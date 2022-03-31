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
            qkfpv__lfw = list()
            for vnd__hepmp in range(len(S)):
                qkfpv__lfw.append(S.iat[vnd__hepmp])
            return qkfpv__lfw
        return impl_float

    def impl(S):
        qkfpv__lfw = list()
        for vnd__hepmp in range(len(S)):
            if bodo.libs.array_kernels.isna(S.values, vnd__hepmp):
                raise ValueError(
                    'Series.to_list(): Not supported for NA values with non-float dtypes'
                    )
            qkfpv__lfw.append(S.iat[vnd__hepmp])
        return qkfpv__lfw
    return impl


@overload_method(SeriesType, 'to_numpy', inline='always', no_unliteral=True)
def overload_series_to_numpy(S, dtype=None, copy=False, na_value=None):
    vor__slq = dict(dtype=dtype, copy=copy, na_value=na_value)
    klgi__dxbz = dict(dtype=None, copy=False, na_value=None)
    check_unsupported_args('Series.to_numpy', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')

    def impl(S, dtype=None, copy=False, na_value=None):
        return S.values
    return impl


@overload_method(SeriesType, 'reset_index', inline='always', no_unliteral=True)
def overload_series_reset_index(S, level=None, drop=False, name=None,
    inplace=False):
    vor__slq = dict(name=name, inplace=inplace)
    klgi__dxbz = dict(name=None, inplace=False)
    check_unsupported_args('Series.reset_index', vor__slq, klgi__dxbz,
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
    jtwx__crwe = get_name_literal(S.index.name_typ, True, series_name)
    columns = [jtwx__crwe, series_name]
    ylz__ooxm = (
        'def _impl(S, level=None, drop=False, name=None, inplace=False):\n')
    ylz__ooxm += '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    ylz__ooxm += """    index = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(S))
"""
    ylz__ooxm += (
        '    df_index = bodo.hiframes.pd_index_ext.init_range_index(0, len(S), 1, None)\n'
        )
    ylz__ooxm += '    col_var = {}\n'.format(gen_const_tup(columns))
    ylz__ooxm += """    return bodo.hiframes.pd_dataframe_ext.init_dataframe((index, arr), df_index, col_var)
"""
    btemg__ueyt = {}
    exec(ylz__ooxm, {'bodo': bodo}, btemg__ueyt)
    jygy__ivnb = btemg__ueyt['_impl']
    return jygy__ivnb


@overload_method(SeriesType, 'isna', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'isnull', inline='always', no_unliteral=True)
def overload_series_isna(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        tit__ynq = bodo.libs.array_ops.array_op_isna(arr)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index, name)
    return impl


@overload_method(SeriesType, 'round', inline='always', no_unliteral=True)
def overload_series_round(S, decimals=0):

    def impl(S, decimals=0):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        numba.parfors.parfor.init_prange()
        n = len(arr)
        tit__ynq = bodo.utils.utils.alloc_type(n, arr, (-1,))
        for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
            if pd.isna(arr[vnd__hepmp]):
                bodo.libs.array_kernels.setna(tit__ynq, vnd__hepmp)
            else:
                tit__ynq[vnd__hepmp] = np.round(arr[vnd__hepmp], decimals)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index, name)
    return impl


@overload_method(SeriesType, 'sum', inline='always', no_unliteral=True)
def overload_series_sum(S, axis=None, skipna=True, level=None, numeric_only
    =None, min_count=0):
    vor__slq = dict(level=level, numeric_only=numeric_only)
    klgi__dxbz = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.sum', vor__slq, klgi__dxbz, package_name
        ='pandas', module_name='Series')
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
    vor__slq = dict(level=level, numeric_only=numeric_only)
    klgi__dxbz = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.product', vor__slq, klgi__dxbz,
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
    vor__slq = dict(axis=axis, bool_only=bool_only, skipna=skipna, level=level)
    klgi__dxbz = dict(axis=0, bool_only=None, skipna=True, level=None)
    check_unsupported_args('Series.any', vor__slq, klgi__dxbz, package_name
        ='pandas', module_name='Series')

    def impl(S, axis=0, bool_only=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        axxa__bnjw = 0
        for vnd__hepmp in numba.parfors.parfor.internal_prange(len(A)):
            hmdy__chlw = 0
            if not bodo.libs.array_kernels.isna(A, vnd__hepmp):
                hmdy__chlw = int(A[vnd__hepmp])
            axxa__bnjw += hmdy__chlw
        return axxa__bnjw != 0
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
        scscu__xukec = bodo.hiframes.pd_series_ext.get_series_data(S)
        wqoi__axvt = bodo.hiframes.pd_series_ext.get_series_data(other)
        numba.parfors.parfor.init_prange()
        axxa__bnjw = 0
        for vnd__hepmp in numba.parfors.parfor.internal_prange(len(
            scscu__xukec)):
            hmdy__chlw = 0
            kgm__bjhje = bodo.libs.array_kernels.isna(scscu__xukec, vnd__hepmp)
            dpw__bgbr = bodo.libs.array_kernels.isna(wqoi__axvt, vnd__hepmp)
            if kgm__bjhje and not dpw__bgbr or not kgm__bjhje and dpw__bgbr:
                hmdy__chlw = 1
            elif not kgm__bjhje:
                if scscu__xukec[vnd__hepmp] != wqoi__axvt[vnd__hepmp]:
                    hmdy__chlw = 1
            axxa__bnjw += hmdy__chlw
        return axxa__bnjw == 0
    return impl


@overload_method(SeriesType, 'all', inline='always', no_unliteral=True)
def overload_series_all(S, axis=0, bool_only=None, skipna=True, level=None):
    vor__slq = dict(axis=axis, bool_only=bool_only, skipna=skipna, level=level)
    klgi__dxbz = dict(axis=0, bool_only=None, skipna=True, level=None)
    check_unsupported_args('Series.all', vor__slq, klgi__dxbz, package_name
        ='pandas', module_name='Series')

    def impl(S, axis=0, bool_only=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        axxa__bnjw = 0
        for vnd__hepmp in numba.parfors.parfor.internal_prange(len(A)):
            hmdy__chlw = 0
            if not bodo.libs.array_kernels.isna(A, vnd__hepmp):
                hmdy__chlw = int(not A[vnd__hepmp])
            axxa__bnjw += hmdy__chlw
        return axxa__bnjw == 0
    return impl


@overload_method(SeriesType, 'mad', inline='always', no_unliteral=True)
def overload_series_mad(S, axis=None, skipna=True, level=None):
    vor__slq = dict(level=level)
    klgi__dxbz = dict(level=None)
    check_unsupported_args('Series.mad', vor__slq, klgi__dxbz, package_name
        ='pandas', module_name='Series')
    if not is_overload_bool(skipna):
        raise BodoError("Series.mad(): 'skipna' argument must be a boolean")
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.mad(): axis argument not supported')
    jthmf__omgg = types.float64
    hsg__atvv = types.float64
    if S.dtype == types.float32:
        jthmf__omgg = types.float32
        hsg__atvv = types.float32
    fhpx__oqc = jthmf__omgg(0)
    hlb__tiea = hsg__atvv(0)
    ywpr__gth = hsg__atvv(1)

    def impl(S, axis=None, skipna=True, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        ygyej__oyhko = fhpx__oqc
        axxa__bnjw = hlb__tiea
        for vnd__hepmp in numba.parfors.parfor.internal_prange(len(A)):
            hmdy__chlw = fhpx__oqc
            fnnuy__vcvb = hlb__tiea
            if not bodo.libs.array_kernels.isna(A, vnd__hepmp) or not skipna:
                hmdy__chlw = A[vnd__hepmp]
                fnnuy__vcvb = ywpr__gth
            ygyej__oyhko += hmdy__chlw
            axxa__bnjw += fnnuy__vcvb
        schzw__krl = bodo.hiframes.series_kernels._mean_handle_nan(ygyej__oyhko
            , axxa__bnjw)
        tki__uwa = fhpx__oqc
        for vnd__hepmp in numba.parfors.parfor.internal_prange(len(A)):
            hmdy__chlw = fhpx__oqc
            if not bodo.libs.array_kernels.isna(A, vnd__hepmp) or not skipna:
                hmdy__chlw = abs(A[vnd__hepmp] - schzw__krl)
            tki__uwa += hmdy__chlw
        ioy__vccm = bodo.hiframes.series_kernels._mean_handle_nan(tki__uwa,
            axxa__bnjw)
        return ioy__vccm
    return impl


@overload_method(SeriesType, 'mean', inline='always', no_unliteral=True)
def overload_series_mean(S, axis=None, skipna=None, level=None,
    numeric_only=None):
    if not isinstance(S.dtype, types.Number) and S.dtype not in [bodo.
        datetime64ns, types.bool_]:
        raise BodoError(f"Series.mean(): Series with type '{S}' not supported")
    vor__slq = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    klgi__dxbz = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.mean', vor__slq, klgi__dxbz,
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
    vor__slq = dict(level=level, numeric_only=numeric_only)
    klgi__dxbz = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.sem', vor__slq, klgi__dxbz, package_name
        ='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.sem(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.sem(): skipna argument must be a boolean')
    if not is_overload_int(ddof):
        raise BodoError('Series.sem(): ddof argument must be an integer')

    def impl(S, axis=None, skipna=True, level=None, ddof=1, numeric_only=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        wgmj__jna = 0
        nohhf__lgbx = 0
        axxa__bnjw = 0
        for vnd__hepmp in numba.parfors.parfor.internal_prange(len(A)):
            hmdy__chlw = 0
            fnnuy__vcvb = 0
            if not bodo.libs.array_kernels.isna(A, vnd__hepmp) or not skipna:
                hmdy__chlw = A[vnd__hepmp]
                fnnuy__vcvb = 1
            wgmj__jna += hmdy__chlw
            nohhf__lgbx += hmdy__chlw * hmdy__chlw
            axxa__bnjw += fnnuy__vcvb
        pquj__uag = bodo.hiframes.series_kernels._compute_var_nan_count_ddof(
            wgmj__jna, nohhf__lgbx, axxa__bnjw, ddof)
        lssx__nwo = bodo.hiframes.series_kernels._sem_handle_nan(pquj__uag,
            axxa__bnjw)
        return lssx__nwo
    return impl


@overload_method(SeriesType, 'kurt', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'kurtosis', inline='always', no_unliteral=True)
def overload_series_kurt(S, axis=None, skipna=True, level=None,
    numeric_only=None):
    vor__slq = dict(level=level, numeric_only=numeric_only)
    klgi__dxbz = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.kurtosis', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.kurtosis(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError(
            "Series.kurtosis(): 'skipna' argument must be a boolean")

    def impl(S, axis=None, skipna=True, level=None, numeric_only=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        wgmj__jna = 0.0
        nohhf__lgbx = 0.0
        alag__sbjs = 0.0
        bnd__pis = 0.0
        axxa__bnjw = 0
        for vnd__hepmp in numba.parfors.parfor.internal_prange(len(A)):
            hmdy__chlw = 0.0
            fnnuy__vcvb = 0
            if not bodo.libs.array_kernels.isna(A, vnd__hepmp) or not skipna:
                hmdy__chlw = np.float64(A[vnd__hepmp])
                fnnuy__vcvb = 1
            wgmj__jna += hmdy__chlw
            nohhf__lgbx += hmdy__chlw ** 2
            alag__sbjs += hmdy__chlw ** 3
            bnd__pis += hmdy__chlw ** 4
            axxa__bnjw += fnnuy__vcvb
        pquj__uag = bodo.hiframes.series_kernels.compute_kurt(wgmj__jna,
            nohhf__lgbx, alag__sbjs, bnd__pis, axxa__bnjw)
        return pquj__uag
    return impl


@overload_method(SeriesType, 'skew', inline='always', no_unliteral=True)
def overload_series_skew(S, axis=None, skipna=True, level=None,
    numeric_only=None):
    vor__slq = dict(level=level, numeric_only=numeric_only)
    klgi__dxbz = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.skew', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error('Series.skew(): axis argument not supported')
    if not is_overload_bool(skipna):
        raise BodoError('Series.skew(): skipna argument must be a boolean')

    def impl(S, axis=None, skipna=True, level=None, numeric_only=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        numba.parfors.parfor.init_prange()
        wgmj__jna = 0.0
        nohhf__lgbx = 0.0
        alag__sbjs = 0.0
        axxa__bnjw = 0
        for vnd__hepmp in numba.parfors.parfor.internal_prange(len(A)):
            hmdy__chlw = 0.0
            fnnuy__vcvb = 0
            if not bodo.libs.array_kernels.isna(A, vnd__hepmp) or not skipna:
                hmdy__chlw = np.float64(A[vnd__hepmp])
                fnnuy__vcvb = 1
            wgmj__jna += hmdy__chlw
            nohhf__lgbx += hmdy__chlw ** 2
            alag__sbjs += hmdy__chlw ** 3
            axxa__bnjw += fnnuy__vcvb
        pquj__uag = bodo.hiframes.series_kernels.compute_skew(wgmj__jna,
            nohhf__lgbx, alag__sbjs, axxa__bnjw)
        return pquj__uag
    return impl


@overload_method(SeriesType, 'var', inline='always', no_unliteral=True)
def overload_series_var(S, axis=None, skipna=True, level=None, ddof=1,
    numeric_only=None):
    vor__slq = dict(level=level, numeric_only=numeric_only)
    klgi__dxbz = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.var', vor__slq, klgi__dxbz, package_name
        ='pandas', module_name='Series')
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
    vor__slq = dict(level=level, numeric_only=numeric_only)
    klgi__dxbz = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.std', vor__slq, klgi__dxbz, package_name
        ='pandas', module_name='Series')
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
        scscu__xukec = bodo.hiframes.pd_series_ext.get_series_data(S)
        wqoi__axvt = bodo.hiframes.pd_series_ext.get_series_data(other)
        numba.parfors.parfor.init_prange()
        vubep__ubo = 0
        for vnd__hepmp in numba.parfors.parfor.internal_prange(len(
            scscu__xukec)):
            qbwbx__kiab = scscu__xukec[vnd__hepmp]
            rht__cmqbq = wqoi__axvt[vnd__hepmp]
            vubep__ubo += qbwbx__kiab * rht__cmqbq
        return vubep__ubo
    return impl


@overload_method(SeriesType, 'cumsum', inline='always', no_unliteral=True)
def overload_series_cumsum(S, axis=None, skipna=True):
    vor__slq = dict(skipna=skipna)
    klgi__dxbz = dict(skipna=True)
    check_unsupported_args('Series.cumsum', vor__slq, klgi__dxbz,
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
    vor__slq = dict(skipna=skipna)
    klgi__dxbz = dict(skipna=True)
    check_unsupported_args('Series.cumprod', vor__slq, klgi__dxbz,
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
    vor__slq = dict(skipna=skipna)
    klgi__dxbz = dict(skipna=True)
    check_unsupported_args('Series.cummin', vor__slq, klgi__dxbz,
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
    vor__slq = dict(skipna=skipna)
    klgi__dxbz = dict(skipna=True)
    check_unsupported_args('Series.cummax', vor__slq, klgi__dxbz,
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
    vor__slq = dict(copy=copy, inplace=inplace, level=level, errors=errors)
    klgi__dxbz = dict(copy=True, inplace=False, level=None, errors='ignore')
    check_unsupported_args('Series.rename', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')

    def impl(S, index=None, axis=None, copy=True, inplace=False, level=None,
        errors='ignore'):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        ngsr__awfsq = bodo.hiframes.pd_series_ext.get_series_index(S)
        return bodo.hiframes.pd_series_ext.init_series(A, ngsr__awfsq, index)
    return impl


@overload_method(SeriesType, 'rename_axis', inline='always', no_unliteral=True)
def overload_series_rename_axis(S, mapper=None, index=None, columns=None,
    axis=None, copy=True, inplace=False):
    vor__slq = dict(index=index, columns=columns, axis=axis, copy=copy,
        inplace=inplace)
    klgi__dxbz = dict(index=None, columns=None, axis=None, copy=True,
        inplace=False)
    check_unsupported_args('Series.rename_axis', vor__slq, klgi__dxbz,
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
    vor__slq = dict(level=level)
    klgi__dxbz = dict(level=None)
    check_unsupported_args('Series.count', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')

    def impl(S, level=None):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        return bodo.libs.array_ops.array_op_count(A)
    return impl


@overload_method(SeriesType, 'corr', inline='always', no_unliteral=True)
def overload_series_corr(S, other, method='pearson', min_periods=None):
    vor__slq = dict(method=method, min_periods=min_periods)
    klgi__dxbz = dict(method='pearson', min_periods=None)
    check_unsupported_args('Series.corr', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')

    def impl(S, other, method='pearson', min_periods=None):
        n = S.count()
        cwwaf__haq = S.sum()
        ygt__ekzr = other.sum()
        a = n * (S * other).sum() - cwwaf__haq * ygt__ekzr
        bqs__sjiv = n * (S ** 2).sum() - cwwaf__haq ** 2
        wah__ttap = n * (other ** 2).sum() - ygt__ekzr ** 2
        return a / np.sqrt(bqs__sjiv * wah__ttap)
    return impl


@overload_method(SeriesType, 'cov', inline='always', no_unliteral=True)
def overload_series_cov(S, other, min_periods=None, ddof=1):
    vor__slq = dict(min_periods=min_periods)
    klgi__dxbz = dict(min_periods=None)
    check_unsupported_args('Series.cov', vor__slq, klgi__dxbz, package_name
        ='pandas', module_name='Series')

    def impl(S, other, min_periods=None, ddof=1):
        cwwaf__haq = S.mean()
        ygt__ekzr = other.mean()
        hhj__hcaep = ((S - cwwaf__haq) * (other - ygt__ekzr)).sum()
        N = np.float64(S.count() - ddof)
        nonzero_len = S.count() * other.count()
        return _series_cov_helper(hhj__hcaep, N, nonzero_len)
    return impl


def _series_cov_helper(sum_val, N, nonzero_len):
    return


@overload(_series_cov_helper, no_unliteral=True)
def _overload_series_cov_helper(sum_val, N, nonzero_len):

    def impl(sum_val, N, nonzero_len):
        if not nonzero_len:
            return np.nan
        if N <= 0.0:
            qjuxu__dks = np.sign(sum_val)
            return np.inf * qjuxu__dks
        return sum_val / N
    return impl


@overload_method(SeriesType, 'min', inline='always', no_unliteral=True)
def overload_series_min(S, axis=None, skipna=None, level=None, numeric_only
    =None):
    vor__slq = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    klgi__dxbz = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.min', vor__slq, klgi__dxbz, package_name
        ='pandas', module_name='Series')
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
    vor__slq = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    klgi__dxbz = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('Series.max', vor__slq, klgi__dxbz, package_name
        ='pandas', module_name='Series')
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
    vor__slq = dict(axis=axis, skipna=skipna)
    klgi__dxbz = dict(axis=0, skipna=True)
    check_unsupported_args('Series.idxmin', vor__slq, klgi__dxbz,
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
    vor__slq = dict(axis=axis, skipna=skipna)
    klgi__dxbz = dict(axis=0, skipna=True)
    check_unsupported_args('Series.idxmax', vor__slq, klgi__dxbz,
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
    vor__slq = dict(level=level, numeric_only=numeric_only)
    klgi__dxbz = dict(level=None, numeric_only=None)
    check_unsupported_args('Series.median', vor__slq, klgi__dxbz,
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
        toho__ccmn = arr[:n]
        uphwv__rpnr = index[:n]
        return bodo.hiframes.pd_series_ext.init_series(toho__ccmn,
            uphwv__rpnr, name)
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
        ofv__pqqj = tail_slice(len(S), n)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        toho__ccmn = arr[ofv__pqqj:]
        uphwv__rpnr = index[ofv__pqqj:]
        return bodo.hiframes.pd_series_ext.init_series(toho__ccmn,
            uphwv__rpnr, name)
    return impl


@overload_method(SeriesType, 'first', inline='always', no_unliteral=True)
def overload_series_first(S, offset):
    thgu__dzlr = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if types.unliteral(offset) not in thgu__dzlr:
        raise BodoError(
            "Series.first(): 'offset' must be a string or a DateOffset")

    def impl(S, offset):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        if len(index):
            rjk__cep = index[0]
            engdb__jtv = (bodo.libs.array_kernels.
                get_valid_entries_from_date_offset(index, offset, rjk__cep,
                False))
        else:
            engdb__jtv = 0
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        toho__ccmn = arr[:engdb__jtv]
        uphwv__rpnr = index[:engdb__jtv]
        return bodo.hiframes.pd_series_ext.init_series(toho__ccmn,
            uphwv__rpnr, name)
    return impl


@overload_method(SeriesType, 'last', inline='always', no_unliteral=True)
def overload_series_last(S, offset):
    thgu__dzlr = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if types.unliteral(offset) not in thgu__dzlr:
        raise BodoError(
            "Series.last(): 'offset' must be a string or a DateOffset")

    def impl(S, offset):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        if len(index):
            oseio__sexx = index[-1]
            engdb__jtv = (bodo.libs.array_kernels.
                get_valid_entries_from_date_offset(index, offset,
                oseio__sexx, True))
        else:
            engdb__jtv = 0
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        toho__ccmn = arr[len(arr) - engdb__jtv:]
        uphwv__rpnr = index[len(arr) - engdb__jtv:]
        return bodo.hiframes.pd_series_ext.init_series(toho__ccmn,
            uphwv__rpnr, name)
    return impl


@overload_method(SeriesType, 'first_valid_index', inline='always',
    no_unliteral=True)
def overload_series_first_valid_index(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        uou__ghk = bodo.utils.conversion.index_to_array(index)
        mns__yjg, lroan__bmngu = (bodo.libs.array_kernels.
            first_last_valid_index(arr, uou__ghk))
        return lroan__bmngu if mns__yjg else None
    return impl


@overload_method(SeriesType, 'last_valid_index', inline='always',
    no_unliteral=True)
def overload_series_last_valid_index(S):

    def impl(S):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        uou__ghk = bodo.utils.conversion.index_to_array(index)
        mns__yjg, lroan__bmngu = (bodo.libs.array_kernels.
            first_last_valid_index(arr, uou__ghk, False))
        return lroan__bmngu if mns__yjg else None
    return impl


@overload_method(SeriesType, 'nlargest', inline='always', no_unliteral=True)
def overload_series_nlargest(S, n=5, keep='first'):
    vor__slq = dict(keep=keep)
    klgi__dxbz = dict(keep='first')
    check_unsupported_args('Series.nlargest', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')
    if not is_overload_int(n):
        raise BodoError('Series.nlargest(): n argument must be an integer')

    def impl(S, n=5, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        uou__ghk = bodo.utils.conversion.coerce_to_ndarray(index)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        tit__ynq, ehjkg__lbag = bodo.libs.array_kernels.nlargest(arr,
            uou__ghk, n, True, bodo.hiframes.series_kernels.gt_f)
        lvyyk__fqij = bodo.utils.conversion.convert_to_index(ehjkg__lbag)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
            lvyyk__fqij, name)
    return impl


@overload_method(SeriesType, 'nsmallest', inline='always', no_unliteral=True)
def overload_series_nsmallest(S, n=5, keep='first'):
    vor__slq = dict(keep=keep)
    klgi__dxbz = dict(keep='first')
    check_unsupported_args('Series.nsmallest', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')
    if not is_overload_int(n):
        raise BodoError('Series.nsmallest(): n argument must be an integer')

    def impl(S, n=5, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        uou__ghk = bodo.utils.conversion.coerce_to_ndarray(index)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        tit__ynq, ehjkg__lbag = bodo.libs.array_kernels.nlargest(arr,
            uou__ghk, n, False, bodo.hiframes.series_kernels.lt_f)
        lvyyk__fqij = bodo.utils.conversion.convert_to_index(ehjkg__lbag)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
            lvyyk__fqij, name)
    return impl


@overload_method(SeriesType, 'notnull', inline='always', no_unliteral=True)
@overload_method(SeriesType, 'notna', inline='always', no_unliteral=True)
def overload_series_notna(S):
    return lambda S: S.isna() == False


@overload_method(SeriesType, 'astype', inline='always', no_unliteral=True)
def overload_series_astype(S, dtype, copy=True, errors='raise',
    _bodo_nan_to_str=True):
    vor__slq = dict(errors=errors)
    klgi__dxbz = dict(errors='raise')
    check_unsupported_args('Series.astype', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')
    if dtype == types.unicode_type:
        raise_bodo_error(
            "Series.astype(): 'dtype' when passed as string must be a constant value"
            )

    def impl(S, dtype, copy=True, errors='raise', _bodo_nan_to_str=True):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        tit__ynq = bodo.utils.conversion.fix_arr_dtype(arr, dtype, copy,
            nan_to_str=_bodo_nan_to_str, from_series=True)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index, name)
    return impl


@overload_method(SeriesType, 'take', inline='always', no_unliteral=True)
def overload_series_take(S, indices, axis=0, is_copy=True):
    vor__slq = dict(axis=axis, is_copy=is_copy)
    klgi__dxbz = dict(axis=0, is_copy=True)
    check_unsupported_args('Series.take', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')
    if not (is_iterable_type(indices) and isinstance(indices.dtype, types.
        Integer)):
        raise BodoError(
            f"Series.take() 'indices' must be an array-like and contain integers. Found type {indices}."
            )

    def impl(S, indices, axis=0, is_copy=True):
        lpnq__rqes = bodo.utils.conversion.coerce_to_ndarray(indices)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        return bodo.hiframes.pd_series_ext.init_series(arr[lpnq__rqes],
            index[lpnq__rqes], name)
    return impl


@overload_method(SeriesType, 'argsort', inline='always', no_unliteral=True)
def overload_series_argsort(S, axis=0, kind='quicksort', order=None):
    vor__slq = dict(axis=axis, kind=kind, order=order)
    klgi__dxbz = dict(axis=0, kind='quicksort', order=None)
    check_unsupported_args('Series.argsort', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')

    def impl(S, axis=0, kind='quicksort', order=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        n = len(arr)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        ixwef__ckdfg = S.notna().values
        if not ixwef__ckdfg.all():
            tit__ynq = np.full(n, -1, np.int64)
            tit__ynq[ixwef__ckdfg] = argsort(arr[ixwef__ckdfg])
        else:
            tit__ynq = argsort(arr)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index, name)
    return impl


@overload_method(SeriesType, 'sort_index', inline='always', no_unliteral=True)
def overload_series_sort_index(S, axis=0, level=None, ascending=True,
    inplace=False, kind='quicksort', na_position='last', sort_remaining=
    True, ignore_index=False, key=None):
    vor__slq = dict(axis=axis, level=level, inplace=inplace, kind=kind,
        sort_remaining=sort_remaining, ignore_index=ignore_index, key=key)
    klgi__dxbz = dict(axis=0, level=None, inplace=False, kind='quicksort',
        sort_remaining=True, ignore_index=False, key=None)
    check_unsupported_args('Series.sort_index', vor__slq, klgi__dxbz,
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
        dwp__epfu = bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,),
            index, ('$_bodo_col3_',))
        tifzj__zixoq = dwp__epfu.sort_index(ascending=ascending, inplace=
            inplace, na_position=na_position)
        tit__ynq = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(
            tifzj__zixoq, 0)
        lvyyk__fqij = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(
            tifzj__zixoq)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
            lvyyk__fqij, name)
    return impl


@overload_method(SeriesType, 'sort_values', inline='always', no_unliteral=True)
def overload_series_sort_values(S, axis=0, ascending=True, inplace=False,
    kind='quicksort', na_position='last', ignore_index=False, key=None):
    vor__slq = dict(axis=axis, inplace=inplace, kind=kind, ignore_index=
        ignore_index, key=key)
    klgi__dxbz = dict(axis=0, inplace=False, kind='quicksort', ignore_index
        =False, key=None)
    check_unsupported_args('Series.sort_values', vor__slq, klgi__dxbz,
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
        dwp__epfu = bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,),
            index, ('$_bodo_col_',))
        tifzj__zixoq = dwp__epfu.sort_values(['$_bodo_col_'], ascending=
            ascending, inplace=inplace, na_position=na_position)
        tit__ynq = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(
            tifzj__zixoq, 0)
        lvyyk__fqij = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(
            tifzj__zixoq)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
            lvyyk__fqij, name)
    return impl


def get_bin_inds(bins, arr):
    return arr


@overload(get_bin_inds, inline='always', no_unliteral=True)
def overload_get_bin_inds(bins, arr, is_nullable=True, include_lowest=True):
    assert is_overload_constant_bool(is_nullable)
    vmar__wku = is_overload_true(is_nullable)
    ylz__ooxm = 'def impl(bins, arr, is_nullable=True, include_lowest=True):\n'
    ylz__ooxm += '  numba.parfors.parfor.init_prange()\n'
    ylz__ooxm += '  n = len(arr)\n'
    if vmar__wku:
        ylz__ooxm += (
            '  out_arr = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n')
    else:
        ylz__ooxm += '  out_arr = np.empty(n, np.int64)\n'
    ylz__ooxm += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    ylz__ooxm += '    if bodo.libs.array_kernels.isna(arr, i):\n'
    if vmar__wku:
        ylz__ooxm += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    else:
        ylz__ooxm += '      out_arr[i] = -1\n'
    ylz__ooxm += '      continue\n'
    ylz__ooxm += '    val = arr[i]\n'
    ylz__ooxm += '    if include_lowest and val == bins[0]:\n'
    ylz__ooxm += '      ind = 1\n'
    ylz__ooxm += '    else:\n'
    ylz__ooxm += '      ind = np.searchsorted(bins, val)\n'
    ylz__ooxm += '    if ind == 0 or ind == len(bins):\n'
    if vmar__wku:
        ylz__ooxm += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    else:
        ylz__ooxm += '      out_arr[i] = -1\n'
    ylz__ooxm += '    else:\n'
    ylz__ooxm += '      out_arr[i] = ind - 1\n'
    ylz__ooxm += '  return out_arr\n'
    btemg__ueyt = {}
    exec(ylz__ooxm, {'bodo': bodo, 'np': np, 'numba': numba}, btemg__ueyt)
    impl = btemg__ueyt['impl']
    return impl


@register_jitable
def _round_frac(x, precision: int):
    if not np.isfinite(x) or x == 0:
        return x
    else:
        mhl__podzw, rcpmf__odm = np.divmod(x, 1)
        if mhl__podzw == 0:
            ojbvm__uties = -int(np.floor(np.log10(abs(rcpmf__odm)))
                ) - 1 + precision
        else:
            ojbvm__uties = precision
        return np.around(x, ojbvm__uties)


@register_jitable
def _infer_precision(base_precision: int, bins) ->int:
    for precision in range(base_precision, 20):
        yuc__nzhnm = np.array([_round_frac(b, precision) for b in bins])
        if len(np.unique(yuc__nzhnm)) == len(bins):
            return precision
    return base_precision


def get_bin_labels(bins):
    pass


@overload(get_bin_labels, no_unliteral=True)
def overload_get_bin_labels(bins, right=True, include_lowest=True):
    dtype = np.float64 if isinstance(bins.dtype, types.Integer) else bins.dtype
    if dtype == bodo.datetime64ns:
        flvwf__wsa = bodo.timedelta64ns(1)

        def impl_dt64(bins, right=True, include_lowest=True):
            cngvp__wszpc = bins.copy()
            if right and include_lowest:
                cngvp__wszpc[0] = cngvp__wszpc[0] - flvwf__wsa
            bgfnf__gzdh = bodo.libs.interval_arr_ext.init_interval_array(
                cngvp__wszpc[:-1], cngvp__wszpc[1:])
            return bodo.hiframes.pd_index_ext.init_interval_index(bgfnf__gzdh,
                None)
        return impl_dt64

    def impl(bins, right=True, include_lowest=True):
        base_precision = 3
        precision = _infer_precision(base_precision, bins)
        cngvp__wszpc = np.array([_round_frac(b, precision) for b in bins],
            dtype=dtype)
        if right and include_lowest:
            cngvp__wszpc[0] = cngvp__wszpc[0] - 10.0 ** -precision
        bgfnf__gzdh = bodo.libs.interval_arr_ext.init_interval_array(
            cngvp__wszpc[:-1], cngvp__wszpc[1:])
        return bodo.hiframes.pd_index_ext.init_interval_index(bgfnf__gzdh, None
            )
    return impl


def get_output_bin_counts(count_series, nbins):
    pass


@overload(get_output_bin_counts, no_unliteral=True)
def overload_get_output_bin_counts(count_series, nbins):

    def impl(count_series, nbins):
        lttxd__yhvsb = bodo.hiframes.pd_series_ext.get_series_data(count_series
            )
        vepqr__azjlb = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(count_series))
        tit__ynq = np.zeros(nbins, np.int64)
        for vnd__hepmp in range(len(lttxd__yhvsb)):
            tit__ynq[vepqr__azjlb[vnd__hepmp]] = lttxd__yhvsb[vnd__hepmp]
        return tit__ynq
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
            agou__ltc = (max_val - min_val) * 0.001
            if right:
                bins[0] -= agou__ltc
            else:
                bins[-1] += agou__ltc
        return bins
    return impl


@overload_method(SeriesType, 'value_counts', inline='always', no_unliteral=True
    )
def overload_series_value_counts(S, normalize=False, sort=True, ascending=
    False, bins=None, dropna=True, _index_name=None):
    vor__slq = dict(dropna=dropna)
    klgi__dxbz = dict(dropna=True)
    check_unsupported_args('Series.value_counts', vor__slq, klgi__dxbz,
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
    nnw__gvnzm = not is_overload_none(bins)
    ylz__ooxm = 'def impl(\n'
    ylz__ooxm += '    S,\n'
    ylz__ooxm += '    normalize=False,\n'
    ylz__ooxm += '    sort=True,\n'
    ylz__ooxm += '    ascending=False,\n'
    ylz__ooxm += '    bins=None,\n'
    ylz__ooxm += '    dropna=True,\n'
    ylz__ooxm += (
        '    _index_name=None,  # bodo argument. See groupby.value_counts\n')
    ylz__ooxm += '):\n'
    ylz__ooxm += '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    ylz__ooxm += (
        '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
    ylz__ooxm += '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    if nnw__gvnzm:
        ylz__ooxm += '    right = True\n'
        ylz__ooxm += _gen_bins_handling(bins, S.dtype)
        ylz__ooxm += '    arr = get_bin_inds(bins, arr)\n'
    ylz__ooxm += '    in_df = bodo.hiframes.pd_dataframe_ext.init_dataframe(\n'
    ylz__ooxm += "        (arr,), index, ('$_bodo_col2_',)\n"
    ylz__ooxm += '    )\n'
    ylz__ooxm += "    count_series = in_df.groupby('$_bodo_col2_').size()\n"
    if nnw__gvnzm:
        ylz__ooxm += """    count_series = bodo.gatherv(count_series, allgather=True, warn_if_rep=False)
"""
        ylz__ooxm += (
            '    count_arr = get_output_bin_counts(count_series, len(bins) - 1)\n'
            )
        ylz__ooxm += '    index = get_bin_labels(bins)\n'
    else:
        ylz__ooxm += (
            '    count_arr = bodo.hiframes.pd_series_ext.get_series_data(count_series)\n'
            )
        ylz__ooxm += '    ind_arr = bodo.utils.conversion.coerce_to_array(\n'
        ylz__ooxm += (
            '        bodo.hiframes.pd_series_ext.get_series_index(count_series)\n'
            )
        ylz__ooxm += '    )\n'
        ylz__ooxm += """    index = bodo.utils.conversion.index_from_array(ind_arr, name=_index_name)
"""
    ylz__ooxm += (
        '    res = bodo.hiframes.pd_series_ext.init_series(count_arr, index, name)\n'
        )
    if is_overload_true(sort):
        ylz__ooxm += '    res = res.sort_values(ascending=ascending)\n'
    if is_overload_true(normalize):
        fumks__fudz = 'len(S)' if nnw__gvnzm else 'count_arr.sum()'
        ylz__ooxm += f'    res = res / float({fumks__fudz})\n'
    ylz__ooxm += '    return res\n'
    btemg__ueyt = {}
    exec(ylz__ooxm, {'bodo': bodo, 'pd': pd, 'np': np, 'get_bin_inds':
        get_bin_inds, 'get_bin_labels': get_bin_labels,
        'get_output_bin_counts': get_output_bin_counts, 'compute_bins':
        compute_bins}, btemg__ueyt)
    impl = btemg__ueyt['impl']
    return impl


def _gen_bins_handling(bins, dtype):
    ylz__ooxm = ''
    if isinstance(bins, types.Integer):
        ylz__ooxm += '    min_val = bodo.libs.array_ops.array_op_min(arr)\n'
        ylz__ooxm += '    max_val = bodo.libs.array_ops.array_op_max(arr)\n'
        if dtype == bodo.datetime64ns:
            ylz__ooxm += '    min_val = min_val.value\n'
            ylz__ooxm += '    max_val = max_val.value\n'
        ylz__ooxm += '    bins = compute_bins(bins, min_val, max_val, right)\n'
        if dtype == bodo.datetime64ns:
            ylz__ooxm += (
                "    bins = bins.astype(np.int64).view(np.dtype('datetime64[ns]'))\n"
                )
    else:
        ylz__ooxm += (
            '    bins = bodo.utils.conversion.coerce_to_ndarray(bins)\n')
    return ylz__ooxm


@overload(pd.cut, inline='always', no_unliteral=True)
def overload_cut(x, bins, right=True, labels=None, retbins=False, precision
    =3, include_lowest=False, duplicates='raise', ordered=True):
    vor__slq = dict(right=right, labels=labels, retbins=retbins, precision=
        precision, duplicates=duplicates, ordered=ordered)
    klgi__dxbz = dict(right=True, labels=None, retbins=False, precision=3,
        duplicates='raise', ordered=True)
    check_unsupported_args('pandas.cut', vor__slq, klgi__dxbz, package_name
        ='pandas', module_name='General')
    ylz__ooxm = 'def impl(\n'
    ylz__ooxm += '    x,\n'
    ylz__ooxm += '    bins,\n'
    ylz__ooxm += '    right=True,\n'
    ylz__ooxm += '    labels=None,\n'
    ylz__ooxm += '    retbins=False,\n'
    ylz__ooxm += '    precision=3,\n'
    ylz__ooxm += '    include_lowest=False,\n'
    ylz__ooxm += "    duplicates='raise',\n"
    ylz__ooxm += '    ordered=True\n'
    ylz__ooxm += '):\n'
    if isinstance(x, SeriesType):
        ylz__ooxm += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(x)\n')
        ylz__ooxm += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(x)\n')
        ylz__ooxm += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(x)\n')
    else:
        ylz__ooxm += '    arr = bodo.utils.conversion.coerce_to_array(x)\n'
    ylz__ooxm += _gen_bins_handling(bins, x.dtype)
    ylz__ooxm += '    arr = get_bin_inds(bins, arr, False, include_lowest)\n'
    ylz__ooxm += (
        '    label_index = get_bin_labels(bins, right, include_lowest)\n')
    ylz__ooxm += """    cat_dtype = bodo.hiframes.pd_categorical_ext.init_cat_dtype(label_index, ordered, None, None)
"""
    ylz__ooxm += """    out_arr = bodo.hiframes.pd_categorical_ext.init_categorical_array(arr, cat_dtype)
"""
    if isinstance(x, SeriesType):
        ylz__ooxm += (
            '    res = bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        ylz__ooxm += '    return res\n'
    else:
        ylz__ooxm += '    return out_arr\n'
    btemg__ueyt = {}
    exec(ylz__ooxm, {'bodo': bodo, 'pd': pd, 'np': np, 'get_bin_inds':
        get_bin_inds, 'get_bin_labels': get_bin_labels,
        'get_output_bin_counts': get_output_bin_counts, 'compute_bins':
        compute_bins}, btemg__ueyt)
    impl = btemg__ueyt['impl']
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
    vor__slq = dict(labels=labels, retbins=retbins, precision=precision,
        duplicates=duplicates)
    klgi__dxbz = dict(labels=None, retbins=False, precision=3, duplicates=
        'raise')
    check_unsupported_args('pandas.qcut', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='General')
    if not (is_overload_int(q) or is_iterable_type(q)):
        raise BodoError(
            "pd.qcut(): 'q' should be an integer or a list of quantiles")

    def impl(x, q, labels=None, retbins=False, precision=3, duplicates='raise'
        ):
        gnptp__zfpex = _get_q_list(q)
        arr = bodo.utils.conversion.coerce_to_array(x)
        bins = bodo.libs.array_ops.array_op_quantile(arr, gnptp__zfpex)
        return pd.cut(x, bins, include_lowest=True)
    return impl


@overload_method(SeriesType, 'groupby', inline='always', no_unliteral=True)
def overload_series_groupby(S, by=None, axis=0, level=None, as_index=True,
    sort=True, group_keys=True, squeeze=False, observed=True, dropna=True):
    vor__slq = dict(axis=axis, sort=sort, group_keys=group_keys, squeeze=
        squeeze, observed=observed, dropna=dropna)
    klgi__dxbz = dict(axis=0, sort=True, group_keys=True, squeeze=False,
        observed=True, dropna=True)
    check_unsupported_args('Series.groupby', vor__slq, klgi__dxbz,
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
            bgb__nrzw = bodo.utils.conversion.coerce_to_array(index)
            dwp__epfu = bodo.hiframes.pd_dataframe_ext.init_dataframe((
                bgb__nrzw, arr), index, (' ', ''))
            return dwp__epfu.groupby(' ')['']
        return impl_index
    rbevx__zon = by
    if isinstance(by, SeriesType):
        rbevx__zon = by.data
    if isinstance(rbevx__zon, DecimalArrayType):
        raise BodoError(
            'Series.groupby(): by argument with decimal type is not supported yet.'
            )
    if isinstance(by, bodo.hiframes.pd_categorical_ext.CategoricalArrayType):
        raise BodoError(
            'Series.groupby(): by argument with categorical type is not supported yet.'
            )

    def impl(S, by=None, axis=0, level=None, as_index=True, sort=True,
        group_keys=True, squeeze=False, observed=True, dropna=True):
        bgb__nrzw = bodo.utils.conversion.coerce_to_array(by)
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        dwp__epfu = bodo.hiframes.pd_dataframe_ext.init_dataframe((
            bgb__nrzw, arr), index, (' ', ''))
        return dwp__epfu.groupby(' ')['']
    return impl


@overload_method(SeriesType, 'append', inline='always', no_unliteral=True)
def overload_series_append(S, to_append, ignore_index=False,
    verify_integrity=False):
    vor__slq = dict(verify_integrity=verify_integrity)
    klgi__dxbz = dict(verify_integrity=False)
    check_unsupported_args('Series.append', vor__slq, klgi__dxbz,
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
            nah__txi = bodo.utils.conversion.coerce_to_array(values)
            A = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            n = len(A)
            tit__ynq = np.empty(n, np.bool_)
            bodo.libs.array.array_isin(tit__ynq, A, nah__txi, False)
            return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index,
                name)
        return impl_arr
    if not isinstance(values, (types.Set, types.List)):
        raise BodoError(
            "Series.isin(): 'values' parameter should be a set or a list")

    def impl(S, values):
        A = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        tit__ynq = bodo.libs.array_ops.array_op_isin(A, values)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index, name)
    return impl


@overload_method(SeriesType, 'quantile', inline='always', no_unliteral=True)
def overload_series_quantile(S, q=0.5, interpolation='linear'):
    vor__slq = dict(interpolation=interpolation)
    klgi__dxbz = dict(interpolation='linear')
    check_unsupported_args('Series.quantile', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')
    if is_iterable_type(q) and isinstance(q.dtype, types.Number):

        def impl_list(S, q=0.5, interpolation='linear'):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            tit__ynq = bodo.libs.array_ops.array_op_quantile(arr, q)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            index = bodo.hiframes.pd_index_ext.init_numeric_index(bodo.
                utils.conversion.coerce_to_array(q), None)
            return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index,
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
        fjlug__bzqg = bodo.libs.array_kernels.unique(arr)
        return bodo.allgatherv(fjlug__bzqg, False)
    return impl


@overload_method(SeriesType, 'describe', inline='always', no_unliteral=True)
def overload_series_describe(S, percentiles=None, include=None, exclude=
    None, datetime_is_numeric=True):
    vor__slq = dict(percentiles=percentiles, include=include, exclude=
        exclude, datetime_is_numeric=datetime_is_numeric)
    klgi__dxbz = dict(percentiles=None, include=None, exclude=None,
        datetime_is_numeric=True)
    check_unsupported_args('Series.describe', vor__slq, klgi__dxbz,
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
        tuz__ldrk = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
    else:
        tuz__ldrk = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
    ylz__ooxm = '\n'.join(('def impl(', '    S,', '    value=None,',
        '    method=None,', '    axis=None,', '    inplace=False,',
        '    limit=None,', '    downcast=None,', '):',
        '    in_arr = bodo.hiframes.pd_series_ext.get_series_data(S)',
        '    fill_arr = bodo.hiframes.pd_series_ext.get_series_data(value)',
        '    n = len(in_arr)', '    nf = len(fill_arr)',
        "    assert n == nf, 'fillna() requires same length arrays'",
        f'    out_arr = {tuz__ldrk}(n, -1)',
        '    for j in numba.parfors.parfor.internal_prange(n):',
        '        s = in_arr[j]',
        '        if bodo.libs.array_kernels.isna(in_arr, j) and not bodo.libs.array_kernels.isna('
        , '            fill_arr, j', '        ):',
        '            s = fill_arr[j]', '        out_arr[j] = s',
        '    bodo.libs.str_arr_ext.move_str_binary_arr_payload(in_arr, out_arr)'
        ))
    pxo__bjaxy = dict()
    exec(ylz__ooxm, {'bodo': bodo, 'numba': numba}, pxo__bjaxy)
    tbhrj__dryxj = pxo__bjaxy['impl']
    return tbhrj__dryxj


def binary_str_fillna_inplace_impl(is_binary=False):
    if is_binary:
        tuz__ldrk = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
    else:
        tuz__ldrk = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
    ylz__ooxm = 'def impl(S,\n'
    ylz__ooxm += '     value=None,\n'
    ylz__ooxm += '    method=None,\n'
    ylz__ooxm += '    axis=None,\n'
    ylz__ooxm += '    inplace=False,\n'
    ylz__ooxm += '    limit=None,\n'
    ylz__ooxm += '   downcast=None,\n'
    ylz__ooxm += '):\n'
    ylz__ooxm += (
        '    in_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    ylz__ooxm += '    n = len(in_arr)\n'
    ylz__ooxm += f'    out_arr = {tuz__ldrk}(n, -1)\n'
    ylz__ooxm += '    for j in numba.parfors.parfor.internal_prange(n):\n'
    ylz__ooxm += '        s = in_arr[j]\n'
    ylz__ooxm += '        if bodo.libs.array_kernels.isna(in_arr, j):\n'
    ylz__ooxm += '            s = value\n'
    ylz__ooxm += '        out_arr[j] = s\n'
    ylz__ooxm += (
        '    bodo.libs.str_arr_ext.move_str_binary_arr_payload(in_arr, out_arr)\n'
        )
    pxo__bjaxy = dict()
    exec(ylz__ooxm, {'bodo': bodo, 'numba': numba}, pxo__bjaxy)
    tbhrj__dryxj = pxo__bjaxy['impl']
    return tbhrj__dryxj


def fillna_inplace_series_impl(S, value=None, method=None, axis=None,
    inplace=False, limit=None, downcast=None):
    orxy__dro = bodo.hiframes.pd_series_ext.get_series_data(S)
    tdfqz__jnngd = bodo.hiframes.pd_series_ext.get_series_data(value)
    for vnd__hepmp in numba.parfors.parfor.internal_prange(len(orxy__dro)):
        s = orxy__dro[vnd__hepmp]
        if bodo.libs.array_kernels.isna(orxy__dro, vnd__hepmp
            ) and not bodo.libs.array_kernels.isna(tdfqz__jnngd, vnd__hepmp):
            s = tdfqz__jnngd[vnd__hepmp]
        orxy__dro[vnd__hepmp] = s


def fillna_inplace_impl(S, value=None, method=None, axis=None, inplace=
    False, limit=None, downcast=None):
    orxy__dro = bodo.hiframes.pd_series_ext.get_series_data(S)
    for vnd__hepmp in numba.parfors.parfor.internal_prange(len(orxy__dro)):
        s = orxy__dro[vnd__hepmp]
        if bodo.libs.array_kernels.isna(orxy__dro, vnd__hepmp):
            s = value
        orxy__dro[vnd__hepmp] = s


def str_fillna_alloc_series_impl(S, value=None, method=None, axis=None,
    inplace=False, limit=None, downcast=None):
    orxy__dro = bodo.hiframes.pd_series_ext.get_series_data(S)
    index = bodo.hiframes.pd_series_ext.get_series_index(S)
    name = bodo.hiframes.pd_series_ext.get_series_name(S)
    tdfqz__jnngd = bodo.hiframes.pd_series_ext.get_series_data(value)
    n = len(orxy__dro)
    tit__ynq = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
    for nuo__yentr in numba.parfors.parfor.internal_prange(n):
        s = orxy__dro[nuo__yentr]
        if bodo.libs.array_kernels.isna(orxy__dro, nuo__yentr
            ) and not bodo.libs.array_kernels.isna(tdfqz__jnngd, nuo__yentr):
            s = tdfqz__jnngd[nuo__yentr]
        tit__ynq[nuo__yentr] = s
        if bodo.libs.array_kernels.isna(orxy__dro, nuo__yentr
            ) and bodo.libs.array_kernels.isna(tdfqz__jnngd, nuo__yentr):
            bodo.libs.array_kernels.setna(tit__ynq, nuo__yentr)
    return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index, name)


def fillna_series_impl(S, value=None, method=None, axis=None, inplace=False,
    limit=None, downcast=None):
    orxy__dro = bodo.hiframes.pd_series_ext.get_series_data(S)
    index = bodo.hiframes.pd_series_ext.get_series_index(S)
    name = bodo.hiframes.pd_series_ext.get_series_name(S)
    tdfqz__jnngd = bodo.hiframes.pd_series_ext.get_series_data(value)
    n = len(orxy__dro)
    tit__ynq = bodo.utils.utils.alloc_type(n, orxy__dro.dtype, (-1,))
    for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
        s = orxy__dro[vnd__hepmp]
        if bodo.libs.array_kernels.isna(orxy__dro, vnd__hepmp
            ) and not bodo.libs.array_kernels.isna(tdfqz__jnngd, vnd__hepmp):
            s = tdfqz__jnngd[vnd__hepmp]
        tit__ynq[vnd__hepmp] = s
    return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index, name)


@overload_method(SeriesType, 'fillna', no_unliteral=True)
def overload_series_fillna(S, value=None, method=None, axis=None, inplace=
    False, limit=None, downcast=None):
    vor__slq = dict(limit=limit, downcast=downcast)
    klgi__dxbz = dict(limit=None, downcast=None)
    check_unsupported_args('Series.fillna', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')
    cosex__rndp = not is_overload_none(value)
    xcowu__dgmvm = not is_overload_none(method)
    if cosex__rndp and xcowu__dgmvm:
        raise BodoError(
            "Series.fillna(): Cannot specify both 'value' and 'method'.")
    if not cosex__rndp and not xcowu__dgmvm:
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
    if xcowu__dgmvm:
        if is_overload_true(inplace):
            raise BodoError(
                "Series.fillna() with inplace=True not supported with 'method' argument yet."
                )
        skgzz__pasu = (
            "Series.fillna(): 'method' argument if provided must be a constant string and one of ('backfill', 'bfill', 'pad' 'ffill')."
            )
        if not is_overload_constant_str(method):
            raise_bodo_error(skgzz__pasu)
        elif get_overload_const_str(method) not in ('backfill', 'bfill',
            'pad', 'ffill'):
            raise BodoError(skgzz__pasu)
    sxm__eibd = element_type(S.data)
    oue__vxgt = None
    if cosex__rndp:
        oue__vxgt = element_type(types.unliteral(value))
    if oue__vxgt and not can_replace(sxm__eibd, oue__vxgt):
        raise BodoError(
            f'Series.fillna(): Cannot use value type {oue__vxgt} with series type {sxm__eibd}'
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
        ppimp__rdyke = to_str_arr_if_dict_array(S.data)
        if isinstance(value, SeriesType):

            def fillna_series_impl(S, value=None, method=None, axis=None,
                inplace=False, limit=None, downcast=None):
                orxy__dro = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                tdfqz__jnngd = bodo.hiframes.pd_series_ext.get_series_data(
                    value)
                n = len(orxy__dro)
                tit__ynq = bodo.utils.utils.alloc_type(n, ppimp__rdyke, (-1,))
                for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(orxy__dro, vnd__hepmp
                        ) and bodo.libs.array_kernels.isna(tdfqz__jnngd,
                        vnd__hepmp):
                        bodo.libs.array_kernels.setna(tit__ynq, vnd__hepmp)
                        continue
                    if bodo.libs.array_kernels.isna(orxy__dro, vnd__hepmp):
                        tit__ynq[vnd__hepmp
                            ] = bodo.utils.conversion.unbox_if_timestamp(
                            tdfqz__jnngd[vnd__hepmp])
                        continue
                    tit__ynq[vnd__hepmp
                        ] = bodo.utils.conversion.unbox_if_timestamp(orxy__dro
                        [vnd__hepmp])
                return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                    index, name)
            return fillna_series_impl
        if xcowu__dgmvm:
            lxmpx__dkrd = (types.unicode_type, types.bool_, bodo.
                datetime64ns, bodo.timedelta64ns)
            if not isinstance(sxm__eibd, (types.Integer, types.Float)
                ) and sxm__eibd not in lxmpx__dkrd:
                raise BodoError(
                    f"Series.fillna(): series of type {sxm__eibd} are not supported with 'method' argument."
                    )

            def fillna_method_impl(S, value=None, method=None, axis=None,
                inplace=False, limit=None, downcast=None):
                orxy__dro = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                tit__ynq = bodo.libs.array_kernels.ffill_bfill_arr(orxy__dro,
                    method)
                return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                    index, name)
            return fillna_method_impl

        def fillna_impl(S, value=None, method=None, axis=None, inplace=
            False, limit=None, downcast=None):
            value = bodo.utils.conversion.unbox_if_timestamp(value)
            orxy__dro = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            n = len(orxy__dro)
            tit__ynq = bodo.utils.utils.alloc_type(n, ppimp__rdyke, (-1,))
            for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
                s = bodo.utils.conversion.unbox_if_timestamp(orxy__dro[
                    vnd__hepmp])
                if bodo.libs.array_kernels.isna(orxy__dro, vnd__hepmp):
                    s = value
                tit__ynq[vnd__hepmp] = s
            return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index,
                name)
        return fillna_impl


def create_fillna_specific_method_overload(overload_name):

    def overload_series_fillna_specific_method(S, axis=None, inplace=False,
        limit=None, downcast=None):
        tgypq__rts = {'ffill': 'ffill', 'bfill': 'bfill', 'pad': 'ffill',
            'backfill': 'bfill'}[overload_name]
        vor__slq = dict(limit=limit, downcast=downcast)
        klgi__dxbz = dict(limit=None, downcast=None)
        check_unsupported_args(f'Series.{overload_name}', vor__slq,
            klgi__dxbz, package_name='pandas', module_name='Series')
        if not (is_overload_none(axis) or is_overload_zero(axis)):
            raise BodoError(
                f'Series.{overload_name}(): axis argument not supported')
        sxm__eibd = element_type(S.data)
        lxmpx__dkrd = (types.unicode_type, types.bool_, bodo.datetime64ns,
            bodo.timedelta64ns)
        if not isinstance(sxm__eibd, (types.Integer, types.Float)
            ) and sxm__eibd not in lxmpx__dkrd:
            raise BodoError(
                f'Series.{overload_name}(): series of type {sxm__eibd} are not supported.'
                )

        def impl(S, axis=None, inplace=False, limit=None, downcast=None):
            orxy__dro = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            tit__ynq = bodo.libs.array_kernels.ffill_bfill_arr(orxy__dro,
                tgypq__rts)
            return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index,
                name)
        return impl
    return overload_series_fillna_specific_method


fillna_specific_methods = 'ffill', 'bfill', 'pad', 'backfill'


def _install_fillna_specific_methods():
    for overload_name in fillna_specific_methods:
        yxqi__ymo = create_fillna_specific_method_overload(overload_name)
        overload_method(SeriesType, overload_name, no_unliteral=True)(yxqi__ymo
            )


_install_fillna_specific_methods()


def check_unsupported_types(S, to_replace, value):
    if any(bodo.utils.utils.is_array_typ(x, True) for x in [S.dtype,
        to_replace, value]):
        yewni__hfhm = (
            'Series.replace(): only support with Scalar, List, or Dictionary')
        raise BodoError(yewni__hfhm)
    elif isinstance(to_replace, types.DictType) and not is_overload_none(value
        ):
        yewni__hfhm = (
            "Series.replace(): 'value' must be None when 'to_replace' is a dictionary"
            )
        raise BodoError(yewni__hfhm)
    elif any(isinstance(x, (PandasTimestampType, PDTimeDeltaType)) for x in
        [to_replace, value]):
        yewni__hfhm = (
            f'Series.replace(): Not supported for types {to_replace} and {value}'
            )
        raise BodoError(yewni__hfhm)


def series_replace_error_checking(S, to_replace, value, inplace, limit,
    regex, method):
    vor__slq = dict(inplace=inplace, limit=limit, regex=regex, method=method)
    myiuy__kpa = dict(inplace=False, limit=None, regex=False, method='pad')
    check_unsupported_args('Series.replace', vor__slq, myiuy__kpa,
        package_name='pandas', module_name='Series')
    check_unsupported_types(S, to_replace, value)


@overload_method(SeriesType, 'replace', inline='always', no_unliteral=True)
def overload_series_replace(S, to_replace=None, value=None, inplace=False,
    limit=None, regex=False, method='pad'):
    series_replace_error_checking(S, to_replace, value, inplace, limit,
        regex, method)
    sxm__eibd = element_type(S.data)
    if isinstance(to_replace, types.DictType):
        qkkjk__gte = element_type(to_replace.key_type)
        oue__vxgt = element_type(to_replace.value_type)
    else:
        qkkjk__gte = element_type(to_replace)
        oue__vxgt = element_type(value)
    tif__tjr = None
    if sxm__eibd != types.unliteral(qkkjk__gte):
        if bodo.utils.typing.equality_always_false(sxm__eibd, types.
            unliteral(qkkjk__gte)
            ) or not bodo.utils.typing.types_equality_exists(sxm__eibd,
            qkkjk__gte):

            def impl(S, to_replace=None, value=None, inplace=False, limit=
                None, regex=False, method='pad'):
                return S.copy()
            return impl
        if isinstance(sxm__eibd, (types.Float, types.Integer)
            ) or sxm__eibd == np.bool_:
            tif__tjr = sxm__eibd
    if not can_replace(sxm__eibd, types.unliteral(oue__vxgt)):

        def impl(S, to_replace=None, value=None, inplace=False, limit=None,
            regex=False, method='pad'):
            return S.copy()
        return impl
    qhbsu__xouqx = to_str_arr_if_dict_array(S.data)
    if isinstance(qhbsu__xouqx, CategoricalArrayType):

        def cat_impl(S, to_replace=None, value=None, inplace=False, limit=
            None, regex=False, method='pad'):
            orxy__dro = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            return bodo.hiframes.pd_series_ext.init_series(orxy__dro.
                replace(to_replace, value), index, name)
        return cat_impl

    def impl(S, to_replace=None, value=None, inplace=False, limit=None,
        regex=False, method='pad'):
        orxy__dro = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        n = len(orxy__dro)
        tit__ynq = bodo.utils.utils.alloc_type(n, qhbsu__xouqx, (-1,))
        qzb__epo = build_replace_dict(to_replace, value, tif__tjr)
        for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(orxy__dro, vnd__hepmp):
                bodo.libs.array_kernels.setna(tit__ynq, vnd__hepmp)
                continue
            s = orxy__dro[vnd__hepmp]
            if s in qzb__epo:
                s = qzb__epo[s]
            tit__ynq[vnd__hepmp] = s
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index, name)
    return impl


def build_replace_dict(to_replace, value, key_dtype_conv):
    pass


@overload(build_replace_dict)
def _build_replace_dict(to_replace, value, key_dtype_conv):
    luj__qjopw = isinstance(to_replace, (types.Number, Decimal128Type)
        ) or to_replace in [bodo.string_type, types.boolean, bodo.bytes_type]
    bnmf__ezntn = is_iterable_type(to_replace)
    pgpib__lejbg = isinstance(value, (types.Number, Decimal128Type)
        ) or value in [bodo.string_type, bodo.bytes_type, types.boolean]
    cam__qval = is_iterable_type(value)
    if luj__qjopw and pgpib__lejbg:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                qzb__epo = {}
                qzb__epo[key_dtype_conv(to_replace)] = value
                return qzb__epo
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            qzb__epo = {}
            qzb__epo[to_replace] = value
            return qzb__epo
        return impl
    if bnmf__ezntn and pgpib__lejbg:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                qzb__epo = {}
                for xsyoi__ife in to_replace:
                    qzb__epo[key_dtype_conv(xsyoi__ife)] = value
                return qzb__epo
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            qzb__epo = {}
            for xsyoi__ife in to_replace:
                qzb__epo[xsyoi__ife] = value
            return qzb__epo
        return impl
    if bnmf__ezntn and cam__qval:
        if not is_overload_none(key_dtype_conv):

            def impl_cast(to_replace, value, key_dtype_conv):
                qzb__epo = {}
                assert len(to_replace) == len(value
                    ), 'To_replace and value lengths must be the same'
                for vnd__hepmp in range(len(to_replace)):
                    qzb__epo[key_dtype_conv(to_replace[vnd__hepmp])] = value[
                        vnd__hepmp]
                return qzb__epo
            return impl_cast

        def impl(to_replace, value, key_dtype_conv):
            qzb__epo = {}
            assert len(to_replace) == len(value
                ), 'To_replace and value lengths must be the same'
            for vnd__hepmp in range(len(to_replace)):
                qzb__epo[to_replace[vnd__hepmp]] = value[vnd__hepmp]
            return qzb__epo
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
            tit__ynq = bodo.hiframes.series_impl.dt64_arr_sub(arr, bodo.
                hiframes.rolling.shift(arr, periods, False))
            return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index,
                name)
        return impl_datetime

    def impl(S, periods=1):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        tit__ynq = arr - bodo.hiframes.rolling.shift(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index, name)
    return impl


@overload_method(SeriesType, 'explode', inline='always', no_unliteral=True)
def overload_series_explode(S, ignore_index=False):
    from bodo.hiframes.split_impl import string_array_split_view_type
    vor__slq = dict(ignore_index=ignore_index)
    yugn__wxo = dict(ignore_index=False)
    check_unsupported_args('Series.explode', vor__slq, yugn__wxo,
        package_name='pandas', module_name='Series')
    if not (isinstance(S.data, ArrayItemArrayType) or S.data ==
        string_array_split_view_type):
        return lambda S, ignore_index=False: S.copy()

    def impl(S, ignore_index=False):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        uou__ghk = bodo.utils.conversion.index_to_array(index)
        tit__ynq, jvlad__vcv = bodo.libs.array_kernels.explode(arr, uou__ghk)
        lvyyk__fqij = bodo.utils.conversion.index_from_array(jvlad__vcv)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
            lvyyk__fqij, name)
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
            kylx__czrq = np.empty(len(a), a.dtype)
            numba.parfors.parfor.init_prange()
            n = len(a)
            for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
                kylx__czrq[vnd__hepmp] = np.argmax(a[vnd__hepmp])
            return kylx__czrq
        return impl


@overload(np.argmin, inline='always', no_unliteral=True)
def argmin_overload(a, axis=None, out=None):
    if isinstance(a, types.Array) and is_overload_constant_int(axis
        ) and get_overload_const_int(axis) == 1:

        def impl(a, axis=None, out=None):
            pqc__zxtzm = np.empty(len(a), a.dtype)
            numba.parfors.parfor.init_prange()
            n = len(a)
            for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
                pqc__zxtzm[vnd__hepmp] = np.argmin(a[vnd__hepmp])
            return pqc__zxtzm
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
    vor__slq = dict(axis=axis, inplace=inplace, how=how)
    zzuh__crqpm = dict(axis=0, inplace=False, how=None)
    check_unsupported_args('Series.dropna', vor__slq, zzuh__crqpm,
        package_name='pandas', module_name='Series')
    if S.dtype == bodo.string_type:

        def dropna_str_impl(S, axis=0, inplace=False, how=None):
            orxy__dro = bodo.hiframes.pd_series_ext.get_series_data(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            ixwef__ckdfg = S.notna().values
            uou__ghk = bodo.utils.conversion.extract_index_array(S)
            lvyyk__fqij = bodo.utils.conversion.convert_to_index(uou__ghk[
                ixwef__ckdfg])
            tit__ynq = (bodo.hiframes.series_kernels.
                _series_dropna_str_alloc_impl_inner(orxy__dro))
            return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                lvyyk__fqij, name)
        return dropna_str_impl
    else:

        def dropna_impl(S, axis=0, inplace=False, how=None):
            orxy__dro = bodo.hiframes.pd_series_ext.get_series_data(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            uou__ghk = bodo.utils.conversion.extract_index_array(S)
            ixwef__ckdfg = S.notna().values
            lvyyk__fqij = bodo.utils.conversion.convert_to_index(uou__ghk[
                ixwef__ckdfg])
            tit__ynq = orxy__dro[ixwef__ckdfg]
            return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                lvyyk__fqij, name)
        return dropna_impl


@overload_method(SeriesType, 'shift', inline='always', no_unliteral=True)
def overload_series_shift(S, periods=1, freq=None, axis=0, fill_value=None):
    vor__slq = dict(freq=freq, axis=axis, fill_value=fill_value)
    klgi__dxbz = dict(freq=None, axis=0, fill_value=None)
    check_unsupported_args('Series.shift', vor__slq, klgi__dxbz,
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
        tit__ynq = bodo.hiframes.rolling.shift(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index, name)
    return impl


@overload_method(SeriesType, 'pct_change', inline='always', no_unliteral=True)
def overload_series_pct_change(S, periods=1, fill_method='pad', limit=None,
    freq=None):
    vor__slq = dict(fill_method=fill_method, limit=limit, freq=freq)
    klgi__dxbz = dict(fill_method='pad', limit=None, freq=None)
    check_unsupported_args('Series.pct_change', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')
    if not is_overload_int(periods):
        raise BodoError(
            'Series.pct_change(): periods argument must be an Integer')

    def impl(S, periods=1, fill_method='pad', limit=None, freq=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        tit__ynq = bodo.hiframes.rolling.pct_change(arr, periods, False)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index, name)
    return impl


def create_series_mask_where_overload(func_name):

    def overload_series_mask_where(S, cond, other=np.nan, inplace=False,
        axis=None, level=None, errors='raise', try_cast=False):
        _validate_arguments_mask_where(f'Series.{func_name}', S, cond,
            other, inplace, axis, level, errors, try_cast)
        if is_overload_constant_nan(other):
            jtguh__imarb = 'None'
        else:
            jtguh__imarb = 'other'
        ylz__ooxm = """def impl(S, cond, other=np.nan, inplace=False, axis=None, level=None, errors='raise',try_cast=False):
"""
        if func_name == 'mask':
            ylz__ooxm += '  cond = ~cond\n'
        ylz__ooxm += '  arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
        ylz__ooxm += (
            '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        ylz__ooxm += (
            '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        ylz__ooxm += f"""  out_arr = bodo.hiframes.series_impl.where_impl(cond, arr, {jtguh__imarb})
"""
        ylz__ooxm += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        btemg__ueyt = {}
        exec(ylz__ooxm, {'bodo': bodo, 'np': np}, btemg__ueyt)
        impl = btemg__ueyt['impl']
        return impl
    return overload_series_mask_where


def _install_series_mask_where_overload():
    for func_name in ('mask', 'where'):
        yxqi__ymo = create_series_mask_where_overload(func_name)
        overload_method(SeriesType, func_name, no_unliteral=True)(yxqi__ymo)


_install_series_mask_where_overload()


def _validate_arguments_mask_where(func_name, S, cond, other, inplace, axis,
    level, errors, try_cast):
    vor__slq = dict(inplace=inplace, level=level, errors=errors, try_cast=
        try_cast)
    klgi__dxbz = dict(inplace=False, level=None, errors='raise', try_cast=False
        )
    check_unsupported_args(f'{func_name}', vor__slq, klgi__dxbz,
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
    amo__xyam = is_overload_constant_nan(other)
    if not (is_default or amo__xyam or is_scalar_type(other) or isinstance(
        other, types.Array) and other.ndim >= 1 and other.ndim <= max_ndim or
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
            gfbn__untha = arr.dtype.elem_type
        else:
            gfbn__untha = arr.dtype
        if is_iterable_type(other):
            wuuv__ccgdj = other.dtype
        elif amo__xyam:
            wuuv__ccgdj = types.float64
        else:
            wuuv__ccgdj = types.unliteral(other)
        if not amo__xyam and not is_common_scalar_dtype([gfbn__untha,
            wuuv__ccgdj]):
            raise BodoError(
                f"{func_name}() series and 'other' must share a common type.")


def create_explicit_binary_op_overload(op):

    def overload_series_explicit_binary_op(S, other, level=None, fill_value
        =None, axis=0):
        vor__slq = dict(level=level, axis=axis)
        klgi__dxbz = dict(level=None, axis=0)
        check_unsupported_args('series.{}'.format(op.__name__), vor__slq,
            klgi__dxbz, package_name='pandas', module_name='Series')
        vlsqn__yhpxq = other == string_type or is_overload_constant_str(other)
        ixlw__ahda = is_iterable_type(other) and other.dtype == string_type
        cvpz__mqbgq = S.dtype == string_type and (op == operator.add and (
            vlsqn__yhpxq or ixlw__ahda) or op == operator.mul and
            isinstance(other, types.Integer))
        mysx__rwb = S.dtype == bodo.timedelta64ns
        owol__gshn = S.dtype == bodo.datetime64ns
        lshfu__vrow = is_iterable_type(other) and (other.dtype ==
            datetime_timedelta_type or other.dtype == bodo.timedelta64ns)
        eugr__phe = is_iterable_type(other) and (other.dtype ==
            datetime_datetime_type or other.dtype == pd_timestamp_type or 
            other.dtype == bodo.datetime64ns)
        irde__aamo = mysx__rwb and (lshfu__vrow or eugr__phe
            ) or owol__gshn and lshfu__vrow
        irde__aamo = irde__aamo and op == operator.add
        if not (isinstance(S.dtype, types.Number) or cvpz__mqbgq or irde__aamo
            ):
            raise BodoError(f'Unsupported types for Series.{op.__name__}')
        byf__kokkg = numba.core.registry.cpu_target.typing_context
        if is_scalar_type(other):
            args = S.data, other
            qhbsu__xouqx = byf__kokkg.resolve_function_type(op, args, {}
                ).return_type
            if isinstance(S.data, IntegerArrayType
                ) and qhbsu__xouqx == types.Array(types.bool_, 1, 'C'):
                qhbsu__xouqx = boolean_array

            def impl_scalar(S, other, level=None, fill_value=None, axis=0):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                numba.parfors.parfor.init_prange()
                other = bodo.utils.conversion.unbox_if_timestamp(other)
                n = len(arr)
                tit__ynq = bodo.utils.utils.alloc_type(n, qhbsu__xouqx, (-1,))
                for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
                    oqa__lvf = bodo.libs.array_kernels.isna(arr, vnd__hepmp)
                    if oqa__lvf:
                        if fill_value is None:
                            bodo.libs.array_kernels.setna(tit__ynq, vnd__hepmp)
                        else:
                            tit__ynq[vnd__hepmp] = op(fill_value, other)
                    else:
                        tit__ynq[vnd__hepmp] = op(arr[vnd__hepmp], other)
                return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                    index, name)
            return impl_scalar
        args = S.data, types.Array(other.dtype, 1, 'C')
        qhbsu__xouqx = byf__kokkg.resolve_function_type(op, args, {}
            ).return_type
        if isinstance(S.data, IntegerArrayType
            ) and qhbsu__xouqx == types.Array(types.bool_, 1, 'C'):
            qhbsu__xouqx = boolean_array

        def impl(S, other, level=None, fill_value=None, axis=0):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            kcnt__dtq = bodo.utils.conversion.coerce_to_array(other)
            numba.parfors.parfor.init_prange()
            n = len(arr)
            tit__ynq = bodo.utils.utils.alloc_type(n, qhbsu__xouqx, (-1,))
            for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
                oqa__lvf = bodo.libs.array_kernels.isna(arr, vnd__hepmp)
                qrmhb__raok = bodo.libs.array_kernels.isna(kcnt__dtq,
                    vnd__hepmp)
                if oqa__lvf and qrmhb__raok:
                    bodo.libs.array_kernels.setna(tit__ynq, vnd__hepmp)
                elif oqa__lvf:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(tit__ynq, vnd__hepmp)
                    else:
                        tit__ynq[vnd__hepmp] = op(fill_value, kcnt__dtq[
                            vnd__hepmp])
                elif qrmhb__raok:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(tit__ynq, vnd__hepmp)
                    else:
                        tit__ynq[vnd__hepmp] = op(arr[vnd__hepmp], fill_value)
                else:
                    tit__ynq[vnd__hepmp] = op(arr[vnd__hepmp], kcnt__dtq[
                        vnd__hepmp])
            return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index,
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
        byf__kokkg = numba.core.registry.cpu_target.typing_context
        if isinstance(other, types.Number):
            args = other, S.data
            qhbsu__xouqx = byf__kokkg.resolve_function_type(op, args, {}
                ).return_type
            if isinstance(S.data, IntegerArrayType
                ) and qhbsu__xouqx == types.Array(types.bool_, 1, 'C'):
                qhbsu__xouqx = boolean_array

            def impl_scalar(S, other, level=None, fill_value=None, axis=0):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                numba.parfors.parfor.init_prange()
                n = len(arr)
                tit__ynq = bodo.utils.utils.alloc_type(n, qhbsu__xouqx, None)
                for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
                    oqa__lvf = bodo.libs.array_kernels.isna(arr, vnd__hepmp)
                    if oqa__lvf:
                        if fill_value is None:
                            bodo.libs.array_kernels.setna(tit__ynq, vnd__hepmp)
                        else:
                            tit__ynq[vnd__hepmp] = op(other, fill_value)
                    else:
                        tit__ynq[vnd__hepmp] = op(other, arr[vnd__hepmp])
                return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                    index, name)
            return impl_scalar
        args = types.Array(other.dtype, 1, 'C'), S.data
        qhbsu__xouqx = byf__kokkg.resolve_function_type(op, args, {}
            ).return_type
        if isinstance(S.data, IntegerArrayType
            ) and qhbsu__xouqx == types.Array(types.bool_, 1, 'C'):
            qhbsu__xouqx = boolean_array

        def impl(S, other, level=None, fill_value=None, axis=0):
            arr = bodo.hiframes.pd_series_ext.get_series_data(S)
            index = bodo.hiframes.pd_series_ext.get_series_index(S)
            name = bodo.hiframes.pd_series_ext.get_series_name(S)
            kcnt__dtq = bodo.hiframes.pd_series_ext.get_series_data(other)
            numba.parfors.parfor.init_prange()
            n = len(arr)
            tit__ynq = bodo.utils.utils.alloc_type(n, qhbsu__xouqx, None)
            for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
                oqa__lvf = bodo.libs.array_kernels.isna(arr, vnd__hepmp)
                qrmhb__raok = bodo.libs.array_kernels.isna(kcnt__dtq,
                    vnd__hepmp)
                tit__ynq[vnd__hepmp] = op(kcnt__dtq[vnd__hepmp], arr[
                    vnd__hepmp])
                if oqa__lvf and qrmhb__raok:
                    bodo.libs.array_kernels.setna(tit__ynq, vnd__hepmp)
                elif oqa__lvf:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(tit__ynq, vnd__hepmp)
                    else:
                        tit__ynq[vnd__hepmp] = op(kcnt__dtq[vnd__hepmp],
                            fill_value)
                elif qrmhb__raok:
                    if fill_value is None:
                        bodo.libs.array_kernels.setna(tit__ynq, vnd__hepmp)
                    else:
                        tit__ynq[vnd__hepmp] = op(fill_value, arr[vnd__hepmp])
                else:
                    tit__ynq[vnd__hepmp] = op(kcnt__dtq[vnd__hepmp], arr[
                        vnd__hepmp])
            return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index,
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
    for op, ghvu__ioui in explicit_binop_funcs_two_ways.items():
        for name in ghvu__ioui:
            yxqi__ymo = create_explicit_binary_op_overload(op)
            eeb__hnmk = create_explicit_binary_reverse_op_overload(op)
            afb__ogov = 'r' + name
            overload_method(SeriesType, name, no_unliteral=True)(yxqi__ymo)
            overload_method(SeriesType, afb__ogov, no_unliteral=True)(eeb__hnmk
                )
            explicit_binop_funcs.add(name)
    for op, name in explicit_binop_funcs_single.items():
        yxqi__ymo = create_explicit_binary_op_overload(op)
        overload_method(SeriesType, name, no_unliteral=True)(yxqi__ymo)
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
                vubkl__zpzk = (bodo.utils.conversion.
                    get_array_if_series_or_index(rhs))
                tit__ynq = dt64_arr_sub(arr, vubkl__zpzk)
                return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
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
                tit__ynq = np.empty(n, np.dtype('datetime64[ns]'))
                for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(arr, vnd__hepmp):
                        bodo.libs.array_kernels.setna(tit__ynq, vnd__hepmp)
                        continue
                    pnd__ghclg = (bodo.hiframes.pd_timestamp_ext.
                        convert_datetime64_to_timestamp(arr[vnd__hepmp]))
                    zjgcx__jots = op(pnd__ghclg, rhs)
                    tit__ynq[vnd__hepmp
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        zjgcx__jots.value)
                return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
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
                    vubkl__zpzk = (bodo.utils.conversion.
                        get_array_if_series_or_index(rhs))
                    tit__ynq = op(arr, bodo.utils.conversion.
                        unbox_if_timestamp(vubkl__zpzk))
                    return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                        index, name)
                return impl

            def impl(lhs, rhs):
                arr = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                index = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                name = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                vubkl__zpzk = (bodo.utils.conversion.
                    get_array_if_series_or_index(rhs))
                tit__ynq = op(arr, vubkl__zpzk)
                return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                    index, name)
            return impl
        if isinstance(rhs, SeriesType):
            if rhs.dtype in [bodo.datetime64ns, bodo.timedelta64ns]:

                def impl(lhs, rhs):
                    arr = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                    index = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                    name = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                    iwl__iuq = (bodo.utils.conversion.
                        get_array_if_series_or_index(lhs))
                    tit__ynq = op(bodo.utils.conversion.unbox_if_timestamp(
                        iwl__iuq), arr)
                    return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                        index, name)
                return impl

            def impl(lhs, rhs):
                arr = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                index = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                name = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                iwl__iuq = bodo.utils.conversion.get_array_if_series_or_index(
                    lhs)
                tit__ynq = op(iwl__iuq, arr)
                return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                    index, name)
            return impl
    return overload_series_binary_op


skips = list(explicit_binop_funcs_two_ways.keys()) + list(
    explicit_binop_funcs_single.keys()) + split_logical_binops_funcs


def _install_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_binary_ops:
        if op in skips:
            continue
        yxqi__ymo = create_binary_op_overload(op)
        overload(op)(yxqi__ymo)


_install_binary_ops()


def dt64_arr_sub(arg1, arg2):
    return arg1 - arg2


@overload(dt64_arr_sub, no_unliteral=True)
def overload_dt64_arr_sub(arg1, arg2):
    assert arg1 == types.Array(bodo.datetime64ns, 1, 'C'
        ) and arg2 == types.Array(bodo.datetime64ns, 1, 'C')
    qylep__fpsmo = np.dtype('timedelta64[ns]')

    def impl(arg1, arg2):
        numba.parfors.parfor.init_prange()
        n = len(arg1)
        S = np.empty(n, qylep__fpsmo)
        for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(arg1, vnd__hepmp
                ) or bodo.libs.array_kernels.isna(arg2, vnd__hepmp):
                bodo.libs.array_kernels.setna(S, vnd__hepmp)
                continue
            S[vnd__hepmp
                ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                bodo.hiframes.pd_timestamp_ext.dt64_to_integer(arg1[
                vnd__hepmp]) - bodo.hiframes.pd_timestamp_ext.
                dt64_to_integer(arg2[vnd__hepmp]))
        return S
    return impl


def create_inplace_binary_op_overload(op):

    def overload_series_inplace_binary_op(S, other):
        if isinstance(S, SeriesType) or isinstance(other, SeriesType):

            def impl(S, other):
                arr = bodo.utils.conversion.get_array_if_series_or_index(S)
                kcnt__dtq = bodo.utils.conversion.get_array_if_series_or_index(
                    other)
                op(arr, kcnt__dtq)
                return S
            return impl
    return overload_series_inplace_binary_op


def _install_inplace_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_inplace_binary_ops:
        yxqi__ymo = create_inplace_binary_op_overload(op)
        overload(op, no_unliteral=True)(yxqi__ymo)


_install_inplace_binary_ops()


def create_unary_op_overload(op):

    def overload_series_unary_op(S):
        if isinstance(S, SeriesType):

            def impl(S):
                arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                index = bodo.hiframes.pd_series_ext.get_series_index(S)
                name = bodo.hiframes.pd_series_ext.get_series_name(S)
                tit__ynq = op(arr)
                return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                    index, name)
            return impl
    return overload_series_unary_op


def _install_unary_ops():
    for op in bodo.hiframes.pd_series_ext.series_unary_ops:
        yxqi__ymo = create_unary_op_overload(op)
        overload(op, no_unliteral=True)(yxqi__ymo)


_install_unary_ops()


def create_ufunc_overload(ufunc):
    if ufunc.nin == 1:

        def overload_series_ufunc_nin_1(S):
            if isinstance(S, SeriesType):

                def impl(S):
                    arr = bodo.hiframes.pd_series_ext.get_series_data(S)
                    index = bodo.hiframes.pd_series_ext.get_series_index(S)
                    name = bodo.hiframes.pd_series_ext.get_series_name(S)
                    tit__ynq = ufunc(arr)
                    return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
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
                    kcnt__dtq = (bodo.utils.conversion.
                        get_array_if_series_or_index(S2))
                    tit__ynq = ufunc(arr, kcnt__dtq)
                    return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                        index, name)
                return impl
            elif isinstance(S2, SeriesType):

                def impl(S1, S2):
                    arr = bodo.utils.conversion.get_array_if_series_or_index(S1
                        )
                    kcnt__dtq = bodo.hiframes.pd_series_ext.get_series_data(S2)
                    index = bodo.hiframes.pd_series_ext.get_series_index(S2)
                    name = bodo.hiframes.pd_series_ext.get_series_name(S2)
                    tit__ynq = ufunc(arr, kcnt__dtq)
                    return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                        index, name)
                return impl
        return overload_series_ufunc_nin_2
    else:
        raise RuntimeError(
            "Don't know how to register ufuncs from ufunc_db with arity > 2")


def _install_np_ufuncs():
    import numba.np.ufunc_db
    for ufunc in numba.np.ufunc_db.get_ufuncs():
        yxqi__ymo = create_ufunc_overload(ufunc)
        overload(ufunc, no_unliteral=True)(yxqi__ymo)


_install_np_ufuncs()


def argsort(A):
    return np.argsort(A)


@overload(argsort, no_unliteral=True)
def overload_argsort(A):

    def impl(A):
        n = len(A)
        gqhc__dxo = bodo.libs.str_arr_ext.to_list_if_immutable_arr((A.copy(),))
        oxn__key = np.arange(n),
        bodo.libs.timsort.sort(gqhc__dxo, 0, n, oxn__key)
        return oxn__key[0]
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
        vmftg__did = get_overload_const_str(downcast)
        if vmftg__did in ('integer', 'signed'):
            out_dtype = types.int64
        elif vmftg__did == 'unsigned':
            out_dtype = types.uint64
        else:
            assert vmftg__did == 'float'
    if isinstance(arg_a, (types.Array, IntegerArrayType)):
        return lambda arg_a, errors='raise', downcast=None: arg_a.astype(
            out_dtype)
    if isinstance(arg_a, SeriesType):

        def impl_series(arg_a, errors='raise', downcast=None):
            orxy__dro = bodo.hiframes.pd_series_ext.get_series_data(arg_a)
            index = bodo.hiframes.pd_series_ext.get_series_index(arg_a)
            name = bodo.hiframes.pd_series_ext.get_series_name(arg_a)
            tit__ynq = pd.to_numeric(orxy__dro, errors, downcast)
            return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index,
                name)
        return impl_series
    if not is_str_arr_type(arg_a):
        raise BodoError(f'pd.to_numeric(): invalid argument type {arg_a}')
    if out_dtype == types.float64:

        def to_numeric_float_impl(arg_a, errors='raise', downcast=None):
            numba.parfors.parfor.init_prange()
            n = len(arg_a)
            ehjek__iqqz = np.empty(n, np.float64)
            for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arg_a, vnd__hepmp):
                    bodo.libs.array_kernels.setna(ehjek__iqqz, vnd__hepmp)
                else:
                    bodo.libs.str_arr_ext.str_arr_item_to_numeric(ehjek__iqqz,
                        vnd__hepmp, arg_a, vnd__hepmp)
            return ehjek__iqqz
        return to_numeric_float_impl
    else:

        def to_numeric_int_impl(arg_a, errors='raise', downcast=None):
            numba.parfors.parfor.init_prange()
            n = len(arg_a)
            ehjek__iqqz = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)
            for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
                if bodo.libs.array_kernels.isna(arg_a, vnd__hepmp):
                    bodo.libs.array_kernels.setna(ehjek__iqqz, vnd__hepmp)
                else:
                    bodo.libs.str_arr_ext.str_arr_item_to_numeric(ehjek__iqqz,
                        vnd__hepmp, arg_a, vnd__hepmp)
            return ehjek__iqqz
        return to_numeric_int_impl


def series_filter_bool(arr, bool_arr):
    return arr[bool_arr]


@infer_global(series_filter_bool)
class SeriesFilterBoolInfer(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 2
        duhrj__eds = if_series_to_array_type(args[0])
        if isinstance(duhrj__eds, types.Array) and isinstance(duhrj__eds.
            dtype, types.Integer):
            duhrj__eds = types.Array(types.float64, 1, 'C')
        return duhrj__eds(*args)


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
    ezot__fdt = bodo.utils.utils.is_array_typ(x, True)
    yko__izb = bodo.utils.utils.is_array_typ(y, True)
    ylz__ooxm = 'def _impl(condition, x, y):\n'
    if isinstance(condition, SeriesType):
        ylz__ooxm += (
            '  condition = bodo.hiframes.pd_series_ext.get_series_data(condition)\n'
            )
    if ezot__fdt and not bodo.utils.utils.is_array_typ(x, False):
        ylz__ooxm += '  x = bodo.utils.conversion.coerce_to_array(x)\n'
    if yko__izb and not bodo.utils.utils.is_array_typ(y, False):
        ylz__ooxm += '  y = bodo.utils.conversion.coerce_to_array(y)\n'
    ylz__ooxm += '  n = len(condition)\n'
    vxzvd__xkyf = x.dtype if ezot__fdt else types.unliteral(x)
    aduvc__kao = y.dtype if yko__izb else types.unliteral(y)
    if not isinstance(x, CategoricalArrayType):
        vxzvd__xkyf = element_type(x)
    if not isinstance(y, CategoricalArrayType):
        aduvc__kao = element_type(y)

    def get_data(x):
        if isinstance(x, SeriesType):
            return x.data
        elif isinstance(x, types.Array):
            return x
        return types.unliteral(x)
    kjuu__iyql = get_data(x)
    clixt__robz = get_data(y)
    is_nullable = any(bodo.utils.typing.is_nullable(oxn__key) for oxn__key in
        [kjuu__iyql, clixt__robz])
    if clixt__robz == types.none:
        if isinstance(vxzvd__xkyf, types.Number):
            out_dtype = types.Array(types.float64, 1, 'C')
        else:
            out_dtype = to_nullable_type(x)
    elif kjuu__iyql == clixt__robz and not is_nullable:
        out_dtype = dtype_to_array_type(vxzvd__xkyf)
    elif vxzvd__xkyf == string_type or aduvc__kao == string_type:
        out_dtype = bodo.string_array_type
    elif kjuu__iyql == bytes_type or (ezot__fdt and vxzvd__xkyf == bytes_type
        ) and (clixt__robz == bytes_type or yko__izb and aduvc__kao ==
        bytes_type):
        out_dtype = binary_array_type
    elif isinstance(vxzvd__xkyf, bodo.PDCategoricalDtype):
        out_dtype = None
    elif vxzvd__xkyf in [bodo.timedelta64ns, bodo.datetime64ns]:
        out_dtype = types.Array(vxzvd__xkyf, 1, 'C')
    elif aduvc__kao in [bodo.timedelta64ns, bodo.datetime64ns]:
        out_dtype = types.Array(aduvc__kao, 1, 'C')
    else:
        out_dtype = numba.from_dtype(np.promote_types(numba.np.
            numpy_support.as_dtype(vxzvd__xkyf), numba.np.numpy_support.
            as_dtype(aduvc__kao)))
        out_dtype = types.Array(out_dtype, 1, 'C')
        if is_nullable:
            out_dtype = bodo.utils.typing.to_nullable_type(out_dtype)
    if isinstance(vxzvd__xkyf, bodo.PDCategoricalDtype):
        gfy__lrn = 'x'
    else:
        gfy__lrn = 'out_dtype'
    ylz__ooxm += (
        f'  out_arr = bodo.utils.utils.alloc_type(n, {gfy__lrn}, (-1,))\n')
    if isinstance(vxzvd__xkyf, bodo.PDCategoricalDtype):
        ylz__ooxm += """  out_codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(out_arr)
"""
        ylz__ooxm += (
            '  x_codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(x)\n'
            )
    ylz__ooxm += '  for j in numba.parfors.parfor.internal_prange(n):\n'
    ylz__ooxm += (
        '    if not bodo.libs.array_kernels.isna(condition, j) and condition[j]:\n'
        )
    if ezot__fdt:
        ylz__ooxm += '      if bodo.libs.array_kernels.isna(x, j):\n'
        ylz__ooxm += '        setna(out_arr, j)\n'
        ylz__ooxm += '        continue\n'
    if isinstance(vxzvd__xkyf, bodo.PDCategoricalDtype):
        ylz__ooxm += '      out_codes[j] = x_codes[j]\n'
    else:
        ylz__ooxm += (
            '      out_arr[j] = bodo.utils.conversion.unbox_if_timestamp({})\n'
            .format('x[j]' if ezot__fdt else 'x'))
    ylz__ooxm += '    else:\n'
    if yko__izb:
        ylz__ooxm += '      if bodo.libs.array_kernels.isna(y, j):\n'
        ylz__ooxm += '        setna(out_arr, j)\n'
        ylz__ooxm += '        continue\n'
    if clixt__robz == types.none:
        if isinstance(vxzvd__xkyf, bodo.PDCategoricalDtype):
            ylz__ooxm += '      out_codes[j] = -1\n'
        else:
            ylz__ooxm += '      setna(out_arr, j)\n'
    else:
        ylz__ooxm += (
            '      out_arr[j] = bodo.utils.conversion.unbox_if_timestamp({})\n'
            .format('y[j]' if yko__izb else 'y'))
    ylz__ooxm += '  return out_arr\n'
    btemg__ueyt = {}
    exec(ylz__ooxm, {'bodo': bodo, 'numba': numba, 'setna': bodo.libs.
        array_kernels.setna, 'np': np, 'out_dtype': out_dtype}, btemg__ueyt)
    jygy__ivnb = btemg__ueyt['_impl']
    return jygy__ivnb


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
        mbb__hvbds = choicelist.dtype
        if not bodo.utils.utils.is_array_typ(mbb__hvbds, True):
            raise BodoError(
                "np.select(): 'choicelist' argument must be list or tuple of series/arrays types"
                )
        if is_series_type(mbb__hvbds):
            gfzph__nxui = mbb__hvbds.data.dtype
        else:
            gfzph__nxui = mbb__hvbds.dtype
        if isinstance(gfzph__nxui, bodo.PDCategoricalDtype):
            raise BodoError(
                'np.select(): data with choicelist of type Categorical not yet supported'
                )
        wpq__obtbm = mbb__hvbds
    else:
        dcy__jtg = []
        for mbb__hvbds in choicelist:
            if not bodo.utils.utils.is_array_typ(mbb__hvbds, True):
                raise BodoError(
                    "np.select(): 'choicelist' argument must be list or tuple of series/arrays types"
                    )
            if is_series_type(mbb__hvbds):
                gfzph__nxui = mbb__hvbds.data.dtype
            else:
                gfzph__nxui = mbb__hvbds.dtype
            if isinstance(gfzph__nxui, bodo.PDCategoricalDtype):
                raise BodoError(
                    'np.select(): data with choicelist of type Categorical not yet supported'
                    )
            dcy__jtg.append(gfzph__nxui)
        if not is_common_scalar_dtype(dcy__jtg):
            raise BodoError(
                f"np.select(): 'choicelist' items must be arrays with a commmon data type. Found a tuple with the following data types {choicelist}."
                )
        wpq__obtbm = choicelist[0]
    if is_series_type(wpq__obtbm):
        wpq__obtbm = wpq__obtbm.data
    if is_overload_constant_int(default) and get_overload_const_int(default
        ) == 0:
        pass
    else:
        if not is_scalar_type(default):
            raise BodoError(
                "np.select(): 'default' argument must be scalar type")
        if not (is_common_scalar_dtype([default, wpq__obtbm.dtype]) or 
            default == types.none or is_overload_constant_nan(default)):
            raise BodoError(
                f"np.select(): 'default' is not type compatible with the array types in choicelist. Choicelist type: {choicelist}, Default type: {default}"
                )
    if not (isinstance(wpq__obtbm, types.Array) or isinstance(wpq__obtbm,
        BooleanArrayType) or isinstance(wpq__obtbm, IntegerArrayType) or 
        bodo.utils.utils.is_array_typ(wpq__obtbm, False) and wpq__obtbm.
        dtype in [bodo.string_type, bodo.bytes_type]):
        raise BodoError(
            f'np.select(): data with choicelist of type {wpq__obtbm} not yet supported'
            )


@overload(np.select)
def overload_np_select(condlist, choicelist, default=0):
    _verify_np_select_arg_typs(condlist, choicelist, default)
    nwhpy__alqfr = isinstance(choicelist, (types.List, types.UniTuple)
        ) and isinstance(condlist, (types.List, types.UniTuple))
    if isinstance(choicelist, (types.List, types.UniTuple)):
        ybipr__oubqr = choicelist.dtype
    else:
        xfvc__pbila = False
        dcy__jtg = []
        for mbb__hvbds in choicelist:
            if is_nullable_type(mbb__hvbds):
                xfvc__pbila = True
            if is_series_type(mbb__hvbds):
                gfzph__nxui = mbb__hvbds.data.dtype
            else:
                gfzph__nxui = mbb__hvbds.dtype
            if isinstance(gfzph__nxui, bodo.PDCategoricalDtype):
                raise BodoError(
                    'np.select(): data with choicelist of type Categorical not yet supported'
                    )
            dcy__jtg.append(gfzph__nxui)
        rjxme__zem, jnb__dljan = get_common_scalar_dtype(dcy__jtg)
        if not jnb__dljan:
            raise BodoError('Internal error in overload_np_select')
        mxkwh__qdio = dtype_to_array_type(rjxme__zem)
        if xfvc__pbila:
            mxkwh__qdio = to_nullable_type(mxkwh__qdio)
        ybipr__oubqr = mxkwh__qdio
    if isinstance(ybipr__oubqr, SeriesType):
        ybipr__oubqr = ybipr__oubqr.data
    if is_overload_constant_int(default) and get_overload_const_int(default
        ) == 0:
        xrgz__cds = True
    else:
        xrgz__cds = False
    etp__jzb = False
    pjc__wscn = False
    if xrgz__cds:
        if isinstance(ybipr__oubqr.dtype, types.Number):
            pass
        elif ybipr__oubqr.dtype == types.bool_:
            pjc__wscn = True
        else:
            etp__jzb = True
            ybipr__oubqr = to_nullable_type(ybipr__oubqr)
    elif default == types.none or is_overload_constant_nan(default):
        etp__jzb = True
        ybipr__oubqr = to_nullable_type(ybipr__oubqr)
    ylz__ooxm = 'def np_select_impl(condlist, choicelist, default=0):\n'
    ylz__ooxm += '  if len(condlist) != len(choicelist):\n'
    ylz__ooxm += """    raise ValueError('list of cases must be same length as list of conditions')
"""
    ylz__ooxm += '  output_len = len(choicelist[0])\n'
    ylz__ooxm += (
        '  out = bodo.utils.utils.alloc_type(output_len, alloc_typ, (-1,))\n')
    ylz__ooxm += '  for i in range(output_len):\n'
    if etp__jzb:
        ylz__ooxm += '    bodo.libs.array_kernels.setna(out, i)\n'
    elif pjc__wscn:
        ylz__ooxm += '    out[i] = False\n'
    else:
        ylz__ooxm += '    out[i] = default\n'
    if nwhpy__alqfr:
        ylz__ooxm += '  for i in range(len(condlist) - 1, -1, -1):\n'
        ylz__ooxm += '    cond = condlist[i]\n'
        ylz__ooxm += '    choice = choicelist[i]\n'
        ylz__ooxm += '    out = np.where(cond, choice, out)\n'
    else:
        for vnd__hepmp in range(len(choicelist) - 1, -1, -1):
            ylz__ooxm += f'  cond = condlist[{vnd__hepmp}]\n'
            ylz__ooxm += f'  choice = choicelist[{vnd__hepmp}]\n'
            ylz__ooxm += f'  out = np.where(cond, choice, out)\n'
    ylz__ooxm += '  return out'
    btemg__ueyt = dict()
    exec(ylz__ooxm, {'bodo': bodo, 'numba': numba, 'setna': bodo.libs.
        array_kernels.setna, 'np': np, 'alloc_typ': ybipr__oubqr}, btemg__ueyt)
    impl = btemg__ueyt['np_select_impl']
    return impl


@overload_method(SeriesType, 'duplicated', inline='always', no_unliteral=True)
def overload_series_duplicated(S, keep='first'):

    def impl(S, keep='first'):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        tit__ynq = bodo.libs.array_kernels.duplicated((arr,))
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index, name)
    return impl


@overload_method(SeriesType, 'drop_duplicates', inline='always',
    no_unliteral=True)
def overload_series_drop_duplicates(S, subset=None, keep='first', inplace=False
    ):
    vor__slq = dict(subset=subset, keep=keep, inplace=inplace)
    klgi__dxbz = dict(subset=None, keep='first', inplace=False)
    check_unsupported_args('Series.drop_duplicates', vor__slq, klgi__dxbz,
        package_name='pandas', module_name='Series')

    def impl(S, subset=None, keep='first', inplace=False):
        onpob__gnvn = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(S))
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        (onpob__gnvn,), uou__ghk = bodo.libs.array_kernels.drop_duplicates((
            onpob__gnvn,), index, 1)
        index = bodo.utils.conversion.index_from_array(uou__ghk)
        return bodo.hiframes.pd_series_ext.init_series(onpob__gnvn, index, name
            )
    return impl


@overload_method(SeriesType, 'between', inline='always', no_unliteral=True)
def overload_series_between(S, left, right, inclusive='both'):
    lxq__dxq = element_type(S.data)
    if not is_common_scalar_dtype([lxq__dxq, left]):
        raise_bodo_error(
            "Series.between(): 'left' must be compariable with the Series data"
            )
    if not is_common_scalar_dtype([lxq__dxq, right]):
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
        tit__ynq = np.empty(n, np.bool_)
        for vnd__hepmp in numba.parfors.parfor.internal_prange(n):
            hmdy__chlw = bodo.utils.conversion.box_if_dt64(arr[vnd__hepmp])
            if inclusive == 'both':
                tit__ynq[vnd__hepmp
                    ] = hmdy__chlw <= right and hmdy__chlw >= left
            else:
                tit__ynq[vnd__hepmp] = hmdy__chlw < right and hmdy__chlw > left
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq, index, name)
    return impl


@overload_method(SeriesType, 'repeat', inline='always', no_unliteral=True)
def overload_series_repeat(S, repeats, axis=None):
    vor__slq = dict(axis=axis)
    klgi__dxbz = dict(axis=None)
    check_unsupported_args('Series.repeat', vor__slq, klgi__dxbz,
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
            uou__ghk = bodo.utils.conversion.index_to_array(index)
            tit__ynq = bodo.libs.array_kernels.repeat_kernel(arr, repeats)
            jvlad__vcv = bodo.libs.array_kernels.repeat_kernel(uou__ghk,
                repeats)
            lvyyk__fqij = bodo.utils.conversion.index_from_array(jvlad__vcv)
            return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
                lvyyk__fqij, name)
        return impl_int

    def impl_arr(S, repeats, axis=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        name = bodo.hiframes.pd_series_ext.get_series_name(S)
        uou__ghk = bodo.utils.conversion.index_to_array(index)
        repeats = bodo.utils.conversion.coerce_to_array(repeats)
        tit__ynq = bodo.libs.array_kernels.repeat_kernel(arr, repeats)
        jvlad__vcv = bodo.libs.array_kernels.repeat_kernel(uou__ghk, repeats)
        lvyyk__fqij = bodo.utils.conversion.index_from_array(jvlad__vcv)
        return bodo.hiframes.pd_series_ext.init_series(tit__ynq,
            lvyyk__fqij, name)
    return impl_arr


@overload_method(SeriesType, 'to_dict', no_unliteral=True)
def overload_to_dict(S, into=None):

    def impl(S, into=None):
        oxn__key = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.utils.conversion.index_to_array(bodo.hiframes.
            pd_series_ext.get_series_index(S))
        n = len(oxn__key)
        btyup__rqvlo = {}
        for vnd__hepmp in range(n):
            hmdy__chlw = bodo.utils.conversion.box_if_dt64(oxn__key[vnd__hepmp]
                )
            btyup__rqvlo[index[vnd__hepmp]] = hmdy__chlw
        return btyup__rqvlo
    return impl


@overload_method(SeriesType, 'to_frame', inline='always', no_unliteral=True)
def overload_series_to_frame(S, name=None):
    skgzz__pasu = (
        "Series.to_frame(): output column name should be known at compile time. Set 'name' to a constant value."
        )
    if is_overload_none(name):
        if is_literal_type(S.name_typ):
            cxb__lir = get_literal_value(S.name_typ)
        else:
            raise_bodo_error(skgzz__pasu)
    elif is_literal_type(name):
        cxb__lir = get_literal_value(name)
    else:
        raise_bodo_error(skgzz__pasu)
    cxb__lir = 0 if cxb__lir is None else cxb__lir

    def impl(S, name=None):
        arr = bodo.hiframes.pd_series_ext.get_series_data(S)
        index = bodo.hiframes.pd_series_ext.get_series_index(S)
        return bodo.hiframes.pd_dataframe_ext.init_dataframe((arr,), index,
            (cxb__lir,))
    return impl


@overload_method(SeriesType, 'keys', inline='always', no_unliteral=True)
def overload_series_keys(S):

    def impl(S):
        return bodo.hiframes.pd_series_ext.get_series_index(S)
    return impl
