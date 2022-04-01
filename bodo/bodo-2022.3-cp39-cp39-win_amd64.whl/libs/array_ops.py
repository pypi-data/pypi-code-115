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
    znkbb__gwov = np.empty(1, types.float64)
    bodo.libs.array_kernels.median_series_computation(znkbb__gwov.ctypes,
        arr, parallel, skipna)
    return znkbb__gwov[0]


def array_op_isna(arr):
    pass


@overload(array_op_isna)
def overload_array_op_isna(arr):

    def impl(arr):
        numba.parfors.parfor.init_prange()
        xnv__joxl = len(arr)
        tch__wydx = np.empty(xnv__joxl, np.bool_)
        for juk__dknjv in numba.parfors.parfor.internal_prange(xnv__joxl):
            tch__wydx[juk__dknjv] = bodo.libs.array_kernels.isna(arr,
                juk__dknjv)
        return tch__wydx
    return impl


def array_op_count(arr):
    pass


@overload(array_op_count)
def overload_array_op_count(arr):

    def impl(arr):
        numba.parfors.parfor.init_prange()
        sllwe__alpzi = 0
        for juk__dknjv in numba.parfors.parfor.internal_prange(len(arr)):
            rqp__yojz = 0
            if not bodo.libs.array_kernels.isna(arr, juk__dknjv):
                rqp__yojz = 1
            sllwe__alpzi += rqp__yojz
        znkbb__gwov = sllwe__alpzi
        return znkbb__gwov
    return impl


def array_op_describe(arr):
    pass


def array_op_describe_impl(arr):
    oqe__aekvo = array_op_count(arr)
    lozb__bwmp = array_op_min(arr)
    mzba__httk = array_op_max(arr)
    oni__swon = array_op_mean(arr)
    bsxos__dcrm = array_op_std(arr)
    emb__gvdt = array_op_quantile(arr, 0.25)
    oiejr__qrsdx = array_op_quantile(arr, 0.5)
    awsh__wcls = array_op_quantile(arr, 0.75)
    return (oqe__aekvo, oni__swon, bsxos__dcrm, lozb__bwmp, emb__gvdt,
        oiejr__qrsdx, awsh__wcls, mzba__httk)


def array_op_describe_dt_impl(arr):
    oqe__aekvo = array_op_count(arr)
    lozb__bwmp = array_op_min(arr)
    mzba__httk = array_op_max(arr)
    oni__swon = array_op_mean(arr)
    emb__gvdt = array_op_quantile(arr, 0.25)
    oiejr__qrsdx = array_op_quantile(arr, 0.5)
    awsh__wcls = array_op_quantile(arr, 0.75)
    return (oqe__aekvo, oni__swon, lozb__bwmp, emb__gvdt, oiejr__qrsdx,
        awsh__wcls, mzba__httk)


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
            ybflt__oph = numba.cpython.builtins.get_type_max_value(np.int64)
            sllwe__alpzi = 0
            for juk__dknjv in numba.parfors.parfor.internal_prange(len(arr)):
                ipr__zvu = ybflt__oph
                rqp__yojz = 0
                if not bodo.libs.array_kernels.isna(arr, juk__dknjv):
                    ipr__zvu = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(arr[juk__dknjv]))
                    rqp__yojz = 1
                ybflt__oph = min(ybflt__oph, ipr__zvu)
                sllwe__alpzi += rqp__yojz
            return bodo.hiframes.pd_index_ext._tdi_val_finalize(ybflt__oph,
                sllwe__alpzi)
        return impl_td64
    if arr.dtype == bodo.datetime64ns:

        def impl_dt64(arr):
            numba.parfors.parfor.init_prange()
            ybflt__oph = numba.cpython.builtins.get_type_max_value(np.int64)
            sllwe__alpzi = 0
            for juk__dknjv in numba.parfors.parfor.internal_prange(len(arr)):
                ipr__zvu = ybflt__oph
                rqp__yojz = 0
                if not bodo.libs.array_kernels.isna(arr, juk__dknjv):
                    ipr__zvu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        arr[juk__dknjv])
                    rqp__yojz = 1
                ybflt__oph = min(ybflt__oph, ipr__zvu)
                sllwe__alpzi += rqp__yojz
            return bodo.hiframes.pd_index_ext._dti_val_finalize(ybflt__oph,
                sllwe__alpzi)
        return impl_dt64
    if isinstance(arr, CategoricalArrayType):

        def impl_cat(arr):
            ckp__zgul = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            ybflt__oph = numba.cpython.builtins.get_type_max_value(np.int64)
            sllwe__alpzi = 0
            for juk__dknjv in numba.parfors.parfor.internal_prange(len(
                ckp__zgul)):
                lsyy__gbo = ckp__zgul[juk__dknjv]
                if lsyy__gbo == -1:
                    continue
                ybflt__oph = min(ybflt__oph, lsyy__gbo)
                sllwe__alpzi += 1
            znkbb__gwov = bodo.hiframes.series_kernels._box_cat_val(ybflt__oph,
                arr.dtype, sllwe__alpzi)
            return znkbb__gwov
        return impl_cat
    if arr == datetime_date_array_type:

        def impl_date(arr):
            numba.parfors.parfor.init_prange()
            ybflt__oph = bodo.hiframes.series_kernels._get_date_max_value()
            sllwe__alpzi = 0
            for juk__dknjv in numba.parfors.parfor.internal_prange(len(arr)):
                ipr__zvu = ybflt__oph
                rqp__yojz = 0
                if not bodo.libs.array_kernels.isna(arr, juk__dknjv):
                    ipr__zvu = arr[juk__dknjv]
                    rqp__yojz = 1
                ybflt__oph = min(ybflt__oph, ipr__zvu)
                sllwe__alpzi += rqp__yojz
            znkbb__gwov = bodo.hiframes.series_kernels._sum_handle_nan(
                ybflt__oph, sllwe__alpzi)
            return znkbb__gwov
        return impl_date

    def impl(arr):
        numba.parfors.parfor.init_prange()
        ybflt__oph = bodo.hiframes.series_kernels._get_type_max_value(arr.dtype
            )
        sllwe__alpzi = 0
        for juk__dknjv in numba.parfors.parfor.internal_prange(len(arr)):
            ipr__zvu = ybflt__oph
            rqp__yojz = 0
            if not bodo.libs.array_kernels.isna(arr, juk__dknjv):
                ipr__zvu = arr[juk__dknjv]
                rqp__yojz = 1
            ybflt__oph = min(ybflt__oph, ipr__zvu)
            sllwe__alpzi += rqp__yojz
        znkbb__gwov = bodo.hiframes.series_kernels._sum_handle_nan(ybflt__oph,
            sllwe__alpzi)
        return znkbb__gwov
    return impl


def array_op_max(arr):
    pass


@overload(array_op_max)
def overload_array_op_max(arr):
    if arr.dtype == bodo.timedelta64ns:

        def impl_td64(arr):
            numba.parfors.parfor.init_prange()
            ybflt__oph = numba.cpython.builtins.get_type_min_value(np.int64)
            sllwe__alpzi = 0
            for juk__dknjv in numba.parfors.parfor.internal_prange(len(arr)):
                ipr__zvu = ybflt__oph
                rqp__yojz = 0
                if not bodo.libs.array_kernels.isna(arr, juk__dknjv):
                    ipr__zvu = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(arr[juk__dknjv]))
                    rqp__yojz = 1
                ybflt__oph = max(ybflt__oph, ipr__zvu)
                sllwe__alpzi += rqp__yojz
            return bodo.hiframes.pd_index_ext._tdi_val_finalize(ybflt__oph,
                sllwe__alpzi)
        return impl_td64
    if arr.dtype == bodo.datetime64ns:

        def impl_dt64(arr):
            numba.parfors.parfor.init_prange()
            ybflt__oph = numba.cpython.builtins.get_type_min_value(np.int64)
            sllwe__alpzi = 0
            for juk__dknjv in numba.parfors.parfor.internal_prange(len(arr)):
                ipr__zvu = ybflt__oph
                rqp__yojz = 0
                if not bodo.libs.array_kernels.isna(arr, juk__dknjv):
                    ipr__zvu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        arr[juk__dknjv])
                    rqp__yojz = 1
                ybflt__oph = max(ybflt__oph, ipr__zvu)
                sllwe__alpzi += rqp__yojz
            return bodo.hiframes.pd_index_ext._dti_val_finalize(ybflt__oph,
                sllwe__alpzi)
        return impl_dt64
    if isinstance(arr, CategoricalArrayType):

        def impl_cat(arr):
            ckp__zgul = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            ybflt__oph = -1
            for juk__dknjv in numba.parfors.parfor.internal_prange(len(
                ckp__zgul)):
                ybflt__oph = max(ybflt__oph, ckp__zgul[juk__dknjv])
            znkbb__gwov = bodo.hiframes.series_kernels._box_cat_val(ybflt__oph,
                arr.dtype, 1)
            return znkbb__gwov
        return impl_cat
    if arr == datetime_date_array_type:

        def impl_date(arr):
            numba.parfors.parfor.init_prange()
            ybflt__oph = bodo.hiframes.series_kernels._get_date_min_value()
            sllwe__alpzi = 0
            for juk__dknjv in numba.parfors.parfor.internal_prange(len(arr)):
                ipr__zvu = ybflt__oph
                rqp__yojz = 0
                if not bodo.libs.array_kernels.isna(arr, juk__dknjv):
                    ipr__zvu = arr[juk__dknjv]
                    rqp__yojz = 1
                ybflt__oph = max(ybflt__oph, ipr__zvu)
                sllwe__alpzi += rqp__yojz
            znkbb__gwov = bodo.hiframes.series_kernels._sum_handle_nan(
                ybflt__oph, sllwe__alpzi)
            return znkbb__gwov
        return impl_date

    def impl(arr):
        numba.parfors.parfor.init_prange()
        ybflt__oph = bodo.hiframes.series_kernels._get_type_min_value(arr.dtype
            )
        sllwe__alpzi = 0
        for juk__dknjv in numba.parfors.parfor.internal_prange(len(arr)):
            ipr__zvu = ybflt__oph
            rqp__yojz = 0
            if not bodo.libs.array_kernels.isna(arr, juk__dknjv):
                ipr__zvu = arr[juk__dknjv]
                rqp__yojz = 1
            ybflt__oph = max(ybflt__oph, ipr__zvu)
            sllwe__alpzi += rqp__yojz
        znkbb__gwov = bodo.hiframes.series_kernels._sum_handle_nan(ybflt__oph,
            sllwe__alpzi)
        return znkbb__gwov
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
    prt__rtgxo = types.float64
    xat__qews = types.float64
    if isinstance(arr, types.Array) and arr.dtype == types.float32:
        prt__rtgxo = types.float32
        xat__qews = types.float32
    jail__dkhsj = prt__rtgxo(0)
    xgaaz__ydjp = xat__qews(0)
    zptxj__vtbrk = xat__qews(1)

    def impl(arr):
        numba.parfors.parfor.init_prange()
        ybflt__oph = jail__dkhsj
        sllwe__alpzi = xgaaz__ydjp
        for juk__dknjv in numba.parfors.parfor.internal_prange(len(arr)):
            ipr__zvu = jail__dkhsj
            rqp__yojz = xgaaz__ydjp
            if not bodo.libs.array_kernels.isna(arr, juk__dknjv):
                ipr__zvu = arr[juk__dknjv]
                rqp__yojz = zptxj__vtbrk
            ybflt__oph += ipr__zvu
            sllwe__alpzi += rqp__yojz
        znkbb__gwov = bodo.hiframes.series_kernels._mean_handle_nan(ybflt__oph,
            sllwe__alpzi)
        return znkbb__gwov
    return impl


def array_op_var(arr, skipna, ddof):
    pass


@overload(array_op_var)
def overload_array_op_var(arr, skipna, ddof):

    def impl(arr, skipna, ddof):
        numba.parfors.parfor.init_prange()
        hdo__yilf = 0.0
        zfq__qaaa = 0.0
        sllwe__alpzi = 0
        for juk__dknjv in numba.parfors.parfor.internal_prange(len(arr)):
            ipr__zvu = 0.0
            rqp__yojz = 0
            if not bodo.libs.array_kernels.isna(arr, juk__dknjv) or not skipna:
                ipr__zvu = arr[juk__dknjv]
                rqp__yojz = 1
            hdo__yilf += ipr__zvu
            zfq__qaaa += ipr__zvu * ipr__zvu
            sllwe__alpzi += rqp__yojz
        znkbb__gwov = bodo.hiframes.series_kernels._compute_var_nan_count_ddof(
            hdo__yilf, zfq__qaaa, sllwe__alpzi, ddof)
        return znkbb__gwov
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
                tch__wydx = np.empty(len(q), np.int64)
                for juk__dknjv in range(len(q)):
                    kjt__nnr = np.float64(q[juk__dknjv])
                    tch__wydx[juk__dknjv] = bodo.libs.array_kernels.quantile(
                        arr.view(np.int64), kjt__nnr)
                return tch__wydx.view(np.dtype('datetime64[ns]'))
            return _impl_list_dt

        def impl_list(arr, q):
            tch__wydx = np.empty(len(q), np.float64)
            for juk__dknjv in range(len(q)):
                kjt__nnr = np.float64(q[juk__dknjv])
                tch__wydx[juk__dknjv] = bodo.libs.array_kernels.quantile(arr,
                    kjt__nnr)
            return tch__wydx
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
        cqic__svnpd = types.intp
    elif arr.dtype == types.bool_:
        cqic__svnpd = np.int64
    else:
        cqic__svnpd = arr.dtype
    pry__crvjt = cqic__svnpd(0)
    if isinstance(arr.dtype, types.Float) and (not is_overload_true(skipna) or
        not is_overload_zero(min_count)):

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            ybflt__oph = pry__crvjt
            xnv__joxl = len(arr)
            sllwe__alpzi = 0
            for juk__dknjv in numba.parfors.parfor.internal_prange(xnv__joxl):
                ipr__zvu = pry__crvjt
                rqp__yojz = 0
                if not bodo.libs.array_kernels.isna(arr, juk__dknjv
                    ) or not skipna:
                    ipr__zvu = arr[juk__dknjv]
                    rqp__yojz = 1
                ybflt__oph += ipr__zvu
                sllwe__alpzi += rqp__yojz
            znkbb__gwov = bodo.hiframes.series_kernels._var_handle_mincount(
                ybflt__oph, sllwe__alpzi, min_count)
            return znkbb__gwov
    else:

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            ybflt__oph = pry__crvjt
            xnv__joxl = len(arr)
            for juk__dknjv in numba.parfors.parfor.internal_prange(xnv__joxl):
                ipr__zvu = pry__crvjt
                if not bodo.libs.array_kernels.isna(arr, juk__dknjv):
                    ipr__zvu = arr[juk__dknjv]
                ybflt__oph += ipr__zvu
            return ybflt__oph
    return impl


def array_op_prod(arr, skipna, min_count):
    pass


@overload(array_op_prod)
def overload_array_op_prod(arr, skipna, min_count):
    zkpcf__nnwzx = arr.dtype(1)
    if arr.dtype == types.bool_:
        zkpcf__nnwzx = 1
    if isinstance(arr.dtype, types.Float):

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            ybflt__oph = zkpcf__nnwzx
            sllwe__alpzi = 0
            for juk__dknjv in numba.parfors.parfor.internal_prange(len(arr)):
                ipr__zvu = zkpcf__nnwzx
                rqp__yojz = 0
                if not bodo.libs.array_kernels.isna(arr, juk__dknjv
                    ) or not skipna:
                    ipr__zvu = arr[juk__dknjv]
                    rqp__yojz = 1
                sllwe__alpzi += rqp__yojz
                ybflt__oph *= ipr__zvu
            znkbb__gwov = bodo.hiframes.series_kernels._var_handle_mincount(
                ybflt__oph, sllwe__alpzi, min_count)
            return znkbb__gwov
    else:

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            ybflt__oph = zkpcf__nnwzx
            for juk__dknjv in numba.parfors.parfor.internal_prange(len(arr)):
                ipr__zvu = zkpcf__nnwzx
                if not bodo.libs.array_kernels.isna(arr, juk__dknjv):
                    ipr__zvu = arr[juk__dknjv]
                ybflt__oph *= ipr__zvu
            return ybflt__oph
    return impl


def array_op_idxmax(arr, index):
    pass


@overload(array_op_idxmax, inline='always')
def overload_array_op_idxmax(arr, index):

    def impl(arr, index):
        juk__dknjv = bodo.libs.array_kernels._nan_argmax(arr)
        return index[juk__dknjv]
    return impl


def array_op_idxmin(arr, index):
    pass


@overload(array_op_idxmin, inline='always')
def overload_array_op_idxmin(arr, index):

    def impl(arr, index):
        juk__dknjv = bodo.libs.array_kernels._nan_argmin(arr)
        return index[juk__dknjv]
    return impl


def _convert_isin_values(values, use_hash_impl):
    pass


@overload(_convert_isin_values, no_unliteral=True)
def overload_convert_isin_values(values, use_hash_impl):
    if is_overload_true(use_hash_impl):

        def impl(values, use_hash_impl):
            ayce__oqd = {}
            for oeuyr__ayog in values:
                ayce__oqd[bodo.utils.conversion.box_if_dt64(oeuyr__ayog)] = 0
            return ayce__oqd
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
        xnv__joxl = len(arr)
        tch__wydx = np.empty(xnv__joxl, np.bool_)
        for juk__dknjv in numba.parfors.parfor.internal_prange(xnv__joxl):
            tch__wydx[juk__dknjv] = bodo.utils.conversion.box_if_dt64(arr[
                juk__dknjv]) in values
        return tch__wydx
    return impl


@generated_jit(nopython=True)
def array_unique_vector_map(in_arr_tup):
    wywxm__wjtp = len(in_arr_tup) != 1
    ljkvf__pbka = list(in_arr_tup.types)
    mlktm__gukbx = 'def impl(in_arr_tup):\n'
    mlktm__gukbx += '  n = len(in_arr_tup[0])\n'
    if wywxm__wjtp:
        wtp__ofxcv = ', '.join([f'in_arr_tup[{juk__dknjv}][unused]' for
            juk__dknjv in range(len(in_arr_tup))])
        ruocq__knn = ', '.join(['False' for mgtbk__vug in range(len(
            in_arr_tup))])
        mlktm__gukbx += f"""  arr_map = {{bodo.libs.nullable_tuple_ext.build_nullable_tuple(({wtp__ofxcv},), ({ruocq__knn},)): 0 for unused in range(0)}}
"""
        mlktm__gukbx += '  map_vector = np.empty(n, np.int64)\n'
        for juk__dknjv, detl__luiqb in enumerate(ljkvf__pbka):
            mlktm__gukbx += f'  in_lst_{juk__dknjv} = []\n'
            if is_str_arr_type(detl__luiqb):
                mlktm__gukbx += f'  total_len_{juk__dknjv} = 0\n'
            mlktm__gukbx += f'  null_in_lst_{juk__dknjv} = []\n'
        mlktm__gukbx += '  for i in range(n):\n'
        epo__prqvb = ', '.join([f'in_arr_tup[{juk__dknjv}][i]' for
            juk__dknjv in range(len(ljkvf__pbka))])
        azs__bpx = ', '.join([
            f'bodo.libs.array_kernels.isna(in_arr_tup[{juk__dknjv}], i)' for
            juk__dknjv in range(len(ljkvf__pbka))])
        mlktm__gukbx += f"""    data_val = bodo.libs.nullable_tuple_ext.build_nullable_tuple(({epo__prqvb},), ({azs__bpx},))
"""
        mlktm__gukbx += '    if data_val not in arr_map:\n'
        mlktm__gukbx += '      set_val = len(arr_map)\n'
        mlktm__gukbx += '      values_tup = data_val._data\n'
        mlktm__gukbx += '      nulls_tup = data_val._null_values\n'
        for juk__dknjv, detl__luiqb in enumerate(ljkvf__pbka):
            mlktm__gukbx += (
                f'      in_lst_{juk__dknjv}.append(values_tup[{juk__dknjv}])\n'
                )
            mlktm__gukbx += (
                f'      null_in_lst_{juk__dknjv}.append(nulls_tup[{juk__dknjv}])\n'
                )
            if is_str_arr_type(detl__luiqb):
                mlktm__gukbx += f"""      total_len_{juk__dknjv}  += nulls_tup[{juk__dknjv}] * len(values_tup[{juk__dknjv}])
"""
        mlktm__gukbx += '      arr_map[data_val] = len(arr_map)\n'
        mlktm__gukbx += '    else:\n'
        mlktm__gukbx += '      set_val = arr_map[data_val]\n'
        mlktm__gukbx += '    map_vector[i] = set_val\n'
        mlktm__gukbx += '  n_rows = len(arr_map)\n'
        for juk__dknjv, detl__luiqb in enumerate(ljkvf__pbka):
            if is_str_arr_type(detl__luiqb):
                mlktm__gukbx += f"""  out_arr_{juk__dknjv} = bodo.libs.str_arr_ext.pre_alloc_string_array(n_rows, total_len_{juk__dknjv})
"""
            else:
                mlktm__gukbx += f"""  out_arr_{juk__dknjv} = bodo.utils.utils.alloc_type(n_rows, in_arr_tup[{juk__dknjv}], (-1,))
"""
        mlktm__gukbx += '  for j in range(len(arr_map)):\n'
        for juk__dknjv in range(len(ljkvf__pbka)):
            mlktm__gukbx += f'    if null_in_lst_{juk__dknjv}[j]:\n'
            mlktm__gukbx += (
                f'      bodo.libs.array_kernels.setna(out_arr_{juk__dknjv}, j)\n'
                )
            mlktm__gukbx += '    else:\n'
            mlktm__gukbx += (
                f'      out_arr_{juk__dknjv}[j] = in_lst_{juk__dknjv}[j]\n')
        ulw__vwn = ', '.join([f'out_arr_{juk__dknjv}' for juk__dknjv in
            range(len(ljkvf__pbka))])
        mlktm__gukbx += f'  return ({ulw__vwn},), map_vector\n'
    else:
        mlktm__gukbx += '  in_arr = in_arr_tup[0]\n'
        mlktm__gukbx += (
            f'  arr_map = {{in_arr[unused]: 0 for unused in range(0)}}\n')
        mlktm__gukbx += '  map_vector = np.empty(n, np.int64)\n'
        mlktm__gukbx += '  is_na = 0\n'
        mlktm__gukbx += '  in_lst = []\n'
        if is_str_arr_type(ljkvf__pbka[0]):
            mlktm__gukbx += '  total_len = 0\n'
        mlktm__gukbx += '  for i in range(n):\n'
        mlktm__gukbx += '    if bodo.libs.array_kernels.isna(in_arr, i):\n'
        mlktm__gukbx += '      is_na = 1\n'
        mlktm__gukbx += (
            '      # Always put NA in the last location. We can safely use\n')
        mlktm__gukbx += (
            '      # -1 because in_arr[-1] == in_arr[len(in_arr) - 1]\n')
        mlktm__gukbx += '      set_val = -1\n'
        mlktm__gukbx += '    else:\n'
        mlktm__gukbx += '      data_val = in_arr[i]\n'
        mlktm__gukbx += '      if data_val not in arr_map:\n'
        mlktm__gukbx += '        set_val = len(arr_map)\n'
        mlktm__gukbx += '        in_lst.append(data_val)\n'
        if is_str_arr_type(ljkvf__pbka[0]):
            mlktm__gukbx += '        total_len += len(data_val)\n'
        mlktm__gukbx += '        arr_map[data_val] = len(arr_map)\n'
        mlktm__gukbx += '      else:\n'
        mlktm__gukbx += '        set_val = arr_map[data_val]\n'
        mlktm__gukbx += '    map_vector[i] = set_val\n'
        mlktm__gukbx += '  n_rows = len(arr_map) + is_na\n'
        if is_str_arr_type(ljkvf__pbka[0]):
            mlktm__gukbx += """  out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(n_rows, total_len)
"""
        else:
            mlktm__gukbx += (
                '  out_arr = bodo.utils.utils.alloc_type(n_rows, in_arr, (-1,))\n'
                )
        mlktm__gukbx += '  for j in range(len(arr_map)):\n'
        mlktm__gukbx += '    out_arr[j] = in_lst[j]\n'
        mlktm__gukbx += '  if is_na:\n'
        mlktm__gukbx += (
            '    bodo.libs.array_kernels.setna(out_arr, n_rows - 1)\n')
        mlktm__gukbx += f'  return (out_arr,), map_vector\n'
    ffx__dtlep = {}
    exec(mlktm__gukbx, {'bodo': bodo, 'np': np}, ffx__dtlep)
    impl = ffx__dtlep['impl']
    return impl
