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
            self.na_position_b = tuple([(True if wrpzv__moep == 'last' else
                False) for wrpzv__moep in na_position])
        if isinstance(ascending_list, bool):
            ascending_list = (ascending_list,) * len(key_arrs)
        self.ascending_list = ascending_list
        self.loc = loc

    def __repr__(self):
        cqtee__zat = ''
        for kzjdn__yzk, wpelm__boapu in self.df_in_vars.items():
            cqtee__zat += "'{}':{}, ".format(kzjdn__yzk, wpelm__boapu.name)
        zvdvx__svy = '{}{{{}}}'.format(self.df_in, cqtee__zat)
        qle__wooc = ''
        for kzjdn__yzk, wpelm__boapu in self.df_out_vars.items():
            qle__wooc += "'{}':{}, ".format(kzjdn__yzk, wpelm__boapu.name)
        fhi__dpqx = '{}{{{}}}'.format(self.df_out, qle__wooc)
        return 'sort: [key: {}] {} [key: {}] {}'.format(', '.join(
            wpelm__boapu.name for wpelm__boapu in self.key_arrs),
            zvdvx__svy, ', '.join(wpelm__boapu.name for wpelm__boapu in
            self.out_key_arrs), fhi__dpqx)


def sort_array_analysis(sort_node, equiv_set, typemap, array_analysis):
    rxky__tscub = []
    wwfw__bizm = sort_node.key_arrs + list(sort_node.df_in_vars.values())
    for yheb__vle in wwfw__bizm:
        iuc__ayba = equiv_set.get_shape(yheb__vle)
        if iuc__ayba is not None:
            rxky__tscub.append(iuc__ayba[0])
    if len(rxky__tscub) > 1:
        equiv_set.insert_equiv(*rxky__tscub)
    mfwe__nsesn = []
    rxky__tscub = []
    ltbe__mzrfo = sort_node.out_key_arrs + list(sort_node.df_out_vars.values())
    for yheb__vle in ltbe__mzrfo:
        jingi__kife = typemap[yheb__vle.name]
        tzu__gsnrt = array_analysis._gen_shape_call(equiv_set, yheb__vle,
            jingi__kife.ndim, None, mfwe__nsesn)
        equiv_set.insert_equiv(yheb__vle, tzu__gsnrt)
        rxky__tscub.append(tzu__gsnrt[0])
        equiv_set.define(yheb__vle, set())
    if len(rxky__tscub) > 1:
        equiv_set.insert_equiv(*rxky__tscub)
    return [], mfwe__nsesn


numba.parfors.array_analysis.array_analysis_extensions[Sort
    ] = sort_array_analysis


def sort_distributed_analysis(sort_node, array_dists):
    wwfw__bizm = sort_node.key_arrs + list(sort_node.df_in_vars.values())
    bupsg__ozucu = sort_node.out_key_arrs + list(sort_node.df_out_vars.values()
        )
    jaowt__zekam = Distribution.OneD
    for yheb__vle in wwfw__bizm:
        jaowt__zekam = Distribution(min(jaowt__zekam.value, array_dists[
            yheb__vle.name].value))
    brq__rktao = Distribution(min(jaowt__zekam.value, Distribution.OneD_Var
        .value))
    for yheb__vle in bupsg__ozucu:
        if yheb__vle.name in array_dists:
            brq__rktao = Distribution(min(brq__rktao.value, array_dists[
                yheb__vle.name].value))
    if brq__rktao != Distribution.OneD_Var:
        jaowt__zekam = brq__rktao
    for yheb__vle in wwfw__bizm:
        array_dists[yheb__vle.name] = jaowt__zekam
    for yheb__vle in bupsg__ozucu:
        array_dists[yheb__vle.name] = brq__rktao
    return


distributed_analysis.distributed_analysis_extensions[Sort
    ] = sort_distributed_analysis


def sort_typeinfer(sort_node, typeinferer):
    for caqws__ednvo, rmhu__ghys in zip(sort_node.key_arrs, sort_node.
        out_key_arrs):
        typeinferer.constraints.append(typeinfer.Propagate(dst=rmhu__ghys.
            name, src=caqws__ednvo.name, loc=sort_node.loc))
    for pyvy__iyv, yheb__vle in sort_node.df_in_vars.items():
        kabix__pjt = sort_node.df_out_vars[pyvy__iyv]
        typeinferer.constraints.append(typeinfer.Propagate(dst=kabix__pjt.
            name, src=yheb__vle.name, loc=sort_node.loc))
    return


typeinfer.typeinfer_extensions[Sort] = sort_typeinfer


def build_sort_definitions(sort_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    if not sort_node.inplace:
        for yheb__vle in (sort_node.out_key_arrs + list(sort_node.
            df_out_vars.values())):
            definitions[yheb__vle.name].append(sort_node)
    return definitions


ir_utils.build_defs_extensions[Sort] = build_sort_definitions


def visit_vars_sort(sort_node, callback, cbdata):
    if debug_prints():
        print('visiting sort vars for:', sort_node)
        print('cbdata: ', sorted(cbdata.items()))
    for mcrcx__wwgxz in range(len(sort_node.key_arrs)):
        sort_node.key_arrs[mcrcx__wwgxz] = visit_vars_inner(sort_node.
            key_arrs[mcrcx__wwgxz], callback, cbdata)
        sort_node.out_key_arrs[mcrcx__wwgxz] = visit_vars_inner(sort_node.
            out_key_arrs[mcrcx__wwgxz], callback, cbdata)
    for pyvy__iyv in list(sort_node.df_in_vars.keys()):
        sort_node.df_in_vars[pyvy__iyv] = visit_vars_inner(sort_node.
            df_in_vars[pyvy__iyv], callback, cbdata)
    for pyvy__iyv in list(sort_node.df_out_vars.keys()):
        sort_node.df_out_vars[pyvy__iyv] = visit_vars_inner(sort_node.
            df_out_vars[pyvy__iyv], callback, cbdata)


ir_utils.visit_vars_extensions[Sort] = visit_vars_sort


def remove_dead_sort(sort_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    rqc__gpzzp = []
    for pyvy__iyv, yheb__vle in sort_node.df_out_vars.items():
        if yheb__vle.name not in lives:
            rqc__gpzzp.append(pyvy__iyv)
    for fxfc__cmn in rqc__gpzzp:
        sort_node.df_in_vars.pop(fxfc__cmn)
        sort_node.df_out_vars.pop(fxfc__cmn)
    if len(sort_node.df_out_vars) == 0 and all(wpelm__boapu.name not in
        lives for wpelm__boapu in sort_node.out_key_arrs):
        return None
    return sort_node


ir_utils.remove_dead_extensions[Sort] = remove_dead_sort


def sort_usedefs(sort_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({wpelm__boapu.name for wpelm__boapu in sort_node.key_arrs})
    use_set.update({wpelm__boapu.name for wpelm__boapu in sort_node.
        df_in_vars.values()})
    if not sort_node.inplace:
        def_set.update({wpelm__boapu.name for wpelm__boapu in sort_node.
            out_key_arrs})
        def_set.update({wpelm__boapu.name for wpelm__boapu in sort_node.
            df_out_vars.values()})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Sort] = sort_usedefs


def get_copies_sort(sort_node, typemap):
    khaey__ljmlj = set()
    if not sort_node.inplace:
        khaey__ljmlj = set(wpelm__boapu.name for wpelm__boapu in sort_node.
            df_out_vars.values())
        khaey__ljmlj.update({wpelm__boapu.name for wpelm__boapu in
            sort_node.out_key_arrs})
    return set(), khaey__ljmlj


ir_utils.copy_propagate_extensions[Sort] = get_copies_sort


def apply_copies_sort(sort_node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    for mcrcx__wwgxz in range(len(sort_node.key_arrs)):
        sort_node.key_arrs[mcrcx__wwgxz] = replace_vars_inner(sort_node.
            key_arrs[mcrcx__wwgxz], var_dict)
        sort_node.out_key_arrs[mcrcx__wwgxz] = replace_vars_inner(sort_node
            .out_key_arrs[mcrcx__wwgxz], var_dict)
    for pyvy__iyv in list(sort_node.df_in_vars.keys()):
        sort_node.df_in_vars[pyvy__iyv] = replace_vars_inner(sort_node.
            df_in_vars[pyvy__iyv], var_dict)
    for pyvy__iyv in list(sort_node.df_out_vars.keys()):
        sort_node.df_out_vars[pyvy__iyv] = replace_vars_inner(sort_node.
            df_out_vars[pyvy__iyv], var_dict)
    return


ir_utils.apply_copy_propagate_extensions[Sort] = apply_copies_sort


def sort_distributed_run(sort_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    seo__jklkp = False
    jojd__oywa = list(sort_node.df_in_vars.values())
    ltbe__mzrfo = list(sort_node.df_out_vars.values())
    if array_dists is not None:
        seo__jklkp = True
        for wpelm__boapu in (sort_node.key_arrs + sort_node.out_key_arrs +
            jojd__oywa + ltbe__mzrfo):
            if array_dists[wpelm__boapu.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                wpelm__boapu.name] != distributed_pass.Distribution.OneD_Var:
                seo__jklkp = False
    loc = sort_node.loc
    ekvnu__rdw = sort_node.key_arrs[0].scope
    nodes = []
    key_arrs = sort_node.key_arrs
    if not sort_node.inplace:
        xggc__eihu = []
        for wpelm__boapu in key_arrs:
            rfpo__wxntv = _copy_array_nodes(wpelm__boapu, nodes, typingctx,
                targetctx, typemap, calltypes)
            xggc__eihu.append(rfpo__wxntv)
        key_arrs = xggc__eihu
        ytcny__dgp = []
        for wpelm__boapu in jojd__oywa:
            xpoi__szt = _copy_array_nodes(wpelm__boapu, nodes, typingctx,
                targetctx, typemap, calltypes)
            ytcny__dgp.append(xpoi__szt)
        jojd__oywa = ytcny__dgp
    key_name_args = [f'key{mcrcx__wwgxz}' for mcrcx__wwgxz in range(len(
        key_arrs))]
    tuwko__lrxn = ', '.join(key_name_args)
    col_name_args = [f'c{mcrcx__wwgxz}' for mcrcx__wwgxz in range(len(
        jojd__oywa))]
    xely__uusp = ', '.join(col_name_args)
    xtxed__tou = 'def f({}, {}):\n'.format(tuwko__lrxn, xely__uusp)
    xtxed__tou += get_sort_cpp_section(key_name_args, col_name_args,
        sort_node.ascending_list, sort_node.na_position_b, seo__jklkp)
    xtxed__tou += '  return key_arrs, data\n'
    acw__fpsz = {}
    exec(xtxed__tou, {}, acw__fpsz)
    qocd__kbejr = acw__fpsz['f']
    augj__syds = types.Tuple([typemap[wpelm__boapu.name] for wpelm__boapu in
        key_arrs])
    nuf__whd = types.Tuple([typemap[wpelm__boapu.name] for wpelm__boapu in
        jojd__oywa])
    quxwj__kje = compile_to_numba_ir(qocd__kbejr, {'bodo': bodo, 'np': np,
        'to_list_if_immutable_arr': to_list_if_immutable_arr,
        'cp_str_list_to_array': cp_str_list_to_array, 'delete_table':
        delete_table, 'delete_table_decref_arrays':
        delete_table_decref_arrays, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'sort_values_table':
        sort_values_table, 'arr_info_list_to_table': arr_info_list_to_table,
        'array_to_info': array_to_info}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=tuple(list(augj__syds.types) + list(nuf__whd.
        types)), typemap=typemap, calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(quxwj__kje, key_arrs + jojd__oywa)
    nodes += quxwj__kje.body[:-2]
    xenji__rmsf = nodes[-1].target
    rle__pviz = ir.Var(ekvnu__rdw, mk_unique_var('key_data'), loc)
    typemap[rle__pviz.name] = augj__syds
    gen_getitem(rle__pviz, xenji__rmsf, 0, calltypes, nodes)
    goq__nxoe = ir.Var(ekvnu__rdw, mk_unique_var('sort_data'), loc)
    typemap[goq__nxoe.name] = nuf__whd
    gen_getitem(goq__nxoe, xenji__rmsf, 1, calltypes, nodes)
    for mcrcx__wwgxz, var in enumerate(sort_node.out_key_arrs):
        gen_getitem(var, rle__pviz, mcrcx__wwgxz, calltypes, nodes)
    for mcrcx__wwgxz, var in enumerate(ltbe__mzrfo):
        gen_getitem(var, goq__nxoe, mcrcx__wwgxz, calltypes, nodes)
    return nodes


distributed_pass.distributed_run_extensions[Sort] = sort_distributed_run


def _copy_array_nodes(var, nodes, typingctx, targetctx, typemap, calltypes):

    def _impl(arr):
        return arr.copy()
    quxwj__kje = compile_to_numba_ir(_impl, {}, typingctx=typingctx,
        targetctx=targetctx, arg_typs=(typemap[var.name],), typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(quxwj__kje, [var])
    nodes += quxwj__kje.body[:-2]
    return nodes[-1].target


def get_sort_cpp_section(key_name_args, col_name_args, ascending_list,
    na_position_b, parallel_b):
    xtxed__tou = ''
    cxzgs__yqmcj = len(key_name_args)
    tyzhc__aoei = ['array_to_info({})'.format(rpo__bzujs) for rpo__bzujs in
        key_name_args] + ['array_to_info({})'.format(rpo__bzujs) for
        rpo__bzujs in col_name_args]
    xtxed__tou += '  info_list_total = [{}]\n'.format(','.join(tyzhc__aoei))
    xtxed__tou += '  table_total = arr_info_list_to_table(info_list_total)\n'
    xtxed__tou += '  vect_ascending = np.array([{}])\n'.format(','.join('1' if
        ssy__tngt else '0' for ssy__tngt in ascending_list))
    xtxed__tou += '  na_position = np.array([{}])\n'.format(','.join('1' if
        ssy__tngt else '0' for ssy__tngt in na_position_b))
    xtxed__tou += (
        """  out_table = sort_values_table(table_total, {}, vect_ascending.ctypes, na_position.ctypes, {})
"""
        .format(cxzgs__yqmcj, parallel_b))
    cznq__sjy = 0
    kive__tzkj = []
    for rpo__bzujs in key_name_args:
        kive__tzkj.append('info_to_array(info_from_table(out_table, {}), {})'
            .format(cznq__sjy, rpo__bzujs))
        cznq__sjy += 1
    xtxed__tou += '  key_arrs = ({},)\n'.format(','.join(kive__tzkj))
    duxq__hxmxh = []
    for rpo__bzujs in col_name_args:
        duxq__hxmxh.append('info_to_array(info_from_table(out_table, {}), {})'
            .format(cznq__sjy, rpo__bzujs))
        cznq__sjy += 1
    if len(duxq__hxmxh) > 0:
        xtxed__tou += '  data = ({},)\n'.format(','.join(duxq__hxmxh))
    else:
        xtxed__tou += '  data = ()\n'
    xtxed__tou += '  delete_table(out_table)\n'
    xtxed__tou += '  delete_table(table_total)\n'
    return xtxed__tou
