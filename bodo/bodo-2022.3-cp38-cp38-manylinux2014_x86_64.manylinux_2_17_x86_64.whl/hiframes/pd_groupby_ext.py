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
        lcrj__yyja = [('obj', fe_type.df_type)]
        super(GroupbyModel, self).__init__(dmm, fe_type, lcrj__yyja)


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
        eolqb__fygt = args[0]
        gdqtr__qojab = signature.return_type
        dekii__jqzty = cgutils.create_struct_proxy(gdqtr__qojab)(context,
            builder)
        dekii__jqzty.obj = eolqb__fygt
        context.nrt.incref(builder, signature.args[0], eolqb__fygt)
        return dekii__jqzty._getvalue()
    if is_overload_constant_list(by_type):
        keys = tuple(get_overload_const_list(by_type))
    elif is_literal_type(by_type):
        keys = get_literal_value(by_type),
    else:
        assert False, 'Reached unreachable code in init_groupby; there is an validate_groupby_spec'
    selection = list(obj_type.columns)
    for ifwd__mwzp in keys:
        selection.remove(ifwd__mwzp)
    if is_overload_constant_bool(as_index_type):
        as_index = is_overload_true(as_index_type)
    else:
        as_index = True
    if is_overload_constant_bool(dropna_type):
        dropna = is_overload_true(dropna_type)
    else:
        dropna = True
    gdqtr__qojab = DataFrameGroupByType(obj_type, keys, tuple(selection),
        as_index, dropna, False)
    return gdqtr__qojab(obj_type, by_type, as_index_type, dropna_type), codegen


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
        grpby, tgzw__pexb = args
        if isinstance(grpby, DataFrameGroupByType):
            series_select = False
            if isinstance(tgzw__pexb, (tuple, list)):
                if len(set(tgzw__pexb).difference(set(grpby.df_type.columns))
                    ) > 0:
                    raise_bodo_error(
                        'groupby: selected column {} not found in dataframe'
                        .format(set(tgzw__pexb).difference(set(grpby.
                        df_type.columns))))
                selection = tgzw__pexb
            else:
                if tgzw__pexb not in grpby.df_type.columns:
                    raise_bodo_error(
                        'groupby: selected column {} not found in dataframe'
                        .format(tgzw__pexb))
                selection = tgzw__pexb,
                series_select = True
            iphqn__ubgf = DataFrameGroupByType(grpby.df_type, grpby.keys,
                selection, grpby.as_index, grpby.dropna, True, series_select)
            return signature(iphqn__ubgf, *args)


@infer_global(operator.getitem)
class GetItemDataFrameGroupBy(AbstractTemplate):

    def generic(self, args, kws):
        grpby, tgzw__pexb = args
        if isinstance(grpby, DataFrameGroupByType) and is_literal_type(
            tgzw__pexb):
            iphqn__ubgf = StaticGetItemDataFrameGroupBy.generic(self, (
                grpby, get_literal_value(tgzw__pexb)), {}).return_type
            return signature(iphqn__ubgf, *args)


GetItemDataFrameGroupBy.prefer_literal = True


@lower_builtin('static_getitem', DataFrameGroupByType, types.Any)
@lower_builtin(operator.getitem, DataFrameGroupByType, types.Any)
def static_getitem_df_groupby(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


def get_groupby_output_dtype(arr_type, func_name, index_type=None):
    arr_type = to_str_arr_if_dict_array(arr_type)
    wdo__kyagq = arr_type == ArrayItemArrayType(string_array_type)
    wscyn__psp = arr_type.dtype
    if isinstance(wscyn__psp, bodo.hiframes.datetime_timedelta_ext.
        DatetimeTimeDeltaType):
        raise BodoError(
            f"""column type of {wscyn__psp} is not supported in groupby built-in function {func_name}.
{dt_err}"""
            )
    if func_name == 'median' and not isinstance(wscyn__psp, (Decimal128Type,
        types.Float, types.Integer)):
        return (None,
            'For median, only column of integer, float or Decimal type are allowed'
            )
    if func_name in ('first', 'last', 'sum', 'prod', 'min', 'max', 'count',
        'nunique', 'head') and isinstance(arr_type, (TupleArrayType,
        ArrayItemArrayType)):
        return (None,
            f'column type of list/tuple of {wscyn__psp} is not supported in groupby built-in function {func_name}'
            )
    if func_name in {'median', 'mean', 'var', 'std'} and isinstance(wscyn__psp,
        (Decimal128Type, types.Integer, types.Float)):
        return dtype_to_array_type(types.float64), 'ok'
    if not isinstance(wscyn__psp, (types.Integer, types.Float, types.Boolean)):
        if wdo__kyagq or wscyn__psp == types.unicode_type:
            if func_name not in {'count', 'nunique', 'min', 'max', 'sum',
                'first', 'last', 'head'}:
                return (None,
                    f'column type of strings or list of strings is not supported in groupby built-in function {func_name}'
                    )
        else:
            if isinstance(wscyn__psp, bodo.PDCategoricalDtype):
                if func_name in ('min', 'max') and not wscyn__psp.ordered:
                    return (None,
                        f'categorical column must be ordered in groupby built-in function {func_name}'
                        )
            if func_name not in {'count', 'nunique', 'min', 'max', 'first',
                'last', 'head'}:
                return (None,
                    f'column type of {wscyn__psp} is not supported in groupby built-in function {func_name}'
                    )
    if isinstance(wscyn__psp, types.Boolean) and func_name in {'cumsum',
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
    wscyn__psp = arr_type.dtype
    if func_name in {'count'}:
        return IntDtype(types.int64)
    if func_name in {'sum', 'prod', 'min', 'max'}:
        if func_name in {'sum', 'prod'} and not isinstance(wscyn__psp, (
            types.Integer, types.Float)):
            raise BodoError(
                'pivot_table(): sum and prod operations require integer or float input'
                )
        if isinstance(wscyn__psp, types.Integer):
            return IntDtype(wscyn__psp)
        return wscyn__psp
    if func_name in {'mean', 'var', 'std'}:
        return types.float64
    raise BodoError('invalid pivot operation')


def check_args_kwargs(func_name, len_args, args, kws):
    if len(kws) > 0:
        vex__saj = list(kws.keys())[0]
        raise BodoError(
            f"Groupby.{func_name}() got an unexpected keyword argument '{vex__saj}'."
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
    for ifwd__mwzp in grp.keys:
        if multi_level_names:
            nzv__rlsya = ifwd__mwzp, ''
        else:
            nzv__rlsya = ifwd__mwzp
        hwhbr__wqc = grp.df_type.columns.index(ifwd__mwzp)
        data = to_str_arr_if_dict_array(grp.df_type.data[hwhbr__wqc])
        out_columns.append(nzv__rlsya)
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
        rqcne__gzj = tuple(grp.df_type.columns.index(grp.keys[fuwca__qlhpz]
            ) for fuwca__qlhpz in range(len(grp.keys)))
        zam__npnn = tuple(grp.df_type.data[hwhbr__wqc] for hwhbr__wqc in
            rqcne__gzj)
        zam__npnn = tuple(to_str_arr_if_dict_array(mse__nivkj) for
            mse__nivkj in zam__npnn)
        index = MultiIndexType(zam__npnn, tuple(types.StringLiteral(
            ifwd__mwzp) for ifwd__mwzp in grp.keys))
    else:
        hwhbr__wqc = grp.df_type.columns.index(grp.keys[0])
        anods__loo = to_str_arr_if_dict_array(grp.df_type.data[hwhbr__wqc])
        index = bodo.hiframes.pd_index_ext.array_type_to_index(anods__loo,
            types.StringLiteral(grp.keys[0]))
    woztv__uofsw = {}
    hcs__kue = []
    if func_name in ('size', 'count'):
        kws = dict(kws) if kws else {}
        check_args_kwargs(func_name, 0, args, kws)
    if func_name == 'size':
        out_data.append(types.Array(types.int64, 1, 'C'))
        out_columns.append('size')
        woztv__uofsw[None, 'size'] = 'size'
    else:
        columns = (grp.selection if func_name != 'head' or grp.
            explicit_select else grp.df_type.columns)
        for ljlin__zxy in columns:
            hwhbr__wqc = grp.df_type.columns.index(ljlin__zxy)
            data = grp.df_type.data[hwhbr__wqc]
            data = to_str_arr_if_dict_array(data)
            xby__slsf = ColumnType.NonNumericalColumn.value
            if isinstance(data, (types.Array, IntegerArrayType)
                ) and isinstance(data.dtype, (types.Integer, types.Float)):
                xby__slsf = ColumnType.NumericalColumn.value
            if func_name == 'agg':
                try:
                    semn__uurct = SeriesType(data.dtype, data, None,
                        string_type)
                    koc__bpv = get_const_func_output_type(func, (
                        semn__uurct,), {}, typing_context, target_context)
                    if koc__bpv != ArrayItemArrayType(string_array_type):
                        koc__bpv = dtype_to_array_type(koc__bpv)
                    err_msg = 'ok'
                except:
                    raise_bodo_error(
                        'Groupy.agg()/Groupy.aggregate(): column {col} of type {type} is unsupported/not a valid input type for user defined function'
                        .format(col=ljlin__zxy, type=data.dtype))
            else:
                if func_name in ('first', 'last', 'min', 'max'):
                    kws = dict(kws) if kws else {}
                    ooacq__rkg = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', False)
                    mbm__liyy = args[1] if len(args) > 1 else kws.pop(
                        'min_count', -1)
                    hqsy__mebat = dict(numeric_only=ooacq__rkg, min_count=
                        mbm__liyy)
                    iturp__gdrna = dict(numeric_only=False, min_count=-1)
                    check_unsupported_args(f'Groupby.{func_name}',
                        hqsy__mebat, iturp__gdrna, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('sum', 'prod'):
                    kws = dict(kws) if kws else {}
                    ooacq__rkg = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', True)
                    mbm__liyy = args[1] if len(args) > 1 else kws.pop(
                        'min_count', 0)
                    hqsy__mebat = dict(numeric_only=ooacq__rkg, min_count=
                        mbm__liyy)
                    iturp__gdrna = dict(numeric_only=True, min_count=0)
                    check_unsupported_args(f'Groupby.{func_name}',
                        hqsy__mebat, iturp__gdrna, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('mean', 'median'):
                    kws = dict(kws) if kws else {}
                    ooacq__rkg = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', True)
                    hqsy__mebat = dict(numeric_only=ooacq__rkg)
                    iturp__gdrna = dict(numeric_only=True)
                    check_unsupported_args(f'Groupby.{func_name}',
                        hqsy__mebat, iturp__gdrna, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('idxmin', 'idxmax'):
                    kws = dict(kws) if kws else {}
                    rcb__nnz = args[0] if len(args) > 0 else kws.pop('axis', 0)
                    vkv__bcgh = args[1] if len(args) > 1 else kws.pop('skipna',
                        True)
                    hqsy__mebat = dict(axis=rcb__nnz, skipna=vkv__bcgh)
                    iturp__gdrna = dict(axis=0, skipna=True)
                    check_unsupported_args(f'Groupby.{func_name}',
                        hqsy__mebat, iturp__gdrna, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('var', 'std'):
                    kws = dict(kws) if kws else {}
                    qfk__hmxu = args[0] if len(args) > 0 else kws.pop('ddof', 1
                        )
                    hqsy__mebat = dict(ddof=qfk__hmxu)
                    iturp__gdrna = dict(ddof=1)
                    check_unsupported_args(f'Groupby.{func_name}',
                        hqsy__mebat, iturp__gdrna, package_name='pandas',
                        module_name='GroupBy')
                elif func_name == 'nunique':
                    kws = dict(kws) if kws else {}
                    dropna = args[0] if len(args) > 0 else kws.pop('dropna', 1)
                    check_args_kwargs(func_name, 1, args, kws)
                elif func_name == 'head':
                    if len(args) == 0:
                        kws.pop('n', None)
                koc__bpv, err_msg = get_groupby_output_dtype(data,
                    func_name, grp.df_type.index)
            if err_msg == 'ok':
                bpjh__mvakw = to_str_arr_if_dict_array(koc__bpv)
                out_data.append(bpjh__mvakw)
                out_columns.append(ljlin__zxy)
                if func_name == 'agg':
                    fkegd__akrol = bodo.ir.aggregate._get_udf_name(bodo.ir.
                        aggregate._get_const_agg_func(func, None))
                    woztv__uofsw[ljlin__zxy, fkegd__akrol] = ljlin__zxy
                else:
                    woztv__uofsw[ljlin__zxy, func_name] = ljlin__zxy
                out_column_type.append(xby__slsf)
            else:
                hcs__kue.append(err_msg)
    if func_name == 'sum':
        elu__zgl = any([(buab__ksr == ColumnType.NumericalColumn.value) for
            buab__ksr in out_column_type])
        if elu__zgl:
            out_data = [buab__ksr for buab__ksr, lfyp__qweev in zip(
                out_data, out_column_type) if lfyp__qweev != ColumnType.
                NonNumericalColumn.value]
            out_columns = [buab__ksr for buab__ksr, lfyp__qweev in zip(
                out_columns, out_column_type) if lfyp__qweev != ColumnType.
                NonNumericalColumn.value]
            woztv__uofsw = {}
            for ljlin__zxy in out_columns:
                if grp.as_index is False and ljlin__zxy in grp.keys:
                    continue
                woztv__uofsw[ljlin__zxy, func_name] = ljlin__zxy
    puilu__rilpy = len(hcs__kue)
    if len(out_data) == 0:
        if puilu__rilpy == 0:
            raise BodoError('No columns in output.')
        else:
            raise BodoError(
                'No columns in output. {} column{} dropped for following reasons: {}'
                .format(puilu__rilpy, ' was' if puilu__rilpy == 1 else
                's were', ','.join(hcs__kue)))
    kkss__wqss = DataFrameType(tuple(out_data), index, tuple(out_columns))
    if (len(grp.selection) == 1 and grp.series_select and grp.as_index or 
        func_name == 'size' and grp.as_index):
        if isinstance(out_data[0], IntegerArrayType):
            sgqb__wxu = IntDtype(out_data[0].dtype)
        else:
            sgqb__wxu = out_data[0].dtype
        iuxie__tpmt = (types.none if func_name == 'size' else types.
            StringLiteral(grp.selection[0]))
        kkss__wqss = SeriesType(sgqb__wxu, index=index, name_typ=iuxie__tpmt)
    return signature(kkss__wqss, *args), woztv__uofsw


def get_agg_funcname_and_outtyp(grp, col, f_val, typing_context, target_context
    ):
    vrk__zaqym = True
    if isinstance(f_val, str):
        vrk__zaqym = False
        bxnbi__xuxn = f_val
    elif is_overload_constant_str(f_val):
        vrk__zaqym = False
        bxnbi__xuxn = get_overload_const_str(f_val)
    elif bodo.utils.typing.is_builtin_function(f_val):
        vrk__zaqym = False
        bxnbi__xuxn = bodo.utils.typing.get_builtin_function_name(f_val)
    if not vrk__zaqym:
        if bxnbi__xuxn not in bodo.ir.aggregate.supported_agg_funcs[:-1]:
            raise BodoError(f'unsupported aggregate function {bxnbi__xuxn}')
        iphqn__ubgf = DataFrameGroupByType(grp.df_type, grp.keys, (col,),
            grp.as_index, grp.dropna, True, True)
        out_tp = get_agg_typ(iphqn__ubgf, (), bxnbi__xuxn, typing_context,
            target_context)[0].return_type
    else:
        if is_expr(f_val, 'make_function'):
            hwswc__ujv = types.functions.MakeFunctionLiteral(f_val)
        else:
            hwswc__ujv = f_val
        validate_udf('agg', hwswc__ujv)
        func = get_overload_const_func(hwswc__ujv, None)
        koax__kql = func.code if hasattr(func, 'code') else func.__code__
        bxnbi__xuxn = koax__kql.co_name
        iphqn__ubgf = DataFrameGroupByType(grp.df_type, grp.keys, (col,),
            grp.as_index, grp.dropna, True, True)
        out_tp = get_agg_typ(iphqn__ubgf, (), 'agg', typing_context,
            target_context, hwswc__ujv)[0].return_type
    return bxnbi__xuxn, out_tp


def resolve_agg(grp, args, kws, typing_context, target_context):
    func = get_call_expr_arg('agg', args, dict(kws), 0, 'func', default=
        types.none)
    buxmn__blfbe = kws and all(isinstance(vbdgh__nwxqz, types.Tuple) and 
        len(vbdgh__nwxqz) == 2 for vbdgh__nwxqz in kws.values())
    if is_overload_none(func) and not buxmn__blfbe:
        raise_bodo_error("Groupby.agg()/aggregate(): Must provide 'func'")
    if len(args) > 1 or kws and not buxmn__blfbe:
        raise_bodo_error(
            'Groupby.agg()/aggregate(): passing extra arguments to functions not supported yet.'
            )
    opo__cwti = False

    def _append_out_type(grp, out_data, out_tp):
        if grp.as_index is False:
            out_data.append(out_tp.data[len(grp.keys)])
        else:
            out_data.append(out_tp.data)
    if buxmn__blfbe or is_overload_constant_dict(func):
        if buxmn__blfbe:
            txplw__mfx = [get_literal_value(nmxbv__jau) for nmxbv__jau,
                wuvy__odrx in kws.values()]
            tgzt__gvr = [get_literal_value(hvjs__uvcql) for wuvy__odrx,
                hvjs__uvcql in kws.values()]
        else:
            covye__fynku = get_overload_constant_dict(func)
            txplw__mfx = tuple(covye__fynku.keys())
            tgzt__gvr = tuple(covye__fynku.values())
        if 'head' in tgzt__gvr:
            raise BodoError(
                'Groupby.agg()/aggregate(): head cannot be mixed with other groupby operations.'
                )
        if any(ljlin__zxy not in grp.selection and ljlin__zxy not in grp.
            keys for ljlin__zxy in txplw__mfx):
            raise_bodo_error(
                f'Selected column names {txplw__mfx} not all available in dataframe column names {grp.selection}'
                )
        multi_level_names = any(isinstance(f_val, (tuple, list)) for f_val in
            tgzt__gvr)
        if buxmn__blfbe and multi_level_names:
            raise_bodo_error(
                'Groupby.agg()/aggregate(): cannot pass multiple functions in a single pd.NamedAgg()'
                )
        woztv__uofsw = {}
        out_columns = []
        out_data = []
        out_column_type = []
        vdl__fkd = []
        if not grp.as_index:
            get_keys_not_as_index(grp, out_columns, out_data,
                out_column_type, multi_level_names=multi_level_names)
        for rso__qwghz, f_val in zip(txplw__mfx, tgzt__gvr):
            if isinstance(f_val, (tuple, list)):
                lbvdl__pfoo = 0
                for hwswc__ujv in f_val:
                    bxnbi__xuxn, out_tp = get_agg_funcname_and_outtyp(grp,
                        rso__qwghz, hwswc__ujv, typing_context, target_context)
                    opo__cwti = bxnbi__xuxn in list_cumulative
                    if bxnbi__xuxn == '<lambda>' and len(f_val) > 1:
                        bxnbi__xuxn = '<lambda_' + str(lbvdl__pfoo) + '>'
                        lbvdl__pfoo += 1
                    out_columns.append((rso__qwghz, bxnbi__xuxn))
                    woztv__uofsw[rso__qwghz, bxnbi__xuxn
                        ] = rso__qwghz, bxnbi__xuxn
                    _append_out_type(grp, out_data, out_tp)
            else:
                bxnbi__xuxn, out_tp = get_agg_funcname_and_outtyp(grp,
                    rso__qwghz, f_val, typing_context, target_context)
                opo__cwti = bxnbi__xuxn in list_cumulative
                if multi_level_names:
                    out_columns.append((rso__qwghz, bxnbi__xuxn))
                    woztv__uofsw[rso__qwghz, bxnbi__xuxn
                        ] = rso__qwghz, bxnbi__xuxn
                elif not buxmn__blfbe:
                    out_columns.append(rso__qwghz)
                    woztv__uofsw[rso__qwghz, bxnbi__xuxn] = rso__qwghz
                elif buxmn__blfbe:
                    vdl__fkd.append(bxnbi__xuxn)
                _append_out_type(grp, out_data, out_tp)
        if buxmn__blfbe:
            for fuwca__qlhpz, tigux__htus in enumerate(kws.keys()):
                out_columns.append(tigux__htus)
                woztv__uofsw[txplw__mfx[fuwca__qlhpz], vdl__fkd[fuwca__qlhpz]
                    ] = tigux__htus
        if opo__cwti:
            index = grp.df_type.index
        else:
            index = out_tp.index
        kkss__wqss = DataFrameType(tuple(out_data), index, tuple(out_columns))
        return signature(kkss__wqss, *args), woztv__uofsw
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
        lbvdl__pfoo = 0
        if not grp.as_index:
            get_keys_not_as_index(grp, out_columns, out_data, out_column_type)
        woztv__uofsw = {}
        zwepy__xtown = grp.selection[0]
        for f_val in func.types:
            bxnbi__xuxn, out_tp = get_agg_funcname_and_outtyp(grp,
                zwepy__xtown, f_val, typing_context, target_context)
            opo__cwti = bxnbi__xuxn in list_cumulative
            if bxnbi__xuxn == '<lambda>':
                bxnbi__xuxn = '<lambda_' + str(lbvdl__pfoo) + '>'
                lbvdl__pfoo += 1
            out_columns.append(bxnbi__xuxn)
            woztv__uofsw[zwepy__xtown, bxnbi__xuxn] = bxnbi__xuxn
            _append_out_type(grp, out_data, out_tp)
        if opo__cwti:
            index = grp.df_type.index
        else:
            index = out_tp.index
        kkss__wqss = DataFrameType(tuple(out_data), index, tuple(out_columns))
        return signature(kkss__wqss, *args), woztv__uofsw
    bxnbi__xuxn = ''
    if types.unliteral(func) == types.unicode_type:
        bxnbi__xuxn = get_overload_const_str(func)
    if bodo.utils.typing.is_builtin_function(func):
        bxnbi__xuxn = bodo.utils.typing.get_builtin_function_name(func)
    if bxnbi__xuxn:
        args = args[1:]
        kws.pop('func', None)
        return get_agg_typ(grp, args, bxnbi__xuxn, typing_context, kws)
    validate_udf('agg', func)
    return get_agg_typ(grp, args, 'agg', typing_context, target_context, func)


def resolve_transformative(grp, args, kws, msg, name_operation):
    index = grp.df_type.index
    out_columns = []
    out_data = []
    if name_operation in list_cumulative:
        kws = dict(kws) if kws else {}
        rcb__nnz = args[0] if len(args) > 0 else kws.pop('axis', 0)
        ooacq__rkg = args[1] if len(args) > 1 else kws.pop('numeric_only', 
            False)
        vkv__bcgh = args[2] if len(args) > 2 else kws.pop('skipna', 1)
        hqsy__mebat = dict(axis=rcb__nnz, numeric_only=ooacq__rkg)
        iturp__gdrna = dict(axis=0, numeric_only=False)
        check_unsupported_args(f'Groupby.{name_operation}', hqsy__mebat,
            iturp__gdrna, package_name='pandas', module_name='GroupBy')
        check_args_kwargs(name_operation, 3, args, kws)
    elif name_operation == 'shift':
        lsqd__uiubz = args[0] if len(args) > 0 else kws.pop('periods', 1)
        sfb__fcwpe = args[1] if len(args) > 1 else kws.pop('freq', None)
        rcb__nnz = args[2] if len(args) > 2 else kws.pop('axis', 0)
        cma__ycicp = args[3] if len(args) > 3 else kws.pop('fill_value', None)
        hqsy__mebat = dict(freq=sfb__fcwpe, axis=rcb__nnz, fill_value=
            cma__ycicp)
        iturp__gdrna = dict(freq=None, axis=0, fill_value=None)
        check_unsupported_args(f'Groupby.{name_operation}', hqsy__mebat,
            iturp__gdrna, package_name='pandas', module_name='GroupBy')
        check_args_kwargs(name_operation, 4, args, kws)
    elif name_operation == 'transform':
        kws = dict(kws)
        lsb__qjvks = args[0] if len(args) > 0 else kws.pop('func', None)
        rpqad__qbgkk = kws.pop('engine', None)
        fml__yxtsd = kws.pop('engine_kwargs', None)
        hqsy__mebat = dict(engine=rpqad__qbgkk, engine_kwargs=fml__yxtsd)
        iturp__gdrna = dict(engine=None, engine_kwargs=None)
        check_unsupported_args(f'Groupby.transform', hqsy__mebat,
            iturp__gdrna, package_name='pandas', module_name='GroupBy')
    woztv__uofsw = {}
    for ljlin__zxy in grp.selection:
        out_columns.append(ljlin__zxy)
        woztv__uofsw[ljlin__zxy, name_operation] = ljlin__zxy
        hwhbr__wqc = grp.df_type.columns.index(ljlin__zxy)
        data = grp.df_type.data[hwhbr__wqc]
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
            koc__bpv, err_msg = get_groupby_output_dtype(data,
                get_literal_value(lsb__qjvks), grp.df_type.index)
            if err_msg == 'ok':
                data = koc__bpv
            else:
                raise BodoError(
                    f'column type of {data.dtype} is not supported by {args[0]} yet.\n'
                    )
        out_data.append(data)
    if len(out_data) == 0:
        raise BodoError('No columns in output.')
    kkss__wqss = DataFrameType(tuple(out_data), index, tuple(out_columns))
    if len(grp.selection) == 1 and grp.series_select and grp.as_index:
        kkss__wqss = SeriesType(out_data[0].dtype, data=out_data[0], index=
            index, name_typ=types.StringLiteral(grp.selection[0]))
    return signature(kkss__wqss, *args), woztv__uofsw


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
        kwimf__nokz = _get_groupby_apply_udf_out_type(func, grp, f_args,
            kws, self.context, numba.core.registry.cpu_target.target_context)
        nkz__fhwrv = isinstance(kwimf__nokz, (SeriesType,
            HeterogeneousSeriesType)
            ) and kwimf__nokz.const_info is not None or not isinstance(
            kwimf__nokz, (SeriesType, DataFrameType))
        if nkz__fhwrv:
            out_data = []
            out_columns = []
            out_column_type = []
            if not grp.as_index:
                get_keys_not_as_index(grp, out_columns, out_data,
                    out_column_type)
                rdcm__agfj = NumericIndexType(types.int64, types.none)
            elif len(grp.keys) > 1:
                rqcne__gzj = tuple(grp.df_type.columns.index(grp.keys[
                    fuwca__qlhpz]) for fuwca__qlhpz in range(len(grp.keys)))
                zam__npnn = tuple(grp.df_type.data[hwhbr__wqc] for
                    hwhbr__wqc in rqcne__gzj)
                zam__npnn = tuple(to_str_arr_if_dict_array(mse__nivkj) for
                    mse__nivkj in zam__npnn)
                rdcm__agfj = MultiIndexType(zam__npnn, tuple(types.literal(
                    ifwd__mwzp) for ifwd__mwzp in grp.keys))
            else:
                hwhbr__wqc = grp.df_type.columns.index(grp.keys[0])
                anods__loo = grp.df_type.data[hwhbr__wqc]
                anods__loo = to_str_arr_if_dict_array(anods__loo)
                rdcm__agfj = bodo.hiframes.pd_index_ext.array_type_to_index(
                    anods__loo, types.literal(grp.keys[0]))
            out_data = tuple(out_data)
            out_columns = tuple(out_columns)
        else:
            ntj__xvfj = tuple(grp.df_type.data[grp.df_type.columns.index(
                ljlin__zxy)] for ljlin__zxy in grp.keys)
            ntj__xvfj = tuple(to_str_arr_if_dict_array(mse__nivkj) for
                mse__nivkj in ntj__xvfj)
            rmczm__qwcxb = tuple(types.literal(vbdgh__nwxqz) for
                vbdgh__nwxqz in grp.keys) + get_index_name_types(kwimf__nokz
                .index)
            if not grp.as_index:
                ntj__xvfj = types.Array(types.int64, 1, 'C'),
                rmczm__qwcxb = (types.none,) + get_index_name_types(kwimf__nokz
                    .index)
            rdcm__agfj = MultiIndexType(ntj__xvfj +
                get_index_data_arr_types(kwimf__nokz.index), rmczm__qwcxb)
        if nkz__fhwrv:
            if isinstance(kwimf__nokz, HeterogeneousSeriesType):
                wuvy__odrx, ukorr__yau = kwimf__nokz.const_info
                meyje__lro = tuple(dtype_to_array_type(mse__nivkj) for
                    mse__nivkj in kwimf__nokz.data.types)
                yez__nqvtf = DataFrameType(out_data + meyje__lro,
                    rdcm__agfj, out_columns + ukorr__yau)
            elif isinstance(kwimf__nokz, SeriesType):
                goo__rvr, ukorr__yau = kwimf__nokz.const_info
                meyje__lro = tuple(dtype_to_array_type(kwimf__nokz.dtype) for
                    wuvy__odrx in range(goo__rvr))
                yez__nqvtf = DataFrameType(out_data + meyje__lro,
                    rdcm__agfj, out_columns + ukorr__yau)
            else:
                tvp__mnn = get_udf_out_arr_type(kwimf__nokz)
                if not grp.as_index:
                    yez__nqvtf = DataFrameType(out_data + (tvp__mnn,),
                        rdcm__agfj, out_columns + ('',))
                else:
                    yez__nqvtf = SeriesType(tvp__mnn.dtype, tvp__mnn,
                        rdcm__agfj, None)
        elif isinstance(kwimf__nokz, SeriesType):
            yez__nqvtf = SeriesType(kwimf__nokz.dtype, kwimf__nokz.data,
                rdcm__agfj, kwimf__nokz.name_typ)
        else:
            yez__nqvtf = DataFrameType(kwimf__nokz.data, rdcm__agfj,
                kwimf__nokz.columns)
        pvhp__ysn = gen_apply_pysig(len(f_args), kws.keys())
        irwti__ilay = (func, *f_args) + tuple(kws.values())
        return signature(yez__nqvtf, *irwti__ilay).replace(pysig=pvhp__ysn)

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
    lrnk__toawl = grp.df_type
    if grp.explicit_select:
        if len(grp.selection) == 1:
            rso__qwghz = grp.selection[0]
            tvp__mnn = lrnk__toawl.data[lrnk__toawl.columns.index(rso__qwghz)]
            tvp__mnn = to_str_arr_if_dict_array(tvp__mnn)
            pyu__dxfi = SeriesType(tvp__mnn.dtype, tvp__mnn, lrnk__toawl.
                index, types.literal(rso__qwghz))
        else:
            snils__hfl = tuple(lrnk__toawl.data[lrnk__toawl.columns.index(
                ljlin__zxy)] for ljlin__zxy in grp.selection)
            snils__hfl = tuple(to_str_arr_if_dict_array(mse__nivkj) for
                mse__nivkj in snils__hfl)
            pyu__dxfi = DataFrameType(snils__hfl, lrnk__toawl.index, tuple(
                grp.selection))
    else:
        pyu__dxfi = lrnk__toawl
    ovobb__lap = pyu__dxfi,
    ovobb__lap += tuple(f_args)
    try:
        kwimf__nokz = get_const_func_output_type(func, ovobb__lap, kws,
            typing_context, target_context)
    except Exception as fojla__ocm:
        raise_bodo_error(get_udf_error_msg('GroupBy.apply()', fojla__ocm),
            getattr(fojla__ocm, 'loc', None))
    return kwimf__nokz


def resolve_obj_pipe(self, grp, args, kws, obj_name):
    kws = dict(kws)
    func = args[0] if len(args) > 0 else kws.pop('func', None)
    f_args = tuple(args[1:]) if len(args) > 0 else ()
    ovobb__lap = (grp,) + f_args
    try:
        kwimf__nokz = get_const_func_output_type(func, ovobb__lap, kws,
            self.context, numba.core.registry.cpu_target.target_context, False)
    except Exception as fojla__ocm:
        raise_bodo_error(get_udf_error_msg(f'{obj_name}.pipe()', fojla__ocm
            ), getattr(fojla__ocm, 'loc', None))
    pvhp__ysn = gen_apply_pysig(len(f_args), kws.keys())
    irwti__ilay = (func, *f_args) + tuple(kws.values())
    return signature(kwimf__nokz, *irwti__ilay).replace(pysig=pvhp__ysn)


def gen_apply_pysig(n_args, kws):
    beno__yos = ', '.join(f'arg{fuwca__qlhpz}' for fuwca__qlhpz in range(
        n_args))
    beno__yos = beno__yos + ', ' if beno__yos else ''
    zgkb__axy = ', '.join(f"{aukhm__pihss} = ''" for aukhm__pihss in kws)
    krne__uzhe = f'def apply_stub(func, {beno__yos}{zgkb__axy}):\n'
    krne__uzhe += '    pass\n'
    fjji__acqc = {}
    exec(krne__uzhe, {}, fjji__acqc)
    uunkp__bvzod = fjji__acqc['apply_stub']
    return numba.core.utils.pysignature(uunkp__bvzod)


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
        koc__bpv = get_pivot_output_dtype(data, aggfunc.literal_value)
        xfj__kfa = dtype_to_array_type(koc__bpv)
        if is_overload_none(_pivot_values):
            raise_bodo_error(
                'Dataframe.pivot_table() requires explicit annotation to determine output columns. For more information, see: https://docs.bodo.ai/latest/source/programming_with_bodo/pandas.html'
                )
        ruty__sps = _pivot_values.meta
        zuu__zxupw = len(ruty__sps)
        hwhbr__wqc = df.columns.index(index)
        anods__loo = df.data[hwhbr__wqc]
        anods__loo = to_str_arr_if_dict_array(anods__loo)
        hwkzv__xsgkv = bodo.hiframes.pd_index_ext.array_type_to_index(
            anods__loo, types.StringLiteral(index))
        sgj__xrrsa = DataFrameType((xfj__kfa,) * zuu__zxupw, hwkzv__xsgkv,
            tuple(ruty__sps))
        return signature(sgj__xrrsa, *args)


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
        xfj__kfa = types.Array(types.int64, 1, 'C')
        ruty__sps = _pivot_values.meta
        zuu__zxupw = len(ruty__sps)
        hwkzv__xsgkv = bodo.hiframes.pd_index_ext.array_type_to_index(
            to_str_arr_if_dict_array(index.data), types.StringLiteral('index'))
        sgj__xrrsa = DataFrameType((xfj__kfa,) * zuu__zxupw, hwkzv__xsgkv,
            tuple(ruty__sps))
        return signature(sgj__xrrsa, *args)


CrossTabTyper._no_unliteral = True


@lower_builtin(crosstab_dummy, types.VarArg(types.Any))
def lower_crosstab_dummy(context, builder, sig, args):
    return context.get_constant_null(sig.return_type)


def get_group_indices(keys, dropna, _is_parallel):
    return np.arange(len(keys))


@overload(get_group_indices)
def get_group_indices_overload(keys, dropna, _is_parallel):
    krne__uzhe = 'def impl(keys, dropna, _is_parallel):\n'
    krne__uzhe += (
        "    ev = bodo.utils.tracing.Event('get_group_indices', _is_parallel)\n"
        )
    krne__uzhe += '    info_list = [{}]\n'.format(', '.join(
        f'array_to_info(keys[{fuwca__qlhpz}])' for fuwca__qlhpz in range(
        len(keys.types))))
    krne__uzhe += '    table = arr_info_list_to_table(info_list)\n'
    krne__uzhe += '    group_labels = np.empty(len(keys[0]), np.int64)\n'
    krne__uzhe += '    sort_idx = np.empty(len(keys[0]), np.int64)\n'
    krne__uzhe += """    ngroups = get_groupby_labels(table, group_labels.ctypes, sort_idx.ctypes, dropna, _is_parallel)
"""
    krne__uzhe += '    delete_table_decref_arrays(table)\n'
    krne__uzhe += '    ev.finalize()\n'
    krne__uzhe += '    return sort_idx, group_labels, ngroups\n'
    fjji__acqc = {}
    exec(krne__uzhe, {'bodo': bodo, 'np': np, 'get_groupby_labels':
        get_groupby_labels, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table,
        'delete_table_decref_arrays': delete_table_decref_arrays}, fjji__acqc)
    bimf__pomiz = fjji__acqc['impl']
    return bimf__pomiz


@numba.njit(no_cpython_wrapper=True)
def generate_slices(labels, ngroups):
    nusxb__makp = len(labels)
    tfv__gdxr = np.zeros(ngroups, dtype=np.int64)
    hxdd__ocnis = np.zeros(ngroups, dtype=np.int64)
    shd__rcmqq = 0
    ahemz__euxef = 0
    for fuwca__qlhpz in range(nusxb__makp):
        clgi__pgl = labels[fuwca__qlhpz]
        if clgi__pgl < 0:
            shd__rcmqq += 1
        else:
            ahemz__euxef += 1
            if fuwca__qlhpz == nusxb__makp - 1 or clgi__pgl != labels[
                fuwca__qlhpz + 1]:
                tfv__gdxr[clgi__pgl] = shd__rcmqq
                hxdd__ocnis[clgi__pgl] = shd__rcmqq + ahemz__euxef
                shd__rcmqq += ahemz__euxef
                ahemz__euxef = 0
    return tfv__gdxr, hxdd__ocnis


def shuffle_dataframe(df, keys, _is_parallel):
    return df, keys, _is_parallel


@overload(shuffle_dataframe, prefer_literal=True)
def overload_shuffle_dataframe(df, keys, _is_parallel):
    bimf__pomiz, wuvy__odrx = gen_shuffle_dataframe(df, keys, _is_parallel)
    return bimf__pomiz


def gen_shuffle_dataframe(df, keys, _is_parallel):
    goo__rvr = len(df.columns)
    vlef__sgxst = len(keys.types)
    assert is_overload_constant_bool(_is_parallel
        ), 'shuffle_dataframe: _is_parallel is not a constant'
    krne__uzhe = 'def impl(df, keys, _is_parallel):\n'
    if is_overload_false(_is_parallel):
        krne__uzhe += '  return df, keys, get_null_shuffle_info()\n'
        fjji__acqc = {}
        exec(krne__uzhe, {'get_null_shuffle_info': get_null_shuffle_info},
            fjji__acqc)
        bimf__pomiz = fjji__acqc['impl']
        return bimf__pomiz
    for fuwca__qlhpz in range(goo__rvr):
        krne__uzhe += f"""  in_arr{fuwca__qlhpz} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {fuwca__qlhpz})
"""
    krne__uzhe += f"""  in_index_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))
"""
    krne__uzhe += '  info_list = [{}, {}, {}]\n'.format(', '.join(
        f'array_to_info(keys[{fuwca__qlhpz}])' for fuwca__qlhpz in range(
        vlef__sgxst)), ', '.join(f'array_to_info(in_arr{fuwca__qlhpz})' for
        fuwca__qlhpz in range(goo__rvr)), 'array_to_info(in_index_arr)')
    krne__uzhe += '  table = arr_info_list_to_table(info_list)\n'
    krne__uzhe += (
        f'  out_table = shuffle_table(table, {vlef__sgxst}, _is_parallel, 1)\n'
        )
    for fuwca__qlhpz in range(vlef__sgxst):
        krne__uzhe += f"""  out_key{fuwca__qlhpz} = info_to_array(info_from_table(out_table, {fuwca__qlhpz}), keys{fuwca__qlhpz}_typ)
"""
    for fuwca__qlhpz in range(goo__rvr):
        krne__uzhe += f"""  out_arr{fuwca__qlhpz} = info_to_array(info_from_table(out_table, {fuwca__qlhpz + vlef__sgxst}), in_arr{fuwca__qlhpz}_typ)
"""
    krne__uzhe += f"""  out_arr_index = info_to_array(info_from_table(out_table, {vlef__sgxst + goo__rvr}), ind_arr_typ)
"""
    krne__uzhe += '  shuffle_info = get_shuffle_info(out_table)\n'
    krne__uzhe += '  delete_table(out_table)\n'
    krne__uzhe += '  delete_table(table)\n'
    out_data = ', '.join(f'out_arr{fuwca__qlhpz}' for fuwca__qlhpz in range
        (goo__rvr))
    krne__uzhe += (
        '  out_index = bodo.utils.conversion.index_from_array(out_arr_index)\n'
        )
    krne__uzhe += f"""  out_df = bodo.hiframes.pd_dataframe_ext.init_dataframe(({out_data},), out_index, {gen_const_tup(df.columns)})
"""
    krne__uzhe += '  return out_df, ({},), shuffle_info\n'.format(', '.join
        (f'out_key{fuwca__qlhpz}' for fuwca__qlhpz in range(vlef__sgxst)))
    cme__rrbd = {'bodo': bodo, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'shuffle_table':
        shuffle_table, 'info_from_table': info_from_table, 'info_to_array':
        info_to_array, 'delete_table': delete_table, 'get_shuffle_info':
        get_shuffle_info, 'ind_arr_typ': types.Array(types.int64, 1, 'C') if
        isinstance(df.index, RangeIndexType) else df.index.data}
    cme__rrbd.update({f'keys{fuwca__qlhpz}_typ': keys.types[fuwca__qlhpz] for
        fuwca__qlhpz in range(vlef__sgxst)})
    cme__rrbd.update({f'in_arr{fuwca__qlhpz}_typ': df.data[fuwca__qlhpz] for
        fuwca__qlhpz in range(goo__rvr)})
    fjji__acqc = {}
    exec(krne__uzhe, cme__rrbd, fjji__acqc)
    bimf__pomiz = fjji__acqc['impl']
    return bimf__pomiz, cme__rrbd


def reverse_shuffle(data, shuffle_info):
    return data


@overload(reverse_shuffle)
def overload_reverse_shuffle(data, shuffle_info):
    if isinstance(data, bodo.hiframes.pd_multi_index_ext.MultiIndexType):
        mge__ccydy = len(data.array_types)
        krne__uzhe = 'def impl(data, shuffle_info):\n'
        krne__uzhe += '  info_list = [{}]\n'.format(', '.join(
            f'array_to_info(data._data[{fuwca__qlhpz}])' for fuwca__qlhpz in
            range(mge__ccydy)))
        krne__uzhe += '  table = arr_info_list_to_table(info_list)\n'
        krne__uzhe += (
            '  out_table = reverse_shuffle_table(table, shuffle_info)\n')
        for fuwca__qlhpz in range(mge__ccydy):
            krne__uzhe += f"""  out_arr{fuwca__qlhpz} = info_to_array(info_from_table(out_table, {fuwca__qlhpz}), data._data[{fuwca__qlhpz}])
"""
        krne__uzhe += '  delete_table(out_table)\n'
        krne__uzhe += '  delete_table(table)\n'
        krne__uzhe += (
            '  return init_multi_index(({},), data._names, data._name)\n'.
            format(', '.join(f'out_arr{fuwca__qlhpz}' for fuwca__qlhpz in
            range(mge__ccydy))))
        fjji__acqc = {}
        exec(krne__uzhe, {'bodo': bodo, 'array_to_info': array_to_info,
            'arr_info_list_to_table': arr_info_list_to_table,
            'reverse_shuffle_table': reverse_shuffle_table,
            'info_from_table': info_from_table, 'info_to_array':
            info_to_array, 'delete_table': delete_table, 'init_multi_index':
            bodo.hiframes.pd_multi_index_ext.init_multi_index}, fjji__acqc)
        bimf__pomiz = fjji__acqc['impl']
        return bimf__pomiz
    if bodo.hiframes.pd_index_ext.is_index_type(data):

        def impl_index(data, shuffle_info):
            leob__swwrn = bodo.utils.conversion.index_to_array(data)
            bpjh__mvakw = reverse_shuffle(leob__swwrn, shuffle_info)
            return bodo.utils.conversion.index_from_array(bpjh__mvakw)
        return impl_index

    def impl_arr(data, shuffle_info):
        eqog__hvswc = [array_to_info(data)]
        hxm__ztpy = arr_info_list_to_table(eqog__hvswc)
        drwj__heo = reverse_shuffle_table(hxm__ztpy, shuffle_info)
        bpjh__mvakw = info_to_array(info_from_table(drwj__heo, 0), data)
        delete_table(drwj__heo)
        delete_table(hxm__ztpy)
        return bpjh__mvakw
    return impl_arr


@overload_method(DataFrameGroupByType, 'value_counts', inline='always',
    no_unliteral=True)
def groupby_value_counts(grp, normalize=False, sort=True, ascending=False,
    bins=None, dropna=True):
    hqsy__mebat = dict(normalize=normalize, sort=sort, bins=bins, dropna=dropna
        )
    iturp__gdrna = dict(normalize=False, sort=True, bins=None, dropna=True)
    check_unsupported_args('Groupby.value_counts', hqsy__mebat,
        iturp__gdrna, package_name='pandas', module_name='GroupBy')
    if len(grp.selection) > 1 or not grp.as_index:
        raise BodoError(
            "'DataFrameGroupBy' object has no attribute 'value_counts'")
    if not is_overload_constant_bool(ascending):
        raise BodoError(
            'Groupby.value_counts() ascending must be a constant boolean')
    maiet__nud = get_overload_const_bool(ascending)
    yifk__ehr = grp.selection[0]
    krne__uzhe = f"""def impl(grp, normalize=False, sort=True, ascending=False, bins=None, dropna=True):
"""
    sculk__iuaq = (
        f"lambda S: S.value_counts(ascending={maiet__nud}, _index_name='{yifk__ehr}')"
        )
    krne__uzhe += f'    return grp.apply({sculk__iuaq})\n'
    fjji__acqc = {}
    exec(krne__uzhe, {'bodo': bodo}, fjji__acqc)
    bimf__pomiz = fjji__acqc['impl']
    return bimf__pomiz


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
    for qyu__sfc in groupby_unsupported_attr:
        overload_attribute(DataFrameGroupByType, qyu__sfc, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{qyu__sfc}'))
    for qyu__sfc in groupby_unsupported:
        overload_method(DataFrameGroupByType, qyu__sfc, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{qyu__sfc}'))
    for qyu__sfc in series_only_unsupported_attrs:
        overload_attribute(DataFrameGroupByType, qyu__sfc, no_unliteral=True)(
            create_unsupported_overload(f'SeriesGroupBy.{qyu__sfc}'))
    for qyu__sfc in series_only_unsupported:
        overload_method(DataFrameGroupByType, qyu__sfc, no_unliteral=True)(
            create_unsupported_overload(f'SeriesGroupBy.{qyu__sfc}'))
    for qyu__sfc in dataframe_only_unsupported:
        overload_method(DataFrameGroupByType, qyu__sfc, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{qyu__sfc}'))


_install_groupby_unsupported()
