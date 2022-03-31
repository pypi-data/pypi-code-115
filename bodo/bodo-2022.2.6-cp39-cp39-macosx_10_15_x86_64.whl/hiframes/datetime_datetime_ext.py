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
        dph__dat = [('year', types.int64), ('month', types.int64), ('day',
            types.int64), ('hour', types.int64), ('minute', types.int64), (
            'second', types.int64), ('microsecond', types.int64)]
        super(DatetimeDateTimeModel, self).__init__(dmm, fe_type, dph__dat)


@box(DatetimeDatetimeType)
def box_datetime_datetime(typ, val, c):
    npoc__rfasd = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    yahe__ubod = c.pyapi.long_from_longlong(npoc__rfasd.year)
    elsj__bswli = c.pyapi.long_from_longlong(npoc__rfasd.month)
    lexga__sei = c.pyapi.long_from_longlong(npoc__rfasd.day)
    nzudc__jbj = c.pyapi.long_from_longlong(npoc__rfasd.hour)
    jndbi__bgs = c.pyapi.long_from_longlong(npoc__rfasd.minute)
    ikp__bcs = c.pyapi.long_from_longlong(npoc__rfasd.second)
    ahiqw__ypigo = c.pyapi.long_from_longlong(npoc__rfasd.microsecond)
    bckis__roa = c.pyapi.unserialize(c.pyapi.serialize_object(datetime.
        datetime))
    bobvd__dnf = c.pyapi.call_function_objargs(bckis__roa, (yahe__ubod,
        elsj__bswli, lexga__sei, nzudc__jbj, jndbi__bgs, ikp__bcs,
        ahiqw__ypigo))
    c.pyapi.decref(yahe__ubod)
    c.pyapi.decref(elsj__bswli)
    c.pyapi.decref(lexga__sei)
    c.pyapi.decref(nzudc__jbj)
    c.pyapi.decref(jndbi__bgs)
    c.pyapi.decref(ikp__bcs)
    c.pyapi.decref(ahiqw__ypigo)
    c.pyapi.decref(bckis__roa)
    return bobvd__dnf


@unbox(DatetimeDatetimeType)
def unbox_datetime_datetime(typ, val, c):
    yahe__ubod = c.pyapi.object_getattr_string(val, 'year')
    elsj__bswli = c.pyapi.object_getattr_string(val, 'month')
    lexga__sei = c.pyapi.object_getattr_string(val, 'day')
    nzudc__jbj = c.pyapi.object_getattr_string(val, 'hour')
    jndbi__bgs = c.pyapi.object_getattr_string(val, 'minute')
    ikp__bcs = c.pyapi.object_getattr_string(val, 'second')
    ahiqw__ypigo = c.pyapi.object_getattr_string(val, 'microsecond')
    npoc__rfasd = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    npoc__rfasd.year = c.pyapi.long_as_longlong(yahe__ubod)
    npoc__rfasd.month = c.pyapi.long_as_longlong(elsj__bswli)
    npoc__rfasd.day = c.pyapi.long_as_longlong(lexga__sei)
    npoc__rfasd.hour = c.pyapi.long_as_longlong(nzudc__jbj)
    npoc__rfasd.minute = c.pyapi.long_as_longlong(jndbi__bgs)
    npoc__rfasd.second = c.pyapi.long_as_longlong(ikp__bcs)
    npoc__rfasd.microsecond = c.pyapi.long_as_longlong(ahiqw__ypigo)
    c.pyapi.decref(yahe__ubod)
    c.pyapi.decref(elsj__bswli)
    c.pyapi.decref(lexga__sei)
    c.pyapi.decref(nzudc__jbj)
    c.pyapi.decref(jndbi__bgs)
    c.pyapi.decref(ikp__bcs)
    c.pyapi.decref(ahiqw__ypigo)
    ygar__vpu = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(npoc__rfasd._getvalue(), is_error=ygar__vpu)


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
        npoc__rfasd = cgutils.create_struct_proxy(typ)(context, builder)
        npoc__rfasd.year = args[0]
        npoc__rfasd.month = args[1]
        npoc__rfasd.day = args[2]
        npoc__rfasd.hour = args[3]
        npoc__rfasd.minute = args[4]
        npoc__rfasd.second = args[5]
        npoc__rfasd.microsecond = args[6]
        return npoc__rfasd._getvalue()
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
                y, lakr__gjnqw = lhs.year, rhs.year
                urxn__wdq, dxnqb__swnr = lhs.month, rhs.month
                d, dqb__suf = lhs.day, rhs.day
                zhoi__bbbrb, ttsqv__wwf = lhs.hour, rhs.hour
                rcxgg__zgbi, ndp__cku = lhs.minute, rhs.minute
                tkcg__jkra, jfht__qxq = lhs.second, rhs.second
                nxbzc__fvqd, chjgw__ghr = lhs.microsecond, rhs.microsecond
                return op(_cmp((y, urxn__wdq, d, zhoi__bbbrb, rcxgg__zgbi,
                    tkcg__jkra, nxbzc__fvqd), (lakr__gjnqw, dxnqb__swnr,
                    dqb__suf, ttsqv__wwf, ndp__cku, jfht__qxq, chjgw__ghr)), 0)
            return impl
    return overload_datetime_cmp


def overload_sub_operator_datetime_datetime(lhs, rhs):
    if lhs == datetime_datetime_type and rhs == datetime_datetime_type:

        def impl(lhs, rhs):
            dumlq__zyei = lhs.toordinal()
            vvehg__usjyv = rhs.toordinal()
            uixp__ict = lhs.second + lhs.minute * 60 + lhs.hour * 3600
            gsd__mmwp = rhs.second + rhs.minute * 60 + rhs.hour * 3600
            mmzq__pztm = datetime.timedelta(dumlq__zyei - vvehg__usjyv, 
                uixp__ict - gsd__mmwp, lhs.microsecond - rhs.microsecond)
            return mmzq__pztm
        return impl


@lower_cast(types.Optional(numba.core.types.NPTimedelta('ns')), numba.core.
    types.NPTimedelta('ns'))
@lower_cast(types.Optional(numba.core.types.NPDatetime('ns')), numba.core.
    types.NPDatetime('ns'))
def optional_dt64_to_dt64(context, builder, fromty, toty, val):
    nmjhi__rzk = context.make_helper(builder, fromty, value=val)
    stfwh__nbeq = cgutils.as_bool_bit(builder, nmjhi__rzk.valid)
    with builder.if_else(stfwh__nbeq) as (wzhnz__pda, twr__kxzv):
        with wzhnz__pda:
            sgr__irarc = context.cast(builder, nmjhi__rzk.data, fromty.type,
                toty)
            fvr__xalto = builder.block
        with twr__kxzv:
            ral__zeur = numba.np.npdatetime.NAT
            jykhm__gqtpj = builder.block
    bobvd__dnf = builder.phi(sgr__irarc.type)
    bobvd__dnf.add_incoming(sgr__irarc, fvr__xalto)
    bobvd__dnf.add_incoming(ral__zeur, jykhm__gqtpj)
    return bobvd__dnf
