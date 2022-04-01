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
    aztma__dgvp = np.empty(1, types.float64)
    bodo.libs.array_kernels.median_series_computation(aztma__dgvp.ctypes,
        arr, parallel, skipna)
    return aztma__dgvp[0]


def array_op_isna(arr):
    pass


@overload(array_op_isna)
def overload_array_op_isna(arr):

    def impl(arr):
        numba.parfors.parfor.init_prange()
        bsuw__sao = len(arr)
        vkyns__ipbuq = np.empty(bsuw__sao, np.bool_)
        for nlw__bhwrl in numba.parfors.parfor.internal_prange(bsuw__sao):
            vkyns__ipbuq[nlw__bhwrl] = bodo.libs.array_kernels.isna(arr,
                nlw__bhwrl)
        return vkyns__ipbuq
    return impl


def array_op_count(arr):
    pass


@overload(array_op_count)
def overload_array_op_count(arr):

    def impl(arr):
        numba.parfors.parfor.init_prange()
        iyy__zlv = 0
        for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(arr)):
            zyny__ekmtq = 0
            if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl):
                zyny__ekmtq = 1
            iyy__zlv += zyny__ekmtq
        aztma__dgvp = iyy__zlv
        return aztma__dgvp
    return impl


def array_op_describe(arr):
    pass


def array_op_describe_impl(arr):
    hdish__cyy = array_op_count(arr)
    mpwvq__jjgm = array_op_min(arr)
    hdj__lmwi = array_op_max(arr)
    vjee__ohkdj = array_op_mean(arr)
    cnhys__vhs = array_op_std(arr)
    tqca__dhndz = array_op_quantile(arr, 0.25)
    haqpd__jzi = array_op_quantile(arr, 0.5)
    xyew__vkc = array_op_quantile(arr, 0.75)
    return (hdish__cyy, vjee__ohkdj, cnhys__vhs, mpwvq__jjgm, tqca__dhndz,
        haqpd__jzi, xyew__vkc, hdj__lmwi)


def array_op_describe_dt_impl(arr):
    hdish__cyy = array_op_count(arr)
    mpwvq__jjgm = array_op_min(arr)
    hdj__lmwi = array_op_max(arr)
    vjee__ohkdj = array_op_mean(arr)
    tqca__dhndz = array_op_quantile(arr, 0.25)
    haqpd__jzi = array_op_quantile(arr, 0.5)
    xyew__vkc = array_op_quantile(arr, 0.75)
    return (hdish__cyy, vjee__ohkdj, mpwvq__jjgm, tqca__dhndz, haqpd__jzi,
        xyew__vkc, hdj__lmwi)


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
            bxp__ocdkg = numba.cpython.builtins.get_type_max_value(np.int64)
            iyy__zlv = 0
            for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(arr)):
                necl__nzhck = bxp__ocdkg
                zyny__ekmtq = 0
                if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl):
                    necl__nzhck = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(arr[nlw__bhwrl]))
                    zyny__ekmtq = 1
                bxp__ocdkg = min(bxp__ocdkg, necl__nzhck)
                iyy__zlv += zyny__ekmtq
            return bodo.hiframes.pd_index_ext._tdi_val_finalize(bxp__ocdkg,
                iyy__zlv)
        return impl_td64
    if arr.dtype == bodo.datetime64ns:

        def impl_dt64(arr):
            numba.parfors.parfor.init_prange()
            bxp__ocdkg = numba.cpython.builtins.get_type_max_value(np.int64)
            iyy__zlv = 0
            for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(arr)):
                necl__nzhck = bxp__ocdkg
                zyny__ekmtq = 0
                if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl):
                    necl__nzhck = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(arr[nlw__bhwrl]))
                    zyny__ekmtq = 1
                bxp__ocdkg = min(bxp__ocdkg, necl__nzhck)
                iyy__zlv += zyny__ekmtq
            return bodo.hiframes.pd_index_ext._dti_val_finalize(bxp__ocdkg,
                iyy__zlv)
        return impl_dt64
    if isinstance(arr, CategoricalArrayType):

        def impl_cat(arr):
            ujsjf__bfbj = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            bxp__ocdkg = numba.cpython.builtins.get_type_max_value(np.int64)
            iyy__zlv = 0
            for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(
                ujsjf__bfbj)):
                ans__pem = ujsjf__bfbj[nlw__bhwrl]
                if ans__pem == -1:
                    continue
                bxp__ocdkg = min(bxp__ocdkg, ans__pem)
                iyy__zlv += 1
            aztma__dgvp = bodo.hiframes.series_kernels._box_cat_val(bxp__ocdkg,
                arr.dtype, iyy__zlv)
            return aztma__dgvp
        return impl_cat
    if arr == datetime_date_array_type:

        def impl_date(arr):
            numba.parfors.parfor.init_prange()
            bxp__ocdkg = bodo.hiframes.series_kernels._get_date_max_value()
            iyy__zlv = 0
            for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(arr)):
                necl__nzhck = bxp__ocdkg
                zyny__ekmtq = 0
                if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl):
                    necl__nzhck = arr[nlw__bhwrl]
                    zyny__ekmtq = 1
                bxp__ocdkg = min(bxp__ocdkg, necl__nzhck)
                iyy__zlv += zyny__ekmtq
            aztma__dgvp = bodo.hiframes.series_kernels._sum_handle_nan(
                bxp__ocdkg, iyy__zlv)
            return aztma__dgvp
        return impl_date

    def impl(arr):
        numba.parfors.parfor.init_prange()
        bxp__ocdkg = bodo.hiframes.series_kernels._get_type_max_value(arr.dtype
            )
        iyy__zlv = 0
        for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(arr)):
            necl__nzhck = bxp__ocdkg
            zyny__ekmtq = 0
            if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl):
                necl__nzhck = arr[nlw__bhwrl]
                zyny__ekmtq = 1
            bxp__ocdkg = min(bxp__ocdkg, necl__nzhck)
            iyy__zlv += zyny__ekmtq
        aztma__dgvp = bodo.hiframes.series_kernels._sum_handle_nan(bxp__ocdkg,
            iyy__zlv)
        return aztma__dgvp
    return impl


def array_op_max(arr):
    pass


@overload(array_op_max)
def overload_array_op_max(arr):
    if arr.dtype == bodo.timedelta64ns:

        def impl_td64(arr):
            numba.parfors.parfor.init_prange()
            bxp__ocdkg = numba.cpython.builtins.get_type_min_value(np.int64)
            iyy__zlv = 0
            for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(arr)):
                necl__nzhck = bxp__ocdkg
                zyny__ekmtq = 0
                if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl):
                    necl__nzhck = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(arr[nlw__bhwrl]))
                    zyny__ekmtq = 1
                bxp__ocdkg = max(bxp__ocdkg, necl__nzhck)
                iyy__zlv += zyny__ekmtq
            return bodo.hiframes.pd_index_ext._tdi_val_finalize(bxp__ocdkg,
                iyy__zlv)
        return impl_td64
    if arr.dtype == bodo.datetime64ns:

        def impl_dt64(arr):
            numba.parfors.parfor.init_prange()
            bxp__ocdkg = numba.cpython.builtins.get_type_min_value(np.int64)
            iyy__zlv = 0
            for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(arr)):
                necl__nzhck = bxp__ocdkg
                zyny__ekmtq = 0
                if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl):
                    necl__nzhck = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(arr[nlw__bhwrl]))
                    zyny__ekmtq = 1
                bxp__ocdkg = max(bxp__ocdkg, necl__nzhck)
                iyy__zlv += zyny__ekmtq
            return bodo.hiframes.pd_index_ext._dti_val_finalize(bxp__ocdkg,
                iyy__zlv)
        return impl_dt64
    if isinstance(arr, CategoricalArrayType):

        def impl_cat(arr):
            ujsjf__bfbj = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arr))
            numba.parfors.parfor.init_prange()
            bxp__ocdkg = -1
            for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(
                ujsjf__bfbj)):
                bxp__ocdkg = max(bxp__ocdkg, ujsjf__bfbj[nlw__bhwrl])
            aztma__dgvp = bodo.hiframes.series_kernels._box_cat_val(bxp__ocdkg,
                arr.dtype, 1)
            return aztma__dgvp
        return impl_cat
    if arr == datetime_date_array_type:

        def impl_date(arr):
            numba.parfors.parfor.init_prange()
            bxp__ocdkg = bodo.hiframes.series_kernels._get_date_min_value()
            iyy__zlv = 0
            for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(arr)):
                necl__nzhck = bxp__ocdkg
                zyny__ekmtq = 0
                if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl):
                    necl__nzhck = arr[nlw__bhwrl]
                    zyny__ekmtq = 1
                bxp__ocdkg = max(bxp__ocdkg, necl__nzhck)
                iyy__zlv += zyny__ekmtq
            aztma__dgvp = bodo.hiframes.series_kernels._sum_handle_nan(
                bxp__ocdkg, iyy__zlv)
            return aztma__dgvp
        return impl_date

    def impl(arr):
        numba.parfors.parfor.init_prange()
        bxp__ocdkg = bodo.hiframes.series_kernels._get_type_min_value(arr.dtype
            )
        iyy__zlv = 0
        for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(arr)):
            necl__nzhck = bxp__ocdkg
            zyny__ekmtq = 0
            if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl):
                necl__nzhck = arr[nlw__bhwrl]
                zyny__ekmtq = 1
            bxp__ocdkg = max(bxp__ocdkg, necl__nzhck)
            iyy__zlv += zyny__ekmtq
        aztma__dgvp = bodo.hiframes.series_kernels._sum_handle_nan(bxp__ocdkg,
            iyy__zlv)
        return aztma__dgvp
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
    spnvb__njljc = types.float64
    jfoeb__kvjj = types.float64
    if isinstance(arr, types.Array) and arr.dtype == types.float32:
        spnvb__njljc = types.float32
        jfoeb__kvjj = types.float32
    yxmw__dkcd = spnvb__njljc(0)
    zal__krlw = jfoeb__kvjj(0)
    qlfy__xqct = jfoeb__kvjj(1)

    def impl(arr):
        numba.parfors.parfor.init_prange()
        bxp__ocdkg = yxmw__dkcd
        iyy__zlv = zal__krlw
        for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(arr)):
            necl__nzhck = yxmw__dkcd
            zyny__ekmtq = zal__krlw
            if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl):
                necl__nzhck = arr[nlw__bhwrl]
                zyny__ekmtq = qlfy__xqct
            bxp__ocdkg += necl__nzhck
            iyy__zlv += zyny__ekmtq
        aztma__dgvp = bodo.hiframes.series_kernels._mean_handle_nan(bxp__ocdkg,
            iyy__zlv)
        return aztma__dgvp
    return impl


def array_op_var(arr, skipna, ddof):
    pass


@overload(array_op_var)
def overload_array_op_var(arr, skipna, ddof):

    def impl(arr, skipna, ddof):
        numba.parfors.parfor.init_prange()
        zovrk__nqow = 0.0
        mosd__lxt = 0.0
        iyy__zlv = 0
        for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(arr)):
            necl__nzhck = 0.0
            zyny__ekmtq = 0
            if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl) or not skipna:
                necl__nzhck = arr[nlw__bhwrl]
                zyny__ekmtq = 1
            zovrk__nqow += necl__nzhck
            mosd__lxt += necl__nzhck * necl__nzhck
            iyy__zlv += zyny__ekmtq
        aztma__dgvp = bodo.hiframes.series_kernels._compute_var_nan_count_ddof(
            zovrk__nqow, mosd__lxt, iyy__zlv, ddof)
        return aztma__dgvp
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
                vkyns__ipbuq = np.empty(len(q), np.int64)
                for nlw__bhwrl in range(len(q)):
                    lekj__gbtfh = np.float64(q[nlw__bhwrl])
                    vkyns__ipbuq[nlw__bhwrl
                        ] = bodo.libs.array_kernels.quantile(arr.view(np.
                        int64), lekj__gbtfh)
                return vkyns__ipbuq.view(np.dtype('datetime64[ns]'))
            return _impl_list_dt

        def impl_list(arr, q):
            vkyns__ipbuq = np.empty(len(q), np.float64)
            for nlw__bhwrl in range(len(q)):
                lekj__gbtfh = np.float64(q[nlw__bhwrl])
                vkyns__ipbuq[nlw__bhwrl] = bodo.libs.array_kernels.quantile(arr
                    , lekj__gbtfh)
            return vkyns__ipbuq
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
        edvvj__zuh = types.intp
    elif arr.dtype == types.bool_:
        edvvj__zuh = np.int64
    else:
        edvvj__zuh = arr.dtype
    zapmd__clsm = edvvj__zuh(0)
    if isinstance(arr.dtype, types.Float) and (not is_overload_true(skipna) or
        not is_overload_zero(min_count)):

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            bxp__ocdkg = zapmd__clsm
            bsuw__sao = len(arr)
            iyy__zlv = 0
            for nlw__bhwrl in numba.parfors.parfor.internal_prange(bsuw__sao):
                necl__nzhck = zapmd__clsm
                zyny__ekmtq = 0
                if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl
                    ) or not skipna:
                    necl__nzhck = arr[nlw__bhwrl]
                    zyny__ekmtq = 1
                bxp__ocdkg += necl__nzhck
                iyy__zlv += zyny__ekmtq
            aztma__dgvp = bodo.hiframes.series_kernels._var_handle_mincount(
                bxp__ocdkg, iyy__zlv, min_count)
            return aztma__dgvp
    else:

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            bxp__ocdkg = zapmd__clsm
            bsuw__sao = len(arr)
            for nlw__bhwrl in numba.parfors.parfor.internal_prange(bsuw__sao):
                necl__nzhck = zapmd__clsm
                if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl):
                    necl__nzhck = arr[nlw__bhwrl]
                bxp__ocdkg += necl__nzhck
            return bxp__ocdkg
    return impl


def array_op_prod(arr, skipna, min_count):
    pass


@overload(array_op_prod)
def overload_array_op_prod(arr, skipna, min_count):
    zkb__fiew = arr.dtype(1)
    if arr.dtype == types.bool_:
        zkb__fiew = 1
    if isinstance(arr.dtype, types.Float):

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            bxp__ocdkg = zkb__fiew
            iyy__zlv = 0
            for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(arr)):
                necl__nzhck = zkb__fiew
                zyny__ekmtq = 0
                if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl
                    ) or not skipna:
                    necl__nzhck = arr[nlw__bhwrl]
                    zyny__ekmtq = 1
                iyy__zlv += zyny__ekmtq
                bxp__ocdkg *= necl__nzhck
            aztma__dgvp = bodo.hiframes.series_kernels._var_handle_mincount(
                bxp__ocdkg, iyy__zlv, min_count)
            return aztma__dgvp
    else:

        def impl(arr, skipna, min_count):
            numba.parfors.parfor.init_prange()
            bxp__ocdkg = zkb__fiew
            for nlw__bhwrl in numba.parfors.parfor.internal_prange(len(arr)):
                necl__nzhck = zkb__fiew
                if not bodo.libs.array_kernels.isna(arr, nlw__bhwrl):
                    necl__nzhck = arr[nlw__bhwrl]
                bxp__ocdkg *= necl__nzhck
            return bxp__ocdkg
    return impl


def array_op_idxmax(arr, index):
    pass


@overload(array_op_idxmax, inline='always')
def overload_array_op_idxmax(arr, index):

    def impl(arr, index):
        nlw__bhwrl = bodo.libs.array_kernels._nan_argmax(arr)
        return index[nlw__bhwrl]
    return impl


def array_op_idxmin(arr, index):
    pass


@overload(array_op_idxmin, inline='always')
def overload_array_op_idxmin(arr, index):

    def impl(arr, index):
        nlw__bhwrl = bodo.libs.array_kernels._nan_argmin(arr)
        return index[nlw__bhwrl]
    return impl


def _convert_isin_values(values, use_hash_impl):
    pass


@overload(_convert_isin_values, no_unliteral=True)
def overload_convert_isin_values(values, use_hash_impl):
    if is_overload_true(use_hash_impl):

        def impl(values, use_hash_impl):
            xbwxh__ueoui = {}
            for ekj__beyj in values:
                xbwxh__ueoui[bodo.utils.conversion.box_if_dt64(ekj__beyj)] = 0
            return xbwxh__ueoui
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
        bsuw__sao = len(arr)
        vkyns__ipbuq = np.empty(bsuw__sao, np.bool_)
        for nlw__bhwrl in numba.parfors.parfor.internal_prange(bsuw__sao):
            vkyns__ipbuq[nlw__bhwrl] = bodo.utils.conversion.box_if_dt64(arr
                [nlw__bhwrl]) in values
        return vkyns__ipbuq
    return impl


@generated_jit(nopython=True)
def array_unique_vector_map(in_arr_tup):
    lgh__dllfx = len(in_arr_tup) != 1
    azmga__xkhtm = list(in_arr_tup.types)
    itsy__xbn = 'def impl(in_arr_tup):\n'
    itsy__xbn += '  n = len(in_arr_tup[0])\n'
    if lgh__dllfx:
        hkk__ood = ', '.join([f'in_arr_tup[{nlw__bhwrl}][unused]' for
            nlw__bhwrl in range(len(in_arr_tup))])
        kquf__vjnlp = ', '.join(['False' for nyawh__efr in range(len(
            in_arr_tup))])
        itsy__xbn += f"""  arr_map = {{bodo.libs.nullable_tuple_ext.build_nullable_tuple(({hkk__ood},), ({kquf__vjnlp},)): 0 for unused in range(0)}}
"""
        itsy__xbn += '  map_vector = np.empty(n, np.int64)\n'
        for nlw__bhwrl, lalj__tazh in enumerate(azmga__xkhtm):
            itsy__xbn += f'  in_lst_{nlw__bhwrl} = []\n'
            if is_str_arr_type(lalj__tazh):
                itsy__xbn += f'  total_len_{nlw__bhwrl} = 0\n'
            itsy__xbn += f'  null_in_lst_{nlw__bhwrl} = []\n'
        itsy__xbn += '  for i in range(n):\n'
        dfoax__nno = ', '.join([f'in_arr_tup[{nlw__bhwrl}][i]' for
            nlw__bhwrl in range(len(azmga__xkhtm))])
        kfqtm__yjmy = ', '.join([
            f'bodo.libs.array_kernels.isna(in_arr_tup[{nlw__bhwrl}], i)' for
            nlw__bhwrl in range(len(azmga__xkhtm))])
        itsy__xbn += f"""    data_val = bodo.libs.nullable_tuple_ext.build_nullable_tuple(({dfoax__nno},), ({kfqtm__yjmy},))
"""
        itsy__xbn += '    if data_val not in arr_map:\n'
        itsy__xbn += '      set_val = len(arr_map)\n'
        itsy__xbn += '      values_tup = data_val._data\n'
        itsy__xbn += '      nulls_tup = data_val._null_values\n'
        for nlw__bhwrl, lalj__tazh in enumerate(azmga__xkhtm):
            itsy__xbn += (
                f'      in_lst_{nlw__bhwrl}.append(values_tup[{nlw__bhwrl}])\n'
                )
            itsy__xbn += (
                f'      null_in_lst_{nlw__bhwrl}.append(nulls_tup[{nlw__bhwrl}])\n'
                )
            if is_str_arr_type(lalj__tazh):
                itsy__xbn += f"""      total_len_{nlw__bhwrl}  += nulls_tup[{nlw__bhwrl}] * len(values_tup[{nlw__bhwrl}])
"""
        itsy__xbn += '      arr_map[data_val] = len(arr_map)\n'
        itsy__xbn += '    else:\n'
        itsy__xbn += '      set_val = arr_map[data_val]\n'
        itsy__xbn += '    map_vector[i] = set_val\n'
        itsy__xbn += '  n_rows = len(arr_map)\n'
        for nlw__bhwrl, lalj__tazh in enumerate(azmga__xkhtm):
            if is_str_arr_type(lalj__tazh):
                itsy__xbn += f"""  out_arr_{nlw__bhwrl} = bodo.libs.str_arr_ext.pre_alloc_string_array(n_rows, total_len_{nlw__bhwrl})
"""
            else:
                itsy__xbn += f"""  out_arr_{nlw__bhwrl} = bodo.utils.utils.alloc_type(n_rows, in_arr_tup[{nlw__bhwrl}], (-1,))
"""
        itsy__xbn += '  for j in range(len(arr_map)):\n'
        for nlw__bhwrl in range(len(azmga__xkhtm)):
            itsy__xbn += f'    if null_in_lst_{nlw__bhwrl}[j]:\n'
            itsy__xbn += (
                f'      bodo.libs.array_kernels.setna(out_arr_{nlw__bhwrl}, j)\n'
                )
            itsy__xbn += '    else:\n'
            itsy__xbn += (
                f'      out_arr_{nlw__bhwrl}[j] = in_lst_{nlw__bhwrl}[j]\n')
        kqq__cirm = ', '.join([f'out_arr_{nlw__bhwrl}' for nlw__bhwrl in
            range(len(azmga__xkhtm))])
        itsy__xbn += f'  return ({kqq__cirm},), map_vector\n'
    else:
        itsy__xbn += '  in_arr = in_arr_tup[0]\n'
        itsy__xbn += (
            f'  arr_map = {{in_arr[unused]: 0 for unused in range(0)}}\n')
        itsy__xbn += '  map_vector = np.empty(n, np.int64)\n'
        itsy__xbn += '  is_na = 0\n'
        itsy__xbn += '  in_lst = []\n'
        if is_str_arr_type(azmga__xkhtm[0]):
            itsy__xbn += '  total_len = 0\n'
        itsy__xbn += '  for i in range(n):\n'
        itsy__xbn += '    if bodo.libs.array_kernels.isna(in_arr, i):\n'
        itsy__xbn += '      is_na = 1\n'
        itsy__xbn += (
            '      # Always put NA in the last location. We can safely use\n')
        itsy__xbn += (
            '      # -1 because in_arr[-1] == in_arr[len(in_arr) - 1]\n')
        itsy__xbn += '      set_val = -1\n'
        itsy__xbn += '    else:\n'
        itsy__xbn += '      data_val = in_arr[i]\n'
        itsy__xbn += '      if data_val not in arr_map:\n'
        itsy__xbn += '        set_val = len(arr_map)\n'
        itsy__xbn += '        in_lst.append(data_val)\n'
        if is_str_arr_type(azmga__xkhtm[0]):
            itsy__xbn += '        total_len += len(data_val)\n'
        itsy__xbn += '        arr_map[data_val] = len(arr_map)\n'
        itsy__xbn += '      else:\n'
        itsy__xbn += '        set_val = arr_map[data_val]\n'
        itsy__xbn += '    map_vector[i] = set_val\n'
        itsy__xbn += '  n_rows = len(arr_map) + is_na\n'
        if is_str_arr_type(azmga__xkhtm[0]):
            itsy__xbn += """  out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(n_rows, total_len)
"""
        else:
            itsy__xbn += (
                '  out_arr = bodo.utils.utils.alloc_type(n_rows, in_arr, (-1,))\n'
                )
        itsy__xbn += '  for j in range(len(arr_map)):\n'
        itsy__xbn += '    out_arr[j] = in_lst[j]\n'
        itsy__xbn += '  if is_na:\n'
        itsy__xbn += '    bodo.libs.array_kernels.setna(out_arr, n_rows - 1)\n'
        itsy__xbn += f'  return (out_arr,), map_vector\n'
    gswg__glke = {}
    exec(itsy__xbn, {'bodo': bodo, 'np': np}, gswg__glke)
    impl = gswg__glke['impl']
    return impl
