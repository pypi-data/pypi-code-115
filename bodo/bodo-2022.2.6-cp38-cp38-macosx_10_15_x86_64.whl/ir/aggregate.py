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
            fbf__zeb = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer()])
            kopy__npbz = cgutils.get_or_insert_function(builder.module,
                fbf__zeb, sym._literal_value)
            builder.call(kopy__npbz, [context.get_constant_null(sig.args[0])])
        elif sig == types.none(types.int64, types.voidptr, types.voidptr):
            fbf__zeb = lir.FunctionType(lir.VoidType(), [lir.IntType(64),
                lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
            kopy__npbz = cgutils.get_or_insert_function(builder.module,
                fbf__zeb, sym._literal_value)
            builder.call(kopy__npbz, [context.get_constant(types.int64, 0),
                context.get_constant_null(sig.args[1]), context.
                get_constant_null(sig.args[2])])
        else:
            fbf__zeb = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64).
                as_pointer()])
            kopy__npbz = cgutils.get_or_insert_function(builder.module,
                fbf__zeb, sym._literal_value)
            builder.call(kopy__npbz, [context.get_constant_null(sig.args[0]
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
        xaq__rrsw = True
        sfo__kunde = 1
        heli__vfjl = -1
        if isinstance(rhs, ir.Expr):
            for acbj__hctj in rhs.kws:
                if func_name in list_cumulative:
                    if acbj__hctj[0] == 'skipna':
                        xaq__rrsw = guard(find_const, func_ir, acbj__hctj[1])
                        if not isinstance(xaq__rrsw, bool):
                            raise BodoError(
                                'For {} argument of skipna should be a boolean'
                                .format(func_name))
                if func_name == 'nunique':
                    if acbj__hctj[0] == 'dropna':
                        xaq__rrsw = guard(find_const, func_ir, acbj__hctj[1])
                        if not isinstance(xaq__rrsw, bool):
                            raise BodoError(
                                'argument of dropna to nunique should be a boolean'
                                )
        if func_name == 'shift' and (len(rhs.args) > 0 or len(rhs.kws) > 0):
            sfo__kunde = get_call_expr_arg('shift', rhs.args, dict(rhs.kws),
                0, 'periods', sfo__kunde)
            sfo__kunde = guard(find_const, func_ir, sfo__kunde)
        if func_name == 'head':
            heli__vfjl = get_call_expr_arg('head', rhs.args, dict(rhs.kws),
                0, 'n', 5)
            if not isinstance(heli__vfjl, int):
                heli__vfjl = guard(find_const, func_ir, heli__vfjl)
            if heli__vfjl < 0:
                raise BodoError(
                    f'groupby.{func_name} does not work with negative values.')
        func.skipdropna = xaq__rrsw
        func.periods = sfo__kunde
        func.head_n = heli__vfjl
        if func_name == 'transform':
            kws = dict(rhs.kws)
            nec__adpwb = get_call_expr_arg(func_name, rhs.args, kws, 0,
                'func', '')
            fnkq__rse = typemap[nec__adpwb.name]
            pnaix__qmhg = None
            if isinstance(fnkq__rse, str):
                pnaix__qmhg = fnkq__rse
            elif is_overload_constant_str(fnkq__rse):
                pnaix__qmhg = get_overload_const_str(fnkq__rse)
            elif bodo.utils.typing.is_builtin_function(fnkq__rse):
                pnaix__qmhg = bodo.utils.typing.get_builtin_function_name(
                    fnkq__rse)
            if pnaix__qmhg not in bodo.ir.aggregate.supported_transform_funcs[:
                ]:
                raise BodoError(f'unsupported transform function {pnaix__qmhg}'
                    )
            func.transform_func = supported_agg_funcs.index(pnaix__qmhg)
        else:
            func.transform_func = supported_agg_funcs.index('no_op')
        return func
    assert func_name in ['agg', 'aggregate']
    assert typemap is not None
    kws = dict(rhs.kws)
    nec__adpwb = get_call_expr_arg(func_name, rhs.args, kws, 0, 'func', '')
    if nec__adpwb == '':
        fnkq__rse = types.none
    else:
        fnkq__rse = typemap[nec__adpwb.name]
    if is_overload_constant_dict(fnkq__rse):
        olwgx__mhpf = get_overload_constant_dict(fnkq__rse)
        oogb__fdeu = [get_agg_func_udf(func_ir, f_val, rhs, series_type,
            typemap) for f_val in olwgx__mhpf.values()]
        return oogb__fdeu
    if fnkq__rse == types.none:
        return [get_agg_func_udf(func_ir, get_literal_value(typemap[f_val.
            name])[1], rhs, series_type, typemap) for f_val in kws.values()]
    if isinstance(fnkq__rse, types.BaseTuple):
        oogb__fdeu = []
        obra__tvr = 0
        for t in fnkq__rse.types:
            if is_overload_constant_str(t):
                func_name = get_overload_const_str(t)
                oogb__fdeu.append(get_agg_func(func_ir, func_name, rhs,
                    series_type, typemap))
            else:
                assert typemap is not None, 'typemap is required for agg UDF handling'
                func = _get_const_agg_func(t, func_ir)
                func.ftype = 'udf'
                func.fname = _get_udf_name(func)
                if func.fname == '<lambda>':
                    func.fname = '<lambda_' + str(obra__tvr) + '>'
                    obra__tvr += 1
                oogb__fdeu.append(func)
        return [oogb__fdeu]
    if is_overload_constant_str(fnkq__rse):
        func_name = get_overload_const_str(fnkq__rse)
        return get_agg_func(func_ir, func_name, rhs, series_type, typemap)
    if bodo.utils.typing.is_builtin_function(fnkq__rse):
        func_name = bodo.utils.typing.get_builtin_function_name(fnkq__rse)
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
        obra__tvr = 0
        fmh__wksht = []
        for oogv__hoiuq in f_val:
            func = get_agg_func_udf(func_ir, oogv__hoiuq, rhs, series_type,
                typemap)
            if func.fname == '<lambda>' and len(f_val) > 1:
                func.fname = f'<lambda_{obra__tvr}>'
                obra__tvr += 1
            fmh__wksht.append(func)
        return fmh__wksht
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
    pnaix__qmhg = code.co_name
    return pnaix__qmhg


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
            sgrle__cwrp = types.DType(args[0])
            return signature(sgrle__cwrp, *args)


@numba.njit(no_cpython_wrapper=True)
def _var_combine(ssqdm_a, mean_a, nobs_a, ssqdm_b, mean_b, nobs_b):
    lgoj__uitoo = nobs_a + nobs_b
    lic__uke = (nobs_a * mean_a + nobs_b * mean_b) / lgoj__uitoo
    qqm__qsga = mean_b - mean_a
    dhzt__hsibr = (ssqdm_a + ssqdm_b + qqm__qsga * qqm__qsga * nobs_a *
        nobs_b / lgoj__uitoo)
    return dhzt__hsibr, lic__uke, lgoj__uitoo


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
        git__raxt = ''
        for rgq__ble, khzi__xzatd in self.df_out_vars.items():
            git__raxt += "'{}':{}, ".format(rgq__ble, khzi__xzatd.name)
        sla__kbue = '{}{{{}}}'.format(self.df_out, git__raxt)
        inuc__nypxe = ''
        for rgq__ble, khzi__xzatd in self.df_in_vars.items():
            inuc__nypxe += "'{}':{}, ".format(rgq__ble, khzi__xzatd.name)
        lmbkr__ninjh = '{}{{{}}}'.format(self.df_in, inuc__nypxe)
        oxncj__spcqg = 'pivot {}:{}'.format(self.pivot_arr.name, self.
            pivot_values) if self.pivot_arr is not None else ''
        key_names = ','.join(self.key_names)
        pajcz__zshay = ','.join([khzi__xzatd.name for khzi__xzatd in self.
            key_arrs])
        return 'aggregate: {} = {} [key: {}:{}] {}'.format(sla__kbue,
            lmbkr__ninjh, key_names, pajcz__zshay, oxncj__spcqg)

    def remove_out_col(self, out_col_name):
        self.df_out_vars.pop(out_col_name)
        ustkc__cjul, qbkow__cdn = self.gb_info_out.pop(out_col_name)
        if ustkc__cjul is None and not self.is_crosstab:
            return
        dvc__akzu = self.gb_info_in[ustkc__cjul]
        if self.pivot_arr is not None:
            self.pivot_values.remove(out_col_name)
            for icn__kaww, (func, git__raxt) in enumerate(dvc__akzu):
                try:
                    git__raxt.remove(out_col_name)
                    if len(git__raxt) == 0:
                        dvc__akzu.pop(icn__kaww)
                        break
                except ValueError as vftfu__hkcmr:
                    continue
        else:
            for icn__kaww, (func, fokdw__shtzq) in enumerate(dvc__akzu):
                if fokdw__shtzq == out_col_name:
                    dvc__akzu.pop(icn__kaww)
                    break
        if len(dvc__akzu) == 0:
            self.gb_info_in.pop(ustkc__cjul)
            self.df_in_vars.pop(ustkc__cjul)


def aggregate_usedefs(aggregate_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({khzi__xzatd.name for khzi__xzatd in aggregate_node.
        key_arrs})
    use_set.update({khzi__xzatd.name for khzi__xzatd in aggregate_node.
        df_in_vars.values()})
    if aggregate_node.pivot_arr is not None:
        use_set.add(aggregate_node.pivot_arr.name)
    def_set.update({khzi__xzatd.name for khzi__xzatd in aggregate_node.
        df_out_vars.values()})
    if aggregate_node.out_key_vars is not None:
        def_set.update({khzi__xzatd.name for khzi__xzatd in aggregate_node.
            out_key_vars})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Aggregate] = aggregate_usedefs


def remove_dead_aggregate(aggregate_node, lives_no_aliases, lives,
    arg_aliases, alias_map, func_ir, typemap):
    ryray__zttac = [aqsyi__irm for aqsyi__irm, rsa__dhky in aggregate_node.
        df_out_vars.items() if rsa__dhky.name not in lives]
    for xkv__fnhtm in ryray__zttac:
        aggregate_node.remove_out_col(xkv__fnhtm)
    out_key_vars = aggregate_node.out_key_vars
    if out_key_vars is not None and all(khzi__xzatd.name not in lives for
        khzi__xzatd in out_key_vars):
        aggregate_node.out_key_vars = None
    if len(aggregate_node.df_out_vars
        ) == 0 and aggregate_node.out_key_vars is None:
        return None
    return aggregate_node


ir_utils.remove_dead_extensions[Aggregate] = remove_dead_aggregate


def get_copies_aggregate(aggregate_node, typemap):
    ocsni__aqfbi = set(khzi__xzatd.name for khzi__xzatd in aggregate_node.
        df_out_vars.values())
    if aggregate_node.out_key_vars is not None:
        ocsni__aqfbi.update({khzi__xzatd.name for khzi__xzatd in
            aggregate_node.out_key_vars})
    return set(), ocsni__aqfbi


ir_utils.copy_propagate_extensions[Aggregate] = get_copies_aggregate


def apply_copies_aggregate(aggregate_node, var_dict, name_var_table,
    typemap, calltypes, save_copies):
    for icn__kaww in range(len(aggregate_node.key_arrs)):
        aggregate_node.key_arrs[icn__kaww] = replace_vars_inner(aggregate_node
            .key_arrs[icn__kaww], var_dict)
    for aqsyi__irm in list(aggregate_node.df_in_vars.keys()):
        aggregate_node.df_in_vars[aqsyi__irm] = replace_vars_inner(
            aggregate_node.df_in_vars[aqsyi__irm], var_dict)
    for aqsyi__irm in list(aggregate_node.df_out_vars.keys()):
        aggregate_node.df_out_vars[aqsyi__irm] = replace_vars_inner(
            aggregate_node.df_out_vars[aqsyi__irm], var_dict)
    if aggregate_node.out_key_vars is not None:
        for icn__kaww in range(len(aggregate_node.out_key_vars)):
            aggregate_node.out_key_vars[icn__kaww] = replace_vars_inner(
                aggregate_node.out_key_vars[icn__kaww], var_dict)
    if aggregate_node.pivot_arr is not None:
        aggregate_node.pivot_arr = replace_vars_inner(aggregate_node.
            pivot_arr, var_dict)


ir_utils.apply_copy_propagate_extensions[Aggregate] = apply_copies_aggregate


def visit_vars_aggregate(aggregate_node, callback, cbdata):
    if debug_prints():
        print('visiting aggregate vars for:', aggregate_node)
        print('cbdata: ', sorted(cbdata.items()))
    for icn__kaww in range(len(aggregate_node.key_arrs)):
        aggregate_node.key_arrs[icn__kaww] = visit_vars_inner(aggregate_node
            .key_arrs[icn__kaww], callback, cbdata)
    for aqsyi__irm in list(aggregate_node.df_in_vars.keys()):
        aggregate_node.df_in_vars[aqsyi__irm] = visit_vars_inner(aggregate_node
            .df_in_vars[aqsyi__irm], callback, cbdata)
    for aqsyi__irm in list(aggregate_node.df_out_vars.keys()):
        aggregate_node.df_out_vars[aqsyi__irm] = visit_vars_inner(
            aggregate_node.df_out_vars[aqsyi__irm], callback, cbdata)
    if aggregate_node.out_key_vars is not None:
        for icn__kaww in range(len(aggregate_node.out_key_vars)):
            aggregate_node.out_key_vars[icn__kaww] = visit_vars_inner(
                aggregate_node.out_key_vars[icn__kaww], callback, cbdata)
    if aggregate_node.pivot_arr is not None:
        aggregate_node.pivot_arr = visit_vars_inner(aggregate_node.
            pivot_arr, callback, cbdata)


ir_utils.visit_vars_extensions[Aggregate] = visit_vars_aggregate


def aggregate_array_analysis(aggregate_node, equiv_set, typemap, array_analysis
    ):
    assert len(aggregate_node.df_out_vars
        ) > 0 or aggregate_node.out_key_vars is not None or aggregate_node.is_crosstab, 'empty aggregate in array analysis'
    qexm__wkx = []
    for slu__ubwbw in aggregate_node.key_arrs:
        cni__gree = equiv_set.get_shape(slu__ubwbw)
        if cni__gree:
            qexm__wkx.append(cni__gree[0])
    if aggregate_node.pivot_arr is not None:
        cni__gree = equiv_set.get_shape(aggregate_node.pivot_arr)
        if cni__gree:
            qexm__wkx.append(cni__gree[0])
    for rsa__dhky in aggregate_node.df_in_vars.values():
        cni__gree = equiv_set.get_shape(rsa__dhky)
        if cni__gree:
            qexm__wkx.append(cni__gree[0])
    if len(qexm__wkx) > 1:
        equiv_set.insert_equiv(*qexm__wkx)
    guqpg__kwh = []
    qexm__wkx = []
    hdvrq__wrdu = list(aggregate_node.df_out_vars.values())
    if aggregate_node.out_key_vars is not None:
        hdvrq__wrdu.extend(aggregate_node.out_key_vars)
    for rsa__dhky in hdvrq__wrdu:
        sxqzy__kbcm = typemap[rsa__dhky.name]
        low__fuvm = array_analysis._gen_shape_call(equiv_set, rsa__dhky,
            sxqzy__kbcm.ndim, None, guqpg__kwh)
        equiv_set.insert_equiv(rsa__dhky, low__fuvm)
        qexm__wkx.append(low__fuvm[0])
        equiv_set.define(rsa__dhky, set())
    if len(qexm__wkx) > 1:
        equiv_set.insert_equiv(*qexm__wkx)
    return [], guqpg__kwh


numba.parfors.array_analysis.array_analysis_extensions[Aggregate
    ] = aggregate_array_analysis


def aggregate_distributed_analysis(aggregate_node, array_dists):
    xla__mog = Distribution.OneD
    for rsa__dhky in aggregate_node.df_in_vars.values():
        xla__mog = Distribution(min(xla__mog.value, array_dists[rsa__dhky.
            name].value))
    for slu__ubwbw in aggregate_node.key_arrs:
        xla__mog = Distribution(min(xla__mog.value, array_dists[slu__ubwbw.
            name].value))
    if aggregate_node.pivot_arr is not None:
        xla__mog = Distribution(min(xla__mog.value, array_dists[
            aggregate_node.pivot_arr.name].value))
        array_dists[aggregate_node.pivot_arr.name] = xla__mog
    for rsa__dhky in aggregate_node.df_in_vars.values():
        array_dists[rsa__dhky.name] = xla__mog
    for slu__ubwbw in aggregate_node.key_arrs:
        array_dists[slu__ubwbw.name] = xla__mog
    edku__cccoo = Distribution.OneD_Var
    for rsa__dhky in aggregate_node.df_out_vars.values():
        if rsa__dhky.name in array_dists:
            edku__cccoo = Distribution(min(edku__cccoo.value, array_dists[
                rsa__dhky.name].value))
    if aggregate_node.out_key_vars is not None:
        for rsa__dhky in aggregate_node.out_key_vars:
            if rsa__dhky.name in array_dists:
                edku__cccoo = Distribution(min(edku__cccoo.value,
                    array_dists[rsa__dhky.name].value))
    edku__cccoo = Distribution(min(edku__cccoo.value, xla__mog.value))
    for rsa__dhky in aggregate_node.df_out_vars.values():
        array_dists[rsa__dhky.name] = edku__cccoo
    if aggregate_node.out_key_vars is not None:
        for wal__zvmmn in aggregate_node.out_key_vars:
            array_dists[wal__zvmmn.name] = edku__cccoo
    if edku__cccoo != Distribution.OneD_Var:
        for slu__ubwbw in aggregate_node.key_arrs:
            array_dists[slu__ubwbw.name] = edku__cccoo
        if aggregate_node.pivot_arr is not None:
            array_dists[aggregate_node.pivot_arr.name] = edku__cccoo
        for rsa__dhky in aggregate_node.df_in_vars.values():
            array_dists[rsa__dhky.name] = edku__cccoo


distributed_analysis.distributed_analysis_extensions[Aggregate
    ] = aggregate_distributed_analysis


def build_agg_definitions(agg_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for rsa__dhky in agg_node.df_out_vars.values():
        definitions[rsa__dhky.name].append(agg_node)
    if agg_node.out_key_vars is not None:
        for wal__zvmmn in agg_node.out_key_vars:
            definitions[wal__zvmmn.name].append(agg_node)
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
        for khzi__xzatd in (list(agg_node.df_in_vars.values()) + list(
            agg_node.df_out_vars.values()) + agg_node.key_arrs):
            if array_dists[khzi__xzatd.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                khzi__xzatd.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    hedhd__eem = tuple(typemap[khzi__xzatd.name] for khzi__xzatd in
        agg_node.key_arrs)
    phgs__ilo = [khzi__xzatd for dkksf__yjthy, khzi__xzatd in agg_node.
        df_in_vars.items()]
    uzvpv__nwr = [khzi__xzatd for dkksf__yjthy, khzi__xzatd in agg_node.
        df_out_vars.items()]
    in_col_typs = []
    oogb__fdeu = []
    if agg_node.pivot_arr is not None:
        for ustkc__cjul, dvc__akzu in agg_node.gb_info_in.items():
            for func, qbkow__cdn in dvc__akzu:
                if ustkc__cjul is not None:
                    in_col_typs.append(typemap[agg_node.df_in_vars[
                        ustkc__cjul].name])
                oogb__fdeu.append(func)
    else:
        for ustkc__cjul, func in agg_node.gb_info_out.values():
            if ustkc__cjul is not None:
                in_col_typs.append(typemap[agg_node.df_in_vars[ustkc__cjul]
                    .name])
            oogb__fdeu.append(func)
    out_col_typs = tuple(typemap[khzi__xzatd.name] for khzi__xzatd in
        uzvpv__nwr)
    pivot_typ = types.none if agg_node.pivot_arr is None else typemap[agg_node
        .pivot_arr.name]
    arg_typs = tuple(hedhd__eem + tuple(typemap[khzi__xzatd.name] for
        khzi__xzatd in phgs__ilo) + (pivot_typ,))
    in_col_typs = [to_str_arr_if_dict_array(t) for t in in_col_typs]
    zqmw__xga = {'bodo': bodo, 'np': np, 'dt64_dtype': np.dtype(
        'datetime64[ns]'), 'td64_dtype': np.dtype('timedelta64[ns]')}
    for icn__kaww, in_col_typ in enumerate(in_col_typs):
        if isinstance(in_col_typ, bodo.CategoricalArrayType):
            zqmw__xga.update({f'in_cat_dtype_{icn__kaww}': in_col_typ})
    for icn__kaww, mcnhm__affp in enumerate(out_col_typs):
        if isinstance(mcnhm__affp, bodo.CategoricalArrayType):
            zqmw__xga.update({f'out_cat_dtype_{icn__kaww}': mcnhm__affp})
    udf_func_struct = get_udf_func_struct(oogb__fdeu, agg_node.
        input_has_index, in_col_typs, out_col_typs, typingctx, targetctx,
        pivot_typ, agg_node.pivot_values, agg_node.is_crosstab)
    qtcma__xtr = gen_top_level_agg_func(agg_node, in_col_typs, out_col_typs,
        parallel, udf_func_struct)
    zqmw__xga.update({'pd': pd, 'pre_alloc_string_array':
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
            zqmw__xga.update({'__update_redvars': udf_func_struct.
                update_all_func, '__init_func': udf_func_struct.init_func,
                '__combine_redvars': udf_func_struct.combine_all_func,
                '__eval_res': udf_func_struct.eval_all_func,
                'cpp_cb_update': udf_func_struct.regular_udf_cfuncs[0],
                'cpp_cb_combine': udf_func_struct.regular_udf_cfuncs[1],
                'cpp_cb_eval': udf_func_struct.regular_udf_cfuncs[2]})
        if udf_func_struct.general_udfs:
            zqmw__xga.update({'cpp_cb_general': udf_func_struct.
                general_udf_cfunc})
    agk__nyj = compile_to_numba_ir(qtcma__xtr, zqmw__xga, typingctx=
        typingctx, targetctx=targetctx, arg_typs=arg_typs, typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    pknt__blgf = []
    if agg_node.pivot_arr is None:
        hqzew__vhyt = agg_node.key_arrs[0].scope
        loc = agg_node.loc
        blkz__vbj = ir.Var(hqzew__vhyt, mk_unique_var('dummy_none'), loc)
        typemap[blkz__vbj.name] = types.none
        pknt__blgf.append(ir.Assign(ir.Const(None, loc), blkz__vbj, loc))
        phgs__ilo.append(blkz__vbj)
    else:
        phgs__ilo.append(agg_node.pivot_arr)
    replace_arg_nodes(agk__nyj, agg_node.key_arrs + phgs__ilo)
    gugp__knwvt = agk__nyj.body[-3]
    assert is_assign(gugp__knwvt) and isinstance(gugp__knwvt.value, ir.Expr
        ) and gugp__knwvt.value.op == 'build_tuple'
    pknt__blgf += agk__nyj.body[:-3]
    hdvrq__wrdu = list(agg_node.df_out_vars.values())
    if agg_node.out_key_vars is not None:
        hdvrq__wrdu += agg_node.out_key_vars
    for icn__kaww, jxga__pkv in enumerate(hdvrq__wrdu):
        oby__tlf = gugp__knwvt.value.items[icn__kaww]
        pknt__blgf.append(ir.Assign(oby__tlf, jxga__pkv, jxga__pkv.loc))
    return pknt__blgf


distributed_pass.distributed_run_extensions[Aggregate] = agg_distributed_run


def get_numba_set(dtype):
    pass


@infer_global(get_numba_set)
class GetNumbaSetTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 1
        lsb__cauud = args[0]
        dtype = types.Tuple([t.dtype for t in lsb__cauud.types]) if isinstance(
            lsb__cauud, types.BaseTuple) else lsb__cauud.dtype
        if isinstance(lsb__cauud, types.BaseTuple) and len(lsb__cauud.types
            ) == 1:
            dtype = lsb__cauud.types[0].dtype
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
        mxgf__idr = args[0]
        if mxgf__idr == types.none:
            return signature(types.boolean, *args)


@lower_builtin(bool, types.none)
def lower_column_mean_impl(context, builder, sig, args):
    jjp__pwd = context.compile_internal(builder, lambda a: False, sig, args)
    return jjp__pwd


def _gen_dummy_alloc(t, colnum=0, is_input=False):
    if isinstance(t, IntegerArrayType):
        pyomn__xoz = IntDtype(t.dtype).name
        assert pyomn__xoz.endswith('Dtype()')
        pyomn__xoz = pyomn__xoz[:-7]
        return (
            f"bodo.hiframes.pd_series_ext.get_series_data(pd.Series([1], dtype='{pyomn__xoz}'))"
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
        kdl__vby = 'in' if is_input else 'out'
        return f'bodo.utils.utils.alloc_type(1, {kdl__vby}_cat_dtype_{colnum})'
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
    iqndo__staam = udf_func_struct.var_typs
    xzc__ufpd = len(iqndo__staam)
    lrk__iud = (
        'def bodo_gb_udf_update_local{}(in_table, out_table, row_to_group):\n'
        .format(label_suffix))
    lrk__iud += '    if is_null_pointer(in_table):\n'
    lrk__iud += '        return\n'
    lrk__iud += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in iqndo__staam]),
        ',' if len(iqndo__staam) == 1 else '')
    zfqck__ldtjw = n_keys
    vvzb__jycr = []
    redvar_offsets = []
    yyigw__wishb = []
    if do_combine:
        for icn__kaww, oogv__hoiuq in enumerate(allfuncs):
            if oogv__hoiuq.ftype != 'udf':
                zfqck__ldtjw += oogv__hoiuq.ncols_pre_shuffle
            else:
                redvar_offsets += list(range(zfqck__ldtjw, zfqck__ldtjw +
                    oogv__hoiuq.n_redvars))
                zfqck__ldtjw += oogv__hoiuq.n_redvars
                yyigw__wishb.append(data_in_typs_[func_idx_to_in_col[
                    icn__kaww]])
                vvzb__jycr.append(func_idx_to_in_col[icn__kaww] + n_keys)
    else:
        for icn__kaww, oogv__hoiuq in enumerate(allfuncs):
            if oogv__hoiuq.ftype != 'udf':
                zfqck__ldtjw += oogv__hoiuq.ncols_post_shuffle
            else:
                redvar_offsets += list(range(zfqck__ldtjw + 1, zfqck__ldtjw +
                    1 + oogv__hoiuq.n_redvars))
                zfqck__ldtjw += oogv__hoiuq.n_redvars + 1
                yyigw__wishb.append(data_in_typs_[func_idx_to_in_col[
                    icn__kaww]])
                vvzb__jycr.append(func_idx_to_in_col[icn__kaww] + n_keys)
    assert len(redvar_offsets) == xzc__ufpd
    ucpes__vpb = len(yyigw__wishb)
    ndpwh__dpt = []
    for icn__kaww, t in enumerate(yyigw__wishb):
        ndpwh__dpt.append(_gen_dummy_alloc(t, icn__kaww, True))
    lrk__iud += '    data_in_dummy = ({}{})\n'.format(','.join(ndpwh__dpt),
        ',' if len(yyigw__wishb) == 1 else '')
    lrk__iud += """
    # initialize redvar cols
"""
    lrk__iud += '    init_vals = __init_func()\n'
    for icn__kaww in range(xzc__ufpd):
        lrk__iud += (
            """    redvar_arr_{} = info_to_array(info_from_table(out_table, {}), data_redvar_dummy[{}])
"""
            .format(icn__kaww, redvar_offsets[icn__kaww], icn__kaww))
        lrk__iud += '    incref(redvar_arr_{})\n'.format(icn__kaww)
        lrk__iud += '    redvar_arr_{}.fill(init_vals[{}])\n'.format(icn__kaww,
            icn__kaww)
    lrk__iud += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'.
        format(icn__kaww) for icn__kaww in range(xzc__ufpd)]), ',' if 
        xzc__ufpd == 1 else '')
    lrk__iud += '\n'
    for icn__kaww in range(ucpes__vpb):
        lrk__iud += (
            """    data_in_{} = info_to_array(info_from_table(in_table, {}), data_in_dummy[{}])
"""
            .format(icn__kaww, vvzb__jycr[icn__kaww], icn__kaww))
        lrk__iud += '    incref(data_in_{})\n'.format(icn__kaww)
    lrk__iud += '    data_in = ({}{})\n'.format(','.join(['data_in_{}'.
        format(icn__kaww) for icn__kaww in range(ucpes__vpb)]), ',' if 
        ucpes__vpb == 1 else '')
    lrk__iud += '\n'
    lrk__iud += '    for i in range(len(data_in_0)):\n'
    lrk__iud += '        w_ind = row_to_group[i]\n'
    lrk__iud += '        if w_ind != -1:\n'
    lrk__iud += (
        '            __update_redvars(redvars, data_in, w_ind, i, pivot_arr=None)\n'
        )
    rja__goc = {}
    exec(lrk__iud, {'bodo': bodo, 'np': np, 'pd': pd, 'info_to_array':
        info_to_array, 'info_from_table': info_from_table, 'incref': incref,
        'pre_alloc_string_array': pre_alloc_string_array, '__init_func':
        udf_func_struct.init_func, '__update_redvars': udf_func_struct.
        update_all_func, 'is_null_pointer': is_null_pointer, 'dt64_dtype':
        np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, rja__goc)
    return rja__goc['bodo_gb_udf_update_local{}'.format(label_suffix)]


def gen_combine_cb(udf_func_struct, allfuncs, n_keys, out_data_typs,
    label_suffix):
    iqndo__staam = udf_func_struct.var_typs
    xzc__ufpd = len(iqndo__staam)
    lrk__iud = (
        'def bodo_gb_udf_combine{}(in_table, out_table, row_to_group):\n'.
        format(label_suffix))
    lrk__iud += '    if is_null_pointer(in_table):\n'
    lrk__iud += '        return\n'
    lrk__iud += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in iqndo__staam]),
        ',' if len(iqndo__staam) == 1 else '')
    vjyt__oxrk = n_keys
    dxpmj__kwb = n_keys
    yyf__hyfj = []
    cfua__dph = []
    for oogv__hoiuq in allfuncs:
        if oogv__hoiuq.ftype != 'udf':
            vjyt__oxrk += oogv__hoiuq.ncols_pre_shuffle
            dxpmj__kwb += oogv__hoiuq.ncols_post_shuffle
        else:
            yyf__hyfj += list(range(vjyt__oxrk, vjyt__oxrk + oogv__hoiuq.
                n_redvars))
            cfua__dph += list(range(dxpmj__kwb + 1, dxpmj__kwb + 1 +
                oogv__hoiuq.n_redvars))
            vjyt__oxrk += oogv__hoiuq.n_redvars
            dxpmj__kwb += 1 + oogv__hoiuq.n_redvars
    assert len(yyf__hyfj) == xzc__ufpd
    lrk__iud += """
    # initialize redvar cols
"""
    lrk__iud += '    init_vals = __init_func()\n'
    for icn__kaww in range(xzc__ufpd):
        lrk__iud += (
            """    redvar_arr_{} = info_to_array(info_from_table(out_table, {}), data_redvar_dummy[{}])
"""
            .format(icn__kaww, cfua__dph[icn__kaww], icn__kaww))
        lrk__iud += '    incref(redvar_arr_{})\n'.format(icn__kaww)
        lrk__iud += '    redvar_arr_{}.fill(init_vals[{}])\n'.format(icn__kaww,
            icn__kaww)
    lrk__iud += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'.
        format(icn__kaww) for icn__kaww in range(xzc__ufpd)]), ',' if 
        xzc__ufpd == 1 else '')
    lrk__iud += '\n'
    for icn__kaww in range(xzc__ufpd):
        lrk__iud += (
            """    recv_redvar_arr_{} = info_to_array(info_from_table(in_table, {}), data_redvar_dummy[{}])
"""
            .format(icn__kaww, yyf__hyfj[icn__kaww], icn__kaww))
        lrk__iud += '    incref(recv_redvar_arr_{})\n'.format(icn__kaww)
    lrk__iud += '    recv_redvars = ({}{})\n'.format(','.join([
        'recv_redvar_arr_{}'.format(icn__kaww) for icn__kaww in range(
        xzc__ufpd)]), ',' if xzc__ufpd == 1 else '')
    lrk__iud += '\n'
    if xzc__ufpd:
        lrk__iud += '    for i in range(len(recv_redvar_arr_0)):\n'
        lrk__iud += '        w_ind = row_to_group[i]\n'
        lrk__iud += (
            '        __combine_redvars(redvars, recv_redvars, w_ind, i, pivot_arr=None)\n'
            )
    rja__goc = {}
    exec(lrk__iud, {'np': np, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref, '__init_func':
        udf_func_struct.init_func, '__combine_redvars': udf_func_struct.
        combine_all_func, 'is_null_pointer': is_null_pointer, 'dt64_dtype':
        np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, rja__goc)
    return rja__goc['bodo_gb_udf_combine{}'.format(label_suffix)]


def gen_eval_cb(udf_func_struct, allfuncs, n_keys, out_data_typs_, label_suffix
    ):
    iqndo__staam = udf_func_struct.var_typs
    xzc__ufpd = len(iqndo__staam)
    zfqck__ldtjw = n_keys
    redvar_offsets = []
    jzgo__xiaa = []
    out_data_typs = []
    for icn__kaww, oogv__hoiuq in enumerate(allfuncs):
        if oogv__hoiuq.ftype != 'udf':
            zfqck__ldtjw += oogv__hoiuq.ncols_post_shuffle
        else:
            jzgo__xiaa.append(zfqck__ldtjw)
            redvar_offsets += list(range(zfqck__ldtjw + 1, zfqck__ldtjw + 1 +
                oogv__hoiuq.n_redvars))
            zfqck__ldtjw += 1 + oogv__hoiuq.n_redvars
            out_data_typs.append(out_data_typs_[icn__kaww])
    assert len(redvar_offsets) == xzc__ufpd
    ucpes__vpb = len(out_data_typs)
    lrk__iud = 'def bodo_gb_udf_eval{}(table):\n'.format(label_suffix)
    lrk__iud += '    if is_null_pointer(table):\n'
    lrk__iud += '        return\n'
    lrk__iud += '    data_redvar_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t)) for t in iqndo__staam]),
        ',' if len(iqndo__staam) == 1 else '')
    lrk__iud += '    out_data_dummy = ({}{})\n'.format(','.join([
        'np.empty(1, {})'.format(_get_np_dtype(t.dtype)) for t in
        out_data_typs]), ',' if len(out_data_typs) == 1 else '')
    for icn__kaww in range(xzc__ufpd):
        lrk__iud += (
            """    redvar_arr_{} = info_to_array(info_from_table(table, {}), data_redvar_dummy[{}])
"""
            .format(icn__kaww, redvar_offsets[icn__kaww], icn__kaww))
        lrk__iud += '    incref(redvar_arr_{})\n'.format(icn__kaww)
    lrk__iud += '    redvars = ({}{})\n'.format(','.join(['redvar_arr_{}'.
        format(icn__kaww) for icn__kaww in range(xzc__ufpd)]), ',' if 
        xzc__ufpd == 1 else '')
    lrk__iud += '\n'
    for icn__kaww in range(ucpes__vpb):
        lrk__iud += (
            """    data_out_{} = info_to_array(info_from_table(table, {}), out_data_dummy[{}])
"""
            .format(icn__kaww, jzgo__xiaa[icn__kaww], icn__kaww))
        lrk__iud += '    incref(data_out_{})\n'.format(icn__kaww)
    lrk__iud += '    data_out = ({}{})\n'.format(','.join(['data_out_{}'.
        format(icn__kaww) for icn__kaww in range(ucpes__vpb)]), ',' if 
        ucpes__vpb == 1 else '')
    lrk__iud += '\n'
    lrk__iud += '    for i in range(len(data_out_0)):\n'
    lrk__iud += '        __eval_res(redvars, data_out, i)\n'
    rja__goc = {}
    exec(lrk__iud, {'np': np, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref, '__eval_res':
        udf_func_struct.eval_all_func, 'is_null_pointer': is_null_pointer,
        'dt64_dtype': np.dtype('datetime64[ns]'), 'td64_dtype': np.dtype(
        'timedelta64[ns]')}, rja__goc)
    return rja__goc['bodo_gb_udf_eval{}'.format(label_suffix)]


def gen_general_udf_cb(udf_func_struct, allfuncs, n_keys, in_col_typs,
    out_col_typs, func_idx_to_in_col, label_suffix):
    zfqck__ldtjw = n_keys
    bmnoz__nocy = []
    for icn__kaww, oogv__hoiuq in enumerate(allfuncs):
        if oogv__hoiuq.ftype == 'gen_udf':
            bmnoz__nocy.append(zfqck__ldtjw)
            zfqck__ldtjw += 1
        elif oogv__hoiuq.ftype != 'udf':
            zfqck__ldtjw += oogv__hoiuq.ncols_post_shuffle
        else:
            zfqck__ldtjw += oogv__hoiuq.n_redvars + 1
    lrk__iud = (
        'def bodo_gb_apply_general_udfs{}(num_groups, in_table, out_table):\n'
        .format(label_suffix))
    lrk__iud += '    if num_groups == 0:\n'
    lrk__iud += '        return\n'
    for icn__kaww, func in enumerate(udf_func_struct.general_udf_funcs):
        lrk__iud += '    # col {}\n'.format(icn__kaww)
        lrk__iud += (
            '    out_col = info_to_array(info_from_table(out_table, {}), out_col_{}_typ)\n'
            .format(bmnoz__nocy[icn__kaww], icn__kaww))
        lrk__iud += '    incref(out_col)\n'
        lrk__iud += '    for j in range(num_groups):\n'
        lrk__iud += (
            """        in_col = info_to_array(info_from_table(in_table, {}*num_groups + j), in_col_{}_typ)
"""
            .format(icn__kaww, icn__kaww))
        lrk__iud += '        incref(in_col)\n'
        lrk__iud += (
            '        out_col[j] = func_{}(pd.Series(in_col))  # func returns scalar\n'
            .format(icn__kaww))
    zqmw__xga = {'pd': pd, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'incref': incref}
    zyh__lwu = 0
    for icn__kaww, func in enumerate(allfuncs):
        if func.ftype != 'gen_udf':
            continue
        func = udf_func_struct.general_udf_funcs[zyh__lwu]
        zqmw__xga['func_{}'.format(zyh__lwu)] = func
        zqmw__xga['in_col_{}_typ'.format(zyh__lwu)] = in_col_typs[
            func_idx_to_in_col[icn__kaww]]
        zqmw__xga['out_col_{}_typ'.format(zyh__lwu)] = out_col_typs[icn__kaww]
        zyh__lwu += 1
    rja__goc = {}
    exec(lrk__iud, zqmw__xga, rja__goc)
    oogv__hoiuq = rja__goc['bodo_gb_apply_general_udfs{}'.format(label_suffix)]
    tnq__deyv = types.void(types.int64, types.voidptr, types.voidptr)
    return numba.cfunc(tnq__deyv, nopython=True)(oogv__hoiuq)


def gen_top_level_agg_func(agg_node, in_col_typs, out_col_typs, parallel,
    udf_func_struct):
    qlh__qdqjk = agg_node.pivot_arr is not None
    if agg_node.same_index:
        assert agg_node.input_has_index
    if agg_node.pivot_values is None:
        log__mioz = 1
    else:
        log__mioz = len(agg_node.pivot_values)
    tvvt__uek = tuple('key_' + sanitize_varname(rgq__ble) for rgq__ble in
        agg_node.key_names)
    qyv__eqdm = {rgq__ble: 'in_{}'.format(sanitize_varname(rgq__ble)) for
        rgq__ble in agg_node.gb_info_in.keys() if rgq__ble is not None}
    eawtj__zcxly = {rgq__ble: ('out_' + sanitize_varname(rgq__ble)) for
        rgq__ble in agg_node.gb_info_out.keys()}
    n_keys = len(agg_node.key_names)
    odxry__xwn = ', '.join(tvvt__uek)
    defq__qge = ', '.join(qyv__eqdm.values())
    if defq__qge != '':
        defq__qge = ', ' + defq__qge
    lrk__iud = 'def agg_top({}{}{}, pivot_arr):\n'.format(odxry__xwn,
        defq__qge, ', index_arg' if agg_node.input_has_index else '')
    for a in (tvvt__uek + tuple(qyv__eqdm.values())):
        lrk__iud += f'    {a} = decode_if_dict_array({a})\n'
    if qlh__qdqjk:
        lrk__iud += f'    pivot_arr = decode_if_dict_array(pivot_arr)\n'
        aig__kjj = []
        for ustkc__cjul, dvc__akzu in agg_node.gb_info_in.items():
            if ustkc__cjul is not None:
                for func, qbkow__cdn in dvc__akzu:
                    aig__kjj.append(qyv__eqdm[ustkc__cjul])
    else:
        aig__kjj = tuple(qyv__eqdm[ustkc__cjul] for ustkc__cjul, qbkow__cdn in
            agg_node.gb_info_out.values() if ustkc__cjul is not None)
    fgb__liq = tvvt__uek + tuple(aig__kjj)
    lrk__iud += '    info_list = [{}{}{}]\n'.format(', '.join(
        'array_to_info({})'.format(a) for a in fgb__liq), 
        ', array_to_info(index_arg)' if agg_node.input_has_index else '', 
        ', array_to_info(pivot_arr)' if agg_node.is_crosstab else '')
    lrk__iud += '    table = arr_info_list_to_table(info_list)\n'
    for icn__kaww, rgq__ble in enumerate(agg_node.gb_info_out.keys()):
        ftacr__tac = eawtj__zcxly[rgq__ble] + '_dummy'
        mcnhm__affp = out_col_typs[icn__kaww]
        ustkc__cjul, func = agg_node.gb_info_out[rgq__ble]
        if isinstance(func, pytypes.SimpleNamespace) and func.fname in ['min',
            'max', 'shift'] and isinstance(mcnhm__affp, bodo.
            CategoricalArrayType):
            lrk__iud += '    {} = {}\n'.format(ftacr__tac, qyv__eqdm[
                ustkc__cjul])
        else:
            lrk__iud += '    {} = {}\n'.format(ftacr__tac, _gen_dummy_alloc
                (mcnhm__affp, icn__kaww, False))
    do_combine = parallel
    allfuncs = []
    lqz__ffd = []
    func_idx_to_in_col = []
    qsh__dkpi = []
    xaq__rrsw = False
    aaj__gsoo = 1
    heli__vfjl = -1
    tcm__tmwl = 0
    dqvf__pex = 0
    if not qlh__qdqjk:
        oogb__fdeu = [func for qbkow__cdn, func in agg_node.gb_info_out.
            values()]
    else:
        oogb__fdeu = [func for func, qbkow__cdn in dvc__akzu for dvc__akzu in
            agg_node.gb_info_in.values()]
    for xcmjv__vuq, func in enumerate(oogb__fdeu):
        lqz__ffd.append(len(allfuncs))
        if func.ftype in {'median', 'nunique'}:
            do_combine = False
        if func.ftype in list_cumulative:
            tcm__tmwl += 1
        if hasattr(func, 'skipdropna'):
            xaq__rrsw = func.skipdropna
        if func.ftype == 'shift':
            aaj__gsoo = func.periods
            do_combine = False
        if func.ftype in {'transform'}:
            dqvf__pex = func.transform_func
            do_combine = False
        if func.ftype == 'head':
            heli__vfjl = func.head_n
            do_combine = False
        allfuncs.append(func)
        func_idx_to_in_col.append(xcmjv__vuq)
        if func.ftype == 'udf':
            qsh__dkpi.append(func.n_redvars)
        elif func.ftype == 'gen_udf':
            qsh__dkpi.append(0)
            do_combine = False
    lqz__ffd.append(len(allfuncs))
    if agg_node.is_crosstab:
        assert len(agg_node.gb_info_out
            ) == log__mioz, 'invalid number of groupby outputs for pivot'
    else:
        assert len(agg_node.gb_info_out) == len(allfuncs
            ) * log__mioz, 'invalid number of groupby outputs'
    if tcm__tmwl > 0:
        if tcm__tmwl != len(allfuncs):
            raise BodoError(
                f'{agg_node.func_name}(): Cannot mix cumulative operations with other aggregation functions'
                , loc=agg_node.loc)
        do_combine = False
    if udf_func_struct is not None:
        knggh__fvmwp = next_label()
        if udf_func_struct.regular_udfs:
            tnq__deyv = types.void(types.voidptr, types.voidptr, types.
                CPointer(types.int64))
            yzej__mugxe = numba.cfunc(tnq__deyv, nopython=True)(gen_update_cb
                (udf_func_struct, allfuncs, n_keys, in_col_typs,
                out_col_typs, do_combine, func_idx_to_in_col, knggh__fvmwp))
            iuxro__vplmb = numba.cfunc(tnq__deyv, nopython=True)(gen_combine_cb
                (udf_func_struct, allfuncs, n_keys, out_col_typs, knggh__fvmwp)
                )
            fzv__cgcu = numba.cfunc('void(voidptr)', nopython=True)(gen_eval_cb
                (udf_func_struct, allfuncs, n_keys, out_col_typs, knggh__fvmwp)
                )
            udf_func_struct.set_regular_cfuncs(yzej__mugxe, iuxro__vplmb,
                fzv__cgcu)
            for uvj__opovx in udf_func_struct.regular_udf_cfuncs:
                gb_agg_cfunc[uvj__opovx.native_name] = uvj__opovx
                gb_agg_cfunc_addr[uvj__opovx.native_name] = uvj__opovx.address
        if udf_func_struct.general_udfs:
            czj__jvf = gen_general_udf_cb(udf_func_struct, allfuncs, n_keys,
                in_col_typs, out_col_typs, func_idx_to_in_col, knggh__fvmwp)
            udf_func_struct.set_general_cfunc(czj__jvf)
        zccv__hzddp = []
        ajfma__nzsi = 0
        icn__kaww = 0
        for ftacr__tac, oogv__hoiuq in zip(eawtj__zcxly.values(), allfuncs):
            if oogv__hoiuq.ftype in ('udf', 'gen_udf'):
                zccv__hzddp.append(ftacr__tac + '_dummy')
                for xrrp__xwy in range(ajfma__nzsi, ajfma__nzsi + qsh__dkpi
                    [icn__kaww]):
                    zccv__hzddp.append('data_redvar_dummy_' + str(xrrp__xwy))
                ajfma__nzsi += qsh__dkpi[icn__kaww]
                icn__kaww += 1
        if udf_func_struct.regular_udfs:
            iqndo__staam = udf_func_struct.var_typs
            for icn__kaww, t in enumerate(iqndo__staam):
                lrk__iud += ('    data_redvar_dummy_{} = np.empty(1, {})\n'
                    .format(icn__kaww, _get_np_dtype(t)))
        lrk__iud += '    out_info_list_dummy = [{}]\n'.format(', '.join(
            'array_to_info({})'.format(a) for a in zccv__hzddp))
        lrk__iud += (
            '    udf_table_dummy = arr_info_list_to_table(out_info_list_dummy)\n'
            )
        if udf_func_struct.regular_udfs:
            lrk__iud += "    add_agg_cfunc_sym(cpp_cb_update, '{}')\n".format(
                yzej__mugxe.native_name)
            lrk__iud += "    add_agg_cfunc_sym(cpp_cb_combine, '{}')\n".format(
                iuxro__vplmb.native_name)
            lrk__iud += "    add_agg_cfunc_sym(cpp_cb_eval, '{}')\n".format(
                fzv__cgcu.native_name)
            lrk__iud += ("    cpp_cb_update_addr = get_agg_udf_addr('{}')\n"
                .format(yzej__mugxe.native_name))
            lrk__iud += ("    cpp_cb_combine_addr = get_agg_udf_addr('{}')\n"
                .format(iuxro__vplmb.native_name))
            lrk__iud += ("    cpp_cb_eval_addr = get_agg_udf_addr('{}')\n".
                format(fzv__cgcu.native_name))
        else:
            lrk__iud += '    cpp_cb_update_addr = 0\n'
            lrk__iud += '    cpp_cb_combine_addr = 0\n'
            lrk__iud += '    cpp_cb_eval_addr = 0\n'
        if udf_func_struct.general_udfs:
            uvj__opovx = udf_func_struct.general_udf_cfunc
            gb_agg_cfunc[uvj__opovx.native_name] = uvj__opovx
            gb_agg_cfunc_addr[uvj__opovx.native_name] = uvj__opovx.address
            lrk__iud += "    add_agg_cfunc_sym(cpp_cb_general, '{}')\n".format(
                uvj__opovx.native_name)
            lrk__iud += ("    cpp_cb_general_addr = get_agg_udf_addr('{}')\n"
                .format(uvj__opovx.native_name))
        else:
            lrk__iud += '    cpp_cb_general_addr = 0\n'
    else:
        lrk__iud += (
            '    udf_table_dummy = arr_info_list_to_table([array_to_info(np.empty(1))])\n'
            )
        lrk__iud += '    cpp_cb_update_addr = 0\n'
        lrk__iud += '    cpp_cb_combine_addr = 0\n'
        lrk__iud += '    cpp_cb_eval_addr = 0\n'
        lrk__iud += '    cpp_cb_general_addr = 0\n'
    lrk__iud += '    ftypes = np.array([{}, 0], dtype=np.int32)\n'.format(', '
        .join([str(supported_agg_funcs.index(oogv__hoiuq.ftype)) for
        oogv__hoiuq in allfuncs] + ['0']))
    lrk__iud += '    func_offsets = np.array({}, dtype=np.int32)\n'.format(str
        (lqz__ffd))
    if len(qsh__dkpi) > 0:
        lrk__iud += '    udf_ncols = np.array({}, dtype=np.int32)\n'.format(str
            (qsh__dkpi))
    else:
        lrk__iud += '    udf_ncols = np.array([0], np.int32)\n'
    if qlh__qdqjk:
        lrk__iud += '    arr_type = coerce_to_array({})\n'.format(agg_node.
            pivot_values)
        lrk__iud += '    arr_info = array_to_info(arr_type)\n'
        lrk__iud += '    dispatch_table = arr_info_list_to_table([arr_info])\n'
        lrk__iud += '    pivot_info = array_to_info(pivot_arr)\n'
        lrk__iud += (
            '    dispatch_info = arr_info_list_to_table([pivot_info])\n')
        lrk__iud += (
            """    out_table = pivot_groupby_and_aggregate(table, {}, dispatch_table, dispatch_info, {}, ftypes.ctypes, func_offsets.ctypes, udf_ncols.ctypes, {}, {}, {}, {}, {}, cpp_cb_update_addr, cpp_cb_combine_addr, cpp_cb_eval_addr, udf_table_dummy)
"""
            .format(n_keys, agg_node.input_has_index, parallel, agg_node.
            is_crosstab, xaq__rrsw, agg_node.return_key, agg_node.same_index))
        lrk__iud += '    delete_info_decref_array(pivot_info)\n'
        lrk__iud += '    delete_info_decref_array(arr_info)\n'
    else:
        lrk__iud += (
            """    out_table = groupby_and_aggregate(table, {}, {}, ftypes.ctypes, func_offsets.ctypes, udf_ncols.ctypes, {}, {}, {}, {}, {}, {}, {}, {}, cpp_cb_update_addr, cpp_cb_combine_addr, cpp_cb_eval_addr, cpp_cb_general_addr, udf_table_dummy)
"""
            .format(n_keys, agg_node.input_has_index, parallel, xaq__rrsw,
            aaj__gsoo, dqvf__pex, heli__vfjl, agg_node.return_key, agg_node
            .same_index, agg_node.dropna))
    zkisb__hido = 0
    if agg_node.return_key:
        for icn__kaww, cbmvy__fbsod in enumerate(tvvt__uek):
            lrk__iud += (
                '    {} = info_to_array(info_from_table(out_table, {}), {})\n'
                .format(cbmvy__fbsod, zkisb__hido, cbmvy__fbsod))
            zkisb__hido += 1
    for ftacr__tac in eawtj__zcxly.values():
        lrk__iud += (
            '    {} = info_to_array(info_from_table(out_table, {}), {})\n'.
            format(ftacr__tac, zkisb__hido, ftacr__tac + '_dummy'))
        zkisb__hido += 1
    if agg_node.same_index:
        lrk__iud += (
            """    out_index_arg = info_to_array(info_from_table(out_table, {}), index_arg)
"""
            .format(zkisb__hido))
        zkisb__hido += 1
    lrk__iud += (
        f"    ev_clean = bodo.utils.tracing.Event('tables_clean_up', {parallel})\n"
        )
    lrk__iud += '    delete_table_decref_arrays(table)\n'
    lrk__iud += '    delete_table_decref_arrays(udf_table_dummy)\n'
    lrk__iud += '    delete_table(out_table)\n'
    lrk__iud += f'    ev_clean.finalize()\n'
    heda__umo = tuple(eawtj__zcxly.values())
    if agg_node.return_key:
        heda__umo += tuple(tvvt__uek)
    lrk__iud += '    return ({},{})\n'.format(', '.join(heda__umo), 
        ' out_index_arg,' if agg_node.same_index else '')
    rja__goc = {}
    exec(lrk__iud, {}, rja__goc)
    jgco__fom = rja__goc['agg_top']
    return jgco__fom


def compile_to_optimized_ir(func, arg_typs, typingctx, targetctx):
    code = func.code if hasattr(func, 'code') else func.__code__
    closure = func.closure if hasattr(func, 'closure') else func.__closure__
    f_ir = get_ir_of_code(func.__globals__, code)
    replace_closures(f_ir, closure, code)
    for block in f_ir.blocks.values():
        for jvxk__yxj in block.body:
            if is_call_assign(jvxk__yxj) and find_callname(f_ir, jvxk__yxj.
                value) == ('len', 'builtins') and jvxk__yxj.value.args[0
                ].name == f_ir.arg_names[0]:
                ifm__pit = get_definition(f_ir, jvxk__yxj.value.func)
                ifm__pit.name = 'dummy_agg_count'
                ifm__pit.value = dummy_agg_count
    jod__nbufa = get_name_var_table(f_ir.blocks)
    gep__hxja = {}
    for name, qbkow__cdn in jod__nbufa.items():
        gep__hxja[name] = mk_unique_var(name)
    replace_var_names(f_ir.blocks, gep__hxja)
    f_ir._definitions = build_definitions(f_ir.blocks)
    assert f_ir.arg_count == 1, 'agg function should have one input'
    ahfr__awxsv = numba.core.compiler.Flags()
    ahfr__awxsv.nrt = True
    dhh__gxc = bodo.transforms.untyped_pass.UntypedPass(f_ir, typingctx,
        arg_typs, {}, {}, ahfr__awxsv)
    dhh__gxc.run()
    f_ir._definitions = build_definitions(f_ir.blocks)
    typemap, ulyc__gof, calltypes, qbkow__cdn = (numba.core.typed_passes.
        type_inference_stage(typingctx, targetctx, f_ir, arg_typs, None))
    lvz__agv = numba.core.cpu.ParallelOptions(True)
    targetctx = numba.core.cpu.CPUContext(typingctx)
    sxh__wnbt = namedtuple('DummyPipeline', ['typingctx', 'targetctx',
        'args', 'func_ir', 'typemap', 'return_type', 'calltypes',
        'type_annotation', 'locals', 'flags', 'pipeline'])
    nriwa__qov = namedtuple('TypeAnnotation', ['typemap', 'calltypes'])
    nok__btvoq = nriwa__qov(typemap, calltypes)
    pm = sxh__wnbt(typingctx, targetctx, None, f_ir, typemap, ulyc__gof,
        calltypes, nok__btvoq, {}, ahfr__awxsv, None)
    iqgxw__eyher = (numba.core.compiler.DefaultPassBuilder.
        define_untyped_pipeline(pm))
    pm = sxh__wnbt(typingctx, targetctx, None, f_ir, typemap, ulyc__gof,
        calltypes, nok__btvoq, {}, ahfr__awxsv, iqgxw__eyher)
    uayz__zsyt = numba.core.typed_passes.InlineOverloads()
    uayz__zsyt.run_pass(pm)
    qyrz__ssmds = bodo.transforms.series_pass.SeriesPass(f_ir, typingctx,
        targetctx, typemap, calltypes, {}, False)
    qyrz__ssmds.run()
    for block in f_ir.blocks.values():
        for jvxk__yxj in block.body:
            if is_assign(jvxk__yxj) and isinstance(jvxk__yxj.value, (ir.Arg,
                ir.Var)) and isinstance(typemap[jvxk__yxj.target.name],
                SeriesType):
                sxqzy__kbcm = typemap.pop(jvxk__yxj.target.name)
                typemap[jvxk__yxj.target.name] = sxqzy__kbcm.data
            if is_call_assign(jvxk__yxj) and find_callname(f_ir, jvxk__yxj.
                value) == ('get_series_data', 'bodo.hiframes.pd_series_ext'):
                f_ir._definitions[jvxk__yxj.target.name].remove(jvxk__yxj.value
                    )
                jvxk__yxj.value = jvxk__yxj.value.args[0]
                f_ir._definitions[jvxk__yxj.target.name].append(jvxk__yxj.value
                    )
            if is_call_assign(jvxk__yxj) and find_callname(f_ir, jvxk__yxj.
                value) == ('isna', 'bodo.libs.array_kernels'):
                f_ir._definitions[jvxk__yxj.target.name].remove(jvxk__yxj.value
                    )
                jvxk__yxj.value = ir.Const(False, jvxk__yxj.loc)
                f_ir._definitions[jvxk__yxj.target.name].append(jvxk__yxj.value
                    )
            if is_call_assign(jvxk__yxj) and find_callname(f_ir, jvxk__yxj.
                value) == ('setna', 'bodo.libs.array_kernels'):
                f_ir._definitions[jvxk__yxj.target.name].remove(jvxk__yxj.value
                    )
                jvxk__yxj.value = ir.Const(False, jvxk__yxj.loc)
                f_ir._definitions[jvxk__yxj.target.name].append(jvxk__yxj.value
                    )
    bodo.transforms.untyped_pass.remove_dead_branches(f_ir)
    efjck__owcjl = numba.parfors.parfor.PreParforPass(f_ir, typemap,
        calltypes, typingctx, targetctx, lvz__agv)
    efjck__owcjl.run()
    f_ir._definitions = build_definitions(f_ir.blocks)
    ilutz__wggar = numba.core.compiler.StateDict()
    ilutz__wggar.func_ir = f_ir
    ilutz__wggar.typemap = typemap
    ilutz__wggar.calltypes = calltypes
    ilutz__wggar.typingctx = typingctx
    ilutz__wggar.targetctx = targetctx
    ilutz__wggar.return_type = ulyc__gof
    numba.core.rewrites.rewrite_registry.apply('after-inference', ilutz__wggar)
    sgtug__jkwe = numba.parfors.parfor.ParforPass(f_ir, typemap, calltypes,
        ulyc__gof, typingctx, targetctx, lvz__agv, ahfr__awxsv, {})
    sgtug__jkwe.run()
    remove_dels(f_ir.blocks)
    numba.parfors.parfor.maximize_fusion(f_ir, f_ir.blocks, typemap, False)
    return f_ir, pm


def replace_closures(f_ir, closure, code):
    if closure:
        closure = f_ir.get_definition(closure)
        if isinstance(closure, tuple):
            uphsv__izo = ctypes.pythonapi.PyCell_Get
            uphsv__izo.restype = ctypes.py_object
            uphsv__izo.argtypes = ctypes.py_object,
            olwgx__mhpf = tuple(uphsv__izo(njc__zgge) for njc__zgge in closure)
        else:
            assert isinstance(closure, ir.Expr) and closure.op == 'build_tuple'
            olwgx__mhpf = closure.items
        assert len(code.co_freevars) == len(olwgx__mhpf)
        numba.core.inline_closurecall._replace_freevars(f_ir.blocks,
            olwgx__mhpf)


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
        ztg__uvmwn = SeriesType(in_col_typ.dtype, in_col_typ, None, string_type
            )
        f_ir, pm = compile_to_optimized_ir(func, (ztg__uvmwn,), self.
            typingctx, self.targetctx)
        f_ir._definitions = build_definitions(f_ir.blocks)
        assert len(f_ir.blocks
            ) == 1 and 0 in f_ir.blocks, 'only simple functions with one block supported for aggregation'
        block = f_ir.blocks[0]
        ctw__tlnf, arr_var = _rm_arg_agg_block(block, pm.typemap)
        wwvj__xhs = -1
        for icn__kaww, jvxk__yxj in enumerate(ctw__tlnf):
            if isinstance(jvxk__yxj, numba.parfors.parfor.Parfor):
                assert wwvj__xhs == -1, 'only one parfor for aggregation function'
                wwvj__xhs = icn__kaww
        parfor = None
        if wwvj__xhs != -1:
            parfor = ctw__tlnf[wwvj__xhs]
            remove_dels(parfor.loop_body)
            remove_dels({(0): parfor.init_block})
        init_nodes = []
        if parfor:
            init_nodes = ctw__tlnf[:wwvj__xhs] + parfor.init_block.body
        eval_nodes = ctw__tlnf[wwvj__xhs + 1:]
        redvars = []
        var_to_redvar = {}
        if parfor:
            redvars, var_to_redvar = get_parfor_reductions(parfor, parfor.
                params, pm.calltypes)
        func.ncols_pre_shuffle = len(redvars)
        func.ncols_post_shuffle = len(redvars) + 1
        func.n_redvars = len(redvars)
        reduce_vars = [0] * len(redvars)
        for jvxk__yxj in init_nodes:
            if is_assign(jvxk__yxj) and jvxk__yxj.target.name in redvars:
                ind = redvars.index(jvxk__yxj.target.name)
                reduce_vars[ind] = jvxk__yxj.target
        var_types = [pm.typemap[khzi__xzatd] for khzi__xzatd in redvars]
        rpf__oaww = gen_combine_func(f_ir, parfor, redvars, var_to_redvar,
            var_types, arr_var, pm, self.typingctx, self.targetctx)
        init_nodes = _mv_read_only_init_vars(init_nodes, parfor, eval_nodes)
        qqcu__ojad = gen_update_func(parfor, redvars, var_to_redvar,
            var_types, arr_var, in_col_typ, pm, self.typingctx, self.targetctx)
        anmz__xaq = gen_eval_func(f_ir, eval_nodes, reduce_vars, var_types,
            pm, self.typingctx, self.targetctx)
        self.all_reduce_vars += reduce_vars
        self.all_vartypes += var_types
        self.all_init_nodes += init_nodes
        self.all_eval_funcs.append(anmz__xaq)
        self.all_update_funcs.append(qqcu__ojad)
        self.all_combine_funcs.append(rpf__oaww)
        self.curr_offset += len(redvars)
        self.redvar_offsets.append(self.curr_offset)

    def gen_all_func(self):
        if len(self.all_update_funcs) == 0:
            return None
        self.all_vartypes = self.all_vartypes * len(self.pivot_values
            ) if self.pivot_values is not None else self.all_vartypes
        self.all_reduce_vars = self.all_reduce_vars * len(self.pivot_values
            ) if self.pivot_values is not None else self.all_reduce_vars
        eheq__cah = gen_init_func(self.all_init_nodes, self.all_reduce_vars,
            self.all_vartypes, self.typingctx, self.targetctx)
        xtam__qqndq = gen_all_update_func(self.all_update_funcs, self.
            all_vartypes, self.in_col_types, self.redvar_offsets, self.
            typingctx, self.targetctx, self.pivot_typ, self.pivot_values,
            self.is_crosstab)
        yflv__hwy = gen_all_combine_func(self.all_combine_funcs, self.
            all_vartypes, self.redvar_offsets, self.typingctx, self.
            targetctx, self.pivot_typ, self.pivot_values)
        qnuy__nxmfz = gen_all_eval_func(self.all_eval_funcs, self.
            all_vartypes, self.redvar_offsets, self.out_col_types, self.
            typingctx, self.targetctx, self.pivot_values)
        return (self.all_vartypes, eheq__cah, xtam__qqndq, yflv__hwy,
            qnuy__nxmfz)


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
    uxws__kus = []
    for t, oogv__hoiuq in zip(in_col_types, agg_func):
        uxws__kus.append((t, oogv__hoiuq))
    ahj__dorj = RegularUDFGenerator(in_col_types, out_col_types, pivot_typ,
        pivot_values, is_crosstab, typingctx, targetctx)
    mgbz__onc = GeneralUDFGenerator()
    for in_col_typ, func in uxws__kus:
        if func.ftype not in ('udf', 'gen_udf'):
            continue
        try:
            ahj__dorj.add_udf(in_col_typ, func)
        except:
            mgbz__onc.add_udf(func)
            func.ftype = 'gen_udf'
    regular_udf_funcs = ahj__dorj.gen_all_func()
    general_udf_funcs = mgbz__onc.gen_all_func()
    if regular_udf_funcs is not None or general_udf_funcs is not None:
        return AggUDFStruct(regular_udf_funcs, general_udf_funcs)
    else:
        return None


def _mv_read_only_init_vars(init_nodes, parfor, eval_nodes):
    if not parfor:
        return init_nodes
    aghlf__jei = compute_use_defs(parfor.loop_body)
    zca__ftu = set()
    for qniw__ays in aghlf__jei.usemap.values():
        zca__ftu |= qniw__ays
    nados__rssda = set()
    for qniw__ays in aghlf__jei.defmap.values():
        nados__rssda |= qniw__ays
    gyb__tkv = ir.Block(ir.Scope(None, parfor.loc), parfor.loc)
    gyb__tkv.body = eval_nodes
    dmifo__bnfor = compute_use_defs({(0): gyb__tkv})
    yxn__vxfdr = dmifo__bnfor.usemap[0]
    tym__trkns = set()
    fkm__azpnl = []
    wps__pkn = []
    for jvxk__yxj in reversed(init_nodes):
        avm__lcbo = {khzi__xzatd.name for khzi__xzatd in jvxk__yxj.list_vars()}
        if is_assign(jvxk__yxj):
            khzi__xzatd = jvxk__yxj.target.name
            avm__lcbo.remove(khzi__xzatd)
            if (khzi__xzatd in zca__ftu and khzi__xzatd not in tym__trkns and
                khzi__xzatd not in yxn__vxfdr and khzi__xzatd not in
                nados__rssda):
                wps__pkn.append(jvxk__yxj)
                zca__ftu |= avm__lcbo
                nados__rssda.add(khzi__xzatd)
                continue
        tym__trkns |= avm__lcbo
        fkm__azpnl.append(jvxk__yxj)
    wps__pkn.reverse()
    fkm__azpnl.reverse()
    wod__jzc = min(parfor.loop_body.keys())
    cyg__unn = parfor.loop_body[wod__jzc]
    cyg__unn.body = wps__pkn + cyg__unn.body
    return fkm__azpnl


def gen_init_func(init_nodes, reduce_vars, var_types, typingctx, targetctx):
    mayqp__epv = (numba.parfors.parfor.max_checker, numba.parfors.parfor.
        min_checker, numba.parfors.parfor.argmax_checker, numba.parfors.
        parfor.argmin_checker)
    ocv__wiqxa = set()
    dre__bikh = []
    for jvxk__yxj in init_nodes:
        if is_assign(jvxk__yxj) and isinstance(jvxk__yxj.value, ir.Global
            ) and isinstance(jvxk__yxj.value.value, pytypes.FunctionType
            ) and jvxk__yxj.value.value in mayqp__epv:
            ocv__wiqxa.add(jvxk__yxj.target.name)
        elif is_call_assign(jvxk__yxj
            ) and jvxk__yxj.value.func.name in ocv__wiqxa:
            pass
        else:
            dre__bikh.append(jvxk__yxj)
    init_nodes = dre__bikh
    utflk__zobfy = types.Tuple(var_types)
    mcny__sue = lambda : None
    f_ir = compile_to_numba_ir(mcny__sue, {})
    block = list(f_ir.blocks.values())[0]
    loc = block.loc
    wtgp__avkij = ir.Var(block.scope, mk_unique_var('init_tup'), loc)
    ppdqt__doe = ir.Assign(ir.Expr.build_tuple(reduce_vars, loc),
        wtgp__avkij, loc)
    block.body = block.body[-2:]
    block.body = init_nodes + [ppdqt__doe] + block.body
    block.body[-2].value.value = wtgp__avkij
    imp__whxr = compiler.compile_ir(typingctx, targetctx, f_ir, (),
        utflk__zobfy, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    oxx__hwgjk = numba.core.target_extension.dispatcher_registry[cpu_target](
        mcny__sue)
    oxx__hwgjk.add_overload(imp__whxr)
    return oxx__hwgjk


def gen_all_update_func(update_funcs, reduce_var_types, in_col_types,
    redvar_offsets, typingctx, targetctx, pivot_typ, pivot_values, is_crosstab
    ):
    auj__ufk = len(update_funcs)
    rpx__avqtw = len(in_col_types)
    if pivot_values is not None:
        assert rpx__avqtw == 1
    lrk__iud = 'def update_all_f(redvar_arrs, data_in, w_ind, i, pivot_arr):\n'
    if pivot_values is not None:
        wyxpk__plzw = redvar_offsets[rpx__avqtw]
        lrk__iud += '  pv = pivot_arr[i]\n'
        for xrrp__xwy, vdf__lgmns in enumerate(pivot_values):
            buhcf__xkb = 'el' if xrrp__xwy != 0 else ''
            lrk__iud += "  {}if pv == '{}':\n".format(buhcf__xkb, vdf__lgmns)
            rskk__nyow = wyxpk__plzw * xrrp__xwy
            wusjd__pewym = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                icn__kaww) for icn__kaww in range(rskk__nyow +
                redvar_offsets[0], rskk__nyow + redvar_offsets[1])])
            gkt__rtoy = 'data_in[0][i]'
            if is_crosstab:
                gkt__rtoy = '0'
            lrk__iud += '    {} = update_vars_0({}, {})\n'.format(wusjd__pewym,
                wusjd__pewym, gkt__rtoy)
    else:
        for xrrp__xwy in range(auj__ufk):
            wusjd__pewym = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                icn__kaww) for icn__kaww in range(redvar_offsets[xrrp__xwy],
                redvar_offsets[xrrp__xwy + 1])])
            if wusjd__pewym:
                lrk__iud += ('  {} = update_vars_{}({},  data_in[{}][i])\n'
                    .format(wusjd__pewym, xrrp__xwy, wusjd__pewym, 0 if 
                    rpx__avqtw == 1 else xrrp__xwy))
    lrk__iud += '  return\n'
    zqmw__xga = {}
    for icn__kaww, oogv__hoiuq in enumerate(update_funcs):
        zqmw__xga['update_vars_{}'.format(icn__kaww)] = oogv__hoiuq
    rja__goc = {}
    exec(lrk__iud, zqmw__xga, rja__goc)
    xvrm__ybpno = rja__goc['update_all_f']
    return numba.njit(no_cpython_wrapper=True)(xvrm__ybpno)


def gen_all_combine_func(combine_funcs, reduce_var_types, redvar_offsets,
    typingctx, targetctx, pivot_typ, pivot_values):
    paxm__fhdu = types.Tuple([types.Array(t, 1, 'C') for t in reduce_var_types]
        )
    arg_typs = paxm__fhdu, paxm__fhdu, types.intp, types.intp, pivot_typ
    lipv__jxfl = len(redvar_offsets) - 1
    wyxpk__plzw = redvar_offsets[lipv__jxfl]
    lrk__iud = (
        'def combine_all_f(redvar_arrs, recv_arrs, w_ind, i, pivot_arr):\n')
    if pivot_values is not None:
        assert lipv__jxfl == 1
        for hvyc__xdyyq in range(len(pivot_values)):
            rskk__nyow = wyxpk__plzw * hvyc__xdyyq
            wusjd__pewym = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                icn__kaww) for icn__kaww in range(rskk__nyow +
                redvar_offsets[0], rskk__nyow + redvar_offsets[1])])
            uwuf__gokyc = ', '.join(['recv_arrs[{}][i]'.format(icn__kaww) for
                icn__kaww in range(rskk__nyow + redvar_offsets[0], 
                rskk__nyow + redvar_offsets[1])])
            lrk__iud += '  {} = combine_vars_0({}, {})\n'.format(wusjd__pewym,
                wusjd__pewym, uwuf__gokyc)
    else:
        for xrrp__xwy in range(lipv__jxfl):
            wusjd__pewym = ', '.join(['redvar_arrs[{}][w_ind]'.format(
                icn__kaww) for icn__kaww in range(redvar_offsets[xrrp__xwy],
                redvar_offsets[xrrp__xwy + 1])])
            uwuf__gokyc = ', '.join(['recv_arrs[{}][i]'.format(icn__kaww) for
                icn__kaww in range(redvar_offsets[xrrp__xwy],
                redvar_offsets[xrrp__xwy + 1])])
            if uwuf__gokyc:
                lrk__iud += '  {} = combine_vars_{}({}, {})\n'.format(
                    wusjd__pewym, xrrp__xwy, wusjd__pewym, uwuf__gokyc)
    lrk__iud += '  return\n'
    zqmw__xga = {}
    for icn__kaww, oogv__hoiuq in enumerate(combine_funcs):
        zqmw__xga['combine_vars_{}'.format(icn__kaww)] = oogv__hoiuq
    rja__goc = {}
    exec(lrk__iud, zqmw__xga, rja__goc)
    wpfjs__zrsn = rja__goc['combine_all_f']
    f_ir = compile_to_numba_ir(wpfjs__zrsn, zqmw__xga)
    yflv__hwy = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        types.none, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    oxx__hwgjk = numba.core.target_extension.dispatcher_registry[cpu_target](
        wpfjs__zrsn)
    oxx__hwgjk.add_overload(yflv__hwy)
    return oxx__hwgjk


def gen_all_eval_func(eval_funcs, reduce_var_types, redvar_offsets,
    out_col_typs, typingctx, targetctx, pivot_values):
    paxm__fhdu = types.Tuple([types.Array(t, 1, 'C') for t in reduce_var_types]
        )
    out_col_typs = types.Tuple(out_col_typs)
    lipv__jxfl = len(redvar_offsets) - 1
    wyxpk__plzw = redvar_offsets[lipv__jxfl]
    lrk__iud = 'def eval_all_f(redvar_arrs, out_arrs, j):\n'
    if pivot_values is not None:
        assert lipv__jxfl == 1
        for xrrp__xwy in range(len(pivot_values)):
            rskk__nyow = wyxpk__plzw * xrrp__xwy
            wusjd__pewym = ', '.join(['redvar_arrs[{}][j]'.format(icn__kaww
                ) for icn__kaww in range(rskk__nyow + redvar_offsets[0], 
                rskk__nyow + redvar_offsets[1])])
            lrk__iud += '  out_arrs[{}][j] = eval_vars_0({})\n'.format(
                xrrp__xwy, wusjd__pewym)
    else:
        for xrrp__xwy in range(lipv__jxfl):
            wusjd__pewym = ', '.join(['redvar_arrs[{}][j]'.format(icn__kaww
                ) for icn__kaww in range(redvar_offsets[xrrp__xwy],
                redvar_offsets[xrrp__xwy + 1])])
            lrk__iud += '  out_arrs[{}][j] = eval_vars_{}({})\n'.format(
                xrrp__xwy, xrrp__xwy, wusjd__pewym)
    lrk__iud += '  return\n'
    zqmw__xga = {}
    for icn__kaww, oogv__hoiuq in enumerate(eval_funcs):
        zqmw__xga['eval_vars_{}'.format(icn__kaww)] = oogv__hoiuq
    rja__goc = {}
    exec(lrk__iud, zqmw__xga, rja__goc)
    gngju__jke = rja__goc['eval_all_f']
    return numba.njit(no_cpython_wrapper=True)(gngju__jke)


def gen_eval_func(f_ir, eval_nodes, reduce_vars, var_types, pm, typingctx,
    targetctx):
    aei__kgz = len(var_types)
    zgk__ankh = [f'in{icn__kaww}' for icn__kaww in range(aei__kgz)]
    utflk__zobfy = types.unliteral(pm.typemap[eval_nodes[-1].value.name])
    zbj__gvcln = utflk__zobfy(0)
    lrk__iud = 'def agg_eval({}):\n return _zero\n'.format(', '.join(zgk__ankh)
        )
    rja__goc = {}
    exec(lrk__iud, {'_zero': zbj__gvcln}, rja__goc)
    yht__czbz = rja__goc['agg_eval']
    arg_typs = tuple(var_types)
    f_ir = compile_to_numba_ir(yht__czbz, {'numba': numba, 'bodo': bodo,
        'np': np, '_zero': zbj__gvcln}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=arg_typs, typemap=pm.typemap, calltypes=pm.
        calltypes)
    block = list(f_ir.blocks.values())[0]
    glpb__ijmqz = []
    for icn__kaww, khzi__xzatd in enumerate(reduce_vars):
        glpb__ijmqz.append(ir.Assign(block.body[icn__kaww].target,
            khzi__xzatd, khzi__xzatd.loc))
        for gjftg__lix in khzi__xzatd.versioned_names:
            glpb__ijmqz.append(ir.Assign(khzi__xzatd, ir.Var(khzi__xzatd.
                scope, gjftg__lix, khzi__xzatd.loc), khzi__xzatd.loc))
    block.body = block.body[:aei__kgz] + glpb__ijmqz + eval_nodes
    anmz__xaq = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        utflk__zobfy, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    oxx__hwgjk = numba.core.target_extension.dispatcher_registry[cpu_target](
        yht__czbz)
    oxx__hwgjk.add_overload(anmz__xaq)
    return oxx__hwgjk


def gen_combine_func(f_ir, parfor, redvars, var_to_redvar, var_types,
    arr_var, pm, typingctx, targetctx):
    if not parfor:
        return numba.njit(lambda : ())
    aei__kgz = len(redvars)
    ozd__ysr = [f'v{icn__kaww}' for icn__kaww in range(aei__kgz)]
    zgk__ankh = [f'in{icn__kaww}' for icn__kaww in range(aei__kgz)]
    lrk__iud = 'def agg_combine({}):\n'.format(', '.join(ozd__ysr + zgk__ankh))
    nrzo__obq = wrap_parfor_blocks(parfor)
    paub__ckvrn = find_topo_order(nrzo__obq)
    paub__ckvrn = paub__ckvrn[1:]
    unwrap_parfor_blocks(parfor)
    ybdz__swzym = {}
    pbuv__kcba = []
    for zhs__kxztb in paub__ckvrn:
        lzc__xuzt = parfor.loop_body[zhs__kxztb]
        for jvxk__yxj in lzc__xuzt.body:
            if is_call_assign(jvxk__yxj) and guard(find_callname, f_ir,
                jvxk__yxj.value) == ('__special_combine', 'bodo.ir.aggregate'):
                args = jvxk__yxj.value.args
                bffy__iro = []
                mzs__xhks = []
                for khzi__xzatd in args[:-1]:
                    ind = redvars.index(khzi__xzatd.name)
                    pbuv__kcba.append(ind)
                    bffy__iro.append('v{}'.format(ind))
                    mzs__xhks.append('in{}'.format(ind))
                eduv__fbjxw = '__special_combine__{}'.format(len(ybdz__swzym))
                lrk__iud += '    ({},) = {}({})\n'.format(', '.join(
                    bffy__iro), eduv__fbjxw, ', '.join(bffy__iro + mzs__xhks))
                ymb__kcgsb = ir.Expr.call(args[-1], [], (), lzc__xuzt.loc)
                wcbjv__tzrn = guard(find_callname, f_ir, ymb__kcgsb)
                assert wcbjv__tzrn == ('_var_combine', 'bodo.ir.aggregate')
                wcbjv__tzrn = bodo.ir.aggregate._var_combine
                ybdz__swzym[eduv__fbjxw] = wcbjv__tzrn
            if is_assign(jvxk__yxj) and jvxk__yxj.target.name in redvars:
                hlogw__vpp = jvxk__yxj.target.name
                ind = redvars.index(hlogw__vpp)
                if ind in pbuv__kcba:
                    continue
                if len(f_ir._definitions[hlogw__vpp]) == 2:
                    var_def = f_ir._definitions[hlogw__vpp][0]
                    lrk__iud += _match_reduce_def(var_def, f_ir, ind)
                    var_def = f_ir._definitions[hlogw__vpp][1]
                    lrk__iud += _match_reduce_def(var_def, f_ir, ind)
    lrk__iud += '    return {}'.format(', '.join(['v{}'.format(icn__kaww) for
        icn__kaww in range(aei__kgz)]))
    rja__goc = {}
    exec(lrk__iud, {}, rja__goc)
    lles__lnb = rja__goc['agg_combine']
    arg_typs = tuple(2 * var_types)
    zqmw__xga = {'numba': numba, 'bodo': bodo, 'np': np}
    zqmw__xga.update(ybdz__swzym)
    f_ir = compile_to_numba_ir(lles__lnb, zqmw__xga, typingctx=typingctx,
        targetctx=targetctx, arg_typs=arg_typs, typemap=pm.typemap,
        calltypes=pm.calltypes)
    block = list(f_ir.blocks.values())[0]
    utflk__zobfy = pm.typemap[block.body[-1].value.name]
    rpf__oaww = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        utflk__zobfy, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    oxx__hwgjk = numba.core.target_extension.dispatcher_registry[cpu_target](
        lles__lnb)
    oxx__hwgjk.add_overload(rpf__oaww)
    return oxx__hwgjk


def _match_reduce_def(var_def, f_ir, ind):
    lrk__iud = ''
    while isinstance(var_def, ir.Var):
        var_def = guard(get_definition, f_ir, var_def)
    if isinstance(var_def, ir.Expr
        ) and var_def.op == 'inplace_binop' and var_def.fn in ('+=',
        operator.iadd):
        lrk__iud = '    v{} += in{}\n'.format(ind, ind)
    if isinstance(var_def, ir.Expr) and var_def.op == 'call':
        zpu__xxu = guard(find_callname, f_ir, var_def)
        if zpu__xxu == ('min', 'builtins'):
            lrk__iud = '    v{} = min(v{}, in{})\n'.format(ind, ind, ind)
        if zpu__xxu == ('max', 'builtins'):
            lrk__iud = '    v{} = max(v{}, in{})\n'.format(ind, ind, ind)
    return lrk__iud


def gen_update_func(parfor, redvars, var_to_redvar, var_types, arr_var,
    in_col_typ, pm, typingctx, targetctx):
    if not parfor:
        return numba.njit(lambda A: ())
    aei__kgz = len(redvars)
    vjhmf__zbx = 1
    qowm__ltyw = []
    for icn__kaww in range(vjhmf__zbx):
        ghsr__tpp = ir.Var(arr_var.scope, f'$input{icn__kaww}', arr_var.loc)
        qowm__ltyw.append(ghsr__tpp)
    bkf__obwnh = parfor.loop_nests[0].index_variable
    wrgal__solm = [0] * aei__kgz
    for lzc__xuzt in parfor.loop_body.values():
        hwv__qwsme = []
        for jvxk__yxj in lzc__xuzt.body:
            if is_var_assign(jvxk__yxj
                ) and jvxk__yxj.value.name == bkf__obwnh.name:
                continue
            if is_getitem(jvxk__yxj
                ) and jvxk__yxj.value.value.name == arr_var.name:
                jvxk__yxj.value = qowm__ltyw[0]
            if is_call_assign(jvxk__yxj) and guard(find_callname, pm.
                func_ir, jvxk__yxj.value) == ('isna', 'bodo.libs.array_kernels'
                ) and jvxk__yxj.value.args[0].name == arr_var.name:
                jvxk__yxj.value = ir.Const(False, jvxk__yxj.target.loc)
            if is_assign(jvxk__yxj) and jvxk__yxj.target.name in redvars:
                ind = redvars.index(jvxk__yxj.target.name)
                wrgal__solm[ind] = jvxk__yxj.target
            hwv__qwsme.append(jvxk__yxj)
        lzc__xuzt.body = hwv__qwsme
    ozd__ysr = ['v{}'.format(icn__kaww) for icn__kaww in range(aei__kgz)]
    zgk__ankh = ['in{}'.format(icn__kaww) for icn__kaww in range(vjhmf__zbx)]
    lrk__iud = 'def agg_update({}):\n'.format(', '.join(ozd__ysr + zgk__ankh))
    lrk__iud += '    __update_redvars()\n'
    lrk__iud += '    return {}'.format(', '.join(['v{}'.format(icn__kaww) for
        icn__kaww in range(aei__kgz)]))
    rja__goc = {}
    exec(lrk__iud, {}, rja__goc)
    vdjtw__ckwsd = rja__goc['agg_update']
    arg_typs = tuple(var_types + [in_col_typ.dtype] * vjhmf__zbx)
    f_ir = compile_to_numba_ir(vdjtw__ckwsd, {'__update_redvars':
        __update_redvars}, typingctx=typingctx, targetctx=targetctx,
        arg_typs=arg_typs, typemap=pm.typemap, calltypes=pm.calltypes)
    f_ir._definitions = build_definitions(f_ir.blocks)
    heskw__egs = f_ir.blocks.popitem()[1].body
    utflk__zobfy = pm.typemap[heskw__egs[-1].value.name]
    nrzo__obq = wrap_parfor_blocks(parfor)
    paub__ckvrn = find_topo_order(nrzo__obq)
    paub__ckvrn = paub__ckvrn[1:]
    unwrap_parfor_blocks(parfor)
    f_ir.blocks = parfor.loop_body
    cyg__unn = f_ir.blocks[paub__ckvrn[0]]
    ttsq__kgxgz = f_ir.blocks[paub__ckvrn[-1]]
    tsktr__uktol = heskw__egs[:aei__kgz + vjhmf__zbx]
    if aei__kgz > 1:
        mtw__ezo = heskw__egs[-3:]
        assert is_assign(mtw__ezo[0]) and isinstance(mtw__ezo[0].value, ir.Expr
            ) and mtw__ezo[0].value.op == 'build_tuple'
    else:
        mtw__ezo = heskw__egs[-2:]
    for icn__kaww in range(aei__kgz):
        edxku__gqed = heskw__egs[icn__kaww].target
        whp__xrdy = ir.Assign(edxku__gqed, wrgal__solm[icn__kaww],
            edxku__gqed.loc)
        tsktr__uktol.append(whp__xrdy)
    for icn__kaww in range(aei__kgz, aei__kgz + vjhmf__zbx):
        edxku__gqed = heskw__egs[icn__kaww].target
        whp__xrdy = ir.Assign(edxku__gqed, qowm__ltyw[icn__kaww - aei__kgz],
            edxku__gqed.loc)
        tsktr__uktol.append(whp__xrdy)
    cyg__unn.body = tsktr__uktol + cyg__unn.body
    oqfaw__zqrb = []
    for icn__kaww in range(aei__kgz):
        edxku__gqed = heskw__egs[icn__kaww].target
        whp__xrdy = ir.Assign(wrgal__solm[icn__kaww], edxku__gqed,
            edxku__gqed.loc)
        oqfaw__zqrb.append(whp__xrdy)
    ttsq__kgxgz.body += oqfaw__zqrb + mtw__ezo
    cvqsy__uhb = compiler.compile_ir(typingctx, targetctx, f_ir, arg_typs,
        utflk__zobfy, compiler.DEFAULT_FLAGS, {})
    from numba.core.target_extension import cpu_target
    oxx__hwgjk = numba.core.target_extension.dispatcher_registry[cpu_target](
        vdjtw__ckwsd)
    oxx__hwgjk.add_overload(cvqsy__uhb)
    return oxx__hwgjk


def _rm_arg_agg_block(block, typemap):
    ctw__tlnf = []
    arr_var = None
    for icn__kaww, jvxk__yxj in enumerate(block.body):
        if is_assign(jvxk__yxj) and isinstance(jvxk__yxj.value, ir.Arg):
            arr_var = jvxk__yxj.target
            iaxq__erefl = typemap[arr_var.name]
            if not isinstance(iaxq__erefl, types.ArrayCompatible):
                ctw__tlnf += block.body[icn__kaww + 1:]
                break
            mhxbj__eirw = block.body[icn__kaww + 1]
            assert is_assign(mhxbj__eirw) and isinstance(mhxbj__eirw.value,
                ir.Expr
                ) and mhxbj__eirw.value.op == 'getattr' and mhxbj__eirw.value.attr == 'shape' and mhxbj__eirw.value.value.name == arr_var.name
            lcckr__betg = mhxbj__eirw.target
            wpe__vyamb = block.body[icn__kaww + 2]
            assert is_assign(wpe__vyamb) and isinstance(wpe__vyamb.value,
                ir.Expr
                ) and wpe__vyamb.value.op == 'static_getitem' and wpe__vyamb.value.value.name == lcckr__betg.name
            ctw__tlnf += block.body[icn__kaww + 3:]
            break
        ctw__tlnf.append(jvxk__yxj)
    return ctw__tlnf, arr_var


def get_parfor_reductions(parfor, parfor_params, calltypes, reduce_varnames
    =None, param_uses=None, var_to_param=None):
    if reduce_varnames is None:
        reduce_varnames = []
    if param_uses is None:
        param_uses = defaultdict(list)
    if var_to_param is None:
        var_to_param = {}
    nrzo__obq = wrap_parfor_blocks(parfor)
    paub__ckvrn = find_topo_order(nrzo__obq)
    paub__ckvrn = paub__ckvrn[1:]
    unwrap_parfor_blocks(parfor)
    for zhs__kxztb in reversed(paub__ckvrn):
        for jvxk__yxj in reversed(parfor.loop_body[zhs__kxztb].body):
            if isinstance(jvxk__yxj, ir.Assign) and (jvxk__yxj.target.name in
                parfor_params or jvxk__yxj.target.name in var_to_param):
                hck__tefgb = jvxk__yxj.target.name
                rhs = jvxk__yxj.value
                bxf__ddfbq = (hck__tefgb if hck__tefgb in parfor_params else
                    var_to_param[hck__tefgb])
                juo__qqw = []
                if isinstance(rhs, ir.Var):
                    juo__qqw = [rhs.name]
                elif isinstance(rhs, ir.Expr):
                    juo__qqw = [khzi__xzatd.name for khzi__xzatd in
                        jvxk__yxj.value.list_vars()]
                param_uses[bxf__ddfbq].extend(juo__qqw)
                for khzi__xzatd in juo__qqw:
                    var_to_param[khzi__xzatd] = bxf__ddfbq
            if isinstance(jvxk__yxj, Parfor):
                get_parfor_reductions(jvxk__yxj, parfor_params, calltypes,
                    reduce_varnames, param_uses, var_to_param)
    for ylv__bkt, juo__qqw in param_uses.items():
        if ylv__bkt in juo__qqw and ylv__bkt not in reduce_varnames:
            reduce_varnames.append(ylv__bkt)
    return reduce_varnames, var_to_param


@numba.extending.register_jitable
def dummy_agg_count(A):
    return len(A)
