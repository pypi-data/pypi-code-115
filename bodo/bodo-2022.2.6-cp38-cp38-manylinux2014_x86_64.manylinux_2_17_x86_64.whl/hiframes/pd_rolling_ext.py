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
        hlm__ullcs = [('obj', fe_type.obj_type), ('window', fe_type.
            window_type), ('min_periods', types.int64), ('center', types.bool_)
            ]
        super(RollingModel, self).__init__(dmm, fe_type, hlm__ullcs)


make_attribute_wrapper(RollingType, 'obj', 'obj')
make_attribute_wrapper(RollingType, 'window', 'window')
make_attribute_wrapper(RollingType, 'center', 'center')
make_attribute_wrapper(RollingType, 'min_periods', 'min_periods')


@overload_method(DataFrameType, 'rolling', inline='always', no_unliteral=True)
def df_rolling_overload(df, window, min_periods=None, center=False,
    win_type=None, on=None, axis=0, closed=None):
    check_runtime_cols_unsupported(df, 'DataFrame.rolling()')
    mnio__ahot = dict(win_type=win_type, axis=axis, closed=closed)
    jswb__gaew = dict(win_type=None, axis=0, closed=None)
    check_unsupported_args('DataFrame.rolling', mnio__ahot, jswb__gaew,
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
    mnio__ahot = dict(win_type=win_type, axis=axis, closed=closed)
    jswb__gaew = dict(win_type=None, axis=0, closed=None)
    check_unsupported_args('Series.rolling', mnio__ahot, jswb__gaew,
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
        mdy__ifc, fthrj__reiyf, gyl__uutki, kgqfi__ozk, pnb__nea = args
        pcz__neay = signature.return_type
        fqr__hnwa = cgutils.create_struct_proxy(pcz__neay)(context, builder)
        fqr__hnwa.obj = mdy__ifc
        fqr__hnwa.window = fthrj__reiyf
        fqr__hnwa.min_periods = gyl__uutki
        fqr__hnwa.center = kgqfi__ozk
        context.nrt.incref(builder, signature.args[0], mdy__ifc)
        context.nrt.incref(builder, signature.args[1], fthrj__reiyf)
        context.nrt.incref(builder, signature.args[2], gyl__uutki)
        context.nrt.incref(builder, signature.args[3], kgqfi__ozk)
        return fqr__hnwa._getvalue()
    on = get_literal_value(on_type)
    if isinstance(obj_type, SeriesType):
        selection = None
    elif isinstance(obj_type, DataFrameType):
        selection = obj_type.columns
    else:
        assert isinstance(obj_type, DataFrameGroupByType
            ), f'invalid obj type for rolling: {obj_type}'
        selection = obj_type.selection
    pcz__neay = RollingType(obj_type, window_type, on, selection, False)
    return pcz__neay(obj_type, window_type, min_periods_type, center_type,
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
    gzvjy__zhyhv = not isinstance(rolling.window_type, types.Integer)
    mqo__ena = 'variable' if gzvjy__zhyhv else 'fixed'
    kdd__jnffm = 'None'
    if gzvjy__zhyhv:
        kdd__jnffm = ('bodo.utils.conversion.index_to_array(index)' if 
            rolling.on is None else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {rolling.obj_type.columns.index(rolling.on)})'
            )
    iqs__lhf = []
    cdah__nti = 'on_arr, ' if gzvjy__zhyhv else ''
    if isinstance(rolling.obj_type, SeriesType):
        return (
            f'bodo.hiframes.rolling.rolling_{mqo__ena}(bodo.hiframes.pd_series_ext.get_series_data(df), {cdah__nti}index_arr, window, minp, center, func, raw)'
            , kdd__jnffm, rolling.selection)
    assert isinstance(rolling.obj_type, DataFrameType
        ), 'expected df in rolling obj'
    sxqld__jmxhl = rolling.obj_type.data
    out_cols = []
    for cmvcr__mdq in rolling.selection:
        zwhba__zdnyw = rolling.obj_type.columns.index(cmvcr__mdq)
        if cmvcr__mdq == rolling.on:
            if len(rolling.selection) == 2 and rolling.series_select:
                continue
            mjm__qlmgx = (
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {zwhba__zdnyw})'
                )
            out_cols.append(cmvcr__mdq)
        else:
            if not isinstance(sxqld__jmxhl[zwhba__zdnyw].dtype, (types.
                Boolean, types.Number)):
                continue
            mjm__qlmgx = (
                f'bodo.hiframes.rolling.rolling_{mqo__ena}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {zwhba__zdnyw}), {cdah__nti}index_arr, window, minp, center, func, raw)'
                )
            out_cols.append(cmvcr__mdq)
        iqs__lhf.append(mjm__qlmgx)
    return ', '.join(iqs__lhf), kdd__jnffm, tuple(out_cols)


@overload_method(RollingType, 'apply', inline='always', no_unliteral=True)
def overload_rolling_apply(rolling, func, raw=False, engine=None,
    engine_kwargs=None, args=None, kwargs=None):
    mnio__ahot = dict(engine=engine, engine_kwargs=engine_kwargs, args=args,
        kwargs=kwargs)
    jswb__gaew = dict(engine=None, engine_kwargs=None, args=None, kwargs=None)
    check_unsupported_args('Rolling.apply', mnio__ahot, jswb__gaew,
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
    mnio__ahot = dict(win_type=win_type, axis=axis, closed=closed, method=
        method)
    jswb__gaew = dict(win_type=None, axis=0, closed=None, method='single')
    check_unsupported_args('GroupBy.rolling', mnio__ahot, jswb__gaew,
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
        zffd__vief = f'def impl(rolling, {_get_rolling_func_args(fname)}):\n'
        utk__eaa = f"'{rolling.on}'" if isinstance(rolling.on, str
            ) else f'{rolling.on}'
        selection = ''
        if rolling.explicit_select:
            selection = '[{}]'.format(', '.join(f"'{lvaq__shu}'" if
                isinstance(lvaq__shu, str) else f'{lvaq__shu}' for
                lvaq__shu in rolling.selection if lvaq__shu != rolling.on))
        xxhqz__nxoo = prlx__wtak = ''
        if fname == 'apply':
            xxhqz__nxoo = 'func, raw, args, kwargs'
            prlx__wtak = 'func, raw, None, None, args, kwargs'
        if fname == 'corr':
            xxhqz__nxoo = prlx__wtak = 'other, pairwise'
        if fname == 'cov':
            xxhqz__nxoo = prlx__wtak = 'other, pairwise, ddof'
        bpr__lipf = (
            f'lambda df, window, minp, center, {xxhqz__nxoo}: bodo.hiframes.pd_rolling_ext.init_rolling(df, window, minp, center, {utk__eaa}){selection}.{fname}({prlx__wtak})'
            )
        zffd__vief += f"""  return rolling.obj.apply({bpr__lipf}, rolling.window, rolling.min_periods, rolling.center, {xxhqz__nxoo})
"""
        rvklm__wqbb = {}
        exec(zffd__vief, {'bodo': bodo}, rvklm__wqbb)
        impl = rvklm__wqbb['impl']
        return impl
    ewko__xawy = isinstance(rolling.obj_type, SeriesType)
    if fname in ('corr', 'cov'):
        out_cols = None if ewko__xawy else _get_corr_cov_out_cols(rolling,
            other, fname)
        df_cols = None if ewko__xawy else rolling.obj_type.columns
        other_cols = None if ewko__xawy else other.columns
        iqs__lhf, kdd__jnffm = _gen_corr_cov_out_data(out_cols, df_cols,
            other_cols, rolling.window_type, fname)
    else:
        iqs__lhf, kdd__jnffm, out_cols = _gen_df_rolling_out_data(rolling)
    xwi__goh = ewko__xawy or len(rolling.selection) == (1 if rolling.on is
        None else 2) and rolling.series_select
    ngjn__keyf = f'def impl(rolling, {_get_rolling_func_args(fname)}):\n'
    ngjn__keyf += '  df = rolling.obj\n'
    ngjn__keyf += '  index = {}\n'.format(
        'bodo.hiframes.pd_series_ext.get_series_index(df)' if ewko__xawy else
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)')
    saom__kezh = 'None'
    if ewko__xawy:
        saom__kezh = 'bodo.hiframes.pd_series_ext.get_series_name(df)'
    elif xwi__goh:
        cmvcr__mdq = (set(out_cols) - set([rolling.on])).pop()
        saom__kezh = f"'{cmvcr__mdq}'" if isinstance(cmvcr__mdq, str) else str(
            cmvcr__mdq)
    ngjn__keyf += f'  name = {saom__kezh}\n'
    ngjn__keyf += '  window = rolling.window\n'
    ngjn__keyf += '  center = rolling.center\n'
    ngjn__keyf += '  minp = rolling.min_periods\n'
    ngjn__keyf += f'  on_arr = {kdd__jnffm}\n'
    if fname == 'apply':
        ngjn__keyf += (
            f'  index_arr = bodo.utils.conversion.index_to_array(index)\n')
    else:
        ngjn__keyf += f"  func = '{fname}'\n"
        ngjn__keyf += f'  index_arr = None\n'
        ngjn__keyf += f'  raw = False\n'
    if xwi__goh:
        ngjn__keyf += (
            f'  return bodo.hiframes.pd_series_ext.init_series({iqs__lhf}, index, name)'
            )
        rvklm__wqbb = {}
        bdw__fmpy = {'bodo': bodo}
        exec(ngjn__keyf, bdw__fmpy, rvklm__wqbb)
        impl = rvklm__wqbb['impl']
        return impl
    return bodo.hiframes.dataframe_impl._gen_init_df(ngjn__keyf, out_cols,
        iqs__lhf)


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
        lsa__kjwbv = create_rolling_overload(fname)
        overload_method(RollingType, fname, inline='always', no_unliteral=True
            )(lsa__kjwbv)


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
    nrxmv__tpyjk = rolling.selection
    if rolling.on is not None:
        raise BodoError(
            f'variable window rolling {func_name} not supported yet.')
    out_cols = tuple(sorted(set(nrxmv__tpyjk) | set(other.columns), key=lambda
        k: str(k)))
    return out_cols


def _gen_corr_cov_out_data(out_cols, df_cols, other_cols, window_type,
    func_name):
    gzvjy__zhyhv = not isinstance(window_type, types.Integer)
    kdd__jnffm = 'None'
    if gzvjy__zhyhv:
        kdd__jnffm = 'bodo.utils.conversion.index_to_array(index)'
    cdah__nti = 'on_arr, ' if gzvjy__zhyhv else ''
    iqs__lhf = []
    if out_cols is None:
        return (
            f'bodo.hiframes.rolling.rolling_{func_name}(bodo.hiframes.pd_series_ext.get_series_data(df), bodo.hiframes.pd_series_ext.get_series_data(other), {cdah__nti}window, minp, center)'
            , kdd__jnffm)
    for cmvcr__mdq in out_cols:
        if cmvcr__mdq in df_cols and cmvcr__mdq in other_cols:
            ozy__ljd = df_cols.index(cmvcr__mdq)
            fmav__fjxno = other_cols.index(cmvcr__mdq)
            mjm__qlmgx = (
                f'bodo.hiframes.rolling.rolling_{func_name}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {ozy__ljd}), bodo.hiframes.pd_dataframe_ext.get_dataframe_data(other, {fmav__fjxno}), {cdah__nti}window, minp, center)'
                )
        else:
            mjm__qlmgx = 'np.full(len(df), np.nan)'
        iqs__lhf.append(mjm__qlmgx)
    return ', '.join(iqs__lhf), kdd__jnffm


@overload_method(RollingType, 'corr', inline='always', no_unliteral=True)
def overload_rolling_corr(rolling, other=None, pairwise=None, ddof=1):
    rtw__mzqn = {'pairwise': pairwise, 'ddof': ddof}
    jxt__vipt = {'pairwise': None, 'ddof': 1}
    check_unsupported_args('pandas.core.window.rolling.Rolling.corr',
        rtw__mzqn, jxt__vipt, package_name='pandas', module_name='Window')
    return _gen_rolling_impl(rolling, 'corr', other)


@overload_method(RollingType, 'cov', inline='always', no_unliteral=True)
def overload_rolling_cov(rolling, other=None, pairwise=None, ddof=1):
    rtw__mzqn = {'ddof': ddof, 'pairwise': pairwise}
    jxt__vipt = {'ddof': 1, 'pairwise': None}
    check_unsupported_args('pandas.core.window.rolling.Rolling.cov',
        rtw__mzqn, jxt__vipt, package_name='pandas', module_name='Window')
    return _gen_rolling_impl(rolling, 'cov', other)


@infer
class GetItemDataFrameRolling2(AbstractTemplate):
    key = 'static_getitem'

    def generic(self, args, kws):
        rolling, dnar__pkod = args
        if isinstance(rolling, RollingType):
            nrxmv__tpyjk = rolling.obj_type.selection if isinstance(rolling
                .obj_type, DataFrameGroupByType) else rolling.obj_type.columns
            series_select = False
            if isinstance(dnar__pkod, (tuple, list)):
                if len(set(dnar__pkod).difference(set(nrxmv__tpyjk))) > 0:
                    raise_bodo_error(
                        'rolling: selected column {} not found in dataframe'
                        .format(set(dnar__pkod).difference(set(nrxmv__tpyjk))))
                selection = list(dnar__pkod)
            else:
                if dnar__pkod not in nrxmv__tpyjk:
                    raise_bodo_error(
                        'rolling: selected column {} not found in dataframe'
                        .format(dnar__pkod))
                selection = [dnar__pkod]
                series_select = True
            if rolling.on is not None:
                selection.append(rolling.on)
            tgkit__busch = RollingType(rolling.obj_type, rolling.
                window_type, rolling.on, tuple(selection), True, series_select)
            return signature(tgkit__busch, *args)


@lower_builtin('static_getitem', RollingType, types.Any)
def static_getitem_df_groupby(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@infer_getattr
class RollingAttribute(AttributeTemplate):
    key = RollingType

    def generic_resolve(self, rolling, attr):
        nrxmv__tpyjk = ()
        if isinstance(rolling.obj_type, DataFrameGroupByType):
            nrxmv__tpyjk = rolling.obj_type.selection
        if isinstance(rolling.obj_type, DataFrameType):
            nrxmv__tpyjk = rolling.obj_type.columns
        if attr in nrxmv__tpyjk:
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
    vml__ocqz = obj.columns if isinstance(obj, DataFrameType
        ) else obj.df_type.columns if isinstance(obj, DataFrameGroupByType
        ) else []
    sxqld__jmxhl = [obj.data] if isinstance(obj, SeriesType
        ) else obj.data if isinstance(obj, DataFrameType) else obj.df_type.data
    if not is_overload_none(on) and (not is_literal_type(on) or 
        get_literal_value(on) not in vml__ocqz):
        raise BodoError(
            f"{func_name}.rolling(): 'on' should be a constant column name.")
    if not is_overload_none(on):
        blzb__cuzcc = sxqld__jmxhl[vml__ocqz.index(get_literal_value(on))]
        if not isinstance(blzb__cuzcc, types.Array
            ) or blzb__cuzcc.dtype != bodo.datetime64ns:
            raise BodoError(
                f"{func_name}.rolling(): 'on' column should have datetime64 data."
                )
    if not any(isinstance(nogun__mfrm.dtype, (types.Boolean, types.Number)) for
        nogun__mfrm in sxqld__jmxhl):
        raise BodoError(f'{func_name}.rolling(): No numeric types to aggregate'
            )
