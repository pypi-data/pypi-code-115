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
    return lambda s: bodo.hiframes.pd_series_ext.get_series_data(s)


@overload_attribute(SeriesType, 'dtype', inline='always')
def overload_series_dtype(s):
    if s.dtype == bodo.string_type:
        raise BodoError('Series.dtype not supported for string Series yet')
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
    if isinstance(S.dtype, types.Float):

        def impl_float(S):
            ljq__drsl = list()
            for heg__sudp in range(len(S)):
                ljq__drsl.append(S.iat[heg__sudp])
            return ljq__drsl
        return impl_float

    def impl(S):
        ljq__drsl = list()
        for heg__sudp in range(len(S)):
            if bodo.libs.array_kernels.isna(S.values, heg__sudp):
                raise ValueError(
                    'Series.to_list(): Not supported for NA values with non-float dtypes'
                    )
            ljq__drsl.append(S.iat[heg__sudp])
        return ljq__drsl
    return impl


@overload_method(SeriesType, 'to_numpy', inline='always', no_unliteral=True)
def overload_series_to_numpy(S, dtype=None, copy=False, na_value=None):
    nyr__qiz = dict(dtype=dtype, copy=copy, na_value=na_value)
    bpal__ets = dict(dtype=None, copy=False, na_value=None)
    check_unsupported_args('Series.to_numpy', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')

    def impl(S, dtype=None, copy=False, na_value=None):
        return S.values
    return impl


@overload_method(SeriesType, 'reset_index', inline='always', no_unliteral=True)
def overload_series_reset_index(S, level=None, drop=False, name=None,
    inplace=False):
    nyr__qiz = dict(name=name, inplace=inplace)
    bpal__ets = dict(name=None, inplace=False)
    check_unsupported_args('Series.reset_index', nyr__qiz, bpal__ets,
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
    ixmmy__jzbb = get_name_literal(S.index.name_typ, True, series_name)
    columns = [ixmmy__jzbb, series_name]
    vsmz__lhbj = (
        'def _impl(S, level=None, drop=False, name=None, inplace=False):\n')
    vsmz__lhbj += '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    vsmz__lhbj += """    index = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(S))
"""
    vsmz__lhbj += """    df_index = bodo.hiframes.pd_index_ext.init_range_index(0, len(S), 1, None)
"""
    vsmz__lhbj += '    col_var = {}\n'.format(gen_const_tup(columns))
    vsmz__lhbj += """    return bodo.hiframes.pd_dataframe_ext.init_dataframe((index, arr), df_index, col_var)
"""
    jhbwu__gfo = {}
    exec(vsmz__lhbj, {'bodo': bodo}, jhbwu__gfo)
    trzbn__kdp = jhbwu__gfo['_impl']
    return trzbn__kdp


@overload_method(SeriesType, 'isna', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'isnull', inline='always', no_unliteral=True)
def overload_series_isna(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        gxi__wyxo = bodo.libs.array_ops.array_op_isna(arr)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index, name)
    return impl


@overload_method(SeriesType, 'round', inline='always', no_unliteral=True)
def overload_series_round(S, decimals=0):

    def impl(S, decimals=0):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        numba.parfors.parfor.init_prange()
        n = len(arr)
        gxi__wyxo = bodo.utils.utils.alloc_type(n, arr, (-1,))
        for heg__sudp in numba.parfors.parfor.internal_prange(n):
            if pd.isna(arr[heg__sudp]):
                bodo.libs.array_kernels.setna(gxi__wyxo, heg__sudp)
            else:
                gxi__wyxo[heg__sudp] = np.round(arr[heg__sudp], decimals)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index, name)
    return impl


@overload_method(SeriesType, 'sum', inline='always', no_unliteral=True)
def overload_series_sum(S, axis=None, skipna=True, level=None, numeric_only
    =None, min_count=0):
    nyr__qiz = dict(level=level, numeric_only=numeric_only)
    bpal__ets = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.sum', nyr__qiz, bpal__ets, package_name=
        'pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.sum(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.sum(): skipna argument must be a boolean')
    if not is_overload_int(min_count):
        raise BodoError('Series.sum(): min_count argument must be an integer')

    def impl(S, axis=None, skipna=True, level=None, numeric_only=None,
        min_count=0):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_sum(arr, skipna, min_count)
    return impl


@overload_method(SeriesType, 'prod', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'product', inline='always', no_unliteral=True)
def overload_series_prod(S, axis=None, skipna=True, level=None,
    numeric_only=None, min_count=0):
    nyr__qiz = dict(level=level, numeric_only=numeric_only)
    bpal__ets = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.product', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.product(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.product(): skipna argument must be a boolean')

    def impl(S, axis=None, skipna=True, level=None, numeric_only=None,
        min_count=0):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_prod(arr, skipna, min_count)
    return impl


@overload_method(SeriesType, 'any', inline='always', no_unliteral=True)
def overload_series_any(S, axis=0, bool_only=None, skipna=True, level=None):
    nyr__qiz = dict(axis=axis, bool_only=bool_only, skipna=skipna, level=level)
    bpal__ets = dict(axis=0, bool_only=None, skipna=True, level=None)
    check_unsupported_args('Series.any', nyr__qiz, bpal__ets, package_name=
        'pandas', module_name='Series')

    def impl(S, axis=0, bool_only=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        nas__ybqmi = 0
        for heg__sudp in numba.parfors.parfor.internal_prange(len(A)):
            zxrjz__aiudx = 0
            if not bodo.libs.array_kernels.isna(A, heg__sudp):
                zxrjz__aiudx = int(A[heg__sudp])
            nas__ybqmi += zxrjz__aiudx
        return nas__ybqmi != 0
    return impl


@overload_method(SeriesType, 'equals', inline='always', no_unliteral=True)
def overload_series_equals(S, other):
    if not isinstance(other, SeriesType):
        raise BodoError("Series.equals() 'other' must be a Series")
    if isinstance(S.data, bodo.ArrayItemArrayType):
        raise BodoError(
            'Series.equals() not supported for Series where each element is an array or list'
            )
    if S.data != other.data:
        return lambda S, other: False

    def impl(S, other):
        lfuqm__fjrxp = bodo.hiframes.pd_series_ext.get_series_data(S)
        mcnsn__eibw = bodo.hiframes.pd_series_ext.get_series_data(other)
        numba.parfors.parfor.init_prange()
        nas__ybqmi = 0
        for heg__sudp in numba.parfors.parfor.internal_prange(len(lfuqm__fjrxp)
            ):
            zxrjz__aiudx = 0
            bpjls__odn = bodo.libs.array_kernels.isna(lfuqm__fjrxp, heg__sudp)
            eca__hdto = bodo.libs.array_kernels.isna(mcnsn__eibw, heg__sudp)
            if bpjls__odn and not eca__hdto or not bpjls__odn and eca__hdto:
                zxrjz__aiudx = 1
            elif not bpjls__odn:
                if lfuqm__fjrxp[heg__sudp] != mcnsn__eibw[heg__sudp]:
                    zxrjz__aiudx = 1
            nas__ybqmi += zxrjz__aiudx
        return nas__ybqmi == 0
    return impl


@overload_method(SeriesType, 'all', inline='always', no_unliteral=True)
def overload_series_all(S, axis=0, bool_only=None, skipna=True, level=None):
    nyr__qiz = dict(axis=axis, bool_only=bool_only, skipna=skipna, level=level)
    bpal__ets = dict(axis=0, bool_only=None, skipna=True, level=None)
    check_unsupported_args('Series.all', nyr__qiz, bpal__ets, package_name=
        'pandas', module_name='Series')

    def impl(S, axis=0, bool_only=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        nas__ybqmi = 0
        for heg__sudp in numba.parfors.parfor.internal_prange(len(A)):
            zxrjz__aiudx = 0
            if not bodo.libs.array_kernels.isna(A, heg__sudp):
                zxrjz__aiudx = int(not A[heg__sudp])
            nas__ybqmi += zxrjz__aiudx
        return nas__ybqmi == 0
    return impl


@overload_method(SeriesType, 'mad', inline='always', no_unliteral=True)
def overload_series_mad(S, axis=None, skipna=True, level=None):
    nyr__qiz = dict(level=level)
    bpal__ets = dict(level=None)
    check_unsupported_args('Series.mad', nyr__qiz, bpal__ets, package_name=
        'pandas', module_name='Series')
    if not is_overload_bool(skipna):
        raise BodoError("Series.mad(): 'skipna' argument must be a boolean")
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.mad(): axis argument not supported')
    jopf__wuz = types.float64
    odtkz__dag = types.float64
    if S.dtype == types.float32:
        jopf__wuz = types.float32
        odtkz__dag = types.float32
    lhi__fuk = jopf__wuz(0)
    ldmc__jfbjp = odtkz__dag(0)
    hbldg__fuvik = odtkz__dag(1)

    def impl(S, axis=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        poaz__wan = lhi__fuk
        nas__ybqmi = ldmc__jfbjp
        for heg__sudp in numba.parfors.parfor.internal_prange(len(A)):
            zxrjz__aiudx = lhi__fuk
            gloa__fpc = ldmc__jfbjp
            if not bodo.libs.array_kernels.isna(A, heg__sudp) or not skipna:
                zxrjz__aiudx = A[heg__sudp]
                gloa__fpc = hbldg__fuvik
            poaz__wan += zxrjz__aiudx
            nas__ybqmi += gloa__fpc
        mpwd__tge = bodo.hiframes.series_kernels._mean_handle_nan(poaz__wan,
            nas__ybqmi)
        nyhfk__kjfyn = lhi__fuk
        for heg__sudp in numba.parfors.parfor.internal_prange(len(A)):
            zxrjz__aiudx = lhi__fuk
            if not bodo.libs.array_kernels.isna(A, heg__sudp) or not skipna:
                zxrjz__aiudx = abs(A[heg__sudp] - mpwd__tge)
            nyhfk__kjfyn += zxrjz__aiudx
        zgah__qyn = bodo.hiframes.series_kernels._mean_handle_nan(nyhfk__kjfyn,
            nas__ybqmi)
        return zgah__qyn
    return impl


@overload_method(SeriesType, 'mean', inline='always', no_unliteral=True)
def overload_series_mean(S, axis=None, skipna=None, level=None,
    numeric_only=None):
    if not isinstance(S.dtype, types.Number) and S.dtype not in [bodo.
        datetime64ns, types.bool_]:
        raise BodoError(f"Series.mean(): Series with type '{S}' not supported")
    nyr__qiz = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    bpal__ets = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.mean', nyr__qiz, bpal__ets, package_name
        ='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.mean(): axis argument not supported')

    def impl(S, axis=None, skipna=None, level=None, numeric_only=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_mean(arr)
    return impl


@overload_method(SeriesType, 'sem', inline='always', no_unliteral=True)
def overload_series_sem(S, axis=None, skipna=True, level=None, ddof=1,
    numeric_only=None):
    nyr__qiz = dict(level=level, numeric_only=numeric_only)
    bpal__ets = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.sem', nyr__qiz, bpal__ets, package_name=
        'pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.sem(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.sem(): skipna argument must be a boolean')
    if not is_overload_int(ddof):
        raise BodoError('Series.sem(): ddof argument must be an integer')

    def impl(S, axis=None, skipna=True, level=None, ddof=1, numeric_only=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        udopu__frilc = 0
        dukwd__lrbx = 0
        nas__ybqmi = 0
        for heg__sudp in numba.parfors.parfor.internal_prange(len(A)):
            zxrjz__aiudx = 0
            gloa__fpc = 0
            if not bodo.libs.array_kernels.isna(A, heg__sudp) or not skipna:
                zxrjz__aiudx = A[heg__sudp]
                gloa__fpc = 1
            udopu__frilc += zxrjz__aiudx
            dukwd__lrbx += zxrjz__aiudx * zxrjz__aiudx
            nas__ybqmi += gloa__fpc
        vwwy__pbew = bodo.hiframes.series_kernels._compute_var_nan_count_ddof(
            udopu__frilc, dukwd__lrbx, nas__ybqmi, ddof)
        igz__xkvv = bodo.hiframes.series_kernels._sem_handle_nan(vwwy__pbew,
            nas__ybqmi)
        return igz__xkvv
    return impl


@overload_method(SeriesType, 'kurt', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'kurtosis', inline='always', no_unliteral=True)
def overload_series_kurt(S, axis=None, skipna=True, level=None,
    numeric_only=None):
    nyr__qiz = dict(level=level, numeric_only=numeric_only)
    bpal__ets = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.kurtosis', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.kurtosis(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError(
            "Series.kurtosis(): 'skipna' argument must be a boolean")

    def impl(S, axis=None, skipna=True, level=None, numeric_only=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        udopu__frilc = 0.0
        dukwd__lrbx = 0.0
        kef__hcrpu = 0.0
        ixfkl__gsi = 0.0
        nas__ybqmi = 0
        for heg__sudp in numba.parfors.parfor.internal_prange(len(A)):
            zxrjz__aiudx = 0.0
            gloa__fpc = 0
            if not bodo.libs.array_kernels.isna(A, heg__sudp) or not skipna:
                zxrjz__aiudx = np.float64(A[heg__sudp])
                gloa__fpc = 1
            udopu__frilc += zxrjz__aiudx
            dukwd__lrbx += zxrjz__aiudx ** 2
            kef__hcrpu += zxrjz__aiudx ** 3
            ixfkl__gsi += zxrjz__aiudx ** 4
            nas__ybqmi += gloa__fpc
        vwwy__pbew = bodo.hiframes.series_kernels.compute_kurt(udopu__frilc,
            dukwd__lrbx, kef__hcrpu, ixfkl__gsi, nas__ybqmi)
        return vwwy__pbew
    return impl


@overload_method(SeriesType, 'skew', inline='always', no_unliteral=True)
def overload_series_skew(S, axis=None, skipna=True, level=None,
    numeric_only=None):
    nyr__qiz = dict(level=level, numeric_only=numeric_only)
    bpal__ets = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.skew', nyr__qiz, bpal__ets, package_name
        ='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.skew(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.skew(): skipna argument must be a boolean')

    def impl(S, axis=None, skipna=True, level=None, numeric_only=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        udopu__frilc = 0.0
        dukwd__lrbx = 0.0
        kef__hcrpu = 0.0
        nas__ybqmi = 0
        for heg__sudp in numba.parfors.parfor.internal_prange(len(A)):
            zxrjz__aiudx = 0.0
            gloa__fpc = 0
            if not bodo.libs.array_kernels.isna(A, heg__sudp) or not skipna:
                zxrjz__aiudx = np.float64(A[heg__sudp])
                gloa__fpc = 1
            udopu__frilc += zxrjz__aiudx
            dukwd__lrbx += zxrjz__aiudx ** 2
            kef__hcrpu += zxrjz__aiudx ** 3
            nas__ybqmi += gloa__fpc
        vwwy__pbew = bodo.hiframes.series_kernels.compute_skew(udopu__frilc,
            dukwd__lrbx, kef__hcrpu, nas__ybqmi)
        return vwwy__pbew
    return impl


@overload_method(SeriesType, 'var', inline='always', no_unliteral=True)
def overload_series_var(S, axis=None, skipna=True, level=None, ddof=1,
    numeric_only=None):
    nyr__qiz = dict(level=level, numeric_only=numeric_only)
    bpal__ets = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.var', nyr__qiz, bpal__ets, package_name=
        'pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.var(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.var(): skipna argument must be a boolean')
    if not is_overload_int(ddof):
        raise BodoError('Series.var(): ddof argument must be an integer')

    def impl(S, axis=None, skipna=True, level=None, ddof=1, numeric_only=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_var(arr, skipna, ddof)
    return impl


@overload_method(SeriesType, 'std', inline='always', no_unliteral=True)
def overload_series_std(S, axis=None, skipna=True, level=None, ddof=1,
    numeric_only=None):
    nyr__qiz = dict(level=level, numeric_only=numeric_only)
    bpal__ets = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.std', nyr__qiz, bpal__ets, package_name=
        'pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.std(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.std(): skipna argument must be a boolean')
    if not is_overload_int(ddof):
        raise BodoError('Series.std(): ddof argument must be an integer')

    def impl(S, axis=None, skipna=True, level=None, ddof=1, numeric_only=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_std(arr, skipna, ddof)
    return impl


@overload_method(SeriesType, 'dot', inline='always', no_unliteral=True)
def overload_series_dot(S, other):

    def impl(S, other):
        lfuqm__fjrxp = bodo.hiframes.pd_series_ext.get_series_data(S)
        mcnsn__eibw = bodo.hiframes.pd_series_ext.get_series_data(other)
        numba.parfors.parfor.init_prange()
        kztvs__ldmgz = 0
        for heg__sudp in numba.parfors.parfor.internal_prange(len(lfuqm__fjrxp)
            ):
            saqgp__ebdu = lfuqm__fjrxp[heg__sudp]
            ggk__qqh = mcnsn__eibw[heg__sudp]
            kztvs__ldmgz += saqgp__ebdu * ggk__qqh
        return kztvs__ldmgz
    return impl


@overload_method(SeriesType, 'cumsum', inline='always', no_unliteral=True)
def overload_series_cumsum(S, axis=None, skipna=True):
    nyr__qiz = dict(skipna=skipna)
    bpal__ets = dict(skipna=True)
    check_unsupported_args('Series.cumsum', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.cumsum(): axis argument not supported')

    def impl(S, axis=None, skipna=True):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(A.cumsum(), index, name)
    return impl


@overload_method(SeriesType, 'cumprod', inline='always', no_unliteral=True)
def overload_series_cumprod(S, axis=None, skipna=True):
    nyr__qiz = dict(skipna=skipna)
    bpal__ets = dict(skipna=True)
    check_unsupported_args('Series.cumprod', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.cumprod(): axis argument not supported')

    def impl(S, axis=None, skipna=True):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(A.cumprod(), index, name
            )
    return impl


@overload_method(SeriesType, 'cummin', inline='always', no_unliteral=True)
def overload_series_cummin(S, axis=None, skipna=True):
    nyr__qiz = dict(skipna=skipna)
    bpal__ets = dict(skipna=True)
    check_unsupported_args('Series.cummin', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.cummin(): axis argument not supported')

    def impl(S, axis=None, skipna=True):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(bodo.libs.
            array_kernels.cummin(arr), index, name)
    return impl


@overload_method(SeriesType, 'cummax', inline='always', no_unliteral=True)
def overload_series_cummax(S, axis=None, skipna=True):
    nyr__qiz = dict(skipna=skipna)
    bpal__ets = dict(skipna=True)
    check_unsupported_args('Series.cummax', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.cummax(): axis argument not supported')

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
    nyr__qiz = dict(copy=copy, inplace=inplace, level=level, errors=errors)
    bpal__ets = dict(copy=True, inplace=False, level=None, errors='ignore')
    check_unsupported_args('Series.rename', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')

    def impl(S, index=None, axis=None, copy=True, inplace=False, level=None,
        errors='ignore'):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        myf__ixa = bodo.hiframes.pd_series_ext.get_series_index(S)
        return bodo.hiframes.pd_series_ext.init_series(A, myf__ixa, index)
    return impl


@overload_method(SeriesType, 'rename_axis', inline='always', no_unliteral=True)
def overload_series_rename_axis(S, mapper=None, index=None, columns=None,
    axis=None, copy=True, inplace=False):
    nyr__qiz = dict(index=index, columns=columns, axis=axis, copy=copy,
        inplace=inplace)
    bpal__ets = dict(index=None, columns=None, axis=None, copy=True,
        inplace=False)
    check_unsupported_args('Series.rename_axis', nyr__qiz, bpal__ets,
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

    def impl(S):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(np.abs(A), index, name)
    return impl


@overload_method(SeriesType, 'count', no_unliteral=True)
def overload_series_count(S, level=None):
    nyr__qiz = dict(level=level)
    bpal__ets = dict(level=None)
    check_unsupported_args('Series.count', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')

    def impl(S, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_count(A)
    return impl


@overload_method(SeriesType, 'corr', inline='always', no_unliteral=True)
def overload_series_corr(S, other, method='pearson', min_periods=None):
    nyr__qiz = dict(method=method, min_periods=min_periods)
    bpal__ets = dict(method='pearson', min_periods=None)
    check_unsupported_args('Series.corr', nyr__qiz, bpal__ets, package_name
        ='pandas', module_name='Series')

    def impl(S, other, method='pearson', min_periods=None):
        n = S.count()
        nkiu__qaubh = S.sum()
        atdri__fpj = other.sum()
        a = n * (S * other).sum() - nkiu__qaubh * atdri__fpj
        rcsk__zqmni = n * (S ** 2).sum() - nkiu__qaubh ** 2
        lyhgi__ooek = n * (other ** 2).sum() - atdri__fpj ** 2
        return a / np.sqrt(rcsk__zqmni * lyhgi__ooek)
    return impl


@overload_method(SeriesType, 'cov', inline='always', no_unliteral=True)
def overload_series_cov(S, other, min_periods=None, ddof=1):
    nyr__qiz = dict(min_periods=min_periods)
    bpal__ets = dict(min_periods=None)
    check_unsupported_args('Series.cov', nyr__qiz, bpal__ets, package_name=
        'pandas', module_name='Series')

    def impl(S, other, min_periods=None, ddof=1):
        nkiu__qaubh = S.mean()
        atdri__fpj = other.mean()
        okiv__gqkm = ((S - nkiu__qaubh) * (other - atdri__fpj)).sum()
        N = np.float64(S.count() - ddof)
        nonzero_len = S.count() * other.count()
        return _series_cov_helper(okiv__gqkm, N, nonzero_len)
    return impl


def _series_cov_helper(sum_val, N, nonzero_len):
    return


@overload(_series_cov_helper, no_unliteral=True)
def _overload_series_cov_helper(sum_val, N, nonzero_len):

    def impl(sum_val, N, nonzero_len):
        if not nonzero_len:
            return np.nan
        if N <= 0.0:
            ozt__ypfpr = np.sign(sum_val)
            return np.inf * ozt__ypfpr
        return sum_val / N
    return impl


@overload_method(SeriesType, 'min', inline='always', no_unliteral=True)
def overload_series_min(S, axis=None, skipna=None, level=None, numeric_only
    =None):
    nyr__qiz = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    bpal__ets = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.min', nyr__qiz, bpal__ets, package_name=
        'pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.min(): axis argument not supported')
    if isinstance(S.dtype, PDCategoricalDtype):
        if not S.dtype.ordered:
            raise BodoError(
                'Series.min(): only ordered categoricals are possible')

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
    nyr__qiz = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    bpal__ets = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.max', nyr__qiz, bpal__ets, package_name=
        'pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.max(): axis argument not supported')
    if isinstance(S.dtype, PDCategoricalDtype):
        if not S.dtype.ordered:
            raise BodoError(
                'Series.max(): only ordered categoricals are possible')

    def impl(S, axis=None, skipna=None, level=None, numeric_only=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_max(arr)
    return impl


@overload_method(SeriesType, 'idxmin', inline='always', no_unliteral=True)
def overload_series_idxmin(S, axis=0, skipna=True):
    nyr__qiz = dict(axis=axis, skipna=skipna)
    bpal__ets = dict(axis=0, skipna=True)
    check_unsupported_args('Series.idxmin', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
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
    nyr__qiz = dict(axis=axis, skipna=skipna)
    bpal__ets = dict(axis=0, skipna=True)
    check_unsupported_args('Series.idxmax', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
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
    return lambda S: bodo.libs.array_kernels.series_monotonicity(bodo.
        hiframes.pd_series_ext.get_series_data(S), 1)


@overload_attribute(SeriesType, 'is_monotonic_decreasing', inline='always')
def overload_series_is_monotonic_decreasing(S):
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
    nyr__qiz = dict(level=level, numeric_only=numeric_only)
    bpal__ets = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.median', nyr__qiz, bpal__ets,
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
        pwo__jmjfa = arr[:n]
        jjrae__jtreo = index[:n]
        return bodo.hiframes.pd_series_ext.init_series(pwo__jmjfa,
            jjrae__jtreo, name)
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
        paiy__oanhw = tail_slice(len(S), n)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        pwo__jmjfa = arr[paiy__oanhw:]
        jjrae__jtreo = index[paiy__oanhw:]
        return bodo.hiframes.pd_series_ext.init_series(pwo__jmjfa,
            jjrae__jtreo, name)
    return impl


@overload_method(SeriesType, 'first', inline='always', no_unliteral=True)
def overload_series_first(S, offset):
    bjlf__yibfq = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if types.unliteral(offset) not in bjlf__yibfq:
        raise BodoError(
            "Series.first(): 'offset' must be a string or a DateOffset")

    def impl(S, offset):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        if len(index):
            wev__jnxx = index[0]
            ribx__ylhls = (bodo.libs.array_kernels.
                get_valid_entries_from_date_offset(index, offset, wev__jnxx,
                False))
        else:
            ribx__ylhls = 0
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        pwo__jmjfa = arr[:ribx__ylhls]
        jjrae__jtreo = index[:ribx__ylhls]
        return bodo.hiframes.pd_series_ext.init_series(pwo__jmjfa,
            jjrae__jtreo, name)
    return impl


@overload_method(SeriesType, 'last', inline='always', no_unliteral=True)
def overload_series_last(S, offset):
    bjlf__yibfq = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if types.unliteral(offset) not in bjlf__yibfq:
        raise BodoError(
            "Series.last(): 'offset' must be a string or a DateOffset")

    def impl(S, offset):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        if len(index):
            yyhk__xjs = index[-1]
            ribx__ylhls = (bodo.libs.array_kernels.
                get_valid_entries_from_date_offset(index, offset, yyhk__xjs,
                True))
        else:
            ribx__ylhls = 0
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        pwo__jmjfa = arr[len(arr) - ribx__ylhls:]
        jjrae__jtreo = index[len(arr) - ribx__ylhls:]
        return bodo.hiframes.pd_series_ext.init_series(pwo__jmjfa,
            jjrae__jtreo, name)
    return impl


@overload_method(SeriesType, 'first_valid_index', inline='always',
    no_unliteral=True)
def overload_series_first_valid_index(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        yivy__mhpn = bodo.utils.conversion.index_to_array(index)
        vrndi__pgbvg, ongaq__eaqj = (bodo.libs.array_kernels.
            first_last_valid_index(arr, yivy__mhpn))
        return ongaq__eaqj if vrndi__pgbvg else None
    return impl


@overload_method(SeriesType, 'last_valid_index', inline='always',
    no_unliteral=True)
def overload_series_last_valid_index(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        yivy__mhpn = bodo.utils.conversion.index_to_array(index)
        vrndi__pgbvg, ongaq__eaqj = (bodo.libs.array_kernels.
            first_last_valid_index(arr, yivy__mhpn, False))
        return ongaq__eaqj if vrndi__pgbvg else None
    return impl


@overload_method(SeriesType, 'nlargest', inline='always', no_unliteral=True)
def overload_series_nlargest(S, n=5, keep='first'):
    nyr__qiz = dict(keep=keep)
    bpal__ets = dict(keep='first')
    check_unsupported_args('Series.nlargest', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
    if not is_overload_int(n):
        raise BodoError('Series.nlargest(): n argument must be an integer')

    def impl(S, n=5, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        yivy__mhpn = bodo.utils.conversion.coerce_to_ndarray(index)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        gxi__wyxo, qwsv__uuj = bodo.libs.array_kernels.nlargest(arr,
            yivy__mhpn, n, True, bodo.hiframes.series_kernels.gt_f)
        jmov__fhwwl = bodo.utils.conversion.convert_to_index(qwsv__uuj)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
            jmov__fhwwl, name)
    return impl


@overload_method(SeriesType, 'nsmallest', inline='always', no_unliteral=True)
def overload_series_nsmallest(S, n=5, keep='first'):
    nyr__qiz = dict(keep=keep)
    bpal__ets = dict(keep='first')
    check_unsupported_args('Series.nsmallest', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
    if not is_overload_int(n):
        raise BodoError('Series.nsmallest(): n argument must be an integer')

    def impl(S, n=5, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        yivy__mhpn = bodo.utils.conversion.coerce_to_ndarray(index)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        gxi__wyxo, qwsv__uuj = bodo.libs.array_kernels.nlargest(arr,
            yivy__mhpn, n, False, bodo.hiframes.series_kernels.lt_f)
        jmov__fhwwl = bodo.utils.conversion.convert_to_index(qwsv__uuj)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
            jmov__fhwwl, name)
    return impl


@overload_method(SeriesType, 'notnull', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'notna', inline='always', no_unliteral=True)
def overload_series_notna(S):
    return lambda S: S.isna() == False


@overload_method(SeriesType, 'astype', inline='always', no_unliteral=True)
def overload_series_astype(S, dtype, copy=True, errors='raise',
    _bodo_nan_to_str=True):
    nyr__qiz = dict(errors=errors)
    bpal__ets = dict(errors='raise')
    check_unsupported_args('Series.astype', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
    if dtype == types.unicode_type:
        raise_bodo_error(
            "Series.astype(): 'dtype' when passed as string must be a constant value"
            )

    def impl(S, dtype, copy=True, errors='raise', _bodo_nan_to_str=True):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        gxi__wyxo = bodo.utils.conversion.fix_arr_dtype(arr, dtype, copy,
            nan_to_str=_bodo_nan_to_str, from_series=True)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index, name)
    return impl


@overload_method(SeriesType, 'take', inline='always', no_unliteral=True)
def overload_series_take(S, indices, axis=0, is_copy=True):
    nyr__qiz = dict(axis=axis, is_copy=is_copy)
    bpal__ets = dict(axis=0, is_copy=True)
    check_unsupported_args('Series.take', nyr__qiz, bpal__ets, package_name
        ='pandas', module_name='Series')
    if not (is_iterable_type(indices) and isinstance(indices.dtype, types.
        Integer)):
        raise BodoError(
            f"Series.take() 'indices' must be an array-like and contain integers. Found type {indices}."
            )

    def impl(S, indices, axis=0, is_copy=True):
        sab__ebvb = bodo.utils.conversion.coerce_to_ndarray(indices)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(arr[sab__ebvb],
            index[sab__ebvb], name)
    return impl


@overload_method(SeriesType, 'argsort', inline='always', no_unliteral=True)
def overload_series_argsort(S, axis=0, kind='quicksort', order=None):
    nyr__qiz = dict(axis=axis, kind=kind, order=order)
    bpal__ets = dict(axis=0, kind='quicksort', order=None)
    check_unsupported_args('Series.argsort', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')

    def impl(S, axis=0, kind='quicksort', order=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        n = len(arr)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        lgbyx__tjaw = S.notna().values
        if not lgbyx__tjaw.all():
            gxi__wyxo = np.full(n, -1, np.int64)
            gxi__wyxo[lgbyx__tjaw] = argsort(arr[lgbyx__tjaw])
        else:
            gxi__wyxo = argsort(arr)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index, name)
    return impl


@overload_method(SeriesType, 'sort_index', inline='always', no_unliteral=True)
def overload_series_sort_index(S, axis=0, level=None, ascending=True,
    inplace=False, kind='quicksort', na_position='last', sort_remaining=
    True, ignore_index=False, key=None):
    nyr__qiz = dict(axis=axis, level=level, inplace=inplace, kind=kind,
        sort_remaining=sort_remaining, ignore_index=ignore_index, key=key)
    bpal__ets = dict(axis=0, level=None, inplace=False, kind='quicksort',
        sort_remaining=True, ignore_index=False, key=None)
    check_unsupported_args('Series.sort_index', nyr__qiz, bpal__ets,
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
        iayn__mxw = bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,),
            index, ('$_bodo_col3_',))
        mmu__oyo = iayn__mxw.sort_index(ascending=ascending, inplace=
            inplace, na_position=na_position)
        gxi__wyxo = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(mmu__oyo,
            0)
        jmov__fhwwl = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(
            mmu__oyo)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
            jmov__fhwwl, name)
    return impl


@overload_method(SeriesType, 'sort_values', inline='always', no_unliteral=True)
def overload_series_sort_values(S, axis=0, ascending=True, inplace=False,
    kind='quicksort', na_position='last', ignore_index=False, key=None):
    nyr__qiz = dict(axis=axis, inplace=inplace, kind=kind, ignore_index=
        ignore_index, key=key)
    bpal__ets = dict(axis=0, inplace=False, kind='quicksort', ignore_index=
        False, key=None)
    check_unsupported_args('Series.sort_values', nyr__qiz, bpal__ets,
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
        iayn__mxw = bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,),
            index, ('$_bodo_col_',))
        mmu__oyo = iayn__mxw.sort_values(['$_bodo_col_'], ascending=
            ascending, inplace=inplace, na_position=na_position)
        gxi__wyxo = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(mmu__oyo,
            0)
        jmov__fhwwl = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(
            mmu__oyo)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
            jmov__fhwwl, name)
    return impl


def get_bin_inds(bins, arr):
    return arr


@overload(get_bin_inds, inline='always', no_unliteral=True)
def overload_get_bin_inds(bins, arr, is_nullable=True, include_lowest=True):
    assert is_overload_constant_bool(is_nullable)
    nqul__wia = is_overload_true(is_nullable)
    vsmz__lhbj = (
        'def impl(bins, arr, is_nullable=True, include_lowest=True):\n')
    vsmz__lhbj += '  numba.parfors.parfor.init_prange()\n'
    vsmz__lhbj += '  n = len(arr)\n'
    if nqul__wia:
        vsmz__lhbj += (
            '  out_arr = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n')
    else:
        vsmz__lhbj += '  out_arr = np.empty(n, np.int64)\n'
    vsmz__lhbj += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    vsmz__lhbj += '    if bodo.libs.array_kernels.isna(arr, i):\n'
    if nqul__wia:
        vsmz__lhbj += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    else:
        vsmz__lhbj += '      out_arr[i] = -1\n'
    vsmz__lhbj += '      continue\n'
    vsmz__lhbj += '    val = arr[i]\n'
    vsmz__lhbj += '    if include_lowest and val == bins[0]:\n'
    vsmz__lhbj += '      ind = 1\n'
    vsmz__lhbj += '    else:\n'
    vsmz__lhbj += '      ind = np.searchsorted(bins, val)\n'
    vsmz__lhbj += '    if ind == 0 or ind == len(bins):\n'
    if nqul__wia:
        vsmz__lhbj += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    else:
        vsmz__lhbj += '      out_arr[i] = -1\n'
    vsmz__lhbj += '    else:\n'
    vsmz__lhbj += '      out_arr[i] = ind - 1\n'
    vsmz__lhbj += '  return out_arr\n'
    jhbwu__gfo = {}
    exec(vsmz__lhbj, {'bodo': bodo, 'np': np, 'numba': numba}, jhbwu__gfo)
    impl = jhbwu__gfo['impl']
    return impl


@register_jitable
def _round_frac(x, precision: int):
    if not np.isfinite(x) or x == 0:
        return x
    else:
        jkeuw__bvbe, zonf__ijl = np.divmod(x, 1)
        if jkeuw__bvbe == 0:
            hzsy__xxp = -int(np.floor(np.log10(abs(zonf__ijl)))
                ) - 1 + precision
        else:
            hzsy__xxp = precision
        return np.around(x, hzsy__xxp)


@register_jitable
def _infer_precision(base_precision: int, bins) ->int:
    for precision in range(base_precision, 20):
        rwomb__uch = np.array([_round_frac(b, precision) for b in bins])
        if len(np.unique(rwomb__uch)) == len(bins):
            return precision
    return base_precision


def get_bin_labels(bins):
    pass


@overload(get_bin_labels, no_unliteral=True)
def overload_get_bin_labels(bins, right=True, include_lowest=True):
    dtype = np.float64 if isinstance(bins.dtype, types.Integer) else bins.dtype
    if dtype == bodo.datetime64ns:
        fblit__fka = bodo.timedelta64ns(1)

        def impl_dt64(bins, right=True, include_lowest=True):
            vfo__kjxh = bins.copy()
            if right and include_lowest:
                vfo__kjxh[0] = vfo__kjxh[0] - fblit__fka
            rpq__gpud = bodo.libs.interval_arr_ext.init_interval_array(
                vfo__kjxh[:-1], vfo__kjxh[1:])
            return bodo.hiframes.pd_index_ext.init_interval_index(rpq__gpud,
                None)
        return impl_dt64

    def impl(bins, right=True, include_lowest=True):
        base_precision = 3
        precision = _infer_precision(base_precision, bins)
        vfo__kjxh = np.array([_round_frac(b, precision) for b in bins],
            dtype=dtype)
        if right and include_lowest:
            vfo__kjxh[0] = vfo__kjxh[0] - 10.0 ** -precision
        rpq__gpud = bodo.libs.interval_arr_ext.init_interval_array(vfo__kjxh
            [:-1], vfo__kjxh[1:])
        return bodo.hiframes.pd_index_ext.init_interval_index(rpq__gpud, None)
    return impl


def get_output_bin_counts(count_series, nbins):
    pass


@overload(get_output_bin_counts, no_unliteral=True)
def overload_get_output_bin_counts(count_series, nbins):

    def impl(count_series, nbins):
        usj__xxkhr = bodo.hiframes.pd_series_ext.get_series_data(count_series)
        plt__alhu = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(count_series))
        gxi__wyxo = np.zeros(nbins, np.int64)
        for heg__sudp in range(len(usj__xxkhr)):
            gxi__wyxo[plt__alhu[heg__sudp]] = usj__xxkhr[heg__sudp]
        return gxi__wyxo
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
            rtkri__qyiak = (max_val - min_val) * 0.001
            if right:
                bins[0] -= rtkri__qyiak
            else:
                bins[-1] += rtkri__qyiak
        return bins
    return impl


@overload_method(SeriesType, 'value_counts', inline='always', no_unliteral=True
    )
def overload_series_value_counts(S, normalize=False, sort=True, ascending=
    False, bins=None, dropna=True, _index_name=None):
    nyr__qiz = dict(dropna=dropna)
    bpal__ets = dict(dropna=True)
    check_unsupported_args('Series.value_counts', nyr__qiz, bpal__ets,
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
    wcvl__lgrhv = not is_overload_none(bins)
    vsmz__lhbj = 'def impl(\n'
    vsmz__lhbj += '    S,\n'
    vsmz__lhbj += '    normalize=False,\n'
    vsmz__lhbj += '    sort=True,\n'
    vsmz__lhbj += '    ascending=False,\n'
    vsmz__lhbj += '    bins=None,\n'
    vsmz__lhbj += '    dropna=True,\n'
    vsmz__lhbj += (
        '    _index_name=None,  # bodo argument. See groupby.value_counts\n')
    vsmz__lhbj += '):\n'
    vsmz__lhbj += '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    vsmz__lhbj += (
        '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
    vsmz__lhbj += '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    if wcvl__lgrhv:
        vsmz__lhbj += '    right = True\n'
        vsmz__lhbj += _gen_bins_handling(bins, S.dtype)
        vsmz__lhbj += '    arr = get_bin_inds(bins, arr)\n'
    vsmz__lhbj += (
        '    in_df = bodo.hiframes.pd_dataframe_ext.init_dataframe(\n')
    vsmz__lhbj += "        (arr,), index, ('$_bodo_col2_',)\n"
    vsmz__lhbj += '    )\n'
    vsmz__lhbj += "    count_series = in_df.groupby('$_bodo_col2_').size()\n"
    if wcvl__lgrhv:
        vsmz__lhbj += """    count_series = bodo.gatherv(count_series, allgather=True, warn_if_rep=False)
"""
        vsmz__lhbj += (
            '    count_arr = get_output_bin_counts(count_series, len(bins) - 1)\n'
            )
        vsmz__lhbj += '    index = get_bin_labels(bins)\n'
    else:
        vsmz__lhbj += (
            '    count_arr = bodo.hiframes.pd_series_ext.get_series_data(count_series)\n'
            )
        vsmz__lhbj += '    ind_arr = bodo.utils.conversion.coerce_to_array(\n'
        vsmz__lhbj += (
            '        bodo.hiframes.pd_series_ext.get_series_index(count_series)\n'
            )
        vsmz__lhbj += '    )\n'
        vsmz__lhbj += """    index = bodo.utils.conversion.index_from_array(ind_arr, name=_index_name)
"""
    vsmz__lhbj += (
        '    res = bodo.hiframes.pd_series_ext.init_series(count_arr, index, name)\n'
        )
    if is_overload_true(sort):
        vsmz__lhbj += '    res = res.sort_values(ascending=ascending)\n'
    if is_overload_true(normalize):
        bvv__gfxvp = 'len(S)' if wcvl__lgrhv else 'count_arr.sum()'
        vsmz__lhbj += f'    res = res / float({bvv__gfxvp})\n'
    vsmz__lhbj += '    return res\n'
    jhbwu__gfo = {}
    exec(vsmz__lhbj, {'bodo': bodo, 'pd': pd, 'np': np, 'get_bin_inds':
        get_bin_inds, 'get_bin_labels': get_bin_labels,
        'get_output_bin_counts': get_output_bin_counts, 'compute_bins':
        compute_bins}, jhbwu__gfo)
    impl = jhbwu__gfo['impl']
    return impl


def _gen_bins_handling(bins, dtype):
    vsmz__lhbj = ''
    if isinstance(bins, types.Integer):
        vsmz__lhbj += '    min_val = bodo.libs.array_ops.array_op_min(arr)\n'
        vsmz__lhbj += '    max_val = bodo.libs.array_ops.array_op_max(arr)\n'
        if dtype == bodo.datetime64ns:
            vsmz__lhbj += '    min_val = min_val.value\n'
            vsmz__lhbj += '    max_val = max_val.value\n'
        vsmz__lhbj += (
            '    bins = compute_bins(bins, min_val, max_val, right)\n')
        if dtype == bodo.datetime64ns:
            vsmz__lhbj += (
                "    bins = bins.astype(np.int64).view(np.dtype('datetime64[ns]'))\n"
                )
    else:
        vsmz__lhbj += (
            '    bins = bodo.utils.conversion.coerce_to_ndarray(bins)\n')
    return vsmz__lhbj


@overload(pd.cut, inline='always', no_unliteral=True)
def overload_cut(x, bins, right=True, labels=None, retbins=False, precision
    =3, include_lowest=False, duplicates='raise', ordered=True):
    nyr__qiz = dict(right=right, labels=labels, retbins=retbins, precision=
        precision, duplicates=duplicates, ordered=ordered)
    bpal__ets = dict(right=True, labels=None, retbins=False, precision=3,
        duplicates='raise', ordered=True)
    check_unsupported_args('pandas.cut', nyr__qiz, bpal__ets, package_name=
        'pandas', module_name='General')
    vsmz__lhbj = 'def impl(\n'
    vsmz__lhbj += '    x,\n'
    vsmz__lhbj += '    bins,\n'
    vsmz__lhbj += '    right=True,\n'
    vsmz__lhbj += '    labels=None,\n'
    vsmz__lhbj += '    retbins=False,\n'
    vsmz__lhbj += '    precision=3,\n'
    vsmz__lhbj += '    include_lowest=False,\n'
    vsmz__lhbj += "    duplicates='raise',\n"
    vsmz__lhbj += '    ordered=True\n'
    vsmz__lhbj += '):\n'
    if isinstance(x, SeriesType):
        vsmz__lhbj += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(x)\n')
        vsmz__lhbj += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(x)\n')
        vsmz__lhbj += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(x)\n')
    else:
        vsmz__lhbj += '    arr = bodo.utils.conversion.coerce_to_array(x)\n'
    vsmz__lhbj += _gen_bins_handling(bins, x.dtype)
    vsmz__lhbj += '    arr = get_bin_inds(bins, arr, False, include_lowest)\n'
    vsmz__lhbj += (
        '    label_index = get_bin_labels(bins, right, include_lowest)\n')
    vsmz__lhbj += """    cat_dtype = bodo.hiframes.pd_categorical_ext.init_cat_dtype(label_index, ordered, None, None)
"""
    vsmz__lhbj += """    out_arr = bodo.hiframes.pd_categorical_ext.init_categorical_array(arr, cat_dtype)
"""
    if isinstance(x, SeriesType):
        vsmz__lhbj += (
            '    res = bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        vsmz__lhbj += '    return res\n'
    else:
        vsmz__lhbj += '    return out_arr\n'
    jhbwu__gfo = {}
    exec(vsmz__lhbj, {'bodo': bodo, 'pd': pd, 'np': np, 'get_bin_inds':
        get_bin_inds, 'get_bin_labels': get_bin_labels,
        'get_output_bin_counts': get_output_bin_counts, 'compute_bins':
        compute_bins}, jhbwu__gfo)
    impl = jhbwu__gfo['impl']
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
    nyr__qiz = dict(labels=labels, retbins=retbins, precision=precision,
        duplicates=duplicates)
    bpal__ets = dict(labels=None, retbins=False, precision=3, duplicates=
        'raise')
    check_unsupported_args('pandas.qcut', nyr__qiz, bpal__ets, package_name
        ='pandas', module_name='General')
    if not (is_overload_int(q) or is_iterable_type(q)):
        raise BodoError(
            "pd.qcut(): 'q' should be an integer or a list of quantiles")

    def impl(x, q, labels=None, retbins=False, precision=3, duplicates='raise'
        ):
        ylc__axea = _get_q_list(q)
        arr = bodo.utils.conversion.coerce_to_array(x)
        bins = bodo.libs.array_ops.array_op_quantile(arr, ylc__axea)
        return pd.cut(x, bins, include_lowest=True)
    return impl


@overload_method(SeriesType, 'groupby', inline='always', no_unliteral=True)
def overload_series_groupby(S, by=None, axis=0, level=None, as_index=True,
    sort=True, group_keys=True, squeeze=False, observed=True, dropna=True):
    nyr__qiz = dict(axis=axis, sort=sort, group_keys=group_keys, squeeze=
        squeeze, observed=observed, dropna=dropna)
    bpal__ets = dict(axis=0, sort=True, group_keys=True, squeeze=False,
        observed=True, dropna=True)
    check_unsupported_args('Series.groupby', nyr__qiz, bpal__ets,
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
            yiupg__bvfo = bodo.utils.conversion.coerce_to_array(index)
            iayn__mxw = bodo.hiframes.pd_dataframe_ext.init_dataframe((
                yiupg__bvfo, arr), index, (' ', ''))
            return iayn__mxw.groupby(' ')['']
        return impl_index
    uhi__ved = by
    if isinstance(by, SeriesType):
        uhi__ved = by.data
    if isinstance(uhi__ved, DecimalArrayType):
        raise BodoError(
            'Series.groupby(): by argument with decimal type is not supported yet.'
            )
    if isinstance(by, bodo.hiframes.pd_categorical_ext.CategoricalArrayType):
        raise BodoError(
            'Series.groupby(): by argument with categorical type is not supported yet.'
            )

    def impl(S, by=None, axis=0, level=None, as_index=True, sort=True,
        group_keys=True, squeeze=False, observed=True, dropna=True):
        yiupg__bvfo = bodo.utils.conversion.coerce_to_array(by)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        iayn__mxw = bodo.hiframes.pd_dataframe_ext.init_dataframe((
            yiupg__bvfo, arr), index, (' ', ''))
        return iayn__mxw.groupby(' ')['']
    return impl


@overload_method(SeriesType, 'append', inline='always', no_unliteral=True)
def overload_series_append(S, to_append, ignore_index=False,
    verify_integrity=False):
    nyr__qiz = dict(verify_integrity=verify_integrity)
    bpal__ets = dict(verify_integrity=False)
    check_unsupported_args('Series.append', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
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
    if bodo.utils.utils.is_array_typ(values):

        def impl_arr(S, values):
            aeewh__eqkg = bodo.utils.conversion.coerce_to_array(values)
            A = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            n = len(A)
            gxi__wyxo = np.empty(n, np.bool_)
            bodo.libs.array.array_isin(gxi__wyxo, A, aeewh__eqkg, False)
            return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index,
                name)
        return impl_arr
    if not isinstance(values, (types.Set, types.List)):
        raise BodoError(
            "Series.isin(): 'values' parameter should be a set or a list")

    def impl(S, values):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        gxi__wyxo = bodo.libs.array_ops.array_op_isin(A, values)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index, name)
    return impl


@overload_method(SeriesType, 'quantile', inline='always', no_unliteral=True)
def overload_series_quantile(S, q=0.5, interpolation='linear'):
    nyr__qiz = dict(interpolation=interpolation)
    bpal__ets = dict(interpolation='linear')
    check_unsupported_args('Series.quantile', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
    if is_iterable_type(q) and isinstance(q.dtype, types.Number):

        def impl_list(S, q=0.5, interpolation='linear'):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            gxi__wyxo = bodo.libs.array_ops.array_op_quantile(arr, q)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            index = bodo.hiframes.pd_index_ext.init_numeric_index(bodo.
                utils.conversion.coerce_to_array(q), None)
            return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index,
                name)
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
        qvm__biqcp = bodo.libs.array_kernels.unique(arr)
        return bodo.allgatherv(qvm__biqcp, False)
    return impl


@overload_method(SeriesType, 'describe', inline='always', no_unliteral=True)
def overload_series_describe(S, percentiles=None, include=None, exclude=
    None, datetime_is_numeric=True):
    nyr__qiz = dict(percentiles=percentiles, include=include, exclude=
        exclude, datetime_is_numeric=datetime_is_numeric)
    bpal__ets = dict(percentiles=None, include=None, exclude=None,
        datetime_is_numeric=True)
    check_unsupported_args('Series.describe', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
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
        zpiq__gpg = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
    else:
        zpiq__gpg = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
    vsmz__lhbj = '\n'.join(('def impl(', '    S,', '    value=None,',
        '    method=None,', '    axis=None,', '    inplace=False,',
        '    limit=None,', '    downcast=None,', '):',
        '    in_arr = bodo.hiframes.pd_series_ext.get_series_data(S)',
        '    fill_arr = bodo.hiframes.pd_series_ext.get_series_data(value)',
        '    n = len(in_arr)', '    nf = len(fill_arr)',
        "    assert n == nf, 'fillna() requires same length arrays'",
        f'    out_arr = {zpiq__gpg}(n, -1)',
        '    for j in numba.parfors.parfor.internal_prange(n):',
        '        s = in_arr[j]',
        '        if bodo.libs.array_kernels.isna(in_arr, j) and not bodo.libs.array_kernels.isna('
        , '            fill_arr, j', '        ):',
        '            s = fill_arr[j]', '        out_arr[j] = s',
        '    bodo.libs.str_arr_ext.move_str_binary_arr_payload(in_arr, out_arr)'
        ))
    jkc__rwrjs = dict()
    exec(vsmz__lhbj, {'bodo': bodo, 'numba': numba}, jkc__rwrjs)
    zhapl__zpk = jkc__rwrjs['impl']
    return zhapl__zpk


def binary_str_fillna_inplace_impl(is_binary=False):
    if is_binary:
        zpiq__gpg = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
    else:
        zpiq__gpg = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
    vsmz__lhbj = 'def impl(S,\n'
    vsmz__lhbj += '     value=None,\n'
    vsmz__lhbj += '    method=None,\n'
    vsmz__lhbj += '    axis=None,\n'
    vsmz__lhbj += '    inplace=False,\n'
    vsmz__lhbj += '    limit=None,\n'
    vsmz__lhbj += '   downcast=None,\n'
    vsmz__lhbj += '):\n'
    vsmz__lhbj += (
        '    in_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    vsmz__lhbj += '    n = len(in_arr)\n'
    vsmz__lhbj += f'    out_arr = {zpiq__gpg}(n, -1)\n'
    vsmz__lhbj += '    for j in numba.parfors.parfor.internal_prange(n):\n'
    vsmz__lhbj += '        s = in_arr[j]\n'
    vsmz__lhbj += '        if bodo.libs.array_kernels.isna(in_arr, j):\n'
    vsmz__lhbj += '            s = value\n'
    vsmz__lhbj += '        out_arr[j] = s\n'
    vsmz__lhbj += (
        '    bodo.libs.str_arr_ext.move_str_binary_arr_payload(in_arr, out_arr)\n'
        )
    jkc__rwrjs = dict()
    exec(vsmz__lhbj, {'bodo': bodo, 'numba': numba}, jkc__rwrjs)
    zhapl__zpk = jkc__rwrjs['impl']
    return zhapl__zpk


def fillna_inplace_series_impl(S, value=None, method=None, axis=None,
    inplace=False, limit=None, downcast=None):
    kurv__esisk = bodo.hiframes.pd_series_ext.get_series_data(S)
    jycb__ubtn = bodo.hiframes.pd_series_ext.get_series_data(value)
    for heg__sudp in numba.parfors.parfor.internal_prange(len(kurv__esisk)):
        s = kurv__esisk[heg__sudp]
        if bodo.libs.array_kernels.isna(kurv__esisk, heg__sudp
            ) and not bodo.libs.array_kernels.isna(jycb__ubtn, heg__sudp):
            s = jycb__ubtn[heg__sudp]
        kurv__esisk[heg__sudp] = s


def fillna_inplace_impl(S, value=None, method=None, axis=None, inplace=
    False, limit=None, downcast=None):
    kurv__esisk = bodo.hiframes.pd_series_ext.get_series_data(S)
    for heg__sudp in numba.parfors.parfor.internal_prange(len(kurv__esisk)):
        s = kurv__esisk[heg__sudp]
        if bodo.libs.array_kernels.isna(kurv__esisk, heg__sudp):
            s = value
        kurv__esisk[heg__sudp] = s


def str_fillna_alloc_series_impl(S, value=None, method=None, axis=None,
    inplace=False, limit=None, downcast=None):
    kurv__esisk = bodo.hiframes.pd_series_ext.get_series_data(S)
    index = bodo.hiframes.pd_series_ext.get_series_index(S)
    name = bodo.hiframes.pd_series_ext.get_series_name(S)
    jycb__ubtn = bodo.hiframes.pd_series_ext.get_series_data(value)
    n = len(kurv__esisk)
    gxi__wyxo = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
    for tdacg__vcwv in numba.parfors.parfor.internal_prange(n):
        s = kurv__esisk[tdacg__vcwv]
        if bodo.libs.array_kernels.isna(kurv__esisk, tdacg__vcwv
            ) and not bodo.libs.array_kernels.isna(jycb__ubtn, tdacg__vcwv):
            s = jycb__ubtn[tdacg__vcwv]
        gxi__wyxo[tdacg__vcwv] = s
        if bodo.libs.array_kernels.isna(kurv__esisk, tdacg__vcwv
            ) and bodo.libs.array_kernels.isna(jycb__ubtn, tdacg__vcwv):
            bodo.libs.array_kernels.setna(gxi__wyxo, tdacg__vcwv)
    return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index, name)


def fillna_series_impl(S, value=None, method=None, axis=None, inplace=False,
    limit=None, downcast=None):
    kurv__esisk = bodo.hiframes.pd_series_ext.get_series_data(S)
    index = bodo.hiframes.pd_series_ext.get_series_index(S)
    name = bodo.hiframes.pd_series_ext.get_series_name(S)
    jycb__ubtn = bodo.hiframes.pd_series_ext.get_series_data(value)
    n = len(kurv__esisk)
    gxi__wyxo = bodo.utils.utils.alloc_type(n, kurv__esisk.dtype, (-1,))
    for heg__sudp in numba.parfors.parfor.internal_prange(n):
        s = kurv__esisk[heg__sudp]
        if bodo.libs.array_kernels.isna(kurv__esisk, heg__sudp
            ) and not bodo.libs.array_kernels.isna(jycb__ubtn, heg__sudp):
            s = jycb__ubtn[heg__sudp]
        gxi__wyxo[heg__sudp] = s
    return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index, name)


@overload_method(SeriesType, 'fillna', no_unliteral=True)
def overload_series_fillna(S, value=None, method=None, axis=None, inplace=
    False, limit=None, downcast=None):
    nyr__qiz = dict(limit=limit, downcast=downcast)
    bpal__ets = dict(limit=None, downcast=None)
    check_unsupported_args('Series.fillna', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
    saiah__qgwxp = not is_overload_none(value)
    ebf__wjzak = not is_overload_none(method)
    if saiah__qgwxp and ebf__wjzak:
        raise BodoError(
            "Series.fillna(): Cannot specify both 'value' and 'method'.")
    if not saiah__qgwxp and not ebf__wjzak:
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
    if ebf__wjzak:
        if is_overload_true(inplace):
            raise BodoError(
                "Series.fillna() with inplace=True not supported with 'method' argument yet."
                )
        aslhn__zeq = (
            "Series.fillna(): 'method' argument if provided must be a constant string and one of ('backfill', 'bfill', 'pad' 'ffill')."
            )
        if not is_overload_constant_str(method):
            raise_bodo_error(aslhn__zeq)
        elif get_overload_const_str(method) not in ('backfill', 'bfill',
            'pad', 'ffill'):
            raise BodoError(aslhn__zeq)
    nifj__pbpao = element_type(S.data)
    pdvc__bnfi = None
    if saiah__qgwxp:
        pdvc__bnfi = element_type(types.unliteral(value))
    if pdvc__bnfi and not can_replace(nifj__pbpao, pdvc__bnfi):
        raise BodoError(
            f'Series.fillna(): Cannot use value type {pdvc__bnfi} with series type {nifj__pbpao}'
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
        ruqf__cqx = to_str_arr_if_dict_array(S.data)
        if isinstance(value, SeriesType):

            def fillna_series_impl(S, value=None, method=None, axis=None,
                inplace=False, limit=None, downcast=None):
                kurv__esisk = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                jycb__ubtn = bodo.hiframes.pd_series_ext.get_series_data(value)
                n = len(kurv__esisk)
                gxi__wyxo = bodo.utils.utils.alloc_type(n, ruqf__cqx, (-1,))
                for heg__sudp in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(kurv__esisk, heg__sudp
                        ) and bodo.libs.array_kernels.isna(jycb__ubtn,
                        heg__sudp):
                        bodo.libs.array_kernels.setna(gxi__wyxo, heg__sudp)
                        continue
                    if bodo.libs.array_kernels.isna(kurv__esisk, heg__sudp):
                        gxi__wyxo[heg__sudp
                            ] = bodo.utils.conversion.unbox_if_timestamp(
                            jycb__ubtn[heg__sudp])
                        continue
                    gxi__wyxo[heg__sudp
                        ] = bodo.utils.conversion.unbox_if_timestamp(
                        kurv__esisk[heg__sudp])
                return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                    index, name)
            return fillna_series_impl
        if ebf__wjzak:
            ikzhq__yxa = (types.unicode_type, types.bool_, bodo.
                datetime64ns, bodo.timedelta64ns)
            if not isinstance(nifj__pbpao, (types.Integer, types.Float)
                ) and nifj__pbpao not in ikzhq__yxa:
                raise BodoError(
                    f"Series.fillna(): series of type {nifj__pbpao} are not supported with 'method' argument."
                    )

            def fillna_method_impl(S, value=None, method=None, axis=None,
                inplace=False, limit=None, downcast=None):
                kurv__esisk = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                gxi__wyxo = bodo.libs.array_kernels.ffill_bfill_arr(kurv__esisk
                    , method)
                return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                    index, name)
            return fillna_method_impl

        def fillna_impl(S, value=None, method=None, axis=None, inplace=
            False, limit=None, downcast=None):
            value = bodo.utils.conversion.unbox_if_timestamp(value)
            kurv__esisk = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            n = len(kurv__esisk)
            gxi__wyxo = bodo.utils.utils.alloc_type(n, ruqf__cqx, (-1,))
            for heg__sudp in numba.parfors.parfor.internal_prange(n):
                s = bodo.utils.conversion.unbox_if_timestamp(kurv__esisk[
                    heg__sudp])
                if bodo.libs.array_kernels.isna(kurv__esisk, heg__sudp):
                    s = value
                gxi__wyxo[heg__sudp] = s
            return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index,
                name)
        return fillna_impl


def create_fillna_specific_method_overload(overload_name):

    def overload_series_fillna_specific_method(S, axis=None, inplace=False,
        limit=None, downcast=None):
        gvl__egib = {'ffill': 'ffill', 'bfill': 'bfill', 'pad': 'ffill',
            'backfill': 'bfill'}[overload_name]
        nyr__qiz = dict(limit=limit, downcast=downcast)
        bpal__ets = dict(limit=None, downcast=None)
        check_unsupported_args(f'Series.{overload_name}', nyr__qiz,
            bpal__ets, package_name='pandas', module_name='Series')
        if not (is_overload_none(axis) or is_overload_zero(axis)):
            raise BodoError(
                f'Series.{overload_name}(): axis argument not supported')
        nifj__pbpao = element_type(S.data)
        ikzhq__yxa = (types.unicode_type, types.bool_, bodo.datetime64ns,
            bodo.timedelta64ns)
        if not isinstance(nifj__pbpao, (types.Integer, types.Float)
            ) and nifj__pbpao not in ikzhq__yxa:
            raise BodoError(
                f'Series.{overload_name}(): series of type {nifj__pbpao} are not supported.'
                )

        def impl(S, axis=None, inplace=False, limit=None, downcast=None):
            kurv__esisk = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            gxi__wyxo = bodo.libs.array_kernels.ffill_bfill_arr(kurv__esisk,
                gvl__egib)
            return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index,
                name)
        return impl
    return overload_series_fillna_specific_method


fillna_specific_methods = 'ffill', 'bfill', 'pad', 'backfill'


def _install_fillna_specific_methods():
    for overload_name in fillna_specific_methods:
        mqbwp__bhnsq = create_fillna_specific_method_overload(overload_name)
        overload_method(SeriesType, overload_name, no_unliteral=True)(
            mqbwp__bhnsq)


_install_fillna_specific_methods()


def check_unsupported_types(S, to_replace, value):
    if any(bodo.utils.utils.is_array_typ(x, True) for x in [S.dtype,
        to_replace, value]):
        ark__jqj = (
            'Series.replace(): only support with Scalar, List, or Dictionary')
        raise BodoError(ark__jqj)
    elif isinstance(to_replace, types.DictType) and not is_overload_none(value
        ):
        ark__jqj = (
            "Series.replace(): 'value' must be None when 'to_replace' is a dictionary"
            )
        raise BodoError(ark__jqj)
    elif any(isinstance(x, (PandasTimestampType, PDTimeDeltaType)) for x in
        [to_replace, value]):
        ark__jqj = (
            f'Series.replace(): Not supported for types {to_replace} and {value}'
            )
        raise BodoError(ark__jqj)


def series_replace_error_checking(S, to_replace, value, inplace, limit,
    regex, method):
    nyr__qiz = dict(inplace=inplace, limit=limit, regex=regex, method=method)
    hkjs__wtjnf = dict(inplace=False, limit=None, regex=False, method='pad')
    check_unsupported_args('Series.replace', nyr__qiz, hkjs__wtjnf,
        package_name='pandas', module_name='Series')
    check_unsupported_types(S, to_replace, value)


@overload_method(SeriesType, 'replace', inline='always', no_unliteral=True)
def overload_series_replace(S, to_replace=None, value=None, inplace=False,
    limit=None, regex=False, method='pad'):
    series_replace_error_checking(S, to_replace, value, inplace, limit,
        regex, method)
    nifj__pbpao = element_type(S.data)
    if isinstance(to_replace, types.DictType):
        dkoh__edhb = element_type(to_replace.key_type)
        pdvc__bnfi = element_type(to_replace.value_type)
    else:
        dkoh__edhb = element_type(to_replace)
        pdvc__bnfi = element_type(value)
    jgkgs__mzcu = None
    if nifj__pbpao != types.unliteral(dkoh__edhb):
        if bodo.utils.typing.equality_always_false(nifj__pbpao, types.
            unliteral(dkoh__edhb)
            ) or not bodo.utils.typing.types_equality_exists(nifj__pbpao,
            dkoh__edhb):

            def impl(S, to_replace=None, value=None, inplace=False, limit=
                None, regex=False, method='pad'):
                return S.copy()
            return impl
        if isinstance(nifj__pbpao, (types.Float, types.Integer)
            ) or nifj__pbpao == np.bool_:
            jgkgs__mzcu = nifj__pbpao
    if not can_replace(nifj__pbpao, types.unliteral(pdvc__bnfi)):

        def impl(S, to_replace=None, value=None, inplace=False, limit=None,
            regex=False, method='pad'):
            return S.copy()
        return impl
    lou__rkoor = to_str_arr_if_dict_array(S.data)
    if isinstance(lou__rkoor, CategoricalArrayType):

        def cat_impl(S, to_replace=None, value=None, inplace=False, limit=
            None, regex=False, method='pad'):
            kurv__esisk = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            return bodo.hiframes.pd_series_ext.init_series(kurv__esisk.
                replace(to_replace, value), index, name)
        return cat_impl

    def impl(S, to_replace=None, value=None, inplace=False, limit=None,
        regex=False, method='pad'):
        kurv__esisk = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        n = len(kurv__esisk)
        gxi__wyxo = bodo.utils.utils.alloc_type(n, lou__rkoor, (-1,))
        mtsl__ftv = build_replace_dict(to_replace, value, jgkgs__mzcu)
        for heg__sudp in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(kurv__esisk, heg__sudp):
                bodo.libs.array_kernels.setna(gxi__wyxo, heg__sudp)
                continue
            s = kurv__esisk[heg__sudp]
            if s in mtsl__ftv:
                s = mtsl__ftv[s]
            gxi__wyxo[heg__sudp] = s
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index, name)
    return impl


def build_replace_dict(to_replace, value, key_dtype_conv):
    pass


@overload(build_replace_dict)
def _build_replace_dict(to_replace, value, key_dtype_conv):
    xay__mzq = isinstance(to_replace, (types.Number, Decimal128Type)
        ) or to_replace in [bodo.string_type, types.boolean, bodo.bytes_type]
    zehsm__qwog = is_iterable_type(to_replace)
    zpu__nja = isinstance(value, (types.Number, Decimal128Type)) or value in [
        bodo.string_type, bodo.bytes_type, types.boolean]
    zcz__imloh = is_iterable_type(value)
    if xay__mzq and zpu__nja:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                mtsl__ftv = {}
                mtsl__ftv[key_dtype_conv(to_replace)] = value
                return mtsl__ftv
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            mtsl__ftv = {}
            mtsl__ftv[to_replace] = value
            return mtsl__ftv
        return impl
    if zehsm__qwog and zpu__nja:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                mtsl__ftv = {}
                for sdmjg__hmsa in to_replace:
                    mtsl__ftv[key_dtype_conv(sdmjg__hmsa)] = value
                return mtsl__ftv
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            mtsl__ftv = {}
            for sdmjg__hmsa in to_replace:
                mtsl__ftv[sdmjg__hmsa] = value
            return mtsl__ftv
        return impl
    if zehsm__qwog and zcz__imloh:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                mtsl__ftv = {}
                assert len(to_replace) == len(value
                    ), 'To_replace and value lengths must be the same'
                for heg__sudp in range(len(to_replace)):
                    mtsl__ftv[key_dtype_conv(to_replace[heg__sudp])] = value[
                        heg__sudp]
                return mtsl__ftv
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            mtsl__ftv = {}
            assert len(to_replace) == len(value
                ), 'To_replace and value lengths must be the same'
            for heg__sudp in range(len(to_replace)):
                mtsl__ftv[to_replace[heg__sudp]] = value[heg__sudp]
            return mtsl__ftv
        return impl
    if isinstance(to_replace, numba.types.DictType) and is_overload_none(value
        ):
        return lambda to_replace, value, key_dtype_conv: to_replace
    raise BodoError(
        'Series.replace(): Not supported for types to_replace={} and value={}'
        .format(to_replace, value))


@overload_method(SeriesType, 'diff', inline='always', no_unliteral=True)
def overload_series_diff(S, periods=1):
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
            gxi__wyxo = bodo.hiframes.series_impl.dt64_arr_sub(arr, bodo.
                hiframes.rolling.shift(arr, periods, False))
            return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index,
                name)
        return impl_datetime

    def impl(S, periods=1):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        gxi__wyxo = arr - bodo.hiframes.rolling.shift(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index, name)
    return impl


@overload_method(SeriesType, 'explode', inline='always', no_unliteral=True)
def overload_series_explode(S, ignore_index=False):
    from bodo.hiframes.split_impl import string_array_split_view_type
    nyr__qiz = dict(ignore_index=ignore_index)
    vehk__nyz = dict(ignore_index=False)
    check_unsupported_args('Series.explode', nyr__qiz, vehk__nyz,
        package_name='pandas', module_name='Series')
    if not (isinstance(S.data, ArrayItemArrayType) or S.data ==
        string_array_split_view_type):
        return lambda S, ignore_index=False: S.copy()

    def impl(S, ignore_index=False):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        yivy__mhpn = bodo.utils.conversion.index_to_array(index)
        gxi__wyxo, tar__urrpk = bodo.libs.array_kernels.explode(arr, yivy__mhpn
            )
        jmov__fhwwl = bodo.utils.conversion.index_from_array(tar__urrpk)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
            jmov__fhwwl, name)
    return impl


@overload(np.digitize, inline='always', no_unliteral=True)
def overload_series_np_digitize(x, bins, right=False):
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
            mipxe__fybez = np.empty(len(a), a.dtype)
            numba.parfors.parfor.init_prange()
            n = len(a)
            for heg__sudp in numba.parfors.parfor.internal_prange(n):
                mipxe__fybez[heg__sudp] = np.argmax(a[heg__sudp])
            return mipxe__fybez
        return impl


@overload(np.argmin, inline='always', no_unliteral=True)
def argmin_overload(a, axis=None, out=None):
    if isinstance(a, types.Array) and is_overload_constant_int(axis
        ) and get_overload_const_int(axis) == 1:

        def impl(a, axis=None, out=None):
            gmywm__qnw = np.empty(len(a), a.dtype)
            numba.parfors.parfor.init_prange()
            n = len(a)
            for heg__sudp in numba.parfors.parfor.internal_prange(n):
                gmywm__qnw[heg__sudp] = np.argmin(a[heg__sudp])
            return gmywm__qnw
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
    nyr__qiz = dict(axis=axis, inplace=inplace, how=how)
    tmni__ejd = dict(axis=0, inplace=False, how=None)
    check_unsupported_args('Series.dropna', nyr__qiz, tmni__ejd,
        package_name='pandas', module_name='Series')
    if S.dtype == bodo.string_type:

        def dropna_str_impl(S, axis=0, inplace=False, how=None):
            kurv__esisk = bodo.hiframes.pd_series_ext.get_series_data(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            lgbyx__tjaw = S.notna().values
            yivy__mhpn = bodo.utils.conversion.extract_index_array(S)
            jmov__fhwwl = bodo.utils.conversion.convert_to_index(yivy__mhpn
                [lgbyx__tjaw])
            gxi__wyxo = (bodo.hiframes.series_kernels.
                _series_dropna_str_alloc_impl_inner(kurv__esisk))
            return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                jmov__fhwwl, name)
        return dropna_str_impl
    else:

        def dropna_impl(S, axis=0, inplace=False, how=None):
            kurv__esisk = bodo.hiframes.pd_series_ext.get_series_data(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            yivy__mhpn = bodo.utils.conversion.extract_index_array(S)
            lgbyx__tjaw = S.notna().values
            jmov__fhwwl = bodo.utils.conversion.convert_to_index(yivy__mhpn
                [lgbyx__tjaw])
            gxi__wyxo = kurv__esisk[lgbyx__tjaw]
            return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                jmov__fhwwl, name)
        return dropna_impl


@overload_method(SeriesType, 'shift', inline='always', no_unliteral=True)
def overload_series_shift(S, periods=1, freq=None, axis=0, fill_value=None):
    nyr__qiz = dict(freq=freq, axis=axis, fill_value=fill_value)
    bpal__ets = dict(freq=None, axis=0, fill_value=None)
    check_unsupported_args('Series.shift', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
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
        gxi__wyxo = bodo.hiframes.rolling.shift(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index, name)
    return impl


@overload_method(SeriesType, 'pct_change', inline='always', no_unliteral=True)
def overload_series_pct_change(S, periods=1, fill_method='pad', limit=None,
    freq=None):
    nyr__qiz = dict(fill_method=fill_method, limit=limit, freq=freq)
    bpal__ets = dict(fill_method='pad', limit=None, freq=None)
    check_unsupported_args('Series.pct_change', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
    if not is_overload_int(periods):
        raise BodoError(
            'Series.pct_change(): periods argument must be an Integer')

    def impl(S, periods=1, fill_method='pad', limit=None, freq=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        gxi__wyxo = bodo.hiframes.rolling.pct_change(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index, name)
    return impl


def create_series_mask_where_overload(func_name):

    def overload_series_mask_where(S, cond, other=np.nan, inplace=False,
        axis=None, level=None, errors='raise', try_cast=False):
        _validate_arguments_mask_where(f'Series.{func_name}', S, cond,
            other, inplace, axis, level, errors, try_cast)
        if is_overload_constant_nan(other):
            aefw__szmp = 'None'
        else:
            aefw__szmp = 'other'
        vsmz__lhbj = """def impl(S, cond, other=np.nan, inplace=False, axis=None, level=None, errors='raise',try_cast=False):
"""
        if func_name == 'mask':
            vsmz__lhbj += '  cond = ~cond\n'
        vsmz__lhbj += (
            '  arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        vsmz__lhbj += (
            '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        vsmz__lhbj += (
            '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        vsmz__lhbj += (
            f'  out_arr = bodo.hiframes.series_impl.where_impl(cond, arr, {aefw__szmp})\n'
            )
        vsmz__lhbj += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        jhbwu__gfo = {}
        exec(vsmz__lhbj, {'bodo': bodo, 'np': np}, jhbwu__gfo)
        impl = jhbwu__gfo['impl']
        return impl
    return overload_series_mask_where


def _install_series_mask_where_overload():
    for func_name in ('mask', 'where'):
        mqbwp__bhnsq = create_series_mask_where_overload(func_name)
        overload_method(SeriesType, func_name, no_unliteral=True)(mqbwp__bhnsq)


_install_series_mask_where_overload()


def _validate_arguments_mask_where(func_name, S, cond, other, inplace, axis,
    level, errors, try_cast):
    nyr__qiz = dict(inplace=inplace, level=level, errors=errors, try_cast=
        try_cast)
    bpal__ets = dict(inplace=False, level=None, errors='raise', try_cast=False)
    check_unsupported_args(f'{func_name}', nyr__qiz, bpal__ets,
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
    rpj__qjcvp = is_overload_constant_nan(other)
    if not (is_default or rpj__qjcvp or is_scalar_type(other) or isinstance
        (other, types.Array) and other.ndim >= 1 and other.ndim <= max_ndim or
        isinstance(other, SeriesType) and (isinstance(arr, types.Array) or 
        arr.dtype in [bodo.string_type, bodo.bytes_type]) or 
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
            xdwtn__maad = arr.dtype.elem_type
        else:
            xdwtn__maad = arr.dtype
        if is_iterable_type(other):
            bnw__cdaz = other.dtype
        elif rpj__qjcvp:
            bnw__cdaz = types.float64
        else:
            bnw__cdaz = types.unliteral(other)
        if not rpj__qjcvp and not is_common_scalar_dtype([xdwtn__maad,
            bnw__cdaz]):
            raise BodoError(
                f"{func_name}() series and 'other' must share a common type.")


def create_explicit_binary_op_overload(op):

    def overload_series_explicit_binary_op(S, other, level=None, fill_value
        =None, axis=0):
        nyr__qiz = dict(level=level, axis=axis)
        bpal__ets = dict(level=None, axis=0)
        check_unsupported_args('series.{}'.format(op.__name__), nyr__qiz,
            bpal__ets, package_name='pandas', module_name='Series')
        syqxi__tmg = other == string_type or is_overload_constant_str(other)
        msco__gia = is_iterable_type(other) and other.dtype == string_type
        pld__ise = S.dtype == string_type and (op == operator.add and (
            syqxi__tmg or msco__gia) or op == operator.mul and isinstance(
            other, types.Integer))
        jxaw__hfw = S.dtype == bodo.timedelta64ns
        irmwf__pzmsa = S.dtype == bodo.datetime64ns
        wafkp__pdr = is_iterable_type(other) and (other.dtype ==
            datetime_timedelta_type or other.dtype == bodo.timedelta64ns)
        ncm__ipt = is_iterable_type(other) and (other.dtype ==
            datetime_datetime_type or other.dtype == pd_timestamp_type or 
            other.dtype == bodo.datetime64ns)
        kekn__lgsne = jxaw__hfw and (wafkp__pdr or ncm__ipt
            ) or irmwf__pzmsa and wafkp__pdr
        kekn__lgsne = kekn__lgsne and op == operator.add
        if not (isinstance(S.dtype, types.Number) or pld__ise or kekn__lgsne):
            raise BodoError(f'Unsupported types for Series.{op.__name__}')
        hxb__rdm = numba.core.registry.cpu_target.typing_context
        if is_scalar_type(other):
            args = S.data, other
            lou__rkoor = hxb__rdm.resolve_function_type(op, args, {}
                ).return_type
            if isinstance(S.data, IntegerArrayType
                ) and lou__rkoor == types.Array(types.bool_, 1, 'C'):
                lou__rkoor = boolean_array

            def impl_scalar(S, other, level=None, fill_value=None, axis=0):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                numba.parfors.parfor.init_prange()
                other = bodo.utils.conversion.unbox_if_timestamp(other)
                n = len(arr)
                gxi__wyxo = bodo.utils.utils.alloc_type(n, lou__rkoor, (-1,))
                for heg__sudp in numba.parfors.parfor.internal_prange(n):
                    nayc__ywfye = bodo.libs.array_kernels.isna(arr, heg__sudp)
                    if nayc__ywfye:
                        if fill_value is None:
                            bodo.libs.array_kernels.setna(gxi__wyxo, heg__sudp)
                        else:
                            gxi__wyxo[heg__sudp] = op(fill_value, other)
                    else:
                        gxi__wyxo[heg__sudp] = op(arr[heg__sudp], other)
                return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                    index, name)
            return impl_scalar
        args = S.data, types.Array(other.dtype, 1, 'C')
        lou__rkoor = hxb__rdm.resolve_function_type(op, args, {}).return_type
        if isinstance(S.data, IntegerArrayType) and lou__rkoor == types.Array(
            types.bool_, 1, 'C'):
            lou__rkoor = boolean_array

        def impl(S, other, level=None, fill_value=None, axis=0):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            vzzd__ryk = bodo.utils.conversion.coerce_to_array(other)
            numba.parfors.parfor.init_prange()
            n = len(arr)
            gxi__wyxo = bodo.utils.utils.alloc_type(n, lou__rkoor, (-1,))
            for heg__sudp in numba.parfors.parfor.internal_prange(n):
                nayc__ywfye = bodo.libs.array_kernels.isna(arr, heg__sudp)
                pfw__punw = bodo.libs.array_kernels.isna(vzzd__ryk, heg__sudp)
                if nayc__ywfye and pfw__punw:
                    bodo.libs.array_kernels.setna(gxi__wyxo, heg__sudp)
                elif nayc__ywfye:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(gxi__wyxo, heg__sudp)
                    else:
                        gxi__wyxo[heg__sudp] = op(fill_value, vzzd__ryk[
                            heg__sudp])
                elif pfw__punw:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(gxi__wyxo, heg__sudp)
                    else:
                        gxi__wyxo[heg__sudp] = op(arr[heg__sudp], fill_value)
                else:
                    gxi__wyxo[heg__sudp] = op(arr[heg__sudp], vzzd__ryk[
                        heg__sudp])
            return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index,
                name)
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
        hxb__rdm = numba.core.registry.cpu_target.typing_context
        if isinstance(other, types.Number):
            args = other, S.data
            lou__rkoor = hxb__rdm.resolve_function_type(op, args, {}
                ).return_type
            if isinstance(S.data, IntegerArrayType
                ) and lou__rkoor == types.Array(types.bool_, 1, 'C'):
                lou__rkoor = boolean_array

            def impl_scalar(S, other, level=None, fill_value=None, axis=0):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                numba.parfors.parfor.init_prange()
                n = len(arr)
                gxi__wyxo = bodo.utils.utils.alloc_type(n, lou__rkoor, None)
                for heg__sudp in numba.parfors.parfor.internal_prange(n):
                    nayc__ywfye = bodo.libs.array_kernels.isna(arr, heg__sudp)
                    if nayc__ywfye:
                        if fill_value is None:
                            bodo.libs.array_kernels.setna(gxi__wyxo, heg__sudp)
                        else:
                            gxi__wyxo[heg__sudp] = op(other, fill_value)
                    else:
                        gxi__wyxo[heg__sudp] = op(other, arr[heg__sudp])
                return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                    index, name)
            return impl_scalar
        args = types.Array(other.dtype, 1, 'C'), S.data
        lou__rkoor = hxb__rdm.resolve_function_type(op, args, {}).return_type
        if isinstance(S.data, IntegerArrayType) and lou__rkoor == types.Array(
            types.bool_, 1, 'C'):
            lou__rkoor = boolean_array

        def impl(S, other, level=None, fill_value=None, axis=0):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            vzzd__ryk = bodo.hiframes.pd_series_ext.get_series_data(other)
            numba.parfors.parfor.init_prange()
            n = len(arr)
            gxi__wyxo = bodo.utils.utils.alloc_type(n, lou__rkoor, None)
            for heg__sudp in numba.parfors.parfor.internal_prange(n):
                nayc__ywfye = bodo.libs.array_kernels.isna(arr, heg__sudp)
                pfw__punw = bodo.libs.array_kernels.isna(vzzd__ryk, heg__sudp)
                gxi__wyxo[heg__sudp] = op(vzzd__ryk[heg__sudp], arr[heg__sudp])
                if nayc__ywfye and pfw__punw:
                    bodo.libs.array_kernels.setna(gxi__wyxo, heg__sudp)
                elif nayc__ywfye:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(gxi__wyxo, heg__sudp)
                    else:
                        gxi__wyxo[heg__sudp] = op(vzzd__ryk[heg__sudp],
                            fill_value)
                elif pfw__punw:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(gxi__wyxo, heg__sudp)
                    else:
                        gxi__wyxo[heg__sudp] = op(fill_value, arr[heg__sudp])
                else:
                    gxi__wyxo[heg__sudp] = op(vzzd__ryk[heg__sudp], arr[
                        heg__sudp])
            return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index,
                name)
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
    for op, vghd__lck in explicit_binop_funcs_two_ways.items():
        for name in vghd__lck:
            mqbwp__bhnsq = create_explicit_binary_op_overload(op)
            djbef__mselw = create_explicit_binary_reverse_op_overload(op)
            uhh__svbu = 'r' + name
            overload_method(SeriesType, name, no_unliteral=True)(mqbwp__bhnsq)
            overload_method(SeriesType, uhh__svbu, no_unliteral=True)(
                djbef__mselw)
            explicit_binop_funcs.add(name)
    for op, name in explicit_binop_funcs_single.items():
        mqbwp__bhnsq = create_explicit_binary_op_overload(op)
        overload_method(SeriesType, name, no_unliteral=True)(mqbwp__bhnsq)
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
                gsy__xpi = bodo.utils.conversion.get_array_if_series_or_index(
                    rhs)
                gxi__wyxo = dt64_arr_sub(arr, gsy__xpi)
                return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
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
                gxi__wyxo = np.empty(n, np.dtype('datetime64[ns]'))
                for heg__sudp in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(arr, heg__sudp):
                        bodo.libs.array_kernels.setna(gxi__wyxo, heg__sudp)
                        continue
                    bnwov__ggj = (bodo.hiframes.pd_timestamp_ext.
                        convert_datetime64_to_timestamp(arr[heg__sudp]))
                    vqpmc__jti = op(bnwov__ggj, rhs)
                    gxi__wyxo[heg__sudp
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        vqpmc__jti.value)
                return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
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
                    gsy__xpi = (bodo.utils.conversion.
                        get_array_if_series_or_index(rhs))
                    gxi__wyxo = op(arr, bodo.utils.conversion.
                        unbox_if_timestamp(gsy__xpi))
                    return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                        index, name)
                return impl

            def impl(lhs, rhs):
                arr = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                index = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                name = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                gsy__xpi = bodo.utils.conversion.get_array_if_series_or_index(
                    rhs)
                gxi__wyxo = op(arr, gsy__xpi)
                return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                    index, name)
            return impl
        if isinstance(rhs, SeriesType):
            if rhs.dtype in [bodo.datetime64ns, bodo.timedelta64ns]:

                def impl(lhs, rhs):
                    arr = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                    index = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                    name = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                    cgxb__lhk = (bodo.utils.conversion.
                        get_array_if_series_or_index(lhs))
                    gxi__wyxo = op(bodo.utils.conversion.unbox_if_timestamp
                        (cgxb__lhk), arr)
                    return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                        index, name)
                return impl

            def impl(lhs, rhs):
                arr = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                index = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                name = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                cgxb__lhk = bodo.utils.conversion.get_array_if_series_or_index(
                    lhs)
                gxi__wyxo = op(cgxb__lhk, arr)
                return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                    index, name)
            return impl
    return overload_series_binary_op


skips = list(explicit_binop_funcs_two_ways.keys()) + list(
    explicit_binop_funcs_single.keys()) + split_logical_binops_funcs


def _install_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_binary_ops:
        if op in skips:
            continue
        mqbwp__bhnsq = create_binary_op_overload(op)
        overload(op)(mqbwp__bhnsq)


_install_binary_ops()


def dt64_arr_sub(arg1, arg2):
    return arg1 - arg2


@overload(dt64_arr_sub, no_unliteral=True)
def overload_dt64_arr_sub(arg1, arg2):
    assert arg1 == types.Array(bodo.datetime64ns, 1, 'C'
        ) and arg2 == types.Array(bodo.datetime64ns, 1, 'C')
    negx__nygea = np.dtype('timedelta64[ns]')

    def impl(arg1, arg2):
        numba.parfors.parfor.init_prange()
        n = len(arg1)
        S = np.empty(n, negx__nygea)
        for heg__sudp in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(arg1, heg__sudp
                ) or bodo.libs.array_kernels.isna(arg2, heg__sudp):
                bodo.libs.array_kernels.setna(S, heg__sudp)
                continue
            S[heg__sudp
                ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                bodo.hiframes.pd_timestamp_ext.dt64_to_integer(arg1[
                heg__sudp]) - bodo.hiframes.pd_timestamp_ext.
                dt64_to_integer(arg2[heg__sudp]))
        return S
    return impl


def create_inplace_binary_op_overload(op):

    def overload_series_inplace_binary_op(S, other):
        if isinstance(S, SeriesType) or isinstance(other, SeriesType):

            def impl(S, other):
                arr = bodo.utils.conversion.get_array_if_series_or_index(S)
                vzzd__ryk = bodo.utils.conversion.get_array_if_series_or_index(
                    other)
                op(arr, vzzd__ryk)
                return S
            return impl
    return overload_series_inplace_binary_op


def _install_inplace_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_inplace_binary_ops:
        mqbwp__bhnsq = create_inplace_binary_op_overload(op)
        overload(op, no_unliteral=True)(mqbwp__bhnsq)


_install_inplace_binary_ops()


def create_unary_op_overload(op):

    def overload_series_unary_op(S):
        if isinstance(S, SeriesType):

            def impl(S):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                gxi__wyxo = op(arr)
                return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                    index, name)
            return impl
    return overload_series_unary_op


def _install_unary_ops():
    for op in bodo.hiframes.pd_series_ext.series_unary_ops:
        mqbwp__bhnsq = create_unary_op_overload(op)
        overload(op, no_unliteral=True)(mqbwp__bhnsq)


_install_unary_ops()


def create_ufunc_overload(ufunc):
    if ufunc.nin == 1:

        def overload_series_ufunc_nin_1(S):
            if isinstance(S, SeriesType):

                def impl(S):
                    arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                    index = bodo.hiframes.pd_series_ext.get_series_index(S)
                    name = bodo.hiframes.pd_series_ext.get_series_name(S)
                    gxi__wyxo = ufunc(arr)
                    return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
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
                    vzzd__ryk = (bodo.utils.conversion.
                        get_array_if_series_or_index(S2))
                    gxi__wyxo = ufunc(arr, vzzd__ryk)
                    return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                        index, name)
                return impl
            elif isinstance(S2, SeriesType):

                def impl(S1, S2):
                    arr = bodo.utils.conversion.get_array_if_series_or_index(S1
                        )
                    vzzd__ryk = bodo.hiframes.pd_series_ext.get_series_data(S2)
                    index = bodo.hiframes.pd_series_ext.get_series_index(S2)
                    name = bodo.hiframes.pd_series_ext.get_series_name(S2)
                    gxi__wyxo = ufunc(arr, vzzd__ryk)
                    return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                        index, name)
                return impl
        return overload_series_ufunc_nin_2
    else:
        raise RuntimeError(
            "Don't know how to register ufuncs from ufunc_db with arity > 2")


def _install_np_ufuncs():
    import numba.np.ufunc_db
    for ufunc in numba.np.ufunc_db.get_ufuncs():
        mqbwp__bhnsq = create_ufunc_overload(ufunc)
        overload(ufunc, no_unliteral=True)(mqbwp__bhnsq)


_install_np_ufuncs()


def argsort(A):
    return np.argsort(A)


@overload(argsort, no_unliteral=True)
def overload_argsort(A):

    def impl(A):
        n = len(A)
        jrvxb__obip = bodo.libs.str_arr_ext.to_list_if_immutable_arr((A.
            copy(),))
        spj__ltmw = np.arange(n),
        bodo.libs.timsort.sort(jrvxb__obip, 0, n, spj__ltmw)
        return spj__ltmw[0]
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
        nxdtn__sfnc = get_overload_const_str(downcast)
        if nxdtn__sfnc in ('integer', 'signed'):
            out_dtype = types.int64
        elif nxdtn__sfnc == 'unsigned':
            out_dtype = types.uint64
        else:
            assert nxdtn__sfnc == 'float'
    if isinstance(arg_a, (types.Array, IntegerArrayType)):
        return lambda arg_a, errors='raise', downcast=None: arg_a.astype(
            out_dtype)
    if isinstance(arg_a, SeriesType):

        def impl_series(arg_a, errors='raise', downcast=None):
            kurv__esisk = bodo.hiframes.pd_series_ext.get_series_data(arg_a)
            index = bodo.hiframes.pd_series_ext.get_series_index(arg_a)
            name = bodo.hiframes.pd_series_ext.get_series_name(arg_a)
            gxi__wyxo = pd.to_numeric(kurv__esisk, errors, downcast)
            return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index,
                name)
        return impl_series
    if not is_str_arr_type(arg_a):
        raise BodoError(f'pd.to_numeric(): invalid argument type {arg_a}')
    if out_dtype == types.float64:

        def to_numeric_float_impl(arg_a, errors='raise', downcast=None):
            numba.parfors.parfor.init_prange()
            n = len(arg_a)
            nwru__wurh = np.empty(n, np.float64)
            for heg__sudp in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arg_a, heg__sudp):
                    bodo.libs.array_kernels.setna(nwru__wurh, heg__sudp)
                else:
                    bodo.libs.str_arr_ext.str_arr_item_to_numeric(nwru__wurh,
                        heg__sudp, arg_a, heg__sudp)
            return nwru__wurh
        return to_numeric_float_impl
    else:

        def to_numeric_int_impl(arg_a, errors='raise', downcast=None):
            numba.parfors.parfor.init_prange()
            n = len(arg_a)
            nwru__wurh = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)
            for heg__sudp in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arg_a, heg__sudp):
                    bodo.libs.array_kernels.setna(nwru__wurh, heg__sudp)
                else:
                    bodo.libs.str_arr_ext.str_arr_item_to_numeric(nwru__wurh,
                        heg__sudp, arg_a, heg__sudp)
            return nwru__wurh
        return to_numeric_int_impl


def series_filter_bool(arr, bool_arr):
    return arr[bool_arr]


@infer_global(series_filter_bool)
class SeriesFilterBoolInfer(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 2
        jobbx__iaeam = if_series_to_array_type(args[0])
        if isinstance(jobbx__iaeam, types.Array) and isinstance(jobbx__iaeam
            .dtype, types.Integer):
            jobbx__iaeam = types.Array(types.float64, 1, 'C')
        return jobbx__iaeam(*args)


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
    jxrj__uumkb = bodo.utils.utils.is_array_typ(x, True)
    xlh__cpakw = bodo.utils.utils.is_array_typ(y, True)
    vsmz__lhbj = 'def _impl(condition, x, y):\n'
    if isinstance(condition, SeriesType):
        vsmz__lhbj += (
            '  condition = bodo.hiframes.pd_series_ext.get_series_data(condition)\n'
            )
    if jxrj__uumkb and not bodo.utils.utils.is_array_typ(x, False):
        vsmz__lhbj += '  x = bodo.utils.conversion.coerce_to_array(x)\n'
    if xlh__cpakw and not bodo.utils.utils.is_array_typ(y, False):
        vsmz__lhbj += '  y = bodo.utils.conversion.coerce_to_array(y)\n'
    vsmz__lhbj += '  n = len(condition)\n'
    acf__mdwj = x.dtype if jxrj__uumkb else types.unliteral(x)
    qak__rcf = y.dtype if xlh__cpakw else types.unliteral(y)
    if not isinstance(x, CategoricalArrayType):
        acf__mdwj = element_type(x)
    if not isinstance(y, CategoricalArrayType):
        qak__rcf = element_type(y)

    def get_data(x):
        if isinstance(x, SeriesType):
            return x.data
        elif isinstance(x, types.Array):
            return x
        return types.unliteral(x)
    fcetc__cenkl = get_data(x)
    xixm__ccn = get_data(y)
    is_nullable = any(bodo.utils.typing.is_nullable(spj__ltmw) for
        spj__ltmw in [fcetc__cenkl, xixm__ccn])
    if xixm__ccn == types.none:
        if isinstance(acf__mdwj, types.Number):
            out_dtype = types.Array(types.float64, 1, 'C')
        else:
            out_dtype = to_nullable_type(x)
    elif fcetc__cenkl == xixm__ccn and not is_nullable:
        out_dtype = dtype_to_array_type(acf__mdwj)
    elif acf__mdwj == string_type or qak__rcf == string_type:
        out_dtype = bodo.string_array_type
    elif fcetc__cenkl == bytes_type or (jxrj__uumkb and acf__mdwj == bytes_type
        ) and (xixm__ccn == bytes_type or xlh__cpakw and qak__rcf == bytes_type
        ):
        out_dtype = binary_array_type
    elif isinstance(acf__mdwj, bodo.PDCategoricalDtype):
        out_dtype = None
    elif acf__mdwj in [bodo.timedelta64ns, bodo.datetime64ns]:
        out_dtype = types.Array(acf__mdwj, 1, 'C')
    elif qak__rcf in [bodo.timedelta64ns, bodo.datetime64ns]:
        out_dtype = types.Array(qak__rcf, 1, 'C')
    else:
        out_dtype = numba.from_dtype(np.promote_types(numba.np.
            numpy_support.as_dtype(acf__mdwj), numba.np.numpy_support.
            as_dtype(qak__rcf)))
        out_dtype = types.Array(out_dtype, 1, 'C')
        if is_nullable:
            out_dtype = bodo.utils.typing.to_nullable_type(out_dtype)
    if isinstance(acf__mdwj, bodo.PDCategoricalDtype):
        qkmtz__veuaf = 'x'
    else:
        qkmtz__veuaf = 'out_dtype'
    vsmz__lhbj += (
        f'  out_arr = bodo.utils.utils.alloc_type(n, {qkmtz__veuaf}, (-1,))\n')
    if isinstance(acf__mdwj, bodo.PDCategoricalDtype):
        vsmz__lhbj += """  out_codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(out_arr)
"""
        vsmz__lhbj += (
            '  x_codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(x)\n'
            )
    vsmz__lhbj += '  for j in numba.parfors.parfor.internal_prange(n):\n'
    vsmz__lhbj += (
        '    if not bodo.libs.array_kernels.isna(condition, j) and condition[j]:\n'
        )
    if jxrj__uumkb:
        vsmz__lhbj += '      if bodo.libs.array_kernels.isna(x, j):\n'
        vsmz__lhbj += '        setna(out_arr, j)\n'
        vsmz__lhbj += '        continue\n'
    if isinstance(acf__mdwj, bodo.PDCategoricalDtype):
        vsmz__lhbj += '      out_codes[j] = x_codes[j]\n'
    else:
        vsmz__lhbj += (
            '      out_arr[j] = bodo.utils.conversion.unbox_if_timestamp({})\n'
            .format('x[j]' if jxrj__uumkb else 'x'))
    vsmz__lhbj += '    else:\n'
    if xlh__cpakw:
        vsmz__lhbj += '      if bodo.libs.array_kernels.isna(y, j):\n'
        vsmz__lhbj += '        setna(out_arr, j)\n'
        vsmz__lhbj += '        continue\n'
    if xixm__ccn == types.none:
        if isinstance(acf__mdwj, bodo.PDCategoricalDtype):
            vsmz__lhbj += '      out_codes[j] = -1\n'
        else:
            vsmz__lhbj += '      setna(out_arr, j)\n'
    else:
        vsmz__lhbj += (
            '      out_arr[j] = bodo.utils.conversion.unbox_if_timestamp({})\n'
            .format('y[j]' if xlh__cpakw else 'y'))
    vsmz__lhbj += '  return out_arr\n'
    jhbwu__gfo = {}
    exec(vsmz__lhbj, {'bodo': bodo, 'numba': numba, 'setna': bodo.libs.
        array_kernels.setna, 'np': np, 'out_dtype': out_dtype}, jhbwu__gfo)
    trzbn__kdp = jhbwu__gfo['_impl']
    return trzbn__kdp


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
        zex__rkgae = choicelist.dtype
        if not bodo.utils.utils.is_array_typ(zex__rkgae, True):
            raise BodoError(
                "np.select(): 'choicelist' argument must be list or tuple of series/arrays types"
                )
        if is_series_type(zex__rkgae):
            ynj__qijle = zex__rkgae.data.dtype
        else:
            ynj__qijle = zex__rkgae.dtype
        if isinstance(ynj__qijle, bodo.PDCategoricalDtype):
            raise BodoError(
                'np.select(): data with choicelist of type Categorical not yet supported'
                )
        gvzrc__kltm = zex__rkgae
    else:
        hdt__dgkmc = []
        for zex__rkgae in choicelist:
            if not bodo.utils.utils.is_array_typ(zex__rkgae, True):
                raise BodoError(
                    "np.select(): 'choicelist' argument must be list or tuple of series/arrays types"
                    )
            if is_series_type(zex__rkgae):
                ynj__qijle = zex__rkgae.data.dtype
            else:
                ynj__qijle = zex__rkgae.dtype
            if isinstance(ynj__qijle, bodo.PDCategoricalDtype):
                raise BodoError(
                    'np.select(): data with choicelist of type Categorical not yet supported'
                    )
            hdt__dgkmc.append(ynj__qijle)
        if not is_common_scalar_dtype(hdt__dgkmc):
            raise BodoError(
                f"np.select(): 'choicelist' items must be arrays with a commmon data type. Found a tuple with the following data types {choicelist}."
                )
        gvzrc__kltm = choicelist[0]
    if is_series_type(gvzrc__kltm):
        gvzrc__kltm = gvzrc__kltm.data
    if is_overload_constant_int(default) and get_overload_const_int(default
        ) == 0:
        pass
    else:
        if not is_scalar_type(default):
            raise BodoError(
                "np.select(): 'default' argument must be scalar type")
        if not (is_common_scalar_dtype([default, gvzrc__kltm.dtype]) or 
            default == types.none or is_overload_constant_nan(default)):
            raise BodoError(
                f"np.select(): 'default' is not type compatible with the array types in choicelist. Choicelist type: {choicelist}, Default type: {default}"
                )
    if not (isinstance(gvzrc__kltm, types.Array) or isinstance(gvzrc__kltm,
        BooleanArrayType) or isinstance(gvzrc__kltm, IntegerArrayType) or 
        bodo.utils.utils.is_array_typ(gvzrc__kltm, False) and gvzrc__kltm.
        dtype in [bodo.string_type, bodo.bytes_type]):
        raise BodoError(
            f'np.select(): data with choicelist of type {gvzrc__kltm} not yet supported'
            )


@overload(np.select)
def overload_np_select(condlist, choicelist, default=0):
    _verify_np_select_arg_typs(condlist, choicelist, default)
    limtr__vgcjj = isinstance(choicelist, (types.List, types.UniTuple)
        ) and isinstance(condlist, (types.List, types.UniTuple))
    if isinstance(choicelist, (types.List, types.UniTuple)):
        jcphl__bmlbz = choicelist.dtype
    else:
        fnhp__bmmg = False
        hdt__dgkmc = []
        for zex__rkgae in choicelist:
            if is_nullable_type(zex__rkgae):
                fnhp__bmmg = True
            if is_series_type(zex__rkgae):
                ynj__qijle = zex__rkgae.data.dtype
            else:
                ynj__qijle = zex__rkgae.dtype
            if isinstance(ynj__qijle, bodo.PDCategoricalDtype):
                raise BodoError(
                    'np.select(): data with choicelist of type Categorical not yet supported'
                    )
            hdt__dgkmc.append(ynj__qijle)
        xrlt__tcoz, mbqo__xuipf = get_common_scalar_dtype(hdt__dgkmc)
        if not mbqo__xuipf:
            raise BodoError('Internal error in overload_np_select')
        vxqhv__tyi = dtype_to_array_type(xrlt__tcoz)
        if fnhp__bmmg:
            vxqhv__tyi = to_nullable_type(vxqhv__tyi)
        jcphl__bmlbz = vxqhv__tyi
    if isinstance(jcphl__bmlbz, SeriesType):
        jcphl__bmlbz = jcphl__bmlbz.data
    if is_overload_constant_int(default) and get_overload_const_int(default
        ) == 0:
        cst__otdye = True
    else:
        cst__otdye = False
    kshu__ipmov = False
    lfcqv__kvarl = False
    if cst__otdye:
        if isinstance(jcphl__bmlbz.dtype, types.Number):
            pass
        elif jcphl__bmlbz.dtype == types.bool_:
            lfcqv__kvarl = True
        else:
            kshu__ipmov = True
            jcphl__bmlbz = to_nullable_type(jcphl__bmlbz)
    elif default == types.none or is_overload_constant_nan(default):
        kshu__ipmov = True
        jcphl__bmlbz = to_nullable_type(jcphl__bmlbz)
    vsmz__lhbj = 'def np_select_impl(condlist, choicelist, default=0):\n'
    vsmz__lhbj += '  if len(condlist) != len(choicelist):\n'
    vsmz__lhbj += """    raise ValueError('list of cases must be same length as list of conditions')
"""
    vsmz__lhbj += '  output_len = len(choicelist[0])\n'
    vsmz__lhbj += (
        '  out = bodo.utils.utils.alloc_type(output_len, alloc_typ, (-1,))\n')
    vsmz__lhbj += '  for i in range(output_len):\n'
    if kshu__ipmov:
        vsmz__lhbj += '    bodo.libs.array_kernels.setna(out, i)\n'
    elif lfcqv__kvarl:
        vsmz__lhbj += '    out[i] = False\n'
    else:
        vsmz__lhbj += '    out[i] = default\n'
    if limtr__vgcjj:
        vsmz__lhbj += '  for i in range(len(condlist) - 1, -1, -1):\n'
        vsmz__lhbj += '    cond = condlist[i]\n'
        vsmz__lhbj += '    choice = choicelist[i]\n'
        vsmz__lhbj += '    out = np.where(cond, choice, out)\n'
    else:
        for heg__sudp in range(len(choicelist) - 1, -1, -1):
            vsmz__lhbj += f'  cond = condlist[{heg__sudp}]\n'
            vsmz__lhbj += f'  choice = choicelist[{heg__sudp}]\n'
            vsmz__lhbj += f'  out = np.where(cond, choice, out)\n'
    vsmz__lhbj += '  return out'
    jhbwu__gfo = dict()
    exec(vsmz__lhbj, {'bodo': bodo, 'numba': numba, 'setna': bodo.libs.
        array_kernels.setna, 'np': np, 'alloc_typ': jcphl__bmlbz}, jhbwu__gfo)
    impl = jhbwu__gfo['np_select_impl']
    return impl


@overload_method(SeriesType, 'duplicated', inline='always', no_unliteral=True)
def overload_series_duplicated(S, keep='first'):

    def impl(S, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        gxi__wyxo = bodo.libs.array_kernels.duplicated((arr,))
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index, name)
    return impl


@overload_method(SeriesType, 'drop_duplicates', inline='always',
    no_unliteral=True)
def overload_series_drop_duplicates(S, subset=None, keep='first', inplace=False
    ):
    nyr__qiz = dict(subset=subset, keep=keep, inplace=inplace)
    bpal__ets = dict(subset=None, keep='first', inplace=False)
    check_unsupported_args('Series.drop_duplicates', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')

    def impl(S, subset=None, keep='first', inplace=False):
        dsexv__rjrn = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(S))
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        (dsexv__rjrn,), yivy__mhpn = bodo.libs.array_kernels.drop_duplicates((
            dsexv__rjrn,), index, 1)
        index = bodo.utils.conversion.index_from_array(yivy__mhpn)
        return bodo.hiframes.pd_series_ext.init_series(dsexv__rjrn, index, name
            )
    return impl


@overload_method(SeriesType, 'between', inline='always', no_unliteral=True)
def overload_series_between(S, left, right, inclusive='both'):
    dsxq__vik = element_type(S.data)
    if not is_common_scalar_dtype([dsxq__vik, left]):
        raise_bodo_error(
            "Series.between(): 'left' must be compariable with the Series data"
            )
    if not is_common_scalar_dtype([dsxq__vik, right]):
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
        gxi__wyxo = np.empty(n, np.bool_)
        for heg__sudp in numba.parfors.parfor.internal_prange(n):
            zxrjz__aiudx = bodo.utils.conversion.box_if_dt64(arr[heg__sudp])
            if inclusive == 'both':
                gxi__wyxo[heg__sudp
                    ] = zxrjz__aiudx <= right and zxrjz__aiudx >= left
            else:
                gxi__wyxo[heg__sudp
                    ] = zxrjz__aiudx < right and zxrjz__aiudx > left
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo, index, name)
    return impl


@overload_method(SeriesType, 'repeat', inline='always', no_unliteral=True)
def overload_series_repeat(S, repeats, axis=None):
    nyr__qiz = dict(axis=axis)
    bpal__ets = dict(axis=None)
    check_unsupported_args('Series.repeat', nyr__qiz, bpal__ets,
        package_name='pandas', module_name='Series')
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
            yivy__mhpn = bodo.utils.conversion.index_to_array(index)
            gxi__wyxo = bodo.libs.array_kernels.repeat_kernel(arr, repeats)
            tar__urrpk = bodo.libs.array_kernels.repeat_kernel(yivy__mhpn,
                repeats)
            jmov__fhwwl = bodo.utils.conversion.index_from_array(tar__urrpk)
            return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
                jmov__fhwwl, name)
        return impl_int

    def impl_arr(S, repeats, axis=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        yivy__mhpn = bodo.utils.conversion.index_to_array(index)
        repeats = bodo.utils.conversion.coerce_to_array(repeats)
        gxi__wyxo = bodo.libs.array_kernels.repeat_kernel(arr, repeats)
        tar__urrpk = bodo.libs.array_kernels.repeat_kernel(yivy__mhpn, repeats)
        jmov__fhwwl = bodo.utils.conversion.index_from_array(tar__urrpk)
        return bodo.hiframes.pd_series_ext.init_series(gxi__wyxo,
            jmov__fhwwl, name)
    return impl_arr


@overload_method(SeriesType, 'to_dict', no_unliteral=True)
def overload_to_dict(S, into=None):

    def impl(S, into=None):
        spj__ltmw = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(S))
        n = len(spj__ltmw)
        wpi__brjpy = {}
        for heg__sudp in range(n):
            zxrjz__aiudx = bodo.utils.conversion.box_if_dt64(spj__ltmw[
                heg__sudp])
            wpi__brjpy[index[heg__sudp]] = zxrjz__aiudx
        return wpi__brjpy
    return impl


@overload_method(SeriesType, 'to_frame', inline='always', no_unliteral=True)
def overload_series_to_frame(S, name=None):
    aslhn__zeq = (
        "Series.to_frame(): output column name should be known at compile time. Set 'name' to a constant value."
        )
    if is_overload_none(name):
        if is_literal_type(S.name_typ):
            smfx__aumak = get_literal_value(S.name_typ)
        else:
            raise_bodo_error(aslhn__zeq)
    elif is_literal_type(name):
        smfx__aumak = get_literal_value(name)
    else:
        raise_bodo_error(aslhn__zeq)
    smfx__aumak = 0 if smfx__aumak is None else smfx__aumak

    def impl(S, name=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        return bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,), index,
            (smfx__aumak,))
    return impl


@overload_method(SeriesType, 'keys', inline='always', no_unliteral=True)
def overload_series_keys(S):

    def impl(S):
        return bodo.hiframes.pd_series_ext.get_series_index(S)
    return impl
