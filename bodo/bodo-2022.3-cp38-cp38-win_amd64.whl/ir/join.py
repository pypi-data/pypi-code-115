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
        aopy__jhfy = func.signature
        tjdr__cyvwn = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64), lir
            .IntType(64)])
        cbfho__grnux = cgutils.get_or_insert_function(builder.module,
            tjdr__cyvwn, sym._literal_value)
        builder.call(cbfho__grnux, [context.get_constant_null(aopy__jhfy.
            args[0]), context.get_constant_null(aopy__jhfy.args[1]),
            context.get_constant_null(aopy__jhfy.args[2]), context.
            get_constant_null(aopy__jhfy.args[3]), context.
            get_constant_null(aopy__jhfy.args[4]), context.
            get_constant_null(aopy__jhfy.args[5]), context.get_constant(
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
        self.left_cond_cols = set(vtb__gxu for vtb__gxu in left_vars.keys() if
            f'(left.{vtb__gxu})' in gen_cond_expr)
        self.right_cond_cols = set(vtb__gxu for vtb__gxu in right_vars.keys
            () if f'(right.{vtb__gxu})' in gen_cond_expr)
        etnt__xlw = set(left_keys) & set(right_keys)
        pgyuu__jzd = set(left_vars.keys()) & set(right_vars.keys())
        kbe__trahr = pgyuu__jzd - etnt__xlw
        vect_same_key = []
        n_keys = len(left_keys)
        for ybj__uylu in range(n_keys):
            cqmzx__swqzp = left_keys[ybj__uylu]
            hcp__zhzuy = right_keys[ybj__uylu]
            vect_same_key.append(cqmzx__swqzp == hcp__zhzuy)
        self.vect_same_key = vect_same_key
        self.column_origins = {(str(vtb__gxu) + suffix_x if vtb__gxu in
            kbe__trahr else vtb__gxu): ('left', vtb__gxu) for vtb__gxu in
            left_vars.keys()}
        self.column_origins.update({(str(vtb__gxu) + suffix_y if vtb__gxu in
            kbe__trahr else vtb__gxu): ('right', vtb__gxu) for vtb__gxu in
            right_vars.keys()})
        if '$_bodo_index_' in kbe__trahr:
            kbe__trahr.remove('$_bodo_index_')
        self.add_suffix = kbe__trahr

    def __repr__(self):
        tdz__egrbk = ''
        for vtb__gxu, dkvjc__ybtpq in self.out_data_vars.items():
            tdz__egrbk += "'{}':{}, ".format(vtb__gxu, dkvjc__ybtpq.name)
        fte__zkuw = '{}{{{}}}'.format(self.df_out, tdz__egrbk)
        huhgt__dfjpc = ''
        for vtb__gxu, dkvjc__ybtpq in self.left_vars.items():
            huhgt__dfjpc += "'{}':{}, ".format(vtb__gxu, dkvjc__ybtpq.name)
        qqs__hhc = '{}{{{}}}'.format(self.left_df, huhgt__dfjpc)
        huhgt__dfjpc = ''
        for vtb__gxu, dkvjc__ybtpq in self.right_vars.items():
            huhgt__dfjpc += "'{}':{}, ".format(vtb__gxu, dkvjc__ybtpq.name)
        wwzu__tutur = '{}{{{}}}'.format(self.right_df, huhgt__dfjpc)
        return 'join [{}={}]: {} , {}, {}'.format(self.left_keys, self.
            right_keys, fte__zkuw, qqs__hhc, wwzu__tutur)


def join_array_analysis(join_node, equiv_set, typemap, array_analysis):
    rqc__qcxqo = []
    assert len(join_node.out_data_vars) > 0, 'empty join in array analysis'
    giq__ipkkt = []
    aok__myah = list(join_node.left_vars.values())
    for lcx__nwa in aok__myah:
        zjw__abdl = typemap[lcx__nwa.name]
        lij__jjnx = equiv_set.get_shape(lcx__nwa)
        if lij__jjnx:
            giq__ipkkt.append(lij__jjnx[0])
    if len(giq__ipkkt) > 1:
        equiv_set.insert_equiv(*giq__ipkkt)
    giq__ipkkt = []
    aok__myah = list(join_node.right_vars.values())
    for lcx__nwa in aok__myah:
        zjw__abdl = typemap[lcx__nwa.name]
        lij__jjnx = equiv_set.get_shape(lcx__nwa)
        if lij__jjnx:
            giq__ipkkt.append(lij__jjnx[0])
    if len(giq__ipkkt) > 1:
        equiv_set.insert_equiv(*giq__ipkkt)
    giq__ipkkt = []
    for lcx__nwa in join_node.out_data_vars.values():
        zjw__abdl = typemap[lcx__nwa.name]
        uysex__bgfs = array_analysis._gen_shape_call(equiv_set, lcx__nwa,
            zjw__abdl.ndim, None, rqc__qcxqo)
        equiv_set.insert_equiv(lcx__nwa, uysex__bgfs)
        giq__ipkkt.append(uysex__bgfs[0])
        equiv_set.define(lcx__nwa, set())
    if len(giq__ipkkt) > 1:
        equiv_set.insert_equiv(*giq__ipkkt)
    return [], rqc__qcxqo


numba.parfors.array_analysis.array_analysis_extensions[Join
    ] = join_array_analysis


def join_distributed_analysis(join_node, array_dists):
    udde__qpu = Distribution.OneD
    vbjts__gsp = Distribution.OneD
    for lcx__nwa in join_node.left_vars.values():
        udde__qpu = Distribution(min(udde__qpu.value, array_dists[lcx__nwa.
            name].value))
    for lcx__nwa in join_node.right_vars.values():
        vbjts__gsp = Distribution(min(vbjts__gsp.value, array_dists[
            lcx__nwa.name].value))
    lyljx__rig = Distribution.OneD_Var
    for lcx__nwa in join_node.out_data_vars.values():
        if lcx__nwa.name in array_dists:
            lyljx__rig = Distribution(min(lyljx__rig.value, array_dists[
                lcx__nwa.name].value))
    ezwm__eotd = Distribution(min(lyljx__rig.value, udde__qpu.value))
    qtos__jia = Distribution(min(lyljx__rig.value, vbjts__gsp.value))
    lyljx__rig = Distribution(max(ezwm__eotd.value, qtos__jia.value))
    for lcx__nwa in join_node.out_data_vars.values():
        array_dists[lcx__nwa.name] = lyljx__rig
    if lyljx__rig != Distribution.OneD_Var:
        udde__qpu = lyljx__rig
        vbjts__gsp = lyljx__rig
    for lcx__nwa in join_node.left_vars.values():
        array_dists[lcx__nwa.name] = udde__qpu
    for lcx__nwa in join_node.right_vars.values():
        array_dists[lcx__nwa.name] = vbjts__gsp
    return


distributed_analysis.distributed_analysis_extensions[Join
    ] = join_distributed_analysis


def join_typeinfer(join_node, typeinferer):
    etnt__xlw = set(join_node.left_keys) & set(join_node.right_keys)
    pgyuu__jzd = set(join_node.left_vars.keys()) & set(join_node.right_vars
        .keys())
    kbe__trahr = pgyuu__jzd - etnt__xlw
    for qrc__rqnmg, bmg__fcgq in join_node.out_data_vars.items():
        if join_node.indicator and qrc__rqnmg == '_merge':
            continue
        if not qrc__rqnmg in join_node.column_origins:
            raise BodoError('join(): The variable ' + qrc__rqnmg +
                ' is absent from the output')
        dgi__smqqz = join_node.column_origins[qrc__rqnmg]
        if dgi__smqqz[0] == 'left':
            lcx__nwa = join_node.left_vars[dgi__smqqz[1]]
        else:
            lcx__nwa = join_node.right_vars[dgi__smqqz[1]]
        typeinferer.constraints.append(typeinfer.Propagate(dst=bmg__fcgq.
            name, src=lcx__nwa.name, loc=join_node.loc))
    return


typeinfer.typeinfer_extensions[Join] = join_typeinfer


def visit_vars_join(join_node, callback, cbdata):
    if debug_prints():
        print('visiting join vars for:', join_node)
        print('cbdata: ', sorted(cbdata.items()))
    for ibia__ybqj in list(join_node.left_vars.keys()):
        join_node.left_vars[ibia__ybqj] = visit_vars_inner(join_node.
            left_vars[ibia__ybqj], callback, cbdata)
    for ibia__ybqj in list(join_node.right_vars.keys()):
        join_node.right_vars[ibia__ybqj] = visit_vars_inner(join_node.
            right_vars[ibia__ybqj], callback, cbdata)
    for ibia__ybqj in list(join_node.out_data_vars.keys()):
        join_node.out_data_vars[ibia__ybqj] = visit_vars_inner(join_node.
            out_data_vars[ibia__ybqj], callback, cbdata)


ir_utils.visit_vars_extensions[Join] = visit_vars_join


def remove_dead_join(join_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    vvpsu__aza = []
    zsadl__ybi = True
    for ibia__ybqj, lcx__nwa in join_node.out_data_vars.items():
        if lcx__nwa.name in lives:
            zsadl__ybi = False
            continue
        if ibia__ybqj == '$_bodo_index_':
            continue
        if join_node.indicator and ibia__ybqj == '_merge':
            vvpsu__aza.append('_merge')
            join_node.indicator = False
            continue
        eoxyh__injzv, kuvp__ozr = join_node.column_origins[ibia__ybqj]
        if (eoxyh__injzv == 'left' and kuvp__ozr not in join_node.left_keys and
            kuvp__ozr not in join_node.left_cond_cols):
            join_node.left_vars.pop(kuvp__ozr)
            vvpsu__aza.append(ibia__ybqj)
        if (eoxyh__injzv == 'right' and kuvp__ozr not in join_node.
            right_keys and kuvp__ozr not in join_node.right_cond_cols):
            join_node.right_vars.pop(kuvp__ozr)
            vvpsu__aza.append(ibia__ybqj)
    for cname in vvpsu__aza:
        join_node.out_data_vars.pop(cname)
    if zsadl__ybi:
        return None
    return join_node


ir_utils.remove_dead_extensions[Join] = remove_dead_join


def join_usedefs(join_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({dkvjc__ybtpq.name for dkvjc__ybtpq in join_node.
        left_vars.values()})
    use_set.update({dkvjc__ybtpq.name for dkvjc__ybtpq in join_node.
        right_vars.values()})
    def_set.update({dkvjc__ybtpq.name for dkvjc__ybtpq in join_node.
        out_data_vars.values()})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Join] = join_usedefs


def get_copies_join(join_node, typemap):
    chbpw__mcnpi = set(dkvjc__ybtpq.name for dkvjc__ybtpq in join_node.
        out_data_vars.values())
    return set(), chbpw__mcnpi


ir_utils.copy_propagate_extensions[Join] = get_copies_join


def apply_copies_join(join_node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    for ibia__ybqj in list(join_node.left_vars.keys()):
        join_node.left_vars[ibia__ybqj] = replace_vars_inner(join_node.
            left_vars[ibia__ybqj], var_dict)
    for ibia__ybqj in list(join_node.right_vars.keys()):
        join_node.right_vars[ibia__ybqj] = replace_vars_inner(join_node.
            right_vars[ibia__ybqj], var_dict)
    for ibia__ybqj in list(join_node.out_data_vars.keys()):
        join_node.out_data_vars[ibia__ybqj] = replace_vars_inner(join_node.
            out_data_vars[ibia__ybqj], var_dict)
    return


ir_utils.apply_copy_propagate_extensions[Join] = apply_copies_join


def build_join_definitions(join_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for lcx__nwa in join_node.out_data_vars.values():
        definitions[lcx__nwa.name].append(join_node)
    return definitions


ir_utils.build_defs_extensions[Join] = build_join_definitions


def join_distributed_run(join_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    left_parallel, right_parallel = False, False
    if array_dists is not None:
        left_parallel, right_parallel = _get_table_parallel_flags(join_node,
            array_dists)
    n_keys = len(join_node.left_keys)
    igv__rxzii = tuple(join_node.left_vars[vtb__gxu] for vtb__gxu in
        join_node.left_keys)
    tlabq__gtctv = tuple(join_node.right_vars[vtb__gxu] for vtb__gxu in
        join_node.right_keys)
    slv__kqy = tuple(join_node.left_vars.keys())
    jxxs__bvuup = tuple(join_node.right_vars.keys())
    iovsc__yga = ()
    uhcd__nbtw = ()
    optional_column = False
    if (join_node.left_index and not join_node.right_index and not
        join_node.is_join):
        cpsnr__kwerz = join_node.right_keys[0]
        if cpsnr__kwerz in slv__kqy:
            uhcd__nbtw = cpsnr__kwerz,
            iovsc__yga = join_node.right_vars[cpsnr__kwerz],
            optional_column = True
    if (join_node.right_index and not join_node.left_index and not
        join_node.is_join):
        cpsnr__kwerz = join_node.left_keys[0]
        if cpsnr__kwerz in jxxs__bvuup:
            uhcd__nbtw = cpsnr__kwerz,
            iovsc__yga = join_node.left_vars[cpsnr__kwerz],
            optional_column = True
    aclnm__uurgm = tuple(join_node.out_data_vars[cname] for cname in uhcd__nbtw
        )
    rknqc__dqhkr = tuple(dkvjc__ybtpq for jkkb__rfaew, dkvjc__ybtpq in
        sorted(join_node.left_vars.items(), key=lambda a: str(a[0])) if 
        jkkb__rfaew not in join_node.left_keys)
    akumu__tzt = tuple(dkvjc__ybtpq for jkkb__rfaew, dkvjc__ybtpq in sorted
        (join_node.right_vars.items(), key=lambda a: str(a[0])) if 
        jkkb__rfaew not in join_node.right_keys)
    ndcz__rze = (iovsc__yga + igv__rxzii + tlabq__gtctv + rknqc__dqhkr +
        akumu__tzt)
    yiax__yiynl = tuple(typemap[dkvjc__ybtpq.name] for dkvjc__ybtpq in
        ndcz__rze)
    ozx__fgvos = tuple('opti_c' + str(qcse__brlfv) for qcse__brlfv in range
        (len(iovsc__yga)))
    left_other_names = tuple('t1_c' + str(qcse__brlfv) for qcse__brlfv in
        range(len(rknqc__dqhkr)))
    right_other_names = tuple('t2_c' + str(qcse__brlfv) for qcse__brlfv in
        range(len(akumu__tzt)))
    left_other_types = tuple([typemap[vtb__gxu.name] for vtb__gxu in
        rknqc__dqhkr])
    right_other_types = tuple([typemap[vtb__gxu.name] for vtb__gxu in
        akumu__tzt])
    left_key_names = tuple('t1_key' + str(qcse__brlfv) for qcse__brlfv in
        range(n_keys))
    right_key_names = tuple('t2_key' + str(qcse__brlfv) for qcse__brlfv in
        range(n_keys))
    glbs = {}
    loc = join_node.loc
    func_text = 'def f({}{}, {},{}{}{}):\n'.format('{},'.format(ozx__fgvos[
        0]) if len(ozx__fgvos) == 1 else '', ','.join(left_key_names), ','.
        join(right_key_names), ','.join(left_other_names), ',' if len(
        left_other_names) != 0 else '', ','.join(right_other_names))
    left_key_types = tuple(typemap[dkvjc__ybtpq.name] for dkvjc__ybtpq in
        igv__rxzii)
    right_key_types = tuple(typemap[dkvjc__ybtpq.name] for dkvjc__ybtpq in
        tlabq__gtctv)
    for qcse__brlfv in range(n_keys):
        glbs[f'key_type_{qcse__brlfv}'] = _match_join_key_types(left_key_types
            [qcse__brlfv], right_key_types[qcse__brlfv], loc)
    func_text += '    t1_keys = ({},)\n'.format(', '.join(
        f'bodo.utils.utils.astype({left_key_names[qcse__brlfv]}, key_type_{qcse__brlfv})'
         for qcse__brlfv in range(n_keys)))
    func_text += '    t2_keys = ({},)\n'.format(', '.join(
        f'bodo.utils.utils.astype({right_key_names[qcse__brlfv]}, key_type_{qcse__brlfv})'
         for qcse__brlfv in range(n_keys)))
    func_text += '    data_left = ({}{})\n'.format(','.join(
        left_other_names), ',' if len(left_other_names) != 0 else '')
    func_text += '    data_right = ({}{})\n'.format(','.join(
        right_other_names), ',' if len(right_other_names) != 0 else '')
    cnxj__dajey = []
    for cname in join_node.left_keys:
        if cname in join_node.add_suffix:
            brm__hef = str(cname) + join_node.suffix_x
        else:
            brm__hef = cname
        assert brm__hef in join_node.out_data_vars
        cnxj__dajey.append(join_node.out_data_vars[brm__hef])
    for qcse__brlfv, cname in enumerate(join_node.right_keys):
        if not join_node.vect_same_key[qcse__brlfv] and not join_node.is_join:
            if cname in join_node.add_suffix:
                brm__hef = str(cname) + join_node.suffix_y
            else:
                brm__hef = cname
            assert brm__hef in join_node.out_data_vars
            cnxj__dajey.append(join_node.out_data_vars[brm__hef])

    def _get_out_col_var(cname, is_left):
        if cname in join_node.add_suffix:
            if is_left:
                brm__hef = str(cname) + join_node.suffix_x
            else:
                brm__hef = str(cname) + join_node.suffix_y
        else:
            brm__hef = cname
        return join_node.out_data_vars[brm__hef]
    gqxyu__wwz = aclnm__uurgm + tuple(cnxj__dajey)
    gqxyu__wwz += tuple(_get_out_col_var(jkkb__rfaew, True) for jkkb__rfaew,
        dkvjc__ybtpq in sorted(join_node.left_vars.items(), key=lambda a:
        str(a[0])) if jkkb__rfaew not in join_node.left_keys)
    gqxyu__wwz += tuple(_get_out_col_var(jkkb__rfaew, False) for 
        jkkb__rfaew, dkvjc__ybtpq in sorted(join_node.right_vars.items(),
        key=lambda a: str(a[0])) if jkkb__rfaew not in join_node.right_keys)
    if join_node.indicator:
        gqxyu__wwz += _get_out_col_var('_merge', False),
    wch__lea = [('t3_c' + str(qcse__brlfv)) for qcse__brlfv in range(len(
        gqxyu__wwz))]
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
            right_parallel, glbs, [typemap[dkvjc__ybtpq.name] for
            dkvjc__ybtpq in gqxyu__wwz], join_node.loc, join_node.indicator,
            join_node.is_na_equal, general_cond_cfunc, left_col_nums,
            right_col_nums)
    if join_node.how == 'asof':
        for qcse__brlfv in range(len(left_other_names)):
            func_text += '    left_{} = out_data_left[{}]\n'.format(qcse__brlfv
                , qcse__brlfv)
        for qcse__brlfv in range(len(right_other_names)):
            func_text += '    right_{} = out_data_right[{}]\n'.format(
                qcse__brlfv, qcse__brlfv)
        for qcse__brlfv in range(n_keys):
            func_text += (
                f'    t1_keys_{qcse__brlfv} = out_t1_keys[{qcse__brlfv}]\n')
        for qcse__brlfv in range(n_keys):
            func_text += (
                f'    t2_keys_{qcse__brlfv} = out_t2_keys[{qcse__brlfv}]\n')
    idx = 0
    if optional_column:
        func_text += f'    {wch__lea[idx]} = opti_0\n'
        idx += 1
    for qcse__brlfv in range(n_keys):
        func_text += f'    {wch__lea[idx]} = t1_keys_{qcse__brlfv}\n'
        idx += 1
    for qcse__brlfv in range(n_keys):
        if not join_node.vect_same_key[qcse__brlfv] and not join_node.is_join:
            func_text += f'    {wch__lea[idx]} = t2_keys_{qcse__brlfv}\n'
            idx += 1
    for qcse__brlfv in range(len(left_other_names)):
        func_text += f'    {wch__lea[idx]} = left_{qcse__brlfv}\n'
        idx += 1
    for qcse__brlfv in range(len(right_other_names)):
        func_text += f'    {wch__lea[idx]} = right_{qcse__brlfv}\n'
        idx += 1
    if join_node.indicator:
        func_text += f'    {wch__lea[idx]} = indicator_col\n'
        idx += 1
    nuday__mud = {}
    exec(func_text, {}, nuday__mud)
    asev__fgbfn = nuday__mud['f']
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
    aln__jtnm = compile_to_numba_ir(asev__fgbfn, glbs, typingctx=typingctx,
        targetctx=targetctx, arg_typs=yiax__yiynl, typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(aln__jtnm, ndcz__rze)
    zwu__mgvkz = aln__jtnm.body[:-3]
    for qcse__brlfv in range(len(gqxyu__wwz)):
        zwu__mgvkz[-len(gqxyu__wwz) + qcse__brlfv].target = gqxyu__wwz[
            qcse__brlfv]
    return zwu__mgvkz


distributed_pass.distributed_run_extensions[Join] = join_distributed_run


def _gen_general_cond_cfunc(join_node, typemap):
    expr = join_node.gen_cond_expr
    if not expr:
        return None, [], []
    mgv__hdepw = next_label()
    qijt__lekk = _get_col_to_ind(join_node.left_keys, join_node.left_vars)
    myo__giboh = _get_col_to_ind(join_node.right_keys, join_node.right_vars)
    table_getitem_funcs = {'bodo': bodo, 'numba': numba, 'is_null_pointer':
        is_null_pointer}
    na_check_name = 'NOT_NA'
    func_text = f"""def bodo_join_gen_cond{mgv__hdepw}(left_table, right_table, left_data1, right_data1, left_null_bitmap, right_null_bitmap, left_ind, right_ind):
"""
    func_text += '  if is_null_pointer(left_table):\n'
    func_text += '    return False\n'
    expr, func_text, left_col_nums = _replace_column_accesses(expr,
        qijt__lekk, typemap, join_node.left_vars, table_getitem_funcs,
        func_text, 'left', len(join_node.left_keys), na_check_name)
    expr, func_text, right_col_nums = _replace_column_accesses(expr,
        myo__giboh, typemap, join_node.right_vars, table_getitem_funcs,
        func_text, 'right', len(join_node.right_keys), na_check_name)
    func_text += f'  return {expr}'
    nuday__mud = {}
    exec(func_text, table_getitem_funcs, nuday__mud)
    mcn__pghqa = nuday__mud[f'bodo_join_gen_cond{mgv__hdepw}']
    nhsk__choxn = types.bool_(types.voidptr, types.voidptr, types.voidptr,
        types.voidptr, types.voidptr, types.voidptr, types.int64, types.int64)
    lwxk__mfgl = numba.cfunc(nhsk__choxn, nopython=True)(mcn__pghqa)
    join_gen_cond_cfunc[lwxk__mfgl.native_name] = lwxk__mfgl
    join_gen_cond_cfunc_addr[lwxk__mfgl.native_name] = lwxk__mfgl.address
    return lwxk__mfgl, left_col_nums, right_col_nums


def _replace_column_accesses(expr, col_to_ind, typemap, col_vars,
    table_getitem_funcs, func_text, table_name, n_keys, na_check_name):
    qftqu__orxhl = []
    for vtb__gxu, mgrhm__nsa in col_to_ind.items():
        cname = f'({table_name}.{vtb__gxu})'
        if cname not in expr:
            continue
        bijm__nvcrm = f'getitem_{table_name}_val_{mgrhm__nsa}'
        wxd__ahy = f'_bodo_{table_name}_val_{mgrhm__nsa}'
        jdeb__jkgw = typemap[col_vars[vtb__gxu].name]
        if is_str_arr_type(jdeb__jkgw):
            func_text += f"""  {wxd__ahy}, {wxd__ahy}_size = {bijm__nvcrm}({table_name}_table, {table_name}_ind)
"""
            func_text += f"""  {wxd__ahy} = bodo.libs.str_arr_ext.decode_utf8({wxd__ahy}, {wxd__ahy}_size)
"""
        else:
            func_text += (
                f'  {wxd__ahy} = {bijm__nvcrm}({table_name}_data1, {table_name}_ind)\n'
                )
        table_getitem_funcs[bijm__nvcrm
            ] = bodo.libs.array._gen_row_access_intrinsic(jdeb__jkgw,
            mgrhm__nsa)
        expr = expr.replace(cname, wxd__ahy)
        rquz__befc = f'({na_check_name}.{table_name}.{vtb__gxu})'
        if rquz__befc in expr:
            xken__wcov = f'nacheck_{table_name}_val_{mgrhm__nsa}'
            fez__ymrwz = f'_bodo_isna_{table_name}_val_{mgrhm__nsa}'
            if (isinstance(jdeb__jkgw, bodo.libs.int_arr_ext.
                IntegerArrayType) or jdeb__jkgw == bodo.libs.bool_arr_ext.
                boolean_array or is_str_arr_type(jdeb__jkgw)):
                func_text += f"""  {fez__ymrwz} = {xken__wcov}({table_name}_null_bitmap, {table_name}_ind)
"""
            else:
                func_text += f"""  {fez__ymrwz} = {xken__wcov}({table_name}_data1, {table_name}_ind)
"""
            table_getitem_funcs[xken__wcov
                ] = bodo.libs.array._gen_row_na_check_intrinsic(jdeb__jkgw,
                mgrhm__nsa)
            expr = expr.replace(rquz__befc, fez__ymrwz)
        if mgrhm__nsa >= n_keys:
            qftqu__orxhl.append(mgrhm__nsa)
    return expr, func_text, qftqu__orxhl


def _get_col_to_ind(key_names, col_vars):
    n_keys = len(key_names)
    col_to_ind = {vtb__gxu: qcse__brlfv for qcse__brlfv, vtb__gxu in
        enumerate(key_names)}
    qcse__brlfv = n_keys
    for vtb__gxu in sorted(col_vars, key=lambda a: str(a)):
        if vtb__gxu in key_names:
            continue
        col_to_ind[vtb__gxu] = qcse__brlfv
        qcse__brlfv += 1
    return col_to_ind


def _match_join_key_types(t1, t2, loc):
    if t1 == t2:
        return t1
    try:
        arr = dtype_to_array_type(find_common_np_dtype([t1, t2]))
        return to_nullable_type(arr) if is_nullable_type(t1
            ) or is_nullable_type(t2) else arr
    except Exception as swl__ydf:
        if is_str_arr_type(t1) and is_str_arr_type(t2):
            return bodo.string_array_type
        raise BodoError(f'Join key types {t1} and {t2} do not match', loc=loc)


def _get_table_parallel_flags(join_node, array_dists):
    crnt__kbir = (distributed_pass.Distribution.OneD, distributed_pass.
        Distribution.OneD_Var)
    left_parallel = all(array_dists[dkvjc__ybtpq.name] in crnt__kbir for
        dkvjc__ybtpq in join_node.left_vars.values())
    right_parallel = all(array_dists[dkvjc__ybtpq.name] in crnt__kbir for
        dkvjc__ybtpq in join_node.right_vars.values())
    if not left_parallel:
        assert not any(array_dists[dkvjc__ybtpq.name] in crnt__kbir for
            dkvjc__ybtpq in join_node.left_vars.values())
    if not right_parallel:
        assert not any(array_dists[dkvjc__ybtpq.name] in crnt__kbir for
            dkvjc__ybtpq in join_node.right_vars.values())
    if left_parallel or right_parallel:
        assert all(array_dists[dkvjc__ybtpq.name] in crnt__kbir for
            dkvjc__ybtpq in join_node.out_data_vars.values())
    return left_parallel, right_parallel


def _gen_local_hash_join(optional_column, left_key_names, right_key_names,
    left_key_types, right_key_types, left_other_names, right_other_names,
    left_other_types, right_other_types, vect_same_key, is_left, is_right,
    is_join, left_parallel, right_parallel, glbs, out_types, loc, indicator,
    is_na_equal, general_cond_cfunc, left_col_nums, right_col_nums):

    def needs_typechange(in_type, need_nullable, is_same_key):
        return isinstance(in_type, types.Array) and not is_dtype_nullable(
            in_type.dtype) and need_nullable and not is_same_key
    vbjk__ipin = []
    for qcse__brlfv in range(len(left_key_names)):
        jzrc__gaavj = _match_join_key_types(left_key_types[qcse__brlfv],
            right_key_types[qcse__brlfv], loc)
        vbjk__ipin.append(needs_typechange(jzrc__gaavj, is_right,
            vect_same_key[qcse__brlfv]))
    for qcse__brlfv in range(len(left_other_names)):
        vbjk__ipin.append(needs_typechange(left_other_types[qcse__brlfv],
            is_right, False))
    for qcse__brlfv in range(len(right_key_names)):
        if not vect_same_key[qcse__brlfv] and not is_join:
            jzrc__gaavj = _match_join_key_types(left_key_types[qcse__brlfv],
                right_key_types[qcse__brlfv], loc)
            vbjk__ipin.append(needs_typechange(jzrc__gaavj, is_left, False))
    for qcse__brlfv in range(len(right_other_names)):
        vbjk__ipin.append(needs_typechange(right_other_types[qcse__brlfv],
            is_left, False))

    def get_out_type(idx, in_type, in_name, need_nullable, is_same_key):
        if isinstance(in_type, types.Array) and not is_dtype_nullable(in_type
            .dtype) and need_nullable and not is_same_key:
            if isinstance(in_type.dtype, types.Integer):
                mpuyc__cpium = IntDtype(in_type.dtype).name
                assert mpuyc__cpium.endswith('Dtype()')
                mpuyc__cpium = mpuyc__cpium[:-7]
                fqqig__ccb = f"""    typ_{idx} = bodo.hiframes.pd_series_ext.get_series_data(pd.Series([1], dtype="{mpuyc__cpium}"))
"""
                vdv__rdmi = f'typ_{idx}'
            else:
                assert in_type.dtype == types.bool_, 'unexpected non-nullable type in join'
                fqqig__ccb = (
                    f'    typ_{idx} = bodo.libs.bool_arr_ext.alloc_bool_array(1)\n'
                    )
                vdv__rdmi = f'typ_{idx}'
        elif in_type == bodo.string_array_type:
            fqqig__ccb = (
                f'    typ_{idx} = bodo.libs.str_arr_ext.pre_alloc_string_array(0, 0)\n'
                )
            vdv__rdmi = f'typ_{idx}'
        else:
            fqqig__ccb = ''
            vdv__rdmi = in_name
        return fqqig__ccb, vdv__rdmi
    n_keys = len(left_key_names)
    func_text = '    # beginning of _gen_local_hash_join\n'
    uvek__hwy = []
    for qcse__brlfv in range(n_keys):
        uvek__hwy.append('t1_keys[{}]'.format(qcse__brlfv))
    for qcse__brlfv in range(len(left_other_names)):
        uvek__hwy.append('data_left[{}]'.format(qcse__brlfv))
    func_text += '    info_list_total_l = [{}]\n'.format(','.join(
        'array_to_info({})'.format(a) for a in uvek__hwy))
    func_text += '    table_left = arr_info_list_to_table(info_list_total_l)\n'
    amznr__ilu = []
    for qcse__brlfv in range(n_keys):
        amznr__ilu.append('t2_keys[{}]'.format(qcse__brlfv))
    for qcse__brlfv in range(len(right_other_names)):
        amznr__ilu.append('data_right[{}]'.format(qcse__brlfv))
    func_text += '    info_list_total_r = [{}]\n'.format(','.join(
        'array_to_info({})'.format(a) for a in amznr__ilu))
    func_text += (
        '    table_right = arr_info_list_to_table(info_list_total_r)\n')
    func_text += '    vect_same_key = np.array([{}])\n'.format(','.join('1' if
        jznun__zzdf else '0' for jznun__zzdf in vect_same_key))
    func_text += '    vect_need_typechange = np.array([{}])\n'.format(','.
        join('1' if jznun__zzdf else '0' for jznun__zzdf in vbjk__ipin))
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
        ucln__ndgi = get_out_type(idx, out_types[idx], 'opti_c0', False, False)
        func_text += ucln__ndgi[0]
        glbs[f'out_type_{idx}'] = out_types[idx]
        func_text += f"""    opti_0 = info_to_array(info_from_table(out_table, {idx}), {ucln__ndgi[1]})
"""
        idx += 1
    for qcse__brlfv, eac__tyvo in enumerate(left_key_names):
        jzrc__gaavj = _match_join_key_types(left_key_types[qcse__brlfv],
            right_key_types[qcse__brlfv], loc)
        ucln__ndgi = get_out_type(idx, jzrc__gaavj,
            f't1_keys[{qcse__brlfv}]', is_right, vect_same_key[qcse__brlfv])
        func_text += ucln__ndgi[0]
        glbs[f'out_type_{idx}'] = out_types[idx]
        if jzrc__gaavj != left_key_types[qcse__brlfv] and left_key_types[
            qcse__brlfv] != bodo.dict_str_arr_type:
            func_text += f"""    t1_keys_{qcse__brlfv} = bodo.utils.utils.astype(info_to_array(info_from_table(out_table, {idx}), {ucln__ndgi[1]}), out_type_{idx})
"""
        else:
            func_text += f"""    t1_keys_{qcse__brlfv} = info_to_array(info_from_table(out_table, {idx}), {ucln__ndgi[1]})
"""
        idx += 1
    for qcse__brlfv, eac__tyvo in enumerate(left_other_names):
        ucln__ndgi = get_out_type(idx, left_other_types[qcse__brlfv],
            eac__tyvo, is_right, False)
        func_text += ucln__ndgi[0]
        func_text += (
            '    left_{} = info_to_array(info_from_table(out_table, {}), {})\n'
            .format(qcse__brlfv, idx, ucln__ndgi[1]))
        idx += 1
    for qcse__brlfv, eac__tyvo in enumerate(right_key_names):
        if not vect_same_key[qcse__brlfv] and not is_join:
            jzrc__gaavj = _match_join_key_types(left_key_types[qcse__brlfv],
                right_key_types[qcse__brlfv], loc)
            ucln__ndgi = get_out_type(idx, jzrc__gaavj,
                f't2_keys[{qcse__brlfv}]', is_left, False)
            func_text += ucln__ndgi[0]
            glbs[f'out_type_{idx}'] = out_types[idx - len(left_other_names)]
            if jzrc__gaavj != right_key_types[qcse__brlfv] and right_key_types[
                qcse__brlfv] != bodo.dict_str_arr_type:
                func_text += f"""    t2_keys_{qcse__brlfv} = bodo.utils.utils.astype(info_to_array(info_from_table(out_table, {idx}), {ucln__ndgi[1]}), out_type_{idx})
"""
            else:
                func_text += f"""    t2_keys_{qcse__brlfv} = info_to_array(info_from_table(out_table, {idx}), {ucln__ndgi[1]})
"""
            idx += 1
    for qcse__brlfv, eac__tyvo in enumerate(right_other_names):
        ucln__ndgi = get_out_type(idx, right_other_types[qcse__brlfv],
            eac__tyvo, is_left, False)
        func_text += ucln__ndgi[0]
        func_text += (
            '    right_{} = info_to_array(info_from_table(out_table, {}), {})\n'
            .format(qcse__brlfv, idx, ucln__ndgi[1]))
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
    tkx__lytup = bodo.libs.distributed_api.get_size()
    febq__hprs = np.empty(tkx__lytup, left_key_arrs[0].dtype)
    vghr__zccdd = np.empty(tkx__lytup, left_key_arrs[0].dtype)
    bodo.libs.distributed_api.allgather(febq__hprs, left_key_arrs[0][0])
    bodo.libs.distributed_api.allgather(vghr__zccdd, left_key_arrs[0][-1])
    rwmy__mussa = np.zeros(tkx__lytup, np.int32)
    hwzzn__vio = np.zeros(tkx__lytup, np.int32)
    vie__qagsf = np.zeros(tkx__lytup, np.int32)
    fay__iao = right_key_arrs[0][0]
    fgk__wfuxd = right_key_arrs[0][-1]
    bjj__ahj = -1
    qcse__brlfv = 0
    while qcse__brlfv < tkx__lytup - 1 and vghr__zccdd[qcse__brlfv] < fay__iao:
        qcse__brlfv += 1
    while qcse__brlfv < tkx__lytup and febq__hprs[qcse__brlfv] <= fgk__wfuxd:
        bjj__ahj, ambe__sxf = _count_overlap(right_key_arrs[0], febq__hprs[
            qcse__brlfv], vghr__zccdd[qcse__brlfv])
        if bjj__ahj != 0:
            bjj__ahj -= 1
            ambe__sxf += 1
        rwmy__mussa[qcse__brlfv] = ambe__sxf
        hwzzn__vio[qcse__brlfv] = bjj__ahj
        qcse__brlfv += 1
    while qcse__brlfv < tkx__lytup:
        rwmy__mussa[qcse__brlfv] = 1
        hwzzn__vio[qcse__brlfv] = len(right_key_arrs[0]) - 1
        qcse__brlfv += 1
    bodo.libs.distributed_api.alltoall(rwmy__mussa, vie__qagsf, 1)
    sibd__kffd = vie__qagsf.sum()
    loxq__iqh = np.empty(sibd__kffd, right_key_arrs[0].dtype)
    uuzs__vpng = alloc_arr_tup(sibd__kffd, right_data)
    exj__ojwaa = bodo.ir.join.calc_disp(vie__qagsf)
    bodo.libs.distributed_api.alltoallv(right_key_arrs[0], loxq__iqh,
        rwmy__mussa, vie__qagsf, hwzzn__vio, exj__ojwaa)
    bodo.libs.distributed_api.alltoallv_tup(right_data, uuzs__vpng,
        rwmy__mussa, vie__qagsf, hwzzn__vio, exj__ojwaa)
    return (loxq__iqh,), uuzs__vpng


@numba.njit
def _count_overlap(r_key_arr, start, end):
    ambe__sxf = 0
    bjj__ahj = 0
    cvrzw__maqou = 0
    while cvrzw__maqou < len(r_key_arr) and r_key_arr[cvrzw__maqou] < start:
        bjj__ahj += 1
        cvrzw__maqou += 1
    while cvrzw__maqou < len(r_key_arr) and start <= r_key_arr[cvrzw__maqou
        ] <= end:
        cvrzw__maqou += 1
        ambe__sxf += 1
    return bjj__ahj, ambe__sxf


import llvmlite.binding as ll
from bodo.libs import hdist
ll.add_symbol('c_alltoallv', hdist.c_alltoallv)


@numba.njit
def calc_disp(arr):
    znlsb__nvc = np.empty_like(arr)
    znlsb__nvc[0] = 0
    for qcse__brlfv in range(1, len(arr)):
        znlsb__nvc[qcse__brlfv] = znlsb__nvc[qcse__brlfv - 1] + arr[
            qcse__brlfv - 1]
    return znlsb__nvc


@numba.njit
def local_merge_asof(left_keys, right_keys, data_left, data_right):
    fpa__nyt = len(left_keys[0])
    fkqqh__ria = len(right_keys[0])
    znoya__wthyc = alloc_arr_tup(fpa__nyt, left_keys)
    tnale__aotxp = alloc_arr_tup(fpa__nyt, right_keys)
    fzso__fkol = alloc_arr_tup(fpa__nyt, data_left)
    bvedc__dxaby = alloc_arr_tup(fpa__nyt, data_right)
    shze__bwddt = 0
    rwui__wdxfy = 0
    for shze__bwddt in range(fpa__nyt):
        if rwui__wdxfy < 0:
            rwui__wdxfy = 0
        while rwui__wdxfy < fkqqh__ria and getitem_arr_tup(right_keys,
            rwui__wdxfy) <= getitem_arr_tup(left_keys, shze__bwddt):
            rwui__wdxfy += 1
        rwui__wdxfy -= 1
        setitem_arr_tup(znoya__wthyc, shze__bwddt, getitem_arr_tup(
            left_keys, shze__bwddt))
        setitem_arr_tup(fzso__fkol, shze__bwddt, getitem_arr_tup(data_left,
            shze__bwddt))
        if rwui__wdxfy >= 0:
            setitem_arr_tup(tnale__aotxp, shze__bwddt, getitem_arr_tup(
                right_keys, rwui__wdxfy))
            setitem_arr_tup(bvedc__dxaby, shze__bwddt, getitem_arr_tup(
                data_right, rwui__wdxfy))
        else:
            bodo.libs.array_kernels.setna_tup(tnale__aotxp, shze__bwddt)
            bodo.libs.array_kernels.setna_tup(bvedc__dxaby, shze__bwddt)
    return znoya__wthyc, tnale__aotxp, fzso__fkol, bvedc__dxaby


def copy_arr_tup(arrs):
    return tuple(a.copy() for a in arrs)


@overload(copy_arr_tup, no_unliteral=True)
def copy_arr_tup_overload(arrs):
    ambe__sxf = arrs.count
    func_text = 'def f(arrs):\n'
    func_text += '  return ({},)\n'.format(','.join('arrs[{}].copy()'.
        format(qcse__brlfv) for qcse__brlfv in range(ambe__sxf)))
    nuday__mud = {}
    exec(func_text, {}, nuday__mud)
    sktq__gwfw = nuday__mud['f']
    return sktq__gwfw
