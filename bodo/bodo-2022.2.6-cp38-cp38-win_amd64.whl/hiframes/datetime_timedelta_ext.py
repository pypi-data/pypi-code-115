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
        xfh__gknvm = [('value', types.int64)]
        super(PDTimeDeltaModel, self).__init__(dmm, fe_type, xfh__gknvm)


@box(PDTimeDeltaType)
def box_pd_timedelta(typ, val, c):
    zirk__ahebn = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    csdrk__zdkb = c.pyapi.long_from_longlong(zirk__ahebn.value)
    mdbo__qxo = c.pyapi.unserialize(c.pyapi.serialize_object(pd.Timedelta))
    res = c.pyapi.call_function_objargs(mdbo__qxo, (csdrk__zdkb,))
    c.pyapi.decref(csdrk__zdkb)
    c.pyapi.decref(mdbo__qxo)
    return res


@unbox(PDTimeDeltaType)
def unbox_pd_timedelta(typ, val, c):
    csdrk__zdkb = c.pyapi.object_getattr_string(val, 'value')
    ypgb__ogb = c.pyapi.long_as_longlong(csdrk__zdkb)
    zirk__ahebn = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    zirk__ahebn.value = ypgb__ogb
    c.pyapi.decref(csdrk__zdkb)
    wssi__vcw = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(zirk__ahebn._getvalue(), is_error=wssi__vcw)


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
            vtgu__ttkqx = 1000 * microseconds
            return init_pd_timedelta(vtgu__ttkqx)
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
            vtgu__ttkqx = 1000 * microseconds
            return init_pd_timedelta(vtgu__ttkqx)
        return impl_timedelta_datetime
    if not is_overload_constant_str(unit):
        raise BodoError('pd.to_timedelta(): unit should be a constant string')
    unit = pd._libs.tslibs.timedeltas.parse_timedelta_unit(
        get_overload_const_str(unit))
    susaf__poh, sdf__apa = pd._libs.tslibs.conversion.precision_from_unit(unit)

    def impl_timedelta(value=_no_input, unit='ns', days=0, seconds=0,
        microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        return init_pd_timedelta(value * susaf__poh)
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
            mxs__vzt = (rhs.microseconds + (rhs.seconds + rhs.days * 60 * 
                60 * 24) * 1000 * 1000) * 1000
            val = lhs.value + mxs__vzt
            return pd.Timedelta(val)
        return impl
    if lhs == datetime_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            xowgt__gip = (lhs.microseconds + (lhs.seconds + lhs.days * 60 *
                60 * 24) * 1000 * 1000) * 1000
            val = xowgt__gip + rhs.value
            return pd.Timedelta(val)
        return impl
    if lhs == pd_timedelta_type and rhs == datetime_datetime_type:
        from bodo.hiframes.pd_timestamp_ext import compute_pd_timestamp

        def impl(lhs, rhs):
            ytohy__cgch = rhs.toordinal()
            sdljs__futg = rhs.second + rhs.minute * 60 + rhs.hour * 3600
            xsxd__zgp = rhs.microsecond
            aik__wqxry = lhs.value // 1000
            wxg__mqxx = lhs.nanoseconds
            sfjw__rmxch = xsxd__zgp + aik__wqxry
            veuw__egawc = 1000000 * (ytohy__cgch * 86400 + sdljs__futg
                ) + sfjw__rmxch
            mbrf__kisfb = wxg__mqxx
            return compute_pd_timestamp(veuw__egawc, mbrf__kisfb)
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
            hiluk__nvyt = datetime.timedelta(rhs.toordinal(), hours=rhs.
                hour, minutes=rhs.minute, seconds=rhs.second, microseconds=
                rhs.microsecond)
            hiluk__nvyt = hiluk__nvyt + lhs
            cltnz__kdwv, bzuoe__gryib = divmod(hiluk__nvyt.seconds, 3600)
            civop__zawi, fsv__cbbc = divmod(bzuoe__gryib, 60)
            if 0 < hiluk__nvyt.days <= _MAXORDINAL:
                d = bodo.hiframes.datetime_date_ext.fromordinal_impl(
                    hiluk__nvyt.days)
                return datetime.datetime(d.year, d.month, d.day,
                    cltnz__kdwv, civop__zawi, fsv__cbbc, hiluk__nvyt.
                    microseconds)
            raise OverflowError('result out of range')
        return impl
    if lhs == datetime_datetime_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            hiluk__nvyt = datetime.timedelta(lhs.toordinal(), hours=lhs.
                hour, minutes=lhs.minute, seconds=lhs.second, microseconds=
                lhs.microsecond)
            hiluk__nvyt = hiluk__nvyt + rhs
            cltnz__kdwv, bzuoe__gryib = divmod(hiluk__nvyt.seconds, 3600)
            civop__zawi, fsv__cbbc = divmod(bzuoe__gryib, 60)
            if 0 < hiluk__nvyt.days <= _MAXORDINAL:
                d = bodo.hiframes.datetime_date_ext.fromordinal_impl(
                    hiluk__nvyt.days)
                return datetime.datetime(d.year, d.month, d.day,
                    cltnz__kdwv, civop__zawi, fsv__cbbc, hiluk__nvyt.
                    microseconds)
            raise OverflowError('result out of range')
        return impl


def overload_sub_operator_datetime_timedelta(lhs, rhs):
    if lhs == pd_timedelta_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            zufg__ddc = lhs.value - rhs.value
            return pd.Timedelta(zufg__ddc)
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
            yzgxo__lquqy = lhs
            numba.parfors.parfor.init_prange()
            n = len(yzgxo__lquqy)
            A = alloc_datetime_timedelta_array(n)
            for hznof__thvl in numba.parfors.parfor.internal_prange(n):
                A[hznof__thvl] = yzgxo__lquqy[hznof__thvl] - rhs
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
            oofgd__rzzzs = _to_microseconds(lhs) % _to_microseconds(rhs)
            return datetime.timedelta(0, 0, oofgd__rzzzs)
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
            cahz__czgr, oofgd__rzzzs = divmod(lhs.value, rhs.value)
            return cahz__czgr, pd.Timedelta(oofgd__rzzzs)
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
        xfh__gknvm = [('days', types.int64), ('seconds', types.int64), (
            'microseconds', types.int64)]
        super(DatetimeTimeDeltaModel, self).__init__(dmm, fe_type, xfh__gknvm)


@box(DatetimeTimeDeltaType)
def box_datetime_timedelta(typ, val, c):
    zirk__ahebn = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    oluv__twp = c.pyapi.long_from_longlong(zirk__ahebn.days)
    itje__zvnlh = c.pyapi.long_from_longlong(zirk__ahebn.seconds)
    fokv__zmtw = c.pyapi.long_from_longlong(zirk__ahebn.microseconds)
    mdbo__qxo = c.pyapi.unserialize(c.pyapi.serialize_object(datetime.
        timedelta))
    res = c.pyapi.call_function_objargs(mdbo__qxo, (oluv__twp, itje__zvnlh,
        fokv__zmtw))
    c.pyapi.decref(oluv__twp)
    c.pyapi.decref(itje__zvnlh)
    c.pyapi.decref(fokv__zmtw)
    c.pyapi.decref(mdbo__qxo)
    return res


@unbox(DatetimeTimeDeltaType)
def unbox_datetime_timedelta(typ, val, c):
    oluv__twp = c.pyapi.object_getattr_string(val, 'days')
    itje__zvnlh = c.pyapi.object_getattr_string(val, 'seconds')
    fokv__zmtw = c.pyapi.object_getattr_string(val, 'microseconds')
    gnat__plsts = c.pyapi.long_as_longlong(oluv__twp)
    yruht__gccu = c.pyapi.long_as_longlong(itje__zvnlh)
    xvqu__mdfx = c.pyapi.long_as_longlong(fokv__zmtw)
    zirk__ahebn = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    zirk__ahebn.days = gnat__plsts
    zirk__ahebn.seconds = yruht__gccu
    zirk__ahebn.microseconds = xvqu__mdfx
    c.pyapi.decref(oluv__twp)
    c.pyapi.decref(itje__zvnlh)
    c.pyapi.decref(fokv__zmtw)
    wssi__vcw = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(zirk__ahebn._getvalue(), is_error=wssi__vcw)


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
    cahz__czgr, oofgd__rzzzs = divmod(a, b)
    oofgd__rzzzs *= 2
    vpd__gqoq = oofgd__rzzzs > b if b > 0 else oofgd__rzzzs < b
    if vpd__gqoq or oofgd__rzzzs == b and cahz__czgr % 2 == 1:
        cahz__czgr += 1
    return cahz__czgr


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
                qhtan__paq = _cmp(_getstate(lhs), _getstate(rhs))
                return op(qhtan__paq, 0)
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
            cahz__czgr, oofgd__rzzzs = divmod(_to_microseconds(lhs),
                _to_microseconds(rhs))
            return cahz__czgr, datetime.timedelta(0, 0, oofgd__rzzzs)
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
    umh__cdqu = datetime.timedelta(0)

    def impl(timedelta):
        return timedelta != umh__cdqu
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
        xfh__gknvm = [('days_data', days_data_type), ('seconds_data',
            seconds_data_type), ('microseconds_data',
            microseconds_data_type), ('null_bitmap', nulls_type)]
        models.StructModel.__init__(self, dmm, fe_type, xfh__gknvm)


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
    zpsux__bale = types.Array(types.intp, 1, 'C')
    snlzm__olig = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        zpsux__bale, [n])
    iex__mngu = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        zpsux__bale, [n])
    rfwe__khpj = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        zpsux__bale, [n])
    ebzf__bgqdn = c.builder.udiv(c.builder.add(n, lir.Constant(lir.IntType(
        64), 7)), lir.Constant(lir.IntType(64), 8))
    zare__uypmf = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        types.Array(types.uint8, 1, 'C'), [ebzf__bgqdn])
    oqbiz__xixfq = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer(), lir.IntType(64), lir.IntType(64).as_pointer(), lir.
        IntType(64).as_pointer(), lir.IntType(64).as_pointer(), lir.IntType
        (8).as_pointer()])
    xfka__ivipx = cgutils.get_or_insert_function(c.builder.module,
        oqbiz__xixfq, name='unbox_datetime_timedelta_array')
    c.builder.call(xfka__ivipx, [val, n, snlzm__olig.data, iex__mngu.data,
        rfwe__khpj.data, zare__uypmf.data])
    daals__erk = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    daals__erk.days_data = snlzm__olig._getvalue()
    daals__erk.seconds_data = iex__mngu._getvalue()
    daals__erk.microseconds_data = rfwe__khpj._getvalue()
    daals__erk.null_bitmap = zare__uypmf._getvalue()
    wssi__vcw = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(daals__erk._getvalue(), is_error=wssi__vcw)


@box(DatetimeTimeDeltaArrayType)
def box_datetime_timedelta_array(typ, val, c):
    yzgxo__lquqy = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    snlzm__olig = c.context.make_array(types.Array(types.int64, 1, 'C'))(c.
        context, c.builder, yzgxo__lquqy.days_data)
    iex__mngu = c.context.make_array(types.Array(types.int64, 1, 'C'))(c.
        context, c.builder, yzgxo__lquqy.seconds_data).data
    rfwe__khpj = c.context.make_array(types.Array(types.int64, 1, 'C'))(c.
        context, c.builder, yzgxo__lquqy.microseconds_data).data
    knm__yzzji = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, yzgxo__lquqy.null_bitmap).data
    n = c.builder.extract_value(snlzm__olig.shape, 0)
    oqbiz__xixfq = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), lir.
        IntType(64).as_pointer(), lir.IntType(64).as_pointer(), lir.IntType
        (64).as_pointer(), lir.IntType(8).as_pointer()])
    njhk__rrxzg = cgutils.get_or_insert_function(c.builder.module,
        oqbiz__xixfq, name='box_datetime_timedelta_array')
    wec__deph = c.builder.call(njhk__rrxzg, [n, snlzm__olig.data, iex__mngu,
        rfwe__khpj, knm__yzzji])
    c.context.nrt.decref(c.builder, typ, val)
    return wec__deph


@intrinsic
def init_datetime_timedelta_array(typingctx, days_data, seconds_data,
    microseconds_data, nulls=None):
    assert days_data == types.Array(types.int64, 1, 'C')
    assert seconds_data == types.Array(types.int64, 1, 'C')
    assert microseconds_data == types.Array(types.int64, 1, 'C')
    assert nulls == types.Array(types.uint8, 1, 'C')

    def codegen(context, builder, signature, args):
        wtp__hvtn, ccj__wfgbk, ibok__myh, jgs__hufn = args
        yfa__qkrd = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        yfa__qkrd.days_data = wtp__hvtn
        yfa__qkrd.seconds_data = ccj__wfgbk
        yfa__qkrd.microseconds_data = ibok__myh
        yfa__qkrd.null_bitmap = jgs__hufn
        context.nrt.incref(builder, signature.args[0], wtp__hvtn)
        context.nrt.incref(builder, signature.args[1], ccj__wfgbk)
        context.nrt.incref(builder, signature.args[2], ibok__myh)
        context.nrt.incref(builder, signature.args[3], jgs__hufn)
        return yfa__qkrd._getvalue()
    gcnv__zda = datetime_timedelta_array_type(days_data, seconds_data,
        microseconds_data, nulls)
    return gcnv__zda, codegen


@lower_constant(DatetimeTimeDeltaArrayType)
def lower_constant_datetime_timedelta_arr(context, builder, typ, pyval):
    n = len(pyval)
    snlzm__olig = np.empty(n, np.int64)
    iex__mngu = np.empty(n, np.int64)
    rfwe__khpj = np.empty(n, np.int64)
    dbwlm__ftau = np.empty(n + 7 >> 3, np.uint8)
    for hznof__thvl, s in enumerate(pyval):
        rsma__xbsl = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(dbwlm__ftau, hznof__thvl, int(
            not rsma__xbsl))
        if not rsma__xbsl:
            snlzm__olig[hznof__thvl] = s.days
            iex__mngu[hznof__thvl] = s.seconds
            rfwe__khpj[hznof__thvl] = s.microseconds
    jrdz__hpoy = context.get_constant_generic(builder, days_data_type,
        snlzm__olig)
    hzwxk__zwz = context.get_constant_generic(builder, seconds_data_type,
        iex__mngu)
    nehuo__sga = context.get_constant_generic(builder,
        microseconds_data_type, rfwe__khpj)
    zdoy__ayds = context.get_constant_generic(builder, nulls_type, dbwlm__ftau)
    return lir.Constant.literal_struct([jrdz__hpoy, hzwxk__zwz, nehuo__sga,
        zdoy__ayds])


@numba.njit(no_cpython_wrapper=True)
def alloc_datetime_timedelta_array(n):
    snlzm__olig = np.empty(n, dtype=np.int64)
    iex__mngu = np.empty(n, dtype=np.int64)
    rfwe__khpj = np.empty(n, dtype=np.int64)
    nulls = np.full(n + 7 >> 3, 255, np.uint8)
    return init_datetime_timedelta_array(snlzm__olig, iex__mngu, rfwe__khpj,
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
            nri__pdb = bodo.utils.conversion.coerce_to_ndarray(ind)
            qjwud__geju = A._null_bitmap
            humsd__zokgk = A._days_data[nri__pdb]
            diq__xaxq = A._seconds_data[nri__pdb]
            evkn__dotll = A._microseconds_data[nri__pdb]
            n = len(humsd__zokgk)
            roi__cqz = get_new_null_mask_bool_index(qjwud__geju, ind, n)
            return init_datetime_timedelta_array(humsd__zokgk, diq__xaxq,
                evkn__dotll, roi__cqz)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            nri__pdb = bodo.utils.conversion.coerce_to_ndarray(ind)
            qjwud__geju = A._null_bitmap
            humsd__zokgk = A._days_data[nri__pdb]
            diq__xaxq = A._seconds_data[nri__pdb]
            evkn__dotll = A._microseconds_data[nri__pdb]
            n = len(humsd__zokgk)
            roi__cqz = get_new_null_mask_int_index(qjwud__geju, nri__pdb, n)
            return init_datetime_timedelta_array(humsd__zokgk, diq__xaxq,
                evkn__dotll, roi__cqz)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            n = len(A._days_data)
            qjwud__geju = A._null_bitmap
            humsd__zokgk = np.ascontiguousarray(A._days_data[ind])
            diq__xaxq = np.ascontiguousarray(A._seconds_data[ind])
            evkn__dotll = np.ascontiguousarray(A._microseconds_data[ind])
            roi__cqz = get_new_null_mask_slice_index(qjwud__geju, ind, n)
            return init_datetime_timedelta_array(humsd__zokgk, diq__xaxq,
                evkn__dotll, roi__cqz)
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
    mwqva__afrm = (
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
            raise BodoError(mwqva__afrm)
    if not (is_iterable_type(val) and val.dtype == bodo.
        datetime_timedelta_type or types.unliteral(val) ==
        datetime_timedelta_type):
        raise BodoError(mwqva__afrm)
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        if types.unliteral(val) == datetime_timedelta_type:

            def impl_arr_ind_scalar(A, ind, val):
                n = len(A)
                for hznof__thvl in range(n):
                    A._days_data[ind[hznof__thvl]] = val._days
                    A._seconds_data[ind[hznof__thvl]] = val._seconds
                    A._microseconds_data[ind[hznof__thvl]] = val._microseconds
                    bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                        ind[hznof__thvl], 1)
            return impl_arr_ind_scalar
        else:

            def impl_arr_ind(A, ind, val):
                val = bodo.utils.conversion.coerce_to_array(val,
                    use_nullable_array=True)
                n = len(val._days_data)
                for hznof__thvl in range(n):
                    A._days_data[ind[hznof__thvl]] = val._days_data[hznof__thvl
                        ]
                    A._seconds_data[ind[hznof__thvl]] = val._seconds_data[
                        hznof__thvl]
                    A._microseconds_data[ind[hznof__thvl]
                        ] = val._microseconds_data[hznof__thvl]
                    jdge__cmury = bodo.libs.int_arr_ext.get_bit_bitmap_arr(val
                        ._null_bitmap, hznof__thvl)
                    bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                        ind[hznof__thvl], jdge__cmury)
            return impl_arr_ind
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        if types.unliteral(val) == datetime_timedelta_type:

            def impl_bool_ind_mask_scalar(A, ind, val):
                n = len(ind)
                for hznof__thvl in range(n):
                    if not bodo.libs.array_kernels.isna(ind, hznof__thvl
                        ) and ind[hznof__thvl]:
                        A._days_data[hznof__thvl] = val._days
                        A._seconds_data[hznof__thvl] = val._seconds
                        A._microseconds_data[hznof__thvl] = val._microseconds
                        bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                            hznof__thvl, 1)
            return impl_bool_ind_mask_scalar
        else:

            def impl_bool_ind_mask(A, ind, val):
                val = bodo.utils.conversion.coerce_to_array(val,
                    use_nullable_array=True)
                n = len(ind)
                twric__rbe = 0
                for hznof__thvl in range(n):
                    if not bodo.libs.array_kernels.isna(ind, hznof__thvl
                        ) and ind[hznof__thvl]:
                        A._days_data[hznof__thvl] = val._days_data[twric__rbe]
                        A._seconds_data[hznof__thvl] = val._seconds_data[
                            twric__rbe]
                        A._microseconds_data[hznof__thvl
                            ] = val._microseconds_data[twric__rbe]
                        jdge__cmury = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                            val._null_bitmap, twric__rbe)
                        bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                            hznof__thvl, jdge__cmury)
                        twric__rbe += 1
            return impl_bool_ind_mask
    if isinstance(ind, types.SliceType):
        if types.unliteral(val) == datetime_timedelta_type:

            def impl_slice_scalar(A, ind, val):
                vun__etzfa = numba.cpython.unicode._normalize_slice(ind, len(A)
                    )
                for hznof__thvl in range(vun__etzfa.start, vun__etzfa.stop,
                    vun__etzfa.step):
                    A._days_data[hznof__thvl] = val._days
                    A._seconds_data[hznof__thvl] = val._seconds
                    A._microseconds_data[hznof__thvl] = val._microseconds
                    bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap,
                        hznof__thvl, 1)
            return impl_slice_scalar
        else:

            def impl_slice_mask(A, ind, val):
                val = bodo.utils.conversion.coerce_to_array(val,
                    use_nullable_array=True)
                n = len(A._days_data)
                A._days_data[ind] = val._days_data
                A._seconds_data[ind] = val._seconds_data
                A._microseconds_data[ind] = val._microseconds_data
                hvm__pve = val._null_bitmap.copy()
                setitem_slice_index_null_bits(A._null_bitmap, hvm__pve, ind, n)
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
            yzgxo__lquqy = arg1
            numba.parfors.parfor.init_prange()
            n = len(yzgxo__lquqy)
            A = alloc_datetime_timedelta_array(n)
            for hznof__thvl in numba.parfors.parfor.internal_prange(n):
                A[hznof__thvl] = yzgxo__lquqy[hznof__thvl] - arg2
            return A
        return impl


def create_cmp_op_overload_arr(op):

    def overload_date_arr_cmp(lhs, rhs):
        if op == operator.ne:
            tda__dwpq = True
        else:
            tda__dwpq = False
        if (lhs == datetime_timedelta_array_type and rhs ==
            datetime_timedelta_array_type):

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(lhs)
                zntoh__bwrku = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for hznof__thvl in numba.parfors.parfor.internal_prange(n):
                    eqj__cnpbg = bodo.libs.array_kernels.isna(lhs, hznof__thvl)
                    djsla__wvv = bodo.libs.array_kernels.isna(rhs, hznof__thvl)
                    if eqj__cnpbg or djsla__wvv:
                        tsxs__qia = tda__dwpq
                    else:
                        tsxs__qia = op(lhs[hznof__thvl], rhs[hznof__thvl])
                    zntoh__bwrku[hznof__thvl] = tsxs__qia
                return zntoh__bwrku
            return impl
        elif lhs == datetime_timedelta_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(lhs)
                zntoh__bwrku = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for hznof__thvl in numba.parfors.parfor.internal_prange(n):
                    jdge__cmury = bodo.libs.array_kernels.isna(lhs, hznof__thvl
                        )
                    if jdge__cmury:
                        tsxs__qia = tda__dwpq
                    else:
                        tsxs__qia = op(lhs[hznof__thvl], rhs)
                    zntoh__bwrku[hznof__thvl] = tsxs__qia
                return zntoh__bwrku
            return impl
        elif rhs == datetime_timedelta_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(rhs)
                zntoh__bwrku = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for hznof__thvl in numba.parfors.parfor.internal_prange(n):
                    jdge__cmury = bodo.libs.array_kernels.isna(rhs, hznof__thvl
                        )
                    if jdge__cmury:
                        tsxs__qia = tda__dwpq
                    else:
                        tsxs__qia = op(lhs, rhs[hznof__thvl])
                    zntoh__bwrku[hznof__thvl] = tsxs__qia
                return zntoh__bwrku
            return impl
    return overload_date_arr_cmp


timedelta_unsupported_attrs = ['asm8', 'resolution_string', 'freq',
    'is_populated']
timedelta_unsupported_methods = ['isoformat']


def _intstall_pd_timedelta_unsupported():
    from bodo.utils.typing import create_unsupported_overload
    for erp__aoua in timedelta_unsupported_attrs:
        jvzr__pii = 'pandas.Timedelta.' + erp__aoua
        overload_attribute(PDTimeDeltaType, erp__aoua)(
            create_unsupported_overload(jvzr__pii))
    for xfzzo__waadv in timedelta_unsupported_methods:
        jvzr__pii = 'pandas.Timedelta.' + xfzzo__waadv
        overload_method(PDTimeDeltaType, xfzzo__waadv)(
            create_unsupported_overload(jvzr__pii + '()'))


_intstall_pd_timedelta_unsupported()
