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
        lfmzk__qqzj = func.signature
        txw__pcn = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64), lir
            .IntType(64)])
        yzl__zuvk = cgutils.get_or_insert_function(builder.module, txw__pcn,
            sym._literal_value)
        builder.call(yzl__zuvk, [context.get_constant_null(lfmzk__qqzj.args
            [0]), context.get_constant_null(lfmzk__qqzj.args[1]), context.
            get_constant_null(lfmzk__qqzj.args[2]), context.
            get_constant_null(lfmzk__qqzj.args[3]), context.
            get_constant_null(lfmzk__qqzj.args[4]), context.
            get_constant_null(lfmzk__qqzj.args[5]), context.get_constant(
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
        self.left_cond_cols = set(aybi__hrxhr for aybi__hrxhr in left_vars.
            keys() if f'(left.{aybi__hrxhr})' in gen_cond_expr)
        self.right_cond_cols = set(aybi__hrxhr for aybi__hrxhr in
            right_vars.keys() if f'(right.{aybi__hrxhr})' in gen_cond_expr)
        aof__fgkws = set(left_keys) & set(right_keys)
        tcgd__qdvra = set(left_vars.keys()) & set(right_vars.keys())
        yeweg__sihlc = tcgd__qdvra - aof__fgkws
        vect_same_key = []
        n_keys = len(left_keys)
        for fdg__gywd in range(n_keys):
            lrdfv__afzn = left_keys[fdg__gywd]
            crc__hslra = right_keys[fdg__gywd]
            vect_same_key.append(lrdfv__afzn == crc__hslra)
        self.vect_same_key = vect_same_key
        self.column_origins = {(str(aybi__hrxhr) + suffix_x if aybi__hrxhr in
            yeweg__sihlc else aybi__hrxhr): ('left', aybi__hrxhr) for
            aybi__hrxhr in left_vars.keys()}
        self.column_origins.update({(str(aybi__hrxhr) + suffix_y if 
            aybi__hrxhr in yeweg__sihlc else aybi__hrxhr): ('right',
            aybi__hrxhr) for aybi__hrxhr in right_vars.keys()})
        if '$_bodo_index_' in yeweg__sihlc:
            yeweg__sihlc.remove('$_bodo_index_')
        self.add_suffix = yeweg__sihlc

    def __repr__(self):
        dglcb__axlo = ''
        for aybi__hrxhr, lctd__rywb in self.out_data_vars.items():
            dglcb__axlo += "'{}':{}, ".format(aybi__hrxhr, lctd__rywb.name)
        cfbjh__zus = '{}{{{}}}'.format(self.df_out, dglcb__axlo)
        osav__syzin = ''
        for aybi__hrxhr, lctd__rywb in self.left_vars.items():
            osav__syzin += "'{}':{}, ".format(aybi__hrxhr, lctd__rywb.name)
        hauaa__bwih = '{}{{{}}}'.format(self.left_df, osav__syzin)
        osav__syzin = ''
        for aybi__hrxhr, lctd__rywb in self.right_vars.items():
            osav__syzin += "'{}':{}, ".format(aybi__hrxhr, lctd__rywb.name)
        pwqhv__iql = '{}{{{}}}'.format(self.right_df, osav__syzin)
        return 'join [{}={}]: {} , {}, {}'.format(self.left_keys, self.
            right_keys, cfbjh__zus, hauaa__bwih, pwqhv__iql)


def join_array_analysis(join_node, equiv_set, typemap, array_analysis):
    unjna__fuv = []
    assert len(join_node.out_data_vars) > 0, 'empty join in array analysis'
    qxktf__pzjx = []
    ceryu__fuvza = list(join_node.left_vars.values())
    for jmr__bvp in ceryu__fuvza:
        dcmg__pjvvx = typemap[jmr__bvp.name]
        pahl__avhp = equiv_set.get_shape(jmr__bvp)
        if pahl__avhp:
            qxktf__pzjx.append(pahl__avhp[0])
    if len(qxktf__pzjx) > 1:
        equiv_set.insert_equiv(*qxktf__pzjx)
    qxktf__pzjx = []
    ceryu__fuvza = list(join_node.right_vars.values())
    for jmr__bvp in ceryu__fuvza:
        dcmg__pjvvx = typemap[jmr__bvp.name]
        pahl__avhp = equiv_set.get_shape(jmr__bvp)
        if pahl__avhp:
            qxktf__pzjx.append(pahl__avhp[0])
    if len(qxktf__pzjx) > 1:
        equiv_set.insert_equiv(*qxktf__pzjx)
    qxktf__pzjx = []
    for jmr__bvp in join_node.out_data_vars.values():
        dcmg__pjvvx = typemap[jmr__bvp.name]
        thb__jll = array_analysis._gen_shape_call(equiv_set, jmr__bvp,
            dcmg__pjvvx.ndim, None, unjna__fuv)
        equiv_set.insert_equiv(jmr__bvp, thb__jll)
        qxktf__pzjx.append(thb__jll[0])
        equiv_set.define(jmr__bvp, set())
    if len(qxktf__pzjx) > 1:
        equiv_set.insert_equiv(*qxktf__pzjx)
    return [], unjna__fuv


numba.parfors.array_analysis.array_analysis_extensions[Join
    ] = join_array_analysis


def join_distributed_analysis(join_node, array_dists):
    ivey__xtlrd = Distribution.OneD
    egtt__rhl = Distribution.OneD
    for jmr__bvp in join_node.left_vars.values():
        ivey__xtlrd = Distribution(min(ivey__xtlrd.value, array_dists[
            jmr__bvp.name].value))
    for jmr__bvp in join_node.right_vars.values():
        egtt__rhl = Distribution(min(egtt__rhl.value, array_dists[jmr__bvp.
            name].value))
    ckrt__cjy = Distribution.OneD_Var
    for jmr__bvp in join_node.out_data_vars.values():
        if jmr__bvp.name in array_dists:
            ckrt__cjy = Distribution(min(ckrt__cjy.value, array_dists[
                jmr__bvp.name].value))
    deqfz__uolt = Distribution(min(ckrt__cjy.value, ivey__xtlrd.value))
    znyrl__hsmmu = Distribution(min(ckrt__cjy.value, egtt__rhl.value))
    ckrt__cjy = Distribution(max(deqfz__uolt.value, znyrl__hsmmu.value))
    for jmr__bvp in join_node.out_data_vars.values():
        array_dists[jmr__bvp.name] = ckrt__cjy
    if ckrt__cjy != Distribution.OneD_Var:
        ivey__xtlrd = ckrt__cjy
        egtt__rhl = ckrt__cjy
    for jmr__bvp in join_node.left_vars.values():
        array_dists[jmr__bvp.name] = ivey__xtlrd
    for jmr__bvp in join_node.right_vars.values():
        array_dists[jmr__bvp.name] = egtt__rhl
    return


distributed_analysis.distributed_analysis_extensions[Join
    ] = join_distributed_analysis


def join_typeinfer(join_node, typeinferer):
    aof__fgkws = set(join_node.left_keys) & set(join_node.right_keys)
    tcgd__qdvra = set(join_node.left_vars.keys()) & set(join_node.
        right_vars.keys())
    yeweg__sihlc = tcgd__qdvra - aof__fgkws
    for egiy__hquat, llgt__oinkx in join_node.out_data_vars.items():
        if join_node.indicator and egiy__hquat == '_merge':
            continue
        if not egiy__hquat in join_node.column_origins:
            raise BodoError('join(): The variable ' + egiy__hquat +
                ' is absent from the output')
        ikqzr__qbwyj = join_node.column_origins[egiy__hquat]
        if ikqzr__qbwyj[0] == 'left':
            jmr__bvp = join_node.left_vars[ikqzr__qbwyj[1]]
        else:
            jmr__bvp = join_node.right_vars[ikqzr__qbwyj[1]]
        typeinferer.constraints.append(typeinfer.Propagate(dst=llgt__oinkx.
            name, src=jmr__bvp.name, loc=join_node.loc))
    return


typeinfer.typeinfer_extensions[Join] = join_typeinfer


def visit_vars_join(join_node, callback, cbdata):
    if debug_prints():
        print('visiting join vars for:', join_node)
        print('cbdata: ', sorted(cbdata.items()))
    for ibf__ptlv in list(join_node.left_vars.keys()):
        join_node.left_vars[ibf__ptlv] = visit_vars_inner(join_node.
            left_vars[ibf__ptlv], callback, cbdata)
    for ibf__ptlv in list(join_node.right_vars.keys()):
        join_node.right_vars[ibf__ptlv] = visit_vars_inner(join_node.
            right_vars[ibf__ptlv], callback, cbdata)
    for ibf__ptlv in list(join_node.out_data_vars.keys()):
        join_node.out_data_vars[ibf__ptlv] = visit_vars_inner(join_node.
            out_data_vars[ibf__ptlv], callback, cbdata)


ir_utils.visit_vars_extensions[Join] = visit_vars_join


def remove_dead_join(join_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    cgxze__bcn = []
    brkzc__neyhu = True
    for ibf__ptlv, jmr__bvp in join_node.out_data_vars.items():
        if jmr__bvp.name in lives:
            brkzc__neyhu = False
            continue
        if ibf__ptlv == '$_bodo_index_':
            continue
        if join_node.indicator and ibf__ptlv == '_merge':
            cgxze__bcn.append('_merge')
            join_node.indicator = False
            continue
        gljmu__nwnb, uge__sgn = join_node.column_origins[ibf__ptlv]
        if (gljmu__nwnb == 'left' and uge__sgn not in join_node.left_keys and
            uge__sgn not in join_node.left_cond_cols):
            join_node.left_vars.pop(uge__sgn)
            cgxze__bcn.append(ibf__ptlv)
        if (gljmu__nwnb == 'right' and uge__sgn not in join_node.right_keys and
            uge__sgn not in join_node.right_cond_cols):
            join_node.right_vars.pop(uge__sgn)
            cgxze__bcn.append(ibf__ptlv)
    for cname in cgxze__bcn:
        join_node.out_data_vars.pop(cname)
    if brkzc__neyhu:
        return None
    return join_node


ir_utils.remove_dead_extensions[Join] = remove_dead_join


def join_usedefs(join_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({lctd__rywb.name for lctd__rywb in join_node.left_vars.
        values()})
    use_set.update({lctd__rywb.name for lctd__rywb in join_node.right_vars.
        values()})
    def_set.update({lctd__rywb.name for lctd__rywb in join_node.
        out_data_vars.values()})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Join] = join_usedefs


def get_copies_join(join_node, typemap):
    jgi__zkuw = set(lctd__rywb.name for lctd__rywb in join_node.
        out_data_vars.values())
    return set(), jgi__zkuw


ir_utils.copy_propagate_extensions[Join] = get_copies_join


def apply_copies_join(join_node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    for ibf__ptlv in list(join_node.left_vars.keys()):
        join_node.left_vars[ibf__ptlv] = replace_vars_inner(join_node.
            left_vars[ibf__ptlv], var_dict)
    for ibf__ptlv in list(join_node.right_vars.keys()):
        join_node.right_vars[ibf__ptlv] = replace_vars_inner(join_node.
            right_vars[ibf__ptlv], var_dict)
    for ibf__ptlv in list(join_node.out_data_vars.keys()):
        join_node.out_data_vars[ibf__ptlv] = replace_vars_inner(join_node.
            out_data_vars[ibf__ptlv], var_dict)
    return


ir_utils.apply_copy_propagate_extensions[Join] = apply_copies_join


def build_join_definitions(join_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for jmr__bvp in join_node.out_data_vars.values():
        definitions[jmr__bvp.name].append(join_node)
    return definitions


ir_utils.build_defs_extensions[Join] = build_join_definitions


def join_distributed_run(join_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    left_parallel, right_parallel = False, False
    if array_dists is not None:
        left_parallel, right_parallel = _get_table_parallel_flags(join_node,
            array_dists)
    n_keys = len(join_node.left_keys)
    pyw__kgage = tuple(join_node.left_vars[aybi__hrxhr] for aybi__hrxhr in
        join_node.left_keys)
    bmdau__fbyie = tuple(join_node.right_vars[aybi__hrxhr] for aybi__hrxhr in
        join_node.right_keys)
    xvqd__vtvq = tuple(join_node.left_vars.keys())
    nfq__zhfr = tuple(join_node.right_vars.keys())
    bsaww__yzzpe = ()
    jdlv__kur = ()
    optional_column = False
    if (join_node.left_index and not join_node.right_index and not
        join_node.is_join):
        mesh__jvje = join_node.right_keys[0]
        if mesh__jvje in xvqd__vtvq:
            jdlv__kur = mesh__jvje,
            bsaww__yzzpe = join_node.right_vars[mesh__jvje],
            optional_column = True
    if (join_node.right_index and not join_node.left_index and not
        join_node.is_join):
        mesh__jvje = join_node.left_keys[0]
        if mesh__jvje in nfq__zhfr:
            jdlv__kur = mesh__jvje,
            bsaww__yzzpe = join_node.left_vars[mesh__jvje],
            optional_column = True
    pra__mmo = tuple(join_node.out_data_vars[cname] for cname in jdlv__kur)
    dvmbg__tjvb = tuple(lctd__rywb for lriq__dtg, lctd__rywb in sorted(
        join_node.left_vars.items(), key=lambda a: str(a[0])) if lriq__dtg
         not in join_node.left_keys)
    nuh__girjq = tuple(lctd__rywb for lriq__dtg, lctd__rywb in sorted(
        join_node.right_vars.items(), key=lambda a: str(a[0])) if lriq__dtg
         not in join_node.right_keys)
    hvvig__ysirr = (bsaww__yzzpe + pyw__kgage + bmdau__fbyie + dvmbg__tjvb +
        nuh__girjq)
    bpnqi__dae = tuple(typemap[lctd__rywb.name] for lctd__rywb in hvvig__ysirr)
    tgszm__dnj = tuple('opti_c' + str(pgaf__wwqds) for pgaf__wwqds in range
        (len(bsaww__yzzpe)))
    left_other_names = tuple('t1_c' + str(pgaf__wwqds) for pgaf__wwqds in
        range(len(dvmbg__tjvb)))
    right_other_names = tuple('t2_c' + str(pgaf__wwqds) for pgaf__wwqds in
        range(len(nuh__girjq)))
    left_other_types = tuple([typemap[aybi__hrxhr.name] for aybi__hrxhr in
        dvmbg__tjvb])
    right_other_types = tuple([typemap[aybi__hrxhr.name] for aybi__hrxhr in
        nuh__girjq])
    left_key_names = tuple('t1_key' + str(pgaf__wwqds) for pgaf__wwqds in
        range(n_keys))
    right_key_names = tuple('t2_key' + str(pgaf__wwqds) for pgaf__wwqds in
        range(n_keys))
    glbs = {}
    loc = join_node.loc
    func_text = 'def f({}{}, {},{}{}{}):\n'.format('{},'.format(tgszm__dnj[
        0]) if len(tgszm__dnj) == 1 else '', ','.join(left_key_names), ','.
        join(right_key_names), ','.join(left_other_names), ',' if len(
        left_other_names) != 0 else '', ','.join(right_other_names))
    left_key_types = tuple(typemap[lctd__rywb.name] for lctd__rywb in
        pyw__kgage)
    right_key_types = tuple(typemap[lctd__rywb.name] for lctd__rywb in
        bmdau__fbyie)
    for pgaf__wwqds in range(n_keys):
        glbs[f'key_type_{pgaf__wwqds}'] = _match_join_key_types(left_key_types
            [pgaf__wwqds], right_key_types[pgaf__wwqds], loc)
    func_text += '    t1_keys = ({},)\n'.format(', '.join(
        f'bodo.utils.utils.astype({left_key_names[pgaf__wwqds]}, key_type_{pgaf__wwqds})'
         for pgaf__wwqds in range(n_keys)))
    func_text += '    t2_keys = ({},)\n'.format(', '.join(
        f'bodo.utils.utils.astype({right_key_names[pgaf__wwqds]}, key_type_{pgaf__wwqds})'
         for pgaf__wwqds in range(n_keys)))
    func_text += '    data_left = ({}{})\n'.format(','.join(
        left_other_names), ',' if len(left_other_names) != 0 else '')
    func_text += '    data_right = ({}{})\n'.format(','.join(
        right_other_names), ',' if len(right_other_names) != 0 else '')
    ziq__awjo = []
    for cname in join_node.left_keys:
        if cname in join_node.add_suffix:
            arjc__ktjgs = str(cname) + join_node.suffix_x
        else:
            arjc__ktjgs = cname
        assert arjc__ktjgs in join_node.out_data_vars
        ziq__awjo.append(join_node.out_data_vars[arjc__ktjgs])
    for pgaf__wwqds, cname in enumerate(join_node.right_keys):
        if not join_node.vect_same_key[pgaf__wwqds] and not join_node.is_join:
            if cname in join_node.add_suffix:
                arjc__ktjgs = str(cname) + join_node.suffix_y
            else:
                arjc__ktjgs = cname
            assert arjc__ktjgs in join_node.out_data_vars
            ziq__awjo.append(join_node.out_data_vars[arjc__ktjgs])

    def _get_out_col_var(cname, is_left):
        if cname in join_node.add_suffix:
            if is_left:
                arjc__ktjgs = str(cname) + join_node.suffix_x
            else:
                arjc__ktjgs = str(cname) + join_node.suffix_y
        else:
            arjc__ktjgs = cname
        return join_node.out_data_vars[arjc__ktjgs]
    neem__qwri = pra__mmo + tuple(ziq__awjo)
    neem__qwri += tuple(_get_out_col_var(lriq__dtg, True) for lriq__dtg,
        lctd__rywb in sorted(join_node.left_vars.items(), key=lambda a: str
        (a[0])) if lriq__dtg not in join_node.left_keys)
    neem__qwri += tuple(_get_out_col_var(lriq__dtg, False) for lriq__dtg,
        lctd__rywb in sorted(join_node.right_vars.items(), key=lambda a:
        str(a[0])) if lriq__dtg not in join_node.right_keys)
    if join_node.indicator:
        neem__qwri += _get_out_col_var('_merge', False),
    qzas__ayqmp = [('t3_c' + str(pgaf__wwqds)) for pgaf__wwqds in range(len
        (neem__qwri))]
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
            right_parallel, glbs, [typemap[lctd__rywb.name] for lctd__rywb in
            neem__qwri], join_node.loc, join_node.indicator, join_node.
            is_na_equal, general_cond_cfunc, left_col_nums, right_col_nums)
    if join_node.how == 'asof':
        for pgaf__wwqds in range(len(left_other_names)):
            func_text += '    left_{} = out_data_left[{}]\n'.format(pgaf__wwqds
                , pgaf__wwqds)
        for pgaf__wwqds in range(len(right_other_names)):
            func_text += '    right_{} = out_data_right[{}]\n'.format(
                pgaf__wwqds, pgaf__wwqds)
        for pgaf__wwqds in range(n_keys):
            func_text += (
                f'    t1_keys_{pgaf__wwqds} = out_t1_keys[{pgaf__wwqds}]\n')
        for pgaf__wwqds in range(n_keys):
            func_text += (
                f'    t2_keys_{pgaf__wwqds} = out_t2_keys[{pgaf__wwqds}]\n')
    idx = 0
    if optional_column:
        func_text += f'    {qzas__ayqmp[idx]} = opti_0\n'
        idx += 1
    for pgaf__wwqds in range(n_keys):
        func_text += f'    {qzas__ayqmp[idx]} = t1_keys_{pgaf__wwqds}\n'
        idx += 1
    for pgaf__wwqds in range(n_keys):
        if not join_node.vect_same_key[pgaf__wwqds] and not join_node.is_join:
            func_text += f'    {qzas__ayqmp[idx]} = t2_keys_{pgaf__wwqds}\n'
            idx += 1
    for pgaf__wwqds in range(len(left_other_names)):
        func_text += f'    {qzas__ayqmp[idx]} = left_{pgaf__wwqds}\n'
        idx += 1
    for pgaf__wwqds in range(len(right_other_names)):
        func_text += f'    {qzas__ayqmp[idx]} = right_{pgaf__wwqds}\n'
        idx += 1
    if join_node.indicator:
        func_text += f'    {qzas__ayqmp[idx]} = indicator_col\n'
        idx += 1
    rfp__bvf = {}
    exec(func_text, {}, rfp__bvf)
    lsfwp__atd = rfp__bvf['f']
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
    duczq__qyaac = compile_to_numba_ir(lsfwp__atd, glbs, typingctx=
        typingctx, targetctx=targetctx, arg_typs=bpnqi__dae, typemap=
        typemap, calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(duczq__qyaac, hvvig__ysirr)
    rtk__vhv = duczq__qyaac.body[:-3]
    for pgaf__wwqds in range(len(neem__qwri)):
        rtk__vhv[-len(neem__qwri) + pgaf__wwqds].target = neem__qwri[
            pgaf__wwqds]
    return rtk__vhv


distributed_pass.distributed_run_extensions[Join] = join_distributed_run


def _gen_general_cond_cfunc(join_node, typemap):
    expr = join_node.gen_cond_expr
    if not expr:
        return None, [], []
    iir__tuc = next_label()
    qfbx__dzkw = _get_col_to_ind(join_node.left_keys, join_node.left_vars)
    wbo__duymy = _get_col_to_ind(join_node.right_keys, join_node.right_vars)
    table_getitem_funcs = {'bodo': bodo, 'numba': numba, 'is_null_pointer':
        is_null_pointer}
    na_check_name = 'NOT_NA'
    func_text = f"""def bodo_join_gen_cond{iir__tuc}(left_table, right_table, left_data1, right_data1, left_null_bitmap, right_null_bitmap, left_ind, right_ind):
"""
    func_text += '  if is_null_pointer(left_table):\n'
    func_text += '    return False\n'
    expr, func_text, left_col_nums = _replace_column_accesses(expr,
        qfbx__dzkw, typemap, join_node.left_vars, table_getitem_funcs,
        func_text, 'left', len(join_node.left_keys), na_check_name)
    expr, func_text, right_col_nums = _replace_column_accesses(expr,
        wbo__duymy, typemap, join_node.right_vars, table_getitem_funcs,
        func_text, 'right', len(join_node.right_keys), na_check_name)
    func_text += f'  return {expr}'
    rfp__bvf = {}
    exec(func_text, table_getitem_funcs, rfp__bvf)
    sxhv__rdkzk = rfp__bvf[f'bodo_join_gen_cond{iir__tuc}']
    tutob__oio = types.bool_(types.voidptr, types.voidptr, types.voidptr,
        types.voidptr, types.voidptr, types.voidptr, types.int64, types.int64)
    hfqoe__smbx = numba.cfunc(tutob__oio, nopython=True)(sxhv__rdkzk)
    join_gen_cond_cfunc[hfqoe__smbx.native_name] = hfqoe__smbx
    join_gen_cond_cfunc_addr[hfqoe__smbx.native_name] = hfqoe__smbx.address
    return hfqoe__smbx, left_col_nums, right_col_nums


def _replace_column_accesses(expr, col_to_ind, typemap, col_vars,
    table_getitem_funcs, func_text, table_name, n_keys, na_check_name):
    axc__skesp = []
    for aybi__hrxhr, kqa__tio in col_to_ind.items():
        cname = f'({table_name}.{aybi__hrxhr})'
        if cname not in expr:
            continue
        vwir__tlk = f'getitem_{table_name}_val_{kqa__tio}'
        zsvkf__yenl = f'_bodo_{table_name}_val_{kqa__tio}'
        wcd__nun = typemap[col_vars[aybi__hrxhr].name]
        if is_str_arr_type(wcd__nun):
            func_text += f"""  {zsvkf__yenl}, {zsvkf__yenl}_size = {vwir__tlk}({table_name}_table, {table_name}_ind)
"""
            func_text += f"""  {zsvkf__yenl} = bodo.libs.str_arr_ext.decode_utf8({zsvkf__yenl}, {zsvkf__yenl}_size)
"""
        else:
            func_text += (
                f'  {zsvkf__yenl} = {vwir__tlk}({table_name}_data1, {table_name}_ind)\n'
                )
        table_getitem_funcs[vwir__tlk
            ] = bodo.libs.array._gen_row_access_intrinsic(wcd__nun, kqa__tio)
        expr = expr.replace(cname, zsvkf__yenl)
        hpijo__tleki = f'({na_check_name}.{table_name}.{aybi__hrxhr})'
        if hpijo__tleki in expr:
            vrg__cjnxv = f'nacheck_{table_name}_val_{kqa__tio}'
            ruxmg__opd = f'_bodo_isna_{table_name}_val_{kqa__tio}'
            if (isinstance(wcd__nun, bodo.libs.int_arr_ext.IntegerArrayType
                ) or wcd__nun == bodo.libs.bool_arr_ext.boolean_array or
                is_str_arr_type(wcd__nun)):
                func_text += f"""  {ruxmg__opd} = {vrg__cjnxv}({table_name}_null_bitmap, {table_name}_ind)
"""
            else:
                func_text += f"""  {ruxmg__opd} = {vrg__cjnxv}({table_name}_data1, {table_name}_ind)
"""
            table_getitem_funcs[vrg__cjnxv
                ] = bodo.libs.array._gen_row_na_check_intrinsic(wcd__nun,
                kqa__tio)
            expr = expr.replace(hpijo__tleki, ruxmg__opd)
        if kqa__tio >= n_keys:
            axc__skesp.append(kqa__tio)
    return expr, func_text, axc__skesp


def _get_col_to_ind(key_names, col_vars):
    n_keys = len(key_names)
    col_to_ind = {aybi__hrxhr: pgaf__wwqds for pgaf__wwqds, aybi__hrxhr in
        enumerate(key_names)}
    pgaf__wwqds = n_keys
    for aybi__hrxhr in sorted(col_vars, key=lambda a: str(a)):
        if aybi__hrxhr in key_names:
            continue
        col_to_ind[aybi__hrxhr] = pgaf__wwqds
        pgaf__wwqds += 1
    return col_to_ind


def _match_join_key_types(t1, t2, loc):
    if t1 == t2:
        return t1
    try:
        arr = dtype_to_array_type(find_common_np_dtype([t1, t2]))
        return to_nullable_type(arr) if is_nullable_type(t1
            ) or is_nullable_type(t2) else arr
    except Exception as jlxao__wskl:
        if is_str_arr_type(t1) and is_str_arr_type(t2):
            return bodo.string_array_type
        raise BodoError(f'Join key types {t1} and {t2} do not match', loc=loc)


def _get_table_parallel_flags(join_node, array_dists):
    dqonh__efper = (distributed_pass.Distribution.OneD, distributed_pass.
        Distribution.OneD_Var)
    left_parallel = all(array_dists[lctd__rywb.name] in dqonh__efper for
        lctd__rywb in join_node.left_vars.values())
    right_parallel = all(array_dists[lctd__rywb.name] in dqonh__efper for
        lctd__rywb in join_node.right_vars.values())
    if not left_parallel:
        assert not any(array_dists[lctd__rywb.name] in dqonh__efper for
            lctd__rywb in join_node.left_vars.values())
    if not right_parallel:
        assert not any(array_dists[lctd__rywb.name] in dqonh__efper for
            lctd__rywb in join_node.right_vars.values())
    if left_parallel or right_parallel:
        assert all(array_dists[lctd__rywb.name] in dqonh__efper for
            lctd__rywb in join_node.out_data_vars.values())
    return left_parallel, right_parallel


def _gen_local_hash_join(optional_column, left_key_names, right_key_names,
    left_key_types, right_key_types, left_other_names, right_other_names,
    left_other_types, right_other_types, vect_same_key, is_left, is_right,
    is_join, left_parallel, right_parallel, glbs, out_types, loc, indicator,
    is_na_equal, general_cond_cfunc, left_col_nums, right_col_nums):

    def needs_typechange(in_type, need_nullable, is_same_key):
        return isinstance(in_type, types.Array) and not is_dtype_nullable(
            in_type.dtype) and need_nullable and not is_same_key
    mxjy__fufvv = []
    for pgaf__wwqds in range(len(left_key_names)):
        zoxn__hfh = _match_join_key_types(left_key_types[pgaf__wwqds],
            right_key_types[pgaf__wwqds], loc)
        mxjy__fufvv.append(needs_typechange(zoxn__hfh, is_right,
            vect_same_key[pgaf__wwqds]))
    for pgaf__wwqds in range(len(left_other_names)):
        mxjy__fufvv.append(needs_typechange(left_other_types[pgaf__wwqds],
            is_right, False))
    for pgaf__wwqds in range(len(right_key_names)):
        if not vect_same_key[pgaf__wwqds] and not is_join:
            zoxn__hfh = _match_join_key_types(left_key_types[pgaf__wwqds],
                right_key_types[pgaf__wwqds], loc)
            mxjy__fufvv.append(needs_typechange(zoxn__hfh, is_left, False))
    for pgaf__wwqds in range(len(right_other_names)):
        mxjy__fufvv.append(needs_typechange(right_other_types[pgaf__wwqds],
            is_left, False))

    def get_out_type(idx, in_type, in_name, need_nullable, is_same_key):
        if isinstance(in_type, types.Array) and not is_dtype_nullable(in_type
            .dtype) and need_nullable and not is_same_key:
            if isinstance(in_type.dtype, types.Integer):
                uzjgq__cgxa = IntDtype(in_type.dtype).name
                assert uzjgq__cgxa.endswith('Dtype()')
                uzjgq__cgxa = uzjgq__cgxa[:-7]
                bxfaz__oue = f"""    typ_{idx} = bodo.hiframes.pd_series_ext.get_series_data(pd.Series([1], dtype="{uzjgq__cgxa}"))
"""
                mzc__djb = f'typ_{idx}'
            else:
                assert in_type.dtype == types.bool_, 'unexpected non-nullable type in join'
                bxfaz__oue = (
                    f'    typ_{idx} = bodo.libs.bool_arr_ext.alloc_bool_array(1)\n'
                    )
                mzc__djb = f'typ_{idx}'
        elif in_type == bodo.string_array_type:
            bxfaz__oue = (
                f'    typ_{idx} = bodo.libs.str_arr_ext.pre_alloc_string_array(0, 0)\n'
                )
            mzc__djb = f'typ_{idx}'
        else:
            bxfaz__oue = ''
            mzc__djb = in_name
        return bxfaz__oue, mzc__djb
    n_keys = len(left_key_names)
    func_text = '    # beginning of _gen_local_hash_join\n'
    lwzue__bvmw = []
    for pgaf__wwqds in range(n_keys):
        lwzue__bvmw.append('t1_keys[{}]'.format(pgaf__wwqds))
    for pgaf__wwqds in range(len(left_other_names)):
        lwzue__bvmw.append('data_left[{}]'.format(pgaf__wwqds))
    func_text += '    info_list_total_l = [{}]\n'.format(','.join(
        'array_to_info({})'.format(a) for a in lwzue__bvmw))
    func_text += '    table_left = arr_info_list_to_table(info_list_total_l)\n'
    kvjft__lghq = []
    for pgaf__wwqds in range(n_keys):
        kvjft__lghq.append('t2_keys[{}]'.format(pgaf__wwqds))
    for pgaf__wwqds in range(len(right_other_names)):
        kvjft__lghq.append('data_right[{}]'.format(pgaf__wwqds))
    func_text += '    info_list_total_r = [{}]\n'.format(','.join(
        'array_to_info({})'.format(a) for a in kvjft__lghq))
    func_text += (
        '    table_right = arr_info_list_to_table(info_list_total_r)\n')
    func_text += '    vect_same_key = np.array([{}])\n'.format(','.join('1' if
        qvamv__hjo else '0' for qvamv__hjo in vect_same_key))
    func_text += '    vect_need_typechange = np.array([{}])\n'.format(','.
        join('1' if qvamv__hjo else '0' for qvamv__hjo in mxjy__fufvv))
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
        mfm__qanx = get_out_type(idx, out_types[idx], 'opti_c0', False, False)
        func_text += mfm__qanx[0]
        glbs[f'out_type_{idx}'] = out_types[idx]
        func_text += f"""    opti_0 = info_to_array(info_from_table(out_table, {idx}), {mfm__qanx[1]})
"""
        idx += 1
    for pgaf__wwqds, gjbrt__ewkc in enumerate(left_key_names):
        zoxn__hfh = _match_join_key_types(left_key_types[pgaf__wwqds],
            right_key_types[pgaf__wwqds], loc)
        mfm__qanx = get_out_type(idx, zoxn__hfh, f't1_keys[{pgaf__wwqds}]',
            is_right, vect_same_key[pgaf__wwqds])
        func_text += mfm__qanx[0]
        glbs[f'out_type_{idx}'] = out_types[idx]
        if zoxn__hfh != left_key_types[pgaf__wwqds] and left_key_types[
            pgaf__wwqds] != bodo.dict_str_arr_type:
            func_text += f"""    t1_keys_{pgaf__wwqds} = bodo.utils.utils.astype(info_to_array(info_from_table(out_table, {idx}), {mfm__qanx[1]}), out_type_{idx})
"""
        else:
            func_text += f"""    t1_keys_{pgaf__wwqds} = info_to_array(info_from_table(out_table, {idx}), {mfm__qanx[1]})
"""
        idx += 1
    for pgaf__wwqds, gjbrt__ewkc in enumerate(left_other_names):
        mfm__qanx = get_out_type(idx, left_other_types[pgaf__wwqds],
            gjbrt__ewkc, is_right, False)
        func_text += mfm__qanx[0]
        func_text += (
            '    left_{} = info_to_array(info_from_table(out_table, {}), {})\n'
            .format(pgaf__wwqds, idx, mfm__qanx[1]))
        idx += 1
    for pgaf__wwqds, gjbrt__ewkc in enumerate(right_key_names):
        if not vect_same_key[pgaf__wwqds] and not is_join:
            zoxn__hfh = _match_join_key_types(left_key_types[pgaf__wwqds],
                right_key_types[pgaf__wwqds], loc)
            mfm__qanx = get_out_type(idx, zoxn__hfh,
                f't2_keys[{pgaf__wwqds}]', is_left, False)
            func_text += mfm__qanx[0]
            glbs[f'out_type_{idx}'] = out_types[idx - len(left_other_names)]
            if zoxn__hfh != right_key_types[pgaf__wwqds] and right_key_types[
                pgaf__wwqds] != bodo.dict_str_arr_type:
                func_text += f"""    t2_keys_{pgaf__wwqds} = bodo.utils.utils.astype(info_to_array(info_from_table(out_table, {idx}), {mfm__qanx[1]}), out_type_{idx})
"""
            else:
                func_text += f"""    t2_keys_{pgaf__wwqds} = info_to_array(info_from_table(out_table, {idx}), {mfm__qanx[1]})
"""
            idx += 1
    for pgaf__wwqds, gjbrt__ewkc in enumerate(right_other_names):
        mfm__qanx = get_out_type(idx, right_other_types[pgaf__wwqds],
            gjbrt__ewkc, is_left, False)
        func_text += mfm__qanx[0]
        func_text += (
            '    right_{} = info_to_array(info_from_table(out_table, {}), {})\n'
            .format(pgaf__wwqds, idx, mfm__qanx[1]))
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
    zwol__zrii = bodo.libs.distributed_api.get_size()
    trtps__sig = np.empty(zwol__zrii, left_key_arrs[0].dtype)
    cmdbd__saybk = np.empty(zwol__zrii, left_key_arrs[0].dtype)
    bodo.libs.distributed_api.allgather(trtps__sig, left_key_arrs[0][0])
    bodo.libs.distributed_api.allgather(cmdbd__saybk, left_key_arrs[0][-1])
    rpa__ody = np.zeros(zwol__zrii, np.int32)
    lpgc__oiy = np.zeros(zwol__zrii, np.int32)
    rmb__smxmp = np.zeros(zwol__zrii, np.int32)
    yuzu__gzo = right_key_arrs[0][0]
    ymi__cba = right_key_arrs[0][-1]
    weblj__rsgb = -1
    pgaf__wwqds = 0
    while pgaf__wwqds < zwol__zrii - 1 and cmdbd__saybk[pgaf__wwqds
        ] < yuzu__gzo:
        pgaf__wwqds += 1
    while pgaf__wwqds < zwol__zrii and trtps__sig[pgaf__wwqds] <= ymi__cba:
        weblj__rsgb, qvn__eim = _count_overlap(right_key_arrs[0],
            trtps__sig[pgaf__wwqds], cmdbd__saybk[pgaf__wwqds])
        if weblj__rsgb != 0:
            weblj__rsgb -= 1
            qvn__eim += 1
        rpa__ody[pgaf__wwqds] = qvn__eim
        lpgc__oiy[pgaf__wwqds] = weblj__rsgb
        pgaf__wwqds += 1
    while pgaf__wwqds < zwol__zrii:
        rpa__ody[pgaf__wwqds] = 1
        lpgc__oiy[pgaf__wwqds] = len(right_key_arrs[0]) - 1
        pgaf__wwqds += 1
    bodo.libs.distributed_api.alltoall(rpa__ody, rmb__smxmp, 1)
    wqgo__fsz = rmb__smxmp.sum()
    eda__yyr = np.empty(wqgo__fsz, right_key_arrs[0].dtype)
    jcpy__ldevq = alloc_arr_tup(wqgo__fsz, right_data)
    oubnf__vpk = bodo.ir.join.calc_disp(rmb__smxmp)
    bodo.libs.distributed_api.alltoallv(right_key_arrs[0], eda__yyr,
        rpa__ody, rmb__smxmp, lpgc__oiy, oubnf__vpk)
    bodo.libs.distributed_api.alltoallv_tup(right_data, jcpy__ldevq,
        rpa__ody, rmb__smxmp, lpgc__oiy, oubnf__vpk)
    return (eda__yyr,), jcpy__ldevq


@numba.njit
def _count_overlap(r_key_arr, start, end):
    qvn__eim = 0
    weblj__rsgb = 0
    qsec__lwyp = 0
    while qsec__lwyp < len(r_key_arr) and r_key_arr[qsec__lwyp] < start:
        weblj__rsgb += 1
        qsec__lwyp += 1
    while qsec__lwyp < len(r_key_arr) and start <= r_key_arr[qsec__lwyp
        ] <= end:
        qsec__lwyp += 1
        qvn__eim += 1
    return weblj__rsgb, qvn__eim


import llvmlite.binding as ll
from bodo.libs import hdist
ll.add_symbol('c_alltoallv', hdist.c_alltoallv)


@numba.njit
def calc_disp(arr):
    zgh__czgz = np.empty_like(arr)
    zgh__czgz[0] = 0
    for pgaf__wwqds in range(1, len(arr)):
        zgh__czgz[pgaf__wwqds] = zgh__czgz[pgaf__wwqds - 1] + arr[
            pgaf__wwqds - 1]
    return zgh__czgz


@numba.njit
def local_merge_asof(left_keys, right_keys, data_left, data_right):
    dyn__yscar = len(left_keys[0])
    eif__rjlqa = len(right_keys[0])
    mms__jmqkf = alloc_arr_tup(dyn__yscar, left_keys)
    kadc__juzm = alloc_arr_tup(dyn__yscar, right_keys)
    kwqgc__woxju = alloc_arr_tup(dyn__yscar, data_left)
    aocwt__zazd = alloc_arr_tup(dyn__yscar, data_right)
    eic__fnkg = 0
    zsjts__bycqg = 0
    for eic__fnkg in range(dyn__yscar):
        if zsjts__bycqg < 0:
            zsjts__bycqg = 0
        while zsjts__bycqg < eif__rjlqa and getitem_arr_tup(right_keys,
            zsjts__bycqg) <= getitem_arr_tup(left_keys, eic__fnkg):
            zsjts__bycqg += 1
        zsjts__bycqg -= 1
        setitem_arr_tup(mms__jmqkf, eic__fnkg, getitem_arr_tup(left_keys,
            eic__fnkg))
        setitem_arr_tup(kwqgc__woxju, eic__fnkg, getitem_arr_tup(data_left,
            eic__fnkg))
        if zsjts__bycqg >= 0:
            setitem_arr_tup(kadc__juzm, eic__fnkg, getitem_arr_tup(
                right_keys, zsjts__bycqg))
            setitem_arr_tup(aocwt__zazd, eic__fnkg, getitem_arr_tup(
                data_right, zsjts__bycqg))
        else:
            bodo.libs.array_kernels.setna_tup(kadc__juzm, eic__fnkg)
            bodo.libs.array_kernels.setna_tup(aocwt__zazd, eic__fnkg)
    return mms__jmqkf, kadc__juzm, kwqgc__woxju, aocwt__zazd


def copy_arr_tup(arrs):
    return tuple(a.copy() for a in arrs)


@overload(copy_arr_tup, no_unliteral=True)
def copy_arr_tup_overload(arrs):
    qvn__eim = arrs.count
    func_text = 'def f(arrs):\n'
    func_text += '  return ({},)\n'.format(','.join('arrs[{}].copy()'.
        format(pgaf__wwqds) for pgaf__wwqds in range(qvn__eim)))
    rfp__bvf = {}
    exec(func_text, {}, rfp__bvf)
    flfv__gofha = rfp__bvf['f']
    return flfv__gofha
