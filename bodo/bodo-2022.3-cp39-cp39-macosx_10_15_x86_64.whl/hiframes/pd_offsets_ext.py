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
        awpxl__ckabk = [('n', types.int64), ('normalize', types.boolean)]
        super(MonthBeginModel, self).__init__(dmm, fe_type, awpxl__ckabk)


@box(MonthBeginType)
def box_month_begin(typ, val, c):
    qvfw__cvde = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    cxpbo__lgj = c.pyapi.long_from_longlong(qvfw__cvde.n)
    dviv__gydlr = c.pyapi.from_native_value(types.boolean, qvfw__cvde.
        normalize, c.env_manager)
    sxg__wmm = c.pyapi.unserialize(c.pyapi.serialize_object(pd.tseries.
        offsets.MonthBegin))
    uosz__taa = c.pyapi.call_function_objargs(sxg__wmm, (cxpbo__lgj,
        dviv__gydlr))
    c.pyapi.decref(cxpbo__lgj)
    c.pyapi.decref(dviv__gydlr)
    c.pyapi.decref(sxg__wmm)
    return uosz__taa


@unbox(MonthBeginType)
def unbox_month_begin(typ, val, c):
    cxpbo__lgj = c.pyapi.object_getattr_string(val, 'n')
    dviv__gydlr = c.pyapi.object_getattr_string(val, 'normalize')
    n = c.pyapi.long_as_longlong(cxpbo__lgj)
    normalize = c.pyapi.to_native_value(types.bool_, dviv__gydlr).value
    qvfw__cvde = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    qvfw__cvde.n = n
    qvfw__cvde.normalize = normalize
    c.pyapi.decref(cxpbo__lgj)
    c.pyapi.decref(dviv__gydlr)
    feriu__hsli = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(qvfw__cvde._getvalue(), is_error=feriu__hsli)


@overload(pd.tseries.offsets.MonthBegin, no_unliteral=True)
def MonthBegin(n=1, normalize=False):

    def impl(n=1, normalize=False):
        return init_month_begin(n, normalize)
    return impl


@intrinsic
def init_month_begin(typingctx, n, normalize):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        qvfw__cvde = cgutils.create_struct_proxy(typ)(context, builder)
        qvfw__cvde.n = args[0]
        qvfw__cvde.normalize = args[1]
        return qvfw__cvde._getvalue()
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
        awpxl__ckabk = [('n', types.int64), ('normalize', types.boolean)]
        super(MonthEndModel, self).__init__(dmm, fe_type, awpxl__ckabk)


@box(MonthEndType)
def box_month_end(typ, val, c):
    zbm__ugz = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val
        )
    cxpbo__lgj = c.pyapi.long_from_longlong(zbm__ugz.n)
    dviv__gydlr = c.pyapi.from_native_value(types.boolean, zbm__ugz.
        normalize, c.env_manager)
    zbx__dykue = c.pyapi.unserialize(c.pyapi.serialize_object(pd.tseries.
        offsets.MonthEnd))
    uosz__taa = c.pyapi.call_function_objargs(zbx__dykue, (cxpbo__lgj,
        dviv__gydlr))
    c.pyapi.decref(cxpbo__lgj)
    c.pyapi.decref(dviv__gydlr)
    c.pyapi.decref(zbx__dykue)
    return uosz__taa


@unbox(MonthEndType)
def unbox_month_end(typ, val, c):
    cxpbo__lgj = c.pyapi.object_getattr_string(val, 'n')
    dviv__gydlr = c.pyapi.object_getattr_string(val, 'normalize')
    n = c.pyapi.long_as_longlong(cxpbo__lgj)
    normalize = c.pyapi.to_native_value(types.bool_, dviv__gydlr).value
    zbm__ugz = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    zbm__ugz.n = n
    zbm__ugz.normalize = normalize
    c.pyapi.decref(cxpbo__lgj)
    c.pyapi.decref(dviv__gydlr)
    feriu__hsli = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(zbm__ugz._getvalue(), is_error=feriu__hsli)


@overload(pd.tseries.offsets.MonthEnd, no_unliteral=True)
def MonthEnd(n=1, normalize=False):

    def impl(n=1, normalize=False):
        return init_month_end(n, normalize)
    return impl


@intrinsic
def init_month_end(typingctx, n, normalize):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        zbm__ugz = cgutils.create_struct_proxy(typ)(context, builder)
        zbm__ugz.n = args[0]
        zbm__ugz.normalize = args[1]
        return zbm__ugz._getvalue()
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
        zbm__ugz = get_days_in_month(year, month)
        if zbm__ugz > day:
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
        awpxl__ckabk = [('n', types.int64), ('normalize', types.boolean), (
            'years', types.int64), ('months', types.int64), ('weeks', types
            .int64), ('days', types.int64), ('hours', types.int64), (
            'minutes', types.int64), ('seconds', types.int64), (
            'microseconds', types.int64), ('nanoseconds', types.int64), (
            'year', types.int64), ('month', types.int64), ('day', types.
            int64), ('weekday', types.int64), ('hour', types.int64), (
            'minute', types.int64), ('second', types.int64), ('microsecond',
            types.int64), ('nanosecond', types.int64), ('has_kws', types.
            boolean)]
        super(DateOffsetModel, self).__init__(dmm, fe_type, awpxl__ckabk)


@box(DateOffsetType)
def box_date_offset(typ, val, c):
    xscjl__xucn = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    cvy__gvjzs = c.builder.alloca(lir.IntType(64), size=lir.Constant(lir.
        IntType(64), 18))
    for kkxhr__jrbj, yaakn__fekn in enumerate(date_offset_fields):
        c.builder.store(getattr(xscjl__xucn, yaakn__fekn), c.builder.
            inttoptr(c.builder.add(c.builder.ptrtoint(cvy__gvjzs, lir.
            IntType(64)), lir.Constant(lir.IntType(64), 8 * kkxhr__jrbj)),
            lir.IntType(64).as_pointer()))
    dyz__yax = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), lir.
        IntType(1), lir.IntType(64).as_pointer(), lir.IntType(1)])
    gscpf__mjflm = cgutils.get_or_insert_function(c.builder.module,
        dyz__yax, name='box_date_offset')
    jslld__mfh = c.builder.call(gscpf__mjflm, [xscjl__xucn.n, xscjl__xucn.
        normalize, cvy__gvjzs, xscjl__xucn.has_kws])
    c.context.nrt.decref(c.builder, typ, val)
    return jslld__mfh


@unbox(DateOffsetType)
def unbox_date_offset(typ, val, c):
    cxpbo__lgj = c.pyapi.object_getattr_string(val, 'n')
    dviv__gydlr = c.pyapi.object_getattr_string(val, 'normalize')
    n = c.pyapi.long_as_longlong(cxpbo__lgj)
    normalize = c.pyapi.to_native_value(types.bool_, dviv__gydlr).value
    cvy__gvjzs = c.builder.alloca(lir.IntType(64), size=lir.Constant(lir.
        IntType(64), 18))
    dyz__yax = lir.FunctionType(lir.IntType(1), [lir.IntType(8).as_pointer(
        ), lir.IntType(64).as_pointer()])
    zmv__jmlc = cgutils.get_or_insert_function(c.builder.module, dyz__yax,
        name='unbox_date_offset')
    has_kws = c.builder.call(zmv__jmlc, [val, cvy__gvjzs])
    xscjl__xucn = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    xscjl__xucn.n = n
    xscjl__xucn.normalize = normalize
    for kkxhr__jrbj, yaakn__fekn in enumerate(date_offset_fields):
        setattr(xscjl__xucn, yaakn__fekn, c.builder.load(c.builder.inttoptr
            (c.builder.add(c.builder.ptrtoint(cvy__gvjzs, lir.IntType(64)),
            lir.Constant(lir.IntType(64), 8 * kkxhr__jrbj)), lir.IntType(64
            ).as_pointer())))
    xscjl__xucn.has_kws = has_kws
    c.pyapi.decref(cxpbo__lgj)
    c.pyapi.decref(dviv__gydlr)
    feriu__hsli = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(xscjl__xucn._getvalue(), is_error=feriu__hsli)


@lower_constant(DateOffsetType)
def lower_constant_date_offset(context, builder, ty, pyval):
    n = context.get_constant(types.int64, pyval.n)
    normalize = context.get_constant(types.boolean, pyval.normalize)
    lahoj__ezo = [n, normalize]
    has_kws = False
    qjzc__kgif = [0] * 9 + [-1] * 9
    for kkxhr__jrbj, yaakn__fekn in enumerate(date_offset_fields):
        if hasattr(pyval, yaakn__fekn):
            upaer__kuf = context.get_constant(types.int64, getattr(pyval,
                yaakn__fekn))
            if yaakn__fekn != 'nanoseconds' and yaakn__fekn != 'nanosecond':
                has_kws = True
        else:
            upaer__kuf = context.get_constant(types.int64, qjzc__kgif[
                kkxhr__jrbj])
        lahoj__ezo.append(upaer__kuf)
    has_kws = context.get_constant(types.boolean, has_kws)
    lahoj__ezo.append(has_kws)
    return lir.Constant.literal_struct(lahoj__ezo)


@overload(pd.tseries.offsets.DateOffset, no_unliteral=True)
def DateOffset(n=1, normalize=False, years=None, months=None, weeks=None,
    days=None, hours=None, minutes=None, seconds=None, microseconds=None,
    nanoseconds=None, year=None, month=None, day=None, weekday=None, hour=
    None, minute=None, second=None, microsecond=None, nanosecond=None):
    has_kws = False
    qpo__hgid = [years, months, weeks, days, hours, minutes, seconds,
        microseconds, year, month, day, weekday, hour, minute, second,
        microsecond]
    for tfd__okbh in qpo__hgid:
        if not is_overload_none(tfd__okbh):
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
        xscjl__xucn = cgutils.create_struct_proxy(typ)(context, builder)
        xscjl__xucn.n = args[0]
        xscjl__xucn.normalize = args[1]
        xscjl__xucn.years = args[2]
        xscjl__xucn.months = args[3]
        xscjl__xucn.weeks = args[4]
        xscjl__xucn.days = args[5]
        xscjl__xucn.hours = args[6]
        xscjl__xucn.minutes = args[7]
        xscjl__xucn.seconds = args[8]
        xscjl__xucn.microseconds = args[9]
        xscjl__xucn.nanoseconds = args[10]
        xscjl__xucn.year = args[11]
        xscjl__xucn.month = args[12]
        xscjl__xucn.day = args[13]
        xscjl__xucn.weekday = args[14]
        xscjl__xucn.hour = args[15]
        xscjl__xucn.minute = args[16]
        xscjl__xucn.second = args[17]
        xscjl__xucn.microsecond = args[18]
        xscjl__xucn.nanosecond = args[19]
        xscjl__xucn.has_kws = args[20]
        return xscjl__xucn._getvalue()
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
        fkvq__iyzo = -1 if dateoffset.n < 0 else 1
        for rkxw__exo in range(np.abs(dateoffset.n)):
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
            year += fkvq__iyzo * dateoffset._years
            if dateoffset._month != -1:
                month = dateoffset._month
            month += fkvq__iyzo * dateoffset._months
            year, month, falrm__shaf = calculate_month_end_date(year, month,
                day, 0)
            if day > falrm__shaf:
                day = falrm__shaf
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
            lfp__itsyj = pd.Timedelta(days=dateoffset._days + 7 *
                dateoffset._weeks, hours=dateoffset._hours, minutes=
                dateoffset._minutes, seconds=dateoffset._seconds,
                microseconds=dateoffset._microseconds)
            if fkvq__iyzo == -1:
                lfp__itsyj = -lfp__itsyj
            ts = ts + lfp__itsyj
            if dateoffset._weekday != -1:
                ajrjo__cirvy = ts.weekday()
                lkw__isw = (dateoffset._weekday - ajrjo__cirvy) % 7
                ts = ts + pd.Timedelta(days=lkw__isw)
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
        awpxl__ckabk = [('n', types.int64), ('normalize', types.boolean), (
            'weekday', types.int64)]
        super(WeekModel, self).__init__(dmm, fe_type, awpxl__ckabk)


make_attribute_wrapper(WeekType, 'n', 'n')
make_attribute_wrapper(WeekType, 'normalize', 'normalize')
make_attribute_wrapper(WeekType, 'weekday', 'weekday')


@overload(pd.tseries.offsets.Week, no_unliteral=True)
def Week(n=1, normalize=False, weekday=None):

    def impl(n=1, normalize=False, weekday=None):
        zwgd__ijfew = -1 if weekday is None else weekday
        return init_week(n, normalize, zwgd__ijfew)
    return impl


@intrinsic
def init_week(typingctx, n, normalize, weekday):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        rheyn__axlez = cgutils.create_struct_proxy(typ)(context, builder)
        rheyn__axlez.n = args[0]
        rheyn__axlez.normalize = args[1]
        rheyn__axlez.weekday = args[2]
        return rheyn__axlez._getvalue()
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
    rheyn__axlez = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    cxpbo__lgj = c.pyapi.long_from_longlong(rheyn__axlez.n)
    dviv__gydlr = c.pyapi.from_native_value(types.boolean, rheyn__axlez.
        normalize, c.env_manager)
    zvriy__hpieb = c.pyapi.long_from_longlong(rheyn__axlez.weekday)
    ogkc__dtt = c.pyapi.unserialize(c.pyapi.serialize_object(pd.tseries.
        offsets.Week))
    yxm__cjdem = c.builder.icmp_signed('!=', lir.Constant(lir.IntType(64), 
        -1), rheyn__axlez.weekday)
    with c.builder.if_else(yxm__cjdem) as (qndo__inuvt, gkkrs__ozlfa):
        with qndo__inuvt:
            qwf__cwws = c.pyapi.call_function_objargs(ogkc__dtt, (
                cxpbo__lgj, dviv__gydlr, zvriy__hpieb))
            lgfdo__ejhw = c.builder.block
        with gkkrs__ozlfa:
            oqq__csb = c.pyapi.call_function_objargs(ogkc__dtt, (cxpbo__lgj,
                dviv__gydlr))
            emp__dkqrz = c.builder.block
    uosz__taa = c.builder.phi(qwf__cwws.type)
    uosz__taa.add_incoming(qwf__cwws, lgfdo__ejhw)
    uosz__taa.add_incoming(oqq__csb, emp__dkqrz)
    c.pyapi.decref(zvriy__hpieb)
    c.pyapi.decref(cxpbo__lgj)
    c.pyapi.decref(dviv__gydlr)
    c.pyapi.decref(ogkc__dtt)
    return uosz__taa


@unbox(WeekType)
def unbox_week(typ, val, c):
    cxpbo__lgj = c.pyapi.object_getattr_string(val, 'n')
    dviv__gydlr = c.pyapi.object_getattr_string(val, 'normalize')
    zvriy__hpieb = c.pyapi.object_getattr_string(val, 'weekday')
    n = c.pyapi.long_as_longlong(cxpbo__lgj)
    normalize = c.pyapi.to_native_value(types.bool_, dviv__gydlr).value
    lzpo__yueiq = c.pyapi.make_none()
    uxjqg__tyrd = c.builder.icmp_unsigned('==', zvriy__hpieb, lzpo__yueiq)
    with c.builder.if_else(uxjqg__tyrd) as (gkkrs__ozlfa, qndo__inuvt):
        with qndo__inuvt:
            qwf__cwws = c.pyapi.long_as_longlong(zvriy__hpieb)
            lgfdo__ejhw = c.builder.block
        with gkkrs__ozlfa:
            oqq__csb = lir.Constant(lir.IntType(64), -1)
            emp__dkqrz = c.builder.block
    uosz__taa = c.builder.phi(qwf__cwws.type)
    uosz__taa.add_incoming(qwf__cwws, lgfdo__ejhw)
    uosz__taa.add_incoming(oqq__csb, emp__dkqrz)
    rheyn__axlez = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    rheyn__axlez.n = n
    rheyn__axlez.normalize = normalize
    rheyn__axlez.weekday = uosz__taa
    c.pyapi.decref(cxpbo__lgj)
    c.pyapi.decref(dviv__gydlr)
    c.pyapi.decref(zvriy__hpieb)
    feriu__hsli = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(rheyn__axlez._getvalue(), is_error=feriu__hsli)


def overload_add_operator_week_offset_type(lhs, rhs):
    if lhs == week_type and rhs == pd_timestamp_type:

        def impl(lhs, rhs):
            fxxd__cqh = calculate_week_date(lhs.n, lhs.weekday, rhs.weekday())
            if lhs.normalize:
                ywva__hudt = pd.Timestamp(year=rhs.year, month=rhs.month,
                    day=rhs.day)
            else:
                ywva__hudt = rhs
            return ywva__hudt + fxxd__cqh
        return impl
    if lhs == week_type and rhs == datetime_datetime_type:

        def impl(lhs, rhs):
            fxxd__cqh = calculate_week_date(lhs.n, lhs.weekday, rhs.weekday())
            if lhs.normalize:
                ywva__hudt = pd.Timestamp(year=rhs.year, month=rhs.month,
                    day=rhs.day)
            else:
                ywva__hudt = pd.Timestamp(year=rhs.year, month=rhs.month,
                    day=rhs.day, hour=rhs.hour, minute=rhs.minute, second=
                    rhs.second, microsecond=rhs.microsecond)
            return ywva__hudt + fxxd__cqh
        return impl
    if lhs == week_type and rhs == datetime_date_type:

        def impl(lhs, rhs):
            fxxd__cqh = calculate_week_date(lhs.n, lhs.weekday, rhs.weekday())
            return rhs + fxxd__cqh
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
        fet__ciy = (weekday - other_weekday) % 7
        if n > 0:
            n = n - 1
    return pd.Timedelta(weeks=n, days=fet__ciy)


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
    for mrax__oebsq in date_offset_unsupported_attrs:
        awxg__kvhto = 'pandas.tseries.offsets.DateOffset.' + mrax__oebsq
        overload_attribute(DateOffsetType, mrax__oebsq)(
            create_unsupported_overload(awxg__kvhto))
    for mrax__oebsq in date_offset_unsupported:
        awxg__kvhto = 'pandas.tseries.offsets.DateOffset.' + mrax__oebsq
        overload_method(DateOffsetType, mrax__oebsq)(
            create_unsupported_overload(awxg__kvhto))


def _install_month_begin_unsupported():
    for mrax__oebsq in month_begin_unsupported_attrs:
        awxg__kvhto = 'pandas.tseries.offsets.MonthBegin.' + mrax__oebsq
        overload_attribute(MonthBeginType, mrax__oebsq)(
            create_unsupported_overload(awxg__kvhto))
    for mrax__oebsq in month_begin_unsupported:
        awxg__kvhto = 'pandas.tseries.offsets.MonthBegin.' + mrax__oebsq
        overload_method(MonthBeginType, mrax__oebsq)(
            create_unsupported_overload(awxg__kvhto))


def _install_month_end_unsupported():
    for mrax__oebsq in date_offset_unsupported_attrs:
        awxg__kvhto = 'pandas.tseries.offsets.MonthEnd.' + mrax__oebsq
        overload_attribute(MonthEndType, mrax__oebsq)(
            create_unsupported_overload(awxg__kvhto))
    for mrax__oebsq in date_offset_unsupported:
        awxg__kvhto = 'pandas.tseries.offsets.MonthEnd.' + mrax__oebsq
        overload_method(MonthEndType, mrax__oebsq)(create_unsupported_overload
            (awxg__kvhto))


def _install_week_unsupported():
    for mrax__oebsq in week_unsupported_attrs:
        awxg__kvhto = 'pandas.tseries.offsets.Week.' + mrax__oebsq
        overload_attribute(WeekType, mrax__oebsq)(create_unsupported_overload
            (awxg__kvhto))
    for mrax__oebsq in week_unsupported:
        awxg__kvhto = 'pandas.tseries.offsets.Week.' + mrax__oebsq
        overload_method(WeekType, mrax__oebsq)(create_unsupported_overload(
            awxg__kvhto))


def _install_offsets_unsupported():
    for upaer__kuf in offsets_unsupported:
        awxg__kvhto = 'pandas.tseries.offsets.' + upaer__kuf.__name__
        overload(upaer__kuf)(create_unsupported_overload(awxg__kvhto))


def _install_frequencies_unsupported():
    for upaer__kuf in frequencies_unsupported:
        awxg__kvhto = 'pandas.tseries.frequencies.' + upaer__kuf.__name__
        overload(upaer__kuf)(create_unsupported_overload(awxg__kvhto))


_install_date_offsets_unsupported()
_install_month_begin_unsupported()
_install_month_end_unsupported()
_install_week_unsupported()
_install_offsets_unsupported()
_install_frequencies_unsupported()
