"""
Utility functions for conversion of data such as list to array.
Need to be inlined for better optimization.
"""
import numba
import numpy as np
import pandas as pd
from numba.core import types
from numba.extending import overload
import bodo
from bodo.libs.binary_arr_ext import bytes_type
from bodo.libs.decimal_arr_ext import Decimal128Type, DecimalArrayType
from bodo.utils.indexing import add_nested_counts, init_nested_counts
from bodo.utils.typing import BodoError, decode_if_dict_array, dtype_to_array_type, get_overload_const_list, get_overload_const_str, is_heterogeneous_tuple_type, is_np_arr_typ, is_overload_constant_list, is_overload_constant_str, is_overload_none, is_overload_true, is_str_arr_type, to_nullable_type
NS_DTYPE = np.dtype('M8[ns]')
TD_DTYPE = np.dtype('m8[ns]')


def coerce_to_ndarray(data, error_on_nonarray=True, use_nullable_array=None,
    scalar_to_arr_len=None):
    return data


@overload(coerce_to_ndarray)
def overload_coerce_to_ndarray(data, error_on_nonarray=True,
    use_nullable_array=None, scalar_to_arr_len=None):
    from bodo.hiframes.pd_index_ext import DatetimeIndexType, NumericIndexType, RangeIndexType, TimedeltaIndexType
    from bodo.hiframes.pd_series_ext import SeriesType
    data = types.unliteral(data)
    if isinstance(data, types.Optional) and bodo.utils.typing.is_scalar_type(
        data.type):
        data = data.type
        use_nullable_array = True
    if isinstance(data, bodo.libs.int_arr_ext.IntegerArrayType
        ) and not is_overload_none(use_nullable_array):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: bodo.libs.int_arr_ext.
            get_int_arr_data(data))
    if data == bodo.libs.bool_arr_ext.boolean_array and not is_overload_none(
        use_nullable_array):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: bodo.libs.bool_arr_ext.
            get_bool_arr_data(data))
    if isinstance(data, types.Array):
        if not is_overload_none(use_nullable_array) and isinstance(data.
            dtype, (types.Boolean, types.Integer)):
            if data.dtype == types.bool_:
                if data.layout != 'C':
                    return (lambda data, error_on_nonarray=True,
                        use_nullable_array=None, scalar_to_arr_len=None:
                        bodo.libs.bool_arr_ext.init_bool_array(np.
                        ascontiguousarray(data), np.full(len(data) + 7 >> 3,
                        255, np.uint8)))
                else:
                    return (lambda data, error_on_nonarray=True,
                        use_nullable_array=None, scalar_to_arr_len=None:
                        bodo.libs.bool_arr_ext.init_bool_array(data, np.
                        full(len(data) + 7 >> 3, 255, np.uint8)))
            elif data.layout != 'C':
                return (lambda data, error_on_nonarray=True,
                    use_nullable_array=None, scalar_to_arr_len=None: bodo.
                    libs.int_arr_ext.init_integer_array(np.
                    ascontiguousarray(data), np.full(len(data) + 7 >> 3, 
                    255, np.uint8)))
            else:
                return (lambda data, error_on_nonarray=True,
                    use_nullable_array=None, scalar_to_arr_len=None: bodo.
                    libs.int_arr_ext.init_integer_array(data, np.full(len(
                    data) + 7 >> 3, 255, np.uint8)))
        if data.layout != 'C':
            return (lambda data, error_on_nonarray=True, use_nullable_array
                =None, scalar_to_arr_len=None: np.ascontiguousarray(data))
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: data)
    if isinstance(data, (types.List, types.UniTuple)):
        jbq__ukpg = data.dtype
        if isinstance(jbq__ukpg, types.Optional):
            jbq__ukpg = jbq__ukpg.type
            if bodo.utils.typing.is_scalar_type(jbq__ukpg):
                use_nullable_array = True
        if isinstance(jbq__ukpg, (types.Boolean, types.Integer, Decimal128Type)
            ) or jbq__ukpg in [bodo.hiframes.pd_timestamp_ext.
            pd_timestamp_type, bodo.hiframes.datetime_date_ext.
            datetime_date_type, bodo.hiframes.datetime_timedelta_ext.
            datetime_timedelta_type]:
            wojcn__xsv = dtype_to_array_type(jbq__ukpg)
            if not is_overload_none(use_nullable_array):
                wojcn__xsv = to_nullable_type(wojcn__xsv)

            def impl(data, error_on_nonarray=True, use_nullable_array=None,
                scalar_to_arr_len=None):
                bqv__qxfg = len(data)
                A = bodo.utils.utils.alloc_type(bqv__qxfg, wojcn__xsv, (-1,))
                bodo.utils.utils.tuple_list_to_array(A, data, jbq__ukpg)
                return A
            return impl
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: np.asarray(data))
    if isinstance(data, SeriesType):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: bodo.hiframes.pd_series_ext.
            get_series_data(data))
    if isinstance(data, (NumericIndexType, DatetimeIndexType,
        TimedeltaIndexType)):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: bodo.hiframes.pd_index_ext.
            get_index_data(data))
    if isinstance(data, RangeIndexType):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: np.arange(data._start, data._stop,
            data._step))
    if isinstance(data, types.RangeType):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: np.arange(data.start, data.stop,
            data.step))
    if not is_overload_none(scalar_to_arr_len):
        if isinstance(data, Decimal128Type):
            wqmd__qce = data.precision
            szus__yrd = data.scale

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                bqv__qxfg = scalar_to_arr_len
                A = bodo.libs.decimal_arr_ext.alloc_decimal_array(bqv__qxfg,
                    wqmd__qce, szus__yrd)
                for jqvy__kmwqq in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    A[jqvy__kmwqq] = data
                return A
            return impl_ts
        if data == bodo.hiframes.datetime_datetime_ext.datetime_datetime_type:
            jtr__rvhat = np.dtype('datetime64[ns]')

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                bqv__qxfg = scalar_to_arr_len
                A = np.empty(bqv__qxfg, jtr__rvhat)
                eulf__eio = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(data))
                skj__dtjx = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                    eulf__eio)
                for jqvy__kmwqq in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    A[jqvy__kmwqq] = skj__dtjx
                return A
            return impl_ts
        if (data == bodo.hiframes.datetime_timedelta_ext.
            datetime_timedelta_type):
            bofo__difpo = np.dtype('timedelta64[ns]')

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                bqv__qxfg = scalar_to_arr_len
                A = np.empty(bqv__qxfg, bofo__difpo)
                fqaav__ysu = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(data))
                for jqvy__kmwqq in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    A[jqvy__kmwqq] = fqaav__ysu
                return A
            return impl_ts
        if data == bodo.hiframes.datetime_date_ext.datetime_date_type:

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                bqv__qxfg = scalar_to_arr_len
                A = bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(
                    bqv__qxfg)
                for jqvy__kmwqq in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    A[jqvy__kmwqq] = data
                return A
            return impl_ts
        if data == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            jtr__rvhat = np.dtype('datetime64[ns]')

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                bqv__qxfg = scalar_to_arr_len
                A = np.empty(scalar_to_arr_len, jtr__rvhat)
                eulf__eio = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(data
                    .value)
                for jqvy__kmwqq in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    A[jqvy__kmwqq] = eulf__eio
                return A
            return impl_ts
        dtype = types.unliteral(data)
        if not is_overload_none(use_nullable_array) and isinstance(dtype,
            types.Integer):

            def impl_null_integer(data, error_on_nonarray=True,
                use_nullable_array=None, scalar_to_arr_len=None):
                numba.parfors.parfor.init_prange()
                bqv__qxfg = scalar_to_arr_len
                zkm__nxn = bodo.libs.int_arr_ext.alloc_int_array(bqv__qxfg,
                    dtype)
                for jqvy__kmwqq in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    zkm__nxn[jqvy__kmwqq] = data
                return zkm__nxn
            return impl_null_integer
        if not is_overload_none(use_nullable_array) and dtype == types.bool_:

            def impl_null_bool(data, error_on_nonarray=True,
                use_nullable_array=None, scalar_to_arr_len=None):
                numba.parfors.parfor.init_prange()
                bqv__qxfg = scalar_to_arr_len
                zkm__nxn = bodo.libs.bool_arr_ext.alloc_bool_array(bqv__qxfg)
                for jqvy__kmwqq in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    zkm__nxn[jqvy__kmwqq] = data
                return zkm__nxn
            return impl_null_bool

        def impl_num(data, error_on_nonarray=True, use_nullable_array=None,
            scalar_to_arr_len=None):
            numba.parfors.parfor.init_prange()
            bqv__qxfg = scalar_to_arr_len
            zkm__nxn = np.empty(bqv__qxfg, dtype)
            for jqvy__kmwqq in numba.parfors.parfor.internal_prange(bqv__qxfg):
                zkm__nxn[jqvy__kmwqq] = data
            return zkm__nxn
        return impl_num
    if isinstance(data, types.BaseTuple) and all(isinstance(hbcf__uqun, (
        types.Float, types.Integer)) for hbcf__uqun in data.types):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: np.array(data))
    if bodo.utils.utils.is_array_typ(data, False):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: data)
    if is_overload_true(error_on_nonarray):
        raise BodoError(f'cannot coerce {data} to array')
    return (lambda data, error_on_nonarray=True, use_nullable_array=None,
        scalar_to_arr_len=None: data)


def coerce_to_array(data, error_on_nonarray=True, use_nullable_array=None,
    scalar_to_arr_len=None):
    return data


@overload(coerce_to_array, no_unliteral=True)
def overload_coerce_to_array(data, error_on_nonarray=True,
    use_nullable_array=None, scalar_to_arr_len=None):
    from bodo.hiframes.pd_index_ext import BinaryIndexType, CategoricalIndexType, StringIndexType
    from bodo.hiframes.pd_series_ext import SeriesType
    data = types.unliteral(data)
    if isinstance(data, types.Optional) and bodo.utils.typing.is_scalar_type(
        data.type):
        data = data.type
        use_nullable_array = True
    if isinstance(data, SeriesType):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: bodo.hiframes.pd_series_ext.
            get_series_data(data))
    if isinstance(data, (StringIndexType, BinaryIndexType,
        CategoricalIndexType)):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: bodo.hiframes.pd_index_ext.
            get_index_data(data))
    if isinstance(data, types.List) and data.dtype in (bodo.string_type,
        bodo.bytes_type):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: bodo.libs.str_arr_ext.
            str_arr_from_sequence(data))
    if isinstance(data, types.BaseTuple) and data.count == 0:
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: bodo.libs.str_arr_ext.
            empty_str_arr(data))
    if isinstance(data, types.UniTuple) and isinstance(data.dtype, (types.
        UnicodeType, types.StringLiteral)) or isinstance(data, types.BaseTuple
        ) and all(isinstance(hbcf__uqun, types.StringLiteral) for
        hbcf__uqun in data.types):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: bodo.libs.str_arr_ext.
            str_arr_from_sequence(data))
    if data in (bodo.string_array_type, bodo.dict_str_arr_type, bodo.
        binary_array_type, bodo.libs.bool_arr_ext.boolean_array, bodo.
        hiframes.datetime_date_ext.datetime_date_array_type, bodo.hiframes.
        datetime_timedelta_ext.datetime_timedelta_array_type, bodo.hiframes
        .split_impl.string_array_split_view_type) or isinstance(data, (bodo
        .libs.int_arr_ext.IntegerArrayType, DecimalArrayType, bodo.libs.
        interval_arr_ext.IntervalArrayType, bodo.libs.tuple_arr_ext.
        TupleArrayType, bodo.libs.struct_arr_ext.StructArrayType, bodo.
        hiframes.pd_categorical_ext.CategoricalArrayType, bodo.libs.
        csr_matrix_ext.CSRMatrixType)):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: data)
    if isinstance(data, (types.List, types.UniTuple)) and isinstance(data.
        dtype, types.BaseTuple):
        vxf__innyl = tuple(dtype_to_array_type(hbcf__uqun) for hbcf__uqun in
            data.dtype.types)

        def impl_tuple_list(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            bqv__qxfg = len(data)
            arr = bodo.libs.tuple_arr_ext.pre_alloc_tuple_array(bqv__qxfg,
                (-1,), vxf__innyl)
            for jqvy__kmwqq in range(bqv__qxfg):
                arr[jqvy__kmwqq] = data[jqvy__kmwqq]
            return arr
        return impl_tuple_list
    if isinstance(data, types.List) and (bodo.utils.utils.is_array_typ(data
        .dtype, False) or isinstance(data.dtype, types.List)):
        modef__ofpr = dtype_to_array_type(data.dtype.dtype)

        def impl_array_item_arr(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            bqv__qxfg = len(data)
            vllwv__ciull = init_nested_counts(modef__ofpr)
            for jqvy__kmwqq in range(bqv__qxfg):
                wej__tnwvy = bodo.utils.conversion.coerce_to_array(data[
                    jqvy__kmwqq], use_nullable_array=True)
                vllwv__ciull = add_nested_counts(vllwv__ciull, wej__tnwvy)
            zkm__nxn = bodo.libs.array_item_arr_ext.pre_alloc_array_item_array(
                bqv__qxfg, vllwv__ciull, modef__ofpr)
            yuvxh__bql = bodo.libs.array_item_arr_ext.get_null_bitmap(zkm__nxn)
            for xwkut__zubm in range(bqv__qxfg):
                wej__tnwvy = bodo.utils.conversion.coerce_to_array(data[
                    xwkut__zubm], use_nullable_array=True)
                zkm__nxn[xwkut__zubm] = wej__tnwvy
                bodo.libs.int_arr_ext.set_bit_to_arr(yuvxh__bql, xwkut__zubm, 1
                    )
            return zkm__nxn
        return impl_array_item_arr
    if not is_overload_none(scalar_to_arr_len) and isinstance(data, (types.
        UnicodeType, types.StringLiteral)):

        def impl_str(data, error_on_nonarray=True, use_nullable_array=None,
            scalar_to_arr_len=None):
            bqv__qxfg = scalar_to_arr_len
            A = bodo.libs.str_arr_ext.pre_alloc_string_array(bqv__qxfg, -1)
            for jqvy__kmwqq in numba.parfors.parfor.internal_prange(bqv__qxfg):
                A[jqvy__kmwqq] = data
            return A
        return impl_str
    if isinstance(data, types.List) and data.dtype == bodo.pd_timestamp_type:

        def impl_list_timestamp(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            bqv__qxfg = len(data)
            A = np.empty(bqv__qxfg, np.dtype('datetime64[ns]'))
            for jqvy__kmwqq in range(bqv__qxfg):
                A[jqvy__kmwqq
                    ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(data
                    [jqvy__kmwqq].value)
            return A
        return impl_list_timestamp
    if isinstance(data, types.List) and data.dtype == bodo.pd_timedelta_type:

        def impl_list_timedelta(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            bqv__qxfg = len(data)
            A = np.empty(bqv__qxfg, np.dtype('timedelta64[ns]'))
            for jqvy__kmwqq in range(bqv__qxfg):
                A[jqvy__kmwqq
                    ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                    data[jqvy__kmwqq].value)
            return A
        return impl_list_timedelta
    if not is_overload_none(scalar_to_arr_len) and data in [bodo.
        pd_timestamp_type, bodo.pd_timedelta_type]:
        qtkp__wprj = ('datetime64[ns]' if data == bodo.pd_timestamp_type else
            'timedelta64[ns]')

        def impl_timestamp(data, error_on_nonarray=True, use_nullable_array
            =None, scalar_to_arr_len=None):
            bqv__qxfg = scalar_to_arr_len
            A = np.empty(bqv__qxfg, qtkp__wprj)
            data = bodo.utils.conversion.unbox_if_timestamp(data)
            for jqvy__kmwqq in numba.parfors.parfor.internal_prange(bqv__qxfg):
                A[jqvy__kmwqq] = data
            return A
        return impl_timestamp
    return (lambda data, error_on_nonarray=True, use_nullable_array=None,
        scalar_to_arr_len=None: bodo.utils.conversion.coerce_to_ndarray(
        data, error_on_nonarray, use_nullable_array, scalar_to_arr_len))


def _is_str_dtype(dtype):
    return isinstance(dtype, bodo.libs.str_arr_ext.StringDtype) or isinstance(
        dtype, types.Function) and dtype.key[0
        ] == str or is_overload_constant_str(dtype) and get_overload_const_str(
        dtype) == 'str' or isinstance(dtype, types.TypeRef
        ) and dtype.instance_type == types.unicode_type


def fix_arr_dtype(data, new_dtype, copy=None, nan_to_str=True, from_series=
    False):
    return data


@overload(fix_arr_dtype, no_unliteral=True)
def overload_fix_arr_dtype(data, new_dtype, copy=None, nan_to_str=True,
    from_series=False):
    ctvwi__fso = is_overload_true(copy)
    sifg__ssg = is_overload_constant_str(new_dtype) and get_overload_const_str(
        new_dtype) == 'object'
    if is_overload_none(new_dtype) or sifg__ssg:
        if ctvwi__fso:
            return (lambda data, new_dtype, copy=None, nan_to_str=True,
                from_series=False: data.copy())
        return (lambda data, new_dtype, copy=None, nan_to_str=True,
            from_series=False: data)
    if _is_str_dtype(new_dtype):
        if isinstance(data.dtype, types.Integer):

            def impl_int_str(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                numba.parfors.parfor.init_prange()
                bqv__qxfg = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(bqv__qxfg, -1)
                for wtxzs__enm in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    if bodo.libs.array_kernels.isna(data, wtxzs__enm):
                        if nan_to_str:
                            bodo.libs.str_arr_ext.str_arr_setitem_NA_str(A,
                                wtxzs__enm)
                        else:
                            bodo.libs.array_kernels.setna(A, wtxzs__enm)
                    else:
                        bodo.libs.str_arr_ext.str_arr_setitem_int_to_str(A,
                            wtxzs__enm, data[wtxzs__enm])
                return A
            return impl_int_str
        if data.dtype == bytes_type:

            def impl_binary(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                numba.parfors.parfor.init_prange()
                bqv__qxfg = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(bqv__qxfg, -1)
                for wtxzs__enm in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    if bodo.libs.array_kernels.isna(data, wtxzs__enm):
                        bodo.libs.array_kernels.setna(A, wtxzs__enm)
                    else:
                        A[wtxzs__enm] = ''.join([chr(jugj__xxr) for
                            jugj__xxr in data[wtxzs__enm]])
                return A
            return impl_binary
        if is_overload_true(from_series) and data.dtype in (bodo.
            datetime64ns, bodo.timedelta64ns):

            def impl_str_dt_series(data, new_dtype, copy=None, nan_to_str=
                True, from_series=False):
                numba.parfors.parfor.init_prange()
                bqv__qxfg = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(bqv__qxfg, -1)
                for wtxzs__enm in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    if bodo.libs.array_kernels.isna(data, wtxzs__enm):
                        if nan_to_str:
                            A[wtxzs__enm] = 'NaT'
                        else:
                            bodo.libs.array_kernels.setna(A, wtxzs__enm)
                        continue
                    A[wtxzs__enm] = str(box_if_dt64(data[wtxzs__enm]))
                return A
            return impl_str_dt_series
        else:

            def impl_str_array(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                numba.parfors.parfor.init_prange()
                bqv__qxfg = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(bqv__qxfg, -1)
                for wtxzs__enm in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    if bodo.libs.array_kernels.isna(data, wtxzs__enm):
                        if nan_to_str:
                            A[wtxzs__enm] = 'nan'
                        else:
                            bodo.libs.array_kernels.setna(A, wtxzs__enm)
                        continue
                    A[wtxzs__enm] = str(data[wtxzs__enm])
                return A
            return impl_str_array
    if isinstance(new_dtype, bodo.hiframes.pd_categorical_ext.
        PDCategoricalDtype):

        def impl_cat_dtype(data, new_dtype, copy=None, nan_to_str=True,
            from_series=False):
            bqv__qxfg = len(data)
            numba.parfors.parfor.init_prange()
            iyxo__qxjy = (bodo.hiframes.pd_categorical_ext.
                get_label_dict_from_categories(new_dtype.categories.values))
            A = bodo.hiframes.pd_categorical_ext.alloc_categorical_array(
                bqv__qxfg, new_dtype)
            qxi__jsiq = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A))
            for jqvy__kmwqq in numba.parfors.parfor.internal_prange(bqv__qxfg):
                if bodo.libs.array_kernels.isna(data, jqvy__kmwqq):
                    bodo.libs.array_kernels.setna(A, jqvy__kmwqq)
                    continue
                val = data[jqvy__kmwqq]
                if val not in iyxo__qxjy:
                    bodo.libs.array_kernels.setna(A, jqvy__kmwqq)
                    continue
                qxi__jsiq[jqvy__kmwqq] = iyxo__qxjy[val]
            return A
        return impl_cat_dtype
    if is_overload_constant_str(new_dtype) and get_overload_const_str(new_dtype
        ) == 'category':

        def impl_category(data, new_dtype, copy=None, nan_to_str=True,
            from_series=False):
            ejuw__hsjz = bodo.libs.array_kernels.unique(data, dropna=True)
            ejuw__hsjz = pd.Series(ejuw__hsjz).sort_values().values
            ejuw__hsjz = bodo.allgatherv(ejuw__hsjz, False)
            qrocx__zibf = bodo.hiframes.pd_categorical_ext.init_cat_dtype(bodo
                .utils.conversion.index_from_array(ejuw__hsjz, None), False,
                None, None)
            bqv__qxfg = len(data)
            numba.parfors.parfor.init_prange()
            iyxo__qxjy = (bodo.hiframes.pd_categorical_ext.
                get_label_dict_from_categories_no_duplicates(ejuw__hsjz))
            A = bodo.hiframes.pd_categorical_ext.alloc_categorical_array(
                bqv__qxfg, qrocx__zibf)
            qxi__jsiq = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A))
            for jqvy__kmwqq in numba.parfors.parfor.internal_prange(bqv__qxfg):
                if bodo.libs.array_kernels.isna(data, jqvy__kmwqq):
                    bodo.libs.array_kernels.setna(A, jqvy__kmwqq)
                    continue
                val = data[jqvy__kmwqq]
                qxi__jsiq[jqvy__kmwqq] = iyxo__qxjy[val]
            return A
        return impl_category
    nb_dtype = bodo.utils.typing.parse_dtype(new_dtype)
    if isinstance(data, bodo.libs.int_arr_ext.IntegerArrayType):
        fxi__jyui = isinstance(nb_dtype, bodo.libs.int_arr_ext.IntDtype
            ) and data.dtype == nb_dtype.dtype
    else:
        fxi__jyui = data.dtype == nb_dtype
    if ctvwi__fso and fxi__jyui:
        return (lambda data, new_dtype, copy=None, nan_to_str=True,
            from_series=False: data.copy())
    if fxi__jyui:
        return (lambda data, new_dtype, copy=None, nan_to_str=True,
            from_series=False: data)
    if isinstance(nb_dtype, bodo.libs.int_arr_ext.IntDtype):
        if isinstance(nb_dtype, types.Integer):
            qtkp__wprj = nb_dtype
        else:
            qtkp__wprj = nb_dtype.dtype
        if isinstance(data.dtype, types.Float):

            def impl_float(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                bqv__qxfg = len(data)
                numba.parfors.parfor.init_prange()
                qwja__ljze = bodo.libs.int_arr_ext.alloc_int_array(bqv__qxfg,
                    qtkp__wprj)
                for jqvy__kmwqq in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    if bodo.libs.array_kernels.isna(data, jqvy__kmwqq):
                        bodo.libs.array_kernels.setna(qwja__ljze, jqvy__kmwqq)
                    else:
                        qwja__ljze[jqvy__kmwqq] = int(data[jqvy__kmwqq])
                return qwja__ljze
            return impl_float
        else:
            if data == bodo.dict_str_arr_type:

                def impl_dict(data, new_dtype, copy=None, nan_to_str=True,
                    from_series=False):
                    return bodo.libs.dict_arr_ext.convert_dict_arr_to_int(data,
                        qtkp__wprj)
                return impl_dict

            def impl(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                bqv__qxfg = len(data)
                numba.parfors.parfor.init_prange()
                qwja__ljze = bodo.libs.int_arr_ext.alloc_int_array(bqv__qxfg,
                    qtkp__wprj)
                for jqvy__kmwqq in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    if bodo.libs.array_kernels.isna(data, jqvy__kmwqq):
                        bodo.libs.array_kernels.setna(qwja__ljze, jqvy__kmwqq)
                    else:
                        qwja__ljze[jqvy__kmwqq] = np.int64(data[jqvy__kmwqq])
                return qwja__ljze
            return impl
    if isinstance(nb_dtype, types.Integer) and isinstance(data.dtype, types
        .Integer):

        def impl(data, new_dtype, copy=None, nan_to_str=True, from_series=False
            ):
            return data.astype(nb_dtype)
        return impl
    if nb_dtype == bodo.libs.bool_arr_ext.boolean_dtype:

        def impl_bool(data, new_dtype, copy=None, nan_to_str=True,
            from_series=False):
            bqv__qxfg = len(data)
            numba.parfors.parfor.init_prange()
            qwja__ljze = bodo.libs.bool_arr_ext.alloc_bool_array(bqv__qxfg)
            for jqvy__kmwqq in numba.parfors.parfor.internal_prange(bqv__qxfg):
                if bodo.libs.array_kernels.isna(data, jqvy__kmwqq):
                    bodo.libs.array_kernels.setna(qwja__ljze, jqvy__kmwqq)
                else:
                    qwja__ljze[jqvy__kmwqq] = bool(data[jqvy__kmwqq])
            return qwja__ljze
        return impl_bool
    if nb_dtype == bodo.datetime_date_type:
        if data.dtype == bodo.datetime64ns:

            def impl_date(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                bqv__qxfg = len(data)
                zkm__nxn = (bodo.hiframes.datetime_date_ext.
                    alloc_datetime_date_array(bqv__qxfg))
                for jqvy__kmwqq in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    if bodo.libs.array_kernels.isna(data, jqvy__kmwqq):
                        bodo.libs.array_kernels.setna(zkm__nxn, jqvy__kmwqq)
                    else:
                        zkm__nxn[jqvy__kmwqq
                            ] = bodo.utils.conversion.box_if_dt64(data[
                            jqvy__kmwqq]).date()
                return zkm__nxn
            return impl_date
    if nb_dtype == bodo.datetime64ns:
        if data.dtype == bodo.string_type:

            def impl_str(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                return bodo.hiframes.pd_timestamp_ext.series_str_dt64_astype(
                    data)
            return impl_str
        if data == bodo.datetime_date_array_type:

            def impl_date(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                return (bodo.hiframes.pd_timestamp_ext.
                    datetime_date_arr_to_dt64_arr(data))
            return impl_date
        if isinstance(data.dtype, types.Number) or data.dtype in [bodo.
            timedelta64ns, types.bool_]:

            def impl_numeric(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                bqv__qxfg = len(data)
                numba.parfors.parfor.init_prange()
                zkm__nxn = np.empty(bqv__qxfg, dtype=np.dtype('datetime64[ns]')
                    )
                for jqvy__kmwqq in numba.parfors.parfor.internal_prange(
                    bqv__qxfg):
                    if bodo.libs.array_kernels.isna(data, jqvy__kmwqq):
                        bodo.libs.array_kernels.setna(zkm__nxn, jqvy__kmwqq)
                    else:
                        zkm__nxn[jqvy__kmwqq
                            ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                            np.int64(data[jqvy__kmwqq]))
                return zkm__nxn
            return impl_numeric
    if nb_dtype == bodo.timedelta64ns:
        if data.dtype == bodo.string_type:

            def impl_str(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                return bodo.hiframes.pd_timestamp_ext.series_str_td64_astype(
                    data)
            return impl_str
        if isinstance(data.dtype, types.Number) or data.dtype in [bodo.
            datetime64ns, types.bool_]:
            if ctvwi__fso:

                def impl_numeric(data, new_dtype, copy=None, nan_to_str=
                    True, from_series=False):
                    bqv__qxfg = len(data)
                    numba.parfors.parfor.init_prange()
                    zkm__nxn = np.empty(bqv__qxfg, dtype=np.dtype(
                        'timedelta64[ns]'))
                    for jqvy__kmwqq in numba.parfors.parfor.internal_prange(
                        bqv__qxfg):
                        if bodo.libs.array_kernels.isna(data, jqvy__kmwqq):
                            bodo.libs.array_kernels.setna(zkm__nxn, jqvy__kmwqq
                                )
                        else:
                            zkm__nxn[jqvy__kmwqq] = (bodo.hiframes.
                                pd_timestamp_ext.integer_to_timedelta64(np.
                                int64(data[jqvy__kmwqq])))
                    return zkm__nxn
                return impl_numeric
            else:
                return (lambda data, new_dtype, copy=None, nan_to_str=True,
                    from_series=False: data.view('int64'))
    if nb_dtype == types.int64 and data.dtype in [bodo.datetime64ns, bodo.
        timedelta64ns]:

        def impl_datelike_to_integer(data, new_dtype, copy=None, nan_to_str
            =True, from_series=False):
            bqv__qxfg = len(data)
            numba.parfors.parfor.init_prange()
            A = np.empty(bqv__qxfg, types.int64)
            for jqvy__kmwqq in numba.parfors.parfor.internal_prange(bqv__qxfg):
                if bodo.libs.array_kernels.isna(data, jqvy__kmwqq):
                    bodo.libs.array_kernels.setna(A, jqvy__kmwqq)
                else:
                    A[jqvy__kmwqq] = np.int64(data[jqvy__kmwqq])
            return A
        return impl_datelike_to_integer
    if data.dtype != nb_dtype:
        return (lambda data, new_dtype, copy=None, nan_to_str=True,
            from_series=False: data.astype(nb_dtype))
    raise BodoError(f'Conversion from {data} to {new_dtype} not supported yet')


def array_type_from_dtype(dtype):
    return dtype_to_array_type(bodo.utils.typing.parse_dtype(dtype))


@overload(array_type_from_dtype)
def overload_array_type_from_dtype(dtype):
    arr_type = dtype_to_array_type(bodo.utils.typing.parse_dtype(dtype))
    return lambda dtype: arr_type


@numba.jit
def flatten_array(A):
    ugheb__hrp = []
    bqv__qxfg = len(A)
    for jqvy__kmwqq in range(bqv__qxfg):
        isjvl__wppvo = A[jqvy__kmwqq]
        for hqntf__wln in isjvl__wppvo:
            ugheb__hrp.append(hqntf__wln)
    return bodo.utils.conversion.coerce_to_array(ugheb__hrp)


def parse_datetimes_from_strings(data):
    return data


@overload(parse_datetimes_from_strings, no_unliteral=True)
def overload_parse_datetimes_from_strings(data):
    assert is_str_arr_type(data
        ), 'parse_datetimes_from_strings: string array expected'

    def parse_impl(data):
        numba.parfors.parfor.init_prange()
        bqv__qxfg = len(data)
        gmfcz__yvxy = np.empty(bqv__qxfg, bodo.utils.conversion.NS_DTYPE)
        for jqvy__kmwqq in numba.parfors.parfor.internal_prange(bqv__qxfg):
            gmfcz__yvxy[jqvy__kmwqq
                ] = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(data[
                jqvy__kmwqq])
        return gmfcz__yvxy
    return parse_impl


def convert_to_dt64ns(data):
    return data


@overload(convert_to_dt64ns, no_unliteral=True)
def overload_convert_to_dt64ns(data):
    if data == bodo.hiframes.datetime_date_ext.datetime_date_array_type:
        return (lambda data: bodo.hiframes.pd_timestamp_ext.
            datetime_date_arr_to_dt64_arr(data))
    if is_np_arr_typ(data, types.int64):
        return lambda data: data.view(bodo.utils.conversion.NS_DTYPE)
    if is_np_arr_typ(data, types.NPDatetime('ns')):
        return lambda data: data
    if is_str_arr_type(data):
        return lambda data: bodo.utils.conversion.parse_datetimes_from_strings(
            data)
    raise BodoError(f'invalid data type {data} for dt64 conversion')


def convert_to_td64ns(data):
    return data


@overload(convert_to_td64ns, no_unliteral=True)
def overload_convert_to_td64ns(data):
    if is_np_arr_typ(data, types.int64):
        return lambda data: data.view(bodo.utils.conversion.TD_DTYPE)
    if is_np_arr_typ(data, types.NPTimedelta('ns')):
        return lambda data: data
    if is_str_arr_type(data):
        raise BodoError('conversion to timedelta from string not supported yet'
            )
    raise BodoError(f'invalid data type {data} for timedelta64 conversion')


def convert_to_index(data, name=None):
    return data


@overload(convert_to_index, no_unliteral=True)
def overload_convert_to_index(data, name=None):
    from bodo.hiframes.pd_index_ext import BinaryIndexType, CategoricalIndexType, DatetimeIndexType, NumericIndexType, PeriodIndexType, RangeIndexType, StringIndexType, TimedeltaIndexType
    if isinstance(data, (RangeIndexType, NumericIndexType,
        DatetimeIndexType, TimedeltaIndexType, StringIndexType,
        BinaryIndexType, CategoricalIndexType, PeriodIndexType, types.NoneType)
        ):
        return lambda data, name=None: data

    def impl(data, name=None):
        fmf__mro = bodo.utils.conversion.coerce_to_array(data)
        return bodo.utils.conversion.index_from_array(fmf__mro, name)
    return impl


def force_convert_index(I1, I2):
    return I2


@overload(force_convert_index, no_unliteral=True)
def overload_force_convert_index(I1, I2):
    from bodo.hiframes.pd_index_ext import RangeIndexType
    if isinstance(I2, RangeIndexType):
        return lambda I1, I2: pd.RangeIndex(len(I1._data))
    return lambda I1, I2: I1


def index_from_array(data, name=None):
    return data


@overload(index_from_array, no_unliteral=True)
def overload_index_from_array(data, name=None):
    if data in [bodo.string_array_type, bodo.binary_array_type]:
        return (lambda data, name=None: bodo.hiframes.pd_index_ext.
            init_binary_str_index(data, name))
    if data == bodo.dict_str_arr_type:
        return (lambda data, name=None: bodo.hiframes.pd_index_ext.
            init_binary_str_index(decode_if_dict_array(data), name))
    if (data == bodo.hiframes.datetime_date_ext.datetime_date_array_type or
        data.dtype == types.NPDatetime('ns')):
        return lambda data, name=None: pd.DatetimeIndex(data, name=name)
    if data.dtype == types.NPTimedelta('ns'):
        return lambda data, name=None: pd.TimedeltaIndex(data, name=name)
    if isinstance(data.dtype, (types.Integer, types.Float, types.Boolean)):
        return (lambda data, name=None: bodo.hiframes.pd_index_ext.
            init_numeric_index(data, name))
    if isinstance(data, bodo.libs.interval_arr_ext.IntervalArrayType):
        return (lambda data, name=None: bodo.hiframes.pd_index_ext.
            init_interval_index(data, name))
    if isinstance(data, bodo.hiframes.pd_categorical_ext.CategoricalArrayType):
        return (lambda data, name=None: bodo.hiframes.pd_index_ext.
            init_categorical_index(data, name))
    if isinstance(data, bodo.libs.pd_datetime_arr_ext.DatetimeArrayType):
        return (lambda data, name=None: bodo.hiframes.pd_index_ext.
            init_datetime_index(data, name))
    raise BodoError(f'cannot convert {data} to Index')


def index_to_array(data):
    return data


@overload(index_to_array, no_unliteral=True)
def overload_index_to_array(I):
    from bodo.hiframes.pd_index_ext import RangeIndexType
    if isinstance(I, RangeIndexType):
        return lambda I: np.arange(I._start, I._stop, I._step)
    return lambda I: bodo.hiframes.pd_index_ext.get_index_data(I)


def false_if_none(val):
    return False if val is None else val


@overload(false_if_none, no_unliteral=True)
def overload_false_if_none(val):
    if is_overload_none(val):
        return lambda val: False
    return lambda val: val


def extract_name_if_none(data, name):
    return name


@overload(extract_name_if_none, no_unliteral=True)
def overload_extract_name_if_none(data, name):
    from bodo.hiframes.pd_index_ext import CategoricalIndexType, DatetimeIndexType, NumericIndexType, PeriodIndexType, TimedeltaIndexType
    from bodo.hiframes.pd_series_ext import SeriesType
    if not is_overload_none(name):
        return lambda data, name: name
    if isinstance(data, (NumericIndexType, DatetimeIndexType,
        TimedeltaIndexType, PeriodIndexType, CategoricalIndexType)):
        return lambda data, name: bodo.hiframes.pd_index_ext.get_index_name(
            data)
    if isinstance(data, SeriesType):
        return lambda data, name: bodo.hiframes.pd_series_ext.get_series_name(
            data)
    return lambda data, name: name


def extract_index_if_none(data, index):
    return index


@overload(extract_index_if_none, no_unliteral=True)
def overload_extract_index_if_none(data, index):
    from bodo.hiframes.pd_series_ext import SeriesType
    if not is_overload_none(index):
        return lambda data, index: index
    if isinstance(data, SeriesType):
        return (lambda data, index: bodo.hiframes.pd_series_ext.
            get_series_index(data))
    return lambda data, index: bodo.hiframes.pd_index_ext.init_range_index(
        0, len(data), 1, None)


def box_if_dt64(val):
    return val


@overload(box_if_dt64, no_unliteral=True)
def overload_box_if_dt64(val):
    if val == types.NPDatetime('ns'):
        return (lambda val: bodo.hiframes.pd_timestamp_ext.
            convert_datetime64_to_timestamp(val))
    if val == types.NPTimedelta('ns'):
        return (lambda val: bodo.hiframes.pd_timestamp_ext.
            convert_numpy_timedelta64_to_pd_timedelta(val))
    return lambda val: val


def unbox_if_timestamp(val):
    return val


@overload(unbox_if_timestamp, no_unliteral=True)
def overload_unbox_if_timestamp(val):
    if val == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
        return lambda val: bodo.hiframes.pd_timestamp_ext.integer_to_dt64(val
            .value)
    if val == bodo.hiframes.datetime_datetime_ext.datetime_datetime_type:
        return lambda val: bodo.hiframes.pd_timestamp_ext.integer_to_dt64(pd
            .Timestamp(val).value)
    if val == bodo.hiframes.datetime_timedelta_ext.pd_timedelta_type:
        return (lambda val: bodo.hiframes.pd_timestamp_ext.
            integer_to_timedelta64(val.value))
    if val == types.Optional(bodo.hiframes.pd_timestamp_ext.pd_timestamp_type):

        def impl_optional(val):
            if val is None:
                xruw__irp = None
            else:
                xruw__irp = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(bodo
                    .utils.indexing.unoptional(val).value)
            return xruw__irp
        return impl_optional
    if val == types.Optional(bodo.hiframes.datetime_timedelta_ext.
        pd_timedelta_type):

        def impl_optional_td(val):
            if val is None:
                xruw__irp = None
            else:
                xruw__irp = (bodo.hiframes.pd_timestamp_ext.
                    integer_to_timedelta64(bodo.utils.indexing.unoptional(
                    val).value))
            return xruw__irp
        return impl_optional_td
    return lambda val: val


def to_tuple(val):
    return val


@overload(to_tuple, no_unliteral=True)
def overload_to_tuple(val):
    if not isinstance(val, types.BaseTuple) and is_overload_constant_list(val):
        uuh__vqu = len(val.types if isinstance(val, types.LiteralList) else
            get_overload_const_list(val))
        furm__onubo = 'def f(val):\n'
        sdaup__daa = ','.join(f'val[{jqvy__kmwqq}]' for jqvy__kmwqq in
            range(uuh__vqu))
        furm__onubo += f'  return ({sdaup__daa},)\n'
        mcc__hdg = {}
        exec(furm__onubo, {}, mcc__hdg)
        impl = mcc__hdg['f']
        return impl
    assert isinstance(val, types.BaseTuple), 'tuple type expected'
    return lambda val: val


def get_array_if_series_or_index(data):
    return data


@overload(get_array_if_series_or_index)
def overload_get_array_if_series_or_index(data):
    from bodo.hiframes.pd_series_ext import SeriesType
    if isinstance(data, SeriesType):
        return lambda data: bodo.hiframes.pd_series_ext.get_series_data(data)
    if bodo.hiframes.pd_index_ext.is_pd_index_type(data):
        return lambda data: bodo.utils.conversion.coerce_to_array(data)
    if isinstance(data, bodo.hiframes.pd_index_ext.HeterogeneousIndexType):
        if not is_heterogeneous_tuple_type(data.data):

            def impl(data):
                rsfg__xkoo = bodo.hiframes.pd_index_ext.get_index_data(data)
                return bodo.utils.conversion.coerce_to_array(rsfg__xkoo)
            return impl

        def impl(data):
            return bodo.hiframes.pd_index_ext.get_index_data(data)
        return impl
    return lambda data: data


def extract_index_array(A):
    return np.arange(len(A))


@overload(extract_index_array, no_unliteral=True)
def overload_extract_index_array(A):
    from bodo.hiframes.pd_series_ext import SeriesType
    if isinstance(A, SeriesType):

        def impl(A):
            index = bodo.hiframes.pd_series_ext.get_series_index(A)
            ergx__iamip = bodo.utils.conversion.coerce_to_array(index)
            return ergx__iamip
        return impl
    return lambda A: np.arange(len(A))


def ensure_contig_if_np(arr):
    return np.ascontiguousarray(arr)


@overload(ensure_contig_if_np, no_unliteral=True)
def overload_ensure_contig_if_np(arr):
    if isinstance(arr, types.Array):
        return lambda arr: np.ascontiguousarray(arr)
    return lambda arr: arr


def struct_if_heter_dict(values, names):
    return {rrxcj__fzsfp: eulf__eio for rrxcj__fzsfp, eulf__eio in zip(
        names, values)}


@overload(struct_if_heter_dict, no_unliteral=True)
def overload_struct_if_heter_dict(values, names):
    if not types.is_homogeneous(*values.types):
        return lambda values, names: bodo.libs.struct_arr_ext.init_struct(
            values, names)
    vppi__njq = len(values.types)
    furm__onubo = 'def f(values, names):\n'
    sdaup__daa = ','.join("'{}': values[{}]".format(get_overload_const_str(
        names.types[jqvy__kmwqq]), jqvy__kmwqq) for jqvy__kmwqq in range(
        vppi__njq))
    furm__onubo += '  return {{{}}}\n'.format(sdaup__daa)
    mcc__hdg = {}
    exec(furm__onubo, {}, mcc__hdg)
    impl = mcc__hdg['f']
    return impl
