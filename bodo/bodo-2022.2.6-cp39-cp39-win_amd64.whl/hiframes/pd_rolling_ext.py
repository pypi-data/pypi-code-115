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
        czop__ivsfk = [('obj', fe_type.obj_type), ('window', fe_type.
            window_type), ('min_periods', types.int64), ('center', types.bool_)
            ]
        super(RollingModel, self).__init__(dmm, fe_type, czop__ivsfk)


make_attribute_wrapper(RollingType, 'obj', 'obj')
make_attribute_wrapper(RollingType, 'window', 'window')
make_attribute_wrapper(RollingType, 'center', 'center')
make_attribute_wrapper(RollingType, 'min_periods', 'min_periods')


@overload_method(DataFrameType, 'rolling', inline='always', no_unliteral=True)
def df_rolling_overload(df, window, min_periods=None, center=False,
    win_type=None, on=None, axis=0, closed=None):
    check_runtime_cols_unsupported(df, 'DataFrame.rolling()')
    kwq__tfiz = dict(win_type=win_type, axis=axis, closed=closed)
    kmbz__yqsuf = dict(win_type=None, axis=0, closed=None)
    check_unsupported_args('DataFrame.rolling', kwq__tfiz, kmbz__yqsuf,
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
    kwq__tfiz = dict(win_type=win_type, axis=axis, closed=closed)
    kmbz__yqsuf = dict(win_type=None, axis=0, closed=None)
    check_unsupported_args('Series.rolling', kwq__tfiz, kmbz__yqsuf,
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
        xph__bdwdw, fnz__expv, pspbk__wetr, xbvce__fqf, zaql__gwalm = args
        ztvd__omgah = signature.return_type
        zir__kwhq = cgutils.create_struct_proxy(ztvd__omgah)(context, builder)
        zir__kwhq.obj = xph__bdwdw
        zir__kwhq.window = fnz__expv
        zir__kwhq.min_periods = pspbk__wetr
        zir__kwhq.center = xbvce__fqf
        context.nrt.incref(builder, signature.args[0], xph__bdwdw)
        context.nrt.incref(builder, signature.args[1], fnz__expv)
        context.nrt.incref(builder, signature.args[2], pspbk__wetr)
        context.nrt.incref(builder, signature.args[3], xbvce__fqf)
        return zir__kwhq._getvalue()
    on = get_literal_value(on_type)
    if isinstance(obj_type, SeriesType):
        selection = None
    elif isinstance(obj_type, DataFrameType):
        selection = obj_type.columns
    else:
        assert isinstance(obj_type, DataFrameGroupByType
            ), f'invalid obj type for rolling: {obj_type}'
        selection = obj_type.selection
    ztvd__omgah = RollingType(obj_type, window_type, on, selection, False)
    return ztvd__omgah(obj_type, window_type, min_periods_type, center_type,
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
    lrgkk__lgt = not isinstance(rolling.window_type, types.Integer)
    eii__ojdu = 'variable' if lrgkk__lgt else 'fixed'
    ajqd__nzozq = 'None'
    if lrgkk__lgt:
        ajqd__nzozq = ('bodo.utils.conversion.index_to_array(index)' if 
            rolling.on is None else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {rolling.obj_type.columns.index(rolling.on)})'
            )
    ztjkl__ijbsh = []
    zirwb__djl = 'on_arr, ' if lrgkk__lgt else ''
    if isinstance(rolling.obj_type, SeriesType):
        return (
            f'bodo.hiframes.rolling.rolling_{eii__ojdu}(bodo.hiframes.pd_series_ext.get_series_data(df), {zirwb__djl}index_arr, window, minp, center, func, raw)'
            , ajqd__nzozq, rolling.selection)
    assert isinstance(rolling.obj_type, DataFrameType
        ), 'expected df in rolling obj'
    uglq__pzpq = rolling.obj_type.data
    out_cols = []
    for odcy__nmiq in rolling.selection:
        alw__rid = rolling.obj_type.columns.index(odcy__nmiq)
        if odcy__nmiq == rolling.on:
            if len(rolling.selection) == 2 and rolling.series_select:
                continue
            haszf__pkmaw = (
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {alw__rid})'
                )
            out_cols.append(odcy__nmiq)
        else:
            if not isinstance(uglq__pzpq[alw__rid].dtype, (types.Boolean,
                types.Number)):
                continue
            haszf__pkmaw = (
                f'bodo.hiframes.rolling.rolling_{eii__ojdu}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {alw__rid}), {zirwb__djl}index_arr, window, minp, center, func, raw)'
                )
            out_cols.append(odcy__nmiq)
        ztjkl__ijbsh.append(haszf__pkmaw)
    return ', '.join(ztjkl__ijbsh), ajqd__nzozq, tuple(out_cols)


@overload_method(RollingType, 'apply', inline='always', no_unliteral=True)
def overload_rolling_apply(rolling, func, raw=False, engine=None,
    engine_kwargs=None, args=None, kwargs=None):
    kwq__tfiz = dict(engine=engine, engine_kwargs=engine_kwargs, args=args,
        kwargs=kwargs)
    kmbz__yqsuf = dict(engine=None, engine_kwargs=None, args=None, kwargs=None)
    check_unsupported_args('Rolling.apply', kwq__tfiz, kmbz__yqsuf,
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
    kwq__tfiz = dict(win_type=win_type, axis=axis, closed=closed, method=method
        )
    kmbz__yqsuf = dict(win_type=None, axis=0, closed=None, method='single')
    check_unsupported_args('GroupBy.rolling', kwq__tfiz, kmbz__yqsuf,
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
        mrkx__osi = f'def impl(rolling, {_get_rolling_func_args(fname)}):\n'
        ddmc__oxaze = f"'{rolling.on}'" if isinstance(rolling.on, str
            ) else f'{rolling.on}'
        selection = ''
        if rolling.explicit_select:
            selection = '[{}]'.format(', '.join(f"'{fmzbc__kjooo}'" if
                isinstance(fmzbc__kjooo, str) else f'{fmzbc__kjooo}' for
                fmzbc__kjooo in rolling.selection if fmzbc__kjooo !=
                rolling.on))
        tmw__dka = ptbfb__qndgn = ''
        if fname == 'apply':
            tmw__dka = 'func, raw, args, kwargs'
            ptbfb__qndgn = 'func, raw, None, None, args, kwargs'
        if fname == 'corr':
            tmw__dka = ptbfb__qndgn = 'other, pairwise'
        if fname == 'cov':
            tmw__dka = ptbfb__qndgn = 'other, pairwise, ddof'
        kyihx__opl = (
            f'lambda df, window, minp, center, {tmw__dka}: bodo.hiframes.pd_rolling_ext.init_rolling(df, window, minp, center, {ddmc__oxaze}){selection}.{fname}({ptbfb__qndgn})'
            )
        mrkx__osi += f"""  return rolling.obj.apply({kyihx__opl}, rolling.window, rolling.min_periods, rolling.center, {tmw__dka})
"""
        hkyvm__czlfv = {}
        exec(mrkx__osi, {'bodo': bodo}, hkyvm__czlfv)
        impl = hkyvm__czlfv['impl']
        return impl
    thqxf__woa = isinstance(rolling.obj_type, SeriesType)
    if fname in ('corr', 'cov'):
        out_cols = None if thqxf__woa else _get_corr_cov_out_cols(rolling,
            other, fname)
        df_cols = None if thqxf__woa else rolling.obj_type.columns
        other_cols = None if thqxf__woa else other.columns
        ztjkl__ijbsh, ajqd__nzozq = _gen_corr_cov_out_data(out_cols,
            df_cols, other_cols, rolling.window_type, fname)
    else:
        ztjkl__ijbsh, ajqd__nzozq, out_cols = _gen_df_rolling_out_data(rolling)
    klg__rgrzq = thqxf__woa or len(rolling.selection) == (1 if rolling.on is
        None else 2) and rolling.series_select
    vjr__kwt = f'def impl(rolling, {_get_rolling_func_args(fname)}):\n'
    vjr__kwt += '  df = rolling.obj\n'
    vjr__kwt += '  index = {}\n'.format(
        'bodo.hiframes.pd_series_ext.get_series_index(df)' if thqxf__woa else
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)')
    plx__imx = 'None'
    if thqxf__woa:
        plx__imx = 'bodo.hiframes.pd_series_ext.get_series_name(df)'
    elif klg__rgrzq:
        odcy__nmiq = (set(out_cols) - set([rolling.on])).pop()
        plx__imx = f"'{odcy__nmiq}'" if isinstance(odcy__nmiq, str) else str(
            odcy__nmiq)
    vjr__kwt += f'  name = {plx__imx}\n'
    vjr__kwt += '  window = rolling.window\n'
    vjr__kwt += '  center = rolling.center\n'
    vjr__kwt += '  minp = rolling.min_periods\n'
    vjr__kwt += f'  on_arr = {ajqd__nzozq}\n'
    if fname == 'apply':
        vjr__kwt += (
            f'  index_arr = bodo.utils.conversion.index_to_array(index)\n')
    else:
        vjr__kwt += f"  func = '{fname}'\n"
        vjr__kwt += f'  index_arr = None\n'
        vjr__kwt += f'  raw = False\n'
    if klg__rgrzq:
        vjr__kwt += (
            f'  return bodo.hiframes.pd_series_ext.init_series({ztjkl__ijbsh}, index, name)'
            )
        hkyvm__czlfv = {}
        eqx__splx = {'bodo': bodo}
        exec(vjr__kwt, eqx__splx, hkyvm__czlfv)
        impl = hkyvm__czlfv['impl']
        return impl
    return bodo.hiframes.dataframe_impl._gen_init_df(vjr__kwt, out_cols,
        ztjkl__ijbsh)


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
        pusv__hnasv = create_rolling_overload(fname)
        overload_method(RollingType, fname, inline='always', no_unliteral=True
            )(pusv__hnasv)


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
    sqxt__qpvrh = rolling.selection
    if rolling.on is not None:
        raise BodoError(
            f'variable window rolling {func_name} not supported yet.')
    out_cols = tuple(sorted(set(sqxt__qpvrh) | set(other.columns), key=lambda
        k: str(k)))
    return out_cols


def _gen_corr_cov_out_data(out_cols, df_cols, other_cols, window_type,
    func_name):
    lrgkk__lgt = not isinstance(window_type, types.Integer)
    ajqd__nzozq = 'None'
    if lrgkk__lgt:
        ajqd__nzozq = 'bodo.utils.conversion.index_to_array(index)'
    zirwb__djl = 'on_arr, ' if lrgkk__lgt else ''
    ztjkl__ijbsh = []
    if out_cols is None:
        return (
            f'bodo.hiframes.rolling.rolling_{func_name}(bodo.hiframes.pd_series_ext.get_series_data(df), bodo.hiframes.pd_series_ext.get_series_data(other), {zirwb__djl}window, minp, center)'
            , ajqd__nzozq)
    for odcy__nmiq in out_cols:
        if odcy__nmiq in df_cols and odcy__nmiq in other_cols:
            zepxy__vnyp = df_cols.index(odcy__nmiq)
            tseex__cgtvg = other_cols.index(odcy__nmiq)
            haszf__pkmaw = (
                f'bodo.hiframes.rolling.rolling_{func_name}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {zepxy__vnyp}), bodo.hiframes.pd_dataframe_ext.get_dataframe_data(other, {tseex__cgtvg}), {zirwb__djl}window, minp, center)'
                )
        else:
            haszf__pkmaw = 'np.full(len(df), np.nan)'
        ztjkl__ijbsh.append(haszf__pkmaw)
    return ', '.join(ztjkl__ijbsh), ajqd__nzozq


@overload_method(RollingType, 'corr', inline='always', no_unliteral=True)
def overload_rolling_corr(rolling, other=None, pairwise=None, ddof=1):
    dqs__sit = {'pairwise': pairwise, 'ddof': ddof}
    wajmc__qkx = {'pairwise': None, 'ddof': 1}
    check_unsupported_args('pandas.core.window.rolling.Rolling.corr',
        dqs__sit, wajmc__qkx, package_name='pandas', module_name='Window')
    return _gen_rolling_impl(rolling, 'corr', other)


@overload_method(RollingType, 'cov', inline='always', no_unliteral=True)
def overload_rolling_cov(rolling, other=None, pairwise=None, ddof=1):
    dqs__sit = {'ddof': ddof, 'pairwise': pairwise}
    wajmc__qkx = {'ddof': 1, 'pairwise': None}
    check_unsupported_args('pandas.core.window.rolling.Rolling.cov',
        dqs__sit, wajmc__qkx, package_name='pandas', module_name='Window')
    return _gen_rolling_impl(rolling, 'cov', other)


@infer
class GetItemDataFrameRolling2(AbstractTemplate):
    key = 'static_getitem'

    def generic(self, args, kws):
        rolling, fbw__pqvf = args
        if isinstance(rolling, RollingType):
            sqxt__qpvrh = rolling.obj_type.selection if isinstance(rolling.
                obj_type, DataFrameGroupByType) else rolling.obj_type.columns
            series_select = False
            if isinstance(fbw__pqvf, (tuple, list)):
                if len(set(fbw__pqvf).difference(set(sqxt__qpvrh))) > 0:
                    raise_bodo_error(
                        'rolling: selected column {} not found in dataframe'
                        .format(set(fbw__pqvf).difference(set(sqxt__qpvrh))))
                selection = list(fbw__pqvf)
            else:
                if fbw__pqvf not in sqxt__qpvrh:
                    raise_bodo_error(
                        'rolling: selected column {} not found in dataframe'
                        .format(fbw__pqvf))
                selection = [fbw__pqvf]
                series_select = True
            if rolling.on is not None:
                selection.append(rolling.on)
            jdp__qcbl = RollingType(rolling.obj_type, rolling.window_type,
                rolling.on, tuple(selection), True, series_select)
            return signature(jdp__qcbl, *args)


@lower_builtin('static_getitem', RollingType, types.Any)
def static_getitem_df_groupby(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@infer_getattr
class RollingAttribute(AttributeTemplate):
    key = RollingType

    def generic_resolve(self, rolling, attr):
        sqxt__qpvrh = ()
        if isinstance(rolling.obj_type, DataFrameGroupByType):
            sqxt__qpvrh = rolling.obj_type.selection
        if isinstance(rolling.obj_type, DataFrameType):
            sqxt__qpvrh = rolling.obj_type.columns
        if attr in sqxt__qpvrh:
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
    zvfk__lwbqd = obj.columns if isinstance(obj, DataFrameType
        ) else obj.df_type.columns if isinstance(obj, DataFrameGroupByType
        ) else []
    uglq__pzpq = [obj.data] if isinstance(obj, SeriesType
        ) else obj.data if isinstance(obj, DataFrameType) else obj.df_type.data
    if not is_overload_none(on) and (not is_literal_type(on) or 
        get_literal_value(on) not in zvfk__lwbqd):
        raise BodoError(
            f"{func_name}.rolling(): 'on' should be a constant column name.")
    if not is_overload_none(on):
        qhpke__iug = uglq__pzpq[zvfk__lwbqd.index(get_literal_value(on))]
        if not isinstance(qhpke__iug, types.Array
            ) or qhpke__iug.dtype != bodo.datetime64ns:
            raise BodoError(
                f"{func_name}.rolling(): 'on' column should have datetime64 data."
                )
    if not any(isinstance(oer__kzujz.dtype, (types.Boolean, types.Number)) for
        oer__kzujz in uglq__pzpq):
        raise BodoError(f'{func_name}.rolling(): No numeric types to aggregate'
            )
