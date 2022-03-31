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
        zro__ygzq = [('obj', fe_type.df_type)]
        super(GroupbyModel, self).__init__(dmm, fe_type, zro__ygzq)


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
        jhx__gpi = args[0]
        rgf__slqm = signature.return_type
        slxl__offjs = cgutils.create_struct_proxy(rgf__slqm)(context, builder)
        slxl__offjs.obj = jhx__gpi
        context.nrt.incref(builder, signature.args[0], jhx__gpi)
        return slxl__offjs._getvalue()
    if is_overload_constant_list(by_type):
        keys = tuple(get_overload_const_list(by_type))
    elif is_literal_type(by_type):
        keys = get_literal_value(by_type),
    else:
        assert False, 'Reached unreachable code in init_groupby; there is an validate_groupby_spec'
    selection = list(obj_type.columns)
    for nsxmy__ighv in keys:
        selection.remove(nsxmy__ighv)
    if is_overload_constant_bool(as_index_type):
        as_index = is_overload_true(as_index_type)
    else:
        as_index = True
    if is_overload_constant_bool(dropna_type):
        dropna = is_overload_true(dropna_type)
    else:
        dropna = True
    rgf__slqm = DataFrameGroupByType(obj_type, keys, tuple(selection),
        as_index, dropna, False)
    return rgf__slqm(obj_type, by_type, as_index_type, dropna_type), codegen


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
        grpby, sgk__nxe = args
        if isinstance(grpby, DataFrameGroupByType):
            series_select = False
            if isinstance(sgk__nxe, (tuple, list)):
                if len(set(sgk__nxe).difference(set(grpby.df_type.columns))
                    ) > 0:
                    raise_bodo_error(
                        'groupby: selected column {} not found in dataframe'
                        .format(set(sgk__nxe).difference(set(grpby.df_type.
                        columns))))
                selection = sgk__nxe
            else:
                if sgk__nxe not in grpby.df_type.columns:
                    raise_bodo_error(
                        'groupby: selected column {} not found in dataframe'
                        .format(sgk__nxe))
                selection = sgk__nxe,
                series_select = True
            yvcw__muyk = DataFrameGroupByType(grpby.df_type, grpby.keys,
                selection, grpby.as_index, grpby.dropna, True, series_select)
            return signature(yvcw__muyk, *args)


@infer_global(operator.getitem)
class GetItemDataFrameGroupBy(AbstractTemplate):

    def generic(self, args, kws):
        grpby, sgk__nxe = args
        if isinstance(grpby, DataFrameGroupByType) and is_literal_type(sgk__nxe
            ):
            yvcw__muyk = StaticGetItemDataFrameGroupBy.generic(self, (grpby,
                get_literal_value(sgk__nxe)), {}).return_type
            return signature(yvcw__muyk, *args)


GetItemDataFrameGroupBy.prefer_literal = True


@lower_builtin('static_getitem', DataFrameGroupByType, types.Any)
@lower_builtin(operator.getitem, DataFrameGroupByType, types.Any)
def static_getitem_df_groupby(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


def get_groupby_output_dtype(arr_type, func_name, index_type=None):
    arr_type = to_str_arr_if_dict_array(arr_type)
    mmcj__swy = arr_type == ArrayItemArrayType(string_array_type)
    wew__afp = arr_type.dtype
    if isinstance(wew__afp, bodo.hiframes.datetime_timedelta_ext.
        DatetimeTimeDeltaType):
        raise BodoError(
            f"""column type of {wew__afp} is not supported in groupby built-in function {func_name}.
{dt_err}"""
            )
    if func_name == 'median' and not isinstance(wew__afp, (Decimal128Type,
        types.Float, types.Integer)):
        return (None,
            'For median, only column of integer, float or Decimal type are allowed'
            )
    if func_name in ('first', 'last', 'sum', 'prod', 'min', 'max', 'count',
        'nunique', 'head') and isinstance(arr_type, (TupleArrayType,
        ArrayItemArrayType)):
        return (None,
            f'column type of list/tuple of {wew__afp} is not supported in groupby built-in function {func_name}'
            )
    if func_name in {'median', 'mean', 'var', 'std'} and isinstance(wew__afp,
        (Decimal128Type, types.Integer, types.Float)):
        return dtype_to_array_type(types.float64), 'ok'
    if not isinstance(wew__afp, (types.Integer, types.Float, types.Boolean)):
        if mmcj__swy or wew__afp == types.unicode_type:
            if func_name not in {'count', 'nunique', 'min', 'max', 'sum',
                'first', 'last', 'head'}:
                return (None,
                    f'column type of strings or list of strings is not supported in groupby built-in function {func_name}'
                    )
        else:
            if isinstance(wew__afp, bodo.PDCategoricalDtype):
                if func_name in ('min', 'max') and not wew__afp.ordered:
                    return (None,
                        f'categorical column must be ordered in groupby built-in function {func_name}'
                        )
            if func_name not in {'count', 'nunique', 'min', 'max', 'first',
                'last', 'head'}:
                return (None,
                    f'column type of {wew__afp} is not supported in groupby built-in function {func_name}'
                    )
    if isinstance(wew__afp, types.Boolean) and func_name in {'cumsum',
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
    wew__afp = arr_type.dtype
    if func_name in {'count'}:
        return IntDtype(types.int64)
    if func_name in {'sum', 'prod', 'min', 'max'}:
        if func_name in {'sum', 'prod'} and not isinstance(wew__afp, (types
            .Integer, types.Float)):
            raise BodoError(
                'pivot_table(): sum and prod operations require integer or float input'
                )
        if isinstance(wew__afp, types.Integer):
            return IntDtype(wew__afp)
        return wew__afp
    if func_name in {'mean', 'var', 'std'}:
        return types.float64
    raise BodoError('invalid pivot operation')


def check_args_kwargs(func_name, len_args, args, kws):
    if len(kws) > 0:
        gujgl__ofu = list(kws.keys())[0]
        raise BodoError(
            f"Groupby.{func_name}() got an unexpected keyword argument '{gujgl__ofu}'."
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
    for nsxmy__ighv in grp.keys:
        if multi_level_names:
            mnqi__wzxvt = nsxmy__ighv, ''
        else:
            mnqi__wzxvt = nsxmy__ighv
        deus__nzsm = grp.df_type.columns.index(nsxmy__ighv)
        data = to_str_arr_if_dict_array(grp.df_type.data[deus__nzsm])
        out_columns.append(mnqi__wzxvt)
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
        voxin__vll = tuple(grp.df_type.columns.index(grp.keys[dovml__prx]) for
            dovml__prx in range(len(grp.keys)))
        rek__reheb = tuple(grp.df_type.data[deus__nzsm] for deus__nzsm in
            voxin__vll)
        rek__reheb = tuple(to_str_arr_if_dict_array(jrv__qom) for jrv__qom in
            rek__reheb)
        index = MultiIndexType(rek__reheb, tuple(types.StringLiteral(
            nsxmy__ighv) for nsxmy__ighv in grp.keys))
    else:
        deus__nzsm = grp.df_type.columns.index(grp.keys[0])
        usxtp__mlnir = to_str_arr_if_dict_array(grp.df_type.data[deus__nzsm])
        index = bodo.hiframes.pd_index_ext.array_type_to_index(usxtp__mlnir,
            types.StringLiteral(grp.keys[0]))
    esv__jlvtp = {}
    tuyb__jyh = []
    if func_name in ('size', 'count'):
        kws = dict(kws) if kws else {}
        check_args_kwargs(func_name, 0, args, kws)
    if func_name == 'size':
        out_data.append(types.Array(types.int64, 1, 'C'))
        out_columns.append('size')
        esv__jlvtp[None, 'size'] = 'size'
    else:
        columns = (grp.selection if func_name != 'head' or grp.
            explicit_select else grp.df_type.columns)
        for howl__wirv in columns:
            deus__nzsm = grp.df_type.columns.index(howl__wirv)
            data = grp.df_type.data[deus__nzsm]
            data = to_str_arr_if_dict_array(data)
            qlo__ykwa = ColumnType.NonNumericalColumn.value
            if isinstance(data, (types.Array, IntegerArrayType)
                ) and isinstance(data.dtype, (types.Integer, types.Float)):
                qlo__ykwa = ColumnType.NumericalColumn.value
            if func_name == 'agg':
                try:
                    nfgmt__poftd = SeriesType(data.dtype, data, None,
                        string_type)
                    pvop__zqwub = get_const_func_output_type(func, (
                        nfgmt__poftd,), {}, typing_context, target_context)
                    if pvop__zqwub != ArrayItemArrayType(string_array_type):
                        pvop__zqwub = dtype_to_array_type(pvop__zqwub)
                    err_msg = 'ok'
                except:
                    raise_bodo_error(
                        'Groupy.agg()/Groupy.aggregate(): column {col} of type {type} is unsupported/not a valid input type for user defined function'
                        .format(col=howl__wirv, type=data.dtype))
            else:
                if func_name in ('first', 'last', 'min', 'max'):
                    kws = dict(kws) if kws else {}
                    gvsdj__usuaf = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', False)
                    zuqb__cxitw = args[1] if len(args) > 1 else kws.pop(
                        'min_count', -1)
                    qyhx__mihcs = dict(numeric_only=gvsdj__usuaf, min_count
                        =zuqb__cxitw)
                    rrrpp__uuxhn = dict(numeric_only=False, min_count=-1)
                    check_unsupported_args(f'Groupby.{func_name}',
                        qyhx__mihcs, rrrpp__uuxhn, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('sum', 'prod'):
                    kws = dict(kws) if kws else {}
                    gvsdj__usuaf = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', True)
                    zuqb__cxitw = args[1] if len(args) > 1 else kws.pop(
                        'min_count', 0)
                    qyhx__mihcs = dict(numeric_only=gvsdj__usuaf, min_count
                        =zuqb__cxitw)
                    rrrpp__uuxhn = dict(numeric_only=True, min_count=0)
                    check_unsupported_args(f'Groupby.{func_name}',
                        qyhx__mihcs, rrrpp__uuxhn, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('mean', 'median'):
                    kws = dict(kws) if kws else {}
                    gvsdj__usuaf = args[0] if len(args) > 0 else kws.pop(
                        'numeric_only', True)
                    qyhx__mihcs = dict(numeric_only=gvsdj__usuaf)
                    rrrpp__uuxhn = dict(numeric_only=True)
                    check_unsupported_args(f'Groupby.{func_name}',
                        qyhx__mihcs, rrrpp__uuxhn, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('idxmin', 'idxmax'):
                    kws = dict(kws) if kws else {}
                    snpm__dmq = args[0] if len(args) > 0 else kws.pop('axis', 0
                        )
                    jbrld__pbbdh = args[1] if len(args) > 1 else kws.pop(
                        'skipna', True)
                    qyhx__mihcs = dict(axis=snpm__dmq, skipna=jbrld__pbbdh)
                    rrrpp__uuxhn = dict(axis=0, skipna=True)
                    check_unsupported_args(f'Groupby.{func_name}',
                        qyhx__mihcs, rrrpp__uuxhn, package_name='pandas',
                        module_name='GroupBy')
                elif func_name in ('var', 'std'):
                    kws = dict(kws) if kws else {}
                    nciem__efn = args[0] if len(args) > 0 else kws.pop('ddof',
                        1)
                    qyhx__mihcs = dict(ddof=nciem__efn)
                    rrrpp__uuxhn = dict(ddof=1)
                    check_unsupported_args(f'Groupby.{func_name}',
                        qyhx__mihcs, rrrpp__uuxhn, package_name='pandas',
                        module_name='GroupBy')
                elif func_name == 'nunique':
                    kws = dict(kws) if kws else {}
                    dropna = args[0] if len(args) > 0 else kws.pop('dropna', 1)
                    check_args_kwargs(func_name, 1, args, kws)
                elif func_name == 'head':
                    if len(args) == 0:
                        kws.pop('n', None)
                pvop__zqwub, err_msg = get_groupby_output_dtype(data,
                    func_name, grp.df_type.index)
            if err_msg == 'ok':
                omaf__qnfjb = to_str_arr_if_dict_array(pvop__zqwub)
                out_data.append(omaf__qnfjb)
                out_columns.append(howl__wirv)
                if func_name == 'agg':
                    faal__xxm = bodo.ir.aggregate._get_udf_name(bodo.ir.
                        aggregate._get_const_agg_func(func, None))
                    esv__jlvtp[howl__wirv, faal__xxm] = howl__wirv
                else:
                    esv__jlvtp[howl__wirv, func_name] = howl__wirv
                out_column_type.append(qlo__ykwa)
            else:
                tuyb__jyh.append(err_msg)
    if func_name == 'sum':
        wapo__lit = any([(gwbrh__ypj == ColumnType.NumericalColumn.value) for
            gwbrh__ypj in out_column_type])
        if wapo__lit:
            out_data = [gwbrh__ypj for gwbrh__ypj, mbimh__pbc in zip(
                out_data, out_column_type) if mbimh__pbc != ColumnType.
                NonNumericalColumn.value]
            out_columns = [gwbrh__ypj for gwbrh__ypj, mbimh__pbc in zip(
                out_columns, out_column_type) if mbimh__pbc != ColumnType.
                NonNumericalColumn.value]
            esv__jlvtp = {}
            for howl__wirv in out_columns:
                if grp.as_index is False and howl__wirv in grp.keys:
                    continue
                esv__jlvtp[howl__wirv, func_name] = howl__wirv
    pxmr__qss = len(tuyb__jyh)
    if len(out_data) == 0:
        if pxmr__qss == 0:
            raise BodoError('No columns in output.')
        else:
            raise BodoError(
                'No columns in output. {} column{} dropped for following reasons: {}'
                .format(pxmr__qss, ' was' if pxmr__qss == 1 else 's were',
                ','.join(tuyb__jyh)))
    sjlyt__mngrr = DataFrameType(tuple(out_data), index, tuple(out_columns))
    if (len(grp.selection) == 1 and grp.series_select and grp.as_index or 
        func_name == 'size' and grp.as_index):
        if isinstance(out_data[0], IntegerArrayType):
            yctah__tfa = IntDtype(out_data[0].dtype)
        else:
            yctah__tfa = out_data[0].dtype
        gwrv__hhgr = (types.none if func_name == 'size' else types.
            StringLiteral(grp.selection[0]))
        sjlyt__mngrr = SeriesType(yctah__tfa, index=index, name_typ=gwrv__hhgr)
    return signature(sjlyt__mngrr, *args), esv__jlvtp


def get_agg_funcname_and_outtyp(grp, col, f_val, typing_context, target_context
    ):
    dyqfn__rueh = True
    if isinstance(f_val, str):
        dyqfn__rueh = False
        yvvvn__znxo = f_val
    elif is_overload_constant_str(f_val):
        dyqfn__rueh = False
        yvvvn__znxo = get_overload_const_str(f_val)
    elif bodo.utils.typing.is_builtin_function(f_val):
        dyqfn__rueh = False
        yvvvn__znxo = bodo.utils.typing.get_builtin_function_name(f_val)
    if not dyqfn__rueh:
        if yvvvn__znxo not in bodo.ir.aggregate.supported_agg_funcs[:-1]:
            raise BodoError(f'unsupported aggregate function {yvvvn__znxo}')
        yvcw__muyk = DataFrameGroupByType(grp.df_type, grp.keys, (col,),
            grp.as_index, grp.dropna, True, True)
        out_tp = get_agg_typ(yvcw__muyk, (), yvvvn__znxo, typing_context,
            target_context)[0].return_type
    else:
        if is_expr(f_val, 'make_function'):
            hyuww__jkyr = types.functions.MakeFunctionLiteral(f_val)
        else:
            hyuww__jkyr = f_val
        validate_udf('agg', hyuww__jkyr)
        func = get_overload_const_func(hyuww__jkyr, None)
        hfumn__hgao = func.code if hasattr(func, 'code') else func.__code__
        yvvvn__znxo = hfumn__hgao.co_name
        yvcw__muyk = DataFrameGroupByType(grp.df_type, grp.keys, (col,),
            grp.as_index, grp.dropna, True, True)
        out_tp = get_agg_typ(yvcw__muyk, (), 'agg', typing_context,
            target_context, hyuww__jkyr)[0].return_type
    return yvvvn__znxo, out_tp


def resolve_agg(grp, args, kws, typing_context, target_context):
    func = get_call_expr_arg('agg', args, dict(kws), 0, 'func', default=
        types.none)
    jbnrp__gpyax = kws and all(isinstance(wmpky__bqaco, types.Tuple) and 
        len(wmpky__bqaco) == 2 for wmpky__bqaco in kws.values())
    if is_overload_none(func) and not jbnrp__gpyax:
        raise_bodo_error("Groupby.agg()/aggregate(): Must provide 'func'")
    if len(args) > 1 or kws and not jbnrp__gpyax:
        raise_bodo_error(
            'Groupby.agg()/aggregate(): passing extra arguments to functions not supported yet.'
            )
    std__qjox = False

    def _append_out_type(grp, out_data, out_tp):
        if grp.as_index is False:
            out_data.append(out_tp.data[len(grp.keys)])
        else:
            out_data.append(out_tp.data)
    if jbnrp__gpyax or is_overload_constant_dict(func):
        if jbnrp__gpyax:
            afhso__dnv = [get_literal_value(xhifn__zuycb) for xhifn__zuycb,
                dwo__toes in kws.values()]
            aepe__msftw = [get_literal_value(eqrrp__cxt) for dwo__toes,
                eqrrp__cxt in kws.values()]
        else:
            chydz__iodcr = get_overload_constant_dict(func)
            afhso__dnv = tuple(chydz__iodcr.keys())
            aepe__msftw = tuple(chydz__iodcr.values())
        if 'head' in aepe__msftw:
            raise BodoError(
                'Groupby.agg()/aggregate(): head cannot be mixed with other groupby operations.'
                )
        if any(howl__wirv not in grp.selection and howl__wirv not in grp.
            keys for howl__wirv in afhso__dnv):
            raise_bodo_error(
                f'Selected column names {afhso__dnv} not all available in dataframe column names {grp.selection}'
                )
        multi_level_names = any(isinstance(f_val, (tuple, list)) for f_val in
            aepe__msftw)
        if jbnrp__gpyax and multi_level_names:
            raise_bodo_error(
                'Groupby.agg()/aggregate(): cannot pass multiple functions in a single pd.NamedAgg()'
                )
        esv__jlvtp = {}
        out_columns = []
        out_data = []
        out_column_type = []
        jit__cyz = []
        if not grp.as_index:
            get_keys_not_as_index(grp, out_columns, out_data,
                out_column_type, multi_level_names=multi_level_names)
        for ynf__zltc, f_val in zip(afhso__dnv, aepe__msftw):
            if isinstance(f_val, (tuple, list)):
                eaad__gwb = 0
                for hyuww__jkyr in f_val:
                    yvvvn__znxo, out_tp = get_agg_funcname_and_outtyp(grp,
                        ynf__zltc, hyuww__jkyr, typing_context, target_context)
                    std__qjox = yvvvn__znxo in list_cumulative
                    if yvvvn__znxo == '<lambda>' and len(f_val) > 1:
                        yvvvn__znxo = '<lambda_' + str(eaad__gwb) + '>'
                        eaad__gwb += 1
                    out_columns.append((ynf__zltc, yvvvn__znxo))
                    esv__jlvtp[ynf__zltc, yvvvn__znxo] = ynf__zltc, yvvvn__znxo
                    _append_out_type(grp, out_data, out_tp)
            else:
                yvvvn__znxo, out_tp = get_agg_funcname_and_outtyp(grp,
                    ynf__zltc, f_val, typing_context, target_context)
                std__qjox = yvvvn__znxo in list_cumulative
                if multi_level_names:
                    out_columns.append((ynf__zltc, yvvvn__znxo))
                    esv__jlvtp[ynf__zltc, yvvvn__znxo] = ynf__zltc, yvvvn__znxo
                elif not jbnrp__gpyax:
                    out_columns.append(ynf__zltc)
                    esv__jlvtp[ynf__zltc, yvvvn__znxo] = ynf__zltc
                elif jbnrp__gpyax:
                    jit__cyz.append(yvvvn__znxo)
                _append_out_type(grp, out_data, out_tp)
        if jbnrp__gpyax:
            for dovml__prx, wzyg__hkjo in enumerate(kws.keys()):
                out_columns.append(wzyg__hkjo)
                esv__jlvtp[afhso__dnv[dovml__prx], jit__cyz[dovml__prx]
                    ] = wzyg__hkjo
        if std__qjox:
            index = grp.df_type.index
        else:
            index = out_tp.index
        sjlyt__mngrr = DataFrameType(tuple(out_data), index, tuple(out_columns)
            )
        return signature(sjlyt__mngrr, *args), esv__jlvtp
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
        eaad__gwb = 0
        if not grp.as_index:
            get_keys_not_as_index(grp, out_columns, out_data, out_column_type)
        esv__jlvtp = {}
        idkf__vqk = grp.selection[0]
        for f_val in func.types:
            yvvvn__znxo, out_tp = get_agg_funcname_and_outtyp(grp,
                idkf__vqk, f_val, typing_context, target_context)
            std__qjox = yvvvn__znxo in list_cumulative
            if yvvvn__znxo == '<lambda>':
                yvvvn__znxo = '<lambda_' + str(eaad__gwb) + '>'
                eaad__gwb += 1
            out_columns.append(yvvvn__znxo)
            esv__jlvtp[idkf__vqk, yvvvn__znxo] = yvvvn__znxo
            _append_out_type(grp, out_data, out_tp)
        if std__qjox:
            index = grp.df_type.index
        else:
            index = out_tp.index
        sjlyt__mngrr = DataFrameType(tuple(out_data), index, tuple(out_columns)
            )
        return signature(sjlyt__mngrr, *args), esv__jlvtp
    yvvvn__znxo = ''
    if types.unliteral(func) == types.unicode_type:
        yvvvn__znxo = get_overload_const_str(func)
    if bodo.utils.typing.is_builtin_function(func):
        yvvvn__znxo = bodo.utils.typing.get_builtin_function_name(func)
    if yvvvn__znxo:
        args = args[1:]
        kws.pop('func', None)
        return get_agg_typ(grp, args, yvvvn__znxo, typing_context, kws)
    validate_udf('agg', func)
    return get_agg_typ(grp, args, 'agg', typing_context, target_context, func)


def resolve_transformative(grp, args, kws, msg, name_operation):
    index = grp.df_type.index
    out_columns = []
    out_data = []
    if name_operation in list_cumulative:
        kws = dict(kws) if kws else {}
        snpm__dmq = args[0] if len(args) > 0 else kws.pop('axis', 0)
        gvsdj__usuaf = args[1] if len(args) > 1 else kws.pop('numeric_only',
            False)
        jbrld__pbbdh = args[2] if len(args) > 2 else kws.pop('skipna', 1)
        qyhx__mihcs = dict(axis=snpm__dmq, numeric_only=gvsdj__usuaf)
        rrrpp__uuxhn = dict(axis=0, numeric_only=False)
        check_unsupported_args(f'Groupby.{name_operation}', qyhx__mihcs,
            rrrpp__uuxhn, package_name='pandas', module_name='GroupBy')
        check_args_kwargs(name_operation, 3, args, kws)
    elif name_operation == 'shift':
        lpao__vpw = args[0] if len(args) > 0 else kws.pop('periods', 1)
        imzvm__pjq = args[1] if len(args) > 1 else kws.pop('freq', None)
        snpm__dmq = args[2] if len(args) > 2 else kws.pop('axis', 0)
        eklzu__cfb = args[3] if len(args) > 3 else kws.pop('fill_value', None)
        qyhx__mihcs = dict(freq=imzvm__pjq, axis=snpm__dmq, fill_value=
            eklzu__cfb)
        rrrpp__uuxhn = dict(freq=None, axis=0, fill_value=None)
        check_unsupported_args(f'Groupby.{name_operation}', qyhx__mihcs,
            rrrpp__uuxhn, package_name='pandas', module_name='GroupBy')
        check_args_kwargs(name_operation, 4, args, kws)
    elif name_operation == 'transform':
        kws = dict(kws)
        qgxr__fxit = args[0] if len(args) > 0 else kws.pop('func', None)
        ygyg__uld = kws.pop('engine', None)
        cevwn__qzm = kws.pop('engine_kwargs', None)
        qyhx__mihcs = dict(engine=ygyg__uld, engine_kwargs=cevwn__qzm)
        rrrpp__uuxhn = dict(engine=None, engine_kwargs=None)
        check_unsupported_args(f'Groupby.transform', qyhx__mihcs,
            rrrpp__uuxhn, package_name='pandas', module_name='GroupBy')
    esv__jlvtp = {}
    for howl__wirv in grp.selection:
        out_columns.append(howl__wirv)
        esv__jlvtp[howl__wirv, name_operation] = howl__wirv
        deus__nzsm = grp.df_type.columns.index(howl__wirv)
        data = grp.df_type.data[deus__nzsm]
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
            pvop__zqwub, err_msg = get_groupby_output_dtype(data,
                get_literal_value(qgxr__fxit), grp.df_type.index)
            if err_msg == 'ok':
                data = pvop__zqwub
            else:
                raise BodoError(
                    f'column type of {data.dtype} is not supported by {args[0]} yet.\n'
                    )
        out_data.append(data)
    if len(out_data) == 0:
        raise BodoError('No columns in output.')
    sjlyt__mngrr = DataFrameType(tuple(out_data), index, tuple(out_columns))
    if len(grp.selection) == 1 and grp.series_select and grp.as_index:
        sjlyt__mngrr = SeriesType(out_data[0].dtype, data=out_data[0],
            index=index, name_typ=types.StringLiteral(grp.selection[0]))
    return signature(sjlyt__mngrr, *args), esv__jlvtp


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
        mhh__blqxt = _get_groupby_apply_udf_out_type(func, grp, f_args, kws,
            self.context, numba.core.registry.cpu_target.target_context)
        fzw__eqol = isinstance(mhh__blqxt, (SeriesType,
            HeterogeneousSeriesType)
            ) and mhh__blqxt.const_info is not None or not isinstance(
            mhh__blqxt, (SeriesType, DataFrameType))
        if fzw__eqol:
            out_data = []
            out_columns = []
            out_column_type = []
            if not grp.as_index:
                get_keys_not_as_index(grp, out_columns, out_data,
                    out_column_type)
                lkdea__czb = NumericIndexType(types.int64, types.none)
            elif len(grp.keys) > 1:
                voxin__vll = tuple(grp.df_type.columns.index(grp.keys[
                    dovml__prx]) for dovml__prx in range(len(grp.keys)))
                rek__reheb = tuple(grp.df_type.data[deus__nzsm] for
                    deus__nzsm in voxin__vll)
                rek__reheb = tuple(to_str_arr_if_dict_array(jrv__qom) for
                    jrv__qom in rek__reheb)
                lkdea__czb = MultiIndexType(rek__reheb, tuple(types.literal
                    (nsxmy__ighv) for nsxmy__ighv in grp.keys))
            else:
                deus__nzsm = grp.df_type.columns.index(grp.keys[0])
                usxtp__mlnir = grp.df_type.data[deus__nzsm]
                usxtp__mlnir = to_str_arr_if_dict_array(usxtp__mlnir)
                lkdea__czb = bodo.hiframes.pd_index_ext.array_type_to_index(
                    usxtp__mlnir, types.literal(grp.keys[0]))
            out_data = tuple(out_data)
            out_columns = tuple(out_columns)
        else:
            omg__cmnve = tuple(grp.df_type.data[grp.df_type.columns.index(
                howl__wirv)] for howl__wirv in grp.keys)
            omg__cmnve = tuple(to_str_arr_if_dict_array(jrv__qom) for
                jrv__qom in omg__cmnve)
            inft__bpe = tuple(types.literal(wmpky__bqaco) for wmpky__bqaco in
                grp.keys) + get_index_name_types(mhh__blqxt.index)
            if not grp.as_index:
                omg__cmnve = types.Array(types.int64, 1, 'C'),
                inft__bpe = (types.none,) + get_index_name_types(mhh__blqxt
                    .index)
            lkdea__czb = MultiIndexType(omg__cmnve +
                get_index_data_arr_types(mhh__blqxt.index), inft__bpe)
        if fzw__eqol:
            if isinstance(mhh__blqxt, HeterogeneousSeriesType):
                dwo__toes, smsb__jhf = mhh__blqxt.const_info
                aoxpl__ujaq = tuple(dtype_to_array_type(jrv__qom) for
                    jrv__qom in mhh__blqxt.data.types)
                kjna__ykbye = DataFrameType(out_data + aoxpl__ujaq,
                    lkdea__czb, out_columns + smsb__jhf)
            elif isinstance(mhh__blqxt, SeriesType):
                yqt__hlw, smsb__jhf = mhh__blqxt.const_info
                aoxpl__ujaq = tuple(dtype_to_array_type(mhh__blqxt.dtype) for
                    dwo__toes in range(yqt__hlw))
                kjna__ykbye = DataFrameType(out_data + aoxpl__ujaq,
                    lkdea__czb, out_columns + smsb__jhf)
            else:
                rstu__tacg = get_udf_out_arr_type(mhh__blqxt)
                if not grp.as_index:
                    kjna__ykbye = DataFrameType(out_data + (rstu__tacg,),
                        lkdea__czb, out_columns + ('',))
                else:
                    kjna__ykbye = SeriesType(rstu__tacg.dtype, rstu__tacg,
                        lkdea__czb, None)
        elif isinstance(mhh__blqxt, SeriesType):
            kjna__ykbye = SeriesType(mhh__blqxt.dtype, mhh__blqxt.data,
                lkdea__czb, mhh__blqxt.name_typ)
        else:
            kjna__ykbye = DataFrameType(mhh__blqxt.data, lkdea__czb,
                mhh__blqxt.columns)
        adyr__iebk = gen_apply_pysig(len(f_args), kws.keys())
        vjy__ggmku = (func, *f_args) + tuple(kws.values())
        return signature(kjna__ykbye, *vjy__ggmku).replace(pysig=adyr__iebk)

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
    wjoc__pmb = grp.df_type
    if grp.explicit_select:
        if len(grp.selection) == 1:
            ynf__zltc = grp.selection[0]
            rstu__tacg = wjoc__pmb.data[wjoc__pmb.columns.index(ynf__zltc)]
            rstu__tacg = to_str_arr_if_dict_array(rstu__tacg)
            lukqy__psrsg = SeriesType(rstu__tacg.dtype, rstu__tacg,
                wjoc__pmb.index, types.literal(ynf__zltc))
        else:
            rmi__kia = tuple(wjoc__pmb.data[wjoc__pmb.columns.index(
                howl__wirv)] for howl__wirv in grp.selection)
            rmi__kia = tuple(to_str_arr_if_dict_array(jrv__qom) for
                jrv__qom in rmi__kia)
            lukqy__psrsg = DataFrameType(rmi__kia, wjoc__pmb.index, tuple(
                grp.selection))
    else:
        lukqy__psrsg = wjoc__pmb
    hfuy__uxbyi = lukqy__psrsg,
    hfuy__uxbyi += tuple(f_args)
    try:
        mhh__blqxt = get_const_func_output_type(func, hfuy__uxbyi, kws,
            typing_context, target_context)
    except Exception as ahxk__zyy:
        raise_bodo_error(get_udf_error_msg('GroupBy.apply()', ahxk__zyy),
            getattr(ahxk__zyy, 'loc', None))
    return mhh__blqxt


def resolve_obj_pipe(self, grp, args, kws, obj_name):
    kws = dict(kws)
    func = args[0] if len(args) > 0 else kws.pop('func', None)
    f_args = tuple(args[1:]) if len(args) > 0 else ()
    hfuy__uxbyi = (grp,) + f_args
    try:
        mhh__blqxt = get_const_func_output_type(func, hfuy__uxbyi, kws,
            self.context, numba.core.registry.cpu_target.target_context, False)
    except Exception as ahxk__zyy:
        raise_bodo_error(get_udf_error_msg(f'{obj_name}.pipe()', ahxk__zyy),
            getattr(ahxk__zyy, 'loc', None))
    adyr__iebk = gen_apply_pysig(len(f_args), kws.keys())
    vjy__ggmku = (func, *f_args) + tuple(kws.values())
    return signature(mhh__blqxt, *vjy__ggmku).replace(pysig=adyr__iebk)


def gen_apply_pysig(n_args, kws):
    okyc__draq = ', '.join(f'arg{dovml__prx}' for dovml__prx in range(n_args))
    okyc__draq = okyc__draq + ', ' if okyc__draq else ''
    xvo__vyll = ', '.join(f"{wkprl__yhl} = ''" for wkprl__yhl in kws)
    psbzo__xsit = f'def apply_stub(func, {okyc__draq}{xvo__vyll}):\n'
    psbzo__xsit += '    pass\n'
    vrwgl__sxpuu = {}
    exec(psbzo__xsit, {}, vrwgl__sxpuu)
    zer__ajqj = vrwgl__sxpuu['apply_stub']
    return numba.core.utils.pysignature(zer__ajqj)


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
        pvop__zqwub = get_pivot_output_dtype(data, aggfunc.literal_value)
        ztc__uvh = dtype_to_array_type(pvop__zqwub)
        if is_overload_none(_pivot_values):
            raise_bodo_error(
                'Dataframe.pivot_table() requires explicit annotation to determine output columns. For more information, see: https://docs.bodo.ai/latest/source/programming_with_bodo/pandas.html'
                )
        jskn__gyrsp = _pivot_values.meta
        hbw__dgrqf = len(jskn__gyrsp)
        deus__nzsm = df.columns.index(index)
        usxtp__mlnir = df.data[deus__nzsm]
        usxtp__mlnir = to_str_arr_if_dict_array(usxtp__mlnir)
        mnf__smno = bodo.hiframes.pd_index_ext.array_type_to_index(usxtp__mlnir
            , types.StringLiteral(index))
        xsx__poz = DataFrameType((ztc__uvh,) * hbw__dgrqf, mnf__smno, tuple
            (jskn__gyrsp))
        return signature(xsx__poz, *args)


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
        ztc__uvh = types.Array(types.int64, 1, 'C')
        jskn__gyrsp = _pivot_values.meta
        hbw__dgrqf = len(jskn__gyrsp)
        mnf__smno = bodo.hiframes.pd_index_ext.array_type_to_index(
            to_str_arr_if_dict_array(index.data), types.StringLiteral('index'))
        xsx__poz = DataFrameType((ztc__uvh,) * hbw__dgrqf, mnf__smno, tuple
            (jskn__gyrsp))
        return signature(xsx__poz, *args)


CrossTabTyper._no_unliteral = True


@lower_builtin(crosstab_dummy, types.VarArg(types.Any))
def lower_crosstab_dummy(context, builder, sig, args):
    return context.get_constant_null(sig.return_type)


def get_group_indices(keys, dropna, _is_parallel):
    return np.arange(len(keys))


@overload(get_group_indices)
def get_group_indices_overload(keys, dropna, _is_parallel):
    psbzo__xsit = 'def impl(keys, dropna, _is_parallel):\n'
    psbzo__xsit += (
        "    ev = bodo.utils.tracing.Event('get_group_indices', _is_parallel)\n"
        )
    psbzo__xsit += '    info_list = [{}]\n'.format(', '.join(
        f'array_to_info(keys[{dovml__prx}])' for dovml__prx in range(len(
        keys.types))))
    psbzo__xsit += '    table = arr_info_list_to_table(info_list)\n'
    psbzo__xsit += '    group_labels = np.empty(len(keys[0]), np.int64)\n'
    psbzo__xsit += '    sort_idx = np.empty(len(keys[0]), np.int64)\n'
    psbzo__xsit += """    ngroups = get_groupby_labels(table, group_labels.ctypes, sort_idx.ctypes, dropna, _is_parallel)
"""
    psbzo__xsit += '    delete_table_decref_arrays(table)\n'
    psbzo__xsit += '    ev.finalize()\n'
    psbzo__xsit += '    return sort_idx, group_labels, ngroups\n'
    vrwgl__sxpuu = {}
    exec(psbzo__xsit, {'bodo': bodo, 'np': np, 'get_groupby_labels':
        get_groupby_labels, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table,
        'delete_table_decref_arrays': delete_table_decref_arrays}, vrwgl__sxpuu
        )
    asdi__ayrx = vrwgl__sxpuu['impl']
    return asdi__ayrx


@numba.njit(no_cpython_wrapper=True)
def generate_slices(labels, ngroups):
    uxq__pluoe = len(labels)
    azwpq__ifu = np.zeros(ngroups, dtype=np.int64)
    dfi__oum = np.zeros(ngroups, dtype=np.int64)
    rwu__xma = 0
    whu__xtl = 0
    for dovml__prx in range(uxq__pluoe):
        qgcc__uxnf = labels[dovml__prx]
        if qgcc__uxnf < 0:
            rwu__xma += 1
        else:
            whu__xtl += 1
            if dovml__prx == uxq__pluoe - 1 or qgcc__uxnf != labels[
                dovml__prx + 1]:
                azwpq__ifu[qgcc__uxnf] = rwu__xma
                dfi__oum[qgcc__uxnf] = rwu__xma + whu__xtl
                rwu__xma += whu__xtl
                whu__xtl = 0
    return azwpq__ifu, dfi__oum


def shuffle_dataframe(df, keys, _is_parallel):
    return df, keys, _is_parallel


@overload(shuffle_dataframe, prefer_literal=True)
def overload_shuffle_dataframe(df, keys, _is_parallel):
    asdi__ayrx, dwo__toes = gen_shuffle_dataframe(df, keys, _is_parallel)
    return asdi__ayrx


def gen_shuffle_dataframe(df, keys, _is_parallel):
    yqt__hlw = len(df.columns)
    lvmni__mhj = len(keys.types)
    assert is_overload_constant_bool(_is_parallel
        ), 'shuffle_dataframe: _is_parallel is not a constant'
    psbzo__xsit = 'def impl(df, keys, _is_parallel):\n'
    if is_overload_false(_is_parallel):
        psbzo__xsit += '  return df, keys, get_null_shuffle_info()\n'
        vrwgl__sxpuu = {}
        exec(psbzo__xsit, {'get_null_shuffle_info': get_null_shuffle_info},
            vrwgl__sxpuu)
        asdi__ayrx = vrwgl__sxpuu['impl']
        return asdi__ayrx
    for dovml__prx in range(yqt__hlw):
        psbzo__xsit += f"""  in_arr{dovml__prx} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {dovml__prx})
"""
    psbzo__xsit += f"""  in_index_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))
"""
    psbzo__xsit += '  info_list = [{}, {}, {}]\n'.format(', '.join(
        f'array_to_info(keys[{dovml__prx}])' for dovml__prx in range(
        lvmni__mhj)), ', '.join(f'array_to_info(in_arr{dovml__prx})' for
        dovml__prx in range(yqt__hlw)), 'array_to_info(in_index_arr)')
    psbzo__xsit += '  table = arr_info_list_to_table(info_list)\n'
    psbzo__xsit += (
        f'  out_table = shuffle_table(table, {lvmni__mhj}, _is_parallel, 1)\n')
    for dovml__prx in range(lvmni__mhj):
        psbzo__xsit += f"""  out_key{dovml__prx} = info_to_array(info_from_table(out_table, {dovml__prx}), keys{dovml__prx}_typ)
"""
    for dovml__prx in range(yqt__hlw):
        psbzo__xsit += f"""  out_arr{dovml__prx} = info_to_array(info_from_table(out_table, {dovml__prx + lvmni__mhj}), in_arr{dovml__prx}_typ)
"""
    psbzo__xsit += f"""  out_arr_index = info_to_array(info_from_table(out_table, {lvmni__mhj + yqt__hlw}), ind_arr_typ)
"""
    psbzo__xsit += '  shuffle_info = get_shuffle_info(out_table)\n'
    psbzo__xsit += '  delete_table(out_table)\n'
    psbzo__xsit += '  delete_table(table)\n'
    out_data = ', '.join(f'out_arr{dovml__prx}' for dovml__prx in range(
        yqt__hlw))
    psbzo__xsit += (
        '  out_index = bodo.utils.conversion.index_from_array(out_arr_index)\n'
        )
    psbzo__xsit += f"""  out_df = bodo.hiframes.pd_dataframe_ext.init_dataframe(({out_data},), out_index, {gen_const_tup(df.columns)})
"""
    psbzo__xsit += '  return out_df, ({},), shuffle_info\n'.format(', '.
        join(f'out_key{dovml__prx}' for dovml__prx in range(lvmni__mhj)))
    fqqj__pyui = {'bodo': bodo, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'shuffle_table':
        shuffle_table, 'info_from_table': info_from_table, 'info_to_array':
        info_to_array, 'delete_table': delete_table, 'get_shuffle_info':
        get_shuffle_info, 'ind_arr_typ': types.Array(types.int64, 1, 'C') if
        isinstance(df.index, RangeIndexType) else df.index.data}
    fqqj__pyui.update({f'keys{dovml__prx}_typ': keys.types[dovml__prx] for
        dovml__prx in range(lvmni__mhj)})
    fqqj__pyui.update({f'in_arr{dovml__prx}_typ': df.data[dovml__prx] for
        dovml__prx in range(yqt__hlw)})
    vrwgl__sxpuu = {}
    exec(psbzo__xsit, fqqj__pyui, vrwgl__sxpuu)
    asdi__ayrx = vrwgl__sxpuu['impl']
    return asdi__ayrx, fqqj__pyui


def reverse_shuffle(data, shuffle_info):
    return data


@overload(reverse_shuffle)
def overload_reverse_shuffle(data, shuffle_info):
    if isinstance(data, bodo.hiframes.pd_multi_index_ext.MultiIndexType):
        akapd__kbxw = len(data.array_types)
        psbzo__xsit = 'def impl(data, shuffle_info):\n'
        psbzo__xsit += '  info_list = [{}]\n'.format(', '.join(
            f'array_to_info(data._data[{dovml__prx}])' for dovml__prx in
            range(akapd__kbxw)))
        psbzo__xsit += '  table = arr_info_list_to_table(info_list)\n'
        psbzo__xsit += (
            '  out_table = reverse_shuffle_table(table, shuffle_info)\n')
        for dovml__prx in range(akapd__kbxw):
            psbzo__xsit += f"""  out_arr{dovml__prx} = info_to_array(info_from_table(out_table, {dovml__prx}), data._data[{dovml__prx}])
"""
        psbzo__xsit += '  delete_table(out_table)\n'
        psbzo__xsit += '  delete_table(table)\n'
        psbzo__xsit += (
            '  return init_multi_index(({},), data._names, data._name)\n'.
            format(', '.join(f'out_arr{dovml__prx}' for dovml__prx in range
            (akapd__kbxw))))
        vrwgl__sxpuu = {}
        exec(psbzo__xsit, {'bodo': bodo, 'array_to_info': array_to_info,
            'arr_info_list_to_table': arr_info_list_to_table,
            'reverse_shuffle_table': reverse_shuffle_table,
            'info_from_table': info_from_table, 'info_to_array':
            info_to_array, 'delete_table': delete_table, 'init_multi_index':
            bodo.hiframes.pd_multi_index_ext.init_multi_index}, vrwgl__sxpuu)
        asdi__ayrx = vrwgl__sxpuu['impl']
        return asdi__ayrx
    if bodo.hiframes.pd_index_ext.is_index_type(data):

        def impl_index(data, shuffle_info):
            uquzo__qas = bodo.utils.conversion.index_to_array(data)
            omaf__qnfjb = reverse_shuffle(uquzo__qas, shuffle_info)
            return bodo.utils.conversion.index_from_array(omaf__qnfjb)
        return impl_index

    def impl_arr(data, shuffle_info):
        okfac__cfdog = [array_to_info(data)]
        rcf__wtct = arr_info_list_to_table(okfac__cfdog)
        wubd__bcs = reverse_shuffle_table(rcf__wtct, shuffle_info)
        omaf__qnfjb = info_to_array(info_from_table(wubd__bcs, 0), data)
        delete_table(wubd__bcs)
        delete_table(rcf__wtct)
        return omaf__qnfjb
    return impl_arr


@overload_method(DataFrameGroupByType, 'value_counts', inline='always',
    no_unliteral=True)
def groupby_value_counts(grp, normalize=False, sort=True, ascending=False,
    bins=None, dropna=True):
    qyhx__mihcs = dict(normalize=normalize, sort=sort, bins=bins, dropna=dropna
        )
    rrrpp__uuxhn = dict(normalize=False, sort=True, bins=None, dropna=True)
    check_unsupported_args('Groupby.value_counts', qyhx__mihcs,
        rrrpp__uuxhn, package_name='pandas', module_name='GroupBy')
    if len(grp.selection) > 1 or not grp.as_index:
        raise BodoError(
            "'DataFrameGroupBy' object has no attribute 'value_counts'")
    if not is_overload_constant_bool(ascending):
        raise BodoError(
            'Groupby.value_counts() ascending must be a constant boolean')
    ucntc__hptue = get_overload_const_bool(ascending)
    qqdc__mxcv = grp.selection[0]
    psbzo__xsit = f"""def impl(grp, normalize=False, sort=True, ascending=False, bins=None, dropna=True):
"""
    eka__uhcu = (
        f"lambda S: S.value_counts(ascending={ucntc__hptue}, _index_name='{qqdc__mxcv}')"
        )
    psbzo__xsit += f'    return grp.apply({eka__uhcu})\n'
    vrwgl__sxpuu = {}
    exec(psbzo__xsit, {'bodo': bodo}, vrwgl__sxpuu)
    asdi__ayrx = vrwgl__sxpuu['impl']
    return asdi__ayrx


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
    for enx__jprvc in groupby_unsupported_attr:
        overload_attribute(DataFrameGroupByType, enx__jprvc, no_unliteral=True
            )(create_unsupported_overload(f'DataFrameGroupBy.{enx__jprvc}'))
    for enx__jprvc in groupby_unsupported:
        overload_method(DataFrameGroupByType, enx__jprvc, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{enx__jprvc}'))
    for enx__jprvc in series_only_unsupported_attrs:
        overload_attribute(DataFrameGroupByType, enx__jprvc, no_unliteral=True
            )(create_unsupported_overload(f'SeriesGroupBy.{enx__jprvc}'))
    for enx__jprvc in series_only_unsupported:
        overload_method(DataFrameGroupByType, enx__jprvc, no_unliteral=True)(
            create_unsupported_overload(f'SeriesGroupBy.{enx__jprvc}'))
    for enx__jprvc in dataframe_only_unsupported:
        overload_method(DataFrameGroupByType, enx__jprvc, no_unliteral=True)(
            create_unsupported_overload(f'DataFrameGroupBy.{enx__jprvc}'))


_install_groupy_unsupported()
