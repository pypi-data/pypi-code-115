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
        tlwzx__vzvnt = [('year', types.int64), ('month', types.int64), (
            'day', types.int64), ('hour', types.int64), ('minute', types.
            int64), ('second', types.int64), ('microsecond', types.int64)]
        super(DatetimeDateTimeModel, self).__init__(dmm, fe_type, tlwzx__vzvnt)


@box(DatetimeDatetimeType)
def box_datetime_datetime(typ, val, c):
    cjt__gahv = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    mow__ppry = c.pyapi.long_from_longlong(cjt__gahv.year)
    fryy__zhld = c.pyapi.long_from_longlong(cjt__gahv.month)
    wlbry__xeo = c.pyapi.long_from_longlong(cjt__gahv.day)
    fffw__icdkt = c.pyapi.long_from_longlong(cjt__gahv.hour)
    etld__adq = c.pyapi.long_from_longlong(cjt__gahv.minute)
    dtv__utorn = c.pyapi.long_from_longlong(cjt__gahv.second)
    ppcq__uweh = c.pyapi.long_from_longlong(cjt__gahv.microsecond)
    fbsws__sho = c.pyapi.unserialize(c.pyapi.serialize_object(datetime.
        datetime))
    nvjof__pvh = c.pyapi.call_function_objargs(fbsws__sho, (mow__ppry,
        fryy__zhld, wlbry__xeo, fffw__icdkt, etld__adq, dtv__utorn, ppcq__uweh)
        )
    c.pyapi.decref(mow__ppry)
    c.pyapi.decref(fryy__zhld)
    c.pyapi.decref(wlbry__xeo)
    c.pyapi.decref(fffw__icdkt)
    c.pyapi.decref(etld__adq)
    c.pyapi.decref(dtv__utorn)
    c.pyapi.decref(ppcq__uweh)
    c.pyapi.decref(fbsws__sho)
    return nvjof__pvh


@unbox(DatetimeDatetimeType)
def unbox_datetime_datetime(typ, val, c):
    mow__ppry = c.pyapi.object_getattr_string(val, 'year')
    fryy__zhld = c.pyapi.object_getattr_string(val, 'month')
    wlbry__xeo = c.pyapi.object_getattr_string(val, 'day')
    fffw__icdkt = c.pyapi.object_getattr_string(val, 'hour')
    etld__adq = c.pyapi.object_getattr_string(val, 'minute')
    dtv__utorn = c.pyapi.object_getattr_string(val, 'second')
    ppcq__uweh = c.pyapi.object_getattr_string(val, 'microsecond')
    cjt__gahv = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    cjt__gahv.year = c.pyapi.long_as_longlong(mow__ppry)
    cjt__gahv.month = c.pyapi.long_as_longlong(fryy__zhld)
    cjt__gahv.day = c.pyapi.long_as_longlong(wlbry__xeo)
    cjt__gahv.hour = c.pyapi.long_as_longlong(fffw__icdkt)
    cjt__gahv.minute = c.pyapi.long_as_longlong(etld__adq)
    cjt__gahv.second = c.pyapi.long_as_longlong(dtv__utorn)
    cjt__gahv.microsecond = c.pyapi.long_as_longlong(ppcq__uweh)
    c.pyapi.decref(mow__ppry)
    c.pyapi.decref(fryy__zhld)
    c.pyapi.decref(wlbry__xeo)
    c.pyapi.decref(fffw__icdkt)
    c.pyapi.decref(etld__adq)
    c.pyapi.decref(dtv__utorn)
    c.pyapi.decref(ppcq__uweh)
    uesam__rou = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(cjt__gahv._getvalue(), is_error=uesam__rou)


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
        cjt__gahv = cgutils.create_struct_proxy(typ)(context, builder)
        cjt__gahv.year = args[0]
        cjt__gahv.month = args[1]
        cjt__gahv.day = args[2]
        cjt__gahv.hour = args[3]
        cjt__gahv.minute = args[4]
        cjt__gahv.second = args[5]
        cjt__gahv.microsecond = args[6]
        return cjt__gahv._getvalue()
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
                y, fsv__ixint = lhs.year, rhs.year
                wqml__exh, yzmee__vuf = lhs.month, rhs.month
                d, nfom__xkds = lhs.day, rhs.day
                zdo__vyt, axstt__gisbj = lhs.hour, rhs.hour
                xdsj__lesgl, tfw__mqi = lhs.minute, rhs.minute
                aof__scrmn, xcyll__ouvbm = lhs.second, rhs.second
                ogx__actre, ndv__bfhvt = lhs.microsecond, rhs.microsecond
                return op(_cmp((y, wqml__exh, d, zdo__vyt, xdsj__lesgl,
                    aof__scrmn, ogx__actre), (fsv__ixint, yzmee__vuf,
                    nfom__xkds, axstt__gisbj, tfw__mqi, xcyll__ouvbm,
                    ndv__bfhvt)), 0)
            return impl
    return overload_datetime_cmp


def overload_sub_operator_datetime_datetime(lhs, rhs):
    if lhs == datetime_datetime_type and rhs == datetime_datetime_type:

        def impl(lhs, rhs):
            jurz__sbsq = lhs.toordinal()
            vhr__hzb = rhs.toordinal()
            iam__qsfp = lhs.second + lhs.minute * 60 + lhs.hour * 3600
            dfwki__ihv = rhs.second + rhs.minute * 60 + rhs.hour * 3600
            rremo__ske = datetime.timedelta(jurz__sbsq - vhr__hzb, 
                iam__qsfp - dfwki__ihv, lhs.microsecond - rhs.microsecond)
            return rremo__ske
        return impl


@lower_cast(types.Optional(numba.core.types.NPTimedelta('ns')), numba.core.
    types.NPTimedelta('ns'))
@lower_cast(types.Optional(numba.core.types.NPDatetime('ns')), numba.core.
    types.NPDatetime('ns'))
def optional_dt64_to_dt64(context, builder, fromty, toty, val):
    xaqk__sfpv = context.make_helper(builder, fromty, value=val)
    nds__ujmq = cgutils.as_bool_bit(builder, xaqk__sfpv.valid)
    with builder.if_else(nds__ujmq) as (bledm__arxgs, mgq__adc):
        with bledm__arxgs:
            tzxk__resvb = context.cast(builder, xaqk__sfpv.data, fromty.
                type, toty)
            zhby__ubh = builder.block
        with mgq__adc:
            cpyt__kke = numba.np.npdatetime.NAT
            hhn__dcx = builder.block
    nvjof__pvh = builder.phi(tzxk__resvb.type)
    nvjof__pvh.add_incoming(tzxk__resvb, zhby__ubh)
    nvjof__pvh.add_incoming(cpyt__kke, hhn__dcx)
    return nvjof__pvh
