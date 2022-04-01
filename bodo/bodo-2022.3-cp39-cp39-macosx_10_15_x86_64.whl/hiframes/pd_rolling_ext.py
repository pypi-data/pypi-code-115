"""typing for rolling window functions
"""
from numba.core import cgutils, types
from numba.core.imputils import impl_ret_borrowed
from numba.core.typing.templates import AbstractTemplate, AttributeTemplate, signature
from numba.extending import infer, infer_getattr, intrinsic, lower_builtin, make_attribute_wrapper, models, overload, overload_method, register_model
import bodo
from bodo.hiframes.datetime_timedelta_ext import datetime_timedelta_type, pd_timedelta_type
from bodo.hiframes.pd_dataframe_ext import DataFrameType, check_runtime_cols_unsupported
from bodo.hiframes.pd_groupby_ext import DataFrameGroupByType
from bodo.hiframes.pd_series_ext import SeriesType
from bodo.hiframes.rolling import supported_rolling_funcs, unsupported_rolling_methods
from bodo.utils.typing import BodoError, check_unsupported_args, create_unsupported_overload, get_literal_value, is_const_func_type, is_literal_type, is_overload_bool, is_overload_constant_str, is_overload_int, is_overload_none, raise_bodo_error


class RollingType(types.Type):

    def __init__(self, obj_type, window_type, on, selection,
        explicit_select=False, series_select=False):
        if isinstance(obj_type, bodo.SeriesType):
            hslyd__ohag = 'Series'
        else:
            hslyd__ohag = 'DataFrame'
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(obj_type,
            f'{hslyd__ohag}.rolling()')
        self.obj_type = obj_type
        self.window_type = window_type
        self.on = on
        self.selection = selection
        self.explicit_select = explicit_select
        self.series_select = series_select
        super(RollingType, self).__init__(name=
            f'RollingType({obj_type}, {window_type}, {on}, {selection}, {explicit_select}, {series_select})'
            )

    def copy(self):
        return RollingType(self.obj_type, self.window_type, self.on, self.
            selection, self.explicit_select, self.series_select)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(RollingType)
class RollingModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        vprea__ysde = [('obj', fe_type.obj_type), ('window', fe_type.
            window_type), ('min_periods', types.int64), ('center', types.bool_)
            ]
        super(RollingModel, self).__init__(dmm, fe_type, vprea__ysde)


make_attribute_wrapper(RollingType, 'obj', 'obj')
make_attribute_wrapper(RollingType, 'window', 'window')
make_attribute_wrapper(RollingType, 'center', 'center')
make_attribute_wrapper(RollingType, 'min_periods', 'min_periods')


@overload_method(DataFrameType, 'rolling', inline='always', no_unliteral=True)
def df_rolling_overload(df, window, min_periods=None, center=False,
    win_type=None, on=None, axis=0, closed=None):
    check_runtime_cols_unsupported(df, 'DataFrame.rolling()')
    dnjkt__eewu = dict(win_type=win_type, axis=axis, closed=closed)
    pzm__bbjae = dict(win_type=None, axis=0, closed=None)
    check_unsupported_args('DataFrame.rolling', dnjkt__eewu, pzm__bbjae,
        package_name='pandas', module_name='Window')
    _validate_rolling_args(df, window, min_periods, center, on)

    def impl(df, window, min_periods=None, center=False, win_type=None, on=
        None, axis=0, closed=None):
        min_periods = _handle_default_min_periods(min_periods, window)
        return bodo.hiframes.pd_rolling_ext.init_rolling(df, window,
            min_periods, center, on)
    return impl


@overload_method(SeriesType, 'rolling', inline='always', no_unliteral=True)
def overload_series_rolling(S, window, min_periods=None, center=False,
    win_type=None, on=None, axis=0, closed=None):
    dnjkt__eewu = dict(win_type=win_type, axis=axis, closed=closed)
    pzm__bbjae = dict(win_type=None, axis=0, closed=None)
    check_unsupported_args('Series.rolling', dnjkt__eewu, pzm__bbjae,
        package_name='pandas', module_name='Window')
    _validate_rolling_args(S, window, min_periods, center, on)

    def impl(S, window, min_periods=None, center=False, win_type=None, on=
        None, axis=0, closed=None):
        min_periods = _handle_default_min_periods(min_periods, window)
        return bodo.hiframes.pd_rolling_ext.init_rolling(S, window,
            min_periods, center, on)
    return impl


@intrinsic
def init_rolling(typingctx, obj_type, window_type, min_periods_type,
    center_type, on_type=None):

    def codegen(context, builder, signature, args):
        fhb__xpimr, vgr__kzm, gljfg__fgiv, ilgjx__qwkx, mxi__hep = args
        zsip__exadd = signature.return_type
        uwyj__qegmy = cgutils.create_struct_proxy(zsip__exadd)(context, builder
            )
        uwyj__qegmy.obj = fhb__xpimr
        uwyj__qegmy.window = vgr__kzm
        uwyj__qegmy.min_periods = gljfg__fgiv
        uwyj__qegmy.center = ilgjx__qwkx
        context.nrt.incref(builder, signature.args[0], fhb__xpimr)
        context.nrt.incref(builder, signature.args[1], vgr__kzm)
        context.nrt.incref(builder, signature.args[2], gljfg__fgiv)
        context.nrt.incref(builder, signature.args[3], ilgjx__qwkx)
        return uwyj__qegmy._getvalue()
    on = get_literal_value(on_type)
    if isinstance(obj_type, SeriesType):
        selection = None
    elif isinstance(obj_type, DataFrameType):
        selection = obj_type.columns
    else:
        assert isinstance(obj_type, DataFrameGroupByType
            ), f'invalid obj type for rolling: {obj_type}'
        selection = obj_type.selection
    zsip__exadd = RollingType(obj_type, window_type, on, selection, False)
    return zsip__exadd(obj_type, window_type, min_periods_type, center_type,
        on_type), codegen


def _handle_default_min_periods(min_periods, window):
    return min_periods


@overload(_handle_default_min_periods)
def overload_handle_default_min_periods(min_periods, window):
    if is_overload_none(min_periods):
        if isinstance(window, types.Integer):
            return lambda min_periods, window: window
        else:
            return lambda min_periods, window: 1
    else:
        return lambda min_periods, window: min_periods


def _gen_df_rolling_out_data(rolling):
    zrg__qvyz = not isinstance(rolling.window_type, types.Integer)
    hsyv__luzw = 'variable' if zrg__qvyz else 'fixed'
    vah__vjw = 'None'
    if zrg__qvyz:
        vah__vjw = ('bodo.utils.conversion.index_to_array(index)' if 
            rolling.on is None else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {rolling.obj_type.columns.index(rolling.on)})'
            )
    uny__sskyp = []
    quf__hnrvc = 'on_arr, ' if zrg__qvyz else ''
    if isinstance(rolling.obj_type, SeriesType):
        return (
            f'bodo.hiframes.rolling.rolling_{hsyv__luzw}(bodo.hiframes.pd_series_ext.get_series_data(df), {quf__hnrvc}index_arr, window, minp, center, func, raw)'
            , vah__vjw, rolling.selection)
    assert isinstance(rolling.obj_type, DataFrameType
        ), 'expected df in rolling obj'
    ldox__ddkpm = rolling.obj_type.data
    out_cols = []
    for vkjzq__agtg in rolling.selection:
        ymje__cynh = rolling.obj_type.columns.index(vkjzq__agtg)
        if vkjzq__agtg == rolling.on:
            if len(rolling.selection) == 2 and rolling.series_select:
                continue
            ujlb__wgqm = (
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {ymje__cynh})'
                )
            out_cols.append(vkjzq__agtg)
        else:
            if not isinstance(ldox__ddkpm[ymje__cynh].dtype, (types.Boolean,
                types.Number)):
                continue
            ujlb__wgqm = (
                f'bodo.hiframes.rolling.rolling_{hsyv__luzw}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {ymje__cynh}), {quf__hnrvc}index_arr, window, minp, center, func, raw)'
                )
            out_cols.append(vkjzq__agtg)
        uny__sskyp.append(ujlb__wgqm)
    return ', '.join(uny__sskyp), vah__vjw, tuple(out_cols)


@overload_method(RollingType, 'apply', inline='always', no_unliteral=True)
def overload_rolling_apply(rolling, func, raw=False, engine=None,
    engine_kwargs=None, args=None, kwargs=None):
    dnjkt__eewu = dict(engine=engine, engine_kwargs=engine_kwargs, args=
        args, kwargs=kwargs)
    pzm__bbjae = dict(engine=None, engine_kwargs=None, args=None, kwargs=None)
    check_unsupported_args('Rolling.apply', dnjkt__eewu, pzm__bbjae,
        package_name='pandas', module_name='Window')
    if not is_const_func_type(func):
        raise BodoError(
            f"Rolling.apply(): 'func' parameter must be a function, not {func} (builtin functions not supported yet)."
            )
    if not is_overload_bool(raw):
        raise BodoError(
            f"Rolling.apply(): 'raw' parameter must be bool, not {raw}.")
    return _gen_rolling_impl(rolling, 'apply')


@overload_method(DataFrameGroupByType, 'rolling', inline='always',
    no_unliteral=True)
def groupby_rolling_overload(grp, window, min_periods=None, center=False,
    win_type=None, on=None, axis=0, closed=None, method='single'):
    dnjkt__eewu = dict(win_type=win_type, axis=axis, closed=closed, method=
        method)
    pzm__bbjae = dict(win_type=None, axis=0, closed=None, method='single')
    check_unsupported_args('GroupBy.rolling', dnjkt__eewu, pzm__bbjae,
        package_name='pandas', module_name='Window')
    _validate_rolling_args(grp, window, min_periods, center, on)

    def _impl(grp, window, min_periods=None, center=False, win_type=None,
        on=None, axis=0, closed=None, method='single'):
        min_periods = _handle_default_min_periods(min_periods, window)
        return bodo.hiframes.pd_rolling_ext.init_rolling(grp, window,
            min_periods, center, on)
    return _impl


def _gen_rolling_impl(rolling, fname, other=None):
    if isinstance(rolling.obj_type, DataFrameGroupByType):
        boila__edrs = f'def impl(rolling, {_get_rolling_func_args(fname)}):\n'
        sty__tfsac = f"'{rolling.on}'" if isinstance(rolling.on, str
            ) else f'{rolling.on}'
        selection = ''
        if rolling.explicit_select:
            selection = '[{}]'.format(', '.join(f"'{eqcz__tfg}'" if
                isinstance(eqcz__tfg, str) else f'{eqcz__tfg}' for
                eqcz__tfg in rolling.selection if eqcz__tfg != rolling.on))
        cexu__ueqc = yxsz__zfltd = ''
        if fname == 'apply':
            cexu__ueqc = 'func, raw, args, kwargs'
            yxsz__zfltd = 'func, raw, None, None, args, kwargs'
        if fname == 'corr':
            cexu__ueqc = yxsz__zfltd = 'other, pairwise'
        if fname == 'cov':
            cexu__ueqc = yxsz__zfltd = 'other, pairwise, ddof'
        wwusr__sskn = (
            f'lambda df, window, minp, center, {cexu__ueqc}: bodo.hiframes.pd_rolling_ext.init_rolling(df, window, minp, center, {sty__tfsac}){selection}.{fname}({yxsz__zfltd})'
            )
        boila__edrs += f"""  return rolling.obj.apply({wwusr__sskn}, rolling.window, rolling.min_periods, rolling.center, {cexu__ueqc})
"""
        xmom__lkkxz = {}
        exec(boila__edrs, {'bodo': bodo}, xmom__lkkxz)
        impl = xmom__lkkxz['impl']
        return impl
    xipt__qpvgf = isinstance(rolling.obj_type, SeriesType)
    if fname in ('corr', 'cov'):
        out_cols = None if xipt__qpvgf else _get_corr_cov_out_cols(rolling,
            other, fname)
        df_cols = None if xipt__qpvgf else rolling.obj_type.columns
        other_cols = None if xipt__qpvgf else other.columns
        uny__sskyp, vah__vjw = _gen_corr_cov_out_data(out_cols, df_cols,
            other_cols, rolling.window_type, fname)
    else:
        uny__sskyp, vah__vjw, out_cols = _gen_df_rolling_out_data(rolling)
    rnh__orrvf = xipt__qpvgf or len(rolling.selection) == (1 if rolling.on is
        None else 2) and rolling.series_select
    autx__tmczd = f'def impl(rolling, {_get_rolling_func_args(fname)}):\n'
    autx__tmczd += '  df = rolling.obj\n'
    autx__tmczd += '  index = {}\n'.format(
        'bodo.hiframes.pd_series_ext.get_series_index(df)' if xipt__qpvgf else
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)')
    hslyd__ohag = 'None'
    if xipt__qpvgf:
        hslyd__ohag = 'bodo.hiframes.pd_series_ext.get_series_name(df)'
    elif rnh__orrvf:
        vkjzq__agtg = (set(out_cols) - set([rolling.on])).pop()
        hslyd__ohag = f"'{vkjzq__agtg}'" if isinstance(vkjzq__agtg, str
            ) else str(vkjzq__agtg)
    autx__tmczd += f'  name = {hslyd__ohag}\n'
    autx__tmczd += '  window = rolling.window\n'
    autx__tmczd += '  center = rolling.center\n'
    autx__tmczd += '  minp = rolling.min_periods\n'
    autx__tmczd += f'  on_arr = {vah__vjw}\n'
    if fname == 'apply':
        autx__tmczd += (
            f'  index_arr = bodo.utils.conversion.index_to_array(index)\n')
    else:
        autx__tmczd += f"  func = '{fname}'\n"
        autx__tmczd += f'  index_arr = None\n'
        autx__tmczd += f'  raw = False\n'
    if rnh__orrvf:
        autx__tmczd += (
            f'  return bodo.hiframes.pd_series_ext.init_series({uny__sskyp}, index, name)'
            )
        xmom__lkkxz = {}
        cgjv__kma = {'bodo': bodo}
        exec(autx__tmczd, cgjv__kma, xmom__lkkxz)
        impl = xmom__lkkxz['impl']
        return impl
    return bodo.hiframes.dataframe_impl._gen_init_df(autx__tmczd, out_cols,
        uny__sskyp)


def _get_rolling_func_args(fname):
    if fname == 'apply':
        return (
            'func, raw=False, engine=None, engine_kwargs=None, args=None, kwargs=None\n'
            )
    elif fname == 'corr':
        return 'other=None, pairwise=None, ddof=1\n'
    elif fname == 'cov':
        return 'other=None, pairwise=None, ddof=1\n'
    return ''


def create_rolling_overload(fname):

    def overload_rolling_func(rolling):
        return _gen_rolling_impl(rolling, fname)
    return overload_rolling_func


def _install_rolling_methods():
    for fname in supported_rolling_funcs:
        if fname in ('apply', 'corr', 'cov'):
            continue
        kjxh__daauu = create_rolling_overload(fname)
        overload_method(RollingType, fname, inline='always', no_unliteral=True
            )(kjxh__daauu)


def _install_rolling_unsupported_methods():
    for fname in unsupported_rolling_methods:
        overload_method(RollingType, fname, no_unliteral=True)(
            create_unsupported_overload(
            f'pandas.core.window.rolling.Rolling.{fname}()'))


_install_rolling_methods()
_install_rolling_unsupported_methods()


def _get_corr_cov_out_cols(rolling, other, func_name):
    if not isinstance(other, DataFrameType):
        raise_bodo_error(
            f"DataFrame.rolling.{func_name}(): requires providing a DataFrame for 'other'"
            )
    cagop__kml = rolling.selection
    if rolling.on is not None:
        raise BodoError(
            f'variable window rolling {func_name} not supported yet.')
    out_cols = tuple(sorted(set(cagop__kml) | set(other.columns), key=lambda
        k: str(k)))
    return out_cols


def _gen_corr_cov_out_data(out_cols, df_cols, other_cols, window_type,
    func_name):
    zrg__qvyz = not isinstance(window_type, types.Integer)
    vah__vjw = 'None'
    if zrg__qvyz:
        vah__vjw = 'bodo.utils.conversion.index_to_array(index)'
    quf__hnrvc = 'on_arr, ' if zrg__qvyz else ''
    uny__sskyp = []
    if out_cols is None:
        return (
            f'bodo.hiframes.rolling.rolling_{func_name}(bodo.hiframes.pd_series_ext.get_series_data(df), bodo.hiframes.pd_series_ext.get_series_data(other), {quf__hnrvc}window, minp, center)'
            , vah__vjw)
    for vkjzq__agtg in out_cols:
        if vkjzq__agtg in df_cols and vkjzq__agtg in other_cols:
            oga__gbd = df_cols.index(vkjzq__agtg)
            bvnu__wruqr = other_cols.index(vkjzq__agtg)
            ujlb__wgqm = (
                f'bodo.hiframes.rolling.rolling_{func_name}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {oga__gbd}), bodo.hiframes.pd_dataframe_ext.get_dataframe_data(other, {bvnu__wruqr}), {quf__hnrvc}window, minp, center)'
                )
        else:
            ujlb__wgqm = 'np.full(len(df), np.nan)'
        uny__sskyp.append(ujlb__wgqm)
    return ', '.join(uny__sskyp), vah__vjw


@overload_method(RollingType, 'corr', inline='always', no_unliteral=True)
def overload_rolling_corr(rolling, other=None, pairwise=None, ddof=1):
    tugxm__udmd = {'pairwise': pairwise, 'ddof': ddof}
    ebr__prr = {'pairwise': None, 'ddof': 1}
    check_unsupported_args('pandas.core.window.rolling.Rolling.corr',
        tugxm__udmd, ebr__prr, package_name='pandas', module_name='Window')
    return _gen_rolling_impl(rolling, 'corr', other)


@overload_method(RollingType, 'cov', inline='always', no_unliteral=True)
def overload_rolling_cov(rolling, other=None, pairwise=None, ddof=1):
    tugxm__udmd = {'ddof': ddof, 'pairwise': pairwise}
    ebr__prr = {'ddof': 1, 'pairwise': None}
    check_unsupported_args('pandas.core.window.rolling.Rolling.cov',
        tugxm__udmd, ebr__prr, package_name='pandas', module_name='Window')
    return _gen_rolling_impl(rolling, 'cov', other)


@infer
class GetItemDataFrameRolling2(AbstractTemplate):
    key = 'static_getitem'

    def generic(self, args, kws):
        rolling, pfmp__nhezi = args
        if isinstance(rolling, RollingType):
            cagop__kml = rolling.obj_type.selection if isinstance(rolling.
                obj_type, DataFrameGroupByType) else rolling.obj_type.columns
            series_select = False
            if isinstance(pfmp__nhezi, (tuple, list)):
                if len(set(pfmp__nhezi).difference(set(cagop__kml))) > 0:
                    raise_bodo_error(
                        'rolling: selected column {} not found in dataframe'
                        .format(set(pfmp__nhezi).difference(set(cagop__kml))))
                selection = list(pfmp__nhezi)
            else:
                if pfmp__nhezi not in cagop__kml:
                    raise_bodo_error(
                        'rolling: selected column {} not found in dataframe'
                        .format(pfmp__nhezi))
                selection = [pfmp__nhezi]
                series_select = True
            if rolling.on is not None:
                selection.append(rolling.on)
            veok__paqir = RollingType(rolling.obj_type, rolling.window_type,
                rolling.on, tuple(selection), True, series_select)
            return signature(veok__paqir, *args)


@lower_builtin('static_getitem', RollingType, types.Any)
def static_getitem_df_groupby(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@infer_getattr
class RollingAttribute(AttributeTemplate):
    key = RollingType

    def generic_resolve(self, rolling, attr):
        cagop__kml = ()
        if isinstance(rolling.obj_type, DataFrameGroupByType):
            cagop__kml = rolling.obj_type.selection
        if isinstance(rolling.obj_type, DataFrameType):
            cagop__kml = rolling.obj_type.columns
        if attr in cagop__kml:
            return RollingType(rolling.obj_type, rolling.window_type,
                rolling.on, (attr,) if rolling.on is None else (attr,
                rolling.on), True, True)


def _validate_rolling_args(obj, window, min_periods, center, on):
    assert isinstance(obj, (SeriesType, DataFrameType, DataFrameGroupByType)
        ), 'invalid rolling obj'
    func_name = 'Series' if isinstance(obj, SeriesType
        ) else 'DataFrame' if isinstance(obj, DataFrameType
        ) else 'DataFrameGroupBy'
    if not (is_overload_int(window) or is_overload_constant_str(window) or 
        window == bodo.string_type or window in (pd_timedelta_type,
        datetime_timedelta_type)):
        raise BodoError(
            f"{func_name}.rolling(): 'window' should be int or time offset (str, pd.Timedelta, datetime.timedelta), not {window}"
            )
    if not is_overload_bool(center):
        raise BodoError(
            f'{func_name}.rolling(): center must be a boolean, not {center}')
    if not (is_overload_none(min_periods) or isinstance(min_periods, types.
        Integer)):
        raise BodoError(
            f'{func_name}.rolling(): min_periods must be an integer, not {min_periods}'
            )
    if isinstance(obj, SeriesType) and not is_overload_none(on):
        raise BodoError(
            f"{func_name}.rolling(): 'on' not supported for Series yet (can use a DataFrame instead)."
            )
    dpslz__cwesy = obj.columns if isinstance(obj, DataFrameType
        ) else obj.df_type.columns if isinstance(obj, DataFrameGroupByType
        ) else []
    ldox__ddkpm = [obj.data] if isinstance(obj, SeriesType
        ) else obj.data if isinstance(obj, DataFrameType) else obj.df_type.data
    if not is_overload_none(on) and (not is_literal_type(on) or 
        get_literal_value(on) not in dpslz__cwesy):
        raise BodoError(
            f"{func_name}.rolling(): 'on' should be a constant column name.")
    if not is_overload_none(on):
        enb__lok = ldox__ddkpm[dpslz__cwesy.index(get_literal_value(on))]
        if not isinstance(enb__lok, types.Array
            ) or enb__lok.dtype != bodo.datetime64ns:
            raise BodoError(
                f"{func_name}.rolling(): 'on' column should have datetime64 data."
                )
    if not any(isinstance(hiv__viklq.dtype, (types.Boolean, types.Number)) for
        hiv__viklq in ldox__ddkpm):
        raise BodoError(f'{func_name}.rolling(): No numeric types to aggregate'
            )
