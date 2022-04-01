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
        ovb__ayej = arr.dtype('NaT')

        def _setnan_impl(arr, ind, int_nan_const=0):
            arr[ind] = ovb__ayej
        return _setnan_impl
    if isinstance(arr, DatetimeArrayType):
        ovb__ayej = bodo.datetime64ns('NaT')

        def _setnan_impl(arr, ind, int_nan_const=0):
            arr._data[ind] = ovb__ayej
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
            fnj__gqit = bodo.libs.array_item_arr_ext.get_offsets(arr._data)
            fnj__gqit[ind + 1] = fnj__gqit[ind]
            bodo.libs.int_arr_ext.set_bit_to_arr(bodo.libs.
                array_item_arr_ext.get_null_bitmap(arr._data), ind, 0)
        return impl_binary_arr
    if isinstance(arr, bodo.libs.array_item_arr_ext.ArrayItemArrayType):

        def impl_arr_item(arr, ind, int_nan_const=0):
            fnj__gqit = bodo.libs.array_item_arr_ext.get_offsets(arr)
            fnj__gqit[ind + 1] = fnj__gqit[ind]
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
    tpeq__idcgf = arr_tup.count
    vqpk__mkl = 'def f(arr_tup, ind, int_nan_const=0):\n'
    for i in range(tpeq__idcgf):
        vqpk__mkl += '  setna(arr_tup[{}], ind, int_nan_const)\n'.format(i)
    vqpk__mkl += '  return\n'
    qelqd__hiqb = {}
    exec(vqpk__mkl, {'setna': setna}, qelqd__hiqb)
    impl = qelqd__hiqb['f']
    return impl


def setna_slice(arr, s):
    arr[s] = np.nan


@overload(setna_slice, no_unliteral=True)
def overload_setna_slice(arr, s):

    def impl(arr, s):
        wsy__wifsi = numba.cpython.unicode._normalize_slice(s, len(arr))
        for i in range(wsy__wifsi.start, wsy__wifsi.stop, wsy__wifsi.step):
            setna(arr, i)
    return impl


@numba.generated_jit
def first_last_valid_index(arr, index_arr, is_first=True, parallel=False):
    is_first = get_overload_const_bool(is_first)
    if is_first:
        kopo__bvmsm = 'n'
    else:
        kopo__bvmsm = 'n-1, -1, -1'
    vqpk__mkl = f"""def impl(arr, index_arr, is_first=True, parallel=False):
    n = len(arr)
    index_val = index_arr[0]
    has_valid = False
    loc_min = -1
    if parallel:
        rank = bodo.libs.distributed_api.get_rank()
        n_pes = bodo.libs.distributed_api.get_size()
        loc_min = n_pes
    for i in range({kopo__bvmsm}):
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
    qelqd__hiqb = {}
    exec(vqpk__mkl, {'np': np, 'bodo': bodo, 'isna': isna, 'min_op': min_op,
        'box_if_dt64': bodo.utils.conversion.box_if_dt64}, qelqd__hiqb)
    impl = qelqd__hiqb['impl']
    return impl


ll.add_symbol('median_series_computation', quantile_alg.
    median_series_computation)
_median_series_computation = types.ExternalFunction('median_series_computation'
    , types.void(types.voidptr, bodo.libs.array.array_info_type, types.
    bool_, types.bool_))


@numba.njit
def median_series_computation(res, arr, is_parallel, skipna):
    zpot__tiub = array_to_info(arr)
    _median_series_computation(res, zpot__tiub, is_parallel, skipna)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(zpot__tiub)


ll.add_symbol('autocorr_series_computation', quantile_alg.
    autocorr_series_computation)
_autocorr_series_computation = types.ExternalFunction(
    'autocorr_series_computation', types.void(types.voidptr, bodo.libs.
    array.array_info_type, types.int64, types.bool_))


@numba.njit
def autocorr_series_computation(res, arr, lag, is_parallel):
    zpot__tiub = array_to_info(arr)
    _autocorr_series_computation(res, zpot__tiub, lag, is_parallel)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(zpot__tiub)


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
    zpot__tiub = array_to_info(arr)
    _compute_series_monotonicity(res, zpot__tiub, inc_dec, is_parallel)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(zpot__tiub)


@numba.njit
def series_monotonicity(arr, inc_dec, parallel=False):
    res = np.empty(1, types.float64)
    series_monotonicity_call(res.ctypes, arr, inc_dec, parallel)
    xfue__mngx = res[0] > 0.5
    return xfue__mngx


@numba.generated_jit(nopython=True)
def get_valid_entries_from_date_offset(index_arr, offset, initial_date,
    is_last, is_parallel=False):
    if get_overload_const_bool(is_last):
        rpin__wwpmu = '-'
        oked__fqjm = 'index_arr[0] > threshhold_date'
        kopo__bvmsm = '1, n+1'
        hrf__zisl = 'index_arr[-i] <= threshhold_date'
        pzf__gwmao = 'i - 1'
    else:
        rpin__wwpmu = '+'
        oked__fqjm = 'index_arr[-1] < threshhold_date'
        kopo__bvmsm = 'n'
        hrf__zisl = 'index_arr[i] >= threshhold_date'
        pzf__gwmao = 'i'
    vqpk__mkl = (
        'def impl(index_arr, offset, initial_date, is_last, is_parallel=False):\n'
        )
    if types.unliteral(offset) == types.unicode_type:
        vqpk__mkl += (
            '  with numba.objmode(threshhold_date=bodo.pd_timestamp_type):\n')
        vqpk__mkl += (
            '    date_offset = pd.tseries.frequencies.to_offset(offset)\n')
        if not get_overload_const_bool(is_last):
            vqpk__mkl += """    if not isinstance(date_offset, pd._libs.tslibs.Tick) and date_offset.is_on_offset(index_arr[0]):
"""
            vqpk__mkl += (
                '      threshhold_date = initial_date - date_offset.base + date_offset\n'
                )
            vqpk__mkl += '    else:\n'
            vqpk__mkl += '      threshhold_date = initial_date + date_offset\n'
        else:
            vqpk__mkl += (
                f'    threshhold_date = initial_date {rpin__wwpmu} date_offset\n'
                )
    else:
        vqpk__mkl += f'  threshhold_date = initial_date {rpin__wwpmu} offset\n'
    vqpk__mkl += '  local_valid = 0\n'
    vqpk__mkl += f'  n = len(index_arr)\n'
    vqpk__mkl += f'  if n:\n'
    vqpk__mkl += f'    if {oked__fqjm}:\n'
    vqpk__mkl += '      loc_valid = n\n'
    vqpk__mkl += '    else:\n'
    vqpk__mkl += f'      for i in range({kopo__bvmsm}):\n'
    vqpk__mkl += f'        if {hrf__zisl}:\n'
    vqpk__mkl += f'          loc_valid = {pzf__gwmao}\n'
    vqpk__mkl += '          break\n'
    vqpk__mkl += '  if is_parallel:\n'
    vqpk__mkl += (
        '    total_valid = bodo.libs.distributed_api.dist_reduce(loc_valid, sum_op)\n'
        )
    vqpk__mkl += '    return total_valid\n'
    vqpk__mkl += '  else:\n'
    vqpk__mkl += '    return loc_valid\n'
    qelqd__hiqb = {}
    exec(vqpk__mkl, {'bodo': bodo, 'pd': pd, 'numba': numba, 'sum_op':
        sum_op}, qelqd__hiqb)
    return qelqd__hiqb['impl']


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
    kkx__pxboz = numba_to_c_type(sig.args[0].dtype)
    dwp__tgeam = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(32), kkx__pxboz))
    zphto__vfx = args[0]
    wxw__hkl = sig.args[0]
    if isinstance(wxw__hkl, (IntegerArrayType, BooleanArrayType)):
        zphto__vfx = cgutils.create_struct_proxy(wxw__hkl)(context, builder,
            zphto__vfx).data
        wxw__hkl = types.Array(wxw__hkl.dtype, 1, 'C')
    assert wxw__hkl.ndim == 1
    arr = make_array(wxw__hkl)(context, builder, zphto__vfx)
    jugy__dmd = builder.extract_value(arr.shape, 0)
    hgmuo__gni = [builder.bitcast(arr.data, lir.IntType(8).as_pointer()),
        jugy__dmd, args[1], builder.load(dwp__tgeam)]
    omsg__nhpd = [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
        DoubleType(), lir.IntType(32)]
    sshoh__kjy = lir.FunctionType(lir.DoubleType(), omsg__nhpd)
    ctoh__jymk = cgutils.get_or_insert_function(builder.module, sshoh__kjy,
        name='quantile_sequential')
    umj__gnqyf = builder.call(ctoh__jymk, hgmuo__gni)
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return umj__gnqyf


@lower_builtin(quantile_parallel, types.Array, types.float64, types.intp)
@lower_builtin(quantile_parallel, IntegerArrayType, types.float64, types.intp)
@lower_builtin(quantile_parallel, BooleanArrayType, types.float64, types.intp)
def lower_dist_quantile_parallel(context, builder, sig, args):
    kkx__pxboz = numba_to_c_type(sig.args[0].dtype)
    dwp__tgeam = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(32), kkx__pxboz))
    zphto__vfx = args[0]
    wxw__hkl = sig.args[0]
    if isinstance(wxw__hkl, (IntegerArrayType, BooleanArrayType)):
        zphto__vfx = cgutils.create_struct_proxy(wxw__hkl)(context, builder,
            zphto__vfx).data
        wxw__hkl = types.Array(wxw__hkl.dtype, 1, 'C')
    assert wxw__hkl.ndim == 1
    arr = make_array(wxw__hkl)(context, builder, zphto__vfx)
    jugy__dmd = builder.extract_value(arr.shape, 0)
    if len(args) == 3:
        egpqy__vepwe = args[2]
    else:
        egpqy__vepwe = jugy__dmd
    hgmuo__gni = [builder.bitcast(arr.data, lir.IntType(8).as_pointer()),
        jugy__dmd, egpqy__vepwe, args[1], builder.load(dwp__tgeam)]
    omsg__nhpd = [lir.IntType(8).as_pointer(), lir.IntType(64), lir.IntType
        (64), lir.DoubleType(), lir.IntType(32)]
    sshoh__kjy = lir.FunctionType(lir.DoubleType(), omsg__nhpd)
    ctoh__jymk = cgutils.get_or_insert_function(builder.module, sshoh__kjy,
        name='quantile_parallel')
    umj__gnqyf = builder.call(ctoh__jymk, hgmuo__gni)
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return umj__gnqyf


@numba.njit
def min_heapify(arr, ind_arr, n, start, cmp_f):
    fqdts__zulol = start
    kljv__hxcua = 2 * start + 1
    gphfc__ohpvl = 2 * start + 2
    if kljv__hxcua < n and not cmp_f(arr[kljv__hxcua], arr[fqdts__zulol]):
        fqdts__zulol = kljv__hxcua
    if gphfc__ohpvl < n and not cmp_f(arr[gphfc__ohpvl], arr[fqdts__zulol]):
        fqdts__zulol = gphfc__ohpvl
    if fqdts__zulol != start:
        arr[start], arr[fqdts__zulol] = arr[fqdts__zulol], arr[start]
        ind_arr[start], ind_arr[fqdts__zulol] = ind_arr[fqdts__zulol], ind_arr[
            start]
        min_heapify(arr, ind_arr, n, fqdts__zulol, cmp_f)


def select_k_nonan(A, index_arr, m, k):
    return A[:k]


@overload(select_k_nonan, no_unliteral=True)
def select_k_nonan_overload(A, index_arr, m, k):
    dtype = A.dtype
    if isinstance(dtype, types.Integer):
        return lambda A, index_arr, m, k: (A[:k].copy(), index_arr[:k].copy
            (), k)

    def select_k_nonan_float(A, index_arr, m, k):
        nolwg__qdajt = np.empty(k, A.dtype)
        kdbj__jgx = np.empty(k, index_arr.dtype)
        i = 0
        ind = 0
        while i < m and ind < k:
            if not bodo.libs.array_kernels.isna(A, i):
                nolwg__qdajt[ind] = A[i]
                kdbj__jgx[ind] = index_arr[i]
                ind += 1
            i += 1
        if ind < k:
            nolwg__qdajt = nolwg__qdajt[:ind]
            kdbj__jgx = kdbj__jgx[:ind]
        return nolwg__qdajt, kdbj__jgx, i
    return select_k_nonan_float


@numba.njit
def nlargest(A, index_arr, k, is_largest, cmp_f):
    m = len(A)
    if k == 0:
        return A[:0], index_arr[:0]
    if k >= m:
        noqhk__ztjhf = np.sort(A)
        hwwox__jobz = index_arr[np.argsort(A)]
        kxzsd__nzxro = pd.Series(noqhk__ztjhf).notna().values
        noqhk__ztjhf = noqhk__ztjhf[kxzsd__nzxro]
        hwwox__jobz = hwwox__jobz[kxzsd__nzxro]
        if is_largest:
            noqhk__ztjhf = noqhk__ztjhf[::-1]
            hwwox__jobz = hwwox__jobz[::-1]
        return np.ascontiguousarray(noqhk__ztjhf), np.ascontiguousarray(
            hwwox__jobz)
    nolwg__qdajt, kdbj__jgx, start = select_k_nonan(A, index_arr, m, k)
    kdbj__jgx = kdbj__jgx[nolwg__qdajt.argsort()]
    nolwg__qdajt.sort()
    if not is_largest:
        nolwg__qdajt = np.ascontiguousarray(nolwg__qdajt[::-1])
        kdbj__jgx = np.ascontiguousarray(kdbj__jgx[::-1])
    for i in range(start, m):
        if cmp_f(A[i], nolwg__qdajt[0]):
            nolwg__qdajt[0] = A[i]
            kdbj__jgx[0] = index_arr[i]
            min_heapify(nolwg__qdajt, kdbj__jgx, k, 0, cmp_f)
    kdbj__jgx = kdbj__jgx[nolwg__qdajt.argsort()]
    nolwg__qdajt.sort()
    if is_largest:
        nolwg__qdajt = nolwg__qdajt[::-1]
        kdbj__jgx = kdbj__jgx[::-1]
    return np.ascontiguousarray(nolwg__qdajt), np.ascontiguousarray(kdbj__jgx)


@numba.njit
def nlargest_parallel(A, I, k, is_largest, cmp_f):
    ovqgu__vrpz = bodo.libs.distributed_api.get_rank()
    hvcpn__aid, fboc__bxii = nlargest(A, I, k, is_largest, cmp_f)
    jctp__onty = bodo.libs.distributed_api.gatherv(hvcpn__aid)
    tuucc__qnpc = bodo.libs.distributed_api.gatherv(fboc__bxii)
    if ovqgu__vrpz == MPI_ROOT:
        res, cdhew__jcr = nlargest(jctp__onty, tuucc__qnpc, k, is_largest,
            cmp_f)
    else:
        res = np.empty(k, A.dtype)
        cdhew__jcr = np.empty(k, I.dtype)
    bodo.libs.distributed_api.bcast(res)
    bodo.libs.distributed_api.bcast(cdhew__jcr)
    return res, cdhew__jcr


@numba.njit(no_cpython_wrapper=True, cache=True)
def nancorr(mat, cov=0, minpv=1, parallel=False):
    ymt__axle, qow__pyo = mat.shape
    mxda__hnc = np.empty((qow__pyo, qow__pyo), dtype=np.float64)
    for fooiv__prw in range(qow__pyo):
        for ccz__kug in range(fooiv__prw + 1):
            uipcd__xge = 0
            vnhd__loot = aqhj__iffna = aaxlr__bqp = wxqww__gha = 0.0
            for i in range(ymt__axle):
                if np.isfinite(mat[i, fooiv__prw]) and np.isfinite(mat[i,
                    ccz__kug]):
                    inyz__ergc = mat[i, fooiv__prw]
                    yjhz__octki = mat[i, ccz__kug]
                    uipcd__xge += 1
                    aaxlr__bqp += inyz__ergc
                    wxqww__gha += yjhz__octki
            if parallel:
                uipcd__xge = bodo.libs.distributed_api.dist_reduce(uipcd__xge,
                    sum_op)
                aaxlr__bqp = bodo.libs.distributed_api.dist_reduce(aaxlr__bqp,
                    sum_op)
                wxqww__gha = bodo.libs.distributed_api.dist_reduce(wxqww__gha,
                    sum_op)
            if uipcd__xge < minpv:
                mxda__hnc[fooiv__prw, ccz__kug] = mxda__hnc[ccz__kug,
                    fooiv__prw] = np.nan
            else:
                npsi__yts = aaxlr__bqp / uipcd__xge
                qrje__cdyx = wxqww__gha / uipcd__xge
                aaxlr__bqp = 0.0
                for i in range(ymt__axle):
                    if np.isfinite(mat[i, fooiv__prw]) and np.isfinite(mat[
                        i, ccz__kug]):
                        inyz__ergc = mat[i, fooiv__prw] - npsi__yts
                        yjhz__octki = mat[i, ccz__kug] - qrje__cdyx
                        aaxlr__bqp += inyz__ergc * yjhz__octki
                        vnhd__loot += inyz__ergc * inyz__ergc
                        aqhj__iffna += yjhz__octki * yjhz__octki
                if parallel:
                    aaxlr__bqp = bodo.libs.distributed_api.dist_reduce(
                        aaxlr__bqp, sum_op)
                    vnhd__loot = bodo.libs.distributed_api.dist_reduce(
                        vnhd__loot, sum_op)
                    aqhj__iffna = bodo.libs.distributed_api.dist_reduce(
                        aqhj__iffna, sum_op)
                dbfzj__ypp = uipcd__xge - 1.0 if cov else sqrt(vnhd__loot *
                    aqhj__iffna)
                if dbfzj__ypp != 0.0:
                    mxda__hnc[fooiv__prw, ccz__kug] = mxda__hnc[ccz__kug,
                        fooiv__prw] = aaxlr__bqp / dbfzj__ypp
                else:
                    mxda__hnc[fooiv__prw, ccz__kug] = mxda__hnc[ccz__kug,
                        fooiv__prw] = np.nan
    return mxda__hnc


@numba.generated_jit(nopython=True)
def duplicated(data, parallel=False):
    n = len(data)
    if n == 0:
        return lambda data, parallel=False: np.empty(0, dtype=np.bool_)
    bnc__xljam = n != 1
    vqpk__mkl = 'def impl(data, parallel=False):\n'
    vqpk__mkl += '  if parallel:\n'
    pbu__xnxn = ', '.join(f'array_to_info(data[{i}])' for i in range(n))
    vqpk__mkl += f'    cpp_table = arr_info_list_to_table([{pbu__xnxn}])\n'
    vqpk__mkl += (
        f'    out_cpp_table = bodo.libs.array.shuffle_table(cpp_table, {n}, parallel, 1)\n'
        )
    fjbsa__eyy = ', '.join(
        f'info_to_array(info_from_table(out_cpp_table, {i}), data[{i}])' for
        i in range(n))
    vqpk__mkl += f'    data = ({fjbsa__eyy},)\n'
    vqpk__mkl += (
        '    shuffle_info = bodo.libs.array.get_shuffle_info(out_cpp_table)\n')
    vqpk__mkl += '    bodo.libs.array.delete_table(out_cpp_table)\n'
    vqpk__mkl += '    bodo.libs.array.delete_table(cpp_table)\n'
    vqpk__mkl += '  n = len(data[0])\n'
    vqpk__mkl += '  out = np.empty(n, np.bool_)\n'
    vqpk__mkl += '  uniqs = dict()\n'
    if bnc__xljam:
        vqpk__mkl += '  for i in range(n):\n'
        tjx__wxipk = ', '.join(f'data[{i}][i]' for i in range(n))
        kab__owu = ',  '.join(f'bodo.libs.array_kernels.isna(data[{i}], i)' for
            i in range(n))
        vqpk__mkl += f"""    val = bodo.libs.nullable_tuple_ext.build_nullable_tuple(({tjx__wxipk},), ({kab__owu},))
"""
        vqpk__mkl += '    if val in uniqs:\n'
        vqpk__mkl += '      out[i] = True\n'
        vqpk__mkl += '    else:\n'
        vqpk__mkl += '      out[i] = False\n'
        vqpk__mkl += '      uniqs[val] = 0\n'
    else:
        vqpk__mkl += '  data = data[0]\n'
        vqpk__mkl += '  hasna = False\n'
        vqpk__mkl += '  for i in range(n):\n'
        vqpk__mkl += '    if bodo.libs.array_kernels.isna(data, i):\n'
        vqpk__mkl += '      out[i] = hasna\n'
        vqpk__mkl += '      hasna = True\n'
        vqpk__mkl += '    else:\n'
        vqpk__mkl += '      val = data[i]\n'
        vqpk__mkl += '      if val in uniqs:\n'
        vqpk__mkl += '        out[i] = True\n'
        vqpk__mkl += '      else:\n'
        vqpk__mkl += '        out[i] = False\n'
        vqpk__mkl += '        uniqs[val] = 0\n'
    vqpk__mkl += '  if parallel:\n'
    vqpk__mkl += (
        '    out = bodo.hiframes.pd_groupby_ext.reverse_shuffle(out, shuffle_info)\n'
        )
    vqpk__mkl += '  return out\n'
    qelqd__hiqb = {}
    exec(vqpk__mkl, {'bodo': bodo, 'np': np, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'info_to_array':
        info_to_array, 'info_from_table': info_from_table}, qelqd__hiqb)
    impl = qelqd__hiqb['impl']
    return impl


def sample_table_operation(data, ind_arr, n, frac, replace, parallel=False):
    return data, ind_arr


@overload(sample_table_operation, no_unliteral=True)
def overload_sample_table_operation(data, ind_arr, n, frac, replace,
    parallel=False):
    tpeq__idcgf = len(data)
    vqpk__mkl = 'def impl(data, ind_arr, n, frac, replace, parallel=False):\n'
    vqpk__mkl += '  info_list_total = [{}, array_to_info(ind_arr)]\n'.format(
        ', '.join('array_to_info(data[{}])'.format(x) for x in range(
        tpeq__idcgf)))
    vqpk__mkl += '  table_total = arr_info_list_to_table(info_list_total)\n'
    vqpk__mkl += (
        '  out_table = sample_table(table_total, n, frac, replace, parallel)\n'
        .format(tpeq__idcgf))
    for gsq__ymq in range(tpeq__idcgf):
        vqpk__mkl += (
            '  out_arr_{} = info_to_array(info_from_table(out_table, {}), data[{}])\n'
            .format(gsq__ymq, gsq__ymq, gsq__ymq))
    vqpk__mkl += (
        '  out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)\n'
        .format(tpeq__idcgf))
    vqpk__mkl += '  delete_table(out_table)\n'
    vqpk__mkl += '  delete_table(table_total)\n'
    vqpk__mkl += '  return ({},), out_arr_index\n'.format(', '.join(
        'out_arr_{}'.format(i) for i in range(tpeq__idcgf)))
    qelqd__hiqb = {}
    exec(vqpk__mkl, {'np': np, 'bodo': bodo, 'array_to_info': array_to_info,
        'sample_table': sample_table, 'arr_info_list_to_table':
        arr_info_list_to_table, 'info_from_table': info_from_table,
        'info_to_array': info_to_array, 'delete_table': delete_table,
        'delete_table_decref_arrays': delete_table_decref_arrays}, qelqd__hiqb)
    impl = qelqd__hiqb['impl']
    return impl


def drop_duplicates(data, ind_arr, ncols, parallel=False):
    return data, ind_arr


@overload(drop_duplicates, no_unliteral=True)
def overload_drop_duplicates(data, ind_arr, ncols, parallel=False):
    tpeq__idcgf = len(data)
    vqpk__mkl = 'def impl(data, ind_arr, ncols, parallel=False):\n'
    vqpk__mkl += '  info_list_total = [{}, array_to_info(ind_arr)]\n'.format(
        ', '.join('array_to_info(data[{}])'.format(x) for x in range(
        tpeq__idcgf)))
    vqpk__mkl += '  table_total = arr_info_list_to_table(info_list_total)\n'
    vqpk__mkl += '  keep_i = 0\n'
    vqpk__mkl += """  out_table = drop_duplicates_table(table_total, parallel, ncols, keep_i, False, True)
"""
    for gsq__ymq in range(tpeq__idcgf):
        vqpk__mkl += (
            '  out_arr_{} = info_to_array(info_from_table(out_table, {}), data[{}])\n'
            .format(gsq__ymq, gsq__ymq, gsq__ymq))
    vqpk__mkl += (
        '  out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)\n'
        .format(tpeq__idcgf))
    vqpk__mkl += '  delete_table(out_table)\n'
    vqpk__mkl += '  delete_table(table_total)\n'
    vqpk__mkl += '  return ({},), out_arr_index\n'.format(', '.join(
        'out_arr_{}'.format(i) for i in range(tpeq__idcgf)))
    qelqd__hiqb = {}
    exec(vqpk__mkl, {'np': np, 'bodo': bodo, 'array_to_info': array_to_info,
        'drop_duplicates_table': drop_duplicates_table,
        'arr_info_list_to_table': arr_info_list_to_table, 'info_from_table':
        info_from_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays}, qelqd__hiqb)
    impl = qelqd__hiqb['impl']
    return impl


def drop_duplicates_array(data_arr, parallel=False):
    return data_arr


@overload(drop_duplicates_array, no_unliteral=True)
def overload_drop_duplicates_array(data_arr, parallel=False):

    def impl(data_arr, parallel=False):
        vhj__hzcb = [array_to_info(data_arr)]
        powm__keb = arr_info_list_to_table(vhj__hzcb)
        hst__rikl = 0
        rdo__iras = drop_duplicates_table(powm__keb, parallel, 1, hst__rikl,
            False, True)
        zara__kmox = info_to_array(info_from_table(rdo__iras, 0), data_arr)
        delete_table(rdo__iras)
        delete_table(powm__keb)
        return zara__kmox
    return impl


def dropna(data, how, thresh, subset, parallel=False):
    return data


@overload(dropna, no_unliteral=True)
def overload_dropna(data, how, thresh, subset):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
        'bodo.dropna()')
    iom__wona = len(data.types)
    qnkrs__wfog = [('out' + str(i)) for i in range(iom__wona)]
    trz__bahz = get_overload_const_list(subset)
    how = get_overload_const_str(how)
    qba__hfznt = ['isna(data[{}], i)'.format(i) for i in trz__bahz]
    wplhi__inso = 'not ({})'.format(' or '.join(qba__hfznt))
    if not is_overload_none(thresh):
        wplhi__inso = '(({}) <= ({}) - thresh)'.format(' + '.join(
            qba__hfznt), iom__wona - 1)
    elif how == 'all':
        wplhi__inso = 'not ({})'.format(' and '.join(qba__hfznt))
    vqpk__mkl = 'def _dropna_imp(data, how, thresh, subset):\n'
    vqpk__mkl += '  old_len = len(data[0])\n'
    vqpk__mkl += '  new_len = 0\n'
    vqpk__mkl += '  for i in range(old_len):\n'
    vqpk__mkl += '    if {}:\n'.format(wplhi__inso)
    vqpk__mkl += '      new_len += 1\n'
    for i, out in enumerate(qnkrs__wfog):
        if isinstance(data[i], bodo.CategoricalArrayType):
            vqpk__mkl += (
                '  {0} = bodo.utils.utils.alloc_type(new_len, data[{1}], (-1,))\n'
                .format(out, i))
        else:
            vqpk__mkl += (
                '  {0} = bodo.utils.utils.alloc_type(new_len, t{1}, (-1,))\n'
                .format(out, i))
    vqpk__mkl += '  curr_ind = 0\n'
    vqpk__mkl += '  for i in range(old_len):\n'
    vqpk__mkl += '    if {}:\n'.format(wplhi__inso)
    for i in range(iom__wona):
        vqpk__mkl += '      if isna(data[{}], i):\n'.format(i)
        vqpk__mkl += '        setna({}, curr_ind)\n'.format(qnkrs__wfog[i])
        vqpk__mkl += '      else:\n'
        vqpk__mkl += '        {}[curr_ind] = data[{}][i]\n'.format(qnkrs__wfog
            [i], i)
    vqpk__mkl += '      curr_ind += 1\n'
    vqpk__mkl += '  return {}\n'.format(', '.join(qnkrs__wfog))
    qelqd__hiqb = {}
    yrqz__loln = {'t{}'.format(i): fqd__rfsbt for i, fqd__rfsbt in
        enumerate(data.types)}
    yrqz__loln.update({'isna': isna, 'setna': setna, 'init_nested_counts':
        bodo.utils.indexing.init_nested_counts, 'add_nested_counts': bodo.
        utils.indexing.add_nested_counts, 'bodo': bodo})
    exec(vqpk__mkl, yrqz__loln, qelqd__hiqb)
    yxz__tvzj = qelqd__hiqb['_dropna_imp']
    return yxz__tvzj


def get(arr, ind):
    return pd.Series(arr).str.get(ind)


@overload(get, no_unliteral=True)
def overload_get(arr, ind):
    if isinstance(arr, ArrayItemArrayType):
        wxw__hkl = arr.dtype
        qdcfy__fmv = wxw__hkl.dtype

        def get_arr_item(arr, ind):
            n = len(arr)
            baxt__atpl = init_nested_counts(qdcfy__fmv)
            for k in range(n):
                if bodo.libs.array_kernels.isna(arr, k):
                    continue
                val = arr[k]
                if not len(val) > ind >= -len(val
                    ) or bodo.libs.array_kernels.isna(val, ind):
                    continue
                baxt__atpl = add_nested_counts(baxt__atpl, val[ind])
            zara__kmox = bodo.utils.utils.alloc_type(n, wxw__hkl, baxt__atpl)
            for ysavt__tlsct in range(n):
                if bodo.libs.array_kernels.isna(arr, ysavt__tlsct):
                    setna(zara__kmox, ysavt__tlsct)
                    continue
                val = arr[ysavt__tlsct]
                if not len(val) > ind >= -len(val
                    ) or bodo.libs.array_kernels.isna(val, ind):
                    setna(zara__kmox, ysavt__tlsct)
                    continue
                zara__kmox[ysavt__tlsct] = val[ind]
            return zara__kmox
        return get_arr_item


def _is_same_categorical_array_type(arr_types):
    from bodo.hiframes.pd_categorical_ext import _to_readonly
    if not isinstance(arr_types, types.BaseTuple) or len(arr_types) == 0:
        return False
    bpz__puz = _to_readonly(arr_types.types[0])
    return all(isinstance(fqd__rfsbt, CategoricalArrayType) and 
        _to_readonly(fqd__rfsbt) == bpz__puz for fqd__rfsbt in arr_types.types)


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
        igjol__dyp = arr_list.dtype.dtype

        def array_item_concat_impl(arr_list):
            tegln__msnas = 0
            zcu__bhegt = []
            for A in arr_list:
                keao__zakf = len(A)
                bodo.libs.array_item_arr_ext.trim_excess_data(A)
                zcu__bhegt.append(bodo.libs.array_item_arr_ext.get_data(A))
                tegln__msnas += keao__zakf
            pdt__gnm = np.empty(tegln__msnas + 1, offset_type)
            ofzby__hewm = bodo.libs.array_kernels.concat(zcu__bhegt)
            skyy__ygnew = np.empty(tegln__msnas + 7 >> 3, np.uint8)
            hwx__yctp = 0
            icokn__dpjqu = 0
            for A in arr_list:
                swl__aukpm = bodo.libs.array_item_arr_ext.get_offsets(A)
                toypx__mmpcs = bodo.libs.array_item_arr_ext.get_null_bitmap(A)
                keao__zakf = len(A)
                zuzjj__qgsf = swl__aukpm[keao__zakf]
                for i in range(keao__zakf):
                    pdt__gnm[i + hwx__yctp] = swl__aukpm[i] + icokn__dpjqu
                    qrxx__xgjj = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        toypx__mmpcs, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(skyy__ygnew, i +
                        hwx__yctp, qrxx__xgjj)
                hwx__yctp += keao__zakf
                icokn__dpjqu += zuzjj__qgsf
            pdt__gnm[hwx__yctp] = icokn__dpjqu
            zara__kmox = bodo.libs.array_item_arr_ext.init_array_item_array(
                tegln__msnas, ofzby__hewm, pdt__gnm, skyy__ygnew)
            return zara__kmox
        return array_item_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, bodo.StructArrayType):
        kny__pbrxv = arr_list.dtype.names
        vqpk__mkl = 'def struct_array_concat_impl(arr_list):\n'
        vqpk__mkl += f'    n_all = 0\n'
        for i in range(len(kny__pbrxv)):
            vqpk__mkl += f'    concat_list{i} = []\n'
        vqpk__mkl += '    for A in arr_list:\n'
        vqpk__mkl += (
            '        data_tuple = bodo.libs.struct_arr_ext.get_data(A)\n')
        for i in range(len(kny__pbrxv)):
            vqpk__mkl += f'        concat_list{i}.append(data_tuple[{i}])\n'
        vqpk__mkl += '        n_all += len(A)\n'
        vqpk__mkl += '    n_bytes = (n_all + 7) >> 3\n'
        vqpk__mkl += '    new_mask = np.empty(n_bytes, np.uint8)\n'
        vqpk__mkl += '    curr_bit = 0\n'
        vqpk__mkl += '    for A in arr_list:\n'
        vqpk__mkl += (
            '        old_mask = bodo.libs.struct_arr_ext.get_null_bitmap(A)\n')
        vqpk__mkl += '        for j in range(len(A)):\n'
        vqpk__mkl += (
            '            bit = bodo.libs.int_arr_ext.get_bit_bitmap_arr(old_mask, j)\n'
            )
        vqpk__mkl += (
            '            bodo.libs.int_arr_ext.set_bit_to_arr(new_mask, curr_bit, bit)\n'
            )
        vqpk__mkl += '            curr_bit += 1\n'
        vqpk__mkl += '    return bodo.libs.struct_arr_ext.init_struct_arr(\n'
        vzia__pywoc = ', '.join([
            f'bodo.libs.array_kernels.concat(concat_list{i})' for i in
            range(len(kny__pbrxv))])
        vqpk__mkl += f'        ({vzia__pywoc},),\n'
        vqpk__mkl += '        new_mask,\n'
        vqpk__mkl += f'        {kny__pbrxv},\n'
        vqpk__mkl += '    )\n'
        qelqd__hiqb = {}
        exec(vqpk__mkl, {'bodo': bodo, 'np': np}, qelqd__hiqb)
        return qelqd__hiqb['struct_array_concat_impl']
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == datetime_date_array_type:

        def datetime_date_array_concat_impl(arr_list):
            fks__oxudc = 0
            for A in arr_list:
                fks__oxudc += len(A)
            obg__xwkw = (bodo.hiframes.datetime_date_ext.
                alloc_datetime_date_array(fks__oxudc))
            yspud__hakj = 0
            for A in arr_list:
                for i in range(len(A)):
                    obg__xwkw._data[i + yspud__hakj] = A._data[i]
                    qrxx__xgjj = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(obg__xwkw.
                        _null_bitmap, i + yspud__hakj, qrxx__xgjj)
                yspud__hakj += len(A)
            return obg__xwkw
        return datetime_date_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == datetime_timedelta_array_type:

        def datetime_timedelta_array_concat_impl(arr_list):
            fks__oxudc = 0
            for A in arr_list:
                fks__oxudc += len(A)
            obg__xwkw = (bodo.hiframes.datetime_timedelta_ext.
                alloc_datetime_timedelta_array(fks__oxudc))
            yspud__hakj = 0
            for A in arr_list:
                for i in range(len(A)):
                    obg__xwkw._days_data[i + yspud__hakj] = A._days_data[i]
                    obg__xwkw._seconds_data[i + yspud__hakj] = A._seconds_data[
                        i]
                    obg__xwkw._microseconds_data[i + yspud__hakj
                        ] = A._microseconds_data[i]
                    qrxx__xgjj = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(obg__xwkw.
                        _null_bitmap, i + yspud__hakj, qrxx__xgjj)
                yspud__hakj += len(A)
            return obg__xwkw
        return datetime_timedelta_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, DecimalArrayType):
        tyapj__wmr = arr_list.dtype.precision
        xotlw__yapu = arr_list.dtype.scale

        def decimal_array_concat_impl(arr_list):
            fks__oxudc = 0
            for A in arr_list:
                fks__oxudc += len(A)
            obg__xwkw = bodo.libs.decimal_arr_ext.alloc_decimal_array(
                fks__oxudc, tyapj__wmr, xotlw__yapu)
            yspud__hakj = 0
            for A in arr_list:
                for i in range(len(A)):
                    obg__xwkw._data[i + yspud__hakj] = A._data[i]
                    qrxx__xgjj = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(obg__xwkw.
                        _null_bitmap, i + yspud__hakj, qrxx__xgjj)
                yspud__hakj += len(A)
            return obg__xwkw
        return decimal_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and (is_str_arr_type
        (arr_list.dtype) or arr_list.dtype == bodo.binary_array_type
        ) or isinstance(arr_list, types.BaseTuple) and all(is_str_arr_type(
        fqd__rfsbt) for fqd__rfsbt in arr_list.types):
        if isinstance(arr_list, types.BaseTuple):
            bvdad__iunqr = arr_list.types[0]
        else:
            bvdad__iunqr = arr_list.dtype
        bvdad__iunqr = to_str_arr_if_dict_array(bvdad__iunqr)

        def impl_str(arr_list):
            arr_list = decode_if_dict_array(arr_list)
            orr__dkdnb = 0
            fzys__aktky = 0
            for A in arr_list:
                arr = A
                orr__dkdnb += len(arr)
                fzys__aktky += bodo.libs.str_arr_ext.num_total_chars(arr)
            zara__kmox = bodo.utils.utils.alloc_type(orr__dkdnb,
                bvdad__iunqr, (fzys__aktky,))
            bodo.libs.str_arr_ext.set_null_bits_to_value(zara__kmox, -1)
            cmq__aqa = 0
            kwlwg__afvxv = 0
            for A in arr_list:
                arr = A
                bodo.libs.str_arr_ext.set_string_array_range(zara__kmox,
                    arr, cmq__aqa, kwlwg__afvxv)
                cmq__aqa += len(arr)
                kwlwg__afvxv += bodo.libs.str_arr_ext.num_total_chars(arr)
            return zara__kmox
        return impl_str
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, IntegerArrayType) or isinstance(arr_list, types.
        BaseTuple) and all(isinstance(fqd__rfsbt.dtype, types.Integer) for
        fqd__rfsbt in arr_list.types) and any(isinstance(fqd__rfsbt,
        IntegerArrayType) for fqd__rfsbt in arr_list.types):

        def impl_int_arr_list(arr_list):
            dawqs__inq = convert_to_nullable_tup(arr_list)
            maov__vbvtx = []
            lfvy__nebep = 0
            for A in dawqs__inq:
                maov__vbvtx.append(A._data)
                lfvy__nebep += len(A)
            ofzby__hewm = bodo.libs.array_kernels.concat(maov__vbvtx)
            ozolg__ykki = lfvy__nebep + 7 >> 3
            gdryf__fbzz = np.empty(ozolg__ykki, np.uint8)
            lete__fuum = 0
            for A in dawqs__inq:
                rljc__ifsib = A._null_bitmap
                for ysavt__tlsct in range(len(A)):
                    qrxx__xgjj = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        rljc__ifsib, ysavt__tlsct)
                    bodo.libs.int_arr_ext.set_bit_to_arr(gdryf__fbzz,
                        lete__fuum, qrxx__xgjj)
                    lete__fuum += 1
            return bodo.libs.int_arr_ext.init_integer_array(ofzby__hewm,
                gdryf__fbzz)
        return impl_int_arr_list
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == boolean_array or isinstance(arr_list, types
        .BaseTuple) and all(fqd__rfsbt.dtype == types.bool_ for fqd__rfsbt in
        arr_list.types) and any(fqd__rfsbt == boolean_array for fqd__rfsbt in
        arr_list.types):

        def impl_bool_arr_list(arr_list):
            dawqs__inq = convert_to_nullable_tup(arr_list)
            maov__vbvtx = []
            lfvy__nebep = 0
            for A in dawqs__inq:
                maov__vbvtx.append(A._data)
                lfvy__nebep += len(A)
            ofzby__hewm = bodo.libs.array_kernels.concat(maov__vbvtx)
            ozolg__ykki = lfvy__nebep + 7 >> 3
            gdryf__fbzz = np.empty(ozolg__ykki, np.uint8)
            lete__fuum = 0
            for A in dawqs__inq:
                rljc__ifsib = A._null_bitmap
                for ysavt__tlsct in range(len(A)):
                    qrxx__xgjj = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        rljc__ifsib, ysavt__tlsct)
                    bodo.libs.int_arr_ext.set_bit_to_arr(gdryf__fbzz,
                        lete__fuum, qrxx__xgjj)
                    lete__fuum += 1
            return bodo.libs.bool_arr_ext.init_bool_array(ofzby__hewm,
                gdryf__fbzz)
        return impl_bool_arr_list
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, CategoricalArrayType):

        def cat_array_concat_impl(arr_list):
            exxc__azb = []
            for A in arr_list:
                exxc__azb.append(A.codes)
            return init_categorical_array(bodo.libs.array_kernels.concat(
                exxc__azb), arr_list[0].dtype)
        return cat_array_concat_impl
    if _is_same_categorical_array_type(arr_list):
        vflyx__jkf = ', '.join(f'arr_list[{i}].codes' for i in range(len(
            arr_list)))
        vqpk__mkl = 'def impl(arr_list):\n'
        vqpk__mkl += f"""    return init_categorical_array(bodo.libs.array_kernels.concat(({vflyx__jkf},)), arr_list[0].dtype)
"""
        ywuv__epqmj = {}
        exec(vqpk__mkl, {'bodo': bodo, 'init_categorical_array':
            init_categorical_array}, ywuv__epqmj)
        return ywuv__epqmj['impl']
    if isinstance(arr_list, types.List) and isinstance(arr_list.dtype,
        types.Array) and arr_list.dtype.ndim == 1:
        dtype = arr_list.dtype.dtype

        def impl_np_arr_list(arr_list):
            lfvy__nebep = 0
            for A in arr_list:
                lfvy__nebep += len(A)
            zara__kmox = np.empty(lfvy__nebep, dtype)
            oix__pld = 0
            for A in arr_list:
                n = len(A)
                zara__kmox[oix__pld:oix__pld + n] = A
                oix__pld += n
            return zara__kmox
        return impl_np_arr_list
    if isinstance(arr_list, types.BaseTuple) and any(isinstance(fqd__rfsbt,
        (types.Array, IntegerArrayType)) and isinstance(fqd__rfsbt.dtype,
        types.Integer) for fqd__rfsbt in arr_list.types) and any(isinstance
        (fqd__rfsbt, types.Array) and isinstance(fqd__rfsbt.dtype, types.
        Float) for fqd__rfsbt in arr_list.types):
        return lambda arr_list: np.concatenate(astype_float_tup(arr_list))
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, bodo.MapArrayType):

        def impl_map_arr_list(arr_list):
            zufxn__ojw = []
            for A in arr_list:
                zufxn__ojw.append(A._data)
            mamxl__qbea = bodo.libs.array_kernels.concat(zufxn__ojw)
            mxda__hnc = bodo.libs.map_arr_ext.init_map_arr(mamxl__qbea)
            return mxda__hnc
        return impl_map_arr_list
    for wwnu__mstq in arr_list:
        if not isinstance(wwnu__mstq, types.Array):
            raise_bodo_error(f'concat of array types {arr_list} not supported')
    return lambda arr_list: np.concatenate(arr_list)


def astype_float_tup(arr_tup):
    return tuple(fqd__rfsbt.astype(np.float64) for fqd__rfsbt in arr_tup)


@overload(astype_float_tup, no_unliteral=True)
def overload_astype_float_tup(arr_tup):
    assert isinstance(arr_tup, types.BaseTuple)
    tpeq__idcgf = len(arr_tup.types)
    vqpk__mkl = 'def f(arr_tup):\n'
    vqpk__mkl += '  return ({}{})\n'.format(','.join(
        'arr_tup[{}].astype(np.float64)'.format(i) for i in range(
        tpeq__idcgf)), ',' if tpeq__idcgf == 1 else '')
    qelqd__hiqb = {}
    exec(vqpk__mkl, {'np': np}, qelqd__hiqb)
    pjix__xthj = qelqd__hiqb['f']
    return pjix__xthj


def convert_to_nullable_tup(arr_tup):
    return arr_tup


@overload(convert_to_nullable_tup, no_unliteral=True)
def overload_convert_to_nullable_tup(arr_tup):
    if isinstance(arr_tup, (types.UniTuple, types.List)) and isinstance(arr_tup
        .dtype, (IntegerArrayType, BooleanArrayType)):
        return lambda arr_tup: arr_tup
    assert isinstance(arr_tup, types.BaseTuple)
    tpeq__idcgf = len(arr_tup.types)
    qszse__gzk = find_common_np_dtype(arr_tup.types)
    qdcfy__fmv = None
    scxbe__dmt = ''
    if isinstance(qszse__gzk, types.Integer):
        qdcfy__fmv = bodo.libs.int_arr_ext.IntDtype(qszse__gzk)
        scxbe__dmt = '.astype(out_dtype, False)'
    vqpk__mkl = 'def f(arr_tup):\n'
    vqpk__mkl += '  return ({}{})\n'.format(','.join(
        'bodo.utils.conversion.coerce_to_array(arr_tup[{}], use_nullable_array=True){}'
        .format(i, scxbe__dmt) for i in range(tpeq__idcgf)), ',' if 
        tpeq__idcgf == 1 else '')
    qelqd__hiqb = {}
    exec(vqpk__mkl, {'bodo': bodo, 'out_dtype': qdcfy__fmv}, qelqd__hiqb)
    lbqa__nqbp = qelqd__hiqb['f']
    return lbqa__nqbp


def nunique(A, dropna):
    return len(set(A))


def nunique_parallel(A, dropna):
    return len(set(A))


@overload(nunique, no_unliteral=True)
def nunique_overload(A, dropna):

    def nunique_seq(A, dropna):
        s, dgo__frw = build_set_seen_na(A)
        return len(s) + int(not dropna and dgo__frw)
    return nunique_seq


@overload(nunique_parallel, no_unliteral=True)
def nunique_overload_parallel(A, dropna):
    sum_op = bodo.libs.distributed_api.Reduce_Type.Sum.value

    def nunique_par(A, dropna):
        sjy__gqj = bodo.libs.array_kernels.unique(A, dropna, parallel=True)
        jeyz__jkxgn = len(sjy__gqj)
        return bodo.libs.distributed_api.dist_reduce(jeyz__jkxgn, np.int32(
            sum_op))
    return nunique_par


def unique(A, dropna=False, parallel=False):
    return np.array([pgv__ipl for pgv__ipl in set(A)]).astype(A.dtype)


def cummin(A):
    return A


@overload(cummin, no_unliteral=True)
def cummin_overload(A):
    if isinstance(A.dtype, types.Float):
        nmcta__jjy = np.finfo(A.dtype(1).dtype).max
    else:
        nmcta__jjy = np.iinfo(A.dtype(1).dtype).max

    def impl(A):
        n = len(A)
        zara__kmox = np.empty(n, A.dtype)
        wwk__xejlg = nmcta__jjy
        for i in range(n):
            wwk__xejlg = min(wwk__xejlg, A[i])
            zara__kmox[i] = wwk__xejlg
        return zara__kmox
    return impl


def cummax(A):
    return A


@overload(cummax, no_unliteral=True)
def cummax_overload(A):
    if isinstance(A.dtype, types.Float):
        nmcta__jjy = np.finfo(A.dtype(1).dtype).min
    else:
        nmcta__jjy = np.iinfo(A.dtype(1).dtype).min

    def impl(A):
        n = len(A)
        zara__kmox = np.empty(n, A.dtype)
        wwk__xejlg = nmcta__jjy
        for i in range(n):
            wwk__xejlg = max(wwk__xejlg, A[i])
            zara__kmox[i] = wwk__xejlg
        return zara__kmox
    return impl


@overload(unique, no_unliteral=True)
def unique_overload(A, dropna=False, parallel=False):

    def unique_impl(A, dropna=False, parallel=False):
        rbt__ryyvf = arr_info_list_to_table([array_to_info(A)])
        cxl__vrjr = 1
        hst__rikl = 0
        rdo__iras = drop_duplicates_table(rbt__ryyvf, parallel, cxl__vrjr,
            hst__rikl, dropna, True)
        zara__kmox = info_to_array(info_from_table(rdo__iras, 0), A)
        delete_table(rbt__ryyvf)
        delete_table(rdo__iras)
        return zara__kmox
    return unique_impl


def explode(arr, index_arr):
    return pd.Series(arr, index_arr).explode()


@overload(explode, no_unliteral=True)
def overload_explode(arr, index_arr):
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type
    igjol__dyp = bodo.utils.typing.to_nullable_type(arr.dtype)
    ijw__txjto = index_arr
    dyzh__wwh = ijw__txjto.dtype

    def impl(arr, index_arr):
        n = len(arr)
        baxt__atpl = init_nested_counts(igjol__dyp)
        wgpx__blu = init_nested_counts(dyzh__wwh)
        for i in range(n):
            qzja__jyjo = index_arr[i]
            if isna(arr, i):
                baxt__atpl = (baxt__atpl[0] + 1,) + baxt__atpl[1:]
                wgpx__blu = add_nested_counts(wgpx__blu, qzja__jyjo)
                continue
            eyrhe__upfq = arr[i]
            if len(eyrhe__upfq) == 0:
                baxt__atpl = (baxt__atpl[0] + 1,) + baxt__atpl[1:]
                wgpx__blu = add_nested_counts(wgpx__blu, qzja__jyjo)
                continue
            baxt__atpl = add_nested_counts(baxt__atpl, eyrhe__upfq)
            for fbpoe__yex in range(len(eyrhe__upfq)):
                wgpx__blu = add_nested_counts(wgpx__blu, qzja__jyjo)
        zara__kmox = bodo.utils.utils.alloc_type(baxt__atpl[0], igjol__dyp,
            baxt__atpl[1:])
        rkyt__lnqng = bodo.utils.utils.alloc_type(baxt__atpl[0], ijw__txjto,
            wgpx__blu)
        icokn__dpjqu = 0
        for i in range(n):
            if isna(arr, i):
                setna(zara__kmox, icokn__dpjqu)
                rkyt__lnqng[icokn__dpjqu] = index_arr[i]
                icokn__dpjqu += 1
                continue
            eyrhe__upfq = arr[i]
            zuzjj__qgsf = len(eyrhe__upfq)
            if zuzjj__qgsf == 0:
                setna(zara__kmox, icokn__dpjqu)
                rkyt__lnqng[icokn__dpjqu] = index_arr[i]
                icokn__dpjqu += 1
                continue
            zara__kmox[icokn__dpjqu:icokn__dpjqu + zuzjj__qgsf] = eyrhe__upfq
            rkyt__lnqng[icokn__dpjqu:icokn__dpjqu + zuzjj__qgsf] = index_arr[i]
            icokn__dpjqu += zuzjj__qgsf
        return zara__kmox, rkyt__lnqng
    return impl


def explode_no_index(arr):
    return pd.Series(arr).explode()


@overload(explode_no_index, no_unliteral=True)
def overload_explode_no_index(arr, counts):
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type
    igjol__dyp = bodo.utils.typing.to_nullable_type(arr.dtype)

    def impl(arr, counts):
        n = len(arr)
        baxt__atpl = init_nested_counts(igjol__dyp)
        for i in range(n):
            if isna(arr, i):
                baxt__atpl = (baxt__atpl[0] + 1,) + baxt__atpl[1:]
                zff__gnw = 1
            else:
                eyrhe__upfq = arr[i]
                yeal__qwn = len(eyrhe__upfq)
                if yeal__qwn == 0:
                    baxt__atpl = (baxt__atpl[0] + 1,) + baxt__atpl[1:]
                    zff__gnw = 1
                    continue
                else:
                    baxt__atpl = add_nested_counts(baxt__atpl, eyrhe__upfq)
                    zff__gnw = yeal__qwn
            if counts[i] != zff__gnw:
                raise ValueError(
                    'DataFrame.explode(): columns must have matching element counts'
                    )
        zara__kmox = bodo.utils.utils.alloc_type(baxt__atpl[0], igjol__dyp,
            baxt__atpl[1:])
        icokn__dpjqu = 0
        for i in range(n):
            if isna(arr, i):
                setna(zara__kmox, icokn__dpjqu)
                icokn__dpjqu += 1
                continue
            eyrhe__upfq = arr[i]
            zuzjj__qgsf = len(eyrhe__upfq)
            if zuzjj__qgsf == 0:
                setna(zara__kmox, icokn__dpjqu)
                icokn__dpjqu += 1
                continue
            zara__kmox[icokn__dpjqu:icokn__dpjqu + zuzjj__qgsf] = eyrhe__upfq
            icokn__dpjqu += zuzjj__qgsf
        return zara__kmox
    return impl


def get_arr_lens(arr, na_empty_as_one=True):
    return [len(enne__ncqy) for enne__ncqy in arr]


@overload(get_arr_lens, inline='always', no_unliteral=True)
def overload_get_arr_lens(arr, na_empty_as_one=True):
    na_empty_as_one = get_overload_const_bool(na_empty_as_one)
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type or is_str_arr_type(arr
        ) and not na_empty_as_one, f'get_arr_lens: invalid input array type {arr}'
    if na_empty_as_one:
        jir__nbu = 'np.empty(n, np.int64)'
        cdir__srbu = 'out_arr[i] = 1'
        ezsp__opkwl = 'max(len(arr[i]), 1)'
    else:
        jir__nbu = 'bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)'
        cdir__srbu = 'bodo.libs.array_kernels.setna(out_arr, i)'
        ezsp__opkwl = 'len(arr[i])'
    vqpk__mkl = f"""def impl(arr, na_empty_as_one=True):
    numba.parfors.parfor.init_prange()
    n = len(arr)
    out_arr = {jir__nbu}
    for i in numba.parfors.parfor.internal_prange(n):
        if bodo.libs.array_kernels.isna(arr, i):
            {cdir__srbu}
        else:
            out_arr[i] = {ezsp__opkwl}
    return out_arr
    """
    qelqd__hiqb = {}
    exec(vqpk__mkl, {'bodo': bodo, 'numba': numba, 'np': np}, qelqd__hiqb)
    impl = qelqd__hiqb['impl']
    return impl


def explode_str_split(arr, pat, n, index_arr):
    return pd.Series(arr, index_arr).str.split(pat, n).explode()


@overload(explode_str_split, no_unliteral=True)
def overload_explode_str_split(arr, pat, n, index_arr):
    assert is_str_arr_type(arr
        ), f'explode_str_split: string array expected, not {arr}'
    ijw__txjto = index_arr
    dyzh__wwh = ijw__txjto.dtype

    def impl(arr, pat, n, index_arr):
        ioln__trath = pat is not None and len(pat) > 1
        if ioln__trath:
            egjhd__nhxh = re.compile(pat)
            if n == -1:
                n = 0
        elif n == 0:
            n = -1
        jopa__edacx = len(arr)
        orr__dkdnb = 0
        fzys__aktky = 0
        wgpx__blu = init_nested_counts(dyzh__wwh)
        for i in range(jopa__edacx):
            qzja__jyjo = index_arr[i]
            if bodo.libs.array_kernels.isna(arr, i):
                orr__dkdnb += 1
                wgpx__blu = add_nested_counts(wgpx__blu, qzja__jyjo)
                continue
            if ioln__trath:
                ggzo__jbgo = egjhd__nhxh.split(arr[i], maxsplit=n)
            else:
                ggzo__jbgo = arr[i].split(pat, n)
            orr__dkdnb += len(ggzo__jbgo)
            for s in ggzo__jbgo:
                wgpx__blu = add_nested_counts(wgpx__blu, qzja__jyjo)
                fzys__aktky += bodo.libs.str_arr_ext.get_utf8_size(s)
        zara__kmox = bodo.libs.str_arr_ext.pre_alloc_string_array(orr__dkdnb,
            fzys__aktky)
        rkyt__lnqng = bodo.utils.utils.alloc_type(orr__dkdnb, ijw__txjto,
            wgpx__blu)
        jqhzp__dyq = 0
        for ysavt__tlsct in range(jopa__edacx):
            if isna(arr, ysavt__tlsct):
                zara__kmox[jqhzp__dyq] = ''
                bodo.libs.array_kernels.setna(zara__kmox, jqhzp__dyq)
                rkyt__lnqng[jqhzp__dyq] = index_arr[ysavt__tlsct]
                jqhzp__dyq += 1
                continue
            if ioln__trath:
                ggzo__jbgo = egjhd__nhxh.split(arr[ysavt__tlsct], maxsplit=n)
            else:
                ggzo__jbgo = arr[ysavt__tlsct].split(pat, n)
            iuo__nwqwg = len(ggzo__jbgo)
            zara__kmox[jqhzp__dyq:jqhzp__dyq + iuo__nwqwg] = ggzo__jbgo
            rkyt__lnqng[jqhzp__dyq:jqhzp__dyq + iuo__nwqwg] = index_arr[
                ysavt__tlsct]
            jqhzp__dyq += iuo__nwqwg
        return zara__kmox, rkyt__lnqng
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
            zara__kmox = np.empty(n, dtype)
            for i in numba.parfors.parfor.internal_prange(n):
                zara__kmox[i] = np.nan
            return zara__kmox
        return impl_float
    uxka__laagm = to_str_arr_if_dict_array(arr)

    def impl(n, arr):
        numba.parfors.parfor.init_prange()
        zara__kmox = bodo.utils.utils.alloc_type(n, uxka__laagm, (0,))
        for i in numba.parfors.parfor.internal_prange(n):
            setna(zara__kmox, i)
        return zara__kmox
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
    wduci__ygmtc = A
    if A == types.Array(types.uint8, 1, 'C'):

        def impl_char(A, old_size, new_len):
            zara__kmox = bodo.utils.utils.alloc_type(new_len, wduci__ygmtc)
            bodo.libs.str_arr_ext.str_copy_ptr(zara__kmox.ctypes, 0, A.
                ctypes, old_size)
            return zara__kmox
        return impl_char

    def impl(A, old_size, new_len):
        zara__kmox = bodo.utils.utils.alloc_type(new_len, wduci__ygmtc, (-1,))
        zara__kmox[:old_size] = A[:old_size]
        return zara__kmox
    return impl


@register_jitable
def calc_nitems(start, stop, step):
    bfrl__psf = math.ceil((stop - start) / step)
    return int(max(bfrl__psf, 0))


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
    if any(isinstance(pgv__ipl, types.Complex) for pgv__ipl in args):

        def arange_4(start, stop, step, dtype):
            numba.parfors.parfor.init_prange()
            rwr__lyhbh = (stop - start) / step
            bfrl__psf = math.ceil(rwr__lyhbh.real)
            ahid__ppywe = math.ceil(rwr__lyhbh.imag)
            rfxe__olgg = int(max(min(ahid__ppywe, bfrl__psf), 0))
            arr = np.empty(rfxe__olgg, dtype)
            for i in numba.parfors.parfor.internal_prange(rfxe__olgg):
                arr[i] = start + i * step
            return arr
    else:

        def arange_4(start, stop, step, dtype):
            numba.parfors.parfor.init_prange()
            rfxe__olgg = bodo.libs.array_kernels.calc_nitems(start, stop, step)
            arr = np.empty(rfxe__olgg, dtype)
            for i in numba.parfors.parfor.internal_prange(rfxe__olgg):
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
        dyz__boi = arr,
        if not inplace:
            dyz__boi = arr.copy(),
        iypu__fbjv = bodo.libs.str_arr_ext.to_list_if_immutable_arr(dyz__boi)
        zxbt__ivzwi = bodo.libs.str_arr_ext.to_list_if_immutable_arr(data, True
            )
        bodo.libs.timsort.sort(iypu__fbjv, 0, n, zxbt__ivzwi)
        if not ascending:
            bodo.libs.timsort.reverseRange(iypu__fbjv, 0, n, zxbt__ivzwi)
        bodo.libs.str_arr_ext.cp_str_list_to_array(dyz__boi, iypu__fbjv)
        return dyz__boi[0]
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
        mxda__hnc = []
        for i in range(n):
            if A[i]:
                mxda__hnc.append(i + offset)
        return np.array(mxda__hnc, np.int64),
    return impl


def ffill_bfill_arr(arr):
    return arr


@overload(ffill_bfill_arr, no_unliteral=True)
def ffill_bfill_overload(A, method, parallel=False):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A,
        'bodo.ffill_bfill_arr()')
    wduci__ygmtc = element_type(A)
    if wduci__ygmtc == types.unicode_type:
        null_value = '""'
    elif wduci__ygmtc == types.bool_:
        null_value = 'False'
    elif wduci__ygmtc == bodo.datetime64ns:
        null_value = (
            'bodo.utils.conversion.unbox_if_timestamp(pd.to_datetime(0))')
    elif wduci__ygmtc == bodo.timedelta64ns:
        null_value = (
            'bodo.utils.conversion.unbox_if_timestamp(pd.to_timedelta(0))')
    else:
        null_value = '0'
    jqhzp__dyq = 'i'
    ray__tmv = False
    vmlim__dsrk = get_overload_const_str(method)
    if vmlim__dsrk in ('ffill', 'pad'):
        xzyj__fcz = 'n'
        send_right = True
    elif vmlim__dsrk in ('backfill', 'bfill'):
        xzyj__fcz = 'n-1, -1, -1'
        send_right = False
        if wduci__ygmtc == types.unicode_type:
            jqhzp__dyq = '(n - 1) - i'
            ray__tmv = True
    vqpk__mkl = 'def impl(A, method, parallel=False):\n'
    vqpk__mkl += '  A = decode_if_dict_array(A)\n'
    vqpk__mkl += '  has_last_value = False\n'
    vqpk__mkl += f'  last_value = {null_value}\n'
    vqpk__mkl += '  if parallel:\n'
    vqpk__mkl += '    rank = bodo.libs.distributed_api.get_rank()\n'
    vqpk__mkl += '    n_pes = bodo.libs.distributed_api.get_size()\n'
    vqpk__mkl += f"""    has_last_value, last_value = null_border_icomm(A, rank, n_pes, {null_value}, {send_right})
"""
    vqpk__mkl += '  n = len(A)\n'
    vqpk__mkl += '  out_arr = bodo.utils.utils.alloc_type(n, A, (-1,))\n'
    vqpk__mkl += f'  for i in range({xzyj__fcz}):\n'
    vqpk__mkl += (
        '    if (bodo.libs.array_kernels.isna(A, i) and not has_last_value):\n'
        )
    vqpk__mkl += (
        f'      bodo.libs.array_kernels.setna(out_arr, {jqhzp__dyq})\n')
    vqpk__mkl += '      continue\n'
    vqpk__mkl += '    s = A[i]\n'
    vqpk__mkl += '    if bodo.libs.array_kernels.isna(A, i):\n'
    vqpk__mkl += '      s = last_value\n'
    vqpk__mkl += f'    out_arr[{jqhzp__dyq}] = s\n'
    vqpk__mkl += '    last_value = s\n'
    vqpk__mkl += '    has_last_value = True\n'
    if ray__tmv:
        vqpk__mkl += '  return out_arr[::-1]\n'
    else:
        vqpk__mkl += '  return out_arr\n'
    xek__mwu = {}
    exec(vqpk__mkl, {'bodo': bodo, 'numba': numba, 'pd': pd,
        'null_border_icomm': null_border_icomm, 'decode_if_dict_array':
        decode_if_dict_array}, xek__mwu)
    impl = xek__mwu['impl']
    return impl


@register_jitable(cache=True)
def null_border_icomm(in_arr, rank, n_pes, null_value, send_right=True):
    if send_right:
        oglls__hjo = 0
        paxn__kvzyy = n_pes - 1
        wxcwd__tkobf = np.int32(rank + 1)
        ydyys__lohpg = np.int32(rank - 1)
        bvz__omu = len(in_arr) - 1
        bjs__ykzhd = -1
        wrswc__jozxg = -1
    else:
        oglls__hjo = n_pes - 1
        paxn__kvzyy = 0
        wxcwd__tkobf = np.int32(rank - 1)
        ydyys__lohpg = np.int32(rank + 1)
        bvz__omu = 0
        bjs__ykzhd = len(in_arr)
        wrswc__jozxg = 1
    opb__lsj = np.int32(bodo.hiframes.rolling.comm_border_tag)
    nae__wzoc = np.empty(1, dtype=np.bool_)
    lnr__kdel = bodo.utils.utils.alloc_type(1, in_arr, (-1,))
    gwuv__mql = np.empty(1, dtype=np.bool_)
    ahds__tmyur = bodo.utils.utils.alloc_type(1, in_arr, (-1,))
    pcjyv__fwnxv = False
    vco__aaiye = null_value
    for i in range(bvz__omu, bjs__ykzhd, wrswc__jozxg):
        if not isna(in_arr, i):
            pcjyv__fwnxv = True
            vco__aaiye = in_arr[i]
            break
    if rank != oglls__hjo:
        kngc__tybe = bodo.libs.distributed_api.irecv(nae__wzoc, 1,
            ydyys__lohpg, opb__lsj, True)
        bodo.libs.distributed_api.wait(kngc__tybe, True)
        euaeu__ykd = bodo.libs.distributed_api.irecv(lnr__kdel, 1,
            ydyys__lohpg, opb__lsj, True)
        bodo.libs.distributed_api.wait(euaeu__ykd, True)
        mfs__ifr = nae__wzoc[0]
        zuws__hdhc = lnr__kdel[0]
    else:
        mfs__ifr = False
        zuws__hdhc = null_value
    if pcjyv__fwnxv:
        gwuv__mql[0] = pcjyv__fwnxv
        ahds__tmyur[0] = vco__aaiye
    else:
        gwuv__mql[0] = mfs__ifr
        ahds__tmyur[0] = zuws__hdhc
    if rank != paxn__kvzyy:
        npoj__vftj = bodo.libs.distributed_api.isend(gwuv__mql, 1,
            wxcwd__tkobf, opb__lsj, True)
        uhps__jna = bodo.libs.distributed_api.isend(ahds__tmyur, 1,
            wxcwd__tkobf, opb__lsj, True)
    return mfs__ifr, zuws__hdhc


@overload(np.sort, inline='always', no_unliteral=True)
def np_sort(A, axis=-1, kind=None, order=None):
    if not bodo.utils.utils.is_array_typ(A, False) or isinstance(A, types.Array
        ):
        return
    yrj__xpoe = {'axis': axis, 'kind': kind, 'order': order}
    wtyq__qker = {'axis': -1, 'kind': None, 'order': None}
    check_unsupported_args('np.sort', yrj__xpoe, wtyq__qker, 'numpy')

    def impl(A, axis=-1, kind=None, order=None):
        return pd.Series(A).sort_values().values
    return impl


def repeat_kernel(A, repeats):
    return A


@overload(repeat_kernel, no_unliteral=True)
def repeat_kernel_overload(A, repeats):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A,
        'Series.repeat()')
    wduci__ygmtc = to_str_arr_if_dict_array(A)
    if isinstance(repeats, types.Integer):

        def impl_int(A, repeats):
            A = decode_if_dict_array(A)
            jopa__edacx = len(A)
            zara__kmox = bodo.utils.utils.alloc_type(jopa__edacx * repeats,
                wduci__ygmtc, (-1,))
            for i in range(jopa__edacx):
                jqhzp__dyq = i * repeats
                if bodo.libs.array_kernels.isna(A, i):
                    for ysavt__tlsct in range(repeats):
                        bodo.libs.array_kernels.setna(zara__kmox, 
                            jqhzp__dyq + ysavt__tlsct)
                else:
                    zara__kmox[jqhzp__dyq:jqhzp__dyq + repeats] = A[i]
            return zara__kmox
        return impl_int

    def impl_arr(A, repeats):
        A = decode_if_dict_array(A)
        jopa__edacx = len(A)
        zara__kmox = bodo.utils.utils.alloc_type(repeats.sum(),
            wduci__ygmtc, (-1,))
        jqhzp__dyq = 0
        for i in range(jopa__edacx):
            mtxyq__lax = repeats[i]
            if bodo.libs.array_kernels.isna(A, i):
                for ysavt__tlsct in range(mtxyq__lax):
                    bodo.libs.array_kernels.setna(zara__kmox, jqhzp__dyq +
                        ysavt__tlsct)
            else:
                zara__kmox[jqhzp__dyq:jqhzp__dyq + mtxyq__lax] = A[i]
            jqhzp__dyq += mtxyq__lax
        return zara__kmox
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
        lmq__foe = bodo.libs.array_kernels.unique(A)
        return bodo.allgatherv(lmq__foe, False)
    return impl


@overload(np.union1d, inline='always', no_unliteral=True)
def overload_union1d(A1, A2):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.union1d()')

    def impl(A1, A2):
        xewp__tvlp = bodo.libs.array_kernels.concat([A1, A2])
        zgik__kovyy = bodo.libs.array_kernels.unique(xewp__tvlp)
        return pd.Series(zgik__kovyy).sort_values().values
    return impl


@overload(np.intersect1d, inline='always', no_unliteral=True)
def overload_intersect1d(A1, A2, assume_unique=False, return_indices=False):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    yrj__xpoe = {'assume_unique': assume_unique, 'return_indices':
        return_indices}
    wtyq__qker = {'assume_unique': False, 'return_indices': False}
    check_unsupported_args('np.intersect1d', yrj__xpoe, wtyq__qker, 'numpy')
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.intersect1d()'
            )
    if A1.ndim != 1 or A2.ndim != 1:
        raise BodoError('Only 1D arrays supported in np.intersect1d()')

    def impl(A1, A2, assume_unique=False, return_indices=False):
        puy__qfldf = bodo.libs.array_kernels.unique(A1)
        jgw__arh = bodo.libs.array_kernels.unique(A2)
        xewp__tvlp = bodo.libs.array_kernels.concat([puy__qfldf, jgw__arh])
        bavxg__bcb = pd.Series(xewp__tvlp).sort_values().values
        return slice_array_intersect1d(bavxg__bcb)
    return impl


@register_jitable
def slice_array_intersect1d(arr):
    kxzsd__nzxro = arr[1:] == arr[:-1]
    return arr[:-1][kxzsd__nzxro]


@overload(np.setdiff1d, inline='always', no_unliteral=True)
def overload_setdiff1d(A1, A2, assume_unique=False):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    yrj__xpoe = {'assume_unique': assume_unique}
    wtyq__qker = {'assume_unique': False}
    check_unsupported_args('np.setdiff1d', yrj__xpoe, wtyq__qker, 'numpy')
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.setdiff1d()')
    if A1.ndim != 1 or A2.ndim != 1:
        raise BodoError('Only 1D arrays supported in np.setdiff1d()')

    def impl(A1, A2, assume_unique=False):
        puy__qfldf = bodo.libs.array_kernels.unique(A1)
        jgw__arh = bodo.libs.array_kernels.unique(A2)
        kxzsd__nzxro = calculate_mask_setdiff1d(puy__qfldf, jgw__arh)
        return pd.Series(puy__qfldf[kxzsd__nzxro]).sort_values().values
    return impl


@register_jitable
def calculate_mask_setdiff1d(A1, A2):
    kxzsd__nzxro = np.ones(len(A1), np.bool_)
    for i in range(len(A2)):
        kxzsd__nzxro &= A1 != A2[i]
    return kxzsd__nzxro


@overload(np.linspace, inline='always', no_unliteral=True)
def np_linspace(start, stop, num=50, endpoint=True, retstep=False, dtype=
    None, axis=0):
    yrj__xpoe = {'retstep': retstep, 'axis': axis}
    wtyq__qker = {'retstep': False, 'axis': 0}
    check_unsupported_args('np.linspace', yrj__xpoe, wtyq__qker, 'numpy')
    jpcw__jhakr = False
    if is_overload_none(dtype):
        wduci__ygmtc = np.promote_types(np.promote_types(numba.np.
            numpy_support.as_dtype(start), numba.np.numpy_support.as_dtype(
            stop)), numba.np.numpy_support.as_dtype(types.float64)).type
    else:
        if isinstance(dtype.dtype, types.Integer):
            jpcw__jhakr = True
        wduci__ygmtc = numba.np.numpy_support.as_dtype(dtype).type
    if jpcw__jhakr:

        def impl_int(start, stop, num=50, endpoint=True, retstep=False,
            dtype=None, axis=0):
            dfrit__xerim = np_linspace_get_stepsize(start, stop, num, endpoint)
            numba.parfors.parfor.init_prange()
            zara__kmox = np.empty(num, wduci__ygmtc)
            for i in numba.parfors.parfor.internal_prange(num):
                zara__kmox[i] = wduci__ygmtc(np.floor(start + i * dfrit__xerim)
                    )
            return zara__kmox
        return impl_int
    else:

        def impl(start, stop, num=50, endpoint=True, retstep=False, dtype=
            None, axis=0):
            dfrit__xerim = np_linspace_get_stepsize(start, stop, num, endpoint)
            numba.parfors.parfor.init_prange()
            zara__kmox = np.empty(num, wduci__ygmtc)
            for i in numba.parfors.parfor.internal_prange(num):
                zara__kmox[i] = wduci__ygmtc(start + i * dfrit__xerim)
            return zara__kmox
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
        tpeq__idcgf = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                tpeq__idcgf += A[i] == val
        return tpeq__idcgf > 0
    return impl


@overload(np.any, inline='always', no_unliteral=True)
def np_any(A, axis=None, out=None, keepdims=None):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A, 'np.any()')
    if not (bodo.utils.utils.is_array_typ(A, False) and A.ndim == 1):
        return
    yrj__xpoe = {'axis': axis, 'out': out, 'keepdims': keepdims}
    wtyq__qker = {'axis': None, 'out': None, 'keepdims': None}
    check_unsupported_args('np.any', yrj__xpoe, wtyq__qker, 'numpy')

    def impl(A, axis=None, out=None, keepdims=None):
        numba.parfors.parfor.init_prange()
        tpeq__idcgf = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                tpeq__idcgf += int(bool(A[i]))
        return tpeq__idcgf > 0
    return impl


@overload(np.all, inline='always', no_unliteral=True)
def np_all(A, axis=None, out=None, keepdims=None):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A, 'np.all()')
    if not (bodo.utils.utils.is_array_typ(A, False) and A.ndim == 1):
        return
    yrj__xpoe = {'axis': axis, 'out': out, 'keepdims': keepdims}
    wtyq__qker = {'axis': None, 'out': None, 'keepdims': None}
    check_unsupported_args('np.any', yrj__xpoe, wtyq__qker, 'numpy')

    def impl(A, axis=None, out=None, keepdims=None):
        numba.parfors.parfor.init_prange()
        tpeq__idcgf = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                tpeq__idcgf += int(bool(A[i]))
        return tpeq__idcgf == n
    return impl


@overload(np.cbrt, inline='always', no_unliteral=True)
def np_cbrt(A, out=None, where=True, casting='same_kind', order='K', dtype=
    None, subok=True):
    if not (isinstance(A, types.Number) or bodo.utils.utils.is_array_typ(A,
        False) and A.ndim == 1 and isinstance(A.dtype, types.Number)):
        return
    yrj__xpoe = {'out': out, 'where': where, 'casting': casting, 'order':
        order, 'dtype': dtype, 'subok': subok}
    wtyq__qker = {'out': None, 'where': True, 'casting': 'same_kind',
        'order': 'K', 'dtype': None, 'subok': True}
    check_unsupported_args('np.cbrt', yrj__xpoe, wtyq__qker, 'numpy')
    if bodo.utils.utils.is_array_typ(A, False):
        uwnz__jsc = np.promote_types(numba.np.numpy_support.as_dtype(A.
            dtype), numba.np.numpy_support.as_dtype(types.float32)).type

        def impl_arr(A, out=None, where=True, casting='same_kind', order=
            'K', dtype=None, subok=True):
            numba.parfors.parfor.init_prange()
            n = len(A)
            zara__kmox = np.empty(n, uwnz__jsc)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(A, i):
                    bodo.libs.array_kernels.setna(zara__kmox, i)
                    continue
                zara__kmox[i] = np_cbrt_scalar(A[i], uwnz__jsc)
            return zara__kmox
        return impl_arr
    uwnz__jsc = np.promote_types(numba.np.numpy_support.as_dtype(A), numba.
        np.numpy_support.as_dtype(types.float32)).type

    def impl_scalar(A, out=None, where=True, casting='same_kind', order='K',
        dtype=None, subok=True):
        return np_cbrt_scalar(A, uwnz__jsc)
    return impl_scalar


@register_jitable
def np_cbrt_scalar(x, float_dtype):
    if np.isnan(x):
        return np.nan
    idz__nfgmj = x < 0
    if idz__nfgmj:
        x = -x
    res = np.power(float_dtype(x), 1.0 / 3.0)
    if idz__nfgmj:
        return -res
    return res


@overload(np.hstack, no_unliteral=True)
def np_hstack(tup):
    qjv__najrg = isinstance(tup, (types.BaseTuple, types.List))
    ybrh__whqjy = isinstance(tup, (bodo.SeriesType, bodo.hiframes.
        pd_series_ext.HeterogeneousSeriesType)) and isinstance(tup.data, (
        types.BaseTuple, types.List, bodo.NullableTupleType))
    if isinstance(tup, types.BaseTuple):
        for wwnu__mstq in tup.types:
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(
                wwnu__mstq, 'numpy.hstack()')
            qjv__najrg = qjv__najrg and bodo.utils.utils.is_array_typ(
                wwnu__mstq, False)
    elif isinstance(tup, types.List):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(tup.dtype,
            'numpy.hstack()')
        qjv__najrg = bodo.utils.utils.is_array_typ(tup.dtype, False)
    elif ybrh__whqjy:
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(tup,
            'numpy.hstack()')
        dno__nwaa = tup.data.tuple_typ if isinstance(tup.data, bodo.
            NullableTupleType) else tup.data
        for wwnu__mstq in dno__nwaa.types:
            ybrh__whqjy = ybrh__whqjy and bodo.utils.utils.is_array_typ(
                wwnu__mstq, False)
    if not (qjv__najrg or ybrh__whqjy):
        return
    if ybrh__whqjy:

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
    yrj__xpoe = {'check_valid': check_valid, 'tol': tol}
    wtyq__qker = {'check_valid': 'warn', 'tol': 1e-08}
    check_unsupported_args('np.random.multivariate_normal', yrj__xpoe,
        wtyq__qker, 'numpy')
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
        ymt__axle = mean.shape[0]
        odmc__lgnf = size, ymt__axle
        nwn__ssqxr = np.random.standard_normal(odmc__lgnf)
        cov = cov.astype(np.float64)
        ojiph__ooxw, s, qkby__hzo = np.linalg.svd(cov)
        res = np.dot(nwn__ssqxr, np.sqrt(s).reshape(ymt__axle, 1) * qkby__hzo)
        aiym__sql = res + mean
        return aiym__sql
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
            ypvrh__gmbv = bodo.hiframes.series_kernels._get_type_max_value(arr)
            yffr__icph = typing.builtins.IndexValue(-1, ypvrh__gmbv)
            for i in numba.parfors.parfor.internal_prange(len(arr)):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                igovr__jfmr = typing.builtins.IndexValue(i, arr[i])
                yffr__icph = min(yffr__icph, igovr__jfmr)
            return yffr__icph.index
        return impl_bodo_arr
    if isinstance(arr, CategoricalArrayType):
        assert arr.dtype.ordered, 'Categorical Array must be ordered to select an argmin'
        bfsgt__qkiqw = (bodo.hiframes.pd_categorical_ext.
            get_categories_int_type(arr.dtype))

        def impl_cat_arr(arr):
            rpx__tockm = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            ypvrh__gmbv = bfsgt__qkiqw(len(arr.dtype.categories) + 1)
            yffr__icph = typing.builtins.IndexValue(-1, ypvrh__gmbv)
            for i in numba.parfors.parfor.internal_prange(len(arr)):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                igovr__jfmr = typing.builtins.IndexValue(i, rpx__tockm[i])
                yffr__icph = min(yffr__icph, igovr__jfmr)
            return yffr__icph.index
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
            ypvrh__gmbv = bodo.hiframes.series_kernels._get_type_min_value(arr)
            yffr__icph = typing.builtins.IndexValue(-1, ypvrh__gmbv)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                igovr__jfmr = typing.builtins.IndexValue(i, arr[i])
                yffr__icph = max(yffr__icph, igovr__jfmr)
            return yffr__icph.index
        return impl_bodo_arr
    if isinstance(arr, CategoricalArrayType):
        assert arr.dtype.ordered, 'Categorical Array must be ordered to select an argmin'
        bfsgt__qkiqw = (bodo.hiframes.pd_categorical_ext.
            get_categories_int_type(arr.dtype))

        def impl_cat_arr(arr):
            n = len(arr)
            rpx__tockm = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            ypvrh__gmbv = bfsgt__qkiqw(-1)
            yffr__icph = typing.builtins.IndexValue(-1, ypvrh__gmbv)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                igovr__jfmr = typing.builtins.IndexValue(i, rpx__tockm[i])
                yffr__icph = max(yffr__icph, igovr__jfmr)
            return yffr__icph.index
        return impl_cat_arr
    return lambda arr: arr.argmax()


@overload_attribute(types.Array, 'nbytes', inline='always')
def overload_dataframe_index(A):
    return lambda A: A.size * bodo.io.np_io.get_dtype_size(A.dtype)
