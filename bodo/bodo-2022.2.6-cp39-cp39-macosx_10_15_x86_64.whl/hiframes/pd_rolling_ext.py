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
        xuk__gfcv = [('obj', fe_type.obj_type), ('window', fe_type.
            window_type), ('min_periods', types.int64), ('center', types.bool_)
            ]
        super(RollingModel, self).__init__(dmm, fe_type, xuk__gfcv)


make_attribute_wrapper(RollingType, 'obj', 'obj')
make_attribute_wrapper(RollingType, 'window', 'window')
make_attribute_wrapper(RollingType, 'center', 'center')
make_attribute_wrapper(RollingType, 'min_periods', 'min_periods')


@overload_method(DataFrameType, 'rolling', inline='always', no_unliteral=True)
def df_rolling_overload(df, window, min_periods=None, center=False,
    win_type=None, on=None, axis=0, closed=None):
    check_runtime_cols_unsupported(df, 'DataFrame.rolling()')
    ekn__jjldb = dict(win_type=win_type, axis=axis, closed=closed)
    qloto__kgwfv = dict(win_type=None, axis=0, closed=None)
    check_unsupported_args('DataFrame.rolling', ekn__jjldb, qloto__kgwfv,
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
    ekn__jjldb = dict(win_type=win_type, axis=axis, closed=closed)
    qloto__kgwfv = dict(win_type=None, axis=0, closed=None)
    check_unsupported_args('Series.rolling', ekn__jjldb, qloto__kgwfv,
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
        lsfo__sav, ayith__utkqb, duobx__sfjmx, txlja__ultqp, yjx__dhopw = args
        vzbi__oso = signature.return_type
        zqtmr__jypy = cgutils.create_struct_proxy(vzbi__oso)(context, builder)
        zqtmr__jypy.obj = lsfo__sav
        zqtmr__jypy.window = ayith__utkqb
        zqtmr__jypy.min_periods = duobx__sfjmx
        zqtmr__jypy.center = txlja__ultqp
        context.nrt.incref(builder, signature.args[0], lsfo__sav)
        context.nrt.incref(builder, signature.args[1], ayith__utkqb)
        context.nrt.incref(builder, signature.args[2], duobx__sfjmx)
        context.nrt.incref(builder, signature.args[3], txlja__ultqp)
        return zqtmr__jypy._getvalue()
    on = get_literal_value(on_type)
    if isinstance(obj_type, SeriesType):
        selection = None
    elif isinstance(obj_type, DataFrameType):
        selection = obj_type.columns
    else:
        assert isinstance(obj_type, DataFrameGroupByType
            ), f'invalid obj type for rolling: {obj_type}'
        selection = obj_type.selection
    vzbi__oso = RollingType(obj_type, window_type, on, selection, False)
    return vzbi__oso(obj_type, window_type, min_periods_type, center_type,
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
    szjb__vtj = not isinstance(rolling.window_type, types.Integer)
    sbg__duwnx = 'variable' if szjb__vtj else 'fixed'
    zyl__wwf = 'None'
    if szjb__vtj:
        zyl__wwf = ('bodo.utils.conversion.index_to_array(index)' if 
            rolling.on is None else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {rolling.obj_type.columns.index(rolling.on)})'
            )
    fqlb__pgoo = []
    vxtcs__gkeqe = 'on_arr, ' if szjb__vtj else ''
    if isinstance(rolling.obj_type, SeriesType):
        return (
            f'bodo.hiframes.rolling.rolling_{sbg__duwnx}(bodo.hiframes.pd_series_ext.get_series_data(df), {vxtcs__gkeqe}index_arr, window, minp, center, func, raw)'
            , zyl__wwf, rolling.selection)
    assert isinstance(rolling.obj_type, DataFrameType
        ), 'expected df in rolling obj'
    zdml__cqonu = rolling.obj_type.data
    out_cols = []
    for greq__mqpm in rolling.selection:
        wsuu__jbk = rolling.obj_type.columns.index(greq__mqpm)
        if greq__mqpm == rolling.on:
            if len(rolling.selection) == 2 and rolling.series_select:
                continue
            udl__ybmf = (
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {wsuu__jbk})'
                )
            out_cols.append(greq__mqpm)
        else:
            if not isinstance(zdml__cqonu[wsuu__jbk].dtype, (types.Boolean,
                types.Number)):
                continue
            udl__ybmf = (
                f'bodo.hiframes.rolling.rolling_{sbg__duwnx}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {wsuu__jbk}), {vxtcs__gkeqe}index_arr, window, minp, center, func, raw)'
                )
            out_cols.append(greq__mqpm)
        fqlb__pgoo.append(udl__ybmf)
    return ', '.join(fqlb__pgoo), zyl__wwf, tuple(out_cols)


@overload_method(RollingType, 'apply', inline='always', no_unliteral=True)
def overload_rolling_apply(rolling, func, raw=False, engine=None,
    engine_kwargs=None, args=None, kwargs=None):
    ekn__jjldb = dict(engine=engine, engine_kwargs=engine_kwargs, args=args,
        kwargs=kwargs)
    qloto__kgwfv = dict(engine=None, engine_kwargs=None, args=None, kwargs=None
        )
    check_unsupported_args('Rolling.apply', ekn__jjldb, qloto__kgwfv,
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
    ekn__jjldb = dict(win_type=win_type, axis=axis, closed=closed, method=
        method)
    qloto__kgwfv = dict(win_type=None, axis=0, closed=None, method='single')
    check_unsupported_args('GroupBy.rolling', ekn__jjldb, qloto__kgwfv,
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
        vjis__oqf = f'def impl(rolling, {_get_rolling_func_args(fname)}):\n'
        tqwk__zkvqm = f"'{rolling.on}'" if isinstance(rolling.on, str
            ) else f'{rolling.on}'
        selection = ''
        if rolling.explicit_select:
            selection = '[{}]'.format(', '.join(f"'{qypt__mfim}'" if
                isinstance(qypt__mfim, str) else f'{qypt__mfim}' for
                qypt__mfim in rolling.selection if qypt__mfim != rolling.on))
        qnot__twf = fvgwt__nnxz = ''
        if fname == 'apply':
            qnot__twf = 'func, raw, args, kwargs'
            fvgwt__nnxz = 'func, raw, None, None, args, kwargs'
        if fname == 'corr':
            qnot__twf = fvgwt__nnxz = 'other, pairwise'
        if fname == 'cov':
            qnot__twf = fvgwt__nnxz = 'other, pairwise, ddof'
        tlxhi__qdpld = (
            f'lambda df, window, minp, center, {qnot__twf}: bodo.hiframes.pd_rolling_ext.init_rolling(df, window, minp, center, {tqwk__zkvqm}){selection}.{fname}({fvgwt__nnxz})'
            )
        vjis__oqf += f"""  return rolling.obj.apply({tlxhi__qdpld}, rolling.window, rolling.min_periods, rolling.center, {qnot__twf})
"""
        ltld__afxi = {}
        exec(vjis__oqf, {'bodo': bodo}, ltld__afxi)
        impl = ltld__afxi['impl']
        return impl
    xszrb__zze = isinstance(rolling.obj_type, SeriesType)
    if fname in ('corr', 'cov'):
        out_cols = None if xszrb__zze else _get_corr_cov_out_cols(rolling,
            other, fname)
        df_cols = None if xszrb__zze else rolling.obj_type.columns
        other_cols = None if xszrb__zze else other.columns
        fqlb__pgoo, zyl__wwf = _gen_corr_cov_out_data(out_cols, df_cols,
            other_cols, rolling.window_type, fname)
    else:
        fqlb__pgoo, zyl__wwf, out_cols = _gen_df_rolling_out_data(rolling)
    otdn__gkslg = xszrb__zze or len(rolling.selection) == (1 if rolling.on is
        None else 2) and rolling.series_select
    amsh__zod = f'def impl(rolling, {_get_rolling_func_args(fname)}):\n'
    amsh__zod += '  df = rolling.obj\n'
    amsh__zod += '  index = {}\n'.format(
        'bodo.hiframes.pd_series_ext.get_series_index(df)' if xszrb__zze else
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)')
    enu__tafr = 'None'
    if xszrb__zze:
        enu__tafr = 'bodo.hiframes.pd_series_ext.get_series_name(df)'
    elif otdn__gkslg:
        greq__mqpm = (set(out_cols) - set([rolling.on])).pop()
        enu__tafr = f"'{greq__mqpm}'" if isinstance(greq__mqpm, str) else str(
            greq__mqpm)
    amsh__zod += f'  name = {enu__tafr}\n'
    amsh__zod += '  window = rolling.window\n'
    amsh__zod += '  center = rolling.center\n'
    amsh__zod += '  minp = rolling.min_periods\n'
    amsh__zod += f'  on_arr = {zyl__wwf}\n'
    if fname == 'apply':
        amsh__zod += (
            f'  index_arr = bodo.utils.conversion.index_to_array(index)\n')
    else:
        amsh__zod += f"  func = '{fname}'\n"
        amsh__zod += f'  index_arr = None\n'
        amsh__zod += f'  raw = False\n'
    if otdn__gkslg:
        amsh__zod += (
            f'  return bodo.hiframes.pd_series_ext.init_series({fqlb__pgoo}, index, name)'
            )
        ltld__afxi = {}
        hxq__dnjk = {'bodo': bodo}
        exec(amsh__zod, hxq__dnjk, ltld__afxi)
        impl = ltld__afxi['impl']
        return impl
    return bodo.hiframes.dataframe_impl._gen_init_df(amsh__zod, out_cols,
        fqlb__pgoo)


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
        dgiw__tfd = create_rolling_overload(fname)
        overload_method(RollingType, fname, inline='always', no_unliteral=True
            )(dgiw__tfd)


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
    ycaez__blyc = rolling.selection
    if rolling.on is not None:
        raise BodoError(
            f'variable window rolling {func_name} not supported yet.')
    out_cols = tuple(sorted(set(ycaez__blyc) | set(other.columns), key=lambda
        k: str(k)))
    return out_cols


def _gen_corr_cov_out_data(out_cols, df_cols, other_cols, window_type,
    func_name):
    szjb__vtj = not isinstance(window_type, types.Integer)
    zyl__wwf = 'None'
    if szjb__vtj:
        zyl__wwf = 'bodo.utils.conversion.index_to_array(index)'
    vxtcs__gkeqe = 'on_arr, ' if szjb__vtj else ''
    fqlb__pgoo = []
    if out_cols is None:
        return (
            f'bodo.hiframes.rolling.rolling_{func_name}(bodo.hiframes.pd_series_ext.get_series_data(df), bodo.hiframes.pd_series_ext.get_series_data(other), {vxtcs__gkeqe}window, minp, center)'
            , zyl__wwf)
    for greq__mqpm in out_cols:
        if greq__mqpm in df_cols and greq__mqpm in other_cols:
            hws__dajh = df_cols.index(greq__mqpm)
            uvsar__cjsud = other_cols.index(greq__mqpm)
            udl__ybmf = (
                f'bodo.hiframes.rolling.rolling_{func_name}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {hws__dajh}), bodo.hiframes.pd_dataframe_ext.get_dataframe_data(other, {uvsar__cjsud}), {vxtcs__gkeqe}window, minp, center)'
                )
        else:
            udl__ybmf = 'np.full(len(df), np.nan)'
        fqlb__pgoo.append(udl__ybmf)
    return ', '.join(fqlb__pgoo), zyl__wwf


@overload_method(RollingType, 'corr', inline='always', no_unliteral=True)
def overload_rolling_corr(rolling, other=None, pairwise=None, ddof=1):
    vkaq__lted = {'pairwise': pairwise, 'ddof': ddof}
    kesak__txwv = {'pairwise': None, 'ddof': 1}
    check_unsupported_args('pandas.core.window.rolling.Rolling.corr',
        vkaq__lted, kesak__txwv, package_name='pandas', module_name='Window')
    return _gen_rolling_impl(rolling, 'corr', other)


@overload_method(RollingType, 'cov', inline='always', no_unliteral=True)
def overload_rolling_cov(rolling, other=None, pairwise=None, ddof=1):
    vkaq__lted = {'ddof': ddof, 'pairwise': pairwise}
    kesak__txwv = {'ddof': 1, 'pairwise': None}
    check_unsupported_args('pandas.core.window.rolling.Rolling.cov',
        vkaq__lted, kesak__txwv, package_name='pandas', module_name='Window')
    return _gen_rolling_impl(rolling, 'cov', other)


@infer
class GetItemDataFrameRolling2(AbstractTemplate):
    key = 'static_getitem'

    def generic(self, args, kws):
        rolling, qsbkv__wuzce = args
        if isinstance(rolling, RollingType):
            ycaez__blyc = rolling.obj_type.selection if isinstance(rolling.
                obj_type, DataFrameGroupByType) else rolling.obj_type.columns
            series_select = False
            if isinstance(qsbkv__wuzce, (tuple, list)):
                if len(set(qsbkv__wuzce).difference(set(ycaez__blyc))) > 0:
                    raise_bodo_error(
                        'rolling: selected column {} not found in dataframe'
                        .format(set(qsbkv__wuzce).difference(set(ycaez__blyc)))
                        )
                selection = list(qsbkv__wuzce)
            else:
                if qsbkv__wuzce not in ycaez__blyc:
                    raise_bodo_error(
                        'rolling: selected column {} not found in dataframe'
                        .format(qsbkv__wuzce))
                selection = [qsbkv__wuzce]
                series_select = True
            if rolling.on is not None:
                selection.append(rolling.on)
            mrp__nrzby = RollingType(rolling.obj_type, rolling.window_type,
                rolling.on, tuple(selection), True, series_select)
            return signature(mrp__nrzby, *args)


@lower_builtin('static_getitem', RollingType, types.Any)
def static_getitem_df_groupby(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@infer_getattr
class RollingAttribute(AttributeTemplate):
    key = RollingType

    def generic_resolve(self, rolling, attr):
        ycaez__blyc = ()
        if isinstance(rolling.obj_type, DataFrameGroupByType):
            ycaez__blyc = rolling.obj_type.selection
        if isinstance(rolling.obj_type, DataFrameType):
            ycaez__blyc = rolling.obj_type.columns
        if attr in ycaez__blyc:
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
    srjgc__gptp = obj.columns if isinstance(obj, DataFrameType
        ) else obj.df_type.columns if isinstance(obj, DataFrameGroupByType
        ) else []
    zdml__cqonu = [obj.data] if isinstance(obj, SeriesType
        ) else obj.data if isinstance(obj, DataFrameType) else obj.df_type.data
    if not is_overload_none(on) and (not is_literal_type(on) or 
        get_literal_value(on) not in srjgc__gptp):
        raise BodoError(
            f"{func_name}.rolling(): 'on' should be a constant column name.")
    if not is_overload_none(on):
        wgi__gbnbq = zdml__cqonu[srjgc__gptp.index(get_literal_value(on))]
        if not isinstance(wgi__gbnbq, types.Array
            ) or wgi__gbnbq.dtype != bodo.datetime64ns:
            raise BodoError(
                f"{func_name}.rolling(): 'on' column should have datetime64 data."
                )
    if not any(isinstance(hevlt__hfxnu.dtype, (types.Boolean, types.Number)
        ) for hevlt__hfxnu in zdml__cqonu):
        raise BodoError(f'{func_name}.rolling(): No numeric types to aggregate'
            )
