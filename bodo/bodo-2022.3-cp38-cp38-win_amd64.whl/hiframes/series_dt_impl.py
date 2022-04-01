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
from bodo.libs.pd_datetime_arr_ext import PandasDatetimeTZDtype
from bodo.utils.typing import BodoError, check_unsupported_args, create_unsupported_overload, raise_bodo_error
dt64_dtype = np.dtype('datetime64[ns]')
timedelta64_dtype = np.dtype('timedelta64[ns]')


class SeriesDatetimePropertiesType(types.Type):

    def __init__(self, stype):
        self.stype = stype
        jlnkd__jio = 'SeriesDatetimePropertiesType({})'.format(stype)
        super(SeriesDatetimePropertiesType, self).__init__(jlnkd__jio)


@register_model(SeriesDatetimePropertiesType)
class SeriesDtModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        wgze__fscgg = [('obj', fe_type.stype)]
        super(SeriesDtModel, self).__init__(dmm, fe_type, wgze__fscgg)


make_attribute_wrapper(SeriesDatetimePropertiesType, 'obj', '_obj')


@intrinsic
def init_series_dt_properties(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        qexb__avj, = args
        sxl__kxrf = signature.return_type
        qjlvx__qciq = cgutils.create_struct_proxy(sxl__kxrf)(context, builder)
        qjlvx__qciq.obj = qexb__avj
        context.nrt.incref(builder, signature.args[0], qexb__avj)
        return qjlvx__qciq._getvalue()
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
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S_dt,
            f'Series.dt.{field}')
        nxh__pwm = 'def impl(S_dt):\n'
        nxh__pwm += '    S = S_dt._obj\n'
        nxh__pwm += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        nxh__pwm += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        nxh__pwm += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        nxh__pwm += '    numba.parfors.parfor.init_prange()\n'
        nxh__pwm += '    n = len(arr)\n'
        if field in ('is_leap_year', 'is_month_start', 'is_month_end',
            'is_quarter_start', 'is_quarter_end', 'is_year_start',
            'is_year_end'):
            nxh__pwm += '    out_arr = np.empty(n, np.bool_)\n'
        else:
            nxh__pwm += (
                '    out_arr = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n'
                )
        nxh__pwm += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        nxh__pwm += '        if bodo.libs.array_kernels.isna(arr, i):\n'
        nxh__pwm += '            bodo.libs.array_kernels.setna(out_arr, i)\n'
        nxh__pwm += '            continue\n'
        nxh__pwm += (
            '        dt64 = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(arr[i])\n'
            )
        if field in ('year', 'month', 'day'):
            nxh__pwm += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            if field in ('month', 'day'):
                nxh__pwm += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            nxh__pwm += '        out_arr[i] = {}\n'.format(field)
        elif field in ('dayofyear', 'day_of_year', 'dayofweek',
            'day_of_week', 'weekday'):
            hzs__lbmln = {'dayofyear': 'get_day_of_year', 'day_of_year':
                'get_day_of_year', 'dayofweek': 'get_day_of_week',
                'day_of_week': 'get_day_of_week', 'weekday': 'get_day_of_week'}
            nxh__pwm += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            nxh__pwm += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            nxh__pwm += (
                """        out_arr[i] = bodo.hiframes.pd_timestamp_ext.{}(year, month, day)
"""
                .format(hzs__lbmln[field]))
        elif field == 'is_leap_year':
            nxh__pwm += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            nxh__pwm += (
                '        out_arr[i] = bodo.hiframes.pd_timestamp_ext.is_leap_year(year)\n'
                )
        elif field in ('daysinmonth', 'days_in_month'):
            hzs__lbmln = {'days_in_month': 'get_days_in_month',
                'daysinmonth': 'get_days_in_month'}
            nxh__pwm += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            nxh__pwm += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            nxh__pwm += (
                '        out_arr[i] = bodo.hiframes.pd_timestamp_ext.{}(year, month)\n'
                .format(hzs__lbmln[field]))
        else:
            nxh__pwm += """        ts = bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp(dt64)
"""
            nxh__pwm += '        out_arr[i] = ts.' + field + '\n'
        nxh__pwm += (
            '    return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        lhcl__sqrrh = {}
        exec(nxh__pwm, {'bodo': bodo, 'numba': numba, 'np': np}, lhcl__sqrrh)
        impl = lhcl__sqrrh['impl']
        return impl
    return overload_field


def _install_date_fields():
    for field in bodo.hiframes.pd_timestamp_ext.date_fields:
        aitl__juj = create_date_field_overload(field)
        overload_attribute(SeriesDatetimePropertiesType, field)(aitl__juj)


_install_date_fields()


def create_date_method_overload(method):
    sboa__lzkyp = method in ['day_name', 'month_name']
    if sboa__lzkyp:
        nxh__pwm = 'def overload_method(S_dt, locale=None):\n'
        nxh__pwm += '    unsupported_args = dict(locale=locale)\n'
        nxh__pwm += '    arg_defaults = dict(locale=None)\n'
        nxh__pwm += '    bodo.utils.typing.check_unsupported_args(\n'
        nxh__pwm += f"        'Series.dt.{method}',\n"
        nxh__pwm += '        unsupported_args,\n'
        nxh__pwm += '        arg_defaults,\n'
        nxh__pwm += "        package_name='pandas',\n"
        nxh__pwm += "        module_name='Series',\n"
        nxh__pwm += '    )\n'
    else:
        nxh__pwm = 'def overload_method(S_dt):\n'
        nxh__pwm += f"""    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S_dt, 'Series.dt.{method}()')
"""
    nxh__pwm += """    if not (S_dt.stype.dtype == bodo.datetime64ns or isinstance(S_dt.stype.dtype, bodo.libs.pd_datetime_arr_ext.PandasDatetimeTZDtype)):
"""
    nxh__pwm += '        return\n'
    if sboa__lzkyp:
        nxh__pwm += '    def impl(S_dt, locale=None):\n'
    else:
        nxh__pwm += '    def impl(S_dt):\n'
    nxh__pwm += '        S = S_dt._obj\n'
    nxh__pwm += (
        '        arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    nxh__pwm += (
        '        index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
    nxh__pwm += (
        '        name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
    nxh__pwm += '        numba.parfors.parfor.init_prange()\n'
    nxh__pwm += '        n = len(arr)\n'
    if sboa__lzkyp:
        nxh__pwm += """        out_arr = bodo.utils.utils.alloc_type(n, bodo.string_array_type, (-1,))
"""
    else:
        nxh__pwm += (
            "        out_arr = np.empty(n, np.dtype('datetime64[ns]'))\n")
    nxh__pwm += '        for i in numba.parfors.parfor.internal_prange(n):\n'
    nxh__pwm += '            if bodo.libs.array_kernels.isna(arr, i):\n'
    nxh__pwm += '                bodo.libs.array_kernels.setna(out_arr, i)\n'
    nxh__pwm += '                continue\n'
    nxh__pwm += '            ts = bodo.utils.conversion.box_if_dt64(arr[i])\n'
    nxh__pwm += f'            method_val = ts.{method}()\n'
    if sboa__lzkyp:
        nxh__pwm += '            out_arr[i] = method_val\n'
    else:
        nxh__pwm += """            out_arr[i] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(method_val.value)
"""
    nxh__pwm += (
        '        return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    nxh__pwm += '    return impl\n'
    lhcl__sqrrh = {}
    exec(nxh__pwm, {'bodo': bodo, 'numba': numba, 'np': np}, lhcl__sqrrh)
    overload_method = lhcl__sqrrh['overload_method']
    return overload_method


def _install_date_methods():
    for method in bodo.hiframes.pd_timestamp_ext.date_methods:
        aitl__juj = create_date_method_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            aitl__juj)


_install_date_methods()


@overload_attribute(SeriesDatetimePropertiesType, 'date')
def series_dt_date_overload(S_dt):
    if not (S_dt.stype.dtype == types.NPDatetime('ns') or isinstance(S_dt.
        stype.dtype, bodo.libs.pd_datetime_arr_ext.PandasDatetimeTZDtype)):
        return

    def impl(S_dt):
        wdt__cqgnm = S_dt._obj
        egwk__gdx = bodo.hiframes.pd_series_ext.get_series_data(wdt__cqgnm)
        dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(wdt__cqgnm)
        jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(wdt__cqgnm)
        numba.parfors.parfor.init_prange()
        degl__eflw = len(egwk__gdx)
        vtqjp__xdj = bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(
            degl__eflw)
        for ebqng__opi in numba.parfors.parfor.internal_prange(degl__eflw):
            tdfn__rxrr = egwk__gdx[ebqng__opi]
            exzz__zlhme = bodo.utils.conversion.box_if_dt64(tdfn__rxrr)
            vtqjp__xdj[ebqng__opi] = datetime.date(exzz__zlhme.year,
                exzz__zlhme.month, exzz__zlhme.day)
        return bodo.hiframes.pd_series_ext.init_series(vtqjp__xdj, dbl__kmf,
            jlnkd__jio)
    return impl


def create_series_dt_df_output_overload(attr):

    def series_dt_df_output_overload(S_dt):
        if not (attr == 'components' and S_dt.stype.dtype == types.
            NPTimedelta('ns') or attr == 'isocalendar' and (S_dt.stype.
            dtype == types.NPDatetime('ns') or isinstance(S_dt.stype.dtype,
            PandasDatetimeTZDtype))):
            return
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S_dt,
            f'Series.dt.{attr}')
        if attr == 'components':
            spabv__cestq = ['days', 'hours', 'minutes', 'seconds',
                'milliseconds', 'microseconds', 'nanoseconds']
            bjl__zvmow = 'convert_numpy_timedelta64_to_pd_timedelta'
            mlww__yipo = 'np.empty(n, np.int64)'
            oxmtj__fpxqb = attr
        elif attr == 'isocalendar':
            spabv__cestq = ['year', 'week', 'day']
            bjl__zvmow = 'convert_datetime64_to_timestamp'
            mlww__yipo = 'bodo.libs.int_arr_ext.alloc_int_array(n, np.uint32)'
            oxmtj__fpxqb = attr + '()'
        nxh__pwm = 'def impl(S_dt):\n'
        nxh__pwm += '    S = S_dt._obj\n'
        nxh__pwm += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        nxh__pwm += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        nxh__pwm += '    numba.parfors.parfor.init_prange()\n'
        nxh__pwm += '    n = len(arr)\n'
        for field in spabv__cestq:
            nxh__pwm += '    {} = {}\n'.format(field, mlww__yipo)
        nxh__pwm += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        nxh__pwm += '        if bodo.libs.array_kernels.isna(arr, i):\n'
        for field in spabv__cestq:
            nxh__pwm += ('            bodo.libs.array_kernels.setna({}, i)\n'
                .format(field))
        nxh__pwm += '            continue\n'
        vwery__yfg = '(' + '[i], '.join(spabv__cestq) + '[i])'
        nxh__pwm += (
            '        {} = bodo.hiframes.pd_timestamp_ext.{}(arr[i]).{}\n'.
            format(vwery__yfg, bjl__zvmow, oxmtj__fpxqb))
        qltr__wxik = '(' + ', '.join(spabv__cestq) + ')'
        aoovj__ucod = "('" + "', '".join(spabv__cestq) + "')"
        nxh__pwm += (
            '    return bodo.hiframes.pd_dataframe_ext.init_dataframe({}, index, {})\n'
            .format(qltr__wxik, aoovj__ucod))
        lhcl__sqrrh = {}
        exec(nxh__pwm, {'bodo': bodo, 'numba': numba, 'np': np}, lhcl__sqrrh)
        impl = lhcl__sqrrh['impl']
        return impl
    return series_dt_df_output_overload


def _install_df_output_overload():
    vdiuv__qgsnb = [('components', overload_attribute), ('isocalendar',
        overload_method)]
    for attr, sas__xndp in vdiuv__qgsnb:
        aitl__juj = create_series_dt_df_output_overload(attr)
        sas__xndp(SeriesDatetimePropertiesType, attr, inline='always')(
            aitl__juj)


_install_df_output_overload()


def create_timedelta_field_overload(field):

    def overload_field(S_dt):
        if not S_dt.stype.dtype == types.NPTimedelta('ns'):
            return
        nxh__pwm = 'def impl(S_dt):\n'
        nxh__pwm += '    S = S_dt._obj\n'
        nxh__pwm += '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
        nxh__pwm += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        nxh__pwm += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        nxh__pwm += '    numba.parfors.parfor.init_prange()\n'
        nxh__pwm += '    n = len(A)\n'
        nxh__pwm += (
            '    B = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n')
        nxh__pwm += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        nxh__pwm += '        if bodo.libs.array_kernels.isna(A, i):\n'
        nxh__pwm += '            bodo.libs.array_kernels.setna(B, i)\n'
        nxh__pwm += '            continue\n'
        nxh__pwm += (
            '        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])\n'
            )
        if field == 'nanoseconds':
            nxh__pwm += '        B[i] = td64 % 1000\n'
        elif field == 'microseconds':
            nxh__pwm += '        B[i] = td64 // 1000 % 1000000\n'
        elif field == 'seconds':
            nxh__pwm += (
                '        B[i] = td64 // (1000 * 1000000) % (60 * 60 * 24)\n')
        elif field == 'days':
            nxh__pwm += (
                '        B[i] = td64 // (1000 * 1000000 * 60 * 60 * 24)\n')
        else:
            assert False, 'invalid timedelta field'
        nxh__pwm += (
            '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
            )
        lhcl__sqrrh = {}
        exec(nxh__pwm, {'numba': numba, 'np': np, 'bodo': bodo}, lhcl__sqrrh)
        impl = lhcl__sqrrh['impl']
        return impl
    return overload_field


def create_timedelta_method_overload(method):

    def overload_method(S_dt):
        if not S_dt.stype.dtype == types.NPTimedelta('ns'):
            return
        nxh__pwm = 'def impl(S_dt):\n'
        nxh__pwm += '    S = S_dt._obj\n'
        nxh__pwm += '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
        nxh__pwm += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        nxh__pwm += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        nxh__pwm += '    numba.parfors.parfor.init_prange()\n'
        nxh__pwm += '    n = len(A)\n'
        if method == 'total_seconds':
            nxh__pwm += '    B = np.empty(n, np.float64)\n'
        else:
            nxh__pwm += """    B = bodo.hiframes.datetime_timedelta_ext.alloc_datetime_timedelta_array(n)
"""
        nxh__pwm += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        nxh__pwm += '        if bodo.libs.array_kernels.isna(A, i):\n'
        nxh__pwm += '            bodo.libs.array_kernels.setna(B, i)\n'
        nxh__pwm += '            continue\n'
        nxh__pwm += (
            '        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])\n'
            )
        if method == 'total_seconds':
            nxh__pwm += '        B[i] = td64 / (1000.0 * 1000000.0)\n'
        elif method == 'to_pytimedelta':
            nxh__pwm += (
                '        B[i] = datetime.timedelta(microseconds=td64 // 1000)\n'
                )
        else:
            assert False, 'invalid timedelta method'
        if method == 'total_seconds':
            nxh__pwm += (
                '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
                )
        else:
            nxh__pwm += '    return B\n'
        lhcl__sqrrh = {}
        exec(nxh__pwm, {'numba': numba, 'np': np, 'bodo': bodo, 'datetime':
            datetime}, lhcl__sqrrh)
        impl = lhcl__sqrrh['impl']
        return impl
    return overload_method


def _install_S_dt_timedelta_fields():
    for field in bodo.hiframes.pd_timestamp_ext.timedelta_fields:
        aitl__juj = create_timedelta_field_overload(field)
        overload_attribute(SeriesDatetimePropertiesType, field)(aitl__juj)


_install_S_dt_timedelta_fields()


def _install_S_dt_timedelta_methods():
    for method in bodo.hiframes.pd_timestamp_ext.timedelta_methods:
        aitl__juj = create_timedelta_method_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            aitl__juj)


_install_S_dt_timedelta_methods()


@overload_method(SeriesDatetimePropertiesType, 'strftime', inline='always',
    no_unliteral=True)
def dt_strftime(S_dt, date_format):
    if not (S_dt.stype.dtype == types.NPDatetime('ns') or isinstance(S_dt.
        stype.dtype, bodo.libs.pd_datetime_arr_ext.PandasDatetimeTZDtype)):
        return
    if types.unliteral(date_format) != types.unicode_type:
        raise BodoError(
            "Series.str.strftime(): 'date_format' argument must be a string")

    def impl(S_dt, date_format):
        wdt__cqgnm = S_dt._obj
        yuf__ywo = bodo.hiframes.pd_series_ext.get_series_data(wdt__cqgnm)
        dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(wdt__cqgnm)
        jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(wdt__cqgnm)
        numba.parfors.parfor.init_prange()
        degl__eflw = len(yuf__ywo)
        xpdo__xbnt = bodo.libs.str_arr_ext.pre_alloc_string_array(degl__eflw,
            -1)
        for gbh__znsb in numba.parfors.parfor.internal_prange(degl__eflw):
            if bodo.libs.array_kernels.isna(yuf__ywo, gbh__znsb):
                bodo.libs.array_kernels.setna(xpdo__xbnt, gbh__znsb)
                continue
            xpdo__xbnt[gbh__znsb] = bodo.utils.conversion.box_if_dt64(yuf__ywo
                [gbh__znsb]).strftime(date_format)
        return bodo.hiframes.pd_series_ext.init_series(xpdo__xbnt, dbl__kmf,
            jlnkd__jio)
    return impl


@overload_method(SeriesDatetimePropertiesType, 'tz_convert', inline=
    'always', no_unliteral=True)
def overload_dt_tz_convert(S_dt, tz):

    def impl(S_dt, tz):
        wdt__cqgnm = S_dt._obj
        leq__sysk = get_series_data(wdt__cqgnm).tz_convert(tz)
        dbl__kmf = get_series_index(wdt__cqgnm)
        jlnkd__jio = get_series_name(wdt__cqgnm)
        return init_series(leq__sysk, dbl__kmf, jlnkd__jio)
    return impl


def create_timedelta_freq_overload(method):

    def freq_overload(S_dt, freq, ambiguous='raise', nonexistent='raise'):
        if S_dt.stype.dtype != types.NPTimedelta('ns'
            ) and S_dt.stype.dtype != types.NPDatetime('ns'
            ) and not isinstance(S_dt.stype.dtype, bodo.libs.
            pd_datetime_arr_ext.PandasDatetimeTZDtype):
            return
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S_dt,
            f'Series.dt.{method}()')
        cdcah__krwzg = dict(ambiguous=ambiguous, nonexistent=nonexistent)
        unta__msytv = dict(ambiguous='raise', nonexistent='raise')
        check_unsupported_args(f'Series.dt.{method}', cdcah__krwzg,
            unta__msytv, package_name='pandas', module_name='Series')
        nxh__pwm = (
            "def impl(S_dt, freq, ambiguous='raise', nonexistent='raise'):\n")
        nxh__pwm += '    S = S_dt._obj\n'
        nxh__pwm += '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
        nxh__pwm += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        nxh__pwm += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        nxh__pwm += '    numba.parfors.parfor.init_prange()\n'
        nxh__pwm += '    n = len(A)\n'
        if S_dt.stype.dtype == types.NPTimedelta('ns'):
            nxh__pwm += "    B = np.empty(n, np.dtype('timedelta64[ns]'))\n"
        else:
            nxh__pwm += "    B = np.empty(n, np.dtype('datetime64[ns]'))\n"
        nxh__pwm += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        nxh__pwm += '        if bodo.libs.array_kernels.isna(A, i):\n'
        nxh__pwm += '            bodo.libs.array_kernels.setna(B, i)\n'
        nxh__pwm += '            continue\n'
        if S_dt.stype.dtype == types.NPTimedelta('ns'):
            fqxn__xlim = (
                'bodo.hiframes.pd_timestamp_ext.convert_numpy_timedelta64_to_pd_timedelta'
                )
            xor__asqzn = (
                'bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64')
        else:
            fqxn__xlim = (
                'bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp'
                )
            xor__asqzn = 'bodo.hiframes.pd_timestamp_ext.integer_to_dt64'
        nxh__pwm += '        B[i] = {}({}(A[i]).{}(freq).value)\n'.format(
            xor__asqzn, fqxn__xlim, method)
        nxh__pwm += (
            '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
            )
        lhcl__sqrrh = {}
        exec(nxh__pwm, {'numba': numba, 'np': np, 'bodo': bodo}, lhcl__sqrrh)
        impl = lhcl__sqrrh['impl']
        return impl
    return freq_overload


def _install_S_dt_timedelta_freq_methods():
    qqf__rfsvm = ['ceil', 'floor', 'round']
    for method in qqf__rfsvm:
        aitl__juj = create_timedelta_freq_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            aitl__juj)


_install_S_dt_timedelta_freq_methods()


def create_bin_op_overload(op):

    def overload_series_dt_binop(lhs, rhs):
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs):
            fas__euwdv = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                xxw__oiw = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                yiuys__hgx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    xxw__oiw)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                tut__pno = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                mebfx__vdit = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    tut__pno)
                degl__eflw = len(yiuys__hgx)
                wdt__cqgnm = np.empty(degl__eflw, timedelta64_dtype)
                cotpw__mirq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fas__euwdv)
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    zco__gcr = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        yiuys__hgx[ebqng__opi])
                    xkxex__uuf = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(mebfx__vdit[ebqng__opi]))
                    if zco__gcr == cotpw__mirq or xkxex__uuf == cotpw__mirq:
                        dsq__saqog = cotpw__mirq
                    else:
                        dsq__saqog = op(zco__gcr, xkxex__uuf)
                    wdt__cqgnm[ebqng__opi
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        dsq__saqog)
                return bodo.hiframes.pd_series_ext.init_series(wdt__cqgnm,
                    dbl__kmf, jlnkd__jio)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs):
            fas__euwdv = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                vvxwp__vzo = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                egwk__gdx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    vvxwp__vzo)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                mebfx__vdit = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                degl__eflw = len(egwk__gdx)
                wdt__cqgnm = np.empty(degl__eflw, dt64_dtype)
                cotpw__mirq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fas__euwdv)
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    wra__ixu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        egwk__gdx[ebqng__opi])
                    xcgj__ozea = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(mebfx__vdit[ebqng__opi]))
                    if wra__ixu == cotpw__mirq or xcgj__ozea == cotpw__mirq:
                        dsq__saqog = cotpw__mirq
                    else:
                        dsq__saqog = op(wra__ixu, xcgj__ozea)
                    wdt__cqgnm[ebqng__opi
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        dsq__saqog)
                return bodo.hiframes.pd_series_ext.init_series(wdt__cqgnm,
                    dbl__kmf, jlnkd__jio)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
            ) and bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs):
            fas__euwdv = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                vvxwp__vzo = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                egwk__gdx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    vvxwp__vzo)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                mebfx__vdit = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                degl__eflw = len(egwk__gdx)
                wdt__cqgnm = np.empty(degl__eflw, dt64_dtype)
                cotpw__mirq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fas__euwdv)
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    wra__ixu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        egwk__gdx[ebqng__opi])
                    xcgj__ozea = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(mebfx__vdit[ebqng__opi]))
                    if wra__ixu == cotpw__mirq or xcgj__ozea == cotpw__mirq:
                        dsq__saqog = cotpw__mirq
                    else:
                        dsq__saqog = op(wra__ixu, xcgj__ozea)
                    wdt__cqgnm[ebqng__opi
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        dsq__saqog)
                return bodo.hiframes.pd_series_ext.init_series(wdt__cqgnm,
                    dbl__kmf, jlnkd__jio)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            fas__euwdv = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                vvxwp__vzo = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                egwk__gdx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    vvxwp__vzo)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                degl__eflw = len(egwk__gdx)
                wdt__cqgnm = np.empty(degl__eflw, timedelta64_dtype)
                cotpw__mirq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fas__euwdv)
                brmen__nsv = rhs.value
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    wra__ixu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        egwk__gdx[ebqng__opi])
                    if wra__ixu == cotpw__mirq or brmen__nsv == cotpw__mirq:
                        dsq__saqog = cotpw__mirq
                    else:
                        dsq__saqog = op(wra__ixu, brmen__nsv)
                    wdt__cqgnm[ebqng__opi
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        dsq__saqog)
                return bodo.hiframes.pd_series_ext.init_series(wdt__cqgnm,
                    dbl__kmf, jlnkd__jio)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
            ) and lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            fas__euwdv = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                vvxwp__vzo = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                egwk__gdx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    vvxwp__vzo)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                degl__eflw = len(egwk__gdx)
                wdt__cqgnm = np.empty(degl__eflw, timedelta64_dtype)
                cotpw__mirq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fas__euwdv)
                brmen__nsv = lhs.value
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    wra__ixu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        egwk__gdx[ebqng__opi])
                    if brmen__nsv == cotpw__mirq or wra__ixu == cotpw__mirq:
                        dsq__saqog = cotpw__mirq
                    else:
                        dsq__saqog = op(brmen__nsv, wra__ixu)
                    wdt__cqgnm[ebqng__opi
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        dsq__saqog)
                return bodo.hiframes.pd_series_ext.init_series(wdt__cqgnm,
                    dbl__kmf, jlnkd__jio)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and rhs ==
            bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type):
            fas__euwdv = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                vvxwp__vzo = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                egwk__gdx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    vvxwp__vzo)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                degl__eflw = len(egwk__gdx)
                wdt__cqgnm = np.empty(degl__eflw, dt64_dtype)
                cotpw__mirq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fas__euwdv)
                szynb__zwcuu = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                xcgj__ozea = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(szynb__zwcuu))
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    wra__ixu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        egwk__gdx[ebqng__opi])
                    if wra__ixu == cotpw__mirq or xcgj__ozea == cotpw__mirq:
                        dsq__saqog = cotpw__mirq
                    else:
                        dsq__saqog = op(wra__ixu, xcgj__ozea)
                    wdt__cqgnm[ebqng__opi
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        dsq__saqog)
                return bodo.hiframes.pd_series_ext.init_series(wdt__cqgnm,
                    dbl__kmf, jlnkd__jio)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and lhs ==
            bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type):
            fas__euwdv = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                vvxwp__vzo = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                egwk__gdx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    vvxwp__vzo)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                degl__eflw = len(egwk__gdx)
                wdt__cqgnm = np.empty(degl__eflw, dt64_dtype)
                cotpw__mirq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fas__euwdv)
                szynb__zwcuu = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                xcgj__ozea = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(szynb__zwcuu))
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    wra__ixu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        egwk__gdx[ebqng__opi])
                    if wra__ixu == cotpw__mirq or xcgj__ozea == cotpw__mirq:
                        dsq__saqog = cotpw__mirq
                    else:
                        dsq__saqog = op(wra__ixu, xcgj__ozea)
                    wdt__cqgnm[ebqng__opi
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        dsq__saqog)
                return bodo.hiframes.pd_series_ext.init_series(wdt__cqgnm,
                    dbl__kmf, jlnkd__jio)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and rhs ==
            bodo.hiframes.datetime_datetime_ext.datetime_datetime_type):
            fas__euwdv = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                vvxwp__vzo = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                egwk__gdx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    vvxwp__vzo)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                degl__eflw = len(egwk__gdx)
                wdt__cqgnm = np.empty(degl__eflw, timedelta64_dtype)
                cotpw__mirq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fas__euwdv)
                uypfo__rfs = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(rhs))
                wra__ixu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    uypfo__rfs)
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    ccva__dnf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        egwk__gdx[ebqng__opi])
                    if ccva__dnf == cotpw__mirq or wra__ixu == cotpw__mirq:
                        dsq__saqog = cotpw__mirq
                    else:
                        dsq__saqog = op(ccva__dnf, wra__ixu)
                    wdt__cqgnm[ebqng__opi
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        dsq__saqog)
                return bodo.hiframes.pd_series_ext.init_series(wdt__cqgnm,
                    dbl__kmf, jlnkd__jio)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and lhs ==
            bodo.hiframes.datetime_datetime_ext.datetime_datetime_type):
            fas__euwdv = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                vvxwp__vzo = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                egwk__gdx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    vvxwp__vzo)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                degl__eflw = len(egwk__gdx)
                wdt__cqgnm = np.empty(degl__eflw, timedelta64_dtype)
                cotpw__mirq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fas__euwdv)
                uypfo__rfs = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(lhs))
                wra__ixu = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    uypfo__rfs)
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    ccva__dnf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        egwk__gdx[ebqng__opi])
                    if wra__ixu == cotpw__mirq or ccva__dnf == cotpw__mirq:
                        dsq__saqog = cotpw__mirq
                    else:
                        dsq__saqog = op(wra__ixu, ccva__dnf)
                    wdt__cqgnm[ebqng__opi
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        dsq__saqog)
                return bodo.hiframes.pd_series_ext.init_series(wdt__cqgnm,
                    dbl__kmf, jlnkd__jio)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs) and 
            rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            fas__euwdv = lhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                egwk__gdx = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                degl__eflw = len(egwk__gdx)
                wdt__cqgnm = np.empty(degl__eflw, timedelta64_dtype)
                cotpw__mirq = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(fas__euwdv))
                szynb__zwcuu = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                xcgj__ozea = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(szynb__zwcuu))
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    pgc__fjoxs = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(egwk__gdx[ebqng__opi]))
                    if xcgj__ozea == cotpw__mirq or pgc__fjoxs == cotpw__mirq:
                        dsq__saqog = cotpw__mirq
                    else:
                        dsq__saqog = op(pgc__fjoxs, xcgj__ozea)
                    wdt__cqgnm[ebqng__opi
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        dsq__saqog)
                return bodo.hiframes.pd_series_ext.init_series(wdt__cqgnm,
                    dbl__kmf, jlnkd__jio)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs) and 
            lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            fas__euwdv = rhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                egwk__gdx = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                degl__eflw = len(egwk__gdx)
                wdt__cqgnm = np.empty(degl__eflw, timedelta64_dtype)
                cotpw__mirq = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(fas__euwdv))
                szynb__zwcuu = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                xcgj__ozea = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(szynb__zwcuu))
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    pgc__fjoxs = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(egwk__gdx[ebqng__opi]))
                    if xcgj__ozea == cotpw__mirq or pgc__fjoxs == cotpw__mirq:
                        dsq__saqog = cotpw__mirq
                    else:
                        dsq__saqog = op(xcgj__ozea, pgc__fjoxs)
                    wdt__cqgnm[ebqng__opi
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        dsq__saqog)
                return bodo.hiframes.pd_series_ext.init_series(wdt__cqgnm,
                    dbl__kmf, jlnkd__jio)
            return impl
        raise BodoError(f'{op} not supported for data types {lhs} and {rhs}.')
    return overload_series_dt_binop


def create_cmp_op_overload(op):

    def overload_series_dt64_cmp(lhs, rhs):
        if op == operator.ne:
            agk__upo = True
        else:
            agk__upo = False
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs) and 
            rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            fas__euwdv = lhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                egwk__gdx = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                degl__eflw = len(egwk__gdx)
                vtqjp__xdj = bodo.libs.bool_arr_ext.alloc_bool_array(degl__eflw
                    )
                cotpw__mirq = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(fas__euwdv))
                htywf__xuoe = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                xdbtg__henu = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(htywf__xuoe))
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    fes__vkw = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(egwk__gdx[ebqng__opi]))
                    if fes__vkw == cotpw__mirq or xdbtg__henu == cotpw__mirq:
                        dsq__saqog = agk__upo
                    else:
                        dsq__saqog = op(fes__vkw, xdbtg__henu)
                    vtqjp__xdj[ebqng__opi] = dsq__saqog
                return bodo.hiframes.pd_series_ext.init_series(vtqjp__xdj,
                    dbl__kmf, jlnkd__jio)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs) and 
            lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            fas__euwdv = rhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                egwk__gdx = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                degl__eflw = len(egwk__gdx)
                vtqjp__xdj = bodo.libs.bool_arr_ext.alloc_bool_array(degl__eflw
                    )
                cotpw__mirq = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(fas__euwdv))
                kyay__glavn = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                fes__vkw = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(kyay__glavn))
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    xdbtg__henu = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(egwk__gdx[ebqng__opi]))
                    if fes__vkw == cotpw__mirq or xdbtg__henu == cotpw__mirq:
                        dsq__saqog = agk__upo
                    else:
                        dsq__saqog = op(fes__vkw, xdbtg__henu)
                    vtqjp__xdj[ebqng__opi] = dsq__saqog
                return bodo.hiframes.pd_series_ext.init_series(vtqjp__xdj,
                    dbl__kmf, jlnkd__jio)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            fas__euwdv = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                vvxwp__vzo = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                egwk__gdx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    vvxwp__vzo)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                degl__eflw = len(egwk__gdx)
                vtqjp__xdj = bodo.libs.bool_arr_ext.alloc_bool_array(degl__eflw
                    )
                cotpw__mirq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fas__euwdv)
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    fes__vkw = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        egwk__gdx[ebqng__opi])
                    if fes__vkw == cotpw__mirq or rhs.value == cotpw__mirq:
                        dsq__saqog = agk__upo
                    else:
                        dsq__saqog = op(fes__vkw, rhs.value)
                    vtqjp__xdj[ebqng__opi] = dsq__saqog
                return bodo.hiframes.pd_series_ext.init_series(vtqjp__xdj,
                    dbl__kmf, jlnkd__jio)
            return impl
        if (lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type and
            bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs)):
            fas__euwdv = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                vvxwp__vzo = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                egwk__gdx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    vvxwp__vzo)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                degl__eflw = len(egwk__gdx)
                vtqjp__xdj = bodo.libs.bool_arr_ext.alloc_bool_array(degl__eflw
                    )
                cotpw__mirq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fas__euwdv)
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    xdbtg__henu = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(egwk__gdx[ebqng__opi]))
                    if xdbtg__henu == cotpw__mirq or lhs.value == cotpw__mirq:
                        dsq__saqog = agk__upo
                    else:
                        dsq__saqog = op(lhs.value, xdbtg__henu)
                    vtqjp__xdj[ebqng__opi] = dsq__saqog
                return bodo.hiframes.pd_series_ext.init_series(vtqjp__xdj,
                    dbl__kmf, jlnkd__jio)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and (rhs ==
            bodo.libs.str_ext.string_type or bodo.utils.typing.
            is_overload_constant_str(rhs)):
            fas__euwdv = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                vvxwp__vzo = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                egwk__gdx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    vvxwp__vzo)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                numba.parfors.parfor.init_prange()
                degl__eflw = len(egwk__gdx)
                vtqjp__xdj = bodo.libs.bool_arr_ext.alloc_bool_array(degl__eflw
                    )
                cotpw__mirq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fas__euwdv)
                swj__mdfx = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(
                    rhs)
                pzrbh__lan = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    swj__mdfx)
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    fes__vkw = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        egwk__gdx[ebqng__opi])
                    if fes__vkw == cotpw__mirq or pzrbh__lan == cotpw__mirq:
                        dsq__saqog = agk__upo
                    else:
                        dsq__saqog = op(fes__vkw, pzrbh__lan)
                    vtqjp__xdj[ebqng__opi] = dsq__saqog
                return bodo.hiframes.pd_series_ext.init_series(vtqjp__xdj,
                    dbl__kmf, jlnkd__jio)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and (lhs ==
            bodo.libs.str_ext.string_type or bodo.utils.typing.
            is_overload_constant_str(lhs)):
            fas__euwdv = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                vvxwp__vzo = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                egwk__gdx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    vvxwp__vzo)
                dbl__kmf = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                jlnkd__jio = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                numba.parfors.parfor.init_prange()
                degl__eflw = len(egwk__gdx)
                vtqjp__xdj = bodo.libs.bool_arr_ext.alloc_bool_array(degl__eflw
                    )
                cotpw__mirq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fas__euwdv)
                swj__mdfx = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(
                    lhs)
                pzrbh__lan = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    swj__mdfx)
                for ebqng__opi in numba.parfors.parfor.internal_prange(
                    degl__eflw):
                    uypfo__rfs = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(egwk__gdx[ebqng__opi]))
                    if uypfo__rfs == cotpw__mirq or pzrbh__lan == cotpw__mirq:
                        dsq__saqog = agk__upo
                    else:
                        dsq__saqog = op(pzrbh__lan, uypfo__rfs)
                    vtqjp__xdj[ebqng__opi] = dsq__saqog
                return bodo.hiframes.pd_series_ext.init_series(vtqjp__xdj,
                    dbl__kmf, jlnkd__jio)
            return impl
        raise BodoError(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_series_dt64_cmp


series_dt_unsupported_methods = {'to_period', 'to_pydatetime',
    'tz_localize', 'asfreq', 'to_timestamp'}
series_dt_unsupported_attrs = {'time', 'timetz', 'tz', 'freq', 'qyear',
    'start_time', 'end_time'}


def _install_series_dt_unsupported():
    for zkvz__pce in series_dt_unsupported_attrs:
        frake__hcyvm = 'Series.dt.' + zkvz__pce
        overload_attribute(SeriesDatetimePropertiesType, zkvz__pce)(
            create_unsupported_overload(frake__hcyvm))
    for nri__dqzxs in series_dt_unsupported_methods:
        frake__hcyvm = 'Series.dt.' + nri__dqzxs
        overload_method(SeriesDatetimePropertiesType, nri__dqzxs,
            no_unliteral=True)(create_unsupported_overload(frake__hcyvm))


_install_series_dt_unsupported()
