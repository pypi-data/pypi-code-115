"""
Helper functions for transformations.
"""
import itertools
import math
import operator
import types as pytypes
from collections import namedtuple
import numba
import numpy as np
import pandas as pd
from numba.core import ir, ir_utils, types
from numba.core.ir_utils import GuardException, build_definitions, compile_to_numba_ir, compute_cfg_from_blocks, find_callname, find_const, get_definition, guard, is_setitem, mk_unique_var, replace_arg_nodes, require
from numba.core.registry import CPUDispatcher
from numba.core.typing.templates import fold_arguments
import bodo
from bodo.libs.array_item_arr_ext import ArrayItemArrayType
from bodo.libs.map_arr_ext import MapArrayType
from bodo.libs.str_arr_ext import string_array_type
from bodo.libs.struct_arr_ext import StructArrayType, StructType
from bodo.libs.tuple_arr_ext import TupleArrayType
from bodo.utils.typing import BodoConstUpdatedError, BodoError, can_literalize_type, get_literal_value, get_overload_const_bool, get_overload_const_list, is_literal_type, is_overload_constant_bool
from bodo.utils.utils import is_array_typ, is_assign, is_call, is_expr
ReplaceFunc = namedtuple('ReplaceFunc', ['func', 'arg_types', 'args',
    'glbls', 'inline_bodo_calls', 'run_full_pipeline', 'pre_nodes'])
bodo_types_with_params = {'ArrayItemArrayType', 'CSRMatrixType',
    'CategoricalArrayType', 'CategoricalIndexType', 'DataFrameType',
    'DatetimeIndexType', 'Decimal128Type', 'DecimalArrayType',
    'IntegerArrayType', 'IntervalArrayType', 'IntervalIndexType', 'List',
    'MapArrayType', 'NumericIndexType', 'PDCategoricalDtype',
    'PeriodIndexType', 'RangeIndexType', 'SeriesType', 'StringIndexType',
    'BinaryIndexType', 'StructArrayType', 'TimedeltaIndexType',
    'TupleArrayType'}
container_update_method_names = ('clear', 'pop', 'popitem', 'update', 'add',
    'difference_update', 'discard', 'intersection_update', 'remove',
    'symmetric_difference_update', 'append', 'extend', 'insert', 'reverse',
    'sort')
no_side_effect_call_tuples = {(int,), (list,), (set,), (dict,), (min,), (
    max,), (abs,), (len,), (bool,), (str,), ('ceil', math), ('init_series',
    'pd_series_ext', 'hiframes', bodo), ('get_series_data', 'pd_series_ext',
    'hiframes', bodo), ('get_series_index', 'pd_series_ext', 'hiframes',
    bodo), ('get_series_name', 'pd_series_ext', 'hiframes', bodo), (
    'get_index_data', 'pd_index_ext', 'hiframes', bodo), ('get_index_name',
    'pd_index_ext', 'hiframes', bodo), ('init_binary_str_index',
    'pd_index_ext', 'hiframes', bodo), ('init_numeric_index',
    'pd_index_ext', 'hiframes', bodo), ('init_categorical_index',
    'pd_index_ext', 'hiframes', bodo), ('_dti_val_finalize', 'pd_index_ext',
    'hiframes', bodo), ('init_datetime_index', 'pd_index_ext', 'hiframes',
    bodo), ('init_timedelta_index', 'pd_index_ext', 'hiframes', bodo), (
    'init_range_index', 'pd_index_ext', 'hiframes', bodo), (
    'init_heter_index', 'pd_index_ext', 'hiframes', bodo), (
    'get_int_arr_data', 'int_arr_ext', 'libs', bodo), ('get_int_arr_bitmap',
    'int_arr_ext', 'libs', bodo), ('init_integer_array', 'int_arr_ext',
    'libs', bodo), ('alloc_int_array', 'int_arr_ext', 'libs', bodo), (
    'inplace_eq', 'str_arr_ext', 'libs', bodo), ('get_bool_arr_data',
    'bool_arr_ext', 'libs', bodo), ('get_bool_arr_bitmap', 'bool_arr_ext',
    'libs', bodo), ('init_bool_array', 'bool_arr_ext', 'libs', bodo), (
    'alloc_bool_array', 'bool_arr_ext', 'libs', bodo), (
    'datetime_date_arr_to_dt64_arr', 'pd_timestamp_ext', 'hiframes', bodo),
    (bodo.libs.bool_arr_ext.compute_or_body,), (bodo.libs.bool_arr_ext.
    compute_and_body,), ('alloc_datetime_date_array', 'datetime_date_ext',
    'hiframes', bodo), ('alloc_datetime_timedelta_array',
    'datetime_timedelta_ext', 'hiframes', bodo), ('cat_replace',
    'pd_categorical_ext', 'hiframes', bodo), ('init_categorical_array',
    'pd_categorical_ext', 'hiframes', bodo), ('alloc_categorical_array',
    'pd_categorical_ext', 'hiframes', bodo), ('get_categorical_arr_codes',
    'pd_categorical_ext', 'hiframes', bodo), ('_sum_handle_nan',
    'series_kernels', 'hiframes', bodo), ('_box_cat_val', 'series_kernels',
    'hiframes', bodo), ('_mean_handle_nan', 'series_kernels', 'hiframes',
    bodo), ('_var_handle_mincount', 'series_kernels', 'hiframes', bodo), (
    '_compute_var_nan_count_ddof', 'series_kernels', 'hiframes', bodo), (
    '_sem_handle_nan', 'series_kernels', 'hiframes', bodo), ('dist_return',
    'distributed_api', 'libs', bodo), ('rep_return', 'distributed_api',
    'libs', bodo), ('init_dataframe', 'pd_dataframe_ext', 'hiframes', bodo),
    ('get_dataframe_data', 'pd_dataframe_ext', 'hiframes', bodo), (
    'get_dataframe_table', 'pd_dataframe_ext', 'hiframes', bodo), (
    'get_dataframe_column_names', 'pd_dataframe_ext', 'hiframes', bodo), (
    'get_table_data', 'table', 'hiframes', bodo), ('get_dataframe_index',
    'pd_dataframe_ext', 'hiframes', bodo), ('init_rolling',
    'pd_rolling_ext', 'hiframes', bodo), ('init_groupby', 'pd_groupby_ext',
    'hiframes', bodo), ('calc_nitems', 'array_kernels', 'libs', bodo), (
    'concat', 'array_kernels', 'libs', bodo), ('unique', 'array_kernels',
    'libs', bodo), ('nunique', 'array_kernels', 'libs', bodo), ('quantile',
    'array_kernels', 'libs', bodo), ('explode', 'array_kernels', 'libs',
    bodo), ('explode_no_index', 'array_kernels', 'libs', bodo), (
    'get_arr_lens', 'array_kernels', 'libs', bodo), (
    'str_arr_from_sequence', 'str_arr_ext', 'libs', bodo), (
    'get_str_arr_str_length', 'str_arr_ext', 'libs', bodo), (
    'parse_datetime_str', 'pd_timestamp_ext', 'hiframes', bodo), (
    'integer_to_dt64', 'pd_timestamp_ext', 'hiframes', bodo), (
    'dt64_to_integer', 'pd_timestamp_ext', 'hiframes', bodo), (
    'timedelta64_to_integer', 'pd_timestamp_ext', 'hiframes', bodo), (
    'integer_to_timedelta64', 'pd_timestamp_ext', 'hiframes', bodo), (
    'npy_datetimestruct_to_datetime', 'pd_timestamp_ext', 'hiframes', bodo),
    ('isna', 'array_kernels', 'libs', bodo), ('copy',), (
    'from_iterable_impl', 'typing', 'utils', bodo), ('chain', itertools), (
    'groupby',), ('rolling',), (pd.CategoricalDtype,), (bodo.hiframes.
    pd_categorical_ext.get_code_for_value,), ('asarray', np), ('int32', np),
    ('int64', np), ('float64', np), ('float32', np), ('bool_', np), ('full',
    np), ('round', np), ('isnan', np), ('isnat', np), ('internal_prange',
    'parfor', numba), ('internal_prange', 'parfor', 'parfors', numba), (
    'empty_inferred', 'ndarray', 'unsafe', numba), ('_slice_span',
    'unicode', numba), ('_normalize_slice', 'unicode', numba), (
    'init_session_builder', 'pyspark_ext', 'libs', bodo), ('init_session',
    'pyspark_ext', 'libs', bodo), ('init_spark_df', 'pyspark_ext', 'libs',
    bodo), ('h5size', 'h5_api', 'io', bodo), ('pre_alloc_struct_array',
    'struct_arr_ext', 'libs', bodo), (bodo.libs.struct_arr_ext.
    pre_alloc_struct_array,), ('pre_alloc_tuple_array', 'tuple_arr_ext',
    'libs', bodo), (bodo.libs.tuple_arr_ext.pre_alloc_tuple_array,), (
    'pre_alloc_array_item_array', 'array_item_arr_ext', 'libs', bodo), (
    bodo.libs.array_item_arr_ext.pre_alloc_array_item_array,), (
    'dist_reduce', 'distributed_api', 'libs', bodo), (bodo.libs.
    distributed_api.dist_reduce,), ('pre_alloc_string_array', 'str_arr_ext',
    'libs', bodo), (bodo.libs.str_arr_ext.pre_alloc_string_array,), (
    'pre_alloc_binary_array', 'binary_arr_ext', 'libs', bodo), (bodo.libs.
    binary_arr_ext.pre_alloc_binary_array,), ('pre_alloc_map_array',
    'map_arr_ext', 'libs', bodo), (bodo.libs.map_arr_ext.
    pre_alloc_map_array,), ('convert_dict_arr_to_int', 'dict_arr_ext',
    'libs', bodo), ('cat_dict_str', 'dict_arr_ext', 'libs', bodo), (
    'str_replace', 'dict_arr_ext', 'libs', bodo), ('dict_arr_eq',
    'dict_arr_ext', 'libs', bodo), ('dict_arr_ne', 'dict_arr_ext', 'libs',
    bodo), ('prange', bodo), (bodo.prange,), ('objmode', bodo), (bodo.
    objmode,), ('get_label_dict_from_categories', 'pd_categorial_ext',
    'hiframes', bodo), ('get_label_dict_from_categories_no_duplicates',
    'pd_categorial_ext', 'hiframes', bodo), ('build_nullable_tuple',
    'nullable_tuple_ext', 'libs', bodo)}


def remove_hiframes(rhs, lives, call_list):
    vke__lzgrz = tuple(call_list)
    if vke__lzgrz in no_side_effect_call_tuples:
        return True
    if len(call_list) == 4 and call_list[1:] == ['conversion', 'utils', bodo]:
        return True
    if isinstance(call_list[-1], pytypes.ModuleType) and call_list[-1
        ].__name__ == 'bodosql':
        return True
    if len(call_list) == 2 and call_list[0] == 'copy':
        return True
    if call_list == ['h5read', 'h5_api', 'io', bodo] and rhs.args[5
        ].name not in lives:
        return True
    if call_list == ['move_str_binary_arr_payload', 'str_arr_ext', 'libs', bodo
        ] and rhs.args[0].name not in lives:
        return True
    if call_list == ['setna', 'array_kernels', 'libs', bodo] and rhs.args[0
        ].name not in lives:
        return True
    if call_list == ['set_table_data', 'table', 'hiframes', bodo] and rhs.args[
        0].name not in lives:
        return True
    if len(vke__lzgrz) == 1 and tuple in getattr(vke__lzgrz[0], '__mro__', ()):
        return True
    return False


numba.core.ir_utils.remove_call_handlers.append(remove_hiframes)


def compile_func_single_block(func, args, ret_var, typing_info=None,
    extra_globals=None, infer_types=True, run_untyped_pass=False, flags=
    None, replace_globals=True):
    rexpz__dau = {'numba': numba, 'np': np, 'bodo': bodo, 'pd': pd, 'math':
        math}
    if extra_globals is not None:
        rexpz__dau.update(extra_globals)
    if not replace_globals:
        rexpz__dau = func.__globals__
    loc = ir.Loc('', 0)
    if ret_var:
        loc = ret_var.loc
    if typing_info and infer_types:
        loc = typing_info.curr_loc
        f_ir = compile_to_numba_ir(func, rexpz__dau, typingctx=typing_info.
            typingctx, targetctx=typing_info.targetctx, arg_typs=tuple(
            typing_info.typemap[aya__qygjd.name] for aya__qygjd in args),
            typemap=typing_info.typemap, calltypes=typing_info.calltypes)
    else:
        f_ir = compile_to_numba_ir(func, rexpz__dau)
    assert len(f_ir.blocks
        ) == 1, 'only single block functions supported in compile_func_single_block()'
    if run_untyped_pass:
        ivbzg__yhpp = tuple(typing_info.typemap[aya__qygjd.name] for
            aya__qygjd in args)
        rboe__ylhej = bodo.transforms.untyped_pass.UntypedPass(f_ir,
            typing_info.typingctx, ivbzg__yhpp, {}, {}, flags)
        rboe__ylhej.run()
    ngppt__smp = f_ir.blocks.popitem()[1]
    replace_arg_nodes(ngppt__smp, args)
    hnqum__gxmt = ngppt__smp.body[:-2]
    update_locs(hnqum__gxmt[len(args):], loc)
    for stmt in hnqum__gxmt[:len(args)]:
        stmt.target.loc = loc
    if ret_var is not None:
        wmtpq__zszqy = ngppt__smp.body[-2]
        assert is_assign(wmtpq__zszqy) and is_expr(wmtpq__zszqy.value, 'cast')
        lhowu__dxme = wmtpq__zszqy.value.value
        hnqum__gxmt.append(ir.Assign(lhowu__dxme, ret_var, loc))
    return hnqum__gxmt


def update_locs(node_list, loc):
    for stmt in node_list:
        stmt.loc = loc
        for oxh__wwv in stmt.list_vars():
            oxh__wwv.loc = loc
        if is_assign(stmt):
            stmt.value.loc = loc


def get_stmt_defs(stmt):
    if is_assign(stmt):
        return set([stmt.target.name])
    if type(stmt) in numba.core.analysis.ir_extension_usedefs:
        iffii__hadci = numba.core.analysis.ir_extension_usedefs[type(stmt)]
        qhqd__uxacl, huz__odnva = iffii__hadci(stmt)
        return huz__odnva
    return set()


def get_const_value(var, func_ir, err_msg, typemap=None, arg_types=None,
    file_info=None):
    if hasattr(var, 'loc'):
        loc = var.loc
    else:
        loc = None
    try:
        gfmnr__jspni = get_const_value_inner(func_ir, var, arg_types,
            typemap, file_info=file_info)
        if isinstance(gfmnr__jspni, ir.UndefinedType):
            omdzk__hal = func_ir.get_definition(var.name).name
            raise BodoError(f"name '{omdzk__hal}' is not defined", loc=loc)
    except GuardException as rtog__onu:
        raise BodoError(err_msg, loc=loc)
    return gfmnr__jspni


def get_const_value_inner(func_ir, var, arg_types=None, typemap=None,
    updated_containers=None, file_info=None, pyobject_to_literal=False,
    literalize_args=True):
    require(isinstance(var, ir.Var))
    kxi__vgm = get_definition(func_ir, var)
    ghu__cywqu = None
    if typemap is not None:
        ghu__cywqu = typemap.get(var.name, None)
    if isinstance(kxi__vgm, ir.Arg) and arg_types is not None:
        ghu__cywqu = arg_types[kxi__vgm.index]
    if updated_containers and var.name in updated_containers:
        raise BodoConstUpdatedError(
            f"variable '{var.name}' is updated inplace using '{updated_containers[var.name]}'"
            )
    if is_literal_type(ghu__cywqu):
        return get_literal_value(ghu__cywqu)
    if isinstance(kxi__vgm, (ir.Const, ir.Global, ir.FreeVar)):
        gfmnr__jspni = kxi__vgm.value
        return gfmnr__jspni
    if literalize_args and isinstance(kxi__vgm, ir.Arg
        ) and can_literalize_type(ghu__cywqu, pyobject_to_literal):
        raise numba.core.errors.ForceLiteralArg({kxi__vgm.index}, loc=var.
            loc, file_infos={kxi__vgm.index: file_info} if file_info is not
            None else None)
    if is_expr(kxi__vgm, 'binop'):
        if file_info and kxi__vgm.fn == operator.add:
            try:
                vplkf__dsv = get_const_value_inner(func_ir, kxi__vgm.lhs,
                    arg_types, typemap, updated_containers, literalize_args
                    =False)
                file_info.set_concat(vplkf__dsv, True)
                iaz__vtmn = get_const_value_inner(func_ir, kxi__vgm.rhs,
                    arg_types, typemap, updated_containers, file_info)
                return kxi__vgm.fn(vplkf__dsv, iaz__vtmn)
            except (GuardException, BodoConstUpdatedError) as rtog__onu:
                pass
            try:
                iaz__vtmn = get_const_value_inner(func_ir, kxi__vgm.rhs,
                    arg_types, typemap, updated_containers, literalize_args
                    =False)
                file_info.set_concat(iaz__vtmn, False)
                vplkf__dsv = get_const_value_inner(func_ir, kxi__vgm.lhs,
                    arg_types, typemap, updated_containers, file_info)
                return kxi__vgm.fn(vplkf__dsv, iaz__vtmn)
            except (GuardException, BodoConstUpdatedError) as rtog__onu:
                pass
        vplkf__dsv = get_const_value_inner(func_ir, kxi__vgm.lhs, arg_types,
            typemap, updated_containers)
        iaz__vtmn = get_const_value_inner(func_ir, kxi__vgm.rhs, arg_types,
            typemap, updated_containers)
        return kxi__vgm.fn(vplkf__dsv, iaz__vtmn)
    if is_expr(kxi__vgm, 'unary'):
        gfmnr__jspni = get_const_value_inner(func_ir, kxi__vgm.value,
            arg_types, typemap, updated_containers)
        return kxi__vgm.fn(gfmnr__jspni)
    if is_expr(kxi__vgm, 'getattr') and typemap:
        kino__hdj = typemap.get(kxi__vgm.value.name, None)
        if isinstance(kino__hdj, bodo.hiframes.pd_dataframe_ext.DataFrameType
            ) and kxi__vgm.attr == 'columns':
            return pd.Index(kino__hdj.columns)
        if isinstance(kino__hdj, types.SliceType):
            jsvc__iftmj = get_definition(func_ir, kxi__vgm.value)
            require(is_call(jsvc__iftmj))
            ujsq__qpp = find_callname(func_ir, jsvc__iftmj)
            bmb__jdvsv = False
            if ujsq__qpp == ('_normalize_slice', 'numba.cpython.unicode'):
                require(kxi__vgm.attr in ('start', 'step'))
                jsvc__iftmj = get_definition(func_ir, jsvc__iftmj.args[0])
                bmb__jdvsv = True
            require(find_callname(func_ir, jsvc__iftmj) == ('slice',
                'builtins'))
            if len(jsvc__iftmj.args) == 1:
                if kxi__vgm.attr == 'start':
                    return 0
                if kxi__vgm.attr == 'step':
                    return 1
                require(kxi__vgm.attr == 'stop')
                return get_const_value_inner(func_ir, jsvc__iftmj.args[0],
                    arg_types, typemap, updated_containers)
            if kxi__vgm.attr == 'start':
                gfmnr__jspni = get_const_value_inner(func_ir, jsvc__iftmj.
                    args[0], arg_types, typemap, updated_containers)
                if gfmnr__jspni is None:
                    gfmnr__jspni = 0
                if bmb__jdvsv:
                    require(gfmnr__jspni == 0)
                return gfmnr__jspni
            if kxi__vgm.attr == 'stop':
                assert not bmb__jdvsv
                return get_const_value_inner(func_ir, jsvc__iftmj.args[1],
                    arg_types, typemap, updated_containers)
            require(kxi__vgm.attr == 'step')
            if len(jsvc__iftmj.args) == 2:
                return 1
            else:
                gfmnr__jspni = get_const_value_inner(func_ir, jsvc__iftmj.
                    args[2], arg_types, typemap, updated_containers)
                if gfmnr__jspni is None:
                    gfmnr__jspni = 1
                if bmb__jdvsv:
                    require(gfmnr__jspni == 1)
                return gfmnr__jspni
    if is_expr(kxi__vgm, 'getattr'):
        return getattr(get_const_value_inner(func_ir, kxi__vgm.value,
            arg_types, typemap, updated_containers), kxi__vgm.attr)
    if is_expr(kxi__vgm, 'getitem'):
        value = get_const_value_inner(func_ir, kxi__vgm.value, arg_types,
            typemap, updated_containers)
        index = get_const_value_inner(func_ir, kxi__vgm.index, arg_types,
            typemap, updated_containers)
        return value[index]
    ryap__yaeqj = guard(find_callname, func_ir, kxi__vgm, typemap)
    if ryap__yaeqj is not None and len(ryap__yaeqj) == 2 and ryap__yaeqj[0
        ] == 'keys' and isinstance(ryap__yaeqj[1], ir.Var):
        rdxt__jwb = kxi__vgm.func
        kxi__vgm = get_definition(func_ir, ryap__yaeqj[1])
        bezmb__znue = ryap__yaeqj[1].name
        if updated_containers and bezmb__znue in updated_containers:
            raise BodoConstUpdatedError(
                "variable '{}' is updated inplace using '{}'".format(
                bezmb__znue, updated_containers[bezmb__znue]))
        require(is_expr(kxi__vgm, 'build_map'))
        vals = [oxh__wwv[0] for oxh__wwv in kxi__vgm.items]
        tsb__rudvn = guard(get_definition, func_ir, rdxt__jwb)
        assert isinstance(tsb__rudvn, ir.Expr) and tsb__rudvn.attr == 'keys'
        tsb__rudvn.attr = 'copy'
        return [get_const_value_inner(func_ir, oxh__wwv, arg_types, typemap,
            updated_containers) for oxh__wwv in vals]
    if is_expr(kxi__vgm, 'build_map'):
        return {get_const_value_inner(func_ir, oxh__wwv[0], arg_types,
            typemap, updated_containers): get_const_value_inner(func_ir,
            oxh__wwv[1], arg_types, typemap, updated_containers) for
            oxh__wwv in kxi__vgm.items}
    if is_expr(kxi__vgm, 'build_tuple'):
        return tuple(get_const_value_inner(func_ir, oxh__wwv, arg_types,
            typemap, updated_containers) for oxh__wwv in kxi__vgm.items)
    if is_expr(kxi__vgm, 'build_list'):
        return [get_const_value_inner(func_ir, oxh__wwv, arg_types, typemap,
            updated_containers) for oxh__wwv in kxi__vgm.items]
    if is_expr(kxi__vgm, 'build_set'):
        return {get_const_value_inner(func_ir, oxh__wwv, arg_types, typemap,
            updated_containers) for oxh__wwv in kxi__vgm.items}
    if ryap__yaeqj == ('list', 'builtins'):
        values = get_const_value_inner(func_ir, kxi__vgm.args[0], arg_types,
            typemap, updated_containers)
        if isinstance(values, set):
            values = sorted(values)
        return list(values)
    if ryap__yaeqj == ('set', 'builtins'):
        return set(get_const_value_inner(func_ir, kxi__vgm.args[0],
            arg_types, typemap, updated_containers))
    if ryap__yaeqj == ('range', 'builtins') and len(kxi__vgm.args) == 1:
        return range(get_const_value_inner(func_ir, kxi__vgm.args[0],
            arg_types, typemap, updated_containers))
    if ryap__yaeqj == ('slice', 'builtins'):
        return slice(*tuple(get_const_value_inner(func_ir, oxh__wwv,
            arg_types, typemap, updated_containers) for oxh__wwv in
            kxi__vgm.args))
    if ryap__yaeqj == ('str', 'builtins'):
        return str(get_const_value_inner(func_ir, kxi__vgm.args[0],
            arg_types, typemap, updated_containers))
    if ryap__yaeqj == ('bool', 'builtins'):
        return bool(get_const_value_inner(func_ir, kxi__vgm.args[0],
            arg_types, typemap, updated_containers))
    if ryap__yaeqj == ('format', 'builtins'):
        aya__qygjd = get_const_value_inner(func_ir, kxi__vgm.args[0],
            arg_types, typemap, updated_containers)
        qwkuo__yit = get_const_value_inner(func_ir, kxi__vgm.args[1],
            arg_types, typemap, updated_containers) if len(kxi__vgm.args
            ) > 1 else ''
        return format(aya__qygjd, qwkuo__yit)
    if ryap__yaeqj in (('init_binary_str_index',
        'bodo.hiframes.pd_index_ext'), ('init_numeric_index',
        'bodo.hiframes.pd_index_ext'), ('init_categorical_index',
        'bodo.hiframes.pd_index_ext'), ('init_datetime_index',
        'bodo.hiframes.pd_index_ext'), ('init_timedelta_index',
        'bodo.hiframes.pd_index_ext'), ('init_heter_index',
        'bodo.hiframes.pd_index_ext')):
        return pd.Index(get_const_value_inner(func_ir, kxi__vgm.args[0],
            arg_types, typemap, updated_containers))
    if ryap__yaeqj == ('str_arr_from_sequence', 'bodo.libs.str_arr_ext'):
        return np.array(get_const_value_inner(func_ir, kxi__vgm.args[0],
            arg_types, typemap, updated_containers))
    if ryap__yaeqj == ('init_range_index', 'bodo.hiframes.pd_index_ext'):
        return pd.RangeIndex(get_const_value_inner(func_ir, kxi__vgm.args[0
            ], arg_types, typemap, updated_containers),
            get_const_value_inner(func_ir, kxi__vgm.args[1], arg_types,
            typemap, updated_containers), get_const_value_inner(func_ir,
            kxi__vgm.args[2], arg_types, typemap, updated_containers))
    if ryap__yaeqj == ('len', 'builtins') and typemap and isinstance(typemap
        .get(kxi__vgm.args[0].name, None), types.BaseTuple):
        return len(typemap[kxi__vgm.args[0].name])
    if ryap__yaeqj == ('len', 'builtins'):
        typn__huoo = guard(get_definition, func_ir, kxi__vgm.args[0])
        if isinstance(typn__huoo, ir.Expr) and typn__huoo.op in ('build_tuple',
            'build_list', 'build_set', 'build_map'):
            return len(typn__huoo.items)
        return len(get_const_value_inner(func_ir, kxi__vgm.args[0],
            arg_types, typemap, updated_containers))
    if ryap__yaeqj == ('CategoricalDtype', 'pandas'):
        kws = dict(kxi__vgm.kws)
        wexkh__rza = get_call_expr_arg('CategoricalDtype', kxi__vgm.args,
            kws, 0, 'categories', '')
        vah__qik = get_call_expr_arg('CategoricalDtype', kxi__vgm.args, kws,
            1, 'ordered', False)
        if vah__qik is not False:
            vah__qik = get_const_value_inner(func_ir, vah__qik, arg_types,
                typemap, updated_containers)
        if wexkh__rza == '':
            wexkh__rza = None
        else:
            wexkh__rza = get_const_value_inner(func_ir, wexkh__rza,
                arg_types, typemap, updated_containers)
        return pd.CategoricalDtype(wexkh__rza, vah__qik)
    if ryap__yaeqj == ('dtype', 'numpy'):
        return np.dtype(get_const_value_inner(func_ir, kxi__vgm.args[0],
            arg_types, typemap, updated_containers))
    if ryap__yaeqj is not None and len(ryap__yaeqj) == 2 and ryap__yaeqj[1
        ] == 'pandas' and ryap__yaeqj[0] in ('Int8Dtype', 'Int16Dtype',
        'Int32Dtype', 'Int64Dtype', 'UInt8Dtype', 'UInt16Dtype',
        'UInt32Dtype', 'UInt64Dtype'):
        return getattr(pd, ryap__yaeqj[0])()
    if ryap__yaeqj is not None and len(ryap__yaeqj) == 2 and isinstance(
        ryap__yaeqj[1], ir.Var):
        gfmnr__jspni = get_const_value_inner(func_ir, ryap__yaeqj[1],
            arg_types, typemap, updated_containers)
        args = [get_const_value_inner(func_ir, oxh__wwv, arg_types, typemap,
            updated_containers) for oxh__wwv in kxi__vgm.args]
        kws = {kjf__mcsmo[0]: get_const_value_inner(func_ir, kjf__mcsmo[1],
            arg_types, typemap, updated_containers) for kjf__mcsmo in
            kxi__vgm.kws}
        return getattr(gfmnr__jspni, ryap__yaeqj[0])(*args, **kws)
    if ryap__yaeqj is not None and len(ryap__yaeqj) == 2 and ryap__yaeqj[1
        ] == 'bodo' and ryap__yaeqj[0] in bodo_types_with_params:
        args = tuple(get_const_value_inner(func_ir, oxh__wwv, arg_types,
            typemap, updated_containers) for oxh__wwv in kxi__vgm.args)
        kwargs = {omdzk__hal: get_const_value_inner(func_ir, oxh__wwv,
            arg_types, typemap, updated_containers) for omdzk__hal,
            oxh__wwv in dict(kxi__vgm.kws).items()}
        return getattr(bodo, ryap__yaeqj[0])(*args, **kwargs)
    if is_call(kxi__vgm) and typemap and isinstance(typemap.get(kxi__vgm.
        func.name, None), types.Dispatcher):
        py_func = typemap[kxi__vgm.func.name].dispatcher.py_func
        require(kxi__vgm.vararg is None)
        args = tuple(get_const_value_inner(func_ir, oxh__wwv, arg_types,
            typemap, updated_containers) for oxh__wwv in kxi__vgm.args)
        kwargs = {omdzk__hal: get_const_value_inner(func_ir, oxh__wwv,
            arg_types, typemap, updated_containers) for omdzk__hal,
            oxh__wwv in dict(kxi__vgm.kws).items()}
        arg_types = tuple(bodo.typeof(oxh__wwv) for oxh__wwv in args)
        kw_types = {pvcmk__axnj: bodo.typeof(oxh__wwv) for pvcmk__axnj,
            oxh__wwv in kwargs.items()}
        require(_func_is_pure(py_func, arg_types, kw_types))
        return py_func(*args, **kwargs)
    raise GuardException('Constant value not found')


def _func_is_pure(py_func, arg_types, kw_types):
    from bodo.hiframes.pd_dataframe_ext import DataFrameType
    from bodo.hiframes.pd_series_ext import SeriesType
    from bodo.ir.csv_ext import CsvReader
    from bodo.ir.json_ext import JsonReader
    from bodo.ir.parquet_ext import ParquetReader
    from bodo.ir.sql_ext import SqlReader
    f_ir, typemap, kif__ujs, kif__ujs = bodo.compiler.get_func_type_info(
        py_func, arg_types, kw_types)
    for block in f_ir.blocks.values():
        for stmt in block.body:
            if isinstance(stmt, ir.Print):
                return False
            if isinstance(stmt, (CsvReader, JsonReader, ParquetReader,
                SqlReader)):
                return False
            if is_setitem(stmt) and isinstance(guard(get_definition, f_ir,
                stmt.target), ir.Arg):
                return False
            if is_assign(stmt):
                rhs = stmt.value
                if isinstance(rhs, ir.Yield):
                    return False
                if is_call(rhs):
                    fzg__dxv = guard(get_definition, f_ir, rhs.func)
                    if isinstance(fzg__dxv, ir.Const) and isinstance(fzg__dxv
                        .value, numba.core.dispatcher.ObjModeLiftedWith):
                        return False
                    lvyqi__rqpd = guard(find_callname, f_ir, rhs)
                    if lvyqi__rqpd is None:
                        return False
                    func_name, anh__xeq = lvyqi__rqpd
                    if anh__xeq == 'pandas' and func_name.startswith('read_'):
                        return False
                    if lvyqi__rqpd in (('fromfile', 'numpy'), ('file_read',
                        'bodo.io.np_io')):
                        return False
                    if lvyqi__rqpd == ('File', 'h5py'):
                        return False
                    if isinstance(anh__xeq, ir.Var):
                        ghu__cywqu = typemap[anh__xeq.name]
                        if isinstance(ghu__cywqu, (DataFrameType, SeriesType)
                            ) and func_name in ('to_csv', 'to_excel',
                            'to_json', 'to_sql', 'to_pickle', 'to_parquet',
                            'info'):
                            return False
                        if isinstance(ghu__cywqu, types.Array
                            ) and func_name == 'tofile':
                            return False
                        if isinstance(ghu__cywqu, bodo.LoggingLoggerType):
                            return False
                        if str(ghu__cywqu).startswith('Mpl'):
                            return False
                        if (func_name in container_update_method_names and
                            isinstance(guard(get_definition, f_ir, anh__xeq
                            ), ir.Arg)):
                            return False
                    if anh__xeq in ('numpy.random', 'time', 'logging',
                        'matplotlib.pyplot'):
                        return False
    return True


def fold_argument_types(pysig, args, kws):

    def normal_handler(index, param, value):
        return value

    def default_handler(index, param, default):
        return types.Omitted(default)

    def stararg_handler(index, param, values):
        return types.StarArgTuple(values)
    args = fold_arguments(pysig, args, kws, normal_handler, default_handler,
        stararg_handler)
    return args


def get_const_func_output_type(func, arg_types, kw_types, typing_context,
    target_context, is_udf=True):
    from bodo.hiframes.pd_series_ext import HeterogeneousSeriesType, SeriesType
    py_func = None
    if isinstance(func, types.MakeFunctionLiteral):
        mhyq__exj = func.literal_value.code
        xwwv__sirc = {'np': np, 'pd': pd, 'numba': numba, 'bodo': bodo}
        if hasattr(func.literal_value, 'globals'):
            xwwv__sirc = func.literal_value.globals
        f_ir = numba.core.ir_utils.get_ir_of_code(xwwv__sirc, mhyq__exj)
        fix_struct_return(f_ir)
        typemap, qdcpt__ozyv, ondg__jmvx, kif__ujs = (numba.core.
            typed_passes.type_inference_stage(typing_context,
            target_context, f_ir, arg_types, None))
    elif isinstance(func, bodo.utils.typing.FunctionLiteral):
        py_func = func.literal_value
        f_ir, typemap, ondg__jmvx, qdcpt__ozyv = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    elif isinstance(func, CPUDispatcher):
        py_func = func.py_func
        f_ir, typemap, ondg__jmvx, qdcpt__ozyv = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    else:
        if not isinstance(func, types.Dispatcher):
            if isinstance(func, types.Function):
                raise BodoError(
                    f'Bodo does not support built-in functions yet, {func}')
            else:
                raise BodoError(f'Function type expected, not {func}')
        py_func = func.dispatcher.py_func
        f_ir, typemap, ondg__jmvx, qdcpt__ozyv = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    if is_udf and isinstance(qdcpt__ozyv, types.DictType):
        oisj__yyqo = guard(get_struct_keynames, f_ir, typemap)
        if oisj__yyqo is not None:
            qdcpt__ozyv = StructType((qdcpt__ozyv.value_type,) * len(
                oisj__yyqo), oisj__yyqo)
    if is_udf and isinstance(qdcpt__ozyv, (SeriesType, HeterogeneousSeriesType)
        ):
        vke__kjhtt = numba.core.registry.cpu_target.typing_context
        uksuw__ndk = numba.core.registry.cpu_target.target_context
        cqvgp__thi = bodo.transforms.series_pass.SeriesPass(f_ir,
            vke__kjhtt, uksuw__ndk, typemap, ondg__jmvx, {})
        cqvgp__thi.run()
        cqvgp__thi.run()
        cqvgp__thi.run()
        cyv__ryfn = compute_cfg_from_blocks(f_ir.blocks)
        scw__pmusj = [guard(_get_const_series_info, f_ir.blocks[bfpn__qeroc
            ], f_ir, typemap) for bfpn__qeroc in cyv__ryfn.exit_points() if
            isinstance(f_ir.blocks[bfpn__qeroc].body[-1], ir.Return)]
        if None in scw__pmusj or len(pd.Series(scw__pmusj).unique()) != 1:
            qdcpt__ozyv.const_info = None
        else:
            qdcpt__ozyv.const_info = scw__pmusj[0]
    return qdcpt__ozyv


def _get_const_series_info(block, f_ir, typemap):
    from bodo.hiframes.pd_series_ext import HeterogeneousSeriesType
    assert isinstance(block.body[-1], ir.Return)
    twodb__yvmt = block.body[-1].value
    dttv__vvs = get_definition(f_ir, twodb__yvmt)
    require(is_expr(dttv__vvs, 'cast'))
    dttv__vvs = get_definition(f_ir, dttv__vvs.value)
    require(is_call(dttv__vvs) and find_callname(f_ir, dttv__vvs) == (
        'init_series', 'bodo.hiframes.pd_series_ext'))
    ddhe__yfbbo = dttv__vvs.args[1]
    nsx__hmxrw = tuple(get_const_value_inner(f_ir, ddhe__yfbbo, typemap=
        typemap))
    if isinstance(typemap[twodb__yvmt.name], HeterogeneousSeriesType):
        return len(typemap[twodb__yvmt.name].data), nsx__hmxrw
    xpeud__jqnf = dttv__vvs.args[0]
    qpf__vbz = get_definition(f_ir, xpeud__jqnf)
    func_name, ecce__dljrk = find_callname(f_ir, qpf__vbz)
    if is_call(qpf__vbz) and bodo.utils.utils.is_alloc_callname(func_name,
        ecce__dljrk):
        qklc__kpgll = qpf__vbz.args[0]
        qwjlc__pfv = get_const_value_inner(f_ir, qklc__kpgll, typemap=typemap)
        return qwjlc__pfv, nsx__hmxrw
    if is_call(qpf__vbz) and find_callname(f_ir, qpf__vbz) in [('asarray',
        'numpy'), ('str_arr_from_sequence', 'bodo.libs.str_arr_ext')]:
        xpeud__jqnf = qpf__vbz.args[0]
        qpf__vbz = get_definition(f_ir, xpeud__jqnf)
    require(is_expr(qpf__vbz, 'build_tuple') or is_expr(qpf__vbz, 'build_list')
        )
    return len(qpf__vbz.items), nsx__hmxrw


def extract_keyvals_from_struct_map(f_ir, build_map, loc, scope, typemap=None):
    azw__joj = []
    kqsz__mua = []
    values = []
    for pvcmk__axnj, oxh__wwv in build_map.items:
        nosje__nvwe = find_const(f_ir, pvcmk__axnj)
        require(isinstance(nosje__nvwe, str))
        kqsz__mua.append(nosje__nvwe)
        azw__joj.append(pvcmk__axnj)
        values.append(oxh__wwv)
    vyfwq__eaaa = ir.Var(scope, mk_unique_var('val_tup'), loc)
    xpeg__wxwkd = ir.Assign(ir.Expr.build_tuple(values, loc), vyfwq__eaaa, loc)
    f_ir._definitions[vyfwq__eaaa.name] = [xpeg__wxwkd.value]
    xayr__xzof = ir.Var(scope, mk_unique_var('key_tup'), loc)
    ugt__olkrl = ir.Assign(ir.Expr.build_tuple(azw__joj, loc), xayr__xzof, loc)
    f_ir._definitions[xayr__xzof.name] = [ugt__olkrl.value]
    if typemap is not None:
        typemap[vyfwq__eaaa.name] = types.Tuple([typemap[oxh__wwv.name] for
            oxh__wwv in values])
        typemap[xayr__xzof.name] = types.Tuple([typemap[oxh__wwv.name] for
            oxh__wwv in azw__joj])
    return kqsz__mua, vyfwq__eaaa, xpeg__wxwkd, xayr__xzof, ugt__olkrl


def _replace_const_map_return(f_ir, block, label):
    require(isinstance(block.body[-1], ir.Return))
    fqfu__louch = block.body[-1].value
    zocu__sxe = guard(get_definition, f_ir, fqfu__louch)
    require(is_expr(zocu__sxe, 'cast'))
    dttv__vvs = guard(get_definition, f_ir, zocu__sxe.value)
    require(is_expr(dttv__vvs, 'build_map'))
    require(len(dttv__vvs.items) > 0)
    loc = block.loc
    scope = block.scope
    kqsz__mua, vyfwq__eaaa, xpeg__wxwkd, xayr__xzof, ugt__olkrl = (
        extract_keyvals_from_struct_map(f_ir, dttv__vvs, loc, scope))
    ifuiw__agf = ir.Var(scope, mk_unique_var('conv_call'), loc)
    uqxu__huu = ir.Assign(ir.Global('struct_if_heter_dict', bodo.utils.
        conversion.struct_if_heter_dict, loc), ifuiw__agf, loc)
    f_ir._definitions[ifuiw__agf.name] = [uqxu__huu.value]
    aea__kws = ir.Var(scope, mk_unique_var('struct_val'), loc)
    tpb__dgmy = ir.Assign(ir.Expr.call(ifuiw__agf, [vyfwq__eaaa, xayr__xzof
        ], {}, loc), aea__kws, loc)
    f_ir._definitions[aea__kws.name] = [tpb__dgmy.value]
    zocu__sxe.value = aea__kws
    dttv__vvs.items = [(pvcmk__axnj, pvcmk__axnj) for pvcmk__axnj, kif__ujs in
        dttv__vvs.items]
    block.body = block.body[:-2] + [xpeg__wxwkd, ugt__olkrl, uqxu__huu,
        tpb__dgmy] + block.body[-2:]
    return tuple(kqsz__mua)


def get_struct_keynames(f_ir, typemap):
    cyv__ryfn = compute_cfg_from_blocks(f_ir.blocks)
    nuy__mbm = list(cyv__ryfn.exit_points())[0]
    block = f_ir.blocks[nuy__mbm]
    require(isinstance(block.body[-1], ir.Return))
    fqfu__louch = block.body[-1].value
    zocu__sxe = guard(get_definition, f_ir, fqfu__louch)
    require(is_expr(zocu__sxe, 'cast'))
    dttv__vvs = guard(get_definition, f_ir, zocu__sxe.value)
    require(is_call(dttv__vvs) and find_callname(f_ir, dttv__vvs) == (
        'struct_if_heter_dict', 'bodo.utils.conversion'))
    return get_overload_const_list(typemap[dttv__vvs.args[1].name])


def fix_struct_return(f_ir):
    xguet__ejsy = None
    cyv__ryfn = compute_cfg_from_blocks(f_ir.blocks)
    for nuy__mbm in cyv__ryfn.exit_points():
        xguet__ejsy = guard(_replace_const_map_return, f_ir, f_ir.blocks[
            nuy__mbm], nuy__mbm)
    return xguet__ejsy


def update_node_list_definitions(node_list, func_ir):
    loc = ir.Loc('', 0)
    zel__wzpyb = ir.Block(ir.Scope(None, loc), loc)
    zel__wzpyb.body = node_list
    build_definitions({(0): zel__wzpyb}, func_ir._definitions)
    return


NESTED_TUP_SENTINEL = '$BODO_NESTED_TUP'


def gen_const_val_str(c):
    if isinstance(c, tuple):
        return "'{}{}', ".format(NESTED_TUP_SENTINEL, len(c)) + ', '.join(
            gen_const_val_str(oxh__wwv) for oxh__wwv in c)
    if isinstance(c, str):
        return "'{}'".format(c)
    if isinstance(c, (pd.Timestamp, pd.Timedelta, float)):
        return "'{}'".format(c)
    return str(c)


def gen_const_tup(vals):
    ivral__omfk = ', '.join(gen_const_val_str(c) for c in vals)
    return '({}{})'.format(ivral__omfk, ',' if len(vals) == 1 else '')


def get_const_tup_vals(c_typ):
    vals = get_overload_const_list(c_typ)
    return _get_original_nested_tups(vals)


def _get_original_nested_tups(vals):
    for zlvc__nkjd in range(len(vals) - 1, -1, -1):
        oxh__wwv = vals[zlvc__nkjd]
        if isinstance(oxh__wwv, str) and oxh__wwv.startswith(
            NESTED_TUP_SENTINEL):
            uaj__wsl = int(oxh__wwv[len(NESTED_TUP_SENTINEL):])
            return _get_original_nested_tups(tuple(vals[:zlvc__nkjd]) + (
                tuple(vals[zlvc__nkjd + 1:zlvc__nkjd + uaj__wsl + 1]),) +
                tuple(vals[zlvc__nkjd + uaj__wsl + 1:]))
    return tuple(vals)


def get_call_expr_arg(f_name, args, kws, arg_no, arg_name, default=None,
    err_msg=None, use_default=False):
    aya__qygjd = None
    if len(args) > arg_no and arg_no >= 0:
        aya__qygjd = args[arg_no]
        if arg_name in kws:
            err_msg = (
                f"{f_name}() got multiple values for argument '{arg_name}'")
            raise BodoError(err_msg)
    elif arg_name in kws:
        aya__qygjd = kws[arg_name]
    if aya__qygjd is None:
        if use_default or default is not None:
            return default
        if err_msg is None:
            err_msg = "{} requires '{}' argument".format(f_name, arg_name)
        raise BodoError(err_msg)
    return aya__qygjd


def set_call_expr_arg(var, args, kws, arg_no, arg_name, add_if_missing=False):
    if len(args) > arg_no:
        args[arg_no] = var
    elif add_if_missing or arg_name in kws:
        kws[arg_name] = var
    else:
        raise BodoError('cannot set call argument since does not exist')


def avoid_udf_inline(py_func, arg_types, kw_types):
    from bodo.hiframes.pd_dataframe_ext import DataFrameType
    f_ir = numba.core.compiler.run_frontend(py_func, inline_closures=True)
    if '_bodo_inline' in kw_types and is_overload_constant_bool(kw_types[
        '_bodo_inline']):
        return not get_overload_const_bool(kw_types['_bodo_inline'])
    if any(isinstance(t, DataFrameType) for t in arg_types + tuple(kw_types
        .values())):
        return True
    for block in f_ir.blocks.values():
        if isinstance(block.body[-1], (ir.Raise, ir.StaticRaise)):
            return True
        for stmt in block.body:
            if isinstance(stmt, ir.EnterWith):
                return True
    return False


def replace_func(pass_info, func, args, const=False, pre_nodes=None,
    extra_globals=None, pysig=None, kws=None, inline_bodo_calls=False,
    run_full_pipeline=False):
    rexpz__dau = {'numba': numba, 'np': np, 'bodo': bodo, 'pd': pd}
    if extra_globals is not None:
        rexpz__dau.update(extra_globals)
    func.__globals__.update(rexpz__dau)
    if pysig is not None:
        pre_nodes = [] if pre_nodes is None else pre_nodes
        scope = next(iter(pass_info.func_ir.blocks.values())).scope
        loc = scope.loc

        def normal_handler(index, param, default):
            return default

        def default_handler(index, param, default):
            xyhb__sxrf = ir.Var(scope, mk_unique_var('defaults'), loc)
            try:
                pass_info.typemap[xyhb__sxrf.name] = types.literal(default)
            except:
                pass_info.typemap[xyhb__sxrf.name] = numba.typeof(default)
            czyh__fmv = ir.Assign(ir.Const(default, loc), xyhb__sxrf, loc)
            pre_nodes.append(czyh__fmv)
            return xyhb__sxrf
        args = numba.core.typing.fold_arguments(pysig, args, kws,
            normal_handler, default_handler, normal_handler)
    ivbzg__yhpp = tuple(pass_info.typemap[oxh__wwv.name] for oxh__wwv in args)
    if const:
        ncrhf__zza = []
        for zlvc__nkjd, aya__qygjd in enumerate(args):
            gfmnr__jspni = guard(find_const, pass_info.func_ir, aya__qygjd)
            if gfmnr__jspni:
                ncrhf__zza.append(types.literal(gfmnr__jspni))
            else:
                ncrhf__zza.append(ivbzg__yhpp[zlvc__nkjd])
        ivbzg__yhpp = tuple(ncrhf__zza)
    return ReplaceFunc(func, ivbzg__yhpp, args, rexpz__dau,
        inline_bodo_calls, run_full_pipeline, pre_nodes)


def is_var_size_item_array_type(t):
    assert is_array_typ(t, False)
    return t == string_array_type or isinstance(t, ArrayItemArrayType
        ) or isinstance(t, StructArrayType) and any(
        is_var_size_item_array_type(icvz__ptmls) for icvz__ptmls in t.data)


def gen_init_varsize_alloc_sizes(t):
    if t == string_array_type:
        omfhd__tyi = 'num_chars_{}'.format(ir_utils.next_label())
        return f'  {omfhd__tyi} = 0\n', (omfhd__tyi,)
    if isinstance(t, ArrayItemArrayType):
        gutgn__imxo, gbih__hrgm = gen_init_varsize_alloc_sizes(t.dtype)
        omfhd__tyi = 'num_items_{}'.format(ir_utils.next_label())
        return f'  {omfhd__tyi} = 0\n' + gutgn__imxo, (omfhd__tyi,
            ) + gbih__hrgm
    return '', ()


def gen_varsize_item_sizes(t, item, var_names):
    if t == string_array_type:
        return '    {} += bodo.libs.str_arr_ext.get_utf8_size({})\n'.format(
            var_names[0], item)
    if isinstance(t, ArrayItemArrayType):
        return '    {} += len({})\n'.format(var_names[0], item
            ) + gen_varsize_array_counts(t.dtype, item, var_names[1:])
    return ''


def gen_varsize_array_counts(t, item, var_names):
    if t == string_array_type:
        return ('    {} += bodo.libs.str_arr_ext.get_num_total_chars({})\n'
            .format(var_names[0], item))
    return ''


def get_type_alloc_counts(t):
    if isinstance(t, (StructArrayType, TupleArrayType)):
        return 1 + sum(get_type_alloc_counts(icvz__ptmls.dtype) for
            icvz__ptmls in t.data)
    if isinstance(t, ArrayItemArrayType) or t == string_array_type:
        return 1 + get_type_alloc_counts(t.dtype)
    if isinstance(t, MapArrayType):
        return get_type_alloc_counts(t.key_arr_type) + get_type_alloc_counts(t
            .value_arr_type)
    if bodo.utils.utils.is_array_typ(t, False) or t == bodo.string_type:
        return 1
    if isinstance(t, StructType):
        return sum(get_type_alloc_counts(icvz__ptmls) for icvz__ptmls in t.data
            )
    if isinstance(t, types.BaseTuple):
        return sum(get_type_alloc_counts(icvz__ptmls) for icvz__ptmls in t.
            types)
    return 0


def find_udf_str_name(obj_dtype, func_name, typing_context, caller_name):
    msm__wka = typing_context.resolve_getattr(obj_dtype, func_name)
    if msm__wka is None:
        mxfl__xog = types.misc.Module(np)
        try:
            msm__wka = typing_context.resolve_getattr(mxfl__xog, func_name)
        except AttributeError as rtog__onu:
            msm__wka = None
        if msm__wka is None:
            raise BodoError(
                f"{caller_name}(): No Pandas method or Numpy function found with the name '{func_name}'."
                )
    return msm__wka


def get_udf_str_return_type(obj_dtype, func_name, typing_context,
    caller_name, axis=None):
    msm__wka = find_udf_str_name(obj_dtype, func_name, typing_context,
        caller_name)
    if isinstance(msm__wka, types.BoundFunction):
        if axis is not None:
            jjw__piyi = msm__wka.get_call_type(typing_context, (), {'axis':
                axis})
        else:
            jjw__piyi = msm__wka.get_call_type(typing_context, (), {})
        return jjw__piyi.return_type
    else:
        if bodo.utils.typing.is_numpy_ufunc(msm__wka):
            jjw__piyi = msm__wka.get_call_type(typing_context, (obj_dtype,), {}
                )
            return jjw__piyi.return_type
        raise BodoError(
            f"{caller_name}(): Only Pandas methods and np.ufunc are supported as string literals. '{func_name}' not supported."
            )


def get_pandas_method_str_impl(obj_dtype, func_name, typing_context,
    caller_name, axis=None):
    msm__wka = find_udf_str_name(obj_dtype, func_name, typing_context,
        caller_name)
    if isinstance(msm__wka, types.BoundFunction):
        anb__bvo = msm__wka.template
        if axis is not None:
            return anb__bvo._overload_func(obj_dtype, axis=axis)
        else:
            return anb__bvo._overload_func(obj_dtype)
    return None


def dict_to_const_keys_var_values_lists(dict_var, func_ir, arg_types,
    typemap, updated_containers, require_const_map, label):
    require(isinstance(dict_var, ir.Var))
    nhlo__jznjf = get_definition(func_ir, dict_var)
    require(isinstance(nhlo__jznjf, ir.Expr))
    require(nhlo__jznjf.op == 'build_map')
    bgvnm__rsjm = nhlo__jznjf.items
    azw__joj = []
    values = []
    egmo__uhsn = False
    for zlvc__nkjd in range(len(bgvnm__rsjm)):
        ztus__ymlu, value = bgvnm__rsjm[zlvc__nkjd]
        try:
            mlkn__ubtvl = get_const_value_inner(func_ir, ztus__ymlu,
                arg_types, typemap, updated_containers)
            azw__joj.append(mlkn__ubtvl)
            values.append(value)
        except GuardException as rtog__onu:
            require_const_map[ztus__ymlu] = label
            egmo__uhsn = True
    if egmo__uhsn:
        raise GuardException
    return azw__joj, values


def _get_const_keys_from_dict(args, func_ir, build_map, err_msg, loc):
    try:
        azw__joj = tuple(get_const_value_inner(func_ir, t[0], args) for t in
            build_map.items)
    except GuardException as rtog__onu:
        raise BodoError(err_msg, loc)
    if not all(isinstance(c, (str, int)) for c in azw__joj):
        raise BodoError(err_msg, loc)
    return azw__joj


def _convert_const_key_dict(args, func_ir, build_map, err_msg, scope, loc,
    output_sentinel_tuple=False):
    azw__joj = _get_const_keys_from_dict(args, func_ir, build_map, err_msg, loc
        )
    kvxpb__fvz = []
    otxo__glu = [bodo.transforms.typing_pass._create_const_var(pvcmk__axnj,
        'dict_key', scope, loc, kvxpb__fvz) for pvcmk__axnj in azw__joj]
    zky__lplx = [t[1] for t in build_map.items]
    if output_sentinel_tuple:
        mtzsm__fycsk = ir.Var(scope, mk_unique_var('sentinel'), loc)
        qgbql__ryqhd = ir.Var(scope, mk_unique_var('dict_tup'), loc)
        kvxpb__fvz.append(ir.Assign(ir.Const('__bodo_tup', loc),
            mtzsm__fycsk, loc))
        burr__vomaz = [mtzsm__fycsk] + otxo__glu + zky__lplx
        kvxpb__fvz.append(ir.Assign(ir.Expr.build_tuple(burr__vomaz, loc),
            qgbql__ryqhd, loc))
        return (qgbql__ryqhd,), kvxpb__fvz
    else:
        qikjq__ujwhg = ir.Var(scope, mk_unique_var('values_tup'), loc)
        fmfwt__yad = ir.Var(scope, mk_unique_var('idx_tup'), loc)
        kvxpb__fvz.append(ir.Assign(ir.Expr.build_tuple(zky__lplx, loc),
            qikjq__ujwhg, loc))
        kvxpb__fvz.append(ir.Assign(ir.Expr.build_tuple(otxo__glu, loc),
            fmfwt__yad, loc))
        return (qikjq__ujwhg, fmfwt__yad), kvxpb__fvz
