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
            rcp__srxm = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer()])
            orua__yikb = cgutils.get_or_insert_function(builder.module,
                rcp__srxm, sym._literal_value)
            builder.call(orua__yikb, [context.get_constant_null(sig.args[0])])
        elif sig == types.none(types.int64, types.voidptr, types.voidptr):
            rcp__srxm = lir.FunctionType(lir.VoidType(), [lir.IntType(64),
                lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
            orua__yikb = cgutils.get_or_insert_function(builder.module,
                rcp__srxm, sym._literal_value)
            builder.call(orua__yikb, [context.get_constant(types.int64, 0),
                context.get_constant_null(sig.args[1]), context.
                get_constant_null(sig.args[2])])
        else:
            rcp__srxm = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64).
                as_pointer()])
            orua__yikb = cgutils.get_or_insert_function(builder.module,
                rcp__srxm, sym._literal_value)
            builder.call(orua__yikb, [context.get_constant_null(sig.args[0]
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
        rhz__eem = True
        qfkc__tki = 1
        hnq__xtb = -1
        if isinstance(rhs, ir.Expr):
            for badb__hhzxw in rhs.kws:
                if func_name in list_cumulative:
                    if badb__hhzxw[0] == 'skipna':
                        rhz__eem = guard(find_const, func_ir, badb__hhzxw[1])
                        if not isinstance(rhz__eem, bool):
                            raise BodoError(
                                'For {} argument of skipna should be a boolean'
                                .format(func_name))
                if func_name == 'nunique':
                    if badb__hhzxw[0] == 'dropna':
                        rhz__eem = guard(find_const, func_ir, badb__hhzxw[1])
                        if not isinstance(rhz__eem, bool):
                            raise BodoError(
                                'argument of dropna to nunique should be a boolean'
                                )
        if func_name == 'shift' and (len(rhs.args) > 0 or len(rhs.kws) > 0):
            qfkc__tki = get_call_expr_arg('shift', rhs.args, dict(rhs.kws),
                0, 'periods', qfkc__tki)
            qfkc__tki = guard(find_const, func_ir, qfkc__tki)
        if func_name == 'head':
            hnq__xtb = get_call_expr_arg('head', rhs.args, dict(rhs.kws), 0,
                'n', 5)
            if not isinstance(hnq__xtb, int):
                hnq__xtb = guard(find_const, func_ir, hnq__xtb)
            if hnq__xtb < 0:
                raise BodoError(
                    f'groupby.{func_name} does not work with negative values.')
        func.skipdropna = rhz__eem
        func.periods = qfkc__tki
        func.head_n = hnq__xtb
        if func_name == 'transform':
            kws = dict(rhs.kws)
            cynk__rgl = get_call_expr_arg(func_name, rhs.args, kws, 0,
                'func', '')
            lpcyi__duig = typemap[cynk__rgl.name]
            iofy__jzhtf = None
            if isinstance(lpcyi__duig, str):
                iofy__jzhtf = lpcyi__duig
            elif is_overload_constant_str(lpcyi__duig):
                iofy__jzhtf = get_overload_const_str(lpcyi__duig)
            elif bodo.utils.typing.is_builtin_function(lpcyi__duig):
                iofy__jzhtf = bodo.utils.typing.get_builtin_function_name(
                    lpcyi__duig)
            if iofy__jzhtf not in bodo.ir.aggregate.supported_transform_funcs[:
                ]:
                raise BodoError(f'unsupported transform function {iofy__jzhtf}'
                    )
            func.transform_func = supported_agg_funcs.index(iofy__jzhtf)
        else:
            func.transform_func = supported_agg_funcs.index('no_op')
        return func
    assert func_name in ['agg', 'aggregate']
    assert typemap is not None
    kws = dict(rhs.kws)
    cynk__rgl = get_call_expr_arg(func_name, rhs.args, kws, 0, 'func', '')
    if cynk__rgl == '':
        lpcyi__duig = types.none
    else:
        lpcyi__duig = typemap[cynk__rgl.name]
    if is_overload_constant_dict(lpcyi__duig):
        rbh__oee = get_overload_constant_dict(lpcyi__duig)
        ntdv__yyik = [get_agg_func_udf(func_ir, f_val, rhs, series_type,
            typemap) for f_val in rbh__oee.values()]
        return ntdv__yyik
    if lpcyi__duig == types.none:
        return [get_agg_func_udf(func_ir, get_literal_value(typemap[f_val.
            name])[1], rhs, series_type, typemap) for f_val in kws.values()]
    if isinstance(lpcyi__duig, types.BaseTuple):
        ntdv__yyik = []
        pqwn__nqa = 0
        for t in lpcyi__duig.types:
            if is_overload_constant_str(t):
                func_name = get_overload_const_str(t)
                ntdv__yyik.append(get_agg_func(func_ir, func_name, rhs,
                    series_type, typemap))
            else:
                assert typemap is not None, 'typemap is required for agg UDF handling'
                func = _get_const_agg_func(t, func_ir)
                func.ftype = 'udf'
                func.fname = _get_udf_name(func)
                if func.fname == '<lambda>':
                    func.fname = '<lambda_' + str(pqwn__nqa) + '>'
                    pqwn__nqa += 1
                ntdv__yyik.append(func)
        return [ntdv__yyik]
    if is_overload_constant_str(lpcyi__duig):
        func_name = get_overload_const_str(lpcyi__duig)
        return get_agg_func(func_ir, func_name, rhs, series_type, typemap)
    if bodo.utils.typing.is_builtin_function(lpcyi__duig):
        func_name = bodo.utils.typing.get_builtin_function_name(lpcyi__duig)
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
        pqwn__nqa = 0
        odax__rgkkf = []
        for axgis__hqs in f_val:
            func = get_agg_func_udf(func_ir, axgis__hqs, rhs, series_type,
                typemap)
            if func.fname == '<lambda>' and len(f_val) > 1:
                func.fname = f'<lambda_{pqwn__nqa}>'
                pqwn__nqa += 1
            odax__rgkkf.append(func)
        return odax__rgkkf
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
    iofy__jzhtf = code.co_name
    return iofy__jzhtf


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
            udu__frkjx = types.DType(args[0])
            return signature(udu__frkjx, *args)


@numba.njit(no_cpython_wrapper=True)
def _var_combine(ssqdm_a, mean_a, nobs_a, ssqdm_b, mean_b, nobs_b):
    wharb__hya = nobs_a + nobs_b
    kdc__njaju = (nobs_a * mean_a + nobs_b * mean_b) / wharb__hya
    gftf__wnofx = mean_b - mean_a
    emxu__yziny = (ssqdm_a + ssqdm_b + gftf__wnofx * gftf__wnofx * nobs_a *
        nobs_b / wharb__hya)
    return emxu__yziny, kdc__njaju, wharb__hya


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
        qptmm__vecan = ''
        for yrzsf__fqrb, ywzqp__slab in self.df_out_vars.items():
            qptmm__vecan += "'{}':{}, ".format(yrzsf__fqrb, ywzqp__slab.name)
        rgv__jegm = '{}{{{}}}'.format(self.df_out, qptmm__vecan)
        kwm__pjwl = ''
        for yrzsf__fqrb, ywzqp__slab in self.df_in_vars.items():
            kwm__pjwl += "'{}':{}, ".format(yrzsf__fqrb, ywzqp__slab.name)
        hak__qskr = '{}{{{}}}'.format(self.df_in, kwm__pjwl)
        gxkhe__qyga = 'pivot {}:{}'.format(self.pivot_arr.name, self.
            pivot_values) if self.pivot_arr is not None else ''
        key_names = ','.join(self.key_names)
        ixm__udaw = ','.join([ywzqp__slab.name for ywzqp__slab in self.
            key_arrs])
        return 'aggregate: {} = {} [key: {}:{}] {}'.format(rgv__jegm,
            hak__qskr, key_names, ixm__udaw, gxkhe__qyga)

    def remove_out_col(self, out_col_name):
        self.df_out_vars.pop(out_col_name)
        znej__zli, aldiq__kcir = self.gb_info_out.pop(out_col_name)
        if znej__zli is None and not self.is_crosstab:
            return
        tlkt__uwvy = self.gb_info_in[znej__zli]
        if self.pivot_arr is not None:
            self.pivot_values.remove(out_col_name)
            for ahn__uwr, (func, qptmm__vecan) in enumerate(tlkt__uwvy):
                try:
                    qptmm__vecan.remove(out_col_name)
                    if len(qptmm__vecan) == 0:
                        tlkt__uwvy.pop(ahn__uwr)
                        break
                except ValueError as hog__ajvr:
                    continue
        else:
            for ahn__uwr, (func, sibp__xgwwx) in enumerate(tlkt__uwvy):
                if sibp__xgwwx == out_col_name:
                    tlkt__uwvy.pop(ahn__uwr)
                    break
        if len(tlkt__uwvy) == 0:
            self.gb_info_in.pop(znej__zli)
            self.df_in_vars.pop(znej__zli)


def aggregate_usedefs(aggregate_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({ywzqp__slab.name for ywzqp__slab in aggregate_node.
        key_arrs})
    use_set.update({ywzqp__slab.name for ywzqp__slab in aggregate_node.
        df_in_vars.values()})
    if aggregate_node.pivot_arr is not None:
        use_set.add(aggregate_node.pivot_arr.name)
    def_set.update({ywzqp__slab.name for ywzqp__slab in aggregate_node.
        df_out_vars.values()})
    if aggregate_node.out_key_vars is not None:
        def_set.update({ywzqp__slab.name for ywzqp__slab in aggregate_node.
            out_key_vars})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Aggregate] = aggregate_usedefs


def remove_dead_aggregate(aggregate_node, lives_no_aliases, lives,
    arg_aliases, alias_map, func_ir, typemap):
    ivbhf__rcxaj = [mhfb__yua for mhfb__yua, txbqf__rwxj in aggregate_node.
        df_out_vars.items() if txbqf__rwxj.name not in lives]
    for yoj__jutt in ivbhf__rcxaj:
        aggregate_node.remove_out_col(yoj__jutt)
    out_key_vars = aggregate_node.out_key_vars
    if out_key_vars is not None and all(ywzqp__slab.name not in lives for
        ywzqp__slab in out_key_vars):
        aggregate_node.out_key_vars = None
    if len(aggregate_node.df_out_vars
        ) == 0 and aggregate_node.out_key_vars is None:
        return None
    return aggregate_node


ir_utils.remove_dead_extensions[Aggregate] = remove_dead_aggregate


def get_copies_aggregate(aggregate_node, typemap):
    fjcb__qvb = set(ywzqp__slab.name for ywzqp__slab in aggregate_node.
        df_out_vars.values())
    if aggregate_node.out_key_vars is not None:
        fjcb__qvb.update({ywzqp__slab.name for ywzqp__slab in
            aggregate_node.out_key_vars})
    return set(), fjcb__qvb


ir_utils.copy_propagate_extensions[Aggregate] = get_copies_aggregate


def apply_copies_aggregate(aggregate_node, var_dict, name_var_table,
    typemap, calltypes, save_copies):
    for ahn__uwr in range(len(aggregate_node.key_arrs)):
        aggregate_node.key_arrs[ahn__uwr] = replace_vars_inner(aggregate_node
            .key_arrs[ahn__uwr], var_dict)
    for mhfb__yua in list(aggregate_node.df_in_vars.keys()):
        aggregate_node.df_in_vars[mhfb__yua] = replace_vars_inner(
            aggregate_node.df_in_vars[mhfb__yua], var_dict)
    for mhfb__yua in list(aggregate_node.df_out_vars.keys()):
        aggregate_node.df_out_vars[mhfb__yua] = replace_vars_inner(
            aggregate_node.df_out_vars[mhfb__yua], var_dict)
    if aggregate_node.out_key_vars is not None:
        for ahn__uwr in range(len(aggregate_node.out_key_vars)):
            aggregate_node.out_key_vars[ahn__uwr] = replace_vars_inner(
                aggregate_node.out_key_vars[ahn__uwr], var_dict)
    if aggregate_node.pivot_arr is not None:
        aggregate_node.pivot_arr = replace_vars_inner(aggregate_node.
            pivot_arr, var_dict)


ir_utils.apply_copy_propagate_extensions[Aggregate] = apply_copies_aggregate


def visit_vars_aggregate(aggregate_node, callback, cbdata):
    if debug_prints():
        print('visiting aggregate vars for:', aggregate_node)
        print('cbdata: ', sorted(cbdata.items()))
    for ahn__uwr in range(len(aggregate_node.key_arrs)):
        aggregate_node.key_arrs[ahn__uwr] = visit_vars_inner(aggregate_node
            .key_arrs[ahn__uwr], callback, cbdata)
    for mhfb__yua in list(aggregate_node.df_in_vars.keys()):
        aggregate_node.df_in_vars[mhfb__yua] = visit_vars_inner(aggregate_node
            .df_in_vars[mhfb__yua], callback, cbdata)
    for mhfb__yua in list(aggregate_node.df_out_vars.keys()):
        aggregate_node.df_out_vars[mhfb__yua] = visit_vars_inner(aggregate_node
            .df_out_vars[mhfb__yua], callback, cbdata)
    if aggregate_node.out_key_vars is not None:
        for ahn__uwr in range(len(aggregate_node.out_key_vars)):
            aggregate_node.out_key_vars[ahn__uwr] = visit_vars_inner(
                aggregate_node.out_key_vars[ahn__uwr], callback, cbdata)
    if aggregate_node.pivot_arr is not None:
        aggregate_node.pivot_arr = visit_vars_inner(aggregate_node.
            pivot_arr, callback, cbdata)


ir_utils.visit_vars_extensions[Aggregate] = visit_vars_aggregate


def aggregate_array_analysis(aggregate_node, equiv_set, typemap, array_analysis
    ):
    assert len(aggregate_node.df_out_vars
        ) > 0 or aggregate_node.out_key_vars is not None or aggregate_node.is_crosstab, 'empty aggregate in array analysis'
    djkf__gmcel = []
    for knifi__pac in aggregate_node.key_arrs:
        sbpt__vlpsu = equiv_set.get_shape(knifi__pac)
        if sbpt__vlpsu:
            djkf__gmcel.append(sbpt__vlpsu[0])
    if aggregate_node.pivot_arr is not None:
        sbpt__vlpsu = equiv_set.get_shape(aggregate_node.pivot_arr)
        if sbpt__vlpsu:
            djkf__gmcel.append(sbpt__vlpsu[0])
    for txbqf__rwxj in aggregate_node.df_in_vars.values():
        sbpt__vlpsu = equiv_set.get_shape(txbqf__rwxj)
        if sbpt__vlpsu:
            djkf__gmcel.append(sbpt__vlpsu[0])
    if len(djkf__gmcel) > 1:
        equiv_set.insert_equiv(*djkf__gmcel)
    uhw__jpwkt = []
    djkf__gmcel = []
    zsxr__ilvcc = list(aggregate_node.df_out_vars.values())
    if aggregate_node.out_key_vars is not None:
        zsxr__ilvcc.extend(aggregate_node.out_key_vars)
    for txbqf__rwxj in zsxr__ilvcc:
        kdg__kem = typemap[txbqf__rwxj.name]
        oqse__jau = array_analysis._gen_shape_call(equiv_set, txbqf__rwxj,
            kdg__kem.ndim, None, uhw__jpwkt)
        equiv_set.insert_equiv(txbqf__rwxj, oqse__jau)
        djkf__gmcel.append(oqse__jau[0])
        equiv_set.define(txbqf__rwxj, set())
    if len(djkf__gmcel) > 1:
        equiv_set.insert_equiv(*djkf__gmcel)
    return [], uhw__jpwkt


numba.parfors.array_analysis.array_analysis_extensions[Aggregate
    ] = aggregate_array_analysis


def aggregate_distributed_analysis(aggregate_node, array_dists):
    krzr__allbx = Distribution.OneD
    for txbqf__rwxj in aggregate_node.df_in_vars.values():
        krzr__allbx = Distribution(min(krzr__allbx.value, array_dists[
            txbqf__rwxj.name].value))
    for knifi__pac in aggregate_node.key_arrs:
        krzr__allbx = Distribution(min(krzr__allbx.value, array_dists[
            knifi__pac.name].value))
    if aggregate_node.pivot_arr is not None:
        krzr__allbx = Distribution(min(krzr__allbx.value, array_dists[
            aggregate_node.pivot_arr.name].value))
        array_dists[aggregate_node.pivot_arr.name] = krzr__allbx
    for txbqf__rwxj in aggregate_node.df_in_vars.values():
        array_dists[txbqf__rwxj.name] = krzr__allbx
    for knifi__pac in aggregate_node.key_arrs:
        array_dists[knifi__pac.name] = krzr__allbx
    llzcd__njalc = Distribution.OneD_Var
    for txbqf__rwxj in aggregate_node.df_out_vars.values():
        if txbqf__rwxj.name in array_dists:
            llzcd__njalc = Distribution(min(llzcd__njalc.value, array_dists
                [txbqf__rwxj.name].value))
    if aggregate_node.out_key_vars is not None:
        for txbqf__rwxj in aggregate_node.out_key_vars:
            if txbqf__rwxj.name in array_dists:
                llzcd__njalc = Distribution(min(llzcd__njalc.value,
                    array_dists[txbqf__rwxj.name].value))
    llzcd__njalc = Distribution(min(llzcd__njalc.value, krzr__allbx.value))
    for txbqf__rwxj in aggregate_node.df_out_vars.values():
        array_dists[txbqf__rwxj.name] = llzcd__njalc
    if aggregate_node.out_key_vars is not None:
        for ovn__qgef in aggregate_node.out_key_vars:
            array_dists[ovn__qgef.name] = llzcd__njalc
    if llzcd__njalc != Distribution.OneD_Var:
        for knifi__pac in aggregate_node.key_arrs:
            array_dists[knifi__pac.name] = llzcd__njalc
        if aggregate_node.pivot_arr is not None:
            array_dists[aggregate_node.pivot_arr.name] = llzcd__njalc
        for txbqf__rwxj in aggregate_node.df_in_vars.values():
            array_dists[txbqf__rwxj.name] = llzcd__njalc


distributed_analysis.distributed_analysis_extensions[Aggregate
    ] = aggregate_distributed_analysis


def build_agg_definitions(agg_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for txbqf__rwxj in agg_node.df_out_vars.values():
        definitions[txbqf__rwxj.name].append(agg_node)
    if agg_node.out_key_vars is not None:
        for ovn__qgef in agg_node.out_key_vars:
            definitions[ovn__qgef.name].append(agg_node)
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
        for ywzqp__slab in (list(agg_node.df_in_vars.values()) + list(
            agg_node.df_out_vars.values()) + agg_node.key_arrs):
            if array_dists[ywzqp__slab.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                ywzqp__slab.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    lpe__wxbu = tuple(typemap[ywzqp__slab.name] for ywzqp__slab in agg_node
        .key_arrs)
    grfj__syiw = [ywzqp__slab for ygte__fct, ywzqp__slab in agg_node.
        df_in_vars.items()]
    kwlr__oukmo = [ywzqp__slab for ygte__fct, ywzqp__slab in agg_node.
        df_out_vars.items()]
    in_col_typs = []
    ntdv__yyik = []
    if agg_node.pivot_arr is not None:
        for znej__zli, tlkt__uwvy in agg_node.gb_info_in.items():
            for func, aldiq__kcir in tlkt__uwvy:
                if znej__zli is not None:
                    in_col_typs.append(typemap[agg_node.df_in_vars[
                        znej__zli].name])
                ntdv__yyik.append(func)
    else:
        for znej__zli, func in agg_node.gb_info_out.values():
            if znej__zli is not None:
                in_col_typs.append(typemap[agg_node.df_in_vars[znej__zli].name]
                    )
            ntdv__yyik.append(func)
    out_col_typs = tuple(typemap[ywzqp__slab.name] for ywzqp__slab in
        kwlr__oukmo)
    pivot_typ = types.none if agg_node.pivot_arr is None else typemap[agg_node
        .pivot_arr.name]
    arg_typs = tuple(lpe__wxbu + tuple(typemap[ywzqp__slab.name] for
        ywzqp__slab in grfj__syiw) + (pivot_typ,))
    in_col_typs = [to_str_arr_if_dict_array(t) for t in in_col_typs]
    anav__qswph = {'bodo': bodo, 'np': np, 'dt64_dtype': np.dtype(
        'datetime64[ns]'), 'td64_dtype': np.dtype('timedelta64[ns]')}
    for ahn__uwr, in_col_typ in enumerate(in_col_typs):
        if isinstance(in_col_typ, bodo.CategoricalArrayType):
            anav__qswph.update({f'in_cat_dtype_{ahn__uwr}': in_col_typ})
    for ahn__uwr, vfu__ewzti in enumerate(out_col_typs):
        if isinstance(vfu__ewzti, bodo.CategoricalArrayType):
            anav__qswph.update({f'out_cat_dtype_{ahn__uwr}': vfu__ewzti})
    udf_func_struct = get_udf_func_struct(ntdv__yyik, agg_node.
        input_has_index, in_col_typs, out_col_typs, typingctx, targetctx,
        pivot_typ, agg_node.pivot_values, agg_node.is_crosstab)
    ffb__jbmq = gen_top_level_agg_func(agg_node, in_col_typs, out_col_typs,
        parallel, udf_func_struct)
    anav__qswph.update({'pd': pd, 'pre_alloc_string_array':
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
            anav__qswph.update({'__update_redvars': udf_func_struct.
                update_all_func, '__init_func': udf_func_struct.init_func,
                '__combine_redvars': udf_func_struct.combine_all_func,
                '__eval_res': udf_func_struct.eval_all_func,
                'cpp_cb_update': udf_func_struct.regular_udf_cfuncs[0],
                'cpp_cb_combine': udf_func_struct.regular_udf_cfuncs[1],
                'cpp_cb_eval': udf_func_struct.regular_udf_cfuncs[2]})
        if udf_func_struct.general_udfs:
            anav__qswph.update({'cpp_cb_general': udf_func_struct.
                general_udf_cfunc})
    pqtz__nps = compile_to_numba_ir(ffb__jbmq, anav__qswph, typingctx=
        typingctx, targetctx=targetctx, arg_typs=arg_typs, typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    uamja__jlqei = []
    if agg_node.pivot_arr is None:
        qmm__vyp = agg_node.key_arrs[0].scope
        loc = agg_node.loc
        ttarf__cee = ir.Var(qmm__vyp, mk_unique_var('dummy_none'), loc)
        typemap[ttarf__cee.name] = types.none
        uamja__jlqei.append(ir.Assign(ir.Const(None, loc), ttarf__cee, loc))
        grfj__syiw.append(ttarf__cee)
    else:
        grfj__syiw.append(agg_node.pivot_arr)
    replace_arg_nodes(pqtz__nps, agg_node.key_arrs + grfj__syiw)
    wmsd__sxd = pqtz__nps.body[-3]
    assert is_assign(wmsd__sxd) and isinstance(wmsd__sxd.value, ir.Expr
        ) and wmsd__sxd.value.op == 'build_tuple'
    uamja__jlqei += pqtz__nps.body[:-3]
    zsxr__ilvcc = list(agg_node.df_out_vars.values())
    if agg_node.out_key_vars is not None:
        zsxr__ilvcc += agg_node.out_key_vars
    for ahn__uwr, tan__vui in enumerate(zsxr__ilvcc):
        klr__vht = wmsd__sxd.value.items[ahn__uwr]
        uamja__jlqei.append(ir.Assign(klr__vht, tan__vui, tan__vui.loc))
    return uamja__jlqei


distributed_pass.distributed_run_extensions[Aggregate] = agg_distributed_run


def get_numba_set(dtype):
    pass


@infer_global(get_numba_set)
class GetNumbaSetTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 1
        asl__vhm = args[0]
        dtype = types.Tuple([t.dtype for t in asl__vhm.types]) if isinstance(
            asl__vhm, types.BaseTuple) else asl__vhm.dtype
        if isinstance(asl__vhm, types.BaseTuple) and len(asl__vhm.types) == 1:
            dtype = asl__vhm.types[0].dtype
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
        gzjpl__owu = args[0]
        if gzjpl__owu == types.none:
            return signature(types.boolean, *args)


@lower_builtin(bool, types.none)
def lower_column_mean_impl(context, builder, sig, args):
    jmxq__xhvv = context.compile_internal(builder, lambda a: False, sig, args)
    return jmxq__xhvv


def _gen_dummy_alloc(t, colnum=0, is_input=False):
    if isinstance(t, IntegerArrayType):
        zbg__llww = IntDtype(t.dtype).name
        assert zbg__llww.endswith('Dtype()')
        zbg__llww = zbg__llww[:-7]
        return (
            f"bodo.hiframes.pd_series_ext.get_series_data(pd.Series([1], dtype='{zbg__llww}'))"
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
        eiiq__cmy = 'in' if is_input else 'out'
        return (
            f'bodo.utils.utils.alloc_type(1, {eiiq__cmy}_cat_dtype_{colnum})')
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
    mbtn__nxcrd = udf_func_struct.var_typs
    mlyw__zsprx = len(mbtn__nxcrd)
    ehulv__jqu = (
        'def bodo_gb_udf_update_local{}(in_table, out_table, row_to_group):\n'
        .format(label_suffix))
    ehulv__jqu += '    if is_null_pointer(in_table):\n'
    ehulv__jqu += '        return\n'
    ehulv__jqu += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in mbtn__nxcrd]), 
        ',' if len(mbtn__nxcrd) == 1 else '')
    aihh__mqvl = n_keys
    znv__chckl = []
    redvar_offsets = []
    tfffv__pay = []
    if do_combine:
        for ahn__uwr, axgis__hqs in enumerate(allfuncs):
            if axgis__hqs.ftype != 'udf':
                aihh__mqvl += axgis__hqs.ncols_pre_shuffle
            else:
                redvar_offsets += list(range(aihh__mqvl, aihh__mqvl +
                    axgis__hqs.n_redvars))
                aihh__mqvl += axgis__hqs.n_redvars
                tfffv__pay.append(data_in_typs_[func_idx_to_in_col[ahn__uwr]])
                znv__chckl.append(func_idx_to_in_col[ahn__uwr] + n_keys)
    else:
        for ahn__uwr, axgis__hqs in enumerate(allfuncs):
            if axgis__hqs.ftype != 'udf':
                aihh__mqvl += axgis__hqs.ncols_post_shuffle
            else:
                redvar_offsets += list(range(aihh__mqvl + 1, aihh__mqvl + 1 +
                    axgis__hqs.n_redvars))
                aihh__mqvl += axgis__hqs.n_redvars + 1
                tfffv__pay.append(data_in_typs_[func_idx_to_in_col[ahn__uwr]])
                znv__chckl.append(func_idx_to_in_col[ahn__uwr] + n_keys)
    assert len(redvar_offsets) == mlyw__zsprx
    ewm__bznj = len(tfffv__pay)
    fct__wqlb = []
    for ahn__uwr, t in enumerate(tfffv__pay):
        fct__wqlb.append(_gen_dummy_alloc(t, ahn__uwr, True))
    ehulv__jqu += '    data_in_dummy = ({}{})\n'.format(','.join(fct__wqlb),
        ',' if len(tfffv__pay) == 1 else '')
    ehulv__jqu += """
    # initialize redvar cols
"""
    ehulv__jqu += '    init_vals = __init_func()\n'
    for ahn__uwr in range(mlyw__zsprx):
        ehulv__jqu += (
            """    redvar_arr_{} = info_to_array(info_from_table(out_table, {}), data_redvar_dummy[{}])
"""
            .format(ahn__uwr, redvar_offsets[ahn__uwr], ahn__uwr))
        ehulv__jqu += '    incref(redvar_arr_{})\n'.format(ahn__uwr)
        ehulv__jqu += '    redvar_arr_{}.fill(init_vals[{}])\n'.format(ahn__uwr
            , ahn__uwr)
    ehulv__jqu += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'
        .format(ahn__uwr) for ahn__uwr in range(mlyw__zsprx)]), ',' if 
        mlyw__zsprx == 1 else '')
    ehulv__jqu += '\n'
    for ahn__uwr in range(ewm__bznj):
        ehulv__jqu += (
            """    data_in_{} = info_to_array(info_from_table(in_table, {}), data_in_dummy[{}])
"""
            .format(ahn__uwr, znv__chckl[ahn__uwr], ahn__uwr))
        ehulv__jqu += '    incref(data_in_{})\n'.format(ahn__uwr)
    ehulv__jqu += '    data_in = ({}{})\n'.format(','.join(['data_in_{}'.
        format(ahn__uwr) for ahn__uwr in range(ewm__bznj)]), ',' if 
        ewm__bznj == 1 else '')
    ehulv__jqu += '\n'
    ehulv__jqu += '    for i in range(len(data_in_0)):\n'
    ehulv__jqu += '        w_ind = row_to_group[i]\n'
    ehulv__jqu += '        if w_ind != -1:\n'
    ehulv__jqu += (
        '            __update_redvars(redvars, data_in, w_ind, i, pivot_arr=None)\n'
        )
    onbqk__vimxo = {}
    exec(ehulv__jqu, {'bodo': bodo, 'np': np, 'pd': pd, 'info_to_array':
        info_to_array, 'info_from_table': info_from_table, 'incref': incref,
        'pre_alloc_string_array': pre_alloc_string_array, '__init_func':
        udf_func_struct.init_func, '__update_redvars': udf_func_struct.
        update_all_func, 'is_null_pointer': is_null_pointer, 'dt64_dtype':
        np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, onbqk__vimxo)
    return onbqk__vimxo['bodo_gb_udf_update_local{}'.format(label_suffix)]


def gen_combine_cb(udf_func_struct, allfuncs, n_keys, out_data_typs,
    label_suffix):
    mbtn__nxcrd = udf_func_struct.var_typs
    mlyw__zsprx = len(mbtn__nxcrd)
    ehulv__jqu = (
        'def bodo_gb_udf_combine{}(in_table, out_table, row_to_group):\n'.
        format(label_suffix))
    ehulv__jqu += '    if is_null_pointer(in_table):\n'
    ehulv__jqu += '        return\n'
    ehulv__jqu += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in mbtn__nxcrd]), 
        ',' if len(mbtn__nxcrd) == 1 else '')
    nue__umytx = n_keys
    qtxph__dhjj = n_keys
    gwlc__rjj = []
    dvdua__irdg = []
    for axgis__hqs in allfuncs:
        if axgis__hqs.ftype != 'udf':
            nue__umytx += axgis__hqs.ncols_pre_shuffle
            qtxph__dhjj += axgis__hqs.ncols_post_shuffle
        else:
            gwlc__rjj += list(range(nue__umytx, nue__umytx + axgis__hqs.
                n_redvars))
            dvdua__irdg += list(range(qtxph__dhjj + 1, qtxph__dhjj + 1 +
                axgis__hqs.n_redvars))
            nue__umytx += axgis__hqs.n_redvars
            qtxph__dhjj += 1 + axgis__hqs.n_redvars
    assert len(gwlc__rjj) == mlyw__zsprx
    ehulv__jqu += """
    # initialize redvar cols
"""
    ehulv__jqu += '    init_vals = __init_func()\n'
    for ahn__uwr in range(mlyw__zsprx):
        ehulv__jqu += (
            """    redvar_arr_{} = info_to_array(info_from_table(out_table, {}), data_redvar_dummy[{}])
"""
            .format(ahn__uwr, dvdua__irdg[ahn__uwr], ahn__uwr))
        ehulv__jqu += '    incref(redvar_arr_{})\n'.format(ahn__uwr)
        ehulv__jqu += '    redvar_arr_{}.fill(init_vals[{}])\n'.format(ahn__uwr
            , ahn__uwr)
    ehulv__jqu += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'
        .format(ahn__uwr) for ahn__uwr in range(mlyw__zsprx)]), ',' if 
        mlyw__zsprx == 1 else '')
    ehulv__jqu += '\n'
    for ahn__uwr in range(mlyw__zsprx):
        ehulv__jqu += (
            """    recv_redvar_arr_{} = info_to_array(info_from_table(in_table, {}), data_redvar_dummy[{}])
"""
            .format(ahn__uwr, gwlc__rjj[ahn__uwr], ahn__uwr))
        ehulv__jqu += '    incref(recv_redvar_arr_{})\n'.format(ahn__uwr)
    ehulv__jqu += '    recv_redvars = ({}{})\n'.format(','.join([
        'recv_redvar_arr_{}'.format(ahn__uwr) for ahn__uwr in range(
        mlyw__zsprx)]), ',' if mlyw__zsprx == 1 else '')
    ehulv__jqu += '\n'
    if mlyw__zsprx:
        ehulv__jqu += '    for i in range(len(recv_redvar_arr_0)):\n'
        ehulv__jqu += '        w_ind = row_to_group[i]\n'
        ehulv__jqu += """        __combine_redvars(redvars, recv_redvars, w_ind, i, pivot_arr=None)
"""
    onbqk__vimxo = {}
    exec(ehulv__jqu, {'np': np, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref, '__init_func':
        udf_func_struct.init_func, '__combine_redvars': udf_func_struct.
        combine_all_func, 'is_null_pointer': is_null_pointer, 'dt64_dtype':
        np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, onbqk__vimxo)
    return onbqk__vimxo['bodo_gb_udf_combine{}'.format(label_suffix)]


def gen_eval_cb(udf_func_struct, allfuncs, n_keys, out_data_typs_, label_suffix
    ):
    mbtn__nxcrd = udf_func_struct.var_typs
    mlyw__zsprx = len(mbtn__nxcrd)
    aihh__mqvl = n_keys
    redvar_offsets = []
    mwsn__zwqdp = []
    out_data_typs = []
    for ahn__uwr, axgis__hqs in enumerate(allfuncs):
        if axgis__hqs.ftype != 'udf':
            aihh__mqvl += axgis__hqs.ncols_post_shuffle
        else:
            mwsn__zwqdp.append(aihh__mqvl)
            redvar_offsets += list(range(aihh__mqvl + 1, aihh__mqvl + 1 +
                axgis__hqs.n_redvars))
            aihh__mqvl += 1 + axgis__hqs.n_redvars
            out_data_typs.append(out_data_typs_[ahn__uwr])
    assert len(redvar_offsets) == mlyw__zsprx
    ewm__bznj = len(out_data_typs)
    ehulv__jqu = 'def bodo_gb_udf_eval{}(table):\n'.format(label_suffix)
    ehulv__jqu += '    if is_null_pointer(table):\n'
    ehulv__jqu += '        return\n'
    ehulv__jqu += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in mbtn__nxcrd]), 
        ',' if len(mbtn__nxcrd) == 1 else '')
    ehulv__jqu += '    out_data_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t.dtype)) for t in
        out_data_typs]), ',' if len(out_data_typs) == 1 else '')
    for ahn__uwr in range(mlyw__zsprx):
        ehulv__jqu += (
            """    redvar_arr_{} = info_to_array(info_from_table(table, {}), data_redvar_dummy[{}])
"""
            .format(ahn__uwr, redvar_offsets[ahn__uwr], ahn__uwr))
        ehulv__jqu += '    incref(redvar_arr_{})\n'.format(ahn__uwr)
    ehulv__jqu += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'
        .format(ahn__uwr) for ahn__uwr in range(mlyw__zsprx)]), ',' if 
        mlyw__zsprx == 1 else '')
    ehulv__jqu += '\n'
    for ahn__uwr in range(ewm__bznj):
        ehulv__jqu += (
            """    data_out_{} = info_to_array(info_from_table(table, {}), out_data_dummy[{}])
"""
            .format(ahn__uwr, mwsn__zwqdp[ahn__uwr], ahn__uwr))
        ehulv__jqu += '    incref(data_out_{})\n'.format(ahn__uwr)
    ehulv__jqu += '    data_out = ({}{})\n'.format(','.join(['data_out_{}'.
        format(ahn__uwr) for ahn__uwr in range(ewm__bznj)]), ',' if 
        ewm__bznj == 1 else '')
    ehulv__jqu += '\n'
    ehulv__jqu += '    for i in range(len(data_out_0)):\n'
    ehulv__jqu += '        __eval_res(redvars, data_out, i)\n'
    onbqk__vimxo = {}
    exec(ehulv__jqu, {'np': np, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref, '__eval_res':
        udf_func_struct.eval_all_func, 'is_null_pointer': is_null_pointer,
        'dt64_dtype': np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, onbqk__vimxo)
    return onbqk__vimxo['bodo_gb_udf_eval{}'.format(label_suffix)]


def gen_general_udf_cb(udf_func_struct, allfuncs, n_keys, in_col_typs,
    out_col_typs, func_idx_to_in_col, label_suffix):
    aihh__mqvl = n_keys
    gdnm__ensc = []
    for ahn__uwr, axgis__hqs in enumerate(allfuncs):
        if axgis__hqs.ftype == 'gen_udf':
            gdnm__ensc.append(aihh__mqvl)
            aihh__mqvl += 1
        elif axgis__hqs.ftype != 'udf':
            aihh__mqvl += axgis__hqs.ncols_post_shuffle
        else:
            aihh__mqvl += axgis__hqs.n_redvars + 1
    ehulv__jqu = (
        'def bodo_gb_apply_general_udfs{}(num_groups, in_table, out_table):\n'
        .format(label_suffix))
    ehulv__jqu += '    if num_groups == 0:\n'
    ehulv__jqu += '        return\n'
    for ahn__uwr, func in enumerate(udf_func_struct.general_udf_funcs):
        ehulv__jqu += '    # col {}\n'.format(ahn__uwr)
        ehulv__jqu += (
            """    out_col = info_to_array(info_from_table(out_table, {}), out_col_{}_typ)
"""
            .format(gdnm__ensc[ahn__uwr], ahn__uwr))
        ehulv__jqu += '    incref(out_col)\n'
        ehulv__jqu += '    for j in range(num_groups):\n'
        ehulv__jqu += (
            """        in_col = info_to_array(info_from_table(in_table, {}*num_groups + j), in_col_{}_typ)
"""
            .format(ahn__uwr, ahn__uwr))
        ehulv__jqu += '        incref(in_col)\n'
        ehulv__jqu += (
            '        out_col[j] = func_{}(pd.Series(in_col))  # func returns scalar\n'
            .format(ahn__uwr))
    anav__qswph = {'pd': pd, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref}
    lvwmb__xbafy = 0
    for ahn__uwr, func in enumerate(allfuncs):
        if func.ftype != 'gen_udf':
            continue
        func = udf_func_struct.general_udf_funcs[lvwmb__xbafy]
        anav__qswph['func_{}'.format(lvwmb__xbafy)] = func
        anav__qswph['in_col_{}_typ'.format(lvwmb__xbafy)] = in_col_typs[
            func_idx_to_in_col[ahn__uwr]]
        anav__qswph['out_col_{}_typ'.format(lvwmb__xbafy)] = out_col_typs[
            ahn__uwr]
        lvwmb__xbafy += 1
    onbqk__vimxo = {}
    exec(ehulv__jqu, anav__qswph, onbqk__vimxo)
    axgis__hqs = onbqk__vimxo['bodo_gb_apply_general_udfs{}'.format(
        label_suffix)]
    pams__mqs = types.void(types.int64, types.voidptr, types.voidptr)
    return numba.cfunc(pams__mqs, nopython=True)(axgis__hqs)


def gen_top_level_agg_func(agg_node, in_col_typs, out_col_typs, parallel,
    udf_func_struct):
    mzb__apus = agg_node.pivot_arr is not None
    if agg_node.same_index:
        assert agg_node.input_has_index
    if agg_node.pivot_values is None:
        lebm__yzchc = 1
    else:
        lebm__yzchc = len(agg_node.pivot_values)
    vtcn__tnyq = tuple('key_' + sanitize_varname(yrzsf__fqrb) for
        yrzsf__fqrb in agg_node.key_names)
    yejgz__wli = {yrzsf__fqrb: 'in_{}'.format(sanitize_varname(yrzsf__fqrb)
        ) for yrzsf__fqrb in agg_node.gb_info_in.keys() if yrzsf__fqrb is not
        None}
    ngpml__gahn = {yrzsf__fqrb: ('out_' + sanitize_varname(yrzsf__fqrb)) for
        yrzsf__fqrb in agg_node.gb_info_out.keys()}
    n_keys = len(agg_node.key_names)
    drjb__knoa = ', '.join(vtcn__tnyq)
    xcsb__xblia = ', '.join(yejgz__wli.values())
    if xcsb__xblia != '':
        xcsb__xblia = ', ' + xcsb__xblia
    ehulv__jqu = 'def agg_top({}{}{}, pivot_arr):\n'.format(drjb__knoa,
        xcsb__xblia, ', index_arg' if agg_node.input_has_index else '')
    for a in (vtcn__tnyq + tuple(yejgz__wli.values())):
        ehulv__jqu += f'    {a} = decode_if_dict_array({a})\n'
    if mzb__apus:
        ehulv__jqu += f'    pivot_arr = decode_if_dict_array(pivot_arr)\n'
        zwvhy__fdq = []
        for znej__zli, tlkt__uwvy in agg_node.gb_info_in.items():
            if znej__zli is not None:
                for func, aldiq__kcir in tlkt__uwvy:
                    zwvhy__fdq.append(yejgz__wli[znej__zli])
    else:
        zwvhy__fdq = tuple(yejgz__wli[znej__zli] for znej__zli, aldiq__kcir in
            agg_node.gb_info_out.values() if znej__zli is not None)
    roxx__yedjh = vtcn__tnyq + tuple(zwvhy__fdq)
    ehulv__jqu += '    info_list = [{}{}{}]\n'.format(', '.join(
        'array_to_info({})'.format(a) for a in roxx__yedjh), 
        ', array_to_info(index_arg)' if agg_node.input_has_index else '', 
        ', array_to_info(pivot_arr)' if agg_node.is_crosstab else '')
    ehulv__jqu += '    table = arr_info_list_to_table(info_list)\n'
    for ahn__uwr, yrzsf__fqrb in enumerate(agg_node.gb_info_out.keys()):
        mebw__jucz = ngpml__gahn[yrzsf__fqrb] + '_dummy'
        vfu__ewzti = out_col_typs[ahn__uwr]
        znej__zli, func = agg_node.gb_info_out[yrzsf__fqrb]
        if isinstance(func, pytypes.SimpleNamespace) and func.fname in ['min',
            'max', 'shift'] and isinstance(vfu__ewzti, bodo.
            CategoricalArrayType):
            ehulv__jqu += '    {} = {}\n'.format(mebw__jucz, yejgz__wli[
                znej__zli])
        else:
            ehulv__jqu += '    {} = {}\n'.format(mebw__jucz,
                _gen_dummy_alloc(vfu__ewzti, ahn__uwr, False))
    do_combine = parallel
    allfuncs = []
    qqzjl__vcqal = []
    func_idx_to_in_col = []
    nryz__zcgnz = []
    rhz__eem = False
    fqr__pxt = 1
    hnq__xtb = -1
    mnxl__fjl = 0
    rtzl__ressy = 0
    if not mzb__apus:
        ntdv__yyik = [func for aldiq__kcir, func in agg_node.gb_info_out.
            values()]
    else:
        ntdv__yyik = [func for func, aldiq__kcir in tlkt__uwvy for
            tlkt__uwvy in agg_node.gb_info_in.values()]
    for wje__fmgll, func in enumerate(ntdv__yyik):
        qqzjl__vcqal.append(len(allfuncs))
        if func.ftype in {'median', 'nunique'}:
            do_combine = False
        if func.ftype in list_cumulative:
            mnxl__fjl += 1
        if hasattr(func, 'skipdropna'):
            rhz__eem = func.skipdropna
        if func.ftype == 'shift':
            fqr__pxt = func.periods
            do_combine = False
        if func.ftype in {'transform'}:
            rtzl__ressy = func.transform_func
            do_combine = False
        if func.ftype == 'head':
            hnq__xtb = func.head_n
            do_combine = False
        allfuncs.append(func)
        func_idx_to_in_col.append(wje__fmgll)
        if func.ftype == 'udf':
            nryz__zcgnz.append(func.n_redvars)
        elif func.ftype == 'gen_udf':
            nryz__zcgnz.append(0)
            do_combine = False
    qqzjl__vcqal.append(len(allfuncs))
    if agg_node.is_crosstab:
        assert len(agg_node.gb_info_out
            ) == lebm__yzchc, 'invalid number of groupby outputs for pivot'
    else:
        assert len(agg_node.gb_info_out) == len(allfuncs
            ) * lebm__yzchc, 'invalid number of groupby outputs'
    if mnxl__fjl > 0:
        if mnxl__fjl != len(allfuncs):
            raise BodoError(
                f'{agg_node.func_name}(): Cannot mix cumulative operations with other aggregation functions'
                , loc=agg_node.loc)
        do_combine = False
    if udf_func_struct is not None:
        oao__lid = next_label()
        if udf_func_struct.regular_udfs:
            pams__mqs = types.void(types.voidptr, types.voidptr, types.
                CPointer(types.int64))
            jga__zboq = numba.cfunc(pams__mqs, nopython=True)(gen_update_cb
                (udf_func_struct, allfuncs, n_keys, in_col_typs,
                out_col_typs, do_combine, func_idx_to_in_col, oao__lid))
            mzsxl__azhk = numba.cfunc(pams__mqs, nopython=True)(gen_combine_cb
                (udf_func_struct, allfuncs, n_keys, out_col_typs, oao__lid))
            doq__uwxyo = numba.cfunc('void(voidptr)', nopython=True)(
                gen_eval_cb(udf_func_struct, allfuncs, n_keys, out_col_typs,
                oao__lid))
            udf_func_struct.set_regular_cfuncs(jga__zboq, mzsxl__azhk,
                doq__uwxyo)
            for hoes__vveg in udf_func_struct.regular_udf_cfuncs:
                gb_agg_cfunc[hoes__vveg.native_name] = hoes__vveg
                gb_agg_cfunc_addr[hoes__vveg.native_name] = hoes__vveg.address
        if udf_func_struct.general_udfs:
            egf__anf = gen_general_udf_cb(udf_func_struct, allfuncs, n_keys,
                in_col_typs, out_col_typs, func_idx_to_in_col, oao__lid)
            udf_func_struct.set_general_cfunc(egf__anf)
        thwj__vcxvj = []
        oylt__qoozs = 0
        ahn__uwr = 0
        for mebw__jucz, axgis__hqs in zip(ngpml__gahn.values(), allfuncs):
            if axgis__hqs.ftype in ('udf', 'gen_udf'):
                thwj__vcxvj.append(mebw__jucz + '_dummy')
                for szf__nzi in range(oylt__qoozs, oylt__qoozs +
                    nryz__zcgnz[ahn__uwr]):
                    thwj__vcxvj.append('data_redvar_dummy_' + str(szf__nzi))
                oylt__qoozs += nryz__zcgnz[ahn__uwr]
                ahn__uwr += 1
        if udf_func_struct.regular_udfs:
            mbtn__nxcrd = udf_func_struct.var_typs
            for ahn__uwr, t in enumerate(mbtn__nxcrd):
                ehulv__jqu += ('    data_redvar_dummy_{} = np.empty(1, {})\n'
                    .format(ahn__uwr, _get_np_dtype(t)))
        ehulv__jqu += '    out_info_list_dummy = [{}]\n'.format(', '.join(
            'array_to_info({})'.format(a) for a in thwj__vcxvj))
        ehulv__jqu += (
            '    udf_table_dummy = arr_info_list_to_table(out_info_list_dummy)\n'
            )
        if udf_func_struct.regular_udfs:
            ehulv__jqu += ("    add_agg_cfunc_sym(cpp_cb_update, '{}')\n".
                format(jga__zboq.native_name))
            ehulv__jqu += ("    add_agg_cfunc_sym(cpp_cb_combine, '{}')\n".
                format(mzsxl__azhk.native_name))
            ehulv__jqu += "    add_agg_cfunc_sym(cpp_cb_eval, '{}')\n".format(
                doq__uwxyo.native_name)
            ehulv__jqu += ("    cpp_cb_update_addr = get_agg_udf_addr('{}')\n"
                .format(jga__zboq.native_name))
            ehulv__jqu += ("    cpp_cb_combine_addr = get_agg_udf_addr('{}')\n"
                .format(mzsxl__azhk.native_name))
            ehulv__jqu += ("    cpp_cb_eval_addr = get_agg_udf_addr('{}')\n"
                .format(doq__uwxyo.native_name))
        else:
            ehulv__jqu += '    cpp_cb_update_addr = 0\n'
            ehulv__jqu += '    cpp_cb_combine_addr = 0\n'
            ehulv__jqu += '    cpp_cb_eval_addr = 0\n'
        if udf_func_struct.general_udfs:
            hoes__vveg = udf_func_struct.general_udf_cfunc
            gb_agg_cfunc[hoes__vveg.native_name] = hoes__vveg
            gb_agg_cfunc_addr[hoes__vveg.native_name] = hoes__vveg.address
            ehulv__jqu += ("    add_agg_cfunc_sym(cpp_cb_general, '{}')\n".
                format(hoes__vveg.native_name))
            ehulv__jqu += ("    cpp_cb_general_addr = get_agg_udf_addr('{}')\n"
                .format(hoes__vveg.native_name))
        else:
            ehulv__jqu += '    cpp_cb_general_addr = 0\n'
    else:
        ehulv__jqu += """    udf_table_dummy = arr_info_list_to_table([array_to_info(np.empty(1))])
"""
        ehulv__jqu += '    cpp_cb_update_addr = 0\n'
        ehulv__jqu += '    cpp_cb_combine_addr = 0\n'
        ehulv__jqu += '    cpp_cb_eval_addr = 0\n'
        ehulv__jqu += '    cpp_cb_general_addr = 0\n'
    ehulv__jqu += '    ftypes = np.array([{}, 0], dtype=np.int32)\n'.format(
        ', '.join([str(supported_agg_funcs.index(axgis__hqs.ftype)) for
        axgis__hqs in allfuncs] + ['0']))
    ehulv__jqu += '    func_offsets = np.array({}, dtype=np.int32)\n'.format(
        str(qqzjl__vcqal))
    if len(nryz__zcgnz) > 0:
        ehulv__jqu += '    udf_ncols = np.array({}, dtype=np.int32)\n'.format(
            str(nryz__zcgnz))
    else:
        ehulv__jqu += '    udf_ncols = np.array([0], np.int32)\n'
    if mzb__apus:
        ehulv__jqu += '    arr_type = coerce_to_array({})\n'.format(agg_node
            .pivot_values)
        ehulv__jqu += '    arr_info = array_to_info(arr_type)\n'
        ehulv__jqu += (
            '    dispatch_table = arr_info_list_to_table([arr_info])\n')
        ehulv__jqu += '    pivot_info = array_to_info(pivot_arr)\n'
        ehulv__jqu += (
            '    dispatch_info = arr_info_list_to_table([pivot_info])\n')
        ehulv__jqu += (
            """    out_table = pivot_groupby_and_aggregate(table, {}, dispatch_table, dispatch_info, {}, ftypes.ctypes, func_offsets.ctypes, udf_ncols.ctypes, {}, {}, {}, {}, {}, cpp_cb_update_addr, cpp_cb_combine_addr, cpp_cb_eval_addr, udf_table_dummy)
"""
            .format(n_keys, agg_node.input_has_index, parallel, agg_node.
            is_crosstab, rhz__eem, agg_node.return_key, agg_node.same_index))
        ehulv__jqu += '    delete_info_decref_array(pivot_info)\n'
        ehulv__jqu += '    delete_info_decref_array(arr_info)\n'
    else:
        ehulv__jqu += (
            """    out_table = groupby_and_aggregate(table, {}, {}, ftypes.ctypes, func_offsets.ctypes, udf_ncols.ctypes, {}, {}, {}, {}, {}, {}, {}, {}, cpp_cb_update_addr, cpp_cb_combine_addr, cpp_cb_eval_addr, cpp_cb_general_addr, udf_table_dummy)
"""
            .format(n_keys, agg_node.input_has_index, parallel, rhz__eem,
            fqr__pxt, rtzl__ressy, hnq__xtb, agg_node.return_key, agg_node.
            same_index, agg_node.dropna))
    qyous__dqb = 0
    if agg_node.return_key:
        for ahn__uwr, wjtkr__ymecg in enumerate(vtcn__tnyq):
            ehulv__jqu += (
                '    {} = info_to_array(info_from_table(out_table, {}), {})\n'
                .format(wjtkr__ymecg, qyous__dqb, wjtkr__ymecg))
            qyous__dqb += 1
    for mebw__jucz in ngpml__gahn.values():
        ehulv__jqu += (
            '    {} = info_to_array(info_from_table(out_table, {}), {})\n'.
            format(mebw__jucz, qyous__dqb, mebw__jucz + '_dummy'))
        qyous__dqb += 1
    if agg_node.same_index:
        ehulv__jqu += (
            """    out_index_arg = info_to_array(info_from_table(out_table, {}), index_arg)
"""
            .format(qyous__dqb))
        qyous__dqb += 1
    ehulv__jqu += (
        f"    ev_clean = bodo.utils.tracing.Event('tables_clean_up', {parallel})\n"
        )
    ehulv__jqu += '    delete_table_decref_arrays(table)\n'
    ehulv__jqu += '    delete_table_decref_arrays(udf_table_dummy)\n'
    ehulv__jqu += '    delete_table(out_table)\n'
    ehulv__jqu += f'    ev_clean.finalize()\n'
    zpa__lqi = tuple(ngpml__gahn.values())
    if agg_node.return_key:
        zpa__lqi += tuple(vtcn__tnyq)
    ehulv__jqu += '    return ({},{})\n'.format(', '.join(zpa__lqi), 
        ' out_index_arg,' if agg_node.same_index else '')
    onbqk__vimxo = {}
    exec(ehulv__jqu, {}, onbqk__vimxo)
    czg__bkyne = onbqk__vimxo['agg_top']
    return czg__bkyne


def compile_to_optimized_ir(func, arg_typs, typingctx, targetctx):
    code = func.code if hasattr(func, 'code') else func.__code__
    closure = func.closure if hasattr(func, 'closure') else func.__closure__
    f_ir = get_ir_of_code(func.__globals__, code)
    replace_closures(f_ir, closure, code)
    for block in f_ir.blocks.values():
        for dos__bwjqj in block.body:
            if is_call_assign(dos__bwjqj) and find_callname(f_ir,
                dos__bwjqj.value) == ('len', 'builtins'
                ) and dos__bwjqj.value.args[0].name == f_ir.arg_names[0]:
                kyad__tleuj = get_definition(f_ir, dos__bwjqj.value.func)
                kyad__tleuj.name = 'dummy_agg_count'
                kyad__tleuj.value = dummy_agg_count
    rpreb__nte = get_name_var_table(f_ir.blocks)
    ltr__uhl = {}
    for name, aldiq__kcir in rpreb__nte.items():
        ltr__uhl[name] = mk_unique_var(name)
    replace_var_names(f_ir.blocks, ltr__uhl)
    f_ir._definitions = build_definitions(f_ir.blocks)
    assert f_ir.arg_count == 1, 'agg function should have one input'
    igf__cyh = numba.core.compiler.Flags()
    igf__cyh.nrt = True
    wvu__pzp = bodo.transforms.untyped_pass.UntypedPass(f_ir, typingctx,
        arg_typs, {}, {}, igf__cyh)
    wvu__pzp.run()
    f_ir._definitions = build_definitions(f_ir.blocks)
    typemap, zkmq__jblz, calltypes, aldiq__kcir = (numba.core.typed_passes.
        type_inference_stage(typingctx, targetctx, f_ir, arg_typs, None))
    rhxj__atrxf = numba.core.cpu.ParallelOptions(True)
    targetctx = numba.core.cpu.CPUContext(typingctx)
    wqtm__lix = namedtuple('DummyPipeline', ['typingctx', 'targetctx',
        'args', 'func_ir', 'typemap', 'return_type', 'calltypes',
        'type_annotation', 'locals', 'flags', 'pipeline'])
    rqyyx__zcdg = namedtuple('TypeAnnotation', ['typemap', 'calltypes'])
    cadkj__jcmq = rqyyx__zcdg(typemap, calltypes)
    pm = wqtm__lix(typingctx, targetctx, None, f_ir, typemap, zkmq__jblz,
        calltypes, cadkj__jcmq, {}, igf__cyh, None)
    tys__aqq = numba.core.compiler.DefaultPassBuilder.define_untyped_pipeline(
        pm)
    pm = wqtm__lix(typingctx, targetctx, None, f_ir, typemap, zkmq__jblz,
        calltypes, cadkj__jcmq, {}, igf__cyh, tys__aqq)
    ljrlt__avqfv = numba.core.typed_passes.InlineOverloads()
    ljrlt__avqfv.run_pass(pm)
    vvb__wdrv = bodo.transforms.series_pass.SeriesPass(f_ir, typingctx,
        targetctx, typemap, calltypes, {}, False)
    vvb__wdrv.run()
    for block in f_ir.blocks.values():
        for dos__bwjqj in block.body:
            if is_assign(dos__bwjqj) and isinstance(dos__bwjqj.value, (ir.
                Arg, ir.Var)) and isinstance(typemap[dos__bwjqj.target.name
                ], SeriesType):
                kdg__kem = typemap.pop(dos__bwjqj.target.name)
                typemap[dos__bwjqj.target.name] = kdg__kem.data
            if is_call_assign(dos__bwjqj) and find_callname(f_ir,
                dos__bwjqj.value) == ('get_series_data',
                'bodo.hiframes.pd_series_ext'):
                f_ir._definitions[dos__bwjqj.target.name].remove(dos__bwjqj
                    .value)
                dos__bwjqj.value = dos__bwjqj.value.args[0]
                f_ir._definitions[dos__bwjqj.target.name].append(dos__bwjqj
                    .value)
            if is_call_assign(dos__bwjqj) and find_callname(f_ir,
                dos__bwjqj.value) == ('isna', 'bodo.libs.array_kernels'):
                f_ir._definitions[dos__bwjqj.target.name].remove(dos__bwjqj
                    .value)
                dos__bwjqj.value = ir.Const(False, dos__bwjqj.loc)
                f_ir._definitions[dos__bwjqj.target.name].append(dos__bwjqj
                    .value)
            if is_call_assign(dos__bwjqj) and find_callname(f_ir,
                dos__bwjqj.value) == ('setna', 'bodo.libs.array_kernels'):
                f_ir._definitions[dos__bwjqj.target.name].remove(dos__bwjqj
                    .value)
                dos__bwjqj.value = ir.Const(False, dos__bwjqj.loc)
                f_ir._definitions[dos__bwjqj.target.name].append(dos__bwjqj
                    .value)
    bodo.transforms.untyped_pass.remove_dead_branches(f_ir)
    hfr__ukte = numba.parfors.parfor.PreParforPass(f_ir, typemap, calltypes,
        typingctx, targetctx, rhxj__atrxf)
    hfr__ukte.run()
    f_ir._definitions = build_definitions(f_ir.blocks)
    vih__pmntz = numba.core.compiler.StateDict()
    vih__pmntz.func_ir = f_ir
    vih__pmntz.typemap = typemap
    vih__pmntz.calltypes = calltypes
    vih__pmntz.typingctx = typingctx
    vih__pmntz.targetctx = targetctx
    vih__pmntz.return_type = zkmq__jblz
    numba.core.rewrites.rewrite_registry.apply('after-inference', vih__pmntz)
    fyz__gxemn = numba.parfors.parfor.ParforPass(f_ir, typemap, calltypes,
        zkmq__jblz, typingctx, targetctx, rhxj__atrxf, igf__cyh, {})
    fyz__gxemn.run()
    remove_dels(f_ir.blocks)
    numba.parfors.parfor.maximize_fusion(f_ir, f_ir.blocks, typemap, False)
    return f_ir, pm


def replace_closures(f_ir, closure, code):
    if closure:
        closure = f_ir.get_definition(closure)
        if isinstance(closure, tuple):
            scxij__zvuu = ctypes.pythonapi.PyCell_Get
            scxij__zvuu.restype = ctypes.py_object
            scxij__zvuu.argtypes = ctypes.py_object,
            rbh__oee = tuple(scxij__zvuu(prdff__cjgxg) for prdff__cjgxg in
                closure)
        else:
            assert isinstance(closure, ir.Expr) and closure.op == 'build_tuple'
            rbh__oee = closure.items
        assert len(code.co_freevars) == len(rbh__oee)
        numba.core.inline_closurecall._replace_freevars(f_ir.blocks, rbh__oee)


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
        mor__agh = SeriesType(in_col_typ.dtype, in_col_typ, None, string_type)
        f_ir, pm = compile_to_optimized_ir(func, (mor__agh,), self.
            typingctx, self.targetctx)
        f_ir._definitions = build_definitions(f_ir.blocks)
        assert len(f_ir.blocks
            ) == 1 and 0 in f_ir.blocks, 'only simple functions with one block supported for aggregation'
        block = f_ir.blocks[0]
        dggel__ogkml, arr_var = _rm_arg_agg_block(block, pm.typemap)
        nnov__nup = -1
        for ahn__uwr, dos__bwjqj in enumerate(dggel__ogkml):
            if isinstance(dos__bwjqj, numba.parfors.parfor.Parfor):
                assert nnov__nup == -1, 'only one parfor for aggregation function'
                nnov__nup = ahn__uwr
        parfor = None
        if nnov__nup != -1:
            parfor = dggel__ogkml[nnov__nup]
            remove_dels(parfor.loop_body)
            remove_dels({(0): parfor.init_block})
        init_nodes = []
        if parfor:
            init_nodes = dggel__ogkml[:nnov__nup] + parfor.init_block.body
        eval_nodes = dggel__ogkml[nnov__nup + 1:]
        redvars = []
        var_to_redvar = {}
        if parfor:
            redvars, var_to_redvar = get_parfor_reductions(parfor, parfor.
                params, pm.calltypes)
        func.ncols_pre_shuffle = len(redvars)
        func.ncols_post_shuffle = len(redvars) + 1
        func.n_redvars = len(redvars)
        reduce_vars = [0] * len(redvars)
        for dos__bwjqj in init_nodes:
            if is_assign(dos__bwjqj) and dos__bwjqj.target.name in redvars:
                ind = redvars.index(dos__bwjqj.target.name)
                reduce_vars[ind] = dos__bwjqj.target
        var_types = [pm.typemap[ywzqp__slab] for ywzqp__slab in redvars]
        wyrqy__viqeb = gen_combine_func(f_ir, parfor, redvars,
            var_to_redvar, var_types, arr_var, pm, self.typingctx, self.
            targetctx)
        init_nodes = _mv_read_only_init_vars(init_nodes, parfor, eval_nodes)
        kwxfz__bjcc = gen_update_func(parfor, redvars, var_to_redvar,
            var_types, arr_var, in_col_typ, pm, self.typingctx, self.targetctx)
        ypbas__srom = gen_eval_func(f_ir, eval_nodes, reduce_vars,
            var_types, pm, self.typingctx, self.targetctx)
        self.all_reduce_vars += reduce_vars
        self.all_vartypes += var_types
        self.all_init_nodes += init_nodes
        self.all_eval_funcs.append(ypbas__srom)
        self.all_update_funcs.append(kwxfz__bjcc)
        self.all_combine_funcs.append(wyrqy__viqeb)
        self.curr_offset += len(redvars)
        self.redvar_offsets.append(self.curr_offset)

    def gen_all_func(self):
        if len(self.all_update_funcs) == 0:
            return None
        self.all_vartypes = self.all_vartypes * len(self.pivot_values
            ) if self.pivot_values is not None else self.all_vartypes
        self.all_reduce_vars = self.all_reduce_vars * len(self.pivot_values
            ) if self.pivot_values is not None else self.all_reduce_vars
        ont__ltlo = gen_init_func(self.all_init_nodes, self.all_reduce_vars,
            self.all_vartypes, self.typingctx, self.targetctx)
        ksxlb__vzs = gen_all_update_func(self.all_update_funcs, self.
            all_vartypes, self.in_col_types, self.redvar_offsets, self.
            typingctx, self.targetctx, self.pivot_typ, self.pivot_values,
            self.is_crosstab)
        azs__pielu = gen_all_combine_func(self.all_combine_funcs, self.
            all_vartypes, self.redvar_offsets, self.typingctx, self.
            targetctx, self.pivot_typ, self.pivot_values)
        rrm__vxp = gen_all_eval_func(self.all_eval_funcs, self.all_vartypes,
            self.redvar_offsets, self.out_col_types, self.typingctx, self.
            targetctx, self.pivot_values)
        return self.all_vartypes, ont__ltlo, ksxlb__vzs, azs__pielu, rrm__vxp


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
    undxp__qmy = []
    for t, axgis__hqs in zip(in_col_types, agg_func):
        undxp__qmy.append((t, axgis__hqs))
    rpxv__gufxe = RegularUDFGenerator(in_col_types, out_col_types,
        pivot_typ, pivot_values, is_crosstab, typingctx, targetctx)
    xjc__jmet = GeneralUDFGenerator()
    for in_col_typ, func in undxp__qmy:
        if func.ftype not in ('udf', 'gen_udf'):
            continue
        try:
            rpxv__gufxe.add_udf(in_col_typ, func)
        except:
            xjc__jmet.add_udf(func)
            func.ftype = 'gen_udf'
    regular_udf_funcs = rpxv__gufxe.gen_all_func()
    general_udf_funcs = xjc__jmet.gen_all_func()
    if regular_udf_funcs is not None or general_udf_funcs is not None:
        return AggUDFStruct(regular_udf_funcs, general_udf_funcs)
    else:
        return None


def _mv_read_only_init_vars(init_nodes, parfor, eval_nodes):
    if not parfor:
        return init_nodes
    wtl__xtb = compute_use_defs(parfor.loop_body)
    huikd__ikgj = set()
    for etsxd__wrctx in wtl__xtb.usemap.values():
        huikd__ikgj |= etsxd__wrctx
    yegn__qeck = set()
    for etsxd__wrctx in wtl__xtb.defmap.values():
        yegn__qeck |= etsxd__wrctx
    ktye__crbi = ir.Block(ir.Scope(None, parfor.loc), parfor.loc)
    ktye__crbi.body = eval_nodes
    pstkz__dkw = compute_use_defs({(0): ktye__crbi})
    udjk__bynr = pstkz__dkw.usemap[0]
    jyvv__qof = set()
    sdfxm__rwwtd = []
    wux__cdfx = []
    for dos__bwjqj in reversed(init_nodes):
        ykco__get = {ywzqp__slab.name for ywzqp__slab in dos__bwjqj.list_vars()
            }
        if is_assign(dos__bwjqj):
            ywzqp__slab = dos__bwjqj.target.name
            ykco__get.remove(ywzqp__slab)
            if (ywzqp__slab in huikd__ikgj and ywzqp__slab not in jyvv__qof and
                ywzqp__slab not in udjk__bynr and ywzqp__slab not in yegn__qeck
                ):
                wux__cdfx.append(dos__bwjqj)
                huikd__ikgj |= ykco__get
                yegn__qeck.add(ywzqp__slab)
                continue
        jyvv__qof |= ykco__get
        sdfxm__rwwtd.append(dos__bwjqj)
    wux__cdfx.reverse()
    sdfxm__rwwtd.reverse()
    wgh__xau = min(parfor.loop_body.keys())
    gdzsm__zzndf = parfor.loop_body[wgh__xau]
    gdzsm__zzndf.body = wux__cdfx + gdzsm__zzndf.body
    return sdfxm__rwwtd


def gen_init_func(init_nodes, reduce_vars, var_types, typingctx, targetctx):
    usen__nntt = (numba.parfors.parfor.max_checker, numba.parfors.parfor.
        min_checker, numba.parfors.parfor.argmax_checker, numba.parfors.
        parfor.argmin_checker)
    owech__xzyl = set()
    syyy__ycy = []
    for dos__bwjqj in init_nodes:
        if is_assign(dos__bwjqj) and isinstance(dos__bwjqj.value, ir.Global
            ) and isinstance(dos__bwjqj.value.value, pytypes.FunctionType
            ) and dos__bwjqj.value.value in usen__nntt:
            owech__xzyl.add(dos__bwjqj.target.name)
        elif is_call_assign(dos__bwjqj
            ) and dos__bwjqj.value.func.name in owech__xzyl:
            pass
        else:
            syyy__ycy.append(dos__bwjqj)
    init_nodes = syyy__ycy
    rch__twg = types.Tuple(var_types)
    egfe__zfgg = lambda : None
    f_ir = compile_to_numba_ir(egfe__zfgg, {})
    block = list(f_ir.blocks.values())[0]
    loc = block.loc
    osxfg__xnc = ir.Var(block.scope, mk_unique_var('init_tup'), loc)
    lcv__pbcyu = ir.Assign(ir.Expr.build_tuple(reduce_vars, loc),
        osxfg__xnc, loc)
    block.body = block.body[-2:]
    block.body = init_nodes + [lcv__pbcyu] + block.body
    block.body[-2].value.value = osxfg__xnc
    zwovk__cxc = compiler.compile_ir(typingctx, targetctx, f_ir, (),
        rch__twg, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    qiofy__qzxqd = numba.core.target_extension.dispatcher_registry[cpu_target](
        egfe__zfgg)
    qiofy__qzxqd.add_overload(zwovk__cxc)
    return qiofy__qzxqd


def gen_all_update_func(update_funcs, reduce_var_types, in_col_types,
    redvar_offsets, typingctx, targetctx, pivot_typ, pivot_values, is_crosstab
    ):
    munw__ldqz = len(update_funcs)
    bio__rax = len(in_col_types)
    if pivot_values is not None:
        assert bio__rax == 1
    ehulv__jqu = (
        'def update_all_f(redvar_arrs, data_in, w_ind, i, pivot_arr):\n')
    if pivot_values is not None:
        henx__rmoj = redvar_offsets[bio__rax]
        ehulv__jqu += '  pv = pivot_arr[i]\n'
        for szf__nzi, xfoqd__zcrf in enumerate(pivot_values):
            szjc__tbeo = 'el' if szf__nzi != 0 else ''
            ehulv__jqu += "  {}if pv == '{}':\n".format(szjc__tbeo, xfoqd__zcrf
                )
            zvodp__setra = henx__rmoj * szf__nzi
            sbqtm__nqhmh = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                ahn__uwr) for ahn__uwr in range(zvodp__setra +
                redvar_offsets[0], zvodp__setra + redvar_offsets[1])])
            jjnf__fdkl = 'data_in[0][i]'
            if is_crosstab:
                jjnf__fdkl = '0'
            ehulv__jqu += '    {} = update_vars_0({}, {})\n'.format(
                sbqtm__nqhmh, sbqtm__nqhmh, jjnf__fdkl)
    else:
        for szf__nzi in range(munw__ldqz):
            sbqtm__nqhmh = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                ahn__uwr) for ahn__uwr in range(redvar_offsets[szf__nzi],
                redvar_offsets[szf__nzi + 1])])
            if sbqtm__nqhmh:
                ehulv__jqu += ('  {} = update_vars_{}({},  data_in[{}][i])\n'
                    .format(sbqtm__nqhmh, szf__nzi, sbqtm__nqhmh, 0 if 
                    bio__rax == 1 else szf__nzi))
    ehulv__jqu += '  return\n'
    anav__qswph = {}
    for ahn__uwr, axgis__hqs in enumerate(update_funcs):
        anav__qswph['update_vars_{}'.format(ahn__uwr)] = axgis__hqs
    onbqk__vimxo = {}
    exec(ehulv__jqu, anav__qswph, onbqk__vimxo)
    hbf__wxjem = onbqk__vimxo['update_all_f']
    return numba.njit(no_cpython_wrapper=True)(hbf__wxjem)


def gen_all_combine_func(combine_funcs, reduce_var_types, redvar_offsets,
    typingctx, targetctx, pivot_typ, pivot_values):
    qlk__wnuhz = types.Tuple([types.Array(t, 1, 'C') for t in reduce_var_types]
        )
    arg_typs = qlk__wnuhz, qlk__wnuhz, types.intp, types.intp, pivot_typ
    pxfl__ujzs = len(redvar_offsets) - 1
    henx__rmoj = redvar_offsets[pxfl__ujzs]
    ehulv__jqu = (
        'def combine_all_f(redvar_arrs, recv_arrs, w_ind, i, pivot_arr):\n')
    if pivot_values is not None:
        assert pxfl__ujzs == 1
        for vrqyr__rhbyd in range(len(pivot_values)):
            zvodp__setra = henx__rmoj * vrqyr__rhbyd
            sbqtm__nqhmh = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                ahn__uwr) for ahn__uwr in range(zvodp__setra +
                redvar_offsets[0], zvodp__setra + redvar_offsets[1])])
            dibky__uyg = ', '.join(['recv_arrs[{}][i]'.format(ahn__uwr) for
                ahn__uwr in range(zvodp__setra + redvar_offsets[0], 
                zvodp__setra + redvar_offsets[1])])
            ehulv__jqu += '  {} = combine_vars_0({}, {})\n'.format(sbqtm__nqhmh
                , sbqtm__nqhmh, dibky__uyg)
    else:
        for szf__nzi in range(pxfl__ujzs):
            sbqtm__nqhmh = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                ahn__uwr) for ahn__uwr in range(redvar_offsets[szf__nzi],
                redvar_offsets[szf__nzi + 1])])
            dibky__uyg = ', '.join(['recv_arrs[{}][i]'.format(ahn__uwr) for
                ahn__uwr in range(redvar_offsets[szf__nzi], redvar_offsets[
                szf__nzi + 1])])
            if dibky__uyg:
                ehulv__jqu += '  {} = combine_vars_{}({}, {})\n'.format(
                    sbqtm__nqhmh, szf__nzi, sbqtm__nqhmh, dibky__uyg)
    ehulv__jqu += '  return\n'
    anav__qswph = {}
    for ahn__uwr, axgis__hqs in enumerate(combine_funcs):
        anav__qswph['combine_vars_{}'.format(ahn__uwr)] = axgis__hqs
    onbqk__vimxo = {}
    exec(ehulv__jqu, anav__qswph, onbqk__vimxo)
    nsr__aeq = onbqk__vimxo['combine_all_f']
    f_ir = compile_to_numba_ir(nsr__aeq, anav__qswph)
    azs__pielu = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        types.none, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    qiofy__qzxqd = numba.core.target_extension.dispatcher_registry[cpu_target](
        nsr__aeq)
    qiofy__qzxqd.add_overload(azs__pielu)
    return qiofy__qzxqd


def gen_all_eval_func(eval_funcs, reduce_var_types, redvar_offsets,
    out_col_typs, typingctx, targetctx, pivot_values):
    qlk__wnuhz = types.Tuple([types.Array(t, 1, 'C') for t in reduce_var_types]
        )
    out_col_typs = types.Tuple(out_col_typs)
    pxfl__ujzs = len(redvar_offsets) - 1
    henx__rmoj = redvar_offsets[pxfl__ujzs]
    ehulv__jqu = 'def eval_all_f(redvar_arrs, out_arrs, j):\n'
    if pivot_values is not None:
        assert pxfl__ujzs == 1
        for szf__nzi in range(len(pivot_values)):
            zvodp__setra = henx__rmoj * szf__nzi
            sbqtm__nqhmh = ', '.join(['redvar_arrs[{}][j]'.format(ahn__uwr) for
                ahn__uwr in range(zvodp__setra + redvar_offsets[0], 
                zvodp__setra + redvar_offsets[1])])
            ehulv__jqu += '  out_arrs[{}][j] = eval_vars_0({})\n'.format(
                szf__nzi, sbqtm__nqhmh)
    else:
        for szf__nzi in range(pxfl__ujzs):
            sbqtm__nqhmh = ', '.join(['redvar_arrs[{}][j]'.format(ahn__uwr) for
                ahn__uwr in range(redvar_offsets[szf__nzi], redvar_offsets[
                szf__nzi + 1])])
            ehulv__jqu += '  out_arrs[{}][j] = eval_vars_{}({})\n'.format(
                szf__nzi, szf__nzi, sbqtm__nqhmh)
    ehulv__jqu += '  return\n'
    anav__qswph = {}
    for ahn__uwr, axgis__hqs in enumerate(eval_funcs):
        anav__qswph['eval_vars_{}'.format(ahn__uwr)] = axgis__hqs
    onbqk__vimxo = {}
    exec(ehulv__jqu, anav__qswph, onbqk__vimxo)
    ndq__rtwvn = onbqk__vimxo['eval_all_f']
    return numba.njit(no_cpython_wrapper=True)(ndq__rtwvn)


def gen_eval_func(f_ir, eval_nodes, reduce_vars, var_types, pm, typingctx,
    targetctx):
    gfyzh__gzrqh = len(var_types)
    oxm__jmd = [f'in{ahn__uwr}' for ahn__uwr in range(gfyzh__gzrqh)]
    rch__twg = types.unliteral(pm.typemap[eval_nodes[-1].value.name])
    xueg__xnn = rch__twg(0)
    ehulv__jqu = 'def agg_eval({}):\n return _zero\n'.format(', '.join(
        oxm__jmd))
    onbqk__vimxo = {}
    exec(ehulv__jqu, {'_zero': xueg__xnn}, onbqk__vimxo)
    qvt__bhjkg = onbqk__vimxo['agg_eval']
    arg_typs = tuple(var_types)
    f_ir = compile_to_numba_ir(qvt__bhjkg, {'numba': numba, 'bodo': bodo,
        'np': np, '_zero': xueg__xnn}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=arg_typs, typemap=pm.typemap, calltypes=pm.
        calltypes)
    block = list(f_ir.blocks.values())[0]
    zre__mrpum = []
    for ahn__uwr, ywzqp__slab in enumerate(reduce_vars):
        zre__mrpum.append(ir.Assign(block.body[ahn__uwr].target,
            ywzqp__slab, ywzqp__slab.loc))
        for spkx__qft in ywzqp__slab.versioned_names:
            zre__mrpum.append(ir.Assign(ywzqp__slab, ir.Var(ywzqp__slab.
                scope, spkx__qft, ywzqp__slab.loc), ywzqp__slab.loc))
    block.body = block.body[:gfyzh__gzrqh] + zre__mrpum + eval_nodes
    ypbas__srom = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        rch__twg, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    qiofy__qzxqd = numba.core.target_extension.dispatcher_registry[cpu_target](
        qvt__bhjkg)
    qiofy__qzxqd.add_overload(ypbas__srom)
    return qiofy__qzxqd


def gen_combine_func(f_ir, parfor, redvars, var_to_redvar, var_types,
    arr_var, pm, typingctx, targetctx):
    if not parfor:
        return numba.njit(lambda : ())
    gfyzh__gzrqh = len(redvars)
    fwsg__jhvv = [f'v{ahn__uwr}' for ahn__uwr in range(gfyzh__gzrqh)]
    oxm__jmd = [f'in{ahn__uwr}' for ahn__uwr in range(gfyzh__gzrqh)]
    ehulv__jqu = 'def agg_combine({}):\n'.format(', '.join(fwsg__jhvv +
        oxm__jmd))
    tqo__pvpa = wrap_parfor_blocks(parfor)
    iussi__rpnjb = find_topo_order(tqo__pvpa)
    iussi__rpnjb = iussi__rpnjb[1:]
    unwrap_parfor_blocks(parfor)
    kqt__grq = {}
    fglxf__ued = []
    for unvv__zjzrl in iussi__rpnjb:
        obena__phj = parfor.loop_body[unvv__zjzrl]
        for dos__bwjqj in obena__phj.body:
            if is_call_assign(dos__bwjqj) and guard(find_callname, f_ir,
                dos__bwjqj.value) == ('__special_combine', 'bodo.ir.aggregate'
                ):
                args = dos__bwjqj.value.args
                zyqo__uqz = []
                ebog__stmkj = []
                for ywzqp__slab in args[:-1]:
                    ind = redvars.index(ywzqp__slab.name)
                    fglxf__ued.append(ind)
                    zyqo__uqz.append('v{}'.format(ind))
                    ebog__stmkj.append('in{}'.format(ind))
                cwgh__xsmvt = '__special_combine__{}'.format(len(kqt__grq))
                ehulv__jqu += '    ({},) = {}({})\n'.format(', '.join(
                    zyqo__uqz), cwgh__xsmvt, ', '.join(zyqo__uqz + ebog__stmkj)
                    )
                jfhzk__oxo = ir.Expr.call(args[-1], [], (), obena__phj.loc)
                rdob__gviof = guard(find_callname, f_ir, jfhzk__oxo)
                assert rdob__gviof == ('_var_combine', 'bodo.ir.aggregate')
                rdob__gviof = bodo.ir.aggregate._var_combine
                kqt__grq[cwgh__xsmvt] = rdob__gviof
            if is_assign(dos__bwjqj) and dos__bwjqj.target.name in redvars:
                ofzsm__uwdt = dos__bwjqj.target.name
                ind = redvars.index(ofzsm__uwdt)
                if ind in fglxf__ued:
                    continue
                if len(f_ir._definitions[ofzsm__uwdt]) == 2:
                    var_def = f_ir._definitions[ofzsm__uwdt][0]
                    ehulv__jqu += _match_reduce_def(var_def, f_ir, ind)
                    var_def = f_ir._definitions[ofzsm__uwdt][1]
                    ehulv__jqu += _match_reduce_def(var_def, f_ir, ind)
    ehulv__jqu += '    return {}'.format(', '.join(['v{}'.format(ahn__uwr) for
        ahn__uwr in range(gfyzh__gzrqh)]))
    onbqk__vimxo = {}
    exec(ehulv__jqu, {}, onbqk__vimxo)
    obsut__xtd = onbqk__vimxo['agg_combine']
    arg_typs = tuple(2 * var_types)
    anav__qswph = {'numba': numba, 'bodo': bodo, 'np': np}
    anav__qswph.update(kqt__grq)
    f_ir = compile_to_numba_ir(obsut__xtd, anav__qswph, typingctx=typingctx,
        targetctx=targetctx, arg_typs=arg_typs, typemap=pm.typemap,
        calltypes=pm.calltypes)
    block = list(f_ir.blocks.values())[0]
    rch__twg = pm.typemap[block.body[-1].value.name]
    wyrqy__viqeb = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        rch__twg, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    qiofy__qzxqd = numba.core.target_extension.dispatcher_registry[cpu_target](
        obsut__xtd)
    qiofy__qzxqd.add_overload(wyrqy__viqeb)
    return qiofy__qzxqd


def _match_reduce_def(var_def, f_ir, ind):
    ehulv__jqu = ''
    while isinstance(var_def, ir.Var):
        var_def = guard(get_definition, f_ir, var_def)
    if isinstance(var_def, ir.Expr
        ) and var_def.op == 'inplace_binop' and var_def.fn in ('+=',
        operator.iadd):
        ehulv__jqu = '    v{} += in{}\n'.format(ind, ind)
    if isinstance(var_def, ir.Expr) and var_def.op == 'call':
        phg__evyki = guard(find_callname, f_ir, var_def)
        if phg__evyki == ('min', 'builtins'):
            ehulv__jqu = '    v{} = min(v{}, in{})\n'.format(ind, ind, ind)
        if phg__evyki == ('max', 'builtins'):
            ehulv__jqu = '    v{} = max(v{}, in{})\n'.format(ind, ind, ind)
    return ehulv__jqu


def gen_update_func(parfor, redvars, var_to_redvar, var_types, arr_var,
    in_col_typ, pm, typingctx, targetctx):
    if not parfor:
        return numba.njit(lambda A: ())
    gfyzh__gzrqh = len(redvars)
    zannc__gxjc = 1
    fcf__bunfh = []
    for ahn__uwr in range(zannc__gxjc):
        ezqk__xml = ir.Var(arr_var.scope, f'$input{ahn__uwr}', arr_var.loc)
        fcf__bunfh.append(ezqk__xml)
    yjb__ensww = parfor.loop_nests[0].index_variable
    xqwn__gfye = [0] * gfyzh__gzrqh
    for obena__phj in parfor.loop_body.values():
        yfy__pjj = []
        for dos__bwjqj in obena__phj.body:
            if is_var_assign(dos__bwjqj
                ) and dos__bwjqj.value.name == yjb__ensww.name:
                continue
            if is_getitem(dos__bwjqj
                ) and dos__bwjqj.value.value.name == arr_var.name:
                dos__bwjqj.value = fcf__bunfh[0]
            if is_call_assign(dos__bwjqj) and guard(find_callname, pm.
                func_ir, dos__bwjqj.value) == ('isna',
                'bodo.libs.array_kernels') and dos__bwjqj.value.args[0
                ].name == arr_var.name:
                dos__bwjqj.value = ir.Const(False, dos__bwjqj.target.loc)
            if is_assign(dos__bwjqj) and dos__bwjqj.target.name in redvars:
                ind = redvars.index(dos__bwjqj.target.name)
                xqwn__gfye[ind] = dos__bwjqj.target
            yfy__pjj.append(dos__bwjqj)
        obena__phj.body = yfy__pjj
    fwsg__jhvv = ['v{}'.format(ahn__uwr) for ahn__uwr in range(gfyzh__gzrqh)]
    oxm__jmd = ['in{}'.format(ahn__uwr) for ahn__uwr in range(zannc__gxjc)]
    ehulv__jqu = 'def agg_update({}):\n'.format(', '.join(fwsg__jhvv +
        oxm__jmd))
    ehulv__jqu += '    __update_redvars()\n'
    ehulv__jqu += '    return {}'.format(', '.join(['v{}'.format(ahn__uwr) for
        ahn__uwr in range(gfyzh__gzrqh)]))
    onbqk__vimxo = {}
    exec(ehulv__jqu, {}, onbqk__vimxo)
    mtw__xml = onbqk__vimxo['agg_update']
    arg_typs = tuple(var_types + [in_col_typ.dtype] * zannc__gxjc)
    f_ir = compile_to_numba_ir(mtw__xml, {'__update_redvars':
        __update_redvars}, typingctx=typingctx, targetctx=targetctx,
        arg_typs=arg_typs, typemap=pm.typemap, calltypes=pm.calltypes)
    f_ir._definitions = build_definitions(f_ir.blocks)
    zvr__omgs = f_ir.blocks.popitem()[1].body
    rch__twg = pm.typemap[zvr__omgs[-1].value.name]
    tqo__pvpa = wrap_parfor_blocks(parfor)
    iussi__rpnjb = find_topo_order(tqo__pvpa)
    iussi__rpnjb = iussi__rpnjb[1:]
    unwrap_parfor_blocks(parfor)
    f_ir.blocks = parfor.loop_body
    gdzsm__zzndf = f_ir.blocks[iussi__rpnjb[0]]
    aeqwm__nrcd = f_ir.blocks[iussi__rpnjb[-1]]
    heb__cprg = zvr__omgs[:gfyzh__gzrqh + zannc__gxjc]
    if gfyzh__gzrqh > 1:
        wikfp__lgxo = zvr__omgs[-3:]
        assert is_assign(wikfp__lgxo[0]) and isinstance(wikfp__lgxo[0].
            value, ir.Expr) and wikfp__lgxo[0].value.op == 'build_tuple'
    else:
        wikfp__lgxo = zvr__omgs[-2:]
    for ahn__uwr in range(gfyzh__gzrqh):
        gss__gox = zvr__omgs[ahn__uwr].target
        huapc__xws = ir.Assign(gss__gox, xqwn__gfye[ahn__uwr], gss__gox.loc)
        heb__cprg.append(huapc__xws)
    for ahn__uwr in range(gfyzh__gzrqh, gfyzh__gzrqh + zannc__gxjc):
        gss__gox = zvr__omgs[ahn__uwr].target
        huapc__xws = ir.Assign(gss__gox, fcf__bunfh[ahn__uwr - gfyzh__gzrqh
            ], gss__gox.loc)
        heb__cprg.append(huapc__xws)
    gdzsm__zzndf.body = heb__cprg + gdzsm__zzndf.body
    naa__sxhst = []
    for ahn__uwr in range(gfyzh__gzrqh):
        gss__gox = zvr__omgs[ahn__uwr].target
        huapc__xws = ir.Assign(xqwn__gfye[ahn__uwr], gss__gox, gss__gox.loc)
        naa__sxhst.append(huapc__xws)
    aeqwm__nrcd.body += naa__sxhst + wikfp__lgxo
    atit__qcrjh = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        rch__twg, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    qiofy__qzxqd = numba.core.target_extension.dispatcher_registry[cpu_target](
        mtw__xml)
    qiofy__qzxqd.add_overload(atit__qcrjh)
    return qiofy__qzxqd


def _rm_arg_agg_block(block, typemap):
    dggel__ogkml = []
    arr_var = None
    for ahn__uwr, dos__bwjqj in enumerate(block.body):
        if is_assign(dos__bwjqj) and isinstance(dos__bwjqj.value, ir.Arg):
            arr_var = dos__bwjqj.target
            xul__kokij = typemap[arr_var.name]
            if not isinstance(xul__kokij, types.ArrayCompatible):
                dggel__ogkml += block.body[ahn__uwr + 1:]
                break
            mchc__yds = block.body[ahn__uwr + 1]
            assert is_assign(mchc__yds) and isinstance(mchc__yds.value, ir.Expr
                ) and mchc__yds.value.op == 'getattr' and mchc__yds.value.attr == 'shape' and mchc__yds.value.value.name == arr_var.name
            zoegv__kat = mchc__yds.target
            fllcy__egcil = block.body[ahn__uwr + 2]
            assert is_assign(fllcy__egcil) and isinstance(fllcy__egcil.
                value, ir.Expr
                ) and fllcy__egcil.value.op == 'static_getitem' and fllcy__egcil.value.value.name == zoegv__kat.name
            dggel__ogkml += block.body[ahn__uwr + 3:]
            break
        dggel__ogkml.append(dos__bwjqj)
    return dggel__ogkml, arr_var


def get_parfor_reductions(parfor, parfor_params, calltypes, reduce_varnames
    =None, param_uses=None, var_to_param=None):
    if reduce_varnames is None:
        reduce_varnames = []
    if param_uses is None:
        param_uses = defaultdict(list)
    if var_to_param is None:
        var_to_param = {}
    tqo__pvpa = wrap_parfor_blocks(parfor)
    iussi__rpnjb = find_topo_order(tqo__pvpa)
    iussi__rpnjb = iussi__rpnjb[1:]
    unwrap_parfor_blocks(parfor)
    for unvv__zjzrl in reversed(iussi__rpnjb):
        for dos__bwjqj in reversed(parfor.loop_body[unvv__zjzrl].body):
            if isinstance(dos__bwjqj, ir.Assign) and (dos__bwjqj.target.
                name in parfor_params or dos__bwjqj.target.name in var_to_param
                ):
                fls__egmq = dos__bwjqj.target.name
                rhs = dos__bwjqj.value
                wpqgs__rbpnf = (fls__egmq if fls__egmq in parfor_params else
                    var_to_param[fls__egmq])
                iqmr__amwy = []
                if isinstance(rhs, ir.Var):
                    iqmr__amwy = [rhs.name]
                elif isinstance(rhs, ir.Expr):
                    iqmr__amwy = [ywzqp__slab.name for ywzqp__slab in
                        dos__bwjqj.value.list_vars()]
                param_uses[wpqgs__rbpnf].extend(iqmr__amwy)
                for ywzqp__slab in iqmr__amwy:
                    var_to_param[ywzqp__slab] = wpqgs__rbpnf
            if isinstance(dos__bwjqj, Parfor):
                get_parfor_reductions(dos__bwjqj, parfor_params, calltypes,
                    reduce_varnames, param_uses, var_to_param)
    for jic__ote, iqmr__amwy in param_uses.items():
        if jic__ote in iqmr__amwy and jic__ote not in reduce_varnames:
            reduce_varnames.append(jic__ote)
    return reduce_varnames, var_to_param


@numba.extending.register_jitable
def dummy_agg_count(A):
    return len(A)
