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
        bdogc__owro = arr.dtype('NaT')

        def _setnan_impl(arr, ind, int_nan_const=0):
            arr[ind] = bdogc__owro
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
            zmsv__bpl = bodo.libs.array_item_arr_ext.get_offsets(arr._data)
            zmsv__bpl[ind + 1] = zmsv__bpl[ind]
            bodo.libs.int_arr_ext.set_bit_to_arr(bodo.libs.
                array_item_arr_ext.get_null_bitmap(arr._data), ind, 0)
        return impl_binary_arr
    if isinstance(arr, bodo.libs.array_item_arr_ext.ArrayItemArrayType):

        def impl_arr_item(arr, ind, int_nan_const=0):
            zmsv__bpl = bodo.libs.array_item_arr_ext.get_offsets(arr)
            zmsv__bpl[ind + 1] = zmsv__bpl[ind]
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
    iqi__ahr = arr_tup.count
    lefnz__mpnyv = 'def f(arr_tup, ind, int_nan_const=0):\n'
    for i in range(iqi__ahr):
        lefnz__mpnyv += '  setna(arr_tup[{}], ind, int_nan_const)\n'.format(i)
    lefnz__mpnyv += '  return\n'
    irkl__lbha = {}
    exec(lefnz__mpnyv, {'setna': setna}, irkl__lbha)
    impl = irkl__lbha['f']
    return impl


def setna_slice(arr, s):
    arr[s] = np.nan


@overload(setna_slice, no_unliteral=True)
def overload_setna_slice(arr, s):

    def impl(arr, s):
        nedq__nwjdm = numba.cpython.unicode._normalize_slice(s, len(arr))
        for i in range(nedq__nwjdm.start, nedq__nwjdm.stop, nedq__nwjdm.step):
            setna(arr, i)
    return impl


@numba.generated_jit
def first_last_valid_index(arr, index_arr, is_first=True, parallel=False):
    is_first = get_overload_const_bool(is_first)
    if is_first:
        eanf__suv = 'n'
    else:
        eanf__suv = 'n-1, -1, -1'
    lefnz__mpnyv = f"""def impl(arr, index_arr, is_first=True, parallel=False):
    n = len(arr)
    index_val = index_arr[0]
    has_valid = False
    loc_min = -1
    if parallel:
        rank = bodo.libs.distributed_api.get_rank()
        n_pes = bodo.libs.distributed_api.get_size()
        loc_min = n_pes
    for i in range({eanf__suv}):
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
    irkl__lbha = {}
    exec(lefnz__mpnyv, {'np': np, 'bodo': bodo, 'isna': isna, 'min_op':
        min_op, 'box_if_dt64': bodo.utils.conversion.box_if_dt64}, irkl__lbha)
    impl = irkl__lbha['impl']
    return impl


ll.add_symbol('median_series_computation', quantile_alg.
    median_series_computation)
_median_series_computation = types.ExternalFunction('median_series_computation'
    , types.void(types.voidptr, bodo.libs.array.array_info_type, types.
    bool_, types.bool_))


@numba.njit
def median_series_computation(res, arr, is_parallel, skipna):
    yffsl__mdsp = array_to_info(arr)
    _median_series_computation(res, yffsl__mdsp, is_parallel, skipna)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(yffsl__mdsp)


ll.add_symbol('autocorr_series_computation', quantile_alg.
    autocorr_series_computation)
_autocorr_series_computation = types.ExternalFunction(
    'autocorr_series_computation', types.void(types.voidptr, bodo.libs.
    array.array_info_type, types.int64, types.bool_))


@numba.njit
def autocorr_series_computation(res, arr, lag, is_parallel):
    yffsl__mdsp = array_to_info(arr)
    _autocorr_series_computation(res, yffsl__mdsp, lag, is_parallel)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(yffsl__mdsp)


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
    yffsl__mdsp = array_to_info(arr)
    _compute_series_monotonicity(res, yffsl__mdsp, inc_dec, is_parallel)
    check_and_propagate_cpp_exception()
    delete_info_decref_array(yffsl__mdsp)


@numba.njit
def series_monotonicity(arr, inc_dec, parallel=False):
    res = np.empty(1, types.float64)
    series_monotonicity_call(res.ctypes, arr, inc_dec, parallel)
    tupkx__qzl = res[0] > 0.5
    return tupkx__qzl


@numba.generated_jit(nopython=True)
def get_valid_entries_from_date_offset(index_arr, offset, initial_date,
    is_last, is_parallel=False):
    if get_overload_const_bool(is_last):
        ilo__acma = '-'
        evj__utm = 'index_arr[0] > threshhold_date'
        eanf__suv = '1, n+1'
        nbr__rmpag = 'index_arr[-i] <= threshhold_date'
        xfq__hlkew = 'i - 1'
    else:
        ilo__acma = '+'
        evj__utm = 'index_arr[-1] < threshhold_date'
        eanf__suv = 'n'
        nbr__rmpag = 'index_arr[i] >= threshhold_date'
        xfq__hlkew = 'i'
    lefnz__mpnyv = (
        'def impl(index_arr, offset, initial_date, is_last, is_parallel=False):\n'
        )
    if types.unliteral(offset) == types.unicode_type:
        lefnz__mpnyv += (
            '  with numba.objmode(threshhold_date=bodo.pd_timestamp_type):\n')
        lefnz__mpnyv += (
            '    date_offset = pd.tseries.frequencies.to_offset(offset)\n')
        if not get_overload_const_bool(is_last):
            lefnz__mpnyv += """    if not isinstance(date_offset, pd._libs.tslibs.Tick) and date_offset.is_on_offset(index_arr[0]):
"""
            lefnz__mpnyv += """      threshhold_date = initial_date - date_offset.base + date_offset
"""
            lefnz__mpnyv += '    else:\n'
            lefnz__mpnyv += (
                '      threshhold_date = initial_date + date_offset\n')
        else:
            lefnz__mpnyv += (
                f'    threshhold_date = initial_date {ilo__acma} date_offset\n'
                )
    else:
        lefnz__mpnyv += (
            f'  threshhold_date = initial_date {ilo__acma} offset\n')
    lefnz__mpnyv += '  local_valid = 0\n'
    lefnz__mpnyv += f'  n = len(index_arr)\n'
    lefnz__mpnyv += f'  if n:\n'
    lefnz__mpnyv += f'    if {evj__utm}:\n'
    lefnz__mpnyv += '      loc_valid = n\n'
    lefnz__mpnyv += '    else:\n'
    lefnz__mpnyv += f'      for i in range({eanf__suv}):\n'
    lefnz__mpnyv += f'        if {nbr__rmpag}:\n'
    lefnz__mpnyv += f'          loc_valid = {xfq__hlkew}\n'
    lefnz__mpnyv += '          break\n'
    lefnz__mpnyv += '  if is_parallel:\n'
    lefnz__mpnyv += (
        '    total_valid = bodo.libs.distributed_api.dist_reduce(loc_valid, sum_op)\n'
        )
    lefnz__mpnyv += '    return total_valid\n'
    lefnz__mpnyv += '  else:\n'
    lefnz__mpnyv += '    return loc_valid\n'
    irkl__lbha = {}
    exec(lefnz__mpnyv, {'bodo': bodo, 'pd': pd, 'numba': numba, 'sum_op':
        sum_op}, irkl__lbha)
    return irkl__lbha['impl']


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
    deda__ffpl = numba_to_c_type(sig.args[0].dtype)
    lbm__dtomk = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(32), deda__ffpl))
    civ__odm = args[0]
    ijo__qlkqh = sig.args[0]
    if isinstance(ijo__qlkqh, (IntegerArrayType, BooleanArrayType)):
        civ__odm = cgutils.create_struct_proxy(ijo__qlkqh)(context, builder,
            civ__odm).data
        ijo__qlkqh = types.Array(ijo__qlkqh.dtype, 1, 'C')
    assert ijo__qlkqh.ndim == 1
    arr = make_array(ijo__qlkqh)(context, builder, civ__odm)
    lfrv__mxkhq = builder.extract_value(arr.shape, 0)
    ssyr__iqw = [builder.bitcast(arr.data, lir.IntType(8).as_pointer()),
        lfrv__mxkhq, args[1], builder.load(lbm__dtomk)]
    cixq__dcbm = [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
        DoubleType(), lir.IntType(32)]
    drue__lsu = lir.FunctionType(lir.DoubleType(), cixq__dcbm)
    raruc__cerv = cgutils.get_or_insert_function(builder.module, drue__lsu,
        name='quantile_sequential')
    lwrdz__pvfnj = builder.call(raruc__cerv, ssyr__iqw)
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return lwrdz__pvfnj


@lower_builtin(quantile_parallel, types.Array, types.float64, types.intp)
@lower_builtin(quantile_parallel, IntegerArrayType, types.float64, types.intp)
@lower_builtin(quantile_parallel, BooleanArrayType, types.float64, types.intp)
def lower_dist_quantile_parallel(context, builder, sig, args):
    deda__ffpl = numba_to_c_type(sig.args[0].dtype)
    lbm__dtomk = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(32), deda__ffpl))
    civ__odm = args[0]
    ijo__qlkqh = sig.args[0]
    if isinstance(ijo__qlkqh, (IntegerArrayType, BooleanArrayType)):
        civ__odm = cgutils.create_struct_proxy(ijo__qlkqh)(context, builder,
            civ__odm).data
        ijo__qlkqh = types.Array(ijo__qlkqh.dtype, 1, 'C')
    assert ijo__qlkqh.ndim == 1
    arr = make_array(ijo__qlkqh)(context, builder, civ__odm)
    lfrv__mxkhq = builder.extract_value(arr.shape, 0)
    if len(args) == 3:
        zhd__yiq = args[2]
    else:
        zhd__yiq = lfrv__mxkhq
    ssyr__iqw = [builder.bitcast(arr.data, lir.IntType(8).as_pointer()),
        lfrv__mxkhq, zhd__yiq, args[1], builder.load(lbm__dtomk)]
    cixq__dcbm = [lir.IntType(8).as_pointer(), lir.IntType(64), lir.IntType
        (64), lir.DoubleType(), lir.IntType(32)]
    drue__lsu = lir.FunctionType(lir.DoubleType(), cixq__dcbm)
    raruc__cerv = cgutils.get_or_insert_function(builder.module, drue__lsu,
        name='quantile_parallel')
    lwrdz__pvfnj = builder.call(raruc__cerv, ssyr__iqw)
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return lwrdz__pvfnj


@numba.njit
def min_heapify(arr, ind_arr, n, start, cmp_f):
    kul__nxms = start
    rlfy__obiaj = 2 * start + 1
    iyma__lal = 2 * start + 2
    if rlfy__obiaj < n and not cmp_f(arr[rlfy__obiaj], arr[kul__nxms]):
        kul__nxms = rlfy__obiaj
    if iyma__lal < n and not cmp_f(arr[iyma__lal], arr[kul__nxms]):
        kul__nxms = iyma__lal
    if kul__nxms != start:
        arr[start], arr[kul__nxms] = arr[kul__nxms], arr[start]
        ind_arr[start], ind_arr[kul__nxms] = ind_arr[kul__nxms], ind_arr[start]
        min_heapify(arr, ind_arr, n, kul__nxms, cmp_f)


def select_k_nonan(A, index_arr, m, k):
    return A[:k]


@overload(select_k_nonan, no_unliteral=True)
def select_k_nonan_overload(A, index_arr, m, k):
    dtype = A.dtype
    if isinstance(dtype, types.Integer):
        return lambda A, index_arr, m, k: (A[:k].copy(), index_arr[:k].copy
            (), k)

    def select_k_nonan_float(A, index_arr, m, k):
        tsh__dpkfh = np.empty(k, A.dtype)
        lkn__iac = np.empty(k, index_arr.dtype)
        i = 0
        ind = 0
        while i < m and ind < k:
            if not bodo.libs.array_kernels.isna(A, i):
                tsh__dpkfh[ind] = A[i]
                lkn__iac[ind] = index_arr[i]
                ind += 1
            i += 1
        if ind < k:
            tsh__dpkfh = tsh__dpkfh[:ind]
            lkn__iac = lkn__iac[:ind]
        return tsh__dpkfh, lkn__iac, i
    return select_k_nonan_float


@numba.njit
def nlargest(A, index_arr, k, is_largest, cmp_f):
    m = len(A)
    if k == 0:
        return A[:0], index_arr[:0]
    if k >= m:
        jepmd__bear = np.sort(A)
        icp__dvka = index_arr[np.argsort(A)]
        qjdl__lzfxl = pd.Series(jepmd__bear).notna().values
        jepmd__bear = jepmd__bear[qjdl__lzfxl]
        icp__dvka = icp__dvka[qjdl__lzfxl]
        if is_largest:
            jepmd__bear = jepmd__bear[::-1]
            icp__dvka = icp__dvka[::-1]
        return np.ascontiguousarray(jepmd__bear), np.ascontiguousarray(
            icp__dvka)
    tsh__dpkfh, lkn__iac, start = select_k_nonan(A, index_arr, m, k)
    lkn__iac = lkn__iac[tsh__dpkfh.argsort()]
    tsh__dpkfh.sort()
    if not is_largest:
        tsh__dpkfh = np.ascontiguousarray(tsh__dpkfh[::-1])
        lkn__iac = np.ascontiguousarray(lkn__iac[::-1])
    for i in range(start, m):
        if cmp_f(A[i], tsh__dpkfh[0]):
            tsh__dpkfh[0] = A[i]
            lkn__iac[0] = index_arr[i]
            min_heapify(tsh__dpkfh, lkn__iac, k, 0, cmp_f)
    lkn__iac = lkn__iac[tsh__dpkfh.argsort()]
    tsh__dpkfh.sort()
    if is_largest:
        tsh__dpkfh = tsh__dpkfh[::-1]
        lkn__iac = lkn__iac[::-1]
    return np.ascontiguousarray(tsh__dpkfh), np.ascontiguousarray(lkn__iac)


@numba.njit
def nlargest_parallel(A, I, k, is_largest, cmp_f):
    hsty__kzb = bodo.libs.distributed_api.get_rank()
    xasvo__xwglz, xvyn__pka = nlargest(A, I, k, is_largest, cmp_f)
    gjr__xyk = bodo.libs.distributed_api.gatherv(xasvo__xwglz)
    dls__fylv = bodo.libs.distributed_api.gatherv(xvyn__pka)
    if hsty__kzb == MPI_ROOT:
        res, koe__orfoi = nlargest(gjr__xyk, dls__fylv, k, is_largest, cmp_f)
    else:
        res = np.empty(k, A.dtype)
        koe__orfoi = np.empty(k, I.dtype)
    bodo.libs.distributed_api.bcast(res)
    bodo.libs.distributed_api.bcast(koe__orfoi)
    return res, koe__orfoi


@numba.njit(no_cpython_wrapper=True, cache=True)
def nancorr(mat, cov=0, minpv=1, parallel=False):
    jha__hgt, laatl__bkn = mat.shape
    miw__twwz = np.empty((laatl__bkn, laatl__bkn), dtype=np.float64)
    for dsnr__uyx in range(laatl__bkn):
        for rus__lvurn in range(dsnr__uyx + 1):
            wghi__wzegu = 0
            hzakm__lkeb = ufst__udqb = absza__xqr = ngl__ogdb = 0.0
            for i in range(jha__hgt):
                if np.isfinite(mat[i, dsnr__uyx]) and np.isfinite(mat[i,
                    rus__lvurn]):
                    adzj__lfodv = mat[i, dsnr__uyx]
                    pmvtn__srfq = mat[i, rus__lvurn]
                    wghi__wzegu += 1
                    absza__xqr += adzj__lfodv
                    ngl__ogdb += pmvtn__srfq
            if parallel:
                wghi__wzegu = bodo.libs.distributed_api.dist_reduce(wghi__wzegu
                    , sum_op)
                absza__xqr = bodo.libs.distributed_api.dist_reduce(absza__xqr,
                    sum_op)
                ngl__ogdb = bodo.libs.distributed_api.dist_reduce(ngl__ogdb,
                    sum_op)
            if wghi__wzegu < minpv:
                miw__twwz[dsnr__uyx, rus__lvurn] = miw__twwz[rus__lvurn,
                    dsnr__uyx] = np.nan
            else:
                qfs__rvoe = absza__xqr / wghi__wzegu
                nsb__xbsb = ngl__ogdb / wghi__wzegu
                absza__xqr = 0.0
                for i in range(jha__hgt):
                    if np.isfinite(mat[i, dsnr__uyx]) and np.isfinite(mat[i,
                        rus__lvurn]):
                        adzj__lfodv = mat[i, dsnr__uyx] - qfs__rvoe
                        pmvtn__srfq = mat[i, rus__lvurn] - nsb__xbsb
                        absza__xqr += adzj__lfodv * pmvtn__srfq
                        hzakm__lkeb += adzj__lfodv * adzj__lfodv
                        ufst__udqb += pmvtn__srfq * pmvtn__srfq
                if parallel:
                    absza__xqr = bodo.libs.distributed_api.dist_reduce(
                        absza__xqr, sum_op)
                    hzakm__lkeb = bodo.libs.distributed_api.dist_reduce(
                        hzakm__lkeb, sum_op)
                    ufst__udqb = bodo.libs.distributed_api.dist_reduce(
                        ufst__udqb, sum_op)
                hcu__lptkt = wghi__wzegu - 1.0 if cov else sqrt(hzakm__lkeb *
                    ufst__udqb)
                if hcu__lptkt != 0.0:
                    miw__twwz[dsnr__uyx, rus__lvurn] = miw__twwz[rus__lvurn,
                        dsnr__uyx] = absza__xqr / hcu__lptkt
                else:
                    miw__twwz[dsnr__uyx, rus__lvurn] = miw__twwz[rus__lvurn,
                        dsnr__uyx] = np.nan
    return miw__twwz


@numba.generated_jit(nopython=True)
def duplicated(data, parallel=False):
    n = len(data)
    if n == 0:
        return lambda data, parallel=False: np.empty(0, dtype=np.bool_)
    onel__lowm = n != 1
    lefnz__mpnyv = 'def impl(data, parallel=False):\n'
    lefnz__mpnyv += '  if parallel:\n'
    shm__vkcko = ', '.join(f'array_to_info(data[{i}])' for i in range(n))
    lefnz__mpnyv += f'    cpp_table = arr_info_list_to_table([{shm__vkcko}])\n'
    lefnz__mpnyv += f"""    out_cpp_table = bodo.libs.array.shuffle_table(cpp_table, {n}, parallel, 1)
"""
    owhx__imrsk = ', '.join(
        f'info_to_array(info_from_table(out_cpp_table, {i}), data[{i}])' for
        i in range(n))
    lefnz__mpnyv += f'    data = ({owhx__imrsk},)\n'
    lefnz__mpnyv += (
        '    shuffle_info = bodo.libs.array.get_shuffle_info(out_cpp_table)\n')
    lefnz__mpnyv += '    bodo.libs.array.delete_table(out_cpp_table)\n'
    lefnz__mpnyv += '    bodo.libs.array.delete_table(cpp_table)\n'
    lefnz__mpnyv += '  n = len(data[0])\n'
    lefnz__mpnyv += '  out = np.empty(n, np.bool_)\n'
    lefnz__mpnyv += '  uniqs = dict()\n'
    if onel__lowm:
        lefnz__mpnyv += '  for i in range(n):\n'
        pkvjg__ebha = ', '.join(f'data[{i}][i]' for i in range(n))
        asrn__zyiv = ',  '.join(
            f'bodo.libs.array_kernels.isna(data[{i}], i)' for i in range(n))
        lefnz__mpnyv += f"""    val = bodo.libs.nullable_tuple_ext.build_nullable_tuple(({pkvjg__ebha},), ({asrn__zyiv},))
"""
        lefnz__mpnyv += '    if val in uniqs:\n'
        lefnz__mpnyv += '      out[i] = True\n'
        lefnz__mpnyv += '    else:\n'
        lefnz__mpnyv += '      out[i] = False\n'
        lefnz__mpnyv += '      uniqs[val] = 0\n'
    else:
        lefnz__mpnyv += '  data = data[0]\n'
        lefnz__mpnyv += '  hasna = False\n'
        lefnz__mpnyv += '  for i in range(n):\n'
        lefnz__mpnyv += '    if bodo.libs.array_kernels.isna(data, i):\n'
        lefnz__mpnyv += '      out[i] = hasna\n'
        lefnz__mpnyv += '      hasna = True\n'
        lefnz__mpnyv += '    else:\n'
        lefnz__mpnyv += '      val = data[i]\n'
        lefnz__mpnyv += '      if val in uniqs:\n'
        lefnz__mpnyv += '        out[i] = True\n'
        lefnz__mpnyv += '      else:\n'
        lefnz__mpnyv += '        out[i] = False\n'
        lefnz__mpnyv += '        uniqs[val] = 0\n'
    lefnz__mpnyv += '  if parallel:\n'
    lefnz__mpnyv += (
        '    out = bodo.hiframes.pd_groupby_ext.reverse_shuffle(out, shuffle_info)\n'
        )
    lefnz__mpnyv += '  return out\n'
    irkl__lbha = {}
    exec(lefnz__mpnyv, {'bodo': bodo, 'np': np, 'array_to_info':
        array_to_info, 'arr_info_list_to_table': arr_info_list_to_table,
        'info_to_array': info_to_array, 'info_from_table': info_from_table},
        irkl__lbha)
    impl = irkl__lbha['impl']
    return impl


def sample_table_operation(data, ind_arr, n, frac, replace, parallel=False):
    return data, ind_arr


@overload(sample_table_operation, no_unliteral=True)
def overload_sample_table_operation(data, ind_arr, n, frac, replace,
    parallel=False):
    iqi__ahr = len(data)
    lefnz__mpnyv = (
        'def impl(data, ind_arr, n, frac, replace, parallel=False):\n')
    lefnz__mpnyv += ('  info_list_total = [{}, array_to_info(ind_arr)]\n'.
        format(', '.join('array_to_info(data[{}])'.format(x) for x in range
        (iqi__ahr))))
    lefnz__mpnyv += '  table_total = arr_info_list_to_table(info_list_total)\n'
    lefnz__mpnyv += (
        '  out_table = sample_table(table_total, n, frac, replace, parallel)\n'
        .format(iqi__ahr))
    for gkw__iosut in range(iqi__ahr):
        lefnz__mpnyv += (
            '  out_arr_{} = info_to_array(info_from_table(out_table, {}), data[{}])\n'
            .format(gkw__iosut, gkw__iosut, gkw__iosut))
    lefnz__mpnyv += (
        '  out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)\n'
        .format(iqi__ahr))
    lefnz__mpnyv += '  delete_table(out_table)\n'
    lefnz__mpnyv += '  delete_table(table_total)\n'
    lefnz__mpnyv += '  return ({},), out_arr_index\n'.format(', '.join(
        'out_arr_{}'.format(i) for i in range(iqi__ahr)))
    irkl__lbha = {}
    exec(lefnz__mpnyv, {'np': np, 'bodo': bodo, 'array_to_info':
        array_to_info, 'sample_table': sample_table,
        'arr_info_list_to_table': arr_info_list_to_table, 'info_from_table':
        info_from_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays}, irkl__lbha)
    impl = irkl__lbha['impl']
    return impl


def drop_duplicates(data, ind_arr, ncols, parallel=False):
    return data, ind_arr


@overload(drop_duplicates, no_unliteral=True)
def overload_drop_duplicates(data, ind_arr, ncols, parallel=False):
    iqi__ahr = len(data)
    lefnz__mpnyv = 'def impl(data, ind_arr, ncols, parallel=False):\n'
    lefnz__mpnyv += ('  info_list_total = [{}, array_to_info(ind_arr)]\n'.
        format(', '.join('array_to_info(data[{}])'.format(x) for x in range
        (iqi__ahr))))
    lefnz__mpnyv += '  table_total = arr_info_list_to_table(info_list_total)\n'
    lefnz__mpnyv += '  keep_i = 0\n'
    lefnz__mpnyv += """  out_table = drop_duplicates_table(table_total, parallel, ncols, keep_i, False, True)
"""
    for gkw__iosut in range(iqi__ahr):
        lefnz__mpnyv += (
            '  out_arr_{} = info_to_array(info_from_table(out_table, {}), data[{}])\n'
            .format(gkw__iosut, gkw__iosut, gkw__iosut))
    lefnz__mpnyv += (
        '  out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)\n'
        .format(iqi__ahr))
    lefnz__mpnyv += '  delete_table(out_table)\n'
    lefnz__mpnyv += '  delete_table(table_total)\n'
    lefnz__mpnyv += '  return ({},), out_arr_index\n'.format(', '.join(
        'out_arr_{}'.format(i) for i in range(iqi__ahr)))
    irkl__lbha = {}
    exec(lefnz__mpnyv, {'np': np, 'bodo': bodo, 'array_to_info':
        array_to_info, 'drop_duplicates_table': drop_duplicates_table,
        'arr_info_list_to_table': arr_info_list_to_table, 'info_from_table':
        info_from_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays}, irkl__lbha)
    impl = irkl__lbha['impl']
    return impl


def drop_duplicates_array(data_arr, parallel=False):
    return data_arr


@overload(drop_duplicates_array, no_unliteral=True)
def overload_drop_duplicates_array(data_arr, parallel=False):

    def impl(data_arr, parallel=False):
        htomd__fbnvi = [array_to_info(data_arr)]
        tqa__tfufq = arr_info_list_to_table(htomd__fbnvi)
        wixfu__zvv = 0
        lnvay__hwh = drop_duplicates_table(tqa__tfufq, parallel, 1,
            wixfu__zvv, False, True)
        imwwn__kdx = info_to_array(info_from_table(lnvay__hwh, 0), data_arr)
        delete_table(lnvay__hwh)
        delete_table(tqa__tfufq)
        return imwwn__kdx
    return impl


def dropna(data, how, thresh, subset, parallel=False):
    return data


@overload(dropna, no_unliteral=True)
def overload_dropna(data, how, thresh, subset):
    hzj__nwzi = len(data.types)
    tws__deav = [('out' + str(i)) for i in range(hzj__nwzi)]
    jvl__vmk = get_overload_const_list(subset)
    how = get_overload_const_str(how)
    rkz__mjwb = ['isna(data[{}], i)'.format(i) for i in jvl__vmk]
    ietvk__rcmi = 'not ({})'.format(' or '.join(rkz__mjwb))
    if not is_overload_none(thresh):
        ietvk__rcmi = '(({}) <= ({}) - thresh)'.format(' + '.join(rkz__mjwb
            ), hzj__nwzi - 1)
    elif how == 'all':
        ietvk__rcmi = 'not ({})'.format(' and '.join(rkz__mjwb))
    lefnz__mpnyv = 'def _dropna_imp(data, how, thresh, subset):\n'
    lefnz__mpnyv += '  old_len = len(data[0])\n'
    lefnz__mpnyv += '  new_len = 0\n'
    lefnz__mpnyv += '  for i in range(old_len):\n'
    lefnz__mpnyv += '    if {}:\n'.format(ietvk__rcmi)
    lefnz__mpnyv += '      new_len += 1\n'
    for i, out in enumerate(tws__deav):
        if isinstance(data[i], bodo.CategoricalArrayType):
            lefnz__mpnyv += (
                '  {0} = bodo.utils.utils.alloc_type(new_len, data[{1}], (-1,))\n'
                .format(out, i))
        else:
            lefnz__mpnyv += (
                '  {0} = bodo.utils.utils.alloc_type(new_len, t{1}, (-1,))\n'
                .format(out, i))
    lefnz__mpnyv += '  curr_ind = 0\n'
    lefnz__mpnyv += '  for i in range(old_len):\n'
    lefnz__mpnyv += '    if {}:\n'.format(ietvk__rcmi)
    for i in range(hzj__nwzi):
        lefnz__mpnyv += '      if isna(data[{}], i):\n'.format(i)
        lefnz__mpnyv += '        setna({}, curr_ind)\n'.format(tws__deav[i])
        lefnz__mpnyv += '      else:\n'
        lefnz__mpnyv += '        {}[curr_ind] = data[{}][i]\n'.format(tws__deav
            [i], i)
    lefnz__mpnyv += '      curr_ind += 1\n'
    lefnz__mpnyv += '  return {}\n'.format(', '.join(tws__deav))
    irkl__lbha = {}
    tgip__ultul = {'t{}'.format(i): ggdd__kikjw for i, ggdd__kikjw in
        enumerate(data.types)}
    tgip__ultul.update({'isna': isna, 'setna': setna, 'init_nested_counts':
        bodo.utils.indexing.init_nested_counts, 'add_nested_counts': bodo.
        utils.indexing.add_nested_counts, 'bodo': bodo})
    exec(lefnz__mpnyv, tgip__ultul, irkl__lbha)
    jaax__bdot = irkl__lbha['_dropna_imp']
    return jaax__bdot


def get(arr, ind):
    return pd.Series(arr).str.get(ind)


@overload(get, no_unliteral=True)
def overload_get(arr, ind):
    if isinstance(arr, ArrayItemArrayType):
        ijo__qlkqh = arr.dtype
        dlm__tkq = ijo__qlkqh.dtype

        def get_arr_item(arr, ind):
            n = len(arr)
            eyyju__cnsbi = init_nested_counts(dlm__tkq)
            for k in range(n):
                if bodo.libs.array_kernels.isna(arr, k):
                    continue
                val = arr[k]
                if not len(val) > ind >= -len(val
                    ) or bodo.libs.array_kernels.isna(val, ind):
                    continue
                eyyju__cnsbi = add_nested_counts(eyyju__cnsbi, val[ind])
            imwwn__kdx = bodo.utils.utils.alloc_type(n, ijo__qlkqh,
                eyyju__cnsbi)
            for vuh__zqnr in range(n):
                if bodo.libs.array_kernels.isna(arr, vuh__zqnr):
                    setna(imwwn__kdx, vuh__zqnr)
                    continue
                val = arr[vuh__zqnr]
                if not len(val) > ind >= -len(val
                    ) or bodo.libs.array_kernels.isna(val, ind):
                    setna(imwwn__kdx, vuh__zqnr)
                    continue
                imwwn__kdx[vuh__zqnr] = val[ind]
            return imwwn__kdx
        return get_arr_item


def _is_same_categorical_array_type(arr_types):
    from bodo.hiframes.pd_categorical_ext import _to_readonly
    if not isinstance(arr_types, types.BaseTuple) or len(arr_types) == 0:
        return False
    uhpt__xgbtn = _to_readonly(arr_types.types[0])
    return all(isinstance(ggdd__kikjw, CategoricalArrayType) and 
        _to_readonly(ggdd__kikjw) == uhpt__xgbtn for ggdd__kikjw in
        arr_types.types)


def concat(arr_list):
    return pd.concat(arr_list)


@overload(concat, no_unliteral=True)
def concat_overload(arr_list):
    if isinstance(arr_list, bodo.NullableTupleType):
        return lambda arr_list: bodo.libs.array_kernels.concat(arr_list._data)
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, ArrayItemArrayType):
        qvco__twxmt = arr_list.dtype.dtype

        def array_item_concat_impl(arr_list):
            advyo__kqwun = 0
            mhvc__ags = []
            for A in arr_list:
                hbt__bxf = len(A)
                bodo.libs.array_item_arr_ext.trim_excess_data(A)
                mhvc__ags.append(bodo.libs.array_item_arr_ext.get_data(A))
                advyo__kqwun += hbt__bxf
            dnwi__tno = np.empty(advyo__kqwun + 1, offset_type)
            gawd__vidv = bodo.libs.array_kernels.concat(mhvc__ags)
            nxue__ciubq = np.empty(advyo__kqwun + 7 >> 3, np.uint8)
            ayllq__pwm = 0
            eywhu__zjh = 0
            for A in arr_list:
                ytdn__apdu = bodo.libs.array_item_arr_ext.get_offsets(A)
                rtfmt__wule = bodo.libs.array_item_arr_ext.get_null_bitmap(A)
                hbt__bxf = len(A)
                zgd__gunxd = ytdn__apdu[hbt__bxf]
                for i in range(hbt__bxf):
                    dnwi__tno[i + ayllq__pwm] = ytdn__apdu[i] + eywhu__zjh
                    yex__bagn = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        rtfmt__wule, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(nxue__ciubq, i +
                        ayllq__pwm, yex__bagn)
                ayllq__pwm += hbt__bxf
                eywhu__zjh += zgd__gunxd
            dnwi__tno[ayllq__pwm] = eywhu__zjh
            imwwn__kdx = bodo.libs.array_item_arr_ext.init_array_item_array(
                advyo__kqwun, gawd__vidv, dnwi__tno, nxue__ciubq)
            return imwwn__kdx
        return array_item_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, bodo.StructArrayType):
        tcm__kbyp = arr_list.dtype.names
        lefnz__mpnyv = 'def struct_array_concat_impl(arr_list):\n'
        lefnz__mpnyv += f'    n_all = 0\n'
        for i in range(len(tcm__kbyp)):
            lefnz__mpnyv += f'    concat_list{i} = []\n'
        lefnz__mpnyv += '    for A in arr_list:\n'
        lefnz__mpnyv += (
            '        data_tuple = bodo.libs.struct_arr_ext.get_data(A)\n')
        for i in range(len(tcm__kbyp)):
            lefnz__mpnyv += f'        concat_list{i}.append(data_tuple[{i}])\n'
        lefnz__mpnyv += '        n_all += len(A)\n'
        lefnz__mpnyv += '    n_bytes = (n_all + 7) >> 3\n'
        lefnz__mpnyv += '    new_mask = np.empty(n_bytes, np.uint8)\n'
        lefnz__mpnyv += '    curr_bit = 0\n'
        lefnz__mpnyv += '    for A in arr_list:\n'
        lefnz__mpnyv += (
            '        old_mask = bodo.libs.struct_arr_ext.get_null_bitmap(A)\n')
        lefnz__mpnyv += '        for j in range(len(A)):\n'
        lefnz__mpnyv += (
            '            bit = bodo.libs.int_arr_ext.get_bit_bitmap_arr(old_mask, j)\n'
            )
        lefnz__mpnyv += """            bodo.libs.int_arr_ext.set_bit_to_arr(new_mask, curr_bit, bit)
"""
        lefnz__mpnyv += '            curr_bit += 1\n'
        lefnz__mpnyv += (
            '    return bodo.libs.struct_arr_ext.init_struct_arr(\n')
        qbqu__ntqr = ', '.join([
            f'bodo.libs.array_kernels.concat(concat_list{i})' for i in
            range(len(tcm__kbyp))])
        lefnz__mpnyv += f'        ({qbqu__ntqr},),\n'
        lefnz__mpnyv += '        new_mask,\n'
        lefnz__mpnyv += f'        {tcm__kbyp},\n'
        lefnz__mpnyv += '    )\n'
        irkl__lbha = {}
        exec(lefnz__mpnyv, {'bodo': bodo, 'np': np}, irkl__lbha)
        return irkl__lbha['struct_array_concat_impl']
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == datetime_date_array_type:

        def datetime_date_array_concat_impl(arr_list):
            woue__kzhau = 0
            for A in arr_list:
                woue__kzhau += len(A)
            elaq__hlvux = (bodo.hiframes.datetime_date_ext.
                alloc_datetime_date_array(woue__kzhau))
            bvbi__xjfb = 0
            for A in arr_list:
                for i in range(len(A)):
                    elaq__hlvux._data[i + bvbi__xjfb] = A._data[i]
                    yex__bagn = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A.
                        _null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(elaq__hlvux.
                        _null_bitmap, i + bvbi__xjfb, yex__bagn)
                bvbi__xjfb += len(A)
            return elaq__hlvux
        return datetime_date_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == datetime_timedelta_array_type:

        def datetime_timedelta_array_concat_impl(arr_list):
            woue__kzhau = 0
            for A in arr_list:
                woue__kzhau += len(A)
            elaq__hlvux = (bodo.hiframes.datetime_timedelta_ext.
                alloc_datetime_timedelta_array(woue__kzhau))
            bvbi__xjfb = 0
            for A in arr_list:
                for i in range(len(A)):
                    elaq__hlvux._days_data[i + bvbi__xjfb] = A._days_data[i]
                    elaq__hlvux._seconds_data[i + bvbi__xjfb
                        ] = A._seconds_data[i]
                    elaq__hlvux._microseconds_data[i + bvbi__xjfb
                        ] = A._microseconds_data[i]
                    yex__bagn = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A.
                        _null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(elaq__hlvux.
                        _null_bitmap, i + bvbi__xjfb, yex__bagn)
                bvbi__xjfb += len(A)
            return elaq__hlvux
        return datetime_timedelta_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, DecimalArrayType):
        mct__gxpg = arr_list.dtype.precision
        jexvx__fzy = arr_list.dtype.scale

        def decimal_array_concat_impl(arr_list):
            woue__kzhau = 0
            for A in arr_list:
                woue__kzhau += len(A)
            elaq__hlvux = bodo.libs.decimal_arr_ext.alloc_decimal_array(
                woue__kzhau, mct__gxpg, jexvx__fzy)
            bvbi__xjfb = 0
            for A in arr_list:
                for i in range(len(A)):
                    elaq__hlvux._data[i + bvbi__xjfb] = A._data[i]
                    yex__bagn = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A.
                        _null_bitmap, i)
                    bodo.libs.int_arr_ext.set_bit_to_arr(elaq__hlvux.
                        _null_bitmap, i + bvbi__xjfb, yex__bagn)
                bvbi__xjfb += len(A)
            return elaq__hlvux
        return decimal_array_concat_impl
    if isinstance(arr_list, (types.UniTuple, types.List)) and (is_str_arr_type
        (arr_list.dtype) or arr_list.dtype == bodo.binary_array_type
        ) or isinstance(arr_list, types.BaseTuple) and all(is_str_arr_type(
        ggdd__kikjw) for ggdd__kikjw in arr_list.types):
        if isinstance(arr_list, types.BaseTuple):
            yus__oay = arr_list.types[0]
        else:
            yus__oay = arr_list.dtype
        yus__oay = to_str_arr_if_dict_array(yus__oay)

        def impl_str(arr_list):
            arr_list = decode_if_dict_array(arr_list)
            ugthz__qieas = 0
            wvoed__kbpp = 0
            for A in arr_list:
                arr = A
                ugthz__qieas += len(arr)
                wvoed__kbpp += bodo.libs.str_arr_ext.num_total_chars(arr)
            imwwn__kdx = bodo.utils.utils.alloc_type(ugthz__qieas, yus__oay,
                (wvoed__kbpp,))
            bodo.libs.str_arr_ext.set_null_bits_to_value(imwwn__kdx, -1)
            fic__kuf = 0
            corwr__rwsmz = 0
            for A in arr_list:
                arr = A
                bodo.libs.str_arr_ext.set_string_array_range(imwwn__kdx,
                    arr, fic__kuf, corwr__rwsmz)
                fic__kuf += len(arr)
                corwr__rwsmz += bodo.libs.str_arr_ext.num_total_chars(arr)
            return imwwn__kdx
        return impl_str
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, IntegerArrayType) or isinstance(arr_list, types.
        BaseTuple) and all(isinstance(ggdd__kikjw.dtype, types.Integer) for
        ggdd__kikjw in arr_list.types) and any(isinstance(ggdd__kikjw,
        IntegerArrayType) for ggdd__kikjw in arr_list.types):

        def impl_int_arr_list(arr_list):
            lhn__ipbph = convert_to_nullable_tup(arr_list)
            gbrg__pjje = []
            kjhwv__rzhss = 0
            for A in lhn__ipbph:
                gbrg__pjje.append(A._data)
                kjhwv__rzhss += len(A)
            gawd__vidv = bodo.libs.array_kernels.concat(gbrg__pjje)
            zmyrl__hqs = kjhwv__rzhss + 7 >> 3
            kdi__qmgjt = np.empty(zmyrl__hqs, np.uint8)
            uxovs__zbbw = 0
            for A in lhn__ipbph:
                lgij__jqac = A._null_bitmap
                for vuh__zqnr in range(len(A)):
                    yex__bagn = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        lgij__jqac, vuh__zqnr)
                    bodo.libs.int_arr_ext.set_bit_to_arr(kdi__qmgjt,
                        uxovs__zbbw, yex__bagn)
                    uxovs__zbbw += 1
            return bodo.libs.int_arr_ext.init_integer_array(gawd__vidv,
                kdi__qmgjt)
        return impl_int_arr_list
    if isinstance(arr_list, (types.UniTuple, types.List)
        ) and arr_list.dtype == boolean_array or isinstance(arr_list, types
        .BaseTuple) and all(ggdd__kikjw.dtype == types.bool_ for
        ggdd__kikjw in arr_list.types) and any(ggdd__kikjw == boolean_array for
        ggdd__kikjw in arr_list.types):

        def impl_bool_arr_list(arr_list):
            lhn__ipbph = convert_to_nullable_tup(arr_list)
            gbrg__pjje = []
            kjhwv__rzhss = 0
            for A in lhn__ipbph:
                gbrg__pjje.append(A._data)
                kjhwv__rzhss += len(A)
            gawd__vidv = bodo.libs.array_kernels.concat(gbrg__pjje)
            zmyrl__hqs = kjhwv__rzhss + 7 >> 3
            kdi__qmgjt = np.empty(zmyrl__hqs, np.uint8)
            uxovs__zbbw = 0
            for A in lhn__ipbph:
                lgij__jqac = A._null_bitmap
                for vuh__zqnr in range(len(A)):
                    yex__bagn = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        lgij__jqac, vuh__zqnr)
                    bodo.libs.int_arr_ext.set_bit_to_arr(kdi__qmgjt,
                        uxovs__zbbw, yex__bagn)
                    uxovs__zbbw += 1
            return bodo.libs.bool_arr_ext.init_bool_array(gawd__vidv,
                kdi__qmgjt)
        return impl_bool_arr_list
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, CategoricalArrayType):

        def cat_array_concat_impl(arr_list):
            sbic__afnk = []
            for A in arr_list:
                sbic__afnk.append(A.codes)
            return init_categorical_array(bodo.libs.array_kernels.concat(
                sbic__afnk), arr_list[0].dtype)
        return cat_array_concat_impl
    if _is_same_categorical_array_type(arr_list):
        sgsa__xvv = ', '.join(f'arr_list[{i}].codes' for i in range(len(
            arr_list)))
        lefnz__mpnyv = 'def impl(arr_list):\n'
        lefnz__mpnyv += f"""    return init_categorical_array(bodo.libs.array_kernels.concat(({sgsa__xvv},)), arr_list[0].dtype)
"""
        vbqoq__bxv = {}
        exec(lefnz__mpnyv, {'bodo': bodo, 'init_categorical_array':
            init_categorical_array}, vbqoq__bxv)
        return vbqoq__bxv['impl']
    if isinstance(arr_list, types.List) and isinstance(arr_list.dtype,
        types.Array) and arr_list.dtype.ndim == 1:
        dtype = arr_list.dtype.dtype

        def impl_np_arr_list(arr_list):
            kjhwv__rzhss = 0
            for A in arr_list:
                kjhwv__rzhss += len(A)
            imwwn__kdx = np.empty(kjhwv__rzhss, dtype)
            zmp__oizr = 0
            for A in arr_list:
                n = len(A)
                imwwn__kdx[zmp__oizr:zmp__oizr + n] = A
                zmp__oizr += n
            return imwwn__kdx
        return impl_np_arr_list
    if isinstance(arr_list, types.BaseTuple) and any(isinstance(ggdd__kikjw,
        (types.Array, IntegerArrayType)) and isinstance(ggdd__kikjw.dtype,
        types.Integer) for ggdd__kikjw in arr_list.types) and any(
        isinstance(ggdd__kikjw, types.Array) and isinstance(ggdd__kikjw.
        dtype, types.Float) for ggdd__kikjw in arr_list.types):
        return lambda arr_list: np.concatenate(astype_float_tup(arr_list))
    if isinstance(arr_list, (types.UniTuple, types.List)) and isinstance(
        arr_list.dtype, bodo.MapArrayType):

        def impl_map_arr_list(arr_list):
            zqqsr__jbu = []
            for A in arr_list:
                zqqsr__jbu.append(A._data)
            weh__irow = bodo.libs.array_kernels.concat(zqqsr__jbu)
            miw__twwz = bodo.libs.map_arr_ext.init_map_arr(weh__irow)
            return miw__twwz
        return impl_map_arr_list
    for dzc__pql in arr_list:
        if not isinstance(dzc__pql, types.Array):
            raise_bodo_error(f'concat of array types {arr_list} not supported')
    return lambda arr_list: np.concatenate(arr_list)


def astype_float_tup(arr_tup):
    return tuple(ggdd__kikjw.astype(np.float64) for ggdd__kikjw in arr_tup)


@overload(astype_float_tup, no_unliteral=True)
def overload_astype_float_tup(arr_tup):
    assert isinstance(arr_tup, types.BaseTuple)
    iqi__ahr = len(arr_tup.types)
    lefnz__mpnyv = 'def f(arr_tup):\n'
    lefnz__mpnyv += '  return ({}{})\n'.format(','.join(
        'arr_tup[{}].astype(np.float64)'.format(i) for i in range(iqi__ahr)
        ), ',' if iqi__ahr == 1 else '')
    irkl__lbha = {}
    exec(lefnz__mpnyv, {'np': np}, irkl__lbha)
    jkpe__vmt = irkl__lbha['f']
    return jkpe__vmt


def convert_to_nullable_tup(arr_tup):
    return arr_tup


@overload(convert_to_nullable_tup, no_unliteral=True)
def overload_convert_to_nullable_tup(arr_tup):
    if isinstance(arr_tup, (types.UniTuple, types.List)) and isinstance(arr_tup
        .dtype, (IntegerArrayType, BooleanArrayType)):
        return lambda arr_tup: arr_tup
    assert isinstance(arr_tup, types.BaseTuple)
    iqi__ahr = len(arr_tup.types)
    akp__ypdkt = find_common_np_dtype(arr_tup.types)
    dlm__tkq = None
    opwvg__zavv = ''
    if isinstance(akp__ypdkt, types.Integer):
        dlm__tkq = bodo.libs.int_arr_ext.IntDtype(akp__ypdkt)
        opwvg__zavv = '.astype(out_dtype, False)'
    lefnz__mpnyv = 'def f(arr_tup):\n'
    lefnz__mpnyv += '  return ({}{})\n'.format(','.join(
        'bodo.utils.conversion.coerce_to_array(arr_tup[{}], use_nullable_array=True){}'
        .format(i, opwvg__zavv) for i in range(iqi__ahr)), ',' if iqi__ahr ==
        1 else '')
    irkl__lbha = {}
    exec(lefnz__mpnyv, {'bodo': bodo, 'out_dtype': dlm__tkq}, irkl__lbha)
    vdgr__ctjd = irkl__lbha['f']
    return vdgr__ctjd


def nunique(A, dropna):
    return len(set(A))


def nunique_parallel(A, dropna):
    return len(set(A))


@overload(nunique, no_unliteral=True)
def nunique_overload(A, dropna):

    def nunique_seq(A, dropna):
        s, ypbv__fndq = build_set_seen_na(A)
        return len(s) + int(not dropna and ypbv__fndq)
    return nunique_seq


@overload(nunique_parallel, no_unliteral=True)
def nunique_overload_parallel(A, dropna):
    sum_op = bodo.libs.distributed_api.Reduce_Type.Sum.value

    def nunique_par(A, dropna):
        uvtas__swvc = bodo.libs.array_kernels.unique(A, dropna, parallel=True)
        bjsim__lek = len(uvtas__swvc)
        return bodo.libs.distributed_api.dist_reduce(bjsim__lek, np.int32(
            sum_op))
    return nunique_par


def unique(A, dropna=False, parallel=False):
    return np.array([izze__nmo for izze__nmo in set(A)]).astype(A.dtype)


def cummin(A):
    return A


@overload(cummin, no_unliteral=True)
def cummin_overload(A):
    if isinstance(A.dtype, types.Float):
        tjmmi__jksuz = np.finfo(A.dtype(1).dtype).max
    else:
        tjmmi__jksuz = np.iinfo(A.dtype(1).dtype).max

    def impl(A):
        n = len(A)
        imwwn__kdx = np.empty(n, A.dtype)
        splj__rffx = tjmmi__jksuz
        for i in range(n):
            splj__rffx = min(splj__rffx, A[i])
            imwwn__kdx[i] = splj__rffx
        return imwwn__kdx
    return impl


def cummax(A):
    return A


@overload(cummax, no_unliteral=True)
def cummax_overload(A):
    if isinstance(A.dtype, types.Float):
        tjmmi__jksuz = np.finfo(A.dtype(1).dtype).min
    else:
        tjmmi__jksuz = np.iinfo(A.dtype(1).dtype).min

    def impl(A):
        n = len(A)
        imwwn__kdx = np.empty(n, A.dtype)
        splj__rffx = tjmmi__jksuz
        for i in range(n):
            splj__rffx = max(splj__rffx, A[i])
            imwwn__kdx[i] = splj__rffx
        return imwwn__kdx
    return impl


@overload(unique, no_unliteral=True)
def unique_overload(A, dropna=False, parallel=False):

    def unique_impl(A, dropna=False, parallel=False):
        njl__hjo = arr_info_list_to_table([array_to_info(A)])
        wcbsi__xxp = 1
        wixfu__zvv = 0
        lnvay__hwh = drop_duplicates_table(njl__hjo, parallel, wcbsi__xxp,
            wixfu__zvv, dropna, True)
        imwwn__kdx = info_to_array(info_from_table(lnvay__hwh, 0), A)
        delete_table(njl__hjo)
        delete_table(lnvay__hwh)
        return imwwn__kdx
    return unique_impl


def explode(arr, index_arr):
    return pd.Series(arr, index_arr).explode()


@overload(explode, no_unliteral=True)
def overload_explode(arr, index_arr):
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type
    qvco__twxmt = bodo.utils.typing.to_nullable_type(arr.dtype)
    ypp__wpgvf = index_arr
    cvonf__cgxw = ypp__wpgvf.dtype

    def impl(arr, index_arr):
        n = len(arr)
        eyyju__cnsbi = init_nested_counts(qvco__twxmt)
        wisjf__puec = init_nested_counts(cvonf__cgxw)
        for i in range(n):
            dek__hzsiq = index_arr[i]
            if isna(arr, i):
                eyyju__cnsbi = (eyyju__cnsbi[0] + 1,) + eyyju__cnsbi[1:]
                wisjf__puec = add_nested_counts(wisjf__puec, dek__hzsiq)
                continue
            dvks__gew = arr[i]
            if len(dvks__gew) == 0:
                eyyju__cnsbi = (eyyju__cnsbi[0] + 1,) + eyyju__cnsbi[1:]
                wisjf__puec = add_nested_counts(wisjf__puec, dek__hzsiq)
                continue
            eyyju__cnsbi = add_nested_counts(eyyju__cnsbi, dvks__gew)
            for ksdfn__dcf in range(len(dvks__gew)):
                wisjf__puec = add_nested_counts(wisjf__puec, dek__hzsiq)
        imwwn__kdx = bodo.utils.utils.alloc_type(eyyju__cnsbi[0],
            qvco__twxmt, eyyju__cnsbi[1:])
        tqbx__inna = bodo.utils.utils.alloc_type(eyyju__cnsbi[0],
            ypp__wpgvf, wisjf__puec)
        eywhu__zjh = 0
        for i in range(n):
            if isna(arr, i):
                setna(imwwn__kdx, eywhu__zjh)
                tqbx__inna[eywhu__zjh] = index_arr[i]
                eywhu__zjh += 1
                continue
            dvks__gew = arr[i]
            zgd__gunxd = len(dvks__gew)
            if zgd__gunxd == 0:
                setna(imwwn__kdx, eywhu__zjh)
                tqbx__inna[eywhu__zjh] = index_arr[i]
                eywhu__zjh += 1
                continue
            imwwn__kdx[eywhu__zjh:eywhu__zjh + zgd__gunxd] = dvks__gew
            tqbx__inna[eywhu__zjh:eywhu__zjh + zgd__gunxd] = index_arr[i]
            eywhu__zjh += zgd__gunxd
        return imwwn__kdx, tqbx__inna
    return impl


def explode_no_index(arr):
    return pd.Series(arr).explode()


@overload(explode_no_index, no_unliteral=True)
def overload_explode_no_index(arr, counts):
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type
    qvco__twxmt = bodo.utils.typing.to_nullable_type(arr.dtype)

    def impl(arr, counts):
        n = len(arr)
        eyyju__cnsbi = init_nested_counts(qvco__twxmt)
        for i in range(n):
            if isna(arr, i):
                eyyju__cnsbi = (eyyju__cnsbi[0] + 1,) + eyyju__cnsbi[1:]
                asytz__hlgxr = 1
            else:
                dvks__gew = arr[i]
                vebf__gju = len(dvks__gew)
                if vebf__gju == 0:
                    eyyju__cnsbi = (eyyju__cnsbi[0] + 1,) + eyyju__cnsbi[1:]
                    asytz__hlgxr = 1
                    continue
                else:
                    eyyju__cnsbi = add_nested_counts(eyyju__cnsbi, dvks__gew)
                    asytz__hlgxr = vebf__gju
            if counts[i] != asytz__hlgxr:
                raise ValueError(
                    'DataFrame.explode(): columns must have matching element counts'
                    )
        imwwn__kdx = bodo.utils.utils.alloc_type(eyyju__cnsbi[0],
            qvco__twxmt, eyyju__cnsbi[1:])
        eywhu__zjh = 0
        for i in range(n):
            if isna(arr, i):
                setna(imwwn__kdx, eywhu__zjh)
                eywhu__zjh += 1
                continue
            dvks__gew = arr[i]
            zgd__gunxd = len(dvks__gew)
            if zgd__gunxd == 0:
                setna(imwwn__kdx, eywhu__zjh)
                eywhu__zjh += 1
                continue
            imwwn__kdx[eywhu__zjh:eywhu__zjh + zgd__gunxd] = dvks__gew
            eywhu__zjh += zgd__gunxd
        return imwwn__kdx
    return impl


def get_arr_lens(arr, na_empty_as_one=True):
    return [len(aka__unwyy) for aka__unwyy in arr]


@overload(get_arr_lens, inline='always', no_unliteral=True)
def overload_get_arr_lens(arr, na_empty_as_one=True):
    na_empty_as_one = get_overload_const_bool(na_empty_as_one)
    assert isinstance(arr, ArrayItemArrayType
        ) or arr == string_array_split_view_type or is_str_arr_type(arr
        ) and not na_empty_as_one, f'get_arr_lens: invalid input array type {arr}'
    if na_empty_as_one:
        cqu__gqbz = 'np.empty(n, np.int64)'
        jpu__zdn = 'out_arr[i] = 1'
        hwre__kmjyb = 'max(len(arr[i]), 1)'
    else:
        cqu__gqbz = 'bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)'
        jpu__zdn = 'bodo.libs.array_kernels.setna(out_arr, i)'
        hwre__kmjyb = 'len(arr[i])'
    lefnz__mpnyv = f"""def impl(arr, na_empty_as_one=True):
    numba.parfors.parfor.init_prange()
    n = len(arr)
    out_arr = {cqu__gqbz}
    for i in numba.parfors.parfor.internal_prange(n):
        if bodo.libs.array_kernels.isna(arr, i):
            {jpu__zdn}
        else:
            out_arr[i] = {hwre__kmjyb}
    return out_arr
    """
    irkl__lbha = {}
    exec(lefnz__mpnyv, {'bodo': bodo, 'numba': numba, 'np': np}, irkl__lbha)
    impl = irkl__lbha['impl']
    return impl


def explode_str_split(arr, pat, n, index_arr):
    return pd.Series(arr, index_arr).str.split(pat, n).explode()


@overload(explode_str_split, no_unliteral=True)
def overload_explode_str_split(arr, pat, n, index_arr):
    assert is_str_arr_type(arr
        ), f'explode_str_split: string array expected, not {arr}'
    ypp__wpgvf = index_arr
    cvonf__cgxw = ypp__wpgvf.dtype

    def impl(arr, pat, n, index_arr):
        wnxvt__olaq = pat is not None and len(pat) > 1
        if wnxvt__olaq:
            owc__isq = re.compile(pat)
            if n == -1:
                n = 0
        elif n == 0:
            n = -1
        niqvw__xhzx = len(arr)
        ugthz__qieas = 0
        wvoed__kbpp = 0
        wisjf__puec = init_nested_counts(cvonf__cgxw)
        for i in range(niqvw__xhzx):
            dek__hzsiq = index_arr[i]
            if bodo.libs.array_kernels.isna(arr, i):
                ugthz__qieas += 1
                wisjf__puec = add_nested_counts(wisjf__puec, dek__hzsiq)
                continue
            if wnxvt__olaq:
                yvnvz__cjgy = owc__isq.split(arr[i], maxsplit=n)
            else:
                yvnvz__cjgy = arr[i].split(pat, n)
            ugthz__qieas += len(yvnvz__cjgy)
            for s in yvnvz__cjgy:
                wisjf__puec = add_nested_counts(wisjf__puec, dek__hzsiq)
                wvoed__kbpp += bodo.libs.str_arr_ext.get_utf8_size(s)
        imwwn__kdx = bodo.libs.str_arr_ext.pre_alloc_string_array(ugthz__qieas,
            wvoed__kbpp)
        tqbx__inna = bodo.utils.utils.alloc_type(ugthz__qieas, ypp__wpgvf,
            wisjf__puec)
        umw__tkxb = 0
        for vuh__zqnr in range(niqvw__xhzx):
            if isna(arr, vuh__zqnr):
                imwwn__kdx[umw__tkxb] = ''
                bodo.libs.array_kernels.setna(imwwn__kdx, umw__tkxb)
                tqbx__inna[umw__tkxb] = index_arr[vuh__zqnr]
                umw__tkxb += 1
                continue
            if wnxvt__olaq:
                yvnvz__cjgy = owc__isq.split(arr[vuh__zqnr], maxsplit=n)
            else:
                yvnvz__cjgy = arr[vuh__zqnr].split(pat, n)
            rpiaq__sfg = len(yvnvz__cjgy)
            imwwn__kdx[umw__tkxb:umw__tkxb + rpiaq__sfg] = yvnvz__cjgy
            tqbx__inna[umw__tkxb:umw__tkxb + rpiaq__sfg] = index_arr[vuh__zqnr]
            umw__tkxb += rpiaq__sfg
        return imwwn__kdx, tqbx__inna
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
            imwwn__kdx = np.empty(n, dtype)
            for i in numba.parfors.parfor.internal_prange(n):
                imwwn__kdx[i] = np.nan
            return imwwn__kdx
        return impl_float
    auprf__snuv = to_str_arr_if_dict_array(arr)

    def impl(n, arr):
        numba.parfors.parfor.init_prange()
        imwwn__kdx = bodo.utils.utils.alloc_type(n, auprf__snuv, (0,))
        for i in numba.parfors.parfor.internal_prange(n):
            setna(imwwn__kdx, i)
        return imwwn__kdx
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
    qswg__wmh = A
    if A == types.Array(types.uint8, 1, 'C'):

        def impl_char(A, old_size, new_len):
            imwwn__kdx = bodo.utils.utils.alloc_type(new_len, qswg__wmh)
            bodo.libs.str_arr_ext.str_copy_ptr(imwwn__kdx.ctypes, 0, A.
                ctypes, old_size)
            return imwwn__kdx
        return impl_char

    def impl(A, old_size, new_len):
        imwwn__kdx = bodo.utils.utils.alloc_type(new_len, qswg__wmh, (-1,))
        imwwn__kdx[:old_size] = A[:old_size]
        return imwwn__kdx
    return impl


@register_jitable
def calc_nitems(start, stop, step):
    puqhd__snpex = math.ceil((stop - start) / step)
    return int(max(puqhd__snpex, 0))


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
    if any(isinstance(izze__nmo, types.Complex) for izze__nmo in args):

        def arange_4(start, stop, step, dtype):
            numba.parfors.parfor.init_prange()
            mfe__nlb = (stop - start) / step
            puqhd__snpex = math.ceil(mfe__nlb.real)
            phfv__biuy = math.ceil(mfe__nlb.imag)
            iybrq__rsyb = int(max(min(phfv__biuy, puqhd__snpex), 0))
            arr = np.empty(iybrq__rsyb, dtype)
            for i in numba.parfors.parfor.internal_prange(iybrq__rsyb):
                arr[i] = start + i * step
            return arr
    else:

        def arange_4(start, stop, step, dtype):
            numba.parfors.parfor.init_prange()
            iybrq__rsyb = bodo.libs.array_kernels.calc_nitems(start, stop, step
                )
            arr = np.empty(iybrq__rsyb, dtype)
            for i in numba.parfors.parfor.internal_prange(iybrq__rsyb):
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
        vaw__ijwee = arr,
        if not inplace:
            vaw__ijwee = arr.copy(),
        wdts__ruh = bodo.libs.str_arr_ext.to_list_if_immutable_arr(vaw__ijwee)
        oyu__zbg = bodo.libs.str_arr_ext.to_list_if_immutable_arr(data, True)
        bodo.libs.timsort.sort(wdts__ruh, 0, n, oyu__zbg)
        if not ascending:
            bodo.libs.timsort.reverseRange(wdts__ruh, 0, n, oyu__zbg)
        bodo.libs.str_arr_ext.cp_str_list_to_array(vaw__ijwee, wdts__ruh)
        return vaw__ijwee[0]
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
        miw__twwz = []
        for i in range(n):
            if A[i]:
                miw__twwz.append(i + offset)
        return np.array(miw__twwz, np.int64),
    return impl


def ffill_bfill_arr(arr):
    return arr


@overload(ffill_bfill_arr, no_unliteral=True)
def ffill_bfill_overload(A, method, parallel=False):
    qswg__wmh = element_type(A)
    if qswg__wmh == types.unicode_type:
        null_value = '""'
    elif qswg__wmh == types.bool_:
        null_value = 'False'
    elif qswg__wmh == bodo.datetime64ns:
        null_value = (
            'bodo.utils.conversion.unbox_if_timestamp(pd.to_datetime(0))')
    elif qswg__wmh == bodo.timedelta64ns:
        null_value = (
            'bodo.utils.conversion.unbox_if_timestamp(pd.to_timedelta(0))')
    else:
        null_value = '0'
    umw__tkxb = 'i'
    ajldm__nwbjs = False
    rim__iqdm = get_overload_const_str(method)
    if rim__iqdm in ('ffill', 'pad'):
        jkifp__tby = 'n'
        send_right = True
    elif rim__iqdm in ('backfill', 'bfill'):
        jkifp__tby = 'n-1, -1, -1'
        send_right = False
        if qswg__wmh == types.unicode_type:
            umw__tkxb = '(n - 1) - i'
            ajldm__nwbjs = True
    lefnz__mpnyv = 'def impl(A, method, parallel=False):\n'
    lefnz__mpnyv += '  A = decode_if_dict_array(A)\n'
    lefnz__mpnyv += '  has_last_value = False\n'
    lefnz__mpnyv += f'  last_value = {null_value}\n'
    lefnz__mpnyv += '  if parallel:\n'
    lefnz__mpnyv += '    rank = bodo.libs.distributed_api.get_rank()\n'
    lefnz__mpnyv += '    n_pes = bodo.libs.distributed_api.get_size()\n'
    lefnz__mpnyv += f"""    has_last_value, last_value = null_border_icomm(A, rank, n_pes, {null_value}, {send_right})
"""
    lefnz__mpnyv += '  n = len(A)\n'
    lefnz__mpnyv += '  out_arr = bodo.utils.utils.alloc_type(n, A, (-1,))\n'
    lefnz__mpnyv += f'  for i in range({jkifp__tby}):\n'
    lefnz__mpnyv += (
        '    if (bodo.libs.array_kernels.isna(A, i) and not has_last_value):\n'
        )
    lefnz__mpnyv += (
        f'      bodo.libs.array_kernels.setna(out_arr, {umw__tkxb})\n')
    lefnz__mpnyv += '      continue\n'
    lefnz__mpnyv += '    s = A[i]\n'
    lefnz__mpnyv += '    if bodo.libs.array_kernels.isna(A, i):\n'
    lefnz__mpnyv += '      s = last_value\n'
    lefnz__mpnyv += f'    out_arr[{umw__tkxb}] = s\n'
    lefnz__mpnyv += '    last_value = s\n'
    lefnz__mpnyv += '    has_last_value = True\n'
    if ajldm__nwbjs:
        lefnz__mpnyv += '  return out_arr[::-1]\n'
    else:
        lefnz__mpnyv += '  return out_arr\n'
    wyik__kkkl = {}
    exec(lefnz__mpnyv, {'bodo': bodo, 'numba': numba, 'pd': pd,
        'null_border_icomm': null_border_icomm, 'decode_if_dict_array':
        decode_if_dict_array}, wyik__kkkl)
    impl = wyik__kkkl['impl']
    return impl


@register_jitable(cache=True)
def null_border_icomm(in_arr, rank, n_pes, null_value, send_right=True):
    if send_right:
        dcf__lwkbo = 0
        rwi__gikfz = n_pes - 1
        ccav__lvq = np.int32(rank + 1)
        xej__ynyad = np.int32(rank - 1)
        pymjh__cgz = len(in_arr) - 1
        ddij__mcch = -1
        fzqo__tsyjd = -1
    else:
        dcf__lwkbo = n_pes - 1
        rwi__gikfz = 0
        ccav__lvq = np.int32(rank - 1)
        xej__ynyad = np.int32(rank + 1)
        pymjh__cgz = 0
        ddij__mcch = len(in_arr)
        fzqo__tsyjd = 1
    ufv__zzjab = np.int32(bodo.hiframes.rolling.comm_border_tag)
    ffsu__pke = np.empty(1, dtype=np.bool_)
    cnyrc__dpvf = bodo.utils.utils.alloc_type(1, in_arr, (-1,))
    wxny__kfodi = np.empty(1, dtype=np.bool_)
    gcii__nktv = bodo.utils.utils.alloc_type(1, in_arr, (-1,))
    lzsp__gowmc = False
    pmjul__zlgn = null_value
    for i in range(pymjh__cgz, ddij__mcch, fzqo__tsyjd):
        if not isna(in_arr, i):
            lzsp__gowmc = True
            pmjul__zlgn = in_arr[i]
            break
    if rank != dcf__lwkbo:
        bwssf__asihi = bodo.libs.distributed_api.irecv(ffsu__pke, 1,
            xej__ynyad, ufv__zzjab, True)
        bodo.libs.distributed_api.wait(bwssf__asihi, True)
        pprxf__pla = bodo.libs.distributed_api.irecv(cnyrc__dpvf, 1,
            xej__ynyad, ufv__zzjab, True)
        bodo.libs.distributed_api.wait(pprxf__pla, True)
        xqk__ymsc = ffsu__pke[0]
        agq__ijfiw = cnyrc__dpvf[0]
    else:
        xqk__ymsc = False
        agq__ijfiw = null_value
    if lzsp__gowmc:
        wxny__kfodi[0] = lzsp__gowmc
        gcii__nktv[0] = pmjul__zlgn
    else:
        wxny__kfodi[0] = xqk__ymsc
        gcii__nktv[0] = agq__ijfiw
    if rank != rwi__gikfz:
        gqjr__ubhu = bodo.libs.distributed_api.isend(wxny__kfodi, 1,
            ccav__lvq, ufv__zzjab, True)
        hyztw__qdq = bodo.libs.distributed_api.isend(gcii__nktv, 1,
            ccav__lvq, ufv__zzjab, True)
    return xqk__ymsc, agq__ijfiw


@overload(np.sort, inline='always', no_unliteral=True)
def np_sort(A, axis=-1, kind=None, order=None):
    if not bodo.utils.utils.is_array_typ(A, False) or isinstance(A, types.Array
        ):
        return
    vmwkt__qyjiy = {'axis': axis, 'kind': kind, 'order': order}
    ogb__uoegt = {'axis': -1, 'kind': None, 'order': None}
    check_unsupported_args('np.sort', vmwkt__qyjiy, ogb__uoegt, 'numpy')

    def impl(A, axis=-1, kind=None, order=None):
        return pd.Series(A).sort_values().values
    return impl


def repeat_kernel(A, repeats):
    return A


@overload(repeat_kernel, no_unliteral=True)
def repeat_kernel_overload(A, repeats):
    qswg__wmh = to_str_arr_if_dict_array(A)
    if isinstance(repeats, types.Integer):

        def impl_int(A, repeats):
            A = decode_if_dict_array(A)
            niqvw__xhzx = len(A)
            imwwn__kdx = bodo.utils.utils.alloc_type(niqvw__xhzx * repeats,
                qswg__wmh, (-1,))
            for i in range(niqvw__xhzx):
                umw__tkxb = i * repeats
                if bodo.libs.array_kernels.isna(A, i):
                    for vuh__zqnr in range(repeats):
                        bodo.libs.array_kernels.setna(imwwn__kdx, umw__tkxb +
                            vuh__zqnr)
                else:
                    imwwn__kdx[umw__tkxb:umw__tkxb + repeats] = A[i]
            return imwwn__kdx
        return impl_int

    def impl_arr(A, repeats):
        A = decode_if_dict_array(A)
        niqvw__xhzx = len(A)
        imwwn__kdx = bodo.utils.utils.alloc_type(repeats.sum(), qswg__wmh,
            (-1,))
        umw__tkxb = 0
        for i in range(niqvw__xhzx):
            qdlb__hqoa = repeats[i]
            if bodo.libs.array_kernels.isna(A, i):
                for vuh__zqnr in range(qdlb__hqoa):
                    bodo.libs.array_kernels.setna(imwwn__kdx, umw__tkxb +
                        vuh__zqnr)
            else:
                imwwn__kdx[umw__tkxb:umw__tkxb + qdlb__hqoa] = A[i]
            umw__tkxb += qdlb__hqoa
        return imwwn__kdx
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
        ljope__kle = bodo.libs.array_kernels.unique(A)
        return bodo.allgatherv(ljope__kle, False)
    return impl


@overload(np.union1d, inline='always', no_unliteral=True)
def overload_union1d(A1, A2):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.union1d()')

    def impl(A1, A2):
        dwihv__dur = bodo.libs.array_kernels.concat([A1, A2])
        jpj__kqv = bodo.libs.array_kernels.unique(dwihv__dur)
        return pd.Series(jpj__kqv).sort_values().values
    return impl


@overload(np.intersect1d, inline='always', no_unliteral=True)
def overload_intersect1d(A1, A2, assume_unique=False, return_indices=False):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    vmwkt__qyjiy = {'assume_unique': assume_unique, 'return_indices':
        return_indices}
    ogb__uoegt = {'assume_unique': False, 'return_indices': False}
    check_unsupported_args('np.intersect1d', vmwkt__qyjiy, ogb__uoegt, 'numpy')
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.intersect1d()'
            )
    if A1.ndim != 1 or A2.ndim != 1:
        raise BodoError('Only 1D arrays supported in np.intersect1d()')

    def impl(A1, A2, assume_unique=False, return_indices=False):
        zqeaz__qjuy = bodo.libs.array_kernels.unique(A1)
        xrtb__viahr = bodo.libs.array_kernels.unique(A2)
        dwihv__dur = bodo.libs.array_kernels.concat([zqeaz__qjuy, xrtb__viahr])
        yug__cwgo = pd.Series(dwihv__dur).sort_values().values
        return slice_array_intersect1d(yug__cwgo)
    return impl


@register_jitable
def slice_array_intersect1d(arr):
    qjdl__lzfxl = arr[1:] == arr[:-1]
    return arr[:-1][qjdl__lzfxl]


@overload(np.setdiff1d, inline='always', no_unliteral=True)
def overload_setdiff1d(A1, A2, assume_unique=False):
    if not bodo.utils.utils.is_array_typ(A1, False
        ) or not bodo.utils.utils.is_array_typ(A2, False):
        return
    vmwkt__qyjiy = {'assume_unique': assume_unique}
    ogb__uoegt = {'assume_unique': False}
    check_unsupported_args('np.setdiff1d', vmwkt__qyjiy, ogb__uoegt, 'numpy')
    if A1 != A2:
        raise BodoError('Both arrays must be the same type in np.setdiff1d()')
    if A1.ndim != 1 or A2.ndim != 1:
        raise BodoError('Only 1D arrays supported in np.setdiff1d()')

    def impl(A1, A2, assume_unique=False):
        zqeaz__qjuy = bodo.libs.array_kernels.unique(A1)
        xrtb__viahr = bodo.libs.array_kernels.unique(A2)
        qjdl__lzfxl = calculate_mask_setdiff1d(zqeaz__qjuy, xrtb__viahr)
        return pd.Series(zqeaz__qjuy[qjdl__lzfxl]).sort_values().values
    return impl


@register_jitable
def calculate_mask_setdiff1d(A1, A2):
    qjdl__lzfxl = np.ones(len(A1), np.bool_)
    for i in range(len(A2)):
        qjdl__lzfxl &= A1 != A2[i]
    return qjdl__lzfxl


@overload(np.linspace, inline='always', no_unliteral=True)
def np_linspace(start, stop, num=50, endpoint=True, retstep=False, dtype=
    None, axis=0):
    vmwkt__qyjiy = {'retstep': retstep, 'axis': axis}
    ogb__uoegt = {'retstep': False, 'axis': 0}
    check_unsupported_args('np.linspace', vmwkt__qyjiy, ogb__uoegt, 'numpy')
    sxuk__azqe = False
    if is_overload_none(dtype):
        qswg__wmh = np.promote_types(np.promote_types(numba.np.
            numpy_support.as_dtype(start), numba.np.numpy_support.as_dtype(
            stop)), numba.np.numpy_support.as_dtype(types.float64)).type
    else:
        if isinstance(dtype.dtype, types.Integer):
            sxuk__azqe = True
        qswg__wmh = numba.np.numpy_support.as_dtype(dtype).type
    if sxuk__azqe:

        def impl_int(start, stop, num=50, endpoint=True, retstep=False,
            dtype=None, axis=0):
            vdv__zrt = np_linspace_get_stepsize(start, stop, num, endpoint)
            numba.parfors.parfor.init_prange()
            imwwn__kdx = np.empty(num, qswg__wmh)
            for i in numba.parfors.parfor.internal_prange(num):
                imwwn__kdx[i] = qswg__wmh(np.floor(start + i * vdv__zrt))
            return imwwn__kdx
        return impl_int
    else:

        def impl(start, stop, num=50, endpoint=True, retstep=False, dtype=
            None, axis=0):
            vdv__zrt = np_linspace_get_stepsize(start, stop, num, endpoint)
            numba.parfors.parfor.init_prange()
            imwwn__kdx = np.empty(num, qswg__wmh)
            for i in numba.parfors.parfor.internal_prange(num):
                imwwn__kdx[i] = qswg__wmh(start + i * vdv__zrt)
            return imwwn__kdx
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
        iqi__ahr = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                iqi__ahr += A[i] == val
        return iqi__ahr > 0
    return impl


@overload(np.any, inline='always', no_unliteral=True)
def np_any(A, axis=None, out=None, keepdims=None):
    if not (bodo.utils.utils.is_array_typ(A, False) and A.ndim == 1):
        return
    vmwkt__qyjiy = {'axis': axis, 'out': out, 'keepdims': keepdims}
    ogb__uoegt = {'axis': None, 'out': None, 'keepdims': None}
    check_unsupported_args('np.any', vmwkt__qyjiy, ogb__uoegt, 'numpy')

    def impl(A, axis=None, out=None, keepdims=None):
        numba.parfors.parfor.init_prange()
        iqi__ahr = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                iqi__ahr += int(bool(A[i]))
        return iqi__ahr > 0
    return impl


@overload(np.all, inline='always', no_unliteral=True)
def np_all(A, axis=None, out=None, keepdims=None):
    if not (bodo.utils.utils.is_array_typ(A, False) and A.ndim == 1):
        return
    vmwkt__qyjiy = {'axis': axis, 'out': out, 'keepdims': keepdims}
    ogb__uoegt = {'axis': None, 'out': None, 'keepdims': None}
    check_unsupported_args('np.any', vmwkt__qyjiy, ogb__uoegt, 'numpy')

    def impl(A, axis=None, out=None, keepdims=None):
        numba.parfors.parfor.init_prange()
        iqi__ahr = 0
        n = len(A)
        for i in numba.parfors.parfor.internal_prange(n):
            if not bodo.libs.array_kernels.isna(A, i):
                iqi__ahr += int(bool(A[i]))
        return iqi__ahr == n
    return impl


@overload(np.cbrt, inline='always', no_unliteral=True)
def np_cbrt(A, out=None, where=True, casting='same_kind', order='K', dtype=
    None, subok=True):
    if not (isinstance(A, types.Number) or bodo.utils.utils.is_array_typ(A,
        False) and A.ndim == 1 and isinstance(A.dtype, types.Number)):
        return
    vmwkt__qyjiy = {'out': out, 'where': where, 'casting': casting, 'order':
        order, 'dtype': dtype, 'subok': subok}
    ogb__uoegt = {'out': None, 'where': True, 'casting': 'same_kind',
        'order': 'K', 'dtype': None, 'subok': True}
    check_unsupported_args('np.cbrt', vmwkt__qyjiy, ogb__uoegt, 'numpy')
    if bodo.utils.utils.is_array_typ(A, False):
        jrxmr__zeg = np.promote_types(numba.np.numpy_support.as_dtype(A.
            dtype), numba.np.numpy_support.as_dtype(types.float32)).type

        def impl_arr(A, out=None, where=True, casting='same_kind', order=
            'K', dtype=None, subok=True):
            numba.parfors.parfor.init_prange()
            n = len(A)
            imwwn__kdx = np.empty(n, jrxmr__zeg)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(A, i):
                    bodo.libs.array_kernels.setna(imwwn__kdx, i)
                    continue
                imwwn__kdx[i] = np_cbrt_scalar(A[i], jrxmr__zeg)
            return imwwn__kdx
        return impl_arr
    jrxmr__zeg = np.promote_types(numba.np.numpy_support.as_dtype(A), numba
        .np.numpy_support.as_dtype(types.float32)).type

    def impl_scalar(A, out=None, where=True, casting='same_kind', order='K',
        dtype=None, subok=True):
        return np_cbrt_scalar(A, jrxmr__zeg)
    return impl_scalar


@register_jitable
def np_cbrt_scalar(x, float_dtype):
    if np.isnan(x):
        return np.nan
    vico__ewud = x < 0
    if vico__ewud:
        x = -x
    res = np.power(float_dtype(x), 1.0 / 3.0)
    if vico__ewud:
        return -res
    return res


@overload(np.hstack, no_unliteral=True)
def np_hstack(tup):
    zknck__xsgr = isinstance(tup, (types.BaseTuple, types.List))
    izng__ntb = isinstance(tup, (bodo.SeriesType, bodo.hiframes.
        pd_series_ext.HeterogeneousSeriesType)) and isinstance(tup.data, (
        types.BaseTuple, types.List, bodo.NullableTupleType))
    if isinstance(tup, types.BaseTuple):
        for dzc__pql in tup.types:
            zknck__xsgr = zknck__xsgr and bodo.utils.utils.is_array_typ(
                dzc__pql, False)
    elif isinstance(tup, types.List):
        zknck__xsgr = bodo.utils.utils.is_array_typ(tup.dtype, False)
    elif izng__ntb:
        lfdk__ohxo = tup.data.tuple_typ if isinstance(tup.data, bodo.
            NullableTupleType) else tup.data
        for dzc__pql in lfdk__ohxo.types:
            izng__ntb = izng__ntb and bodo.utils.utils.is_array_typ(dzc__pql,
                False)
    if not (zknck__xsgr or izng__ntb):
        return
    if izng__ntb:

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
    vmwkt__qyjiy = {'check_valid': check_valid, 'tol': tol}
    ogb__uoegt = {'check_valid': 'warn', 'tol': 1e-08}
    check_unsupported_args('np.random.multivariate_normal', vmwkt__qyjiy,
        ogb__uoegt, 'numpy')
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
        jha__hgt = mean.shape[0]
        edjw__smxr = size, jha__hgt
        tyhz__zjm = np.random.standard_normal(edjw__smxr)
        cov = cov.astype(np.float64)
        len__cgj, s, oexn__bvf = np.linalg.svd(cov)
        res = np.dot(tyhz__zjm, np.sqrt(s).reshape(jha__hgt, 1) * oexn__bvf)
        nktcv__qpyw = res + mean
        return nktcv__qpyw
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
            fdgkq__kxxx = bodo.hiframes.series_kernels._get_type_max_value(arr)
            tue__dnzqp = typing.builtins.IndexValue(-1, fdgkq__kxxx)
            for i in numba.parfors.parfor.internal_prange(len(arr)):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                swph__jfvwx = typing.builtins.IndexValue(i, arr[i])
                tue__dnzqp = min(tue__dnzqp, swph__jfvwx)
            return tue__dnzqp.index
        return impl_bodo_arr
    if isinstance(arr, CategoricalArrayType):
        assert arr.dtype.ordered, 'Categorical Array must be ordered to select an argmin'
        wlps__swa = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            arr.dtype)

        def impl_cat_arr(arr):
            oqi__istte = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            fdgkq__kxxx = wlps__swa(len(arr.dtype.categories) + 1)
            tue__dnzqp = typing.builtins.IndexValue(-1, fdgkq__kxxx)
            for i in numba.parfors.parfor.internal_prange(len(arr)):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                swph__jfvwx = typing.builtins.IndexValue(i, oqi__istte[i])
                tue__dnzqp = min(tue__dnzqp, swph__jfvwx)
            return tue__dnzqp.index
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
            fdgkq__kxxx = bodo.hiframes.series_kernels._get_type_min_value(arr)
            tue__dnzqp = typing.builtins.IndexValue(-1, fdgkq__kxxx)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                swph__jfvwx = typing.builtins.IndexValue(i, arr[i])
                tue__dnzqp = max(tue__dnzqp, swph__jfvwx)
            return tue__dnzqp.index
        return impl_bodo_arr
    if isinstance(arr, CategoricalArrayType):
        assert arr.dtype.ordered, 'Categorical Array must be ordered to select an argmin'
        wlps__swa = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            arr.dtype)

        def impl_cat_arr(arr):
            n = len(arr)
            oqi__istte = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            fdgkq__kxxx = wlps__swa(-1)
            tue__dnzqp = typing.builtins.IndexValue(-1, fdgkq__kxxx)
            for i in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arr, i):
                    continue
                swph__jfvwx = typing.builtins.IndexValue(i, oqi__istte[i])
                tue__dnzqp = max(tue__dnzqp, swph__jfvwx)
            return tue__dnzqp.index
        return impl_cat_arr
    return lambda arr: arr.argmax()


@overload_attribute(types.Array, 'nbytes', inline='always')
def overload_dataframe_index(A):
    return lambda A: A.size * bodo.io.np_io.get_dtype_size(A.dtype)
