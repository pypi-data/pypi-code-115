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
        yyfty__hxp = 'SeriesDatetimePropertiesType({})'.format(stype)
        super(SeriesDatetimePropertiesType, self).__init__(yyfty__hxp)


@register_model(SeriesDatetimePropertiesType)
class SeriesDtModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        ebt__rnhgm = [('obj', fe_type.stype)]
        super(SeriesDtModel, self).__init__(dmm, fe_type, ebt__rnhgm)


make_attribute_wrapper(SeriesDatetimePropertiesType, 'obj', '_obj')


@intrinsic
def init_series_dt_properties(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        ngw__bgyuc, = args
        murl__aobxb = signature.return_type
        ndi__sgi = cgutils.create_struct_proxy(murl__aobxb)(context, builder)
        ndi__sgi.obj = ngw__bgyuc
        context.nrt.incref(builder, signature.args[0], ngw__bgyuc)
        return ndi__sgi._getvalue()
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
        sik__uhrim = 'def impl(S_dt):\n'
        sik__uhrim += '    S = S_dt._obj\n'
        sik__uhrim += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        sik__uhrim += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        sik__uhrim += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        sik__uhrim += '    numba.parfors.parfor.init_prange()\n'
        sik__uhrim += '    n = len(arr)\n'
        if field in ('is_leap_year', 'is_month_start', 'is_month_end',
            'is_quarter_start', 'is_quarter_end', 'is_year_start',
            'is_year_end'):
            sik__uhrim += '    out_arr = np.empty(n, np.bool_)\n'
        else:
            sik__uhrim += (
                '    out_arr = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n'
                )
        sik__uhrim += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        sik__uhrim += '        if bodo.libs.array_kernels.isna(arr, i):\n'
        sik__uhrim += '            bodo.libs.array_kernels.setna(out_arr, i)\n'
        sik__uhrim += '            continue\n'
        sik__uhrim += (
            '        dt64 = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(arr[i])\n'
            )
        if field in ('year', 'month', 'day'):
            sik__uhrim += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            if field in ('month', 'day'):
                sik__uhrim += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            sik__uhrim += '        out_arr[i] = {}\n'.format(field)
        elif field in ('dayofyear', 'day_of_year', 'dayofweek',
            'day_of_week', 'weekday'):
            lee__pbg = {'dayofyear': 'get_day_of_year', 'day_of_year':
                'get_day_of_year', 'dayofweek': 'get_day_of_week',
                'day_of_week': 'get_day_of_week', 'weekday': 'get_day_of_week'}
            sik__uhrim += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            sik__uhrim += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            sik__uhrim += (
                """        out_arr[i] = bodo.hiframes.pd_timestamp_ext.{}(year, month, day)
"""
                .format(lee__pbg[field]))
        elif field == 'is_leap_year':
            sik__uhrim += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            sik__uhrim += """        out_arr[i] = bodo.hiframes.pd_timestamp_ext.is_leap_year(year)
"""
        elif field in ('daysinmonth', 'days_in_month'):
            lee__pbg = {'days_in_month': 'get_days_in_month', 'daysinmonth':
                'get_days_in_month'}
            sik__uhrim += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            sik__uhrim += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            sik__uhrim += (
                '        out_arr[i] = bodo.hiframes.pd_timestamp_ext.{}(year, month)\n'
                .format(lee__pbg[field]))
        else:
            sik__uhrim += """        ts = bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp(dt64)
"""
            sik__uhrim += '        out_arr[i] = ts.' + field + '\n'
        sik__uhrim += (
            '    return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        zunko__ywdnw = {}
        exec(sik__uhrim, {'bodo': bodo, 'numba': numba, 'np': np}, zunko__ywdnw
            )
        impl = zunko__ywdnw['impl']
        return impl
    return overload_field


def _install_date_fields():
    for field in bodo.hiframes.pd_timestamp_ext.date_fields:
        zeveu__olba = create_date_field_overload(field)
        overload_attribute(SeriesDatetimePropertiesType, field)(zeveu__olba)


_install_date_fields()


def create_date_method_overload(method):
    xnli__wuh = method in ['day_name', 'month_name']
    if xnli__wuh:
        sik__uhrim = 'def overload_method(S_dt, locale=None):\n'
        sik__uhrim += '    unsupported_args = dict(locale=locale)\n'
        sik__uhrim += '    arg_defaults = dict(locale=None)\n'
        sik__uhrim += '    bodo.utils.typing.check_unsupported_args(\n'
        sik__uhrim += f"        'Series.dt.{method}',\n"
        sik__uhrim += '        unsupported_args,\n'
        sik__uhrim += '        arg_defaults,\n'
        sik__uhrim += "        package_name='pandas',\n"
        sik__uhrim += "        module_name='Series',\n"
        sik__uhrim += '    )\n'
    else:
        sik__uhrim = 'def overload_method(S_dt):\n'
    sik__uhrim += '    if not S_dt.stype.dtype == bodo.datetime64ns:\n'
    sik__uhrim += '        return\n'
    if xnli__wuh:
        sik__uhrim += '    def impl(S_dt, locale=None):\n'
    else:
        sik__uhrim += '    def impl(S_dt):\n'
    sik__uhrim += '        S = S_dt._obj\n'
    sik__uhrim += (
        '        arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    sik__uhrim += (
        '        index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
    sik__uhrim += (
        '        name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
    sik__uhrim += '        numba.parfors.parfor.init_prange()\n'
    sik__uhrim += '        n = len(arr)\n'
    if xnli__wuh:
        sik__uhrim += """        out_arr = bodo.utils.utils.alloc_type(n, bodo.string_array_type, (-1,))
"""
    else:
        sik__uhrim += (
            "        out_arr = np.empty(n, np.dtype('datetime64[ns]'))\n")
    sik__uhrim += '        for i in numba.parfors.parfor.internal_prange(n):\n'
    sik__uhrim += '            if bodo.libs.array_kernels.isna(arr, i):\n'
    sik__uhrim += '                bodo.libs.array_kernels.setna(out_arr, i)\n'
    sik__uhrim += '                continue\n'
    sik__uhrim += """            ts = bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp(arr[i])
"""
    sik__uhrim += f'            method_val = ts.{method}()\n'
    if xnli__wuh:
        sik__uhrim += '            out_arr[i] = method_val\n'
    else:
        sik__uhrim += """            out_arr[i] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(method_val.value)
"""
    sik__uhrim += (
        '        return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    sik__uhrim += '    return impl\n'
    zunko__ywdnw = {}
    exec(sik__uhrim, {'bodo': bodo, 'numba': numba, 'np': np}, zunko__ywdnw)
    overload_method = zunko__ywdnw['overload_method']
    return overload_method


def _install_date_methods():
    for method in bodo.hiframes.pd_timestamp_ext.date_methods:
        zeveu__olba = create_date_method_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            zeveu__olba)


_install_date_methods()


@overload_attribute(SeriesDatetimePropertiesType, 'date')
def series_dt_date_overload(S_dt):
    if not S_dt.stype.dtype == types.NPDatetime('ns'):
        return

    def impl(S_dt):
        sxylj__hnnw = S_dt._obj
        wvv__vdwlm = bodo.hiframes.pd_series_ext.get_series_data(sxylj__hnnw)
        bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(sxylj__hnnw)
        yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(sxylj__hnnw)
        numba.parfors.parfor.init_prange()
        iomoi__ssbie = len(wvv__vdwlm)
        nxw__dbo = bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(
            iomoi__ssbie)
        for avbf__lpll in numba.parfors.parfor.internal_prange(iomoi__ssbie):
            fwk__mycn = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                wvv__vdwlm[avbf__lpll])
            onlor__znuwu = (bodo.hiframes.pd_timestamp_ext.
                convert_datetime64_to_timestamp(fwk__mycn))
            nxw__dbo[avbf__lpll] = datetime.date(onlor__znuwu.year,
                onlor__znuwu.month, onlor__znuwu.day)
        return bodo.hiframes.pd_series_ext.init_series(nxw__dbo, bgjf__cfh,
            yyfty__hxp)
    return impl


def create_series_dt_df_output_overload(attr):

    def series_dt_df_output_overload(S_dt):
        if not (attr == 'components' and S_dt.stype.dtype == types.
            NPTimedelta('ns') or attr == 'isocalendar' and S_dt.stype.dtype ==
            types.NPDatetime('ns')):
            return
        if attr == 'components':
            ffqu__umf = ['days', 'hours', 'minutes', 'seconds',
                'milliseconds', 'microseconds', 'nanoseconds']
            gvn__jwri = 'convert_numpy_timedelta64_to_pd_timedelta'
            bjci__rsbb = 'np.empty(n, np.int64)'
            fkk__tsdog = attr
        elif attr == 'isocalendar':
            ffqu__umf = ['year', 'week', 'day']
            gvn__jwri = 'convert_datetime64_to_timestamp'
            bjci__rsbb = 'bodo.libs.int_arr_ext.alloc_int_array(n, np.uint32)'
            fkk__tsdog = attr + '()'
        sik__uhrim = 'def impl(S_dt):\n'
        sik__uhrim += '    S = S_dt._obj\n'
        sik__uhrim += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        sik__uhrim += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        sik__uhrim += '    numba.parfors.parfor.init_prange()\n'
        sik__uhrim += '    n = len(arr)\n'
        for field in ffqu__umf:
            sik__uhrim += '    {} = {}\n'.format(field, bjci__rsbb)
        sik__uhrim += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        sik__uhrim += '        if bodo.libs.array_kernels.isna(arr, i):\n'
        for field in ffqu__umf:
            sik__uhrim += ('            bodo.libs.array_kernels.setna({}, i)\n'
                .format(field))
        sik__uhrim += '            continue\n'
        hormk__mcsok = '(' + '[i], '.join(ffqu__umf) + '[i])'
        sik__uhrim += (
            '        {} = bodo.hiframes.pd_timestamp_ext.{}(arr[i]).{}\n'.
            format(hormk__mcsok, gvn__jwri, fkk__tsdog))
        zyvfg__ydwjf = '(' + ', '.join(ffqu__umf) + ')'
        qjcw__dywlw = "('" + "', '".join(ffqu__umf) + "')"
        sik__uhrim += (
            '    return bodo.hiframes.pd_dataframe_ext.init_dataframe({}, index, {})\n'
            .format(zyvfg__ydwjf, qjcw__dywlw))
        zunko__ywdnw = {}
        exec(sik__uhrim, {'bodo': bodo, 'numba': numba, 'np': np}, zunko__ywdnw
            )
        impl = zunko__ywdnw['impl']
        return impl
    return series_dt_df_output_overload


def _install_df_output_overload():
    ezb__dfi = [('components', overload_attribute), ('isocalendar',
        overload_method)]
    for attr, dlq__fmad in ezb__dfi:
        zeveu__olba = create_series_dt_df_output_overload(attr)
        dlq__fmad(SeriesDatetimePropertiesType, attr, inline='always')(
            zeveu__olba)


_install_df_output_overload()


def create_timedelta_field_overload(field):

    def overload_field(S_dt):
        if not S_dt.stype.dtype == types.NPTimedelta('ns'):
            return
        sik__uhrim = 'def impl(S_dt):\n'
        sik__uhrim += '    S = S_dt._obj\n'
        sik__uhrim += (
            '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        sik__uhrim += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        sik__uhrim += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        sik__uhrim += '    numba.parfors.parfor.init_prange()\n'
        sik__uhrim += '    n = len(A)\n'
        sik__uhrim += (
            '    B = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n')
        sik__uhrim += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        sik__uhrim += '        if bodo.libs.array_kernels.isna(A, i):\n'
        sik__uhrim += '            bodo.libs.array_kernels.setna(B, i)\n'
        sik__uhrim += '            continue\n'
        sik__uhrim += """        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])
"""
        if field == 'nanoseconds':
            sik__uhrim += '        B[i] = td64 % 1000\n'
        elif field == 'microseconds':
            sik__uhrim += '        B[i] = td64 // 1000 % 1000000\n'
        elif field == 'seconds':
            sik__uhrim += (
                '        B[i] = td64 // (1000 * 1000000) % (60 * 60 * 24)\n')
        elif field == 'days':
            sik__uhrim += (
                '        B[i] = td64 // (1000 * 1000000 * 60 * 60 * 24)\n')
        else:
            assert False, 'invalid timedelta field'
        sik__uhrim += (
            '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
            )
        zunko__ywdnw = {}
        exec(sik__uhrim, {'numba': numba, 'np': np, 'bodo': bodo}, zunko__ywdnw
            )
        impl = zunko__ywdnw['impl']
        return impl
    return overload_field


def create_timedelta_method_overload(method):

    def overload_method(S_dt):
        if not S_dt.stype.dtype == types.NPTimedelta('ns'):
            return
        sik__uhrim = 'def impl(S_dt):\n'
        sik__uhrim += '    S = S_dt._obj\n'
        sik__uhrim += (
            '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        sik__uhrim += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        sik__uhrim += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        sik__uhrim += '    numba.parfors.parfor.init_prange()\n'
        sik__uhrim += '    n = len(A)\n'
        if method == 'total_seconds':
            sik__uhrim += '    B = np.empty(n, np.float64)\n'
        else:
            sik__uhrim += """    B = bodo.hiframes.datetime_timedelta_ext.alloc_datetime_timedelta_array(n)
"""
        sik__uhrim += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        sik__uhrim += '        if bodo.libs.array_kernels.isna(A, i):\n'
        sik__uhrim += '            bodo.libs.array_kernels.setna(B, i)\n'
        sik__uhrim += '            continue\n'
        sik__uhrim += """        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])
"""
        if method == 'total_seconds':
            sik__uhrim += '        B[i] = td64 / (1000.0 * 1000000.0)\n'
        elif method == 'to_pytimedelta':
            sik__uhrim += (
                '        B[i] = datetime.timedelta(microseconds=td64 // 1000)\n'
                )
        else:
            assert False, 'invalid timedelta method'
        if method == 'total_seconds':
            sik__uhrim += (
                '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
                )
        else:
            sik__uhrim += '    return B\n'
        zunko__ywdnw = {}
        exec(sik__uhrim, {'numba': numba, 'np': np, 'bodo': bodo,
            'datetime': datetime}, zunko__ywdnw)
        impl = zunko__ywdnw['impl']
        return impl
    return overload_method


def _install_S_dt_timedelta_fields():
    for field in bodo.hiframes.pd_timestamp_ext.timedelta_fields:
        zeveu__olba = create_timedelta_field_overload(field)
        overload_attribute(SeriesDatetimePropertiesType, field)(zeveu__olba)


_install_S_dt_timedelta_fields()


def _install_S_dt_timedelta_methods():
    for method in bodo.hiframes.pd_timestamp_ext.timedelta_methods:
        zeveu__olba = create_timedelta_method_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            zeveu__olba)


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
        sxylj__hnnw = S_dt._obj
        whfnp__qmoex = bodo.hiframes.pd_series_ext.get_series_data(sxylj__hnnw)
        bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(sxylj__hnnw)
        yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(sxylj__hnnw)
        numba.parfors.parfor.init_prange()
        iomoi__ssbie = len(whfnp__qmoex)
        qqbxh__umjyn = bodo.libs.str_arr_ext.pre_alloc_string_array(
            iomoi__ssbie, -1)
        for lpv__zku in numba.parfors.parfor.internal_prange(iomoi__ssbie):
            if bodo.libs.array_kernels.isna(whfnp__qmoex, lpv__zku):
                bodo.libs.array_kernels.setna(qqbxh__umjyn, lpv__zku)
                continue
            qqbxh__umjyn[lpv__zku
                ] = bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp(
                whfnp__qmoex[lpv__zku]).strftime(date_format)
        return bodo.hiframes.pd_series_ext.init_series(qqbxh__umjyn,
            bgjf__cfh, yyfty__hxp)
    return impl


@overload_method(SeriesDatetimePropertiesType, 'tz_convert', inline=
    'always', no_unliteral=True)
def overload_dt_tz_convert(S_dt, tz):

    def impl(S_dt, tz):
        sxylj__hnnw = S_dt._obj
        anmbk__unohv = get_series_data(sxylj__hnnw).tz_convert(tz)
        bgjf__cfh = get_series_index(sxylj__hnnw)
        yyfty__hxp = get_series_name(sxylj__hnnw)
        return init_series(anmbk__unohv, bgjf__cfh, yyfty__hxp)
    return impl


def create_timedelta_freq_overload(method):

    def freq_overload(S_dt, freq, ambiguous='raise', nonexistent='raise'):
        if S_dt.stype.dtype != types.NPTimedelta('ns'
            ) and S_dt.stype.dtype != types.NPDatetime('ns'):
            return
        hgecz__vuge = dict(ambiguous=ambiguous, nonexistent=nonexistent)
        rvrc__xtyar = dict(ambiguous='raise', nonexistent='raise')
        check_unsupported_args(f'Series.dt.{method}', hgecz__vuge,
            rvrc__xtyar, package_name='pandas', module_name='Series')
        sik__uhrim = (
            "def impl(S_dt, freq, ambiguous='raise', nonexistent='raise'):\n")
        sik__uhrim += '    S = S_dt._obj\n'
        sik__uhrim += (
            '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        sik__uhrim += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        sik__uhrim += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        sik__uhrim += '    numba.parfors.parfor.init_prange()\n'
        sik__uhrim += '    n = len(A)\n'
        if S_dt.stype.dtype == types.NPTimedelta('ns'):
            sik__uhrim += "    B = np.empty(n, np.dtype('timedelta64[ns]'))\n"
        else:
            sik__uhrim += "    B = np.empty(n, np.dtype('datetime64[ns]'))\n"
        sik__uhrim += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        sik__uhrim += '        if bodo.libs.array_kernels.isna(A, i):\n'
        sik__uhrim += '            bodo.libs.array_kernels.setna(B, i)\n'
        sik__uhrim += '            continue\n'
        if S_dt.stype.dtype == types.NPTimedelta('ns'):
            vcej__wph = (
                'bodo.hiframes.pd_timestamp_ext.convert_numpy_timedelta64_to_pd_timedelta'
                )
            gkh__mksym = (
                'bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64')
        else:
            vcej__wph = (
                'bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp'
                )
            gkh__mksym = 'bodo.hiframes.pd_timestamp_ext.integer_to_dt64'
        sik__uhrim += '        B[i] = {}({}(A[i]).{}(freq).value)\n'.format(
            gkh__mksym, vcej__wph, method)
        sik__uhrim += (
            '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
            )
        zunko__ywdnw = {}
        exec(sik__uhrim, {'numba': numba, 'np': np, 'bodo': bodo}, zunko__ywdnw
            )
        impl = zunko__ywdnw['impl']
        return impl
    return freq_overload


def _install_S_dt_timedelta_freq_methods():
    ovaz__ujs = ['ceil', 'floor', 'round']
    for method in ovaz__ujs:
        zeveu__olba = create_timedelta_freq_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            zeveu__olba)


_install_S_dt_timedelta_freq_methods()


def create_bin_op_overload(op):

    def overload_series_dt_binop(lhs, rhs):
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs):
            ifx__wein = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qxi__pnuh = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                uczh__yvg = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qxi__pnuh)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                nbdhe__pnr = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                cba__vihmb = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    nbdhe__pnr)
                iomoi__ssbie = len(uczh__yvg)
                sxylj__hnnw = np.empty(iomoi__ssbie, timedelta64_dtype)
                lwcb__yrrk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ifx__wein)
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    iat__ygubq = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(uczh__yvg[avbf__lpll]))
                    kqp__qgkjd = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(cba__vihmb[avbf__lpll]))
                    if iat__ygubq == lwcb__yrrk or kqp__qgkjd == lwcb__yrrk:
                        heoj__ssj = lwcb__yrrk
                    else:
                        heoj__ssj = op(iat__ygubq, kqp__qgkjd)
                    sxylj__hnnw[avbf__lpll
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        heoj__ssj)
                return bodo.hiframes.pd_series_ext.init_series(sxylj__hnnw,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs):
            ifx__wein = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                frox__psu = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                wvv__vdwlm = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    frox__psu)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                cba__vihmb = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                iomoi__ssbie = len(wvv__vdwlm)
                sxylj__hnnw = np.empty(iomoi__ssbie, dt64_dtype)
                lwcb__yrrk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ifx__wein)
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    kor__vxoqo = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(wvv__vdwlm[avbf__lpll]))
                    untl__jkjrj = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(cba__vihmb[avbf__lpll]))
                    if kor__vxoqo == lwcb__yrrk or untl__jkjrj == lwcb__yrrk:
                        heoj__ssj = lwcb__yrrk
                    else:
                        heoj__ssj = op(kor__vxoqo, untl__jkjrj)
                    sxylj__hnnw[avbf__lpll
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        heoj__ssj)
                return bodo.hiframes.pd_series_ext.init_series(sxylj__hnnw,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
            ) and bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs):
            ifx__wein = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                frox__psu = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                wvv__vdwlm = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    frox__psu)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                cba__vihmb = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                iomoi__ssbie = len(wvv__vdwlm)
                sxylj__hnnw = np.empty(iomoi__ssbie, dt64_dtype)
                lwcb__yrrk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ifx__wein)
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    kor__vxoqo = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(wvv__vdwlm[avbf__lpll]))
                    untl__jkjrj = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(cba__vihmb[avbf__lpll]))
                    if kor__vxoqo == lwcb__yrrk or untl__jkjrj == lwcb__yrrk:
                        heoj__ssj = lwcb__yrrk
                    else:
                        heoj__ssj = op(kor__vxoqo, untl__jkjrj)
                    sxylj__hnnw[avbf__lpll
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        heoj__ssj)
                return bodo.hiframes.pd_series_ext.init_series(sxylj__hnnw,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            ifx__wein = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                frox__psu = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                wvv__vdwlm = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    frox__psu)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                iomoi__ssbie = len(wvv__vdwlm)
                sxylj__hnnw = np.empty(iomoi__ssbie, timedelta64_dtype)
                lwcb__yrrk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ifx__wein)
                mur__arle = rhs.value
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    kor__vxoqo = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(wvv__vdwlm[avbf__lpll]))
                    if kor__vxoqo == lwcb__yrrk or mur__arle == lwcb__yrrk:
                        heoj__ssj = lwcb__yrrk
                    else:
                        heoj__ssj = op(kor__vxoqo, mur__arle)
                    sxylj__hnnw[avbf__lpll
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        heoj__ssj)
                return bodo.hiframes.pd_series_ext.init_series(sxylj__hnnw,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
            ) and lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            ifx__wein = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                frox__psu = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                wvv__vdwlm = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    frox__psu)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                iomoi__ssbie = len(wvv__vdwlm)
                sxylj__hnnw = np.empty(iomoi__ssbie, timedelta64_dtype)
                lwcb__yrrk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ifx__wein)
                mur__arle = lhs.value
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    kor__vxoqo = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(wvv__vdwlm[avbf__lpll]))
                    if mur__arle == lwcb__yrrk or kor__vxoqo == lwcb__yrrk:
                        heoj__ssj = lwcb__yrrk
                    else:
                        heoj__ssj = op(mur__arle, kor__vxoqo)
                    sxylj__hnnw[avbf__lpll
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        heoj__ssj)
                return bodo.hiframes.pd_series_ext.init_series(sxylj__hnnw,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and rhs ==
            bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type):
            ifx__wein = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                frox__psu = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                wvv__vdwlm = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    frox__psu)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                iomoi__ssbie = len(wvv__vdwlm)
                sxylj__hnnw = np.empty(iomoi__ssbie, dt64_dtype)
                lwcb__yrrk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ifx__wein)
                ovyzt__amj = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                untl__jkjrj = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(ovyzt__amj))
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    kor__vxoqo = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(wvv__vdwlm[avbf__lpll]))
                    if kor__vxoqo == lwcb__yrrk or untl__jkjrj == lwcb__yrrk:
                        heoj__ssj = lwcb__yrrk
                    else:
                        heoj__ssj = op(kor__vxoqo, untl__jkjrj)
                    sxylj__hnnw[avbf__lpll
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        heoj__ssj)
                return bodo.hiframes.pd_series_ext.init_series(sxylj__hnnw,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and lhs ==
            bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type):
            ifx__wein = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                frox__psu = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                wvv__vdwlm = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    frox__psu)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                iomoi__ssbie = len(wvv__vdwlm)
                sxylj__hnnw = np.empty(iomoi__ssbie, dt64_dtype)
                lwcb__yrrk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ifx__wein)
                ovyzt__amj = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                untl__jkjrj = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(ovyzt__amj))
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    kor__vxoqo = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(wvv__vdwlm[avbf__lpll]))
                    if kor__vxoqo == lwcb__yrrk or untl__jkjrj == lwcb__yrrk:
                        heoj__ssj = lwcb__yrrk
                    else:
                        heoj__ssj = op(kor__vxoqo, untl__jkjrj)
                    sxylj__hnnw[avbf__lpll
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        heoj__ssj)
                return bodo.hiframes.pd_series_ext.init_series(sxylj__hnnw,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and rhs ==
            bodo.hiframes.datetime_datetime_ext.datetime_datetime_type):
            ifx__wein = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                frox__psu = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                wvv__vdwlm = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    frox__psu)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                iomoi__ssbie = len(wvv__vdwlm)
                sxylj__hnnw = np.empty(iomoi__ssbie, timedelta64_dtype)
                lwcb__yrrk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ifx__wein)
                fwk__mycn = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(rhs))
                kor__vxoqo = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fwk__mycn)
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    jos__fbg = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        wvv__vdwlm[avbf__lpll])
                    if jos__fbg == lwcb__yrrk or kor__vxoqo == lwcb__yrrk:
                        heoj__ssj = lwcb__yrrk
                    else:
                        heoj__ssj = op(jos__fbg, kor__vxoqo)
                    sxylj__hnnw[avbf__lpll
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        heoj__ssj)
                return bodo.hiframes.pd_series_ext.init_series(sxylj__hnnw,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and lhs ==
            bodo.hiframes.datetime_datetime_ext.datetime_datetime_type):
            ifx__wein = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                frox__psu = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                wvv__vdwlm = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    frox__psu)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                iomoi__ssbie = len(wvv__vdwlm)
                sxylj__hnnw = np.empty(iomoi__ssbie, timedelta64_dtype)
                lwcb__yrrk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ifx__wein)
                fwk__mycn = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(lhs))
                kor__vxoqo = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    fwk__mycn)
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    jos__fbg = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        wvv__vdwlm[avbf__lpll])
                    if kor__vxoqo == lwcb__yrrk or jos__fbg == lwcb__yrrk:
                        heoj__ssj = lwcb__yrrk
                    else:
                        heoj__ssj = op(kor__vxoqo, jos__fbg)
                    sxylj__hnnw[avbf__lpll
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        heoj__ssj)
                return bodo.hiframes.pd_series_ext.init_series(sxylj__hnnw,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs) and 
            rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            ifx__wein = lhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                wvv__vdwlm = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                iomoi__ssbie = len(wvv__vdwlm)
                sxylj__hnnw = np.empty(iomoi__ssbie, timedelta64_dtype)
                lwcb__yrrk = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(ifx__wein))
                ovyzt__amj = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                untl__jkjrj = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(ovyzt__amj))
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    lgo__yduph = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(wvv__vdwlm[avbf__lpll]))
                    if untl__jkjrj == lwcb__yrrk or lgo__yduph == lwcb__yrrk:
                        heoj__ssj = lwcb__yrrk
                    else:
                        heoj__ssj = op(lgo__yduph, untl__jkjrj)
                    sxylj__hnnw[avbf__lpll
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        heoj__ssj)
                return bodo.hiframes.pd_series_ext.init_series(sxylj__hnnw,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs) and 
            lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            ifx__wein = rhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                wvv__vdwlm = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                iomoi__ssbie = len(wvv__vdwlm)
                sxylj__hnnw = np.empty(iomoi__ssbie, timedelta64_dtype)
                lwcb__yrrk = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(ifx__wein))
                ovyzt__amj = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                untl__jkjrj = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(ovyzt__amj))
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    lgo__yduph = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(wvv__vdwlm[avbf__lpll]))
                    if untl__jkjrj == lwcb__yrrk or lgo__yduph == lwcb__yrrk:
                        heoj__ssj = lwcb__yrrk
                    else:
                        heoj__ssj = op(untl__jkjrj, lgo__yduph)
                    sxylj__hnnw[avbf__lpll
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        heoj__ssj)
                return bodo.hiframes.pd_series_ext.init_series(sxylj__hnnw,
                    bgjf__cfh, yyfty__hxp)
            return impl
        raise BodoError(f'{op} not supported for data types {lhs} and {rhs}.')
    return overload_series_dt_binop


def create_cmp_op_overload(op):

    def overload_series_dt64_cmp(lhs, rhs):
        if op == operator.ne:
            votly__kex = True
        else:
            votly__kex = False
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs) and 
            rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            ifx__wein = lhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                wvv__vdwlm = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                iomoi__ssbie = len(wvv__vdwlm)
                nxw__dbo = bodo.libs.bool_arr_ext.alloc_bool_array(iomoi__ssbie
                    )
                lwcb__yrrk = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(ifx__wein))
                uuqa__fmlgm = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                fkqb__krb = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(uuqa__fmlgm))
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    ugdiz__gxj = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(wvv__vdwlm[avbf__lpll]))
                    if ugdiz__gxj == lwcb__yrrk or fkqb__krb == lwcb__yrrk:
                        heoj__ssj = votly__kex
                    else:
                        heoj__ssj = op(ugdiz__gxj, fkqb__krb)
                    nxw__dbo[avbf__lpll] = heoj__ssj
                return bodo.hiframes.pd_series_ext.init_series(nxw__dbo,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs) and 
            lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            ifx__wein = rhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                wvv__vdwlm = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                iomoi__ssbie = len(wvv__vdwlm)
                nxw__dbo = bodo.libs.bool_arr_ext.alloc_bool_array(iomoi__ssbie
                    )
                lwcb__yrrk = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(ifx__wein))
                cfh__clpyt = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                ugdiz__gxj = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(cfh__clpyt))
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    fkqb__krb = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(wvv__vdwlm[avbf__lpll]))
                    if ugdiz__gxj == lwcb__yrrk or fkqb__krb == lwcb__yrrk:
                        heoj__ssj = votly__kex
                    else:
                        heoj__ssj = op(ugdiz__gxj, fkqb__krb)
                    nxw__dbo[avbf__lpll] = heoj__ssj
                return bodo.hiframes.pd_series_ext.init_series(nxw__dbo,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            ifx__wein = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                frox__psu = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                wvv__vdwlm = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    frox__psu)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                iomoi__ssbie = len(wvv__vdwlm)
                nxw__dbo = bodo.libs.bool_arr_ext.alloc_bool_array(iomoi__ssbie
                    )
                lwcb__yrrk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ifx__wein)
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    ugdiz__gxj = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(wvv__vdwlm[avbf__lpll]))
                    if ugdiz__gxj == lwcb__yrrk or rhs.value == lwcb__yrrk:
                        heoj__ssj = votly__kex
                    else:
                        heoj__ssj = op(ugdiz__gxj, rhs.value)
                    nxw__dbo[avbf__lpll] = heoj__ssj
                return bodo.hiframes.pd_series_ext.init_series(nxw__dbo,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if (lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type and
            bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs)):
            ifx__wein = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                frox__psu = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                wvv__vdwlm = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    frox__psu)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                iomoi__ssbie = len(wvv__vdwlm)
                nxw__dbo = bodo.libs.bool_arr_ext.alloc_bool_array(iomoi__ssbie
                    )
                lwcb__yrrk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ifx__wein)
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    fkqb__krb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        wvv__vdwlm[avbf__lpll])
                    if fkqb__krb == lwcb__yrrk or lhs.value == lwcb__yrrk:
                        heoj__ssj = votly__kex
                    else:
                        heoj__ssj = op(lhs.value, fkqb__krb)
                    nxw__dbo[avbf__lpll] = heoj__ssj
                return bodo.hiframes.pd_series_ext.init_series(nxw__dbo,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and (rhs ==
            bodo.libs.str_ext.string_type or bodo.utils.typing.
            is_overload_constant_str(rhs)):
            ifx__wein = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                frox__psu = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                wvv__vdwlm = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    frox__psu)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                numba.parfors.parfor.init_prange()
                iomoi__ssbie = len(wvv__vdwlm)
                nxw__dbo = bodo.libs.bool_arr_ext.alloc_bool_array(iomoi__ssbie
                    )
                lwcb__yrrk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ifx__wein)
                dwr__lwzlt = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(
                    rhs)
                cfcy__adb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    dwr__lwzlt)
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    ugdiz__gxj = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(wvv__vdwlm[avbf__lpll]))
                    if ugdiz__gxj == lwcb__yrrk or cfcy__adb == lwcb__yrrk:
                        heoj__ssj = votly__kex
                    else:
                        heoj__ssj = op(ugdiz__gxj, cfcy__adb)
                    nxw__dbo[avbf__lpll] = heoj__ssj
                return bodo.hiframes.pd_series_ext.init_series(nxw__dbo,
                    bgjf__cfh, yyfty__hxp)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and (lhs ==
            bodo.libs.str_ext.string_type or bodo.utils.typing.
            is_overload_constant_str(lhs)):
            ifx__wein = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                frox__psu = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                wvv__vdwlm = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    frox__psu)
                bgjf__cfh = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                yyfty__hxp = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                numba.parfors.parfor.init_prange()
                iomoi__ssbie = len(wvv__vdwlm)
                nxw__dbo = bodo.libs.bool_arr_ext.alloc_bool_array(iomoi__ssbie
                    )
                lwcb__yrrk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ifx__wein)
                dwr__lwzlt = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(
                    lhs)
                cfcy__adb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    dwr__lwzlt)
                for avbf__lpll in numba.parfors.parfor.internal_prange(
                    iomoi__ssbie):
                    fwk__mycn = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        wvv__vdwlm[avbf__lpll])
                    if fwk__mycn == lwcb__yrrk or cfcy__adb == lwcb__yrrk:
                        heoj__ssj = votly__kex
                    else:
                        heoj__ssj = op(cfcy__adb, fwk__mycn)
                    nxw__dbo[avbf__lpll] = heoj__ssj
                return bodo.hiframes.pd_series_ext.init_series(nxw__dbo,
                    bgjf__cfh, yyfty__hxp)
            return impl
        raise BodoError(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_series_dt64_cmp


series_dt_unsupported_methods = {'to_period', 'to_pydatetime',
    'tz_localize', 'asfreq', 'to_timestamp'}
series_dt_unsupported_attrs = {'time', 'timetz', 'tz', 'freq', 'qyear',
    'start_time', 'end_time'}


def _install_series_dt_unsupported():
    for trbsm__ize in series_dt_unsupported_attrs:
        oycmy__euf = 'Series.dt.' + trbsm__ize
        overload_attribute(SeriesDatetimePropertiesType, trbsm__ize)(
            create_unsupported_overload(oycmy__euf))
    for kzimm__uys in series_dt_unsupported_methods:
        oycmy__euf = 'Series.dt.' + kzimm__uys
        overload_method(SeriesDatetimePropertiesType, kzimm__uys,
            no_unliteral=True)(create_unsupported_overload(oycmy__euf))


_install_series_dt_unsupported()
