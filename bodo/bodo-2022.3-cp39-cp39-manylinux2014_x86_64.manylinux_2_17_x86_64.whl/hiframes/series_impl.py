"""
Implementation of Series attributes and methods using overload.
"""
import operator
import numba
import numpy as np
import pandas as pd
from numba.core import types
from numba.core.typing.templates import AbstractTemplate, infer_global
from numba.extending import lower_builtin, overload, overload_attribute, overload_method, register_jitable
import bodo
from bodo.hiframes.datetime_datetime_ext import datetime_datetime_type
from bodo.hiframes.datetime_timedelta_ext import PDTimeDeltaType, datetime_timedelta_type
from bodo.hiframes.pd_categorical_ext import CategoricalArrayType, PDCategoricalDtype
from bodo.hiframes.pd_offsets_ext import is_offsets_type
from bodo.hiframes.pd_series_ext import HeterogeneousSeriesType, SeriesType, if_series_to_array_type, is_series_type
from bodo.hiframes.pd_timestamp_ext import PandasTimestampType, pd_timestamp_type
from bodo.hiframes.rolling import is_supported_shift_array_type
from bodo.libs.array_item_arr_ext import ArrayItemArrayType
from bodo.libs.binary_arr_ext import BinaryArrayType, binary_array_type, bytes_type
from bodo.libs.bool_arr_ext import BooleanArrayType, boolean_array
from bodo.libs.decimal_arr_ext import Decimal128Type, DecimalArrayType
from bodo.libs.int_arr_ext import IntegerArrayType
from bodo.libs.str_arr_ext import StringArrayType
from bodo.libs.str_ext import string_type
from bodo.utils.transform import gen_const_tup, is_var_size_item_array_type
from bodo.utils.typing import BodoError, can_replace, check_unsupported_args, dtype_to_array_type, element_type, get_common_scalar_dtype, get_literal_value, get_overload_const_bytes, get_overload_const_int, get_overload_const_str, is_common_scalar_dtype, is_iterable_type, is_literal_type, is_nullable_type, is_overload_bool, is_overload_constant_bool, is_overload_constant_bytes, is_overload_constant_int, is_overload_constant_nan, is_overload_constant_str, is_overload_false, is_overload_int, is_overload_none, is_overload_true, is_overload_zero, is_scalar_type, is_str_arr_type, raise_bodo_error, to_nullable_type, to_str_arr_if_dict_array


@overload_attribute(HeterogeneousSeriesType, 'index', inline='always')
@overload_attribute(SeriesType, 'index', inline='always')
def overload_series_index(s):
    return lambda s: bodo.hiframes.pd_series_ext.get_series_index(s)


@overload_attribute(HeterogeneousSeriesType, 'values', inline='always')
@overload_attribute(SeriesType, 'values', inline='always')
def overload_series_values(s):
    if isinstance(s.data, bodo.DatetimeArrayType):

        def impl(s):
            uvpru__iaeah = bodo.hiframes.pd_series_ext.get_series_data(s)
            rqkmk__vwntu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                uvpru__iaeah)
            return rqkmk__vwntu
        return impl
    return lambda s: bodo.hiframes.pd_series_ext.get_series_data(s)


@overload_attribute(SeriesType, 'dtype', inline='always')
def overload_series_dtype(s):
    if s.dtype == bodo.string_type:
        raise BodoError('Series.dtype not supported for string Series yet')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(s, 'Series.dtype'
        )
    return lambda s: bodo.hiframes.pd_series_ext.get_series_data(s).dtype


@overload_attribute(HeterogeneousSeriesType, 'shape')
@overload_attribute(SeriesType, 'shape')
def overload_series_shape(s):
    return lambda s: (len(bodo.hiframes.pd_series_ext.get_series_data(s)),)


@overload_attribute(HeterogeneousSeriesType, 'ndim', inline='always')
@overload_attribute(SeriesType, 'ndim', inline='always')
def overload_series_ndim(s):
    return lambda s: 1


@overload_attribute(HeterogeneousSeriesType, 'size')
@overload_attribute(SeriesType, 'size')
def overload_series_size(s):
    return lambda s: len(bodo.hiframes.pd_series_ext.get_series_data(s))


@overload_attribute(HeterogeneousSeriesType, 'T', inline='always')
@overload_attribute(SeriesType, 'T', inline='always')
def overload_series_T(s):
    return lambda s: s


@overload_attribute(SeriesType, 'hasnans', inline='always')
def overload_series_hasnans(s):
    return lambda s: s.isna().sum() != 0


@overload_attribute(HeterogeneousSeriesType, 'empty')
@overload_attribute(SeriesType, 'empty')
def overload_series_empty(s):
    return lambda s: len(bodo.hiframes.pd_series_ext.get_series_data(s)) == 0


@overload_attribute(SeriesType, 'dtypes', inline='always')
def overload_series_dtypes(s):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(s,
        'Series.dtypes')
    return lambda s: s.dtype


@overload_attribute(HeterogeneousSeriesType, 'name', inline='always')
@overload_attribute(SeriesType, 'name', inline='always')
def overload_series_name(s):
    return lambda s: bodo.hiframes.pd_series_ext.get_series_name(s)


@overload(len, no_unliteral=True)
def overload_series_len(S):
    if isinstance(S, (SeriesType, HeterogeneousSeriesType)):
        return lambda S: len(bodo.hiframes.pd_series_ext.get_series_data(S))


@overload_method(SeriesType, 'copy', inline='always', no_unliteral=True)
def overload_series_copy(S, deep=True):
    if is_overload_true(deep):

        def impl1(S, deep=True):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            return bodo.hiframes.pd_series_ext.init_series(arr.copy(),
                index, name)
        return impl1
    if is_overload_false(deep):

        def impl2(S, deep=True):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            return bodo.hiframes.pd_series_ext.init_series(arr, index, name)
        return impl2

    def impl(S, deep=True):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        if deep:
            arr = arr.copy()
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(arr, index, name)
    return impl


@overload_method(SeriesType, 'to_list', no_unliteral=True)
@overload_method(SeriesType, 'tolist', no_unliteral=True)
def overload_series_to_list(S):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.tolist()')
    if isinstance(S.dtype, types.Float):

        def impl_float(S):
            xqdhm__rdgd = list()
            for qbtq__ayyb in range(len(S)):
                xqdhm__rdgd.append(S.iat[qbtq__ayyb])
            return xqdhm__rdgd
        return impl_float

    def impl(S):
        xqdhm__rdgd = list()
        for qbtq__ayyb in range(len(S)):
            if bodo.libs.array_kernels.isna(S.values, qbtq__ayyb):
                raise ValueError(
                    'Series.to_list(): Not supported for NA values with non-float dtypes'
                    )
            xqdhm__rdgd.append(S.iat[qbtq__ayyb])
        return xqdhm__rdgd
    return impl


@overload_method(SeriesType, 'to_numpy', inline='always', no_unliteral=True)
def overload_series_to_numpy(S, dtype=None, copy=False, na_value=None):
    kbz__qvmt = dict(dtype=dtype, copy=copy, na_value=na_value)
    wcxf__wtnln = dict(dtype=None, copy=False, na_value=None)
    check_unsupported_args('Series.to_numpy', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')

    def impl(S, dtype=None, copy=False, na_value=None):
        return S.values
    return impl


@overload_method(SeriesType, 'reset_index', inline='always', no_unliteral=True)
def overload_series_reset_index(S, level=None, drop=False, name=None,
    inplace=False):
    kbz__qvmt = dict(name=name, inplace=inplace)
    wcxf__wtnln = dict(name=None, inplace=False)
    check_unsupported_args('Series.reset_index', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not bodo.hiframes.dataframe_impl._is_all_levels(S, level):
        raise_bodo_error(
            'Series.reset_index(): only dropping all index levels supported')
    if not is_overload_constant_bool(drop):
        raise_bodo_error(
            "Series.reset_index(): 'drop' parameter should be a constant boolean value"
            )
    if is_overload_true(drop):

        def impl_drop(S, level=None, drop=False, name=None, inplace=False):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_index_ext.init_range_index(0, len(arr),
                1, None)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            return bodo.hiframes.pd_series_ext.init_series(arr, index, name)
        return impl_drop

    def get_name_literal(name_typ, is_index=False, series_name=None):
        if is_overload_none(name_typ):
            if is_index:
                return 'index' if series_name != 'index' else 'level_0'
            return 0
        if is_literal_type(name_typ):
            return get_literal_value(name_typ)
        else:
            raise BodoError(
                'Series.reset_index() not supported for non-literal series names'
                )
    series_name = get_name_literal(S.name_typ)
    jyz__vvo = get_name_literal(S.index.name_typ, True, series_name)
    columns = [jyz__vvo, series_name]
    acxuc__tss = (
        'def _impl(S, level=None, drop=False, name=None, inplace=False):\n')
    acxuc__tss += '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    acxuc__tss += """    index = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(S))
"""
    acxuc__tss += """    df_index = bodo.hiframes.pd_index_ext.init_range_index(0, len(S), 1, None)
"""
    acxuc__tss += '    col_var = {}\n'.format(gen_const_tup(columns))
    acxuc__tss += """    return bodo.hiframes.pd_dataframe_ext.init_dataframe((index, arr), df_index, col_var)
"""
    bsc__zfa = {}
    exec(acxuc__tss, {'bodo': bodo}, bsc__zfa)
    cdvme__nbb = bsc__zfa['_impl']
    return cdvme__nbb


@overload_method(SeriesType, 'isna', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'isnull', inline='always', no_unliteral=True)
def overload_series_isna(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        hedma__sko = bodo.libs.array_ops.array_op_isna(arr)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko, index, name)
    return impl


@overload_method(SeriesType, 'round', inline='always', no_unliteral=True)
def overload_series_round(S, decimals=0):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.round()')

    def impl(S, decimals=0):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        numba.parfors.parfor.init_prange()
        n = len(arr)
        hedma__sko = bodo.utils.utils.alloc_type(n, arr, (-1,))
        for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
            if pd.isna(arr[qbtq__ayyb]):
                bodo.libs.array_kernels.setna(hedma__sko, qbtq__ayyb)
            else:
                hedma__sko[qbtq__ayyb] = np.round(arr[qbtq__ayyb], decimals)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko, index, name)
    return impl


@overload_method(SeriesType, 'sum', inline='always', no_unliteral=True)
def overload_series_sum(S, axis=None, skipna=True, level=None, numeric_only
    =None, min_count=0):
    kbz__qvmt = dict(level=level, numeric_only=numeric_only)
    wcxf__wtnln = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.sum', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.sum(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.sum(): skipna argument must be a boolean')
    if not is_overload_int(min_count):
        raise BodoError('Series.sum(): min_count argument must be an integer')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.sum()'
        )

    def impl(S, axis=None, skipna=True, level=None, numeric_only=None,
        min_count=0):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_sum(arr, skipna, min_count)
    return impl


@overload_method(SeriesType, 'prod', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'product', inline='always', no_unliteral=True)
def overload_series_prod(S, axis=None, skipna=True, level=None,
    numeric_only=None, min_count=0):
    kbz__qvmt = dict(level=level, numeric_only=numeric_only)
    wcxf__wtnln = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.product', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.product(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.product(): skipna argument must be a boolean')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.product()')

    def impl(S, axis=None, skipna=True, level=None, numeric_only=None,
        min_count=0):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_prod(arr, skipna, min_count)
    return impl


@overload_method(SeriesType, 'any', inline='always', no_unliteral=True)
def overload_series_any(S, axis=0, bool_only=None, skipna=True, level=None):
    kbz__qvmt = dict(axis=axis, bool_only=bool_only, skipna=skipna, level=level
        )
    wcxf__wtnln = dict(axis=0, bool_only=None, skipna=True, level=None)
    check_unsupported_args('Series.any', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.any()'
        )

    def impl(S, axis=0, bool_only=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        olu__mwwdw = 0
        for qbtq__ayyb in numba.parfors.parfor.internal_prange(len(A)):
            acujo__vnwbj = 0
            if not bodo.libs.array_kernels.isna(A, qbtq__ayyb):
                acujo__vnwbj = int(A[qbtq__ayyb])
            olu__mwwdw += acujo__vnwbj
        return olu__mwwdw != 0
    return impl


@overload_method(SeriesType, 'equals', inline='always', no_unliteral=True)
def overload_series_equals(S, other):
    if not isinstance(other, SeriesType):
        raise BodoError("Series.equals() 'other' must be a Series")
    if isinstance(S.data, bodo.ArrayItemArrayType):
        raise BodoError(
            'Series.equals() not supported for Series where each element is an array or list'
            )
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.equals()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(other,
        'Series.equals()')
    if S.data != other.data:
        return lambda S, other: False

    def impl(S, other):
        ifp__qzk = bodo.hiframes.pd_series_ext.get_series_data(S)
        kulz__pkhlc = bodo.hiframes.pd_series_ext.get_series_data(other)
        numba.parfors.parfor.init_prange()
        olu__mwwdw = 0
        for qbtq__ayyb in numba.parfors.parfor.internal_prange(len(ifp__qzk)):
            acujo__vnwbj = 0
            ydfq__mwiqp = bodo.libs.array_kernels.isna(ifp__qzk, qbtq__ayyb)
            kvck__bmfnj = bodo.libs.array_kernels.isna(kulz__pkhlc, qbtq__ayyb)
            if (ydfq__mwiqp and not kvck__bmfnj or not ydfq__mwiqp and
                kvck__bmfnj):
                acujo__vnwbj = 1
            elif not ydfq__mwiqp:
                if ifp__qzk[qbtq__ayyb] != kulz__pkhlc[qbtq__ayyb]:
                    acujo__vnwbj = 1
            olu__mwwdw += acujo__vnwbj
        return olu__mwwdw == 0
    return impl


@overload_method(SeriesType, 'all', inline='always', no_unliteral=True)
def overload_series_all(S, axis=0, bool_only=None, skipna=True, level=None):
    kbz__qvmt = dict(axis=axis, bool_only=bool_only, skipna=skipna, level=level
        )
    wcxf__wtnln = dict(axis=0, bool_only=None, skipna=True, level=None)
    check_unsupported_args('Series.all', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.all()'
        )

    def impl(S, axis=0, bool_only=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        olu__mwwdw = 0
        for qbtq__ayyb in numba.parfors.parfor.internal_prange(len(A)):
            acujo__vnwbj = 0
            if not bodo.libs.array_kernels.isna(A, qbtq__ayyb):
                acujo__vnwbj = int(not A[qbtq__ayyb])
            olu__mwwdw += acujo__vnwbj
        return olu__mwwdw == 0
    return impl


@overload_method(SeriesType, 'mad', inline='always', no_unliteral=True)
def overload_series_mad(S, axis=None, skipna=True, level=None):
    kbz__qvmt = dict(level=level)
    wcxf__wtnln = dict(level=None)
    check_unsupported_args('Series.mad', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not is_overload_bool(skipna):
        raise BodoError("Series.mad(): 'skipna' argument must be a boolean")
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.mad(): axis argument not supported')
    qlyw__ihqd = types.float64
    cjc__dai = types.float64
    if S.dtype == types.float32:
        qlyw__ihqd = types.float32
        cjc__dai = types.float32
    tydn__xkb = qlyw__ihqd(0)
    jqhs__tpsg = cjc__dai(0)
    ymd__okcz = cjc__dai(1)
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.mad()'
        )

    def impl(S, axis=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        pkmov__iczp = tydn__xkb
        olu__mwwdw = jqhs__tpsg
        for qbtq__ayyb in numba.parfors.parfor.internal_prange(len(A)):
            acujo__vnwbj = tydn__xkb
            slkiv__pgedx = jqhs__tpsg
            if not bodo.libs.array_kernels.isna(A, qbtq__ayyb) or not skipna:
                acujo__vnwbj = A[qbtq__ayyb]
                slkiv__pgedx = ymd__okcz
            pkmov__iczp += acujo__vnwbj
            olu__mwwdw += slkiv__pgedx
        kwkx__welr = bodo.hiframes.series_kernels._mean_handle_nan(pkmov__iczp,
            olu__mwwdw)
        tfve__ydgj = tydn__xkb
        for qbtq__ayyb in numba.parfors.parfor.internal_prange(len(A)):
            acujo__vnwbj = tydn__xkb
            if not bodo.libs.array_kernels.isna(A, qbtq__ayyb) or not skipna:
                acujo__vnwbj = abs(A[qbtq__ayyb] - kwkx__welr)
            tfve__ydgj += acujo__vnwbj
        ocl__accll = bodo.hiframes.series_kernels._mean_handle_nan(tfve__ydgj,
            olu__mwwdw)
        return ocl__accll
    return impl


@overload_method(SeriesType, 'mean', inline='always', no_unliteral=True)
def overload_series_mean(S, axis=None, skipna=None, level=None,
    numeric_only=None):
    if not isinstance(S.dtype, types.Number) and S.dtype not in [bodo.
        datetime64ns, types.bool_]:
        raise BodoError(f"Series.mean(): Series with type '{S}' not supported")
    kbz__qvmt = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    wcxf__wtnln = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.mean', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.mean(): axis argument not supported')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.mean()')

    def impl(S, axis=None, skipna=None, level=None, numeric_only=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_mean(arr)
    return impl


@overload_method(SeriesType, 'sem', inline='always', no_unliteral=True)
def overload_series_sem(S, axis=None, skipna=True, level=None, ddof=1,
    numeric_only=None):
    kbz__qvmt = dict(level=level, numeric_only=numeric_only)
    wcxf__wtnln = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.sem', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.sem(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.sem(): skipna argument must be a boolean')
    if not is_overload_int(ddof):
        raise BodoError('Series.sem(): ddof argument must be an integer')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.sem()'
        )

    def impl(S, axis=None, skipna=True, level=None, ddof=1, numeric_only=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        glle__gqiay = 0
        yph__qpnl = 0
        olu__mwwdw = 0
        for qbtq__ayyb in numba.parfors.parfor.internal_prange(len(A)):
            acujo__vnwbj = 0
            slkiv__pgedx = 0
            if not bodo.libs.array_kernels.isna(A, qbtq__ayyb) or not skipna:
                acujo__vnwbj = A[qbtq__ayyb]
                slkiv__pgedx = 1
            glle__gqiay += acujo__vnwbj
            yph__qpnl += acujo__vnwbj * acujo__vnwbj
            olu__mwwdw += slkiv__pgedx
        uujh__ulus = bodo.hiframes.series_kernels._compute_var_nan_count_ddof(
            glle__gqiay, yph__qpnl, olu__mwwdw, ddof)
        ttym__umkq = bodo.hiframes.series_kernels._sem_handle_nan(uujh__ulus,
            olu__mwwdw)
        return ttym__umkq
    return impl


@overload_method(SeriesType, 'kurt', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'kurtosis', inline='always', no_unliteral=True)
def overload_series_kurt(S, axis=None, skipna=True, level=None,
    numeric_only=None):
    kbz__qvmt = dict(level=level, numeric_only=numeric_only)
    wcxf__wtnln = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.kurtosis', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.kurtosis(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError(
            "Series.kurtosis(): 'skipna' argument must be a boolean")
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.kurtosis()')

    def impl(S, axis=None, skipna=True, level=None, numeric_only=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        glle__gqiay = 0.0
        yph__qpnl = 0.0
        gvnnu__max = 0.0
        mqw__xsmv = 0.0
        olu__mwwdw = 0
        for qbtq__ayyb in numba.parfors.parfor.internal_prange(len(A)):
            acujo__vnwbj = 0.0
            slkiv__pgedx = 0
            if not bodo.libs.array_kernels.isna(A, qbtq__ayyb) or not skipna:
                acujo__vnwbj = np.float64(A[qbtq__ayyb])
                slkiv__pgedx = 1
            glle__gqiay += acujo__vnwbj
            yph__qpnl += acujo__vnwbj ** 2
            gvnnu__max += acujo__vnwbj ** 3
            mqw__xsmv += acujo__vnwbj ** 4
            olu__mwwdw += slkiv__pgedx
        uujh__ulus = bodo.hiframes.series_kernels.compute_kurt(glle__gqiay,
            yph__qpnl, gvnnu__max, mqw__xsmv, olu__mwwdw)
        return uujh__ulus
    return impl


@overload_method(SeriesType, 'skew', inline='always', no_unliteral=True)
def overload_series_skew(S, axis=None, skipna=True, level=None,
    numeric_only=None):
    kbz__qvmt = dict(level=level, numeric_only=numeric_only)
    wcxf__wtnln = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.skew', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.skew(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.skew(): skipna argument must be a boolean')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.skew()')

    def impl(S, axis=None, skipna=True, level=None, numeric_only=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        glle__gqiay = 0.0
        yph__qpnl = 0.0
        gvnnu__max = 0.0
        olu__mwwdw = 0
        for qbtq__ayyb in numba.parfors.parfor.internal_prange(len(A)):
            acujo__vnwbj = 0.0
            slkiv__pgedx = 0
            if not bodo.libs.array_kernels.isna(A, qbtq__ayyb) or not skipna:
                acujo__vnwbj = np.float64(A[qbtq__ayyb])
                slkiv__pgedx = 1
            glle__gqiay += acujo__vnwbj
            yph__qpnl += acujo__vnwbj ** 2
            gvnnu__max += acujo__vnwbj ** 3
            olu__mwwdw += slkiv__pgedx
        uujh__ulus = bodo.hiframes.series_kernels.compute_skew(glle__gqiay,
            yph__qpnl, gvnnu__max, olu__mwwdw)
        return uujh__ulus
    return impl


@overload_method(SeriesType, 'var', inline='always', no_unliteral=True)
def overload_series_var(S, axis=None, skipna=True, level=None, ddof=1,
    numeric_only=None):
    kbz__qvmt = dict(level=level, numeric_only=numeric_only)
    wcxf__wtnln = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.var', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.var(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.var(): skipna argument must be a boolean')
    if not is_overload_int(ddof):
        raise BodoError('Series.var(): ddof argument must be an integer')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.var()'
        )

    def impl(S, axis=None, skipna=True, level=None, ddof=1, numeric_only=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_var(arr, skipna, ddof)
    return impl


@overload_method(SeriesType, 'std', inline='always', no_unliteral=True)
def overload_series_std(S, axis=None, skipna=True, level=None, ddof=1,
    numeric_only=None):
    kbz__qvmt = dict(level=level, numeric_only=numeric_only)
    wcxf__wtnln = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.std', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.std(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.std(): skipna argument must be a boolean')
    if not is_overload_int(ddof):
        raise BodoError('Series.std(): ddof argument must be an integer')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.std()'
        )

    def impl(S, axis=None, skipna=True, level=None, ddof=1, numeric_only=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_std(arr, skipna, ddof)
    return impl


@overload_method(SeriesType, 'dot', inline='always', no_unliteral=True)
def overload_series_dot(S, other):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.dot()'
        )
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(other,
        'Series.dot()')

    def impl(S, other):
        ifp__qzk = bodo.hiframes.pd_series_ext.get_series_data(S)
        kulz__pkhlc = bodo.hiframes.pd_series_ext.get_series_data(other)
        numba.parfors.parfor.init_prange()
        fdmli__xlgvl = 0
        for qbtq__ayyb in numba.parfors.parfor.internal_prange(len(ifp__qzk)):
            qabr__szmxr = ifp__qzk[qbtq__ayyb]
            fcaz__kwtrc = kulz__pkhlc[qbtq__ayyb]
            fdmli__xlgvl += qabr__szmxr * fcaz__kwtrc
        return fdmli__xlgvl
    return impl


@overload_method(SeriesType, 'cumsum', inline='always', no_unliteral=True)
def overload_series_cumsum(S, axis=None, skipna=True):
    kbz__qvmt = dict(skipna=skipna)
    wcxf__wtnln = dict(skipna=True)
    check_unsupported_args('Series.cumsum', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.cumsum(): axis argument not supported')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.cumsum()')

    def impl(S, axis=None, skipna=True):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(A.cumsum(), index, name)
    return impl


@overload_method(SeriesType, 'cumprod', inline='always', no_unliteral=True)
def overload_series_cumprod(S, axis=None, skipna=True):
    kbz__qvmt = dict(skipna=skipna)
    wcxf__wtnln = dict(skipna=True)
    check_unsupported_args('Series.cumprod', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.cumprod(): axis argument not supported')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.cumprod()')

    def impl(S, axis=None, skipna=True):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(A.cumprod(), index, name
            )
    return impl


@overload_method(SeriesType, 'cummin', inline='always', no_unliteral=True)
def overload_series_cummin(S, axis=None, skipna=True):
    kbz__qvmt = dict(skipna=skipna)
    wcxf__wtnln = dict(skipna=True)
    check_unsupported_args('Series.cummin', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.cummin(): axis argument not supported')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.cummin()')

    def impl(S, axis=None, skipna=True):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(bodo.libs.
            array_kernels.cummin(arr), index, name)
    return impl


@overload_method(SeriesType, 'cummax', inline='always', no_unliteral=True)
def overload_series_cummax(S, axis=None, skipna=True):
    kbz__qvmt = dict(skipna=skipna)
    wcxf__wtnln = dict(skipna=True)
    check_unsupported_args('Series.cummax', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.cummax(): axis argument not supported')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.cummax()')

    def impl(S, axis=None, skipna=True):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(bodo.libs.
            array_kernels.cummax(arr), index, name)
    return impl


@overload_method(SeriesType, 'rename', inline='always', no_unliteral=True)
def overload_series_rename(S, index=None, axis=None, copy=True, inplace=
    False, level=None, errors='ignore'):
    if not (index == bodo.string_type or isinstance(index, types.StringLiteral)
        ):
        raise BodoError("Series.rename() 'index' can only be a string")
    kbz__qvmt = dict(copy=copy, inplace=inplace, level=level, errors=errors)
    wcxf__wtnln = dict(copy=True, inplace=False, level=None, errors='ignore')
    check_unsupported_args('Series.rename', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')

    def impl(S, index=None, axis=None, copy=True, inplace=False, level=None,
        errors='ignore'):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        prt__zkzk = bodo.hiframes.pd_series_ext.get_series_index(S)
        return bodo.hiframes.pd_series_ext.init_series(A, prt__zkzk, index)
    return impl


@overload_method(SeriesType, 'rename_axis', inline='always', no_unliteral=True)
def overload_series_rename_axis(S, mapper=None, index=None, columns=None,
    axis=None, copy=True, inplace=False):
    kbz__qvmt = dict(index=index, columns=columns, axis=axis, copy=copy,
        inplace=inplace)
    wcxf__wtnln = dict(index=None, columns=None, axis=None, copy=True,
        inplace=False)
    check_unsupported_args('Series.rename_axis', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if is_overload_none(mapper) or not is_scalar_type(mapper):
        raise BodoError(
            "Series.rename_axis(): 'mapper' is required and must be a scalar type."
            )

    def impl(S, mapper=None, index=None, columns=None, axis=None, copy=True,
        inplace=False):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        index = index.rename(mapper)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(arr, index, name)
    return impl


@overload_method(SeriesType, 'abs', inline='always', no_unliteral=True)
def overload_series_abs(S):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.abs()'
        )

    def impl(S):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(np.abs(A), index, name)
    return impl


@overload_method(SeriesType, 'count', no_unliteral=True)
def overload_series_count(S, level=None):
    kbz__qvmt = dict(level=level)
    wcxf__wtnln = dict(level=None)
    check_unsupported_args('Series.count', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')

    def impl(S, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_count(A)
    return impl


@overload_method(SeriesType, 'corr', inline='always', no_unliteral=True)
def overload_series_corr(S, other, method='pearson', min_periods=None):
    kbz__qvmt = dict(method=method, min_periods=min_periods)
    wcxf__wtnln = dict(method='pearson', min_periods=None)
    check_unsupported_args('Series.corr', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.corr()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(other,
        'Series.corr()')

    def impl(S, other, method='pearson', min_periods=None):
        n = S.count()
        kgg__vsak = S.sum()
        fcel__rgut = other.sum()
        a = n * (S * other).sum() - kgg__vsak * fcel__rgut
        cgrny__dnm = n * (S ** 2).sum() - kgg__vsak ** 2
        tmiq__ofmux = n * (other ** 2).sum() - fcel__rgut ** 2
        return a / np.sqrt(cgrny__dnm * tmiq__ofmux)
    return impl


@overload_method(SeriesType, 'cov', inline='always', no_unliteral=True)
def overload_series_cov(S, other, min_periods=None, ddof=1):
    kbz__qvmt = dict(min_periods=min_periods)
    wcxf__wtnln = dict(min_periods=None)
    check_unsupported_args('Series.cov', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.cov()'
        )
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(other,
        'Series.cov()')

    def impl(S, other, min_periods=None, ddof=1):
        kgg__vsak = S.mean()
        fcel__rgut = other.mean()
        skah__szx = ((S - kgg__vsak) * (other - fcel__rgut)).sum()
        N = np.float64(S.count() - ddof)
        nonzero_len = S.count() * other.count()
        return _series_cov_helper(skah__szx, N, nonzero_len)
    return impl


def _series_cov_helper(sum_val, N, nonzero_len):
    return


@overload(_series_cov_helper, no_unliteral=True)
def _overload_series_cov_helper(sum_val, N, nonzero_len):

    def impl(sum_val, N, nonzero_len):
        if not nonzero_len:
            return np.nan
        if N <= 0.0:
            bpzds__cofb = np.sign(sum_val)
            return np.inf * bpzds__cofb
        return sum_val / N
    return impl


@overload_method(SeriesType, 'min', inline='always', no_unliteral=True)
def overload_series_min(S, axis=None, skipna=None, level=None, numeric_only
    =None):
    kbz__qvmt = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    wcxf__wtnln = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.min', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.min(): axis argument not supported')
    if isinstance(S.dtype, PDCategoricalDtype):
        if not S.dtype.ordered:
            raise BodoError(
                'Series.min(): only ordered categoricals are possible')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.min()'
        )

    def impl(S, axis=None, skipna=None, level=None, numeric_only=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_min(arr)
    return impl


@overload(max, no_unliteral=True)
def overload_series_builtins_max(S):
    if isinstance(S, SeriesType):

        def impl(S):
            return S.max()
        return impl


@overload(min, no_unliteral=True)
def overload_series_builtins_min(S):
    if isinstance(S, SeriesType):

        def impl(S):
            return S.min()
        return impl


@overload(sum, no_unliteral=True)
def overload_series_builtins_sum(S):
    if isinstance(S, SeriesType):

        def impl(S):
            return S.sum()
        return impl


@overload(np.prod, inline='always', no_unliteral=True)
def overload_series_np_prod(S):
    if isinstance(S, SeriesType):

        def impl(S):
            return S.prod()
        return impl


@overload_method(SeriesType, 'max', inline='always', no_unliteral=True)
def overload_series_max(S, axis=None, skipna=None, level=None, numeric_only
    =None):
    kbz__qvmt = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    wcxf__wtnln = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.max', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.max(): axis argument not supported')
    if isinstance(S.dtype, PDCategoricalDtype):
        if not S.dtype.ordered:
            raise BodoError(
                'Series.max(): only ordered categoricals are possible')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.max()'
        )

    def impl(S, axis=None, skipna=None, level=None, numeric_only=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_max(arr)
    return impl


@overload_method(SeriesType, 'idxmin', inline='always', no_unliteral=True)
def overload_series_idxmin(S, axis=0, skipna=True):
    kbz__qvmt = dict(axis=axis, skipna=skipna)
    wcxf__wtnln = dict(axis=0, skipna=True)
    check_unsupported_args('Series.idxmin', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.idxmin()')
    if not (S.dtype == types.none or bodo.utils.utils.is_np_array_typ(S.
        data) and (S.dtype in [bodo.datetime64ns, bodo.timedelta64ns] or
        isinstance(S.dtype, (types.Number, types.Boolean))) or isinstance(S
        .data, (bodo.IntegerArrayType, bodo.CategoricalArrayType)) or S.
        data in [bodo.boolean_array, bodo.datetime_date_array_type]):
        raise BodoError(
            f'Series.idxmin() only supported for numeric array types. Array type: {S.data} not supported.'
            )
    if isinstance(S.data, bodo.CategoricalArrayType) and not S.dtype.ordered:
        raise BodoError(
            'Series.idxmin(): only ordered categoricals are possible')

    def impl(S, axis=0, skipna=True):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        return bodo.libs.array_ops.array_op_idxmin(arr, index)
    return impl


@overload_method(SeriesType, 'idxmax', inline='always', no_unliteral=True)
def overload_series_idxmax(S, axis=0, skipna=True):
    kbz__qvmt = dict(axis=axis, skipna=skipna)
    wcxf__wtnln = dict(axis=0, skipna=True)
    check_unsupported_args('Series.idxmax', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.idxmax()')
    if not (S.dtype == types.none or bodo.utils.utils.is_np_array_typ(S.
        data) and (S.dtype in [bodo.datetime64ns, bodo.timedelta64ns] or
        isinstance(S.dtype, (types.Number, types.Boolean))) or isinstance(S
        .data, (bodo.IntegerArrayType, bodo.CategoricalArrayType)) or S.
        data in [bodo.boolean_array, bodo.datetime_date_array_type]):
        raise BodoError(
            f'Series.idxmax() only supported for numeric array types. Array type: {S.data} not supported.'
            )
    if isinstance(S.data, bodo.CategoricalArrayType) and not S.dtype.ordered:
        raise BodoError(
            'Series.idxmax(): only ordered categoricals are possible')

    def impl(S, axis=0, skipna=True):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        return bodo.libs.array_ops.array_op_idxmax(arr, index)
    return impl


@overload_method(SeriesType, 'infer_objects', inline='always')
def overload_series_infer_objects(S):
    return lambda S: S.copy()


@overload_attribute(SeriesType, 'is_monotonic', inline='always')
@overload_attribute(SeriesType, 'is_monotonic_increasing', inline='always')
def overload_series_is_monotonic_increasing(S):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.is_monotonic_increasing')
    return lambda S: bodo.libs.array_kernels.series_monotonicity(bodo.
        hiframes.pd_series_ext.get_series_data(S), 1)


@overload_attribute(SeriesType, 'is_monotonic_decreasing', inline='always')
def overload_series_is_monotonic_decreasing(S):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.is_monotonic_decreasing')
    return lambda S: bodo.libs.array_kernels.series_monotonicity(bodo.
        hiframes.pd_series_ext.get_series_data(S), 2)


@overload_attribute(SeriesType, 'nbytes', inline='always')
def overload_series_nbytes(S):
    return lambda S: bodo.hiframes.pd_series_ext.get_series_data(S).nbytes


@overload_method(SeriesType, 'autocorr', inline='always', no_unliteral=True)
def overload_series_autocorr(S, lag=1):
    return lambda S, lag=1: bodo.libs.array_kernels.autocorr(bodo.hiframes.
        pd_series_ext.get_series_data(S), lag)


@overload_method(SeriesType, 'median', inline='always', no_unliteral=True)
def overload_series_median(S, axis=None, skipna=True, level=None,
    numeric_only=None):
    kbz__qvmt = dict(level=level, numeric_only=numeric_only)
    wcxf__wtnln = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.median', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.median(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.median(): skipna argument must be a boolean')
    return (lambda S, axis=None, skipna=True, level=None, numeric_only=None:
        bodo.libs.array_ops.array_op_median(bodo.hiframes.pd_series_ext.
        get_series_data(S), skipna))


def overload_series_head(S, n=5):

    def impl(S, n=5):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        yli__wsfre = arr[:n]
        mwwoz__bptx = index[:n]
        return bodo.hiframes.pd_series_ext.init_series(yli__wsfre,
            mwwoz__bptx, name)
    return impl


@lower_builtin('series.head', SeriesType, types.Integer)
@lower_builtin('series.head', SeriesType, types.Omitted)
def series_head_lower(context, builder, sig, args):
    impl = overload_series_head(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


@numba.extending.register_jitable
def tail_slice(k, n):
    if n == 0:
        return k
    return -n


@overload_method(SeriesType, 'tail', inline='always', no_unliteral=True)
def overload_series_tail(S, n=5):
    if not is_overload_int(n):
        raise BodoError("Series.tail(): 'n' must be an Integer")

    def impl(S, n=5):
        brwbg__arpo = tail_slice(len(S), n)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        yli__wsfre = arr[brwbg__arpo:]
        mwwoz__bptx = index[brwbg__arpo:]
        return bodo.hiframes.pd_series_ext.init_series(yli__wsfre,
            mwwoz__bptx, name)
    return impl


@overload_method(SeriesType, 'first', inline='always', no_unliteral=True)
def overload_series_first(S, offset):
    yaqc__lohn = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if types.unliteral(offset) not in yaqc__lohn:
        raise BodoError(
            "Series.first(): 'offset' must be a string or a DateOffset")
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.first()')

    def impl(S, offset):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        if len(index):
            tls__ncdpc = index[0]
            pfjj__ieot = (bodo.libs.array_kernels.
                get_valid_entries_from_date_offset(index, offset,
                tls__ncdpc, False))
        else:
            pfjj__ieot = 0
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        yli__wsfre = arr[:pfjj__ieot]
        mwwoz__bptx = index[:pfjj__ieot]
        return bodo.hiframes.pd_series_ext.init_series(yli__wsfre,
            mwwoz__bptx, name)
    return impl


@overload_method(SeriesType, 'last', inline='always', no_unliteral=True)
def overload_series_last(S, offset):
    yaqc__lohn = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if types.unliteral(offset) not in yaqc__lohn:
        raise BodoError(
            "Series.last(): 'offset' must be a string or a DateOffset")
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.last()')

    def impl(S, offset):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        if len(index):
            czm__kyfew = index[-1]
            pfjj__ieot = (bodo.libs.array_kernels.
                get_valid_entries_from_date_offset(index, offset,
                czm__kyfew, True))
        else:
            pfjj__ieot = 0
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        yli__wsfre = arr[len(arr) - pfjj__ieot:]
        mwwoz__bptx = index[len(arr) - pfjj__ieot:]
        return bodo.hiframes.pd_series_ext.init_series(yli__wsfre,
            mwwoz__bptx, name)
    return impl


@overload_method(SeriesType, 'first_valid_index', inline='always',
    no_unliteral=True)
def overload_series_first_valid_index(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        abm__les = bodo.utils.conversion.index_to_array(index)
        sqznx__etuzr, cpmih__rlk = (bodo.libs.array_kernels.
            first_last_valid_index(arr, abm__les))
        return cpmih__rlk if sqznx__etuzr else None
    return impl


@overload_method(SeriesType, 'last_valid_index', inline='always',
    no_unliteral=True)
def overload_series_last_valid_index(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        abm__les = bodo.utils.conversion.index_to_array(index)
        sqznx__etuzr, cpmih__rlk = (bodo.libs.array_kernels.
            first_last_valid_index(arr, abm__les, False))
        return cpmih__rlk if sqznx__etuzr else None
    return impl


@overload_method(SeriesType, 'nlargest', inline='always', no_unliteral=True)
def overload_series_nlargest(S, n=5, keep='first'):
    kbz__qvmt = dict(keep=keep)
    wcxf__wtnln = dict(keep='first')
    check_unsupported_args('Series.nlargest', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not is_overload_int(n):
        raise BodoError('Series.nlargest(): n argument must be an integer')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.nlargest()')

    def impl(S, n=5, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        abm__les = bodo.utils.conversion.coerce_to_ndarray(index)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        hedma__sko, nrged__pcao = bodo.libs.array_kernels.nlargest(arr,
            abm__les, n, True, bodo.hiframes.series_kernels.gt_f)
        ylvd__llbk = bodo.utils.conversion.convert_to_index(nrged__pcao)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
            ylvd__llbk, name)
    return impl


@overload_method(SeriesType, 'nsmallest', inline='always', no_unliteral=True)
def overload_series_nsmallest(S, n=5, keep='first'):
    kbz__qvmt = dict(keep=keep)
    wcxf__wtnln = dict(keep='first')
    check_unsupported_args('Series.nsmallest', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not is_overload_int(n):
        raise BodoError('Series.nsmallest(): n argument must be an integer')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.nsmallest()')

    def impl(S, n=5, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        abm__les = bodo.utils.conversion.coerce_to_ndarray(index)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        hedma__sko, nrged__pcao = bodo.libs.array_kernels.nlargest(arr,
            abm__les, n, False, bodo.hiframes.series_kernels.lt_f)
        ylvd__llbk = bodo.utils.conversion.convert_to_index(nrged__pcao)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
            ylvd__llbk, name)
    return impl


@overload_method(SeriesType, 'notnull', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'notna', inline='always', no_unliteral=True)
def overload_series_notna(S):
    return lambda S: S.isna() == False


@overload_method(SeriesType, 'astype', inline='always', no_unliteral=True)
def overload_series_astype(S, dtype, copy=True, errors='raise',
    _bodo_nan_to_str=True):
    kbz__qvmt = dict(errors=errors)
    wcxf__wtnln = dict(errors='raise')
    check_unsupported_args('Series.astype', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if dtype == types.unicode_type:
        raise_bodo_error(
            "Series.astype(): 'dtype' when passed as string must be a constant value"
            )
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.astype()')

    def impl(S, dtype, copy=True, errors='raise', _bodo_nan_to_str=True):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        hedma__sko = bodo.utils.conversion.fix_arr_dtype(arr, dtype, copy,
            nan_to_str=_bodo_nan_to_str, from_series=True)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko, index, name)
    return impl


@overload_method(SeriesType, 'take', inline='always', no_unliteral=True)
def overload_series_take(S, indices, axis=0, is_copy=True):
    kbz__qvmt = dict(axis=axis, is_copy=is_copy)
    wcxf__wtnln = dict(axis=0, is_copy=True)
    check_unsupported_args('Series.take', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_iterable_type(indices) and isinstance(indices.dtype, types.
        Integer)):
        raise BodoError(
            f"Series.take() 'indices' must be an array-like and contain integers. Found type {indices}."
            )

    def impl(S, indices, axis=0, is_copy=True):
        fdof__smj = bodo.utils.conversion.coerce_to_ndarray(indices)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(arr[fdof__smj],
            index[fdof__smj], name)
    return impl


@overload_method(SeriesType, 'argsort', inline='always', no_unliteral=True)
def overload_series_argsort(S, axis=0, kind='quicksort', order=None):
    kbz__qvmt = dict(axis=axis, kind=kind, order=order)
    wcxf__wtnln = dict(axis=0, kind='quicksort', order=None)
    check_unsupported_args('Series.argsort', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')

    def impl(S, axis=0, kind='quicksort', order=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        n = len(arr)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        fdrss__teum = S.notna().values
        if not fdrss__teum.all():
            hedma__sko = np.full(n, -1, np.int64)
            hedma__sko[fdrss__teum] = argsort(arr[fdrss__teum])
        else:
            hedma__sko = argsort(arr)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko, index, name)
    return impl


@overload_method(SeriesType, 'sort_index', inline='always', no_unliteral=True)
def overload_series_sort_index(S, axis=0, level=None, ascending=True,
    inplace=False, kind='quicksort', na_position='last', sort_remaining=
    True, ignore_index=False, key=None):
    kbz__qvmt = dict(axis=axis, level=level, inplace=inplace, kind=kind,
        sort_remaining=sort_remaining, ignore_index=ignore_index, key=key)
    wcxf__wtnln = dict(axis=0, level=None, inplace=False, kind='quicksort',
        sort_remaining=True, ignore_index=False, key=None)
    check_unsupported_args('Series.sort_index', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not is_overload_bool(ascending):
        raise BodoError(
            "Series.sort_index(): 'ascending' parameter must be of type bool")
    if not is_overload_constant_str(na_position) or get_overload_const_str(
        na_position) not in ('first', 'last'):
        raise_bodo_error(
            "Series.sort_index(): 'na_position' should either be 'first' or 'last'"
            )

    def impl(S, axis=0, level=None, ascending=True, inplace=False, kind=
        'quicksort', na_position='last', sort_remaining=True, ignore_index=
        False, key=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        ana__gnyf = bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,),
            index, ('$_bodo_col3_',))
        fwaz__fwx = ana__gnyf.sort_index(ascending=ascending, inplace=
            inplace, na_position=na_position)
        hedma__sko = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(
            fwaz__fwx, 0)
        ylvd__llbk = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(
            fwaz__fwx)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
            ylvd__llbk, name)
    return impl


@overload_method(SeriesType, 'sort_values', inline='always', no_unliteral=True)
def overload_series_sort_values(S, axis=0, ascending=True, inplace=False,
    kind='quicksort', na_position='last', ignore_index=False, key=None):
    kbz__qvmt = dict(axis=axis, inplace=inplace, kind=kind, ignore_index=
        ignore_index, key=key)
    wcxf__wtnln = dict(axis=0, inplace=False, kind='quicksort',
        ignore_index=False, key=None)
    check_unsupported_args('Series.sort_values', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not is_overload_bool(ascending):
        raise BodoError(
            "Series.sort_values(): 'ascending' parameter must be of type bool")
    if not is_overload_constant_str(na_position) or get_overload_const_str(
        na_position) not in ('first', 'last'):
        raise_bodo_error(
            "Series.sort_values(): 'na_position' should either be 'first' or 'last'"
            )

    def impl(S, axis=0, ascending=True, inplace=False, kind='quicksort',
        na_position='last', ignore_index=False, key=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        ana__gnyf = bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,),
            index, ('$_bodo_col_',))
        fwaz__fwx = ana__gnyf.sort_values(['$_bodo_col_'], ascending=
            ascending, inplace=inplace, na_position=na_position)
        hedma__sko = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(
            fwaz__fwx, 0)
        ylvd__llbk = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(
            fwaz__fwx)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
            ylvd__llbk, name)
    return impl


def get_bin_inds(bins, arr):
    return arr


@overload(get_bin_inds, inline='always', no_unliteral=True)
def overload_get_bin_inds(bins, arr, is_nullable=True, include_lowest=True):
    assert is_overload_constant_bool(is_nullable)
    vhz__nns = is_overload_true(is_nullable)
    acxuc__tss = (
        'def impl(bins, arr, is_nullable=True, include_lowest=True):\n')
    acxuc__tss += '  numba.parfors.parfor.init_prange()\n'
    acxuc__tss += '  n = len(arr)\n'
    if vhz__nns:
        acxuc__tss += (
            '  out_arr = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n')
    else:
        acxuc__tss += '  out_arr = np.empty(n, np.int64)\n'
    acxuc__tss += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    acxuc__tss += '    if bodo.libs.array_kernels.isna(arr, i):\n'
    if vhz__nns:
        acxuc__tss += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    else:
        acxuc__tss += '      out_arr[i] = -1\n'
    acxuc__tss += '      continue\n'
    acxuc__tss += '    val = arr[i]\n'
    acxuc__tss += '    if include_lowest and val == bins[0]:\n'
    acxuc__tss += '      ind = 1\n'
    acxuc__tss += '    else:\n'
    acxuc__tss += '      ind = np.searchsorted(bins, val)\n'
    acxuc__tss += '    if ind == 0 or ind == len(bins):\n'
    if vhz__nns:
        acxuc__tss += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    else:
        acxuc__tss += '      out_arr[i] = -1\n'
    acxuc__tss += '    else:\n'
    acxuc__tss += '      out_arr[i] = ind - 1\n'
    acxuc__tss += '  return out_arr\n'
    bsc__zfa = {}
    exec(acxuc__tss, {'bodo': bodo, 'np': np, 'numba': numba}, bsc__zfa)
    impl = bsc__zfa['impl']
    return impl


@register_jitable
def _round_frac(x, precision: int):
    if not np.isfinite(x) or x == 0:
        return x
    else:
        inegk__idqr, bra__vpvm = np.divmod(x, 1)
        if inegk__idqr == 0:
            znwiz__vfvxv = -int(np.floor(np.log10(abs(bra__vpvm)))
                ) - 1 + precision
        else:
            znwiz__vfvxv = precision
        return np.around(x, znwiz__vfvxv)


@register_jitable
def _infer_precision(base_precision: int, bins) ->int:
    for precision in range(base_precision, 20):
        xbb__hfzpx = np.array([_round_frac(b, precision) for b in bins])
        if len(np.unique(xbb__hfzpx)) == len(bins):
            return precision
    return base_precision


def get_bin_labels(bins):
    pass


@overload(get_bin_labels, no_unliteral=True)
def overload_get_bin_labels(bins, right=True, include_lowest=True):
    dtype = np.float64 if isinstance(bins.dtype, types.Integer) else bins.dtype
    if dtype == bodo.datetime64ns:
        pgmt__ohqz = bodo.timedelta64ns(1)

        def impl_dt64(bins, right=True, include_lowest=True):
            gri__cffn = bins.copy()
            if right and include_lowest:
                gri__cffn[0] = gri__cffn[0] - pgmt__ohqz
            umb__xfsan = bodo.libs.interval_arr_ext.init_interval_array(
                gri__cffn[:-1], gri__cffn[1:])
            return bodo.hiframes.pd_index_ext.init_interval_index(umb__xfsan,
                None)
        return impl_dt64

    def impl(bins, right=True, include_lowest=True):
        base_precision = 3
        precision = _infer_precision(base_precision, bins)
        gri__cffn = np.array([_round_frac(b, precision) for b in bins],
            dtype=dtype)
        if right and include_lowest:
            gri__cffn[0] = gri__cffn[0] - 10.0 ** -precision
        umb__xfsan = bodo.libs.interval_arr_ext.init_interval_array(gri__cffn
            [:-1], gri__cffn[1:])
        return bodo.hiframes.pd_index_ext.init_interval_index(umb__xfsan, None)
    return impl


def get_output_bin_counts(count_series, nbins):
    pass


@overload(get_output_bin_counts, no_unliteral=True)
def overload_get_output_bin_counts(count_series, nbins):

    def impl(count_series, nbins):
        vqf__sask = bodo.hiframes.pd_series_ext.get_series_data(count_series)
        fbfu__jbw = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(count_series))
        hedma__sko = np.zeros(nbins, np.int64)
        for qbtq__ayyb in range(len(vqf__sask)):
            hedma__sko[fbfu__jbw[qbtq__ayyb]] = vqf__sask[qbtq__ayyb]
        return hedma__sko
    return impl


def compute_bins(nbins, min_val, max_val):
    pass


@overload(compute_bins, no_unliteral=True)
def overload_compute_bins(nbins, min_val, max_val, right=True):

    def impl(nbins, min_val, max_val, right=True):
        if nbins < 1:
            raise ValueError('`bins` should be a positive integer.')
        min_val = min_val + 0.0
        max_val = max_val + 0.0
        if np.isinf(min_val) or np.isinf(max_val):
            raise ValueError(
                'cannot specify integer `bins` when input data contains infinity'
                )
        elif min_val == max_val:
            min_val -= 0.001 * abs(min_val) if min_val != 0 else 0.001
            max_val += 0.001 * abs(max_val) if max_val != 0 else 0.001
            bins = np.linspace(min_val, max_val, nbins + 1, endpoint=True)
        else:
            bins = np.linspace(min_val, max_val, nbins + 1, endpoint=True)
            jyvex__hrmo = (max_val - min_val) * 0.001
            if right:
                bins[0] -= jyvex__hrmo
            else:
                bins[-1] += jyvex__hrmo
        return bins
    return impl


@overload_method(SeriesType, 'value_counts', inline='always', no_unliteral=True
    )
def overload_series_value_counts(S, normalize=False, sort=True, ascending=
    False, bins=None, dropna=True, _index_name=None):
    kbz__qvmt = dict(dropna=dropna)
    wcxf__wtnln = dict(dropna=True)
    check_unsupported_args('Series.value_counts', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not is_overload_constant_bool(normalize):
        raise_bodo_error(
            'Series.value_counts(): normalize argument must be a constant boolean'
            )
    if not is_overload_constant_bool(sort):
        raise_bodo_error(
            'Series.value_counts(): sort argument must be a constant boolean')
    if not is_overload_bool(ascending):
        raise_bodo_error(
            'Series.value_counts(): ascending argument must be a constant boolean'
            )
    amyo__lmfxh = not is_overload_none(bins)
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.value_counts()')
    acxuc__tss = 'def impl(\n'
    acxuc__tss += '    S,\n'
    acxuc__tss += '    normalize=False,\n'
    acxuc__tss += '    sort=True,\n'
    acxuc__tss += '    ascending=False,\n'
    acxuc__tss += '    bins=None,\n'
    acxuc__tss += '    dropna=True,\n'
    acxuc__tss += (
        '    _index_name=None,  # bodo argument. See groupby.value_counts\n')
    acxuc__tss += '):\n'
    acxuc__tss += '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    acxuc__tss += (
        '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
    acxuc__tss += '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    if amyo__lmfxh:
        acxuc__tss += '    right = True\n'
        acxuc__tss += _gen_bins_handling(bins, S.dtype)
        acxuc__tss += '    arr = get_bin_inds(bins, arr)\n'
    acxuc__tss += (
        '    in_df = bodo.hiframes.pd_dataframe_ext.init_dataframe(\n')
    acxuc__tss += "        (arr,), index, ('$_bodo_col2_',)\n"
    acxuc__tss += '    )\n'
    acxuc__tss += "    count_series = in_df.groupby('$_bodo_col2_').size()\n"
    if amyo__lmfxh:
        acxuc__tss += """    count_series = bodo.gatherv(count_series, allgather=True, warn_if_rep=False)
"""
        acxuc__tss += (
            '    count_arr = get_output_bin_counts(count_series, len(bins) - 1)\n'
            )
        acxuc__tss += '    index = get_bin_labels(bins)\n'
    else:
        acxuc__tss += (
            '    count_arr = bodo.hiframes.pd_series_ext.get_series_data(count_series)\n'
            )
        acxuc__tss += '    ind_arr = bodo.utils.conversion.coerce_to_array(\n'
        acxuc__tss += (
            '        bodo.hiframes.pd_series_ext.get_series_index(count_series)\n'
            )
        acxuc__tss += '    )\n'
        acxuc__tss += """    index = bodo.utils.conversion.index_from_array(ind_arr, name=_index_name)
"""
    acxuc__tss += (
        '    res = bodo.hiframes.pd_series_ext.init_series(count_arr, index, name)\n'
        )
    if is_overload_true(sort):
        acxuc__tss += '    res = res.sort_values(ascending=ascending)\n'
    if is_overload_true(normalize):
        gncfw__ucyzu = 'len(S)' if amyo__lmfxh else 'count_arr.sum()'
        acxuc__tss += f'    res = res / float({gncfw__ucyzu})\n'
    acxuc__tss += '    return res\n'
    bsc__zfa = {}
    exec(acxuc__tss, {'bodo': bodo, 'pd': pd, 'np': np, 'get_bin_inds':
        get_bin_inds, 'get_bin_labels': get_bin_labels,
        'get_output_bin_counts': get_output_bin_counts, 'compute_bins':
        compute_bins}, bsc__zfa)
    impl = bsc__zfa['impl']
    return impl


def _gen_bins_handling(bins, dtype):
    acxuc__tss = ''
    if isinstance(bins, types.Integer):
        acxuc__tss += '    min_val = bodo.libs.array_ops.array_op_min(arr)\n'
        acxuc__tss += '    max_val = bodo.libs.array_ops.array_op_max(arr)\n'
        if dtype == bodo.datetime64ns:
            acxuc__tss += '    min_val = min_val.value\n'
            acxuc__tss += '    max_val = max_val.value\n'
        acxuc__tss += (
            '    bins = compute_bins(bins, min_val, max_val, right)\n')
        if dtype == bodo.datetime64ns:
            acxuc__tss += (
                "    bins = bins.astype(np.int64).view(np.dtype('datetime64[ns]'))\n"
                )
    else:
        acxuc__tss += (
            '    bins = bodo.utils.conversion.coerce_to_ndarray(bins)\n')
    return acxuc__tss


@overload(pd.cut, inline='always', no_unliteral=True)
def overload_cut(x, bins, right=True, labels=None, retbins=False, precision
    =3, include_lowest=False, duplicates='raise', ordered=True):
    kbz__qvmt = dict(right=right, labels=labels, retbins=retbins, precision
        =precision, duplicates=duplicates, ordered=ordered)
    wcxf__wtnln = dict(right=True, labels=None, retbins=False, precision=3,
        duplicates='raise', ordered=True)
    check_unsupported_args('pandas.cut', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='General')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(x, 'pandas.cut()'
        )
    acxuc__tss = 'def impl(\n'
    acxuc__tss += '    x,\n'
    acxuc__tss += '    bins,\n'
    acxuc__tss += '    right=True,\n'
    acxuc__tss += '    labels=None,\n'
    acxuc__tss += '    retbins=False,\n'
    acxuc__tss += '    precision=3,\n'
    acxuc__tss += '    include_lowest=False,\n'
    acxuc__tss += "    duplicates='raise',\n"
    acxuc__tss += '    ordered=True\n'
    acxuc__tss += '):\n'
    if isinstance(x, SeriesType):
        acxuc__tss += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(x)\n')
        acxuc__tss += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(x)\n')
        acxuc__tss += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(x)\n')
    else:
        acxuc__tss += '    arr = bodo.utils.conversion.coerce_to_array(x)\n'
    acxuc__tss += _gen_bins_handling(bins, x.dtype)
    acxuc__tss += '    arr = get_bin_inds(bins, arr, False, include_lowest)\n'
    acxuc__tss += (
        '    label_index = get_bin_labels(bins, right, include_lowest)\n')
    acxuc__tss += """    cat_dtype = bodo.hiframes.pd_categorical_ext.init_cat_dtype(label_index, ordered, None, None)
"""
    acxuc__tss += """    out_arr = bodo.hiframes.pd_categorical_ext.init_categorical_array(arr, cat_dtype)
"""
    if isinstance(x, SeriesType):
        acxuc__tss += (
            '    res = bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        acxuc__tss += '    return res\n'
    else:
        acxuc__tss += '    return out_arr\n'
    bsc__zfa = {}
    exec(acxuc__tss, {'bodo': bodo, 'pd': pd, 'np': np, 'get_bin_inds':
        get_bin_inds, 'get_bin_labels': get_bin_labels,
        'get_output_bin_counts': get_output_bin_counts, 'compute_bins':
        compute_bins}, bsc__zfa)
    impl = bsc__zfa['impl']
    return impl


def _get_q_list(q):
    return q


@overload(_get_q_list, no_unliteral=True)
def get_q_list_overload(q):
    if is_overload_int(q):
        return lambda q: np.linspace(0, 1, q + 1)
    return lambda q: q


@overload(pd.unique, inline='always', no_unliteral=True)
def overload_unique(values):
    if not is_series_type(values) and not (bodo.utils.utils.is_array_typ(
        values, False) and values.ndim == 1):
        raise BodoError(
            "pd.unique(): 'values' must be either a Series or a 1-d array")
    if is_series_type(values):

        def impl(values):
            arr = bodo.hiframes.pd_series_ext.get_series_data(values)
            return bodo.allgatherv(bodo.libs.array_kernels.unique(arr), False)
        return impl
    else:
        return lambda values: bodo.allgatherv(bodo.libs.array_kernels.
            unique(values), False)


@overload(pd.qcut, inline='always', no_unliteral=True)
def overload_qcut(x, q, labels=None, retbins=False, precision=3, duplicates
    ='raise'):
    kbz__qvmt = dict(labels=labels, retbins=retbins, precision=precision,
        duplicates=duplicates)
    wcxf__wtnln = dict(labels=None, retbins=False, precision=3, duplicates=
        'raise')
    check_unsupported_args('pandas.qcut', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='General')
    if not (is_overload_int(q) or is_iterable_type(q)):
        raise BodoError(
            "pd.qcut(): 'q' should be an integer or a list of quantiles")
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(x,
        'pandas.qcut()')

    def impl(x, q, labels=None, retbins=False, precision=3, duplicates='raise'
        ):
        cxrkx__dudyf = _get_q_list(q)
        arr = bodo.utils.conversion.coerce_to_array(x)
        bins = bodo.libs.array_ops.array_op_quantile(arr, cxrkx__dudyf)
        return pd.cut(x, bins, include_lowest=True)
    return impl


@overload_method(SeriesType, 'groupby', inline='always', no_unliteral=True)
def overload_series_groupby(S, by=None, axis=0, level=None, as_index=True,
    sort=True, group_keys=True, squeeze=False, observed=True, dropna=True):
    kbz__qvmt = dict(axis=axis, sort=sort, group_keys=group_keys, squeeze=
        squeeze, observed=observed, dropna=dropna)
    wcxf__wtnln = dict(axis=0, sort=True, group_keys=True, squeeze=False,
        observed=True, dropna=True)
    check_unsupported_args('Series.groupby', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='GroupBy')
    if not is_overload_true(as_index):
        raise BodoError('as_index=False only valid with DataFrame')
    if is_overload_none(by) and is_overload_none(level):
        raise BodoError("You have to supply one of 'by' and 'level'")
    if not is_overload_none(by) and not is_overload_none(level):
        raise BodoError(
            "Series.groupby(): 'level' argument should be None if 'by' is not None"
            )
    if not is_overload_none(level):
        if not (is_overload_constant_int(level) and get_overload_const_int(
            level) == 0) or isinstance(S.index, bodo.hiframes.
            pd_multi_index_ext.MultiIndexType):
            raise BodoError(
                "Series.groupby(): MultiIndex case or 'level' other than 0 not supported yet"
                )

        def impl_index(S, by=None, axis=0, level=None, as_index=True, sort=
            True, group_keys=True, squeeze=False, observed=True, dropna=True):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            lrq__jca = bodo.utils.conversion.coerce_to_array(index)
            ana__gnyf = bodo.hiframes.pd_dataframe_ext.init_dataframe((
                lrq__jca, arr), index, (' ', ''))
            return ana__gnyf.groupby(' ')['']
        return impl_index
    yrlu__rwre = by
    if isinstance(by, SeriesType):
        yrlu__rwre = by.data
    if isinstance(yrlu__rwre, DecimalArrayType):
        raise BodoError(
            'Series.groupby(): by argument with decimal type is not supported yet.'
            )
    if isinstance(by, bodo.hiframes.pd_categorical_ext.CategoricalArrayType):
        raise BodoError(
            'Series.groupby(): by argument with categorical type is not supported yet.'
            )

    def impl(S, by=None, axis=0, level=None, as_index=True, sort=True,
        group_keys=True, squeeze=False, observed=True, dropna=True):
        lrq__jca = bodo.utils.conversion.coerce_to_array(by)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        ana__gnyf = bodo.hiframes.pd_dataframe_ext.init_dataframe((lrq__jca,
            arr), index, (' ', ''))
        return ana__gnyf.groupby(' ')['']
    return impl


@overload_method(SeriesType, 'append', inline='always', no_unliteral=True)
def overload_series_append(S, to_append, ignore_index=False,
    verify_integrity=False):
    kbz__qvmt = dict(verify_integrity=verify_integrity)
    wcxf__wtnln = dict(verify_integrity=False)
    check_unsupported_args('Series.append', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.append()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(to_append,
        'Series.append()')
    if isinstance(to_append, SeriesType):
        return (lambda S, to_append, ignore_index=False, verify_integrity=
            False: pd.concat((S, to_append), ignore_index=ignore_index,
            verify_integrity=verify_integrity))
    if isinstance(to_append, types.BaseTuple):
        return (lambda S, to_append, ignore_index=False, verify_integrity=
            False: pd.concat((S,) + to_append, ignore_index=ignore_index,
            verify_integrity=verify_integrity))
    return (lambda S, to_append, ignore_index=False, verify_integrity=False:
        pd.concat([S] + to_append, ignore_index=ignore_index,
        verify_integrity=verify_integrity))


@overload_method(SeriesType, 'isin', inline='always', no_unliteral=True)
def overload_series_isin(S, values):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.isin()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(values,
        'Series.isin()')
    if bodo.utils.utils.is_array_typ(values):

        def impl_arr(S, values):
            uefp__vyd = bodo.utils.conversion.coerce_to_array(values)
            A = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            n = len(A)
            hedma__sko = np.empty(n, np.bool_)
            bodo.libs.array.array_isin(hedma__sko, A, uefp__vyd, False)
            return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                index, name)
        return impl_arr
    if not isinstance(values, (types.Set, types.List)):
        raise BodoError(
            "Series.isin(): 'values' parameter should be a set or a list")

    def impl(S, values):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        hedma__sko = bodo.libs.array_ops.array_op_isin(A, values)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko, index, name)
    return impl


@overload_method(SeriesType, 'quantile', inline='always', no_unliteral=True)
def overload_series_quantile(S, q=0.5, interpolation='linear'):
    kbz__qvmt = dict(interpolation=interpolation)
    wcxf__wtnln = dict(interpolation='linear')
    check_unsupported_args('Series.quantile', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.quantile()')
    if is_iterable_type(q) and isinstance(q.dtype, types.Number):

        def impl_list(S, q=0.5, interpolation='linear'):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            hedma__sko = bodo.libs.array_ops.array_op_quantile(arr, q)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            index = bodo.hiframes.pd_index_ext.init_numeric_index(bodo.
                utils.conversion.coerce_to_array(q), None)
            return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                index, name)
        return impl_list
    elif isinstance(q, (float, types.Number)) or is_overload_constant_int(q):

        def impl(S, q=0.5, interpolation='linear'):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            return bodo.libs.array_ops.array_op_quantile(arr, q)
        return impl
    else:
        raise BodoError(
            f'Series.quantile() q type must be float or iterable of floats only.'
            )


@overload_method(SeriesType, 'nunique', inline='always', no_unliteral=True)
def overload_series_nunique(S, dropna=True):
    if not is_overload_bool(dropna):
        raise BodoError('Series.nunique: dropna must be a boolean value')

    def impl(S, dropna=True):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_kernels.nunique(arr, dropna)
    return impl


@overload_method(SeriesType, 'unique', inline='always', no_unliteral=True)
def overload_series_unique(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        uamie__mddcx = bodo.libs.array_kernels.unique(arr)
        return bodo.allgatherv(uamie__mddcx, False)
    return impl


@overload_method(SeriesType, 'describe', inline='always', no_unliteral=True)
def overload_series_describe(S, percentiles=None, include=None, exclude=
    None, datetime_is_numeric=True):
    kbz__qvmt = dict(percentiles=percentiles, include=include, exclude=
        exclude, datetime_is_numeric=datetime_is_numeric)
    wcxf__wtnln = dict(percentiles=None, include=None, exclude=None,
        datetime_is_numeric=True)
    check_unsupported_args('Series.describe', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.describe()')
    if not (isinstance(S.data, types.Array) and (isinstance(S.data.dtype,
        types.Number) or S.data.dtype == bodo.datetime64ns)
        ) and not isinstance(S.data, IntegerArrayType):
        raise BodoError(f'describe() column input type {S.data} not supported.'
            )
    if S.data.dtype == bodo.datetime64ns:

        def impl_dt(S, percentiles=None, include=None, exclude=None,
            datetime_is_numeric=True):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            return bodo.hiframes.pd_series_ext.init_series(bodo.libs.
                array_ops.array_op_describe(arr), bodo.utils.conversion.
                convert_to_index(['count', 'mean', 'min', '25%', '50%',
                '75%', 'max']), name)
        return impl_dt

    def impl(S, percentiles=None, include=None, exclude=None,
        datetime_is_numeric=True):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(bodo.libs.array_ops.
            array_op_describe(arr), bodo.utils.conversion.convert_to_index(
            ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']), name)
    return impl


@overload_method(SeriesType, 'memory_usage', inline='always', no_unliteral=True
    )
def overload_series_memory_usage(S, index=True, deep=False):
    if is_overload_true(index):

        def impl(S, index=True, deep=False):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            return arr.nbytes + index.nbytes
        return impl
    else:

        def impl(S, index=True, deep=False):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            return arr.nbytes
        return impl


def binary_str_fillna_inplace_series_impl(is_binary=False):
    if is_binary:
        aixs__baydh = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
    else:
        aixs__baydh = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
    acxuc__tss = '\n'.join(('def impl(', '    S,', '    value=None,',
        '    method=None,', '    axis=None,', '    inplace=False,',
        '    limit=None,', '    downcast=None,', '):',
        '    in_arr = bodo.hiframes.pd_series_ext.get_series_data(S)',
        '    fill_arr = bodo.hiframes.pd_series_ext.get_series_data(value)',
        '    n = len(in_arr)', '    nf = len(fill_arr)',
        "    assert n == nf, 'fillna() requires same length arrays'",
        f'    out_arr = {aixs__baydh}(n, -1)',
        '    for j in numba.parfors.parfor.internal_prange(n):',
        '        s = in_arr[j]',
        '        if bodo.libs.array_kernels.isna(in_arr, j) and not bodo.libs.array_kernels.isna('
        , '            fill_arr, j', '        ):',
        '            s = fill_arr[j]', '        out_arr[j] = s',
        '    bodo.libs.str_arr_ext.move_str_binary_arr_payload(in_arr, out_arr)'
        ))
    tkfae__yfou = dict()
    exec(acxuc__tss, {'bodo': bodo, 'numba': numba}, tkfae__yfou)
    oml__ystum = tkfae__yfou['impl']
    return oml__ystum


def binary_str_fillna_inplace_impl(is_binary=False):
    if is_binary:
        aixs__baydh = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
    else:
        aixs__baydh = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
    acxuc__tss = 'def impl(S,\n'
    acxuc__tss += '     value=None,\n'
    acxuc__tss += '    method=None,\n'
    acxuc__tss += '    axis=None,\n'
    acxuc__tss += '    inplace=False,\n'
    acxuc__tss += '    limit=None,\n'
    acxuc__tss += '   downcast=None,\n'
    acxuc__tss += '):\n'
    acxuc__tss += (
        '    in_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    acxuc__tss += '    n = len(in_arr)\n'
    acxuc__tss += f'    out_arr = {aixs__baydh}(n, -1)\n'
    acxuc__tss += '    for j in numba.parfors.parfor.internal_prange(n):\n'
    acxuc__tss += '        s = in_arr[j]\n'
    acxuc__tss += '        if bodo.libs.array_kernels.isna(in_arr, j):\n'
    acxuc__tss += '            s = value\n'
    acxuc__tss += '        out_arr[j] = s\n'
    acxuc__tss += (
        '    bodo.libs.str_arr_ext.move_str_binary_arr_payload(in_arr, out_arr)\n'
        )
    tkfae__yfou = dict()
    exec(acxuc__tss, {'bodo': bodo, 'numba': numba}, tkfae__yfou)
    oml__ystum = tkfae__yfou['impl']
    return oml__ystum


def fillna_inplace_series_impl(S, value=None, method=None, axis=None,
    inplace=False, limit=None, downcast=None):
    kdwkq__bvuy = bodo.hiframes.pd_series_ext.get_series_data(S)
    fhawb__bsyz = bodo.hiframes.pd_series_ext.get_series_data(value)
    for qbtq__ayyb in numba.parfors.parfor.internal_prange(len(kdwkq__bvuy)):
        s = kdwkq__bvuy[qbtq__ayyb]
        if bodo.libs.array_kernels.isna(kdwkq__bvuy, qbtq__ayyb
            ) and not bodo.libs.array_kernels.isna(fhawb__bsyz, qbtq__ayyb):
            s = fhawb__bsyz[qbtq__ayyb]
        kdwkq__bvuy[qbtq__ayyb] = s


def fillna_inplace_impl(S, value=None, method=None, axis=None, inplace=
    False, limit=None, downcast=None):
    kdwkq__bvuy = bodo.hiframes.pd_series_ext.get_series_data(S)
    for qbtq__ayyb in numba.parfors.parfor.internal_prange(len(kdwkq__bvuy)):
        s = kdwkq__bvuy[qbtq__ayyb]
        if bodo.libs.array_kernels.isna(kdwkq__bvuy, qbtq__ayyb):
            s = value
        kdwkq__bvuy[qbtq__ayyb] = s


def str_fillna_alloc_series_impl(S, value=None, method=None, axis=None,
    inplace=False, limit=None, downcast=None):
    kdwkq__bvuy = bodo.hiframes.pd_series_ext.get_series_data(S)
    index = bodo.hiframes.pd_series_ext.get_series_index(S)
    name = bodo.hiframes.pd_series_ext.get_series_name(S)
    fhawb__bsyz = bodo.hiframes.pd_series_ext.get_series_data(value)
    n = len(kdwkq__bvuy)
    hedma__sko = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
    for ara__eml in numba.parfors.parfor.internal_prange(n):
        s = kdwkq__bvuy[ara__eml]
        if bodo.libs.array_kernels.isna(kdwkq__bvuy, ara__eml
            ) and not bodo.libs.array_kernels.isna(fhawb__bsyz, ara__eml):
            s = fhawb__bsyz[ara__eml]
        hedma__sko[ara__eml] = s
        if bodo.libs.array_kernels.isna(kdwkq__bvuy, ara__eml
            ) and bodo.libs.array_kernels.isna(fhawb__bsyz, ara__eml):
            bodo.libs.array_kernels.setna(hedma__sko, ara__eml)
    return bodo.hiframes.pd_series_ext.init_series(hedma__sko, index, name)


def fillna_series_impl(S, value=None, method=None, axis=None, inplace=False,
    limit=None, downcast=None):
    kdwkq__bvuy = bodo.hiframes.pd_series_ext.get_series_data(S)
    index = bodo.hiframes.pd_series_ext.get_series_index(S)
    name = bodo.hiframes.pd_series_ext.get_series_name(S)
    fhawb__bsyz = bodo.hiframes.pd_series_ext.get_series_data(value)
    n = len(kdwkq__bvuy)
    hedma__sko = bodo.utils.utils.alloc_type(n, kdwkq__bvuy.dtype, (-1,))
    for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
        s = kdwkq__bvuy[qbtq__ayyb]
        if bodo.libs.array_kernels.isna(kdwkq__bvuy, qbtq__ayyb
            ) and not bodo.libs.array_kernels.isna(fhawb__bsyz, qbtq__ayyb):
            s = fhawb__bsyz[qbtq__ayyb]
        hedma__sko[qbtq__ayyb] = s
    return bodo.hiframes.pd_series_ext.init_series(hedma__sko, index, name)


@overload_method(SeriesType, 'fillna', no_unliteral=True)
def overload_series_fillna(S, value=None, method=None, axis=None, inplace=
    False, limit=None, downcast=None):
    kbz__qvmt = dict(limit=limit, downcast=downcast)
    wcxf__wtnln = dict(limit=None, downcast=None)
    check_unsupported_args('Series.fillna', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    xnvju__tuji = not is_overload_none(value)
    nbqp__aeejh = not is_overload_none(method)
    if xnvju__tuji and nbqp__aeejh:
        raise BodoError(
            "Series.fillna(): Cannot specify both 'value' and 'method'.")
    if not xnvju__tuji and not nbqp__aeejh:
        raise BodoError(
            "Series.fillna(): Must specify one of 'value' and 'method'.")
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.fillna(): axis argument not supported')
    elif is_iterable_type(value) and not isinstance(value, SeriesType):
        raise BodoError('Series.fillna(): "value" parameter cannot be a list')
    elif is_var_size_item_array_type(S.data
        ) and not S.dtype == bodo.string_type:
        raise BodoError(
            f'Series.fillna() with inplace=True not supported for {S.dtype} values yet.'
            )
    if not is_overload_constant_bool(inplace):
        raise_bodo_error(
            "Series.fillna(): 'inplace' argument must be a constant boolean")
    if nbqp__aeejh:
        if is_overload_true(inplace):
            raise BodoError(
                "Series.fillna() with inplace=True not supported with 'method' argument yet."
                )
        zfzbo__yny = (
            "Series.fillna(): 'method' argument if provided must be a constant string and one of ('backfill', 'bfill', 'pad' 'ffill')."
            )
        if not is_overload_constant_str(method):
            raise_bodo_error(zfzbo__yny)
        elif get_overload_const_str(method) not in ('backfill', 'bfill',
            'pad', 'ffill'):
            raise BodoError(zfzbo__yny)
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.fillna()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(value,
        'Series.fillna()')
    iryzc__esg = element_type(S.data)
    cvhpp__thz = None
    if xnvju__tuji:
        cvhpp__thz = element_type(types.unliteral(value))
    if cvhpp__thz and not can_replace(iryzc__esg, cvhpp__thz):
        raise BodoError(
            f'Series.fillna(): Cannot use value type {cvhpp__thz} with series type {iryzc__esg}'
            )
    if is_overload_true(inplace):
        if S.dtype == bodo.string_type:
            if S.data == bodo.dict_str_arr_type:
                raise_bodo_error(
                    "Series.fillna(): 'inplace' not supported for dictionary-encoded string arrays yet."
                    )
            if is_overload_constant_str(value) and get_overload_const_str(value
                ) == '':
                return (lambda S, value=None, method=None, axis=None,
                    inplace=False, limit=None, downcast=None: bodo.libs.
                    str_arr_ext.set_null_bits_to_value(bodo.hiframes.
                    pd_series_ext.get_series_data(S), -1))
            if isinstance(value, SeriesType):
                return binary_str_fillna_inplace_series_impl(is_binary=False)
            return binary_str_fillna_inplace_impl(is_binary=False)
        if S.dtype == bodo.bytes_type:
            if is_overload_constant_bytes(value) and get_overload_const_bytes(
                value) == b'':
                return (lambda S, value=None, method=None, axis=None,
                    inplace=False, limit=None, downcast=None: bodo.libs.
                    str_arr_ext.set_null_bits_to_value(bodo.hiframes.
                    pd_series_ext.get_series_data(S), -1))
            if isinstance(value, SeriesType):
                return binary_str_fillna_inplace_series_impl(is_binary=True)
            return binary_str_fillna_inplace_impl(is_binary=True)
        else:
            if isinstance(value, SeriesType):
                return fillna_inplace_series_impl
            return fillna_inplace_impl
    else:
        xvj__uvw = to_str_arr_if_dict_array(S.data)
        if isinstance(value, SeriesType):

            def fillna_series_impl(S, value=None, method=None, axis=None,
                inplace=False, limit=None, downcast=None):
                kdwkq__bvuy = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                fhawb__bsyz = bodo.hiframes.pd_series_ext.get_series_data(value
                    )
                n = len(kdwkq__bvuy)
                hedma__sko = bodo.utils.utils.alloc_type(n, xvj__uvw, (-1,))
                for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(kdwkq__bvuy, qbtq__ayyb
                        ) and bodo.libs.array_kernels.isna(fhawb__bsyz,
                        qbtq__ayyb):
                        bodo.libs.array_kernels.setna(hedma__sko, qbtq__ayyb)
                        continue
                    if bodo.libs.array_kernels.isna(kdwkq__bvuy, qbtq__ayyb):
                        hedma__sko[qbtq__ayyb
                            ] = bodo.utils.conversion.unbox_if_timestamp(
                            fhawb__bsyz[qbtq__ayyb])
                        continue
                    hedma__sko[qbtq__ayyb
                        ] = bodo.utils.conversion.unbox_if_timestamp(
                        kdwkq__bvuy[qbtq__ayyb])
                return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                    index, name)
            return fillna_series_impl
        if nbqp__aeejh:
            aoyt__tjo = (types.unicode_type, types.bool_, bodo.datetime64ns,
                bodo.timedelta64ns)
            if not isinstance(iryzc__esg, (types.Integer, types.Float)
                ) and iryzc__esg not in aoyt__tjo:
                raise BodoError(
                    f"Series.fillna(): series of type {iryzc__esg} are not supported with 'method' argument."
                    )

            def fillna_method_impl(S, value=None, method=None, axis=None,
                inplace=False, limit=None, downcast=None):
                kdwkq__bvuy = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                hedma__sko = bodo.libs.array_kernels.ffill_bfill_arr(
                    kdwkq__bvuy, method)
                return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                    index, name)
            return fillna_method_impl

        def fillna_impl(S, value=None, method=None, axis=None, inplace=
            False, limit=None, downcast=None):
            value = bodo.utils.conversion.unbox_if_timestamp(value)
            kdwkq__bvuy = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            n = len(kdwkq__bvuy)
            hedma__sko = bodo.utils.utils.alloc_type(n, xvj__uvw, (-1,))
            for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
                s = bodo.utils.conversion.unbox_if_timestamp(kdwkq__bvuy[
                    qbtq__ayyb])
                if bodo.libs.array_kernels.isna(kdwkq__bvuy, qbtq__ayyb):
                    s = value
                hedma__sko[qbtq__ayyb] = s
            return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                index, name)
        return fillna_impl


def create_fillna_specific_method_overload(overload_name):

    def overload_series_fillna_specific_method(S, axis=None, inplace=False,
        limit=None, downcast=None):
        tci__nig = {'ffill': 'ffill', 'bfill': 'bfill', 'pad': 'ffill',
            'backfill': 'bfill'}[overload_name]
        kbz__qvmt = dict(limit=limit, downcast=downcast)
        wcxf__wtnln = dict(limit=None, downcast=None)
        check_unsupported_args(f'Series.{overload_name}', kbz__qvmt,
            wcxf__wtnln, package_name='pandas', module_name='Series')
        if not (is_overload_none(axis) or is_overload_zero(axis)):
            raise BodoError(
                f'Series.{overload_name}(): axis argument not supported')
        iryzc__esg = element_type(S.data)
        aoyt__tjo = (types.unicode_type, types.bool_, bodo.datetime64ns,
            bodo.timedelta64ns)
        if not isinstance(iryzc__esg, (types.Integer, types.Float)
            ) and iryzc__esg not in aoyt__tjo:
            raise BodoError(
                f'Series.{overload_name}(): series of type {iryzc__esg} are not supported.'
                )

        def impl(S, axis=None, inplace=False, limit=None, downcast=None):
            kdwkq__bvuy = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            hedma__sko = bodo.libs.array_kernels.ffill_bfill_arr(kdwkq__bvuy,
                tci__nig)
            return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                index, name)
        return impl
    return overload_series_fillna_specific_method


fillna_specific_methods = 'ffill', 'bfill', 'pad', 'backfill'


def _install_fillna_specific_methods():
    for overload_name in fillna_specific_methods:
        ghkm__twqk = create_fillna_specific_method_overload(overload_name)
        overload_method(SeriesType, overload_name, no_unliteral=True)(
            ghkm__twqk)


_install_fillna_specific_methods()


def check_unsupported_types(S, to_replace, value):
    if any(bodo.utils.utils.is_array_typ(x, True) for x in [S.dtype,
        to_replace, value]):
        tmmyg__nrus = (
            'Series.replace(): only support with Scalar, List, or Dictionary')
        raise BodoError(tmmyg__nrus)
    elif isinstance(to_replace, types.DictType) and not is_overload_none(value
        ):
        tmmyg__nrus = (
            "Series.replace(): 'value' must be None when 'to_replace' is a dictionary"
            )
        raise BodoError(tmmyg__nrus)
    elif any(isinstance(x, (PandasTimestampType, PDTimeDeltaType)) for x in
        [to_replace, value]):
        tmmyg__nrus = (
            f'Series.replace(): Not supported for types {to_replace} and {value}'
            )
        raise BodoError(tmmyg__nrus)


def series_replace_error_checking(S, to_replace, value, inplace, limit,
    regex, method):
    kbz__qvmt = dict(inplace=inplace, limit=limit, regex=regex, method=method)
    efzb__yddzt = dict(inplace=False, limit=None, regex=False, method='pad')
    check_unsupported_args('Series.replace', kbz__qvmt, efzb__yddzt,
        package_name='pandas', module_name='Series')
    check_unsupported_types(S, to_replace, value)


@overload_method(SeriesType, 'replace', inline='always', no_unliteral=True)
def overload_series_replace(S, to_replace=None, value=None, inplace=False,
    limit=None, regex=False, method='pad'):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.replace()')
    series_replace_error_checking(S, to_replace, value, inplace, limit,
        regex, method)
    iryzc__esg = element_type(S.data)
    if isinstance(to_replace, types.DictType):
        cmsfp__npjs = element_type(to_replace.key_type)
        cvhpp__thz = element_type(to_replace.value_type)
    else:
        cmsfp__npjs = element_type(to_replace)
        cvhpp__thz = element_type(value)
    zuajb__ylv = None
    if iryzc__esg != types.unliteral(cmsfp__npjs):
        if bodo.utils.typing.equality_always_false(iryzc__esg, types.
            unliteral(cmsfp__npjs)
            ) or not bodo.utils.typing.types_equality_exists(iryzc__esg,
            cmsfp__npjs):

            def impl(S, to_replace=None, value=None, inplace=False, limit=
                None, regex=False, method='pad'):
                return S.copy()
            return impl
        if isinstance(iryzc__esg, (types.Float, types.Integer)
            ) or iryzc__esg == np.bool_:
            zuajb__ylv = iryzc__esg
    if not can_replace(iryzc__esg, types.unliteral(cvhpp__thz)):

        def impl(S, to_replace=None, value=None, inplace=False, limit=None,
            regex=False, method='pad'):
            return S.copy()
        return impl
    yrhp__oom = to_str_arr_if_dict_array(S.data)
    if isinstance(yrhp__oom, CategoricalArrayType):

        def cat_impl(S, to_replace=None, value=None, inplace=False, limit=
            None, regex=False, method='pad'):
            kdwkq__bvuy = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            return bodo.hiframes.pd_series_ext.init_series(kdwkq__bvuy.
                replace(to_replace, value), index, name)
        return cat_impl

    def impl(S, to_replace=None, value=None, inplace=False, limit=None,
        regex=False, method='pad'):
        kdwkq__bvuy = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        n = len(kdwkq__bvuy)
        hedma__sko = bodo.utils.utils.alloc_type(n, yrhp__oom, (-1,))
        bgl__zeldf = build_replace_dict(to_replace, value, zuajb__ylv)
        for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(kdwkq__bvuy, qbtq__ayyb):
                bodo.libs.array_kernels.setna(hedma__sko, qbtq__ayyb)
                continue
            s = kdwkq__bvuy[qbtq__ayyb]
            if s in bgl__zeldf:
                s = bgl__zeldf[s]
            hedma__sko[qbtq__ayyb] = s
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko, index, name)
    return impl


def build_replace_dict(to_replace, value, key_dtype_conv):
    pass


@overload(build_replace_dict)
def _build_replace_dict(to_replace, value, key_dtype_conv):
    zvh__dez = isinstance(to_replace, (types.Number, Decimal128Type)
        ) or to_replace in [bodo.string_type, types.boolean, bodo.bytes_type]
    okdn__nnzsy = is_iterable_type(to_replace)
    gpfp__wnuq = isinstance(value, (types.Number, Decimal128Type)
        ) or value in [bodo.string_type, bodo.bytes_type, types.boolean]
    obsqi__gqh = is_iterable_type(value)
    if zvh__dez and gpfp__wnuq:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                bgl__zeldf = {}
                bgl__zeldf[key_dtype_conv(to_replace)] = value
                return bgl__zeldf
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            bgl__zeldf = {}
            bgl__zeldf[to_replace] = value
            return bgl__zeldf
        return impl
    if okdn__nnzsy and gpfp__wnuq:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                bgl__zeldf = {}
                for ztjw__qjz in to_replace:
                    bgl__zeldf[key_dtype_conv(ztjw__qjz)] = value
                return bgl__zeldf
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            bgl__zeldf = {}
            for ztjw__qjz in to_replace:
                bgl__zeldf[ztjw__qjz] = value
            return bgl__zeldf
        return impl
    if okdn__nnzsy and obsqi__gqh:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                bgl__zeldf = {}
                assert len(to_replace) == len(value
                    ), 'To_replace and value lengths must be the same'
                for qbtq__ayyb in range(len(to_replace)):
                    bgl__zeldf[key_dtype_conv(to_replace[qbtq__ayyb])] = value[
                        qbtq__ayyb]
                return bgl__zeldf
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            bgl__zeldf = {}
            assert len(to_replace) == len(value
                ), 'To_replace and value lengths must be the same'
            for qbtq__ayyb in range(len(to_replace)):
                bgl__zeldf[to_replace[qbtq__ayyb]] = value[qbtq__ayyb]
            return bgl__zeldf
        return impl
    if isinstance(to_replace, numba.types.DictType) and is_overload_none(value
        ):
        return lambda to_replace, value, key_dtype_conv: to_replace
    raise BodoError(
        'Series.replace(): Not supported for types to_replace={} and value={}'
        .format(to_replace, value))


@overload_method(SeriesType, 'diff', inline='always', no_unliteral=True)
def overload_series_diff(S, periods=1):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.diff()')
    if not (isinstance(S.data, types.Array) and (isinstance(S.data.dtype,
        types.Number) or S.data.dtype == bodo.datetime64ns)):
        raise BodoError(
            f'Series.diff() column input type {S.data} not supported.')
    if not is_overload_int(periods):
        raise BodoError("Series.diff(): 'periods' input must be an integer.")
    if S.data == types.Array(bodo.datetime64ns, 1, 'C'):

        def impl_datetime(S, periods=1):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            hedma__sko = bodo.hiframes.series_impl.dt64_arr_sub(arr, bodo.
                hiframes.rolling.shift(arr, periods, False))
            return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                index, name)
        return impl_datetime

    def impl(S, periods=1):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        hedma__sko = arr - bodo.hiframes.rolling.shift(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko, index, name)
    return impl


@overload_method(SeriesType, 'explode', inline='always', no_unliteral=True)
def overload_series_explode(S, ignore_index=False):
    from bodo.hiframes.split_impl import string_array_split_view_type
    kbz__qvmt = dict(ignore_index=ignore_index)
    epxge__sljq = dict(ignore_index=False)
    check_unsupported_args('Series.explode', kbz__qvmt, epxge__sljq,
        package_name='pandas', module_name='Series')
    if not (isinstance(S.data, ArrayItemArrayType) or S.data ==
        string_array_split_view_type):
        return lambda S, ignore_index=False: S.copy()

    def impl(S, ignore_index=False):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        abm__les = bodo.utils.conversion.index_to_array(index)
        hedma__sko, bjfn__fhrhg = bodo.libs.array_kernels.explode(arr, abm__les
            )
        ylvd__llbk = bodo.utils.conversion.index_from_array(bjfn__fhrhg)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
            ylvd__llbk, name)
    return impl


@overload(np.digitize, inline='always', no_unliteral=True)
def overload_series_np_digitize(x, bins, right=False):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(x,
        'numpy.digitize()')
    if isinstance(x, SeriesType):

        def impl(x, bins, right=False):
            arr = bodo.hiframes.pd_series_ext.get_series_data(x)
            return np.digitize(arr, bins, right)
        return impl


@overload(np.argmax, inline='always', no_unliteral=True)
def argmax_overload(a, axis=None, out=None):
    if isinstance(a, types.Array) and is_overload_constant_int(axis
        ) and get_overload_const_int(axis) == 1:

        def impl(a, axis=None, out=None):
            qqwli__lxu = np.empty(len(a), a.dtype)
            numba.parfors.parfor.init_prange()
            n = len(a)
            for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
                qqwli__lxu[qbtq__ayyb] = np.argmax(a[qbtq__ayyb])
            return qqwli__lxu
        return impl


@overload(np.argmin, inline='always', no_unliteral=True)
def argmin_overload(a, axis=None, out=None):
    if isinstance(a, types.Array) and is_overload_constant_int(axis
        ) and get_overload_const_int(axis) == 1:

        def impl(a, axis=None, out=None):
            iqb__xsnzz = np.empty(len(a), a.dtype)
            numba.parfors.parfor.init_prange()
            n = len(a)
            for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
                iqb__xsnzz[qbtq__ayyb] = np.argmin(a[qbtq__ayyb])
            return iqb__xsnzz
        return impl


def overload_series_np_dot(a, b, out=None):
    if (isinstance(a, SeriesType) or isinstance(b, SeriesType)
        ) and not is_overload_none(out):
        raise BodoError("np.dot(): 'out' parameter not supported yet")
    if isinstance(a, SeriesType):

        def impl(a, b, out=None):
            arr = bodo.hiframes.pd_series_ext.get_series_data(a)
            return np.dot(arr, b)
        return impl
    if isinstance(b, SeriesType):

        def impl(a, b, out=None):
            arr = bodo.hiframes.pd_series_ext.get_series_data(b)
            return np.dot(a, arr)
        return impl


overload(np.dot, inline='always', no_unliteral=True)(overload_series_np_dot)
overload(operator.matmul, inline='always', no_unliteral=True)(
    overload_series_np_dot)


@overload_method(SeriesType, 'dropna', inline='always', no_unliteral=True)
def overload_series_dropna(S, axis=0, inplace=False, how=None):
    kbz__qvmt = dict(axis=axis, inplace=inplace, how=how)
    gsqce__mfua = dict(axis=0, inplace=False, how=None)
    check_unsupported_args('Series.dropna', kbz__qvmt, gsqce__mfua,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.dropna()')
    if S.dtype == bodo.string_type:

        def dropna_str_impl(S, axis=0, inplace=False, how=None):
            kdwkq__bvuy = bodo.hiframes.pd_series_ext.get_series_data(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            fdrss__teum = S.notna().values
            abm__les = bodo.utils.conversion.extract_index_array(S)
            ylvd__llbk = bodo.utils.conversion.convert_to_index(abm__les[
                fdrss__teum])
            hedma__sko = (bodo.hiframes.series_kernels.
                _series_dropna_str_alloc_impl_inner(kdwkq__bvuy))
            return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                ylvd__llbk, name)
        return dropna_str_impl
    else:

        def dropna_impl(S, axis=0, inplace=False, how=None):
            kdwkq__bvuy = bodo.hiframes.pd_series_ext.get_series_data(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            abm__les = bodo.utils.conversion.extract_index_array(S)
            fdrss__teum = S.notna().values
            ylvd__llbk = bodo.utils.conversion.convert_to_index(abm__les[
                fdrss__teum])
            hedma__sko = kdwkq__bvuy[fdrss__teum]
            return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                ylvd__llbk, name)
        return dropna_impl


@overload_method(SeriesType, 'shift', inline='always', no_unliteral=True)
def overload_series_shift(S, periods=1, freq=None, axis=0, fill_value=None):
    kbz__qvmt = dict(freq=freq, axis=axis, fill_value=fill_value)
    wcxf__wtnln = dict(freq=None, axis=0, fill_value=None)
    check_unsupported_args('Series.shift', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.shift()')
    if not is_supported_shift_array_type(S.data):
        raise BodoError(
            f"Series.shift(): Series input type '{S.data.dtype}' not supported yet."
            )
    if not is_overload_int(periods):
        raise BodoError("Series.shift(): 'periods' input must be an integer.")

    def impl(S, periods=1, freq=None, axis=0, fill_value=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        hedma__sko = bodo.hiframes.rolling.shift(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko, index, name)
    return impl


@overload_method(SeriesType, 'pct_change', inline='always', no_unliteral=True)
def overload_series_pct_change(S, periods=1, fill_method='pad', limit=None,
    freq=None):
    kbz__qvmt = dict(fill_method=fill_method, limit=limit, freq=freq)
    wcxf__wtnln = dict(fill_method='pad', limit=None, freq=None)
    check_unsupported_args('Series.pct_change', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not is_overload_int(periods):
        raise BodoError(
            'Series.pct_change(): periods argument must be an Integer')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.pct_change()')

    def impl(S, periods=1, fill_method='pad', limit=None, freq=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        hedma__sko = bodo.hiframes.rolling.pct_change(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko, index, name)
    return impl


def create_series_mask_where_overload(func_name):

    def overload_series_mask_where(S, cond, other=np.nan, inplace=False,
        axis=None, level=None, errors='raise', try_cast=False):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
            f'Series.{func_name}()')
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(other,
            f'Series.{func_name}()')
        _validate_arguments_mask_where(f'Series.{func_name}', S, cond,
            other, inplace, axis, level, errors, try_cast)
        if is_overload_constant_nan(other):
            uzmke__fnf = 'None'
        else:
            uzmke__fnf = 'other'
        acxuc__tss = """def impl(S, cond, other=np.nan, inplace=False, axis=None, level=None, errors='raise',try_cast=False):
"""
        if func_name == 'mask':
            acxuc__tss += '  cond = ~cond\n'
        acxuc__tss += (
            '  arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        acxuc__tss += (
            '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        acxuc__tss += (
            '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        acxuc__tss += (
            f'  out_arr = bodo.hiframes.series_impl.where_impl(cond, arr, {uzmke__fnf})\n'
            )
        acxuc__tss += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        bsc__zfa = {}
        exec(acxuc__tss, {'bodo': bodo, 'np': np}, bsc__zfa)
        impl = bsc__zfa['impl']
        return impl
    return overload_series_mask_where


def _install_series_mask_where_overload():
    for func_name in ('mask', 'where'):
        ghkm__twqk = create_series_mask_where_overload(func_name)
        overload_method(SeriesType, func_name, no_unliteral=True)(ghkm__twqk)


_install_series_mask_where_overload()


def _validate_arguments_mask_where(func_name, S, cond, other, inplace, axis,
    level, errors, try_cast):
    kbz__qvmt = dict(inplace=inplace, level=level, errors=errors, try_cast=
        try_cast)
    wcxf__wtnln = dict(inplace=False, level=None, errors='raise', try_cast=
        False)
    check_unsupported_args(f'{func_name}', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error(f'{func_name}(): axis argument not supported')
    if isinstance(other, SeriesType):
        _validate_self_other_mask_where(func_name, S.data, other.data)
    else:
        _validate_self_other_mask_where(func_name, S.data, other)
    if not (isinstance(cond, (SeriesType, types.Array, BooleanArrayType)) and
        cond.ndim == 1 and cond.dtype == types.bool_):
        raise BodoError(
            f"{func_name}() 'cond' argument must be a Series or 1-dim array of booleans"
            )


def _validate_self_other_mask_where(func_name, arr, other, max_ndim=1,
    is_default=False):
    if not (isinstance(arr, types.Array) or isinstance(arr,
        BooleanArrayType) or isinstance(arr, IntegerArrayType) or bodo.
        utils.utils.is_array_typ(arr, False) and arr.dtype in [bodo.
        string_type, bodo.bytes_type] or isinstance(arr, bodo.
        CategoricalArrayType) and arr.dtype.elem_type not in [bodo.
        datetime64ns, bodo.timedelta64ns, bodo.pd_timestamp_type, bodo.
        pd_timedelta_type]):
        raise BodoError(
            f'{func_name}() Series data with type {arr} not yet supported')
    detcx__ieuz = is_overload_constant_nan(other)
    if not (is_default or detcx__ieuz or is_scalar_type(other) or 
        isinstance(other, types.Array) and other.ndim >= 1 and other.ndim <=
        max_ndim or isinstance(other, SeriesType) and (isinstance(arr,
        types.Array) or arr.dtype in [bodo.string_type, bodo.bytes_type]) or
        is_str_arr_type(other) and (arr.dtype == bodo.string_type or 
        isinstance(arr, bodo.CategoricalArrayType) and arr.dtype.elem_type ==
        bodo.string_type) or isinstance(other, BinaryArrayType) and (arr.
        dtype == bodo.bytes_type or isinstance(arr, bodo.
        CategoricalArrayType) and arr.dtype.elem_type == bodo.bytes_type) or
        (not (isinstance(other, (StringArrayType, BinaryArrayType)) or 
        other == bodo.dict_str_arr_type) and (isinstance(arr.dtype, types.
        Integer) and (bodo.utils.utils.is_array_typ(other) and isinstance(
        other.dtype, types.Integer) or is_series_type(other) and isinstance
        (other.dtype, types.Integer))) or (bodo.utils.utils.is_array_typ(
        other) and arr.dtype == other.dtype or is_series_type(other) and 
        arr.dtype == other.dtype)) and (isinstance(arr, BooleanArrayType) or
        isinstance(arr, IntegerArrayType))):
        raise BodoError(
            f"{func_name}() 'other' must be a scalar, non-categorical series, 1-dim numpy array or StringArray with a matching type for Series."
            )
    if not is_default:
        if isinstance(arr.dtype, bodo.PDCategoricalDtype):
            bwiv__llbb = arr.dtype.elem_type
        else:
            bwiv__llbb = arr.dtype
        if is_iterable_type(other):
            boyyf__wua = other.dtype
        elif detcx__ieuz:
            boyyf__wua = types.float64
        else:
            boyyf__wua = types.unliteral(other)
        if not detcx__ieuz and not is_common_scalar_dtype([bwiv__llbb,
            boyyf__wua]):
            raise BodoError(
                f"{func_name}() series and 'other' must share a common type.")


def create_explicit_binary_op_overload(op):

    def overload_series_explicit_binary_op(S, other, level=None, fill_value
        =None, axis=0):
        kbz__qvmt = dict(level=level, axis=axis)
        wcxf__wtnln = dict(level=None, axis=0)
        check_unsupported_args('series.{}'.format(op.__name__), kbz__qvmt,
            wcxf__wtnln, package_name='pandas', module_name='Series')
        pwsu__jbuij = other == string_type or is_overload_constant_str(other)
        kydq__lnjrr = is_iterable_type(other) and other.dtype == string_type
        ovpul__brx = S.dtype == string_type and (op == operator.add and (
            pwsu__jbuij or kydq__lnjrr) or op == operator.mul and
            isinstance(other, types.Integer))
        weiz__tonqx = S.dtype == bodo.timedelta64ns
        lyzrr__jzwou = S.dtype == bodo.datetime64ns
        suw__qdwsn = is_iterable_type(other) and (other.dtype ==
            datetime_timedelta_type or other.dtype == bodo.timedelta64ns)
        qla__mbbml = is_iterable_type(other) and (other.dtype ==
            datetime_datetime_type or other.dtype == pd_timestamp_type or 
            other.dtype == bodo.datetime64ns)
        zwxm__zyk = weiz__tonqx and (suw__qdwsn or qla__mbbml
            ) or lyzrr__jzwou and suw__qdwsn
        zwxm__zyk = zwxm__zyk and op == operator.add
        if not (isinstance(S.dtype, types.Number) or ovpul__brx or zwxm__zyk):
            raise BodoError(f'Unsupported types for Series.{op.__name__}')
        xas__uneh = numba.core.registry.cpu_target.typing_context
        if is_scalar_type(other):
            args = S.data, other
            yrhp__oom = xas__uneh.resolve_function_type(op, args, {}
                ).return_type
            if isinstance(S.data, IntegerArrayType
                ) and yrhp__oom == types.Array(types.bool_, 1, 'C'):
                yrhp__oom = boolean_array

            def impl_scalar(S, other, level=None, fill_value=None, axis=0):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                numba.parfors.parfor.init_prange()
                other = bodo.utils.conversion.unbox_if_timestamp(other)
                n = len(arr)
                hedma__sko = bodo.utils.utils.alloc_type(n, yrhp__oom, (-1,))
                for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
                    pnz__lylb = bodo.libs.array_kernels.isna(arr, qbtq__ayyb)
                    if pnz__lylb:
                        if fill_value is None:
                            bodo.libs.array_kernels.setna(hedma__sko,
                                qbtq__ayyb)
                        else:
                            hedma__sko[qbtq__ayyb] = op(fill_value, other)
                    else:
                        hedma__sko[qbtq__ayyb] = op(arr[qbtq__ayyb], other)
                return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                    index, name)
            return impl_scalar
        args = S.data, types.Array(other.dtype, 1, 'C')
        yrhp__oom = xas__uneh.resolve_function_type(op, args, {}).return_type
        if isinstance(S.data, IntegerArrayType) and yrhp__oom == types.Array(
            types.bool_, 1, 'C'):
            yrhp__oom = boolean_array

        def impl(S, other, level=None, fill_value=None, axis=0):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            xmetc__otrw = bodo.utils.conversion.coerce_to_array(other)
            numba.parfors.parfor.init_prange()
            n = len(arr)
            hedma__sko = bodo.utils.utils.alloc_type(n, yrhp__oom, (-1,))
            for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
                pnz__lylb = bodo.libs.array_kernels.isna(arr, qbtq__ayyb)
                qgpmn__yvrnd = bodo.libs.array_kernels.isna(xmetc__otrw,
                    qbtq__ayyb)
                if pnz__lylb and qgpmn__yvrnd:
                    bodo.libs.array_kernels.setna(hedma__sko, qbtq__ayyb)
                elif pnz__lylb:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(hedma__sko, qbtq__ayyb)
                    else:
                        hedma__sko[qbtq__ayyb] = op(fill_value, xmetc__otrw
                            [qbtq__ayyb])
                elif qgpmn__yvrnd:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(hedma__sko, qbtq__ayyb)
                    else:
                        hedma__sko[qbtq__ayyb] = op(arr[qbtq__ayyb], fill_value
                            )
                else:
                    hedma__sko[qbtq__ayyb] = op(arr[qbtq__ayyb],
                        xmetc__otrw[qbtq__ayyb])
            return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                index, name)
        return impl
    return overload_series_explicit_binary_op


def create_explicit_binary_reverse_op_overload(op):

    def overload_series_explicit_binary_reverse_op(S, other, level=None,
        fill_value=None, axis=0):
        if not is_overload_none(level):
            raise BodoError('level argument not supported')
        if not is_overload_zero(axis):
            raise BodoError('axis argument not supported')
        if not isinstance(S.dtype, types.Number):
            raise BodoError('only numeric values supported')
        xas__uneh = numba.core.registry.cpu_target.typing_context
        if isinstance(other, types.Number):
            args = other, S.data
            yrhp__oom = xas__uneh.resolve_function_type(op, args, {}
                ).return_type
            if isinstance(S.data, IntegerArrayType
                ) and yrhp__oom == types.Array(types.bool_, 1, 'C'):
                yrhp__oom = boolean_array

            def impl_scalar(S, other, level=None, fill_value=None, axis=0):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                numba.parfors.parfor.init_prange()
                n = len(arr)
                hedma__sko = bodo.utils.utils.alloc_type(n, yrhp__oom, None)
                for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
                    pnz__lylb = bodo.libs.array_kernels.isna(arr, qbtq__ayyb)
                    if pnz__lylb:
                        if fill_value is None:
                            bodo.libs.array_kernels.setna(hedma__sko,
                                qbtq__ayyb)
                        else:
                            hedma__sko[qbtq__ayyb] = op(other, fill_value)
                    else:
                        hedma__sko[qbtq__ayyb] = op(other, arr[qbtq__ayyb])
                return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                    index, name)
            return impl_scalar
        args = types.Array(other.dtype, 1, 'C'), S.data
        yrhp__oom = xas__uneh.resolve_function_type(op, args, {}).return_type
        if isinstance(S.data, IntegerArrayType) and yrhp__oom == types.Array(
            types.bool_, 1, 'C'):
            yrhp__oom = boolean_array

        def impl(S, other, level=None, fill_value=None, axis=0):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            xmetc__otrw = bodo.hiframes.pd_series_ext.get_series_data(other)
            numba.parfors.parfor.init_prange()
            n = len(arr)
            hedma__sko = bodo.utils.utils.alloc_type(n, yrhp__oom, None)
            for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
                pnz__lylb = bodo.libs.array_kernels.isna(arr, qbtq__ayyb)
                qgpmn__yvrnd = bodo.libs.array_kernels.isna(xmetc__otrw,
                    qbtq__ayyb)
                hedma__sko[qbtq__ayyb] = op(xmetc__otrw[qbtq__ayyb], arr[
                    qbtq__ayyb])
                if pnz__lylb and qgpmn__yvrnd:
                    bodo.libs.array_kernels.setna(hedma__sko, qbtq__ayyb)
                elif pnz__lylb:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(hedma__sko, qbtq__ayyb)
                    else:
                        hedma__sko[qbtq__ayyb] = op(xmetc__otrw[qbtq__ayyb],
                            fill_value)
                elif qgpmn__yvrnd:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(hedma__sko, qbtq__ayyb)
                    else:
                        hedma__sko[qbtq__ayyb] = op(fill_value, arr[qbtq__ayyb]
                            )
                else:
                    hedma__sko[qbtq__ayyb] = op(xmetc__otrw[qbtq__ayyb],
                        arr[qbtq__ayyb])
            return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                index, name)
        return impl
    return overload_series_explicit_binary_reverse_op


explicit_binop_funcs_two_ways = {operator.add: {'add'}, operator.sub: {
    'sub'}, operator.mul: {'mul'}, operator.truediv: {'div', 'truediv'},
    operator.floordiv: {'floordiv'}, operator.mod: {'mod'}, operator.pow: {
    'pow'}}
explicit_binop_funcs_single = {operator.lt: 'lt', operator.gt: 'gt',
    operator.le: 'le', operator.ge: 'ge', operator.ne: 'ne', operator.eq: 'eq'}
explicit_binop_funcs = set()
split_logical_binops_funcs = [operator.or_, operator.and_]


def _install_explicit_binary_ops():
    for op, wluy__drf in explicit_binop_funcs_two_ways.items():
        for name in wluy__drf:
            ghkm__twqk = create_explicit_binary_op_overload(op)
            qba__ssk = create_explicit_binary_reverse_op_overload(op)
            vvm__fsgsi = 'r' + name
            overload_method(SeriesType, name, no_unliteral=True)(ghkm__twqk)
            overload_method(SeriesType, vvm__fsgsi, no_unliteral=True)(qba__ssk
                )
            explicit_binop_funcs.add(name)
    for op, name in explicit_binop_funcs_single.items():
        ghkm__twqk = create_explicit_binary_op_overload(op)
        overload_method(SeriesType, name, no_unliteral=True)(ghkm__twqk)
        explicit_binop_funcs.add(name)


_install_explicit_binary_ops()


def create_binary_op_overload(op):

    def overload_series_binary_op(lhs, rhs):
        if (isinstance(lhs, SeriesType) and isinstance(rhs, SeriesType) and
            lhs.dtype == bodo.datetime64ns and rhs.dtype == bodo.
            datetime64ns and op == operator.sub):

            def impl_dt64(lhs, rhs):
                arr = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                index = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                name = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                cneyg__flt = (bodo.utils.conversion.
                    get_array_if_series_or_index(rhs))
                hedma__sko = dt64_arr_sub(arr, cneyg__flt)
                return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                    index, name)
            return impl_dt64
        if op in [operator.add, operator.sub] and isinstance(lhs, SeriesType
            ) and lhs.dtype == bodo.datetime64ns and is_offsets_type(rhs):

            def impl_offsets(lhs, rhs):
                arr = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                index = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                name = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                numba.parfors.parfor.init_prange()
                n = len(lhs)
                hedma__sko = np.empty(n, np.dtype('datetime64[ns]'))
                for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(arr, qbtq__ayyb):
                        bodo.libs.array_kernels.setna(hedma__sko, qbtq__ayyb)
                        continue
                    cby__wlalp = (bodo.hiframes.pd_timestamp_ext.
                        convert_datetime64_to_timestamp(arr[qbtq__ayyb]))
                    pqi__aejic = op(cby__wlalp, rhs)
                    hedma__sko[qbtq__ayyb
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        pqi__aejic.value)
                return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                    index, name)
            return impl_offsets
        if op == operator.add and is_offsets_type(lhs) and isinstance(rhs,
            SeriesType) and rhs.dtype == bodo.datetime64ns:

            def impl(lhs, rhs):
                return op(rhs, lhs)
            return impl
        if isinstance(lhs, SeriesType):
            if lhs.dtype in [bodo.datetime64ns, bodo.timedelta64ns]:

                def impl(lhs, rhs):
                    arr = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                    index = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                    name = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                    cneyg__flt = (bodo.utils.conversion.
                        get_array_if_series_or_index(rhs))
                    hedma__sko = op(arr, bodo.utils.conversion.
                        unbox_if_timestamp(cneyg__flt))
                    return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                        index, name)
                return impl

            def impl(lhs, rhs):
                arr = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                index = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                name = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                cneyg__flt = (bodo.utils.conversion.
                    get_array_if_series_or_index(rhs))
                hedma__sko = op(arr, cneyg__flt)
                return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                    index, name)
            return impl
        if isinstance(rhs, SeriesType):
            if rhs.dtype in [bodo.datetime64ns, bodo.timedelta64ns]:

                def impl(lhs, rhs):
                    arr = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                    index = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                    name = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                    nwil__ajibp = (bodo.utils.conversion.
                        get_array_if_series_or_index(lhs))
                    hedma__sko = op(bodo.utils.conversion.
                        unbox_if_timestamp(nwil__ajibp), arr)
                    return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                        index, name)
                return impl

            def impl(lhs, rhs):
                arr = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                index = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                name = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                nwil__ajibp = (bodo.utils.conversion.
                    get_array_if_series_or_index(lhs))
                hedma__sko = op(nwil__ajibp, arr)
                return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                    index, name)
            return impl
    return overload_series_binary_op


skips = list(explicit_binop_funcs_two_ways.keys()) + list(
    explicit_binop_funcs_single.keys()) + split_logical_binops_funcs


def _install_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_binary_ops:
        if op in skips:
            continue
        ghkm__twqk = create_binary_op_overload(op)
        overload(op)(ghkm__twqk)


_install_binary_ops()


def dt64_arr_sub(arg1, arg2):
    return arg1 - arg2


@overload(dt64_arr_sub, no_unliteral=True)
def overload_dt64_arr_sub(arg1, arg2):
    assert arg1 == types.Array(bodo.datetime64ns, 1, 'C'
        ) and arg2 == types.Array(bodo.datetime64ns, 1, 'C')
    nndko__iddbk = np.dtype('timedelta64[ns]')

    def impl(arg1, arg2):
        numba.parfors.parfor.init_prange()
        n = len(arg1)
        S = np.empty(n, nndko__iddbk)
        for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(arg1, qbtq__ayyb
                ) or bodo.libs.array_kernels.isna(arg2, qbtq__ayyb):
                bodo.libs.array_kernels.setna(S, qbtq__ayyb)
                continue
            S[qbtq__ayyb
                ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                bodo.hiframes.pd_timestamp_ext.dt64_to_integer(arg1[
                qbtq__ayyb]) - bodo.hiframes.pd_timestamp_ext.
                dt64_to_integer(arg2[qbtq__ayyb]))
        return S
    return impl


def create_inplace_binary_op_overload(op):

    def overload_series_inplace_binary_op(S, other):
        if isinstance(S, SeriesType) or isinstance(other, SeriesType):

            def impl(S, other):
                arr = bodo.utils.conversion.get_array_if_series_or_index(S)
                xmetc__otrw = (bodo.utils.conversion.
                    get_array_if_series_or_index(other))
                op(arr, xmetc__otrw)
                return S
            return impl
    return overload_series_inplace_binary_op


def _install_inplace_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_inplace_binary_ops:
        ghkm__twqk = create_inplace_binary_op_overload(op)
        overload(op, no_unliteral=True)(ghkm__twqk)


_install_inplace_binary_ops()


def create_unary_op_overload(op):

    def overload_series_unary_op(S):
        if isinstance(S, SeriesType):

            def impl(S):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                hedma__sko = op(arr)
                return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                    index, name)
            return impl
    return overload_series_unary_op


def _install_unary_ops():
    for op in bodo.hiframes.pd_series_ext.series_unary_ops:
        ghkm__twqk = create_unary_op_overload(op)
        overload(op, no_unliteral=True)(ghkm__twqk)


_install_unary_ops()


def create_ufunc_overload(ufunc):
    if ufunc.nin == 1:

        def overload_series_ufunc_nin_1(S):
            if isinstance(S, SeriesType):

                def impl(S):
                    arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                    index = bodo.hiframes.pd_series_ext.get_series_index(S)
                    name = bodo.hiframes.pd_series_ext.get_series_name(S)
                    hedma__sko = ufunc(arr)
                    return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                        index, name)
                return impl
        return overload_series_ufunc_nin_1
    elif ufunc.nin == 2:

        def overload_series_ufunc_nin_2(S1, S2):
            if isinstance(S1, SeriesType):

                def impl(S1, S2):
                    arr = bodo.hiframes.pd_series_ext.get_series_data(S1)
                    index = bodo.hiframes.pd_series_ext.get_series_index(S1)
                    name = bodo.hiframes.pd_series_ext.get_series_name(S1)
                    xmetc__otrw = (bodo.utils.conversion.
                        get_array_if_series_or_index(S2))
                    hedma__sko = ufunc(arr, xmetc__otrw)
                    return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                        index, name)
                return impl
            elif isinstance(S2, SeriesType):

                def impl(S1, S2):
                    arr = bodo.utils.conversion.get_array_if_series_or_index(S1
                        )
                    xmetc__otrw = bodo.hiframes.pd_series_ext.get_series_data(
                        S2)
                    index = bodo.hiframes.pd_series_ext.get_series_index(S2)
                    name = bodo.hiframes.pd_series_ext.get_series_name(S2)
                    hedma__sko = ufunc(arr, xmetc__otrw)
                    return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                        index, name)
                return impl
        return overload_series_ufunc_nin_2
    else:
        raise RuntimeError(
            "Don't know how to register ufuncs from ufunc_db with arity > 2")


def _install_np_ufuncs():
    import numba.np.ufunc_db
    for ufunc in numba.np.ufunc_db.get_ufuncs():
        ghkm__twqk = create_ufunc_overload(ufunc)
        overload(ufunc, no_unliteral=True)(ghkm__twqk)


_install_np_ufuncs()


def argsort(A):
    return np.argsort(A)


@overload(argsort, no_unliteral=True)
def overload_argsort(A):

    def impl(A):
        n = len(A)
        sku__mzumh = bodo.libs.str_arr_ext.to_list_if_immutable_arr((A.copy(),)
            )
        uvpru__iaeah = np.arange(n),
        bodo.libs.timsort.sort(sku__mzumh, 0, n, uvpru__iaeah)
        return uvpru__iaeah[0]
    return impl


@overload(pd.to_numeric, inline='always', no_unliteral=True)
def overload_to_numeric(arg_a, errors='raise', downcast=None):
    if not is_overload_none(downcast) and not (is_overload_constant_str(
        downcast) and get_overload_const_str(downcast) in ('integer',
        'signed', 'unsigned', 'float')):
        raise BodoError(
            'pd.to_numeric(): invalid downcasting method provided {}'.
            format(downcast))
    out_dtype = types.float64
    if not is_overload_none(downcast):
        vjo__zllf = get_overload_const_str(downcast)
        if vjo__zllf in ('integer', 'signed'):
            out_dtype = types.int64
        elif vjo__zllf == 'unsigned':
            out_dtype = types.uint64
        else:
            assert vjo__zllf == 'float'
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(arg_a,
        'pandas.to_numeric()')
    if isinstance(arg_a, (types.Array, IntegerArrayType)):
        return lambda arg_a, errors='raise', downcast=None: arg_a.astype(
            out_dtype)
    if isinstance(arg_a, SeriesType):

        def impl_series(arg_a, errors='raise', downcast=None):
            kdwkq__bvuy = bodo.hiframes.pd_series_ext.get_series_data(arg_a)
            index = bodo.hiframes.pd_series_ext.get_series_index(arg_a)
            name = bodo.hiframes.pd_series_ext.get_series_name(arg_a)
            hedma__sko = pd.to_numeric(kdwkq__bvuy, errors, downcast)
            return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                index, name)
        return impl_series
    if not is_str_arr_type(arg_a):
        raise BodoError(f'pd.to_numeric(): invalid argument type {arg_a}')
    if out_dtype == types.float64:

        def to_numeric_float_impl(arg_a, errors='raise', downcast=None):
            numba.parfors.parfor.init_prange()
            n = len(arg_a)
            tlu__plbhx = np.empty(n, np.float64)
            for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arg_a, qbtq__ayyb):
                    bodo.libs.array_kernels.setna(tlu__plbhx, qbtq__ayyb)
                else:
                    bodo.libs.str_arr_ext.str_arr_item_to_numeric(tlu__plbhx,
                        qbtq__ayyb, arg_a, qbtq__ayyb)
            return tlu__plbhx
        return to_numeric_float_impl
    else:

        def to_numeric_int_impl(arg_a, errors='raise', downcast=None):
            numba.parfors.parfor.init_prange()
            n = len(arg_a)
            tlu__plbhx = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)
            for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arg_a, qbtq__ayyb):
                    bodo.libs.array_kernels.setna(tlu__plbhx, qbtq__ayyb)
                else:
                    bodo.libs.str_arr_ext.str_arr_item_to_numeric(tlu__plbhx,
                        qbtq__ayyb, arg_a, qbtq__ayyb)
            return tlu__plbhx
        return to_numeric_int_impl


def series_filter_bool(arr, bool_arr):
    return arr[bool_arr]


@infer_global(series_filter_bool)
class SeriesFilterBoolInfer(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 2
        omed__bzm = if_series_to_array_type(args[0])
        if isinstance(omed__bzm, types.Array) and isinstance(omed__bzm.
            dtype, types.Integer):
            omed__bzm = types.Array(types.float64, 1, 'C')
        return omed__bzm(*args)


def where_impl_one_arg(c):
    return np.where(c)


@overload(where_impl_one_arg, no_unliteral=True)
def overload_where_unsupported_one_arg(condition):
    if isinstance(condition, SeriesType) or bodo.utils.utils.is_array_typ(
        condition, False):
        return lambda condition: np.where(condition)


def overload_np_where_one_arg(condition):
    if isinstance(condition, SeriesType):

        def impl_series(condition):
            condition = bodo.hiframes.pd_series_ext.get_series_data(condition)
            return bodo.libs.array_kernels.nonzero(condition)
        return impl_series
    elif bodo.utils.utils.is_array_typ(condition, False):

        def impl(condition):
            return bodo.libs.array_kernels.nonzero(condition)
        return impl


overload(np.where, inline='always', no_unliteral=True)(
    overload_np_where_one_arg)
overload(where_impl_one_arg, inline='always', no_unliteral=True)(
    overload_np_where_one_arg)


def where_impl(c, x, y):
    return np.where(c, x, y)


@overload(where_impl, no_unliteral=True)
def overload_where_unsupported(condition, x, y):
    if not isinstance(condition, (SeriesType, types.Array, BooleanArrayType)
        ) or condition.ndim != 1:
        return lambda condition, x, y: np.where(condition, x, y)


@overload(where_impl, no_unliteral=True)
@overload(np.where, no_unliteral=True)
def overload_np_where(condition, x, y):
    if not isinstance(condition, (SeriesType, types.Array, BooleanArrayType)
        ) or condition.ndim != 1:
        return
    assert condition.dtype == types.bool_, 'invalid condition dtype'
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(x,
        'numpy.where()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(y,
        'numpy.where()')
    ifef__imtd = bodo.utils.utils.is_array_typ(x, True)
    rin__for = bodo.utils.utils.is_array_typ(y, True)
    acxuc__tss = 'def _impl(condition, x, y):\n'
    if isinstance(condition, SeriesType):
        acxuc__tss += (
            '  condition = bodo.hiframes.pd_series_ext.get_series_data(condition)\n'
            )
    if ifef__imtd and not bodo.utils.utils.is_array_typ(x, False):
        acxuc__tss += '  x = bodo.utils.conversion.coerce_to_array(x)\n'
    if rin__for and not bodo.utils.utils.is_array_typ(y, False):
        acxuc__tss += '  y = bodo.utils.conversion.coerce_to_array(y)\n'
    acxuc__tss += '  n = len(condition)\n'
    tzh__egza = x.dtype if ifef__imtd else types.unliteral(x)
    hwjs__uxec = y.dtype if rin__for else types.unliteral(y)
    if not isinstance(x, CategoricalArrayType):
        tzh__egza = element_type(x)
    if not isinstance(y, CategoricalArrayType):
        hwjs__uxec = element_type(y)

    def get_data(x):
        if isinstance(x, SeriesType):
            return x.data
        elif isinstance(x, types.Array):
            return x
        return types.unliteral(x)
    yzr__med = get_data(x)
    fke__gfp = get_data(y)
    is_nullable = any(bodo.utils.typing.is_nullable(uvpru__iaeah) for
        uvpru__iaeah in [yzr__med, fke__gfp])
    if fke__gfp == types.none:
        if isinstance(tzh__egza, types.Number):
            out_dtype = types.Array(types.float64, 1, 'C')
        else:
            out_dtype = to_nullable_type(x)
    elif yzr__med == fke__gfp and not is_nullable:
        out_dtype = dtype_to_array_type(tzh__egza)
    elif tzh__egza == string_type or hwjs__uxec == string_type:
        out_dtype = bodo.string_array_type
    elif yzr__med == bytes_type or (ifef__imtd and tzh__egza == bytes_type
        ) and (fke__gfp == bytes_type or rin__for and hwjs__uxec == bytes_type
        ):
        out_dtype = binary_array_type
    elif isinstance(tzh__egza, bodo.PDCategoricalDtype):
        out_dtype = None
    elif tzh__egza in [bodo.timedelta64ns, bodo.datetime64ns]:
        out_dtype = types.Array(tzh__egza, 1, 'C')
    elif hwjs__uxec in [bodo.timedelta64ns, bodo.datetime64ns]:
        out_dtype = types.Array(hwjs__uxec, 1, 'C')
    else:
        out_dtype = numba.from_dtype(np.promote_types(numba.np.
            numpy_support.as_dtype(tzh__egza), numba.np.numpy_support.
            as_dtype(hwjs__uxec)))
        out_dtype = types.Array(out_dtype, 1, 'C')
        if is_nullable:
            out_dtype = bodo.utils.typing.to_nullable_type(out_dtype)
    if isinstance(tzh__egza, bodo.PDCategoricalDtype):
        jps__dzqfq = 'x'
    else:
        jps__dzqfq = 'out_dtype'
    acxuc__tss += (
        f'  out_arr = bodo.utils.utils.alloc_type(n, {jps__dzqfq}, (-1,))\n')
    if isinstance(tzh__egza, bodo.PDCategoricalDtype):
        acxuc__tss += """  out_codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(out_arr)
"""
        acxuc__tss += (
            '  x_codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(x)\n'
            )
    acxuc__tss += '  for j in numba.parfors.parfor.internal_prange(n):\n'
    acxuc__tss += (
        '    if not bodo.libs.array_kernels.isna(condition, j) and condition[j]:\n'
        )
    if ifef__imtd:
        acxuc__tss += '      if bodo.libs.array_kernels.isna(x, j):\n'
        acxuc__tss += '        setna(out_arr, j)\n'
        acxuc__tss += '        continue\n'
    if isinstance(tzh__egza, bodo.PDCategoricalDtype):
        acxuc__tss += '      out_codes[j] = x_codes[j]\n'
    else:
        acxuc__tss += (
            '      out_arr[j] = bodo.utils.conversion.unbox_if_timestamp({})\n'
            .format('x[j]' if ifef__imtd else 'x'))
    acxuc__tss += '    else:\n'
    if rin__for:
        acxuc__tss += '      if bodo.libs.array_kernels.isna(y, j):\n'
        acxuc__tss += '        setna(out_arr, j)\n'
        acxuc__tss += '        continue\n'
    if fke__gfp == types.none:
        if isinstance(tzh__egza, bodo.PDCategoricalDtype):
            acxuc__tss += '      out_codes[j] = -1\n'
        else:
            acxuc__tss += '      setna(out_arr, j)\n'
    else:
        acxuc__tss += (
            '      out_arr[j] = bodo.utils.conversion.unbox_if_timestamp({})\n'
            .format('y[j]' if rin__for else 'y'))
    acxuc__tss += '  return out_arr\n'
    bsc__zfa = {}
    exec(acxuc__tss, {'bodo': bodo, 'numba': numba, 'setna': bodo.libs.
        array_kernels.setna, 'np': np, 'out_dtype': out_dtype}, bsc__zfa)
    cdvme__nbb = bsc__zfa['_impl']
    return cdvme__nbb


def _verify_np_select_arg_typs(condlist, choicelist, default):
    if isinstance(condlist, (types.List, types.UniTuple)):
        if not (bodo.utils.utils.is_np_array_typ(condlist.dtype) and 
            condlist.dtype.dtype == types.bool_):
            raise BodoError(
                "np.select(): 'condlist' argument must be list or tuple of boolean ndarrays. If passing a Series, please convert with pd.Series.to_numpy()."
                )
    else:
        raise BodoError(
            "np.select(): 'condlist' argument must be list or tuple of boolean ndarrays. If passing a Series, please convert with pd.Series.to_numpy()."
            )
    if not isinstance(choicelist, (types.List, types.UniTuple, types.BaseTuple)
        ):
        raise BodoError(
            "np.select(): 'choicelist' argument must be list or tuple type")
    if isinstance(choicelist, (types.List, types.UniTuple)):
        avf__tpfg = choicelist.dtype
        if not bodo.utils.utils.is_array_typ(avf__tpfg, True):
            raise BodoError(
                "np.select(): 'choicelist' argument must be list or tuple of series/arrays types"
                )
        if is_series_type(avf__tpfg):
            kzjnv__cekx = avf__tpfg.data.dtype
        else:
            kzjnv__cekx = avf__tpfg.dtype
        if isinstance(kzjnv__cekx, bodo.PDCategoricalDtype):
            raise BodoError(
                'np.select(): data with choicelist of type Categorical not yet supported'
                )
        lypar__bexa = avf__tpfg
    else:
        nsi__hcgkd = []
        for avf__tpfg in choicelist:
            if not bodo.utils.utils.is_array_typ(avf__tpfg, True):
                raise BodoError(
                    "np.select(): 'choicelist' argument must be list or tuple of series/arrays types"
                    )
            if is_series_type(avf__tpfg):
                kzjnv__cekx = avf__tpfg.data.dtype
            else:
                kzjnv__cekx = avf__tpfg.dtype
            if isinstance(kzjnv__cekx, bodo.PDCategoricalDtype):
                raise BodoError(
                    'np.select(): data with choicelist of type Categorical not yet supported'
                    )
            nsi__hcgkd.append(kzjnv__cekx)
        if not is_common_scalar_dtype(nsi__hcgkd):
            raise BodoError(
                f"np.select(): 'choicelist' items must be arrays with a commmon data type. Found a tuple with the following data types {choicelist}."
                )
        lypar__bexa = choicelist[0]
    if is_series_type(lypar__bexa):
        lypar__bexa = lypar__bexa.data
    if is_overload_constant_int(default) and get_overload_const_int(default
        ) == 0:
        pass
    else:
        if not is_scalar_type(default):
            raise BodoError(
                "np.select(): 'default' argument must be scalar type")
        if not (is_common_scalar_dtype([default, lypar__bexa.dtype]) or 
            default == types.none or is_overload_constant_nan(default)):
            raise BodoError(
                f"np.select(): 'default' is not type compatible with the array types in choicelist. Choicelist type: {choicelist}, Default type: {default}"
                )
    if not (isinstance(lypar__bexa, types.Array) or isinstance(lypar__bexa,
        BooleanArrayType) or isinstance(lypar__bexa, IntegerArrayType) or 
        bodo.utils.utils.is_array_typ(lypar__bexa, False) and lypar__bexa.
        dtype in [bodo.string_type, bodo.bytes_type]):
        raise BodoError(
            f'np.select(): data with choicelist of type {lypar__bexa} not yet supported'
            )


@overload(np.select)
def overload_np_select(condlist, choicelist, default=0):
    _verify_np_select_arg_typs(condlist, choicelist, default)
    dve__yny = isinstance(choicelist, (types.List, types.UniTuple)
        ) and isinstance(condlist, (types.List, types.UniTuple))
    if isinstance(choicelist, (types.List, types.UniTuple)):
        pvepo__ocqss = choicelist.dtype
    else:
        wstc__vgx = False
        nsi__hcgkd = []
        for avf__tpfg in choicelist:
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(avf__tpfg
                , 'numpy.select()')
            if is_nullable_type(avf__tpfg):
                wstc__vgx = True
            if is_series_type(avf__tpfg):
                kzjnv__cekx = avf__tpfg.data.dtype
            else:
                kzjnv__cekx = avf__tpfg.dtype
            if isinstance(kzjnv__cekx, bodo.PDCategoricalDtype):
                raise BodoError(
                    'np.select(): data with choicelist of type Categorical not yet supported'
                    )
            nsi__hcgkd.append(kzjnv__cekx)
        gfrhq__lpg, rghcs__vziv = get_common_scalar_dtype(nsi__hcgkd)
        if not rghcs__vziv:
            raise BodoError('Internal error in overload_np_select')
        grx__jlxe = dtype_to_array_type(gfrhq__lpg)
        if wstc__vgx:
            grx__jlxe = to_nullable_type(grx__jlxe)
        pvepo__ocqss = grx__jlxe
    if isinstance(pvepo__ocqss, SeriesType):
        pvepo__ocqss = pvepo__ocqss.data
    if is_overload_constant_int(default) and get_overload_const_int(default
        ) == 0:
        zszow__alfh = True
    else:
        zszow__alfh = False
    hfygr__phe = False
    xnb__hbvly = False
    if zszow__alfh:
        if isinstance(pvepo__ocqss.dtype, types.Number):
            pass
        elif pvepo__ocqss.dtype == types.bool_:
            xnb__hbvly = True
        else:
            hfygr__phe = True
            pvepo__ocqss = to_nullable_type(pvepo__ocqss)
    elif default == types.none or is_overload_constant_nan(default):
        hfygr__phe = True
        pvepo__ocqss = to_nullable_type(pvepo__ocqss)
    acxuc__tss = 'def np_select_impl(condlist, choicelist, default=0):\n'
    acxuc__tss += '  if len(condlist) != len(choicelist):\n'
    acxuc__tss += """    raise ValueError('list of cases must be same length as list of conditions')
"""
    acxuc__tss += '  output_len = len(choicelist[0])\n'
    acxuc__tss += (
        '  out = bodo.utils.utils.alloc_type(output_len, alloc_typ, (-1,))\n')
    acxuc__tss += '  for i in range(output_len):\n'
    if hfygr__phe:
        acxuc__tss += '    bodo.libs.array_kernels.setna(out, i)\n'
    elif xnb__hbvly:
        acxuc__tss += '    out[i] = False\n'
    else:
        acxuc__tss += '    out[i] = default\n'
    if dve__yny:
        acxuc__tss += '  for i in range(len(condlist) - 1, -1, -1):\n'
        acxuc__tss += '    cond = condlist[i]\n'
        acxuc__tss += '    choice = choicelist[i]\n'
        acxuc__tss += '    out = np.where(cond, choice, out)\n'
    else:
        for qbtq__ayyb in range(len(choicelist) - 1, -1, -1):
            acxuc__tss += f'  cond = condlist[{qbtq__ayyb}]\n'
            acxuc__tss += f'  choice = choicelist[{qbtq__ayyb}]\n'
            acxuc__tss += f'  out = np.where(cond, choice, out)\n'
    acxuc__tss += '  return out'
    bsc__zfa = dict()
    exec(acxuc__tss, {'bodo': bodo, 'numba': numba, 'setna': bodo.libs.
        array_kernels.setna, 'np': np, 'alloc_typ': pvepo__ocqss}, bsc__zfa)
    impl = bsc__zfa['np_select_impl']
    return impl


@overload_method(SeriesType, 'duplicated', inline='always', no_unliteral=True)
def overload_series_duplicated(S, keep='first'):

    def impl(S, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        hedma__sko = bodo.libs.array_kernels.duplicated((arr,))
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko, index, name)
    return impl


@overload_method(SeriesType, 'drop_duplicates', inline='always',
    no_unliteral=True)
def overload_series_drop_duplicates(S, subset=None, keep='first', inplace=False
    ):
    kbz__qvmt = dict(subset=subset, keep=keep, inplace=inplace)
    wcxf__wtnln = dict(subset=None, keep='first', inplace=False)
    check_unsupported_args('Series.drop_duplicates', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')

    def impl(S, subset=None, keep='first', inplace=False):
        qtro__lrgk = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(S))
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        (qtro__lrgk,), abm__les = bodo.libs.array_kernels.drop_duplicates((
            qtro__lrgk,), index, 1)
        index = bodo.utils.conversion.index_from_array(abm__les)
        return bodo.hiframes.pd_series_ext.init_series(qtro__lrgk, index, name)
    return impl


@overload_method(SeriesType, 'between', inline='always', no_unliteral=True)
def overload_series_between(S, left, right, inclusive='both'):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.between()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(left,
        'Series.between()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(right,
        'Series.between()')
    ysynr__nmxzm = element_type(S.data)
    if not is_common_scalar_dtype([ysynr__nmxzm, left]):
        raise_bodo_error(
            "Series.between(): 'left' must be compariable with the Series data"
            )
    if not is_common_scalar_dtype([ysynr__nmxzm, right]):
        raise_bodo_error(
            "Series.between(): 'right' must be compariable with the Series data"
            )
    if not is_overload_constant_str(inclusive) or get_overload_const_str(
        inclusive) not in ('both', 'neither'):
        raise_bodo_error(
            "Series.between(): 'inclusive' must be a constant string and one of ('both', 'neither')"
            )

    def impl(S, left, right, inclusive='both'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        numba.parfors.parfor.init_prange()
        n = len(arr)
        hedma__sko = np.empty(n, np.bool_)
        for qbtq__ayyb in numba.parfors.parfor.internal_prange(n):
            acujo__vnwbj = bodo.utils.conversion.box_if_dt64(arr[qbtq__ayyb])
            if inclusive == 'both':
                hedma__sko[qbtq__ayyb
                    ] = acujo__vnwbj <= right and acujo__vnwbj >= left
            else:
                hedma__sko[qbtq__ayyb
                    ] = acujo__vnwbj < right and acujo__vnwbj > left
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko, index, name)
    return impl


@overload_method(SeriesType, 'repeat', inline='always', no_unliteral=True)
def overload_series_repeat(S, repeats, axis=None):
    kbz__qvmt = dict(axis=axis)
    wcxf__wtnln = dict(axis=None)
    check_unsupported_args('Series.repeat', kbz__qvmt, wcxf__wtnln,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.repeat()')
    if not (isinstance(repeats, types.Integer) or is_iterable_type(repeats) and
        isinstance(repeats.dtype, types.Integer)):
        raise BodoError(
            "Series.repeat(): 'repeats' should be an integer or array of integers"
            )
    if isinstance(repeats, types.Integer):

        def impl_int(S, repeats, axis=None):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            abm__les = bodo.utils.conversion.index_to_array(index)
            hedma__sko = bodo.libs.array_kernels.repeat_kernel(arr, repeats)
            bjfn__fhrhg = bodo.libs.array_kernels.repeat_kernel(abm__les,
                repeats)
            ylvd__llbk = bodo.utils.conversion.index_from_array(bjfn__fhrhg)
            return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
                ylvd__llbk, name)
        return impl_int

    def impl_arr(S, repeats, axis=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        abm__les = bodo.utils.conversion.index_to_array(index)
        repeats = bodo.utils.conversion.coerce_to_array(repeats)
        hedma__sko = bodo.libs.array_kernels.repeat_kernel(arr, repeats)
        bjfn__fhrhg = bodo.libs.array_kernels.repeat_kernel(abm__les, repeats)
        ylvd__llbk = bodo.utils.conversion.index_from_array(bjfn__fhrhg)
        return bodo.hiframes.pd_series_ext.init_series(hedma__sko,
            ylvd__llbk, name)
    return impl_arr


@overload_method(SeriesType, 'to_dict', no_unliteral=True)
def overload_to_dict(S, into=None):

    def impl(S, into=None):
        uvpru__iaeah = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(S))
        n = len(uvpru__iaeah)
        uyzs__arbw = {}
        for qbtq__ayyb in range(n):
            acujo__vnwbj = bodo.utils.conversion.box_if_dt64(uvpru__iaeah[
                qbtq__ayyb])
            uyzs__arbw[index[qbtq__ayyb]] = acujo__vnwbj
        return uyzs__arbw
    return impl


@overload_method(SeriesType, 'to_frame', inline='always', no_unliteral=True)
def overload_series_to_frame(S, name=None):
    zfzbo__yny = (
        "Series.to_frame(): output column name should be known at compile time. Set 'name' to a constant value."
        )
    if is_overload_none(name):
        if is_literal_type(S.name_typ):
            fywed__utmac = get_literal_value(S.name_typ)
        else:
            raise_bodo_error(zfzbo__yny)
    elif is_literal_type(name):
        fywed__utmac = get_literal_value(name)
    else:
        raise_bodo_error(zfzbo__yny)
    fywed__utmac = 0 if fywed__utmac is None else fywed__utmac

    def impl(S, name=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        return bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,), index,
            (fywed__utmac,))
    return impl


@overload_method(SeriesType, 'keys', inline='always', no_unliteral=True)
def overload_series_keys(S):

    def impl(S):
        return bodo.hiframes.pd_series_ext.get_series_index(S)
    return impl
