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
        wqgu__ywv = [('n', types.int64), ('normalize', types.boolean)]
        super(MonthBeginModel, self).__init__(dmm, fe_type, wqgu__ywv)


@box(MonthBeginType)
def box_month_begin(typ, val, c):
    lqsk__dpcfr = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    jkug__ekcfi = c.pyapi.long_from_longlong(lqsk__dpcfr.n)
    xlgh__qhr = c.pyapi.from_native_value(types.boolean, lqsk__dpcfr.
        normalize, c.env_manager)
    ntl__vzgkn = c.pyapi.unserialize(c.pyapi.serialize_object(pd.tseries.
        offsets.MonthBegin))
    rvzl__rxqt = c.pyapi.call_function_objargs(ntl__vzgkn, (jkug__ekcfi,
        xlgh__qhr))
    c.pyapi.decref(jkug__ekcfi)
    c.pyapi.decref(xlgh__qhr)
    c.pyapi.decref(ntl__vzgkn)
    return rvzl__rxqt


@unbox(MonthBeginType)
def unbox_month_begin(typ, val, c):
    jkug__ekcfi = c.pyapi.object_getattr_string(val, 'n')
    xlgh__qhr = c.pyapi.object_getattr_string(val, 'normalize')
    n = c.pyapi.long_as_longlong(jkug__ekcfi)
    normalize = c.pyapi.to_native_value(types.bool_, xlgh__qhr).value
    lqsk__dpcfr = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    lqsk__dpcfr.n = n
    lqsk__dpcfr.normalize = normalize
    c.pyapi.decref(jkug__ekcfi)
    c.pyapi.decref(xlgh__qhr)
    rixs__sbk = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(lqsk__dpcfr._getvalue(), is_error=rixs__sbk)


@overload(pd.tseries.offsets.MonthBegin, no_unliteral=True)
def MonthBegin(n=1, normalize=False):

    def impl(n=1, normalize=False):
        return init_month_begin(n, normalize)
    return impl


@intrinsic
def init_month_begin(typingctx, n, normalize):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        lqsk__dpcfr = cgutils.create_struct_proxy(typ)(context, builder)
        lqsk__dpcfr.n = args[0]
        lqsk__dpcfr.normalize = args[1]
        return lqsk__dpcfr._getvalue()
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
        wqgu__ywv = [('n', types.int64), ('normalize', types.boolean)]
        super(MonthEndModel, self).__init__(dmm, fe_type, wqgu__ywv)


@box(MonthEndType)
def box_month_end(typ, val, c):
    cvyko__tjgqm = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    jkug__ekcfi = c.pyapi.long_from_longlong(cvyko__tjgqm.n)
    xlgh__qhr = c.pyapi.from_native_value(types.boolean, cvyko__tjgqm.
        normalize, c.env_manager)
    kks__sgxhn = c.pyapi.unserialize(c.pyapi.serialize_object(pd.tseries.
        offsets.MonthEnd))
    rvzl__rxqt = c.pyapi.call_function_objargs(kks__sgxhn, (jkug__ekcfi,
        xlgh__qhr))
    c.pyapi.decref(jkug__ekcfi)
    c.pyapi.decref(xlgh__qhr)
    c.pyapi.decref(kks__sgxhn)
    return rvzl__rxqt


@unbox(MonthEndType)
def unbox_month_end(typ, val, c):
    jkug__ekcfi = c.pyapi.object_getattr_string(val, 'n')
    xlgh__qhr = c.pyapi.object_getattr_string(val, 'normalize')
    n = c.pyapi.long_as_longlong(jkug__ekcfi)
    normalize = c.pyapi.to_native_value(types.bool_, xlgh__qhr).value
    cvyko__tjgqm = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    cvyko__tjgqm.n = n
    cvyko__tjgqm.normalize = normalize
    c.pyapi.decref(jkug__ekcfi)
    c.pyapi.decref(xlgh__qhr)
    rixs__sbk = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(cvyko__tjgqm._getvalue(), is_error=rixs__sbk)


@overload(pd.tseries.offsets.MonthEnd, no_unliteral=True)
def MonthEnd(n=1, normalize=False):

    def impl(n=1, normalize=False):
        return init_month_end(n, normalize)
    return impl


@intrinsic
def init_month_end(typingctx, n, normalize):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        cvyko__tjgqm = cgutils.create_struct_proxy(typ)(context, builder)
        cvyko__tjgqm.n = args[0]
        cvyko__tjgqm.normalize = args[1]
        return cvyko__tjgqm._getvalue()
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
        cvyko__tjgqm = get_days_in_month(year, month)
        if cvyko__tjgqm > day:
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
        wqgu__ywv = [('n', types.int64), ('normalize', types.boolean), (
            'years', types.int64), ('months', types.int64), ('weeks', types
            .int64), ('days', types.int64), ('hours', types.int64), (
            'minutes', types.int64), ('seconds', types.int64), (
            'microseconds', types.int64), ('nanoseconds', types.int64), (
            'year', types.int64), ('month', types.int64), ('day', types.
            int64), ('weekday', types.int64), ('hour', types.int64), (
            'minute', types.int64), ('second', types.int64), ('microsecond',
            types.int64), ('nanosecond', types.int64), ('has_kws', types.
            boolean)]
        super(DateOffsetModel, self).__init__(dmm, fe_type, wqgu__ywv)


@box(DateOffsetType)
def box_date_offset(typ, val, c):
    hwz__uicm = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    eeset__bhb = c.builder.alloca(lir.IntType(64), size=lir.Constant(lir.
        IntType(64), 18))
    for ghll__zygwh, aoxuy__fzq in enumerate(date_offset_fields):
        c.builder.store(getattr(hwz__uicm, aoxuy__fzq), c.builder.inttoptr(
            c.builder.add(c.builder.ptrtoint(eeset__bhb, lir.IntType(64)),
            lir.Constant(lir.IntType(64), 8 * ghll__zygwh)), lir.IntType(64
            ).as_pointer()))
    erzv__imwa = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), lir.
        IntType(1), lir.IntType(64).as_pointer(), lir.IntType(1)])
    fzjvd__qnyak = cgutils.get_or_insert_function(c.builder.module,
        erzv__imwa, name='box_date_offset')
    koyp__uwco = c.builder.call(fzjvd__qnyak, [hwz__uicm.n, hwz__uicm.
        normalize, eeset__bhb, hwz__uicm.has_kws])
    c.context.nrt.decref(c.builder, typ, val)
    return koyp__uwco


@unbox(DateOffsetType)
def unbox_date_offset(typ, val, c):
    jkug__ekcfi = c.pyapi.object_getattr_string(val, 'n')
    xlgh__qhr = c.pyapi.object_getattr_string(val, 'normalize')
    n = c.pyapi.long_as_longlong(jkug__ekcfi)
    normalize = c.pyapi.to_native_value(types.bool_, xlgh__qhr).value
    eeset__bhb = c.builder.alloca(lir.IntType(64), size=lir.Constant(lir.
        IntType(64), 18))
    erzv__imwa = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
        as_pointer(), lir.IntType(64).as_pointer()])
    cjilq__qsobt = cgutils.get_or_insert_function(c.builder.module,
        erzv__imwa, name='unbox_date_offset')
    has_kws = c.builder.call(cjilq__qsobt, [val, eeset__bhb])
    hwz__uicm = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    hwz__uicm.n = n
    hwz__uicm.normalize = normalize
    for ghll__zygwh, aoxuy__fzq in enumerate(date_offset_fields):
        setattr(hwz__uicm, aoxuy__fzq, c.builder.load(c.builder.inttoptr(c.
            builder.add(c.builder.ptrtoint(eeset__bhb, lir.IntType(64)),
            lir.Constant(lir.IntType(64), 8 * ghll__zygwh)), lir.IntType(64
            ).as_pointer())))
    hwz__uicm.has_kws = has_kws
    c.pyapi.decref(jkug__ekcfi)
    c.pyapi.decref(xlgh__qhr)
    rixs__sbk = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(hwz__uicm._getvalue(), is_error=rixs__sbk)


@lower_constant(DateOffsetType)
def lower_constant_date_offset(context, builder, ty, pyval):
    n = context.get_constant(types.int64, pyval.n)
    normalize = context.get_constant(types.boolean, pyval.normalize)
    jkcxl__tnj = [n, normalize]
    has_kws = False
    phfr__fchb = [0] * 9 + [-1] * 9
    for ghll__zygwh, aoxuy__fzq in enumerate(date_offset_fields):
        if hasattr(pyval, aoxuy__fzq):
            xilw__lei = context.get_constant(types.int64, getattr(pyval,
                aoxuy__fzq))
            if aoxuy__fzq != 'nanoseconds' and aoxuy__fzq != 'nanosecond':
                has_kws = True
        else:
            xilw__lei = context.get_constant(types.int64, phfr__fchb[
                ghll__zygwh])
        jkcxl__tnj.append(xilw__lei)
    has_kws = context.get_constant(types.boolean, has_kws)
    jkcxl__tnj.append(has_kws)
    return lir.Constant.literal_struct(jkcxl__tnj)


@overload(pd.tseries.offsets.DateOffset, no_unliteral=True)
def DateOffset(n=1, normalize=False, years=None, months=None, weeks=None,
    days=None, hours=None, minutes=None, seconds=None, microseconds=None,
    nanoseconds=None, year=None, month=None, day=None, weekday=None, hour=
    None, minute=None, second=None, microsecond=None, nanosecond=None):
    has_kws = False
    ymvwe__mfj = [years, months, weeks, days, hours, minutes, seconds,
        microseconds, year, month, day, weekday, hour, minute, second,
        microsecond]
    for ovlrh__jwhgy in ymvwe__mfj:
        if not is_overload_none(ovlrh__jwhgy):
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
        hwz__uicm = cgutils.create_struct_proxy(typ)(context, builder)
        hwz__uicm.n = args[0]
        hwz__uicm.normalize = args[1]
        hwz__uicm.years = args[2]
        hwz__uicm.months = args[3]
        hwz__uicm.weeks = args[4]
        hwz__uicm.days = args[5]
        hwz__uicm.hours = args[6]
        hwz__uicm.minutes = args[7]
        hwz__uicm.seconds = args[8]
        hwz__uicm.microseconds = args[9]
        hwz__uicm.nanoseconds = args[10]
        hwz__uicm.year = args[11]
        hwz__uicm.month = args[12]
        hwz__uicm.day = args[13]
        hwz__uicm.weekday = args[14]
        hwz__uicm.hour = args[15]
        hwz__uicm.minute = args[16]
        hwz__uicm.second = args[17]
        hwz__uicm.microsecond = args[18]
        hwz__uicm.nanosecond = args[19]
        hwz__uicm.has_kws = args[20]
        return hwz__uicm._getvalue()
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
        vtj__wol = -1 if dateoffset.n < 0 else 1
        for prdkp__lqaoc in range(np.abs(dateoffset.n)):
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
            year += vtj__wol * dateoffset._years
            if dateoffset._month != -1:
                month = dateoffset._month
            month += vtj__wol * dateoffset._months
            year, month, muqx__huzwc = calculate_month_end_date(year, month,
                day, 0)
            if day > muqx__huzwc:
                day = muqx__huzwc
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
            gxsz__avi = pd.Timedelta(days=dateoffset._days + 7 * dateoffset
                ._weeks, hours=dateoffset._hours, minutes=dateoffset.
                _minutes, seconds=dateoffset._seconds, microseconds=
                dateoffset._microseconds)
            if vtj__wol == -1:
                gxsz__avi = -gxsz__avi
            ts = ts + gxsz__avi
            if dateoffset._weekday != -1:
                smtwr__duffn = ts.weekday()
                msr__dzch = (dateoffset._weekday - smtwr__duffn) % 7
                ts = ts + pd.Timedelta(days=msr__dzch)
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
        wqgu__ywv = [('n', types.int64), ('normalize', types.boolean), (
            'weekday', types.int64)]
        super(WeekModel, self).__init__(dmm, fe_type, wqgu__ywv)


make_attribute_wrapper(WeekType, 'n', 'n')
make_attribute_wrapper(WeekType, 'normalize', 'normalize')
make_attribute_wrapper(WeekType, 'weekday', 'weekday')


@overload(pd.tseries.offsets.Week, no_unliteral=True)
def Week(n=1, normalize=False, weekday=None):

    def impl(n=1, normalize=False, weekday=None):
        jyovn__xvmo = -1 if weekday is None else weekday
        return init_week(n, normalize, jyovn__xvmo)
    return impl


@intrinsic
def init_week(typingctx, n, normalize, weekday):

    def codegen(context, builder, signature, args):
        typ = signature.return_type
        gfr__hkx = cgutils.create_struct_proxy(typ)(context, builder)
        gfr__hkx.n = args[0]
        gfr__hkx.normalize = args[1]
        gfr__hkx.weekday = args[2]
        return gfr__hkx._getvalue()
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
    gfr__hkx = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val
        )
    jkug__ekcfi = c.pyapi.long_from_longlong(gfr__hkx.n)
    xlgh__qhr = c.pyapi.from_native_value(types.boolean, gfr__hkx.normalize,
        c.env_manager)
    jvu__ehli = c.pyapi.long_from_longlong(gfr__hkx.weekday)
    pco__thg = c.pyapi.unserialize(c.pyapi.serialize_object(pd.tseries.
        offsets.Week))
    zkc__ecsko = c.builder.icmp_signed('!=', lir.Constant(lir.IntType(64), 
        -1), gfr__hkx.weekday)
    with c.builder.if_else(zkc__ecsko) as (lqdmt__mnehc, xjmpr__tike):
        with lqdmt__mnehc:
            fadm__wpul = c.pyapi.call_function_objargs(pco__thg, (
                jkug__ekcfi, xlgh__qhr, jvu__ehli))
            bix__uygyv = c.builder.block
        with xjmpr__tike:
            rohsa__akxs = c.pyapi.call_function_objargs(pco__thg, (
                jkug__ekcfi, xlgh__qhr))
            jcc__zeycf = c.builder.block
    rvzl__rxqt = c.builder.phi(fadm__wpul.type)
    rvzl__rxqt.add_incoming(fadm__wpul, bix__uygyv)
    rvzl__rxqt.add_incoming(rohsa__akxs, jcc__zeycf)
    c.pyapi.decref(jvu__ehli)
    c.pyapi.decref(jkug__ekcfi)
    c.pyapi.decref(xlgh__qhr)
    c.pyapi.decref(pco__thg)
    return rvzl__rxqt


@unbox(WeekType)
def unbox_week(typ, val, c):
    jkug__ekcfi = c.pyapi.object_getattr_string(val, 'n')
    xlgh__qhr = c.pyapi.object_getattr_string(val, 'normalize')
    jvu__ehli = c.pyapi.object_getattr_string(val, 'weekday')
    n = c.pyapi.long_as_longlong(jkug__ekcfi)
    normalize = c.pyapi.to_native_value(types.bool_, xlgh__qhr).value
    kzek__inf = c.pyapi.make_none()
    egtxn__xiyrr = c.builder.icmp_unsigned('==', jvu__ehli, kzek__inf)
    with c.builder.if_else(egtxn__xiyrr) as (xjmpr__tike, lqdmt__mnehc):
        with lqdmt__mnehc:
            fadm__wpul = c.pyapi.long_as_longlong(jvu__ehli)
            bix__uygyv = c.builder.block
        with xjmpr__tike:
            rohsa__akxs = lir.Constant(lir.IntType(64), -1)
            jcc__zeycf = c.builder.block
    rvzl__rxqt = c.builder.phi(fadm__wpul.type)
    rvzl__rxqt.add_incoming(fadm__wpul, bix__uygyv)
    rvzl__rxqt.add_incoming(rohsa__akxs, jcc__zeycf)
    gfr__hkx = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    gfr__hkx.n = n
    gfr__hkx.normalize = normalize
    gfr__hkx.weekday = rvzl__rxqt
    c.pyapi.decref(jkug__ekcfi)
    c.pyapi.decref(xlgh__qhr)
    c.pyapi.decref(jvu__ehli)
    rixs__sbk = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(gfr__hkx._getvalue(), is_error=rixs__sbk)


def overload_add_operator_week_offset_type(lhs, rhs):
    if lhs == week_type and rhs == pd_timestamp_type:

        def impl(lhs, rhs):
            hfx__now = calculate_week_date(lhs.n, lhs.weekday, rhs.weekday())
            if lhs.normalize:
                vov__zch = pd.Timestamp(year=rhs.year, month=rhs.month, day
                    =rhs.day)
            else:
                vov__zch = rhs
            return vov__zch + hfx__now
        return impl
    if lhs == week_type and rhs == datetime_datetime_type:

        def impl(lhs, rhs):
            hfx__now = calculate_week_date(lhs.n, lhs.weekday, rhs.weekday())
            if lhs.normalize:
                vov__zch = pd.Timestamp(year=rhs.year, month=rhs.month, day
                    =rhs.day)
            else:
                vov__zch = pd.Timestamp(year=rhs.year, month=rhs.month, day
                    =rhs.day, hour=rhs.hour, minute=rhs.minute, second=rhs.
                    second, microsecond=rhs.microsecond)
            return vov__zch + hfx__now
        return impl
    if lhs == week_type and rhs == datetime_date_type:

        def impl(lhs, rhs):
            hfx__now = calculate_week_date(lhs.n, lhs.weekday, rhs.weekday())
            return rhs + hfx__now
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
        qrhfq__mbyjw = (weekday - other_weekday) % 7
        if n > 0:
            n = n - 1
    return pd.Timedelta(weeks=n, days=qrhfq__mbyjw)


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
    for wwp__lkm in date_offset_unsupported_attrs:
        icb__uuv = 'pandas.tseries.offsets.DateOffset.' + wwp__lkm
        overload_attribute(DateOffsetType, wwp__lkm)(
            create_unsupported_overload(icb__uuv))
    for wwp__lkm in date_offset_unsupported:
        icb__uuv = 'pandas.tseries.offsets.DateOffset.' + wwp__lkm
        overload_method(DateOffsetType, wwp__lkm)(create_unsupported_overload
            (icb__uuv))


def _install_month_begin_unsupported():
    for wwp__lkm in month_begin_unsupported_attrs:
        icb__uuv = 'pandas.tseries.offsets.MonthBegin.' + wwp__lkm
        overload_attribute(MonthBeginType, wwp__lkm)(
            create_unsupported_overload(icb__uuv))
    for wwp__lkm in month_begin_unsupported:
        icb__uuv = 'pandas.tseries.offsets.MonthBegin.' + wwp__lkm
        overload_method(MonthBeginType, wwp__lkm)(create_unsupported_overload
            (icb__uuv))


def _install_month_end_unsupported():
    for wwp__lkm in date_offset_unsupported_attrs:
        icb__uuv = 'pandas.tseries.offsets.MonthEnd.' + wwp__lkm
        overload_attribute(MonthEndType, wwp__lkm)(create_unsupported_overload
            (icb__uuv))
    for wwp__lkm in date_offset_unsupported:
        icb__uuv = 'pandas.tseries.offsets.MonthEnd.' + wwp__lkm
        overload_method(MonthEndType, wwp__lkm)(create_unsupported_overload
            (icb__uuv))


def _install_week_unsupported():
    for wwp__lkm in week_unsupported_attrs:
        icb__uuv = 'pandas.tseries.offsets.Week.' + wwp__lkm
        overload_attribute(WeekType, wwp__lkm)(create_unsupported_overload(
            icb__uuv))
    for wwp__lkm in week_unsupported:
        icb__uuv = 'pandas.tseries.offsets.Week.' + wwp__lkm
        overload_method(WeekType, wwp__lkm)(create_unsupported_overload(
            icb__uuv))


def _install_offsets_unsupported():
    for xilw__lei in offsets_unsupported:
        icb__uuv = 'pandas.tseries.offsets.' + xilw__lei.__name__
        overload(xilw__lei)(create_unsupported_overload(icb__uuv))


def _install_frequencies_unsupported():
    for xilw__lei in frequencies_unsupported:
        icb__uuv = 'pandas.tseries.frequencies.' + xilw__lei.__name__
        overload(xilw__lei)(create_unsupported_overload(icb__uuv))


_install_date_offsets_unsupported()
_install_month_begin_unsupported()
_install_month_end_unsupported()
_install_week_unsupported()
_install_offsets_unsupported()
_install_frequencies_unsupported()
