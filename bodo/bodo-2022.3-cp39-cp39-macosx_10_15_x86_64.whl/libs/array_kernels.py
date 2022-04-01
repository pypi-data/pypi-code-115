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
from bodo.libs.pd_datetime_arr_ext import DatetimeArrayType
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
    if isinstance(arr, DatetimeArrayType):
        return lambda arr, i: np.isnat(arr._data[i])
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
        omnnn__brrb = arr.dtype('NaT')

        def _setnan_impl(arr, ind, int_nan_const=0):
            arr[ind] = omnnn__brrb
        return _setnan_impl
    if isinstance(arr, DatetimeArrayType):
        omnnn__brrb = bodo.datetime64ns('NaT')

        def _setnan_impl(arr, ind, int_nan_const=0):
            arr._data[ind] = omnnn__brrb
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
            rjabb__erjnh = bodo.libs.array_item_arr_ext.get_offsets(arr._data)
            rjabb__erjnh[ind + 1] = rjabb__erjnh[ind]
            bodo.libs.int_arr_ext.set_bit_to_arr(bodo.libs.
                array_item_arr_ext.get_null_bitmap(arr._data), ind, 0)
        return impl_binary_arr
    if isinstance(arr, bodo.libs.array_item_arr_ext.ArrayItemArrayType):

        def impl_arr_item(arr, ind, int_nan_const=0):
            rjabb__erjnh = bodo.libs.array_item_arr_ext.get_offsets(arr)
            rjabb__erjnh[ind + 1] = rjabb__erjnh[ind]
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
    lebd__lkc = arr_tup.count
    ldhhg__aahpu = 'def f(arr_tup, ind, int_nan_const=0):\n'
    for i in range(lebd__lkc):
        ldhhg__aahpu += '  setna(arr_tup[{}], ind, int_nan_const)\n'.format(i)
    ldhhg__aahpu += '  return\n'
    rku__lpej = {}
    exec(ldhhg__aahpu, {'setna': setna}, rku__lpej)
    impl = rku__lpej['f']
    return impl


def setna_slice(arr, s):
    arr[s] = np.nan


@overload(setna_slice, no_unliteral=True)
def overload_setna_slice(arr, s):

    def impl(arr, s):
        gkcsa__bdn = numba.cpython.unicode._normalize_slice(s, len(arr))
        for i in range(gkcsa__bdn.start, gkcsa__bdn.stop, gkcsa__bdn.step):
            setna(arr, i)
    return impl


@numba.generated_jit
def first_last_valid_index(arr, index_arr, is_first=True, parallel=False):
    is_first = get_overload_const_bool(is_first)
    if is_first:
        cgbu__ltlf = 'n'
    else:
        cgbu__ltlf = 'n-1, -1, -1'
    ldhhg__aahpu = f"""def impl(arr, index_arr, is_first=True, parallel=False):
    n = len(arr)
    index_val = index_arr[0]
    has_valid = False
    loc_min = -1
    if parallel:
        rank = bodo.libs.distributed_api.get_rank()
        n_pes = bodo.libs.distributed_api.get_size()
        loc_min = n_pes
    for i in range({cgbu__ltlf}):
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
    rku__lpej = {}
    exec(ldhhg__aahpu, {'np': np, 'bodo': bodo, 'isna': isna, 'min_op':
        min_op, 'box_if_dt64': bodo.utils.conversion.box_if_dt64}, rku__lpej)
    impl = rku__lpej['impl']
    return impl


ll.add_symbol('median_series_computation', quantile_alg.
    median_series_computation)
_median_series_computation = types.ExternalFunction('median_series_computation'
    , types.void(types.voidptr, bodo.libs.array.array_info_type, types.
    bool_, types.bool_))


@numba.njit
def median_series_computation(res, arr, is_parallel, skipna):
    izdj__hwch = array_to_info(arr)
    _median_series_computation(res, izdj__hwch, is_parallel, skipna)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(izdj__hwch)


ll.add_symbol('autocorr_series_computation', quantile_alg.
    autocorr_series_computation)
_autocorr_series_computation = types.ExternalFunction(
    'autocorr_series_computation', types.void(types.voidptr, bodo.libs.
    array.array_info_type, types.int64, types.bool_))


@numba.njit
def autocorr_series_computation(res, arr, lag, is_parallel):
    izdj__hwch = array_to_info(arr)
    _autocorr_series_computation(res, izdj__hwch, lag, is_parallel)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(izdj__hwch)


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
    izdj__hwch = array_to_info(arr)
    _compute_series_monotonicity(res, izdj__hwch, inc_dec, is_parallel)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(izdj__hwch)


@numba.njit
def series_monotonicity(arr, inc_dec, parallel=False):
    res = np.empty(1, types.float64)
    series_monotonicity_call(res.ctypes, arr, inc_dec, parallel)
    bjtu__aeren = res[0] > 0.5
    return bjtu__aeren


@numba.generated_jit(nopython=True)
def get_valid_entries_from_date_offset(index_arr, offset, initial_date,
    is_last, is_parallel=False):
    if get_overload_const_bool(is_last):
        xrx__dyckf = '-'
        fpjtk__kkizf = 'index_arr[0] > threshhold_date'
        cgbu__ltlf = '1, n+1'
        xtdtm__jwtp = 'index_arr[-i] <= threshhold_date'
        ggfgu__wlde = 'i - 1'
    else:
        xrx__dyckf = '+'
        fpjtk__kkizf = 'index_arr[-1] < threshhold_date'
        cgbu__ltlf = 'n'
        xtdtm__jwtp = 'index_arr[i] >= threshhold_date'
        ggfgu__wlde = 'i'
    ldhhg__aahpu = (
        'def impl(index_arr, offset, initial_date, is_last, is_parallel=False):\n'
        )
    if types.unliteral(offset) == types.unicode_type:
        ldhhg__aahpu += (
            '  with numba.objmode(threshhold_date=bodo.pd_timestamp_type):\n')
        ldhhg__aahpu += (
            '    date_offset = pd.tseries.frequencies.to_offset(offset)\n')
        if not get_overload_const_bool(is_last):
            ldhhg__aahpu += """    if not isinstance(date_offset, pd._libs.tslibs.Tick) and date_offset.is_on_offset(index_arr[0]):
"""
            ldhhg__aahpu += """      threshhold_date = initial_date - date_offset.base + date_offset
"""
            ldhhg__aahpu += '    else:\n'
            ldhhg__aahpu += (
                '      threshhold_date = initial_date + date_offset\n')
        else:
            ldhhg__aahpu += (
                f'    threshhold_date = initial_date {xrx__dyckf} date_offset\n'
                )
    else:
        ldhhg__aahpu += (
            f'  threshhold_date = initial_date {xrx__dyckf} offset\n')
    ldhhg__aahpu += '  local_valid = 0\n'
    ldhhg__aahpu += f'  n = len(index_arr)\n'
    ldhhg__aahpu += f'  if n:\n'
    ldhhg__aahpu += f'    if {fpjtk__kkizf}:\n'
    ldhhg__aahpu += '      loc_valid = n\n'
    ldhhg__aahpu += '    else:\n'
    ldhhg__aahpu += f'      for i in range({cgbu__ltlf}):\n'
    ldhhg__aahpu += f'        if {xtdtm__jwtp}:\n'
    ldhhg__aahpu += f'          loc_valid = {ggfgu__wlde}\n'
    ldhhg__aahpu += '          break\n'
    ldhhg__aahpu += '  if is_parallel:\n'
    ldhhg__aahpu += (
        '    total_valid = bodo.libs.distributed_api.dist_reduce(loc_valid, sum_op)\n'
        )
    ldhhg__aahpu += '    return total_valid\n'
    ldhhg__aahpu += '  else:\n'
    ldhhg__aahpu += '    return loc_valid\n'
    rku__lpej = {}
    exec(ldhhg__aahpu, {'bodo': bodo, 'pd': pd, 'numba': numba, 'sum_op':
        sum_op}, rku__lpej)
    return rku__lpej['impl']


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
    bykuk__iad = numba_to_c_type(sig.args[0].dtype)
    dknr__rzgv = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(32), bykuk__iad))
    zqmj__akbk = args[0]
    jhftk__ukrwx = sig.args[0]
    if isinstance(jhftk__ukrwx, (IntegerArrayType, BooleanArrayType)):
        zqmj__akbk = cgutils.create_struct_proxy(jhftk__ukrwx)(context,
            builder, zqmj__akbk).data
        jhftk__ukrwx = types.Array(jhftk__ukrwx.dtype, 1, 'C')
    assert jhftk__ukrwx.ndim == 1
    arr = make_array(jhftk__ukrwx)(context, builder, zqmj__akbk)
    tnr__vxpdl = builder.extract_value(arr.shape, 0)
    nhp__askn = [builder.bitcast(arr.data, lir.IntType(8).as_pointer()),
        tnr__vxpdl, args[1], builder.load(dknr__rzgv)]
    gzbbs__myca = [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
        DoubleType(), lir.IntType(32)]
    mizwr__nzz = lir.FunctionType(lir.DoubleType(), gzbbs__myca)
    tth__pfr = cgutils.get_or_insert_function(builder.module, mizwr__nzz,
        name='quantile_sequential')
    hmsj__nyowa = builder.call(tth__pfr, nhp__askn)
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return hmsj__nyowa


@lower_builtin(quantile_parallel, types.Array, types.float64, types.intp)
@lower_builtin(quantile_parallel, IntegerArrayType, types.float64, types.intp)
@lower_builtin(quantile_parallel, BooleanArrayType, types.float64, types.intp)
def lower_dist_quantile_parallel(context, builder, sig, args):
    bykuk__iad = numba_to_c_type(sig.args[0].dtype)
    dknr__rzgv = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(32), bykuk__iad))
    zqmj__akbk = args[0]
    jhftk__ukrwx = sig.args[0]
    if isinstance(jhftk__ukrwx, (IntegerArrayType, BooleanArrayType)):
        zqmj__akbk = cgutils.create_struct_proxy(jhftk__ukrwx)(context,
            builder, zqmj__akbk).data
        jhftk__ukrwx = types.Array(jhftk__ukrwx.dtype, 1, 'C')
    assert jhftk__ukrwx.ndim == 1
    arr = make_array(jhftk__ukrwx)(context, builder, zqmj__akbk)
    tnr__vxpdl = builder.extract_value(arr.shape, 0)
    if len(args) == 3:
        zynn__jaf = args[2]
    else:
        zynn__jaf = tnr__vxpdl
    nhp__askn = [builder.bitcast(arr.data, lir.IntType(8).as_pointer()),
        tnr__vxpdl, zynn__jaf, args[1], builder.load(dknr__rzgv)]
    gzbbs__myca = [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
        IntType(64), lir.DoubleType(), lir.IntType(32)]
    mizwr__nzz = lir.FunctionType(lir.DoubleType(), gzbbs__myca)
    tth__pfr = cgutils.get_or_insert_function(builder.module, mizwr__nzz,
        name='quantile_parallel')
    hmsj__nyowa = builder.call(tth__pfr, nhp__askn)
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return hmsj__nyowa


@numba.njit
def min_heapify(arr, ind_arr, n, start, cmp_f):
    czkg__pbmq = start
    pjtp__zysx = 2 * start + 1
    yio__rbsut = 2 * start + 2
    if pjtp__zysx < n and not cmp_f(arr[pjtp__zysx], arr[czkg__pbmq]):
        czkg__pbmq = pjtp__zysx
    if yio__rbsut < n and not cmp_f(arr[yio__rbsut], arr[czkg__pbmq]):
        czkg__pbmq = yio__rbsut
    if czkg__pbmq != start:
        arr[start], arr[czkg__pbmq] = arr[czkg__pbmq], arr[start]
        ind_arr[start], ind_arr[czkg__pbmq] = ind_arr[czkg__pbmq], ind_arr[
            start]
        min_heapify(arr, ind_arr, n, czkg__pbmq, cmp_f)


def select_k_nonan(A, index_arr, m, k):
    return A[:k]


@overload(select_k_nonan, no_unliteral=True)
def select_k_nonan_overload(A, index_arr, m, k):
    dtype = A.dtype
    if isinstance(dtype, types.Integer):
        return lambda A, index_arr, m, k: (A[:k].copy(), index_arr[:k].copy
            (), k)

    def select_k_nonan_float(A, index_arr, m, k):
        rvxwp__bfgkq = np.empty(k, A.dtype)
        atqmj__pyibr = np.empty(k, index_arr.dtype)
        i = 0
        ind = 0
        while i < m and ind < k:
            if not bodo.libs.array_kernels.isna(A, i):
                rvxwp__bfgkq[ind] = A[i]
                atqmj__pyibr[ind] = index_arr[i]
                ind += 1
            i += 1
        if ind < k:
            rvxwp__bfgkq = rvxwp__bfgkq[:ind]
            atqmj__pyibr = atqmj__pyibr[:ind]
        return rvxwp__bfgkq, atqmj__pyibr, i
    return select_k_nonan_float


@numba.njit
def nlargest(A, index_arr, k, is_largest, cmp_f):
    m = len(A)
    if k == 0:
        return A[:0], index_arr[:0]
    if k >= m:
        rukjv__bitg = np.sort(A)
        cux__mzk = index_arr[np.argsort(A)]
        unpp__ucpm = pd.Series(rukjv__bitg).notna().values
        rukjv__bitg = rukjv__bitg[unpp__ucpm]
        cux__mzk = cux__mzk[unpp__ucpm]
        if is_largest:
            rukjv__bitg = rukjv__bitg[::-1]
            cux__mzk = cux__mzk[::-1]
        return np.ascontiguousarray(rukjv__bitg), np.ascontiguousarray(cux__mzk
            )
    rvxwp__bfgkq, atqmj__pyibr, start = select_k_nonan(A, index_arr, m, k)
    atqmj__pyibr = atqmj__pyibr[rvxwp__bfgkq.argsort()]
    rvxwp__bfgkq.sort()
    if not is_largest:
        rvxwp__bfgkq = np.ascontiguousarray(rvxwp__bfgkq[::-1])
        atqmj__pyibr = np.ascontiguousarray(atqmj__pyibr[::-1])
    for i in range(start, m):
        if cmp_f(A[i], rvxwp__bfgkq[0]):
            rvxwp__bfgkq[0] = A[i]
            atqmj__pyibr[0] = index_arr[i]
            min_heapify(rvxwp__bfgkq, atqmj__pyibr, k, 0, cmp_f)
    atqmj__pyibr = atqmj__pyibr[rvxwp__bfgkq.argsort()]
    rvxwp__bfgkq.sort()
    if is_largest:
        rvxwp__bfgkq = rvxwp__bfgkq[::-1]
        atqmj__pyibr = atqmj__pyibr[::-1]
    return np.ascontiguousarray(rvxwp__bfgkq), np.ascontiguousarray(
        atqmj__pyibr)


@numba.njit
def nlargest_parallel(A, I, k, is_largest, cmp_f):
    vhyek__efbkr = bodo.libs.distributed_api.get_rank()
    wfzz__igec, txv__tgmf = nlargest(A, I, k, is_largest, cmp_f)
    awo__het = bodo.libs.distributed_api.gatherv(wfzz__igec)
    qlkj__jfwfm = bodo.libs.distributed_api.gatherv(txv__tgmf)
    if vhyek__efbkr == MPI_ROOT:
        res, kmsi__hdre = nlargest(awo__het, qlkj__jfwfm, k, is_largest, cmp_f)
    else:
        res = np.empty(k, A.dtype)
        kmsi__hdre = np.empty(k, I.dtype)
    bodo.libs.distributed_api.bcast(res)
    bodo.libs.distributed_api.bcast(kmsi__hdre)
    return res, kmsi__hdre


@numba.njit(no_cpython_wrapper=True, cache=True)
def nancorr(mat, cov=0, minpv=1, parallel=False):
    jzkyi__rfyd, rrqt__oac = mat.shape
    ttn__kjb = np.empty((rrqt__oac, rrqt__oac), dtype=np.float64)
    for smynd__kxc in range(rrqt__oac):
        for vdmts__qelqw in range(smynd__kxc + 1):
            ahe__uufvu = 0
            pzt__qese = onqm__oxv = wqs__acle = bqd__sssal = 0.0
            for i in range(jzkyi__rfyd):
                if np.isfinite(mat[i, smynd__kxc]) and np.isfinite(mat[i,
                    vdmts__qelqw]):
                    zsg__qvyy = mat[i, smynd__kxc]
                    smj__mgrr = mat[i, vdmts__qelqw]
                    ahe__uufvu += 1
                    wqs__acle += zsg__qvyy
                    bqd__sssal += smj__mgrr
            if parallel:
                ahe__uufvu = bodo.libs.distributed_api.dist_reduce(ahe__uufvu,
                    sum_op)
                wqs__acle = bodo.libs.distributed_api.dist_reduce(wqs__acle,
                    sum_op)
                bqd__sssal = bodo.libs.distributed_api.dist_reduce(bqd__sssal,
                    sum_op)
            if ahe__uufvu < minpv:
                ttn__kjb[smynd__kxc, vdmts__qelqw] = ttn__kjb[vdmts__qelqw,
                    smynd__kxc] = np.nan
            else:
                ngjw__jsom = wqs__acle / ahe__uufvu
                fyah__mtrx = bqd__sssal / ahe__uufvu
                wqs__acle = 0.0
                for i in range(jzkyi__rfyd):
                    if np.isfinite(mat[i, smynd__kxc]) and np.isfinite(mat[
                        i, vdmts__qelqw]):
                        zsg__qvyy = mat[i, smynd__kxc] - ngjw__jsom
                        smj__mgrr = mat[i, vdmts__qelqw] - fyah__mtrx
                        wqs__acle += zsg__qvyy * smj__mgrr
                        pzt__qese += zsg__qvyy * zsg__qvyy
                        onqm__oxv += smj__mgrr * smj__mgrr
                if parallel:
                    wqs__acle = bodo.libs.distributed_api.dist_reduce(wqs__acle
                        , sum_op)
                    pzt__qese = bodo.libs.distributed_api.dist_reduce(pzt__qese
                        , sum_op)
                    onqm__oxv = bodo.libs.distributed_api.dist_reduce(onqm__oxv
                        , sum_op)
                vkf__tsje = ahe__uufvu - 1.0 if cov else sqrt(pzt__qese *
                    onqm__oxv)
                if vkf__tsje != 0.0:
                    ttn__kjb[smynd__kxc, vdmts__qelqw] = ttn__kjb[
                        vdmts__qelqw, smynd__kxc] = wqs__acle / vkf__tsje
                else:
                    ttn__kjb[smynd__kxc, vdmts__qelqw] = ttn__kjb[
                        vdmts__qelqw, smynd__kxc] = np.nan
    return ttn__kjb


@numba.generated_jit(nopython=True)
def duplicated(data, parallel=False):
    n = len(data)
    if n == 0:
        return lambda data, parallel=False: np.empty(0, dtype=np.bool_)
    ncuaw__uttyg = n != 1
    ldhhg__aahpu = 'def impl(data, parallel=False):\n'
    ldhhg__aahpu += '  if parallel:\n'
    wbwy__iei = ', '.join(f'array_to_info(data[{i}])' for i in range(n))
    ldhhg__aahpu += f'    cpp_table = arr_info_list_to_table([{wbwy__iei}])\n'
    ldhhg__aahpu += f"""    out_cpp_table = bodo.libs.array.shuffle_table(cpp_table, {n}, parallel, 1)
"""
    iscb__xlfxs = ', '.join(
        f'info_to_array(info_from_table(out_cpp_table, {i}), data[{i}])' for
        i in range(n))
    ldhhg__aahpu += f'    data = ({iscb__xlfxs},)\n'
    ldhhg__aahpu += (
        '    shuffle_info = bodo.libs.array.get_shuffle_info(out_cpp_table)\n')
    ldhhg__aahpu += '    bodo.libs.array.delete_table(out_cpp_table)\n'
    ldhhg__aahpu += '    bodo.libs.array.delete_table(cpp_table)\n'
    ldhhg__aahpu += '  n = len(data[0])\n'
    ldhhg__aahpu += '  out = np.empty(n, np.bool_)\n'
    ldhhg__aahpu += '  uniqs = dict()\n'
    if ncuaw__uttyg:
        ldhhg__aahpu += '  for i in range(n):\n'
        ckstd__zrkh = ', '.join(f'data[{i}][i]' for i in range(n))
        caopz__ixp = ',  '.join(
            f'bodo.libs.array_kernels.isna(data[{i}], i)' for i in range(n))
        ldhhg__aahpu += f"""    val = bodo.libs.nullable_tuple_ext.build_nullable_tuple(({ckstd__zrkh},), ({caopz__ixp},))
"""
        ldhhg__aahpu += '    if val in uniqs:\n'
        ldhhg__aahpu += '      out[i] = True\n'
        ldhhg__aahpu += '    else:\n'
        ldhhg__aahpu += '      out[i] = False\n'
        ldhhg__aahpu += '      uniqs[val] = 0\n'
    else:
        ldhhg__aahpu += '  data = data[0]\n'
        ldhhg__aahpu += '  hasna = False\n'
        ldhhg__aahpu += '  for i in range(n):\n'
        ldhhg__aahpu += '    if bodo.libs.array_kernels.isna(data, i):\n'
        ldhhg__aahpu += '      out[i] = hasna\n'
        ldhhg__aahpu += '      hasna = True\n'
        ldhhg__aahpu += '    else:\n'
        ldhhg__aahpu += '      val = data[i]\n'
        ldhhg__aahpu += '      if val in uniqs:\n'
        ldhhg__aahpu += '        out[i] = True\n'
        ldhhg__aahpu += '      else:\n'
        ldhhg__aahpu += '        out[i] = False\n'
        ldhhg__aahpu += '        uniqs[val] = 0\n'
    ldhhg__aahpu += '  if parallel:\n'
    ldhhg__aahpu += (
        '    out = bodo.hiframes.pd_groupby_ext.reverse_shuffle(out, shuffle_info)\n'
        )
    ldhhg__aahpu += '  return out\n'
    rku__lpej = {}
    exec(ldhhg__aahpu, {'bodo': bodo, 'np': np, 'array_to_info':
        array_to_info, 'arr_info_list_to_table': arr_info_list_to_table,
        'info_to_array': info_to_array, 'info_from_table': info_from_table},
        rku__lpej)
    impl = rku__lpej['impl']
    return impl


def sample_table_operation(data, ind_arr, n, frac, replace, parallel=False):
    return data, ind_arr


@overload(sample_table_operation, no_unliteral=True)
def overload_sample_table_operation(data, ind_arr, n, frac, replace,
    parallel=False):
    lebd__lkc = len(data)
    ldhhg__aahpu = (
        'def impl(data, ind_arr, n, frac, replace, parallel=False):\n')
    ldhhg__aahpu += ('  info_list_total = [{}, array_to_info(ind_arr)]\n'.
        format(', '.join('array_to_info(data[{}])'.format(x) for x in range
        (lebd__lkc))))
    ldhhg__aahpu += '  table_total = arr_info_list_to_table(info_list_total)\n'
    ldhhg__aahpu += (
        '  out_table = sample_table(table_total, n, frac, replace, parallel)\n'
        .format(lebd__lkc))
    for wun__gqthc in range(lebd__lkc):
        ldhhg__aahpu += (
            '  out_arr_{} = info_to_array(info_from_table(out_table, {}), data[{}])\n'
            .format(wun__gqthc, wun__gqthc, wun__gqthc))
    ldhhg__aahpu += (
        '  out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)\n'
        .format(lebd__lkc))
    ldhhg__aahpu += '  delete_table(out_table)\n'
    ldhhg__aahpu += '  delete_table(table_total)\n'
    ldhhg__aahpu += '  return ({},), out_arr_index\n'.format(', '.join(
        'out_arr_{}'.format(i) for i in range(lebd__lkc)))
    rku__lpej = {}
    exec(ldhhg__aahpu, {'np': np, 'bodo': bodo, 'array_to_info':
        array_to_info, 'sample_table': sample_table,
        'arr_info_list_to_table': arr_info_list_to_table, 'info_from_table':
        info_from_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays}, rku__lpej)
    impl = rku__lpej['impl']
    return impl


def drop_duplicates(data, ind_arr, ncols, parallel=False):
    return data, ind_arr


@overload(drop_duplicates, no_unliteral=True)
def overload_drop_duplicates(data, ind_arr, ncols, parallel=False):
    lebd__lkc = len(data)
    ldhhg__aahpu = 'def impl(data, ind_arr, ncols, parallel=False):\n'
    ldhhg__aahpu += ('  info_list_total = [{}, array_to_info(ind_arr)]\n'.
        format(', '.join('array_to_info(data[{}])'.format(x) for x in range
        (lebd__lkc))))
    ldhhg__aahpu += '  table_total = arr_info_list_to_table(info_list_total)\n'
    ldhhg__aahpu += '  keep_i = 0\n'
    ldhhg__aahpu += """  out_table = drop_duplicates_table(table_total, parallel, ncols, keep_i, False, True)
"""
    for wun__gqthc in range(lebd__lkc):
        ldhhg__aahpu += (
            '  out_arr_{} = info_to_array(info_from_table(out_table, {}), data[{}])\n'
            .format(wun__gqthc, wun__gqthc, wun__gqthc))
    ldhhg__aahpu += (
        '  out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)\n'
        .format(lebd__lkc))
    ldhhg__aahpu += '  delete_table(out_table)\n'
    ldhhg__aahpu += '  delete_table(table_total)\n'
    ldhhg__aahpu += '  return ({},), out_arr_index\n'.format(', '.join(
        'out_arr_{}'.format(i) for i in range(lebd__lkc)))
    rku__lpej = {}
    exec(ldhhg__aahpu, {'np': np, 'bodo': bodo, 'array_to_info':
        array_to_info, 'drop_duplicates_table': drop_duplicates_table,
        'arr_info_list_to_table': arr_info_list_to_table, 'info_from_table':
        info_from_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays}, rku__lpej)
    impl = rku__lpej['impl']
    return impl


def drop_duplicates_array(data_arr, parallel=False):
    return data_arr


@overload(drop_duplicates_array, no_unliteral=True)
def overload_drop_duplicates_array(data_arr, parallel=False):

    def impl(data_arr, parallel=False):
        rxlu__prr = [array_to_info(data_arr)]
        howi__tpnr = arr_info_list_to_table(rxlu__prr)
        ryfj__wczdi = 0
        pwkv__opm = drop_duplicates_table(howi__tpnr, parallel, 1,
            ryfj__wczdi, False, True)
        nqzq__koj = info_to_array(info_from_table(pwkv__opm, 0), data_arr)
        delete_table(pwkv__opm)
        delete_table(howi__tpnr)
        return nqzq__koj
    return impl


def dropna(data, how, thresh, subset, parallel=False):
    return data


@overload(dropna, no_unliteral=True)
def overload_dropna(data, how, thresh, subset):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
        'bodo.dropna()')
    bxg__lrhlw = len(data.types)
    cfwac__qjs = [('out' + str(i)) for i in range(bxg__lrhlw)]
    bxqol__zxp = get_overload_const_list(subset)
    how = get_overload_const_str(how)
    uyx__yuag = ['isna(data[{}], i)'.format(i) for i in bxqol__zxp]
    gpjid__zygs = 'not ({})'.format(' or '.join(uyx__yuag))
    if not is_overload_none(thresh):
        gpjid__zygs = '(({}) <= ({}) - thresh)'.format(' + '.join(uyx__yuag
            ), bxg__lrhlw - 1)
    elif how == 'all':
        gpjid__zygs = 'not ({})'.format(' and '.join(uyx__yuag))
    ldhhg__aahpu = 'def _dropna_imp(data, how, thresh, subset):\n'
    ldhhg__aahpu += '  old_len = len(data[0])\n'
    ldhhg__aahpu += '  new_len = 0\n'
    ldhhg__aahpu += '  for i in range(old_len):\n'
    ldhhg__aahpu += '    if {}:\n'.format(gpjid__zygs)
    ldhhg__aahpu += '      new_len += 1\n'
    for i, out in enumerate(cfwac__qjs):
        if isinstance(data[i], bodo.CategoricalArrayType):
            ldhhg__aahpu += (
                '  {0} = bodo.utils.utils.alloc_type(new_len, data[{1}], (-1,))\n'
                .format(out, i))
        else:
            ldhhg__aahpu += (
                '  {0} = bodo.utils.utils.alloc_type(new_len, t{1}, (-1,))\n'
                .format(out, i))
    ldhhg__aahpu += '  curr_ind = 0\n'
    ldhhg__aahpu += '  for i in range(old_len):\n'
    ldhhg__aahpu += '    if {}:\n'.format(gpjid__zygs)
    for i in range(bxg__lrhlw):
        ldhhg__aahpu += '      if isna(data[{}], i):\n'.format(i)
        ldhhg__aahpu += '        setna({}, curr_ind)\n'.format(cfwac__qjs[i])
        ldhhg__aahpu += '      else:\n'
        ldhhg__aahpu += '        {}[curr_ind] = data[{}][i]\n'.format(
            cfwac__qjs[i], i)
    ldhhg__aahpu += '      curr_ind += 1\n'
    ldhhg__aahpu += '  return {}\n'.format(', '.join(cfwac__qjs))
    rku__lpej = {}
    rrp__cchf = {'t{}'.format(i): jud__ddbhl for i, jud__ddbhl in enumerate
        (data.types)}
    rrp__cchf.update({'isna': isna, 'setna': setna, 'init_nested_counts':
        bodo.utils.indexing.init_nested_counts, 'add_nested_counts': bodo.
        utils.indexing.add_nested_counts, 'bodo': bodo})
    exec(ldhhg__aahpu, rrp__cchf, rku__lpej)
    thno__pxlqk = rku__lpej['_dropna_imp']
    return thno__pxlqk


def get(arr, ind):
    return pd.Series(arr).str.get(ind)


@overload(get, no_unliteral=True)
def overload_get(arr, ind):
    if isinstance(arr, ArrayItemArrayType):
        jhftk__ukrwx = arr.dtype
        ugm__cdylb = jhftk__ukrwx.dtype

        def get_arr_item(arr, ind):
            n = len(arr)
            vzuvf__mdi = init_nested_counts(ugm__cdylb)
            for k in range(n):
                if bodo.libs.array_kernels.isna(arr, k):
                    continue
                val = arr[k]
                if not len(val) > ind >= -len(val
                    ) or bodo.libs.array_kernels.isna(val, ind):
                    continue
                vzuvf__mdi = add_nested_counts(vzuvf__mdi, val[ind])
            nqzq__koj = bodo.utils.utils.alloc_type(n, jhftk__ukrwx, vzuvf__mdi
                )
            for qvcb__mzim in range(n):
                if bodo.libs.array_kernels.isna(arr, qvcb__mzim):
                    setna(nqzq__koj, qvcb__mzim)
                    continue
                val = arr[qvcb__mzim]
                if not len(val) > ind >= -len(val
                    ) or bodo.libs.array_kernels.isna(val, ind):
                    setna(nqzq__koj, qvcb__mzim)
                    continue
                nqzq__koj[qvcb__mzim] = val[ind]
            return nqzq__koj
        return get_arr_item


def _is_same_categorical_array_type(arr_types):
    from bodo.hiframes.pd_categorical_ext import _to_readonly
    if not isinstance(arr_types, types.BaseTuple) or len(arr_types) == 0:
        return False
    kycnr__jyq = _to_readonly(arr_types.types[0])
    return all(isinstance(jud__ddbhl, CategoricalArrayType) and 
        _to_readonly(jud__ddbhl) == kycnr__jyq for jud__ddbhl in arr_types.
        types)


def concat(arr_list):
    return pd.concat(arr_list)


@overload(concat, no_unliteral=True)
def concat_overload(arr_list):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(arr_list.
        dtype, 'bodo.concat()')
    if isinstance(arr_list, bodo.NullableTupleType):
        return lambda arr_list: bodo.libs.array_kernels.concat(arr_list._data)
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, ArrayItemArrayType):
        fntai__xstrv = arr_list.dtype.dtype

        def array_item_concat_impl(arr_list):
            hco__uxmba = 0
            byu__smm = []
            for A in arr_list:
                tmmdc__nee = len(A)
                bodo.libs.array_item_arr_ext.trim_excess_data(A)
                byu__smm.append(bodo.libs.array_item_arr_ext.get_data(A))
                hco__uxmba += tmmdc__nee
            ooqy__gnjxg = np.empty(hco__uxmba + 1, offset_type)
            jrn__cuhsy = bodo.libs.array_kernels.concat(byu__smm)
            czl__pcziv = np.empty(hco__uxmba + 7 >> 3, np.uint8)
            wzq__kioi = 0
            jtmv__bigqr = 0
            for A in arr_list:
                olc__wlnu = bodo.libs.array_item_arr_ext.get_offsets(A)
                fkriw__yjt = bodo.libs.array_item_arr_ext.get_null_bitmap(A)
                tmmdc__nee = len(A)
                azwa__izquz = olc__wlnu[tmmdc__nee]
                for i in range(tmmdc__nee):
                    ooqy__gnjxg[i + wzq__kioi] = olc__wlnu[i] + jtmv__bigqr
                    trwn__cpfys = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        fkriw__yjt, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(czl__pcziv, i +
                        wzq__kioi, trwn__cpfys)
                wzq__kioi += tmmdc__nee
                jtmv__bigqr += azwa__izquz
            ooqy__gnjxg[wzq__kioi] = jtmv__bigqr
            nqzq__koj = bodo.libs.array_item_arr_ext.init_array_item_array(
                hco__uxmba, jrn__cuhsy, ooqy__gnjxg, czl__pcziv)
            return nqzq__koj
        return array_item_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, bodo.StructArrayType):
        izskg__wdjto = arr_list.dtype.names
        ldhhg__aahpu = 'def struct_array_concat_impl(arr_list):\n'
        ldhhg__aahpu += f'    n_all = 0\n'
        for i in range(len(izskg__wdjto)):
            ldhhg__aahpu += f'    concat_list{i} = []\n'
        ldhhg__aahpu += '    for A in arr_list:\n'
        ldhhg__aahpu += (
            '        data_tuple = bodo.libs.struct_arr_ext.get_data(A)\n')
        for i in range(len(izskg__wdjto)):
            ldhhg__aahpu += f'        concat_list{i}.append(data_tuple[{i}])\n'
        ldhhg__aahpu += '        n_all += len(A)\n'
        ldhhg__aahpu += '    n_bytes = (n_all + 7) >> 3\n'
        ldhhg__aahpu += '    new_mask = np.empty(n_bytes, np.uint8)\n'
        ldhhg__aahpu += '    curr_bit = 0\n'
        ldhhg__aahpu += '    for A in arr_list:\n'
        ldhhg__aahpu += (
            '        old_mask = bodo.libs.struct_arr_ext.get_null_bitmap(A)\n')
        ldhhg__aahpu += '        for j in range(len(A)):\n'
        ldhhg__aahpu += (
            '            bit = bodo.libs.int_arr_ext.get_bit_bitmap_arr(old_mask, j)\n'
            )
        ldhhg__aahpu += """            bodo.libs.int_arr_ext.set_bit_to_arr(new_mask, curr_bit, bit)
"""
        ldhhg__aahpu += '            curr_bit += 1\n'
        ldhhg__aahpu += (
            '    return bodo.libs.struct_arr_ext.init_struct_arr(\n')
        qcs__iin = ', '.join([
            f'bodo.libs.array_kernels.concat(concat_list{i})' for i in
            range(len(izskg__wdjto))])
        ldhhg__aahpu += f'        ({qcs__iin},),\n'
        ldhhg__aahpu += '        new_mask,\n'
        ldhhg__aahpu += f'        {izskg__wdjto},\n'
        ldhhg__aahpu += '    )\n'
        rku__lpej = {}
        exec(ldhhg__aahpu, {'bodo': bodo, 'np': np}, rku__lpej)
        return rku__lpej['struct_array_concat_impl']
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == datetime_date_array_type:

        def datetime_date_array_concat_impl(arr_list):
            enegx__xhocr = 0
            for A in arr_list:
                enegx__xhocr += len(A)
            qqbz__yxj = (bodo.hiframes.datetime_date_ext.
                alloc_datetime_date_array(enegx__xhocr))
            noaj__fql = 0
            for A in arr_list:
                for i in range(len(A)):
                    qqbz__yxj._data[i + noaj__fql] = A._data[i]
                    trwn__cpfys = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(qqbz__yxj.
                        _null_bitmap, i + noaj__fql, trwn__cpfys)
                noaj__fql += len(A)
            return qqbz__yxj
        return datetime_date_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == datetime_timedelta_array_type:

        def datetime_timedelta_array_concat_impl(arr_list):
            enegx__xhocr = 0
            for A in arr_list:
                enegx__xhocr += len(A)
            qqbz__yxj = (bodo.hiframes.datetime_timedelta_ext.
                alloc_datetime_timedelta_array(enegx__xhocr))
            noaj__fql = 0
            for A in arr_list:
                for i in range(len(A)):
                    qqbz__yxj._days_data[i + noaj__fql] = A._days_data[i]
                    qqbz__yxj._seconds_data[i + noaj__fql] = A._seconds_data[i]
                    qqbz__yxj._microseconds_data[i + noaj__fql
                        ] = A._microseconds_data[i]
                    trwn__cpfys = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(qqbz__yxj.
                        _null_bitmap, i + noaj__fql, trwn__cpfys)
                noaj__fql += len(A)
            return qqbz__yxj
        return datetime_timedelta_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, DecimalArrayType):
        qafhh__jigbf = arr_list.dtype.precision
        jxfo__xwxl = arr_list.dtype.scale

        def decimal_array_concat_impl(arr_list):
            enegx__xhocr = 0
            for A in arr_list:
                enegx__xhocr += len(A)
            qqbz__yxj = bodo.libs.decimal_arr_ext.alloc_decimal_array(
                enegx__xhocr, qafhh__jigbf, jxfo__xwxl)
            noaj__fql = 0
            for A in arr_list:
                for i in range(len(A)):
                    qqbz__yxj._data[i + noaj__fql] = A._data[i]
                    trwn__cpfys = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(qqbz__yxj.
                        _null_bitmap, i + noaj__fql, trwn__cpfys)
                noaj__fql += len(A)
            return qqbz__yxj
        return decimal_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and (is_str_arr_type
        (arr_list.dtype) or arr_list.dtype == bodo.binary_array_type
        ) or isinstance(arr_list, types.BaseTuple) and all(is_str_arr_type(
        jud__ddbhl) for jud__ddbhl in arr_list.types):
        if isinstance(arr_list, types.BaseTuple):
            jhfa__mur = arr_list.types[0]
        else:
            jhfa__mur = arr_list.dtype
        jhfa__mur = to_str_arr_if_dict_array(jhfa__mur)

        def impl_str(arr_list):
            arr_list = decode_if_dict_array(arr_list)
            acbls__izkj = 0
            fkjf__dvro = 0
            for A in arr_list:
                arr = A
                acbls__izkj += len(arr)
                fkjf__dvro += bodo.libs.str_arr_ext.num_total_chars(arr)
            nqzq__koj = bodo.utils.utils.alloc_type(acbls__izkj, jhfa__mur,
                (fkjf__dvro,))
            bodo.libs.str_arr_ext.set_null_bits_to_value(nqzq__koj, -1)
            ult__hhov = 0
            mso__oefwg = 0
            for A in arr_list:
                arr = A
                bodo.libs.str_arr_ext.set_string_array_range(nqzq__koj, arr,
                    ult__hhov, mso__oefwg)
                ult__hhov += len(arr)
                mso__oefwg += bodo.libs.str_arr_ext.num_total_chars(arr)
            return nqzq__koj
        return impl_str
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, IntegerArrayType) or isinstance(arr_list, types.
        BaseTuple) and all(isinstance(jud__ddbhl.dtype, types.Integer) for
        jud__ddbhl in arr_list.types) and any(isinstance(jud__ddbhl,
        IntegerArrayType) for jud__ddbhl in arr_list.types):

        def impl_int_arr_list(arr_list):
            vay__hjdcz = convert_to_nullable_tup(arr_list)
            sizfq__wbduk = []
            uii__offy = 0
            for A in vay__hjdcz:
                sizfq__wbduk.append(A._data)
                uii__offy += len(A)
            jrn__cuhsy = bodo.libs.array_kernels.concat(sizfq__wbduk)
            qfdsc__glw = uii__offy + 7 >> 3
            miswb__bxt = np.empty(qfdsc__glw, np.uint8)
            rvgj__ctr = 0
            for A in vay__hjdcz:
                xhdf__ppqpa = A._null_bitmap
                for qvcb__mzim in range(len(A)):
                    trwn__cpfys = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        xhdf__ppqpa, qvcb__mzim)
                    bodo.libs.int_arr_ext.set_bit_to_arr(miswb__bxt,
                        rvgj__ctr, trwn__cpfys)
                    rvgj__ctr += 1
            return bodo.libs.int_arr_ext.init_integer_array(jrn__cuhsy,
                miswb__bxt)
        return impl_int_arr_list
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == boolean_array or isinstance(arr_list, types
        .BaseTuple) and all(jud__ddbhl.dtype == types.bool_ for jud__ddbhl in
        arr_list.types) and any(jud__ddbhl == boolean_array for jud__ddbhl in
        arr_list.types):

        def impl_bool_arr_list(arr_list):
            vay__hjdcz = convert_to_nullable_tup(arr_list)
            sizfq__wbduk = []
            uii__offy = 0
            for A in vay__hjdcz:
                sizfq__wbduk.append(A._data)
                uii__offy += len(A)
            jrn__cuhsy = bodo.libs.array_kernels.concat(sizfq__wbduk)
            qfdsc__glw = uii__offy + 7 >> 3
            miswb__bxt = np.empty(qfdsc__glw, np.uint8)
            rvgj__ctr = 0
            for A in vay__hjdcz:
                xhdf__ppqpa = A._null_bitmap
                for qvcb__mzim in range(len(A)):
                    trwn__cpfys = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        xhdf__ppqpa, qvcb__mzim)
                    bodo.libs.int_arr_ext.set_bit_to_arr(miswb__bxt,
                        rvgj__ctr, trwn__cpfys)
                    rvgj__ctr += 1
            return bodo.libs.bool_arr_ext.init_bool_array(jrn__cuhsy,
                miswb__bxt)
        return impl_bool_arr_list
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, CategoricalArrayType):

        def cat_array_concat_impl(arr_list):
            swdh__cdt = []
            for A in arr_list:
                swdh__cdt.append(A.codes)
            return init_categorical_array(bodo.libs.array_kernels.concat(
                swdh__cdt), arr_list[0].dtype)
        return cat_array_concat_impl
    if _is_same_categorical_array_type(arr_list):
        cylvp__ftoch = ', '.join(f'arr_list[{i}].codes' for i in range(len(
            arr_list)))
        ldhhg__aahpu = 'def impl(arr_list):\n'
        ldhhg__aahpu += f"""    return init_categorical_array(bodo.libs.array_kernels.concat(({cylvp__ftoch},)), arr_list[0].dtype)
"""
        thvy__cixcz = {}
        exec(ldhhg__aahpu, {'bodo': bodo, 'init_categorical_array':
            init_categorical_array}, thvy__cixcz)
        return thvy__cixcz['impl']
    if isinstance(arr_list, types.List) and isinstance(arr_list.dtype,
        types.Array) and arr_list.dtype.ndim == 1:
        dtype = arr_list.dtype.dtype

        def impl_np_arr_list(arr_list):
            uii__offy = 0
            for A in arr_list:
                uii__offy += len(A)
            nqzq__koj = np.empty(uii__offy, dtype)
            yik__vpra = 0
            for A in arr_list:
                n = len(A)
                nqzq__koj[yik__vpra:yik__vpra + n] = A
                yik__vpra += n
            return nqzq__koj
        return impl_np_arr_list
    if isinstance(arr_list, types.BaseTuple) and any(isinstance(jud__ddbhl,
        (types.Array, IntegerArrayType)) and isinstance(jud__ddbhl.dtype,
        types.Integer) for jud__ddbhl in arr_list.types) and any(isinstance
        (jud__ddbhl, types.Array) and isinstance(jud__ddbhl.dtype, types.
        Float) for jud__ddbhl in arr_list.types):
        return lambda arr_list: np.concatenate(astype_float_tup(arr_list))
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, bodo.MapArrayType):

        def impl_map_arr_list(arr_list):
            xokkg__zwkz = []
            for A in arr_list:
                xokkg__zwkz.append(A._data)
            jhxf__qimss = bodo.libs.array_kernels.concat(xokkg__zwkz)
            ttn__kjb = bodo.libs.map_arr_ext.init_map_arr(jhxf__qimss)
            return ttn__kjb
        return impl_map_arr_list
    for kqq__judk in arr_list:
        if not isinstance(kqq__judk, types.Array):
            raise_bodo_error(f'concat of array types {arr_list} not supported')
    return lambda arr_list: np.concatenate(arr_list)


def astype_float_tup(arr_tup):
    return tuple(jud__ddbhl.astype(np.float64) for jud__ddbhl in arr_tup)


@overload(astype_float_tup, no_unliteral=True)
def overload_astype_float_tup(arr_tup):
    assert isinstance(arr_tup, types.BaseTuple)
    lebd__lkc = len(arr_tup.types)
    ldhhg__aahpu = 'def f(arr_tup):\n'
    ldhhg__aahpu += '  return ({}{})\n'.format(','.join(
        'arr_tup[{}].astype(np.float64)'.format(i) for i in range(lebd__lkc
        )), ',' if lebd__lkc == 1 else '')
    rku__lpej = {}
    exec(ldhhg__aahpu, {'np': np}, rku__lpej)
    wasbi__jumt = rku__lpej['f']
    return wasbi__jumt


def convert_to_nullable_tup(arr_tup):
    return arr_tup


@overload(convert_to_nullable_tup, no_unliteral=True)
def overload_convert_to_nullable_tup(arr_tup):
    if isinstance(arr_tup, (types.UniTuple, types.List)) and isinstance(arr_tup
        .dtype, (IntegerArrayType, BooleanArrayType)):
        return lambda arr_tup: arr_tup
    assert isinstance(arr_tup, types.BaseTuple)
    lebd__lkc = len(arr_tup.types)
    vwh__yolu = find_common_np_dtype(arr_tup.types)
    ugm__cdylb = None
    yjt__xadb = ''
    if isinstance(vwh__yolu, types.Integer):
        ugm__cdylb = bodo.libs.int_arr_ext.IntDtype(vwh__yolu)
        yjt__xadb = '.astype(out_dtype, False)'
    ldhhg__aahpu = 'def f(arr_tup):\n'
    ldhhg__aahpu += '  return ({}{})\n'.format(','.join(
        'bodo.utils.conversion.coerce_to_array(arr_tup[{}], use_nullable_array=True){}'
        .format(i, yjt__xadb) for i in range(lebd__lkc)), ',' if lebd__lkc ==
        1 else '')
    rku__lpej = {}
    exec(ldhhg__aahpu, {'bodo': bodo, 'out_dtype': ugm__cdylb}, rku__lpej)
    oqafj__unm = rku__lpej['f']
    return oqafj__unm


def nunique(A, dropna):
    return len(set(A))


def nunique_parallel(A, dropna):
    return len(set(A))


@overload(nunique, no_unliteral=True)
def nunique_overload(A, dropna):

    def nunique_seq(A, dropna):
        s, cya__icch = build_set_seen_na(A)
        return len(s) + int(not dropna and cya__icch)
    return nunique_seq


@overload(nunique_parallel, no_unliteral=True)
def nunique_overload_parallel(A, dropna):
    sum_op = bodo.libs.distributed_api.Reduce_Type.Sum.value

    def nunique_par(A, dropna):
        vjsh__jfxub = bodo.libs.array_kernels.unique(A, dropna, parallel=True)
        dmnq__gvndt = len(vjsh__jfxub)
        return bodo.libs.distributed_api.dist_reduce(dmnq__gvndt, np.int32(
            sum_op))
    return nunique_par


def unique(A, dropna=False, parallel=False):
    return np.array([bdacy__sedwk for bdacy__sedwk in set(A)]).astype(A.dtype)


def cummin(A):
    return A


@overload(cummin, no_unliteral=True)
def cummin_overload(A):
    if isinstance(A.dtype, types.Float):
        rhvon__brp = np.finfo(A.dtype(1).dtype).max
    else:
        rhvon__brp = np.iinfo(A.dtype(1).dtype).max

    def impl(A):
        n = len(A)
        nqzq__koj = np.empty(n, A.dtype)
        zlm__kfimz = rhvon__brp
        for i in range(n):
            zlm__kfimz = min(zlm__kfimz, A[i])
            nqzq__koj[i] = zlm__kfimz
        return nqzq__koj
    return impl


def cummax(A):
    return A


@overload(cummax, no_unliteral=True)
def cummax_overload(A):
    if isinstance(A.dtype, types.Float):
        rhvon__brp = np.finfo(A.dtype(1).dtype).min
    else:
        rhvon__brp = np.iinfo(A.dtype(1).dtype).min

    def impl(A):
        n = len(A)
        nqzq__koj = np.empty(n, A.dtype)
        zlm__kfimz = rhvon__brp
        for i in range(n):
            zlm__kfimz = max(zlm__kfimz, A[i])
            nqzq__koj[i] = zlm__kfimz
        return nqzq__koj
    return impl


@overload(unique, no_unliteral=True)
def unique_overload(A, dropna=False, parallel=False):

    def unique_impl(A, dropna=False, parallel=False):
        gsa__dpyun = arr_info_list_to_table([array_to_info(A)])
        xfgq__rzuns = 1
        ryfj__wczdi = 0
        pwkv__opm = drop_duplicates_table(gsa__dpyun, parallel, xfgq__rzuns,
            ryfj__wczdi, dropna, True)
        nqzq__koj = info_to_array(info_from_table(pwkv__opm, 0), A)
        delete_table(gsa__dpyun)
        delete_table(pwkv__opm)
        return nqzq__koj
    return unique_impl


def explode(arr, index_arr):
    return pd.Series(arr, index_arr).explode()


@overload(explode, no_unliteral=True)
def overload_explode(arr, index_arr):
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type
    fntai__xstrv = bodo.utils.typing.to_nullable_type(arr.dtype)
    siehh__bvxxk = index_arr
    pmgvv__pbn = siehh__bvxxk.dtype

    def impl(arr, index_arr):
        n = len(arr)
        vzuvf__mdi = init_nested_counts(fntai__xstrv)
        egvn__nhu = init_nested_counts(pmgvv__pbn)
        for i in range(n):
            hzpk__vbj = index_arr[i]
            if isna(arr, i):
                vzuvf__mdi = (vzuvf__mdi[0] + 1,) + vzuvf__mdi[1:]
                egvn__nhu = add_nested_counts(egvn__nhu, hzpk__vbj)
                continue
            dsb__dnkzl = arr[i]
            if len(dsb__dnkzl) == 0:
                vzuvf__mdi = (vzuvf__mdi[0] + 1,) + vzuvf__mdi[1:]
                egvn__nhu = add_nested_counts(egvn__nhu, hzpk__vbj)
                continue
            vzuvf__mdi = add_nested_counts(vzuvf__mdi, dsb__dnkzl)
            for tiots__ygwst in range(len(dsb__dnkzl)):
                egvn__nhu = add_nested_counts(egvn__nhu, hzpk__vbj)
        nqzq__koj = bodo.utils.utils.alloc_type(vzuvf__mdi[0], fntai__xstrv,
            vzuvf__mdi[1:])
        igv__kjaph = bodo.utils.utils.alloc_type(vzuvf__mdi[0],
            siehh__bvxxk, egvn__nhu)
        jtmv__bigqr = 0
        for i in range(n):
            if isna(arr, i):
                setna(nqzq__koj, jtmv__bigqr)
                igv__kjaph[jtmv__bigqr] = index_arr[i]
                jtmv__bigqr += 1
                continue
            dsb__dnkzl = arr[i]
            azwa__izquz = len(dsb__dnkzl)
            if azwa__izquz == 0:
                setna(nqzq__koj, jtmv__bigqr)
                igv__kjaph[jtmv__bigqr] = index_arr[i]
                jtmv__bigqr += 1
                continue
            nqzq__koj[jtmv__bigqr:jtmv__bigqr + azwa__izquz] = dsb__dnkzl
            igv__kjaph[jtmv__bigqr:jtmv__bigqr + azwa__izquz] = index_arr[i]
            jtmv__bigqr += azwa__izquz
        return nqzq__koj, igv__kjaph
    return impl


def explode_no_index(arr):
    return pd.Series(arr).explode()


@overload(explode_no_index, no_unliteral=True)
def overload_explode_no_index(arr, counts):
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type
    fntai__xstrv = bodo.utils.typing.to_nullable_type(arr.dtype)

    def impl(arr, counts):
        n = len(arr)
        vzuvf__mdi = init_nested_counts(fntai__xstrv)
        for i in range(n):
            if isna(arr, i):
                vzuvf__mdi = (vzuvf__mdi[0] + 1,) + vzuvf__mdi[1:]
                plbr__goc = 1
            else:
                dsb__dnkzl = arr[i]
                vge__gssnu = len(dsb__dnkzl)
                if vge__gssnu == 0:
                    vzuvf__mdi = (vzuvf__mdi[0] + 1,) + vzuvf__mdi[1:]
                    plbr__goc = 1
                    continue
                else:
                    vzuvf__mdi = add_nested_counts(vzuvf__mdi, dsb__dnkzl)
                    plbr__goc = vge__gssnu
            if counts[i] != plbr__goc:
                raise ValueError(
                    'DataFrame.explode(): columns must have matching element counts'
                    )
        nqzq__koj = bodo.utils.utils.alloc_type(vzuvf__mdi[0], fntai__xstrv,
            vzuvf__mdi[1:])
        jtmv__bigqr = 0
        for i in range(n):
            if isna(arr, i):
                setna(nqzq__koj, jtmv__bigqr)
                jtmv__bigqr += 1
                continue
            dsb__dnkzl = arr[i]
            azwa__izquz = len(dsb__dnkzl)
            if azwa__izquz == 0:
                setna(nqzq__koj, jtmv__bigqr)
                jtmv__bigqr += 1
                continue
            nqzq__koj[jtmv__bigqr:jtmv__bigqr + azwa__izquz] = dsb__dnkzl
            jtmv__bigqr += azwa__izquz
        return nqzq__koj
    return impl


def get_arr_lens(arr, na_empty_as_one=True):
    return [len(gcypy__ztam) for gcypy__ztam in arr]


@overload(get_arr_lens, inline='always', no_unliteral=True)
def overload_get_arr_lens(arr, na_empty_as_one=True):
    na_empty_as_one = get_overload_const_bool(na_empty_as_one)
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type or is_str_arr_type(arr
        ) and not na_empty_as_one, f'get_arr_lens: invalid input array type {arr}'
    if na_empty_as_one:
        vpbm__yzecx = 'np.empty(n, np.int64)'
        lmsa__ylyk = 'out_arr[i] = 1'
        jmw__ndqls = 'max(len(arr[i]), 1)'
    else:
        vpbm__yzecx = 'bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)'
        lmsa__ylyk = 'bodo.libs.array_kernels.setna(out_arr, i)'
        jmw__ndqls = 'len(arr[i])'
    ldhhg__aahpu = f"""def impl(arr, na_empty_as_one=True):
    numba.parfors.parfor.init_prange()
    n = len(arr)
    out_arr = {vpbm__yzecx}
    for i in numba.parfors.parfor.internal_prange(n):
        if bodo.libs.array_kernels.isna(arr, i):
            {lmsa__ylyk}
        else:
            out_arr[i] = {jmw__ndqls}
    return out_arr
    """
    rku__lpej = {}
    exec(ldhhg__aahpu, {'bodo': bodo, 'numba': numba, 'np': np}, rku__lpej)
    impl = rku__lpej['impl']
    return impl


def explode_str_split(arr, pat, n, index_arr):
    return pd.Series(arr, index_arr).str.split(pat, n).explode()


@overload(explode_str_split, no_unliteral=True)
def overload_explode_str_split(arr, pat, n, index_arr):
    assert is_str_arr_type(arr
        ), f'explode_str_split: string array expected, not {arr}'
    siehh__bvxxk = index_arr
    pmgvv__pbn = siehh__bvxxk.dtype

    def impl(arr, pat, n, index_arr):
        mynb__acua = pat is not None and len(pat) > 1
        if mynb__acua:
            kbx__ryu = re.compile(pat)
            if n == -1:
                n = 0
        elif n == 0:
            n = -1
        cdg__oxx = len(arr)
        acbls__izkj = 0
        fkjf__dvro = 0
        egvn__nhu = init_nested_counts(pmgvv__pbn)
        for i in range(cdg__oxx):
            hzpk__vbj = index_arr[i]
            if bodo.libs.array_kernels.isna(arr, i):
                acbls__izkj += 1
                egvn__nhu = add_nested_counts(egvn__nhu, hzpk__vbj)
                continue
            if mynb__acua:
                woh__zhs = kbx__ryu.split(arr[i], maxsplit=n)
            else:
                woh__zhs = arr[i].split(pat, n)
            acbls__izkj += len(woh__zhs)
            for s in woh__zhs:
                egvn__nhu = add_nested_counts(egvn__nhu, hzpk__vbj)
                fkjf__dvro += bodo.libs.str_arr_ext.get_utf8_size(s)
        nqzq__koj = bodo.libs.str_arr_ext.pre_alloc_string_array(acbls__izkj,
            fkjf__dvro)
        igv__kjaph = bodo.utils.utils.alloc_type(acbls__izkj, siehh__bvxxk,
            egvn__nhu)
        imou__bqsrn = 0
        for qvcb__mzim in range(cdg__oxx):
            if isna(arr, qvcb__mzim):
                nqzq__koj[imou__bqsrn] = ''
                bodo.libs.array_kernels.setna(nqzq__koj, imou__bqsrn)
                igv__kjaph[imou__bqsrn] = index_arr[qvcb__mzim]
                imou__bqsrn += 1
                continue
            if mynb__acua:
                woh__zhs = kbx__ryu.split(arr[qvcb__mzim], maxsplit=n)
            else:
                woh__zhs = arr[qvcb__mzim].split(pat, n)
            bfdp__uljl = len(woh__zhs)
            nqzq__koj[imou__bqsrn:imou__bqsrn + bfdp__uljl] = woh__zhs
            igv__kjaph[imou__bqsrn:imou__bqsrn + bfdp__uljl] = index_arr[
                qvcb__mzim]
            imou__bqsrn += bfdp__uljl
        return nqzq__koj, igv__kjaph
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
            nqzq__koj = np.empty(n, dtype)
            for i in numba.parfors.parfor.internal_prange(n):
                nqzq__koj[i] = np.nan
            return nqzq__koj
        return impl_float
    pycy__ojqt = to_str_arr_if_dict_array(arr)

    def impl(n, arr):
        numba.parfors.parfor.init_prange()
        nqzq__koj = bodo.utils.utils.alloc_type(n, pycy__ojqt, (0,))
        for i in numba.parfors.parfor.internal_prange(n):
            setna(nqzq__koj, i)
        return nqzq__koj
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
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A,
        'bodo.resize_and_copy()')
    zux__jyvoq = A
    if A == types.Array(types.uint8, 1, 'C'):

        def impl_char(A, old_size, new_len):
            nqzq__koj = bodo.utils.utils.alloc_type(new_len, zux__jyvoq)
            bodo.libs.str_arr_ext.str_copy_ptr(nqzq__koj.ctypes, 0, A.
                ctypes, old_size)
            return nqzq__koj
        return impl_char

    def impl(A, old_size, new_len):
        nqzq__koj = bodo.utils.utils.alloc_type(new_len, zux__jyvoq, (-1,))
        nqzq__koj[:old_size] = A[:old_size]
        return nqzq__koj
    return impl


@register_jitable
def calc_nitems(start, stop, step):
    sbr__qyo = math.ceil((stop - start) / step)
    return int(max(sbr__qyo, 0))


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
    if any(isinstance(bdacy__sedwk, types.Complex) for bdacy__sedwk in args):

        def arange_4(start, stop, step, dtype):
            numba.parfors.parfor.init_prange()
            aativ__wawqi = (stop - start) / step
            sbr__qyo = math.ceil(aativ__wawqi.real)
            dfa__pxwcu = math.ceil(aativ__wawqi.imag)
            wzayv__rhs = int(max(min(dfa__pxwcu, sbr__qyo), 0))
            arr = np.empty(wzayv__rhs, dtype)
            for i in numba.parfors.parfor.internal_prange(wzayv__rhs):
                arr[i] = start + i * step
            return arr
    else:

        def arange_4(start, stop, step, dtype):
            numba.parfors.parfor.init_prange()
            wzayv__rhs = bodo.libs.array_kernels.calc_nitems(start, stop, step)
            arr = np.empty(wzayv__rhs, dtype)
            for i in numba.parfors.parfor.internal_prange(wzayv__rhs):
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
        upqe__opk = arr,
        if not inplace:
            upqe__opk = arr.copy(),
        clkrb__scl = bodo.libs.str_arr_ext.to_list_if_immutable_arr(upqe__opk)
        syfxg__aaqkt = bodo.libs.str_arr_ext.to_list_if_immutable_arr(data,
            True)
        bodo.libs.timsort.sort(clkrb__scl, 0, n, syfxg__aaqkt)
        if not ascending:
            bodo.libs.timsort.reverseRange(clkrb__scl, 0, n, syfxg__aaqkt)
        bodo.libs.str_arr_ext.cp_str_list_to_array(upqe__opk, clkrb__scl)
        return upqe__opk[0]
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
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A,
        'bodo.nonzero()')
    if not bodo.utils.utils.is_array_typ(A, False):
        return

    def impl(A, parallel=False):
        n = len(A)
        if parallel:
            offset = bodo.libs.distributed_api.dist_exscan(n, Reduce_Type.
                Sum.value)
        else:
            offset = 0
        ttn__kjb = []
        for i in range(n):
            if A[i]:
                ttn__kjb.append(i + offset)
        return np.array(ttn__kjb, np.int64),
    return impl


def ffill_bfill_arr(arr):
    return arr


@overload(ffill_bfill_arr, no_unliteral=True)
def ffill_bfill_overload(A, method, parallel=False):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A,
        'bodo.ffill_bfill_arr()')
    zux__jyvoq = element_type(A)
    if zux__jyvoq == types.unicode_type:
        null_value = '""'
    elif zux__jyvoq == types.bool_:
        null_value = 'False'
    elif zux__jyvoq == bodo.datetime64ns:
        null_value = (
            'bodo.utils.conversion.unbox_if_timestamp(pd.to_datetime(0))')
    elif zux__jyvoq == bodo.timedelta64ns:
        null_value = (
            'bodo.utils.conversion.unbox_if_timestamp(pd.to_timedelta(0))')
    else:
        null_value = '0'
    imou__bqsrn = 'i'
    lwyp__zicn = False
    uwngh__mod = get_overload_const_str(method)
    if uwngh__mod in ('ffill', 'pad'):
        rbx__mxu = 'n'
        send_right = True
    elif uwngh__mod in ('backfill', 'bfill'):
        rbx__mxu = 'n-1, -1, -1'
        send_right = False
        if zux__jyvoq == types.unicode_type:
            imou__bqsrn = '(n - 1) - i'
            lwyp__zicn = True
    ldhhg__aahpu = 'def impl(A, method, parallel=False):\n'
    ldhhg__aahpu += '  A = decode_if_dict_array(A)\n'
    ldhhg__aahpu += '  has_last_value = False\n'
    ldhhg__aahpu += f'  last_value = {null_value}\n'
    ldhhg__aahpu += '  if parallel:\n'
    ldhhg__aahpu += '    rank = bodo.libs.distributed_api.get_rank()\n'
    ldhhg__aahpu += '    n_pes = bodo.libs.distributed_api.get_size()\n'
    ldhhg__aahpu += f"""    has_last_value, last_value = null_border_icomm(A, rank, n_pes, {null_value}, {send_right})
"""
    ldhhg__aahpu += '  n = len(A)\n'
    ldhhg__aahpu += '  out_arr = bodo.utils.utils.alloc_type(n, A, (-1,))\n'
    ldhhg__aahpu += f'  for i in range({rbx__mxu}):\n'
    ldhhg__aahpu += (
        '    if (bodo.libs.array_kernels.isna(A, i) and not has_last_value):\n'
        )
    ldhhg__aahpu += (
        f'      bodo.libs.array_kernels.setna(out_arr, {imou__bqsrn})\n')
    ldhhg__aahpu += '      continue\n'
    ldhhg__aahpu += '    s = A[i]\n'
    ldhhg__aahpu += '    if bodo.libs.array_kernels.isna(A, i):\n'
    ldhhg__aahpu += '      s = last_value\n'
    ldhhg__aahpu += f'    out_arr[{imou__bqsrn}] = s\n'
    ldhhg__aahpu += '    last_value = s\n'
    ldhhg__aahpu += '    has_last_value = True\n'
    if lwyp__zicn:
        ldhhg__aahpu += '  return out_arr[::-1]\n'
    else:
        ldhhg__aahpu += '  return out_arr\n'
    yit__tcwu = {}
    exec(ldhhg__aahpu, {'bodo': bodo, 'numba': numba, 'pd': pd,
        'null_border_icomm': null_border_icomm, 'decode_if_dict_array':
        decode_if_dict_array}, yit__tcwu)
    impl = yit__tcwu['impl']
    return impl


@register_jitable(cache=True)
def null_border_icomm(in_arr, rank, n_pes, null_value, send_right=True):
    if send_right:
        shbul__hpzzj = 0
        jwlh__hnat = n_pes - 1
        fbbbk__oomrv = np.int32(rank + 1)
        mqb__zjny = np.int32(rank - 1)
        byjad__haw = len(in_arr) - 1
        ukr__kio = -1
        xhcb__fwgx = -1
    else:
        shbul__hpzzj = n_pes - 1
        jwlh__hnat = 0
        fbbbk__oomrv = np.int32(rank - 1)
        mqb__zjny = np.int32(rank + 1)
        byjad__haw = 0
        ukr__kio = len(in_arr)
        xhcb__fwgx = 1
    cjt__wkvr = np.int32(bodo.hiframes.rolling.comm_border_tag)
    knz__sght = np.empty(1, dtype=np.bool_)
    jnikr__yuwly = bodo.utils.utils.alloc_type(1, in_arr, (-1,))
    blpsb__qtuk = np.empty(1, dtype=np.bool_)
    bkd__zlvz = bodo.utils.utils.alloc_type(1, in_arr, (-1,))
    nxqmm__okyln = False
    mcst__jbwpv = null_value
    for i in range(byjad__haw, ukr__kio, xhcb__fwgx):
        if not isna(in_arr, i):
            nxqmm__okyln = True
            mcst__jbwpv = in_arr[i]
            break
    if rank != shbul__hpzzj:
        cgydj__mtice = bodo.libs.distributed_api.irecv(knz__sght, 1,
            mqb__zjny, cjt__wkvr, True)
        bodo.libs.distributed_api.wait(cgydj__mtice, True)
        mwzi__rvr = bodo.libs.distributed_api.irecv(jnikr__yuwly, 1,
            mqb__zjny, cjt__wkvr, True)
        bodo.libs.distributed_api.wait(mwzi__rvr, True)
        krai__assuy = knz__sght[0]
        kpymm__rmt = jnikr__yuwly[0]
    else:
        krai__assuy = False
        kpymm__rmt = null_value
    if nxqmm__okyln:
        blpsb__qtuk[0] = nxqmm__okyln
        bkd__zlvz[0] = mcst__jbwpv
    else:
        blpsb__qtuk[0] = krai__assuy
        bkd__zlvz[0] = kpymm__rmt
    if rank != jwlh__hnat:
        urw__anvos = bodo.libs.distributed_api.isend(blpsb__qtuk, 1,
            fbbbk__oomrv, cjt__wkvr, True)
        ixzq__una = bodo.libs.distributed_api.isend(bkd__zlvz, 1,
            fbbbk__oomrv, cjt__wkvr, True)
    return krai__assuy, kpymm__rmt


@overload(np.sort, inline='always', no_unliteral=True)
def np_sort(A, axis=-1, kind=None, order=None):
    if not bodo.utils.utils.is_array_typ(A, False) or isinstance(A, types.Array
        ):
        return
    zbj__kpsl = {'axis': axis, 'kind': kind, 'order': order}
    uabc__mrpr = {'axis': -1, 'kind': None, 'order': None}
    check_unsupported_args('np.sort', zbj__kpsl, uabc__mrpr, 'numpy')

    def impl(A, axis=-1, kind=None, order=None):
        return pd.Series(A).sort_values().values
    return impl


def repeat_kernel(A, repeats):
    return A


@overload(repeat_kernel, no_unliteral=True)
def repeat_kernel_overload(A, repeats):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A,
        'Series.repeat()')
    zux__jyvoq = to_str_arr_if_dict_array(A)
    if isinstance(repeats, types.Integer):

        def impl_int(A, repeats):
            A = decode_if_dict_array(A)
            cdg__oxx = len(A)
            nqzq__koj = bodo.utils.utils.alloc_type(cdg__oxx * repeats,
                zux__jyvoq, (-1,))
            for i in range(cdg__oxx):
                imou__bqsrn = i * repeats
                if bodo.libs.array_kernels.isna(A, i):
                    for qvcb__mzim in range(repeats):
                        bodo.libs.array_kernels.setna(nqzq__koj, 
                            imou__bqsrn + qvcb__mzim)
                else:
                    nqzq__koj[imou__bqsrn:imou__bqsrn + repeats] = A[i]
            return nqzq__koj
        return impl_int

    def impl_arr(A, repeats):
        A = decode_if_dict_array(A)
        cdg__oxx = len(A)
        nqzq__koj = bodo.utils.utils.alloc_type(repeats.sum(), zux__jyvoq,
            (-1,))
        imou__bqsrn = 0
        for i in range(cdg__oxx):
            qrpp__zpaxf = repeats[i]
            if bodo.libs.array_kernels.isna(A, i):
                for qvcb__mzim in range(qrpp__zpaxf):
                    bodo.libs.array_kernels.setna(nqzq__koj, imou__bqsrn +
                        qvcb__mzim)
            else:
                nqzq__koj[imou__bqsrn:imou__bqsrn + qrpp__zpaxf] = A[i]
            imou__bqsrn += qrpp__zpaxf
        return nqzq__koj
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
        pva__qdrj = bodo.libs.array_kernels.unique(A)
        return bodo.allgatherv(pva__qdrj, False)
    return impl


@overload(np.union1d, inline='always', no_unliteral=True)
def overload_union1d(A1, A2):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.union1d()')

    def impl(A1, A2):
        thcui__hlvjw = bodo.libs.array_kernels.concat([A1, A2])
        mtyor__wav = bodo.libs.array_kernels.unique(thcui__hlvjw)
        return pd.Series(mtyor__wav).sort_values().values
    return impl


@overload(np.intersect1d, inline='always', no_unliteral=True)
def overload_intersect1d(A1, A2, assume_unique=False, return_indices=False):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    zbj__kpsl = {'assume_unique': assume_unique, 'return_indices':
        return_indices}
    uabc__mrpr = {'assume_unique': False, 'return_indices': False}
    check_unsupported_args('np.intersect1d', zbj__kpsl, uabc__mrpr, 'numpy')
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.intersect1d()'
            )
    if A1.ndim != 1 or A2.ndim != 1:
        raise BodoError('Only 1D arrays supported in np.intersect1d()')

    def impl(A1, A2, assume_unique=False, return_indices=False):
        bgad__roqq = bodo.libs.array_kernels.unique(A1)
        kcjl__zbuy = bodo.libs.array_kernels.unique(A2)
        thcui__hlvjw = bodo.libs.array_kernels.concat([bgad__roqq, kcjl__zbuy])
        nffix__ezxth = pd.Series(thcui__hlvjw).sort_values().values
        return slice_array_intersect1d(nffix__ezxth)
    return impl


@register_jitable
def slice_array_intersect1d(arr):
    unpp__ucpm = arr[1:] == arr[:-1]
    return arr[:-1][unpp__ucpm]


@overload(np.setdiff1d, inline='always', no_unliteral=True)
def overload_setdiff1d(A1, A2, assume_unique=False):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    zbj__kpsl = {'assume_unique': assume_unique}
    uabc__mrpr = {'assume_unique': False}
    check_unsupported_args('np.setdiff1d', zbj__kpsl, uabc__mrpr, 'numpy')
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.setdiff1d()')
    if A1.ndim != 1 or A2.ndim != 1:
        raise BodoError('Only 1D arrays supported in np.setdiff1d()')

    def impl(A1, A2, assume_unique=False):
        bgad__roqq = bodo.libs.array_kernels.unique(A1)
        kcjl__zbuy = bodo.libs.array_kernels.unique(A2)
        unpp__ucpm = calculate_mask_setdiff1d(bgad__roqq, kcjl__zbuy)
        return pd.Series(bgad__roqq[unpp__ucpm]).sort_values().values
    return impl


@register_jitable
def calculate_mask_setdiff1d(A1, A2):
    unpp__ucpm = np.ones(len(A1), np.bool_)
    for i in range(len(A2)):
        unpp__ucpm &= A1 != A2[i]
    return unpp__ucpm


@overload(np.linspace, inline='always', no_unliteral=True)
def np_linspace(start, stop, num=50, endpoint=True, retstep=False, dtype=
    None, axis=0):
    zbj__kpsl = {'retstep': retstep, 'axis': axis}
    uabc__mrpr = {'retstep': False, 'axis': 0}
    check_unsupported_args('np.linspace', zbj__kpsl, uabc__mrpr, 'numpy')
    sqwxs__reiqw = False
    if is_overload_none(dtype):
        zux__jyvoq = np.promote_types(np.promote_types(numba.np.
            numpy_support.as_dtype(start), numba.np.numpy_support.as_dtype(
            stop)), numba.np.numpy_support.as_dtype(types.float64)).type
    else:
        if isinstance(dtype.dtype, types.Integer):
            sqwxs__reiqw = True
        zux__jyvoq = numba.np.numpy_support.as_dtype(dtype).type
    if sqwxs__reiqw:

        def impl_int(start, stop, num=50, endpoint=True, retstep=False,
            dtype=None, axis=0):
            gzox__chmvo = np_linspace_get_stepsize(start, stop, num, endpoint)
            numba.parfors.parfor.init_prange()
            nqzq__koj = np.empty(num, zux__jyvoq)
            for i in numba.parfors.parfor.internal_prange(num):
                nqzq__koj[i] = zux__jyvoq(np.floor(start + i * gzox__chmvo))
            return nqzq__koj
        return impl_int
    else:

        def impl(start, stop, num=50, endpoint=True, retstep=False, dtype=
            None, axis=0):
            gzox__chmvo = np_linspace_get_stepsize(start, stop, num, endpoint)
            numba.parfors.parfor.init_prange()
            nqzq__koj = np.empty(num, zux__jyvoq)
            for i in numba.parfors.parfor.internal_prange(num):
                nqzq__koj[i] = zux__jyvoq(start + i * gzox__chmvo)
            return nqzq__koj
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
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A,
        'np.contains()')
    if not (bodo.utils.utils.is_array_typ(A, False) and A.dtype == types.
        unliteral(val)):
        return

    def impl(A, val):
        numba.parfors.parfor.init_prange()
        lebd__lkc = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                lebd__lkc += A[i] == val
        return lebd__lkc > 0
    return impl


@overload(np.any, inline='always', no_unliteral=True)
def np_any(A, axis=None, out=None, keepdims=None):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A, 'np.any()')
    if not (bodo.utils.utils.is_array_typ(A, False) and A.ndim == 1):
        return
    zbj__kpsl = {'axis': axis, 'out': out, 'keepdims': keepdims}
    uabc__mrpr = {'axis': None, 'out': None, 'keepdims': None}
    check_unsupported_args('np.any', zbj__kpsl, uabc__mrpr, 'numpy')

    def impl(A, axis=None, out=None, keepdims=None):
        numba.parfors.parfor.init_prange()
        lebd__lkc = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                lebd__lkc += int(bool(A[i]))
        return lebd__lkc > 0
    return impl


@overload(np.all, inline='always', no_unliteral=True)
def np_all(A, axis=None, out=None, keepdims=None):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A, 'np.all()')
    if not (bodo.utils.utils.is_array_typ(A, False) and A.ndim == 1):
        return
    zbj__kpsl = {'axis': axis, 'out': out, 'keepdims': keepdims}
    uabc__mrpr = {'axis': None, 'out': None, 'keepdims': None}
    check_unsupported_args('np.any', zbj__kpsl, uabc__mrpr, 'numpy')

    def impl(A, axis=None, out=None, keepdims=None):
        numba.parfors.parfor.init_prange()
        lebd__lkc = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                lebd__lkc += int(bool(A[i]))
        return lebd__lkc == n
    return impl


@overload(np.cbrt, inline='always', no_unliteral=True)
def np_cbrt(A, out=None, where=True, casting='same_kind', order='K', dtype=
    None, subok=True):
    if not (isinstance(A, types.Number) or bodo.utils.utils.is_array_typ(A,
        False) and A.ndim == 1 and isinstance(A.dtype, types.Number)):
        return
    zbj__kpsl = {'out': out, 'where': where, 'casting': casting, 'order':
        order, 'dtype': dtype, 'subok': subok}
    uabc__mrpr = {'out': None, 'where': True, 'casting': 'same_kind',
        'order': 'K', 'dtype': None, 'subok': True}
    check_unsupported_args('np.cbrt', zbj__kpsl, uabc__mrpr, 'numpy')
    if bodo.utils.utils.is_array_typ(A, False):
        qgpmk__zovr = np.promote_types(numba.np.numpy_support.as_dtype(A.
            dtype), numba.np.numpy_support.as_dtype(types.float32)).type

        def impl_arr(A, out=None, where=True, casting='same_kind', order=
            'K', dtype=None, subok=True):
            numba.parfors.parfor.init_prange()
            n = len(A)
            nqzq__koj = np.empty(n, qgpmk__zovr)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(A, i):
                    bodo.libs.array_kernels.setna(nqzq__koj, i)
                    continue
                nqzq__koj[i] = np_cbrt_scalar(A[i], qgpmk__zovr)
            return nqzq__koj
        return impl_arr
    qgpmk__zovr = np.promote_types(numba.np.numpy_support.as_dtype(A),
        numba.np.numpy_support.as_dtype(types.float32)).type

    def impl_scalar(A, out=None, where=True, casting='same_kind', order='K',
        dtype=None, subok=True):
        return np_cbrt_scalar(A, qgpmk__zovr)
    return impl_scalar


@register_jitable
def np_cbrt_scalar(x, float_dtype):
    if np.isnan(x):
        return np.nan
    wgvjo__kbbp = x < 0
    if wgvjo__kbbp:
        x = -x
    res = np.power(float_dtype(x), 1.0 / 3.0)
    if wgvjo__kbbp:
        return -res
    return res


@overload(np.hstack, no_unliteral=True)
def np_hstack(tup):
    mcwa__omsk = isinstance(tup, (types.BaseTuple, types.List))
    jvttg__lrfn = isinstance(tup, (bodo.SeriesType, bodo.hiframes.
        pd_series_ext.HeterogeneousSeriesType)) and isinstance(tup.data, (
        types.BaseTuple, types.List, bodo.NullableTupleType))
    if isinstance(tup, types.BaseTuple):
        for kqq__judk in tup.types:
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(kqq__judk
                , 'numpy.hstack()')
            mcwa__omsk = mcwa__omsk and bodo.utils.utils.is_array_typ(kqq__judk
                , False)
    elif isinstance(tup, types.List):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(tup.dtype,
            'numpy.hstack()')
        mcwa__omsk = bodo.utils.utils.is_array_typ(tup.dtype, False)
    elif jvttg__lrfn:
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(tup,
            'numpy.hstack()')
        zkcrd__sbq = tup.data.tuple_typ if isinstance(tup.data, bodo.
            NullableTupleType) else tup.data
        for kqq__judk in zkcrd__sbq.types:
            jvttg__lrfn = jvttg__lrfn and bodo.utils.utils.is_array_typ(
                kqq__judk, False)
    if not (mcwa__omsk or jvttg__lrfn):
        return
    if jvttg__lrfn:

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
    zbj__kpsl = {'check_valid': check_valid, 'tol': tol}
    uabc__mrpr = {'check_valid': 'warn', 'tol': 1e-08}
    check_unsupported_args('np.random.multivariate_normal', zbj__kpsl,
        uabc__mrpr, 'numpy')
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
        jzkyi__rfyd = mean.shape[0]
        tuuvs__lcdt = size, jzkyi__rfyd
        mnd__zmf = np.random.standard_normal(tuuvs__lcdt)
        cov = cov.astype(np.float64)
        wueo__qtwij, s, snriw__dnraz = np.linalg.svd(cov)
        res = np.dot(mnd__zmf, np.sqrt(s).reshape(jzkyi__rfyd, 1) *
            snriw__dnraz)
        ybv__yol = res + mean
        return ybv__yol
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
            gpjo__ibp = bodo.hiframes.series_kernels._get_type_max_value(arr)
            iruz__crg = typing.builtins.IndexValue(-1, gpjo__ibp)
            for i in numba.parfors.parfor.internal_prange(len(arr)):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                meji__hgj = typing.builtins.IndexValue(i, arr[i])
                iruz__crg = min(iruz__crg, meji__hgj)
            return iruz__crg.index
        return impl_bodo_arr
    if isinstance(arr, CategoricalArrayType):
        assert arr.dtype.ordered, 'Categorical Array must be ordered to select an argmin'
        fkp__gdwaw = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            arr.dtype)

        def impl_cat_arr(arr):
            dtp__xkzkw = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            gpjo__ibp = fkp__gdwaw(len(arr.dtype.categories) + 1)
            iruz__crg = typing.builtins.IndexValue(-1, gpjo__ibp)
            for i in numba.parfors.parfor.internal_prange(len(arr)):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                meji__hgj = typing.builtins.IndexValue(i, dtp__xkzkw[i])
                iruz__crg = min(iruz__crg, meji__hgj)
            return iruz__crg.index
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
            gpjo__ibp = bodo.hiframes.series_kernels._get_type_min_value(arr)
            iruz__crg = typing.builtins.IndexValue(-1, gpjo__ibp)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                meji__hgj = typing.builtins.IndexValue(i, arr[i])
                iruz__crg = max(iruz__crg, meji__hgj)
            return iruz__crg.index
        return impl_bodo_arr
    if isinstance(arr, CategoricalArrayType):
        assert arr.dtype.ordered, 'Categorical Array must be ordered to select an argmin'
        fkp__gdwaw = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            arr.dtype)

        def impl_cat_arr(arr):
            n = len(arr)
            dtp__xkzkw = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            gpjo__ibp = fkp__gdwaw(-1)
            iruz__crg = typing.builtins.IndexValue(-1, gpjo__ibp)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                meji__hgj = typing.builtins.IndexValue(i, dtp__xkzkw[i])
                iruz__crg = max(iruz__crg, meji__hgj)
            return iruz__crg.index
        return impl_cat_arr
    return lambda arr: arr.argmax()


@overload_attribute(types.Array, 'nbytes', inline='always')
def overload_dataframe_index(A):
    return lambda A: A.size * bodo.io.np_io.get_dtype_size(A.dtype)
