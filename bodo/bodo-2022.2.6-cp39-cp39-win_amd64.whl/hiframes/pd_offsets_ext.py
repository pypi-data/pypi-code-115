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
        hth__hdv = [('n', types.int64), ('normalize', types.boolean)]
        super(MonthBeginModel, self).__init__(dmm, fe_type, hth__hdv)


@box(MonthBeginType)
def box_month_begin(typ, val, c):
    cem__pbtk = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    slaod__ytoa = c.pyapi.long_from_longlong(cem__pbtk.n)
    qaftj__uwjuj = c.pyapi.from_native_value(types.boolean, cem__pbtk.
        normalize, c.env_manager)
    rvvme__qjzlj = c.pyapi.unserialize(c.pyapi.serialize_object(pd.tseries.
        offsets.MonthBegin))
    yegbl__zami = c.pyapi.call_function_objargs(rvvme__qjzlj, (slaod__ytoa,
        qaftj__uwjuj))
    c.pyapi.decref(slaod__ytoa)
    c.pyapi.decref(qaftj__uwjuj)
    c.pyapi.decref(rvvme__qjzlj)
    return yegbl__zami


@unbox(MonthBeginType)
def unbox_month_begin(typ, val, c):
    slaod__ytoa = c.pyapi.object_getattr_string(val, 'n')
    qaftj__uwjuj = c.pyapi.object_getattr_string(val, 'normalize')
    n = c.pyapi.long_as_longlong(slaod__ytoa)
    normalize = c.pyapi.to_native_value(types.bool_, qaftj__uwjuj).value
    cem__pbtk = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    cem__pbtk.n = n
    cem__pbtk.normalize = normalize
    c.pyapi.decref(slaod__ytoa)
    c.pyapi.decref(qaftj__uwjuj)
    mfg__dmyyl = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(cem__pbtk._getvalue(), is_error=mfg__dmyyl)


@overload(pd.tseries.offsets.MonthBegin, no_unliteral=True)
def MonthBegin(n=1, normalize=False):

    def impl(n=1, normalize=False):
        return init_month_begin(n, normalize)
    return impl


@intrinsic
def init_month_begin(typingctx, n, normalize):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        cem__pbtk = cgutils.create_struct_proxy(typ)(context, builder)
        cem__pbtk.n = args[0]
        cem__pbtk.normalize = args[1]
        return cem__pbtk._getvalue()
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
        hth__hdv = [('n', types.int64), ('normalize', types.boolean)]
        super(MonthEndModel, self).__init__(dmm, fe_type, hth__hdv)


@box(MonthEndType)
def box_month_end(typ, val, c):
    ylv__beme = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    slaod__ytoa = c.pyapi.long_from_longlong(ylv__beme.n)
    qaftj__uwjuj = c.pyapi.from_native_value(types.boolean, ylv__beme.
        normalize, c.env_manager)
    jbl__jla = c.pyapi.unserialize(c.pyapi.serialize_object(pd.tseries.
        offsets.MonthEnd))
    yegbl__zami = c.pyapi.call_function_objargs(jbl__jla, (slaod__ytoa,
        qaftj__uwjuj))
    c.pyapi.decref(slaod__ytoa)
    c.pyapi.decref(qaftj__uwjuj)
    c.pyapi.decref(jbl__jla)
    return yegbl__zami


@unbox(MonthEndType)
def unbox_month_end(typ, val, c):
    slaod__ytoa = c.pyapi.object_getattr_string(val, 'n')
    qaftj__uwjuj = c.pyapi.object_getattr_string(val, 'normalize')
    n = c.pyapi.long_as_longlong(slaod__ytoa)
    normalize = c.pyapi.to_native_value(types.bool_, qaftj__uwjuj).value
    ylv__beme = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    ylv__beme.n = n
    ylv__beme.normalize = normalize
    c.pyapi.decref(slaod__ytoa)
    c.pyapi.decref(qaftj__uwjuj)
    mfg__dmyyl = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(ylv__beme._getvalue(), is_error=mfg__dmyyl)


@overload(pd.tseries.offsets.MonthEnd, no_unliteral=True)
def MonthEnd(n=1, normalize=False):

    def impl(n=1, normalize=False):
        return init_month_end(n, normalize)
    return impl


@intrinsic
def init_month_end(typingctx, n, normalize):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        ylv__beme = cgutils.create_struct_proxy(typ)(context, builder)
        ylv__beme.n = args[0]
        ylv__beme.normalize = args[1]
        return ylv__beme._getvalue()
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
        ylv__beme = get_days_in_month(year, month)
        if ylv__beme > day:
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
        hth__hdv = [('n', types.int64), ('normalize', types.boolean), (
            'years', types.int64), ('months', types.int64), ('weeks', types
            .int64), ('days', types.int64), ('hours', types.int64), (
            'minutes', types.int64), ('seconds', types.int64), (
            'microseconds', types.int64), ('nanoseconds', types.int64), (
            'year', types.int64), ('month', types.int64), ('day', types.
            int64), ('weekday', types.int64), ('hour', types.int64), (
            'minute', types.int64), ('second', types.int64), ('microsecond',
            types.int64), ('nanosecond', types.int64), ('has_kws', types.
            boolean)]
        super(DateOffsetModel, self).__init__(dmm, fe_type, hth__hdv)


@box(DateOffsetType)
def box_date_offset(typ, val, c):
    pcpzl__sjz = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    iegho__xwk = c.builder.alloca(lir.IntType(64), size=lir.Constant(lir.
        IntType(64), 18))
    for wrr__qjvv, pscgo__tvj in enumerate(date_offset_fields):
        c.builder.store(getattr(pcpzl__sjz, pscgo__tvj), c.builder.inttoptr
            (c.builder.add(c.builder.ptrtoint(iegho__xwk, lir.IntType(64)),
            lir.Constant(lir.IntType(64), 8 * wrr__qjvv)), lir.IntType(64).
            as_pointer()))
    mhkn__pkd = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), lir.
        IntType(1), lir.IntType(64).as_pointer(), lir.IntType(1)])
    zwso__bslr = cgutils.get_or_insert_function(c.builder.module, mhkn__pkd,
        name='box_date_offset')
    hmsfx__jxwa = c.builder.call(zwso__bslr, [pcpzl__sjz.n, pcpzl__sjz.
        normalize, iegho__xwk, pcpzl__sjz.has_kws])
    c.context.nrt.decref(c.builder, typ, val)
    return hmsfx__jxwa


@unbox(DateOffsetType)
def unbox_date_offset(typ, val, c):
    slaod__ytoa = c.pyapi.object_getattr_string(val, 'n')
    qaftj__uwjuj = c.pyapi.object_getattr_string(val, 'normalize')
    n = c.pyapi.long_as_longlong(slaod__ytoa)
    normalize = c.pyapi.to_native_value(types.bool_, qaftj__uwjuj).value
    iegho__xwk = c.builder.alloca(lir.IntType(64), size=lir.Constant(lir.
        IntType(64), 18))
    mhkn__pkd = lir.FunctionType(lir.IntType(1), [lir.IntType(8).as_pointer
        (), lir.IntType(64).as_pointer()])
    xgxve__skmpe = cgutils.get_or_insert_function(c.builder.module,
        mhkn__pkd, name='unbox_date_offset')
    has_kws = c.builder.call(xgxve__skmpe, [val, iegho__xwk])
    pcpzl__sjz = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    pcpzl__sjz.n = n
    pcpzl__sjz.normalize = normalize
    for wrr__qjvv, pscgo__tvj in enumerate(date_offset_fields):
        setattr(pcpzl__sjz, pscgo__tvj, c.builder.load(c.builder.inttoptr(c
            .builder.add(c.builder.ptrtoint(iegho__xwk, lir.IntType(64)),
            lir.Constant(lir.IntType(64), 8 * wrr__qjvv)), lir.IntType(64).
            as_pointer())))
    pcpzl__sjz.has_kws = has_kws
    c.pyapi.decref(slaod__ytoa)
    c.pyapi.decref(qaftj__uwjuj)
    mfg__dmyyl = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(pcpzl__sjz._getvalue(), is_error=mfg__dmyyl)


@lower_constant(DateOffsetType)
def lower_constant_date_offset(context, builder, ty, pyval):
    n = context.get_constant(types.int64, pyval.n)
    normalize = context.get_constant(types.boolean, pyval.normalize)
    eerm__basgc = [n, normalize]
    has_kws = False
    tcvv__gzuik = [0] * 9 + [-1] * 9
    for wrr__qjvv, pscgo__tvj in enumerate(date_offset_fields):
        if hasattr(pyval, pscgo__tvj):
            rpzl__fcco = context.get_constant(types.int64, getattr(pyval,
                pscgo__tvj))
            if pscgo__tvj != 'nanoseconds' and pscgo__tvj != 'nanosecond':
                has_kws = True
        else:
            rpzl__fcco = context.get_constant(types.int64, tcvv__gzuik[
                wrr__qjvv])
        eerm__basgc.append(rpzl__fcco)
    has_kws = context.get_constant(types.boolean, has_kws)
    eerm__basgc.append(has_kws)
    return lir.Constant.literal_struct(eerm__basgc)


@overload(pd.tseries.offsets.DateOffset, no_unliteral=True)
def DateOffset(n=1, normalize=False, years=None, months=None, weeks=None,
    days=None, hours=None, minutes=None, seconds=None, microseconds=None,
    nanoseconds=None, year=None, month=None, day=None, weekday=None, hour=
    None, minute=None, second=None, microsecond=None, nanosecond=None):
    has_kws = False
    sulq__abwre = [years, months, weeks, days, hours, minutes, seconds,
        microseconds, year, month, day, weekday, hour, minute, second,
        microsecond]
    for oqhkd__cku in sulq__abwre:
        if not is_overload_none(oqhkd__cku):
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
        pcpzl__sjz = cgutils.create_struct_proxy(typ)(context, builder)
        pcpzl__sjz.n = args[0]
        pcpzl__sjz.normalize = args[1]
        pcpzl__sjz.years = args[2]
        pcpzl__sjz.months = args[3]
        pcpzl__sjz.weeks = args[4]
        pcpzl__sjz.days = args[5]
        pcpzl__sjz.hours = args[6]
        pcpzl__sjz.minutes = args[7]
        pcpzl__sjz.seconds = args[8]
        pcpzl__sjz.microseconds = args[9]
        pcpzl__sjz.nanoseconds = args[10]
        pcpzl__sjz.year = args[11]
        pcpzl__sjz.month = args[12]
        pcpzl__sjz.day = args[13]
        pcpzl__sjz.weekday = args[14]
        pcpzl__sjz.hour = args[15]
        pcpzl__sjz.minute = args[16]
        pcpzl__sjz.second = args[17]
        pcpzl__sjz.microsecond = args[18]
        pcpzl__sjz.nanosecond = args[19]
        pcpzl__sjz.has_kws = args[20]
        return pcpzl__sjz._getvalue()
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
        bcvg__afz = -1 if dateoffset.n < 0 else 1
        for rbbn__algz in range(np.abs(dateoffset.n)):
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
            year += bcvg__afz * dateoffset._years
            if dateoffset._month != -1:
                month = dateoffset._month
            month += bcvg__afz * dateoffset._months
            year, month, jua__woqt = calculate_month_end_date(year, month,
                day, 0)
            if day > jua__woqt:
                day = jua__woqt
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
            fuao__cydnf = pd.Timedelta(days=dateoffset._days + 7 *
                dateoffset._weeks, hours=dateoffset._hours, minutes=
                dateoffset._minutes, seconds=dateoffset._seconds,
                microseconds=dateoffset._microseconds)
            if bcvg__afz == -1:
                fuao__cydnf = -fuao__cydnf
            ts = ts + fuao__cydnf
            if dateoffset._weekday != -1:
                tsrn__yvh = ts.weekday()
                ajrre__jun = (dateoffset._weekday - tsrn__yvh) % 7
                ts = ts + pd.Timedelta(days=ajrre__jun)
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
        hth__hdv = [('n', types.int64), ('normalize', types.boolean), (
            'weekday', types.int64)]
        super(WeekModel, self).__init__(dmm, fe_type, hth__hdv)


make_attribute_wrapper(WeekType, 'n', 'n')
make_attribute_wrapper(WeekType, 'normalize', 'normalize')
make_attribute_wrapper(WeekType, 'weekday', 'weekday')


@overload(pd.tseries.offsets.Week, no_unliteral=True)
def Week(n=1, normalize=False, weekday=None):

    def impl(n=1, normalize=False, weekday=None):
        qcyno__syyex = -1 if weekday is None else weekday
        return init_week(n, normalize, qcyno__syyex)
    return impl


@intrinsic
def init_week(typingctx, n, normalize, weekday):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        lkwnj__yaz = cgutils.create_struct_proxy(typ)(context, builder)
        lkwnj__yaz.n = args[0]
        lkwnj__yaz.normalize = args[1]
        lkwnj__yaz.weekday = args[2]
        return lkwnj__yaz._getvalue()
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
    lkwnj__yaz = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    slaod__ytoa = c.pyapi.long_from_longlong(lkwnj__yaz.n)
    qaftj__uwjuj = c.pyapi.from_native_value(types.boolean, lkwnj__yaz.
        normalize, c.env_manager)
    mshje__tudf = c.pyapi.long_from_longlong(lkwnj__yaz.weekday)
    yrijf__tkt = c.pyapi.unserialize(c.pyapi.serialize_object(pd.tseries.
        offsets.Week))
    vcnp__ddxfk = c.builder.icmp_signed('!=', lir.Constant(lir.IntType(64),
        -1), lkwnj__yaz.weekday)
    with c.builder.if_else(vcnp__ddxfk) as (kifw__fupql, rtf__kzst):
        with kifw__fupql:
            jczmy__xik = c.pyapi.call_function_objargs(yrijf__tkt, (
                slaod__ytoa, qaftj__uwjuj, mshje__tudf))
            vuad__qlh = c.builder.block
        with rtf__kzst:
            dsgx__flfj = c.pyapi.call_function_objargs(yrijf__tkt, (
                slaod__ytoa, qaftj__uwjuj))
            vyx__hra = c.builder.block
    yegbl__zami = c.builder.phi(jczmy__xik.type)
    yegbl__zami.add_incoming(jczmy__xik, vuad__qlh)
    yegbl__zami.add_incoming(dsgx__flfj, vyx__hra)
    c.pyapi.decref(mshje__tudf)
    c.pyapi.decref(slaod__ytoa)
    c.pyapi.decref(qaftj__uwjuj)
    c.pyapi.decref(yrijf__tkt)
    return yegbl__zami


@unbox(WeekType)
def unbox_week(typ, val, c):
    slaod__ytoa = c.pyapi.object_getattr_string(val, 'n')
    qaftj__uwjuj = c.pyapi.object_getattr_string(val, 'normalize')
    mshje__tudf = c.pyapi.object_getattr_string(val, 'weekday')
    n = c.pyapi.long_as_longlong(slaod__ytoa)
    normalize = c.pyapi.to_native_value(types.bool_, qaftj__uwjuj).value
    jvjot__tma = c.pyapi.make_none()
    ato__mcbi = c.builder.icmp_unsigned('==', mshje__tudf, jvjot__tma)
    with c.builder.if_else(ato__mcbi) as (rtf__kzst, kifw__fupql):
        with kifw__fupql:
            jczmy__xik = c.pyapi.long_as_longlong(mshje__tudf)
            vuad__qlh = c.builder.block
        with rtf__kzst:
            dsgx__flfj = lir.Constant(lir.IntType(64), -1)
            vyx__hra = c.builder.block
    yegbl__zami = c.builder.phi(jczmy__xik.type)
    yegbl__zami.add_incoming(jczmy__xik, vuad__qlh)
    yegbl__zami.add_incoming(dsgx__flfj, vyx__hra)
    lkwnj__yaz = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    lkwnj__yaz.n = n
    lkwnj__yaz.normalize = normalize
    lkwnj__yaz.weekday = yegbl__zami
    c.pyapi.decref(slaod__ytoa)
    c.pyapi.decref(qaftj__uwjuj)
    c.pyapi.decref(mshje__tudf)
    mfg__dmyyl = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(lkwnj__yaz._getvalue(), is_error=mfg__dmyyl)


def overload_add_operator_week_offset_type(lhs, rhs):
    if lhs == week_type and rhs == pd_timestamp_type:

        def impl(lhs, rhs):
            joite__swy = calculate_week_date(lhs.n, lhs.weekday, rhs.weekday())
            if lhs.normalize:
                kxl__qswd = pd.Timestamp(year=rhs.year, month=rhs.month,
                    day=rhs.day)
            else:
                kxl__qswd = rhs
            return kxl__qswd + joite__swy
        return impl
    if lhs == week_type and rhs == datetime_datetime_type:

        def impl(lhs, rhs):
            joite__swy = calculate_week_date(lhs.n, lhs.weekday, rhs.weekday())
            if lhs.normalize:
                kxl__qswd = pd.Timestamp(year=rhs.year, month=rhs.month,
                    day=rhs.day)
            else:
                kxl__qswd = pd.Timestamp(year=rhs.year, month=rhs.month,
                    day=rhs.day, hour=rhs.hour, minute=rhs.minute, second=
                    rhs.second, microsecond=rhs.microsecond)
            return kxl__qswd + joite__swy
        return impl
    if lhs == week_type and rhs == datetime_date_type:

        def impl(lhs, rhs):
            joite__swy = calculate_week_date(lhs.n, lhs.weekday, rhs.weekday())
            return rhs + joite__swy
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
        mfsd__lmkhv = (weekday - other_weekday) % 7
        if n > 0:
            n = n - 1
    return pd.Timedelta(weeks=n, days=mfsd__lmkhv)


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
    for ikjyt__hfx in date_offset_unsupported_attrs:
        rqq__yvjy = 'pandas.tseries.offsets.DateOffset.' + ikjyt__hfx
        overload_attribute(DateOffsetType, ikjyt__hfx)(
            create_unsupported_overload(rqq__yvjy))
    for ikjyt__hfx in date_offset_unsupported:
        rqq__yvjy = 'pandas.tseries.offsets.DateOffset.' + ikjyt__hfx
        overload_method(DateOffsetType, ikjyt__hfx)(create_unsupported_overload
            (rqq__yvjy))


def _install_month_begin_unsupported():
    for ikjyt__hfx in month_begin_unsupported_attrs:
        rqq__yvjy = 'pandas.tseries.offsets.MonthBegin.' + ikjyt__hfx
        overload_attribute(MonthBeginType, ikjyt__hfx)(
            create_unsupported_overload(rqq__yvjy))
    for ikjyt__hfx in month_begin_unsupported:
        rqq__yvjy = 'pandas.tseries.offsets.MonthBegin.' + ikjyt__hfx
        overload_method(MonthBeginType, ikjyt__hfx)(create_unsupported_overload
            (rqq__yvjy))


def _install_month_end_unsupported():
    for ikjyt__hfx in date_offset_unsupported_attrs:
        rqq__yvjy = 'pandas.tseries.offsets.MonthEnd.' + ikjyt__hfx
        overload_attribute(MonthEndType, ikjyt__hfx)(
            create_unsupported_overload(rqq__yvjy))
    for ikjyt__hfx in date_offset_unsupported:
        rqq__yvjy = 'pandas.tseries.offsets.MonthEnd.' + ikjyt__hfx
        overload_method(MonthEndType, ikjyt__hfx)(create_unsupported_overload
            (rqq__yvjy))


def _install_week_unsupported():
    for ikjyt__hfx in week_unsupported_attrs:
        rqq__yvjy = 'pandas.tseries.offsets.Week.' + ikjyt__hfx
        overload_attribute(WeekType, ikjyt__hfx)(create_unsupported_overload
            (rqq__yvjy))
    for ikjyt__hfx in week_unsupported:
        rqq__yvjy = 'pandas.tseries.offsets.Week.' + ikjyt__hfx
        overload_method(WeekType, ikjyt__hfx)(create_unsupported_overload(
            rqq__yvjy))


def _install_offsets_unsupported():
    for rpzl__fcco in offsets_unsupported:
        rqq__yvjy = 'pandas.tseries.offsets.' + rpzl__fcco.__name__
        overload(rpzl__fcco)(create_unsupported_overload(rqq__yvjy))


def _install_frequencies_unsupported():
    for rpzl__fcco in frequencies_unsupported:
        rqq__yvjy = 'pandas.tseries.frequencies.' + rpzl__fcco.__name__
        overload(rpzl__fcco)(create_unsupported_overload(rqq__yvjy))


_install_date_offsets_unsupported()
_install_month_begin_unsupported()
_install_month_end_unsupported()
_install_week_unsupported()
_install_offsets_unsupported()
_install_frequencies_unsupported()
