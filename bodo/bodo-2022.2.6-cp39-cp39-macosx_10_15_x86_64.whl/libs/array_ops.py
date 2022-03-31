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
    gohrr__jbkch = np.empty(1, types.float64)
    bodo.libs.array_kernels.median_series_computation(gohrr__jbkch.ctypes,
        arr, parallel, skipna)
    return gohrr__jbkch[0]


def array_op_isna(arr):
    pass


@overload(array_op_isna)
def overload_array_op_isna(arr):

    def impl(arr):
        numba.parfors.parfor.init_prange()
        ondqa__lfha = len(arr)
        ebo__tirp = np.empty(ondqa__lfha, np.bool_)
        for ddm__dhqix in numba.parfors.parfor.internal_prange(ondqa__lfha):
            ebo__tirp[ddm__dhqix] = bodo.libs.array_kernels.isna(arr,
                ddm__dhqix)
        return ebo__tirp
    return impl


def array_op_count(arr):
    pass


@overload(array_op_count)
def overload_array_op_count(arr):

    def impl(arr):
        numba.parfors.parfor.init_prange()
        wol__rcm = 0
        for ddm__dhqix in numba.parfors.parfor.internal_prange(len(arr)):
            yvd__fybn = 0
            if not bodo.libs.array_kernels.isna(arr, ddm__dhqix):
                yvd__fybn = 1
            wol__rcm += yvd__fybn
        gohrr__jbkch = wol__rcm
        return gohrr__jbkch
    return impl


def array_op_describe(arr):
    pass


def array_op_describe_impl(arr):
    dsndk__spj = array_op_count(arr)
    hmicj__zevj = array_op_min(arr)
    ssbi__jer = array_op_max(arr)
    xyio__tcy = array_op_mean(arr)
    aacsf__pkz = array_op_std(arr)
    bhf__ufio = array_op_quantile(arr, 0.25)
    oohh__ybmt = array_op_quantile(arr, 0.5)
    lxzf__xrg = array_op_quantile(arr, 0.75)
    return (dsndk__spj, xyio__tcy, aacsf__pkz, hmicj__zevj, bhf__ufio,
        oohh__ybmt, lxzf__xrg, ssbi__jer)


def array_op_describe_dt_impl(arr):
    dsndk__spj = array_op_count(arr)
    hmicj__zevj = array_op_min(arr)
    ssbi__jer = array_op_max(arr)
    xyio__tcy = array_op_mean(arr)
    bhf__ufio = array_op_quantile(arr, 0.25)
    oohh__ybmt = array_op_quantile(arr, 0.5)
    lxzf__xrg = array_op_quantile(arr, 0.75)
    return (dsndk__spj, xyio__tcy, hmicj__zevj, bhf__ufio, oohh__ybmt,
        lxzf__xrg, ssbi__jer)


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
            hin__xzic = numba.cpython.builtins.get_type_max_value(np.int64)
            wol__rcm = 0
            for ddm__dhqix in numba.parfors.parfor.internal_prange(len(arr)):
                msgu__wki = hin__xzic
                yvd__fybn = 0
                if not bodo.libs.array_kernels.isna(arr, ddm__dhqix):
                    msgu__wki = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(arr[ddm__dhqix]))
                    yvd__fybn = 1
                hin__xzic = min(hin__xzic, msgu__wki)
                wol__rcm += yvd__fybn
            return bodo.hiframes.pd_index_ext._tdi_val_finalize(hin__xzic,
                wol__rcm)
        return impl_td64
    if arr.dtype == bodo.datetime64ns:

        def impl_dt64(arr):
            numba.parfors.parfor.init_prange()
            hin__xzic = numba.cpython.builtins.get_type_max_value(np.int64)
            wol__rcm = 0
            for ddm__dhqix in numba.parfors.parfor.internal_prange(len(arr)):
                msgu__wki = hin__xzic
                yvd__fybn = 0
                if not bodo.libs.array_kernels.isna(arr, ddm__dhqix):
                    msgu__wki = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        arr[ddm__dhqix])
                    yvd__fybn = 1
                hin__xzic = min(hin__xzic, msgu__wki)
                wol__rcm += yvd__fybn
            return bodo.hiframes.pd_index_ext._dti_val_finalize(hin__xzic,
                wol__rcm)
        return impl_dt64
    if isinstance(arr, CategoricalArrayType):

        def impl_cat(arr):
            fxoka__vty = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            hin__xzic = numba.cpython.builtins.get_type_max_value(np.int64)
            wol__rcm = 0
            for ddm__dhqix in numba.parfors.parfor.internal_prange(len(
                fxoka__vty)):
                cgu__upo = fxoka__vty[ddm__dhqix]
                if cgu__upo == -1:
                    continue
                hin__xzic = min(hin__xzic, cgu__upo)
                wol__rcm += 1
            gohrr__jbkch = bodo.hiframes.series_kernels._box_cat_val(hin__xzic,
                arr.dtype, wol__rcm)
            return gohrr__jbkch
        return impl_cat
    if arr == datetime_date_array_type:

        def impl_date(arr):
            numba.parfors.parfor.init_prange()
            hin__xzic = bodo.hiframes.series_kernels._get_date_max_value()
            wol__rcm = 0
            for ddm__dhqix in numba.parfors.parfor.internal_prange(len(arr)):
                msgu__wki = hin__xzic
                yvd__fybn = 0
                if not bodo.libs.array_kernels.isna(arr, ddm__dhqix):
                    msgu__wki = arr[ddm__dhqix]
                    yvd__fybn = 1
                hin__xzic = min(hin__xzic, msgu__wki)
                wol__rcm += yvd__fybn
            gohrr__jbkch = bodo.hiframes.series_kernels._sum_handle_nan(
                hin__xzic, wol__rcm)
            return gohrr__jbkch
        return impl_date

    def impl(arr):
        numba.parfors.parfor.init_prange()
        hin__xzic = bodo.hiframes.series_kernels._get_type_max_value(arr.dtype)
        wol__rcm = 0
        for ddm__dhqix in numba.parfors.parfor.internal_prange(len(arr)):
            msgu__wki = hin__xzic
            yvd__fybn = 0
            if not bodo.libs.array_kernels.isna(arr, ddm__dhqix):
                msgu__wki = arr[ddm__dhqix]
                yvd__fybn = 1
            hin__xzic = min(hin__xzic, msgu__wki)
            wol__rcm += yvd__fybn
        gohrr__jbkch = bodo.hiframes.series_kernels._sum_handle_nan(hin__xzic,
            wol__rcm)
        return gohrr__jbkch
    return impl


def array_op_max(arr):
    pass


@overload(array_op_max)
def overload_array_op_max(arr):
    if arr.dtype == bodo.timedelta64ns:

        def impl_td64(arr):
            numba.parfors.parfor.init_prange()
            hin__xzic = numba.cpython.builtins.get_type_min_value(np.int64)
            wol__rcm = 0
            for ddm__dhqix in numba.parfors.parfor.internal_prange(len(arr)):
                msgu__wki = hin__xzic
                yvd__fybn = 0
                if not bodo.libs.array_kernels.isna(arr, ddm__dhqix):
                    msgu__wki = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(arr[ddm__dhqix]))
                    yvd__fybn = 1
                hin__xzic = max(hin__xzic, msgu__wki)
                wol__rcm += yvd__fybn
            return bodo.hiframes.pd_index_ext._tdi_val_finalize(hin__xzic,
                wol__rcm)
        return impl_td64
    if arr.dtype == bodo.datetime64ns:

        def impl_dt64(arr):
            numba.parfors.parfor.init_prange()
            hin__xzic = numba.cpython.builtins.get_type_min_value(np.int64)
            wol__rcm = 0
            for ddm__dhqix in numba.parfors.parfor.internal_prange(len(arr)):
                msgu__wki = hin__xzic
                yvd__fybn = 0
                if not bodo.libs.array_kernels.isna(arr, ddm__dhqix):
                    msgu__wki = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        arr[ddm__dhqix])
                    yvd__fybn = 1
                hin__xzic = max(hin__xzic, msgu__wki)
                wol__rcm += yvd__fybn
            return bodo.hiframes.pd_index_ext._dti_val_finalize(hin__xzic,
                wol__rcm)
        return impl_dt64
    if isinstance(arr, CategoricalArrayType):

        def impl_cat(arr):
            fxoka__vty = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            hin__xzic = -1
            for ddm__dhqix in numba.parfors.parfor.internal_prange(len(
                fxoka__vty)):
                hin__xzic = max(hin__xzic, fxoka__vty[ddm__dhqix])
            gohrr__jbkch = bodo.hiframes.series_kernels._box_cat_val(hin__xzic,
                arr.dtype, 1)
            return gohrr__jbkch
        return impl_cat
    if arr == datetime_date_array_type:

        def impl_date(arr):
            numba.parfors.parfor.init_prange()
            hin__xzic = bodo.hiframes.series_kernels._get_date_min_value()
            wol__rcm = 0
            for ddm__dhqix in numba.parfors.parfor.internal_prange(len(arr)):
                msgu__wki = hin__xzic
                yvd__fybn = 0
                if not bodo.libs.array_kernels.isna(arr, ddm__dhqix):
                    msgu__wki = arr[ddm__dhqix]
                    yvd__fybn = 1
                hin__xzic = max(hin__xzic, msgu__wki)
                wol__rcm += yvd__fybn
            gohrr__jbkch = bodo.hiframes.series_kernels._sum_handle_nan(
                hin__xzic, wol__rcm)
            return gohrr__jbkch
        return impl_date

    def impl(arr):
        numba.parfors.parfor.init_prange()
        hin__xzic = bodo.hiframes.series_kernels._get_type_min_value(arr.dtype)
        wol__rcm = 0
        for ddm__dhqix in numba.parfors.parfor.internal_prange(len(arr)):
            msgu__wki = hin__xzic
            yvd__fybn = 0
            if not bodo.libs.array_kernels.isna(arr, ddm__dhqix):
                msgu__wki = arr[ddm__dhqix]
                yvd__fybn = 1
            hin__xzic = max(hin__xzic, msgu__wki)
            wol__rcm += yvd__fybn
        gohrr__jbkch = bodo.hiframes.series_kernels._sum_handle_nan(hin__xzic,
            wol__rcm)
        return gohrr__jbkch
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
    jau__kyzqh = types.float64
    qiq__jllq = types.float64
    if isinstance(arr, types.Array) and arr.dtype == types.float32:
        jau__kyzqh = types.float32
        qiq__jllq = types.float32
    ncyv__anhb = jau__kyzqh(0)
    zdysb__uetj = qiq__jllq(0)
    pcy__rmgec = qiq__jllq(1)

    def impl(arr):
        numba.parfors.parfor.init_prange()
        hin__xzic = ncyv__anhb
        wol__rcm = zdysb__uetj
        for ddm__dhqix in numba.parfors.parfor.internal_prange(len(arr)):
            msgu__wki = ncyv__anhb
            yvd__fybn = zdysb__uetj
            if not bodo.libs.array_kernels.isna(arr, ddm__dhqix):
                msgu__wki = arr[ddm__dhqix]
                yvd__fybn = pcy__rmgec
            hin__xzic += msgu__wki
            wol__rcm += yvd__fybn
        gohrr__jbkch = bodo.hiframes.series_kernels._mean_handle_nan(hin__xzic,
            wol__rcm)
        return gohrr__jbkch
    return impl


def array_op_var(arr, skipna, ddof):
    pass


@overload(array_op_var)
def overload_array_op_var(arr, skipna, ddof):

    def impl(arr, skipna, ddof):
        numba.parfors.parfor.init_prange()
        twt__nmz = 0.0
        vvo__jhuqk = 0.0
        wol__rcm = 0
        for ddm__dhqix in numba.parfors.parfor.internal_prange(len(arr)):
            msgu__wki = 0.0
            yvd__fybn = 0
            if not bodo.libs.array_kernels.isna(arr, ddm__dhqix) or not skipna:
                msgu__wki = arr[ddm__dhqix]
                yvd__fybn = 1
            twt__nmz += msgu__wki
            vvo__jhuqk += msgu__wki * msgu__wki
            wol__rcm += yvd__fybn
        gohrr__jbkch = (bodo.hiframes.series_kernels.
            _compute_var_nan_count_ddof(twt__nmz, vvo__jhuqk, wol__rcm, ddof))
        return gohrr__jbkch
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
                ebo__tirp = np.empty(len(q), np.int64)
                for ddm__dhqix in range(len(q)):
                    hdav__ipvmc = np.float64(q[ddm__dhqix])
                    ebo__tirp[ddm__dhqix] = bodo.libs.array_kernels.quantile(
                        arr.view(np.int64), hdav__ipvmc)
                return ebo__tirp.view(np.dtype('datetime64[ns]'))
            return _impl_list_dt

        def impl_list(arr, q):
            ebo__tirp = np.empty(len(q), np.float64)
            for ddm__dhqix in range(len(q)):
                hdav__ipvmc = np.float64(q[ddm__dhqix])
                ebo__tirp[ddm__dhqix] = bodo.libs.array_kernels.quantile(arr,
                    hdav__ipvmc)
            return ebo__tirp
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
        jze__fms = types.intp
    elif arr.dtype == types.bool_:
        jze__fms = np.int64
    else:
        jze__fms = arr.dtype
    wskmy__dsls = jze__fms(0)
    if isinstance(arr.dtype, types.Float) and (not is_overload_true(skipna) or
        not is_overload_zero(min_count)):

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            hin__xzic = wskmy__dsls
            ondqa__lfha = len(arr)
            wol__rcm = 0
            for ddm__dhqix in numba.parfors.parfor.internal_prange(ondqa__lfha
                ):
                msgu__wki = wskmy__dsls
                yvd__fybn = 0
                if not bodo.libs.array_kernels.isna(arr, ddm__dhqix
                    ) or not skipna:
                    msgu__wki = arr[ddm__dhqix]
                    yvd__fybn = 1
                hin__xzic += msgu__wki
                wol__rcm += yvd__fybn
            gohrr__jbkch = bodo.hiframes.series_kernels._var_handle_mincount(
                hin__xzic, wol__rcm, min_count)
            return gohrr__jbkch
    else:

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            hin__xzic = wskmy__dsls
            ondqa__lfha = len(arr)
            for ddm__dhqix in numba.parfors.parfor.internal_prange(ondqa__lfha
                ):
                msgu__wki = wskmy__dsls
                if not bodo.libs.array_kernels.isna(arr, ddm__dhqix):
                    msgu__wki = arr[ddm__dhqix]
                hin__xzic += msgu__wki
            return hin__xzic
    return impl


def array_op_prod(arr, skipna, min_count):
    pass


@overload(array_op_prod)
def overload_array_op_prod(arr, skipna, min_count):
    gjspm__wmxw = arr.dtype(1)
    if arr.dtype == types.bool_:
        gjspm__wmxw = 1
    if isinstance(arr.dtype, types.Float):

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            hin__xzic = gjspm__wmxw
            wol__rcm = 0
            for ddm__dhqix in numba.parfors.parfor.internal_prange(len(arr)):
                msgu__wki = gjspm__wmxw
                yvd__fybn = 0
                if not bodo.libs.array_kernels.isna(arr, ddm__dhqix
                    ) or not skipna:
                    msgu__wki = arr[ddm__dhqix]
                    yvd__fybn = 1
                wol__rcm += yvd__fybn
                hin__xzic *= msgu__wki
            gohrr__jbkch = bodo.hiframes.series_kernels._var_handle_mincount(
                hin__xzic, wol__rcm, min_count)
            return gohrr__jbkch
    else:

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            hin__xzic = gjspm__wmxw
            for ddm__dhqix in numba.parfors.parfor.internal_prange(len(arr)):
                msgu__wki = gjspm__wmxw
                if not bodo.libs.array_kernels.isna(arr, ddm__dhqix):
                    msgu__wki = arr[ddm__dhqix]
                hin__xzic *= msgu__wki
            return hin__xzic
    return impl


def array_op_idxmax(arr, index):
    pass


@overload(array_op_idxmax, inline='always')
def overload_array_op_idxmax(arr, index):

    def impl(arr, index):
        ddm__dhqix = bodo.libs.array_kernels._nan_argmax(arr)
        return index[ddm__dhqix]
    return impl


def array_op_idxmin(arr, index):
    pass


@overload(array_op_idxmin, inline='always')
def overload_array_op_idxmin(arr, index):

    def impl(arr, index):
        ddm__dhqix = bodo.libs.array_kernels._nan_argmin(arr)
        return index[ddm__dhqix]
    return impl


def _convert_isin_values(values, use_hash_impl):
    pass


@overload(_convert_isin_values, no_unliteral=True)
def overload_convert_isin_values(values, use_hash_impl):
    if is_overload_true(use_hash_impl):

        def impl(values, use_hash_impl):
            perpi__bmrx = {}
            for dzlwk__sjm in values:
                perpi__bmrx[bodo.utils.conversion.box_if_dt64(dzlwk__sjm)] = 0
            return perpi__bmrx
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
        ondqa__lfha = len(arr)
        ebo__tirp = np.empty(ondqa__lfha, np.bool_)
        for ddm__dhqix in numba.parfors.parfor.internal_prange(ondqa__lfha):
            ebo__tirp[ddm__dhqix] = bodo.utils.conversion.box_if_dt64(arr[
                ddm__dhqix]) in values
        return ebo__tirp
    return impl


@generated_jit(nopython=True)
def array_unique_vector_map(in_arr_tup):
    fcyh__iwl = len(in_arr_tup) != 1
    nvri__dopf = list(in_arr_tup.types)
    dhhln__lhdr = 'def impl(in_arr_tup):\n'
    dhhln__lhdr += '  n = len(in_arr_tup[0])\n'
    if fcyh__iwl:
        jjey__usfxj = ', '.join([f'in_arr_tup[{ddm__dhqix}][unused]' for
            ddm__dhqix in range(len(in_arr_tup))])
        yyjwj__nlj = ', '.join(['False' for cbog__ycw in range(len(
            in_arr_tup))])
        dhhln__lhdr += f"""  arr_map = {{bodo.libs.nullable_tuple_ext.build_nullable_tuple(({jjey__usfxj},), ({yyjwj__nlj},)): 0 for unused in range(0)}}
"""
        dhhln__lhdr += '  map_vector = np.empty(n, np.int64)\n'
        for ddm__dhqix, qfdo__alxe in enumerate(nvri__dopf):
            dhhln__lhdr += f'  in_lst_{ddm__dhqix} = []\n'
            if is_str_arr_type(qfdo__alxe):
                dhhln__lhdr += f'  total_len_{ddm__dhqix} = 0\n'
            dhhln__lhdr += f'  null_in_lst_{ddm__dhqix} = []\n'
        dhhln__lhdr += '  for i in range(n):\n'
        jvfr__idhn = ', '.join([f'in_arr_tup[{ddm__dhqix}][i]' for
            ddm__dhqix in range(len(nvri__dopf))])
        dpduk__dpsu = ', '.join([
            f'bodo.libs.array_kernels.isna(in_arr_tup[{ddm__dhqix}], i)' for
            ddm__dhqix in range(len(nvri__dopf))])
        dhhln__lhdr += f"""    data_val = bodo.libs.nullable_tuple_ext.build_nullable_tuple(({jvfr__idhn},), ({dpduk__dpsu},))
"""
        dhhln__lhdr += '    if data_val not in arr_map:\n'
        dhhln__lhdr += '      set_val = len(arr_map)\n'
        dhhln__lhdr += '      values_tup = data_val._data\n'
        dhhln__lhdr += '      nulls_tup = data_val._null_values\n'
        for ddm__dhqix, qfdo__alxe in enumerate(nvri__dopf):
            dhhln__lhdr += (
                f'      in_lst_{ddm__dhqix}.append(values_tup[{ddm__dhqix}])\n'
                )
            dhhln__lhdr += (
                f'      null_in_lst_{ddm__dhqix}.append(nulls_tup[{ddm__dhqix}])\n'
                )
            if is_str_arr_type(qfdo__alxe):
                dhhln__lhdr += f"""      total_len_{ddm__dhqix}  += nulls_tup[{ddm__dhqix}] * len(values_tup[{ddm__dhqix}])
"""
        dhhln__lhdr += '      arr_map[data_val] = len(arr_map)\n'
        dhhln__lhdr += '    else:\n'
        dhhln__lhdr += '      set_val = arr_map[data_val]\n'
        dhhln__lhdr += '    map_vector[i] = set_val\n'
        dhhln__lhdr += '  n_rows = len(arr_map)\n'
        for ddm__dhqix, qfdo__alxe in enumerate(nvri__dopf):
            if is_str_arr_type(qfdo__alxe):
                dhhln__lhdr += f"""  out_arr_{ddm__dhqix} = bodo.libs.str_arr_ext.pre_alloc_string_array(n_rows, total_len_{ddm__dhqix})
"""
            else:
                dhhln__lhdr += f"""  out_arr_{ddm__dhqix} = bodo.utils.utils.alloc_type(n_rows, in_arr_tup[{ddm__dhqix}], (-1,))
"""
        dhhln__lhdr += '  for j in range(len(arr_map)):\n'
        for ddm__dhqix in range(len(nvri__dopf)):
            dhhln__lhdr += f'    if null_in_lst_{ddm__dhqix}[j]:\n'
            dhhln__lhdr += (
                f'      bodo.libs.array_kernels.setna(out_arr_{ddm__dhqix}, j)\n'
                )
            dhhln__lhdr += '    else:\n'
            dhhln__lhdr += (
                f'      out_arr_{ddm__dhqix}[j] = in_lst_{ddm__dhqix}[j]\n')
        xhi__did = ', '.join([f'out_arr_{ddm__dhqix}' for ddm__dhqix in
            range(len(nvri__dopf))])
        dhhln__lhdr += f'  return ({xhi__did},), map_vector\n'
    else:
        dhhln__lhdr += '  in_arr = in_arr_tup[0]\n'
        dhhln__lhdr += (
            f'  arr_map = {{in_arr[unused]: 0 for unused in range(0)}}\n')
        dhhln__lhdr += '  map_vector = np.empty(n, np.int64)\n'
        dhhln__lhdr += '  is_na = 0\n'
        dhhln__lhdr += '  in_lst = []\n'
        if is_str_arr_type(nvri__dopf[0]):
            dhhln__lhdr += '  total_len = 0\n'
        dhhln__lhdr += '  for i in range(n):\n'
        dhhln__lhdr += '    if bodo.libs.array_kernels.isna(in_arr, i):\n'
        dhhln__lhdr += '      is_na = 1\n'
        dhhln__lhdr += (
            '      # Always put NA in the last location. We can safely use\n')
        dhhln__lhdr += (
            '      # -1 because in_arr[-1] == in_arr[len(in_arr) - 1]\n')
        dhhln__lhdr += '      set_val = -1\n'
        dhhln__lhdr += '    else:\n'
        dhhln__lhdr += '      data_val = in_arr[i]\n'
        dhhln__lhdr += '      if data_val not in arr_map:\n'
        dhhln__lhdr += '        set_val = len(arr_map)\n'
        dhhln__lhdr += '        in_lst.append(data_val)\n'
        if is_str_arr_type(nvri__dopf[0]):
            dhhln__lhdr += '        total_len += len(data_val)\n'
        dhhln__lhdr += '        arr_map[data_val] = len(arr_map)\n'
        dhhln__lhdr += '      else:\n'
        dhhln__lhdr += '        set_val = arr_map[data_val]\n'
        dhhln__lhdr += '    map_vector[i] = set_val\n'
        dhhln__lhdr += '  n_rows = len(arr_map) + is_na\n'
        if is_str_arr_type(nvri__dopf[0]):
            dhhln__lhdr += """  out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(n_rows, total_len)
"""
        else:
            dhhln__lhdr += (
                '  out_arr = bodo.utils.utils.alloc_type(n_rows, in_arr, (-1,))\n'
                )
        dhhln__lhdr += '  for j in range(len(arr_map)):\n'
        dhhln__lhdr += '    out_arr[j] = in_lst[j]\n'
        dhhln__lhdr += '  if is_na:\n'
        dhhln__lhdr += (
            '    bodo.libs.array_kernels.setna(out_arr, n_rows - 1)\n')
        dhhln__lhdr += f'  return (out_arr,), map_vector\n'
    tqopo__kejj = {}
    exec(dhhln__lhdr, {'bodo': bodo, 'np': np}, tqopo__kejj)
    impl = tqopo__kejj['impl']
    return impl
