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
        bwlp__yrmn = [('year', types.int64), ('month', types.int64), ('day',
            types.int64), ('hour', types.int64), ('minute', types.int64), (
            'second', types.int64), ('microsecond', types.int64)]
        super(DatetimeDateTimeModel, self).__init__(dmm, fe_type, bwlp__yrmn)


@box(DatetimeDatetimeType)
def box_datetime_datetime(typ, val, c):
    wifw__inq = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    hpidh__rgquy = c.pyapi.long_from_longlong(wifw__inq.year)
    agt__gsg = c.pyapi.long_from_longlong(wifw__inq.month)
    lnhnd__dbfh = c.pyapi.long_from_longlong(wifw__inq.day)
    sjj__gsm = c.pyapi.long_from_longlong(wifw__inq.hour)
    pcvy__fypd = c.pyapi.long_from_longlong(wifw__inq.minute)
    roy__tjnyu = c.pyapi.long_from_longlong(wifw__inq.second)
    smcw__syzo = c.pyapi.long_from_longlong(wifw__inq.microsecond)
    mzm__njflt = c.pyapi.unserialize(c.pyapi.serialize_object(datetime.
        datetime))
    bkl__otsh = c.pyapi.call_function_objargs(mzm__njflt, (hpidh__rgquy,
        agt__gsg, lnhnd__dbfh, sjj__gsm, pcvy__fypd, roy__tjnyu, smcw__syzo))
    c.pyapi.decref(hpidh__rgquy)
    c.pyapi.decref(agt__gsg)
    c.pyapi.decref(lnhnd__dbfh)
    c.pyapi.decref(sjj__gsm)
    c.pyapi.decref(pcvy__fypd)
    c.pyapi.decref(roy__tjnyu)
    c.pyapi.decref(smcw__syzo)
    c.pyapi.decref(mzm__njflt)
    return bkl__otsh


@unbox(DatetimeDatetimeType)
def unbox_datetime_datetime(typ, val, c):
    hpidh__rgquy = c.pyapi.object_getattr_string(val, 'year')
    agt__gsg = c.pyapi.object_getattr_string(val, 'month')
    lnhnd__dbfh = c.pyapi.object_getattr_string(val, 'day')
    sjj__gsm = c.pyapi.object_getattr_string(val, 'hour')
    pcvy__fypd = c.pyapi.object_getattr_string(val, 'minute')
    roy__tjnyu = c.pyapi.object_getattr_string(val, 'second')
    smcw__syzo = c.pyapi.object_getattr_string(val, 'microsecond')
    wifw__inq = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    wifw__inq.year = c.pyapi.long_as_longlong(hpidh__rgquy)
    wifw__inq.month = c.pyapi.long_as_longlong(agt__gsg)
    wifw__inq.day = c.pyapi.long_as_longlong(lnhnd__dbfh)
    wifw__inq.hour = c.pyapi.long_as_longlong(sjj__gsm)
    wifw__inq.minute = c.pyapi.long_as_longlong(pcvy__fypd)
    wifw__inq.second = c.pyapi.long_as_longlong(roy__tjnyu)
    wifw__inq.microsecond = c.pyapi.long_as_longlong(smcw__syzo)
    c.pyapi.decref(hpidh__rgquy)
    c.pyapi.decref(agt__gsg)
    c.pyapi.decref(lnhnd__dbfh)
    c.pyapi.decref(sjj__gsm)
    c.pyapi.decref(pcvy__fypd)
    c.pyapi.decref(roy__tjnyu)
    c.pyapi.decref(smcw__syzo)
    owj__kjz = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(wifw__inq._getvalue(), is_error=owj__kjz)


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
        wifw__inq = cgutils.create_struct_proxy(typ)(context, builder)
        wifw__inq.year = args[0]
        wifw__inq.month = args[1]
        wifw__inq.day = args[2]
        wifw__inq.hour = args[3]
        wifw__inq.minute = args[4]
        wifw__inq.second = args[5]
        wifw__inq.microsecond = args[6]
        return wifw__inq._getvalue()
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
                y, hhrn__jpfy = lhs.year, rhs.year
                yter__ywdq, pqwrf__manit = lhs.month, rhs.month
                d, axuj__tifzo = lhs.day, rhs.day
                ypix__rpx, akve__gise = lhs.hour, rhs.hour
                ixif__xpdbv, hpw__uvbyt = lhs.minute, rhs.minute
                coe__ugh, zewv__rzk = lhs.second, rhs.second
                voinb__awa, ovbym__tlvhs = lhs.microsecond, rhs.microsecond
                return op(_cmp((y, yter__ywdq, d, ypix__rpx, ixif__xpdbv,
                    coe__ugh, voinb__awa), (hhrn__jpfy, pqwrf__manit,
                    axuj__tifzo, akve__gise, hpw__uvbyt, zewv__rzk,
                    ovbym__tlvhs)), 0)
            return impl
    return overload_datetime_cmp


def overload_sub_operator_datetime_datetime(lhs, rhs):
    if lhs == datetime_datetime_type and rhs == datetime_datetime_type:

        def impl(lhs, rhs):
            qoa__lzf = lhs.toordinal()
            sbu__ihx = rhs.toordinal()
            usxf__pkvta = lhs.second + lhs.minute * 60 + lhs.hour * 3600
            ecv__qvak = rhs.second + rhs.minute * 60 + rhs.hour * 3600
            sksyv__req = datetime.timedelta(qoa__lzf - sbu__ihx, 
                usxf__pkvta - ecv__qvak, lhs.microsecond - rhs.microsecond)
            return sksyv__req
        return impl


@lower_cast(types.Optional(numba.core.types.NPTimedelta('ns')), numba.core.
    types.NPTimedelta('ns'))
@lower_cast(types.Optional(numba.core.types.NPDatetime('ns')), numba.core.
    types.NPDatetime('ns'))
def optional_dt64_to_dt64(context, builder, fromty, toty, val):
    hkvtv__czwgf = context.make_helper(builder, fromty, value=val)
    wgb__fzc = cgutils.as_bool_bit(builder, hkvtv__czwgf.valid)
    with builder.if_else(wgb__fzc) as (vzp__ocxmv, hpwpc__vrnzq):
        with vzp__ocxmv:
            vrkc__fdgdj = context.cast(builder, hkvtv__czwgf.data, fromty.
                type, toty)
            msz__ubzul = builder.block
        with hpwpc__vrnzq:
            ogf__xqd = numba.np.npdatetime.NAT
            jcbce__bfsar = builder.block
    bkl__otsh = builder.phi(vrkc__fdgdj.type)
    bkl__otsh.add_incoming(vrkc__fdgdj, msz__ubzul)
    bkl__otsh.add_incoming(ogf__xqd, jcbce__bfsar)
    return bkl__otsh
