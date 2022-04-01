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
            wci__soyz = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer()])
            tqvh__vraf = cgutils.get_or_insert_function(builder.module,
                wci__soyz, sym._literal_value)
            builder.call(tqvh__vraf, [context.get_constant_null(sig.args[0])])
        elif sig == types.none(types.int64, types.voidptr, types.voidptr):
            wci__soyz = lir.FunctionType(lir.VoidType(), [lir.IntType(64),
                lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
            tqvh__vraf = cgutils.get_or_insert_function(builder.module,
                wci__soyz, sym._literal_value)
            builder.call(tqvh__vraf, [context.get_constant(types.int64, 0),
                context.get_constant_null(sig.args[1]), context.
                get_constant_null(sig.args[2])])
        else:
            wci__soyz = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64).
                as_pointer()])
            tqvh__vraf = cgutils.get_or_insert_function(builder.module,
                wci__soyz, sym._literal_value)
            builder.call(tqvh__vraf, [context.get_constant_null(sig.args[0]
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
        nlisx__cxv = True
        flu__jfyp = 1
        lmahf__cbi = -1
        if isinstance(rhs, ir.Expr):
            for xusyh__kyx in rhs.kws:
                if func_name in list_cumulative:
                    if xusyh__kyx[0] == 'skipna':
                        nlisx__cxv = guard(find_const, func_ir, xusyh__kyx[1])
                        if not isinstance(nlisx__cxv, bool):
                            raise BodoError(
                                'For {} argument of skipna should be a boolean'
                                .format(func_name))
                if func_name == 'nunique':
                    if xusyh__kyx[0] == 'dropna':
                        nlisx__cxv = guard(find_const, func_ir, xusyh__kyx[1])
                        if not isinstance(nlisx__cxv, bool):
                            raise BodoError(
                                'argument of dropna to nunique should be a boolean'
                                )
        if func_name == 'shift' and (len(rhs.args) > 0 or len(rhs.kws) > 0):
            flu__jfyp = get_call_expr_arg('shift', rhs.args, dict(rhs.kws),
                0, 'periods', flu__jfyp)
            flu__jfyp = guard(find_const, func_ir, flu__jfyp)
        if func_name == 'head':
            lmahf__cbi = get_call_expr_arg('head', rhs.args, dict(rhs.kws),
                0, 'n', 5)
            if not isinstance(lmahf__cbi, int):
                lmahf__cbi = guard(find_const, func_ir, lmahf__cbi)
            if lmahf__cbi < 0:
                raise BodoError(
                    f'groupby.{func_name} does not work with negative values.')
        func.skipdropna = nlisx__cxv
        func.periods = flu__jfyp
        func.head_n = lmahf__cbi
        if func_name == 'transform':
            kws = dict(rhs.kws)
            ifbv__wcbaj = get_call_expr_arg(func_name, rhs.args, kws, 0,
                'func', '')
            yvn__ewi = typemap[ifbv__wcbaj.name]
            qirdh__sna = None
            if isinstance(yvn__ewi, str):
                qirdh__sna = yvn__ewi
            elif is_overload_constant_str(yvn__ewi):
                qirdh__sna = get_overload_const_str(yvn__ewi)
            elif bodo.utils.typing.is_builtin_function(yvn__ewi):
                qirdh__sna = bodo.utils.typing.get_builtin_function_name(
                    yvn__ewi)
            if qirdh__sna not in bodo.ir.aggregate.supported_transform_funcs[:
                ]:
                raise BodoError(f'unsupported transform function {qirdh__sna}')
            func.transform_func = supported_agg_funcs.index(qirdh__sna)
        else:
            func.transform_func = supported_agg_funcs.index('no_op')
        return func
    assert func_name in ['agg', 'aggregate']
    assert typemap is not None
    kws = dict(rhs.kws)
    ifbv__wcbaj = get_call_expr_arg(func_name, rhs.args, kws, 0, 'func', '')
    if ifbv__wcbaj == '':
        yvn__ewi = types.none
    else:
        yvn__ewi = typemap[ifbv__wcbaj.name]
    if is_overload_constant_dict(yvn__ewi):
        sdplf__mmh = get_overload_constant_dict(yvn__ewi)
        ilup__vkfk = [get_agg_func_udf(func_ir, f_val, rhs, series_type,
            typemap) for f_val in sdplf__mmh.values()]
        return ilup__vkfk
    if yvn__ewi == types.none:
        return [get_agg_func_udf(func_ir, get_literal_value(typemap[f_val.
            name])[1], rhs, series_type, typemap) for f_val in kws.values()]
    if isinstance(yvn__ewi, types.BaseTuple):
        ilup__vkfk = []
        vhg__xmcm = 0
        for t in yvn__ewi.types:
            if is_overload_constant_str(t):
                func_name = get_overload_const_str(t)
                ilup__vkfk.append(get_agg_func(func_ir, func_name, rhs,
                    series_type, typemap))
            else:
                assert typemap is not None, 'typemap is required for agg UDF handling'
                func = _get_const_agg_func(t, func_ir)
                func.ftype = 'udf'
                func.fname = _get_udf_name(func)
                if func.fname == '<lambda>':
                    func.fname = '<lambda_' + str(vhg__xmcm) + '>'
                    vhg__xmcm += 1
                ilup__vkfk.append(func)
        return [ilup__vkfk]
    if is_overload_constant_str(yvn__ewi):
        func_name = get_overload_const_str(yvn__ewi)
        return get_agg_func(func_ir, func_name, rhs, series_type, typemap)
    if bodo.utils.typing.is_builtin_function(yvn__ewi):
        func_name = bodo.utils.typing.get_builtin_function_name(yvn__ewi)
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
        vhg__xmcm = 0
        sfzlt__ghojz = []
        for pwthh__kjwsu in f_val:
            func = get_agg_func_udf(func_ir, pwthh__kjwsu, rhs, series_type,
                typemap)
            if func.fname == '<lambda>' and len(f_val) > 1:
                func.fname = f'<lambda_{vhg__xmcm}>'
                vhg__xmcm += 1
            sfzlt__ghojz.append(func)
        return sfzlt__ghojz
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
    qirdh__sna = code.co_name
    return qirdh__sna


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
            kmlfp__zehb = types.DType(args[0])
            return signature(kmlfp__zehb, *args)


@numba.njit(no_cpython_wrapper=True)
def _var_combine(ssqdm_a, mean_a, nobs_a, ssqdm_b, mean_b, nobs_b):
    gxnd__usn = nobs_a + nobs_b
    oyft__mcc = (nobs_a * mean_a + nobs_b * mean_b) / gxnd__usn
    ghppg__irflh = mean_b - mean_a
    qlf__wam = (ssqdm_a + ssqdm_b + ghppg__irflh * ghppg__irflh * nobs_a *
        nobs_b / gxnd__usn)
    return qlf__wam, oyft__mcc, gxnd__usn


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
        ygsks__nvmla = ''
        for tnyr__cqzbs, ccq__zcay in self.df_out_vars.items():
            ygsks__nvmla += "'{}':{}, ".format(tnyr__cqzbs, ccq__zcay.name)
        xfw__gpt = '{}{{{}}}'.format(self.df_out, ygsks__nvmla)
        numc__lsqtm = ''
        for tnyr__cqzbs, ccq__zcay in self.df_in_vars.items():
            numc__lsqtm += "'{}':{}, ".format(tnyr__cqzbs, ccq__zcay.name)
        rgr__uyl = '{}{{{}}}'.format(self.df_in, numc__lsqtm)
        rzpz__jgzn = 'pivot {}:{}'.format(self.pivot_arr.name, self.
            pivot_values) if self.pivot_arr is not None else ''
        key_names = ','.join(self.key_names)
        vrc__zbmpe = ','.join([ccq__zcay.name for ccq__zcay in self.key_arrs])
        return 'aggregate: {} = {} [key: {}:{}] {}'.format(xfw__gpt,
            rgr__uyl, key_names, vrc__zbmpe, rzpz__jgzn)

    def remove_out_col(self, out_col_name):
        self.df_out_vars.pop(out_col_name)
        ckt__rrpu, zzm__xkqnm = self.gb_info_out.pop(out_col_name)
        if ckt__rrpu is None and not self.is_crosstab:
            return
        vyib__qnit = self.gb_info_in[ckt__rrpu]
        if self.pivot_arr is not None:
            self.pivot_values.remove(out_col_name)
            for rvo__pmu, (func, ygsks__nvmla) in enumerate(vyib__qnit):
                try:
                    ygsks__nvmla.remove(out_col_name)
                    if len(ygsks__nvmla) == 0:
                        vyib__qnit.pop(rvo__pmu)
                        break
                except ValueError as snbfw__ohml:
                    continue
        else:
            for rvo__pmu, (func, jiibj__yfbs) in enumerate(vyib__qnit):
                if jiibj__yfbs == out_col_name:
                    vyib__qnit.pop(rvo__pmu)
                    break
        if len(vyib__qnit) == 0:
            self.gb_info_in.pop(ckt__rrpu)
            self.df_in_vars.pop(ckt__rrpu)


def aggregate_usedefs(aggregate_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({ccq__zcay.name for ccq__zcay in aggregate_node.key_arrs})
    use_set.update({ccq__zcay.name for ccq__zcay in aggregate_node.
        df_in_vars.values()})
    if aggregate_node.pivot_arr is not None:
        use_set.add(aggregate_node.pivot_arr.name)
    def_set.update({ccq__zcay.name for ccq__zcay in aggregate_node.
        df_out_vars.values()})
    if aggregate_node.out_key_vars is not None:
        def_set.update({ccq__zcay.name for ccq__zcay in aggregate_node.
            out_key_vars})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Aggregate] = aggregate_usedefs


def remove_dead_aggregate(aggregate_node, lives_no_aliases, lives,
    arg_aliases, alias_map, func_ir, typemap):
    sjl__ybymb = [uwad__yff for uwad__yff, wxxa__pzbq in aggregate_node.
        df_out_vars.items() if wxxa__pzbq.name not in lives]
    for uunip__tybxk in sjl__ybymb:
        aggregate_node.remove_out_col(uunip__tybxk)
    out_key_vars = aggregate_node.out_key_vars
    if out_key_vars is not None and all(ccq__zcay.name not in lives for
        ccq__zcay in out_key_vars):
        aggregate_node.out_key_vars = None
    if len(aggregate_node.df_out_vars
        ) == 0 and aggregate_node.out_key_vars is None:
        return None
    return aggregate_node


ir_utils.remove_dead_extensions[Aggregate] = remove_dead_aggregate


def get_copies_aggregate(aggregate_node, typemap):
    fht__yiofo = set(ccq__zcay.name for ccq__zcay in aggregate_node.
        df_out_vars.values())
    if aggregate_node.out_key_vars is not None:
        fht__yiofo.update({ccq__zcay.name for ccq__zcay in aggregate_node.
            out_key_vars})
    return set(), fht__yiofo


ir_utils.copy_propagate_extensions[Aggregate] = get_copies_aggregate


def apply_copies_aggregate(aggregate_node, var_dict, name_var_table,
    typemap, calltypes, save_copies):
    for rvo__pmu in range(len(aggregate_node.key_arrs)):
        aggregate_node.key_arrs[rvo__pmu] = replace_vars_inner(aggregate_node
            .key_arrs[rvo__pmu], var_dict)
    for uwad__yff in list(aggregate_node.df_in_vars.keys()):
        aggregate_node.df_in_vars[uwad__yff] = replace_vars_inner(
            aggregate_node.df_in_vars[uwad__yff], var_dict)
    for uwad__yff in list(aggregate_node.df_out_vars.keys()):
        aggregate_node.df_out_vars[uwad__yff] = replace_vars_inner(
            aggregate_node.df_out_vars[uwad__yff], var_dict)
    if aggregate_node.out_key_vars is not None:
        for rvo__pmu in range(len(aggregate_node.out_key_vars)):
            aggregate_node.out_key_vars[rvo__pmu] = replace_vars_inner(
                aggregate_node.out_key_vars[rvo__pmu], var_dict)
    if aggregate_node.pivot_arr is not None:
        aggregate_node.pivot_arr = replace_vars_inner(aggregate_node.
            pivot_arr, var_dict)


ir_utils.apply_copy_propagate_extensions[Aggregate] = apply_copies_aggregate


def visit_vars_aggregate(aggregate_node, callback, cbdata):
    if debug_prints():
        print('visiting aggregate vars for:', aggregate_node)
        print('cbdata: ', sorted(cbdata.items()))
    for rvo__pmu in range(len(aggregate_node.key_arrs)):
        aggregate_node.key_arrs[rvo__pmu] = visit_vars_inner(aggregate_node
            .key_arrs[rvo__pmu], callback, cbdata)
    for uwad__yff in list(aggregate_node.df_in_vars.keys()):
        aggregate_node.df_in_vars[uwad__yff] = visit_vars_inner(aggregate_node
            .df_in_vars[uwad__yff], callback, cbdata)
    for uwad__yff in list(aggregate_node.df_out_vars.keys()):
        aggregate_node.df_out_vars[uwad__yff] = visit_vars_inner(aggregate_node
            .df_out_vars[uwad__yff], callback, cbdata)
    if aggregate_node.out_key_vars is not None:
        for rvo__pmu in range(len(aggregate_node.out_key_vars)):
            aggregate_node.out_key_vars[rvo__pmu] = visit_vars_inner(
                aggregate_node.out_key_vars[rvo__pmu], callback, cbdata)
    if aggregate_node.pivot_arr is not None:
        aggregate_node.pivot_arr = visit_vars_inner(aggregate_node.
            pivot_arr, callback, cbdata)


ir_utils.visit_vars_extensions[Aggregate] = visit_vars_aggregate


def aggregate_array_analysis(aggregate_node, equiv_set, typemap, array_analysis
    ):
    assert len(aggregate_node.df_out_vars
        ) > 0 or aggregate_node.out_key_vars is not None or aggregate_node.is_crosstab, 'empty aggregate in array analysis'
    kqxu__ivcu = []
    for jxj__bnyt in aggregate_node.key_arrs:
        xaccy__adarw = equiv_set.get_shape(jxj__bnyt)
        if xaccy__adarw:
            kqxu__ivcu.append(xaccy__adarw[0])
    if aggregate_node.pivot_arr is not None:
        xaccy__adarw = equiv_set.get_shape(aggregate_node.pivot_arr)
        if xaccy__adarw:
            kqxu__ivcu.append(xaccy__adarw[0])
    for wxxa__pzbq in aggregate_node.df_in_vars.values():
        xaccy__adarw = equiv_set.get_shape(wxxa__pzbq)
        if xaccy__adarw:
            kqxu__ivcu.append(xaccy__adarw[0])
    if len(kqxu__ivcu) > 1:
        equiv_set.insert_equiv(*kqxu__ivcu)
    pehaw__ils = []
    kqxu__ivcu = []
    fjhai__gonqc = list(aggregate_node.df_out_vars.values())
    if aggregate_node.out_key_vars is not None:
        fjhai__gonqc.extend(aggregate_node.out_key_vars)
    for wxxa__pzbq in fjhai__gonqc:
        lae__yje = typemap[wxxa__pzbq.name]
        ved__krxyb = array_analysis._gen_shape_call(equiv_set, wxxa__pzbq,
            lae__yje.ndim, None, pehaw__ils)
        equiv_set.insert_equiv(wxxa__pzbq, ved__krxyb)
        kqxu__ivcu.append(ved__krxyb[0])
        equiv_set.define(wxxa__pzbq, set())
    if len(kqxu__ivcu) > 1:
        equiv_set.insert_equiv(*kqxu__ivcu)
    return [], pehaw__ils


numba.parfors.array_analysis.array_analysis_extensions[Aggregate
    ] = aggregate_array_analysis


def aggregate_distributed_analysis(aggregate_node, array_dists):
    iagdw__wln = Distribution.OneD
    for wxxa__pzbq in aggregate_node.df_in_vars.values():
        iagdw__wln = Distribution(min(iagdw__wln.value, array_dists[
            wxxa__pzbq.name].value))
    for jxj__bnyt in aggregate_node.key_arrs:
        iagdw__wln = Distribution(min(iagdw__wln.value, array_dists[
            jxj__bnyt.name].value))
    if aggregate_node.pivot_arr is not None:
        iagdw__wln = Distribution(min(iagdw__wln.value, array_dists[
            aggregate_node.pivot_arr.name].value))
        array_dists[aggregate_node.pivot_arr.name] = iagdw__wln
    for wxxa__pzbq in aggregate_node.df_in_vars.values():
        array_dists[wxxa__pzbq.name] = iagdw__wln
    for jxj__bnyt in aggregate_node.key_arrs:
        array_dists[jxj__bnyt.name] = iagdw__wln
    fjaxp__jiv = Distribution.OneD_Var
    for wxxa__pzbq in aggregate_node.df_out_vars.values():
        if wxxa__pzbq.name in array_dists:
            fjaxp__jiv = Distribution(min(fjaxp__jiv.value, array_dists[
                wxxa__pzbq.name].value))
    if aggregate_node.out_key_vars is not None:
        for wxxa__pzbq in aggregate_node.out_key_vars:
            if wxxa__pzbq.name in array_dists:
                fjaxp__jiv = Distribution(min(fjaxp__jiv.value, array_dists
                    [wxxa__pzbq.name].value))
    fjaxp__jiv = Distribution(min(fjaxp__jiv.value, iagdw__wln.value))
    for wxxa__pzbq in aggregate_node.df_out_vars.values():
        array_dists[wxxa__pzbq.name] = fjaxp__jiv
    if aggregate_node.out_key_vars is not None:
        for nbacg__vmw in aggregate_node.out_key_vars:
            array_dists[nbacg__vmw.name] = fjaxp__jiv
    if fjaxp__jiv != Distribution.OneD_Var:
        for jxj__bnyt in aggregate_node.key_arrs:
            array_dists[jxj__bnyt.name] = fjaxp__jiv
        if aggregate_node.pivot_arr is not None:
            array_dists[aggregate_node.pivot_arr.name] = fjaxp__jiv
        for wxxa__pzbq in aggregate_node.df_in_vars.values():
            array_dists[wxxa__pzbq.name] = fjaxp__jiv


distributed_analysis.distributed_analysis_extensions[Aggregate
    ] = aggregate_distributed_analysis


def build_agg_definitions(agg_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for wxxa__pzbq in agg_node.df_out_vars.values():
        definitions[wxxa__pzbq.name].append(agg_node)
    if agg_node.out_key_vars is not None:
        for nbacg__vmw in agg_node.out_key_vars:
            definitions[nbacg__vmw.name].append(agg_node)
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
        for ccq__zcay in (list(agg_node.df_in_vars.values()) + list(
            agg_node.df_out_vars.values()) + agg_node.key_arrs):
            if array_dists[ccq__zcay.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                ccq__zcay.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    lou__waxx = tuple(typemap[ccq__zcay.name] for ccq__zcay in agg_node.
        key_arrs)
    gfjs__nzv = [ccq__zcay for bckhw__gjer, ccq__zcay in agg_node.
        df_in_vars.items()]
    xkxvg__yzgg = [ccq__zcay for bckhw__gjer, ccq__zcay in agg_node.
        df_out_vars.items()]
    in_col_typs = []
    ilup__vkfk = []
    if agg_node.pivot_arr is not None:
        for ckt__rrpu, vyib__qnit in agg_node.gb_info_in.items():
            for func, zzm__xkqnm in vyib__qnit:
                if ckt__rrpu is not None:
                    in_col_typs.append(typemap[agg_node.df_in_vars[
                        ckt__rrpu].name])
                ilup__vkfk.append(func)
    else:
        for ckt__rrpu, func in agg_node.gb_info_out.values():
            if ckt__rrpu is not None:
                in_col_typs.append(typemap[agg_node.df_in_vars[ckt__rrpu].name]
                    )
            ilup__vkfk.append(func)
    out_col_typs = tuple(typemap[ccq__zcay.name] for ccq__zcay in xkxvg__yzgg)
    pivot_typ = types.none if agg_node.pivot_arr is None else typemap[agg_node
        .pivot_arr.name]
    arg_typs = tuple(lou__waxx + tuple(typemap[ccq__zcay.name] for
        ccq__zcay in gfjs__nzv) + (pivot_typ,))
    in_col_typs = [to_str_arr_if_dict_array(t) for t in in_col_typs]
    ntsla__yjm = {'bodo': bodo, 'np': np, 'dt64_dtype': np.dtype(
        'datetime64[ns]'), 'td64_dtype': np.dtype('timedelta64[ns]')}
    for rvo__pmu, in_col_typ in enumerate(in_col_typs):
        if isinstance(in_col_typ, bodo.CategoricalArrayType):
            ntsla__yjm.update({f'in_cat_dtype_{rvo__pmu}': in_col_typ})
    for rvo__pmu, voddp__jstp in enumerate(out_col_typs):
        if isinstance(voddp__jstp, bodo.CategoricalArrayType):
            ntsla__yjm.update({f'out_cat_dtype_{rvo__pmu}': voddp__jstp})
    udf_func_struct = get_udf_func_struct(ilup__vkfk, agg_node.
        input_has_index, in_col_typs, out_col_typs, typingctx, targetctx,
        pivot_typ, agg_node.pivot_values, agg_node.is_crosstab)
    hgllz__lyios = gen_top_level_agg_func(agg_node, in_col_typs,
        out_col_typs, parallel, udf_func_struct)
    ntsla__yjm.update({'pd': pd, 'pre_alloc_string_array':
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
            ntsla__yjm.update({'__update_redvars': udf_func_struct.
                update_all_func, '__init_func': udf_func_struct.init_func,
                '__combine_redvars': udf_func_struct.combine_all_func,
                '__eval_res': udf_func_struct.eval_all_func,
                'cpp_cb_update': udf_func_struct.regular_udf_cfuncs[0],
                'cpp_cb_combine': udf_func_struct.regular_udf_cfuncs[1],
                'cpp_cb_eval': udf_func_struct.regular_udf_cfuncs[2]})
        if udf_func_struct.general_udfs:
            ntsla__yjm.update({'cpp_cb_general': udf_func_struct.
                general_udf_cfunc})
    xpxw__bhgf = compile_to_numba_ir(hgllz__lyios, ntsla__yjm, typingctx=
        typingctx, targetctx=targetctx, arg_typs=arg_typs, typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    qfhq__yqjod = []
    if agg_node.pivot_arr is None:
        usa__bddl = agg_node.key_arrs[0].scope
        loc = agg_node.loc
        hclv__smlj = ir.Var(usa__bddl, mk_unique_var('dummy_none'), loc)
        typemap[hclv__smlj.name] = types.none
        qfhq__yqjod.append(ir.Assign(ir.Const(None, loc), hclv__smlj, loc))
        gfjs__nzv.append(hclv__smlj)
    else:
        gfjs__nzv.append(agg_node.pivot_arr)
    replace_arg_nodes(xpxw__bhgf, agg_node.key_arrs + gfjs__nzv)
    niwvo__qqd = xpxw__bhgf.body[-3]
    assert is_assign(niwvo__qqd) and isinstance(niwvo__qqd.value, ir.Expr
        ) and niwvo__qqd.value.op == 'build_tuple'
    qfhq__yqjod += xpxw__bhgf.body[:-3]
    fjhai__gonqc = list(agg_node.df_out_vars.values())
    if agg_node.out_key_vars is not None:
        fjhai__gonqc += agg_node.out_key_vars
    for rvo__pmu, llrr__qqzsa in enumerate(fjhai__gonqc):
        ysbdp__imwe = niwvo__qqd.value.items[rvo__pmu]
        qfhq__yqjod.append(ir.Assign(ysbdp__imwe, llrr__qqzsa, llrr__qqzsa.loc)
            )
    return qfhq__yqjod


distributed_pass.distributed_run_extensions[Aggregate] = agg_distributed_run


def get_numba_set(dtype):
    pass


@infer_global(get_numba_set)
class GetNumbaSetTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 1
        vkzm__uqyb = args[0]
        dtype = types.Tuple([t.dtype for t in vkzm__uqyb.types]) if isinstance(
            vkzm__uqyb, types.BaseTuple) else vkzm__uqyb.dtype
        if isinstance(vkzm__uqyb, types.BaseTuple) and len(vkzm__uqyb.types
            ) == 1:
            dtype = vkzm__uqyb.types[0].dtype
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
        mhriy__rfeq = args[0]
        if mhriy__rfeq == types.none:
            return signature(types.boolean, *args)


@lower_builtin(bool, types.none)
def lower_column_mean_impl(context, builder, sig, args):
    otyl__ukr = context.compile_internal(builder, lambda a: False, sig, args)
    return otyl__ukr


def _gen_dummy_alloc(t, colnum=0, is_input=False):
    if isinstance(t, IntegerArrayType):
        cosre__pvbxz = IntDtype(t.dtype).name
        assert cosre__pvbxz.endswith('Dtype()')
        cosre__pvbxz = cosre__pvbxz[:-7]
        return (
            f"bodo.hiframes.pd_series_ext.get_series_data(pd.Series([1], dtype='{cosre__pvbxz}'))"
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
        donx__vcv = 'in' if is_input else 'out'
        return (
            f'bodo.utils.utils.alloc_type(1, {donx__vcv}_cat_dtype_{colnum})')
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
    gjp__yuj = udf_func_struct.var_typs
    kpw__kshx = len(gjp__yuj)
    cnqr__fsjy = (
        'def bodo_gb_udf_update_local{}(in_table, out_table, row_to_group):\n'
        .format(label_suffix))
    cnqr__fsjy += '    if is_null_pointer(in_table):\n'
    cnqr__fsjy += '        return\n'
    cnqr__fsjy += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in gjp__yuj]), ',' if
        len(gjp__yuj) == 1 else '')
    otlik__zym = n_keys
    ebnrk__mzs = []
    redvar_offsets = []
    avipo__unp = []
    if do_combine:
        for rvo__pmu, pwthh__kjwsu in enumerate(allfuncs):
            if pwthh__kjwsu.ftype != 'udf':
                otlik__zym += pwthh__kjwsu.ncols_pre_shuffle
            else:
                redvar_offsets += list(range(otlik__zym, otlik__zym +
                    pwthh__kjwsu.n_redvars))
                otlik__zym += pwthh__kjwsu.n_redvars
                avipo__unp.append(data_in_typs_[func_idx_to_in_col[rvo__pmu]])
                ebnrk__mzs.append(func_idx_to_in_col[rvo__pmu] + n_keys)
    else:
        for rvo__pmu, pwthh__kjwsu in enumerate(allfuncs):
            if pwthh__kjwsu.ftype != 'udf':
                otlik__zym += pwthh__kjwsu.ncols_post_shuffle
            else:
                redvar_offsets += list(range(otlik__zym + 1, otlik__zym + 1 +
                    pwthh__kjwsu.n_redvars))
                otlik__zym += pwthh__kjwsu.n_redvars + 1
                avipo__unp.append(data_in_typs_[func_idx_to_in_col[rvo__pmu]])
                ebnrk__mzs.append(func_idx_to_in_col[rvo__pmu] + n_keys)
    assert len(redvar_offsets) == kpw__kshx
    ggiax__jqfj = len(avipo__unp)
    tnep__gijr = []
    for rvo__pmu, t in enumerate(avipo__unp):
        tnep__gijr.append(_gen_dummy_alloc(t, rvo__pmu, True))
    cnqr__fsjy += '    data_in_dummy = ({}{})\n'.format(','.join(tnep__gijr
        ), ',' if len(avipo__unp) == 1 else '')
    cnqr__fsjy += """
    # initialize redvar cols
"""
    cnqr__fsjy += '    init_vals = __init_func()\n'
    for rvo__pmu in range(kpw__kshx):
        cnqr__fsjy += (
            """    redvar_arr_{} = info_to_array(info_from_table(out_table, {}), data_redvar_dummy[{}])
"""
            .format(rvo__pmu, redvar_offsets[rvo__pmu], rvo__pmu))
        cnqr__fsjy += '    incref(redvar_arr_{})\n'.format(rvo__pmu)
        cnqr__fsjy += '    redvar_arr_{}.fill(init_vals[{}])\n'.format(rvo__pmu
            , rvo__pmu)
    cnqr__fsjy += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'
        .format(rvo__pmu) for rvo__pmu in range(kpw__kshx)]), ',' if 
        kpw__kshx == 1 else '')
    cnqr__fsjy += '\n'
    for rvo__pmu in range(ggiax__jqfj):
        cnqr__fsjy += (
            """    data_in_{} = info_to_array(info_from_table(in_table, {}), data_in_dummy[{}])
"""
            .format(rvo__pmu, ebnrk__mzs[rvo__pmu], rvo__pmu))
        cnqr__fsjy += '    incref(data_in_{})\n'.format(rvo__pmu)
    cnqr__fsjy += '    data_in = ({}{})\n'.format(','.join(['data_in_{}'.
        format(rvo__pmu) for rvo__pmu in range(ggiax__jqfj)]), ',' if 
        ggiax__jqfj == 1 else '')
    cnqr__fsjy += '\n'
    cnqr__fsjy += '    for i in range(len(data_in_0)):\n'
    cnqr__fsjy += '        w_ind = row_to_group[i]\n'
    cnqr__fsjy += '        if w_ind != -1:\n'
    cnqr__fsjy += (
        '            __update_redvars(redvars, data_in, w_ind, i, pivot_arr=None)\n'
        )
    kojo__bea = {}
    exec(cnqr__fsjy, {'bodo': bodo, 'np': np, 'pd': pd, 'info_to_array':
        info_to_array, 'info_from_table': info_from_table, 'incref': incref,
        'pre_alloc_string_array': pre_alloc_string_array, '__init_func':
        udf_func_struct.init_func, '__update_redvars': udf_func_struct.
        update_all_func, 'is_null_pointer': is_null_pointer, 'dt64_dtype':
        np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, kojo__bea)
    return kojo__bea['bodo_gb_udf_update_local{}'.format(label_suffix)]


def gen_combine_cb(udf_func_struct, allfuncs, n_keys, out_data_typs,
    label_suffix):
    gjp__yuj = udf_func_struct.var_typs
    kpw__kshx = len(gjp__yuj)
    cnqr__fsjy = (
        'def bodo_gb_udf_combine{}(in_table, out_table, row_to_group):\n'.
        format(label_suffix))
    cnqr__fsjy += '    if is_null_pointer(in_table):\n'
    cnqr__fsjy += '        return\n'
    cnqr__fsjy += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in gjp__yuj]), ',' if
        len(gjp__yuj) == 1 else '')
    yky__ohnl = n_keys
    wnebp__hpqe = n_keys
    olmx__mtu = []
    olz__vgfm = []
    for pwthh__kjwsu in allfuncs:
        if pwthh__kjwsu.ftype != 'udf':
            yky__ohnl += pwthh__kjwsu.ncols_pre_shuffle
            wnebp__hpqe += pwthh__kjwsu.ncols_post_shuffle
        else:
            olmx__mtu += list(range(yky__ohnl, yky__ohnl + pwthh__kjwsu.
                n_redvars))
            olz__vgfm += list(range(wnebp__hpqe + 1, wnebp__hpqe + 1 +
                pwthh__kjwsu.n_redvars))
            yky__ohnl += pwthh__kjwsu.n_redvars
            wnebp__hpqe += 1 + pwthh__kjwsu.n_redvars
    assert len(olmx__mtu) == kpw__kshx
    cnqr__fsjy += """
    # initialize redvar cols
"""
    cnqr__fsjy += '    init_vals = __init_func()\n'
    for rvo__pmu in range(kpw__kshx):
        cnqr__fsjy += (
            """    redvar_arr_{} = info_to_array(info_from_table(out_table, {}), data_redvar_dummy[{}])
"""
            .format(rvo__pmu, olz__vgfm[rvo__pmu], rvo__pmu))
        cnqr__fsjy += '    incref(redvar_arr_{})\n'.format(rvo__pmu)
        cnqr__fsjy += '    redvar_arr_{}.fill(init_vals[{}])\n'.format(rvo__pmu
            , rvo__pmu)
    cnqr__fsjy += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'
        .format(rvo__pmu) for rvo__pmu in range(kpw__kshx)]), ',' if 
        kpw__kshx == 1 else '')
    cnqr__fsjy += '\n'
    for rvo__pmu in range(kpw__kshx):
        cnqr__fsjy += (
            """    recv_redvar_arr_{} = info_to_array(info_from_table(in_table, {}), data_redvar_dummy[{}])
"""
            .format(rvo__pmu, olmx__mtu[rvo__pmu], rvo__pmu))
        cnqr__fsjy += '    incref(recv_redvar_arr_{})\n'.format(rvo__pmu)
    cnqr__fsjy += '    recv_redvars = ({}{})\n'.format(','.join([
        'recv_redvar_arr_{}'.format(rvo__pmu) for rvo__pmu in range(
        kpw__kshx)]), ',' if kpw__kshx == 1 else '')
    cnqr__fsjy += '\n'
    if kpw__kshx:
        cnqr__fsjy += '    for i in range(len(recv_redvar_arr_0)):\n'
        cnqr__fsjy += '        w_ind = row_to_group[i]\n'
        cnqr__fsjy += """        __combine_redvars(redvars, recv_redvars, w_ind, i, pivot_arr=None)
"""
    kojo__bea = {}
    exec(cnqr__fsjy, {'np': np, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref, '__init_func':
        udf_func_struct.init_func, '__combine_redvars': udf_func_struct.
        combine_all_func, 'is_null_pointer': is_null_pointer, 'dt64_dtype':
        np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, kojo__bea)
    return kojo__bea['bodo_gb_udf_combine{}'.format(label_suffix)]


def gen_eval_cb(udf_func_struct, allfuncs, n_keys, out_data_typs_, label_suffix
    ):
    gjp__yuj = udf_func_struct.var_typs
    kpw__kshx = len(gjp__yuj)
    otlik__zym = n_keys
    redvar_offsets = []
    nyri__lejmn = []
    out_data_typs = []
    for rvo__pmu, pwthh__kjwsu in enumerate(allfuncs):
        if pwthh__kjwsu.ftype != 'udf':
            otlik__zym += pwthh__kjwsu.ncols_post_shuffle
        else:
            nyri__lejmn.append(otlik__zym)
            redvar_offsets += list(range(otlik__zym + 1, otlik__zym + 1 +
                pwthh__kjwsu.n_redvars))
            otlik__zym += 1 + pwthh__kjwsu.n_redvars
            out_data_typs.append(out_data_typs_[rvo__pmu])
    assert len(redvar_offsets) == kpw__kshx
    ggiax__jqfj = len(out_data_typs)
    cnqr__fsjy = 'def bodo_gb_udf_eval{}(table):\n'.format(label_suffix)
    cnqr__fsjy += '    if is_null_pointer(table):\n'
    cnqr__fsjy += '        return\n'
    cnqr__fsjy += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in gjp__yuj]), ',' if
        len(gjp__yuj) == 1 else '')
    cnqr__fsjy += '    out_data_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t.dtype)) for t in
        out_data_typs]), ',' if len(out_data_typs) == 1 else '')
    for rvo__pmu in range(kpw__kshx):
        cnqr__fsjy += (
            """    redvar_arr_{} = info_to_array(info_from_table(table, {}), data_redvar_dummy[{}])
"""
            .format(rvo__pmu, redvar_offsets[rvo__pmu], rvo__pmu))
        cnqr__fsjy += '    incref(redvar_arr_{})\n'.format(rvo__pmu)
    cnqr__fsjy += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'
        .format(rvo__pmu) for rvo__pmu in range(kpw__kshx)]), ',' if 
        kpw__kshx == 1 else '')
    cnqr__fsjy += '\n'
    for rvo__pmu in range(ggiax__jqfj):
        cnqr__fsjy += (
            """    data_out_{} = info_to_array(info_from_table(table, {}), out_data_dummy[{}])
"""
            .format(rvo__pmu, nyri__lejmn[rvo__pmu], rvo__pmu))
        cnqr__fsjy += '    incref(data_out_{})\n'.format(rvo__pmu)
    cnqr__fsjy += '    data_out = ({}{})\n'.format(','.join(['data_out_{}'.
        format(rvo__pmu) for rvo__pmu in range(ggiax__jqfj)]), ',' if 
        ggiax__jqfj == 1 else '')
    cnqr__fsjy += '\n'
    cnqr__fsjy += '    for i in range(len(data_out_0)):\n'
    cnqr__fsjy += '        __eval_res(redvars, data_out, i)\n'
    kojo__bea = {}
    exec(cnqr__fsjy, {'np': np, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref, '__eval_res':
        udf_func_struct.eval_all_func, 'is_null_pointer': is_null_pointer,
        'dt64_dtype': np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, kojo__bea)
    return kojo__bea['bodo_gb_udf_eval{}'.format(label_suffix)]


def gen_general_udf_cb(udf_func_struct, allfuncs, n_keys, in_col_typs,
    out_col_typs, func_idx_to_in_col, label_suffix):
    otlik__zym = n_keys
    zvnew__ktpc = []
    for rvo__pmu, pwthh__kjwsu in enumerate(allfuncs):
        if pwthh__kjwsu.ftype == 'gen_udf':
            zvnew__ktpc.append(otlik__zym)
            otlik__zym += 1
        elif pwthh__kjwsu.ftype != 'udf':
            otlik__zym += pwthh__kjwsu.ncols_post_shuffle
        else:
            otlik__zym += pwthh__kjwsu.n_redvars + 1
    cnqr__fsjy = (
        'def bodo_gb_apply_general_udfs{}(num_groups, in_table, out_table):\n'
        .format(label_suffix))
    cnqr__fsjy += '    if num_groups == 0:\n'
    cnqr__fsjy += '        return\n'
    for rvo__pmu, func in enumerate(udf_func_struct.general_udf_funcs):
        cnqr__fsjy += '    # col {}\n'.format(rvo__pmu)
        cnqr__fsjy += (
            """    out_col = info_to_array(info_from_table(out_table, {}), out_col_{}_typ)
"""
            .format(zvnew__ktpc[rvo__pmu], rvo__pmu))
        cnqr__fsjy += '    incref(out_col)\n'
        cnqr__fsjy += '    for j in range(num_groups):\n'
        cnqr__fsjy += (
            """        in_col = info_to_array(info_from_table(in_table, {}*num_groups + j), in_col_{}_typ)
"""
            .format(rvo__pmu, rvo__pmu))
        cnqr__fsjy += '        incref(in_col)\n'
        cnqr__fsjy += (
            '        out_col[j] = func_{}(pd.Series(in_col))  # func returns scalar\n'
            .format(rvo__pmu))
    ntsla__yjm = {'pd': pd, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref}
    hptt__zupg = 0
    for rvo__pmu, func in enumerate(allfuncs):
        if func.ftype != 'gen_udf':
            continue
        func = udf_func_struct.general_udf_funcs[hptt__zupg]
        ntsla__yjm['func_{}'.format(hptt__zupg)] = func
        ntsla__yjm['in_col_{}_typ'.format(hptt__zupg)] = in_col_typs[
            func_idx_to_in_col[rvo__pmu]]
        ntsla__yjm['out_col_{}_typ'.format(hptt__zupg)] = out_col_typs[rvo__pmu
            ]
        hptt__zupg += 1
    kojo__bea = {}
    exec(cnqr__fsjy, ntsla__yjm, kojo__bea)
    pwthh__kjwsu = kojo__bea['bodo_gb_apply_general_udfs{}'.format(
        label_suffix)]
    rpdxa__ibr = types.void(types.int64, types.voidptr, types.voidptr)
    return numba.cfunc(rpdxa__ibr, nopython=True)(pwthh__kjwsu)


def gen_top_level_agg_func(agg_node, in_col_typs, out_col_typs, parallel,
    udf_func_struct):
    oydu__buxr = agg_node.pivot_arr is not None
    if agg_node.same_index:
        assert agg_node.input_has_index
    if agg_node.pivot_values is None:
        otusk__gtw = 1
    else:
        otusk__gtw = len(agg_node.pivot_values)
    fcycq__twni = tuple('key_' + sanitize_varname(tnyr__cqzbs) for
        tnyr__cqzbs in agg_node.key_names)
    jirin__dhfkp = {tnyr__cqzbs: 'in_{}'.format(sanitize_varname(
        tnyr__cqzbs)) for tnyr__cqzbs in agg_node.gb_info_in.keys() if 
        tnyr__cqzbs is not None}
    eey__vsuad = {tnyr__cqzbs: ('out_' + sanitize_varname(tnyr__cqzbs)) for
        tnyr__cqzbs in agg_node.gb_info_out.keys()}
    n_keys = len(agg_node.key_names)
    svzzo__qxvjw = ', '.join(fcycq__twni)
    tans__dyp = ', '.join(jirin__dhfkp.values())
    if tans__dyp != '':
        tans__dyp = ', ' + tans__dyp
    cnqr__fsjy = 'def agg_top({}{}{}, pivot_arr):\n'.format(svzzo__qxvjw,
        tans__dyp, ', index_arg' if agg_node.input_has_index else '')
    for a in (fcycq__twni + tuple(jirin__dhfkp.values())):
        cnqr__fsjy += f'    {a} = decode_if_dict_array({a})\n'
    if oydu__buxr:
        cnqr__fsjy += f'    pivot_arr = decode_if_dict_array(pivot_arr)\n'
        nafg__wgjhe = []
        for ckt__rrpu, vyib__qnit in agg_node.gb_info_in.items():
            if ckt__rrpu is not None:
                for func, zzm__xkqnm in vyib__qnit:
                    nafg__wgjhe.append(jirin__dhfkp[ckt__rrpu])
    else:
        nafg__wgjhe = tuple(jirin__dhfkp[ckt__rrpu] for ckt__rrpu,
            zzm__xkqnm in agg_node.gb_info_out.values() if ckt__rrpu is not
            None)
    qqr__ahm = fcycq__twni + tuple(nafg__wgjhe)
    cnqr__fsjy += '    info_list = [{}{}{}]\n'.format(', '.join(
        'array_to_info({})'.format(a) for a in qqr__ahm), 
        ', array_to_info(index_arg)' if agg_node.input_has_index else '', 
        ', array_to_info(pivot_arr)' if agg_node.is_crosstab else '')
    cnqr__fsjy += '    table = arr_info_list_to_table(info_list)\n'
    for rvo__pmu, tnyr__cqzbs in enumerate(agg_node.gb_info_out.keys()):
        uvl__swfg = eey__vsuad[tnyr__cqzbs] + '_dummy'
        voddp__jstp = out_col_typs[rvo__pmu]
        ckt__rrpu, func = agg_node.gb_info_out[tnyr__cqzbs]
        if isinstance(func, pytypes.SimpleNamespace) and func.fname in ['min',
            'max', 'shift'] and isinstance(voddp__jstp, bodo.
            CategoricalArrayType):
            cnqr__fsjy += '    {} = {}\n'.format(uvl__swfg, jirin__dhfkp[
                ckt__rrpu])
        else:
            cnqr__fsjy += '    {} = {}\n'.format(uvl__swfg,
                _gen_dummy_alloc(voddp__jstp, rvo__pmu, False))
    do_combine = parallel
    allfuncs = []
    htqsa__mdjoq = []
    func_idx_to_in_col = []
    jjl__sni = []
    nlisx__cxv = False
    byxr__fpsly = 1
    lmahf__cbi = -1
    zctas__gxak = 0
    yqp__rxe = 0
    if not oydu__buxr:
        ilup__vkfk = [func for zzm__xkqnm, func in agg_node.gb_info_out.
            values()]
    else:
        ilup__vkfk = [func for func, zzm__xkqnm in vyib__qnit for
            vyib__qnit in agg_node.gb_info_in.values()]
    for arstk__bmgpk, func in enumerate(ilup__vkfk):
        htqsa__mdjoq.append(len(allfuncs))
        if func.ftype in {'median', 'nunique'}:
            do_combine = False
        if func.ftype in list_cumulative:
            zctas__gxak += 1
        if hasattr(func, 'skipdropna'):
            nlisx__cxv = func.skipdropna
        if func.ftype == 'shift':
            byxr__fpsly = func.periods
            do_combine = False
        if func.ftype in {'transform'}:
            yqp__rxe = func.transform_func
            do_combine = False
        if func.ftype == 'head':
            lmahf__cbi = func.head_n
            do_combine = False
        allfuncs.append(func)
        func_idx_to_in_col.append(arstk__bmgpk)
        if func.ftype == 'udf':
            jjl__sni.append(func.n_redvars)
        elif func.ftype == 'gen_udf':
            jjl__sni.append(0)
            do_combine = False
    htqsa__mdjoq.append(len(allfuncs))
    if agg_node.is_crosstab:
        assert len(agg_node.gb_info_out
            ) == otusk__gtw, 'invalid number of groupby outputs for pivot'
    else:
        assert len(agg_node.gb_info_out) == len(allfuncs
            ) * otusk__gtw, 'invalid number of groupby outputs'
    if zctas__gxak > 0:
        if zctas__gxak != len(allfuncs):
            raise BodoError(
                f'{agg_node.func_name}(): Cannot mix cumulative operations with other aggregation functions'
                , loc=agg_node.loc)
        do_combine = False
    if udf_func_struct is not None:
        hgz__yfihi = next_label()
        if udf_func_struct.regular_udfs:
            rpdxa__ibr = types.void(types.voidptr, types.voidptr, types.
                CPointer(types.int64))
            oyq__pvwy = numba.cfunc(rpdxa__ibr, nopython=True)(gen_update_cb
                (udf_func_struct, allfuncs, n_keys, in_col_typs,
                out_col_typs, do_combine, func_idx_to_in_col, hgz__yfihi))
            yla__cezo = numba.cfunc(rpdxa__ibr, nopython=True)(gen_combine_cb
                (udf_func_struct, allfuncs, n_keys, out_col_typs, hgz__yfihi))
            ybwkn__shnf = numba.cfunc('void(voidptr)', nopython=True)(
                gen_eval_cb(udf_func_struct, allfuncs, n_keys, out_col_typs,
                hgz__yfihi))
            udf_func_struct.set_regular_cfuncs(oyq__pvwy, yla__cezo,
                ybwkn__shnf)
            for wuyn__xsuc in udf_func_struct.regular_udf_cfuncs:
                gb_agg_cfunc[wuyn__xsuc.native_name] = wuyn__xsuc
                gb_agg_cfunc_addr[wuyn__xsuc.native_name] = wuyn__xsuc.address
        if udf_func_struct.general_udfs:
            yvt__rmlbx = gen_general_udf_cb(udf_func_struct, allfuncs,
                n_keys, in_col_typs, out_col_typs, func_idx_to_in_col,
                hgz__yfihi)
            udf_func_struct.set_general_cfunc(yvt__rmlbx)
        tuuhn__rkr = []
        gcd__gszc = 0
        rvo__pmu = 0
        for uvl__swfg, pwthh__kjwsu in zip(eey__vsuad.values(), allfuncs):
            if pwthh__kjwsu.ftype in ('udf', 'gen_udf'):
                tuuhn__rkr.append(uvl__swfg + '_dummy')
                for wxn__uem in range(gcd__gszc, gcd__gszc + jjl__sni[rvo__pmu]
                    ):
                    tuuhn__rkr.append('data_redvar_dummy_' + str(wxn__uem))
                gcd__gszc += jjl__sni[rvo__pmu]
                rvo__pmu += 1
        if udf_func_struct.regular_udfs:
            gjp__yuj = udf_func_struct.var_typs
            for rvo__pmu, t in enumerate(gjp__yuj):
                cnqr__fsjy += ('    data_redvar_dummy_{} = np.empty(1, {})\n'
                    .format(rvo__pmu, _get_np_dtype(t)))
        cnqr__fsjy += '    out_info_list_dummy = [{}]\n'.format(', '.join(
            'array_to_info({})'.format(a) for a in tuuhn__rkr))
        cnqr__fsjy += (
            '    udf_table_dummy = arr_info_list_to_table(out_info_list_dummy)\n'
            )
        if udf_func_struct.regular_udfs:
            cnqr__fsjy += ("    add_agg_cfunc_sym(cpp_cb_update, '{}')\n".
                format(oyq__pvwy.native_name))
            cnqr__fsjy += ("    add_agg_cfunc_sym(cpp_cb_combine, '{}')\n".
                format(yla__cezo.native_name))
            cnqr__fsjy += "    add_agg_cfunc_sym(cpp_cb_eval, '{}')\n".format(
                ybwkn__shnf.native_name)
            cnqr__fsjy += ("    cpp_cb_update_addr = get_agg_udf_addr('{}')\n"
                .format(oyq__pvwy.native_name))
            cnqr__fsjy += ("    cpp_cb_combine_addr = get_agg_udf_addr('{}')\n"
                .format(yla__cezo.native_name))
            cnqr__fsjy += ("    cpp_cb_eval_addr = get_agg_udf_addr('{}')\n"
                .format(ybwkn__shnf.native_name))
        else:
            cnqr__fsjy += '    cpp_cb_update_addr = 0\n'
            cnqr__fsjy += '    cpp_cb_combine_addr = 0\n'
            cnqr__fsjy += '    cpp_cb_eval_addr = 0\n'
        if udf_func_struct.general_udfs:
            wuyn__xsuc = udf_func_struct.general_udf_cfunc
            gb_agg_cfunc[wuyn__xsuc.native_name] = wuyn__xsuc
            gb_agg_cfunc_addr[wuyn__xsuc.native_name] = wuyn__xsuc.address
            cnqr__fsjy += ("    add_agg_cfunc_sym(cpp_cb_general, '{}')\n".
                format(wuyn__xsuc.native_name))
            cnqr__fsjy += ("    cpp_cb_general_addr = get_agg_udf_addr('{}')\n"
                .format(wuyn__xsuc.native_name))
        else:
            cnqr__fsjy += '    cpp_cb_general_addr = 0\n'
    else:
        cnqr__fsjy += """    udf_table_dummy = arr_info_list_to_table([array_to_info(np.empty(1))])
"""
        cnqr__fsjy += '    cpp_cb_update_addr = 0\n'
        cnqr__fsjy += '    cpp_cb_combine_addr = 0\n'
        cnqr__fsjy += '    cpp_cb_eval_addr = 0\n'
        cnqr__fsjy += '    cpp_cb_general_addr = 0\n'
    cnqr__fsjy += '    ftypes = np.array([{}, 0], dtype=np.int32)\n'.format(
        ', '.join([str(supported_agg_funcs.index(pwthh__kjwsu.ftype)) for
        pwthh__kjwsu in allfuncs] + ['0']))
    cnqr__fsjy += '    func_offsets = np.array({}, dtype=np.int32)\n'.format(
        str(htqsa__mdjoq))
    if len(jjl__sni) > 0:
        cnqr__fsjy += '    udf_ncols = np.array({}, dtype=np.int32)\n'.format(
            str(jjl__sni))
    else:
        cnqr__fsjy += '    udf_ncols = np.array([0], np.int32)\n'
    if oydu__buxr:
        cnqr__fsjy += '    arr_type = coerce_to_array({})\n'.format(agg_node
            .pivot_values)
        cnqr__fsjy += '    arr_info = array_to_info(arr_type)\n'
        cnqr__fsjy += (
            '    dispatch_table = arr_info_list_to_table([arr_info])\n')
        cnqr__fsjy += '    pivot_info = array_to_info(pivot_arr)\n'
        cnqr__fsjy += (
            '    dispatch_info = arr_info_list_to_table([pivot_info])\n')
        cnqr__fsjy += (
            """    out_table = pivot_groupby_and_aggregate(table, {}, dispatch_table, dispatch_info, {}, ftypes.ctypes, func_offsets.ctypes, udf_ncols.ctypes, {}, {}, {}, {}, {}, cpp_cb_update_addr, cpp_cb_combine_addr, cpp_cb_eval_addr, udf_table_dummy)
"""
            .format(n_keys, agg_node.input_has_index, parallel, agg_node.
            is_crosstab, nlisx__cxv, agg_node.return_key, agg_node.same_index))
        cnqr__fsjy += '    delete_info_decref_array(pivot_info)\n'
        cnqr__fsjy += '    delete_info_decref_array(arr_info)\n'
    else:
        cnqr__fsjy += (
            """    out_table = groupby_and_aggregate(table, {}, {}, ftypes.ctypes, func_offsets.ctypes, udf_ncols.ctypes, {}, {}, {}, {}, {}, {}, {}, {}, cpp_cb_update_addr, cpp_cb_combine_addr, cpp_cb_eval_addr, cpp_cb_general_addr, udf_table_dummy)
"""
            .format(n_keys, agg_node.input_has_index, parallel, nlisx__cxv,
            byxr__fpsly, yqp__rxe, lmahf__cbi, agg_node.return_key,
            agg_node.same_index, agg_node.dropna))
    mrnqm__bphi = 0
    if agg_node.return_key:
        for rvo__pmu, bdu__kky in enumerate(fcycq__twni):
            cnqr__fsjy += (
                '    {} = info_to_array(info_from_table(out_table, {}), {})\n'
                .format(bdu__kky, mrnqm__bphi, bdu__kky))
            mrnqm__bphi += 1
    for uvl__swfg in eey__vsuad.values():
        cnqr__fsjy += (
            '    {} = info_to_array(info_from_table(out_table, {}), {})\n'.
            format(uvl__swfg, mrnqm__bphi, uvl__swfg + '_dummy'))
        mrnqm__bphi += 1
    if agg_node.same_index:
        cnqr__fsjy += (
            """    out_index_arg = info_to_array(info_from_table(out_table, {}), index_arg)
"""
            .format(mrnqm__bphi))
        mrnqm__bphi += 1
    cnqr__fsjy += (
        f"    ev_clean = bodo.utils.tracing.Event('tables_clean_up', {parallel})\n"
        )
    cnqr__fsjy += '    delete_table_decref_arrays(table)\n'
    cnqr__fsjy += '    delete_table_decref_arrays(udf_table_dummy)\n'
    cnqr__fsjy += '    delete_table(out_table)\n'
    cnqr__fsjy += f'    ev_clean.finalize()\n'
    wuel__txhjc = tuple(eey__vsuad.values())
    if agg_node.return_key:
        wuel__txhjc += tuple(fcycq__twni)
    cnqr__fsjy += '    return ({},{})\n'.format(', '.join(wuel__txhjc), 
        ' out_index_arg,' if agg_node.same_index else '')
    kojo__bea = {}
    exec(cnqr__fsjy, {}, kojo__bea)
    fjhk__hqem = kojo__bea['agg_top']
    return fjhk__hqem


def compile_to_optimized_ir(func, arg_typs, typingctx, targetctx):
    code = func.code if hasattr(func, 'code') else func.__code__
    closure = func.closure if hasattr(func, 'closure') else func.__closure__
    f_ir = get_ir_of_code(func.__globals__, code)
    replace_closures(f_ir, closure, code)
    for block in f_ir.blocks.values():
        for ieesd__vivb in block.body:
            if is_call_assign(ieesd__vivb) and find_callname(f_ir,
                ieesd__vivb.value) == ('len', 'builtins'
                ) and ieesd__vivb.value.args[0].name == f_ir.arg_names[0]:
                mnb__dpri = get_definition(f_ir, ieesd__vivb.value.func)
                mnb__dpri.name = 'dummy_agg_count'
                mnb__dpri.value = dummy_agg_count
    saoi__xis = get_name_var_table(f_ir.blocks)
    bth__qcdhr = {}
    for name, zzm__xkqnm in saoi__xis.items():
        bth__qcdhr[name] = mk_unique_var(name)
    replace_var_names(f_ir.blocks, bth__qcdhr)
    f_ir._definitions = build_definitions(f_ir.blocks)
    assert f_ir.arg_count == 1, 'agg function should have one input'
    bxv__yxlsn = numba.core.compiler.Flags()
    bxv__yxlsn.nrt = True
    lnf__yyn = bodo.transforms.untyped_pass.UntypedPass(f_ir, typingctx,
        arg_typs, {}, {}, bxv__yxlsn)
    lnf__yyn.run()
    f_ir._definitions = build_definitions(f_ir.blocks)
    typemap, qeve__escsn, calltypes, zzm__xkqnm = (numba.core.typed_passes.
        type_inference_stage(typingctx, targetctx, f_ir, arg_typs, None))
    irhke__ktgo = numba.core.cpu.ParallelOptions(True)
    targetctx = numba.core.cpu.CPUContext(typingctx)
    lemq__jawbh = namedtuple('DummyPipeline', ['typingctx', 'targetctx',
        'args', 'func_ir', 'typemap', 'return_type', 'calltypes',
        'type_annotation', 'locals', 'flags', 'pipeline'])
    rccdk__jpt = namedtuple('TypeAnnotation', ['typemap', 'calltypes'])
    yxxaf__moij = rccdk__jpt(typemap, calltypes)
    pm = lemq__jawbh(typingctx, targetctx, None, f_ir, typemap, qeve__escsn,
        calltypes, yxxaf__moij, {}, bxv__yxlsn, None)
    hlj__fep = numba.core.compiler.DefaultPassBuilder.define_untyped_pipeline(
        pm)
    pm = lemq__jawbh(typingctx, targetctx, None, f_ir, typemap, qeve__escsn,
        calltypes, yxxaf__moij, {}, bxv__yxlsn, hlj__fep)
    kwxpi__fsp = numba.core.typed_passes.InlineOverloads()
    kwxpi__fsp.run_pass(pm)
    hlz__ubnfe = bodo.transforms.series_pass.SeriesPass(f_ir, typingctx,
        targetctx, typemap, calltypes, {}, False)
    hlz__ubnfe.run()
    for block in f_ir.blocks.values():
        for ieesd__vivb in block.body:
            if is_assign(ieesd__vivb) and isinstance(ieesd__vivb.value, (ir
                .Arg, ir.Var)) and isinstance(typemap[ieesd__vivb.target.
                name], SeriesType):
                lae__yje = typemap.pop(ieesd__vivb.target.name)
                typemap[ieesd__vivb.target.name] = lae__yje.data
            if is_call_assign(ieesd__vivb) and find_callname(f_ir,
                ieesd__vivb.value) == ('get_series_data',
                'bodo.hiframes.pd_series_ext'):
                f_ir._definitions[ieesd__vivb.target.name].remove(ieesd__vivb
                    .value)
                ieesd__vivb.value = ieesd__vivb.value.args[0]
                f_ir._definitions[ieesd__vivb.target.name].append(ieesd__vivb
                    .value)
            if is_call_assign(ieesd__vivb) and find_callname(f_ir,
                ieesd__vivb.value) == ('isna', 'bodo.libs.array_kernels'):
                f_ir._definitions[ieesd__vivb.target.name].remove(ieesd__vivb
                    .value)
                ieesd__vivb.value = ir.Const(False, ieesd__vivb.loc)
                f_ir._definitions[ieesd__vivb.target.name].append(ieesd__vivb
                    .value)
            if is_call_assign(ieesd__vivb) and find_callname(f_ir,
                ieesd__vivb.value) == ('setna', 'bodo.libs.array_kernels'):
                f_ir._definitions[ieesd__vivb.target.name].remove(ieesd__vivb
                    .value)
                ieesd__vivb.value = ir.Const(False, ieesd__vivb.loc)
                f_ir._definitions[ieesd__vivb.target.name].append(ieesd__vivb
                    .value)
    bodo.transforms.untyped_pass.remove_dead_branches(f_ir)
    oiue__gdc = numba.parfors.parfor.PreParforPass(f_ir, typemap, calltypes,
        typingctx, targetctx, irhke__ktgo)
    oiue__gdc.run()
    f_ir._definitions = build_definitions(f_ir.blocks)
    lnmx__obr = numba.core.compiler.StateDict()
    lnmx__obr.func_ir = f_ir
    lnmx__obr.typemap = typemap
    lnmx__obr.calltypes = calltypes
    lnmx__obr.typingctx = typingctx
    lnmx__obr.targetctx = targetctx
    lnmx__obr.return_type = qeve__escsn
    numba.core.rewrites.rewrite_registry.apply('after-inference', lnmx__obr)
    mhua__kppki = numba.parfors.parfor.ParforPass(f_ir, typemap, calltypes,
        qeve__escsn, typingctx, targetctx, irhke__ktgo, bxv__yxlsn, {})
    mhua__kppki.run()
    remove_dels(f_ir.blocks)
    numba.parfors.parfor.maximize_fusion(f_ir, f_ir.blocks, typemap, False)
    return f_ir, pm


def replace_closures(f_ir, closure, code):
    if closure:
        closure = f_ir.get_definition(closure)
        if isinstance(closure, tuple):
            cklrc__ocqec = ctypes.pythonapi.PyCell_Get
            cklrc__ocqec.restype = ctypes.py_object
            cklrc__ocqec.argtypes = ctypes.py_object,
            sdplf__mmh = tuple(cklrc__ocqec(ebhd__ipam) for ebhd__ipam in
                closure)
        else:
            assert isinstance(closure, ir.Expr) and closure.op == 'build_tuple'
            sdplf__mmh = closure.items
        assert len(code.co_freevars) == len(sdplf__mmh)
        numba.core.inline_closurecall._replace_freevars(f_ir.blocks, sdplf__mmh
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
        nuyby__fwq = SeriesType(in_col_typ.dtype, in_col_typ, None, string_type
            )
        f_ir, pm = compile_to_optimized_ir(func, (nuyby__fwq,), self.
            typingctx, self.targetctx)
        f_ir._definitions = build_definitions(f_ir.blocks)
        assert len(f_ir.blocks
            ) == 1 and 0 in f_ir.blocks, 'only simple functions with one block supported for aggregation'
        block = f_ir.blocks[0]
        qcuhl__smm, arr_var = _rm_arg_agg_block(block, pm.typemap)
        uolx__hbt = -1
        for rvo__pmu, ieesd__vivb in enumerate(qcuhl__smm):
            if isinstance(ieesd__vivb, numba.parfors.parfor.Parfor):
                assert uolx__hbt == -1, 'only one parfor for aggregation function'
                uolx__hbt = rvo__pmu
        parfor = None
        if uolx__hbt != -1:
            parfor = qcuhl__smm[uolx__hbt]
            remove_dels(parfor.loop_body)
            remove_dels({(0): parfor.init_block})
        init_nodes = []
        if parfor:
            init_nodes = qcuhl__smm[:uolx__hbt] + parfor.init_block.body
        eval_nodes = qcuhl__smm[uolx__hbt + 1:]
        redvars = []
        var_to_redvar = {}
        if parfor:
            redvars, var_to_redvar = get_parfor_reductions(parfor, parfor.
                params, pm.calltypes)
        func.ncols_pre_shuffle = len(redvars)
        func.ncols_post_shuffle = len(redvars) + 1
        func.n_redvars = len(redvars)
        reduce_vars = [0] * len(redvars)
        for ieesd__vivb in init_nodes:
            if is_assign(ieesd__vivb) and ieesd__vivb.target.name in redvars:
                ind = redvars.index(ieesd__vivb.target.name)
                reduce_vars[ind] = ieesd__vivb.target
        var_types = [pm.typemap[ccq__zcay] for ccq__zcay in redvars]
        outhw__ifz = gen_combine_func(f_ir, parfor, redvars, var_to_redvar,
            var_types, arr_var, pm, self.typingctx, self.targetctx)
        init_nodes = _mv_read_only_init_vars(init_nodes, parfor, eval_nodes)
        muvj__kucn = gen_update_func(parfor, redvars, var_to_redvar,
            var_types, arr_var, in_col_typ, pm, self.typingctx, self.targetctx)
        oswts__dst = gen_eval_func(f_ir, eval_nodes, reduce_vars, var_types,
            pm, self.typingctx, self.targetctx)
        self.all_reduce_vars += reduce_vars
        self.all_vartypes += var_types
        self.all_init_nodes += init_nodes
        self.all_eval_funcs.append(oswts__dst)
        self.all_update_funcs.append(muvj__kucn)
        self.all_combine_funcs.append(outhw__ifz)
        self.curr_offset += len(redvars)
        self.redvar_offsets.append(self.curr_offset)

    def gen_all_func(self):
        if len(self.all_update_funcs) == 0:
            return None
        self.all_vartypes = self.all_vartypes * len(self.pivot_values
            ) if self.pivot_values is not None else self.all_vartypes
        self.all_reduce_vars = self.all_reduce_vars * len(self.pivot_values
            ) if self.pivot_values is not None else self.all_reduce_vars
        wsmz__hrq = gen_init_func(self.all_init_nodes, self.all_reduce_vars,
            self.all_vartypes, self.typingctx, self.targetctx)
        rwtt__xbnq = gen_all_update_func(self.all_update_funcs, self.
            all_vartypes, self.in_col_types, self.redvar_offsets, self.
            typingctx, self.targetctx, self.pivot_typ, self.pivot_values,
            self.is_crosstab)
        utgr__lxwc = gen_all_combine_func(self.all_combine_funcs, self.
            all_vartypes, self.redvar_offsets, self.typingctx, self.
            targetctx, self.pivot_typ, self.pivot_values)
        fza__nhp = gen_all_eval_func(self.all_eval_funcs, self.all_vartypes,
            self.redvar_offsets, self.out_col_types, self.typingctx, self.
            targetctx, self.pivot_values)
        return self.all_vartypes, wsmz__hrq, rwtt__xbnq, utgr__lxwc, fza__nhp


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
    grav__lom = []
    for t, pwthh__kjwsu in zip(in_col_types, agg_func):
        grav__lom.append((t, pwthh__kjwsu))
    coxb__psrx = RegularUDFGenerator(in_col_types, out_col_types, pivot_typ,
        pivot_values, is_crosstab, typingctx, targetctx)
    nuc__soy = GeneralUDFGenerator()
    for in_col_typ, func in grav__lom:
        if func.ftype not in ('udf', 'gen_udf'):
            continue
        try:
            coxb__psrx.add_udf(in_col_typ, func)
        except:
            nuc__soy.add_udf(func)
            func.ftype = 'gen_udf'
    regular_udf_funcs = coxb__psrx.gen_all_func()
    general_udf_funcs = nuc__soy.gen_all_func()
    if regular_udf_funcs is not None or general_udf_funcs is not None:
        return AggUDFStruct(regular_udf_funcs, general_udf_funcs)
    else:
        return None


def _mv_read_only_init_vars(init_nodes, parfor, eval_nodes):
    if not parfor:
        return init_nodes
    rspdp__ycltt = compute_use_defs(parfor.loop_body)
    emnwg__kuxkt = set()
    for ojmsc__mbbwm in rspdp__ycltt.usemap.values():
        emnwg__kuxkt |= ojmsc__mbbwm
    eesrd__ryh = set()
    for ojmsc__mbbwm in rspdp__ycltt.defmap.values():
        eesrd__ryh |= ojmsc__mbbwm
    sqj__wrull = ir.Block(ir.Scope(None, parfor.loc), parfor.loc)
    sqj__wrull.body = eval_nodes
    nqvj__lvcx = compute_use_defs({(0): sqj__wrull})
    wrv__qzqi = nqvj__lvcx.usemap[0]
    iudgc__dbpcr = set()
    ejml__cew = []
    qocz__ydcnu = []
    for ieesd__vivb in reversed(init_nodes):
        dhxz__kkiei = {ccq__zcay.name for ccq__zcay in ieesd__vivb.list_vars()}
        if is_assign(ieesd__vivb):
            ccq__zcay = ieesd__vivb.target.name
            dhxz__kkiei.remove(ccq__zcay)
            if (ccq__zcay in emnwg__kuxkt and ccq__zcay not in iudgc__dbpcr and
                ccq__zcay not in wrv__qzqi and ccq__zcay not in eesrd__ryh):
                qocz__ydcnu.append(ieesd__vivb)
                emnwg__kuxkt |= dhxz__kkiei
                eesrd__ryh.add(ccq__zcay)
                continue
        iudgc__dbpcr |= dhxz__kkiei
        ejml__cew.append(ieesd__vivb)
    qocz__ydcnu.reverse()
    ejml__cew.reverse()
    rrq__lmsk = min(parfor.loop_body.keys())
    jlxnl__muyeg = parfor.loop_body[rrq__lmsk]
    jlxnl__muyeg.body = qocz__ydcnu + jlxnl__muyeg.body
    return ejml__cew


def gen_init_func(init_nodes, reduce_vars, var_types, typingctx, targetctx):
    ldgb__qwe = (numba.parfors.parfor.max_checker, numba.parfors.parfor.
        min_checker, numba.parfors.parfor.argmax_checker, numba.parfors.
        parfor.argmin_checker)
    ganmv__djlcw = set()
    oaxa__thpsl = []
    for ieesd__vivb in init_nodes:
        if is_assign(ieesd__vivb) and isinstance(ieesd__vivb.value, ir.Global
            ) and isinstance(ieesd__vivb.value.value, pytypes.FunctionType
            ) and ieesd__vivb.value.value in ldgb__qwe:
            ganmv__djlcw.add(ieesd__vivb.target.name)
        elif is_call_assign(ieesd__vivb
            ) and ieesd__vivb.value.func.name in ganmv__djlcw:
            pass
        else:
            oaxa__thpsl.append(ieesd__vivb)
    init_nodes = oaxa__thpsl
    ams__yumt = types.Tuple(var_types)
    rsn__bzd = lambda : None
    f_ir = compile_to_numba_ir(rsn__bzd, {})
    block = list(f_ir.blocks.values())[0]
    loc = block.loc
    azm__yiqd = ir.Var(block.scope, mk_unique_var('init_tup'), loc)
    vav__xszdl = ir.Assign(ir.Expr.build_tuple(reduce_vars, loc), azm__yiqd,
        loc)
    block.body = block.body[-2:]
    block.body = init_nodes + [vav__xszdl] + block.body
    block.body[-2].value.value = azm__yiqd
    ekv__ogbh = compiler.compile_ir(typingctx, targetctx, f_ir, (),
        ams__yumt, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    ekmg__eacbc = numba.core.target_extension.dispatcher_registry[cpu_target](
        rsn__bzd)
    ekmg__eacbc.add_overload(ekv__ogbh)
    return ekmg__eacbc


def gen_all_update_func(update_funcs, reduce_var_types, in_col_types,
    redvar_offsets, typingctx, targetctx, pivot_typ, pivot_values, is_crosstab
    ):
    sdpd__fvgs = len(update_funcs)
    hwpnj__oimvz = len(in_col_types)
    if pivot_values is not None:
        assert hwpnj__oimvz == 1
    cnqr__fsjy = (
        'def update_all_f(redvar_arrs, data_in, w_ind, i, pivot_arr):\n')
    if pivot_values is not None:
        frijw__cylic = redvar_offsets[hwpnj__oimvz]
        cnqr__fsjy += '  pv = pivot_arr[i]\n'
        for wxn__uem, oxmay__mkek in enumerate(pivot_values):
            mnm__brs = 'el' if wxn__uem != 0 else ''
            cnqr__fsjy += "  {}if pv == '{}':\n".format(mnm__brs, oxmay__mkek)
            msti__fjpkf = frijw__cylic * wxn__uem
            hgq__phko = ', '.join(['redvar_arrs[{}][w_ind]'.format(rvo__pmu
                ) for rvo__pmu in range(msti__fjpkf + redvar_offsets[0], 
                msti__fjpkf + redvar_offsets[1])])
            vsftj__ufk = 'data_in[0][i]'
            if is_crosstab:
                vsftj__ufk = '0'
            cnqr__fsjy += '    {} = update_vars_0({}, {})\n'.format(hgq__phko,
                hgq__phko, vsftj__ufk)
    else:
        for wxn__uem in range(sdpd__fvgs):
            hgq__phko = ', '.join(['redvar_arrs[{}][w_ind]'.format(rvo__pmu
                ) for rvo__pmu in range(redvar_offsets[wxn__uem],
                redvar_offsets[wxn__uem + 1])])
            if hgq__phko:
                cnqr__fsjy += ('  {} = update_vars_{}({},  data_in[{}][i])\n'
                    .format(hgq__phko, wxn__uem, hgq__phko, 0 if 
                    hwpnj__oimvz == 1 else wxn__uem))
    cnqr__fsjy += '  return\n'
    ntsla__yjm = {}
    for rvo__pmu, pwthh__kjwsu in enumerate(update_funcs):
        ntsla__yjm['update_vars_{}'.format(rvo__pmu)] = pwthh__kjwsu
    kojo__bea = {}
    exec(cnqr__fsjy, ntsla__yjm, kojo__bea)
    lepj__eni = kojo__bea['update_all_f']
    return numba.njit(no_cpython_wrapper=True)(lepj__eni)


def gen_all_combine_func(combine_funcs, reduce_var_types, redvar_offsets,
    typingctx, targetctx, pivot_typ, pivot_values):
    athye__zitus = types.Tuple([types.Array(t, 1, 'C') for t in
        reduce_var_types])
    arg_typs = athye__zitus, athye__zitus, types.intp, types.intp, pivot_typ
    gfoos__jknr = len(redvar_offsets) - 1
    frijw__cylic = redvar_offsets[gfoos__jknr]
    cnqr__fsjy = (
        'def combine_all_f(redvar_arrs, recv_arrs, w_ind, i, pivot_arr):\n')
    if pivot_values is not None:
        assert gfoos__jknr == 1
        for fcnuc__ulkj in range(len(pivot_values)):
            msti__fjpkf = frijw__cylic * fcnuc__ulkj
            hgq__phko = ', '.join(['redvar_arrs[{}][w_ind]'.format(rvo__pmu
                ) for rvo__pmu in range(msti__fjpkf + redvar_offsets[0], 
                msti__fjpkf + redvar_offsets[1])])
            osbu__buxru = ', '.join(['recv_arrs[{}][i]'.format(rvo__pmu) for
                rvo__pmu in range(msti__fjpkf + redvar_offsets[0], 
                msti__fjpkf + redvar_offsets[1])])
            cnqr__fsjy += '  {} = combine_vars_0({}, {})\n'.format(hgq__phko,
                hgq__phko, osbu__buxru)
    else:
        for wxn__uem in range(gfoos__jknr):
            hgq__phko = ', '.join(['redvar_arrs[{}][w_ind]'.format(rvo__pmu
                ) for rvo__pmu in range(redvar_offsets[wxn__uem],
                redvar_offsets[wxn__uem + 1])])
            osbu__buxru = ', '.join(['recv_arrs[{}][i]'.format(rvo__pmu) for
                rvo__pmu in range(redvar_offsets[wxn__uem], redvar_offsets[
                wxn__uem + 1])])
            if osbu__buxru:
                cnqr__fsjy += '  {} = combine_vars_{}({}, {})\n'.format(
                    hgq__phko, wxn__uem, hgq__phko, osbu__buxru)
    cnqr__fsjy += '  return\n'
    ntsla__yjm = {}
    for rvo__pmu, pwthh__kjwsu in enumerate(combine_funcs):
        ntsla__yjm['combine_vars_{}'.format(rvo__pmu)] = pwthh__kjwsu
    kojo__bea = {}
    exec(cnqr__fsjy, ntsla__yjm, kojo__bea)
    fpnot__ognfb = kojo__bea['combine_all_f']
    f_ir = compile_to_numba_ir(fpnot__ognfb, ntsla__yjm)
    utgr__lxwc = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        types.none, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    ekmg__eacbc = numba.core.target_extension.dispatcher_registry[cpu_target](
        fpnot__ognfb)
    ekmg__eacbc.add_overload(utgr__lxwc)
    return ekmg__eacbc


def gen_all_eval_func(eval_funcs, reduce_var_types, redvar_offsets,
    out_col_typs, typingctx, targetctx, pivot_values):
    athye__zitus = types.Tuple([types.Array(t, 1, 'C') for t in
        reduce_var_types])
    out_col_typs = types.Tuple(out_col_typs)
    gfoos__jknr = len(redvar_offsets) - 1
    frijw__cylic = redvar_offsets[gfoos__jknr]
    cnqr__fsjy = 'def eval_all_f(redvar_arrs, out_arrs, j):\n'
    if pivot_values is not None:
        assert gfoos__jknr == 1
        for wxn__uem in range(len(pivot_values)):
            msti__fjpkf = frijw__cylic * wxn__uem
            hgq__phko = ', '.join(['redvar_arrs[{}][j]'.format(rvo__pmu) for
                rvo__pmu in range(msti__fjpkf + redvar_offsets[0], 
                msti__fjpkf + redvar_offsets[1])])
            cnqr__fsjy += '  out_arrs[{}][j] = eval_vars_0({})\n'.format(
                wxn__uem, hgq__phko)
    else:
        for wxn__uem in range(gfoos__jknr):
            hgq__phko = ', '.join(['redvar_arrs[{}][j]'.format(rvo__pmu) for
                rvo__pmu in range(redvar_offsets[wxn__uem], redvar_offsets[
                wxn__uem + 1])])
            cnqr__fsjy += '  out_arrs[{}][j] = eval_vars_{}({})\n'.format(
                wxn__uem, wxn__uem, hgq__phko)
    cnqr__fsjy += '  return\n'
    ntsla__yjm = {}
    for rvo__pmu, pwthh__kjwsu in enumerate(eval_funcs):
        ntsla__yjm['eval_vars_{}'.format(rvo__pmu)] = pwthh__kjwsu
    kojo__bea = {}
    exec(cnqr__fsjy, ntsla__yjm, kojo__bea)
    dtc__dpa = kojo__bea['eval_all_f']
    return numba.njit(no_cpython_wrapper=True)(dtc__dpa)


def gen_eval_func(f_ir, eval_nodes, reduce_vars, var_types, pm, typingctx,
    targetctx):
    rvum__oekzl = len(var_types)
    jix__jrp = [f'in{rvo__pmu}' for rvo__pmu in range(rvum__oekzl)]
    ams__yumt = types.unliteral(pm.typemap[eval_nodes[-1].value.name])
    tqsz__adi = ams__yumt(0)
    cnqr__fsjy = 'def agg_eval({}):\n return _zero\n'.format(', '.join(
        jix__jrp))
    kojo__bea = {}
    exec(cnqr__fsjy, {'_zero': tqsz__adi}, kojo__bea)
    acihl__yjfea = kojo__bea['agg_eval']
    arg_typs = tuple(var_types)
    f_ir = compile_to_numba_ir(acihl__yjfea, {'numba': numba, 'bodo': bodo,
        'np': np, '_zero': tqsz__adi}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=arg_typs, typemap=pm.typemap, calltypes=pm.
        calltypes)
    block = list(f_ir.blocks.values())[0]
    xun__upjxg = []
    for rvo__pmu, ccq__zcay in enumerate(reduce_vars):
        xun__upjxg.append(ir.Assign(block.body[rvo__pmu].target, ccq__zcay,
            ccq__zcay.loc))
        for ifu__fmao in ccq__zcay.versioned_names:
            xun__upjxg.append(ir.Assign(ccq__zcay, ir.Var(ccq__zcay.scope,
                ifu__fmao, ccq__zcay.loc), ccq__zcay.loc))
    block.body = block.body[:rvum__oekzl] + xun__upjxg + eval_nodes
    oswts__dst = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        ams__yumt, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    ekmg__eacbc = numba.core.target_extension.dispatcher_registry[cpu_target](
        acihl__yjfea)
    ekmg__eacbc.add_overload(oswts__dst)
    return ekmg__eacbc


def gen_combine_func(f_ir, parfor, redvars, var_to_redvar, var_types,
    arr_var, pm, typingctx, targetctx):
    if not parfor:
        return numba.njit(lambda : ())
    rvum__oekzl = len(redvars)
    hdzc__ugtwk = [f'v{rvo__pmu}' for rvo__pmu in range(rvum__oekzl)]
    jix__jrp = [f'in{rvo__pmu}' for rvo__pmu in range(rvum__oekzl)]
    cnqr__fsjy = 'def agg_combine({}):\n'.format(', '.join(hdzc__ugtwk +
        jix__jrp))
    ztfe__uctdg = wrap_parfor_blocks(parfor)
    whj__vsuw = find_topo_order(ztfe__uctdg)
    whj__vsuw = whj__vsuw[1:]
    unwrap_parfor_blocks(parfor)
    mruxd__shnt = {}
    znwv__bnt = []
    for rak__pyh in whj__vsuw:
        xahy__sjev = parfor.loop_body[rak__pyh]
        for ieesd__vivb in xahy__sjev.body:
            if is_call_assign(ieesd__vivb) and guard(find_callname, f_ir,
                ieesd__vivb.value) == ('__special_combine', 'bodo.ir.aggregate'
                ):
                args = ieesd__vivb.value.args
                siytj__mwdr = []
                szkoq__shzy = []
                for ccq__zcay in args[:-1]:
                    ind = redvars.index(ccq__zcay.name)
                    znwv__bnt.append(ind)
                    siytj__mwdr.append('v{}'.format(ind))
                    szkoq__shzy.append('in{}'.format(ind))
                cauzv__tjnqg = '__special_combine__{}'.format(len(mruxd__shnt))
                cnqr__fsjy += '    ({},) = {}({})\n'.format(', '.join(
                    siytj__mwdr), cauzv__tjnqg, ', '.join(siytj__mwdr +
                    szkoq__shzy))
                lupu__cdjs = ir.Expr.call(args[-1], [], (), xahy__sjev.loc)
                mgs__rwuwg = guard(find_callname, f_ir, lupu__cdjs)
                assert mgs__rwuwg == ('_var_combine', 'bodo.ir.aggregate')
                mgs__rwuwg = bodo.ir.aggregate._var_combine
                mruxd__shnt[cauzv__tjnqg] = mgs__rwuwg
            if is_assign(ieesd__vivb) and ieesd__vivb.target.name in redvars:
                tdlgc__hxl = ieesd__vivb.target.name
                ind = redvars.index(tdlgc__hxl)
                if ind in znwv__bnt:
                    continue
                if len(f_ir._definitions[tdlgc__hxl]) == 2:
                    var_def = f_ir._definitions[tdlgc__hxl][0]
                    cnqr__fsjy += _match_reduce_def(var_def, f_ir, ind)
                    var_def = f_ir._definitions[tdlgc__hxl][1]
                    cnqr__fsjy += _match_reduce_def(var_def, f_ir, ind)
    cnqr__fsjy += '    return {}'.format(', '.join(['v{}'.format(rvo__pmu) for
        rvo__pmu in range(rvum__oekzl)]))
    kojo__bea = {}
    exec(cnqr__fsjy, {}, kojo__bea)
    aqmuh__lgvqd = kojo__bea['agg_combine']
    arg_typs = tuple(2 * var_types)
    ntsla__yjm = {'numba': numba, 'bodo': bodo, 'np': np}
    ntsla__yjm.update(mruxd__shnt)
    f_ir = compile_to_numba_ir(aqmuh__lgvqd, ntsla__yjm, typingctx=
        typingctx, targetctx=targetctx, arg_typs=arg_typs, typemap=pm.
        typemap, calltypes=pm.calltypes)
    block = list(f_ir.blocks.values())[0]
    ams__yumt = pm.typemap[block.body[-1].value.name]
    outhw__ifz = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        ams__yumt, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    ekmg__eacbc = numba.core.target_extension.dispatcher_registry[cpu_target](
        aqmuh__lgvqd)
    ekmg__eacbc.add_overload(outhw__ifz)
    return ekmg__eacbc


def _match_reduce_def(var_def, f_ir, ind):
    cnqr__fsjy = ''
    while isinstance(var_def, ir.Var):
        var_def = guard(get_definition, f_ir, var_def)
    if isinstance(var_def, ir.Expr
        ) and var_def.op == 'inplace_binop' and var_def.fn in ('+=',
        operator.iadd):
        cnqr__fsjy = '    v{} += in{}\n'.format(ind, ind)
    if isinstance(var_def, ir.Expr) and var_def.op == 'call':
        ljqax__pbz = guard(find_callname, f_ir, var_def)
        if ljqax__pbz == ('min', 'builtins'):
            cnqr__fsjy = '    v{} = min(v{}, in{})\n'.format(ind, ind, ind)
        if ljqax__pbz == ('max', 'builtins'):
            cnqr__fsjy = '    v{} = max(v{}, in{})\n'.format(ind, ind, ind)
    return cnqr__fsjy


def gen_update_func(parfor, redvars, var_to_redvar, var_types, arr_var,
    in_col_typ, pm, typingctx, targetctx):
    if not parfor:
        return numba.njit(lambda A: ())
    rvum__oekzl = len(redvars)
    bsks__tglf = 1
    rpijf__qzux = []
    for rvo__pmu in range(bsks__tglf):
        umw__soa = ir.Var(arr_var.scope, f'$input{rvo__pmu}', arr_var.loc)
        rpijf__qzux.append(umw__soa)
    qfzfq__syvaj = parfor.loop_nests[0].index_variable
    aptcd__ctov = [0] * rvum__oekzl
    for xahy__sjev in parfor.loop_body.values():
        evkve__szou = []
        for ieesd__vivb in xahy__sjev.body:
            if is_var_assign(ieesd__vivb
                ) and ieesd__vivb.value.name == qfzfq__syvaj.name:
                continue
            if is_getitem(ieesd__vivb
                ) and ieesd__vivb.value.value.name == arr_var.name:
                ieesd__vivb.value = rpijf__qzux[0]
            if is_call_assign(ieesd__vivb) and guard(find_callname, pm.
                func_ir, ieesd__vivb.value) == ('isna',
                'bodo.libs.array_kernels') and ieesd__vivb.value.args[0
                ].name == arr_var.name:
                ieesd__vivb.value = ir.Const(False, ieesd__vivb.target.loc)
            if is_assign(ieesd__vivb) and ieesd__vivb.target.name in redvars:
                ind = redvars.index(ieesd__vivb.target.name)
                aptcd__ctov[ind] = ieesd__vivb.target
            evkve__szou.append(ieesd__vivb)
        xahy__sjev.body = evkve__szou
    hdzc__ugtwk = ['v{}'.format(rvo__pmu) for rvo__pmu in range(rvum__oekzl)]
    jix__jrp = ['in{}'.format(rvo__pmu) for rvo__pmu in range(bsks__tglf)]
    cnqr__fsjy = 'def agg_update({}):\n'.format(', '.join(hdzc__ugtwk +
        jix__jrp))
    cnqr__fsjy += '    __update_redvars()\n'
    cnqr__fsjy += '    return {}'.format(', '.join(['v{}'.format(rvo__pmu) for
        rvo__pmu in range(rvum__oekzl)]))
    kojo__bea = {}
    exec(cnqr__fsjy, {}, kojo__bea)
    zblcx__rykp = kojo__bea['agg_update']
    arg_typs = tuple(var_types + [in_col_typ.dtype] * bsks__tglf)
    f_ir = compile_to_numba_ir(zblcx__rykp, {'__update_redvars':
        __update_redvars}, typingctx=typingctx, targetctx=targetctx,
        arg_typs=arg_typs, typemap=pm.typemap, calltypes=pm.calltypes)
    f_ir._definitions = build_definitions(f_ir.blocks)
    yxlly__nuv = f_ir.blocks.popitem()[1].body
    ams__yumt = pm.typemap[yxlly__nuv[-1].value.name]
    ztfe__uctdg = wrap_parfor_blocks(parfor)
    whj__vsuw = find_topo_order(ztfe__uctdg)
    whj__vsuw = whj__vsuw[1:]
    unwrap_parfor_blocks(parfor)
    f_ir.blocks = parfor.loop_body
    jlxnl__muyeg = f_ir.blocks[whj__vsuw[0]]
    nksfh__epa = f_ir.blocks[whj__vsuw[-1]]
    pbo__tqjms = yxlly__nuv[:rvum__oekzl + bsks__tglf]
    if rvum__oekzl > 1:
        lcuva__jwrc = yxlly__nuv[-3:]
        assert is_assign(lcuva__jwrc[0]) and isinstance(lcuva__jwrc[0].
            value, ir.Expr) and lcuva__jwrc[0].value.op == 'build_tuple'
    else:
        lcuva__jwrc = yxlly__nuv[-2:]
    for rvo__pmu in range(rvum__oekzl):
        zdr__wuer = yxlly__nuv[rvo__pmu].target
        ktjep__ksf = ir.Assign(zdr__wuer, aptcd__ctov[rvo__pmu], zdr__wuer.loc)
        pbo__tqjms.append(ktjep__ksf)
    for rvo__pmu in range(rvum__oekzl, rvum__oekzl + bsks__tglf):
        zdr__wuer = yxlly__nuv[rvo__pmu].target
        ktjep__ksf = ir.Assign(zdr__wuer, rpijf__qzux[rvo__pmu -
            rvum__oekzl], zdr__wuer.loc)
        pbo__tqjms.append(ktjep__ksf)
    jlxnl__muyeg.body = pbo__tqjms + jlxnl__muyeg.body
    yyc__ifu = []
    for rvo__pmu in range(rvum__oekzl):
        zdr__wuer = yxlly__nuv[rvo__pmu].target
        ktjep__ksf = ir.Assign(aptcd__ctov[rvo__pmu], zdr__wuer, zdr__wuer.loc)
        yyc__ifu.append(ktjep__ksf)
    nksfh__epa.body += yyc__ifu + lcuva__jwrc
    vjq__luew = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        ams__yumt, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    ekmg__eacbc = numba.core.target_extension.dispatcher_registry[cpu_target](
        zblcx__rykp)
    ekmg__eacbc.add_overload(vjq__luew)
    return ekmg__eacbc


def _rm_arg_agg_block(block, typemap):
    qcuhl__smm = []
    arr_var = None
    for rvo__pmu, ieesd__vivb in enumerate(block.body):
        if is_assign(ieesd__vivb) and isinstance(ieesd__vivb.value, ir.Arg):
            arr_var = ieesd__vivb.target
            qcj__dfhef = typemap[arr_var.name]
            if not isinstance(qcj__dfhef, types.ArrayCompatible):
                qcuhl__smm += block.body[rvo__pmu + 1:]
                break
            xqvr__ydk = block.body[rvo__pmu + 1]
            assert is_assign(xqvr__ydk) and isinstance(xqvr__ydk.value, ir.Expr
                ) and xqvr__ydk.value.op == 'getattr' and xqvr__ydk.value.attr == 'shape' and xqvr__ydk.value.value.name == arr_var.name
            rsdz__wikre = xqvr__ydk.target
            pnxz__nweke = block.body[rvo__pmu + 2]
            assert is_assign(pnxz__nweke) and isinstance(pnxz__nweke.value,
                ir.Expr
                ) and pnxz__nweke.value.op == 'static_getitem' and pnxz__nweke.value.value.name == rsdz__wikre.name
            qcuhl__smm += block.body[rvo__pmu + 3:]
            break
        qcuhl__smm.append(ieesd__vivb)
    return qcuhl__smm, arr_var


def get_parfor_reductions(parfor, parfor_params, calltypes, reduce_varnames
    =None, param_uses=None, var_to_param=None):
    if reduce_varnames is None:
        reduce_varnames = []
    if param_uses is None:
        param_uses = defaultdict(list)
    if var_to_param is None:
        var_to_param = {}
    ztfe__uctdg = wrap_parfor_blocks(parfor)
    whj__vsuw = find_topo_order(ztfe__uctdg)
    whj__vsuw = whj__vsuw[1:]
    unwrap_parfor_blocks(parfor)
    for rak__pyh in reversed(whj__vsuw):
        for ieesd__vivb in reversed(parfor.loop_body[rak__pyh].body):
            if isinstance(ieesd__vivb, ir.Assign) and (ieesd__vivb.target.
                name in parfor_params or ieesd__vivb.target.name in
                var_to_param):
                wua__gmdpj = ieesd__vivb.target.name
                rhs = ieesd__vivb.value
                pofi__ushns = (wua__gmdpj if wua__gmdpj in parfor_params else
                    var_to_param[wua__gmdpj])
                hsvo__ahelr = []
                if isinstance(rhs, ir.Var):
                    hsvo__ahelr = [rhs.name]
                elif isinstance(rhs, ir.Expr):
                    hsvo__ahelr = [ccq__zcay.name for ccq__zcay in
                        ieesd__vivb.value.list_vars()]
                param_uses[pofi__ushns].extend(hsvo__ahelr)
                for ccq__zcay in hsvo__ahelr:
                    var_to_param[ccq__zcay] = pofi__ushns
            if isinstance(ieesd__vivb, Parfor):
                get_parfor_reductions(ieesd__vivb, parfor_params, calltypes,
                    reduce_varnames, param_uses, var_to_param)
    for lwvw__bsrf, hsvo__ahelr in param_uses.items():
        if lwvw__bsrf in hsvo__ahelr and lwvw__bsrf not in reduce_varnames:
            reduce_varnames.append(lwvw__bsrf)
    return reduce_varnames, var_to_param


@numba.extending.register_jitable
def dummy_agg_count(A):
    return len(A)
