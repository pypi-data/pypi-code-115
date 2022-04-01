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
            self.na_position_b = tuple([(True if vqwu__jdx == 'last' else 
                False) for vqwu__jdx in na_position])
        if isinstance(ascending_list, bool):
            ascending_list = (ascending_list,) * len(key_arrs)
        self.ascending_list = ascending_list
        self.loc = loc

    def __repr__(self):
        xegh__jwva = ''
        for nodb__hiipt, wcaj__tptf in self.df_in_vars.items():
            xegh__jwva += "'{}':{}, ".format(nodb__hiipt, wcaj__tptf.name)
        qic__riy = '{}{{{}}}'.format(self.df_in, xegh__jwva)
        tfob__szmy = ''
        for nodb__hiipt, wcaj__tptf in self.df_out_vars.items():
            tfob__szmy += "'{}':{}, ".format(nodb__hiipt, wcaj__tptf.name)
        czh__rwsc = '{}{{{}}}'.format(self.df_out, tfob__szmy)
        return 'sort: [key: {}] {} [key: {}] {}'.format(', '.join(
            wcaj__tptf.name for wcaj__tptf in self.key_arrs), qic__riy,
            ', '.join(wcaj__tptf.name for wcaj__tptf in self.out_key_arrs),
            czh__rwsc)


def sort_array_analysis(sort_node, equiv_set, typemap, array_analysis):
    fqak__niq = []
    fkh__nyrlb = sort_node.key_arrs + list(sort_node.df_in_vars.values())
    for qbxod__koh in fkh__nyrlb:
        fufxn__jmrgs = equiv_set.get_shape(qbxod__koh)
        if fufxn__jmrgs is not None:
            fqak__niq.append(fufxn__jmrgs[0])
    if len(fqak__niq) > 1:
        equiv_set.insert_equiv(*fqak__niq)
    reths__mrtrz = []
    fqak__niq = []
    kmqr__oilx = sort_node.out_key_arrs + list(sort_node.df_out_vars.values())
    for qbxod__koh in kmqr__oilx:
        rmniw__lzfvk = typemap[qbxod__koh.name]
        dgz__qzxv = array_analysis._gen_shape_call(equiv_set, qbxod__koh,
            rmniw__lzfvk.ndim, None, reths__mrtrz)
        equiv_set.insert_equiv(qbxod__koh, dgz__qzxv)
        fqak__niq.append(dgz__qzxv[0])
        equiv_set.define(qbxod__koh, set())
    if len(fqak__niq) > 1:
        equiv_set.insert_equiv(*fqak__niq)
    return [], reths__mrtrz


numba.parfors.array_analysis.array_analysis_extensions[Sort
    ] = sort_array_analysis


def sort_distributed_analysis(sort_node, array_dists):
    fkh__nyrlb = sort_node.key_arrs + list(sort_node.df_in_vars.values())
    uqru__pfdn = sort_node.out_key_arrs + list(sort_node.df_out_vars.values())
    besyy__onka = Distribution.OneD
    for qbxod__koh in fkh__nyrlb:
        besyy__onka = Distribution(min(besyy__onka.value, array_dists[
            qbxod__koh.name].value))
    xawk__kbxsf = Distribution(min(besyy__onka.value, Distribution.OneD_Var
        .value))
    for qbxod__koh in uqru__pfdn:
        if qbxod__koh.name in array_dists:
            xawk__kbxsf = Distribution(min(xawk__kbxsf.value, array_dists[
                qbxod__koh.name].value))
    if xawk__kbxsf != Distribution.OneD_Var:
        besyy__onka = xawk__kbxsf
    for qbxod__koh in fkh__nyrlb:
        array_dists[qbxod__koh.name] = besyy__onka
    for qbxod__koh in uqru__pfdn:
        array_dists[qbxod__koh.name] = xawk__kbxsf
    return


distributed_analysis.distributed_analysis_extensions[Sort
    ] = sort_distributed_analysis


def sort_typeinfer(sort_node, typeinferer):
    for kfe__etiw, bfwhy__egcsc in zip(sort_node.key_arrs, sort_node.
        out_key_arrs):
        typeinferer.constraints.append(typeinfer.Propagate(dst=bfwhy__egcsc
            .name, src=kfe__etiw.name, loc=sort_node.loc))
    for brz__nzx, qbxod__koh in sort_node.df_in_vars.items():
        hpya__kkvlr = sort_node.df_out_vars[brz__nzx]
        typeinferer.constraints.append(typeinfer.Propagate(dst=hpya__kkvlr.
            name, src=qbxod__koh.name, loc=sort_node.loc))
    return


typeinfer.typeinfer_extensions[Sort] = sort_typeinfer


def build_sort_definitions(sort_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    if not sort_node.inplace:
        for qbxod__koh in (sort_node.out_key_arrs + list(sort_node.
            df_out_vars.values())):
            definitions[qbxod__koh.name].append(sort_node)
    return definitions


ir_utils.build_defs_extensions[Sort] = build_sort_definitions


def visit_vars_sort(sort_node, callback, cbdata):
    if debug_prints():
        print('visiting sort vars for:', sort_node)
        print('cbdata: ', sorted(cbdata.items()))
    for jvj__vjwl in range(len(sort_node.key_arrs)):
        sort_node.key_arrs[jvj__vjwl] = visit_vars_inner(sort_node.key_arrs
            [jvj__vjwl], callback, cbdata)
        sort_node.out_key_arrs[jvj__vjwl] = visit_vars_inner(sort_node.
            out_key_arrs[jvj__vjwl], callback, cbdata)
    for brz__nzx in list(sort_node.df_in_vars.keys()):
        sort_node.df_in_vars[brz__nzx] = visit_vars_inner(sort_node.
            df_in_vars[brz__nzx], callback, cbdata)
    for brz__nzx in list(sort_node.df_out_vars.keys()):
        sort_node.df_out_vars[brz__nzx] = visit_vars_inner(sort_node.
            df_out_vars[brz__nzx], callback, cbdata)


ir_utils.visit_vars_extensions[Sort] = visit_vars_sort


def remove_dead_sort(sort_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    bbhd__rwu = []
    for brz__nzx, qbxod__koh in sort_node.df_out_vars.items():
        if qbxod__koh.name not in lives:
            bbhd__rwu.append(brz__nzx)
    for mjpv__wcx in bbhd__rwu:
        sort_node.df_in_vars.pop(mjpv__wcx)
        sort_node.df_out_vars.pop(mjpv__wcx)
    if len(sort_node.df_out_vars) == 0 and all(wcaj__tptf.name not in lives for
        wcaj__tptf in sort_node.out_key_arrs):
        return None
    return sort_node


ir_utils.remove_dead_extensions[Sort] = remove_dead_sort


def sort_usedefs(sort_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({wcaj__tptf.name for wcaj__tptf in sort_node.key_arrs})
    use_set.update({wcaj__tptf.name for wcaj__tptf in sort_node.df_in_vars.
        values()})
    if not sort_node.inplace:
        def_set.update({wcaj__tptf.name for wcaj__tptf in sort_node.
            out_key_arrs})
        def_set.update({wcaj__tptf.name for wcaj__tptf in sort_node.
            df_out_vars.values()})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Sort] = sort_usedefs


def get_copies_sort(sort_node, typemap):
    xgyxo__uuwv = set()
    if not sort_node.inplace:
        xgyxo__uuwv = set(wcaj__tptf.name for wcaj__tptf in sort_node.
            df_out_vars.values())
        xgyxo__uuwv.update({wcaj__tptf.name for wcaj__tptf in sort_node.
            out_key_arrs})
    return set(), xgyxo__uuwv


ir_utils.copy_propagate_extensions[Sort] = get_copies_sort


def apply_copies_sort(sort_node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    for jvj__vjwl in range(len(sort_node.key_arrs)):
        sort_node.key_arrs[jvj__vjwl] = replace_vars_inner(sort_node.
            key_arrs[jvj__vjwl], var_dict)
        sort_node.out_key_arrs[jvj__vjwl] = replace_vars_inner(sort_node.
            out_key_arrs[jvj__vjwl], var_dict)
    for brz__nzx in list(sort_node.df_in_vars.keys()):
        sort_node.df_in_vars[brz__nzx] = replace_vars_inner(sort_node.
            df_in_vars[brz__nzx], var_dict)
    for brz__nzx in list(sort_node.df_out_vars.keys()):
        sort_node.df_out_vars[brz__nzx] = replace_vars_inner(sort_node.
            df_out_vars[brz__nzx], var_dict)
    return


ir_utils.apply_copy_propagate_extensions[Sort] = apply_copies_sort


def sort_distributed_run(sort_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    nhlzy__vqvt = False
    mcs__jjmnd = list(sort_node.df_in_vars.values())
    kmqr__oilx = list(sort_node.df_out_vars.values())
    if array_dists is not None:
        nhlzy__vqvt = True
        for wcaj__tptf in (sort_node.key_arrs + sort_node.out_key_arrs +
            mcs__jjmnd + kmqr__oilx):
            if array_dists[wcaj__tptf.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                wcaj__tptf.name] != distributed_pass.Distribution.OneD_Var:
                nhlzy__vqvt = False
    loc = sort_node.loc
    ele__wmiwh = sort_node.key_arrs[0].scope
    nodes = []
    key_arrs = sort_node.key_arrs
    if not sort_node.inplace:
        ajhh__fep = []
        for wcaj__tptf in key_arrs:
            xhv__avlb = _copy_array_nodes(wcaj__tptf, nodes, typingctx,
                targetctx, typemap, calltypes)
            ajhh__fep.append(xhv__avlb)
        key_arrs = ajhh__fep
        ekj__lon = []
        for wcaj__tptf in mcs__jjmnd:
            eut__qjynl = _copy_array_nodes(wcaj__tptf, nodes, typingctx,
                targetctx, typemap, calltypes)
            ekj__lon.append(eut__qjynl)
        mcs__jjmnd = ekj__lon
    key_name_args = [f'key{jvj__vjwl}' for jvj__vjwl in range(len(key_arrs))]
    exr__bnupi = ', '.join(key_name_args)
    col_name_args = [f'c{jvj__vjwl}' for jvj__vjwl in range(len(mcs__jjmnd))]
    tgnap__bhblx = ', '.join(col_name_args)
    msuw__qniy = 'def f({}, {}):\n'.format(exr__bnupi, tgnap__bhblx)
    msuw__qniy += get_sort_cpp_section(key_name_args, col_name_args,
        sort_node.ascending_list, sort_node.na_position_b, nhlzy__vqvt)
    msuw__qniy += '  return key_arrs, data\n'
    ipp__jeyz = {}
    exec(msuw__qniy, {}, ipp__jeyz)
    hvz__wbuw = ipp__jeyz['f']
    bhn__lqsc = types.Tuple([typemap[wcaj__tptf.name] for wcaj__tptf in
        key_arrs])
    forot__ghvo = types.Tuple([typemap[wcaj__tptf.name] for wcaj__tptf in
        mcs__jjmnd])
    ztme__djaud = compile_to_numba_ir(hvz__wbuw, {'bodo': bodo, 'np': np,
        'to_list_if_immutable_arr': to_list_if_immutable_arr,
        'cp_str_list_to_array': cp_str_list_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'sort_values_table':
        sort_values_table, 'arr_info_list_to_table': arr_info_list_to_table,
        'array_to_info': array_to_info}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=tuple(list(bhn__lqsc.types) + list(forot__ghvo.
        types)), typemap=typemap, calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(ztme__djaud, key_arrs + mcs__jjmnd)
    nodes += ztme__djaud.body[:-2]
    piqkl__vgj = nodes[-1].target
    erlf__snu = ir.Var(ele__wmiwh, mk_unique_var('key_data'), loc)
    typemap[erlf__snu.name] = bhn__lqsc
    gen_getitem(erlf__snu, piqkl__vgj, 0, calltypes, nodes)
    sqv__jja = ir.Var(ele__wmiwh, mk_unique_var('sort_data'), loc)
    typemap[sqv__jja.name] = forot__ghvo
    gen_getitem(sqv__jja, piqkl__vgj, 1, calltypes, nodes)
    for jvj__vjwl, var in enumerate(sort_node.out_key_arrs):
        gen_getitem(var, erlf__snu, jvj__vjwl, calltypes, nodes)
    for jvj__vjwl, var in enumerate(kmqr__oilx):
        gen_getitem(var, sqv__jja, jvj__vjwl, calltypes, nodes)
    return nodes


distributed_pass.distributed_run_extensions[Sort] = sort_distributed_run


def _copy_array_nodes(var, nodes, typingctx, targetctx, typemap, calltypes):

    def _impl(arr):
        return arr.copy()
    ztme__djaud = compile_to_numba_ir(_impl, {}, typingctx=typingctx,
        targetctx=targetctx, arg_typs=(typemap[var.name],), typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(ztme__djaud, [var])
    nodes += ztme__djaud.body[:-2]
    return nodes[-1].target


def get_sort_cpp_section(key_name_args, col_name_args, ascending_list,
    na_position_b, parallel_b):
    msuw__qniy = ''
    sghsh__hlycp = len(key_name_args)
    tcp__xlch = ['array_to_info({})'.format(cfoav__syv) for cfoav__syv in
        key_name_args] + ['array_to_info({})'.format(cfoav__syv) for
        cfoav__syv in col_name_args]
    msuw__qniy += '  info_list_total = [{}]\n'.format(','.join(tcp__xlch))
    msuw__qniy += '  table_total = arr_info_list_to_table(info_list_total)\n'
    msuw__qniy += '  vect_ascending = np.array([{}])\n'.format(','.join('1' if
        unin__hxhoa else '0' for unin__hxhoa in ascending_list))
    msuw__qniy += '  na_position = np.array([{}])\n'.format(','.join('1' if
        unin__hxhoa else '0' for unin__hxhoa in na_position_b))
    msuw__qniy += (
        """  out_table = sort_values_table(table_total, {}, vect_ascending.ctypes, na_position.ctypes, {})
"""
        .format(sghsh__hlycp, parallel_b))
    jmjs__lqmky = 0
    lzvw__hcwau = []
    for cfoav__syv in key_name_args:
        lzvw__hcwau.append('info_to_array(info_from_table(out_table, {}), {})'
            .format(jmjs__lqmky, cfoav__syv))
        jmjs__lqmky += 1
    msuw__qniy += '  key_arrs = ({},)\n'.format(','.join(lzvw__hcwau))
    qjui__peg = []
    for cfoav__syv in col_name_args:
        qjui__peg.append('info_to_array(info_from_table(out_table, {}), {})'
            .format(jmjs__lqmky, cfoav__syv))
        jmjs__lqmky += 1
    if len(qjui__peg) > 0:
        msuw__qniy += '  data = ({},)\n'.format(','.join(qjui__peg))
    else:
        msuw__qniy += '  data = ()\n'
    msuw__qniy += '  delete_table(out_table)\n'
    msuw__qniy += '  delete_table(table_total)\n'
    return msuw__qniy
