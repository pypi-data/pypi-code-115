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
            self.na_position_b = tuple([(True if maupe__lutf == 'last' else
                False) for maupe__lutf in na_position])
        if isinstance(ascending_list, bool):
            ascending_list = (ascending_list,) * len(key_arrs)
        self.ascending_list = ascending_list
        self.loc = loc

    def __repr__(self):
        xmz__ngw = ''
        for vntdk__pwtpc, kyidg__yjtlc in self.df_in_vars.items():
            xmz__ngw += "'{}':{}, ".format(vntdk__pwtpc, kyidg__yjtlc.name)
        uxf__dbw = '{}{{{}}}'.format(self.df_in, xmz__ngw)
        gbbt__zdgku = ''
        for vntdk__pwtpc, kyidg__yjtlc in self.df_out_vars.items():
            gbbt__zdgku += "'{}':{}, ".format(vntdk__pwtpc, kyidg__yjtlc.name)
        xks__ghigr = '{}{{{}}}'.format(self.df_out, gbbt__zdgku)
        return 'sort: [key: {}] {} [key: {}] {}'.format(', '.join(
            kyidg__yjtlc.name for kyidg__yjtlc in self.key_arrs), uxf__dbw,
            ', '.join(kyidg__yjtlc.name for kyidg__yjtlc in self.
            out_key_arrs), xks__ghigr)


def sort_array_analysis(sort_node, equiv_set, typemap, array_analysis):
    tbuo__phedm = []
    qstd__uczg = sort_node.key_arrs + list(sort_node.df_in_vars.values())
    for mavf__hzah in qstd__uczg:
        wbk__znny = equiv_set.get_shape(mavf__hzah)
        if wbk__znny is not None:
            tbuo__phedm.append(wbk__znny[0])
    if len(tbuo__phedm) > 1:
        equiv_set.insert_equiv(*tbuo__phedm)
    tdwxz__tknd = []
    tbuo__phedm = []
    aakpu__decs = sort_node.out_key_arrs + list(sort_node.df_out_vars.values())
    for mavf__hzah in aakpu__decs:
        xur__urrz = typemap[mavf__hzah.name]
        aosf__xoymd = array_analysis._gen_shape_call(equiv_set, mavf__hzah,
            xur__urrz.ndim, None, tdwxz__tknd)
        equiv_set.insert_equiv(mavf__hzah, aosf__xoymd)
        tbuo__phedm.append(aosf__xoymd[0])
        equiv_set.define(mavf__hzah, set())
    if len(tbuo__phedm) > 1:
        equiv_set.insert_equiv(*tbuo__phedm)
    return [], tdwxz__tknd


numba.parfors.array_analysis.array_analysis_extensions[Sort
    ] = sort_array_analysis


def sort_distributed_analysis(sort_node, array_dists):
    qstd__uczg = sort_node.key_arrs + list(sort_node.df_in_vars.values())
    xwn__tined = sort_node.out_key_arrs + list(sort_node.df_out_vars.values())
    tapw__mzn = Distribution.OneD
    for mavf__hzah in qstd__uczg:
        tapw__mzn = Distribution(min(tapw__mzn.value, array_dists[
            mavf__hzah.name].value))
    ithh__iywry = Distribution(min(tapw__mzn.value, Distribution.OneD_Var.
        value))
    for mavf__hzah in xwn__tined:
        if mavf__hzah.name in array_dists:
            ithh__iywry = Distribution(min(ithh__iywry.value, array_dists[
                mavf__hzah.name].value))
    if ithh__iywry != Distribution.OneD_Var:
        tapw__mzn = ithh__iywry
    for mavf__hzah in qstd__uczg:
        array_dists[mavf__hzah.name] = tapw__mzn
    for mavf__hzah in xwn__tined:
        array_dists[mavf__hzah.name] = ithh__iywry
    return


distributed_analysis.distributed_analysis_extensions[Sort
    ] = sort_distributed_analysis


def sort_typeinfer(sort_node, typeinferer):
    for uboxf__qzz, ukpns__oxyp in zip(sort_node.key_arrs, sort_node.
        out_key_arrs):
        typeinferer.constraints.append(typeinfer.Propagate(dst=ukpns__oxyp.
            name, src=uboxf__qzz.name, loc=sort_node.loc))
    for ndcu__kzjkc, mavf__hzah in sort_node.df_in_vars.items():
        yidtw__rxgt = sort_node.df_out_vars[ndcu__kzjkc]
        typeinferer.constraints.append(typeinfer.Propagate(dst=yidtw__rxgt.
            name, src=mavf__hzah.name, loc=sort_node.loc))
    return


typeinfer.typeinfer_extensions[Sort] = sort_typeinfer


def build_sort_definitions(sort_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    if not sort_node.inplace:
        for mavf__hzah in (sort_node.out_key_arrs + list(sort_node.
            df_out_vars.values())):
            definitions[mavf__hzah.name].append(sort_node)
    return definitions


ir_utils.build_defs_extensions[Sort] = build_sort_definitions


def visit_vars_sort(sort_node, callback, cbdata):
    if debug_prints():
        print('visiting sort vars for:', sort_node)
        print('cbdata: ', sorted(cbdata.items()))
    for nhkv__bzax in range(len(sort_node.key_arrs)):
        sort_node.key_arrs[nhkv__bzax] = visit_vars_inner(sort_node.
            key_arrs[nhkv__bzax], callback, cbdata)
        sort_node.out_key_arrs[nhkv__bzax] = visit_vars_inner(sort_node.
            out_key_arrs[nhkv__bzax], callback, cbdata)
    for ndcu__kzjkc in list(sort_node.df_in_vars.keys()):
        sort_node.df_in_vars[ndcu__kzjkc] = visit_vars_inner(sort_node.
            df_in_vars[ndcu__kzjkc], callback, cbdata)
    for ndcu__kzjkc in list(sort_node.df_out_vars.keys()):
        sort_node.df_out_vars[ndcu__kzjkc] = visit_vars_inner(sort_node.
            df_out_vars[ndcu__kzjkc], callback, cbdata)


ir_utils.visit_vars_extensions[Sort] = visit_vars_sort


def remove_dead_sort(sort_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    alxie__mqx = []
    for ndcu__kzjkc, mavf__hzah in sort_node.df_out_vars.items():
        if mavf__hzah.name not in lives:
            alxie__mqx.append(ndcu__kzjkc)
    for ymftk__byng in alxie__mqx:
        sort_node.df_in_vars.pop(ymftk__byng)
        sort_node.df_out_vars.pop(ymftk__byng)
    if len(sort_node.df_out_vars) == 0 and all(kyidg__yjtlc.name not in
        lives for kyidg__yjtlc in sort_node.out_key_arrs):
        return None
    return sort_node


ir_utils.remove_dead_extensions[Sort] = remove_dead_sort


def sort_usedefs(sort_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({kyidg__yjtlc.name for kyidg__yjtlc in sort_node.key_arrs})
    use_set.update({kyidg__yjtlc.name for kyidg__yjtlc in sort_node.
        df_in_vars.values()})
    if not sort_node.inplace:
        def_set.update({kyidg__yjtlc.name for kyidg__yjtlc in sort_node.
            out_key_arrs})
        def_set.update({kyidg__yjtlc.name for kyidg__yjtlc in sort_node.
            df_out_vars.values()})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Sort] = sort_usedefs


def get_copies_sort(sort_node, typemap):
    lmos__ghibe = set()
    if not sort_node.inplace:
        lmos__ghibe = set(kyidg__yjtlc.name for kyidg__yjtlc in sort_node.
            df_out_vars.values())
        lmos__ghibe.update({kyidg__yjtlc.name for kyidg__yjtlc in sort_node
            .out_key_arrs})
    return set(), lmos__ghibe


ir_utils.copy_propagate_extensions[Sort] = get_copies_sort


def apply_copies_sort(sort_node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    for nhkv__bzax in range(len(sort_node.key_arrs)):
        sort_node.key_arrs[nhkv__bzax] = replace_vars_inner(sort_node.
            key_arrs[nhkv__bzax], var_dict)
        sort_node.out_key_arrs[nhkv__bzax] = replace_vars_inner(sort_node.
            out_key_arrs[nhkv__bzax], var_dict)
    for ndcu__kzjkc in list(sort_node.df_in_vars.keys()):
        sort_node.df_in_vars[ndcu__kzjkc] = replace_vars_inner(sort_node.
            df_in_vars[ndcu__kzjkc], var_dict)
    for ndcu__kzjkc in list(sort_node.df_out_vars.keys()):
        sort_node.df_out_vars[ndcu__kzjkc] = replace_vars_inner(sort_node.
            df_out_vars[ndcu__kzjkc], var_dict)
    return


ir_utils.apply_copy_propagate_extensions[Sort] = apply_copies_sort


def sort_distributed_run(sort_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    lfkid__xmtk = False
    zpqz__ewyy = list(sort_node.df_in_vars.values())
    aakpu__decs = list(sort_node.df_out_vars.values())
    if array_dists is not None:
        lfkid__xmtk = True
        for kyidg__yjtlc in (sort_node.key_arrs + sort_node.out_key_arrs +
            zpqz__ewyy + aakpu__decs):
            if array_dists[kyidg__yjtlc.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                kyidg__yjtlc.name] != distributed_pass.Distribution.OneD_Var:
                lfkid__xmtk = False
    loc = sort_node.loc
    sqv__zxg = sort_node.key_arrs[0].scope
    nodes = []
    key_arrs = sort_node.key_arrs
    if not sort_node.inplace:
        rdbe__mrar = []
        for kyidg__yjtlc in key_arrs:
            wktk__yrrzg = _copy_array_nodes(kyidg__yjtlc, nodes, typingctx,
                targetctx, typemap, calltypes)
            rdbe__mrar.append(wktk__yrrzg)
        key_arrs = rdbe__mrar
        mtj__dsw = []
        for kyidg__yjtlc in zpqz__ewyy:
            ynjaf__tclw = _copy_array_nodes(kyidg__yjtlc, nodes, typingctx,
                targetctx, typemap, calltypes)
            mtj__dsw.append(ynjaf__tclw)
        zpqz__ewyy = mtj__dsw
    key_name_args = [f'key{nhkv__bzax}' for nhkv__bzax in range(len(key_arrs))]
    hcq__sibj = ', '.join(key_name_args)
    col_name_args = [f'c{nhkv__bzax}' for nhkv__bzax in range(len(zpqz__ewyy))]
    xxig__rkgnc = ', '.join(col_name_args)
    jck__jgvpp = 'def f({}, {}):\n'.format(hcq__sibj, xxig__rkgnc)
    jck__jgvpp += get_sort_cpp_section(key_name_args, col_name_args,
        sort_node.ascending_list, sort_node.na_position_b, lfkid__xmtk)
    jck__jgvpp += '  return key_arrs, data\n'
    ndwpx__rpbc = {}
    exec(jck__jgvpp, {}, ndwpx__rpbc)
    ssxb__myo = ndwpx__rpbc['f']
    vpv__nwey = types.Tuple([typemap[kyidg__yjtlc.name] for kyidg__yjtlc in
        key_arrs])
    mhp__irg = types.Tuple([typemap[kyidg__yjtlc.name] for kyidg__yjtlc in
        zpqz__ewyy])
    duq__yye = compile_to_numba_ir(ssxb__myo, {'bodo': bodo, 'np': np,
        'to_list_if_immutable_arr': to_list_if_immutable_arr,
        'cp_str_list_to_array': cp_str_list_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'sort_values_table':
        sort_values_table, 'arr_info_list_to_table': arr_info_list_to_table,
        'array_to_info': array_to_info}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=tuple(list(vpv__nwey.types) + list(mhp__irg.
        types)), typemap=typemap, calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(duq__yye, key_arrs + zpqz__ewyy)
    nodes += duq__yye.body[:-2]
    aoeb__gclky = nodes[-1].target
    lzm__iaz = ir.Var(sqv__zxg, mk_unique_var('key_data'), loc)
    typemap[lzm__iaz.name] = vpv__nwey
    gen_getitem(lzm__iaz, aoeb__gclky, 0, calltypes, nodes)
    mdruq__qou = ir.Var(sqv__zxg, mk_unique_var('sort_data'), loc)
    typemap[mdruq__qou.name] = mhp__irg
    gen_getitem(mdruq__qou, aoeb__gclky, 1, calltypes, nodes)
    for nhkv__bzax, var in enumerate(sort_node.out_key_arrs):
        gen_getitem(var, lzm__iaz, nhkv__bzax, calltypes, nodes)
    for nhkv__bzax, var in enumerate(aakpu__decs):
        gen_getitem(var, mdruq__qou, nhkv__bzax, calltypes, nodes)
    return nodes


distributed_pass.distributed_run_extensions[Sort] = sort_distributed_run


def _copy_array_nodes(var, nodes, typingctx, targetctx, typemap, calltypes):

    def _impl(arr):
        return arr.copy()
    duq__yye = compile_to_numba_ir(_impl, {}, typingctx=typingctx,
        targetctx=targetctx, arg_typs=(typemap[var.name],), typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(duq__yye, [var])
    nodes += duq__yye.body[:-2]
    return nodes[-1].target


def get_sort_cpp_section(key_name_args, col_name_args, ascending_list,
    na_position_b, parallel_b):
    jck__jgvpp = ''
    rhix__oqljq = len(key_name_args)
    kwe__upd = ['array_to_info({})'.format(ksz__uuel) for ksz__uuel in
        key_name_args] + ['array_to_info({})'.format(ksz__uuel) for
        ksz__uuel in col_name_args]
    jck__jgvpp += '  info_list_total = [{}]\n'.format(','.join(kwe__upd))
    jck__jgvpp += '  table_total = arr_info_list_to_table(info_list_total)\n'
    jck__jgvpp += '  vect_ascending = np.array([{}])\n'.format(','.join('1' if
        cqc__wjeh else '0' for cqc__wjeh in ascending_list))
    jck__jgvpp += '  na_position = np.array([{}])\n'.format(','.join('1' if
        cqc__wjeh else '0' for cqc__wjeh in na_position_b))
    jck__jgvpp += (
        """  out_table = sort_values_table(table_total, {}, vect_ascending.ctypes, na_position.ctypes, {})
"""
        .format(rhix__oqljq, parallel_b))
    lzpi__nqlgj = 0
    wcjjw__ikj = []
    for ksz__uuel in key_name_args:
        wcjjw__ikj.append('info_to_array(info_from_table(out_table, {}), {})'
            .format(lzpi__nqlgj, ksz__uuel))
        lzpi__nqlgj += 1
    jck__jgvpp += '  key_arrs = ({},)\n'.format(','.join(wcjjw__ikj))
    qdbrp__sul = []
    for ksz__uuel in col_name_args:
        qdbrp__sul.append('info_to_array(info_from_table(out_table, {}), {})'
            .format(lzpi__nqlgj, ksz__uuel))
        lzpi__nqlgj += 1
    if len(qdbrp__sul) > 0:
        jck__jgvpp += '  data = ({},)\n'.format(','.join(qdbrp__sul))
    else:
        jck__jgvpp += '  data = ()\n'
    jck__jgvpp += '  delete_table(out_table)\n'
    jck__jgvpp += '  delete_table(table_total)\n'
    return jck__jgvpp
