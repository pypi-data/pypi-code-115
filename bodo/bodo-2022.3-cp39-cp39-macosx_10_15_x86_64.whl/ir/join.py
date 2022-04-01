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
        aeku__swpjw = func.signature
        jpqy__eviy = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64), lir
            .IntType(64)])
        xmd__rzx = cgutils.get_or_insert_function(builder.module,
            jpqy__eviy, sym._literal_value)
        builder.call(xmd__rzx, [context.get_constant_null(aeku__swpjw.args[
            0]), context.get_constant_null(aeku__swpjw.args[1]), context.
            get_constant_null(aeku__swpjw.args[2]), context.
            get_constant_null(aeku__swpjw.args[3]), context.
            get_constant_null(aeku__swpjw.args[4]), context.
            get_constant_null(aeku__swpjw.args[5]), context.get_constant(
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
        self.left_cond_cols = set(pdxy__nkfqe for pdxy__nkfqe in left_vars.
            keys() if f'(left.{pdxy__nkfqe})' in gen_cond_expr)
        self.right_cond_cols = set(pdxy__nkfqe for pdxy__nkfqe in
            right_vars.keys() if f'(right.{pdxy__nkfqe})' in gen_cond_expr)
        qkg__zmd = set(left_keys) & set(right_keys)
        yxra__xpwb = set(left_vars.keys()) & set(right_vars.keys())
        hxm__ozayy = yxra__xpwb - qkg__zmd
        vect_same_key = []
        n_keys = len(left_keys)
        for wana__gwh in range(n_keys):
            pys__gcapd = left_keys[wana__gwh]
            fce__bfte = right_keys[wana__gwh]
            vect_same_key.append(pys__gcapd == fce__bfte)
        self.vect_same_key = vect_same_key
        self.column_origins = {(str(pdxy__nkfqe) + suffix_x if pdxy__nkfqe in
            hxm__ozayy else pdxy__nkfqe): ('left', pdxy__nkfqe) for
            pdxy__nkfqe in left_vars.keys()}
        self.column_origins.update({(str(pdxy__nkfqe) + suffix_y if 
            pdxy__nkfqe in hxm__ozayy else pdxy__nkfqe): ('right',
            pdxy__nkfqe) for pdxy__nkfqe in right_vars.keys()})
        if '$_bodo_index_' in hxm__ozayy:
            hxm__ozayy.remove('$_bodo_index_')
        self.add_suffix = hxm__ozayy

    def __repr__(self):
        jckny__ntqc = ''
        for pdxy__nkfqe, aug__crg in self.out_data_vars.items():
            jckny__ntqc += "'{}':{}, ".format(pdxy__nkfqe, aug__crg.name)
        yslr__rer = '{}{{{}}}'.format(self.df_out, jckny__ntqc)
        frpr__lbvs = ''
        for pdxy__nkfqe, aug__crg in self.left_vars.items():
            frpr__lbvs += "'{}':{}, ".format(pdxy__nkfqe, aug__crg.name)
        hnww__btpy = '{}{{{}}}'.format(self.left_df, frpr__lbvs)
        frpr__lbvs = ''
        for pdxy__nkfqe, aug__crg in self.right_vars.items():
            frpr__lbvs += "'{}':{}, ".format(pdxy__nkfqe, aug__crg.name)
        jzx__ese = '{}{{{}}}'.format(self.right_df, frpr__lbvs)
        return 'join [{}={}]: {} , {}, {}'.format(self.left_keys, self.
            right_keys, yslr__rer, hnww__btpy, jzx__ese)


def join_array_analysis(join_node, equiv_set, typemap, array_analysis):
    awqv__jaltd = []
    assert len(join_node.out_data_vars) > 0, 'empty join in array analysis'
    gwhau__vvpj = []
    ppsza__tox = list(join_node.left_vars.values())
    for rxqph__cihm in ppsza__tox:
        shtn__pha = typemap[rxqph__cihm.name]
        hlz__zozgh = equiv_set.get_shape(rxqph__cihm)
        if hlz__zozgh:
            gwhau__vvpj.append(hlz__zozgh[0])
    if len(gwhau__vvpj) > 1:
        equiv_set.insert_equiv(*gwhau__vvpj)
    gwhau__vvpj = []
    ppsza__tox = list(join_node.right_vars.values())
    for rxqph__cihm in ppsza__tox:
        shtn__pha = typemap[rxqph__cihm.name]
        hlz__zozgh = equiv_set.get_shape(rxqph__cihm)
        if hlz__zozgh:
            gwhau__vvpj.append(hlz__zozgh[0])
    if len(gwhau__vvpj) > 1:
        equiv_set.insert_equiv(*gwhau__vvpj)
    gwhau__vvpj = []
    for rxqph__cihm in join_node.out_data_vars.values():
        shtn__pha = typemap[rxqph__cihm.name]
        ybbki__lyjsb = array_analysis._gen_shape_call(equiv_set,
            rxqph__cihm, shtn__pha.ndim, None, awqv__jaltd)
        equiv_set.insert_equiv(rxqph__cihm, ybbki__lyjsb)
        gwhau__vvpj.append(ybbki__lyjsb[0])
        equiv_set.define(rxqph__cihm, set())
    if len(gwhau__vvpj) > 1:
        equiv_set.insert_equiv(*gwhau__vvpj)
    return [], awqv__jaltd


numba.parfors.array_analysis.array_analysis_extensions[Join
    ] = join_array_analysis


def join_distributed_analysis(join_node, array_dists):
    ovq__lzgmz = Distribution.OneD
    xpptu__dlgu = Distribution.OneD
    for rxqph__cihm in join_node.left_vars.values():
        ovq__lzgmz = Distribution(min(ovq__lzgmz.value, array_dists[
            rxqph__cihm.name].value))
    for rxqph__cihm in join_node.right_vars.values():
        xpptu__dlgu = Distribution(min(xpptu__dlgu.value, array_dists[
            rxqph__cihm.name].value))
    xlj__rrvwu = Distribution.OneD_Var
    for rxqph__cihm in join_node.out_data_vars.values():
        if rxqph__cihm.name in array_dists:
            xlj__rrvwu = Distribution(min(xlj__rrvwu.value, array_dists[
                rxqph__cihm.name].value))
    tdkxf__frb = Distribution(min(xlj__rrvwu.value, ovq__lzgmz.value))
    ukog__aqzn = Distribution(min(xlj__rrvwu.value, xpptu__dlgu.value))
    xlj__rrvwu = Distribution(max(tdkxf__frb.value, ukog__aqzn.value))
    for rxqph__cihm in join_node.out_data_vars.values():
        array_dists[rxqph__cihm.name] = xlj__rrvwu
    if xlj__rrvwu != Distribution.OneD_Var:
        ovq__lzgmz = xlj__rrvwu
        xpptu__dlgu = xlj__rrvwu
    for rxqph__cihm in join_node.left_vars.values():
        array_dists[rxqph__cihm.name] = ovq__lzgmz
    for rxqph__cihm in join_node.right_vars.values():
        array_dists[rxqph__cihm.name] = xpptu__dlgu
    return


distributed_analysis.distributed_analysis_extensions[Join
    ] = join_distributed_analysis


def join_typeinfer(join_node, typeinferer):
    qkg__zmd = set(join_node.left_keys) & set(join_node.right_keys)
    yxra__xpwb = set(join_node.left_vars.keys()) & set(join_node.right_vars
        .keys())
    hxm__ozayy = yxra__xpwb - qkg__zmd
    for unt__tajo, ygbpl__nok in join_node.out_data_vars.items():
        if join_node.indicator and unt__tajo == '_merge':
            continue
        if not unt__tajo in join_node.column_origins:
            raise BodoError('join(): The variable ' + unt__tajo +
                ' is absent from the output')
        fon__jjwqk = join_node.column_origins[unt__tajo]
        if fon__jjwqk[0] == 'left':
            rxqph__cihm = join_node.left_vars[fon__jjwqk[1]]
        else:
            rxqph__cihm = join_node.right_vars[fon__jjwqk[1]]
        typeinferer.constraints.append(typeinfer.Propagate(dst=ygbpl__nok.
            name, src=rxqph__cihm.name, loc=join_node.loc))
    return


typeinfer.typeinfer_extensions[Join] = join_typeinfer


def visit_vars_join(join_node, callback, cbdata):
    if debug_prints():
        print('visiting join vars for:', join_node)
        print('cbdata: ', sorted(cbdata.items()))
    for rab__rhnhu in list(join_node.left_vars.keys()):
        join_node.left_vars[rab__rhnhu] = visit_vars_inner(join_node.
            left_vars[rab__rhnhu], callback, cbdata)
    for rab__rhnhu in list(join_node.right_vars.keys()):
        join_node.right_vars[rab__rhnhu] = visit_vars_inner(join_node.
            right_vars[rab__rhnhu], callback, cbdata)
    for rab__rhnhu in list(join_node.out_data_vars.keys()):
        join_node.out_data_vars[rab__rhnhu] = visit_vars_inner(join_node.
            out_data_vars[rab__rhnhu], callback, cbdata)


ir_utils.visit_vars_extensions[Join] = visit_vars_join


def remove_dead_join(join_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    vsy__gjugs = []
    upsm__whtf = True
    for rab__rhnhu, rxqph__cihm in join_node.out_data_vars.items():
        if rxqph__cihm.name in lives:
            upsm__whtf = False
            continue
        if rab__rhnhu == '$_bodo_index_':
            continue
        if join_node.indicator and rab__rhnhu == '_merge':
            vsy__gjugs.append('_merge')
            join_node.indicator = False
            continue
        yah__hjox, buqc__nelk = join_node.column_origins[rab__rhnhu]
        if (yah__hjox == 'left' and buqc__nelk not in join_node.left_keys and
            buqc__nelk not in join_node.left_cond_cols):
            join_node.left_vars.pop(buqc__nelk)
            vsy__gjugs.append(rab__rhnhu)
        if (yah__hjox == 'right' and buqc__nelk not in join_node.right_keys and
            buqc__nelk not in join_node.right_cond_cols):
            join_node.right_vars.pop(buqc__nelk)
            vsy__gjugs.append(rab__rhnhu)
    for cname in vsy__gjugs:
        join_node.out_data_vars.pop(cname)
    if upsm__whtf:
        return None
    return join_node


ir_utils.remove_dead_extensions[Join] = remove_dead_join


def join_usedefs(join_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({aug__crg.name for aug__crg in join_node.left_vars.values()}
        )
    use_set.update({aug__crg.name for aug__crg in join_node.right_vars.
        values()})
    def_set.update({aug__crg.name for aug__crg in join_node.out_data_vars.
        values()})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Join] = join_usedefs


def get_copies_join(join_node, typemap):
    cnfyb__adzb = set(aug__crg.name for aug__crg in join_node.out_data_vars
        .values())
    return set(), cnfyb__adzb


ir_utils.copy_propagate_extensions[Join] = get_copies_join


def apply_copies_join(join_node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    for rab__rhnhu in list(join_node.left_vars.keys()):
        join_node.left_vars[rab__rhnhu] = replace_vars_inner(join_node.
            left_vars[rab__rhnhu], var_dict)
    for rab__rhnhu in list(join_node.right_vars.keys()):
        join_node.right_vars[rab__rhnhu] = replace_vars_inner(join_node.
            right_vars[rab__rhnhu], var_dict)
    for rab__rhnhu in list(join_node.out_data_vars.keys()):
        join_node.out_data_vars[rab__rhnhu] = replace_vars_inner(join_node.
            out_data_vars[rab__rhnhu], var_dict)
    return


ir_utils.apply_copy_propagate_extensions[Join] = apply_copies_join


def build_join_definitions(join_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for rxqph__cihm in join_node.out_data_vars.values():
        definitions[rxqph__cihm.name].append(join_node)
    return definitions


ir_utils.build_defs_extensions[Join] = build_join_definitions


def join_distributed_run(join_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    left_parallel, right_parallel = False, False
    if array_dists is not None:
        left_parallel, right_parallel = _get_table_parallel_flags(join_node,
            array_dists)
    n_keys = len(join_node.left_keys)
    bsht__nlot = tuple(join_node.left_vars[pdxy__nkfqe] for pdxy__nkfqe in
        join_node.left_keys)
    wqh__cyer = tuple(join_node.right_vars[pdxy__nkfqe] for pdxy__nkfqe in
        join_node.right_keys)
    pove__fokg = tuple(join_node.left_vars.keys())
    gft__lsv = tuple(join_node.right_vars.keys())
    jpli__ryyz = ()
    vmirx__mqb = ()
    optional_column = False
    if (join_node.left_index and not join_node.right_index and not
        join_node.is_join):
        ukc__ijumk = join_node.right_keys[0]
        if ukc__ijumk in pove__fokg:
            vmirx__mqb = ukc__ijumk,
            jpli__ryyz = join_node.right_vars[ukc__ijumk],
            optional_column = True
    if (join_node.right_index and not join_node.left_index and not
        join_node.is_join):
        ukc__ijumk = join_node.left_keys[0]
        if ukc__ijumk in gft__lsv:
            vmirx__mqb = ukc__ijumk,
            jpli__ryyz = join_node.left_vars[ukc__ijumk],
            optional_column = True
    cdhox__nvse = tuple(join_node.out_data_vars[cname] for cname in vmirx__mqb)
    ujf__hez = tuple(aug__crg for rgv__ubmai, aug__crg in sorted(join_node.
        left_vars.items(), key=lambda a: str(a[0])) if rgv__ubmai not in
        join_node.left_keys)
    vbt__mbsv = tuple(aug__crg for rgv__ubmai, aug__crg in sorted(join_node
        .right_vars.items(), key=lambda a: str(a[0])) if rgv__ubmai not in
        join_node.right_keys)
    djc__mbji = jpli__ryyz + bsht__nlot + wqh__cyer + ujf__hez + vbt__mbsv
    tpllb__krgzh = tuple(typemap[aug__crg.name] for aug__crg in djc__mbji)
    edygu__tih = tuple('opti_c' + str(eazan__juqfh) for eazan__juqfh in
        range(len(jpli__ryyz)))
    left_other_names = tuple('t1_c' + str(eazan__juqfh) for eazan__juqfh in
        range(len(ujf__hez)))
    right_other_names = tuple('t2_c' + str(eazan__juqfh) for eazan__juqfh in
        range(len(vbt__mbsv)))
    left_other_types = tuple([typemap[pdxy__nkfqe.name] for pdxy__nkfqe in
        ujf__hez])
    right_other_types = tuple([typemap[pdxy__nkfqe.name] for pdxy__nkfqe in
        vbt__mbsv])
    left_key_names = tuple('t1_key' + str(eazan__juqfh) for eazan__juqfh in
        range(n_keys))
    right_key_names = tuple('t2_key' + str(eazan__juqfh) for eazan__juqfh in
        range(n_keys))
    glbs = {}
    loc = join_node.loc
    func_text = 'def f({}{}, {},{}{}{}):\n'.format('{},'.format(edygu__tih[
        0]) if len(edygu__tih) == 1 else '', ','.join(left_key_names), ','.
        join(right_key_names), ','.join(left_other_names), ',' if len(
        left_other_names) != 0 else '', ','.join(right_other_names))
    left_key_types = tuple(typemap[aug__crg.name] for aug__crg in bsht__nlot)
    right_key_types = tuple(typemap[aug__crg.name] for aug__crg in wqh__cyer)
    for eazan__juqfh in range(n_keys):
        glbs[f'key_type_{eazan__juqfh}'] = _match_join_key_types(left_key_types
            [eazan__juqfh], right_key_types[eazan__juqfh], loc)
    func_text += '    t1_keys = ({},)\n'.format(', '.join(
        f'bodo.utils.utils.astype({left_key_names[eazan__juqfh]}, key_type_{eazan__juqfh})'
         for eazan__juqfh in range(n_keys)))
    func_text += '    t2_keys = ({},)\n'.format(', '.join(
        f'bodo.utils.utils.astype({right_key_names[eazan__juqfh]}, key_type_{eazan__juqfh})'
         for eazan__juqfh in range(n_keys)))
    func_text += '    data_left = ({}{})\n'.format(','.join(
        left_other_names), ',' if len(left_other_names) != 0 else '')
    func_text += '    data_right = ({}{})\n'.format(','.join(
        right_other_names), ',' if len(right_other_names) != 0 else '')
    xhvn__glw = []
    for cname in join_node.left_keys:
        if cname in join_node.add_suffix:
            lyc__xmk = str(cname) + join_node.suffix_x
        else:
            lyc__xmk = cname
        assert lyc__xmk in join_node.out_data_vars
        xhvn__glw.append(join_node.out_data_vars[lyc__xmk])
    for eazan__juqfh, cname in enumerate(join_node.right_keys):
        if not join_node.vect_same_key[eazan__juqfh] and not join_node.is_join:
            if cname in join_node.add_suffix:
                lyc__xmk = str(cname) + join_node.suffix_y
            else:
                lyc__xmk = cname
            assert lyc__xmk in join_node.out_data_vars
            xhvn__glw.append(join_node.out_data_vars[lyc__xmk])

    def _get_out_col_var(cname, is_left):
        if cname in join_node.add_suffix:
            if is_left:
                lyc__xmk = str(cname) + join_node.suffix_x
            else:
                lyc__xmk = str(cname) + join_node.suffix_y
        else:
            lyc__xmk = cname
        return join_node.out_data_vars[lyc__xmk]
    lxg__tdcn = cdhox__nvse + tuple(xhvn__glw)
    lxg__tdcn += tuple(_get_out_col_var(rgv__ubmai, True) for rgv__ubmai,
        aug__crg in sorted(join_node.left_vars.items(), key=lambda a: str(a
        [0])) if rgv__ubmai not in join_node.left_keys)
    lxg__tdcn += tuple(_get_out_col_var(rgv__ubmai, False) for rgv__ubmai,
        aug__crg in sorted(join_node.right_vars.items(), key=lambda a: str(
        a[0])) if rgv__ubmai not in join_node.right_keys)
    if join_node.indicator:
        lxg__tdcn += _get_out_col_var('_merge', False),
    ijdq__agw = [('t3_c' + str(eazan__juqfh)) for eazan__juqfh in range(len
        (lxg__tdcn))]
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
            right_parallel, glbs, [typemap[aug__crg.name] for aug__crg in
            lxg__tdcn], join_node.loc, join_node.indicator, join_node.
            is_na_equal, general_cond_cfunc, left_col_nums, right_col_nums)
    if join_node.how == 'asof':
        for eazan__juqfh in range(len(left_other_names)):
            func_text += '    left_{} = out_data_left[{}]\n'.format(
                eazan__juqfh, eazan__juqfh)
        for eazan__juqfh in range(len(right_other_names)):
            func_text += '    right_{} = out_data_right[{}]\n'.format(
                eazan__juqfh, eazan__juqfh)
        for eazan__juqfh in range(n_keys):
            func_text += (
                f'    t1_keys_{eazan__juqfh} = out_t1_keys[{eazan__juqfh}]\n')
        for eazan__juqfh in range(n_keys):
            func_text += (
                f'    t2_keys_{eazan__juqfh} = out_t2_keys[{eazan__juqfh}]\n')
    idx = 0
    if optional_column:
        func_text += f'    {ijdq__agw[idx]} = opti_0\n'
        idx += 1
    for eazan__juqfh in range(n_keys):
        func_text += f'    {ijdq__agw[idx]} = t1_keys_{eazan__juqfh}\n'
        idx += 1
    for eazan__juqfh in range(n_keys):
        if not join_node.vect_same_key[eazan__juqfh] and not join_node.is_join:
            func_text += f'    {ijdq__agw[idx]} = t2_keys_{eazan__juqfh}\n'
            idx += 1
    for eazan__juqfh in range(len(left_other_names)):
        func_text += f'    {ijdq__agw[idx]} = left_{eazan__juqfh}\n'
        idx += 1
    for eazan__juqfh in range(len(right_other_names)):
        func_text += f'    {ijdq__agw[idx]} = right_{eazan__juqfh}\n'
        idx += 1
    if join_node.indicator:
        func_text += f'    {ijdq__agw[idx]} = indicator_col\n'
        idx += 1
    chet__bsui = {}
    exec(func_text, {}, chet__bsui)
    xwul__fgb = chet__bsui['f']
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
    vycfe__uou = compile_to_numba_ir(xwul__fgb, glbs, typingctx=typingctx,
        targetctx=targetctx, arg_typs=tpllb__krgzh, typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(vycfe__uou, djc__mbji)
    yow__impt = vycfe__uou.body[:-3]
    for eazan__juqfh in range(len(lxg__tdcn)):
        yow__impt[-len(lxg__tdcn) + eazan__juqfh].target = lxg__tdcn[
            eazan__juqfh]
    return yow__impt


distributed_pass.distributed_run_extensions[Join] = join_distributed_run


def _gen_general_cond_cfunc(join_node, typemap):
    expr = join_node.gen_cond_expr
    if not expr:
        return None, [], []
    ynq__gzwbu = next_label()
    ged__imjb = _get_col_to_ind(join_node.left_keys, join_node.left_vars)
    cgoo__jpc = _get_col_to_ind(join_node.right_keys, join_node.right_vars)
    table_getitem_funcs = {'bodo': bodo, 'numba': numba, 'is_null_pointer':
        is_null_pointer}
    na_check_name = 'NOT_NA'
    func_text = f"""def bodo_join_gen_cond{ynq__gzwbu}(left_table, right_table, left_data1, right_data1, left_null_bitmap, right_null_bitmap, left_ind, right_ind):
"""
    func_text += '  if is_null_pointer(left_table):\n'
    func_text += '    return False\n'
    expr, func_text, left_col_nums = _replace_column_accesses(expr,
        ged__imjb, typemap, join_node.left_vars, table_getitem_funcs,
        func_text, 'left', len(join_node.left_keys), na_check_name)
    expr, func_text, right_col_nums = _replace_column_accesses(expr,
        cgoo__jpc, typemap, join_node.right_vars, table_getitem_funcs,
        func_text, 'right', len(join_node.right_keys), na_check_name)
    func_text += f'  return {expr}'
    chet__bsui = {}
    exec(func_text, table_getitem_funcs, chet__bsui)
    zrn__ijkdt = chet__bsui[f'bodo_join_gen_cond{ynq__gzwbu}']
    aqy__jslgt = types.bool_(types.voidptr, types.voidptr, types.voidptr,
        types.voidptr, types.voidptr, types.voidptr, types.int64, types.int64)
    sya__hrxxp = numba.cfunc(aqy__jslgt, nopython=True)(zrn__ijkdt)
    join_gen_cond_cfunc[sya__hrxxp.native_name] = sya__hrxxp
    join_gen_cond_cfunc_addr[sya__hrxxp.native_name] = sya__hrxxp.address
    return sya__hrxxp, left_col_nums, right_col_nums


def _replace_column_accesses(expr, col_to_ind, typemap, col_vars,
    table_getitem_funcs, func_text, table_name, n_keys, na_check_name):
    xxc__rapox = []
    for pdxy__nkfqe, kku__tzbn in col_to_ind.items():
        cname = f'({table_name}.{pdxy__nkfqe})'
        if cname not in expr:
            continue
        aejnd__hhhkb = f'getitem_{table_name}_val_{kku__tzbn}'
        fne__aet = f'_bodo_{table_name}_val_{kku__tzbn}'
        daki__qthdz = typemap[col_vars[pdxy__nkfqe].name]
        if is_str_arr_type(daki__qthdz):
            func_text += f"""  {fne__aet}, {fne__aet}_size = {aejnd__hhhkb}({table_name}_table, {table_name}_ind)
"""
            func_text += f"""  {fne__aet} = bodo.libs.str_arr_ext.decode_utf8({fne__aet}, {fne__aet}_size)
"""
        else:
            func_text += (
                f'  {fne__aet} = {aejnd__hhhkb}({table_name}_data1, {table_name}_ind)\n'
                )
        table_getitem_funcs[aejnd__hhhkb
            ] = bodo.libs.array._gen_row_access_intrinsic(daki__qthdz,
            kku__tzbn)
        expr = expr.replace(cname, fne__aet)
        szjc__ohpo = f'({na_check_name}.{table_name}.{pdxy__nkfqe})'
        if szjc__ohpo in expr:
            vlr__ovcu = f'nacheck_{table_name}_val_{kku__tzbn}'
            trfr__vvlu = f'_bodo_isna_{table_name}_val_{kku__tzbn}'
            if (isinstance(daki__qthdz, bodo.libs.int_arr_ext.
                IntegerArrayType) or daki__qthdz == bodo.libs.bool_arr_ext.
                boolean_array or is_str_arr_type(daki__qthdz)):
                func_text += f"""  {trfr__vvlu} = {vlr__ovcu}({table_name}_null_bitmap, {table_name}_ind)
"""
            else:
                func_text += (
                    f'  {trfr__vvlu} = {vlr__ovcu}({table_name}_data1, {table_name}_ind)\n'
                    )
            table_getitem_funcs[vlr__ovcu
                ] = bodo.libs.array._gen_row_na_check_intrinsic(daki__qthdz,
                kku__tzbn)
            expr = expr.replace(szjc__ohpo, trfr__vvlu)
        if kku__tzbn >= n_keys:
            xxc__rapox.append(kku__tzbn)
    return expr, func_text, xxc__rapox


def _get_col_to_ind(key_names, col_vars):
    n_keys = len(key_names)
    col_to_ind = {pdxy__nkfqe: eazan__juqfh for eazan__juqfh, pdxy__nkfqe in
        enumerate(key_names)}
    eazan__juqfh = n_keys
    for pdxy__nkfqe in sorted(col_vars, key=lambda a: str(a)):
        if pdxy__nkfqe in key_names:
            continue
        col_to_ind[pdxy__nkfqe] = eazan__juqfh
        eazan__juqfh += 1
    return col_to_ind


def _match_join_key_types(t1, t2, loc):
    if t1 == t2:
        return t1
    try:
        arr = dtype_to_array_type(find_common_np_dtype([t1, t2]))
        return to_nullable_type(arr) if is_nullable_type(t1
            ) or is_nullable_type(t2) else arr
    except Exception as toyjf__dist:
        if is_str_arr_type(t1) and is_str_arr_type(t2):
            return bodo.string_array_type
        raise BodoError(f'Join key types {t1} and {t2} do not match', loc=loc)


def _get_table_parallel_flags(join_node, array_dists):
    ajcv__wqmcr = (distributed_pass.Distribution.OneD, distributed_pass.
        Distribution.OneD_Var)
    left_parallel = all(array_dists[aug__crg.name] in ajcv__wqmcr for
        aug__crg in join_node.left_vars.values())
    right_parallel = all(array_dists[aug__crg.name] in ajcv__wqmcr for
        aug__crg in join_node.right_vars.values())
    if not left_parallel:
        assert not any(array_dists[aug__crg.name] in ajcv__wqmcr for
            aug__crg in join_node.left_vars.values())
    if not right_parallel:
        assert not any(array_dists[aug__crg.name] in ajcv__wqmcr for
            aug__crg in join_node.right_vars.values())
    if left_parallel or right_parallel:
        assert all(array_dists[aug__crg.name] in ajcv__wqmcr for aug__crg in
            join_node.out_data_vars.values())
    return left_parallel, right_parallel


def _gen_local_hash_join(optional_column, left_key_names, right_key_names,
    left_key_types, right_key_types, left_other_names, right_other_names,
    left_other_types, right_other_types, vect_same_key, is_left, is_right,
    is_join, left_parallel, right_parallel, glbs, out_types, loc, indicator,
    is_na_equal, general_cond_cfunc, left_col_nums, right_col_nums):

    def needs_typechange(in_type, need_nullable, is_same_key):
        return isinstance(in_type, types.Array) and not is_dtype_nullable(
            in_type.dtype) and need_nullable and not is_same_key
    ouyfo__lto = []
    for eazan__juqfh in range(len(left_key_names)):
        duhi__zrc = _match_join_key_types(left_key_types[eazan__juqfh],
            right_key_types[eazan__juqfh], loc)
        ouyfo__lto.append(needs_typechange(duhi__zrc, is_right,
            vect_same_key[eazan__juqfh]))
    for eazan__juqfh in range(len(left_other_names)):
        ouyfo__lto.append(needs_typechange(left_other_types[eazan__juqfh],
            is_right, False))
    for eazan__juqfh in range(len(right_key_names)):
        if not vect_same_key[eazan__juqfh] and not is_join:
            duhi__zrc = _match_join_key_types(left_key_types[eazan__juqfh],
                right_key_types[eazan__juqfh], loc)
            ouyfo__lto.append(needs_typechange(duhi__zrc, is_left, False))
    for eazan__juqfh in range(len(right_other_names)):
        ouyfo__lto.append(needs_typechange(right_other_types[eazan__juqfh],
            is_left, False))

    def get_out_type(idx, in_type, in_name, need_nullable, is_same_key):
        if isinstance(in_type, types.Array) and not is_dtype_nullable(in_type
            .dtype) and need_nullable and not is_same_key:
            if isinstance(in_type.dtype, types.Integer):
                gnc__mhui = IntDtype(in_type.dtype).name
                assert gnc__mhui.endswith('Dtype()')
                gnc__mhui = gnc__mhui[:-7]
                hcl__zmjf = f"""    typ_{idx} = bodo.hiframes.pd_series_ext.get_series_data(pd.Series([1], dtype="{gnc__mhui}"))
"""
                daik__rqvwr = f'typ_{idx}'
            else:
                assert in_type.dtype == types.bool_, 'unexpected non-nullable type in join'
                hcl__zmjf = (
                    f'    typ_{idx} = bodo.libs.bool_arr_ext.alloc_bool_array(1)\n'
                    )
                daik__rqvwr = f'typ_{idx}'
        elif in_type == bodo.string_array_type:
            hcl__zmjf = (
                f'    typ_{idx} = bodo.libs.str_arr_ext.pre_alloc_string_array(0, 0)\n'
                )
            daik__rqvwr = f'typ_{idx}'
        else:
            hcl__zmjf = ''
            daik__rqvwr = in_name
        return hcl__zmjf, daik__rqvwr
    n_keys = len(left_key_names)
    func_text = '    # beginning of _gen_local_hash_join\n'
    eww__jyyg = []
    for eazan__juqfh in range(n_keys):
        eww__jyyg.append('t1_keys[{}]'.format(eazan__juqfh))
    for eazan__juqfh in range(len(left_other_names)):
        eww__jyyg.append('data_left[{}]'.format(eazan__juqfh))
    func_text += '    info_list_total_l = [{}]\n'.format(','.join(
        'array_to_info({})'.format(a) for a in eww__jyyg))
    func_text += '    table_left = arr_info_list_to_table(info_list_total_l)\n'
    qpe__lse = []
    for eazan__juqfh in range(n_keys):
        qpe__lse.append('t2_keys[{}]'.format(eazan__juqfh))
    for eazan__juqfh in range(len(right_other_names)):
        qpe__lse.append('data_right[{}]'.format(eazan__juqfh))
    func_text += '    info_list_total_r = [{}]\n'.format(','.join(
        'array_to_info({})'.format(a) for a in qpe__lse))
    func_text += (
        '    table_right = arr_info_list_to_table(info_list_total_r)\n')
    func_text += '    vect_same_key = np.array([{}])\n'.format(','.join('1' if
        tyja__jpcl else '0' for tyja__jpcl in vect_same_key))
    func_text += '    vect_need_typechange = np.array([{}])\n'.format(','.
        join('1' if tyja__jpcl else '0' for tyja__jpcl in ouyfo__lto))
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
        tws__obux = get_out_type(idx, out_types[idx], 'opti_c0', False, False)
        func_text += tws__obux[0]
        glbs[f'out_type_{idx}'] = out_types[idx]
        func_text += f"""    opti_0 = info_to_array(info_from_table(out_table, {idx}), {tws__obux[1]})
"""
        idx += 1
    for eazan__juqfh, uxety__dwlp in enumerate(left_key_names):
        duhi__zrc = _match_join_key_types(left_key_types[eazan__juqfh],
            right_key_types[eazan__juqfh], loc)
        tws__obux = get_out_type(idx, duhi__zrc, f't1_keys[{eazan__juqfh}]',
            is_right, vect_same_key[eazan__juqfh])
        func_text += tws__obux[0]
        glbs[f'out_type_{idx}'] = out_types[idx]
        if duhi__zrc != left_key_types[eazan__juqfh] and left_key_types[
            eazan__juqfh] != bodo.dict_str_arr_type:
            func_text += f"""    t1_keys_{eazan__juqfh} = bodo.utils.utils.astype(info_to_array(info_from_table(out_table, {idx}), {tws__obux[1]}), out_type_{idx})
"""
        else:
            func_text += f"""    t1_keys_{eazan__juqfh} = info_to_array(info_from_table(out_table, {idx}), {tws__obux[1]})
"""
        idx += 1
    for eazan__juqfh, uxety__dwlp in enumerate(left_other_names):
        tws__obux = get_out_type(idx, left_other_types[eazan__juqfh],
            uxety__dwlp, is_right, False)
        func_text += tws__obux[0]
        func_text += (
            '    left_{} = info_to_array(info_from_table(out_table, {}), {})\n'
            .format(eazan__juqfh, idx, tws__obux[1]))
        idx += 1
    for eazan__juqfh, uxety__dwlp in enumerate(right_key_names):
        if not vect_same_key[eazan__juqfh] and not is_join:
            duhi__zrc = _match_join_key_types(left_key_types[eazan__juqfh],
                right_key_types[eazan__juqfh], loc)
            tws__obux = get_out_type(idx, duhi__zrc,
                f't2_keys[{eazan__juqfh}]', is_left, False)
            func_text += tws__obux[0]
            glbs[f'out_type_{idx}'] = out_types[idx - len(left_other_names)]
            if duhi__zrc != right_key_types[eazan__juqfh] and right_key_types[
                eazan__juqfh] != bodo.dict_str_arr_type:
                func_text += f"""    t2_keys_{eazan__juqfh} = bodo.utils.utils.astype(info_to_array(info_from_table(out_table, {idx}), {tws__obux[1]}), out_type_{idx})
"""
            else:
                func_text += f"""    t2_keys_{eazan__juqfh} = info_to_array(info_from_table(out_table, {idx}), {tws__obux[1]})
"""
            idx += 1
    for eazan__juqfh, uxety__dwlp in enumerate(right_other_names):
        tws__obux = get_out_type(idx, right_other_types[eazan__juqfh],
            uxety__dwlp, is_left, False)
        func_text += tws__obux[0]
        func_text += (
            '    right_{} = info_to_array(info_from_table(out_table, {}), {})\n'
            .format(eazan__juqfh, idx, tws__obux[1]))
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
    xjskg__wkklm = bodo.libs.distributed_api.get_size()
    borzl__wqcax = np.empty(xjskg__wkklm, left_key_arrs[0].dtype)
    rkhpp__wzo = np.empty(xjskg__wkklm, left_key_arrs[0].dtype)
    bodo.libs.distributed_api.allgather(borzl__wqcax, left_key_arrs[0][0])
    bodo.libs.distributed_api.allgather(rkhpp__wzo, left_key_arrs[0][-1])
    qfl__sgkvo = np.zeros(xjskg__wkklm, np.int32)
    hzhp__oheu = np.zeros(xjskg__wkklm, np.int32)
    qqk__tisfy = np.zeros(xjskg__wkklm, np.int32)
    lwnki__wxu = right_key_arrs[0][0]
    isuh__ynkxa = right_key_arrs[0][-1]
    sdd__cyicv = -1
    eazan__juqfh = 0
    while eazan__juqfh < xjskg__wkklm - 1 and rkhpp__wzo[eazan__juqfh
        ] < lwnki__wxu:
        eazan__juqfh += 1
    while eazan__juqfh < xjskg__wkklm and borzl__wqcax[eazan__juqfh
        ] <= isuh__ynkxa:
        sdd__cyicv, vgd__hyfu = _count_overlap(right_key_arrs[0],
            borzl__wqcax[eazan__juqfh], rkhpp__wzo[eazan__juqfh])
        if sdd__cyicv != 0:
            sdd__cyicv -= 1
            vgd__hyfu += 1
        qfl__sgkvo[eazan__juqfh] = vgd__hyfu
        hzhp__oheu[eazan__juqfh] = sdd__cyicv
        eazan__juqfh += 1
    while eazan__juqfh < xjskg__wkklm:
        qfl__sgkvo[eazan__juqfh] = 1
        hzhp__oheu[eazan__juqfh] = len(right_key_arrs[0]) - 1
        eazan__juqfh += 1
    bodo.libs.distributed_api.alltoall(qfl__sgkvo, qqk__tisfy, 1)
    ivf__fkpe = qqk__tisfy.sum()
    yaf__fdy = np.empty(ivf__fkpe, right_key_arrs[0].dtype)
    odzsy__adpr = alloc_arr_tup(ivf__fkpe, right_data)
    tmon__prvjx = bodo.ir.join.calc_disp(qqk__tisfy)
    bodo.libs.distributed_api.alltoallv(right_key_arrs[0], yaf__fdy,
        qfl__sgkvo, qqk__tisfy, hzhp__oheu, tmon__prvjx)
    bodo.libs.distributed_api.alltoallv_tup(right_data, odzsy__adpr,
        qfl__sgkvo, qqk__tisfy, hzhp__oheu, tmon__prvjx)
    return (yaf__fdy,), odzsy__adpr


@numba.njit
def _count_overlap(r_key_arr, start, end):
    vgd__hyfu = 0
    sdd__cyicv = 0
    cgjt__cboj = 0
    while cgjt__cboj < len(r_key_arr) and r_key_arr[cgjt__cboj] < start:
        sdd__cyicv += 1
        cgjt__cboj += 1
    while cgjt__cboj < len(r_key_arr) and start <= r_key_arr[cgjt__cboj
        ] <= end:
        cgjt__cboj += 1
        vgd__hyfu += 1
    return sdd__cyicv, vgd__hyfu


import llvmlite.binding as ll
from bodo.libs import hdist
ll.add_symbol('c_alltoallv', hdist.c_alltoallv)


@numba.njit
def calc_disp(arr):
    szkn__egpn = np.empty_like(arr)
    szkn__egpn[0] = 0
    for eazan__juqfh in range(1, len(arr)):
        szkn__egpn[eazan__juqfh] = szkn__egpn[eazan__juqfh - 1] + arr[
            eazan__juqfh - 1]
    return szkn__egpn


@numba.njit
def local_merge_asof(left_keys, right_keys, data_left, data_right):
    dngft__qou = len(left_keys[0])
    qakiq__buu = len(right_keys[0])
    dujj__kcw = alloc_arr_tup(dngft__qou, left_keys)
    lft__xyt = alloc_arr_tup(dngft__qou, right_keys)
    iwpb__thfb = alloc_arr_tup(dngft__qou, data_left)
    jcaga__matu = alloc_arr_tup(dngft__qou, data_right)
    ftt__twfeo = 0
    wmjg__mhwpk = 0
    for ftt__twfeo in range(dngft__qou):
        if wmjg__mhwpk < 0:
            wmjg__mhwpk = 0
        while wmjg__mhwpk < qakiq__buu and getitem_arr_tup(right_keys,
            wmjg__mhwpk) <= getitem_arr_tup(left_keys, ftt__twfeo):
            wmjg__mhwpk += 1
        wmjg__mhwpk -= 1
        setitem_arr_tup(dujj__kcw, ftt__twfeo, getitem_arr_tup(left_keys,
            ftt__twfeo))
        setitem_arr_tup(iwpb__thfb, ftt__twfeo, getitem_arr_tup(data_left,
            ftt__twfeo))
        if wmjg__mhwpk >= 0:
            setitem_arr_tup(lft__xyt, ftt__twfeo, getitem_arr_tup(
                right_keys, wmjg__mhwpk))
            setitem_arr_tup(jcaga__matu, ftt__twfeo, getitem_arr_tup(
                data_right, wmjg__mhwpk))
        else:
            bodo.libs.array_kernels.setna_tup(lft__xyt, ftt__twfeo)
            bodo.libs.array_kernels.setna_tup(jcaga__matu, ftt__twfeo)
    return dujj__kcw, lft__xyt, iwpb__thfb, jcaga__matu


def copy_arr_tup(arrs):
    return tuple(a.copy() for a in arrs)


@overload(copy_arr_tup, no_unliteral=True)
def copy_arr_tup_overload(arrs):
    vgd__hyfu = arrs.count
    func_text = 'def f(arrs):\n'
    func_text += '  return ({},)\n'.format(','.join('arrs[{}].copy()'.
        format(eazan__juqfh) for eazan__juqfh in range(vgd__hyfu)))
    chet__bsui = {}
    exec(func_text, {}, chet__bsui)
    aqi__byde = chet__bsui['f']
    return aqi__byde
