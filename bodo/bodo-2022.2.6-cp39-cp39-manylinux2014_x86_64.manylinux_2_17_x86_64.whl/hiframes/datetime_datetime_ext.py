import datetime
import numba
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import lower_constant
from numba.extending import NativeValue, box, intrinsic, lower_cast, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_jitable, register_model, typeof_impl, unbox
"""
Implementation is based on
https://github.com/python/cpython/blob/39a5c889d30d03a88102e56f03ee0c95db198fb3/Lib/datetime.py
"""


class DatetimeDatetimeType(types.Type):

    def __init__(self):
        super(DatetimeDatetimeType, self).__init__(name=
            'DatetimeDatetimeType()')


datetime_datetime_type = DatetimeDatetimeType()
types.datetime_datetime_type = datetime_datetime_type


@typeof_impl.register(datetime.datetime)
def typeof_datetime_datetime(val, c):
    return datetime_datetime_type


@register_model(DatetimeDatetimeType)
class DatetimeDateTimeModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        treqz__uawu = [('year', types.int64), ('month', types.int64), (
            'day', types.int64), ('hour', types.int64), ('minute', types.
            int64), ('second', types.int64), ('microsecond', types.int64)]
        super(DatetimeDateTimeModel, self).__init__(dmm, fe_type, treqz__uawu)


@box(DatetimeDatetimeType)
def box_datetime_datetime(typ, val, c):
    fvcm__hlgj = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    nsph__hplw = c.pyapi.long_from_longlong(fvcm__hlgj.year)
    vjtlu__abf = c.pyapi.long_from_longlong(fvcm__hlgj.month)
    lop__eqhyt = c.pyapi.long_from_longlong(fvcm__hlgj.day)
    sgavk__tktw = c.pyapi.long_from_longlong(fvcm__hlgj.hour)
    gwuyl__rhpdk = c.pyapi.long_from_longlong(fvcm__hlgj.minute)
    jjqy__zbmh = c.pyapi.long_from_longlong(fvcm__hlgj.second)
    ltyud__oarb = c.pyapi.long_from_longlong(fvcm__hlgj.microsecond)
    xbbb__xwth = c.pyapi.unserialize(c.pyapi.serialize_object(datetime.
        datetime))
    eybyy__bucn = c.pyapi.call_function_objargs(xbbb__xwth, (nsph__hplw,
        vjtlu__abf, lop__eqhyt, sgavk__tktw, gwuyl__rhpdk, jjqy__zbmh,
        ltyud__oarb))
    c.pyapi.decref(nsph__hplw)
    c.pyapi.decref(vjtlu__abf)
    c.pyapi.decref(lop__eqhyt)
    c.pyapi.decref(sgavk__tktw)
    c.pyapi.decref(gwuyl__rhpdk)
    c.pyapi.decref(jjqy__zbmh)
    c.pyapi.decref(ltyud__oarb)
    c.pyapi.decref(xbbb__xwth)
    return eybyy__bucn


@unbox(DatetimeDatetimeType)
def unbox_datetime_datetime(typ, val, c):
    nsph__hplw = c.pyapi.object_getattr_string(val, 'year')
    vjtlu__abf = c.pyapi.object_getattr_string(val, 'month')
    lop__eqhyt = c.pyapi.object_getattr_string(val, 'day')
    sgavk__tktw = c.pyapi.object_getattr_string(val, 'hour')
    gwuyl__rhpdk = c.pyapi.object_getattr_string(val, 'minute')
    jjqy__zbmh = c.pyapi.object_getattr_string(val, 'second')
    ltyud__oarb = c.pyapi.object_getattr_string(val, 'microsecond')
    fvcm__hlgj = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    fvcm__hlgj.year = c.pyapi.long_as_longlong(nsph__hplw)
    fvcm__hlgj.month = c.pyapi.long_as_longlong(vjtlu__abf)
    fvcm__hlgj.day = c.pyapi.long_as_longlong(lop__eqhyt)
    fvcm__hlgj.hour = c.pyapi.long_as_longlong(sgavk__tktw)
    fvcm__hlgj.minute = c.pyapi.long_as_longlong(gwuyl__rhpdk)
    fvcm__hlgj.second = c.pyapi.long_as_longlong(jjqy__zbmh)
    fvcm__hlgj.microsecond = c.pyapi.long_as_longlong(ltyud__oarb)
    c.pyapi.decref(nsph__hplw)
    c.pyapi.decref(vjtlu__abf)
    c.pyapi.decref(lop__eqhyt)
    c.pyapi.decref(sgavk__tktw)
    c.pyapi.decref(gwuyl__rhpdk)
    c.pyapi.decref(jjqy__zbmh)
    c.pyapi.decref(ltyud__oarb)
    nou__uzx = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(fvcm__hlgj._getvalue(), is_error=nou__uzx)


@lower_constant(DatetimeDatetimeType)
def constant_datetime(context, builder, ty, pyval):
    year = context.get_constant(types.int64, pyval.year)
    month = context.get_constant(types.int64, pyval.month)
    day = context.get_constant(types.int64, pyval.day)
    hour = context.get_constant(types.int64, pyval.hour)
    minute = context.get_constant(types.int64, pyval.minute)
    second = context.get_constant(types.int64, pyval.second)
    microsecond = context.get_constant(types.int64, pyval.microsecond)
    return lir.Constant.literal_struct([year, month, day, hour, minute,
        second, microsecond])


@overload(datetime.datetime, no_unliteral=True)
def datetime_datetime(year, month, day, hour=0, minute=0, second=0,
    microsecond=0):

    def impl_datetime(year, month, day, hour=0, minute=0, second=0,
        microsecond=0):
        return init_datetime(year, month, day, hour, minute, second,
            microsecond)
    return impl_datetime


@intrinsic
def init_datetime(typingctx, year, month, day, hour, minute, second,
    microsecond):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        fvcm__hlgj = cgutils.create_struct_proxy(typ)(context, builder)
        fvcm__hlgj.year = args[0]
        fvcm__hlgj.month = args[1]
        fvcm__hlgj.day = args[2]
        fvcm__hlgj.hour = args[3]
        fvcm__hlgj.minute = args[4]
        fvcm__hlgj.second = args[5]
        fvcm__hlgj.microsecond = args[6]
        return fvcm__hlgj._getvalue()
    return DatetimeDatetimeType()(year, month, day, hour, minute, second,
        microsecond), codegen


make_attribute_wrapper(DatetimeDatetimeType, 'year', '_year')
make_attribute_wrapper(DatetimeDatetimeType, 'month', '_month')
make_attribute_wrapper(DatetimeDatetimeType, 'day', '_day')
make_attribute_wrapper(DatetimeDatetimeType, 'hour', '_hour')
make_attribute_wrapper(DatetimeDatetimeType, 'minute', '_minute')
make_attribute_wrapper(DatetimeDatetimeType, 'second', '_second')
make_attribute_wrapper(DatetimeDatetimeType, 'microsecond', '_microsecond')


@overload_attribute(DatetimeDatetimeType, 'year')
def datetime_get_year(dt):

    def impl(dt):
        return dt._year
    return impl


@overload_attribute(DatetimeDatetimeType, 'month')
def datetime_get_month(dt):

    def impl(dt):
        return dt._month
    return impl


@overload_attribute(DatetimeDatetimeType, 'day')
def datetime_get_day(dt):

    def impl(dt):
        return dt._day
    return impl


@overload_attribute(DatetimeDatetimeType, 'hour')
def datetime_get_hour(dt):

    def impl(dt):
        return dt._hour
    return impl


@overload_attribute(DatetimeDatetimeType, 'minute')
def datetime_get_minute(dt):

    def impl(dt):
        return dt._minute
    return impl


@overload_attribute(DatetimeDatetimeType, 'second')
def datetime_get_second(dt):

    def impl(dt):
        return dt._second
    return impl


@overload_attribute(DatetimeDatetimeType, 'microsecond')
def datetime_get_microsecond(dt):

    def impl(dt):
        return dt._microsecond
    return impl


@overload_method(DatetimeDatetimeType, 'date', no_unliteral=True)
def date(dt):

    def impl(dt):
        return datetime.date(dt.year, dt.month, dt.day)
    return impl


@register_jitable
def now_impl():
    with numba.objmode(d='datetime_datetime_type'):
        d = datetime.datetime.now()
    return d


@register_jitable
def today_impl():
    with numba.objmode(d='datetime_datetime_type'):
        d = datetime.datetime.today()
    return d


@register_jitable
def strptime_impl(date_string, dtformat):
    with numba.objmode(d='datetime_datetime_type'):
        d = datetime.datetime.strptime(date_string, dtformat)
    return d


@register_jitable
def _cmp(x, y):
    return 0 if x == y else 1 if x > y else -1


def create_cmp_op_overload(op):

    def overload_datetime_cmp(lhs, rhs):
        if lhs == datetime_datetime_type and rhs == datetime_datetime_type:

            def impl(lhs, rhs):
                y, rqpy__qebb = lhs.year, rhs.year
                ndmay__tlp, sorbg__jgeaj = lhs.month, rhs.month
                d, rie__cqqkk = lhs.day, rhs.day
                vvno__gkgb, oulh__wyzk = lhs.hour, rhs.hour
                wsh__jymir, awg__yptm = lhs.minute, rhs.minute
                zgzdn__uyddy, fmzxx__rvpjh = lhs.second, rhs.second
                ovtl__xyw, ktmq__jbdrd = lhs.microsecond, rhs.microsecond
                return op(_cmp((y, ndmay__tlp, d, vvno__gkgb, wsh__jymir,
                    zgzdn__uyddy, ovtl__xyw), (rqpy__qebb, sorbg__jgeaj,
                    rie__cqqkk, oulh__wyzk, awg__yptm, fmzxx__rvpjh,
                    ktmq__jbdrd)), 0)
            return impl
    return overload_datetime_cmp


def overload_sub_operator_datetime_datetime(lhs, rhs):
    if lhs == datetime_datetime_type and rhs == datetime_datetime_type:

        def impl(lhs, rhs):
            vogu__kisw = lhs.toordinal()
            sipe__vpdv = rhs.toordinal()
            wbtn__sfpdu = lhs.second + lhs.minute * 60 + lhs.hour * 3600
            oij__ugzoa = rhs.second + rhs.minute * 60 + rhs.hour * 3600
            mdph__wvh = datetime.timedelta(vogu__kisw - sipe__vpdv, 
                wbtn__sfpdu - oij__ugzoa, lhs.microsecond - rhs.microsecond)
            return mdph__wvh
        return impl


@lower_cast(types.Optional(numba.core.types.NPTimedelta('ns')), numba.core.
    types.NPTimedelta('ns'))
@lower_cast(types.Optional(numba.core.types.NPDatetime('ns')), numba.core.
    types.NPDatetime('ns'))
def optional_dt64_to_dt64(context, builder, fromty, toty, val):
    gjyd__gul = context.make_helper(builder, fromty, value=val)
    odn__rwybc = cgutils.as_bool_bit(builder, gjyd__gul.valid)
    with builder.if_else(odn__rwybc) as (kox__ttm, qamop__kteli):
        with kox__ttm:
            oavx__ismyb = context.cast(builder, gjyd__gul.data, fromty.type,
                toty)
            sin__yxxg = builder.block
        with qamop__kteli:
            rvina__hxem = numba.np.npdatetime.NAT
            oiw__itl = builder.block
    eybyy__bucn = builder.phi(oavx__ismyb.type)
    eybyy__bucn.add_incoming(oavx__ismyb, sin__yxxg)
    eybyy__bucn.add_incoming(rvina__hxem, oiw__itl)
    return eybyy__bucn
