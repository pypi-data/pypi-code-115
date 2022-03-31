"""DatetimeArray extension for Pandas DatetimeArray with timezone support."""
import operator
from re import T
import numba
import numpy as np
import pandas as pd
import pytz
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import lower_constant
from numba.extending import NativeValue, box, intrinsic, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_model, typeof_impl, unbox
import bodo
from bodo.utils.conversion import ensure_contig_if_np
from bodo.utils.typing import BodoArrayIterator, BodoError, get_literal_value, get_overload_const_bool, is_list_like_index_type, is_overload_constant_bool, is_overload_constant_int, is_overload_constant_str, raise_bodo_error


class PandasDatetimeTZDtype(types.Type):

    def __init__(self, tz):
        if isinstance(tz, (pytz._FixedOffset, pytz.tzinfo.BaseTzInfo)):
            tz = get_pytz_type_info(tz)
        if not isinstance(tz, (int, str)):
            raise BodoError(
                'Timezone must be either a valid pytz type with a zone or a fixed offset'
                )
        self.tz = tz
        super(PandasDatetimeTZDtype, self).__init__(name=
            f'PandasDatetimeTZDtype[{tz}]')


def get_pytz_type_info(pytz_type):
    if isinstance(pytz_type, pytz._FixedOffset):
        evwoq__lmko = pd.Timedelta(pytz_type._offset).value
    else:
        evwoq__lmko = pytz_type.zone
        if evwoq__lmko not in pytz.all_timezones_set:
            raise BodoError(
                'Unsupported timezone type. Timezones must be a fixedOffset or contain a zone found in pytz.all_timezones'
                )
    return evwoq__lmko


def nanoseconds_to_offset(nanoseconds):
    gppew__zfk = nanoseconds // (60 * 1000 * 1000 * 1000)
    return pytz.FixedOffset(gppew__zfk)


class DatetimeArrayType(types.IterableType, types.ArrayCompatible):

    def __init__(self, tz):
        if isinstance(tz, (pytz._FixedOffset, pytz.tzinfo.BaseTzInfo)):
            tz = get_pytz_type_info(tz)
        if not isinstance(tz, (int, str)):
            raise BodoError(
                'Timezone must be either a valid pytz type with a zone or a fixed offset'
                )
        self.tz = tz
        self._data_array_type = types.Array(types.NPDatetime('ns'), 1, 'C')
        self._dtype = PandasDatetimeTZDtype(tz)
        super(DatetimeArrayType, self).__init__(name=
            f'PandasDatetimeArray[{tz}]')

    @property
    def data_array_type(self):
        return self._data_array_type

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def iterator_type(self):
        return BodoArrayIterator(self)

    @property
    def dtype(self):
        return self._dtype

    def copy(self):
        return DatetimeArrayType(self.tz)


@register_model(DatetimeArrayType)
class PandasDatetimeArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        adim__lwj = [('data', fe_type.data_array_type)]
        models.StructModel.__init__(self, dmm, fe_type, adim__lwj)


make_attribute_wrapper(DatetimeArrayType, 'data', '_data')


@typeof_impl.register(pd.arrays.DatetimeArray)
def typeof_pd_datetime_array(val, c):
    return DatetimeArrayType(val.dtype.tz)


@unbox(DatetimeArrayType)
def unbox_pd_datetime_array(typ, val, c):
    pmrv__ctrch = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    vgfck__klw = c.pyapi.string_from_constant_string('datetime64[ns]')
    ujs__rnv = c.pyapi.call_method(val, 'to_numpy', (vgfck__klw,))
    pmrv__ctrch.data = c.unbox(typ.data_array_type, ujs__rnv).value
    c.pyapi.decref(ujs__rnv)
    tey__lhhax = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(pmrv__ctrch._getvalue(), is_error=tey__lhhax)


@box(DatetimeArrayType)
def box_pd_datetime_array(typ, val, c):
    pmrv__ctrch = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    c.context.nrt.incref(c.builder, typ.data_array_type, pmrv__ctrch.data)
    sadu__porku = c.pyapi.from_native_value(typ.data_array_type,
        pmrv__ctrch.data, c.env_manager)
    lizzy__uwcc = c.context.get_constant_generic(c.builder, types.
        unicode_type, 'ns')
    vow__dzwm = c.pyapi.from_native_value(types.unicode_type, lizzy__uwcc,
        c.env_manager)
    if isinstance(typ.tz, str):
        gjny__ytjw = c.context.get_constant_generic(c.builder, types.
            unicode_type, typ.tz)
        bvd__xgga = c.pyapi.from_native_value(types.unicode_type,
            gjny__ytjw, c.env_manager)
    else:
        kmz__rifhe = nanoseconds_to_offset(typ.tz)
        bvd__xgga = c.pyapi.unserialize(c.pyapi.serialize_object(kmz__rifhe))
    ccu__ebask = c.context.insert_const_string(c.builder.module, 'pandas')
    pxub__hblh = c.pyapi.import_module_noblock(ccu__ebask)
    uwn__vgv = c.pyapi.call_method(pxub__hblh, 'DatetimeTZDtype', (
        vow__dzwm, bvd__xgga))
    zev__ffmny = c.pyapi.object_getattr_string(pxub__hblh, 'arrays')
    bfe__xevz = c.pyapi.call_method(zev__ffmny, 'DatetimeArray', (
        sadu__porku, uwn__vgv))
    c.pyapi.decref(sadu__porku)
    c.pyapi.decref(vow__dzwm)
    c.pyapi.decref(bvd__xgga)
    c.pyapi.decref(pxub__hblh)
    c.pyapi.decref(uwn__vgv)
    c.pyapi.decref(zev__ffmny)
    c.context.nrt.decref(c.builder, typ, val)
    return bfe__xevz


@intrinsic
def init_pandas_datetime_array(typingctx, data, tz):

    def codegen(context, builder, sig, args):
        data, tz = args
        peq__eyakh = cgutils.create_struct_proxy(sig.return_type)(context,
            builder)
        peq__eyakh.data = data
        context.nrt.incref(builder, sig.args[0], data)
        return peq__eyakh._getvalue()
    if is_overload_constant_str(tz) or is_overload_constant_int(tz):
        gjny__ytjw = get_literal_value(tz)
    else:
        raise BodoError('tz must be a constant string or Fixed Offset')
    umyca__lfx = DatetimeArrayType(gjny__ytjw)
    sig = umyca__lfx(umyca__lfx.data_array_type, tz)
    return sig, codegen


@overload(len, no_unliteral=True)
def overload_pd_datetime_arr_len(A):
    if isinstance(A, DatetimeArrayType):
        return lambda A: len(A._data)


@lower_constant(DatetimeArrayType)
def lower_constant_pd_datetime_arr(context, builder, typ, pyval):
    raise BodoError('pd.DatetimeArray(): Lowering not supported')


@overload_attribute(DatetimeArrayType, 'shape')
def overload_pd_datetime_arr_shape(A):
    return lambda A: (len(A._data),)


@overload_method(DatetimeArrayType, 'tz_convert', no_unliteral=True)
def overload_pd_datetime_tz_convert(A, tz):
    if tz == types.none:
        raise_bodo_error('tz_convert(): tz must be a string or Fixed Offset')
    else:

        def impl(A, tz):
            return init_pandas_datetime_array(A._data.copy(), tz)
    return impl


@overload_method(DatetimeArrayType, 'copy', no_unliteral=True)
def overload_pd_datetime_tz_convert(A):
    tz = A.tz

    def impl(A):
        return init_pandas_datetime_array(A._data.copy(), tz)
    return impl


@overload(operator.getitem, no_unliteral=True)
def overload_getitem(A, ind):
    if not isinstance(A, DatetimeArrayType):
        return
    tz = A.tz
    if isinstance(ind, types.Integer):

        def impl(A, ind):
            return bodo.hiframes.pd_timestamp_ext.convert_val_to_timestamp(bodo
                .hiframes.pd_timestamp_ext.dt64_to_integer(A._data[ind]), tz)
        return impl
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:

        def impl_bool(A, ind):
            ind = bodo.utils.conversion.coerce_to_ndarray(ind)
            szh__njn = ensure_contig_if_np(A._data[ind])
            return init_pandas_datetime_array(szh__njn, tz)
        return impl_bool
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            szh__njn = ensure_contig_if_np(A._data[ind])
            return init_pandas_datetime_array(szh__njn, tz)
        return impl_slice
    raise BodoError(
        'operator.getitem with DatetimeArrayType is only supported with an integer index, boolean array, or slice.'
        )


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def unwrap_tz_array(A):
    if isinstance(A, DatetimeArrayType):
        return lambda A: A._data
    return lambda A: A
