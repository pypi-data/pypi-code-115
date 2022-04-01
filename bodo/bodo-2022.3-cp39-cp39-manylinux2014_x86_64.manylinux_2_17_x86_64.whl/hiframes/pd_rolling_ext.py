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
            zhh__bcye = 'Series'
        else:
            zhh__bcye = 'DataFrame'
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(obj_type,
            f'{zhh__bcye}.rolling()')
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
        hoedk__jkzx = [('obj', fe_type.obj_type), ('window', fe_type.
            window_type), ('min_periods', types.int64), ('center', types.bool_)
            ]
        super(RollingModel, self).__init__(dmm, fe_type, hoedk__jkzx)


make_attribute_wrapper(RollingType, 'obj', 'obj')
make_attribute_wrapper(RollingType, 'window', 'window')
make_attribute_wrapper(RollingType, 'center', 'center')
make_attribute_wrapper(RollingType, 'min_periods', 'min_periods')


@overload_method(DataFrameType, 'rolling', inline='always', no_unliteral=True)
def df_rolling_overload(df, window, min_periods=None, center=False,
    win_type=None, on=None, axis=0, closed=None):
    check_runtime_cols_unsupported(df, 'DataFrame.rolling()')
    mjptp__hwjro = dict(win_type=win_type, axis=axis, closed=closed)
    fxz__qqc = dict(win_type=None, axis=0, closed=None)
    check_unsupported_args('DataFrame.rolling', mjptp__hwjro, fxz__qqc,
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
    mjptp__hwjro = dict(win_type=win_type, axis=axis, closed=closed)
    fxz__qqc = dict(win_type=None, axis=0, closed=None)
    check_unsupported_args('Series.rolling', mjptp__hwjro, fxz__qqc,
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
        tbtzb__vemu, zbof__hijci, busnv__qwmy, mabe__zoy, hduib__rmx = args
        ayo__pdy = signature.return_type
        axhz__mxo = cgutils.create_struct_proxy(ayo__pdy)(context, builder)
        axhz__mxo.obj = tbtzb__vemu
        axhz__mxo.window = zbof__hijci
        axhz__mxo.min_periods = busnv__qwmy
        axhz__mxo.center = mabe__zoy
        context.nrt.incref(builder, signature.args[0], tbtzb__vemu)
        context.nrt.incref(builder, signature.args[1], zbof__hijci)
        context.nrt.incref(builder, signature.args[2], busnv__qwmy)
        context.nrt.incref(builder, signature.args[3], mabe__zoy)
        return axhz__mxo._getvalue()
    on = get_literal_value(on_type)
    if isinstance(obj_type, SeriesType):
        selection = None
    elif isinstance(obj_type, DataFrameType):
        selection = obj_type.columns
    else:
        assert isinstance(obj_type, DataFrameGroupByType
            ), f'invalid obj type for rolling: {obj_type}'
        selection = obj_type.selection
    ayo__pdy = RollingType(obj_type, window_type, on, selection, False)
    return ayo__pdy(obj_type, window_type, min_periods_type, center_type,
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
    ramtv__rae = not isinstance(rolling.window_type, types.Integer)
    ymd__qlwq = 'variable' if ramtv__rae else 'fixed'
    tjdss__cjpzh = 'None'
    if ramtv__rae:
        tjdss__cjpzh = ('bodo.utils.conversion.index_to_array(index)' if 
            rolling.on is None else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {rolling.obj_type.columns.index(rolling.on)})'
            )
    jywi__epgxw = []
    lvw__qwgd = 'on_arr, ' if ramtv__rae else ''
    if isinstance(rolling.obj_type, SeriesType):
        return (
            f'bodo.hiframes.rolling.rolling_{ymd__qlwq}(bodo.hiframes.pd_series_ext.get_series_data(df), {lvw__qwgd}index_arr, window, minp, center, func, raw)'
            , tjdss__cjpzh, rolling.selection)
    assert isinstance(rolling.obj_type, DataFrameType
        ), 'expected df in rolling obj'
    acncc__npfx = rolling.obj_type.data
    out_cols = []
    for grepb__nzjdz in rolling.selection:
        qeb__lyx = rolling.obj_type.columns.index(grepb__nzjdz)
        if grepb__nzjdz == rolling.on:
            if len(rolling.selection) == 2 and rolling.series_select:
                continue
            hlrkf__ozbr = (
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {qeb__lyx})'
                )
            out_cols.append(grepb__nzjdz)
        else:
            if not isinstance(acncc__npfx[qeb__lyx].dtype, (types.Boolean,
                types.Number)):
                continue
            hlrkf__ozbr = (
                f'bodo.hiframes.rolling.rolling_{ymd__qlwq}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {qeb__lyx}), {lvw__qwgd}index_arr, window, minp, center, func, raw)'
                )
            out_cols.append(grepb__nzjdz)
        jywi__epgxw.append(hlrkf__ozbr)
    return ', '.join(jywi__epgxw), tjdss__cjpzh, tuple(out_cols)


@overload_method(RollingType, 'apply', inline='always', no_unliteral=True)
def overload_rolling_apply(rolling, func, raw=False, engine=None,
    engine_kwargs=None, args=None, kwargs=None):
    mjptp__hwjro = dict(engine=engine, engine_kwargs=engine_kwargs, args=
        args, kwargs=kwargs)
    fxz__qqc = dict(engine=None, engine_kwargs=None, args=None, kwargs=None)
    check_unsupported_args('Rolling.apply', mjptp__hwjro, fxz__qqc,
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
    mjptp__hwjro = dict(win_type=win_type, axis=axis, closed=closed, method
        =method)
    fxz__qqc = dict(win_type=None, axis=0, closed=None, method='single')
    check_unsupported_args('GroupBy.rolling', mjptp__hwjro, fxz__qqc,
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
        vwep__tib = f'def impl(rolling, {_get_rolling_func_args(fname)}):\n'
        mdruj__lzqd = f"'{rolling.on}'" if isinstance(rolling.on, str
            ) else f'{rolling.on}'
        selection = ''
        if rolling.explicit_select:
            selection = '[{}]'.format(', '.join(f"'{oln__hsqug}'" if
                isinstance(oln__hsqug, str) else f'{oln__hsqug}' for
                oln__hsqug in rolling.selection if oln__hsqug != rolling.on))
        ngxd__rxv = jeo__ucg = ''
        if fname == 'apply':
            ngxd__rxv = 'func, raw, args, kwargs'
            jeo__ucg = 'func, raw, None, None, args, kwargs'
        if fname == 'corr':
            ngxd__rxv = jeo__ucg = 'other, pairwise'
        if fname == 'cov':
            ngxd__rxv = jeo__ucg = 'other, pairwise, ddof'
        uxl__gxonb = (
            f'lambda df, window, minp, center, {ngxd__rxv}: bodo.hiframes.pd_rolling_ext.init_rolling(df, window, minp, center, {mdruj__lzqd}){selection}.{fname}({jeo__ucg})'
            )
        vwep__tib += f"""  return rolling.obj.apply({uxl__gxonb}, rolling.window, rolling.min_periods, rolling.center, {ngxd__rxv})
"""
        tewx__yxbf = {}
        exec(vwep__tib, {'bodo': bodo}, tewx__yxbf)
        impl = tewx__yxbf['impl']
        return impl
    ouroo__qthbn = isinstance(rolling.obj_type, SeriesType)
    if fname in ('corr', 'cov'):
        out_cols = None if ouroo__qthbn else _get_corr_cov_out_cols(rolling,
            other, fname)
        df_cols = None if ouroo__qthbn else rolling.obj_type.columns
        other_cols = None if ouroo__qthbn else other.columns
        jywi__epgxw, tjdss__cjpzh = _gen_corr_cov_out_data(out_cols,
            df_cols, other_cols, rolling.window_type, fname)
    else:
        jywi__epgxw, tjdss__cjpzh, out_cols = _gen_df_rolling_out_data(rolling)
    hxrtm__yux = ouroo__qthbn or len(rolling.selection) == (1 if rolling.on is
        None else 2) and rolling.series_select
    prduo__mtk = f'def impl(rolling, {_get_rolling_func_args(fname)}):\n'
    prduo__mtk += '  df = rolling.obj\n'
    prduo__mtk += '  index = {}\n'.format(
        'bodo.hiframes.pd_series_ext.get_series_index(df)' if ouroo__qthbn else
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)')
    zhh__bcye = 'None'
    if ouroo__qthbn:
        zhh__bcye = 'bodo.hiframes.pd_series_ext.get_series_name(df)'
    elif hxrtm__yux:
        grepb__nzjdz = (set(out_cols) - set([rolling.on])).pop()
        zhh__bcye = f"'{grepb__nzjdz}'" if isinstance(grepb__nzjdz, str
            ) else str(grepb__nzjdz)
    prduo__mtk += f'  name = {zhh__bcye}\n'
    prduo__mtk += '  window = rolling.window\n'
    prduo__mtk += '  center = rolling.center\n'
    prduo__mtk += '  minp = rolling.min_periods\n'
    prduo__mtk += f'  on_arr = {tjdss__cjpzh}\n'
    if fname == 'apply':
        prduo__mtk += (
            f'  index_arr = bodo.utils.conversion.index_to_array(index)\n')
    else:
        prduo__mtk += f"  func = '{fname}'\n"
        prduo__mtk += f'  index_arr = None\n'
        prduo__mtk += f'  raw = False\n'
    if hxrtm__yux:
        prduo__mtk += (
            f'  return bodo.hiframes.pd_series_ext.init_series({jywi__epgxw}, index, name)'
            )
        tewx__yxbf = {}
        uxedr__mxw = {'bodo': bodo}
        exec(prduo__mtk, uxedr__mxw, tewx__yxbf)
        impl = tewx__yxbf['impl']
        return impl
    return bodo.hiframes.dataframe_impl._gen_init_df(prduo__mtk, out_cols,
        jywi__epgxw)


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
        qtvvy__ril = create_rolling_overload(fname)
        overload_method(RollingType, fname, inline='always', no_unliteral=True
            )(qtvvy__ril)


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
    hvn__nkan = rolling.selection
    if rolling.on is not None:
        raise BodoError(
            f'variable window rolling {func_name} not supported yet.')
    out_cols = tuple(sorted(set(hvn__nkan) | set(other.columns), key=lambda
        k: str(k)))
    return out_cols


def _gen_corr_cov_out_data(out_cols, df_cols, other_cols, window_type,
    func_name):
    ramtv__rae = not isinstance(window_type, types.Integer)
    tjdss__cjpzh = 'None'
    if ramtv__rae:
        tjdss__cjpzh = 'bodo.utils.conversion.index_to_array(index)'
    lvw__qwgd = 'on_arr, ' if ramtv__rae else ''
    jywi__epgxw = []
    if out_cols is None:
        return (
            f'bodo.hiframes.rolling.rolling_{func_name}(bodo.hiframes.pd_series_ext.get_series_data(df), bodo.hiframes.pd_series_ext.get_series_data(other), {lvw__qwgd}window, minp, center)'
            , tjdss__cjpzh)
    for grepb__nzjdz in out_cols:
        if grepb__nzjdz in df_cols and grepb__nzjdz in other_cols:
            oiw__ntm = df_cols.index(grepb__nzjdz)
            eedt__kkd = other_cols.index(grepb__nzjdz)
            hlrkf__ozbr = (
                f'bodo.hiframes.rolling.rolling_{func_name}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {oiw__ntm}), bodo.hiframes.pd_dataframe_ext.get_dataframe_data(other, {eedt__kkd}), {lvw__qwgd}window, minp, center)'
                )
        else:
            hlrkf__ozbr = 'np.full(len(df), np.nan)'
        jywi__epgxw.append(hlrkf__ozbr)
    return ', '.join(jywi__epgxw), tjdss__cjpzh


@overload_method(RollingType, 'corr', inline='always', no_unliteral=True)
def overload_rolling_corr(rolling, other=None, pairwise=None, ddof=1):
    nzrk__zteek = {'pairwise': pairwise, 'ddof': ddof}
    kypb__dmcnj = {'pairwise': None, 'ddof': 1}
    check_unsupported_args('pandas.core.window.rolling.Rolling.corr',
        nzrk__zteek, kypb__dmcnj, package_name='pandas', module_name='Window')
    return _gen_rolling_impl(rolling, 'corr', other)


@overload_method(RollingType, 'cov', inline='always', no_unliteral=True)
def overload_rolling_cov(rolling, other=None, pairwise=None, ddof=1):
    nzrk__zteek = {'ddof': ddof, 'pairwise': pairwise}
    kypb__dmcnj = {'ddof': 1, 'pairwise': None}
    check_unsupported_args('pandas.core.window.rolling.Rolling.cov',
        nzrk__zteek, kypb__dmcnj, package_name='pandas', module_name='Window')
    return _gen_rolling_impl(rolling, 'cov', other)


@infer
class GetItemDataFrameRolling2(AbstractTemplate):
    key = 'static_getitem'

    def generic(self, args, kws):
        rolling, ufc__vbwah = args
        if isinstance(rolling, RollingType):
            hvn__nkan = rolling.obj_type.selection if isinstance(rolling.
                obj_type, DataFrameGroupByType) else rolling.obj_type.columns
            series_select = False
            if isinstance(ufc__vbwah, (tuple, list)):
                if len(set(ufc__vbwah).difference(set(hvn__nkan))) > 0:
                    raise_bodo_error(
                        'rolling: selected column {} not found in dataframe'
                        .format(set(ufc__vbwah).difference(set(hvn__nkan))))
                selection = list(ufc__vbwah)
            else:
                if ufc__vbwah not in hvn__nkan:
                    raise_bodo_error(
                        'rolling: selected column {} not found in dataframe'
                        .format(ufc__vbwah))
                selection = [ufc__vbwah]
                series_select = True
            if rolling.on is not None:
                selection.append(rolling.on)
            tdvtb__akdy = RollingType(rolling.obj_type, rolling.window_type,
                rolling.on, tuple(selection), True, series_select)
            return signature(tdvtb__akdy, *args)


@lower_builtin('static_getitem', RollingType, types.Any)
def static_getitem_df_groupby(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@infer_getattr
class RollingAttribute(AttributeTemplate):
    key = RollingType

    def generic_resolve(self, rolling, attr):
        hvn__nkan = ()
        if isinstance(rolling.obj_type, DataFrameGroupByType):
            hvn__nkan = rolling.obj_type.selection
        if isinstance(rolling.obj_type, DataFrameType):
            hvn__nkan = rolling.obj_type.columns
        if attr in hvn__nkan:
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
    ignib__pxf = obj.columns if isinstance(obj, DataFrameType
        ) else obj.df_type.columns if isinstance(obj, DataFrameGroupByType
        ) else []
    acncc__npfx = [obj.data] if isinstance(obj, SeriesType
        ) else obj.data if isinstance(obj, DataFrameType) else obj.df_type.data
    if not is_overload_none(on) and (not is_literal_type(on) or 
        get_literal_value(on) not in ignib__pxf):
        raise BodoError(
            f"{func_name}.rolling(): 'on' should be a constant column name.")
    if not is_overload_none(on):
        ttex__kizax = acncc__npfx[ignib__pxf.index(get_literal_value(on))]
        if not isinstance(ttex__kizax, types.Array
            ) or ttex__kizax.dtype != bodo.datetime64ns:
            raise BodoError(
                f"{func_name}.rolling(): 'on' column should have datetime64 data."
                )
    if not any(isinstance(tdwvo__mwhcm.dtype, (types.Boolean, types.Number)
        ) for tdwvo__mwhcm in acncc__npfx):
        raise BodoError(f'{func_name}.rolling(): No numeric types to aggregate'
            )
