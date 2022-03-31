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
        lgqi__yfdgn = [('obj', fe_type.df_type)]
        super(GroupbyModel, self).__init__(dmm, fe_type, lgqi__yfdgn)


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
        awj__rbwyc = args[0]
        vgzeq__iuw = signature.return_type
        xulp__iblrw = cgutils.create_struct_proxy(vgzeq__iuw)(context, builder)
        xulp__iblrw.obj = awj__rbwyc
        context.nrt.incref(builder, signature.args[0], awj__rbwyc)
        return xulp__iblrw._getvalue()
    if is_overload_constant_list(by_type):
        keys = tuple(get_overload_const_list(by_type))
    elif is_literal_type(by_type):
        keys = get_literal_value(by_type),
    else:
        assert False, 'Reached unreachable code in init_groupby; there is an validate_groupby_spec'
    selection = list(obj_type.columns)
    for ndh__aspux in keys:
        selection.remove(ndh__aspux)
    if is_overload_constant_bool(as_index_type):
        as_index = is_overload_true(as_index_type)
    else:
        as_index = True
    if is_overload_constant_bool(dropna_type):
        dropna = is_overload_true(dropna_type)
    else:
        dropna = True
    vgzeq__iuw = DataFrameGroupByType(obj_type, keys, tuple(selection),
        as_index, dropna, False)
    return vgzeq__iuw(obj_type, by_type, as_index_type, dropna_type), codegen


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
        grpby, ptcbi__jcli = args
        if isinstance(grpby, DataFrameGroupByType):
            series_select = False
            if isinstance(ptcbi__jcli, (tuple, list)):
                if len(set(ptcbi__jcli).difference(set(grpby.df_type.columns))
                    ) > 0:
                    raise_bodo_error(
                        'groupby: selected column {} not found in dataframe'
                        .format(set(ptcbi__jcli).difference(set(grpby.
                        df_type.columns))))
                selection = ptcbi__jcli
            else:
                if ptcbi__jcli not in grpby.df_type.columns:
                    raise_bodo_error(
                        'groupby: selected column {} not found in dataframe'
                        .format(ptcbi__jcli))
                selection = ptcbi__jcli,
                series_select = True
            hcbmf__onleu = DataFrameGroupByType(grpby.df_type, grpby.keys,
                selection, grpby.as_index, grpby.dropna, True, series_select)
            return signature(hcbmf__onleu, *args)


@infer_global(operator.getitem)
class GetItemDataFrameGroupBy(AbstractTemplate):

    def generic(self, args, kws):
        grpby, ptcbi__jcli = args
        if isinstance(grpby, DataFrameGroupByType) and is_literal_type(
            ptcbi__jcli):
            hcbmf__onleu = StaticGetItemDataFrameGroupBy.generic(self, (
                grpby, get_literal_value(ptcbi__jcli)), {}).return_type
            return signature(hcbmf__onleu, *args)


GetItemDataFrameGroupBy.prefer_literal = True


@lower_builtin('static_getitem', DataFrameGroupByType, types.Any)
@lower_builtin(operator.getitem, DataFrameGroupByType, types.Any)
def static_getitem_df_groupby(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


def get_groupby_output_dtype(arr_type, func_name, index_type=None):
    arr_type = to_str_arr_if_dict_array(arr_type)
    vvsz__ftb = arr_type == ArrayItemArrayType(string_array_type)
    rpakm__eajev = arr_type.dtype
    if isinstance(rpakm__eajev, bodo.hiframes.datetime_timedelta_ext.
        DatetimeTimeDeltaType):
        raise BodoError(
            f"""column type of {rpakm__eajev} is not supported in groupby built-in function {func_name}.
{dt_err}"""
            )
    if func_name == 'median' and not isinstance(rpakm__eajev, (
        Decimal128Type, types.Float, types.Integer)):
        return (None,
            'For median, only column of integer, float or Decimal type are allowed'
            )
    if func_name in ('first', 'last', 'sum', 'prod', 'min', 'max', 'count',
        'nunique', 'head') and isinstance(arr_type, (TupleArrayType,
        ArrayItemArrayType)):
        return (None,
            f'column type of list/tuple of {rpakm__eajev} is not supported in groupby built-in function {func_name}'
            )
    if func_name in {'median', 'mean', 'var', 'std'} and isinstance(
        rpakm__eajev, (Decimal128Type, types.Integer, types.Float)):
        return dtype_to_array_type(types.float64), 'ok'
    if not isinstance(rpakm__eajev, (types.Integer, types.Float, types.Boolean)
        ):
        if vvsz__ftb or rpakm__eajev == types.unicode_type:
            if func_name not in {'count', 'nunique', 'min', 'max', 'sum',
                'first', 'last', 'head'}:
                return (None,
                    f'column type of strings or list of strings is not supported in groupby built-in function {func_name}'
                    )
        else:
            if isinstance(rpakm__eajev, bodo.PDCategoricalDtype):
                if func_name in ('min', 'max') and not rpakm__eajev.ordered:
                    return (None,
                        f'categorical column must be ordered in groupby built-in function {func_name}'
                        )
            if func_name not in {'count', 'nunique', 'min', 'max', 'first',
                'last', 'head'}:
                return (None,
                    f'column type of {rpakm__eajev} is not supported in groupby built-in function {func_name}'
                    )
    if isinstance(rpakm__eajev, types.Boolean) and func_name in {'cumsum',
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
    rpakm__eajev = arr_type.dtype
    if func_name in {'count'}:
        return IntDtype(types.int64)
    if func_name in {'sum', 'prod', 'min', 'max'}:
        if func_name in {'sum', 'prod'} and not isinstance(rpakm__eajev, (
            types.Integer, types.Float)):
            raise BodoError(
                'pivot_table(): sum and prod operations require integer or float input'
                )
        if isinstance(rpakm__eajev, types.Integer):
            return IntDtype(rpakm__eajev)
        return rpakm__eajev
    if func_name in {'mean', 'var', 'std'}:
        return types.float64
    raise BodoError('invalid pivot operation')


def check_args_kwargs(func_name, len_args, args, kws):
    if len(kws) > 0:
        gskun__kmvt = list(kws.keys())[0]
        raise BodoError(
            f"Groupby.{func_name}() got an unexpected keyword argument '{gskun__kmvt}'."
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
    for ndh__aspux in grp.keys:
        if multi_level_names:
            eyf__phrnh = ndh__aspux, ''
        else:
            eyf__phrnh = ndh__aspux
        mrsm__enr = grp.df_type.columns.index(ndh__aspux)
        data = to_str_arr_if_dict_array(grp.df_type.data[mrsm__enr])
        out_columns.append(eyf__phrnh)
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
        eljgm__gpyyi = tuple(grp.df_type.columns.index(grp.keys[fmd__nsqt]) for
            fmd__nsqt in range(len(grp.keys)))
        xju__nqf = tuple(grp.df_type.data[mrsm__enr] for mrsm__enr in
            eljgm__gpyyi)
        xju__nqf = tuple(to_str_arr_if_dict_array(rjvaj__tjr) for
            rjvaj__tjr in xju__nqf)
        index = MultiIndexType(xju__nqf, tuple(types.StringLiteral(
            ndh__aspux) for ndh__aspux in grp.keys))
    else:
        mrsm__enr = grp.df_type.columns.index(grp.keys[0])
        adl__ves = to_str_arr_if_dict_array(grp.df_type.data[mrsm__enr])
        index = bodo.hiframes.pd_index_ext.array_type_to_index(adl__ves,
            types.StringLiteral(grp.keys[0]))
    hfff__qhazm = {}
    vqyh__ewp = []
    if func_name in ('size', 'count'):
        kws = dict(kws) if kws else {}
        check_args_kwargs(func_name, 0, args, kws)
    if func_name == 'size':
        out_data.append(types.Array(types.int64, 1, 'C'))
        out_columns.append('size')
        hfff__qhazm[None, 'size'] = 'size'
    else:
        columns = (grp.selection if func_name != 'head' or grp.
            explicit_select else grp.df_type.columns)
        for egb__lrccf in columns:
            mrsm__enr = grp.df_type.columns.index(egb__lrccf)
            data = grp.df_type.data[mrsm__enr]
            data = to_str_arr_if_dict_array(data)
            htbej__awb = ColumnType.NonNumericalColumn.value
            if isinstance(data, (types.Array, IntegerArrayType)
                ) and isinstance(data.dtype, (types.Integer, types.Float)):
                htbej__awb = ColumnType.NumericalColumn.value
            if func_name == 'agg':
                try:
                    dni__noeo = SeriesType(data.dtype, data, None, string_type)
                    nqm__agt = get_const_func_output_type(func, (dni__noeo,
                        ), {}, typing_context, target_context)
                    if nqm__agt != ArrayItemArrayType(string_array_type):
                        nqm__agt = dtype_to_array_type(nqm__agt)
                    err_msg = 'ok'
                except:
                    raise_bodo_error(
                        'Groupy.agg()/Groupy.aggregate(): column {col} of type {type} is unsupported/not a valid input type for user defined function'
                        .format(col=egb__lrccf, type=data.dtype))
            else:
                if func_name in ('first', 'last', 'min', 'max'):
                    kws = dict(kws) if kws else {}
                    xcjs__fwdm = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', False)
                    fbiql__vrml = args[1] if len(args) > 1 else kws.pop(
                        'min_count', -1)
                    cmemm__xvrkf = dict(numeric_only=xcjs__fwdm, min_count=
                        fbiql__vrml)
                    nvg__kxzyi = dict(numeric_only=False, min_count=-1)
                    check_unsupported_args(f'Groupby.{func_name}',
                        cmemm__xvrkf, nvg__kxzyi, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('sum', 'prod'):
                    kws = dict(kws) if kws else {}
                    xcjs__fwdm = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', True)
                    fbiql__vrml = args[1] if len(args) > 1 else kws.pop(
                        'min_count', 0)
                    cmemm__xvrkf = dict(numeric_only=xcjs__fwdm, min_count=
                        fbiql__vrml)
                    nvg__kxzyi = dict(numeric_only=True, min_count=0)
                    check_unsupported_args(f'Groupby.{func_name}',
                        cmemm__xvrkf, nvg__kxzyi, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('mean', 'median'):
                    kws = dict(kws) if kws else {}
                    xcjs__fwdm = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', True)
                    cmemm__xvrkf = dict(numeric_only=xcjs__fwdm)
                    nvg__kxzyi = dict(numeric_only=True)
                    check_unsupported_args(f'Groupby.{func_name}',
                        cmemm__xvrkf, nvg__kxzyi, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('idxmin', 'idxmax'):
                    kws = dict(kws) if kws else {}
                    zyuxf__kpsy = args[0] if len(args) > 0 else kws.pop('axis',
                        0)
                    gkt__qfup = args[1] if len(args) > 1 else kws.pop('skipna',
                        True)
                    cmemm__xvrkf = dict(axis=zyuxf__kpsy, skipna=gkt__qfup)
                    nvg__kxzyi = dict(axis=0, skipna=True)
                    check_unsupported_args(f'Groupby.{func_name}',
                        cmemm__xvrkf, nvg__kxzyi, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('var', 'std'):
                    kws = dict(kws) if kws else {}
                    glbks__gilka = args[0] if len(args) > 0 else kws.pop('ddof'
                        , 1)
                    cmemm__xvrkf = dict(ddof=glbks__gilka)
                    nvg__kxzyi = dict(ddof=1)
                    check_unsupported_args(f'Groupby.{func_name}',
                        cmemm__xvrkf, nvg__kxzyi, package_name='pandas',
                        module_name='GroupBy')
                elif func_name == 'nunique':
                    kws = dict(kws) if kws else {}
                    dropna = args[0] if len(args) > 0 else kws.pop('dropna', 1)
                    check_args_kwargs(func_name, 1, args, kws)
                elif func_name == 'head':
                    if len(args) == 0:
                        kws.pop('n', None)
                nqm__agt, err_msg = get_groupby_output_dtype(data,
                    func_name, grp.df_type.index)
            if err_msg == 'ok':
                lmq__nbji = to_str_arr_if_dict_array(nqm__agt)
                out_data.append(lmq__nbji)
                out_columns.append(egb__lrccf)
                if func_name == 'agg':
                    jgs__kqf = bodo.ir.aggregate._get_udf_name(bodo.ir.
                        aggregate._get_const_agg_func(func, None))
                    hfff__qhazm[egb__lrccf, jgs__kqf] = egb__lrccf
                else:
                    hfff__qhazm[egb__lrccf, func_name] = egb__lrccf
                out_column_type.append(htbej__awb)
            else:
                vqyh__ewp.append(err_msg)
    if func_name == 'sum':
        wkc__vowlp = any([(zjaap__rkuab == ColumnType.NumericalColumn.value
            ) for zjaap__rkuab in out_column_type])
        if wkc__vowlp:
            out_data = [zjaap__rkuab for zjaap__rkuab, auolk__rxroo in zip(
                out_data, out_column_type) if auolk__rxroo != ColumnType.
                NonNumericalColumn.value]
            out_columns = [zjaap__rkuab for zjaap__rkuab, auolk__rxroo in
                zip(out_columns, out_column_type) if auolk__rxroo !=
                ColumnType.NonNumericalColumn.value]
            hfff__qhazm = {}
            for egb__lrccf in out_columns:
                if grp.as_index is False and egb__lrccf in grp.keys:
                    continue
                hfff__qhazm[egb__lrccf, func_name] = egb__lrccf
    ppozs__gpeq = len(vqyh__ewp)
    if len(out_data) == 0:
        if ppozs__gpeq == 0:
            raise BodoError('No columns in output.')
        else:
            raise BodoError(
                'No columns in output. {} column{} dropped for following reasons: {}'
                .format(ppozs__gpeq, ' was' if ppozs__gpeq == 1 else
                's were', ','.join(vqyh__ewp)))
    osphx__sdzgy = DataFrameType(tuple(out_data), index, tuple(out_columns))
    if (len(grp.selection) == 1 and grp.series_select and grp.as_index or 
        func_name == 'size' and grp.as_index):
        if isinstance(out_data[0], IntegerArrayType):
            lybxx__mrr = IntDtype(out_data[0].dtype)
        else:
            lybxx__mrr = out_data[0].dtype
        mgw__lldh = types.none if func_name == 'size' else types.StringLiteral(
            grp.selection[0])
        osphx__sdzgy = SeriesType(lybxx__mrr, index=index, name_typ=mgw__lldh)
    return signature(osphx__sdzgy, *args), hfff__qhazm


def get_agg_funcname_and_outtyp(grp, col, f_val, typing_context, target_context
    ):
    crtfq__brjj = True
    if isinstance(f_val, str):
        crtfq__brjj = False
        wteg__xau = f_val
    elif is_overload_constant_str(f_val):
        crtfq__brjj = False
        wteg__xau = get_overload_const_str(f_val)
    elif bodo.utils.typing.is_builtin_function(f_val):
        crtfq__brjj = False
        wteg__xau = bodo.utils.typing.get_builtin_function_name(f_val)
    if not crtfq__brjj:
        if wteg__xau not in bodo.ir.aggregate.supported_agg_funcs[:-1]:
            raise BodoError(f'unsupported aggregate function {wteg__xau}')
        hcbmf__onleu = DataFrameGroupByType(grp.df_type, grp.keys, (col,),
            grp.as_index, grp.dropna, True, True)
        out_tp = get_agg_typ(hcbmf__onleu, (), wteg__xau, typing_context,
            target_context)[0].return_type
    else:
        if is_expr(f_val, 'make_function'):
            ocyk__iup = types.functions.MakeFunctionLiteral(f_val)
        else:
            ocyk__iup = f_val
        validate_udf('agg', ocyk__iup)
        func = get_overload_const_func(ocyk__iup, None)
        bfe__fig = func.code if hasattr(func, 'code') else func.__code__
        wteg__xau = bfe__fig.co_name
        hcbmf__onleu = DataFrameGroupByType(grp.df_type, grp.keys, (col,),
            grp.as_index, grp.dropna, True, True)
        out_tp = get_agg_typ(hcbmf__onleu, (), 'agg', typing_context,
            target_context, ocyk__iup)[0].return_type
    return wteg__xau, out_tp


def resolve_agg(grp, args, kws, typing_context, target_context):
    func = get_call_expr_arg('agg', args, dict(kws), 0, 'func', default=
        types.none)
    zlrds__tqu = kws and all(isinstance(emnym__vbe, types.Tuple) and len(
        emnym__vbe) == 2 for emnym__vbe in kws.values())
    if is_overload_none(func) and not zlrds__tqu:
        raise_bodo_error("Groupby.agg()/aggregate(): Must provide 'func'")
    if len(args) > 1 or kws and not zlrds__tqu:
        raise_bodo_error(
            'Groupby.agg()/aggregate(): passing extra arguments to functions not supported yet.'
            )
    kmgn__dsd = False

    def _append_out_type(grp, out_data, out_tp):
        if grp.as_index is False:
            out_data.append(out_tp.data[len(grp.keys)])
        else:
            out_data.append(out_tp.data)
    if zlrds__tqu or is_overload_constant_dict(func):
        if zlrds__tqu:
            qged__znjck = [get_literal_value(bnmif__lgtsi) for bnmif__lgtsi,
                jiq__hovgn in kws.values()]
            gviq__otam = [get_literal_value(fkvm__gyo) for jiq__hovgn,
                fkvm__gyo in kws.values()]
        else:
            ghbfk__nxg = get_overload_constant_dict(func)
            qged__znjck = tuple(ghbfk__nxg.keys())
            gviq__otam = tuple(ghbfk__nxg.values())
        if 'head' in gviq__otam:
            raise BodoError(
                'Groupby.agg()/aggregate(): head cannot be mixed with other groupby operations.'
                )
        if any(egb__lrccf not in grp.selection and egb__lrccf not in grp.
            keys for egb__lrccf in qged__znjck):
            raise_bodo_error(
                f'Selected column names {qged__znjck} not all available in dataframe column names {grp.selection}'
                )
        multi_level_names = any(isinstance(f_val, (tuple, list)) for f_val in
            gviq__otam)
        if zlrds__tqu and multi_level_names:
            raise_bodo_error(
                'Groupby.agg()/aggregate(): cannot pass multiple functions in a single pd.NamedAgg()'
                )
        hfff__qhazm = {}
        out_columns = []
        out_data = []
        out_column_type = []
        cey__hxu = []
        if not grp.as_index:
            get_keys_not_as_index(grp, out_columns, out_data,
                out_column_type, multi_level_names=multi_level_names)
        for ccln__utn, f_val in zip(qged__znjck, gviq__otam):
            if isinstance(f_val, (tuple, list)):
                nfgu__qrk = 0
                for ocyk__iup in f_val:
                    wteg__xau, out_tp = get_agg_funcname_and_outtyp(grp,
                        ccln__utn, ocyk__iup, typing_context, target_context)
                    kmgn__dsd = wteg__xau in list_cumulative
                    if wteg__xau == '<lambda>' and len(f_val) > 1:
                        wteg__xau = '<lambda_' + str(nfgu__qrk) + '>'
                        nfgu__qrk += 1
                    out_columns.append((ccln__utn, wteg__xau))
                    hfff__qhazm[ccln__utn, wteg__xau] = ccln__utn, wteg__xau
                    _append_out_type(grp, out_data, out_tp)
            else:
                wteg__xau, out_tp = get_agg_funcname_and_outtyp(grp,
                    ccln__utn, f_val, typing_context, target_context)
                kmgn__dsd = wteg__xau in list_cumulative
                if multi_level_names:
                    out_columns.append((ccln__utn, wteg__xau))
                    hfff__qhazm[ccln__utn, wteg__xau] = ccln__utn, wteg__xau
                elif not zlrds__tqu:
                    out_columns.append(ccln__utn)
                    hfff__qhazm[ccln__utn, wteg__xau] = ccln__utn
                elif zlrds__tqu:
                    cey__hxu.append(wteg__xau)
                _append_out_type(grp, out_data, out_tp)
        if zlrds__tqu:
            for fmd__nsqt, fkk__fmf in enumerate(kws.keys()):
                out_columns.append(fkk__fmf)
                hfff__qhazm[qged__znjck[fmd__nsqt], cey__hxu[fmd__nsqt]
                    ] = fkk__fmf
        if kmgn__dsd:
            index = grp.df_type.index
        else:
            index = out_tp.index
        osphx__sdzgy = DataFrameType(tuple(out_data), index, tuple(out_columns)
            )
        return signature(osphx__sdzgy, *args), hfff__qhazm
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
        nfgu__qrk = 0
        if not grp.as_index:
            get_keys_not_as_index(grp, out_columns, out_data, out_column_type)
        hfff__qhazm = {}
        nby__kfujp = grp.selection[0]
        for f_val in func.types:
            wteg__xau, out_tp = get_agg_funcname_and_outtyp(grp, nby__kfujp,
                f_val, typing_context, target_context)
            kmgn__dsd = wteg__xau in list_cumulative
            if wteg__xau == '<lambda>':
                wteg__xau = '<lambda_' + str(nfgu__qrk) + '>'
                nfgu__qrk += 1
            out_columns.append(wteg__xau)
            hfff__qhazm[nby__kfujp, wteg__xau] = wteg__xau
            _append_out_type(grp, out_data, out_tp)
        if kmgn__dsd:
            index = grp.df_type.index
        else:
            index = out_tp.index
        osphx__sdzgy = DataFrameType(tuple(out_data), index, tuple(out_columns)
            )
        return signature(osphx__sdzgy, *args), hfff__qhazm
    wteg__xau = ''
    if types.unliteral(func) == types.unicode_type:
        wteg__xau = get_overload_const_str(func)
    if bodo.utils.typing.is_builtin_function(func):
        wteg__xau = bodo.utils.typing.get_builtin_function_name(func)
    if wteg__xau:
        args = args[1:]
        kws.pop('func', None)
        return get_agg_typ(grp, args, wteg__xau, typing_context, kws)
    validate_udf('agg', func)
    return get_agg_typ(grp, args, 'agg', typing_context, target_context, func)


def resolve_transformative(grp, args, kws, msg, name_operation):
    index = grp.df_type.index
    out_columns = []
    out_data = []
    if name_operation in list_cumulative:
        kws = dict(kws) if kws else {}
        zyuxf__kpsy = args[0] if len(args) > 0 else kws.pop('axis', 0)
        xcjs__fwdm = args[1] if len(args) > 1 else kws.pop('numeric_only', 
            False)
        gkt__qfup = args[2] if len(args) > 2 else kws.pop('skipna', 1)
        cmemm__xvrkf = dict(axis=zyuxf__kpsy, numeric_only=xcjs__fwdm)
        nvg__kxzyi = dict(axis=0, numeric_only=False)
        check_unsupported_args(f'Groupby.{name_operation}', cmemm__xvrkf,
            nvg__kxzyi, package_name='pandas', module_name='GroupBy')
        check_args_kwargs(name_operation, 3, args, kws)
    elif name_operation == 'shift':
        miix__kkpn = args[0] if len(args) > 0 else kws.pop('periods', 1)
        wqio__fet = args[1] if len(args) > 1 else kws.pop('freq', None)
        zyuxf__kpsy = args[2] if len(args) > 2 else kws.pop('axis', 0)
        slfk__fkac = args[3] if len(args) > 3 else kws.pop('fill_value', None)
        cmemm__xvrkf = dict(freq=wqio__fet, axis=zyuxf__kpsy, fill_value=
            slfk__fkac)
        nvg__kxzyi = dict(freq=None, axis=0, fill_value=None)
        check_unsupported_args(f'Groupby.{name_operation}', cmemm__xvrkf,
            nvg__kxzyi, package_name='pandas', module_name='GroupBy')
        check_args_kwargs(name_operation, 4, args, kws)
    elif name_operation == 'transform':
        kws = dict(kws)
        klbab__bkj = args[0] if len(args) > 0 else kws.pop('func', None)
        fsnwv__lnt = kws.pop('engine', None)
        pyct__umhhw = kws.pop('engine_kwargs', None)
        cmemm__xvrkf = dict(engine=fsnwv__lnt, engine_kwargs=pyct__umhhw)
        nvg__kxzyi = dict(engine=None, engine_kwargs=None)
        check_unsupported_args(f'Groupby.transform', cmemm__xvrkf,
            nvg__kxzyi, package_name='pandas', module_name='GroupBy')
    hfff__qhazm = {}
    for egb__lrccf in grp.selection:
        out_columns.append(egb__lrccf)
        hfff__qhazm[egb__lrccf, name_operation] = egb__lrccf
        mrsm__enr = grp.df_type.columns.index(egb__lrccf)
        data = grp.df_type.data[mrsm__enr]
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
            nqm__agt, err_msg = get_groupby_output_dtype(data,
                get_literal_value(klbab__bkj), grp.df_type.index)
            if err_msg == 'ok':
                data = nqm__agt
            else:
                raise BodoError(
                    f'column type of {data.dtype} is not supported by {args[0]} yet.\n'
                    )
        out_data.append(data)
    if len(out_data) == 0:
        raise BodoError('No columns in output.')
    osphx__sdzgy = DataFrameType(tuple(out_data), index, tuple(out_columns))
    if len(grp.selection) == 1 and grp.series_select and grp.as_index:
        osphx__sdzgy = SeriesType(out_data[0].dtype, data=out_data[0],
            index=index, name_typ=types.StringLiteral(grp.selection[0]))
    return signature(osphx__sdzgy, *args), hfff__qhazm


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
        dhc__ramos = _get_groupby_apply_udf_out_type(func, grp, f_args, kws,
            self.context, numba.core.registry.cpu_target.target_context)
        apu__cze = isinstance(dhc__ramos, (SeriesType, HeterogeneousSeriesType)
            ) and dhc__ramos.const_info is not None or not isinstance(
            dhc__ramos, (SeriesType, DataFrameType))
        if apu__cze:
            out_data = []
            out_columns = []
            out_column_type = []
            if not grp.as_index:
                get_keys_not_as_index(grp, out_columns, out_data,
                    out_column_type)
                pbcf__ubqa = NumericIndexType(types.int64, types.none)
            elif len(grp.keys) > 1:
                eljgm__gpyyi = tuple(grp.df_type.columns.index(grp.keys[
                    fmd__nsqt]) for fmd__nsqt in range(len(grp.keys)))
                xju__nqf = tuple(grp.df_type.data[mrsm__enr] for mrsm__enr in
                    eljgm__gpyyi)
                xju__nqf = tuple(to_str_arr_if_dict_array(rjvaj__tjr) for
                    rjvaj__tjr in xju__nqf)
                pbcf__ubqa = MultiIndexType(xju__nqf, tuple(types.literal(
                    ndh__aspux) for ndh__aspux in grp.keys))
            else:
                mrsm__enr = grp.df_type.columns.index(grp.keys[0])
                adl__ves = grp.df_type.data[mrsm__enr]
                adl__ves = to_str_arr_if_dict_array(adl__ves)
                pbcf__ubqa = bodo.hiframes.pd_index_ext.array_type_to_index(
                    adl__ves, types.literal(grp.keys[0]))
            out_data = tuple(out_data)
            out_columns = tuple(out_columns)
        else:
            wrjc__ktb = tuple(grp.df_type.data[grp.df_type.columns.index(
                egb__lrccf)] for egb__lrccf in grp.keys)
            wrjc__ktb = tuple(to_str_arr_if_dict_array(rjvaj__tjr) for
                rjvaj__tjr in wrjc__ktb)
            gbmw__hhd = tuple(types.literal(emnym__vbe) for emnym__vbe in
                grp.keys) + get_index_name_types(dhc__ramos.index)
            if not grp.as_index:
                wrjc__ktb = types.Array(types.int64, 1, 'C'),
                gbmw__hhd = (types.none,) + get_index_name_types(dhc__ramos
                    .index)
            pbcf__ubqa = MultiIndexType(wrjc__ktb +
                get_index_data_arr_types(dhc__ramos.index), gbmw__hhd)
        if apu__cze:
            if isinstance(dhc__ramos, HeterogeneousSeriesType):
                jiq__hovgn, nwew__qroaz = dhc__ramos.const_info
                ixyv__ywai = tuple(dtype_to_array_type(rjvaj__tjr) for
                    rjvaj__tjr in dhc__ramos.data.types)
                hhwxy__ani = DataFrameType(out_data + ixyv__ywai,
                    pbcf__ubqa, out_columns + nwew__qroaz)
            elif isinstance(dhc__ramos, SeriesType):
                cijcm__srwfk, nwew__qroaz = dhc__ramos.const_info
                ixyv__ywai = tuple(dtype_to_array_type(dhc__ramos.dtype) for
                    jiq__hovgn in range(cijcm__srwfk))
                hhwxy__ani = DataFrameType(out_data + ixyv__ywai,
                    pbcf__ubqa, out_columns + nwew__qroaz)
            else:
                macvr__wwv = get_udf_out_arr_type(dhc__ramos)
                if not grp.as_index:
                    hhwxy__ani = DataFrameType(out_data + (macvr__wwv,),
                        pbcf__ubqa, out_columns + ('',))
                else:
                    hhwxy__ani = SeriesType(macvr__wwv.dtype, macvr__wwv,
                        pbcf__ubqa, None)
        elif isinstance(dhc__ramos, SeriesType):
            hhwxy__ani = SeriesType(dhc__ramos.dtype, dhc__ramos.data,
                pbcf__ubqa, dhc__ramos.name_typ)
        else:
            hhwxy__ani = DataFrameType(dhc__ramos.data, pbcf__ubqa,
                dhc__ramos.columns)
        wium__oulb = gen_apply_pysig(len(f_args), kws.keys())
        vru__vgv = (func, *f_args) + tuple(kws.values())
        return signature(hhwxy__ani, *vru__vgv).replace(pysig=wium__oulb)

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
    dppya__dqee = grp.df_type
    if grp.explicit_select:
        if len(grp.selection) == 1:
            ccln__utn = grp.selection[0]
            macvr__wwv = dppya__dqee.data[dppya__dqee.columns.index(ccln__utn)]
            macvr__wwv = to_str_arr_if_dict_array(macvr__wwv)
            yqmv__pomy = SeriesType(macvr__wwv.dtype, macvr__wwv,
                dppya__dqee.index, types.literal(ccln__utn))
        else:
            uqi__kjy = tuple(dppya__dqee.data[dppya__dqee.columns.index(
                egb__lrccf)] for egb__lrccf in grp.selection)
            uqi__kjy = tuple(to_str_arr_if_dict_array(rjvaj__tjr) for
                rjvaj__tjr in uqi__kjy)
            yqmv__pomy = DataFrameType(uqi__kjy, dppya__dqee.index, tuple(
                grp.selection))
    else:
        yqmv__pomy = dppya__dqee
    edljw__wpjl = yqmv__pomy,
    edljw__wpjl += tuple(f_args)
    try:
        dhc__ramos = get_const_func_output_type(func, edljw__wpjl, kws,
            typing_context, target_context)
    except Exception as vqk__asex:
        raise_bodo_error(get_udf_error_msg('GroupBy.apply()', vqk__asex),
            getattr(vqk__asex, 'loc', None))
    return dhc__ramos


def resolve_obj_pipe(self, grp, args, kws, obj_name):
    kws = dict(kws)
    func = args[0] if len(args) > 0 else kws.pop('func', None)
    f_args = tuple(args[1:]) if len(args) > 0 else ()
    edljw__wpjl = (grp,) + f_args
    try:
        dhc__ramos = get_const_func_output_type(func, edljw__wpjl, kws,
            self.context, numba.core.registry.cpu_target.target_context, False)
    except Exception as vqk__asex:
        raise_bodo_error(get_udf_error_msg(f'{obj_name}.pipe()', vqk__asex),
            getattr(vqk__asex, 'loc', None))
    wium__oulb = gen_apply_pysig(len(f_args), kws.keys())
    vru__vgv = (func, *f_args) + tuple(kws.values())
    return signature(dhc__ramos, *vru__vgv).replace(pysig=wium__oulb)


def gen_apply_pysig(n_args, kws):
    xvhkw__uyg = ', '.join(f'arg{fmd__nsqt}' for fmd__nsqt in range(n_args))
    xvhkw__uyg = xvhkw__uyg + ', ' if xvhkw__uyg else ''
    cypu__uay = ', '.join(f"{xaf__tebz} = ''" for xaf__tebz in kws)
    gehgx__qmu = f'def apply_stub(func, {xvhkw__uyg}{cypu__uay}):\n'
    gehgx__qmu += '    pass\n'
    vsuf__tanmf = {}
    exec(gehgx__qmu, {}, vsuf__tanmf)
    fjape__xrivj = vsuf__tanmf['apply_stub']
    return numba.core.utils.pysignature(fjape__xrivj)


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
        nqm__agt = get_pivot_output_dtype(data, aggfunc.literal_value)
        zqy__yfouw = dtype_to_array_type(nqm__agt)
        if is_overload_none(_pivot_values):
            raise_bodo_error(
                'Dataframe.pivot_table() requires explicit annotation to determine output columns. For more information, see: https://docs.bodo.ai/latest/source/programming_with_bodo/pandas.html'
                )
        nrbvp__pmxl = _pivot_values.meta
        pmeqt__pfl = len(nrbvp__pmxl)
        mrsm__enr = df.columns.index(index)
        adl__ves = df.data[mrsm__enr]
        adl__ves = to_str_arr_if_dict_array(adl__ves)
        craxv__bhluj = bodo.hiframes.pd_index_ext.array_type_to_index(adl__ves,
            types.StringLiteral(index))
        cekz__zwfb = DataFrameType((zqy__yfouw,) * pmeqt__pfl, craxv__bhluj,
            tuple(nrbvp__pmxl))
        return signature(cekz__zwfb, *args)


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
        zqy__yfouw = types.Array(types.int64, 1, 'C')
        nrbvp__pmxl = _pivot_values.meta
        pmeqt__pfl = len(nrbvp__pmxl)
        craxv__bhluj = bodo.hiframes.pd_index_ext.array_type_to_index(
            to_str_arr_if_dict_array(index.data), types.StringLiteral('index'))
        cekz__zwfb = DataFrameType((zqy__yfouw,) * pmeqt__pfl, craxv__bhluj,
            tuple(nrbvp__pmxl))
        return signature(cekz__zwfb, *args)


CrossTabTyper._no_unliteral = True


@lower_builtin(crosstab_dummy, types.VarArg(types.Any))
def lower_crosstab_dummy(context, builder, sig, args):
    return context.get_constant_null(sig.return_type)


def get_group_indices(keys, dropna, _is_parallel):
    return np.arange(len(keys))


@overload(get_group_indices)
def get_group_indices_overload(keys, dropna, _is_parallel):
    gehgx__qmu = 'def impl(keys, dropna, _is_parallel):\n'
    gehgx__qmu += (
        "    ev = bodo.utils.tracing.Event('get_group_indices', _is_parallel)\n"
        )
    gehgx__qmu += '    info_list = [{}]\n'.format(', '.join(
        f'array_to_info(keys[{fmd__nsqt}])' for fmd__nsqt in range(len(keys
        .types))))
    gehgx__qmu += '    table = arr_info_list_to_table(info_list)\n'
    gehgx__qmu += '    group_labels = np.empty(len(keys[0]), np.int64)\n'
    gehgx__qmu += '    sort_idx = np.empty(len(keys[0]), np.int64)\n'
    gehgx__qmu += """    ngroups = get_groupby_labels(table, group_labels.ctypes, sort_idx.ctypes, dropna, _is_parallel)
"""
    gehgx__qmu += '    delete_table_decref_arrays(table)\n'
    gehgx__qmu += '    ev.finalize()\n'
    gehgx__qmu += '    return sort_idx, group_labels, ngroups\n'
    vsuf__tanmf = {}
    exec(gehgx__qmu, {'bodo': bodo, 'np': np, 'get_groupby_labels':
        get_groupby_labels, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table,
        'delete_table_decref_arrays': delete_table_decref_arrays}, vsuf__tanmf)
    qlnp__imsui = vsuf__tanmf['impl']
    return qlnp__imsui


@numba.njit(no_cpython_wrapper=True)
def generate_slices(labels, ngroups):
    qppm__hrf = len(labels)
    ephpr__bud = np.zeros(ngroups, dtype=np.int64)
    rftbh__vcc = np.zeros(ngroups, dtype=np.int64)
    enun__ycs = 0
    ktj__zjxd = 0
    for fmd__nsqt in range(qppm__hrf):
        kdw__etg = labels[fmd__nsqt]
        if kdw__etg < 0:
            enun__ycs += 1
        else:
            ktj__zjxd += 1
            if fmd__nsqt == qppm__hrf - 1 or kdw__etg != labels[fmd__nsqt + 1]:
                ephpr__bud[kdw__etg] = enun__ycs
                rftbh__vcc[kdw__etg] = enun__ycs + ktj__zjxd
                enun__ycs += ktj__zjxd
                ktj__zjxd = 0
    return ephpr__bud, rftbh__vcc


def shuffle_dataframe(df, keys, _is_parallel):
    return df, keys, _is_parallel


@overload(shuffle_dataframe, prefer_literal=True)
def overload_shuffle_dataframe(df, keys, _is_parallel):
    qlnp__imsui, jiq__hovgn = gen_shuffle_dataframe(df, keys, _is_parallel)
    return qlnp__imsui


def gen_shuffle_dataframe(df, keys, _is_parallel):
    cijcm__srwfk = len(df.columns)
    bvl__gfxsx = len(keys.types)
    assert is_overload_constant_bool(_is_parallel
        ), 'shuffle_dataframe: _is_parallel is not a constant'
    gehgx__qmu = 'def impl(df, keys, _is_parallel):\n'
    if is_overload_false(_is_parallel):
        gehgx__qmu += '  return df, keys, get_null_shuffle_info()\n'
        vsuf__tanmf = {}
        exec(gehgx__qmu, {'get_null_shuffle_info': get_null_shuffle_info},
            vsuf__tanmf)
        qlnp__imsui = vsuf__tanmf['impl']
        return qlnp__imsui
    for fmd__nsqt in range(cijcm__srwfk):
        gehgx__qmu += f"""  in_arr{fmd__nsqt} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {fmd__nsqt})
"""
    gehgx__qmu += f"""  in_index_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))
"""
    gehgx__qmu += '  info_list = [{}, {}, {}]\n'.format(', '.join(
        f'array_to_info(keys[{fmd__nsqt}])' for fmd__nsqt in range(
        bvl__gfxsx)), ', '.join(f'array_to_info(in_arr{fmd__nsqt})' for
        fmd__nsqt in range(cijcm__srwfk)), 'array_to_info(in_index_arr)')
    gehgx__qmu += '  table = arr_info_list_to_table(info_list)\n'
    gehgx__qmu += (
        f'  out_table = shuffle_table(table, {bvl__gfxsx}, _is_parallel, 1)\n')
    for fmd__nsqt in range(bvl__gfxsx):
        gehgx__qmu += f"""  out_key{fmd__nsqt} = info_to_array(info_from_table(out_table, {fmd__nsqt}), keys{fmd__nsqt}_typ)
"""
    for fmd__nsqt in range(cijcm__srwfk):
        gehgx__qmu += f"""  out_arr{fmd__nsqt} = info_to_array(info_from_table(out_table, {fmd__nsqt + bvl__gfxsx}), in_arr{fmd__nsqt}_typ)
"""
    gehgx__qmu += f"""  out_arr_index = info_to_array(info_from_table(out_table, {bvl__gfxsx + cijcm__srwfk}), ind_arr_typ)
"""
    gehgx__qmu += '  shuffle_info = get_shuffle_info(out_table)\n'
    gehgx__qmu += '  delete_table(out_table)\n'
    gehgx__qmu += '  delete_table(table)\n'
    out_data = ', '.join(f'out_arr{fmd__nsqt}' for fmd__nsqt in range(
        cijcm__srwfk))
    gehgx__qmu += (
        '  out_index = bodo.utils.conversion.index_from_array(out_arr_index)\n'
        )
    gehgx__qmu += f"""  out_df = bodo.hiframes.pd_dataframe_ext.init_dataframe(({out_data},), out_index, {gen_const_tup(df.columns)})
"""
    gehgx__qmu += '  return out_df, ({},), shuffle_info\n'.format(', '.join
        (f'out_key{fmd__nsqt}' for fmd__nsqt in range(bvl__gfxsx)))
    cxo__ewbo = {'bodo': bodo, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'shuffle_table':
        shuffle_table, 'info_from_table': info_from_table, 'info_to_array':
        info_to_array, 'delete_table': delete_table, 'get_shuffle_info':
        get_shuffle_info, 'ind_arr_typ': types.Array(types.int64, 1, 'C') if
        isinstance(df.index, RangeIndexType) else df.index.data}
    cxo__ewbo.update({f'keys{fmd__nsqt}_typ': keys.types[fmd__nsqt] for
        fmd__nsqt in range(bvl__gfxsx)})
    cxo__ewbo.update({f'in_arr{fmd__nsqt}_typ': df.data[fmd__nsqt] for
        fmd__nsqt in range(cijcm__srwfk)})
    vsuf__tanmf = {}
    exec(gehgx__qmu, cxo__ewbo, vsuf__tanmf)
    qlnp__imsui = vsuf__tanmf['impl']
    return qlnp__imsui, cxo__ewbo


def reverse_shuffle(data, shuffle_info):
    return data


@overload(reverse_shuffle)
def overload_reverse_shuffle(data, shuffle_info):
    if isinstance(data, bodo.hiframes.pd_multi_index_ext.MultiIndexType):
        czaw__losa = len(data.array_types)
        gehgx__qmu = 'def impl(data, shuffle_info):\n'
        gehgx__qmu += '  info_list = [{}]\n'.format(', '.join(
            f'array_to_info(data._data[{fmd__nsqt}])' for fmd__nsqt in
            range(czaw__losa)))
        gehgx__qmu += '  table = arr_info_list_to_table(info_list)\n'
        gehgx__qmu += (
            '  out_table = reverse_shuffle_table(table, shuffle_info)\n')
        for fmd__nsqt in range(czaw__losa):
            gehgx__qmu += f"""  out_arr{fmd__nsqt} = info_to_array(info_from_table(out_table, {fmd__nsqt}), data._data[{fmd__nsqt}])
"""
        gehgx__qmu += '  delete_table(out_table)\n'
        gehgx__qmu += '  delete_table(table)\n'
        gehgx__qmu += (
            '  return init_multi_index(({},), data._names, data._name)\n'.
            format(', '.join(f'out_arr{fmd__nsqt}' for fmd__nsqt in range(
            czaw__losa))))
        vsuf__tanmf = {}
        exec(gehgx__qmu, {'bodo': bodo, 'array_to_info': array_to_info,
            'arr_info_list_to_table': arr_info_list_to_table,
            'reverse_shuffle_table': reverse_shuffle_table,
            'info_from_table': info_from_table, 'info_to_array':
            info_to_array, 'delete_table': delete_table, 'init_multi_index':
            bodo.hiframes.pd_multi_index_ext.init_multi_index}, vsuf__tanmf)
        qlnp__imsui = vsuf__tanmf['impl']
        return qlnp__imsui
    if bodo.hiframes.pd_index_ext.is_index_type(data):

        def impl_index(data, shuffle_info):
            jvtsm__zmsi = bodo.utils.conversion.index_to_array(data)
            lmq__nbji = reverse_shuffle(jvtsm__zmsi, shuffle_info)
            return bodo.utils.conversion.index_from_array(lmq__nbji)
        return impl_index

    def impl_arr(data, shuffle_info):
        zsqrl__sxgkh = [array_to_info(data)]
        azn__nupee = arr_info_list_to_table(zsqrl__sxgkh)
        gts__mth = reverse_shuffle_table(azn__nupee, shuffle_info)
        lmq__nbji = info_to_array(info_from_table(gts__mth, 0), data)
        delete_table(gts__mth)
        delete_table(azn__nupee)
        return lmq__nbji
    return impl_arr


@overload_method(DataFrameGroupByType, 'value_counts', inline='always',
    no_unliteral=True)
def groupby_value_counts(grp, normalize=False, sort=True, ascending=False,
    bins=None, dropna=True):
    cmemm__xvrkf = dict(normalize=normalize, sort=sort, bins=bins, dropna=
        dropna)
    nvg__kxzyi = dict(normalize=False, sort=True, bins=None, dropna=True)
    check_unsupported_args('Groupby.value_counts', cmemm__xvrkf, nvg__kxzyi,
        package_name='pandas', module_name='GroupBy')
    if len(grp.selection) > 1 or not grp.as_index:
        raise BodoError(
            "'DataFrameGroupBy' object has no attribute 'value_counts'")
    if not is_overload_constant_bool(ascending):
        raise BodoError(
            'Groupby.value_counts() ascending must be a constant boolean')
    tanyi__pblyn = get_overload_const_bool(ascending)
    akavl__igwc = grp.selection[0]
    gehgx__qmu = f"""def impl(grp, normalize=False, sort=True, ascending=False, bins=None, dropna=True):
"""
    wuhgr__yyibp = (
        f"lambda S: S.value_counts(ascending={tanyi__pblyn}, _index_name='{akavl__igwc}')"
        )
    gehgx__qmu += f'    return grp.apply({wuhgr__yyibp})\n'
    vsuf__tanmf = {}
    exec(gehgx__qmu, {'bodo': bodo}, vsuf__tanmf)
    qlnp__imsui = vsuf__tanmf['impl']
    return qlnp__imsui


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
    for wwg__ckb in groupby_unsupported_attr:
        overload_attribute(DataFrameGroupByType, wwg__ckb, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{wwg__ckb}'))
    for wwg__ckb in groupby_unsupported:
        overload_method(DataFrameGroupByType, wwg__ckb, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{wwg__ckb}'))
    for wwg__ckb in series_only_unsupported_attrs:
        overload_attribute(DataFrameGroupByType, wwg__ckb, no_unliteral=True)(
            create_unsupported_overload(f'SeriesGroupBy.{wwg__ckb}'))
    for wwg__ckb in series_only_unsupported:
        overload_method(DataFrameGroupByType, wwg__ckb, no_unliteral=True)(
            create_unsupported_overload(f'SeriesGroupBy.{wwg__ckb}'))
    for wwg__ckb in dataframe_only_unsupported:
        overload_method(DataFrameGroupByType, wwg__ckb, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{wwg__ckb}'))


_install_groupy_unsupported()
