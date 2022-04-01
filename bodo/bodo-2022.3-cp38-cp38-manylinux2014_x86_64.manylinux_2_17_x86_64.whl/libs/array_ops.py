"""
Implements array operations for usage by DataFrames and Series
such as count and max.
"""
import numba
import numpy as np
import pandas as pd
from numba import generated_jit
from numba.core import types
from numba.extending import overload
import bodo
from bodo.hiframes.datetime_date_ext import datetime_date_array_type
from bodo.hiframes.pd_categorical_ext import CategoricalArrayType
from bodo.utils.typing import element_type, is_hashable_type, is_iterable_type, is_overload_true, is_overload_zero, is_str_arr_type


@numba.njit
def array_op_median(arr, skipna=True, parallel=False):
    ded__zvi = np.empty(1, types.float64)
    bodo.libs.array_kernels.median_series_computation(ded__zvi.ctypes, arr,
        parallel, skipna)
    return ded__zvi[0]


def array_op_isna(arr):
    pass


@overload(array_op_isna)
def overload_array_op_isna(arr):

    def impl(arr):
        numba.parfors.parfor.init_prange()
        ncpq__mog = len(arr)
        qqrir__ddkkl = np.empty(ncpq__mog, np.bool_)
        for umvpg__suy in numba.parfors.parfor.internal_prange(ncpq__mog):
            qqrir__ddkkl[umvpg__suy] = bodo.libs.array_kernels.isna(arr,
                umvpg__suy)
        return qqrir__ddkkl
    return impl


def array_op_count(arr):
    pass


@overload(array_op_count)
def overload_array_op_count(arr):

    def impl(arr):
        numba.parfors.parfor.init_prange()
        ixln__wksqs = 0
        for umvpg__suy in numba.parfors.parfor.internal_prange(len(arr)):
            vdur__xvlz = 0
            if not bodo.libs.array_kernels.isna(arr, umvpg__suy):
                vdur__xvlz = 1
            ixln__wksqs += vdur__xvlz
        ded__zvi = ixln__wksqs
        return ded__zvi
    return impl


def array_op_describe(arr):
    pass


def array_op_describe_impl(arr):
    eeqk__ctqs = array_op_count(arr)
    btrf__czu = array_op_min(arr)
    sqbkh__dtnxx = array_op_max(arr)
    wvn__mkwx = array_op_mean(arr)
    euuag__fyab = array_op_std(arr)
    bzaon__aof = array_op_quantile(arr, 0.25)
    zwk__glj = array_op_quantile(arr, 0.5)
    ere__yqy = array_op_quantile(arr, 0.75)
    return (eeqk__ctqs, wvn__mkwx, euuag__fyab, btrf__czu, bzaon__aof,
        zwk__glj, ere__yqy, sqbkh__dtnxx)


def array_op_describe_dt_impl(arr):
    eeqk__ctqs = array_op_count(arr)
    btrf__czu = array_op_min(arr)
    sqbkh__dtnxx = array_op_max(arr)
    wvn__mkwx = array_op_mean(arr)
    bzaon__aof = array_op_quantile(arr, 0.25)
    zwk__glj = array_op_quantile(arr, 0.5)
    ere__yqy = array_op_quantile(arr, 0.75)
    return (eeqk__ctqs, wvn__mkwx, btrf__czu, bzaon__aof, zwk__glj,
        ere__yqy, sqbkh__dtnxx)


@overload(array_op_describe)
def overload_array_op_describe(arr):
    if arr.dtype == bodo.datetime64ns:
        return array_op_describe_dt_impl
    return array_op_describe_impl


def array_op_min(arr):
    pass


@overload(array_op_min)
def overload_array_op_min(arr):
    if arr.dtype == bodo.timedelta64ns:

        def impl_td64(arr):
            numba.parfors.parfor.init_prange()
            sagfl__szpdn = numba.cpython.builtins.get_type_max_value(np.int64)
            ixln__wksqs = 0
            for umvpg__suy in numba.parfors.parfor.internal_prange(len(arr)):
                tffc__hbux = sagfl__szpdn
                vdur__xvlz = 0
                if not bodo.libs.array_kernels.isna(arr, umvpg__suy):
                    tffc__hbux = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(arr[umvpg__suy]))
                    vdur__xvlz = 1
                sagfl__szpdn = min(sagfl__szpdn, tffc__hbux)
                ixln__wksqs += vdur__xvlz
            return bodo.hiframes.pd_index_ext._tdi_val_finalize(sagfl__szpdn,
                ixln__wksqs)
        return impl_td64
    if arr.dtype == bodo.datetime64ns:

        def impl_dt64(arr):
            numba.parfors.parfor.init_prange()
            sagfl__szpdn = numba.cpython.builtins.get_type_max_value(np.int64)
            ixln__wksqs = 0
            for umvpg__suy in numba.parfors.parfor.internal_prange(len(arr)):
                tffc__hbux = sagfl__szpdn
                vdur__xvlz = 0
                if not bodo.libs.array_kernels.isna(arr, umvpg__suy):
                    tffc__hbux = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(arr[umvpg__suy]))
                    vdur__xvlz = 1
                sagfl__szpdn = min(sagfl__szpdn, tffc__hbux)
                ixln__wksqs += vdur__xvlz
            return bodo.hiframes.pd_index_ext._dti_val_finalize(sagfl__szpdn,
                ixln__wksqs)
        return impl_dt64
    if isinstance(arr, CategoricalArrayType):

        def impl_cat(arr):
            nmss__eolx = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            sagfl__szpdn = numba.cpython.builtins.get_type_max_value(np.int64)
            ixln__wksqs = 0
            for umvpg__suy in numba.parfors.parfor.internal_prange(len(
                nmss__eolx)):
                foz__amppt = nmss__eolx[umvpg__suy]
                if foz__amppt == -1:
                    continue
                sagfl__szpdn = min(sagfl__szpdn, foz__amppt)
                ixln__wksqs += 1
            ded__zvi = bodo.hiframes.series_kernels._box_cat_val(sagfl__szpdn,
                arr.dtype, ixln__wksqs)
            return ded__zvi
        return impl_cat
    if arr == datetime_date_array_type:

        def impl_date(arr):
            numba.parfors.parfor.init_prange()
            sagfl__szpdn = bodo.hiframes.series_kernels._get_date_max_value()
            ixln__wksqs = 0
            for umvpg__suy in numba.parfors.parfor.internal_prange(len(arr)):
                tffc__hbux = sagfl__szpdn
                vdur__xvlz = 0
                if not bodo.libs.array_kernels.isna(arr, umvpg__suy):
                    tffc__hbux = arr[umvpg__suy]
                    vdur__xvlz = 1
                sagfl__szpdn = min(sagfl__szpdn, tffc__hbux)
                ixln__wksqs += vdur__xvlz
            ded__zvi = bodo.hiframes.series_kernels._sum_handle_nan(
                sagfl__szpdn, ixln__wksqs)
            return ded__zvi
        return impl_date

    def impl(arr):
        numba.parfors.parfor.init_prange()
        sagfl__szpdn = bodo.hiframes.series_kernels._get_type_max_value(arr
            .dtype)
        ixln__wksqs = 0
        for umvpg__suy in numba.parfors.parfor.internal_prange(len(arr)):
            tffc__hbux = sagfl__szpdn
            vdur__xvlz = 0
            if not bodo.libs.array_kernels.isna(arr, umvpg__suy):
                tffc__hbux = arr[umvpg__suy]
                vdur__xvlz = 1
            sagfl__szpdn = min(sagfl__szpdn, tffc__hbux)
            ixln__wksqs += vdur__xvlz
        ded__zvi = bodo.hiframes.series_kernels._sum_handle_nan(sagfl__szpdn,
            ixln__wksqs)
        return ded__zvi
    return impl


def array_op_max(arr):
    pass


@overload(array_op_max)
def overload_array_op_max(arr):
    if arr.dtype == bodo.timedelta64ns:

        def impl_td64(arr):
            numba.parfors.parfor.init_prange()
            sagfl__szpdn = numba.cpython.builtins.get_type_min_value(np.int64)
            ixln__wksqs = 0
            for umvpg__suy in numba.parfors.parfor.internal_prange(len(arr)):
                tffc__hbux = sagfl__szpdn
                vdur__xvlz = 0
                if not bodo.libs.array_kernels.isna(arr, umvpg__suy):
                    tffc__hbux = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(arr[umvpg__suy]))
                    vdur__xvlz = 1
                sagfl__szpdn = max(sagfl__szpdn, tffc__hbux)
                ixln__wksqs += vdur__xvlz
            return bodo.hiframes.pd_index_ext._tdi_val_finalize(sagfl__szpdn,
                ixln__wksqs)
        return impl_td64
    if arr.dtype == bodo.datetime64ns:

        def impl_dt64(arr):
            numba.parfors.parfor.init_prange()
            sagfl__szpdn = numba.cpython.builtins.get_type_min_value(np.int64)
            ixln__wksqs = 0
            for umvpg__suy in numba.parfors.parfor.internal_prange(len(arr)):
                tffc__hbux = sagfl__szpdn
                vdur__xvlz = 0
                if not bodo.libs.array_kernels.isna(arr, umvpg__suy):
                    tffc__hbux = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(arr[umvpg__suy]))
                    vdur__xvlz = 1
                sagfl__szpdn = max(sagfl__szpdn, tffc__hbux)
                ixln__wksqs += vdur__xvlz
            return bodo.hiframes.pd_index_ext._dti_val_finalize(sagfl__szpdn,
                ixln__wksqs)
        return impl_dt64
    if isinstance(arr, CategoricalArrayType):

        def impl_cat(arr):
            nmss__eolx = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            sagfl__szpdn = -1
            for umvpg__suy in numba.parfors.parfor.internal_prange(len(
                nmss__eolx)):
                sagfl__szpdn = max(sagfl__szpdn, nmss__eolx[umvpg__suy])
            ded__zvi = bodo.hiframes.series_kernels._box_cat_val(sagfl__szpdn,
                arr.dtype, 1)
            return ded__zvi
        return impl_cat
    if arr == datetime_date_array_type:

        def impl_date(arr):
            numba.parfors.parfor.init_prange()
            sagfl__szpdn = bodo.hiframes.series_kernels._get_date_min_value()
            ixln__wksqs = 0
            for umvpg__suy in numba.parfors.parfor.internal_prange(len(arr)):
                tffc__hbux = sagfl__szpdn
                vdur__xvlz = 0
                if not bodo.libs.array_kernels.isna(arr, umvpg__suy):
                    tffc__hbux = arr[umvpg__suy]
                    vdur__xvlz = 1
                sagfl__szpdn = max(sagfl__szpdn, tffc__hbux)
                ixln__wksqs += vdur__xvlz
            ded__zvi = bodo.hiframes.series_kernels._sum_handle_nan(
                sagfl__szpdn, ixln__wksqs)
            return ded__zvi
        return impl_date

    def impl(arr):
        numba.parfors.parfor.init_prange()
        sagfl__szpdn = bodo.hiframes.series_kernels._get_type_min_value(arr
            .dtype)
        ixln__wksqs = 0
        for umvpg__suy in numba.parfors.parfor.internal_prange(len(arr)):
            tffc__hbux = sagfl__szpdn
            vdur__xvlz = 0
            if not bodo.libs.array_kernels.isna(arr, umvpg__suy):
                tffc__hbux = arr[umvpg__suy]
                vdur__xvlz = 1
            sagfl__szpdn = max(sagfl__szpdn, tffc__hbux)
            ixln__wksqs += vdur__xvlz
        ded__zvi = bodo.hiframes.series_kernels._sum_handle_nan(sagfl__szpdn,
            ixln__wksqs)
        return ded__zvi
    return impl


def array_op_mean(arr):
    pass


@overload(array_op_mean)
def overload_array_op_mean(arr):
    if arr.dtype == bodo.datetime64ns:

        def impl(arr):
            return pd.Timestamp(types.int64(bodo.libs.array_ops.
                array_op_mean(arr.view(np.int64))))
        return impl
    rbsub__hni = types.float64
    pkv__blr = types.float64
    if isinstance(arr, types.Array) and arr.dtype == types.float32:
        rbsub__hni = types.float32
        pkv__blr = types.float32
    wmct__ccm = rbsub__hni(0)
    hquq__sjqr = pkv__blr(0)
    sogxh__lieca = pkv__blr(1)

    def impl(arr):
        numba.parfors.parfor.init_prange()
        sagfl__szpdn = wmct__ccm
        ixln__wksqs = hquq__sjqr
        for umvpg__suy in numba.parfors.parfor.internal_prange(len(arr)):
            tffc__hbux = wmct__ccm
            vdur__xvlz = hquq__sjqr
            if not bodo.libs.array_kernels.isna(arr, umvpg__suy):
                tffc__hbux = arr[umvpg__suy]
                vdur__xvlz = sogxh__lieca
            sagfl__szpdn += tffc__hbux
            ixln__wksqs += vdur__xvlz
        ded__zvi = bodo.hiframes.series_kernels._mean_handle_nan(sagfl__szpdn,
            ixln__wksqs)
        return ded__zvi
    return impl


def array_op_var(arr, skipna, ddof):
    pass


@overload(array_op_var)
def overload_array_op_var(arr, skipna, ddof):

    def impl(arr, skipna, ddof):
        numba.parfors.parfor.init_prange()
        tmd__bsmu = 0.0
        ovbt__glb = 0.0
        ixln__wksqs = 0
        for umvpg__suy in numba.parfors.parfor.internal_prange(len(arr)):
            tffc__hbux = 0.0
            vdur__xvlz = 0
            if not bodo.libs.array_kernels.isna(arr, umvpg__suy) or not skipna:
                tffc__hbux = arr[umvpg__suy]
                vdur__xvlz = 1
            tmd__bsmu += tffc__hbux
            ovbt__glb += tffc__hbux * tffc__hbux
            ixln__wksqs += vdur__xvlz
        ded__zvi = bodo.hiframes.series_kernels._compute_var_nan_count_ddof(
            tmd__bsmu, ovbt__glb, ixln__wksqs, ddof)
        return ded__zvi
    return impl


def array_op_std(arr, skipna=True, ddof=1):
    pass


@overload(array_op_std)
def overload_array_op_std(arr, skipna=True, ddof=1):
    if arr.dtype == bodo.datetime64ns:

        def impl_dt64(arr, skipna=True, ddof=1):
            return pd.Timedelta(types.int64(array_op_var(arr.view(np.int64),
                skipna, ddof) ** 0.5))
        return impl_dt64
    return lambda arr, skipna=True, ddof=1: array_op_var(arr, skipna, ddof
        ) ** 0.5


def array_op_quantile(arr, q):
    pass


@overload(array_op_quantile)
def overload_array_op_quantile(arr, q):
    if is_iterable_type(q):
        if arr.dtype == bodo.datetime64ns:

            def _impl_list_dt(arr, q):
                qqrir__ddkkl = np.empty(len(q), np.int64)
                for umvpg__suy in range(len(q)):
                    cjv__qbgvt = np.float64(q[umvpg__suy])
                    qqrir__ddkkl[umvpg__suy
                        ] = bodo.libs.array_kernels.quantile(arr.view(np.
                        int64), cjv__qbgvt)
                return qqrir__ddkkl.view(np.dtype('datetime64[ns]'))
            return _impl_list_dt

        def impl_list(arr, q):
            qqrir__ddkkl = np.empty(len(q), np.float64)
            for umvpg__suy in range(len(q)):
                cjv__qbgvt = np.float64(q[umvpg__suy])
                qqrir__ddkkl[umvpg__suy] = bodo.libs.array_kernels.quantile(arr
                    , cjv__qbgvt)
            return qqrir__ddkkl
        return impl_list
    if arr.dtype == bodo.datetime64ns:

        def _impl_dt(arr, q):
            return pd.Timestamp(bodo.libs.array_kernels.quantile(arr.view(
                np.int64), np.float64(q)))
        return _impl_dt

    def impl(arr, q):
        return bodo.libs.array_kernels.quantile(arr, np.float64(q))
    return impl


def array_op_sum(arr, skipna, min_count):
    pass


@overload(array_op_sum, no_unliteral=True)
def overload_array_op_sum(arr, skipna, min_count):
    if isinstance(arr.dtype, types.Integer):
        cqbz__mmp = types.intp
    elif arr.dtype == types.bool_:
        cqbz__mmp = np.int64
    else:
        cqbz__mmp = arr.dtype
    elzb__wpd = cqbz__mmp(0)
    if isinstance(arr.dtype, types.Float) and (not is_overload_true(skipna) or
        not is_overload_zero(min_count)):

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            sagfl__szpdn = elzb__wpd
            ncpq__mog = len(arr)
            ixln__wksqs = 0
            for umvpg__suy in numba.parfors.parfor.internal_prange(ncpq__mog):
                tffc__hbux = elzb__wpd
                vdur__xvlz = 0
                if not bodo.libs.array_kernels.isna(arr, umvpg__suy
                    ) or not skipna:
                    tffc__hbux = arr[umvpg__suy]
                    vdur__xvlz = 1
                sagfl__szpdn += tffc__hbux
                ixln__wksqs += vdur__xvlz
            ded__zvi = bodo.hiframes.series_kernels._var_handle_mincount(
                sagfl__szpdn, ixln__wksqs, min_count)
            return ded__zvi
    else:

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            sagfl__szpdn = elzb__wpd
            ncpq__mog = len(arr)
            for umvpg__suy in numba.parfors.parfor.internal_prange(ncpq__mog):
                tffc__hbux = elzb__wpd
                if not bodo.libs.array_kernels.isna(arr, umvpg__suy):
                    tffc__hbux = arr[umvpg__suy]
                sagfl__szpdn += tffc__hbux
            return sagfl__szpdn
    return impl


def array_op_prod(arr, skipna, min_count):
    pass


@overload(array_op_prod)
def overload_array_op_prod(arr, skipna, min_count):
    eou__gssav = arr.dtype(1)
    if arr.dtype == types.bool_:
        eou__gssav = 1
    if isinstance(arr.dtype, types.Float):

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            sagfl__szpdn = eou__gssav
            ixln__wksqs = 0
            for umvpg__suy in numba.parfors.parfor.internal_prange(len(arr)):
                tffc__hbux = eou__gssav
                vdur__xvlz = 0
                if not bodo.libs.array_kernels.isna(arr, umvpg__suy
                    ) or not skipna:
                    tffc__hbux = arr[umvpg__suy]
                    vdur__xvlz = 1
                ixln__wksqs += vdur__xvlz
                sagfl__szpdn *= tffc__hbux
            ded__zvi = bodo.hiframes.series_kernels._var_handle_mincount(
                sagfl__szpdn, ixln__wksqs, min_count)
            return ded__zvi
    else:

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            sagfl__szpdn = eou__gssav
            for umvpg__suy in numba.parfors.parfor.internal_prange(len(arr)):
                tffc__hbux = eou__gssav
                if not bodo.libs.array_kernels.isna(arr, umvpg__suy):
                    tffc__hbux = arr[umvpg__suy]
                sagfl__szpdn *= tffc__hbux
            return sagfl__szpdn
    return impl


def array_op_idxmax(arr, index):
    pass


@overload(array_op_idxmax, inline='always')
def overload_array_op_idxmax(arr, index):

    def impl(arr, index):
        umvpg__suy = bodo.libs.array_kernels._nan_argmax(arr)
        return index[umvpg__suy]
    return impl


def array_op_idxmin(arr, index):
    pass


@overload(array_op_idxmin, inline='always')
def overload_array_op_idxmin(arr, index):

    def impl(arr, index):
        umvpg__suy = bodo.libs.array_kernels._nan_argmin(arr)
        return index[umvpg__suy]
    return impl


def _convert_isin_values(values, use_hash_impl):
    pass


@overload(_convert_isin_values, no_unliteral=True)
def overload_convert_isin_values(values, use_hash_impl):
    if is_overload_true(use_hash_impl):

        def impl(values, use_hash_impl):
            zpjd__xjqp = {}
            for jabm__jxh in values:
                zpjd__xjqp[bodo.utils.conversion.box_if_dt64(jabm__jxh)] = 0
            return zpjd__xjqp
        return impl
    else:

        def impl(values, use_hash_impl):
            return values
        return impl


def array_op_isin(arr, values):
    pass


@overload(array_op_isin, inline='always')
def overload_array_op_isin(arr, values):
    use_hash_impl = element_type(values) == element_type(arr
        ) and is_hashable_type(element_type(values))

    def impl(arr, values):
        values = bodo.libs.array_ops._convert_isin_values(values, use_hash_impl
            )
        numba.parfors.parfor.init_prange()
        ncpq__mog = len(arr)
        qqrir__ddkkl = np.empty(ncpq__mog, np.bool_)
        for umvpg__suy in numba.parfors.parfor.internal_prange(ncpq__mog):
            qqrir__ddkkl[umvpg__suy] = bodo.utils.conversion.box_if_dt64(arr
                [umvpg__suy]) in values
        return qqrir__ddkkl
    return impl


@generated_jit(nopython=True)
def array_unique_vector_map(in_arr_tup):
    otlao__jctpj = len(in_arr_tup) != 1
    shz__izf = list(in_arr_tup.types)
    ihsc__dfpg = 'def impl(in_arr_tup):\n'
    ihsc__dfpg += '  n = len(in_arr_tup[0])\n'
    if otlao__jctpj:
        hjm__iwjo = ', '.join([f'in_arr_tup[{umvpg__suy}][unused]' for
            umvpg__suy in range(len(in_arr_tup))])
        ani__yki = ', '.join(['False' for uazkz__tmp in range(len(in_arr_tup))]
            )
        ihsc__dfpg += f"""  arr_map = {{bodo.libs.nullable_tuple_ext.build_nullable_tuple(({hjm__iwjo},), ({ani__yki},)): 0 for unused in range(0)}}
"""
        ihsc__dfpg += '  map_vector = np.empty(n, np.int64)\n'
        for umvpg__suy, plbw__fbff in enumerate(shz__izf):
            ihsc__dfpg += f'  in_lst_{umvpg__suy} = []\n'
            if is_str_arr_type(plbw__fbff):
                ihsc__dfpg += f'  total_len_{umvpg__suy} = 0\n'
            ihsc__dfpg += f'  null_in_lst_{umvpg__suy} = []\n'
        ihsc__dfpg += '  for i in range(n):\n'
        iak__rkj = ', '.join([f'in_arr_tup[{umvpg__suy}][i]' for umvpg__suy in
            range(len(shz__izf))])
        ifvxc__kcdtj = ', '.join([
            f'bodo.libs.array_kernels.isna(in_arr_tup[{umvpg__suy}], i)' for
            umvpg__suy in range(len(shz__izf))])
        ihsc__dfpg += f"""    data_val = bodo.libs.nullable_tuple_ext.build_nullable_tuple(({iak__rkj},), ({ifvxc__kcdtj},))
"""
        ihsc__dfpg += '    if data_val not in arr_map:\n'
        ihsc__dfpg += '      set_val = len(arr_map)\n'
        ihsc__dfpg += '      values_tup = data_val._data\n'
        ihsc__dfpg += '      nulls_tup = data_val._null_values\n'
        for umvpg__suy, plbw__fbff in enumerate(shz__izf):
            ihsc__dfpg += (
                f'      in_lst_{umvpg__suy}.append(values_tup[{umvpg__suy}])\n'
                )
            ihsc__dfpg += (
                f'      null_in_lst_{umvpg__suy}.append(nulls_tup[{umvpg__suy}])\n'
                )
            if is_str_arr_type(plbw__fbff):
                ihsc__dfpg += f"""      total_len_{umvpg__suy}  += nulls_tup[{umvpg__suy}] * len(values_tup[{umvpg__suy}])
"""
        ihsc__dfpg += '      arr_map[data_val] = len(arr_map)\n'
        ihsc__dfpg += '    else:\n'
        ihsc__dfpg += '      set_val = arr_map[data_val]\n'
        ihsc__dfpg += '    map_vector[i] = set_val\n'
        ihsc__dfpg += '  n_rows = len(arr_map)\n'
        for umvpg__suy, plbw__fbff in enumerate(shz__izf):
            if is_str_arr_type(plbw__fbff):
                ihsc__dfpg += f"""  out_arr_{umvpg__suy} = bodo.libs.str_arr_ext.pre_alloc_string_array(n_rows, total_len_{umvpg__suy})
"""
            else:
                ihsc__dfpg += f"""  out_arr_{umvpg__suy} = bodo.utils.utils.alloc_type(n_rows, in_arr_tup[{umvpg__suy}], (-1,))
"""
        ihsc__dfpg += '  for j in range(len(arr_map)):\n'
        for umvpg__suy in range(len(shz__izf)):
            ihsc__dfpg += f'    if null_in_lst_{umvpg__suy}[j]:\n'
            ihsc__dfpg += (
                f'      bodo.libs.array_kernels.setna(out_arr_{umvpg__suy}, j)\n'
                )
            ihsc__dfpg += '    else:\n'
            ihsc__dfpg += (
                f'      out_arr_{umvpg__suy}[j] = in_lst_{umvpg__suy}[j]\n')
        mmjnm__inu = ', '.join([f'out_arr_{umvpg__suy}' for umvpg__suy in
            range(len(shz__izf))])
        ihsc__dfpg += f'  return ({mmjnm__inu},), map_vector\n'
    else:
        ihsc__dfpg += '  in_arr = in_arr_tup[0]\n'
        ihsc__dfpg += (
            f'  arr_map = {{in_arr[unused]: 0 for unused in range(0)}}\n')
        ihsc__dfpg += '  map_vector = np.empty(n, np.int64)\n'
        ihsc__dfpg += '  is_na = 0\n'
        ihsc__dfpg += '  in_lst = []\n'
        if is_str_arr_type(shz__izf[0]):
            ihsc__dfpg += '  total_len = 0\n'
        ihsc__dfpg += '  for i in range(n):\n'
        ihsc__dfpg += '    if bodo.libs.array_kernels.isna(in_arr, i):\n'
        ihsc__dfpg += '      is_na = 1\n'
        ihsc__dfpg += (
            '      # Always put NA in the last location. We can safely use\n')
        ihsc__dfpg += (
            '      # -1 because in_arr[-1] == in_arr[len(in_arr) - 1]\n')
        ihsc__dfpg += '      set_val = -1\n'
        ihsc__dfpg += '    else:\n'
        ihsc__dfpg += '      data_val = in_arr[i]\n'
        ihsc__dfpg += '      if data_val not in arr_map:\n'
        ihsc__dfpg += '        set_val = len(arr_map)\n'
        ihsc__dfpg += '        in_lst.append(data_val)\n'
        if is_str_arr_type(shz__izf[0]):
            ihsc__dfpg += '        total_len += len(data_val)\n'
        ihsc__dfpg += '        arr_map[data_val] = len(arr_map)\n'
        ihsc__dfpg += '      else:\n'
        ihsc__dfpg += '        set_val = arr_map[data_val]\n'
        ihsc__dfpg += '    map_vector[i] = set_val\n'
        ihsc__dfpg += '  n_rows = len(arr_map) + is_na\n'
        if is_str_arr_type(shz__izf[0]):
            ihsc__dfpg += """  out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(n_rows, total_len)
"""
        else:
            ihsc__dfpg += (
                '  out_arr = bodo.utils.utils.alloc_type(n_rows, in_arr, (-1,))\n'
                )
        ihsc__dfpg += '  for j in range(len(arr_map)):\n'
        ihsc__dfpg += '    out_arr[j] = in_lst[j]\n'
        ihsc__dfpg += '  if is_na:\n'
        ihsc__dfpg += (
            '    bodo.libs.array_kernels.setna(out_arr, n_rows - 1)\n')
        ihsc__dfpg += f'  return (out_arr,), map_vector\n'
    uymx__qxjw = {}
    exec(ihsc__dfpg, {'bodo': bodo, 'np': np}, uymx__qxjw)
    impl = uymx__qxjw['impl']
    return impl
