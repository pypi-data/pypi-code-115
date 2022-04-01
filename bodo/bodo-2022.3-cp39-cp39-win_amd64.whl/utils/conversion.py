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
        tam__yhpk = data.dtype
        if isinstance(tam__yhpk, types.Optional):
            tam__yhpk = tam__yhpk.type
            if bodo.utils.typing.is_scalar_type(tam__yhpk):
                use_nullable_array = True
        if isinstance(tam__yhpk, (types.Boolean, types.Integer, Decimal128Type)
            ) or tam__yhpk in [bodo.hiframes.pd_timestamp_ext.
            pd_timestamp_type, bodo.hiframes.datetime_date_ext.
            datetime_date_type, bodo.hiframes.datetime_timedelta_ext.
            datetime_timedelta_type]:
            ydhc__qgqzy = dtype_to_array_type(tam__yhpk)
            if not is_overload_none(use_nullable_array):
                ydhc__qgqzy = to_nullable_type(ydhc__qgqzy)

            def impl(data, error_on_nonarray=True, use_nullable_array=None,
                scalar_to_arr_len=None):
                vhol__ztr = len(data)
                A = bodo.utils.utils.alloc_type(vhol__ztr, ydhc__qgqzy, (-1,))
                bodo.utils.utils.tuple_list_to_array(A, data, tam__yhpk)
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
            gyn__axbl = data.precision
            syuzt__wns = data.scale

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                vhol__ztr = scalar_to_arr_len
                A = bodo.libs.decimal_arr_ext.alloc_decimal_array(vhol__ztr,
                    gyn__axbl, syuzt__wns)
                for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    A[rbhpg__cqfhn] = data
                return A
            return impl_ts
        if data == bodo.hiframes.datetime_datetime_ext.datetime_datetime_type:
            rfe__itx = np.dtype('datetime64[ns]')

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                vhol__ztr = scalar_to_arr_len
                A = np.empty(vhol__ztr, rfe__itx)
                bkqs__ifc = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(data))
                sqolg__ijtc = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                    bkqs__ifc)
                for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    A[rbhpg__cqfhn] = sqolg__ijtc
                return A
            return impl_ts
        if (data == bodo.hiframes.datetime_timedelta_ext.
            datetime_timedelta_type):
            jvp__jec = np.dtype('timedelta64[ns]')

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                vhol__ztr = scalar_to_arr_len
                A = np.empty(vhol__ztr, jvp__jec)
                ncbvd__hzenh = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(data))
                for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    A[rbhpg__cqfhn] = ncbvd__hzenh
                return A
            return impl_ts
        if data == bodo.hiframes.datetime_date_ext.datetime_date_type:

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                vhol__ztr = scalar_to_arr_len
                A = bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(
                    vhol__ztr)
                for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    A[rbhpg__cqfhn] = data
                return A
            return impl_ts
        if data == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            rfe__itx = np.dtype('datetime64[ns]')

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                vhol__ztr = scalar_to_arr_len
                A = np.empty(scalar_to_arr_len, rfe__itx)
                bkqs__ifc = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(data
                    .value)
                for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    A[rbhpg__cqfhn] = bkqs__ifc
                return A
            return impl_ts
        dtype = types.unliteral(data)
        if not is_overload_none(use_nullable_array) and isinstance(dtype,
            types.Integer):

            def impl_null_integer(data, error_on_nonarray=True,
                use_nullable_array=None, scalar_to_arr_len=None):
                numba.parfors.parfor.init_prange()
                vhol__ztr = scalar_to_arr_len
                efrum__exv = bodo.libs.int_arr_ext.alloc_int_array(vhol__ztr,
                    dtype)
                for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    efrum__exv[rbhpg__cqfhn] = data
                return efrum__exv
            return impl_null_integer
        if not is_overload_none(use_nullable_array) and dtype == types.bool_:

            def impl_null_bool(data, error_on_nonarray=True,
                use_nullable_array=None, scalar_to_arr_len=None):
                numba.parfors.parfor.init_prange()
                vhol__ztr = scalar_to_arr_len
                efrum__exv = bodo.libs.bool_arr_ext.alloc_bool_array(vhol__ztr)
                for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    efrum__exv[rbhpg__cqfhn] = data
                return efrum__exv
            return impl_null_bool

        def impl_num(data, error_on_nonarray=True, use_nullable_array=None,
            scalar_to_arr_len=None):
            numba.parfors.parfor.init_prange()
            vhol__ztr = scalar_to_arr_len
            efrum__exv = np.empty(vhol__ztr, dtype)
            for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(vhol__ztr
                ):
                efrum__exv[rbhpg__cqfhn] = data
            return efrum__exv
        return impl_num
    if isinstance(data, types.BaseTuple) and all(isinstance(couzi__rhc, (
        types.Float, types.Integer)) for couzi__rhc in data.types):
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
        ) and all(isinstance(couzi__rhc, types.StringLiteral) for
        couzi__rhc in data.types):
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
        csr_matrix_ext.CSRMatrixType, bodo.DatetimeArrayType)):
        return (lambda data, error_on_nonarray=True, use_nullable_array=
            None, scalar_to_arr_len=None: data)
    if isinstance(data, (types.List, types.UniTuple)) and isinstance(data.
        dtype, types.BaseTuple):
        cain__ijjam = tuple(dtype_to_array_type(couzi__rhc) for couzi__rhc in
            data.dtype.types)

        def impl_tuple_list(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            vhol__ztr = len(data)
            arr = bodo.libs.tuple_arr_ext.pre_alloc_tuple_array(vhol__ztr,
                (-1,), cain__ijjam)
            for rbhpg__cqfhn in range(vhol__ztr):
                arr[rbhpg__cqfhn] = data[rbhpg__cqfhn]
            return arr
        return impl_tuple_list
    if isinstance(data, types.List) and (bodo.utils.utils.is_array_typ(data
        .dtype, False) or isinstance(data.dtype, types.List)):
        marn__hzq = dtype_to_array_type(data.dtype.dtype)

        def impl_array_item_arr(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            vhol__ztr = len(data)
            vlxl__drlf = init_nested_counts(marn__hzq)
            for rbhpg__cqfhn in range(vhol__ztr):
                crrb__yvma = bodo.utils.conversion.coerce_to_array(data[
                    rbhpg__cqfhn], use_nullable_array=True)
                vlxl__drlf = add_nested_counts(vlxl__drlf, crrb__yvma)
            efrum__exv = (bodo.libs.array_item_arr_ext.
                pre_alloc_array_item_array(vhol__ztr, vlxl__drlf, marn__hzq))
            tarwd__vgcs = bodo.libs.array_item_arr_ext.get_null_bitmap(
                efrum__exv)
            for qvm__ffpi in range(vhol__ztr):
                crrb__yvma = bodo.utils.conversion.coerce_to_array(data[
                    qvm__ffpi], use_nullable_array=True)
                efrum__exv[qvm__ffpi] = crrb__yvma
                bodo.libs.int_arr_ext.set_bit_to_arr(tarwd__vgcs, qvm__ffpi, 1)
            return efrum__exv
        return impl_array_item_arr
    if not is_overload_none(scalar_to_arr_len) and isinstance(data, (types.
        UnicodeType, types.StringLiteral)):

        def impl_str(data, error_on_nonarray=True, use_nullable_array=None,
            scalar_to_arr_len=None):
            vhol__ztr = scalar_to_arr_len
            A = bodo.libs.str_arr_ext.pre_alloc_string_array(vhol__ztr, -1)
            for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(vhol__ztr
                ):
                A[rbhpg__cqfhn] = data
            return A
        return impl_str
    if isinstance(data, types.List) and isinstance(data.dtype, bodo.
        hiframes.pd_timestamp_ext.PandasTimestampType):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
            'coerce_to_array()')

        def impl_list_timestamp(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            vhol__ztr = len(data)
            A = np.empty(vhol__ztr, np.dtype('datetime64[ns]'))
            for rbhpg__cqfhn in range(vhol__ztr):
                A[rbhpg__cqfhn
                    ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(data
                    [rbhpg__cqfhn].value)
            return A
        return impl_list_timestamp
    if isinstance(data, types.List) and data.dtype == bodo.pd_timedelta_type:

        def impl_list_timedelta(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            vhol__ztr = len(data)
            A = np.empty(vhol__ztr, np.dtype('timedelta64[ns]'))
            for rbhpg__cqfhn in range(vhol__ztr):
                A[rbhpg__cqfhn
                    ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                    data[rbhpg__cqfhn].value)
            return A
        return impl_list_timedelta
    if isinstance(data, bodo.hiframes.pd_timestamp_ext.PandasTimestampType):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
            'coerce_to_array()')
    if not is_overload_none(scalar_to_arr_len) and data in [bodo.
        pd_timestamp_type, bodo.pd_timedelta_type]:
        ybksp__ozv = ('datetime64[ns]' if data == bodo.pd_timestamp_type else
            'timedelta64[ns]')

        def impl_timestamp(data, error_on_nonarray=True, use_nullable_array
            =None, scalar_to_arr_len=None):
            vhol__ztr = scalar_to_arr_len
            A = np.empty(vhol__ztr, ybksp__ozv)
            data = bodo.utils.conversion.unbox_if_timestamp(data)
            for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(vhol__ztr
                ):
                A[rbhpg__cqfhn] = data
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
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
        'fix_arr_dtype()')
    qtkf__woww = is_overload_true(copy)
    pcivx__hbef = is_overload_constant_str(new_dtype
        ) and get_overload_const_str(new_dtype) == 'object'
    if is_overload_none(new_dtype) or pcivx__hbef:
        if qtkf__woww:
            return (lambda data, new_dtype, copy=None, nan_to_str=True,
                from_series=False: data.copy())
        return (lambda data, new_dtype, copy=None, nan_to_str=True,
            from_series=False: data)
    if _is_str_dtype(new_dtype):
        if isinstance(data.dtype, types.Integer):

            def impl_int_str(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                numba.parfors.parfor.init_prange()
                vhol__ztr = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(vhol__ztr, -1)
                for bxkaw__lgsg in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    if bodo.libs.array_kernels.isna(data, bxkaw__lgsg):
                        if nan_to_str:
                            bodo.libs.str_arr_ext.str_arr_setitem_NA_str(A,
                                bxkaw__lgsg)
                        else:
                            bodo.libs.array_kernels.setna(A, bxkaw__lgsg)
                    else:
                        bodo.libs.str_arr_ext.str_arr_setitem_int_to_str(A,
                            bxkaw__lgsg, data[bxkaw__lgsg])
                return A
            return impl_int_str
        if data.dtype == bytes_type:

            def impl_binary(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                numba.parfors.parfor.init_prange()
                vhol__ztr = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(vhol__ztr, -1)
                for bxkaw__lgsg in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    if bodo.libs.array_kernels.isna(data, bxkaw__lgsg):
                        bodo.libs.array_kernels.setna(A, bxkaw__lgsg)
                    else:
                        A[bxkaw__lgsg] = ''.join([chr(blqmn__gxudq) for
                            blqmn__gxudq in data[bxkaw__lgsg]])
                return A
            return impl_binary
        if is_overload_true(from_series) and data.dtype in (bodo.
            datetime64ns, bodo.timedelta64ns):

            def impl_str_dt_series(data, new_dtype, copy=None, nan_to_str=
                True, from_series=False):
                numba.parfors.parfor.init_prange()
                vhol__ztr = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(vhol__ztr, -1)
                for bxkaw__lgsg in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    if bodo.libs.array_kernels.isna(data, bxkaw__lgsg):
                        if nan_to_str:
                            A[bxkaw__lgsg] = 'NaT'
                        else:
                            bodo.libs.array_kernels.setna(A, bxkaw__lgsg)
                        continue
                    A[bxkaw__lgsg] = str(box_if_dt64(data[bxkaw__lgsg]))
                return A
            return impl_str_dt_series
        else:

            def impl_str_array(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                numba.parfors.parfor.init_prange()
                vhol__ztr = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(vhol__ztr, -1)
                for bxkaw__lgsg in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    if bodo.libs.array_kernels.isna(data, bxkaw__lgsg):
                        if nan_to_str:
                            A[bxkaw__lgsg] = 'nan'
                        else:
                            bodo.libs.array_kernels.setna(A, bxkaw__lgsg)
                        continue
                    A[bxkaw__lgsg] = str(data[bxkaw__lgsg])
                return A
            return impl_str_array
    if isinstance(new_dtype, bodo.hiframes.pd_categorical_ext.
        PDCategoricalDtype):

        def impl_cat_dtype(data, new_dtype, copy=None, nan_to_str=True,
            from_series=False):
            vhol__ztr = len(data)
            numba.parfors.parfor.init_prange()
            awgu__xjnc = (bodo.hiframes.pd_categorical_ext.
                get_label_dict_from_categories(new_dtype.categories.values))
            A = bodo.hiframes.pd_categorical_ext.alloc_categorical_array(
                vhol__ztr, new_dtype)
            fwvt__term = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A))
            for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(vhol__ztr
                ):
                if bodo.libs.array_kernels.isna(data, rbhpg__cqfhn):
                    bodo.libs.array_kernels.setna(A, rbhpg__cqfhn)
                    continue
                val = data[rbhpg__cqfhn]
                if val not in awgu__xjnc:
                    bodo.libs.array_kernels.setna(A, rbhpg__cqfhn)
                    continue
                fwvt__term[rbhpg__cqfhn] = awgu__xjnc[val]
            return A
        return impl_cat_dtype
    if is_overload_constant_str(new_dtype) and get_overload_const_str(new_dtype
        ) == 'category':

        def impl_category(data, new_dtype, copy=None, nan_to_str=True,
            from_series=False):
            gypa__aeyyo = bodo.libs.array_kernels.unique(data, dropna=True)
            gypa__aeyyo = pd.Series(gypa__aeyyo).sort_values().values
            gypa__aeyyo = bodo.allgatherv(gypa__aeyyo, False)
            fozv__arrar = bodo.hiframes.pd_categorical_ext.init_cat_dtype(bodo
                .utils.conversion.index_from_array(gypa__aeyyo, None), 
                False, None, None)
            vhol__ztr = len(data)
            numba.parfors.parfor.init_prange()
            awgu__xjnc = (bodo.hiframes.pd_categorical_ext.
                get_label_dict_from_categories_no_duplicates(gypa__aeyyo))
            A = bodo.hiframes.pd_categorical_ext.alloc_categorical_array(
                vhol__ztr, fozv__arrar)
            fwvt__term = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A))
            for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(vhol__ztr
                ):
                if bodo.libs.array_kernels.isna(data, rbhpg__cqfhn):
                    bodo.libs.array_kernels.setna(A, rbhpg__cqfhn)
                    continue
                val = data[rbhpg__cqfhn]
                fwvt__term[rbhpg__cqfhn] = awgu__xjnc[val]
            return A
        return impl_category
    nb_dtype = bodo.utils.typing.parse_dtype(new_dtype)
    if isinstance(data, bodo.libs.int_arr_ext.IntegerArrayType):
        xaueu__wkc = isinstance(nb_dtype, bodo.libs.int_arr_ext.IntDtype
            ) and data.dtype == nb_dtype.dtype
    else:
        xaueu__wkc = data.dtype == nb_dtype
    if qtkf__woww and xaueu__wkc:
        return (lambda data, new_dtype, copy=None, nan_to_str=True,
            from_series=False: data.copy())
    if xaueu__wkc:
        return (lambda data, new_dtype, copy=None, nan_to_str=True,
            from_series=False: data)
    if isinstance(nb_dtype, bodo.libs.int_arr_ext.IntDtype):
        if isinstance(nb_dtype, types.Integer):
            ybksp__ozv = nb_dtype
        else:
            ybksp__ozv = nb_dtype.dtype
        if isinstance(data.dtype, types.Float):

            def impl_float(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                vhol__ztr = len(data)
                numba.parfors.parfor.init_prange()
                mry__qzudy = bodo.libs.int_arr_ext.alloc_int_array(vhol__ztr,
                    ybksp__ozv)
                for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    if bodo.libs.array_kernels.isna(data, rbhpg__cqfhn):
                        bodo.libs.array_kernels.setna(mry__qzudy, rbhpg__cqfhn)
                    else:
                        mry__qzudy[rbhpg__cqfhn] = int(data[rbhpg__cqfhn])
                return mry__qzudy
            return impl_float
        else:
            if data == bodo.dict_str_arr_type:

                def impl_dict(data, new_dtype, copy=None, nan_to_str=True,
                    from_series=False):
                    return bodo.libs.dict_arr_ext.convert_dict_arr_to_int(data,
                        ybksp__ozv)
                return impl_dict

            def impl(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                vhol__ztr = len(data)
                numba.parfors.parfor.init_prange()
                mry__qzudy = bodo.libs.int_arr_ext.alloc_int_array(vhol__ztr,
                    ybksp__ozv)
                for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    if bodo.libs.array_kernels.isna(data, rbhpg__cqfhn):
                        bodo.libs.array_kernels.setna(mry__qzudy, rbhpg__cqfhn)
                    else:
                        mry__qzudy[rbhpg__cqfhn] = np.int64(data[rbhpg__cqfhn])
                return mry__qzudy
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
            vhol__ztr = len(data)
            numba.parfors.parfor.init_prange()
            mry__qzudy = bodo.libs.bool_arr_ext.alloc_bool_array(vhol__ztr)
            for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(vhol__ztr
                ):
                if bodo.libs.array_kernels.isna(data, rbhpg__cqfhn):
                    bodo.libs.array_kernels.setna(mry__qzudy, rbhpg__cqfhn)
                else:
                    mry__qzudy[rbhpg__cqfhn] = bool(data[rbhpg__cqfhn])
            return mry__qzudy
        return impl_bool
    if nb_dtype == bodo.datetime_date_type:
        if data.dtype == bodo.datetime64ns:

            def impl_date(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                vhol__ztr = len(data)
                efrum__exv = (bodo.hiframes.datetime_date_ext.
                    alloc_datetime_date_array(vhol__ztr))
                for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    if bodo.libs.array_kernels.isna(data, rbhpg__cqfhn):
                        bodo.libs.array_kernels.setna(efrum__exv, rbhpg__cqfhn)
                    else:
                        efrum__exv[rbhpg__cqfhn
                            ] = bodo.utils.conversion.box_if_dt64(data[
                            rbhpg__cqfhn]).date()
                return efrum__exv
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
                vhol__ztr = len(data)
                numba.parfors.parfor.init_prange()
                efrum__exv = np.empty(vhol__ztr, dtype=np.dtype(
                    'datetime64[ns]'))
                for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(
                    vhol__ztr):
                    if bodo.libs.array_kernels.isna(data, rbhpg__cqfhn):
                        bodo.libs.array_kernels.setna(efrum__exv, rbhpg__cqfhn)
                    else:
                        efrum__exv[rbhpg__cqfhn
                            ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                            np.int64(data[rbhpg__cqfhn]))
                return efrum__exv
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
            if qtkf__woww:

                def impl_numeric(data, new_dtype, copy=None, nan_to_str=
                    True, from_series=False):
                    vhol__ztr = len(data)
                    numba.parfors.parfor.init_prange()
                    efrum__exv = np.empty(vhol__ztr, dtype=np.dtype(
                        'timedelta64[ns]'))
                    for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(
                        vhol__ztr):
                        if bodo.libs.array_kernels.isna(data, rbhpg__cqfhn):
                            bodo.libs.array_kernels.setna(efrum__exv,
                                rbhpg__cqfhn)
                        else:
                            efrum__exv[rbhpg__cqfhn] = (bodo.hiframes.
                                pd_timestamp_ext.integer_to_timedelta64(np.
                                int64(data[rbhpg__cqfhn])))
                    return efrum__exv
                return impl_numeric
            else:
                return (lambda data, new_dtype, copy=None, nan_to_str=True,
                    from_series=False: data.view('int64'))
    if nb_dtype == types.int64 and data.dtype in [bodo.datetime64ns, bodo.
        timedelta64ns]:

        def impl_datelike_to_integer(data, new_dtype, copy=None, nan_to_str
            =True, from_series=False):
            vhol__ztr = len(data)
            numba.parfors.parfor.init_prange()
            A = np.empty(vhol__ztr, types.int64)
            for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(vhol__ztr
                ):
                if bodo.libs.array_kernels.isna(data, rbhpg__cqfhn):
                    bodo.libs.array_kernels.setna(A, rbhpg__cqfhn)
                else:
                    A[rbhpg__cqfhn] = np.int64(data[rbhpg__cqfhn])
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
    mxv__ifp = []
    vhol__ztr = len(A)
    for rbhpg__cqfhn in range(vhol__ztr):
        qrzn__odizw = A[rbhpg__cqfhn]
        for wez__joleg in qrzn__odizw:
            mxv__ifp.append(wez__joleg)
    return bodo.utils.conversion.coerce_to_array(mxv__ifp)


def parse_datetimes_from_strings(data):
    return data


@overload(parse_datetimes_from_strings, no_unliteral=True)
def overload_parse_datetimes_from_strings(data):
    assert is_str_arr_type(data
        ), 'parse_datetimes_from_strings: string array expected'

    def parse_impl(data):
        numba.parfors.parfor.init_prange()
        vhol__ztr = len(data)
        xffqx__isegk = np.empty(vhol__ztr, bodo.utils.conversion.NS_DTYPE)
        for rbhpg__cqfhn in numba.parfors.parfor.internal_prange(vhol__ztr):
            xffqx__isegk[rbhpg__cqfhn
                ] = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(data[
                rbhpg__cqfhn])
        return xffqx__isegk
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
        vmfr__rwwd = bodo.utils.conversion.coerce_to_array(data)
        return bodo.utils.conversion.index_from_array(vmfr__rwwd, name)
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
                vvn__mhqv = None
            else:
                vvn__mhqv = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(bodo
                    .utils.indexing.unoptional(val).value)
            return vvn__mhqv
        return impl_optional
    if val == types.Optional(bodo.hiframes.datetime_timedelta_ext.
        pd_timedelta_type):

        def impl_optional_td(val):
            if val is None:
                vvn__mhqv = None
            else:
                vvn__mhqv = (bodo.hiframes.pd_timestamp_ext.
                    integer_to_timedelta64(bodo.utils.indexing.unoptional(
                    val).value))
            return vvn__mhqv
        return impl_optional_td
    return lambda val: val


def to_tuple(val):
    return val


@overload(to_tuple, no_unliteral=True)
def overload_to_tuple(val):
    if not isinstance(val, types.BaseTuple) and is_overload_constant_list(val):
        qyugy__hbe = len(val.types if isinstance(val, types.LiteralList) else
            get_overload_const_list(val))
        tfzm__pgfb = 'def f(val):\n'
        ydun__aqvoz = ','.join(f'val[{rbhpg__cqfhn}]' for rbhpg__cqfhn in
            range(qyugy__hbe))
        tfzm__pgfb += f'  return ({ydun__aqvoz},)\n'
        wwqau__erde = {}
        exec(tfzm__pgfb, {}, wwqau__erde)
        impl = wwqau__erde['f']
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
                qso__jps = bodo.hiframes.pd_index_ext.get_index_data(data)
                return bodo.utils.conversion.coerce_to_array(qso__jps)
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
            qpgpt__vztf = bodo.utils.conversion.coerce_to_array(index)
            return qpgpt__vztf
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
    return {bsuh__rxp: bkqs__ifc for bsuh__rxp, bkqs__ifc in zip(names, values)
        }


@overload(struct_if_heter_dict, no_unliteral=True)
def overload_struct_if_heter_dict(values, names):
    if not types.is_homogeneous(*values.types):
        return lambda values, names: bodo.libs.struct_arr_ext.init_struct(
            values, names)
    ciwu__pnk = len(values.types)
    tfzm__pgfb = 'def f(values, names):\n'
    ydun__aqvoz = ','.join("'{}': values[{}]".format(get_overload_const_str
        (names.types[rbhpg__cqfhn]), rbhpg__cqfhn) for rbhpg__cqfhn in
        range(ciwu__pnk))
    tfzm__pgfb += '  return {{{}}}\n'.format(ydun__aqvoz)
    wwqau__erde = {}
    exec(tfzm__pgfb, {}, wwqau__erde)
    impl = wwqau__erde['f']
    return impl
