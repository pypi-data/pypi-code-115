"""
Implements array kernels such as median and quantile.
"""
import hashlib
import inspect
import math
import operator
import re
import warnings
from math import sqrt
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, types, typing
from numba.core.imputils import lower_builtin
from numba.core.ir_utils import find_const, guard
from numba.core.typing import signature
from numba.core.typing.templates import AbstractTemplate, infer_global
from numba.extending import overload, overload_attribute, register_jitable
from numba.np.arrayobj import make_array
from numba.np.numpy_support import as_dtype
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
from bodo.hiframes.datetime_date_ext import datetime_date_array_type
from bodo.hiframes.datetime_timedelta_ext import datetime_timedelta_array_type
from bodo.hiframes.pd_categorical_ext import CategoricalArrayType, init_categorical_array
from bodo.hiframes.split_impl import string_array_split_view_type
from bodo.libs import quantile_alg
from bodo.libs.array import arr_info_list_to_table, array_to_info, delete_info_decref_array, delete_table, delete_table_decref_arrays, drop_duplicates_table, info_from_table, info_to_array, sample_table
from bodo.libs.array_item_arr_ext import ArrayItemArrayType, offset_type
from bodo.libs.bool_arr_ext import BooleanArrayType, boolean_array
from bodo.libs.decimal_arr_ext import DecimalArrayType
from bodo.libs.dict_arr_ext import DictionaryArrayType
from bodo.libs.distributed_api import Reduce_Type
from bodo.libs.int_arr_ext import IntegerArrayType
from bodo.libs.str_arr_ext import str_arr_set_na, string_array_type
from bodo.libs.struct_arr_ext import StructArrayType
from bodo.libs.tuple_arr_ext import TupleArrayType
from bodo.utils.indexing import add_nested_counts, init_nested_counts
from bodo.utils.typing import BodoError, check_unsupported_args, decode_if_dict_array, element_type, find_common_np_dtype, get_overload_const_bool, get_overload_const_list, get_overload_const_str, is_overload_none, is_str_arr_type, raise_bodo_error, to_str_arr_if_dict_array
from bodo.utils.utils import build_set_seen_na, check_and_propagate_cpp_exception, numba_to_c_type, unliteral_all
ll.add_symbol('quantile_sequential', quantile_alg.quantile_sequential)
ll.add_symbol('quantile_parallel', quantile_alg.quantile_parallel)
MPI_ROOT = 0
sum_op = np.int32(bodo.libs.distributed_api.Reduce_Type.Sum.value)
min_op = np.int32(bodo.libs.distributed_api.Reduce_Type.Min.value)


def isna(arr, i):
    return False


@overload(isna)
def overload_isna(arr, i):
    i = types.unliteral(i)
    if arr == string_array_type:
        return lambda arr, i: bodo.libs.str_arr_ext.str_arr_is_na(arr, i)
    if isinstance(arr, (IntegerArrayType, DecimalArrayType)) or arr in (
        boolean_array, datetime_date_array_type,
        datetime_timedelta_array_type, string_array_split_view_type):
        return lambda arr, i: not bodo.libs.int_arr_ext.get_bit_bitmap_arr(arr
            ._null_bitmap, i)
    if isinstance(arr, ArrayItemArrayType):
        return lambda arr, i: not bodo.libs.int_arr_ext.get_bit_bitmap_arr(bodo
            .libs.array_item_arr_ext.get_null_bitmap(arr), i)
    if isinstance(arr, StructArrayType):
        return lambda arr, i: not bodo.libs.int_arr_ext.get_bit_bitmap_arr(bodo
            .libs.struct_arr_ext.get_null_bitmap(arr), i)
    if isinstance(arr, TupleArrayType):
        return lambda arr, i: bodo.libs.array_kernels.isna(arr._data, i)
    if isinstance(arr, bodo.hiframes.pd_categorical_ext.CategoricalArrayType):
        return lambda arr, i: arr.codes[i] == -1
    if arr == bodo.binary_array_type:
        return lambda arr, i: not bodo.libs.int_arr_ext.get_bit_bitmap_arr(bodo
            .libs.array_item_arr_ext.get_null_bitmap(arr._data), i)
    if isinstance(arr, types.List):
        if arr.dtype == types.none:
            return lambda arr, i: True
        elif isinstance(arr.dtype, types.optional):
            return lambda arr, i: arr[i] is None
        else:
            return lambda arr, i: False
    if isinstance(arr, bodo.NullableTupleType):
        return lambda arr, i: arr._null_values[i]
    if isinstance(arr, DictionaryArrayType):
        return lambda arr, i: not bodo.libs.int_arr_ext.get_bit_bitmap_arr(arr
            ._indices._null_bitmap, i) or bodo.libs.array_kernels.isna(arr.
            _data, arr._indices[i])
    assert isinstance(arr, types.Array), f'Invalid array type in isna(): {arr}'
    dtype = arr.dtype
    if isinstance(dtype, types.Float):
        return lambda arr, i: np.isnan(arr[i])
    if isinstance(dtype, (types.NPDatetime, types.NPTimedelta)):
        return lambda arr, i: np.isnat(arr[i])
    return lambda arr, i: False


def setna(arr, ind, int_nan_const=0):
    arr[ind] = np.nan


@overload(setna, no_unliteral=True)
def setna_overload(arr, ind, int_nan_const=0):
    if isinstance(arr.dtype, types.Float):
        return setna
    if isinstance(arr.dtype, (types.NPDatetime, types.NPTimedelta)):
        nyfch__shg = arr.dtype('NaT')

        def _setnan_impl(arr, ind, int_nan_const=0):
            arr[ind] = nyfch__shg
        return _setnan_impl
    if arr == string_array_type:

        def impl(arr, ind, int_nan_const=0):
            arr[ind] = ''
            str_arr_set_na(arr, ind)
        return impl
    if isinstance(arr, DictionaryArrayType):
        return lambda arr, ind, int_nan_const=0: bodo.libs.array_kernels.setna(
            arr._indices, ind)
    if arr == boolean_array:

        def impl(arr, ind, int_nan_const=0):
            arr[ind] = False
            bodo.libs.int_arr_ext.set_bit_to_arr(arr._null_bitmap, ind, 0)
        return impl
    if isinstance(arr, (IntegerArrayType, DecimalArrayType)):
        return (lambda arr, ind, int_nan_const=0: bodo.libs.int_arr_ext.
            set_bit_to_arr(arr._null_bitmap, ind, 0))
    if arr == bodo.binary_array_type:

        def impl_binary_arr(arr, ind, int_nan_const=0):
            ousi__meg = bodo.libs.array_item_arr_ext.get_offsets(arr._data)
            ousi__meg[ind + 1] = ousi__meg[ind]
            bodo.libs.int_arr_ext.set_bit_to_arr(bodo.libs.
                array_item_arr_ext.get_null_bitmap(arr._data), ind, 0)
        return impl_binary_arr
    if isinstance(arr, bodo.libs.array_item_arr_ext.ArrayItemArrayType):

        def impl_arr_item(arr, ind, int_nan_const=0):
            ousi__meg = bodo.libs.array_item_arr_ext.get_offsets(arr)
            ousi__meg[ind + 1] = ousi__meg[ind]
            bodo.libs.int_arr_ext.set_bit_to_arr(bodo.libs.
                array_item_arr_ext.get_null_bitmap(arr), ind, 0)
        return impl_arr_item
    if isinstance(arr, bodo.libs.struct_arr_ext.StructArrayType):

        def impl(arr, ind, int_nan_const=0):
            bodo.libs.int_arr_ext.set_bit_to_arr(bodo.libs.struct_arr_ext.
                get_null_bitmap(arr), ind, 0)
            data = bodo.libs.struct_arr_ext.get_data(arr)
            setna_tup(data, ind)
        return impl
    if isinstance(arr, TupleArrayType):

        def impl(arr, ind, int_nan_const=0):
            bodo.libs.array_kernels.setna(arr._data, ind)
        return impl
    if arr.dtype == types.bool_:

        def b_set(arr, ind, int_nan_const=0):
            arr[ind] = False
        return b_set
    if isinstance(arr, bodo.hiframes.pd_categorical_ext.CategoricalArrayType):

        def setna_cat(arr, ind, int_nan_const=0):
            arr.codes[ind] = -1
        return setna_cat
    if isinstance(arr.dtype, types.Integer):

        def setna_int(arr, ind, int_nan_const=0):
            arr[ind] = int_nan_const
        return setna_int
    if arr == datetime_date_array_type:

        def setna_datetime_date(arr, ind, int_nan_const=0):
            arr._data[ind] = (1970 << 32) + (1 << 16) + 1
            bodo.libs.int_arr_ext.set_bit_to_arr(arr._null_bitmap, ind, 0)
        return setna_datetime_date
    if arr == datetime_timedelta_array_type:

        def setna_datetime_timedelta(arr, ind, int_nan_const=0):
            bodo.libs.array_kernels.setna(arr._days_data, ind)
            bodo.libs.array_kernels.setna(arr._seconds_data, ind)
            bodo.libs.array_kernels.setna(arr._microseconds_data, ind)
            bodo.libs.int_arr_ext.set_bit_to_arr(arr._null_bitmap, ind, 0)
        return setna_datetime_timedelta
    return lambda arr, ind, int_nan_const=0: None


def setna_tup(arr_tup, ind, int_nan_const=0):
    for arr in arr_tup:
        arr[ind] = np.nan


@overload(setna_tup, no_unliteral=True)
def overload_setna_tup(arr_tup, ind, int_nan_const=0):
    acv__gghb = arr_tup.count
    jmou__upb = 'def f(arr_tup, ind, int_nan_const=0):\n'
    for i in range(acv__gghb):
        jmou__upb += '  setna(arr_tup[{}], ind, int_nan_const)\n'.format(i)
    jmou__upb += '  return\n'
    vhiej__cjdka = {}
    exec(jmou__upb, {'setna': setna}, vhiej__cjdka)
    impl = vhiej__cjdka['f']
    return impl


def setna_slice(arr, s):
    arr[s] = np.nan


@overload(setna_slice, no_unliteral=True)
def overload_setna_slice(arr, s):

    def impl(arr, s):
        zaz__bkox = numba.cpython.unicode._normalize_slice(s, len(arr))
        for i in range(zaz__bkox.start, zaz__bkox.stop, zaz__bkox.step):
            setna(arr, i)
    return impl


@numba.generated_jit
def first_last_valid_index(arr, index_arr, is_first=True, parallel=False):
    is_first = get_overload_const_bool(is_first)
    if is_first:
        rurj__vbh = 'n'
    else:
        rurj__vbh = 'n-1, -1, -1'
    jmou__upb = f"""def impl(arr, index_arr, is_first=True, parallel=False):
    n = len(arr)
    index_val = index_arr[0]
    has_valid = False
    loc_min = -1
    if parallel:
        rank = bodo.libs.distributed_api.get_rank()
        n_pes = bodo.libs.distributed_api.get_size()
        loc_min = n_pes
    for i in range({rurj__vbh}):
        if not isna(arr, i):
            if parallel:
                loc_min = rank
            index_val = index_arr[i]
            has_valid = True
            break
    if parallel:
        min_rank = np.int32(bodo.libs.distributed_api.dist_reduce(loc_min, min_op))
        if min_rank != n_pes:
            has_valid = True
            index_val = bodo.libs.distributed_api.bcast_scalar(index_val, min_rank)
    return has_valid, box_if_dt64(index_val)

    """
    vhiej__cjdka = {}
    exec(jmou__upb, {'np': np, 'bodo': bodo, 'isna': isna, 'min_op': min_op,
        'box_if_dt64': bodo.utils.conversion.box_if_dt64}, vhiej__cjdka)
    impl = vhiej__cjdka['impl']
    return impl


ll.add_symbol('median_series_computation', quantile_alg.
    median_series_computation)
_median_series_computation = types.ExternalFunction('median_series_computation'
    , types.void(types.voidptr, bodo.libs.array.array_info_type, types.
    bool_, types.bool_))


@numba.njit
def median_series_computation(res, arr, is_parallel, skipna):
    pbxu__epfpn = array_to_info(arr)
    _median_series_computation(res, pbxu__epfpn, is_parallel, skipna)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(pbxu__epfpn)


ll.add_symbol('autocorr_series_computation', quantile_alg.
    autocorr_series_computation)
_autocorr_series_computation = types.ExternalFunction(
    'autocorr_series_computation', types.void(types.voidptr, bodo.libs.
    array.array_info_type, types.int64, types.bool_))


@numba.njit
def autocorr_series_computation(res, arr, lag, is_parallel):
    pbxu__epfpn = array_to_info(arr)
    _autocorr_series_computation(res, pbxu__epfpn, lag, is_parallel)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(pbxu__epfpn)


@numba.njit
def autocorr(arr, lag=1, parallel=False):
    res = np.empty(1, types.float64)
    autocorr_series_computation(res.ctypes, arr, lag, parallel)
    return res[0]


ll.add_symbol('compute_series_monotonicity', quantile_alg.
    compute_series_monotonicity)
_compute_series_monotonicity = types.ExternalFunction(
    'compute_series_monotonicity', types.void(types.voidptr, bodo.libs.
    array.array_info_type, types.int64, types.bool_))


@numba.njit
def series_monotonicity_call(res, arr, inc_dec, is_parallel):
    pbxu__epfpn = array_to_info(arr)
    _compute_series_monotonicity(res, pbxu__epfpn, inc_dec, is_parallel)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(pbxu__epfpn)


@numba.njit
def series_monotonicity(arr, inc_dec, parallel=False):
    res = np.empty(1, types.float64)
    series_monotonicity_call(res.ctypes, arr, inc_dec, parallel)
    qqe__ueg = res[0] > 0.5
    return qqe__ueg


@numba.generated_jit(nopython=True)
def get_valid_entries_from_date_offset(index_arr, offset, initial_date,
    is_last, is_parallel=False):
    if get_overload_const_bool(is_last):
        qik__xpfs = '-'
        oueiv__swntx = 'index_arr[0] > threshhold_date'
        rurj__vbh = '1, n+1'
        fddb__zqpb = 'index_arr[-i] <= threshhold_date'
        gwj__rkxu = 'i - 1'
    else:
        qik__xpfs = '+'
        oueiv__swntx = 'index_arr[-1] < threshhold_date'
        rurj__vbh = 'n'
        fddb__zqpb = 'index_arr[i] >= threshhold_date'
        gwj__rkxu = 'i'
    jmou__upb = (
        'def impl(index_arr, offset, initial_date, is_last, is_parallel=False):\n'
        )
    if types.unliteral(offset) == types.unicode_type:
        jmou__upb += (
            '  with numba.objmode(threshhold_date=bodo.pd_timestamp_type):\n')
        jmou__upb += (
            '    date_offset = pd.tseries.frequencies.to_offset(offset)\n')
        if not get_overload_const_bool(is_last):
            jmou__upb += """    if not isinstance(date_offset, pd._libs.tslibs.Tick) and date_offset.is_on_offset(index_arr[0]):
"""
            jmou__upb += (
                '      threshhold_date = initial_date - date_offset.base + date_offset\n'
                )
            jmou__upb += '    else:\n'
            jmou__upb += '      threshhold_date = initial_date + date_offset\n'
        else:
            jmou__upb += (
                f'    threshhold_date = initial_date {qik__xpfs} date_offset\n'
                )
    else:
        jmou__upb += f'  threshhold_date = initial_date {qik__xpfs} offset\n'
    jmou__upb += '  local_valid = 0\n'
    jmou__upb += f'  n = len(index_arr)\n'
    jmou__upb += f'  if n:\n'
    jmou__upb += f'    if {oueiv__swntx}:\n'
    jmou__upb += '      loc_valid = n\n'
    jmou__upb += '    else:\n'
    jmou__upb += f'      for i in range({rurj__vbh}):\n'
    jmou__upb += f'        if {fddb__zqpb}:\n'
    jmou__upb += f'          loc_valid = {gwj__rkxu}\n'
    jmou__upb += '          break\n'
    jmou__upb += '  if is_parallel:\n'
    jmou__upb += (
        '    total_valid = bodo.libs.distributed_api.dist_reduce(loc_valid, sum_op)\n'
        )
    jmou__upb += '    return total_valid\n'
    jmou__upb += '  else:\n'
    jmou__upb += '    return loc_valid\n'
    vhiej__cjdka = {}
    exec(jmou__upb, {'bodo': bodo, 'pd': pd, 'numba': numba, 'sum_op':
        sum_op}, vhiej__cjdka)
    return vhiej__cjdka['impl']


def quantile(A, q):
    return 0


def quantile_parallel(A, q):
    return 0


@infer_global(quantile)
@infer_global(quantile_parallel)
class QuantileType(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) in [2, 3]
        return signature(types.float64, *unliteral_all(args))


@lower_builtin(quantile, types.Array, types.float64)
@lower_builtin(quantile, IntegerArrayType, types.float64)
@lower_builtin(quantile, BooleanArrayType, types.float64)
def lower_dist_quantile_seq(context, builder, sig, args):
    ppti__xyls = numba_to_c_type(sig.args[0].dtype)
    hxnp__ayrg = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(32), ppti__xyls))
    paky__zit = args[0]
    cosa__qufs = sig.args[0]
    if isinstance(cosa__qufs, (IntegerArrayType, BooleanArrayType)):
        paky__zit = cgutils.create_struct_proxy(cosa__qufs)(context,
            builder, paky__zit).data
        cosa__qufs = types.Array(cosa__qufs.dtype, 1, 'C')
    assert cosa__qufs.ndim == 1
    arr = make_array(cosa__qufs)(context, builder, paky__zit)
    mufg__bjylj = builder.extract_value(arr.shape, 0)
    wbe__fxwj = [builder.bitcast(arr.data, lir.IntType(8).as_pointer()),
        mufg__bjylj, args[1], builder.load(hxnp__ayrg)]
    tkad__pjy = [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
        DoubleType(), lir.IntType(32)]
    aeknb__hiwtv = lir.FunctionType(lir.DoubleType(), tkad__pjy)
    gvhvn__ypvq = cgutils.get_or_insert_function(builder.module,
        aeknb__hiwtv, name='quantile_sequential')
    alum__nyay = builder.call(gvhvn__ypvq, wbe__fxwj)
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return alum__nyay


@lower_builtin(quantile_parallel, types.Array, types.float64, types.intp)
@lower_builtin(quantile_parallel, IntegerArrayType, types.float64, types.intp)
@lower_builtin(quantile_parallel, BooleanArrayType, types.float64, types.intp)
def lower_dist_quantile_parallel(context, builder, sig, args):
    ppti__xyls = numba_to_c_type(sig.args[0].dtype)
    hxnp__ayrg = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(32), ppti__xyls))
    paky__zit = args[0]
    cosa__qufs = sig.args[0]
    if isinstance(cosa__qufs, (IntegerArrayType, BooleanArrayType)):
        paky__zit = cgutils.create_struct_proxy(cosa__qufs)(context,
            builder, paky__zit).data
        cosa__qufs = types.Array(cosa__qufs.dtype, 1, 'C')
    assert cosa__qufs.ndim == 1
    arr = make_array(cosa__qufs)(context, builder, paky__zit)
    mufg__bjylj = builder.extract_value(arr.shape, 0)
    if len(args) == 3:
        dmkd__oqg = args[2]
    else:
        dmkd__oqg = mufg__bjylj
    wbe__fxwj = [builder.bitcast(arr.data, lir.IntType(8).as_pointer()),
        mufg__bjylj, dmkd__oqg, args[1], builder.load(hxnp__ayrg)]
    tkad__pjy = [lir.IntType(8).as_pointer(), lir.IntType(64), lir.IntType(
        64), lir.DoubleType(), lir.IntType(32)]
    aeknb__hiwtv = lir.FunctionType(lir.DoubleType(), tkad__pjy)
    gvhvn__ypvq = cgutils.get_or_insert_function(builder.module,
        aeknb__hiwtv, name='quantile_parallel')
    alum__nyay = builder.call(gvhvn__ypvq, wbe__fxwj)
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return alum__nyay


@numba.njit
def min_heapify(arr, ind_arr, n, start, cmp_f):
    xdxv__utapx = start
    vhdhq__xclhd = 2 * start + 1
    rsmhx__eopm = 2 * start + 2
    if vhdhq__xclhd < n and not cmp_f(arr[vhdhq__xclhd], arr[xdxv__utapx]):
        xdxv__utapx = vhdhq__xclhd
    if rsmhx__eopm < n and not cmp_f(arr[rsmhx__eopm], arr[xdxv__utapx]):
        xdxv__utapx = rsmhx__eopm
    if xdxv__utapx != start:
        arr[start], arr[xdxv__utapx] = arr[xdxv__utapx], arr[start]
        ind_arr[start], ind_arr[xdxv__utapx] = ind_arr[xdxv__utapx], ind_arr[
            start]
        min_heapify(arr, ind_arr, n, xdxv__utapx, cmp_f)


def select_k_nonan(A, index_arr, m, k):
    return A[:k]


@overload(select_k_nonan, no_unliteral=True)
def select_k_nonan_overload(A, index_arr, m, k):
    dtype = A.dtype
    if isinstance(dtype, types.Integer):
        return lambda A, index_arr, m, k: (A[:k].copy(), index_arr[:k].copy
            (), k)

    def select_k_nonan_float(A, index_arr, m, k):
        ollvo__kwt = np.empty(k, A.dtype)
        mstmx__qqccx = np.empty(k, index_arr.dtype)
        i = 0
        ind = 0
        while i < m and ind < k:
            if not bodo.libs.array_kernels.isna(A, i):
                ollvo__kwt[ind] = A[i]
                mstmx__qqccx[ind] = index_arr[i]
                ind += 1
            i += 1
        if ind < k:
            ollvo__kwt = ollvo__kwt[:ind]
            mstmx__qqccx = mstmx__qqccx[:ind]
        return ollvo__kwt, mstmx__qqccx, i
    return select_k_nonan_float


@numba.njit
def nlargest(A, index_arr, k, is_largest, cmp_f):
    m = len(A)
    if k == 0:
        return A[:0], index_arr[:0]
    if k >= m:
        iagl__tdd = np.sort(A)
        sdh__lkj = index_arr[np.argsort(A)]
        qcq__nyv = pd.Series(iagl__tdd).notna().values
        iagl__tdd = iagl__tdd[qcq__nyv]
        sdh__lkj = sdh__lkj[qcq__nyv]
        if is_largest:
            iagl__tdd = iagl__tdd[::-1]
            sdh__lkj = sdh__lkj[::-1]
        return np.ascontiguousarray(iagl__tdd), np.ascontiguousarray(sdh__lkj)
    ollvo__kwt, mstmx__qqccx, start = select_k_nonan(A, index_arr, m, k)
    mstmx__qqccx = mstmx__qqccx[ollvo__kwt.argsort()]
    ollvo__kwt.sort()
    if not is_largest:
        ollvo__kwt = np.ascontiguousarray(ollvo__kwt[::-1])
        mstmx__qqccx = np.ascontiguousarray(mstmx__qqccx[::-1])
    for i in range(start, m):
        if cmp_f(A[i], ollvo__kwt[0]):
            ollvo__kwt[0] = A[i]
            mstmx__qqccx[0] = index_arr[i]
            min_heapify(ollvo__kwt, mstmx__qqccx, k, 0, cmp_f)
    mstmx__qqccx = mstmx__qqccx[ollvo__kwt.argsort()]
    ollvo__kwt.sort()
    if is_largest:
        ollvo__kwt = ollvo__kwt[::-1]
        mstmx__qqccx = mstmx__qqccx[::-1]
    return np.ascontiguousarray(ollvo__kwt), np.ascontiguousarray(mstmx__qqccx)


@numba.njit
def nlargest_parallel(A, I, k, is_largest, cmp_f):
    xierm__rwrw = bodo.libs.distributed_api.get_rank()
    smpg__xth, rstlr__zhfcf = nlargest(A, I, k, is_largest, cmp_f)
    mrrtp__xfyeh = bodo.libs.distributed_api.gatherv(smpg__xth)
    bjhap__eks = bodo.libs.distributed_api.gatherv(rstlr__zhfcf)
    if xierm__rwrw == MPI_ROOT:
        res, tkjix__lhdt = nlargest(mrrtp__xfyeh, bjhap__eks, k, is_largest,
            cmp_f)
    else:
        res = np.empty(k, A.dtype)
        tkjix__lhdt = np.empty(k, I.dtype)
    bodo.libs.distributed_api.bcast(res)
    bodo.libs.distributed_api.bcast(tkjix__lhdt)
    return res, tkjix__lhdt


@numba.njit(no_cpython_wrapper=True, cache=True)
def nancorr(mat, cov=0, minpv=1, parallel=False):
    qkcf__deus, yycf__jdvo = mat.shape
    wit__rcd = np.empty((yycf__jdvo, yycf__jdvo), dtype=np.float64)
    for lodw__jcks in range(yycf__jdvo):
        for nql__kjg in range(lodw__jcks + 1):
            tbqu__wqk = 0
            hoe__rqwdp = ztqf__ico = dccfs__wsx = xda__buao = 0.0
            for i in range(qkcf__deus):
                if np.isfinite(mat[i, lodw__jcks]) and np.isfinite(mat[i,
                    nql__kjg]):
                    mkbpn__ulifg = mat[i, lodw__jcks]
                    ypufe__jdtc = mat[i, nql__kjg]
                    tbqu__wqk += 1
                    dccfs__wsx += mkbpn__ulifg
                    xda__buao += ypufe__jdtc
            if parallel:
                tbqu__wqk = bodo.libs.distributed_api.dist_reduce(tbqu__wqk,
                    sum_op)
                dccfs__wsx = bodo.libs.distributed_api.dist_reduce(dccfs__wsx,
                    sum_op)
                xda__buao = bodo.libs.distributed_api.dist_reduce(xda__buao,
                    sum_op)
            if tbqu__wqk < minpv:
                wit__rcd[lodw__jcks, nql__kjg] = wit__rcd[nql__kjg, lodw__jcks
                    ] = np.nan
            else:
                eml__mkv = dccfs__wsx / tbqu__wqk
                rdo__rxb = xda__buao / tbqu__wqk
                dccfs__wsx = 0.0
                for i in range(qkcf__deus):
                    if np.isfinite(mat[i, lodw__jcks]) and np.isfinite(mat[
                        i, nql__kjg]):
                        mkbpn__ulifg = mat[i, lodw__jcks] - eml__mkv
                        ypufe__jdtc = mat[i, nql__kjg] - rdo__rxb
                        dccfs__wsx += mkbpn__ulifg * ypufe__jdtc
                        hoe__rqwdp += mkbpn__ulifg * mkbpn__ulifg
                        ztqf__ico += ypufe__jdtc * ypufe__jdtc
                if parallel:
                    dccfs__wsx = bodo.libs.distributed_api.dist_reduce(
                        dccfs__wsx, sum_op)
                    hoe__rqwdp = bodo.libs.distributed_api.dist_reduce(
                        hoe__rqwdp, sum_op)
                    ztqf__ico = bodo.libs.distributed_api.dist_reduce(ztqf__ico
                        , sum_op)
                bkdb__szbly = tbqu__wqk - 1.0 if cov else sqrt(hoe__rqwdp *
                    ztqf__ico)
                if bkdb__szbly != 0.0:
                    wit__rcd[lodw__jcks, nql__kjg] = wit__rcd[nql__kjg,
                        lodw__jcks] = dccfs__wsx / bkdb__szbly
                else:
                    wit__rcd[lodw__jcks, nql__kjg] = wit__rcd[nql__kjg,
                        lodw__jcks] = np.nan
    return wit__rcd


@numba.generated_jit(nopython=True)
def duplicated(data, parallel=False):
    n = len(data)
    if n == 0:
        return lambda data, parallel=False: np.empty(0, dtype=np.bool_)
    lbics__gyc = n != 1
    jmou__upb = 'def impl(data, parallel=False):\n'
    jmou__upb += '  if parallel:\n'
    prpg__siga = ', '.join(f'array_to_info(data[{i}])' for i in range(n))
    jmou__upb += f'    cpp_table = arr_info_list_to_table([{prpg__siga}])\n'
    jmou__upb += (
        f'    out_cpp_table = bodo.libs.array.shuffle_table(cpp_table, {n}, parallel, 1)\n'
        )
    qgfv__krr = ', '.join(
        f'info_to_array(info_from_table(out_cpp_table, {i}), data[{i}])' for
        i in range(n))
    jmou__upb += f'    data = ({qgfv__krr},)\n'
    jmou__upb += (
        '    shuffle_info = bodo.libs.array.get_shuffle_info(out_cpp_table)\n')
    jmou__upb += '    bodo.libs.array.delete_table(out_cpp_table)\n'
    jmou__upb += '    bodo.libs.array.delete_table(cpp_table)\n'
    jmou__upb += '  n = len(data[0])\n'
    jmou__upb += '  out = np.empty(n, np.bool_)\n'
    jmou__upb += '  uniqs = dict()\n'
    if lbics__gyc:
        jmou__upb += '  for i in range(n):\n'
        zmtfl__bxqs = ', '.join(f'data[{i}][i]' for i in range(n))
        quq__ctofk = ',  '.join(
            f'bodo.libs.array_kernels.isna(data[{i}], i)' for i in range(n))
        jmou__upb += f"""    val = bodo.libs.nullable_tuple_ext.build_nullable_tuple(({zmtfl__bxqs},), ({quq__ctofk},))
"""
        jmou__upb += '    if val in uniqs:\n'
        jmou__upb += '      out[i] = True\n'
        jmou__upb += '    else:\n'
        jmou__upb += '      out[i] = False\n'
        jmou__upb += '      uniqs[val] = 0\n'
    else:
        jmou__upb += '  data = data[0]\n'
        jmou__upb += '  hasna = False\n'
        jmou__upb += '  for i in range(n):\n'
        jmou__upb += '    if bodo.libs.array_kernels.isna(data, i):\n'
        jmou__upb += '      out[i] = hasna\n'
        jmou__upb += '      hasna = True\n'
        jmou__upb += '    else:\n'
        jmou__upb += '      val = data[i]\n'
        jmou__upb += '      if val in uniqs:\n'
        jmou__upb += '        out[i] = True\n'
        jmou__upb += '      else:\n'
        jmou__upb += '        out[i] = False\n'
        jmou__upb += '        uniqs[val] = 0\n'
    jmou__upb += '  if parallel:\n'
    jmou__upb += (
        '    out = bodo.hiframes.pd_groupby_ext.reverse_shuffle(out, shuffle_info)\n'
        )
    jmou__upb += '  return out\n'
    vhiej__cjdka = {}
    exec(jmou__upb, {'bodo': bodo, 'np': np, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'info_to_array':
        info_to_array, 'info_from_table': info_from_table}, vhiej__cjdka)
    impl = vhiej__cjdka['impl']
    return impl


def sample_table_operation(data, ind_arr, n, frac, replace, parallel=False):
    return data, ind_arr


@overload(sample_table_operation, no_unliteral=True)
def overload_sample_table_operation(data, ind_arr, n, frac, replace,
    parallel=False):
    acv__gghb = len(data)
    jmou__upb = 'def impl(data, ind_arr, n, frac, replace, parallel=False):\n'
    jmou__upb += '  info_list_total = [{}, array_to_info(ind_arr)]\n'.format(
        ', '.join('array_to_info(data[{}])'.format(x) for x in range(
        acv__gghb)))
    jmou__upb += '  table_total = arr_info_list_to_table(info_list_total)\n'
    jmou__upb += (
        '  out_table = sample_table(table_total, n, frac, replace, parallel)\n'
        .format(acv__gghb))
    for rraxe__yudig in range(acv__gghb):
        jmou__upb += (
            '  out_arr_{} = info_to_array(info_from_table(out_table, {}), data[{}])\n'
            .format(rraxe__yudig, rraxe__yudig, rraxe__yudig))
    jmou__upb += (
        '  out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)\n'
        .format(acv__gghb))
    jmou__upb += '  delete_table(out_table)\n'
    jmou__upb += '  delete_table(table_total)\n'
    jmou__upb += '  return ({},), out_arr_index\n'.format(', '.join(
        'out_arr_{}'.format(i) for i in range(acv__gghb)))
    vhiej__cjdka = {}
    exec(jmou__upb, {'np': np, 'bodo': bodo, 'array_to_info': array_to_info,
        'sample_table': sample_table, 'arr_info_list_to_table':
        arr_info_list_to_table, 'info_from_table': info_from_table,
        'info_to_array': info_to_array, 'delete_table': delete_table,
        'delete_table_decref_arrays': delete_table_decref_arrays}, vhiej__cjdka
        )
    impl = vhiej__cjdka['impl']
    return impl


def drop_duplicates(data, ind_arr, ncols, parallel=False):
    return data, ind_arr


@overload(drop_duplicates, no_unliteral=True)
def overload_drop_duplicates(data, ind_arr, ncols, parallel=False):
    acv__gghb = len(data)
    jmou__upb = 'def impl(data, ind_arr, ncols, parallel=False):\n'
    jmou__upb += '  info_list_total = [{}, array_to_info(ind_arr)]\n'.format(
        ', '.join('array_to_info(data[{}])'.format(x) for x in range(
        acv__gghb)))
    jmou__upb += '  table_total = arr_info_list_to_table(info_list_total)\n'
    jmou__upb += '  keep_i = 0\n'
    jmou__upb += """  out_table = drop_duplicates_table(table_total, parallel, ncols, keep_i, False, True)
"""
    for rraxe__yudig in range(acv__gghb):
        jmou__upb += (
            '  out_arr_{} = info_to_array(info_from_table(out_table, {}), data[{}])\n'
            .format(rraxe__yudig, rraxe__yudig, rraxe__yudig))
    jmou__upb += (
        '  out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)\n'
        .format(acv__gghb))
    jmou__upb += '  delete_table(out_table)\n'
    jmou__upb += '  delete_table(table_total)\n'
    jmou__upb += '  return ({},), out_arr_index\n'.format(', '.join(
        'out_arr_{}'.format(i) for i in range(acv__gghb)))
    vhiej__cjdka = {}
    exec(jmou__upb, {'np': np, 'bodo': bodo, 'array_to_info': array_to_info,
        'drop_duplicates_table': drop_duplicates_table,
        'arr_info_list_to_table': arr_info_list_to_table, 'info_from_table':
        info_from_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays}, vhiej__cjdka)
    impl = vhiej__cjdka['impl']
    return impl


def drop_duplicates_array(data_arr, parallel=False):
    return data_arr


@overload(drop_duplicates_array, no_unliteral=True)
def overload_drop_duplicates_array(data_arr, parallel=False):

    def impl(data_arr, parallel=False):
        qdi__xpe = [array_to_info(data_arr)]
        gxtgu__tldd = arr_info_list_to_table(qdi__xpe)
        yymj__ojhgf = 0
        ktlqi__jwfa = drop_duplicates_table(gxtgu__tldd, parallel, 1,
            yymj__ojhgf, False, True)
        wqs__qxj = info_to_array(info_from_table(ktlqi__jwfa, 0), data_arr)
        delete_table(ktlqi__jwfa)
        delete_table(gxtgu__tldd)
        return wqs__qxj
    return impl


def dropna(data, how, thresh, subset, parallel=False):
    return data


@overload(dropna, no_unliteral=True)
def overload_dropna(data, how, thresh, subset):
    jcfmd__sbk = len(data.types)
    hug__ika = [('out' + str(i)) for i in range(jcfmd__sbk)]
    oap__ijtdd = get_overload_const_list(subset)
    how = get_overload_const_str(how)
    pdxm__xtd = ['isna(data[{}], i)'.format(i) for i in oap__ijtdd]
    ggv__clyt = 'not ({})'.format(' or '.join(pdxm__xtd))
    if not is_overload_none(thresh):
        ggv__clyt = '(({}) <= ({}) - thresh)'.format(' + '.join(pdxm__xtd),
            jcfmd__sbk - 1)
    elif how == 'all':
        ggv__clyt = 'not ({})'.format(' and '.join(pdxm__xtd))
    jmou__upb = 'def _dropna_imp(data, how, thresh, subset):\n'
    jmou__upb += '  old_len = len(data[0])\n'
    jmou__upb += '  new_len = 0\n'
    jmou__upb += '  for i in range(old_len):\n'
    jmou__upb += '    if {}:\n'.format(ggv__clyt)
    jmou__upb += '      new_len += 1\n'
    for i, out in enumerate(hug__ika):
        if isinstance(data[i], bodo.CategoricalArrayType):
            jmou__upb += (
                '  {0} = bodo.utils.utils.alloc_type(new_len, data[{1}], (-1,))\n'
                .format(out, i))
        else:
            jmou__upb += (
                '  {0} = bodo.utils.utils.alloc_type(new_len, t{1}, (-1,))\n'
                .format(out, i))
    jmou__upb += '  curr_ind = 0\n'
    jmou__upb += '  for i in range(old_len):\n'
    jmou__upb += '    if {}:\n'.format(ggv__clyt)
    for i in range(jcfmd__sbk):
        jmou__upb += '      if isna(data[{}], i):\n'.format(i)
        jmou__upb += '        setna({}, curr_ind)\n'.format(hug__ika[i])
        jmou__upb += '      else:\n'
        jmou__upb += '        {}[curr_ind] = data[{}][i]\n'.format(hug__ika
            [i], i)
    jmou__upb += '      curr_ind += 1\n'
    jmou__upb += '  return {}\n'.format(', '.join(hug__ika))
    vhiej__cjdka = {}
    hdf__ahtj = {'t{}'.format(i): jwb__sragj for i, jwb__sragj in enumerate
        (data.types)}
    hdf__ahtj.update({'isna': isna, 'setna': setna, 'init_nested_counts':
        bodo.utils.indexing.init_nested_counts, 'add_nested_counts': bodo.
        utils.indexing.add_nested_counts, 'bodo': bodo})
    exec(jmou__upb, hdf__ahtj, vhiej__cjdka)
    pqa__fgz = vhiej__cjdka['_dropna_imp']
    return pqa__fgz


def get(arr, ind):
    return pd.Series(arr).str.get(ind)


@overload(get, no_unliteral=True)
def overload_get(arr, ind):
    if isinstance(arr, ArrayItemArrayType):
        cosa__qufs = arr.dtype
        krl__vkk = cosa__qufs.dtype

        def get_arr_item(arr, ind):
            n = len(arr)
            ikazr__wlg = init_nested_counts(krl__vkk)
            for k in range(n):
                if bodo.libs.array_kernels.isna(arr, k):
                    continue
                val = arr[k]
                if not len(val) > ind >= -len(val
                    ) or bodo.libs.array_kernels.isna(val, ind):
                    continue
                ikazr__wlg = add_nested_counts(ikazr__wlg, val[ind])
            wqs__qxj = bodo.utils.utils.alloc_type(n, cosa__qufs, ikazr__wlg)
            for cmjzq__czcgs in range(n):
                if bodo.libs.array_kernels.isna(arr, cmjzq__czcgs):
                    setna(wqs__qxj, cmjzq__czcgs)
                    continue
                val = arr[cmjzq__czcgs]
                if not len(val) > ind >= -len(val
                    ) or bodo.libs.array_kernels.isna(val, ind):
                    setna(wqs__qxj, cmjzq__czcgs)
                    continue
                wqs__qxj[cmjzq__czcgs] = val[ind]
            return wqs__qxj
        return get_arr_item


def _is_same_categorical_array_type(arr_types):
    from bodo.hiframes.pd_categorical_ext import _to_readonly
    if not isinstance(arr_types, types.BaseTuple) or len(arr_types) == 0:
        return False
    zhuk__ggnlt = _to_readonly(arr_types.types[0])
    return all(isinstance(jwb__sragj, CategoricalArrayType) and 
        _to_readonly(jwb__sragj) == zhuk__ggnlt for jwb__sragj in arr_types
        .types)


def concat(arr_list):
    return pd.concat(arr_list)


@overload(concat, no_unliteral=True)
def concat_overload(arr_list):
    if isinstance(arr_list, bodo.NullableTupleType):
        return lambda arr_list: bodo.libs.array_kernels.concat(arr_list._data)
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, ArrayItemArrayType):
        hbq__ddkw = arr_list.dtype.dtype

        def array_item_concat_impl(arr_list):
            azly__gieg = 0
            ovs__znr = []
            for A in arr_list:
                dezzh__iqis = len(A)
                bodo.libs.array_item_arr_ext.trim_excess_data(A)
                ovs__znr.append(bodo.libs.array_item_arr_ext.get_data(A))
                azly__gieg += dezzh__iqis
            dkfme__xkrmb = np.empty(azly__gieg + 1, offset_type)
            daarc__jjdk = bodo.libs.array_kernels.concat(ovs__znr)
            khbu__lcjqh = np.empty(azly__gieg + 7 >> 3, np.uint8)
            zvki__tay = 0
            jpx__fquyw = 0
            for A in arr_list:
                vodag__jgo = bodo.libs.array_item_arr_ext.get_offsets(A)
                vcesx__trtme = bodo.libs.array_item_arr_ext.get_null_bitmap(A)
                dezzh__iqis = len(A)
                ezly__wsk = vodag__jgo[dezzh__iqis]
                for i in range(dezzh__iqis):
                    dkfme__xkrmb[i + zvki__tay] = vodag__jgo[i] + jpx__fquyw
                    qjs__znoej = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        vcesx__trtme, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(khbu__lcjqh, i +
                        zvki__tay, qjs__znoej)
                zvki__tay += dezzh__iqis
                jpx__fquyw += ezly__wsk
            dkfme__xkrmb[zvki__tay] = jpx__fquyw
            wqs__qxj = bodo.libs.array_item_arr_ext.init_array_item_array(
                azly__gieg, daarc__jjdk, dkfme__xkrmb, khbu__lcjqh)
            return wqs__qxj
        return array_item_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, bodo.StructArrayType):
        zyxsd__matd = arr_list.dtype.names
        jmou__upb = 'def struct_array_concat_impl(arr_list):\n'
        jmou__upb += f'    n_all = 0\n'
        for i in range(len(zyxsd__matd)):
            jmou__upb += f'    concat_list{i} = []\n'
        jmou__upb += '    for A in arr_list:\n'
        jmou__upb += (
            '        data_tuple = bodo.libs.struct_arr_ext.get_data(A)\n')
        for i in range(len(zyxsd__matd)):
            jmou__upb += f'        concat_list{i}.append(data_tuple[{i}])\n'
        jmou__upb += '        n_all += len(A)\n'
        jmou__upb += '    n_bytes = (n_all + 7) >> 3\n'
        jmou__upb += '    new_mask = np.empty(n_bytes, np.uint8)\n'
        jmou__upb += '    curr_bit = 0\n'
        jmou__upb += '    for A in arr_list:\n'
        jmou__upb += (
            '        old_mask = bodo.libs.struct_arr_ext.get_null_bitmap(A)\n')
        jmou__upb += '        for j in range(len(A)):\n'
        jmou__upb += (
            '            bit = bodo.libs.int_arr_ext.get_bit_bitmap_arr(old_mask, j)\n'
            )
        jmou__upb += (
            '            bodo.libs.int_arr_ext.set_bit_to_arr(new_mask, curr_bit, bit)\n'
            )
        jmou__upb += '            curr_bit += 1\n'
        jmou__upb += '    return bodo.libs.struct_arr_ext.init_struct_arr(\n'
        sogj__sujw = ', '.join([
            f'bodo.libs.array_kernels.concat(concat_list{i})' for i in
            range(len(zyxsd__matd))])
        jmou__upb += f'        ({sogj__sujw},),\n'
        jmou__upb += '        new_mask,\n'
        jmou__upb += f'        {zyxsd__matd},\n'
        jmou__upb += '    )\n'
        vhiej__cjdka = {}
        exec(jmou__upb, {'bodo': bodo, 'np': np}, vhiej__cjdka)
        return vhiej__cjdka['struct_array_concat_impl']
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == datetime_date_array_type:

        def datetime_date_array_concat_impl(arr_list):
            tkian__sipl = 0
            for A in arr_list:
                tkian__sipl += len(A)
            yyid__smumb = (bodo.hiframes.datetime_date_ext.
                alloc_datetime_date_array(tkian__sipl))
            sptij__dss = 0
            for A in arr_list:
                for i in range(len(A)):
                    yyid__smumb._data[i + sptij__dss] = A._data[i]
                    qjs__znoej = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(yyid__smumb.
                        _null_bitmap, i + sptij__dss, qjs__znoej)
                sptij__dss += len(A)
            return yyid__smumb
        return datetime_date_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == datetime_timedelta_array_type:

        def datetime_timedelta_array_concat_impl(arr_list):
            tkian__sipl = 0
            for A in arr_list:
                tkian__sipl += len(A)
            yyid__smumb = (bodo.hiframes.datetime_timedelta_ext.
                alloc_datetime_timedelta_array(tkian__sipl))
            sptij__dss = 0
            for A in arr_list:
                for i in range(len(A)):
                    yyid__smumb._days_data[i + sptij__dss] = A._days_data[i]
                    yyid__smumb._seconds_data[i + sptij__dss
                        ] = A._seconds_data[i]
                    yyid__smumb._microseconds_data[i + sptij__dss
                        ] = A._microseconds_data[i]
                    qjs__znoej = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(yyid__smumb.
                        _null_bitmap, i + sptij__dss, qjs__znoej)
                sptij__dss += len(A)
            return yyid__smumb
        return datetime_timedelta_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, DecimalArrayType):
        hwhz__spsfs = arr_list.dtype.precision
        ptfah__llijw = arr_list.dtype.scale

        def decimal_array_concat_impl(arr_list):
            tkian__sipl = 0
            for A in arr_list:
                tkian__sipl += len(A)
            yyid__smumb = bodo.libs.decimal_arr_ext.alloc_decimal_array(
                tkian__sipl, hwhz__spsfs, ptfah__llijw)
            sptij__dss = 0
            for A in arr_list:
                for i in range(len(A)):
                    yyid__smumb._data[i + sptij__dss] = A._data[i]
                    qjs__znoej = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(yyid__smumb.
                        _null_bitmap, i + sptij__dss, qjs__znoej)
                sptij__dss += len(A)
            return yyid__smumb
        return decimal_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and (is_str_arr_type
        (arr_list.dtype) or arr_list.dtype == bodo.binary_array_type
        ) or isinstance(arr_list, types.BaseTuple) and all(is_str_arr_type(
        jwb__sragj) for jwb__sragj in arr_list.types):
        if isinstance(arr_list, types.BaseTuple):
            gvo__icv = arr_list.types[0]
        else:
            gvo__icv = arr_list.dtype
        gvo__icv = to_str_arr_if_dict_array(gvo__icv)

        def impl_str(arr_list):
            arr_list = decode_if_dict_array(arr_list)
            mgvwm__fsh = 0
            hxm__rhc = 0
            for A in arr_list:
                arr = A
                mgvwm__fsh += len(arr)
                hxm__rhc += bodo.libs.str_arr_ext.num_total_chars(arr)
            wqs__qxj = bodo.utils.utils.alloc_type(mgvwm__fsh, gvo__icv, (
                hxm__rhc,))
            bodo.libs.str_arr_ext.set_null_bits_to_value(wqs__qxj, -1)
            ofhnc__ivxre = 0
            adn__xsqxm = 0
            for A in arr_list:
                arr = A
                bodo.libs.str_arr_ext.set_string_array_range(wqs__qxj, arr,
                    ofhnc__ivxre, adn__xsqxm)
                ofhnc__ivxre += len(arr)
                adn__xsqxm += bodo.libs.str_arr_ext.num_total_chars(arr)
            return wqs__qxj
        return impl_str
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, IntegerArrayType) or isinstance(arr_list, types.
        BaseTuple) and all(isinstance(jwb__sragj.dtype, types.Integer) for
        jwb__sragj in arr_list.types) and any(isinstance(jwb__sragj,
        IntegerArrayType) for jwb__sragj in arr_list.types):

        def impl_int_arr_list(arr_list):
            jdxk__qwrs = convert_to_nullable_tup(arr_list)
            jdgnb__nmp = []
            bih__frzyb = 0
            for A in jdxk__qwrs:
                jdgnb__nmp.append(A._data)
                bih__frzyb += len(A)
            daarc__jjdk = bodo.libs.array_kernels.concat(jdgnb__nmp)
            kbdf__aud = bih__frzyb + 7 >> 3
            zujkr__rryz = np.empty(kbdf__aud, np.uint8)
            vkop__qgrc = 0
            for A in jdxk__qwrs:
                zeaa__dvcc = A._null_bitmap
                for cmjzq__czcgs in range(len(A)):
                    qjs__znoej = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        zeaa__dvcc, cmjzq__czcgs)
                    bodo.libs.int_arr_ext.set_bit_to_arr(zujkr__rryz,
                        vkop__qgrc, qjs__znoej)
                    vkop__qgrc += 1
            return bodo.libs.int_arr_ext.init_integer_array(daarc__jjdk,
                zujkr__rryz)
        return impl_int_arr_list
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == boolean_array or isinstance(arr_list, types
        .BaseTuple) and all(jwb__sragj.dtype == types.bool_ for jwb__sragj in
        arr_list.types) and any(jwb__sragj == boolean_array for jwb__sragj in
        arr_list.types):

        def impl_bool_arr_list(arr_list):
            jdxk__qwrs = convert_to_nullable_tup(arr_list)
            jdgnb__nmp = []
            bih__frzyb = 0
            for A in jdxk__qwrs:
                jdgnb__nmp.append(A._data)
                bih__frzyb += len(A)
            daarc__jjdk = bodo.libs.array_kernels.concat(jdgnb__nmp)
            kbdf__aud = bih__frzyb + 7 >> 3
            zujkr__rryz = np.empty(kbdf__aud, np.uint8)
            vkop__qgrc = 0
            for A in jdxk__qwrs:
                zeaa__dvcc = A._null_bitmap
                for cmjzq__czcgs in range(len(A)):
                    qjs__znoej = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        zeaa__dvcc, cmjzq__czcgs)
                    bodo.libs.int_arr_ext.set_bit_to_arr(zujkr__rryz,
                        vkop__qgrc, qjs__znoej)
                    vkop__qgrc += 1
            return bodo.libs.bool_arr_ext.init_bool_array(daarc__jjdk,
                zujkr__rryz)
        return impl_bool_arr_list
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, CategoricalArrayType):

        def cat_array_concat_impl(arr_list):
            exggt__uban = []
            for A in arr_list:
                exggt__uban.append(A.codes)
            return init_categorical_array(bodo.libs.array_kernels.concat(
                exggt__uban), arr_list[0].dtype)
        return cat_array_concat_impl
    if _is_same_categorical_array_type(arr_list):
        hvsxj__qsi = ', '.join(f'arr_list[{i}].codes' for i in range(len(
            arr_list)))
        jmou__upb = 'def impl(arr_list):\n'
        jmou__upb += f"""    return init_categorical_array(bodo.libs.array_kernels.concat(({hvsxj__qsi},)), arr_list[0].dtype)
"""
        xej__ypdq = {}
        exec(jmou__upb, {'bodo': bodo, 'init_categorical_array':
            init_categorical_array}, xej__ypdq)
        return xej__ypdq['impl']
    if isinstance(arr_list, types.List) and isinstance(arr_list.dtype,
        types.Array) and arr_list.dtype.ndim == 1:
        dtype = arr_list.dtype.dtype

        def impl_np_arr_list(arr_list):
            bih__frzyb = 0
            for A in arr_list:
                bih__frzyb += len(A)
            wqs__qxj = np.empty(bih__frzyb, dtype)
            feoa__rjpb = 0
            for A in arr_list:
                n = len(A)
                wqs__qxj[feoa__rjpb:feoa__rjpb + n] = A
                feoa__rjpb += n
            return wqs__qxj
        return impl_np_arr_list
    if isinstance(arr_list, types.BaseTuple) and any(isinstance(jwb__sragj,
        (types.Array, IntegerArrayType)) and isinstance(jwb__sragj.dtype,
        types.Integer) for jwb__sragj in arr_list.types) and any(isinstance
        (jwb__sragj, types.Array) and isinstance(jwb__sragj.dtype, types.
        Float) for jwb__sragj in arr_list.types):
        return lambda arr_list: np.concatenate(astype_float_tup(arr_list))
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, bodo.MapArrayType):

        def impl_map_arr_list(arr_list):
            vrzd__sjwqr = []
            for A in arr_list:
                vrzd__sjwqr.append(A._data)
            bze__mzk = bodo.libs.array_kernels.concat(vrzd__sjwqr)
            wit__rcd = bodo.libs.map_arr_ext.init_map_arr(bze__mzk)
            return wit__rcd
        return impl_map_arr_list
    for yne__yrpq in arr_list:
        if not isinstance(yne__yrpq, types.Array):
            raise_bodo_error(f'concat of array types {arr_list} not supported')
    return lambda arr_list: np.concatenate(arr_list)


def astype_float_tup(arr_tup):
    return tuple(jwb__sragj.astype(np.float64) for jwb__sragj in arr_tup)


@overload(astype_float_tup, no_unliteral=True)
def overload_astype_float_tup(arr_tup):
    assert isinstance(arr_tup, types.BaseTuple)
    acv__gghb = len(arr_tup.types)
    jmou__upb = 'def f(arr_tup):\n'
    jmou__upb += '  return ({}{})\n'.format(','.join(
        'arr_tup[{}].astype(np.float64)'.format(i) for i in range(acv__gghb
        )), ',' if acv__gghb == 1 else '')
    vhiej__cjdka = {}
    exec(jmou__upb, {'np': np}, vhiej__cjdka)
    xjxno__rgd = vhiej__cjdka['f']
    return xjxno__rgd


def convert_to_nullable_tup(arr_tup):
    return arr_tup


@overload(convert_to_nullable_tup, no_unliteral=True)
def overload_convert_to_nullable_tup(arr_tup):
    if isinstance(arr_tup, (types.UniTuple, types.List)) and isinstance(arr_tup
        .dtype, (IntegerArrayType, BooleanArrayType)):
        return lambda arr_tup: arr_tup
    assert isinstance(arr_tup, types.BaseTuple)
    acv__gghb = len(arr_tup.types)
    gutx__rfvld = find_common_np_dtype(arr_tup.types)
    krl__vkk = None
    vlzg__uvt = ''
    if isinstance(gutx__rfvld, types.Integer):
        krl__vkk = bodo.libs.int_arr_ext.IntDtype(gutx__rfvld)
        vlzg__uvt = '.astype(out_dtype, False)'
    jmou__upb = 'def f(arr_tup):\n'
    jmou__upb += '  return ({}{})\n'.format(','.join(
        'bodo.utils.conversion.coerce_to_array(arr_tup[{}], use_nullable_array=True){}'
        .format(i, vlzg__uvt) for i in range(acv__gghb)), ',' if acv__gghb ==
        1 else '')
    vhiej__cjdka = {}
    exec(jmou__upb, {'bodo': bodo, 'out_dtype': krl__vkk}, vhiej__cjdka)
    ovoca__aqq = vhiej__cjdka['f']
    return ovoca__aqq


def nunique(A, dropna):
    return len(set(A))


def nunique_parallel(A, dropna):
    return len(set(A))


@overload(nunique, no_unliteral=True)
def nunique_overload(A, dropna):

    def nunique_seq(A, dropna):
        s, rtap__sjwa = build_set_seen_na(A)
        return len(s) + int(not dropna and rtap__sjwa)
    return nunique_seq


@overload(nunique_parallel, no_unliteral=True)
def nunique_overload_parallel(A, dropna):
    sum_op = bodo.libs.distributed_api.Reduce_Type.Sum.value

    def nunique_par(A, dropna):
        laxoz__xtpvz = bodo.libs.array_kernels.unique(A, dropna, parallel=True)
        lgy__pss = len(laxoz__xtpvz)
        return bodo.libs.distributed_api.dist_reduce(lgy__pss, np.int32(sum_op)
            )
    return nunique_par


def unique(A, dropna=False, parallel=False):
    return np.array([qtt__ztogj for qtt__ztogj in set(A)]).astype(A.dtype)


def cummin(A):
    return A


@overload(cummin, no_unliteral=True)
def cummin_overload(A):
    if isinstance(A.dtype, types.Float):
        zpj__rgl = np.finfo(A.dtype(1).dtype).max
    else:
        zpj__rgl = np.iinfo(A.dtype(1).dtype).max

    def impl(A):
        n = len(A)
        wqs__qxj = np.empty(n, A.dtype)
        pqcm__zthsc = zpj__rgl
        for i in range(n):
            pqcm__zthsc = min(pqcm__zthsc, A[i])
            wqs__qxj[i] = pqcm__zthsc
        return wqs__qxj
    return impl


def cummax(A):
    return A


@overload(cummax, no_unliteral=True)
def cummax_overload(A):
    if isinstance(A.dtype, types.Float):
        zpj__rgl = np.finfo(A.dtype(1).dtype).min
    else:
        zpj__rgl = np.iinfo(A.dtype(1).dtype).min

    def impl(A):
        n = len(A)
        wqs__qxj = np.empty(n, A.dtype)
        pqcm__zthsc = zpj__rgl
        for i in range(n):
            pqcm__zthsc = max(pqcm__zthsc, A[i])
            wqs__qxj[i] = pqcm__zthsc
        return wqs__qxj
    return impl


@overload(unique, no_unliteral=True)
def unique_overload(A, dropna=False, parallel=False):

    def unique_impl(A, dropna=False, parallel=False):
        dgw__ugg = arr_info_list_to_table([array_to_info(A)])
        eserc__zxk = 1
        yymj__ojhgf = 0
        ktlqi__jwfa = drop_duplicates_table(dgw__ugg, parallel, eserc__zxk,
            yymj__ojhgf, dropna, True)
        wqs__qxj = info_to_array(info_from_table(ktlqi__jwfa, 0), A)
        delete_table(dgw__ugg)
        delete_table(ktlqi__jwfa)
        return wqs__qxj
    return unique_impl


def explode(arr, index_arr):
    return pd.Series(arr, index_arr).explode()


@overload(explode, no_unliteral=True)
def overload_explode(arr, index_arr):
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type
    hbq__ddkw = bodo.utils.typing.to_nullable_type(arr.dtype)
    sgdsm__ozbp = index_arr
    knsub__trfx = sgdsm__ozbp.dtype

    def impl(arr, index_arr):
        n = len(arr)
        ikazr__wlg = init_nested_counts(hbq__ddkw)
        hhmc__gng = init_nested_counts(knsub__trfx)
        for i in range(n):
            hrpm__meif = index_arr[i]
            if isna(arr, i):
                ikazr__wlg = (ikazr__wlg[0] + 1,) + ikazr__wlg[1:]
                hhmc__gng = add_nested_counts(hhmc__gng, hrpm__meif)
                continue
            mco__brxf = arr[i]
            if len(mco__brxf) == 0:
                ikazr__wlg = (ikazr__wlg[0] + 1,) + ikazr__wlg[1:]
                hhmc__gng = add_nested_counts(hhmc__gng, hrpm__meif)
                continue
            ikazr__wlg = add_nested_counts(ikazr__wlg, mco__brxf)
            for ovxve__eoe in range(len(mco__brxf)):
                hhmc__gng = add_nested_counts(hhmc__gng, hrpm__meif)
        wqs__qxj = bodo.utils.utils.alloc_type(ikazr__wlg[0], hbq__ddkw,
            ikazr__wlg[1:])
        qkmkm__jmpd = bodo.utils.utils.alloc_type(ikazr__wlg[0],
            sgdsm__ozbp, hhmc__gng)
        jpx__fquyw = 0
        for i in range(n):
            if isna(arr, i):
                setna(wqs__qxj, jpx__fquyw)
                qkmkm__jmpd[jpx__fquyw] = index_arr[i]
                jpx__fquyw += 1
                continue
            mco__brxf = arr[i]
            ezly__wsk = len(mco__brxf)
            if ezly__wsk == 0:
                setna(wqs__qxj, jpx__fquyw)
                qkmkm__jmpd[jpx__fquyw] = index_arr[i]
                jpx__fquyw += 1
                continue
            wqs__qxj[jpx__fquyw:jpx__fquyw + ezly__wsk] = mco__brxf
            qkmkm__jmpd[jpx__fquyw:jpx__fquyw + ezly__wsk] = index_arr[i]
            jpx__fquyw += ezly__wsk
        return wqs__qxj, qkmkm__jmpd
    return impl


def explode_no_index(arr):
    return pd.Series(arr).explode()


@overload(explode_no_index, no_unliteral=True)
def overload_explode_no_index(arr, counts):
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type
    hbq__ddkw = bodo.utils.typing.to_nullable_type(arr.dtype)

    def impl(arr, counts):
        n = len(arr)
        ikazr__wlg = init_nested_counts(hbq__ddkw)
        for i in range(n):
            if isna(arr, i):
                ikazr__wlg = (ikazr__wlg[0] + 1,) + ikazr__wlg[1:]
                eoxl__kot = 1
            else:
                mco__brxf = arr[i]
                aip__zgr = len(mco__brxf)
                if aip__zgr == 0:
                    ikazr__wlg = (ikazr__wlg[0] + 1,) + ikazr__wlg[1:]
                    eoxl__kot = 1
                    continue
                else:
                    ikazr__wlg = add_nested_counts(ikazr__wlg, mco__brxf)
                    eoxl__kot = aip__zgr
            if counts[i] != eoxl__kot:
                raise ValueError(
                    'DataFrame.explode(): columns must have matching element counts'
                    )
        wqs__qxj = bodo.utils.utils.alloc_type(ikazr__wlg[0], hbq__ddkw,
            ikazr__wlg[1:])
        jpx__fquyw = 0
        for i in range(n):
            if isna(arr, i):
                setna(wqs__qxj, jpx__fquyw)
                jpx__fquyw += 1
                continue
            mco__brxf = arr[i]
            ezly__wsk = len(mco__brxf)
            if ezly__wsk == 0:
                setna(wqs__qxj, jpx__fquyw)
                jpx__fquyw += 1
                continue
            wqs__qxj[jpx__fquyw:jpx__fquyw + ezly__wsk] = mco__brxf
            jpx__fquyw += ezly__wsk
        return wqs__qxj
    return impl


def get_arr_lens(arr, na_empty_as_one=True):
    return [len(fmmi__utnlx) for fmmi__utnlx in arr]


@overload(get_arr_lens, inline='always', no_unliteral=True)
def overload_get_arr_lens(arr, na_empty_as_one=True):
    na_empty_as_one = get_overload_const_bool(na_empty_as_one)
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type or is_str_arr_type(arr
        ) and not na_empty_as_one, f'get_arr_lens: invalid input array type {arr}'
    if na_empty_as_one:
        ahmk__vuoac = 'np.empty(n, np.int64)'
        wya__mubu = 'out_arr[i] = 1'
        neyww__dqgf = 'max(len(arr[i]), 1)'
    else:
        ahmk__vuoac = 'bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)'
        wya__mubu = 'bodo.libs.array_kernels.setna(out_arr, i)'
        neyww__dqgf = 'len(arr[i])'
    jmou__upb = f"""def impl(arr, na_empty_as_one=True):
    numba.parfors.parfor.init_prange()
    n = len(arr)
    out_arr = {ahmk__vuoac}
    for i in numba.parfors.parfor.internal_prange(n):
        if bodo.libs.array_kernels.isna(arr, i):
            {wya__mubu}
        else:
            out_arr[i] = {neyww__dqgf}
    return out_arr
    """
    vhiej__cjdka = {}
    exec(jmou__upb, {'bodo': bodo, 'numba': numba, 'np': np}, vhiej__cjdka)
    impl = vhiej__cjdka['impl']
    return impl


def explode_str_split(arr, pat, n, index_arr):
    return pd.Series(arr, index_arr).str.split(pat, n).explode()


@overload(explode_str_split, no_unliteral=True)
def overload_explode_str_split(arr, pat, n, index_arr):
    assert is_str_arr_type(arr
        ), f'explode_str_split: string array expected, not {arr}'
    sgdsm__ozbp = index_arr
    knsub__trfx = sgdsm__ozbp.dtype

    def impl(arr, pat, n, index_arr):
        cfzpg__kat = pat is not None and len(pat) > 1
        if cfzpg__kat:
            nrkpv__noe = re.compile(pat)
            if n == -1:
                n = 0
        elif n == 0:
            n = -1
        vlq__tjvbm = len(arr)
        mgvwm__fsh = 0
        hxm__rhc = 0
        hhmc__gng = init_nested_counts(knsub__trfx)
        for i in range(vlq__tjvbm):
            hrpm__meif = index_arr[i]
            if bodo.libs.array_kernels.isna(arr, i):
                mgvwm__fsh += 1
                hhmc__gng = add_nested_counts(hhmc__gng, hrpm__meif)
                continue
            if cfzpg__kat:
                nsmc__pnzfs = nrkpv__noe.split(arr[i], maxsplit=n)
            else:
                nsmc__pnzfs = arr[i].split(pat, n)
            mgvwm__fsh += len(nsmc__pnzfs)
            for s in nsmc__pnzfs:
                hhmc__gng = add_nested_counts(hhmc__gng, hrpm__meif)
                hxm__rhc += bodo.libs.str_arr_ext.get_utf8_size(s)
        wqs__qxj = bodo.libs.str_arr_ext.pre_alloc_string_array(mgvwm__fsh,
            hxm__rhc)
        qkmkm__jmpd = bodo.utils.utils.alloc_type(mgvwm__fsh, sgdsm__ozbp,
            hhmc__gng)
        ycm__vcd = 0
        for cmjzq__czcgs in range(vlq__tjvbm):
            if isna(arr, cmjzq__czcgs):
                wqs__qxj[ycm__vcd] = ''
                bodo.libs.array_kernels.setna(wqs__qxj, ycm__vcd)
                qkmkm__jmpd[ycm__vcd] = index_arr[cmjzq__czcgs]
                ycm__vcd += 1
                continue
            if cfzpg__kat:
                nsmc__pnzfs = nrkpv__noe.split(arr[cmjzq__czcgs], maxsplit=n)
            else:
                nsmc__pnzfs = arr[cmjzq__czcgs].split(pat, n)
            vun__etam = len(nsmc__pnzfs)
            wqs__qxj[ycm__vcd:ycm__vcd + vun__etam] = nsmc__pnzfs
            qkmkm__jmpd[ycm__vcd:ycm__vcd + vun__etam] = index_arr[cmjzq__czcgs
                ]
            ycm__vcd += vun__etam
        return wqs__qxj, qkmkm__jmpd
    return impl


def gen_na_array(n, arr):
    return np.full(n, np.nan)


@overload(gen_na_array, no_unliteral=True)
def overload_gen_na_array(n, arr):
    if isinstance(arr, types.TypeRef):
        arr = arr.instance_type
    dtype = arr.dtype
    if isinstance(dtype, (types.Integer, types.Float)):
        dtype = dtype if isinstance(dtype, types.Float) else types.float64

        def impl_float(n, arr):
            numba.parfors.parfor.init_prange()
            wqs__qxj = np.empty(n, dtype)
            for i in numba.parfors.parfor.internal_prange(n):
                wqs__qxj[i] = np.nan
            return wqs__qxj
        return impl_float
    cssj__fimc = to_str_arr_if_dict_array(arr)

    def impl(n, arr):
        numba.parfors.parfor.init_prange()
        wqs__qxj = bodo.utils.utils.alloc_type(n, cssj__fimc, (0,))
        for i in numba.parfors.parfor.internal_prange(n):
            setna(wqs__qxj, i)
        return wqs__qxj
    return impl


def gen_na_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


ArrayAnalysis._analyze_op_call_bodo_libs_array_kernels_gen_na_array = (
    gen_na_array_equiv)


def resize_and_copy(A, new_len):
    return A


@overload(resize_and_copy, no_unliteral=True)
def overload_resize_and_copy(A, old_size, new_len):
    kmjqw__jmr = A
    if A == types.Array(types.uint8, 1, 'C'):

        def impl_char(A, old_size, new_len):
            wqs__qxj = bodo.utils.utils.alloc_type(new_len, kmjqw__jmr)
            bodo.libs.str_arr_ext.str_copy_ptr(wqs__qxj.ctypes, 0, A.ctypes,
                old_size)
            return wqs__qxj
        return impl_char

    def impl(A, old_size, new_len):
        wqs__qxj = bodo.utils.utils.alloc_type(new_len, kmjqw__jmr, (-1,))
        wqs__qxj[:old_size] = A[:old_size]
        return wqs__qxj
    return impl


@register_jitable
def calc_nitems(start, stop, step):
    pyuq__osgv = math.ceil((stop - start) / step)
    return int(max(pyuq__osgv, 0))


def calc_nitems_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 3 and not kws
    if guard(find_const, self.func_ir, args[0]) == 0 and guard(find_const,
        self.func_ir, args[2]) == 1:
        return ArrayAnalysis.AnalyzeResult(shape=args[1], pre=[])


ArrayAnalysis._analyze_op_call_bodo_libs_array_kernels_calc_nitems = (
    calc_nitems_equiv)


def arange_parallel_impl(return_type, *args):
    dtype = as_dtype(return_type.dtype)

    def arange_1(stop):
        return np.arange(0, stop, 1, dtype)

    def arange_2(start, stop):
        return np.arange(start, stop, 1, dtype)

    def arange_3(start, stop, step):
        return np.arange(start, stop, step, dtype)
    if any(isinstance(qtt__ztogj, types.Complex) for qtt__ztogj in args):

        def arange_4(start, stop, step, dtype):
            numba.parfors.parfor.init_prange()
            wndi__jmpg = (stop - start) / step
            pyuq__osgv = math.ceil(wndi__jmpg.real)
            hxck__qfsmk = math.ceil(wndi__jmpg.imag)
            jvrkc__qytuj = int(max(min(hxck__qfsmk, pyuq__osgv), 0))
            arr = np.empty(jvrkc__qytuj, dtype)
            for i in numba.parfors.parfor.internal_prange(jvrkc__qytuj):
                arr[i] = start + i * step
            return arr
    else:

        def arange_4(start, stop, step, dtype):
            numba.parfors.parfor.init_prange()
            jvrkc__qytuj = bodo.libs.array_kernels.calc_nitems(start, stop,
                step)
            arr = np.empty(jvrkc__qytuj, dtype)
            for i in numba.parfors.parfor.internal_prange(jvrkc__qytuj):
                arr[i] = start + i * step
            return arr
    if len(args) == 1:
        return arange_1
    elif len(args) == 2:
        return arange_2
    elif len(args) == 3:
        return arange_3
    elif len(args) == 4:
        return arange_4
    else:
        raise BodoError('parallel arange with types {}'.format(args))


if bodo.numba_compat._check_numba_change:
    lines = inspect.getsource(numba.parfors.parfor.arange_parallel_impl)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'c72b0390b4f3e52dcc5426bd42c6b55ff96bae5a425381900985d36e7527a4bd':
        warnings.warn('numba.parfors.parfor.arange_parallel_impl has changed')
numba.parfors.parfor.swap_functions_map['arange', 'numpy'
    ] = arange_parallel_impl


def sort(arr, ascending, inplace):
    return np.sort(arr)


@overload(sort, no_unliteral=True)
def overload_sort(arr, ascending, inplace):

    def impl(arr, ascending, inplace):
        n = len(arr)
        data = np.arange(n),
        qvtd__vbmn = arr,
        if not inplace:
            qvtd__vbmn = arr.copy(),
        jwkfr__gbf = bodo.libs.str_arr_ext.to_list_if_immutable_arr(qvtd__vbmn)
        vng__bupe = bodo.libs.str_arr_ext.to_list_if_immutable_arr(data, True)
        bodo.libs.timsort.sort(jwkfr__gbf, 0, n, vng__bupe)
        if not ascending:
            bodo.libs.timsort.reverseRange(jwkfr__gbf, 0, n, vng__bupe)
        bodo.libs.str_arr_ext.cp_str_list_to_array(qvtd__vbmn, jwkfr__gbf)
        return qvtd__vbmn[0]
    return impl


def overload_array_max(A):
    if isinstance(A, IntegerArrayType) or A == boolean_array:

        def impl(A):
            return pd.Series(A).max()
        return impl


overload(np.max, inline='always', no_unliteral=True)(overload_array_max)
overload(max, inline='always', no_unliteral=True)(overload_array_max)


def overload_array_min(A):
    if isinstance(A, IntegerArrayType) or A == boolean_array:

        def impl(A):
            return pd.Series(A).min()
        return impl


overload(np.min, inline='always', no_unliteral=True)(overload_array_min)
overload(min, inline='always', no_unliteral=True)(overload_array_min)


def overload_array_sum(A):
    if isinstance(A, IntegerArrayType) or A == boolean_array:

        def impl(A):
            return pd.Series(A).sum()
    return impl


overload(np.sum, inline='always', no_unliteral=True)(overload_array_sum)
overload(sum, inline='always', no_unliteral=True)(overload_array_sum)


@overload(np.prod, inline='always', no_unliteral=True)
def overload_array_prod(A):
    if isinstance(A, IntegerArrayType) or A == boolean_array:

        def impl(A):
            return pd.Series(A).prod()
    return impl


def nonzero(arr):
    return arr,


@overload(nonzero, no_unliteral=True)
def nonzero_overload(A, parallel=False):
    if not bodo.utils.utils.is_array_typ(A, False):
        return

    def impl(A, parallel=False):
        n = len(A)
        if parallel:
            offset = bodo.libs.distributed_api.dist_exscan(n, Reduce_Type.
                Sum.value)
        else:
            offset = 0
        wit__rcd = []
        for i in range(n):
            if A[i]:
                wit__rcd.append(i + offset)
        return np.array(wit__rcd, np.int64),
    return impl


def ffill_bfill_arr(arr):
    return arr


@overload(ffill_bfill_arr, no_unliteral=True)
def ffill_bfill_overload(A, method, parallel=False):
    kmjqw__jmr = element_type(A)
    if kmjqw__jmr == types.unicode_type:
        null_value = '""'
    elif kmjqw__jmr == types.bool_:
        null_value = 'False'
    elif kmjqw__jmr == bodo.datetime64ns:
        null_value = (
            'bodo.utils.conversion.unbox_if_timestamp(pd.to_datetime(0))')
    elif kmjqw__jmr == bodo.timedelta64ns:
        null_value = (
            'bodo.utils.conversion.unbox_if_timestamp(pd.to_timedelta(0))')
    else:
        null_value = '0'
    ycm__vcd = 'i'
    tsbf__vfpe = False
    pwow__wkkpy = get_overload_const_str(method)
    if pwow__wkkpy in ('ffill', 'pad'):
        tbn__jmcwo = 'n'
        send_right = True
    elif pwow__wkkpy in ('backfill', 'bfill'):
        tbn__jmcwo = 'n-1, -1, -1'
        send_right = False
        if kmjqw__jmr == types.unicode_type:
            ycm__vcd = '(n - 1) - i'
            tsbf__vfpe = True
    jmou__upb = 'def impl(A, method, parallel=False):\n'
    jmou__upb += '  A = decode_if_dict_array(A)\n'
    jmou__upb += '  has_last_value = False\n'
    jmou__upb += f'  last_value = {null_value}\n'
    jmou__upb += '  if parallel:\n'
    jmou__upb += '    rank = bodo.libs.distributed_api.get_rank()\n'
    jmou__upb += '    n_pes = bodo.libs.distributed_api.get_size()\n'
    jmou__upb += f"""    has_last_value, last_value = null_border_icomm(A, rank, n_pes, {null_value}, {send_right})
"""
    jmou__upb += '  n = len(A)\n'
    jmou__upb += '  out_arr = bodo.utils.utils.alloc_type(n, A, (-1,))\n'
    jmou__upb += f'  for i in range({tbn__jmcwo}):\n'
    jmou__upb += (
        '    if (bodo.libs.array_kernels.isna(A, i) and not has_last_value):\n'
        )
    jmou__upb += f'      bodo.libs.array_kernels.setna(out_arr, {ycm__vcd})\n'
    jmou__upb += '      continue\n'
    jmou__upb += '    s = A[i]\n'
    jmou__upb += '    if bodo.libs.array_kernels.isna(A, i):\n'
    jmou__upb += '      s = last_value\n'
    jmou__upb += f'    out_arr[{ycm__vcd}] = s\n'
    jmou__upb += '    last_value = s\n'
    jmou__upb += '    has_last_value = True\n'
    if tsbf__vfpe:
        jmou__upb += '  return out_arr[::-1]\n'
    else:
        jmou__upb += '  return out_arr\n'
    glvd__jfg = {}
    exec(jmou__upb, {'bodo': bodo, 'numba': numba, 'pd': pd,
        'null_border_icomm': null_border_icomm, 'decode_if_dict_array':
        decode_if_dict_array}, glvd__jfg)
    impl = glvd__jfg['impl']
    return impl


@register_jitable(cache=True)
def null_border_icomm(in_arr, rank, n_pes, null_value, send_right=True):
    if send_right:
        gya__idfi = 0
        ajg__xijm = n_pes - 1
        wna__zmknd = np.int32(rank + 1)
        nze__arvcv = np.int32(rank - 1)
        woak__iad = len(in_arr) - 1
        qjhvf__hjcre = -1
        fwb__nui = -1
    else:
        gya__idfi = n_pes - 1
        ajg__xijm = 0
        wna__zmknd = np.int32(rank - 1)
        nze__arvcv = np.int32(rank + 1)
        woak__iad = 0
        qjhvf__hjcre = len(in_arr)
        fwb__nui = 1
    sxu__pwhtg = np.int32(bodo.hiframes.rolling.comm_border_tag)
    qnqn__otmxv = np.empty(1, dtype=np.bool_)
    banb__xgin = bodo.utils.utils.alloc_type(1, in_arr, (-1,))
    fdyp__esnq = np.empty(1, dtype=np.bool_)
    upmgl__hxnoq = bodo.utils.utils.alloc_type(1, in_arr, (-1,))
    bhxh__vlvg = False
    svi__bqu = null_value
    for i in range(woak__iad, qjhvf__hjcre, fwb__nui):
        if not isna(in_arr, i):
            bhxh__vlvg = True
            svi__bqu = in_arr[i]
            break
    if rank != gya__idfi:
        nhnp__mvi = bodo.libs.distributed_api.irecv(qnqn__otmxv, 1,
            nze__arvcv, sxu__pwhtg, True)
        bodo.libs.distributed_api.wait(nhnp__mvi, True)
        bun__reg = bodo.libs.distributed_api.irecv(banb__xgin, 1,
            nze__arvcv, sxu__pwhtg, True)
        bodo.libs.distributed_api.wait(bun__reg, True)
        yzmus__cva = qnqn__otmxv[0]
        wtlj__efyp = banb__xgin[0]
    else:
        yzmus__cva = False
        wtlj__efyp = null_value
    if bhxh__vlvg:
        fdyp__esnq[0] = bhxh__vlvg
        upmgl__hxnoq[0] = svi__bqu
    else:
        fdyp__esnq[0] = yzmus__cva
        upmgl__hxnoq[0] = wtlj__efyp
    if rank != ajg__xijm:
        aer__jhvp = bodo.libs.distributed_api.isend(fdyp__esnq, 1,
            wna__zmknd, sxu__pwhtg, True)
        kib__vtq = bodo.libs.distributed_api.isend(upmgl__hxnoq, 1,
            wna__zmknd, sxu__pwhtg, True)
    return yzmus__cva, wtlj__efyp


@overload(np.sort, inline='always', no_unliteral=True)
def np_sort(A, axis=-1, kind=None, order=None):
    if not bodo.utils.utils.is_array_typ(A, False) or isinstance(A, types.Array
        ):
        return
    lzbp__jjwx = {'axis': axis, 'kind': kind, 'order': order}
    inaxd__foyo = {'axis': -1, 'kind': None, 'order': None}
    check_unsupported_args('np.sort', lzbp__jjwx, inaxd__foyo, 'numpy')

    def impl(A, axis=-1, kind=None, order=None):
        return pd.Series(A).sort_values().values
    return impl


def repeat_kernel(A, repeats):
    return A


@overload(repeat_kernel, no_unliteral=True)
def repeat_kernel_overload(A, repeats):
    kmjqw__jmr = to_str_arr_if_dict_array(A)
    if isinstance(repeats, types.Integer):

        def impl_int(A, repeats):
            A = decode_if_dict_array(A)
            vlq__tjvbm = len(A)
            wqs__qxj = bodo.utils.utils.alloc_type(vlq__tjvbm * repeats,
                kmjqw__jmr, (-1,))
            for i in range(vlq__tjvbm):
                ycm__vcd = i * repeats
                if bodo.libs.array_kernels.isna(A, i):
                    for cmjzq__czcgs in range(repeats):
                        bodo.libs.array_kernels.setna(wqs__qxj, ycm__vcd +
                            cmjzq__czcgs)
                else:
                    wqs__qxj[ycm__vcd:ycm__vcd + repeats] = A[i]
            return wqs__qxj
        return impl_int

    def impl_arr(A, repeats):
        A = decode_if_dict_array(A)
        vlq__tjvbm = len(A)
        wqs__qxj = bodo.utils.utils.alloc_type(repeats.sum(), kmjqw__jmr, (-1,)
            )
        ycm__vcd = 0
        for i in range(vlq__tjvbm):
            xqq__kosnd = repeats[i]
            if bodo.libs.array_kernels.isna(A, i):
                for cmjzq__czcgs in range(xqq__kosnd):
                    bodo.libs.array_kernels.setna(wqs__qxj, ycm__vcd +
                        cmjzq__czcgs)
            else:
                wqs__qxj[ycm__vcd:ycm__vcd + xqq__kosnd] = A[i]
            ycm__vcd += xqq__kosnd
        return wqs__qxj
    return impl_arr


@overload(np.repeat, inline='always', no_unliteral=True)
def np_repeat(A, repeats):
    if not bodo.utils.utils.is_array_typ(A, False) or isinstance(A, types.Array
        ):
        return
    if not isinstance(repeats, types.Integer):
        raise BodoError(
            'Only integer type supported for repeats in np.repeat()')

    def impl(A, repeats):
        return bodo.libs.array_kernels.repeat_kernel(A, repeats)
    return impl


@overload(np.unique, inline='always', no_unliteral=True)
def np_unique(A):
    if not bodo.utils.utils.is_array_typ(A, False) or isinstance(A, types.Array
        ):
        return

    def impl(A):
        ixx__yzoj = bodo.libs.array_kernels.unique(A)
        return bodo.allgatherv(ixx__yzoj, False)
    return impl


@overload(np.union1d, inline='always', no_unliteral=True)
def overload_union1d(A1, A2):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.union1d()')

    def impl(A1, A2):
        kglhv__yrq = bodo.libs.array_kernels.concat([A1, A2])
        yryfn__tuep = bodo.libs.array_kernels.unique(kglhv__yrq)
        return pd.Series(yryfn__tuep).sort_values().values
    return impl


@overload(np.intersect1d, inline='always', no_unliteral=True)
def overload_intersect1d(A1, A2, assume_unique=False, return_indices=False):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    lzbp__jjwx = {'assume_unique': assume_unique, 'return_indices':
        return_indices}
    inaxd__foyo = {'assume_unique': False, 'return_indices': False}
    check_unsupported_args('np.intersect1d', lzbp__jjwx, inaxd__foyo, 'numpy')
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.intersect1d()'
            )
    if A1.ndim != 1 or A2.ndim != 1:
        raise BodoError('Only 1D arrays supported in np.intersect1d()')

    def impl(A1, A2, assume_unique=False, return_indices=False):
        apja__som = bodo.libs.array_kernels.unique(A1)
        cbcfe__moxbk = bodo.libs.array_kernels.unique(A2)
        kglhv__yrq = bodo.libs.array_kernels.concat([apja__som, cbcfe__moxbk])
        adqz__aoi = pd.Series(kglhv__yrq).sort_values().values
        return slice_array_intersect1d(adqz__aoi)
    return impl


@register_jitable
def slice_array_intersect1d(arr):
    qcq__nyv = arr[1:] == arr[:-1]
    return arr[:-1][qcq__nyv]


@overload(np.setdiff1d, inline='always', no_unliteral=True)
def overload_setdiff1d(A1, A2, assume_unique=False):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    lzbp__jjwx = {'assume_unique': assume_unique}
    inaxd__foyo = {'assume_unique': False}
    check_unsupported_args('np.setdiff1d', lzbp__jjwx, inaxd__foyo, 'numpy')
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.setdiff1d()')
    if A1.ndim != 1 or A2.ndim != 1:
        raise BodoError('Only 1D arrays supported in np.setdiff1d()')

    def impl(A1, A2, assume_unique=False):
        apja__som = bodo.libs.array_kernels.unique(A1)
        cbcfe__moxbk = bodo.libs.array_kernels.unique(A2)
        qcq__nyv = calculate_mask_setdiff1d(apja__som, cbcfe__moxbk)
        return pd.Series(apja__som[qcq__nyv]).sort_values().values
    return impl


@register_jitable
def calculate_mask_setdiff1d(A1, A2):
    qcq__nyv = np.ones(len(A1), np.bool_)
    for i in range(len(A2)):
        qcq__nyv &= A1 != A2[i]
    return qcq__nyv


@overload(np.linspace, inline='always', no_unliteral=True)
def np_linspace(start, stop, num=50, endpoint=True, retstep=False, dtype=
    None, axis=0):
    lzbp__jjwx = {'retstep': retstep, 'axis': axis}
    inaxd__foyo = {'retstep': False, 'axis': 0}
    check_unsupported_args('np.linspace', lzbp__jjwx, inaxd__foyo, 'numpy')
    xiif__clzt = False
    if is_overload_none(dtype):
        kmjqw__jmr = np.promote_types(np.promote_types(numba.np.
            numpy_support.as_dtype(start), numba.np.numpy_support.as_dtype(
            stop)), numba.np.numpy_support.as_dtype(types.float64)).type
    else:
        if isinstance(dtype.dtype, types.Integer):
            xiif__clzt = True
        kmjqw__jmr = numba.np.numpy_support.as_dtype(dtype).type
    if xiif__clzt:

        def impl_int(start, stop, num=50, endpoint=True, retstep=False,
            dtype=None, axis=0):
            bdti__gzvm = np_linspace_get_stepsize(start, stop, num, endpoint)
            numba.parfors.parfor.init_prange()
            wqs__qxj = np.empty(num, kmjqw__jmr)
            for i in numba.parfors.parfor.internal_prange(num):
                wqs__qxj[i] = kmjqw__jmr(np.floor(start + i * bdti__gzvm))
            return wqs__qxj
        return impl_int
    else:

        def impl(start, stop, num=50, endpoint=True, retstep=False, dtype=
            None, axis=0):
            bdti__gzvm = np_linspace_get_stepsize(start, stop, num, endpoint)
            numba.parfors.parfor.init_prange()
            wqs__qxj = np.empty(num, kmjqw__jmr)
            for i in numba.parfors.parfor.internal_prange(num):
                wqs__qxj[i] = kmjqw__jmr(start + i * bdti__gzvm)
            return wqs__qxj
        return impl


def np_linspace_get_stepsize(start, stop, num, endpoint):
    return 0


@overload(np_linspace_get_stepsize, no_unliteral=True)
def overload_np_linspace_get_stepsize(start, stop, num, endpoint):

    def impl(start, stop, num, endpoint):
        if num < 0:
            raise ValueError('np.linspace() Num must be >= 0')
        if endpoint:
            num -= 1
        if num > 1:
            return (stop - start) / num
        return 0
    return impl


@overload(operator.contains, no_unliteral=True)
def arr_contains(A, val):
    if not (bodo.utils.utils.is_array_typ(A, False) and A.dtype == types.
        unliteral(val)):
        return

    def impl(A, val):
        numba.parfors.parfor.init_prange()
        acv__gghb = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                acv__gghb += A[i] == val
        return acv__gghb > 0
    return impl


@overload(np.any, inline='always', no_unliteral=True)
def np_any(A, axis=None, out=None, keepdims=None):
    if not (bodo.utils.utils.is_array_typ(A, False) and A.ndim == 1):
        return
    lzbp__jjwx = {'axis': axis, 'out': out, 'keepdims': keepdims}
    inaxd__foyo = {'axis': None, 'out': None, 'keepdims': None}
    check_unsupported_args('np.any', lzbp__jjwx, inaxd__foyo, 'numpy')

    def impl(A, axis=None, out=None, keepdims=None):
        numba.parfors.parfor.init_prange()
        acv__gghb = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                acv__gghb += int(bool(A[i]))
        return acv__gghb > 0
    return impl


@overload(np.all, inline='always', no_unliteral=True)
def np_all(A, axis=None, out=None, keepdims=None):
    if not (bodo.utils.utils.is_array_typ(A, False) and A.ndim == 1):
        return
    lzbp__jjwx = {'axis': axis, 'out': out, 'keepdims': keepdims}
    inaxd__foyo = {'axis': None, 'out': None, 'keepdims': None}
    check_unsupported_args('np.any', lzbp__jjwx, inaxd__foyo, 'numpy')

    def impl(A, axis=None, out=None, keepdims=None):
        numba.parfors.parfor.init_prange()
        acv__gghb = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                acv__gghb += int(bool(A[i]))
        return acv__gghb == n
    return impl


@overload(np.cbrt, inline='always', no_unliteral=True)
def np_cbrt(A, out=None, where=True, casting='same_kind', order='K', dtype=
    None, subok=True):
    if not (isinstance(A, types.Number) or bodo.utils.utils.is_array_typ(A,
        False) and A.ndim == 1 and isinstance(A.dtype, types.Number)):
        return
    lzbp__jjwx = {'out': out, 'where': where, 'casting': casting, 'order':
        order, 'dtype': dtype, 'subok': subok}
    inaxd__foyo = {'out': None, 'where': True, 'casting': 'same_kind',
        'order': 'K', 'dtype': None, 'subok': True}
    check_unsupported_args('np.cbrt', lzbp__jjwx, inaxd__foyo, 'numpy')
    if bodo.utils.utils.is_array_typ(A, False):
        vebp__wfvn = np.promote_types(numba.np.numpy_support.as_dtype(A.
            dtype), numba.np.numpy_support.as_dtype(types.float32)).type

        def impl_arr(A, out=None, where=True, casting='same_kind', order=
            'K', dtype=None, subok=True):
            numba.parfors.parfor.init_prange()
            n = len(A)
            wqs__qxj = np.empty(n, vebp__wfvn)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(A, i):
                    bodo.libs.array_kernels.setna(wqs__qxj, i)
                    continue
                wqs__qxj[i] = np_cbrt_scalar(A[i], vebp__wfvn)
            return wqs__qxj
        return impl_arr
    vebp__wfvn = np.promote_types(numba.np.numpy_support.as_dtype(A), numba
        .np.numpy_support.as_dtype(types.float32)).type

    def impl_scalar(A, out=None, where=True, casting='same_kind', order='K',
        dtype=None, subok=True):
        return np_cbrt_scalar(A, vebp__wfvn)
    return impl_scalar


@register_jitable
def np_cbrt_scalar(x, float_dtype):
    if np.isnan(x):
        return np.nan
    ikeji__nmfnw = x < 0
    if ikeji__nmfnw:
        x = -x
    res = np.power(float_dtype(x), 1.0 / 3.0)
    if ikeji__nmfnw:
        return -res
    return res


@overload(np.hstack, no_unliteral=True)
def np_hstack(tup):
    pqvl__zyihu = isinstance(tup, (types.BaseTuple, types.List))
    prea__mikqd = isinstance(tup, (bodo.SeriesType, bodo.hiframes.
        pd_series_ext.HeterogeneousSeriesType)) and isinstance(tup.data, (
        types.BaseTuple, types.List, bodo.NullableTupleType))
    if isinstance(tup, types.BaseTuple):
        for yne__yrpq in tup.types:
            pqvl__zyihu = pqvl__zyihu and bodo.utils.utils.is_array_typ(
                yne__yrpq, False)
    elif isinstance(tup, types.List):
        pqvl__zyihu = bodo.utils.utils.is_array_typ(tup.dtype, False)
    elif prea__mikqd:
        zbk__jngev = tup.data.tuple_typ if isinstance(tup.data, bodo.
            NullableTupleType) else tup.data
        for yne__yrpq in zbk__jngev.types:
            prea__mikqd = prea__mikqd and bodo.utils.utils.is_array_typ(
                yne__yrpq, False)
    if not (pqvl__zyihu or prea__mikqd):
        return
    if prea__mikqd:

        def impl_series(tup):
            arr_tup = bodo.hiframes.pd_series_ext.get_series_data(tup)
            return bodo.libs.array_kernels.concat(arr_tup)
        return impl_series

    def impl(tup):
        return bodo.libs.array_kernels.concat(tup)
    return impl


@overload(np.random.multivariate_normal, inline='always', no_unliteral=True)
def np_random_multivariate_normal(mean, cov, size=None, check_valid='warn',
    tol=1e-08):
    lzbp__jjwx = {'check_valid': check_valid, 'tol': tol}
    inaxd__foyo = {'check_valid': 'warn', 'tol': 1e-08}
    check_unsupported_args('np.random.multivariate_normal', lzbp__jjwx,
        inaxd__foyo, 'numpy')
    if not isinstance(size, types.Integer):
        raise BodoError(
            'np.random.multivariate_normal() size argument is required and must be an integer'
            )
    if not (bodo.utils.utils.is_array_typ(mean, False) and mean.ndim == 1):
        raise BodoError(
            'np.random.multivariate_normal() mean must be a 1 dimensional numpy array'
            )
    if not (bodo.utils.utils.is_array_typ(cov, False) and cov.ndim == 2):
        raise BodoError(
            'np.random.multivariate_normal() cov must be a 2 dimensional square, numpy array'
            )

    def impl(mean, cov, size=None, check_valid='warn', tol=1e-08):
        _validate_multivar_norm(cov)
        qkcf__deus = mean.shape[0]
        lxt__yexm = size, qkcf__deus
        gxh__vxzj = np.random.standard_normal(lxt__yexm)
        cov = cov.astype(np.float64)
        apwji__urbs, s, ztbkv__ftnj = np.linalg.svd(cov)
        res = np.dot(gxh__vxzj, np.sqrt(s).reshape(qkcf__deus, 1) * ztbkv__ftnj
            )
        wdte__uezkc = res + mean
        return wdte__uezkc
    return impl


def _validate_multivar_norm(cov):
    return


@overload(_validate_multivar_norm, no_unliteral=True)
def _overload_validate_multivar_norm(cov):

    def impl(cov):
        if cov.shape[0] != cov.shape[1]:
            raise ValueError(
                'np.random.multivariate_normal() cov must be a 2 dimensional square, numpy array'
                )
    return impl


def _nan_argmin(arr):
    return


@overload(_nan_argmin, no_unliteral=True)
def _overload_nan_argmin(arr):
    if isinstance(arr, IntegerArrayType) or arr in [boolean_array,
        datetime_date_array_type] or arr.dtype == bodo.timedelta64ns:

        def impl_bodo_arr(arr):
            numba.parfors.parfor.init_prange()
            igh__ywct = bodo.hiframes.series_kernels._get_type_max_value(arr)
            eha__izjif = typing.builtins.IndexValue(-1, igh__ywct)
            for i in numba.parfors.parfor.internal_prange(len(arr)):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                nxslq__mlj = typing.builtins.IndexValue(i, arr[i])
                eha__izjif = min(eha__izjif, nxslq__mlj)
            return eha__izjif.index
        return impl_bodo_arr
    if isinstance(arr, CategoricalArrayType):
        assert arr.dtype.ordered, 'Categorical Array must be ordered to select an argmin'
        yzlia__yakc = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            arr.dtype)

        def impl_cat_arr(arr):
            nhgo__osy = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            igh__ywct = yzlia__yakc(len(arr.dtype.categories) + 1)
            eha__izjif = typing.builtins.IndexValue(-1, igh__ywct)
            for i in numba.parfors.parfor.internal_prange(len(arr)):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                nxslq__mlj = typing.builtins.IndexValue(i, nhgo__osy[i])
                eha__izjif = min(eha__izjif, nxslq__mlj)
            return eha__izjif.index
        return impl_cat_arr
    return lambda arr: arr.argmin()


def _nan_argmax(arr):
    return


@overload(_nan_argmax, no_unliteral=True)
def _overload_nan_argmax(arr):
    if isinstance(arr, IntegerArrayType) or arr in [boolean_array,
        datetime_date_array_type] or arr.dtype == bodo.timedelta64ns:

        def impl_bodo_arr(arr):
            n = len(arr)
            numba.parfors.parfor.init_prange()
            igh__ywct = bodo.hiframes.series_kernels._get_type_min_value(arr)
            eha__izjif = typing.builtins.IndexValue(-1, igh__ywct)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                nxslq__mlj = typing.builtins.IndexValue(i, arr[i])
                eha__izjif = max(eha__izjif, nxslq__mlj)
            return eha__izjif.index
        return impl_bodo_arr
    if isinstance(arr, CategoricalArrayType):
        assert arr.dtype.ordered, 'Categorical Array must be ordered to select an argmin'
        yzlia__yakc = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            arr.dtype)

        def impl_cat_arr(arr):
            n = len(arr)
            nhgo__osy = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            igh__ywct = yzlia__yakc(-1)
            eha__izjif = typing.builtins.IndexValue(-1, igh__ywct)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                nxslq__mlj = typing.builtins.IndexValue(i, nhgo__osy[i])
                eha__izjif = max(eha__izjif, nxslq__mlj)
            return eha__izjif.index
        return impl_cat_arr
    return lambda arr: arr.argmax()


@overload_attribute(types.Array, 'nbytes', inline='always')
def overload_dataframe_index(A):
    return lambda A: A.size * bodo.io.np_io.get_dtype_size(A.dtype)
