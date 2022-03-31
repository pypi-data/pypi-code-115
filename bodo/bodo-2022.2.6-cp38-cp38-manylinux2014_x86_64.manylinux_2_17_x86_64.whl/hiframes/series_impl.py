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
            vwr__ujq = list()
            for jtn__frw in range(len(S)):
                vwr__ujq.append(S.iat[jtn__frw])
            return vwr__ujq
        return impl_float

    def impl(S):
        vwr__ujq = list()
        for jtn__frw in range(len(S)):
            if bodo.libs.array_kernels.isna(S.values, jtn__frw):
                raise ValueError(
                    'Series.to_list(): Not supported for NA values with non-float dtypes'
                    )
            vwr__ujq.append(S.iat[jtn__frw])
        return vwr__ujq
    return impl


@overload_method(SeriesType, 'to_numpy', inline='always', no_unliteral=True)
def overload_series_to_numpy(S, dtype=None, copy=False, na_value=None):
    ggb__psugn = dict(dtype=dtype, copy=copy, na_value=na_value)
    ngy__olry = dict(dtype=None, copy=False, na_value=None)
    check_unsupported_args('Series.to_numpy', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')

    def impl(S, dtype=None, copy=False, na_value=None):
        return S.values
    return impl


@overload_method(SeriesType, 'reset_index', inline='always', no_unliteral=True)
def overload_series_reset_index(S, level=None, drop=False, name=None,
    inplace=False):
    ggb__psugn = dict(name=name, inplace=inplace)
    ngy__olry = dict(name=None, inplace=False)
    check_unsupported_args('Series.reset_index', ggb__psugn, ngy__olry,
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
    gwz__szits = get_name_literal(S.index.name_typ, True, series_name)
    columns = [gwz__szits, series_name]
    ybrom__rjw = (
        'def _impl(S, level=None, drop=False, name=None, inplace=False):\n')
    ybrom__rjw += '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    ybrom__rjw += """    index = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(S))
"""
    ybrom__rjw += """    df_index = bodo.hiframes.pd_index_ext.init_range_index(0, len(S), 1, None)
"""
    ybrom__rjw += '    col_var = {}\n'.format(gen_const_tup(columns))
    ybrom__rjw += """    return bodo.hiframes.pd_dataframe_ext.init_dataframe((index, arr), df_index, col_var)
"""
    nhc__gmjhk = {}
    exec(ybrom__rjw, {'bodo': bodo}, nhc__gmjhk)
    kong__wzta = nhc__gmjhk['_impl']
    return kong__wzta


@overload_method(SeriesType, 'isna', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'isnull', inline='always', no_unliteral=True)
def overload_series_isna(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        rexh__qmwzb = bodo.libs.array_ops.array_op_isna(arr)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb, index, name
            )
    return impl


@overload_method(SeriesType, 'round', inline='always', no_unliteral=True)
def overload_series_round(S, decimals=0):

    def impl(S, decimals=0):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        numba.parfors.parfor.init_prange()
        n = len(arr)
        rexh__qmwzb = bodo.utils.utils.alloc_type(n, arr, (-1,))
        for jtn__frw in numba.parfors.parfor.internal_prange(n):
            if pd.isna(arr[jtn__frw]):
                bodo.libs.array_kernels.setna(rexh__qmwzb, jtn__frw)
            else:
                rexh__qmwzb[jtn__frw] = np.round(arr[jtn__frw], decimals)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb, index, name
            )
    return impl


@overload_method(SeriesType, 'sum', inline='always', no_unliteral=True)
def overload_series_sum(S, axis=None, skipna=True, level=None, numeric_only
    =None, min_count=0):
    ggb__psugn = dict(level=level, numeric_only=numeric_only)
    ngy__olry = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.sum', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
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
    ggb__psugn = dict(level=level, numeric_only=numeric_only)
    ngy__olry = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.product', ggb__psugn, ngy__olry,
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
    ggb__psugn = dict(axis=axis, bool_only=bool_only, skipna=skipna, level=
        level)
    ngy__olry = dict(axis=0, bool_only=None, skipna=True, level=None)
    check_unsupported_args('Series.any', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')

    def impl(S, axis=0, bool_only=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        pwudx__ndhfj = 0
        for jtn__frw in numba.parfors.parfor.internal_prange(len(A)):
            gtovl__bepi = 0
            if not bodo.libs.array_kernels.isna(A, jtn__frw):
                gtovl__bepi = int(A[jtn__frw])
            pwudx__ndhfj += gtovl__bepi
        return pwudx__ndhfj != 0
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
        gjxly__maqo = bodo.hiframes.pd_series_ext.get_series_data(S)
        zhzw__boe = bodo.hiframes.pd_series_ext.get_series_data(other)
        numba.parfors.parfor.init_prange()
        pwudx__ndhfj = 0
        for jtn__frw in numba.parfors.parfor.internal_prange(len(gjxly__maqo)):
            gtovl__bepi = 0
            pqbdl__vhkkl = bodo.libs.array_kernels.isna(gjxly__maqo, jtn__frw)
            lnb__fmvm = bodo.libs.array_kernels.isna(zhzw__boe, jtn__frw)
            if (pqbdl__vhkkl and not lnb__fmvm or not pqbdl__vhkkl and
                lnb__fmvm):
                gtovl__bepi = 1
            elif not pqbdl__vhkkl:
                if gjxly__maqo[jtn__frw] != zhzw__boe[jtn__frw]:
                    gtovl__bepi = 1
            pwudx__ndhfj += gtovl__bepi
        return pwudx__ndhfj == 0
    return impl


@overload_method(SeriesType, 'all', inline='always', no_unliteral=True)
def overload_series_all(S, axis=0, bool_only=None, skipna=True, level=None):
    ggb__psugn = dict(axis=axis, bool_only=bool_only, skipna=skipna, level=
        level)
    ngy__olry = dict(axis=0, bool_only=None, skipna=True, level=None)
    check_unsupported_args('Series.all', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')

    def impl(S, axis=0, bool_only=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        pwudx__ndhfj = 0
        for jtn__frw in numba.parfors.parfor.internal_prange(len(A)):
            gtovl__bepi = 0
            if not bodo.libs.array_kernels.isna(A, jtn__frw):
                gtovl__bepi = int(not A[jtn__frw])
            pwudx__ndhfj += gtovl__bepi
        return pwudx__ndhfj == 0
    return impl


@overload_method(SeriesType, 'mad', inline='always', no_unliteral=True)
def overload_series_mad(S, axis=None, skipna=True, level=None):
    ggb__psugn = dict(level=level)
    ngy__olry = dict(level=None)
    check_unsupported_args('Series.mad', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
    if not is_overload_bool(skipna):
        raise BodoError("Series.mad(): 'skipna' argument must be a boolean")
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.mad(): axis argument not supported')
    fcga__qef = types.float64
    zbip__ipmea = types.float64
    if S.dtype == types.float32:
        fcga__qef = types.float32
        zbip__ipmea = types.float32
    apsg__novu = fcga__qef(0)
    gcg__gemce = zbip__ipmea(0)
    gsft__bpuzr = zbip__ipmea(1)

    def impl(S, axis=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        tpzf__yuc = apsg__novu
        pwudx__ndhfj = gcg__gemce
        for jtn__frw in numba.parfors.parfor.internal_prange(len(A)):
            gtovl__bepi = apsg__novu
            csqh__xqjpt = gcg__gemce
            if not bodo.libs.array_kernels.isna(A, jtn__frw) or not skipna:
                gtovl__bepi = A[jtn__frw]
                csqh__xqjpt = gsft__bpuzr
            tpzf__yuc += gtovl__bepi
            pwudx__ndhfj += csqh__xqjpt
        lbi__gymkz = bodo.hiframes.series_kernels._mean_handle_nan(tpzf__yuc,
            pwudx__ndhfj)
        xfkzm__gnb = apsg__novu
        for jtn__frw in numba.parfors.parfor.internal_prange(len(A)):
            gtovl__bepi = apsg__novu
            if not bodo.libs.array_kernels.isna(A, jtn__frw) or not skipna:
                gtovl__bepi = abs(A[jtn__frw] - lbi__gymkz)
            xfkzm__gnb += gtovl__bepi
        uvhsj__usjwc = bodo.hiframes.series_kernels._mean_handle_nan(xfkzm__gnb
            , pwudx__ndhfj)
        return uvhsj__usjwc
    return impl


@overload_method(SeriesType, 'mean', inline='always', no_unliteral=True)
def overload_series_mean(S, axis=None, skipna=None, level=None,
    numeric_only=None):
    if not isinstance(S.dtype, types.Number) and S.dtype not in [bodo.
        datetime64ns, types.bool_]:
        raise BodoError(f"Series.mean(): Series with type '{S}' not supported")
    ggb__psugn = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    ngy__olry = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.mean', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.mean(): axis argument not supported')

    def impl(S, axis=None, skipna=None, level=None, numeric_only=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_mean(arr)
    return impl


@overload_method(SeriesType, 'sem', inline='always', no_unliteral=True)
def overload_series_sem(S, axis=None, skipna=True, level=None, ddof=1,
    numeric_only=None):
    ggb__psugn = dict(level=level, numeric_only=numeric_only)
    ngy__olry = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.sem', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.sem(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.sem(): skipna argument must be a boolean')
    if not is_overload_int(ddof):
        raise BodoError('Series.sem(): ddof argument must be an integer')

    def impl(S, axis=None, skipna=True, level=None, ddof=1, numeric_only=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        mtn__iiqlp = 0
        prob__wcnrr = 0
        pwudx__ndhfj = 0
        for jtn__frw in numba.parfors.parfor.internal_prange(len(A)):
            gtovl__bepi = 0
            csqh__xqjpt = 0
            if not bodo.libs.array_kernels.isna(A, jtn__frw) or not skipna:
                gtovl__bepi = A[jtn__frw]
                csqh__xqjpt = 1
            mtn__iiqlp += gtovl__bepi
            prob__wcnrr += gtovl__bepi * gtovl__bepi
            pwudx__ndhfj += csqh__xqjpt
        jmluc__rxjw = bodo.hiframes.series_kernels._compute_var_nan_count_ddof(
            mtn__iiqlp, prob__wcnrr, pwudx__ndhfj, ddof)
        jmesp__lfz = bodo.hiframes.series_kernels._sem_handle_nan(jmluc__rxjw,
            pwudx__ndhfj)
        return jmesp__lfz
    return impl


@overload_method(SeriesType, 'kurt', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'kurtosis', inline='always', no_unliteral=True)
def overload_series_kurt(S, axis=None, skipna=True, level=None,
    numeric_only=None):
    ggb__psugn = dict(level=level, numeric_only=numeric_only)
    ngy__olry = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.kurtosis', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.kurtosis(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError(
            "Series.kurtosis(): 'skipna' argument must be a boolean")

    def impl(S, axis=None, skipna=True, level=None, numeric_only=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        mtn__iiqlp = 0.0
        prob__wcnrr = 0.0
        aor__mnv = 0.0
        zate__rfh = 0.0
        pwudx__ndhfj = 0
        for jtn__frw in numba.parfors.parfor.internal_prange(len(A)):
            gtovl__bepi = 0.0
            csqh__xqjpt = 0
            if not bodo.libs.array_kernels.isna(A, jtn__frw) or not skipna:
                gtovl__bepi = np.float64(A[jtn__frw])
                csqh__xqjpt = 1
            mtn__iiqlp += gtovl__bepi
            prob__wcnrr += gtovl__bepi ** 2
            aor__mnv += gtovl__bepi ** 3
            zate__rfh += gtovl__bepi ** 4
            pwudx__ndhfj += csqh__xqjpt
        jmluc__rxjw = bodo.hiframes.series_kernels.compute_kurt(mtn__iiqlp,
            prob__wcnrr, aor__mnv, zate__rfh, pwudx__ndhfj)
        return jmluc__rxjw
    return impl


@overload_method(SeriesType, 'skew', inline='always', no_unliteral=True)
def overload_series_skew(S, axis=None, skipna=True, level=None,
    numeric_only=None):
    ggb__psugn = dict(level=level, numeric_only=numeric_only)
    ngy__olry = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.skew', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.skew(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.skew(): skipna argument must be a boolean')

    def impl(S, axis=None, skipna=True, level=None, numeric_only=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        mtn__iiqlp = 0.0
        prob__wcnrr = 0.0
        aor__mnv = 0.0
        pwudx__ndhfj = 0
        for jtn__frw in numba.parfors.parfor.internal_prange(len(A)):
            gtovl__bepi = 0.0
            csqh__xqjpt = 0
            if not bodo.libs.array_kernels.isna(A, jtn__frw) or not skipna:
                gtovl__bepi = np.float64(A[jtn__frw])
                csqh__xqjpt = 1
            mtn__iiqlp += gtovl__bepi
            prob__wcnrr += gtovl__bepi ** 2
            aor__mnv += gtovl__bepi ** 3
            pwudx__ndhfj += csqh__xqjpt
        jmluc__rxjw = bodo.hiframes.series_kernels.compute_skew(mtn__iiqlp,
            prob__wcnrr, aor__mnv, pwudx__ndhfj)
        return jmluc__rxjw
    return impl


@overload_method(SeriesType, 'var', inline='always', no_unliteral=True)
def overload_series_var(S, axis=None, skipna=True, level=None, ddof=1,
    numeric_only=None):
    ggb__psugn = dict(level=level, numeric_only=numeric_only)
    ngy__olry = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.var', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
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
    ggb__psugn = dict(level=level, numeric_only=numeric_only)
    ngy__olry = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.std', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
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
        gjxly__maqo = bodo.hiframes.pd_series_ext.get_series_data(S)
        zhzw__boe = bodo.hiframes.pd_series_ext.get_series_data(other)
        numba.parfors.parfor.init_prange()
        exm__jqt = 0
        for jtn__frw in numba.parfors.parfor.internal_prange(len(gjxly__maqo)):
            eagh__kpi = gjxly__maqo[jtn__frw]
            sojs__zlmgc = zhzw__boe[jtn__frw]
            exm__jqt += eagh__kpi * sojs__zlmgc
        return exm__jqt
    return impl


@overload_method(SeriesType, 'cumsum', inline='always', no_unliteral=True)
def overload_series_cumsum(S, axis=None, skipna=True):
    ggb__psugn = dict(skipna=skipna)
    ngy__olry = dict(skipna=True)
    check_unsupported_args('Series.cumsum', ggb__psugn, ngy__olry,
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
    ggb__psugn = dict(skipna=skipna)
    ngy__olry = dict(skipna=True)
    check_unsupported_args('Series.cumprod', ggb__psugn, ngy__olry,
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
    ggb__psugn = dict(skipna=skipna)
    ngy__olry = dict(skipna=True)
    check_unsupported_args('Series.cummin', ggb__psugn, ngy__olry,
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
    ggb__psugn = dict(skipna=skipna)
    ngy__olry = dict(skipna=True)
    check_unsupported_args('Series.cummax', ggb__psugn, ngy__olry,
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
    ggb__psugn = dict(copy=copy, inplace=inplace, level=level, errors=errors)
    ngy__olry = dict(copy=True, inplace=False, level=None, errors='ignore')
    check_unsupported_args('Series.rename', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')

    def impl(S, index=None, axis=None, copy=True, inplace=False, level=None,
        errors='ignore'):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        odft__weaj = bodo.hiframes.pd_series_ext.get_series_index(S)
        return bodo.hiframes.pd_series_ext.init_series(A, odft__weaj, index)
    return impl


@overload_method(SeriesType, 'rename_axis', inline='always', no_unliteral=True)
def overload_series_rename_axis(S, mapper=None, index=None, columns=None,
    axis=None, copy=True, inplace=False):
    ggb__psugn = dict(index=index, columns=columns, axis=axis, copy=copy,
        inplace=inplace)
    ngy__olry = dict(index=None, columns=None, axis=None, copy=True,
        inplace=False)
    check_unsupported_args('Series.rename_axis', ggb__psugn, ngy__olry,
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
    ggb__psugn = dict(level=level)
    ngy__olry = dict(level=None)
    check_unsupported_args('Series.count', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')

    def impl(S, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_count(A)
    return impl


@overload_method(SeriesType, 'corr', inline='always', no_unliteral=True)
def overload_series_corr(S, other, method='pearson', min_periods=None):
    ggb__psugn = dict(method=method, min_periods=min_periods)
    ngy__olry = dict(method='pearson', min_periods=None)
    check_unsupported_args('Series.corr', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')

    def impl(S, other, method='pearson', min_periods=None):
        n = S.count()
        vvpy__bqtgm = S.sum()
        kfy__falav = other.sum()
        a = n * (S * other).sum() - vvpy__bqtgm * kfy__falav
        tyub__kndts = n * (S ** 2).sum() - vvpy__bqtgm ** 2
        rkx__qhk = n * (other ** 2).sum() - kfy__falav ** 2
        return a / np.sqrt(tyub__kndts * rkx__qhk)
    return impl


@overload_method(SeriesType, 'cov', inline='always', no_unliteral=True)
def overload_series_cov(S, other, min_periods=None, ddof=1):
    ggb__psugn = dict(min_periods=min_periods)
    ngy__olry = dict(min_periods=None)
    check_unsupported_args('Series.cov', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')

    def impl(S, other, min_periods=None, ddof=1):
        vvpy__bqtgm = S.mean()
        kfy__falav = other.mean()
        ursvy__wsttw = ((S - vvpy__bqtgm) * (other - kfy__falav)).sum()
        N = np.float64(S.count() - ddof)
        nonzero_len = S.count() * other.count()
        return _series_cov_helper(ursvy__wsttw, N, nonzero_len)
    return impl


def _series_cov_helper(sum_val, N, nonzero_len):
    return


@overload(_series_cov_helper, no_unliteral=True)
def _overload_series_cov_helper(sum_val, N, nonzero_len):

    def impl(sum_val, N, nonzero_len):
        if not nonzero_len:
            return np.nan
        if N <= 0.0:
            byzj__fxn = np.sign(sum_val)
            return np.inf * byzj__fxn
        return sum_val / N
    return impl


@overload_method(SeriesType, 'min', inline='always', no_unliteral=True)
def overload_series_min(S, axis=None, skipna=None, level=None, numeric_only
    =None):
    ggb__psugn = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    ngy__olry = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.min', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
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
    ggb__psugn = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    ngy__olry = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.max', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
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
    ggb__psugn = dict(axis=axis, skipna=skipna)
    ngy__olry = dict(axis=0, skipna=True)
    check_unsupported_args('Series.idxmin', ggb__psugn, ngy__olry,
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
    ggb__psugn = dict(axis=axis, skipna=skipna)
    ngy__olry = dict(axis=0, skipna=True)
    check_unsupported_args('Series.idxmax', ggb__psugn, ngy__olry,
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
    ggb__psugn = dict(level=level, numeric_only=numeric_only)
    ngy__olry = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.median', ggb__psugn, ngy__olry,
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
        quhlu__gqb = arr[:n]
        aqp__fuagu = index[:n]
        return bodo.hiframes.pd_series_ext.init_series(quhlu__gqb,
            aqp__fuagu, name)
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
        etpc__aqe = tail_slice(len(S), n)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        quhlu__gqb = arr[etpc__aqe:]
        aqp__fuagu = index[etpc__aqe:]
        return bodo.hiframes.pd_series_ext.init_series(quhlu__gqb,
            aqp__fuagu, name)
    return impl


@overload_method(SeriesType, 'first', inline='always', no_unliteral=True)
def overload_series_first(S, offset):
    rac__kxvo = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if types.unliteral(offset) not in rac__kxvo:
        raise BodoError(
            "Series.first(): 'offset' must be a string or a DateOffset")

    def impl(S, offset):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        if len(index):
            wvd__sfjf = index[0]
            byy__bfqb = (bodo.libs.array_kernels.
                get_valid_entries_from_date_offset(index, offset, wvd__sfjf,
                False))
        else:
            byy__bfqb = 0
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        quhlu__gqb = arr[:byy__bfqb]
        aqp__fuagu = index[:byy__bfqb]
        return bodo.hiframes.pd_series_ext.init_series(quhlu__gqb,
            aqp__fuagu, name)
    return impl


@overload_method(SeriesType, 'last', inline='always', no_unliteral=True)
def overload_series_last(S, offset):
    rac__kxvo = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if types.unliteral(offset) not in rac__kxvo:
        raise BodoError(
            "Series.last(): 'offset' must be a string or a DateOffset")

    def impl(S, offset):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        if len(index):
            olpb__ahuj = index[-1]
            byy__bfqb = (bodo.libs.array_kernels.
                get_valid_entries_from_date_offset(index, offset,
                olpb__ahuj, True))
        else:
            byy__bfqb = 0
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        quhlu__gqb = arr[len(arr) - byy__bfqb:]
        aqp__fuagu = index[len(arr) - byy__bfqb:]
        return bodo.hiframes.pd_series_ext.init_series(quhlu__gqb,
            aqp__fuagu, name)
    return impl


@overload_method(SeriesType, 'first_valid_index', inline='always',
    no_unliteral=True)
def overload_series_first_valid_index(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        qycd__audbd = bodo.utils.conversion.index_to_array(index)
        tmul__krx, gtae__nhfon = (bodo.libs.array_kernels.
            first_last_valid_index(arr, qycd__audbd))
        return gtae__nhfon if tmul__krx else None
    return impl


@overload_method(SeriesType, 'last_valid_index', inline='always',
    no_unliteral=True)
def overload_series_last_valid_index(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        qycd__audbd = bodo.utils.conversion.index_to_array(index)
        tmul__krx, gtae__nhfon = (bodo.libs.array_kernels.
            first_last_valid_index(arr, qycd__audbd, False))
        return gtae__nhfon if tmul__krx else None
    return impl


@overload_method(SeriesType, 'nlargest', inline='always', no_unliteral=True)
def overload_series_nlargest(S, n=5, keep='first'):
    ggb__psugn = dict(keep=keep)
    ngy__olry = dict(keep='first')
    check_unsupported_args('Series.nlargest', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
    if not is_overload_int(n):
        raise BodoError('Series.nlargest(): n argument must be an integer')

    def impl(S, n=5, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        qycd__audbd = bodo.utils.conversion.coerce_to_ndarray(index)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        rexh__qmwzb, egicd__hniyg = bodo.libs.array_kernels.nlargest(arr,
            qycd__audbd, n, True, bodo.hiframes.series_kernels.gt_f)
        mucr__rmi = bodo.utils.conversion.convert_to_index(egicd__hniyg)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
            mucr__rmi, name)
    return impl


@overload_method(SeriesType, 'nsmallest', inline='always', no_unliteral=True)
def overload_series_nsmallest(S, n=5, keep='first'):
    ggb__psugn = dict(keep=keep)
    ngy__olry = dict(keep='first')
    check_unsupported_args('Series.nsmallest', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
    if not is_overload_int(n):
        raise BodoError('Series.nsmallest(): n argument must be an integer')

    def impl(S, n=5, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        qycd__audbd = bodo.utils.conversion.coerce_to_ndarray(index)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        rexh__qmwzb, egicd__hniyg = bodo.libs.array_kernels.nlargest(arr,
            qycd__audbd, n, False, bodo.hiframes.series_kernels.lt_f)
        mucr__rmi = bodo.utils.conversion.convert_to_index(egicd__hniyg)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
            mucr__rmi, name)
    return impl


@overload_method(SeriesType, 'notnull', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'notna', inline='always', no_unliteral=True)
def overload_series_notna(S):
    return lambda S: S.isna() == False


@overload_method(SeriesType, 'astype', inline='always', no_unliteral=True)
def overload_series_astype(S, dtype, copy=True, errors='raise',
    _bodo_nan_to_str=True):
    ggb__psugn = dict(errors=errors)
    ngy__olry = dict(errors='raise')
    check_unsupported_args('Series.astype', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
    if dtype == types.unicode_type:
        raise_bodo_error(
            "Series.astype(): 'dtype' when passed as string must be a constant value"
            )

    def impl(S, dtype, copy=True, errors='raise', _bodo_nan_to_str=True):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        rexh__qmwzb = bodo.utils.conversion.fix_arr_dtype(arr, dtype, copy,
            nan_to_str=_bodo_nan_to_str, from_series=True)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb, index, name
            )
    return impl


@overload_method(SeriesType, 'take', inline='always', no_unliteral=True)
def overload_series_take(S, indices, axis=0, is_copy=True):
    ggb__psugn = dict(axis=axis, is_copy=is_copy)
    ngy__olry = dict(axis=0, is_copy=True)
    check_unsupported_args('Series.take', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
    if not (is_iterable_type(indices) and isinstance(indices.dtype, types.
        Integer)):
        raise BodoError(
            f"Series.take() 'indices' must be an array-like and contain integers. Found type {indices}."
            )

    def impl(S, indices, axis=0, is_copy=True):
        vezn__sddrp = bodo.utils.conversion.coerce_to_ndarray(indices)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(arr[vezn__sddrp],
            index[vezn__sddrp], name)
    return impl


@overload_method(SeriesType, 'argsort', inline='always', no_unliteral=True)
def overload_series_argsort(S, axis=0, kind='quicksort', order=None):
    ggb__psugn = dict(axis=axis, kind=kind, order=order)
    ngy__olry = dict(axis=0, kind='quicksort', order=None)
    check_unsupported_args('Series.argsort', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')

    def impl(S, axis=0, kind='quicksort', order=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        n = len(arr)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        vledo__clywj = S.notna().values
        if not vledo__clywj.all():
            rexh__qmwzb = np.full(n, -1, np.int64)
            rexh__qmwzb[vledo__clywj] = argsort(arr[vledo__clywj])
        else:
            rexh__qmwzb = argsort(arr)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb, index, name
            )
    return impl


@overload_method(SeriesType, 'sort_index', inline='always', no_unliteral=True)
def overload_series_sort_index(S, axis=0, level=None, ascending=True,
    inplace=False, kind='quicksort', na_position='last', sort_remaining=
    True, ignore_index=False, key=None):
    ggb__psugn = dict(axis=axis, level=level, inplace=inplace, kind=kind,
        sort_remaining=sort_remaining, ignore_index=ignore_index, key=key)
    ngy__olry = dict(axis=0, level=None, inplace=False, kind='quicksort',
        sort_remaining=True, ignore_index=False, key=None)
    check_unsupported_args('Series.sort_index', ggb__psugn, ngy__olry,
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
        tclsi__dyv = bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,),
            index, ('$_bodo_col3_',))
        rzd__hofg = tclsi__dyv.sort_index(ascending=ascending, inplace=
            inplace, na_position=na_position)
        rexh__qmwzb = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(
            rzd__hofg, 0)
        mucr__rmi = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(
            rzd__hofg)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
            mucr__rmi, name)
    return impl


@overload_method(SeriesType, 'sort_values', inline='always', no_unliteral=True)
def overload_series_sort_values(S, axis=0, ascending=True, inplace=False,
    kind='quicksort', na_position='last', ignore_index=False, key=None):
    ggb__psugn = dict(axis=axis, inplace=inplace, kind=kind, ignore_index=
        ignore_index, key=key)
    ngy__olry = dict(axis=0, inplace=False, kind='quicksort', ignore_index=
        False, key=None)
    check_unsupported_args('Series.sort_values', ggb__psugn, ngy__olry,
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
        tclsi__dyv = bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,),
            index, ('$_bodo_col_',))
        rzd__hofg = tclsi__dyv.sort_values(['$_bodo_col_'], ascending=
            ascending, inplace=inplace, na_position=na_position)
        rexh__qmwzb = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(
            rzd__hofg, 0)
        mucr__rmi = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(
            rzd__hofg)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
            mucr__rmi, name)
    return impl


def get_bin_inds(bins, arr):
    return arr


@overload(get_bin_inds, inline='always', no_unliteral=True)
def overload_get_bin_inds(bins, arr, is_nullable=True, include_lowest=True):
    assert is_overload_constant_bool(is_nullable)
    nlcwe__wjgjk = is_overload_true(is_nullable)
    ybrom__rjw = (
        'def impl(bins, arr, is_nullable=True, include_lowest=True):\n')
    ybrom__rjw += '  numba.parfors.parfor.init_prange()\n'
    ybrom__rjw += '  n = len(arr)\n'
    if nlcwe__wjgjk:
        ybrom__rjw += (
            '  out_arr = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n')
    else:
        ybrom__rjw += '  out_arr = np.empty(n, np.int64)\n'
    ybrom__rjw += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    ybrom__rjw += '    if bodo.libs.array_kernels.isna(arr, i):\n'
    if nlcwe__wjgjk:
        ybrom__rjw += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    else:
        ybrom__rjw += '      out_arr[i] = -1\n'
    ybrom__rjw += '      continue\n'
    ybrom__rjw += '    val = arr[i]\n'
    ybrom__rjw += '    if include_lowest and val == bins[0]:\n'
    ybrom__rjw += '      ind = 1\n'
    ybrom__rjw += '    else:\n'
    ybrom__rjw += '      ind = np.searchsorted(bins, val)\n'
    ybrom__rjw += '    if ind == 0 or ind == len(bins):\n'
    if nlcwe__wjgjk:
        ybrom__rjw += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    else:
        ybrom__rjw += '      out_arr[i] = -1\n'
    ybrom__rjw += '    else:\n'
    ybrom__rjw += '      out_arr[i] = ind - 1\n'
    ybrom__rjw += '  return out_arr\n'
    nhc__gmjhk = {}
    exec(ybrom__rjw, {'bodo': bodo, 'np': np, 'numba': numba}, nhc__gmjhk)
    impl = nhc__gmjhk['impl']
    return impl


@register_jitable
def _round_frac(x, precision: int):
    if not np.isfinite(x) or x == 0:
        return x
    else:
        uepol__kww, jfkf__ojspm = np.divmod(x, 1)
        if uepol__kww == 0:
            sfwe__dcic = -int(np.floor(np.log10(abs(jfkf__ojspm)))
                ) - 1 + precision
        else:
            sfwe__dcic = precision
        return np.around(x, sfwe__dcic)


@register_jitable
def _infer_precision(base_precision: int, bins) ->int:
    for precision in range(base_precision, 20):
        epxxi__ymab = np.array([_round_frac(b, precision) for b in bins])
        if len(np.unique(epxxi__ymab)) == len(bins):
            return precision
    return base_precision


def get_bin_labels(bins):
    pass


@overload(get_bin_labels, no_unliteral=True)
def overload_get_bin_labels(bins, right=True, include_lowest=True):
    dtype = np.float64 if isinstance(bins.dtype, types.Integer) else bins.dtype
    if dtype == bodo.datetime64ns:
        khn__mfd = bodo.timedelta64ns(1)

        def impl_dt64(bins, right=True, include_lowest=True):
            axq__rixao = bins.copy()
            if right and include_lowest:
                axq__rixao[0] = axq__rixao[0] - khn__mfd
            neoxy__covwa = bodo.libs.interval_arr_ext.init_interval_array(
                axq__rixao[:-1], axq__rixao[1:])
            return bodo.hiframes.pd_index_ext.init_interval_index(neoxy__covwa,
                None)
        return impl_dt64

    def impl(bins, right=True, include_lowest=True):
        base_precision = 3
        precision = _infer_precision(base_precision, bins)
        axq__rixao = np.array([_round_frac(b, precision) for b in bins],
            dtype=dtype)
        if right and include_lowest:
            axq__rixao[0] = axq__rixao[0] - 10.0 ** -precision
        neoxy__covwa = bodo.libs.interval_arr_ext.init_interval_array(
            axq__rixao[:-1], axq__rixao[1:])
        return bodo.hiframes.pd_index_ext.init_interval_index(neoxy__covwa,
            None)
    return impl


def get_output_bin_counts(count_series, nbins):
    pass


@overload(get_output_bin_counts, no_unliteral=True)
def overload_get_output_bin_counts(count_series, nbins):

    def impl(count_series, nbins):
        ushjv__indz = bodo.hiframes.pd_series_ext.get_series_data(count_series)
        jkbvx__rnyk = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(count_series))
        rexh__qmwzb = np.zeros(nbins, np.int64)
        for jtn__frw in range(len(ushjv__indz)):
            rexh__qmwzb[jkbvx__rnyk[jtn__frw]] = ushjv__indz[jtn__frw]
        return rexh__qmwzb
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
            jfw__oqtxa = (max_val - min_val) * 0.001
            if right:
                bins[0] -= jfw__oqtxa
            else:
                bins[-1] += jfw__oqtxa
        return bins
    return impl


@overload_method(SeriesType, 'value_counts', inline='always', no_unliteral=True
    )
def overload_series_value_counts(S, normalize=False, sort=True, ascending=
    False, bins=None, dropna=True, _index_name=None):
    ggb__psugn = dict(dropna=dropna)
    ngy__olry = dict(dropna=True)
    check_unsupported_args('Series.value_counts', ggb__psugn, ngy__olry,
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
    rfaci__zqy = not is_overload_none(bins)
    ybrom__rjw = 'def impl(\n'
    ybrom__rjw += '    S,\n'
    ybrom__rjw += '    normalize=False,\n'
    ybrom__rjw += '    sort=True,\n'
    ybrom__rjw += '    ascending=False,\n'
    ybrom__rjw += '    bins=None,\n'
    ybrom__rjw += '    dropna=True,\n'
    ybrom__rjw += (
        '    _index_name=None,  # bodo argument. See groupby.value_counts\n')
    ybrom__rjw += '):\n'
    ybrom__rjw += '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    ybrom__rjw += (
        '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
    ybrom__rjw += '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    if rfaci__zqy:
        ybrom__rjw += '    right = True\n'
        ybrom__rjw += _gen_bins_handling(bins, S.dtype)
        ybrom__rjw += '    arr = get_bin_inds(bins, arr)\n'
    ybrom__rjw += (
        '    in_df = bodo.hiframes.pd_dataframe_ext.init_dataframe(\n')
    ybrom__rjw += "        (arr,), index, ('$_bodo_col2_',)\n"
    ybrom__rjw += '    )\n'
    ybrom__rjw += "    count_series = in_df.groupby('$_bodo_col2_').size()\n"
    if rfaci__zqy:
        ybrom__rjw += """    count_series = bodo.gatherv(count_series, allgather=True, warn_if_rep=False)
"""
        ybrom__rjw += (
            '    count_arr = get_output_bin_counts(count_series, len(bins) - 1)\n'
            )
        ybrom__rjw += '    index = get_bin_labels(bins)\n'
    else:
        ybrom__rjw += (
            '    count_arr = bodo.hiframes.pd_series_ext.get_series_data(count_series)\n'
            )
        ybrom__rjw += '    ind_arr = bodo.utils.conversion.coerce_to_array(\n'
        ybrom__rjw += (
            '        bodo.hiframes.pd_series_ext.get_series_index(count_series)\n'
            )
        ybrom__rjw += '    )\n'
        ybrom__rjw += """    index = bodo.utils.conversion.index_from_array(ind_arr, name=_index_name)
"""
    ybrom__rjw += (
        '    res = bodo.hiframes.pd_series_ext.init_series(count_arr, index, name)\n'
        )
    if is_overload_true(sort):
        ybrom__rjw += '    res = res.sort_values(ascending=ascending)\n'
    if is_overload_true(normalize):
        lhf__bnl = 'len(S)' if rfaci__zqy else 'count_arr.sum()'
        ybrom__rjw += f'    res = res / float({lhf__bnl})\n'
    ybrom__rjw += '    return res\n'
    nhc__gmjhk = {}
    exec(ybrom__rjw, {'bodo': bodo, 'pd': pd, 'np': np, 'get_bin_inds':
        get_bin_inds, 'get_bin_labels': get_bin_labels,
        'get_output_bin_counts': get_output_bin_counts, 'compute_bins':
        compute_bins}, nhc__gmjhk)
    impl = nhc__gmjhk['impl']
    return impl


def _gen_bins_handling(bins, dtype):
    ybrom__rjw = ''
    if isinstance(bins, types.Integer):
        ybrom__rjw += '    min_val = bodo.libs.array_ops.array_op_min(arr)\n'
        ybrom__rjw += '    max_val = bodo.libs.array_ops.array_op_max(arr)\n'
        if dtype == bodo.datetime64ns:
            ybrom__rjw += '    min_val = min_val.value\n'
            ybrom__rjw += '    max_val = max_val.value\n'
        ybrom__rjw += (
            '    bins = compute_bins(bins, min_val, max_val, right)\n')
        if dtype == bodo.datetime64ns:
            ybrom__rjw += (
                "    bins = bins.astype(np.int64).view(np.dtype('datetime64[ns]'))\n"
                )
    else:
        ybrom__rjw += (
            '    bins = bodo.utils.conversion.coerce_to_ndarray(bins)\n')
    return ybrom__rjw


@overload(pd.cut, inline='always', no_unliteral=True)
def overload_cut(x, bins, right=True, labels=None, retbins=False, precision
    =3, include_lowest=False, duplicates='raise', ordered=True):
    ggb__psugn = dict(right=right, labels=labels, retbins=retbins,
        precision=precision, duplicates=duplicates, ordered=ordered)
    ngy__olry = dict(right=True, labels=None, retbins=False, precision=3,
        duplicates='raise', ordered=True)
    check_unsupported_args('pandas.cut', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='General')
    ybrom__rjw = 'def impl(\n'
    ybrom__rjw += '    x,\n'
    ybrom__rjw += '    bins,\n'
    ybrom__rjw += '    right=True,\n'
    ybrom__rjw += '    labels=None,\n'
    ybrom__rjw += '    retbins=False,\n'
    ybrom__rjw += '    precision=3,\n'
    ybrom__rjw += '    include_lowest=False,\n'
    ybrom__rjw += "    duplicates='raise',\n"
    ybrom__rjw += '    ordered=True\n'
    ybrom__rjw += '):\n'
    if isinstance(x, SeriesType):
        ybrom__rjw += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(x)\n')
        ybrom__rjw += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(x)\n')
        ybrom__rjw += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(x)\n')
    else:
        ybrom__rjw += '    arr = bodo.utils.conversion.coerce_to_array(x)\n'
    ybrom__rjw += _gen_bins_handling(bins, x.dtype)
    ybrom__rjw += '    arr = get_bin_inds(bins, arr, False, include_lowest)\n'
    ybrom__rjw += (
        '    label_index = get_bin_labels(bins, right, include_lowest)\n')
    ybrom__rjw += """    cat_dtype = bodo.hiframes.pd_categorical_ext.init_cat_dtype(label_index, ordered, None, None)
"""
    ybrom__rjw += """    out_arr = bodo.hiframes.pd_categorical_ext.init_categorical_array(arr, cat_dtype)
"""
    if isinstance(x, SeriesType):
        ybrom__rjw += (
            '    res = bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        ybrom__rjw += '    return res\n'
    else:
        ybrom__rjw += '    return out_arr\n'
    nhc__gmjhk = {}
    exec(ybrom__rjw, {'bodo': bodo, 'pd': pd, 'np': np, 'get_bin_inds':
        get_bin_inds, 'get_bin_labels': get_bin_labels,
        'get_output_bin_counts': get_output_bin_counts, 'compute_bins':
        compute_bins}, nhc__gmjhk)
    impl = nhc__gmjhk['impl']
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
    ggb__psugn = dict(labels=labels, retbins=retbins, precision=precision,
        duplicates=duplicates)
    ngy__olry = dict(labels=None, retbins=False, precision=3, duplicates=
        'raise')
    check_unsupported_args('pandas.qcut', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='General')
    if not (is_overload_int(q) or is_iterable_type(q)):
        raise BodoError(
            "pd.qcut(): 'q' should be an integer or a list of quantiles")

    def impl(x, q, labels=None, retbins=False, precision=3, duplicates='raise'
        ):
        lbl__lczts = _get_q_list(q)
        arr = bodo.utils.conversion.coerce_to_array(x)
        bins = bodo.libs.array_ops.array_op_quantile(arr, lbl__lczts)
        return pd.cut(x, bins, include_lowest=True)
    return impl


@overload_method(SeriesType, 'groupby', inline='always', no_unliteral=True)
def overload_series_groupby(S, by=None, axis=0, level=None, as_index=True,
    sort=True, group_keys=True, squeeze=False, observed=True, dropna=True):
    ggb__psugn = dict(axis=axis, sort=sort, group_keys=group_keys, squeeze=
        squeeze, observed=observed, dropna=dropna)
    ngy__olry = dict(axis=0, sort=True, group_keys=True, squeeze=False,
        observed=True, dropna=True)
    check_unsupported_args('Series.groupby', ggb__psugn, ngy__olry,
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
            fse__lasrh = bodo.utils.conversion.coerce_to_array(index)
            tclsi__dyv = bodo.hiframes.pd_dataframe_ext.init_dataframe((
                fse__lasrh, arr), index, (' ', ''))
            return tclsi__dyv.groupby(' ')['']
        return impl_index
    wxwbg__nynk = by
    if isinstance(by, SeriesType):
        wxwbg__nynk = by.data
    if isinstance(wxwbg__nynk, DecimalArrayType):
        raise BodoError(
            'Series.groupby(): by argument with decimal type is not supported yet.'
            )
    if isinstance(by, bodo.hiframes.pd_categorical_ext.CategoricalArrayType):
        raise BodoError(
            'Series.groupby(): by argument with categorical type is not supported yet.'
            )

    def impl(S, by=None, axis=0, level=None, as_index=True, sort=True,
        group_keys=True, squeeze=False, observed=True, dropna=True):
        fse__lasrh = bodo.utils.conversion.coerce_to_array(by)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        tclsi__dyv = bodo.hiframes.pd_dataframe_ext.init_dataframe((
            fse__lasrh, arr), index, (' ', ''))
        return tclsi__dyv.groupby(' ')['']
    return impl


@overload_method(SeriesType, 'append', inline='always', no_unliteral=True)
def overload_series_append(S, to_append, ignore_index=False,
    verify_integrity=False):
    ggb__psugn = dict(verify_integrity=verify_integrity)
    ngy__olry = dict(verify_integrity=False)
    check_unsupported_args('Series.append', ggb__psugn, ngy__olry,
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
            xcj__rkkjs = bodo.utils.conversion.coerce_to_array(values)
            A = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            n = len(A)
            rexh__qmwzb = np.empty(n, np.bool_)
            bodo.libs.array.array_isin(rexh__qmwzb, A, xcj__rkkjs, False)
            return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                index, name)
        return impl_arr
    if not isinstance(values, (types.Set, types.List)):
        raise BodoError(
            "Series.isin(): 'values' parameter should be a set or a list")

    def impl(S, values):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        rexh__qmwzb = bodo.libs.array_ops.array_op_isin(A, values)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb, index, name
            )
    return impl


@overload_method(SeriesType, 'quantile', inline='always', no_unliteral=True)
def overload_series_quantile(S, q=0.5, interpolation='linear'):
    ggb__psugn = dict(interpolation=interpolation)
    ngy__olry = dict(interpolation='linear')
    check_unsupported_args('Series.quantile', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
    if is_iterable_type(q) and isinstance(q.dtype, types.Number):

        def impl_list(S, q=0.5, interpolation='linear'):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            rexh__qmwzb = bodo.libs.array_ops.array_op_quantile(arr, q)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            index = bodo.hiframes.pd_index_ext.init_numeric_index(bodo.
                utils.conversion.coerce_to_array(q), None)
            return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
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
        mgvwy__ptic = bodo.libs.array_kernels.unique(arr)
        return bodo.allgatherv(mgvwy__ptic, False)
    return impl


@overload_method(SeriesType, 'describe', inline='always', no_unliteral=True)
def overload_series_describe(S, percentiles=None, include=None, exclude=
    None, datetime_is_numeric=True):
    ggb__psugn = dict(percentiles=percentiles, include=include, exclude=
        exclude, datetime_is_numeric=datetime_is_numeric)
    ngy__olry = dict(percentiles=None, include=None, exclude=None,
        datetime_is_numeric=True)
    check_unsupported_args('Series.describe', ggb__psugn, ngy__olry,
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
        hovo__tlr = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
    else:
        hovo__tlr = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
    ybrom__rjw = '\n'.join(('def impl(', '    S,', '    value=None,',
        '    method=None,', '    axis=None,', '    inplace=False,',
        '    limit=None,', '    downcast=None,', '):',
        '    in_arr = bodo.hiframes.pd_series_ext.get_series_data(S)',
        '    fill_arr = bodo.hiframes.pd_series_ext.get_series_data(value)',
        '    n = len(in_arr)', '    nf = len(fill_arr)',
        "    assert n == nf, 'fillna() requires same length arrays'",
        f'    out_arr = {hovo__tlr}(n, -1)',
        '    for j in numba.parfors.parfor.internal_prange(n):',
        '        s = in_arr[j]',
        '        if bodo.libs.array_kernels.isna(in_arr, j) and not bodo.libs.array_kernels.isna('
        , '            fill_arr, j', '        ):',
        '            s = fill_arr[j]', '        out_arr[j] = s',
        '    bodo.libs.str_arr_ext.move_str_binary_arr_payload(in_arr, out_arr)'
        ))
    lthnd__asce = dict()
    exec(ybrom__rjw, {'bodo': bodo, 'numba': numba}, lthnd__asce)
    hrys__lit = lthnd__asce['impl']
    return hrys__lit


def binary_str_fillna_inplace_impl(is_binary=False):
    if is_binary:
        hovo__tlr = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
    else:
        hovo__tlr = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
    ybrom__rjw = 'def impl(S,\n'
    ybrom__rjw += '     value=None,\n'
    ybrom__rjw += '    method=None,\n'
    ybrom__rjw += '    axis=None,\n'
    ybrom__rjw += '    inplace=False,\n'
    ybrom__rjw += '    limit=None,\n'
    ybrom__rjw += '   downcast=None,\n'
    ybrom__rjw += '):\n'
    ybrom__rjw += (
        '    in_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    ybrom__rjw += '    n = len(in_arr)\n'
    ybrom__rjw += f'    out_arr = {hovo__tlr}(n, -1)\n'
    ybrom__rjw += '    for j in numba.parfors.parfor.internal_prange(n):\n'
    ybrom__rjw += '        s = in_arr[j]\n'
    ybrom__rjw += '        if bodo.libs.array_kernels.isna(in_arr, j):\n'
    ybrom__rjw += '            s = value\n'
    ybrom__rjw += '        out_arr[j] = s\n'
    ybrom__rjw += (
        '    bodo.libs.str_arr_ext.move_str_binary_arr_payload(in_arr, out_arr)\n'
        )
    lthnd__asce = dict()
    exec(ybrom__rjw, {'bodo': bodo, 'numba': numba}, lthnd__asce)
    hrys__lit = lthnd__asce['impl']
    return hrys__lit


def fillna_inplace_series_impl(S, value=None, method=None, axis=None,
    inplace=False, limit=None, downcast=None):
    rprfh__ibfq = bodo.hiframes.pd_series_ext.get_series_data(S)
    tkh__knh = bodo.hiframes.pd_series_ext.get_series_data(value)
    for jtn__frw in numba.parfors.parfor.internal_prange(len(rprfh__ibfq)):
        s = rprfh__ibfq[jtn__frw]
        if bodo.libs.array_kernels.isna(rprfh__ibfq, jtn__frw
            ) and not bodo.libs.array_kernels.isna(tkh__knh, jtn__frw):
            s = tkh__knh[jtn__frw]
        rprfh__ibfq[jtn__frw] = s


def fillna_inplace_impl(S, value=None, method=None, axis=None, inplace=
    False, limit=None, downcast=None):
    rprfh__ibfq = bodo.hiframes.pd_series_ext.get_series_data(S)
    for jtn__frw in numba.parfors.parfor.internal_prange(len(rprfh__ibfq)):
        s = rprfh__ibfq[jtn__frw]
        if bodo.libs.array_kernels.isna(rprfh__ibfq, jtn__frw):
            s = value
        rprfh__ibfq[jtn__frw] = s


def str_fillna_alloc_series_impl(S, value=None, method=None, axis=None,
    inplace=False, limit=None, downcast=None):
    rprfh__ibfq = bodo.hiframes.pd_series_ext.get_series_data(S)
    index = bodo.hiframes.pd_series_ext.get_series_index(S)
    name = bodo.hiframes.pd_series_ext.get_series_name(S)
    tkh__knh = bodo.hiframes.pd_series_ext.get_series_data(value)
    n = len(rprfh__ibfq)
    rexh__qmwzb = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
    for flxhn__xdb in numba.parfors.parfor.internal_prange(n):
        s = rprfh__ibfq[flxhn__xdb]
        if bodo.libs.array_kernels.isna(rprfh__ibfq, flxhn__xdb
            ) and not bodo.libs.array_kernels.isna(tkh__knh, flxhn__xdb):
            s = tkh__knh[flxhn__xdb]
        rexh__qmwzb[flxhn__xdb] = s
        if bodo.libs.array_kernels.isna(rprfh__ibfq, flxhn__xdb
            ) and bodo.libs.array_kernels.isna(tkh__knh, flxhn__xdb):
            bodo.libs.array_kernels.setna(rexh__qmwzb, flxhn__xdb)
    return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb, index, name)


def fillna_series_impl(S, value=None, method=None, axis=None, inplace=False,
    limit=None, downcast=None):
    rprfh__ibfq = bodo.hiframes.pd_series_ext.get_series_data(S)
    index = bodo.hiframes.pd_series_ext.get_series_index(S)
    name = bodo.hiframes.pd_series_ext.get_series_name(S)
    tkh__knh = bodo.hiframes.pd_series_ext.get_series_data(value)
    n = len(rprfh__ibfq)
    rexh__qmwzb = bodo.utils.utils.alloc_type(n, rprfh__ibfq.dtype, (-1,))
    for jtn__frw in numba.parfors.parfor.internal_prange(n):
        s = rprfh__ibfq[jtn__frw]
        if bodo.libs.array_kernels.isna(rprfh__ibfq, jtn__frw
            ) and not bodo.libs.array_kernels.isna(tkh__knh, jtn__frw):
            s = tkh__knh[jtn__frw]
        rexh__qmwzb[jtn__frw] = s
    return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb, index, name)


@overload_method(SeriesType, 'fillna', no_unliteral=True)
def overload_series_fillna(S, value=None, method=None, axis=None, inplace=
    False, limit=None, downcast=None):
    ggb__psugn = dict(limit=limit, downcast=downcast)
    ngy__olry = dict(limit=None, downcast=None)
    check_unsupported_args('Series.fillna', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
    hafh__utgp = not is_overload_none(value)
    cfbe__jfpg = not is_overload_none(method)
    if hafh__utgp and cfbe__jfpg:
        raise BodoError(
            "Series.fillna(): Cannot specify both 'value' and 'method'.")
    if not hafh__utgp and not cfbe__jfpg:
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
    if cfbe__jfpg:
        if is_overload_true(inplace):
            raise BodoError(
                "Series.fillna() with inplace=True not supported with 'method' argument yet."
                )
        dhwi__fcls = (
            "Series.fillna(): 'method' argument if provided must be a constant string and one of ('backfill', 'bfill', 'pad' 'ffill')."
            )
        if not is_overload_constant_str(method):
            raise_bodo_error(dhwi__fcls)
        elif get_overload_const_str(method) not in ('backfill', 'bfill',
            'pad', 'ffill'):
            raise BodoError(dhwi__fcls)
    czvee__ujemm = element_type(S.data)
    uof__ndzgp = None
    if hafh__utgp:
        uof__ndzgp = element_type(types.unliteral(value))
    if uof__ndzgp and not can_replace(czvee__ujemm, uof__ndzgp):
        raise BodoError(
            f'Series.fillna(): Cannot use value type {uof__ndzgp} with series type {czvee__ujemm}'
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
        khfy__wbqkg = to_str_arr_if_dict_array(S.data)
        if isinstance(value, SeriesType):

            def fillna_series_impl(S, value=None, method=None, axis=None,
                inplace=False, limit=None, downcast=None):
                rprfh__ibfq = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                tkh__knh = bodo.hiframes.pd_series_ext.get_series_data(value)
                n = len(rprfh__ibfq)
                rexh__qmwzb = bodo.utils.utils.alloc_type(n, khfy__wbqkg, (-1,)
                    )
                for jtn__frw in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(rprfh__ibfq, jtn__frw
                        ) and bodo.libs.array_kernels.isna(tkh__knh, jtn__frw):
                        bodo.libs.array_kernels.setna(rexh__qmwzb, jtn__frw)
                        continue
                    if bodo.libs.array_kernels.isna(rprfh__ibfq, jtn__frw):
                        rexh__qmwzb[jtn__frw
                            ] = bodo.utils.conversion.unbox_if_timestamp(
                            tkh__knh[jtn__frw])
                        continue
                    rexh__qmwzb[jtn__frw
                        ] = bodo.utils.conversion.unbox_if_timestamp(
                        rprfh__ibfq[jtn__frw])
                return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                    index, name)
            return fillna_series_impl
        if cfbe__jfpg:
            qokb__erv = (types.unicode_type, types.bool_, bodo.datetime64ns,
                bodo.timedelta64ns)
            if not isinstance(czvee__ujemm, (types.Integer, types.Float)
                ) and czvee__ujemm not in qokb__erv:
                raise BodoError(
                    f"Series.fillna(): series of type {czvee__ujemm} are not supported with 'method' argument."
                    )

            def fillna_method_impl(S, value=None, method=None, axis=None,
                inplace=False, limit=None, downcast=None):
                rprfh__ibfq = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                rexh__qmwzb = bodo.libs.array_kernels.ffill_bfill_arr(
                    rprfh__ibfq, method)
                return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                    index, name)
            return fillna_method_impl

        def fillna_impl(S, value=None, method=None, axis=None, inplace=
            False, limit=None, downcast=None):
            value = bodo.utils.conversion.unbox_if_timestamp(value)
            rprfh__ibfq = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            n = len(rprfh__ibfq)
            rexh__qmwzb = bodo.utils.utils.alloc_type(n, khfy__wbqkg, (-1,))
            for jtn__frw in numba.parfors.parfor.internal_prange(n):
                s = bodo.utils.conversion.unbox_if_timestamp(rprfh__ibfq[
                    jtn__frw])
                if bodo.libs.array_kernels.isna(rprfh__ibfq, jtn__frw):
                    s = value
                rexh__qmwzb[jtn__frw] = s
            return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                index, name)
        return fillna_impl


def create_fillna_specific_method_overload(overload_name):

    def overload_series_fillna_specific_method(S, axis=None, inplace=False,
        limit=None, downcast=None):
        nzpv__iraaw = {'ffill': 'ffill', 'bfill': 'bfill', 'pad': 'ffill',
            'backfill': 'bfill'}[overload_name]
        ggb__psugn = dict(limit=limit, downcast=downcast)
        ngy__olry = dict(limit=None, downcast=None)
        check_unsupported_args(f'Series.{overload_name}', ggb__psugn,
            ngy__olry, package_name='pandas', module_name='Series')
        if not (is_overload_none(axis) or is_overload_zero(axis)):
            raise BodoError(
                f'Series.{overload_name}(): axis argument not supported')
        czvee__ujemm = element_type(S.data)
        qokb__erv = (types.unicode_type, types.bool_, bodo.datetime64ns,
            bodo.timedelta64ns)
        if not isinstance(czvee__ujemm, (types.Integer, types.Float)
            ) and czvee__ujemm not in qokb__erv:
            raise BodoError(
                f'Series.{overload_name}(): series of type {czvee__ujemm} are not supported.'
                )

        def impl(S, axis=None, inplace=False, limit=None, downcast=None):
            rprfh__ibfq = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            rexh__qmwzb = bodo.libs.array_kernels.ffill_bfill_arr(rprfh__ibfq,
                nzpv__iraaw)
            return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                index, name)
        return impl
    return overload_series_fillna_specific_method


fillna_specific_methods = 'ffill', 'bfill', 'pad', 'backfill'


def _install_fillna_specific_methods():
    for overload_name in fillna_specific_methods:
        bfxqv__jgcr = create_fillna_specific_method_overload(overload_name)
        overload_method(SeriesType, overload_name, no_unliteral=True)(
            bfxqv__jgcr)


_install_fillna_specific_methods()


def check_unsupported_types(S, to_replace, value):
    if any(bodo.utils.utils.is_array_typ(x, True) for x in [S.dtype,
        to_replace, value]):
        jisgp__cppaq = (
            'Series.replace(): only support with Scalar, List, or Dictionary')
        raise BodoError(jisgp__cppaq)
    elif isinstance(to_replace, types.DictType) and not is_overload_none(value
        ):
        jisgp__cppaq = (
            "Series.replace(): 'value' must be None when 'to_replace' is a dictionary"
            )
        raise BodoError(jisgp__cppaq)
    elif any(isinstance(x, (PandasTimestampType, PDTimeDeltaType)) for x in
        [to_replace, value]):
        jisgp__cppaq = (
            f'Series.replace(): Not supported for types {to_replace} and {value}'
            )
        raise BodoError(jisgp__cppaq)


def series_replace_error_checking(S, to_replace, value, inplace, limit,
    regex, method):
    ggb__psugn = dict(inplace=inplace, limit=limit, regex=regex, method=method)
    hsw__bresc = dict(inplace=False, limit=None, regex=False, method='pad')
    check_unsupported_args('Series.replace', ggb__psugn, hsw__bresc,
        package_name='pandas', module_name='Series')
    check_unsupported_types(S, to_replace, value)


@overload_method(SeriesType, 'replace', inline='always', no_unliteral=True)
def overload_series_replace(S, to_replace=None, value=None, inplace=False,
    limit=None, regex=False, method='pad'):
    series_replace_error_checking(S, to_replace, value, inplace, limit,
        regex, method)
    czvee__ujemm = element_type(S.data)
    if isinstance(to_replace, types.DictType):
        tnp__rosg = element_type(to_replace.key_type)
        uof__ndzgp = element_type(to_replace.value_type)
    else:
        tnp__rosg = element_type(to_replace)
        uof__ndzgp = element_type(value)
    pnu__ogsi = None
    if czvee__ujemm != types.unliteral(tnp__rosg):
        if bodo.utils.typing.equality_always_false(czvee__ujemm, types.
            unliteral(tnp__rosg)
            ) or not bodo.utils.typing.types_equality_exists(czvee__ujemm,
            tnp__rosg):

            def impl(S, to_replace=None, value=None, inplace=False, limit=
                None, regex=False, method='pad'):
                return S.copy()
            return impl
        if isinstance(czvee__ujemm, (types.Float, types.Integer)
            ) or czvee__ujemm == np.bool_:
            pnu__ogsi = czvee__ujemm
    if not can_replace(czvee__ujemm, types.unliteral(uof__ndzgp)):

        def impl(S, to_replace=None, value=None, inplace=False, limit=None,
            regex=False, method='pad'):
            return S.copy()
        return impl
    iqer__hmsy = to_str_arr_if_dict_array(S.data)
    if isinstance(iqer__hmsy, CategoricalArrayType):

        def cat_impl(S, to_replace=None, value=None, inplace=False, limit=
            None, regex=False, method='pad'):
            rprfh__ibfq = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            return bodo.hiframes.pd_series_ext.init_series(rprfh__ibfq.
                replace(to_replace, value), index, name)
        return cat_impl

    def impl(S, to_replace=None, value=None, inplace=False, limit=None,
        regex=False, method='pad'):
        rprfh__ibfq = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        n = len(rprfh__ibfq)
        rexh__qmwzb = bodo.utils.utils.alloc_type(n, iqer__hmsy, (-1,))
        eiru__mafnf = build_replace_dict(to_replace, value, pnu__ogsi)
        for jtn__frw in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(rprfh__ibfq, jtn__frw):
                bodo.libs.array_kernels.setna(rexh__qmwzb, jtn__frw)
                continue
            s = rprfh__ibfq[jtn__frw]
            if s in eiru__mafnf:
                s = eiru__mafnf[s]
            rexh__qmwzb[jtn__frw] = s
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb, index, name
            )
    return impl


def build_replace_dict(to_replace, value, key_dtype_conv):
    pass


@overload(build_replace_dict)
def _build_replace_dict(to_replace, value, key_dtype_conv):
    deil__sye = isinstance(to_replace, (types.Number, Decimal128Type)
        ) or to_replace in [bodo.string_type, types.boolean, bodo.bytes_type]
    aynnr__azb = is_iterable_type(to_replace)
    aox__hux = isinstance(value, (types.Number, Decimal128Type)) or value in [
        bodo.string_type, bodo.bytes_type, types.boolean]
    iln__zuvb = is_iterable_type(value)
    if deil__sye and aox__hux:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                eiru__mafnf = {}
                eiru__mafnf[key_dtype_conv(to_replace)] = value
                return eiru__mafnf
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            eiru__mafnf = {}
            eiru__mafnf[to_replace] = value
            return eiru__mafnf
        return impl
    if aynnr__azb and aox__hux:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                eiru__mafnf = {}
                for rvijr__rutwg in to_replace:
                    eiru__mafnf[key_dtype_conv(rvijr__rutwg)] = value
                return eiru__mafnf
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            eiru__mafnf = {}
            for rvijr__rutwg in to_replace:
                eiru__mafnf[rvijr__rutwg] = value
            return eiru__mafnf
        return impl
    if aynnr__azb and iln__zuvb:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                eiru__mafnf = {}
                assert len(to_replace) == len(value
                    ), 'To_replace and value lengths must be the same'
                for jtn__frw in range(len(to_replace)):
                    eiru__mafnf[key_dtype_conv(to_replace[jtn__frw])] = value[
                        jtn__frw]
                return eiru__mafnf
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            eiru__mafnf = {}
            assert len(to_replace) == len(value
                ), 'To_replace and value lengths must be the same'
            for jtn__frw in range(len(to_replace)):
                eiru__mafnf[to_replace[jtn__frw]] = value[jtn__frw]
            return eiru__mafnf
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
            rexh__qmwzb = bodo.hiframes.series_impl.dt64_arr_sub(arr, bodo.
                hiframes.rolling.shift(arr, periods, False))
            return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                index, name)
        return impl_datetime

    def impl(S, periods=1):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        rexh__qmwzb = arr - bodo.hiframes.rolling.shift(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb, index, name
            )
    return impl


@overload_method(SeriesType, 'explode', inline='always', no_unliteral=True)
def overload_series_explode(S, ignore_index=False):
    from bodo.hiframes.split_impl import string_array_split_view_type
    ggb__psugn = dict(ignore_index=ignore_index)
    fbe__nnxv = dict(ignore_index=False)
    check_unsupported_args('Series.explode', ggb__psugn, fbe__nnxv,
        package_name='pandas', module_name='Series')
    if not (isinstance(S.data, ArrayItemArrayType) or S.data ==
        string_array_split_view_type):
        return lambda S, ignore_index=False: S.copy()

    def impl(S, ignore_index=False):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        qycd__audbd = bodo.utils.conversion.index_to_array(index)
        rexh__qmwzb, psfv__mrua = bodo.libs.array_kernels.explode(arr,
            qycd__audbd)
        mucr__rmi = bodo.utils.conversion.index_from_array(psfv__mrua)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
            mucr__rmi, name)
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
            lhv__pnj = np.empty(len(a), a.dtype)
            numba.parfors.parfor.init_prange()
            n = len(a)
            for jtn__frw in numba.parfors.parfor.internal_prange(n):
                lhv__pnj[jtn__frw] = np.argmax(a[jtn__frw])
            return lhv__pnj
        return impl


@overload(np.argmin, inline='always', no_unliteral=True)
def argmin_overload(a, axis=None, out=None):
    if isinstance(a, types.Array) and is_overload_constant_int(axis
        ) and get_overload_const_int(axis) == 1:

        def impl(a, axis=None, out=None):
            uod__bpn = np.empty(len(a), a.dtype)
            numba.parfors.parfor.init_prange()
            n = len(a)
            for jtn__frw in numba.parfors.parfor.internal_prange(n):
                uod__bpn[jtn__frw] = np.argmin(a[jtn__frw])
            return uod__bpn
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
    ggb__psugn = dict(axis=axis, inplace=inplace, how=how)
    juqv__bui = dict(axis=0, inplace=False, how=None)
    check_unsupported_args('Series.dropna', ggb__psugn, juqv__bui,
        package_name='pandas', module_name='Series')
    if S.dtype == bodo.string_type:

        def dropna_str_impl(S, axis=0, inplace=False, how=None):
            rprfh__ibfq = bodo.hiframes.pd_series_ext.get_series_data(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            vledo__clywj = S.notna().values
            qycd__audbd = bodo.utils.conversion.extract_index_array(S)
            mucr__rmi = bodo.utils.conversion.convert_to_index(qycd__audbd[
                vledo__clywj])
            rexh__qmwzb = (bodo.hiframes.series_kernels.
                _series_dropna_str_alloc_impl_inner(rprfh__ibfq))
            return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                mucr__rmi, name)
        return dropna_str_impl
    else:

        def dropna_impl(S, axis=0, inplace=False, how=None):
            rprfh__ibfq = bodo.hiframes.pd_series_ext.get_series_data(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            qycd__audbd = bodo.utils.conversion.extract_index_array(S)
            vledo__clywj = S.notna().values
            mucr__rmi = bodo.utils.conversion.convert_to_index(qycd__audbd[
                vledo__clywj])
            rexh__qmwzb = rprfh__ibfq[vledo__clywj]
            return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                mucr__rmi, name)
        return dropna_impl


@overload_method(SeriesType, 'shift', inline='always', no_unliteral=True)
def overload_series_shift(S, periods=1, freq=None, axis=0, fill_value=None):
    ggb__psugn = dict(freq=freq, axis=axis, fill_value=fill_value)
    ngy__olry = dict(freq=None, axis=0, fill_value=None)
    check_unsupported_args('Series.shift', ggb__psugn, ngy__olry,
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
        rexh__qmwzb = bodo.hiframes.rolling.shift(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb, index, name
            )
    return impl


@overload_method(SeriesType, 'pct_change', inline='always', no_unliteral=True)
def overload_series_pct_change(S, periods=1, fill_method='pad', limit=None,
    freq=None):
    ggb__psugn = dict(fill_method=fill_method, limit=limit, freq=freq)
    ngy__olry = dict(fill_method='pad', limit=None, freq=None)
    check_unsupported_args('Series.pct_change', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')
    if not is_overload_int(periods):
        raise BodoError(
            'Series.pct_change(): periods argument must be an Integer')

    def impl(S, periods=1, fill_method='pad', limit=None, freq=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        rexh__qmwzb = bodo.hiframes.rolling.pct_change(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb, index, name
            )
    return impl


def create_series_mask_where_overload(func_name):

    def overload_series_mask_where(S, cond, other=np.nan, inplace=False,
        axis=None, level=None, errors='raise', try_cast=False):
        _validate_arguments_mask_where(f'Series.{func_name}', S, cond,
            other, inplace, axis, level, errors, try_cast)
        if is_overload_constant_nan(other):
            iovll__hnl = 'None'
        else:
            iovll__hnl = 'other'
        ybrom__rjw = """def impl(S, cond, other=np.nan, inplace=False, axis=None, level=None, errors='raise',try_cast=False):
"""
        if func_name == 'mask':
            ybrom__rjw += '  cond = ~cond\n'
        ybrom__rjw += (
            '  arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        ybrom__rjw += (
            '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        ybrom__rjw += (
            '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        ybrom__rjw += (
            f'  out_arr = bodo.hiframes.series_impl.where_impl(cond, arr, {iovll__hnl})\n'
            )
        ybrom__rjw += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        nhc__gmjhk = {}
        exec(ybrom__rjw, {'bodo': bodo, 'np': np}, nhc__gmjhk)
        impl = nhc__gmjhk['impl']
        return impl
    return overload_series_mask_where


def _install_series_mask_where_overload():
    for func_name in ('mask', 'where'):
        bfxqv__jgcr = create_series_mask_where_overload(func_name)
        overload_method(SeriesType, func_name, no_unliteral=True)(bfxqv__jgcr)


_install_series_mask_where_overload()


def _validate_arguments_mask_where(func_name, S, cond, other, inplace, axis,
    level, errors, try_cast):
    ggb__psugn = dict(inplace=inplace, level=level, errors=errors, try_cast
        =try_cast)
    ngy__olry = dict(inplace=False, level=None, errors='raise', try_cast=False)
    check_unsupported_args(f'{func_name}', ggb__psugn, ngy__olry,
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
    qvcb__wrxwu = is_overload_constant_nan(other)
    if not (is_default or qvcb__wrxwu or is_scalar_type(other) or 
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
            ccihp__gfr = arr.dtype.elem_type
        else:
            ccihp__gfr = arr.dtype
        if is_iterable_type(other):
            zllx__atuh = other.dtype
        elif qvcb__wrxwu:
            zllx__atuh = types.float64
        else:
            zllx__atuh = types.unliteral(other)
        if not qvcb__wrxwu and not is_common_scalar_dtype([ccihp__gfr,
            zllx__atuh]):
            raise BodoError(
                f"{func_name}() series and 'other' must share a common type.")


def create_explicit_binary_op_overload(op):

    def overload_series_explicit_binary_op(S, other, level=None, fill_value
        =None, axis=0):
        ggb__psugn = dict(level=level, axis=axis)
        ngy__olry = dict(level=None, axis=0)
        check_unsupported_args('series.{}'.format(op.__name__), ggb__psugn,
            ngy__olry, package_name='pandas', module_name='Series')
        kno__oqwh = other == string_type or is_overload_constant_str(other)
        tmni__yak = is_iterable_type(other) and other.dtype == string_type
        qmhlh__wsdjk = S.dtype == string_type and (op == operator.add and (
            kno__oqwh or tmni__yak) or op == operator.mul and isinstance(
            other, types.Integer))
        wkbj__eyi = S.dtype == bodo.timedelta64ns
        mmsti__lkt = S.dtype == bodo.datetime64ns
        pie__gkgh = is_iterable_type(other) and (other.dtype ==
            datetime_timedelta_type or other.dtype == bodo.timedelta64ns)
        jarnm__iud = is_iterable_type(other) and (other.dtype ==
            datetime_datetime_type or other.dtype == pd_timestamp_type or 
            other.dtype == bodo.datetime64ns)
        awnti__cpz = wkbj__eyi and (pie__gkgh or jarnm__iud
            ) or mmsti__lkt and pie__gkgh
        awnti__cpz = awnti__cpz and op == operator.add
        if not (isinstance(S.dtype, types.Number) or qmhlh__wsdjk or awnti__cpz
            ):
            raise BodoError(f'Unsupported types for Series.{op.__name__}')
        oddm__uhdmg = numba.core.registry.cpu_target.typing_context
        if is_scalar_type(other):
            args = S.data, other
            iqer__hmsy = oddm__uhdmg.resolve_function_type(op, args, {}
                ).return_type
            if isinstance(S.data, IntegerArrayType
                ) and iqer__hmsy == types.Array(types.bool_, 1, 'C'):
                iqer__hmsy = boolean_array

            def impl_scalar(S, other, level=None, fill_value=None, axis=0):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                numba.parfors.parfor.init_prange()
                other = bodo.utils.conversion.unbox_if_timestamp(other)
                n = len(arr)
                rexh__qmwzb = bodo.utils.utils.alloc_type(n, iqer__hmsy, (-1,))
                for jtn__frw in numba.parfors.parfor.internal_prange(n):
                    syk__vedvw = bodo.libs.array_kernels.isna(arr, jtn__frw)
                    if syk__vedvw:
                        if fill_value is None:
                            bodo.libs.array_kernels.setna(rexh__qmwzb, jtn__frw
                                )
                        else:
                            rexh__qmwzb[jtn__frw] = op(fill_value, other)
                    else:
                        rexh__qmwzb[jtn__frw] = op(arr[jtn__frw], other)
                return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                    index, name)
            return impl_scalar
        args = S.data, types.Array(other.dtype, 1, 'C')
        iqer__hmsy = oddm__uhdmg.resolve_function_type(op, args, {}
            ).return_type
        if isinstance(S.data, IntegerArrayType) and iqer__hmsy == types.Array(
            types.bool_, 1, 'C'):
            iqer__hmsy = boolean_array

        def impl(S, other, level=None, fill_value=None, axis=0):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            arw__yuc = bodo.utils.conversion.coerce_to_array(other)
            numba.parfors.parfor.init_prange()
            n = len(arr)
            rexh__qmwzb = bodo.utils.utils.alloc_type(n, iqer__hmsy, (-1,))
            for jtn__frw in numba.parfors.parfor.internal_prange(n):
                syk__vedvw = bodo.libs.array_kernels.isna(arr, jtn__frw)
                apb__spxs = bodo.libs.array_kernels.isna(arw__yuc, jtn__frw)
                if syk__vedvw and apb__spxs:
                    bodo.libs.array_kernels.setna(rexh__qmwzb, jtn__frw)
                elif syk__vedvw:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(rexh__qmwzb, jtn__frw)
                    else:
                        rexh__qmwzb[jtn__frw] = op(fill_value, arw__yuc[
                            jtn__frw])
                elif apb__spxs:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(rexh__qmwzb, jtn__frw)
                    else:
                        rexh__qmwzb[jtn__frw] = op(arr[jtn__frw], fill_value)
                else:
                    rexh__qmwzb[jtn__frw] = op(arr[jtn__frw], arw__yuc[
                        jtn__frw])
            return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
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
        oddm__uhdmg = numba.core.registry.cpu_target.typing_context
        if isinstance(other, types.Number):
            args = other, S.data
            iqer__hmsy = oddm__uhdmg.resolve_function_type(op, args, {}
                ).return_type
            if isinstance(S.data, IntegerArrayType
                ) and iqer__hmsy == types.Array(types.bool_, 1, 'C'):
                iqer__hmsy = boolean_array

            def impl_scalar(S, other, level=None, fill_value=None, axis=0):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                numba.parfors.parfor.init_prange()
                n = len(arr)
                rexh__qmwzb = bodo.utils.utils.alloc_type(n, iqer__hmsy, None)
                for jtn__frw in numba.parfors.parfor.internal_prange(n):
                    syk__vedvw = bodo.libs.array_kernels.isna(arr, jtn__frw)
                    if syk__vedvw:
                        if fill_value is None:
                            bodo.libs.array_kernels.setna(rexh__qmwzb, jtn__frw
                                )
                        else:
                            rexh__qmwzb[jtn__frw] = op(other, fill_value)
                    else:
                        rexh__qmwzb[jtn__frw] = op(other, arr[jtn__frw])
                return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                    index, name)
            return impl_scalar
        args = types.Array(other.dtype, 1, 'C'), S.data
        iqer__hmsy = oddm__uhdmg.resolve_function_type(op, args, {}
            ).return_type
        if isinstance(S.data, IntegerArrayType) and iqer__hmsy == types.Array(
            types.bool_, 1, 'C'):
            iqer__hmsy = boolean_array

        def impl(S, other, level=None, fill_value=None, axis=0):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            arw__yuc = bodo.hiframes.pd_series_ext.get_series_data(other)
            numba.parfors.parfor.init_prange()
            n = len(arr)
            rexh__qmwzb = bodo.utils.utils.alloc_type(n, iqer__hmsy, None)
            for jtn__frw in numba.parfors.parfor.internal_prange(n):
                syk__vedvw = bodo.libs.array_kernels.isna(arr, jtn__frw)
                apb__spxs = bodo.libs.array_kernels.isna(arw__yuc, jtn__frw)
                rexh__qmwzb[jtn__frw] = op(arw__yuc[jtn__frw], arr[jtn__frw])
                if syk__vedvw and apb__spxs:
                    bodo.libs.array_kernels.setna(rexh__qmwzb, jtn__frw)
                elif syk__vedvw:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(rexh__qmwzb, jtn__frw)
                    else:
                        rexh__qmwzb[jtn__frw] = op(arw__yuc[jtn__frw],
                            fill_value)
                elif apb__spxs:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(rexh__qmwzb, jtn__frw)
                    else:
                        rexh__qmwzb[jtn__frw] = op(fill_value, arr[jtn__frw])
                else:
                    rexh__qmwzb[jtn__frw] = op(arw__yuc[jtn__frw], arr[
                        jtn__frw])
            return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
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
    for op, fmgy__orurk in explicit_binop_funcs_two_ways.items():
        for name in fmgy__orurk:
            bfxqv__jgcr = create_explicit_binary_op_overload(op)
            bbyo__lfw = create_explicit_binary_reverse_op_overload(op)
            gxh__xadoo = 'r' + name
            overload_method(SeriesType, name, no_unliteral=True)(bfxqv__jgcr)
            overload_method(SeriesType, gxh__xadoo, no_unliteral=True)(
                bbyo__lfw)
            explicit_binop_funcs.add(name)
    for op, name in explicit_binop_funcs_single.items():
        bfxqv__jgcr = create_explicit_binary_op_overload(op)
        overload_method(SeriesType, name, no_unliteral=True)(bfxqv__jgcr)
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
                fytw__impo = (bodo.utils.conversion.
                    get_array_if_series_or_index(rhs))
                rexh__qmwzb = dt64_arr_sub(arr, fytw__impo)
                return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
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
                rexh__qmwzb = np.empty(n, np.dtype('datetime64[ns]'))
                for jtn__frw in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(arr, jtn__frw):
                        bodo.libs.array_kernels.setna(rexh__qmwzb, jtn__frw)
                        continue
                    gpuv__lcg = (bodo.hiframes.pd_timestamp_ext.
                        convert_datetime64_to_timestamp(arr[jtn__frw]))
                    sseoi__knmn = op(gpuv__lcg, rhs)
                    rexh__qmwzb[jtn__frw
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        sseoi__knmn.value)
                return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
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
                    fytw__impo = (bodo.utils.conversion.
                        get_array_if_series_or_index(rhs))
                    rexh__qmwzb = op(arr, bodo.utils.conversion.
                        unbox_if_timestamp(fytw__impo))
                    return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                        index, name)
                return impl

            def impl(lhs, rhs):
                arr = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                index = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                name = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                fytw__impo = (bodo.utils.conversion.
                    get_array_if_series_or_index(rhs))
                rexh__qmwzb = op(arr, fytw__impo)
                return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                    index, name)
            return impl
        if isinstance(rhs, SeriesType):
            if rhs.dtype in [bodo.datetime64ns, bodo.timedelta64ns]:

                def impl(lhs, rhs):
                    arr = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                    index = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                    name = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                    uhm__zxx = (bodo.utils.conversion.
                        get_array_if_series_or_index(lhs))
                    rexh__qmwzb = op(bodo.utils.conversion.
                        unbox_if_timestamp(uhm__zxx), arr)
                    return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                        index, name)
                return impl

            def impl(lhs, rhs):
                arr = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                index = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                name = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                uhm__zxx = bodo.utils.conversion.get_array_if_series_or_index(
                    lhs)
                rexh__qmwzb = op(uhm__zxx, arr)
                return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                    index, name)
            return impl
    return overload_series_binary_op


skips = list(explicit_binop_funcs_two_ways.keys()) + list(
    explicit_binop_funcs_single.keys()) + split_logical_binops_funcs


def _install_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_binary_ops:
        if op in skips:
            continue
        bfxqv__jgcr = create_binary_op_overload(op)
        overload(op)(bfxqv__jgcr)


_install_binary_ops()


def dt64_arr_sub(arg1, arg2):
    return arg1 - arg2


@overload(dt64_arr_sub, no_unliteral=True)
def overload_dt64_arr_sub(arg1, arg2):
    assert arg1 == types.Array(bodo.datetime64ns, 1, 'C'
        ) and arg2 == types.Array(bodo.datetime64ns, 1, 'C')
    uyxav__knm = np.dtype('timedelta64[ns]')

    def impl(arg1, arg2):
        numba.parfors.parfor.init_prange()
        n = len(arg1)
        S = np.empty(n, uyxav__knm)
        for jtn__frw in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(arg1, jtn__frw
                ) or bodo.libs.array_kernels.isna(arg2, jtn__frw):
                bodo.libs.array_kernels.setna(S, jtn__frw)
                continue
            S[jtn__frw
                ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                bodo.hiframes.pd_timestamp_ext.dt64_to_integer(arg1[
                jtn__frw]) - bodo.hiframes.pd_timestamp_ext.dt64_to_integer
                (arg2[jtn__frw]))
        return S
    return impl


def create_inplace_binary_op_overload(op):

    def overload_series_inplace_binary_op(S, other):
        if isinstance(S, SeriesType) or isinstance(other, SeriesType):

            def impl(S, other):
                arr = bodo.utils.conversion.get_array_if_series_or_index(S)
                arw__yuc = bodo.utils.conversion.get_array_if_series_or_index(
                    other)
                op(arr, arw__yuc)
                return S
            return impl
    return overload_series_inplace_binary_op


def _install_inplace_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_inplace_binary_ops:
        bfxqv__jgcr = create_inplace_binary_op_overload(op)
        overload(op, no_unliteral=True)(bfxqv__jgcr)


_install_inplace_binary_ops()


def create_unary_op_overload(op):

    def overload_series_unary_op(S):
        if isinstance(S, SeriesType):

            def impl(S):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                rexh__qmwzb = op(arr)
                return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                    index, name)
            return impl
    return overload_series_unary_op


def _install_unary_ops():
    for op in bodo.hiframes.pd_series_ext.series_unary_ops:
        bfxqv__jgcr = create_unary_op_overload(op)
        overload(op, no_unliteral=True)(bfxqv__jgcr)


_install_unary_ops()


def create_ufunc_overload(ufunc):
    if ufunc.nin == 1:

        def overload_series_ufunc_nin_1(S):
            if isinstance(S, SeriesType):

                def impl(S):
                    arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                    index = bodo.hiframes.pd_series_ext.get_series_index(S)
                    name = bodo.hiframes.pd_series_ext.get_series_name(S)
                    rexh__qmwzb = ufunc(arr)
                    return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
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
                    arw__yuc = (bodo.utils.conversion.
                        get_array_if_series_or_index(S2))
                    rexh__qmwzb = ufunc(arr, arw__yuc)
                    return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                        index, name)
                return impl
            elif isinstance(S2, SeriesType):

                def impl(S1, S2):
                    arr = bodo.utils.conversion.get_array_if_series_or_index(S1
                        )
                    arw__yuc = bodo.hiframes.pd_series_ext.get_series_data(S2)
                    index = bodo.hiframes.pd_series_ext.get_series_index(S2)
                    name = bodo.hiframes.pd_series_ext.get_series_name(S2)
                    rexh__qmwzb = ufunc(arr, arw__yuc)
                    return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                        index, name)
                return impl
        return overload_series_ufunc_nin_2
    else:
        raise RuntimeError(
            "Don't know how to register ufuncs from ufunc_db with arity > 2")


def _install_np_ufuncs():
    import numba.np.ufunc_db
    for ufunc in numba.np.ufunc_db.get_ufuncs():
        bfxqv__jgcr = create_ufunc_overload(ufunc)
        overload(ufunc, no_unliteral=True)(bfxqv__jgcr)


_install_np_ufuncs()


def argsort(A):
    return np.argsort(A)


@overload(argsort, no_unliteral=True)
def overload_argsort(A):

    def impl(A):
        n = len(A)
        mebx__hyyu = bodo.libs.str_arr_ext.to_list_if_immutable_arr((A.copy(),)
            )
        tkpss__gerj = np.arange(n),
        bodo.libs.timsort.sort(mebx__hyyu, 0, n, tkpss__gerj)
        return tkpss__gerj[0]
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
        hrsz__gbo = get_overload_const_str(downcast)
        if hrsz__gbo in ('integer', 'signed'):
            out_dtype = types.int64
        elif hrsz__gbo == 'unsigned':
            out_dtype = types.uint64
        else:
            assert hrsz__gbo == 'float'
    if isinstance(arg_a, (types.Array, IntegerArrayType)):
        return lambda arg_a, errors='raise', downcast=None: arg_a.astype(
            out_dtype)
    if isinstance(arg_a, SeriesType):

        def impl_series(arg_a, errors='raise', downcast=None):
            rprfh__ibfq = bodo.hiframes.pd_series_ext.get_series_data(arg_a)
            index = bodo.hiframes.pd_series_ext.get_series_index(arg_a)
            name = bodo.hiframes.pd_series_ext.get_series_name(arg_a)
            rexh__qmwzb = pd.to_numeric(rprfh__ibfq, errors, downcast)
            return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                index, name)
        return impl_series
    if not is_str_arr_type(arg_a):
        raise BodoError(f'pd.to_numeric(): invalid argument type {arg_a}')
    if out_dtype == types.float64:

        def to_numeric_float_impl(arg_a, errors='raise', downcast=None):
            numba.parfors.parfor.init_prange()
            n = len(arg_a)
            ina__zitlk = np.empty(n, np.float64)
            for jtn__frw in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arg_a, jtn__frw):
                    bodo.libs.array_kernels.setna(ina__zitlk, jtn__frw)
                else:
                    bodo.libs.str_arr_ext.str_arr_item_to_numeric(ina__zitlk,
                        jtn__frw, arg_a, jtn__frw)
            return ina__zitlk
        return to_numeric_float_impl
    else:

        def to_numeric_int_impl(arg_a, errors='raise', downcast=None):
            numba.parfors.parfor.init_prange()
            n = len(arg_a)
            ina__zitlk = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)
            for jtn__frw in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arg_a, jtn__frw):
                    bodo.libs.array_kernels.setna(ina__zitlk, jtn__frw)
                else:
                    bodo.libs.str_arr_ext.str_arr_item_to_numeric(ina__zitlk,
                        jtn__frw, arg_a, jtn__frw)
            return ina__zitlk
        return to_numeric_int_impl


def series_filter_bool(arr, bool_arr):
    return arr[bool_arr]


@infer_global(series_filter_bool)
class SeriesFilterBoolInfer(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 2
        kiume__oml = if_series_to_array_type(args[0])
        if isinstance(kiume__oml, types.Array) and isinstance(kiume__oml.
            dtype, types.Integer):
            kiume__oml = types.Array(types.float64, 1, 'C')
        return kiume__oml(*args)


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
    ikdzo__qsrfp = bodo.utils.utils.is_array_typ(x, True)
    vrex__fll = bodo.utils.utils.is_array_typ(y, True)
    ybrom__rjw = 'def _impl(condition, x, y):\n'
    if isinstance(condition, SeriesType):
        ybrom__rjw += (
            '  condition = bodo.hiframes.pd_series_ext.get_series_data(condition)\n'
            )
    if ikdzo__qsrfp and not bodo.utils.utils.is_array_typ(x, False):
        ybrom__rjw += '  x = bodo.utils.conversion.coerce_to_array(x)\n'
    if vrex__fll and not bodo.utils.utils.is_array_typ(y, False):
        ybrom__rjw += '  y = bodo.utils.conversion.coerce_to_array(y)\n'
    ybrom__rjw += '  n = len(condition)\n'
    btjo__mhfz = x.dtype if ikdzo__qsrfp else types.unliteral(x)
    yqw__ahqfs = y.dtype if vrex__fll else types.unliteral(y)
    if not isinstance(x, CategoricalArrayType):
        btjo__mhfz = element_type(x)
    if not isinstance(y, CategoricalArrayType):
        yqw__ahqfs = element_type(y)

    def get_data(x):
        if isinstance(x, SeriesType):
            return x.data
        elif isinstance(x, types.Array):
            return x
        return types.unliteral(x)
    cnz__lwqhv = get_data(x)
    owuyk__xetwt = get_data(y)
    is_nullable = any(bodo.utils.typing.is_nullable(tkpss__gerj) for
        tkpss__gerj in [cnz__lwqhv, owuyk__xetwt])
    if owuyk__xetwt == types.none:
        if isinstance(btjo__mhfz, types.Number):
            out_dtype = types.Array(types.float64, 1, 'C')
        else:
            out_dtype = to_nullable_type(x)
    elif cnz__lwqhv == owuyk__xetwt and not is_nullable:
        out_dtype = dtype_to_array_type(btjo__mhfz)
    elif btjo__mhfz == string_type or yqw__ahqfs == string_type:
        out_dtype = bodo.string_array_type
    elif cnz__lwqhv == bytes_type or (ikdzo__qsrfp and btjo__mhfz == bytes_type
        ) and (owuyk__xetwt == bytes_type or vrex__fll and yqw__ahqfs ==
        bytes_type):
        out_dtype = binary_array_type
    elif isinstance(btjo__mhfz, bodo.PDCategoricalDtype):
        out_dtype = None
    elif btjo__mhfz in [bodo.timedelta64ns, bodo.datetime64ns]:
        out_dtype = types.Array(btjo__mhfz, 1, 'C')
    elif yqw__ahqfs in [bodo.timedelta64ns, bodo.datetime64ns]:
        out_dtype = types.Array(yqw__ahqfs, 1, 'C')
    else:
        out_dtype = numba.from_dtype(np.promote_types(numba.np.
            numpy_support.as_dtype(btjo__mhfz), numba.np.numpy_support.
            as_dtype(yqw__ahqfs)))
        out_dtype = types.Array(out_dtype, 1, 'C')
        if is_nullable:
            out_dtype = bodo.utils.typing.to_nullable_type(out_dtype)
    if isinstance(btjo__mhfz, bodo.PDCategoricalDtype):
        hilug__ree = 'x'
    else:
        hilug__ree = 'out_dtype'
    ybrom__rjw += (
        f'  out_arr = bodo.utils.utils.alloc_type(n, {hilug__ree}, (-1,))\n')
    if isinstance(btjo__mhfz, bodo.PDCategoricalDtype):
        ybrom__rjw += """  out_codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(out_arr)
"""
        ybrom__rjw += (
            '  x_codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(x)\n'
            )
    ybrom__rjw += '  for j in numba.parfors.parfor.internal_prange(n):\n'
    ybrom__rjw += (
        '    if not bodo.libs.array_kernels.isna(condition, j) and condition[j]:\n'
        )
    if ikdzo__qsrfp:
        ybrom__rjw += '      if bodo.libs.array_kernels.isna(x, j):\n'
        ybrom__rjw += '        setna(out_arr, j)\n'
        ybrom__rjw += '        continue\n'
    if isinstance(btjo__mhfz, bodo.PDCategoricalDtype):
        ybrom__rjw += '      out_codes[j] = x_codes[j]\n'
    else:
        ybrom__rjw += (
            '      out_arr[j] = bodo.utils.conversion.unbox_if_timestamp({})\n'
            .format('x[j]' if ikdzo__qsrfp else 'x'))
    ybrom__rjw += '    else:\n'
    if vrex__fll:
        ybrom__rjw += '      if bodo.libs.array_kernels.isna(y, j):\n'
        ybrom__rjw += '        setna(out_arr, j)\n'
        ybrom__rjw += '        continue\n'
    if owuyk__xetwt == types.none:
        if isinstance(btjo__mhfz, bodo.PDCategoricalDtype):
            ybrom__rjw += '      out_codes[j] = -1\n'
        else:
            ybrom__rjw += '      setna(out_arr, j)\n'
    else:
        ybrom__rjw += (
            '      out_arr[j] = bodo.utils.conversion.unbox_if_timestamp({})\n'
            .format('y[j]' if vrex__fll else 'y'))
    ybrom__rjw += '  return out_arr\n'
    nhc__gmjhk = {}
    exec(ybrom__rjw, {'bodo': bodo, 'numba': numba, 'setna': bodo.libs.
        array_kernels.setna, 'np': np, 'out_dtype': out_dtype}, nhc__gmjhk)
    kong__wzta = nhc__gmjhk['_impl']
    return kong__wzta


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
        vdvsz__bhx = choicelist.dtype
        if not bodo.utils.utils.is_array_typ(vdvsz__bhx, True):
            raise BodoError(
                "np.select(): 'choicelist' argument must be list or tuple of series/arrays types"
                )
        if is_series_type(vdvsz__bhx):
            jalu__rrm = vdvsz__bhx.data.dtype
        else:
            jalu__rrm = vdvsz__bhx.dtype
        if isinstance(jalu__rrm, bodo.PDCategoricalDtype):
            raise BodoError(
                'np.select(): data with choicelist of type Categorical not yet supported'
                )
        etv__rgolw = vdvsz__bhx
    else:
        nmys__klb = []
        for vdvsz__bhx in choicelist:
            if not bodo.utils.utils.is_array_typ(vdvsz__bhx, True):
                raise BodoError(
                    "np.select(): 'choicelist' argument must be list or tuple of series/arrays types"
                    )
            if is_series_type(vdvsz__bhx):
                jalu__rrm = vdvsz__bhx.data.dtype
            else:
                jalu__rrm = vdvsz__bhx.dtype
            if isinstance(jalu__rrm, bodo.PDCategoricalDtype):
                raise BodoError(
                    'np.select(): data with choicelist of type Categorical not yet supported'
                    )
            nmys__klb.append(jalu__rrm)
        if not is_common_scalar_dtype(nmys__klb):
            raise BodoError(
                f"np.select(): 'choicelist' items must be arrays with a commmon data type. Found a tuple with the following data types {choicelist}."
                )
        etv__rgolw = choicelist[0]
    if is_series_type(etv__rgolw):
        etv__rgolw = etv__rgolw.data
    if is_overload_constant_int(default) and get_overload_const_int(default
        ) == 0:
        pass
    else:
        if not is_scalar_type(default):
            raise BodoError(
                "np.select(): 'default' argument must be scalar type")
        if not (is_common_scalar_dtype([default, etv__rgolw.dtype]) or 
            default == types.none or is_overload_constant_nan(default)):
            raise BodoError(
                f"np.select(): 'default' is not type compatible with the array types in choicelist. Choicelist type: {choicelist}, Default type: {default}"
                )
    if not (isinstance(etv__rgolw, types.Array) or isinstance(etv__rgolw,
        BooleanArrayType) or isinstance(etv__rgolw, IntegerArrayType) or 
        bodo.utils.utils.is_array_typ(etv__rgolw, False) and etv__rgolw.
        dtype in [bodo.string_type, bodo.bytes_type]):
        raise BodoError(
            f'np.select(): data with choicelist of type {etv__rgolw} not yet supported'
            )


@overload(np.select)
def overload_np_select(condlist, choicelist, default=0):
    _verify_np_select_arg_typs(condlist, choicelist, default)
    egftp__akav = isinstance(choicelist, (types.List, types.UniTuple)
        ) and isinstance(condlist, (types.List, types.UniTuple))
    if isinstance(choicelist, (types.List, types.UniTuple)):
        xijfj__bvktc = choicelist.dtype
    else:
        qsn__ldgji = False
        nmys__klb = []
        for vdvsz__bhx in choicelist:
            if is_nullable_type(vdvsz__bhx):
                qsn__ldgji = True
            if is_series_type(vdvsz__bhx):
                jalu__rrm = vdvsz__bhx.data.dtype
            else:
                jalu__rrm = vdvsz__bhx.dtype
            if isinstance(jalu__rrm, bodo.PDCategoricalDtype):
                raise BodoError(
                    'np.select(): data with choicelist of type Categorical not yet supported'
                    )
            nmys__klb.append(jalu__rrm)
        niuch__ldon, wfw__hqh = get_common_scalar_dtype(nmys__klb)
        if not wfw__hqh:
            raise BodoError('Internal error in overload_np_select')
        tkky__devn = dtype_to_array_type(niuch__ldon)
        if qsn__ldgji:
            tkky__devn = to_nullable_type(tkky__devn)
        xijfj__bvktc = tkky__devn
    if isinstance(xijfj__bvktc, SeriesType):
        xijfj__bvktc = xijfj__bvktc.data
    if is_overload_constant_int(default) and get_overload_const_int(default
        ) == 0:
        ydp__iped = True
    else:
        ydp__iped = False
    lxco__mnma = False
    bio__euxk = False
    if ydp__iped:
        if isinstance(xijfj__bvktc.dtype, types.Number):
            pass
        elif xijfj__bvktc.dtype == types.bool_:
            bio__euxk = True
        else:
            lxco__mnma = True
            xijfj__bvktc = to_nullable_type(xijfj__bvktc)
    elif default == types.none or is_overload_constant_nan(default):
        lxco__mnma = True
        xijfj__bvktc = to_nullable_type(xijfj__bvktc)
    ybrom__rjw = 'def np_select_impl(condlist, choicelist, default=0):\n'
    ybrom__rjw += '  if len(condlist) != len(choicelist):\n'
    ybrom__rjw += """    raise ValueError('list of cases must be same length as list of conditions')
"""
    ybrom__rjw += '  output_len = len(choicelist[0])\n'
    ybrom__rjw += (
        '  out = bodo.utils.utils.alloc_type(output_len, alloc_typ, (-1,))\n')
    ybrom__rjw += '  for i in range(output_len):\n'
    if lxco__mnma:
        ybrom__rjw += '    bodo.libs.array_kernels.setna(out, i)\n'
    elif bio__euxk:
        ybrom__rjw += '    out[i] = False\n'
    else:
        ybrom__rjw += '    out[i] = default\n'
    if egftp__akav:
        ybrom__rjw += '  for i in range(len(condlist) - 1, -1, -1):\n'
        ybrom__rjw += '    cond = condlist[i]\n'
        ybrom__rjw += '    choice = choicelist[i]\n'
        ybrom__rjw += '    out = np.where(cond, choice, out)\n'
    else:
        for jtn__frw in range(len(choicelist) - 1, -1, -1):
            ybrom__rjw += f'  cond = condlist[{jtn__frw}]\n'
            ybrom__rjw += f'  choice = choicelist[{jtn__frw}]\n'
            ybrom__rjw += f'  out = np.where(cond, choice, out)\n'
    ybrom__rjw += '  return out'
    nhc__gmjhk = dict()
    exec(ybrom__rjw, {'bodo': bodo, 'numba': numba, 'setna': bodo.libs.
        array_kernels.setna, 'np': np, 'alloc_typ': xijfj__bvktc}, nhc__gmjhk)
    impl = nhc__gmjhk['np_select_impl']
    return impl


@overload_method(SeriesType, 'duplicated', inline='always', no_unliteral=True)
def overload_series_duplicated(S, keep='first'):

    def impl(S, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        rexh__qmwzb = bodo.libs.array_kernels.duplicated((arr,))
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb, index, name
            )
    return impl


@overload_method(SeriesType, 'drop_duplicates', inline='always',
    no_unliteral=True)
def overload_series_drop_duplicates(S, subset=None, keep='first', inplace=False
    ):
    ggb__psugn = dict(subset=subset, keep=keep, inplace=inplace)
    ngy__olry = dict(subset=None, keep='first', inplace=False)
    check_unsupported_args('Series.drop_duplicates', ggb__psugn, ngy__olry,
        package_name='pandas', module_name='Series')

    def impl(S, subset=None, keep='first', inplace=False):
        mqm__xxxkn = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(S))
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        (mqm__xxxkn,), qycd__audbd = bodo.libs.array_kernels.drop_duplicates((
            mqm__xxxkn,), index, 1)
        index = bodo.utils.conversion.index_from_array(qycd__audbd)
        return bodo.hiframes.pd_series_ext.init_series(mqm__xxxkn, index, name)
    return impl


@overload_method(SeriesType, 'between', inline='always', no_unliteral=True)
def overload_series_between(S, left, right, inclusive='both'):
    zdguw__fgwk = element_type(S.data)
    if not is_common_scalar_dtype([zdguw__fgwk, left]):
        raise_bodo_error(
            "Series.between(): 'left' must be compariable with the Series data"
            )
    if not is_common_scalar_dtype([zdguw__fgwk, right]):
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
        rexh__qmwzb = np.empty(n, np.bool_)
        for jtn__frw in numba.parfors.parfor.internal_prange(n):
            gtovl__bepi = bodo.utils.conversion.box_if_dt64(arr[jtn__frw])
            if inclusive == 'both':
                rexh__qmwzb[jtn__frw
                    ] = gtovl__bepi <= right and gtovl__bepi >= left
            else:
                rexh__qmwzb[jtn__frw
                    ] = gtovl__bepi < right and gtovl__bepi > left
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb, index, name
            )
    return impl


@overload_method(SeriesType, 'repeat', inline='always', no_unliteral=True)
def overload_series_repeat(S, repeats, axis=None):
    ggb__psugn = dict(axis=axis)
    ngy__olry = dict(axis=None)
    check_unsupported_args('Series.repeat', ggb__psugn, ngy__olry,
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
            qycd__audbd = bodo.utils.conversion.index_to_array(index)
            rexh__qmwzb = bodo.libs.array_kernels.repeat_kernel(arr, repeats)
            psfv__mrua = bodo.libs.array_kernels.repeat_kernel(qycd__audbd,
                repeats)
            mucr__rmi = bodo.utils.conversion.index_from_array(psfv__mrua)
            return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
                mucr__rmi, name)
        return impl_int

    def impl_arr(S, repeats, axis=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        qycd__audbd = bodo.utils.conversion.index_to_array(index)
        repeats = bodo.utils.conversion.coerce_to_array(repeats)
        rexh__qmwzb = bodo.libs.array_kernels.repeat_kernel(arr, repeats)
        psfv__mrua = bodo.libs.array_kernels.repeat_kernel(qycd__audbd, repeats
            )
        mucr__rmi = bodo.utils.conversion.index_from_array(psfv__mrua)
        return bodo.hiframes.pd_series_ext.init_series(rexh__qmwzb,
            mucr__rmi, name)
    return impl_arr


@overload_method(SeriesType, 'to_dict', no_unliteral=True)
def overload_to_dict(S, into=None):

    def impl(S, into=None):
        tkpss__gerj = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(S))
        n = len(tkpss__gerj)
        eigbg__mjaiu = {}
        for jtn__frw in range(n):
            gtovl__bepi = bodo.utils.conversion.box_if_dt64(tkpss__gerj[
                jtn__frw])
            eigbg__mjaiu[index[jtn__frw]] = gtovl__bepi
        return eigbg__mjaiu
    return impl


@overload_method(SeriesType, 'to_frame', inline='always', no_unliteral=True)
def overload_series_to_frame(S, name=None):
    dhwi__fcls = (
        "Series.to_frame(): output column name should be known at compile time. Set 'name' to a constant value."
        )
    if is_overload_none(name):
        if is_literal_type(S.name_typ):
            loop__jmr = get_literal_value(S.name_typ)
        else:
            raise_bodo_error(dhwi__fcls)
    elif is_literal_type(name):
        loop__jmr = get_literal_value(name)
    else:
        raise_bodo_error(dhwi__fcls)
    loop__jmr = 0 if loop__jmr is None else loop__jmr

    def impl(S, name=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        return bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,), index,
            (loop__jmr,))
    return impl


@overload_method(SeriesType, 'keys', inline='always', no_unliteral=True)
def overload_series_keys(S):

    def impl(S):
        return bodo.hiframes.pd_series_ext.get_series_index(S)
    return impl
