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
    wgcbg__aav = np.empty(1, types.float64)
    bodo.libs.array_kernels.median_series_computation(wgcbg__aav.ctypes,
        arr, parallel, skipna)
    return wgcbg__aav[0]


def array_op_isna(arr):
    pass


@overload(array_op_isna)
def overload_array_op_isna(arr):

    def impl(arr):
        numba.parfors.parfor.init_prange()
        vtstq__rlhh = len(arr)
        qepjg__tew = np.empty(vtstq__rlhh, np.bool_)
        for gpwe__utg in numba.parfors.parfor.internal_prange(vtstq__rlhh):
            qepjg__tew[gpwe__utg] = bodo.libs.array_kernels.isna(arr, gpwe__utg
                )
        return qepjg__tew
    return impl


def array_op_count(arr):
    pass


@overload(array_op_count)
def overload_array_op_count(arr):

    def impl(arr):
        numba.parfors.parfor.init_prange()
        iyrp__dudzu = 0
        for gpwe__utg in numba.parfors.parfor.internal_prange(len(arr)):
            ahzva__gwj = 0
            if not bodo.libs.array_kernels.isna(arr, gpwe__utg):
                ahzva__gwj = 1
            iyrp__dudzu += ahzva__gwj
        wgcbg__aav = iyrp__dudzu
        return wgcbg__aav
    return impl


def array_op_describe(arr):
    pass


def array_op_describe_impl(arr):
    jgf__fshit = array_op_count(arr)
    hwp__urqs = array_op_min(arr)
    xivg__jync = array_op_max(arr)
    xbgye__qoz = array_op_mean(arr)
    ccsw__vrp = array_op_std(arr)
    zcbu__woqk = array_op_quantile(arr, 0.25)
    wjp__pnr = array_op_quantile(arr, 0.5)
    eti__lhc = array_op_quantile(arr, 0.75)
    return (jgf__fshit, xbgye__qoz, ccsw__vrp, hwp__urqs, zcbu__woqk,
        wjp__pnr, eti__lhc, xivg__jync)


def array_op_describe_dt_impl(arr):
    jgf__fshit = array_op_count(arr)
    hwp__urqs = array_op_min(arr)
    xivg__jync = array_op_max(arr)
    xbgye__qoz = array_op_mean(arr)
    zcbu__woqk = array_op_quantile(arr, 0.25)
    wjp__pnr = array_op_quantile(arr, 0.5)
    eti__lhc = array_op_quantile(arr, 0.75)
    return (jgf__fshit, xbgye__qoz, hwp__urqs, zcbu__woqk, wjp__pnr,
        eti__lhc, xivg__jync)


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
            ocunm__rmkv = numba.cpython.builtins.get_type_max_value(np.int64)
            iyrp__dudzu = 0
            for gpwe__utg in numba.parfors.parfor.internal_prange(len(arr)):
                birf__cuipl = ocunm__rmkv
                ahzva__gwj = 0
                if not bodo.libs.array_kernels.isna(arr, gpwe__utg):
                    birf__cuipl = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(arr[gpwe__utg]))
                    ahzva__gwj = 1
                ocunm__rmkv = min(ocunm__rmkv, birf__cuipl)
                iyrp__dudzu += ahzva__gwj
            return bodo.hiframes.pd_index_ext._tdi_val_finalize(ocunm__rmkv,
                iyrp__dudzu)
        return impl_td64
    if arr.dtype == bodo.datetime64ns:

        def impl_dt64(arr):
            numba.parfors.parfor.init_prange()
            ocunm__rmkv = numba.cpython.builtins.get_type_max_value(np.int64)
            iyrp__dudzu = 0
            for gpwe__utg in numba.parfors.parfor.internal_prange(len(arr)):
                birf__cuipl = ocunm__rmkv
                ahzva__gwj = 0
                if not bodo.libs.array_kernels.isna(arr, gpwe__utg):
                    birf__cuipl = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(arr[gpwe__utg]))
                    ahzva__gwj = 1
                ocunm__rmkv = min(ocunm__rmkv, birf__cuipl)
                iyrp__dudzu += ahzva__gwj
            return bodo.hiframes.pd_index_ext._dti_val_finalize(ocunm__rmkv,
                iyrp__dudzu)
        return impl_dt64
    if isinstance(arr, CategoricalArrayType):

        def impl_cat(arr):
            luhvi__cqnfm = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            ocunm__rmkv = numba.cpython.builtins.get_type_max_value(np.int64)
            iyrp__dudzu = 0
            for gpwe__utg in numba.parfors.parfor.internal_prange(len(
                luhvi__cqnfm)):
                kvv__gsdzu = luhvi__cqnfm[gpwe__utg]
                if kvv__gsdzu == -1:
                    continue
                ocunm__rmkv = min(ocunm__rmkv, kvv__gsdzu)
                iyrp__dudzu += 1
            wgcbg__aav = bodo.hiframes.series_kernels._box_cat_val(ocunm__rmkv,
                arr.dtype, iyrp__dudzu)
            return wgcbg__aav
        return impl_cat
    if arr == datetime_date_array_type:

        def impl_date(arr):
            numba.parfors.parfor.init_prange()
            ocunm__rmkv = bodo.hiframes.series_kernels._get_date_max_value()
            iyrp__dudzu = 0
            for gpwe__utg in numba.parfors.parfor.internal_prange(len(arr)):
                birf__cuipl = ocunm__rmkv
                ahzva__gwj = 0
                if not bodo.libs.array_kernels.isna(arr, gpwe__utg):
                    birf__cuipl = arr[gpwe__utg]
                    ahzva__gwj = 1
                ocunm__rmkv = min(ocunm__rmkv, birf__cuipl)
                iyrp__dudzu += ahzva__gwj
            wgcbg__aav = bodo.hiframes.series_kernels._sum_handle_nan(
                ocunm__rmkv, iyrp__dudzu)
            return wgcbg__aav
        return impl_date

    def impl(arr):
        numba.parfors.parfor.init_prange()
        ocunm__rmkv = bodo.hiframes.series_kernels._get_type_max_value(arr.
            dtype)
        iyrp__dudzu = 0
        for gpwe__utg in numba.parfors.parfor.internal_prange(len(arr)):
            birf__cuipl = ocunm__rmkv
            ahzva__gwj = 0
            if not bodo.libs.array_kernels.isna(arr, gpwe__utg):
                birf__cuipl = arr[gpwe__utg]
                ahzva__gwj = 1
            ocunm__rmkv = min(ocunm__rmkv, birf__cuipl)
            iyrp__dudzu += ahzva__gwj
        wgcbg__aav = bodo.hiframes.series_kernels._sum_handle_nan(ocunm__rmkv,
            iyrp__dudzu)
        return wgcbg__aav
    return impl


def array_op_max(arr):
    pass


@overload(array_op_max)
def overload_array_op_max(arr):
    if arr.dtype == bodo.timedelta64ns:

        def impl_td64(arr):
            numba.parfors.parfor.init_prange()
            ocunm__rmkv = numba.cpython.builtins.get_type_min_value(np.int64)
            iyrp__dudzu = 0
            for gpwe__utg in numba.parfors.parfor.internal_prange(len(arr)):
                birf__cuipl = ocunm__rmkv
                ahzva__gwj = 0
                if not bodo.libs.array_kernels.isna(arr, gpwe__utg):
                    birf__cuipl = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(arr[gpwe__utg]))
                    ahzva__gwj = 1
                ocunm__rmkv = max(ocunm__rmkv, birf__cuipl)
                iyrp__dudzu += ahzva__gwj
            return bodo.hiframes.pd_index_ext._tdi_val_finalize(ocunm__rmkv,
                iyrp__dudzu)
        return impl_td64
    if arr.dtype == bodo.datetime64ns:

        def impl_dt64(arr):
            numba.parfors.parfor.init_prange()
            ocunm__rmkv = numba.cpython.builtins.get_type_min_value(np.int64)
            iyrp__dudzu = 0
            for gpwe__utg in numba.parfors.parfor.internal_prange(len(arr)):
                birf__cuipl = ocunm__rmkv
                ahzva__gwj = 0
                if not bodo.libs.array_kernels.isna(arr, gpwe__utg):
                    birf__cuipl = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(arr[gpwe__utg]))
                    ahzva__gwj = 1
                ocunm__rmkv = max(ocunm__rmkv, birf__cuipl)
                iyrp__dudzu += ahzva__gwj
            return bodo.hiframes.pd_index_ext._dti_val_finalize(ocunm__rmkv,
                iyrp__dudzu)
        return impl_dt64
    if isinstance(arr, CategoricalArrayType):

        def impl_cat(arr):
            luhvi__cqnfm = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            ocunm__rmkv = -1
            for gpwe__utg in numba.parfors.parfor.internal_prange(len(
                luhvi__cqnfm)):
                ocunm__rmkv = max(ocunm__rmkv, luhvi__cqnfm[gpwe__utg])
            wgcbg__aav = bodo.hiframes.series_kernels._box_cat_val(ocunm__rmkv,
                arr.dtype, 1)
            return wgcbg__aav
        return impl_cat
    if arr == datetime_date_array_type:

        def impl_date(arr):
            numba.parfors.parfor.init_prange()
            ocunm__rmkv = bodo.hiframes.series_kernels._get_date_min_value()
            iyrp__dudzu = 0
            for gpwe__utg in numba.parfors.parfor.internal_prange(len(arr)):
                birf__cuipl = ocunm__rmkv
                ahzva__gwj = 0
                if not bodo.libs.array_kernels.isna(arr, gpwe__utg):
                    birf__cuipl = arr[gpwe__utg]
                    ahzva__gwj = 1
                ocunm__rmkv = max(ocunm__rmkv, birf__cuipl)
                iyrp__dudzu += ahzva__gwj
            wgcbg__aav = bodo.hiframes.series_kernels._sum_handle_nan(
                ocunm__rmkv, iyrp__dudzu)
            return wgcbg__aav
        return impl_date

    def impl(arr):
        numba.parfors.parfor.init_prange()
        ocunm__rmkv = bodo.hiframes.series_kernels._get_type_min_value(arr.
            dtype)
        iyrp__dudzu = 0
        for gpwe__utg in numba.parfors.parfor.internal_prange(len(arr)):
            birf__cuipl = ocunm__rmkv
            ahzva__gwj = 0
            if not bodo.libs.array_kernels.isna(arr, gpwe__utg):
                birf__cuipl = arr[gpwe__utg]
                ahzva__gwj = 1
            ocunm__rmkv = max(ocunm__rmkv, birf__cuipl)
            iyrp__dudzu += ahzva__gwj
        wgcbg__aav = bodo.hiframes.series_kernels._sum_handle_nan(ocunm__rmkv,
            iyrp__dudzu)
        return wgcbg__aav
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
    kmih__wnh = types.float64
    sou__bir = types.float64
    if isinstance(arr, types.Array) and arr.dtype == types.float32:
        kmih__wnh = types.float32
        sou__bir = types.float32
    gafee__heye = kmih__wnh(0)
    tqme__tph = sou__bir(0)
    elxdb__vso = sou__bir(1)

    def impl(arr):
        numba.parfors.parfor.init_prange()
        ocunm__rmkv = gafee__heye
        iyrp__dudzu = tqme__tph
        for gpwe__utg in numba.parfors.parfor.internal_prange(len(arr)):
            birf__cuipl = gafee__heye
            ahzva__gwj = tqme__tph
            if not bodo.libs.array_kernels.isna(arr, gpwe__utg):
                birf__cuipl = arr[gpwe__utg]
                ahzva__gwj = elxdb__vso
            ocunm__rmkv += birf__cuipl
            iyrp__dudzu += ahzva__gwj
        wgcbg__aav = bodo.hiframes.series_kernels._mean_handle_nan(ocunm__rmkv,
            iyrp__dudzu)
        return wgcbg__aav
    return impl


def array_op_var(arr, skipna, ddof):
    pass


@overload(array_op_var)
def overload_array_op_var(arr, skipna, ddof):

    def impl(arr, skipna, ddof):
        numba.parfors.parfor.init_prange()
        xhrsz__vlwor = 0.0
        xaa__avir = 0.0
        iyrp__dudzu = 0
        for gpwe__utg in numba.parfors.parfor.internal_prange(len(arr)):
            birf__cuipl = 0.0
            ahzva__gwj = 0
            if not bodo.libs.array_kernels.isna(arr, gpwe__utg) or not skipna:
                birf__cuipl = arr[gpwe__utg]
                ahzva__gwj = 1
            xhrsz__vlwor += birf__cuipl
            xaa__avir += birf__cuipl * birf__cuipl
            iyrp__dudzu += ahzva__gwj
        wgcbg__aav = bodo.hiframes.series_kernels._compute_var_nan_count_ddof(
            xhrsz__vlwor, xaa__avir, iyrp__dudzu, ddof)
        return wgcbg__aav
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
                qepjg__tew = np.empty(len(q), np.int64)
                for gpwe__utg in range(len(q)):
                    skiww__kzifq = np.float64(q[gpwe__utg])
                    qepjg__tew[gpwe__utg] = bodo.libs.array_kernels.quantile(
                        arr.view(np.int64), skiww__kzifq)
                return qepjg__tew.view(np.dtype('datetime64[ns]'))
            return _impl_list_dt

        def impl_list(arr, q):
            qepjg__tew = np.empty(len(q), np.float64)
            for gpwe__utg in range(len(q)):
                skiww__kzifq = np.float64(q[gpwe__utg])
                qepjg__tew[gpwe__utg] = bodo.libs.array_kernels.quantile(arr,
                    skiww__kzifq)
            return qepjg__tew
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
        evw__wlpd = types.intp
    elif arr.dtype == types.bool_:
        evw__wlpd = np.int64
    else:
        evw__wlpd = arr.dtype
    apnpo__cmbe = evw__wlpd(0)
    if isinstance(arr.dtype, types.Float) and (not is_overload_true(skipna) or
        not is_overload_zero(min_count)):

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            ocunm__rmkv = apnpo__cmbe
            vtstq__rlhh = len(arr)
            iyrp__dudzu = 0
            for gpwe__utg in numba.parfors.parfor.internal_prange(vtstq__rlhh):
                birf__cuipl = apnpo__cmbe
                ahzva__gwj = 0
                if not bodo.libs.array_kernels.isna(arr, gpwe__utg
                    ) or not skipna:
                    birf__cuipl = arr[gpwe__utg]
                    ahzva__gwj = 1
                ocunm__rmkv += birf__cuipl
                iyrp__dudzu += ahzva__gwj
            wgcbg__aav = bodo.hiframes.series_kernels._var_handle_mincount(
                ocunm__rmkv, iyrp__dudzu, min_count)
            return wgcbg__aav
    else:

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            ocunm__rmkv = apnpo__cmbe
            vtstq__rlhh = len(arr)
            for gpwe__utg in numba.parfors.parfor.internal_prange(vtstq__rlhh):
                birf__cuipl = apnpo__cmbe
                if not bodo.libs.array_kernels.isna(arr, gpwe__utg):
                    birf__cuipl = arr[gpwe__utg]
                ocunm__rmkv += birf__cuipl
            return ocunm__rmkv
    return impl


def array_op_prod(arr, skipna, min_count):
    pass


@overload(array_op_prod)
def overload_array_op_prod(arr, skipna, min_count):
    wdvyo__hve = arr.dtype(1)
    if arr.dtype == types.bool_:
        wdvyo__hve = 1
    if isinstance(arr.dtype, types.Float):

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            ocunm__rmkv = wdvyo__hve
            iyrp__dudzu = 0
            for gpwe__utg in numba.parfors.parfor.internal_prange(len(arr)):
                birf__cuipl = wdvyo__hve
                ahzva__gwj = 0
                if not bodo.libs.array_kernels.isna(arr, gpwe__utg
                    ) or not skipna:
                    birf__cuipl = arr[gpwe__utg]
                    ahzva__gwj = 1
                iyrp__dudzu += ahzva__gwj
                ocunm__rmkv *= birf__cuipl
            wgcbg__aav = bodo.hiframes.series_kernels._var_handle_mincount(
                ocunm__rmkv, iyrp__dudzu, min_count)
            return wgcbg__aav
    else:

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            ocunm__rmkv = wdvyo__hve
            for gpwe__utg in numba.parfors.parfor.internal_prange(len(arr)):
                birf__cuipl = wdvyo__hve
                if not bodo.libs.array_kernels.isna(arr, gpwe__utg):
                    birf__cuipl = arr[gpwe__utg]
                ocunm__rmkv *= birf__cuipl
            return ocunm__rmkv
    return impl


def array_op_idxmax(arr, index):
    pass


@overload(array_op_idxmax, inline='always')
def overload_array_op_idxmax(arr, index):

    def impl(arr, index):
        gpwe__utg = bodo.libs.array_kernels._nan_argmax(arr)
        return index[gpwe__utg]
    return impl


def array_op_idxmin(arr, index):
    pass


@overload(array_op_idxmin, inline='always')
def overload_array_op_idxmin(arr, index):

    def impl(arr, index):
        gpwe__utg = bodo.libs.array_kernels._nan_argmin(arr)
        return index[gpwe__utg]
    return impl


def _convert_isin_values(values, use_hash_impl):
    pass


@overload(_convert_isin_values, no_unliteral=True)
def overload_convert_isin_values(values, use_hash_impl):
    if is_overload_true(use_hash_impl):

        def impl(values, use_hash_impl):
            ymaxe__ckju = {}
            for qokrn__jvk in values:
                ymaxe__ckju[bodo.utils.conversion.box_if_dt64(qokrn__jvk)] = 0
            return ymaxe__ckju
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
        vtstq__rlhh = len(arr)
        qepjg__tew = np.empty(vtstq__rlhh, np.bool_)
        for gpwe__utg in numba.parfors.parfor.internal_prange(vtstq__rlhh):
            qepjg__tew[gpwe__utg] = bodo.utils.conversion.box_if_dt64(arr[
                gpwe__utg]) in values
        return qepjg__tew
    return impl


@generated_jit(nopython=True)
def array_unique_vector_map(in_arr_tup):
    pccxs__cetjd = len(in_arr_tup) != 1
    wwyg__ayeju = list(in_arr_tup.types)
    jfj__mxt = 'def impl(in_arr_tup):\n'
    jfj__mxt += '  n = len(in_arr_tup[0])\n'
    if pccxs__cetjd:
        iid__vver = ', '.join([f'in_arr_tup[{gpwe__utg}][unused]' for
            gpwe__utg in range(len(in_arr_tup))])
        tdvt__iuk = ', '.join(['False' for xgxli__kxgrj in range(len(
            in_arr_tup))])
        jfj__mxt += f"""  arr_map = {{bodo.libs.nullable_tuple_ext.build_nullable_tuple(({iid__vver},), ({tdvt__iuk},)): 0 for unused in range(0)}}
"""
        jfj__mxt += '  map_vector = np.empty(n, np.int64)\n'
        for gpwe__utg, ucrrw__vae in enumerate(wwyg__ayeju):
            jfj__mxt += f'  in_lst_{gpwe__utg} = []\n'
            if is_str_arr_type(ucrrw__vae):
                jfj__mxt += f'  total_len_{gpwe__utg} = 0\n'
            jfj__mxt += f'  null_in_lst_{gpwe__utg} = []\n'
        jfj__mxt += '  for i in range(n):\n'
        edgwj__fwo = ', '.join([f'in_arr_tup[{gpwe__utg}][i]' for gpwe__utg in
            range(len(wwyg__ayeju))])
        bkcpv__gew = ', '.join([
            f'bodo.libs.array_kernels.isna(in_arr_tup[{gpwe__utg}], i)' for
            gpwe__utg in range(len(wwyg__ayeju))])
        jfj__mxt += f"""    data_val = bodo.libs.nullable_tuple_ext.build_nullable_tuple(({edgwj__fwo},), ({bkcpv__gew},))
"""
        jfj__mxt += '    if data_val not in arr_map:\n'
        jfj__mxt += '      set_val = len(arr_map)\n'
        jfj__mxt += '      values_tup = data_val._data\n'
        jfj__mxt += '      nulls_tup = data_val._null_values\n'
        for gpwe__utg, ucrrw__vae in enumerate(wwyg__ayeju):
            jfj__mxt += (
                f'      in_lst_{gpwe__utg}.append(values_tup[{gpwe__utg}])\n')
            jfj__mxt += (
                f'      null_in_lst_{gpwe__utg}.append(nulls_tup[{gpwe__utg}])\n'
                )
            if is_str_arr_type(ucrrw__vae):
                jfj__mxt += f"""      total_len_{gpwe__utg}  += nulls_tup[{gpwe__utg}] * len(values_tup[{gpwe__utg}])
"""
        jfj__mxt += '      arr_map[data_val] = len(arr_map)\n'
        jfj__mxt += '    else:\n'
        jfj__mxt += '      set_val = arr_map[data_val]\n'
        jfj__mxt += '    map_vector[i] = set_val\n'
        jfj__mxt += '  n_rows = len(arr_map)\n'
        for gpwe__utg, ucrrw__vae in enumerate(wwyg__ayeju):
            if is_str_arr_type(ucrrw__vae):
                jfj__mxt += f"""  out_arr_{gpwe__utg} = bodo.libs.str_arr_ext.pre_alloc_string_array(n_rows, total_len_{gpwe__utg})
"""
            else:
                jfj__mxt += f"""  out_arr_{gpwe__utg} = bodo.utils.utils.alloc_type(n_rows, in_arr_tup[{gpwe__utg}], (-1,))
"""
        jfj__mxt += '  for j in range(len(arr_map)):\n'
        for gpwe__utg in range(len(wwyg__ayeju)):
            jfj__mxt += f'    if null_in_lst_{gpwe__utg}[j]:\n'
            jfj__mxt += (
                f'      bodo.libs.array_kernels.setna(out_arr_{gpwe__utg}, j)\n'
                )
            jfj__mxt += '    else:\n'
            jfj__mxt += (
                f'      out_arr_{gpwe__utg}[j] = in_lst_{gpwe__utg}[j]\n')
        yudd__xqzh = ', '.join([f'out_arr_{gpwe__utg}' for gpwe__utg in
            range(len(wwyg__ayeju))])
        jfj__mxt += f'  return ({yudd__xqzh},), map_vector\n'
    else:
        jfj__mxt += '  in_arr = in_arr_tup[0]\n'
        jfj__mxt += (
            f'  arr_map = {{in_arr[unused]: 0 for unused in range(0)}}\n')
        jfj__mxt += '  map_vector = np.empty(n, np.int64)\n'
        jfj__mxt += '  is_na = 0\n'
        jfj__mxt += '  in_lst = []\n'
        if is_str_arr_type(wwyg__ayeju[0]):
            jfj__mxt += '  total_len = 0\n'
        jfj__mxt += '  for i in range(n):\n'
        jfj__mxt += '    if bodo.libs.array_kernels.isna(in_arr, i):\n'
        jfj__mxt += '      is_na = 1\n'
        jfj__mxt += (
            '      # Always put NA in the last location. We can safely use\n')
        jfj__mxt += (
            '      # -1 because in_arr[-1] == in_arr[len(in_arr) - 1]\n')
        jfj__mxt += '      set_val = -1\n'
        jfj__mxt += '    else:\n'
        jfj__mxt += '      data_val = in_arr[i]\n'
        jfj__mxt += '      if data_val not in arr_map:\n'
        jfj__mxt += '        set_val = len(arr_map)\n'
        jfj__mxt += '        in_lst.append(data_val)\n'
        if is_str_arr_type(wwyg__ayeju[0]):
            jfj__mxt += '        total_len += len(data_val)\n'
        jfj__mxt += '        arr_map[data_val] = len(arr_map)\n'
        jfj__mxt += '      else:\n'
        jfj__mxt += '        set_val = arr_map[data_val]\n'
        jfj__mxt += '    map_vector[i] = set_val\n'
        jfj__mxt += '  n_rows = len(arr_map) + is_na\n'
        if is_str_arr_type(wwyg__ayeju[0]):
            jfj__mxt += """  out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(n_rows, total_len)
"""
        else:
            jfj__mxt += (
                '  out_arr = bodo.utils.utils.alloc_type(n_rows, in_arr, (-1,))\n'
                )
        jfj__mxt += '  for j in range(len(arr_map)):\n'
        jfj__mxt += '    out_arr[j] = in_lst[j]\n'
        jfj__mxt += '  if is_na:\n'
        jfj__mxt += '    bodo.libs.array_kernels.setna(out_arr, n_rows - 1)\n'
        jfj__mxt += f'  return (out_arr,), map_vector\n'
    sqimb__asot = {}
    exec(jfj__mxt, {'bodo': bodo, 'np': np}, sqimb__asot)
    impl = sqimb__asot['impl']
    return impl
