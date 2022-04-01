"""IR node for the join and merge"""
from collections import defaultdict
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, ir, ir_utils, typeinfer, types
from numba.core.ir_utils import compile_to_numba_ir, next_label, replace_arg_nodes, replace_vars_inner, visit_vars_inner
from numba.extending import intrinsic, overload
import bodo
from bodo.libs.array import arr_info_list_to_table, array_to_info, delete_table, delete_table_decref_arrays, hash_join_table, info_from_table, info_to_array
from bodo.libs.int_arr_ext import IntDtype
from bodo.libs.str_arr_ext import cp_str_list_to_array, to_list_if_immutable_arr
from bodo.libs.timsort import getitem_arr_tup, setitem_arr_tup
from bodo.transforms import distributed_analysis, distributed_pass
from bodo.transforms.distributed_analysis import Distribution
from bodo.utils.typing import BodoError, dtype_to_array_type, find_common_np_dtype, is_dtype_nullable, is_nullable_type, is_str_arr_type, to_nullable_type
from bodo.utils.utils import alloc_arr_tup, debug_prints, is_null_pointer
join_gen_cond_cfunc = {}
join_gen_cond_cfunc_addr = {}


@intrinsic
def add_join_gen_cond_cfunc_sym(typingctx, func, sym):

    def codegen(context, builder, signature, args):
        obkcy__kwjz = func.signature
        mqn__eeia = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64), lir
            .IntType(64)])
        egnty__ztol = cgutils.get_or_insert_function(builder.module,
            mqn__eeia, sym._literal_value)
        builder.call(egnty__ztol, [context.get_constant_null(obkcy__kwjz.
            args[0]), context.get_constant_null(obkcy__kwjz.args[1]),
            context.get_constant_null(obkcy__kwjz.args[2]), context.
            get_constant_null(obkcy__kwjz.args[3]), context.
            get_constant_null(obkcy__kwjz.args[4]), context.
            get_constant_null(obkcy__kwjz.args[5]), context.get_constant(
            types.int64, 0), context.get_constant(types.int64, 0)])
        context.add_linking_libs([join_gen_cond_cfunc[sym._literal_value].
            _library])
        return
    return types.none(func, sym), codegen


@numba.jit
def get_join_cond_addr(name):
    with numba.objmode(addr='int64'):
        addr = join_gen_cond_cfunc_addr[name]
    return addr


class Join(ir.Stmt):

    def __init__(self, df_out, left_df, right_df, left_keys, right_keys,
        out_data_vars, left_vars, right_vars, how, suffix_x, suffix_y, loc,
        is_left, is_right, is_join, left_index, right_index, indicator,
        is_na_equal, gen_cond_expr):
        self.df_out = df_out
        self.left_df = left_df
        self.right_df = right_df
        self.left_keys = left_keys
        self.right_keys = right_keys
        self.out_data_vars = out_data_vars
        self.left_vars = left_vars
        self.right_vars = right_vars
        self.how = how
        self.suffix_x = suffix_x
        self.suffix_y = suffix_y
        self.loc = loc
        self.is_left = is_left
        self.is_right = is_right
        self.is_join = is_join
        self.left_index = left_index
        self.right_index = right_index
        self.indicator = indicator
        self.is_na_equal = is_na_equal
        self.gen_cond_expr = gen_cond_expr
        self.left_cond_cols = set(hrw__aobl for hrw__aobl in left_vars.keys
            () if f'(left.{hrw__aobl})' in gen_cond_expr)
        self.right_cond_cols = set(hrw__aobl for hrw__aobl in right_vars.
            keys() if f'(right.{hrw__aobl})' in gen_cond_expr)
        dqyd__zszi = set(left_keys) & set(right_keys)
        jaaw__buq = set(left_vars.keys()) & set(right_vars.keys())
        aaeed__wpa = jaaw__buq - dqyd__zszi
        vect_same_key = []
        n_keys = len(left_keys)
        for lown__wxgq in range(n_keys):
            mrns__fqlx = left_keys[lown__wxgq]
            oyp__qbqfp = right_keys[lown__wxgq]
            vect_same_key.append(mrns__fqlx == oyp__qbqfp)
        self.vect_same_key = vect_same_key
        self.column_origins = {(str(hrw__aobl) + suffix_x if hrw__aobl in
            aaeed__wpa else hrw__aobl): ('left', hrw__aobl) for hrw__aobl in
            left_vars.keys()}
        self.column_origins.update({(str(hrw__aobl) + suffix_y if hrw__aobl in
            aaeed__wpa else hrw__aobl): ('right', hrw__aobl) for hrw__aobl in
            right_vars.keys()})
        if '$_bodo_index_' in aaeed__wpa:
            aaeed__wpa.remove('$_bodo_index_')
        self.add_suffix = aaeed__wpa

    def __repr__(self):
        bzwbp__algkr = ''
        for hrw__aobl, cjcal__bvbx in self.out_data_vars.items():
            bzwbp__algkr += "'{}':{}, ".format(hrw__aobl, cjcal__bvbx.name)
        vperl__nbn = '{}{{{}}}'.format(self.df_out, bzwbp__algkr)
        ajs__jlpp = ''
        for hrw__aobl, cjcal__bvbx in self.left_vars.items():
            ajs__jlpp += "'{}':{}, ".format(hrw__aobl, cjcal__bvbx.name)
        kpau__sgu = '{}{{{}}}'.format(self.left_df, ajs__jlpp)
        ajs__jlpp = ''
        for hrw__aobl, cjcal__bvbx in self.right_vars.items():
            ajs__jlpp += "'{}':{}, ".format(hrw__aobl, cjcal__bvbx.name)
        vfvuz__qlj = '{}{{{}}}'.format(self.right_df, ajs__jlpp)
        return 'join [{}={}]: {} , {}, {}'.format(self.left_keys, self.
            right_keys, vperl__nbn, kpau__sgu, vfvuz__qlj)


def join_array_analysis(join_node, equiv_set, typemap, array_analysis):
    txqq__olmv = []
    assert len(join_node.out_data_vars) > 0, 'empty join in array analysis'
    pahve__ecgmt = []
    rdl__crgrm = list(join_node.left_vars.values())
    for zhcoz__bwhff in rdl__crgrm:
        qxu__ddr = typemap[zhcoz__bwhff.name]
        pxhy__duz = equiv_set.get_shape(zhcoz__bwhff)
        if pxhy__duz:
            pahve__ecgmt.append(pxhy__duz[0])
    if len(pahve__ecgmt) > 1:
        equiv_set.insert_equiv(*pahve__ecgmt)
    pahve__ecgmt = []
    rdl__crgrm = list(join_node.right_vars.values())
    for zhcoz__bwhff in rdl__crgrm:
        qxu__ddr = typemap[zhcoz__bwhff.name]
        pxhy__duz = equiv_set.get_shape(zhcoz__bwhff)
        if pxhy__duz:
            pahve__ecgmt.append(pxhy__duz[0])
    if len(pahve__ecgmt) > 1:
        equiv_set.insert_equiv(*pahve__ecgmt)
    pahve__ecgmt = []
    for zhcoz__bwhff in join_node.out_data_vars.values():
        qxu__ddr = typemap[zhcoz__bwhff.name]
        rmn__grwyc = array_analysis._gen_shape_call(equiv_set, zhcoz__bwhff,
            qxu__ddr.ndim, None, txqq__olmv)
        equiv_set.insert_equiv(zhcoz__bwhff, rmn__grwyc)
        pahve__ecgmt.append(rmn__grwyc[0])
        equiv_set.define(zhcoz__bwhff, set())
    if len(pahve__ecgmt) > 1:
        equiv_set.insert_equiv(*pahve__ecgmt)
    return [], txqq__olmv


numba.parfors.array_analysis.array_analysis_extensions[Join
    ] = join_array_analysis


def join_distributed_analysis(join_node, array_dists):
    oqr__rgd = Distribution.OneD
    mqnq__xoml = Distribution.OneD
    for zhcoz__bwhff in join_node.left_vars.values():
        oqr__rgd = Distribution(min(oqr__rgd.value, array_dists[
            zhcoz__bwhff.name].value))
    for zhcoz__bwhff in join_node.right_vars.values():
        mqnq__xoml = Distribution(min(mqnq__xoml.value, array_dists[
            zhcoz__bwhff.name].value))
    ezbm__chpfu = Distribution.OneD_Var
    for zhcoz__bwhff in join_node.out_data_vars.values():
        if zhcoz__bwhff.name in array_dists:
            ezbm__chpfu = Distribution(min(ezbm__chpfu.value, array_dists[
                zhcoz__bwhff.name].value))
    itq__tevp = Distribution(min(ezbm__chpfu.value, oqr__rgd.value))
    khf__rhhb = Distribution(min(ezbm__chpfu.value, mqnq__xoml.value))
    ezbm__chpfu = Distribution(max(itq__tevp.value, khf__rhhb.value))
    for zhcoz__bwhff in join_node.out_data_vars.values():
        array_dists[zhcoz__bwhff.name] = ezbm__chpfu
    if ezbm__chpfu != Distribution.OneD_Var:
        oqr__rgd = ezbm__chpfu
        mqnq__xoml = ezbm__chpfu
    for zhcoz__bwhff in join_node.left_vars.values():
        array_dists[zhcoz__bwhff.name] = oqr__rgd
    for zhcoz__bwhff in join_node.right_vars.values():
        array_dists[zhcoz__bwhff.name] = mqnq__xoml
    return


distributed_analysis.distributed_analysis_extensions[Join
    ] = join_distributed_analysis


def join_typeinfer(join_node, typeinferer):
    dqyd__zszi = set(join_node.left_keys) & set(join_node.right_keys)
    jaaw__buq = set(join_node.left_vars.keys()) & set(join_node.right_vars.
        keys())
    aaeed__wpa = jaaw__buq - dqyd__zszi
    for ktobi__cpemt, hsgv__zfylw in join_node.out_data_vars.items():
        if join_node.indicator and ktobi__cpemt == '_merge':
            continue
        if not ktobi__cpemt in join_node.column_origins:
            raise BodoError('join(): The variable ' + ktobi__cpemt +
                ' is absent from the output')
        eisdk__fddo = join_node.column_origins[ktobi__cpemt]
        if eisdk__fddo[0] == 'left':
            zhcoz__bwhff = join_node.left_vars[eisdk__fddo[1]]
        else:
            zhcoz__bwhff = join_node.right_vars[eisdk__fddo[1]]
        typeinferer.constraints.append(typeinfer.Propagate(dst=hsgv__zfylw.
            name, src=zhcoz__bwhff.name, loc=join_node.loc))
    return


typeinfer.typeinfer_extensions[Join] = join_typeinfer


def visit_vars_join(join_node, callback, cbdata):
    if debug_prints():
        print('visiting join vars for:', join_node)
        print('cbdata: ', sorted(cbdata.items()))
    for uqi__xbq in list(join_node.left_vars.keys()):
        join_node.left_vars[uqi__xbq] = visit_vars_inner(join_node.
            left_vars[uqi__xbq], callback, cbdata)
    for uqi__xbq in list(join_node.right_vars.keys()):
        join_node.right_vars[uqi__xbq] = visit_vars_inner(join_node.
            right_vars[uqi__xbq], callback, cbdata)
    for uqi__xbq in list(join_node.out_data_vars.keys()):
        join_node.out_data_vars[uqi__xbq] = visit_vars_inner(join_node.
            out_data_vars[uqi__xbq], callback, cbdata)


ir_utils.visit_vars_extensions[Join] = visit_vars_join


def remove_dead_join(join_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    uqbsf__feitr = []
    jun__maell = True
    for uqi__xbq, zhcoz__bwhff in join_node.out_data_vars.items():
        if zhcoz__bwhff.name in lives:
            jun__maell = False
            continue
        if uqi__xbq == '$_bodo_index_':
            continue
        if join_node.indicator and uqi__xbq == '_merge':
            uqbsf__feitr.append('_merge')
            join_node.indicator = False
            continue
        vyfv__tzb, fuwrm__dgvdr = join_node.column_origins[uqi__xbq]
        if (vyfv__tzb == 'left' and fuwrm__dgvdr not in join_node.left_keys and
            fuwrm__dgvdr not in join_node.left_cond_cols):
            join_node.left_vars.pop(fuwrm__dgvdr)
            uqbsf__feitr.append(uqi__xbq)
        if (vyfv__tzb == 'right' and fuwrm__dgvdr not in join_node.
            right_keys and fuwrm__dgvdr not in join_node.right_cond_cols):
            join_node.right_vars.pop(fuwrm__dgvdr)
            uqbsf__feitr.append(uqi__xbq)
    for cname in uqbsf__feitr:
        join_node.out_data_vars.pop(cname)
    if jun__maell:
        return None
    return join_node


ir_utils.remove_dead_extensions[Join] = remove_dead_join


def join_usedefs(join_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({cjcal__bvbx.name for cjcal__bvbx in join_node.left_vars
        .values()})
    use_set.update({cjcal__bvbx.name for cjcal__bvbx in join_node.
        right_vars.values()})
    def_set.update({cjcal__bvbx.name for cjcal__bvbx in join_node.
        out_data_vars.values()})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Join] = join_usedefs


def get_copies_join(join_node, typemap):
    zxuh__jza = set(cjcal__bvbx.name for cjcal__bvbx in join_node.
        out_data_vars.values())
    return set(), zxuh__jza


ir_utils.copy_propagate_extensions[Join] = get_copies_join


def apply_copies_join(join_node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    for uqi__xbq in list(join_node.left_vars.keys()):
        join_node.left_vars[uqi__xbq] = replace_vars_inner(join_node.
            left_vars[uqi__xbq], var_dict)
    for uqi__xbq in list(join_node.right_vars.keys()):
        join_node.right_vars[uqi__xbq] = replace_vars_inner(join_node.
            right_vars[uqi__xbq], var_dict)
    for uqi__xbq in list(join_node.out_data_vars.keys()):
        join_node.out_data_vars[uqi__xbq] = replace_vars_inner(join_node.
            out_data_vars[uqi__xbq], var_dict)
    return


ir_utils.apply_copy_propagate_extensions[Join] = apply_copies_join


def build_join_definitions(join_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for zhcoz__bwhff in join_node.out_data_vars.values():
        definitions[zhcoz__bwhff.name].append(join_node)
    return definitions


ir_utils.build_defs_extensions[Join] = build_join_definitions


def join_distributed_run(join_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    left_parallel, right_parallel = False, False
    if array_dists is not None:
        left_parallel, right_parallel = _get_table_parallel_flags(join_node,
            array_dists)
    n_keys = len(join_node.left_keys)
    ppo__wce = tuple(join_node.left_vars[hrw__aobl] for hrw__aobl in
        join_node.left_keys)
    acut__qktz = tuple(join_node.right_vars[hrw__aobl] for hrw__aobl in
        join_node.right_keys)
    hrtj__zky = tuple(join_node.left_vars.keys())
    wtgz__dooq = tuple(join_node.right_vars.keys())
    bjldy__bjs = ()
    ptakc__bemro = ()
    optional_column = False
    if (join_node.left_index and not join_node.right_index and not
        join_node.is_join):
        bkx__oqils = join_node.right_keys[0]
        if bkx__oqils in hrtj__zky:
            ptakc__bemro = bkx__oqils,
            bjldy__bjs = join_node.right_vars[bkx__oqils],
            optional_column = True
    if (join_node.right_index and not join_node.left_index and not
        join_node.is_join):
        bkx__oqils = join_node.left_keys[0]
        if bkx__oqils in wtgz__dooq:
            ptakc__bemro = bkx__oqils,
            bjldy__bjs = join_node.left_vars[bkx__oqils],
            optional_column = True
    oebo__hbogy = tuple(join_node.out_data_vars[cname] for cname in
        ptakc__bemro)
    xdjfo__hrus = tuple(cjcal__bvbx for vsf__mut, cjcal__bvbx in sorted(
        join_node.left_vars.items(), key=lambda a: str(a[0])) if vsf__mut
         not in join_node.left_keys)
    ziy__wuc = tuple(cjcal__bvbx for vsf__mut, cjcal__bvbx in sorted(
        join_node.right_vars.items(), key=lambda a: str(a[0])) if vsf__mut
         not in join_node.right_keys)
    weti__cfrb = bjldy__bjs + ppo__wce + acut__qktz + xdjfo__hrus + ziy__wuc
    lbxw__gpizl = tuple(typemap[cjcal__bvbx.name] for cjcal__bvbx in weti__cfrb
        )
    jsnqc__qll = tuple('opti_c' + str(fvme__cuas) for fvme__cuas in range(
        len(bjldy__bjs)))
    left_other_names = tuple('t1_c' + str(fvme__cuas) for fvme__cuas in
        range(len(xdjfo__hrus)))
    right_other_names = tuple('t2_c' + str(fvme__cuas) for fvme__cuas in
        range(len(ziy__wuc)))
    left_other_types = tuple([typemap[hrw__aobl.name] for hrw__aobl in
        xdjfo__hrus])
    right_other_types = tuple([typemap[hrw__aobl.name] for hrw__aobl in
        ziy__wuc])
    left_key_names = tuple('t1_key' + str(fvme__cuas) for fvme__cuas in
        range(n_keys))
    right_key_names = tuple('t2_key' + str(fvme__cuas) for fvme__cuas in
        range(n_keys))
    glbs = {}
    loc = join_node.loc
    func_text = 'def f({}{}, {},{}{}{}):\n'.format('{},'.format(jsnqc__qll[
        0]) if len(jsnqc__qll) == 1 else '', ','.join(left_key_names), ','.
        join(right_key_names), ','.join(left_other_names), ',' if len(
        left_other_names) != 0 else '', ','.join(right_other_names))
    left_key_types = tuple(typemap[cjcal__bvbx.name] for cjcal__bvbx in
        ppo__wce)
    right_key_types = tuple(typemap[cjcal__bvbx.name] for cjcal__bvbx in
        acut__qktz)
    for fvme__cuas in range(n_keys):
        glbs[f'key_type_{fvme__cuas}'] = _match_join_key_types(left_key_types
            [fvme__cuas], right_key_types[fvme__cuas], loc)
    func_text += '    t1_keys = ({},)\n'.format(', '.join(
        f'bodo.utils.utils.astype({left_key_names[fvme__cuas]}, key_type_{fvme__cuas})'
         for fvme__cuas in range(n_keys)))
    func_text += '    t2_keys = ({},)\n'.format(', '.join(
        f'bodo.utils.utils.astype({right_key_names[fvme__cuas]}, key_type_{fvme__cuas})'
         for fvme__cuas in range(n_keys)))
    func_text += '    data_left = ({}{})\n'.format(','.join(
        left_other_names), ',' if len(left_other_names) != 0 else '')
    func_text += '    data_right = ({}{})\n'.format(','.join(
        right_other_names), ',' if len(right_other_names) != 0 else '')
    eoq__wmfn = []
    for cname in join_node.left_keys:
        if cname in join_node.add_suffix:
            kaxtt__znhip = str(cname) + join_node.suffix_x
        else:
            kaxtt__znhip = cname
        assert kaxtt__znhip in join_node.out_data_vars
        eoq__wmfn.append(join_node.out_data_vars[kaxtt__znhip])
    for fvme__cuas, cname in enumerate(join_node.right_keys):
        if not join_node.vect_same_key[fvme__cuas] and not join_node.is_join:
            if cname in join_node.add_suffix:
                kaxtt__znhip = str(cname) + join_node.suffix_y
            else:
                kaxtt__znhip = cname
            assert kaxtt__znhip in join_node.out_data_vars
            eoq__wmfn.append(join_node.out_data_vars[kaxtt__znhip])

    def _get_out_col_var(cname, is_left):
        if cname in join_node.add_suffix:
            if is_left:
                kaxtt__znhip = str(cname) + join_node.suffix_x
            else:
                kaxtt__znhip = str(cname) + join_node.suffix_y
        else:
            kaxtt__znhip = cname
        return join_node.out_data_vars[kaxtt__znhip]
    qev__bmkx = oebo__hbogy + tuple(eoq__wmfn)
    qev__bmkx += tuple(_get_out_col_var(vsf__mut, True) for vsf__mut,
        cjcal__bvbx in sorted(join_node.left_vars.items(), key=lambda a:
        str(a[0])) if vsf__mut not in join_node.left_keys)
    qev__bmkx += tuple(_get_out_col_var(vsf__mut, False) for vsf__mut,
        cjcal__bvbx in sorted(join_node.right_vars.items(), key=lambda a:
        str(a[0])) if vsf__mut not in join_node.right_keys)
    if join_node.indicator:
        qev__bmkx += _get_out_col_var('_merge', False),
    gcfny__por = [('t3_c' + str(fvme__cuas)) for fvme__cuas in range(len(
        qev__bmkx))]
    general_cond_cfunc, left_col_nums, right_col_nums = (
        _gen_general_cond_cfunc(join_node, typemap))
    if join_node.how == 'asof':
        if left_parallel or right_parallel:
            assert left_parallel and right_parallel
            func_text += """    t2_keys, data_right = parallel_asof_comm(t1_keys, t2_keys, data_right)
"""
        func_text += """    out_t1_keys, out_t2_keys, out_data_left, out_data_right = bodo.ir.join.local_merge_asof(t1_keys, t2_keys, data_left, data_right)
"""
    else:
        func_text += _gen_local_hash_join(optional_column, left_key_names,
            right_key_names, left_key_types, right_key_types,
            left_other_names, right_other_names, left_other_types,
            right_other_types, join_node.vect_same_key, join_node.is_left,
            join_node.is_right, join_node.is_join, left_parallel,
            right_parallel, glbs, [typemap[cjcal__bvbx.name] for
            cjcal__bvbx in qev__bmkx], join_node.loc, join_node.indicator,
            join_node.is_na_equal, general_cond_cfunc, left_col_nums,
            right_col_nums)
    if join_node.how == 'asof':
        for fvme__cuas in range(len(left_other_names)):
            func_text += '    left_{} = out_data_left[{}]\n'.format(fvme__cuas,
                fvme__cuas)
        for fvme__cuas in range(len(right_other_names)):
            func_text += '    right_{} = out_data_right[{}]\n'.format(
                fvme__cuas, fvme__cuas)
        for fvme__cuas in range(n_keys):
            func_text += (
                f'    t1_keys_{fvme__cuas} = out_t1_keys[{fvme__cuas}]\n')
        for fvme__cuas in range(n_keys):
            func_text += (
                f'    t2_keys_{fvme__cuas} = out_t2_keys[{fvme__cuas}]\n')
    idx = 0
    if optional_column:
        func_text += f'    {gcfny__por[idx]} = opti_0\n'
        idx += 1
    for fvme__cuas in range(n_keys):
        func_text += f'    {gcfny__por[idx]} = t1_keys_{fvme__cuas}\n'
        idx += 1
    for fvme__cuas in range(n_keys):
        if not join_node.vect_same_key[fvme__cuas] and not join_node.is_join:
            func_text += f'    {gcfny__por[idx]} = t2_keys_{fvme__cuas}\n'
            idx += 1
    for fvme__cuas in range(len(left_other_names)):
        func_text += f'    {gcfny__por[idx]} = left_{fvme__cuas}\n'
        idx += 1
    for fvme__cuas in range(len(right_other_names)):
        func_text += f'    {gcfny__por[idx]} = right_{fvme__cuas}\n'
        idx += 1
    if join_node.indicator:
        func_text += f'    {gcfny__por[idx]} = indicator_col\n'
        idx += 1
    cjf__wbd = {}
    exec(func_text, {}, cjf__wbd)
    nfea__jfus = cjf__wbd['f']
    glbs.update({'bodo': bodo, 'np': np, 'pd': pd,
        'to_list_if_immutable_arr': to_list_if_immutable_arr,
        'cp_str_list_to_array': cp_str_list_to_array, 'parallel_asof_comm':
        parallel_asof_comm, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'hash_join_table':
        hash_join_table, 'info_from_table': info_from_table,
        'info_to_array': info_to_array, 'delete_table': delete_table,
        'delete_table_decref_arrays': delete_table_decref_arrays,
        'add_join_gen_cond_cfunc_sym': add_join_gen_cond_cfunc_sym,
        'get_join_cond_addr': get_join_cond_addr})
    if general_cond_cfunc:
        glbs.update({'general_cond_cfunc': general_cond_cfunc})
    lsjw__ndr = compile_to_numba_ir(nfea__jfus, glbs, typingctx=typingctx,
        targetctx=targetctx, arg_typs=lbxw__gpizl, typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(lsjw__ndr, weti__cfrb)
    sxqa__ars = lsjw__ndr.body[:-3]
    for fvme__cuas in range(len(qev__bmkx)):
        sxqa__ars[-len(qev__bmkx) + fvme__cuas].target = qev__bmkx[fvme__cuas]
    return sxqa__ars


distributed_pass.distributed_run_extensions[Join] = join_distributed_run


def _gen_general_cond_cfunc(join_node, typemap):
    expr = join_node.gen_cond_expr
    if not expr:
        return None, [], []
    kphmp__hzc = next_label()
    klf__glq = _get_col_to_ind(join_node.left_keys, join_node.left_vars)
    biigj__kucg = _get_col_to_ind(join_node.right_keys, join_node.right_vars)
    table_getitem_funcs = {'bodo': bodo, 'numba': numba, 'is_null_pointer':
        is_null_pointer}
    na_check_name = 'NOT_NA'
    func_text = f"""def bodo_join_gen_cond{kphmp__hzc}(left_table, right_table, left_data1, right_data1, left_null_bitmap, right_null_bitmap, left_ind, right_ind):
"""
    func_text += '  if is_null_pointer(left_table):\n'
    func_text += '    return False\n'
    expr, func_text, left_col_nums = _replace_column_accesses(expr,
        klf__glq, typemap, join_node.left_vars, table_getitem_funcs,
        func_text, 'left', len(join_node.left_keys), na_check_name)
    expr, func_text, right_col_nums = _replace_column_accesses(expr,
        biigj__kucg, typemap, join_node.right_vars, table_getitem_funcs,
        func_text, 'right', len(join_node.right_keys), na_check_name)
    func_text += f'  return {expr}'
    cjf__wbd = {}
    exec(func_text, table_getitem_funcs, cjf__wbd)
    lvr__xejcp = cjf__wbd[f'bodo_join_gen_cond{kphmp__hzc}']
    yiv__bmzi = types.bool_(types.voidptr, types.voidptr, types.voidptr,
        types.voidptr, types.voidptr, types.voidptr, types.int64, types.int64)
    yvn__txt = numba.cfunc(yiv__bmzi, nopython=True)(lvr__xejcp)
    join_gen_cond_cfunc[yvn__txt.native_name] = yvn__txt
    join_gen_cond_cfunc_addr[yvn__txt.native_name] = yvn__txt.address
    return yvn__txt, left_col_nums, right_col_nums


def _replace_column_accesses(expr, col_to_ind, typemap, col_vars,
    table_getitem_funcs, func_text, table_name, n_keys, na_check_name):
    cbpy__zoks = []
    for hrw__aobl, omfxa__jrvp in col_to_ind.items():
        cname = f'({table_name}.{hrw__aobl})'
        if cname not in expr:
            continue
        aof__hozr = f'getitem_{table_name}_val_{omfxa__jrvp}'
        bwbtm__txoj = f'_bodo_{table_name}_val_{omfxa__jrvp}'
        yosi__kif = typemap[col_vars[hrw__aobl].name]
        if is_str_arr_type(yosi__kif):
            func_text += f"""  {bwbtm__txoj}, {bwbtm__txoj}_size = {aof__hozr}({table_name}_table, {table_name}_ind)
"""
            func_text += f"""  {bwbtm__txoj} = bodo.libs.str_arr_ext.decode_utf8({bwbtm__txoj}, {bwbtm__txoj}_size)
"""
        else:
            func_text += (
                f'  {bwbtm__txoj} = {aof__hozr}({table_name}_data1, {table_name}_ind)\n'
                )
        table_getitem_funcs[aof__hozr
            ] = bodo.libs.array._gen_row_access_intrinsic(yosi__kif,
            omfxa__jrvp)
        expr = expr.replace(cname, bwbtm__txoj)
        xhz__nfvmf = f'({na_check_name}.{table_name}.{hrw__aobl})'
        if xhz__nfvmf in expr:
            dnik__fydp = f'nacheck_{table_name}_val_{omfxa__jrvp}'
            rcgy__pwgc = f'_bodo_isna_{table_name}_val_{omfxa__jrvp}'
            if (isinstance(yosi__kif, bodo.libs.int_arr_ext.
                IntegerArrayType) or yosi__kif == bodo.libs.bool_arr_ext.
                boolean_array or is_str_arr_type(yosi__kif)):
                func_text += f"""  {rcgy__pwgc} = {dnik__fydp}({table_name}_null_bitmap, {table_name}_ind)
"""
            else:
                func_text += f"""  {rcgy__pwgc} = {dnik__fydp}({table_name}_data1, {table_name}_ind)
"""
            table_getitem_funcs[dnik__fydp
                ] = bodo.libs.array._gen_row_na_check_intrinsic(yosi__kif,
                omfxa__jrvp)
            expr = expr.replace(xhz__nfvmf, rcgy__pwgc)
        if omfxa__jrvp >= n_keys:
            cbpy__zoks.append(omfxa__jrvp)
    return expr, func_text, cbpy__zoks


def _get_col_to_ind(key_names, col_vars):
    n_keys = len(key_names)
    col_to_ind = {hrw__aobl: fvme__cuas for fvme__cuas, hrw__aobl in
        enumerate(key_names)}
    fvme__cuas = n_keys
    for hrw__aobl in sorted(col_vars, key=lambda a: str(a)):
        if hrw__aobl in key_names:
            continue
        col_to_ind[hrw__aobl] = fvme__cuas
        fvme__cuas += 1
    return col_to_ind


def _match_join_key_types(t1, t2, loc):
    if t1 == t2:
        return t1
    try:
        arr = dtype_to_array_type(find_common_np_dtype([t1, t2]))
        return to_nullable_type(arr) if is_nullable_type(t1
            ) or is_nullable_type(t2) else arr
    except Exception as vzmu__ngftr:
        if is_str_arr_type(t1) and is_str_arr_type(t2):
            return bodo.string_array_type
        raise BodoError(f'Join key types {t1} and {t2} do not match', loc=loc)


def _get_table_parallel_flags(join_node, array_dists):
    yovp__shezm = (distributed_pass.Distribution.OneD, distributed_pass.
        Distribution.OneD_Var)
    left_parallel = all(array_dists[cjcal__bvbx.name] in yovp__shezm for
        cjcal__bvbx in join_node.left_vars.values())
    right_parallel = all(array_dists[cjcal__bvbx.name] in yovp__shezm for
        cjcal__bvbx in join_node.right_vars.values())
    if not left_parallel:
        assert not any(array_dists[cjcal__bvbx.name] in yovp__shezm for
            cjcal__bvbx in join_node.left_vars.values())
    if not right_parallel:
        assert not any(array_dists[cjcal__bvbx.name] in yovp__shezm for
            cjcal__bvbx in join_node.right_vars.values())
    if left_parallel or right_parallel:
        assert all(array_dists[cjcal__bvbx.name] in yovp__shezm for
            cjcal__bvbx in join_node.out_data_vars.values())
    return left_parallel, right_parallel


def _gen_local_hash_join(optional_column, left_key_names, right_key_names,
    left_key_types, right_key_types, left_other_names, right_other_names,
    left_other_types, right_other_types, vect_same_key, is_left, is_right,
    is_join, left_parallel, right_parallel, glbs, out_types, loc, indicator,
    is_na_equal, general_cond_cfunc, left_col_nums, right_col_nums):

    def needs_typechange(in_type, need_nullable, is_same_key):
        return isinstance(in_type, types.Array) and not is_dtype_nullable(
            in_type.dtype) and need_nullable and not is_same_key
    efr__muygi = []
    for fvme__cuas in range(len(left_key_names)):
        cmurj__stcvq = _match_join_key_types(left_key_types[fvme__cuas],
            right_key_types[fvme__cuas], loc)
        efr__muygi.append(needs_typechange(cmurj__stcvq, is_right,
            vect_same_key[fvme__cuas]))
    for fvme__cuas in range(len(left_other_names)):
        efr__muygi.append(needs_typechange(left_other_types[fvme__cuas],
            is_right, False))
    for fvme__cuas in range(len(right_key_names)):
        if not vect_same_key[fvme__cuas] and not is_join:
            cmurj__stcvq = _match_join_key_types(left_key_types[fvme__cuas],
                right_key_types[fvme__cuas], loc)
            efr__muygi.append(needs_typechange(cmurj__stcvq, is_left, False))
    for fvme__cuas in range(len(right_other_names)):
        efr__muygi.append(needs_typechange(right_other_types[fvme__cuas],
            is_left, False))

    def get_out_type(idx, in_type, in_name, need_nullable, is_same_key):
        if isinstance(in_type, types.Array) and not is_dtype_nullable(in_type
            .dtype) and need_nullable and not is_same_key:
            if isinstance(in_type.dtype, types.Integer):
                yklje__llnbb = IntDtype(in_type.dtype).name
                assert yklje__llnbb.endswith('Dtype()')
                yklje__llnbb = yklje__llnbb[:-7]
                lmzwp__wogo = f"""    typ_{idx} = bodo.hiframes.pd_series_ext.get_series_data(pd.Series([1], dtype="{yklje__llnbb}"))
"""
                xnpme__nyxn = f'typ_{idx}'
            else:
                assert in_type.dtype == types.bool_, 'unexpected non-nullable type in join'
                lmzwp__wogo = (
                    f'    typ_{idx} = bodo.libs.bool_arr_ext.alloc_bool_array(1)\n'
                    )
                xnpme__nyxn = f'typ_{idx}'
        elif in_type == bodo.string_array_type:
            lmzwp__wogo = (
                f'    typ_{idx} = bodo.libs.str_arr_ext.pre_alloc_string_array(0, 0)\n'
                )
            xnpme__nyxn = f'typ_{idx}'
        else:
            lmzwp__wogo = ''
            xnpme__nyxn = in_name
        return lmzwp__wogo, xnpme__nyxn
    n_keys = len(left_key_names)
    func_text = '    # beginning of _gen_local_hash_join\n'
    baw__rkd = []
    for fvme__cuas in range(n_keys):
        baw__rkd.append('t1_keys[{}]'.format(fvme__cuas))
    for fvme__cuas in range(len(left_other_names)):
        baw__rkd.append('data_left[{}]'.format(fvme__cuas))
    func_text += '    info_list_total_l = [{}]\n'.format(','.join(
        'array_to_info({})'.format(a) for a in baw__rkd))
    func_text += '    table_left = arr_info_list_to_table(info_list_total_l)\n'
    eolx__orm = []
    for fvme__cuas in range(n_keys):
        eolx__orm.append('t2_keys[{}]'.format(fvme__cuas))
    for fvme__cuas in range(len(right_other_names)):
        eolx__orm.append('data_right[{}]'.format(fvme__cuas))
    func_text += '    info_list_total_r = [{}]\n'.format(','.join(
        'array_to_info({})'.format(a) for a in eolx__orm))
    func_text += (
        '    table_right = arr_info_list_to_table(info_list_total_r)\n')
    func_text += '    vect_same_key = np.array([{}])\n'.format(','.join('1' if
        blqvq__xfux else '0' for blqvq__xfux in vect_same_key))
    func_text += '    vect_need_typechange = np.array([{}])\n'.format(','.
        join('1' if blqvq__xfux else '0' for blqvq__xfux in efr__muygi))
    func_text += f"""    left_table_cond_columns = np.array({left_col_nums if len(left_col_nums) > 0 else [-1]}, dtype=np.int64)
"""
    func_text += f"""    right_table_cond_columns = np.array({right_col_nums if len(right_col_nums) > 0 else [-1]}, dtype=np.int64)
"""
    if general_cond_cfunc:
        func_text += f"""    cfunc_cond = add_join_gen_cond_cfunc_sym(general_cond_cfunc, '{general_cond_cfunc.native_name}')
"""
        func_text += (
            f"    cfunc_cond = get_join_cond_addr('{general_cond_cfunc.native_name}')\n"
            )
    else:
        func_text += '    cfunc_cond = 0\n'
    func_text += (
        """    out_table = hash_join_table(table_left, table_right, {}, {}, {}, {}, {}, vect_same_key.ctypes, vect_need_typechange.ctypes, {}, {}, {}, {}, {}, {}, cfunc_cond, left_table_cond_columns.ctypes, {}, right_table_cond_columns.ctypes, {})
"""
        .format(left_parallel, right_parallel, n_keys, len(left_other_names
        ), len(right_other_names), is_left, is_right, is_join,
        optional_column, indicator, is_na_equal, len(left_col_nums), len(
        right_col_nums)))
    func_text += '    delete_table(table_left)\n'
    func_text += '    delete_table(table_right)\n'
    idx = 0
    if optional_column:
        gveym__tws = get_out_type(idx, out_types[idx], 'opti_c0', False, False)
        func_text += gveym__tws[0]
        glbs[f'out_type_{idx}'] = out_types[idx]
        func_text += f"""    opti_0 = info_to_array(info_from_table(out_table, {idx}), {gveym__tws[1]})
"""
        idx += 1
    for fvme__cuas, vao__xnxrv in enumerate(left_key_names):
        cmurj__stcvq = _match_join_key_types(left_key_types[fvme__cuas],
            right_key_types[fvme__cuas], loc)
        gveym__tws = get_out_type(idx, cmurj__stcvq,
            f't1_keys[{fvme__cuas}]', is_right, vect_same_key[fvme__cuas])
        func_text += gveym__tws[0]
        glbs[f'out_type_{idx}'] = out_types[idx]
        if cmurj__stcvq != left_key_types[fvme__cuas] and left_key_types[
            fvme__cuas] != bodo.dict_str_arr_type:
            func_text += f"""    t1_keys_{fvme__cuas} = bodo.utils.utils.astype(info_to_array(info_from_table(out_table, {idx}), {gveym__tws[1]}), out_type_{idx})
"""
        else:
            func_text += f"""    t1_keys_{fvme__cuas} = info_to_array(info_from_table(out_table, {idx}), {gveym__tws[1]})
"""
        idx += 1
    for fvme__cuas, vao__xnxrv in enumerate(left_other_names):
        gveym__tws = get_out_type(idx, left_other_types[fvme__cuas],
            vao__xnxrv, is_right, False)
        func_text += gveym__tws[0]
        func_text += (
            '    left_{} = info_to_array(info_from_table(out_table, {}), {})\n'
            .format(fvme__cuas, idx, gveym__tws[1]))
        idx += 1
    for fvme__cuas, vao__xnxrv in enumerate(right_key_names):
        if not vect_same_key[fvme__cuas] and not is_join:
            cmurj__stcvq = _match_join_key_types(left_key_types[fvme__cuas],
                right_key_types[fvme__cuas], loc)
            gveym__tws = get_out_type(idx, cmurj__stcvq,
                f't2_keys[{fvme__cuas}]', is_left, False)
            func_text += gveym__tws[0]
            glbs[f'out_type_{idx}'] = out_types[idx - len(left_other_names)]
            if cmurj__stcvq != right_key_types[fvme__cuas] and right_key_types[
                fvme__cuas] != bodo.dict_str_arr_type:
                func_text += f"""    t2_keys_{fvme__cuas} = bodo.utils.utils.astype(info_to_array(info_from_table(out_table, {idx}), {gveym__tws[1]}), out_type_{idx})
"""
            else:
                func_text += f"""    t2_keys_{fvme__cuas} = info_to_array(info_from_table(out_table, {idx}), {gveym__tws[1]})
"""
            idx += 1
    for fvme__cuas, vao__xnxrv in enumerate(right_other_names):
        gveym__tws = get_out_type(idx, right_other_types[fvme__cuas],
            vao__xnxrv, is_left, False)
        func_text += gveym__tws[0]
        func_text += (
            '    right_{} = info_to_array(info_from_table(out_table, {}), {})\n'
            .format(fvme__cuas, idx, gveym__tws[1]))
        idx += 1
    if indicator:
        func_text += f"""    typ_{idx} = pd.Categorical(values=['both'], categories=('left_only', 'right_only', 'both'))
"""
        func_text += f"""    indicator_col = info_to_array(info_from_table(out_table, {idx}), typ_{idx})
"""
        idx += 1
    func_text += '    delete_table(out_table)\n'
    return func_text


@numba.njit
def parallel_asof_comm(left_key_arrs, right_key_arrs, right_data):
    uglrt__supj = bodo.libs.distributed_api.get_size()
    wxp__vvdc = np.empty(uglrt__supj, left_key_arrs[0].dtype)
    pcun__treos = np.empty(uglrt__supj, left_key_arrs[0].dtype)
    bodo.libs.distributed_api.allgather(wxp__vvdc, left_key_arrs[0][0])
    bodo.libs.distributed_api.allgather(pcun__treos, left_key_arrs[0][-1])
    arsee__cfgwh = np.zeros(uglrt__supj, np.int32)
    int__ahc = np.zeros(uglrt__supj, np.int32)
    ejihd__tmlom = np.zeros(uglrt__supj, np.int32)
    mfppr__okj = right_key_arrs[0][0]
    rwav__ksjtv = right_key_arrs[0][-1]
    wegr__hvkuk = -1
    fvme__cuas = 0
    while fvme__cuas < uglrt__supj - 1 and pcun__treos[fvme__cuas
        ] < mfppr__okj:
        fvme__cuas += 1
    while fvme__cuas < uglrt__supj and wxp__vvdc[fvme__cuas] <= rwav__ksjtv:
        wegr__hvkuk, enh__pbk = _count_overlap(right_key_arrs[0], wxp__vvdc
            [fvme__cuas], pcun__treos[fvme__cuas])
        if wegr__hvkuk != 0:
            wegr__hvkuk -= 1
            enh__pbk += 1
        arsee__cfgwh[fvme__cuas] = enh__pbk
        int__ahc[fvme__cuas] = wegr__hvkuk
        fvme__cuas += 1
    while fvme__cuas < uglrt__supj:
        arsee__cfgwh[fvme__cuas] = 1
        int__ahc[fvme__cuas] = len(right_key_arrs[0]) - 1
        fvme__cuas += 1
    bodo.libs.distributed_api.alltoall(arsee__cfgwh, ejihd__tmlom, 1)
    ciam__aho = ejihd__tmlom.sum()
    fbko__lmoeg = np.empty(ciam__aho, right_key_arrs[0].dtype)
    xubj__atjwq = alloc_arr_tup(ciam__aho, right_data)
    bef__xgorr = bodo.ir.join.calc_disp(ejihd__tmlom)
    bodo.libs.distributed_api.alltoallv(right_key_arrs[0], fbko__lmoeg,
        arsee__cfgwh, ejihd__tmlom, int__ahc, bef__xgorr)
    bodo.libs.distributed_api.alltoallv_tup(right_data, xubj__atjwq,
        arsee__cfgwh, ejihd__tmlom, int__ahc, bef__xgorr)
    return (fbko__lmoeg,), xubj__atjwq


@numba.njit
def _count_overlap(r_key_arr, start, end):
    enh__pbk = 0
    wegr__hvkuk = 0
    orij__uvk = 0
    while orij__uvk < len(r_key_arr) and r_key_arr[orij__uvk] < start:
        wegr__hvkuk += 1
        orij__uvk += 1
    while orij__uvk < len(r_key_arr) and start <= r_key_arr[orij__uvk] <= end:
        orij__uvk += 1
        enh__pbk += 1
    return wegr__hvkuk, enh__pbk


import llvmlite.binding as ll
from bodo.libs import hdist
ll.add_symbol('c_alltoallv', hdist.c_alltoallv)


@numba.njit
def calc_disp(arr):
    cmomz__kskj = np.empty_like(arr)
    cmomz__kskj[0] = 0
    for fvme__cuas in range(1, len(arr)):
        cmomz__kskj[fvme__cuas] = cmomz__kskj[fvme__cuas - 1] + arr[
            fvme__cuas - 1]
    return cmomz__kskj


@numba.njit
def local_merge_asof(left_keys, right_keys, data_left, data_right):
    dflg__ewtl = len(left_keys[0])
    ypju__kzv = len(right_keys[0])
    rps__mnqx = alloc_arr_tup(dflg__ewtl, left_keys)
    uppw__cjyvp = alloc_arr_tup(dflg__ewtl, right_keys)
    zvl__qzp = alloc_arr_tup(dflg__ewtl, data_left)
    wgpe__agtl = alloc_arr_tup(dflg__ewtl, data_right)
    ykz__nnprc = 0
    mfbqh__gnfi = 0
    for ykz__nnprc in range(dflg__ewtl):
        if mfbqh__gnfi < 0:
            mfbqh__gnfi = 0
        while mfbqh__gnfi < ypju__kzv and getitem_arr_tup(right_keys,
            mfbqh__gnfi) <= getitem_arr_tup(left_keys, ykz__nnprc):
            mfbqh__gnfi += 1
        mfbqh__gnfi -= 1
        setitem_arr_tup(rps__mnqx, ykz__nnprc, getitem_arr_tup(left_keys,
            ykz__nnprc))
        setitem_arr_tup(zvl__qzp, ykz__nnprc, getitem_arr_tup(data_left,
            ykz__nnprc))
        if mfbqh__gnfi >= 0:
            setitem_arr_tup(uppw__cjyvp, ykz__nnprc, getitem_arr_tup(
                right_keys, mfbqh__gnfi))
            setitem_arr_tup(wgpe__agtl, ykz__nnprc, getitem_arr_tup(
                data_right, mfbqh__gnfi))
        else:
            bodo.libs.array_kernels.setna_tup(uppw__cjyvp, ykz__nnprc)
            bodo.libs.array_kernels.setna_tup(wgpe__agtl, ykz__nnprc)
    return rps__mnqx, uppw__cjyvp, zvl__qzp, wgpe__agtl


def copy_arr_tup(arrs):
    return tuple(a.copy() for a in arrs)


@overload(copy_arr_tup, no_unliteral=True)
def copy_arr_tup_overload(arrs):
    enh__pbk = arrs.count
    func_text = 'def f(arrs):\n'
    func_text += '  return ({},)\n'.format(','.join('arrs[{}].copy()'.
        format(fvme__cuas) for fvme__cuas in range(enh__pbk)))
    cjf__wbd = {}
    exec(func_text, {}, cjf__wbd)
    zjlxp__cqc = cjf__wbd['f']
    return zjlxp__cqc
