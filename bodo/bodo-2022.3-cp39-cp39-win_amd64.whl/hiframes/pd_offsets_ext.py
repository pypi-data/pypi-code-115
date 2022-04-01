"""
Implement support for the various classes in pd.tseries.offsets.
"""
import operator
import llvmlite.binding as ll
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import lower_constant
from numba.extending import NativeValue, box, intrinsic, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_jitable, register_model, typeof_impl, unbox
from bodo.hiframes.datetime_date_ext import datetime_date_type
from bodo.hiframes.datetime_datetime_ext import datetime_datetime_type
from bodo.hiframes.pd_timestamp_ext import get_days_in_month, pd_timestamp_type
from bodo.libs import hdatetime_ext
from bodo.utils.typing import BodoError, create_unsupported_overload, is_overload_none
ll.add_symbol('box_date_offset', hdatetime_ext.box_date_offset)
ll.add_symbol('unbox_date_offset', hdatetime_ext.unbox_date_offset)


class MonthBeginType(types.Type):

    def __init__(self):
        super(MonthBeginType, self).__init__(name='MonthBeginType()')


month_begin_type = MonthBeginType()


@typeof_impl.register(pd.tseries.offsets.MonthBegin)
def typeof_month_begin(val, c):
    return month_begin_type


@register_model(MonthBeginType)
class MonthBeginModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        lgdj__halwp = [('n', types.int64), ('normalize', types.boolean)]
        super(MonthBeginModel, self).__init__(dmm, fe_type, lgdj__halwp)


@box(MonthBeginType)
def box_month_begin(typ, val, c):
    ltwi__hsxuk = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    vglg__mnwrh = c.pyapi.long_from_longlong(ltwi__hsxuk.n)
    sdwc__lhn = c.pyapi.from_native_value(types.boolean, ltwi__hsxuk.
        normalize, c.env_manager)
    bdpyr__qtw = c.pyapi.unserialize(c.pyapi.serialize_object(pd.tseries.
        offsets.MonthBegin))
    lnhdi__nsapv = c.pyapi.call_function_objargs(bdpyr__qtw, (vglg__mnwrh,
        sdwc__lhn))
    c.pyapi.decref(vglg__mnwrh)
    c.pyapi.decref(sdwc__lhn)
    c.pyapi.decref(bdpyr__qtw)
    return lnhdi__nsapv


@unbox(MonthBeginType)
def unbox_month_begin(typ, val, c):
    vglg__mnwrh = c.pyapi.object_getattr_string(val, 'n')
    sdwc__lhn = c.pyapi.object_getattr_string(val, 'normalize')
    n = c.pyapi.long_as_longlong(vglg__mnwrh)
    normalize = c.pyapi.to_native_value(types.bool_, sdwc__lhn).value
    ltwi__hsxuk = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    ltwi__hsxuk.n = n
    ltwi__hsxuk.normalize = normalize
    c.pyapi.decref(vglg__mnwrh)
    c.pyapi.decref(sdwc__lhn)
    bao__hbal = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(ltwi__hsxuk._getvalue(), is_error=bao__hbal)


@overload(pd.tseries.offsets.MonthBegin, no_unliteral=True)
def MonthBegin(n=1, normalize=False):

    def impl(n=1, normalize=False):
        return init_month_begin(n, normalize)
    return impl


@intrinsic
def init_month_begin(typingctx, n, normalize):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        ltwi__hsxuk = cgutils.create_struct_proxy(typ)(context, builder)
        ltwi__hsxuk.n = args[0]
        ltwi__hsxuk.normalize = args[1]
        return ltwi__hsxuk._getvalue()
    return MonthBeginType()(n, normalize), codegen


make_attribute_wrapper(MonthBeginType, 'n', 'n')
make_attribute_wrapper(MonthBeginType, 'normalize', 'normalize')


@register_jitable
def calculate_month_begin_date(year, month, day, n):
    if n <= 0:
        if day > 1:
            n += 1
    month = month + n
    month -= 1
    year += month // 12
    month = month % 12 + 1
    day = 1
    return year, month, day


def overload_add_operator_month_begin_offset_type(lhs, rhs):
    if lhs == month_begin_type and rhs == datetime_datetime_type:

        def impl(lhs, rhs):
            year, month, day = calculate_month_begin_date(rhs.year, rhs.
                month, rhs.day, lhs.n)
            if lhs.normalize:
                return pd.Timestamp(year=year, month=month, day=day)
            else:
                return pd.Timestamp(year=year, month=month, day=day, hour=
                    rhs.hour, minute=rhs.minute, second=rhs.second,
                    microsecond=rhs.microsecond)
        return impl
    if lhs == month_begin_type and rhs == pd_timestamp_type:

        def impl(lhs, rhs):
            year, month, day = calculate_month_begin_date(rhs.year, rhs.
                month, rhs.day, lhs.n)
            if lhs.normalize:
                return pd.Timestamp(year=year, month=month, day=day)
            else:
                return pd.Timestamp(year=year, month=month, day=day, hour=
                    rhs.hour, minute=rhs.minute, second=rhs.second,
                    microsecond=rhs.microsecond, nanosecond=rhs.nanosecond)
        return impl
    if lhs == month_begin_type and rhs == datetime_date_type:

        def impl(lhs, rhs):
            year, month, day = calculate_month_begin_date(rhs.year, rhs.
                month, rhs.day, lhs.n)
            return pd.Timestamp(year=year, month=month, day=day)
        return impl
    if lhs in [datetime_datetime_type, pd_timestamp_type, datetime_date_type
        ] and rhs == month_begin_type:

        def impl(lhs, rhs):
            return rhs + lhs
        return impl
    raise BodoError(
        f'add operator not supported for data types {lhs} and {rhs}.')


class MonthEndType(types.Type):

    def __init__(self):
        super(MonthEndType, self).__init__(name='MonthEndType()')


month_end_type = MonthEndType()


@typeof_impl.register(pd.tseries.offsets.MonthEnd)
def typeof_month_end(val, c):
    return month_end_type


@register_model(MonthEndType)
class MonthEndModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        lgdj__halwp = [('n', types.int64), ('normalize', types.boolean)]
        super(MonthEndModel, self).__init__(dmm, fe_type, lgdj__halwp)


@box(MonthEndType)
def box_month_end(typ, val, c):
    zgezw__uflj = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    vglg__mnwrh = c.pyapi.long_from_longlong(zgezw__uflj.n)
    sdwc__lhn = c.pyapi.from_native_value(types.boolean, zgezw__uflj.
        normalize, c.env_manager)
    vltmw__wed = c.pyapi.unserialize(c.pyapi.serialize_object(pd.tseries.
        offsets.MonthEnd))
    lnhdi__nsapv = c.pyapi.call_function_objargs(vltmw__wed, (vglg__mnwrh,
        sdwc__lhn))
    c.pyapi.decref(vglg__mnwrh)
    c.pyapi.decref(sdwc__lhn)
    c.pyapi.decref(vltmw__wed)
    return lnhdi__nsapv


@unbox(MonthEndType)
def unbox_month_end(typ, val, c):
    vglg__mnwrh = c.pyapi.object_getattr_string(val, 'n')
    sdwc__lhn = c.pyapi.object_getattr_string(val, 'normalize')
    n = c.pyapi.long_as_longlong(vglg__mnwrh)
    normalize = c.pyapi.to_native_value(types.bool_, sdwc__lhn).value
    zgezw__uflj = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    zgezw__uflj.n = n
    zgezw__uflj.normalize = normalize
    c.pyapi.decref(vglg__mnwrh)
    c.pyapi.decref(sdwc__lhn)
    bao__hbal = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(zgezw__uflj._getvalue(), is_error=bao__hbal)


@overload(pd.tseries.offsets.MonthEnd, no_unliteral=True)
def MonthEnd(n=1, normalize=False):

    def impl(n=1, normalize=False):
        return init_month_end(n, normalize)
    return impl


@intrinsic
def init_month_end(typingctx, n, normalize):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        zgezw__uflj = cgutils.create_struct_proxy(typ)(context, builder)
        zgezw__uflj.n = args[0]
        zgezw__uflj.normalize = args[1]
        return zgezw__uflj._getvalue()
    return MonthEndType()(n, normalize), codegen


make_attribute_wrapper(MonthEndType, 'n', 'n')
make_attribute_wrapper(MonthEndType, 'normalize', 'normalize')


@lower_constant(MonthBeginType)
@lower_constant(MonthEndType)
def lower_constant_month_end(context, builder, ty, pyval):
    n = context.get_constant(types.int64, pyval.n)
    normalize = context.get_constant(types.boolean, pyval.normalize)
    return lir.Constant.literal_struct([n, normalize])


@register_jitable
def calculate_month_end_date(year, month, day, n):
    if n > 0:
        zgezw__uflj = get_days_in_month(year, month)
        if zgezw__uflj > day:
            n -= 1
    month = month + n
    month -= 1
    year += month // 12
    month = month % 12 + 1
    day = get_days_in_month(year, month)
    return year, month, day


def overload_add_operator_month_end_offset_type(lhs, rhs):
    if lhs == month_end_type and rhs == datetime_datetime_type:

        def impl(lhs, rhs):
            year, month, day = calculate_month_end_date(rhs.year, rhs.month,
                rhs.day, lhs.n)
            if lhs.normalize:
                return pd.Timestamp(year=year, month=month, day=day)
            else:
                return pd.Timestamp(year=year, month=month, day=day, hour=
                    rhs.hour, minute=rhs.minute, second=rhs.second,
                    microsecond=rhs.microsecond)
        return impl
    if lhs == month_end_type and rhs == pd_timestamp_type:

        def impl(lhs, rhs):
            year, month, day = calculate_month_end_date(rhs.year, rhs.month,
                rhs.day, lhs.n)
            if lhs.normalize:
                return pd.Timestamp(year=year, month=month, day=day)
            else:
                return pd.Timestamp(year=year, month=month, day=day, hour=
                    rhs.hour, minute=rhs.minute, second=rhs.second,
                    microsecond=rhs.microsecond, nanosecond=rhs.nanosecond)
        return impl
    if lhs == month_end_type and rhs == datetime_date_type:

        def impl(lhs, rhs):
            year, month, day = calculate_month_end_date(rhs.year, rhs.month,
                rhs.day, lhs.n)
            return pd.Timestamp(year=year, month=month, day=day)
        return impl
    if lhs in [datetime_datetime_type, pd_timestamp_type, datetime_date_type
        ] and rhs == month_end_type:

        def impl(lhs, rhs):
            return rhs + lhs
        return impl
    raise BodoError(
        f'add operator not supported for data types {lhs} and {rhs}.')


def overload_mul_date_offset_types(lhs, rhs):
    if lhs == month_begin_type:

        def impl(lhs, rhs):
            return pd.tseries.offsets.MonthBegin(lhs.n * rhs, lhs.normalize)
    if lhs == month_end_type:

        def impl(lhs, rhs):
            return pd.tseries.offsets.MonthEnd(lhs.n * rhs, lhs.normalize)
    if lhs == week_type:

        def impl(lhs, rhs):
            return pd.tseries.offsets.Week(lhs.n * rhs, lhs.normalize, lhs.
                weekday)
    if lhs == date_offset_type:

        def impl(lhs, rhs):
            n = lhs.n * rhs
            normalize = lhs.normalize
            nanoseconds = lhs._nanoseconds
            nanosecond = lhs._nanosecond
            if lhs._has_kws:
                years = lhs._years
                months = lhs._months
                weeks = lhs._weeks
                days = lhs._days
                hours = lhs._hours
                minutes = lhs._minutes
                seconds = lhs._seconds
                microseconds = lhs._microseconds
                year = lhs._year
                month = lhs._month
                day = lhs._day
                weekday = lhs._weekday
                hour = lhs._hour
                minute = lhs._minute
                second = lhs._second
                microsecond = lhs._microsecond
                return pd.tseries.offsets.DateOffset(n, normalize, years,
                    months, weeks, days, hours, minutes, seconds,
                    microseconds, nanoseconds, year, month, day, weekday,
                    hour, minute, second, microsecond, nanosecond)
            else:
                return pd.tseries.offsets.DateOffset(n, normalize,
                    nanoseconds=nanoseconds, nanosecond=nanosecond)
    if rhs in [week_type, month_end_type, month_begin_type, date_offset_type]:

        def impl(lhs, rhs):
            return rhs * lhs
        return impl
    return impl


class DateOffsetType(types.Type):

    def __init__(self):
        super(DateOffsetType, self).__init__(name='DateOffsetType()')


date_offset_type = DateOffsetType()
date_offset_fields = ['years', 'months', 'weeks', 'days', 'hours',
    'minutes', 'seconds', 'microseconds', 'nanoseconds', 'year', 'month',
    'day', 'weekday', 'hour', 'minute', 'second', 'microsecond', 'nanosecond']


@typeof_impl.register(pd.tseries.offsets.DateOffset)
def type_of_date_offset(val, c):
    return date_offset_type


@register_model(DateOffsetType)
class DateOffsetModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        lgdj__halwp = [('n', types.int64), ('normalize', types.boolean), (
            'years', types.int64), ('months', types.int64), ('weeks', types
            .int64), ('days', types.int64), ('hours', types.int64), (
            'minutes', types.int64), ('seconds', types.int64), (
            'microseconds', types.int64), ('nanoseconds', types.int64), (
            'year', types.int64), ('month', types.int64), ('day', types.
            int64), ('weekday', types.int64), ('hour', types.int64), (
            'minute', types.int64), ('second', types.int64), ('microsecond',
            types.int64), ('nanosecond', types.int64), ('has_kws', types.
            boolean)]
        super(DateOffsetModel, self).__init__(dmm, fe_type, lgdj__halwp)


@box(DateOffsetType)
def box_date_offset(typ, val, c):
    aixtt__wgyff = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    lmx__bnpya = c.builder.alloca(lir.IntType(64), size=lir.Constant(lir.
        IntType(64), 18))
    for vfyy__zpl, nzzs__iqi in enumerate(date_offset_fields):
        c.builder.store(getattr(aixtt__wgyff, nzzs__iqi), c.builder.
            inttoptr(c.builder.add(c.builder.ptrtoint(lmx__bnpya, lir.
            IntType(64)), lir.Constant(lir.IntType(64), 8 * vfyy__zpl)),
            lir.IntType(64).as_pointer()))
    turmm__ffsn = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), lir.
        IntType(1), lir.IntType(64).as_pointer(), lir.IntType(1)])
    wrzvt__guqgf = cgutils.get_or_insert_function(c.builder.module,
        turmm__ffsn, name='box_date_offset')
    uea__qrc = c.builder.call(wrzvt__guqgf, [aixtt__wgyff.n, aixtt__wgyff.
        normalize, lmx__bnpya, aixtt__wgyff.has_kws])
    c.context.nrt.decref(c.builder, typ, val)
    return uea__qrc


@unbox(DateOffsetType)
def unbox_date_offset(typ, val, c):
    vglg__mnwrh = c.pyapi.object_getattr_string(val, 'n')
    sdwc__lhn = c.pyapi.object_getattr_string(val, 'normalize')
    n = c.pyapi.long_as_longlong(vglg__mnwrh)
    normalize = c.pyapi.to_native_value(types.bool_, sdwc__lhn).value
    lmx__bnpya = c.builder.alloca(lir.IntType(64), size=lir.Constant(lir.
        IntType(64), 18))
    turmm__ffsn = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
        as_pointer(), lir.IntType(64).as_pointer()])
    dngb__kcw = cgutils.get_or_insert_function(c.builder.module,
        turmm__ffsn, name='unbox_date_offset')
    has_kws = c.builder.call(dngb__kcw, [val, lmx__bnpya])
    aixtt__wgyff = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    aixtt__wgyff.n = n
    aixtt__wgyff.normalize = normalize
    for vfyy__zpl, nzzs__iqi in enumerate(date_offset_fields):
        setattr(aixtt__wgyff, nzzs__iqi, c.builder.load(c.builder.inttoptr(
            c.builder.add(c.builder.ptrtoint(lmx__bnpya, lir.IntType(64)),
            lir.Constant(lir.IntType(64), 8 * vfyy__zpl)), lir.IntType(64).
            as_pointer())))
    aixtt__wgyff.has_kws = has_kws
    c.pyapi.decref(vglg__mnwrh)
    c.pyapi.decref(sdwc__lhn)
    bao__hbal = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(aixtt__wgyff._getvalue(), is_error=bao__hbal)


@lower_constant(DateOffsetType)
def lower_constant_date_offset(context, builder, ty, pyval):
    n = context.get_constant(types.int64, pyval.n)
    normalize = context.get_constant(types.boolean, pyval.normalize)
    byfr__jthd = [n, normalize]
    has_kws = False
    uuo__loxmh = [0] * 9 + [-1] * 9
    for vfyy__zpl, nzzs__iqi in enumerate(date_offset_fields):
        if hasattr(pyval, nzzs__iqi):
            ugt__rfkb = context.get_constant(types.int64, getattr(pyval,
                nzzs__iqi))
            if nzzs__iqi != 'nanoseconds' and nzzs__iqi != 'nanosecond':
                has_kws = True
        else:
            ugt__rfkb = context.get_constant(types.int64, uuo__loxmh[vfyy__zpl]
                )
        byfr__jthd.append(ugt__rfkb)
    has_kws = context.get_constant(types.boolean, has_kws)
    byfr__jthd.append(has_kws)
    return lir.Constant.literal_struct(byfr__jthd)


@overload(pd.tseries.offsets.DateOffset, no_unliteral=True)
def DateOffset(n=1, normalize=False, years=None, months=None, weeks=None,
    days=None, hours=None, minutes=None, seconds=None, microseconds=None,
    nanoseconds=None, year=None, month=None, day=None, weekday=None, hour=
    None, minute=None, second=None, microsecond=None, nanosecond=None):
    has_kws = False
    cov__tit = [years, months, weeks, days, hours, minutes, seconds,
        microseconds, year, month, day, weekday, hour, minute, second,
        microsecond]
    for nno__cmpo in cov__tit:
        if not is_overload_none(nno__cmpo):
            has_kws = True
            break

    def impl(n=1, normalize=False, years=None, months=None, weeks=None,
        days=None, hours=None, minutes=None, seconds=None, microseconds=
        None, nanoseconds=None, year=None, month=None, day=None, weekday=
        None, hour=None, minute=None, second=None, microsecond=None,
        nanosecond=None):
        years = 0 if years is None else years
        months = 0 if months is None else months
        weeks = 0 if weeks is None else weeks
        days = 0 if days is None else days
        hours = 0 if hours is None else hours
        minutes = 0 if minutes is None else minutes
        seconds = 0 if seconds is None else seconds
        microseconds = 0 if microseconds is None else microseconds
        nanoseconds = 0 if nanoseconds is None else nanoseconds
        year = -1 if year is None else year
        month = -1 if month is None else month
        weekday = -1 if weekday is None else weekday
        day = -1 if day is None else day
        hour = -1 if hour is None else hour
        minute = -1 if minute is None else minute
        second = -1 if second is None else second
        microsecond = -1 if microsecond is None else microsecond
        nanosecond = -1 if nanosecond is None else nanosecond
        return init_date_offset(n, normalize, years, months, weeks, days,
            hours, minutes, seconds, microseconds, nanoseconds, year, month,
            day, weekday, hour, minute, second, microsecond, nanosecond,
            has_kws)
    return impl


@intrinsic
def init_date_offset(typingctx, n, normalize, years, months, weeks, days,
    hours, minutes, seconds, microseconds, nanoseconds, year, month, day,
    weekday, hour, minute, second, microsecond, nanosecond, has_kws):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        aixtt__wgyff = cgutils.create_struct_proxy(typ)(context, builder)
        aixtt__wgyff.n = args[0]
        aixtt__wgyff.normalize = args[1]
        aixtt__wgyff.years = args[2]
        aixtt__wgyff.months = args[3]
        aixtt__wgyff.weeks = args[4]
        aixtt__wgyff.days = args[5]
        aixtt__wgyff.hours = args[6]
        aixtt__wgyff.minutes = args[7]
        aixtt__wgyff.seconds = args[8]
        aixtt__wgyff.microseconds = args[9]
        aixtt__wgyff.nanoseconds = args[10]
        aixtt__wgyff.year = args[11]
        aixtt__wgyff.month = args[12]
        aixtt__wgyff.day = args[13]
        aixtt__wgyff.weekday = args[14]
        aixtt__wgyff.hour = args[15]
        aixtt__wgyff.minute = args[16]
        aixtt__wgyff.second = args[17]
        aixtt__wgyff.microsecond = args[18]
        aixtt__wgyff.nanosecond = args[19]
        aixtt__wgyff.has_kws = args[20]
        return aixtt__wgyff._getvalue()
    return DateOffsetType()(n, normalize, years, months, weeks, days, hours,
        minutes, seconds, microseconds, nanoseconds, year, month, day,
        weekday, hour, minute, second, microsecond, nanosecond, has_kws
        ), codegen


make_attribute_wrapper(DateOffsetType, 'n', 'n')
make_attribute_wrapper(DateOffsetType, 'normalize', 'normalize')
make_attribute_wrapper(DateOffsetType, 'years', '_years')
make_attribute_wrapper(DateOffsetType, 'months', '_months')
make_attribute_wrapper(DateOffsetType, 'weeks', '_weeks')
make_attribute_wrapper(DateOffsetType, 'days', '_days')
make_attribute_wrapper(DateOffsetType, 'hours', '_hours')
make_attribute_wrapper(DateOffsetType, 'minutes', '_minutes')
make_attribute_wrapper(DateOffsetType, 'seconds', '_seconds')
make_attribute_wrapper(DateOffsetType, 'microseconds', '_microseconds')
make_attribute_wrapper(DateOffsetType, 'nanoseconds', '_nanoseconds')
make_attribute_wrapper(DateOffsetType, 'year', '_year')
make_attribute_wrapper(DateOffsetType, 'month', '_month')
make_attribute_wrapper(DateOffsetType, 'weekday', '_weekday')
make_attribute_wrapper(DateOffsetType, 'day', '_day')
make_attribute_wrapper(DateOffsetType, 'hour', '_hour')
make_attribute_wrapper(DateOffsetType, 'minute', '_minute')
make_attribute_wrapper(DateOffsetType, 'second', '_second')
make_attribute_wrapper(DateOffsetType, 'microsecond', '_microsecond')
make_attribute_wrapper(DateOffsetType, 'nanosecond', '_nanosecond')
make_attribute_wrapper(DateOffsetType, 'has_kws', '_has_kws')


@register_jitable
def relative_delta_addition(dateoffset, ts):
    if dateoffset._has_kws:
        mehkb__jqrr = -1 if dateoffset.n < 0 else 1
        for fwa__ddqhn in range(np.abs(dateoffset.n)):
            year = ts.year
            month = ts.month
            day = ts.day
            hour = ts.hour
            minute = ts.minute
            second = ts.second
            microsecond = ts.microsecond
            nanosecond = ts.nanosecond
            if dateoffset._year != -1:
                year = dateoffset._year
            year += mehkb__jqrr * dateoffset._years
            if dateoffset._month != -1:
                month = dateoffset._month
            month += mehkb__jqrr * dateoffset._months
            year, month, eub__jvbt = calculate_month_end_date(year, month,
                day, 0)
            if day > eub__jvbt:
                day = eub__jvbt
            if dateoffset._day != -1:
                day = dateoffset._day
            if dateoffset._hour != -1:
                hour = dateoffset._hour
            if dateoffset._minute != -1:
                minute = dateoffset._minute
            if dateoffset._second != -1:
                second = dateoffset._second
            if dateoffset._microsecond != -1:
                microsecond = dateoffset._microsecond
            ts = pd.Timestamp(year=year, month=month, day=day, hour=hour,
                minute=minute, second=second, microsecond=microsecond,
                nanosecond=nanosecond)
            bmgpb__qxx = pd.Timedelta(days=dateoffset._days + 7 *
                dateoffset._weeks, hours=dateoffset._hours, minutes=
                dateoffset._minutes, seconds=dateoffset._seconds,
                microseconds=dateoffset._microseconds)
            if mehkb__jqrr == -1:
                bmgpb__qxx = -bmgpb__qxx
            ts = ts + bmgpb__qxx
            if dateoffset._weekday != -1:
                xut__mmk = ts.weekday()
                hniwt__hqis = (dateoffset._weekday - xut__mmk) % 7
                ts = ts + pd.Timedelta(days=hniwt__hqis)
        return ts
    else:
        return pd.Timedelta(days=dateoffset.n) + ts


def overload_add_operator_date_offset_type(lhs, rhs):
    if lhs == date_offset_type and rhs == pd_timestamp_type:

        def impl(lhs, rhs):
            ts = relative_delta_addition(lhs, rhs)
            if lhs.normalize:
                return ts.normalize()
            return ts
        return impl
    if lhs == date_offset_type and rhs in [datetime_date_type,
        datetime_datetime_type]:

        def impl(lhs, rhs):
            ts = relative_delta_addition(lhs, pd.Timestamp(rhs))
            if lhs.normalize:
                return ts.normalize()
            return ts
        return impl
    if lhs in [datetime_datetime_type, pd_timestamp_type, datetime_date_type
        ] and rhs == date_offset_type:

        def impl(lhs, rhs):
            return rhs + lhs
        return impl
    raise BodoError(
        f'add operator not supported for data types {lhs} and {rhs}.')


def overload_sub_operator_offsets(lhs, rhs):
    if lhs in [datetime_datetime_type, pd_timestamp_type, datetime_date_type
        ] and rhs in [date_offset_type, month_begin_type, month_end_type,
        week_type]:

        def impl(lhs, rhs):
            return lhs + -rhs
        return impl


@overload(operator.neg, no_unliteral=True)
def overload_neg(lhs):
    if lhs == month_begin_type:

        def impl(lhs):
            return pd.tseries.offsets.MonthBegin(-lhs.n, lhs.normalize)
    elif lhs == month_end_type:

        def impl(lhs):
            return pd.tseries.offsets.MonthEnd(-lhs.n, lhs.normalize)
    elif lhs == week_type:

        def impl(lhs):
            return pd.tseries.offsets.Week(-lhs.n, lhs.normalize, lhs.weekday)
    elif lhs == date_offset_type:

        def impl(lhs):
            n = -lhs.n
            normalize = lhs.normalize
            nanoseconds = lhs._nanoseconds
            nanosecond = lhs._nanosecond
            if lhs._has_kws:
                years = lhs._years
                months = lhs._months
                weeks = lhs._weeks
                days = lhs._days
                hours = lhs._hours
                minutes = lhs._minutes
                seconds = lhs._seconds
                microseconds = lhs._microseconds
                year = lhs._year
                month = lhs._month
                day = lhs._day
                weekday = lhs._weekday
                hour = lhs._hour
                minute = lhs._minute
                second = lhs._second
                microsecond = lhs._microsecond
                return pd.tseries.offsets.DateOffset(n, normalize, years,
                    months, weeks, days, hours, minutes, seconds,
                    microseconds, nanoseconds, year, month, day, weekday,
                    hour, minute, second, microsecond, nanosecond)
            else:
                return pd.tseries.offsets.DateOffset(n, normalize,
                    nanoseconds=nanoseconds, nanosecond=nanosecond)
    else:
        return
    return impl


def is_offsets_type(val):
    return val in [date_offset_type, month_begin_type, month_end_type,
        week_type]


class WeekType(types.Type):

    def __init__(self):
        super(WeekType, self).__init__(name='WeekType()')


week_type = WeekType()


@typeof_impl.register(pd.tseries.offsets.Week)
def typeof_week(val, c):
    return week_type


@register_model(WeekType)
class WeekModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        lgdj__halwp = [('n', types.int64), ('normalize', types.boolean), (
            'weekday', types.int64)]
        super(WeekModel, self).__init__(dmm, fe_type, lgdj__halwp)


make_attribute_wrapper(WeekType, 'n', 'n')
make_attribute_wrapper(WeekType, 'normalize', 'normalize')
make_attribute_wrapper(WeekType, 'weekday', 'weekday')


@overload(pd.tseries.offsets.Week, no_unliteral=True)
def Week(n=1, normalize=False, weekday=None):

    def impl(n=1, normalize=False, weekday=None):
        pkhpd__indq = -1 if weekday is None else weekday
        return init_week(n, normalize, pkhpd__indq)
    return impl


@intrinsic
def init_week(typingctx, n, normalize, weekday):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        cin__ogh = cgutils.create_struct_proxy(typ)(context, builder)
        cin__ogh.n = args[0]
        cin__ogh.normalize = args[1]
        cin__ogh.weekday = args[2]
        return cin__ogh._getvalue()
    return WeekType()(n, normalize, weekday), codegen


@lower_constant(WeekType)
def lower_constant_week(context, builder, ty, pyval):
    n = context.get_constant(types.int64, pyval.n)
    normalize = context.get_constant(types.boolean, pyval.normalize)
    if pyval.weekday is not None:
        weekday = context.get_constant(types.int64, pyval.weekday)
    else:
        weekday = context.get_constant(types.int64, -1)
    return lir.Constant.literal_struct([n, normalize, weekday])


@box(WeekType)
def box_week(typ, val, c):
    cin__ogh = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val
        )
    vglg__mnwrh = c.pyapi.long_from_longlong(cin__ogh.n)
    sdwc__lhn = c.pyapi.from_native_value(types.boolean, cin__ogh.normalize,
        c.env_manager)
    mvvci__sne = c.pyapi.long_from_longlong(cin__ogh.weekday)
    oiczw__rkog = c.pyapi.unserialize(c.pyapi.serialize_object(pd.tseries.
        offsets.Week))
    unvjb__tdmpr = c.builder.icmp_signed('!=', lir.Constant(lir.IntType(64),
        -1), cin__ogh.weekday)
    with c.builder.if_else(unvjb__tdmpr) as (xzyr__vau, hga__twg):
        with xzyr__vau:
            kgp__oixf = c.pyapi.call_function_objargs(oiczw__rkog, (
                vglg__mnwrh, sdwc__lhn, mvvci__sne))
            fah__punt = c.builder.block
        with hga__twg:
            nwii__wzxf = c.pyapi.call_function_objargs(oiczw__rkog, (
                vglg__mnwrh, sdwc__lhn))
            zposc__pghr = c.builder.block
    lnhdi__nsapv = c.builder.phi(kgp__oixf.type)
    lnhdi__nsapv.add_incoming(kgp__oixf, fah__punt)
    lnhdi__nsapv.add_incoming(nwii__wzxf, zposc__pghr)
    c.pyapi.decref(mvvci__sne)
    c.pyapi.decref(vglg__mnwrh)
    c.pyapi.decref(sdwc__lhn)
    c.pyapi.decref(oiczw__rkog)
    return lnhdi__nsapv


@unbox(WeekType)
def unbox_week(typ, val, c):
    vglg__mnwrh = c.pyapi.object_getattr_string(val, 'n')
    sdwc__lhn = c.pyapi.object_getattr_string(val, 'normalize')
    mvvci__sne = c.pyapi.object_getattr_string(val, 'weekday')
    n = c.pyapi.long_as_longlong(vglg__mnwrh)
    normalize = c.pyapi.to_native_value(types.bool_, sdwc__lhn).value
    cayxi__lol = c.pyapi.make_none()
    bcpc__oalq = c.builder.icmp_unsigned('==', mvvci__sne, cayxi__lol)
    with c.builder.if_else(bcpc__oalq) as (hga__twg, xzyr__vau):
        with xzyr__vau:
            kgp__oixf = c.pyapi.long_as_longlong(mvvci__sne)
            fah__punt = c.builder.block
        with hga__twg:
            nwii__wzxf = lir.Constant(lir.IntType(64), -1)
            zposc__pghr = c.builder.block
    lnhdi__nsapv = c.builder.phi(kgp__oixf.type)
    lnhdi__nsapv.add_incoming(kgp__oixf, fah__punt)
    lnhdi__nsapv.add_incoming(nwii__wzxf, zposc__pghr)
    cin__ogh = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    cin__ogh.n = n
    cin__ogh.normalize = normalize
    cin__ogh.weekday = lnhdi__nsapv
    c.pyapi.decref(vglg__mnwrh)
    c.pyapi.decref(sdwc__lhn)
    c.pyapi.decref(mvvci__sne)
    bao__hbal = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(cin__ogh._getvalue(), is_error=bao__hbal)


def overload_add_operator_week_offset_type(lhs, rhs):
    if lhs == week_type and rhs == pd_timestamp_type:

        def impl(lhs, rhs):
            wrrtx__jwfsu = calculate_week_date(lhs.n, lhs.weekday, rhs.
                weekday())
            if lhs.normalize:
                widau__djh = pd.Timestamp(year=rhs.year, month=rhs.month,
                    day=rhs.day)
            else:
                widau__djh = rhs
            return widau__djh + wrrtx__jwfsu
        return impl
    if lhs == week_type and rhs == datetime_datetime_type:

        def impl(lhs, rhs):
            wrrtx__jwfsu = calculate_week_date(lhs.n, lhs.weekday, rhs.
                weekday())
            if lhs.normalize:
                widau__djh = pd.Timestamp(year=rhs.year, month=rhs.month,
                    day=rhs.day)
            else:
                widau__djh = pd.Timestamp(year=rhs.year, month=rhs.month,
                    day=rhs.day, hour=rhs.hour, minute=rhs.minute, second=
                    rhs.second, microsecond=rhs.microsecond)
            return widau__djh + wrrtx__jwfsu
        return impl
    if lhs == week_type and rhs == datetime_date_type:

        def impl(lhs, rhs):
            wrrtx__jwfsu = calculate_week_date(lhs.n, lhs.weekday, rhs.
                weekday())
            return rhs + wrrtx__jwfsu
        return impl
    if lhs in [datetime_datetime_type, pd_timestamp_type, datetime_date_type
        ] and rhs == week_type:

        def impl(lhs, rhs):
            return rhs + lhs
        return impl
    raise BodoError(
        f'add operator not supported for data types {lhs} and {rhs}.')


@register_jitable
def calculate_week_date(n, weekday, other_weekday):
    if weekday == -1:
        return pd.Timedelta(weeks=n)
    if weekday != other_weekday:
        ijvp__drcsc = (weekday - other_weekday) % 7
        if n > 0:
            n = n - 1
    return pd.Timedelta(weeks=n, days=ijvp__drcsc)


date_offset_unsupported_attrs = {'base', 'freqstr', 'kwds', 'name', 'nanos',
    'rule_code'}
date_offset_unsupported = {'__call__', 'rollback', 'rollforward',
    'is_month_start', 'is_month_end', 'apply', 'apply_index', 'copy',
    'isAnchored', 'onOffset', 'is_anchored', 'is_on_offset',
    'is_quarter_start', 'is_quarter_end', 'is_year_start', 'is_year_end'}
month_end_unsupported_attrs = {'base', 'freqstr', 'kwds', 'name', 'nanos',
    'rule_code'}
month_end_unsupported = {'__call__', 'rollback', 'rollforward', 'apply',
    'apply_index', 'copy', 'isAnchored', 'onOffset', 'is_anchored',
    'is_on_offset', 'is_month_start', 'is_month_end', 'is_quarter_start',
    'is_quarter_end', 'is_year_start', 'is_year_end'}
month_begin_unsupported_attrs = {'basefreqstr', 'kwds', 'name', 'nanos',
    'rule_code'}
month_begin_unsupported = {'__call__', 'rollback', 'rollforward', 'apply',
    'apply_index', 'copy', 'isAnchored', 'onOffset', 'is_anchored',
    'is_on_offset', 'is_month_start', 'is_month_end', 'is_quarter_start',
    'is_quarter_end', 'is_year_start', 'is_year_end'}
week_unsupported_attrs = {'basefreqstr', 'kwds', 'name', 'nanos', 'rule_code'}
week_unsupported = {'__call__', 'rollback', 'rollforward', 'apply',
    'apply_index', 'copy', 'isAnchored', 'onOffset', 'is_anchored',
    'is_on_offset', 'is_month_start', 'is_month_end', 'is_quarter_start',
    'is_quarter_end', 'is_year_start', 'is_year_end'}
offsets_unsupported = {pd.tseries.offsets.BusinessDay, pd.tseries.offsets.
    BDay, pd.tseries.offsets.BusinessHour, pd.tseries.offsets.
    CustomBusinessDay, pd.tseries.offsets.CDay, pd.tseries.offsets.
    CustomBusinessHour, pd.tseries.offsets.BusinessMonthEnd, pd.tseries.
    offsets.BMonthEnd, pd.tseries.offsets.BusinessMonthBegin, pd.tseries.
    offsets.BMonthBegin, pd.tseries.offsets.CustomBusinessMonthEnd, pd.
    tseries.offsets.CBMonthEnd, pd.tseries.offsets.CustomBusinessMonthBegin,
    pd.tseries.offsets.CBMonthBegin, pd.tseries.offsets.SemiMonthEnd, pd.
    tseries.offsets.SemiMonthBegin, pd.tseries.offsets.WeekOfMonth, pd.
    tseries.offsets.LastWeekOfMonth, pd.tseries.offsets.BQuarterEnd, pd.
    tseries.offsets.BQuarterBegin, pd.tseries.offsets.QuarterEnd, pd.
    tseries.offsets.QuarterBegin, pd.tseries.offsets.BYearEnd, pd.tseries.
    offsets.BYearBegin, pd.tseries.offsets.YearEnd, pd.tseries.offsets.
    YearBegin, pd.tseries.offsets.FY5253, pd.tseries.offsets.FY5253Quarter,
    pd.tseries.offsets.Easter, pd.tseries.offsets.Tick, pd.tseries.offsets.
    Day, pd.tseries.offsets.Hour, pd.tseries.offsets.Minute, pd.tseries.
    offsets.Second, pd.tseries.offsets.Milli, pd.tseries.offsets.Micro, pd.
    tseries.offsets.Nano}
frequencies_unsupported = {pd.tseries.frequencies.to_offset}


def _install_date_offsets_unsupported():
    for ttxmu__eueq in date_offset_unsupported_attrs:
        gihn__lfk = 'pandas.tseries.offsets.DateOffset.' + ttxmu__eueq
        overload_attribute(DateOffsetType, ttxmu__eueq)(
            create_unsupported_overload(gihn__lfk))
    for ttxmu__eueq in date_offset_unsupported:
        gihn__lfk = 'pandas.tseries.offsets.DateOffset.' + ttxmu__eueq
        overload_method(DateOffsetType, ttxmu__eueq)(
            create_unsupported_overload(gihn__lfk))


def _install_month_begin_unsupported():
    for ttxmu__eueq in month_begin_unsupported_attrs:
        gihn__lfk = 'pandas.tseries.offsets.MonthBegin.' + ttxmu__eueq
        overload_attribute(MonthBeginType, ttxmu__eueq)(
            create_unsupported_overload(gihn__lfk))
    for ttxmu__eueq in month_begin_unsupported:
        gihn__lfk = 'pandas.tseries.offsets.MonthBegin.' + ttxmu__eueq
        overload_method(MonthBeginType, ttxmu__eueq)(
            create_unsupported_overload(gihn__lfk))


def _install_month_end_unsupported():
    for ttxmu__eueq in date_offset_unsupported_attrs:
        gihn__lfk = 'pandas.tseries.offsets.MonthEnd.' + ttxmu__eueq
        overload_attribute(MonthEndType, ttxmu__eueq)(
            create_unsupported_overload(gihn__lfk))
    for ttxmu__eueq in date_offset_unsupported:
        gihn__lfk = 'pandas.tseries.offsets.MonthEnd.' + ttxmu__eueq
        overload_method(MonthEndType, ttxmu__eueq)(create_unsupported_overload
            (gihn__lfk))


def _install_week_unsupported():
    for ttxmu__eueq in week_unsupported_attrs:
        gihn__lfk = 'pandas.tseries.offsets.Week.' + ttxmu__eueq
        overload_attribute(WeekType, ttxmu__eueq)(create_unsupported_overload
            (gihn__lfk))
    for ttxmu__eueq in week_unsupported:
        gihn__lfk = 'pandas.tseries.offsets.Week.' + ttxmu__eueq
        overload_method(WeekType, ttxmu__eueq)(create_unsupported_overload(
            gihn__lfk))


def _install_offsets_unsupported():
    for ugt__rfkb in offsets_unsupported:
        gihn__lfk = 'pandas.tseries.offsets.' + ugt__rfkb.__name__
        overload(ugt__rfkb)(create_unsupported_overload(gihn__lfk))


def _install_frequencies_unsupported():
    for ugt__rfkb in frequencies_unsupported:
        gihn__lfk = 'pandas.tseries.frequencies.' + ugt__rfkb.__name__
        overload(ugt__rfkb)(create_unsupported_overload(gihn__lfk))


_install_date_offsets_unsupported()
_install_month_begin_unsupported()
_install_month_end_unsupported()
_install_week_unsupported()
_install_offsets_unsupported()
_install_frequencies_unsupported()
