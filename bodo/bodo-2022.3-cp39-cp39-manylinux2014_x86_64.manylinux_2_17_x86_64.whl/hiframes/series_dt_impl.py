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
        jxk__xswy = 'SeriesDatetimePropertiesType({})'.format(stype)
        super(SeriesDatetimePropertiesType, self).__init__(jxk__xswy)


@register_model(SeriesDatetimePropertiesType)
class SeriesDtModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        xydj__pvfvx = [('obj', fe_type.stype)]
        super(SeriesDtModel, self).__init__(dmm, fe_type, xydj__pvfvx)


make_attribute_wrapper(SeriesDatetimePropertiesType, 'obj', '_obj')


@intrinsic
def init_series_dt_properties(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        czgwd__bjiiy, = args
        ynpx__nsci = signature.return_type
        nhok__bvp = cgutils.create_struct_proxy(ynpx__nsci)(context, builder)
        nhok__bvp.obj = czgwd__bjiiy
        context.nrt.incref(builder, signature.args[0], czgwd__bjiiy)
        return nhok__bvp._getvalue()
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
        cvwhz__sps = 'def impl(S_dt):\n'
        cvwhz__sps += '    S = S_dt._obj\n'
        cvwhz__sps += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        cvwhz__sps += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        cvwhz__sps += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        cvwhz__sps += '    numba.parfors.parfor.init_prange()\n'
        cvwhz__sps += '    n = len(arr)\n'
        if field in ('is_leap_year', 'is_month_start', 'is_month_end',
            'is_quarter_start', 'is_quarter_end', 'is_year_start',
            'is_year_end'):
            cvwhz__sps += '    out_arr = np.empty(n, np.bool_)\n'
        else:
            cvwhz__sps += (
                '    out_arr = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n'
                )
        cvwhz__sps += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        cvwhz__sps += '        if bodo.libs.array_kernels.isna(arr, i):\n'
        cvwhz__sps += '            bodo.libs.array_kernels.setna(out_arr, i)\n'
        cvwhz__sps += '            continue\n'
        cvwhz__sps += (
            '        dt64 = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(arr[i])\n'
            )
        if field in ('year', 'month', 'day'):
            cvwhz__sps += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            if field in ('month', 'day'):
                cvwhz__sps += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            cvwhz__sps += '        out_arr[i] = {}\n'.format(field)
        elif field in ('dayofyear', 'day_of_year', 'dayofweek',
            'day_of_week', 'weekday'):
            mbg__bbiaj = {'dayofyear': 'get_day_of_year', 'day_of_year':
                'get_day_of_year', 'dayofweek': 'get_day_of_week',
                'day_of_week': 'get_day_of_week', 'weekday': 'get_day_of_week'}
            cvwhz__sps += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            cvwhz__sps += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            cvwhz__sps += (
                """        out_arr[i] = bodo.hiframes.pd_timestamp_ext.{}(year, month, day)
"""
                .format(mbg__bbiaj[field]))
        elif field == 'is_leap_year':
            cvwhz__sps += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            cvwhz__sps += """        out_arr[i] = bodo.hiframes.pd_timestamp_ext.is_leap_year(year)
"""
        elif field in ('daysinmonth', 'days_in_month'):
            mbg__bbiaj = {'days_in_month': 'get_days_in_month',
                'daysinmonth': 'get_days_in_month'}
            cvwhz__sps += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            cvwhz__sps += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            cvwhz__sps += (
                '        out_arr[i] = bodo.hiframes.pd_timestamp_ext.{}(year, month)\n'
                .format(mbg__bbiaj[field]))
        else:
            cvwhz__sps += """        ts = bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp(dt64)
"""
            cvwhz__sps += '        out_arr[i] = ts.' + field + '\n'
        cvwhz__sps += (
            '    return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        arer__pnw = {}
        exec(cvwhz__sps, {'bodo': bodo, 'numba': numba, 'np': np}, arer__pnw)
        impl = arer__pnw['impl']
        return impl
    return overload_field


def _install_date_fields():
    for field in bodo.hiframes.pd_timestamp_ext.date_fields:
        zijd__khvah = create_date_field_overload(field)
        overload_attribute(SeriesDatetimePropertiesType, field)(zijd__khvah)


_install_date_fields()


def create_date_method_overload(method):
    vhg__xzuf = method in ['day_name', 'month_name']
    if vhg__xzuf:
        cvwhz__sps = 'def overload_method(S_dt, locale=None):\n'
        cvwhz__sps += '    unsupported_args = dict(locale=locale)\n'
        cvwhz__sps += '    arg_defaults = dict(locale=None)\n'
        cvwhz__sps += '    bodo.utils.typing.check_unsupported_args(\n'
        cvwhz__sps += f"        'Series.dt.{method}',\n"
        cvwhz__sps += '        unsupported_args,\n'
        cvwhz__sps += '        arg_defaults,\n'
        cvwhz__sps += "        package_name='pandas',\n"
        cvwhz__sps += "        module_name='Series',\n"
        cvwhz__sps += '    )\n'
    else:
        cvwhz__sps = 'def overload_method(S_dt):\n'
        cvwhz__sps += f"""    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S_dt, 'Series.dt.{method}()')
"""
    cvwhz__sps += """    if not (S_dt.stype.dtype == bodo.datetime64ns or isinstance(S_dt.stype.dtype, bodo.libs.pd_datetime_arr_ext.PandasDatetimeTZDtype)):
"""
    cvwhz__sps += '        return\n'
    if vhg__xzuf:
        cvwhz__sps += '    def impl(S_dt, locale=None):\n'
    else:
        cvwhz__sps += '    def impl(S_dt):\n'
    cvwhz__sps += '        S = S_dt._obj\n'
    cvwhz__sps += (
        '        arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    cvwhz__sps += (
        '        index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
    cvwhz__sps += (
        '        name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
    cvwhz__sps += '        numba.parfors.parfor.init_prange()\n'
    cvwhz__sps += '        n = len(arr)\n'
    if vhg__xzuf:
        cvwhz__sps += """        out_arr = bodo.utils.utils.alloc_type(n, bodo.string_array_type, (-1,))
"""
    else:
        cvwhz__sps += (
            "        out_arr = np.empty(n, np.dtype('datetime64[ns]'))\n")
    cvwhz__sps += '        for i in numba.parfors.parfor.internal_prange(n):\n'
    cvwhz__sps += '            if bodo.libs.array_kernels.isna(arr, i):\n'
    cvwhz__sps += '                bodo.libs.array_kernels.setna(out_arr, i)\n'
    cvwhz__sps += '                continue\n'
    cvwhz__sps += (
        '            ts = bodo.utils.conversion.box_if_dt64(arr[i])\n')
    cvwhz__sps += f'            method_val = ts.{method}()\n'
    if vhg__xzuf:
        cvwhz__sps += '            out_arr[i] = method_val\n'
    else:
        cvwhz__sps += """            out_arr[i] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(method_val.value)
"""
    cvwhz__sps += (
        '        return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    cvwhz__sps += '    return impl\n'
    arer__pnw = {}
    exec(cvwhz__sps, {'bodo': bodo, 'numba': numba, 'np': np}, arer__pnw)
    overload_method = arer__pnw['overload_method']
    return overload_method


def _install_date_methods():
    for method in bodo.hiframes.pd_timestamp_ext.date_methods:
        zijd__khvah = create_date_method_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            zijd__khvah)


_install_date_methods()


@overload_attribute(SeriesDatetimePropertiesType, 'date')
def series_dt_date_overload(S_dt):
    if not (S_dt.stype.dtype == types.NPDatetime('ns') or isinstance(S_dt.
        stype.dtype, bodo.libs.pd_datetime_arr_ext.PandasDatetimeTZDtype)):
        return

    def impl(S_dt):
        gvwfm__brq = S_dt._obj
        msopt__odgqx = bodo.hiframes.pd_series_ext.get_series_data(gvwfm__brq)
        mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(gvwfm__brq)
        jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(gvwfm__brq)
        numba.parfors.parfor.init_prange()
        kznp__kyao = len(msopt__odgqx)
        jxy__bgtky = bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(
            kznp__kyao)
        for rytnz__yqj in numba.parfors.parfor.internal_prange(kznp__kyao):
            qhdk__frqam = msopt__odgqx[rytnz__yqj]
            okg__spr = bodo.utils.conversion.box_if_dt64(qhdk__frqam)
            jxy__bgtky[rytnz__yqj] = datetime.date(okg__spr.year, okg__spr.
                month, okg__spr.day)
        return bodo.hiframes.pd_series_ext.init_series(jxy__bgtky,
            mdrgw__siefj, jxk__xswy)
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
            umayr__uwuvn = ['days', 'hours', 'minutes', 'seconds',
                'milliseconds', 'microseconds', 'nanoseconds']
            uem__nqdt = 'convert_numpy_timedelta64_to_pd_timedelta'
            qhtr__fnag = 'np.empty(n, np.int64)'
            hssum__jffn = attr
        elif attr == 'isocalendar':
            umayr__uwuvn = ['year', 'week', 'day']
            uem__nqdt = 'convert_datetime64_to_timestamp'
            qhtr__fnag = 'bodo.libs.int_arr_ext.alloc_int_array(n, np.uint32)'
            hssum__jffn = attr + '()'
        cvwhz__sps = 'def impl(S_dt):\n'
        cvwhz__sps += '    S = S_dt._obj\n'
        cvwhz__sps += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        cvwhz__sps += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        cvwhz__sps += '    numba.parfors.parfor.init_prange()\n'
        cvwhz__sps += '    n = len(arr)\n'
        for field in umayr__uwuvn:
            cvwhz__sps += '    {} = {}\n'.format(field, qhtr__fnag)
        cvwhz__sps += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        cvwhz__sps += '        if bodo.libs.array_kernels.isna(arr, i):\n'
        for field in umayr__uwuvn:
            cvwhz__sps += ('            bodo.libs.array_kernels.setna({}, i)\n'
                .format(field))
        cvwhz__sps += '            continue\n'
        uszdz__gxo = '(' + '[i], '.join(umayr__uwuvn) + '[i])'
        cvwhz__sps += (
            '        {} = bodo.hiframes.pd_timestamp_ext.{}(arr[i]).{}\n'.
            format(uszdz__gxo, uem__nqdt, hssum__jffn))
        iuola__dlu = '(' + ', '.join(umayr__uwuvn) + ')'
        crku__cejxf = "('" + "', '".join(umayr__uwuvn) + "')"
        cvwhz__sps += (
            '    return bodo.hiframes.pd_dataframe_ext.init_dataframe({}, index, {})\n'
            .format(iuola__dlu, crku__cejxf))
        arer__pnw = {}
        exec(cvwhz__sps, {'bodo': bodo, 'numba': numba, 'np': np}, arer__pnw)
        impl = arer__pnw['impl']
        return impl
    return series_dt_df_output_overload


def _install_df_output_overload():
    qrce__mbjoy = [('components', overload_attribute), ('isocalendar',
        overload_method)]
    for attr, gbzf__wng in qrce__mbjoy:
        zijd__khvah = create_series_dt_df_output_overload(attr)
        gbzf__wng(SeriesDatetimePropertiesType, attr, inline='always')(
            zijd__khvah)


_install_df_output_overload()


def create_timedelta_field_overload(field):

    def overload_field(S_dt):
        if not S_dt.stype.dtype == types.NPTimedelta('ns'):
            return
        cvwhz__sps = 'def impl(S_dt):\n'
        cvwhz__sps += '    S = S_dt._obj\n'
        cvwhz__sps += (
            '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        cvwhz__sps += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        cvwhz__sps += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        cvwhz__sps += '    numba.parfors.parfor.init_prange()\n'
        cvwhz__sps += '    n = len(A)\n'
        cvwhz__sps += (
            '    B = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n')
        cvwhz__sps += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        cvwhz__sps += '        if bodo.libs.array_kernels.isna(A, i):\n'
        cvwhz__sps += '            bodo.libs.array_kernels.setna(B, i)\n'
        cvwhz__sps += '            continue\n'
        cvwhz__sps += """        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])
"""
        if field == 'nanoseconds':
            cvwhz__sps += '        B[i] = td64 % 1000\n'
        elif field == 'microseconds':
            cvwhz__sps += '        B[i] = td64 // 1000 % 1000000\n'
        elif field == 'seconds':
            cvwhz__sps += (
                '        B[i] = td64 // (1000 * 1000000) % (60 * 60 * 24)\n')
        elif field == 'days':
            cvwhz__sps += (
                '        B[i] = td64 // (1000 * 1000000 * 60 * 60 * 24)\n')
        else:
            assert False, 'invalid timedelta field'
        cvwhz__sps += (
            '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
            )
        arer__pnw = {}
        exec(cvwhz__sps, {'numba': numba, 'np': np, 'bodo': bodo}, arer__pnw)
        impl = arer__pnw['impl']
        return impl
    return overload_field


def create_timedelta_method_overload(method):

    def overload_method(S_dt):
        if not S_dt.stype.dtype == types.NPTimedelta('ns'):
            return
        cvwhz__sps = 'def impl(S_dt):\n'
        cvwhz__sps += '    S = S_dt._obj\n'
        cvwhz__sps += (
            '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        cvwhz__sps += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        cvwhz__sps += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        cvwhz__sps += '    numba.parfors.parfor.init_prange()\n'
        cvwhz__sps += '    n = len(A)\n'
        if method == 'total_seconds':
            cvwhz__sps += '    B = np.empty(n, np.float64)\n'
        else:
            cvwhz__sps += """    B = bodo.hiframes.datetime_timedelta_ext.alloc_datetime_timedelta_array(n)
"""
        cvwhz__sps += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        cvwhz__sps += '        if bodo.libs.array_kernels.isna(A, i):\n'
        cvwhz__sps += '            bodo.libs.array_kernels.setna(B, i)\n'
        cvwhz__sps += '            continue\n'
        cvwhz__sps += """        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])
"""
        if method == 'total_seconds':
            cvwhz__sps += '        B[i] = td64 / (1000.0 * 1000000.0)\n'
        elif method == 'to_pytimedelta':
            cvwhz__sps += (
                '        B[i] = datetime.timedelta(microseconds=td64 // 1000)\n'
                )
        else:
            assert False, 'invalid timedelta method'
        if method == 'total_seconds':
            cvwhz__sps += (
                '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
                )
        else:
            cvwhz__sps += '    return B\n'
        arer__pnw = {}
        exec(cvwhz__sps, {'numba': numba, 'np': np, 'bodo': bodo,
            'datetime': datetime}, arer__pnw)
        impl = arer__pnw['impl']
        return impl
    return overload_method


def _install_S_dt_timedelta_fields():
    for field in bodo.hiframes.pd_timestamp_ext.timedelta_fields:
        zijd__khvah = create_timedelta_field_overload(field)
        overload_attribute(SeriesDatetimePropertiesType, field)(zijd__khvah)


_install_S_dt_timedelta_fields()


def _install_S_dt_timedelta_methods():
    for method in bodo.hiframes.pd_timestamp_ext.timedelta_methods:
        zijd__khvah = create_timedelta_method_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            zijd__khvah)


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
        gvwfm__brq = S_dt._obj
        ibtw__xri = bodo.hiframes.pd_series_ext.get_series_data(gvwfm__brq)
        mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(gvwfm__brq)
        jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(gvwfm__brq)
        numba.parfors.parfor.init_prange()
        kznp__kyao = len(ibtw__xri)
        fvcj__wqwtw = bodo.libs.str_arr_ext.pre_alloc_string_array(kznp__kyao,
            -1)
        for zzxt__dylb in numba.parfors.parfor.internal_prange(kznp__kyao):
            if bodo.libs.array_kernels.isna(ibtw__xri, zzxt__dylb):
                bodo.libs.array_kernels.setna(fvcj__wqwtw, zzxt__dylb)
                continue
            fvcj__wqwtw[zzxt__dylb] = bodo.utils.conversion.box_if_dt64(
                ibtw__xri[zzxt__dylb]).strftime(date_format)
        return bodo.hiframes.pd_series_ext.init_series(fvcj__wqwtw,
            mdrgw__siefj, jxk__xswy)
    return impl


@overload_method(SeriesDatetimePropertiesType, 'tz_convert', inline=
    'always', no_unliteral=True)
def overload_dt_tz_convert(S_dt, tz):

    def impl(S_dt, tz):
        gvwfm__brq = S_dt._obj
        gkztq__nera = get_series_data(gvwfm__brq).tz_convert(tz)
        mdrgw__siefj = get_series_index(gvwfm__brq)
        jxk__xswy = get_series_name(gvwfm__brq)
        return init_series(gkztq__nera, mdrgw__siefj, jxk__xswy)
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
        ekrv__ipfwz = dict(ambiguous=ambiguous, nonexistent=nonexistent)
        owxm__chh = dict(ambiguous='raise', nonexistent='raise')
        check_unsupported_args(f'Series.dt.{method}', ekrv__ipfwz,
            owxm__chh, package_name='pandas', module_name='Series')
        cvwhz__sps = (
            "def impl(S_dt, freq, ambiguous='raise', nonexistent='raise'):\n")
        cvwhz__sps += '    S = S_dt._obj\n'
        cvwhz__sps += (
            '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        cvwhz__sps += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        cvwhz__sps += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        cvwhz__sps += '    numba.parfors.parfor.init_prange()\n'
        cvwhz__sps += '    n = len(A)\n'
        if S_dt.stype.dtype == types.NPTimedelta('ns'):
            cvwhz__sps += "    B = np.empty(n, np.dtype('timedelta64[ns]'))\n"
        else:
            cvwhz__sps += "    B = np.empty(n, np.dtype('datetime64[ns]'))\n"
        cvwhz__sps += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        cvwhz__sps += '        if bodo.libs.array_kernels.isna(A, i):\n'
        cvwhz__sps += '            bodo.libs.array_kernels.setna(B, i)\n'
        cvwhz__sps += '            continue\n'
        if S_dt.stype.dtype == types.NPTimedelta('ns'):
            weq__wib = (
                'bodo.hiframes.pd_timestamp_ext.convert_numpy_timedelta64_to_pd_timedelta'
                )
            jnt__jbki = 'bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64'
        else:
            weq__wib = (
                'bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp'
                )
            jnt__jbki = 'bodo.hiframes.pd_timestamp_ext.integer_to_dt64'
        cvwhz__sps += '        B[i] = {}({}(A[i]).{}(freq).value)\n'.format(
            jnt__jbki, weq__wib, method)
        cvwhz__sps += (
            '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
            )
        arer__pnw = {}
        exec(cvwhz__sps, {'numba': numba, 'np': np, 'bodo': bodo}, arer__pnw)
        impl = arer__pnw['impl']
        return impl
    return freq_overload


def _install_S_dt_timedelta_freq_methods():
    zkahx__xvz = ['ceil', 'floor', 'round']
    for method in zkahx__xvz:
        zijd__khvah = create_timedelta_freq_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            zijd__khvah)


_install_S_dt_timedelta_freq_methods()


def create_bin_op_overload(op):

    def overload_series_dt_binop(lhs, rhs):
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs):
            pvolx__msx = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                mkjpp__wcil = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                tvna__paiz = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    mkjpp__wcil)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(lhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                mruy__tcl = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                eogb__yme = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    mruy__tcl)
                kznp__kyao = len(tvna__paiz)
                gvwfm__brq = np.empty(kznp__kyao, timedelta64_dtype)
                hts__ywb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    pvolx__msx)
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    fpljy__lyvv = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(tvna__paiz[rytnz__yqj]))
                    kke__blgbf = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(eogb__yme[rytnz__yqj]))
                    if fpljy__lyvv == hts__ywb or kke__blgbf == hts__ywb:
                        vex__dwa = hts__ywb
                    else:
                        vex__dwa = op(fpljy__lyvv, kke__blgbf)
                    gvwfm__brq[rytnz__yqj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        vex__dwa)
                return bodo.hiframes.pd_series_ext.init_series(gvwfm__brq,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs):
            pvolx__msx = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qxz__iahp = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                msopt__odgqx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qxz__iahp)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(lhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                eogb__yme = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                kznp__kyao = len(msopt__odgqx)
                gvwfm__brq = np.empty(kznp__kyao, dt64_dtype)
                hts__ywb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    pvolx__msx)
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    mci__vuwqj = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(msopt__odgqx[rytnz__yqj]))
                    tmp__uvxd = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(eogb__yme[rytnz__yqj]))
                    if mci__vuwqj == hts__ywb or tmp__uvxd == hts__ywb:
                        vex__dwa = hts__ywb
                    else:
                        vex__dwa = op(mci__vuwqj, tmp__uvxd)
                    gvwfm__brq[rytnz__yqj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        vex__dwa)
                return bodo.hiframes.pd_series_ext.init_series(gvwfm__brq,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
            ) and bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs):
            pvolx__msx = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qxz__iahp = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                msopt__odgqx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qxz__iahp)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(rhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                eogb__yme = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                kznp__kyao = len(msopt__odgqx)
                gvwfm__brq = np.empty(kznp__kyao, dt64_dtype)
                hts__ywb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    pvolx__msx)
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    mci__vuwqj = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(msopt__odgqx[rytnz__yqj]))
                    tmp__uvxd = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(eogb__yme[rytnz__yqj]))
                    if mci__vuwqj == hts__ywb or tmp__uvxd == hts__ywb:
                        vex__dwa = hts__ywb
                    else:
                        vex__dwa = op(mci__vuwqj, tmp__uvxd)
                    gvwfm__brq[rytnz__yqj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        vex__dwa)
                return bodo.hiframes.pd_series_ext.init_series(gvwfm__brq,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            pvolx__msx = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qxz__iahp = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                msopt__odgqx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qxz__iahp)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(lhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                kznp__kyao = len(msopt__odgqx)
                gvwfm__brq = np.empty(kznp__kyao, timedelta64_dtype)
                hts__ywb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    pvolx__msx)
                qosj__ialfz = rhs.value
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    mci__vuwqj = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if mci__vuwqj == hts__ywb or qosj__ialfz == hts__ywb:
                        vex__dwa = hts__ywb
                    else:
                        vex__dwa = op(mci__vuwqj, qosj__ialfz)
                    gvwfm__brq[rytnz__yqj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        vex__dwa)
                return bodo.hiframes.pd_series_ext.init_series(gvwfm__brq,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
            ) and lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            pvolx__msx = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qxz__iahp = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                msopt__odgqx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qxz__iahp)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(rhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                kznp__kyao = len(msopt__odgqx)
                gvwfm__brq = np.empty(kznp__kyao, timedelta64_dtype)
                hts__ywb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    pvolx__msx)
                qosj__ialfz = lhs.value
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    mci__vuwqj = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if qosj__ialfz == hts__ywb or mci__vuwqj == hts__ywb:
                        vex__dwa = hts__ywb
                    else:
                        vex__dwa = op(qosj__ialfz, mci__vuwqj)
                    gvwfm__brq[rytnz__yqj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        vex__dwa)
                return bodo.hiframes.pd_series_ext.init_series(gvwfm__brq,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and rhs ==
            bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type):
            pvolx__msx = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qxz__iahp = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                msopt__odgqx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qxz__iahp)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(lhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                kznp__kyao = len(msopt__odgqx)
                gvwfm__brq = np.empty(kznp__kyao, dt64_dtype)
                hts__ywb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    pvolx__msx)
                xlfmn__edys = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                tmp__uvxd = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(xlfmn__edys))
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    mci__vuwqj = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if mci__vuwqj == hts__ywb or tmp__uvxd == hts__ywb:
                        vex__dwa = hts__ywb
                    else:
                        vex__dwa = op(mci__vuwqj, tmp__uvxd)
                    gvwfm__brq[rytnz__yqj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        vex__dwa)
                return bodo.hiframes.pd_series_ext.init_series(gvwfm__brq,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and lhs ==
            bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type):
            pvolx__msx = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qxz__iahp = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                msopt__odgqx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qxz__iahp)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(rhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                kznp__kyao = len(msopt__odgqx)
                gvwfm__brq = np.empty(kznp__kyao, dt64_dtype)
                hts__ywb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    pvolx__msx)
                xlfmn__edys = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                tmp__uvxd = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(xlfmn__edys))
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    mci__vuwqj = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if mci__vuwqj == hts__ywb or tmp__uvxd == hts__ywb:
                        vex__dwa = hts__ywb
                    else:
                        vex__dwa = op(mci__vuwqj, tmp__uvxd)
                    gvwfm__brq[rytnz__yqj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        vex__dwa)
                return bodo.hiframes.pd_series_ext.init_series(gvwfm__brq,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and rhs ==
            bodo.hiframes.datetime_datetime_ext.datetime_datetime_type):
            pvolx__msx = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qxz__iahp = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                msopt__odgqx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qxz__iahp)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(lhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                kznp__kyao = len(msopt__odgqx)
                gvwfm__brq = np.empty(kznp__kyao, timedelta64_dtype)
                hts__ywb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    pvolx__msx)
                spzq__tlmq = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(rhs))
                mci__vuwqj = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    spzq__tlmq)
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    xgkkp__vmp = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if xgkkp__vmp == hts__ywb or mci__vuwqj == hts__ywb:
                        vex__dwa = hts__ywb
                    else:
                        vex__dwa = op(xgkkp__vmp, mci__vuwqj)
                    gvwfm__brq[rytnz__yqj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        vex__dwa)
                return bodo.hiframes.pd_series_ext.init_series(gvwfm__brq,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and lhs ==
            bodo.hiframes.datetime_datetime_ext.datetime_datetime_type):
            pvolx__msx = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qxz__iahp = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                msopt__odgqx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qxz__iahp)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(rhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                kznp__kyao = len(msopt__odgqx)
                gvwfm__brq = np.empty(kznp__kyao, timedelta64_dtype)
                hts__ywb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    pvolx__msx)
                spzq__tlmq = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(lhs))
                mci__vuwqj = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    spzq__tlmq)
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    xgkkp__vmp = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if mci__vuwqj == hts__ywb or xgkkp__vmp == hts__ywb:
                        vex__dwa = hts__ywb
                    else:
                        vex__dwa = op(mci__vuwqj, xgkkp__vmp)
                    gvwfm__brq[rytnz__yqj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        vex__dwa)
                return bodo.hiframes.pd_series_ext.init_series(gvwfm__brq,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs) and 
            rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            pvolx__msx = lhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                msopt__odgqx = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(lhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                kznp__kyao = len(msopt__odgqx)
                gvwfm__brq = np.empty(kznp__kyao, timedelta64_dtype)
                hts__ywb = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(pvolx__msx))
                xlfmn__edys = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                tmp__uvxd = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(xlfmn__edys))
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    vistb__jkvm = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if tmp__uvxd == hts__ywb or vistb__jkvm == hts__ywb:
                        vex__dwa = hts__ywb
                    else:
                        vex__dwa = op(vistb__jkvm, tmp__uvxd)
                    gvwfm__brq[rytnz__yqj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        vex__dwa)
                return bodo.hiframes.pd_series_ext.init_series(gvwfm__brq,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs) and 
            lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            pvolx__msx = rhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                msopt__odgqx = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(rhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                kznp__kyao = len(msopt__odgqx)
                gvwfm__brq = np.empty(kznp__kyao, timedelta64_dtype)
                hts__ywb = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(pvolx__msx))
                xlfmn__edys = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                tmp__uvxd = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(xlfmn__edys))
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    vistb__jkvm = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if tmp__uvxd == hts__ywb or vistb__jkvm == hts__ywb:
                        vex__dwa = hts__ywb
                    else:
                        vex__dwa = op(tmp__uvxd, vistb__jkvm)
                    gvwfm__brq[rytnz__yqj
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        vex__dwa)
                return bodo.hiframes.pd_series_ext.init_series(gvwfm__brq,
                    mdrgw__siefj, jxk__xswy)
            return impl
        raise BodoError(f'{op} not supported for data types {lhs} and {rhs}.')
    return overload_series_dt_binop


def create_cmp_op_overload(op):

    def overload_series_dt64_cmp(lhs, rhs):
        if op == operator.ne:
            uao__bukqe = True
        else:
            uao__bukqe = False
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs) and 
            rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            pvolx__msx = lhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                msopt__odgqx = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(lhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                kznp__kyao = len(msopt__odgqx)
                jxy__bgtky = bodo.libs.bool_arr_ext.alloc_bool_array(kznp__kyao
                    )
                hts__ywb = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(pvolx__msx))
                nav__dikv = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                amx__nrmrr = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(nav__dikv))
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    okhb__wqtvd = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if okhb__wqtvd == hts__ywb or amx__nrmrr == hts__ywb:
                        vex__dwa = uao__bukqe
                    else:
                        vex__dwa = op(okhb__wqtvd, amx__nrmrr)
                    jxy__bgtky[rytnz__yqj] = vex__dwa
                return bodo.hiframes.pd_series_ext.init_series(jxy__bgtky,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs) and 
            lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            pvolx__msx = rhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                msopt__odgqx = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(rhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                kznp__kyao = len(msopt__odgqx)
                jxy__bgtky = bodo.libs.bool_arr_ext.alloc_bool_array(kznp__kyao
                    )
                hts__ywb = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(pvolx__msx))
                rri__hajm = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                okhb__wqtvd = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(rri__hajm))
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    amx__nrmrr = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if okhb__wqtvd == hts__ywb or amx__nrmrr == hts__ywb:
                        vex__dwa = uao__bukqe
                    else:
                        vex__dwa = op(okhb__wqtvd, amx__nrmrr)
                    jxy__bgtky[rytnz__yqj] = vex__dwa
                return bodo.hiframes.pd_series_ext.init_series(jxy__bgtky,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            pvolx__msx = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qxz__iahp = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                msopt__odgqx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qxz__iahp)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(lhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                kznp__kyao = len(msopt__odgqx)
                jxy__bgtky = bodo.libs.bool_arr_ext.alloc_bool_array(kznp__kyao
                    )
                hts__ywb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    pvolx__msx)
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    okhb__wqtvd = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if okhb__wqtvd == hts__ywb or rhs.value == hts__ywb:
                        vex__dwa = uao__bukqe
                    else:
                        vex__dwa = op(okhb__wqtvd, rhs.value)
                    jxy__bgtky[rytnz__yqj] = vex__dwa
                return bodo.hiframes.pd_series_ext.init_series(jxy__bgtky,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if (lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type and
            bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs)):
            pvolx__msx = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qxz__iahp = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                msopt__odgqx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qxz__iahp)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(rhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                kznp__kyao = len(msopt__odgqx)
                jxy__bgtky = bodo.libs.bool_arr_ext.alloc_bool_array(kznp__kyao
                    )
                hts__ywb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    pvolx__msx)
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    amx__nrmrr = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if amx__nrmrr == hts__ywb or lhs.value == hts__ywb:
                        vex__dwa = uao__bukqe
                    else:
                        vex__dwa = op(lhs.value, amx__nrmrr)
                    jxy__bgtky[rytnz__yqj] = vex__dwa
                return bodo.hiframes.pd_series_ext.init_series(jxy__bgtky,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and (rhs ==
            bodo.libs.str_ext.string_type or bodo.utils.typing.
            is_overload_constant_str(rhs)):
            pvolx__msx = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                qxz__iahp = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                msopt__odgqx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qxz__iahp)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(lhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                numba.parfors.parfor.init_prange()
                kznp__kyao = len(msopt__odgqx)
                jxy__bgtky = bodo.libs.bool_arr_ext.alloc_bool_array(kznp__kyao
                    )
                hts__ywb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    pvolx__msx)
                mbtp__rvhb = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(
                    rhs)
                nlvr__bar = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    mbtp__rvhb)
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    okhb__wqtvd = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if okhb__wqtvd == hts__ywb or nlvr__bar == hts__ywb:
                        vex__dwa = uao__bukqe
                    else:
                        vex__dwa = op(okhb__wqtvd, nlvr__bar)
                    jxy__bgtky[rytnz__yqj] = vex__dwa
                return bodo.hiframes.pd_series_ext.init_series(jxy__bgtky,
                    mdrgw__siefj, jxk__xswy)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and (lhs ==
            bodo.libs.str_ext.string_type or bodo.utils.typing.
            is_overload_constant_str(lhs)):
            pvolx__msx = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                qxz__iahp = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                msopt__odgqx = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    qxz__iahp)
                mdrgw__siefj = bodo.hiframes.pd_series_ext.get_series_index(rhs
                    )
                jxk__xswy = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                numba.parfors.parfor.init_prange()
                kznp__kyao = len(msopt__odgqx)
                jxy__bgtky = bodo.libs.bool_arr_ext.alloc_bool_array(kznp__kyao
                    )
                hts__ywb = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    pvolx__msx)
                mbtp__rvhb = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(
                    lhs)
                nlvr__bar = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    mbtp__rvhb)
                for rytnz__yqj in numba.parfors.parfor.internal_prange(
                    kznp__kyao):
                    spzq__tlmq = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(msopt__odgqx[rytnz__yqj]))
                    if spzq__tlmq == hts__ywb or nlvr__bar == hts__ywb:
                        vex__dwa = uao__bukqe
                    else:
                        vex__dwa = op(nlvr__bar, spzq__tlmq)
                    jxy__bgtky[rytnz__yqj] = vex__dwa
                return bodo.hiframes.pd_series_ext.init_series(jxy__bgtky,
                    mdrgw__siefj, jxk__xswy)
            return impl
        raise BodoError(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_series_dt64_cmp


series_dt_unsupported_methods = {'to_period', 'to_pydatetime',
    'tz_localize', 'asfreq', 'to_timestamp'}
series_dt_unsupported_attrs = {'time', 'timetz', 'tz', 'freq', 'qyear',
    'start_time', 'end_time'}


def _install_series_dt_unsupported():
    for oxi__nzr in series_dt_unsupported_attrs:
        kkodq__dpohu = 'Series.dt.' + oxi__nzr
        overload_attribute(SeriesDatetimePropertiesType, oxi__nzr)(
            create_unsupported_overload(kkodq__dpohu))
    for znjs__gwhs in series_dt_unsupported_methods:
        kkodq__dpohu = 'Series.dt.' + znjs__gwhs
        overload_method(SeriesDatetimePropertiesType, znjs__gwhs,
            no_unliteral=True)(create_unsupported_overload(kkodq__dpohu))


_install_series_dt_unsupported()
