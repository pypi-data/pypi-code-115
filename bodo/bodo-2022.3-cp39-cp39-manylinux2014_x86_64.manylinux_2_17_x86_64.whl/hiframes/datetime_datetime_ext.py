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
        ercdt__lkqux = [('year', types.int64), ('month', types.int64), (
            'day', types.int64), ('hour', types.int64), ('minute', types.
            int64), ('second', types.int64), ('microsecond', types.int64)]
        super(DatetimeDateTimeModel, self).__init__(dmm, fe_type, ercdt__lkqux)


@box(DatetimeDatetimeType)
def box_datetime_datetime(typ, val, c):
    arz__zqa = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val
        )
    omsf__mzpp = c.pyapi.long_from_longlong(arz__zqa.year)
    kan__niyg = c.pyapi.long_from_longlong(arz__zqa.month)
    fkmt__kvqh = c.pyapi.long_from_longlong(arz__zqa.day)
    lvfom__djpg = c.pyapi.long_from_longlong(arz__zqa.hour)
    vmm__lmtnl = c.pyapi.long_from_longlong(arz__zqa.minute)
    qtuq__sjc = c.pyapi.long_from_longlong(arz__zqa.second)
    skisb__iavo = c.pyapi.long_from_longlong(arz__zqa.microsecond)
    lpsfc__ylqy = c.pyapi.unserialize(c.pyapi.serialize_object(datetime.
        datetime))
    vbx__ibz = c.pyapi.call_function_objargs(lpsfc__ylqy, (omsf__mzpp,
        kan__niyg, fkmt__kvqh, lvfom__djpg, vmm__lmtnl, qtuq__sjc, skisb__iavo)
        )
    c.pyapi.decref(omsf__mzpp)
    c.pyapi.decref(kan__niyg)
    c.pyapi.decref(fkmt__kvqh)
    c.pyapi.decref(lvfom__djpg)
    c.pyapi.decref(vmm__lmtnl)
    c.pyapi.decref(qtuq__sjc)
    c.pyapi.decref(skisb__iavo)
    c.pyapi.decref(lpsfc__ylqy)
    return vbx__ibz


@unbox(DatetimeDatetimeType)
def unbox_datetime_datetime(typ, val, c):
    omsf__mzpp = c.pyapi.object_getattr_string(val, 'year')
    kan__niyg = c.pyapi.object_getattr_string(val, 'month')
    fkmt__kvqh = c.pyapi.object_getattr_string(val, 'day')
    lvfom__djpg = c.pyapi.object_getattr_string(val, 'hour')
    vmm__lmtnl = c.pyapi.object_getattr_string(val, 'minute')
    qtuq__sjc = c.pyapi.object_getattr_string(val, 'second')
    skisb__iavo = c.pyapi.object_getattr_string(val, 'microsecond')
    arz__zqa = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    arz__zqa.year = c.pyapi.long_as_longlong(omsf__mzpp)
    arz__zqa.month = c.pyapi.long_as_longlong(kan__niyg)
    arz__zqa.day = c.pyapi.long_as_longlong(fkmt__kvqh)
    arz__zqa.hour = c.pyapi.long_as_longlong(lvfom__djpg)
    arz__zqa.minute = c.pyapi.long_as_longlong(vmm__lmtnl)
    arz__zqa.second = c.pyapi.long_as_longlong(qtuq__sjc)
    arz__zqa.microsecond = c.pyapi.long_as_longlong(skisb__iavo)
    c.pyapi.decref(omsf__mzpp)
    c.pyapi.decref(kan__niyg)
    c.pyapi.decref(fkmt__kvqh)
    c.pyapi.decref(lvfom__djpg)
    c.pyapi.decref(vmm__lmtnl)
    c.pyapi.decref(qtuq__sjc)
    c.pyapi.decref(skisb__iavo)
    lfq__hfov = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(arz__zqa._getvalue(), is_error=lfq__hfov)


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
        arz__zqa = cgutils.create_struct_proxy(typ)(context, builder)
        arz__zqa.year = args[0]
        arz__zqa.month = args[1]
        arz__zqa.day = args[2]
        arz__zqa.hour = args[3]
        arz__zqa.minute = args[4]
        arz__zqa.second = args[5]
        arz__zqa.microsecond = args[6]
        return arz__zqa._getvalue()
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
                y, xvka__omsy = lhs.year, rhs.year
                xnbz__scrgc, xrgze__ccryg = lhs.month, rhs.month
                d, gcj__hmad = lhs.day, rhs.day
                ynwt__fwvdj, pgmnb__igh = lhs.hour, rhs.hour
                ufm__ericm, bkcl__sxk = lhs.minute, rhs.minute
                qvqg__uzk, rzdy__wxr = lhs.second, rhs.second
                jdv__abh, ptvq__mpx = lhs.microsecond, rhs.microsecond
                return op(_cmp((y, xnbz__scrgc, d, ynwt__fwvdj, ufm__ericm,
                    qvqg__uzk, jdv__abh), (xvka__omsy, xrgze__ccryg,
                    gcj__hmad, pgmnb__igh, bkcl__sxk, rzdy__wxr, ptvq__mpx)), 0
                    )
            return impl
    return overload_datetime_cmp


def overload_sub_operator_datetime_datetime(lhs, rhs):
    if lhs == datetime_datetime_type and rhs == datetime_datetime_type:

        def impl(lhs, rhs):
            hthf__ivqho = lhs.toordinal()
            ybwxf__fbn = rhs.toordinal()
            ekok__cnowg = lhs.second + lhs.minute * 60 + lhs.hour * 3600
            gry__vqfej = rhs.second + rhs.minute * 60 + rhs.hour * 3600
            hfjn__lypo = datetime.timedelta(hthf__ivqho - ybwxf__fbn, 
                ekok__cnowg - gry__vqfej, lhs.microsecond - rhs.microsecond)
            return hfjn__lypo
        return impl


@lower_cast(types.Optional(numba.core.types.NPTimedelta('ns')), numba.core.
    types.NPTimedelta('ns'))
@lower_cast(types.Optional(numba.core.types.NPDatetime('ns')), numba.core.
    types.NPDatetime('ns'))
def optional_dt64_to_dt64(context, builder, fromty, toty, val):
    mbwep__riak = context.make_helper(builder, fromty, value=val)
    obrv__ueiji = cgutils.as_bool_bit(builder, mbwep__riak.valid)
    with builder.if_else(obrv__ueiji) as (qdp__lmu, pnfk__apc):
        with qdp__lmu:
            xzy__ywhn = context.cast(builder, mbwep__riak.data, fromty.type,
                toty)
            fuw__adw = builder.block
        with pnfk__apc:
            mft__uqrvf = numba.np.npdatetime.NAT
            yxm__rjh = builder.block
    vbx__ibz = builder.phi(xzy__ywhn.type)
    vbx__ibz.add_incoming(xzy__ywhn, fuw__adw)
    vbx__ibz.add_incoming(mft__uqrvf, yxm__rjh)
    return vbx__ibz
