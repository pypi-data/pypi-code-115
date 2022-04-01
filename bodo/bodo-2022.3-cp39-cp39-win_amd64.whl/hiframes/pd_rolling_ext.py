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
            wyf__lsn = 'Series'
        else:
            wyf__lsn = 'DataFrame'
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(obj_type,
            f'{wyf__lsn}.rolling()')
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
        zeou__wlv = [('obj', fe_type.obj_type), ('window', fe_type.
            window_type), ('min_periods', types.int64), ('center', types.bool_)
            ]
        super(RollingModel, self).__init__(dmm, fe_type, zeou__wlv)


make_attribute_wrapper(RollingType, 'obj', 'obj')
make_attribute_wrapper(RollingType, 'window', 'window')
make_attribute_wrapper(RollingType, 'center', 'center')
make_attribute_wrapper(RollingType, 'min_periods', 'min_periods')


@overload_method(DataFrameType, 'rolling', inline='always', no_unliteral=True)
def df_rolling_overload(df, window, min_periods=None, center=False,
    win_type=None, on=None, axis=0, closed=None):
    check_runtime_cols_unsupported(df, 'DataFrame.rolling()')
    egok__bje = dict(win_type=win_type, axis=axis, closed=closed)
    gxxhf__tnm = dict(win_type=None, axis=0, closed=None)
    check_unsupported_args('DataFrame.rolling', egok__bje, gxxhf__tnm,
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
    egok__bje = dict(win_type=win_type, axis=axis, closed=closed)
    gxxhf__tnm = dict(win_type=None, axis=0, closed=None)
    check_unsupported_args('Series.rolling', egok__bje, gxxhf__tnm,
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
        efl__flv, qmi__kbu, kzao__wvfje, hiv__fehd, qbs__gqoto = args
        scap__dlf = signature.return_type
        avpu__fad = cgutils.create_struct_proxy(scap__dlf)(context, builder)
        avpu__fad.obj = efl__flv
        avpu__fad.window = qmi__kbu
        avpu__fad.min_periods = kzao__wvfje
        avpu__fad.center = hiv__fehd
        context.nrt.incref(builder, signature.args[0], efl__flv)
        context.nrt.incref(builder, signature.args[1], qmi__kbu)
        context.nrt.incref(builder, signature.args[2], kzao__wvfje)
        context.nrt.incref(builder, signature.args[3], hiv__fehd)
        return avpu__fad._getvalue()
    on = get_literal_value(on_type)
    if isinstance(obj_type, SeriesType):
        selection = None
    elif isinstance(obj_type, DataFrameType):
        selection = obj_type.columns
    else:
        assert isinstance(obj_type, DataFrameGroupByType
            ), f'invalid obj type for rolling: {obj_type}'
        selection = obj_type.selection
    scap__dlf = RollingType(obj_type, window_type, on, selection, False)
    return scap__dlf(obj_type, window_type, min_periods_type, center_type,
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
    smons__lakod = not isinstance(rolling.window_type, types.Integer)
    ljxx__izoz = 'variable' if smons__lakod else 'fixed'
    kfnq__otwo = 'None'
    if smons__lakod:
        kfnq__otwo = ('bodo.utils.conversion.index_to_array(index)' if 
            rolling.on is None else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {rolling.obj_type.columns.index(rolling.on)})'
            )
    bpqnf__ezi = []
    zxbca__fgasm = 'on_arr, ' if smons__lakod else ''
    if isinstance(rolling.obj_type, SeriesType):
        return (
            f'bodo.hiframes.rolling.rolling_{ljxx__izoz}(bodo.hiframes.pd_series_ext.get_series_data(df), {zxbca__fgasm}index_arr, window, minp, center, func, raw)'
            , kfnq__otwo, rolling.selection)
    assert isinstance(rolling.obj_type, DataFrameType
        ), 'expected df in rolling obj'
    jlpau__nkq = rolling.obj_type.data
    out_cols = []
    for frdlk__sik in rolling.selection:
        vvp__zito = rolling.obj_type.columns.index(frdlk__sik)
        if frdlk__sik == rolling.on:
            if len(rolling.selection) == 2 and rolling.series_select:
                continue
            ckshy__ocm = (
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {vvp__zito})'
                )
            out_cols.append(frdlk__sik)
        else:
            if not isinstance(jlpau__nkq[vvp__zito].dtype, (types.Boolean,
                types.Number)):
                continue
            ckshy__ocm = (
                f'bodo.hiframes.rolling.rolling_{ljxx__izoz}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {vvp__zito}), {zxbca__fgasm}index_arr, window, minp, center, func, raw)'
                )
            out_cols.append(frdlk__sik)
        bpqnf__ezi.append(ckshy__ocm)
    return ', '.join(bpqnf__ezi), kfnq__otwo, tuple(out_cols)


@overload_method(RollingType, 'apply', inline='always', no_unliteral=True)
def overload_rolling_apply(rolling, func, raw=False, engine=None,
    engine_kwargs=None, args=None, kwargs=None):
    egok__bje = dict(engine=engine, engine_kwargs=engine_kwargs, args=args,
        kwargs=kwargs)
    gxxhf__tnm = dict(engine=None, engine_kwargs=None, args=None, kwargs=None)
    check_unsupported_args('Rolling.apply', egok__bje, gxxhf__tnm,
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
    egok__bje = dict(win_type=win_type, axis=axis, closed=closed, method=method
        )
    gxxhf__tnm = dict(win_type=None, axis=0, closed=None, method='single')
    check_unsupported_args('GroupBy.rolling', egok__bje, gxxhf__tnm,
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
        bbr__xatlv = f'def impl(rolling, {_get_rolling_func_args(fname)}):\n'
        fwo__syk = f"'{rolling.on}'" if isinstance(rolling.on, str
            ) else f'{rolling.on}'
        selection = ''
        if rolling.explicit_select:
            selection = '[{}]'.format(', '.join(f"'{imoe__vfljh}'" if
                isinstance(imoe__vfljh, str) else f'{imoe__vfljh}' for
                imoe__vfljh in rolling.selection if imoe__vfljh != rolling.on))
        qedj__sbxtj = jjy__vyd = ''
        if fname == 'apply':
            qedj__sbxtj = 'func, raw, args, kwargs'
            jjy__vyd = 'func, raw, None, None, args, kwargs'
        if fname == 'corr':
            qedj__sbxtj = jjy__vyd = 'other, pairwise'
        if fname == 'cov':
            qedj__sbxtj = jjy__vyd = 'other, pairwise, ddof'
        sxosz__ynno = (
            f'lambda df, window, minp, center, {qedj__sbxtj}: bodo.hiframes.pd_rolling_ext.init_rolling(df, window, minp, center, {fwo__syk}){selection}.{fname}({jjy__vyd})'
            )
        bbr__xatlv += f"""  return rolling.obj.apply({sxosz__ynno}, rolling.window, rolling.min_periods, rolling.center, {qedj__sbxtj})
"""
        jhjie__ltxw = {}
        exec(bbr__xatlv, {'bodo': bodo}, jhjie__ltxw)
        impl = jhjie__ltxw['impl']
        return impl
    jzyq__qmoof = isinstance(rolling.obj_type, SeriesType)
    if fname in ('corr', 'cov'):
        out_cols = None if jzyq__qmoof else _get_corr_cov_out_cols(rolling,
            other, fname)
        df_cols = None if jzyq__qmoof else rolling.obj_type.columns
        other_cols = None if jzyq__qmoof else other.columns
        bpqnf__ezi, kfnq__otwo = _gen_corr_cov_out_data(out_cols, df_cols,
            other_cols, rolling.window_type, fname)
    else:
        bpqnf__ezi, kfnq__otwo, out_cols = _gen_df_rolling_out_data(rolling)
    ctev__tcc = jzyq__qmoof or len(rolling.selection) == (1 if rolling.on is
        None else 2) and rolling.series_select
    hcjz__wahka = f'def impl(rolling, {_get_rolling_func_args(fname)}):\n'
    hcjz__wahka += '  df = rolling.obj\n'
    hcjz__wahka += '  index = {}\n'.format(
        'bodo.hiframes.pd_series_ext.get_series_index(df)' if jzyq__qmoof else
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)')
    wyf__lsn = 'None'
    if jzyq__qmoof:
        wyf__lsn = 'bodo.hiframes.pd_series_ext.get_series_name(df)'
    elif ctev__tcc:
        frdlk__sik = (set(out_cols) - set([rolling.on])).pop()
        wyf__lsn = f"'{frdlk__sik}'" if isinstance(frdlk__sik, str) else str(
            frdlk__sik)
    hcjz__wahka += f'  name = {wyf__lsn}\n'
    hcjz__wahka += '  window = rolling.window\n'
    hcjz__wahka += '  center = rolling.center\n'
    hcjz__wahka += '  minp = rolling.min_periods\n'
    hcjz__wahka += f'  on_arr = {kfnq__otwo}\n'
    if fname == 'apply':
        hcjz__wahka += (
            f'  index_arr = bodo.utils.conversion.index_to_array(index)\n')
    else:
        hcjz__wahka += f"  func = '{fname}'\n"
        hcjz__wahka += f'  index_arr = None\n'
        hcjz__wahka += f'  raw = False\n'
    if ctev__tcc:
        hcjz__wahka += (
            f'  return bodo.hiframes.pd_series_ext.init_series({bpqnf__ezi}, index, name)'
            )
        jhjie__ltxw = {}
        eoare__zkvs = {'bodo': bodo}
        exec(hcjz__wahka, eoare__zkvs, jhjie__ltxw)
        impl = jhjie__ltxw['impl']
        return impl
    return bodo.hiframes.dataframe_impl._gen_init_df(hcjz__wahka, out_cols,
        bpqnf__ezi)


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
        hdym__hgia = create_rolling_overload(fname)
        overload_method(RollingType, fname, inline='always', no_unliteral=True
            )(hdym__hgia)


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
    zyn__dir = rolling.selection
    if rolling.on is not None:
        raise BodoError(
            f'variable window rolling {func_name} not supported yet.')
    out_cols = tuple(sorted(set(zyn__dir) | set(other.columns), key=lambda
        k: str(k)))
    return out_cols


def _gen_corr_cov_out_data(out_cols, df_cols, other_cols, window_type,
    func_name):
    smons__lakod = not isinstance(window_type, types.Integer)
    kfnq__otwo = 'None'
    if smons__lakod:
        kfnq__otwo = 'bodo.utils.conversion.index_to_array(index)'
    zxbca__fgasm = 'on_arr, ' if smons__lakod else ''
    bpqnf__ezi = []
    if out_cols is None:
        return (
            f'bodo.hiframes.rolling.rolling_{func_name}(bodo.hiframes.pd_series_ext.get_series_data(df), bodo.hiframes.pd_series_ext.get_series_data(other), {zxbca__fgasm}window, minp, center)'
            , kfnq__otwo)
    for frdlk__sik in out_cols:
        if frdlk__sik in df_cols and frdlk__sik in other_cols:
            dzgno__oyyv = df_cols.index(frdlk__sik)
            etrk__sxf = other_cols.index(frdlk__sik)
            ckshy__ocm = (
                f'bodo.hiframes.rolling.rolling_{func_name}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {dzgno__oyyv}), bodo.hiframes.pd_dataframe_ext.get_dataframe_data(other, {etrk__sxf}), {zxbca__fgasm}window, minp, center)'
                )
        else:
            ckshy__ocm = 'np.full(len(df), np.nan)'
        bpqnf__ezi.append(ckshy__ocm)
    return ', '.join(bpqnf__ezi), kfnq__otwo


@overload_method(RollingType, 'corr', inline='always', no_unliteral=True)
def overload_rolling_corr(rolling, other=None, pairwise=None, ddof=1):
    lev__syge = {'pairwise': pairwise, 'ddof': ddof}
    wszdj__subt = {'pairwise': None, 'ddof': 1}
    check_unsupported_args('pandas.core.window.rolling.Rolling.corr',
        lev__syge, wszdj__subt, package_name='pandas', module_name='Window')
    return _gen_rolling_impl(rolling, 'corr', other)


@overload_method(RollingType, 'cov', inline='always', no_unliteral=True)
def overload_rolling_cov(rolling, other=None, pairwise=None, ddof=1):
    lev__syge = {'ddof': ddof, 'pairwise': pairwise}
    wszdj__subt = {'ddof': 1, 'pairwise': None}
    check_unsupported_args('pandas.core.window.rolling.Rolling.cov',
        lev__syge, wszdj__subt, package_name='pandas', module_name='Window')
    return _gen_rolling_impl(rolling, 'cov', other)


@infer
class GetItemDataFrameRolling2(AbstractTemplate):
    key = 'static_getitem'

    def generic(self, args, kws):
        rolling, anp__iukl = args
        if isinstance(rolling, RollingType):
            zyn__dir = rolling.obj_type.selection if isinstance(rolling.
                obj_type, DataFrameGroupByType) else rolling.obj_type.columns
            series_select = False
            if isinstance(anp__iukl, (tuple, list)):
                if len(set(anp__iukl).difference(set(zyn__dir))) > 0:
                    raise_bodo_error(
                        'rolling: selected column {} not found in dataframe'
                        .format(set(anp__iukl).difference(set(zyn__dir))))
                selection = list(anp__iukl)
            else:
                if anp__iukl not in zyn__dir:
                    raise_bodo_error(
                        'rolling: selected column {} not found in dataframe'
                        .format(anp__iukl))
                selection = [anp__iukl]
                series_select = True
            if rolling.on is not None:
                selection.append(rolling.on)
            sout__opwg = RollingType(rolling.obj_type, rolling.window_type,
                rolling.on, tuple(selection), True, series_select)
            return signature(sout__opwg, *args)


@lower_builtin('static_getitem', RollingType, types.Any)
def static_getitem_df_groupby(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@infer_getattr
class RollingAttribute(AttributeTemplate):
    key = RollingType

    def generic_resolve(self, rolling, attr):
        zyn__dir = ()
        if isinstance(rolling.obj_type, DataFrameGroupByType):
            zyn__dir = rolling.obj_type.selection
        if isinstance(rolling.obj_type, DataFrameType):
            zyn__dir = rolling.obj_type.columns
        if attr in zyn__dir:
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
    rxgkf__mkopf = obj.columns if isinstance(obj, DataFrameType
        ) else obj.df_type.columns if isinstance(obj, DataFrameGroupByType
        ) else []
    jlpau__nkq = [obj.data] if isinstance(obj, SeriesType
        ) else obj.data if isinstance(obj, DataFrameType) else obj.df_type.data
    if not is_overload_none(on) and (not is_literal_type(on) or 
        get_literal_value(on) not in rxgkf__mkopf):
        raise BodoError(
            f"{func_name}.rolling(): 'on' should be a constant column name.")
    if not is_overload_none(on):
        rlfy__agizk = jlpau__nkq[rxgkf__mkopf.index(get_literal_value(on))]
        if not isinstance(rlfy__agizk, types.Array
            ) or rlfy__agizk.dtype != bodo.datetime64ns:
            raise BodoError(
                f"{func_name}.rolling(): 'on' column should have datetime64 data."
                )
    if not any(isinstance(vuxe__etlly.dtype, (types.Boolean, types.Number)) for
        vuxe__etlly in jlpau__nkq):
        raise BodoError(f'{func_name}.rolling(): No numeric types to aggregate'
            )
