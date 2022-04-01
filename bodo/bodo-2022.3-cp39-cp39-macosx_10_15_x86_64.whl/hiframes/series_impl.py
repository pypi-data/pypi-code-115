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
            ijnzw__vjmw = bodo.hiframes.pd_series_ext.get_series_data(s)
            gphb__kcxdu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                ijnzw__vjmw)
            return gphb__kcxdu
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
            yrkbq__sskm = list()
            for afu__aekf in range(len(S)):
                yrkbq__sskm.append(S.iat[afu__aekf])
            return yrkbq__sskm
        return impl_float

    def impl(S):
        yrkbq__sskm = list()
        for afu__aekf in range(len(S)):
            if bodo.libs.array_kernels.isna(S.values, afu__aekf):
                raise ValueError(
                    'Series.to_list(): Not supported for NA values with non-float dtypes'
                    )
            yrkbq__sskm.append(S.iat[afu__aekf])
        return yrkbq__sskm
    return impl


@overload_method(SeriesType, 'to_numpy', inline='always', no_unliteral=True)
def overload_series_to_numpy(S, dtype=None, copy=False, na_value=None):
    xqt__pxxev = dict(dtype=dtype, copy=copy, na_value=na_value)
    okxj__pvszq = dict(dtype=None, copy=False, na_value=None)
    check_unsupported_args('Series.to_numpy', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')

    def impl(S, dtype=None, copy=False, na_value=None):
        return S.values
    return impl


@overload_method(SeriesType, 'reset_index', inline='always', no_unliteral=True)
def overload_series_reset_index(S, level=None, drop=False, name=None,
    inplace=False):
    xqt__pxxev = dict(name=name, inplace=inplace)
    okxj__pvszq = dict(name=None, inplace=False)
    check_unsupported_args('Series.reset_index', xqt__pxxev, okxj__pvszq,
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
    zncz__cotp = get_name_literal(S.index.name_typ, True, series_name)
    columns = [zncz__cotp, series_name]
    ttone__wjf = (
        'def _impl(S, level=None, drop=False, name=None, inplace=False):\n')
    ttone__wjf += '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    ttone__wjf += """    index = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(S))
"""
    ttone__wjf += """    df_index = bodo.hiframes.pd_index_ext.init_range_index(0, len(S), 1, None)
"""
    ttone__wjf += '    col_var = {}\n'.format(gen_const_tup(columns))
    ttone__wjf += """    return bodo.hiframes.pd_dataframe_ext.init_dataframe((index, arr), df_index, col_var)
"""
    lum__vkqd = {}
    exec(ttone__wjf, {'bodo': bodo}, lum__vkqd)
    nhb__jakji = lum__vkqd['_impl']
    return nhb__jakji


@overload_method(SeriesType, 'isna', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'isnull', inline='always', no_unliteral=True)
def overload_series_isna(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        xkui__woahs = bodo.libs.array_ops.array_op_isna(arr)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs, index, name
            )
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
        xkui__woahs = bodo.utils.utils.alloc_type(n, arr, (-1,))
        for afu__aekf in numba.parfors.parfor.internal_prange(n):
            if pd.isna(arr[afu__aekf]):
                bodo.libs.array_kernels.setna(xkui__woahs, afu__aekf)
            else:
                xkui__woahs[afu__aekf] = np.round(arr[afu__aekf], decimals)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs, index, name
            )
    return impl


@overload_method(SeriesType, 'sum', inline='always', no_unliteral=True)
def overload_series_sum(S, axis=None, skipna=True, level=None, numeric_only
    =None, min_count=0):
    xqt__pxxev = dict(level=level, numeric_only=numeric_only)
    okxj__pvszq = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.sum', xqt__pxxev, okxj__pvszq,
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
    xqt__pxxev = dict(level=level, numeric_only=numeric_only)
    okxj__pvszq = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.product', xqt__pxxev, okxj__pvszq,
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
    xqt__pxxev = dict(axis=axis, bool_only=bool_only, skipna=skipna, level=
        level)
    okxj__pvszq = dict(axis=0, bool_only=None, skipna=True, level=None)
    check_unsupported_args('Series.any', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.any()'
        )

    def impl(S, axis=0, bool_only=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        fklak__kocs = 0
        for afu__aekf in numba.parfors.parfor.internal_prange(len(A)):
            gfy__hdlz = 0
            if not bodo.libs.array_kernels.isna(A, afu__aekf):
                gfy__hdlz = int(A[afu__aekf])
            fklak__kocs += gfy__hdlz
        return fklak__kocs != 0
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
        ulkty__dkdi = bodo.hiframes.pd_series_ext.get_series_data(S)
        gidhr__vrkyy = bodo.hiframes.pd_series_ext.get_series_data(other)
        numba.parfors.parfor.init_prange()
        fklak__kocs = 0
        for afu__aekf in numba.parfors.parfor.internal_prange(len(ulkty__dkdi)
            ):
            gfy__hdlz = 0
            nua__lvr = bodo.libs.array_kernels.isna(ulkty__dkdi, afu__aekf)
            bqhtt__upr = bodo.libs.array_kernels.isna(gidhr__vrkyy, afu__aekf)
            if nua__lvr and not bqhtt__upr or not nua__lvr and bqhtt__upr:
                gfy__hdlz = 1
            elif not nua__lvr:
                if ulkty__dkdi[afu__aekf] != gidhr__vrkyy[afu__aekf]:
                    gfy__hdlz = 1
            fklak__kocs += gfy__hdlz
        return fklak__kocs == 0
    return impl


@overload_method(SeriesType, 'all', inline='always', no_unliteral=True)
def overload_series_all(S, axis=0, bool_only=None, skipna=True, level=None):
    xqt__pxxev = dict(axis=axis, bool_only=bool_only, skipna=skipna, level=
        level)
    okxj__pvszq = dict(axis=0, bool_only=None, skipna=True, level=None)
    check_unsupported_args('Series.all', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.all()'
        )

    def impl(S, axis=0, bool_only=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        fklak__kocs = 0
        for afu__aekf in numba.parfors.parfor.internal_prange(len(A)):
            gfy__hdlz = 0
            if not bodo.libs.array_kernels.isna(A, afu__aekf):
                gfy__hdlz = int(not A[afu__aekf])
            fklak__kocs += gfy__hdlz
        return fklak__kocs == 0
    return impl


@overload_method(SeriesType, 'mad', inline='always', no_unliteral=True)
def overload_series_mad(S, axis=None, skipna=True, level=None):
    xqt__pxxev = dict(level=level)
    okxj__pvszq = dict(level=None)
    check_unsupported_args('Series.mad', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')
    if not is_overload_bool(skipna):
        raise BodoError("Series.mad(): 'skipna' argument must be a boolean")
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.mad(): axis argument not supported')
    oklme__nbfwn = types.float64
    kjbx__dmk = types.float64
    if S.dtype == types.float32:
        oklme__nbfwn = types.float32
        kjbx__dmk = types.float32
    fwjxg__xsg = oklme__nbfwn(0)
    xqklu__bmgo = kjbx__dmk(0)
    cvt__vlro = kjbx__dmk(1)
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.mad()'
        )

    def impl(S, axis=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        mnnj__cvl = fwjxg__xsg
        fklak__kocs = xqklu__bmgo
        for afu__aekf in numba.parfors.parfor.internal_prange(len(A)):
            gfy__hdlz = fwjxg__xsg
            jdtow__grsoo = xqklu__bmgo
            if not bodo.libs.array_kernels.isna(A, afu__aekf) or not skipna:
                gfy__hdlz = A[afu__aekf]
                jdtow__grsoo = cvt__vlro
            mnnj__cvl += gfy__hdlz
            fklak__kocs += jdtow__grsoo
        owm__oidcn = bodo.hiframes.series_kernels._mean_handle_nan(mnnj__cvl,
            fklak__kocs)
        vuh__fhko = fwjxg__xsg
        for afu__aekf in numba.parfors.parfor.internal_prange(len(A)):
            gfy__hdlz = fwjxg__xsg
            if not bodo.libs.array_kernels.isna(A, afu__aekf) or not skipna:
                gfy__hdlz = abs(A[afu__aekf] - owm__oidcn)
            vuh__fhko += gfy__hdlz
        pstlk__hsngj = bodo.hiframes.series_kernels._mean_handle_nan(vuh__fhko,
            fklak__kocs)
        return pstlk__hsngj
    return impl


@overload_method(SeriesType, 'mean', inline='always', no_unliteral=True)
def overload_series_mean(S, axis=None, skipna=None, level=None,
    numeric_only=None):
    if not isinstance(S.dtype, types.Number) and S.dtype not in [bodo.
        datetime64ns, types.bool_]:
        raise BodoError(f"Series.mean(): Series with type '{S}' not supported")
    xqt__pxxev = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    okxj__pvszq = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.mean', xqt__pxxev, okxj__pvszq,
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
    xqt__pxxev = dict(level=level, numeric_only=numeric_only)
    okxj__pvszq = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.sem', xqt__pxxev, okxj__pvszq,
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
        wzrfx__yrq = 0
        ofj__xna = 0
        fklak__kocs = 0
        for afu__aekf in numba.parfors.parfor.internal_prange(len(A)):
            gfy__hdlz = 0
            jdtow__grsoo = 0
            if not bodo.libs.array_kernels.isna(A, afu__aekf) or not skipna:
                gfy__hdlz = A[afu__aekf]
                jdtow__grsoo = 1
            wzrfx__yrq += gfy__hdlz
            ofj__xna += gfy__hdlz * gfy__hdlz
            fklak__kocs += jdtow__grsoo
        ssks__yzzsb = bodo.hiframes.series_kernels._compute_var_nan_count_ddof(
            wzrfx__yrq, ofj__xna, fklak__kocs, ddof)
        nqpz__aag = bodo.hiframes.series_kernels._sem_handle_nan(ssks__yzzsb,
            fklak__kocs)
        return nqpz__aag
    return impl


@overload_method(SeriesType, 'kurt', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'kurtosis', inline='always', no_unliteral=True)
def overload_series_kurt(S, axis=None, skipna=True, level=None,
    numeric_only=None):
    xqt__pxxev = dict(level=level, numeric_only=numeric_only)
    okxj__pvszq = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.kurtosis', xqt__pxxev, okxj__pvszq,
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
        wzrfx__yrq = 0.0
        ofj__xna = 0.0
        wfx__prv = 0.0
        zsqt__lgd = 0.0
        fklak__kocs = 0
        for afu__aekf in numba.parfors.parfor.internal_prange(len(A)):
            gfy__hdlz = 0.0
            jdtow__grsoo = 0
            if not bodo.libs.array_kernels.isna(A, afu__aekf) or not skipna:
                gfy__hdlz = np.float64(A[afu__aekf])
                jdtow__grsoo = 1
            wzrfx__yrq += gfy__hdlz
            ofj__xna += gfy__hdlz ** 2
            wfx__prv += gfy__hdlz ** 3
            zsqt__lgd += gfy__hdlz ** 4
            fklak__kocs += jdtow__grsoo
        ssks__yzzsb = bodo.hiframes.series_kernels.compute_kurt(wzrfx__yrq,
            ofj__xna, wfx__prv, zsqt__lgd, fklak__kocs)
        return ssks__yzzsb
    return impl


@overload_method(SeriesType, 'skew', inline='always', no_unliteral=True)
def overload_series_skew(S, axis=None, skipna=True, level=None,
    numeric_only=None):
    xqt__pxxev = dict(level=level, numeric_only=numeric_only)
    okxj__pvszq = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.skew', xqt__pxxev, okxj__pvszq,
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
        wzrfx__yrq = 0.0
        ofj__xna = 0.0
        wfx__prv = 0.0
        fklak__kocs = 0
        for afu__aekf in numba.parfors.parfor.internal_prange(len(A)):
            gfy__hdlz = 0.0
            jdtow__grsoo = 0
            if not bodo.libs.array_kernels.isna(A, afu__aekf) or not skipna:
                gfy__hdlz = np.float64(A[afu__aekf])
                jdtow__grsoo = 1
            wzrfx__yrq += gfy__hdlz
            ofj__xna += gfy__hdlz ** 2
            wfx__prv += gfy__hdlz ** 3
            fklak__kocs += jdtow__grsoo
        ssks__yzzsb = bodo.hiframes.series_kernels.compute_skew(wzrfx__yrq,
            ofj__xna, wfx__prv, fklak__kocs)
        return ssks__yzzsb
    return impl


@overload_method(SeriesType, 'var', inline='always', no_unliteral=True)
def overload_series_var(S, axis=None, skipna=True, level=None, ddof=1,
    numeric_only=None):
    xqt__pxxev = dict(level=level, numeric_only=numeric_only)
    okxj__pvszq = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.var', xqt__pxxev, okxj__pvszq,
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
    xqt__pxxev = dict(level=level, numeric_only=numeric_only)
    okxj__pvszq = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.std', xqt__pxxev, okxj__pvszq,
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
        ulkty__dkdi = bodo.hiframes.pd_series_ext.get_series_data(S)
        gidhr__vrkyy = bodo.hiframes.pd_series_ext.get_series_data(other)
        numba.parfors.parfor.init_prange()
        bzpl__azuq = 0
        for afu__aekf in numba.parfors.parfor.internal_prange(len(ulkty__dkdi)
            ):
            lqjo__jat = ulkty__dkdi[afu__aekf]
            nuub__ulhpf = gidhr__vrkyy[afu__aekf]
            bzpl__azuq += lqjo__jat * nuub__ulhpf
        return bzpl__azuq
    return impl


@overload_method(SeriesType, 'cumsum', inline='always', no_unliteral=True)
def overload_series_cumsum(S, axis=None, skipna=True):
    xqt__pxxev = dict(skipna=skipna)
    okxj__pvszq = dict(skipna=True)
    check_unsupported_args('Series.cumsum', xqt__pxxev, okxj__pvszq,
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
    xqt__pxxev = dict(skipna=skipna)
    okxj__pvszq = dict(skipna=True)
    check_unsupported_args('Series.cumprod', xqt__pxxev, okxj__pvszq,
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
    xqt__pxxev = dict(skipna=skipna)
    okxj__pvszq = dict(skipna=True)
    check_unsupported_args('Series.cummin', xqt__pxxev, okxj__pvszq,
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
    xqt__pxxev = dict(skipna=skipna)
    okxj__pvszq = dict(skipna=True)
    check_unsupported_args('Series.cummax', xqt__pxxev, okxj__pvszq,
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
    xqt__pxxev = dict(copy=copy, inplace=inplace, level=level, errors=errors)
    okxj__pvszq = dict(copy=True, inplace=False, level=None, errors='ignore')
    check_unsupported_args('Series.rename', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')

    def impl(S, index=None, axis=None, copy=True, inplace=False, level=None,
        errors='ignore'):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        yxzs__upgfp = bodo.hiframes.pd_series_ext.get_series_index(S)
        return bodo.hiframes.pd_series_ext.init_series(A, yxzs__upgfp, index)
    return impl


@overload_method(SeriesType, 'rename_axis', inline='always', no_unliteral=True)
def overload_series_rename_axis(S, mapper=None, index=None, columns=None,
    axis=None, copy=True, inplace=False):
    xqt__pxxev = dict(index=index, columns=columns, axis=axis, copy=copy,
        inplace=inplace)
    okxj__pvszq = dict(index=None, columns=None, axis=None, copy=True,
        inplace=False)
    check_unsupported_args('Series.rename_axis', xqt__pxxev, okxj__pvszq,
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
    xqt__pxxev = dict(level=level)
    okxj__pvszq = dict(level=None)
    check_unsupported_args('Series.count', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')

    def impl(S, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_count(A)
    return impl


@overload_method(SeriesType, 'corr', inline='always', no_unliteral=True)
def overload_series_corr(S, other, method='pearson', min_periods=None):
    xqt__pxxev = dict(method=method, min_periods=min_periods)
    okxj__pvszq = dict(method='pearson', min_periods=None)
    check_unsupported_args('Series.corr', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.corr()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(other,
        'Series.corr()')

    def impl(S, other, method='pearson', min_periods=None):
        n = S.count()
        bkdtv__kjxhk = S.sum()
        izca__rehn = other.sum()
        a = n * (S * other).sum() - bkdtv__kjxhk * izca__rehn
        zjjh__zkyn = n * (S ** 2).sum() - bkdtv__kjxhk ** 2
        bmfv__nele = n * (other ** 2).sum() - izca__rehn ** 2
        return a / np.sqrt(zjjh__zkyn * bmfv__nele)
    return impl


@overload_method(SeriesType, 'cov', inline='always', no_unliteral=True)
def overload_series_cov(S, other, min_periods=None, ddof=1):
    xqt__pxxev = dict(min_periods=min_periods)
    okxj__pvszq = dict(min_periods=None)
    check_unsupported_args('Series.cov', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S, 'Series.cov()'
        )
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(other,
        'Series.cov()')

    def impl(S, other, min_periods=None, ddof=1):
        bkdtv__kjxhk = S.mean()
        izca__rehn = other.mean()
        dcqyz__hyi = ((S - bkdtv__kjxhk) * (other - izca__rehn)).sum()
        N = np.float64(S.count() - ddof)
        nonzero_len = S.count() * other.count()
        return _series_cov_helper(dcqyz__hyi, N, nonzero_len)
    return impl


def _series_cov_helper(sum_val, N, nonzero_len):
    return


@overload(_series_cov_helper, no_unliteral=True)
def _overload_series_cov_helper(sum_val, N, nonzero_len):

    def impl(sum_val, N, nonzero_len):
        if not nonzero_len:
            return np.nan
        if N <= 0.0:
            wuki__iqpk = np.sign(sum_val)
            return np.inf * wuki__iqpk
        return sum_val / N
    return impl


@overload_method(SeriesType, 'min', inline='always', no_unliteral=True)
def overload_series_min(S, axis=None, skipna=None, level=None, numeric_only
    =None):
    xqt__pxxev = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    okxj__pvszq = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.min', xqt__pxxev, okxj__pvszq,
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
    xqt__pxxev = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    okxj__pvszq = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.max', xqt__pxxev, okxj__pvszq,
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
    xqt__pxxev = dict(axis=axis, skipna=skipna)
    okxj__pvszq = dict(axis=0, skipna=True)
    check_unsupported_args('Series.idxmin', xqt__pxxev, okxj__pvszq,
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
    xqt__pxxev = dict(axis=axis, skipna=skipna)
    okxj__pvszq = dict(axis=0, skipna=True)
    check_unsupported_args('Series.idxmax', xqt__pxxev, okxj__pvszq,
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
    xqt__pxxev = dict(level=level, numeric_only=numeric_only)
    okxj__pvszq = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.median', xqt__pxxev, okxj__pvszq,
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
        oblpj__sfjy = arr[:n]
        vlqy__avzr = index[:n]
        return bodo.hiframes.pd_series_ext.init_series(oblpj__sfjy,
            vlqy__avzr, name)
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
        jik__dbqfq = tail_slice(len(S), n)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        oblpj__sfjy = arr[jik__dbqfq:]
        vlqy__avzr = index[jik__dbqfq:]
        return bodo.hiframes.pd_series_ext.init_series(oblpj__sfjy,
            vlqy__avzr, name)
    return impl


@overload_method(SeriesType, 'first', inline='always', no_unliteral=True)
def overload_series_first(S, offset):
    mvof__izxru = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if types.unliteral(offset) not in mvof__izxru:
        raise BodoError(
            "Series.first(): 'offset' must be a string or a DateOffset")
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.first()')

    def impl(S, offset):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        if len(index):
            ehhug__rqycn = index[0]
            jnt__gxk = (bodo.libs.array_kernels.
                get_valid_entries_from_date_offset(index, offset,
                ehhug__rqycn, False))
        else:
            jnt__gxk = 0
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        oblpj__sfjy = arr[:jnt__gxk]
        vlqy__avzr = index[:jnt__gxk]
        return bodo.hiframes.pd_series_ext.init_series(oblpj__sfjy,
            vlqy__avzr, name)
    return impl


@overload_method(SeriesType, 'last', inline='always', no_unliteral=True)
def overload_series_last(S, offset):
    mvof__izxru = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if types.unliteral(offset) not in mvof__izxru:
        raise BodoError(
            "Series.last(): 'offset' must be a string or a DateOffset")
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.last()')

    def impl(S, offset):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        if len(index):
            hun__xcosv = index[-1]
            jnt__gxk = (bodo.libs.array_kernels.
                get_valid_entries_from_date_offset(index, offset,
                hun__xcosv, True))
        else:
            jnt__gxk = 0
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        oblpj__sfjy = arr[len(arr) - jnt__gxk:]
        vlqy__avzr = index[len(arr) - jnt__gxk:]
        return bodo.hiframes.pd_series_ext.init_series(oblpj__sfjy,
            vlqy__avzr, name)
    return impl


@overload_method(SeriesType, 'first_valid_index', inline='always',
    no_unliteral=True)
def overload_series_first_valid_index(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        pds__clxht = bodo.utils.conversion.index_to_array(index)
        qyhx__fjk, qhxbb__qkkx = (bodo.libs.array_kernels.
            first_last_valid_index(arr, pds__clxht))
        return qhxbb__qkkx if qyhx__fjk else None
    return impl


@overload_method(SeriesType, 'last_valid_index', inline='always',
    no_unliteral=True)
def overload_series_last_valid_index(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        pds__clxht = bodo.utils.conversion.index_to_array(index)
        qyhx__fjk, qhxbb__qkkx = (bodo.libs.array_kernels.
            first_last_valid_index(arr, pds__clxht, False))
        return qhxbb__qkkx if qyhx__fjk else None
    return impl


@overload_method(SeriesType, 'nlargest', inline='always', no_unliteral=True)
def overload_series_nlargest(S, n=5, keep='first'):
    xqt__pxxev = dict(keep=keep)
    okxj__pvszq = dict(keep='first')
    check_unsupported_args('Series.nlargest', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')
    if not is_overload_int(n):
        raise BodoError('Series.nlargest(): n argument must be an integer')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.nlargest()')

    def impl(S, n=5, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        pds__clxht = bodo.utils.conversion.coerce_to_ndarray(index)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        xkui__woahs, dpovo__jams = bodo.libs.array_kernels.nlargest(arr,
            pds__clxht, n, True, bodo.hiframes.series_kernels.gt_f)
        qiyo__jxpbn = bodo.utils.conversion.convert_to_index(dpovo__jams)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
            qiyo__jxpbn, name)
    return impl


@overload_method(SeriesType, 'nsmallest', inline='always', no_unliteral=True)
def overload_series_nsmallest(S, n=5, keep='first'):
    xqt__pxxev = dict(keep=keep)
    okxj__pvszq = dict(keep='first')
    check_unsupported_args('Series.nsmallest', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')
    if not is_overload_int(n):
        raise BodoError('Series.nsmallest(): n argument must be an integer')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.nsmallest()')

    def impl(S, n=5, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        pds__clxht = bodo.utils.conversion.coerce_to_ndarray(index)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        xkui__woahs, dpovo__jams = bodo.libs.array_kernels.nlargest(arr,
            pds__clxht, n, False, bodo.hiframes.series_kernels.lt_f)
        qiyo__jxpbn = bodo.utils.conversion.convert_to_index(dpovo__jams)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
            qiyo__jxpbn, name)
    return impl


@overload_method(SeriesType, 'notnull', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'notna', inline='always', no_unliteral=True)
def overload_series_notna(S):
    return lambda S: S.isna() == False


@overload_method(SeriesType, 'astype', inline='always', no_unliteral=True)
def overload_series_astype(S, dtype, copy=True, errors='raise',
    _bodo_nan_to_str=True):
    xqt__pxxev = dict(errors=errors)
    okxj__pvszq = dict(errors='raise')
    check_unsupported_args('Series.astype', xqt__pxxev, okxj__pvszq,
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
        xkui__woahs = bodo.utils.conversion.fix_arr_dtype(arr, dtype, copy,
            nan_to_str=_bodo_nan_to_str, from_series=True)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs, index, name
            )
    return impl


@overload_method(SeriesType, 'take', inline='always', no_unliteral=True)
def overload_series_take(S, indices, axis=0, is_copy=True):
    xqt__pxxev = dict(axis=axis, is_copy=is_copy)
    okxj__pvszq = dict(axis=0, is_copy=True)
    check_unsupported_args('Series.take', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')
    if not (is_iterable_type(indices) and isinstance(indices.dtype, types.
        Integer)):
        raise BodoError(
            f"Series.take() 'indices' must be an array-like and contain integers. Found type {indices}."
            )

    def impl(S, indices, axis=0, is_copy=True):
        onhvy__cbk = bodo.utils.conversion.coerce_to_ndarray(indices)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(arr[onhvy__cbk],
            index[onhvy__cbk], name)
    return impl


@overload_method(SeriesType, 'argsort', inline='always', no_unliteral=True)
def overload_series_argsort(S, axis=0, kind='quicksort', order=None):
    xqt__pxxev = dict(axis=axis, kind=kind, order=order)
    okxj__pvszq = dict(axis=0, kind='quicksort', order=None)
    check_unsupported_args('Series.argsort', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')

    def impl(S, axis=0, kind='quicksort', order=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        n = len(arr)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        itgk__czqu = S.notna().values
        if not itgk__czqu.all():
            xkui__woahs = np.full(n, -1, np.int64)
            xkui__woahs[itgk__czqu] = argsort(arr[itgk__czqu])
        else:
            xkui__woahs = argsort(arr)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs, index, name
            )
    return impl


@overload_method(SeriesType, 'sort_index', inline='always', no_unliteral=True)
def overload_series_sort_index(S, axis=0, level=None, ascending=True,
    inplace=False, kind='quicksort', na_position='last', sort_remaining=
    True, ignore_index=False, key=None):
    xqt__pxxev = dict(axis=axis, level=level, inplace=inplace, kind=kind,
        sort_remaining=sort_remaining, ignore_index=ignore_index, key=key)
    okxj__pvszq = dict(axis=0, level=None, inplace=False, kind='quicksort',
        sort_remaining=True, ignore_index=False, key=None)
    check_unsupported_args('Series.sort_index', xqt__pxxev, okxj__pvszq,
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
        par__oahdt = bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,),
            index, ('$_bodo_col3_',))
        rdhkt__tetfc = par__oahdt.sort_index(ascending=ascending, inplace=
            inplace, na_position=na_position)
        xkui__woahs = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(
            rdhkt__tetfc, 0)
        qiyo__jxpbn = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(
            rdhkt__tetfc)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
            qiyo__jxpbn, name)
    return impl


@overload_method(SeriesType, 'sort_values', inline='always', no_unliteral=True)
def overload_series_sort_values(S, axis=0, ascending=True, inplace=False,
    kind='quicksort', na_position='last', ignore_index=False, key=None):
    xqt__pxxev = dict(axis=axis, inplace=inplace, kind=kind, ignore_index=
        ignore_index, key=key)
    okxj__pvszq = dict(axis=0, inplace=False, kind='quicksort',
        ignore_index=False, key=None)
    check_unsupported_args('Series.sort_values', xqt__pxxev, okxj__pvszq,
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
        par__oahdt = bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,),
            index, ('$_bodo_col_',))
        rdhkt__tetfc = par__oahdt.sort_values(['$_bodo_col_'], ascending=
            ascending, inplace=inplace, na_position=na_position)
        xkui__woahs = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(
            rdhkt__tetfc, 0)
        qiyo__jxpbn = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(
            rdhkt__tetfc)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
            qiyo__jxpbn, name)
    return impl


def get_bin_inds(bins, arr):
    return arr


@overload(get_bin_inds, inline='always', no_unliteral=True)
def overload_get_bin_inds(bins, arr, is_nullable=True, include_lowest=True):
    assert is_overload_constant_bool(is_nullable)
    dfvwu__auxuf = is_overload_true(is_nullable)
    ttone__wjf = (
        'def impl(bins, arr, is_nullable=True, include_lowest=True):\n')
    ttone__wjf += '  numba.parfors.parfor.init_prange()\n'
    ttone__wjf += '  n = len(arr)\n'
    if dfvwu__auxuf:
        ttone__wjf += (
            '  out_arr = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n')
    else:
        ttone__wjf += '  out_arr = np.empty(n, np.int64)\n'
    ttone__wjf += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    ttone__wjf += '    if bodo.libs.array_kernels.isna(arr, i):\n'
    if dfvwu__auxuf:
        ttone__wjf += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    else:
        ttone__wjf += '      out_arr[i] = -1\n'
    ttone__wjf += '      continue\n'
    ttone__wjf += '    val = arr[i]\n'
    ttone__wjf += '    if include_lowest and val == bins[0]:\n'
    ttone__wjf += '      ind = 1\n'
    ttone__wjf += '    else:\n'
    ttone__wjf += '      ind = np.searchsorted(bins, val)\n'
    ttone__wjf += '    if ind == 0 or ind == len(bins):\n'
    if dfvwu__auxuf:
        ttone__wjf += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    else:
        ttone__wjf += '      out_arr[i] = -1\n'
    ttone__wjf += '    else:\n'
    ttone__wjf += '      out_arr[i] = ind - 1\n'
    ttone__wjf += '  return out_arr\n'
    lum__vkqd = {}
    exec(ttone__wjf, {'bodo': bodo, 'np': np, 'numba': numba}, lum__vkqd)
    impl = lum__vkqd['impl']
    return impl


@register_jitable
def _round_frac(x, precision: int):
    if not np.isfinite(x) or x == 0:
        return x
    else:
        cszcr__wupl, ymmp__xxol = np.divmod(x, 1)
        if cszcr__wupl == 0:
            vvqc__poa = -int(np.floor(np.log10(abs(ymmp__xxol)))
                ) - 1 + precision
        else:
            vvqc__poa = precision
        return np.around(x, vvqc__poa)


@register_jitable
def _infer_precision(base_precision: int, bins) ->int:
    for precision in range(base_precision, 20):
        bme__zbmr = np.array([_round_frac(b, precision) for b in bins])
        if len(np.unique(bme__zbmr)) == len(bins):
            return precision
    return base_precision


def get_bin_labels(bins):
    pass


@overload(get_bin_labels, no_unliteral=True)
def overload_get_bin_labels(bins, right=True, include_lowest=True):
    dtype = np.float64 if isinstance(bins.dtype, types.Integer) else bins.dtype
    if dtype == bodo.datetime64ns:
        ahav__nkv = bodo.timedelta64ns(1)

        def impl_dt64(bins, right=True, include_lowest=True):
            wbf__cztnq = bins.copy()
            if right and include_lowest:
                wbf__cztnq[0] = wbf__cztnq[0] - ahav__nkv
            jwiev__jbsh = bodo.libs.interval_arr_ext.init_interval_array(
                wbf__cztnq[:-1], wbf__cztnq[1:])
            return bodo.hiframes.pd_index_ext.init_interval_index(jwiev__jbsh,
                None)
        return impl_dt64

    def impl(bins, right=True, include_lowest=True):
        base_precision = 3
        precision = _infer_precision(base_precision, bins)
        wbf__cztnq = np.array([_round_frac(b, precision) for b in bins],
            dtype=dtype)
        if right and include_lowest:
            wbf__cztnq[0] = wbf__cztnq[0] - 10.0 ** -precision
        jwiev__jbsh = bodo.libs.interval_arr_ext.init_interval_array(wbf__cztnq
            [:-1], wbf__cztnq[1:])
        return bodo.hiframes.pd_index_ext.init_interval_index(jwiev__jbsh, None
            )
    return impl


def get_output_bin_counts(count_series, nbins):
    pass


@overload(get_output_bin_counts, no_unliteral=True)
def overload_get_output_bin_counts(count_series, nbins):

    def impl(count_series, nbins):
        lfnb__soo = bodo.hiframes.pd_series_ext.get_series_data(count_series)
        fde__zirld = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(count_series))
        xkui__woahs = np.zeros(nbins, np.int64)
        for afu__aekf in range(len(lfnb__soo)):
            xkui__woahs[fde__zirld[afu__aekf]] = lfnb__soo[afu__aekf]
        return xkui__woahs
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
            gti__lim = (max_val - min_val) * 0.001
            if right:
                bins[0] -= gti__lim
            else:
                bins[-1] += gti__lim
        return bins
    return impl


@overload_method(SeriesType, 'value_counts', inline='always', no_unliteral=True
    )
def overload_series_value_counts(S, normalize=False, sort=True, ascending=
    False, bins=None, dropna=True, _index_name=None):
    xqt__pxxev = dict(dropna=dropna)
    okxj__pvszq = dict(dropna=True)
    check_unsupported_args('Series.value_counts', xqt__pxxev, okxj__pvszq,
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
    ddhw__tkqlv = not is_overload_none(bins)
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.value_counts()')
    ttone__wjf = 'def impl(\n'
    ttone__wjf += '    S,\n'
    ttone__wjf += '    normalize=False,\n'
    ttone__wjf += '    sort=True,\n'
    ttone__wjf += '    ascending=False,\n'
    ttone__wjf += '    bins=None,\n'
    ttone__wjf += '    dropna=True,\n'
    ttone__wjf += (
        '    _index_name=None,  # bodo argument. See groupby.value_counts\n')
    ttone__wjf += '):\n'
    ttone__wjf += '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    ttone__wjf += (
        '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
    ttone__wjf += '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    if ddhw__tkqlv:
        ttone__wjf += '    right = True\n'
        ttone__wjf += _gen_bins_handling(bins, S.dtype)
        ttone__wjf += '    arr = get_bin_inds(bins, arr)\n'
    ttone__wjf += (
        '    in_df = bodo.hiframes.pd_dataframe_ext.init_dataframe(\n')
    ttone__wjf += "        (arr,), index, ('$_bodo_col2_',)\n"
    ttone__wjf += '    )\n'
    ttone__wjf += "    count_series = in_df.groupby('$_bodo_col2_').size()\n"
    if ddhw__tkqlv:
        ttone__wjf += """    count_series = bodo.gatherv(count_series, allgather=True, warn_if_rep=False)
"""
        ttone__wjf += (
            '    count_arr = get_output_bin_counts(count_series, len(bins) - 1)\n'
            )
        ttone__wjf += '    index = get_bin_labels(bins)\n'
    else:
        ttone__wjf += (
            '    count_arr = bodo.hiframes.pd_series_ext.get_series_data(count_series)\n'
            )
        ttone__wjf += '    ind_arr = bodo.utils.conversion.coerce_to_array(\n'
        ttone__wjf += (
            '        bodo.hiframes.pd_series_ext.get_series_index(count_series)\n'
            )
        ttone__wjf += '    )\n'
        ttone__wjf += """    index = bodo.utils.conversion.index_from_array(ind_arr, name=_index_name)
"""
    ttone__wjf += (
        '    res = bodo.hiframes.pd_series_ext.init_series(count_arr, index, name)\n'
        )
    if is_overload_true(sort):
        ttone__wjf += '    res = res.sort_values(ascending=ascending)\n'
    if is_overload_true(normalize):
        ygytj__cfci = 'len(S)' if ddhw__tkqlv else 'count_arr.sum()'
        ttone__wjf += f'    res = res / float({ygytj__cfci})\n'
    ttone__wjf += '    return res\n'
    lum__vkqd = {}
    exec(ttone__wjf, {'bodo': bodo, 'pd': pd, 'np': np, 'get_bin_inds':
        get_bin_inds, 'get_bin_labels': get_bin_labels,
        'get_output_bin_counts': get_output_bin_counts, 'compute_bins':
        compute_bins}, lum__vkqd)
    impl = lum__vkqd['impl']
    return impl


def _gen_bins_handling(bins, dtype):
    ttone__wjf = ''
    if isinstance(bins, types.Integer):
        ttone__wjf += '    min_val = bodo.libs.array_ops.array_op_min(arr)\n'
        ttone__wjf += '    max_val = bodo.libs.array_ops.array_op_max(arr)\n'
        if dtype == bodo.datetime64ns:
            ttone__wjf += '    min_val = min_val.value\n'
            ttone__wjf += '    max_val = max_val.value\n'
        ttone__wjf += (
            '    bins = compute_bins(bins, min_val, max_val, right)\n')
        if dtype == bodo.datetime64ns:
            ttone__wjf += (
                "    bins = bins.astype(np.int64).view(np.dtype('datetime64[ns]'))\n"
                )
    else:
        ttone__wjf += (
            '    bins = bodo.utils.conversion.coerce_to_ndarray(bins)\n')
    return ttone__wjf


@overload(pd.cut, inline='always', no_unliteral=True)
def overload_cut(x, bins, right=True, labels=None, retbins=False, precision
    =3, include_lowest=False, duplicates='raise', ordered=True):
    xqt__pxxev = dict(right=right, labels=labels, retbins=retbins,
        precision=precision, duplicates=duplicates, ordered=ordered)
    okxj__pvszq = dict(right=True, labels=None, retbins=False, precision=3,
        duplicates='raise', ordered=True)
    check_unsupported_args('pandas.cut', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='General')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(x, 'pandas.cut()'
        )
    ttone__wjf = 'def impl(\n'
    ttone__wjf += '    x,\n'
    ttone__wjf += '    bins,\n'
    ttone__wjf += '    right=True,\n'
    ttone__wjf += '    labels=None,\n'
    ttone__wjf += '    retbins=False,\n'
    ttone__wjf += '    precision=3,\n'
    ttone__wjf += '    include_lowest=False,\n'
    ttone__wjf += "    duplicates='raise',\n"
    ttone__wjf += '    ordered=True\n'
    ttone__wjf += '):\n'
    if isinstance(x, SeriesType):
        ttone__wjf += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(x)\n')
        ttone__wjf += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(x)\n')
        ttone__wjf += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(x)\n')
    else:
        ttone__wjf += '    arr = bodo.utils.conversion.coerce_to_array(x)\n'
    ttone__wjf += _gen_bins_handling(bins, x.dtype)
    ttone__wjf += '    arr = get_bin_inds(bins, arr, False, include_lowest)\n'
    ttone__wjf += (
        '    label_index = get_bin_labels(bins, right, include_lowest)\n')
    ttone__wjf += """    cat_dtype = bodo.hiframes.pd_categorical_ext.init_cat_dtype(label_index, ordered, None, None)
"""
    ttone__wjf += """    out_arr = bodo.hiframes.pd_categorical_ext.init_categorical_array(arr, cat_dtype)
"""
    if isinstance(x, SeriesType):
        ttone__wjf += (
            '    res = bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        ttone__wjf += '    return res\n'
    else:
        ttone__wjf += '    return out_arr\n'
    lum__vkqd = {}
    exec(ttone__wjf, {'bodo': bodo, 'pd': pd, 'np': np, 'get_bin_inds':
        get_bin_inds, 'get_bin_labels': get_bin_labels,
        'get_output_bin_counts': get_output_bin_counts, 'compute_bins':
        compute_bins}, lum__vkqd)
    impl = lum__vkqd['impl']
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
    xqt__pxxev = dict(labels=labels, retbins=retbins, precision=precision,
        duplicates=duplicates)
    okxj__pvszq = dict(labels=None, retbins=False, precision=3, duplicates=
        'raise')
    check_unsupported_args('pandas.qcut', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='General')
    if not (is_overload_int(q) or is_iterable_type(q)):
        raise BodoError(
            "pd.qcut(): 'q' should be an integer or a list of quantiles")
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(x,
        'pandas.qcut()')

    def impl(x, q, labels=None, retbins=False, precision=3, duplicates='raise'
        ):
        nuk__prpq = _get_q_list(q)
        arr = bodo.utils.conversion.coerce_to_array(x)
        bins = bodo.libs.array_ops.array_op_quantile(arr, nuk__prpq)
        return pd.cut(x, bins, include_lowest=True)
    return impl


@overload_method(SeriesType, 'groupby', inline='always', no_unliteral=True)
def overload_series_groupby(S, by=None, axis=0, level=None, as_index=True,
    sort=True, group_keys=True, squeeze=False, observed=True, dropna=True):
    xqt__pxxev = dict(axis=axis, sort=sort, group_keys=group_keys, squeeze=
        squeeze, observed=observed, dropna=dropna)
    okxj__pvszq = dict(axis=0, sort=True, group_keys=True, squeeze=False,
        observed=True, dropna=True)
    check_unsupported_args('Series.groupby', xqt__pxxev, okxj__pvszq,
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
            ianfc__ixo = bodo.utils.conversion.coerce_to_array(index)
            par__oahdt = bodo.hiframes.pd_dataframe_ext.init_dataframe((
                ianfc__ixo, arr), index, (' ', ''))
            return par__oahdt.groupby(' ')['']
        return impl_index
    vuixc__lestx = by
    if isinstance(by, SeriesType):
        vuixc__lestx = by.data
    if isinstance(vuixc__lestx, DecimalArrayType):
        raise BodoError(
            'Series.groupby(): by argument with decimal type is not supported yet.'
            )
    if isinstance(by, bodo.hiframes.pd_categorical_ext.CategoricalArrayType):
        raise BodoError(
            'Series.groupby(): by argument with categorical type is not supported yet.'
            )

    def impl(S, by=None, axis=0, level=None, as_index=True, sort=True,
        group_keys=True, squeeze=False, observed=True, dropna=True):
        ianfc__ixo = bodo.utils.conversion.coerce_to_array(by)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        par__oahdt = bodo.hiframes.pd_dataframe_ext.init_dataframe((
            ianfc__ixo, arr), index, (' ', ''))
        return par__oahdt.groupby(' ')['']
    return impl


@overload_method(SeriesType, 'append', inline='always', no_unliteral=True)
def overload_series_append(S, to_append, ignore_index=False,
    verify_integrity=False):
    xqt__pxxev = dict(verify_integrity=verify_integrity)
    okxj__pvszq = dict(verify_integrity=False)
    check_unsupported_args('Series.append', xqt__pxxev, okxj__pvszq,
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
            wtsle__dfs = bodo.utils.conversion.coerce_to_array(values)
            A = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            n = len(A)
            xkui__woahs = np.empty(n, np.bool_)
            bodo.libs.array.array_isin(xkui__woahs, A, wtsle__dfs, False)
            return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                index, name)
        return impl_arr
    if not isinstance(values, (types.Set, types.List)):
        raise BodoError(
            "Series.isin(): 'values' parameter should be a set or a list")

    def impl(S, values):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        xkui__woahs = bodo.libs.array_ops.array_op_isin(A, values)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs, index, name
            )
    return impl


@overload_method(SeriesType, 'quantile', inline='always', no_unliteral=True)
def overload_series_quantile(S, q=0.5, interpolation='linear'):
    xqt__pxxev = dict(interpolation=interpolation)
    okxj__pvszq = dict(interpolation='linear')
    check_unsupported_args('Series.quantile', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.quantile()')
    if is_iterable_type(q) and isinstance(q.dtype, types.Number):

        def impl_list(S, q=0.5, interpolation='linear'):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            xkui__woahs = bodo.libs.array_ops.array_op_quantile(arr, q)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            index = bodo.hiframes.pd_index_ext.init_numeric_index(bodo.
                utils.conversion.coerce_to_array(q), None)
            return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
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
        kql__ezpng = bodo.libs.array_kernels.unique(arr)
        return bodo.allgatherv(kql__ezpng, False)
    return impl


@overload_method(SeriesType, 'describe', inline='always', no_unliteral=True)
def overload_series_describe(S, percentiles=None, include=None, exclude=
    None, datetime_is_numeric=True):
    xqt__pxxev = dict(percentiles=percentiles, include=include, exclude=
        exclude, datetime_is_numeric=datetime_is_numeric)
    okxj__pvszq = dict(percentiles=None, include=None, exclude=None,
        datetime_is_numeric=True)
    check_unsupported_args('Series.describe', xqt__pxxev, okxj__pvszq,
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
        cjtd__tcmij = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
    else:
        cjtd__tcmij = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
    ttone__wjf = '\n'.join(('def impl(', '    S,', '    value=None,',
        '    method=None,', '    axis=None,', '    inplace=False,',
        '    limit=None,', '    downcast=None,', '):',
        '    in_arr = bodo.hiframes.pd_series_ext.get_series_data(S)',
        '    fill_arr = bodo.hiframes.pd_series_ext.get_series_data(value)',
        '    n = len(in_arr)', '    nf = len(fill_arr)',
        "    assert n == nf, 'fillna() requires same length arrays'",
        f'    out_arr = {cjtd__tcmij}(n, -1)',
        '    for j in numba.parfors.parfor.internal_prange(n):',
        '        s = in_arr[j]',
        '        if bodo.libs.array_kernels.isna(in_arr, j) and not bodo.libs.array_kernels.isna('
        , '            fill_arr, j', '        ):',
        '            s = fill_arr[j]', '        out_arr[j] = s',
        '    bodo.libs.str_arr_ext.move_str_binary_arr_payload(in_arr, out_arr)'
        ))
    mui__lrge = dict()
    exec(ttone__wjf, {'bodo': bodo, 'numba': numba}, mui__lrge)
    cvqy__ehka = mui__lrge['impl']
    return cvqy__ehka


def binary_str_fillna_inplace_impl(is_binary=False):
    if is_binary:
        cjtd__tcmij = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
    else:
        cjtd__tcmij = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
    ttone__wjf = 'def impl(S,\n'
    ttone__wjf += '     value=None,\n'
    ttone__wjf += '    method=None,\n'
    ttone__wjf += '    axis=None,\n'
    ttone__wjf += '    inplace=False,\n'
    ttone__wjf += '    limit=None,\n'
    ttone__wjf += '   downcast=None,\n'
    ttone__wjf += '):\n'
    ttone__wjf += (
        '    in_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    ttone__wjf += '    n = len(in_arr)\n'
    ttone__wjf += f'    out_arr = {cjtd__tcmij}(n, -1)\n'
    ttone__wjf += '    for j in numba.parfors.parfor.internal_prange(n):\n'
    ttone__wjf += '        s = in_arr[j]\n'
    ttone__wjf += '        if bodo.libs.array_kernels.isna(in_arr, j):\n'
    ttone__wjf += '            s = value\n'
    ttone__wjf += '        out_arr[j] = s\n'
    ttone__wjf += (
        '    bodo.libs.str_arr_ext.move_str_binary_arr_payload(in_arr, out_arr)\n'
        )
    mui__lrge = dict()
    exec(ttone__wjf, {'bodo': bodo, 'numba': numba}, mui__lrge)
    cvqy__ehka = mui__lrge['impl']
    return cvqy__ehka


def fillna_inplace_series_impl(S, value=None, method=None, axis=None,
    inplace=False, limit=None, downcast=None):
    hrpln__gze = bodo.hiframes.pd_series_ext.get_series_data(S)
    zpgbp__hjz = bodo.hiframes.pd_series_ext.get_series_data(value)
    for afu__aekf in numba.parfors.parfor.internal_prange(len(hrpln__gze)):
        s = hrpln__gze[afu__aekf]
        if bodo.libs.array_kernels.isna(hrpln__gze, afu__aekf
            ) and not bodo.libs.array_kernels.isna(zpgbp__hjz, afu__aekf):
            s = zpgbp__hjz[afu__aekf]
        hrpln__gze[afu__aekf] = s


def fillna_inplace_impl(S, value=None, method=None, axis=None, inplace=
    False, limit=None, downcast=None):
    hrpln__gze = bodo.hiframes.pd_series_ext.get_series_data(S)
    for afu__aekf in numba.parfors.parfor.internal_prange(len(hrpln__gze)):
        s = hrpln__gze[afu__aekf]
        if bodo.libs.array_kernels.isna(hrpln__gze, afu__aekf):
            s = value
        hrpln__gze[afu__aekf] = s


def str_fillna_alloc_series_impl(S, value=None, method=None, axis=None,
    inplace=False, limit=None, downcast=None):
    hrpln__gze = bodo.hiframes.pd_series_ext.get_series_data(S)
    index = bodo.hiframes.pd_series_ext.get_series_index(S)
    name = bodo.hiframes.pd_series_ext.get_series_name(S)
    zpgbp__hjz = bodo.hiframes.pd_series_ext.get_series_data(value)
    n = len(hrpln__gze)
    xkui__woahs = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
    for ptx__jtgz in numba.parfors.parfor.internal_prange(n):
        s = hrpln__gze[ptx__jtgz]
        if bodo.libs.array_kernels.isna(hrpln__gze, ptx__jtgz
            ) and not bodo.libs.array_kernels.isna(zpgbp__hjz, ptx__jtgz):
            s = zpgbp__hjz[ptx__jtgz]
        xkui__woahs[ptx__jtgz] = s
        if bodo.libs.array_kernels.isna(hrpln__gze, ptx__jtgz
            ) and bodo.libs.array_kernels.isna(zpgbp__hjz, ptx__jtgz):
            bodo.libs.array_kernels.setna(xkui__woahs, ptx__jtgz)
    return bodo.hiframes.pd_series_ext.init_series(xkui__woahs, index, name)


def fillna_series_impl(S, value=None, method=None, axis=None, inplace=False,
    limit=None, downcast=None):
    hrpln__gze = bodo.hiframes.pd_series_ext.get_series_data(S)
    index = bodo.hiframes.pd_series_ext.get_series_index(S)
    name = bodo.hiframes.pd_series_ext.get_series_name(S)
    zpgbp__hjz = bodo.hiframes.pd_series_ext.get_series_data(value)
    n = len(hrpln__gze)
    xkui__woahs = bodo.utils.utils.alloc_type(n, hrpln__gze.dtype, (-1,))
    for afu__aekf in numba.parfors.parfor.internal_prange(n):
        s = hrpln__gze[afu__aekf]
        if bodo.libs.array_kernels.isna(hrpln__gze, afu__aekf
            ) and not bodo.libs.array_kernels.isna(zpgbp__hjz, afu__aekf):
            s = zpgbp__hjz[afu__aekf]
        xkui__woahs[afu__aekf] = s
    return bodo.hiframes.pd_series_ext.init_series(xkui__woahs, index, name)


@overload_method(SeriesType, 'fillna', no_unliteral=True)
def overload_series_fillna(S, value=None, method=None, axis=None, inplace=
    False, limit=None, downcast=None):
    xqt__pxxev = dict(limit=limit, downcast=downcast)
    okxj__pvszq = dict(limit=None, downcast=None)
    check_unsupported_args('Series.fillna', xqt__pxxev, okxj__pvszq,
        package_name='pandas', module_name='Series')
    gloc__aqvlf = not is_overload_none(value)
    dmwz__nlsze = not is_overload_none(method)
    if gloc__aqvlf and dmwz__nlsze:
        raise BodoError(
            "Series.fillna(): Cannot specify both 'value' and 'method'.")
    if not gloc__aqvlf and not dmwz__nlsze:
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
    if dmwz__nlsze:
        if is_overload_true(inplace):
            raise BodoError(
                "Series.fillna() with inplace=True not supported with 'method' argument yet."
                )
        gol__qpro = (
            "Series.fillna(): 'method' argument if provided must be a constant string and one of ('backfill', 'bfill', 'pad' 'ffill')."
            )
        if not is_overload_constant_str(method):
            raise_bodo_error(gol__qpro)
        elif get_overload_const_str(method) not in ('backfill', 'bfill',
            'pad', 'ffill'):
            raise BodoError(gol__qpro)
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.fillna()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(value,
        'Series.fillna()')
    fagjc__kryog = element_type(S.data)
    gaa__nzctq = None
    if gloc__aqvlf:
        gaa__nzctq = element_type(types.unliteral(value))
    if gaa__nzctq and not can_replace(fagjc__kryog, gaa__nzctq):
        raise BodoError(
            f'Series.fillna(): Cannot use value type {gaa__nzctq} with series type {fagjc__kryog}'
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
        uicb__gle = to_str_arr_if_dict_array(S.data)
        if isinstance(value, SeriesType):

            def fillna_series_impl(S, value=None, method=None, axis=None,
                inplace=False, limit=None, downcast=None):
                hrpln__gze = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                zpgbp__hjz = bodo.hiframes.pd_series_ext.get_series_data(value)
                n = len(hrpln__gze)
                xkui__woahs = bodo.utils.utils.alloc_type(n, uicb__gle, (-1,))
                for afu__aekf in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(hrpln__gze, afu__aekf
                        ) and bodo.libs.array_kernels.isna(zpgbp__hjz,
                        afu__aekf):
                        bodo.libs.array_kernels.setna(xkui__woahs, afu__aekf)
                        continue
                    if bodo.libs.array_kernels.isna(hrpln__gze, afu__aekf):
                        xkui__woahs[afu__aekf
                            ] = bodo.utils.conversion.unbox_if_timestamp(
                            zpgbp__hjz[afu__aekf])
                        continue
                    xkui__woahs[afu__aekf
                        ] = bodo.utils.conversion.unbox_if_timestamp(hrpln__gze
                        [afu__aekf])
                return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                    index, name)
            return fillna_series_impl
        if dmwz__nlsze:
            nbkm__rxf = (types.unicode_type, types.bool_, bodo.datetime64ns,
                bodo.timedelta64ns)
            if not isinstance(fagjc__kryog, (types.Integer, types.Float)
                ) and fagjc__kryog not in nbkm__rxf:
                raise BodoError(
                    f"Series.fillna(): series of type {fagjc__kryog} are not supported with 'method' argument."
                    )

            def fillna_method_impl(S, value=None, method=None, axis=None,
                inplace=False, limit=None, downcast=None):
                hrpln__gze = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                xkui__woahs = bodo.libs.array_kernels.ffill_bfill_arr(
                    hrpln__gze, method)
                return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                    index, name)
            return fillna_method_impl

        def fillna_impl(S, value=None, method=None, axis=None, inplace=
            False, limit=None, downcast=None):
            value = bodo.utils.conversion.unbox_if_timestamp(value)
            hrpln__gze = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            n = len(hrpln__gze)
            xkui__woahs = bodo.utils.utils.alloc_type(n, uicb__gle, (-1,))
            for afu__aekf in numba.parfors.parfor.internal_prange(n):
                s = bodo.utils.conversion.unbox_if_timestamp(hrpln__gze[
                    afu__aekf])
                if bodo.libs.array_kernels.isna(hrpln__gze, afu__aekf):
                    s = value
                xkui__woahs[afu__aekf] = s
            return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                index, name)
        return fillna_impl


def create_fillna_specific_method_overload(overload_name):

    def overload_series_fillna_specific_method(S, axis=None, inplace=False,
        limit=None, downcast=None):
        ywf__qkxur = {'ffill': 'ffill', 'bfill': 'bfill', 'pad': 'ffill',
            'backfill': 'bfill'}[overload_name]
        xqt__pxxev = dict(limit=limit, downcast=downcast)
        okxj__pvszq = dict(limit=None, downcast=None)
        check_unsupported_args(f'Series.{overload_name}', xqt__pxxev,
            okxj__pvszq, package_name='pandas', module_name='Series')
        if not (is_overload_none(axis) or is_overload_zero(axis)):
            raise BodoError(
                f'Series.{overload_name}(): axis argument not supported')
        fagjc__kryog = element_type(S.data)
        nbkm__rxf = (types.unicode_type, types.bool_, bodo.datetime64ns,
            bodo.timedelta64ns)
        if not isinstance(fagjc__kryog, (types.Integer, types.Float)
            ) and fagjc__kryog not in nbkm__rxf:
            raise BodoError(
                f'Series.{overload_name}(): series of type {fagjc__kryog} are not supported.'
                )

        def impl(S, axis=None, inplace=False, limit=None, downcast=None):
            hrpln__gze = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            xkui__woahs = bodo.libs.array_kernels.ffill_bfill_arr(hrpln__gze,
                ywf__qkxur)
            return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                index, name)
        return impl
    return overload_series_fillna_specific_method


fillna_specific_methods = 'ffill', 'bfill', 'pad', 'backfill'


def _install_fillna_specific_methods():
    for overload_name in fillna_specific_methods:
        qqak__byah = create_fillna_specific_method_overload(overload_name)
        overload_method(SeriesType, overload_name, no_unliteral=True)(
            qqak__byah)


_install_fillna_specific_methods()


def check_unsupported_types(S, to_replace, value):
    if any(bodo.utils.utils.is_array_typ(x, True) for x in [S.dtype,
        to_replace, value]):
        gulrh__udaug = (
            'Series.replace(): only support with Scalar, List, or Dictionary')
        raise BodoError(gulrh__udaug)
    elif isinstance(to_replace, types.DictType) and not is_overload_none(value
        ):
        gulrh__udaug = (
            "Series.replace(): 'value' must be None when 'to_replace' is a dictionary"
            )
        raise BodoError(gulrh__udaug)
    elif any(isinstance(x, (PandasTimestampType, PDTimeDeltaType)) for x in
        [to_replace, value]):
        gulrh__udaug = (
            f'Series.replace(): Not supported for types {to_replace} and {value}'
            )
        raise BodoError(gulrh__udaug)


def series_replace_error_checking(S, to_replace, value, inplace, limit,
    regex, method):
    xqt__pxxev = dict(inplace=inplace, limit=limit, regex=regex, method=method)
    jjty__wzn = dict(inplace=False, limit=None, regex=False, method='pad')
    check_unsupported_args('Series.replace', xqt__pxxev, jjty__wzn,
        package_name='pandas', module_name='Series')
    check_unsupported_types(S, to_replace, value)


@overload_method(SeriesType, 'replace', inline='always', no_unliteral=True)
def overload_series_replace(S, to_replace=None, value=None, inplace=False,
    limit=None, regex=False, method='pad'):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.replace()')
    series_replace_error_checking(S, to_replace, value, inplace, limit,
        regex, method)
    fagjc__kryog = element_type(S.data)
    if isinstance(to_replace, types.DictType):
        arw__kxn = element_type(to_replace.key_type)
        gaa__nzctq = element_type(to_replace.value_type)
    else:
        arw__kxn = element_type(to_replace)
        gaa__nzctq = element_type(value)
    epn__hltdk = None
    if fagjc__kryog != types.unliteral(arw__kxn):
        if bodo.utils.typing.equality_always_false(fagjc__kryog, types.
            unliteral(arw__kxn)
            ) or not bodo.utils.typing.types_equality_exists(fagjc__kryog,
            arw__kxn):

            def impl(S, to_replace=None, value=None, inplace=False, limit=
                None, regex=False, method='pad'):
                return S.copy()
            return impl
        if isinstance(fagjc__kryog, (types.Float, types.Integer)
            ) or fagjc__kryog == np.bool_:
            epn__hltdk = fagjc__kryog
    if not can_replace(fagjc__kryog, types.unliteral(gaa__nzctq)):

        def impl(S, to_replace=None, value=None, inplace=False, limit=None,
            regex=False, method='pad'):
            return S.copy()
        return impl
    aeewo__awxz = to_str_arr_if_dict_array(S.data)
    if isinstance(aeewo__awxz, CategoricalArrayType):

        def cat_impl(S, to_replace=None, value=None, inplace=False, limit=
            None, regex=False, method='pad'):
            hrpln__gze = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            return bodo.hiframes.pd_series_ext.init_series(hrpln__gze.
                replace(to_replace, value), index, name)
        return cat_impl

    def impl(S, to_replace=None, value=None, inplace=False, limit=None,
        regex=False, method='pad'):
        hrpln__gze = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        n = len(hrpln__gze)
        xkui__woahs = bodo.utils.utils.alloc_type(n, aeewo__awxz, (-1,))
        pnpw__efbc = build_replace_dict(to_replace, value, epn__hltdk)
        for afu__aekf in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(hrpln__gze, afu__aekf):
                bodo.libs.array_kernels.setna(xkui__woahs, afu__aekf)
                continue
            s = hrpln__gze[afu__aekf]
            if s in pnpw__efbc:
                s = pnpw__efbc[s]
            xkui__woahs[afu__aekf] = s
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs, index, name
            )
    return impl


def build_replace_dict(to_replace, value, key_dtype_conv):
    pass


@overload(build_replace_dict)
def _build_replace_dict(to_replace, value, key_dtype_conv):
    mtb__yctf = isinstance(to_replace, (types.Number, Decimal128Type)
        ) or to_replace in [bodo.string_type, types.boolean, bodo.bytes_type]
    cpj__qcudb = is_iterable_type(to_replace)
    xurf__ueig = isinstance(value, (types.Number, Decimal128Type)
        ) or value in [bodo.string_type, bodo.bytes_type, types.boolean]
    rtb__opwoj = is_iterable_type(value)
    if mtb__yctf and xurf__ueig:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                pnpw__efbc = {}
                pnpw__efbc[key_dtype_conv(to_replace)] = value
                return pnpw__efbc
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            pnpw__efbc = {}
            pnpw__efbc[to_replace] = value
            return pnpw__efbc
        return impl
    if cpj__qcudb and xurf__ueig:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                pnpw__efbc = {}
                for nra__ciiqv in to_replace:
                    pnpw__efbc[key_dtype_conv(nra__ciiqv)] = value
                return pnpw__efbc
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            pnpw__efbc = {}
            for nra__ciiqv in to_replace:
                pnpw__efbc[nra__ciiqv] = value
            return pnpw__efbc
        return impl
    if cpj__qcudb and rtb__opwoj:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                pnpw__efbc = {}
                assert len(to_replace) == len(value
                    ), 'To_replace and value lengths must be the same'
                for afu__aekf in range(len(to_replace)):
                    pnpw__efbc[key_dtype_conv(to_replace[afu__aekf])] = value[
                        afu__aekf]
                return pnpw__efbc
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            pnpw__efbc = {}
            assert len(to_replace) == len(value
                ), 'To_replace and value lengths must be the same'
            for afu__aekf in range(len(to_replace)):
                pnpw__efbc[to_replace[afu__aekf]] = value[afu__aekf]
            return pnpw__efbc
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
            xkui__woahs = bodo.hiframes.series_impl.dt64_arr_sub(arr, bodo.
                hiframes.rolling.shift(arr, periods, False))
            return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                index, name)
        return impl_datetime

    def impl(S, periods=1):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        xkui__woahs = arr - bodo.hiframes.rolling.shift(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs, index, name
            )
    return impl


@overload_method(SeriesType, 'explode', inline='always', no_unliteral=True)
def overload_series_explode(S, ignore_index=False):
    from bodo.hiframes.split_impl import string_array_split_view_type
    xqt__pxxev = dict(ignore_index=ignore_index)
    npr__duxlt = dict(ignore_index=False)
    check_unsupported_args('Series.explode', xqt__pxxev, npr__duxlt,
        package_name='pandas', module_name='Series')
    if not (isinstance(S.data, ArrayItemArrayType) or S.data ==
        string_array_split_view_type):
        return lambda S, ignore_index=False: S.copy()

    def impl(S, ignore_index=False):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        pds__clxht = bodo.utils.conversion.index_to_array(index)
        xkui__woahs, uaz__eoadf = bodo.libs.array_kernels.explode(arr,
            pds__clxht)
        qiyo__jxpbn = bodo.utils.conversion.index_from_array(uaz__eoadf)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
            qiyo__jxpbn, name)
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
            mzb__mfi = np.empty(len(a), a.dtype)
            numba.parfors.parfor.init_prange()
            n = len(a)
            for afu__aekf in numba.parfors.parfor.internal_prange(n):
                mzb__mfi[afu__aekf] = np.argmax(a[afu__aekf])
            return mzb__mfi
        return impl


@overload(np.argmin, inline='always', no_unliteral=True)
def argmin_overload(a, axis=None, out=None):
    if isinstance(a, types.Array) and is_overload_constant_int(axis
        ) and get_overload_const_int(axis) == 1:

        def impl(a, axis=None, out=None):
            odoxs__amosc = np.empty(len(a), a.dtype)
            numba.parfors.parfor.init_prange()
            n = len(a)
            for afu__aekf in numba.parfors.parfor.internal_prange(n):
                odoxs__amosc[afu__aekf] = np.argmin(a[afu__aekf])
            return odoxs__amosc
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
    xqt__pxxev = dict(axis=axis, inplace=inplace, how=how)
    zqeou__wft = dict(axis=0, inplace=False, how=None)
    check_unsupported_args('Series.dropna', xqt__pxxev, zqeou__wft,
        package_name='pandas', module_name='Series')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.dropna()')
    if S.dtype == bodo.string_type:

        def dropna_str_impl(S, axis=0, inplace=False, how=None):
            hrpln__gze = bodo.hiframes.pd_series_ext.get_series_data(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            itgk__czqu = S.notna().values
            pds__clxht = bodo.utils.conversion.extract_index_array(S)
            qiyo__jxpbn = bodo.utils.conversion.convert_to_index(pds__clxht
                [itgk__czqu])
            xkui__woahs = (bodo.hiframes.series_kernels.
                _series_dropna_str_alloc_impl_inner(hrpln__gze))
            return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                qiyo__jxpbn, name)
        return dropna_str_impl
    else:

        def dropna_impl(S, axis=0, inplace=False, how=None):
            hrpln__gze = bodo.hiframes.pd_series_ext.get_series_data(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            pds__clxht = bodo.utils.conversion.extract_index_array(S)
            itgk__czqu = S.notna().values
            qiyo__jxpbn = bodo.utils.conversion.convert_to_index(pds__clxht
                [itgk__czqu])
            xkui__woahs = hrpln__gze[itgk__czqu]
            return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                qiyo__jxpbn, name)
        return dropna_impl


@overload_method(SeriesType, 'shift', inline='always', no_unliteral=True)
def overload_series_shift(S, periods=1, freq=None, axis=0, fill_value=None):
    xqt__pxxev = dict(freq=freq, axis=axis, fill_value=fill_value)
    okxj__pvszq = dict(freq=None, axis=0, fill_value=None)
    check_unsupported_args('Series.shift', xqt__pxxev, okxj__pvszq,
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
        xkui__woahs = bodo.hiframes.rolling.shift(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs, index, name
            )
    return impl


@overload_method(SeriesType, 'pct_change', inline='always', no_unliteral=True)
def overload_series_pct_change(S, periods=1, fill_method='pad', limit=None,
    freq=None):
    xqt__pxxev = dict(fill_method=fill_method, limit=limit, freq=freq)
    okxj__pvszq = dict(fill_method='pad', limit=None, freq=None)
    check_unsupported_args('Series.pct_change', xqt__pxxev, okxj__pvszq,
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
        xkui__woahs = bodo.hiframes.rolling.pct_change(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs, index, name
            )
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
            mor__tkx = 'None'
        else:
            mor__tkx = 'other'
        ttone__wjf = """def impl(S, cond, other=np.nan, inplace=False, axis=None, level=None, errors='raise',try_cast=False):
"""
        if func_name == 'mask':
            ttone__wjf += '  cond = ~cond\n'
        ttone__wjf += (
            '  arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        ttone__wjf += (
            '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        ttone__wjf += (
            '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        ttone__wjf += (
            f'  out_arr = bodo.hiframes.series_impl.where_impl(cond, arr, {mor__tkx})\n'
            )
        ttone__wjf += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        lum__vkqd = {}
        exec(ttone__wjf, {'bodo': bodo, 'np': np}, lum__vkqd)
        impl = lum__vkqd['impl']
        return impl
    return overload_series_mask_where


def _install_series_mask_where_overload():
    for func_name in ('mask', 'where'):
        qqak__byah = create_series_mask_where_overload(func_name)
        overload_method(SeriesType, func_name, no_unliteral=True)(qqak__byah)


_install_series_mask_where_overload()


def _validate_arguments_mask_where(func_name, S, cond, other, inplace, axis,
    level, errors, try_cast):
    xqt__pxxev = dict(inplace=inplace, level=level, errors=errors, try_cast
        =try_cast)
    okxj__pvszq = dict(inplace=False, level=None, errors='raise', try_cast=
        False)
    check_unsupported_args(f'{func_name}', xqt__pxxev, okxj__pvszq,
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
    vlxnv__rdjre = is_overload_constant_nan(other)
    if not (is_default or vlxnv__rdjre or is_scalar_type(other) or 
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
            hwdju__hxet = arr.dtype.elem_type
        else:
            hwdju__hxet = arr.dtype
        if is_iterable_type(other):
            nbqb__miynd = other.dtype
        elif vlxnv__rdjre:
            nbqb__miynd = types.float64
        else:
            nbqb__miynd = types.unliteral(other)
        if not vlxnv__rdjre and not is_common_scalar_dtype([hwdju__hxet,
            nbqb__miynd]):
            raise BodoError(
                f"{func_name}() series and 'other' must share a common type.")


def create_explicit_binary_op_overload(op):

    def overload_series_explicit_binary_op(S, other, level=None, fill_value
        =None, axis=0):
        xqt__pxxev = dict(level=level, axis=axis)
        okxj__pvszq = dict(level=None, axis=0)
        check_unsupported_args('series.{}'.format(op.__name__), xqt__pxxev,
            okxj__pvszq, package_name='pandas', module_name='Series')
        xxs__ouol = other == string_type or is_overload_constant_str(other)
        dzzht__vdwtz = is_iterable_type(other) and other.dtype == string_type
        jqpb__cwv = S.dtype == string_type and (op == operator.add and (
            xxs__ouol or dzzht__vdwtz) or op == operator.mul and isinstance
            (other, types.Integer))
        lniy__vpdow = S.dtype == bodo.timedelta64ns
        qqgh__ejjt = S.dtype == bodo.datetime64ns
        megz__taxd = is_iterable_type(other) and (other.dtype ==
            datetime_timedelta_type or other.dtype == bodo.timedelta64ns)
        hsxq__xoby = is_iterable_type(other) and (other.dtype ==
            datetime_datetime_type or other.dtype == pd_timestamp_type or 
            other.dtype == bodo.datetime64ns)
        til__pde = lniy__vpdow and (megz__taxd or hsxq__xoby
            ) or qqgh__ejjt and megz__taxd
        til__pde = til__pde and op == operator.add
        if not (isinstance(S.dtype, types.Number) or jqpb__cwv or til__pde):
            raise BodoError(f'Unsupported types for Series.{op.__name__}')
        pygw__dwu = numba.core.registry.cpu_target.typing_context
        if is_scalar_type(other):
            args = S.data, other
            aeewo__awxz = pygw__dwu.resolve_function_type(op, args, {}
                ).return_type
            if isinstance(S.data, IntegerArrayType
                ) and aeewo__awxz == types.Array(types.bool_, 1, 'C'):
                aeewo__awxz = boolean_array

            def impl_scalar(S, other, level=None, fill_value=None, axis=0):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                numba.parfors.parfor.init_prange()
                other = bodo.utils.conversion.unbox_if_timestamp(other)
                n = len(arr)
                xkui__woahs = bodo.utils.utils.alloc_type(n, aeewo__awxz, (-1,)
                    )
                for afu__aekf in numba.parfors.parfor.internal_prange(n):
                    rqpm__hkn = bodo.libs.array_kernels.isna(arr, afu__aekf)
                    if rqpm__hkn:
                        if fill_value is None:
                            bodo.libs.array_kernels.setna(xkui__woahs,
                                afu__aekf)
                        else:
                            xkui__woahs[afu__aekf] = op(fill_value, other)
                    else:
                        xkui__woahs[afu__aekf] = op(arr[afu__aekf], other)
                return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                    index, name)
            return impl_scalar
        args = S.data, types.Array(other.dtype, 1, 'C')
        aeewo__awxz = pygw__dwu.resolve_function_type(op, args, {}).return_type
        if isinstance(S.data, IntegerArrayType) and aeewo__awxz == types.Array(
            types.bool_, 1, 'C'):
            aeewo__awxz = boolean_array

        def impl(S, other, level=None, fill_value=None, axis=0):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            pwbfx__mjay = bodo.utils.conversion.coerce_to_array(other)
            numba.parfors.parfor.init_prange()
            n = len(arr)
            xkui__woahs = bodo.utils.utils.alloc_type(n, aeewo__awxz, (-1,))
            for afu__aekf in numba.parfors.parfor.internal_prange(n):
                rqpm__hkn = bodo.libs.array_kernels.isna(arr, afu__aekf)
                kmwc__bzds = bodo.libs.array_kernels.isna(pwbfx__mjay,
                    afu__aekf)
                if rqpm__hkn and kmwc__bzds:
                    bodo.libs.array_kernels.setna(xkui__woahs, afu__aekf)
                elif rqpm__hkn:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(xkui__woahs, afu__aekf)
                    else:
                        xkui__woahs[afu__aekf] = op(fill_value, pwbfx__mjay
                            [afu__aekf])
                elif kmwc__bzds:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(xkui__woahs, afu__aekf)
                    else:
                        xkui__woahs[afu__aekf] = op(arr[afu__aekf], fill_value)
                else:
                    xkui__woahs[afu__aekf] = op(arr[afu__aekf], pwbfx__mjay
                        [afu__aekf])
            return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
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
        pygw__dwu = numba.core.registry.cpu_target.typing_context
        if isinstance(other, types.Number):
            args = other, S.data
            aeewo__awxz = pygw__dwu.resolve_function_type(op, args, {}
                ).return_type
            if isinstance(S.data, IntegerArrayType
                ) and aeewo__awxz == types.Array(types.bool_, 1, 'C'):
                aeewo__awxz = boolean_array

            def impl_scalar(S, other, level=None, fill_value=None, axis=0):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                numba.parfors.parfor.init_prange()
                n = len(arr)
                xkui__woahs = bodo.utils.utils.alloc_type(n, aeewo__awxz, None)
                for afu__aekf in numba.parfors.parfor.internal_prange(n):
                    rqpm__hkn = bodo.libs.array_kernels.isna(arr, afu__aekf)
                    if rqpm__hkn:
                        if fill_value is None:
                            bodo.libs.array_kernels.setna(xkui__woahs,
                                afu__aekf)
                        else:
                            xkui__woahs[afu__aekf] = op(other, fill_value)
                    else:
                        xkui__woahs[afu__aekf] = op(other, arr[afu__aekf])
                return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                    index, name)
            return impl_scalar
        args = types.Array(other.dtype, 1, 'C'), S.data
        aeewo__awxz = pygw__dwu.resolve_function_type(op, args, {}).return_type
        if isinstance(S.data, IntegerArrayType) and aeewo__awxz == types.Array(
            types.bool_, 1, 'C'):
            aeewo__awxz = boolean_array

        def impl(S, other, level=None, fill_value=None, axis=0):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            pwbfx__mjay = bodo.hiframes.pd_series_ext.get_series_data(other)
            numba.parfors.parfor.init_prange()
            n = len(arr)
            xkui__woahs = bodo.utils.utils.alloc_type(n, aeewo__awxz, None)
            for afu__aekf in numba.parfors.parfor.internal_prange(n):
                rqpm__hkn = bodo.libs.array_kernels.isna(arr, afu__aekf)
                kmwc__bzds = bodo.libs.array_kernels.isna(pwbfx__mjay,
                    afu__aekf)
                xkui__woahs[afu__aekf] = op(pwbfx__mjay[afu__aekf], arr[
                    afu__aekf])
                if rqpm__hkn and kmwc__bzds:
                    bodo.libs.array_kernels.setna(xkui__woahs, afu__aekf)
                elif rqpm__hkn:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(xkui__woahs, afu__aekf)
                    else:
                        xkui__woahs[afu__aekf] = op(pwbfx__mjay[afu__aekf],
                            fill_value)
                elif kmwc__bzds:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(xkui__woahs, afu__aekf)
                    else:
                        xkui__woahs[afu__aekf] = op(fill_value, arr[afu__aekf])
                else:
                    xkui__woahs[afu__aekf] = op(pwbfx__mjay[afu__aekf], arr
                        [afu__aekf])
            return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
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
    for op, nyqa__jyrq in explicit_binop_funcs_two_ways.items():
        for name in nyqa__jyrq:
            qqak__byah = create_explicit_binary_op_overload(op)
            gouw__gvfe = create_explicit_binary_reverse_op_overload(op)
            zdzfl__yqc = 'r' + name
            overload_method(SeriesType, name, no_unliteral=True)(qqak__byah)
            overload_method(SeriesType, zdzfl__yqc, no_unliteral=True)(
                gouw__gvfe)
            explicit_binop_funcs.add(name)
    for op, name in explicit_binop_funcs_single.items():
        qqak__byah = create_explicit_binary_op_overload(op)
        overload_method(SeriesType, name, no_unliteral=True)(qqak__byah)
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
                jff__ouwto = (bodo.utils.conversion.
                    get_array_if_series_or_index(rhs))
                xkui__woahs = dt64_arr_sub(arr, jff__ouwto)
                return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
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
                xkui__woahs = np.empty(n, np.dtype('datetime64[ns]'))
                for afu__aekf in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(arr, afu__aekf):
                        bodo.libs.array_kernels.setna(xkui__woahs, afu__aekf)
                        continue
                    ygv__yusa = (bodo.hiframes.pd_timestamp_ext.
                        convert_datetime64_to_timestamp(arr[afu__aekf]))
                    lzkov__rgh = op(ygv__yusa, rhs)
                    xkui__woahs[afu__aekf
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        lzkov__rgh.value)
                return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
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
                    jff__ouwto = (bodo.utils.conversion.
                        get_array_if_series_or_index(rhs))
                    xkui__woahs = op(arr, bodo.utils.conversion.
                        unbox_if_timestamp(jff__ouwto))
                    return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                        index, name)
                return impl

            def impl(lhs, rhs):
                arr = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                index = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                name = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                jff__ouwto = (bodo.utils.conversion.
                    get_array_if_series_or_index(rhs))
                xkui__woahs = op(arr, jff__ouwto)
                return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                    index, name)
            return impl
        if isinstance(rhs, SeriesType):
            if rhs.dtype in [bodo.datetime64ns, bodo.timedelta64ns]:

                def impl(lhs, rhs):
                    arr = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                    index = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                    name = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                    rcued__kki = (bodo.utils.conversion.
                        get_array_if_series_or_index(lhs))
                    xkui__woahs = op(bodo.utils.conversion.
                        unbox_if_timestamp(rcued__kki), arr)
                    return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                        index, name)
                return impl

            def impl(lhs, rhs):
                arr = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                index = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                name = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                rcued__kki = (bodo.utils.conversion.
                    get_array_if_series_or_index(lhs))
                xkui__woahs = op(rcued__kki, arr)
                return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                    index, name)
            return impl
    return overload_series_binary_op


skips = list(explicit_binop_funcs_two_ways.keys()) + list(
    explicit_binop_funcs_single.keys()) + split_logical_binops_funcs


def _install_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_binary_ops:
        if op in skips:
            continue
        qqak__byah = create_binary_op_overload(op)
        overload(op)(qqak__byah)


_install_binary_ops()


def dt64_arr_sub(arg1, arg2):
    return arg1 - arg2


@overload(dt64_arr_sub, no_unliteral=True)
def overload_dt64_arr_sub(arg1, arg2):
    assert arg1 == types.Array(bodo.datetime64ns, 1, 'C'
        ) and arg2 == types.Array(bodo.datetime64ns, 1, 'C')
    eaqbm__nizft = np.dtype('timedelta64[ns]')

    def impl(arg1, arg2):
        numba.parfors.parfor.init_prange()
        n = len(arg1)
        S = np.empty(n, eaqbm__nizft)
        for afu__aekf in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(arg1, afu__aekf
                ) or bodo.libs.array_kernels.isna(arg2, afu__aekf):
                bodo.libs.array_kernels.setna(S, afu__aekf)
                continue
            S[afu__aekf
                ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                bodo.hiframes.pd_timestamp_ext.dt64_to_integer(arg1[
                afu__aekf]) - bodo.hiframes.pd_timestamp_ext.
                dt64_to_integer(arg2[afu__aekf]))
        return S
    return impl


def create_inplace_binary_op_overload(op):

    def overload_series_inplace_binary_op(S, other):
        if isinstance(S, SeriesType) or isinstance(other, SeriesType):

            def impl(S, other):
                arr = bodo.utils.conversion.get_array_if_series_or_index(S)
                pwbfx__mjay = (bodo.utils.conversion.
                    get_array_if_series_or_index(other))
                op(arr, pwbfx__mjay)
                return S
            return impl
    return overload_series_inplace_binary_op


def _install_inplace_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_inplace_binary_ops:
        qqak__byah = create_inplace_binary_op_overload(op)
        overload(op, no_unliteral=True)(qqak__byah)


_install_inplace_binary_ops()


def create_unary_op_overload(op):

    def overload_series_unary_op(S):
        if isinstance(S, SeriesType):

            def impl(S):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                xkui__woahs = op(arr)
                return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                    index, name)
            return impl
    return overload_series_unary_op


def _install_unary_ops():
    for op in bodo.hiframes.pd_series_ext.series_unary_ops:
        qqak__byah = create_unary_op_overload(op)
        overload(op, no_unliteral=True)(qqak__byah)


_install_unary_ops()


def create_ufunc_overload(ufunc):
    if ufunc.nin == 1:

        def overload_series_ufunc_nin_1(S):
            if isinstance(S, SeriesType):

                def impl(S):
                    arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                    index = bodo.hiframes.pd_series_ext.get_series_index(S)
                    name = bodo.hiframes.pd_series_ext.get_series_name(S)
                    xkui__woahs = ufunc(arr)
                    return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
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
                    pwbfx__mjay = (bodo.utils.conversion.
                        get_array_if_series_or_index(S2))
                    xkui__woahs = ufunc(arr, pwbfx__mjay)
                    return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                        index, name)
                return impl
            elif isinstance(S2, SeriesType):

                def impl(S1, S2):
                    arr = bodo.utils.conversion.get_array_if_series_or_index(S1
                        )
                    pwbfx__mjay = bodo.hiframes.pd_series_ext.get_series_data(
                        S2)
                    index = bodo.hiframes.pd_series_ext.get_series_index(S2)
                    name = bodo.hiframes.pd_series_ext.get_series_name(S2)
                    xkui__woahs = ufunc(arr, pwbfx__mjay)
                    return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                        index, name)
                return impl
        return overload_series_ufunc_nin_2
    else:
        raise RuntimeError(
            "Don't know how to register ufuncs from ufunc_db with arity > 2")


def _install_np_ufuncs():
    import numba.np.ufunc_db
    for ufunc in numba.np.ufunc_db.get_ufuncs():
        qqak__byah = create_ufunc_overload(ufunc)
        overload(ufunc, no_unliteral=True)(qqak__byah)


_install_np_ufuncs()


def argsort(A):
    return np.argsort(A)


@overload(argsort, no_unliteral=True)
def overload_argsort(A):

    def impl(A):
        n = len(A)
        dkela__viw = bodo.libs.str_arr_ext.to_list_if_immutable_arr((A.copy(),)
            )
        ijnzw__vjmw = np.arange(n),
        bodo.libs.timsort.sort(dkela__viw, 0, n, ijnzw__vjmw)
        return ijnzw__vjmw[0]
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
        szjg__obcj = get_overload_const_str(downcast)
        if szjg__obcj in ('integer', 'signed'):
            out_dtype = types.int64
        elif szjg__obcj == 'unsigned':
            out_dtype = types.uint64
        else:
            assert szjg__obcj == 'float'
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(arg_a,
        'pandas.to_numeric()')
    if isinstance(arg_a, (types.Array, IntegerArrayType)):
        return lambda arg_a, errors='raise', downcast=None: arg_a.astype(
            out_dtype)
    if isinstance(arg_a, SeriesType):

        def impl_series(arg_a, errors='raise', downcast=None):
            hrpln__gze = bodo.hiframes.pd_series_ext.get_series_data(arg_a)
            index = bodo.hiframes.pd_series_ext.get_series_index(arg_a)
            name = bodo.hiframes.pd_series_ext.get_series_name(arg_a)
            xkui__woahs = pd.to_numeric(hrpln__gze, errors, downcast)
            return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                index, name)
        return impl_series
    if not is_str_arr_type(arg_a):
        raise BodoError(f'pd.to_numeric(): invalid argument type {arg_a}')
    if out_dtype == types.float64:

        def to_numeric_float_impl(arg_a, errors='raise', downcast=None):
            numba.parfors.parfor.init_prange()
            n = len(arg_a)
            bcbc__rrar = np.empty(n, np.float64)
            for afu__aekf in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arg_a, afu__aekf):
                    bodo.libs.array_kernels.setna(bcbc__rrar, afu__aekf)
                else:
                    bodo.libs.str_arr_ext.str_arr_item_to_numeric(bcbc__rrar,
                        afu__aekf, arg_a, afu__aekf)
            return bcbc__rrar
        return to_numeric_float_impl
    else:

        def to_numeric_int_impl(arg_a, errors='raise', downcast=None):
            numba.parfors.parfor.init_prange()
            n = len(arg_a)
            bcbc__rrar = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)
            for afu__aekf in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arg_a, afu__aekf):
                    bodo.libs.array_kernels.setna(bcbc__rrar, afu__aekf)
                else:
                    bodo.libs.str_arr_ext.str_arr_item_to_numeric(bcbc__rrar,
                        afu__aekf, arg_a, afu__aekf)
            return bcbc__rrar
        return to_numeric_int_impl


def series_filter_bool(arr, bool_arr):
    return arr[bool_arr]


@infer_global(series_filter_bool)
class SeriesFilterBoolInfer(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 2
        xvaz__zqp = if_series_to_array_type(args[0])
        if isinstance(xvaz__zqp, types.Array) and isinstance(xvaz__zqp.
            dtype, types.Integer):
            xvaz__zqp = types.Array(types.float64, 1, 'C')
        return xvaz__zqp(*args)


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
    qns__oenvn = bodo.utils.utils.is_array_typ(x, True)
    cbz__njpji = bodo.utils.utils.is_array_typ(y, True)
    ttone__wjf = 'def _impl(condition, x, y):\n'
    if isinstance(condition, SeriesType):
        ttone__wjf += (
            '  condition = bodo.hiframes.pd_series_ext.get_series_data(condition)\n'
            )
    if qns__oenvn and not bodo.utils.utils.is_array_typ(x, False):
        ttone__wjf += '  x = bodo.utils.conversion.coerce_to_array(x)\n'
    if cbz__njpji and not bodo.utils.utils.is_array_typ(y, False):
        ttone__wjf += '  y = bodo.utils.conversion.coerce_to_array(y)\n'
    ttone__wjf += '  n = len(condition)\n'
    uqp__txmd = x.dtype if qns__oenvn else types.unliteral(x)
    adbxf__bjnr = y.dtype if cbz__njpji else types.unliteral(y)
    if not isinstance(x, CategoricalArrayType):
        uqp__txmd = element_type(x)
    if not isinstance(y, CategoricalArrayType):
        adbxf__bjnr = element_type(y)

    def get_data(x):
        if isinstance(x, SeriesType):
            return x.data
        elif isinstance(x, types.Array):
            return x
        return types.unliteral(x)
    hhca__qhvld = get_data(x)
    rky__fcx = get_data(y)
    is_nullable = any(bodo.utils.typing.is_nullable(ijnzw__vjmw) for
        ijnzw__vjmw in [hhca__qhvld, rky__fcx])
    if rky__fcx == types.none:
        if isinstance(uqp__txmd, types.Number):
            out_dtype = types.Array(types.float64, 1, 'C')
        else:
            out_dtype = to_nullable_type(x)
    elif hhca__qhvld == rky__fcx and not is_nullable:
        out_dtype = dtype_to_array_type(uqp__txmd)
    elif uqp__txmd == string_type or adbxf__bjnr == string_type:
        out_dtype = bodo.string_array_type
    elif hhca__qhvld == bytes_type or (qns__oenvn and uqp__txmd == bytes_type
        ) and (rky__fcx == bytes_type or cbz__njpji and adbxf__bjnr ==
        bytes_type):
        out_dtype = binary_array_type
    elif isinstance(uqp__txmd, bodo.PDCategoricalDtype):
        out_dtype = None
    elif uqp__txmd in [bodo.timedelta64ns, bodo.datetime64ns]:
        out_dtype = types.Array(uqp__txmd, 1, 'C')
    elif adbxf__bjnr in [bodo.timedelta64ns, bodo.datetime64ns]:
        out_dtype = types.Array(adbxf__bjnr, 1, 'C')
    else:
        out_dtype = numba.from_dtype(np.promote_types(numba.np.
            numpy_support.as_dtype(uqp__txmd), numba.np.numpy_support.
            as_dtype(adbxf__bjnr)))
        out_dtype = types.Array(out_dtype, 1, 'C')
        if is_nullable:
            out_dtype = bodo.utils.typing.to_nullable_type(out_dtype)
    if isinstance(uqp__txmd, bodo.PDCategoricalDtype):
        wgtml__nur = 'x'
    else:
        wgtml__nur = 'out_dtype'
    ttone__wjf += (
        f'  out_arr = bodo.utils.utils.alloc_type(n, {wgtml__nur}, (-1,))\n')
    if isinstance(uqp__txmd, bodo.PDCategoricalDtype):
        ttone__wjf += """  out_codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(out_arr)
"""
        ttone__wjf += (
            '  x_codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(x)\n'
            )
    ttone__wjf += '  for j in numba.parfors.parfor.internal_prange(n):\n'
    ttone__wjf += (
        '    if not bodo.libs.array_kernels.isna(condition, j) and condition[j]:\n'
        )
    if qns__oenvn:
        ttone__wjf += '      if bodo.libs.array_kernels.isna(x, j):\n'
        ttone__wjf += '        setna(out_arr, j)\n'
        ttone__wjf += '        continue\n'
    if isinstance(uqp__txmd, bodo.PDCategoricalDtype):
        ttone__wjf += '      out_codes[j] = x_codes[j]\n'
    else:
        ttone__wjf += (
            '      out_arr[j] = bodo.utils.conversion.unbox_if_timestamp({})\n'
            .format('x[j]' if qns__oenvn else 'x'))
    ttone__wjf += '    else:\n'
    if cbz__njpji:
        ttone__wjf += '      if bodo.libs.array_kernels.isna(y, j):\n'
        ttone__wjf += '        setna(out_arr, j)\n'
        ttone__wjf += '        continue\n'
    if rky__fcx == types.none:
        if isinstance(uqp__txmd, bodo.PDCategoricalDtype):
            ttone__wjf += '      out_codes[j] = -1\n'
        else:
            ttone__wjf += '      setna(out_arr, j)\n'
    else:
        ttone__wjf += (
            '      out_arr[j] = bodo.utils.conversion.unbox_if_timestamp({})\n'
            .format('y[j]' if cbz__njpji else 'y'))
    ttone__wjf += '  return out_arr\n'
    lum__vkqd = {}
    exec(ttone__wjf, {'bodo': bodo, 'numba': numba, 'setna': bodo.libs.
        array_kernels.setna, 'np': np, 'out_dtype': out_dtype}, lum__vkqd)
    nhb__jakji = lum__vkqd['_impl']
    return nhb__jakji


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
        kwb__lkjx = choicelist.dtype
        if not bodo.utils.utils.is_array_typ(kwb__lkjx, True):
            raise BodoError(
                "np.select(): 'choicelist' argument must be list or tuple of series/arrays types"
                )
        if is_series_type(kwb__lkjx):
            pccj__xhmiv = kwb__lkjx.data.dtype
        else:
            pccj__xhmiv = kwb__lkjx.dtype
        if isinstance(pccj__xhmiv, bodo.PDCategoricalDtype):
            raise BodoError(
                'np.select(): data with choicelist of type Categorical not yet supported'
                )
        vha__gugis = kwb__lkjx
    else:
        fzha__bndfq = []
        for kwb__lkjx in choicelist:
            if not bodo.utils.utils.is_array_typ(kwb__lkjx, True):
                raise BodoError(
                    "np.select(): 'choicelist' argument must be list or tuple of series/arrays types"
                    )
            if is_series_type(kwb__lkjx):
                pccj__xhmiv = kwb__lkjx.data.dtype
            else:
                pccj__xhmiv = kwb__lkjx.dtype
            if isinstance(pccj__xhmiv, bodo.PDCategoricalDtype):
                raise BodoError(
                    'np.select(): data with choicelist of type Categorical not yet supported'
                    )
            fzha__bndfq.append(pccj__xhmiv)
        if not is_common_scalar_dtype(fzha__bndfq):
            raise BodoError(
                f"np.select(): 'choicelist' items must be arrays with a commmon data type. Found a tuple with the following data types {choicelist}."
                )
        vha__gugis = choicelist[0]
    if is_series_type(vha__gugis):
        vha__gugis = vha__gugis.data
    if is_overload_constant_int(default) and get_overload_const_int(default
        ) == 0:
        pass
    else:
        if not is_scalar_type(default):
            raise BodoError(
                "np.select(): 'default' argument must be scalar type")
        if not (is_common_scalar_dtype([default, vha__gugis.dtype]) or 
            default == types.none or is_overload_constant_nan(default)):
            raise BodoError(
                f"np.select(): 'default' is not type compatible with the array types in choicelist. Choicelist type: {choicelist}, Default type: {default}"
                )
    if not (isinstance(vha__gugis, types.Array) or isinstance(vha__gugis,
        BooleanArrayType) or isinstance(vha__gugis, IntegerArrayType) or 
        bodo.utils.utils.is_array_typ(vha__gugis, False) and vha__gugis.
        dtype in [bodo.string_type, bodo.bytes_type]):
        raise BodoError(
            f'np.select(): data with choicelist of type {vha__gugis} not yet supported'
            )


@overload(np.select)
def overload_np_select(condlist, choicelist, default=0):
    _verify_np_select_arg_typs(condlist, choicelist, default)
    njdq__rbg = isinstance(choicelist, (types.List, types.UniTuple)
        ) and isinstance(condlist, (types.List, types.UniTuple))
    if isinstance(choicelist, (types.List, types.UniTuple)):
        mhy__kpx = choicelist.dtype
    else:
        sufkp__sqfqz = False
        fzha__bndfq = []
        for kwb__lkjx in choicelist:
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(kwb__lkjx
                , 'numpy.select()')
            if is_nullable_type(kwb__lkjx):
                sufkp__sqfqz = True
            if is_series_type(kwb__lkjx):
                pccj__xhmiv = kwb__lkjx.data.dtype
            else:
                pccj__xhmiv = kwb__lkjx.dtype
            if isinstance(pccj__xhmiv, bodo.PDCategoricalDtype):
                raise BodoError(
                    'np.select(): data with choicelist of type Categorical not yet supported'
                    )
            fzha__bndfq.append(pccj__xhmiv)
        vuwia__vjvca, bii__qsgu = get_common_scalar_dtype(fzha__bndfq)
        if not bii__qsgu:
            raise BodoError('Internal error in overload_np_select')
        xnqa__xadh = dtype_to_array_type(vuwia__vjvca)
        if sufkp__sqfqz:
            xnqa__xadh = to_nullable_type(xnqa__xadh)
        mhy__kpx = xnqa__xadh
    if isinstance(mhy__kpx, SeriesType):
        mhy__kpx = mhy__kpx.data
    if is_overload_constant_int(default) and get_overload_const_int(default
        ) == 0:
        dmqb__tftw = True
    else:
        dmqb__tftw = False
    usv__creo = False
    gfw__ctzz = False
    if dmqb__tftw:
        if isinstance(mhy__kpx.dtype, types.Number):
            pass
        elif mhy__kpx.dtype == types.bool_:
            gfw__ctzz = True
        else:
            usv__creo = True
            mhy__kpx = to_nullable_type(mhy__kpx)
    elif default == types.none or is_overload_constant_nan(default):
        usv__creo = True
        mhy__kpx = to_nullable_type(mhy__kpx)
    ttone__wjf = 'def np_select_impl(condlist, choicelist, default=0):\n'
    ttone__wjf += '  if len(condlist) != len(choicelist):\n'
    ttone__wjf += """    raise ValueError('list of cases must be same length as list of conditions')
"""
    ttone__wjf += '  output_len = len(choicelist[0])\n'
    ttone__wjf += (
        '  out = bodo.utils.utils.alloc_type(output_len, alloc_typ, (-1,))\n')
    ttone__wjf += '  for i in range(output_len):\n'
    if usv__creo:
        ttone__wjf += '    bodo.libs.array_kernels.setna(out, i)\n'
    elif gfw__ctzz:
        ttone__wjf += '    out[i] = False\n'
    else:
        ttone__wjf += '    out[i] = default\n'
    if njdq__rbg:
        ttone__wjf += '  for i in range(len(condlist) - 1, -1, -1):\n'
        ttone__wjf += '    cond = condlist[i]\n'
        ttone__wjf += '    choice = choicelist[i]\n'
        ttone__wjf += '    out = np.where(cond, choice, out)\n'
    else:
        for afu__aekf in range(len(choicelist) - 1, -1, -1):
            ttone__wjf += f'  cond = condlist[{afu__aekf}]\n'
            ttone__wjf += f'  choice = choicelist[{afu__aekf}]\n'
            ttone__wjf += f'  out = np.where(cond, choice, out)\n'
    ttone__wjf += '  return out'
    lum__vkqd = dict()
    exec(ttone__wjf, {'bodo': bodo, 'numba': numba, 'setna': bodo.libs.
        array_kernels.setna, 'np': np, 'alloc_typ': mhy__kpx}, lum__vkqd)
    impl = lum__vkqd['np_select_impl']
    return impl


@overload_method(SeriesType, 'duplicated', inline='always', no_unliteral=True)
def overload_series_duplicated(S, keep='first'):

    def impl(S, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        xkui__woahs = bodo.libs.array_kernels.duplicated((arr,))
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs, index, name
            )
    return impl


@overload_method(SeriesType, 'drop_duplicates', inline='always',
    no_unliteral=True)
def overload_series_drop_duplicates(S, subset=None, keep='first', inplace=False
    ):
    xqt__pxxev = dict(subset=subset, keep=keep, inplace=inplace)
    okxj__pvszq = dict(subset=None, keep='first', inplace=False)
    check_unsupported_args('Series.drop_duplicates', xqt__pxxev,
        okxj__pvszq, package_name='pandas', module_name='Series')

    def impl(S, subset=None, keep='first', inplace=False):
        cebu__ghmo = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(S))
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        (cebu__ghmo,), pds__clxht = bodo.libs.array_kernels.drop_duplicates((
            cebu__ghmo,), index, 1)
        index = bodo.utils.conversion.index_from_array(pds__clxht)
        return bodo.hiframes.pd_series_ext.init_series(cebu__ghmo, index, name)
    return impl


@overload_method(SeriesType, 'between', inline='always', no_unliteral=True)
def overload_series_between(S, left, right, inclusive='both'):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S,
        'Series.between()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(left,
        'Series.between()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(right,
        'Series.between()')
    vwubu__uoe = element_type(S.data)
    if not is_common_scalar_dtype([vwubu__uoe, left]):
        raise_bodo_error(
            "Series.between(): 'left' must be compariable with the Series data"
            )
    if not is_common_scalar_dtype([vwubu__uoe, right]):
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
        xkui__woahs = np.empty(n, np.bool_)
        for afu__aekf in numba.parfors.parfor.internal_prange(n):
            gfy__hdlz = bodo.utils.conversion.box_if_dt64(arr[afu__aekf])
            if inclusive == 'both':
                xkui__woahs[afu__aekf
                    ] = gfy__hdlz <= right and gfy__hdlz >= left
            else:
                xkui__woahs[afu__aekf] = gfy__hdlz < right and gfy__hdlz > left
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs, index, name
            )
    return impl


@overload_method(SeriesType, 'repeat', inline='always', no_unliteral=True)
def overload_series_repeat(S, repeats, axis=None):
    xqt__pxxev = dict(axis=axis)
    okxj__pvszq = dict(axis=None)
    check_unsupported_args('Series.repeat', xqt__pxxev, okxj__pvszq,
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
            pds__clxht = bodo.utils.conversion.index_to_array(index)
            xkui__woahs = bodo.libs.array_kernels.repeat_kernel(arr, repeats)
            uaz__eoadf = bodo.libs.array_kernels.repeat_kernel(pds__clxht,
                repeats)
            qiyo__jxpbn = bodo.utils.conversion.index_from_array(uaz__eoadf)
            return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
                qiyo__jxpbn, name)
        return impl_int

    def impl_arr(S, repeats, axis=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        pds__clxht = bodo.utils.conversion.index_to_array(index)
        repeats = bodo.utils.conversion.coerce_to_array(repeats)
        xkui__woahs = bodo.libs.array_kernels.repeat_kernel(arr, repeats)
        uaz__eoadf = bodo.libs.array_kernels.repeat_kernel(pds__clxht, repeats)
        qiyo__jxpbn = bodo.utils.conversion.index_from_array(uaz__eoadf)
        return bodo.hiframes.pd_series_ext.init_series(xkui__woahs,
            qiyo__jxpbn, name)
    return impl_arr


@overload_method(SeriesType, 'to_dict', no_unliteral=True)
def overload_to_dict(S, into=None):

    def impl(S, into=None):
        ijnzw__vjmw = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(S))
        n = len(ijnzw__vjmw)
        scn__vqwd = {}
        for afu__aekf in range(n):
            gfy__hdlz = bodo.utils.conversion.box_if_dt64(ijnzw__vjmw[
                afu__aekf])
            scn__vqwd[index[afu__aekf]] = gfy__hdlz
        return scn__vqwd
    return impl


@overload_method(SeriesType, 'to_frame', inline='always', no_unliteral=True)
def overload_series_to_frame(S, name=None):
    gol__qpro = (
        "Series.to_frame(): output column name should be known at compile time. Set 'name' to a constant value."
        )
    if is_overload_none(name):
        if is_literal_type(S.name_typ):
            bjm__gzgvn = get_literal_value(S.name_typ)
        else:
            raise_bodo_error(gol__qpro)
    elif is_literal_type(name):
        bjm__gzgvn = get_literal_value(name)
    else:
        raise_bodo_error(gol__qpro)
    bjm__gzgvn = 0 if bjm__gzgvn is None else bjm__gzgvn

    def impl(S, name=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        return bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,), index,
            (bjm__gzgvn,))
    return impl


@overload_method(SeriesType, 'keys', inline='always', no_unliteral=True)
def overload_series_keys(S):

    def impl(S):
        return bodo.hiframes.pd_series_ext.get_series_index(S)
    return impl
