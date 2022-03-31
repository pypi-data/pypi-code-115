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
            kozvc__eussk = lir.FunctionType(lir.VoidType(), [lir.IntType(8)
                .as_pointer()])
            qpbo__rjn = cgutils.get_or_insert_function(builder.module,
                kozvc__eussk, sym._literal_value)
            builder.call(qpbo__rjn, [context.get_constant_null(sig.args[0])])
        elif sig == types.none(types.int64, types.voidptr, types.voidptr):
            kozvc__eussk = lir.FunctionType(lir.VoidType(), [lir.IntType(64
                ), lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
            qpbo__rjn = cgutils.get_or_insert_function(builder.module,
                kozvc__eussk, sym._literal_value)
            builder.call(qpbo__rjn, [context.get_constant(types.int64, 0),
                context.get_constant_null(sig.args[1]), context.
                get_constant_null(sig.args[2])])
        else:
            kozvc__eussk = lir.FunctionType(lir.VoidType(), [lir.IntType(8)
                .as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)
                .as_pointer()])
            qpbo__rjn = cgutils.get_or_insert_function(builder.module,
                kozvc__eussk, sym._literal_value)
            builder.call(qpbo__rjn, [context.get_constant_null(sig.args[0]),
                context.get_constant_null(sig.args[1]), context.
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
        xsgbg__syv = True
        yeiq__ukxt = 1
        ilnep__yonmk = -1
        if isinstance(rhs, ir.Expr):
            for cohl__zxk in rhs.kws:
                if func_name in list_cumulative:
                    if cohl__zxk[0] == 'skipna':
                        xsgbg__syv = guard(find_const, func_ir, cohl__zxk[1])
                        if not isinstance(xsgbg__syv, bool):
                            raise BodoError(
                                'For {} argument of skipna should be a boolean'
                                .format(func_name))
                if func_name == 'nunique':
                    if cohl__zxk[0] == 'dropna':
                        xsgbg__syv = guard(find_const, func_ir, cohl__zxk[1])
                        if not isinstance(xsgbg__syv, bool):
                            raise BodoError(
                                'argument of dropna to nunique should be a boolean'
                                )
        if func_name == 'shift' and (len(rhs.args) > 0 or len(rhs.kws) > 0):
            yeiq__ukxt = get_call_expr_arg('shift', rhs.args, dict(rhs.kws),
                0, 'periods', yeiq__ukxt)
            yeiq__ukxt = guard(find_const, func_ir, yeiq__ukxt)
        if func_name == 'head':
            ilnep__yonmk = get_call_expr_arg('head', rhs.args, dict(rhs.kws
                ), 0, 'n', 5)
            if not isinstance(ilnep__yonmk, int):
                ilnep__yonmk = guard(find_const, func_ir, ilnep__yonmk)
            if ilnep__yonmk < 0:
                raise BodoError(
                    f'groupby.{func_name} does not work with negative values.')
        func.skipdropna = xsgbg__syv
        func.periods = yeiq__ukxt
        func.head_n = ilnep__yonmk
        if func_name == 'transform':
            kws = dict(rhs.kws)
            ohel__axon = get_call_expr_arg(func_name, rhs.args, kws, 0,
                'func', '')
            klxwd__xjid = typemap[ohel__axon.name]
            qew__kwy = None
            if isinstance(klxwd__xjid, str):
                qew__kwy = klxwd__xjid
            elif is_overload_constant_str(klxwd__xjid):
                qew__kwy = get_overload_const_str(klxwd__xjid)
            elif bodo.utils.typing.is_builtin_function(klxwd__xjid):
                qew__kwy = bodo.utils.typing.get_builtin_function_name(
                    klxwd__xjid)
            if qew__kwy not in bodo.ir.aggregate.supported_transform_funcs[:]:
                raise BodoError(f'unsupported transform function {qew__kwy}')
            func.transform_func = supported_agg_funcs.index(qew__kwy)
        else:
            func.transform_func = supported_agg_funcs.index('no_op')
        return func
    assert func_name in ['agg', 'aggregate']
    assert typemap is not None
    kws = dict(rhs.kws)
    ohel__axon = get_call_expr_arg(func_name, rhs.args, kws, 0, 'func', '')
    if ohel__axon == '':
        klxwd__xjid = types.none
    else:
        klxwd__xjid = typemap[ohel__axon.name]
    if is_overload_constant_dict(klxwd__xjid):
        bru__mnlrx = get_overload_constant_dict(klxwd__xjid)
        avvq__ycm = [get_agg_func_udf(func_ir, f_val, rhs, series_type,
            typemap) for f_val in bru__mnlrx.values()]
        return avvq__ycm
    if klxwd__xjid == types.none:
        return [get_agg_func_udf(func_ir, get_literal_value(typemap[f_val.
            name])[1], rhs, series_type, typemap) for f_val in kws.values()]
    if isinstance(klxwd__xjid, types.BaseTuple):
        avvq__ycm = []
        ets__expat = 0
        for t in klxwd__xjid.types:
            if is_overload_constant_str(t):
                func_name = get_overload_const_str(t)
                avvq__ycm.append(get_agg_func(func_ir, func_name, rhs,
                    series_type, typemap))
            else:
                assert typemap is not None, 'typemap is required for agg UDF handling'
                func = _get_const_agg_func(t, func_ir)
                func.ftype = 'udf'
                func.fname = _get_udf_name(func)
                if func.fname == '<lambda>':
                    func.fname = '<lambda_' + str(ets__expat) + '>'
                    ets__expat += 1
                avvq__ycm.append(func)
        return [avvq__ycm]
    if is_overload_constant_str(klxwd__xjid):
        func_name = get_overload_const_str(klxwd__xjid)
        return get_agg_func(func_ir, func_name, rhs, series_type, typemap)
    if bodo.utils.typing.is_builtin_function(klxwd__xjid):
        func_name = bodo.utils.typing.get_builtin_function_name(klxwd__xjid)
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
        ets__expat = 0
        tcf__wrvs = []
        for bajni__otmxw in f_val:
            func = get_agg_func_udf(func_ir, bajni__otmxw, rhs, series_type,
                typemap)
            if func.fname == '<lambda>' and len(f_val) > 1:
                func.fname = f'<lambda_{ets__expat}>'
                ets__expat += 1
            tcf__wrvs.append(func)
        return tcf__wrvs
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
    qew__kwy = code.co_name
    return qew__kwy


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
            xhtvr__ucvey = types.DType(args[0])
            return signature(xhtvr__ucvey, *args)


@numba.njit(no_cpython_wrapper=True)
def _var_combine(ssqdm_a, mean_a, nobs_a, ssqdm_b, mean_b, nobs_b):
    hsvvp__wly = nobs_a + nobs_b
    mfhtk__kmd = (nobs_a * mean_a + nobs_b * mean_b) / hsvvp__wly
    tumm__uozh = mean_b - mean_a
    uonpc__ueliv = (ssqdm_a + ssqdm_b + tumm__uozh * tumm__uozh * nobs_a *
        nobs_b / hsvvp__wly)
    return uonpc__ueliv, mfhtk__kmd, hsvvp__wly


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
        lzpry__sva = ''
        for gkych__ddeel, mis__xixm in self.df_out_vars.items():
            lzpry__sva += "'{}':{}, ".format(gkych__ddeel, mis__xixm.name)
        jpch__ympsj = '{}{{{}}}'.format(self.df_out, lzpry__sva)
        vwdm__abtv = ''
        for gkych__ddeel, mis__xixm in self.df_in_vars.items():
            vwdm__abtv += "'{}':{}, ".format(gkych__ddeel, mis__xixm.name)
        kjam__vmdb = '{}{{{}}}'.format(self.df_in, vwdm__abtv)
        yor__kvsse = 'pivot {}:{}'.format(self.pivot_arr.name, self.
            pivot_values) if self.pivot_arr is not None else ''
        key_names = ','.join(self.key_names)
        tnd__zlm = ','.join([mis__xixm.name for mis__xixm in self.key_arrs])
        return 'aggregate: {} = {} [key: {}:{}] {}'.format(jpch__ympsj,
            kjam__vmdb, key_names, tnd__zlm, yor__kvsse)

    def remove_out_col(self, out_col_name):
        self.df_out_vars.pop(out_col_name)
        lxmmf__mst, hyo__tyv = self.gb_info_out.pop(out_col_name)
        if lxmmf__mst is None and not self.is_crosstab:
            return
        zqyuu__tvv = self.gb_info_in[lxmmf__mst]
        if self.pivot_arr is not None:
            self.pivot_values.remove(out_col_name)
            for eyhid__zifl, (func, lzpry__sva) in enumerate(zqyuu__tvv):
                try:
                    lzpry__sva.remove(out_col_name)
                    if len(lzpry__sva) == 0:
                        zqyuu__tvv.pop(eyhid__zifl)
                        break
                except ValueError as mrse__eos:
                    continue
        else:
            for eyhid__zifl, (func, hyk__fkuz) in enumerate(zqyuu__tvv):
                if hyk__fkuz == out_col_name:
                    zqyuu__tvv.pop(eyhid__zifl)
                    break
        if len(zqyuu__tvv) == 0:
            self.gb_info_in.pop(lxmmf__mst)
            self.df_in_vars.pop(lxmmf__mst)


def aggregate_usedefs(aggregate_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({mis__xixm.name for mis__xixm in aggregate_node.key_arrs})
    use_set.update({mis__xixm.name for mis__xixm in aggregate_node.
        df_in_vars.values()})
    if aggregate_node.pivot_arr is not None:
        use_set.add(aggregate_node.pivot_arr.name)
    def_set.update({mis__xixm.name for mis__xixm in aggregate_node.
        df_out_vars.values()})
    if aggregate_node.out_key_vars is not None:
        def_set.update({mis__xixm.name for mis__xixm in aggregate_node.
            out_key_vars})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Aggregate] = aggregate_usedefs


def remove_dead_aggregate(aggregate_node, lives_no_aliases, lives,
    arg_aliases, alias_map, func_ir, typemap):
    onyik__uic = [cma__dera for cma__dera, eqtrw__shk in aggregate_node.
        df_out_vars.items() if eqtrw__shk.name not in lives]
    for usrdo__rjzs in onyik__uic:
        aggregate_node.remove_out_col(usrdo__rjzs)
    out_key_vars = aggregate_node.out_key_vars
    if out_key_vars is not None and all(mis__xixm.name not in lives for
        mis__xixm in out_key_vars):
        aggregate_node.out_key_vars = None
    if len(aggregate_node.df_out_vars
        ) == 0 and aggregate_node.out_key_vars is None:
        return None
    return aggregate_node


ir_utils.remove_dead_extensions[Aggregate] = remove_dead_aggregate


def get_copies_aggregate(aggregate_node, typemap):
    iyggi__zohqr = set(mis__xixm.name for mis__xixm in aggregate_node.
        df_out_vars.values())
    if aggregate_node.out_key_vars is not None:
        iyggi__zohqr.update({mis__xixm.name for mis__xixm in aggregate_node
            .out_key_vars})
    return set(), iyggi__zohqr


ir_utils.copy_propagate_extensions[Aggregate] = get_copies_aggregate


def apply_copies_aggregate(aggregate_node, var_dict, name_var_table,
    typemap, calltypes, save_copies):
    for eyhid__zifl in range(len(aggregate_node.key_arrs)):
        aggregate_node.key_arrs[eyhid__zifl] = replace_vars_inner(
            aggregate_node.key_arrs[eyhid__zifl], var_dict)
    for cma__dera in list(aggregate_node.df_in_vars.keys()):
        aggregate_node.df_in_vars[cma__dera] = replace_vars_inner(
            aggregate_node.df_in_vars[cma__dera], var_dict)
    for cma__dera in list(aggregate_node.df_out_vars.keys()):
        aggregate_node.df_out_vars[cma__dera] = replace_vars_inner(
            aggregate_node.df_out_vars[cma__dera], var_dict)
    if aggregate_node.out_key_vars is not None:
        for eyhid__zifl in range(len(aggregate_node.out_key_vars)):
            aggregate_node.out_key_vars[eyhid__zifl] = replace_vars_inner(
                aggregate_node.out_key_vars[eyhid__zifl], var_dict)
    if aggregate_node.pivot_arr is not None:
        aggregate_node.pivot_arr = replace_vars_inner(aggregate_node.
            pivot_arr, var_dict)


ir_utils.apply_copy_propagate_extensions[Aggregate] = apply_copies_aggregate


def visit_vars_aggregate(aggregate_node, callback, cbdata):
    if debug_prints():
        print('visiting aggregate vars for:', aggregate_node)
        print('cbdata: ', sorted(cbdata.items()))
    for eyhid__zifl in range(len(aggregate_node.key_arrs)):
        aggregate_node.key_arrs[eyhid__zifl] = visit_vars_inner(aggregate_node
            .key_arrs[eyhid__zifl], callback, cbdata)
    for cma__dera in list(aggregate_node.df_in_vars.keys()):
        aggregate_node.df_in_vars[cma__dera] = visit_vars_inner(aggregate_node
            .df_in_vars[cma__dera], callback, cbdata)
    for cma__dera in list(aggregate_node.df_out_vars.keys()):
        aggregate_node.df_out_vars[cma__dera] = visit_vars_inner(aggregate_node
            .df_out_vars[cma__dera], callback, cbdata)
    if aggregate_node.out_key_vars is not None:
        for eyhid__zifl in range(len(aggregate_node.out_key_vars)):
            aggregate_node.out_key_vars[eyhid__zifl] = visit_vars_inner(
                aggregate_node.out_key_vars[eyhid__zifl], callback, cbdata)
    if aggregate_node.pivot_arr is not None:
        aggregate_node.pivot_arr = visit_vars_inner(aggregate_node.
            pivot_arr, callback, cbdata)


ir_utils.visit_vars_extensions[Aggregate] = visit_vars_aggregate


def aggregate_array_analysis(aggregate_node, equiv_set, typemap, array_analysis
    ):
    assert len(aggregate_node.df_out_vars
        ) > 0 or aggregate_node.out_key_vars is not None or aggregate_node.is_crosstab, 'empty aggregate in array analysis'
    nrhgz__rpp = []
    for vvle__whx in aggregate_node.key_arrs:
        cbk__uzkye = equiv_set.get_shape(vvle__whx)
        if cbk__uzkye:
            nrhgz__rpp.append(cbk__uzkye[0])
    if aggregate_node.pivot_arr is not None:
        cbk__uzkye = equiv_set.get_shape(aggregate_node.pivot_arr)
        if cbk__uzkye:
            nrhgz__rpp.append(cbk__uzkye[0])
    for eqtrw__shk in aggregate_node.df_in_vars.values():
        cbk__uzkye = equiv_set.get_shape(eqtrw__shk)
        if cbk__uzkye:
            nrhgz__rpp.append(cbk__uzkye[0])
    if len(nrhgz__rpp) > 1:
        equiv_set.insert_equiv(*nrhgz__rpp)
    neag__tfuv = []
    nrhgz__rpp = []
    pjdm__reeko = list(aggregate_node.df_out_vars.values())
    if aggregate_node.out_key_vars is not None:
        pjdm__reeko.extend(aggregate_node.out_key_vars)
    for eqtrw__shk in pjdm__reeko:
        ttnnh__kva = typemap[eqtrw__shk.name]
        kje__axq = array_analysis._gen_shape_call(equiv_set, eqtrw__shk,
            ttnnh__kva.ndim, None, neag__tfuv)
        equiv_set.insert_equiv(eqtrw__shk, kje__axq)
        nrhgz__rpp.append(kje__axq[0])
        equiv_set.define(eqtrw__shk, set())
    if len(nrhgz__rpp) > 1:
        equiv_set.insert_equiv(*nrhgz__rpp)
    return [], neag__tfuv


numba.parfors.array_analysis.array_analysis_extensions[Aggregate
    ] = aggregate_array_analysis


def aggregate_distributed_analysis(aggregate_node, array_dists):
    mund__awoq = Distribution.OneD
    for eqtrw__shk in aggregate_node.df_in_vars.values():
        mund__awoq = Distribution(min(mund__awoq.value, array_dists[
            eqtrw__shk.name].value))
    for vvle__whx in aggregate_node.key_arrs:
        mund__awoq = Distribution(min(mund__awoq.value, array_dists[
            vvle__whx.name].value))
    if aggregate_node.pivot_arr is not None:
        mund__awoq = Distribution(min(mund__awoq.value, array_dists[
            aggregate_node.pivot_arr.name].value))
        array_dists[aggregate_node.pivot_arr.name] = mund__awoq
    for eqtrw__shk in aggregate_node.df_in_vars.values():
        array_dists[eqtrw__shk.name] = mund__awoq
    for vvle__whx in aggregate_node.key_arrs:
        array_dists[vvle__whx.name] = mund__awoq
    axjhm__cxmzv = Distribution.OneD_Var
    for eqtrw__shk in aggregate_node.df_out_vars.values():
        if eqtrw__shk.name in array_dists:
            axjhm__cxmzv = Distribution(min(axjhm__cxmzv.value, array_dists
                [eqtrw__shk.name].value))
    if aggregate_node.out_key_vars is not None:
        for eqtrw__shk in aggregate_node.out_key_vars:
            if eqtrw__shk.name in array_dists:
                axjhm__cxmzv = Distribution(min(axjhm__cxmzv.value,
                    array_dists[eqtrw__shk.name].value))
    axjhm__cxmzv = Distribution(min(axjhm__cxmzv.value, mund__awoq.value))
    for eqtrw__shk in aggregate_node.df_out_vars.values():
        array_dists[eqtrw__shk.name] = axjhm__cxmzv
    if aggregate_node.out_key_vars is not None:
        for ffdi__jnsix in aggregate_node.out_key_vars:
            array_dists[ffdi__jnsix.name] = axjhm__cxmzv
    if axjhm__cxmzv != Distribution.OneD_Var:
        for vvle__whx in aggregate_node.key_arrs:
            array_dists[vvle__whx.name] = axjhm__cxmzv
        if aggregate_node.pivot_arr is not None:
            array_dists[aggregate_node.pivot_arr.name] = axjhm__cxmzv
        for eqtrw__shk in aggregate_node.df_in_vars.values():
            array_dists[eqtrw__shk.name] = axjhm__cxmzv


distributed_analysis.distributed_analysis_extensions[Aggregate
    ] = aggregate_distributed_analysis


def build_agg_definitions(agg_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for eqtrw__shk in agg_node.df_out_vars.values():
        definitions[eqtrw__shk.name].append(agg_node)
    if agg_node.out_key_vars is not None:
        for ffdi__jnsix in agg_node.out_key_vars:
            definitions[ffdi__jnsix.name].append(agg_node)
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
        for mis__xixm in (list(agg_node.df_in_vars.values()) + list(
            agg_node.df_out_vars.values()) + agg_node.key_arrs):
            if array_dists[mis__xixm.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                mis__xixm.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    fvu__xjfum = tuple(typemap[mis__xixm.name] for mis__xixm in agg_node.
        key_arrs)
    ifxf__woawv = [mis__xixm for yomrp__miqab, mis__xixm in agg_node.
        df_in_vars.items()]
    dmqxs__kgnwp = [mis__xixm for yomrp__miqab, mis__xixm in agg_node.
        df_out_vars.items()]
    in_col_typs = []
    avvq__ycm = []
    if agg_node.pivot_arr is not None:
        for lxmmf__mst, zqyuu__tvv in agg_node.gb_info_in.items():
            for func, hyo__tyv in zqyuu__tvv:
                if lxmmf__mst is not None:
                    in_col_typs.append(typemap[agg_node.df_in_vars[
                        lxmmf__mst].name])
                avvq__ycm.append(func)
    else:
        for lxmmf__mst, func in agg_node.gb_info_out.values():
            if lxmmf__mst is not None:
                in_col_typs.append(typemap[agg_node.df_in_vars[lxmmf__mst].
                    name])
            avvq__ycm.append(func)
    out_col_typs = tuple(typemap[mis__xixm.name] for mis__xixm in dmqxs__kgnwp)
    pivot_typ = types.none if agg_node.pivot_arr is None else typemap[agg_node
        .pivot_arr.name]
    arg_typs = tuple(fvu__xjfum + tuple(typemap[mis__xixm.name] for
        mis__xixm in ifxf__woawv) + (pivot_typ,))
    in_col_typs = [to_str_arr_if_dict_array(t) for t in in_col_typs]
    pomj__wqnn = {'bodo': bodo, 'np': np, 'dt64_dtype': np.dtype(
        'datetime64[ns]'), 'td64_dtype': np.dtype('timedelta64[ns]')}
    for eyhid__zifl, in_col_typ in enumerate(in_col_typs):
        if isinstance(in_col_typ, bodo.CategoricalArrayType):
            pomj__wqnn.update({f'in_cat_dtype_{eyhid__zifl}': in_col_typ})
    for eyhid__zifl, xhq__vfca in enumerate(out_col_typs):
        if isinstance(xhq__vfca, bodo.CategoricalArrayType):
            pomj__wqnn.update({f'out_cat_dtype_{eyhid__zifl}': xhq__vfca})
    udf_func_struct = get_udf_func_struct(avvq__ycm, agg_node.
        input_has_index, in_col_typs, out_col_typs, typingctx, targetctx,
        pivot_typ, agg_node.pivot_values, agg_node.is_crosstab)
    fimq__heo = gen_top_level_agg_func(agg_node, in_col_typs, out_col_typs,
        parallel, udf_func_struct)
    pomj__wqnn.update({'pd': pd, 'pre_alloc_string_array':
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
            pomj__wqnn.update({'__update_redvars': udf_func_struct.
                update_all_func, '__init_func': udf_func_struct.init_func,
                '__combine_redvars': udf_func_struct.combine_all_func,
                '__eval_res': udf_func_struct.eval_all_func,
                'cpp_cb_update': udf_func_struct.regular_udf_cfuncs[0],
                'cpp_cb_combine': udf_func_struct.regular_udf_cfuncs[1],
                'cpp_cb_eval': udf_func_struct.regular_udf_cfuncs[2]})
        if udf_func_struct.general_udfs:
            pomj__wqnn.update({'cpp_cb_general': udf_func_struct.
                general_udf_cfunc})
    dilu__xymgc = compile_to_numba_ir(fimq__heo, pomj__wqnn, typingctx=
        typingctx, targetctx=targetctx, arg_typs=arg_typs, typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    uvhkm__sufa = []
    if agg_node.pivot_arr is None:
        tqgb__dzl = agg_node.key_arrs[0].scope
        loc = agg_node.loc
        obhb__auun = ir.Var(tqgb__dzl, mk_unique_var('dummy_none'), loc)
        typemap[obhb__auun.name] = types.none
        uvhkm__sufa.append(ir.Assign(ir.Const(None, loc), obhb__auun, loc))
        ifxf__woawv.append(obhb__auun)
    else:
        ifxf__woawv.append(agg_node.pivot_arr)
    replace_arg_nodes(dilu__xymgc, agg_node.key_arrs + ifxf__woawv)
    lrwxe__kdx = dilu__xymgc.body[-3]
    assert is_assign(lrwxe__kdx) and isinstance(lrwxe__kdx.value, ir.Expr
        ) and lrwxe__kdx.value.op == 'build_tuple'
    uvhkm__sufa += dilu__xymgc.body[:-3]
    pjdm__reeko = list(agg_node.df_out_vars.values())
    if agg_node.out_key_vars is not None:
        pjdm__reeko += agg_node.out_key_vars
    for eyhid__zifl, smfu__iuo in enumerate(pjdm__reeko):
        bvr__zyix = lrwxe__kdx.value.items[eyhid__zifl]
        uvhkm__sufa.append(ir.Assign(bvr__zyix, smfu__iuo, smfu__iuo.loc))
    return uvhkm__sufa


distributed_pass.distributed_run_extensions[Aggregate] = agg_distributed_run


def get_numba_set(dtype):
    pass


@infer_global(get_numba_set)
class GetNumbaSetTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 1
        hzto__eehom = args[0]
        dtype = types.Tuple([t.dtype for t in hzto__eehom.types]
            ) if isinstance(hzto__eehom, types.BaseTuple
            ) else hzto__eehom.dtype
        if isinstance(hzto__eehom, types.BaseTuple) and len(hzto__eehom.types
            ) == 1:
            dtype = hzto__eehom.types[0].dtype
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
        zyx__ljw = args[0]
        if zyx__ljw == types.none:
            return signature(types.boolean, *args)


@lower_builtin(bool, types.none)
def lower_column_mean_impl(context, builder, sig, args):
    rutnu__pikvs = context.compile_internal(builder, lambda a: False, sig, args
        )
    return rutnu__pikvs


def _gen_dummy_alloc(t, colnum=0, is_input=False):
    if isinstance(t, IntegerArrayType):
        kfblf__eglot = IntDtype(t.dtype).name
        assert kfblf__eglot.endswith('Dtype()')
        kfblf__eglot = kfblf__eglot[:-7]
        return (
            f"bodo.hiframes.pd_series_ext.get_series_data(pd.Series([1], dtype='{kfblf__eglot}'))"
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
        iwdnd__byjk = 'in' if is_input else 'out'
        return (
            f'bodo.utils.utils.alloc_type(1, {iwdnd__byjk}_cat_dtype_{colnum})'
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
    bnr__nfcna = udf_func_struct.var_typs
    cho__fdvth = len(bnr__nfcna)
    whpe__yyum = (
        'def bodo_gb_udf_update_local{}(in_table, out_table, row_to_group):\n'
        .format(label_suffix))
    whpe__yyum += '    if is_null_pointer(in_table):\n'
    whpe__yyum += '        return\n'
    whpe__yyum += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in bnr__nfcna]), 
        ',' if len(bnr__nfcna) == 1 else '')
    lgk__iprm = n_keys
    epnb__jnrzr = []
    redvar_offsets = []
    jtgm__aihk = []
    if do_combine:
        for eyhid__zifl, bajni__otmxw in enumerate(allfuncs):
            if bajni__otmxw.ftype != 'udf':
                lgk__iprm += bajni__otmxw.ncols_pre_shuffle
            else:
                redvar_offsets += list(range(lgk__iprm, lgk__iprm +
                    bajni__otmxw.n_redvars))
                lgk__iprm += bajni__otmxw.n_redvars
                jtgm__aihk.append(data_in_typs_[func_idx_to_in_col[
                    eyhid__zifl]])
                epnb__jnrzr.append(func_idx_to_in_col[eyhid__zifl] + n_keys)
    else:
        for eyhid__zifl, bajni__otmxw in enumerate(allfuncs):
            if bajni__otmxw.ftype != 'udf':
                lgk__iprm += bajni__otmxw.ncols_post_shuffle
            else:
                redvar_offsets += list(range(lgk__iprm + 1, lgk__iprm + 1 +
                    bajni__otmxw.n_redvars))
                lgk__iprm += bajni__otmxw.n_redvars + 1
                jtgm__aihk.append(data_in_typs_[func_idx_to_in_col[
                    eyhid__zifl]])
                epnb__jnrzr.append(func_idx_to_in_col[eyhid__zifl] + n_keys)
    assert len(redvar_offsets) == cho__fdvth
    znb__iqq = len(jtgm__aihk)
    phkrm__ogr = []
    for eyhid__zifl, t in enumerate(jtgm__aihk):
        phkrm__ogr.append(_gen_dummy_alloc(t, eyhid__zifl, True))
    whpe__yyum += '    data_in_dummy = ({}{})\n'.format(','.join(phkrm__ogr
        ), ',' if len(jtgm__aihk) == 1 else '')
    whpe__yyum += """
    # initialize redvar cols
"""
    whpe__yyum += '    init_vals = __init_func()\n'
    for eyhid__zifl in range(cho__fdvth):
        whpe__yyum += (
            """    redvar_arr_{} = info_to_array(info_from_table(out_table, {}), data_redvar_dummy[{}])
"""
            .format(eyhid__zifl, redvar_offsets[eyhid__zifl], eyhid__zifl))
        whpe__yyum += '    incref(redvar_arr_{})\n'.format(eyhid__zifl)
        whpe__yyum += '    redvar_arr_{}.fill(init_vals[{}])\n'.format(
            eyhid__zifl, eyhid__zifl)
    whpe__yyum += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'
        .format(eyhid__zifl) for eyhid__zifl in range(cho__fdvth)]), ',' if
        cho__fdvth == 1 else '')
    whpe__yyum += '\n'
    for eyhid__zifl in range(znb__iqq):
        whpe__yyum += (
            """    data_in_{} = info_to_array(info_from_table(in_table, {}), data_in_dummy[{}])
"""
            .format(eyhid__zifl, epnb__jnrzr[eyhid__zifl], eyhid__zifl))
        whpe__yyum += '    incref(data_in_{})\n'.format(eyhid__zifl)
    whpe__yyum += '    data_in = ({}{})\n'.format(','.join(['data_in_{}'.
        format(eyhid__zifl) for eyhid__zifl in range(znb__iqq)]), ',' if 
        znb__iqq == 1 else '')
    whpe__yyum += '\n'
    whpe__yyum += '    for i in range(len(data_in_0)):\n'
    whpe__yyum += '        w_ind = row_to_group[i]\n'
    whpe__yyum += '        if w_ind != -1:\n'
    whpe__yyum += (
        '            __update_redvars(redvars, data_in, w_ind, i, pivot_arr=None)\n'
        )
    qpp__wqbb = {}
    exec(whpe__yyum, {'bodo': bodo, 'np': np, 'pd': pd, 'info_to_array':
        info_to_array, 'info_from_table': info_from_table, 'incref': incref,
        'pre_alloc_string_array': pre_alloc_string_array, '__init_func':
        udf_func_struct.init_func, '__update_redvars': udf_func_struct.
        update_all_func, 'is_null_pointer': is_null_pointer, 'dt64_dtype':
        np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, qpp__wqbb)
    return qpp__wqbb['bodo_gb_udf_update_local{}'.format(label_suffix)]


def gen_combine_cb(udf_func_struct, allfuncs, n_keys, out_data_typs,
    label_suffix):
    bnr__nfcna = udf_func_struct.var_typs
    cho__fdvth = len(bnr__nfcna)
    whpe__yyum = (
        'def bodo_gb_udf_combine{}(in_table, out_table, row_to_group):\n'.
        format(label_suffix))
    whpe__yyum += '    if is_null_pointer(in_table):\n'
    whpe__yyum += '        return\n'
    whpe__yyum += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in bnr__nfcna]), 
        ',' if len(bnr__nfcna) == 1 else '')
    yxwi__gdx = n_keys
    innt__fddg = n_keys
    pogj__zwj = []
    kpggq__txgn = []
    for bajni__otmxw in allfuncs:
        if bajni__otmxw.ftype != 'udf':
            yxwi__gdx += bajni__otmxw.ncols_pre_shuffle
            innt__fddg += bajni__otmxw.ncols_post_shuffle
        else:
            pogj__zwj += list(range(yxwi__gdx, yxwi__gdx + bajni__otmxw.
                n_redvars))
            kpggq__txgn += list(range(innt__fddg + 1, innt__fddg + 1 +
                bajni__otmxw.n_redvars))
            yxwi__gdx += bajni__otmxw.n_redvars
            innt__fddg += 1 + bajni__otmxw.n_redvars
    assert len(pogj__zwj) == cho__fdvth
    whpe__yyum += """
    # initialize redvar cols
"""
    whpe__yyum += '    init_vals = __init_func()\n'
    for eyhid__zifl in range(cho__fdvth):
        whpe__yyum += (
            """    redvar_arr_{} = info_to_array(info_from_table(out_table, {}), data_redvar_dummy[{}])
"""
            .format(eyhid__zifl, kpggq__txgn[eyhid__zifl], eyhid__zifl))
        whpe__yyum += '    incref(redvar_arr_{})\n'.format(eyhid__zifl)
        whpe__yyum += '    redvar_arr_{}.fill(init_vals[{}])\n'.format(
            eyhid__zifl, eyhid__zifl)
    whpe__yyum += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'
        .format(eyhid__zifl) for eyhid__zifl in range(cho__fdvth)]), ',' if
        cho__fdvth == 1 else '')
    whpe__yyum += '\n'
    for eyhid__zifl in range(cho__fdvth):
        whpe__yyum += (
            """    recv_redvar_arr_{} = info_to_array(info_from_table(in_table, {}), data_redvar_dummy[{}])
"""
            .format(eyhid__zifl, pogj__zwj[eyhid__zifl], eyhid__zifl))
        whpe__yyum += '    incref(recv_redvar_arr_{})\n'.format(eyhid__zifl)
    whpe__yyum += '    recv_redvars = ({}{})\n'.format(','.join([
        'recv_redvar_arr_{}'.format(eyhid__zifl) for eyhid__zifl in range(
        cho__fdvth)]), ',' if cho__fdvth == 1 else '')
    whpe__yyum += '\n'
    if cho__fdvth:
        whpe__yyum += '    for i in range(len(recv_redvar_arr_0)):\n'
        whpe__yyum += '        w_ind = row_to_group[i]\n'
        whpe__yyum += """        __combine_redvars(redvars, recv_redvars, w_ind, i, pivot_arr=None)
"""
    qpp__wqbb = {}
    exec(whpe__yyum, {'np': np, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref, '__init_func':
        udf_func_struct.init_func, '__combine_redvars': udf_func_struct.
        combine_all_func, 'is_null_pointer': is_null_pointer, 'dt64_dtype':
        np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, qpp__wqbb)
    return qpp__wqbb['bodo_gb_udf_combine{}'.format(label_suffix)]


def gen_eval_cb(udf_func_struct, allfuncs, n_keys, out_data_typs_, label_suffix
    ):
    bnr__nfcna = udf_func_struct.var_typs
    cho__fdvth = len(bnr__nfcna)
    lgk__iprm = n_keys
    redvar_offsets = []
    gggr__eig = []
    out_data_typs = []
    for eyhid__zifl, bajni__otmxw in enumerate(allfuncs):
        if bajni__otmxw.ftype != 'udf':
            lgk__iprm += bajni__otmxw.ncols_post_shuffle
        else:
            gggr__eig.append(lgk__iprm)
            redvar_offsets += list(range(lgk__iprm + 1, lgk__iprm + 1 +
                bajni__otmxw.n_redvars))
            lgk__iprm += 1 + bajni__otmxw.n_redvars
            out_data_typs.append(out_data_typs_[eyhid__zifl])
    assert len(redvar_offsets) == cho__fdvth
    znb__iqq = len(out_data_typs)
    whpe__yyum = 'def bodo_gb_udf_eval{}(table):\n'.format(label_suffix)
    whpe__yyum += '    if is_null_pointer(table):\n'
    whpe__yyum += '        return\n'
    whpe__yyum += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in bnr__nfcna]), 
        ',' if len(bnr__nfcna) == 1 else '')
    whpe__yyum += '    out_data_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t.dtype)) for t in
        out_data_typs]), ',' if len(out_data_typs) == 1 else '')
    for eyhid__zifl in range(cho__fdvth):
        whpe__yyum += (
            """    redvar_arr_{} = info_to_array(info_from_table(table, {}), data_redvar_dummy[{}])
"""
            .format(eyhid__zifl, redvar_offsets[eyhid__zifl], eyhid__zifl))
        whpe__yyum += '    incref(redvar_arr_{})\n'.format(eyhid__zifl)
    whpe__yyum += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'
        .format(eyhid__zifl) for eyhid__zifl in range(cho__fdvth)]), ',' if
        cho__fdvth == 1 else '')
    whpe__yyum += '\n'
    for eyhid__zifl in range(znb__iqq):
        whpe__yyum += (
            """    data_out_{} = info_to_array(info_from_table(table, {}), out_data_dummy[{}])
"""
            .format(eyhid__zifl, gggr__eig[eyhid__zifl], eyhid__zifl))
        whpe__yyum += '    incref(data_out_{})\n'.format(eyhid__zifl)
    whpe__yyum += '    data_out = ({}{})\n'.format(','.join(['data_out_{}'.
        format(eyhid__zifl) for eyhid__zifl in range(znb__iqq)]), ',' if 
        znb__iqq == 1 else '')
    whpe__yyum += '\n'
    whpe__yyum += '    for i in range(len(data_out_0)):\n'
    whpe__yyum += '        __eval_res(redvars, data_out, i)\n'
    qpp__wqbb = {}
    exec(whpe__yyum, {'np': np, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref, '__eval_res':
        udf_func_struct.eval_all_func, 'is_null_pointer': is_null_pointer,
        'dt64_dtype': np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, qpp__wqbb)
    return qpp__wqbb['bodo_gb_udf_eval{}'.format(label_suffix)]


def gen_general_udf_cb(udf_func_struct, allfuncs, n_keys, in_col_typs,
    out_col_typs, func_idx_to_in_col, label_suffix):
    lgk__iprm = n_keys
    xbdwu__fea = []
    for eyhid__zifl, bajni__otmxw in enumerate(allfuncs):
        if bajni__otmxw.ftype == 'gen_udf':
            xbdwu__fea.append(lgk__iprm)
            lgk__iprm += 1
        elif bajni__otmxw.ftype != 'udf':
            lgk__iprm += bajni__otmxw.ncols_post_shuffle
        else:
            lgk__iprm += bajni__otmxw.n_redvars + 1
    whpe__yyum = (
        'def bodo_gb_apply_general_udfs{}(num_groups, in_table, out_table):\n'
        .format(label_suffix))
    whpe__yyum += '    if num_groups == 0:\n'
    whpe__yyum += '        return\n'
    for eyhid__zifl, func in enumerate(udf_func_struct.general_udf_funcs):
        whpe__yyum += '    # col {}\n'.format(eyhid__zifl)
        whpe__yyum += (
            """    out_col = info_to_array(info_from_table(out_table, {}), out_col_{}_typ)
"""
            .format(xbdwu__fea[eyhid__zifl], eyhid__zifl))
        whpe__yyum += '    incref(out_col)\n'
        whpe__yyum += '    for j in range(num_groups):\n'
        whpe__yyum += (
            """        in_col = info_to_array(info_from_table(in_table, {}*num_groups + j), in_col_{}_typ)
"""
            .format(eyhid__zifl, eyhid__zifl))
        whpe__yyum += '        incref(in_col)\n'
        whpe__yyum += (
            '        out_col[j] = func_{}(pd.Series(in_col))  # func returns scalar\n'
            .format(eyhid__zifl))
    pomj__wqnn = {'pd': pd, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref}
    ojil__xrd = 0
    for eyhid__zifl, func in enumerate(allfuncs):
        if func.ftype != 'gen_udf':
            continue
        func = udf_func_struct.general_udf_funcs[ojil__xrd]
        pomj__wqnn['func_{}'.format(ojil__xrd)] = func
        pomj__wqnn['in_col_{}_typ'.format(ojil__xrd)] = in_col_typs[
            func_idx_to_in_col[eyhid__zifl]]
        pomj__wqnn['out_col_{}_typ'.format(ojil__xrd)] = out_col_typs[
            eyhid__zifl]
        ojil__xrd += 1
    qpp__wqbb = {}
    exec(whpe__yyum, pomj__wqnn, qpp__wqbb)
    bajni__otmxw = qpp__wqbb['bodo_gb_apply_general_udfs{}'.format(
        label_suffix)]
    nfzy__cglpm = types.void(types.int64, types.voidptr, types.voidptr)
    return numba.cfunc(nfzy__cglpm, nopython=True)(bajni__otmxw)


def gen_top_level_agg_func(agg_node, in_col_typs, out_col_typs, parallel,
    udf_func_struct):
    bcb__tuahv = agg_node.pivot_arr is not None
    if agg_node.same_index:
        assert agg_node.input_has_index
    if agg_node.pivot_values is None:
        skmz__ojdux = 1
    else:
        skmz__ojdux = len(agg_node.pivot_values)
    rrp__knmkf = tuple('key_' + sanitize_varname(gkych__ddeel) for
        gkych__ddeel in agg_node.key_names)
    vnem__kdqw = {gkych__ddeel: 'in_{}'.format(sanitize_varname(
        gkych__ddeel)) for gkych__ddeel in agg_node.gb_info_in.keys() if 
        gkych__ddeel is not None}
    eqtv__uwstp = {gkych__ddeel: ('out_' + sanitize_varname(gkych__ddeel)) for
        gkych__ddeel in agg_node.gb_info_out.keys()}
    n_keys = len(agg_node.key_names)
    fzvw__hfzn = ', '.join(rrp__knmkf)
    ywyxi__sxjx = ', '.join(vnem__kdqw.values())
    if ywyxi__sxjx != '':
        ywyxi__sxjx = ', ' + ywyxi__sxjx
    whpe__yyum = 'def agg_top({}{}{}, pivot_arr):\n'.format(fzvw__hfzn,
        ywyxi__sxjx, ', index_arg' if agg_node.input_has_index else '')
    for a in (rrp__knmkf + tuple(vnem__kdqw.values())):
        whpe__yyum += f'    {a} = decode_if_dict_array({a})\n'
    if bcb__tuahv:
        whpe__yyum += f'    pivot_arr = decode_if_dict_array(pivot_arr)\n'
        doe__vfvda = []
        for lxmmf__mst, zqyuu__tvv in agg_node.gb_info_in.items():
            if lxmmf__mst is not None:
                for func, hyo__tyv in zqyuu__tvv:
                    doe__vfvda.append(vnem__kdqw[lxmmf__mst])
    else:
        doe__vfvda = tuple(vnem__kdqw[lxmmf__mst] for lxmmf__mst, hyo__tyv in
            agg_node.gb_info_out.values() if lxmmf__mst is not None)
    raqk__jmfyq = rrp__knmkf + tuple(doe__vfvda)
    whpe__yyum += '    info_list = [{}{}{}]\n'.format(', '.join(
        'array_to_info({})'.format(a) for a in raqk__jmfyq), 
        ', array_to_info(index_arg)' if agg_node.input_has_index else '', 
        ', array_to_info(pivot_arr)' if agg_node.is_crosstab else '')
    whpe__yyum += '    table = arr_info_list_to_table(info_list)\n'
    for eyhid__zifl, gkych__ddeel in enumerate(agg_node.gb_info_out.keys()):
        cyo__msq = eqtv__uwstp[gkych__ddeel] + '_dummy'
        xhq__vfca = out_col_typs[eyhid__zifl]
        lxmmf__mst, func = agg_node.gb_info_out[gkych__ddeel]
        if isinstance(func, pytypes.SimpleNamespace) and func.fname in ['min',
            'max', 'shift'] and isinstance(xhq__vfca, bodo.CategoricalArrayType
            ):
            whpe__yyum += '    {} = {}\n'.format(cyo__msq, vnem__kdqw[
                lxmmf__mst])
        else:
            whpe__yyum += '    {} = {}\n'.format(cyo__msq, _gen_dummy_alloc
                (xhq__vfca, eyhid__zifl, False))
    do_combine = parallel
    allfuncs = []
    gucg__mjy = []
    func_idx_to_in_col = []
    lxojz__ena = []
    xsgbg__syv = False
    yizcx__rvj = 1
    ilnep__yonmk = -1
    srz__aplni = 0
    ggt__auwv = 0
    if not bcb__tuahv:
        avvq__ycm = [func for hyo__tyv, func in agg_node.gb_info_out.values()]
    else:
        avvq__ycm = [func for func, hyo__tyv in zqyuu__tvv for zqyuu__tvv in
            agg_node.gb_info_in.values()]
    for inv__aiz, func in enumerate(avvq__ycm):
        gucg__mjy.append(len(allfuncs))
        if func.ftype in {'median', 'nunique'}:
            do_combine = False
        if func.ftype in list_cumulative:
            srz__aplni += 1
        if hasattr(func, 'skipdropna'):
            xsgbg__syv = func.skipdropna
        if func.ftype == 'shift':
            yizcx__rvj = func.periods
            do_combine = False
        if func.ftype in {'transform'}:
            ggt__auwv = func.transform_func
            do_combine = False
        if func.ftype == 'head':
            ilnep__yonmk = func.head_n
            do_combine = False
        allfuncs.append(func)
        func_idx_to_in_col.append(inv__aiz)
        if func.ftype == 'udf':
            lxojz__ena.append(func.n_redvars)
        elif func.ftype == 'gen_udf':
            lxojz__ena.append(0)
            do_combine = False
    gucg__mjy.append(len(allfuncs))
    if agg_node.is_crosstab:
        assert len(agg_node.gb_info_out
            ) == skmz__ojdux, 'invalid number of groupby outputs for pivot'
    else:
        assert len(agg_node.gb_info_out) == len(allfuncs
            ) * skmz__ojdux, 'invalid number of groupby outputs'
    if srz__aplni > 0:
        if srz__aplni != len(allfuncs):
            raise BodoError(
                f'{agg_node.func_name}(): Cannot mix cumulative operations with other aggregation functions'
                , loc=agg_node.loc)
        do_combine = False
    if udf_func_struct is not None:
        asak__omdsl = next_label()
        if udf_func_struct.regular_udfs:
            nfzy__cglpm = types.void(types.voidptr, types.voidptr, types.
                CPointer(types.int64))
            isabh__kllnu = numba.cfunc(nfzy__cglpm, nopython=True)(
                gen_update_cb(udf_func_struct, allfuncs, n_keys,
                in_col_typs, out_col_typs, do_combine, func_idx_to_in_col,
                asak__omdsl))
            jtjz__qsmh = numba.cfunc(nfzy__cglpm, nopython=True)(gen_combine_cb
                (udf_func_struct, allfuncs, n_keys, out_col_typs, asak__omdsl))
            pfdzl__eib = numba.cfunc('void(voidptr)', nopython=True)(
                gen_eval_cb(udf_func_struct, allfuncs, n_keys, out_col_typs,
                asak__omdsl))
            udf_func_struct.set_regular_cfuncs(isabh__kllnu, jtjz__qsmh,
                pfdzl__eib)
            for xko__pel in udf_func_struct.regular_udf_cfuncs:
                gb_agg_cfunc[xko__pel.native_name] = xko__pel
                gb_agg_cfunc_addr[xko__pel.native_name] = xko__pel.address
        if udf_func_struct.general_udfs:
            odrj__aay = gen_general_udf_cb(udf_func_struct, allfuncs,
                n_keys, in_col_typs, out_col_typs, func_idx_to_in_col,
                asak__omdsl)
            udf_func_struct.set_general_cfunc(odrj__aay)
        njrvp__qqbiz = []
        bdsi__ydi = 0
        eyhid__zifl = 0
        for cyo__msq, bajni__otmxw in zip(eqtv__uwstp.values(), allfuncs):
            if bajni__otmxw.ftype in ('udf', 'gen_udf'):
                njrvp__qqbiz.append(cyo__msq + '_dummy')
                for sdy__huig in range(bdsi__ydi, bdsi__ydi + lxojz__ena[
                    eyhid__zifl]):
                    njrvp__qqbiz.append('data_redvar_dummy_' + str(sdy__huig))
                bdsi__ydi += lxojz__ena[eyhid__zifl]
                eyhid__zifl += 1
        if udf_func_struct.regular_udfs:
            bnr__nfcna = udf_func_struct.var_typs
            for eyhid__zifl, t in enumerate(bnr__nfcna):
                whpe__yyum += ('    data_redvar_dummy_{} = np.empty(1, {})\n'
                    .format(eyhid__zifl, _get_np_dtype(t)))
        whpe__yyum += '    out_info_list_dummy = [{}]\n'.format(', '.join(
            'array_to_info({})'.format(a) for a in njrvp__qqbiz))
        whpe__yyum += (
            '    udf_table_dummy = arr_info_list_to_table(out_info_list_dummy)\n'
            )
        if udf_func_struct.regular_udfs:
            whpe__yyum += ("    add_agg_cfunc_sym(cpp_cb_update, '{}')\n".
                format(isabh__kllnu.native_name))
            whpe__yyum += ("    add_agg_cfunc_sym(cpp_cb_combine, '{}')\n".
                format(jtjz__qsmh.native_name))
            whpe__yyum += "    add_agg_cfunc_sym(cpp_cb_eval, '{}')\n".format(
                pfdzl__eib.native_name)
            whpe__yyum += ("    cpp_cb_update_addr = get_agg_udf_addr('{}')\n"
                .format(isabh__kllnu.native_name))
            whpe__yyum += ("    cpp_cb_combine_addr = get_agg_udf_addr('{}')\n"
                .format(jtjz__qsmh.native_name))
            whpe__yyum += ("    cpp_cb_eval_addr = get_agg_udf_addr('{}')\n"
                .format(pfdzl__eib.native_name))
        else:
            whpe__yyum += '    cpp_cb_update_addr = 0\n'
            whpe__yyum += '    cpp_cb_combine_addr = 0\n'
            whpe__yyum += '    cpp_cb_eval_addr = 0\n'
        if udf_func_struct.general_udfs:
            xko__pel = udf_func_struct.general_udf_cfunc
            gb_agg_cfunc[xko__pel.native_name] = xko__pel
            gb_agg_cfunc_addr[xko__pel.native_name] = xko__pel.address
            whpe__yyum += ("    add_agg_cfunc_sym(cpp_cb_general, '{}')\n".
                format(xko__pel.native_name))
            whpe__yyum += ("    cpp_cb_general_addr = get_agg_udf_addr('{}')\n"
                .format(xko__pel.native_name))
        else:
            whpe__yyum += '    cpp_cb_general_addr = 0\n'
    else:
        whpe__yyum += """    udf_table_dummy = arr_info_list_to_table([array_to_info(np.empty(1))])
"""
        whpe__yyum += '    cpp_cb_update_addr = 0\n'
        whpe__yyum += '    cpp_cb_combine_addr = 0\n'
        whpe__yyum += '    cpp_cb_eval_addr = 0\n'
        whpe__yyum += '    cpp_cb_general_addr = 0\n'
    whpe__yyum += '    ftypes = np.array([{}, 0], dtype=np.int32)\n'.format(
        ', '.join([str(supported_agg_funcs.index(bajni__otmxw.ftype)) for
        bajni__otmxw in allfuncs] + ['0']))
    whpe__yyum += '    func_offsets = np.array({}, dtype=np.int32)\n'.format(
        str(gucg__mjy))
    if len(lxojz__ena) > 0:
        whpe__yyum += '    udf_ncols = np.array({}, dtype=np.int32)\n'.format(
            str(lxojz__ena))
    else:
        whpe__yyum += '    udf_ncols = np.array([0], np.int32)\n'
    if bcb__tuahv:
        whpe__yyum += '    arr_type = coerce_to_array({})\n'.format(agg_node
            .pivot_values)
        whpe__yyum += '    arr_info = array_to_info(arr_type)\n'
        whpe__yyum += (
            '    dispatch_table = arr_info_list_to_table([arr_info])\n')
        whpe__yyum += '    pivot_info = array_to_info(pivot_arr)\n'
        whpe__yyum += (
            '    dispatch_info = arr_info_list_to_table([pivot_info])\n')
        whpe__yyum += (
            """    out_table = pivot_groupby_and_aggregate(table, {}, dispatch_table, dispatch_info, {}, ftypes.ctypes, func_offsets.ctypes, udf_ncols.ctypes, {}, {}, {}, {}, {}, cpp_cb_update_addr, cpp_cb_combine_addr, cpp_cb_eval_addr, udf_table_dummy)
"""
            .format(n_keys, agg_node.input_has_index, parallel, agg_node.
            is_crosstab, xsgbg__syv, agg_node.return_key, agg_node.same_index))
        whpe__yyum += '    delete_info_decref_array(pivot_info)\n'
        whpe__yyum += '    delete_info_decref_array(arr_info)\n'
    else:
        whpe__yyum += (
            """    out_table = groupby_and_aggregate(table, {}, {}, ftypes.ctypes, func_offsets.ctypes, udf_ncols.ctypes, {}, {}, {}, {}, {}, {}, {}, {}, cpp_cb_update_addr, cpp_cb_combine_addr, cpp_cb_eval_addr, cpp_cb_general_addr, udf_table_dummy)
"""
            .format(n_keys, agg_node.input_has_index, parallel, xsgbg__syv,
            yizcx__rvj, ggt__auwv, ilnep__yonmk, agg_node.return_key,
            agg_node.same_index, agg_node.dropna))
    hcmh__ntxl = 0
    if agg_node.return_key:
        for eyhid__zifl, ubj__rsys in enumerate(rrp__knmkf):
            whpe__yyum += (
                '    {} = info_to_array(info_from_table(out_table, {}), {})\n'
                .format(ubj__rsys, hcmh__ntxl, ubj__rsys))
            hcmh__ntxl += 1
    for cyo__msq in eqtv__uwstp.values():
        whpe__yyum += (
            '    {} = info_to_array(info_from_table(out_table, {}), {})\n'.
            format(cyo__msq, hcmh__ntxl, cyo__msq + '_dummy'))
        hcmh__ntxl += 1
    if agg_node.same_index:
        whpe__yyum += (
            """    out_index_arg = info_to_array(info_from_table(out_table, {}), index_arg)
"""
            .format(hcmh__ntxl))
        hcmh__ntxl += 1
    whpe__yyum += (
        f"    ev_clean = bodo.utils.tracing.Event('tables_clean_up', {parallel})\n"
        )
    whpe__yyum += '    delete_table_decref_arrays(table)\n'
    whpe__yyum += '    delete_table_decref_arrays(udf_table_dummy)\n'
    whpe__yyum += '    delete_table(out_table)\n'
    whpe__yyum += f'    ev_clean.finalize()\n'
    ovtuu__jykbm = tuple(eqtv__uwstp.values())
    if agg_node.return_key:
        ovtuu__jykbm += tuple(rrp__knmkf)
    whpe__yyum += '    return ({},{})\n'.format(', '.join(ovtuu__jykbm), 
        ' out_index_arg,' if agg_node.same_index else '')
    qpp__wqbb = {}
    exec(whpe__yyum, {}, qpp__wqbb)
    fhb__xnbp = qpp__wqbb['agg_top']
    return fhb__xnbp


def compile_to_optimized_ir(func, arg_typs, typingctx, targetctx):
    code = func.code if hasattr(func, 'code') else func.__code__
    closure = func.closure if hasattr(func, 'closure') else func.__closure__
    f_ir = get_ir_of_code(func.__globals__, code)
    replace_closures(f_ir, closure, code)
    for block in f_ir.blocks.values():
        for zrfkd__dfnk in block.body:
            if is_call_assign(zrfkd__dfnk) and find_callname(f_ir,
                zrfkd__dfnk.value) == ('len', 'builtins'
                ) and zrfkd__dfnk.value.args[0].name == f_ir.arg_names[0]:
                dsrua__mfksv = get_definition(f_ir, zrfkd__dfnk.value.func)
                dsrua__mfksv.name = 'dummy_agg_count'
                dsrua__mfksv.value = dummy_agg_count
    qkyc__koqo = get_name_var_table(f_ir.blocks)
    oexjp__nqe = {}
    for name, hyo__tyv in qkyc__koqo.items():
        oexjp__nqe[name] = mk_unique_var(name)
    replace_var_names(f_ir.blocks, oexjp__nqe)
    f_ir._definitions = build_definitions(f_ir.blocks)
    assert f_ir.arg_count == 1, 'agg function should have one input'
    clbdd__eky = numba.core.compiler.Flags()
    clbdd__eky.nrt = True
    pyj__ufe = bodo.transforms.untyped_pass.UntypedPass(f_ir, typingctx,
        arg_typs, {}, {}, clbdd__eky)
    pyj__ufe.run()
    f_ir._definitions = build_definitions(f_ir.blocks)
    typemap, ttf__ewynz, calltypes, hyo__tyv = (numba.core.typed_passes.
        type_inference_stage(typingctx, targetctx, f_ir, arg_typs, None))
    egsv__huov = numba.core.cpu.ParallelOptions(True)
    targetctx = numba.core.cpu.CPUContext(typingctx)
    ctva__yicpv = namedtuple('DummyPipeline', ['typingctx', 'targetctx',
        'args', 'func_ir', 'typemap', 'return_type', 'calltypes',
        'type_annotation', 'locals', 'flags', 'pipeline'])
    cngod__ldrvo = namedtuple('TypeAnnotation', ['typemap', 'calltypes'])
    ilmf__azif = cngod__ldrvo(typemap, calltypes)
    pm = ctva__yicpv(typingctx, targetctx, None, f_ir, typemap, ttf__ewynz,
        calltypes, ilmf__azif, {}, clbdd__eky, None)
    ttyge__sufhj = (numba.core.compiler.DefaultPassBuilder.
        define_untyped_pipeline(pm))
    pm = ctva__yicpv(typingctx, targetctx, None, f_ir, typemap, ttf__ewynz,
        calltypes, ilmf__azif, {}, clbdd__eky, ttyge__sufhj)
    hrke__npes = numba.core.typed_passes.InlineOverloads()
    hrke__npes.run_pass(pm)
    uqyn__cjqoa = bodo.transforms.series_pass.SeriesPass(f_ir, typingctx,
        targetctx, typemap, calltypes, {}, False)
    uqyn__cjqoa.run()
    for block in f_ir.blocks.values():
        for zrfkd__dfnk in block.body:
            if is_assign(zrfkd__dfnk) and isinstance(zrfkd__dfnk.value, (ir
                .Arg, ir.Var)) and isinstance(typemap[zrfkd__dfnk.target.
                name], SeriesType):
                ttnnh__kva = typemap.pop(zrfkd__dfnk.target.name)
                typemap[zrfkd__dfnk.target.name] = ttnnh__kva.data
            if is_call_assign(zrfkd__dfnk) and find_callname(f_ir,
                zrfkd__dfnk.value) == ('get_series_data',
                'bodo.hiframes.pd_series_ext'):
                f_ir._definitions[zrfkd__dfnk.target.name].remove(zrfkd__dfnk
                    .value)
                zrfkd__dfnk.value = zrfkd__dfnk.value.args[0]
                f_ir._definitions[zrfkd__dfnk.target.name].append(zrfkd__dfnk
                    .value)
            if is_call_assign(zrfkd__dfnk) and find_callname(f_ir,
                zrfkd__dfnk.value) == ('isna', 'bodo.libs.array_kernels'):
                f_ir._definitions[zrfkd__dfnk.target.name].remove(zrfkd__dfnk
                    .value)
                zrfkd__dfnk.value = ir.Const(False, zrfkd__dfnk.loc)
                f_ir._definitions[zrfkd__dfnk.target.name].append(zrfkd__dfnk
                    .value)
            if is_call_assign(zrfkd__dfnk) and find_callname(f_ir,
                zrfkd__dfnk.value) == ('setna', 'bodo.libs.array_kernels'):
                f_ir._definitions[zrfkd__dfnk.target.name].remove(zrfkd__dfnk
                    .value)
                zrfkd__dfnk.value = ir.Const(False, zrfkd__dfnk.loc)
                f_ir._definitions[zrfkd__dfnk.target.name].append(zrfkd__dfnk
                    .value)
    bodo.transforms.untyped_pass.remove_dead_branches(f_ir)
    csrpn__jytp = numba.parfors.parfor.PreParforPass(f_ir, typemap,
        calltypes, typingctx, targetctx, egsv__huov)
    csrpn__jytp.run()
    f_ir._definitions = build_definitions(f_ir.blocks)
    rfuyc__tfx = numba.core.compiler.StateDict()
    rfuyc__tfx.func_ir = f_ir
    rfuyc__tfx.typemap = typemap
    rfuyc__tfx.calltypes = calltypes
    rfuyc__tfx.typingctx = typingctx
    rfuyc__tfx.targetctx = targetctx
    rfuyc__tfx.return_type = ttf__ewynz
    numba.core.rewrites.rewrite_registry.apply('after-inference', rfuyc__tfx)
    rrkl__ljo = numba.parfors.parfor.ParforPass(f_ir, typemap, calltypes,
        ttf__ewynz, typingctx, targetctx, egsv__huov, clbdd__eky, {})
    rrkl__ljo.run()
    remove_dels(f_ir.blocks)
    numba.parfors.parfor.maximize_fusion(f_ir, f_ir.blocks, typemap, False)
    return f_ir, pm


def replace_closures(f_ir, closure, code):
    if closure:
        closure = f_ir.get_definition(closure)
        if isinstance(closure, tuple):
            key__cge = ctypes.pythonapi.PyCell_Get
            key__cge.restype = ctypes.py_object
            key__cge.argtypes = ctypes.py_object,
            bru__mnlrx = tuple(key__cge(xbx__pun) for xbx__pun in closure)
        else:
            assert isinstance(closure, ir.Expr) and closure.op == 'build_tuple'
            bru__mnlrx = closure.items
        assert len(code.co_freevars) == len(bru__mnlrx)
        numba.core.inline_closurecall._replace_freevars(f_ir.blocks, bru__mnlrx
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
        nydib__cjzv = SeriesType(in_col_typ.dtype, in_col_typ, None,
            string_type)
        f_ir, pm = compile_to_optimized_ir(func, (nydib__cjzv,), self.
            typingctx, self.targetctx)
        f_ir._definitions = build_definitions(f_ir.blocks)
        assert len(f_ir.blocks
            ) == 1 and 0 in f_ir.blocks, 'only simple functions with one block supported for aggregation'
        block = f_ir.blocks[0]
        jsj__rafq, arr_var = _rm_arg_agg_block(block, pm.typemap)
        xaj__bkd = -1
        for eyhid__zifl, zrfkd__dfnk in enumerate(jsj__rafq):
            if isinstance(zrfkd__dfnk, numba.parfors.parfor.Parfor):
                assert xaj__bkd == -1, 'only one parfor for aggregation function'
                xaj__bkd = eyhid__zifl
        parfor = None
        if xaj__bkd != -1:
            parfor = jsj__rafq[xaj__bkd]
            remove_dels(parfor.loop_body)
            remove_dels({(0): parfor.init_block})
        init_nodes = []
        if parfor:
            init_nodes = jsj__rafq[:xaj__bkd] + parfor.init_block.body
        eval_nodes = jsj__rafq[xaj__bkd + 1:]
        redvars = []
        var_to_redvar = {}
        if parfor:
            redvars, var_to_redvar = get_parfor_reductions(parfor, parfor.
                params, pm.calltypes)
        func.ncols_pre_shuffle = len(redvars)
        func.ncols_post_shuffle = len(redvars) + 1
        func.n_redvars = len(redvars)
        reduce_vars = [0] * len(redvars)
        for zrfkd__dfnk in init_nodes:
            if is_assign(zrfkd__dfnk) and zrfkd__dfnk.target.name in redvars:
                ind = redvars.index(zrfkd__dfnk.target.name)
                reduce_vars[ind] = zrfkd__dfnk.target
        var_types = [pm.typemap[mis__xixm] for mis__xixm in redvars]
        yhj__zoxm = gen_combine_func(f_ir, parfor, redvars, var_to_redvar,
            var_types, arr_var, pm, self.typingctx, self.targetctx)
        init_nodes = _mv_read_only_init_vars(init_nodes, parfor, eval_nodes)
        bos__ffne = gen_update_func(parfor, redvars, var_to_redvar,
            var_types, arr_var, in_col_typ, pm, self.typingctx, self.targetctx)
        dqp__demt = gen_eval_func(f_ir, eval_nodes, reduce_vars, var_types,
            pm, self.typingctx, self.targetctx)
        self.all_reduce_vars += reduce_vars
        self.all_vartypes += var_types
        self.all_init_nodes += init_nodes
        self.all_eval_funcs.append(dqp__demt)
        self.all_update_funcs.append(bos__ffne)
        self.all_combine_funcs.append(yhj__zoxm)
        self.curr_offset += len(redvars)
        self.redvar_offsets.append(self.curr_offset)

    def gen_all_func(self):
        if len(self.all_update_funcs) == 0:
            return None
        self.all_vartypes = self.all_vartypes * len(self.pivot_values
            ) if self.pivot_values is not None else self.all_vartypes
        self.all_reduce_vars = self.all_reduce_vars * len(self.pivot_values
            ) if self.pivot_values is not None else self.all_reduce_vars
        bante__ttoyl = gen_init_func(self.all_init_nodes, self.
            all_reduce_vars, self.all_vartypes, self.typingctx, self.targetctx)
        roqf__txtqt = gen_all_update_func(self.all_update_funcs, self.
            all_vartypes, self.in_col_types, self.redvar_offsets, self.
            typingctx, self.targetctx, self.pivot_typ, self.pivot_values,
            self.is_crosstab)
        conpc__lpo = gen_all_combine_func(self.all_combine_funcs, self.
            all_vartypes, self.redvar_offsets, self.typingctx, self.
            targetctx, self.pivot_typ, self.pivot_values)
        wpbcx__enk = gen_all_eval_func(self.all_eval_funcs, self.
            all_vartypes, self.redvar_offsets, self.out_col_types, self.
            typingctx, self.targetctx, self.pivot_values)
        return (self.all_vartypes, bante__ttoyl, roqf__txtqt, conpc__lpo,
            wpbcx__enk)


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
    ramgr__oiwuk = []
    for t, bajni__otmxw in zip(in_col_types, agg_func):
        ramgr__oiwuk.append((t, bajni__otmxw))
    ymz__qtiwn = RegularUDFGenerator(in_col_types, out_col_types, pivot_typ,
        pivot_values, is_crosstab, typingctx, targetctx)
    rinwj__cyamz = GeneralUDFGenerator()
    for in_col_typ, func in ramgr__oiwuk:
        if func.ftype not in ('udf', 'gen_udf'):
            continue
        try:
            ymz__qtiwn.add_udf(in_col_typ, func)
        except:
            rinwj__cyamz.add_udf(func)
            func.ftype = 'gen_udf'
    regular_udf_funcs = ymz__qtiwn.gen_all_func()
    general_udf_funcs = rinwj__cyamz.gen_all_func()
    if regular_udf_funcs is not None or general_udf_funcs is not None:
        return AggUDFStruct(regular_udf_funcs, general_udf_funcs)
    else:
        return None


def _mv_read_only_init_vars(init_nodes, parfor, eval_nodes):
    if not parfor:
        return init_nodes
    bnto__fbpn = compute_use_defs(parfor.loop_body)
    pkvn__dojl = set()
    for vjngs__jttii in bnto__fbpn.usemap.values():
        pkvn__dojl |= vjngs__jttii
    qxd__apea = set()
    for vjngs__jttii in bnto__fbpn.defmap.values():
        qxd__apea |= vjngs__jttii
    fge__nzbqb = ir.Block(ir.Scope(None, parfor.loc), parfor.loc)
    fge__nzbqb.body = eval_nodes
    cgkey__frg = compute_use_defs({(0): fge__nzbqb})
    pkmh__oqmp = cgkey__frg.usemap[0]
    zsz__vexso = set()
    jsrhp__uojd = []
    tny__eiqfw = []
    for zrfkd__dfnk in reversed(init_nodes):
        aqy__yjqzc = {mis__xixm.name for mis__xixm in zrfkd__dfnk.list_vars()}
        if is_assign(zrfkd__dfnk):
            mis__xixm = zrfkd__dfnk.target.name
            aqy__yjqzc.remove(mis__xixm)
            if (mis__xixm in pkvn__dojl and mis__xixm not in zsz__vexso and
                mis__xixm not in pkmh__oqmp and mis__xixm not in qxd__apea):
                tny__eiqfw.append(zrfkd__dfnk)
                pkvn__dojl |= aqy__yjqzc
                qxd__apea.add(mis__xixm)
                continue
        zsz__vexso |= aqy__yjqzc
        jsrhp__uojd.append(zrfkd__dfnk)
    tny__eiqfw.reverse()
    jsrhp__uojd.reverse()
    dzqxh__sea = min(parfor.loop_body.keys())
    rlg__ubtva = parfor.loop_body[dzqxh__sea]
    rlg__ubtva.body = tny__eiqfw + rlg__ubtva.body
    return jsrhp__uojd


def gen_init_func(init_nodes, reduce_vars, var_types, typingctx, targetctx):
    noeqa__gjciq = (numba.parfors.parfor.max_checker, numba.parfors.parfor.
        min_checker, numba.parfors.parfor.argmax_checker, numba.parfors.
        parfor.argmin_checker)
    laet__fcjkk = set()
    sle__vxss = []
    for zrfkd__dfnk in init_nodes:
        if is_assign(zrfkd__dfnk) and isinstance(zrfkd__dfnk.value, ir.Global
            ) and isinstance(zrfkd__dfnk.value.value, pytypes.FunctionType
            ) and zrfkd__dfnk.value.value in noeqa__gjciq:
            laet__fcjkk.add(zrfkd__dfnk.target.name)
        elif is_call_assign(zrfkd__dfnk
            ) and zrfkd__dfnk.value.func.name in laet__fcjkk:
            pass
        else:
            sle__vxss.append(zrfkd__dfnk)
    init_nodes = sle__vxss
    iqmzg__ywd = types.Tuple(var_types)
    nzxtm__fujgu = lambda : None
    f_ir = compile_to_numba_ir(nzxtm__fujgu, {})
    block = list(f_ir.blocks.values())[0]
    loc = block.loc
    hsfz__sqmy = ir.Var(block.scope, mk_unique_var('init_tup'), loc)
    vdbj__hylcc = ir.Assign(ir.Expr.build_tuple(reduce_vars, loc),
        hsfz__sqmy, loc)
    block.body = block.body[-2:]
    block.body = init_nodes + [vdbj__hylcc] + block.body
    block.body[-2].value.value = hsfz__sqmy
    hsy__drq = compiler.compile_ir(typingctx, targetctx, f_ir, (),
        iqmzg__ywd, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    wqfqa__csf = numba.core.target_extension.dispatcher_registry[cpu_target](
        nzxtm__fujgu)
    wqfqa__csf.add_overload(hsy__drq)
    return wqfqa__csf


def gen_all_update_func(update_funcs, reduce_var_types, in_col_types,
    redvar_offsets, typingctx, targetctx, pivot_typ, pivot_values, is_crosstab
    ):
    ibty__ufr = len(update_funcs)
    vid__jyfdf = len(in_col_types)
    if pivot_values is not None:
        assert vid__jyfdf == 1
    whpe__yyum = (
        'def update_all_f(redvar_arrs, data_in, w_ind, i, pivot_arr):\n')
    if pivot_values is not None:
        gvl__ycs = redvar_offsets[vid__jyfdf]
        whpe__yyum += '  pv = pivot_arr[i]\n'
        for sdy__huig, dxh__rzj in enumerate(pivot_values):
            fgx__sgz = 'el' if sdy__huig != 0 else ''
            whpe__yyum += "  {}if pv == '{}':\n".format(fgx__sgz, dxh__rzj)
            uti__fssa = gvl__ycs * sdy__huig
            dptdd__llsw = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                eyhid__zifl) for eyhid__zifl in range(uti__fssa +
                redvar_offsets[0], uti__fssa + redvar_offsets[1])])
            ywo__zag = 'data_in[0][i]'
            if is_crosstab:
                ywo__zag = '0'
            whpe__yyum += '    {} = update_vars_0({}, {})\n'.format(dptdd__llsw
                , dptdd__llsw, ywo__zag)
    else:
        for sdy__huig in range(ibty__ufr):
            dptdd__llsw = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                eyhid__zifl) for eyhid__zifl in range(redvar_offsets[
                sdy__huig], redvar_offsets[sdy__huig + 1])])
            if dptdd__llsw:
                whpe__yyum += ('  {} = update_vars_{}({},  data_in[{}][i])\n'
                    .format(dptdd__llsw, sdy__huig, dptdd__llsw, 0 if 
                    vid__jyfdf == 1 else sdy__huig))
    whpe__yyum += '  return\n'
    pomj__wqnn = {}
    for eyhid__zifl, bajni__otmxw in enumerate(update_funcs):
        pomj__wqnn['update_vars_{}'.format(eyhid__zifl)] = bajni__otmxw
    qpp__wqbb = {}
    exec(whpe__yyum, pomj__wqnn, qpp__wqbb)
    rdlin__wqvnl = qpp__wqbb['update_all_f']
    return numba.njit(no_cpython_wrapper=True)(rdlin__wqvnl)


def gen_all_combine_func(combine_funcs, reduce_var_types, redvar_offsets,
    typingctx, targetctx, pivot_typ, pivot_values):
    spk__rmkxm = types.Tuple([types.Array(t, 1, 'C') for t in reduce_var_types]
        )
    arg_typs = spk__rmkxm, spk__rmkxm, types.intp, types.intp, pivot_typ
    tbdcz__yhqvk = len(redvar_offsets) - 1
    gvl__ycs = redvar_offsets[tbdcz__yhqvk]
    whpe__yyum = (
        'def combine_all_f(redvar_arrs, recv_arrs, w_ind, i, pivot_arr):\n')
    if pivot_values is not None:
        assert tbdcz__yhqvk == 1
        for myfr__ohxk in range(len(pivot_values)):
            uti__fssa = gvl__ycs * myfr__ohxk
            dptdd__llsw = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                eyhid__zifl) for eyhid__zifl in range(uti__fssa +
                redvar_offsets[0], uti__fssa + redvar_offsets[1])])
            wsxfh__tgzyz = ', '.join(['recv_arrs[{}][i]'.format(eyhid__zifl
                ) for eyhid__zifl in range(uti__fssa + redvar_offsets[0], 
                uti__fssa + redvar_offsets[1])])
            whpe__yyum += '  {} = combine_vars_0({}, {})\n'.format(dptdd__llsw,
                dptdd__llsw, wsxfh__tgzyz)
    else:
        for sdy__huig in range(tbdcz__yhqvk):
            dptdd__llsw = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                eyhid__zifl) for eyhid__zifl in range(redvar_offsets[
                sdy__huig], redvar_offsets[sdy__huig + 1])])
            wsxfh__tgzyz = ', '.join(['recv_arrs[{}][i]'.format(eyhid__zifl
                ) for eyhid__zifl in range(redvar_offsets[sdy__huig],
                redvar_offsets[sdy__huig + 1])])
            if wsxfh__tgzyz:
                whpe__yyum += '  {} = combine_vars_{}({}, {})\n'.format(
                    dptdd__llsw, sdy__huig, dptdd__llsw, wsxfh__tgzyz)
    whpe__yyum += '  return\n'
    pomj__wqnn = {}
    for eyhid__zifl, bajni__otmxw in enumerate(combine_funcs):
        pomj__wqnn['combine_vars_{}'.format(eyhid__zifl)] = bajni__otmxw
    qpp__wqbb = {}
    exec(whpe__yyum, pomj__wqnn, qpp__wqbb)
    qfjwo__cxs = qpp__wqbb['combine_all_f']
    f_ir = compile_to_numba_ir(qfjwo__cxs, pomj__wqnn)
    conpc__lpo = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        types.none, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    wqfqa__csf = numba.core.target_extension.dispatcher_registry[cpu_target](
        qfjwo__cxs)
    wqfqa__csf.add_overload(conpc__lpo)
    return wqfqa__csf


def gen_all_eval_func(eval_funcs, reduce_var_types, redvar_offsets,
    out_col_typs, typingctx, targetctx, pivot_values):
    spk__rmkxm = types.Tuple([types.Array(t, 1, 'C') for t in reduce_var_types]
        )
    out_col_typs = types.Tuple(out_col_typs)
    tbdcz__yhqvk = len(redvar_offsets) - 1
    gvl__ycs = redvar_offsets[tbdcz__yhqvk]
    whpe__yyum = 'def eval_all_f(redvar_arrs, out_arrs, j):\n'
    if pivot_values is not None:
        assert tbdcz__yhqvk == 1
        for sdy__huig in range(len(pivot_values)):
            uti__fssa = gvl__ycs * sdy__huig
            dptdd__llsw = ', '.join(['redvar_arrs[{}][j]'.format(
                eyhid__zifl) for eyhid__zifl in range(uti__fssa +
                redvar_offsets[0], uti__fssa + redvar_offsets[1])])
            whpe__yyum += '  out_arrs[{}][j] = eval_vars_0({})\n'.format(
                sdy__huig, dptdd__llsw)
    else:
        for sdy__huig in range(tbdcz__yhqvk):
            dptdd__llsw = ', '.join(['redvar_arrs[{}][j]'.format(
                eyhid__zifl) for eyhid__zifl in range(redvar_offsets[
                sdy__huig], redvar_offsets[sdy__huig + 1])])
            whpe__yyum += '  out_arrs[{}][j] = eval_vars_{}({})\n'.format(
                sdy__huig, sdy__huig, dptdd__llsw)
    whpe__yyum += '  return\n'
    pomj__wqnn = {}
    for eyhid__zifl, bajni__otmxw in enumerate(eval_funcs):
        pomj__wqnn['eval_vars_{}'.format(eyhid__zifl)] = bajni__otmxw
    qpp__wqbb = {}
    exec(whpe__yyum, pomj__wqnn, qpp__wqbb)
    dhp__bcno = qpp__wqbb['eval_all_f']
    return numba.njit(no_cpython_wrapper=True)(dhp__bcno)


def gen_eval_func(f_ir, eval_nodes, reduce_vars, var_types, pm, typingctx,
    targetctx):
    jpde__pzf = len(var_types)
    rnuz__awplm = [f'in{eyhid__zifl}' for eyhid__zifl in range(jpde__pzf)]
    iqmzg__ywd = types.unliteral(pm.typemap[eval_nodes[-1].value.name])
    zkwrt__vcp = iqmzg__ywd(0)
    whpe__yyum = 'def agg_eval({}):\n return _zero\n'.format(', '.join(
        rnuz__awplm))
    qpp__wqbb = {}
    exec(whpe__yyum, {'_zero': zkwrt__vcp}, qpp__wqbb)
    shhfq__kxtad = qpp__wqbb['agg_eval']
    arg_typs = tuple(var_types)
    f_ir = compile_to_numba_ir(shhfq__kxtad, {'numba': numba, 'bodo': bodo,
        'np': np, '_zero': zkwrt__vcp}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=arg_typs, typemap=pm.typemap, calltypes=pm.
        calltypes)
    block = list(f_ir.blocks.values())[0]
    yqn__tkrhy = []
    for eyhid__zifl, mis__xixm in enumerate(reduce_vars):
        yqn__tkrhy.append(ir.Assign(block.body[eyhid__zifl].target,
            mis__xixm, mis__xixm.loc))
        for rufpl__tddj in mis__xixm.versioned_names:
            yqn__tkrhy.append(ir.Assign(mis__xixm, ir.Var(mis__xixm.scope,
                rufpl__tddj, mis__xixm.loc), mis__xixm.loc))
    block.body = block.body[:jpde__pzf] + yqn__tkrhy + eval_nodes
    dqp__demt = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        iqmzg__ywd, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    wqfqa__csf = numba.core.target_extension.dispatcher_registry[cpu_target](
        shhfq__kxtad)
    wqfqa__csf.add_overload(dqp__demt)
    return wqfqa__csf


def gen_combine_func(f_ir, parfor, redvars, var_to_redvar, var_types,
    arr_var, pm, typingctx, targetctx):
    if not parfor:
        return numba.njit(lambda : ())
    jpde__pzf = len(redvars)
    ved__dllbq = [f'v{eyhid__zifl}' for eyhid__zifl in range(jpde__pzf)]
    rnuz__awplm = [f'in{eyhid__zifl}' for eyhid__zifl in range(jpde__pzf)]
    whpe__yyum = 'def agg_combine({}):\n'.format(', '.join(ved__dllbq +
        rnuz__awplm))
    gqxj__hoj = wrap_parfor_blocks(parfor)
    nhctt__usxq = find_topo_order(gqxj__hoj)
    nhctt__usxq = nhctt__usxq[1:]
    unwrap_parfor_blocks(parfor)
    mlce__zont = {}
    eyptc__nqqg = []
    for vbts__cglsg in nhctt__usxq:
        zdzr__pbfw = parfor.loop_body[vbts__cglsg]
        for zrfkd__dfnk in zdzr__pbfw.body:
            if is_call_assign(zrfkd__dfnk) and guard(find_callname, f_ir,
                zrfkd__dfnk.value) == ('__special_combine', 'bodo.ir.aggregate'
                ):
                args = zrfkd__dfnk.value.args
                juhjh__liva = []
                edymx__abbjm = []
                for mis__xixm in args[:-1]:
                    ind = redvars.index(mis__xixm.name)
                    eyptc__nqqg.append(ind)
                    juhjh__liva.append('v{}'.format(ind))
                    edymx__abbjm.append('in{}'.format(ind))
                wxa__asa = '__special_combine__{}'.format(len(mlce__zont))
                whpe__yyum += '    ({},) = {}({})\n'.format(', '.join(
                    juhjh__liva), wxa__asa, ', '.join(juhjh__liva +
                    edymx__abbjm))
                suues__wjhi = ir.Expr.call(args[-1], [], (), zdzr__pbfw.loc)
                fzvd__juofm = guard(find_callname, f_ir, suues__wjhi)
                assert fzvd__juofm == ('_var_combine', 'bodo.ir.aggregate')
                fzvd__juofm = bodo.ir.aggregate._var_combine
                mlce__zont[wxa__asa] = fzvd__juofm
            if is_assign(zrfkd__dfnk) and zrfkd__dfnk.target.name in redvars:
                rmn__turgk = zrfkd__dfnk.target.name
                ind = redvars.index(rmn__turgk)
                if ind in eyptc__nqqg:
                    continue
                if len(f_ir._definitions[rmn__turgk]) == 2:
                    var_def = f_ir._definitions[rmn__turgk][0]
                    whpe__yyum += _match_reduce_def(var_def, f_ir, ind)
                    var_def = f_ir._definitions[rmn__turgk][1]
                    whpe__yyum += _match_reduce_def(var_def, f_ir, ind)
    whpe__yyum += '    return {}'.format(', '.join(['v{}'.format(
        eyhid__zifl) for eyhid__zifl in range(jpde__pzf)]))
    qpp__wqbb = {}
    exec(whpe__yyum, {}, qpp__wqbb)
    cwii__zxiuu = qpp__wqbb['agg_combine']
    arg_typs = tuple(2 * var_types)
    pomj__wqnn = {'numba': numba, 'bodo': bodo, 'np': np}
    pomj__wqnn.update(mlce__zont)
    f_ir = compile_to_numba_ir(cwii__zxiuu, pomj__wqnn, typingctx=typingctx,
        targetctx=targetctx, arg_typs=arg_typs, typemap=pm.typemap,
        calltypes=pm.calltypes)
    block = list(f_ir.blocks.values())[0]
    iqmzg__ywd = pm.typemap[block.body[-1].value.name]
    yhj__zoxm = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        iqmzg__ywd, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    wqfqa__csf = numba.core.target_extension.dispatcher_registry[cpu_target](
        cwii__zxiuu)
    wqfqa__csf.add_overload(yhj__zoxm)
    return wqfqa__csf


def _match_reduce_def(var_def, f_ir, ind):
    whpe__yyum = ''
    while isinstance(var_def, ir.Var):
        var_def = guard(get_definition, f_ir, var_def)
    if isinstance(var_def, ir.Expr
        ) and var_def.op == 'inplace_binop' and var_def.fn in ('+=',
        operator.iadd):
        whpe__yyum = '    v{} += in{}\n'.format(ind, ind)
    if isinstance(var_def, ir.Expr) and var_def.op == 'call':
        bjh__aux = guard(find_callname, f_ir, var_def)
        if bjh__aux == ('min', 'builtins'):
            whpe__yyum = '    v{} = min(v{}, in{})\n'.format(ind, ind, ind)
        if bjh__aux == ('max', 'builtins'):
            whpe__yyum = '    v{} = max(v{}, in{})\n'.format(ind, ind, ind)
    return whpe__yyum


def gen_update_func(parfor, redvars, var_to_redvar, var_types, arr_var,
    in_col_typ, pm, typingctx, targetctx):
    if not parfor:
        return numba.njit(lambda A: ())
    jpde__pzf = len(redvars)
    mmtw__tlvuv = 1
    rxxo__rckm = []
    for eyhid__zifl in range(mmtw__tlvuv):
        phtxa__ralgd = ir.Var(arr_var.scope, f'$input{eyhid__zifl}',
            arr_var.loc)
        rxxo__rckm.append(phtxa__ralgd)
    uvqde__kqqmv = parfor.loop_nests[0].index_variable
    xpwc__gvdx = [0] * jpde__pzf
    for zdzr__pbfw in parfor.loop_body.values():
        arro__bam = []
        for zrfkd__dfnk in zdzr__pbfw.body:
            if is_var_assign(zrfkd__dfnk
                ) and zrfkd__dfnk.value.name == uvqde__kqqmv.name:
                continue
            if is_getitem(zrfkd__dfnk
                ) and zrfkd__dfnk.value.value.name == arr_var.name:
                zrfkd__dfnk.value = rxxo__rckm[0]
            if is_call_assign(zrfkd__dfnk) and guard(find_callname, pm.
                func_ir, zrfkd__dfnk.value) == ('isna',
                'bodo.libs.array_kernels') and zrfkd__dfnk.value.args[0
                ].name == arr_var.name:
                zrfkd__dfnk.value = ir.Const(False, zrfkd__dfnk.target.loc)
            if is_assign(zrfkd__dfnk) and zrfkd__dfnk.target.name in redvars:
                ind = redvars.index(zrfkd__dfnk.target.name)
                xpwc__gvdx[ind] = zrfkd__dfnk.target
            arro__bam.append(zrfkd__dfnk)
        zdzr__pbfw.body = arro__bam
    ved__dllbq = ['v{}'.format(eyhid__zifl) for eyhid__zifl in range(jpde__pzf)
        ]
    rnuz__awplm = ['in{}'.format(eyhid__zifl) for eyhid__zifl in range(
        mmtw__tlvuv)]
    whpe__yyum = 'def agg_update({}):\n'.format(', '.join(ved__dllbq +
        rnuz__awplm))
    whpe__yyum += '    __update_redvars()\n'
    whpe__yyum += '    return {}'.format(', '.join(['v{}'.format(
        eyhid__zifl) for eyhid__zifl in range(jpde__pzf)]))
    qpp__wqbb = {}
    exec(whpe__yyum, {}, qpp__wqbb)
    brhew__dur = qpp__wqbb['agg_update']
    arg_typs = tuple(var_types + [in_col_typ.dtype] * mmtw__tlvuv)
    f_ir = compile_to_numba_ir(brhew__dur, {'__update_redvars':
        __update_redvars}, typingctx=typingctx, targetctx=targetctx,
        arg_typs=arg_typs, typemap=pm.typemap, calltypes=pm.calltypes)
    f_ir._definitions = build_definitions(f_ir.blocks)
    arf__qsq = f_ir.blocks.popitem()[1].body
    iqmzg__ywd = pm.typemap[arf__qsq[-1].value.name]
    gqxj__hoj = wrap_parfor_blocks(parfor)
    nhctt__usxq = find_topo_order(gqxj__hoj)
    nhctt__usxq = nhctt__usxq[1:]
    unwrap_parfor_blocks(parfor)
    f_ir.blocks = parfor.loop_body
    rlg__ubtva = f_ir.blocks[nhctt__usxq[0]]
    ukoz__ezstj = f_ir.blocks[nhctt__usxq[-1]]
    ucobi__urt = arf__qsq[:jpde__pzf + mmtw__tlvuv]
    if jpde__pzf > 1:
        fbs__pnw = arf__qsq[-3:]
        assert is_assign(fbs__pnw[0]) and isinstance(fbs__pnw[0].value, ir.Expr
            ) and fbs__pnw[0].value.op == 'build_tuple'
    else:
        fbs__pnw = arf__qsq[-2:]
    for eyhid__zifl in range(jpde__pzf):
        ksw__jrf = arf__qsq[eyhid__zifl].target
        mnhn__bekma = ir.Assign(ksw__jrf, xpwc__gvdx[eyhid__zifl], ksw__jrf.loc
            )
        ucobi__urt.append(mnhn__bekma)
    for eyhid__zifl in range(jpde__pzf, jpde__pzf + mmtw__tlvuv):
        ksw__jrf = arf__qsq[eyhid__zifl].target
        mnhn__bekma = ir.Assign(ksw__jrf, rxxo__rckm[eyhid__zifl -
            jpde__pzf], ksw__jrf.loc)
        ucobi__urt.append(mnhn__bekma)
    rlg__ubtva.body = ucobi__urt + rlg__ubtva.body
    jljvi__gkxkv = []
    for eyhid__zifl in range(jpde__pzf):
        ksw__jrf = arf__qsq[eyhid__zifl].target
        mnhn__bekma = ir.Assign(xpwc__gvdx[eyhid__zifl], ksw__jrf, ksw__jrf.loc
            )
        jljvi__gkxkv.append(mnhn__bekma)
    ukoz__ezstj.body += jljvi__gkxkv + fbs__pnw
    izs__cdyo = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        iqmzg__ywd, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    wqfqa__csf = numba.core.target_extension.dispatcher_registry[cpu_target](
        brhew__dur)
    wqfqa__csf.add_overload(izs__cdyo)
    return wqfqa__csf


def _rm_arg_agg_block(block, typemap):
    jsj__rafq = []
    arr_var = None
    for eyhid__zifl, zrfkd__dfnk in enumerate(block.body):
        if is_assign(zrfkd__dfnk) and isinstance(zrfkd__dfnk.value, ir.Arg):
            arr_var = zrfkd__dfnk.target
            mbx__khky = typemap[arr_var.name]
            if not isinstance(mbx__khky, types.ArrayCompatible):
                jsj__rafq += block.body[eyhid__zifl + 1:]
                break
            lyxv__clwck = block.body[eyhid__zifl + 1]
            assert is_assign(lyxv__clwck) and isinstance(lyxv__clwck.value,
                ir.Expr
                ) and lyxv__clwck.value.op == 'getattr' and lyxv__clwck.value.attr == 'shape' and lyxv__clwck.value.value.name == arr_var.name
            wai__zpjp = lyxv__clwck.target
            bwf__youh = block.body[eyhid__zifl + 2]
            assert is_assign(bwf__youh) and isinstance(bwf__youh.value, ir.Expr
                ) and bwf__youh.value.op == 'static_getitem' and bwf__youh.value.value.name == wai__zpjp.name
            jsj__rafq += block.body[eyhid__zifl + 3:]
            break
        jsj__rafq.append(zrfkd__dfnk)
    return jsj__rafq, arr_var


def get_parfor_reductions(parfor, parfor_params, calltypes, reduce_varnames
    =None, param_uses=None, var_to_param=None):
    if reduce_varnames is None:
        reduce_varnames = []
    if param_uses is None:
        param_uses = defaultdict(list)
    if var_to_param is None:
        var_to_param = {}
    gqxj__hoj = wrap_parfor_blocks(parfor)
    nhctt__usxq = find_topo_order(gqxj__hoj)
    nhctt__usxq = nhctt__usxq[1:]
    unwrap_parfor_blocks(parfor)
    for vbts__cglsg in reversed(nhctt__usxq):
        for zrfkd__dfnk in reversed(parfor.loop_body[vbts__cglsg].body):
            if isinstance(zrfkd__dfnk, ir.Assign) and (zrfkd__dfnk.target.
                name in parfor_params or zrfkd__dfnk.target.name in
                var_to_param):
                vjzk__efxrr = zrfkd__dfnk.target.name
                rhs = zrfkd__dfnk.value
                agl__szzcf = (vjzk__efxrr if vjzk__efxrr in parfor_params else
                    var_to_param[vjzk__efxrr])
                eldk__nugsn = []
                if isinstance(rhs, ir.Var):
                    eldk__nugsn = [rhs.name]
                elif isinstance(rhs, ir.Expr):
                    eldk__nugsn = [mis__xixm.name for mis__xixm in
                        zrfkd__dfnk.value.list_vars()]
                param_uses[agl__szzcf].extend(eldk__nugsn)
                for mis__xixm in eldk__nugsn:
                    var_to_param[mis__xixm] = agl__szzcf
            if isinstance(zrfkd__dfnk, Parfor):
                get_parfor_reductions(zrfkd__dfnk, parfor_params, calltypes,
                    reduce_varnames, param_uses, var_to_param)
    for uaarz__ifurk, eldk__nugsn in param_uses.items():
        if uaarz__ifurk in eldk__nugsn and uaarz__ifurk not in reduce_varnames:
            reduce_varnames.append(uaarz__ifurk)
    return reduce_varnames, var_to_param


@numba.extending.register_jitable
def dummy_agg_count(A):
    return len(A)
