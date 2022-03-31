"""IR node for the groupby, pivot and cross_tabulation"""
import ctypes
import operator
import types as pytypes
from collections import defaultdict, namedtuple
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, compiler, ir, ir_utils, types
from numba.core.analysis import compute_use_defs
from numba.core.ir_utils import build_definitions, compile_to_numba_ir, find_callname, find_const, find_topo_order, get_definition, get_ir_of_code, get_name_var_table, guard, is_getitem, mk_unique_var, next_label, remove_dels, replace_arg_nodes, replace_var_names, replace_vars_inner, visit_vars_inner
from numba.core.typing import signature
from numba.core.typing.templates import AbstractTemplate, infer_global
from numba.extending import intrinsic, lower_builtin
from numba.parfors.parfor import Parfor, unwrap_parfor_blocks, wrap_parfor_blocks
import bodo
from bodo.hiframes.datetime_date_ext import DatetimeDateArrayType
from bodo.hiframes.pd_series_ext import SeriesType
from bodo.libs.array import arr_info_list_to_table, array_to_info, delete_info_decref_array, delete_table, delete_table_decref_arrays, groupby_and_aggregate, info_from_table, info_to_array, pivot_groupby_and_aggregate
from bodo.libs.array_item_arr_ext import ArrayItemArrayType, pre_alloc_array_item_array
from bodo.libs.binary_arr_ext import BinaryArrayType, pre_alloc_binary_array
from bodo.libs.bool_arr_ext import BooleanArrayType
from bodo.libs.decimal_arr_ext import DecimalArrayType, alloc_decimal_array
from bodo.libs.int_arr_ext import IntDtype, IntegerArrayType
from bodo.libs.str_arr_ext import StringArrayType, pre_alloc_string_array, string_array_type
from bodo.libs.str_ext import string_type
from bodo.transforms import distributed_analysis, distributed_pass
from bodo.transforms.distributed_analysis import Distribution
from bodo.utils.transform import get_call_expr_arg
from bodo.utils.typing import BodoError, decode_if_dict_array, get_literal_value, get_overload_const_func, get_overload_const_str, get_overload_constant_dict, is_overload_constant_dict, is_overload_constant_str, list_cumulative, to_str_arr_if_dict_array
from bodo.utils.utils import debug_prints, incref, is_assign, is_call_assign, is_expr, is_null_pointer, is_var_assign, sanitize_varname, unliteral_all
gb_agg_cfunc = {}
gb_agg_cfunc_addr = {}


@intrinsic
def add_agg_cfunc_sym(typingctx, func, sym):

    def codegen(context, builder, signature, args):
        sig = func.signature
        if sig == types.none(types.voidptr):
            pkzc__tneue = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer()])
            vei__pzaqz = cgutils.get_or_insert_function(builder.module,
                pkzc__tneue, sym._literal_value)
            builder.call(vei__pzaqz, [context.get_constant_null(sig.args[0])])
        elif sig == types.none(types.int64, types.voidptr, types.voidptr):
            pkzc__tneue = lir.FunctionType(lir.VoidType(), [lir.IntType(64),
                lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
            vei__pzaqz = cgutils.get_or_insert_function(builder.module,
                pkzc__tneue, sym._literal_value)
            builder.call(vei__pzaqz, [context.get_constant(types.int64, 0),
                context.get_constant_null(sig.args[1]), context.
                get_constant_null(sig.args[2])])
        else:
            pkzc__tneue = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64).
                as_pointer()])
            vei__pzaqz = cgutils.get_or_insert_function(builder.module,
                pkzc__tneue, sym._literal_value)
            builder.call(vei__pzaqz, [context.get_constant_null(sig.args[0]
                ), context.get_constant_null(sig.args[1]), context.
                get_constant_null(sig.args[2])])
        context.add_linking_libs([gb_agg_cfunc[sym._literal_value]._library])
        return
    return types.none(func, sym), codegen


@numba.jit
def get_agg_udf_addr(name):
    with numba.objmode(addr='int64'):
        addr = gb_agg_cfunc_addr[name]
    return addr


class AggUDFStruct(object):

    def __init__(self, regular_udf_funcs=None, general_udf_funcs=None):
        assert regular_udf_funcs is not None or general_udf_funcs is not None
        self.regular_udfs = False
        self.general_udfs = False
        self.regular_udf_cfuncs = None
        self.general_udf_cfunc = None
        if regular_udf_funcs is not None:
            (self.var_typs, self.init_func, self.update_all_func, self.
                combine_all_func, self.eval_all_func) = regular_udf_funcs
            self.regular_udfs = True
        if general_udf_funcs is not None:
            self.general_udf_funcs = general_udf_funcs
            self.general_udfs = True

    def set_regular_cfuncs(self, update_cb, combine_cb, eval_cb):
        assert self.regular_udfs and self.regular_udf_cfuncs is None
        self.regular_udf_cfuncs = [update_cb, combine_cb, eval_cb]

    def set_general_cfunc(self, general_udf_cb):
        assert self.general_udfs and self.general_udf_cfunc is None
        self.general_udf_cfunc = general_udf_cb


AggFuncStruct = namedtuple('AggFuncStruct', ['func', 'ftype'])
supported_agg_funcs = ['no_op', 'head', 'transform', 'size', 'shift', 'sum',
    'count', 'nunique', 'median', 'cumsum', 'cumprod', 'cummin', 'cummax',
    'mean', 'min', 'max', 'prod', 'first', 'last', 'idxmin', 'idxmax',
    'var', 'std', 'udf', 'gen_udf']
supported_transform_funcs = ['no_op', 'sum', 'count', 'nunique', 'median',
    'mean', 'min', 'max', 'prod', 'first', 'last', 'var', 'std']


def get_agg_func(func_ir, func_name, rhs, series_type=None, typemap=None):
    if func_name == 'no_op':
        raise BodoError('Unknown aggregation function used in groupby.')
    if series_type is None:
        series_type = SeriesType(types.float64)
    if func_name in {'var', 'std'}:
        func = pytypes.SimpleNamespace()
        func.ftype = func_name
        func.fname = func_name
        func.ncols_pre_shuffle = 3
        func.ncols_post_shuffle = 4
        return func
    if func_name in {'first', 'last'}:
        func = pytypes.SimpleNamespace()
        func.ftype = func_name
        func.fname = func_name
        func.ncols_pre_shuffle = 1
        func.ncols_post_shuffle = 1
        return func
    if func_name in {'idxmin', 'idxmax'}:
        func = pytypes.SimpleNamespace()
        func.ftype = func_name
        func.fname = func_name
        func.ncols_pre_shuffle = 2
        func.ncols_post_shuffle = 2
        return func
    if func_name in supported_agg_funcs[:-8]:
        func = pytypes.SimpleNamespace()
        func.ftype = func_name
        func.fname = func_name
        func.ncols_pre_shuffle = 1
        func.ncols_post_shuffle = 1
        srs__xmae = True
        hwwxb__gibs = 1
        zidl__mhgj = -1
        if isinstance(rhs, ir.Expr):
            for bpelq__orzpi in rhs.kws:
                if func_name in list_cumulative:
                    if bpelq__orzpi[0] == 'skipna':
                        srs__xmae = guard(find_const, func_ir, bpelq__orzpi[1])
                        if not isinstance(srs__xmae, bool):
                            raise BodoError(
                                'For {} argument of skipna should be a boolean'
                                .format(func_name))
                if func_name == 'nunique':
                    if bpelq__orzpi[0] == 'dropna':
                        srs__xmae = guard(find_const, func_ir, bpelq__orzpi[1])
                        if not isinstance(srs__xmae, bool):
                            raise BodoError(
                                'argument of dropna to nunique should be a boolean'
                                )
        if func_name == 'shift' and (len(rhs.args) > 0 or len(rhs.kws) > 0):
            hwwxb__gibs = get_call_expr_arg('shift', rhs.args, dict(rhs.kws
                ), 0, 'periods', hwwxb__gibs)
            hwwxb__gibs = guard(find_const, func_ir, hwwxb__gibs)
        if func_name == 'head':
            zidl__mhgj = get_call_expr_arg('head', rhs.args, dict(rhs.kws),
                0, 'n', 5)
            if not isinstance(zidl__mhgj, int):
                zidl__mhgj = guard(find_const, func_ir, zidl__mhgj)
            if zidl__mhgj < 0:
                raise BodoError(
                    f'groupby.{func_name} does not work with negative values.')
        func.skipdropna = srs__xmae
        func.periods = hwwxb__gibs
        func.head_n = zidl__mhgj
        if func_name == 'transform':
            kws = dict(rhs.kws)
            mhibq__kyy = get_call_expr_arg(func_name, rhs.args, kws, 0,
                'func', '')
            qdm__hsdx = typemap[mhibq__kyy.name]
            eoqei__rpzof = None
            if isinstance(qdm__hsdx, str):
                eoqei__rpzof = qdm__hsdx
            elif is_overload_constant_str(qdm__hsdx):
                eoqei__rpzof = get_overload_const_str(qdm__hsdx)
            elif bodo.utils.typing.is_builtin_function(qdm__hsdx):
                eoqei__rpzof = bodo.utils.typing.get_builtin_function_name(
                    qdm__hsdx)
            if eoqei__rpzof not in bodo.ir.aggregate.supported_transform_funcs[
                :]:
                raise BodoError(
                    f'unsupported transform function {eoqei__rpzof}')
            func.transform_func = supported_agg_funcs.index(eoqei__rpzof)
        else:
            func.transform_func = supported_agg_funcs.index('no_op')
        return func
    assert func_name in ['agg', 'aggregate']
    assert typemap is not None
    kws = dict(rhs.kws)
    mhibq__kyy = get_call_expr_arg(func_name, rhs.args, kws, 0, 'func', '')
    if mhibq__kyy == '':
        qdm__hsdx = types.none
    else:
        qdm__hsdx = typemap[mhibq__kyy.name]
    if is_overload_constant_dict(qdm__hsdx):
        erc__ptuyr = get_overload_constant_dict(qdm__hsdx)
        rlj__ormz = [get_agg_func_udf(func_ir, f_val, rhs, series_type,
            typemap) for f_val in erc__ptuyr.values()]
        return rlj__ormz
    if qdm__hsdx == types.none:
        return [get_agg_func_udf(func_ir, get_literal_value(typemap[f_val.
            name])[1], rhs, series_type, typemap) for f_val in kws.values()]
    if isinstance(qdm__hsdx, types.BaseTuple):
        rlj__ormz = []
        gtxf__vtgo = 0
        for t in qdm__hsdx.types:
            if is_overload_constant_str(t):
                func_name = get_overload_const_str(t)
                rlj__ormz.append(get_agg_func(func_ir, func_name, rhs,
                    series_type, typemap))
            else:
                assert typemap is not None, 'typemap is required for agg UDF handling'
                func = _get_const_agg_func(t, func_ir)
                func.ftype = 'udf'
                func.fname = _get_udf_name(func)
                if func.fname == '<lambda>':
                    func.fname = '<lambda_' + str(gtxf__vtgo) + '>'
                    gtxf__vtgo += 1
                rlj__ormz.append(func)
        return [rlj__ormz]
    if is_overload_constant_str(qdm__hsdx):
        func_name = get_overload_const_str(qdm__hsdx)
        return get_agg_func(func_ir, func_name, rhs, series_type, typemap)
    if bodo.utils.typing.is_builtin_function(qdm__hsdx):
        func_name = bodo.utils.typing.get_builtin_function_name(qdm__hsdx)
        return get_agg_func(func_ir, func_name, rhs, series_type, typemap)
    assert typemap is not None, 'typemap is required for agg UDF handling'
    func = _get_const_agg_func(typemap[rhs.args[0].name], func_ir)
    func.ftype = 'udf'
    func.fname = _get_udf_name(func)
    return func


def get_agg_func_udf(func_ir, f_val, rhs, series_type, typemap):
    if isinstance(f_val, str):
        return get_agg_func(func_ir, f_val, rhs, series_type, typemap)
    if bodo.utils.typing.is_builtin_function(f_val):
        func_name = bodo.utils.typing.get_builtin_function_name(f_val)
        return get_agg_func(func_ir, func_name, rhs, series_type, typemap)
    if isinstance(f_val, (tuple, list)):
        gtxf__vtgo = 0
        ydia__mtn = []
        for ncjmg__vwjz in f_val:
            func = get_agg_func_udf(func_ir, ncjmg__vwjz, rhs, series_type,
                typemap)
            if func.fname == '<lambda>' and len(f_val) > 1:
                func.fname = f'<lambda_{gtxf__vtgo}>'
                gtxf__vtgo += 1
            ydia__mtn.append(func)
        return ydia__mtn
    else:
        assert is_expr(f_val, 'make_function') or isinstance(f_val, (numba.
            core.registry.CPUDispatcher, types.Dispatcher))
        assert typemap is not None, 'typemap is required for agg UDF handling'
        func = _get_const_agg_func(f_val, func_ir)
        func.ftype = 'udf'
        func.fname = _get_udf_name(func)
        return func


def _get_udf_name(func):
    code = func.code if hasattr(func, 'code') else func.__code__
    eoqei__rpzof = code.co_name
    return eoqei__rpzof


def _get_const_agg_func(func_typ, func_ir):
    agg_func = get_overload_const_func(func_typ, func_ir)
    if is_expr(agg_func, 'make_function'):

        def agg_func_wrapper(A):
            return A
        agg_func_wrapper.__code__ = agg_func.code
        agg_func = agg_func_wrapper
        return agg_func
    return agg_func


@infer_global(type)
class TypeDt64(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        if len(args) == 1 and isinstance(args[0], (types.NPDatetime, types.
            NPTimedelta)):
            lnnb__atbd = types.DType(args[0])
            return signature(lnnb__atbd, *args)


@numba.njit(no_cpython_wrapper=True)
def _var_combine(ssqdm_a, mean_a, nobs_a, ssqdm_b, mean_b, nobs_b):
    kvowt__vxdrp = nobs_a + nobs_b
    hvr__bnj = (nobs_a * mean_a + nobs_b * mean_b) / kvowt__vxdrp
    nvwep__ejdq = mean_b - mean_a
    zcxt__bydp = (ssqdm_a + ssqdm_b + nvwep__ejdq * nvwep__ejdq * nobs_a *
        nobs_b / kvowt__vxdrp)
    return zcxt__bydp, hvr__bnj, kvowt__vxdrp


def __special_combine(*args):
    return


@infer_global(__special_combine)
class SpecialCombineTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        return signature(types.void, *unliteral_all(args))


@lower_builtin(__special_combine, types.VarArg(types.Any))
def lower_special_combine(context, builder, sig, args):
    return context.get_dummy_value()


class Aggregate(ir.Stmt):

    def __init__(self, df_out, df_in, key_names, gb_info_in, gb_info_out,
        out_key_vars, df_out_vars, df_in_vars, key_arrs, input_has_index,
        same_index, return_key, loc, func_name, dropna=True, pivot_arr=None,
        pivot_values=None, is_crosstab=False):
        self.df_out = df_out
        self.df_in = df_in
        self.key_names = key_names
        self.gb_info_in = gb_info_in
        self.gb_info_out = gb_info_out
        self.out_key_vars = out_key_vars
        self.df_out_vars = df_out_vars
        self.df_in_vars = df_in_vars
        self.key_arrs = key_arrs
        self.input_has_index = input_has_index
        self.same_index = same_index
        self.return_key = return_key
        self.loc = loc
        self.func_name = func_name
        self.dropna = dropna
        self.pivot_arr = pivot_arr
        self.pivot_values = pivot_values
        self.is_crosstab = is_crosstab

    def __repr__(self):
        kxec__anmwj = ''
        for qew__gbucl, pnr__vndwl in self.df_out_vars.items():
            kxec__anmwj += "'{}':{}, ".format(qew__gbucl, pnr__vndwl.name)
        bab__abz = '{}{{{}}}'.format(self.df_out, kxec__anmwj)
        zwve__ydrm = ''
        for qew__gbucl, pnr__vndwl in self.df_in_vars.items():
            zwve__ydrm += "'{}':{}, ".format(qew__gbucl, pnr__vndwl.name)
        kxvvk__auj = '{}{{{}}}'.format(self.df_in, zwve__ydrm)
        bugt__zqm = 'pivot {}:{}'.format(self.pivot_arr.name, self.pivot_values
            ) if self.pivot_arr is not None else ''
        key_names = ','.join(self.key_names)
        tkfw__eyxs = ','.join([pnr__vndwl.name for pnr__vndwl in self.key_arrs]
            )
        return 'aggregate: {} = {} [key: {}:{}] {}'.format(bab__abz,
            kxvvk__auj, key_names, tkfw__eyxs, bugt__zqm)

    def remove_out_col(self, out_col_name):
        self.df_out_vars.pop(out_col_name)
        twsht__ogmls, kotin__fzy = self.gb_info_out.pop(out_col_name)
        if twsht__ogmls is None and not self.is_crosstab:
            return
        iuz__alcmu = self.gb_info_in[twsht__ogmls]
        if self.pivot_arr is not None:
            self.pivot_values.remove(out_col_name)
            for tpup__alzyi, (func, kxec__anmwj) in enumerate(iuz__alcmu):
                try:
                    kxec__anmwj.remove(out_col_name)
                    if len(kxec__anmwj) == 0:
                        iuz__alcmu.pop(tpup__alzyi)
                        break
                except ValueError as gbsig__drtyx:
                    continue
        else:
            for tpup__alzyi, (func, qezbh__ccyhr) in enumerate(iuz__alcmu):
                if qezbh__ccyhr == out_col_name:
                    iuz__alcmu.pop(tpup__alzyi)
                    break
        if len(iuz__alcmu) == 0:
            self.gb_info_in.pop(twsht__ogmls)
            self.df_in_vars.pop(twsht__ogmls)


def aggregate_usedefs(aggregate_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({pnr__vndwl.name for pnr__vndwl in aggregate_node.key_arrs})
    use_set.update({pnr__vndwl.name for pnr__vndwl in aggregate_node.
        df_in_vars.values()})
    if aggregate_node.pivot_arr is not None:
        use_set.add(aggregate_node.pivot_arr.name)
    def_set.update({pnr__vndwl.name for pnr__vndwl in aggregate_node.
        df_out_vars.values()})
    if aggregate_node.out_key_vars is not None:
        def_set.update({pnr__vndwl.name for pnr__vndwl in aggregate_node.
            out_key_vars})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Aggregate] = aggregate_usedefs


def remove_dead_aggregate(aggregate_node, lives_no_aliases, lives,
    arg_aliases, alias_map, func_ir, typemap):
    wkbk__foe = [tyww__ykn for tyww__ykn, lbb__kqn in aggregate_node.
        df_out_vars.items() if lbb__kqn.name not in lives]
    for wxmo__dblxi in wkbk__foe:
        aggregate_node.remove_out_col(wxmo__dblxi)
    out_key_vars = aggregate_node.out_key_vars
    if out_key_vars is not None and all(pnr__vndwl.name not in lives for
        pnr__vndwl in out_key_vars):
        aggregate_node.out_key_vars = None
    if len(aggregate_node.df_out_vars
        ) == 0 and aggregate_node.out_key_vars is None:
        return None
    return aggregate_node


ir_utils.remove_dead_extensions[Aggregate] = remove_dead_aggregate


def get_copies_aggregate(aggregate_node, typemap):
    jnylu__zwkg = set(pnr__vndwl.name for pnr__vndwl in aggregate_node.
        df_out_vars.values())
    if aggregate_node.out_key_vars is not None:
        jnylu__zwkg.update({pnr__vndwl.name for pnr__vndwl in
            aggregate_node.out_key_vars})
    return set(), jnylu__zwkg


ir_utils.copy_propagate_extensions[Aggregate] = get_copies_aggregate


def apply_copies_aggregate(aggregate_node, var_dict, name_var_table,
    typemap, calltypes, save_copies):
    for tpup__alzyi in range(len(aggregate_node.key_arrs)):
        aggregate_node.key_arrs[tpup__alzyi] = replace_vars_inner(
            aggregate_node.key_arrs[tpup__alzyi], var_dict)
    for tyww__ykn in list(aggregate_node.df_in_vars.keys()):
        aggregate_node.df_in_vars[tyww__ykn] = replace_vars_inner(
            aggregate_node.df_in_vars[tyww__ykn], var_dict)
    for tyww__ykn in list(aggregate_node.df_out_vars.keys()):
        aggregate_node.df_out_vars[tyww__ykn] = replace_vars_inner(
            aggregate_node.df_out_vars[tyww__ykn], var_dict)
    if aggregate_node.out_key_vars is not None:
        for tpup__alzyi in range(len(aggregate_node.out_key_vars)):
            aggregate_node.out_key_vars[tpup__alzyi] = replace_vars_inner(
                aggregate_node.out_key_vars[tpup__alzyi], var_dict)
    if aggregate_node.pivot_arr is not None:
        aggregate_node.pivot_arr = replace_vars_inner(aggregate_node.
            pivot_arr, var_dict)


ir_utils.apply_copy_propagate_extensions[Aggregate] = apply_copies_aggregate


def visit_vars_aggregate(aggregate_node, callback, cbdata):
    if debug_prints():
        print('visiting aggregate vars for:', aggregate_node)
        print('cbdata: ', sorted(cbdata.items()))
    for tpup__alzyi in range(len(aggregate_node.key_arrs)):
        aggregate_node.key_arrs[tpup__alzyi] = visit_vars_inner(aggregate_node
            .key_arrs[tpup__alzyi], callback, cbdata)
    for tyww__ykn in list(aggregate_node.df_in_vars.keys()):
        aggregate_node.df_in_vars[tyww__ykn] = visit_vars_inner(aggregate_node
            .df_in_vars[tyww__ykn], callback, cbdata)
    for tyww__ykn in list(aggregate_node.df_out_vars.keys()):
        aggregate_node.df_out_vars[tyww__ykn] = visit_vars_inner(aggregate_node
            .df_out_vars[tyww__ykn], callback, cbdata)
    if aggregate_node.out_key_vars is not None:
        for tpup__alzyi in range(len(aggregate_node.out_key_vars)):
            aggregate_node.out_key_vars[tpup__alzyi] = visit_vars_inner(
                aggregate_node.out_key_vars[tpup__alzyi], callback, cbdata)
    if aggregate_node.pivot_arr is not None:
        aggregate_node.pivot_arr = visit_vars_inner(aggregate_node.
            pivot_arr, callback, cbdata)


ir_utils.visit_vars_extensions[Aggregate] = visit_vars_aggregate


def aggregate_array_analysis(aggregate_node, equiv_set, typemap, array_analysis
    ):
    assert len(aggregate_node.df_out_vars
        ) > 0 or aggregate_node.out_key_vars is not None or aggregate_node.is_crosstab, 'empty aggregate in array analysis'
    xui__ooy = []
    for fnzn__rkwmk in aggregate_node.key_arrs:
        hgob__kmkps = equiv_set.get_shape(fnzn__rkwmk)
        if hgob__kmkps:
            xui__ooy.append(hgob__kmkps[0])
    if aggregate_node.pivot_arr is not None:
        hgob__kmkps = equiv_set.get_shape(aggregate_node.pivot_arr)
        if hgob__kmkps:
            xui__ooy.append(hgob__kmkps[0])
    for lbb__kqn in aggregate_node.df_in_vars.values():
        hgob__kmkps = equiv_set.get_shape(lbb__kqn)
        if hgob__kmkps:
            xui__ooy.append(hgob__kmkps[0])
    if len(xui__ooy) > 1:
        equiv_set.insert_equiv(*xui__ooy)
    tlj__rwcgq = []
    xui__ooy = []
    xoass__mvoyj = list(aggregate_node.df_out_vars.values())
    if aggregate_node.out_key_vars is not None:
        xoass__mvoyj.extend(aggregate_node.out_key_vars)
    for lbb__kqn in xoass__mvoyj:
        ywo__nzmg = typemap[lbb__kqn.name]
        ihc__yvtc = array_analysis._gen_shape_call(equiv_set, lbb__kqn,
            ywo__nzmg.ndim, None, tlj__rwcgq)
        equiv_set.insert_equiv(lbb__kqn, ihc__yvtc)
        xui__ooy.append(ihc__yvtc[0])
        equiv_set.define(lbb__kqn, set())
    if len(xui__ooy) > 1:
        equiv_set.insert_equiv(*xui__ooy)
    return [], tlj__rwcgq


numba.parfors.array_analysis.array_analysis_extensions[Aggregate
    ] = aggregate_array_analysis


def aggregate_distributed_analysis(aggregate_node, array_dists):
    yuej__rjmry = Distribution.OneD
    for lbb__kqn in aggregate_node.df_in_vars.values():
        yuej__rjmry = Distribution(min(yuej__rjmry.value, array_dists[
            lbb__kqn.name].value))
    for fnzn__rkwmk in aggregate_node.key_arrs:
        yuej__rjmry = Distribution(min(yuej__rjmry.value, array_dists[
            fnzn__rkwmk.name].value))
    if aggregate_node.pivot_arr is not None:
        yuej__rjmry = Distribution(min(yuej__rjmry.value, array_dists[
            aggregate_node.pivot_arr.name].value))
        array_dists[aggregate_node.pivot_arr.name] = yuej__rjmry
    for lbb__kqn in aggregate_node.df_in_vars.values():
        array_dists[lbb__kqn.name] = yuej__rjmry
    for fnzn__rkwmk in aggregate_node.key_arrs:
        array_dists[fnzn__rkwmk.name] = yuej__rjmry
    gus__qgta = Distribution.OneD_Var
    for lbb__kqn in aggregate_node.df_out_vars.values():
        if lbb__kqn.name in array_dists:
            gus__qgta = Distribution(min(gus__qgta.value, array_dists[
                lbb__kqn.name].value))
    if aggregate_node.out_key_vars is not None:
        for lbb__kqn in aggregate_node.out_key_vars:
            if lbb__kqn.name in array_dists:
                gus__qgta = Distribution(min(gus__qgta.value, array_dists[
                    lbb__kqn.name].value))
    gus__qgta = Distribution(min(gus__qgta.value, yuej__rjmry.value))
    for lbb__kqn in aggregate_node.df_out_vars.values():
        array_dists[lbb__kqn.name] = gus__qgta
    if aggregate_node.out_key_vars is not None:
        for piqkt__ohk in aggregate_node.out_key_vars:
            array_dists[piqkt__ohk.name] = gus__qgta
    if gus__qgta != Distribution.OneD_Var:
        for fnzn__rkwmk in aggregate_node.key_arrs:
            array_dists[fnzn__rkwmk.name] = gus__qgta
        if aggregate_node.pivot_arr is not None:
            array_dists[aggregate_node.pivot_arr.name] = gus__qgta
        for lbb__kqn in aggregate_node.df_in_vars.values():
            array_dists[lbb__kqn.name] = gus__qgta


distributed_analysis.distributed_analysis_extensions[Aggregate
    ] = aggregate_distributed_analysis


def build_agg_definitions(agg_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for lbb__kqn in agg_node.df_out_vars.values():
        definitions[lbb__kqn.name].append(agg_node)
    if agg_node.out_key_vars is not None:
        for piqkt__ohk in agg_node.out_key_vars:
            definitions[piqkt__ohk.name].append(agg_node)
    return definitions


ir_utils.build_defs_extensions[Aggregate] = build_agg_definitions


def __update_redvars():
    pass


@infer_global(__update_redvars)
class UpdateDummyTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        return signature(types.void, *args)


def __combine_redvars():
    pass


@infer_global(__combine_redvars)
class CombineDummyTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        return signature(types.void, *args)


def __eval_res():
    pass


@infer_global(__eval_res)
class EvalDummyTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        return signature(args[0].dtype, *args)


def agg_distributed_run(agg_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    parallel = False
    if array_dists is not None:
        parallel = True
        for pnr__vndwl in (list(agg_node.df_in_vars.values()) + list(
            agg_node.df_out_vars.values()) + agg_node.key_arrs):
            if array_dists[pnr__vndwl.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                pnr__vndwl.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    jnm__sihy = tuple(typemap[pnr__vndwl.name] for pnr__vndwl in agg_node.
        key_arrs)
    ynwej__otey = [pnr__vndwl for nvhai__pjhb, pnr__vndwl in agg_node.
        df_in_vars.items()]
    gofd__xqq = [pnr__vndwl for nvhai__pjhb, pnr__vndwl in agg_node.
        df_out_vars.items()]
    in_col_typs = []
    rlj__ormz = []
    if agg_node.pivot_arr is not None:
        for twsht__ogmls, iuz__alcmu in agg_node.gb_info_in.items():
            for func, kotin__fzy in iuz__alcmu:
                if twsht__ogmls is not None:
                    in_col_typs.append(typemap[agg_node.df_in_vars[
                        twsht__ogmls].name])
                rlj__ormz.append(func)
    else:
        for twsht__ogmls, func in agg_node.gb_info_out.values():
            if twsht__ogmls is not None:
                in_col_typs.append(typemap[agg_node.df_in_vars[twsht__ogmls
                    ].name])
            rlj__ormz.append(func)
    out_col_typs = tuple(typemap[pnr__vndwl.name] for pnr__vndwl in gofd__xqq)
    pivot_typ = types.none if agg_node.pivot_arr is None else typemap[agg_node
        .pivot_arr.name]
    arg_typs = tuple(jnm__sihy + tuple(typemap[pnr__vndwl.name] for
        pnr__vndwl in ynwej__otey) + (pivot_typ,))
    in_col_typs = [to_str_arr_if_dict_array(t) for t in in_col_typs]
    ubm__rjee = {'bodo': bodo, 'np': np, 'dt64_dtype': np.dtype(
        'datetime64[ns]'), 'td64_dtype': np.dtype('timedelta64[ns]')}
    for tpup__alzyi, in_col_typ in enumerate(in_col_typs):
        if isinstance(in_col_typ, bodo.CategoricalArrayType):
            ubm__rjee.update({f'in_cat_dtype_{tpup__alzyi}': in_col_typ})
    for tpup__alzyi, qcy__yfh in enumerate(out_col_typs):
        if isinstance(qcy__yfh, bodo.CategoricalArrayType):
            ubm__rjee.update({f'out_cat_dtype_{tpup__alzyi}': qcy__yfh})
    udf_func_struct = get_udf_func_struct(rlj__ormz, agg_node.
        input_has_index, in_col_typs, out_col_typs, typingctx, targetctx,
        pivot_typ, agg_node.pivot_values, agg_node.is_crosstab)
    ithek__lijt = gen_top_level_agg_func(agg_node, in_col_typs,
        out_col_typs, parallel, udf_func_struct)
    ubm__rjee.update({'pd': pd, 'pre_alloc_string_array':
        pre_alloc_string_array, 'pre_alloc_binary_array':
        pre_alloc_binary_array, 'pre_alloc_array_item_array':
        pre_alloc_array_item_array, 'string_array_type': string_array_type,
        'alloc_decimal_array': alloc_decimal_array, 'array_to_info':
        array_to_info, 'arr_info_list_to_table': arr_info_list_to_table,
        'coerce_to_array': bodo.utils.conversion.coerce_to_array,
        'groupby_and_aggregate': groupby_and_aggregate,
        'pivot_groupby_and_aggregate': pivot_groupby_and_aggregate,
        'info_from_table': info_from_table, 'info_to_array': info_to_array,
        'delete_info_decref_array': delete_info_decref_array,
        'delete_table': delete_table, 'add_agg_cfunc_sym':
        add_agg_cfunc_sym, 'get_agg_udf_addr': get_agg_udf_addr,
        'delete_table_decref_arrays': delete_table_decref_arrays,
        'decode_if_dict_array': decode_if_dict_array})
    if udf_func_struct is not None:
        if udf_func_struct.regular_udfs:
            ubm__rjee.update({'__update_redvars': udf_func_struct.
                update_all_func, '__init_func': udf_func_struct.init_func,
                '__combine_redvars': udf_func_struct.combine_all_func,
                '__eval_res': udf_func_struct.eval_all_func,
                'cpp_cb_update': udf_func_struct.regular_udf_cfuncs[0],
                'cpp_cb_combine': udf_func_struct.regular_udf_cfuncs[1],
                'cpp_cb_eval': udf_func_struct.regular_udf_cfuncs[2]})
        if udf_func_struct.general_udfs:
            ubm__rjee.update({'cpp_cb_general': udf_func_struct.
                general_udf_cfunc})
    aol__xtolc = compile_to_numba_ir(ithek__lijt, ubm__rjee, typingctx=
        typingctx, targetctx=targetctx, arg_typs=arg_typs, typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    zxymd__ktr = []
    if agg_node.pivot_arr is None:
        pycd__ppwj = agg_node.key_arrs[0].scope
        loc = agg_node.loc
        onaut__meum = ir.Var(pycd__ppwj, mk_unique_var('dummy_none'), loc)
        typemap[onaut__meum.name] = types.none
        zxymd__ktr.append(ir.Assign(ir.Const(None, loc), onaut__meum, loc))
        ynwej__otey.append(onaut__meum)
    else:
        ynwej__otey.append(agg_node.pivot_arr)
    replace_arg_nodes(aol__xtolc, agg_node.key_arrs + ynwej__otey)
    sfoo__jnu = aol__xtolc.body[-3]
    assert is_assign(sfoo__jnu) and isinstance(sfoo__jnu.value, ir.Expr
        ) and sfoo__jnu.value.op == 'build_tuple'
    zxymd__ktr += aol__xtolc.body[:-3]
    xoass__mvoyj = list(agg_node.df_out_vars.values())
    if agg_node.out_key_vars is not None:
        xoass__mvoyj += agg_node.out_key_vars
    for tpup__alzyi, ttbuf__hze in enumerate(xoass__mvoyj):
        wgqin__iqf = sfoo__jnu.value.items[tpup__alzyi]
        zxymd__ktr.append(ir.Assign(wgqin__iqf, ttbuf__hze, ttbuf__hze.loc))
    return zxymd__ktr


distributed_pass.distributed_run_extensions[Aggregate] = agg_distributed_run


def get_numba_set(dtype):
    pass


@infer_global(get_numba_set)
class GetNumbaSetTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 1
        edue__tti = args[0]
        dtype = types.Tuple([t.dtype for t in edue__tti.types]) if isinstance(
            edue__tti, types.BaseTuple) else edue__tti.dtype
        if isinstance(edue__tti, types.BaseTuple) and len(edue__tti.types
            ) == 1:
            dtype = edue__tti.types[0].dtype
        return signature(types.Set(dtype), *args)


@lower_builtin(get_numba_set, types.Any)
def lower_get_numba_set(context, builder, sig, args):
    return numba.cpython.setobj.set_empty_constructor(context, builder, sig,
        args)


@infer_global(bool)
class BoolNoneTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 1
        jtcnc__hlxsp = args[0]
        if jtcnc__hlxsp == types.none:
            return signature(types.boolean, *args)


@lower_builtin(bool, types.none)
def lower_column_mean_impl(context, builder, sig, args):
    adpj__xnl = context.compile_internal(builder, lambda a: False, sig, args)
    return adpj__xnl


def _gen_dummy_alloc(t, colnum=0, is_input=False):
    if isinstance(t, IntegerArrayType):
        pkmgs__qmjzx = IntDtype(t.dtype).name
        assert pkmgs__qmjzx.endswith('Dtype()')
        pkmgs__qmjzx = pkmgs__qmjzx[:-7]
        return (
            f"bodo.hiframes.pd_series_ext.get_series_data(pd.Series([1], dtype='{pkmgs__qmjzx}'))"
            )
    elif isinstance(t, BooleanArrayType):
        return (
            'bodo.libs.bool_arr_ext.init_bool_array(np.empty(0, np.bool_), np.empty(0, np.uint8))'
            )
    elif isinstance(t, StringArrayType):
        return 'pre_alloc_string_array(1, 1)'
    elif isinstance(t, BinaryArrayType):
        return 'pre_alloc_binary_array(1, 1)'
    elif t == ArrayItemArrayType(string_array_type):
        return 'pre_alloc_array_item_array(1, (1, 1), string_array_type)'
    elif isinstance(t, DecimalArrayType):
        return 'alloc_decimal_array(1, {}, {})'.format(t.precision, t.scale)
    elif isinstance(t, DatetimeDateArrayType):
        return (
            'bodo.hiframes.datetime_date_ext.init_datetime_date_array(np.empty(1, np.int64), np.empty(1, np.uint8))'
            )
    elif isinstance(t, bodo.CategoricalArrayType):
        if t.dtype.categories is None:
            raise BodoError(
                'Groupby agg operations on Categorical types require constant categories'
                )
        gkrpn__yhy = 'in' if is_input else 'out'
        return (
            f'bodo.utils.utils.alloc_type(1, {gkrpn__yhy}_cat_dtype_{colnum})')
    else:
        return 'np.empty(1, {})'.format(_get_np_dtype(t.dtype))


def _get_np_dtype(t):
    if t == types.bool_:
        return 'np.bool_'
    if t == types.NPDatetime('ns'):
        return 'dt64_dtype'
    if t == types.NPTimedelta('ns'):
        return 'td64_dtype'
    return 'np.{}'.format(t)


def gen_update_cb(udf_func_struct, allfuncs, n_keys, data_in_typs_,
    out_data_typs, do_combine, func_idx_to_in_col, label_suffix):
    gpil__cin = udf_func_struct.var_typs
    eyx__vpb = len(gpil__cin)
    kya__amw = (
        'def bodo_gb_udf_update_local{}(in_table, out_table, row_to_group):\n'
        .format(label_suffix))
    kya__amw += '    if is_null_pointer(in_table):\n'
    kya__amw += '        return\n'
    kya__amw += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in gpil__cin]), 
        ',' if len(gpil__cin) == 1 else '')
    vtakv__qyl = n_keys
    fkwh__ily = []
    redvar_offsets = []
    qzbd__zjd = []
    if do_combine:
        for tpup__alzyi, ncjmg__vwjz in enumerate(allfuncs):
            if ncjmg__vwjz.ftype != 'udf':
                vtakv__qyl += ncjmg__vwjz.ncols_pre_shuffle
            else:
                redvar_offsets += list(range(vtakv__qyl, vtakv__qyl +
                    ncjmg__vwjz.n_redvars))
                vtakv__qyl += ncjmg__vwjz.n_redvars
                qzbd__zjd.append(data_in_typs_[func_idx_to_in_col[tpup__alzyi]]
                    )
                fkwh__ily.append(func_idx_to_in_col[tpup__alzyi] + n_keys)
    else:
        for tpup__alzyi, ncjmg__vwjz in enumerate(allfuncs):
            if ncjmg__vwjz.ftype != 'udf':
                vtakv__qyl += ncjmg__vwjz.ncols_post_shuffle
            else:
                redvar_offsets += list(range(vtakv__qyl + 1, vtakv__qyl + 1 +
                    ncjmg__vwjz.n_redvars))
                vtakv__qyl += ncjmg__vwjz.n_redvars + 1
                qzbd__zjd.append(data_in_typs_[func_idx_to_in_col[tpup__alzyi]]
                    )
                fkwh__ily.append(func_idx_to_in_col[tpup__alzyi] + n_keys)
    assert len(redvar_offsets) == eyx__vpb
    kopuk__bugn = len(qzbd__zjd)
    vjco__iavhy = []
    for tpup__alzyi, t in enumerate(qzbd__zjd):
        vjco__iavhy.append(_gen_dummy_alloc(t, tpup__alzyi, True))
    kya__amw += '    data_in_dummy = ({}{})\n'.format(','.join(vjco__iavhy),
        ',' if len(qzbd__zjd) == 1 else '')
    kya__amw += """
    # initialize redvar cols
"""
    kya__amw += '    init_vals = __init_func()\n'
    for tpup__alzyi in range(eyx__vpb):
        kya__amw += (
            """    redvar_arr_{} = info_to_array(info_from_table(out_table, {}), data_redvar_dummy[{}])
"""
            .format(tpup__alzyi, redvar_offsets[tpup__alzyi], tpup__alzyi))
        kya__amw += '    incref(redvar_arr_{})\n'.format(tpup__alzyi)
        kya__amw += '    redvar_arr_{}.fill(init_vals[{}])\n'.format(
            tpup__alzyi, tpup__alzyi)
    kya__amw += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'.
        format(tpup__alzyi) for tpup__alzyi in range(eyx__vpb)]), ',' if 
        eyx__vpb == 1 else '')
    kya__amw += '\n'
    for tpup__alzyi in range(kopuk__bugn):
        kya__amw += (
            """    data_in_{} = info_to_array(info_from_table(in_table, {}), data_in_dummy[{}])
"""
            .format(tpup__alzyi, fkwh__ily[tpup__alzyi], tpup__alzyi))
        kya__amw += '    incref(data_in_{})\n'.format(tpup__alzyi)
    kya__amw += '    data_in = ({}{})\n'.format(','.join(['data_in_{}'.
        format(tpup__alzyi) for tpup__alzyi in range(kopuk__bugn)]), ',' if
        kopuk__bugn == 1 else '')
    kya__amw += '\n'
    kya__amw += '    for i in range(len(data_in_0)):\n'
    kya__amw += '        w_ind = row_to_group[i]\n'
    kya__amw += '        if w_ind != -1:\n'
    kya__amw += (
        '            __update_redvars(redvars, data_in, w_ind, i, pivot_arr=None)\n'
        )
    htd__ixrh = {}
    exec(kya__amw, {'bodo': bodo, 'np': np, 'pd': pd, 'info_to_array':
        info_to_array, 'info_from_table': info_from_table, 'incref': incref,
        'pre_alloc_string_array': pre_alloc_string_array, '__init_func':
        udf_func_struct.init_func, '__update_redvars': udf_func_struct.
        update_all_func, 'is_null_pointer': is_null_pointer, 'dt64_dtype':
        np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, htd__ixrh)
    return htd__ixrh['bodo_gb_udf_update_local{}'.format(label_suffix)]


def gen_combine_cb(udf_func_struct, allfuncs, n_keys, out_data_typs,
    label_suffix):
    gpil__cin = udf_func_struct.var_typs
    eyx__vpb = len(gpil__cin)
    kya__amw = (
        'def bodo_gb_udf_combine{}(in_table, out_table, row_to_group):\n'.
        format(label_suffix))
    kya__amw += '    if is_null_pointer(in_table):\n'
    kya__amw += '        return\n'
    kya__amw += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in gpil__cin]), 
        ',' if len(gpil__cin) == 1 else '')
    jlp__gcc = n_keys
    gjr__sjphm = n_keys
    custt__wbdw = []
    zrk__citgf = []
    for ncjmg__vwjz in allfuncs:
        if ncjmg__vwjz.ftype != 'udf':
            jlp__gcc += ncjmg__vwjz.ncols_pre_shuffle
            gjr__sjphm += ncjmg__vwjz.ncols_post_shuffle
        else:
            custt__wbdw += list(range(jlp__gcc, jlp__gcc + ncjmg__vwjz.
                n_redvars))
            zrk__citgf += list(range(gjr__sjphm + 1, gjr__sjphm + 1 +
                ncjmg__vwjz.n_redvars))
            jlp__gcc += ncjmg__vwjz.n_redvars
            gjr__sjphm += 1 + ncjmg__vwjz.n_redvars
    assert len(custt__wbdw) == eyx__vpb
    kya__amw += """
    # initialize redvar cols
"""
    kya__amw += '    init_vals = __init_func()\n'
    for tpup__alzyi in range(eyx__vpb):
        kya__amw += (
            """    redvar_arr_{} = info_to_array(info_from_table(out_table, {}), data_redvar_dummy[{}])
"""
            .format(tpup__alzyi, zrk__citgf[tpup__alzyi], tpup__alzyi))
        kya__amw += '    incref(redvar_arr_{})\n'.format(tpup__alzyi)
        kya__amw += '    redvar_arr_{}.fill(init_vals[{}])\n'.format(
            tpup__alzyi, tpup__alzyi)
    kya__amw += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'.
        format(tpup__alzyi) for tpup__alzyi in range(eyx__vpb)]), ',' if 
        eyx__vpb == 1 else '')
    kya__amw += '\n'
    for tpup__alzyi in range(eyx__vpb):
        kya__amw += (
            """    recv_redvar_arr_{} = info_to_array(info_from_table(in_table, {}), data_redvar_dummy[{}])
"""
            .format(tpup__alzyi, custt__wbdw[tpup__alzyi], tpup__alzyi))
        kya__amw += '    incref(recv_redvar_arr_{})\n'.format(tpup__alzyi)
    kya__amw += '    recv_redvars = ({}{})\n'.format(','.join([
        'recv_redvar_arr_{}'.format(tpup__alzyi) for tpup__alzyi in range(
        eyx__vpb)]), ',' if eyx__vpb == 1 else '')
    kya__amw += '\n'
    if eyx__vpb:
        kya__amw += '    for i in range(len(recv_redvar_arr_0)):\n'
        kya__amw += '        w_ind = row_to_group[i]\n'
        kya__amw += (
            '        __combine_redvars(redvars, recv_redvars, w_ind, i, pivot_arr=None)\n'
            )
    htd__ixrh = {}
    exec(kya__amw, {'np': np, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref, '__init_func':
        udf_func_struct.init_func, '__combine_redvars': udf_func_struct.
        combine_all_func, 'is_null_pointer': is_null_pointer, 'dt64_dtype':
        np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, htd__ixrh)
    return htd__ixrh['bodo_gb_udf_combine{}'.format(label_suffix)]


def gen_eval_cb(udf_func_struct, allfuncs, n_keys, out_data_typs_, label_suffix
    ):
    gpil__cin = udf_func_struct.var_typs
    eyx__vpb = len(gpil__cin)
    vtakv__qyl = n_keys
    redvar_offsets = []
    qucj__wfolv = []
    out_data_typs = []
    for tpup__alzyi, ncjmg__vwjz in enumerate(allfuncs):
        if ncjmg__vwjz.ftype != 'udf':
            vtakv__qyl += ncjmg__vwjz.ncols_post_shuffle
        else:
            qucj__wfolv.append(vtakv__qyl)
            redvar_offsets += list(range(vtakv__qyl + 1, vtakv__qyl + 1 +
                ncjmg__vwjz.n_redvars))
            vtakv__qyl += 1 + ncjmg__vwjz.n_redvars
            out_data_typs.append(out_data_typs_[tpup__alzyi])
    assert len(redvar_offsets) == eyx__vpb
    kopuk__bugn = len(out_data_typs)
    kya__amw = 'def bodo_gb_udf_eval{}(table):\n'.format(label_suffix)
    kya__amw += '    if is_null_pointer(table):\n'
    kya__amw += '        return\n'
    kya__amw += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in gpil__cin]), 
        ',' if len(gpil__cin) == 1 else '')
    kya__amw += '    out_data_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t.dtype)) for t in
        out_data_typs]), ',' if len(out_data_typs) == 1 else '')
    for tpup__alzyi in range(eyx__vpb):
        kya__amw += (
            """    redvar_arr_{} = info_to_array(info_from_table(table, {}), data_redvar_dummy[{}])
"""
            .format(tpup__alzyi, redvar_offsets[tpup__alzyi], tpup__alzyi))
        kya__amw += '    incref(redvar_arr_{})\n'.format(tpup__alzyi)
    kya__amw += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'.
        format(tpup__alzyi) for tpup__alzyi in range(eyx__vpb)]), ',' if 
        eyx__vpb == 1 else '')
    kya__amw += '\n'
    for tpup__alzyi in range(kopuk__bugn):
        kya__amw += (
            """    data_out_{} = info_to_array(info_from_table(table, {}), out_data_dummy[{}])
"""
            .format(tpup__alzyi, qucj__wfolv[tpup__alzyi], tpup__alzyi))
        kya__amw += '    incref(data_out_{})\n'.format(tpup__alzyi)
    kya__amw += '    data_out = ({}{})\n'.format(','.join(['data_out_{}'.
        format(tpup__alzyi) for tpup__alzyi in range(kopuk__bugn)]), ',' if
        kopuk__bugn == 1 else '')
    kya__amw += '\n'
    kya__amw += '    for i in range(len(data_out_0)):\n'
    kya__amw += '        __eval_res(redvars, data_out, i)\n'
    htd__ixrh = {}
    exec(kya__amw, {'np': np, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref, '__eval_res':
        udf_func_struct.eval_all_func, 'is_null_pointer': is_null_pointer,
        'dt64_dtype': np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, htd__ixrh)
    return htd__ixrh['bodo_gb_udf_eval{}'.format(label_suffix)]


def gen_general_udf_cb(udf_func_struct, allfuncs, n_keys, in_col_typs,
    out_col_typs, func_idx_to_in_col, label_suffix):
    vtakv__qyl = n_keys
    ksis__txtq = []
    for tpup__alzyi, ncjmg__vwjz in enumerate(allfuncs):
        if ncjmg__vwjz.ftype == 'gen_udf':
            ksis__txtq.append(vtakv__qyl)
            vtakv__qyl += 1
        elif ncjmg__vwjz.ftype != 'udf':
            vtakv__qyl += ncjmg__vwjz.ncols_post_shuffle
        else:
            vtakv__qyl += ncjmg__vwjz.n_redvars + 1
    kya__amw = (
        'def bodo_gb_apply_general_udfs{}(num_groups, in_table, out_table):\n'
        .format(label_suffix))
    kya__amw += '    if num_groups == 0:\n'
    kya__amw += '        return\n'
    for tpup__alzyi, func in enumerate(udf_func_struct.general_udf_funcs):
        kya__amw += '    # col {}\n'.format(tpup__alzyi)
        kya__amw += (
            '    out_col = info_to_array(info_from_table(out_table, {}), out_col_{}_typ)\n'
            .format(ksis__txtq[tpup__alzyi], tpup__alzyi))
        kya__amw += '    incref(out_col)\n'
        kya__amw += '    for j in range(num_groups):\n'
        kya__amw += (
            """        in_col = info_to_array(info_from_table(in_table, {}*num_groups + j), in_col_{}_typ)
"""
            .format(tpup__alzyi, tpup__alzyi))
        kya__amw += '        incref(in_col)\n'
        kya__amw += (
            '        out_col[j] = func_{}(pd.Series(in_col))  # func returns scalar\n'
            .format(tpup__alzyi))
    ubm__rjee = {'pd': pd, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref}
    svnhl__gzcx = 0
    for tpup__alzyi, func in enumerate(allfuncs):
        if func.ftype != 'gen_udf':
            continue
        func = udf_func_struct.general_udf_funcs[svnhl__gzcx]
        ubm__rjee['func_{}'.format(svnhl__gzcx)] = func
        ubm__rjee['in_col_{}_typ'.format(svnhl__gzcx)] = in_col_typs[
            func_idx_to_in_col[tpup__alzyi]]
        ubm__rjee['out_col_{}_typ'.format(svnhl__gzcx)] = out_col_typs[
            tpup__alzyi]
        svnhl__gzcx += 1
    htd__ixrh = {}
    exec(kya__amw, ubm__rjee, htd__ixrh)
    ncjmg__vwjz = htd__ixrh['bodo_gb_apply_general_udfs{}'.format(label_suffix)
        ]
    abf__kddj = types.void(types.int64, types.voidptr, types.voidptr)
    return numba.cfunc(abf__kddj, nopython=True)(ncjmg__vwjz)


def gen_top_level_agg_func(agg_node, in_col_typs, out_col_typs, parallel,
    udf_func_struct):
    pwayn__obyy = agg_node.pivot_arr is not None
    if agg_node.same_index:
        assert agg_node.input_has_index
    if agg_node.pivot_values is None:
        sgxt__efblh = 1
    else:
        sgxt__efblh = len(agg_node.pivot_values)
    nakvu__ada = tuple('key_' + sanitize_varname(qew__gbucl) for qew__gbucl in
        agg_node.key_names)
    rbjz__oqno = {qew__gbucl: 'in_{}'.format(sanitize_varname(qew__gbucl)) for
        qew__gbucl in agg_node.gb_info_in.keys() if qew__gbucl is not None}
    vbe__znyx = {qew__gbucl: ('out_' + sanitize_varname(qew__gbucl)) for
        qew__gbucl in agg_node.gb_info_out.keys()}
    n_keys = len(agg_node.key_names)
    umwa__lvlpx = ', '.join(nakvu__ada)
    drv__jben = ', '.join(rbjz__oqno.values())
    if drv__jben != '':
        drv__jben = ', ' + drv__jben
    kya__amw = 'def agg_top({}{}{}, pivot_arr):\n'.format(umwa__lvlpx,
        drv__jben, ', index_arg' if agg_node.input_has_index else '')
    for a in (nakvu__ada + tuple(rbjz__oqno.values())):
        kya__amw += f'    {a} = decode_if_dict_array({a})\n'
    if pwayn__obyy:
        kya__amw += f'    pivot_arr = decode_if_dict_array(pivot_arr)\n'
        rgr__qxik = []
        for twsht__ogmls, iuz__alcmu in agg_node.gb_info_in.items():
            if twsht__ogmls is not None:
                for func, kotin__fzy in iuz__alcmu:
                    rgr__qxik.append(rbjz__oqno[twsht__ogmls])
    else:
        rgr__qxik = tuple(rbjz__oqno[twsht__ogmls] for twsht__ogmls,
            kotin__fzy in agg_node.gb_info_out.values() if twsht__ogmls is not
            None)
    ljglu__kie = nakvu__ada + tuple(rgr__qxik)
    kya__amw += '    info_list = [{}{}{}]\n'.format(', '.join(
        'array_to_info({})'.format(a) for a in ljglu__kie), 
        ', array_to_info(index_arg)' if agg_node.input_has_index else '', 
        ', array_to_info(pivot_arr)' if agg_node.is_crosstab else '')
    kya__amw += '    table = arr_info_list_to_table(info_list)\n'
    for tpup__alzyi, qew__gbucl in enumerate(agg_node.gb_info_out.keys()):
        ngpcr__gan = vbe__znyx[qew__gbucl] + '_dummy'
        qcy__yfh = out_col_typs[tpup__alzyi]
        twsht__ogmls, func = agg_node.gb_info_out[qew__gbucl]
        if isinstance(func, pytypes.SimpleNamespace) and func.fname in ['min',
            'max', 'shift'] and isinstance(qcy__yfh, bodo.CategoricalArrayType
            ):
            kya__amw += '    {} = {}\n'.format(ngpcr__gan, rbjz__oqno[
                twsht__ogmls])
        else:
            kya__amw += '    {} = {}\n'.format(ngpcr__gan, _gen_dummy_alloc
                (qcy__yfh, tpup__alzyi, False))
    do_combine = parallel
    allfuncs = []
    tcxz__yofen = []
    func_idx_to_in_col = []
    etm__upotz = []
    srs__xmae = False
    khs__rux = 1
    zidl__mhgj = -1
    nbcut__hct = 0
    sqr__lyxok = 0
    if not pwayn__obyy:
        rlj__ormz = [func for kotin__fzy, func in agg_node.gb_info_out.values()
            ]
    else:
        rlj__ormz = [func for func, kotin__fzy in iuz__alcmu for iuz__alcmu in
            agg_node.gb_info_in.values()]
    for fqasv__nwjbi, func in enumerate(rlj__ormz):
        tcxz__yofen.append(len(allfuncs))
        if func.ftype in {'median', 'nunique'}:
            do_combine = False
        if func.ftype in list_cumulative:
            nbcut__hct += 1
        if hasattr(func, 'skipdropna'):
            srs__xmae = func.skipdropna
        if func.ftype == 'shift':
            khs__rux = func.periods
            do_combine = False
        if func.ftype in {'transform'}:
            sqr__lyxok = func.transform_func
            do_combine = False
        if func.ftype == 'head':
            zidl__mhgj = func.head_n
            do_combine = False
        allfuncs.append(func)
        func_idx_to_in_col.append(fqasv__nwjbi)
        if func.ftype == 'udf':
            etm__upotz.append(func.n_redvars)
        elif func.ftype == 'gen_udf':
            etm__upotz.append(0)
            do_combine = False
    tcxz__yofen.append(len(allfuncs))
    if agg_node.is_crosstab:
        assert len(agg_node.gb_info_out
            ) == sgxt__efblh, 'invalid number of groupby outputs for pivot'
    else:
        assert len(agg_node.gb_info_out) == len(allfuncs
            ) * sgxt__efblh, 'invalid number of groupby outputs'
    if nbcut__hct > 0:
        if nbcut__hct != len(allfuncs):
            raise BodoError(
                f'{agg_node.func_name}(): Cannot mix cumulative operations with other aggregation functions'
                , loc=agg_node.loc)
        do_combine = False
    if udf_func_struct is not None:
        yhe__iet = next_label()
        if udf_func_struct.regular_udfs:
            abf__kddj = types.void(types.voidptr, types.voidptr, types.
                CPointer(types.int64))
            ivzf__fldik = numba.cfunc(abf__kddj, nopython=True)(gen_update_cb
                (udf_func_struct, allfuncs, n_keys, in_col_typs,
                out_col_typs, do_combine, func_idx_to_in_col, yhe__iet))
            kigi__ohu = numba.cfunc(abf__kddj, nopython=True)(gen_combine_cb
                (udf_func_struct, allfuncs, n_keys, out_col_typs, yhe__iet))
            wplf__uzp = numba.cfunc('void(voidptr)', nopython=True)(gen_eval_cb
                (udf_func_struct, allfuncs, n_keys, out_col_typs, yhe__iet))
            udf_func_struct.set_regular_cfuncs(ivzf__fldik, kigi__ohu,
                wplf__uzp)
            for pgexu__ynwed in udf_func_struct.regular_udf_cfuncs:
                gb_agg_cfunc[pgexu__ynwed.native_name] = pgexu__ynwed
                gb_agg_cfunc_addr[pgexu__ynwed.native_name
                    ] = pgexu__ynwed.address
        if udf_func_struct.general_udfs:
            hdudg__arp = gen_general_udf_cb(udf_func_struct, allfuncs,
                n_keys, in_col_typs, out_col_typs, func_idx_to_in_col, yhe__iet
                )
            udf_func_struct.set_general_cfunc(hdudg__arp)
        ect__tognf = []
        bcqr__kacmp = 0
        tpup__alzyi = 0
        for ngpcr__gan, ncjmg__vwjz in zip(vbe__znyx.values(), allfuncs):
            if ncjmg__vwjz.ftype in ('udf', 'gen_udf'):
                ect__tognf.append(ngpcr__gan + '_dummy')
                for lurf__sokcq in range(bcqr__kacmp, bcqr__kacmp +
                    etm__upotz[tpup__alzyi]):
                    ect__tognf.append('data_redvar_dummy_' + str(lurf__sokcq))
                bcqr__kacmp += etm__upotz[tpup__alzyi]
                tpup__alzyi += 1
        if udf_func_struct.regular_udfs:
            gpil__cin = udf_func_struct.var_typs
            for tpup__alzyi, t in enumerate(gpil__cin):
                kya__amw += ('    data_redvar_dummy_{} = np.empty(1, {})\n'
                    .format(tpup__alzyi, _get_np_dtype(t)))
        kya__amw += '    out_info_list_dummy = [{}]\n'.format(', '.join(
            'array_to_info({})'.format(a) for a in ect__tognf))
        kya__amw += (
            '    udf_table_dummy = arr_info_list_to_table(out_info_list_dummy)\n'
            )
        if udf_func_struct.regular_udfs:
            kya__amw += "    add_agg_cfunc_sym(cpp_cb_update, '{}')\n".format(
                ivzf__fldik.native_name)
            kya__amw += "    add_agg_cfunc_sym(cpp_cb_combine, '{}')\n".format(
                kigi__ohu.native_name)
            kya__amw += "    add_agg_cfunc_sym(cpp_cb_eval, '{}')\n".format(
                wplf__uzp.native_name)
            kya__amw += ("    cpp_cb_update_addr = get_agg_udf_addr('{}')\n"
                .format(ivzf__fldik.native_name))
            kya__amw += ("    cpp_cb_combine_addr = get_agg_udf_addr('{}')\n"
                .format(kigi__ohu.native_name))
            kya__amw += ("    cpp_cb_eval_addr = get_agg_udf_addr('{}')\n".
                format(wplf__uzp.native_name))
        else:
            kya__amw += '    cpp_cb_update_addr = 0\n'
            kya__amw += '    cpp_cb_combine_addr = 0\n'
            kya__amw += '    cpp_cb_eval_addr = 0\n'
        if udf_func_struct.general_udfs:
            pgexu__ynwed = udf_func_struct.general_udf_cfunc
            gb_agg_cfunc[pgexu__ynwed.native_name] = pgexu__ynwed
            gb_agg_cfunc_addr[pgexu__ynwed.native_name] = pgexu__ynwed.address
            kya__amw += "    add_agg_cfunc_sym(cpp_cb_general, '{}')\n".format(
                pgexu__ynwed.native_name)
            kya__amw += ("    cpp_cb_general_addr = get_agg_udf_addr('{}')\n"
                .format(pgexu__ynwed.native_name))
        else:
            kya__amw += '    cpp_cb_general_addr = 0\n'
    else:
        kya__amw += (
            '    udf_table_dummy = arr_info_list_to_table([array_to_info(np.empty(1))])\n'
            )
        kya__amw += '    cpp_cb_update_addr = 0\n'
        kya__amw += '    cpp_cb_combine_addr = 0\n'
        kya__amw += '    cpp_cb_eval_addr = 0\n'
        kya__amw += '    cpp_cb_general_addr = 0\n'
    kya__amw += '    ftypes = np.array([{}, 0], dtype=np.int32)\n'.format(', '
        .join([str(supported_agg_funcs.index(ncjmg__vwjz.ftype)) for
        ncjmg__vwjz in allfuncs] + ['0']))
    kya__amw += '    func_offsets = np.array({}, dtype=np.int32)\n'.format(str
        (tcxz__yofen))
    if len(etm__upotz) > 0:
        kya__amw += '    udf_ncols = np.array({}, dtype=np.int32)\n'.format(str
            (etm__upotz))
    else:
        kya__amw += '    udf_ncols = np.array([0], np.int32)\n'
    if pwayn__obyy:
        kya__amw += '    arr_type = coerce_to_array({})\n'.format(agg_node.
            pivot_values)
        kya__amw += '    arr_info = array_to_info(arr_type)\n'
        kya__amw += '    dispatch_table = arr_info_list_to_table([arr_info])\n'
        kya__amw += '    pivot_info = array_to_info(pivot_arr)\n'
        kya__amw += (
            '    dispatch_info = arr_info_list_to_table([pivot_info])\n')
        kya__amw += (
            """    out_table = pivot_groupby_and_aggregate(table, {}, dispatch_table, dispatch_info, {}, ftypes.ctypes, func_offsets.ctypes, udf_ncols.ctypes, {}, {}, {}, {}, {}, cpp_cb_update_addr, cpp_cb_combine_addr, cpp_cb_eval_addr, udf_table_dummy)
"""
            .format(n_keys, agg_node.input_has_index, parallel, agg_node.
            is_crosstab, srs__xmae, agg_node.return_key, agg_node.same_index))
        kya__amw += '    delete_info_decref_array(pivot_info)\n'
        kya__amw += '    delete_info_decref_array(arr_info)\n'
    else:
        kya__amw += (
            """    out_table = groupby_and_aggregate(table, {}, {}, ftypes.ctypes, func_offsets.ctypes, udf_ncols.ctypes, {}, {}, {}, {}, {}, {}, {}, {}, cpp_cb_update_addr, cpp_cb_combine_addr, cpp_cb_eval_addr, cpp_cb_general_addr, udf_table_dummy)
"""
            .format(n_keys, agg_node.input_has_index, parallel, srs__xmae,
            khs__rux, sqr__lyxok, zidl__mhgj, agg_node.return_key, agg_node
            .same_index, agg_node.dropna))
    iwfw__mjmc = 0
    if agg_node.return_key:
        for tpup__alzyi, wmsze__ycppw in enumerate(nakvu__ada):
            kya__amw += (
                '    {} = info_to_array(info_from_table(out_table, {}), {})\n'
                .format(wmsze__ycppw, iwfw__mjmc, wmsze__ycppw))
            iwfw__mjmc += 1
    for ngpcr__gan in vbe__znyx.values():
        kya__amw += (
            '    {} = info_to_array(info_from_table(out_table, {}), {})\n'.
            format(ngpcr__gan, iwfw__mjmc, ngpcr__gan + '_dummy'))
        iwfw__mjmc += 1
    if agg_node.same_index:
        kya__amw += (
            """    out_index_arg = info_to_array(info_from_table(out_table, {}), index_arg)
"""
            .format(iwfw__mjmc))
        iwfw__mjmc += 1
    kya__amw += (
        f"    ev_clean = bodo.utils.tracing.Event('tables_clean_up', {parallel})\n"
        )
    kya__amw += '    delete_table_decref_arrays(table)\n'
    kya__amw += '    delete_table_decref_arrays(udf_table_dummy)\n'
    kya__amw += '    delete_table(out_table)\n'
    kya__amw += f'    ev_clean.finalize()\n'
    mukr__jeqtr = tuple(vbe__znyx.values())
    if agg_node.return_key:
        mukr__jeqtr += tuple(nakvu__ada)
    kya__amw += '    return ({},{})\n'.format(', '.join(mukr__jeqtr), 
        ' out_index_arg,' if agg_node.same_index else '')
    htd__ixrh = {}
    exec(kya__amw, {}, htd__ixrh)
    yjw__hdbs = htd__ixrh['agg_top']
    return yjw__hdbs


def compile_to_optimized_ir(func, arg_typs, typingctx, targetctx):
    code = func.code if hasattr(func, 'code') else func.__code__
    closure = func.closure if hasattr(func, 'closure') else func.__closure__
    f_ir = get_ir_of_code(func.__globals__, code)
    replace_closures(f_ir, closure, code)
    for block in f_ir.blocks.values():
        for lgjwm__irkse in block.body:
            if is_call_assign(lgjwm__irkse) and find_callname(f_ir,
                lgjwm__irkse.value) == ('len', 'builtins'
                ) and lgjwm__irkse.value.args[0].name == f_ir.arg_names[0]:
                thnto__zyuxo = get_definition(f_ir, lgjwm__irkse.value.func)
                thnto__zyuxo.name = 'dummy_agg_count'
                thnto__zyuxo.value = dummy_agg_count
    hkjuv__jdq = get_name_var_table(f_ir.blocks)
    ivo__usfab = {}
    for name, kotin__fzy in hkjuv__jdq.items():
        ivo__usfab[name] = mk_unique_var(name)
    replace_var_names(f_ir.blocks, ivo__usfab)
    f_ir._definitions = build_definitions(f_ir.blocks)
    assert f_ir.arg_count == 1, 'agg function should have one input'
    zev__kvr = numba.core.compiler.Flags()
    zev__kvr.nrt = True
    zmtka__oxso = bodo.transforms.untyped_pass.UntypedPass(f_ir, typingctx,
        arg_typs, {}, {}, zev__kvr)
    zmtka__oxso.run()
    f_ir._definitions = build_definitions(f_ir.blocks)
    typemap, wpty__etbgf, calltypes, kotin__fzy = (numba.core.typed_passes.
        type_inference_stage(typingctx, targetctx, f_ir, arg_typs, None))
    pbtpn__ogka = numba.core.cpu.ParallelOptions(True)
    targetctx = numba.core.cpu.CPUContext(typingctx)
    dir__axvdq = namedtuple('DummyPipeline', ['typingctx', 'targetctx',
        'args', 'func_ir', 'typemap', 'return_type', 'calltypes',
        'type_annotation', 'locals', 'flags', 'pipeline'])
    fju__vii = namedtuple('TypeAnnotation', ['typemap', 'calltypes'])
    ewb__rjki = fju__vii(typemap, calltypes)
    pm = dir__axvdq(typingctx, targetctx, None, f_ir, typemap, wpty__etbgf,
        calltypes, ewb__rjki, {}, zev__kvr, None)
    kqytb__tzo = (numba.core.compiler.DefaultPassBuilder.
        define_untyped_pipeline(pm))
    pm = dir__axvdq(typingctx, targetctx, None, f_ir, typemap, wpty__etbgf,
        calltypes, ewb__rjki, {}, zev__kvr, kqytb__tzo)
    bzeo__doc = numba.core.typed_passes.InlineOverloads()
    bzeo__doc.run_pass(pm)
    lulf__vevvs = bodo.transforms.series_pass.SeriesPass(f_ir, typingctx,
        targetctx, typemap, calltypes, {}, False)
    lulf__vevvs.run()
    for block in f_ir.blocks.values():
        for lgjwm__irkse in block.body:
            if is_assign(lgjwm__irkse) and isinstance(lgjwm__irkse.value, (
                ir.Arg, ir.Var)) and isinstance(typemap[lgjwm__irkse.target
                .name], SeriesType):
                ywo__nzmg = typemap.pop(lgjwm__irkse.target.name)
                typemap[lgjwm__irkse.target.name] = ywo__nzmg.data
            if is_call_assign(lgjwm__irkse) and find_callname(f_ir,
                lgjwm__irkse.value) == ('get_series_data',
                'bodo.hiframes.pd_series_ext'):
                f_ir._definitions[lgjwm__irkse.target.name].remove(lgjwm__irkse
                    .value)
                lgjwm__irkse.value = lgjwm__irkse.value.args[0]
                f_ir._definitions[lgjwm__irkse.target.name].append(lgjwm__irkse
                    .value)
            if is_call_assign(lgjwm__irkse) and find_callname(f_ir,
                lgjwm__irkse.value) == ('isna', 'bodo.libs.array_kernels'):
                f_ir._definitions[lgjwm__irkse.target.name].remove(lgjwm__irkse
                    .value)
                lgjwm__irkse.value = ir.Const(False, lgjwm__irkse.loc)
                f_ir._definitions[lgjwm__irkse.target.name].append(lgjwm__irkse
                    .value)
            if is_call_assign(lgjwm__irkse) and find_callname(f_ir,
                lgjwm__irkse.value) == ('setna', 'bodo.libs.array_kernels'):
                f_ir._definitions[lgjwm__irkse.target.name].remove(lgjwm__irkse
                    .value)
                lgjwm__irkse.value = ir.Const(False, lgjwm__irkse.loc)
                f_ir._definitions[lgjwm__irkse.target.name].append(lgjwm__irkse
                    .value)
    bodo.transforms.untyped_pass.remove_dead_branches(f_ir)
    sqhi__vvp = numba.parfors.parfor.PreParforPass(f_ir, typemap, calltypes,
        typingctx, targetctx, pbtpn__ogka)
    sqhi__vvp.run()
    f_ir._definitions = build_definitions(f_ir.blocks)
    yvj__gnaqi = numba.core.compiler.StateDict()
    yvj__gnaqi.func_ir = f_ir
    yvj__gnaqi.typemap = typemap
    yvj__gnaqi.calltypes = calltypes
    yvj__gnaqi.typingctx = typingctx
    yvj__gnaqi.targetctx = targetctx
    yvj__gnaqi.return_type = wpty__etbgf
    numba.core.rewrites.rewrite_registry.apply('after-inference', yvj__gnaqi)
    iqq__gtc = numba.parfors.parfor.ParforPass(f_ir, typemap, calltypes,
        wpty__etbgf, typingctx, targetctx, pbtpn__ogka, zev__kvr, {})
    iqq__gtc.run()
    remove_dels(f_ir.blocks)
    numba.parfors.parfor.maximize_fusion(f_ir, f_ir.blocks, typemap, False)
    return f_ir, pm


def replace_closures(f_ir, closure, code):
    if closure:
        closure = f_ir.get_definition(closure)
        if isinstance(closure, tuple):
            pnaqi__hcwnn = ctypes.pythonapi.PyCell_Get
            pnaqi__hcwnn.restype = ctypes.py_object
            pnaqi__hcwnn.argtypes = ctypes.py_object,
            erc__ptuyr = tuple(pnaqi__hcwnn(hpkpw__fzx) for hpkpw__fzx in
                closure)
        else:
            assert isinstance(closure, ir.Expr) and closure.op == 'build_tuple'
            erc__ptuyr = closure.items
        assert len(code.co_freevars) == len(erc__ptuyr)
        numba.core.inline_closurecall._replace_freevars(f_ir.blocks, erc__ptuyr
            )


class RegularUDFGenerator(object):

    def __init__(self, in_col_types, out_col_types, pivot_typ, pivot_values,
        is_crosstab, typingctx, targetctx):
        self.in_col_types = in_col_types
        self.out_col_types = out_col_types
        self.pivot_typ = pivot_typ
        self.pivot_values = pivot_values
        self.is_crosstab = is_crosstab
        self.typingctx = typingctx
        self.targetctx = targetctx
        self.all_reduce_vars = []
        self.all_vartypes = []
        self.all_init_nodes = []
        self.all_eval_funcs = []
        self.all_update_funcs = []
        self.all_combine_funcs = []
        self.curr_offset = 0
        self.redvar_offsets = [0]

    def add_udf(self, in_col_typ, func):
        bfml__tcrls = SeriesType(in_col_typ.dtype, in_col_typ, None,
            string_type)
        f_ir, pm = compile_to_optimized_ir(func, (bfml__tcrls,), self.
            typingctx, self.targetctx)
        f_ir._definitions = build_definitions(f_ir.blocks)
        assert len(f_ir.blocks
            ) == 1 and 0 in f_ir.blocks, 'only simple functions with one block supported for aggregation'
        block = f_ir.blocks[0]
        gfwe__rpol, arr_var = _rm_arg_agg_block(block, pm.typemap)
        mqki__ozkrn = -1
        for tpup__alzyi, lgjwm__irkse in enumerate(gfwe__rpol):
            if isinstance(lgjwm__irkse, numba.parfors.parfor.Parfor):
                assert mqki__ozkrn == -1, 'only one parfor for aggregation function'
                mqki__ozkrn = tpup__alzyi
        parfor = None
        if mqki__ozkrn != -1:
            parfor = gfwe__rpol[mqki__ozkrn]
            remove_dels(parfor.loop_body)
            remove_dels({(0): parfor.init_block})
        init_nodes = []
        if parfor:
            init_nodes = gfwe__rpol[:mqki__ozkrn] + parfor.init_block.body
        eval_nodes = gfwe__rpol[mqki__ozkrn + 1:]
        redvars = []
        var_to_redvar = {}
        if parfor:
            redvars, var_to_redvar = get_parfor_reductions(parfor, parfor.
                params, pm.calltypes)
        func.ncols_pre_shuffle = len(redvars)
        func.ncols_post_shuffle = len(redvars) + 1
        func.n_redvars = len(redvars)
        reduce_vars = [0] * len(redvars)
        for lgjwm__irkse in init_nodes:
            if is_assign(lgjwm__irkse) and lgjwm__irkse.target.name in redvars:
                ind = redvars.index(lgjwm__irkse.target.name)
                reduce_vars[ind] = lgjwm__irkse.target
        var_types = [pm.typemap[pnr__vndwl] for pnr__vndwl in redvars]
        aqjau__adcuq = gen_combine_func(f_ir, parfor, redvars,
            var_to_redvar, var_types, arr_var, pm, self.typingctx, self.
            targetctx)
        init_nodes = _mv_read_only_init_vars(init_nodes, parfor, eval_nodes)
        jzimn__sia = gen_update_func(parfor, redvars, var_to_redvar,
            var_types, arr_var, in_col_typ, pm, self.typingctx, self.targetctx)
        dklsf__aih = gen_eval_func(f_ir, eval_nodes, reduce_vars, var_types,
            pm, self.typingctx, self.targetctx)
        self.all_reduce_vars += reduce_vars
        self.all_vartypes += var_types
        self.all_init_nodes += init_nodes
        self.all_eval_funcs.append(dklsf__aih)
        self.all_update_funcs.append(jzimn__sia)
        self.all_combine_funcs.append(aqjau__adcuq)
        self.curr_offset += len(redvars)
        self.redvar_offsets.append(self.curr_offset)

    def gen_all_func(self):
        if len(self.all_update_funcs) == 0:
            return None
        self.all_vartypes = self.all_vartypes * len(self.pivot_values
            ) if self.pivot_values is not None else self.all_vartypes
        self.all_reduce_vars = self.all_reduce_vars * len(self.pivot_values
            ) if self.pivot_values is not None else self.all_reduce_vars
        rhn__stxoq = gen_init_func(self.all_init_nodes, self.
            all_reduce_vars, self.all_vartypes, self.typingctx, self.targetctx)
        tiljo__dvnu = gen_all_update_func(self.all_update_funcs, self.
            all_vartypes, self.in_col_types, self.redvar_offsets, self.
            typingctx, self.targetctx, self.pivot_typ, self.pivot_values,
            self.is_crosstab)
        mam__ymiub = gen_all_combine_func(self.all_combine_funcs, self.
            all_vartypes, self.redvar_offsets, self.typingctx, self.
            targetctx, self.pivot_typ, self.pivot_values)
        jisg__qnmbu = gen_all_eval_func(self.all_eval_funcs, self.
            all_vartypes, self.redvar_offsets, self.out_col_types, self.
            typingctx, self.targetctx, self.pivot_values)
        return (self.all_vartypes, rhn__stxoq, tiljo__dvnu, mam__ymiub,
            jisg__qnmbu)


class GeneralUDFGenerator(object):

    def __init__(self):
        self.funcs = []

    def add_udf(self, func):
        self.funcs.append(bodo.jit(distributed=False)(func))
        func.ncols_pre_shuffle = 1
        func.ncols_post_shuffle = 1
        func.n_redvars = 0

    def gen_all_func(self):
        if len(self.funcs) > 0:
            return self.funcs
        else:
            return None


def get_udf_func_struct(agg_func, input_has_index, in_col_types,
    out_col_types, typingctx, targetctx, pivot_typ, pivot_values, is_crosstab):
    if is_crosstab and len(in_col_types) == 0:
        in_col_types = [types.Array(types.intp, 1, 'C')]
    hdvda__qgh = []
    for t, ncjmg__vwjz in zip(in_col_types, agg_func):
        hdvda__qgh.append((t, ncjmg__vwjz))
    yxys__voej = RegularUDFGenerator(in_col_types, out_col_types, pivot_typ,
        pivot_values, is_crosstab, typingctx, targetctx)
    oyl__vbz = GeneralUDFGenerator()
    for in_col_typ, func in hdvda__qgh:
        if func.ftype not in ('udf', 'gen_udf'):
            continue
        try:
            yxys__voej.add_udf(in_col_typ, func)
        except:
            oyl__vbz.add_udf(func)
            func.ftype = 'gen_udf'
    regular_udf_funcs = yxys__voej.gen_all_func()
    general_udf_funcs = oyl__vbz.gen_all_func()
    if regular_udf_funcs is not None or general_udf_funcs is not None:
        return AggUDFStruct(regular_udf_funcs, general_udf_funcs)
    else:
        return None


def _mv_read_only_init_vars(init_nodes, parfor, eval_nodes):
    if not parfor:
        return init_nodes
    jll__gzoc = compute_use_defs(parfor.loop_body)
    rinwp__rsevg = set()
    for nmxy__ncla in jll__gzoc.usemap.values():
        rinwp__rsevg |= nmxy__ncla
    zaim__cdmp = set()
    for nmxy__ncla in jll__gzoc.defmap.values():
        zaim__cdmp |= nmxy__ncla
    mdlej__zwnvl = ir.Block(ir.Scope(None, parfor.loc), parfor.loc)
    mdlej__zwnvl.body = eval_nodes
    dtigf__wauy = compute_use_defs({(0): mdlej__zwnvl})
    xxjjd__klgfr = dtigf__wauy.usemap[0]
    uej__cey = set()
    vky__valm = []
    qoohj__xxlza = []
    for lgjwm__irkse in reversed(init_nodes):
        ksy__nvu = {pnr__vndwl.name for pnr__vndwl in lgjwm__irkse.list_vars()}
        if is_assign(lgjwm__irkse):
            pnr__vndwl = lgjwm__irkse.target.name
            ksy__nvu.remove(pnr__vndwl)
            if (pnr__vndwl in rinwp__rsevg and pnr__vndwl not in uej__cey and
                pnr__vndwl not in xxjjd__klgfr and pnr__vndwl not in zaim__cdmp
                ):
                qoohj__xxlza.append(lgjwm__irkse)
                rinwp__rsevg |= ksy__nvu
                zaim__cdmp.add(pnr__vndwl)
                continue
        uej__cey |= ksy__nvu
        vky__valm.append(lgjwm__irkse)
    qoohj__xxlza.reverse()
    vky__valm.reverse()
    sntpb__ihdvi = min(parfor.loop_body.keys())
    zkxp__zmrw = parfor.loop_body[sntpb__ihdvi]
    zkxp__zmrw.body = qoohj__xxlza + zkxp__zmrw.body
    return vky__valm


def gen_init_func(init_nodes, reduce_vars, var_types, typingctx, targetctx):
    dxpb__ybef = (numba.parfors.parfor.max_checker, numba.parfors.parfor.
        min_checker, numba.parfors.parfor.argmax_checker, numba.parfors.
        parfor.argmin_checker)
    lvp__oyia = set()
    lyhy__sqd = []
    for lgjwm__irkse in init_nodes:
        if is_assign(lgjwm__irkse) and isinstance(lgjwm__irkse.value, ir.Global
            ) and isinstance(lgjwm__irkse.value.value, pytypes.FunctionType
            ) and lgjwm__irkse.value.value in dxpb__ybef:
            lvp__oyia.add(lgjwm__irkse.target.name)
        elif is_call_assign(lgjwm__irkse
            ) and lgjwm__irkse.value.func.name in lvp__oyia:
            pass
        else:
            lyhy__sqd.append(lgjwm__irkse)
    init_nodes = lyhy__sqd
    uby__wtjxg = types.Tuple(var_types)
    ayf__klar = lambda : None
    f_ir = compile_to_numba_ir(ayf__klar, {})
    block = list(f_ir.blocks.values())[0]
    loc = block.loc
    plyic__csooa = ir.Var(block.scope, mk_unique_var('init_tup'), loc)
    ecmvk__xhnhu = ir.Assign(ir.Expr.build_tuple(reduce_vars, loc),
        plyic__csooa, loc)
    block.body = block.body[-2:]
    block.body = init_nodes + [ecmvk__xhnhu] + block.body
    block.body[-2].value.value = plyic__csooa
    nioj__lfe = compiler.compile_ir(typingctx, targetctx, f_ir, (),
        uby__wtjxg, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    fmin__qauyy = numba.core.target_extension.dispatcher_registry[cpu_target](
        ayf__klar)
    fmin__qauyy.add_overload(nioj__lfe)
    return fmin__qauyy


def gen_all_update_func(update_funcs, reduce_var_types, in_col_types,
    redvar_offsets, typingctx, targetctx, pivot_typ, pivot_values, is_crosstab
    ):
    wvfod__cylh = len(update_funcs)
    ewjr__rsdyv = len(in_col_types)
    if pivot_values is not None:
        assert ewjr__rsdyv == 1
    kya__amw = 'def update_all_f(redvar_arrs, data_in, w_ind, i, pivot_arr):\n'
    if pivot_values is not None:
        vqczw__qvre = redvar_offsets[ewjr__rsdyv]
        kya__amw += '  pv = pivot_arr[i]\n'
        for lurf__sokcq, udy__icpi in enumerate(pivot_values):
            lnh__bvfi = 'el' if lurf__sokcq != 0 else ''
            kya__amw += "  {}if pv == '{}':\n".format(lnh__bvfi, udy__icpi)
            tzzjh__nmbt = vqczw__qvre * lurf__sokcq
            apr__pepxk = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                tpup__alzyi) for tpup__alzyi in range(tzzjh__nmbt +
                redvar_offsets[0], tzzjh__nmbt + redvar_offsets[1])])
            hlenb__mac = 'data_in[0][i]'
            if is_crosstab:
                hlenb__mac = '0'
            kya__amw += '    {} = update_vars_0({}, {})\n'.format(apr__pepxk,
                apr__pepxk, hlenb__mac)
    else:
        for lurf__sokcq in range(wvfod__cylh):
            apr__pepxk = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                tpup__alzyi) for tpup__alzyi in range(redvar_offsets[
                lurf__sokcq], redvar_offsets[lurf__sokcq + 1])])
            if apr__pepxk:
                kya__amw += ('  {} = update_vars_{}({},  data_in[{}][i])\n'
                    .format(apr__pepxk, lurf__sokcq, apr__pepxk, 0 if 
                    ewjr__rsdyv == 1 else lurf__sokcq))
    kya__amw += '  return\n'
    ubm__rjee = {}
    for tpup__alzyi, ncjmg__vwjz in enumerate(update_funcs):
        ubm__rjee['update_vars_{}'.format(tpup__alzyi)] = ncjmg__vwjz
    htd__ixrh = {}
    exec(kya__amw, ubm__rjee, htd__ixrh)
    xdfc__zrd = htd__ixrh['update_all_f']
    return numba.njit(no_cpython_wrapper=True)(xdfc__zrd)


def gen_all_combine_func(combine_funcs, reduce_var_types, redvar_offsets,
    typingctx, targetctx, pivot_typ, pivot_values):
    ylpo__ypyy = types.Tuple([types.Array(t, 1, 'C') for t in reduce_var_types]
        )
    arg_typs = ylpo__ypyy, ylpo__ypyy, types.intp, types.intp, pivot_typ
    yjyu__ibj = len(redvar_offsets) - 1
    vqczw__qvre = redvar_offsets[yjyu__ibj]
    kya__amw = (
        'def combine_all_f(redvar_arrs, recv_arrs, w_ind, i, pivot_arr):\n')
    if pivot_values is not None:
        assert yjyu__ibj == 1
        for fcz__aaeig in range(len(pivot_values)):
            tzzjh__nmbt = vqczw__qvre * fcz__aaeig
            apr__pepxk = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                tpup__alzyi) for tpup__alzyi in range(tzzjh__nmbt +
                redvar_offsets[0], tzzjh__nmbt + redvar_offsets[1])])
            kypi__wzep = ', '.join(['recv_arrs[{}][i]'.format(tpup__alzyi) for
                tpup__alzyi in range(tzzjh__nmbt + redvar_offsets[0], 
                tzzjh__nmbt + redvar_offsets[1])])
            kya__amw += '  {} = combine_vars_0({}, {})\n'.format(apr__pepxk,
                apr__pepxk, kypi__wzep)
    else:
        for lurf__sokcq in range(yjyu__ibj):
            apr__pepxk = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                tpup__alzyi) for tpup__alzyi in range(redvar_offsets[
                lurf__sokcq], redvar_offsets[lurf__sokcq + 1])])
            kypi__wzep = ', '.join(['recv_arrs[{}][i]'.format(tpup__alzyi) for
                tpup__alzyi in range(redvar_offsets[lurf__sokcq],
                redvar_offsets[lurf__sokcq + 1])])
            if kypi__wzep:
                kya__amw += '  {} = combine_vars_{}({}, {})\n'.format(
                    apr__pepxk, lurf__sokcq, apr__pepxk, kypi__wzep)
    kya__amw += '  return\n'
    ubm__rjee = {}
    for tpup__alzyi, ncjmg__vwjz in enumerate(combine_funcs):
        ubm__rjee['combine_vars_{}'.format(tpup__alzyi)] = ncjmg__vwjz
    htd__ixrh = {}
    exec(kya__amw, ubm__rjee, htd__ixrh)
    zmy__tddkf = htd__ixrh['combine_all_f']
    f_ir = compile_to_numba_ir(zmy__tddkf, ubm__rjee)
    mam__ymiub = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        types.none, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    fmin__qauyy = numba.core.target_extension.dispatcher_registry[cpu_target](
        zmy__tddkf)
    fmin__qauyy.add_overload(mam__ymiub)
    return fmin__qauyy


def gen_all_eval_func(eval_funcs, reduce_var_types, redvar_offsets,
    out_col_typs, typingctx, targetctx, pivot_values):
    ylpo__ypyy = types.Tuple([types.Array(t, 1, 'C') for t in reduce_var_types]
        )
    out_col_typs = types.Tuple(out_col_typs)
    yjyu__ibj = len(redvar_offsets) - 1
    vqczw__qvre = redvar_offsets[yjyu__ibj]
    kya__amw = 'def eval_all_f(redvar_arrs, out_arrs, j):\n'
    if pivot_values is not None:
        assert yjyu__ibj == 1
        for lurf__sokcq in range(len(pivot_values)):
            tzzjh__nmbt = vqczw__qvre * lurf__sokcq
            apr__pepxk = ', '.join(['redvar_arrs[{}][j]'.format(tpup__alzyi
                ) for tpup__alzyi in range(tzzjh__nmbt + redvar_offsets[0],
                tzzjh__nmbt + redvar_offsets[1])])
            kya__amw += '  out_arrs[{}][j] = eval_vars_0({})\n'.format(
                lurf__sokcq, apr__pepxk)
    else:
        for lurf__sokcq in range(yjyu__ibj):
            apr__pepxk = ', '.join(['redvar_arrs[{}][j]'.format(tpup__alzyi
                ) for tpup__alzyi in range(redvar_offsets[lurf__sokcq],
                redvar_offsets[lurf__sokcq + 1])])
            kya__amw += '  out_arrs[{}][j] = eval_vars_{}({})\n'.format(
                lurf__sokcq, lurf__sokcq, apr__pepxk)
    kya__amw += '  return\n'
    ubm__rjee = {}
    for tpup__alzyi, ncjmg__vwjz in enumerate(eval_funcs):
        ubm__rjee['eval_vars_{}'.format(tpup__alzyi)] = ncjmg__vwjz
    htd__ixrh = {}
    exec(kya__amw, ubm__rjee, htd__ixrh)
    kus__dxsqx = htd__ixrh['eval_all_f']
    return numba.njit(no_cpython_wrapper=True)(kus__dxsqx)


def gen_eval_func(f_ir, eval_nodes, reduce_vars, var_types, pm, typingctx,
    targetctx):
    bndbm__etrdm = len(var_types)
    sabb__uexob = [f'in{tpup__alzyi}' for tpup__alzyi in range(bndbm__etrdm)]
    uby__wtjxg = types.unliteral(pm.typemap[eval_nodes[-1].value.name])
    eydz__jsnsy = uby__wtjxg(0)
    kya__amw = 'def agg_eval({}):\n return _zero\n'.format(', '.join(
        sabb__uexob))
    htd__ixrh = {}
    exec(kya__amw, {'_zero': eydz__jsnsy}, htd__ixrh)
    vjhtn__ocxlf = htd__ixrh['agg_eval']
    arg_typs = tuple(var_types)
    f_ir = compile_to_numba_ir(vjhtn__ocxlf, {'numba': numba, 'bodo': bodo,
        'np': np, '_zero': eydz__jsnsy}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=arg_typs, typemap=pm.typemap, calltypes=pm.
        calltypes)
    block = list(f_ir.blocks.values())[0]
    ahcna__uzog = []
    for tpup__alzyi, pnr__vndwl in enumerate(reduce_vars):
        ahcna__uzog.append(ir.Assign(block.body[tpup__alzyi].target,
            pnr__vndwl, pnr__vndwl.loc))
        for rly__crw in pnr__vndwl.versioned_names:
            ahcna__uzog.append(ir.Assign(pnr__vndwl, ir.Var(pnr__vndwl.
                scope, rly__crw, pnr__vndwl.loc), pnr__vndwl.loc))
    block.body = block.body[:bndbm__etrdm] + ahcna__uzog + eval_nodes
    dklsf__aih = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        uby__wtjxg, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    fmin__qauyy = numba.core.target_extension.dispatcher_registry[cpu_target](
        vjhtn__ocxlf)
    fmin__qauyy.add_overload(dklsf__aih)
    return fmin__qauyy


def gen_combine_func(f_ir, parfor, redvars, var_to_redvar, var_types,
    arr_var, pm, typingctx, targetctx):
    if not parfor:
        return numba.njit(lambda : ())
    bndbm__etrdm = len(redvars)
    ljcq__zrt = [f'v{tpup__alzyi}' for tpup__alzyi in range(bndbm__etrdm)]
    sabb__uexob = [f'in{tpup__alzyi}' for tpup__alzyi in range(bndbm__etrdm)]
    kya__amw = 'def agg_combine({}):\n'.format(', '.join(ljcq__zrt +
        sabb__uexob))
    qnqyx__gln = wrap_parfor_blocks(parfor)
    rejqu__ttfd = find_topo_order(qnqyx__gln)
    rejqu__ttfd = rejqu__ttfd[1:]
    unwrap_parfor_blocks(parfor)
    aviy__lpx = {}
    yclr__xlu = []
    for ogbp__cuhr in rejqu__ttfd:
        aqda__cor = parfor.loop_body[ogbp__cuhr]
        for lgjwm__irkse in aqda__cor.body:
            if is_call_assign(lgjwm__irkse) and guard(find_callname, f_ir,
                lgjwm__irkse.value) == ('__special_combine',
                'bodo.ir.aggregate'):
                args = lgjwm__irkse.value.args
                rloy__pqk = []
                bnsi__hfr = []
                for pnr__vndwl in args[:-1]:
                    ind = redvars.index(pnr__vndwl.name)
                    yclr__xlu.append(ind)
                    rloy__pqk.append('v{}'.format(ind))
                    bnsi__hfr.append('in{}'.format(ind))
                gadzh__xjys = '__special_combine__{}'.format(len(aviy__lpx))
                kya__amw += '    ({},) = {}({})\n'.format(', '.join(
                    rloy__pqk), gadzh__xjys, ', '.join(rloy__pqk + bnsi__hfr))
                lcw__qxnyb = ir.Expr.call(args[-1], [], (), aqda__cor.loc)
                aie__hui = guard(find_callname, f_ir, lcw__qxnyb)
                assert aie__hui == ('_var_combine', 'bodo.ir.aggregate')
                aie__hui = bodo.ir.aggregate._var_combine
                aviy__lpx[gadzh__xjys] = aie__hui
            if is_assign(lgjwm__irkse) and lgjwm__irkse.target.name in redvars:
                lix__byfj = lgjwm__irkse.target.name
                ind = redvars.index(lix__byfj)
                if ind in yclr__xlu:
                    continue
                if len(f_ir._definitions[lix__byfj]) == 2:
                    var_def = f_ir._definitions[lix__byfj][0]
                    kya__amw += _match_reduce_def(var_def, f_ir, ind)
                    var_def = f_ir._definitions[lix__byfj][1]
                    kya__amw += _match_reduce_def(var_def, f_ir, ind)
    kya__amw += '    return {}'.format(', '.join(['v{}'.format(tpup__alzyi) for
        tpup__alzyi in range(bndbm__etrdm)]))
    htd__ixrh = {}
    exec(kya__amw, {}, htd__ixrh)
    nihzc__qrakg = htd__ixrh['agg_combine']
    arg_typs = tuple(2 * var_types)
    ubm__rjee = {'numba': numba, 'bodo': bodo, 'np': np}
    ubm__rjee.update(aviy__lpx)
    f_ir = compile_to_numba_ir(nihzc__qrakg, ubm__rjee, typingctx=typingctx,
        targetctx=targetctx, arg_typs=arg_typs, typemap=pm.typemap,
        calltypes=pm.calltypes)
    block = list(f_ir.blocks.values())[0]
    uby__wtjxg = pm.typemap[block.body[-1].value.name]
    aqjau__adcuq = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        uby__wtjxg, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    fmin__qauyy = numba.core.target_extension.dispatcher_registry[cpu_target](
        nihzc__qrakg)
    fmin__qauyy.add_overload(aqjau__adcuq)
    return fmin__qauyy


def _match_reduce_def(var_def, f_ir, ind):
    kya__amw = ''
    while isinstance(var_def, ir.Var):
        var_def = guard(get_definition, f_ir, var_def)
    if isinstance(var_def, ir.Expr
        ) and var_def.op == 'inplace_binop' and var_def.fn in ('+=',
        operator.iadd):
        kya__amw = '    v{} += in{}\n'.format(ind, ind)
    if isinstance(var_def, ir.Expr) and var_def.op == 'call':
        vqs__fpjc = guard(find_callname, f_ir, var_def)
        if vqs__fpjc == ('min', 'builtins'):
            kya__amw = '    v{} = min(v{}, in{})\n'.format(ind, ind, ind)
        if vqs__fpjc == ('max', 'builtins'):
            kya__amw = '    v{} = max(v{}, in{})\n'.format(ind, ind, ind)
    return kya__amw


def gen_update_func(parfor, redvars, var_to_redvar, var_types, arr_var,
    in_col_typ, pm, typingctx, targetctx):
    if not parfor:
        return numba.njit(lambda A: ())
    bndbm__etrdm = len(redvars)
    xkrd__sehv = 1
    zippj__bzooo = []
    for tpup__alzyi in range(xkrd__sehv):
        uftg__cze = ir.Var(arr_var.scope, f'$input{tpup__alzyi}', arr_var.loc)
        zippj__bzooo.append(uftg__cze)
    mxqu__jenwc = parfor.loop_nests[0].index_variable
    pudbb__sfwdn = [0] * bndbm__etrdm
    for aqda__cor in parfor.loop_body.values():
        jtk__hyjnt = []
        for lgjwm__irkse in aqda__cor.body:
            if is_var_assign(lgjwm__irkse
                ) and lgjwm__irkse.value.name == mxqu__jenwc.name:
                continue
            if is_getitem(lgjwm__irkse
                ) and lgjwm__irkse.value.value.name == arr_var.name:
                lgjwm__irkse.value = zippj__bzooo[0]
            if is_call_assign(lgjwm__irkse) and guard(find_callname, pm.
                func_ir, lgjwm__irkse.value) == ('isna',
                'bodo.libs.array_kernels') and lgjwm__irkse.value.args[0
                ].name == arr_var.name:
                lgjwm__irkse.value = ir.Const(False, lgjwm__irkse.target.loc)
            if is_assign(lgjwm__irkse) and lgjwm__irkse.target.name in redvars:
                ind = redvars.index(lgjwm__irkse.target.name)
                pudbb__sfwdn[ind] = lgjwm__irkse.target
            jtk__hyjnt.append(lgjwm__irkse)
        aqda__cor.body = jtk__hyjnt
    ljcq__zrt = ['v{}'.format(tpup__alzyi) for tpup__alzyi in range(
        bndbm__etrdm)]
    sabb__uexob = ['in{}'.format(tpup__alzyi) for tpup__alzyi in range(
        xkrd__sehv)]
    kya__amw = 'def agg_update({}):\n'.format(', '.join(ljcq__zrt +
        sabb__uexob))
    kya__amw += '    __update_redvars()\n'
    kya__amw += '    return {}'.format(', '.join(['v{}'.format(tpup__alzyi) for
        tpup__alzyi in range(bndbm__etrdm)]))
    htd__ixrh = {}
    exec(kya__amw, {}, htd__ixrh)
    ydoga__dvxdr = htd__ixrh['agg_update']
    arg_typs = tuple(var_types + [in_col_typ.dtype] * xkrd__sehv)
    f_ir = compile_to_numba_ir(ydoga__dvxdr, {'__update_redvars':
        __update_redvars}, typingctx=typingctx, targetctx=targetctx,
        arg_typs=arg_typs, typemap=pm.typemap, calltypes=pm.calltypes)
    f_ir._definitions = build_definitions(f_ir.blocks)
    fgem__rkxru = f_ir.blocks.popitem()[1].body
    uby__wtjxg = pm.typemap[fgem__rkxru[-1].value.name]
    qnqyx__gln = wrap_parfor_blocks(parfor)
    rejqu__ttfd = find_topo_order(qnqyx__gln)
    rejqu__ttfd = rejqu__ttfd[1:]
    unwrap_parfor_blocks(parfor)
    f_ir.blocks = parfor.loop_body
    zkxp__zmrw = f_ir.blocks[rejqu__ttfd[0]]
    fgcl__mmyv = f_ir.blocks[rejqu__ttfd[-1]]
    oycr__gto = fgem__rkxru[:bndbm__etrdm + xkrd__sehv]
    if bndbm__etrdm > 1:
        kgc__mgjag = fgem__rkxru[-3:]
        assert is_assign(kgc__mgjag[0]) and isinstance(kgc__mgjag[0].value,
            ir.Expr) and kgc__mgjag[0].value.op == 'build_tuple'
    else:
        kgc__mgjag = fgem__rkxru[-2:]
    for tpup__alzyi in range(bndbm__etrdm):
        wrlin__vijtb = fgem__rkxru[tpup__alzyi].target
        lxg__ewg = ir.Assign(wrlin__vijtb, pudbb__sfwdn[tpup__alzyi],
            wrlin__vijtb.loc)
        oycr__gto.append(lxg__ewg)
    for tpup__alzyi in range(bndbm__etrdm, bndbm__etrdm + xkrd__sehv):
        wrlin__vijtb = fgem__rkxru[tpup__alzyi].target
        lxg__ewg = ir.Assign(wrlin__vijtb, zippj__bzooo[tpup__alzyi -
            bndbm__etrdm], wrlin__vijtb.loc)
        oycr__gto.append(lxg__ewg)
    zkxp__zmrw.body = oycr__gto + zkxp__zmrw.body
    sgasw__yyd = []
    for tpup__alzyi in range(bndbm__etrdm):
        wrlin__vijtb = fgem__rkxru[tpup__alzyi].target
        lxg__ewg = ir.Assign(pudbb__sfwdn[tpup__alzyi], wrlin__vijtb,
            wrlin__vijtb.loc)
        sgasw__yyd.append(lxg__ewg)
    fgcl__mmyv.body += sgasw__yyd + kgc__mgjag
    ebumg__fby = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        uby__wtjxg, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    fmin__qauyy = numba.core.target_extension.dispatcher_registry[cpu_target](
        ydoga__dvxdr)
    fmin__qauyy.add_overload(ebumg__fby)
    return fmin__qauyy


def _rm_arg_agg_block(block, typemap):
    gfwe__rpol = []
    arr_var = None
    for tpup__alzyi, lgjwm__irkse in enumerate(block.body):
        if is_assign(lgjwm__irkse) and isinstance(lgjwm__irkse.value, ir.Arg):
            arr_var = lgjwm__irkse.target
            qni__pja = typemap[arr_var.name]
            if not isinstance(qni__pja, types.ArrayCompatible):
                gfwe__rpol += block.body[tpup__alzyi + 1:]
                break
            cifhm__blxua = block.body[tpup__alzyi + 1]
            assert is_assign(cifhm__blxua) and isinstance(cifhm__blxua.
                value, ir.Expr
                ) and cifhm__blxua.value.op == 'getattr' and cifhm__blxua.value.attr == 'shape' and cifhm__blxua.value.value.name == arr_var.name
            coy__zqc = cifhm__blxua.target
            fycr__yxvdj = block.body[tpup__alzyi + 2]
            assert is_assign(fycr__yxvdj) and isinstance(fycr__yxvdj.value,
                ir.Expr
                ) and fycr__yxvdj.value.op == 'static_getitem' and fycr__yxvdj.value.value.name == coy__zqc.name
            gfwe__rpol += block.body[tpup__alzyi + 3:]
            break
        gfwe__rpol.append(lgjwm__irkse)
    return gfwe__rpol, arr_var


def get_parfor_reductions(parfor, parfor_params, calltypes, reduce_varnames
    =None, param_uses=None, var_to_param=None):
    if reduce_varnames is None:
        reduce_varnames = []
    if param_uses is None:
        param_uses = defaultdict(list)
    if var_to_param is None:
        var_to_param = {}
    qnqyx__gln = wrap_parfor_blocks(parfor)
    rejqu__ttfd = find_topo_order(qnqyx__gln)
    rejqu__ttfd = rejqu__ttfd[1:]
    unwrap_parfor_blocks(parfor)
    for ogbp__cuhr in reversed(rejqu__ttfd):
        for lgjwm__irkse in reversed(parfor.loop_body[ogbp__cuhr].body):
            if isinstance(lgjwm__irkse, ir.Assign) and (lgjwm__irkse.target
                .name in parfor_params or lgjwm__irkse.target.name in
                var_to_param):
                mkb__nfn = lgjwm__irkse.target.name
                rhs = lgjwm__irkse.value
                ghfgs__fizrv = (mkb__nfn if mkb__nfn in parfor_params else
                    var_to_param[mkb__nfn])
                ivzm__tobn = []
                if isinstance(rhs, ir.Var):
                    ivzm__tobn = [rhs.name]
                elif isinstance(rhs, ir.Expr):
                    ivzm__tobn = [pnr__vndwl.name for pnr__vndwl in
                        lgjwm__irkse.value.list_vars()]
                param_uses[ghfgs__fizrv].extend(ivzm__tobn)
                for pnr__vndwl in ivzm__tobn:
                    var_to_param[pnr__vndwl] = ghfgs__fizrv
            if isinstance(lgjwm__irkse, Parfor):
                get_parfor_reductions(lgjwm__irkse, parfor_params,
                    calltypes, reduce_varnames, param_uses, var_to_param)
    for gbd__gov, ivzm__tobn in param_uses.items():
        if gbd__gov in ivzm__tobn and gbd__gov not in reduce_varnames:
            reduce_varnames.append(gbd__gov)
    return reduce_varnames, var_to_param


@numba.extending.register_jitable
def dummy_agg_count(A):
    return len(A)
