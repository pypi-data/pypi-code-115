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
        ieq__pccq = func.signature
        skpg__rloz = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64), lir
            .IntType(64)])
        onj__jukcn = cgutils.get_or_insert_function(builder.module,
            skpg__rloz, sym._literal_value)
        builder.call(onj__jukcn, [context.get_constant_null(ieq__pccq.args[
            0]), context.get_constant_null(ieq__pccq.args[1]), context.
            get_constant_null(ieq__pccq.args[2]), context.get_constant_null
            (ieq__pccq.args[3]), context.get_constant_null(ieq__pccq.args[4
            ]), context.get_constant_null(ieq__pccq.args[5]), context.
            get_constant(types.int64, 0), context.get_constant(types.int64, 0)]
            )
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
        self.left_cond_cols = set(rxx__nrko for rxx__nrko in left_vars.keys
            () if f'(left.{rxx__nrko})' in gen_cond_expr)
        self.right_cond_cols = set(rxx__nrko for rxx__nrko in right_vars.
            keys() if f'(right.{rxx__nrko})' in gen_cond_expr)
        nvk__mist = set(left_keys) & set(right_keys)
        ivl__xkrmo = set(left_vars.keys()) & set(right_vars.keys())
        tbq__rab = ivl__xkrmo - nvk__mist
        vect_same_key = []
        n_keys = len(left_keys)
        for hxsjw__fcx in range(n_keys):
            abdl__ozyk = left_keys[hxsjw__fcx]
            eyae__ymusy = right_keys[hxsjw__fcx]
            vect_same_key.append(abdl__ozyk == eyae__ymusy)
        self.vect_same_key = vect_same_key
        self.column_origins = {(str(rxx__nrko) + suffix_x if rxx__nrko in
            tbq__rab else rxx__nrko): ('left', rxx__nrko) for rxx__nrko in
            left_vars.keys()}
        self.column_origins.update({(str(rxx__nrko) + suffix_y if rxx__nrko in
            tbq__rab else rxx__nrko): ('right', rxx__nrko) for rxx__nrko in
            right_vars.keys()})
        if '$_bodo_index_' in tbq__rab:
            tbq__rab.remove('$_bodo_index_')
        self.add_suffix = tbq__rab

    def __repr__(self):
        bzv__rwip = ''
        for rxx__nrko, lano__ser in self.out_data_vars.items():
            bzv__rwip += "'{}':{}, ".format(rxx__nrko, lano__ser.name)
        xny__ufeje = '{}{{{}}}'.format(self.df_out, bzv__rwip)
        zen__jaqvt = ''
        for rxx__nrko, lano__ser in self.left_vars.items():
            zen__jaqvt += "'{}':{}, ".format(rxx__nrko, lano__ser.name)
        ynqi__tza = '{}{{{}}}'.format(self.left_df, zen__jaqvt)
        zen__jaqvt = ''
        for rxx__nrko, lano__ser in self.right_vars.items():
            zen__jaqvt += "'{}':{}, ".format(rxx__nrko, lano__ser.name)
        yybaw__yqa = '{}{{{}}}'.format(self.right_df, zen__jaqvt)
        return 'join [{}={}]: {} , {}, {}'.format(self.left_keys, self.
            right_keys, xny__ufeje, ynqi__tza, yybaw__yqa)


def join_array_analysis(join_node, equiv_set, typemap, array_analysis):
    ooprx__qohkk = []
    assert len(join_node.out_data_vars) > 0, 'empty join in array analysis'
    nex__nzz = []
    amziw__hawi = list(join_node.left_vars.values())
    for llgxn__szw in amziw__hawi:
        mnf__pom = typemap[llgxn__szw.name]
        czn__kep = equiv_set.get_shape(llgxn__szw)
        if czn__kep:
            nex__nzz.append(czn__kep[0])
    if len(nex__nzz) > 1:
        equiv_set.insert_equiv(*nex__nzz)
    nex__nzz = []
    amziw__hawi = list(join_node.right_vars.values())
    for llgxn__szw in amziw__hawi:
        mnf__pom = typemap[llgxn__szw.name]
        czn__kep = equiv_set.get_shape(llgxn__szw)
        if czn__kep:
            nex__nzz.append(czn__kep[0])
    if len(nex__nzz) > 1:
        equiv_set.insert_equiv(*nex__nzz)
    nex__nzz = []
    for llgxn__szw in join_node.out_data_vars.values():
        mnf__pom = typemap[llgxn__szw.name]
        azqhp__wkn = array_analysis._gen_shape_call(equiv_set, llgxn__szw,
            mnf__pom.ndim, None, ooprx__qohkk)
        equiv_set.insert_equiv(llgxn__szw, azqhp__wkn)
        nex__nzz.append(azqhp__wkn[0])
        equiv_set.define(llgxn__szw, set())
    if len(nex__nzz) > 1:
        equiv_set.insert_equiv(*nex__nzz)
    return [], ooprx__qohkk


numba.parfors.array_analysis.array_analysis_extensions[Join
    ] = join_array_analysis


def join_distributed_analysis(join_node, array_dists):
    jcou__blkzr = Distribution.OneD
    cddq__ciksh = Distribution.OneD
    for llgxn__szw in join_node.left_vars.values():
        jcou__blkzr = Distribution(min(jcou__blkzr.value, array_dists[
            llgxn__szw.name].value))
    for llgxn__szw in join_node.right_vars.values():
        cddq__ciksh = Distribution(min(cddq__ciksh.value, array_dists[
            llgxn__szw.name].value))
    zgh__mxmf = Distribution.OneD_Var
    for llgxn__szw in join_node.out_data_vars.values():
        if llgxn__szw.name in array_dists:
            zgh__mxmf = Distribution(min(zgh__mxmf.value, array_dists[
                llgxn__szw.name].value))
    ukej__yrkld = Distribution(min(zgh__mxmf.value, jcou__blkzr.value))
    fjecn__rqmir = Distribution(min(zgh__mxmf.value, cddq__ciksh.value))
    zgh__mxmf = Distribution(max(ukej__yrkld.value, fjecn__rqmir.value))
    for llgxn__szw in join_node.out_data_vars.values():
        array_dists[llgxn__szw.name] = zgh__mxmf
    if zgh__mxmf != Distribution.OneD_Var:
        jcou__blkzr = zgh__mxmf
        cddq__ciksh = zgh__mxmf
    for llgxn__szw in join_node.left_vars.values():
        array_dists[llgxn__szw.name] = jcou__blkzr
    for llgxn__szw in join_node.right_vars.values():
        array_dists[llgxn__szw.name] = cddq__ciksh
    return


distributed_analysis.distributed_analysis_extensions[Join
    ] = join_distributed_analysis


def join_typeinfer(join_node, typeinferer):
    nvk__mist = set(join_node.left_keys) & set(join_node.right_keys)
    ivl__xkrmo = set(join_node.left_vars.keys()) & set(join_node.right_vars
        .keys())
    tbq__rab = ivl__xkrmo - nvk__mist
    for tdei__ugcp, ypx__ebtr in join_node.out_data_vars.items():
        if join_node.indicator and tdei__ugcp == '_merge':
            continue
        if not tdei__ugcp in join_node.column_origins:
            raise BodoError('join(): The variable ' + tdei__ugcp +
                ' is absent from the output')
        yel__zlns = join_node.column_origins[tdei__ugcp]
        if yel__zlns[0] == 'left':
            llgxn__szw = join_node.left_vars[yel__zlns[1]]
        else:
            llgxn__szw = join_node.right_vars[yel__zlns[1]]
        typeinferer.constraints.append(typeinfer.Propagate(dst=ypx__ebtr.
            name, src=llgxn__szw.name, loc=join_node.loc))
    return


typeinfer.typeinfer_extensions[Join] = join_typeinfer


def visit_vars_join(join_node, callback, cbdata):
    if debug_prints():
        print('visiting join vars for:', join_node)
        print('cbdata: ', sorted(cbdata.items()))
    for hxfsf__jwc in list(join_node.left_vars.keys()):
        join_node.left_vars[hxfsf__jwc] = visit_vars_inner(join_node.
            left_vars[hxfsf__jwc], callback, cbdata)
    for hxfsf__jwc in list(join_node.right_vars.keys()):
        join_node.right_vars[hxfsf__jwc] = visit_vars_inner(join_node.
            right_vars[hxfsf__jwc], callback, cbdata)
    for hxfsf__jwc in list(join_node.out_data_vars.keys()):
        join_node.out_data_vars[hxfsf__jwc] = visit_vars_inner(join_node.
            out_data_vars[hxfsf__jwc], callback, cbdata)


ir_utils.visit_vars_extensions[Join] = visit_vars_join


def remove_dead_join(join_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    xbau__qjvj = []
    dkxsr__qyyig = True
    for hxfsf__jwc, llgxn__szw in join_node.out_data_vars.items():
        if llgxn__szw.name in lives:
            dkxsr__qyyig = False
            continue
        if hxfsf__jwc == '$_bodo_index_':
            continue
        if join_node.indicator and hxfsf__jwc == '_merge':
            xbau__qjvj.append('_merge')
            join_node.indicator = False
            continue
        otcey__eazfr, zhjc__nnazu = join_node.column_origins[hxfsf__jwc]
        if (otcey__eazfr == 'left' and zhjc__nnazu not in join_node.
            left_keys and zhjc__nnazu not in join_node.left_cond_cols):
            join_node.left_vars.pop(zhjc__nnazu)
            xbau__qjvj.append(hxfsf__jwc)
        if (otcey__eazfr == 'right' and zhjc__nnazu not in join_node.
            right_keys and zhjc__nnazu not in join_node.right_cond_cols):
            join_node.right_vars.pop(zhjc__nnazu)
            xbau__qjvj.append(hxfsf__jwc)
    for cname in xbau__qjvj:
        join_node.out_data_vars.pop(cname)
    if dkxsr__qyyig:
        return None
    return join_node


ir_utils.remove_dead_extensions[Join] = remove_dead_join


def join_usedefs(join_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({lano__ser.name for lano__ser in join_node.left_vars.
        values()})
    use_set.update({lano__ser.name for lano__ser in join_node.right_vars.
        values()})
    def_set.update({lano__ser.name for lano__ser in join_node.out_data_vars
        .values()})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Join] = join_usedefs


def get_copies_join(join_node, typemap):
    knqdf__bqe = set(lano__ser.name for lano__ser in join_node.
        out_data_vars.values())
    return set(), knqdf__bqe


ir_utils.copy_propagate_extensions[Join] = get_copies_join


def apply_copies_join(join_node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    for hxfsf__jwc in list(join_node.left_vars.keys()):
        join_node.left_vars[hxfsf__jwc] = replace_vars_inner(join_node.
            left_vars[hxfsf__jwc], var_dict)
    for hxfsf__jwc in list(join_node.right_vars.keys()):
        join_node.right_vars[hxfsf__jwc] = replace_vars_inner(join_node.
            right_vars[hxfsf__jwc], var_dict)
    for hxfsf__jwc in list(join_node.out_data_vars.keys()):
        join_node.out_data_vars[hxfsf__jwc] = replace_vars_inner(join_node.
            out_data_vars[hxfsf__jwc], var_dict)
    return


ir_utils.apply_copy_propagate_extensions[Join] = apply_copies_join


def build_join_definitions(join_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for llgxn__szw in join_node.out_data_vars.values():
        definitions[llgxn__szw.name].append(join_node)
    return definitions


ir_utils.build_defs_extensions[Join] = build_join_definitions


def join_distributed_run(join_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    left_parallel, right_parallel = False, False
    if array_dists is not None:
        left_parallel, right_parallel = _get_table_parallel_flags(join_node,
            array_dists)
    n_keys = len(join_node.left_keys)
    akqz__bqunk = tuple(join_node.left_vars[rxx__nrko] for rxx__nrko in
        join_node.left_keys)
    pfi__ksr = tuple(join_node.right_vars[rxx__nrko] for rxx__nrko in
        join_node.right_keys)
    kfg__yjgln = tuple(join_node.left_vars.keys())
    rhsqu__cgoo = tuple(join_node.right_vars.keys())
    tgl__binb = ()
    zegov__jld = ()
    optional_column = False
    if (join_node.left_index and not join_node.right_index and not
        join_node.is_join):
        ykjvx__lhr = join_node.right_keys[0]
        if ykjvx__lhr in kfg__yjgln:
            zegov__jld = ykjvx__lhr,
            tgl__binb = join_node.right_vars[ykjvx__lhr],
            optional_column = True
    if (join_node.right_index and not join_node.left_index and not
        join_node.is_join):
        ykjvx__lhr = join_node.left_keys[0]
        if ykjvx__lhr in rhsqu__cgoo:
            zegov__jld = ykjvx__lhr,
            tgl__binb = join_node.left_vars[ykjvx__lhr],
            optional_column = True
    bau__pdukw = tuple(join_node.out_data_vars[cname] for cname in zegov__jld)
    hugex__nbmf = tuple(lano__ser for suqq__oqg, lano__ser in sorted(
        join_node.left_vars.items(), key=lambda a: str(a[0])) if suqq__oqg
         not in join_node.left_keys)
    lxyc__oju = tuple(lano__ser for suqq__oqg, lano__ser in sorted(
        join_node.right_vars.items(), key=lambda a: str(a[0])) if suqq__oqg
         not in join_node.right_keys)
    qanw__rkkq = tgl__binb + akqz__bqunk + pfi__ksr + hugex__nbmf + lxyc__oju
    xvh__ekng = tuple(typemap[lano__ser.name] for lano__ser in qanw__rkkq)
    xby__jimzo = tuple('opti_c' + str(cen__zpx) for cen__zpx in range(len(
        tgl__binb)))
    left_other_names = tuple('t1_c' + str(cen__zpx) for cen__zpx in range(
        len(hugex__nbmf)))
    right_other_names = tuple('t2_c' + str(cen__zpx) for cen__zpx in range(
        len(lxyc__oju)))
    left_other_types = tuple([typemap[rxx__nrko.name] for rxx__nrko in
        hugex__nbmf])
    right_other_types = tuple([typemap[rxx__nrko.name] for rxx__nrko in
        lxyc__oju])
    left_key_names = tuple('t1_key' + str(cen__zpx) for cen__zpx in range(
        n_keys))
    right_key_names = tuple('t2_key' + str(cen__zpx) for cen__zpx in range(
        n_keys))
    glbs = {}
    loc = join_node.loc
    func_text = 'def f({}{}, {},{}{}{}):\n'.format('{},'.format(xby__jimzo[
        0]) if len(xby__jimzo) == 1 else '', ','.join(left_key_names), ','.
        join(right_key_names), ','.join(left_other_names), ',' if len(
        left_other_names) != 0 else '', ','.join(right_other_names))
    left_key_types = tuple(typemap[lano__ser.name] for lano__ser in akqz__bqunk
        )
    right_key_types = tuple(typemap[lano__ser.name] for lano__ser in pfi__ksr)
    for cen__zpx in range(n_keys):
        glbs[f'key_type_{cen__zpx}'] = _match_join_key_types(left_key_types
            [cen__zpx], right_key_types[cen__zpx], loc)
    func_text += '    t1_keys = ({},)\n'.format(', '.join(
        f'bodo.utils.utils.astype({left_key_names[cen__zpx]}, key_type_{cen__zpx})'
         for cen__zpx in range(n_keys)))
    func_text += '    t2_keys = ({},)\n'.format(', '.join(
        f'bodo.utils.utils.astype({right_key_names[cen__zpx]}, key_type_{cen__zpx})'
         for cen__zpx in range(n_keys)))
    func_text += '    data_left = ({}{})\n'.format(','.join(
        left_other_names), ',' if len(left_other_names) != 0 else '')
    func_text += '    data_right = ({}{})\n'.format(','.join(
        right_other_names), ',' if len(right_other_names) != 0 else '')
    qpd__tejj = []
    for cname in join_node.left_keys:
        if cname in join_node.add_suffix:
            hmxar__qvt = str(cname) + join_node.suffix_x
        else:
            hmxar__qvt = cname
        assert hmxar__qvt in join_node.out_data_vars
        qpd__tejj.append(join_node.out_data_vars[hmxar__qvt])
    for cen__zpx, cname in enumerate(join_node.right_keys):
        if not join_node.vect_same_key[cen__zpx] and not join_node.is_join:
            if cname in join_node.add_suffix:
                hmxar__qvt = str(cname) + join_node.suffix_y
            else:
                hmxar__qvt = cname
            assert hmxar__qvt in join_node.out_data_vars
            qpd__tejj.append(join_node.out_data_vars[hmxar__qvt])

    def _get_out_col_var(cname, is_left):
        if cname in join_node.add_suffix:
            if is_left:
                hmxar__qvt = str(cname) + join_node.suffix_x
            else:
                hmxar__qvt = str(cname) + join_node.suffix_y
        else:
            hmxar__qvt = cname
        return join_node.out_data_vars[hmxar__qvt]
    cbsrl__prim = bau__pdukw + tuple(qpd__tejj)
    cbsrl__prim += tuple(_get_out_col_var(suqq__oqg, True) for suqq__oqg,
        lano__ser in sorted(join_node.left_vars.items(), key=lambda a: str(
        a[0])) if suqq__oqg not in join_node.left_keys)
    cbsrl__prim += tuple(_get_out_col_var(suqq__oqg, False) for suqq__oqg,
        lano__ser in sorted(join_node.right_vars.items(), key=lambda a: str
        (a[0])) if suqq__oqg not in join_node.right_keys)
    if join_node.indicator:
        cbsrl__prim += _get_out_col_var('_merge', False),
    yhczw__cmt = [('t3_c' + str(cen__zpx)) for cen__zpx in range(len(
        cbsrl__prim))]
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
            right_parallel, glbs, [typemap[lano__ser.name] for lano__ser in
            cbsrl__prim], join_node.loc, join_node.indicator, join_node.
            is_na_equal, general_cond_cfunc, left_col_nums, right_col_nums)
    if join_node.how == 'asof':
        for cen__zpx in range(len(left_other_names)):
            func_text += '    left_{} = out_data_left[{}]\n'.format(cen__zpx,
                cen__zpx)
        for cen__zpx in range(len(right_other_names)):
            func_text += '    right_{} = out_data_right[{}]\n'.format(cen__zpx,
                cen__zpx)
        for cen__zpx in range(n_keys):
            func_text += f'    t1_keys_{cen__zpx} = out_t1_keys[{cen__zpx}]\n'
        for cen__zpx in range(n_keys):
            func_text += f'    t2_keys_{cen__zpx} = out_t2_keys[{cen__zpx}]\n'
    idx = 0
    if optional_column:
        func_text += f'    {yhczw__cmt[idx]} = opti_0\n'
        idx += 1
    for cen__zpx in range(n_keys):
        func_text += f'    {yhczw__cmt[idx]} = t1_keys_{cen__zpx}\n'
        idx += 1
    for cen__zpx in range(n_keys):
        if not join_node.vect_same_key[cen__zpx] and not join_node.is_join:
            func_text += f'    {yhczw__cmt[idx]} = t2_keys_{cen__zpx}\n'
            idx += 1
    for cen__zpx in range(len(left_other_names)):
        func_text += f'    {yhczw__cmt[idx]} = left_{cen__zpx}\n'
        idx += 1
    for cen__zpx in range(len(right_other_names)):
        func_text += f'    {yhczw__cmt[idx]} = right_{cen__zpx}\n'
        idx += 1
    if join_node.indicator:
        func_text += f'    {yhczw__cmt[idx]} = indicator_col\n'
        idx += 1
    qsgol__nhzu = {}
    exec(func_text, {}, qsgol__nhzu)
    krwvg__nwj = qsgol__nhzu['f']
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
    qkro__ljqiw = compile_to_numba_ir(krwvg__nwj, glbs, typingctx=typingctx,
        targetctx=targetctx, arg_typs=xvh__ekng, typemap=typemap, calltypes
        =calltypes).blocks.popitem()[1]
    replace_arg_nodes(qkro__ljqiw, qanw__rkkq)
    dhgd__epdg = qkro__ljqiw.body[:-3]
    for cen__zpx in range(len(cbsrl__prim)):
        dhgd__epdg[-len(cbsrl__prim) + cen__zpx].target = cbsrl__prim[cen__zpx]
    return dhgd__epdg


distributed_pass.distributed_run_extensions[Join] = join_distributed_run


def _gen_general_cond_cfunc(join_node, typemap):
    expr = join_node.gen_cond_expr
    if not expr:
        return None, [], []
    ckuvh__ydbk = next_label()
    eiz__rpbmm = _get_col_to_ind(join_node.left_keys, join_node.left_vars)
    njgkx__ihsdo = _get_col_to_ind(join_node.right_keys, join_node.right_vars)
    table_getitem_funcs = {'bodo': bodo, 'numba': numba, 'is_null_pointer':
        is_null_pointer}
    na_check_name = 'NOT_NA'
    func_text = f"""def bodo_join_gen_cond{ckuvh__ydbk}(left_table, right_table, left_data1, right_data1, left_null_bitmap, right_null_bitmap, left_ind, right_ind):
"""
    func_text += '  if is_null_pointer(left_table):\n'
    func_text += '    return False\n'
    expr, func_text, left_col_nums = _replace_column_accesses(expr,
        eiz__rpbmm, typemap, join_node.left_vars, table_getitem_funcs,
        func_text, 'left', len(join_node.left_keys), na_check_name)
    expr, func_text, right_col_nums = _replace_column_accesses(expr,
        njgkx__ihsdo, typemap, join_node.right_vars, table_getitem_funcs,
        func_text, 'right', len(join_node.right_keys), na_check_name)
    func_text += f'  return {expr}'
    qsgol__nhzu = {}
    exec(func_text, table_getitem_funcs, qsgol__nhzu)
    agas__jgjso = qsgol__nhzu[f'bodo_join_gen_cond{ckuvh__ydbk}']
    matta__pjvf = types.bool_(types.voidptr, types.voidptr, types.voidptr,
        types.voidptr, types.voidptr, types.voidptr, types.int64, types.int64)
    dfle__uytud = numba.cfunc(matta__pjvf, nopython=True)(agas__jgjso)
    join_gen_cond_cfunc[dfle__uytud.native_name] = dfle__uytud
    join_gen_cond_cfunc_addr[dfle__uytud.native_name] = dfle__uytud.address
    return dfle__uytud, left_col_nums, right_col_nums


def _replace_column_accesses(expr, col_to_ind, typemap, col_vars,
    table_getitem_funcs, func_text, table_name, n_keys, na_check_name):
    tczk__btdq = []
    for rxx__nrko, ylii__hsrs in col_to_ind.items():
        cname = f'({table_name}.{rxx__nrko})'
        if cname not in expr:
            continue
        afw__edfk = f'getitem_{table_name}_val_{ylii__hsrs}'
        qnpz__vzx = f'_bodo_{table_name}_val_{ylii__hsrs}'
        dgm__wojl = typemap[col_vars[rxx__nrko].name]
        if is_str_arr_type(dgm__wojl):
            func_text += f"""  {qnpz__vzx}, {qnpz__vzx}_size = {afw__edfk}({table_name}_table, {table_name}_ind)
"""
            func_text += f"""  {qnpz__vzx} = bodo.libs.str_arr_ext.decode_utf8({qnpz__vzx}, {qnpz__vzx}_size)
"""
        else:
            func_text += (
                f'  {qnpz__vzx} = {afw__edfk}({table_name}_data1, {table_name}_ind)\n'
                )
        table_getitem_funcs[afw__edfk
            ] = bodo.libs.array._gen_row_access_intrinsic(dgm__wojl, ylii__hsrs
            )
        expr = expr.replace(cname, qnpz__vzx)
        hlkum__mbzy = f'({na_check_name}.{table_name}.{rxx__nrko})'
        if hlkum__mbzy in expr:
            lirij__gttl = f'nacheck_{table_name}_val_{ylii__hsrs}'
            oymm__cwbpr = f'_bodo_isna_{table_name}_val_{ylii__hsrs}'
            if (isinstance(dgm__wojl, bodo.libs.int_arr_ext.
                IntegerArrayType) or dgm__wojl == bodo.libs.bool_arr_ext.
                boolean_array or is_str_arr_type(dgm__wojl)):
                func_text += f"""  {oymm__cwbpr} = {lirij__gttl}({table_name}_null_bitmap, {table_name}_ind)
"""
            else:
                func_text += f"""  {oymm__cwbpr} = {lirij__gttl}({table_name}_data1, {table_name}_ind)
"""
            table_getitem_funcs[lirij__gttl
                ] = bodo.libs.array._gen_row_na_check_intrinsic(dgm__wojl,
                ylii__hsrs)
            expr = expr.replace(hlkum__mbzy, oymm__cwbpr)
        if ylii__hsrs >= n_keys:
            tczk__btdq.append(ylii__hsrs)
    return expr, func_text, tczk__btdq


def _get_col_to_ind(key_names, col_vars):
    n_keys = len(key_names)
    col_to_ind = {rxx__nrko: cen__zpx for cen__zpx, rxx__nrko in enumerate(
        key_names)}
    cen__zpx = n_keys
    for rxx__nrko in sorted(col_vars, key=lambda a: str(a)):
        if rxx__nrko in key_names:
            continue
        col_to_ind[rxx__nrko] = cen__zpx
        cen__zpx += 1
    return col_to_ind


def _match_join_key_types(t1, t2, loc):
    if t1 == t2:
        return t1
    try:
        arr = dtype_to_array_type(find_common_np_dtype([t1, t2]))
        return to_nullable_type(arr) if is_nullable_type(t1
            ) or is_nullable_type(t2) else arr
    except Exception as wwn__izqng:
        if is_str_arr_type(t1) and is_str_arr_type(t2):
            return bodo.string_array_type
        raise BodoError(f'Join key types {t1} and {t2} do not match', loc=loc)


def _get_table_parallel_flags(join_node, array_dists):
    erddg__odtz = (distributed_pass.Distribution.OneD, distributed_pass.
        Distribution.OneD_Var)
    left_parallel = all(array_dists[lano__ser.name] in erddg__odtz for
        lano__ser in join_node.left_vars.values())
    right_parallel = all(array_dists[lano__ser.name] in erddg__odtz for
        lano__ser in join_node.right_vars.values())
    if not left_parallel:
        assert not any(array_dists[lano__ser.name] in erddg__odtz for
            lano__ser in join_node.left_vars.values())
    if not right_parallel:
        assert not any(array_dists[lano__ser.name] in erddg__odtz for
            lano__ser in join_node.right_vars.values())
    if left_parallel or right_parallel:
        assert all(array_dists[lano__ser.name] in erddg__odtz for lano__ser in
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
    amueb__kel = []
    for cen__zpx in range(len(left_key_names)):
        cdd__jpthk = _match_join_key_types(left_key_types[cen__zpx],
            right_key_types[cen__zpx], loc)
        amueb__kel.append(needs_typechange(cdd__jpthk, is_right,
            vect_same_key[cen__zpx]))
    for cen__zpx in range(len(left_other_names)):
        amueb__kel.append(needs_typechange(left_other_types[cen__zpx],
            is_right, False))
    for cen__zpx in range(len(right_key_names)):
        if not vect_same_key[cen__zpx] and not is_join:
            cdd__jpthk = _match_join_key_types(left_key_types[cen__zpx],
                right_key_types[cen__zpx], loc)
            amueb__kel.append(needs_typechange(cdd__jpthk, is_left, False))
    for cen__zpx in range(len(right_other_names)):
        amueb__kel.append(needs_typechange(right_other_types[cen__zpx],
            is_left, False))

    def get_out_type(idx, in_type, in_name, need_nullable, is_same_key):
        if isinstance(in_type, types.Array) and not is_dtype_nullable(in_type
            .dtype) and need_nullable and not is_same_key:
            if isinstance(in_type.dtype, types.Integer):
                ixu__hlkif = IntDtype(in_type.dtype).name
                assert ixu__hlkif.endswith('Dtype()')
                ixu__hlkif = ixu__hlkif[:-7]
                cub__rkxwt = f"""    typ_{idx} = bodo.hiframes.pd_series_ext.get_series_data(pd.Series([1], dtype="{ixu__hlkif}"))
"""
                ykpkg__hojk = f'typ_{idx}'
            else:
                assert in_type.dtype == types.bool_, 'unexpected non-nullable type in join'
                cub__rkxwt = (
                    f'    typ_{idx} = bodo.libs.bool_arr_ext.alloc_bool_array(1)\n'
                    )
                ykpkg__hojk = f'typ_{idx}'
        elif in_type == bodo.string_array_type:
            cub__rkxwt = (
                f'    typ_{idx} = bodo.libs.str_arr_ext.pre_alloc_string_array(0, 0)\n'
                )
            ykpkg__hojk = f'typ_{idx}'
        else:
            cub__rkxwt = ''
            ykpkg__hojk = in_name
        return cub__rkxwt, ykpkg__hojk
    n_keys = len(left_key_names)
    func_text = '    # beginning of _gen_local_hash_join\n'
    btt__ack = []
    for cen__zpx in range(n_keys):
        btt__ack.append('t1_keys[{}]'.format(cen__zpx))
    for cen__zpx in range(len(left_other_names)):
        btt__ack.append('data_left[{}]'.format(cen__zpx))
    func_text += '    info_list_total_l = [{}]\n'.format(','.join(
        'array_to_info({})'.format(a) for a in btt__ack))
    func_text += '    table_left = arr_info_list_to_table(info_list_total_l)\n'
    pvr__pdib = []
    for cen__zpx in range(n_keys):
        pvr__pdib.append('t2_keys[{}]'.format(cen__zpx))
    for cen__zpx in range(len(right_other_names)):
        pvr__pdib.append('data_right[{}]'.format(cen__zpx))
    func_text += '    info_list_total_r = [{}]\n'.format(','.join(
        'array_to_info({})'.format(a) for a in pvr__pdib))
    func_text += (
        '    table_right = arr_info_list_to_table(info_list_total_r)\n')
    func_text += '    vect_same_key = np.array([{}])\n'.format(','.join('1' if
        njaas__hrrff else '0' for njaas__hrrff in vect_same_key))
    func_text += '    vect_need_typechange = np.array([{}])\n'.format(','.
        join('1' if njaas__hrrff else '0' for njaas__hrrff in amueb__kel))
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
        hyti__chail = get_out_type(idx, out_types[idx], 'opti_c0', False, False
            )
        func_text += hyti__chail[0]
        glbs[f'out_type_{idx}'] = out_types[idx]
        func_text += f"""    opti_0 = info_to_array(info_from_table(out_table, {idx}), {hyti__chail[1]})
"""
        idx += 1
    for cen__zpx, gtw__tzlw in enumerate(left_key_names):
        cdd__jpthk = _match_join_key_types(left_key_types[cen__zpx],
            right_key_types[cen__zpx], loc)
        hyti__chail = get_out_type(idx, cdd__jpthk, f't1_keys[{cen__zpx}]',
            is_right, vect_same_key[cen__zpx])
        func_text += hyti__chail[0]
        glbs[f'out_type_{idx}'] = out_types[idx]
        if cdd__jpthk != left_key_types[cen__zpx] and left_key_types[cen__zpx
            ] != bodo.dict_str_arr_type:
            func_text += f"""    t1_keys_{cen__zpx} = bodo.utils.utils.astype(info_to_array(info_from_table(out_table, {idx}), {hyti__chail[1]}), out_type_{idx})
"""
        else:
            func_text += f"""    t1_keys_{cen__zpx} = info_to_array(info_from_table(out_table, {idx}), {hyti__chail[1]})
"""
        idx += 1
    for cen__zpx, gtw__tzlw in enumerate(left_other_names):
        hyti__chail = get_out_type(idx, left_other_types[cen__zpx],
            gtw__tzlw, is_right, False)
        func_text += hyti__chail[0]
        func_text += (
            '    left_{} = info_to_array(info_from_table(out_table, {}), {})\n'
            .format(cen__zpx, idx, hyti__chail[1]))
        idx += 1
    for cen__zpx, gtw__tzlw in enumerate(right_key_names):
        if not vect_same_key[cen__zpx] and not is_join:
            cdd__jpthk = _match_join_key_types(left_key_types[cen__zpx],
                right_key_types[cen__zpx], loc)
            hyti__chail = get_out_type(idx, cdd__jpthk,
                f't2_keys[{cen__zpx}]', is_left, False)
            func_text += hyti__chail[0]
            glbs[f'out_type_{idx}'] = out_types[idx - len(left_other_names)]
            if cdd__jpthk != right_key_types[cen__zpx] and right_key_types[
                cen__zpx] != bodo.dict_str_arr_type:
                func_text += f"""    t2_keys_{cen__zpx} = bodo.utils.utils.astype(info_to_array(info_from_table(out_table, {idx}), {hyti__chail[1]}), out_type_{idx})
"""
            else:
                func_text += f"""    t2_keys_{cen__zpx} = info_to_array(info_from_table(out_table, {idx}), {hyti__chail[1]})
"""
            idx += 1
    for cen__zpx, gtw__tzlw in enumerate(right_other_names):
        hyti__chail = get_out_type(idx, right_other_types[cen__zpx],
            gtw__tzlw, is_left, False)
        func_text += hyti__chail[0]
        func_text += (
            '    right_{} = info_to_array(info_from_table(out_table, {}), {})\n'
            .format(cen__zpx, idx, hyti__chail[1]))
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
    kcu__dvirm = bodo.libs.distributed_api.get_size()
    gxa__wsi = np.empty(kcu__dvirm, left_key_arrs[0].dtype)
    ttymi__tze = np.empty(kcu__dvirm, left_key_arrs[0].dtype)
    bodo.libs.distributed_api.allgather(gxa__wsi, left_key_arrs[0][0])
    bodo.libs.distributed_api.allgather(ttymi__tze, left_key_arrs[0][-1])
    ixx__rrdg = np.zeros(kcu__dvirm, np.int32)
    nhu__rcv = np.zeros(kcu__dvirm, np.int32)
    fud__jkabi = np.zeros(kcu__dvirm, np.int32)
    qon__oyhkc = right_key_arrs[0][0]
    opnx__ozslw = right_key_arrs[0][-1]
    skmz__oicsz = -1
    cen__zpx = 0
    while cen__zpx < kcu__dvirm - 1 and ttymi__tze[cen__zpx] < qon__oyhkc:
        cen__zpx += 1
    while cen__zpx < kcu__dvirm and gxa__wsi[cen__zpx] <= opnx__ozslw:
        skmz__oicsz, mykr__qghgu = _count_overlap(right_key_arrs[0],
            gxa__wsi[cen__zpx], ttymi__tze[cen__zpx])
        if skmz__oicsz != 0:
            skmz__oicsz -= 1
            mykr__qghgu += 1
        ixx__rrdg[cen__zpx] = mykr__qghgu
        nhu__rcv[cen__zpx] = skmz__oicsz
        cen__zpx += 1
    while cen__zpx < kcu__dvirm:
        ixx__rrdg[cen__zpx] = 1
        nhu__rcv[cen__zpx] = len(right_key_arrs[0]) - 1
        cen__zpx += 1
    bodo.libs.distributed_api.alltoall(ixx__rrdg, fud__jkabi, 1)
    eilqu__sjed = fud__jkabi.sum()
    tbvvc__ljw = np.empty(eilqu__sjed, right_key_arrs[0].dtype)
    acuw__nvphj = alloc_arr_tup(eilqu__sjed, right_data)
    tar__hicvn = bodo.ir.join.calc_disp(fud__jkabi)
    bodo.libs.distributed_api.alltoallv(right_key_arrs[0], tbvvc__ljw,
        ixx__rrdg, fud__jkabi, nhu__rcv, tar__hicvn)
    bodo.libs.distributed_api.alltoallv_tup(right_data, acuw__nvphj,
        ixx__rrdg, fud__jkabi, nhu__rcv, tar__hicvn)
    return (tbvvc__ljw,), acuw__nvphj


@numba.njit
def _count_overlap(r_key_arr, start, end):
    mykr__qghgu = 0
    skmz__oicsz = 0
    klm__ivuit = 0
    while klm__ivuit < len(r_key_arr) and r_key_arr[klm__ivuit] < start:
        skmz__oicsz += 1
        klm__ivuit += 1
    while klm__ivuit < len(r_key_arr) and start <= r_key_arr[klm__ivuit
        ] <= end:
        klm__ivuit += 1
        mykr__qghgu += 1
    return skmz__oicsz, mykr__qghgu


import llvmlite.binding as ll
from bodo.libs import hdist
ll.add_symbol('c_alltoallv', hdist.c_alltoallv)


@numba.njit
def calc_disp(arr):
    jvv__utk = np.empty_like(arr)
    jvv__utk[0] = 0
    for cen__zpx in range(1, len(arr)):
        jvv__utk[cen__zpx] = jvv__utk[cen__zpx - 1] + arr[cen__zpx - 1]
    return jvv__utk


@numba.njit
def local_merge_asof(left_keys, right_keys, data_left, data_right):
    llvcp__ligq = len(left_keys[0])
    alr__hipg = len(right_keys[0])
    peur__avpa = alloc_arr_tup(llvcp__ligq, left_keys)
    lndgo__mxzig = alloc_arr_tup(llvcp__ligq, right_keys)
    fec__yqlkb = alloc_arr_tup(llvcp__ligq, data_left)
    bvofd__bmxg = alloc_arr_tup(llvcp__ligq, data_right)
    gnr__rrf = 0
    xgsoh__ryt = 0
    for gnr__rrf in range(llvcp__ligq):
        if xgsoh__ryt < 0:
            xgsoh__ryt = 0
        while xgsoh__ryt < alr__hipg and getitem_arr_tup(right_keys, xgsoh__ryt
            ) <= getitem_arr_tup(left_keys, gnr__rrf):
            xgsoh__ryt += 1
        xgsoh__ryt -= 1
        setitem_arr_tup(peur__avpa, gnr__rrf, getitem_arr_tup(left_keys,
            gnr__rrf))
        setitem_arr_tup(fec__yqlkb, gnr__rrf, getitem_arr_tup(data_left,
            gnr__rrf))
        if xgsoh__ryt >= 0:
            setitem_arr_tup(lndgo__mxzig, gnr__rrf, getitem_arr_tup(
                right_keys, xgsoh__ryt))
            setitem_arr_tup(bvofd__bmxg, gnr__rrf, getitem_arr_tup(
                data_right, xgsoh__ryt))
        else:
            bodo.libs.array_kernels.setna_tup(lndgo__mxzig, gnr__rrf)
            bodo.libs.array_kernels.setna_tup(bvofd__bmxg, gnr__rrf)
    return peur__avpa, lndgo__mxzig, fec__yqlkb, bvofd__bmxg


def copy_arr_tup(arrs):
    return tuple(a.copy() for a in arrs)


@overload(copy_arr_tup, no_unliteral=True)
def copy_arr_tup_overload(arrs):
    mykr__qghgu = arrs.count
    func_text = 'def f(arrs):\n'
    func_text += '  return ({},)\n'.format(','.join('arrs[{}].copy()'.
        format(cen__zpx) for cen__zpx in range(mykr__qghgu)))
    qsgol__nhzu = {}
    exec(func_text, {}, qsgol__nhzu)
    fakfx__yspci = qsgol__nhzu['f']
    return fakfx__yspci
