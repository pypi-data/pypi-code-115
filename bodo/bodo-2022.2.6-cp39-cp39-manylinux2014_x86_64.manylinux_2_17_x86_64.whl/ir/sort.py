"""IR node for the data sorting"""
from collections import defaultdict
import numba
import numpy as np
from numba.core import ir, ir_utils, typeinfer, types
from numba.core.ir_utils import compile_to_numba_ir, mk_unique_var, replace_arg_nodes, replace_vars_inner, visit_vars_inner
import bodo
import bodo.libs.timsort
from bodo.libs.array import arr_info_list_to_table, array_to_info, delete_table, delete_table_decref_arrays, info_from_table, info_to_array, sort_values_table
from bodo.libs.str_arr_ext import cp_str_list_to_array, to_list_if_immutable_arr
from bodo.transforms import distributed_analysis, distributed_pass
from bodo.transforms.distributed_analysis import Distribution
from bodo.utils.utils import debug_prints, gen_getitem
MIN_SAMPLES = 1000000
samplePointsPerPartitionHint = 20
MPI_ROOT = 0


class Sort(ir.Stmt):

    def __init__(self, df_in, df_out, key_arrs, out_key_arrs, df_in_vars,
        df_out_vars, inplace, loc, ascending_list=True, na_position='last'):
        self.df_in = df_in
        self.df_out = df_out
        self.key_arrs = key_arrs
        self.out_key_arrs = out_key_arrs
        self.df_in_vars = df_in_vars
        self.df_out_vars = df_out_vars
        self.inplace = inplace
        if isinstance(na_position, str):
            if na_position == 'last':
                self.na_position_b = (True,) * len(key_arrs)
            else:
                self.na_position_b = (False,) * len(key_arrs)
        else:
            self.na_position_b = tuple([(True if cmpy__pht == 'last' else 
                False) for cmpy__pht in na_position])
        if isinstance(ascending_list, bool):
            ascending_list = (ascending_list,) * len(key_arrs)
        self.ascending_list = ascending_list
        self.loc = loc

    def __repr__(self):
        jdoca__zqf = ''
        for qqkem__sdynw, wujzv__kvjka in self.df_in_vars.items():
            jdoca__zqf += "'{}':{}, ".format(qqkem__sdynw, wujzv__kvjka.name)
        bwqm__aajdq = '{}{{{}}}'.format(self.df_in, jdoca__zqf)
        sia__kzw = ''
        for qqkem__sdynw, wujzv__kvjka in self.df_out_vars.items():
            sia__kzw += "'{}':{}, ".format(qqkem__sdynw, wujzv__kvjka.name)
        ymi__blv = '{}{{{}}}'.format(self.df_out, sia__kzw)
        return 'sort: [key: {}] {} [key: {}] {}'.format(', '.join(
            wujzv__kvjka.name for wujzv__kvjka in self.key_arrs),
            bwqm__aajdq, ', '.join(wujzv__kvjka.name for wujzv__kvjka in
            self.out_key_arrs), ymi__blv)


def sort_array_analysis(sort_node, equiv_set, typemap, array_analysis):
    ijxlh__whj = []
    biuz__tqamn = sort_node.key_arrs + list(sort_node.df_in_vars.values())
    for sgqo__rfaik in biuz__tqamn:
        ypdso__jhm = equiv_set.get_shape(sgqo__rfaik)
        if ypdso__jhm is not None:
            ijxlh__whj.append(ypdso__jhm[0])
    if len(ijxlh__whj) > 1:
        equiv_set.insert_equiv(*ijxlh__whj)
    dnrcw__kvnsr = []
    ijxlh__whj = []
    wouw__pld = sort_node.out_key_arrs + list(sort_node.df_out_vars.values())
    for sgqo__rfaik in wouw__pld:
        hfsbv__jecy = typemap[sgqo__rfaik.name]
        nfeg__xnmvv = array_analysis._gen_shape_call(equiv_set, sgqo__rfaik,
            hfsbv__jecy.ndim, None, dnrcw__kvnsr)
        equiv_set.insert_equiv(sgqo__rfaik, nfeg__xnmvv)
        ijxlh__whj.append(nfeg__xnmvv[0])
        equiv_set.define(sgqo__rfaik, set())
    if len(ijxlh__whj) > 1:
        equiv_set.insert_equiv(*ijxlh__whj)
    return [], dnrcw__kvnsr


numba.parfors.array_analysis.array_analysis_extensions[Sort
    ] = sort_array_analysis


def sort_distributed_analysis(sort_node, array_dists):
    biuz__tqamn = sort_node.key_arrs + list(sort_node.df_in_vars.values())
    bxoql__acrq = sort_node.out_key_arrs + list(sort_node.df_out_vars.values())
    trg__qdlq = Distribution.OneD
    for sgqo__rfaik in biuz__tqamn:
        trg__qdlq = Distribution(min(trg__qdlq.value, array_dists[
            sgqo__rfaik.name].value))
    biaxu__waq = Distribution(min(trg__qdlq.value, Distribution.OneD_Var.value)
        )
    for sgqo__rfaik in bxoql__acrq:
        if sgqo__rfaik.name in array_dists:
            biaxu__waq = Distribution(min(biaxu__waq.value, array_dists[
                sgqo__rfaik.name].value))
    if biaxu__waq != Distribution.OneD_Var:
        trg__qdlq = biaxu__waq
    for sgqo__rfaik in biuz__tqamn:
        array_dists[sgqo__rfaik.name] = trg__qdlq
    for sgqo__rfaik in bxoql__acrq:
        array_dists[sgqo__rfaik.name] = biaxu__waq
    return


distributed_analysis.distributed_analysis_extensions[Sort
    ] = sort_distributed_analysis


def sort_typeinfer(sort_node, typeinferer):
    for ejrfa__gmqi, tscv__pvxp in zip(sort_node.key_arrs, sort_node.
        out_key_arrs):
        typeinferer.constraints.append(typeinfer.Propagate(dst=tscv__pvxp.
            name, src=ejrfa__gmqi.name, loc=sort_node.loc))
    for nksup__xpqg, sgqo__rfaik in sort_node.df_in_vars.items():
        llo__bgw = sort_node.df_out_vars[nksup__xpqg]
        typeinferer.constraints.append(typeinfer.Propagate(dst=llo__bgw.
            name, src=sgqo__rfaik.name, loc=sort_node.loc))
    return


typeinfer.typeinfer_extensions[Sort] = sort_typeinfer


def build_sort_definitions(sort_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    if not sort_node.inplace:
        for sgqo__rfaik in (sort_node.out_key_arrs + list(sort_node.
            df_out_vars.values())):
            definitions[sgqo__rfaik.name].append(sort_node)
    return definitions


ir_utils.build_defs_extensions[Sort] = build_sort_definitions


def visit_vars_sort(sort_node, callback, cbdata):
    if debug_prints():
        print('visiting sort vars for:', sort_node)
        print('cbdata: ', sorted(cbdata.items()))
    for vhsw__wiwg in range(len(sort_node.key_arrs)):
        sort_node.key_arrs[vhsw__wiwg] = visit_vars_inner(sort_node.
            key_arrs[vhsw__wiwg], callback, cbdata)
        sort_node.out_key_arrs[vhsw__wiwg] = visit_vars_inner(sort_node.
            out_key_arrs[vhsw__wiwg], callback, cbdata)
    for nksup__xpqg in list(sort_node.df_in_vars.keys()):
        sort_node.df_in_vars[nksup__xpqg] = visit_vars_inner(sort_node.
            df_in_vars[nksup__xpqg], callback, cbdata)
    for nksup__xpqg in list(sort_node.df_out_vars.keys()):
        sort_node.df_out_vars[nksup__xpqg] = visit_vars_inner(sort_node.
            df_out_vars[nksup__xpqg], callback, cbdata)


ir_utils.visit_vars_extensions[Sort] = visit_vars_sort


def remove_dead_sort(sort_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    rolgk__tisrb = []
    for nksup__xpqg, sgqo__rfaik in sort_node.df_out_vars.items():
        if sgqo__rfaik.name not in lives:
            rolgk__tisrb.append(nksup__xpqg)
    for fbg__sbuts in rolgk__tisrb:
        sort_node.df_in_vars.pop(fbg__sbuts)
        sort_node.df_out_vars.pop(fbg__sbuts)
    if len(sort_node.df_out_vars) == 0 and all(wujzv__kvjka.name not in
        lives for wujzv__kvjka in sort_node.out_key_arrs):
        return None
    return sort_node


ir_utils.remove_dead_extensions[Sort] = remove_dead_sort


def sort_usedefs(sort_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({wujzv__kvjka.name for wujzv__kvjka in sort_node.key_arrs})
    use_set.update({wujzv__kvjka.name for wujzv__kvjka in sort_node.
        df_in_vars.values()})
    if not sort_node.inplace:
        def_set.update({wujzv__kvjka.name for wujzv__kvjka in sort_node.
            out_key_arrs})
        def_set.update({wujzv__kvjka.name for wujzv__kvjka in sort_node.
            df_out_vars.values()})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Sort] = sort_usedefs


def get_copies_sort(sort_node, typemap):
    yisby__eglfq = set()
    if not sort_node.inplace:
        yisby__eglfq = set(wujzv__kvjka.name for wujzv__kvjka in sort_node.
            df_out_vars.values())
        yisby__eglfq.update({wujzv__kvjka.name for wujzv__kvjka in
            sort_node.out_key_arrs})
    return set(), yisby__eglfq


ir_utils.copy_propagate_extensions[Sort] = get_copies_sort


def apply_copies_sort(sort_node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    for vhsw__wiwg in range(len(sort_node.key_arrs)):
        sort_node.key_arrs[vhsw__wiwg] = replace_vars_inner(sort_node.
            key_arrs[vhsw__wiwg], var_dict)
        sort_node.out_key_arrs[vhsw__wiwg] = replace_vars_inner(sort_node.
            out_key_arrs[vhsw__wiwg], var_dict)
    for nksup__xpqg in list(sort_node.df_in_vars.keys()):
        sort_node.df_in_vars[nksup__xpqg] = replace_vars_inner(sort_node.
            df_in_vars[nksup__xpqg], var_dict)
    for nksup__xpqg in list(sort_node.df_out_vars.keys()):
        sort_node.df_out_vars[nksup__xpqg] = replace_vars_inner(sort_node.
            df_out_vars[nksup__xpqg], var_dict)
    return


ir_utils.apply_copy_propagate_extensions[Sort] = apply_copies_sort


def sort_distributed_run(sort_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    abx__drap = False
    joqy__cicd = list(sort_node.df_in_vars.values())
    wouw__pld = list(sort_node.df_out_vars.values())
    if array_dists is not None:
        abx__drap = True
        for wujzv__kvjka in (sort_node.key_arrs + sort_node.out_key_arrs +
            joqy__cicd + wouw__pld):
            if array_dists[wujzv__kvjka.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                wujzv__kvjka.name] != distributed_pass.Distribution.OneD_Var:
                abx__drap = False
    loc = sort_node.loc
    oucs__ybsok = sort_node.key_arrs[0].scope
    nodes = []
    key_arrs = sort_node.key_arrs
    if not sort_node.inplace:
        piwx__ybs = []
        for wujzv__kvjka in key_arrs:
            tnkk__deqm = _copy_array_nodes(wujzv__kvjka, nodes, typingctx,
                targetctx, typemap, calltypes)
            piwx__ybs.append(tnkk__deqm)
        key_arrs = piwx__ybs
        dli__hjbe = []
        for wujzv__kvjka in joqy__cicd:
            oeire__fssih = _copy_array_nodes(wujzv__kvjka, nodes, typingctx,
                targetctx, typemap, calltypes)
            dli__hjbe.append(oeire__fssih)
        joqy__cicd = dli__hjbe
    key_name_args = [f'key{vhsw__wiwg}' for vhsw__wiwg in range(len(key_arrs))]
    hjrko__zesaj = ', '.join(key_name_args)
    col_name_args = [f'c{vhsw__wiwg}' for vhsw__wiwg in range(len(joqy__cicd))]
    rybkh__cyb = ', '.join(col_name_args)
    mhd__wusj = 'def f({}, {}):\n'.format(hjrko__zesaj, rybkh__cyb)
    mhd__wusj += get_sort_cpp_section(key_name_args, col_name_args,
        sort_node.ascending_list, sort_node.na_position_b, abx__drap)
    mhd__wusj += '  return key_arrs, data\n'
    lbtk__ooacb = {}
    exec(mhd__wusj, {}, lbtk__ooacb)
    swlnq__jyddn = lbtk__ooacb['f']
    uxam__loxhc = types.Tuple([typemap[wujzv__kvjka.name] for wujzv__kvjka in
        key_arrs])
    xxyey__icypa = types.Tuple([typemap[wujzv__kvjka.name] for wujzv__kvjka in
        joqy__cicd])
    deqsw__ywb = compile_to_numba_ir(swlnq__jyddn, {'bodo': bodo, 'np': np,
        'to_list_if_immutable_arr': to_list_if_immutable_arr,
        'cp_str_list_to_array': cp_str_list_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'sort_values_table':
        sort_values_table, 'arr_info_list_to_table': arr_info_list_to_table,
        'array_to_info': array_to_info}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=tuple(list(uxam__loxhc.types) + list(
        xxyey__icypa.types)), typemap=typemap, calltypes=calltypes
        ).blocks.popitem()[1]
    replace_arg_nodes(deqsw__ywb, key_arrs + joqy__cicd)
    nodes += deqsw__ywb.body[:-2]
    qijg__zzktu = nodes[-1].target
    uzhv__kpp = ir.Var(oucs__ybsok, mk_unique_var('key_data'), loc)
    typemap[uzhv__kpp.name] = uxam__loxhc
    gen_getitem(uzhv__kpp, qijg__zzktu, 0, calltypes, nodes)
    uxi__pudk = ir.Var(oucs__ybsok, mk_unique_var('sort_data'), loc)
    typemap[uxi__pudk.name] = xxyey__icypa
    gen_getitem(uxi__pudk, qijg__zzktu, 1, calltypes, nodes)
    for vhsw__wiwg, var in enumerate(sort_node.out_key_arrs):
        gen_getitem(var, uzhv__kpp, vhsw__wiwg, calltypes, nodes)
    for vhsw__wiwg, var in enumerate(wouw__pld):
        gen_getitem(var, uxi__pudk, vhsw__wiwg, calltypes, nodes)
    return nodes


distributed_pass.distributed_run_extensions[Sort] = sort_distributed_run


def _copy_array_nodes(var, nodes, typingctx, targetctx, typemap, calltypes):

    def _impl(arr):
        return arr.copy()
    deqsw__ywb = compile_to_numba_ir(_impl, {}, typingctx=typingctx,
        targetctx=targetctx, arg_typs=(typemap[var.name],), typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(deqsw__ywb, [var])
    nodes += deqsw__ywb.body[:-2]
    return nodes[-1].target


def get_sort_cpp_section(key_name_args, col_name_args, ascending_list,
    na_position_b, parallel_b):
    mhd__wusj = ''
    ixhzi__quh = len(key_name_args)
    qyocz__pyf = ['array_to_info({})'.format(eorpy__omuus) for eorpy__omuus in
        key_name_args] + ['array_to_info({})'.format(eorpy__omuus) for
        eorpy__omuus in col_name_args]
    mhd__wusj += '  info_list_total = [{}]\n'.format(','.join(qyocz__pyf))
    mhd__wusj += '  table_total = arr_info_list_to_table(info_list_total)\n'
    mhd__wusj += '  vect_ascending = np.array([{}])\n'.format(','.join('1' if
        qpo__rbss else '0' for qpo__rbss in ascending_list))
    mhd__wusj += '  na_position = np.array([{}])\n'.format(','.join('1' if
        qpo__rbss else '0' for qpo__rbss in na_position_b))
    mhd__wusj += (
        """  out_table = sort_values_table(table_total, {}, vect_ascending.ctypes, na_position.ctypes, {})
"""
        .format(ixhzi__quh, parallel_b))
    vctn__wbjyn = 0
    vsncn__kmni = []
    for eorpy__omuus in key_name_args:
        vsncn__kmni.append('info_to_array(info_from_table(out_table, {}), {})'
            .format(vctn__wbjyn, eorpy__omuus))
        vctn__wbjyn += 1
    mhd__wusj += '  key_arrs = ({},)\n'.format(','.join(vsncn__kmni))
    uhg__sihak = []
    for eorpy__omuus in col_name_args:
        uhg__sihak.append('info_to_array(info_from_table(out_table, {}), {})'
            .format(vctn__wbjyn, eorpy__omuus))
        vctn__wbjyn += 1
    if len(uhg__sihak) > 0:
        mhd__wusj += '  data = ({},)\n'.format(','.join(uhg__sihak))
    else:
        mhd__wusj += '  data = ()\n'
    mhd__wusj += '  delete_table(out_table)\n'
    mhd__wusj += '  delete_table(table_total)\n'
    return mhd__wusj
