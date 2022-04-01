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
            hgqm__yjn = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer()])
            bkzpx__eayub = cgutils.get_or_insert_function(builder.module,
                hgqm__yjn, sym._literal_value)
            builder.call(bkzpx__eayub, [context.get_constant_null(sig.args[0])]
                )
        elif sig == types.none(types.int64, types.voidptr, types.voidptr):
            hgqm__yjn = lir.FunctionType(lir.VoidType(), [lir.IntType(64),
                lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
            bkzpx__eayub = cgutils.get_or_insert_function(builder.module,
                hgqm__yjn, sym._literal_value)
            builder.call(bkzpx__eayub, [context.get_constant(types.int64, 0
                ), context.get_constant_null(sig.args[1]), context.
                get_constant_null(sig.args[2])])
        else:
            hgqm__yjn = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64).
                as_pointer()])
            bkzpx__eayub = cgutils.get_or_insert_function(builder.module,
                hgqm__yjn, sym._literal_value)
            builder.call(bkzpx__eayub, [context.get_constant_null(sig.args[
                0]), context.get_constant_null(sig.args[1]), context.
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
        ffew__kvpe = True
        tqts__pwi = 1
        dcs__ecc = -1
        if isinstance(rhs, ir.Expr):
            for gaz__vqa in rhs.kws:
                if func_name in list_cumulative:
                    if gaz__vqa[0] == 'skipna':
                        ffew__kvpe = guard(find_const, func_ir, gaz__vqa[1])
                        if not isinstance(ffew__kvpe, bool):
                            raise BodoError(
                                'For {} argument of skipna should be a boolean'
                                .format(func_name))
                if func_name == 'nunique':
                    if gaz__vqa[0] == 'dropna':
                        ffew__kvpe = guard(find_const, func_ir, gaz__vqa[1])
                        if not isinstance(ffew__kvpe, bool):
                            raise BodoError(
                                'argument of dropna to nunique should be a boolean'
                                )
        if func_name == 'shift' and (len(rhs.args) > 0 or len(rhs.kws) > 0):
            tqts__pwi = get_call_expr_arg('shift', rhs.args, dict(rhs.kws),
                0, 'periods', tqts__pwi)
            tqts__pwi = guard(find_const, func_ir, tqts__pwi)
        if func_name == 'head':
            dcs__ecc = get_call_expr_arg('head', rhs.args, dict(rhs.kws), 0,
                'n', 5)
            if not isinstance(dcs__ecc, int):
                dcs__ecc = guard(find_const, func_ir, dcs__ecc)
            if dcs__ecc < 0:
                raise BodoError(
                    f'groupby.{func_name} does not work with negative values.')
        func.skipdropna = ffew__kvpe
        func.periods = tqts__pwi
        func.head_n = dcs__ecc
        if func_name == 'transform':
            kws = dict(rhs.kws)
            apj__uzg = get_call_expr_arg(func_name, rhs.args, kws, 0,
                'func', '')
            sql__qovy = typemap[apj__uzg.name]
            ujsv__qhare = None
            if isinstance(sql__qovy, str):
                ujsv__qhare = sql__qovy
            elif is_overload_constant_str(sql__qovy):
                ujsv__qhare = get_overload_const_str(sql__qovy)
            elif bodo.utils.typing.is_builtin_function(sql__qovy):
                ujsv__qhare = bodo.utils.typing.get_builtin_function_name(
                    sql__qovy)
            if ujsv__qhare not in bodo.ir.aggregate.supported_transform_funcs[:
                ]:
                raise BodoError(f'unsupported transform function {ujsv__qhare}'
                    )
            func.transform_func = supported_agg_funcs.index(ujsv__qhare)
        else:
            func.transform_func = supported_agg_funcs.index('no_op')
        return func
    assert func_name in ['agg', 'aggregate']
    assert typemap is not None
    kws = dict(rhs.kws)
    apj__uzg = get_call_expr_arg(func_name, rhs.args, kws, 0, 'func', '')
    if apj__uzg == '':
        sql__qovy = types.none
    else:
        sql__qovy = typemap[apj__uzg.name]
    if is_overload_constant_dict(sql__qovy):
        ackb__rgldl = get_overload_constant_dict(sql__qovy)
        jnr__zun = [get_agg_func_udf(func_ir, f_val, rhs, series_type,
            typemap) for f_val in ackb__rgldl.values()]
        return jnr__zun
    if sql__qovy == types.none:
        return [get_agg_func_udf(func_ir, get_literal_value(typemap[f_val.
            name])[1], rhs, series_type, typemap) for f_val in kws.values()]
    if isinstance(sql__qovy, types.BaseTuple):
        jnr__zun = []
        uhwei__qqp = 0
        for t in sql__qovy.types:
            if is_overload_constant_str(t):
                func_name = get_overload_const_str(t)
                jnr__zun.append(get_agg_func(func_ir, func_name, rhs,
                    series_type, typemap))
            else:
                assert typemap is not None, 'typemap is required for agg UDF handling'
                func = _get_const_agg_func(t, func_ir)
                func.ftype = 'udf'
                func.fname = _get_udf_name(func)
                if func.fname == '<lambda>':
                    func.fname = '<lambda_' + str(uhwei__qqp) + '>'
                    uhwei__qqp += 1
                jnr__zun.append(func)
        return [jnr__zun]
    if is_overload_constant_str(sql__qovy):
        func_name = get_overload_const_str(sql__qovy)
        return get_agg_func(func_ir, func_name, rhs, series_type, typemap)
    if bodo.utils.typing.is_builtin_function(sql__qovy):
        func_name = bodo.utils.typing.get_builtin_function_name(sql__qovy)
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
        uhwei__qqp = 0
        uyh__uxxs = []
        for acyd__qmrdz in f_val:
            func = get_agg_func_udf(func_ir, acyd__qmrdz, rhs, series_type,
                typemap)
            if func.fname == '<lambda>' and len(f_val) > 1:
                func.fname = f'<lambda_{uhwei__qqp}>'
                uhwei__qqp += 1
            uyh__uxxs.append(func)
        return uyh__uxxs
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
    ujsv__qhare = code.co_name
    return ujsv__qhare


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
            smddd__ffb = types.DType(args[0])
            return signature(smddd__ffb, *args)


@numba.njit(no_cpython_wrapper=True)
def _var_combine(ssqdm_a, mean_a, nobs_a, ssqdm_b, mean_b, nobs_b):
    ghk__vrs = nobs_a + nobs_b
    ebl__gfa = (nobs_a * mean_a + nobs_b * mean_b) / ghk__vrs
    ikjqe__hmb = mean_b - mean_a
    qpk__xosm = (ssqdm_a + ssqdm_b + ikjqe__hmb * ikjqe__hmb * nobs_a *
        nobs_b / ghk__vrs)
    return qpk__xosm, ebl__gfa, ghk__vrs


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
        ftmvm__bop = ''
        for lgv__hec, adf__zmte in self.df_out_vars.items():
            ftmvm__bop += "'{}':{}, ".format(lgv__hec, adf__zmte.name)
        pyn__gzrhg = '{}{{{}}}'.format(self.df_out, ftmvm__bop)
        qqodc__gozt = ''
        for lgv__hec, adf__zmte in self.df_in_vars.items():
            qqodc__gozt += "'{}':{}, ".format(lgv__hec, adf__zmte.name)
        cpjt__jywbu = '{}{{{}}}'.format(self.df_in, qqodc__gozt)
        gxa__twk = 'pivot {}:{}'.format(self.pivot_arr.name, self.pivot_values
            ) if self.pivot_arr is not None else ''
        key_names = ','.join(self.key_names)
        usu__udiv = ','.join([adf__zmte.name for adf__zmte in self.key_arrs])
        return 'aggregate: {} = {} [key: {}:{}] {}'.format(pyn__gzrhg,
            cpjt__jywbu, key_names, usu__udiv, gxa__twk)

    def remove_out_col(self, out_col_name):
        self.df_out_vars.pop(out_col_name)
        qwv__gmdvj, mpmbo__hprdo = self.gb_info_out.pop(out_col_name)
        if qwv__gmdvj is None and not self.is_crosstab:
            return
        vvfjm__rjx = self.gb_info_in[qwv__gmdvj]
        if self.pivot_arr is not None:
            self.pivot_values.remove(out_col_name)
            for yjbeg__kenxj, (func, ftmvm__bop) in enumerate(vvfjm__rjx):
                try:
                    ftmvm__bop.remove(out_col_name)
                    if len(ftmvm__bop) == 0:
                        vvfjm__rjx.pop(yjbeg__kenxj)
                        break
                except ValueError as azzy__mjn:
                    continue
        else:
            for yjbeg__kenxj, (func, ivrad__irjzb) in enumerate(vvfjm__rjx):
                if ivrad__irjzb == out_col_name:
                    vvfjm__rjx.pop(yjbeg__kenxj)
                    break
        if len(vvfjm__rjx) == 0:
            self.gb_info_in.pop(qwv__gmdvj)
            self.df_in_vars.pop(qwv__gmdvj)


def aggregate_usedefs(aggregate_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({adf__zmte.name for adf__zmte in aggregate_node.key_arrs})
    use_set.update({adf__zmte.name for adf__zmte in aggregate_node.
        df_in_vars.values()})
    if aggregate_node.pivot_arr is not None:
        use_set.add(aggregate_node.pivot_arr.name)
    def_set.update({adf__zmte.name for adf__zmte in aggregate_node.
        df_out_vars.values()})
    if aggregate_node.out_key_vars is not None:
        def_set.update({adf__zmte.name for adf__zmte in aggregate_node.
            out_key_vars})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Aggregate] = aggregate_usedefs


def remove_dead_aggregate(aggregate_node, lives_no_aliases, lives,
    arg_aliases, alias_map, func_ir, typemap):
    ens__rnnbo = [vzdsg__iruys for vzdsg__iruys, axq__ganxh in
        aggregate_node.df_out_vars.items() if axq__ganxh.name not in lives]
    for liq__spmo in ens__rnnbo:
        aggregate_node.remove_out_col(liq__spmo)
    out_key_vars = aggregate_node.out_key_vars
    if out_key_vars is not None and all(adf__zmte.name not in lives for
        adf__zmte in out_key_vars):
        aggregate_node.out_key_vars = None
    if len(aggregate_node.df_out_vars
        ) == 0 and aggregate_node.out_key_vars is None:
        return None
    return aggregate_node


ir_utils.remove_dead_extensions[Aggregate] = remove_dead_aggregate


def get_copies_aggregate(aggregate_node, typemap):
    zbs__ksd = set(adf__zmte.name for adf__zmte in aggregate_node.
        df_out_vars.values())
    if aggregate_node.out_key_vars is not None:
        zbs__ksd.update({adf__zmte.name for adf__zmte in aggregate_node.
            out_key_vars})
    return set(), zbs__ksd


ir_utils.copy_propagate_extensions[Aggregate] = get_copies_aggregate


def apply_copies_aggregate(aggregate_node, var_dict, name_var_table,
    typemap, calltypes, save_copies):
    for yjbeg__kenxj in range(len(aggregate_node.key_arrs)):
        aggregate_node.key_arrs[yjbeg__kenxj] = replace_vars_inner(
            aggregate_node.key_arrs[yjbeg__kenxj], var_dict)
    for vzdsg__iruys in list(aggregate_node.df_in_vars.keys()):
        aggregate_node.df_in_vars[vzdsg__iruys] = replace_vars_inner(
            aggregate_node.df_in_vars[vzdsg__iruys], var_dict)
    for vzdsg__iruys in list(aggregate_node.df_out_vars.keys()):
        aggregate_node.df_out_vars[vzdsg__iruys] = replace_vars_inner(
            aggregate_node.df_out_vars[vzdsg__iruys], var_dict)
    if aggregate_node.out_key_vars is not None:
        for yjbeg__kenxj in range(len(aggregate_node.out_key_vars)):
            aggregate_node.out_key_vars[yjbeg__kenxj] = replace_vars_inner(
                aggregate_node.out_key_vars[yjbeg__kenxj], var_dict)
    if aggregate_node.pivot_arr is not None:
        aggregate_node.pivot_arr = replace_vars_inner(aggregate_node.
            pivot_arr, var_dict)


ir_utils.apply_copy_propagate_extensions[Aggregate] = apply_copies_aggregate


def visit_vars_aggregate(aggregate_node, callback, cbdata):
    if debug_prints():
        print('visiting aggregate vars for:', aggregate_node)
        print('cbdata: ', sorted(cbdata.items()))
    for yjbeg__kenxj in range(len(aggregate_node.key_arrs)):
        aggregate_node.key_arrs[yjbeg__kenxj] = visit_vars_inner(aggregate_node
            .key_arrs[yjbeg__kenxj], callback, cbdata)
    for vzdsg__iruys in list(aggregate_node.df_in_vars.keys()):
        aggregate_node.df_in_vars[vzdsg__iruys] = visit_vars_inner(
            aggregate_node.df_in_vars[vzdsg__iruys], callback, cbdata)
    for vzdsg__iruys in list(aggregate_node.df_out_vars.keys()):
        aggregate_node.df_out_vars[vzdsg__iruys] = visit_vars_inner(
            aggregate_node.df_out_vars[vzdsg__iruys], callback, cbdata)
    if aggregate_node.out_key_vars is not None:
        for yjbeg__kenxj in range(len(aggregate_node.out_key_vars)):
            aggregate_node.out_key_vars[yjbeg__kenxj] = visit_vars_inner(
                aggregate_node.out_key_vars[yjbeg__kenxj], callback, cbdata)
    if aggregate_node.pivot_arr is not None:
        aggregate_node.pivot_arr = visit_vars_inner(aggregate_node.
            pivot_arr, callback, cbdata)


ir_utils.visit_vars_extensions[Aggregate] = visit_vars_aggregate


def aggregate_array_analysis(aggregate_node, equiv_set, typemap, array_analysis
    ):
    assert len(aggregate_node.df_out_vars
        ) > 0 or aggregate_node.out_key_vars is not None or aggregate_node.is_crosstab, 'empty aggregate in array analysis'
    bunw__tzlat = []
    for aaua__seyb in aggregate_node.key_arrs:
        nlq__oxkj = equiv_set.get_shape(aaua__seyb)
        if nlq__oxkj:
            bunw__tzlat.append(nlq__oxkj[0])
    if aggregate_node.pivot_arr is not None:
        nlq__oxkj = equiv_set.get_shape(aggregate_node.pivot_arr)
        if nlq__oxkj:
            bunw__tzlat.append(nlq__oxkj[0])
    for axq__ganxh in aggregate_node.df_in_vars.values():
        nlq__oxkj = equiv_set.get_shape(axq__ganxh)
        if nlq__oxkj:
            bunw__tzlat.append(nlq__oxkj[0])
    if len(bunw__tzlat) > 1:
        equiv_set.insert_equiv(*bunw__tzlat)
    ujarb__rxzeq = []
    bunw__tzlat = []
    own__cmpsi = list(aggregate_node.df_out_vars.values())
    if aggregate_node.out_key_vars is not None:
        own__cmpsi.extend(aggregate_node.out_key_vars)
    for axq__ganxh in own__cmpsi:
        kwdo__lvpmt = typemap[axq__ganxh.name]
        ppqd__bykqe = array_analysis._gen_shape_call(equiv_set, axq__ganxh,
            kwdo__lvpmt.ndim, None, ujarb__rxzeq)
        equiv_set.insert_equiv(axq__ganxh, ppqd__bykqe)
        bunw__tzlat.append(ppqd__bykqe[0])
        equiv_set.define(axq__ganxh, set())
    if len(bunw__tzlat) > 1:
        equiv_set.insert_equiv(*bunw__tzlat)
    return [], ujarb__rxzeq


numba.parfors.array_analysis.array_analysis_extensions[Aggregate
    ] = aggregate_array_analysis


def aggregate_distributed_analysis(aggregate_node, array_dists):
    psj__lfod = Distribution.OneD
    for axq__ganxh in aggregate_node.df_in_vars.values():
        psj__lfod = Distribution(min(psj__lfod.value, array_dists[
            axq__ganxh.name].value))
    for aaua__seyb in aggregate_node.key_arrs:
        psj__lfod = Distribution(min(psj__lfod.value, array_dists[
            aaua__seyb.name].value))
    if aggregate_node.pivot_arr is not None:
        psj__lfod = Distribution(min(psj__lfod.value, array_dists[
            aggregate_node.pivot_arr.name].value))
        array_dists[aggregate_node.pivot_arr.name] = psj__lfod
    for axq__ganxh in aggregate_node.df_in_vars.values():
        array_dists[axq__ganxh.name] = psj__lfod
    for aaua__seyb in aggregate_node.key_arrs:
        array_dists[aaua__seyb.name] = psj__lfod
    twkze__nmoj = Distribution.OneD_Var
    for axq__ganxh in aggregate_node.df_out_vars.values():
        if axq__ganxh.name in array_dists:
            twkze__nmoj = Distribution(min(twkze__nmoj.value, array_dists[
                axq__ganxh.name].value))
    if aggregate_node.out_key_vars is not None:
        for axq__ganxh in aggregate_node.out_key_vars:
            if axq__ganxh.name in array_dists:
                twkze__nmoj = Distribution(min(twkze__nmoj.value,
                    array_dists[axq__ganxh.name].value))
    twkze__nmoj = Distribution(min(twkze__nmoj.value, psj__lfod.value))
    for axq__ganxh in aggregate_node.df_out_vars.values():
        array_dists[axq__ganxh.name] = twkze__nmoj
    if aggregate_node.out_key_vars is not None:
        for ucd__vjv in aggregate_node.out_key_vars:
            array_dists[ucd__vjv.name] = twkze__nmoj
    if twkze__nmoj != Distribution.OneD_Var:
        for aaua__seyb in aggregate_node.key_arrs:
            array_dists[aaua__seyb.name] = twkze__nmoj
        if aggregate_node.pivot_arr is not None:
            array_dists[aggregate_node.pivot_arr.name] = twkze__nmoj
        for axq__ganxh in aggregate_node.df_in_vars.values():
            array_dists[axq__ganxh.name] = twkze__nmoj


distributed_analysis.distributed_analysis_extensions[Aggregate
    ] = aggregate_distributed_analysis


def build_agg_definitions(agg_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for axq__ganxh in agg_node.df_out_vars.values():
        definitions[axq__ganxh.name].append(agg_node)
    if agg_node.out_key_vars is not None:
        for ucd__vjv in agg_node.out_key_vars:
            definitions[ucd__vjv.name].append(agg_node)
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
        for adf__zmte in (list(agg_node.df_in_vars.values()) + list(
            agg_node.df_out_vars.values()) + agg_node.key_arrs):
            if array_dists[adf__zmte.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                adf__zmte.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    qdx__dzttd = tuple(typemap[adf__zmte.name] for adf__zmte in agg_node.
        key_arrs)
    vcozy__qhtpm = [adf__zmte for bgil__skru, adf__zmte in agg_node.
        df_in_vars.items()]
    fgg__mbc = [adf__zmte for bgil__skru, adf__zmte in agg_node.df_out_vars
        .items()]
    in_col_typs = []
    jnr__zun = []
    if agg_node.pivot_arr is not None:
        for qwv__gmdvj, vvfjm__rjx in agg_node.gb_info_in.items():
            for func, mpmbo__hprdo in vvfjm__rjx:
                if qwv__gmdvj is not None:
                    in_col_typs.append(typemap[agg_node.df_in_vars[
                        qwv__gmdvj].name])
                jnr__zun.append(func)
    else:
        for qwv__gmdvj, func in agg_node.gb_info_out.values():
            if qwv__gmdvj is not None:
                in_col_typs.append(typemap[agg_node.df_in_vars[qwv__gmdvj].
                    name])
            jnr__zun.append(func)
    out_col_typs = tuple(typemap[adf__zmte.name] for adf__zmte in fgg__mbc)
    pivot_typ = types.none if agg_node.pivot_arr is None else typemap[agg_node
        .pivot_arr.name]
    arg_typs = tuple(qdx__dzttd + tuple(typemap[adf__zmte.name] for
        adf__zmte in vcozy__qhtpm) + (pivot_typ,))
    in_col_typs = [to_str_arr_if_dict_array(t) for t in in_col_typs]
    gygcq__hye = {'bodo': bodo, 'np': np, 'dt64_dtype': np.dtype(
        'datetime64[ns]'), 'td64_dtype': np.dtype('timedelta64[ns]')}
    for yjbeg__kenxj, in_col_typ in enumerate(in_col_typs):
        if isinstance(in_col_typ, bodo.CategoricalArrayType):
            gygcq__hye.update({f'in_cat_dtype_{yjbeg__kenxj}': in_col_typ})
    for yjbeg__kenxj, hrf__mlg in enumerate(out_col_typs):
        if isinstance(hrf__mlg, bodo.CategoricalArrayType):
            gygcq__hye.update({f'out_cat_dtype_{yjbeg__kenxj}': hrf__mlg})
    udf_func_struct = get_udf_func_struct(jnr__zun, agg_node.
        input_has_index, in_col_typs, out_col_typs, typingctx, targetctx,
        pivot_typ, agg_node.pivot_values, agg_node.is_crosstab)
    cxsi__zjecg = gen_top_level_agg_func(agg_node, in_col_typs,
        out_col_typs, parallel, udf_func_struct)
    gygcq__hye.update({'pd': pd, 'pre_alloc_string_array':
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
            gygcq__hye.update({'__update_redvars': udf_func_struct.
                update_all_func, '__init_func': udf_func_struct.init_func,
                '__combine_redvars': udf_func_struct.combine_all_func,
                '__eval_res': udf_func_struct.eval_all_func,
                'cpp_cb_update': udf_func_struct.regular_udf_cfuncs[0],
                'cpp_cb_combine': udf_func_struct.regular_udf_cfuncs[1],
                'cpp_cb_eval': udf_func_struct.regular_udf_cfuncs[2]})
        if udf_func_struct.general_udfs:
            gygcq__hye.update({'cpp_cb_general': udf_func_struct.
                general_udf_cfunc})
    ffbx__iyees = compile_to_numba_ir(cxsi__zjecg, gygcq__hye, typingctx=
        typingctx, targetctx=targetctx, arg_typs=arg_typs, typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    yasj__vzt = []
    if agg_node.pivot_arr is None:
        zupik__rjpui = agg_node.key_arrs[0].scope
        loc = agg_node.loc
        rgvp__twrfk = ir.Var(zupik__rjpui, mk_unique_var('dummy_none'), loc)
        typemap[rgvp__twrfk.name] = types.none
        yasj__vzt.append(ir.Assign(ir.Const(None, loc), rgvp__twrfk, loc))
        vcozy__qhtpm.append(rgvp__twrfk)
    else:
        vcozy__qhtpm.append(agg_node.pivot_arr)
    replace_arg_nodes(ffbx__iyees, agg_node.key_arrs + vcozy__qhtpm)
    tuud__xaadh = ffbx__iyees.body[-3]
    assert is_assign(tuud__xaadh) and isinstance(tuud__xaadh.value, ir.Expr
        ) and tuud__xaadh.value.op == 'build_tuple'
    yasj__vzt += ffbx__iyees.body[:-3]
    own__cmpsi = list(agg_node.df_out_vars.values())
    if agg_node.out_key_vars is not None:
        own__cmpsi += agg_node.out_key_vars
    for yjbeg__kenxj, dirgj__hcsof in enumerate(own__cmpsi):
        exdun__spv = tuud__xaadh.value.items[yjbeg__kenxj]
        yasj__vzt.append(ir.Assign(exdun__spv, dirgj__hcsof, dirgj__hcsof.loc))
    return yasj__vzt


distributed_pass.distributed_run_extensions[Aggregate] = agg_distributed_run


def get_numba_set(dtype):
    pass


@infer_global(get_numba_set)
class GetNumbaSetTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 1
        scq__njawt = args[0]
        dtype = types.Tuple([t.dtype for t in scq__njawt.types]) if isinstance(
            scq__njawt, types.BaseTuple) else scq__njawt.dtype
        if isinstance(scq__njawt, types.BaseTuple) and len(scq__njawt.types
            ) == 1:
            dtype = scq__njawt.types[0].dtype
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
        ejr__usd = args[0]
        if ejr__usd == types.none:
            return signature(types.boolean, *args)


@lower_builtin(bool, types.none)
def lower_column_mean_impl(context, builder, sig, args):
    eoiy__pjx = context.compile_internal(builder, lambda a: False, sig, args)
    return eoiy__pjx


def _gen_dummy_alloc(t, colnum=0, is_input=False):
    if isinstance(t, IntegerArrayType):
        xlf__ifxfq = IntDtype(t.dtype).name
        assert xlf__ifxfq.endswith('Dtype()')
        xlf__ifxfq = xlf__ifxfq[:-7]
        return (
            f"bodo.hiframes.pd_series_ext.get_series_data(pd.Series([1], dtype='{xlf__ifxfq}'))"
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
        vraa__hoxvx = 'in' if is_input else 'out'
        return (
            f'bodo.utils.utils.alloc_type(1, {vraa__hoxvx}_cat_dtype_{colnum})'
            )
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
    ghtcw__oet = udf_func_struct.var_typs
    jfde__qsc = len(ghtcw__oet)
    dbx__rqc = (
        'def bodo_gb_udf_update_local{}(in_table, out_table, row_to_group):\n'
        .format(label_suffix))
    dbx__rqc += '    if is_null_pointer(in_table):\n'
    dbx__rqc += '        return\n'
    dbx__rqc += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in ghtcw__oet]), 
        ',' if len(ghtcw__oet) == 1 else '')
    urg__qhagh = n_keys
    vdtfn__nxkhi = []
    redvar_offsets = []
    nqp__wnmke = []
    if do_combine:
        for yjbeg__kenxj, acyd__qmrdz in enumerate(allfuncs):
            if acyd__qmrdz.ftype != 'udf':
                urg__qhagh += acyd__qmrdz.ncols_pre_shuffle
            else:
                redvar_offsets += list(range(urg__qhagh, urg__qhagh +
                    acyd__qmrdz.n_redvars))
                urg__qhagh += acyd__qmrdz.n_redvars
                nqp__wnmke.append(data_in_typs_[func_idx_to_in_col[
                    yjbeg__kenxj]])
                vdtfn__nxkhi.append(func_idx_to_in_col[yjbeg__kenxj] + n_keys)
    else:
        for yjbeg__kenxj, acyd__qmrdz in enumerate(allfuncs):
            if acyd__qmrdz.ftype != 'udf':
                urg__qhagh += acyd__qmrdz.ncols_post_shuffle
            else:
                redvar_offsets += list(range(urg__qhagh + 1, urg__qhagh + 1 +
                    acyd__qmrdz.n_redvars))
                urg__qhagh += acyd__qmrdz.n_redvars + 1
                nqp__wnmke.append(data_in_typs_[func_idx_to_in_col[
                    yjbeg__kenxj]])
                vdtfn__nxkhi.append(func_idx_to_in_col[yjbeg__kenxj] + n_keys)
    assert len(redvar_offsets) == jfde__qsc
    hoi__roju = len(nqp__wnmke)
    hgwyx__bgoe = []
    for yjbeg__kenxj, t in enumerate(nqp__wnmke):
        hgwyx__bgoe.append(_gen_dummy_alloc(t, yjbeg__kenxj, True))
    dbx__rqc += '    data_in_dummy = ({}{})\n'.format(','.join(hgwyx__bgoe),
        ',' if len(nqp__wnmke) == 1 else '')
    dbx__rqc += """
    # initialize redvar cols
"""
    dbx__rqc += '    init_vals = __init_func()\n'
    for yjbeg__kenxj in range(jfde__qsc):
        dbx__rqc += (
            """    redvar_arr_{} = info_to_array(info_from_table(out_table, {}), data_redvar_dummy[{}])
"""
            .format(yjbeg__kenxj, redvar_offsets[yjbeg__kenxj], yjbeg__kenxj))
        dbx__rqc += '    incref(redvar_arr_{})\n'.format(yjbeg__kenxj)
        dbx__rqc += '    redvar_arr_{}.fill(init_vals[{}])\n'.format(
            yjbeg__kenxj, yjbeg__kenxj)
    dbx__rqc += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'.
        format(yjbeg__kenxj) for yjbeg__kenxj in range(jfde__qsc)]), ',' if
        jfde__qsc == 1 else '')
    dbx__rqc += '\n'
    for yjbeg__kenxj in range(hoi__roju):
        dbx__rqc += (
            """    data_in_{} = info_to_array(info_from_table(in_table, {}), data_in_dummy[{}])
"""
            .format(yjbeg__kenxj, vdtfn__nxkhi[yjbeg__kenxj], yjbeg__kenxj))
        dbx__rqc += '    incref(data_in_{})\n'.format(yjbeg__kenxj)
    dbx__rqc += '    data_in = ({}{})\n'.format(','.join(['data_in_{}'.
        format(yjbeg__kenxj) for yjbeg__kenxj in range(hoi__roju)]), ',' if
        hoi__roju == 1 else '')
    dbx__rqc += '\n'
    dbx__rqc += '    for i in range(len(data_in_0)):\n'
    dbx__rqc += '        w_ind = row_to_group[i]\n'
    dbx__rqc += '        if w_ind != -1:\n'
    dbx__rqc += (
        '            __update_redvars(redvars, data_in, w_ind, i, pivot_arr=None)\n'
        )
    xsenc__calgv = {}
    exec(dbx__rqc, {'bodo': bodo, 'np': np, 'pd': pd, 'info_to_array':
        info_to_array, 'info_from_table': info_from_table, 'incref': incref,
        'pre_alloc_string_array': pre_alloc_string_array, '__init_func':
        udf_func_struct.init_func, '__update_redvars': udf_func_struct.
        update_all_func, 'is_null_pointer': is_null_pointer, 'dt64_dtype':
        np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, xsenc__calgv)
    return xsenc__calgv['bodo_gb_udf_update_local{}'.format(label_suffix)]


def gen_combine_cb(udf_func_struct, allfuncs, n_keys, out_data_typs,
    label_suffix):
    ghtcw__oet = udf_func_struct.var_typs
    jfde__qsc = len(ghtcw__oet)
    dbx__rqc = (
        'def bodo_gb_udf_combine{}(in_table, out_table, row_to_group):\n'.
        format(label_suffix))
    dbx__rqc += '    if is_null_pointer(in_table):\n'
    dbx__rqc += '        return\n'
    dbx__rqc += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in ghtcw__oet]), 
        ',' if len(ghtcw__oet) == 1 else '')
    nftxt__bshaf = n_keys
    dbfv__dzq = n_keys
    repuu__bcsb = []
    tldhx__lelx = []
    for acyd__qmrdz in allfuncs:
        if acyd__qmrdz.ftype != 'udf':
            nftxt__bshaf += acyd__qmrdz.ncols_pre_shuffle
            dbfv__dzq += acyd__qmrdz.ncols_post_shuffle
        else:
            repuu__bcsb += list(range(nftxt__bshaf, nftxt__bshaf +
                acyd__qmrdz.n_redvars))
            tldhx__lelx += list(range(dbfv__dzq + 1, dbfv__dzq + 1 +
                acyd__qmrdz.n_redvars))
            nftxt__bshaf += acyd__qmrdz.n_redvars
            dbfv__dzq += 1 + acyd__qmrdz.n_redvars
    assert len(repuu__bcsb) == jfde__qsc
    dbx__rqc += """
    # initialize redvar cols
"""
    dbx__rqc += '    init_vals = __init_func()\n'
    for yjbeg__kenxj in range(jfde__qsc):
        dbx__rqc += (
            """    redvar_arr_{} = info_to_array(info_from_table(out_table, {}), data_redvar_dummy[{}])
"""
            .format(yjbeg__kenxj, tldhx__lelx[yjbeg__kenxj], yjbeg__kenxj))
        dbx__rqc += '    incref(redvar_arr_{})\n'.format(yjbeg__kenxj)
        dbx__rqc += '    redvar_arr_{}.fill(init_vals[{}])\n'.format(
            yjbeg__kenxj, yjbeg__kenxj)
    dbx__rqc += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'.
        format(yjbeg__kenxj) for yjbeg__kenxj in range(jfde__qsc)]), ',' if
        jfde__qsc == 1 else '')
    dbx__rqc += '\n'
    for yjbeg__kenxj in range(jfde__qsc):
        dbx__rqc += (
            """    recv_redvar_arr_{} = info_to_array(info_from_table(in_table, {}), data_redvar_dummy[{}])
"""
            .format(yjbeg__kenxj, repuu__bcsb[yjbeg__kenxj], yjbeg__kenxj))
        dbx__rqc += '    incref(recv_redvar_arr_{})\n'.format(yjbeg__kenxj)
    dbx__rqc += '    recv_redvars = ({}{})\n'.format(','.join([
        'recv_redvar_arr_{}'.format(yjbeg__kenxj) for yjbeg__kenxj in range
        (jfde__qsc)]), ',' if jfde__qsc == 1 else '')
    dbx__rqc += '\n'
    if jfde__qsc:
        dbx__rqc += '    for i in range(len(recv_redvar_arr_0)):\n'
        dbx__rqc += '        w_ind = row_to_group[i]\n'
        dbx__rqc += (
            '        __combine_redvars(redvars, recv_redvars, w_ind, i, pivot_arr=None)\n'
            )
    xsenc__calgv = {}
    exec(dbx__rqc, {'np': np, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref, '__init_func':
        udf_func_struct.init_func, '__combine_redvars': udf_func_struct.
        combine_all_func, 'is_null_pointer': is_null_pointer, 'dt64_dtype':
        np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, xsenc__calgv)
    return xsenc__calgv['bodo_gb_udf_combine{}'.format(label_suffix)]


def gen_eval_cb(udf_func_struct, allfuncs, n_keys, out_data_typs_, label_suffix
    ):
    ghtcw__oet = udf_func_struct.var_typs
    jfde__qsc = len(ghtcw__oet)
    urg__qhagh = n_keys
    redvar_offsets = []
    hxxic__heahz = []
    out_data_typs = []
    for yjbeg__kenxj, acyd__qmrdz in enumerate(allfuncs):
        if acyd__qmrdz.ftype != 'udf':
            urg__qhagh += acyd__qmrdz.ncols_post_shuffle
        else:
            hxxic__heahz.append(urg__qhagh)
            redvar_offsets += list(range(urg__qhagh + 1, urg__qhagh + 1 +
                acyd__qmrdz.n_redvars))
            urg__qhagh += 1 + acyd__qmrdz.n_redvars
            out_data_typs.append(out_data_typs_[yjbeg__kenxj])
    assert len(redvar_offsets) == jfde__qsc
    hoi__roju = len(out_data_typs)
    dbx__rqc = 'def bodo_gb_udf_eval{}(table):\n'.format(label_suffix)
    dbx__rqc += '    if is_null_pointer(table):\n'
    dbx__rqc += '        return\n'
    dbx__rqc += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in ghtcw__oet]), 
        ',' if len(ghtcw__oet) == 1 else '')
    dbx__rqc += '    out_data_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t.dtype)) for t in
        out_data_typs]), ',' if len(out_data_typs) == 1 else '')
    for yjbeg__kenxj in range(jfde__qsc):
        dbx__rqc += (
            """    redvar_arr_{} = info_to_array(info_from_table(table, {}), data_redvar_dummy[{}])
"""
            .format(yjbeg__kenxj, redvar_offsets[yjbeg__kenxj], yjbeg__kenxj))
        dbx__rqc += '    incref(redvar_arr_{})\n'.format(yjbeg__kenxj)
    dbx__rqc += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'.
        format(yjbeg__kenxj) for yjbeg__kenxj in range(jfde__qsc)]), ',' if
        jfde__qsc == 1 else '')
    dbx__rqc += '\n'
    for yjbeg__kenxj in range(hoi__roju):
        dbx__rqc += (
            """    data_out_{} = info_to_array(info_from_table(table, {}), out_data_dummy[{}])
"""
            .format(yjbeg__kenxj, hxxic__heahz[yjbeg__kenxj], yjbeg__kenxj))
        dbx__rqc += '    incref(data_out_{})\n'.format(yjbeg__kenxj)
    dbx__rqc += '    data_out = ({}{})\n'.format(','.join(['data_out_{}'.
        format(yjbeg__kenxj) for yjbeg__kenxj in range(hoi__roju)]), ',' if
        hoi__roju == 1 else '')
    dbx__rqc += '\n'
    dbx__rqc += '    for i in range(len(data_out_0)):\n'
    dbx__rqc += '        __eval_res(redvars, data_out, i)\n'
    xsenc__calgv = {}
    exec(dbx__rqc, {'np': np, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref, '__eval_res':
        udf_func_struct.eval_all_func, 'is_null_pointer': is_null_pointer,
        'dt64_dtype': np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, xsenc__calgv)
    return xsenc__calgv['bodo_gb_udf_eval{}'.format(label_suffix)]


def gen_general_udf_cb(udf_func_struct, allfuncs, n_keys, in_col_typs,
    out_col_typs, func_idx_to_in_col, label_suffix):
    urg__qhagh = n_keys
    etpwc__pwi = []
    for yjbeg__kenxj, acyd__qmrdz in enumerate(allfuncs):
        if acyd__qmrdz.ftype == 'gen_udf':
            etpwc__pwi.append(urg__qhagh)
            urg__qhagh += 1
        elif acyd__qmrdz.ftype != 'udf':
            urg__qhagh += acyd__qmrdz.ncols_post_shuffle
        else:
            urg__qhagh += acyd__qmrdz.n_redvars + 1
    dbx__rqc = (
        'def bodo_gb_apply_general_udfs{}(num_groups, in_table, out_table):\n'
        .format(label_suffix))
    dbx__rqc += '    if num_groups == 0:\n'
    dbx__rqc += '        return\n'
    for yjbeg__kenxj, func in enumerate(udf_func_struct.general_udf_funcs):
        dbx__rqc += '    # col {}\n'.format(yjbeg__kenxj)
        dbx__rqc += (
            '    out_col = info_to_array(info_from_table(out_table, {}), out_col_{}_typ)\n'
            .format(etpwc__pwi[yjbeg__kenxj], yjbeg__kenxj))
        dbx__rqc += '    incref(out_col)\n'
        dbx__rqc += '    for j in range(num_groups):\n'
        dbx__rqc += (
            """        in_col = info_to_array(info_from_table(in_table, {}*num_groups + j), in_col_{}_typ)
"""
            .format(yjbeg__kenxj, yjbeg__kenxj))
        dbx__rqc += '        incref(in_col)\n'
        dbx__rqc += (
            '        out_col[j] = func_{}(pd.Series(in_col))  # func returns scalar\n'
            .format(yjbeg__kenxj))
    gygcq__hye = {'pd': pd, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref}
    tcjh__mmva = 0
    for yjbeg__kenxj, func in enumerate(allfuncs):
        if func.ftype != 'gen_udf':
            continue
        func = udf_func_struct.general_udf_funcs[tcjh__mmva]
        gygcq__hye['func_{}'.format(tcjh__mmva)] = func
        gygcq__hye['in_col_{}_typ'.format(tcjh__mmva)] = in_col_typs[
            func_idx_to_in_col[yjbeg__kenxj]]
        gygcq__hye['out_col_{}_typ'.format(tcjh__mmva)] = out_col_typs[
            yjbeg__kenxj]
        tcjh__mmva += 1
    xsenc__calgv = {}
    exec(dbx__rqc, gygcq__hye, xsenc__calgv)
    acyd__qmrdz = xsenc__calgv['bodo_gb_apply_general_udfs{}'.format(
        label_suffix)]
    lgvjp__qhdw = types.void(types.int64, types.voidptr, types.voidptr)
    return numba.cfunc(lgvjp__qhdw, nopython=True)(acyd__qmrdz)


def gen_top_level_agg_func(agg_node, in_col_typs, out_col_typs, parallel,
    udf_func_struct):
    pucl__yvry = agg_node.pivot_arr is not None
    if agg_node.same_index:
        assert agg_node.input_has_index
    if agg_node.pivot_values is None:
        bzjyz__cdb = 1
    else:
        bzjyz__cdb = len(agg_node.pivot_values)
    tqg__oqrcs = tuple('key_' + sanitize_varname(lgv__hec) for lgv__hec in
        agg_node.key_names)
    ygt__jcbkk = {lgv__hec: 'in_{}'.format(sanitize_varname(lgv__hec)) for
        lgv__hec in agg_node.gb_info_in.keys() if lgv__hec is not None}
    pagkr__ykzg = {lgv__hec: ('out_' + sanitize_varname(lgv__hec)) for
        lgv__hec in agg_node.gb_info_out.keys()}
    n_keys = len(agg_node.key_names)
    txch__zon = ', '.join(tqg__oqrcs)
    osnjz__uqipq = ', '.join(ygt__jcbkk.values())
    if osnjz__uqipq != '':
        osnjz__uqipq = ', ' + osnjz__uqipq
    dbx__rqc = 'def agg_top({}{}{}, pivot_arr):\n'.format(txch__zon,
        osnjz__uqipq, ', index_arg' if agg_node.input_has_index else '')
    for a in (tqg__oqrcs + tuple(ygt__jcbkk.values())):
        dbx__rqc += f'    {a} = decode_if_dict_array({a})\n'
    if pucl__yvry:
        dbx__rqc += f'    pivot_arr = decode_if_dict_array(pivot_arr)\n'
        yzgd__kiyek = []
        for qwv__gmdvj, vvfjm__rjx in agg_node.gb_info_in.items():
            if qwv__gmdvj is not None:
                for func, mpmbo__hprdo in vvfjm__rjx:
                    yzgd__kiyek.append(ygt__jcbkk[qwv__gmdvj])
    else:
        yzgd__kiyek = tuple(ygt__jcbkk[qwv__gmdvj] for qwv__gmdvj,
            mpmbo__hprdo in agg_node.gb_info_out.values() if qwv__gmdvj is not
            None)
    nec__zaecw = tqg__oqrcs + tuple(yzgd__kiyek)
    dbx__rqc += '    info_list = [{}{}{}]\n'.format(', '.join(
        'array_to_info({})'.format(a) for a in nec__zaecw), 
        ', array_to_info(index_arg)' if agg_node.input_has_index else '', 
        ', array_to_info(pivot_arr)' if agg_node.is_crosstab else '')
    dbx__rqc += '    table = arr_info_list_to_table(info_list)\n'
    for yjbeg__kenxj, lgv__hec in enumerate(agg_node.gb_info_out.keys()):
        onpzr__lloml = pagkr__ykzg[lgv__hec] + '_dummy'
        hrf__mlg = out_col_typs[yjbeg__kenxj]
        qwv__gmdvj, func = agg_node.gb_info_out[lgv__hec]
        if isinstance(func, pytypes.SimpleNamespace) and func.fname in ['min',
            'max', 'shift'] and isinstance(hrf__mlg, bodo.CategoricalArrayType
            ):
            dbx__rqc += '    {} = {}\n'.format(onpzr__lloml, ygt__jcbkk[
                qwv__gmdvj])
        else:
            dbx__rqc += '    {} = {}\n'.format(onpzr__lloml,
                _gen_dummy_alloc(hrf__mlg, yjbeg__kenxj, False))
    do_combine = parallel
    allfuncs = []
    sva__aend = []
    func_idx_to_in_col = []
    dlqlr__fahe = []
    ffew__kvpe = False
    xnr__fkndn = 1
    dcs__ecc = -1
    kqbjb__jwifs = 0
    rfcx__lut = 0
    if not pucl__yvry:
        jnr__zun = [func for mpmbo__hprdo, func in agg_node.gb_info_out.
            values()]
    else:
        jnr__zun = [func for func, mpmbo__hprdo in vvfjm__rjx for
            vvfjm__rjx in agg_node.gb_info_in.values()]
    for foi__xjce, func in enumerate(jnr__zun):
        sva__aend.append(len(allfuncs))
        if func.ftype in {'median', 'nunique'}:
            do_combine = False
        if func.ftype in list_cumulative:
            kqbjb__jwifs += 1
        if hasattr(func, 'skipdropna'):
            ffew__kvpe = func.skipdropna
        if func.ftype == 'shift':
            xnr__fkndn = func.periods
            do_combine = False
        if func.ftype in {'transform'}:
            rfcx__lut = func.transform_func
            do_combine = False
        if func.ftype == 'head':
            dcs__ecc = func.head_n
            do_combine = False
        allfuncs.append(func)
        func_idx_to_in_col.append(foi__xjce)
        if func.ftype == 'udf':
            dlqlr__fahe.append(func.n_redvars)
        elif func.ftype == 'gen_udf':
            dlqlr__fahe.append(0)
            do_combine = False
    sva__aend.append(len(allfuncs))
    if agg_node.is_crosstab:
        assert len(agg_node.gb_info_out
            ) == bzjyz__cdb, 'invalid number of groupby outputs for pivot'
    else:
        assert len(agg_node.gb_info_out) == len(allfuncs
            ) * bzjyz__cdb, 'invalid number of groupby outputs'
    if kqbjb__jwifs > 0:
        if kqbjb__jwifs != len(allfuncs):
            raise BodoError(
                f'{agg_node.func_name}(): Cannot mix cumulative operations with other aggregation functions'
                , loc=agg_node.loc)
        do_combine = False
    if udf_func_struct is not None:
        vfhsf__dyi = next_label()
        if udf_func_struct.regular_udfs:
            lgvjp__qhdw = types.void(types.voidptr, types.voidptr, types.
                CPointer(types.int64))
            arzii__ksvf = numba.cfunc(lgvjp__qhdw, nopython=True)(gen_update_cb
                (udf_func_struct, allfuncs, n_keys, in_col_typs,
                out_col_typs, do_combine, func_idx_to_in_col, vfhsf__dyi))
            dovzv__jadle = numba.cfunc(lgvjp__qhdw, nopython=True)(
                gen_combine_cb(udf_func_struct, allfuncs, n_keys,
                out_col_typs, vfhsf__dyi))
            pby__eyoms = numba.cfunc('void(voidptr)', nopython=True)(
                gen_eval_cb(udf_func_struct, allfuncs, n_keys, out_col_typs,
                vfhsf__dyi))
            udf_func_struct.set_regular_cfuncs(arzii__ksvf, dovzv__jadle,
                pby__eyoms)
            for pxsv__csti in udf_func_struct.regular_udf_cfuncs:
                gb_agg_cfunc[pxsv__csti.native_name] = pxsv__csti
                gb_agg_cfunc_addr[pxsv__csti.native_name] = pxsv__csti.address
        if udf_func_struct.general_udfs:
            lls__jbv = gen_general_udf_cb(udf_func_struct, allfuncs, n_keys,
                in_col_typs, out_col_typs, func_idx_to_in_col, vfhsf__dyi)
            udf_func_struct.set_general_cfunc(lls__jbv)
        azqk__uzelt = []
        jpulo__pzmli = 0
        yjbeg__kenxj = 0
        for onpzr__lloml, acyd__qmrdz in zip(pagkr__ykzg.values(), allfuncs):
            if acyd__qmrdz.ftype in ('udf', 'gen_udf'):
                azqk__uzelt.append(onpzr__lloml + '_dummy')
                for lcj__sgx in range(jpulo__pzmli, jpulo__pzmli +
                    dlqlr__fahe[yjbeg__kenxj]):
                    azqk__uzelt.append('data_redvar_dummy_' + str(lcj__sgx))
                jpulo__pzmli += dlqlr__fahe[yjbeg__kenxj]
                yjbeg__kenxj += 1
        if udf_func_struct.regular_udfs:
            ghtcw__oet = udf_func_struct.var_typs
            for yjbeg__kenxj, t in enumerate(ghtcw__oet):
                dbx__rqc += ('    data_redvar_dummy_{} = np.empty(1, {})\n'
                    .format(yjbeg__kenxj, _get_np_dtype(t)))
        dbx__rqc += '    out_info_list_dummy = [{}]\n'.format(', '.join(
            'array_to_info({})'.format(a) for a in azqk__uzelt))
        dbx__rqc += (
            '    udf_table_dummy = arr_info_list_to_table(out_info_list_dummy)\n'
            )
        if udf_func_struct.regular_udfs:
            dbx__rqc += "    add_agg_cfunc_sym(cpp_cb_update, '{}')\n".format(
                arzii__ksvf.native_name)
            dbx__rqc += "    add_agg_cfunc_sym(cpp_cb_combine, '{}')\n".format(
                dovzv__jadle.native_name)
            dbx__rqc += "    add_agg_cfunc_sym(cpp_cb_eval, '{}')\n".format(
                pby__eyoms.native_name)
            dbx__rqc += ("    cpp_cb_update_addr = get_agg_udf_addr('{}')\n"
                .format(arzii__ksvf.native_name))
            dbx__rqc += ("    cpp_cb_combine_addr = get_agg_udf_addr('{}')\n"
                .format(dovzv__jadle.native_name))
            dbx__rqc += ("    cpp_cb_eval_addr = get_agg_udf_addr('{}')\n".
                format(pby__eyoms.native_name))
        else:
            dbx__rqc += '    cpp_cb_update_addr = 0\n'
            dbx__rqc += '    cpp_cb_combine_addr = 0\n'
            dbx__rqc += '    cpp_cb_eval_addr = 0\n'
        if udf_func_struct.general_udfs:
            pxsv__csti = udf_func_struct.general_udf_cfunc
            gb_agg_cfunc[pxsv__csti.native_name] = pxsv__csti
            gb_agg_cfunc_addr[pxsv__csti.native_name] = pxsv__csti.address
            dbx__rqc += "    add_agg_cfunc_sym(cpp_cb_general, '{}')\n".format(
                pxsv__csti.native_name)
            dbx__rqc += ("    cpp_cb_general_addr = get_agg_udf_addr('{}')\n"
                .format(pxsv__csti.native_name))
        else:
            dbx__rqc += '    cpp_cb_general_addr = 0\n'
    else:
        dbx__rqc += (
            '    udf_table_dummy = arr_info_list_to_table([array_to_info(np.empty(1))])\n'
            )
        dbx__rqc += '    cpp_cb_update_addr = 0\n'
        dbx__rqc += '    cpp_cb_combine_addr = 0\n'
        dbx__rqc += '    cpp_cb_eval_addr = 0\n'
        dbx__rqc += '    cpp_cb_general_addr = 0\n'
    dbx__rqc += '    ftypes = np.array([{}, 0], dtype=np.int32)\n'.format(', '
        .join([str(supported_agg_funcs.index(acyd__qmrdz.ftype)) for
        acyd__qmrdz in allfuncs] + ['0']))
    dbx__rqc += '    func_offsets = np.array({}, dtype=np.int32)\n'.format(str
        (sva__aend))
    if len(dlqlr__fahe) > 0:
        dbx__rqc += '    udf_ncols = np.array({}, dtype=np.int32)\n'.format(str
            (dlqlr__fahe))
    else:
        dbx__rqc += '    udf_ncols = np.array([0], np.int32)\n'
    if pucl__yvry:
        dbx__rqc += '    arr_type = coerce_to_array({})\n'.format(agg_node.
            pivot_values)
        dbx__rqc += '    arr_info = array_to_info(arr_type)\n'
        dbx__rqc += '    dispatch_table = arr_info_list_to_table([arr_info])\n'
        dbx__rqc += '    pivot_info = array_to_info(pivot_arr)\n'
        dbx__rqc += (
            '    dispatch_info = arr_info_list_to_table([pivot_info])\n')
        dbx__rqc += (
            """    out_table = pivot_groupby_and_aggregate(table, {}, dispatch_table, dispatch_info, {}, ftypes.ctypes, func_offsets.ctypes, udf_ncols.ctypes, {}, {}, {}, {}, {}, cpp_cb_update_addr, cpp_cb_combine_addr, cpp_cb_eval_addr, udf_table_dummy)
"""
            .format(n_keys, agg_node.input_has_index, parallel, agg_node.
            is_crosstab, ffew__kvpe, agg_node.return_key, agg_node.same_index))
        dbx__rqc += '    delete_info_decref_array(pivot_info)\n'
        dbx__rqc += '    delete_info_decref_array(arr_info)\n'
    else:
        dbx__rqc += (
            """    out_table = groupby_and_aggregate(table, {}, {}, ftypes.ctypes, func_offsets.ctypes, udf_ncols.ctypes, {}, {}, {}, {}, {}, {}, {}, {}, cpp_cb_update_addr, cpp_cb_combine_addr, cpp_cb_eval_addr, cpp_cb_general_addr, udf_table_dummy)
"""
            .format(n_keys, agg_node.input_has_index, parallel, ffew__kvpe,
            xnr__fkndn, rfcx__lut, dcs__ecc, agg_node.return_key, agg_node.
            same_index, agg_node.dropna))
    eusn__sjd = 0
    if agg_node.return_key:
        for yjbeg__kenxj, xchqh__vxi in enumerate(tqg__oqrcs):
            dbx__rqc += (
                '    {} = info_to_array(info_from_table(out_table, {}), {})\n'
                .format(xchqh__vxi, eusn__sjd, xchqh__vxi))
            eusn__sjd += 1
    for onpzr__lloml in pagkr__ykzg.values():
        dbx__rqc += (
            '    {} = info_to_array(info_from_table(out_table, {}), {})\n'.
            format(onpzr__lloml, eusn__sjd, onpzr__lloml + '_dummy'))
        eusn__sjd += 1
    if agg_node.same_index:
        dbx__rqc += (
            """    out_index_arg = info_to_array(info_from_table(out_table, {}), index_arg)
"""
            .format(eusn__sjd))
        eusn__sjd += 1
    dbx__rqc += (
        f"    ev_clean = bodo.utils.tracing.Event('tables_clean_up', {parallel})\n"
        )
    dbx__rqc += '    delete_table_decref_arrays(table)\n'
    dbx__rqc += '    delete_table_decref_arrays(udf_table_dummy)\n'
    dbx__rqc += '    delete_table(out_table)\n'
    dbx__rqc += f'    ev_clean.finalize()\n'
    jqqk__vhkr = tuple(pagkr__ykzg.values())
    if agg_node.return_key:
        jqqk__vhkr += tuple(tqg__oqrcs)
    dbx__rqc += '    return ({},{})\n'.format(', '.join(jqqk__vhkr), 
        ' out_index_arg,' if agg_node.same_index else '')
    xsenc__calgv = {}
    exec(dbx__rqc, {}, xsenc__calgv)
    itcga__ccx = xsenc__calgv['agg_top']
    return itcga__ccx


def compile_to_optimized_ir(func, arg_typs, typingctx, targetctx):
    code = func.code if hasattr(func, 'code') else func.__code__
    closure = func.closure if hasattr(func, 'closure') else func.__closure__
    f_ir = get_ir_of_code(func.__globals__, code)
    replace_closures(f_ir, closure, code)
    for block in f_ir.blocks.values():
        for qdigq__onto in block.body:
            if is_call_assign(qdigq__onto) and find_callname(f_ir,
                qdigq__onto.value) == ('len', 'builtins'
                ) and qdigq__onto.value.args[0].name == f_ir.arg_names[0]:
                zhs__mhc = get_definition(f_ir, qdigq__onto.value.func)
                zhs__mhc.name = 'dummy_agg_count'
                zhs__mhc.value = dummy_agg_count
    fjr__soq = get_name_var_table(f_ir.blocks)
    vbst__ukmsx = {}
    for name, mpmbo__hprdo in fjr__soq.items():
        vbst__ukmsx[name] = mk_unique_var(name)
    replace_var_names(f_ir.blocks, vbst__ukmsx)
    f_ir._definitions = build_definitions(f_ir.blocks)
    assert f_ir.arg_count == 1, 'agg function should have one input'
    bku__dkr = numba.core.compiler.Flags()
    bku__dkr.nrt = True
    cdq__uywam = bodo.transforms.untyped_pass.UntypedPass(f_ir, typingctx,
        arg_typs, {}, {}, bku__dkr)
    cdq__uywam.run()
    f_ir._definitions = build_definitions(f_ir.blocks)
    typemap, vvl__vorgk, calltypes, mpmbo__hprdo = (numba.core.typed_passes
        .type_inference_stage(typingctx, targetctx, f_ir, arg_typs, None))
    dxvcv__wwnxg = numba.core.cpu.ParallelOptions(True)
    targetctx = numba.core.cpu.CPUContext(typingctx)
    cuedp__zvc = namedtuple('DummyPipeline', ['typingctx', 'targetctx',
        'args', 'func_ir', 'typemap', 'return_type', 'calltypes',
        'type_annotation', 'locals', 'flags', 'pipeline'])
    oyu__iof = namedtuple('TypeAnnotation', ['typemap', 'calltypes'])
    fnfni__dbtw = oyu__iof(typemap, calltypes)
    pm = cuedp__zvc(typingctx, targetctx, None, f_ir, typemap, vvl__vorgk,
        calltypes, fnfni__dbtw, {}, bku__dkr, None)
    jbt__rvdqd = (numba.core.compiler.DefaultPassBuilder.
        define_untyped_pipeline(pm))
    pm = cuedp__zvc(typingctx, targetctx, None, f_ir, typemap, vvl__vorgk,
        calltypes, fnfni__dbtw, {}, bku__dkr, jbt__rvdqd)
    abry__ezfer = numba.core.typed_passes.InlineOverloads()
    abry__ezfer.run_pass(pm)
    qkda__lqb = bodo.transforms.series_pass.SeriesPass(f_ir, typingctx,
        targetctx, typemap, calltypes, {}, False)
    qkda__lqb.run()
    for block in f_ir.blocks.values():
        for qdigq__onto in block.body:
            if is_assign(qdigq__onto) and isinstance(qdigq__onto.value, (ir
                .Arg, ir.Var)) and isinstance(typemap[qdigq__onto.target.
                name], SeriesType):
                kwdo__lvpmt = typemap.pop(qdigq__onto.target.name)
                typemap[qdigq__onto.target.name] = kwdo__lvpmt.data
            if is_call_assign(qdigq__onto) and find_callname(f_ir,
                qdigq__onto.value) == ('get_series_data',
                'bodo.hiframes.pd_series_ext'):
                f_ir._definitions[qdigq__onto.target.name].remove(qdigq__onto
                    .value)
                qdigq__onto.value = qdigq__onto.value.args[0]
                f_ir._definitions[qdigq__onto.target.name].append(qdigq__onto
                    .value)
            if is_call_assign(qdigq__onto) and find_callname(f_ir,
                qdigq__onto.value) == ('isna', 'bodo.libs.array_kernels'):
                f_ir._definitions[qdigq__onto.target.name].remove(qdigq__onto
                    .value)
                qdigq__onto.value = ir.Const(False, qdigq__onto.loc)
                f_ir._definitions[qdigq__onto.target.name].append(qdigq__onto
                    .value)
            if is_call_assign(qdigq__onto) and find_callname(f_ir,
                qdigq__onto.value) == ('setna', 'bodo.libs.array_kernels'):
                f_ir._definitions[qdigq__onto.target.name].remove(qdigq__onto
                    .value)
                qdigq__onto.value = ir.Const(False, qdigq__onto.loc)
                f_ir._definitions[qdigq__onto.target.name].append(qdigq__onto
                    .value)
    bodo.transforms.untyped_pass.remove_dead_branches(f_ir)
    xzj__qijx = numba.parfors.parfor.PreParforPass(f_ir, typemap, calltypes,
        typingctx, targetctx, dxvcv__wwnxg)
    xzj__qijx.run()
    f_ir._definitions = build_definitions(f_ir.blocks)
    dho__lxfkb = numba.core.compiler.StateDict()
    dho__lxfkb.func_ir = f_ir
    dho__lxfkb.typemap = typemap
    dho__lxfkb.calltypes = calltypes
    dho__lxfkb.typingctx = typingctx
    dho__lxfkb.targetctx = targetctx
    dho__lxfkb.return_type = vvl__vorgk
    numba.core.rewrites.rewrite_registry.apply('after-inference', dho__lxfkb)
    hcdpe__afzu = numba.parfors.parfor.ParforPass(f_ir, typemap, calltypes,
        vvl__vorgk, typingctx, targetctx, dxvcv__wwnxg, bku__dkr, {})
    hcdpe__afzu.run()
    remove_dels(f_ir.blocks)
    numba.parfors.parfor.maximize_fusion(f_ir, f_ir.blocks, typemap, False)
    return f_ir, pm


def replace_closures(f_ir, closure, code):
    if closure:
        closure = f_ir.get_definition(closure)
        if isinstance(closure, tuple):
            omizz__wfzj = ctypes.pythonapi.PyCell_Get
            omizz__wfzj.restype = ctypes.py_object
            omizz__wfzj.argtypes = ctypes.py_object,
            ackb__rgldl = tuple(omizz__wfzj(zwc__hxyuv) for zwc__hxyuv in
                closure)
        else:
            assert isinstance(closure, ir.Expr) and closure.op == 'build_tuple'
            ackb__rgldl = closure.items
        assert len(code.co_freevars) == len(ackb__rgldl)
        numba.core.inline_closurecall._replace_freevars(f_ir.blocks,
            ackb__rgldl)


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
        ntiis__oogqy = SeriesType(in_col_typ.dtype, in_col_typ, None,
            string_type)
        f_ir, pm = compile_to_optimized_ir(func, (ntiis__oogqy,), self.
            typingctx, self.targetctx)
        f_ir._definitions = build_definitions(f_ir.blocks)
        assert len(f_ir.blocks
            ) == 1 and 0 in f_ir.blocks, 'only simple functions with one block supported for aggregation'
        block = f_ir.blocks[0]
        epmi__tzo, arr_var = _rm_arg_agg_block(block, pm.typemap)
        qukgo__jlhu = -1
        for yjbeg__kenxj, qdigq__onto in enumerate(epmi__tzo):
            if isinstance(qdigq__onto, numba.parfors.parfor.Parfor):
                assert qukgo__jlhu == -1, 'only one parfor for aggregation function'
                qukgo__jlhu = yjbeg__kenxj
        parfor = None
        if qukgo__jlhu != -1:
            parfor = epmi__tzo[qukgo__jlhu]
            remove_dels(parfor.loop_body)
            remove_dels({(0): parfor.init_block})
        init_nodes = []
        if parfor:
            init_nodes = epmi__tzo[:qukgo__jlhu] + parfor.init_block.body
        eval_nodes = epmi__tzo[qukgo__jlhu + 1:]
        redvars = []
        var_to_redvar = {}
        if parfor:
            redvars, var_to_redvar = get_parfor_reductions(parfor, parfor.
                params, pm.calltypes)
        func.ncols_pre_shuffle = len(redvars)
        func.ncols_post_shuffle = len(redvars) + 1
        func.n_redvars = len(redvars)
        reduce_vars = [0] * len(redvars)
        for qdigq__onto in init_nodes:
            if is_assign(qdigq__onto) and qdigq__onto.target.name in redvars:
                ind = redvars.index(qdigq__onto.target.name)
                reduce_vars[ind] = qdigq__onto.target
        var_types = [pm.typemap[adf__zmte] for adf__zmte in redvars]
        qwla__qub = gen_combine_func(f_ir, parfor, redvars, var_to_redvar,
            var_types, arr_var, pm, self.typingctx, self.targetctx)
        init_nodes = _mv_read_only_init_vars(init_nodes, parfor, eval_nodes)
        tmsr__txty = gen_update_func(parfor, redvars, var_to_redvar,
            var_types, arr_var, in_col_typ, pm, self.typingctx, self.targetctx)
        glmrk__agf = gen_eval_func(f_ir, eval_nodes, reduce_vars, var_types,
            pm, self.typingctx, self.targetctx)
        self.all_reduce_vars += reduce_vars
        self.all_vartypes += var_types
        self.all_init_nodes += init_nodes
        self.all_eval_funcs.append(glmrk__agf)
        self.all_update_funcs.append(tmsr__txty)
        self.all_combine_funcs.append(qwla__qub)
        self.curr_offset += len(redvars)
        self.redvar_offsets.append(self.curr_offset)

    def gen_all_func(self):
        if len(self.all_update_funcs) == 0:
            return None
        self.all_vartypes = self.all_vartypes * len(self.pivot_values
            ) if self.pivot_values is not None else self.all_vartypes
        self.all_reduce_vars = self.all_reduce_vars * len(self.pivot_values
            ) if self.pivot_values is not None else self.all_reduce_vars
        eswdd__bapqf = gen_init_func(self.all_init_nodes, self.
            all_reduce_vars, self.all_vartypes, self.typingctx, self.targetctx)
        lwekm__ptkil = gen_all_update_func(self.all_update_funcs, self.
            all_vartypes, self.in_col_types, self.redvar_offsets, self.
            typingctx, self.targetctx, self.pivot_typ, self.pivot_values,
            self.is_crosstab)
        dbv__uew = gen_all_combine_func(self.all_combine_funcs, self.
            all_vartypes, self.redvar_offsets, self.typingctx, self.
            targetctx, self.pivot_typ, self.pivot_values)
        xty__rpwv = gen_all_eval_func(self.all_eval_funcs, self.
            all_vartypes, self.redvar_offsets, self.out_col_types, self.
            typingctx, self.targetctx, self.pivot_values)
        return (self.all_vartypes, eswdd__bapqf, lwekm__ptkil, dbv__uew,
            xty__rpwv)


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
    ndn__vlik = []
    for t, acyd__qmrdz in zip(in_col_types, agg_func):
        ndn__vlik.append((t, acyd__qmrdz))
    tlf__ytkvg = RegularUDFGenerator(in_col_types, out_col_types, pivot_typ,
        pivot_values, is_crosstab, typingctx, targetctx)
    ntdvu__vbif = GeneralUDFGenerator()
    for in_col_typ, func in ndn__vlik:
        if func.ftype not in ('udf', 'gen_udf'):
            continue
        try:
            tlf__ytkvg.add_udf(in_col_typ, func)
        except:
            ntdvu__vbif.add_udf(func)
            func.ftype = 'gen_udf'
    regular_udf_funcs = tlf__ytkvg.gen_all_func()
    general_udf_funcs = ntdvu__vbif.gen_all_func()
    if regular_udf_funcs is not None or general_udf_funcs is not None:
        return AggUDFStruct(regular_udf_funcs, general_udf_funcs)
    else:
        return None


def _mv_read_only_init_vars(init_nodes, parfor, eval_nodes):
    if not parfor:
        return init_nodes
    tshh__subgs = compute_use_defs(parfor.loop_body)
    nefa__lkevy = set()
    for kdnl__lfiup in tshh__subgs.usemap.values():
        nefa__lkevy |= kdnl__lfiup
    kfrb__dgri = set()
    for kdnl__lfiup in tshh__subgs.defmap.values():
        kfrb__dgri |= kdnl__lfiup
    vnhb__peta = ir.Block(ir.Scope(None, parfor.loc), parfor.loc)
    vnhb__peta.body = eval_nodes
    pbyt__skaih = compute_use_defs({(0): vnhb__peta})
    cyejy__jdgq = pbyt__skaih.usemap[0]
    bbk__fslx = set()
    rofw__tpnwj = []
    pjdc__zbfo = []
    for qdigq__onto in reversed(init_nodes):
        lrzg__kao = {adf__zmte.name for adf__zmte in qdigq__onto.list_vars()}
        if is_assign(qdigq__onto):
            adf__zmte = qdigq__onto.target.name
            lrzg__kao.remove(adf__zmte)
            if (adf__zmte in nefa__lkevy and adf__zmte not in bbk__fslx and
                adf__zmte not in cyejy__jdgq and adf__zmte not in kfrb__dgri):
                pjdc__zbfo.append(qdigq__onto)
                nefa__lkevy |= lrzg__kao
                kfrb__dgri.add(adf__zmte)
                continue
        bbk__fslx |= lrzg__kao
        rofw__tpnwj.append(qdigq__onto)
    pjdc__zbfo.reverse()
    rofw__tpnwj.reverse()
    ieab__ziys = min(parfor.loop_body.keys())
    rqng__jtih = parfor.loop_body[ieab__ziys]
    rqng__jtih.body = pjdc__zbfo + rqng__jtih.body
    return rofw__tpnwj


def gen_init_func(init_nodes, reduce_vars, var_types, typingctx, targetctx):
    welu__jdg = (numba.parfors.parfor.max_checker, numba.parfors.parfor.
        min_checker, numba.parfors.parfor.argmax_checker, numba.parfors.
        parfor.argmin_checker)
    hhuou__jtj = set()
    amo__nwwu = []
    for qdigq__onto in init_nodes:
        if is_assign(qdigq__onto) and isinstance(qdigq__onto.value, ir.Global
            ) and isinstance(qdigq__onto.value.value, pytypes.FunctionType
            ) and qdigq__onto.value.value in welu__jdg:
            hhuou__jtj.add(qdigq__onto.target.name)
        elif is_call_assign(qdigq__onto
            ) and qdigq__onto.value.func.name in hhuou__jtj:
            pass
        else:
            amo__nwwu.append(qdigq__onto)
    init_nodes = amo__nwwu
    ddjpr__ojcz = types.Tuple(var_types)
    tnr__sxuz = lambda : None
    f_ir = compile_to_numba_ir(tnr__sxuz, {})
    block = list(f_ir.blocks.values())[0]
    loc = block.loc
    nsohx__mete = ir.Var(block.scope, mk_unique_var('init_tup'), loc)
    fdrbq__tfejh = ir.Assign(ir.Expr.build_tuple(reduce_vars, loc),
        nsohx__mete, loc)
    block.body = block.body[-2:]
    block.body = init_nodes + [fdrbq__tfejh] + block.body
    block.body[-2].value.value = nsohx__mete
    lpxg__fyyzn = compiler.compile_ir(typingctx, targetctx, f_ir, (),
        ddjpr__ojcz, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    wxeg__gglkb = numba.core.target_extension.dispatcher_registry[cpu_target](
        tnr__sxuz)
    wxeg__gglkb.add_overload(lpxg__fyyzn)
    return wxeg__gglkb


def gen_all_update_func(update_funcs, reduce_var_types, in_col_types,
    redvar_offsets, typingctx, targetctx, pivot_typ, pivot_values, is_crosstab
    ):
    gqbpt__chuut = len(update_funcs)
    oer__qnthc = len(in_col_types)
    if pivot_values is not None:
        assert oer__qnthc == 1
    dbx__rqc = 'def update_all_f(redvar_arrs, data_in, w_ind, i, pivot_arr):\n'
    if pivot_values is not None:
        ahl__azlb = redvar_offsets[oer__qnthc]
        dbx__rqc += '  pv = pivot_arr[i]\n'
        for lcj__sgx, sax__qqe in enumerate(pivot_values):
            uxy__ndymu = 'el' if lcj__sgx != 0 else ''
            dbx__rqc += "  {}if pv == '{}':\n".format(uxy__ndymu, sax__qqe)
            mji__bhw = ahl__azlb * lcj__sgx
            wjri__fxxgh = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                yjbeg__kenxj) for yjbeg__kenxj in range(mji__bhw +
                redvar_offsets[0], mji__bhw + redvar_offsets[1])])
            beg__plare = 'data_in[0][i]'
            if is_crosstab:
                beg__plare = '0'
            dbx__rqc += '    {} = update_vars_0({}, {})\n'.format(wjri__fxxgh,
                wjri__fxxgh, beg__plare)
    else:
        for lcj__sgx in range(gqbpt__chuut):
            wjri__fxxgh = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                yjbeg__kenxj) for yjbeg__kenxj in range(redvar_offsets[
                lcj__sgx], redvar_offsets[lcj__sgx + 1])])
            if wjri__fxxgh:
                dbx__rqc += ('  {} = update_vars_{}({},  data_in[{}][i])\n'
                    .format(wjri__fxxgh, lcj__sgx, wjri__fxxgh, 0 if 
                    oer__qnthc == 1 else lcj__sgx))
    dbx__rqc += '  return\n'
    gygcq__hye = {}
    for yjbeg__kenxj, acyd__qmrdz in enumerate(update_funcs):
        gygcq__hye['update_vars_{}'.format(yjbeg__kenxj)] = acyd__qmrdz
    xsenc__calgv = {}
    exec(dbx__rqc, gygcq__hye, xsenc__calgv)
    addgc__vcsdp = xsenc__calgv['update_all_f']
    return numba.njit(no_cpython_wrapper=True)(addgc__vcsdp)


def gen_all_combine_func(combine_funcs, reduce_var_types, redvar_offsets,
    typingctx, targetctx, pivot_typ, pivot_values):
    hlrd__jqn = types.Tuple([types.Array(t, 1, 'C') for t in reduce_var_types])
    arg_typs = hlrd__jqn, hlrd__jqn, types.intp, types.intp, pivot_typ
    mkqcp__nymto = len(redvar_offsets) - 1
    ahl__azlb = redvar_offsets[mkqcp__nymto]
    dbx__rqc = (
        'def combine_all_f(redvar_arrs, recv_arrs, w_ind, i, pivot_arr):\n')
    if pivot_values is not None:
        assert mkqcp__nymto == 1
        for kvbkx__taz in range(len(pivot_values)):
            mji__bhw = ahl__azlb * kvbkx__taz
            wjri__fxxgh = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                yjbeg__kenxj) for yjbeg__kenxj in range(mji__bhw +
                redvar_offsets[0], mji__bhw + redvar_offsets[1])])
            pza__qolit = ', '.join(['recv_arrs[{}][i]'.format(yjbeg__kenxj) for
                yjbeg__kenxj in range(mji__bhw + redvar_offsets[0], 
                mji__bhw + redvar_offsets[1])])
            dbx__rqc += '  {} = combine_vars_0({}, {})\n'.format(wjri__fxxgh,
                wjri__fxxgh, pza__qolit)
    else:
        for lcj__sgx in range(mkqcp__nymto):
            wjri__fxxgh = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                yjbeg__kenxj) for yjbeg__kenxj in range(redvar_offsets[
                lcj__sgx], redvar_offsets[lcj__sgx + 1])])
            pza__qolit = ', '.join(['recv_arrs[{}][i]'.format(yjbeg__kenxj) for
                yjbeg__kenxj in range(redvar_offsets[lcj__sgx],
                redvar_offsets[lcj__sgx + 1])])
            if pza__qolit:
                dbx__rqc += '  {} = combine_vars_{}({}, {})\n'.format(
                    wjri__fxxgh, lcj__sgx, wjri__fxxgh, pza__qolit)
    dbx__rqc += '  return\n'
    gygcq__hye = {}
    for yjbeg__kenxj, acyd__qmrdz in enumerate(combine_funcs):
        gygcq__hye['combine_vars_{}'.format(yjbeg__kenxj)] = acyd__qmrdz
    xsenc__calgv = {}
    exec(dbx__rqc, gygcq__hye, xsenc__calgv)
    tcz__swszs = xsenc__calgv['combine_all_f']
    f_ir = compile_to_numba_ir(tcz__swszs, gygcq__hye)
    dbv__uew = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        types.none, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    wxeg__gglkb = numba.core.target_extension.dispatcher_registry[cpu_target](
        tcz__swszs)
    wxeg__gglkb.add_overload(dbv__uew)
    return wxeg__gglkb


def gen_all_eval_func(eval_funcs, reduce_var_types, redvar_offsets,
    out_col_typs, typingctx, targetctx, pivot_values):
    hlrd__jqn = types.Tuple([types.Array(t, 1, 'C') for t in reduce_var_types])
    out_col_typs = types.Tuple(out_col_typs)
    mkqcp__nymto = len(redvar_offsets) - 1
    ahl__azlb = redvar_offsets[mkqcp__nymto]
    dbx__rqc = 'def eval_all_f(redvar_arrs, out_arrs, j):\n'
    if pivot_values is not None:
        assert mkqcp__nymto == 1
        for lcj__sgx in range(len(pivot_values)):
            mji__bhw = ahl__azlb * lcj__sgx
            wjri__fxxgh = ', '.join(['redvar_arrs[{}][j]'.format(
                yjbeg__kenxj) for yjbeg__kenxj in range(mji__bhw +
                redvar_offsets[0], mji__bhw + redvar_offsets[1])])
            dbx__rqc += '  out_arrs[{}][j] = eval_vars_0({})\n'.format(lcj__sgx
                , wjri__fxxgh)
    else:
        for lcj__sgx in range(mkqcp__nymto):
            wjri__fxxgh = ', '.join(['redvar_arrs[{}][j]'.format(
                yjbeg__kenxj) for yjbeg__kenxj in range(redvar_offsets[
                lcj__sgx], redvar_offsets[lcj__sgx + 1])])
            dbx__rqc += '  out_arrs[{}][j] = eval_vars_{}({})\n'.format(
                lcj__sgx, lcj__sgx, wjri__fxxgh)
    dbx__rqc += '  return\n'
    gygcq__hye = {}
    for yjbeg__kenxj, acyd__qmrdz in enumerate(eval_funcs):
        gygcq__hye['eval_vars_{}'.format(yjbeg__kenxj)] = acyd__qmrdz
    xsenc__calgv = {}
    exec(dbx__rqc, gygcq__hye, xsenc__calgv)
    lay__vrafx = xsenc__calgv['eval_all_f']
    return numba.njit(no_cpython_wrapper=True)(lay__vrafx)


def gen_eval_func(f_ir, eval_nodes, reduce_vars, var_types, pm, typingctx,
    targetctx):
    rntbk__xyoh = len(var_types)
    shyh__ueff = [f'in{yjbeg__kenxj}' for yjbeg__kenxj in range(rntbk__xyoh)]
    ddjpr__ojcz = types.unliteral(pm.typemap[eval_nodes[-1].value.name])
    mmlhm__glqkj = ddjpr__ojcz(0)
    dbx__rqc = 'def agg_eval({}):\n return _zero\n'.format(', '.join(
        shyh__ueff))
    xsenc__calgv = {}
    exec(dbx__rqc, {'_zero': mmlhm__glqkj}, xsenc__calgv)
    tsgtt__lwxn = xsenc__calgv['agg_eval']
    arg_typs = tuple(var_types)
    f_ir = compile_to_numba_ir(tsgtt__lwxn, {'numba': numba, 'bodo': bodo,
        'np': np, '_zero': mmlhm__glqkj}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=arg_typs, typemap=pm.typemap, calltypes=pm.
        calltypes)
    block = list(f_ir.blocks.values())[0]
    ptmbt__vjvnh = []
    for yjbeg__kenxj, adf__zmte in enumerate(reduce_vars):
        ptmbt__vjvnh.append(ir.Assign(block.body[yjbeg__kenxj].target,
            adf__zmte, adf__zmte.loc))
        for qbu__ikkic in adf__zmte.versioned_names:
            ptmbt__vjvnh.append(ir.Assign(adf__zmte, ir.Var(adf__zmte.scope,
                qbu__ikkic, adf__zmte.loc), adf__zmte.loc))
    block.body = block.body[:rntbk__xyoh] + ptmbt__vjvnh + eval_nodes
    glmrk__agf = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        ddjpr__ojcz, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    wxeg__gglkb = numba.core.target_extension.dispatcher_registry[cpu_target](
        tsgtt__lwxn)
    wxeg__gglkb.add_overload(glmrk__agf)
    return wxeg__gglkb


def gen_combine_func(f_ir, parfor, redvars, var_to_redvar, var_types,
    arr_var, pm, typingctx, targetctx):
    if not parfor:
        return numba.njit(lambda : ())
    rntbk__xyoh = len(redvars)
    myw__edei = [f'v{yjbeg__kenxj}' for yjbeg__kenxj in range(rntbk__xyoh)]
    shyh__ueff = [f'in{yjbeg__kenxj}' for yjbeg__kenxj in range(rntbk__xyoh)]
    dbx__rqc = 'def agg_combine({}):\n'.format(', '.join(myw__edei +
        shyh__ueff))
    xnpqk__dbfkh = wrap_parfor_blocks(parfor)
    maf__gooiu = find_topo_order(xnpqk__dbfkh)
    maf__gooiu = maf__gooiu[1:]
    unwrap_parfor_blocks(parfor)
    navot__mevm = {}
    tobia__tinuz = []
    for tae__knkg in maf__gooiu:
        enk__kvfeq = parfor.loop_body[tae__knkg]
        for qdigq__onto in enk__kvfeq.body:
            if is_call_assign(qdigq__onto) and guard(find_callname, f_ir,
                qdigq__onto.value) == ('__special_combine', 'bodo.ir.aggregate'
                ):
                args = qdigq__onto.value.args
                lsc__ynple = []
                heu__giev = []
                for adf__zmte in args[:-1]:
                    ind = redvars.index(adf__zmte.name)
                    tobia__tinuz.append(ind)
                    lsc__ynple.append('v{}'.format(ind))
                    heu__giev.append('in{}'.format(ind))
                pzmh__vuyv = '__special_combine__{}'.format(len(navot__mevm))
                dbx__rqc += '    ({},) = {}({})\n'.format(', '.join(
                    lsc__ynple), pzmh__vuyv, ', '.join(lsc__ynple + heu__giev))
                bxmm__maet = ir.Expr.call(args[-1], [], (), enk__kvfeq.loc)
                hyb__tdm = guard(find_callname, f_ir, bxmm__maet)
                assert hyb__tdm == ('_var_combine', 'bodo.ir.aggregate')
                hyb__tdm = bodo.ir.aggregate._var_combine
                navot__mevm[pzmh__vuyv] = hyb__tdm
            if is_assign(qdigq__onto) and qdigq__onto.target.name in redvars:
                pkxp__neeb = qdigq__onto.target.name
                ind = redvars.index(pkxp__neeb)
                if ind in tobia__tinuz:
                    continue
                if len(f_ir._definitions[pkxp__neeb]) == 2:
                    var_def = f_ir._definitions[pkxp__neeb][0]
                    dbx__rqc += _match_reduce_def(var_def, f_ir, ind)
                    var_def = f_ir._definitions[pkxp__neeb][1]
                    dbx__rqc += _match_reduce_def(var_def, f_ir, ind)
    dbx__rqc += '    return {}'.format(', '.join(['v{}'.format(yjbeg__kenxj
        ) for yjbeg__kenxj in range(rntbk__xyoh)]))
    xsenc__calgv = {}
    exec(dbx__rqc, {}, xsenc__calgv)
    ooo__suy = xsenc__calgv['agg_combine']
    arg_typs = tuple(2 * var_types)
    gygcq__hye = {'numba': numba, 'bodo': bodo, 'np': np}
    gygcq__hye.update(navot__mevm)
    f_ir = compile_to_numba_ir(ooo__suy, gygcq__hye, typingctx=typingctx,
        targetctx=targetctx, arg_typs=arg_typs, typemap=pm.typemap,
        calltypes=pm.calltypes)
    block = list(f_ir.blocks.values())[0]
    ddjpr__ojcz = pm.typemap[block.body[-1].value.name]
    qwla__qub = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        ddjpr__ojcz, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    wxeg__gglkb = numba.core.target_extension.dispatcher_registry[cpu_target](
        ooo__suy)
    wxeg__gglkb.add_overload(qwla__qub)
    return wxeg__gglkb


def _match_reduce_def(var_def, f_ir, ind):
    dbx__rqc = ''
    while isinstance(var_def, ir.Var):
        var_def = guard(get_definition, f_ir, var_def)
    if isinstance(var_def, ir.Expr
        ) and var_def.op == 'inplace_binop' and var_def.fn in ('+=',
        operator.iadd):
        dbx__rqc = '    v{} += in{}\n'.format(ind, ind)
    if isinstance(var_def, ir.Expr) and var_def.op == 'call':
        scpy__qhs = guard(find_callname, f_ir, var_def)
        if scpy__qhs == ('min', 'builtins'):
            dbx__rqc = '    v{} = min(v{}, in{})\n'.format(ind, ind, ind)
        if scpy__qhs == ('max', 'builtins'):
            dbx__rqc = '    v{} = max(v{}, in{})\n'.format(ind, ind, ind)
    return dbx__rqc


def gen_update_func(parfor, redvars, var_to_redvar, var_types, arr_var,
    in_col_typ, pm, typingctx, targetctx):
    if not parfor:
        return numba.njit(lambda A: ())
    rntbk__xyoh = len(redvars)
    zbhs__amces = 1
    bmpz__eeq = []
    for yjbeg__kenxj in range(zbhs__amces):
        bfdo__dyn = ir.Var(arr_var.scope, f'$input{yjbeg__kenxj}', arr_var.loc)
        bmpz__eeq.append(bfdo__dyn)
    azcij__zbvf = parfor.loop_nests[0].index_variable
    julo__err = [0] * rntbk__xyoh
    for enk__kvfeq in parfor.loop_body.values():
        xnk__tysx = []
        for qdigq__onto in enk__kvfeq.body:
            if is_var_assign(qdigq__onto
                ) and qdigq__onto.value.name == azcij__zbvf.name:
                continue
            if is_getitem(qdigq__onto
                ) and qdigq__onto.value.value.name == arr_var.name:
                qdigq__onto.value = bmpz__eeq[0]
            if is_call_assign(qdigq__onto) and guard(find_callname, pm.
                func_ir, qdigq__onto.value) == ('isna',
                'bodo.libs.array_kernels') and qdigq__onto.value.args[0
                ].name == arr_var.name:
                qdigq__onto.value = ir.Const(False, qdigq__onto.target.loc)
            if is_assign(qdigq__onto) and qdigq__onto.target.name in redvars:
                ind = redvars.index(qdigq__onto.target.name)
                julo__err[ind] = qdigq__onto.target
            xnk__tysx.append(qdigq__onto)
        enk__kvfeq.body = xnk__tysx
    myw__edei = ['v{}'.format(yjbeg__kenxj) for yjbeg__kenxj in range(
        rntbk__xyoh)]
    shyh__ueff = ['in{}'.format(yjbeg__kenxj) for yjbeg__kenxj in range(
        zbhs__amces)]
    dbx__rqc = 'def agg_update({}):\n'.format(', '.join(myw__edei + shyh__ueff)
        )
    dbx__rqc += '    __update_redvars()\n'
    dbx__rqc += '    return {}'.format(', '.join(['v{}'.format(yjbeg__kenxj
        ) for yjbeg__kenxj in range(rntbk__xyoh)]))
    xsenc__calgv = {}
    exec(dbx__rqc, {}, xsenc__calgv)
    xehcu__rhlmo = xsenc__calgv['agg_update']
    arg_typs = tuple(var_types + [in_col_typ.dtype] * zbhs__amces)
    f_ir = compile_to_numba_ir(xehcu__rhlmo, {'__update_redvars':
        __update_redvars}, typingctx=typingctx, targetctx=targetctx,
        arg_typs=arg_typs, typemap=pm.typemap, calltypes=pm.calltypes)
    f_ir._definitions = build_definitions(f_ir.blocks)
    pfdw__fyq = f_ir.blocks.popitem()[1].body
    ddjpr__ojcz = pm.typemap[pfdw__fyq[-1].value.name]
    xnpqk__dbfkh = wrap_parfor_blocks(parfor)
    maf__gooiu = find_topo_order(xnpqk__dbfkh)
    maf__gooiu = maf__gooiu[1:]
    unwrap_parfor_blocks(parfor)
    f_ir.blocks = parfor.loop_body
    rqng__jtih = f_ir.blocks[maf__gooiu[0]]
    vsdo__mndg = f_ir.blocks[maf__gooiu[-1]]
    xjra__mdqt = pfdw__fyq[:rntbk__xyoh + zbhs__amces]
    if rntbk__xyoh > 1:
        ajy__jmdxc = pfdw__fyq[-3:]
        assert is_assign(ajy__jmdxc[0]) and isinstance(ajy__jmdxc[0].value,
            ir.Expr) and ajy__jmdxc[0].value.op == 'build_tuple'
    else:
        ajy__jmdxc = pfdw__fyq[-2:]
    for yjbeg__kenxj in range(rntbk__xyoh):
        eoi__yjxqs = pfdw__fyq[yjbeg__kenxj].target
        txtrs__ekqg = ir.Assign(eoi__yjxqs, julo__err[yjbeg__kenxj],
            eoi__yjxqs.loc)
        xjra__mdqt.append(txtrs__ekqg)
    for yjbeg__kenxj in range(rntbk__xyoh, rntbk__xyoh + zbhs__amces):
        eoi__yjxqs = pfdw__fyq[yjbeg__kenxj].target
        txtrs__ekqg = ir.Assign(eoi__yjxqs, bmpz__eeq[yjbeg__kenxj -
            rntbk__xyoh], eoi__yjxqs.loc)
        xjra__mdqt.append(txtrs__ekqg)
    rqng__jtih.body = xjra__mdqt + rqng__jtih.body
    ygier__zkmi = []
    for yjbeg__kenxj in range(rntbk__xyoh):
        eoi__yjxqs = pfdw__fyq[yjbeg__kenxj].target
        txtrs__ekqg = ir.Assign(julo__err[yjbeg__kenxj], eoi__yjxqs,
            eoi__yjxqs.loc)
        ygier__zkmi.append(txtrs__ekqg)
    vsdo__mndg.body += ygier__zkmi + ajy__jmdxc
    byc__ufxi = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        ddjpr__ojcz, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    wxeg__gglkb = numba.core.target_extension.dispatcher_registry[cpu_target](
        xehcu__rhlmo)
    wxeg__gglkb.add_overload(byc__ufxi)
    return wxeg__gglkb


def _rm_arg_agg_block(block, typemap):
    epmi__tzo = []
    arr_var = None
    for yjbeg__kenxj, qdigq__onto in enumerate(block.body):
        if is_assign(qdigq__onto) and isinstance(qdigq__onto.value, ir.Arg):
            arr_var = qdigq__onto.target
            njmtr__hibxa = typemap[arr_var.name]
            if not isinstance(njmtr__hibxa, types.ArrayCompatible):
                epmi__tzo += block.body[yjbeg__kenxj + 1:]
                break
            pninn__moe = block.body[yjbeg__kenxj + 1]
            assert is_assign(pninn__moe) and isinstance(pninn__moe.value,
                ir.Expr
                ) and pninn__moe.value.op == 'getattr' and pninn__moe.value.attr == 'shape' and pninn__moe.value.value.name == arr_var.name
            szzvy__fxvl = pninn__moe.target
            smm__mugvh = block.body[yjbeg__kenxj + 2]
            assert is_assign(smm__mugvh) and isinstance(smm__mugvh.value,
                ir.Expr
                ) and smm__mugvh.value.op == 'static_getitem' and smm__mugvh.value.value.name == szzvy__fxvl.name
            epmi__tzo += block.body[yjbeg__kenxj + 3:]
            break
        epmi__tzo.append(qdigq__onto)
    return epmi__tzo, arr_var


def get_parfor_reductions(parfor, parfor_params, calltypes, reduce_varnames
    =None, param_uses=None, var_to_param=None):
    if reduce_varnames is None:
        reduce_varnames = []
    if param_uses is None:
        param_uses = defaultdict(list)
    if var_to_param is None:
        var_to_param = {}
    xnpqk__dbfkh = wrap_parfor_blocks(parfor)
    maf__gooiu = find_topo_order(xnpqk__dbfkh)
    maf__gooiu = maf__gooiu[1:]
    unwrap_parfor_blocks(parfor)
    for tae__knkg in reversed(maf__gooiu):
        for qdigq__onto in reversed(parfor.loop_body[tae__knkg].body):
            if isinstance(qdigq__onto, ir.Assign) and (qdigq__onto.target.
                name in parfor_params or qdigq__onto.target.name in
                var_to_param):
                ndx__hpkn = qdigq__onto.target.name
                rhs = qdigq__onto.value
                ygkys__qycr = (ndx__hpkn if ndx__hpkn in parfor_params else
                    var_to_param[ndx__hpkn])
                mwtg__fiuly = []
                if isinstance(rhs, ir.Var):
                    mwtg__fiuly = [rhs.name]
                elif isinstance(rhs, ir.Expr):
                    mwtg__fiuly = [adf__zmte.name for adf__zmte in
                        qdigq__onto.value.list_vars()]
                param_uses[ygkys__qycr].extend(mwtg__fiuly)
                for adf__zmte in mwtg__fiuly:
                    var_to_param[adf__zmte] = ygkys__qycr
            if isinstance(qdigq__onto, Parfor):
                get_parfor_reductions(qdigq__onto, parfor_params, calltypes,
                    reduce_varnames, param_uses, var_to_param)
    for zhhgb__sfabq, mwtg__fiuly in param_uses.items():
        if zhhgb__sfabq in mwtg__fiuly and zhhgb__sfabq not in reduce_varnames:
            reduce_varnames.append(zhhgb__sfabq)
    return reduce_varnames, var_to_param


@numba.extending.register_jitable
def dummy_agg_count(A):
    return len(A)
