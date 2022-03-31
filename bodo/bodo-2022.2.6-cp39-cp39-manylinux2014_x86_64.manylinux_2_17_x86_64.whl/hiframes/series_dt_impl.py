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
        kcfi__qzlkg = 'SeriesDatetimePropertiesType({})'.format(stype)
        super(SeriesDatetimePropertiesType, self).__init__(kcfi__qzlkg)


@register_model(SeriesDatetimePropertiesType)
class SeriesDtModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        wnj__bhtj = [('obj', fe_type.stype)]
        super(SeriesDtModel, self).__init__(dmm, fe_type, wnj__bhtj)


make_attribute_wrapper(SeriesDatetimePropertiesType, 'obj', '_obj')


@intrinsic
def init_series_dt_properties(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        tlk__oruk, = args
        gdp__rfdcy = signature.return_type
        ihroy__lzl = cgutils.create_struct_proxy(gdp__rfdcy)(context, builder)
        ihroy__lzl.obj = tlk__oruk
        context.nrt.incref(builder, signature.args[0], tlk__oruk)
        return ihroy__lzl._getvalue()
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
        jspf__llisc = 'def impl(S_dt):\n'
        jspf__llisc += '    S = S_dt._obj\n'
        jspf__llisc += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        jspf__llisc += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        jspf__llisc += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        jspf__llisc += '    numba.parfors.parfor.init_prange()\n'
        jspf__llisc += '    n = len(arr)\n'
        if field in ('is_leap_year', 'is_month_start', 'is_month_end',
            'is_quarter_start', 'is_quarter_end', 'is_year_start',
            'is_year_end'):
            jspf__llisc += '    out_arr = np.empty(n, np.bool_)\n'
        else:
            jspf__llisc += (
                '    out_arr = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n'
                )
        jspf__llisc += (
            '    for i in numba.parfors.parfor.internal_prange(n):\n')
        jspf__llisc += '        if bodo.libs.array_kernels.isna(arr, i):\n'
        jspf__llisc += (
            '            bodo.libs.array_kernels.setna(out_arr, i)\n')
        jspf__llisc += '            continue\n'
        jspf__llisc += (
            '        dt64 = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(arr[i])\n'
            )
        if field in ('year', 'month', 'day'):
            jspf__llisc += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            if field in ('month', 'day'):
                jspf__llisc += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            jspf__llisc += '        out_arr[i] = {}\n'.format(field)
        elif field in ('dayofyear', 'day_of_year', 'dayofweek',
            'day_of_week', 'weekday'):
            lcxe__hdv = {'dayofyear': 'get_day_of_year', 'day_of_year':
                'get_day_of_year', 'dayofweek': 'get_day_of_week',
                'day_of_week': 'get_day_of_week', 'weekday': 'get_day_of_week'}
            jspf__llisc += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            jspf__llisc += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            jspf__llisc += (
                """        out_arr[i] = bodo.hiframes.pd_timestamp_ext.{}(year, month, day)
"""
                .format(lcxe__hdv[field]))
        elif field == 'is_leap_year':
            jspf__llisc += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            jspf__llisc += """        out_arr[i] = bodo.hiframes.pd_timestamp_ext.is_leap_year(year)
"""
        elif field in ('daysinmonth', 'days_in_month'):
            lcxe__hdv = {'days_in_month': 'get_days_in_month',
                'daysinmonth': 'get_days_in_month'}
            jspf__llisc += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            jspf__llisc += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            jspf__llisc += (
                '        out_arr[i] = bodo.hiframes.pd_timestamp_ext.{}(year, month)\n'
                .format(lcxe__hdv[field]))
        else:
            jspf__llisc += """        ts = bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp(dt64)
"""
            jspf__llisc += '        out_arr[i] = ts.' + field + '\n'
        jspf__llisc += (
            '    return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        upia__hkww = {}
        exec(jspf__llisc, {'bodo': bodo, 'numba': numba, 'np': np}, upia__hkww)
        impl = upia__hkww['impl']
        return impl
    return overload_field


def _install_date_fields():
    for field in bodo.hiframes.pd_timestamp_ext.date_fields:
        bpiz__vbs = create_date_field_overload(field)
        overload_attribute(SeriesDatetimePropertiesType, field)(bpiz__vbs)


_install_date_fields()


def create_date_method_overload(method):
    mjic__cdjau = method in ['day_name', 'month_name']
    if mjic__cdjau:
        jspf__llisc = 'def overload_method(S_dt, locale=None):\n'
        jspf__llisc += '    unsupported_args = dict(locale=locale)\n'
        jspf__llisc += '    arg_defaults = dict(locale=None)\n'
        jspf__llisc += '    bodo.utils.typing.check_unsupported_args(\n'
        jspf__llisc += f"        'Series.dt.{method}',\n"
        jspf__llisc += '        unsupported_args,\n'
        jspf__llisc += '        arg_defaults,\n'
        jspf__llisc += "        package_name='pandas',\n"
        jspf__llisc += "        module_name='Series',\n"
        jspf__llisc += '    )\n'
    else:
        jspf__llisc = 'def overload_method(S_dt):\n'
    jspf__llisc += '    if not S_dt.stype.dtype == bodo.datetime64ns:\n'
    jspf__llisc += '        return\n'
    if mjic__cdjau:
        jspf__llisc += '    def impl(S_dt, locale=None):\n'
    else:
        jspf__llisc += '    def impl(S_dt):\n'
    jspf__llisc += '        S = S_dt._obj\n'
    jspf__llisc += (
        '        arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    jspf__llisc += (
        '        index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
    jspf__llisc += (
        '        name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
    jspf__llisc += '        numba.parfors.parfor.init_prange()\n'
    jspf__llisc += '        n = len(arr)\n'
    if mjic__cdjau:
        jspf__llisc += """        out_arr = bodo.utils.utils.alloc_type(n, bodo.string_array_type, (-1,))
"""
    else:
        jspf__llisc += (
            "        out_arr = np.empty(n, np.dtype('datetime64[ns]'))\n")
    jspf__llisc += (
        '        for i in numba.parfors.parfor.internal_prange(n):\n')
    jspf__llisc += '            if bodo.libs.array_kernels.isna(arr, i):\n'
    jspf__llisc += (
        '                bodo.libs.array_kernels.setna(out_arr, i)\n')
    jspf__llisc += '                continue\n'
    jspf__llisc += """            ts = bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp(arr[i])
"""
    jspf__llisc += f'            method_val = ts.{method}()\n'
    if mjic__cdjau:
        jspf__llisc += '            out_arr[i] = method_val\n'
    else:
        jspf__llisc += """            out_arr[i] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(method_val.value)
"""
    jspf__llisc += (
        '        return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    jspf__llisc += '    return impl\n'
    upia__hkww = {}
    exec(jspf__llisc, {'bodo': bodo, 'numba': numba, 'np': np}, upia__hkww)
    overload_method = upia__hkww['overload_method']
    return overload_method


def _install_date_methods():
    for method in bodo.hiframes.pd_timestamp_ext.date_methods:
        bpiz__vbs = create_date_method_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            bpiz__vbs)


_install_date_methods()


@overload_attribute(SeriesDatetimePropertiesType, 'date')
def series_dt_date_overload(S_dt):
    if not S_dt.stype.dtype == types.NPDatetime('ns'):
        return

    def impl(S_dt):
        ttji__jphx = S_dt._obj
        qyo__ucdu = bodo.hiframes.pd_series_ext.get_series_data(ttji__jphx)
        mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(ttji__jphx)
        kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(ttji__jphx)
        numba.parfors.parfor.init_prange()
        gqur__ohs = len(qyo__ucdu)
        bcw__tuec = bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(
            gqur__ohs)
        for tfid__haevd in numba.parfors.parfor.internal_prange(gqur__ohs):
            emc__wlq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(qyo__ucdu
                [tfid__haevd])
            iiaxv__babsx = (bodo.hiframes.pd_timestamp_ext.
                convert_datetime64_to_timestamp(emc__wlq))
            bcw__tuec[tfid__haevd] = datetime.date(iiaxv__babsx.year,
                iiaxv__babsx.month, iiaxv__babsx.day)
        return bodo.hiframes.pd_series_ext.init_series(bcw__tuec, mkt__dckj,
            kcfi__qzlkg)
    return impl


def create_series_dt_df_output_overload(attr):

    def series_dt_df_output_overload(S_dt):
        if not (attr == 'components' and S_dt.stype.dtype == types.
            NPTimedelta('ns') or attr == 'isocalendar' and S_dt.stype.dtype ==
            types.NPDatetime('ns')):
            return
        if attr == 'components':
            lzpgn__qudnm = ['days', 'hours', 'minutes', 'seconds',
                'milliseconds', 'microseconds', 'nanoseconds']
            ykjf__kbujp = 'convert_numpy_timedelta64_to_pd_timedelta'
            qknh__elhe = 'np.empty(n, np.int64)'
            hnplr__oyjz = attr
        elif attr == 'isocalendar':
            lzpgn__qudnm = ['year', 'week', 'day']
            ykjf__kbujp = 'convert_datetime64_to_timestamp'
            qknh__elhe = 'bodo.libs.int_arr_ext.alloc_int_array(n, np.uint32)'
            hnplr__oyjz = attr + '()'
        jspf__llisc = 'def impl(S_dt):\n'
        jspf__llisc += '    S = S_dt._obj\n'
        jspf__llisc += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        jspf__llisc += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        jspf__llisc += '    numba.parfors.parfor.init_prange()\n'
        jspf__llisc += '    n = len(arr)\n'
        for field in lzpgn__qudnm:
            jspf__llisc += '    {} = {}\n'.format(field, qknh__elhe)
        jspf__llisc += (
            '    for i in numba.parfors.parfor.internal_prange(n):\n')
        jspf__llisc += '        if bodo.libs.array_kernels.isna(arr, i):\n'
        for field in lzpgn__qudnm:
            jspf__llisc += (
                '            bodo.libs.array_kernels.setna({}, i)\n'.format
                (field))
        jspf__llisc += '            continue\n'
        xnls__dsvi = '(' + '[i], '.join(lzpgn__qudnm) + '[i])'
        jspf__llisc += (
            '        {} = bodo.hiframes.pd_timestamp_ext.{}(arr[i]).{}\n'.
            format(xnls__dsvi, ykjf__kbujp, hnplr__oyjz))
        mir__ccme = '(' + ', '.join(lzpgn__qudnm) + ')'
        nkmut__edt = "('" + "', '".join(lzpgn__qudnm) + "')"
        jspf__llisc += (
            '    return bodo.hiframes.pd_dataframe_ext.init_dataframe({}, index, {})\n'
            .format(mir__ccme, nkmut__edt))
        upia__hkww = {}
        exec(jspf__llisc, {'bodo': bodo, 'numba': numba, 'np': np}, upia__hkww)
        impl = upia__hkww['impl']
        return impl
    return series_dt_df_output_overload


def _install_df_output_overload():
    mxv__nijrn = [('components', overload_attribute), ('isocalendar',
        overload_method)]
    for attr, pzz__mtfz in mxv__nijrn:
        bpiz__vbs = create_series_dt_df_output_overload(attr)
        pzz__mtfz(SeriesDatetimePropertiesType, attr, inline='always')(
            bpiz__vbs)


_install_df_output_overload()


def create_timedelta_field_overload(field):

    def overload_field(S_dt):
        if not S_dt.stype.dtype == types.NPTimedelta('ns'):
            return
        jspf__llisc = 'def impl(S_dt):\n'
        jspf__llisc += '    S = S_dt._obj\n'
        jspf__llisc += (
            '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        jspf__llisc += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        jspf__llisc += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        jspf__llisc += '    numba.parfors.parfor.init_prange()\n'
        jspf__llisc += '    n = len(A)\n'
        jspf__llisc += (
            '    B = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n')
        jspf__llisc += (
            '    for i in numba.parfors.parfor.internal_prange(n):\n')
        jspf__llisc += '        if bodo.libs.array_kernels.isna(A, i):\n'
        jspf__llisc += '            bodo.libs.array_kernels.setna(B, i)\n'
        jspf__llisc += '            continue\n'
        jspf__llisc += """        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])
"""
        if field == 'nanoseconds':
            jspf__llisc += '        B[i] = td64 % 1000\n'
        elif field == 'microseconds':
            jspf__llisc += '        B[i] = td64 // 1000 % 1000000\n'
        elif field == 'seconds':
            jspf__llisc += (
                '        B[i] = td64 // (1000 * 1000000) % (60 * 60 * 24)\n')
        elif field == 'days':
            jspf__llisc += (
                '        B[i] = td64 // (1000 * 1000000 * 60 * 60 * 24)\n')
        else:
            assert False, 'invalid timedelta field'
        jspf__llisc += (
            '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
            )
        upia__hkww = {}
        exec(jspf__llisc, {'numba': numba, 'np': np, 'bodo': bodo}, upia__hkww)
        impl = upia__hkww['impl']
        return impl
    return overload_field


def create_timedelta_method_overload(method):

    def overload_method(S_dt):
        if not S_dt.stype.dtype == types.NPTimedelta('ns'):
            return
        jspf__llisc = 'def impl(S_dt):\n'
        jspf__llisc += '    S = S_dt._obj\n'
        jspf__llisc += (
            '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        jspf__llisc += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        jspf__llisc += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        jspf__llisc += '    numba.parfors.parfor.init_prange()\n'
        jspf__llisc += '    n = len(A)\n'
        if method == 'total_seconds':
            jspf__llisc += '    B = np.empty(n, np.float64)\n'
        else:
            jspf__llisc += """    B = bodo.hiframes.datetime_timedelta_ext.alloc_datetime_timedelta_array(n)
"""
        jspf__llisc += (
            '    for i in numba.parfors.parfor.internal_prange(n):\n')
        jspf__llisc += '        if bodo.libs.array_kernels.isna(A, i):\n'
        jspf__llisc += '            bodo.libs.array_kernels.setna(B, i)\n'
        jspf__llisc += '            continue\n'
        jspf__llisc += """        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])
"""
        if method == 'total_seconds':
            jspf__llisc += '        B[i] = td64 / (1000.0 * 1000000.0)\n'
        elif method == 'to_pytimedelta':
            jspf__llisc += (
                '        B[i] = datetime.timedelta(microseconds=td64 // 1000)\n'
                )
        else:
            assert False, 'invalid timedelta method'
        if method == 'total_seconds':
            jspf__llisc += (
                '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
                )
        else:
            jspf__llisc += '    return B\n'
        upia__hkww = {}
        exec(jspf__llisc, {'numba': numba, 'np': np, 'bodo': bodo,
            'datetime': datetime}, upia__hkww)
        impl = upia__hkww['impl']
        return impl
    return overload_method


def _install_S_dt_timedelta_fields():
    for field in bodo.hiframes.pd_timestamp_ext.timedelta_fields:
        bpiz__vbs = create_timedelta_field_overload(field)
        overload_attribute(SeriesDatetimePropertiesType, field)(bpiz__vbs)


_install_S_dt_timedelta_fields()


def _install_S_dt_timedelta_methods():
    for method in bodo.hiframes.pd_timestamp_ext.timedelta_methods:
        bpiz__vbs = create_timedelta_method_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            bpiz__vbs)


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
        ttji__jphx = S_dt._obj
        izrvc__zgn = bodo.hiframes.pd_series_ext.get_series_data(ttji__jphx)
        mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(ttji__jphx)
        kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(ttji__jphx)
        numba.parfors.parfor.init_prange()
        gqur__ohs = len(izrvc__zgn)
        hctn__uewg = bodo.libs.str_arr_ext.pre_alloc_string_array(gqur__ohs, -1
            )
        for ganqd__zhzvt in numba.parfors.parfor.internal_prange(gqur__ohs):
            if bodo.libs.array_kernels.isna(izrvc__zgn, ganqd__zhzvt):
                bodo.libs.array_kernels.setna(hctn__uewg, ganqd__zhzvt)
                continue
            hctn__uewg[ganqd__zhzvt
                ] = bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp(
                izrvc__zgn[ganqd__zhzvt]).strftime(date_format)
        return bodo.hiframes.pd_series_ext.init_series(hctn__uewg,
            mkt__dckj, kcfi__qzlkg)
    return impl


@overload_method(SeriesDatetimePropertiesType, 'tz_convert', inline=
    'always', no_unliteral=True)
def overload_dt_tz_convert(S_dt, tz):

    def impl(S_dt, tz):
        ttji__jphx = S_dt._obj
        anxm__gwxk = get_series_data(ttji__jphx).tz_convert(tz)
        mkt__dckj = get_series_index(ttji__jphx)
        kcfi__qzlkg = get_series_name(ttji__jphx)
        return init_series(anxm__gwxk, mkt__dckj, kcfi__qzlkg)
    return impl


def create_timedelta_freq_overload(method):

    def freq_overload(S_dt, freq, ambiguous='raise', nonexistent='raise'):
        if S_dt.stype.dtype != types.NPTimedelta('ns'
            ) and S_dt.stype.dtype != types.NPDatetime('ns'):
            return
        lgr__qkoo = dict(ambiguous=ambiguous, nonexistent=nonexistent)
        xct__arh = dict(ambiguous='raise', nonexistent='raise')
        check_unsupported_args(f'Series.dt.{method}', lgr__qkoo, xct__arh,
            package_name='pandas', module_name='Series')
        jspf__llisc = (
            "def impl(S_dt, freq, ambiguous='raise', nonexistent='raise'):\n")
        jspf__llisc += '    S = S_dt._obj\n'
        jspf__llisc += (
            '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        jspf__llisc += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        jspf__llisc += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        jspf__llisc += '    numba.parfors.parfor.init_prange()\n'
        jspf__llisc += '    n = len(A)\n'
        if S_dt.stype.dtype == types.NPTimedelta('ns'):
            jspf__llisc += "    B = np.empty(n, np.dtype('timedelta64[ns]'))\n"
        else:
            jspf__llisc += "    B = np.empty(n, np.dtype('datetime64[ns]'))\n"
        jspf__llisc += (
            '    for i in numba.parfors.parfor.internal_prange(n):\n')
        jspf__llisc += '        if bodo.libs.array_kernels.isna(A, i):\n'
        jspf__llisc += '            bodo.libs.array_kernels.setna(B, i)\n'
        jspf__llisc += '            continue\n'
        if S_dt.stype.dtype == types.NPTimedelta('ns'):
            hko__mpjt = (
                'bodo.hiframes.pd_timestamp_ext.convert_numpy_timedelta64_to_pd_timedelta'
                )
            bsqui__zshq = (
                'bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64')
        else:
            hko__mpjt = (
                'bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp'
                )
            bsqui__zshq = 'bodo.hiframes.pd_timestamp_ext.integer_to_dt64'
        jspf__llisc += '        B[i] = {}({}(A[i]).{}(freq).value)\n'.format(
            bsqui__zshq, hko__mpjt, method)
        jspf__llisc += (
            '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
            )
        upia__hkww = {}
        exec(jspf__llisc, {'numba': numba, 'np': np, 'bodo': bodo}, upia__hkww)
        impl = upia__hkww['impl']
        return impl
    return freq_overload


def _install_S_dt_timedelta_freq_methods():
    smf__zoaqs = ['ceil', 'floor', 'round']
    for method in smf__zoaqs:
        bpiz__vbs = create_timedelta_freq_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            bpiz__vbs)


_install_S_dt_timedelta_freq_methods()


def create_bin_op_overload(op):

    def overload_series_dt_binop(lhs, rhs):
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs):
            gjzv__dfbn = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                hcuhb__utge = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                cah__yjib = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    hcuhb__utge)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                hzkr__ytgii = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                zrcg__vdcri = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    hzkr__ytgii)
                gqur__ohs = len(cah__yjib)
                ttji__jphx = np.empty(gqur__ohs, timedelta64_dtype)
                yiowb__maxf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gjzv__dfbn)
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    phacs__kqs = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(cah__yjib[tfid__haevd]))
                    pnmr__xwwsq = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(zrcg__vdcri[tfid__haevd]))
                    if phacs__kqs == yiowb__maxf or pnmr__xwwsq == yiowb__maxf:
                        zpuw__gkfms = yiowb__maxf
                    else:
                        zpuw__gkfms = op(phacs__kqs, pnmr__xwwsq)
                    ttji__jphx[tfid__haevd
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        zpuw__gkfms)
                return bodo.hiframes.pd_series_ext.init_series(ttji__jphx,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs):
            gjzv__dfbn = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gpxr__zcduj = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                qyo__ucdu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gpxr__zcduj)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                zrcg__vdcri = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                gqur__ohs = len(qyo__ucdu)
                ttji__jphx = np.empty(gqur__ohs, dt64_dtype)
                yiowb__maxf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gjzv__dfbn)
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    upd__noy = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        qyo__ucdu[tfid__haevd])
                    vqv__gycy = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(zrcg__vdcri[tfid__haevd]))
                    if upd__noy == yiowb__maxf or vqv__gycy == yiowb__maxf:
                        zpuw__gkfms = yiowb__maxf
                    else:
                        zpuw__gkfms = op(upd__noy, vqv__gycy)
                    ttji__jphx[tfid__haevd
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        zpuw__gkfms)
                return bodo.hiframes.pd_series_ext.init_series(ttji__jphx,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
            ) and bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs):
            gjzv__dfbn = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gpxr__zcduj = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                qyo__ucdu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gpxr__zcduj)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                zrcg__vdcri = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                gqur__ohs = len(qyo__ucdu)
                ttji__jphx = np.empty(gqur__ohs, dt64_dtype)
                yiowb__maxf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gjzv__dfbn)
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    upd__noy = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        qyo__ucdu[tfid__haevd])
                    vqv__gycy = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(zrcg__vdcri[tfid__haevd]))
                    if upd__noy == yiowb__maxf or vqv__gycy == yiowb__maxf:
                        zpuw__gkfms = yiowb__maxf
                    else:
                        zpuw__gkfms = op(upd__noy, vqv__gycy)
                    ttji__jphx[tfid__haevd
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        zpuw__gkfms)
                return bodo.hiframes.pd_series_ext.init_series(ttji__jphx,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            gjzv__dfbn = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gpxr__zcduj = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                qyo__ucdu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gpxr__zcduj)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                gqur__ohs = len(qyo__ucdu)
                ttji__jphx = np.empty(gqur__ohs, timedelta64_dtype)
                yiowb__maxf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gjzv__dfbn)
                jci__amklg = rhs.value
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    upd__noy = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        qyo__ucdu[tfid__haevd])
                    if upd__noy == yiowb__maxf or jci__amklg == yiowb__maxf:
                        zpuw__gkfms = yiowb__maxf
                    else:
                        zpuw__gkfms = op(upd__noy, jci__amklg)
                    ttji__jphx[tfid__haevd
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        zpuw__gkfms)
                return bodo.hiframes.pd_series_ext.init_series(ttji__jphx,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
            ) and lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            gjzv__dfbn = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gpxr__zcduj = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                qyo__ucdu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gpxr__zcduj)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                gqur__ohs = len(qyo__ucdu)
                ttji__jphx = np.empty(gqur__ohs, timedelta64_dtype)
                yiowb__maxf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gjzv__dfbn)
                jci__amklg = lhs.value
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    upd__noy = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        qyo__ucdu[tfid__haevd])
                    if jci__amklg == yiowb__maxf or upd__noy == yiowb__maxf:
                        zpuw__gkfms = yiowb__maxf
                    else:
                        zpuw__gkfms = op(jci__amklg, upd__noy)
                    ttji__jphx[tfid__haevd
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        zpuw__gkfms)
                return bodo.hiframes.pd_series_ext.init_series(ttji__jphx,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and rhs ==
            bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type):
            gjzv__dfbn = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gpxr__zcduj = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                qyo__ucdu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gpxr__zcduj)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                gqur__ohs = len(qyo__ucdu)
                ttji__jphx = np.empty(gqur__ohs, dt64_dtype)
                yiowb__maxf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gjzv__dfbn)
                vio__kmc = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                vqv__gycy = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(vio__kmc))
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    upd__noy = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        qyo__ucdu[tfid__haevd])
                    if upd__noy == yiowb__maxf or vqv__gycy == yiowb__maxf:
                        zpuw__gkfms = yiowb__maxf
                    else:
                        zpuw__gkfms = op(upd__noy, vqv__gycy)
                    ttji__jphx[tfid__haevd
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        zpuw__gkfms)
                return bodo.hiframes.pd_series_ext.init_series(ttji__jphx,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and lhs ==
            bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type):
            gjzv__dfbn = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gpxr__zcduj = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                qyo__ucdu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gpxr__zcduj)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                gqur__ohs = len(qyo__ucdu)
                ttji__jphx = np.empty(gqur__ohs, dt64_dtype)
                yiowb__maxf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gjzv__dfbn)
                vio__kmc = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                vqv__gycy = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(vio__kmc))
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    upd__noy = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        qyo__ucdu[tfid__haevd])
                    if upd__noy == yiowb__maxf or vqv__gycy == yiowb__maxf:
                        zpuw__gkfms = yiowb__maxf
                    else:
                        zpuw__gkfms = op(upd__noy, vqv__gycy)
                    ttji__jphx[tfid__haevd
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        zpuw__gkfms)
                return bodo.hiframes.pd_series_ext.init_series(ttji__jphx,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and rhs ==
            bodo.hiframes.datetime_datetime_ext.datetime_datetime_type):
            gjzv__dfbn = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gpxr__zcduj = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                qyo__ucdu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gpxr__zcduj)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                gqur__ohs = len(qyo__ucdu)
                ttji__jphx = np.empty(gqur__ohs, timedelta64_dtype)
                yiowb__maxf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gjzv__dfbn)
                emc__wlq = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(rhs))
                upd__noy = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    emc__wlq)
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    nie__hsg = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        qyo__ucdu[tfid__haevd])
                    if nie__hsg == yiowb__maxf or upd__noy == yiowb__maxf:
                        zpuw__gkfms = yiowb__maxf
                    else:
                        zpuw__gkfms = op(nie__hsg, upd__noy)
                    ttji__jphx[tfid__haevd
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        zpuw__gkfms)
                return bodo.hiframes.pd_series_ext.init_series(ttji__jphx,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and lhs ==
            bodo.hiframes.datetime_datetime_ext.datetime_datetime_type):
            gjzv__dfbn = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gpxr__zcduj = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                qyo__ucdu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gpxr__zcduj)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                gqur__ohs = len(qyo__ucdu)
                ttji__jphx = np.empty(gqur__ohs, timedelta64_dtype)
                yiowb__maxf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gjzv__dfbn)
                emc__wlq = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(lhs))
                upd__noy = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    emc__wlq)
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    nie__hsg = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        qyo__ucdu[tfid__haevd])
                    if upd__noy == yiowb__maxf or nie__hsg == yiowb__maxf:
                        zpuw__gkfms = yiowb__maxf
                    else:
                        zpuw__gkfms = op(upd__noy, nie__hsg)
                    ttji__jphx[tfid__haevd
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        zpuw__gkfms)
                return bodo.hiframes.pd_series_ext.init_series(ttji__jphx,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs) and 
            rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            gjzv__dfbn = lhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qyo__ucdu = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                gqur__ohs = len(qyo__ucdu)
                ttji__jphx = np.empty(gqur__ohs, timedelta64_dtype)
                yiowb__maxf = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(gjzv__dfbn))
                vio__kmc = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                vqv__gycy = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(vio__kmc))
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    gsbo__osjz = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(qyo__ucdu[tfid__haevd]))
                    if vqv__gycy == yiowb__maxf or gsbo__osjz == yiowb__maxf:
                        zpuw__gkfms = yiowb__maxf
                    else:
                        zpuw__gkfms = op(gsbo__osjz, vqv__gycy)
                    ttji__jphx[tfid__haevd
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        zpuw__gkfms)
                return bodo.hiframes.pd_series_ext.init_series(ttji__jphx,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs) and 
            lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            gjzv__dfbn = rhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qyo__ucdu = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                gqur__ohs = len(qyo__ucdu)
                ttji__jphx = np.empty(gqur__ohs, timedelta64_dtype)
                yiowb__maxf = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(gjzv__dfbn))
                vio__kmc = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                vqv__gycy = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(vio__kmc))
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    gsbo__osjz = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(qyo__ucdu[tfid__haevd]))
                    if vqv__gycy == yiowb__maxf or gsbo__osjz == yiowb__maxf:
                        zpuw__gkfms = yiowb__maxf
                    else:
                        zpuw__gkfms = op(vqv__gycy, gsbo__osjz)
                    ttji__jphx[tfid__haevd
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        zpuw__gkfms)
                return bodo.hiframes.pd_series_ext.init_series(ttji__jphx,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        raise BodoError(f'{op} not supported for data types {lhs} and {rhs}.')
    return overload_series_dt_binop


def create_cmp_op_overload(op):

    def overload_series_dt64_cmp(lhs, rhs):
        if op == operator.ne:
            rhb__eduwa = True
        else:
            rhb__eduwa = False
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs) and 
            rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            gjzv__dfbn = lhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qyo__ucdu = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                gqur__ohs = len(qyo__ucdu)
                bcw__tuec = bodo.libs.bool_arr_ext.alloc_bool_array(gqur__ohs)
                yiowb__maxf = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(gjzv__dfbn))
                xigt__dix = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                jns__eri = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(xigt__dix))
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    cfruw__hmfl = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(qyo__ucdu[tfid__haevd]))
                    if cfruw__hmfl == yiowb__maxf or jns__eri == yiowb__maxf:
                        zpuw__gkfms = rhb__eduwa
                    else:
                        zpuw__gkfms = op(cfruw__hmfl, jns__eri)
                    bcw__tuec[tfid__haevd] = zpuw__gkfms
                return bodo.hiframes.pd_series_ext.init_series(bcw__tuec,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs) and 
            lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            gjzv__dfbn = rhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                qyo__ucdu = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                gqur__ohs = len(qyo__ucdu)
                bcw__tuec = bodo.libs.bool_arr_ext.alloc_bool_array(gqur__ohs)
                yiowb__maxf = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(gjzv__dfbn))
                zil__pkv = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                cfruw__hmfl = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(zil__pkv))
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    jns__eri = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(qyo__ucdu[tfid__haevd]))
                    if cfruw__hmfl == yiowb__maxf or jns__eri == yiowb__maxf:
                        zpuw__gkfms = rhb__eduwa
                    else:
                        zpuw__gkfms = op(cfruw__hmfl, jns__eri)
                    bcw__tuec[tfid__haevd] = zpuw__gkfms
                return bodo.hiframes.pd_series_ext.init_series(bcw__tuec,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            gjzv__dfbn = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gpxr__zcduj = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                qyo__ucdu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gpxr__zcduj)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                gqur__ohs = len(qyo__ucdu)
                bcw__tuec = bodo.libs.bool_arr_ext.alloc_bool_array(gqur__ohs)
                yiowb__maxf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gjzv__dfbn)
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    cfruw__hmfl = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(qyo__ucdu[tfid__haevd]))
                    if cfruw__hmfl == yiowb__maxf or rhs.value == yiowb__maxf:
                        zpuw__gkfms = rhb__eduwa
                    else:
                        zpuw__gkfms = op(cfruw__hmfl, rhs.value)
                    bcw__tuec[tfid__haevd] = zpuw__gkfms
                return bodo.hiframes.pd_series_ext.init_series(bcw__tuec,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if (lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type and
            bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs)):
            gjzv__dfbn = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                gpxr__zcduj = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                qyo__ucdu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gpxr__zcduj)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                gqur__ohs = len(qyo__ucdu)
                bcw__tuec = bodo.libs.bool_arr_ext.alloc_bool_array(gqur__ohs)
                yiowb__maxf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gjzv__dfbn)
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    jns__eri = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        qyo__ucdu[tfid__haevd])
                    if jns__eri == yiowb__maxf or lhs.value == yiowb__maxf:
                        zpuw__gkfms = rhb__eduwa
                    else:
                        zpuw__gkfms = op(lhs.value, jns__eri)
                    bcw__tuec[tfid__haevd] = zpuw__gkfms
                return bodo.hiframes.pd_series_ext.init_series(bcw__tuec,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and (rhs ==
            bodo.libs.str_ext.string_type or bodo.utils.typing.
            is_overload_constant_str(rhs)):
            gjzv__dfbn = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                gpxr__zcduj = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                qyo__ucdu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gpxr__zcduj)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                numba.parfors.parfor.init_prange()
                gqur__ohs = len(qyo__ucdu)
                bcw__tuec = bodo.libs.bool_arr_ext.alloc_bool_array(gqur__ohs)
                yiowb__maxf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gjzv__dfbn)
                ofee__ihshs = (bodo.hiframes.pd_timestamp_ext.
                    parse_datetime_str(rhs))
                ltbw__myppc = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ofee__ihshs)
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    cfruw__hmfl = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(qyo__ucdu[tfid__haevd]))
                    if (cfruw__hmfl == yiowb__maxf or ltbw__myppc ==
                        yiowb__maxf):
                        zpuw__gkfms = rhb__eduwa
                    else:
                        zpuw__gkfms = op(cfruw__hmfl, ltbw__myppc)
                    bcw__tuec[tfid__haevd] = zpuw__gkfms
                return bodo.hiframes.pd_series_ext.init_series(bcw__tuec,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and (lhs ==
            bodo.libs.str_ext.string_type or bodo.utils.typing.
            is_overload_constant_str(lhs)):
            gjzv__dfbn = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                gpxr__zcduj = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                qyo__ucdu = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    gpxr__zcduj)
                mkt__dckj = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                kcfi__qzlkg = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                numba.parfors.parfor.init_prange()
                gqur__ohs = len(qyo__ucdu)
                bcw__tuec = bodo.libs.bool_arr_ext.alloc_bool_array(gqur__ohs)
                yiowb__maxf = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gjzv__dfbn)
                ofee__ihshs = (bodo.hiframes.pd_timestamp_ext.
                    parse_datetime_str(lhs))
                ltbw__myppc = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    ofee__ihshs)
                for tfid__haevd in numba.parfors.parfor.internal_prange(
                    gqur__ohs):
                    emc__wlq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        qyo__ucdu[tfid__haevd])
                    if emc__wlq == yiowb__maxf or ltbw__myppc == yiowb__maxf:
                        zpuw__gkfms = rhb__eduwa
                    else:
                        zpuw__gkfms = op(ltbw__myppc, emc__wlq)
                    bcw__tuec[tfid__haevd] = zpuw__gkfms
                return bodo.hiframes.pd_series_ext.init_series(bcw__tuec,
                    mkt__dckj, kcfi__qzlkg)
            return impl
        raise BodoError(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_series_dt64_cmp


series_dt_unsupported_methods = {'to_period', 'to_pydatetime',
    'tz_localize', 'asfreq', 'to_timestamp'}
series_dt_unsupported_attrs = {'time', 'timetz', 'tz', 'freq', 'qyear',
    'start_time', 'end_time'}


def _install_series_dt_unsupported():
    for byxdl__yhgyp in series_dt_unsupported_attrs:
        gas__ztope = 'Series.dt.' + byxdl__yhgyp
        overload_attribute(SeriesDatetimePropertiesType, byxdl__yhgyp)(
            create_unsupported_overload(gas__ztope))
    for tjsd__uhctn in series_dt_unsupported_methods:
        gas__ztope = 'Series.dt.' + tjsd__uhctn
        overload_method(SeriesDatetimePropertiesType, tjsd__uhctn,
            no_unliteral=True)(create_unsupported_overload(gas__ztope))


_install_series_dt_unsupported()
