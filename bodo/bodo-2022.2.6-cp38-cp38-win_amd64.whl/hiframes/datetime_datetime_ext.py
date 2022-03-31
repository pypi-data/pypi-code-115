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
        ecx__uyx = [('year', types.int64), ('month', types.int64), ('day',
            types.int64), ('hour', types.int64), ('minute', types.int64), (
            'second', types.int64), ('microsecond', types.int64)]
        super(DatetimeDateTimeModel, self).__init__(dmm, fe_type, ecx__uyx)


@box(DatetimeDatetimeType)
def box_datetime_datetime(typ, val, c):
    pno__pxngt = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    zbxcn__stq = c.pyapi.long_from_longlong(pno__pxngt.year)
    ajgzl__utv = c.pyapi.long_from_longlong(pno__pxngt.month)
    fnk__vuac = c.pyapi.long_from_longlong(pno__pxngt.day)
    tnukv__rzyb = c.pyapi.long_from_longlong(pno__pxngt.hour)
    cpjaq__nyysm = c.pyapi.long_from_longlong(pno__pxngt.minute)
    ehz__omjhz = c.pyapi.long_from_longlong(pno__pxngt.second)
    scchd__uma = c.pyapi.long_from_longlong(pno__pxngt.microsecond)
    fmsk__jtn = c.pyapi.unserialize(c.pyapi.serialize_object(datetime.datetime)
        )
    ibx__kixa = c.pyapi.call_function_objargs(fmsk__jtn, (zbxcn__stq,
        ajgzl__utv, fnk__vuac, tnukv__rzyb, cpjaq__nyysm, ehz__omjhz,
        scchd__uma))
    c.pyapi.decref(zbxcn__stq)
    c.pyapi.decref(ajgzl__utv)
    c.pyapi.decref(fnk__vuac)
    c.pyapi.decref(tnukv__rzyb)
    c.pyapi.decref(cpjaq__nyysm)
    c.pyapi.decref(ehz__omjhz)
    c.pyapi.decref(scchd__uma)
    c.pyapi.decref(fmsk__jtn)
    return ibx__kixa


@unbox(DatetimeDatetimeType)
def unbox_datetime_datetime(typ, val, c):
    zbxcn__stq = c.pyapi.object_getattr_string(val, 'year')
    ajgzl__utv = c.pyapi.object_getattr_string(val, 'month')
    fnk__vuac = c.pyapi.object_getattr_string(val, 'day')
    tnukv__rzyb = c.pyapi.object_getattr_string(val, 'hour')
    cpjaq__nyysm = c.pyapi.object_getattr_string(val, 'minute')
    ehz__omjhz = c.pyapi.object_getattr_string(val, 'second')
    scchd__uma = c.pyapi.object_getattr_string(val, 'microsecond')
    pno__pxngt = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    pno__pxngt.year = c.pyapi.long_as_longlong(zbxcn__stq)
    pno__pxngt.month = c.pyapi.long_as_longlong(ajgzl__utv)
    pno__pxngt.day = c.pyapi.long_as_longlong(fnk__vuac)
    pno__pxngt.hour = c.pyapi.long_as_longlong(tnukv__rzyb)
    pno__pxngt.minute = c.pyapi.long_as_longlong(cpjaq__nyysm)
    pno__pxngt.second = c.pyapi.long_as_longlong(ehz__omjhz)
    pno__pxngt.microsecond = c.pyapi.long_as_longlong(scchd__uma)
    c.pyapi.decref(zbxcn__stq)
    c.pyapi.decref(ajgzl__utv)
    c.pyapi.decref(fnk__vuac)
    c.pyapi.decref(tnukv__rzyb)
    c.pyapi.decref(cpjaq__nyysm)
    c.pyapi.decref(ehz__omjhz)
    c.pyapi.decref(scchd__uma)
    iydk__zbzm = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(pno__pxngt._getvalue(), is_error=iydk__zbzm)


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
        pno__pxngt = cgutils.create_struct_proxy(typ)(context, builder)
        pno__pxngt.year = args[0]
        pno__pxngt.month = args[1]
        pno__pxngt.day = args[2]
        pno__pxngt.hour = args[3]
        pno__pxngt.minute = args[4]
        pno__pxngt.second = args[5]
        pno__pxngt.microsecond = args[6]
        return pno__pxngt._getvalue()
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
                y, aqb__krp = lhs.year, rhs.year
                syb__jwnl, yttzj__qmpr = lhs.month, rhs.month
                d, ysofv__susa = lhs.day, rhs.day
                ccb__bszp, vnq__efj = lhs.hour, rhs.hour
                kso__xxb, mbp__rcjz = lhs.minute, rhs.minute
                lvk__fciom, odmc__gyevq = lhs.second, rhs.second
                ufnf__eajd, gqlzg__iwola = lhs.microsecond, rhs.microsecond
                return op(_cmp((y, syb__jwnl, d, ccb__bszp, kso__xxb,
                    lvk__fciom, ufnf__eajd), (aqb__krp, yttzj__qmpr,
                    ysofv__susa, vnq__efj, mbp__rcjz, odmc__gyevq,
                    gqlzg__iwola)), 0)
            return impl
    return overload_datetime_cmp


def overload_sub_operator_datetime_datetime(lhs, rhs):
    if lhs == datetime_datetime_type and rhs == datetime_datetime_type:

        def impl(lhs, rhs):
            dqfnf__fmeo = lhs.toordinal()
            zgvm__tcz = rhs.toordinal()
            urqxa__cmtbj = lhs.second + lhs.minute * 60 + lhs.hour * 3600
            wog__fenfz = rhs.second + rhs.minute * 60 + rhs.hour * 3600
            wuwv__rin = datetime.timedelta(dqfnf__fmeo - zgvm__tcz, 
                urqxa__cmtbj - wog__fenfz, lhs.microsecond - rhs.microsecond)
            return wuwv__rin
        return impl


@lower_cast(types.Optional(numba.core.types.NPTimedelta('ns')), numba.core.
    types.NPTimedelta('ns'))
@lower_cast(types.Optional(numba.core.types.NPDatetime('ns')), numba.core.
    types.NPDatetime('ns'))
def optional_dt64_to_dt64(context, builder, fromty, toty, val):
    xhauf__giajm = context.make_helper(builder, fromty, value=val)
    bdo__elgs = cgutils.as_bool_bit(builder, xhauf__giajm.valid)
    with builder.if_else(bdo__elgs) as (iinrd__felyf, karwn__fbz):
        with iinrd__felyf:
            vwk__walvy = context.cast(builder, xhauf__giajm.data, fromty.
                type, toty)
            ogk__jik = builder.block
        with karwn__fbz:
            wejt__bri = numba.np.npdatetime.NAT
            aut__fxdls = builder.block
    ibx__kixa = builder.phi(vwk__walvy.type)
    ibx__kixa.add_incoming(vwk__walvy, ogk__jik)
    ibx__kixa.add_incoming(wejt__bri, aut__fxdls)
    return ibx__kixa
