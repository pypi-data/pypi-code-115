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
        slur__flheh = 'SeriesDatetimePropertiesType({})'.format(stype)
        super(SeriesDatetimePropertiesType, self).__init__(slur__flheh)


@register_model(SeriesDatetimePropertiesType)
class SeriesDtModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        onbx__icxn = [('obj', fe_type.stype)]
        super(SeriesDtModel, self).__init__(dmm, fe_type, onbx__icxn)


make_attribute_wrapper(SeriesDatetimePropertiesType, 'obj', '_obj')


@intrinsic
def init_series_dt_properties(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        uno__pdop, = args
        vtvvf__qtokd = signature.return_type
        ibt__dgnl = cgutils.create_struct_proxy(vtvvf__qtokd)(context, builder)
        ibt__dgnl.obj = uno__pdop
        context.nrt.incref(builder, signature.args[0], uno__pdop)
        return ibt__dgnl._getvalue()
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
        tdtse__coj = 'def impl(S_dt):\n'
        tdtse__coj += '    S = S_dt._obj\n'
        tdtse__coj += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        tdtse__coj += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        tdtse__coj += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        tdtse__coj += '    numba.parfors.parfor.init_prange()\n'
        tdtse__coj += '    n = len(arr)\n'
        if field in ('is_leap_year', 'is_month_start', 'is_month_end',
            'is_quarter_start', 'is_quarter_end', 'is_year_start',
            'is_year_end'):
            tdtse__coj += '    out_arr = np.empty(n, np.bool_)\n'
        else:
            tdtse__coj += (
                '    out_arr = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n'
                )
        tdtse__coj += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        tdtse__coj += '        if bodo.libs.array_kernels.isna(arr, i):\n'
        tdtse__coj += '            bodo.libs.array_kernels.setna(out_arr, i)\n'
        tdtse__coj += '            continue\n'
        tdtse__coj += (
            '        dt64 = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(arr[i])\n'
            )
        if field in ('year', 'month', 'day'):
            tdtse__coj += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            if field in ('month', 'day'):
                tdtse__coj += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            tdtse__coj += '        out_arr[i] = {}\n'.format(field)
        elif field in ('dayofyear', 'day_of_year', 'dayofweek',
            'day_of_week', 'weekday'):
            bucex__rgfsy = {'dayofyear': 'get_day_of_year', 'day_of_year':
                'get_day_of_year', 'dayofweek': 'get_day_of_week',
                'day_of_week': 'get_day_of_week', 'weekday': 'get_day_of_week'}
            tdtse__coj += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            tdtse__coj += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            tdtse__coj += (
                """        out_arr[i] = bodo.hiframes.pd_timestamp_ext.{}(year, month, day)
"""
                .format(bucex__rgfsy[field]))
        elif field == 'is_leap_year':
            tdtse__coj += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            tdtse__coj += """        out_arr[i] = bodo.hiframes.pd_timestamp_ext.is_leap_year(year)
"""
        elif field in ('daysinmonth', 'days_in_month'):
            bucex__rgfsy = {'days_in_month': 'get_days_in_month',
                'daysinmonth': 'get_days_in_month'}
            tdtse__coj += """        dt, year, days = bodo.hiframes.pd_timestamp_ext.extract_year_days(dt64)
"""
            tdtse__coj += """        month, day = bodo.hiframes.pd_timestamp_ext.get_month_day(year, days)
"""
            tdtse__coj += (
                '        out_arr[i] = bodo.hiframes.pd_timestamp_ext.{}(year, month)\n'
                .format(bucex__rgfsy[field]))
        else:
            tdtse__coj += """        ts = bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp(dt64)
"""
            tdtse__coj += '        out_arr[i] = ts.' + field + '\n'
        tdtse__coj += (
            '    return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
            )
        lqrx__mnlvv = {}
        exec(tdtse__coj, {'bodo': bodo, 'numba': numba, 'np': np}, lqrx__mnlvv)
        impl = lqrx__mnlvv['impl']
        return impl
    return overload_field


def _install_date_fields():
    for field in bodo.hiframes.pd_timestamp_ext.date_fields:
        okwi__mbvmj = create_date_field_overload(field)
        overload_attribute(SeriesDatetimePropertiesType, field)(okwi__mbvmj)


_install_date_fields()


def create_date_method_overload(method):
    dthqk__pddbf = method in ['day_name', 'month_name']
    if dthqk__pddbf:
        tdtse__coj = 'def overload_method(S_dt, locale=None):\n'
        tdtse__coj += '    unsupported_args = dict(locale=locale)\n'
        tdtse__coj += '    arg_defaults = dict(locale=None)\n'
        tdtse__coj += '    bodo.utils.typing.check_unsupported_args(\n'
        tdtse__coj += f"        'Series.dt.{method}',\n"
        tdtse__coj += '        unsupported_args,\n'
        tdtse__coj += '        arg_defaults,\n'
        tdtse__coj += "        package_name='pandas',\n"
        tdtse__coj += "        module_name='Series',\n"
        tdtse__coj += '    )\n'
    else:
        tdtse__coj = 'def overload_method(S_dt):\n'
        tdtse__coj += f"""    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(S_dt, 'Series.dt.{method}()')
"""
    tdtse__coj += """    if not (S_dt.stype.dtype == bodo.datetime64ns or isinstance(S_dt.stype.dtype, bodo.libs.pd_datetime_arr_ext.PandasDatetimeTZDtype)):
"""
    tdtse__coj += '        return\n'
    if dthqk__pddbf:
        tdtse__coj += '    def impl(S_dt, locale=None):\n'
    else:
        tdtse__coj += '    def impl(S_dt):\n'
    tdtse__coj += '        S = S_dt._obj\n'
    tdtse__coj += (
        '        arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    tdtse__coj += (
        '        index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
    tdtse__coj += (
        '        name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
    tdtse__coj += '        numba.parfors.parfor.init_prange()\n'
    tdtse__coj += '        n = len(arr)\n'
    if dthqk__pddbf:
        tdtse__coj += """        out_arr = bodo.utils.utils.alloc_type(n, bodo.string_array_type, (-1,))
"""
    else:
        tdtse__coj += (
            "        out_arr = np.empty(n, np.dtype('datetime64[ns]'))\n")
    tdtse__coj += '        for i in numba.parfors.parfor.internal_prange(n):\n'
    tdtse__coj += '            if bodo.libs.array_kernels.isna(arr, i):\n'
    tdtse__coj += '                bodo.libs.array_kernels.setna(out_arr, i)\n'
    tdtse__coj += '                continue\n'
    tdtse__coj += (
        '            ts = bodo.utils.conversion.box_if_dt64(arr[i])\n')
    tdtse__coj += f'            method_val = ts.{method}()\n'
    if dthqk__pddbf:
        tdtse__coj += '            out_arr[i] = method_val\n'
    else:
        tdtse__coj += """            out_arr[i] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(method_val.value)
"""
    tdtse__coj += (
        '        return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    tdtse__coj += '    return impl\n'
    lqrx__mnlvv = {}
    exec(tdtse__coj, {'bodo': bodo, 'numba': numba, 'np': np}, lqrx__mnlvv)
    overload_method = lqrx__mnlvv['overload_method']
    return overload_method


def _install_date_methods():
    for method in bodo.hiframes.pd_timestamp_ext.date_methods:
        okwi__mbvmj = create_date_method_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            okwi__mbvmj)


_install_date_methods()


@overload_attribute(SeriesDatetimePropertiesType, 'date')
def series_dt_date_overload(S_dt):
    if not (S_dt.stype.dtype == types.NPDatetime('ns') or isinstance(S_dt.
        stype.dtype, bodo.libs.pd_datetime_arr_ext.PandasDatetimeTZDtype)):
        return

    def impl(S_dt):
        sioss__xvfhi = S_dt._obj
        nboqd__ecul = bodo.hiframes.pd_series_ext.get_series_data(sioss__xvfhi)
        tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(sioss__xvfhi)
        slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(sioss__xvfhi)
        numba.parfors.parfor.init_prange()
        dptaf__jij = len(nboqd__ecul)
        lduk__rng = bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(
            dptaf__jij)
        for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij):
            pph__pvnnh = nboqd__ecul[wfl__mdf]
            mrsbf__hcc = bodo.utils.conversion.box_if_dt64(pph__pvnnh)
            lduk__rng[wfl__mdf] = datetime.date(mrsbf__hcc.year, mrsbf__hcc
                .month, mrsbf__hcc.day)
        return bodo.hiframes.pd_series_ext.init_series(lduk__rng,
            tbk__axcgo, slur__flheh)
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
            wrd__lofb = ['days', 'hours', 'minutes', 'seconds',
                'milliseconds', 'microseconds', 'nanoseconds']
            aeze__htd = 'convert_numpy_timedelta64_to_pd_timedelta'
            hrzad__bbn = 'np.empty(n, np.int64)'
            xkhd__cam = attr
        elif attr == 'isocalendar':
            wrd__lofb = ['year', 'week', 'day']
            aeze__htd = 'convert_datetime64_to_timestamp'
            hrzad__bbn = 'bodo.libs.int_arr_ext.alloc_int_array(n, np.uint32)'
            xkhd__cam = attr + '()'
        tdtse__coj = 'def impl(S_dt):\n'
        tdtse__coj += '    S = S_dt._obj\n'
        tdtse__coj += (
            '    arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        tdtse__coj += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        tdtse__coj += '    numba.parfors.parfor.init_prange()\n'
        tdtse__coj += '    n = len(arr)\n'
        for field in wrd__lofb:
            tdtse__coj += '    {} = {}\n'.format(field, hrzad__bbn)
        tdtse__coj += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        tdtse__coj += '        if bodo.libs.array_kernels.isna(arr, i):\n'
        for field in wrd__lofb:
            tdtse__coj += ('            bodo.libs.array_kernels.setna({}, i)\n'
                .format(field))
        tdtse__coj += '            continue\n'
        xst__xbqz = '(' + '[i], '.join(wrd__lofb) + '[i])'
        tdtse__coj += (
            '        {} = bodo.hiframes.pd_timestamp_ext.{}(arr[i]).{}\n'.
            format(xst__xbqz, aeze__htd, xkhd__cam))
        cim__pps = '(' + ', '.join(wrd__lofb) + ')'
        sbyk__bgw = "('" + "', '".join(wrd__lofb) + "')"
        tdtse__coj += (
            '    return bodo.hiframes.pd_dataframe_ext.init_dataframe({}, index, {})\n'
            .format(cim__pps, sbyk__bgw))
        lqrx__mnlvv = {}
        exec(tdtse__coj, {'bodo': bodo, 'numba': numba, 'np': np}, lqrx__mnlvv)
        impl = lqrx__mnlvv['impl']
        return impl
    return series_dt_df_output_overload


def _install_df_output_overload():
    zomsh__hryf = [('components', overload_attribute), ('isocalendar',
        overload_method)]
    for attr, lpe__mnhr in zomsh__hryf:
        okwi__mbvmj = create_series_dt_df_output_overload(attr)
        lpe__mnhr(SeriesDatetimePropertiesType, attr, inline='always')(
            okwi__mbvmj)


_install_df_output_overload()


def create_timedelta_field_overload(field):

    def overload_field(S_dt):
        if not S_dt.stype.dtype == types.NPTimedelta('ns'):
            return
        tdtse__coj = 'def impl(S_dt):\n'
        tdtse__coj += '    S = S_dt._obj\n'
        tdtse__coj += (
            '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        tdtse__coj += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        tdtse__coj += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        tdtse__coj += '    numba.parfors.parfor.init_prange()\n'
        tdtse__coj += '    n = len(A)\n'
        tdtse__coj += (
            '    B = bodo.libs.int_arr_ext.alloc_int_array(n, np.int64)\n')
        tdtse__coj += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        tdtse__coj += '        if bodo.libs.array_kernels.isna(A, i):\n'
        tdtse__coj += '            bodo.libs.array_kernels.setna(B, i)\n'
        tdtse__coj += '            continue\n'
        tdtse__coj += """        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])
"""
        if field == 'nanoseconds':
            tdtse__coj += '        B[i] = td64 % 1000\n'
        elif field == 'microseconds':
            tdtse__coj += '        B[i] = td64 // 1000 % 1000000\n'
        elif field == 'seconds':
            tdtse__coj += (
                '        B[i] = td64 // (1000 * 1000000) % (60 * 60 * 24)\n')
        elif field == 'days':
            tdtse__coj += (
                '        B[i] = td64 // (1000 * 1000000 * 60 * 60 * 24)\n')
        else:
            assert False, 'invalid timedelta field'
        tdtse__coj += (
            '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
            )
        lqrx__mnlvv = {}
        exec(tdtse__coj, {'numba': numba, 'np': np, 'bodo': bodo}, lqrx__mnlvv)
        impl = lqrx__mnlvv['impl']
        return impl
    return overload_field


def create_timedelta_method_overload(method):

    def overload_method(S_dt):
        if not S_dt.stype.dtype == types.NPTimedelta('ns'):
            return
        tdtse__coj = 'def impl(S_dt):\n'
        tdtse__coj += '    S = S_dt._obj\n'
        tdtse__coj += (
            '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        tdtse__coj += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        tdtse__coj += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        tdtse__coj += '    numba.parfors.parfor.init_prange()\n'
        tdtse__coj += '    n = len(A)\n'
        if method == 'total_seconds':
            tdtse__coj += '    B = np.empty(n, np.float64)\n'
        else:
            tdtse__coj += """    B = bodo.hiframes.datetime_timedelta_ext.alloc_datetime_timedelta_array(n)
"""
        tdtse__coj += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        tdtse__coj += '        if bodo.libs.array_kernels.isna(A, i):\n'
        tdtse__coj += '            bodo.libs.array_kernels.setna(B, i)\n'
        tdtse__coj += '            continue\n'
        tdtse__coj += """        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])
"""
        if method == 'total_seconds':
            tdtse__coj += '        B[i] = td64 / (1000.0 * 1000000.0)\n'
        elif method == 'to_pytimedelta':
            tdtse__coj += (
                '        B[i] = datetime.timedelta(microseconds=td64 // 1000)\n'
                )
        else:
            assert False, 'invalid timedelta method'
        if method == 'total_seconds':
            tdtse__coj += (
                '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
                )
        else:
            tdtse__coj += '    return B\n'
        lqrx__mnlvv = {}
        exec(tdtse__coj, {'numba': numba, 'np': np, 'bodo': bodo,
            'datetime': datetime}, lqrx__mnlvv)
        impl = lqrx__mnlvv['impl']
        return impl
    return overload_method


def _install_S_dt_timedelta_fields():
    for field in bodo.hiframes.pd_timestamp_ext.timedelta_fields:
        okwi__mbvmj = create_timedelta_field_overload(field)
        overload_attribute(SeriesDatetimePropertiesType, field)(okwi__mbvmj)


_install_S_dt_timedelta_fields()


def _install_S_dt_timedelta_methods():
    for method in bodo.hiframes.pd_timestamp_ext.timedelta_methods:
        okwi__mbvmj = create_timedelta_method_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            okwi__mbvmj)


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
        sioss__xvfhi = S_dt._obj
        epbur__fzmvq = bodo.hiframes.pd_series_ext.get_series_data(sioss__xvfhi
            )
        tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(sioss__xvfhi)
        slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(sioss__xvfhi)
        numba.parfors.parfor.init_prange()
        dptaf__jij = len(epbur__fzmvq)
        yvkol__apgzv = bodo.libs.str_arr_ext.pre_alloc_string_array(dptaf__jij,
            -1)
        for fiyhc__rycz in numba.parfors.parfor.internal_prange(dptaf__jij):
            if bodo.libs.array_kernels.isna(epbur__fzmvq, fiyhc__rycz):
                bodo.libs.array_kernels.setna(yvkol__apgzv, fiyhc__rycz)
                continue
            yvkol__apgzv[fiyhc__rycz] = bodo.utils.conversion.box_if_dt64(
                epbur__fzmvq[fiyhc__rycz]).strftime(date_format)
        return bodo.hiframes.pd_series_ext.init_series(yvkol__apgzv,
            tbk__axcgo, slur__flheh)
    return impl


@overload_method(SeriesDatetimePropertiesType, 'tz_convert', inline=
    'always', no_unliteral=True)
def overload_dt_tz_convert(S_dt, tz):

    def impl(S_dt, tz):
        sioss__xvfhi = S_dt._obj
        uruq__booi = get_series_data(sioss__xvfhi).tz_convert(tz)
        tbk__axcgo = get_series_index(sioss__xvfhi)
        slur__flheh = get_series_name(sioss__xvfhi)
        return init_series(uruq__booi, tbk__axcgo, slur__flheh)
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
        gwv__cgfa = dict(ambiguous=ambiguous, nonexistent=nonexistent)
        guxl__jvs = dict(ambiguous='raise', nonexistent='raise')
        check_unsupported_args(f'Series.dt.{method}', gwv__cgfa, guxl__jvs,
            package_name='pandas', module_name='Series')
        tdtse__coj = (
            "def impl(S_dt, freq, ambiguous='raise', nonexistent='raise'):\n")
        tdtse__coj += '    S = S_dt._obj\n'
        tdtse__coj += (
            '    A = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        tdtse__coj += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        tdtse__coj += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        tdtse__coj += '    numba.parfors.parfor.init_prange()\n'
        tdtse__coj += '    n = len(A)\n'
        if S_dt.stype.dtype == types.NPTimedelta('ns'):
            tdtse__coj += "    B = np.empty(n, np.dtype('timedelta64[ns]'))\n"
        else:
            tdtse__coj += "    B = np.empty(n, np.dtype('datetime64[ns]'))\n"
        tdtse__coj += '    for i in numba.parfors.parfor.internal_prange(n):\n'
        tdtse__coj += '        if bodo.libs.array_kernels.isna(A, i):\n'
        tdtse__coj += '            bodo.libs.array_kernels.setna(B, i)\n'
        tdtse__coj += '            continue\n'
        if S_dt.stype.dtype == types.NPTimedelta('ns'):
            ipnkq__kglgc = (
                'bodo.hiframes.pd_timestamp_ext.convert_numpy_timedelta64_to_pd_timedelta'
                )
            wna__vbsgt = (
                'bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64')
        else:
            ipnkq__kglgc = (
                'bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp'
                )
            wna__vbsgt = 'bodo.hiframes.pd_timestamp_ext.integer_to_dt64'
        tdtse__coj += '        B[i] = {}({}(A[i]).{}(freq).value)\n'.format(
            wna__vbsgt, ipnkq__kglgc, method)
        tdtse__coj += (
            '    return bodo.hiframes.pd_series_ext.init_series(B, index, name)\n'
            )
        lqrx__mnlvv = {}
        exec(tdtse__coj, {'numba': numba, 'np': np, 'bodo': bodo}, lqrx__mnlvv)
        impl = lqrx__mnlvv['impl']
        return impl
    return freq_overload


def _install_S_dt_timedelta_freq_methods():
    qczr__bgosz = ['ceil', 'floor', 'round']
    for method in qczr__bgosz:
        okwi__mbvmj = create_timedelta_freq_overload(method)
        overload_method(SeriesDatetimePropertiesType, method, inline='always')(
            okwi__mbvmj)


_install_S_dt_timedelta_freq_methods()


def create_bin_op_overload(op):

    def overload_series_dt_binop(lhs, rhs):
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs):
            gzum__maj = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                diny__etop = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                pmevz__lcb = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    diny__etop)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                ynn__cgph = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                hjzf__rlw = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    ynn__cgph)
                dptaf__jij = len(pmevz__lcb)
                sioss__xvfhi = np.empty(dptaf__jij, timedelta64_dtype)
                ksoed__ysdxi = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gzum__maj)
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    qbyr__jukyq = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(pmevz__lcb[wfl__mdf]))
                    ddk__uoby = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        hjzf__rlw[wfl__mdf])
                    if (qbyr__jukyq == ksoed__ysdxi or ddk__uoby ==
                        ksoed__ysdxi):
                        mmt__ibfs = ksoed__ysdxi
                    else:
                        mmt__ibfs = op(qbyr__jukyq, ddk__uoby)
                    sioss__xvfhi[wfl__mdf
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        mmt__ibfs)
                return bodo.hiframes.pd_series_ext.init_series(sioss__xvfhi,
                    tbk__axcgo, slur__flheh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs):
            gzum__maj = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                joz__yhiof = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                nboqd__ecul = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    joz__yhiof)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                hjzf__rlw = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                dptaf__jij = len(nboqd__ecul)
                sioss__xvfhi = np.empty(dptaf__jij, dt64_dtype)
                ksoed__ysdxi = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gzum__maj)
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    xuypv__hxgk = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(nboqd__ecul[wfl__mdf]))
                    rxbql__dqpw = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(hjzf__rlw[wfl__mdf]))
                    if (xuypv__hxgk == ksoed__ysdxi or rxbql__dqpw ==
                        ksoed__ysdxi):
                        mmt__ibfs = ksoed__ysdxi
                    else:
                        mmt__ibfs = op(xuypv__hxgk, rxbql__dqpw)
                    sioss__xvfhi[wfl__mdf
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        mmt__ibfs)
                return bodo.hiframes.pd_series_ext.init_series(sioss__xvfhi,
                    tbk__axcgo, slur__flheh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
            ) and bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs):
            gzum__maj = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                joz__yhiof = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                nboqd__ecul = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    joz__yhiof)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                hjzf__rlw = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                dptaf__jij = len(nboqd__ecul)
                sioss__xvfhi = np.empty(dptaf__jij, dt64_dtype)
                ksoed__ysdxi = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gzum__maj)
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    xuypv__hxgk = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(nboqd__ecul[wfl__mdf]))
                    rxbql__dqpw = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(hjzf__rlw[wfl__mdf]))
                    if (xuypv__hxgk == ksoed__ysdxi or rxbql__dqpw ==
                        ksoed__ysdxi):
                        mmt__ibfs = ksoed__ysdxi
                    else:
                        mmt__ibfs = op(xuypv__hxgk, rxbql__dqpw)
                    sioss__xvfhi[wfl__mdf
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        mmt__ibfs)
                return bodo.hiframes.pd_series_ext.init_series(sioss__xvfhi,
                    tbk__axcgo, slur__flheh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            gzum__maj = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                joz__yhiof = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                nboqd__ecul = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    joz__yhiof)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                dptaf__jij = len(nboqd__ecul)
                sioss__xvfhi = np.empty(dptaf__jij, timedelta64_dtype)
                ksoed__ysdxi = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gzum__maj)
                hhv__adb = rhs.value
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    xuypv__hxgk = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(nboqd__ecul[wfl__mdf]))
                    if xuypv__hxgk == ksoed__ysdxi or hhv__adb == ksoed__ysdxi:
                        mmt__ibfs = ksoed__ysdxi
                    else:
                        mmt__ibfs = op(xuypv__hxgk, hhv__adb)
                    sioss__xvfhi[wfl__mdf
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        mmt__ibfs)
                return bodo.hiframes.pd_series_ext.init_series(sioss__xvfhi,
                    tbk__axcgo, slur__flheh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
            ) and lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            gzum__maj = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                joz__yhiof = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                nboqd__ecul = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    joz__yhiof)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                dptaf__jij = len(nboqd__ecul)
                sioss__xvfhi = np.empty(dptaf__jij, timedelta64_dtype)
                ksoed__ysdxi = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gzum__maj)
                hhv__adb = lhs.value
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    xuypv__hxgk = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(nboqd__ecul[wfl__mdf]))
                    if hhv__adb == ksoed__ysdxi or xuypv__hxgk == ksoed__ysdxi:
                        mmt__ibfs = ksoed__ysdxi
                    else:
                        mmt__ibfs = op(hhv__adb, xuypv__hxgk)
                    sioss__xvfhi[wfl__mdf
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        mmt__ibfs)
                return bodo.hiframes.pd_series_ext.init_series(sioss__xvfhi,
                    tbk__axcgo, slur__flheh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and rhs ==
            bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type):
            gzum__maj = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                joz__yhiof = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                nboqd__ecul = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    joz__yhiof)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                dptaf__jij = len(nboqd__ecul)
                sioss__xvfhi = np.empty(dptaf__jij, dt64_dtype)
                ksoed__ysdxi = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gzum__maj)
                xmqn__dzkj = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                rxbql__dqpw = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(xmqn__dzkj))
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    xuypv__hxgk = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(nboqd__ecul[wfl__mdf]))
                    if (xuypv__hxgk == ksoed__ysdxi or rxbql__dqpw ==
                        ksoed__ysdxi):
                        mmt__ibfs = ksoed__ysdxi
                    else:
                        mmt__ibfs = op(xuypv__hxgk, rxbql__dqpw)
                    sioss__xvfhi[wfl__mdf
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        mmt__ibfs)
                return bodo.hiframes.pd_series_ext.init_series(sioss__xvfhi,
                    tbk__axcgo, slur__flheh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and lhs ==
            bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type):
            gzum__maj = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                joz__yhiof = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                nboqd__ecul = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    joz__yhiof)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                dptaf__jij = len(nboqd__ecul)
                sioss__xvfhi = np.empty(dptaf__jij, dt64_dtype)
                ksoed__ysdxi = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gzum__maj)
                xmqn__dzkj = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                rxbql__dqpw = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(xmqn__dzkj))
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    xuypv__hxgk = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(nboqd__ecul[wfl__mdf]))
                    if (xuypv__hxgk == ksoed__ysdxi or rxbql__dqpw ==
                        ksoed__ysdxi):
                        mmt__ibfs = ksoed__ysdxi
                    else:
                        mmt__ibfs = op(xuypv__hxgk, rxbql__dqpw)
                    sioss__xvfhi[wfl__mdf
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_dt64(
                        mmt__ibfs)
                return bodo.hiframes.pd_series_ext.init_series(sioss__xvfhi,
                    tbk__axcgo, slur__flheh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and rhs ==
            bodo.hiframes.datetime_datetime_ext.datetime_datetime_type):
            gzum__maj = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                joz__yhiof = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                nboqd__ecul = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    joz__yhiof)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                dptaf__jij = len(nboqd__ecul)
                sioss__xvfhi = np.empty(dptaf__jij, timedelta64_dtype)
                ksoed__ysdxi = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gzum__maj)
                zwaw__sqcne = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(rhs))
                xuypv__hxgk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    zwaw__sqcne)
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    fagg__iaweq = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(nboqd__ecul[wfl__mdf]))
                    if (fagg__iaweq == ksoed__ysdxi or xuypv__hxgk ==
                        ksoed__ysdxi):
                        mmt__ibfs = ksoed__ysdxi
                    else:
                        mmt__ibfs = op(fagg__iaweq, xuypv__hxgk)
                    sioss__xvfhi[wfl__mdf
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        mmt__ibfs)
                return bodo.hiframes.pd_series_ext.init_series(sioss__xvfhi,
                    tbk__axcgo, slur__flheh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and lhs ==
            bodo.hiframes.datetime_datetime_ext.datetime_datetime_type):
            gzum__maj = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                joz__yhiof = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                nboqd__ecul = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    joz__yhiof)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                dptaf__jij = len(nboqd__ecul)
                sioss__xvfhi = np.empty(dptaf__jij, timedelta64_dtype)
                ksoed__ysdxi = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gzum__maj)
                zwaw__sqcne = (bodo.hiframes.pd_timestamp_ext.
                    datetime_datetime_to_dt64(lhs))
                xuypv__hxgk = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    zwaw__sqcne)
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    fagg__iaweq = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(nboqd__ecul[wfl__mdf]))
                    if (xuypv__hxgk == ksoed__ysdxi or fagg__iaweq ==
                        ksoed__ysdxi):
                        mmt__ibfs = ksoed__ysdxi
                    else:
                        mmt__ibfs = op(xuypv__hxgk, fagg__iaweq)
                    sioss__xvfhi[wfl__mdf
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        mmt__ibfs)
                return bodo.hiframes.pd_series_ext.init_series(sioss__xvfhi,
                    tbk__axcgo, slur__flheh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs) and 
            rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            gzum__maj = lhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                nboqd__ecul = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                dptaf__jij = len(nboqd__ecul)
                sioss__xvfhi = np.empty(dptaf__jij, timedelta64_dtype)
                ksoed__ysdxi = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(gzum__maj))
                xmqn__dzkj = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                rxbql__dqpw = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(xmqn__dzkj))
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    kxk__kfy = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(nboqd__ecul[wfl__mdf]))
                    if rxbql__dqpw == ksoed__ysdxi or kxk__kfy == ksoed__ysdxi:
                        mmt__ibfs = ksoed__ysdxi
                    else:
                        mmt__ibfs = op(kxk__kfy, rxbql__dqpw)
                    sioss__xvfhi[wfl__mdf
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        mmt__ibfs)
                return bodo.hiframes.pd_series_ext.init_series(sioss__xvfhi,
                    tbk__axcgo, slur__flheh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs) and 
            lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            gzum__maj = rhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                nboqd__ecul = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                dptaf__jij = len(nboqd__ecul)
                sioss__xvfhi = np.empty(dptaf__jij, timedelta64_dtype)
                ksoed__ysdxi = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(gzum__maj))
                xmqn__dzkj = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                rxbql__dqpw = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(xmqn__dzkj))
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    kxk__kfy = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(nboqd__ecul[wfl__mdf]))
                    if rxbql__dqpw == ksoed__ysdxi or kxk__kfy == ksoed__ysdxi:
                        mmt__ibfs = ksoed__ysdxi
                    else:
                        mmt__ibfs = op(rxbql__dqpw, kxk__kfy)
                    sioss__xvfhi[wfl__mdf
                        ] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                        mmt__ibfs)
                return bodo.hiframes.pd_series_ext.init_series(sioss__xvfhi,
                    tbk__axcgo, slur__flheh)
            return impl
        raise BodoError(f'{op} not supported for data types {lhs} and {rhs}.')
    return overload_series_dt_binop


def create_cmp_op_overload(op):

    def overload_series_dt64_cmp(lhs, rhs):
        if op == operator.ne:
            tbgm__gqbh = True
        else:
            tbgm__gqbh = False
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs) and 
            rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            gzum__maj = lhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                nboqd__ecul = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                dptaf__jij = len(nboqd__ecul)
                lduk__rng = bodo.libs.bool_arr_ext.alloc_bool_array(dptaf__jij)
                ksoed__ysdxi = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(gzum__maj))
                hjr__zzd = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(rhs))
                ygmwc__jcd = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(hjr__zzd))
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    szl__epq = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(nboqd__ecul[wfl__mdf]))
                    if szl__epq == ksoed__ysdxi or ygmwc__jcd == ksoed__ysdxi:
                        mmt__ibfs = tbgm__gqbh
                    else:
                        mmt__ibfs = op(szl__epq, ygmwc__jcd)
                    lduk__rng[wfl__mdf] = mmt__ibfs
                return bodo.hiframes.pd_series_ext.init_series(lduk__rng,
                    tbk__axcgo, slur__flheh)
            return impl
        if (bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs) and 
            lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
            ):
            gzum__maj = rhs.dtype('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                nboqd__ecul = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                dptaf__jij = len(nboqd__ecul)
                lduk__rng = bodo.libs.bool_arr_ext.alloc_bool_array(dptaf__jij)
                ksoed__ysdxi = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(gzum__maj))
                gecsd__bjhk = (bodo.hiframes.pd_timestamp_ext.
                    datetime_timedelta_to_timedelta64(lhs))
                szl__epq = (bodo.hiframes.pd_timestamp_ext.
                    timedelta64_to_integer(gecsd__bjhk))
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    ygmwc__jcd = (bodo.hiframes.pd_timestamp_ext.
                        timedelta64_to_integer(nboqd__ecul[wfl__mdf]))
                    if szl__epq == ksoed__ysdxi or ygmwc__jcd == ksoed__ysdxi:
                        mmt__ibfs = tbgm__gqbh
                    else:
                        mmt__ibfs = op(szl__epq, ygmwc__jcd)
                    lduk__rng[wfl__mdf] = mmt__ibfs
                return bodo.hiframes.pd_series_ext.init_series(lduk__rng,
                    tbk__axcgo, slur__flheh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
            ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
            gzum__maj = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                joz__yhiof = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                nboqd__ecul = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    joz__yhiof)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                dptaf__jij = len(nboqd__ecul)
                lduk__rng = bodo.libs.bool_arr_ext.alloc_bool_array(dptaf__jij)
                ksoed__ysdxi = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gzum__maj)
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    szl__epq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        nboqd__ecul[wfl__mdf])
                    if szl__epq == ksoed__ysdxi or rhs.value == ksoed__ysdxi:
                        mmt__ibfs = tbgm__gqbh
                    else:
                        mmt__ibfs = op(szl__epq, rhs.value)
                    lduk__rng[wfl__mdf] = mmt__ibfs
                return bodo.hiframes.pd_series_ext.init_series(lduk__rng,
                    tbk__axcgo, slur__flheh)
            return impl
        if (lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type and
            bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs)):
            gzum__maj = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                joz__yhiof = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                nboqd__ecul = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    joz__yhiof)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                dptaf__jij = len(nboqd__ecul)
                lduk__rng = bodo.libs.bool_arr_ext.alloc_bool_array(dptaf__jij)
                ksoed__ysdxi = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gzum__maj)
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    ygmwc__jcd = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(nboqd__ecul[wfl__mdf]))
                    if ygmwc__jcd == ksoed__ysdxi or lhs.value == ksoed__ysdxi:
                        mmt__ibfs = tbgm__gqbh
                    else:
                        mmt__ibfs = op(lhs.value, ygmwc__jcd)
                    lduk__rng[wfl__mdf] = mmt__ibfs
                return bodo.hiframes.pd_series_ext.init_series(lduk__rng,
                    tbk__axcgo, slur__flheh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and (rhs ==
            bodo.libs.str_ext.string_type or bodo.utils.typing.
            is_overload_constant_str(rhs)):
            gzum__maj = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                joz__yhiof = bodo.hiframes.pd_series_ext.get_series_data(lhs)
                nboqd__ecul = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    joz__yhiof)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(lhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(lhs)
                numba.parfors.parfor.init_prange()
                dptaf__jij = len(nboqd__ecul)
                lduk__rng = bodo.libs.bool_arr_ext.alloc_bool_array(dptaf__jij)
                ksoed__ysdxi = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gzum__maj)
                bthv__seon = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(
                    rhs)
                jkg__qbe = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    bthv__seon)
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    szl__epq = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                        nboqd__ecul[wfl__mdf])
                    if szl__epq == ksoed__ysdxi or jkg__qbe == ksoed__ysdxi:
                        mmt__ibfs = tbgm__gqbh
                    else:
                        mmt__ibfs = op(szl__epq, jkg__qbe)
                    lduk__rng[wfl__mdf] = mmt__ibfs
                return bodo.hiframes.pd_series_ext.init_series(lduk__rng,
                    tbk__axcgo, slur__flheh)
            return impl
        if bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and (lhs ==
            bodo.libs.str_ext.string_type or bodo.utils.typing.
            is_overload_constant_str(lhs)):
            gzum__maj = bodo.datetime64ns('NaT')

            def impl(lhs, rhs):
                joz__yhiof = bodo.hiframes.pd_series_ext.get_series_data(rhs)
                nboqd__ecul = bodo.libs.pd_datetime_arr_ext.unwrap_tz_array(
                    joz__yhiof)
                tbk__axcgo = bodo.hiframes.pd_series_ext.get_series_index(rhs)
                slur__flheh = bodo.hiframes.pd_series_ext.get_series_name(rhs)
                numba.parfors.parfor.init_prange()
                dptaf__jij = len(nboqd__ecul)
                lduk__rng = bodo.libs.bool_arr_ext.alloc_bool_array(dptaf__jij)
                ksoed__ysdxi = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    gzum__maj)
                bthv__seon = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(
                    lhs)
                jkg__qbe = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    bthv__seon)
                for wfl__mdf in numba.parfors.parfor.internal_prange(dptaf__jij
                    ):
                    zwaw__sqcne = (bodo.hiframes.pd_timestamp_ext.
                        dt64_to_integer(nboqd__ecul[wfl__mdf]))
                    if zwaw__sqcne == ksoed__ysdxi or jkg__qbe == ksoed__ysdxi:
                        mmt__ibfs = tbgm__gqbh
                    else:
                        mmt__ibfs = op(jkg__qbe, zwaw__sqcne)
                    lduk__rng[wfl__mdf] = mmt__ibfs
                return bodo.hiframes.pd_series_ext.init_series(lduk__rng,
                    tbk__axcgo, slur__flheh)
            return impl
        raise BodoError(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_series_dt64_cmp


series_dt_unsupported_methods = {'to_period', 'to_pydatetime',
    'tz_localize', 'asfreq', 'to_timestamp'}
series_dt_unsupported_attrs = {'time', 'timetz', 'tz', 'freq', 'qyear',
    'start_time', 'end_time'}


def _install_series_dt_unsupported():
    for krwei__cmwg in series_dt_unsupported_attrs:
        pfs__sxl = 'Series.dt.' + krwei__cmwg
        overload_attribute(SeriesDatetimePropertiesType, krwei__cmwg)(
            create_unsupported_overload(pfs__sxl))
    for jvz__iqr in series_dt_unsupported_methods:
        pfs__sxl = 'Series.dt.' + jvz__iqr
        overload_method(SeriesDatetimePropertiesType, jvz__iqr,
            no_unliteral=True)(create_unsupported_overload(pfs__sxl))


_install_series_dt_unsupported()
