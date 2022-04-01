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
        mub__grn = [('obj', fe_type.df_type)]
        super(GroupbyModel, self).__init__(dmm, fe_type, mub__grn)


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
        lrli__tiu = args[0]
        istxq__ivepx = signature.return_type
        qyog__tec = cgutils.create_struct_proxy(istxq__ivepx)(context, builder)
        qyog__tec.obj = lrli__tiu
        context.nrt.incref(builder, signature.args[0], lrli__tiu)
        return qyog__tec._getvalue()
    if is_overload_constant_list(by_type):
        keys = tuple(get_overload_const_list(by_type))
    elif is_literal_type(by_type):
        keys = get_literal_value(by_type),
    else:
        assert False, 'Reached unreachable code in init_groupby; there is an validate_groupby_spec'
    selection = list(obj_type.columns)
    for zmm__muyct in keys:
        selection.remove(zmm__muyct)
    if is_overload_constant_bool(as_index_type):
        as_index = is_overload_true(as_index_type)
    else:
        as_index = True
    if is_overload_constant_bool(dropna_type):
        dropna = is_overload_true(dropna_type)
    else:
        dropna = True
    istxq__ivepx = DataFrameGroupByType(obj_type, keys, tuple(selection),
        as_index, dropna, False)
    return istxq__ivepx(obj_type, by_type, as_index_type, dropna_type), codegen


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
        grpby, zbvyq__dkn = args
        if isinstance(grpby, DataFrameGroupByType):
            series_select = False
            if isinstance(zbvyq__dkn, (tuple, list)):
                if len(set(zbvyq__dkn).difference(set(grpby.df_type.columns))
                    ) > 0:
                    raise_bodo_error(
                        'groupby: selected column {} not found in dataframe'
                        .format(set(zbvyq__dkn).difference(set(grpby.
                        df_type.columns))))
                selection = zbvyq__dkn
            else:
                if zbvyq__dkn not in grpby.df_type.columns:
                    raise_bodo_error(
                        'groupby: selected column {} not found in dataframe'
                        .format(zbvyq__dkn))
                selection = zbvyq__dkn,
                series_select = True
            yxhw__szpvx = DataFrameGroupByType(grpby.df_type, grpby.keys,
                selection, grpby.as_index, grpby.dropna, True, series_select)
            return signature(yxhw__szpvx, *args)


@infer_global(operator.getitem)
class GetItemDataFrameGroupBy(AbstractTemplate):

    def generic(self, args, kws):
        grpby, zbvyq__dkn = args
        if isinstance(grpby, DataFrameGroupByType) and is_literal_type(
            zbvyq__dkn):
            yxhw__szpvx = StaticGetItemDataFrameGroupBy.generic(self, (
                grpby, get_literal_value(zbvyq__dkn)), {}).return_type
            return signature(yxhw__szpvx, *args)


GetItemDataFrameGroupBy.prefer_literal = True


@lower_builtin('static_getitem', DataFrameGroupByType, types.Any)
@lower_builtin(operator.getitem, DataFrameGroupByType, types.Any)
def static_getitem_df_groupby(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


def get_groupby_output_dtype(arr_type, func_name, index_type=None):
    arr_type = to_str_arr_if_dict_array(arr_type)
    lbb__zielk = arr_type == ArrayItemArrayType(string_array_type)
    xdrn__bdndf = arr_type.dtype
    if isinstance(xdrn__bdndf, bodo.hiframes.datetime_timedelta_ext.
        DatetimeTimeDeltaType):
        raise BodoError(
            f"""column type of {xdrn__bdndf} is not supported in groupby built-in function {func_name}.
{dt_err}"""
            )
    if func_name == 'median' and not isinstance(xdrn__bdndf, (
        Decimal128Type, types.Float, types.Integer)):
        return (None,
            'For median, only column of integer, float or Decimal type are allowed'
            )
    if func_name in ('first', 'last', 'sum', 'prod', 'min', 'max', 'count',
        'nunique', 'head') and isinstance(arr_type, (TupleArrayType,
        ArrayItemArrayType)):
        return (None,
            f'column type of list/tuple of {xdrn__bdndf} is not supported in groupby built-in function {func_name}'
            )
    if func_name in {'median', 'mean', 'var', 'std'} and isinstance(xdrn__bdndf
        , (Decimal128Type, types.Integer, types.Float)):
        return dtype_to_array_type(types.float64), 'ok'
    if not isinstance(xdrn__bdndf, (types.Integer, types.Float, types.Boolean)
        ):
        if lbb__zielk or xdrn__bdndf == types.unicode_type:
            if func_name not in {'count', 'nunique', 'min', 'max', 'sum',
                'first', 'last', 'head'}:
                return (None,
                    f'column type of strings or list of strings is not supported in groupby built-in function {func_name}'
                    )
        else:
            if isinstance(xdrn__bdndf, bodo.PDCategoricalDtype):
                if func_name in ('min', 'max') and not xdrn__bdndf.ordered:
                    return (None,
                        f'categorical column must be ordered in groupby built-in function {func_name}'
                        )
            if func_name not in {'count', 'nunique', 'min', 'max', 'first',
                'last', 'head'}:
                return (None,
                    f'column type of {xdrn__bdndf} is not supported in groupby built-in function {func_name}'
                    )
    if isinstance(xdrn__bdndf, types.Boolean) and func_name in {'cumsum',
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
    xdrn__bdndf = arr_type.dtype
    if func_name in {'count'}:
        return IntDtype(types.int64)
    if func_name in {'sum', 'prod', 'min', 'max'}:
        if func_name in {'sum', 'prod'} and not isinstance(xdrn__bdndf, (
            types.Integer, types.Float)):
            raise BodoError(
                'pivot_table(): sum and prod operations require integer or float input'
                )
        if isinstance(xdrn__bdndf, types.Integer):
            return IntDtype(xdrn__bdndf)
        return xdrn__bdndf
    if func_name in {'mean', 'var', 'std'}:
        return types.float64
    raise BodoError('invalid pivot operation')


def check_args_kwargs(func_name, len_args, args, kws):
    if len(kws) > 0:
        kmqnu__svfi = list(kws.keys())[0]
        raise BodoError(
            f"Groupby.{func_name}() got an unexpected keyword argument '{kmqnu__svfi}'."
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
    for zmm__muyct in grp.keys:
        if multi_level_names:
            plzo__nppgf = zmm__muyct, ''
        else:
            plzo__nppgf = zmm__muyct
        zmden__fyvr = grp.df_type.columns.index(zmm__muyct)
        data = to_str_arr_if_dict_array(grp.df_type.data[zmden__fyvr])
        out_columns.append(plzo__nppgf)
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
        cmeg__ker = tuple(grp.df_type.columns.index(grp.keys[fifdq__zdvu]) for
            fifdq__zdvu in range(len(grp.keys)))
        uuglv__gcv = tuple(grp.df_type.data[zmden__fyvr] for zmden__fyvr in
            cmeg__ker)
        uuglv__gcv = tuple(to_str_arr_if_dict_array(ihjwq__ncxze) for
            ihjwq__ncxze in uuglv__gcv)
        index = MultiIndexType(uuglv__gcv, tuple(types.StringLiteral(
            zmm__muyct) for zmm__muyct in grp.keys))
    else:
        zmden__fyvr = grp.df_type.columns.index(grp.keys[0])
        geks__moa = to_str_arr_if_dict_array(grp.df_type.data[zmden__fyvr])
        index = bodo.hiframes.pd_index_ext.array_type_to_index(geks__moa,
            types.StringLiteral(grp.keys[0]))
    gtxc__awmk = {}
    xqt__jyprd = []
    if func_name in ('size', 'count'):
        kws = dict(kws) if kws else {}
        check_args_kwargs(func_name, 0, args, kws)
    if func_name == 'size':
        out_data.append(types.Array(types.int64, 1, 'C'))
        out_columns.append('size')
        gtxc__awmk[None, 'size'] = 'size'
    else:
        columns = (grp.selection if func_name != 'head' or grp.
            explicit_select else grp.df_type.columns)
        for wafba__swoaf in columns:
            zmden__fyvr = grp.df_type.columns.index(wafba__swoaf)
            data = grp.df_type.data[zmden__fyvr]
            data = to_str_arr_if_dict_array(data)
            byfju__hgd = ColumnType.NonNumericalColumn.value
            if isinstance(data, (types.Array, IntegerArrayType)
                ) and isinstance(data.dtype, (types.Integer, types.Float)):
                byfju__hgd = ColumnType.NumericalColumn.value
            if func_name == 'agg':
                try:
                    ydqg__ijbbj = SeriesType(data.dtype, data, None,
                        string_type)
                    jdtjw__eqbo = get_const_func_output_type(func, (
                        ydqg__ijbbj,), {}, typing_context, target_context)
                    if jdtjw__eqbo != ArrayItemArrayType(string_array_type):
                        jdtjw__eqbo = dtype_to_array_type(jdtjw__eqbo)
                    err_msg = 'ok'
                except:
                    raise_bodo_error(
                        'Groupy.agg()/Groupy.aggregate(): column {col} of type {type} is unsupported/not a valid input type for user defined function'
                        .format(col=wafba__swoaf, type=data.dtype))
            else:
                if func_name in ('first', 'last', 'min', 'max'):
                    kws = dict(kws) if kws else {}
                    wlbs__zeaxf = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', False)
                    kuhpc__mth = args[1] if len(args) > 1 else kws.pop(
                        'min_count', -1)
                    mlaev__yilzr = dict(numeric_only=wlbs__zeaxf, min_count
                        =kuhpc__mth)
                    ibu__apga = dict(numeric_only=False, min_count=-1)
                    check_unsupported_args(f'Groupby.{func_name}',
                        mlaev__yilzr, ibu__apga, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('sum', 'prod'):
                    kws = dict(kws) if kws else {}
                    wlbs__zeaxf = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', True)
                    kuhpc__mth = args[1] if len(args) > 1 else kws.pop(
                        'min_count', 0)
                    mlaev__yilzr = dict(numeric_only=wlbs__zeaxf, min_count
                        =kuhpc__mth)
                    ibu__apga = dict(numeric_only=True, min_count=0)
                    check_unsupported_args(f'Groupby.{func_name}',
                        mlaev__yilzr, ibu__apga, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('mean', 'median'):
                    kws = dict(kws) if kws else {}
                    wlbs__zeaxf = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', True)
                    mlaev__yilzr = dict(numeric_only=wlbs__zeaxf)
                    ibu__apga = dict(numeric_only=True)
                    check_unsupported_args(f'Groupby.{func_name}',
                        mlaev__yilzr, ibu__apga, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('idxmin', 'idxmax'):
                    kws = dict(kws) if kws else {}
                    qdur__rdvib = args[0] if len(args) > 0 else kws.pop('axis',
                        0)
                    yozk__zxooo = args[1] if len(args) > 1 else kws.pop(
                        'skipna', True)
                    mlaev__yilzr = dict(axis=qdur__rdvib, skipna=yozk__zxooo)
                    ibu__apga = dict(axis=0, skipna=True)
                    check_unsupported_args(f'Groupby.{func_name}',
                        mlaev__yilzr, ibu__apga, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('var', 'std'):
                    kws = dict(kws) if kws else {}
                    eauh__jbl = args[0] if len(args) > 0 else kws.pop('ddof', 1
                        )
                    mlaev__yilzr = dict(ddof=eauh__jbl)
                    ibu__apga = dict(ddof=1)
                    check_unsupported_args(f'Groupby.{func_name}',
                        mlaev__yilzr, ibu__apga, package_name='pandas',
                        module_name='GroupBy')
                elif func_name == 'nunique':
                    kws = dict(kws) if kws else {}
                    dropna = args[0] if len(args) > 0 else kws.pop('dropna', 1)
                    check_args_kwargs(func_name, 1, args, kws)
                elif func_name == 'head':
                    if len(args) == 0:
                        kws.pop('n', None)
                jdtjw__eqbo, err_msg = get_groupby_output_dtype(data,
                    func_name, grp.df_type.index)
            if err_msg == 'ok':
                ocw__dga = to_str_arr_if_dict_array(jdtjw__eqbo)
                out_data.append(ocw__dga)
                out_columns.append(wafba__swoaf)
                if func_name == 'agg':
                    jbuc__ibpxx = bodo.ir.aggregate._get_udf_name(bodo.ir.
                        aggregate._get_const_agg_func(func, None))
                    gtxc__awmk[wafba__swoaf, jbuc__ibpxx] = wafba__swoaf
                else:
                    gtxc__awmk[wafba__swoaf, func_name] = wafba__swoaf
                out_column_type.append(byfju__hgd)
            else:
                xqt__jyprd.append(err_msg)
    if func_name == 'sum':
        yxyi__dywy = any([(ywwa__peksj == ColumnType.NumericalColumn.value) for
            ywwa__peksj in out_column_type])
        if yxyi__dywy:
            out_data = [ywwa__peksj for ywwa__peksj, bfz__dfnc in zip(
                out_data, out_column_type) if bfz__dfnc != ColumnType.
                NonNumericalColumn.value]
            out_columns = [ywwa__peksj for ywwa__peksj, bfz__dfnc in zip(
                out_columns, out_column_type) if bfz__dfnc != ColumnType.
                NonNumericalColumn.value]
            gtxc__awmk = {}
            for wafba__swoaf in out_columns:
                if grp.as_index is False and wafba__swoaf in grp.keys:
                    continue
                gtxc__awmk[wafba__swoaf, func_name] = wafba__swoaf
    oxvb__lws = len(xqt__jyprd)
    if len(out_data) == 0:
        if oxvb__lws == 0:
            raise BodoError('No columns in output.')
        else:
            raise BodoError(
                'No columns in output. {} column{} dropped for following reasons: {}'
                .format(oxvb__lws, ' was' if oxvb__lws == 1 else 's were',
                ','.join(xqt__jyprd)))
    qctpf__tbyfr = DataFrameType(tuple(out_data), index, tuple(out_columns))
    if (len(grp.selection) == 1 and grp.series_select and grp.as_index or 
        func_name == 'size' and grp.as_index):
        if isinstance(out_data[0], IntegerArrayType):
            zeg__asj = IntDtype(out_data[0].dtype)
        else:
            zeg__asj = out_data[0].dtype
        leol__dxfri = (types.none if func_name == 'size' else types.
            StringLiteral(grp.selection[0]))
        qctpf__tbyfr = SeriesType(zeg__asj, index=index, name_typ=leol__dxfri)
    return signature(qctpf__tbyfr, *args), gtxc__awmk


def get_agg_funcname_and_outtyp(grp, col, f_val, typing_context, target_context
    ):
    owix__yov = True
    if isinstance(f_val, str):
        owix__yov = False
        knri__qat = f_val
    elif is_overload_constant_str(f_val):
        owix__yov = False
        knri__qat = get_overload_const_str(f_val)
    elif bodo.utils.typing.is_builtin_function(f_val):
        owix__yov = False
        knri__qat = bodo.utils.typing.get_builtin_function_name(f_val)
    if not owix__yov:
        if knri__qat not in bodo.ir.aggregate.supported_agg_funcs[:-1]:
            raise BodoError(f'unsupported aggregate function {knri__qat}')
        yxhw__szpvx = DataFrameGroupByType(grp.df_type, grp.keys, (col,),
            grp.as_index, grp.dropna, True, True)
        out_tp = get_agg_typ(yxhw__szpvx, (), knri__qat, typing_context,
            target_context)[0].return_type
    else:
        if is_expr(f_val, 'make_function'):
            xpeb__jbkxg = types.functions.MakeFunctionLiteral(f_val)
        else:
            xpeb__jbkxg = f_val
        validate_udf('agg', xpeb__jbkxg)
        func = get_overload_const_func(xpeb__jbkxg, None)
        ieg__lrpi = func.code if hasattr(func, 'code') else func.__code__
        knri__qat = ieg__lrpi.co_name
        yxhw__szpvx = DataFrameGroupByType(grp.df_type, grp.keys, (col,),
            grp.as_index, grp.dropna, True, True)
        out_tp = get_agg_typ(yxhw__szpvx, (), 'agg', typing_context,
            target_context, xpeb__jbkxg)[0].return_type
    return knri__qat, out_tp


def resolve_agg(grp, args, kws, typing_context, target_context):
    func = get_call_expr_arg('agg', args, dict(kws), 0, 'func', default=
        types.none)
    vrdk__tnuyd = kws and all(isinstance(jwd__knw, types.Tuple) and len(
        jwd__knw) == 2 for jwd__knw in kws.values())
    if is_overload_none(func) and not vrdk__tnuyd:
        raise_bodo_error("Groupby.agg()/aggregate(): Must provide 'func'")
    if len(args) > 1 or kws and not vrdk__tnuyd:
        raise_bodo_error(
            'Groupby.agg()/aggregate(): passing extra arguments to functions not supported yet.'
            )
    aeu__nabgn = False

    def _append_out_type(grp, out_data, out_tp):
        if grp.as_index is False:
            out_data.append(out_tp.data[len(grp.keys)])
        else:
            out_data.append(out_tp.data)
    if vrdk__tnuyd or is_overload_constant_dict(func):
        if vrdk__tnuyd:
            tnvse__jdpue = [get_literal_value(rko__nbohz) for rko__nbohz,
                ham__luk in kws.values()]
            cxbqi__ibivc = [get_literal_value(abug__eptf) for ham__luk,
                abug__eptf in kws.values()]
        else:
            hrqx__rhth = get_overload_constant_dict(func)
            tnvse__jdpue = tuple(hrqx__rhth.keys())
            cxbqi__ibivc = tuple(hrqx__rhth.values())
        if 'head' in cxbqi__ibivc:
            raise BodoError(
                'Groupby.agg()/aggregate(): head cannot be mixed with other groupby operations.'
                )
        if any(wafba__swoaf not in grp.selection and wafba__swoaf not in
            grp.keys for wafba__swoaf in tnvse__jdpue):
            raise_bodo_error(
                f'Selected column names {tnvse__jdpue} not all available in dataframe column names {grp.selection}'
                )
        multi_level_names = any(isinstance(f_val, (tuple, list)) for f_val in
            cxbqi__ibivc)
        if vrdk__tnuyd and multi_level_names:
            raise_bodo_error(
                'Groupby.agg()/aggregate(): cannot pass multiple functions in a single pd.NamedAgg()'
                )
        gtxc__awmk = {}
        out_columns = []
        out_data = []
        out_column_type = []
        tidvk__kvrl = []
        if not grp.as_index:
            get_keys_not_as_index(grp, out_columns, out_data,
                out_column_type, multi_level_names=multi_level_names)
        for xvsy__kokvu, f_val in zip(tnvse__jdpue, cxbqi__ibivc):
            if isinstance(f_val, (tuple, list)):
                zfho__shfa = 0
                for xpeb__jbkxg in f_val:
                    knri__qat, out_tp = get_agg_funcname_and_outtyp(grp,
                        xvsy__kokvu, xpeb__jbkxg, typing_context,
                        target_context)
                    aeu__nabgn = knri__qat in list_cumulative
                    if knri__qat == '<lambda>' and len(f_val) > 1:
                        knri__qat = '<lambda_' + str(zfho__shfa) + '>'
                        zfho__shfa += 1
                    out_columns.append((xvsy__kokvu, knri__qat))
                    gtxc__awmk[xvsy__kokvu, knri__qat] = xvsy__kokvu, knri__qat
                    _append_out_type(grp, out_data, out_tp)
            else:
                knri__qat, out_tp = get_agg_funcname_and_outtyp(grp,
                    xvsy__kokvu, f_val, typing_context, target_context)
                aeu__nabgn = knri__qat in list_cumulative
                if multi_level_names:
                    out_columns.append((xvsy__kokvu, knri__qat))
                    gtxc__awmk[xvsy__kokvu, knri__qat] = xvsy__kokvu, knri__qat
                elif not vrdk__tnuyd:
                    out_columns.append(xvsy__kokvu)
                    gtxc__awmk[xvsy__kokvu, knri__qat] = xvsy__kokvu
                elif vrdk__tnuyd:
                    tidvk__kvrl.append(knri__qat)
                _append_out_type(grp, out_data, out_tp)
        if vrdk__tnuyd:
            for fifdq__zdvu, xhdsl__dodg in enumerate(kws.keys()):
                out_columns.append(xhdsl__dodg)
                gtxc__awmk[tnvse__jdpue[fifdq__zdvu], tidvk__kvrl[fifdq__zdvu]
                    ] = xhdsl__dodg
        if aeu__nabgn:
            index = grp.df_type.index
        else:
            index = out_tp.index
        qctpf__tbyfr = DataFrameType(tuple(out_data), index, tuple(out_columns)
            )
        return signature(qctpf__tbyfr, *args), gtxc__awmk
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
        zfho__shfa = 0
        if not grp.as_index:
            get_keys_not_as_index(grp, out_columns, out_data, out_column_type)
        gtxc__awmk = {}
        vaj__pst = grp.selection[0]
        for f_val in func.types:
            knri__qat, out_tp = get_agg_funcname_and_outtyp(grp, vaj__pst,
                f_val, typing_context, target_context)
            aeu__nabgn = knri__qat in list_cumulative
            if knri__qat == '<lambda>':
                knri__qat = '<lambda_' + str(zfho__shfa) + '>'
                zfho__shfa += 1
            out_columns.append(knri__qat)
            gtxc__awmk[vaj__pst, knri__qat] = knri__qat
            _append_out_type(grp, out_data, out_tp)
        if aeu__nabgn:
            index = grp.df_type.index
        else:
            index = out_tp.index
        qctpf__tbyfr = DataFrameType(tuple(out_data), index, tuple(out_columns)
            )
        return signature(qctpf__tbyfr, *args), gtxc__awmk
    knri__qat = ''
    if types.unliteral(func) == types.unicode_type:
        knri__qat = get_overload_const_str(func)
    if bodo.utils.typing.is_builtin_function(func):
        knri__qat = bodo.utils.typing.get_builtin_function_name(func)
    if knri__qat:
        args = args[1:]
        kws.pop('func', None)
        return get_agg_typ(grp, args, knri__qat, typing_context, kws)
    validate_udf('agg', func)
    return get_agg_typ(grp, args, 'agg', typing_context, target_context, func)


def resolve_transformative(grp, args, kws, msg, name_operation):
    index = grp.df_type.index
    out_columns = []
    out_data = []
    if name_operation in list_cumulative:
        kws = dict(kws) if kws else {}
        qdur__rdvib = args[0] if len(args) > 0 else kws.pop('axis', 0)
        wlbs__zeaxf = args[1] if len(args) > 1 else kws.pop('numeric_only',
            False)
        yozk__zxooo = args[2] if len(args) > 2 else kws.pop('skipna', 1)
        mlaev__yilzr = dict(axis=qdur__rdvib, numeric_only=wlbs__zeaxf)
        ibu__apga = dict(axis=0, numeric_only=False)
        check_unsupported_args(f'Groupby.{name_operation}', mlaev__yilzr,
            ibu__apga, package_name='pandas', module_name='GroupBy')
        check_args_kwargs(name_operation, 3, args, kws)
    elif name_operation == 'shift':
        qpkfs__lthw = args[0] if len(args) > 0 else kws.pop('periods', 1)
        vtz__rtzuq = args[1] if len(args) > 1 else kws.pop('freq', None)
        qdur__rdvib = args[2] if len(args) > 2 else kws.pop('axis', 0)
        skyhw__ielho = args[3] if len(args) > 3 else kws.pop('fill_value', None
            )
        mlaev__yilzr = dict(freq=vtz__rtzuq, axis=qdur__rdvib, fill_value=
            skyhw__ielho)
        ibu__apga = dict(freq=None, axis=0, fill_value=None)
        check_unsupported_args(f'Groupby.{name_operation}', mlaev__yilzr,
            ibu__apga, package_name='pandas', module_name='GroupBy')
        check_args_kwargs(name_operation, 4, args, kws)
    elif name_operation == 'transform':
        kws = dict(kws)
        kbkl__huv = args[0] if len(args) > 0 else kws.pop('func', None)
        qxy__gris = kws.pop('engine', None)
        syb__nec = kws.pop('engine_kwargs', None)
        mlaev__yilzr = dict(engine=qxy__gris, engine_kwargs=syb__nec)
        ibu__apga = dict(engine=None, engine_kwargs=None)
        check_unsupported_args(f'Groupby.transform', mlaev__yilzr,
            ibu__apga, package_name='pandas', module_name='GroupBy')
    gtxc__awmk = {}
    for wafba__swoaf in grp.selection:
        out_columns.append(wafba__swoaf)
        gtxc__awmk[wafba__swoaf, name_operation] = wafba__swoaf
        zmden__fyvr = grp.df_type.columns.index(wafba__swoaf)
        data = grp.df_type.data[zmden__fyvr]
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
            jdtjw__eqbo, err_msg = get_groupby_output_dtype(data,
                get_literal_value(kbkl__huv), grp.df_type.index)
            if err_msg == 'ok':
                data = jdtjw__eqbo
            else:
                raise BodoError(
                    f'column type of {data.dtype} is not supported by {args[0]} yet.\n'
                    )
        out_data.append(data)
    if len(out_data) == 0:
        raise BodoError('No columns in output.')
    qctpf__tbyfr = DataFrameType(tuple(out_data), index, tuple(out_columns))
    if len(grp.selection) == 1 and grp.series_select and grp.as_index:
        qctpf__tbyfr = SeriesType(out_data[0].dtype, data=out_data[0],
            index=index, name_typ=types.StringLiteral(grp.selection[0]))
    return signature(qctpf__tbyfr, *args), gtxc__awmk


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
        ectp__nwfjm = _get_groupby_apply_udf_out_type(func, grp, f_args,
            kws, self.context, numba.core.registry.cpu_target.target_context)
        ofqfe__jijm = isinstance(ectp__nwfjm, (SeriesType,
            HeterogeneousSeriesType)
            ) and ectp__nwfjm.const_info is not None or not isinstance(
            ectp__nwfjm, (SeriesType, DataFrameType))
        if ofqfe__jijm:
            out_data = []
            out_columns = []
            out_column_type = []
            if not grp.as_index:
                get_keys_not_as_index(grp, out_columns, out_data,
                    out_column_type)
                hyn__dgbrl = NumericIndexType(types.int64, types.none)
            elif len(grp.keys) > 1:
                cmeg__ker = tuple(grp.df_type.columns.index(grp.keys[
                    fifdq__zdvu]) for fifdq__zdvu in range(len(grp.keys)))
                uuglv__gcv = tuple(grp.df_type.data[zmden__fyvr] for
                    zmden__fyvr in cmeg__ker)
                uuglv__gcv = tuple(to_str_arr_if_dict_array(ihjwq__ncxze) for
                    ihjwq__ncxze in uuglv__gcv)
                hyn__dgbrl = MultiIndexType(uuglv__gcv, tuple(types.literal
                    (zmm__muyct) for zmm__muyct in grp.keys))
            else:
                zmden__fyvr = grp.df_type.columns.index(grp.keys[0])
                geks__moa = grp.df_type.data[zmden__fyvr]
                geks__moa = to_str_arr_if_dict_array(geks__moa)
                hyn__dgbrl = bodo.hiframes.pd_index_ext.array_type_to_index(
                    geks__moa, types.literal(grp.keys[0]))
            out_data = tuple(out_data)
            out_columns = tuple(out_columns)
        else:
            oasm__bzv = tuple(grp.df_type.data[grp.df_type.columns.index(
                wafba__swoaf)] for wafba__swoaf in grp.keys)
            oasm__bzv = tuple(to_str_arr_if_dict_array(ihjwq__ncxze) for
                ihjwq__ncxze in oasm__bzv)
            rbgc__gzw = tuple(types.literal(jwd__knw) for jwd__knw in grp.keys
                ) + get_index_name_types(ectp__nwfjm.index)
            if not grp.as_index:
                oasm__bzv = types.Array(types.int64, 1, 'C'),
                rbgc__gzw = (types.none,) + get_index_name_types(ectp__nwfjm
                    .index)
            hyn__dgbrl = MultiIndexType(oasm__bzv +
                get_index_data_arr_types(ectp__nwfjm.index), rbgc__gzw)
        if ofqfe__jijm:
            if isinstance(ectp__nwfjm, HeterogeneousSeriesType):
                ham__luk, fym__wvp = ectp__nwfjm.const_info
                ghfx__schae = tuple(dtype_to_array_type(ihjwq__ncxze) for
                    ihjwq__ncxze in ectp__nwfjm.data.types)
                nubwa__ywdk = DataFrameType(out_data + ghfx__schae,
                    hyn__dgbrl, out_columns + fym__wvp)
            elif isinstance(ectp__nwfjm, SeriesType):
                qvyi__qez, fym__wvp = ectp__nwfjm.const_info
                ghfx__schae = tuple(dtype_to_array_type(ectp__nwfjm.dtype) for
                    ham__luk in range(qvyi__qez))
                nubwa__ywdk = DataFrameType(out_data + ghfx__schae,
                    hyn__dgbrl, out_columns + fym__wvp)
            else:
                tviso__jrb = get_udf_out_arr_type(ectp__nwfjm)
                if not grp.as_index:
                    nubwa__ywdk = DataFrameType(out_data + (tviso__jrb,),
                        hyn__dgbrl, out_columns + ('',))
                else:
                    nubwa__ywdk = SeriesType(tviso__jrb.dtype, tviso__jrb,
                        hyn__dgbrl, None)
        elif isinstance(ectp__nwfjm, SeriesType):
            nubwa__ywdk = SeriesType(ectp__nwfjm.dtype, ectp__nwfjm.data,
                hyn__dgbrl, ectp__nwfjm.name_typ)
        else:
            nubwa__ywdk = DataFrameType(ectp__nwfjm.data, hyn__dgbrl,
                ectp__nwfjm.columns)
        bzjry__bkib = gen_apply_pysig(len(f_args), kws.keys())
        ecay__ruqde = (func, *f_args) + tuple(kws.values())
        return signature(nubwa__ywdk, *ecay__ruqde).replace(pysig=bzjry__bkib)

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
    utdm__dzu = grp.df_type
    if grp.explicit_select:
        if len(grp.selection) == 1:
            xvsy__kokvu = grp.selection[0]
            tviso__jrb = utdm__dzu.data[utdm__dzu.columns.index(xvsy__kokvu)]
            tviso__jrb = to_str_arr_if_dict_array(tviso__jrb)
            mbmc__rypbj = SeriesType(tviso__jrb.dtype, tviso__jrb,
                utdm__dzu.index, types.literal(xvsy__kokvu))
        else:
            qonm__kfs = tuple(utdm__dzu.data[utdm__dzu.columns.index(
                wafba__swoaf)] for wafba__swoaf in grp.selection)
            qonm__kfs = tuple(to_str_arr_if_dict_array(ihjwq__ncxze) for
                ihjwq__ncxze in qonm__kfs)
            mbmc__rypbj = DataFrameType(qonm__kfs, utdm__dzu.index, tuple(
                grp.selection))
    else:
        mbmc__rypbj = utdm__dzu
    kyli__wiqr = mbmc__rypbj,
    kyli__wiqr += tuple(f_args)
    try:
        ectp__nwfjm = get_const_func_output_type(func, kyli__wiqr, kws,
            typing_context, target_context)
    except Exception as fdv__minbi:
        raise_bodo_error(get_udf_error_msg('GroupBy.apply()', fdv__minbi),
            getattr(fdv__minbi, 'loc', None))
    return ectp__nwfjm


def resolve_obj_pipe(self, grp, args, kws, obj_name):
    kws = dict(kws)
    func = args[0] if len(args) > 0 else kws.pop('func', None)
    f_args = tuple(args[1:]) if len(args) > 0 else ()
    kyli__wiqr = (grp,) + f_args
    try:
        ectp__nwfjm = get_const_func_output_type(func, kyli__wiqr, kws,
            self.context, numba.core.registry.cpu_target.target_context, False)
    except Exception as fdv__minbi:
        raise_bodo_error(get_udf_error_msg(f'{obj_name}.pipe()', fdv__minbi
            ), getattr(fdv__minbi, 'loc', None))
    bzjry__bkib = gen_apply_pysig(len(f_args), kws.keys())
    ecay__ruqde = (func, *f_args) + tuple(kws.values())
    return signature(ectp__nwfjm, *ecay__ruqde).replace(pysig=bzjry__bkib)


def gen_apply_pysig(n_args, kws):
    uyqh__cix = ', '.join(f'arg{fifdq__zdvu}' for fifdq__zdvu in range(n_args))
    uyqh__cix = uyqh__cix + ', ' if uyqh__cix else ''
    rof__pioig = ', '.join(f"{zcsjo__zfnm} = ''" for zcsjo__zfnm in kws)
    gqw__mnq = f'def apply_stub(func, {uyqh__cix}{rof__pioig}):\n'
    gqw__mnq += '    pass\n'
    mzq__iyud = {}
    exec(gqw__mnq, {}, mzq__iyud)
    rvyr__gszf = mzq__iyud['apply_stub']
    return numba.core.utils.pysignature(rvyr__gszf)


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
        jdtjw__eqbo = get_pivot_output_dtype(data, aggfunc.literal_value)
        jwxaq__bdzib = dtype_to_array_type(jdtjw__eqbo)
        if is_overload_none(_pivot_values):
            raise_bodo_error(
                'Dataframe.pivot_table() requires explicit annotation to determine output columns. For more information, see: https://docs.bodo.ai/latest/source/programming_with_bodo/pandas.html'
                )
        hkeg__gxto = _pivot_values.meta
        ths__nzy = len(hkeg__gxto)
        zmden__fyvr = df.columns.index(index)
        geks__moa = df.data[zmden__fyvr]
        geks__moa = to_str_arr_if_dict_array(geks__moa)
        iaru__xhx = bodo.hiframes.pd_index_ext.array_type_to_index(geks__moa,
            types.StringLiteral(index))
        zunzh__uza = DataFrameType((jwxaq__bdzib,) * ths__nzy, iaru__xhx,
            tuple(hkeg__gxto))
        return signature(zunzh__uza, *args)


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
        jwxaq__bdzib = types.Array(types.int64, 1, 'C')
        hkeg__gxto = _pivot_values.meta
        ths__nzy = len(hkeg__gxto)
        iaru__xhx = bodo.hiframes.pd_index_ext.array_type_to_index(
            to_str_arr_if_dict_array(index.data), types.StringLiteral('index'))
        zunzh__uza = DataFrameType((jwxaq__bdzib,) * ths__nzy, iaru__xhx,
            tuple(hkeg__gxto))
        return signature(zunzh__uza, *args)


CrossTabTyper._no_unliteral = True


@lower_builtin(crosstab_dummy, types.VarArg(types.Any))
def lower_crosstab_dummy(context, builder, sig, args):
    return context.get_constant_null(sig.return_type)


def get_group_indices(keys, dropna, _is_parallel):
    return np.arange(len(keys))


@overload(get_group_indices)
def get_group_indices_overload(keys, dropna, _is_parallel):
    gqw__mnq = 'def impl(keys, dropna, _is_parallel):\n'
    gqw__mnq += (
        "    ev = bodo.utils.tracing.Event('get_group_indices', _is_parallel)\n"
        )
    gqw__mnq += '    info_list = [{}]\n'.format(', '.join(
        f'array_to_info(keys[{fifdq__zdvu}])' for fifdq__zdvu in range(len(
        keys.types))))
    gqw__mnq += '    table = arr_info_list_to_table(info_list)\n'
    gqw__mnq += '    group_labels = np.empty(len(keys[0]), np.int64)\n'
    gqw__mnq += '    sort_idx = np.empty(len(keys[0]), np.int64)\n'
    gqw__mnq += """    ngroups = get_groupby_labels(table, group_labels.ctypes, sort_idx.ctypes, dropna, _is_parallel)
"""
    gqw__mnq += '    delete_table_decref_arrays(table)\n'
    gqw__mnq += '    ev.finalize()\n'
    gqw__mnq += '    return sort_idx, group_labels, ngroups\n'
    mzq__iyud = {}
    exec(gqw__mnq, {'bodo': bodo, 'np': np, 'get_groupby_labels':
        get_groupby_labels, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table,
        'delete_table_decref_arrays': delete_table_decref_arrays}, mzq__iyud)
    vbe__mhn = mzq__iyud['impl']
    return vbe__mhn


@numba.njit(no_cpython_wrapper=True)
def generate_slices(labels, ngroups):
    tmxxt__igoxi = len(labels)
    ehkp__sohh = np.zeros(ngroups, dtype=np.int64)
    knjlf__pfq = np.zeros(ngroups, dtype=np.int64)
    vwl__dojvs = 0
    orhm__uatt = 0
    for fifdq__zdvu in range(tmxxt__igoxi):
        kbe__gytv = labels[fifdq__zdvu]
        if kbe__gytv < 0:
            vwl__dojvs += 1
        else:
            orhm__uatt += 1
            if fifdq__zdvu == tmxxt__igoxi - 1 or kbe__gytv != labels[
                fifdq__zdvu + 1]:
                ehkp__sohh[kbe__gytv] = vwl__dojvs
                knjlf__pfq[kbe__gytv] = vwl__dojvs + orhm__uatt
                vwl__dojvs += orhm__uatt
                orhm__uatt = 0
    return ehkp__sohh, knjlf__pfq


def shuffle_dataframe(df, keys, _is_parallel):
    return df, keys, _is_parallel


@overload(shuffle_dataframe, prefer_literal=True)
def overload_shuffle_dataframe(df, keys, _is_parallel):
    vbe__mhn, ham__luk = gen_shuffle_dataframe(df, keys, _is_parallel)
    return vbe__mhn


def gen_shuffle_dataframe(df, keys, _is_parallel):
    qvyi__qez = len(df.columns)
    sqp__kux = len(keys.types)
    assert is_overload_constant_bool(_is_parallel
        ), 'shuffle_dataframe: _is_parallel is not a constant'
    gqw__mnq = 'def impl(df, keys, _is_parallel):\n'
    if is_overload_false(_is_parallel):
        gqw__mnq += '  return df, keys, get_null_shuffle_info()\n'
        mzq__iyud = {}
        exec(gqw__mnq, {'get_null_shuffle_info': get_null_shuffle_info},
            mzq__iyud)
        vbe__mhn = mzq__iyud['impl']
        return vbe__mhn
    for fifdq__zdvu in range(qvyi__qez):
        gqw__mnq += f"""  in_arr{fifdq__zdvu} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {fifdq__zdvu})
"""
    gqw__mnq += f"""  in_index_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))
"""
    gqw__mnq += '  info_list = [{}, {}, {}]\n'.format(', '.join(
        f'array_to_info(keys[{fifdq__zdvu}])' for fifdq__zdvu in range(
        sqp__kux)), ', '.join(f'array_to_info(in_arr{fifdq__zdvu})' for
        fifdq__zdvu in range(qvyi__qez)), 'array_to_info(in_index_arr)')
    gqw__mnq += '  table = arr_info_list_to_table(info_list)\n'
    gqw__mnq += (
        f'  out_table = shuffle_table(table, {sqp__kux}, _is_parallel, 1)\n')
    for fifdq__zdvu in range(sqp__kux):
        gqw__mnq += f"""  out_key{fifdq__zdvu} = info_to_array(info_from_table(out_table, {fifdq__zdvu}), keys{fifdq__zdvu}_typ)
"""
    for fifdq__zdvu in range(qvyi__qez):
        gqw__mnq += f"""  out_arr{fifdq__zdvu} = info_to_array(info_from_table(out_table, {fifdq__zdvu + sqp__kux}), in_arr{fifdq__zdvu}_typ)
"""
    gqw__mnq += f"""  out_arr_index = info_to_array(info_from_table(out_table, {sqp__kux + qvyi__qez}), ind_arr_typ)
"""
    gqw__mnq += '  shuffle_info = get_shuffle_info(out_table)\n'
    gqw__mnq += '  delete_table(out_table)\n'
    gqw__mnq += '  delete_table(table)\n'
    out_data = ', '.join(f'out_arr{fifdq__zdvu}' for fifdq__zdvu in range(
        qvyi__qez))
    gqw__mnq += (
        '  out_index = bodo.utils.conversion.index_from_array(out_arr_index)\n'
        )
    gqw__mnq += f"""  out_df = bodo.hiframes.pd_dataframe_ext.init_dataframe(({out_data},), out_index, {gen_const_tup(df.columns)})
"""
    gqw__mnq += '  return out_df, ({},), shuffle_info\n'.format(', '.join(
        f'out_key{fifdq__zdvu}' for fifdq__zdvu in range(sqp__kux)))
    hdfw__xwxv = {'bodo': bodo, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'shuffle_table':
        shuffle_table, 'info_from_table': info_from_table, 'info_to_array':
        info_to_array, 'delete_table': delete_table, 'get_shuffle_info':
        get_shuffle_info, 'ind_arr_typ': types.Array(types.int64, 1, 'C') if
        isinstance(df.index, RangeIndexType) else df.index.data}
    hdfw__xwxv.update({f'keys{fifdq__zdvu}_typ': keys.types[fifdq__zdvu] for
        fifdq__zdvu in range(sqp__kux)})
    hdfw__xwxv.update({f'in_arr{fifdq__zdvu}_typ': df.data[fifdq__zdvu] for
        fifdq__zdvu in range(qvyi__qez)})
    mzq__iyud = {}
    exec(gqw__mnq, hdfw__xwxv, mzq__iyud)
    vbe__mhn = mzq__iyud['impl']
    return vbe__mhn, hdfw__xwxv


def reverse_shuffle(data, shuffle_info):
    return data


@overload(reverse_shuffle)
def overload_reverse_shuffle(data, shuffle_info):
    if isinstance(data, bodo.hiframes.pd_multi_index_ext.MultiIndexType):
        zitdw__mngqh = len(data.array_types)
        gqw__mnq = 'def impl(data, shuffle_info):\n'
        gqw__mnq += '  info_list = [{}]\n'.format(', '.join(
            f'array_to_info(data._data[{fifdq__zdvu}])' for fifdq__zdvu in
            range(zitdw__mngqh)))
        gqw__mnq += '  table = arr_info_list_to_table(info_list)\n'
        gqw__mnq += (
            '  out_table = reverse_shuffle_table(table, shuffle_info)\n')
        for fifdq__zdvu in range(zitdw__mngqh):
            gqw__mnq += f"""  out_arr{fifdq__zdvu} = info_to_array(info_from_table(out_table, {fifdq__zdvu}), data._data[{fifdq__zdvu}])
"""
        gqw__mnq += '  delete_table(out_table)\n'
        gqw__mnq += '  delete_table(table)\n'
        gqw__mnq += (
            '  return init_multi_index(({},), data._names, data._name)\n'.
            format(', '.join(f'out_arr{fifdq__zdvu}' for fifdq__zdvu in
            range(zitdw__mngqh))))
        mzq__iyud = {}
        exec(gqw__mnq, {'bodo': bodo, 'array_to_info': array_to_info,
            'arr_info_list_to_table': arr_info_list_to_table,
            'reverse_shuffle_table': reverse_shuffle_table,
            'info_from_table': info_from_table, 'info_to_array':
            info_to_array, 'delete_table': delete_table, 'init_multi_index':
            bodo.hiframes.pd_multi_index_ext.init_multi_index}, mzq__iyud)
        vbe__mhn = mzq__iyud['impl']
        return vbe__mhn
    if bodo.hiframes.pd_index_ext.is_index_type(data):

        def impl_index(data, shuffle_info):
            wdszj__mxow = bodo.utils.conversion.index_to_array(data)
            ocw__dga = reverse_shuffle(wdszj__mxow, shuffle_info)
            return bodo.utils.conversion.index_from_array(ocw__dga)
        return impl_index

    def impl_arr(data, shuffle_info):
        xgq__hlmgc = [array_to_info(data)]
        lkup__vqv = arr_info_list_to_table(xgq__hlmgc)
        wtx__pscny = reverse_shuffle_table(lkup__vqv, shuffle_info)
        ocw__dga = info_to_array(info_from_table(wtx__pscny, 0), data)
        delete_table(wtx__pscny)
        delete_table(lkup__vqv)
        return ocw__dga
    return impl_arr


@overload_method(DataFrameGroupByType, 'value_counts', inline='always',
    no_unliteral=True)
def groupby_value_counts(grp, normalize=False, sort=True, ascending=False,
    bins=None, dropna=True):
    mlaev__yilzr = dict(normalize=normalize, sort=sort, bins=bins, dropna=
        dropna)
    ibu__apga = dict(normalize=False, sort=True, bins=None, dropna=True)
    check_unsupported_args('Groupby.value_counts', mlaev__yilzr, ibu__apga,
        package_name='pandas', module_name='GroupBy')
    if len(grp.selection) > 1 or not grp.as_index:
        raise BodoError(
            "'DataFrameGroupBy' object has no attribute 'value_counts'")
    if not is_overload_constant_bool(ascending):
        raise BodoError(
            'Groupby.value_counts() ascending must be a constant boolean')
    ofl__rlw = get_overload_const_bool(ascending)
    gnzug__icg = grp.selection[0]
    gqw__mnq = f"""def impl(grp, normalize=False, sort=True, ascending=False, bins=None, dropna=True):
"""
    lmra__xnpz = (
        f"lambda S: S.value_counts(ascending={ofl__rlw}, _index_name='{gnzug__icg}')"
        )
    gqw__mnq += f'    return grp.apply({lmra__xnpz})\n'
    mzq__iyud = {}
    exec(gqw__mnq, {'bodo': bodo}, mzq__iyud)
    vbe__mhn = mzq__iyud['impl']
    return vbe__mhn


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
    for rje__kpff in groupby_unsupported_attr:
        overload_attribute(DataFrameGroupByType, rje__kpff, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{rje__kpff}'))
    for rje__kpff in groupby_unsupported:
        overload_method(DataFrameGroupByType, rje__kpff, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{rje__kpff}'))
    for rje__kpff in series_only_unsupported_attrs:
        overload_attribute(DataFrameGroupByType, rje__kpff, no_unliteral=True)(
            create_unsupported_overload(f'SeriesGroupBy.{rje__kpff}'))
    for rje__kpff in series_only_unsupported:
        overload_method(DataFrameGroupByType, rje__kpff, no_unliteral=True)(
            create_unsupported_overload(f'SeriesGroupBy.{rje__kpff}'))
    for rje__kpff in dataframe_only_unsupported:
        overload_method(DataFrameGroupByType, rje__kpff, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{rje__kpff}'))


_install_groupby_unsupported()
