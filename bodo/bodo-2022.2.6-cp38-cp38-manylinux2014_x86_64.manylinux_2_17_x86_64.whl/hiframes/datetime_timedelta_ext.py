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
        orw__ihdwl = [('value', types.int64)]
        super(PDTimeDeltaModel, self).__init__(dmm, fe_type, orw__ihdwl)


@box(PDTimeDeltaType)
def box_pd_timedelta(typ, val, c):
    yslyp__uye = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    ktb__zcg = c.pyapi.long_from_longlong(yslyp__uye.value)
    unbhw__aumm = c.pyapi.unserialize(c.pyapi.serialize_object(pd.Timedelta))
    res = c.pyapi.call_function_objargs(unbhw__aumm, (ktb__zcg,))
    c.pyapi.decref(ktb__zcg)
    c.pyapi.decref(unbhw__aumm)
    return res


@unbox(PDTimeDeltaType)
def unbox_pd_timedelta(typ, val, c):
    ktb__zcg = c.pyapi.object_getattr_string(val, 'value')
    evk__tbi = c.pyapi.long_as_longlong(ktb__zcg)
    yslyp__uye = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    yslyp__uye.value = evk__tbi
    c.pyapi.decref(ktb__zcg)
    vcp__qoyta = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(yslyp__uye._getvalue(), is_error=vcp__qoyta)


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
            ojb__njilv = 1000 * microseconds
            return init_pd_timedelta(ojb__njilv)
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
            ojb__njilv = 1000 * microseconds
            return init_pd_timedelta(ojb__njilv)
        return impl_timedelta_datetime
    if not is_overload_constant_str(unit):
        raise BodoError('pd.to_timedelta(): unit should be a constant string')
    unit = pd._libs.tslibs.timedeltas.parse_timedelta_unit(
        get_overload_const_str(unit))
    tnj__ffcm, rowl__efqog = pd._libs.tslibs.conversion.precision_from_unit(
        unit)

    def impl_timedelta(value=_no_input, unit='ns', days=0, seconds=0,
        microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        return init_pd_timedelta(value * tnj__ffcm)
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
            hzkzi__tzog = (rhs.microseconds + (rhs.seconds + rhs.days * 60 *
                60 * 24) * 1000 * 1000) * 1000
            val = lhs.value + hzkzi__tzog
            return pd.Timedelta(val)
        return impl
    if lhs == datetime_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            gjd__jxbl = (lhs.microseconds + (lhs.seconds + lhs.days * 60 * 
                60 * 24) * 1000 * 1000) * 1000
            val = gjd__jxbl + rhs.value
            return pd.Timedelta(val)
        return impl
    if lhs == pd_timedelta_type and rhs == datetime_datetime_type:
        from bodo.hiframes.pd_timestamp_ext import compute_pd_timestamp

        def impl(lhs, rhs):
            iuhm__bafn = rhs.toordinal()
            stt__czd = rhs.second + rhs.minute * 60 + rhs.hour * 3600
            dbybq__zyb = rhs.microsecond
            ofg__kuiwg = lhs.value // 1000
            mpez__cmfrm = lhs.nanoseconds
            qsei__wmrn = dbybq__zyb + ofg__kuiwg
            uicuw__pia = 1000000 * (iuhm__bafn * 86400 + stt__czd) + qsei__wmrn
            wkmpt__xzjh = mpez__cmfrm
            return compute_pd_timestamp(uicuw__pia, wkmpt__xzjh)
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
            adqev__ltmwt = datetime.timedelta(rhs.toordinal(), hours=rhs.
                hour, minutes=rhs.minute, seconds=rhs.second, microseconds=
                rhs.microsecond)
            adqev__ltmwt = adqev__ltmwt + lhs
            bkfqp__fqi, pgt__hioa = divmod(adqev__ltmwt.seconds, 3600)
            qbcsr__vtd, fqr__bvhk = divmod(pgt__hioa, 60)
            if 0 < adqev__ltmwt.days <= _MAXORDINAL:
                d = bodo.hiframes.datetime_date_ext.fromordinal_impl(
                    adqev__ltmwt.days)
                return datetime.datetime(d.year, d.month, d.day, bkfqp__fqi,
                    qbcsr__vtd, fqr__bvhk, adqev__ltmwt.microseconds)
            raise OverflowError('result out of range')
        return impl
    if lhs == datetime_datetime_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            adqev__ltmwt = datetime.timedelta(lhs.toordinal(), hours=lhs.
                hour, minutes=lhs.minute, seconds=lhs.second, microseconds=
                lhs.microsecond)
            adqev__ltmwt = adqev__ltmwt + rhs
            bkfqp__fqi, pgt__hioa = divmod(adqev__ltmwt.seconds, 3600)
            qbcsr__vtd, fqr__bvhk = divmod(pgt__hioa, 60)
            if 0 < adqev__ltmwt.days <= _MAXORDINAL:
                d = bodo.hiframes.datetime_date_ext.fromordinal_impl(
                    adqev__ltmwt.days)
                return datetime.datetime(d.year, d.month, d.day, bkfqp__fqi,
                    qbcsr__vtd, fqr__bvhk, adqev__ltmwt.microseconds)
            raise OverflowError('result out of range')
        return impl


def overload_sub_operator_datetime_timedelta(lhs, rhs):
    if lhs == pd_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            ntzg__pjpbh = lhs.value - rhs.value
            return pd.Timedelta(ntzg__pjpbh)
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
            bypw__ies = lhs
            numba.parfors.parfor.init_prange()
            n = len(bypw__ies)
            A = alloc_datetime_timedelta_array(n)
            for stsn__gxqut in numba.parfors.parfor.internal_prange(n):
                A[stsn__gxqut] = bypw__ies[stsn__gxqut] - rhs
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
            arbqp__pyte = _to_microseconds(lhs) % _to_microseconds(rhs)
            return datetime.timedelta(0, 0, arbqp__pyte)
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
            ziuj__kgrtd, arbqp__pyte = divmod(lhs.value, rhs.value)
            return ziuj__kgrtd, pd.Timedelta(arbqp__pyte)
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
        orw__ihdwl = [('days', types.int64), ('seconds', types.int64), (
            'microseconds', types.int64)]
        super(DatetimeTimeDeltaModel, self).__init__(dmm, fe_type, orw__ihdwl)


@box(DatetimeTimeDeltaType)
def box_datetime_timedelta(typ, val, c):
    yslyp__uye = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    nah__frs = c.pyapi.long_from_longlong(yslyp__uye.days)
    qys__qadx = c.pyapi.long_from_longlong(yslyp__uye.seconds)
    dhbi__aru = c.pyapi.long_from_longlong(yslyp__uye.microseconds)
    unbhw__aumm = c.pyapi.unserialize(c.pyapi.serialize_object(datetime.
        timedelta))
    res = c.pyapi.call_function_objargs(unbhw__aumm, (nah__frs, qys__qadx,
        dhbi__aru))
    c.pyapi.decref(nah__frs)
    c.pyapi.decref(qys__qadx)
    c.pyapi.decref(dhbi__aru)
    c.pyapi.decref(unbhw__aumm)
    return res


@unbox(DatetimeTimeDeltaType)
def unbox_datetime_timedelta(typ, val, c):
    nah__frs = c.pyapi.object_getattr_string(val, 'days')
    qys__qadx = c.pyapi.object_getattr_string(val, 'seconds')
    dhbi__aru = c.pyapi.object_getattr_string(val, 'microseconds')
    bax__dnwbn = c.pyapi.long_as_longlong(nah__frs)
    wmi__rvngx = c.pyapi.long_as_longlong(qys__qadx)
    epoye__hgf = c.pyapi.long_as_longlong(dhbi__aru)
    yslyp__uye = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    yslyp__uye.days = bax__dnwbn
    yslyp__uye.seconds = wmi__rvngx
    yslyp__uye.microseconds = epoye__hgf
    c.pyapi.decref(nah__frs)
    c.pyapi.decref(qys__qadx)
    c.pyapi.decref(dhbi__aru)
    vcp__qoyta = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(yslyp__uye._getvalue(), is_error=vcp__qoyta)


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
    ziuj__kgrtd, arbqp__pyte = divmod(a, b)
    arbqp__pyte *= 2
    can__tnkp = arbqp__pyte > b if b > 0 else arbqp__pyte < b
    if can__tnkp or arbqp__pyte == b and ziuj__kgrtd % 2 == 1:
        ziuj__kgrtd += 1
    return ziuj__kgrtd


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
                jlpa__ejew = _cmp(_getstate(lhs), _getstate(rhs))
                return op(jlpa__ejew, 0)
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
            ziuj__kgrtd, arbqp__pyte = divmod(_to_microseconds(lhs),
                _to_microseconds(rhs))
            return ziuj__kgrtd, datetime.timedelta(0, 0, arbqp__pyte)
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
    hyp__yhg = datetime.timedelta(0)

    def impl(timedelta):
        return timedelta != hyp__yhg
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
        orw__ihdwl = [('days_data', days_data_type), ('seconds_data',
            seconds_data_type), ('microseconds_data',
            microseconds_data_type), ('null_bitmap', nulls_type)]
        models.StructModel.__init__(self, dmm, fe_type, orw__ihdwl)


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
    rgl__zmgql = types.Array(types.intp, 1, 'C')
    elu__kerr = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        rgl__zmgql, [n])
    wxidn__sbcqb = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        rgl__zmgql, [n])
    zcu__wdqb = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        rgl__zmgql, [n])
    zpz__arc = c.builder.udiv(c.builder.add(n, lir.Constant(lir.IntType(64),
        7)), lir.Constant(lir.IntType(64), 8))
    hpga__pfh = bodo.utils.utils._empty_nd_impl(c.context, c.builder, types
        .Array(types.uint8, 1, 'C'), [zpz__arc])
    uzwva__ipyq = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer(), lir.IntType(64), lir.IntType(64).as_pointer(), lir.
        IntType(64).as_pointer(), lir.IntType(64).as_pointer(), lir.IntType
        (8).as_pointer()])
    czf__vqag = cgutils.get_or_insert_function(c.builder.module,
        uzwva__ipyq, name='unbox_datetime_timedelta_array')
    c.builder.call(czf__vqag, [val, n, elu__kerr.data, wxidn__sbcqb.data,
        zcu__wdqb.data, hpga__pfh.data])
    kxc__fmdvx = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    kxc__fmdvx.days_data = elu__kerr._getvalue()
    kxc__fmdvx.seconds_data = wxidn__sbcqb._getvalue()
    kxc__fmdvx.microseconds_data = zcu__wdqb._getvalue()
    kxc__fmdvx.null_bitmap = hpga__pfh._getvalue()
    vcp__qoyta = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(kxc__fmdvx._getvalue(), is_error=vcp__qoyta)


@box(DatetimeTimeDeltaArrayType)
def box_datetime_timedelta_array(typ, val, c):
    bypw__ies = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    elu__kerr = c.context.make_array(types.Array(types.int64, 1, 'C'))(c.
        context, c.builder, bypw__ies.days_data)
    wxidn__sbcqb = c.context.make_array(types.Array(types.int64, 1, 'C'))(c
        .context, c.builder, bypw__ies.seconds_data).data
    zcu__wdqb = c.context.make_array(types.Array(types.int64, 1, 'C'))(c.
        context, c.builder, bypw__ies.microseconds_data).data
    oake__hsm = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, bypw__ies.null_bitmap).data
    n = c.builder.extract_value(elu__kerr.shape, 0)
    uzwva__ipyq = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), lir.
        IntType(64).as_pointer(), lir.IntType(64).as_pointer(), lir.IntType
        (64).as_pointer(), lir.IntType(8).as_pointer()])
    xysg__brtix = cgutils.get_or_insert_function(c.builder.module,
        uzwva__ipyq, name='box_datetime_timedelta_array')
    qrvh__qoo = c.builder.call(xysg__brtix, [n, elu__kerr.data,
        wxidn__sbcqb, zcu__wdqb, oake__hsm])
    c.context.nrt.decref(c.builder, typ, val)
    return qrvh__qoo


@intrinsic
def init_datetime_timedelta_array(typingctx, days_data, seconds_data,
    microseconds_data, nulls=None):
    assert days_data == types.Array(types.int64, 1, 'C')
    assert seconds_data == types.Array(types.int64, 1, 'C')
    assert microseconds_data == types.Array(types.int64, 1, 'C')
    assert nulls == types.Array(types.uint8, 1, 'C')

    def codegen(context, builder, signature, args):
        uxv__wojw, quu__qnapu, lph__rho, fik__bxngh = args
        unpf__ipzh = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        unpf__ipzh.days_data = uxv__wojw
        unpf__ipzh.seconds_data = quu__qnapu
        unpf__ipzh.microseconds_data = lph__rho
        unpf__ipzh.null_bitmap = fik__bxngh
        context.nrt.incref(builder, signature.args[0], uxv__wojw)
        context.nrt.incref(builder, signature.args[1], quu__qnapu)
        context.nrt.incref(builder, signature.args[2], lph__rho)
        context.nrt.incref(builder, signature.args[3], fik__bxngh)
        return unpf__ipzh._getvalue()
    ctgcq__kygbz = datetime_timedelta_array_type(days_data, seconds_data,
        microseconds_data, nulls)
    return ctgcq__kygbz, codegen


@lower_constant(DatetimeTimeDeltaArrayType)
def lower_constant_datetime_timedelta_arr(context, builder, typ, pyval):
    n = len(pyval)
    elu__kerr = np.empty(n, np.int64)
    wxidn__sbcqb = np.empty(n, np.int64)
    zcu__wdqb = np.empty(n, np.int64)
    pvawy__kzx = np.empty(n + 7 >> 3, np.uint8)
    for stsn__gxqut, s in enumerate(pyval):
        tkd__nbheq = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(pvawy__kzx, stsn__gxqut, int(
            not tkd__nbheq))
        if not tkd__nbheq:
            elu__kerr[stsn__gxqut] = s.days
            wxidn__sbcqb[stsn__gxqut] = s.seconds
            zcu__wdqb[stsn__gxqut] = s.microseconds
    ljbi__qtzd = context.get_constant_generic(builder, days_data_type,
        elu__kerr)
    jqims__vjqlq = context.get_constant_generic(builder, seconds_data_type,
        wxidn__sbcqb)
    goie__zxjoy = context.get_constant_generic(builder,
        microseconds_data_type, zcu__wdqb)
    ttw__mzaeg = context.get_constant_generic(builder, nulls_type, pvawy__kzx)
    return lir.Constant.literal_struct([ljbi__qtzd, jqims__vjqlq,
        goie__zxjoy, ttw__mzaeg])


@numba.njit(no_cpython_wrapper=True)
def alloc_datetime_timedelta_array(n):
    elu__kerr = np.empty(n, dtype=np.int64)
    wxidn__sbcqb = np.empty(n, dtype=np.int64)
    zcu__wdqb = np.empty(n, dtype=np.int64)
    nulls = np.full(n + 7 >> 3, 255, np.uint8)
    return init_datetime_timedelta_array(elu__kerr, wxidn__sbcqb, zcu__wdqb,
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
            byel__omgt = bodo.utils.conversion.coerce_to_ndarray(ind)
            qmy__ydps = A._null_bitmap
            qnvf__yyah = A._days_data[byel__omgt]
            vklgh__sxw = A._seconds_data[byel__omgt]
            aocqq__fustl = A._microseconds_data[byel__omgt]
            n = len(qnvf__yyah)
            voj__jxij = get_new_null_mask_bool_index(qmy__ydps, ind, n)
            return init_datetime_timedelta_array(qnvf__yyah, vklgh__sxw,
                aocqq__fustl, voj__jxij)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            byel__omgt = bodo.utils.conversion.coerce_to_ndarray(ind)
            qmy__ydps = A._null_bitmap
            qnvf__yyah = A._days_data[byel__omgt]
            vklgh__sxw = A._seconds_data[byel__omgt]
            aocqq__fustl = A._microseconds_data[byel__omgt]
            n = len(qnvf__yyah)
            voj__jxij = get_new_null_mask_int_index(qmy__ydps, byel__omgt, n)
            return init_datetime_timedelta_array(qnvf__yyah, vklgh__sxw,
                aocqq__fustl, voj__jxij)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            n = len(A._days_data)
            qmy__ydps = A._null_bitmap
            qnvf__yyah = np.ascontiguousarray(A._days_data[ind])
            vklgh__sxw = np.ascontiguousarray(A._seconds_data[ind])
            aocqq__fustl = np.ascontiguousarray(A._microseconds_data[ind])
            voj__jxij = get_new_null_mask_slice_index(qmy__ydps, ind, n)
            return init_datetime_timedelta_array(qnvf__yyah, vklgh__sxw,
                aocqq__fustl, voj__jxij)
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
    vwpb__vfsz = (
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
            raise BodoError(vwpb__vfsz)
    if not (is_iterable_type(val) and val.dtype == bodo.
        datetime_timedelta_type or types.unliteral(val) ==
        datetime_timedelta_type):
        raise BodoError(vwpb__vfsz)
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        if types.unliteral(val) == datetime_timedelta_type:

            def impl_arr_ind_scalar(A, ind, val):
                n = len(A)
                for stsn__gxqut in range(n):
                    A._days_data[ind[stsn__gxqut]] = val._days
                    A._seconds_data[ind[stsn__gxqut]] = val._seconds
                    A._microseconds_data[ind[stsn__gxqut]] = val._microseconds
                    bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                        ind[stsn__gxqut], 1)
            return impl_arr_ind_scalar
        else:

            def impl_arr_ind(A, ind, val):
                val = bodo.utils.conversion.coerce_to_array(val,
                    use_nullable_array=True)
                n = len(val._days_data)
                for stsn__gxqut in range(n):
                    A._days_data[ind[stsn__gxqut]] = val._days_data[stsn__gxqut
                        ]
                    A._seconds_data[ind[stsn__gxqut]] = val._seconds_data[
                        stsn__gxqut]
                    A._microseconds_data[ind[stsn__gxqut]
                        ] = val._microseconds_data[stsn__gxqut]
                    ovd__afoay = bodo.libs.int_arr_ext.get_bit_bitmap_arr(val
                        ._null_bitmap, stsn__gxqut)
                    bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                        ind[stsn__gxqut], ovd__afoay)
            return impl_arr_ind
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        if types.unliteral(val) == datetime_timedelta_type:

            def impl_bool_ind_mask_scalar(A, ind, val):
                n = len(ind)
                for stsn__gxqut in range(n):
                    if not bodo.libs.array_kernels.isna(ind, stsn__gxqut
                        ) and ind[stsn__gxqut]:
                        A._days_data[stsn__gxqut] = val._days
                        A._seconds_data[stsn__gxqut] = val._seconds
                        A._microseconds_data[stsn__gxqut] = val._microseconds
                        bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                            stsn__gxqut, 1)
            return impl_bool_ind_mask_scalar
        else:

            def impl_bool_ind_mask(A, ind, val):
                val = bodo.utils.conversion.coerce_to_array(val,
                    use_nullable_array=True)
                n = len(ind)
                jveb__hgoz = 0
                for stsn__gxqut in range(n):
                    if not bodo.libs.array_kernels.isna(ind, stsn__gxqut
                        ) and ind[stsn__gxqut]:
                        A._days_data[stsn__gxqut] = val._days_data[jveb__hgoz]
                        A._seconds_data[stsn__gxqut] = val._seconds_data[
                            jveb__hgoz]
                        A._microseconds_data[stsn__gxqut
                            ] = val._microseconds_data[jveb__hgoz]
                        ovd__afoay = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                            val._null_bitmap, jveb__hgoz)
                        bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                            stsn__gxqut, ovd__afoay)
                        jveb__hgoz += 1
            return impl_bool_ind_mask
    if isinstance(ind, types.SliceType):
        if types.unliteral(val) == datetime_timedelta_type:

            def impl_slice_scalar(A, ind, val):
                uuslu__fljri = numba.cpython.unicode._normalize_slice(ind,
                    len(A))
                for stsn__gxqut in range(uuslu__fljri.start, uuslu__fljri.
                    stop, uuslu__fljri.step):
                    A._days_data[stsn__gxqut] = val._days
                    A._seconds_data[stsn__gxqut] = val._seconds
                    A._microseconds_data[stsn__gxqut] = val._microseconds
                    bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                        stsn__gxqut, 1)
            return impl_slice_scalar
        else:

            def impl_slice_mask(A, ind, val):
                val = bodo.utils.conversion.coerce_to_array(val,
                    use_nullable_array=True)
                n = len(A._days_data)
                A._days_data[ind] = val._days_data
                A._seconds_data[ind] = val._seconds_data
                A._microseconds_data[ind] = val._microseconds_data
                khear__zpoaa = val._null_bitmap.copy()
                setitem_slice_index_null_bits(A._null_bitmap, khear__zpoaa,
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
            bypw__ies = arg1
            numba.parfors.parfor.init_prange()
            n = len(bypw__ies)
            A = alloc_datetime_timedelta_array(n)
            for stsn__gxqut in numba.parfors.parfor.internal_prange(n):
                A[stsn__gxqut] = bypw__ies[stsn__gxqut] - arg2
            return A
        return impl


def create_cmp_op_overload_arr(op):

    def overload_date_arr_cmp(lhs, rhs):
        if op == operator.ne:
            vsa__aok = True
        else:
            vsa__aok = False
        if (lhs == datetime_timedelta_array_type and rhs ==
            datetime_timedelta_array_type):

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(lhs)
                srwor__faxw = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for stsn__gxqut in numba.parfors.parfor.internal_prange(n):
                    wrobg__zym = bodo.libs.array_kernels.isna(lhs, stsn__gxqut)
                    nkn__loa = bodo.libs.array_kernels.isna(rhs, stsn__gxqut)
                    if wrobg__zym or nkn__loa:
                        myr__ydwe = vsa__aok
                    else:
                        myr__ydwe = op(lhs[stsn__gxqut], rhs[stsn__gxqut])
                    srwor__faxw[stsn__gxqut] = myr__ydwe
                return srwor__faxw
            return impl
        elif lhs == datetime_timedelta_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(lhs)
                srwor__faxw = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for stsn__gxqut in numba.parfors.parfor.internal_prange(n):
                    ovd__afoay = bodo.libs.array_kernels.isna(lhs, stsn__gxqut)
                    if ovd__afoay:
                        myr__ydwe = vsa__aok
                    else:
                        myr__ydwe = op(lhs[stsn__gxqut], rhs)
                    srwor__faxw[stsn__gxqut] = myr__ydwe
                return srwor__faxw
            return impl
        elif rhs == datetime_timedelta_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(rhs)
                srwor__faxw = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for stsn__gxqut in numba.parfors.parfor.internal_prange(n):
                    ovd__afoay = bodo.libs.array_kernels.isna(rhs, stsn__gxqut)
                    if ovd__afoay:
                        myr__ydwe = vsa__aok
                    else:
                        myr__ydwe = op(lhs, rhs[stsn__gxqut])
                    srwor__faxw[stsn__gxqut] = myr__ydwe
                return srwor__faxw
            return impl
    return overload_date_arr_cmp


timedelta_unsupported_attrs = ['asm8', 'resolution_string', 'freq',
    'is_populated']
timedelta_unsupported_methods = ['isoformat']


def _intstall_pd_timedelta_unsupported():
    from bodo.utils.typing import create_unsupported_overload
    for pbjw__btpd in timedelta_unsupported_attrs:
        stqbe__zmnj = 'pandas.Timedelta.' + pbjw__btpd
        overload_attribute(PDTimeDeltaType, pbjw__btpd)(
            create_unsupported_overload(stqbe__zmnj))
    for huruk__xnh in timedelta_unsupported_methods:
        stqbe__zmnj = 'pandas.Timedelta.' + huruk__xnh
        overload_method(PDTimeDeltaType, huruk__xnh)(
            create_unsupported_overload(stqbe__zmnj + '()'))


_intstall_pd_timedelta_unsupported()
