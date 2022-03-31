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
        uztv__ozt = arr.dtype('NaT')

        def _setnan_impl(arr, ind, int_nan_const=0):
            arr[ind] = uztv__ozt
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
            vui__ebm = bodo.libs.array_item_arr_ext.get_offsets(arr._data)
            vui__ebm[ind + 1] = vui__ebm[ind]
            bodo.libs.int_arr_ext.set_bit_to_arr(bodo.libs.
                array_item_arr_ext.get_null_bitmap(arr._data), ind, 0)
        return impl_binary_arr
    if isinstance(arr, bodo.libs.array_item_arr_ext.ArrayItemArrayType):

        def impl_arr_item(arr, ind, int_nan_const=0):
            vui__ebm = bodo.libs.array_item_arr_ext.get_offsets(arr)
            vui__ebm[ind + 1] = vui__ebm[ind]
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
    ziqb__ccamc = arr_tup.count
    tvq__gii = 'def f(arr_tup, ind, int_nan_const=0):\n'
    for i in range(ziqb__ccamc):
        tvq__gii += '  setna(arr_tup[{}], ind, int_nan_const)\n'.format(i)
    tvq__gii += '  return\n'
    emui__evxbh = {}
    exec(tvq__gii, {'setna': setna}, emui__evxbh)
    impl = emui__evxbh['f']
    return impl


def setna_slice(arr, s):
    arr[s] = np.nan


@overload(setna_slice, no_unliteral=True)
def overload_setna_slice(arr, s):

    def impl(arr, s):
        mxso__xlsw = numba.cpython.unicode._normalize_slice(s, len(arr))
        for i in range(mxso__xlsw.start, mxso__xlsw.stop, mxso__xlsw.step):
            setna(arr, i)
    return impl


@numba.generated_jit
def first_last_valid_index(arr, index_arr, is_first=True, parallel=False):
    is_first = get_overload_const_bool(is_first)
    if is_first:
        vhs__hud = 'n'
    else:
        vhs__hud = 'n-1, -1, -1'
    tvq__gii = f"""def impl(arr, index_arr, is_first=True, parallel=False):
    n = len(arr)
    index_val = index_arr[0]
    has_valid = False
    loc_min = -1
    if parallel:
        rank = bodo.libs.distributed_api.get_rank()
        n_pes = bodo.libs.distributed_api.get_size()
        loc_min = n_pes
    for i in range({vhs__hud}):
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
    emui__evxbh = {}
    exec(tvq__gii, {'np': np, 'bodo': bodo, 'isna': isna, 'min_op': min_op,
        'box_if_dt64': bodo.utils.conversion.box_if_dt64}, emui__evxbh)
    impl = emui__evxbh['impl']
    return impl


ll.add_symbol('median_series_computation', quantile_alg.
    median_series_computation)
_median_series_computation = types.ExternalFunction('median_series_computation'
    , types.void(types.voidptr, bodo.libs.array.array_info_type, types.
    bool_, types.bool_))


@numba.njit
def median_series_computation(res, arr, is_parallel, skipna):
    ozt__uggmn = array_to_info(arr)
    _median_series_computation(res, ozt__uggmn, is_parallel, skipna)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(ozt__uggmn)


ll.add_symbol('autocorr_series_computation', quantile_alg.
    autocorr_series_computation)
_autocorr_series_computation = types.ExternalFunction(
    'autocorr_series_computation', types.void(types.voidptr, bodo.libs.
    array.array_info_type, types.int64, types.bool_))


@numba.njit
def autocorr_series_computation(res, arr, lag, is_parallel):
    ozt__uggmn = array_to_info(arr)
    _autocorr_series_computation(res, ozt__uggmn, lag, is_parallel)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(ozt__uggmn)


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
    ozt__uggmn = array_to_info(arr)
    _compute_series_monotonicity(res, ozt__uggmn, inc_dec, is_parallel)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(ozt__uggmn)


@numba.njit
def series_monotonicity(arr, inc_dec, parallel=False):
    res = np.empty(1, types.float64)
    series_monotonicity_call(res.ctypes, arr, inc_dec, parallel)
    pstfk__gpc = res[0] > 0.5
    return pstfk__gpc


@numba.generated_jit(nopython=True)
def get_valid_entries_from_date_offset(index_arr, offset, initial_date,
    is_last, is_parallel=False):
    if get_overload_const_bool(is_last):
        ntl__ssyl = '-'
        btgx__vpo = 'index_arr[0] > threshhold_date'
        vhs__hud = '1, n+1'
        nfhff__lkgzb = 'index_arr[-i] <= threshhold_date'
        nbbr__negt = 'i - 1'
    else:
        ntl__ssyl = '+'
        btgx__vpo = 'index_arr[-1] < threshhold_date'
        vhs__hud = 'n'
        nfhff__lkgzb = 'index_arr[i] >= threshhold_date'
        nbbr__negt = 'i'
    tvq__gii = (
        'def impl(index_arr, offset, initial_date, is_last, is_parallel=False):\n'
        )
    if types.unliteral(offset) == types.unicode_type:
        tvq__gii += (
            '  with numba.objmode(threshhold_date=bodo.pd_timestamp_type):\n')
        tvq__gii += (
            '    date_offset = pd.tseries.frequencies.to_offset(offset)\n')
        if not get_overload_const_bool(is_last):
            tvq__gii += """    if not isinstance(date_offset, pd._libs.tslibs.Tick) and date_offset.is_on_offset(index_arr[0]):
"""
            tvq__gii += (
                '      threshhold_date = initial_date - date_offset.base + date_offset\n'
                )
            tvq__gii += '    else:\n'
            tvq__gii += '      threshhold_date = initial_date + date_offset\n'
        else:
            tvq__gii += (
                f'    threshhold_date = initial_date {ntl__ssyl} date_offset\n'
                )
    else:
        tvq__gii += f'  threshhold_date = initial_date {ntl__ssyl} offset\n'
    tvq__gii += '  local_valid = 0\n'
    tvq__gii += f'  n = len(index_arr)\n'
    tvq__gii += f'  if n:\n'
    tvq__gii += f'    if {btgx__vpo}:\n'
    tvq__gii += '      loc_valid = n\n'
    tvq__gii += '    else:\n'
    tvq__gii += f'      for i in range({vhs__hud}):\n'
    tvq__gii += f'        if {nfhff__lkgzb}:\n'
    tvq__gii += f'          loc_valid = {nbbr__negt}\n'
    tvq__gii += '          break\n'
    tvq__gii += '  if is_parallel:\n'
    tvq__gii += (
        '    total_valid = bodo.libs.distributed_api.dist_reduce(loc_valid, sum_op)\n'
        )
    tvq__gii += '    return total_valid\n'
    tvq__gii += '  else:\n'
    tvq__gii += '    return loc_valid\n'
    emui__evxbh = {}
    exec(tvq__gii, {'bodo': bodo, 'pd': pd, 'numba': numba, 'sum_op':
        sum_op}, emui__evxbh)
    return emui__evxbh['impl']


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
    pcmgh__fdzrk = numba_to_c_type(sig.args[0].dtype)
    rtufh__uxwl = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(32), pcmgh__fdzrk))
    mptv__xzada = args[0]
    fgqhx__fjz = sig.args[0]
    if isinstance(fgqhx__fjz, (IntegerArrayType, BooleanArrayType)):
        mptv__xzada = cgutils.create_struct_proxy(fgqhx__fjz)(context,
            builder, mptv__xzada).data
        fgqhx__fjz = types.Array(fgqhx__fjz.dtype, 1, 'C')
    assert fgqhx__fjz.ndim == 1
    arr = make_array(fgqhx__fjz)(context, builder, mptv__xzada)
    cifde__xwsar = builder.extract_value(arr.shape, 0)
    jmwdo__asj = [builder.bitcast(arr.data, lir.IntType(8).as_pointer()),
        cifde__xwsar, args[1], builder.load(rtufh__uxwl)]
    uehu__luy = [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
        DoubleType(), lir.IntType(32)]
    kxmy__bfya = lir.FunctionType(lir.DoubleType(), uehu__luy)
    avy__riow = cgutils.get_or_insert_function(builder.module, kxmy__bfya,
        name='quantile_sequential')
    regva__edq = builder.call(avy__riow, jmwdo__asj)
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return regva__edq


@lower_builtin(quantile_parallel, types.Array, types.float64, types.intp)
@lower_builtin(quantile_parallel, IntegerArrayType, types.float64, types.intp)
@lower_builtin(quantile_parallel, BooleanArrayType, types.float64, types.intp)
def lower_dist_quantile_parallel(context, builder, sig, args):
    pcmgh__fdzrk = numba_to_c_type(sig.args[0].dtype)
    rtufh__uxwl = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(32), pcmgh__fdzrk))
    mptv__xzada = args[0]
    fgqhx__fjz = sig.args[0]
    if isinstance(fgqhx__fjz, (IntegerArrayType, BooleanArrayType)):
        mptv__xzada = cgutils.create_struct_proxy(fgqhx__fjz)(context,
            builder, mptv__xzada).data
        fgqhx__fjz = types.Array(fgqhx__fjz.dtype, 1, 'C')
    assert fgqhx__fjz.ndim == 1
    arr = make_array(fgqhx__fjz)(context, builder, mptv__xzada)
    cifde__xwsar = builder.extract_value(arr.shape, 0)
    if len(args) == 3:
        izg__ifj = args[2]
    else:
        izg__ifj = cifde__xwsar
    jmwdo__asj = [builder.bitcast(arr.data, lir.IntType(8).as_pointer()),
        cifde__xwsar, izg__ifj, args[1], builder.load(rtufh__uxwl)]
    uehu__luy = [lir.IntType(8).as_pointer(), lir.IntType(64), lir.IntType(
        64), lir.DoubleType(), lir.IntType(32)]
    kxmy__bfya = lir.FunctionType(lir.DoubleType(), uehu__luy)
    avy__riow = cgutils.get_or_insert_function(builder.module, kxmy__bfya,
        name='quantile_parallel')
    regva__edq = builder.call(avy__riow, jmwdo__asj)
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return regva__edq


@numba.njit
def min_heapify(arr, ind_arr, n, start, cmp_f):
    rooz__lroj = start
    jvip__uia = 2 * start + 1
    lbd__kdod = 2 * start + 2
    if jvip__uia < n and not cmp_f(arr[jvip__uia], arr[rooz__lroj]):
        rooz__lroj = jvip__uia
    if lbd__kdod < n and not cmp_f(arr[lbd__kdod], arr[rooz__lroj]):
        rooz__lroj = lbd__kdod
    if rooz__lroj != start:
        arr[start], arr[rooz__lroj] = arr[rooz__lroj], arr[start]
        ind_arr[start], ind_arr[rooz__lroj] = ind_arr[rooz__lroj], ind_arr[
            start]
        min_heapify(arr, ind_arr, n, rooz__lroj, cmp_f)


def select_k_nonan(A, index_arr, m, k):
    return A[:k]


@overload(select_k_nonan, no_unliteral=True)
def select_k_nonan_overload(A, index_arr, m, k):
    dtype = A.dtype
    if isinstance(dtype, types.Integer):
        return lambda A, index_arr, m, k: (A[:k].copy(), index_arr[:k].copy
            (), k)

    def select_k_nonan_float(A, index_arr, m, k):
        fpg__gyue = np.empty(k, A.dtype)
        hdcb__hucc = np.empty(k, index_arr.dtype)
        i = 0
        ind = 0
        while i < m and ind < k:
            if not bodo.libs.array_kernels.isna(A, i):
                fpg__gyue[ind] = A[i]
                hdcb__hucc[ind] = index_arr[i]
                ind += 1
            i += 1
        if ind < k:
            fpg__gyue = fpg__gyue[:ind]
            hdcb__hucc = hdcb__hucc[:ind]
        return fpg__gyue, hdcb__hucc, i
    return select_k_nonan_float


@numba.njit
def nlargest(A, index_arr, k, is_largest, cmp_f):
    m = len(A)
    if k == 0:
        return A[:0], index_arr[:0]
    if k >= m:
        oeh__gdff = np.sort(A)
        rkae__rdsrp = index_arr[np.argsort(A)]
        ayta__nquk = pd.Series(oeh__gdff).notna().values
        oeh__gdff = oeh__gdff[ayta__nquk]
        rkae__rdsrp = rkae__rdsrp[ayta__nquk]
        if is_largest:
            oeh__gdff = oeh__gdff[::-1]
            rkae__rdsrp = rkae__rdsrp[::-1]
        return np.ascontiguousarray(oeh__gdff), np.ascontiguousarray(
            rkae__rdsrp)
    fpg__gyue, hdcb__hucc, start = select_k_nonan(A, index_arr, m, k)
    hdcb__hucc = hdcb__hucc[fpg__gyue.argsort()]
    fpg__gyue.sort()
    if not is_largest:
        fpg__gyue = np.ascontiguousarray(fpg__gyue[::-1])
        hdcb__hucc = np.ascontiguousarray(hdcb__hucc[::-1])
    for i in range(start, m):
        if cmp_f(A[i], fpg__gyue[0]):
            fpg__gyue[0] = A[i]
            hdcb__hucc[0] = index_arr[i]
            min_heapify(fpg__gyue, hdcb__hucc, k, 0, cmp_f)
    hdcb__hucc = hdcb__hucc[fpg__gyue.argsort()]
    fpg__gyue.sort()
    if is_largest:
        fpg__gyue = fpg__gyue[::-1]
        hdcb__hucc = hdcb__hucc[::-1]
    return np.ascontiguousarray(fpg__gyue), np.ascontiguousarray(hdcb__hucc)


@numba.njit
def nlargest_parallel(A, I, k, is_largest, cmp_f):
    zkatf__rbsf = bodo.libs.distributed_api.get_rank()
    npeye__qdu, lei__jhp = nlargest(A, I, k, is_largest, cmp_f)
    okba__pcp = bodo.libs.distributed_api.gatherv(npeye__qdu)
    gsmvm__pwx = bodo.libs.distributed_api.gatherv(lei__jhp)
    if zkatf__rbsf == MPI_ROOT:
        res, elnt__vwllk = nlargest(okba__pcp, gsmvm__pwx, k, is_largest, cmp_f
            )
    else:
        res = np.empty(k, A.dtype)
        elnt__vwllk = np.empty(k, I.dtype)
    bodo.libs.distributed_api.bcast(res)
    bodo.libs.distributed_api.bcast(elnt__vwllk)
    return res, elnt__vwllk


@numba.njit(no_cpython_wrapper=True, cache=True)
def nancorr(mat, cov=0, minpv=1, parallel=False):
    iukz__brg, wxbmx__cinqg = mat.shape
    bbe__jer = np.empty((wxbmx__cinqg, wxbmx__cinqg), dtype=np.float64)
    for sicn__pglzy in range(wxbmx__cinqg):
        for grdo__zlu in range(sicn__pglzy + 1):
            nvwxg__yahbw = 0
            gnrsv__hllde = xlug__ddbha = lqc__qoz = vpnj__hykxz = 0.0
            for i in range(iukz__brg):
                if np.isfinite(mat[i, sicn__pglzy]) and np.isfinite(mat[i,
                    grdo__zlu]):
                    wlxoa__fsfyf = mat[i, sicn__pglzy]
                    rqdt__gpcst = mat[i, grdo__zlu]
                    nvwxg__yahbw += 1
                    lqc__qoz += wlxoa__fsfyf
                    vpnj__hykxz += rqdt__gpcst
            if parallel:
                nvwxg__yahbw = bodo.libs.distributed_api.dist_reduce(
                    nvwxg__yahbw, sum_op)
                lqc__qoz = bodo.libs.distributed_api.dist_reduce(lqc__qoz,
                    sum_op)
                vpnj__hykxz = bodo.libs.distributed_api.dist_reduce(vpnj__hykxz
                    , sum_op)
            if nvwxg__yahbw < minpv:
                bbe__jer[sicn__pglzy, grdo__zlu] = bbe__jer[grdo__zlu,
                    sicn__pglzy] = np.nan
            else:
                geeg__bqrsz = lqc__qoz / nvwxg__yahbw
                ejxw__nmowz = vpnj__hykxz / nvwxg__yahbw
                lqc__qoz = 0.0
                for i in range(iukz__brg):
                    if np.isfinite(mat[i, sicn__pglzy]) and np.isfinite(mat
                        [i, grdo__zlu]):
                        wlxoa__fsfyf = mat[i, sicn__pglzy] - geeg__bqrsz
                        rqdt__gpcst = mat[i, grdo__zlu] - ejxw__nmowz
                        lqc__qoz += wlxoa__fsfyf * rqdt__gpcst
                        gnrsv__hllde += wlxoa__fsfyf * wlxoa__fsfyf
                        xlug__ddbha += rqdt__gpcst * rqdt__gpcst
                if parallel:
                    lqc__qoz = bodo.libs.distributed_api.dist_reduce(lqc__qoz,
                        sum_op)
                    gnrsv__hllde = bodo.libs.distributed_api.dist_reduce(
                        gnrsv__hllde, sum_op)
                    xlug__ddbha = bodo.libs.distributed_api.dist_reduce(
                        xlug__ddbha, sum_op)
                udwx__cio = nvwxg__yahbw - 1.0 if cov else sqrt(
                    gnrsv__hllde * xlug__ddbha)
                if udwx__cio != 0.0:
                    bbe__jer[sicn__pglzy, grdo__zlu] = bbe__jer[grdo__zlu,
                        sicn__pglzy] = lqc__qoz / udwx__cio
                else:
                    bbe__jer[sicn__pglzy, grdo__zlu] = bbe__jer[grdo__zlu,
                        sicn__pglzy] = np.nan
    return bbe__jer


@numba.generated_jit(nopython=True)
def duplicated(data, parallel=False):
    n = len(data)
    if n == 0:
        return lambda data, parallel=False: np.empty(0, dtype=np.bool_)
    uxwdp__gnis = n != 1
    tvq__gii = 'def impl(data, parallel=False):\n'
    tvq__gii += '  if parallel:\n'
    rgud__pisvr = ', '.join(f'array_to_info(data[{i}])' for i in range(n))
    tvq__gii += f'    cpp_table = arr_info_list_to_table([{rgud__pisvr}])\n'
    tvq__gii += (
        f'    out_cpp_table = bodo.libs.array.shuffle_table(cpp_table, {n}, parallel, 1)\n'
        )
    fbnx__ucx = ', '.join(
        f'info_to_array(info_from_table(out_cpp_table, {i}), data[{i}])' for
        i in range(n))
    tvq__gii += f'    data = ({fbnx__ucx},)\n'
    tvq__gii += (
        '    shuffle_info = bodo.libs.array.get_shuffle_info(out_cpp_table)\n')
    tvq__gii += '    bodo.libs.array.delete_table(out_cpp_table)\n'
    tvq__gii += '    bodo.libs.array.delete_table(cpp_table)\n'
    tvq__gii += '  n = len(data[0])\n'
    tvq__gii += '  out = np.empty(n, np.bool_)\n'
    tvq__gii += '  uniqs = dict()\n'
    if uxwdp__gnis:
        tvq__gii += '  for i in range(n):\n'
        upv__hmssq = ', '.join(f'data[{i}][i]' for i in range(n))
        fbqzm__wvv = ',  '.join(
            f'bodo.libs.array_kernels.isna(data[{i}], i)' for i in range(n))
        tvq__gii += f"""    val = bodo.libs.nullable_tuple_ext.build_nullable_tuple(({upv__hmssq},), ({fbqzm__wvv},))
"""
        tvq__gii += '    if val in uniqs:\n'
        tvq__gii += '      out[i] = True\n'
        tvq__gii += '    else:\n'
        tvq__gii += '      out[i] = False\n'
        tvq__gii += '      uniqs[val] = 0\n'
    else:
        tvq__gii += '  data = data[0]\n'
        tvq__gii += '  hasna = False\n'
        tvq__gii += '  for i in range(n):\n'
        tvq__gii += '    if bodo.libs.array_kernels.isna(data, i):\n'
        tvq__gii += '      out[i] = hasna\n'
        tvq__gii += '      hasna = True\n'
        tvq__gii += '    else:\n'
        tvq__gii += '      val = data[i]\n'
        tvq__gii += '      if val in uniqs:\n'
        tvq__gii += '        out[i] = True\n'
        tvq__gii += '      else:\n'
        tvq__gii += '        out[i] = False\n'
        tvq__gii += '        uniqs[val] = 0\n'
    tvq__gii += '  if parallel:\n'
    tvq__gii += (
        '    out = bodo.hiframes.pd_groupby_ext.reverse_shuffle(out, shuffle_info)\n'
        )
    tvq__gii += '  return out\n'
    emui__evxbh = {}
    exec(tvq__gii, {'bodo': bodo, 'np': np, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'info_to_array':
        info_to_array, 'info_from_table': info_from_table}, emui__evxbh)
    impl = emui__evxbh['impl']
    return impl


def sample_table_operation(data, ind_arr, n, frac, replace, parallel=False):
    return data, ind_arr


@overload(sample_table_operation, no_unliteral=True)
def overload_sample_table_operation(data, ind_arr, n, frac, replace,
    parallel=False):
    ziqb__ccamc = len(data)
    tvq__gii = 'def impl(data, ind_arr, n, frac, replace, parallel=False):\n'
    tvq__gii += '  info_list_total = [{}, array_to_info(ind_arr)]\n'.format(
        ', '.join('array_to_info(data[{}])'.format(x) for x in range(
        ziqb__ccamc)))
    tvq__gii += '  table_total = arr_info_list_to_table(info_list_total)\n'
    tvq__gii += (
        '  out_table = sample_table(table_total, n, frac, replace, parallel)\n'
        .format(ziqb__ccamc))
    for aay__wndl in range(ziqb__ccamc):
        tvq__gii += (
            '  out_arr_{} = info_to_array(info_from_table(out_table, {}), data[{}])\n'
            .format(aay__wndl, aay__wndl, aay__wndl))
    tvq__gii += (
        '  out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)\n'
        .format(ziqb__ccamc))
    tvq__gii += '  delete_table(out_table)\n'
    tvq__gii += '  delete_table(table_total)\n'
    tvq__gii += '  return ({},), out_arr_index\n'.format(', '.join(
        'out_arr_{}'.format(i) for i in range(ziqb__ccamc)))
    emui__evxbh = {}
    exec(tvq__gii, {'np': np, 'bodo': bodo, 'array_to_info': array_to_info,
        'sample_table': sample_table, 'arr_info_list_to_table':
        arr_info_list_to_table, 'info_from_table': info_from_table,
        'info_to_array': info_to_array, 'delete_table': delete_table,
        'delete_table_decref_arrays': delete_table_decref_arrays}, emui__evxbh)
    impl = emui__evxbh['impl']
    return impl


def drop_duplicates(data, ind_arr, ncols, parallel=False):
    return data, ind_arr


@overload(drop_duplicates, no_unliteral=True)
def overload_drop_duplicates(data, ind_arr, ncols, parallel=False):
    ziqb__ccamc = len(data)
    tvq__gii = 'def impl(data, ind_arr, ncols, parallel=False):\n'
    tvq__gii += '  info_list_total = [{}, array_to_info(ind_arr)]\n'.format(
        ', '.join('array_to_info(data[{}])'.format(x) for x in range(
        ziqb__ccamc)))
    tvq__gii += '  table_total = arr_info_list_to_table(info_list_total)\n'
    tvq__gii += '  keep_i = 0\n'
    tvq__gii += """  out_table = drop_duplicates_table(table_total, parallel, ncols, keep_i, False, True)
"""
    for aay__wndl in range(ziqb__ccamc):
        tvq__gii += (
            '  out_arr_{} = info_to_array(info_from_table(out_table, {}), data[{}])\n'
            .format(aay__wndl, aay__wndl, aay__wndl))
    tvq__gii += (
        '  out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)\n'
        .format(ziqb__ccamc))
    tvq__gii += '  delete_table(out_table)\n'
    tvq__gii += '  delete_table(table_total)\n'
    tvq__gii += '  return ({},), out_arr_index\n'.format(', '.join(
        'out_arr_{}'.format(i) for i in range(ziqb__ccamc)))
    emui__evxbh = {}
    exec(tvq__gii, {'np': np, 'bodo': bodo, 'array_to_info': array_to_info,
        'drop_duplicates_table': drop_duplicates_table,
        'arr_info_list_to_table': arr_info_list_to_table, 'info_from_table':
        info_from_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays}, emui__evxbh)
    impl = emui__evxbh['impl']
    return impl


def drop_duplicates_array(data_arr, parallel=False):
    return data_arr


@overload(drop_duplicates_array, no_unliteral=True)
def overload_drop_duplicates_array(data_arr, parallel=False):

    def impl(data_arr, parallel=False):
        jly__nlck = [array_to_info(data_arr)]
        dmrnd__wna = arr_info_list_to_table(jly__nlck)
        tthc__ojfd = 0
        pgugv__xmand = drop_duplicates_table(dmrnd__wna, parallel, 1,
            tthc__ojfd, False, True)
        roev__djw = info_to_array(info_from_table(pgugv__xmand, 0), data_arr)
        delete_table(pgugv__xmand)
        delete_table(dmrnd__wna)
        return roev__djw
    return impl


def dropna(data, how, thresh, subset, parallel=False):
    return data


@overload(dropna, no_unliteral=True)
def overload_dropna(data, how, thresh, subset):
    ssck__axj = len(data.types)
    bmx__wjz = [('out' + str(i)) for i in range(ssck__axj)]
    whzpm__kjf = get_overload_const_list(subset)
    how = get_overload_const_str(how)
    cqidm__aye = ['isna(data[{}], i)'.format(i) for i in whzpm__kjf]
    oxszx__ygvy = 'not ({})'.format(' or '.join(cqidm__aye))
    if not is_overload_none(thresh):
        oxszx__ygvy = '(({}) <= ({}) - thresh)'.format(' + '.join(
            cqidm__aye), ssck__axj - 1)
    elif how == 'all':
        oxszx__ygvy = 'not ({})'.format(' and '.join(cqidm__aye))
    tvq__gii = 'def _dropna_imp(data, how, thresh, subset):\n'
    tvq__gii += '  old_len = len(data[0])\n'
    tvq__gii += '  new_len = 0\n'
    tvq__gii += '  for i in range(old_len):\n'
    tvq__gii += '    if {}:\n'.format(oxszx__ygvy)
    tvq__gii += '      new_len += 1\n'
    for i, out in enumerate(bmx__wjz):
        if isinstance(data[i], bodo.CategoricalArrayType):
            tvq__gii += (
                '  {0} = bodo.utils.utils.alloc_type(new_len, data[{1}], (-1,))\n'
                .format(out, i))
        else:
            tvq__gii += (
                '  {0} = bodo.utils.utils.alloc_type(new_len, t{1}, (-1,))\n'
                .format(out, i))
    tvq__gii += '  curr_ind = 0\n'
    tvq__gii += '  for i in range(old_len):\n'
    tvq__gii += '    if {}:\n'.format(oxszx__ygvy)
    for i in range(ssck__axj):
        tvq__gii += '      if isna(data[{}], i):\n'.format(i)
        tvq__gii += '        setna({}, curr_ind)\n'.format(bmx__wjz[i])
        tvq__gii += '      else:\n'
        tvq__gii += '        {}[curr_ind] = data[{}][i]\n'.format(bmx__wjz[
            i], i)
    tvq__gii += '      curr_ind += 1\n'
    tvq__gii += '  return {}\n'.format(', '.join(bmx__wjz))
    emui__evxbh = {}
    ixlb__pbvb = {'t{}'.format(i): exas__jkxal for i, exas__jkxal in
        enumerate(data.types)}
    ixlb__pbvb.update({'isna': isna, 'setna': setna, 'init_nested_counts':
        bodo.utils.indexing.init_nested_counts, 'add_nested_counts': bodo.
        utils.indexing.add_nested_counts, 'bodo': bodo})
    exec(tvq__gii, ixlb__pbvb, emui__evxbh)
    opuw__padh = emui__evxbh['_dropna_imp']
    return opuw__padh


def get(arr, ind):
    return pd.Series(arr).str.get(ind)


@overload(get, no_unliteral=True)
def overload_get(arr, ind):
    if isinstance(arr, ArrayItemArrayType):
        fgqhx__fjz = arr.dtype
        pche__tti = fgqhx__fjz.dtype

        def get_arr_item(arr, ind):
            n = len(arr)
            txref__mfe = init_nested_counts(pche__tti)
            for k in range(n):
                if bodo.libs.array_kernels.isna(arr, k):
                    continue
                val = arr[k]
                if not len(val) > ind >= -len(val
                    ) or bodo.libs.array_kernels.isna(val, ind):
                    continue
                txref__mfe = add_nested_counts(txref__mfe, val[ind])
            roev__djw = bodo.utils.utils.alloc_type(n, fgqhx__fjz, txref__mfe)
            for fejrh__bnz in range(n):
                if bodo.libs.array_kernels.isna(arr, fejrh__bnz):
                    setna(roev__djw, fejrh__bnz)
                    continue
                val = arr[fejrh__bnz]
                if not len(val) > ind >= -len(val
                    ) or bodo.libs.array_kernels.isna(val, ind):
                    setna(roev__djw, fejrh__bnz)
                    continue
                roev__djw[fejrh__bnz] = val[ind]
            return roev__djw
        return get_arr_item


def _is_same_categorical_array_type(arr_types):
    from bodo.hiframes.pd_categorical_ext import _to_readonly
    if not isinstance(arr_types, types.BaseTuple) or len(arr_types) == 0:
        return False
    bth__lfl = _to_readonly(arr_types.types[0])
    return all(isinstance(exas__jkxal, CategoricalArrayType) and 
        _to_readonly(exas__jkxal) == bth__lfl for exas__jkxal in arr_types.
        types)


def concat(arr_list):
    return pd.concat(arr_list)


@overload(concat, no_unliteral=True)
def concat_overload(arr_list):
    if isinstance(arr_list, bodo.NullableTupleType):
        return lambda arr_list: bodo.libs.array_kernels.concat(arr_list._data)
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, ArrayItemArrayType):
        ouk__epf = arr_list.dtype.dtype

        def array_item_concat_impl(arr_list):
            dzfr__scuj = 0
            xjbw__qcvev = []
            for A in arr_list:
                ihf__riyr = len(A)
                bodo.libs.array_item_arr_ext.trim_excess_data(A)
                xjbw__qcvev.append(bodo.libs.array_item_arr_ext.get_data(A))
                dzfr__scuj += ihf__riyr
            esfvb__tdf = np.empty(dzfr__scuj + 1, offset_type)
            iaqd__wrdo = bodo.libs.array_kernels.concat(xjbw__qcvev)
            rjxb__snx = np.empty(dzfr__scuj + 7 >> 3, np.uint8)
            rzq__thr = 0
            qqhl__wwnik = 0
            for A in arr_list:
                ybk__pllz = bodo.libs.array_item_arr_ext.get_offsets(A)
                dva__hufog = bodo.libs.array_item_arr_ext.get_null_bitmap(A)
                ihf__riyr = len(A)
                ret__dss = ybk__pllz[ihf__riyr]
                for i in range(ihf__riyr):
                    esfvb__tdf[i + rzq__thr] = ybk__pllz[i] + qqhl__wwnik
                    pcuua__odkum = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        dva__hufog, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(rjxb__snx, i +
                        rzq__thr, pcuua__odkum)
                rzq__thr += ihf__riyr
                qqhl__wwnik += ret__dss
            esfvb__tdf[rzq__thr] = qqhl__wwnik
            roev__djw = bodo.libs.array_item_arr_ext.init_array_item_array(
                dzfr__scuj, iaqd__wrdo, esfvb__tdf, rjxb__snx)
            return roev__djw
        return array_item_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, bodo.StructArrayType):
        njrt__xtfe = arr_list.dtype.names
        tvq__gii = 'def struct_array_concat_impl(arr_list):\n'
        tvq__gii += f'    n_all = 0\n'
        for i in range(len(njrt__xtfe)):
            tvq__gii += f'    concat_list{i} = []\n'
        tvq__gii += '    for A in arr_list:\n'
        tvq__gii += (
            '        data_tuple = bodo.libs.struct_arr_ext.get_data(A)\n')
        for i in range(len(njrt__xtfe)):
            tvq__gii += f'        concat_list{i}.append(data_tuple[{i}])\n'
        tvq__gii += '        n_all += len(A)\n'
        tvq__gii += '    n_bytes = (n_all + 7) >> 3\n'
        tvq__gii += '    new_mask = np.empty(n_bytes, np.uint8)\n'
        tvq__gii += '    curr_bit = 0\n'
        tvq__gii += '    for A in arr_list:\n'
        tvq__gii += (
            '        old_mask = bodo.libs.struct_arr_ext.get_null_bitmap(A)\n')
        tvq__gii += '        for j in range(len(A)):\n'
        tvq__gii += (
            '            bit = bodo.libs.int_arr_ext.get_bit_bitmap_arr(old_mask, j)\n'
            )
        tvq__gii += (
            '            bodo.libs.int_arr_ext.set_bit_to_arr(new_mask, curr_bit, bit)\n'
            )
        tvq__gii += '            curr_bit += 1\n'
        tvq__gii += '    return bodo.libs.struct_arr_ext.init_struct_arr(\n'
        cwtr__wlkgz = ', '.join([
            f'bodo.libs.array_kernels.concat(concat_list{i})' for i in
            range(len(njrt__xtfe))])
        tvq__gii += f'        ({cwtr__wlkgz},),\n'
        tvq__gii += '        new_mask,\n'
        tvq__gii += f'        {njrt__xtfe},\n'
        tvq__gii += '    )\n'
        emui__evxbh = {}
        exec(tvq__gii, {'bodo': bodo, 'np': np}, emui__evxbh)
        return emui__evxbh['struct_array_concat_impl']
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == datetime_date_array_type:

        def datetime_date_array_concat_impl(arr_list):
            suh__fka = 0
            for A in arr_list:
                suh__fka += len(A)
            idtqh__qhb = (bodo.hiframes.datetime_date_ext.
                alloc_datetime_date_array(suh__fka))
            xrumr__urgwg = 0
            for A in arr_list:
                for i in range(len(A)):
                    idtqh__qhb._data[i + xrumr__urgwg] = A._data[i]
                    pcuua__odkum = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(idtqh__qhb.
                        _null_bitmap, i + xrumr__urgwg, pcuua__odkum)
                xrumr__urgwg += len(A)
            return idtqh__qhb
        return datetime_date_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == datetime_timedelta_array_type:

        def datetime_timedelta_array_concat_impl(arr_list):
            suh__fka = 0
            for A in arr_list:
                suh__fka += len(A)
            idtqh__qhb = (bodo.hiframes.datetime_timedelta_ext.
                alloc_datetime_timedelta_array(suh__fka))
            xrumr__urgwg = 0
            for A in arr_list:
                for i in range(len(A)):
                    idtqh__qhb._days_data[i + xrumr__urgwg] = A._days_data[i]
                    idtqh__qhb._seconds_data[i + xrumr__urgwg
                        ] = A._seconds_data[i]
                    idtqh__qhb._microseconds_data[i + xrumr__urgwg
                        ] = A._microseconds_data[i]
                    pcuua__odkum = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(idtqh__qhb.
                        _null_bitmap, i + xrumr__urgwg, pcuua__odkum)
                xrumr__urgwg += len(A)
            return idtqh__qhb
        return datetime_timedelta_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, DecimalArrayType):
        xsbr__fejq = arr_list.dtype.precision
        nute__zwh = arr_list.dtype.scale

        def decimal_array_concat_impl(arr_list):
            suh__fka = 0
            for A in arr_list:
                suh__fka += len(A)
            idtqh__qhb = bodo.libs.decimal_arr_ext.alloc_decimal_array(suh__fka
                , xsbr__fejq, nute__zwh)
            xrumr__urgwg = 0
            for A in arr_list:
                for i in range(len(A)):
                    idtqh__qhb._data[i + xrumr__urgwg] = A._data[i]
                    pcuua__odkum = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(idtqh__qhb.
                        _null_bitmap, i + xrumr__urgwg, pcuua__odkum)
                xrumr__urgwg += len(A)
            return idtqh__qhb
        return decimal_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and (is_str_arr_type
        (arr_list.dtype) or arr_list.dtype == bodo.binary_array_type
        ) or isinstance(arr_list, types.BaseTuple) and all(is_str_arr_type(
        exas__jkxal) for exas__jkxal in arr_list.types):
        if isinstance(arr_list, types.BaseTuple):
            fzdhk__gegxy = arr_list.types[0]
        else:
            fzdhk__gegxy = arr_list.dtype
        fzdhk__gegxy = to_str_arr_if_dict_array(fzdhk__gegxy)

        def impl_str(arr_list):
            arr_list = decode_if_dict_array(arr_list)
            rbe__cdkt = 0
            qdk__kjofw = 0
            for A in arr_list:
                arr = A
                rbe__cdkt += len(arr)
                qdk__kjofw += bodo.libs.str_arr_ext.num_total_chars(arr)
            roev__djw = bodo.utils.utils.alloc_type(rbe__cdkt, fzdhk__gegxy,
                (qdk__kjofw,))
            bodo.libs.str_arr_ext.set_null_bits_to_value(roev__djw, -1)
            lubwh__smw = 0
            kykr__imv = 0
            for A in arr_list:
                arr = A
                bodo.libs.str_arr_ext.set_string_array_range(roev__djw, arr,
                    lubwh__smw, kykr__imv)
                lubwh__smw += len(arr)
                kykr__imv += bodo.libs.str_arr_ext.num_total_chars(arr)
            return roev__djw
        return impl_str
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, IntegerArrayType) or isinstance(arr_list, types.
        BaseTuple) and all(isinstance(exas__jkxal.dtype, types.Integer) for
        exas__jkxal in arr_list.types) and any(isinstance(exas__jkxal,
        IntegerArrayType) for exas__jkxal in arr_list.types):

        def impl_int_arr_list(arr_list):
            nblxw__ubt = convert_to_nullable_tup(arr_list)
            oirpt__fyuk = []
            flxc__mlcm = 0
            for A in nblxw__ubt:
                oirpt__fyuk.append(A._data)
                flxc__mlcm += len(A)
            iaqd__wrdo = bodo.libs.array_kernels.concat(oirpt__fyuk)
            toifm__zzce = flxc__mlcm + 7 >> 3
            tvxxn__qxox = np.empty(toifm__zzce, np.uint8)
            iptc__nrtx = 0
            for A in nblxw__ubt:
                dyqca__lbocb = A._null_bitmap
                for fejrh__bnz in range(len(A)):
                    pcuua__odkum = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        dyqca__lbocb, fejrh__bnz)
                    bodo.libs.int_arr_ext.set_bit_to_arr(tvxxn__qxox,
                        iptc__nrtx, pcuua__odkum)
                    iptc__nrtx += 1
            return bodo.libs.int_arr_ext.init_integer_array(iaqd__wrdo,
                tvxxn__qxox)
        return impl_int_arr_list
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == boolean_array or isinstance(arr_list, types
        .BaseTuple) and all(exas__jkxal.dtype == types.bool_ for
        exas__jkxal in arr_list.types) and any(exas__jkxal == boolean_array for
        exas__jkxal in arr_list.types):

        def impl_bool_arr_list(arr_list):
            nblxw__ubt = convert_to_nullable_tup(arr_list)
            oirpt__fyuk = []
            flxc__mlcm = 0
            for A in nblxw__ubt:
                oirpt__fyuk.append(A._data)
                flxc__mlcm += len(A)
            iaqd__wrdo = bodo.libs.array_kernels.concat(oirpt__fyuk)
            toifm__zzce = flxc__mlcm + 7 >> 3
            tvxxn__qxox = np.empty(toifm__zzce, np.uint8)
            iptc__nrtx = 0
            for A in nblxw__ubt:
                dyqca__lbocb = A._null_bitmap
                for fejrh__bnz in range(len(A)):
                    pcuua__odkum = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        dyqca__lbocb, fejrh__bnz)
                    bodo.libs.int_arr_ext.set_bit_to_arr(tvxxn__qxox,
                        iptc__nrtx, pcuua__odkum)
                    iptc__nrtx += 1
            return bodo.libs.bool_arr_ext.init_bool_array(iaqd__wrdo,
                tvxxn__qxox)
        return impl_bool_arr_list
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, CategoricalArrayType):

        def cat_array_concat_impl(arr_list):
            qxv__hwvnm = []
            for A in arr_list:
                qxv__hwvnm.append(A.codes)
            return init_categorical_array(bodo.libs.array_kernels.concat(
                qxv__hwvnm), arr_list[0].dtype)
        return cat_array_concat_impl
    if _is_same_categorical_array_type(arr_list):
        nje__dkfkp = ', '.join(f'arr_list[{i}].codes' for i in range(len(
            arr_list)))
        tvq__gii = 'def impl(arr_list):\n'
        tvq__gii += f"""    return init_categorical_array(bodo.libs.array_kernels.concat(({nje__dkfkp},)), arr_list[0].dtype)
"""
        dqykk__fwp = {}
        exec(tvq__gii, {'bodo': bodo, 'init_categorical_array':
            init_categorical_array}, dqykk__fwp)
        return dqykk__fwp['impl']
    if isinstance(arr_list, types.List) and isinstance(arr_list.dtype,
        types.Array) and arr_list.dtype.ndim == 1:
        dtype = arr_list.dtype.dtype

        def impl_np_arr_list(arr_list):
            flxc__mlcm = 0
            for A in arr_list:
                flxc__mlcm += len(A)
            roev__djw = np.empty(flxc__mlcm, dtype)
            axwmh__khtz = 0
            for A in arr_list:
                n = len(A)
                roev__djw[axwmh__khtz:axwmh__khtz + n] = A
                axwmh__khtz += n
            return roev__djw
        return impl_np_arr_list
    if isinstance(arr_list, types.BaseTuple) and any(isinstance(exas__jkxal,
        (types.Array, IntegerArrayType)) and isinstance(exas__jkxal.dtype,
        types.Integer) for exas__jkxal in arr_list.types) and any(
        isinstance(exas__jkxal, types.Array) and isinstance(exas__jkxal.
        dtype, types.Float) for exas__jkxal in arr_list.types):
        return lambda arr_list: np.concatenate(astype_float_tup(arr_list))
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, bodo.MapArrayType):

        def impl_map_arr_list(arr_list):
            algnm__tiwt = []
            for A in arr_list:
                algnm__tiwt.append(A._data)
            ehqs__dgz = bodo.libs.array_kernels.concat(algnm__tiwt)
            bbe__jer = bodo.libs.map_arr_ext.init_map_arr(ehqs__dgz)
            return bbe__jer
        return impl_map_arr_list
    for pvpo__gokku in arr_list:
        if not isinstance(pvpo__gokku, types.Array):
            raise_bodo_error(f'concat of array types {arr_list} not supported')
    return lambda arr_list: np.concatenate(arr_list)


def astype_float_tup(arr_tup):
    return tuple(exas__jkxal.astype(np.float64) for exas__jkxal in arr_tup)


@overload(astype_float_tup, no_unliteral=True)
def overload_astype_float_tup(arr_tup):
    assert isinstance(arr_tup, types.BaseTuple)
    ziqb__ccamc = len(arr_tup.types)
    tvq__gii = 'def f(arr_tup):\n'
    tvq__gii += '  return ({}{})\n'.format(','.join(
        'arr_tup[{}].astype(np.float64)'.format(i) for i in range(
        ziqb__ccamc)), ',' if ziqb__ccamc == 1 else '')
    emui__evxbh = {}
    exec(tvq__gii, {'np': np}, emui__evxbh)
    bigg__tmlsp = emui__evxbh['f']
    return bigg__tmlsp


def convert_to_nullable_tup(arr_tup):
    return arr_tup


@overload(convert_to_nullable_tup, no_unliteral=True)
def overload_convert_to_nullable_tup(arr_tup):
    if isinstance(arr_tup, (types.UniTuple, types.List)) and isinstance(arr_tup
        .dtype, (IntegerArrayType, BooleanArrayType)):
        return lambda arr_tup: arr_tup
    assert isinstance(arr_tup, types.BaseTuple)
    ziqb__ccamc = len(arr_tup.types)
    ftv__orci = find_common_np_dtype(arr_tup.types)
    pche__tti = None
    fbbh__fiii = ''
    if isinstance(ftv__orci, types.Integer):
        pche__tti = bodo.libs.int_arr_ext.IntDtype(ftv__orci)
        fbbh__fiii = '.astype(out_dtype, False)'
    tvq__gii = 'def f(arr_tup):\n'
    tvq__gii += '  return ({}{})\n'.format(','.join(
        'bodo.utils.conversion.coerce_to_array(arr_tup[{}], use_nullable_array=True){}'
        .format(i, fbbh__fiii) for i in range(ziqb__ccamc)), ',' if 
        ziqb__ccamc == 1 else '')
    emui__evxbh = {}
    exec(tvq__gii, {'bodo': bodo, 'out_dtype': pche__tti}, emui__evxbh)
    wrhit__spn = emui__evxbh['f']
    return wrhit__spn


def nunique(A, dropna):
    return len(set(A))


def nunique_parallel(A, dropna):
    return len(set(A))


@overload(nunique, no_unliteral=True)
def nunique_overload(A, dropna):

    def nunique_seq(A, dropna):
        s, xcei__chf = build_set_seen_na(A)
        return len(s) + int(not dropna and xcei__chf)
    return nunique_seq


@overload(nunique_parallel, no_unliteral=True)
def nunique_overload_parallel(A, dropna):
    sum_op = bodo.libs.distributed_api.Reduce_Type.Sum.value

    def nunique_par(A, dropna):
        xiktd__bbqfj = bodo.libs.array_kernels.unique(A, dropna, parallel=True)
        exh__nnwu = len(xiktd__bbqfj)
        return bodo.libs.distributed_api.dist_reduce(exh__nnwu, np.int32(
            sum_op))
    return nunique_par


def unique(A, dropna=False, parallel=False):
    return np.array([kunwt__jzl for kunwt__jzl in set(A)]).astype(A.dtype)


def cummin(A):
    return A


@overload(cummin, no_unliteral=True)
def cummin_overload(A):
    if isinstance(A.dtype, types.Float):
        nydaz__yjw = np.finfo(A.dtype(1).dtype).max
    else:
        nydaz__yjw = np.iinfo(A.dtype(1).dtype).max

    def impl(A):
        n = len(A)
        roev__djw = np.empty(n, A.dtype)
        tzi__vsz = nydaz__yjw
        for i in range(n):
            tzi__vsz = min(tzi__vsz, A[i])
            roev__djw[i] = tzi__vsz
        return roev__djw
    return impl


def cummax(A):
    return A


@overload(cummax, no_unliteral=True)
def cummax_overload(A):
    if isinstance(A.dtype, types.Float):
        nydaz__yjw = np.finfo(A.dtype(1).dtype).min
    else:
        nydaz__yjw = np.iinfo(A.dtype(1).dtype).min

    def impl(A):
        n = len(A)
        roev__djw = np.empty(n, A.dtype)
        tzi__vsz = nydaz__yjw
        for i in range(n):
            tzi__vsz = max(tzi__vsz, A[i])
            roev__djw[i] = tzi__vsz
        return roev__djw
    return impl


@overload(unique, no_unliteral=True)
def unique_overload(A, dropna=False, parallel=False):

    def unique_impl(A, dropna=False, parallel=False):
        bgtm__dls = arr_info_list_to_table([array_to_info(A)])
        knq__yeo = 1
        tthc__ojfd = 0
        pgugv__xmand = drop_duplicates_table(bgtm__dls, parallel, knq__yeo,
            tthc__ojfd, dropna, True)
        roev__djw = info_to_array(info_from_table(pgugv__xmand, 0), A)
        delete_table(bgtm__dls)
        delete_table(pgugv__xmand)
        return roev__djw
    return unique_impl


def explode(arr, index_arr):
    return pd.Series(arr, index_arr).explode()


@overload(explode, no_unliteral=True)
def overload_explode(arr, index_arr):
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type
    ouk__epf = bodo.utils.typing.to_nullable_type(arr.dtype)
    qdnkn__yjgf = index_arr
    aro__wcz = qdnkn__yjgf.dtype

    def impl(arr, index_arr):
        n = len(arr)
        txref__mfe = init_nested_counts(ouk__epf)
        wxzwk__thx = init_nested_counts(aro__wcz)
        for i in range(n):
            vkte__hwam = index_arr[i]
            if isna(arr, i):
                txref__mfe = (txref__mfe[0] + 1,) + txref__mfe[1:]
                wxzwk__thx = add_nested_counts(wxzwk__thx, vkte__hwam)
                continue
            tywdk__eujus = arr[i]
            if len(tywdk__eujus) == 0:
                txref__mfe = (txref__mfe[0] + 1,) + txref__mfe[1:]
                wxzwk__thx = add_nested_counts(wxzwk__thx, vkte__hwam)
                continue
            txref__mfe = add_nested_counts(txref__mfe, tywdk__eujus)
            for foqwd__kbkbb in range(len(tywdk__eujus)):
                wxzwk__thx = add_nested_counts(wxzwk__thx, vkte__hwam)
        roev__djw = bodo.utils.utils.alloc_type(txref__mfe[0], ouk__epf,
            txref__mfe[1:])
        puyf__elh = bodo.utils.utils.alloc_type(txref__mfe[0], qdnkn__yjgf,
            wxzwk__thx)
        qqhl__wwnik = 0
        for i in range(n):
            if isna(arr, i):
                setna(roev__djw, qqhl__wwnik)
                puyf__elh[qqhl__wwnik] = index_arr[i]
                qqhl__wwnik += 1
                continue
            tywdk__eujus = arr[i]
            ret__dss = len(tywdk__eujus)
            if ret__dss == 0:
                setna(roev__djw, qqhl__wwnik)
                puyf__elh[qqhl__wwnik] = index_arr[i]
                qqhl__wwnik += 1
                continue
            roev__djw[qqhl__wwnik:qqhl__wwnik + ret__dss] = tywdk__eujus
            puyf__elh[qqhl__wwnik:qqhl__wwnik + ret__dss] = index_arr[i]
            qqhl__wwnik += ret__dss
        return roev__djw, puyf__elh
    return impl


def explode_no_index(arr):
    return pd.Series(arr).explode()


@overload(explode_no_index, no_unliteral=True)
def overload_explode_no_index(arr, counts):
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type
    ouk__epf = bodo.utils.typing.to_nullable_type(arr.dtype)

    def impl(arr, counts):
        n = len(arr)
        txref__mfe = init_nested_counts(ouk__epf)
        for i in range(n):
            if isna(arr, i):
                txref__mfe = (txref__mfe[0] + 1,) + txref__mfe[1:]
                eayli__wvxl = 1
            else:
                tywdk__eujus = arr[i]
                mwpw__whcy = len(tywdk__eujus)
                if mwpw__whcy == 0:
                    txref__mfe = (txref__mfe[0] + 1,) + txref__mfe[1:]
                    eayli__wvxl = 1
                    continue
                else:
                    txref__mfe = add_nested_counts(txref__mfe, tywdk__eujus)
                    eayli__wvxl = mwpw__whcy
            if counts[i] != eayli__wvxl:
                raise ValueError(
                    'DataFrame.explode(): columns must have matching element counts'
                    )
        roev__djw = bodo.utils.utils.alloc_type(txref__mfe[0], ouk__epf,
            txref__mfe[1:])
        qqhl__wwnik = 0
        for i in range(n):
            if isna(arr, i):
                setna(roev__djw, qqhl__wwnik)
                qqhl__wwnik += 1
                continue
            tywdk__eujus = arr[i]
            ret__dss = len(tywdk__eujus)
            if ret__dss == 0:
                setna(roev__djw, qqhl__wwnik)
                qqhl__wwnik += 1
                continue
            roev__djw[qqhl__wwnik:qqhl__wwnik + ret__dss] = tywdk__eujus
            qqhl__wwnik += ret__dss
        return roev__djw
    return impl


def get_arr_lens(arr, na_empty_as_one=True):
    return [len(qhy__mtvu) for qhy__mtvu in arr]


@overload(get_arr_lens, inline='always', no_unliteral=True)
def overload_get_arr_lens(arr, na_empty_as_one=True):
    na_empty_as_one = get_overload_const_bool(na_empty_as_one)
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type or is_str_arr_type(arr
        ) and not na_empty_as_one, f'get_arr_lens: invalid input array type {arr}'
    if na_empty_as_one:
        cyxw__gufz = 'np.empty(n, np.int64)'
        dmq__jkn = 'out_arr[i] = 1'
        muom__zepm = 'max(len(arr[i]), 1)'
    else:
        cyxw__gufz = 'bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)'
        dmq__jkn = 'bodo.libs.array_kernels.setna(out_arr, i)'
        muom__zepm = 'len(arr[i])'
    tvq__gii = f"""def impl(arr, na_empty_as_one=True):
    numba.parfors.parfor.init_prange()
    n = len(arr)
    out_arr = {cyxw__gufz}
    for i in numba.parfors.parfor.internal_prange(n):
        if bodo.libs.array_kernels.isna(arr, i):
            {dmq__jkn}
        else:
            out_arr[i] = {muom__zepm}
    return out_arr
    """
    emui__evxbh = {}
    exec(tvq__gii, {'bodo': bodo, 'numba': numba, 'np': np}, emui__evxbh)
    impl = emui__evxbh['impl']
    return impl


def explode_str_split(arr, pat, n, index_arr):
    return pd.Series(arr, index_arr).str.split(pat, n).explode()


@overload(explode_str_split, no_unliteral=True)
def overload_explode_str_split(arr, pat, n, index_arr):
    assert is_str_arr_type(arr
        ), f'explode_str_split: string array expected, not {arr}'
    qdnkn__yjgf = index_arr
    aro__wcz = qdnkn__yjgf.dtype

    def impl(arr, pat, n, index_arr):
        bjta__moi = pat is not None and len(pat) > 1
        if bjta__moi:
            aoxyp__pno = re.compile(pat)
            if n == -1:
                n = 0
        elif n == 0:
            n = -1
        rrq__jniu = len(arr)
        rbe__cdkt = 0
        qdk__kjofw = 0
        wxzwk__thx = init_nested_counts(aro__wcz)
        for i in range(rrq__jniu):
            vkte__hwam = index_arr[i]
            if bodo.libs.array_kernels.isna(arr, i):
                rbe__cdkt += 1
                wxzwk__thx = add_nested_counts(wxzwk__thx, vkte__hwam)
                continue
            if bjta__moi:
                tlwdi__orpa = aoxyp__pno.split(arr[i], maxsplit=n)
            else:
                tlwdi__orpa = arr[i].split(pat, n)
            rbe__cdkt += len(tlwdi__orpa)
            for s in tlwdi__orpa:
                wxzwk__thx = add_nested_counts(wxzwk__thx, vkte__hwam)
                qdk__kjofw += bodo.libs.str_arr_ext.get_utf8_size(s)
        roev__djw = bodo.libs.str_arr_ext.pre_alloc_string_array(rbe__cdkt,
            qdk__kjofw)
        puyf__elh = bodo.utils.utils.alloc_type(rbe__cdkt, qdnkn__yjgf,
            wxzwk__thx)
        kay__pzy = 0
        for fejrh__bnz in range(rrq__jniu):
            if isna(arr, fejrh__bnz):
                roev__djw[kay__pzy] = ''
                bodo.libs.array_kernels.setna(roev__djw, kay__pzy)
                puyf__elh[kay__pzy] = index_arr[fejrh__bnz]
                kay__pzy += 1
                continue
            if bjta__moi:
                tlwdi__orpa = aoxyp__pno.split(arr[fejrh__bnz], maxsplit=n)
            else:
                tlwdi__orpa = arr[fejrh__bnz].split(pat, n)
            hlsi__thnu = len(tlwdi__orpa)
            roev__djw[kay__pzy:kay__pzy + hlsi__thnu] = tlwdi__orpa
            puyf__elh[kay__pzy:kay__pzy + hlsi__thnu] = index_arr[fejrh__bnz]
            kay__pzy += hlsi__thnu
        return roev__djw, puyf__elh
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
            roev__djw = np.empty(n, dtype)
            for i in numba.parfors.parfor.internal_prange(n):
                roev__djw[i] = np.nan
            return roev__djw
        return impl_float
    pmjz__cvhb = to_str_arr_if_dict_array(arr)

    def impl(n, arr):
        numba.parfors.parfor.init_prange()
        roev__djw = bodo.utils.utils.alloc_type(n, pmjz__cvhb, (0,))
        for i in numba.parfors.parfor.internal_prange(n):
            setna(roev__djw, i)
        return roev__djw
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
    gqa__lkp = A
    if A == types.Array(types.uint8, 1, 'C'):

        def impl_char(A, old_size, new_len):
            roev__djw = bodo.utils.utils.alloc_type(new_len, gqa__lkp)
            bodo.libs.str_arr_ext.str_copy_ptr(roev__djw.ctypes, 0, A.
                ctypes, old_size)
            return roev__djw
        return impl_char

    def impl(A, old_size, new_len):
        roev__djw = bodo.utils.utils.alloc_type(new_len, gqa__lkp, (-1,))
        roev__djw[:old_size] = A[:old_size]
        return roev__djw
    return impl


@register_jitable
def calc_nitems(start, stop, step):
    nuee__lsltk = math.ceil((stop - start) / step)
    return int(max(nuee__lsltk, 0))


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
    if any(isinstance(kunwt__jzl, types.Complex) for kunwt__jzl in args):

        def arange_4(start, stop, step, dtype):
            numba.parfors.parfor.init_prange()
            suxkh__wtpbq = (stop - start) / step
            nuee__lsltk = math.ceil(suxkh__wtpbq.real)
            wjphk__ytv = math.ceil(suxkh__wtpbq.imag)
            hnut__lmxax = int(max(min(wjphk__ytv, nuee__lsltk), 0))
            arr = np.empty(hnut__lmxax, dtype)
            for i in numba.parfors.parfor.internal_prange(hnut__lmxax):
                arr[i] = start + i * step
            return arr
    else:

        def arange_4(start, stop, step, dtype):
            numba.parfors.parfor.init_prange()
            hnut__lmxax = bodo.libs.array_kernels.calc_nitems(start, stop, step
                )
            arr = np.empty(hnut__lmxax, dtype)
            for i in numba.parfors.parfor.internal_prange(hnut__lmxax):
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
        szxx__fbzz = arr,
        if not inplace:
            szxx__fbzz = arr.copy(),
        ygqf__kuo = bodo.libs.str_arr_ext.to_list_if_immutable_arr(szxx__fbzz)
        bwxxm__wqz = bodo.libs.str_arr_ext.to_list_if_immutable_arr(data, True)
        bodo.libs.timsort.sort(ygqf__kuo, 0, n, bwxxm__wqz)
        if not ascending:
            bodo.libs.timsort.reverseRange(ygqf__kuo, 0, n, bwxxm__wqz)
        bodo.libs.str_arr_ext.cp_str_list_to_array(szxx__fbzz, ygqf__kuo)
        return szxx__fbzz[0]
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
        bbe__jer = []
        for i in range(n):
            if A[i]:
                bbe__jer.append(i + offset)
        return np.array(bbe__jer, np.int64),
    return impl


def ffill_bfill_arr(arr):
    return arr


@overload(ffill_bfill_arr, no_unliteral=True)
def ffill_bfill_overload(A, method, parallel=False):
    gqa__lkp = element_type(A)
    if gqa__lkp == types.unicode_type:
        null_value = '""'
    elif gqa__lkp == types.bool_:
        null_value = 'False'
    elif gqa__lkp == bodo.datetime64ns:
        null_value = (
            'bodo.utils.conversion.unbox_if_timestamp(pd.to_datetime(0))')
    elif gqa__lkp == bodo.timedelta64ns:
        null_value = (
            'bodo.utils.conversion.unbox_if_timestamp(pd.to_timedelta(0))')
    else:
        null_value = '0'
    kay__pzy = 'i'
    fxx__wre = False
    enrba__nybz = get_overload_const_str(method)
    if enrba__nybz in ('ffill', 'pad'):
        kgm__huet = 'n'
        send_right = True
    elif enrba__nybz in ('backfill', 'bfill'):
        kgm__huet = 'n-1, -1, -1'
        send_right = False
        if gqa__lkp == types.unicode_type:
            kay__pzy = '(n - 1) - i'
            fxx__wre = True
    tvq__gii = 'def impl(A, method, parallel=False):\n'
    tvq__gii += '  A = decode_if_dict_array(A)\n'
    tvq__gii += '  has_last_value = False\n'
    tvq__gii += f'  last_value = {null_value}\n'
    tvq__gii += '  if parallel:\n'
    tvq__gii += '    rank = bodo.libs.distributed_api.get_rank()\n'
    tvq__gii += '    n_pes = bodo.libs.distributed_api.get_size()\n'
    tvq__gii += f"""    has_last_value, last_value = null_border_icomm(A, rank, n_pes, {null_value}, {send_right})
"""
    tvq__gii += '  n = len(A)\n'
    tvq__gii += '  out_arr = bodo.utils.utils.alloc_type(n, A, (-1,))\n'
    tvq__gii += f'  for i in range({kgm__huet}):\n'
    tvq__gii += (
        '    if (bodo.libs.array_kernels.isna(A, i) and not has_last_value):\n'
        )
    tvq__gii += f'      bodo.libs.array_kernels.setna(out_arr, {kay__pzy})\n'
    tvq__gii += '      continue\n'
    tvq__gii += '    s = A[i]\n'
    tvq__gii += '    if bodo.libs.array_kernels.isna(A, i):\n'
    tvq__gii += '      s = last_value\n'
    tvq__gii += f'    out_arr[{kay__pzy}] = s\n'
    tvq__gii += '    last_value = s\n'
    tvq__gii += '    has_last_value = True\n'
    if fxx__wre:
        tvq__gii += '  return out_arr[::-1]\n'
    else:
        tvq__gii += '  return out_arr\n'
    cqwiv__rtz = {}
    exec(tvq__gii, {'bodo': bodo, 'numba': numba, 'pd': pd,
        'null_border_icomm': null_border_icomm, 'decode_if_dict_array':
        decode_if_dict_array}, cqwiv__rtz)
    impl = cqwiv__rtz['impl']
    return impl


@register_jitable(cache=True)
def null_border_icomm(in_arr, rank, n_pes, null_value, send_right=True):
    if send_right:
        mra__afxk = 0
        qlxnf__lvhs = n_pes - 1
        xtri__jek = np.int32(rank + 1)
        kerl__rpp = np.int32(rank - 1)
        czz__hfonp = len(in_arr) - 1
        zkh__qxi = -1
        mmgx__nfas = -1
    else:
        mra__afxk = n_pes - 1
        qlxnf__lvhs = 0
        xtri__jek = np.int32(rank - 1)
        kerl__rpp = np.int32(rank + 1)
        czz__hfonp = 0
        zkh__qxi = len(in_arr)
        mmgx__nfas = 1
    ghbkj__gphb = np.int32(bodo.hiframes.rolling.comm_border_tag)
    jkk__loxg = np.empty(1, dtype=np.bool_)
    rqa__lkxj = bodo.utils.utils.alloc_type(1, in_arr, (-1,))
    ihybh__xnq = np.empty(1, dtype=np.bool_)
    xenw__uvy = bodo.utils.utils.alloc_type(1, in_arr, (-1,))
    sfy__zlxh = False
    xglgt__wywpg = null_value
    for i in range(czz__hfonp, zkh__qxi, mmgx__nfas):
        if not isna(in_arr, i):
            sfy__zlxh = True
            xglgt__wywpg = in_arr[i]
            break
    if rank != mra__afxk:
        csdb__mzsuj = bodo.libs.distributed_api.irecv(jkk__loxg, 1,
            kerl__rpp, ghbkj__gphb, True)
        bodo.libs.distributed_api.wait(csdb__mzsuj, True)
        lpgi__flu = bodo.libs.distributed_api.irecv(rqa__lkxj, 1, kerl__rpp,
            ghbkj__gphb, True)
        bodo.libs.distributed_api.wait(lpgi__flu, True)
        uzje__zmpve = jkk__loxg[0]
        ima__atkwx = rqa__lkxj[0]
    else:
        uzje__zmpve = False
        ima__atkwx = null_value
    if sfy__zlxh:
        ihybh__xnq[0] = sfy__zlxh
        xenw__uvy[0] = xglgt__wywpg
    else:
        ihybh__xnq[0] = uzje__zmpve
        xenw__uvy[0] = ima__atkwx
    if rank != qlxnf__lvhs:
        ime__kslz = bodo.libs.distributed_api.isend(ihybh__xnq, 1,
            xtri__jek, ghbkj__gphb, True)
        tua__drscu = bodo.libs.distributed_api.isend(xenw__uvy, 1,
            xtri__jek, ghbkj__gphb, True)
    return uzje__zmpve, ima__atkwx


@overload(np.sort, inline='always', no_unliteral=True)
def np_sort(A, axis=-1, kind=None, order=None):
    if not bodo.utils.utils.is_array_typ(A, False) or isinstance(A, types.Array
        ):
        return
    icx__cboe = {'axis': axis, 'kind': kind, 'order': order}
    jofm__pfr = {'axis': -1, 'kind': None, 'order': None}
    check_unsupported_args('np.sort', icx__cboe, jofm__pfr, 'numpy')

    def impl(A, axis=-1, kind=None, order=None):
        return pd.Series(A).sort_values().values
    return impl


def repeat_kernel(A, repeats):
    return A


@overload(repeat_kernel, no_unliteral=True)
def repeat_kernel_overload(A, repeats):
    gqa__lkp = to_str_arr_if_dict_array(A)
    if isinstance(repeats, types.Integer):

        def impl_int(A, repeats):
            A = decode_if_dict_array(A)
            rrq__jniu = len(A)
            roev__djw = bodo.utils.utils.alloc_type(rrq__jniu * repeats,
                gqa__lkp, (-1,))
            for i in range(rrq__jniu):
                kay__pzy = i * repeats
                if bodo.libs.array_kernels.isna(A, i):
                    for fejrh__bnz in range(repeats):
                        bodo.libs.array_kernels.setna(roev__djw, kay__pzy +
                            fejrh__bnz)
                else:
                    roev__djw[kay__pzy:kay__pzy + repeats] = A[i]
            return roev__djw
        return impl_int

    def impl_arr(A, repeats):
        A = decode_if_dict_array(A)
        rrq__jniu = len(A)
        roev__djw = bodo.utils.utils.alloc_type(repeats.sum(), gqa__lkp, (-1,))
        kay__pzy = 0
        for i in range(rrq__jniu):
            okjll__oaqs = repeats[i]
            if bodo.libs.array_kernels.isna(A, i):
                for fejrh__bnz in range(okjll__oaqs):
                    bodo.libs.array_kernels.setna(roev__djw, kay__pzy +
                        fejrh__bnz)
            else:
                roev__djw[kay__pzy:kay__pzy + okjll__oaqs] = A[i]
            kay__pzy += okjll__oaqs
        return roev__djw
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
        eftbs__jpq = bodo.libs.array_kernels.unique(A)
        return bodo.allgatherv(eftbs__jpq, False)
    return impl


@overload(np.union1d, inline='always', no_unliteral=True)
def overload_union1d(A1, A2):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.union1d()')

    def impl(A1, A2):
        gjom__gge = bodo.libs.array_kernels.concat([A1, A2])
        ozvd__icrlt = bodo.libs.array_kernels.unique(gjom__gge)
        return pd.Series(ozvd__icrlt).sort_values().values
    return impl


@overload(np.intersect1d, inline='always', no_unliteral=True)
def overload_intersect1d(A1, A2, assume_unique=False, return_indices=False):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    icx__cboe = {'assume_unique': assume_unique, 'return_indices':
        return_indices}
    jofm__pfr = {'assume_unique': False, 'return_indices': False}
    check_unsupported_args('np.intersect1d', icx__cboe, jofm__pfr, 'numpy')
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.intersect1d()'
            )
    if A1.ndim != 1 or A2.ndim != 1:
        raise BodoError('Only 1D arrays supported in np.intersect1d()')

    def impl(A1, A2, assume_unique=False, return_indices=False):
        nfjo__axqsk = bodo.libs.array_kernels.unique(A1)
        yasoa__tsanm = bodo.libs.array_kernels.unique(A2)
        gjom__gge = bodo.libs.array_kernels.concat([nfjo__axqsk, yasoa__tsanm])
        vhkz__qoy = pd.Series(gjom__gge).sort_values().values
        return slice_array_intersect1d(vhkz__qoy)
    return impl


@register_jitable
def slice_array_intersect1d(arr):
    ayta__nquk = arr[1:] == arr[:-1]
    return arr[:-1][ayta__nquk]


@overload(np.setdiff1d, inline='always', no_unliteral=True)
def overload_setdiff1d(A1, A2, assume_unique=False):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    icx__cboe = {'assume_unique': assume_unique}
    jofm__pfr = {'assume_unique': False}
    check_unsupported_args('np.setdiff1d', icx__cboe, jofm__pfr, 'numpy')
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.setdiff1d()')
    if A1.ndim != 1 or A2.ndim != 1:
        raise BodoError('Only 1D arrays supported in np.setdiff1d()')

    def impl(A1, A2, assume_unique=False):
        nfjo__axqsk = bodo.libs.array_kernels.unique(A1)
        yasoa__tsanm = bodo.libs.array_kernels.unique(A2)
        ayta__nquk = calculate_mask_setdiff1d(nfjo__axqsk, yasoa__tsanm)
        return pd.Series(nfjo__axqsk[ayta__nquk]).sort_values().values
    return impl


@register_jitable
def calculate_mask_setdiff1d(A1, A2):
    ayta__nquk = np.ones(len(A1), np.bool_)
    for i in range(len(A2)):
        ayta__nquk &= A1 != A2[i]
    return ayta__nquk


@overload(np.linspace, inline='always', no_unliteral=True)
def np_linspace(start, stop, num=50, endpoint=True, retstep=False, dtype=
    None, axis=0):
    icx__cboe = {'retstep': retstep, 'axis': axis}
    jofm__pfr = {'retstep': False, 'axis': 0}
    check_unsupported_args('np.linspace', icx__cboe, jofm__pfr, 'numpy')
    rym__prm = False
    if is_overload_none(dtype):
        gqa__lkp = np.promote_types(np.promote_types(numba.np.numpy_support
            .as_dtype(start), numba.np.numpy_support.as_dtype(stop)), numba
            .np.numpy_support.as_dtype(types.float64)).type
    else:
        if isinstance(dtype.dtype, types.Integer):
            rym__prm = True
        gqa__lkp = numba.np.numpy_support.as_dtype(dtype).type
    if rym__prm:

        def impl_int(start, stop, num=50, endpoint=True, retstep=False,
            dtype=None, axis=0):
            bxcj__tpion = np_linspace_get_stepsize(start, stop, num, endpoint)
            numba.parfors.parfor.init_prange()
            roev__djw = np.empty(num, gqa__lkp)
            for i in numba.parfors.parfor.internal_prange(num):
                roev__djw[i] = gqa__lkp(np.floor(start + i * bxcj__tpion))
            return roev__djw
        return impl_int
    else:

        def impl(start, stop, num=50, endpoint=True, retstep=False, dtype=
            None, axis=0):
            bxcj__tpion = np_linspace_get_stepsize(start, stop, num, endpoint)
            numba.parfors.parfor.init_prange()
            roev__djw = np.empty(num, gqa__lkp)
            for i in numba.parfors.parfor.internal_prange(num):
                roev__djw[i] = gqa__lkp(start + i * bxcj__tpion)
            return roev__djw
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
        ziqb__ccamc = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                ziqb__ccamc += A[i] == val
        return ziqb__ccamc > 0
    return impl


@overload(np.any, inline='always', no_unliteral=True)
def np_any(A, axis=None, out=None, keepdims=None):
    if not (bodo.utils.utils.is_array_typ(A, False) and A.ndim == 1):
        return
    icx__cboe = {'axis': axis, 'out': out, 'keepdims': keepdims}
    jofm__pfr = {'axis': None, 'out': None, 'keepdims': None}
    check_unsupported_args('np.any', icx__cboe, jofm__pfr, 'numpy')

    def impl(A, axis=None, out=None, keepdims=None):
        numba.parfors.parfor.init_prange()
        ziqb__ccamc = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                ziqb__ccamc += int(bool(A[i]))
        return ziqb__ccamc > 0
    return impl


@overload(np.all, inline='always', no_unliteral=True)
def np_all(A, axis=None, out=None, keepdims=None):
    if not (bodo.utils.utils.is_array_typ(A, False) and A.ndim == 1):
        return
    icx__cboe = {'axis': axis, 'out': out, 'keepdims': keepdims}
    jofm__pfr = {'axis': None, 'out': None, 'keepdims': None}
    check_unsupported_args('np.any', icx__cboe, jofm__pfr, 'numpy')

    def impl(A, axis=None, out=None, keepdims=None):
        numba.parfors.parfor.init_prange()
        ziqb__ccamc = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                ziqb__ccamc += int(bool(A[i]))
        return ziqb__ccamc == n
    return impl


@overload(np.cbrt, inline='always', no_unliteral=True)
def np_cbrt(A, out=None, where=True, casting='same_kind', order='K', dtype=
    None, subok=True):
    if not (isinstance(A, types.Number) or bodo.utils.utils.is_array_typ(A,
        False) and A.ndim == 1 and isinstance(A.dtype, types.Number)):
        return
    icx__cboe = {'out': out, 'where': where, 'casting': casting, 'order':
        order, 'dtype': dtype, 'subok': subok}
    jofm__pfr = {'out': None, 'where': True, 'casting': 'same_kind',
        'order': 'K', 'dtype': None, 'subok': True}
    check_unsupported_args('np.cbrt', icx__cboe, jofm__pfr, 'numpy')
    if bodo.utils.utils.is_array_typ(A, False):
        bobqr__ngqul = np.promote_types(numba.np.numpy_support.as_dtype(A.
            dtype), numba.np.numpy_support.as_dtype(types.float32)).type

        def impl_arr(A, out=None, where=True, casting='same_kind', order=
            'K', dtype=None, subok=True):
            numba.parfors.parfor.init_prange()
            n = len(A)
            roev__djw = np.empty(n, bobqr__ngqul)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(A, i):
                    bodo.libs.array_kernels.setna(roev__djw, i)
                    continue
                roev__djw[i] = np_cbrt_scalar(A[i], bobqr__ngqul)
            return roev__djw
        return impl_arr
    bobqr__ngqul = np.promote_types(numba.np.numpy_support.as_dtype(A),
        numba.np.numpy_support.as_dtype(types.float32)).type

    def impl_scalar(A, out=None, where=True, casting='same_kind', order='K',
        dtype=None, subok=True):
        return np_cbrt_scalar(A, bobqr__ngqul)
    return impl_scalar


@register_jitable
def np_cbrt_scalar(x, float_dtype):
    if np.isnan(x):
        return np.nan
    xubwc__hhozf = x < 0
    if xubwc__hhozf:
        x = -x
    res = np.power(float_dtype(x), 1.0 / 3.0)
    if xubwc__hhozf:
        return -res
    return res


@overload(np.hstack, no_unliteral=True)
def np_hstack(tup):
    ulfq__xne = isinstance(tup, (types.BaseTuple, types.List))
    ouji__deosx = isinstance(tup, (bodo.SeriesType, bodo.hiframes.
        pd_series_ext.HeterogeneousSeriesType)) and isinstance(tup.data, (
        types.BaseTuple, types.List, bodo.NullableTupleType))
    if isinstance(tup, types.BaseTuple):
        for pvpo__gokku in tup.types:
            ulfq__xne = ulfq__xne and bodo.utils.utils.is_array_typ(pvpo__gokku
                , False)
    elif isinstance(tup, types.List):
        ulfq__xne = bodo.utils.utils.is_array_typ(tup.dtype, False)
    elif ouji__deosx:
        pbhnj__hgso = tup.data.tuple_typ if isinstance(tup.data, bodo.
            NullableTupleType) else tup.data
        for pvpo__gokku in pbhnj__hgso.types:
            ouji__deosx = ouji__deosx and bodo.utils.utils.is_array_typ(
                pvpo__gokku, False)
    if not (ulfq__xne or ouji__deosx):
        return
    if ouji__deosx:

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
    icx__cboe = {'check_valid': check_valid, 'tol': tol}
    jofm__pfr = {'check_valid': 'warn', 'tol': 1e-08}
    check_unsupported_args('np.random.multivariate_normal', icx__cboe,
        jofm__pfr, 'numpy')
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
        iukz__brg = mean.shape[0]
        oqv__zwxqh = size, iukz__brg
        htf__ivhc = np.random.standard_normal(oqv__zwxqh)
        cov = cov.astype(np.float64)
        dmri__tpfg, s, raqo__meu = np.linalg.svd(cov)
        res = np.dot(htf__ivhc, np.sqrt(s).reshape(iukz__brg, 1) * raqo__meu)
        nsy__rxyt = res + mean
        return nsy__rxyt
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
            rpm__dwnvh = bodo.hiframes.series_kernels._get_type_max_value(arr)
            tdd__yyv = typing.builtins.IndexValue(-1, rpm__dwnvh)
            for i in numba.parfors.parfor.internal_prange(len(arr)):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                klu__buqr = typing.builtins.IndexValue(i, arr[i])
                tdd__yyv = min(tdd__yyv, klu__buqr)
            return tdd__yyv.index
        return impl_bodo_arr
    if isinstance(arr, CategoricalArrayType):
        assert arr.dtype.ordered, 'Categorical Array must be ordered to select an argmin'
        gix__tdhc = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            arr.dtype)

        def impl_cat_arr(arr):
            cfana__iwdby = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            rpm__dwnvh = gix__tdhc(len(arr.dtype.categories) + 1)
            tdd__yyv = typing.builtins.IndexValue(-1, rpm__dwnvh)
            for i in numba.parfors.parfor.internal_prange(len(arr)):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                klu__buqr = typing.builtins.IndexValue(i, cfana__iwdby[i])
                tdd__yyv = min(tdd__yyv, klu__buqr)
            return tdd__yyv.index
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
            rpm__dwnvh = bodo.hiframes.series_kernels._get_type_min_value(arr)
            tdd__yyv = typing.builtins.IndexValue(-1, rpm__dwnvh)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                klu__buqr = typing.builtins.IndexValue(i, arr[i])
                tdd__yyv = max(tdd__yyv, klu__buqr)
            return tdd__yyv.index
        return impl_bodo_arr
    if isinstance(arr, CategoricalArrayType):
        assert arr.dtype.ordered, 'Categorical Array must be ordered to select an argmin'
        gix__tdhc = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            arr.dtype)

        def impl_cat_arr(arr):
            n = len(arr)
            cfana__iwdby = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            rpm__dwnvh = gix__tdhc(-1)
            tdd__yyv = typing.builtins.IndexValue(-1, rpm__dwnvh)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                klu__buqr = typing.builtins.IndexValue(i, cfana__iwdby[i])
                tdd__yyv = max(tdd__yyv, klu__buqr)
            return tdd__yyv.index
        return impl_cat_arr
    return lambda arr: arr.argmax()


@overload_attribute(types.Array, 'nbytes', inline='always')
def overload_dataframe_index(A):
    return lambda A: A.size * bodo.io.np_io.get_dtype_size(A.dtype)
