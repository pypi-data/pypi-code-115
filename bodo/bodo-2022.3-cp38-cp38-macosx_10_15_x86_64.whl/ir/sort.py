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
            self.na_position_b = tuple([(True if wjki__vhhwy == 'last' else
                False) for wjki__vhhwy in na_position])
        if isinstance(ascending_list, bool):
            ascending_list = (ascending_list,) * len(key_arrs)
        self.ascending_list = ascending_list
        self.loc = loc

    def __repr__(self):
        ryhg__uho = ''
        for bymbi__xyfk, nhkrc__ptoi in self.df_in_vars.items():
            ryhg__uho += "'{}':{}, ".format(bymbi__xyfk, nhkrc__ptoi.name)
        iuey__eke = '{}{{{}}}'.format(self.df_in, ryhg__uho)
        pibzq__xphm = ''
        for bymbi__xyfk, nhkrc__ptoi in self.df_out_vars.items():
            pibzq__xphm += "'{}':{}, ".format(bymbi__xyfk, nhkrc__ptoi.name)
        axyx__ygaj = '{}{{{}}}'.format(self.df_out, pibzq__xphm)
        return 'sort: [key: {}] {} [key: {}] {}'.format(', '.join(
            nhkrc__ptoi.name for nhkrc__ptoi in self.key_arrs), iuey__eke,
            ', '.join(nhkrc__ptoi.name for nhkrc__ptoi in self.out_key_arrs
            ), axyx__ygaj)


def sort_array_analysis(sort_node, equiv_set, typemap, array_analysis):
    ddfv__vaj = []
    qjnbs__nmdxi = sort_node.key_arrs + list(sort_node.df_in_vars.values())
    for xck__vor in qjnbs__nmdxi:
        diqw__tex = equiv_set.get_shape(xck__vor)
        if diqw__tex is not None:
            ddfv__vaj.append(diqw__tex[0])
    if len(ddfv__vaj) > 1:
        equiv_set.insert_equiv(*ddfv__vaj)
    lsv__jdve = []
    ddfv__vaj = []
    dpdkp__dixlv = sort_node.out_key_arrs + list(sort_node.df_out_vars.values()
        )
    for xck__vor in dpdkp__dixlv:
        xlin__kxkm = typemap[xck__vor.name]
        qft__nkn = array_analysis._gen_shape_call(equiv_set, xck__vor,
            xlin__kxkm.ndim, None, lsv__jdve)
        equiv_set.insert_equiv(xck__vor, qft__nkn)
        ddfv__vaj.append(qft__nkn[0])
        equiv_set.define(xck__vor, set())
    if len(ddfv__vaj) > 1:
        equiv_set.insert_equiv(*ddfv__vaj)
    return [], lsv__jdve


numba.parfors.array_analysis.array_analysis_extensions[Sort
    ] = sort_array_analysis


def sort_distributed_analysis(sort_node, array_dists):
    qjnbs__nmdxi = sort_node.key_arrs + list(sort_node.df_in_vars.values())
    xsgkt__fgva = sort_node.out_key_arrs + list(sort_node.df_out_vars.values())
    kher__lsogc = Distribution.OneD
    for xck__vor in qjnbs__nmdxi:
        kher__lsogc = Distribution(min(kher__lsogc.value, array_dists[
            xck__vor.name].value))
    yjwf__lvc = Distribution(min(kher__lsogc.value, Distribution.OneD_Var.
        value))
    for xck__vor in xsgkt__fgva:
        if xck__vor.name in array_dists:
            yjwf__lvc = Distribution(min(yjwf__lvc.value, array_dists[
                xck__vor.name].value))
    if yjwf__lvc != Distribution.OneD_Var:
        kher__lsogc = yjwf__lvc
    for xck__vor in qjnbs__nmdxi:
        array_dists[xck__vor.name] = kher__lsogc
    for xck__vor in xsgkt__fgva:
        array_dists[xck__vor.name] = yjwf__lvc
    return


distributed_analysis.distributed_analysis_extensions[Sort
    ] = sort_distributed_analysis


def sort_typeinfer(sort_node, typeinferer):
    for gwzg__jih, pmo__erpl in zip(sort_node.key_arrs, sort_node.out_key_arrs
        ):
        typeinferer.constraints.append(typeinfer.Propagate(dst=pmo__erpl.
            name, src=gwzg__jih.name, loc=sort_node.loc))
    for bgry__jvat, xck__vor in sort_node.df_in_vars.items():
        emz__wwh = sort_node.df_out_vars[bgry__jvat]
        typeinferer.constraints.append(typeinfer.Propagate(dst=emz__wwh.
            name, src=xck__vor.name, loc=sort_node.loc))
    return


typeinfer.typeinfer_extensions[Sort] = sort_typeinfer


def build_sort_definitions(sort_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    if not sort_node.inplace:
        for xck__vor in (sort_node.out_key_arrs + list(sort_node.
            df_out_vars.values())):
            definitions[xck__vor.name].append(sort_node)
    return definitions


ir_utils.build_defs_extensions[Sort] = build_sort_definitions


def visit_vars_sort(sort_node, callback, cbdata):
    if debug_prints():
        print('visiting sort vars for:', sort_node)
        print('cbdata: ', sorted(cbdata.items()))
    for kds__immq in range(len(sort_node.key_arrs)):
        sort_node.key_arrs[kds__immq] = visit_vars_inner(sort_node.key_arrs
            [kds__immq], callback, cbdata)
        sort_node.out_key_arrs[kds__immq] = visit_vars_inner(sort_node.
            out_key_arrs[kds__immq], callback, cbdata)
    for bgry__jvat in list(sort_node.df_in_vars.keys()):
        sort_node.df_in_vars[bgry__jvat] = visit_vars_inner(sort_node.
            df_in_vars[bgry__jvat], callback, cbdata)
    for bgry__jvat in list(sort_node.df_out_vars.keys()):
        sort_node.df_out_vars[bgry__jvat] = visit_vars_inner(sort_node.
            df_out_vars[bgry__jvat], callback, cbdata)


ir_utils.visit_vars_extensions[Sort] = visit_vars_sort


def remove_dead_sort(sort_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    qta__yuxlf = []
    for bgry__jvat, xck__vor in sort_node.df_out_vars.items():
        if xck__vor.name not in lives:
            qta__yuxlf.append(bgry__jvat)
    for bzgkd__vado in qta__yuxlf:
        sort_node.df_in_vars.pop(bzgkd__vado)
        sort_node.df_out_vars.pop(bzgkd__vado)
    if len(sort_node.df_out_vars) == 0 and all(nhkrc__ptoi.name not in
        lives for nhkrc__ptoi in sort_node.out_key_arrs):
        return None
    return sort_node


ir_utils.remove_dead_extensions[Sort] = remove_dead_sort


def sort_usedefs(sort_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({nhkrc__ptoi.name for nhkrc__ptoi in sort_node.key_arrs})
    use_set.update({nhkrc__ptoi.name for nhkrc__ptoi in sort_node.
        df_in_vars.values()})
    if not sort_node.inplace:
        def_set.update({nhkrc__ptoi.name for nhkrc__ptoi in sort_node.
            out_key_arrs})
        def_set.update({nhkrc__ptoi.name for nhkrc__ptoi in sort_node.
            df_out_vars.values()})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Sort] = sort_usedefs


def get_copies_sort(sort_node, typemap):
    lhfk__dfjc = set()
    if not sort_node.inplace:
        lhfk__dfjc = set(nhkrc__ptoi.name for nhkrc__ptoi in sort_node.
            df_out_vars.values())
        lhfk__dfjc.update({nhkrc__ptoi.name for nhkrc__ptoi in sort_node.
            out_key_arrs})
    return set(), lhfk__dfjc


ir_utils.copy_propagate_extensions[Sort] = get_copies_sort


def apply_copies_sort(sort_node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    for kds__immq in range(len(sort_node.key_arrs)):
        sort_node.key_arrs[kds__immq] = replace_vars_inner(sort_node.
            key_arrs[kds__immq], var_dict)
        sort_node.out_key_arrs[kds__immq] = replace_vars_inner(sort_node.
            out_key_arrs[kds__immq], var_dict)
    for bgry__jvat in list(sort_node.df_in_vars.keys()):
        sort_node.df_in_vars[bgry__jvat] = replace_vars_inner(sort_node.
            df_in_vars[bgry__jvat], var_dict)
    for bgry__jvat in list(sort_node.df_out_vars.keys()):
        sort_node.df_out_vars[bgry__jvat] = replace_vars_inner(sort_node.
            df_out_vars[bgry__jvat], var_dict)
    return


ir_utils.apply_copy_propagate_extensions[Sort] = apply_copies_sort


def sort_distributed_run(sort_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    qxig__wwu = False
    xyjr__rgrnu = list(sort_node.df_in_vars.values())
    dpdkp__dixlv = list(sort_node.df_out_vars.values())
    if array_dists is not None:
        qxig__wwu = True
        for nhkrc__ptoi in (sort_node.key_arrs + sort_node.out_key_arrs +
            xyjr__rgrnu + dpdkp__dixlv):
            if array_dists[nhkrc__ptoi.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                nhkrc__ptoi.name] != distributed_pass.Distribution.OneD_Var:
                qxig__wwu = False
    loc = sort_node.loc
    nkfg__ytses = sort_node.key_arrs[0].scope
    nodes = []
    key_arrs = sort_node.key_arrs
    if not sort_node.inplace:
        tgj__uhhg = []
        for nhkrc__ptoi in key_arrs:
            zrqk__rwrv = _copy_array_nodes(nhkrc__ptoi, nodes, typingctx,
                targetctx, typemap, calltypes)
            tgj__uhhg.append(zrqk__rwrv)
        key_arrs = tgj__uhhg
        pezj__uvbqp = []
        for nhkrc__ptoi in xyjr__rgrnu:
            jhfwy__idemn = _copy_array_nodes(nhkrc__ptoi, nodes, typingctx,
                targetctx, typemap, calltypes)
            pezj__uvbqp.append(jhfwy__idemn)
        xyjr__rgrnu = pezj__uvbqp
    key_name_args = [f'key{kds__immq}' for kds__immq in range(len(key_arrs))]
    fehu__jrm = ', '.join(key_name_args)
    col_name_args = [f'c{kds__immq}' for kds__immq in range(len(xyjr__rgrnu))]
    dyj__hhyr = ', '.join(col_name_args)
    gghm__hfrf = 'def f({}, {}):\n'.format(fehu__jrm, dyj__hhyr)
    gghm__hfrf += get_sort_cpp_section(key_name_args, col_name_args,
        sort_node.ascending_list, sort_node.na_position_b, qxig__wwu)
    gghm__hfrf += '  return key_arrs, data\n'
    ouq__hoogl = {}
    exec(gghm__hfrf, {}, ouq__hoogl)
    qxjbu__qhqn = ouq__hoogl['f']
    pcez__bzfds = types.Tuple([typemap[nhkrc__ptoi.name] for nhkrc__ptoi in
        key_arrs])
    xckzl__rrmbb = types.Tuple([typemap[nhkrc__ptoi.name] for nhkrc__ptoi in
        xyjr__rgrnu])
    mimds__mvm = compile_to_numba_ir(qxjbu__qhqn, {'bodo': bodo, 'np': np,
        'to_list_if_immutable_arr': to_list_if_immutable_arr,
        'cp_str_list_to_array': cp_str_list_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'sort_values_table':
        sort_values_table, 'arr_info_list_to_table': arr_info_list_to_table,
        'array_to_info': array_to_info}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=tuple(list(pcez__bzfds.types) + list(
        xckzl__rrmbb.types)), typemap=typemap, calltypes=calltypes
        ).blocks.popitem()[1]
    replace_arg_nodes(mimds__mvm, key_arrs + xyjr__rgrnu)
    nodes += mimds__mvm.body[:-2]
    ijzo__yan = nodes[-1].target
    txbg__lxcgm = ir.Var(nkfg__ytses, mk_unique_var('key_data'), loc)
    typemap[txbg__lxcgm.name] = pcez__bzfds
    gen_getitem(txbg__lxcgm, ijzo__yan, 0, calltypes, nodes)
    civ__hgwyt = ir.Var(nkfg__ytses, mk_unique_var('sort_data'), loc)
    typemap[civ__hgwyt.name] = xckzl__rrmbb
    gen_getitem(civ__hgwyt, ijzo__yan, 1, calltypes, nodes)
    for kds__immq, var in enumerate(sort_node.out_key_arrs):
        gen_getitem(var, txbg__lxcgm, kds__immq, calltypes, nodes)
    for kds__immq, var in enumerate(dpdkp__dixlv):
        gen_getitem(var, civ__hgwyt, kds__immq, calltypes, nodes)
    return nodes


distributed_pass.distributed_run_extensions[Sort] = sort_distributed_run


def _copy_array_nodes(var, nodes, typingctx, targetctx, typemap, calltypes):

    def _impl(arr):
        return arr.copy()
    mimds__mvm = compile_to_numba_ir(_impl, {}, typingctx=typingctx,
        targetctx=targetctx, arg_typs=(typemap[var.name],), typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(mimds__mvm, [var])
    nodes += mimds__mvm.body[:-2]
    return nodes[-1].target


def get_sort_cpp_section(key_name_args, col_name_args, ascending_list,
    na_position_b, parallel_b):
    gghm__hfrf = ''
    smz__ownd = len(key_name_args)
    fkwj__avx = ['array_to_info({})'.format(bzmmo__gxec) for bzmmo__gxec in
        key_name_args] + ['array_to_info({})'.format(bzmmo__gxec) for
        bzmmo__gxec in col_name_args]
    gghm__hfrf += '  info_list_total = [{}]\n'.format(','.join(fkwj__avx))
    gghm__hfrf += '  table_total = arr_info_list_to_table(info_list_total)\n'
    gghm__hfrf += '  vect_ascending = np.array([{}])\n'.format(','.join('1' if
        jeh__xsnyh else '0' for jeh__xsnyh in ascending_list))
    gghm__hfrf += '  na_position = np.array([{}])\n'.format(','.join('1' if
        jeh__xsnyh else '0' for jeh__xsnyh in na_position_b))
    gghm__hfrf += (
        """  out_table = sort_values_table(table_total, {}, vect_ascending.ctypes, na_position.ctypes, {})
"""
        .format(smz__ownd, parallel_b))
    psddo__yus = 0
    gxy__ldb = []
    for bzmmo__gxec in key_name_args:
        gxy__ldb.append('info_to_array(info_from_table(out_table, {}), {})'
            .format(psddo__yus, bzmmo__gxec))
        psddo__yus += 1
    gghm__hfrf += '  key_arrs = ({},)\n'.format(','.join(gxy__ldb))
    hbxl__smvq = []
    for bzmmo__gxec in col_name_args:
        hbxl__smvq.append('info_to_array(info_from_table(out_table, {}), {})'
            .format(psddo__yus, bzmmo__gxec))
        psddo__yus += 1
    if len(hbxl__smvq) > 0:
        gghm__hfrf += '  data = ({},)\n'.format(','.join(hbxl__smvq))
    else:
        gghm__hfrf += '  data = ()\n'
    gghm__hfrf += '  delete_table(out_table)\n'
    gghm__hfrf += '  delete_table(table_total)\n'
    return gghm__hfrf
