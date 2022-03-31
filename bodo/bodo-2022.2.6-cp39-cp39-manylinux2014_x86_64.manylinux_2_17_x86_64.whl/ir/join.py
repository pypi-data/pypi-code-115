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
        duecu__fjtkt = func.signature
        wxwn__znoro = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64), lir
            .IntType(64)])
        aioz__aes = cgutils.get_or_insert_function(builder.module,
            wxwn__znoro, sym._literal_value)
        builder.call(aioz__aes, [context.get_constant_null(duecu__fjtkt.
            args[0]), context.get_constant_null(duecu__fjtkt.args[1]),
            context.get_constant_null(duecu__fjtkt.args[2]), context.
            get_constant_null(duecu__fjtkt.args[3]), context.
            get_constant_null(duecu__fjtkt.args[4]), context.
            get_constant_null(duecu__fjtkt.args[5]), context.get_constant(
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
        self.left_cond_cols = set(tty__efsc for tty__efsc in left_vars.keys
            () if f'(left.{tty__efsc})' in gen_cond_expr)
        self.right_cond_cols = set(tty__efsc for tty__efsc in right_vars.
            keys() if f'(right.{tty__efsc})' in gen_cond_expr)
        bdaur__yoy = set(left_keys) & set(right_keys)
        djd__mrx = set(left_vars.keys()) & set(right_vars.keys())
        auy__nae = djd__mrx - bdaur__yoy
        vect_same_key = []
        n_keys = len(left_keys)
        for eazv__zeile in range(n_keys):
            jlrq__lzco = left_keys[eazv__zeile]
            bre__sbju = right_keys[eazv__zeile]
            vect_same_key.append(jlrq__lzco == bre__sbju)
        self.vect_same_key = vect_same_key
        self.column_origins = {(str(tty__efsc) + suffix_x if tty__efsc in
            auy__nae else tty__efsc): ('left', tty__efsc) for tty__efsc in
            left_vars.keys()}
        self.column_origins.update({(str(tty__efsc) + suffix_y if tty__efsc in
            auy__nae else tty__efsc): ('right', tty__efsc) for tty__efsc in
            right_vars.keys()})
        if '$_bodo_index_' in auy__nae:
            auy__nae.remove('$_bodo_index_')
        self.add_suffix = auy__nae

    def __repr__(self):
        eye__lrr = ''
        for tty__efsc, rcy__jix in self.out_data_vars.items():
            eye__lrr += "'{}':{}, ".format(tty__efsc, rcy__jix.name)
        alm__tlnk = '{}{{{}}}'.format(self.df_out, eye__lrr)
        mttbq__orn = ''
        for tty__efsc, rcy__jix in self.left_vars.items():
            mttbq__orn += "'{}':{}, ".format(tty__efsc, rcy__jix.name)
        kynac__gtp = '{}{{{}}}'.format(self.left_df, mttbq__orn)
        mttbq__orn = ''
        for tty__efsc, rcy__jix in self.right_vars.items():
            mttbq__orn += "'{}':{}, ".format(tty__efsc, rcy__jix.name)
        zrlni__gftv = '{}{{{}}}'.format(self.right_df, mttbq__orn)
        return 'join [{}={}]: {} , {}, {}'.format(self.left_keys, self.
            right_keys, alm__tlnk, kynac__gtp, zrlni__gftv)


def join_array_analysis(join_node, equiv_set, typemap, array_analysis):
    ouwy__sych = []
    assert len(join_node.out_data_vars) > 0, 'empty join in array analysis'
    qdqa__pbv = []
    vwtqz__graj = list(join_node.left_vars.values())
    for abm__jlq in vwtqz__graj:
        gcgc__yult = typemap[abm__jlq.name]
        vwnz__bjgl = equiv_set.get_shape(abm__jlq)
        if vwnz__bjgl:
            qdqa__pbv.append(vwnz__bjgl[0])
    if len(qdqa__pbv) > 1:
        equiv_set.insert_equiv(*qdqa__pbv)
    qdqa__pbv = []
    vwtqz__graj = list(join_node.right_vars.values())
    for abm__jlq in vwtqz__graj:
        gcgc__yult = typemap[abm__jlq.name]
        vwnz__bjgl = equiv_set.get_shape(abm__jlq)
        if vwnz__bjgl:
            qdqa__pbv.append(vwnz__bjgl[0])
    if len(qdqa__pbv) > 1:
        equiv_set.insert_equiv(*qdqa__pbv)
    qdqa__pbv = []
    for abm__jlq in join_node.out_data_vars.values():
        gcgc__yult = typemap[abm__jlq.name]
        lfzmz__yifd = array_analysis._gen_shape_call(equiv_set, abm__jlq,
            gcgc__yult.ndim, None, ouwy__sych)
        equiv_set.insert_equiv(abm__jlq, lfzmz__yifd)
        qdqa__pbv.append(lfzmz__yifd[0])
        equiv_set.define(abm__jlq, set())
    if len(qdqa__pbv) > 1:
        equiv_set.insert_equiv(*qdqa__pbv)
    return [], ouwy__sych


numba.parfors.array_analysis.array_analysis_extensions[Join
    ] = join_array_analysis


def join_distributed_analysis(join_node, array_dists):
    juc__xesh = Distribution.OneD
    ezcj__uxic = Distribution.OneD
    for abm__jlq in join_node.left_vars.values():
        juc__xesh = Distribution(min(juc__xesh.value, array_dists[abm__jlq.
            name].value))
    for abm__jlq in join_node.right_vars.values():
        ezcj__uxic = Distribution(min(ezcj__uxic.value, array_dists[
            abm__jlq.name].value))
    xxbu__dpwi = Distribution.OneD_Var
    for abm__jlq in join_node.out_data_vars.values():
        if abm__jlq.name in array_dists:
            xxbu__dpwi = Distribution(min(xxbu__dpwi.value, array_dists[
                abm__jlq.name].value))
    npsnu__kic = Distribution(min(xxbu__dpwi.value, juc__xesh.value))
    ngiqi__xbrln = Distribution(min(xxbu__dpwi.value, ezcj__uxic.value))
    xxbu__dpwi = Distribution(max(npsnu__kic.value, ngiqi__xbrln.value))
    for abm__jlq in join_node.out_data_vars.values():
        array_dists[abm__jlq.name] = xxbu__dpwi
    if xxbu__dpwi != Distribution.OneD_Var:
        juc__xesh = xxbu__dpwi
        ezcj__uxic = xxbu__dpwi
    for abm__jlq in join_node.left_vars.values():
        array_dists[abm__jlq.name] = juc__xesh
    for abm__jlq in join_node.right_vars.values():
        array_dists[abm__jlq.name] = ezcj__uxic
    return


distributed_analysis.distributed_analysis_extensions[Join
    ] = join_distributed_analysis


def join_typeinfer(join_node, typeinferer):
    bdaur__yoy = set(join_node.left_keys) & set(join_node.right_keys)
    djd__mrx = set(join_node.left_vars.keys()) & set(join_node.right_vars.
        keys())
    auy__nae = djd__mrx - bdaur__yoy
    for vkhl__fbof, ybapo__hky in join_node.out_data_vars.items():
        if join_node.indicator and vkhl__fbof == '_merge':
            continue
        if not vkhl__fbof in join_node.column_origins:
            raise BodoError('join(): The variable ' + vkhl__fbof +
                ' is absent from the output')
        gqod__budhb = join_node.column_origins[vkhl__fbof]
        if gqod__budhb[0] == 'left':
            abm__jlq = join_node.left_vars[gqod__budhb[1]]
        else:
            abm__jlq = join_node.right_vars[gqod__budhb[1]]
        typeinferer.constraints.append(typeinfer.Propagate(dst=ybapo__hky.
            name, src=abm__jlq.name, loc=join_node.loc))
    return


typeinfer.typeinfer_extensions[Join] = join_typeinfer


def visit_vars_join(join_node, callback, cbdata):
    if debug_prints():
        print('visiting join vars for:', join_node)
        print('cbdata: ', sorted(cbdata.items()))
    for hpulf__rghiy in list(join_node.left_vars.keys()):
        join_node.left_vars[hpulf__rghiy] = visit_vars_inner(join_node.
            left_vars[hpulf__rghiy], callback, cbdata)
    for hpulf__rghiy in list(join_node.right_vars.keys()):
        join_node.right_vars[hpulf__rghiy] = visit_vars_inner(join_node.
            right_vars[hpulf__rghiy], callback, cbdata)
    for hpulf__rghiy in list(join_node.out_data_vars.keys()):
        join_node.out_data_vars[hpulf__rghiy] = visit_vars_inner(join_node.
            out_data_vars[hpulf__rghiy], callback, cbdata)


ir_utils.visit_vars_extensions[Join] = visit_vars_join


def remove_dead_join(join_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    mskt__hxixj = []
    hcl__hbubp = True
    for hpulf__rghiy, abm__jlq in join_node.out_data_vars.items():
        if abm__jlq.name in lives:
            hcl__hbubp = False
            continue
        if hpulf__rghiy == '$_bodo_index_':
            continue
        if join_node.indicator and hpulf__rghiy == '_merge':
            mskt__hxixj.append('_merge')
            join_node.indicator = False
            continue
        vibo__kax, qtpfn__nbj = join_node.column_origins[hpulf__rghiy]
        if (vibo__kax == 'left' and qtpfn__nbj not in join_node.left_keys and
            qtpfn__nbj not in join_node.left_cond_cols):
            join_node.left_vars.pop(qtpfn__nbj)
            mskt__hxixj.append(hpulf__rghiy)
        if (vibo__kax == 'right' and qtpfn__nbj not in join_node.right_keys and
            qtpfn__nbj not in join_node.right_cond_cols):
            join_node.right_vars.pop(qtpfn__nbj)
            mskt__hxixj.append(hpulf__rghiy)
    for cname in mskt__hxixj:
        join_node.out_data_vars.pop(cname)
    if hcl__hbubp:
        return None
    return join_node


ir_utils.remove_dead_extensions[Join] = remove_dead_join


def join_usedefs(join_node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    use_set.update({rcy__jix.name for rcy__jix in join_node.left_vars.values()}
        )
    use_set.update({rcy__jix.name for rcy__jix in join_node.right_vars.
        values()})
    def_set.update({rcy__jix.name for rcy__jix in join_node.out_data_vars.
        values()})
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


numba.core.analysis.ir_extension_usedefs[Join] = join_usedefs


def get_copies_join(join_node, typemap):
    yzs__avfu = set(rcy__jix.name for rcy__jix in join_node.out_data_vars.
        values())
    return set(), yzs__avfu


ir_utils.copy_propagate_extensions[Join] = get_copies_join


def apply_copies_join(join_node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    for hpulf__rghiy in list(join_node.left_vars.keys()):
        join_node.left_vars[hpulf__rghiy] = replace_vars_inner(join_node.
            left_vars[hpulf__rghiy], var_dict)
    for hpulf__rghiy in list(join_node.right_vars.keys()):
        join_node.right_vars[hpulf__rghiy] = replace_vars_inner(join_node.
            right_vars[hpulf__rghiy], var_dict)
    for hpulf__rghiy in list(join_node.out_data_vars.keys()):
        join_node.out_data_vars[hpulf__rghiy] = replace_vars_inner(join_node
            .out_data_vars[hpulf__rghiy], var_dict)
    return


ir_utils.apply_copy_propagate_extensions[Join] = apply_copies_join


def build_join_definitions(join_node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for abm__jlq in join_node.out_data_vars.values():
        definitions[abm__jlq.name].append(join_node)
    return definitions


ir_utils.build_defs_extensions[Join] = build_join_definitions


def join_distributed_run(join_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    left_parallel, right_parallel = False, False
    if array_dists is not None:
        left_parallel, right_parallel = _get_table_parallel_flags(join_node,
            array_dists)
    n_keys = len(join_node.left_keys)
    pvwfl__vqnj = tuple(join_node.left_vars[tty__efsc] for tty__efsc in
        join_node.left_keys)
    bnpq__edr = tuple(join_node.right_vars[tty__efsc] for tty__efsc in
        join_node.right_keys)
    eevn__ffpmb = tuple(join_node.left_vars.keys())
    gtcpy__wfr = tuple(join_node.right_vars.keys())
    qsjl__adw = ()
    nfht__afsmp = ()
    optional_column = False
    if (join_node.left_index and not join_node.right_index and not
        join_node.is_join):
        ysbsj__zmiek = join_node.right_keys[0]
        if ysbsj__zmiek in eevn__ffpmb:
            nfht__afsmp = ysbsj__zmiek,
            qsjl__adw = join_node.right_vars[ysbsj__zmiek],
            optional_column = True
    if (join_node.right_index and not join_node.left_index and not
        join_node.is_join):
        ysbsj__zmiek = join_node.left_keys[0]
        if ysbsj__zmiek in gtcpy__wfr:
            nfht__afsmp = ysbsj__zmiek,
            qsjl__adw = join_node.left_vars[ysbsj__zmiek],
            optional_column = True
    qfr__vvd = tuple(join_node.out_data_vars[cname] for cname in nfht__afsmp)
    ougi__ywanb = tuple(rcy__jix for yblvl__cpx, rcy__jix in sorted(
        join_node.left_vars.items(), key=lambda a: str(a[0])) if yblvl__cpx
         not in join_node.left_keys)
    dhe__kmb = tuple(rcy__jix for yblvl__cpx, rcy__jix in sorted(join_node.
        right_vars.items(), key=lambda a: str(a[0])) if yblvl__cpx not in
        join_node.right_keys)
    qiv__wmeys = qsjl__adw + pvwfl__vqnj + bnpq__edr + ougi__ywanb + dhe__kmb
    xwn__tvbg = tuple(typemap[rcy__jix.name] for rcy__jix in qiv__wmeys)
    ocg__pisf = tuple('opti_c' + str(paj__mgb) for paj__mgb in range(len(
        qsjl__adw)))
    left_other_names = tuple('t1_c' + str(paj__mgb) for paj__mgb in range(
        len(ougi__ywanb)))
    right_other_names = tuple('t2_c' + str(paj__mgb) for paj__mgb in range(
        len(dhe__kmb)))
    left_other_types = tuple([typemap[tty__efsc.name] for tty__efsc in
        ougi__ywanb])
    right_other_types = tuple([typemap[tty__efsc.name] for tty__efsc in
        dhe__kmb])
    left_key_names = tuple('t1_key' + str(paj__mgb) for paj__mgb in range(
        n_keys))
    right_key_names = tuple('t2_key' + str(paj__mgb) for paj__mgb in range(
        n_keys))
    glbs = {}
    loc = join_node.loc
    func_text = 'def f({}{}, {},{}{}{}):\n'.format('{},'.format(ocg__pisf[0
        ]) if len(ocg__pisf) == 1 else '', ','.join(left_key_names), ','.
        join(right_key_names), ','.join(left_other_names), ',' if len(
        left_other_names) != 0 else '', ','.join(right_other_names))
    left_key_types = tuple(typemap[rcy__jix.name] for rcy__jix in pvwfl__vqnj)
    right_key_types = tuple(typemap[rcy__jix.name] for rcy__jix in bnpq__edr)
    for paj__mgb in range(n_keys):
        glbs[f'key_type_{paj__mgb}'] = _match_join_key_types(left_key_types
            [paj__mgb], right_key_types[paj__mgb], loc)
    func_text += '    t1_keys = ({},)\n'.format(', '.join(
        f'bodo.utils.utils.astype({left_key_names[paj__mgb]}, key_type_{paj__mgb})'
         for paj__mgb in range(n_keys)))
    func_text += '    t2_keys = ({},)\n'.format(', '.join(
        f'bodo.utils.utils.astype({right_key_names[paj__mgb]}, key_type_{paj__mgb})'
         for paj__mgb in range(n_keys)))
    func_text += '    data_left = ({}{})\n'.format(','.join(
        left_other_names), ',' if len(left_other_names) != 0 else '')
    func_text += '    data_right = ({}{})\n'.format(','.join(
        right_other_names), ',' if len(right_other_names) != 0 else '')
    usuan__xjqa = []
    for cname in join_node.left_keys:
        if cname in join_node.add_suffix:
            ktwy__pblxu = str(cname) + join_node.suffix_x
        else:
            ktwy__pblxu = cname
        assert ktwy__pblxu in join_node.out_data_vars
        usuan__xjqa.append(join_node.out_data_vars[ktwy__pblxu])
    for paj__mgb, cname in enumerate(join_node.right_keys):
        if not join_node.vect_same_key[paj__mgb] and not join_node.is_join:
            if cname in join_node.add_suffix:
                ktwy__pblxu = str(cname) + join_node.suffix_y
            else:
                ktwy__pblxu = cname
            assert ktwy__pblxu in join_node.out_data_vars
            usuan__xjqa.append(join_node.out_data_vars[ktwy__pblxu])

    def _get_out_col_var(cname, is_left):
        if cname in join_node.add_suffix:
            if is_left:
                ktwy__pblxu = str(cname) + join_node.suffix_x
            else:
                ktwy__pblxu = str(cname) + join_node.suffix_y
        else:
            ktwy__pblxu = cname
        return join_node.out_data_vars[ktwy__pblxu]
    pxpp__imm = qfr__vvd + tuple(usuan__xjqa)
    pxpp__imm += tuple(_get_out_col_var(yblvl__cpx, True) for yblvl__cpx,
        rcy__jix in sorted(join_node.left_vars.items(), key=lambda a: str(a
        [0])) if yblvl__cpx not in join_node.left_keys)
    pxpp__imm += tuple(_get_out_col_var(yblvl__cpx, False) for yblvl__cpx,
        rcy__jix in sorted(join_node.right_vars.items(), key=lambda a: str(
        a[0])) if yblvl__cpx not in join_node.right_keys)
    if join_node.indicator:
        pxpp__imm += _get_out_col_var('_merge', False),
    bauik__sejvz = [('t3_c' + str(paj__mgb)) for paj__mgb in range(len(
        pxpp__imm))]
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
            right_parallel, glbs, [typemap[rcy__jix.name] for rcy__jix in
            pxpp__imm], join_node.loc, join_node.indicator, join_node.
            is_na_equal, general_cond_cfunc, left_col_nums, right_col_nums)
    if join_node.how == 'asof':
        for paj__mgb in range(len(left_other_names)):
            func_text += '    left_{} = out_data_left[{}]\n'.format(paj__mgb,
                paj__mgb)
        for paj__mgb in range(len(right_other_names)):
            func_text += '    right_{} = out_data_right[{}]\n'.format(paj__mgb,
                paj__mgb)
        for paj__mgb in range(n_keys):
            func_text += f'    t1_keys_{paj__mgb} = out_t1_keys[{paj__mgb}]\n'
        for paj__mgb in range(n_keys):
            func_text += f'    t2_keys_{paj__mgb} = out_t2_keys[{paj__mgb}]\n'
    idx = 0
    if optional_column:
        func_text += f'    {bauik__sejvz[idx]} = opti_0\n'
        idx += 1
    for paj__mgb in range(n_keys):
        func_text += f'    {bauik__sejvz[idx]} = t1_keys_{paj__mgb}\n'
        idx += 1
    for paj__mgb in range(n_keys):
        if not join_node.vect_same_key[paj__mgb] and not join_node.is_join:
            func_text += f'    {bauik__sejvz[idx]} = t2_keys_{paj__mgb}\n'
            idx += 1
    for paj__mgb in range(len(left_other_names)):
        func_text += f'    {bauik__sejvz[idx]} = left_{paj__mgb}\n'
        idx += 1
    for paj__mgb in range(len(right_other_names)):
        func_text += f'    {bauik__sejvz[idx]} = right_{paj__mgb}\n'
        idx += 1
    if join_node.indicator:
        func_text += f'    {bauik__sejvz[idx]} = indicator_col\n'
        idx += 1
    frrx__cbej = {}
    exec(func_text, {}, frrx__cbej)
    sikr__pmlfu = frrx__cbej['f']
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
    mxl__tdjl = compile_to_numba_ir(sikr__pmlfu, glbs, typingctx=typingctx,
        targetctx=targetctx, arg_typs=xwn__tvbg, typemap=typemap, calltypes
        =calltypes).blocks.popitem()[1]
    replace_arg_nodes(mxl__tdjl, qiv__wmeys)
    obj__uxnu = mxl__tdjl.body[:-3]
    for paj__mgb in range(len(pxpp__imm)):
        obj__uxnu[-len(pxpp__imm) + paj__mgb].target = pxpp__imm[paj__mgb]
    return obj__uxnu


distributed_pass.distributed_run_extensions[Join] = join_distributed_run


def _gen_general_cond_cfunc(join_node, typemap):
    expr = join_node.gen_cond_expr
    if not expr:
        return None, [], []
    kih__ygeod = next_label()
    pcq__mrz = _get_col_to_ind(join_node.left_keys, join_node.left_vars)
    hkn__jif = _get_col_to_ind(join_node.right_keys, join_node.right_vars)
    table_getitem_funcs = {'bodo': bodo, 'numba': numba, 'is_null_pointer':
        is_null_pointer}
    na_check_name = 'NOT_NA'
    func_text = f"""def bodo_join_gen_cond{kih__ygeod}(left_table, right_table, left_data1, right_data1, left_null_bitmap, right_null_bitmap, left_ind, right_ind):
"""
    func_text += '  if is_null_pointer(left_table):\n'
    func_text += '    return False\n'
    expr, func_text, left_col_nums = _replace_column_accesses(expr,
        pcq__mrz, typemap, join_node.left_vars, table_getitem_funcs,
        func_text, 'left', len(join_node.left_keys), na_check_name)
    expr, func_text, right_col_nums = _replace_column_accesses(expr,
        hkn__jif, typemap, join_node.right_vars, table_getitem_funcs,
        func_text, 'right', len(join_node.right_keys), na_check_name)
    func_text += f'  return {expr}'
    frrx__cbej = {}
    exec(func_text, table_getitem_funcs, frrx__cbej)
    fcc__hnpqp = frrx__cbej[f'bodo_join_gen_cond{kih__ygeod}']
    cbrkr__klucq = types.bool_(types.voidptr, types.voidptr, types.voidptr,
        types.voidptr, types.voidptr, types.voidptr, types.int64, types.int64)
    poqqx__iozt = numba.cfunc(cbrkr__klucq, nopython=True)(fcc__hnpqp)
    join_gen_cond_cfunc[poqqx__iozt.native_name] = poqqx__iozt
    join_gen_cond_cfunc_addr[poqqx__iozt.native_name] = poqqx__iozt.address
    return poqqx__iozt, left_col_nums, right_col_nums


def _replace_column_accesses(expr, col_to_ind, typemap, col_vars,
    table_getitem_funcs, func_text, table_name, n_keys, na_check_name):
    pmnmz__lyeva = []
    for tty__efsc, ylthq__qakdl in col_to_ind.items():
        cname = f'({table_name}.{tty__efsc})'
        if cname not in expr:
            continue
        yafho__eoa = f'getitem_{table_name}_val_{ylthq__qakdl}'
        xirus__rppp = f'_bodo_{table_name}_val_{ylthq__qakdl}'
        dsuc__oqvrc = typemap[col_vars[tty__efsc].name]
        if is_str_arr_type(dsuc__oqvrc):
            func_text += f"""  {xirus__rppp}, {xirus__rppp}_size = {yafho__eoa}({table_name}_table, {table_name}_ind)
"""
            func_text += f"""  {xirus__rppp} = bodo.libs.str_arr_ext.decode_utf8({xirus__rppp}, {xirus__rppp}_size)
"""
        else:
            func_text += (
                f'  {xirus__rppp} = {yafho__eoa}({table_name}_data1, {table_name}_ind)\n'
                )
        table_getitem_funcs[yafho__eoa
            ] = bodo.libs.array._gen_row_access_intrinsic(dsuc__oqvrc,
            ylthq__qakdl)
        expr = expr.replace(cname, xirus__rppp)
        zfa__aqmb = f'({na_check_name}.{table_name}.{tty__efsc})'
        if zfa__aqmb in expr:
            ioq__grqhh = f'nacheck_{table_name}_val_{ylthq__qakdl}'
            qmeul__lmug = f'_bodo_isna_{table_name}_val_{ylthq__qakdl}'
            if (isinstance(dsuc__oqvrc, bodo.libs.int_arr_ext.
                IntegerArrayType) or dsuc__oqvrc == bodo.libs.bool_arr_ext.
                boolean_array or is_str_arr_type(dsuc__oqvrc)):
                func_text += f"""  {qmeul__lmug} = {ioq__grqhh}({table_name}_null_bitmap, {table_name}_ind)
"""
            else:
                func_text += f"""  {qmeul__lmug} = {ioq__grqhh}({table_name}_data1, {table_name}_ind)
"""
            table_getitem_funcs[ioq__grqhh
                ] = bodo.libs.array._gen_row_na_check_intrinsic(dsuc__oqvrc,
                ylthq__qakdl)
            expr = expr.replace(zfa__aqmb, qmeul__lmug)
        if ylthq__qakdl >= n_keys:
            pmnmz__lyeva.append(ylthq__qakdl)
    return expr, func_text, pmnmz__lyeva


def _get_col_to_ind(key_names, col_vars):
    n_keys = len(key_names)
    col_to_ind = {tty__efsc: paj__mgb for paj__mgb, tty__efsc in enumerate(
        key_names)}
    paj__mgb = n_keys
    for tty__efsc in sorted(col_vars, key=lambda a: str(a)):
        if tty__efsc in key_names:
            continue
        col_to_ind[tty__efsc] = paj__mgb
        paj__mgb += 1
    return col_to_ind


def _match_join_key_types(t1, t2, loc):
    if t1 == t2:
        return t1
    try:
        arr = dtype_to_array_type(find_common_np_dtype([t1, t2]))
        return to_nullable_type(arr) if is_nullable_type(t1
            ) or is_nullable_type(t2) else arr
    except Exception as mxflj__wsw:
        if is_str_arr_type(t1) and is_str_arr_type(t2):
            return bodo.string_array_type
        raise BodoError(f'Join key types {t1} and {t2} do not match', loc=loc)


def _get_table_parallel_flags(join_node, array_dists):
    pmk__daew = (distributed_pass.Distribution.OneD, distributed_pass.
        Distribution.OneD_Var)
    left_parallel = all(array_dists[rcy__jix.name] in pmk__daew for
        rcy__jix in join_node.left_vars.values())
    right_parallel = all(array_dists[rcy__jix.name] in pmk__daew for
        rcy__jix in join_node.right_vars.values())
    if not left_parallel:
        assert not any(array_dists[rcy__jix.name] in pmk__daew for rcy__jix in
            join_node.left_vars.values())
    if not right_parallel:
        assert not any(array_dists[rcy__jix.name] in pmk__daew for rcy__jix in
            join_node.right_vars.values())
    if left_parallel or right_parallel:
        assert all(array_dists[rcy__jix.name] in pmk__daew for rcy__jix in
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
    fbbxz__tjtob = []
    for paj__mgb in range(len(left_key_names)):
        wzrr__azmk = _match_join_key_types(left_key_types[paj__mgb],
            right_key_types[paj__mgb], loc)
        fbbxz__tjtob.append(needs_typechange(wzrr__azmk, is_right,
            vect_same_key[paj__mgb]))
    for paj__mgb in range(len(left_other_names)):
        fbbxz__tjtob.append(needs_typechange(left_other_types[paj__mgb],
            is_right, False))
    for paj__mgb in range(len(right_key_names)):
        if not vect_same_key[paj__mgb] and not is_join:
            wzrr__azmk = _match_join_key_types(left_key_types[paj__mgb],
                right_key_types[paj__mgb], loc)
            fbbxz__tjtob.append(needs_typechange(wzrr__azmk, is_left, False))
    for paj__mgb in range(len(right_other_names)):
        fbbxz__tjtob.append(needs_typechange(right_other_types[paj__mgb],
            is_left, False))

    def get_out_type(idx, in_type, in_name, need_nullable, is_same_key):
        if isinstance(in_type, types.Array) and not is_dtype_nullable(in_type
            .dtype) and need_nullable and not is_same_key:
            if isinstance(in_type.dtype, types.Integer):
                tcgoq__phz = IntDtype(in_type.dtype).name
                assert tcgoq__phz.endswith('Dtype()')
                tcgoq__phz = tcgoq__phz[:-7]
                sjrf__mfp = f"""    typ_{idx} = bodo.hiframes.pd_series_ext.get_series_data(pd.Series([1], dtype="{tcgoq__phz}"))
"""
                ieze__oqbee = f'typ_{idx}'
            else:
                assert in_type.dtype == types.bool_, 'unexpected non-nullable type in join'
                sjrf__mfp = (
                    f'    typ_{idx} = bodo.libs.bool_arr_ext.alloc_bool_array(1)\n'
                    )
                ieze__oqbee = f'typ_{idx}'
        elif in_type == bodo.string_array_type:
            sjrf__mfp = (
                f'    typ_{idx} = bodo.libs.str_arr_ext.pre_alloc_string_array(0, 0)\n'
                )
            ieze__oqbee = f'typ_{idx}'
        else:
            sjrf__mfp = ''
            ieze__oqbee = in_name
        return sjrf__mfp, ieze__oqbee
    n_keys = len(left_key_names)
    func_text = '    # beginning of _gen_local_hash_join\n'
    owsuu__gbnur = []
    for paj__mgb in range(n_keys):
        owsuu__gbnur.append('t1_keys[{}]'.format(paj__mgb))
    for paj__mgb in range(len(left_other_names)):
        owsuu__gbnur.append('data_left[{}]'.format(paj__mgb))
    func_text += '    info_list_total_l = [{}]\n'.format(','.join(
        'array_to_info({})'.format(a) for a in owsuu__gbnur))
    func_text += '    table_left = arr_info_list_to_table(info_list_total_l)\n'
    fvgf__uixs = []
    for paj__mgb in range(n_keys):
        fvgf__uixs.append('t2_keys[{}]'.format(paj__mgb))
    for paj__mgb in range(len(right_other_names)):
        fvgf__uixs.append('data_right[{}]'.format(paj__mgb))
    func_text += '    info_list_total_r = [{}]\n'.format(','.join(
        'array_to_info({})'.format(a) for a in fvgf__uixs))
    func_text += (
        '    table_right = arr_info_list_to_table(info_list_total_r)\n')
    func_text += '    vect_same_key = np.array([{}])\n'.format(','.join('1' if
        vdlkt__kuu else '0' for vdlkt__kuu in vect_same_key))
    func_text += '    vect_need_typechange = np.array([{}])\n'.format(','.
        join('1' if vdlkt__kuu else '0' for vdlkt__kuu in fbbxz__tjtob))
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
        ydfef__uuzgl = get_out_type(idx, out_types[idx], 'opti_c0', False, 
            False)
        func_text += ydfef__uuzgl[0]
        glbs[f'out_type_{idx}'] = out_types[idx]
        func_text += f"""    opti_0 = info_to_array(info_from_table(out_table, {idx}), {ydfef__uuzgl[1]})
"""
        idx += 1
    for paj__mgb, fjxuy__hxh in enumerate(left_key_names):
        wzrr__azmk = _match_join_key_types(left_key_types[paj__mgb],
            right_key_types[paj__mgb], loc)
        ydfef__uuzgl = get_out_type(idx, wzrr__azmk, f't1_keys[{paj__mgb}]',
            is_right, vect_same_key[paj__mgb])
        func_text += ydfef__uuzgl[0]
        glbs[f'out_type_{idx}'] = out_types[idx]
        if wzrr__azmk != left_key_types[paj__mgb] and left_key_types[paj__mgb
            ] != bodo.dict_str_arr_type:
            func_text += f"""    t1_keys_{paj__mgb} = bodo.utils.utils.astype(info_to_array(info_from_table(out_table, {idx}), {ydfef__uuzgl[1]}), out_type_{idx})
"""
        else:
            func_text += f"""    t1_keys_{paj__mgb} = info_to_array(info_from_table(out_table, {idx}), {ydfef__uuzgl[1]})
"""
        idx += 1
    for paj__mgb, fjxuy__hxh in enumerate(left_other_names):
        ydfef__uuzgl = get_out_type(idx, left_other_types[paj__mgb],
            fjxuy__hxh, is_right, False)
        func_text += ydfef__uuzgl[0]
        func_text += (
            '    left_{} = info_to_array(info_from_table(out_table, {}), {})\n'
            .format(paj__mgb, idx, ydfef__uuzgl[1]))
        idx += 1
    for paj__mgb, fjxuy__hxh in enumerate(right_key_names):
        if not vect_same_key[paj__mgb] and not is_join:
            wzrr__azmk = _match_join_key_types(left_key_types[paj__mgb],
                right_key_types[paj__mgb], loc)
            ydfef__uuzgl = get_out_type(idx, wzrr__azmk,
                f't2_keys[{paj__mgb}]', is_left, False)
            func_text += ydfef__uuzgl[0]
            glbs[f'out_type_{idx}'] = out_types[idx - len(left_other_names)]
            if wzrr__azmk != right_key_types[paj__mgb] and right_key_types[
                paj__mgb] != bodo.dict_str_arr_type:
                func_text += f"""    t2_keys_{paj__mgb} = bodo.utils.utils.astype(info_to_array(info_from_table(out_table, {idx}), {ydfef__uuzgl[1]}), out_type_{idx})
"""
            else:
                func_text += f"""    t2_keys_{paj__mgb} = info_to_array(info_from_table(out_table, {idx}), {ydfef__uuzgl[1]})
"""
            idx += 1
    for paj__mgb, fjxuy__hxh in enumerate(right_other_names):
        ydfef__uuzgl = get_out_type(idx, right_other_types[paj__mgb],
            fjxuy__hxh, is_left, False)
        func_text += ydfef__uuzgl[0]
        func_text += (
            '    right_{} = info_to_array(info_from_table(out_table, {}), {})\n'
            .format(paj__mgb, idx, ydfef__uuzgl[1]))
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
    zou__kwuc = bodo.libs.distributed_api.get_size()
    mzzp__tyy = np.empty(zou__kwuc, left_key_arrs[0].dtype)
    pbe__cdrbn = np.empty(zou__kwuc, left_key_arrs[0].dtype)
    bodo.libs.distributed_api.allgather(mzzp__tyy, left_key_arrs[0][0])
    bodo.libs.distributed_api.allgather(pbe__cdrbn, left_key_arrs[0][-1])
    psbas__zzbp = np.zeros(zou__kwuc, np.int32)
    fij__omqu = np.zeros(zou__kwuc, np.int32)
    usks__fpnq = np.zeros(zou__kwuc, np.int32)
    omnqw__ejl = right_key_arrs[0][0]
    xchjr__pizco = right_key_arrs[0][-1]
    grpl__hbju = -1
    paj__mgb = 0
    while paj__mgb < zou__kwuc - 1 and pbe__cdrbn[paj__mgb] < omnqw__ejl:
        paj__mgb += 1
    while paj__mgb < zou__kwuc and mzzp__tyy[paj__mgb] <= xchjr__pizco:
        grpl__hbju, qaog__jkzw = _count_overlap(right_key_arrs[0],
            mzzp__tyy[paj__mgb], pbe__cdrbn[paj__mgb])
        if grpl__hbju != 0:
            grpl__hbju -= 1
            qaog__jkzw += 1
        psbas__zzbp[paj__mgb] = qaog__jkzw
        fij__omqu[paj__mgb] = grpl__hbju
        paj__mgb += 1
    while paj__mgb < zou__kwuc:
        psbas__zzbp[paj__mgb] = 1
        fij__omqu[paj__mgb] = len(right_key_arrs[0]) - 1
        paj__mgb += 1
    bodo.libs.distributed_api.alltoall(psbas__zzbp, usks__fpnq, 1)
    qpcrz__geq = usks__fpnq.sum()
    zlkq__dnt = np.empty(qpcrz__geq, right_key_arrs[0].dtype)
    bdga__lvb = alloc_arr_tup(qpcrz__geq, right_data)
    mrs__uyws = bodo.ir.join.calc_disp(usks__fpnq)
    bodo.libs.distributed_api.alltoallv(right_key_arrs[0], zlkq__dnt,
        psbas__zzbp, usks__fpnq, fij__omqu, mrs__uyws)
    bodo.libs.distributed_api.alltoallv_tup(right_data, bdga__lvb,
        psbas__zzbp, usks__fpnq, fij__omqu, mrs__uyws)
    return (zlkq__dnt,), bdga__lvb


@numba.njit
def _count_overlap(r_key_arr, start, end):
    qaog__jkzw = 0
    grpl__hbju = 0
    wll__uwue = 0
    while wll__uwue < len(r_key_arr) and r_key_arr[wll__uwue] < start:
        grpl__hbju += 1
        wll__uwue += 1
    while wll__uwue < len(r_key_arr) and start <= r_key_arr[wll__uwue] <= end:
        wll__uwue += 1
        qaog__jkzw += 1
    return grpl__hbju, qaog__jkzw


import llvmlite.binding as ll
from bodo.libs import hdist
ll.add_symbol('c_alltoallv', hdist.c_alltoallv)


@numba.njit
def calc_disp(arr):
    mlola__rpxpm = np.empty_like(arr)
    mlola__rpxpm[0] = 0
    for paj__mgb in range(1, len(arr)):
        mlola__rpxpm[paj__mgb] = mlola__rpxpm[paj__mgb - 1] + arr[paj__mgb - 1]
    return mlola__rpxpm


@numba.njit
def local_merge_asof(left_keys, right_keys, data_left, data_right):
    jzm__twqi = len(left_keys[0])
    emplz__yddns = len(right_keys[0])
    gkstk__jnogz = alloc_arr_tup(jzm__twqi, left_keys)
    dkm__tiox = alloc_arr_tup(jzm__twqi, right_keys)
    ljdiq__riqgd = alloc_arr_tup(jzm__twqi, data_left)
    mrpd__jkf = alloc_arr_tup(jzm__twqi, data_right)
    vgxx__ngwc = 0
    thjn__dfz = 0
    for vgxx__ngwc in range(jzm__twqi):
        if thjn__dfz < 0:
            thjn__dfz = 0
        while thjn__dfz < emplz__yddns and getitem_arr_tup(right_keys,
            thjn__dfz) <= getitem_arr_tup(left_keys, vgxx__ngwc):
            thjn__dfz += 1
        thjn__dfz -= 1
        setitem_arr_tup(gkstk__jnogz, vgxx__ngwc, getitem_arr_tup(left_keys,
            vgxx__ngwc))
        setitem_arr_tup(ljdiq__riqgd, vgxx__ngwc, getitem_arr_tup(data_left,
            vgxx__ngwc))
        if thjn__dfz >= 0:
            setitem_arr_tup(dkm__tiox, vgxx__ngwc, getitem_arr_tup(
                right_keys, thjn__dfz))
            setitem_arr_tup(mrpd__jkf, vgxx__ngwc, getitem_arr_tup(
                data_right, thjn__dfz))
        else:
            bodo.libs.array_kernels.setna_tup(dkm__tiox, vgxx__ngwc)
            bodo.libs.array_kernels.setna_tup(mrpd__jkf, vgxx__ngwc)
    return gkstk__jnogz, dkm__tiox, ljdiq__riqgd, mrpd__jkf


def copy_arr_tup(arrs):
    return tuple(a.copy() for a in arrs)


@overload(copy_arr_tup, no_unliteral=True)
def copy_arr_tup_overload(arrs):
    qaog__jkzw = arrs.count
    func_text = 'def f(arrs):\n'
    func_text += '  return ({},)\n'.format(','.join('arrs[{}].copy()'.
        format(paj__mgb) for paj__mgb in range(qaog__jkzw)))
    frrx__cbej = {}
    exec(func_text, {}, frrx__cbej)
    wyjpo__yed = frrx__cbej['f']
    return wyjpo__yed
