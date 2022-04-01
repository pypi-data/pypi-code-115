"""Support for Pandas Groupby operations
"""
import operator
from enum import Enum
import numba
import numpy as np
from numba.core import cgutils, types
from numba.core.imputils import impl_ret_borrowed
from numba.core.registry import CPUDispatcher
from numba.core.typing.templates import AbstractTemplate, bound_function, infer_global, signature
from numba.extending import infer, infer_getattr, intrinsic, lower_builtin, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_model
import bodo
from bodo.hiframes.pd_dataframe_ext import DataFrameType
from bodo.hiframes.pd_index_ext import NumericIndexType, RangeIndexType
from bodo.hiframes.pd_multi_index_ext import MultiIndexType
from bodo.hiframes.pd_series_ext import HeterogeneousSeriesType, SeriesType
from bodo.libs.array import arr_info_list_to_table, array_to_info, delete_table, delete_table_decref_arrays, get_groupby_labels, get_null_shuffle_info, get_shuffle_info, info_from_table, info_to_array, reverse_shuffle_table, shuffle_table
from bodo.libs.array_item_arr_ext import ArrayItemArrayType
from bodo.libs.decimal_arr_ext import Decimal128Type
from bodo.libs.int_arr_ext import IntDtype, IntegerArrayType
from bodo.libs.str_arr_ext import string_array_type
from bodo.libs.str_ext import string_type
from bodo.libs.tuple_arr_ext import TupleArrayType
from bodo.utils.templates import OverloadedKeyAttributeTemplate
from bodo.utils.transform import gen_const_tup, get_call_expr_arg, get_const_func_output_type
from bodo.utils.typing import BodoError, check_unsupported_args, create_unsupported_overload, dtype_to_array_type, get_index_data_arr_types, get_index_name_types, get_literal_value, get_overload_const_bool, get_overload_const_func, get_overload_const_list, get_overload_const_str, get_overload_constant_dict, get_udf_error_msg, get_udf_out_arr_type, is_dtype_nullable, is_literal_type, is_overload_constant_bool, is_overload_constant_dict, is_overload_constant_list, is_overload_constant_str, is_overload_false, is_overload_none, is_overload_true, list_cumulative, raise_bodo_error, to_str_arr_if_dict_array
from bodo.utils.utils import dt_err, is_expr


class DataFrameGroupByType(types.Type):

    def __init__(self, df_type, keys, selection, as_index, dropna=True,
        explicit_select=False, series_select=False):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df_type,
            'pandas.groupby()')
        self.df_type = df_type
        self.keys = keys
        self.selection = selection
        self.as_index = as_index
        self.dropna = dropna
        self.explicit_select = explicit_select
        self.series_select = series_select
        super(DataFrameGroupByType, self).__init__(name=
            f'DataFrameGroupBy({df_type}, {keys}, {selection}, {as_index}, {dropna}, {explicit_select}, {series_select})'
            )

    def copy(self):
        return DataFrameGroupByType(self.df_type, self.keys, self.selection,
            self.as_index, self.dropna, self.explicit_select, self.
            series_select)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(DataFrameGroupByType)
class GroupbyModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        ssylw__ifli = [('obj', fe_type.df_type)]
        super(GroupbyModel, self).__init__(dmm, fe_type, ssylw__ifli)


make_attribute_wrapper(DataFrameGroupByType, 'obj', 'obj')


def validate_udf(func_name, func):
    if not isinstance(func, (types.functions.MakeFunctionLiteral, bodo.
        utils.typing.FunctionLiteral, types.Dispatcher, CPUDispatcher)):
        raise_bodo_error(
            f"Groupby.{func_name}: 'func' must be user defined function")


@intrinsic
def init_groupby(typingctx, obj_type, by_type, as_index_type=None,
    dropna_type=None):

    def codegen(context, builder, signature, args):
        vjxpc__enlsq = args[0]
        irc__ooqhz = signature.return_type
        xglfc__jgoz = cgutils.create_struct_proxy(irc__ooqhz)(context, builder)
        xglfc__jgoz.obj = vjxpc__enlsq
        context.nrt.incref(builder, signature.args[0], vjxpc__enlsq)
        return xglfc__jgoz._getvalue()
    if is_overload_constant_list(by_type):
        keys = tuple(get_overload_const_list(by_type))
    elif is_literal_type(by_type):
        keys = get_literal_value(by_type),
    else:
        assert False, 'Reached unreachable code in init_groupby; there is an validate_groupby_spec'
    selection = list(obj_type.columns)
    for ghu__rzbxc in keys:
        selection.remove(ghu__rzbxc)
    if is_overload_constant_bool(as_index_type):
        as_index = is_overload_true(as_index_type)
    else:
        as_index = True
    if is_overload_constant_bool(dropna_type):
        dropna = is_overload_true(dropna_type)
    else:
        dropna = True
    irc__ooqhz = DataFrameGroupByType(obj_type, keys, tuple(selection),
        as_index, dropna, False)
    return irc__ooqhz(obj_type, by_type, as_index_type, dropna_type), codegen


@lower_builtin('groupby.count', types.VarArg(types.Any))
@lower_builtin('groupby.size', types.VarArg(types.Any))
@lower_builtin('groupby.apply', types.VarArg(types.Any))
@lower_builtin('groupby.agg', types.VarArg(types.Any))
def lower_groupby_count_dummy(context, builder, sig, args):
    return context.get_constant_null(sig.return_type)


@infer
class StaticGetItemDataFrameGroupBy(AbstractTemplate):
    key = 'static_getitem'

    def generic(self, args, kws):
        grpby, zrn__lmf = args
        if isinstance(grpby, DataFrameGroupByType):
            series_select = False
            if isinstance(zrn__lmf, (tuple, list)):
                if len(set(zrn__lmf).difference(set(grpby.df_type.columns))
                    ) > 0:
                    raise_bodo_error(
                        'groupby: selected column {} not found in dataframe'
                        .format(set(zrn__lmf).difference(set(grpby.df_type.
                        columns))))
                selection = zrn__lmf
            else:
                if zrn__lmf not in grpby.df_type.columns:
                    raise_bodo_error(
                        'groupby: selected column {} not found in dataframe'
                        .format(zrn__lmf))
                selection = zrn__lmf,
                series_select = True
            cmzf__jfj = DataFrameGroupByType(grpby.df_type, grpby.keys,
                selection, grpby.as_index, grpby.dropna, True, series_select)
            return signature(cmzf__jfj, *args)


@infer_global(operator.getitem)
class GetItemDataFrameGroupBy(AbstractTemplate):

    def generic(self, args, kws):
        grpby, zrn__lmf = args
        if isinstance(grpby, DataFrameGroupByType) and is_literal_type(zrn__lmf
            ):
            cmzf__jfj = StaticGetItemDataFrameGroupBy.generic(self, (grpby,
                get_literal_value(zrn__lmf)), {}).return_type
            return signature(cmzf__jfj, *args)


GetItemDataFrameGroupBy.prefer_literal = True


@lower_builtin('static_getitem', DataFrameGroupByType, types.Any)
@lower_builtin(operator.getitem, DataFrameGroupByType, types.Any)
def static_getitem_df_groupby(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


def get_groupby_output_dtype(arr_type, func_name, index_type=None):
    arr_type = to_str_arr_if_dict_array(arr_type)
    ane__xxpeo = arr_type == ArrayItemArrayType(string_array_type)
    ghhne__enqdk = arr_type.dtype
    if isinstance(ghhne__enqdk, bodo.hiframes.datetime_timedelta_ext.
        DatetimeTimeDeltaType):
        raise BodoError(
            f"""column type of {ghhne__enqdk} is not supported in groupby built-in function {func_name}.
{dt_err}"""
            )
    if func_name == 'median' and not isinstance(ghhne__enqdk, (
        Decimal128Type, types.Float, types.Integer)):
        return (None,
            'For median, only column of integer, float or Decimal type are allowed'
            )
    if func_name in ('first', 'last', 'sum', 'prod', 'min', 'max', 'count',
        'nunique', 'head') and isinstance(arr_type, (TupleArrayType,
        ArrayItemArrayType)):
        return (None,
            f'column type of list/tuple of {ghhne__enqdk} is not supported in groupby built-in function {func_name}'
            )
    if func_name in {'median', 'mean', 'var', 'std'} and isinstance(
        ghhne__enqdk, (Decimal128Type, types.Integer, types.Float)):
        return dtype_to_array_type(types.float64), 'ok'
    if not isinstance(ghhne__enqdk, (types.Integer, types.Float, types.Boolean)
        ):
        if ane__xxpeo or ghhne__enqdk == types.unicode_type:
            if func_name not in {'count', 'nunique', 'min', 'max', 'sum',
                'first', 'last', 'head'}:
                return (None,
                    f'column type of strings or list of strings is not supported in groupby built-in function {func_name}'
                    )
        else:
            if isinstance(ghhne__enqdk, bodo.PDCategoricalDtype):
                if func_name in ('min', 'max') and not ghhne__enqdk.ordered:
                    return (None,
                        f'categorical column must be ordered in groupby built-in function {func_name}'
                        )
            if func_name not in {'count', 'nunique', 'min', 'max', 'first',
                'last', 'head'}:
                return (None,
                    f'column type of {ghhne__enqdk} is not supported in groupby built-in function {func_name}'
                    )
    if isinstance(ghhne__enqdk, types.Boolean) and func_name in {'cumsum',
        'sum', 'mean', 'std', 'var'}:
        return (None,
            f'groupby built-in functions {func_name} does not support boolean column'
            )
    if func_name in {'idxmin', 'idxmax'}:
        return dtype_to_array_type(get_index_data_arr_types(index_type)[0].
            dtype), 'ok'
    if func_name in {'count', 'nunique'}:
        return dtype_to_array_type(types.int64), 'ok'
    else:
        return arr_type, 'ok'


def get_pivot_output_dtype(arr_type, func_name, index_type=None):
    ghhne__enqdk = arr_type.dtype
    if func_name in {'count'}:
        return IntDtype(types.int64)
    if func_name in {'sum', 'prod', 'min', 'max'}:
        if func_name in {'sum', 'prod'} and not isinstance(ghhne__enqdk, (
            types.Integer, types.Float)):
            raise BodoError(
                'pivot_table(): sum and prod operations require integer or float input'
                )
        if isinstance(ghhne__enqdk, types.Integer):
            return IntDtype(ghhne__enqdk)
        return ghhne__enqdk
    if func_name in {'mean', 'var', 'std'}:
        return types.float64
    raise BodoError('invalid pivot operation')


def check_args_kwargs(func_name, len_args, args, kws):
    if len(kws) > 0:
        vtsl__heb = list(kws.keys())[0]
        raise BodoError(
            f"Groupby.{func_name}() got an unexpected keyword argument '{vtsl__heb}'."
            )
    elif len(args) > len_args:
        raise BodoError(
            f'Groupby.{func_name}() takes {len_args + 1} positional argument but {len(args)} were given.'
            )


class ColumnType(Enum):
    KeyColumn = 0
    NumericalColumn = 1
    NonNumericalColumn = 2


def get_keys_not_as_index(grp, out_columns, out_data, out_column_type,
    multi_level_names=False):
    for ghu__rzbxc in grp.keys:
        if multi_level_names:
            cqh__vira = ghu__rzbxc, ''
        else:
            cqh__vira = ghu__rzbxc
        dctr__vgk = grp.df_type.columns.index(ghu__rzbxc)
        data = to_str_arr_if_dict_array(grp.df_type.data[dctr__vgk])
        out_columns.append(cqh__vira)
        out_data.append(data)
        out_column_type.append(ColumnType.KeyColumn.value)


def get_agg_typ(grp, args, func_name, typing_context, target_context, func=
    None, kws=None):
    index = RangeIndexType(types.none)
    out_data = []
    out_columns = []
    out_column_type = []
    if func_name == 'head':
        grp.dropna = False
        grp.as_index = True
    if not grp.as_index:
        get_keys_not_as_index(grp, out_columns, out_data, out_column_type)
    elif func_name == 'head':
        if grp.df_type.index == index:
            index = NumericIndexType(types.int64, types.none)
        else:
            index = grp.df_type.index
    elif len(grp.keys) > 1:
        sqvnn__yzvu = tuple(grp.df_type.columns.index(grp.keys[gzhic__bfi]) for
            gzhic__bfi in range(len(grp.keys)))
        lbgzp__bdmp = tuple(grp.df_type.data[dctr__vgk] for dctr__vgk in
            sqvnn__yzvu)
        lbgzp__bdmp = tuple(to_str_arr_if_dict_array(jbmc__pkgfr) for
            jbmc__pkgfr in lbgzp__bdmp)
        index = MultiIndexType(lbgzp__bdmp, tuple(types.StringLiteral(
            ghu__rzbxc) for ghu__rzbxc in grp.keys))
    else:
        dctr__vgk = grp.df_type.columns.index(grp.keys[0])
        ctjp__dtbsz = to_str_arr_if_dict_array(grp.df_type.data[dctr__vgk])
        index = bodo.hiframes.pd_index_ext.array_type_to_index(ctjp__dtbsz,
            types.StringLiteral(grp.keys[0]))
    gmgan__nzn = {}
    bqd__muej = []
    if func_name in ('size', 'count'):
        kws = dict(kws) if kws else {}
        check_args_kwargs(func_name, 0, args, kws)
    if func_name == 'size':
        out_data.append(types.Array(types.int64, 1, 'C'))
        out_columns.append('size')
        gmgan__nzn[None, 'size'] = 'size'
    else:
        columns = (grp.selection if func_name != 'head' or grp.
            explicit_select else grp.df_type.columns)
        for ocpyi__hgulf in columns:
            dctr__vgk = grp.df_type.columns.index(ocpyi__hgulf)
            data = grp.df_type.data[dctr__vgk]
            data = to_str_arr_if_dict_array(data)
            rar__qwtwb = ColumnType.NonNumericalColumn.value
            if isinstance(data, (types.Array, IntegerArrayType)
                ) and isinstance(data.dtype, (types.Integer, types.Float)):
                rar__qwtwb = ColumnType.NumericalColumn.value
            if func_name == 'agg':
                try:
                    zyouk__rgfu = SeriesType(data.dtype, data, None,
                        string_type)
                    wul__jekq = get_const_func_output_type(func, (
                        zyouk__rgfu,), {}, typing_context, target_context)
                    if wul__jekq != ArrayItemArrayType(string_array_type):
                        wul__jekq = dtype_to_array_type(wul__jekq)
                    err_msg = 'ok'
                except:
                    raise_bodo_error(
                        'Groupy.agg()/Groupy.aggregate(): column {col} of type {type} is unsupported/not a valid input type for user defined function'
                        .format(col=ocpyi__hgulf, type=data.dtype))
            else:
                if func_name in ('first', 'last', 'min', 'max'):
                    kws = dict(kws) if kws else {}
                    nwf__dez = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', False)
                    esbsw__utno = args[1] if len(args) > 1 else kws.pop(
                        'min_count', -1)
                    uboto__iviu = dict(numeric_only=nwf__dez, min_count=
                        esbsw__utno)
                    fkf__asru = dict(numeric_only=False, min_count=-1)
                    check_unsupported_args(f'Groupby.{func_name}',
                        uboto__iviu, fkf__asru, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('sum', 'prod'):
                    kws = dict(kws) if kws else {}
                    nwf__dez = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', True)
                    esbsw__utno = args[1] if len(args) > 1 else kws.pop(
                        'min_count', 0)
                    uboto__iviu = dict(numeric_only=nwf__dez, min_count=
                        esbsw__utno)
                    fkf__asru = dict(numeric_only=True, min_count=0)
                    check_unsupported_args(f'Groupby.{func_name}',
                        uboto__iviu, fkf__asru, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('mean', 'median'):
                    kws = dict(kws) if kws else {}
                    nwf__dez = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', True)
                    uboto__iviu = dict(numeric_only=nwf__dez)
                    fkf__asru = dict(numeric_only=True)
                    check_unsupported_args(f'Groupby.{func_name}',
                        uboto__iviu, fkf__asru, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('idxmin', 'idxmax'):
                    kws = dict(kws) if kws else {}
                    jei__vljm = args[0] if len(args) > 0 else kws.pop('axis', 0
                        )
                    zgahi__swmz = args[1] if len(args) > 1 else kws.pop(
                        'skipna', True)
                    uboto__iviu = dict(axis=jei__vljm, skipna=zgahi__swmz)
                    fkf__asru = dict(axis=0, skipna=True)
                    check_unsupported_args(f'Groupby.{func_name}',
                        uboto__iviu, fkf__asru, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('var', 'std'):
                    kws = dict(kws) if kws else {}
                    amnm__emcxe = args[0] if len(args) > 0 else kws.pop('ddof',
                        1)
                    uboto__iviu = dict(ddof=amnm__emcxe)
                    fkf__asru = dict(ddof=1)
                    check_unsupported_args(f'Groupby.{func_name}',
                        uboto__iviu, fkf__asru, package_name='pandas',
                        module_name='GroupBy')
                elif func_name == 'nunique':
                    kws = dict(kws) if kws else {}
                    dropna = args[0] if len(args) > 0 else kws.pop('dropna', 1)
                    check_args_kwargs(func_name, 1, args, kws)
                elif func_name == 'head':
                    if len(args) == 0:
                        kws.pop('n', None)
                wul__jekq, err_msg = get_groupby_output_dtype(data,
                    func_name, grp.df_type.index)
            if err_msg == 'ok':
                rebar__nhs = to_str_arr_if_dict_array(wul__jekq)
                out_data.append(rebar__nhs)
                out_columns.append(ocpyi__hgulf)
                if func_name == 'agg':
                    psd__ndomm = bodo.ir.aggregate._get_udf_name(bodo.ir.
                        aggregate._get_const_agg_func(func, None))
                    gmgan__nzn[ocpyi__hgulf, psd__ndomm] = ocpyi__hgulf
                else:
                    gmgan__nzn[ocpyi__hgulf, func_name] = ocpyi__hgulf
                out_column_type.append(rar__qwtwb)
            else:
                bqd__muej.append(err_msg)
    if func_name == 'sum':
        ebt__tej = any([(dty__styeh == ColumnType.NumericalColumn.value) for
            dty__styeh in out_column_type])
        if ebt__tej:
            out_data = [dty__styeh for dty__styeh, hepi__vhrov in zip(
                out_data, out_column_type) if hepi__vhrov != ColumnType.
                NonNumericalColumn.value]
            out_columns = [dty__styeh for dty__styeh, hepi__vhrov in zip(
                out_columns, out_column_type) if hepi__vhrov != ColumnType.
                NonNumericalColumn.value]
            gmgan__nzn = {}
            for ocpyi__hgulf in out_columns:
                if grp.as_index is False and ocpyi__hgulf in grp.keys:
                    continue
                gmgan__nzn[ocpyi__hgulf, func_name] = ocpyi__hgulf
    noqw__vwqx = len(bqd__muej)
    if len(out_data) == 0:
        if noqw__vwqx == 0:
            raise BodoError('No columns in output.')
        else:
            raise BodoError(
                'No columns in output. {} column{} dropped for following reasons: {}'
                .format(noqw__vwqx, ' was' if noqw__vwqx == 1 else 's were',
                ','.join(bqd__muej)))
    wucq__nzh = DataFrameType(tuple(out_data), index, tuple(out_columns))
    if (len(grp.selection) == 1 and grp.series_select and grp.as_index or 
        func_name == 'size' and grp.as_index):
        if isinstance(out_data[0], IntegerArrayType):
            kfrf__ovufj = IntDtype(out_data[0].dtype)
        else:
            kfrf__ovufj = out_data[0].dtype
        cmu__vln = types.none if func_name == 'size' else types.StringLiteral(
            grp.selection[0])
        wucq__nzh = SeriesType(kfrf__ovufj, index=index, name_typ=cmu__vln)
    return signature(wucq__nzh, *args), gmgan__nzn


def get_agg_funcname_and_outtyp(grp, col, f_val, typing_context, target_context
    ):
    abflm__ddyz = True
    if isinstance(f_val, str):
        abflm__ddyz = False
        leekg__tmg = f_val
    elif is_overload_constant_str(f_val):
        abflm__ddyz = False
        leekg__tmg = get_overload_const_str(f_val)
    elif bodo.utils.typing.is_builtin_function(f_val):
        abflm__ddyz = False
        leekg__tmg = bodo.utils.typing.get_builtin_function_name(f_val)
    if not abflm__ddyz:
        if leekg__tmg not in bodo.ir.aggregate.supported_agg_funcs[:-1]:
            raise BodoError(f'unsupported aggregate function {leekg__tmg}')
        cmzf__jfj = DataFrameGroupByType(grp.df_type, grp.keys, (col,), grp
            .as_index, grp.dropna, True, True)
        out_tp = get_agg_typ(cmzf__jfj, (), leekg__tmg, typing_context,
            target_context)[0].return_type
    else:
        if is_expr(f_val, 'make_function'):
            ozzp__ead = types.functions.MakeFunctionLiteral(f_val)
        else:
            ozzp__ead = f_val
        validate_udf('agg', ozzp__ead)
        func = get_overload_const_func(ozzp__ead, None)
        ajwhy__zrgwr = func.code if hasattr(func, 'code') else func.__code__
        leekg__tmg = ajwhy__zrgwr.co_name
        cmzf__jfj = DataFrameGroupByType(grp.df_type, grp.keys, (col,), grp
            .as_index, grp.dropna, True, True)
        out_tp = get_agg_typ(cmzf__jfj, (), 'agg', typing_context,
            target_context, ozzp__ead)[0].return_type
    return leekg__tmg, out_tp


def resolve_agg(grp, args, kws, typing_context, target_context):
    func = get_call_expr_arg('agg', args, dict(kws), 0, 'func', default=
        types.none)
    sbzn__arz = kws and all(isinstance(xlr__rduk, types.Tuple) and len(
        xlr__rduk) == 2 for xlr__rduk in kws.values())
    if is_overload_none(func) and not sbzn__arz:
        raise_bodo_error("Groupby.agg()/aggregate(): Must provide 'func'")
    if len(args) > 1 or kws and not sbzn__arz:
        raise_bodo_error(
            'Groupby.agg()/aggregate(): passing extra arguments to functions not supported yet.'
            )
    oqas__avk = False

    def _append_out_type(grp, out_data, out_tp):
        if grp.as_index is False:
            out_data.append(out_tp.data[len(grp.keys)])
        else:
            out_data.append(out_tp.data)
    if sbzn__arz or is_overload_constant_dict(func):
        if sbzn__arz:
            iken__sih = [get_literal_value(nqxm__kul) for nqxm__kul,
                edll__fleti in kws.values()]
            mpyjf__oea = [get_literal_value(xxxqj__oym) for edll__fleti,
                xxxqj__oym in kws.values()]
        else:
            uixd__isszv = get_overload_constant_dict(func)
            iken__sih = tuple(uixd__isszv.keys())
            mpyjf__oea = tuple(uixd__isszv.values())
        if 'head' in mpyjf__oea:
            raise BodoError(
                'Groupby.agg()/aggregate(): head cannot be mixed with other groupby operations.'
                )
        if any(ocpyi__hgulf not in grp.selection and ocpyi__hgulf not in
            grp.keys for ocpyi__hgulf in iken__sih):
            raise_bodo_error(
                f'Selected column names {iken__sih} not all available in dataframe column names {grp.selection}'
                )
        multi_level_names = any(isinstance(f_val, (tuple, list)) for f_val in
            mpyjf__oea)
        if sbzn__arz and multi_level_names:
            raise_bodo_error(
                'Groupby.agg()/aggregate(): cannot pass multiple functions in a single pd.NamedAgg()'
                )
        gmgan__nzn = {}
        out_columns = []
        out_data = []
        out_column_type = []
        wzc__tixjk = []
        if not grp.as_index:
            get_keys_not_as_index(grp, out_columns, out_data,
                out_column_type, multi_level_names=multi_level_names)
        for ikuif__qcfq, f_val in zip(iken__sih, mpyjf__oea):
            if isinstance(f_val, (tuple, list)):
                zuaj__qufmf = 0
                for ozzp__ead in f_val:
                    leekg__tmg, out_tp = get_agg_funcname_and_outtyp(grp,
                        ikuif__qcfq, ozzp__ead, typing_context, target_context)
                    oqas__avk = leekg__tmg in list_cumulative
                    if leekg__tmg == '<lambda>' and len(f_val) > 1:
                        leekg__tmg = '<lambda_' + str(zuaj__qufmf) + '>'
                        zuaj__qufmf += 1
                    out_columns.append((ikuif__qcfq, leekg__tmg))
                    gmgan__nzn[ikuif__qcfq, leekg__tmg
                        ] = ikuif__qcfq, leekg__tmg
                    _append_out_type(grp, out_data, out_tp)
            else:
                leekg__tmg, out_tp = get_agg_funcname_and_outtyp(grp,
                    ikuif__qcfq, f_val, typing_context, target_context)
                oqas__avk = leekg__tmg in list_cumulative
                if multi_level_names:
                    out_columns.append((ikuif__qcfq, leekg__tmg))
                    gmgan__nzn[ikuif__qcfq, leekg__tmg
                        ] = ikuif__qcfq, leekg__tmg
                elif not sbzn__arz:
                    out_columns.append(ikuif__qcfq)
                    gmgan__nzn[ikuif__qcfq, leekg__tmg] = ikuif__qcfq
                elif sbzn__arz:
                    wzc__tixjk.append(leekg__tmg)
                _append_out_type(grp, out_data, out_tp)
        if sbzn__arz:
            for gzhic__bfi, kzblz__klg in enumerate(kws.keys()):
                out_columns.append(kzblz__klg)
                gmgan__nzn[iken__sih[gzhic__bfi], wzc__tixjk[gzhic__bfi]
                    ] = kzblz__klg
        if oqas__avk:
            index = grp.df_type.index
        else:
            index = out_tp.index
        wucq__nzh = DataFrameType(tuple(out_data), index, tuple(out_columns))
        return signature(wucq__nzh, *args), gmgan__nzn
    if isinstance(func, types.BaseTuple) and not isinstance(func, types.
        LiteralStrKeyDict):
        if not (len(grp.selection) == 1 and grp.explicit_select):
            raise_bodo_error(
                'Groupby.agg()/aggregate(): must select exactly one column when more than one functions supplied'
                )
        assert len(func) > 0
        out_data = []
        out_columns = []
        out_column_type = []
        zuaj__qufmf = 0
        if not grp.as_index:
            get_keys_not_as_index(grp, out_columns, out_data, out_column_type)
        gmgan__nzn = {}
        bjecg__yvl = grp.selection[0]
        for f_val in func.types:
            leekg__tmg, out_tp = get_agg_funcname_and_outtyp(grp,
                bjecg__yvl, f_val, typing_context, target_context)
            oqas__avk = leekg__tmg in list_cumulative
            if leekg__tmg == '<lambda>':
                leekg__tmg = '<lambda_' + str(zuaj__qufmf) + '>'
                zuaj__qufmf += 1
            out_columns.append(leekg__tmg)
            gmgan__nzn[bjecg__yvl, leekg__tmg] = leekg__tmg
            _append_out_type(grp, out_data, out_tp)
        if oqas__avk:
            index = grp.df_type.index
        else:
            index = out_tp.index
        wucq__nzh = DataFrameType(tuple(out_data), index, tuple(out_columns))
        return signature(wucq__nzh, *args), gmgan__nzn
    leekg__tmg = ''
    if types.unliteral(func) == types.unicode_type:
        leekg__tmg = get_overload_const_str(func)
    if bodo.utils.typing.is_builtin_function(func):
        leekg__tmg = bodo.utils.typing.get_builtin_function_name(func)
    if leekg__tmg:
        args = args[1:]
        kws.pop('func', None)
        return get_agg_typ(grp, args, leekg__tmg, typing_context, kws)
    validate_udf('agg', func)
    return get_agg_typ(grp, args, 'agg', typing_context, target_context, func)


def resolve_transformative(grp, args, kws, msg, name_operation):
    index = grp.df_type.index
    out_columns = []
    out_data = []
    if name_operation in list_cumulative:
        kws = dict(kws) if kws else {}
        jei__vljm = args[0] if len(args) > 0 else kws.pop('axis', 0)
        nwf__dez = args[1] if len(args) > 1 else kws.pop('numeric_only', False)
        zgahi__swmz = args[2] if len(args) > 2 else kws.pop('skipna', 1)
        uboto__iviu = dict(axis=jei__vljm, numeric_only=nwf__dez)
        fkf__asru = dict(axis=0, numeric_only=False)
        check_unsupported_args(f'Groupby.{name_operation}', uboto__iviu,
            fkf__asru, package_name='pandas', module_name='GroupBy')
        check_args_kwargs(name_operation, 3, args, kws)
    elif name_operation == 'shift':
        ghlle__aceuk = args[0] if len(args) > 0 else kws.pop('periods', 1)
        imbn__isyr = args[1] if len(args) > 1 else kws.pop('freq', None)
        jei__vljm = args[2] if len(args) > 2 else kws.pop('axis', 0)
        txo__jgka = args[3] if len(args) > 3 else kws.pop('fill_value', None)
        uboto__iviu = dict(freq=imbn__isyr, axis=jei__vljm, fill_value=
            txo__jgka)
        fkf__asru = dict(freq=None, axis=0, fill_value=None)
        check_unsupported_args(f'Groupby.{name_operation}', uboto__iviu,
            fkf__asru, package_name='pandas', module_name='GroupBy')
        check_args_kwargs(name_operation, 4, args, kws)
    elif name_operation == 'transform':
        kws = dict(kws)
        smeb__mdbh = args[0] if len(args) > 0 else kws.pop('func', None)
        rkny__yfqc = kws.pop('engine', None)
        qzzu__vomi = kws.pop('engine_kwargs', None)
        uboto__iviu = dict(engine=rkny__yfqc, engine_kwargs=qzzu__vomi)
        fkf__asru = dict(engine=None, engine_kwargs=None)
        check_unsupported_args(f'Groupby.transform', uboto__iviu, fkf__asru,
            package_name='pandas', module_name='GroupBy')
    gmgan__nzn = {}
    for ocpyi__hgulf in grp.selection:
        out_columns.append(ocpyi__hgulf)
        gmgan__nzn[ocpyi__hgulf, name_operation] = ocpyi__hgulf
        dctr__vgk = grp.df_type.columns.index(ocpyi__hgulf)
        data = grp.df_type.data[dctr__vgk]
        data = to_str_arr_if_dict_array(data)
        if name_operation == 'cumprod':
            if not isinstance(data.dtype, (types.Integer, types.Float)):
                raise BodoError(msg)
        if name_operation == 'cumsum':
            if data.dtype != types.unicode_type and data != ArrayItemArrayType(
                string_array_type) and not isinstance(data.dtype, (types.
                Integer, types.Float)):
                raise BodoError(msg)
        if name_operation in ('cummin', 'cummax'):
            if not isinstance(data.dtype, types.Integer
                ) and not is_dtype_nullable(data.dtype):
                raise BodoError(msg)
        if name_operation == 'shift':
            if isinstance(data, (TupleArrayType, ArrayItemArrayType)):
                raise BodoError(msg)
            if isinstance(data.dtype, bodo.hiframes.datetime_timedelta_ext.
                DatetimeTimeDeltaType):
                raise BodoError(
                    f"""column type of {data.dtype} is not supported in groupby built-in function shift.
{dt_err}"""
                    )
        if name_operation == 'transform':
            wul__jekq, err_msg = get_groupby_output_dtype(data,
                get_literal_value(smeb__mdbh), grp.df_type.index)
            if err_msg == 'ok':
                data = wul__jekq
            else:
                raise BodoError(
                    f'column type of {data.dtype} is not supported by {args[0]} yet.\n'
                    )
        out_data.append(data)
    if len(out_data) == 0:
        raise BodoError('No columns in output.')
    wucq__nzh = DataFrameType(tuple(out_data), index, tuple(out_columns))
    if len(grp.selection) == 1 and grp.series_select and grp.as_index:
        wucq__nzh = SeriesType(out_data[0].dtype, data=out_data[0], index=
            index, name_typ=types.StringLiteral(grp.selection[0]))
    return signature(wucq__nzh, *args), gmgan__nzn


def resolve_gb(grp, args, kws, func_name, typing_context, target_context,
    err_msg=''):
    if func_name in set(list_cumulative) | {'shift', 'transform'}:
        return resolve_transformative(grp, args, kws, err_msg, func_name)
    elif func_name in {'agg', 'aggregate'}:
        return resolve_agg(grp, args, kws, typing_context, target_context)
    else:
        return get_agg_typ(grp, args, func_name, typing_context,
            target_context, kws=kws)


@infer_getattr
class DataframeGroupByAttribute(OverloadedKeyAttributeTemplate):
    key = DataFrameGroupByType
    _attr_set = None

    @bound_function('groupby.agg', no_unliteral=True)
    def resolve_agg(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'agg', self.context, numba.core.
            registry.cpu_target.target_context)[0]

    @bound_function('groupby.aggregate', no_unliteral=True)
    def resolve_aggregate(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'agg', self.context, numba.core.
            registry.cpu_target.target_context)[0]

    @bound_function('groupby.sum', no_unliteral=True)
    def resolve_sum(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'sum', self.context, numba.core.
            registry.cpu_target.target_context)[0]

    @bound_function('groupby.count', no_unliteral=True)
    def resolve_count(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'count', self.context, numba.core
            .registry.cpu_target.target_context)[0]

    @bound_function('groupby.nunique', no_unliteral=True)
    def resolve_nunique(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'nunique', self.context, numba.
            core.registry.cpu_target.target_context)[0]

    @bound_function('groupby.median', no_unliteral=True)
    def resolve_median(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'median', self.context, numba.
            core.registry.cpu_target.target_context)[0]

    @bound_function('groupby.mean', no_unliteral=True)
    def resolve_mean(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'mean', self.context, numba.core.
            registry.cpu_target.target_context)[0]

    @bound_function('groupby.min', no_unliteral=True)
    def resolve_min(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'min', self.context, numba.core.
            registry.cpu_target.target_context)[0]

    @bound_function('groupby.max', no_unliteral=True)
    def resolve_max(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'max', self.context, numba.core.
            registry.cpu_target.target_context)[0]

    @bound_function('groupby.prod', no_unliteral=True)
    def resolve_prod(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'prod', self.context, numba.core.
            registry.cpu_target.target_context)[0]

    @bound_function('groupby.var', no_unliteral=True)
    def resolve_var(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'var', self.context, numba.core.
            registry.cpu_target.target_context)[0]

    @bound_function('groupby.std', no_unliteral=True)
    def resolve_std(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'std', self.context, numba.core.
            registry.cpu_target.target_context)[0]

    @bound_function('groupby.first', no_unliteral=True)
    def resolve_first(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'first', self.context, numba.core
            .registry.cpu_target.target_context)[0]

    @bound_function('groupby.last', no_unliteral=True)
    def resolve_last(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'last', self.context, numba.core.
            registry.cpu_target.target_context)[0]

    @bound_function('groupby.idxmin', no_unliteral=True)
    def resolve_idxmin(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'idxmin', self.context, numba.
            core.registry.cpu_target.target_context)[0]

    @bound_function('groupby.idxmax', no_unliteral=True)
    def resolve_idxmax(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'idxmax', self.context, numba.
            core.registry.cpu_target.target_context)[0]

    @bound_function('groupby.size', no_unliteral=True)
    def resolve_size(self, grp, args, kws):
        return resolve_gb(grp, args, kws, 'size', self.context, numba.core.
            registry.cpu_target.target_context)[0]

    @bound_function('groupby.cumsum', no_unliteral=True)
    def resolve_cumsum(self, grp, args, kws):
        msg = (
            'Groupby.cumsum() only supports columns of types integer, float, string or liststring'
            )
        return resolve_gb(grp, args, kws, 'cumsum', self.context, numba.
            core.registry.cpu_target.target_context, err_msg=msg)[0]

    @bound_function('groupby.cumprod', no_unliteral=True)
    def resolve_cumprod(self, grp, args, kws):
        msg = (
            'Groupby.cumprod() only supports columns of types integer and float'
            )
        return resolve_gb(grp, args, kws, 'cumprod', self.context, numba.
            core.registry.cpu_target.target_context, err_msg=msg)[0]

    @bound_function('groupby.cummin', no_unliteral=True)
    def resolve_cummin(self, grp, args, kws):
        msg = (
            'Groupby.cummin() only supports columns of types integer, float, string, liststring, date, datetime or timedelta'
            )
        return resolve_gb(grp, args, kws, 'cummin', self.context, numba.
            core.registry.cpu_target.target_context, err_msg=msg)[0]

    @bound_function('groupby.cummax', no_unliteral=True)
    def resolve_cummax(self, grp, args, kws):
        msg = (
            'Groupby.cummax() only supports columns of types integer, float, string, liststring, date, datetime or timedelta'
            )
        return resolve_gb(grp, args, kws, 'cummax', self.context, numba.
            core.registry.cpu_target.target_context, err_msg=msg)[0]

    @bound_function('groupby.shift', no_unliteral=True)
    def resolve_shift(self, grp, args, kws):
        msg = (
            'Column type of list/tuple is not supported in groupby built-in function shift'
            )
        return resolve_gb(grp, args, kws, 'shift', self.context, numba.core
            .registry.cpu_target.target_context, err_msg=msg)[0]

    @bound_function('groupby.pipe', no_unliteral=True)
    def resolve_pipe(self, grp, args, kws):
        return resolve_obj_pipe(self, grp, args, kws, 'GroupBy')

    @bound_function('groupby.transform', no_unliteral=True)
    def resolve_transform(self, grp, args, kws):
        msg = (
            'Groupby.transform() only supports sum, count, min, max, mean, and std operations'
            )
        return resolve_gb(grp, args, kws, 'transform', self.context, numba.
            core.registry.cpu_target.target_context, err_msg=msg)[0]

    @bound_function('groupby.head', no_unliteral=True)
    def resolve_head(self, grp, args, kws):
        msg = 'Unsupported Gropupby head operation.\n'
        return resolve_gb(grp, args, kws, 'head', self.context, numba.core.
            registry.cpu_target.target_context, err_msg=msg)[0]

    @bound_function('groupby.apply', no_unliteral=True)
    def resolve_apply(self, grp, args, kws):
        kws = dict(kws)
        func = args[0] if len(args) > 0 else kws.pop('func', None)
        f_args = tuple(args[1:]) if len(args) > 0 else ()
        pjz__tzbua = _get_groupby_apply_udf_out_type(func, grp, f_args, kws,
            self.context, numba.core.registry.cpu_target.target_context)
        wqnxo__vywvr = isinstance(pjz__tzbua, (SeriesType,
            HeterogeneousSeriesType)
            ) and pjz__tzbua.const_info is not None or not isinstance(
            pjz__tzbua, (SeriesType, DataFrameType))
        if wqnxo__vywvr:
            out_data = []
            out_columns = []
            out_column_type = []
            if not grp.as_index:
                get_keys_not_as_index(grp, out_columns, out_data,
                    out_column_type)
                kbwz__dgpg = NumericIndexType(types.int64, types.none)
            elif len(grp.keys) > 1:
                sqvnn__yzvu = tuple(grp.df_type.columns.index(grp.keys[
                    gzhic__bfi]) for gzhic__bfi in range(len(grp.keys)))
                lbgzp__bdmp = tuple(grp.df_type.data[dctr__vgk] for
                    dctr__vgk in sqvnn__yzvu)
                lbgzp__bdmp = tuple(to_str_arr_if_dict_array(jbmc__pkgfr) for
                    jbmc__pkgfr in lbgzp__bdmp)
                kbwz__dgpg = MultiIndexType(lbgzp__bdmp, tuple(types.
                    literal(ghu__rzbxc) for ghu__rzbxc in grp.keys))
            else:
                dctr__vgk = grp.df_type.columns.index(grp.keys[0])
                ctjp__dtbsz = grp.df_type.data[dctr__vgk]
                ctjp__dtbsz = to_str_arr_if_dict_array(ctjp__dtbsz)
                kbwz__dgpg = bodo.hiframes.pd_index_ext.array_type_to_index(
                    ctjp__dtbsz, types.literal(grp.keys[0]))
            out_data = tuple(out_data)
            out_columns = tuple(out_columns)
        else:
            dqjhu__tovgp = tuple(grp.df_type.data[grp.df_type.columns.index
                (ocpyi__hgulf)] for ocpyi__hgulf in grp.keys)
            dqjhu__tovgp = tuple(to_str_arr_if_dict_array(jbmc__pkgfr) for
                jbmc__pkgfr in dqjhu__tovgp)
            atomo__mvd = tuple(types.literal(xlr__rduk) for xlr__rduk in
                grp.keys) + get_index_name_types(pjz__tzbua.index)
            if not grp.as_index:
                dqjhu__tovgp = types.Array(types.int64, 1, 'C'),
                atomo__mvd = (types.none,) + get_index_name_types(pjz__tzbua
                    .index)
            kbwz__dgpg = MultiIndexType(dqjhu__tovgp +
                get_index_data_arr_types(pjz__tzbua.index), atomo__mvd)
        if wqnxo__vywvr:
            if isinstance(pjz__tzbua, HeterogeneousSeriesType):
                edll__fleti, xrrd__vzbw = pjz__tzbua.const_info
                gspde__sio = tuple(dtype_to_array_type(jbmc__pkgfr) for
                    jbmc__pkgfr in pjz__tzbua.data.types)
                xgvb__wwje = DataFrameType(out_data + gspde__sio,
                    kbwz__dgpg, out_columns + xrrd__vzbw)
            elif isinstance(pjz__tzbua, SeriesType):
                fcyjq__rvoow, xrrd__vzbw = pjz__tzbua.const_info
                gspde__sio = tuple(dtype_to_array_type(pjz__tzbua.dtype) for
                    edll__fleti in range(fcyjq__rvoow))
                xgvb__wwje = DataFrameType(out_data + gspde__sio,
                    kbwz__dgpg, out_columns + xrrd__vzbw)
            else:
                comig__pqw = get_udf_out_arr_type(pjz__tzbua)
                if not grp.as_index:
                    xgvb__wwje = DataFrameType(out_data + (comig__pqw,),
                        kbwz__dgpg, out_columns + ('',))
                else:
                    xgvb__wwje = SeriesType(comig__pqw.dtype, comig__pqw,
                        kbwz__dgpg, None)
        elif isinstance(pjz__tzbua, SeriesType):
            xgvb__wwje = SeriesType(pjz__tzbua.dtype, pjz__tzbua.data,
                kbwz__dgpg, pjz__tzbua.name_typ)
        else:
            xgvb__wwje = DataFrameType(pjz__tzbua.data, kbwz__dgpg,
                pjz__tzbua.columns)
        ihti__bckbw = gen_apply_pysig(len(f_args), kws.keys())
        woe__nwua = (func, *f_args) + tuple(kws.values())
        return signature(xgvb__wwje, *woe__nwua).replace(pysig=ihti__bckbw)

    def generic_resolve(self, grpby, attr):
        if self._is_existing_attr(attr):
            return
        if attr not in grpby.df_type.columns:
            raise_bodo_error(
                f'groupby: invalid attribute {attr} (column not found in dataframe or unsupported function)'
                )
        return DataFrameGroupByType(grpby.df_type, grpby.keys, (attr,),
            grpby.as_index, grpby.dropna, True, True)


def _get_groupby_apply_udf_out_type(func, grp, f_args, kws, typing_context,
    target_context):
    yebkw__uehxm = grp.df_type
    if grp.explicit_select:
        if len(grp.selection) == 1:
            ikuif__qcfq = grp.selection[0]
            comig__pqw = yebkw__uehxm.data[yebkw__uehxm.columns.index(
                ikuif__qcfq)]
            comig__pqw = to_str_arr_if_dict_array(comig__pqw)
            kqrm__rydc = SeriesType(comig__pqw.dtype, comig__pqw,
                yebkw__uehxm.index, types.literal(ikuif__qcfq))
        else:
            uaqe__mrwow = tuple(yebkw__uehxm.data[yebkw__uehxm.columns.
                index(ocpyi__hgulf)] for ocpyi__hgulf in grp.selection)
            uaqe__mrwow = tuple(to_str_arr_if_dict_array(jbmc__pkgfr) for
                jbmc__pkgfr in uaqe__mrwow)
            kqrm__rydc = DataFrameType(uaqe__mrwow, yebkw__uehxm.index,
                tuple(grp.selection))
    else:
        kqrm__rydc = yebkw__uehxm
    esa__ptjf = kqrm__rydc,
    esa__ptjf += tuple(f_args)
    try:
        pjz__tzbua = get_const_func_output_type(func, esa__ptjf, kws,
            typing_context, target_context)
    except Exception as yrhh__oxb:
        raise_bodo_error(get_udf_error_msg('GroupBy.apply()', yrhh__oxb),
            getattr(yrhh__oxb, 'loc', None))
    return pjz__tzbua


def resolve_obj_pipe(self, grp, args, kws, obj_name):
    kws = dict(kws)
    func = args[0] if len(args) > 0 else kws.pop('func', None)
    f_args = tuple(args[1:]) if len(args) > 0 else ()
    esa__ptjf = (grp,) + f_args
    try:
        pjz__tzbua = get_const_func_output_type(func, esa__ptjf, kws, self.
            context, numba.core.registry.cpu_target.target_context, False)
    except Exception as yrhh__oxb:
        raise_bodo_error(get_udf_error_msg(f'{obj_name}.pipe()', yrhh__oxb),
            getattr(yrhh__oxb, 'loc', None))
    ihti__bckbw = gen_apply_pysig(len(f_args), kws.keys())
    woe__nwua = (func, *f_args) + tuple(kws.values())
    return signature(pjz__tzbua, *woe__nwua).replace(pysig=ihti__bckbw)


def gen_apply_pysig(n_args, kws):
    squf__czyo = ', '.join(f'arg{gzhic__bfi}' for gzhic__bfi in range(n_args))
    squf__czyo = squf__czyo + ', ' if squf__czyo else ''
    tio__bhmd = ', '.join(f"{xmbs__ovqou} = ''" for xmbs__ovqou in kws)
    lajlp__xjojw = f'def apply_stub(func, {squf__czyo}{tio__bhmd}):\n'
    lajlp__xjojw += '    pass\n'
    exx__zbnwm = {}
    exec(lajlp__xjojw, {}, exx__zbnwm)
    mrwkj__suxh = exx__zbnwm['apply_stub']
    return numba.core.utils.pysignature(mrwkj__suxh)


def pivot_table_dummy(df, values, index, columns, aggfunc, _pivot_values):
    return 0


@infer_global(pivot_table_dummy)
class PivotTableTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        df, values, index, columns, aggfunc, _pivot_values = args
        if not (is_overload_constant_str(values) and
            is_overload_constant_str(index) and is_overload_constant_str(
            columns)):
            raise BodoError(
                "pivot_table() only support string constants for 'values', 'index' and 'columns' arguments"
                )
        values = values.literal_value
        index = index.literal_value
        columns = columns.literal_value
        data = df.data[df.columns.index(values)]
        data = to_str_arr_if_dict_array(data)
        wul__jekq = get_pivot_output_dtype(data, aggfunc.literal_value)
        sekpq__lepf = dtype_to_array_type(wul__jekq)
        if is_overload_none(_pivot_values):
            raise_bodo_error(
                'Dataframe.pivot_table() requires explicit annotation to determine output columns. For more information, see: https://docs.bodo.ai/latest/source/programming_with_bodo/pandas.html'
                )
        mdd__rfuv = _pivot_values.meta
        nvol__zvks = len(mdd__rfuv)
        dctr__vgk = df.columns.index(index)
        ctjp__dtbsz = df.data[dctr__vgk]
        ctjp__dtbsz = to_str_arr_if_dict_array(ctjp__dtbsz)
        qoki__bpaiu = bodo.hiframes.pd_index_ext.array_type_to_index(
            ctjp__dtbsz, types.StringLiteral(index))
        uom__ibtdq = DataFrameType((sekpq__lepf,) * nvol__zvks, qoki__bpaiu,
            tuple(mdd__rfuv))
        return signature(uom__ibtdq, *args)


PivotTableTyper._no_unliteral = True


@lower_builtin(pivot_table_dummy, types.VarArg(types.Any))
def lower_pivot_table_dummy(context, builder, sig, args):
    return context.get_constant_null(sig.return_type)


def crosstab_dummy(index, columns, _pivot_values):
    return 0


@infer_global(crosstab_dummy)
class CrossTabTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        index, columns, _pivot_values = args
        sekpq__lepf = types.Array(types.int64, 1, 'C')
        mdd__rfuv = _pivot_values.meta
        nvol__zvks = len(mdd__rfuv)
        qoki__bpaiu = bodo.hiframes.pd_index_ext.array_type_to_index(
            to_str_arr_if_dict_array(index.data), types.StringLiteral('index'))
        uom__ibtdq = DataFrameType((sekpq__lepf,) * nvol__zvks, qoki__bpaiu,
            tuple(mdd__rfuv))
        return signature(uom__ibtdq, *args)


CrossTabTyper._no_unliteral = True


@lower_builtin(crosstab_dummy, types.VarArg(types.Any))
def lower_crosstab_dummy(context, builder, sig, args):
    return context.get_constant_null(sig.return_type)


def get_group_indices(keys, dropna, _is_parallel):
    return np.arange(len(keys))


@overload(get_group_indices)
def get_group_indices_overload(keys, dropna, _is_parallel):
    lajlp__xjojw = 'def impl(keys, dropna, _is_parallel):\n'
    lajlp__xjojw += (
        "    ev = bodo.utils.tracing.Event('get_group_indices', _is_parallel)\n"
        )
    lajlp__xjojw += '    info_list = [{}]\n'.format(', '.join(
        f'array_to_info(keys[{gzhic__bfi}])' for gzhic__bfi in range(len(
        keys.types))))
    lajlp__xjojw += '    table = arr_info_list_to_table(info_list)\n'
    lajlp__xjojw += '    group_labels = np.empty(len(keys[0]), np.int64)\n'
    lajlp__xjojw += '    sort_idx = np.empty(len(keys[0]), np.int64)\n'
    lajlp__xjojw += """    ngroups = get_groupby_labels(table, group_labels.ctypes, sort_idx.ctypes, dropna, _is_parallel)
"""
    lajlp__xjojw += '    delete_table_decref_arrays(table)\n'
    lajlp__xjojw += '    ev.finalize()\n'
    lajlp__xjojw += '    return sort_idx, group_labels, ngroups\n'
    exx__zbnwm = {}
    exec(lajlp__xjojw, {'bodo': bodo, 'np': np, 'get_groupby_labels':
        get_groupby_labels, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table,
        'delete_table_decref_arrays': delete_table_decref_arrays}, exx__zbnwm)
    xisrw__ple = exx__zbnwm['impl']
    return xisrw__ple


@numba.njit(no_cpython_wrapper=True)
def generate_slices(labels, ngroups):
    klb__vaie = len(labels)
    wnid__hyjf = np.zeros(ngroups, dtype=np.int64)
    aqsi__qdg = np.zeros(ngroups, dtype=np.int64)
    dzrya__wzymd = 0
    xar__wht = 0
    for gzhic__bfi in range(klb__vaie):
        bdrhe__ojtd = labels[gzhic__bfi]
        if bdrhe__ojtd < 0:
            dzrya__wzymd += 1
        else:
            xar__wht += 1
            if gzhic__bfi == klb__vaie - 1 or bdrhe__ojtd != labels[
                gzhic__bfi + 1]:
                wnid__hyjf[bdrhe__ojtd] = dzrya__wzymd
                aqsi__qdg[bdrhe__ojtd] = dzrya__wzymd + xar__wht
                dzrya__wzymd += xar__wht
                xar__wht = 0
    return wnid__hyjf, aqsi__qdg


def shuffle_dataframe(df, keys, _is_parallel):
    return df, keys, _is_parallel


@overload(shuffle_dataframe, prefer_literal=True)
def overload_shuffle_dataframe(df, keys, _is_parallel):
    xisrw__ple, edll__fleti = gen_shuffle_dataframe(df, keys, _is_parallel)
    return xisrw__ple


def gen_shuffle_dataframe(df, keys, _is_parallel):
    fcyjq__rvoow = len(df.columns)
    vyib__fah = len(keys.types)
    assert is_overload_constant_bool(_is_parallel
        ), 'shuffle_dataframe: _is_parallel is not a constant'
    lajlp__xjojw = 'def impl(df, keys, _is_parallel):\n'
    if is_overload_false(_is_parallel):
        lajlp__xjojw += '  return df, keys, get_null_shuffle_info()\n'
        exx__zbnwm = {}
        exec(lajlp__xjojw, {'get_null_shuffle_info': get_null_shuffle_info},
            exx__zbnwm)
        xisrw__ple = exx__zbnwm['impl']
        return xisrw__ple
    for gzhic__bfi in range(fcyjq__rvoow):
        lajlp__xjojw += f"""  in_arr{gzhic__bfi} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {gzhic__bfi})
"""
    lajlp__xjojw += f"""  in_index_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))
"""
    lajlp__xjojw += '  info_list = [{}, {}, {}]\n'.format(', '.join(
        f'array_to_info(keys[{gzhic__bfi}])' for gzhic__bfi in range(
        vyib__fah)), ', '.join(f'array_to_info(in_arr{gzhic__bfi})' for
        gzhic__bfi in range(fcyjq__rvoow)), 'array_to_info(in_index_arr)')
    lajlp__xjojw += '  table = arr_info_list_to_table(info_list)\n'
    lajlp__xjojw += (
        f'  out_table = shuffle_table(table, {vyib__fah}, _is_parallel, 1)\n')
    for gzhic__bfi in range(vyib__fah):
        lajlp__xjojw += f"""  out_key{gzhic__bfi} = info_to_array(info_from_table(out_table, {gzhic__bfi}), keys{gzhic__bfi}_typ)
"""
    for gzhic__bfi in range(fcyjq__rvoow):
        lajlp__xjojw += f"""  out_arr{gzhic__bfi} = info_to_array(info_from_table(out_table, {gzhic__bfi + vyib__fah}), in_arr{gzhic__bfi}_typ)
"""
    lajlp__xjojw += f"""  out_arr_index = info_to_array(info_from_table(out_table, {vyib__fah + fcyjq__rvoow}), ind_arr_typ)
"""
    lajlp__xjojw += '  shuffle_info = get_shuffle_info(out_table)\n'
    lajlp__xjojw += '  delete_table(out_table)\n'
    lajlp__xjojw += '  delete_table(table)\n'
    out_data = ', '.join(f'out_arr{gzhic__bfi}' for gzhic__bfi in range(
        fcyjq__rvoow))
    lajlp__xjojw += (
        '  out_index = bodo.utils.conversion.index_from_array(out_arr_index)\n'
        )
    lajlp__xjojw += f"""  out_df = bodo.hiframes.pd_dataframe_ext.init_dataframe(({out_data},), out_index, {gen_const_tup(df.columns)})
"""
    lajlp__xjojw += '  return out_df, ({},), shuffle_info\n'.format(', '.
        join(f'out_key{gzhic__bfi}' for gzhic__bfi in range(vyib__fah)))
    tcaw__mxwgb = {'bodo': bodo, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'shuffle_table':
        shuffle_table, 'info_from_table': info_from_table, 'info_to_array':
        info_to_array, 'delete_table': delete_table, 'get_shuffle_info':
        get_shuffle_info, 'ind_arr_typ': types.Array(types.int64, 1, 'C') if
        isinstance(df.index, RangeIndexType) else df.index.data}
    tcaw__mxwgb.update({f'keys{gzhic__bfi}_typ': keys.types[gzhic__bfi] for
        gzhic__bfi in range(vyib__fah)})
    tcaw__mxwgb.update({f'in_arr{gzhic__bfi}_typ': df.data[gzhic__bfi] for
        gzhic__bfi in range(fcyjq__rvoow)})
    exx__zbnwm = {}
    exec(lajlp__xjojw, tcaw__mxwgb, exx__zbnwm)
    xisrw__ple = exx__zbnwm['impl']
    return xisrw__ple, tcaw__mxwgb


def reverse_shuffle(data, shuffle_info):
    return data


@overload(reverse_shuffle)
def overload_reverse_shuffle(data, shuffle_info):
    if isinstance(data, bodo.hiframes.pd_multi_index_ext.MultiIndexType):
        cod__txlbw = len(data.array_types)
        lajlp__xjojw = 'def impl(data, shuffle_info):\n'
        lajlp__xjojw += '  info_list = [{}]\n'.format(', '.join(
            f'array_to_info(data._data[{gzhic__bfi}])' for gzhic__bfi in
            range(cod__txlbw)))
        lajlp__xjojw += '  table = arr_info_list_to_table(info_list)\n'
        lajlp__xjojw += (
            '  out_table = reverse_shuffle_table(table, shuffle_info)\n')
        for gzhic__bfi in range(cod__txlbw):
            lajlp__xjojw += f"""  out_arr{gzhic__bfi} = info_to_array(info_from_table(out_table, {gzhic__bfi}), data._data[{gzhic__bfi}])
"""
        lajlp__xjojw += '  delete_table(out_table)\n'
        lajlp__xjojw += '  delete_table(table)\n'
        lajlp__xjojw += (
            '  return init_multi_index(({},), data._names, data._name)\n'.
            format(', '.join(f'out_arr{gzhic__bfi}' for gzhic__bfi in range
            (cod__txlbw))))
        exx__zbnwm = {}
        exec(lajlp__xjojw, {'bodo': bodo, 'array_to_info': array_to_info,
            'arr_info_list_to_table': arr_info_list_to_table,
            'reverse_shuffle_table': reverse_shuffle_table,
            'info_from_table': info_from_table, 'info_to_array':
            info_to_array, 'delete_table': delete_table, 'init_multi_index':
            bodo.hiframes.pd_multi_index_ext.init_multi_index}, exx__zbnwm)
        xisrw__ple = exx__zbnwm['impl']
        return xisrw__ple
    if bodo.hiframes.pd_index_ext.is_index_type(data):

        def impl_index(data, shuffle_info):
            jgu__qxua = bodo.utils.conversion.index_to_array(data)
            rebar__nhs = reverse_shuffle(jgu__qxua, shuffle_info)
            return bodo.utils.conversion.index_from_array(rebar__nhs)
        return impl_index

    def impl_arr(data, shuffle_info):
        zbd__upkfp = [array_to_info(data)]
        otb__rdo = arr_info_list_to_table(zbd__upkfp)
        rmkck__astvi = reverse_shuffle_table(otb__rdo, shuffle_info)
        rebar__nhs = info_to_array(info_from_table(rmkck__astvi, 0), data)
        delete_table(rmkck__astvi)
        delete_table(otb__rdo)
        return rebar__nhs
    return impl_arr


@overload_method(DataFrameGroupByType, 'value_counts', inline='always',
    no_unliteral=True)
def groupby_value_counts(grp, normalize=False, sort=True, ascending=False,
    bins=None, dropna=True):
    uboto__iviu = dict(normalize=normalize, sort=sort, bins=bins, dropna=dropna
        )
    fkf__asru = dict(normalize=False, sort=True, bins=None, dropna=True)
    check_unsupported_args('Groupby.value_counts', uboto__iviu, fkf__asru,
        package_name='pandas', module_name='GroupBy')
    if len(grp.selection) > 1 or not grp.as_index:
        raise BodoError(
            "'DataFrameGroupBy' object has no attribute 'value_counts'")
    if not is_overload_constant_bool(ascending):
        raise BodoError(
            'Groupby.value_counts() ascending must be a constant boolean')
    vyuc__guoym = get_overload_const_bool(ascending)
    muimy__hpyd = grp.selection[0]
    lajlp__xjojw = f"""def impl(grp, normalize=False, sort=True, ascending=False, bins=None, dropna=True):
"""
    uvcz__cwpnf = (
        f"lambda S: S.value_counts(ascending={vyuc__guoym}, _index_name='{muimy__hpyd}')"
        )
    lajlp__xjojw += f'    return grp.apply({uvcz__cwpnf})\n'
    exx__zbnwm = {}
    exec(lajlp__xjojw, {'bodo': bodo}, exx__zbnwm)
    xisrw__ple = exx__zbnwm['impl']
    return xisrw__ple


groupby_unsupported_attr = {'groups', 'indices'}
groupby_unsupported = {'__iter__', 'get_group', 'all', 'any', 'bfill',
    'backfill', 'cumcount', 'cummax', 'cummin', 'cumprod', 'ffill',
    'ngroup', 'nth', 'ohlc', 'pad', 'rank', 'pct_change', 'sem', 'tail',
    'corr', 'cov', 'describe', 'diff', 'fillna', 'filter', 'hist', 'mad',
    'plot', 'quantile', 'resample', 'sample', 'skew', 'take', 'tshift'}
series_only_unsupported_attrs = {'is_monotonic_increasing',
    'is_monotonic_decreasing'}
series_only_unsupported = {'nlargest', 'nsmallest', 'unique'}
dataframe_only_unsupported = {'corrwith', 'boxplot'}


def _install_groupby_unsupported():
    for pawa__wkdj in groupby_unsupported_attr:
        overload_attribute(DataFrameGroupByType, pawa__wkdj, no_unliteral=True
            )(create_unsupported_overload(f'DataFrameGroupBy.{pawa__wkdj}'))
    for pawa__wkdj in groupby_unsupported:
        overload_method(DataFrameGroupByType, pawa__wkdj, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{pawa__wkdj}'))
    for pawa__wkdj in series_only_unsupported_attrs:
        overload_attribute(DataFrameGroupByType, pawa__wkdj, no_unliteral=True
            )(create_unsupported_overload(f'SeriesGroupBy.{pawa__wkdj}'))
    for pawa__wkdj in series_only_unsupported:
        overload_method(DataFrameGroupByType, pawa__wkdj, no_unliteral=True)(
            create_unsupported_overload(f'SeriesGroupBy.{pawa__wkdj}'))
    for pawa__wkdj in dataframe_only_unsupported:
        overload_method(DataFrameGroupByType, pawa__wkdj, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{pawa__wkdj}'))


_install_groupby_unsupported()
