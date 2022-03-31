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
        kaffy__pkdff = [('obj', fe_type.df_type)]
        super(GroupbyModel, self).__init__(dmm, fe_type, kaffy__pkdff)


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
        vqk__vkji = args[0]
        yno__bsrlu = signature.return_type
        qceol__wcvxq = cgutils.create_struct_proxy(yno__bsrlu)(context, builder
            )
        qceol__wcvxq.obj = vqk__vkji
        context.nrt.incref(builder, signature.args[0], vqk__vkji)
        return qceol__wcvxq._getvalue()
    if is_overload_constant_list(by_type):
        keys = tuple(get_overload_const_list(by_type))
    elif is_literal_type(by_type):
        keys = get_literal_value(by_type),
    else:
        assert False, 'Reached unreachable code in init_groupby; there is an validate_groupby_spec'
    selection = list(obj_type.columns)
    for mwmgj__fmvni in keys:
        selection.remove(mwmgj__fmvni)
    if is_overload_constant_bool(as_index_type):
        as_index = is_overload_true(as_index_type)
    else:
        as_index = True
    if is_overload_constant_bool(dropna_type):
        dropna = is_overload_true(dropna_type)
    else:
        dropna = True
    yno__bsrlu = DataFrameGroupByType(obj_type, keys, tuple(selection),
        as_index, dropna, False)
    return yno__bsrlu(obj_type, by_type, as_index_type, dropna_type), codegen


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
        grpby, ktxpe__relj = args
        if isinstance(grpby, DataFrameGroupByType):
            series_select = False
            if isinstance(ktxpe__relj, (tuple, list)):
                if len(set(ktxpe__relj).difference(set(grpby.df_type.columns))
                    ) > 0:
                    raise_bodo_error(
                        'groupby: selected column {} not found in dataframe'
                        .format(set(ktxpe__relj).difference(set(grpby.
                        df_type.columns))))
                selection = ktxpe__relj
            else:
                if ktxpe__relj not in grpby.df_type.columns:
                    raise_bodo_error(
                        'groupby: selected column {} not found in dataframe'
                        .format(ktxpe__relj))
                selection = ktxpe__relj,
                series_select = True
            wqs__pdvxy = DataFrameGroupByType(grpby.df_type, grpby.keys,
                selection, grpby.as_index, grpby.dropna, True, series_select)
            return signature(wqs__pdvxy, *args)


@infer_global(operator.getitem)
class GetItemDataFrameGroupBy(AbstractTemplate):

    def generic(self, args, kws):
        grpby, ktxpe__relj = args
        if isinstance(grpby, DataFrameGroupByType) and is_literal_type(
            ktxpe__relj):
            wqs__pdvxy = StaticGetItemDataFrameGroupBy.generic(self, (grpby,
                get_literal_value(ktxpe__relj)), {}).return_type
            return signature(wqs__pdvxy, *args)


GetItemDataFrameGroupBy.prefer_literal = True


@lower_builtin('static_getitem', DataFrameGroupByType, types.Any)
@lower_builtin(operator.getitem, DataFrameGroupByType, types.Any)
def static_getitem_df_groupby(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


def get_groupby_output_dtype(arr_type, func_name, index_type=None):
    arr_type = to_str_arr_if_dict_array(arr_type)
    dmq__zwzvl = arr_type == ArrayItemArrayType(string_array_type)
    ypcv__kqxs = arr_type.dtype
    if isinstance(ypcv__kqxs, bodo.hiframes.datetime_timedelta_ext.
        DatetimeTimeDeltaType):
        raise BodoError(
            f"""column type of {ypcv__kqxs} is not supported in groupby built-in function {func_name}.
{dt_err}"""
            )
    if func_name == 'median' and not isinstance(ypcv__kqxs, (Decimal128Type,
        types.Float, types.Integer)):
        return (None,
            'For median, only column of integer, float or Decimal type are allowed'
            )
    if func_name in ('first', 'last', 'sum', 'prod', 'min', 'max', 'count',
        'nunique', 'head') and isinstance(arr_type, (TupleArrayType,
        ArrayItemArrayType)):
        return (None,
            f'column type of list/tuple of {ypcv__kqxs} is not supported in groupby built-in function {func_name}'
            )
    if func_name in {'median', 'mean', 'var', 'std'} and isinstance(ypcv__kqxs,
        (Decimal128Type, types.Integer, types.Float)):
        return dtype_to_array_type(types.float64), 'ok'
    if not isinstance(ypcv__kqxs, (types.Integer, types.Float, types.Boolean)):
        if dmq__zwzvl or ypcv__kqxs == types.unicode_type:
            if func_name not in {'count', 'nunique', 'min', 'max', 'sum',
                'first', 'last', 'head'}:
                return (None,
                    f'column type of strings or list of strings is not supported in groupby built-in function {func_name}'
                    )
        else:
            if isinstance(ypcv__kqxs, bodo.PDCategoricalDtype):
                if func_name in ('min', 'max') and not ypcv__kqxs.ordered:
                    return (None,
                        f'categorical column must be ordered in groupby built-in function {func_name}'
                        )
            if func_name not in {'count', 'nunique', 'min', 'max', 'first',
                'last', 'head'}:
                return (None,
                    f'column type of {ypcv__kqxs} is not supported in groupby built-in function {func_name}'
                    )
    if isinstance(ypcv__kqxs, types.Boolean) and func_name in {'cumsum',
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
    ypcv__kqxs = arr_type.dtype
    if func_name in {'count'}:
        return IntDtype(types.int64)
    if func_name in {'sum', 'prod', 'min', 'max'}:
        if func_name in {'sum', 'prod'} and not isinstance(ypcv__kqxs, (
            types.Integer, types.Float)):
            raise BodoError(
                'pivot_table(): sum and prod operations require integer or float input'
                )
        if isinstance(ypcv__kqxs, types.Integer):
            return IntDtype(ypcv__kqxs)
        return ypcv__kqxs
    if func_name in {'mean', 'var', 'std'}:
        return types.float64
    raise BodoError('invalid pivot operation')


def check_args_kwargs(func_name, len_args, args, kws):
    if len(kws) > 0:
        vzvw__dpj = list(kws.keys())[0]
        raise BodoError(
            f"Groupby.{func_name}() got an unexpected keyword argument '{vzvw__dpj}'."
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
    for mwmgj__fmvni in grp.keys:
        if multi_level_names:
            vkrk__nyxfi = mwmgj__fmvni, ''
        else:
            vkrk__nyxfi = mwmgj__fmvni
        zza__nfg = grp.df_type.columns.index(mwmgj__fmvni)
        data = to_str_arr_if_dict_array(grp.df_type.data[zza__nfg])
        out_columns.append(vkrk__nyxfi)
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
        velmb__jpub = tuple(grp.df_type.columns.index(grp.keys[vad__trzeb]) for
            vad__trzeb in range(len(grp.keys)))
        lmn__oshc = tuple(grp.df_type.data[zza__nfg] for zza__nfg in
            velmb__jpub)
        lmn__oshc = tuple(to_str_arr_if_dict_array(bfjih__fjk) for
            bfjih__fjk in lmn__oshc)
        index = MultiIndexType(lmn__oshc, tuple(types.StringLiteral(
            mwmgj__fmvni) for mwmgj__fmvni in grp.keys))
    else:
        zza__nfg = grp.df_type.columns.index(grp.keys[0])
        ktcpj__yfye = to_str_arr_if_dict_array(grp.df_type.data[zza__nfg])
        index = bodo.hiframes.pd_index_ext.array_type_to_index(ktcpj__yfye,
            types.StringLiteral(grp.keys[0]))
    pdk__dks = {}
    omq__tba = []
    if func_name in ('size', 'count'):
        kws = dict(kws) if kws else {}
        check_args_kwargs(func_name, 0, args, kws)
    if func_name == 'size':
        out_data.append(types.Array(types.int64, 1, 'C'))
        out_columns.append('size')
        pdk__dks[None, 'size'] = 'size'
    else:
        columns = (grp.selection if func_name != 'head' or grp.
            explicit_select else grp.df_type.columns)
        for qbkuy__njl in columns:
            zza__nfg = grp.df_type.columns.index(qbkuy__njl)
            data = grp.df_type.data[zza__nfg]
            data = to_str_arr_if_dict_array(data)
            lwywf__foet = ColumnType.NonNumericalColumn.value
            if isinstance(data, (types.Array, IntegerArrayType)
                ) and isinstance(data.dtype, (types.Integer, types.Float)):
                lwywf__foet = ColumnType.NumericalColumn.value
            if func_name == 'agg':
                try:
                    osj__shgvg = SeriesType(data.dtype, data, None, string_type
                        )
                    ekzl__bvgq = get_const_func_output_type(func, (
                        osj__shgvg,), {}, typing_context, target_context)
                    if ekzl__bvgq != ArrayItemArrayType(string_array_type):
                        ekzl__bvgq = dtype_to_array_type(ekzl__bvgq)
                    err_msg = 'ok'
                except:
                    raise_bodo_error(
                        'Groupy.agg()/Groupy.aggregate(): column {col} of type {type} is unsupported/not a valid input type for user defined function'
                        .format(col=qbkuy__njl, type=data.dtype))
            else:
                if func_name in ('first', 'last', 'min', 'max'):
                    kws = dict(kws) if kws else {}
                    lmhy__cpz = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', False)
                    ect__sjmj = args[1] if len(args) > 1 else kws.pop(
                        'min_count', -1)
                    hso__emaxk = dict(numeric_only=lmhy__cpz, min_count=
                        ect__sjmj)
                    bnbik__uqut = dict(numeric_only=False, min_count=-1)
                    check_unsupported_args(f'Groupby.{func_name}',
                        hso__emaxk, bnbik__uqut, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('sum', 'prod'):
                    kws = dict(kws) if kws else {}
                    lmhy__cpz = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', True)
                    ect__sjmj = args[1] if len(args) > 1 else kws.pop(
                        'min_count', 0)
                    hso__emaxk = dict(numeric_only=lmhy__cpz, min_count=
                        ect__sjmj)
                    bnbik__uqut = dict(numeric_only=True, min_count=0)
                    check_unsupported_args(f'Groupby.{func_name}',
                        hso__emaxk, bnbik__uqut, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('mean', 'median'):
                    kws = dict(kws) if kws else {}
                    lmhy__cpz = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', True)
                    hso__emaxk = dict(numeric_only=lmhy__cpz)
                    bnbik__uqut = dict(numeric_only=True)
                    check_unsupported_args(f'Groupby.{func_name}',
                        hso__emaxk, bnbik__uqut, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('idxmin', 'idxmax'):
                    kws = dict(kws) if kws else {}
                    vud__xif = args[0] if len(args) > 0 else kws.pop('axis', 0)
                    drfkk__hbv = args[1] if len(args) > 1 else kws.pop('skipna'
                        , True)
                    hso__emaxk = dict(axis=vud__xif, skipna=drfkk__hbv)
                    bnbik__uqut = dict(axis=0, skipna=True)
                    check_unsupported_args(f'Groupby.{func_name}',
                        hso__emaxk, bnbik__uqut, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('var', 'std'):
                    kws = dict(kws) if kws else {}
                    gwo__dbtn = args[0] if len(args) > 0 else kws.pop('ddof', 1
                        )
                    hso__emaxk = dict(ddof=gwo__dbtn)
                    bnbik__uqut = dict(ddof=1)
                    check_unsupported_args(f'Groupby.{func_name}',
                        hso__emaxk, bnbik__uqut, package_name='pandas',
                        module_name='GroupBy')
                elif func_name == 'nunique':
                    kws = dict(kws) if kws else {}
                    dropna = args[0] if len(args) > 0 else kws.pop('dropna', 1)
                    check_args_kwargs(func_name, 1, args, kws)
                elif func_name == 'head':
                    if len(args) == 0:
                        kws.pop('n', None)
                ekzl__bvgq, err_msg = get_groupby_output_dtype(data,
                    func_name, grp.df_type.index)
            if err_msg == 'ok':
                vuv__dcus = to_str_arr_if_dict_array(ekzl__bvgq)
                out_data.append(vuv__dcus)
                out_columns.append(qbkuy__njl)
                if func_name == 'agg':
                    zfp__qfail = bodo.ir.aggregate._get_udf_name(bodo.ir.
                        aggregate._get_const_agg_func(func, None))
                    pdk__dks[qbkuy__njl, zfp__qfail] = qbkuy__njl
                else:
                    pdk__dks[qbkuy__njl, func_name] = qbkuy__njl
                out_column_type.append(lwywf__foet)
            else:
                omq__tba.append(err_msg)
    if func_name == 'sum':
        mkqxx__nzyq = any([(yyzk__mcot == ColumnType.NumericalColumn.value) for
            yyzk__mcot in out_column_type])
        if mkqxx__nzyq:
            out_data = [yyzk__mcot for yyzk__mcot, bpg__qvi in zip(out_data,
                out_column_type) if bpg__qvi != ColumnType.
                NonNumericalColumn.value]
            out_columns = [yyzk__mcot for yyzk__mcot, bpg__qvi in zip(
                out_columns, out_column_type) if bpg__qvi != ColumnType.
                NonNumericalColumn.value]
            pdk__dks = {}
            for qbkuy__njl in out_columns:
                if grp.as_index is False and qbkuy__njl in grp.keys:
                    continue
                pdk__dks[qbkuy__njl, func_name] = qbkuy__njl
    hdo__cqktb = len(omq__tba)
    if len(out_data) == 0:
        if hdo__cqktb == 0:
            raise BodoError('No columns in output.')
        else:
            raise BodoError(
                'No columns in output. {} column{} dropped for following reasons: {}'
                .format(hdo__cqktb, ' was' if hdo__cqktb == 1 else 's were',
                ','.join(omq__tba)))
    lxhg__epl = DataFrameType(tuple(out_data), index, tuple(out_columns))
    if (len(grp.selection) == 1 and grp.series_select and grp.as_index or 
        func_name == 'size' and grp.as_index):
        if isinstance(out_data[0], IntegerArrayType):
            ptaey__yjwoi = IntDtype(out_data[0].dtype)
        else:
            ptaey__yjwoi = out_data[0].dtype
        fbuhh__edwe = (types.none if func_name == 'size' else types.
            StringLiteral(grp.selection[0]))
        lxhg__epl = SeriesType(ptaey__yjwoi, index=index, name_typ=fbuhh__edwe)
    return signature(lxhg__epl, *args), pdk__dks


def get_agg_funcname_and_outtyp(grp, col, f_val, typing_context, target_context
    ):
    uwwp__kwkdj = True
    if isinstance(f_val, str):
        uwwp__kwkdj = False
        qwd__ewx = f_val
    elif is_overload_constant_str(f_val):
        uwwp__kwkdj = False
        qwd__ewx = get_overload_const_str(f_val)
    elif bodo.utils.typing.is_builtin_function(f_val):
        uwwp__kwkdj = False
        qwd__ewx = bodo.utils.typing.get_builtin_function_name(f_val)
    if not uwwp__kwkdj:
        if qwd__ewx not in bodo.ir.aggregate.supported_agg_funcs[:-1]:
            raise BodoError(f'unsupported aggregate function {qwd__ewx}')
        wqs__pdvxy = DataFrameGroupByType(grp.df_type, grp.keys, (col,),
            grp.as_index, grp.dropna, True, True)
        out_tp = get_agg_typ(wqs__pdvxy, (), qwd__ewx, typing_context,
            target_context)[0].return_type
    else:
        if is_expr(f_val, 'make_function'):
            mjnz__kewlk = types.functions.MakeFunctionLiteral(f_val)
        else:
            mjnz__kewlk = f_val
        validate_udf('agg', mjnz__kewlk)
        func = get_overload_const_func(mjnz__kewlk, None)
        zhd__xgsea = func.code if hasattr(func, 'code') else func.__code__
        qwd__ewx = zhd__xgsea.co_name
        wqs__pdvxy = DataFrameGroupByType(grp.df_type, grp.keys, (col,),
            grp.as_index, grp.dropna, True, True)
        out_tp = get_agg_typ(wqs__pdvxy, (), 'agg', typing_context,
            target_context, mjnz__kewlk)[0].return_type
    return qwd__ewx, out_tp


def resolve_agg(grp, args, kws, typing_context, target_context):
    func = get_call_expr_arg('agg', args, dict(kws), 0, 'func', default=
        types.none)
    eji__taba = kws and all(isinstance(kks__uvgog, types.Tuple) and len(
        kks__uvgog) == 2 for kks__uvgog in kws.values())
    if is_overload_none(func) and not eji__taba:
        raise_bodo_error("Groupby.agg()/aggregate(): Must provide 'func'")
    if len(args) > 1 or kws and not eji__taba:
        raise_bodo_error(
            'Groupby.agg()/aggregate(): passing extra arguments to functions not supported yet.'
            )
    jsqv__wayh = False

    def _append_out_type(grp, out_data, out_tp):
        if grp.as_index is False:
            out_data.append(out_tp.data[len(grp.keys)])
        else:
            out_data.append(out_tp.data)
    if eji__taba or is_overload_constant_dict(func):
        if eji__taba:
            fuovi__qkf = [get_literal_value(indi__pshmj) for indi__pshmj,
                tkfai__meuz in kws.values()]
            akgwf__hwx = [get_literal_value(aeso__dqz) for tkfai__meuz,
                aeso__dqz in kws.values()]
        else:
            edxaw__hlqy = get_overload_constant_dict(func)
            fuovi__qkf = tuple(edxaw__hlqy.keys())
            akgwf__hwx = tuple(edxaw__hlqy.values())
        if 'head' in akgwf__hwx:
            raise BodoError(
                'Groupby.agg()/aggregate(): head cannot be mixed with other groupby operations.'
                )
        if any(qbkuy__njl not in grp.selection and qbkuy__njl not in grp.
            keys for qbkuy__njl in fuovi__qkf):
            raise_bodo_error(
                f'Selected column names {fuovi__qkf} not all available in dataframe column names {grp.selection}'
                )
        multi_level_names = any(isinstance(f_val, (tuple, list)) for f_val in
            akgwf__hwx)
        if eji__taba and multi_level_names:
            raise_bodo_error(
                'Groupby.agg()/aggregate(): cannot pass multiple functions in a single pd.NamedAgg()'
                )
        pdk__dks = {}
        out_columns = []
        out_data = []
        out_column_type = []
        ccibz__vgpi = []
        if not grp.as_index:
            get_keys_not_as_index(grp, out_columns, out_data,
                out_column_type, multi_level_names=multi_level_names)
        for mlj__bge, f_val in zip(fuovi__qkf, akgwf__hwx):
            if isinstance(f_val, (tuple, list)):
                xjx__fay = 0
                for mjnz__kewlk in f_val:
                    qwd__ewx, out_tp = get_agg_funcname_and_outtyp(grp,
                        mlj__bge, mjnz__kewlk, typing_context, target_context)
                    jsqv__wayh = qwd__ewx in list_cumulative
                    if qwd__ewx == '<lambda>' and len(f_val) > 1:
                        qwd__ewx = '<lambda_' + str(xjx__fay) + '>'
                        xjx__fay += 1
                    out_columns.append((mlj__bge, qwd__ewx))
                    pdk__dks[mlj__bge, qwd__ewx] = mlj__bge, qwd__ewx
                    _append_out_type(grp, out_data, out_tp)
            else:
                qwd__ewx, out_tp = get_agg_funcname_and_outtyp(grp,
                    mlj__bge, f_val, typing_context, target_context)
                jsqv__wayh = qwd__ewx in list_cumulative
                if multi_level_names:
                    out_columns.append((mlj__bge, qwd__ewx))
                    pdk__dks[mlj__bge, qwd__ewx] = mlj__bge, qwd__ewx
                elif not eji__taba:
                    out_columns.append(mlj__bge)
                    pdk__dks[mlj__bge, qwd__ewx] = mlj__bge
                elif eji__taba:
                    ccibz__vgpi.append(qwd__ewx)
                _append_out_type(grp, out_data, out_tp)
        if eji__taba:
            for vad__trzeb, xpl__mkoje in enumerate(kws.keys()):
                out_columns.append(xpl__mkoje)
                pdk__dks[fuovi__qkf[vad__trzeb], ccibz__vgpi[vad__trzeb]
                    ] = xpl__mkoje
        if jsqv__wayh:
            index = grp.df_type.index
        else:
            index = out_tp.index
        lxhg__epl = DataFrameType(tuple(out_data), index, tuple(out_columns))
        return signature(lxhg__epl, *args), pdk__dks
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
        xjx__fay = 0
        if not grp.as_index:
            get_keys_not_as_index(grp, out_columns, out_data, out_column_type)
        pdk__dks = {}
        bwkvh__sdc = grp.selection[0]
        for f_val in func.types:
            qwd__ewx, out_tp = get_agg_funcname_and_outtyp(grp, bwkvh__sdc,
                f_val, typing_context, target_context)
            jsqv__wayh = qwd__ewx in list_cumulative
            if qwd__ewx == '<lambda>':
                qwd__ewx = '<lambda_' + str(xjx__fay) + '>'
                xjx__fay += 1
            out_columns.append(qwd__ewx)
            pdk__dks[bwkvh__sdc, qwd__ewx] = qwd__ewx
            _append_out_type(grp, out_data, out_tp)
        if jsqv__wayh:
            index = grp.df_type.index
        else:
            index = out_tp.index
        lxhg__epl = DataFrameType(tuple(out_data), index, tuple(out_columns))
        return signature(lxhg__epl, *args), pdk__dks
    qwd__ewx = ''
    if types.unliteral(func) == types.unicode_type:
        qwd__ewx = get_overload_const_str(func)
    if bodo.utils.typing.is_builtin_function(func):
        qwd__ewx = bodo.utils.typing.get_builtin_function_name(func)
    if qwd__ewx:
        args = args[1:]
        kws.pop('func', None)
        return get_agg_typ(grp, args, qwd__ewx, typing_context, kws)
    validate_udf('agg', func)
    return get_agg_typ(grp, args, 'agg', typing_context, target_context, func)


def resolve_transformative(grp, args, kws, msg, name_operation):
    index = grp.df_type.index
    out_columns = []
    out_data = []
    if name_operation in list_cumulative:
        kws = dict(kws) if kws else {}
        vud__xif = args[0] if len(args) > 0 else kws.pop('axis', 0)
        lmhy__cpz = args[1] if len(args) > 1 else kws.pop('numeric_only', False
            )
        drfkk__hbv = args[2] if len(args) > 2 else kws.pop('skipna', 1)
        hso__emaxk = dict(axis=vud__xif, numeric_only=lmhy__cpz)
        bnbik__uqut = dict(axis=0, numeric_only=False)
        check_unsupported_args(f'Groupby.{name_operation}', hso__emaxk,
            bnbik__uqut, package_name='pandas', module_name='GroupBy')
        check_args_kwargs(name_operation, 3, args, kws)
    elif name_operation == 'shift':
        mjf__dfvv = args[0] if len(args) > 0 else kws.pop('periods', 1)
        qdizu__uiwi = args[1] if len(args) > 1 else kws.pop('freq', None)
        vud__xif = args[2] if len(args) > 2 else kws.pop('axis', 0)
        styl__vzei = args[3] if len(args) > 3 else kws.pop('fill_value', None)
        hso__emaxk = dict(freq=qdizu__uiwi, axis=vud__xif, fill_value=
            styl__vzei)
        bnbik__uqut = dict(freq=None, axis=0, fill_value=None)
        check_unsupported_args(f'Groupby.{name_operation}', hso__emaxk,
            bnbik__uqut, package_name='pandas', module_name='GroupBy')
        check_args_kwargs(name_operation, 4, args, kws)
    elif name_operation == 'transform':
        kws = dict(kws)
        wef__bzxk = args[0] if len(args) > 0 else kws.pop('func', None)
        cysvb__xnp = kws.pop('engine', None)
        ibaow__oezz = kws.pop('engine_kwargs', None)
        hso__emaxk = dict(engine=cysvb__xnp, engine_kwargs=ibaow__oezz)
        bnbik__uqut = dict(engine=None, engine_kwargs=None)
        check_unsupported_args(f'Groupby.transform', hso__emaxk,
            bnbik__uqut, package_name='pandas', module_name='GroupBy')
    pdk__dks = {}
    for qbkuy__njl in grp.selection:
        out_columns.append(qbkuy__njl)
        pdk__dks[qbkuy__njl, name_operation] = qbkuy__njl
        zza__nfg = grp.df_type.columns.index(qbkuy__njl)
        data = grp.df_type.data[zza__nfg]
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
            ekzl__bvgq, err_msg = get_groupby_output_dtype(data,
                get_literal_value(wef__bzxk), grp.df_type.index)
            if err_msg == 'ok':
                data = ekzl__bvgq
            else:
                raise BodoError(
                    f'column type of {data.dtype} is not supported by {args[0]} yet.\n'
                    )
        out_data.append(data)
    if len(out_data) == 0:
        raise BodoError('No columns in output.')
    lxhg__epl = DataFrameType(tuple(out_data), index, tuple(out_columns))
    if len(grp.selection) == 1 and grp.series_select and grp.as_index:
        lxhg__epl = SeriesType(out_data[0].dtype, data=out_data[0], index=
            index, name_typ=types.StringLiteral(grp.selection[0]))
    return signature(lxhg__epl, *args), pdk__dks


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
        fdqlj__kyf = _get_groupby_apply_udf_out_type(func, grp, f_args, kws,
            self.context, numba.core.registry.cpu_target.target_context)
        yqg__dlwc = isinstance(fdqlj__kyf, (SeriesType,
            HeterogeneousSeriesType)
            ) and fdqlj__kyf.const_info is not None or not isinstance(
            fdqlj__kyf, (SeriesType, DataFrameType))
        if yqg__dlwc:
            out_data = []
            out_columns = []
            out_column_type = []
            if not grp.as_index:
                get_keys_not_as_index(grp, out_columns, out_data,
                    out_column_type)
                otd__uzi = NumericIndexType(types.int64, types.none)
            elif len(grp.keys) > 1:
                velmb__jpub = tuple(grp.df_type.columns.index(grp.keys[
                    vad__trzeb]) for vad__trzeb in range(len(grp.keys)))
                lmn__oshc = tuple(grp.df_type.data[zza__nfg] for zza__nfg in
                    velmb__jpub)
                lmn__oshc = tuple(to_str_arr_if_dict_array(bfjih__fjk) for
                    bfjih__fjk in lmn__oshc)
                otd__uzi = MultiIndexType(lmn__oshc, tuple(types.literal(
                    mwmgj__fmvni) for mwmgj__fmvni in grp.keys))
            else:
                zza__nfg = grp.df_type.columns.index(grp.keys[0])
                ktcpj__yfye = grp.df_type.data[zza__nfg]
                ktcpj__yfye = to_str_arr_if_dict_array(ktcpj__yfye)
                otd__uzi = bodo.hiframes.pd_index_ext.array_type_to_index(
                    ktcpj__yfye, types.literal(grp.keys[0]))
            out_data = tuple(out_data)
            out_columns = tuple(out_columns)
        else:
            ppa__xgq = tuple(grp.df_type.data[grp.df_type.columns.index(
                qbkuy__njl)] for qbkuy__njl in grp.keys)
            ppa__xgq = tuple(to_str_arr_if_dict_array(bfjih__fjk) for
                bfjih__fjk in ppa__xgq)
            qhta__hfdgw = tuple(types.literal(kks__uvgog) for kks__uvgog in
                grp.keys) + get_index_name_types(fdqlj__kyf.index)
            if not grp.as_index:
                ppa__xgq = types.Array(types.int64, 1, 'C'),
                qhta__hfdgw = (types.none,) + get_index_name_types(fdqlj__kyf
                    .index)
            otd__uzi = MultiIndexType(ppa__xgq + get_index_data_arr_types(
                fdqlj__kyf.index), qhta__hfdgw)
        if yqg__dlwc:
            if isinstance(fdqlj__kyf, HeterogeneousSeriesType):
                tkfai__meuz, mfei__zhgt = fdqlj__kyf.const_info
                qckuy__eam = tuple(dtype_to_array_type(bfjih__fjk) for
                    bfjih__fjk in fdqlj__kyf.data.types)
                wikmj__pzxcc = DataFrameType(out_data + qckuy__eam,
                    otd__uzi, out_columns + mfei__zhgt)
            elif isinstance(fdqlj__kyf, SeriesType):
                acebd__ffpno, mfei__zhgt = fdqlj__kyf.const_info
                qckuy__eam = tuple(dtype_to_array_type(fdqlj__kyf.dtype) for
                    tkfai__meuz in range(acebd__ffpno))
                wikmj__pzxcc = DataFrameType(out_data + qckuy__eam,
                    otd__uzi, out_columns + mfei__zhgt)
            else:
                geh__bfcfv = get_udf_out_arr_type(fdqlj__kyf)
                if not grp.as_index:
                    wikmj__pzxcc = DataFrameType(out_data + (geh__bfcfv,),
                        otd__uzi, out_columns + ('',))
                else:
                    wikmj__pzxcc = SeriesType(geh__bfcfv.dtype, geh__bfcfv,
                        otd__uzi, None)
        elif isinstance(fdqlj__kyf, SeriesType):
            wikmj__pzxcc = SeriesType(fdqlj__kyf.dtype, fdqlj__kyf.data,
                otd__uzi, fdqlj__kyf.name_typ)
        else:
            wikmj__pzxcc = DataFrameType(fdqlj__kyf.data, otd__uzi,
                fdqlj__kyf.columns)
        mjpbi__ismjh = gen_apply_pysig(len(f_args), kws.keys())
        lyr__bnts = (func, *f_args) + tuple(kws.values())
        return signature(wikmj__pzxcc, *lyr__bnts).replace(pysig=mjpbi__ismjh)

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
    xrr__qwsq = grp.df_type
    if grp.explicit_select:
        if len(grp.selection) == 1:
            mlj__bge = grp.selection[0]
            geh__bfcfv = xrr__qwsq.data[xrr__qwsq.columns.index(mlj__bge)]
            geh__bfcfv = to_str_arr_if_dict_array(geh__bfcfv)
            hty__bfga = SeriesType(geh__bfcfv.dtype, geh__bfcfv, xrr__qwsq.
                index, types.literal(mlj__bge))
        else:
            old__mqoum = tuple(xrr__qwsq.data[xrr__qwsq.columns.index(
                qbkuy__njl)] for qbkuy__njl in grp.selection)
            old__mqoum = tuple(to_str_arr_if_dict_array(bfjih__fjk) for
                bfjih__fjk in old__mqoum)
            hty__bfga = DataFrameType(old__mqoum, xrr__qwsq.index, tuple(
                grp.selection))
    else:
        hty__bfga = xrr__qwsq
    agtu__nii = hty__bfga,
    agtu__nii += tuple(f_args)
    try:
        fdqlj__kyf = get_const_func_output_type(func, agtu__nii, kws,
            typing_context, target_context)
    except Exception as zcq__kykl:
        raise_bodo_error(get_udf_error_msg('GroupBy.apply()', zcq__kykl),
            getattr(zcq__kykl, 'loc', None))
    return fdqlj__kyf


def resolve_obj_pipe(self, grp, args, kws, obj_name):
    kws = dict(kws)
    func = args[0] if len(args) > 0 else kws.pop('func', None)
    f_args = tuple(args[1:]) if len(args) > 0 else ()
    agtu__nii = (grp,) + f_args
    try:
        fdqlj__kyf = get_const_func_output_type(func, agtu__nii, kws, self.
            context, numba.core.registry.cpu_target.target_context, False)
    except Exception as zcq__kykl:
        raise_bodo_error(get_udf_error_msg(f'{obj_name}.pipe()', zcq__kykl),
            getattr(zcq__kykl, 'loc', None))
    mjpbi__ismjh = gen_apply_pysig(len(f_args), kws.keys())
    lyr__bnts = (func, *f_args) + tuple(kws.values())
    return signature(fdqlj__kyf, *lyr__bnts).replace(pysig=mjpbi__ismjh)


def gen_apply_pysig(n_args, kws):
    bhtl__fwkp = ', '.join(f'arg{vad__trzeb}' for vad__trzeb in range(n_args))
    bhtl__fwkp = bhtl__fwkp + ', ' if bhtl__fwkp else ''
    pmbki__mspqc = ', '.join(f"{yptfw__zbl} = ''" for yptfw__zbl in kws)
    xbbb__flmk = f'def apply_stub(func, {bhtl__fwkp}{pmbki__mspqc}):\n'
    xbbb__flmk += '    pass\n'
    sxqwk__sztu = {}
    exec(xbbb__flmk, {}, sxqwk__sztu)
    clfek__qyii = sxqwk__sztu['apply_stub']
    return numba.core.utils.pysignature(clfek__qyii)


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
        ekzl__bvgq = get_pivot_output_dtype(data, aggfunc.literal_value)
        qoz__gtf = dtype_to_array_type(ekzl__bvgq)
        if is_overload_none(_pivot_values):
            raise_bodo_error(
                'Dataframe.pivot_table() requires explicit annotation to determine output columns. For more information, see: https://docs.bodo.ai/latest/source/programming_with_bodo/pandas.html'
                )
        ydchl__wmsmr = _pivot_values.meta
        ffs__rvhbn = len(ydchl__wmsmr)
        zza__nfg = df.columns.index(index)
        ktcpj__yfye = df.data[zza__nfg]
        ktcpj__yfye = to_str_arr_if_dict_array(ktcpj__yfye)
        kab__beit = bodo.hiframes.pd_index_ext.array_type_to_index(ktcpj__yfye,
            types.StringLiteral(index))
        gqa__jdoa = DataFrameType((qoz__gtf,) * ffs__rvhbn, kab__beit,
            tuple(ydchl__wmsmr))
        return signature(gqa__jdoa, *args)


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
        qoz__gtf = types.Array(types.int64, 1, 'C')
        ydchl__wmsmr = _pivot_values.meta
        ffs__rvhbn = len(ydchl__wmsmr)
        kab__beit = bodo.hiframes.pd_index_ext.array_type_to_index(
            to_str_arr_if_dict_array(index.data), types.StringLiteral('index'))
        gqa__jdoa = DataFrameType((qoz__gtf,) * ffs__rvhbn, kab__beit,
            tuple(ydchl__wmsmr))
        return signature(gqa__jdoa, *args)


CrossTabTyper._no_unliteral = True


@lower_builtin(crosstab_dummy, types.VarArg(types.Any))
def lower_crosstab_dummy(context, builder, sig, args):
    return context.get_constant_null(sig.return_type)


def get_group_indices(keys, dropna, _is_parallel):
    return np.arange(len(keys))


@overload(get_group_indices)
def get_group_indices_overload(keys, dropna, _is_parallel):
    xbbb__flmk = 'def impl(keys, dropna, _is_parallel):\n'
    xbbb__flmk += (
        "    ev = bodo.utils.tracing.Event('get_group_indices', _is_parallel)\n"
        )
    xbbb__flmk += '    info_list = [{}]\n'.format(', '.join(
        f'array_to_info(keys[{vad__trzeb}])' for vad__trzeb in range(len(
        keys.types))))
    xbbb__flmk += '    table = arr_info_list_to_table(info_list)\n'
    xbbb__flmk += '    group_labels = np.empty(len(keys[0]), np.int64)\n'
    xbbb__flmk += '    sort_idx = np.empty(len(keys[0]), np.int64)\n'
    xbbb__flmk += """    ngroups = get_groupby_labels(table, group_labels.ctypes, sort_idx.ctypes, dropna, _is_parallel)
"""
    xbbb__flmk += '    delete_table_decref_arrays(table)\n'
    xbbb__flmk += '    ev.finalize()\n'
    xbbb__flmk += '    return sort_idx, group_labels, ngroups\n'
    sxqwk__sztu = {}
    exec(xbbb__flmk, {'bodo': bodo, 'np': np, 'get_groupby_labels':
        get_groupby_labels, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table,
        'delete_table_decref_arrays': delete_table_decref_arrays}, sxqwk__sztu)
    yxen__zxei = sxqwk__sztu['impl']
    return yxen__zxei


@numba.njit(no_cpython_wrapper=True)
def generate_slices(labels, ngroups):
    clyfp__zxt = len(labels)
    nwmzm__xlt = np.zeros(ngroups, dtype=np.int64)
    qpyja__ckx = np.zeros(ngroups, dtype=np.int64)
    yntq__coskr = 0
    crpa__rhyh = 0
    for vad__trzeb in range(clyfp__zxt):
        lsdjt__odc = labels[vad__trzeb]
        if lsdjt__odc < 0:
            yntq__coskr += 1
        else:
            crpa__rhyh += 1
            if vad__trzeb == clyfp__zxt - 1 or lsdjt__odc != labels[
                vad__trzeb + 1]:
                nwmzm__xlt[lsdjt__odc] = yntq__coskr
                qpyja__ckx[lsdjt__odc] = yntq__coskr + crpa__rhyh
                yntq__coskr += crpa__rhyh
                crpa__rhyh = 0
    return nwmzm__xlt, qpyja__ckx


def shuffle_dataframe(df, keys, _is_parallel):
    return df, keys, _is_parallel


@overload(shuffle_dataframe, prefer_literal=True)
def overload_shuffle_dataframe(df, keys, _is_parallel):
    yxen__zxei, tkfai__meuz = gen_shuffle_dataframe(df, keys, _is_parallel)
    return yxen__zxei


def gen_shuffle_dataframe(df, keys, _is_parallel):
    acebd__ffpno = len(df.columns)
    evg__kiqr = len(keys.types)
    assert is_overload_constant_bool(_is_parallel
        ), 'shuffle_dataframe: _is_parallel is not a constant'
    xbbb__flmk = 'def impl(df, keys, _is_parallel):\n'
    if is_overload_false(_is_parallel):
        xbbb__flmk += '  return df, keys, get_null_shuffle_info()\n'
        sxqwk__sztu = {}
        exec(xbbb__flmk, {'get_null_shuffle_info': get_null_shuffle_info},
            sxqwk__sztu)
        yxen__zxei = sxqwk__sztu['impl']
        return yxen__zxei
    for vad__trzeb in range(acebd__ffpno):
        xbbb__flmk += f"""  in_arr{vad__trzeb} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {vad__trzeb})
"""
    xbbb__flmk += f"""  in_index_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))
"""
    xbbb__flmk += '  info_list = [{}, {}, {}]\n'.format(', '.join(
        f'array_to_info(keys[{vad__trzeb}])' for vad__trzeb in range(
        evg__kiqr)), ', '.join(f'array_to_info(in_arr{vad__trzeb})' for
        vad__trzeb in range(acebd__ffpno)), 'array_to_info(in_index_arr)')
    xbbb__flmk += '  table = arr_info_list_to_table(info_list)\n'
    xbbb__flmk += (
        f'  out_table = shuffle_table(table, {evg__kiqr}, _is_parallel, 1)\n')
    for vad__trzeb in range(evg__kiqr):
        xbbb__flmk += f"""  out_key{vad__trzeb} = info_to_array(info_from_table(out_table, {vad__trzeb}), keys{vad__trzeb}_typ)
"""
    for vad__trzeb in range(acebd__ffpno):
        xbbb__flmk += f"""  out_arr{vad__trzeb} = info_to_array(info_from_table(out_table, {vad__trzeb + evg__kiqr}), in_arr{vad__trzeb}_typ)
"""
    xbbb__flmk += f"""  out_arr_index = info_to_array(info_from_table(out_table, {evg__kiqr + acebd__ffpno}), ind_arr_typ)
"""
    xbbb__flmk += '  shuffle_info = get_shuffle_info(out_table)\n'
    xbbb__flmk += '  delete_table(out_table)\n'
    xbbb__flmk += '  delete_table(table)\n'
    out_data = ', '.join(f'out_arr{vad__trzeb}' for vad__trzeb in range(
        acebd__ffpno))
    xbbb__flmk += (
        '  out_index = bodo.utils.conversion.index_from_array(out_arr_index)\n'
        )
    xbbb__flmk += f"""  out_df = bodo.hiframes.pd_dataframe_ext.init_dataframe(({out_data},), out_index, {gen_const_tup(df.columns)})
"""
    xbbb__flmk += '  return out_df, ({},), shuffle_info\n'.format(', '.join
        (f'out_key{vad__trzeb}' for vad__trzeb in range(evg__kiqr)))
    dxzac__oyyp = {'bodo': bodo, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'shuffle_table':
        shuffle_table, 'info_from_table': info_from_table, 'info_to_array':
        info_to_array, 'delete_table': delete_table, 'get_shuffle_info':
        get_shuffle_info, 'ind_arr_typ': types.Array(types.int64, 1, 'C') if
        isinstance(df.index, RangeIndexType) else df.index.data}
    dxzac__oyyp.update({f'keys{vad__trzeb}_typ': keys.types[vad__trzeb] for
        vad__trzeb in range(evg__kiqr)})
    dxzac__oyyp.update({f'in_arr{vad__trzeb}_typ': df.data[vad__trzeb] for
        vad__trzeb in range(acebd__ffpno)})
    sxqwk__sztu = {}
    exec(xbbb__flmk, dxzac__oyyp, sxqwk__sztu)
    yxen__zxei = sxqwk__sztu['impl']
    return yxen__zxei, dxzac__oyyp


def reverse_shuffle(data, shuffle_info):
    return data


@overload(reverse_shuffle)
def overload_reverse_shuffle(data, shuffle_info):
    if isinstance(data, bodo.hiframes.pd_multi_index_ext.MultiIndexType):
        iopp__fiai = len(data.array_types)
        xbbb__flmk = 'def impl(data, shuffle_info):\n'
        xbbb__flmk += '  info_list = [{}]\n'.format(', '.join(
            f'array_to_info(data._data[{vad__trzeb}])' for vad__trzeb in
            range(iopp__fiai)))
        xbbb__flmk += '  table = arr_info_list_to_table(info_list)\n'
        xbbb__flmk += (
            '  out_table = reverse_shuffle_table(table, shuffle_info)\n')
        for vad__trzeb in range(iopp__fiai):
            xbbb__flmk += f"""  out_arr{vad__trzeb} = info_to_array(info_from_table(out_table, {vad__trzeb}), data._data[{vad__trzeb}])
"""
        xbbb__flmk += '  delete_table(out_table)\n'
        xbbb__flmk += '  delete_table(table)\n'
        xbbb__flmk += (
            '  return init_multi_index(({},), data._names, data._name)\n'.
            format(', '.join(f'out_arr{vad__trzeb}' for vad__trzeb in range
            (iopp__fiai))))
        sxqwk__sztu = {}
        exec(xbbb__flmk, {'bodo': bodo, 'array_to_info': array_to_info,
            'arr_info_list_to_table': arr_info_list_to_table,
            'reverse_shuffle_table': reverse_shuffle_table,
            'info_from_table': info_from_table, 'info_to_array':
            info_to_array, 'delete_table': delete_table, 'init_multi_index':
            bodo.hiframes.pd_multi_index_ext.init_multi_index}, sxqwk__sztu)
        yxen__zxei = sxqwk__sztu['impl']
        return yxen__zxei
    if bodo.hiframes.pd_index_ext.is_index_type(data):

        def impl_index(data, shuffle_info):
            llk__fhz = bodo.utils.conversion.index_to_array(data)
            vuv__dcus = reverse_shuffle(llk__fhz, shuffle_info)
            return bodo.utils.conversion.index_from_array(vuv__dcus)
        return impl_index

    def impl_arr(data, shuffle_info):
        fke__fdt = [array_to_info(data)]
        fmoh__qgik = arr_info_list_to_table(fke__fdt)
        krsnh__rald = reverse_shuffle_table(fmoh__qgik, shuffle_info)
        vuv__dcus = info_to_array(info_from_table(krsnh__rald, 0), data)
        delete_table(krsnh__rald)
        delete_table(fmoh__qgik)
        return vuv__dcus
    return impl_arr


@overload_method(DataFrameGroupByType, 'value_counts', inline='always',
    no_unliteral=True)
def groupby_value_counts(grp, normalize=False, sort=True, ascending=False,
    bins=None, dropna=True):
    hso__emaxk = dict(normalize=normalize, sort=sort, bins=bins, dropna=dropna)
    bnbik__uqut = dict(normalize=False, sort=True, bins=None, dropna=True)
    check_unsupported_args('Groupby.value_counts', hso__emaxk, bnbik__uqut,
        package_name='pandas', module_name='GroupBy')
    if len(grp.selection) > 1 or not grp.as_index:
        raise BodoError(
            "'DataFrameGroupBy' object has no attribute 'value_counts'")
    if not is_overload_constant_bool(ascending):
        raise BodoError(
            'Groupby.value_counts() ascending must be a constant boolean')
    atjs__jsxw = get_overload_const_bool(ascending)
    tous__dlwk = grp.selection[0]
    xbbb__flmk = f"""def impl(grp, normalize=False, sort=True, ascending=False, bins=None, dropna=True):
"""
    jpg__jdfqz = (
        f"lambda S: S.value_counts(ascending={atjs__jsxw}, _index_name='{tous__dlwk}')"
        )
    xbbb__flmk += f'    return grp.apply({jpg__jdfqz})\n'
    sxqwk__sztu = {}
    exec(xbbb__flmk, {'bodo': bodo}, sxqwk__sztu)
    yxen__zxei = sxqwk__sztu['impl']
    return yxen__zxei


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


def _install_groupy_unsupported():
    for zbl__uav in groupby_unsupported_attr:
        overload_attribute(DataFrameGroupByType, zbl__uav, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{zbl__uav}'))
    for zbl__uav in groupby_unsupported:
        overload_method(DataFrameGroupByType, zbl__uav, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{zbl__uav}'))
    for zbl__uav in series_only_unsupported_attrs:
        overload_attribute(DataFrameGroupByType, zbl__uav, no_unliteral=True)(
            create_unsupported_overload(f'SeriesGroupBy.{zbl__uav}'))
    for zbl__uav in series_only_unsupported:
        overload_method(DataFrameGroupByType, zbl__uav, no_unliteral=True)(
            create_unsupported_overload(f'SeriesGroupBy.{zbl__uav}'))
    for zbl__uav in dataframe_only_unsupported:
        overload_method(DataFrameGroupByType, zbl__uav, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{zbl__uav}'))


_install_groupy_unsupported()
