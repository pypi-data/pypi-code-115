"""Some kernels for Series related functions. This is a legacy file that needs to be
refactored.
"""
import datetime
import numba
import numpy as np
from numba.core import types
from numba.extending import overload, register_jitable
import bodo
from bodo.libs.int_arr_ext import IntDtype
from bodo.utils.typing import decode_if_dict_array


def _column_filter_impl(B, ind):
    otll__bgy = bodo.hiframes.rolling.alloc_shift(len(B), B, (-1,))
    for hithf__ygm in numba.parfors.parfor.internal_prange(len(otll__bgy)):
        if ind[hithf__ygm]:
            otll__bgy[hithf__ygm] = B[hithf__ygm]
        else:
            bodo.libs.array_kernels.setna(otll__bgy, hithf__ygm)
    return otll__bgy


@numba.njit(no_cpython_wrapper=True)
def _series_dropna_str_alloc_impl_inner(B):
    B = decode_if_dict_array(B)
    xeybl__yiyvq = len(B)
    jgg__djfku = 0
    for hithf__ygm in range(len(B)):
        if bodo.libs.str_arr_ext.str_arr_is_na(B, hithf__ygm):
            jgg__djfku += 1
    lkwhz__wteq = xeybl__yiyvq - jgg__djfku
    asl__jrdn = bodo.libs.str_arr_ext.num_total_chars(B)
    otll__bgy = bodo.libs.str_arr_ext.pre_alloc_string_array(lkwhz__wteq,
        asl__jrdn)
    bodo.libs.str_arr_ext.copy_non_null_offsets(otll__bgy, B)
    bodo.libs.str_arr_ext.copy_data(otll__bgy, B)
    bodo.libs.str_arr_ext.set_null_bits_to_value(otll__bgy, -1)
    return otll__bgy


def _get_nan(val):
    return np.nan


@overload(_get_nan, no_unliteral=True)
def _get_nan_overload(val):
    if isinstance(val, (types.NPDatetime, types.NPTimedelta)):
        nat = val('NaT')
        return lambda val: nat
    if isinstance(val, types.Float):
        return lambda val: np.nan
    return lambda val: val


def _get_type_max_value(dtype):
    return 0


@overload(_get_type_max_value, inline='always', no_unliteral=True)
def _get_type_max_value_overload(dtype):
    if isinstance(dtype, (bodo.IntegerArrayType, IntDtype)):
        _dtype = dtype.dtype
        return lambda dtype: numba.cpython.builtins.get_type_max_value(_dtype)
    if dtype == bodo.datetime_date_array_type:
        return lambda dtype: _get_date_max_value()
    if isinstance(dtype.dtype, types.NPDatetime):
        return lambda dtype: bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
            numba.cpython.builtins.get_type_max_value(numba.core.types.int64))
    if isinstance(dtype.dtype, types.NPTimedelta):
        return (lambda dtype: bodo.hiframes.pd_timestamp_ext.
            integer_to_timedelta64(numba.cpython.builtins.
            get_type_max_value(numba.core.types.int64)))
    if dtype.dtype == types.bool_:
        return lambda dtype: True
    return lambda dtype: numba.cpython.builtins.get_type_max_value(dtype)


@register_jitable
def _get_date_max_value():
    return datetime.date(datetime.MAXYEAR, 12, 31)


def _get_type_min_value(dtype):
    return 0


@overload(_get_type_min_value, inline='always', no_unliteral=True)
def _get_type_min_value_overload(dtype):
    if isinstance(dtype, (bodo.IntegerArrayType, IntDtype)):
        _dtype = dtype.dtype
        return lambda dtype: numba.cpython.builtins.get_type_min_value(_dtype)
    if dtype == bodo.datetime_date_array_type:
        return lambda dtype: _get_date_min_value()
    if isinstance(dtype.dtype, types.NPDatetime):
        return lambda dtype: bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
            numba.cpython.builtins.get_type_min_value(numba.core.types.int64))
    if isinstance(dtype.dtype, types.NPTimedelta):
        return (lambda dtype: bodo.hiframes.pd_timestamp_ext.
            integer_to_timedelta64(numba.cpython.builtins.
            get_type_min_value(numba.core.types.uint64)))
    if dtype.dtype == types.bool_:
        return lambda dtype: False
    return lambda dtype: numba.cpython.builtins.get_type_min_value(dtype)


@register_jitable
def _get_date_min_value():
    return datetime.date(datetime.MINYEAR, 1, 1)


@overload(min)
def indval_min(a1, a2):
    if a1 == types.bool_ and a2 == types.bool_:

        def min_impl(a1, a2):
            if a1 > a2:
                return a2
            return a1
        return min_impl


@overload(max)
def indval_max(a1, a2):
    if a1 == types.bool_ and a2 == types.bool_:

        def max_impl(a1, a2):
            if a2 > a1:
                return a2
            return a1
        return max_impl


@numba.njit
def _sum_handle_nan(s, count):
    if not count:
        s = bodo.hiframes.series_kernels._get_nan(s)
    return s


@numba.njit
def _box_cat_val(s, cat_dtype, count):
    if s == -1 or count == 0:
        return bodo.hiframes.series_kernels._get_nan(cat_dtype.categories[0])
    return cat_dtype.categories[s]


@numba.generated_jit
def get_float_nan(s):
    nan = np.nan
    if s == types.float32:
        nan = np.float32('nan')
    return lambda s: nan


@numba.njit
def _mean_handle_nan(s, count):
    if not count:
        s = get_float_nan(s)
    else:
        s = s / count
    return s


@numba.njit
def _var_handle_mincount(s, count, min_count):
    if count < min_count:
        res = np.nan
    else:
        res = s
    return res


@numba.njit
def _compute_var_nan_count_ddof(first_moment, second_moment, count, ddof):
    if count == 0 or count <= ddof:
        s = np.nan
    else:
        s = second_moment - first_moment * first_moment / count
        s = s / (count - ddof)
    return s


@numba.njit
def _sem_handle_nan(res, count):
    if count < 1:
        fmw__qcgh = np.nan
    else:
        fmw__qcgh = (res / count) ** 0.5
    return fmw__qcgh


@numba.njit
def lt_f(a, b):
    return a < b


@numba.njit
def gt_f(a, b):
    return a > b


@numba.njit
def compute_skew(first_moment, second_moment, third_moment, count):
    if count < 3:
        return np.nan
    iqmnb__adej = first_moment / count
    zwwb__lkt = (third_moment - 3 * second_moment * iqmnb__adej + 2 * count *
        iqmnb__adej ** 3)
    vcme__meil = second_moment - iqmnb__adej * first_moment
    s = count * (count - 1) ** 1.5 / (count - 2
        ) * zwwb__lkt / vcme__meil ** 1.5
    s = s / (count - 1)
    return s


@numba.njit
def compute_kurt(first_moment, second_moment, third_moment, fourth_moment,
    count):
    if count < 4:
        return np.nan
    iqmnb__adej = first_moment / count
    niux__bbhid = (fourth_moment - 4 * third_moment * iqmnb__adej + 6 *
        second_moment * iqmnb__adej ** 2 - 3 * count * iqmnb__adej ** 4)
    ddfk__wnfa = second_moment - iqmnb__adej * first_moment
    nur__ddsn = 3 * (count - 1) ** 2 / ((count - 2) * (count - 3))
    cpmoz__rxnmn = count * (count + 1) * (count - 1) * niux__bbhid
    lvtj__otz = (count - 2) * (count - 3) * ddfk__wnfa ** 2
    s = (count - 1) * (cpmoz__rxnmn / lvtj__otz - nur__ddsn)
    s = s / (count - 1)
    return s
