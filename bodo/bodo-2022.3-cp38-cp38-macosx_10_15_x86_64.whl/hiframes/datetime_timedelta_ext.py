"""Numba extension support for datetime.timedelta objects and their arrays.
"""
import datetime
import operator
from collections import namedtuple
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import lower_constant
from numba.extending import NativeValue, box, intrinsic, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_jitable, register_model, typeof_impl, unbox
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
from bodo.hiframes.datetime_datetime_ext import datetime_datetime_type
from bodo.libs import hdatetime_ext
from bodo.utils.indexing import get_new_null_mask_bool_index, get_new_null_mask_int_index, get_new_null_mask_slice_index, setitem_slice_index_null_bits
from bodo.utils.typing import BodoError, get_overload_const_str, is_iterable_type, is_list_like_index_type, is_overload_constant_str
ll.add_symbol('box_datetime_timedelta_array', hdatetime_ext.
    box_datetime_timedelta_array)
ll.add_symbol('unbox_datetime_timedelta_array', hdatetime_ext.
    unbox_datetime_timedelta_array)


class NoInput:
    pass


_no_input = NoInput()


class NoInputType(types.Type):

    def __init__(self):
        super(NoInputType, self).__init__(name='NoInput')


register_model(NoInputType)(models.OpaqueModel)


@typeof_impl.register(NoInput)
def _typ_no_input(val, c):
    return NoInputType()


@lower_constant(NoInputType)
def constant_no_input(context, builder, ty, pyval):
    return context.get_dummy_value()


class PDTimeDeltaType(types.Type):

    def __init__(self):
        super(PDTimeDeltaType, self).__init__(name='PDTimeDeltaType()')


pd_timedelta_type = PDTimeDeltaType()
types.pd_timedelta_type = pd_timedelta_type


@typeof_impl.register(pd.Timedelta)
def typeof_pd_timedelta(val, c):
    return pd_timedelta_type


@register_model(PDTimeDeltaType)
class PDTimeDeltaModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        bpla__yjxy = [('value', types.int64)]
        super(PDTimeDeltaModel, self).__init__(dmm, fe_type, bpla__yjxy)


@box(PDTimeDeltaType)
def box_pd_timedelta(typ, val, c):
    xjhnd__rdho = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    bgm__xjbqx = c.pyapi.long_from_longlong(xjhnd__rdho.value)
    tndj__ctjco = c.pyapi.unserialize(c.pyapi.serialize_object(pd.Timedelta))
    res = c.pyapi.call_function_objargs(tndj__ctjco, (bgm__xjbqx,))
    c.pyapi.decref(bgm__xjbqx)
    c.pyapi.decref(tndj__ctjco)
    return res


@unbox(PDTimeDeltaType)
def unbox_pd_timedelta(typ, val, c):
    bgm__xjbqx = c.pyapi.object_getattr_string(val, 'value')
    neds__bymoa = c.pyapi.long_as_longlong(bgm__xjbqx)
    xjhnd__rdho = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    xjhnd__rdho.value = neds__bymoa
    c.pyapi.decref(bgm__xjbqx)
    idie__crgm = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(xjhnd__rdho._getvalue(), is_error=idie__crgm)


@lower_constant(PDTimeDeltaType)
def lower_constant_pd_timedelta(context, builder, ty, pyval):
    value = context.get_constant(types.int64, pyval.value)
    return lir.Constant.literal_struct([value])


@overload(pd.Timedelta, no_unliteral=True)
def pd_timedelta(value=_no_input, unit='ns', days=0, seconds=0,
    microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
    if value == _no_input:

        def impl_timedelta_kw(value=_no_input, unit='ns', days=0, seconds=0,
            microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
            days += weeks * 7
            hours += days * 24
            minutes += 60 * hours
            seconds += 60 * minutes
            milliseconds += 1000 * seconds
            microseconds += 1000 * milliseconds
            gvm__vljf = 1000 * microseconds
            return init_pd_timedelta(gvm__vljf)
        return impl_timedelta_kw
    if value == bodo.string_type or is_overload_constant_str(value):

        def impl_str(value=_no_input, unit='ns', days=0, seconds=0,
            microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
            with numba.objmode(res='pd_timedelta_type'):
                res = pd.Timedelta(value)
            return res
        return impl_str
    if value == pd_timedelta_type:
        return (lambda value=_no_input, unit='ns', days=0, seconds=0,
            microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0: value)
    if value == datetime_timedelta_type:

        def impl_timedelta_datetime(value=_no_input, unit='ns', days=0,
            seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0,
            weeks=0):
            days = value.days
            seconds = 60 * 60 * 24 * days + value.seconds
            microseconds = 1000 * 1000 * seconds + value.microseconds
            gvm__vljf = 1000 * microseconds
            return init_pd_timedelta(gvm__vljf)
        return impl_timedelta_datetime
    if not is_overload_constant_str(unit):
        raise BodoError('pd.to_timedelta(): unit should be a constant string')
    unit = pd._libs.tslibs.timedeltas.parse_timedelta_unit(
        get_overload_const_str(unit))
    hrzkw__ipkwq, gkikx__his = pd._libs.tslibs.conversion.precision_from_unit(
        unit)

    def impl_timedelta(value=_no_input, unit='ns', days=0, seconds=0,
        microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        return init_pd_timedelta(value * hrzkw__ipkwq)
    return impl_timedelta


@intrinsic
def init_pd_timedelta(typingctx, value):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        timedelta = cgutils.create_struct_proxy(typ)(context, builder)
        timedelta.value = args[0]
        return timedelta._getvalue()
    return PDTimeDeltaType()(value), codegen


make_attribute_wrapper(PDTimeDeltaType, 'value', '_value')


@overload_attribute(PDTimeDeltaType, 'value')
@overload_attribute(PDTimeDeltaType, 'delta')
def pd_timedelta_get_value(td):

    def impl(td):
        return td._value
    return impl


@overload_attribute(PDTimeDeltaType, 'days')
def pd_timedelta_get_days(td):

    def impl(td):
        return td._value // (1000 * 1000 * 1000 * 60 * 60 * 24)
    return impl


@overload_attribute(PDTimeDeltaType, 'seconds')
def pd_timedelta_get_seconds(td):

    def impl(td):
        return td._value // (1000 * 1000 * 1000) % (60 * 60 * 24)
    return impl


@overload_attribute(PDTimeDeltaType, 'microseconds')
def pd_timedelta_get_microseconds(td):

    def impl(td):
        return td._value // 1000 % 1000000
    return impl


@overload_attribute(PDTimeDeltaType, 'nanoseconds')
def pd_timedelta_get_nanoseconds(td):

    def impl(td):
        return td._value % 1000
    return impl


@register_jitable
def _to_hours_pd_td(td):
    return td._value // (1000 * 1000 * 1000 * 60 * 60) % 24


@register_jitable
def _to_minutes_pd_td(td):
    return td._value // (1000 * 1000 * 1000 * 60) % 60


@register_jitable
def _to_seconds_pd_td(td):
    return td._value // (1000 * 1000 * 1000) % 60


@register_jitable
def _to_milliseconds_pd_td(td):
    return td._value // (1000 * 1000) % 1000


@register_jitable
def _to_microseconds_pd_td(td):
    return td._value // 1000 % 1000


Components = namedtuple('Components', ['days', 'hours', 'minutes',
    'seconds', 'milliseconds', 'microseconds', 'nanoseconds'], defaults=[0,
    0, 0, 0, 0, 0, 0])


@overload_attribute(PDTimeDeltaType, 'components', no_unliteral=True)
def pd_timedelta_get_components(td):

    def impl(td):
        a = Components(td.days, _to_hours_pd_td(td), _to_minutes_pd_td(td),
            _to_seconds_pd_td(td), _to_milliseconds_pd_td(td),
            _to_microseconds_pd_td(td), td.nanoseconds)
        return a
    return impl


@overload_method(PDTimeDeltaType, '__hash__', no_unliteral=True)
def pd_td___hash__(td):

    def impl(td):
        return hash(td._value)
    return impl


@overload_method(PDTimeDeltaType, 'to_numpy', no_unliteral=True)
@overload_method(PDTimeDeltaType, 'to_timedelta64', no_unliteral=True)
def pd_td_to_numpy(td):
    from bodo.hiframes.pd_timestamp_ext import integer_to_timedelta64

    def impl(td):
        return integer_to_timedelta64(td.value)
    return impl


@overload_method(PDTimeDeltaType, 'to_pytimedelta', no_unliteral=True)
def pd_td_to_pytimedelta(td):

    def impl(td):
        return datetime.timedelta(microseconds=np.int64(td._value / 1000))
    return impl


@overload_method(PDTimeDeltaType, 'total_seconds', no_unliteral=True)
def pd_td_total_seconds(td):

    def impl(td):
        return td._value // 1000 / 10 ** 6
    return impl


def overload_add_operator_datetime_timedelta(lhs, rhs):
    if lhs == pd_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            val = lhs.value + rhs.value
            return pd.Timedelta(val)
        return impl
    if lhs == pd_timedelta_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            olplw__nuv = (rhs.microseconds + (rhs.seconds + rhs.days * 60 *
                60 * 24) * 1000 * 1000) * 1000
            val = lhs.value + olplw__nuv
            return pd.Timedelta(val)
        return impl
    if lhs == datetime_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            glccb__cxwog = (lhs.microseconds + (lhs.seconds + lhs.days * 60 *
                60 * 24) * 1000 * 1000) * 1000
            val = glccb__cxwog + rhs.value
            return pd.Timedelta(val)
        return impl
    if lhs == pd_timedelta_type and rhs == datetime_datetime_type:
        from bodo.hiframes.pd_timestamp_ext import compute_pd_timestamp

        def impl(lhs, rhs):
            bfm__yfv = rhs.toordinal()
            jlsyk__zobm = rhs.second + rhs.minute * 60 + rhs.hour * 3600
            pvk__vza = rhs.microsecond
            kuu__hpbl = lhs.value // 1000
            xtac__yvty = lhs.nanoseconds
            bnl__egg = pvk__vza + kuu__hpbl
            ciui__yey = 1000000 * (bfm__yfv * 86400 + jlsyk__zobm) + bnl__egg
            ldsec__dbs = xtac__yvty
            return compute_pd_timestamp(ciui__yey, ldsec__dbs)
        return impl
    if lhs == datetime_datetime_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            return lhs + rhs.to_pytimedelta()
        return impl
    if lhs == datetime_timedelta_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            d = lhs.days + rhs.days
            s = lhs.seconds + rhs.seconds
            us = lhs.microseconds + rhs.microseconds
            return datetime.timedelta(d, s, us)
        return impl
    if lhs == datetime_timedelta_type and rhs == datetime_datetime_type:

        def impl(lhs, rhs):
            xbz__toj = datetime.timedelta(rhs.toordinal(), hours=rhs.hour,
                minutes=rhs.minute, seconds=rhs.second, microseconds=rhs.
                microsecond)
            xbz__toj = xbz__toj + lhs
            jpvwi__xeen, ojjhh__rfsad = divmod(xbz__toj.seconds, 3600)
            eeqz__brly, kxbbz__wikvw = divmod(ojjhh__rfsad, 60)
            if 0 < xbz__toj.days <= _MAXORDINAL:
                d = bodo.hiframes.datetime_date_ext.fromordinal_impl(xbz__toj
                    .days)
                return datetime.datetime(d.year, d.month, d.day,
                    jpvwi__xeen, eeqz__brly, kxbbz__wikvw, xbz__toj.
                    microseconds)
            raise OverflowError('result out of range')
        return impl
    if lhs == datetime_datetime_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            xbz__toj = datetime.timedelta(lhs.toordinal(), hours=lhs.hour,
                minutes=lhs.minute, seconds=lhs.second, microseconds=lhs.
                microsecond)
            xbz__toj = xbz__toj + rhs
            jpvwi__xeen, ojjhh__rfsad = divmod(xbz__toj.seconds, 3600)
            eeqz__brly, kxbbz__wikvw = divmod(ojjhh__rfsad, 60)
            if 0 < xbz__toj.days <= _MAXORDINAL:
                d = bodo.hiframes.datetime_date_ext.fromordinal_impl(xbz__toj
                    .days)
                return datetime.datetime(d.year, d.month, d.day,
                    jpvwi__xeen, eeqz__brly, kxbbz__wikvw, xbz__toj.
                    microseconds)
            raise OverflowError('result out of range')
        return impl


def overload_sub_operator_datetime_timedelta(lhs, rhs):
    if lhs == pd_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            fbam__gcjc = lhs.value - rhs.value
            return pd.Timedelta(fbam__gcjc)
        return impl
    if lhs == pd_timedelta_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            return lhs + -rhs
        return impl
    if lhs == datetime_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            return lhs + -rhs
        return impl
    if lhs == datetime_datetime_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            return lhs + -rhs
        return impl
    if lhs == datetime_timedelta_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            d = lhs.days - rhs.days
            s = lhs.seconds - rhs.seconds
            us = lhs.microseconds - rhs.microseconds
            return datetime.timedelta(d, s, us)
        return impl
    if lhs == datetime_datetime_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            return lhs + -rhs
        return impl
    if lhs == datetime_timedelta_array_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            advwu__gwmw = lhs
            numba.parfors.parfor.init_prange()
            n = len(advwu__gwmw)
            A = alloc_datetime_timedelta_array(n)
            for zzriz__vpy in numba.parfors.parfor.internal_prange(n):
                A[zzriz__vpy] = advwu__gwmw[zzriz__vpy] - rhs
            return A
        return impl


def overload_mul_operator_timedelta(lhs, rhs):
    if lhs == pd_timedelta_type and isinstance(rhs, types.Integer):

        def impl(lhs, rhs):
            return pd.Timedelta(lhs.value * rhs)
        return impl
    elif isinstance(lhs, types.Integer) and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            return pd.Timedelta(rhs.value * lhs)
        return impl
    if lhs == datetime_timedelta_type and isinstance(rhs, types.Integer):

        def impl(lhs, rhs):
            d = lhs.days * rhs
            s = lhs.seconds * rhs
            us = lhs.microseconds * rhs
            return datetime.timedelta(d, s, us)
        return impl
    elif isinstance(lhs, types.Integer) and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            d = lhs * rhs.days
            s = lhs * rhs.seconds
            us = lhs * rhs.microseconds
            return datetime.timedelta(d, s, us)
        return impl


def overload_floordiv_operator_pd_timedelta(lhs, rhs):
    if lhs == pd_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            return lhs.value // rhs.value
        return impl
    elif lhs == pd_timedelta_type and isinstance(rhs, types.Integer):

        def impl(lhs, rhs):
            return pd.Timedelta(lhs.value // rhs)
        return impl


def overload_truediv_operator_pd_timedelta(lhs, rhs):
    if lhs == pd_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            return lhs.value / rhs.value
        return impl
    elif lhs == pd_timedelta_type and isinstance(rhs, types.Integer):

        def impl(lhs, rhs):
            return pd.Timedelta(int(lhs.value / rhs))
        return impl


def overload_mod_operator_timedeltas(lhs, rhs):
    if lhs == pd_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            return pd.Timedelta(lhs.value % rhs.value)
        return impl
    if lhs == datetime_timedelta_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            vfc__xcuac = _to_microseconds(lhs) % _to_microseconds(rhs)
            return datetime.timedelta(0, 0, vfc__xcuac)
        return impl


def pd_create_cmp_op_overload(op):

    def overload_pd_timedelta_cmp(lhs, rhs):
        if lhs == pd_timedelta_type and rhs == pd_timedelta_type:

            def impl(lhs, rhs):
                return op(lhs.value, rhs.value)
            return impl
        if lhs == pd_timedelta_type and rhs == bodo.timedelta64ns:
            return lambda lhs, rhs: op(bodo.hiframes.pd_timestamp_ext.
                integer_to_timedelta64(lhs.value), rhs)
        if lhs == bodo.timedelta64ns and rhs == pd_timedelta_type:
            return lambda lhs, rhs: op(lhs, bodo.hiframes.pd_timestamp_ext.
                integer_to_timedelta64(rhs.value))
    return overload_pd_timedelta_cmp


@overload(operator.neg, no_unliteral=True)
def pd_timedelta_neg(lhs):
    if lhs == pd_timedelta_type:

        def impl(lhs):
            return pd.Timedelta(-lhs.value)
        return impl


@overload(operator.pos, no_unliteral=True)
def pd_timedelta_pos(lhs):
    if lhs == pd_timedelta_type:

        def impl(lhs):
            return lhs
        return impl


@overload(divmod, no_unliteral=True)
def pd_timedelta_divmod(lhs, rhs):
    if lhs == pd_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            okp__sqrbg, vfc__xcuac = divmod(lhs.value, rhs.value)
            return okp__sqrbg, pd.Timedelta(vfc__xcuac)
        return impl


@overload(abs, no_unliteral=True)
def pd_timedelta_abs(lhs):
    if lhs == pd_timedelta_type:

        def impl(lhs):
            if lhs.value < 0:
                return -lhs
            else:
                return lhs
        return impl


class DatetimeTimeDeltaType(types.Type):

    def __init__(self):
        super(DatetimeTimeDeltaType, self).__init__(name=
            'DatetimeTimeDeltaType()')


datetime_timedelta_type = DatetimeTimeDeltaType()


@typeof_impl.register(datetime.timedelta)
def typeof_datetime_timedelta(val, c):
    return datetime_timedelta_type


@register_model(DatetimeTimeDeltaType)
class DatetimeTimeDeltaModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        bpla__yjxy = [('days', types.int64), ('seconds', types.int64), (
            'microseconds', types.int64)]
        super(DatetimeTimeDeltaModel, self).__init__(dmm, fe_type, bpla__yjxy)


@box(DatetimeTimeDeltaType)
def box_datetime_timedelta(typ, val, c):
    xjhnd__rdho = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    ump__nrc = c.pyapi.long_from_longlong(xjhnd__rdho.days)
    ptij__zbo = c.pyapi.long_from_longlong(xjhnd__rdho.seconds)
    smb__owmy = c.pyapi.long_from_longlong(xjhnd__rdho.microseconds)
    tndj__ctjco = c.pyapi.unserialize(c.pyapi.serialize_object(datetime.
        timedelta))
    res = c.pyapi.call_function_objargs(tndj__ctjco, (ump__nrc, ptij__zbo,
        smb__owmy))
    c.pyapi.decref(ump__nrc)
    c.pyapi.decref(ptij__zbo)
    c.pyapi.decref(smb__owmy)
    c.pyapi.decref(tndj__ctjco)
    return res


@unbox(DatetimeTimeDeltaType)
def unbox_datetime_timedelta(typ, val, c):
    ump__nrc = c.pyapi.object_getattr_string(val, 'days')
    ptij__zbo = c.pyapi.object_getattr_string(val, 'seconds')
    smb__owmy = c.pyapi.object_getattr_string(val, 'microseconds')
    odmwf__surmz = c.pyapi.long_as_longlong(ump__nrc)
    vnh__ibp = c.pyapi.long_as_longlong(ptij__zbo)
    nkmj__latwd = c.pyapi.long_as_longlong(smb__owmy)
    xjhnd__rdho = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    xjhnd__rdho.days = odmwf__surmz
    xjhnd__rdho.seconds = vnh__ibp
    xjhnd__rdho.microseconds = nkmj__latwd
    c.pyapi.decref(ump__nrc)
    c.pyapi.decref(ptij__zbo)
    c.pyapi.decref(smb__owmy)
    idie__crgm = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(xjhnd__rdho._getvalue(), is_error=idie__crgm)


@lower_constant(DatetimeTimeDeltaType)
def lower_constant_datetime_timedelta(context, builder, ty, pyval):
    days = context.get_constant(types.int64, pyval.days)
    seconds = context.get_constant(types.int64, pyval.seconds)
    microseconds = context.get_constant(types.int64, pyval.microseconds)
    return lir.Constant.literal_struct([days, seconds, microseconds])


@overload(datetime.timedelta, no_unliteral=True)
def datetime_timedelta(days=0, seconds=0, microseconds=0, milliseconds=0,
    minutes=0, hours=0, weeks=0):

    def impl_timedelta(days=0, seconds=0, microseconds=0, milliseconds=0,
        minutes=0, hours=0, weeks=0):
        d = s = us = 0
        days += weeks * 7
        seconds += minutes * 60 + hours * 3600
        microseconds += milliseconds * 1000
        d = days
        days, seconds = divmod(seconds, 24 * 3600)
        d += days
        s += int(seconds)
        seconds, us = divmod(microseconds, 1000000)
        days, seconds = divmod(seconds, 24 * 3600)
        d += days
        s += seconds
        return init_timedelta(d, s, us)
    return impl_timedelta


@intrinsic
def init_timedelta(typingctx, d, s, us):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        timedelta = cgutils.create_struct_proxy(typ)(context, builder)
        timedelta.days = args[0]
        timedelta.seconds = args[1]
        timedelta.microseconds = args[2]
        return timedelta._getvalue()
    return DatetimeTimeDeltaType()(d, s, us), codegen


make_attribute_wrapper(DatetimeTimeDeltaType, 'days', '_days')
make_attribute_wrapper(DatetimeTimeDeltaType, 'seconds', '_seconds')
make_attribute_wrapper(DatetimeTimeDeltaType, 'microseconds', '_microseconds')


@overload_attribute(DatetimeTimeDeltaType, 'days')
def timedelta_get_days(td):

    def impl(td):
        return td._days
    return impl


@overload_attribute(DatetimeTimeDeltaType, 'seconds')
def timedelta_get_seconds(td):

    def impl(td):
        return td._seconds
    return impl


@overload_attribute(DatetimeTimeDeltaType, 'microseconds')
def timedelta_get_microseconds(td):

    def impl(td):
        return td._microseconds
    return impl


@overload_method(DatetimeTimeDeltaType, 'total_seconds', no_unliteral=True)
def total_seconds(td):

    def impl(td):
        return ((td._days * 86400 + td._seconds) * 10 ** 6 + td._microseconds
            ) / 10 ** 6
    return impl


@overload_method(DatetimeTimeDeltaType, '__hash__', no_unliteral=True)
def __hash__(td):

    def impl(td):
        return hash((td._days, td._seconds, td._microseconds))
    return impl


@register_jitable
def _to_nanoseconds(td):
    return np.int64(((td._days * 86400 + td._seconds) * 1000000 + td.
        _microseconds) * 1000)


@register_jitable
def _to_microseconds(td):
    return (td._days * (24 * 3600) + td._seconds) * 1000000 + td._microseconds


@register_jitable
def _cmp(x, y):
    return 0 if x == y else 1 if x > y else -1


@register_jitable
def _getstate(td):
    return td._days, td._seconds, td._microseconds


@register_jitable
def _divide_and_round(a, b):
    okp__sqrbg, vfc__xcuac = divmod(a, b)
    vfc__xcuac *= 2
    gsli__mlfh = vfc__xcuac > b if b > 0 else vfc__xcuac < b
    if gsli__mlfh or vfc__xcuac == b and okp__sqrbg % 2 == 1:
        okp__sqrbg += 1
    return okp__sqrbg


_MAXORDINAL = 3652059


def overload_floordiv_operator_dt_timedelta(lhs, rhs):
    if lhs == datetime_timedelta_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            us = _to_microseconds(lhs)
            return us // _to_microseconds(rhs)
        return impl
    elif lhs == datetime_timedelta_type and rhs == types.int64:

        def impl(lhs, rhs):
            us = _to_microseconds(lhs)
            return datetime.timedelta(0, 0, us // rhs)
        return impl


def overload_truediv_operator_dt_timedelta(lhs, rhs):
    if lhs == datetime_timedelta_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            us = _to_microseconds(lhs)
            return us / _to_microseconds(rhs)
        return impl
    elif lhs == datetime_timedelta_type and rhs == types.int64:

        def impl(lhs, rhs):
            us = _to_microseconds(lhs)
            return datetime.timedelta(0, 0, _divide_and_round(us, rhs))
        return impl


def create_cmp_op_overload(op):

    def overload_timedelta_cmp(lhs, rhs):
        if lhs == datetime_timedelta_type and rhs == datetime_timedelta_type:

            def impl(lhs, rhs):
                lelzf__wxtoe = _cmp(_getstate(lhs), _getstate(rhs))
                return op(lelzf__wxtoe, 0)
            return impl
    return overload_timedelta_cmp


@overload(operator.neg, no_unliteral=True)
def timedelta_neg(lhs):
    if lhs == datetime_timedelta_type:

        def impl(lhs):
            return datetime.timedelta(-lhs.days, -lhs.seconds, -lhs.
                microseconds)
        return impl


@overload(operator.pos, no_unliteral=True)
def timedelta_pos(lhs):
    if lhs == datetime_timedelta_type:

        def impl(lhs):
            return lhs
        return impl


@overload(divmod, no_unliteral=True)
def timedelta_divmod(lhs, rhs):
    if lhs == datetime_timedelta_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            okp__sqrbg, vfc__xcuac = divmod(_to_microseconds(lhs),
                _to_microseconds(rhs))
            return okp__sqrbg, datetime.timedelta(0, 0, vfc__xcuac)
        return impl


@overload(abs, no_unliteral=True)
def timedelta_abs(lhs):
    if lhs == datetime_timedelta_type:

        def impl(lhs):
            if lhs.days < 0:
                return -lhs
            else:
                return lhs
        return impl


@intrinsic
def cast_numpy_timedelta_to_int(typingctx, val=None):
    assert val in (types.NPTimedelta('ns'), types.int64)

    def codegen(context, builder, signature, args):
        return args[0]
    return types.int64(val), codegen


@overload(bool, no_unliteral=True)
def timedelta_to_bool(timedelta):
    if timedelta != datetime_timedelta_type:
        return
    mon__jzqqo = datetime.timedelta(0)

    def impl(timedelta):
        return timedelta != mon__jzqqo
    return impl


class DatetimeTimeDeltaArrayType(types.ArrayCompatible):

    def __init__(self):
        super(DatetimeTimeDeltaArrayType, self).__init__(name=
            'DatetimeTimeDeltaArrayType()')

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def dtype(self):
        return datetime_timedelta_type

    def copy(self):
        return DatetimeTimeDeltaArrayType()


datetime_timedelta_array_type = DatetimeTimeDeltaArrayType()
types.datetime_timedelta_array_type = datetime_timedelta_array_type
days_data_type = types.Array(types.int64, 1, 'C')
seconds_data_type = types.Array(types.int64, 1, 'C')
microseconds_data_type = types.Array(types.int64, 1, 'C')
nulls_type = types.Array(types.uint8, 1, 'C')


@register_model(DatetimeTimeDeltaArrayType)
class DatetimeTimeDeltaArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        bpla__yjxy = [('days_data', days_data_type), ('seconds_data',
            seconds_data_type), ('microseconds_data',
            microseconds_data_type), ('null_bitmap', nulls_type)]
        models.StructModel.__init__(self, dmm, fe_type, bpla__yjxy)


make_attribute_wrapper(DatetimeTimeDeltaArrayType, 'days_data', '_days_data')
make_attribute_wrapper(DatetimeTimeDeltaArrayType, 'seconds_data',
    '_seconds_data')
make_attribute_wrapper(DatetimeTimeDeltaArrayType, 'microseconds_data',
    '_microseconds_data')
make_attribute_wrapper(DatetimeTimeDeltaArrayType, 'null_bitmap',
    '_null_bitmap')


@overload_method(DatetimeTimeDeltaArrayType, 'copy', no_unliteral=True)
def overload_datetime_timedelta_arr_copy(A):
    return (lambda A: bodo.hiframes.datetime_timedelta_ext.
        init_datetime_timedelta_array(A._days_data.copy(), A._seconds_data.
        copy(), A._microseconds_data.copy(), A._null_bitmap.copy()))


@unbox(DatetimeTimeDeltaArrayType)
def unbox_datetime_timedelta_array(typ, val, c):
    n = bodo.utils.utils.object_length(c, val)
    ngyu__gfpcd = types.Array(types.intp, 1, 'C')
    qdmw__hrq = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        ngyu__gfpcd, [n])
    yst__dnivz = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        ngyu__gfpcd, [n])
    wnami__wdx = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        ngyu__gfpcd, [n])
    kyd__spg = c.builder.udiv(c.builder.add(n, lir.Constant(lir.IntType(64),
        7)), lir.Constant(lir.IntType(64), 8))
    pbrv__klhqo = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        types.Array(types.uint8, 1, 'C'), [kyd__spg])
    qxgx__ythf = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer(), lir.IntType(64), lir.IntType(64).as_pointer(), lir.
        IntType(64).as_pointer(), lir.IntType(64).as_pointer(), lir.IntType
        (8).as_pointer()])
    dhd__lpnm = cgutils.get_or_insert_function(c.builder.module, qxgx__ythf,
        name='unbox_datetime_timedelta_array')
    c.builder.call(dhd__lpnm, [val, n, qdmw__hrq.data, yst__dnivz.data,
        wnami__wdx.data, pbrv__klhqo.data])
    ftxcl__ryygj = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    ftxcl__ryygj.days_data = qdmw__hrq._getvalue()
    ftxcl__ryygj.seconds_data = yst__dnivz._getvalue()
    ftxcl__ryygj.microseconds_data = wnami__wdx._getvalue()
    ftxcl__ryygj.null_bitmap = pbrv__klhqo._getvalue()
    idie__crgm = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(ftxcl__ryygj._getvalue(), is_error=idie__crgm)


@box(DatetimeTimeDeltaArrayType)
def box_datetime_timedelta_array(typ, val, c):
    advwu__gwmw = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    qdmw__hrq = c.context.make_array(types.Array(types.int64, 1, 'C'))(c.
        context, c.builder, advwu__gwmw.days_data)
    yst__dnivz = c.context.make_array(types.Array(types.int64, 1, 'C'))(c.
        context, c.builder, advwu__gwmw.seconds_data).data
    wnami__wdx = c.context.make_array(types.Array(types.int64, 1, 'C'))(c.
        context, c.builder, advwu__gwmw.microseconds_data).data
    axnn__xlets = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, advwu__gwmw.null_bitmap).data
    n = c.builder.extract_value(qdmw__hrq.shape, 0)
    qxgx__ythf = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), lir.
        IntType(64).as_pointer(), lir.IntType(64).as_pointer(), lir.IntType
        (64).as_pointer(), lir.IntType(8).as_pointer()])
    wbhc__xjdpe = cgutils.get_or_insert_function(c.builder.module,
        qxgx__ythf, name='box_datetime_timedelta_array')
    pxx__xrxy = c.builder.call(wbhc__xjdpe, [n, qdmw__hrq.data, yst__dnivz,
        wnami__wdx, axnn__xlets])
    c.context.nrt.decref(c.builder, typ, val)
    return pxx__xrxy


@intrinsic
def init_datetime_timedelta_array(typingctx, days_data, seconds_data,
    microseconds_data, nulls=None):
    assert days_data == types.Array(types.int64, 1, 'C')
    assert seconds_data == types.Array(types.int64, 1, 'C')
    assert microseconds_data == types.Array(types.int64, 1, 'C')
    assert nulls == types.Array(types.uint8, 1, 'C')

    def codegen(context, builder, signature, args):
        smh__sqtv, wnk__uukid, lld__wpim, axmmr__gnlox = args
        qpsjx__pwzu = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        qpsjx__pwzu.days_data = smh__sqtv
        qpsjx__pwzu.seconds_data = wnk__uukid
        qpsjx__pwzu.microseconds_data = lld__wpim
        qpsjx__pwzu.null_bitmap = axmmr__gnlox
        context.nrt.incref(builder, signature.args[0], smh__sqtv)
        context.nrt.incref(builder, signature.args[1], wnk__uukid)
        context.nrt.incref(builder, signature.args[2], lld__wpim)
        context.nrt.incref(builder, signature.args[3], axmmr__gnlox)
        return qpsjx__pwzu._getvalue()
    mocl__tkr = datetime_timedelta_array_type(days_data, seconds_data,
        microseconds_data, nulls)
    return mocl__tkr, codegen


@lower_constant(DatetimeTimeDeltaArrayType)
def lower_constant_datetime_timedelta_arr(context, builder, typ, pyval):
    n = len(pyval)
    qdmw__hrq = np.empty(n, np.int64)
    yst__dnivz = np.empty(n, np.int64)
    wnami__wdx = np.empty(n, np.int64)
    evlv__fqz = np.empty(n + 7 >> 3, np.uint8)
    for zzriz__vpy, s in enumerate(pyval):
        dsjg__pryj = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(evlv__fqz, zzriz__vpy, int(not
            dsjg__pryj))
        if not dsjg__pryj:
            qdmw__hrq[zzriz__vpy] = s.days
            yst__dnivz[zzriz__vpy] = s.seconds
            wnami__wdx[zzriz__vpy] = s.microseconds
    fpspq__exb = context.get_constant_generic(builder, days_data_type,
        qdmw__hrq)
    bqtqh__egz = context.get_constant_generic(builder, seconds_data_type,
        yst__dnivz)
    nsn__oyq = context.get_constant_generic(builder, microseconds_data_type,
        wnami__wdx)
    lvuj__arh = context.get_constant_generic(builder, nulls_type, evlv__fqz)
    return lir.Constant.literal_struct([fpspq__exb, bqtqh__egz, nsn__oyq,
        lvuj__arh])


@numba.njit(no_cpython_wrapper=True)
def alloc_datetime_timedelta_array(n):
    qdmw__hrq = np.empty(n, dtype=np.int64)
    yst__dnivz = np.empty(n, dtype=np.int64)
    wnami__wdx = np.empty(n, dtype=np.int64)
    nulls = np.full(n + 7 >> 3, 255, np.uint8)
    return init_datetime_timedelta_array(qdmw__hrq, yst__dnivz, wnami__wdx,
        nulls)


def alloc_datetime_timedelta_array_equiv(self, scope, equiv_set, loc, args, kws
    ):
    assert len(args) == 1 and not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_datetime_timedelta_ext_alloc_datetime_timedelta_array
    ) = alloc_datetime_timedelta_array_equiv


@overload(operator.getitem, no_unliteral=True)
def dt_timedelta_arr_getitem(A, ind):
    if A != datetime_timedelta_array_type:
        return
    if isinstance(ind, types.Integer):

        def impl_int(A, ind):
            return datetime.timedelta(days=A._days_data[ind], seconds=A.
                _seconds_data[ind], microseconds=A._microseconds_data[ind])
        return impl_int
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:

        def impl_bool(A, ind):
            mdi__efpw = bodo.utils.conversion.coerce_to_ndarray(ind)
            msnfk__ecuga = A._null_bitmap
            cgi__upgft = A._days_data[mdi__efpw]
            rkd__jmxa = A._seconds_data[mdi__efpw]
            qjgb__npcfu = A._microseconds_data[mdi__efpw]
            n = len(cgi__upgft)
            mgsvf__pad = get_new_null_mask_bool_index(msnfk__ecuga, ind, n)
            return init_datetime_timedelta_array(cgi__upgft, rkd__jmxa,
                qjgb__npcfu, mgsvf__pad)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            mdi__efpw = bodo.utils.conversion.coerce_to_ndarray(ind)
            msnfk__ecuga = A._null_bitmap
            cgi__upgft = A._days_data[mdi__efpw]
            rkd__jmxa = A._seconds_data[mdi__efpw]
            qjgb__npcfu = A._microseconds_data[mdi__efpw]
            n = len(cgi__upgft)
            mgsvf__pad = get_new_null_mask_int_index(msnfk__ecuga, mdi__efpw, n
                )
            return init_datetime_timedelta_array(cgi__upgft, rkd__jmxa,
                qjgb__npcfu, mgsvf__pad)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            n = len(A._days_data)
            msnfk__ecuga = A._null_bitmap
            cgi__upgft = np.ascontiguousarray(A._days_data[ind])
            rkd__jmxa = np.ascontiguousarray(A._seconds_data[ind])
            qjgb__npcfu = np.ascontiguousarray(A._microseconds_data[ind])
            mgsvf__pad = get_new_null_mask_slice_index(msnfk__ecuga, ind, n)
            return init_datetime_timedelta_array(cgi__upgft, rkd__jmxa,
                qjgb__npcfu, mgsvf__pad)
        return impl_slice
    raise BodoError(
        f'getitem for DatetimeTimedeltaArray with indexing type {ind} not supported.'
        )


@overload(operator.setitem, no_unliteral=True)
def dt_timedelta_arr_setitem(A, ind, val):
    if A != datetime_timedelta_array_type:
        return
    if val == types.none or isinstance(val, types.optional):
        return
    sim__perb = (
        f"setitem for DatetimeTimedeltaArray with indexing type {ind} received an incorrect 'value' type {val}."
        )
    if isinstance(ind, types.Integer):
        if types.unliteral(val) == datetime_timedelta_type:

            def impl(A, ind, val):
                A._days_data[ind] = val._days
                A._seconds_data[ind] = val._seconds
                A._microseconds_data[ind] = val._microseconds
                bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap, ind, 1)
            return impl
        else:
            raise BodoError(sim__perb)
    if not (is_iterable_type(val) and val.dtype == bodo.
        datetime_timedelta_type or types.unliteral(val) ==
        datetime_timedelta_type):
        raise BodoError(sim__perb)
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        if types.unliteral(val) == datetime_timedelta_type:

            def impl_arr_ind_scalar(A, ind, val):
                n = len(A)
                for zzriz__vpy in range(n):
                    A._days_data[ind[zzriz__vpy]] = val._days
                    A._seconds_data[ind[zzriz__vpy]] = val._seconds
                    A._microseconds_data[ind[zzriz__vpy]] = val._microseconds
                    bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                        ind[zzriz__vpy], 1)
            return impl_arr_ind_scalar
        else:

            def impl_arr_ind(A, ind, val):
                val = bodo.utils.conversion.coerce_to_array(val,
                    use_nullable_array=True)
                n = len(val._days_data)
                for zzriz__vpy in range(n):
                    A._days_data[ind[zzriz__vpy]] = val._days_data[zzriz__vpy]
                    A._seconds_data[ind[zzriz__vpy]] = val._seconds_data[
                        zzriz__vpy]
                    A._microseconds_data[ind[zzriz__vpy]
                        ] = val._microseconds_data[zzriz__vpy]
                    ikp__dnc = bodo.libs.int_arr_ext.get_bit_bitmap_arr(val
                        ._null_bitmap, zzriz__vpy)
                    bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                        ind[zzriz__vpy], ikp__dnc)
            return impl_arr_ind
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        if types.unliteral(val) == datetime_timedelta_type:

            def impl_bool_ind_mask_scalar(A, ind, val):
                n = len(ind)
                for zzriz__vpy in range(n):
                    if not bodo.libs.array_kernels.isna(ind, zzriz__vpy
                        ) and ind[zzriz__vpy]:
                        A._days_data[zzriz__vpy] = val._days
                        A._seconds_data[zzriz__vpy] = val._seconds
                        A._microseconds_data[zzriz__vpy] = val._microseconds
                        bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                            zzriz__vpy, 1)
            return impl_bool_ind_mask_scalar
        else:

            def impl_bool_ind_mask(A, ind, val):
                val = bodo.utils.conversion.coerce_to_array(val,
                    use_nullable_array=True)
                n = len(ind)
                xjmgo__vnxg = 0
                for zzriz__vpy in range(n):
                    if not bodo.libs.array_kernels.isna(ind, zzriz__vpy
                        ) and ind[zzriz__vpy]:
                        A._days_data[zzriz__vpy] = val._days_data[xjmgo__vnxg]
                        A._seconds_data[zzriz__vpy] = val._seconds_data[
                            xjmgo__vnxg]
                        A._microseconds_data[zzriz__vpy
                            ] = val._microseconds_data[xjmgo__vnxg]
                        ikp__dnc = bodo.libs.int_arr_ext.get_bit_bitmap_arr(val
                            ._null_bitmap, xjmgo__vnxg)
                        bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                            zzriz__vpy, ikp__dnc)
                        xjmgo__vnxg += 1
            return impl_bool_ind_mask
    if isinstance(ind, types.SliceType):
        if types.unliteral(val) == datetime_timedelta_type:

            def impl_slice_scalar(A, ind, val):
                ewms__nwbu = numba.cpython.unicode._normalize_slice(ind, len(A)
                    )
                for zzriz__vpy in range(ewms__nwbu.start, ewms__nwbu.stop,
                    ewms__nwbu.step):
                    A._days_data[zzriz__vpy] = val._days
                    A._seconds_data[zzriz__vpy] = val._seconds
                    A._microseconds_data[zzriz__vpy] = val._microseconds
                    bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                        zzriz__vpy, 1)
            return impl_slice_scalar
        else:

            def impl_slice_mask(A, ind, val):
                val = bodo.utils.conversion.coerce_to_array(val,
                    use_nullable_array=True)
                n = len(A._days_data)
                A._days_data[ind] = val._days_data
                A._seconds_data[ind] = val._seconds_data
                A._microseconds_data[ind] = val._microseconds_data
                jhdbh__ujsv = val._null_bitmap.copy()
                setitem_slice_index_null_bits(A._null_bitmap, jhdbh__ujsv,
                    ind, n)
            return impl_slice_mask
    raise BodoError(
        f'setitem for DatetimeTimedeltaArray with indexing type {ind} not supported.'
        )


@overload(len, no_unliteral=True)
def overload_len_datetime_timedelta_arr(A):
    if A == datetime_timedelta_array_type:
        return lambda A: len(A._days_data)


@overload_attribute(DatetimeTimeDeltaArrayType, 'shape')
def overload_datetime_timedelta_arr_shape(A):
    return lambda A: (len(A._days_data),)


@overload_attribute(DatetimeTimeDeltaArrayType, 'nbytes')
def timedelta_arr_nbytes_overload(A):
    return (lambda A: A._days_data.nbytes + A._seconds_data.nbytes + A.
        _microseconds_data.nbytes + A._null_bitmap.nbytes)


def overload_datetime_timedelta_arr_sub(arg1, arg2):
    if (arg1 == datetime_timedelta_array_type and arg2 ==
        datetime_timedelta_type):

        def impl(arg1, arg2):
            advwu__gwmw = arg1
            numba.parfors.parfor.init_prange()
            n = len(advwu__gwmw)
            A = alloc_datetime_timedelta_array(n)
            for zzriz__vpy in numba.parfors.parfor.internal_prange(n):
                A[zzriz__vpy] = advwu__gwmw[zzriz__vpy] - arg2
            return A
        return impl


def create_cmp_op_overload_arr(op):

    def overload_date_arr_cmp(lhs, rhs):
        if op == operator.ne:
            dnqp__jzhcg = True
        else:
            dnqp__jzhcg = False
        if (lhs == datetime_timedelta_array_type and rhs ==
            datetime_timedelta_array_type):

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(lhs)
                fmvej__lepv = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for zzriz__vpy in numba.parfors.parfor.internal_prange(n):
                    pbe__sqh = bodo.libs.array_kernels.isna(lhs, zzriz__vpy)
                    linu__ilp = bodo.libs.array_kernels.isna(rhs, zzriz__vpy)
                    if pbe__sqh or linu__ilp:
                        exa__hfclv = dnqp__jzhcg
                    else:
                        exa__hfclv = op(lhs[zzriz__vpy], rhs[zzriz__vpy])
                    fmvej__lepv[zzriz__vpy] = exa__hfclv
                return fmvej__lepv
            return impl
        elif lhs == datetime_timedelta_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(lhs)
                fmvej__lepv = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for zzriz__vpy in numba.parfors.parfor.internal_prange(n):
                    ikp__dnc = bodo.libs.array_kernels.isna(lhs, zzriz__vpy)
                    if ikp__dnc:
                        exa__hfclv = dnqp__jzhcg
                    else:
                        exa__hfclv = op(lhs[zzriz__vpy], rhs)
                    fmvej__lepv[zzriz__vpy] = exa__hfclv
                return fmvej__lepv
            return impl
        elif rhs == datetime_timedelta_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(rhs)
                fmvej__lepv = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for zzriz__vpy in numba.parfors.parfor.internal_prange(n):
                    ikp__dnc = bodo.libs.array_kernels.isna(rhs, zzriz__vpy)
                    if ikp__dnc:
                        exa__hfclv = dnqp__jzhcg
                    else:
                        exa__hfclv = op(lhs, rhs[zzriz__vpy])
                    fmvej__lepv[zzriz__vpy] = exa__hfclv
                return fmvej__lepv
            return impl
    return overload_date_arr_cmp


timedelta_unsupported_attrs = ['asm8', 'resolution_string', 'freq',
    'is_populated']
timedelta_unsupported_methods = ['isoformat']


def _intstall_pd_timedelta_unsupported():
    from bodo.utils.typing import create_unsupported_overload
    for puc__lig in timedelta_unsupported_attrs:
        wrwi__duzf = 'pandas.Timedelta.' + puc__lig
        overload_attribute(PDTimeDeltaType, puc__lig)(
            create_unsupported_overload(wrwi__duzf))
    for uqhfn__vqxky in timedelta_unsupported_methods:
        wrwi__duzf = 'pandas.Timedelta.' + uqhfn__vqxky
        overload_method(PDTimeDeltaType, uqhfn__vqxky)(
            create_unsupported_overload(wrwi__duzf + '()'))


_intstall_pd_timedelta_unsupported()
