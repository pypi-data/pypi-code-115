"""Timestamp extension for Pandas Timestamp with timezone support."""
import calendar
import datetime
import operator
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
import pytz
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import lower_constant
from numba.core.typing.templates import ConcreteTemplate, infer_global, signature
from numba.extending import NativeValue, box, intrinsic, lower_builtin, lower_cast, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_jitable, register_model, typeof_impl, unbox
import bodo.libs.str_ext
import bodo.utils.utils
from bodo.hiframes.datetime_date_ext import DatetimeDateType, _ord2ymd, _ymd2ord, get_isocalendar
from bodo.hiframes.datetime_timedelta_ext import PDTimeDeltaType, _no_input, datetime_timedelta_type, pd_timedelta_type
from bodo.hiframes.pd_categorical_ext import CategoricalArrayType
from bodo.libs import hdatetime_ext
from bodo.libs.pd_datetime_arr_ext import get_pytz_type_info
from bodo.libs.str_arr_ext import string_array_type
from bodo.utils.typing import BodoError, check_unsupported_args, get_overload_const_bool, get_overload_const_int, get_overload_const_str, is_iterable_type, is_overload_constant_int, is_overload_constant_str, is_overload_none, raise_bodo_error
ll.add_symbol('extract_year_days', hdatetime_ext.extract_year_days)
ll.add_symbol('get_month_day', hdatetime_ext.get_month_day)
ll.add_symbol('npy_datetimestruct_to_datetime', hdatetime_ext.
    npy_datetimestruct_to_datetime)
npy_datetimestruct_to_datetime = types.ExternalFunction(
    'npy_datetimestruct_to_datetime', types.int64(types.int64, types.int32,
    types.int32, types.int32, types.int32, types.int32, types.int32))
date_fields = ['year', 'month', 'day', 'hour', 'minute', 'second',
    'microsecond', 'nanosecond', 'quarter', 'dayofyear', 'day_of_year',
    'dayofweek', 'day_of_week', 'daysinmonth', 'days_in_month',
    'is_leap_year', 'is_month_start', 'is_month_end', 'is_quarter_start',
    'is_quarter_end', 'is_year_start', 'is_year_end', 'week', 'weekofyear',
    'weekday']
date_methods = ['normalize', 'day_name', 'month_name']
timedelta_fields = ['days', 'seconds', 'microseconds', 'nanoseconds']
timedelta_methods = ['total_seconds', 'to_pytimedelta']
iNaT = pd._libs.tslibs.iNaT


class PandasTimestampType(types.Type):

    def __init__(self, tz_val=None):
        self.tz = tz_val
        if tz_val is None:
            ngrr__gxgh = 'PandasTimestampType()'
        else:
            ngrr__gxgh = f'PandasTimestampType({tz_val})'
        super(PandasTimestampType, self).__init__(name=ngrr__gxgh)


pd_timestamp_type = PandasTimestampType()


@typeof_impl.register(pd.Timestamp)
def typeof_pd_timestamp(val, c):
    return PandasTimestampType(get_pytz_type_info(val.tz) if val.tz else None)


ts_field_typ = types.int64


@register_model(PandasTimestampType)
class PandasTimestampModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        lrd__gjslt = [('year', ts_field_typ), ('month', ts_field_typ), (
            'day', ts_field_typ), ('hour', ts_field_typ), ('minute',
            ts_field_typ), ('second', ts_field_typ), ('microsecond',
            ts_field_typ), ('nanosecond', ts_field_typ), ('value',
            ts_field_typ)]
        models.StructModel.__init__(self, dmm, fe_type, lrd__gjslt)


make_attribute_wrapper(PandasTimestampType, 'year', 'year')
make_attribute_wrapper(PandasTimestampType, 'month', 'month')
make_attribute_wrapper(PandasTimestampType, 'day', 'day')
make_attribute_wrapper(PandasTimestampType, 'hour', 'hour')
make_attribute_wrapper(PandasTimestampType, 'minute', 'minute')
make_attribute_wrapper(PandasTimestampType, 'second', 'second')
make_attribute_wrapper(PandasTimestampType, 'microsecond', 'microsecond')
make_attribute_wrapper(PandasTimestampType, 'nanosecond', 'nanosecond')
make_attribute_wrapper(PandasTimestampType, 'value', 'value')


@unbox(PandasTimestampType)
def unbox_pandas_timestamp(typ, val, c):
    hmg__plk = c.pyapi.object_getattr_string(val, 'year')
    ydrg__avulu = c.pyapi.object_getattr_string(val, 'month')
    cyfk__vro = c.pyapi.object_getattr_string(val, 'day')
    sicln__fyy = c.pyapi.object_getattr_string(val, 'hour')
    wmwih__jjc = c.pyapi.object_getattr_string(val, 'minute')
    ctz__xqabp = c.pyapi.object_getattr_string(val, 'second')
    otymr__yalk = c.pyapi.object_getattr_string(val, 'microsecond')
    mmxor__szv = c.pyapi.object_getattr_string(val, 'nanosecond')
    erz__qaz = c.pyapi.object_getattr_string(val, 'value')
    jfb__olqy = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    jfb__olqy.year = c.pyapi.long_as_longlong(hmg__plk)
    jfb__olqy.month = c.pyapi.long_as_longlong(ydrg__avulu)
    jfb__olqy.day = c.pyapi.long_as_longlong(cyfk__vro)
    jfb__olqy.hour = c.pyapi.long_as_longlong(sicln__fyy)
    jfb__olqy.minute = c.pyapi.long_as_longlong(wmwih__jjc)
    jfb__olqy.second = c.pyapi.long_as_longlong(ctz__xqabp)
    jfb__olqy.microsecond = c.pyapi.long_as_longlong(otymr__yalk)
    jfb__olqy.nanosecond = c.pyapi.long_as_longlong(mmxor__szv)
    jfb__olqy.value = c.pyapi.long_as_longlong(erz__qaz)
    c.pyapi.decref(hmg__plk)
    c.pyapi.decref(ydrg__avulu)
    c.pyapi.decref(cyfk__vro)
    c.pyapi.decref(sicln__fyy)
    c.pyapi.decref(wmwih__jjc)
    c.pyapi.decref(ctz__xqabp)
    c.pyapi.decref(otymr__yalk)
    c.pyapi.decref(mmxor__szv)
    c.pyapi.decref(erz__qaz)
    hxlgw__num = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(jfb__olqy._getvalue(), is_error=hxlgw__num)


@box(PandasTimestampType)
def box_pandas_timestamp(typ, val, c):
    aupj__itxu = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    hmg__plk = c.pyapi.long_from_longlong(aupj__itxu.year)
    ydrg__avulu = c.pyapi.long_from_longlong(aupj__itxu.month)
    cyfk__vro = c.pyapi.long_from_longlong(aupj__itxu.day)
    sicln__fyy = c.pyapi.long_from_longlong(aupj__itxu.hour)
    wmwih__jjc = c.pyapi.long_from_longlong(aupj__itxu.minute)
    ctz__xqabp = c.pyapi.long_from_longlong(aupj__itxu.second)
    ipblw__nbup = c.pyapi.long_from_longlong(aupj__itxu.microsecond)
    mhjm__lzgq = c.pyapi.long_from_longlong(aupj__itxu.nanosecond)
    gzqsm__dau = c.pyapi.unserialize(c.pyapi.serialize_object(pd.Timestamp))
    if typ.tz is None:
        res = c.pyapi.call_function_objargs(gzqsm__dau, (hmg__plk,
            ydrg__avulu, cyfk__vro, sicln__fyy, wmwih__jjc, ctz__xqabp,
            ipblw__nbup, mhjm__lzgq))
    else:
        if isinstance(typ.tz, int):
            uzoux__alaig = c.pyapi.long_from_longlong(lir.Constant(lir.
                IntType(64), typ.tz))
        else:
            jlu__lmt = c.context.insert_const_string(c.builder.module, str(
                typ.tz))
            uzoux__alaig = c.pyapi.string_from_string(jlu__lmt)
        args = c.pyapi.tuple_pack(())
        kwargs = c.pyapi.dict_pack([('year', hmg__plk), ('month',
            ydrg__avulu), ('day', cyfk__vro), ('hour', sicln__fyy), (
            'minute', wmwih__jjc), ('second', ctz__xqabp), ('microsecond',
            ipblw__nbup), ('nanosecond', mhjm__lzgq), ('tz', uzoux__alaig)])
        res = c.pyapi.call(gzqsm__dau, args, kwargs)
        c.pyapi.decref(args)
        c.pyapi.decref(kwargs)
        c.pyapi.decref(uzoux__alaig)
    c.pyapi.decref(hmg__plk)
    c.pyapi.decref(ydrg__avulu)
    c.pyapi.decref(cyfk__vro)
    c.pyapi.decref(sicln__fyy)
    c.pyapi.decref(wmwih__jjc)
    c.pyapi.decref(ctz__xqabp)
    c.pyapi.decref(ipblw__nbup)
    c.pyapi.decref(mhjm__lzgq)
    return res


@intrinsic
def init_timestamp(typingctx, year, month, day, hour, minute, second,
    microsecond, nanosecond, value, tz):

    def codegen(context, builder, sig, args):
        (year, month, day, hour, minute, second, gul__hhu, sim__hfjub,
            value, cmfm__isap) = args
        ts = cgutils.create_struct_proxy(sig.return_type)(context, builder)
        ts.year = year
        ts.month = month
        ts.day = day
        ts.hour = hour
        ts.minute = minute
        ts.second = second
        ts.microsecond = gul__hhu
        ts.nanosecond = sim__hfjub
        ts.value = value
        return ts._getvalue()
    if is_overload_none(tz):
        typ = pd_timestamp_type
    elif is_overload_constant_str(tz):
        typ = PandasTimestampType(get_overload_const_str(tz))
    elif is_overload_constant_int(tz):
        typ = PandasTimestampType(get_overload_const_int(tz))
    else:
        raise_bodo_error('tz must be a constant string, int, or None')
    return typ(types.int64, types.int64, types.int64, types.int64, types.
        int64, types.int64, types.int64, types.int64, types.int64, tz), codegen


@numba.generated_jit
def zero_if_none(value):
    if value == types.none:
        return lambda value: 0
    return lambda value: value


@lower_constant(PandasTimestampType)
def constant_timestamp(context, builder, ty, pyval):
    year = context.get_constant(types.int64, pyval.year)
    month = context.get_constant(types.int64, pyval.month)
    day = context.get_constant(types.int64, pyval.day)
    hour = context.get_constant(types.int64, pyval.hour)
    minute = context.get_constant(types.int64, pyval.minute)
    second = context.get_constant(types.int64, pyval.second)
    microsecond = context.get_constant(types.int64, pyval.microsecond)
    nanosecond = context.get_constant(types.int64, pyval.nanosecond)
    value = context.get_constant(types.int64, pyval.value)
    return lir.Constant.literal_struct((year, month, day, hour, minute,
        second, microsecond, nanosecond, value))


@overload(pd.Timestamp, no_unliteral=True)
def overload_pd_timestamp(ts_input=_no_input, freq=None, tz=None, unit=None,
    year=None, month=None, day=None, hour=None, minute=None, second=None,
    microsecond=None, nanosecond=None, tzinfo=None):
    if not is_overload_none(tz) and is_overload_constant_str(tz
        ) and get_overload_const_str(tz) not in pytz.all_timezones_set:
        raise BodoError(
            "pandas.Timestamp(): 'tz', if provided, must be constant string found in pytz.all_timezones"
            )
    if ts_input == _no_input or getattr(ts_input, 'value', None) == _no_input:

        def impl_kw(ts_input=_no_input, freq=None, tz=None, unit=None, year
            =None, month=None, day=None, hour=None, minute=None, second=
            None, microsecond=None, nanosecond=None, tzinfo=None):
            value = npy_datetimestruct_to_datetime(year, month, day,
                zero_if_none(hour), zero_if_none(minute), zero_if_none(
                second), zero_if_none(microsecond))
            value += zero_if_none(nanosecond)
            return init_timestamp(year, month, day, zero_if_none(hour),
                zero_if_none(minute), zero_if_none(second), zero_if_none(
                microsecond), zero_if_none(nanosecond), value, tz)
        return impl_kw
    if isinstance(types.unliteral(freq), types.Integer):

        def impl_pos(ts_input=_no_input, freq=None, tz=None, unit=None,
            year=None, month=None, day=None, hour=None, minute=None, second
            =None, microsecond=None, nanosecond=None, tzinfo=None):
            value = npy_datetimestruct_to_datetime(ts_input, freq, tz,
                zero_if_none(unit), zero_if_none(year), zero_if_none(month),
                zero_if_none(day))
            value += zero_if_none(hour)
            return init_timestamp(ts_input, freq, tz, zero_if_none(unit),
                zero_if_none(year), zero_if_none(month), zero_if_none(day),
                zero_if_none(hour), value, None)
        return impl_pos
    if isinstance(ts_input, types.Number):
        if is_overload_none(unit):
            unit = 'ns'
        if not is_overload_constant_str(unit):
            raise BodoError(
                'pandas.Timedelta(): unit argument must be a constant str')
        unit = pd._libs.tslibs.timedeltas.parse_timedelta_unit(
            get_overload_const_str(unit))
        hlygf__vgnyi, precision = (pd._libs.tslibs.conversion.
            precision_from_unit(unit))
        if isinstance(ts_input, types.Integer):

            def impl_int(ts_input=_no_input, freq=None, tz=None, unit=None,
                year=None, month=None, day=None, hour=None, minute=None,
                second=None, microsecond=None, nanosecond=None, tzinfo=None):
                value = ts_input * hlygf__vgnyi
                return convert_val_to_timestamp(value, tz)
            return impl_int

        def impl_float(ts_input=_no_input, freq=None, tz=None, unit=None,
            year=None, month=None, day=None, hour=None, minute=None, second
            =None, microsecond=None, nanosecond=None, tzinfo=None):
            cln__clh = np.int64(ts_input)
            tig__krd = ts_input - cln__clh
            if precision:
                tig__krd = np.round(tig__krd, precision)
            value = cln__clh * hlygf__vgnyi + np.int64(tig__krd * hlygf__vgnyi)
            return convert_val_to_timestamp(value, tz)
        return impl_float
    if ts_input == bodo.string_type or is_overload_constant_str(ts_input):
        types.pd_timestamp_type = pd_timestamp_type
        if is_overload_none(tz):
            tz_val = None
        elif is_overload_constant_str(tz):
            tz_val = get_overload_const_str(tz)
        else:
            raise_bodo_error(
                'pandas.Timestamp(): tz argument must be a constant string or None'
                )
        typ = PandasTimestampType(tz_val)

        def impl_str(ts_input=_no_input, freq=None, tz=None, unit=None,
            year=None, month=None, day=None, hour=None, minute=None, second
            =None, microsecond=None, nanosecond=None, tzinfo=None):
            with numba.objmode(res=typ):
                res = pd.Timestamp(ts_input, tz=tz)
            return res
        return impl_str
    if ts_input == pd_timestamp_type:
        return (lambda ts_input=_no_input, freq=None, tz=None, unit=None,
            year=None, month=None, day=None, hour=None, minute=None, second
            =None, microsecond=None, nanosecond=None, tzinfo=None: ts_input)
    if ts_input == bodo.hiframes.datetime_datetime_ext.datetime_datetime_type:

        def impl_datetime(ts_input=_no_input, freq=None, tz=None, unit=None,
            year=None, month=None, day=None, hour=None, minute=None, second
            =None, microsecond=None, nanosecond=None, tzinfo=None):
            year = ts_input.year
            month = ts_input.month
            day = ts_input.day
            hour = ts_input.hour
            minute = ts_input.minute
            second = ts_input.second
            microsecond = ts_input.microsecond
            value = npy_datetimestruct_to_datetime(year, month, day,
                zero_if_none(hour), zero_if_none(minute), zero_if_none(
                second), zero_if_none(microsecond))
            value += zero_if_none(nanosecond)
            return init_timestamp(year, month, day, zero_if_none(hour),
                zero_if_none(minute), zero_if_none(second), zero_if_none(
                microsecond), zero_if_none(nanosecond), value, tz)
        return impl_datetime
    if ts_input == bodo.hiframes.datetime_date_ext.datetime_date_type:

        def impl_date(ts_input=_no_input, freq=None, tz=None, unit=None,
            year=None, month=None, day=None, hour=None, minute=None, second
            =None, microsecond=None, nanosecond=None, tzinfo=None):
            year = ts_input.year
            month = ts_input.month
            day = ts_input.day
            value = npy_datetimestruct_to_datetime(year, month, day,
                zero_if_none(hour), zero_if_none(minute), zero_if_none(
                second), zero_if_none(microsecond))
            value += zero_if_none(nanosecond)
            return init_timestamp(year, month, day, zero_if_none(hour),
                zero_if_none(minute), zero_if_none(second), zero_if_none(
                microsecond), zero_if_none(nanosecond), value, None)
        return impl_date
    if isinstance(ts_input, numba.core.types.scalars.NPDatetime):
        hlygf__vgnyi, precision = (pd._libs.tslibs.conversion.
            precision_from_unit(ts_input.unit))

        def impl_date(ts_input=_no_input, freq=None, tz=None, unit=None,
            year=None, month=None, day=None, hour=None, minute=None, second
            =None, microsecond=None, nanosecond=None, tzinfo=None):
            value = np.int64(ts_input) * hlygf__vgnyi
            return convert_datetime64_to_timestamp(integer_to_dt64(value))
        return impl_date


@overload_attribute(PandasTimestampType, 'dayofyear')
@overload_attribute(PandasTimestampType, 'day_of_year')
def overload_pd_dayofyear(ptt):

    def pd_dayofyear(ptt):
        return get_day_of_year(ptt.year, ptt.month, ptt.day)
    return pd_dayofyear


@overload_method(PandasTimestampType, 'weekday')
@overload_attribute(PandasTimestampType, 'dayofweek')
@overload_attribute(PandasTimestampType, 'day_of_week')
def overload_pd_dayofweek(ptt):

    def pd_dayofweek(ptt):
        return get_day_of_week(ptt.year, ptt.month, ptt.day)
    return pd_dayofweek


@overload_attribute(PandasTimestampType, 'week')
@overload_attribute(PandasTimestampType, 'weekofyear')
def overload_week_number(ptt):

    def pd_week_number(ptt):
        cmfm__isap, zqbz__nri, cmfm__isap = get_isocalendar(ptt.year, ptt.
            month, ptt.day)
        return zqbz__nri
    return pd_week_number


@overload_method(PandasTimestampType, '__hash__', no_unliteral=True)
def dt64_hash(val):
    return lambda val: hash(val.value)


@overload_attribute(PandasTimestampType, 'days_in_month')
@overload_attribute(PandasTimestampType, 'daysinmonth')
def overload_pd_daysinmonth(ptt):

    def pd_daysinmonth(ptt):
        return get_days_in_month(ptt.year, ptt.month)
    return pd_daysinmonth


@overload_attribute(PandasTimestampType, 'is_leap_year')
def overload_pd_is_leap_year(ptt):

    def pd_is_leap_year(ptt):
        return is_leap_year(ptt.year)
    return pd_is_leap_year


@overload_attribute(PandasTimestampType, 'is_month_start')
def overload_pd_is_month_start(ptt):

    def pd_is_month_start(ptt):
        return ptt.day == 1
    return pd_is_month_start


@overload_attribute(PandasTimestampType, 'is_month_end')
def overload_pd_is_month_end(ptt):

    def pd_is_month_end(ptt):
        return ptt.day == get_days_in_month(ptt.year, ptt.month)
    return pd_is_month_end


@overload_attribute(PandasTimestampType, 'is_quarter_start')
def overload_pd_is_quarter_start(ptt):

    def pd_is_quarter_start(ptt):
        return ptt.day == 1 and ptt.month % 3 == 1
    return pd_is_quarter_start


@overload_attribute(PandasTimestampType, 'is_quarter_end')
def overload_pd_is_quarter_end(ptt):

    def pd_is_quarter_end(ptt):
        return ptt.month % 3 == 0 and ptt.day == get_days_in_month(ptt.year,
            ptt.month)
    return pd_is_quarter_end


@overload_attribute(PandasTimestampType, 'is_year_start')
def overload_pd_is_year_start(ptt):

    def pd_is_year_start(ptt):
        return ptt.day == 1 and ptt.month == 1
    return pd_is_year_start


@overload_attribute(PandasTimestampType, 'is_year_end')
def overload_pd_is_year_end(ptt):

    def pd_is_year_end(ptt):
        return ptt.day == 31 and ptt.month == 12
    return pd_is_year_end


@overload_attribute(PandasTimestampType, 'quarter')
def overload_quarter(ptt):

    def quarter(ptt):
        return (ptt.month - 1) // 3 + 1
    return quarter


@overload_method(PandasTimestampType, 'date', no_unliteral=True)
def overload_pd_timestamp_date(ptt):

    def pd_timestamp_date_impl(ptt):
        return datetime.date(ptt.year, ptt.month, ptt.day)
    return pd_timestamp_date_impl


@overload_method(PandasTimestampType, 'isocalendar', no_unliteral=True)
def overload_pd_timestamp_isocalendar(ptt):

    def impl(ptt):
        year, zqbz__nri, oiys__jgxeh = get_isocalendar(ptt.year, ptt.month,
            ptt.day)
        return year, zqbz__nri, oiys__jgxeh
    return impl


@overload_method(PandasTimestampType, 'isoformat', no_unliteral=True)
def overload_pd_timestamp_isoformat(ts, sep=None):
    if is_overload_none(sep):

        def timestamp_isoformat_impl(ts, sep=None):
            assert ts.nanosecond == 0
            zqf__dnam = str_2d(ts.hour) + ':' + str_2d(ts.minute
                ) + ':' + str_2d(ts.second)
            res = str(ts.year) + '-' + str_2d(ts.month) + '-' + str_2d(ts.day
                ) + 'T' + zqf__dnam
            return res
        return timestamp_isoformat_impl
    else:

        def timestamp_isoformat_impl(ts, sep=None):
            assert ts.nanosecond == 0
            zqf__dnam = str_2d(ts.hour) + ':' + str_2d(ts.minute
                ) + ':' + str_2d(ts.second)
            res = str(ts.year) + '-' + str_2d(ts.month) + '-' + str_2d(ts.day
                ) + sep + zqf__dnam
            return res
    return timestamp_isoformat_impl


@overload_method(PandasTimestampType, 'normalize', no_unliteral=True)
def overload_pd_timestamp_normalize(ptt):

    def impl(ptt):
        return pd.Timestamp(year=ptt.year, month=ptt.month, day=ptt.day)
    return impl


@overload_method(PandasTimestampType, 'day_name', no_unliteral=True)
def overload_pd_timestamp_day_name(ptt, locale=None):
    cdwfp__vfss = dict(locale=locale)
    qnixy__mgfzs = dict(locale=None)
    check_unsupported_args('Timestamp.day_name', cdwfp__vfss, qnixy__mgfzs,
        package_name='pandas', module_name='Timestamp')

    def impl(ptt, locale=None):
        wzqqt__oat = ('Monday', 'Tuesday', 'Wednesday', 'Thursday',
            'Friday', 'Saturday', 'Sunday')
        cmfm__isap, cmfm__isap, vyb__akfbs = ptt.isocalendar()
        return wzqqt__oat[vyb__akfbs - 1]
    return impl


@overload_method(PandasTimestampType, 'month_name', no_unliteral=True)
def overload_pd_timestamp_month_name(ptt, locale=None):
    cdwfp__vfss = dict(locale=locale)
    qnixy__mgfzs = dict(locale=None)
    check_unsupported_args('Timestamp.month_name', cdwfp__vfss,
        qnixy__mgfzs, package_name='pandas', module_name='Timestamp')

    def impl(ptt, locale=None):
        ldqzx__tckxd = ('January', 'February', 'March', 'April', 'May',
            'June', 'July', 'August', 'September', 'October', 'November',
            'December')
        return ldqzx__tckxd[ptt.month - 1]
    return impl


@overload_method(PandasTimestampType, 'tz_convert', no_unliteral=True)
def overload_pd_timestamp_tz_convert(ptt, tz):
    if ptt.tz is None:
        raise BodoError(
            'Cannot convert tz-naive Timestamp, use tz_localize to localize')
    if is_overload_none(tz):
        return lambda ptt, tz: convert_val_to_timestamp(ptt.value)
    elif is_overload_constant_str(tz):
        return lambda ptt, tz: convert_val_to_timestamp(ptt.value, tz=tz)


@overload_method(PandasTimestampType, 'tz_localize', no_unliteral=True)
def overload_pd_timestamp_tz_localize(ptt, tz, ambiguous='raise',
    nonexistent='raise'):
    if ptt.tz is not None and not is_overload_none(tz):
        raise BodoError(
            'Cannot localize tz-aware Timestamp, use tz_convert for conversions'
            )
    cdwfp__vfss = dict(ambiguous=ambiguous, nonexistent=nonexistent)
    pzju__pjcu = dict(ambiguous='raise', nonexistent='raise')
    check_unsupported_args('Timestamp.tz_localize', cdwfp__vfss, pzju__pjcu,
        package_name='pandas', module_name='Timestamp')
    if is_overload_none(tz):
        return (lambda ptt, tz, ambiguous='raise', nonexistent='raise':
            convert_val_to_timestamp(ptt.value, is_convert=False))
    elif is_overload_constant_str(tz):
        return (lambda ptt, tz, ambiguous='raise', nonexistent='raise':
            convert_val_to_timestamp(ptt.value, tz=tz, is_convert=False))


@numba.njit
def str_2d(a):
    res = str(a)
    if len(res) == 1:
        return '0' + res
    return res


@overload(str, no_unliteral=True)
def ts_str_overload(a):
    if a == pd_timestamp_type:
        return lambda a: a.isoformat(' ')


@intrinsic
def extract_year_days(typingctx, dt64_t=None):
    assert dt64_t in (types.int64, types.NPDatetime('ns'))

    def codegen(context, builder, sig, args):
        nwv__gukgq = cgutils.alloca_once(builder, lir.IntType(64))
        builder.store(args[0], nwv__gukgq)
        year = cgutils.alloca_once(builder, lir.IntType(64))
        ipedi__axx = cgutils.alloca_once(builder, lir.IntType(64))
        qfi__qsdd = lir.FunctionType(lir.VoidType(), [lir.IntType(64).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(64).
            as_pointer()])
        fbk__wdyp = cgutils.get_or_insert_function(builder.module,
            qfi__qsdd, name='extract_year_days')
        builder.call(fbk__wdyp, [nwv__gukgq, year, ipedi__axx])
        return cgutils.pack_array(builder, [builder.load(nwv__gukgq),
            builder.load(year), builder.load(ipedi__axx)])
    return types.Tuple([types.int64, types.int64, types.int64])(dt64_t
        ), codegen


@intrinsic
def get_month_day(typingctx, year_t, days_t=None):
    assert year_t == types.int64
    assert days_t == types.int64

    def codegen(context, builder, sig, args):
        month = cgutils.alloca_once(builder, lir.IntType(64))
        day = cgutils.alloca_once(builder, lir.IntType(64))
        qfi__qsdd = lir.FunctionType(lir.VoidType(), [lir.IntType(64), lir.
            IntType(64), lir.IntType(64).as_pointer(), lir.IntType(64).
            as_pointer()])
        fbk__wdyp = cgutils.get_or_insert_function(builder.module,
            qfi__qsdd, name='get_month_day')
        builder.call(fbk__wdyp, [args[0], args[1], month, day])
        return cgutils.pack_array(builder, [builder.load(month), builder.
            load(day)])
    return types.Tuple([types.int64, types.int64])(types.int64, types.int64
        ), codegen


@register_jitable
def get_day_of_year(year, month, day):
    cgrwe__kvjfp = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 
        365, 0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366]
    bzuty__hfc = is_leap_year(year)
    xifsi__blt = cgrwe__kvjfp[bzuty__hfc * 13 + month - 1]
    flvsp__gomtd = xifsi__blt + day
    return flvsp__gomtd


@register_jitable
def get_day_of_week(y, m, d):
    wlkt__xuw = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4]
    y -= m < 3
    day = (y + y // 4 - y // 100 + y // 400 + wlkt__xuw[m - 1] + d) % 7
    return (day + 6) % 7


@register_jitable
def get_days_in_month(year, month):
    is_leap_year = year & 3 == 0 and (year % 100 != 0 or year % 400 == 0)
    dzi__jyeye = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31, 29, 
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return dzi__jyeye[12 * is_leap_year + month - 1]


@register_jitable
def is_leap_year(year):
    return year & 3 == 0 and (year % 100 != 0 or year % 400 == 0)


@numba.generated_jit(nopython=True)
def convert_val_to_timestamp(ts_input, tz=None, is_convert=True):
    wsl__dptv = miqk__vuswy = np.array([])
    bnzs__bxbbn = '0'
    if is_overload_constant_str(tz):
        jlu__lmt = get_overload_const_str(tz)
        uzoux__alaig = pytz.timezone(jlu__lmt)
        if isinstance(uzoux__alaig, pytz.tzinfo.DstTzInfo):
            wsl__dptv = np.array(uzoux__alaig._utc_transition_times, dtype=
                'M8[ns]').view('i8')
            miqk__vuswy = np.array(uzoux__alaig._transition_info)[:, 0]
            miqk__vuswy = (pd.Series(miqk__vuswy).dt.total_seconds() * 
                1000000000).astype(np.int64).values
            bnzs__bxbbn = (
                "deltas[np.searchsorted(trans, ts_input, side='right') - 1]")
        else:
            miqk__vuswy = np.int64(uzoux__alaig._utcoffset.total_seconds() *
                1000000000)
            bnzs__bxbbn = 'deltas'
    elif is_overload_constant_int(tz):
        dhdt__snr = get_overload_const_int(tz)
        bnzs__bxbbn = str(dhdt__snr)
    elif not is_overload_none(tz):
        raise_bodo_error(
            'convert_val_to_timestamp(): tz value must be a constant string or None'
            )
    is_convert = get_overload_const_bool(is_convert)
    if is_convert:
        nqyi__pkkt = 'tz_ts_input'
        qkp__gqnxc = 'ts_input'
    else:
        nqyi__pkkt = 'ts_input'
        qkp__gqnxc = 'tz_ts_input'
    aqr__lnjc = 'def impl(ts_input, tz=None, is_convert=True):\n'
    aqr__lnjc += f'  tz_ts_input = ts_input + {bnzs__bxbbn}\n'
    aqr__lnjc += (
        f'  dt, year, days = extract_year_days(integer_to_dt64({nqyi__pkkt}))\n'
        )
    aqr__lnjc += '  month, day = get_month_day(year, days)\n'
    aqr__lnjc += '  return init_timestamp(\n'
    aqr__lnjc += '    year=year,\n'
    aqr__lnjc += '    month=month,\n'
    aqr__lnjc += '    day=day,\n'
    aqr__lnjc += '    hour=dt // (60 * 60 * 1_000_000_000),\n'
    aqr__lnjc += '    minute=(dt // (60 * 1_000_000_000)) % 60,\n'
    aqr__lnjc += '    second=(dt // 1_000_000_000) % 60,\n'
    aqr__lnjc += '    microsecond=(dt // 1000) % 1_000_000,\n'
    aqr__lnjc += '    nanosecond=dt % 1000,\n'
    aqr__lnjc += f'    value={qkp__gqnxc},\n'
    aqr__lnjc += '    tz=tz,\n'
    aqr__lnjc += '  )\n'
    iax__vgxb = {}
    exec(aqr__lnjc, {'np': np, 'pd': pd, 'trans': wsl__dptv, 'deltas':
        miqk__vuswy, 'integer_to_dt64': integer_to_dt64,
        'extract_year_days': extract_year_days, 'get_month_day':
        get_month_day, 'init_timestamp': init_timestamp, 'zero_if_none':
        zero_if_none}, iax__vgxb)
    impl = iax__vgxb['impl']
    return impl


@numba.njit(no_cpython_wrapper=True)
def convert_datetime64_to_timestamp(dt64):
    nwv__gukgq, year, ipedi__axx = extract_year_days(dt64)
    month, day = get_month_day(year, ipedi__axx)
    return init_timestamp(year=year, month=month, day=day, hour=nwv__gukgq //
        (60 * 60 * 1000000000), minute=nwv__gukgq // (60 * 1000000000) % 60,
        second=nwv__gukgq // 1000000000 % 60, microsecond=nwv__gukgq // 
        1000 % 1000000, nanosecond=nwv__gukgq % 1000, value=dt64, tz=None)


@numba.njit(no_cpython_wrapper=True)
def convert_numpy_timedelta64_to_datetime_timedelta(dt64):
    zaez__fqapw = (bodo.hiframes.datetime_timedelta_ext.
        cast_numpy_timedelta_to_int(dt64))
    zit__vbim = zaez__fqapw // (86400 * 1000000000)
    bqt__ubvi = zaez__fqapw - zit__vbim * 86400 * 1000000000
    lyr__llqyv = bqt__ubvi // 1000000000
    nqv__ymrk = bqt__ubvi - lyr__llqyv * 1000000000
    mkm__gjw = nqv__ymrk // 1000
    return datetime.timedelta(zit__vbim, lyr__llqyv, mkm__gjw)


@numba.njit(no_cpython_wrapper=True)
def convert_numpy_timedelta64_to_pd_timedelta(dt64):
    zaez__fqapw = (bodo.hiframes.datetime_timedelta_ext.
        cast_numpy_timedelta_to_int(dt64))
    return pd.Timedelta(zaez__fqapw)


@intrinsic
def integer_to_timedelta64(typingctx, val=None):

    def codegen(context, builder, sig, args):
        return args[0]
    return types.NPTimedelta('ns')(val), codegen


@intrinsic
def integer_to_dt64(typingctx, val=None):

    def codegen(context, builder, sig, args):
        return args[0]
    return types.NPDatetime('ns')(val), codegen


@intrinsic
def dt64_to_integer(typingctx, val=None):

    def codegen(context, builder, sig, args):
        return args[0]
    return types.int64(val), codegen


@lower_cast(types.NPDatetime('ns'), types.int64)
def cast_dt64_to_integer(context, builder, fromty, toty, val):
    return val


@overload_method(types.NPDatetime, '__hash__', no_unliteral=True)
def dt64_hash(val):
    return lambda val: hash(dt64_to_integer(val))


@overload_method(types.NPTimedelta, '__hash__', no_unliteral=True)
def td64_hash(val):
    return lambda val: hash(dt64_to_integer(val))


@intrinsic
def timedelta64_to_integer(typingctx, val=None):

    def codegen(context, builder, sig, args):
        return args[0]
    return types.int64(val), codegen


@lower_cast(bodo.timedelta64ns, types.int64)
def cast_td64_to_integer(context, builder, fromty, toty, val):
    return val


@numba.njit
def parse_datetime_str(val):
    with numba.objmode(res='int64'):
        res = pd.Timestamp(val).value
    return integer_to_dt64(res)


@numba.njit
def datetime_timedelta_to_timedelta64(val):
    with numba.objmode(res='NPTimedelta("ns")'):
        res = pd.to_timedelta(val)
        res = res.to_timedelta64()
    return res


@numba.njit
def series_str_dt64_astype(data):
    with numba.objmode(res="NPDatetime('ns')[::1]"):
        res = pd.Series(data).astype('datetime64[ns]').values
    return res


@numba.njit
def series_str_td64_astype(data):
    with numba.objmode(res="NPTimedelta('ns')[::1]"):
        res = data.astype('timedelta64[ns]')
    return res


@numba.njit
def datetime_datetime_to_dt64(val):
    with numba.objmode(res='NPDatetime("ns")'):
        res = np.datetime64(val).astype('datetime64[ns]')
    return res


@register_jitable
def datetime_date_arr_to_dt64_arr(arr):
    with numba.objmode(res='NPDatetime("ns")[:]'):
        res = np.array(arr, dtype='datetime64[ns]')
    return res


types.pd_timestamp_type = pd_timestamp_type


@register_jitable
def to_datetime_scalar(a, errors='raise', dayfirst=False, yearfirst=False,
    utc=None, format=None, exact=True, unit=None, infer_datetime_format=
    False, origin='unix', cache=True):
    with numba.objmode(t='pd_timestamp_type'):
        t = pd.to_datetime(a, errors=errors, dayfirst=dayfirst, yearfirst=
            yearfirst, utc=utc, format=format, exact=exact, unit=unit,
            infer_datetime_format=infer_datetime_format, origin=origin,
            cache=cache)
    return t


@numba.njit
def pandas_string_array_to_datetime(arr, errors, dayfirst, yearfirst, utc,
    format, exact, unit, infer_datetime_format, origin, cache):
    with numba.objmode(result='datetime_index'):
        result = pd.to_datetime(arr, errors=errors, dayfirst=dayfirst,
            yearfirst=yearfirst, utc=utc, format=format, exact=exact, unit=
            unit, infer_datetime_format=infer_datetime_format, origin=
            origin, cache=cache)
    return result


@numba.njit
def pandas_dict_string_array_to_datetime(arr, errors, dayfirst, yearfirst,
    utc, format, exact, unit, infer_datetime_format, origin, cache):
    cfes__alt = len(arr)
    unfm__ackb = np.empty(cfes__alt, 'datetime64[ns]')
    rdvle__ona = arr._indices
    kxbm__rzol = pandas_string_array_to_datetime(arr._data, errors,
        dayfirst, yearfirst, utc, format, exact, unit,
        infer_datetime_format, origin, cache).values
    for muhs__xmht in range(cfes__alt):
        if bodo.libs.array_kernels.isna(rdvle__ona, muhs__xmht):
            bodo.libs.array_kernels.setna(unfm__ackb, muhs__xmht)
            continue
        unfm__ackb[muhs__xmht] = kxbm__rzol[rdvle__ona[muhs__xmht]]
    return unfm__ackb


@overload(pd.to_datetime, inline='always', no_unliteral=True)
def overload_to_datetime(arg_a, errors='raise', dayfirst=False, yearfirst=
    False, utc=None, format=None, exact=True, unit=None,
    infer_datetime_format=False, origin='unix', cache=True):
    if arg_a == bodo.string_type or is_overload_constant_str(arg_a
        ) or is_overload_constant_int(arg_a) or isinstance(arg_a, types.Integer
        ):

        def pd_to_datetime_impl(arg_a, errors='raise', dayfirst=False,
            yearfirst=False, utc=None, format=None, exact=True, unit=None,
            infer_datetime_format=False, origin='unix', cache=True):
            return to_datetime_scalar(arg_a, errors=errors, dayfirst=
                dayfirst, yearfirst=yearfirst, utc=utc, format=format,
                exact=exact, unit=unit, infer_datetime_format=
                infer_datetime_format, origin=origin, cache=cache)
        return pd_to_datetime_impl
    if isinstance(arg_a, bodo.hiframes.pd_series_ext.SeriesType):

        def impl_series(arg_a, errors='raise', dayfirst=False, yearfirst=
            False, utc=None, format=None, exact=True, unit=None,
            infer_datetime_format=False, origin='unix', cache=True):
            arr = bodo.hiframes.pd_series_ext.get_series_data(arg_a)
            rfbcv__ouqyp = bodo.hiframes.pd_series_ext.get_series_index(arg_a)
            ngrr__gxgh = bodo.hiframes.pd_series_ext.get_series_name(arg_a)
            vdxu__xtss = bodo.utils.conversion.coerce_to_ndarray(pd.
                to_datetime(arr, errors=errors, dayfirst=dayfirst,
                yearfirst=yearfirst, utc=utc, format=format, exact=exact,
                unit=unit, infer_datetime_format=infer_datetime_format,
                origin=origin, cache=cache))
            return bodo.hiframes.pd_series_ext.init_series(vdxu__xtss,
                rfbcv__ouqyp, ngrr__gxgh)
        return impl_series
    if arg_a == bodo.hiframes.datetime_date_ext.datetime_date_array_type:
        mplwg__copjz = np.dtype('datetime64[ns]')
        iNaT = pd._libs.tslibs.iNaT

        def impl_date_arr(arg_a, errors='raise', dayfirst=False, yearfirst=
            False, utc=None, format=None, exact=True, unit=None,
            infer_datetime_format=False, origin='unix', cache=True):
            cfes__alt = len(arg_a)
            unfm__ackb = np.empty(cfes__alt, mplwg__copjz)
            for muhs__xmht in numba.parfors.parfor.internal_prange(cfes__alt):
                val = iNaT
                if not bodo.libs.array_kernels.isna(arg_a, muhs__xmht):
                    data = arg_a[muhs__xmht]
                    val = (bodo.hiframes.pd_timestamp_ext.
                        npy_datetimestruct_to_datetime(data.year, data.
                        month, data.day, 0, 0, 0, 0))
                unfm__ackb[muhs__xmht
                    ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(val)
            return bodo.hiframes.pd_index_ext.init_datetime_index(unfm__ackb,
                None)
        return impl_date_arr
    if arg_a == types.Array(types.NPDatetime('ns'), 1, 'C'):
        return (lambda arg_a, errors='raise', dayfirst=False, yearfirst=
            False, utc=None, format=None, exact=True, unit=None,
            infer_datetime_format=False, origin='unix', cache=True: bodo.
            hiframes.pd_index_ext.init_datetime_index(arg_a, None))
    if arg_a == string_array_type:

        def impl_string_array(arg_a, errors='raise', dayfirst=False,
            yearfirst=False, utc=None, format=None, exact=True, unit=None,
            infer_datetime_format=False, origin='unix', cache=True):
            return pandas_string_array_to_datetime(arg_a, errors, dayfirst,
                yearfirst, utc, format, exact, unit, infer_datetime_format,
                origin, cache)
        return impl_string_array
    if isinstance(arg_a, types.Array) and isinstance(arg_a.dtype, types.Integer
        ):
        mplwg__copjz = np.dtype('datetime64[ns]')

        def impl_date_arr(arg_a, errors='raise', dayfirst=False, yearfirst=
            False, utc=None, format=None, exact=True, unit=None,
            infer_datetime_format=False, origin='unix', cache=True):
            cfes__alt = len(arg_a)
            unfm__ackb = np.empty(cfes__alt, mplwg__copjz)
            for muhs__xmht in numba.parfors.parfor.internal_prange(cfes__alt):
                data = arg_a[muhs__xmht]
                val = to_datetime_scalar(data, errors=errors, dayfirst=
                    dayfirst, yearfirst=yearfirst, utc=utc, format=format,
                    exact=exact, unit=unit, infer_datetime_format=
                    infer_datetime_format, origin=origin, cache=cache)
                unfm__ackb[muhs__xmht
                    ] = bodo.hiframes.pd_timestamp_ext.datetime_datetime_to_dt64(
                    val)
            return bodo.hiframes.pd_index_ext.init_datetime_index(unfm__ackb,
                None)
        return impl_date_arr
    if isinstance(arg_a, CategoricalArrayType
        ) and arg_a.dtype.elem_type == bodo.string_type:
        mplwg__copjz = np.dtype('datetime64[ns]')

        def impl_cat_arr(arg_a, errors='raise', dayfirst=False, yearfirst=
            False, utc=None, format=None, exact=True, unit=None,
            infer_datetime_format=False, origin='unix', cache=True):
            cfes__alt = len(arg_a)
            unfm__ackb = np.empty(cfes__alt, mplwg__copjz)
            hmaft__nzkq = (bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(arg_a))
            kxbm__rzol = pandas_string_array_to_datetime(arg_a.dtype.
                categories.values, errors, dayfirst, yearfirst, utc, format,
                exact, unit, infer_datetime_format, origin, cache).values
            for muhs__xmht in numba.parfors.parfor.internal_prange(cfes__alt):
                c = hmaft__nzkq[muhs__xmht]
                if c == -1:
                    bodo.libs.array_kernels.setna(unfm__ackb, muhs__xmht)
                    continue
                unfm__ackb[muhs__xmht] = kxbm__rzol[c]
            return bodo.hiframes.pd_index_ext.init_datetime_index(unfm__ackb,
                None)
        return impl_cat_arr
    if arg_a == bodo.dict_str_arr_type:

        def impl_dict_str_arr(arg_a, errors='raise', dayfirst=False,
            yearfirst=False, utc=None, format=None, exact=True, unit=None,
            infer_datetime_format=False, origin='unix', cache=True):
            unfm__ackb = pandas_dict_string_array_to_datetime(arg_a, errors,
                dayfirst, yearfirst, utc, format, exact, unit,
                infer_datetime_format, origin, cache)
            return bodo.hiframes.pd_index_ext.init_datetime_index(unfm__ackb,
                None)
        return impl_dict_str_arr
    if arg_a == pd_timestamp_type:

        def impl_timestamp(arg_a, errors='raise', dayfirst=False, yearfirst
            =False, utc=None, format=None, exact=True, unit=None,
            infer_datetime_format=False, origin='unix', cache=True):
            return arg_a
        return impl_timestamp
    raise_bodo_error(f'pd.to_datetime(): cannot convert date type {arg_a}')


@overload(pd.to_timedelta, inline='always', no_unliteral=True)
def overload_to_timedelta(arg_a, unit='ns', errors='raise'):
    if not is_overload_constant_str(unit):
        raise BodoError(
            'pandas.to_timedelta(): unit should be a constant string')
    unit = pd._libs.tslibs.timedeltas.parse_timedelta_unit(
        get_overload_const_str(unit))
    if isinstance(arg_a, bodo.hiframes.pd_series_ext.SeriesType):

        def impl_series(arg_a, unit='ns', errors='raise'):
            arr = bodo.hiframes.pd_series_ext.get_series_data(arg_a)
            rfbcv__ouqyp = bodo.hiframes.pd_series_ext.get_series_index(arg_a)
            ngrr__gxgh = bodo.hiframes.pd_series_ext.get_series_name(arg_a)
            vdxu__xtss = bodo.utils.conversion.coerce_to_ndarray(pd.
                to_timedelta(arr, unit, errors))
            return bodo.hiframes.pd_series_ext.init_series(vdxu__xtss,
                rfbcv__ouqyp, ngrr__gxgh)
        return impl_series
    if is_overload_constant_str(arg_a) or arg_a in (pd_timedelta_type,
        datetime_timedelta_type, bodo.string_type):

        def impl_string(arg_a, unit='ns', errors='raise'):
            return pd.Timedelta(arg_a)
        return impl_string
    if isinstance(arg_a, types.Float):
        m, dqr__yml = pd._libs.tslibs.conversion.precision_from_unit(unit)

        def impl_float_scalar(arg_a, unit='ns', errors='raise'):
            val = float_to_timedelta_val(arg_a, dqr__yml, m)
            return pd.Timedelta(val)
        return impl_float_scalar
    if isinstance(arg_a, types.Integer):
        m, cmfm__isap = pd._libs.tslibs.conversion.precision_from_unit(unit)

        def impl_integer_scalar(arg_a, unit='ns', errors='raise'):
            return pd.Timedelta(arg_a * m)
        return impl_integer_scalar
    if is_iterable_type(arg_a) and not isinstance(arg_a, types.BaseTuple):
        m, dqr__yml = pd._libs.tslibs.conversion.precision_from_unit(unit)
        akad__bfs = np.dtype('timedelta64[ns]')
        if isinstance(arg_a.dtype, types.Float):

            def impl_float(arg_a, unit='ns', errors='raise'):
                cfes__alt = len(arg_a)
                unfm__ackb = np.empty(cfes__alt, akad__bfs)
                for muhs__xmht in numba.parfors.parfor.internal_prange(
                    cfes__alt):
                    val = iNaT
                    if not bodo.libs.array_kernels.isna(arg_a, muhs__xmht):
                        val = float_to_timedelta_val(arg_a[muhs__xmht],
                            dqr__yml, m)
                    unfm__ackb[muhs__xmht
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        val)
                return bodo.hiframes.pd_index_ext.init_timedelta_index(
                    unfm__ackb, None)
            return impl_float
        if isinstance(arg_a.dtype, types.Integer):

            def impl_int(arg_a, unit='ns', errors='raise'):
                cfes__alt = len(arg_a)
                unfm__ackb = np.empty(cfes__alt, akad__bfs)
                for muhs__xmht in numba.parfors.parfor.internal_prange(
                    cfes__alt):
                    val = iNaT
                    if not bodo.libs.array_kernels.isna(arg_a, muhs__xmht):
                        val = arg_a[muhs__xmht] * m
                    unfm__ackb[muhs__xmht
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        val)
                return bodo.hiframes.pd_index_ext.init_timedelta_index(
                    unfm__ackb, None)
            return impl_int
        if arg_a.dtype == bodo.timedelta64ns:

            def impl_td64(arg_a, unit='ns', errors='raise'):
                arr = bodo.utils.conversion.coerce_to_ndarray(arg_a)
                return bodo.hiframes.pd_index_ext.init_timedelta_index(arr,
                    None)
            return impl_td64
        if arg_a.dtype == bodo.string_type or isinstance(arg_a.dtype, types
            .UnicodeCharSeq):

            def impl_str(arg_a, unit='ns', errors='raise'):
                return pandas_string_array_to_timedelta(arg_a, unit, errors)
            return impl_str
        if arg_a.dtype == datetime_timedelta_type:

            def impl_datetime_timedelta(arg_a, unit='ns', errors='raise'):
                cfes__alt = len(arg_a)
                unfm__ackb = np.empty(cfes__alt, akad__bfs)
                for muhs__xmht in numba.parfors.parfor.internal_prange(
                    cfes__alt):
                    val = iNaT
                    if not bodo.libs.array_kernels.isna(arg_a, muhs__xmht):
                        lks__bdz = arg_a[muhs__xmht]
                        val = (lks__bdz.microseconds + 1000 * 1000 * (
                            lks__bdz.seconds + 24 * 60 * 60 * lks__bdz.days)
                            ) * 1000
                    unfm__ackb[muhs__xmht
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        val)
                return bodo.hiframes.pd_index_ext.init_timedelta_index(
                    unfm__ackb, None)
            return impl_datetime_timedelta
    raise_bodo_error(
        f'pd.to_timedelta(): cannot convert date type {arg_a.dtype}')


@register_jitable
def float_to_timedelta_val(data, precision, multiplier):
    cln__clh = np.int64(data)
    tig__krd = data - cln__clh
    if precision:
        tig__krd = np.round(tig__krd, precision)
    return cln__clh * multiplier + np.int64(tig__krd * multiplier)


@numba.njit
def pandas_string_array_to_timedelta(arg_a, unit='ns', errors='raise'):
    with numba.objmode(result='timedelta_index'):
        result = pd.to_timedelta(arg_a, errors=errors)
    return result


def create_timestamp_cmp_op_overload(op):

    def overload_date_timestamp_cmp(lhs, rhs):
        if (lhs == pd_timestamp_type and rhs == bodo.hiframes.
            datetime_date_ext.datetime_date_type):
            return lambda lhs, rhs: op(lhs.value, bodo.hiframes.
                pd_timestamp_ext.npy_datetimestruct_to_datetime(rhs.year,
                rhs.month, rhs.day, 0, 0, 0, 0))
        if (lhs == bodo.hiframes.datetime_date_ext.datetime_date_type and 
            rhs == pd_timestamp_type):
            return lambda lhs, rhs: op(bodo.hiframes.pd_timestamp_ext.
                npy_datetimestruct_to_datetime(lhs.year, lhs.month, lhs.day,
                0, 0, 0, 0), rhs.value)
        if lhs == pd_timestamp_type and rhs == pd_timestamp_type:
            return lambda lhs, rhs: op(lhs.value, rhs.value)
        if lhs == pd_timestamp_type and rhs == bodo.datetime64ns:
            return lambda lhs, rhs: op(bodo.hiframes.pd_timestamp_ext.
                integer_to_dt64(lhs.value), rhs)
        if lhs == bodo.datetime64ns and rhs == pd_timestamp_type:
            return lambda lhs, rhs: op(lhs, bodo.hiframes.pd_timestamp_ext.
                integer_to_dt64(rhs.value))
    return overload_date_timestamp_cmp


@overload_method(PandasTimestampType, 'toordinal', no_unliteral=True)
def toordinal(date):

    def impl(date):
        return _ymd2ord(date.year, date.month, date.day)
    return impl


def overload_freq_methods(method):

    def freq_overload(td, freq, ambiguous='raise', nonexistent='raise'):
        cdwfp__vfss = dict(ambiguous=ambiguous, nonexistent=nonexistent)
        ogdlx__ptn = dict(ambiguous='raise', nonexistent='raise')
        check_unsupported_args(f'Timestamp.{method}', cdwfp__vfss,
            ogdlx__ptn, package_name='pandas', module_name='Timestamp')
        iszr__qvys = ["freq == 'D'", "freq == 'H'",
            "freq == 'min' or freq == 'T'", "freq == 'S'",
            "freq == 'ms' or freq == 'L'", "freq == 'U' or freq == 'us'",
            "freq == 'N'"]
        ueh__zcvt = [24 * 60 * 60 * 1000000 * 1000, 60 * 60 * 1000000 * 
            1000, 60 * 1000000 * 1000, 1000000 * 1000, 1000 * 1000, 1000, 1]
        aqr__lnjc = (
            "def impl(td, freq, ambiguous='raise', nonexistent='raise'):\n")
        for muhs__xmht, xcw__wxiqf in enumerate(iszr__qvys):
            vravd__znr = 'if' if muhs__xmht == 0 else 'elif'
            aqr__lnjc += '    {} {}:\n'.format(vravd__znr, xcw__wxiqf)
            aqr__lnjc += '        unit_value = {}\n'.format(ueh__zcvt[
                muhs__xmht])
        aqr__lnjc += '    else:\n'
        aqr__lnjc += (
            "        raise ValueError('Incorrect Frequency specification')\n")
        if td == pd_timedelta_type:
            aqr__lnjc += (
                """    return pd.Timedelta(unit_value * np.int64(np.{}(td.value / unit_value)))
"""
                .format(method))
        elif td == pd_timestamp_type:
            if method == 'ceil':
                aqr__lnjc += (
                    '    value = td.value + np.remainder(-td.value, unit_value)\n'
                    )
            if method == 'floor':
                aqr__lnjc += (
                    '    value = td.value - np.remainder(td.value, unit_value)\n'
                    )
            if method == 'round':
                aqr__lnjc += '    if unit_value == 1:\n'
                aqr__lnjc += '        value = td.value\n'
                aqr__lnjc += '    else:\n'
                aqr__lnjc += (
                    '        quotient, remainder = np.divmod(td.value, unit_value)\n'
                    )
                aqr__lnjc += """        mask = np.logical_or(remainder > (unit_value // 2), np.logical_and(remainder == (unit_value // 2), quotient % 2))
"""
                aqr__lnjc += '        if mask:\n'
                aqr__lnjc += '            quotient = quotient + 1\n'
                aqr__lnjc += '        value = quotient * unit_value\n'
            aqr__lnjc += '    return pd.Timestamp(value)\n'
        iax__vgxb = {}
        exec(aqr__lnjc, {'np': np, 'pd': pd}, iax__vgxb)
        impl = iax__vgxb['impl']
        return impl
    return freq_overload


def _install_freq_methods():
    eth__wyvq = ['ceil', 'floor', 'round']
    for method in eth__wyvq:
        dkdcz__lxkje = overload_freq_methods(method)
        overload_method(PDTimeDeltaType, method, no_unliteral=True)(
            dkdcz__lxkje)
        overload_method(PandasTimestampType, method, no_unliteral=True)(
            dkdcz__lxkje)


_install_freq_methods()


@register_jitable
def compute_pd_timestamp(totmicrosec, nanosecond):
    microsecond = totmicrosec % 1000000
    rqvs__tnlf = totmicrosec // 1000000
    second = rqvs__tnlf % 60
    fbw__bdb = rqvs__tnlf // 60
    minute = fbw__bdb % 60
    gvijq__ntmcf = fbw__bdb // 60
    hour = gvijq__ntmcf % 24
    gytto__vwsp = gvijq__ntmcf // 24
    year, month, day = _ord2ymd(gytto__vwsp)
    value = npy_datetimestruct_to_datetime(year, month, day, hour, minute,
        second, microsecond)
    value += zero_if_none(nanosecond)
    return init_timestamp(year, month, day, hour, minute, second,
        microsecond, nanosecond, value, None)


def overload_sub_operator_timestamp(lhs, rhs):
    if lhs == pd_timestamp_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            nbc__pkh = lhs.toordinal()
            eavx__eqv = lhs.second + lhs.minute * 60 + lhs.hour * 3600
            vyoys__eootb = lhs.microsecond
            nanosecond = lhs.nanosecond
            hmzzr__zoalh = rhs.days
            sfip__ypljm = rhs.seconds
            mvp__jbni = rhs.microseconds
            rkt__sdugf = nbc__pkh - hmzzr__zoalh
            gqzp__qxs = eavx__eqv - sfip__ypljm
            uctg__pqg = vyoys__eootb - mvp__jbni
            totmicrosec = 1000000 * (rkt__sdugf * 86400 + gqzp__qxs
                ) + uctg__pqg
            return compute_pd_timestamp(totmicrosec, nanosecond)
        return impl
    if lhs == pd_timestamp_type and rhs == pd_timestamp_type:

        def impl_timestamp(lhs, rhs):
            return convert_numpy_timedelta64_to_pd_timedelta(lhs.value -
                rhs.value)
        return impl_timestamp
    if lhs == pd_timestamp_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            return lhs + -rhs
        return impl


def overload_add_operator_timestamp(lhs, rhs):
    if lhs == pd_timestamp_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            nbc__pkh = lhs.toordinal()
            eavx__eqv = lhs.second + lhs.minute * 60 + lhs.hour * 3600
            vyoys__eootb = lhs.microsecond
            nanosecond = lhs.nanosecond
            hmzzr__zoalh = rhs.days
            sfip__ypljm = rhs.seconds
            mvp__jbni = rhs.microseconds
            rkt__sdugf = nbc__pkh + hmzzr__zoalh
            gqzp__qxs = eavx__eqv + sfip__ypljm
            uctg__pqg = vyoys__eootb + mvp__jbni
            totmicrosec = 1000000 * (rkt__sdugf * 86400 + gqzp__qxs
                ) + uctg__pqg
            return compute_pd_timestamp(totmicrosec, nanosecond)
        return impl
    if lhs == pd_timestamp_type and rhs == pd_timedelta_type:

        def impl(lhs, rhs):
            nbc__pkh = lhs.toordinal()
            eavx__eqv = lhs.second + lhs.minute * 60 + lhs.hour * 3600
            vyoys__eootb = lhs.microsecond
            ais__yrmb = lhs.nanosecond
            mvp__jbni = rhs.value // 1000
            gwln__ykbjx = rhs.nanoseconds
            uctg__pqg = vyoys__eootb + mvp__jbni
            totmicrosec = 1000000 * (nbc__pkh * 86400 + eavx__eqv) + uctg__pqg
            vhvph__toua = ais__yrmb + gwln__ykbjx
            return compute_pd_timestamp(totmicrosec, vhvph__toua)
        return impl
    if (lhs == pd_timedelta_type and rhs == pd_timestamp_type or lhs ==
        datetime_timedelta_type and rhs == pd_timestamp_type):

        def impl(lhs, rhs):
            return rhs + lhs
        return impl


@overload(min, no_unliteral=True)
def timestamp_min(lhs, rhs):
    if lhs == pd_timestamp_type and rhs == pd_timestamp_type:

        def impl(lhs, rhs):
            return lhs if lhs < rhs else rhs
        return impl


@overload(max, no_unliteral=True)
def timestamp_max(lhs, rhs):
    if lhs == pd_timestamp_type and rhs == pd_timestamp_type:

        def impl(lhs, rhs):
            return lhs if lhs > rhs else rhs
        return impl


@overload_method(DatetimeDateType, 'strftime')
@overload_method(PandasTimestampType, 'strftime')
def strftime(ts, format):
    if isinstance(ts, DatetimeDateType):
        eova__gqjmj = 'datetime.date'
    else:
        eova__gqjmj = 'pandas.Timestamp'
    if types.unliteral(format) != types.unicode_type:
        raise BodoError(
            f"{eova__gqjmj}.strftime(): 'strftime' argument must be a string")

    def impl(ts, format):
        with numba.objmode(res='unicode_type'):
            res = ts.strftime(format)
        return res
    return impl


@overload_method(PandasTimestampType, 'to_datetime64')
def to_datetime64(ts):

    def impl(ts):
        return integer_to_dt64(ts.value)
    return impl


@register_jitable
def now_impl():
    with numba.objmode(d='pd_timestamp_type'):
        d = pd.Timestamp.now()
    return d


class CompDT64(ConcreteTemplate):
    cases = [signature(types.boolean, types.NPDatetime('ns'), types.
        NPDatetime('ns'))]


@infer_global(operator.lt)
class CmpOpLt(CompDT64):
    key = operator.lt


@infer_global(operator.le)
class CmpOpLe(CompDT64):
    key = operator.le


@infer_global(operator.gt)
class CmpOpGt(CompDT64):
    key = operator.gt


@infer_global(operator.ge)
class CmpOpGe(CompDT64):
    key = operator.ge


@infer_global(operator.eq)
class CmpOpEq(CompDT64):
    key = operator.eq


@infer_global(operator.ne)
class CmpOpNe(CompDT64):
    key = operator.ne


@typeof_impl.register(calendar._localized_month)
def typeof_python_calendar(val, c):
    return types.Tuple([types.StringLiteral(vxxa__fvj) for vxxa__fvj in val])


@overload(str)
def overload_datetime64_str(val):
    if val == bodo.datetime64ns:

        def impl(val):
            return (bodo.hiframes.pd_timestamp_ext.
                convert_datetime64_to_timestamp(val).isoformat('T'))
        return impl


timestamp_unsupported_attrs = ['asm8', 'components', 'freqstr', 'tz',
    'fold', 'tzinfo', 'freq']
timestamp_unsupported_methods = ['astimezone', 'ctime', 'dst', 'isoweekday',
    'replace', 'strptime', 'time', 'timestamp', 'timetuple', 'timetz',
    'to_julian_date', 'to_numpy', 'to_period', 'to_pydatetime', 'tzname',
    'utcoffset', 'utctimetuple']


def _install_pd_timestamp_unsupported():
    from bodo.utils.typing import create_unsupported_overload
    for sdxs__oynm in timestamp_unsupported_attrs:
        xcmi__hnht = 'pandas.Timestamp.' + sdxs__oynm
        overload_attribute(PandasTimestampType, sdxs__oynm)(
            create_unsupported_overload(xcmi__hnht))
    for qhvha__qpnat in timestamp_unsupported_methods:
        xcmi__hnht = 'pandas.Timestamp.' + qhvha__qpnat
        overload_method(PandasTimestampType, qhvha__qpnat)(
            create_unsupported_overload(xcmi__hnht + '()'))


_install_pd_timestamp_unsupported()


@lower_builtin(numba.core.types.functions.NumberClass, pd_timestamp_type,
    types.StringLiteral)
def datetime64_constructor(context, builder, sig, args):

    def datetime64_constructor_impl(a, b):
        return integer_to_dt64(a.value)
    return context.compile_internal(builder, datetime64_constructor_impl,
        sig, args)
