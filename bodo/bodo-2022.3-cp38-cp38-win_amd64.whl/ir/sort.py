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
            self.na_position_b = tuple([(True if gefgg__hlujj == 'last' else
                False) for gefgg__hlujj in na_position])
        if isinstance(ascending_list, bool):
            ascending_list = (ascending_list,) * len(key_arrs)
        self.ascending_list = ascending_list
        self.loc = loc

    def __repr__(self):
        nqnk__fdwtn = ''
        for pwdgy__boq, kbvze__zmv in self.df_in_vars.items():
            nqnk__fdwtn += "'{}':{}, ".format(pwdgy__boq, kbvze__zmv.name)
        okr__jlt = '{}{{{}}}'.format(self.df_in, nqnk__fdwtn)
        mll__avgd = ''
        for pwdgy__boq, kbvze__zmv in self.df_out_vars.items():
            mll__avgd += "'{}':{}, ".format(pwdgy__boq, kbvze__zmv.name)
        mwlvf__eczzs = '{}{{{}}}'.format(self.df_out, mll__avgd)
        return 'sort: [key: {}] {} [key: {}] {}'.format(', '.join(
            kbvze__zmv.name for kbvze__zmv in self.key_arrs), okr__jlt,
            ', '.join(kbvze__zmv.name for kbvze__zmv in self.out_key_arrs),
            mwlvf__eczzs)


def sort_array_analysis(sort_node, equiv_set, typemap, array_analysis):
    ubsjl__qmsq = []
    nymrz__ckv = sort_node.key_arrs + list(sort_node.df_in_vars.values())
    for vbmlt__yrqnl in nymrz__ckv:
        yvft__drijm = equiv_set.get_shape(vbmlt__yrqnl)
        if yvft__drijm is not None:
            ubsjl__qmsq.append(yvft__drijm[0])
    if len(ubsjl__qmsq) > 1:
        equiv_set.insert_equiv(*ubsjl__qmsq)
    tgpma__vxt = []
    ubsjl__qmsq = []
    qmzyn__inhy = sort_node.out_key_arrs + list(sort_node.df_out_vars.values())
    for vbmlt__yrqnl in qmzyn__inhy:
        tjrue__lfue = typemap[vbmlt__yrqnl.name]
        jbh__qrx = array_analysis._gen_shape_call(equiv_set, vbmlt__yrqnl,
            tjrue__lfue.ndim, None, tgpma__vxt)
        equiv_set.insert_equiv(vbmlt__yrqnl, jbh__qrx)
        ubsjl__qmsq.append(jbh__qrx[0])
        equiv_set.define(vbmlt__yrqnl, set())
    if len(ubsjl__qmsq) > 1:
        equiv_set.insert_equiv(*ubsjl__qmsq)
    return [], tgpma__vxt


numba.parfors.array_analysis.array_analysis_extensions[Sort
    ] = sort_array_analysis


def sort_distributed_analysis(sort_node, array_dists):
    nymrz__ckv = sort_node.key_arrs + list(sort_node.df_in_vars.values())
    hxqsz__ecte = sort_node.out_key_arrs + list(sort_node.df_out_vars.values())
    grwgy__sjm = Distribution.OneD
    for vbmlt__yrqnl in nymrz__ckv:
        grwgy__sjm = Distribution(min(grwgy__sjm.value, array_dists[
            vbmlt__yrqnl.name].value))
    otpw__wxri = Distribution(min(grwgy__sjm.value, Distribution.OneD_Var.
        value))
    for vbmlt__yrqnl in hxqsz__ecte:
        if vbmlt__yrqnl.name in array_dists:
            otpw__wxri = Distribution(min(otpw__wxri.value, array_dists[
                vbmlt__yrqnl.name].value))
    if otpw__wxri != Distribution.OneD_Var:
        grwgy__sjm = otpw__wxri
    for vbmlt__yrqnl in nymrz__ckv:
        array_dists[vbmlt__yrqnl.name] = grwgy__sjm
    for vbmlt__yrqnl in hxqsz__ecte:
        array_dists[vbmlt__yrqnl.name] = otpw__wxri
    return


distributed_analysis.distributed_analysis_extensions[Sort
    ] = sort_distributed_analysis


def sort_typeinfer(sort_node, typeinferer):
    for dxwj__jnr, cawqv__uyty in zip(sort_node.key_arrs, sort_node.
        out_key_arrs):
        typeinferer.constraints.append(typeinfer.Propagate(dst=cawqv__uyty.
            name, src=dxwj__jnr.name, loc=sort_node.loc))
    for dff__iut, vbmlt__yrqnl in sort_node.df_in_vars.items():
        hgc__hykz = sort_node.df_out_vars[dff__iut]
        typeinferer.constraints.append(typeinfer.Propagate(dst=hgc__hykz.
            name, src=vbmlt__yrqnl.name, loc=sort_node.loc))
    return


typeinfer.typeinfer_extensions[Sort] = sort_typeinfer


def build_sort_definitions(sort_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    if not sort_node.inplace:
        for vbmlt__yrqnl in (sort_node.out_key_arrs + list(sort_node.
            df_out_vars.values())):
            definitions[vbmlt__yrqnl.name].append(sort_node)
    return definitions


ir_utils.build_defs_extensions[Sort] = build_sort_definitions


def visit_vars_sort(sort_node, callback, cbdata):
    if debug_prints():
        print('visiting sort vars for:', sort_node)
        print('cbdata: ', sorted(cbdata.items()))
    for iemeg__hys in range(len(sort_node.key_arrs)):
        sort_node.key_arrs[iemeg__hys] = visit_vars_inner(sort_node.
            key_arrs[iemeg__hys], callback, cbdata)
        sort_node.out_key_arrs[iemeg__hys] = visit_vars_inner(sort_node.
            out_key_arrs[iemeg__hys], callback, cbdata)
    for dff__iut in list(sort_node.df_in_vars.keys()):
        sort_node.df_in_vars[dff__iut] = visit_vars_inner(sort_node.
            df_in_vars[dff__iut], callback, cbdata)
    for dff__iut in list(sort_node.df_out_vars.keys()):
        sort_node.df_out_vars[dff__iut] = visit_vars_inner(sort_node.
            df_out_vars[dff__iut], callback, cbdata)


ir_utils.visit_vars_extensions[Sort] = visit_vars_sort


def remove_dead_sort(sort_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    ejsd__fqwql = []
    for dff__iut, vbmlt__yrqnl in sort_node.df_out_vars.items():
        if vbmlt__yrqnl.name not in lives:
            ejsd__fqwql.append(dff__iut)
    for qzkgy__lbpu in ejsd__fqwql:
        sort_node.df_in_vars.pop(qzkgy__lbpu)
        sort_node.df_out_vars.pop(qzkgy__lbpu)
    if len(sort_node.df_out_vars) == 0 and all(kbvze__zmv.name not in lives for
        kbvze__zmv in sort_node.out_key_arrs):
        return None
    return sort_node


ir_utils.remove_dead_extensions[Sort] = remove_dead_sort


def sort_usedefs(sort_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({kbvze__zmv.name for kbvze__zmv in sort_node.key_arrs})
    use_set.update({kbvze__zmv.name for kbvze__zmv in sort_node.df_in_vars.
        values()})
    if not sort_node.inplace:
        def_set.update({kbvze__zmv.name for kbvze__zmv in sort_node.
            out_key_arrs})
        def_set.update({kbvze__zmv.name for kbvze__zmv in sort_node.
            df_out_vars.values()})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Sort] = sort_usedefs


def get_copies_sort(sort_node, typemap):
    lch__ndt = set()
    if not sort_node.inplace:
        lch__ndt = set(kbvze__zmv.name for kbvze__zmv in sort_node.
            df_out_vars.values())
        lch__ndt.update({kbvze__zmv.name for kbvze__zmv in sort_node.
            out_key_arrs})
    return set(), lch__ndt


ir_utils.copy_propagate_extensions[Sort] = get_copies_sort


def apply_copies_sort(sort_node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    for iemeg__hys in range(len(sort_node.key_arrs)):
        sort_node.key_arrs[iemeg__hys] = replace_vars_inner(sort_node.
            key_arrs[iemeg__hys], var_dict)
        sort_node.out_key_arrs[iemeg__hys] = replace_vars_inner(sort_node.
            out_key_arrs[iemeg__hys], var_dict)
    for dff__iut in list(sort_node.df_in_vars.keys()):
        sort_node.df_in_vars[dff__iut] = replace_vars_inner(sort_node.
            df_in_vars[dff__iut], var_dict)
    for dff__iut in list(sort_node.df_out_vars.keys()):
        sort_node.df_out_vars[dff__iut] = replace_vars_inner(sort_node.
            df_out_vars[dff__iut], var_dict)
    return


ir_utils.apply_copy_propagate_extensions[Sort] = apply_copies_sort


def sort_distributed_run(sort_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    pcor__benpo = False
    cwez__dddsy = list(sort_node.df_in_vars.values())
    qmzyn__inhy = list(sort_node.df_out_vars.values())
    if array_dists is not None:
        pcor__benpo = True
        for kbvze__zmv in (sort_node.key_arrs + sort_node.out_key_arrs +
            cwez__dddsy + qmzyn__inhy):
            if array_dists[kbvze__zmv.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                kbvze__zmv.name] != distributed_pass.Distribution.OneD_Var:
                pcor__benpo = False
    loc = sort_node.loc
    bkc__hdc = sort_node.key_arrs[0].scope
    nodes = []
    key_arrs = sort_node.key_arrs
    if not sort_node.inplace:
        gjep__lyaj = []
        for kbvze__zmv in key_arrs:
            fif__jbn = _copy_array_nodes(kbvze__zmv, nodes, typingctx,
                targetctx, typemap, calltypes)
            gjep__lyaj.append(fif__jbn)
        key_arrs = gjep__lyaj
        mrsug__stq = []
        for kbvze__zmv in cwez__dddsy:
            hcqza__dxyf = _copy_array_nodes(kbvze__zmv, nodes, typingctx,
                targetctx, typemap, calltypes)
            mrsug__stq.append(hcqza__dxyf)
        cwez__dddsy = mrsug__stq
    key_name_args = [f'key{iemeg__hys}' for iemeg__hys in range(len(key_arrs))]
    pkeh__faask = ', '.join(key_name_args)
    col_name_args = [f'c{iemeg__hys}' for iemeg__hys in range(len(cwez__dddsy))
        ]
    shdw__bmc = ', '.join(col_name_args)
    fcgw__yixl = 'def f({}, {}):\n'.format(pkeh__faask, shdw__bmc)
    fcgw__yixl += get_sort_cpp_section(key_name_args, col_name_args,
        sort_node.ascending_list, sort_node.na_position_b, pcor__benpo)
    fcgw__yixl += '  return key_arrs, data\n'
    jbko__oyuxh = {}
    exec(fcgw__yixl, {}, jbko__oyuxh)
    wmmei__obre = jbko__oyuxh['f']
    qzaz__kkwqd = types.Tuple([typemap[kbvze__zmv.name] for kbvze__zmv in
        key_arrs])
    vqfyh__nkvvs = types.Tuple([typemap[kbvze__zmv.name] for kbvze__zmv in
        cwez__dddsy])
    oecq__mkwlr = compile_to_numba_ir(wmmei__obre, {'bodo': bodo, 'np': np,
        'to_list_if_immutable_arr': to_list_if_immutable_arr,
        'cp_str_list_to_array': cp_str_list_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'sort_values_table':
        sort_values_table, 'arr_info_list_to_table': arr_info_list_to_table,
        'array_to_info': array_to_info}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=tuple(list(qzaz__kkwqd.types) + list(
        vqfyh__nkvvs.types)), typemap=typemap, calltypes=calltypes
        ).blocks.popitem()[1]
    replace_arg_nodes(oecq__mkwlr, key_arrs + cwez__dddsy)
    nodes += oecq__mkwlr.body[:-2]
    gbs__tjf = nodes[-1].target
    yxi__jgl = ir.Var(bkc__hdc, mk_unique_var('key_data'), loc)
    typemap[yxi__jgl.name] = qzaz__kkwqd
    gen_getitem(yxi__jgl, gbs__tjf, 0, calltypes, nodes)
    vtmem__wowd = ir.Var(bkc__hdc, mk_unique_var('sort_data'), loc)
    typemap[vtmem__wowd.name] = vqfyh__nkvvs
    gen_getitem(vtmem__wowd, gbs__tjf, 1, calltypes, nodes)
    for iemeg__hys, var in enumerate(sort_node.out_key_arrs):
        gen_getitem(var, yxi__jgl, iemeg__hys, calltypes, nodes)
    for iemeg__hys, var in enumerate(qmzyn__inhy):
        gen_getitem(var, vtmem__wowd, iemeg__hys, calltypes, nodes)
    return nodes


distributed_pass.distributed_run_extensions[Sort] = sort_distributed_run


def _copy_array_nodes(var, nodes, typingctx, targetctx, typemap, calltypes):

    def _impl(arr):
        return arr.copy()
    oecq__mkwlr = compile_to_numba_ir(_impl, {}, typingctx=typingctx,
        targetctx=targetctx, arg_typs=(typemap[var.name],), typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(oecq__mkwlr, [var])
    nodes += oecq__mkwlr.body[:-2]
    return nodes[-1].target


def get_sort_cpp_section(key_name_args, col_name_args, ascending_list,
    na_position_b, parallel_b):
    fcgw__yixl = ''
    wdnir__tda = len(key_name_args)
    lyen__dzid = ['array_to_info({})'.format(hghy__azhj) for hghy__azhj in
        key_name_args] + ['array_to_info({})'.format(hghy__azhj) for
        hghy__azhj in col_name_args]
    fcgw__yixl += '  info_list_total = [{}]\n'.format(','.join(lyen__dzid))
    fcgw__yixl += '  table_total = arr_info_list_to_table(info_list_total)\n'
    fcgw__yixl += '  vect_ascending = np.array([{}])\n'.format(','.join('1' if
        pbtuj__aaqbv else '0' for pbtuj__aaqbv in ascending_list))
    fcgw__yixl += '  na_position = np.array([{}])\n'.format(','.join('1' if
        pbtuj__aaqbv else '0' for pbtuj__aaqbv in na_position_b))
    fcgw__yixl += (
        """  out_table = sort_values_table(table_total, {}, vect_ascending.ctypes, na_position.ctypes, {})
"""
        .format(wdnir__tda, parallel_b))
    gnxn__masq = 0
    pqtwf__jtlg = []
    for hghy__azhj in key_name_args:
        pqtwf__jtlg.append('info_to_array(info_from_table(out_table, {}), {})'
            .format(gnxn__masq, hghy__azhj))
        gnxn__masq += 1
    fcgw__yixl += '  key_arrs = ({},)\n'.format(','.join(pqtwf__jtlg))
    pntw__iei = []
    for hghy__azhj in col_name_args:
        pntw__iei.append('info_to_array(info_from_table(out_table, {}), {})'
            .format(gnxn__masq, hghy__azhj))
        gnxn__masq += 1
    if len(pntw__iei) > 0:
        fcgw__yixl += '  data = ({},)\n'.format(','.join(pntw__iei))
    else:
        fcgw__yixl += '  data = ()\n'
    fcgw__yixl += '  delete_table(out_table)\n'
    fcgw__yixl += '  delete_table(table_total)\n'
    return fcgw__yixl
