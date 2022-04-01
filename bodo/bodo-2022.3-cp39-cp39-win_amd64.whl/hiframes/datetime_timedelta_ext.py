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
        hfo__qffvt = [('value', types.int64)]
        super(PDTimeDeltaModel, self).__init__(dmm, fe_type, hfo__qffvt)


@box(PDTimeDeltaType)
def box_pd_timedelta(typ, val, c):
    ukyf__dkch = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    uur__ogc = c.pyapi.long_from_longlong(ukyf__dkch.value)
    fpw__hwj = c.pyapi.unserialize(c.pyapi.serialize_object(pd.Timedelta))
    res = c.pyapi.call_function_objargs(fpw__hwj, (uur__ogc,))
    c.pyapi.decref(uur__ogc)
    c.pyapi.decref(fpw__hwj)
    return res


@unbox(PDTimeDeltaType)
def unbox_pd_timedelta(typ, val, c):
    uur__ogc = c.pyapi.object_getattr_string(val, 'value')
    twbrm__sap = c.pyapi.long_as_longlong(uur__ogc)
    ukyf__dkch = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    ukyf__dkch.value = twbrm__sap
    c.pyapi.decref(uur__ogc)
    hqizl__revql = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(ukyf__dkch._getvalue(), is_error=hqizl__revql)


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
            aots__zsk = 1000 * microseconds
            return init_pd_timedelta(aots__zsk)
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
            aots__zsk = 1000 * microseconds
            return init_pd_timedelta(aots__zsk)
        return impl_timedelta_datetime
    if not is_overload_constant_str(unit):
        raise BodoError('pd.to_timedelta(): unit should be a constant string')
    unit = pd._libs.tslibs.timedeltas.parse_timedelta_unit(
        get_overload_const_str(unit))
    aexa__ecnk, tipn__uciyl = pd._libs.tslibs.conversion.precision_from_unit(
        unit)

    def impl_timedelta(value=_no_input, unit='ns', days=0, seconds=0,
        microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        return init_pd_timedelta(value * aexa__ecnk)
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
            yma__aojb = (rhs.microseconds + (rhs.seconds + rhs.days * 60 * 
                60 * 24) * 1000 * 1000) * 1000
            val = lhs.value + yma__aojb
            return pd.Timedelta(val)
        return impl
    if lhs == datetime_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            cddm__rdw = (lhs.microseconds + (lhs.seconds + lhs.days * 60 * 
                60 * 24) * 1000 * 1000) * 1000
            val = cddm__rdw + rhs.value
            return pd.Timedelta(val)
        return impl
    if lhs == pd_timedelta_type and rhs == datetime_datetime_type:
        from bodo.hiframes.pd_timestamp_ext import compute_pd_timestamp

        def impl(lhs, rhs):
            plh__frotf = rhs.toordinal()
            elqn__lns = rhs.second + rhs.minute * 60 + rhs.hour * 3600
            qnxvp__twi = rhs.microsecond
            kpfo__nixe = lhs.value // 1000
            xmb__vhu = lhs.nanoseconds
            wjcmb__ocbb = qnxvp__twi + kpfo__nixe
            knlru__gtwvk = 1000000 * (plh__frotf * 86400 + elqn__lns
                ) + wjcmb__ocbb
            flhf__esdx = xmb__vhu
            return compute_pd_timestamp(knlru__gtwvk, flhf__esdx)
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
            hzip__oxyyp = datetime.timedelta(rhs.toordinal(), hours=rhs.
                hour, minutes=rhs.minute, seconds=rhs.second, microseconds=
                rhs.microsecond)
            hzip__oxyyp = hzip__oxyyp + lhs
            ddmt__zagn, mwd__rov = divmod(hzip__oxyyp.seconds, 3600)
            mxl__rcxg, pwsms__wwtbp = divmod(mwd__rov, 60)
            if 0 < hzip__oxyyp.days <= _MAXORDINAL:
                d = bodo.hiframes.datetime_date_ext.fromordinal_impl(
                    hzip__oxyyp.days)
                return datetime.datetime(d.year, d.month, d.day, ddmt__zagn,
                    mxl__rcxg, pwsms__wwtbp, hzip__oxyyp.microseconds)
            raise OverflowError('result out of range')
        return impl
    if lhs == datetime_datetime_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            hzip__oxyyp = datetime.timedelta(lhs.toordinal(), hours=lhs.
                hour, minutes=lhs.minute, seconds=lhs.second, microseconds=
                lhs.microsecond)
            hzip__oxyyp = hzip__oxyyp + rhs
            ddmt__zagn, mwd__rov = divmod(hzip__oxyyp.seconds, 3600)
            mxl__rcxg, pwsms__wwtbp = divmod(mwd__rov, 60)
            if 0 < hzip__oxyyp.days <= _MAXORDINAL:
                d = bodo.hiframes.datetime_date_ext.fromordinal_impl(
                    hzip__oxyyp.days)
                return datetime.datetime(d.year, d.month, d.day, ddmt__zagn,
                    mxl__rcxg, pwsms__wwtbp, hzip__oxyyp.microseconds)
            raise OverflowError('result out of range')
        return impl


def overload_sub_operator_datetime_timedelta(lhs, rhs):
    if lhs == pd_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            mitw__aiqs = lhs.value - rhs.value
            return pd.Timedelta(mitw__aiqs)
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
            ybx__cjecw = lhs
            numba.parfors.parfor.init_prange()
            n = len(ybx__cjecw)
            A = alloc_datetime_timedelta_array(n)
            for iktx__exkm in numba.parfors.parfor.internal_prange(n):
                A[iktx__exkm] = ybx__cjecw[iktx__exkm] - rhs
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
            wav__tkq = _to_microseconds(lhs) % _to_microseconds(rhs)
            return datetime.timedelta(0, 0, wav__tkq)
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
            jpsyh__ozj, wav__tkq = divmod(lhs.value, rhs.value)
            return jpsyh__ozj, pd.Timedelta(wav__tkq)
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
        hfo__qffvt = [('days', types.int64), ('seconds', types.int64), (
            'microseconds', types.int64)]
        super(DatetimeTimeDeltaModel, self).__init__(dmm, fe_type, hfo__qffvt)


@box(DatetimeTimeDeltaType)
def box_datetime_timedelta(typ, val, c):
    ukyf__dkch = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    npj__zfb = c.pyapi.long_from_longlong(ukyf__dkch.days)
    vomp__weqgk = c.pyapi.long_from_longlong(ukyf__dkch.seconds)
    fpw__teyqs = c.pyapi.long_from_longlong(ukyf__dkch.microseconds)
    fpw__hwj = c.pyapi.unserialize(c.pyapi.serialize_object(datetime.timedelta)
        )
    res = c.pyapi.call_function_objargs(fpw__hwj, (npj__zfb, vomp__weqgk,
        fpw__teyqs))
    c.pyapi.decref(npj__zfb)
    c.pyapi.decref(vomp__weqgk)
    c.pyapi.decref(fpw__teyqs)
    c.pyapi.decref(fpw__hwj)
    return res


@unbox(DatetimeTimeDeltaType)
def unbox_datetime_timedelta(typ, val, c):
    npj__zfb = c.pyapi.object_getattr_string(val, 'days')
    vomp__weqgk = c.pyapi.object_getattr_string(val, 'seconds')
    fpw__teyqs = c.pyapi.object_getattr_string(val, 'microseconds')
    aoacs__ychu = c.pyapi.long_as_longlong(npj__zfb)
    xkoto__hufkv = c.pyapi.long_as_longlong(vomp__weqgk)
    mbnwu__mwn = c.pyapi.long_as_longlong(fpw__teyqs)
    ukyf__dkch = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    ukyf__dkch.days = aoacs__ychu
    ukyf__dkch.seconds = xkoto__hufkv
    ukyf__dkch.microseconds = mbnwu__mwn
    c.pyapi.decref(npj__zfb)
    c.pyapi.decref(vomp__weqgk)
    c.pyapi.decref(fpw__teyqs)
    hqizl__revql = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(ukyf__dkch._getvalue(), is_error=hqizl__revql)


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
    jpsyh__ozj, wav__tkq = divmod(a, b)
    wav__tkq *= 2
    joee__xot = wav__tkq > b if b > 0 else wav__tkq < b
    if joee__xot or wav__tkq == b and jpsyh__ozj % 2 == 1:
        jpsyh__ozj += 1
    return jpsyh__ozj


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
                wvx__yvlx = _cmp(_getstate(lhs), _getstate(rhs))
                return op(wvx__yvlx, 0)
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
            jpsyh__ozj, wav__tkq = divmod(_to_microseconds(lhs),
                _to_microseconds(rhs))
            return jpsyh__ozj, datetime.timedelta(0, 0, wav__tkq)
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
    bnjo__ermt = datetime.timedelta(0)

    def impl(timedelta):
        return timedelta != bnjo__ermt
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
        hfo__qffvt = [('days_data', days_data_type), ('seconds_data',
            seconds_data_type), ('microseconds_data',
            microseconds_data_type), ('null_bitmap', nulls_type)]
        models.StructModel.__init__(self, dmm, fe_type, hfo__qffvt)


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
    knoc__ptc = types.Array(types.intp, 1, 'C')
    buu__axah = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        knoc__ptc, [n])
    rgy__thph = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        knoc__ptc, [n])
    isaz__uepx = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        knoc__ptc, [n])
    xlqs__rjnb = c.builder.udiv(c.builder.add(n, lir.Constant(lir.IntType(
        64), 7)), lir.Constant(lir.IntType(64), 8))
    dem__efv = bodo.utils.utils._empty_nd_impl(c.context, c.builder, types.
        Array(types.uint8, 1, 'C'), [xlqs__rjnb])
    wpk__snm = lir.FunctionType(lir.VoidType(), [lir.IntType(8).as_pointer(
        ), lir.IntType(64), lir.IntType(64).as_pointer(), lir.IntType(64).
        as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
        as_pointer()])
    wmibj__iky = cgutils.get_or_insert_function(c.builder.module, wpk__snm,
        name='unbox_datetime_timedelta_array')
    c.builder.call(wmibj__iky, [val, n, buu__axah.data, rgy__thph.data,
        isaz__uepx.data, dem__efv.data])
    wlgt__onq = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    wlgt__onq.days_data = buu__axah._getvalue()
    wlgt__onq.seconds_data = rgy__thph._getvalue()
    wlgt__onq.microseconds_data = isaz__uepx._getvalue()
    wlgt__onq.null_bitmap = dem__efv._getvalue()
    hqizl__revql = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(wlgt__onq._getvalue(), is_error=hqizl__revql)


@box(DatetimeTimeDeltaArrayType)
def box_datetime_timedelta_array(typ, val, c):
    ybx__cjecw = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    buu__axah = c.context.make_array(types.Array(types.int64, 1, 'C'))(c.
        context, c.builder, ybx__cjecw.days_data)
    rgy__thph = c.context.make_array(types.Array(types.int64, 1, 'C'))(c.
        context, c.builder, ybx__cjecw.seconds_data).data
    isaz__uepx = c.context.make_array(types.Array(types.int64, 1, 'C'))(c.
        context, c.builder, ybx__cjecw.microseconds_data).data
    pfo__ollh = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, ybx__cjecw.null_bitmap).data
    n = c.builder.extract_value(buu__axah.shape, 0)
    wpk__snm = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), lir.
        IntType(64).as_pointer(), lir.IntType(64).as_pointer(), lir.IntType
        (64).as_pointer(), lir.IntType(8).as_pointer()])
    aeff__xjw = cgutils.get_or_insert_function(c.builder.module, wpk__snm,
        name='box_datetime_timedelta_array')
    wjz__oeavm = c.builder.call(aeff__xjw, [n, buu__axah.data, rgy__thph,
        isaz__uepx, pfo__ollh])
    c.context.nrt.decref(c.builder, typ, val)
    return wjz__oeavm


@intrinsic
def init_datetime_timedelta_array(typingctx, days_data, seconds_data,
    microseconds_data, nulls=None):
    assert days_data == types.Array(types.int64, 1, 'C')
    assert seconds_data == types.Array(types.int64, 1, 'C')
    assert microseconds_data == types.Array(types.int64, 1, 'C')
    assert nulls == types.Array(types.uint8, 1, 'C')

    def codegen(context, builder, signature, args):
        cvnzq__brs, uacj__qpmb, rmlww__syuzc, viei__wotxz = args
        yafvs__qochu = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        yafvs__qochu.days_data = cvnzq__brs
        yafvs__qochu.seconds_data = uacj__qpmb
        yafvs__qochu.microseconds_data = rmlww__syuzc
        yafvs__qochu.null_bitmap = viei__wotxz
        context.nrt.incref(builder, signature.args[0], cvnzq__brs)
        context.nrt.incref(builder, signature.args[1], uacj__qpmb)
        context.nrt.incref(builder, signature.args[2], rmlww__syuzc)
        context.nrt.incref(builder, signature.args[3], viei__wotxz)
        return yafvs__qochu._getvalue()
    ray__lkqi = datetime_timedelta_array_type(days_data, seconds_data,
        microseconds_data, nulls)
    return ray__lkqi, codegen


@lower_constant(DatetimeTimeDeltaArrayType)
def lower_constant_datetime_timedelta_arr(context, builder, typ, pyval):
    n = len(pyval)
    buu__axah = np.empty(n, np.int64)
    rgy__thph = np.empty(n, np.int64)
    isaz__uepx = np.empty(n, np.int64)
    obwr__xfgq = np.empty(n + 7 >> 3, np.uint8)
    for iktx__exkm, s in enumerate(pyval):
        eekwh__gxs = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(obwr__xfgq, iktx__exkm, int(
            not eekwh__gxs))
        if not eekwh__gxs:
            buu__axah[iktx__exkm] = s.days
            rgy__thph[iktx__exkm] = s.seconds
            isaz__uepx[iktx__exkm] = s.microseconds
    yuis__djr = context.get_constant_generic(builder, days_data_type, buu__axah
        )
    ruvy__kele = context.get_constant_generic(builder, seconds_data_type,
        rgy__thph)
    bpj__nbv = context.get_constant_generic(builder, microseconds_data_type,
        isaz__uepx)
    nic__tps = context.get_constant_generic(builder, nulls_type, obwr__xfgq)
    return lir.Constant.literal_struct([yuis__djr, ruvy__kele, bpj__nbv,
        nic__tps])


@numba.njit(no_cpython_wrapper=True)
def alloc_datetime_timedelta_array(n):
    buu__axah = np.empty(n, dtype=np.int64)
    rgy__thph = np.empty(n, dtype=np.int64)
    isaz__uepx = np.empty(n, dtype=np.int64)
    nulls = np.full(n + 7 >> 3, 255, np.uint8)
    return init_datetime_timedelta_array(buu__axah, rgy__thph, isaz__uepx,
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
            cxi__sxew = bodo.utils.conversion.coerce_to_ndarray(ind)
            zjax__ezno = A._null_bitmap
            svdrv__kenjc = A._days_data[cxi__sxew]
            tvwmn__moq = A._seconds_data[cxi__sxew]
            rdp__liyi = A._microseconds_data[cxi__sxew]
            n = len(svdrv__kenjc)
            ying__dhdvp = get_new_null_mask_bool_index(zjax__ezno, ind, n)
            return init_datetime_timedelta_array(svdrv__kenjc, tvwmn__moq,
                rdp__liyi, ying__dhdvp)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            cxi__sxew = bodo.utils.conversion.coerce_to_ndarray(ind)
            zjax__ezno = A._null_bitmap
            svdrv__kenjc = A._days_data[cxi__sxew]
            tvwmn__moq = A._seconds_data[cxi__sxew]
            rdp__liyi = A._microseconds_data[cxi__sxew]
            n = len(svdrv__kenjc)
            ying__dhdvp = get_new_null_mask_int_index(zjax__ezno, cxi__sxew, n)
            return init_datetime_timedelta_array(svdrv__kenjc, tvwmn__moq,
                rdp__liyi, ying__dhdvp)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            n = len(A._days_data)
            zjax__ezno = A._null_bitmap
            svdrv__kenjc = np.ascontiguousarray(A._days_data[ind])
            tvwmn__moq = np.ascontiguousarray(A._seconds_data[ind])
            rdp__liyi = np.ascontiguousarray(A._microseconds_data[ind])
            ying__dhdvp = get_new_null_mask_slice_index(zjax__ezno, ind, n)
            return init_datetime_timedelta_array(svdrv__kenjc, tvwmn__moq,
                rdp__liyi, ying__dhdvp)
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
    rffp__aegw = (
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
            raise BodoError(rffp__aegw)
    if not (is_iterable_type(val) and val.dtype == bodo.
        datetime_timedelta_type or types.unliteral(val) ==
        datetime_timedelta_type):
        raise BodoError(rffp__aegw)
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        if types.unliteral(val) == datetime_timedelta_type:

            def impl_arr_ind_scalar(A, ind, val):
                n = len(A)
                for iktx__exkm in range(n):
                    A._days_data[ind[iktx__exkm]] = val._days
                    A._seconds_data[ind[iktx__exkm]] = val._seconds
                    A._microseconds_data[ind[iktx__exkm]] = val._microseconds
                    bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                        ind[iktx__exkm], 1)
            return impl_arr_ind_scalar
        else:

            def impl_arr_ind(A, ind, val):
                val = bodo.utils.conversion.coerce_to_array(val,
                    use_nullable_array=True)
                n = len(val._days_data)
                for iktx__exkm in range(n):
                    A._days_data[ind[iktx__exkm]] = val._days_data[iktx__exkm]
                    A._seconds_data[ind[iktx__exkm]] = val._seconds_data[
                        iktx__exkm]
                    A._microseconds_data[ind[iktx__exkm]
                        ] = val._microseconds_data[iktx__exkm]
                    esgb__gvbv = bodo.libs.int_arr_ext.get_bit_bitmap_arr(val
                        ._null_bitmap, iktx__exkm)
                    bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                        ind[iktx__exkm], esgb__gvbv)
            return impl_arr_ind
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        if types.unliteral(val) == datetime_timedelta_type:

            def impl_bool_ind_mask_scalar(A, ind, val):
                n = len(ind)
                for iktx__exkm in range(n):
                    if not bodo.libs.array_kernels.isna(ind, iktx__exkm
                        ) and ind[iktx__exkm]:
                        A._days_data[iktx__exkm] = val._days
                        A._seconds_data[iktx__exkm] = val._seconds
                        A._microseconds_data[iktx__exkm] = val._microseconds
                        bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                            iktx__exkm, 1)
            return impl_bool_ind_mask_scalar
        else:

            def impl_bool_ind_mask(A, ind, val):
                val = bodo.utils.conversion.coerce_to_array(val,
                    use_nullable_array=True)
                n = len(ind)
                laz__dwfb = 0
                for iktx__exkm in range(n):
                    if not bodo.libs.array_kernels.isna(ind, iktx__exkm
                        ) and ind[iktx__exkm]:
                        A._days_data[iktx__exkm] = val._days_data[laz__dwfb]
                        A._seconds_data[iktx__exkm] = val._seconds_data[
                            laz__dwfb]
                        A._microseconds_data[iktx__exkm
                            ] = val._microseconds_data[laz__dwfb]
                        esgb__gvbv = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                            val._null_bitmap, laz__dwfb)
                        bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                            iktx__exkm, esgb__gvbv)
                        laz__dwfb += 1
            return impl_bool_ind_mask
    if isinstance(ind, types.SliceType):
        if types.unliteral(val) == datetime_timedelta_type:

            def impl_slice_scalar(A, ind, val):
                crtuv__baz = numba.cpython.unicode._normalize_slice(ind, len(A)
                    )
                for iktx__exkm in range(crtuv__baz.start, crtuv__baz.stop,
                    crtuv__baz.step):
                    A._days_data[iktx__exkm] = val._days
                    A._seconds_data[iktx__exkm] = val._seconds
                    A._microseconds_data[iktx__exkm] = val._microseconds
                    bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                        iktx__exkm, 1)
            return impl_slice_scalar
        else:

            def impl_slice_mask(A, ind, val):
                val = bodo.utils.conversion.coerce_to_array(val,
                    use_nullable_array=True)
                n = len(A._days_data)
                A._days_data[ind] = val._days_data
                A._seconds_data[ind] = val._seconds_data
                A._microseconds_data[ind] = val._microseconds_data
                wzn__jkucw = val._null_bitmap.copy()
                setitem_slice_index_null_bits(A._null_bitmap, wzn__jkucw,
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
            ybx__cjecw = arg1
            numba.parfors.parfor.init_prange()
            n = len(ybx__cjecw)
            A = alloc_datetime_timedelta_array(n)
            for iktx__exkm in numba.parfors.parfor.internal_prange(n):
                A[iktx__exkm] = ybx__cjecw[iktx__exkm] - arg2
            return A
        return impl


def create_cmp_op_overload_arr(op):

    def overload_date_arr_cmp(lhs, rhs):
        if op == operator.ne:
            bdyo__rvnzy = True
        else:
            bdyo__rvnzy = False
        if (lhs == datetime_timedelta_array_type and rhs ==
            datetime_timedelta_array_type):

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(lhs)
                qaoax__tkyr = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for iktx__exkm in numba.parfors.parfor.internal_prange(n):
                    qizk__yinfn = bodo.libs.array_kernels.isna(lhs, iktx__exkm)
                    syr__nbfex = bodo.libs.array_kernels.isna(rhs, iktx__exkm)
                    if qizk__yinfn or syr__nbfex:
                        sxwh__bpozq = bdyo__rvnzy
                    else:
                        sxwh__bpozq = op(lhs[iktx__exkm], rhs[iktx__exkm])
                    qaoax__tkyr[iktx__exkm] = sxwh__bpozq
                return qaoax__tkyr
            return impl
        elif lhs == datetime_timedelta_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(lhs)
                qaoax__tkyr = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for iktx__exkm in numba.parfors.parfor.internal_prange(n):
                    esgb__gvbv = bodo.libs.array_kernels.isna(lhs, iktx__exkm)
                    if esgb__gvbv:
                        sxwh__bpozq = bdyo__rvnzy
                    else:
                        sxwh__bpozq = op(lhs[iktx__exkm], rhs)
                    qaoax__tkyr[iktx__exkm] = sxwh__bpozq
                return qaoax__tkyr
            return impl
        elif rhs == datetime_timedelta_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(rhs)
                qaoax__tkyr = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for iktx__exkm in numba.parfors.parfor.internal_prange(n):
                    esgb__gvbv = bodo.libs.array_kernels.isna(rhs, iktx__exkm)
                    if esgb__gvbv:
                        sxwh__bpozq = bdyo__rvnzy
                    else:
                        sxwh__bpozq = op(lhs, rhs[iktx__exkm])
                    qaoax__tkyr[iktx__exkm] = sxwh__bpozq
                return qaoax__tkyr
            return impl
    return overload_date_arr_cmp


timedelta_unsupported_attrs = ['asm8', 'resolution_string', 'freq',
    'is_populated']
timedelta_unsupported_methods = ['isoformat']


def _intstall_pd_timedelta_unsupported():
    from bodo.utils.typing import create_unsupported_overload
    for qir__uxpg in timedelta_unsupported_attrs:
        aeiv__pwqpo = 'pandas.Timedelta.' + qir__uxpg
        overload_attribute(PDTimeDeltaType, qir__uxpg)(
            create_unsupported_overload(aeiv__pwqpo))
    for iwtf__ajwy in timedelta_unsupported_methods:
        aeiv__pwqpo = 'pandas.Timedelta.' + iwtf__ajwy
        overload_method(PDTimeDeltaType, iwtf__ajwy)(
            create_unsupported_overload(aeiv__pwqpo + '()'))


_intstall_pd_timedelta_unsupported()
