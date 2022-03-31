"""
Support for Series.dt attributes and methods
"""
import datetime
import operator
import numba
import numpy as np
from numba.core import cgutils, types
from numba.extending import intrinsic, make_attribute_wrapper, models, overload_attribute, overload_method, register_model
import bodo
from bodo.hiframes.pd_series_ext import SeriesType, get_series_data, get_series_index, get_series_name, init_series
from bodo.libs.pd_datetime_arr_ext import DatetimeArrayType, PandasDatetimeTZDtype, init_pandas_datetime_array
from bodo.utils.typing import BodoError, check_unsupported_args, create_unsupported_overload, get_overload_const_str, is_overload_constant_str, raise_bodo_error
dt64_dtype = np.dtype('datetime64[ns]')
timedelta64_dtype = np.dtype('timedelta64[ns]')


class SeriesDatetimePropertiesType(types.Type):

    def __init__(self, stype):
        self.stype = stype
        skj__xyh = 'SeriesDatetimePropertiesType({})'.format(stype)
        super(SeriesDatetimePropertiesType, self).__init__(skj__xyh)


@register_model(SeriesDatetimePropertiesType)
class SeriesDtModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        wrap__iqax = [('obj', fe_type.stype)]
        super(SeriesDtModel, self).__init__(dmm, fe_type, wrap__iqax)


make_attribute_wrapper(SeriesDatetimePropertiesType, 'obj', '_obj')


@intrinsic
def init_series_dt_properties(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        bnp__agb, = args
        fei__kbb = signature.return_type
        xia__xoxwq = cgutils.create_struct_proxy(fei__kbb)(context, builder)
        xia__xoxwq.obj = bnp__agb
        context.nrt.incref(builder, signature.args[0], bnp__agb)
        return xia__xoxwq._getvalue()
    return SeriesDatetimePropertiesType(obj)(obj), codegen


@overload_attribute(SeriesType, 'dt')
def overload_series_dt(s):
    if not (bodo.hiframes.pd_series_ext.is_dt64_series_typ(s) or bodo.
        hiframes.pd_series_ext.is_timedelta64_series_typ(s)):
        raise_bodo_error('Can only use .dt accessor with datetimelike values.')
    return lambda s: bodo.hiframes.series_dt_impl.init_series_dt_properties(s)


def create_date_field_overload(field):

    def overload_field(S_dt):
        if S_dt.stype.dtype != types.NPDatetime('ns') and not isinstance(S_dt
            .stype.dtype, PandasDatetimeTZDtype):
            return
        tnqt__ozj = 'def impl(S_dt):\n'
        tnqt__ozj += '    S = S_dt._obj\n'
        tnqt__ozj += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        tnqt__ozj += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        tnqt__ozj += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        tnqt__ozj += '    numba.parfors.parfor.init_prange()\n'
        tnqt__ozj += '    n = len(arr)\n'
        if field in ('is_leap_year', 'is_month_start', 'is_month_end',
            'is_quarter_start', 'is_quarter_end', 'is_year_start',
            'is_year_end'):
            tnqt__ozj += '    out_arr = np.empty(n, np.bool_)\n'
        else:
            tnqt__ozj += (
                '    out_arr = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n'
                )
        tnqt__ozj += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        tnqt__ozj += '        if bodo.libs.array_kernels.isna(arr, i):\n'
        tnqt__ozj += '            bodo.libs.array_kernels.setna(out_arr, i)\n'
        tnqt__ozj += '            continue\n'
        tnqt__ozj += (
            '        dt64 = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(arr[i])\n'
            )
        if field in ('year', 'month', 'day'):
            tnqt__ozj += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            if field in ('month', 'day'):
                tnqt__ozj += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            tnqt__ozj += '        out_arr[i] = {}\n'.format(field)
        elif field in ('dayofyear', 'day_of_year', 'dayofweek',
            'day_of_week', 'weekday'):
            aht__jgbq = {'dayofyear': 'get_day_of_year', 'day_of_year':
                'get_day_of_year', 'dayofweek': 'get_day_of_week',
                'day_of_week': 'get_day_of_week', 'weekday': 'get_day_of_week'}
            tnqt__ozj += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            tnqt__ozj += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            tnqt__ozj += (
                """        out_arr[i] = bodo.hiframes.pd_timestamp_ext.{}(year, month, day)
"""
                .format(aht__jgbq[field]))
        elif field == 'is_leap_year':
            tnqt__ozj += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            tnqt__ozj += (
                '        out_arr[i] = bodo.hiframes.pd_timestamp_ext.is_leap_year(year)\n'
                )
        elif field in ('daysinmonth', 'days_in_month'):
            aht__jgbq = {'days_in_month': 'get_days_in_month',
                'daysinmonth': 'get_days_in_month'}
            tnqt__ozj += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            tnqt__ozj += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            tnqt__ozj += (
                '        out_arr[i] = bodo.hiframes.pd_timestamp_ext.{}(year, month)\n'
                .format(aht__jgbq[field]))
        else:
            tnqt__ozj += """        ts = bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp(dt64)
"""
            tnqt__ozj += '        out_arr[i] = ts.' + field + '\n'
        tnqt__ozj += (
            '    return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        ppcop__gga = {}
        exec(tnqt__ozj, {'bodo': bodo, 'numba': numba, 'np': np}, ppcop__gga)
        impl = ppcop__gga['impl']
        return impl
    return overload_field


def _install_date_fields():
    for field in bodo.hiframes.pd_timestamp_ext.date_fields:
        hqdfi__kdqkd = create_date_field_overload(field)
        overload_attribute(SeriesDatetimePropertiesType, field)(hqdfi__kdqkd)


_install_date_fields()


def create_date_method_overload(method):
    atimd__kfpqj = method in ['day_name', 'month_name']
    if atimd__kfpqj:
        tnqt__ozj = 'def overload_method(S_dt, locale=None):\n'
        tnqt__ozj += '    unsupported_args = dict(locale=locale)\n'
        tnqt__ozj += '    arg_defaults = dict(locale=None)\n'
        tnqt__ozj += '    bodo.utils.typing.check_unsupported_args(\n'
        tnqt__ozj += f"        'Series.dt.{method}',\n"
        tnqt__ozj += '        unsupported_args,\n'
        tnqt__ozj += '        arg_defaults,\n'
        tnqt__ozj += "        package_name='pandas',\n"
        tnqt__ozj += "        module_name='Series',\n"
        tnqt__ozj += '    )\n'
    else:
        tnqt__ozj = 'def overload_method(S_dt):\n'
    tnqt__ozj += '    if not S_dt.stype.dtype == bodo.datetime64ns:\n'
    tnqt__ozj += '        return\n'
    if atimd__kfpqj:
        tnqt__ozj += '    def impl(S_dt, locale=None):\n'
    else:
        tnqt__ozj += '    def impl(S_dt):\n'
    tnqt__ozj += '        S = S_dt._obj\n'
    tnqt__ozj += (
        '        arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    tnqt__ozj += (
        '        index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
    tnqt__ozj += (
        '        name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
    tnqt__ozj += '        numba.parfors.parfor.init_prange()\n'
    tnqt__ozj += '        n = len(arr)\n'
    if atimd__kfpqj:
        tnqt__ozj += """        out_arr = bodo.utils.utils.alloc_type(n, bodo.string_array_type, (-1,))
"""
    else:
        tnqt__ozj += (
            "        out_arr = np.empty(n, np.dtype('datetime64[ns]'))\n")
    tnqt__ozj += '        for i in numba.parfors.parfor.internal_prange(n):\n'
    tnqt__ozj += '            if bodo.libs.array_kernels.isna(arr, i):\n'
    tnqt__ozj += '                bodo.libs.array_kernels.setna(out_arr, i)\n'
    tnqt__ozj += '                continue\n'
    tnqt__ozj += """            ts = bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp(arr[i])
"""
    tnqt__ozj += f'            method_val = ts.{method}()\n'
    if atimd__kfpqj:
        tnqt__ozj += '            out_arr[i] = method_val\n'
    else:
        tnqt__ozj += """            out_arr[i] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(method_val.value)
"""
    tnqt__ozj += (
        '        return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    tnqt__ozj += '    return impl\n'
    ppcop__gga = {}
    exec(tnqt__ozj, {'bodo': bodo, 'numba': numba, 'np': np}, ppcop__gga)
    overload_method = ppcop__gga['overload_method']
    return overload_method


def _install_date_methods():
    for method in bodo.hiframes.pd_timestamp_ext.date_methods:
        hqdfi__kdqkd = create_date_method_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            hqdfi__kdqkd)


_install_date_methods()


@overload_attribute(SeriesDatetimePropertiesType, 'date')
def series_dt_date_overload(S_dt):
    if not S_dt.stype.dtype == types.NPDatetime('ns'):
        return

    def impl(S_dt):
        wpcqk__inat = S_dt._obj
        afn__fbj = bodo.hiframes.pd_series_ext.get_series_data(wpcqk__inat)
        fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(wpcqk__inat)
        skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(wpcqk__inat)
        numba.parfors.parfor.init_prange()
        niqs__zmkj = len(afn__fbj)
        rrrom__rsm = bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(
            niqs__zmkj)
        for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj):
            soq__xylo = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(afn__fbj
                [efu__kcj])
            zehqc__rktw = (bodo.hiframes.pd_timestamp_ext.
                convert_datetime64_to_timestamp(soq__xylo))
            rrrom__rsm[efu__kcj] = datetime.date(zehqc__rktw.year,
                zehqc__rktw.month, zehqc__rktw.day)
        return bodo.hiframes.pd_series_ext.init_series(rrrom__rsm,
            fkrtl__cbn, skj__xyh)
    return impl


def create_series_dt_df_output_overload(attr):

    def series_dt_df_output_overload(S_dt):
        if not (attr == 'components' and S_dt.stype.dtype == types.
            NPTimedelta('ns') or attr == 'isocalendar' and S_dt.stype.dtype ==
            types.NPDatetime('ns')):
            return
        if attr == 'components':
            wpj__oijyn = ['days', 'hours', 'minutes', 'seconds',
                'milliseconds', 'microseconds', 'nanoseconds']
            aqqn__urd = 'convert_numpy_timedelta64_to_pd_timedelta'
            zcbos__ndbh = 'np.empty(n, np.int64)'
            hari__kwx = attr
        elif attr == 'isocalendar':
            wpj__oijyn = ['year', 'week', 'day']
            aqqn__urd = 'convert_datetime64_to_timestamp'
            zcbos__ndbh = 'bodo.libs.int_arr_ext.alloc_int_array(n, np.uint32)'
            hari__kwx = attr + '()'
        tnqt__ozj = 'def impl(S_dt):\n'
        tnqt__ozj += '    S = S_dt._obj\n'
        tnqt__ozj += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        tnqt__ozj += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        tnqt__ozj += '    numba.parfors.parfor.init_prange()\n'
        tnqt__ozj += '    n = len(arr)\n'
        for field in wpj__oijyn:
            tnqt__ozj += '    {} = {}\n'.format(field, zcbos__ndbh)
        tnqt__ozj += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        tnqt__ozj += '        if bodo.libs.array_kernels.isna(arr, i):\n'
        for field in wpj__oijyn:
            tnqt__ozj += ('            bodo.libs.array_kernels.setna({}, i)\n'
                .format(field))
        tnqt__ozj += '            continue\n'
        zxhwh__kkikr = '(' + '[i], '.join(wpj__oijyn) + '[i])'
        tnqt__ozj += (
            '        {} = bodo.hiframes.pd_timestamp_ext.{}(arr[i]).{}\n'.
            format(zxhwh__kkikr, aqqn__urd, hari__kwx))
        zsvi__leyj = '(' + ', '.join(wpj__oijyn) + ')'
        upsl__owabx = "('" + "', '".join(wpj__oijyn) + "')"
        tnqt__ozj += (
            '    return bodo.hiframes.pd_dataframe_ext.init_dataframe({}, index, {})\n'
            .format(zsvi__leyj, upsl__owabx))
        ppcop__gga = {}
        exec(tnqt__ozj, {'bodo': bodo, 'numba': numba, 'np': np}, ppcop__gga)
        impl = ppcop__gga['impl']
        return impl
    return series_dt_df_output_overload


def _install_df_output_overload():
    kxn__nhog = [('components', overload_attribute), ('isocalendar',
        overload_method)]
    for attr, oxnhp__cbwp in kxn__nhog:
        hqdfi__kdqkd = create_series_dt_df_output_overload(attr)
        oxnhp__cbwp(SeriesDatetimePropertiesType, attr, inline='always')(
            hqdfi__kdqkd)


_install_df_output_overload()


def create_timedelta_field_overload(field):

    def overload_field(S_dt):
        if not S_dt.stype.dtype == types.NPTimedelta('ns'):
            return
        tnqt__ozj = 'def impl(S_dt):\n'
        tnqt__ozj += '    S = S_dt._obj\n'
        tnqt__ozj += '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
        tnqt__ozj += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        tnqt__ozj += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        tnqt__ozj += '    numba.parfors.parfor.init_prange()\n'
        tnqt__ozj += '    n = len(A)\n'
        tnqt__ozj += (
            '    B = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n')
        tnqt__ozj += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        tnqt__ozj += '        if bodo.libs.array_kernels.isna(A, i):\n'
        tnqt__ozj += '            bodo.libs.array_kernels.setna(B, i)\n'
        tnqt__ozj += '            continue\n'
        tnqt__ozj += (
            '        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])\n'
            )
        if field == 'nanoseconds':
            tnqt__ozj += '        B[i] = td64 % 1000\n'
        elif field == 'microseconds':
            tnqt__ozj += '        B[i] = td64 // 1000 % 1000000\n'
        elif field == 'seconds':
            tnqt__ozj += (
                '        B[i] = td64 // (1000 * 1000000) % (60 * 60 * 24)\n')
        elif field == 'days':
            tnqt__ozj += (
                '        B[i] = td64 // (1000 * 1000000 * 60 * 60 * 24)\n')
        else:
            assert False, 'invalid timedelta field'
        tnqt__ozj += (
            '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
            )
        ppcop__gga = {}
        exec(tnqt__ozj, {'numba': numba, 'np': np, 'bodo': bodo}, ppcop__gga)
        impl = ppcop__gga['impl']
        return impl
    return overload_field


def create_timedelta_method_overload(method):

    def overload_method(S_dt):
        if not S_dt.stype.dtype == types.NPTimedelta('ns'):
            return
        tnqt__ozj = 'def impl(S_dt):\n'
        tnqt__ozj += '    S = S_dt._obj\n'
        tnqt__ozj += '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
        tnqt__ozj += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        tnqt__ozj += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        tnqt__ozj += '    numba.parfors.parfor.init_prange()\n'
        tnqt__ozj += '    n = len(A)\n'
        if method == 'total_seconds':
            tnqt__ozj += '    B = np.empty(n, np.float64)\n'
        else:
            tnqt__ozj += """    B = bodo.hiframes.datetime_timedelta_ext.alloc_datetime_timedelta_array(n)
"""
        tnqt__ozj += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        tnqt__ozj += '        if bodo.libs.array_kernels.isna(A, i):\n'
        tnqt__ozj += '            bodo.libs.array_kernels.setna(B, i)\n'
        tnqt__ozj += '            continue\n'
        tnqt__ozj += (
            '        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])\n'
            )
        if method == 'total_seconds':
            tnqt__ozj += '        B[i] = td64 / (1000.0 * 1000000.0)\n'
        elif method == 'to_pytimedelta':
            tnqt__ozj += (
                '        B[i] = datetime.timedelta(microseconds=td64 // 1000)\n'
                )
        else:
            assert False, 'invalid timedelta method'
        if method == 'total_seconds':
            tnqt__ozj += (
                '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
                )
        else:
            tnqt__ozj += '    return B\n'
        ppcop__gga = {}
        exec(tnqt__ozj, {'numba': numba, 'np': np, 'bodo': bodo, 'datetime':
            datetime}, ppcop__gga)
        impl = ppcop__gga['impl']
        return impl
    return overload_method


def _install_S_dt_timedelta_fields():
    for field in bodo.hiframes.pd_timestamp_ext.timedelta_fields:
        hqdfi__kdqkd = create_timedelta_field_overload(field)
        overload_attribute(SeriesDatetimePropertiesType, field)(hqdfi__kdqkd)


_install_S_dt_timedelta_fields()


def _install_S_dt_timedelta_methods():
    for method in bodo.hiframes.pd_timestamp_ext.timedelta_methods:
        hqdfi__kdqkd = create_timedelta_method_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            hqdfi__kdqkd)


_install_S_dt_timedelta_methods()


@overload_method(SeriesDatetimePropertiesType, 'strftime', inline='always',
    no_unliteral=True)
def dt_strftime(S_dt, date_format):
    if S_dt.stype.dtype != types.NPDatetime('ns'):
        return
    if types.unliteral(date_format) != types.unicode_type:
        raise BodoError(
            "Series.str.strftime(): 'date_format' argument must be a string")

    def impl(S_dt, date_format):
        wpcqk__inat = S_dt._obj
        vhy__kty = bodo.hiframes.pd_series_ext.get_series_data(wpcqk__inat)
        fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(wpcqk__inat)
        skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(wpcqk__inat)
        numba.parfors.parfor.init_prange()
        niqs__zmkj = len(vhy__kty)
        oezsg__fknow = bodo.libs.str_arr_ext.pre_alloc_string_array(niqs__zmkj,
            -1)
        for ast__txdzf in numba.parfors.parfor.internal_prange(niqs__zmkj):
            if bodo.libs.array_kernels.isna(vhy__kty, ast__txdzf):
                bodo.libs.array_kernels.setna(oezsg__fknow, ast__txdzf)
                continue
            oezsg__fknow[ast__txdzf
                ] = bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp(
                vhy__kty[ast__txdzf]).strftime(date_format)
        return bodo.hiframes.pd_series_ext.init_series(oezsg__fknow,
            fkrtl__cbn, skj__xyh)
    return impl


@overload_method(SeriesDatetimePropertiesType, 'tz_convert', inline=
    'always', no_unliteral=True)
def overload_dt_tz_convert(S_dt, tz):

    def impl(S_dt, tz):
        wpcqk__inat = S_dt._obj
        iaen__kfmnp = get_series_data(wpcqk__inat).tz_convert(tz)
        fkrtl__cbn = get_series_index(wpcqk__inat)
        skj__xyh = get_series_name(wpcqk__inat)
        return init_series(iaen__kfmnp, fkrtl__cbn, skj__xyh)
    return impl


def create_timedelta_freq_overload(method):

    def freq_overload(S_dt, freq, ambiguous='raise', nonexistent='raise'):
        if S_dt.stype.dtype != types.NPTimedelta('ns'
            ) and S_dt.stype.dtype != types.NPDatetime('ns'):
            return
        oiu__iol = dict(ambiguous=ambiguous, nonexistent=nonexistent)
        ofirj__rbnc = dict(ambiguous='raise', nonexistent='raise')
        check_unsupported_args(f'Series.dt.{method}', oiu__iol, ofirj__rbnc,
            package_name='pandas', module_name='Series')
        tnqt__ozj = (
            "def impl(S_dt, freq, ambiguous='raise', nonexistent='raise'):\n")
        tnqt__ozj += '    S = S_dt._obj\n'
        tnqt__ozj += '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
        tnqt__ozj += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        tnqt__ozj += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        tnqt__ozj += '    numba.parfors.parfor.init_prange()\n'
        tnqt__ozj += '    n = len(A)\n'
        if S_dt.stype.dtype == types.NPTimedelta('ns'):
            tnqt__ozj += "    B = np.empty(n, np.dtype('timedelta64[ns]'))\n"
        else:
            tnqt__ozj += "    B = np.empty(n, np.dtype('datetime64[ns]'))\n"
        tnqt__ozj += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        tnqt__ozj += '        if bodo.libs.array_kernels.isna(A, i):\n'
        tnqt__ozj += '            bodo.libs.array_kernels.setna(B, i)\n'
        tnqt__ozj += '            continue\n'
        if S_dt.stype.dtype == types.NPTimedelta('ns'):
            thwkj__dhuq = (
                'bodo.hiframes.pd_timestamp_ext.convert_numpy_timedelta64_to_pd_timedelta'
                )
            owyzv__nace = (
                'bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64')
        else:
            thwkj__dhuq = (
                'bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp'
                )
            owyzv__nace = 'bodo.hiframes.pd_timestamp_ext.integer_to_dt64'
        tnqt__ozj += '        B[i] = {}({}(A[i]).{}(freq).value)\n'.format(
            owyzv__nace, thwkj__dhuq, method)
        tnqt__ozj += (
            '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
            )
        ppcop__gga = {}
        exec(tnqt__ozj, {'numba': numba, 'np': np, 'bodo': bodo}, ppcop__gga)
        impl = ppcop__gga['impl']
        return impl
    return freq_overload


def _install_S_dt_timedelta_freq_methods():
    rvb__mwqx = ['ceil', 'floor', 'round']
    for method in rvb__mwqx:
        hqdfi__kdqkd = create_timedelta_freq_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            hqdfi__kdqkd)


_install_S_dt_timedelta_freq_methods()


def create_bin_op_overload(op):

    def overload_series_dt_binop(lhs, rhs):
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs):
            qhfop__plq = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                pdno__tnq = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                nxx__bmwp = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    pdno__tnq)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                qdgi__xmoj = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                yga__hwgjq = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qdgi__xmoj)
                niqs__zmkj = len(nxx__bmwp)
                wpcqk__inat = np.empty(niqs__zmkj, timedelta64_dtype)
                fhjyg__bqu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qhfop__plq)
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    jgah__vgn = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        nxx__bmwp[efu__kcj])
                    zoaqf__gwwma = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(yga__hwgjq[efu__kcj]))
                    if jgah__vgn == fhjyg__bqu or zoaqf__gwwma == fhjyg__bqu:
                        frmn__pexxd = fhjyg__bqu
                    else:
                        frmn__pexxd = op(jgah__vgn, zoaqf__gwwma)
                    wpcqk__inat[efu__kcj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        frmn__pexxd)
                return bodo.hiframes.pd_series_ext.init_series(wpcqk__inat,
                    fkrtl__cbn, skj__xyh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs):
            qhfop__plq = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gtwts__baed = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                afn__fbj = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gtwts__baed)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                yga__hwgjq = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                niqs__zmkj = len(afn__fbj)
                wpcqk__inat = np.empty(niqs__zmkj, dt64_dtype)
                fhjyg__bqu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qhfop__plq)
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    zadsz__vqjq = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(afn__fbj[efu__kcj]))
                    kbe__ryz = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(yga__hwgjq[efu__kcj]))
                    if zadsz__vqjq == fhjyg__bqu or kbe__ryz == fhjyg__bqu:
                        frmn__pexxd = fhjyg__bqu
                    else:
                        frmn__pexxd = op(zadsz__vqjq, kbe__ryz)
                    wpcqk__inat[efu__kcj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        frmn__pexxd)
                return bodo.hiframes.pd_series_ext.init_series(wpcqk__inat,
                    fkrtl__cbn, skj__xyh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
            ) and bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs):
            qhfop__plq = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gtwts__baed = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                afn__fbj = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gtwts__baed)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                yga__hwgjq = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                niqs__zmkj = len(afn__fbj)
                wpcqk__inat = np.empty(niqs__zmkj, dt64_dtype)
                fhjyg__bqu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qhfop__plq)
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    zadsz__vqjq = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(afn__fbj[efu__kcj]))
                    kbe__ryz = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(yga__hwgjq[efu__kcj]))
                    if zadsz__vqjq == fhjyg__bqu or kbe__ryz == fhjyg__bqu:
                        frmn__pexxd = fhjyg__bqu
                    else:
                        frmn__pexxd = op(zadsz__vqjq, kbe__ryz)
                    wpcqk__inat[efu__kcj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        frmn__pexxd)
                return bodo.hiframes.pd_series_ext.init_series(wpcqk__inat,
                    fkrtl__cbn, skj__xyh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            qhfop__plq = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gtwts__baed = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                afn__fbj = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gtwts__baed)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                niqs__zmkj = len(afn__fbj)
                wpcqk__inat = np.empty(niqs__zmkj, timedelta64_dtype)
                fhjyg__bqu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qhfop__plq)
                lmip__erv = rhs.value
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    zadsz__vqjq = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(afn__fbj[efu__kcj]))
                    if zadsz__vqjq == fhjyg__bqu or lmip__erv == fhjyg__bqu:
                        frmn__pexxd = fhjyg__bqu
                    else:
                        frmn__pexxd = op(zadsz__vqjq, lmip__erv)
                    wpcqk__inat[efu__kcj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        frmn__pexxd)
                return bodo.hiframes.pd_series_ext.init_series(wpcqk__inat,
                    fkrtl__cbn, skj__xyh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
            ) and lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            qhfop__plq = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gtwts__baed = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                afn__fbj = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gtwts__baed)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                niqs__zmkj = len(afn__fbj)
                wpcqk__inat = np.empty(niqs__zmkj, timedelta64_dtype)
                fhjyg__bqu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qhfop__plq)
                lmip__erv = lhs.value
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    zadsz__vqjq = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(afn__fbj[efu__kcj]))
                    if lmip__erv == fhjyg__bqu or zadsz__vqjq == fhjyg__bqu:
                        frmn__pexxd = fhjyg__bqu
                    else:
                        frmn__pexxd = op(lmip__erv, zadsz__vqjq)
                    wpcqk__inat[efu__kcj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        frmn__pexxd)
                return bodo.hiframes.pd_series_ext.init_series(wpcqk__inat,
                    fkrtl__cbn, skj__xyh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and rhs ==
            bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type):
            qhfop__plq = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gtwts__baed = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                afn__fbj = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gtwts__baed)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                niqs__zmkj = len(afn__fbj)
                wpcqk__inat = np.empty(niqs__zmkj, dt64_dtype)
                fhjyg__bqu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qhfop__plq)
                qmbf__lmnd = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                kbe__ryz = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(qmbf__lmnd))
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    zadsz__vqjq = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(afn__fbj[efu__kcj]))
                    if zadsz__vqjq == fhjyg__bqu or kbe__ryz == fhjyg__bqu:
                        frmn__pexxd = fhjyg__bqu
                    else:
                        frmn__pexxd = op(zadsz__vqjq, kbe__ryz)
                    wpcqk__inat[efu__kcj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        frmn__pexxd)
                return bodo.hiframes.pd_series_ext.init_series(wpcqk__inat,
                    fkrtl__cbn, skj__xyh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and lhs ==
            bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type):
            qhfop__plq = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gtwts__baed = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                afn__fbj = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gtwts__baed)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                niqs__zmkj = len(afn__fbj)
                wpcqk__inat = np.empty(niqs__zmkj, dt64_dtype)
                fhjyg__bqu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qhfop__plq)
                qmbf__lmnd = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                kbe__ryz = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(qmbf__lmnd))
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    zadsz__vqjq = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(afn__fbj[efu__kcj]))
                    if zadsz__vqjq == fhjyg__bqu or kbe__ryz == fhjyg__bqu:
                        frmn__pexxd = fhjyg__bqu
                    else:
                        frmn__pexxd = op(zadsz__vqjq, kbe__ryz)
                    wpcqk__inat[efu__kcj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        frmn__pexxd)
                return bodo.hiframes.pd_series_ext.init_series(wpcqk__inat,
                    fkrtl__cbn, skj__xyh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and rhs ==
            bodo.hiframes.datetime_datetime_ext.datetime_datetime_type):
            qhfop__plq = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gtwts__baed = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                afn__fbj = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gtwts__baed)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                niqs__zmkj = len(afn__fbj)
                wpcqk__inat = np.empty(niqs__zmkj, timedelta64_dtype)
                fhjyg__bqu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qhfop__plq)
                soq__xylo = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(rhs))
                zadsz__vqjq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    soq__xylo)
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    mbzfs__vwi = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(afn__fbj[efu__kcj]))
                    if mbzfs__vwi == fhjyg__bqu or zadsz__vqjq == fhjyg__bqu:
                        frmn__pexxd = fhjyg__bqu
                    else:
                        frmn__pexxd = op(mbzfs__vwi, zadsz__vqjq)
                    wpcqk__inat[efu__kcj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        frmn__pexxd)
                return bodo.hiframes.pd_series_ext.init_series(wpcqk__inat,
                    fkrtl__cbn, skj__xyh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and lhs ==
            bodo.hiframes.datetime_datetime_ext.datetime_datetime_type):
            qhfop__plq = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gtwts__baed = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                afn__fbj = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gtwts__baed)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                niqs__zmkj = len(afn__fbj)
                wpcqk__inat = np.empty(niqs__zmkj, timedelta64_dtype)
                fhjyg__bqu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qhfop__plq)
                soq__xylo = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(lhs))
                zadsz__vqjq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    soq__xylo)
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    mbzfs__vwi = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(afn__fbj[efu__kcj]))
                    if zadsz__vqjq == fhjyg__bqu or mbzfs__vwi == fhjyg__bqu:
                        frmn__pexxd = fhjyg__bqu
                    else:
                        frmn__pexxd = op(zadsz__vqjq, mbzfs__vwi)
                    wpcqk__inat[efu__kcj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        frmn__pexxd)
                return bodo.hiframes.pd_series_ext.init_series(wpcqk__inat,
                    fkrtl__cbn, skj__xyh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs) and 
            rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            qhfop__plq = lhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                afn__fbj = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                niqs__zmkj = len(afn__fbj)
                wpcqk__inat = np.empty(niqs__zmkj, timedelta64_dtype)
                fhjyg__bqu = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(qhfop__plq))
                qmbf__lmnd = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                kbe__ryz = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(qmbf__lmnd))
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    pxcs__gonw = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(afn__fbj[efu__kcj]))
                    if kbe__ryz == fhjyg__bqu or pxcs__gonw == fhjyg__bqu:
                        frmn__pexxd = fhjyg__bqu
                    else:
                        frmn__pexxd = op(pxcs__gonw, kbe__ryz)
                    wpcqk__inat[efu__kcj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        frmn__pexxd)
                return bodo.hiframes.pd_series_ext.init_series(wpcqk__inat,
                    fkrtl__cbn, skj__xyh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs) and 
            lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            qhfop__plq = rhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                afn__fbj = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                niqs__zmkj = len(afn__fbj)
                wpcqk__inat = np.empty(niqs__zmkj, timedelta64_dtype)
                fhjyg__bqu = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(qhfop__plq))
                qmbf__lmnd = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                kbe__ryz = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(qmbf__lmnd))
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    pxcs__gonw = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(afn__fbj[efu__kcj]))
                    if kbe__ryz == fhjyg__bqu or pxcs__gonw == fhjyg__bqu:
                        frmn__pexxd = fhjyg__bqu
                    else:
                        frmn__pexxd = op(kbe__ryz, pxcs__gonw)
                    wpcqk__inat[efu__kcj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        frmn__pexxd)
                return bodo.hiframes.pd_series_ext.init_series(wpcqk__inat,
                    fkrtl__cbn, skj__xyh)
            return impl
        raise BodoError(f'{op} not supported for data types {lhs} and {rhs}.')
    return overload_series_dt_binop


def create_cmp_op_overload(op):

    def overload_series_dt64_cmp(lhs, rhs):
        if op == operator.ne:
            tau__yei = True
        else:
            tau__yei = False
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs) and 
            rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            qhfop__plq = lhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                afn__fbj = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                niqs__zmkj = len(afn__fbj)
                rrrom__rsm = bodo.libs.bool_arr_ext.alloc_bool_array(niqs__zmkj
                    )
                fhjyg__bqu = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(qhfop__plq))
                ryruw__jid = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                mnrfd__qnoqh = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(ryruw__jid))
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    dyy__vby = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(afn__fbj[efu__kcj]))
                    if dyy__vby == fhjyg__bqu or mnrfd__qnoqh == fhjyg__bqu:
                        frmn__pexxd = tau__yei
                    else:
                        frmn__pexxd = op(dyy__vby, mnrfd__qnoqh)
                    rrrom__rsm[efu__kcj] = frmn__pexxd
                return bodo.hiframes.pd_series_ext.init_series(rrrom__rsm,
                    fkrtl__cbn, skj__xyh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs) and 
            lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            qhfop__plq = rhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                afn__fbj = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                niqs__zmkj = len(afn__fbj)
                rrrom__rsm = bodo.libs.bool_arr_ext.alloc_bool_array(niqs__zmkj
                    )
                fhjyg__bqu = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(qhfop__plq))
                wuxsi__msa = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                dyy__vby = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(wuxsi__msa))
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    mnrfd__qnoqh = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(afn__fbj[efu__kcj]))
                    if dyy__vby == fhjyg__bqu or mnrfd__qnoqh == fhjyg__bqu:
                        frmn__pexxd = tau__yei
                    else:
                        frmn__pexxd = op(dyy__vby, mnrfd__qnoqh)
                    rrrom__rsm[efu__kcj] = frmn__pexxd
                return bodo.hiframes.pd_series_ext.init_series(rrrom__rsm,
                    fkrtl__cbn, skj__xyh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            qhfop__plq = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gtwts__baed = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                afn__fbj = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gtwts__baed)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                niqs__zmkj = len(afn__fbj)
                rrrom__rsm = bodo.libs.bool_arr_ext.alloc_bool_array(niqs__zmkj
                    )
                fhjyg__bqu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qhfop__plq)
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    dyy__vby = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        afn__fbj[efu__kcj])
                    if dyy__vby == fhjyg__bqu or rhs.value == fhjyg__bqu:
                        frmn__pexxd = tau__yei
                    else:
                        frmn__pexxd = op(dyy__vby, rhs.value)
                    rrrom__rsm[efu__kcj] = frmn__pexxd
                return bodo.hiframes.pd_series_ext.init_series(rrrom__rsm,
                    fkrtl__cbn, skj__xyh)
            return impl
        if (lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type and
            bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs)):
            qhfop__plq = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gtwts__baed = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                afn__fbj = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gtwts__baed)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                niqs__zmkj = len(afn__fbj)
                rrrom__rsm = bodo.libs.bool_arr_ext.alloc_bool_array(niqs__zmkj
                    )
                fhjyg__bqu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qhfop__plq)
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    mnrfd__qnoqh = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(afn__fbj[efu__kcj]))
                    if mnrfd__qnoqh == fhjyg__bqu or lhs.value == fhjyg__bqu:
                        frmn__pexxd = tau__yei
                    else:
                        frmn__pexxd = op(lhs.value, mnrfd__qnoqh)
                    rrrom__rsm[efu__kcj] = frmn__pexxd
                return bodo.hiframes.pd_series_ext.init_series(rrrom__rsm,
                    fkrtl__cbn, skj__xyh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and (rhs ==
            bodo.libs.str_ext.string_type or bodo.utils.typing.
            is_overload_constant_str(rhs)):
            qhfop__plq = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                gtwts__baed = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                afn__fbj = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gtwts__baed)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                numba.parfors.parfor.init_prange()
                niqs__zmkj = len(afn__fbj)
                rrrom__rsm = bodo.libs.bool_arr_ext.alloc_bool_array(niqs__zmkj
                    )
                fhjyg__bqu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qhfop__plq)
                qpk__frg = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(
                    rhs)
                esbq__axpgj = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qpk__frg)
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    dyy__vby = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        afn__fbj[efu__kcj])
                    if dyy__vby == fhjyg__bqu or esbq__axpgj == fhjyg__bqu:
                        frmn__pexxd = tau__yei
                    else:
                        frmn__pexxd = op(dyy__vby, esbq__axpgj)
                    rrrom__rsm[efu__kcj] = frmn__pexxd
                return bodo.hiframes.pd_series_ext.init_series(rrrom__rsm,
                    fkrtl__cbn, skj__xyh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and (lhs ==
            bodo.libs.str_ext.string_type or bodo.utils.typing.
            is_overload_constant_str(lhs)):
            qhfop__plq = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                gtwts__baed = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                afn__fbj = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gtwts__baed)
                fkrtl__cbn = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                skj__xyh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                numba.parfors.parfor.init_prange()
                niqs__zmkj = len(afn__fbj)
                rrrom__rsm = bodo.libs.bool_arr_ext.alloc_bool_array(niqs__zmkj
                    )
                fhjyg__bqu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qhfop__plq)
                qpk__frg = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(
                    lhs)
                esbq__axpgj = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    qpk__frg)
                for efu__kcj in numba.parfors.parfor.internal_prange(niqs__zmkj
                    ):
                    soq__xylo = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        afn__fbj[efu__kcj])
                    if soq__xylo == fhjyg__bqu or esbq__axpgj == fhjyg__bqu:
                        frmn__pexxd = tau__yei
                    else:
                        frmn__pexxd = op(esbq__axpgj, soq__xylo)
                    rrrom__rsm[efu__kcj] = frmn__pexxd
                return bodo.hiframes.pd_series_ext.init_series(rrrom__rsm,
                    fkrtl__cbn, skj__xyh)
            return impl
        raise BodoError(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_series_dt64_cmp


series_dt_unsupported_methods = {'to_period', 'to_pydatetime',
    'tz_localize', 'asfreq', 'to_timestamp'}
series_dt_unsupported_attrs = {'time', 'timetz', 'tz', 'freq', 'qyear',
    'start_time', 'end_time'}


def _install_series_dt_unsupported():
    for gzro__ozqa in series_dt_unsupported_attrs:
        uey__svwbf = 'Series.dt.' + gzro__ozqa
        overload_attribute(SeriesDatetimePropertiesType, gzro__ozqa)(
            create_unsupported_overload(uey__svwbf))
    for blicn__jkelr in series_dt_unsupported_methods:
        uey__svwbf = 'Series.dt.' + blicn__jkelr
        overload_method(SeriesDatetimePropertiesType, blicn__jkelr,
            no_unliteral=True)(create_unsupported_overload(uey__svwbf))


_install_series_dt_unsupported()
