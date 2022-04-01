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
        fql__rnghk = data.dtype
        if isinstance(fql__rnghk, types.Optional):
            fql__rnghk = fql__rnghk.type
            if bodo.utils.typing.is_scalar_type(fql__rnghk):
                use_nullable_array = True
        if isinstance(fql__rnghk, (types.Boolean, types.Integer,
            Decimal128Type)) or fql__rnghk in [bodo.hiframes.
            pd_timestamp_ext.pd_timestamp_type, bodo.hiframes.
            datetime_date_ext.datetime_date_type, bodo.hiframes.
            datetime_timedelta_ext.datetime_timedelta_type]:
            mtb__mzdvt = dtype_to_array_type(fql__rnghk)
            if not is_overload_none(use_nullable_array):
                mtb__mzdvt = to_nullable_type(mtb__mzdvt)

            def impl(data, error_on_nonarray=True, use_nullable_array=None,
                scalar_to_arr_len=None):
                saiwn__zsb = len(data)
                A = bodo.utils.utils.alloc_type(saiwn__zsb, mtb__mzdvt, (-1,))
                bodo.utils.utils.tuple_list_to_array(A, data, fql__rnghk)
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
            okag__sybui = data.precision
            bmekr__ikwdf = data.scale

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                saiwn__zsb = scalar_to_arr_len
                A = bodo.libs.decimal_arr_ext.alloc_decimal_array(saiwn__zsb,
                    okag__sybui, bmekr__ikwdf)
                for dofm__odrd in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    A[dofm__odrd] = data
                return A
            return impl_ts
        if data == bodo.hiframes.datetime_datetime_ext.datetime_datetime_type:
            ohvmq__uuv = np.dtype('datetime64[ns]')

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                saiwn__zsb = scalar_to_arr_len
                A = np.empty(saiwn__zsb, ohvmq__uuv)
                qhfk__jbm = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(data))
                tcj__wclsj = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                    qhfk__jbm)
                for dofm__odrd in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    A[dofm__odrd] = tcj__wclsj
                return A
            return impl_ts
        if (data == bodo.hiframes.datetime_timedelta_ext.
            datetime_timedelta_type):
            baz__aio = np.dtype('timedelta64[ns]')

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                saiwn__zsb = scalar_to_arr_len
                A = np.empty(saiwn__zsb, baz__aio)
                afdp__jucy = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(data))
                for dofm__odrd in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    A[dofm__odrd] = afdp__jucy
                return A
            return impl_ts
        if data == bodo.hiframes.datetime_date_ext.datetime_date_type:

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                saiwn__zsb = scalar_to_arr_len
                A = bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(
                    saiwn__zsb)
                for dofm__odrd in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    A[dofm__odrd] = data
                return A
            return impl_ts
        if data == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            ohvmq__uuv = np.dtype('datetime64[ns]')

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                saiwn__zsb = scalar_to_arr_len
                A = np.empty(scalar_to_arr_len, ohvmq__uuv)
                qhfk__jbm = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(data
                    .value)
                for dofm__odrd in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    A[dofm__odrd] = qhfk__jbm
                return A
            return impl_ts
        dtype = types.unliteral(data)
        if not is_overload_none(use_nullable_array) and isinstance(dtype,
            types.Integer):

            def impl_null_integer(data, error_on_nonarray=True,
                use_nullable_array=None, scalar_to_arr_len=None):
                numba.parfors.parfor.init_prange()
                saiwn__zsb = scalar_to_arr_len
                llfwz__uud = bodo.libs.int_arr_ext.alloc_int_array(saiwn__zsb,
                    dtype)
                for dofm__odrd in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    llfwz__uud[dofm__odrd] = data
                return llfwz__uud
            return impl_null_integer
        if not is_overload_none(use_nullable_array) and dtype == types.bool_:

            def impl_null_bool(data, error_on_nonarray=True,
                use_nullable_array=None, scalar_to_arr_len=None):
                numba.parfors.parfor.init_prange()
                saiwn__zsb = scalar_to_arr_len
                llfwz__uud = bodo.libs.bool_arr_ext.alloc_bool_array(saiwn__zsb
                    )
                for dofm__odrd in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    llfwz__uud[dofm__odrd] = data
                return llfwz__uud
            return impl_null_bool

        def impl_num(data, error_on_nonarray=True, use_nullable_array=None,
            scalar_to_arr_len=None):
            numba.parfors.parfor.init_prange()
            saiwn__zsb = scalar_to_arr_len
            llfwz__uud = np.empty(saiwn__zsb, dtype)
            for dofm__odrd in numba.parfors.parfor.internal_prange(saiwn__zsb):
                llfwz__uud[dofm__odrd] = data
            return llfwz__uud
        return impl_num
    if isinstance(data, types.BaseTuple) and all(isinstance(drap__iuu, (
        types.Float, types.Integer)) for drap__iuu in data.types):
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
        ) and all(isinstance(drap__iuu, types.StringLiteral) for drap__iuu in
        data.types):
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
        iriqn__onpt = tuple(dtype_to_array_type(drap__iuu) for drap__iuu in
            data.dtype.types)

        def impl_tuple_list(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            saiwn__zsb = len(data)
            arr = bodo.libs.tuple_arr_ext.pre_alloc_tuple_array(saiwn__zsb,
                (-1,), iriqn__onpt)
            for dofm__odrd in range(saiwn__zsb):
                arr[dofm__odrd] = data[dofm__odrd]
            return arr
        return impl_tuple_list
    if isinstance(data, types.List) and (bodo.utils.utils.is_array_typ(data
        .dtype, False) or isinstance(data.dtype, types.List)):
        xuoy__xqfa = dtype_to_array_type(data.dtype.dtype)

        def impl_array_item_arr(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            saiwn__zsb = len(data)
            tqp__vcrbn = init_nested_counts(xuoy__xqfa)
            for dofm__odrd in range(saiwn__zsb):
                fztk__nex = bodo.utils.conversion.coerce_to_array(data[
                    dofm__odrd], use_nullable_array=True)
                tqp__vcrbn = add_nested_counts(tqp__vcrbn, fztk__nex)
            llfwz__uud = (bodo.libs.array_item_arr_ext.
                pre_alloc_array_item_array(saiwn__zsb, tqp__vcrbn, xuoy__xqfa))
            gtl__bjhp = bodo.libs.array_item_arr_ext.get_null_bitmap(llfwz__uud
                )
            for brbe__jgs in range(saiwn__zsb):
                fztk__nex = bodo.utils.conversion.coerce_to_array(data[
                    brbe__jgs], use_nullable_array=True)
                llfwz__uud[brbe__jgs] = fztk__nex
                bodo.libs.int_arr_ext.set_bit_to_arr(gtl__bjhp, brbe__jgs, 1)
            return llfwz__uud
        return impl_array_item_arr
    if not is_overload_none(scalar_to_arr_len) and isinstance(data, (types.
        UnicodeType, types.StringLiteral)):

        def impl_str(data, error_on_nonarray=True, use_nullable_array=None,
            scalar_to_arr_len=None):
            saiwn__zsb = scalar_to_arr_len
            A = bodo.libs.str_arr_ext.pre_alloc_string_array(saiwn__zsb, -1)
            for dofm__odrd in numba.parfors.parfor.internal_prange(saiwn__zsb):
                A[dofm__odrd] = data
            return A
        return impl_str
    if isinstance(data, types.List) and isinstance(data.dtype, bodo.
        hiframes.pd_timestamp_ext.PandasTimestampType):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
            'coerce_to_array()')

        def impl_list_timestamp(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            saiwn__zsb = len(data)
            A = np.empty(saiwn__zsb, np.dtype('datetime64[ns]'))
            for dofm__odrd in range(saiwn__zsb):
                A[dofm__odrd] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                    data[dofm__odrd].value)
            return A
        return impl_list_timestamp
    if isinstance(data, types.List) and data.dtype == bodo.pd_timedelta_type:

        def impl_list_timedelta(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            saiwn__zsb = len(data)
            A = np.empty(saiwn__zsb, np.dtype('timedelta64[ns]'))
            for dofm__odrd in range(saiwn__zsb):
                A[dofm__odrd
                    ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                    data[dofm__odrd].value)
            return A
        return impl_list_timedelta
    if isinstance(data, bodo.hiframes.pd_timestamp_ext.PandasTimestampType):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
            'coerce_to_array()')
    if not is_overload_none(scalar_to_arr_len) and data in [bodo.
        pd_timestamp_type, bodo.pd_timedelta_type]:
        owfxl__dhaw = ('datetime64[ns]' if data == bodo.pd_timestamp_type else
            'timedelta64[ns]')

        def impl_timestamp(data, error_on_nonarray=True, use_nullable_array
            =None, scalar_to_arr_len=None):
            saiwn__zsb = scalar_to_arr_len
            A = np.empty(saiwn__zsb, owfxl__dhaw)
            data = bodo.utils.conversion.unbox_if_timestamp(data)
            for dofm__odrd in numba.parfors.parfor.internal_prange(saiwn__zsb):
                A[dofm__odrd] = data
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
    ovgi__kcykq = is_overload_true(copy)
    nyxcu__ufnc = is_overload_constant_str(new_dtype
        ) and get_overload_const_str(new_dtype) == 'object'
    if is_overload_none(new_dtype) or nyxcu__ufnc:
        if ovgi__kcykq:
            return (lambda data, new_dtype, copy=None, nan_to_str=True,
                from_series=False: data.copy())
        return (lambda data, new_dtype, copy=None, nan_to_str=True,
            from_series=False: data)
    if _is_str_dtype(new_dtype):
        if isinstance(data.dtype, types.Integer):

            def impl_int_str(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                numba.parfors.parfor.init_prange()
                saiwn__zsb = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(saiwn__zsb, -1
                    )
                for atq__aizif in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    if bodo.libs.array_kernels.isna(data, atq__aizif):
                        if nan_to_str:
                            bodo.libs.str_arr_ext.str_arr_setitem_NA_str(A,
                                atq__aizif)
                        else:
                            bodo.libs.array_kernels.setna(A, atq__aizif)
                    else:
                        bodo.libs.str_arr_ext.str_arr_setitem_int_to_str(A,
                            atq__aizif, data[atq__aizif])
                return A
            return impl_int_str
        if data.dtype == bytes_type:

            def impl_binary(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                numba.parfors.parfor.init_prange()
                saiwn__zsb = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(saiwn__zsb, -1
                    )
                for atq__aizif in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    if bodo.libs.array_kernels.isna(data, atq__aizif):
                        bodo.libs.array_kernels.setna(A, atq__aizif)
                    else:
                        A[atq__aizif] = ''.join([chr(rzxjt__dtrbs) for
                            rzxjt__dtrbs in data[atq__aizif]])
                return A
            return impl_binary
        if is_overload_true(from_series) and data.dtype in (bodo.
            datetime64ns, bodo.timedelta64ns):

            def impl_str_dt_series(data, new_dtype, copy=None, nan_to_str=
                True, from_series=False):
                numba.parfors.parfor.init_prange()
                saiwn__zsb = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(saiwn__zsb, -1
                    )
                for atq__aizif in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    if bodo.libs.array_kernels.isna(data, atq__aizif):
                        if nan_to_str:
                            A[atq__aizif] = 'NaT'
                        else:
                            bodo.libs.array_kernels.setna(A, atq__aizif)
                        continue
                    A[atq__aizif] = str(box_if_dt64(data[atq__aizif]))
                return A
            return impl_str_dt_series
        else:

            def impl_str_array(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                numba.parfors.parfor.init_prange()
                saiwn__zsb = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(saiwn__zsb, -1
                    )
                for atq__aizif in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    if bodo.libs.array_kernels.isna(data, atq__aizif):
                        if nan_to_str:
                            A[atq__aizif] = 'nan'
                        else:
                            bodo.libs.array_kernels.setna(A, atq__aizif)
                        continue
                    A[atq__aizif] = str(data[atq__aizif])
                return A
            return impl_str_array
    if isinstance(new_dtype, bodo.hiframes.pd_categorical_ext.
        PDCategoricalDtype):

        def impl_cat_dtype(data, new_dtype, copy=None, nan_to_str=True,
            from_series=False):
            saiwn__zsb = len(data)
            numba.parfors.parfor.init_prange()
            scg__rtw = (bodo.hiframes.pd_categorical_ext.
                get_label_dict_from_categories(new_dtype.categories.values))
            A = bodo.hiframes.pd_categorical_ext.alloc_categorical_array(
                saiwn__zsb, new_dtype)
            kfpx__mqna = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A))
            for dofm__odrd in numba.parfors.parfor.internal_prange(saiwn__zsb):
                if bodo.libs.array_kernels.isna(data, dofm__odrd):
                    bodo.libs.array_kernels.setna(A, dofm__odrd)
                    continue
                val = data[dofm__odrd]
                if val not in scg__rtw:
                    bodo.libs.array_kernels.setna(A, dofm__odrd)
                    continue
                kfpx__mqna[dofm__odrd] = scg__rtw[val]
            return A
        return impl_cat_dtype
    if is_overload_constant_str(new_dtype) and get_overload_const_str(new_dtype
        ) == 'category':

        def impl_category(data, new_dtype, copy=None, nan_to_str=True,
            from_series=False):
            cnlr__vzcm = bodo.libs.array_kernels.unique(data, dropna=True)
            cnlr__vzcm = pd.Series(cnlr__vzcm).sort_values().values
            cnlr__vzcm = bodo.allgatherv(cnlr__vzcm, False)
            esv__eaaqf = bodo.hiframes.pd_categorical_ext.init_cat_dtype(bodo
                .utils.conversion.index_from_array(cnlr__vzcm, None), False,
                None, None)
            saiwn__zsb = len(data)
            numba.parfors.parfor.init_prange()
            scg__rtw = (bodo.hiframes.pd_categorical_ext.
                get_label_dict_from_categories_no_duplicates(cnlr__vzcm))
            A = bodo.hiframes.pd_categorical_ext.alloc_categorical_array(
                saiwn__zsb, esv__eaaqf)
            kfpx__mqna = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A))
            for dofm__odrd in numba.parfors.parfor.internal_prange(saiwn__zsb):
                if bodo.libs.array_kernels.isna(data, dofm__odrd):
                    bodo.libs.array_kernels.setna(A, dofm__odrd)
                    continue
                val = data[dofm__odrd]
                kfpx__mqna[dofm__odrd] = scg__rtw[val]
            return A
        return impl_category
    nb_dtype = bodo.utils.typing.parse_dtype(new_dtype)
    if isinstance(data, bodo.libs.int_arr_ext.IntegerArrayType):
        tumbp__ygmjq = isinstance(nb_dtype, bodo.libs.int_arr_ext.IntDtype
            ) and data.dtype == nb_dtype.dtype
    else:
        tumbp__ygmjq = data.dtype == nb_dtype
    if ovgi__kcykq and tumbp__ygmjq:
        return (lambda data, new_dtype, copy=None, nan_to_str=True,
            from_series=False: data.copy())
    if tumbp__ygmjq:
        return (lambda data, new_dtype, copy=None, nan_to_str=True,
            from_series=False: data)
    if isinstance(nb_dtype, bodo.libs.int_arr_ext.IntDtype):
        if isinstance(nb_dtype, types.Integer):
            owfxl__dhaw = nb_dtype
        else:
            owfxl__dhaw = nb_dtype.dtype
        if isinstance(data.dtype, types.Float):

            def impl_float(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                saiwn__zsb = len(data)
                numba.parfors.parfor.init_prange()
                yshnd__aswv = bodo.libs.int_arr_ext.alloc_int_array(saiwn__zsb,
                    owfxl__dhaw)
                for dofm__odrd in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    if bodo.libs.array_kernels.isna(data, dofm__odrd):
                        bodo.libs.array_kernels.setna(yshnd__aswv, dofm__odrd)
                    else:
                        yshnd__aswv[dofm__odrd] = int(data[dofm__odrd])
                return yshnd__aswv
            return impl_float
        else:
            if data == bodo.dict_str_arr_type:

                def impl_dict(data, new_dtype, copy=None, nan_to_str=True,
                    from_series=False):
                    return bodo.libs.dict_arr_ext.convert_dict_arr_to_int(data,
                        owfxl__dhaw)
                return impl_dict

            def impl(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                saiwn__zsb = len(data)
                numba.parfors.parfor.init_prange()
                yshnd__aswv = bodo.libs.int_arr_ext.alloc_int_array(saiwn__zsb,
                    owfxl__dhaw)
                for dofm__odrd in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    if bodo.libs.array_kernels.isna(data, dofm__odrd):
                        bodo.libs.array_kernels.setna(yshnd__aswv, dofm__odrd)
                    else:
                        yshnd__aswv[dofm__odrd] = np.int64(data[dofm__odrd])
                return yshnd__aswv
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
            saiwn__zsb = len(data)
            numba.parfors.parfor.init_prange()
            yshnd__aswv = bodo.libs.bool_arr_ext.alloc_bool_array(saiwn__zsb)
            for dofm__odrd in numba.parfors.parfor.internal_prange(saiwn__zsb):
                if bodo.libs.array_kernels.isna(data, dofm__odrd):
                    bodo.libs.array_kernels.setna(yshnd__aswv, dofm__odrd)
                else:
                    yshnd__aswv[dofm__odrd] = bool(data[dofm__odrd])
            return yshnd__aswv
        return impl_bool
    if nb_dtype == bodo.datetime_date_type:
        if data.dtype == bodo.datetime64ns:

            def impl_date(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                saiwn__zsb = len(data)
                llfwz__uud = (bodo.hiframes.datetime_date_ext.
                    alloc_datetime_date_array(saiwn__zsb))
                for dofm__odrd in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    if bodo.libs.array_kernels.isna(data, dofm__odrd):
                        bodo.libs.array_kernels.setna(llfwz__uud, dofm__odrd)
                    else:
                        llfwz__uud[dofm__odrd
                            ] = bodo.utils.conversion.box_if_dt64(data[
                            dofm__odrd]).date()
                return llfwz__uud
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
                saiwn__zsb = len(data)
                numba.parfors.parfor.init_prange()
                llfwz__uud = np.empty(saiwn__zsb, dtype=np.dtype(
                    'datetime64[ns]'))
                for dofm__odrd in numba.parfors.parfor.internal_prange(
                    saiwn__zsb):
                    if bodo.libs.array_kernels.isna(data, dofm__odrd):
                        bodo.libs.array_kernels.setna(llfwz__uud, dofm__odrd)
                    else:
                        llfwz__uud[dofm__odrd
                            ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                            np.int64(data[dofm__odrd]))
                return llfwz__uud
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
            if ovgi__kcykq:

                def impl_numeric(data, new_dtype, copy=None, nan_to_str=
                    True, from_series=False):
                    saiwn__zsb = len(data)
                    numba.parfors.parfor.init_prange()
                    llfwz__uud = np.empty(saiwn__zsb, dtype=np.dtype(
                        'timedelta64[ns]'))
                    for dofm__odrd in numba.parfors.parfor.internal_prange(
                        saiwn__zsb):
                        if bodo.libs.array_kernels.isna(data, dofm__odrd):
                            bodo.libs.array_kernels.setna(llfwz__uud,
                                dofm__odrd)
                        else:
                            llfwz__uud[dofm__odrd] = (bodo.hiframes.
                                pd_timestamp_ext.integer_to_timedelta64(np.
                                int64(data[dofm__odrd])))
                    return llfwz__uud
                return impl_numeric
            else:
                return (lambda data, new_dtype, copy=None, nan_to_str=True,
                    from_series=False: data.view('int64'))
    if nb_dtype == types.int64 and data.dtype in [bodo.datetime64ns, bodo.
        timedelta64ns]:

        def impl_datelike_to_integer(data, new_dtype, copy=None, nan_to_str
            =True, from_series=False):
            saiwn__zsb = len(data)
            numba.parfors.parfor.init_prange()
            A = np.empty(saiwn__zsb, types.int64)
            for dofm__odrd in numba.parfors.parfor.internal_prange(saiwn__zsb):
                if bodo.libs.array_kernels.isna(data, dofm__odrd):
                    bodo.libs.array_kernels.setna(A, dofm__odrd)
                else:
                    A[dofm__odrd] = np.int64(data[dofm__odrd])
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
    grrt__albpe = []
    saiwn__zsb = len(A)
    for dofm__odrd in range(saiwn__zsb):
        cztm__hemk = A[dofm__odrd]
        for nzbkg__juimb in cztm__hemk:
            grrt__albpe.append(nzbkg__juimb)
    return bodo.utils.conversion.coerce_to_array(grrt__albpe)


def parse_datetimes_from_strings(data):
    return data


@overload(parse_datetimes_from_strings, no_unliteral=True)
def overload_parse_datetimes_from_strings(data):
    assert is_str_arr_type(data
        ), 'parse_datetimes_from_strings: string array expected'

    def parse_impl(data):
        numba.parfors.parfor.init_prange()
        saiwn__zsb = len(data)
        ccyy__ixgb = np.empty(saiwn__zsb, bodo.utils.conversion.NS_DTYPE)
        for dofm__odrd in numba.parfors.parfor.internal_prange(saiwn__zsb):
            ccyy__ixgb[dofm__odrd
                ] = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(data[
                dofm__odrd])
        return ccyy__ixgb
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
        nthyn__cearq = bodo.utils.conversion.coerce_to_array(data)
        return bodo.utils.conversion.index_from_array(nthyn__cearq, name)
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
                ecxxm__ddcly = None
            else:
                ecxxm__ddcly = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                    bodo.utils.indexing.unoptional(val).value)
            return ecxxm__ddcly
        return impl_optional
    if val == types.Optional(bodo.hiframes.datetime_timedelta_ext.
        pd_timedelta_type):

        def impl_optional_td(val):
            if val is None:
                ecxxm__ddcly = None
            else:
                ecxxm__ddcly = (bodo.hiframes.pd_timestamp_ext.
                    integer_to_timedelta64(bodo.utils.indexing.unoptional(
                    val).value))
            return ecxxm__ddcly
        return impl_optional_td
    return lambda val: val


def to_tuple(val):
    return val


@overload(to_tuple, no_unliteral=True)
def overload_to_tuple(val):
    if not isinstance(val, types.BaseTuple) and is_overload_constant_list(val):
        yctxj__ncyx = len(val.types if isinstance(val, types.LiteralList) else
            get_overload_const_list(val))
        iwpce__hlsto = 'def f(val):\n'
        wucqk__tqou = ','.join(f'val[{dofm__odrd}]' for dofm__odrd in range
            (yctxj__ncyx))
        iwpce__hlsto += f'  return ({wucqk__tqou},)\n'
        fcalh__glrdv = {}
        exec(iwpce__hlsto, {}, fcalh__glrdv)
        impl = fcalh__glrdv['f']
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
                btyh__rac = bodo.hiframes.pd_index_ext.get_index_data(data)
                return bodo.utils.conversion.coerce_to_array(btyh__rac)
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
            evcsq__ztefd = bodo.utils.conversion.coerce_to_array(index)
            return evcsq__ztefd
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
    return {yxl__mnur: qhfk__jbm for yxl__mnur, qhfk__jbm in zip(names, values)
        }


@overload(struct_if_heter_dict, no_unliteral=True)
def overload_struct_if_heter_dict(values, names):
    if not types.is_homogeneous(*values.types):
        return lambda values, names: bodo.libs.struct_arr_ext.init_struct(
            values, names)
    ambp__nfsfp = len(values.types)
    iwpce__hlsto = 'def f(values, names):\n'
    wucqk__tqou = ','.join("'{}': values[{}]".format(get_overload_const_str
        (names.types[dofm__odrd]), dofm__odrd) for dofm__odrd in range(
        ambp__nfsfp))
    iwpce__hlsto += '  return {{{}}}\n'.format(wucqk__tqou)
    fcalh__glrdv = {}
    exec(iwpce__hlsto, {}, fcalh__glrdv)
    impl = fcalh__glrdv['f']
    return impl
