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
        curuk__rgbr = arr.dtype('NaT')

        def _setnan_impl(arr, ind, int_nan_const=0):
            arr[ind] = curuk__rgbr
        return _setnan_impl
    if isinstance(arr, DatetimeArrayType):
        curuk__rgbr = bodo.datetime64ns('NaT')

        def _setnan_impl(arr, ind, int_nan_const=0):
            arr._data[ind] = curuk__rgbr
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
            eyiz__jqi = bodo.libs.array_item_arr_ext.get_offsets(arr._data)
            eyiz__jqi[ind + 1] = eyiz__jqi[ind]
            bodo.libs.int_arr_ext.set_bit_to_arr(bodo.libs.
                array_item_arr_ext.get_null_bitmap(arr._data), ind, 0)
        return impl_binary_arr
    if isinstance(arr, bodo.libs.array_item_arr_ext.ArrayItemArrayType):

        def impl_arr_item(arr, ind, int_nan_const=0):
            eyiz__jqi = bodo.libs.array_item_arr_ext.get_offsets(arr)
            eyiz__jqi[ind + 1] = eyiz__jqi[ind]
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
    fduv__iiueh = arr_tup.count
    swwag__fubr = 'def f(arr_tup, ind, int_nan_const=0):\n'
    for i in range(fduv__iiueh):
        swwag__fubr += '  setna(arr_tup[{}], ind, int_nan_const)\n'.format(i)
    swwag__fubr += '  return\n'
    glxrg__qmx = {}
    exec(swwag__fubr, {'setna': setna}, glxrg__qmx)
    impl = glxrg__qmx['f']
    return impl


def setna_slice(arr, s):
    arr[s] = np.nan


@overload(setna_slice, no_unliteral=True)
def overload_setna_slice(arr, s):

    def impl(arr, s):
        smj__wdx = numba.cpython.unicode._normalize_slice(s, len(arr))
        for i in range(smj__wdx.start, smj__wdx.stop, smj__wdx.step):
            setna(arr, i)
    return impl


@numba.generated_jit
def first_last_valid_index(arr, index_arr, is_first=True, parallel=False):
    is_first = get_overload_const_bool(is_first)
    if is_first:
        omi__dtj = 'n'
    else:
        omi__dtj = 'n-1, -1, -1'
    swwag__fubr = f"""def impl(arr, index_arr, is_first=True, parallel=False):
    n = len(arr)
    index_val = index_arr[0]
    has_valid = False
    loc_min = -1
    if parallel:
        rank = bodo.libs.distributed_api.get_rank()
        n_pes = bodo.libs.distributed_api.get_size()
        loc_min = n_pes
    for i in range({omi__dtj}):
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
    glxrg__qmx = {}
    exec(swwag__fubr, {'np': np, 'bodo': bodo, 'isna': isna, 'min_op':
        min_op, 'box_if_dt64': bodo.utils.conversion.box_if_dt64}, glxrg__qmx)
    impl = glxrg__qmx['impl']
    return impl


ll.add_symbol('median_series_computation', quantile_alg.
    median_series_computation)
_median_series_computation = types.ExternalFunction('median_series_computation'
    , types.void(types.voidptr, bodo.libs.array.array_info_type, types.
    bool_, types.bool_))


@numba.njit
def median_series_computation(res, arr, is_parallel, skipna):
    obe__kmnm = array_to_info(arr)
    _median_series_computation(res, obe__kmnm, is_parallel, skipna)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(obe__kmnm)


ll.add_symbol('autocorr_series_computation', quantile_alg.
    autocorr_series_computation)
_autocorr_series_computation = types.ExternalFunction(
    'autocorr_series_computation', types.void(types.voidptr, bodo.libs.
    array.array_info_type, types.int64, types.bool_))


@numba.njit
def autocorr_series_computation(res, arr, lag, is_parallel):
    obe__kmnm = array_to_info(arr)
    _autocorr_series_computation(res, obe__kmnm, lag, is_parallel)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(obe__kmnm)


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
    obe__kmnm = array_to_info(arr)
    _compute_series_monotonicity(res, obe__kmnm, inc_dec, is_parallel)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(obe__kmnm)


@numba.njit
def series_monotonicity(arr, inc_dec, parallel=False):
    res = np.empty(1, types.float64)
    series_monotonicity_call(res.ctypes, arr, inc_dec, parallel)
    uzxys__lejtx = res[0] > 0.5
    return uzxys__lejtx


@numba.generated_jit(nopython=True)
def get_valid_entries_from_date_offset(index_arr, offset, initial_date,
    is_last, is_parallel=False):
    if get_overload_const_bool(is_last):
        ipkq__pcr = '-'
        kuud__ircb = 'index_arr[0] > threshhold_date'
        omi__dtj = '1, n+1'
        tdg__tqe = 'index_arr[-i] <= threshhold_date'
        nvfv__ewty = 'i - 1'
    else:
        ipkq__pcr = '+'
        kuud__ircb = 'index_arr[-1] < threshhold_date'
        omi__dtj = 'n'
        tdg__tqe = 'index_arr[i] >= threshhold_date'
        nvfv__ewty = 'i'
    swwag__fubr = (
        'def impl(index_arr, offset, initial_date, is_last, is_parallel=False):\n'
        )
    if types.unliteral(offset) == types.unicode_type:
        swwag__fubr += (
            '  with numba.objmode(threshhold_date=bodo.pd_timestamp_type):\n')
        swwag__fubr += (
            '    date_offset = pd.tseries.frequencies.to_offset(offset)\n')
        if not get_overload_const_bool(is_last):
            swwag__fubr += """    if not isinstance(date_offset, pd._libs.tslibs.Tick) and date_offset.is_on_offset(index_arr[0]):
"""
            swwag__fubr += """      threshhold_date = initial_date - date_offset.base + date_offset
"""
            swwag__fubr += '    else:\n'
            swwag__fubr += (
                '      threshhold_date = initial_date + date_offset\n')
        else:
            swwag__fubr += (
                f'    threshhold_date = initial_date {ipkq__pcr} date_offset\n'
                )
    else:
        swwag__fubr += f'  threshhold_date = initial_date {ipkq__pcr} offset\n'
    swwag__fubr += '  local_valid = 0\n'
    swwag__fubr += f'  n = len(index_arr)\n'
    swwag__fubr += f'  if n:\n'
    swwag__fubr += f'    if {kuud__ircb}:\n'
    swwag__fubr += '      loc_valid = n\n'
    swwag__fubr += '    else:\n'
    swwag__fubr += f'      for i in range({omi__dtj}):\n'
    swwag__fubr += f'        if {tdg__tqe}:\n'
    swwag__fubr += f'          loc_valid = {nvfv__ewty}\n'
    swwag__fubr += '          break\n'
    swwag__fubr += '  if is_parallel:\n'
    swwag__fubr += (
        '    total_valid = bodo.libs.distributed_api.dist_reduce(loc_valid, sum_op)\n'
        )
    swwag__fubr += '    return total_valid\n'
    swwag__fubr += '  else:\n'
    swwag__fubr += '    return loc_valid\n'
    glxrg__qmx = {}
    exec(swwag__fubr, {'bodo': bodo, 'pd': pd, 'numba': numba, 'sum_op':
        sum_op}, glxrg__qmx)
    return glxrg__qmx['impl']


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
    kxku__ber = numba_to_c_type(sig.args[0].dtype)
    oeapq__jsecu = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(32), kxku__ber))
    zjyf__mgv = args[0]
    hcbj__qdk = sig.args[0]
    if isinstance(hcbj__qdk, (IntegerArrayType, BooleanArrayType)):
        zjyf__mgv = cgutils.create_struct_proxy(hcbj__qdk)(context, builder,
            zjyf__mgv).data
        hcbj__qdk = types.Array(hcbj__qdk.dtype, 1, 'C')
    assert hcbj__qdk.ndim == 1
    arr = make_array(hcbj__qdk)(context, builder, zjyf__mgv)
    yeff__prbz = builder.extract_value(arr.shape, 0)
    acjx__ngjae = [builder.bitcast(arr.data, lir.IntType(8).as_pointer()),
        yeff__prbz, args[1], builder.load(oeapq__jsecu)]
    avczy__hol = [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
        DoubleType(), lir.IntType(32)]
    gvk__gikg = lir.FunctionType(lir.DoubleType(), avczy__hol)
    kazlx__luvxc = cgutils.get_or_insert_function(builder.module, gvk__gikg,
        name='quantile_sequential')
    wnn__ekoft = builder.call(kazlx__luvxc, acjx__ngjae)
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return wnn__ekoft


@lower_builtin(quantile_parallel, types.Array, types.float64, types.intp)
@lower_builtin(quantile_parallel, IntegerArrayType, types.float64, types.intp)
@lower_builtin(quantile_parallel, BooleanArrayType, types.float64, types.intp)
def lower_dist_quantile_parallel(context, builder, sig, args):
    kxku__ber = numba_to_c_type(sig.args[0].dtype)
    oeapq__jsecu = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(32), kxku__ber))
    zjyf__mgv = args[0]
    hcbj__qdk = sig.args[0]
    if isinstance(hcbj__qdk, (IntegerArrayType, BooleanArrayType)):
        zjyf__mgv = cgutils.create_struct_proxy(hcbj__qdk)(context, builder,
            zjyf__mgv).data
        hcbj__qdk = types.Array(hcbj__qdk.dtype, 1, 'C')
    assert hcbj__qdk.ndim == 1
    arr = make_array(hcbj__qdk)(context, builder, zjyf__mgv)
    yeff__prbz = builder.extract_value(arr.shape, 0)
    if len(args) == 3:
        qgpom__ptfjy = args[2]
    else:
        qgpom__ptfjy = yeff__prbz
    acjx__ngjae = [builder.bitcast(arr.data, lir.IntType(8).as_pointer()),
        yeff__prbz, qgpom__ptfjy, args[1], builder.load(oeapq__jsecu)]
    avczy__hol = [lir.IntType(8).as_pointer(), lir.IntType(64), lir.IntType
        (64), lir.DoubleType(), lir.IntType(32)]
    gvk__gikg = lir.FunctionType(lir.DoubleType(), avczy__hol)
    kazlx__luvxc = cgutils.get_or_insert_function(builder.module, gvk__gikg,
        name='quantile_parallel')
    wnn__ekoft = builder.call(kazlx__luvxc, acjx__ngjae)
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return wnn__ekoft


@numba.njit
def min_heapify(arr, ind_arr, n, start, cmp_f):
    mvx__wvlfu = start
    nectf__spu = 2 * start + 1
    fbin__hlmgj = 2 * start + 2
    if nectf__spu < n and not cmp_f(arr[nectf__spu], arr[mvx__wvlfu]):
        mvx__wvlfu = nectf__spu
    if fbin__hlmgj < n and not cmp_f(arr[fbin__hlmgj], arr[mvx__wvlfu]):
        mvx__wvlfu = fbin__hlmgj
    if mvx__wvlfu != start:
        arr[start], arr[mvx__wvlfu] = arr[mvx__wvlfu], arr[start]
        ind_arr[start], ind_arr[mvx__wvlfu] = ind_arr[mvx__wvlfu], ind_arr[
            start]
        min_heapify(arr, ind_arr, n, mvx__wvlfu, cmp_f)


def select_k_nonan(A, index_arr, m, k):
    return A[:k]


@overload(select_k_nonan, no_unliteral=True)
def select_k_nonan_overload(A, index_arr, m, k):
    dtype = A.dtype
    if isinstance(dtype, types.Integer):
        return lambda A, index_arr, m, k: (A[:k].copy(), index_arr[:k].copy
            (), k)

    def select_k_nonan_float(A, index_arr, m, k):
        eyiv__pqs = np.empty(k, A.dtype)
        zkb__fwg = np.empty(k, index_arr.dtype)
        i = 0
        ind = 0
        while i < m and ind < k:
            if not bodo.libs.array_kernels.isna(A, i):
                eyiv__pqs[ind] = A[i]
                zkb__fwg[ind] = index_arr[i]
                ind += 1
            i += 1
        if ind < k:
            eyiv__pqs = eyiv__pqs[:ind]
            zkb__fwg = zkb__fwg[:ind]
        return eyiv__pqs, zkb__fwg, i
    return select_k_nonan_float


@numba.njit
def nlargest(A, index_arr, k, is_largest, cmp_f):
    m = len(A)
    if k == 0:
        return A[:0], index_arr[:0]
    if k >= m:
        shyf__dlgz = np.sort(A)
        rphqp__ipd = index_arr[np.argsort(A)]
        skt__paj = pd.Series(shyf__dlgz).notna().values
        shyf__dlgz = shyf__dlgz[skt__paj]
        rphqp__ipd = rphqp__ipd[skt__paj]
        if is_largest:
            shyf__dlgz = shyf__dlgz[::-1]
            rphqp__ipd = rphqp__ipd[::-1]
        return np.ascontiguousarray(shyf__dlgz), np.ascontiguousarray(
            rphqp__ipd)
    eyiv__pqs, zkb__fwg, start = select_k_nonan(A, index_arr, m, k)
    zkb__fwg = zkb__fwg[eyiv__pqs.argsort()]
    eyiv__pqs.sort()
    if not is_largest:
        eyiv__pqs = np.ascontiguousarray(eyiv__pqs[::-1])
        zkb__fwg = np.ascontiguousarray(zkb__fwg[::-1])
    for i in range(start, m):
        if cmp_f(A[i], eyiv__pqs[0]):
            eyiv__pqs[0] = A[i]
            zkb__fwg[0] = index_arr[i]
            min_heapify(eyiv__pqs, zkb__fwg, k, 0, cmp_f)
    zkb__fwg = zkb__fwg[eyiv__pqs.argsort()]
    eyiv__pqs.sort()
    if is_largest:
        eyiv__pqs = eyiv__pqs[::-1]
        zkb__fwg = zkb__fwg[::-1]
    return np.ascontiguousarray(eyiv__pqs), np.ascontiguousarray(zkb__fwg)


@numba.njit
def nlargest_parallel(A, I, k, is_largest, cmp_f):
    epwda__mckr = bodo.libs.distributed_api.get_rank()
    qib__rax, rxzar__togat = nlargest(A, I, k, is_largest, cmp_f)
    djzl__xrhy = bodo.libs.distributed_api.gatherv(qib__rax)
    xpj__aucxz = bodo.libs.distributed_api.gatherv(rxzar__togat)
    if epwda__mckr == MPI_ROOT:
        res, fhxj__kxh = nlargest(djzl__xrhy, xpj__aucxz, k, is_largest, cmp_f)
    else:
        res = np.empty(k, A.dtype)
        fhxj__kxh = np.empty(k, I.dtype)
    bodo.libs.distributed_api.bcast(res)
    bodo.libs.distributed_api.bcast(fhxj__kxh)
    return res, fhxj__kxh


@numba.njit(no_cpython_wrapper=True, cache=True)
def nancorr(mat, cov=0, minpv=1, parallel=False):
    cyhgi__sjgz, xity__hvb = mat.shape
    lmt__lzcxz = np.empty((xity__hvb, xity__hvb), dtype=np.float64)
    for hds__wlko in range(xity__hvb):
        for jevec__pcine in range(hds__wlko + 1):
            kzmx__yfwdb = 0
            odrww__uwope = aqa__mbqb = kaajt__aazcj = pnhz__dxn = 0.0
            for i in range(cyhgi__sjgz):
                if np.isfinite(mat[i, hds__wlko]) and np.isfinite(mat[i,
                    jevec__pcine]):
                    onzp__tibr = mat[i, hds__wlko]
                    mgh__tob = mat[i, jevec__pcine]
                    kzmx__yfwdb += 1
                    kaajt__aazcj += onzp__tibr
                    pnhz__dxn += mgh__tob
            if parallel:
                kzmx__yfwdb = bodo.libs.distributed_api.dist_reduce(kzmx__yfwdb
                    , sum_op)
                kaajt__aazcj = bodo.libs.distributed_api.dist_reduce(
                    kaajt__aazcj, sum_op)
                pnhz__dxn = bodo.libs.distributed_api.dist_reduce(pnhz__dxn,
                    sum_op)
            if kzmx__yfwdb < minpv:
                lmt__lzcxz[hds__wlko, jevec__pcine] = lmt__lzcxz[
                    jevec__pcine, hds__wlko] = np.nan
            else:
                gnnd__zxck = kaajt__aazcj / kzmx__yfwdb
                hapaf__cyr = pnhz__dxn / kzmx__yfwdb
                kaajt__aazcj = 0.0
                for i in range(cyhgi__sjgz):
                    if np.isfinite(mat[i, hds__wlko]) and np.isfinite(mat[i,
                        jevec__pcine]):
                        onzp__tibr = mat[i, hds__wlko] - gnnd__zxck
                        mgh__tob = mat[i, jevec__pcine] - hapaf__cyr
                        kaajt__aazcj += onzp__tibr * mgh__tob
                        odrww__uwope += onzp__tibr * onzp__tibr
                        aqa__mbqb += mgh__tob * mgh__tob
                if parallel:
                    kaajt__aazcj = bodo.libs.distributed_api.dist_reduce(
                        kaajt__aazcj, sum_op)
                    odrww__uwope = bodo.libs.distributed_api.dist_reduce(
                        odrww__uwope, sum_op)
                    aqa__mbqb = bodo.libs.distributed_api.dist_reduce(aqa__mbqb
                        , sum_op)
                mekb__anc = kzmx__yfwdb - 1.0 if cov else sqrt(odrww__uwope *
                    aqa__mbqb)
                if mekb__anc != 0.0:
                    lmt__lzcxz[hds__wlko, jevec__pcine] = lmt__lzcxz[
                        jevec__pcine, hds__wlko] = kaajt__aazcj / mekb__anc
                else:
                    lmt__lzcxz[hds__wlko, jevec__pcine] = lmt__lzcxz[
                        jevec__pcine, hds__wlko] = np.nan
    return lmt__lzcxz


@numba.generated_jit(nopython=True)
def duplicated(data, parallel=False):
    n = len(data)
    if n == 0:
        return lambda data, parallel=False: np.empty(0, dtype=np.bool_)
    fmisu__oqlph = n != 1
    swwag__fubr = 'def impl(data, parallel=False):\n'
    swwag__fubr += '  if parallel:\n'
    fykdl__scvka = ', '.join(f'array_to_info(data[{i}])' for i in range(n))
    swwag__fubr += (
        f'    cpp_table = arr_info_list_to_table([{fykdl__scvka}])\n')
    swwag__fubr += f"""    out_cpp_table = bodo.libs.array.shuffle_table(cpp_table, {n}, parallel, 1)
"""
    bll__kprn = ', '.join(
        f'info_to_array(info_from_table(out_cpp_table, {i}), data[{i}])' for
        i in range(n))
    swwag__fubr += f'    data = ({bll__kprn},)\n'
    swwag__fubr += (
        '    shuffle_info = bodo.libs.array.get_shuffle_info(out_cpp_table)\n')
    swwag__fubr += '    bodo.libs.array.delete_table(out_cpp_table)\n'
    swwag__fubr += '    bodo.libs.array.delete_table(cpp_table)\n'
    swwag__fubr += '  n = len(data[0])\n'
    swwag__fubr += '  out = np.empty(n, np.bool_)\n'
    swwag__fubr += '  uniqs = dict()\n'
    if fmisu__oqlph:
        swwag__fubr += '  for i in range(n):\n'
        tqt__zsbr = ', '.join(f'data[{i}][i]' for i in range(n))
        vkkqc__qee = ',  '.join(
            f'bodo.libs.array_kernels.isna(data[{i}], i)' for i in range(n))
        swwag__fubr += f"""    val = bodo.libs.nullable_tuple_ext.build_nullable_tuple(({tqt__zsbr},), ({vkkqc__qee},))
"""
        swwag__fubr += '    if val in uniqs:\n'
        swwag__fubr += '      out[i] = True\n'
        swwag__fubr += '    else:\n'
        swwag__fubr += '      out[i] = False\n'
        swwag__fubr += '      uniqs[val] = 0\n'
    else:
        swwag__fubr += '  data = data[0]\n'
        swwag__fubr += '  hasna = False\n'
        swwag__fubr += '  for i in range(n):\n'
        swwag__fubr += '    if bodo.libs.array_kernels.isna(data, i):\n'
        swwag__fubr += '      out[i] = hasna\n'
        swwag__fubr += '      hasna = True\n'
        swwag__fubr += '    else:\n'
        swwag__fubr += '      val = data[i]\n'
        swwag__fubr += '      if val in uniqs:\n'
        swwag__fubr += '        out[i] = True\n'
        swwag__fubr += '      else:\n'
        swwag__fubr += '        out[i] = False\n'
        swwag__fubr += '        uniqs[val] = 0\n'
    swwag__fubr += '  if parallel:\n'
    swwag__fubr += (
        '    out = bodo.hiframes.pd_groupby_ext.reverse_shuffle(out, shuffle_info)\n'
        )
    swwag__fubr += '  return out\n'
    glxrg__qmx = {}
    exec(swwag__fubr, {'bodo': bodo, 'np': np, 'array_to_info':
        array_to_info, 'arr_info_list_to_table': arr_info_list_to_table,
        'info_to_array': info_to_array, 'info_from_table': info_from_table},
        glxrg__qmx)
    impl = glxrg__qmx['impl']
    return impl


def sample_table_operation(data, ind_arr, n, frac, replace, parallel=False):
    return data, ind_arr


@overload(sample_table_operation, no_unliteral=True)
def overload_sample_table_operation(data, ind_arr, n, frac, replace,
    parallel=False):
    fduv__iiueh = len(data)
    swwag__fubr = (
        'def impl(data, ind_arr, n, frac, replace, parallel=False):\n')
    swwag__fubr += '  info_list_total = [{}, array_to_info(ind_arr)]\n'.format(
        ', '.join('array_to_info(data[{}])'.format(x) for x in range(
        fduv__iiueh)))
    swwag__fubr += '  table_total = arr_info_list_to_table(info_list_total)\n'
    swwag__fubr += (
        '  out_table = sample_table(table_total, n, frac, replace, parallel)\n'
        .format(fduv__iiueh))
    for isxw__chht in range(fduv__iiueh):
        swwag__fubr += (
            '  out_arr_{} = info_to_array(info_from_table(out_table, {}), data[{}])\n'
            .format(isxw__chht, isxw__chht, isxw__chht))
    swwag__fubr += (
        '  out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)\n'
        .format(fduv__iiueh))
    swwag__fubr += '  delete_table(out_table)\n'
    swwag__fubr += '  delete_table(table_total)\n'
    swwag__fubr += '  return ({},), out_arr_index\n'.format(', '.join(
        'out_arr_{}'.format(i) for i in range(fduv__iiueh)))
    glxrg__qmx = {}
    exec(swwag__fubr, {'np': np, 'bodo': bodo, 'array_to_info':
        array_to_info, 'sample_table': sample_table,
        'arr_info_list_to_table': arr_info_list_to_table, 'info_from_table':
        info_from_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays}, glxrg__qmx)
    impl = glxrg__qmx['impl']
    return impl


def drop_duplicates(data, ind_arr, ncols, parallel=False):
    return data, ind_arr


@overload(drop_duplicates, no_unliteral=True)
def overload_drop_duplicates(data, ind_arr, ncols, parallel=False):
    fduv__iiueh = len(data)
    swwag__fubr = 'def impl(data, ind_arr, ncols, parallel=False):\n'
    swwag__fubr += '  info_list_total = [{}, array_to_info(ind_arr)]\n'.format(
        ', '.join('array_to_info(data[{}])'.format(x) for x in range(
        fduv__iiueh)))
    swwag__fubr += '  table_total = arr_info_list_to_table(info_list_total)\n'
    swwag__fubr += '  keep_i = 0\n'
    swwag__fubr += """  out_table = drop_duplicates_table(table_total, parallel, ncols, keep_i, False, True)
"""
    for isxw__chht in range(fduv__iiueh):
        swwag__fubr += (
            '  out_arr_{} = info_to_array(info_from_table(out_table, {}), data[{}])\n'
            .format(isxw__chht, isxw__chht, isxw__chht))
    swwag__fubr += (
        '  out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)\n'
        .format(fduv__iiueh))
    swwag__fubr += '  delete_table(out_table)\n'
    swwag__fubr += '  delete_table(table_total)\n'
    swwag__fubr += '  return ({},), out_arr_index\n'.format(', '.join(
        'out_arr_{}'.format(i) for i in range(fduv__iiueh)))
    glxrg__qmx = {}
    exec(swwag__fubr, {'np': np, 'bodo': bodo, 'array_to_info':
        array_to_info, 'drop_duplicates_table': drop_duplicates_table,
        'arr_info_list_to_table': arr_info_list_to_table, 'info_from_table':
        info_from_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays}, glxrg__qmx)
    impl = glxrg__qmx['impl']
    return impl


def drop_duplicates_array(data_arr, parallel=False):
    return data_arr


@overload(drop_duplicates_array, no_unliteral=True)
def overload_drop_duplicates_array(data_arr, parallel=False):

    def impl(data_arr, parallel=False):
        rbes__cym = [array_to_info(data_arr)]
        lxjf__lulo = arr_info_list_to_table(rbes__cym)
        wfd__zbxl = 0
        bjpd__fdmck = drop_duplicates_table(lxjf__lulo, parallel, 1,
            wfd__zbxl, False, True)
        voaon__tst = info_to_array(info_from_table(bjpd__fdmck, 0), data_arr)
        delete_table(bjpd__fdmck)
        delete_table(lxjf__lulo)
        return voaon__tst
    return impl


def dropna(data, how, thresh, subset, parallel=False):
    return data


@overload(dropna, no_unliteral=True)
def overload_dropna(data, how, thresh, subset):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
        'bodo.dropna()')
    eove__heyc = len(data.types)
    ldxj__qls = [('out' + str(i)) for i in range(eove__heyc)]
    alk__ddl = get_overload_const_list(subset)
    how = get_overload_const_str(how)
    xjhdl__iromj = ['isna(data[{}], i)'.format(i) for i in alk__ddl]
    lkixa__fry = 'not ({})'.format(' or '.join(xjhdl__iromj))
    if not is_overload_none(thresh):
        lkixa__fry = '(({}) <= ({}) - thresh)'.format(' + '.join(
            xjhdl__iromj), eove__heyc - 1)
    elif how == 'all':
        lkixa__fry = 'not ({})'.format(' and '.join(xjhdl__iromj))
    swwag__fubr = 'def _dropna_imp(data, how, thresh, subset):\n'
    swwag__fubr += '  old_len = len(data[0])\n'
    swwag__fubr += '  new_len = 0\n'
    swwag__fubr += '  for i in range(old_len):\n'
    swwag__fubr += '    if {}:\n'.format(lkixa__fry)
    swwag__fubr += '      new_len += 1\n'
    for i, out in enumerate(ldxj__qls):
        if isinstance(data[i], bodo.CategoricalArrayType):
            swwag__fubr += (
                '  {0} = bodo.utils.utils.alloc_type(new_len, data[{1}], (-1,))\n'
                .format(out, i))
        else:
            swwag__fubr += (
                '  {0} = bodo.utils.utils.alloc_type(new_len, t{1}, (-1,))\n'
                .format(out, i))
    swwag__fubr += '  curr_ind = 0\n'
    swwag__fubr += '  for i in range(old_len):\n'
    swwag__fubr += '    if {}:\n'.format(lkixa__fry)
    for i in range(eove__heyc):
        swwag__fubr += '      if isna(data[{}], i):\n'.format(i)
        swwag__fubr += '        setna({}, curr_ind)\n'.format(ldxj__qls[i])
        swwag__fubr += '      else:\n'
        swwag__fubr += '        {}[curr_ind] = data[{}][i]\n'.format(ldxj__qls
            [i], i)
    swwag__fubr += '      curr_ind += 1\n'
    swwag__fubr += '  return {}\n'.format(', '.join(ldxj__qls))
    glxrg__qmx = {}
    xtv__mfpo = {'t{}'.format(i): irjx__thaos for i, irjx__thaos in
        enumerate(data.types)}
    xtv__mfpo.update({'isna': isna, 'setna': setna, 'init_nested_counts':
        bodo.utils.indexing.init_nested_counts, 'add_nested_counts': bodo.
        utils.indexing.add_nested_counts, 'bodo': bodo})
    exec(swwag__fubr, xtv__mfpo, glxrg__qmx)
    myqyd__kgl = glxrg__qmx['_dropna_imp']
    return myqyd__kgl


def get(arr, ind):
    return pd.Series(arr).str.get(ind)


@overload(get, no_unliteral=True)
def overload_get(arr, ind):
    if isinstance(arr, ArrayItemArrayType):
        hcbj__qdk = arr.dtype
        col__ktxd = hcbj__qdk.dtype

        def get_arr_item(arr, ind):
            n = len(arr)
            bvs__guhfi = init_nested_counts(col__ktxd)
            for k in range(n):
                if bodo.libs.array_kernels.isna(arr, k):
                    continue
                val = arr[k]
                if not len(val) > ind >= -len(val
                    ) or bodo.libs.array_kernels.isna(val, ind):
                    continue
                bvs__guhfi = add_nested_counts(bvs__guhfi, val[ind])
            voaon__tst = bodo.utils.utils.alloc_type(n, hcbj__qdk, bvs__guhfi)
            for dvc__njh in range(n):
                if bodo.libs.array_kernels.isna(arr, dvc__njh):
                    setna(voaon__tst, dvc__njh)
                    continue
                val = arr[dvc__njh]
                if not len(val) > ind >= -len(val
                    ) or bodo.libs.array_kernels.isna(val, ind):
                    setna(voaon__tst, dvc__njh)
                    continue
                voaon__tst[dvc__njh] = val[ind]
            return voaon__tst
        return get_arr_item


def _is_same_categorical_array_type(arr_types):
    from bodo.hiframes.pd_categorical_ext import _to_readonly
    if not isinstance(arr_types, types.BaseTuple) or len(arr_types) == 0:
        return False
    jgebn__lyp = _to_readonly(arr_types.types[0])
    return all(isinstance(irjx__thaos, CategoricalArrayType) and 
        _to_readonly(irjx__thaos) == jgebn__lyp for irjx__thaos in
        arr_types.types)


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
        ttjgj__jebz = arr_list.dtype.dtype

        def array_item_concat_impl(arr_list):
            pizqd__xdle = 0
            uuixp__prqr = []
            for A in arr_list:
                waung__irel = len(A)
                bodo.libs.array_item_arr_ext.trim_excess_data(A)
                uuixp__prqr.append(bodo.libs.array_item_arr_ext.get_data(A))
                pizqd__xdle += waung__irel
            phb__vvall = np.empty(pizqd__xdle + 1, offset_type)
            uixaj__jmrs = bodo.libs.array_kernels.concat(uuixp__prqr)
            pzj__ekkru = np.empty(pizqd__xdle + 7 >> 3, np.uint8)
            evsbd__ektnp = 0
            nvb__orfk = 0
            for A in arr_list:
                ehdd__lug = bodo.libs.array_item_arr_ext.get_offsets(A)
                nhei__mrlc = bodo.libs.array_item_arr_ext.get_null_bitmap(A)
                waung__irel = len(A)
                soomf__txi = ehdd__lug[waung__irel]
                for i in range(waung__irel):
                    phb__vvall[i + evsbd__ektnp] = ehdd__lug[i] + nvb__orfk
                    dgnpc__oqq = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        nhei__mrlc, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(pzj__ekkru, i +
                        evsbd__ektnp, dgnpc__oqq)
                evsbd__ektnp += waung__irel
                nvb__orfk += soomf__txi
            phb__vvall[evsbd__ektnp] = nvb__orfk
            voaon__tst = bodo.libs.array_item_arr_ext.init_array_item_array(
                pizqd__xdle, uixaj__jmrs, phb__vvall, pzj__ekkru)
            return voaon__tst
        return array_item_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, bodo.StructArrayType):
        iqabv__uqpuk = arr_list.dtype.names
        swwag__fubr = 'def struct_array_concat_impl(arr_list):\n'
        swwag__fubr += f'    n_all = 0\n'
        for i in range(len(iqabv__uqpuk)):
            swwag__fubr += f'    concat_list{i} = []\n'
        swwag__fubr += '    for A in arr_list:\n'
        swwag__fubr += (
            '        data_tuple = bodo.libs.struct_arr_ext.get_data(A)\n')
        for i in range(len(iqabv__uqpuk)):
            swwag__fubr += f'        concat_list{i}.append(data_tuple[{i}])\n'
        swwag__fubr += '        n_all += len(A)\n'
        swwag__fubr += '    n_bytes = (n_all + 7) >> 3\n'
        swwag__fubr += '    new_mask = np.empty(n_bytes, np.uint8)\n'
        swwag__fubr += '    curr_bit = 0\n'
        swwag__fubr += '    for A in arr_list:\n'
        swwag__fubr += (
            '        old_mask = bodo.libs.struct_arr_ext.get_null_bitmap(A)\n')
        swwag__fubr += '        for j in range(len(A)):\n'
        swwag__fubr += (
            '            bit = bodo.libs.int_arr_ext.get_bit_bitmap_arr(old_mask, j)\n'
            )
        swwag__fubr += """            bodo.libs.int_arr_ext.set_bit_to_arr(new_mask, curr_bit, bit)
"""
        swwag__fubr += '            curr_bit += 1\n'
        swwag__fubr += '    return bodo.libs.struct_arr_ext.init_struct_arr(\n'
        itfpn__tku = ', '.join([
            f'bodo.libs.array_kernels.concat(concat_list{i})' for i in
            range(len(iqabv__uqpuk))])
        swwag__fubr += f'        ({itfpn__tku},),\n'
        swwag__fubr += '        new_mask,\n'
        swwag__fubr += f'        {iqabv__uqpuk},\n'
        swwag__fubr += '    )\n'
        glxrg__qmx = {}
        exec(swwag__fubr, {'bodo': bodo, 'np': np}, glxrg__qmx)
        return glxrg__qmx['struct_array_concat_impl']
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == datetime_date_array_type:

        def datetime_date_array_concat_impl(arr_list):
            dkb__awmw = 0
            for A in arr_list:
                dkb__awmw += len(A)
            lljbb__hkrji = (bodo.hiframes.datetime_date_ext.
                alloc_datetime_date_array(dkb__awmw))
            yunzn__cgc = 0
            for A in arr_list:
                for i in range(len(A)):
                    lljbb__hkrji._data[i + yunzn__cgc] = A._data[i]
                    dgnpc__oqq = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(lljbb__hkrji.
                        _null_bitmap, i + yunzn__cgc, dgnpc__oqq)
                yunzn__cgc += len(A)
            return lljbb__hkrji
        return datetime_date_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == datetime_timedelta_array_type:

        def datetime_timedelta_array_concat_impl(arr_list):
            dkb__awmw = 0
            for A in arr_list:
                dkb__awmw += len(A)
            lljbb__hkrji = (bodo.hiframes.datetime_timedelta_ext.
                alloc_datetime_timedelta_array(dkb__awmw))
            yunzn__cgc = 0
            for A in arr_list:
                for i in range(len(A)):
                    lljbb__hkrji._days_data[i + yunzn__cgc] = A._days_data[i]
                    lljbb__hkrji._seconds_data[i + yunzn__cgc
                        ] = A._seconds_data[i]
                    lljbb__hkrji._microseconds_data[i + yunzn__cgc
                        ] = A._microseconds_data[i]
                    dgnpc__oqq = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(lljbb__hkrji.
                        _null_bitmap, i + yunzn__cgc, dgnpc__oqq)
                yunzn__cgc += len(A)
            return lljbb__hkrji
        return datetime_timedelta_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, DecimalArrayType):
        qmwhy__tmdi = arr_list.dtype.precision
        uldeg__caq = arr_list.dtype.scale

        def decimal_array_concat_impl(arr_list):
            dkb__awmw = 0
            for A in arr_list:
                dkb__awmw += len(A)
            lljbb__hkrji = bodo.libs.decimal_arr_ext.alloc_decimal_array(
                dkb__awmw, qmwhy__tmdi, uldeg__caq)
            yunzn__cgc = 0
            for A in arr_list:
                for i in range(len(A)):
                    lljbb__hkrji._data[i + yunzn__cgc] = A._data[i]
                    dgnpc__oqq = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(lljbb__hkrji.
                        _null_bitmap, i + yunzn__cgc, dgnpc__oqq)
                yunzn__cgc += len(A)
            return lljbb__hkrji
        return decimal_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and (is_str_arr_type
        (arr_list.dtype) or arr_list.dtype == bodo.binary_array_type
        ) or isinstance(arr_list, types.BaseTuple) and all(is_str_arr_type(
        irjx__thaos) for irjx__thaos in arr_list.types):
        if isinstance(arr_list, types.BaseTuple):
            abs__xjm = arr_list.types[0]
        else:
            abs__xjm = arr_list.dtype
        abs__xjm = to_str_arr_if_dict_array(abs__xjm)

        def impl_str(arr_list):
            arr_list = decode_if_dict_array(arr_list)
            elf__hpgjv = 0
            hli__uafam = 0
            for A in arr_list:
                arr = A
                elf__hpgjv += len(arr)
                hli__uafam += bodo.libs.str_arr_ext.num_total_chars(arr)
            voaon__tst = bodo.utils.utils.alloc_type(elf__hpgjv, abs__xjm,
                (hli__uafam,))
            bodo.libs.str_arr_ext.set_null_bits_to_value(voaon__tst, -1)
            wyu__uil = 0
            cms__yxf = 0
            for A in arr_list:
                arr = A
                bodo.libs.str_arr_ext.set_string_array_range(voaon__tst,
                    arr, wyu__uil, cms__yxf)
                wyu__uil += len(arr)
                cms__yxf += bodo.libs.str_arr_ext.num_total_chars(arr)
            return voaon__tst
        return impl_str
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, IntegerArrayType) or isinstance(arr_list, types.
        BaseTuple) and all(isinstance(irjx__thaos.dtype, types.Integer) for
        irjx__thaos in arr_list.types) and any(isinstance(irjx__thaos,
        IntegerArrayType) for irjx__thaos in arr_list.types):

        def impl_int_arr_list(arr_list):
            kgw__xitbj = convert_to_nullable_tup(arr_list)
            cukwj__gocpg = []
            ogr__knrgl = 0
            for A in kgw__xitbj:
                cukwj__gocpg.append(A._data)
                ogr__knrgl += len(A)
            uixaj__jmrs = bodo.libs.array_kernels.concat(cukwj__gocpg)
            irq__rqtgg = ogr__knrgl + 7 >> 3
            dcab__xkhoo = np.empty(irq__rqtgg, np.uint8)
            niigu__njsd = 0
            for A in kgw__xitbj:
                kmyvk__fyo = A._null_bitmap
                for dvc__njh in range(len(A)):
                    dgnpc__oqq = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        kmyvk__fyo, dvc__njh)
                    bodo.libs.int_arr_ext.set_bit_to_arr(dcab__xkhoo,
                        niigu__njsd, dgnpc__oqq)
                    niigu__njsd += 1
            return bodo.libs.int_arr_ext.init_integer_array(uixaj__jmrs,
                dcab__xkhoo)
        return impl_int_arr_list
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == boolean_array or isinstance(arr_list, types
        .BaseTuple) and all(irjx__thaos.dtype == types.bool_ for
        irjx__thaos in arr_list.types) and any(irjx__thaos == boolean_array for
        irjx__thaos in arr_list.types):

        def impl_bool_arr_list(arr_list):
            kgw__xitbj = convert_to_nullable_tup(arr_list)
            cukwj__gocpg = []
            ogr__knrgl = 0
            for A in kgw__xitbj:
                cukwj__gocpg.append(A._data)
                ogr__knrgl += len(A)
            uixaj__jmrs = bodo.libs.array_kernels.concat(cukwj__gocpg)
            irq__rqtgg = ogr__knrgl + 7 >> 3
            dcab__xkhoo = np.empty(irq__rqtgg, np.uint8)
            niigu__njsd = 0
            for A in kgw__xitbj:
                kmyvk__fyo = A._null_bitmap
                for dvc__njh in range(len(A)):
                    dgnpc__oqq = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        kmyvk__fyo, dvc__njh)
                    bodo.libs.int_arr_ext.set_bit_to_arr(dcab__xkhoo,
                        niigu__njsd, dgnpc__oqq)
                    niigu__njsd += 1
            return bodo.libs.bool_arr_ext.init_bool_array(uixaj__jmrs,
                dcab__xkhoo)
        return impl_bool_arr_list
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, CategoricalArrayType):

        def cat_array_concat_impl(arr_list):
            vkwlr__txet = []
            for A in arr_list:
                vkwlr__txet.append(A.codes)
            return init_categorical_array(bodo.libs.array_kernels.concat(
                vkwlr__txet), arr_list[0].dtype)
        return cat_array_concat_impl
    if _is_same_categorical_array_type(arr_list):
        hjkc__ppcqq = ', '.join(f'arr_list[{i}].codes' for i in range(len(
            arr_list)))
        swwag__fubr = 'def impl(arr_list):\n'
        swwag__fubr += f"""    return init_categorical_array(bodo.libs.array_kernels.concat(({hjkc__ppcqq},)), arr_list[0].dtype)
"""
        vkk__vav = {}
        exec(swwag__fubr, {'bodo': bodo, 'init_categorical_array':
            init_categorical_array}, vkk__vav)
        return vkk__vav['impl']
    if isinstance(arr_list, types.List) and isinstance(arr_list.dtype,
        types.Array) and arr_list.dtype.ndim == 1:
        dtype = arr_list.dtype.dtype

        def impl_np_arr_list(arr_list):
            ogr__knrgl = 0
            for A in arr_list:
                ogr__knrgl += len(A)
            voaon__tst = np.empty(ogr__knrgl, dtype)
            foyz__oqqs = 0
            for A in arr_list:
                n = len(A)
                voaon__tst[foyz__oqqs:foyz__oqqs + n] = A
                foyz__oqqs += n
            return voaon__tst
        return impl_np_arr_list
    if isinstance(arr_list, types.BaseTuple) and any(isinstance(irjx__thaos,
        (types.Array, IntegerArrayType)) and isinstance(irjx__thaos.dtype,
        types.Integer) for irjx__thaos in arr_list.types) and any(
        isinstance(irjx__thaos, types.Array) and isinstance(irjx__thaos.
        dtype, types.Float) for irjx__thaos in arr_list.types):
        return lambda arr_list: np.concatenate(astype_float_tup(arr_list))
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, bodo.MapArrayType):

        def impl_map_arr_list(arr_list):
            xsyfj__uywy = []
            for A in arr_list:
                xsyfj__uywy.append(A._data)
            bya__jxil = bodo.libs.array_kernels.concat(xsyfj__uywy)
            lmt__lzcxz = bodo.libs.map_arr_ext.init_map_arr(bya__jxil)
            return lmt__lzcxz
        return impl_map_arr_list
    for evgjy__ovkkq in arr_list:
        if not isinstance(evgjy__ovkkq, types.Array):
            raise_bodo_error(f'concat of array types {arr_list} not supported')
    return lambda arr_list: np.concatenate(arr_list)


def astype_float_tup(arr_tup):
    return tuple(irjx__thaos.astype(np.float64) for irjx__thaos in arr_tup)


@overload(astype_float_tup, no_unliteral=True)
def overload_astype_float_tup(arr_tup):
    assert isinstance(arr_tup, types.BaseTuple)
    fduv__iiueh = len(arr_tup.types)
    swwag__fubr = 'def f(arr_tup):\n'
    swwag__fubr += '  return ({}{})\n'.format(','.join(
        'arr_tup[{}].astype(np.float64)'.format(i) for i in range(
        fduv__iiueh)), ',' if fduv__iiueh == 1 else '')
    glxrg__qmx = {}
    exec(swwag__fubr, {'np': np}, glxrg__qmx)
    fou__ews = glxrg__qmx['f']
    return fou__ews


def convert_to_nullable_tup(arr_tup):
    return arr_tup


@overload(convert_to_nullable_tup, no_unliteral=True)
def overload_convert_to_nullable_tup(arr_tup):
    if isinstance(arr_tup, (types.UniTuple, types.List)) and isinstance(arr_tup
        .dtype, (IntegerArrayType, BooleanArrayType)):
        return lambda arr_tup: arr_tup
    assert isinstance(arr_tup, types.BaseTuple)
    fduv__iiueh = len(arr_tup.types)
    jkk__emn = find_common_np_dtype(arr_tup.types)
    col__ktxd = None
    xet__xxr = ''
    if isinstance(jkk__emn, types.Integer):
        col__ktxd = bodo.libs.int_arr_ext.IntDtype(jkk__emn)
        xet__xxr = '.astype(out_dtype, False)'
    swwag__fubr = 'def f(arr_tup):\n'
    swwag__fubr += '  return ({}{})\n'.format(','.join(
        'bodo.utils.conversion.coerce_to_array(arr_tup[{}], use_nullable_array=True){}'
        .format(i, xet__xxr) for i in range(fduv__iiueh)), ',' if 
        fduv__iiueh == 1 else '')
    glxrg__qmx = {}
    exec(swwag__fubr, {'bodo': bodo, 'out_dtype': col__ktxd}, glxrg__qmx)
    njn__uveet = glxrg__qmx['f']
    return njn__uveet


def nunique(A, dropna):
    return len(set(A))


def nunique_parallel(A, dropna):
    return len(set(A))


@overload(nunique, no_unliteral=True)
def nunique_overload(A, dropna):

    def nunique_seq(A, dropna):
        s, cnoa__jyop = build_set_seen_na(A)
        return len(s) + int(not dropna and cnoa__jyop)
    return nunique_seq


@overload(nunique_parallel, no_unliteral=True)
def nunique_overload_parallel(A, dropna):
    sum_op = bodo.libs.distributed_api.Reduce_Type.Sum.value

    def nunique_par(A, dropna):
        npqm__dukg = bodo.libs.array_kernels.unique(A, dropna, parallel=True)
        oese__tbtv = len(npqm__dukg)
        return bodo.libs.distributed_api.dist_reduce(oese__tbtv, np.int32(
            sum_op))
    return nunique_par


def unique(A, dropna=False, parallel=False):
    return np.array([wcb__asz for wcb__asz in set(A)]).astype(A.dtype)


def cummin(A):
    return A


@overload(cummin, no_unliteral=True)
def cummin_overload(A):
    if isinstance(A.dtype, types.Float):
        fcx__yocb = np.finfo(A.dtype(1).dtype).max
    else:
        fcx__yocb = np.iinfo(A.dtype(1).dtype).max

    def impl(A):
        n = len(A)
        voaon__tst = np.empty(n, A.dtype)
        nds__kmkzd = fcx__yocb
        for i in range(n):
            nds__kmkzd = min(nds__kmkzd, A[i])
            voaon__tst[i] = nds__kmkzd
        return voaon__tst
    return impl


def cummax(A):
    return A


@overload(cummax, no_unliteral=True)
def cummax_overload(A):
    if isinstance(A.dtype, types.Float):
        fcx__yocb = np.finfo(A.dtype(1).dtype).min
    else:
        fcx__yocb = np.iinfo(A.dtype(1).dtype).min

    def impl(A):
        n = len(A)
        voaon__tst = np.empty(n, A.dtype)
        nds__kmkzd = fcx__yocb
        for i in range(n):
            nds__kmkzd = max(nds__kmkzd, A[i])
            voaon__tst[i] = nds__kmkzd
        return voaon__tst
    return impl


@overload(unique, no_unliteral=True)
def unique_overload(A, dropna=False, parallel=False):

    def unique_impl(A, dropna=False, parallel=False):
        rpao__ifm = arr_info_list_to_table([array_to_info(A)])
        dvmw__ndk = 1
        wfd__zbxl = 0
        bjpd__fdmck = drop_duplicates_table(rpao__ifm, parallel, dvmw__ndk,
            wfd__zbxl, dropna, True)
        voaon__tst = info_to_array(info_from_table(bjpd__fdmck, 0), A)
        delete_table(rpao__ifm)
        delete_table(bjpd__fdmck)
        return voaon__tst
    return unique_impl


def explode(arr, index_arr):
    return pd.Series(arr, index_arr).explode()


@overload(explode, no_unliteral=True)
def overload_explode(arr, index_arr):
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type
    ttjgj__jebz = bodo.utils.typing.to_nullable_type(arr.dtype)
    bqe__zdu = index_arr
    ove__ucey = bqe__zdu.dtype

    def impl(arr, index_arr):
        n = len(arr)
        bvs__guhfi = init_nested_counts(ttjgj__jebz)
        ftlps__lies = init_nested_counts(ove__ucey)
        for i in range(n):
            wwxho__fawr = index_arr[i]
            if isna(arr, i):
                bvs__guhfi = (bvs__guhfi[0] + 1,) + bvs__guhfi[1:]
                ftlps__lies = add_nested_counts(ftlps__lies, wwxho__fawr)
                continue
            kro__mtl = arr[i]
            if len(kro__mtl) == 0:
                bvs__guhfi = (bvs__guhfi[0] + 1,) + bvs__guhfi[1:]
                ftlps__lies = add_nested_counts(ftlps__lies, wwxho__fawr)
                continue
            bvs__guhfi = add_nested_counts(bvs__guhfi, kro__mtl)
            for eavmk__ebiy in range(len(kro__mtl)):
                ftlps__lies = add_nested_counts(ftlps__lies, wwxho__fawr)
        voaon__tst = bodo.utils.utils.alloc_type(bvs__guhfi[0], ttjgj__jebz,
            bvs__guhfi[1:])
        qnkos__gkk = bodo.utils.utils.alloc_type(bvs__guhfi[0], bqe__zdu,
            ftlps__lies)
        nvb__orfk = 0
        for i in range(n):
            if isna(arr, i):
                setna(voaon__tst, nvb__orfk)
                qnkos__gkk[nvb__orfk] = index_arr[i]
                nvb__orfk += 1
                continue
            kro__mtl = arr[i]
            soomf__txi = len(kro__mtl)
            if soomf__txi == 0:
                setna(voaon__tst, nvb__orfk)
                qnkos__gkk[nvb__orfk] = index_arr[i]
                nvb__orfk += 1
                continue
            voaon__tst[nvb__orfk:nvb__orfk + soomf__txi] = kro__mtl
            qnkos__gkk[nvb__orfk:nvb__orfk + soomf__txi] = index_arr[i]
            nvb__orfk += soomf__txi
        return voaon__tst, qnkos__gkk
    return impl


def explode_no_index(arr):
    return pd.Series(arr).explode()


@overload(explode_no_index, no_unliteral=True)
def overload_explode_no_index(arr, counts):
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type
    ttjgj__jebz = bodo.utils.typing.to_nullable_type(arr.dtype)

    def impl(arr, counts):
        n = len(arr)
        bvs__guhfi = init_nested_counts(ttjgj__jebz)
        for i in range(n):
            if isna(arr, i):
                bvs__guhfi = (bvs__guhfi[0] + 1,) + bvs__guhfi[1:]
                bwrbk__jgr = 1
            else:
                kro__mtl = arr[i]
                kqow__lrmg = len(kro__mtl)
                if kqow__lrmg == 0:
                    bvs__guhfi = (bvs__guhfi[0] + 1,) + bvs__guhfi[1:]
                    bwrbk__jgr = 1
                    continue
                else:
                    bvs__guhfi = add_nested_counts(bvs__guhfi, kro__mtl)
                    bwrbk__jgr = kqow__lrmg
            if counts[i] != bwrbk__jgr:
                raise ValueError(
                    'DataFrame.explode(): columns must have matching element counts'
                    )
        voaon__tst = bodo.utils.utils.alloc_type(bvs__guhfi[0], ttjgj__jebz,
            bvs__guhfi[1:])
        nvb__orfk = 0
        for i in range(n):
            if isna(arr, i):
                setna(voaon__tst, nvb__orfk)
                nvb__orfk += 1
                continue
            kro__mtl = arr[i]
            soomf__txi = len(kro__mtl)
            if soomf__txi == 0:
                setna(voaon__tst, nvb__orfk)
                nvb__orfk += 1
                continue
            voaon__tst[nvb__orfk:nvb__orfk + soomf__txi] = kro__mtl
            nvb__orfk += soomf__txi
        return voaon__tst
    return impl


def get_arr_lens(arr, na_empty_as_one=True):
    return [len(qicuj__kcvb) for qicuj__kcvb in arr]


@overload(get_arr_lens, inline='always', no_unliteral=True)
def overload_get_arr_lens(arr, na_empty_as_one=True):
    na_empty_as_one = get_overload_const_bool(na_empty_as_one)
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type or is_str_arr_type(arr
        ) and not na_empty_as_one, f'get_arr_lens: invalid input array type {arr}'
    if na_empty_as_one:
        bniz__yxro = 'np.empty(n, np.int64)'
        totd__vulcd = 'out_arr[i] = 1'
        wtna__amhqw = 'max(len(arr[i]), 1)'
    else:
        bniz__yxro = 'bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)'
        totd__vulcd = 'bodo.libs.array_kernels.setna(out_arr, i)'
        wtna__amhqw = 'len(arr[i])'
    swwag__fubr = f"""def impl(arr, na_empty_as_one=True):
    numba.parfors.parfor.init_prange()
    n = len(arr)
    out_arr = {bniz__yxro}
    for i in numba.parfors.parfor.internal_prange(n):
        if bodo.libs.array_kernels.isna(arr, i):
            {totd__vulcd}
        else:
            out_arr[i] = {wtna__amhqw}
    return out_arr
    """
    glxrg__qmx = {}
    exec(swwag__fubr, {'bodo': bodo, 'numba': numba, 'np': np}, glxrg__qmx)
    impl = glxrg__qmx['impl']
    return impl


def explode_str_split(arr, pat, n, index_arr):
    return pd.Series(arr, index_arr).str.split(pat, n).explode()


@overload(explode_str_split, no_unliteral=True)
def overload_explode_str_split(arr, pat, n, index_arr):
    assert is_str_arr_type(arr
        ), f'explode_str_split: string array expected, not {arr}'
    bqe__zdu = index_arr
    ove__ucey = bqe__zdu.dtype

    def impl(arr, pat, n, index_arr):
        blwxt__kgqxs = pat is not None and len(pat) > 1
        if blwxt__kgqxs:
            pux__bslq = re.compile(pat)
            if n == -1:
                n = 0
        elif n == 0:
            n = -1
        ouj__altk = len(arr)
        elf__hpgjv = 0
        hli__uafam = 0
        ftlps__lies = init_nested_counts(ove__ucey)
        for i in range(ouj__altk):
            wwxho__fawr = index_arr[i]
            if bodo.libs.array_kernels.isna(arr, i):
                elf__hpgjv += 1
                ftlps__lies = add_nested_counts(ftlps__lies, wwxho__fawr)
                continue
            if blwxt__kgqxs:
                mnu__zanb = pux__bslq.split(arr[i], maxsplit=n)
            else:
                mnu__zanb = arr[i].split(pat, n)
            elf__hpgjv += len(mnu__zanb)
            for s in mnu__zanb:
                ftlps__lies = add_nested_counts(ftlps__lies, wwxho__fawr)
                hli__uafam += bodo.libs.str_arr_ext.get_utf8_size(s)
        voaon__tst = bodo.libs.str_arr_ext.pre_alloc_string_array(elf__hpgjv,
            hli__uafam)
        qnkos__gkk = bodo.utils.utils.alloc_type(elf__hpgjv, bqe__zdu,
            ftlps__lies)
        phpa__hykf = 0
        for dvc__njh in range(ouj__altk):
            if isna(arr, dvc__njh):
                voaon__tst[phpa__hykf] = ''
                bodo.libs.array_kernels.setna(voaon__tst, phpa__hykf)
                qnkos__gkk[phpa__hykf] = index_arr[dvc__njh]
                phpa__hykf += 1
                continue
            if blwxt__kgqxs:
                mnu__zanb = pux__bslq.split(arr[dvc__njh], maxsplit=n)
            else:
                mnu__zanb = arr[dvc__njh].split(pat, n)
            ywo__sgoqn = len(mnu__zanb)
            voaon__tst[phpa__hykf:phpa__hykf + ywo__sgoqn] = mnu__zanb
            qnkos__gkk[phpa__hykf:phpa__hykf + ywo__sgoqn] = index_arr[dvc__njh
                ]
            phpa__hykf += ywo__sgoqn
        return voaon__tst, qnkos__gkk
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
            voaon__tst = np.empty(n, dtype)
            for i in numba.parfors.parfor.internal_prange(n):
                voaon__tst[i] = np.nan
            return voaon__tst
        return impl_float
    pud__fxur = to_str_arr_if_dict_array(arr)

    def impl(n, arr):
        numba.parfors.parfor.init_prange()
        voaon__tst = bodo.utils.utils.alloc_type(n, pud__fxur, (0,))
        for i in numba.parfors.parfor.internal_prange(n):
            setna(voaon__tst, i)
        return voaon__tst
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
    kwgi__ptu = A
    if A == types.Array(types.uint8, 1, 'C'):

        def impl_char(A, old_size, new_len):
            voaon__tst = bodo.utils.utils.alloc_type(new_len, kwgi__ptu)
            bodo.libs.str_arr_ext.str_copy_ptr(voaon__tst.ctypes, 0, A.
                ctypes, old_size)
            return voaon__tst
        return impl_char

    def impl(A, old_size, new_len):
        voaon__tst = bodo.utils.utils.alloc_type(new_len, kwgi__ptu, (-1,))
        voaon__tst[:old_size] = A[:old_size]
        return voaon__tst
    return impl


@register_jitable
def calc_nitems(start, stop, step):
    tbwr__tqg = math.ceil((stop - start) / step)
    return int(max(tbwr__tqg, 0))


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
    if any(isinstance(wcb__asz, types.Complex) for wcb__asz in args):

        def arange_4(start, stop, step, dtype):
            numba.parfors.parfor.init_prange()
            fjurd__evasg = (stop - start) / step
            tbwr__tqg = math.ceil(fjurd__evasg.real)
            brwl__irnpo = math.ceil(fjurd__evasg.imag)
            thk__vxkxf = int(max(min(brwl__irnpo, tbwr__tqg), 0))
            arr = np.empty(thk__vxkxf, dtype)
            for i in numba.parfors.parfor.internal_prange(thk__vxkxf):
                arr[i] = start + i * step
            return arr
    else:

        def arange_4(start, stop, step, dtype):
            numba.parfors.parfor.init_prange()
            thk__vxkxf = bodo.libs.array_kernels.calc_nitems(start, stop, step)
            arr = np.empty(thk__vxkxf, dtype)
            for i in numba.parfors.parfor.internal_prange(thk__vxkxf):
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
        azat__fyfz = arr,
        if not inplace:
            azat__fyfz = arr.copy(),
        ndcq__iboze = bodo.libs.str_arr_ext.to_list_if_immutable_arr(azat__fyfz
            )
        caqfh__bcf = bodo.libs.str_arr_ext.to_list_if_immutable_arr(data, True)
        bodo.libs.timsort.sort(ndcq__iboze, 0, n, caqfh__bcf)
        if not ascending:
            bodo.libs.timsort.reverseRange(ndcq__iboze, 0, n, caqfh__bcf)
        bodo.libs.str_arr_ext.cp_str_list_to_array(azat__fyfz, ndcq__iboze)
        return azat__fyfz[0]
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
        lmt__lzcxz = []
        for i in range(n):
            if A[i]:
                lmt__lzcxz.append(i + offset)
        return np.array(lmt__lzcxz, np.int64),
    return impl


def ffill_bfill_arr(arr):
    return arr


@overload(ffill_bfill_arr, no_unliteral=True)
def ffill_bfill_overload(A, method, parallel=False):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A,
        'bodo.ffill_bfill_arr()')
    kwgi__ptu = element_type(A)
    if kwgi__ptu == types.unicode_type:
        null_value = '""'
    elif kwgi__ptu == types.bool_:
        null_value = 'False'
    elif kwgi__ptu == bodo.datetime64ns:
        null_value = (
            'bodo.utils.conversion.unbox_if_timestamp(pd.to_datetime(0))')
    elif kwgi__ptu == bodo.timedelta64ns:
        null_value = (
            'bodo.utils.conversion.unbox_if_timestamp(pd.to_timedelta(0))')
    else:
        null_value = '0'
    phpa__hykf = 'i'
    tfj__gyo = False
    vbh__sqqb = get_overload_const_str(method)
    if vbh__sqqb in ('ffill', 'pad'):
        sckre__tevl = 'n'
        send_right = True
    elif vbh__sqqb in ('backfill', 'bfill'):
        sckre__tevl = 'n-1, -1, -1'
        send_right = False
        if kwgi__ptu == types.unicode_type:
            phpa__hykf = '(n - 1) - i'
            tfj__gyo = True
    swwag__fubr = 'def impl(A, method, parallel=False):\n'
    swwag__fubr += '  A = decode_if_dict_array(A)\n'
    swwag__fubr += '  has_last_value = False\n'
    swwag__fubr += f'  last_value = {null_value}\n'
    swwag__fubr += '  if parallel:\n'
    swwag__fubr += '    rank = bodo.libs.distributed_api.get_rank()\n'
    swwag__fubr += '    n_pes = bodo.libs.distributed_api.get_size()\n'
    swwag__fubr += f"""    has_last_value, last_value = null_border_icomm(A, rank, n_pes, {null_value}, {send_right})
"""
    swwag__fubr += '  n = len(A)\n'
    swwag__fubr += '  out_arr = bodo.utils.utils.alloc_type(n, A, (-1,))\n'
    swwag__fubr += f'  for i in range({sckre__tevl}):\n'
    swwag__fubr += (
        '    if (bodo.libs.array_kernels.isna(A, i) and not has_last_value):\n'
        )
    swwag__fubr += (
        f'      bodo.libs.array_kernels.setna(out_arr, {phpa__hykf})\n')
    swwag__fubr += '      continue\n'
    swwag__fubr += '    s = A[i]\n'
    swwag__fubr += '    if bodo.libs.array_kernels.isna(A, i):\n'
    swwag__fubr += '      s = last_value\n'
    swwag__fubr += f'    out_arr[{phpa__hykf}] = s\n'
    swwag__fubr += '    last_value = s\n'
    swwag__fubr += '    has_last_value = True\n'
    if tfj__gyo:
        swwag__fubr += '  return out_arr[::-1]\n'
    else:
        swwag__fubr += '  return out_arr\n'
    jjpfs__kwmyw = {}
    exec(swwag__fubr, {'bodo': bodo, 'numba': numba, 'pd': pd,
        'null_border_icomm': null_border_icomm, 'decode_if_dict_array':
        decode_if_dict_array}, jjpfs__kwmyw)
    impl = jjpfs__kwmyw['impl']
    return impl


@register_jitable(cache=True)
def null_border_icomm(in_arr, rank, n_pes, null_value, send_right=True):
    if send_right:
        gupw__agsx = 0
        qic__mwtz = n_pes - 1
        tevsh__kdun = np.int32(rank + 1)
        ienx__mbj = np.int32(rank - 1)
        emwb__res = len(in_arr) - 1
        ahhhl__rphfs = -1
        tpuuw__qofe = -1
    else:
        gupw__agsx = n_pes - 1
        qic__mwtz = 0
        tevsh__kdun = np.int32(rank - 1)
        ienx__mbj = np.int32(rank + 1)
        emwb__res = 0
        ahhhl__rphfs = len(in_arr)
        tpuuw__qofe = 1
    dxr__ohc = np.int32(bodo.hiframes.rolling.comm_border_tag)
    itlg__ntt = np.empty(1, dtype=np.bool_)
    msrss__ugxfe = bodo.utils.utils.alloc_type(1, in_arr, (-1,))
    dbl__whjpl = np.empty(1, dtype=np.bool_)
    lcczw__warx = bodo.utils.utils.alloc_type(1, in_arr, (-1,))
    nqag__tce = False
    alwx__zoj = null_value
    for i in range(emwb__res, ahhhl__rphfs, tpuuw__qofe):
        if not isna(in_arr, i):
            nqag__tce = True
            alwx__zoj = in_arr[i]
            break
    if rank != gupw__agsx:
        mmtwd__gbm = bodo.libs.distributed_api.irecv(itlg__ntt, 1,
            ienx__mbj, dxr__ohc, True)
        bodo.libs.distributed_api.wait(mmtwd__gbm, True)
        gedk__zwzlg = bodo.libs.distributed_api.irecv(msrss__ugxfe, 1,
            ienx__mbj, dxr__ohc, True)
        bodo.libs.distributed_api.wait(gedk__zwzlg, True)
        cnu__aruo = itlg__ntt[0]
        utg__lmz = msrss__ugxfe[0]
    else:
        cnu__aruo = False
        utg__lmz = null_value
    if nqag__tce:
        dbl__whjpl[0] = nqag__tce
        lcczw__warx[0] = alwx__zoj
    else:
        dbl__whjpl[0] = cnu__aruo
        lcczw__warx[0] = utg__lmz
    if rank != qic__mwtz:
        khv__sfk = bodo.libs.distributed_api.isend(dbl__whjpl, 1,
            tevsh__kdun, dxr__ohc, True)
        oon__yaekt = bodo.libs.distributed_api.isend(lcczw__warx, 1,
            tevsh__kdun, dxr__ohc, True)
    return cnu__aruo, utg__lmz


@overload(np.sort, inline='always', no_unliteral=True)
def np_sort(A, axis=-1, kind=None, order=None):
    if not bodo.utils.utils.is_array_typ(A, False) or isinstance(A, types.Array
        ):
        return
    fun__dohsn = {'axis': axis, 'kind': kind, 'order': order}
    flwqn__ijfa = {'axis': -1, 'kind': None, 'order': None}
    check_unsupported_args('np.sort', fun__dohsn, flwqn__ijfa, 'numpy')

    def impl(A, axis=-1, kind=None, order=None):
        return pd.Series(A).sort_values().values
    return impl


def repeat_kernel(A, repeats):
    return A


@overload(repeat_kernel, no_unliteral=True)
def repeat_kernel_overload(A, repeats):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A,
        'Series.repeat()')
    kwgi__ptu = to_str_arr_if_dict_array(A)
    if isinstance(repeats, types.Integer):

        def impl_int(A, repeats):
            A = decode_if_dict_array(A)
            ouj__altk = len(A)
            voaon__tst = bodo.utils.utils.alloc_type(ouj__altk * repeats,
                kwgi__ptu, (-1,))
            for i in range(ouj__altk):
                phpa__hykf = i * repeats
                if bodo.libs.array_kernels.isna(A, i):
                    for dvc__njh in range(repeats):
                        bodo.libs.array_kernels.setna(voaon__tst, 
                            phpa__hykf + dvc__njh)
                else:
                    voaon__tst[phpa__hykf:phpa__hykf + repeats] = A[i]
            return voaon__tst
        return impl_int

    def impl_arr(A, repeats):
        A = decode_if_dict_array(A)
        ouj__altk = len(A)
        voaon__tst = bodo.utils.utils.alloc_type(repeats.sum(), kwgi__ptu,
            (-1,))
        phpa__hykf = 0
        for i in range(ouj__altk):
            wwmtf__etrdt = repeats[i]
            if bodo.libs.array_kernels.isna(A, i):
                for dvc__njh in range(wwmtf__etrdt):
                    bodo.libs.array_kernels.setna(voaon__tst, phpa__hykf +
                        dvc__njh)
            else:
                voaon__tst[phpa__hykf:phpa__hykf + wwmtf__etrdt] = A[i]
            phpa__hykf += wwmtf__etrdt
        return voaon__tst
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
        gaa__chnwi = bodo.libs.array_kernels.unique(A)
        return bodo.allgatherv(gaa__chnwi, False)
    return impl


@overload(np.union1d, inline='always', no_unliteral=True)
def overload_union1d(A1, A2):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.union1d()')

    def impl(A1, A2):
        nzk__rihe = bodo.libs.array_kernels.concat([A1, A2])
        eey__bje = bodo.libs.array_kernels.unique(nzk__rihe)
        return pd.Series(eey__bje).sort_values().values
    return impl


@overload(np.intersect1d, inline='always', no_unliteral=True)
def overload_intersect1d(A1, A2, assume_unique=False, return_indices=False):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    fun__dohsn = {'assume_unique': assume_unique, 'return_indices':
        return_indices}
    flwqn__ijfa = {'assume_unique': False, 'return_indices': False}
    check_unsupported_args('np.intersect1d', fun__dohsn, flwqn__ijfa, 'numpy')
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.intersect1d()'
            )
    if A1.ndim != 1 or A2.ndim != 1:
        raise BodoError('Only 1D arrays supported in np.intersect1d()')

    def impl(A1, A2, assume_unique=False, return_indices=False):
        dpj__sqxa = bodo.libs.array_kernels.unique(A1)
        zlkex__oajr = bodo.libs.array_kernels.unique(A2)
        nzk__rihe = bodo.libs.array_kernels.concat([dpj__sqxa, zlkex__oajr])
        ihdlg__nln = pd.Series(nzk__rihe).sort_values().values
        return slice_array_intersect1d(ihdlg__nln)
    return impl


@register_jitable
def slice_array_intersect1d(arr):
    skt__paj = arr[1:] == arr[:-1]
    return arr[:-1][skt__paj]


@overload(np.setdiff1d, inline='always', no_unliteral=True)
def overload_setdiff1d(A1, A2, assume_unique=False):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    fun__dohsn = {'assume_unique': assume_unique}
    flwqn__ijfa = {'assume_unique': False}
    check_unsupported_args('np.setdiff1d', fun__dohsn, flwqn__ijfa, 'numpy')
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.setdiff1d()')
    if A1.ndim != 1 or A2.ndim != 1:
        raise BodoError('Only 1D arrays supported in np.setdiff1d()')

    def impl(A1, A2, assume_unique=False):
        dpj__sqxa = bodo.libs.array_kernels.unique(A1)
        zlkex__oajr = bodo.libs.array_kernels.unique(A2)
        skt__paj = calculate_mask_setdiff1d(dpj__sqxa, zlkex__oajr)
        return pd.Series(dpj__sqxa[skt__paj]).sort_values().values
    return impl


@register_jitable
def calculate_mask_setdiff1d(A1, A2):
    skt__paj = np.ones(len(A1), np.bool_)
    for i in range(len(A2)):
        skt__paj &= A1 != A2[i]
    return skt__paj


@overload(np.linspace, inline='always', no_unliteral=True)
def np_linspace(start, stop, num=50, endpoint=True, retstep=False, dtype=
    None, axis=0):
    fun__dohsn = {'retstep': retstep, 'axis': axis}
    flwqn__ijfa = {'retstep': False, 'axis': 0}
    check_unsupported_args('np.linspace', fun__dohsn, flwqn__ijfa, 'numpy')
    rmwm__xyc = False
    if is_overload_none(dtype):
        kwgi__ptu = np.promote_types(np.promote_types(numba.np.
            numpy_support.as_dtype(start), numba.np.numpy_support.as_dtype(
            stop)), numba.np.numpy_support.as_dtype(types.float64)).type
    else:
        if isinstance(dtype.dtype, types.Integer):
            rmwm__xyc = True
        kwgi__ptu = numba.np.numpy_support.as_dtype(dtype).type
    if rmwm__xyc:

        def impl_int(start, stop, num=50, endpoint=True, retstep=False,
            dtype=None, axis=0):
            looo__xfpq = np_linspace_get_stepsize(start, stop, num, endpoint)
            numba.parfors.parfor.init_prange()
            voaon__tst = np.empty(num, kwgi__ptu)
            for i in numba.parfors.parfor.internal_prange(num):
                voaon__tst[i] = kwgi__ptu(np.floor(start + i * looo__xfpq))
            return voaon__tst
        return impl_int
    else:

        def impl(start, stop, num=50, endpoint=True, retstep=False, dtype=
            None, axis=0):
            looo__xfpq = np_linspace_get_stepsize(start, stop, num, endpoint)
            numba.parfors.parfor.init_prange()
            voaon__tst = np.empty(num, kwgi__ptu)
            for i in numba.parfors.parfor.internal_prange(num):
                voaon__tst[i] = kwgi__ptu(start + i * looo__xfpq)
            return voaon__tst
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
        fduv__iiueh = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                fduv__iiueh += A[i] == val
        return fduv__iiueh > 0
    return impl


@overload(np.any, inline='always', no_unliteral=True)
def np_any(A, axis=None, out=None, keepdims=None):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A, 'np.any()')
    if not (bodo.utils.utils.is_array_typ(A, False) and A.ndim == 1):
        return
    fun__dohsn = {'axis': axis, 'out': out, 'keepdims': keepdims}
    flwqn__ijfa = {'axis': None, 'out': None, 'keepdims': None}
    check_unsupported_args('np.any', fun__dohsn, flwqn__ijfa, 'numpy')

    def impl(A, axis=None, out=None, keepdims=None):
        numba.parfors.parfor.init_prange()
        fduv__iiueh = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                fduv__iiueh += int(bool(A[i]))
        return fduv__iiueh > 0
    return impl


@overload(np.all, inline='always', no_unliteral=True)
def np_all(A, axis=None, out=None, keepdims=None):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(A, 'np.all()')
    if not (bodo.utils.utils.is_array_typ(A, False) and A.ndim == 1):
        return
    fun__dohsn = {'axis': axis, 'out': out, 'keepdims': keepdims}
    flwqn__ijfa = {'axis': None, 'out': None, 'keepdims': None}
    check_unsupported_args('np.any', fun__dohsn, flwqn__ijfa, 'numpy')

    def impl(A, axis=None, out=None, keepdims=None):
        numba.parfors.parfor.init_prange()
        fduv__iiueh = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                fduv__iiueh += int(bool(A[i]))
        return fduv__iiueh == n
    return impl


@overload(np.cbrt, inline='always', no_unliteral=True)
def np_cbrt(A, out=None, where=True, casting='same_kind', order='K', dtype=
    None, subok=True):
    if not (isinstance(A, types.Number) or bodo.utils.utils.is_array_typ(A,
        False) and A.ndim == 1 and isinstance(A.dtype, types.Number)):
        return
    fun__dohsn = {'out': out, 'where': where, 'casting': casting, 'order':
        order, 'dtype': dtype, 'subok': subok}
    flwqn__ijfa = {'out': None, 'where': True, 'casting': 'same_kind',
        'order': 'K', 'dtype': None, 'subok': True}
    check_unsupported_args('np.cbrt', fun__dohsn, flwqn__ijfa, 'numpy')
    if bodo.utils.utils.is_array_typ(A, False):
        bcxbs__ljwbw = np.promote_types(numba.np.numpy_support.as_dtype(A.
            dtype), numba.np.numpy_support.as_dtype(types.float32)).type

        def impl_arr(A, out=None, where=True, casting='same_kind', order=
            'K', dtype=None, subok=True):
            numba.parfors.parfor.init_prange()
            n = len(A)
            voaon__tst = np.empty(n, bcxbs__ljwbw)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(A, i):
                    bodo.libs.array_kernels.setna(voaon__tst, i)
                    continue
                voaon__tst[i] = np_cbrt_scalar(A[i], bcxbs__ljwbw)
            return voaon__tst
        return impl_arr
    bcxbs__ljwbw = np.promote_types(numba.np.numpy_support.as_dtype(A),
        numba.np.numpy_support.as_dtype(types.float32)).type

    def impl_scalar(A, out=None, where=True, casting='same_kind', order='K',
        dtype=None, subok=True):
        return np_cbrt_scalar(A, bcxbs__ljwbw)
    return impl_scalar


@register_jitable
def np_cbrt_scalar(x, float_dtype):
    if np.isnan(x):
        return np.nan
    jlnq__sis = x < 0
    if jlnq__sis:
        x = -x
    res = np.power(float_dtype(x), 1.0 / 3.0)
    if jlnq__sis:
        return -res
    return res


@overload(np.hstack, no_unliteral=True)
def np_hstack(tup):
    fpvvb__mmnzc = isinstance(tup, (types.BaseTuple, types.List))
    avt__wjg = isinstance(tup, (bodo.SeriesType, bodo.hiframes.
        pd_series_ext.HeterogeneousSeriesType)) and isinstance(tup.data, (
        types.BaseTuple, types.List, bodo.NullableTupleType))
    if isinstance(tup, types.BaseTuple):
        for evgjy__ovkkq in tup.types:
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(
                evgjy__ovkkq, 'numpy.hstack()')
            fpvvb__mmnzc = fpvvb__mmnzc and bodo.utils.utils.is_array_typ(
                evgjy__ovkkq, False)
    elif isinstance(tup, types.List):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(tup.dtype,
            'numpy.hstack()')
        fpvvb__mmnzc = bodo.utils.utils.is_array_typ(tup.dtype, False)
    elif avt__wjg:
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(tup,
            'numpy.hstack()')
        oanbh__dph = tup.data.tuple_typ if isinstance(tup.data, bodo.
            NullableTupleType) else tup.data
        for evgjy__ovkkq in oanbh__dph.types:
            avt__wjg = avt__wjg and bodo.utils.utils.is_array_typ(evgjy__ovkkq,
                False)
    if not (fpvvb__mmnzc or avt__wjg):
        return
    if avt__wjg:

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
    fun__dohsn = {'check_valid': check_valid, 'tol': tol}
    flwqn__ijfa = {'check_valid': 'warn', 'tol': 1e-08}
    check_unsupported_args('np.random.multivariate_normal', fun__dohsn,
        flwqn__ijfa, 'numpy')
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
        cyhgi__sjgz = mean.shape[0]
        jmz__wiey = size, cyhgi__sjgz
        vkl__cewv = np.random.standard_normal(jmz__wiey)
        cov = cov.astype(np.float64)
        cekms__zvw, s, iuji__kwdh = np.linalg.svd(cov)
        res = np.dot(vkl__cewv, np.sqrt(s).reshape(cyhgi__sjgz, 1) * iuji__kwdh
            )
        nklqq__gst = res + mean
        return nklqq__gst
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
            dfqh__eppp = bodo.hiframes.series_kernels._get_type_max_value(arr)
            fhu__vhikl = typing.builtins.IndexValue(-1, dfqh__eppp)
            for i in numba.parfors.parfor.internal_prange(len(arr)):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                bjxsi__qrorp = typing.builtins.IndexValue(i, arr[i])
                fhu__vhikl = min(fhu__vhikl, bjxsi__qrorp)
            return fhu__vhikl.index
        return impl_bodo_arr
    if isinstance(arr, CategoricalArrayType):
        assert arr.dtype.ordered, 'Categorical Array must be ordered to select an argmin'
        fstpg__kejhi = (bodo.hiframes.pd_categorical_ext.
            get_categories_int_type(arr.dtype))

        def impl_cat_arr(arr):
            suty__rqife = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            dfqh__eppp = fstpg__kejhi(len(arr.dtype.categories) + 1)
            fhu__vhikl = typing.builtins.IndexValue(-1, dfqh__eppp)
            for i in numba.parfors.parfor.internal_prange(len(arr)):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                bjxsi__qrorp = typing.builtins.IndexValue(i, suty__rqife[i])
                fhu__vhikl = min(fhu__vhikl, bjxsi__qrorp)
            return fhu__vhikl.index
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
            dfqh__eppp = bodo.hiframes.series_kernels._get_type_min_value(arr)
            fhu__vhikl = typing.builtins.IndexValue(-1, dfqh__eppp)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                bjxsi__qrorp = typing.builtins.IndexValue(i, arr[i])
                fhu__vhikl = max(fhu__vhikl, bjxsi__qrorp)
            return fhu__vhikl.index
        return impl_bodo_arr
    if isinstance(arr, CategoricalArrayType):
        assert arr.dtype.ordered, 'Categorical Array must be ordered to select an argmin'
        fstpg__kejhi = (bodo.hiframes.pd_categorical_ext.
            get_categories_int_type(arr.dtype))

        def impl_cat_arr(arr):
            n = len(arr)
            suty__rqife = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            dfqh__eppp = fstpg__kejhi(-1)
            fhu__vhikl = typing.builtins.IndexValue(-1, dfqh__eppp)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                bjxsi__qrorp = typing.builtins.IndexValue(i, suty__rqife[i])
                fhu__vhikl = max(fhu__vhikl, bjxsi__qrorp)
            return fhu__vhikl.index
        return impl_cat_arr
    return lambda arr: arr.argmax()


@overload_attribute(types.Array, 'nbytes', inline='always')
def overload_dataframe_index(A):
    return lambda A: A.size * bodo.io.np_io.get_dtype_size(A.dtype)
