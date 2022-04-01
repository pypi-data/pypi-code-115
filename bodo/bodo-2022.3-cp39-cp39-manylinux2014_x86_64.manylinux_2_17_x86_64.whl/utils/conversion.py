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
        anx__ynt = data.dtype
        if isinstance(anx__ynt, types.Optional):
            anx__ynt = anx__ynt.type
            if bodo.utils.typing.is_scalar_type(anx__ynt):
                use_nullable_array = True
        if isinstance(anx__ynt, (types.Boolean, types.Integer, Decimal128Type)
            ) or anx__ynt in [bodo.hiframes.pd_timestamp_ext.
            pd_timestamp_type, bodo.hiframes.datetime_date_ext.
            datetime_date_type, bodo.hiframes.datetime_timedelta_ext.
            datetime_timedelta_type]:
            lyj__ljtpz = dtype_to_array_type(anx__ynt)
            if not is_overload_none(use_nullable_array):
                lyj__ljtpz = to_nullable_type(lyj__ljtpz)

            def impl(data, error_on_nonarray=True, use_nullable_array=None,
                scalar_to_arr_len=None):
                msqh__xla = len(data)
                A = bodo.utils.utils.alloc_type(msqh__xla, lyj__ljtpz, (-1,))
                bodo.utils.utils.tuple_list_to_array(A, data, anx__ynt)
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
            ybicx__casjl = data.precision
            lrssa__brffc = data.scale

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                msqh__xla = scalar_to_arr_len
                A = bodo.libs.decimal_arr_ext.alloc_decimal_array(msqh__xla,
                    ybicx__casjl, lrssa__brffc)
                for slqe__yhao in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    A[slqe__yhao] = data
                return A
            return impl_ts
        if data == bodo.hiframes.datetime_datetime_ext.datetime_datetime_type:
            dvf__ojy = np.dtype('datetime64[ns]')

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                msqh__xla = scalar_to_arr_len
                A = np.empty(msqh__xla, dvf__ojy)
                gngm__xts = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(data))
                pdb__ieatb = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                    gngm__xts)
                for slqe__yhao in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    A[slqe__yhao] = pdb__ieatb
                return A
            return impl_ts
        if (data == bodo.hiframes.datetime_timedelta_ext.
            datetime_timedelta_type):
            yhcv__wzvqx = np.dtype('timedelta64[ns]')

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                msqh__xla = scalar_to_arr_len
                A = np.empty(msqh__xla, yhcv__wzvqx)
                smlxm__rvnnc = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(data))
                for slqe__yhao in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    A[slqe__yhao] = smlxm__rvnnc
                return A
            return impl_ts
        if data == bodo.hiframes.datetime_date_ext.datetime_date_type:

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                msqh__xla = scalar_to_arr_len
                A = bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(
                    msqh__xla)
                for slqe__yhao in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    A[slqe__yhao] = data
                return A
            return impl_ts
        if data == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            dvf__ojy = np.dtype('datetime64[ns]')

            def impl_ts(data, error_on_nonarray=True, use_nullable_array=
                None, scalar_to_arr_len=None):
                msqh__xla = scalar_to_arr_len
                A = np.empty(scalar_to_arr_len, dvf__ojy)
                gngm__xts = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(data
                    .value)
                for slqe__yhao in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    A[slqe__yhao] = gngm__xts
                return A
            return impl_ts
        dtype = types.unliteral(data)
        if not is_overload_none(use_nullable_array) and isinstance(dtype,
            types.Integer):

            def impl_null_integer(data, error_on_nonarray=True,
                use_nullable_array=None, scalar_to_arr_len=None):
                numba.parfors.parfor.init_prange()
                msqh__xla = scalar_to_arr_len
                waf__hceln = bodo.libs.int_arr_ext.alloc_int_array(msqh__xla,
                    dtype)
                for slqe__yhao in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    waf__hceln[slqe__yhao] = data
                return waf__hceln
            return impl_null_integer
        if not is_overload_none(use_nullable_array) and dtype == types.bool_:

            def impl_null_bool(data, error_on_nonarray=True,
                use_nullable_array=None, scalar_to_arr_len=None):
                numba.parfors.parfor.init_prange()
                msqh__xla = scalar_to_arr_len
                waf__hceln = bodo.libs.bool_arr_ext.alloc_bool_array(msqh__xla)
                for slqe__yhao in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    waf__hceln[slqe__yhao] = data
                return waf__hceln
            return impl_null_bool

        def impl_num(data, error_on_nonarray=True, use_nullable_array=None,
            scalar_to_arr_len=None):
            numba.parfors.parfor.init_prange()
            msqh__xla = scalar_to_arr_len
            waf__hceln = np.empty(msqh__xla, dtype)
            for slqe__yhao in numba.parfors.parfor.internal_prange(msqh__xla):
                waf__hceln[slqe__yhao] = data
            return waf__hceln
        return impl_num
    if isinstance(data, types.BaseTuple) and all(isinstance(zhwmx__pjf, (
        types.Float, types.Integer)) for zhwmx__pjf in data.types):
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
        ) and all(isinstance(zhwmx__pjf, types.StringLiteral) for
        zhwmx__pjf in data.types):
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
        vnvat__lfuyz = tuple(dtype_to_array_type(zhwmx__pjf) for zhwmx__pjf in
            data.dtype.types)

        def impl_tuple_list(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            msqh__xla = len(data)
            arr = bodo.libs.tuple_arr_ext.pre_alloc_tuple_array(msqh__xla,
                (-1,), vnvat__lfuyz)
            for slqe__yhao in range(msqh__xla):
                arr[slqe__yhao] = data[slqe__yhao]
            return arr
        return impl_tuple_list
    if isinstance(data, types.List) and (bodo.utils.utils.is_array_typ(data
        .dtype, False) or isinstance(data.dtype, types.List)):
        zyhg__mzjx = dtype_to_array_type(data.dtype.dtype)

        def impl_array_item_arr(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            msqh__xla = len(data)
            jziw__ghrag = init_nested_counts(zyhg__mzjx)
            for slqe__yhao in range(msqh__xla):
                lsqg__uuzhl = bodo.utils.conversion.coerce_to_array(data[
                    slqe__yhao], use_nullable_array=True)
                jziw__ghrag = add_nested_counts(jziw__ghrag, lsqg__uuzhl)
            waf__hceln = (bodo.libs.array_item_arr_ext.
                pre_alloc_array_item_array(msqh__xla, jziw__ghrag, zyhg__mzjx))
            ivbnw__bblwo = bodo.libs.array_item_arr_ext.get_null_bitmap(
                waf__hceln)
            for cxrwo__omo in range(msqh__xla):
                lsqg__uuzhl = bodo.utils.conversion.coerce_to_array(data[
                    cxrwo__omo], use_nullable_array=True)
                waf__hceln[cxrwo__omo] = lsqg__uuzhl
                bodo.libs.int_arr_ext.set_bit_to_arr(ivbnw__bblwo,
                    cxrwo__omo, 1)
            return waf__hceln
        return impl_array_item_arr
    if not is_overload_none(scalar_to_arr_len) and isinstance(data, (types.
        UnicodeType, types.StringLiteral)):

        def impl_str(data, error_on_nonarray=True, use_nullable_array=None,
            scalar_to_arr_len=None):
            msqh__xla = scalar_to_arr_len
            A = bodo.libs.str_arr_ext.pre_alloc_string_array(msqh__xla, -1)
            for slqe__yhao in numba.parfors.parfor.internal_prange(msqh__xla):
                A[slqe__yhao] = data
            return A
        return impl_str
    if isinstance(data, types.List) and isinstance(data.dtype, bodo.
        hiframes.pd_timestamp_ext.PandasTimestampType):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
            'coerce_to_array()')

        def impl_list_timestamp(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            msqh__xla = len(data)
            A = np.empty(msqh__xla, np.dtype('datetime64[ns]'))
            for slqe__yhao in range(msqh__xla):
                A[slqe__yhao] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                    data[slqe__yhao].value)
            return A
        return impl_list_timestamp
    if isinstance(data, types.List) and data.dtype == bodo.pd_timedelta_type:

        def impl_list_timedelta(data, error_on_nonarray=True,
            use_nullable_array=None, scalar_to_arr_len=None):
            msqh__xla = len(data)
            A = np.empty(msqh__xla, np.dtype('timedelta64[ns]'))
            for slqe__yhao in range(msqh__xla):
                A[slqe__yhao
                    ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                    data[slqe__yhao].value)
            return A
        return impl_list_timedelta
    if isinstance(data, bodo.hiframes.pd_timestamp_ext.PandasTimestampType):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
            'coerce_to_array()')
    if not is_overload_none(scalar_to_arr_len) and data in [bodo.
        pd_timestamp_type, bodo.pd_timedelta_type]:
        gmu__ssvm = ('datetime64[ns]' if data == bodo.pd_timestamp_type else
            'timedelta64[ns]')

        def impl_timestamp(data, error_on_nonarray=True, use_nullable_array
            =None, scalar_to_arr_len=None):
            msqh__xla = scalar_to_arr_len
            A = np.empty(msqh__xla, gmu__ssvm)
            data = bodo.utils.conversion.unbox_if_timestamp(data)
            for slqe__yhao in numba.parfors.parfor.internal_prange(msqh__xla):
                A[slqe__yhao] = data
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
    xjwny__mhhpg = is_overload_true(copy)
    ajvr__dulwq = is_overload_constant_str(new_dtype
        ) and get_overload_const_str(new_dtype) == 'object'
    if is_overload_none(new_dtype) or ajvr__dulwq:
        if xjwny__mhhpg:
            return (lambda data, new_dtype, copy=None, nan_to_str=True,
                from_series=False: data.copy())
        return (lambda data, new_dtype, copy=None, nan_to_str=True,
            from_series=False: data)
    if _is_str_dtype(new_dtype):
        if isinstance(data.dtype, types.Integer):

            def impl_int_str(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                numba.parfors.parfor.init_prange()
                msqh__xla = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(msqh__xla, -1)
                for oxjcl__udg in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    if bodo.libs.array_kernels.isna(data, oxjcl__udg):
                        if nan_to_str:
                            bodo.libs.str_arr_ext.str_arr_setitem_NA_str(A,
                                oxjcl__udg)
                        else:
                            bodo.libs.array_kernels.setna(A, oxjcl__udg)
                    else:
                        bodo.libs.str_arr_ext.str_arr_setitem_int_to_str(A,
                            oxjcl__udg, data[oxjcl__udg])
                return A
            return impl_int_str
        if data.dtype == bytes_type:

            def impl_binary(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                numba.parfors.parfor.init_prange()
                msqh__xla = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(msqh__xla, -1)
                for oxjcl__udg in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    if bodo.libs.array_kernels.isna(data, oxjcl__udg):
                        bodo.libs.array_kernels.setna(A, oxjcl__udg)
                    else:
                        A[oxjcl__udg] = ''.join([chr(crxw__bkn) for
                            crxw__bkn in data[oxjcl__udg]])
                return A
            return impl_binary
        if is_overload_true(from_series) and data.dtype in (bodo.
            datetime64ns, bodo.timedelta64ns):

            def impl_str_dt_series(data, new_dtype, copy=None, nan_to_str=
                True, from_series=False):
                numba.parfors.parfor.init_prange()
                msqh__xla = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(msqh__xla, -1)
                for oxjcl__udg in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    if bodo.libs.array_kernels.isna(data, oxjcl__udg):
                        if nan_to_str:
                            A[oxjcl__udg] = 'NaT'
                        else:
                            bodo.libs.array_kernels.setna(A, oxjcl__udg)
                        continue
                    A[oxjcl__udg] = str(box_if_dt64(data[oxjcl__udg]))
                return A
            return impl_str_dt_series
        else:

            def impl_str_array(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                numba.parfors.parfor.init_prange()
                msqh__xla = len(data)
                A = bodo.libs.str_arr_ext.pre_alloc_string_array(msqh__xla, -1)
                for oxjcl__udg in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    if bodo.libs.array_kernels.isna(data, oxjcl__udg):
                        if nan_to_str:
                            A[oxjcl__udg] = 'nan'
                        else:
                            bodo.libs.array_kernels.setna(A, oxjcl__udg)
                        continue
                    A[oxjcl__udg] = str(data[oxjcl__udg])
                return A
            return impl_str_array
    if isinstance(new_dtype, bodo.hiframes.pd_categorical_ext.
        PDCategoricalDtype):

        def impl_cat_dtype(data, new_dtype, copy=None, nan_to_str=True,
            from_series=False):
            msqh__xla = len(data)
            numba.parfors.parfor.init_prange()
            ypul__lxj = (bodo.hiframes.pd_categorical_ext.
                get_label_dict_from_categories(new_dtype.categories.values))
            A = bodo.hiframes.pd_categorical_ext.alloc_categorical_array(
                msqh__xla, new_dtype)
            evolt__drcq = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A))
            for slqe__yhao in numba.parfors.parfor.internal_prange(msqh__xla):
                if bodo.libs.array_kernels.isna(data, slqe__yhao):
                    bodo.libs.array_kernels.setna(A, slqe__yhao)
                    continue
                val = data[slqe__yhao]
                if val not in ypul__lxj:
                    bodo.libs.array_kernels.setna(A, slqe__yhao)
                    continue
                evolt__drcq[slqe__yhao] = ypul__lxj[val]
            return A
        return impl_cat_dtype
    if is_overload_constant_str(new_dtype) and get_overload_const_str(new_dtype
        ) == 'category':

        def impl_category(data, new_dtype, copy=None, nan_to_str=True,
            from_series=False):
            bhivs__jogj = bodo.libs.array_kernels.unique(data, dropna=True)
            bhivs__jogj = pd.Series(bhivs__jogj).sort_values().values
            bhivs__jogj = bodo.allgatherv(bhivs__jogj, False)
            gpksg__ned = bodo.hiframes.pd_categorical_ext.init_cat_dtype(bodo
                .utils.conversion.index_from_array(bhivs__jogj, None), 
                False, None, None)
            msqh__xla = len(data)
            numba.parfors.parfor.init_prange()
            ypul__lxj = (bodo.hiframes.pd_categorical_ext.
                get_label_dict_from_categories_no_duplicates(bhivs__jogj))
            A = bodo.hiframes.pd_categorical_ext.alloc_categorical_array(
                msqh__xla, gpksg__ned)
            evolt__drcq = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A))
            for slqe__yhao in numba.parfors.parfor.internal_prange(msqh__xla):
                if bodo.libs.array_kernels.isna(data, slqe__yhao):
                    bodo.libs.array_kernels.setna(A, slqe__yhao)
                    continue
                val = data[slqe__yhao]
                evolt__drcq[slqe__yhao] = ypul__lxj[val]
            return A
        return impl_category
    nb_dtype = bodo.utils.typing.parse_dtype(new_dtype)
    if isinstance(data, bodo.libs.int_arr_ext.IntegerArrayType):
        wcdj__hqv = isinstance(nb_dtype, bodo.libs.int_arr_ext.IntDtype
            ) and data.dtype == nb_dtype.dtype
    else:
        wcdj__hqv = data.dtype == nb_dtype
    if xjwny__mhhpg and wcdj__hqv:
        return (lambda data, new_dtype, copy=None, nan_to_str=True,
            from_series=False: data.copy())
    if wcdj__hqv:
        return (lambda data, new_dtype, copy=None, nan_to_str=True,
            from_series=False: data)
    if isinstance(nb_dtype, bodo.libs.int_arr_ext.IntDtype):
        if isinstance(nb_dtype, types.Integer):
            gmu__ssvm = nb_dtype
        else:
            gmu__ssvm = nb_dtype.dtype
        if isinstance(data.dtype, types.Float):

            def impl_float(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                msqh__xla = len(data)
                numba.parfors.parfor.init_prange()
                ujbe__ydl = bodo.libs.int_arr_ext.alloc_int_array(msqh__xla,
                    gmu__ssvm)
                for slqe__yhao in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    if bodo.libs.array_kernels.isna(data, slqe__yhao):
                        bodo.libs.array_kernels.setna(ujbe__ydl, slqe__yhao)
                    else:
                        ujbe__ydl[slqe__yhao] = int(data[slqe__yhao])
                return ujbe__ydl
            return impl_float
        else:
            if data == bodo.dict_str_arr_type:

                def impl_dict(data, new_dtype, copy=None, nan_to_str=True,
                    from_series=False):
                    return bodo.libs.dict_arr_ext.convert_dict_arr_to_int(data,
                        gmu__ssvm)
                return impl_dict

            def impl(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                msqh__xla = len(data)
                numba.parfors.parfor.init_prange()
                ujbe__ydl = bodo.libs.int_arr_ext.alloc_int_array(msqh__xla,
                    gmu__ssvm)
                for slqe__yhao in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    if bodo.libs.array_kernels.isna(data, slqe__yhao):
                        bodo.libs.array_kernels.setna(ujbe__ydl, slqe__yhao)
                    else:
                        ujbe__ydl[slqe__yhao] = np.int64(data[slqe__yhao])
                return ujbe__ydl
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
            msqh__xla = len(data)
            numba.parfors.parfor.init_prange()
            ujbe__ydl = bodo.libs.bool_arr_ext.alloc_bool_array(msqh__xla)
            for slqe__yhao in numba.parfors.parfor.internal_prange(msqh__xla):
                if bodo.libs.array_kernels.isna(data, slqe__yhao):
                    bodo.libs.array_kernels.setna(ujbe__ydl, slqe__yhao)
                else:
                    ujbe__ydl[slqe__yhao] = bool(data[slqe__yhao])
            return ujbe__ydl
        return impl_bool
    if nb_dtype == bodo.datetime_date_type:
        if data.dtype == bodo.datetime64ns:

            def impl_date(data, new_dtype, copy=None, nan_to_str=True,
                from_series=False):
                msqh__xla = len(data)
                waf__hceln = (bodo.hiframes.datetime_date_ext.
                    alloc_datetime_date_array(msqh__xla))
                for slqe__yhao in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    if bodo.libs.array_kernels.isna(data, slqe__yhao):
                        bodo.libs.array_kernels.setna(waf__hceln, slqe__yhao)
                    else:
                        waf__hceln[slqe__yhao
                            ] = bodo.utils.conversion.box_if_dt64(data[
                            slqe__yhao]).date()
                return waf__hceln
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
                msqh__xla = len(data)
                numba.parfors.parfor.init_prange()
                waf__hceln = np.empty(msqh__xla, dtype=np.dtype(
                    'datetime64[ns]'))
                for slqe__yhao in numba.parfors.parfor.internal_prange(
                    msqh__xla):
                    if bodo.libs.array_kernels.isna(data, slqe__yhao):
                        bodo.libs.array_kernels.setna(waf__hceln, slqe__yhao)
                    else:
                        waf__hceln[slqe__yhao
                            ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                            np.int64(data[slqe__yhao]))
                return waf__hceln
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
            if xjwny__mhhpg:

                def impl_numeric(data, new_dtype, copy=None, nan_to_str=
                    True, from_series=False):
                    msqh__xla = len(data)
                    numba.parfors.parfor.init_prange()
                    waf__hceln = np.empty(msqh__xla, dtype=np.dtype(
                        'timedelta64[ns]'))
                    for slqe__yhao in numba.parfors.parfor.internal_prange(
                        msqh__xla):
                        if bodo.libs.array_kernels.isna(data, slqe__yhao):
                            bodo.libs.array_kernels.setna(waf__hceln,
                                slqe__yhao)
                        else:
                            waf__hceln[slqe__yhao] = (bodo.hiframes.
                                pd_timestamp_ext.integer_to_timedelta64(np.
                                int64(data[slqe__yhao])))
                    return waf__hceln
                return impl_numeric
            else:
                return (lambda data, new_dtype, copy=None, nan_to_str=True,
                    from_series=False: data.view('int64'))
    if nb_dtype == types.int64 and data.dtype in [bodo.datetime64ns, bodo.
        timedelta64ns]:

        def impl_datelike_to_integer(data, new_dtype, copy=None, nan_to_str
            =True, from_series=False):
            msqh__xla = len(data)
            numba.parfors.parfor.init_prange()
            A = np.empty(msqh__xla, types.int64)
            for slqe__yhao in numba.parfors.parfor.internal_prange(msqh__xla):
                if bodo.libs.array_kernels.isna(data, slqe__yhao):
                    bodo.libs.array_kernels.setna(A, slqe__yhao)
                else:
                    A[slqe__yhao] = np.int64(data[slqe__yhao])
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
    qhoz__aexc = []
    msqh__xla = len(A)
    for slqe__yhao in range(msqh__xla):
        uhmm__vtwt = A[slqe__yhao]
        for wrz__pyn in uhmm__vtwt:
            qhoz__aexc.append(wrz__pyn)
    return bodo.utils.conversion.coerce_to_array(qhoz__aexc)


def parse_datetimes_from_strings(data):
    return data


@overload(parse_datetimes_from_strings, no_unliteral=True)
def overload_parse_datetimes_from_strings(data):
    assert is_str_arr_type(data
        ), 'parse_datetimes_from_strings: string array expected'

    def parse_impl(data):
        numba.parfors.parfor.init_prange()
        msqh__xla = len(data)
        jfzc__dmey = np.empty(msqh__xla, bodo.utils.conversion.NS_DTYPE)
        for slqe__yhao in numba.parfors.parfor.internal_prange(msqh__xla):
            jfzc__dmey[slqe__yhao
                ] = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(data[
                slqe__yhao])
        return jfzc__dmey
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
        cwatq__lpsc = bodo.utils.conversion.coerce_to_array(data)
        return bodo.utils.conversion.index_from_array(cwatq__lpsc, name)
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
                nhsxc__uzar = None
            else:
                nhsxc__uzar = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                    bodo.utils.indexing.unoptional(val).value)
            return nhsxc__uzar
        return impl_optional
    if val == types.Optional(bodo.hiframes.datetime_timedelta_ext.
        pd_timedelta_type):

        def impl_optional_td(val):
            if val is None:
                nhsxc__uzar = None
            else:
                nhsxc__uzar = (bodo.hiframes.pd_timestamp_ext.
                    integer_to_timedelta64(bodo.utils.indexing.unoptional(
                    val).value))
            return nhsxc__uzar
        return impl_optional_td
    return lambda val: val


def to_tuple(val):
    return val


@overload(to_tuple, no_unliteral=True)
def overload_to_tuple(val):
    if not isinstance(val, types.BaseTuple) and is_overload_constant_list(val):
        syc__hdn = len(val.types if isinstance(val, types.LiteralList) else
            get_overload_const_list(val))
        etac__kmbj = 'def f(val):\n'
        qwq__jqoxq = ','.join(f'val[{slqe__yhao}]' for slqe__yhao in range(
            syc__hdn))
        etac__kmbj += f'  return ({qwq__jqoxq},)\n'
        pcmv__ncdq = {}
        exec(etac__kmbj, {}, pcmv__ncdq)
        impl = pcmv__ncdq['f']
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
                glhf__uer = bodo.hiframes.pd_index_ext.get_index_data(data)
                return bodo.utils.conversion.coerce_to_array(glhf__uer)
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
            tmh__ywm = bodo.utils.conversion.coerce_to_array(index)
            return tmh__ywm
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
    return {hwz__eraaw: gngm__xts for hwz__eraaw, gngm__xts in zip(names,
        values)}


@overload(struct_if_heter_dict, no_unliteral=True)
def overload_struct_if_heter_dict(values, names):
    if not types.is_homogeneous(*values.types):
        return lambda values, names: bodo.libs.struct_arr_ext.init_struct(
            values, names)
    pca__rbd = len(values.types)
    etac__kmbj = 'def f(values, names):\n'
    qwq__jqoxq = ','.join("'{}': values[{}]".format(get_overload_const_str(
        names.types[slqe__yhao]), slqe__yhao) for slqe__yhao in range(pca__rbd)
        )
    etac__kmbj += '  return {{{}}}\n'.format(qwq__jqoxq)
    pcmv__ncdq = {}
    exec(etac__kmbj, {}, pcmv__ncdq)
    impl = pcmv__ncdq['f']
    return impl
