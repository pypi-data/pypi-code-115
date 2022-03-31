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
    ucpo__hbxpp = np.empty(1, types.float64)
    bodo.libs.array_kernels.median_series_computation(ucpo__hbxpp.ctypes,
        arr, parallel, skipna)
    return ucpo__hbxpp[0]


def array_op_isna(arr):
    pass


@overload(array_op_isna)
def overload_array_op_isna(arr):

    def impl(arr):
        numba.parfors.parfor.init_prange()
        rkbc__seiaw = len(arr)
        vcw__pls = np.empty(rkbc__seiaw, np.bool_)
        for rvst__pjed in numba.parfors.parfor.internal_prange(rkbc__seiaw):
            vcw__pls[rvst__pjed] = bodo.libs.array_kernels.isna(arr, rvst__pjed
                )
        return vcw__pls
    return impl


def array_op_count(arr):
    pass


@overload(array_op_count)
def overload_array_op_count(arr):

    def impl(arr):
        numba.parfors.parfor.init_prange()
        mjz__ygxed = 0
        for rvst__pjed in numba.parfors.parfor.internal_prange(len(arr)):
            sbt__nwaf = 0
            if not bodo.libs.array_kernels.isna(arr, rvst__pjed):
                sbt__nwaf = 1
            mjz__ygxed += sbt__nwaf
        ucpo__hbxpp = mjz__ygxed
        return ucpo__hbxpp
    return impl


def array_op_describe(arr):
    pass


def array_op_describe_impl(arr):
    fgprt__fhpsn = array_op_count(arr)
    vio__lhqx = array_op_min(arr)
    cxdlw__awych = array_op_max(arr)
    mupx__lsvcj = array_op_mean(arr)
    rgfaj__qmgcp = array_op_std(arr)
    sgrd__xlvts = array_op_quantile(arr, 0.25)
    zuc__pqq = array_op_quantile(arr, 0.5)
    txezu__addt = array_op_quantile(arr, 0.75)
    return (fgprt__fhpsn, mupx__lsvcj, rgfaj__qmgcp, vio__lhqx, sgrd__xlvts,
        zuc__pqq, txezu__addt, cxdlw__awych)


def array_op_describe_dt_impl(arr):
    fgprt__fhpsn = array_op_count(arr)
    vio__lhqx = array_op_min(arr)
    cxdlw__awych = array_op_max(arr)
    mupx__lsvcj = array_op_mean(arr)
    sgrd__xlvts = array_op_quantile(arr, 0.25)
    zuc__pqq = array_op_quantile(arr, 0.5)
    txezu__addt = array_op_quantile(arr, 0.75)
    return (fgprt__fhpsn, mupx__lsvcj, vio__lhqx, sgrd__xlvts, zuc__pqq,
        txezu__addt, cxdlw__awych)


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
            wvnfn__cozif = numba.cpython.builtins.get_type_max_value(np.int64)
            mjz__ygxed = 0
            for rvst__pjed in numba.parfors.parfor.internal_prange(len(arr)):
                dimlt__yky = wvnfn__cozif
                sbt__nwaf = 0
                if not bodo.libs.array_kernels.isna(arr, rvst__pjed):
                    dimlt__yky = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(arr[rvst__pjed]))
                    sbt__nwaf = 1
                wvnfn__cozif = min(wvnfn__cozif, dimlt__yky)
                mjz__ygxed += sbt__nwaf
            return bodo.hiframes.pd_index_ext._tdi_val_finalize(wvnfn__cozif,
                mjz__ygxed)
        return impl_td64
    if arr.dtype == bodo.datetime64ns:

        def impl_dt64(arr):
            numba.parfors.parfor.init_prange()
            wvnfn__cozif = numba.cpython.builtins.get_type_max_value(np.int64)
            mjz__ygxed = 0
            for rvst__pjed in numba.parfors.parfor.internal_prange(len(arr)):
                dimlt__yky = wvnfn__cozif
                sbt__nwaf = 0
                if not bodo.libs.array_kernels.isna(arr, rvst__pjed):
                    dimlt__yky = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(arr[rvst__pjed]))
                    sbt__nwaf = 1
                wvnfn__cozif = min(wvnfn__cozif, dimlt__yky)
                mjz__ygxed += sbt__nwaf
            return bodo.hiframes.pd_index_ext._dti_val_finalize(wvnfn__cozif,
                mjz__ygxed)
        return impl_dt64
    if isinstance(arr, CategoricalArrayType):

        def impl_cat(arr):
            zenqa__old = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            wvnfn__cozif = numba.cpython.builtins.get_type_max_value(np.int64)
            mjz__ygxed = 0
            for rvst__pjed in numba.parfors.parfor.internal_prange(len(
                zenqa__old)):
                iwey__eguxn = zenqa__old[rvst__pjed]
                if iwey__eguxn == -1:
                    continue
                wvnfn__cozif = min(wvnfn__cozif, iwey__eguxn)
                mjz__ygxed += 1
            ucpo__hbxpp = bodo.hiframes.series_kernels._box_cat_val(
                wvnfn__cozif, arr.dtype, mjz__ygxed)
            return ucpo__hbxpp
        return impl_cat
    if arr == datetime_date_array_type:

        def impl_date(arr):
            numba.parfors.parfor.init_prange()
            wvnfn__cozif = bodo.hiframes.series_kernels._get_date_max_value()
            mjz__ygxed = 0
            for rvst__pjed in numba.parfors.parfor.internal_prange(len(arr)):
                dimlt__yky = wvnfn__cozif
                sbt__nwaf = 0
                if not bodo.libs.array_kernels.isna(arr, rvst__pjed):
                    dimlt__yky = arr[rvst__pjed]
                    sbt__nwaf = 1
                wvnfn__cozif = min(wvnfn__cozif, dimlt__yky)
                mjz__ygxed += sbt__nwaf
            ucpo__hbxpp = bodo.hiframes.series_kernels._sum_handle_nan(
                wvnfn__cozif, mjz__ygxed)
            return ucpo__hbxpp
        return impl_date

    def impl(arr):
        numba.parfors.parfor.init_prange()
        wvnfn__cozif = bodo.hiframes.series_kernels._get_type_max_value(arr
            .dtype)
        mjz__ygxed = 0
        for rvst__pjed in numba.parfors.parfor.internal_prange(len(arr)):
            dimlt__yky = wvnfn__cozif
            sbt__nwaf = 0
            if not bodo.libs.array_kernels.isna(arr, rvst__pjed):
                dimlt__yky = arr[rvst__pjed]
                sbt__nwaf = 1
            wvnfn__cozif = min(wvnfn__cozif, dimlt__yky)
            mjz__ygxed += sbt__nwaf
        ucpo__hbxpp = bodo.hiframes.series_kernels._sum_handle_nan(wvnfn__cozif
            , mjz__ygxed)
        return ucpo__hbxpp
    return impl


def array_op_max(arr):
    pass


@overload(array_op_max)
def overload_array_op_max(arr):
    if arr.dtype == bodo.timedelta64ns:

        def impl_td64(arr):
            numba.parfors.parfor.init_prange()
            wvnfn__cozif = numba.cpython.builtins.get_type_min_value(np.int64)
            mjz__ygxed = 0
            for rvst__pjed in numba.parfors.parfor.internal_prange(len(arr)):
                dimlt__yky = wvnfn__cozif
                sbt__nwaf = 0
                if not bodo.libs.array_kernels.isna(arr, rvst__pjed):
                    dimlt__yky = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(arr[rvst__pjed]))
                    sbt__nwaf = 1
                wvnfn__cozif = max(wvnfn__cozif, dimlt__yky)
                mjz__ygxed += sbt__nwaf
            return bodo.hiframes.pd_index_ext._tdi_val_finalize(wvnfn__cozif,
                mjz__ygxed)
        return impl_td64
    if arr.dtype == bodo.datetime64ns:

        def impl_dt64(arr):
            numba.parfors.parfor.init_prange()
            wvnfn__cozif = numba.cpython.builtins.get_type_min_value(np.int64)
            mjz__ygxed = 0
            for rvst__pjed in numba.parfors.parfor.internal_prange(len(arr)):
                dimlt__yky = wvnfn__cozif
                sbt__nwaf = 0
                if not bodo.libs.array_kernels.isna(arr, rvst__pjed):
                    dimlt__yky = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(arr[rvst__pjed]))
                    sbt__nwaf = 1
                wvnfn__cozif = max(wvnfn__cozif, dimlt__yky)
                mjz__ygxed += sbt__nwaf
            return bodo.hiframes.pd_index_ext._dti_val_finalize(wvnfn__cozif,
                mjz__ygxed)
        return impl_dt64
    if isinstance(arr, CategoricalArrayType):

        def impl_cat(arr):
            zenqa__old = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            wvnfn__cozif = -1
            for rvst__pjed in numba.parfors.parfor.internal_prange(len(
                zenqa__old)):
                wvnfn__cozif = max(wvnfn__cozif, zenqa__old[rvst__pjed])
            ucpo__hbxpp = bodo.hiframes.series_kernels._box_cat_val(
                wvnfn__cozif, arr.dtype, 1)
            return ucpo__hbxpp
        return impl_cat
    if arr == datetime_date_array_type:

        def impl_date(arr):
            numba.parfors.parfor.init_prange()
            wvnfn__cozif = bodo.hiframes.series_kernels._get_date_min_value()
            mjz__ygxed = 0
            for rvst__pjed in numba.parfors.parfor.internal_prange(len(arr)):
                dimlt__yky = wvnfn__cozif
                sbt__nwaf = 0
                if not bodo.libs.array_kernels.isna(arr, rvst__pjed):
                    dimlt__yky = arr[rvst__pjed]
                    sbt__nwaf = 1
                wvnfn__cozif = max(wvnfn__cozif, dimlt__yky)
                mjz__ygxed += sbt__nwaf
            ucpo__hbxpp = bodo.hiframes.series_kernels._sum_handle_nan(
                wvnfn__cozif, mjz__ygxed)
            return ucpo__hbxpp
        return impl_date

    def impl(arr):
        numba.parfors.parfor.init_prange()
        wvnfn__cozif = bodo.hiframes.series_kernels._get_type_min_value(arr
            .dtype)
        mjz__ygxed = 0
        for rvst__pjed in numba.parfors.parfor.internal_prange(len(arr)):
            dimlt__yky = wvnfn__cozif
            sbt__nwaf = 0
            if not bodo.libs.array_kernels.isna(arr, rvst__pjed):
                dimlt__yky = arr[rvst__pjed]
                sbt__nwaf = 1
            wvnfn__cozif = max(wvnfn__cozif, dimlt__yky)
            mjz__ygxed += sbt__nwaf
        ucpo__hbxpp = bodo.hiframes.series_kernels._sum_handle_nan(wvnfn__cozif
            , mjz__ygxed)
        return ucpo__hbxpp
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
    egca__nvbjg = types.float64
    jbax__dbtxy = types.float64
    if isinstance(arr, types.Array) and arr.dtype == types.float32:
        egca__nvbjg = types.float32
        jbax__dbtxy = types.float32
    xqwg__zad = egca__nvbjg(0)
    mrq__nfkgn = jbax__dbtxy(0)
    plo__bdnz = jbax__dbtxy(1)

    def impl(arr):
        numba.parfors.parfor.init_prange()
        wvnfn__cozif = xqwg__zad
        mjz__ygxed = mrq__nfkgn
        for rvst__pjed in numba.parfors.parfor.internal_prange(len(arr)):
            dimlt__yky = xqwg__zad
            sbt__nwaf = mrq__nfkgn
            if not bodo.libs.array_kernels.isna(arr, rvst__pjed):
                dimlt__yky = arr[rvst__pjed]
                sbt__nwaf = plo__bdnz
            wvnfn__cozif += dimlt__yky
            mjz__ygxed += sbt__nwaf
        ucpo__hbxpp = bodo.hiframes.series_kernels._mean_handle_nan(
            wvnfn__cozif, mjz__ygxed)
        return ucpo__hbxpp
    return impl


def array_op_var(arr, skipna, ddof):
    pass


@overload(array_op_var)
def overload_array_op_var(arr, skipna, ddof):

    def impl(arr, skipna, ddof):
        numba.parfors.parfor.init_prange()
        oan__yio = 0.0
        ijj__gxf = 0.0
        mjz__ygxed = 0
        for rvst__pjed in numba.parfors.parfor.internal_prange(len(arr)):
            dimlt__yky = 0.0
            sbt__nwaf = 0
            if not bodo.libs.array_kernels.isna(arr, rvst__pjed) or not skipna:
                dimlt__yky = arr[rvst__pjed]
                sbt__nwaf = 1
            oan__yio += dimlt__yky
            ijj__gxf += dimlt__yky * dimlt__yky
            mjz__ygxed += sbt__nwaf
        ucpo__hbxpp = bodo.hiframes.series_kernels._compute_var_nan_count_ddof(
            oan__yio, ijj__gxf, mjz__ygxed, ddof)
        return ucpo__hbxpp
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
                vcw__pls = np.empty(len(q), np.int64)
                for rvst__pjed in range(len(q)):
                    axkai__nrdx = np.float64(q[rvst__pjed])
                    vcw__pls[rvst__pjed] = bodo.libs.array_kernels.quantile(arr
                        .view(np.int64), axkai__nrdx)
                return vcw__pls.view(np.dtype('datetime64[ns]'))
            return _impl_list_dt

        def impl_list(arr, q):
            vcw__pls = np.empty(len(q), np.float64)
            for rvst__pjed in range(len(q)):
                axkai__nrdx = np.float64(q[rvst__pjed])
                vcw__pls[rvst__pjed] = bodo.libs.array_kernels.quantile(arr,
                    axkai__nrdx)
            return vcw__pls
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
        jvqw__fix = types.intp
    elif arr.dtype == types.bool_:
        jvqw__fix = np.int64
    else:
        jvqw__fix = arr.dtype
    cxm__iebq = jvqw__fix(0)
    if isinstance(arr.dtype, types.Float) and (not is_overload_true(skipna) or
        not is_overload_zero(min_count)):

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            wvnfn__cozif = cxm__iebq
            rkbc__seiaw = len(arr)
            mjz__ygxed = 0
            for rvst__pjed in numba.parfors.parfor.internal_prange(rkbc__seiaw
                ):
                dimlt__yky = cxm__iebq
                sbt__nwaf = 0
                if not bodo.libs.array_kernels.isna(arr, rvst__pjed
                    ) or not skipna:
                    dimlt__yky = arr[rvst__pjed]
                    sbt__nwaf = 1
                wvnfn__cozif += dimlt__yky
                mjz__ygxed += sbt__nwaf
            ucpo__hbxpp = bodo.hiframes.series_kernels._var_handle_mincount(
                wvnfn__cozif, mjz__ygxed, min_count)
            return ucpo__hbxpp
    else:

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            wvnfn__cozif = cxm__iebq
            rkbc__seiaw = len(arr)
            for rvst__pjed in numba.parfors.parfor.internal_prange(rkbc__seiaw
                ):
                dimlt__yky = cxm__iebq
                if not bodo.libs.array_kernels.isna(arr, rvst__pjed):
                    dimlt__yky = arr[rvst__pjed]
                wvnfn__cozif += dimlt__yky
            return wvnfn__cozif
    return impl


def array_op_prod(arr, skipna, min_count):
    pass


@overload(array_op_prod)
def overload_array_op_prod(arr, skipna, min_count):
    mqb__qls = arr.dtype(1)
    if arr.dtype == types.bool_:
        mqb__qls = 1
    if isinstance(arr.dtype, types.Float):

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            wvnfn__cozif = mqb__qls
            mjz__ygxed = 0
            for rvst__pjed in numba.parfors.parfor.internal_prange(len(arr)):
                dimlt__yky = mqb__qls
                sbt__nwaf = 0
                if not bodo.libs.array_kernels.isna(arr, rvst__pjed
                    ) or not skipna:
                    dimlt__yky = arr[rvst__pjed]
                    sbt__nwaf = 1
                mjz__ygxed += sbt__nwaf
                wvnfn__cozif *= dimlt__yky
            ucpo__hbxpp = bodo.hiframes.series_kernels._var_handle_mincount(
                wvnfn__cozif, mjz__ygxed, min_count)
            return ucpo__hbxpp
    else:

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            wvnfn__cozif = mqb__qls
            for rvst__pjed in numba.parfors.parfor.internal_prange(len(arr)):
                dimlt__yky = mqb__qls
                if not bodo.libs.array_kernels.isna(arr, rvst__pjed):
                    dimlt__yky = arr[rvst__pjed]
                wvnfn__cozif *= dimlt__yky
            return wvnfn__cozif
    return impl


def array_op_idxmax(arr, index):
    pass


@overload(array_op_idxmax, inline='always')
def overload_array_op_idxmax(arr, index):

    def impl(arr, index):
        rvst__pjed = bodo.libs.array_kernels._nan_argmax(arr)
        return index[rvst__pjed]
    return impl


def array_op_idxmin(arr, index):
    pass


@overload(array_op_idxmin, inline='always')
def overload_array_op_idxmin(arr, index):

    def impl(arr, index):
        rvst__pjed = bodo.libs.array_kernels._nan_argmin(arr)
        return index[rvst__pjed]
    return impl


def _convert_isin_values(values, use_hash_impl):
    pass


@overload(_convert_isin_values, no_unliteral=True)
def overload_convert_isin_values(values, use_hash_impl):
    if is_overload_true(use_hash_impl):

        def impl(values, use_hash_impl):
            ubf__hsri = {}
            for ncwef__josr in values:
                ubf__hsri[bodo.utils.conversion.box_if_dt64(ncwef__josr)] = 0
            return ubf__hsri
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
        rkbc__seiaw = len(arr)
        vcw__pls = np.empty(rkbc__seiaw, np.bool_)
        for rvst__pjed in numba.parfors.parfor.internal_prange(rkbc__seiaw):
            vcw__pls[rvst__pjed] = bodo.utils.conversion.box_if_dt64(arr[
                rvst__pjed]) in values
        return vcw__pls
    return impl


@generated_jit(nopython=True)
def array_unique_vector_map(in_arr_tup):
    utdbt__ajcj = len(in_arr_tup) != 1
    itflx__zapch = list(in_arr_tup.types)
    tcp__mpqaz = 'def impl(in_arr_tup):\n'
    tcp__mpqaz += '  n = len(in_arr_tup[0])\n'
    if utdbt__ajcj:
        ttkk__onpjc = ', '.join([f'in_arr_tup[{rvst__pjed}][unused]' for
            rvst__pjed in range(len(in_arr_tup))])
        vbu__hfwpf = ', '.join(['False' for gwi__byuvi in range(len(
            in_arr_tup))])
        tcp__mpqaz += f"""  arr_map = {{bodo.libs.nullable_tuple_ext.build_nullable_tuple(({ttkk__onpjc},), ({vbu__hfwpf},)): 0 for unused in range(0)}}
"""
        tcp__mpqaz += '  map_vector = np.empty(n, np.int64)\n'
        for rvst__pjed, hpuug__gadrv in enumerate(itflx__zapch):
            tcp__mpqaz += f'  in_lst_{rvst__pjed} = []\n'
            if is_str_arr_type(hpuug__gadrv):
                tcp__mpqaz += f'  total_len_{rvst__pjed} = 0\n'
            tcp__mpqaz += f'  null_in_lst_{rvst__pjed} = []\n'
        tcp__mpqaz += '  for i in range(n):\n'
        dqogt__qeb = ', '.join([f'in_arr_tup[{rvst__pjed}][i]' for
            rvst__pjed in range(len(itflx__zapch))])
        tprc__byqto = ', '.join([
            f'bodo.libs.array_kernels.isna(in_arr_tup[{rvst__pjed}], i)' for
            rvst__pjed in range(len(itflx__zapch))])
        tcp__mpqaz += f"""    data_val = bodo.libs.nullable_tuple_ext.build_nullable_tuple(({dqogt__qeb},), ({tprc__byqto},))
"""
        tcp__mpqaz += '    if data_val not in arr_map:\n'
        tcp__mpqaz += '      set_val = len(arr_map)\n'
        tcp__mpqaz += '      values_tup = data_val._data\n'
        tcp__mpqaz += '      nulls_tup = data_val._null_values\n'
        for rvst__pjed, hpuug__gadrv in enumerate(itflx__zapch):
            tcp__mpqaz += (
                f'      in_lst_{rvst__pjed}.append(values_tup[{rvst__pjed}])\n'
                )
            tcp__mpqaz += (
                f'      null_in_lst_{rvst__pjed}.append(nulls_tup[{rvst__pjed}])\n'
                )
            if is_str_arr_type(hpuug__gadrv):
                tcp__mpqaz += f"""      total_len_{rvst__pjed}  += nulls_tup[{rvst__pjed}] * len(values_tup[{rvst__pjed}])
"""
        tcp__mpqaz += '      arr_map[data_val] = len(arr_map)\n'
        tcp__mpqaz += '    else:\n'
        tcp__mpqaz += '      set_val = arr_map[data_val]\n'
        tcp__mpqaz += '    map_vector[i] = set_val\n'
        tcp__mpqaz += '  n_rows = len(arr_map)\n'
        for rvst__pjed, hpuug__gadrv in enumerate(itflx__zapch):
            if is_str_arr_type(hpuug__gadrv):
                tcp__mpqaz += f"""  out_arr_{rvst__pjed} = bodo.libs.str_arr_ext.pre_alloc_string_array(n_rows, total_len_{rvst__pjed})
"""
            else:
                tcp__mpqaz += f"""  out_arr_{rvst__pjed} = bodo.utils.utils.alloc_type(n_rows, in_arr_tup[{rvst__pjed}], (-1,))
"""
        tcp__mpqaz += '  for j in range(len(arr_map)):\n'
        for rvst__pjed in range(len(itflx__zapch)):
            tcp__mpqaz += f'    if null_in_lst_{rvst__pjed}[j]:\n'
            tcp__mpqaz += (
                f'      bodo.libs.array_kernels.setna(out_arr_{rvst__pjed}, j)\n'
                )
            tcp__mpqaz += '    else:\n'
            tcp__mpqaz += (
                f'      out_arr_{rvst__pjed}[j] = in_lst_{rvst__pjed}[j]\n')
        szx__xlv = ', '.join([f'out_arr_{rvst__pjed}' for rvst__pjed in
            range(len(itflx__zapch))])
        tcp__mpqaz += f'  return ({szx__xlv},), map_vector\n'
    else:
        tcp__mpqaz += '  in_arr = in_arr_tup[0]\n'
        tcp__mpqaz += (
            f'  arr_map = {{in_arr[unused]: 0 for unused in range(0)}}\n')
        tcp__mpqaz += '  map_vector = np.empty(n, np.int64)\n'
        tcp__mpqaz += '  is_na = 0\n'
        tcp__mpqaz += '  in_lst = []\n'
        if is_str_arr_type(itflx__zapch[0]):
            tcp__mpqaz += '  total_len = 0\n'
        tcp__mpqaz += '  for i in range(n):\n'
        tcp__mpqaz += '    if bodo.libs.array_kernels.isna(in_arr, i):\n'
        tcp__mpqaz += '      is_na = 1\n'
        tcp__mpqaz += (
            '      # Always put NA in the last location. We can safely use\n')
        tcp__mpqaz += (
            '      # -1 because in_arr[-1] == in_arr[len(in_arr) - 1]\n')
        tcp__mpqaz += '      set_val = -1\n'
        tcp__mpqaz += '    else:\n'
        tcp__mpqaz += '      data_val = in_arr[i]\n'
        tcp__mpqaz += '      if data_val not in arr_map:\n'
        tcp__mpqaz += '        set_val = len(arr_map)\n'
        tcp__mpqaz += '        in_lst.append(data_val)\n'
        if is_str_arr_type(itflx__zapch[0]):
            tcp__mpqaz += '        total_len += len(data_val)\n'
        tcp__mpqaz += '        arr_map[data_val] = len(arr_map)\n'
        tcp__mpqaz += '      else:\n'
        tcp__mpqaz += '        set_val = arr_map[data_val]\n'
        tcp__mpqaz += '    map_vector[i] = set_val\n'
        tcp__mpqaz += '  n_rows = len(arr_map) + is_na\n'
        if is_str_arr_type(itflx__zapch[0]):
            tcp__mpqaz += """  out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(n_rows, total_len)
"""
        else:
            tcp__mpqaz += (
                '  out_arr = bodo.utils.utils.alloc_type(n_rows, in_arr, (-1,))\n'
                )
        tcp__mpqaz += '  for j in range(len(arr_map)):\n'
        tcp__mpqaz += '    out_arr[j] = in_lst[j]\n'
        tcp__mpqaz += '  if is_na:\n'
        tcp__mpqaz += (
            '    bodo.libs.array_kernels.setna(out_arr, n_rows - 1)\n')
        tcp__mpqaz += f'  return (out_arr,), map_vector\n'
    ubm__mgox = {}
    exec(tcp__mpqaz, {'bodo': bodo, 'np': np}, ubm__mgox)
    impl = ubm__mgox['impl']
    return impl
