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
    lqxln__shrjg = tuple(call_list)
    if lqxln__shrjg in no_side_effect_call_tuples:
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
    if len(lqxln__shrjg) == 1 and tuple in getattr(lqxln__shrjg[0],
        '__mro__', ()):
        return True
    return False


numba.core.ir_utils.remove_call_handlers.append(remove_hiframes)


def compile_func_single_block(func, args, ret_var, typing_info=None,
    extra_globals=None, infer_types=True, run_untyped_pass=False, flags=
    None, replace_globals=True):
    zmk__pqre = {'numba': numba, 'np': np, 'bodo': bodo, 'pd': pd, 'math': math
        }
    if extra_globals is not None:
        zmk__pqre.update(extra_globals)
    if not replace_globals:
        zmk__pqre = func.__globals__
    loc = ir.Loc('', 0)
    if ret_var:
        loc = ret_var.loc
    if typing_info and infer_types:
        loc = typing_info.curr_loc
        f_ir = compile_to_numba_ir(func, zmk__pqre, typingctx=typing_info.
            typingctx, targetctx=typing_info.targetctx, arg_typs=tuple(
            typing_info.typemap[ovz__gck.name] for ovz__gck in args),
            typemap=typing_info.typemap, calltypes=typing_info.calltypes)
    else:
        f_ir = compile_to_numba_ir(func, zmk__pqre)
    assert len(f_ir.blocks
        ) == 1, 'only single block functions supported in compile_func_single_block()'
    if run_untyped_pass:
        gljh__vih = tuple(typing_info.typemap[ovz__gck.name] for ovz__gck in
            args)
        skzcx__izl = bodo.transforms.untyped_pass.UntypedPass(f_ir,
            typing_info.typingctx, gljh__vih, {}, {}, flags)
        skzcx__izl.run()
    sicz__vaca = f_ir.blocks.popitem()[1]
    replace_arg_nodes(sicz__vaca, args)
    tzvmz__psk = sicz__vaca.body[:-2]
    update_locs(tzvmz__psk[len(args):], loc)
    for stmt in tzvmz__psk[:len(args)]:
        stmt.target.loc = loc
    if ret_var is not None:
        xwlh__nyne = sicz__vaca.body[-2]
        assert is_assign(xwlh__nyne) and is_expr(xwlh__nyne.value, 'cast')
        fjiaz__rxrui = xwlh__nyne.value.value
        tzvmz__psk.append(ir.Assign(fjiaz__rxrui, ret_var, loc))
    return tzvmz__psk


def update_locs(node_list, loc):
    for stmt in node_list:
        stmt.loc = loc
        for rpigf__ntt in stmt.list_vars():
            rpigf__ntt.loc = loc
        if is_assign(stmt):
            stmt.value.loc = loc


def get_stmt_defs(stmt):
    if is_assign(stmt):
        return set([stmt.target.name])
    if type(stmt) in numba.core.analysis.ir_extension_usedefs:
        nppr__henb = numba.core.analysis.ir_extension_usedefs[type(stmt)]
        agmtr__xwjo, hrvjz__txc = nppr__henb(stmt)
        return hrvjz__txc
    return set()


def get_const_value(var, func_ir, err_msg, typemap=None, arg_types=None,
    file_info=None):
    if hasattr(var, 'loc'):
        loc = var.loc
    else:
        loc = None
    try:
        vmw__sydrd = get_const_value_inner(func_ir, var, arg_types, typemap,
            file_info=file_info)
        if isinstance(vmw__sydrd, ir.UndefinedType):
            dvlel__vxcba = func_ir.get_definition(var.name).name
            raise BodoError(f"name '{dvlel__vxcba}' is not defined", loc=loc)
    except GuardException as fzeit__dlen:
        raise BodoError(err_msg, loc=loc)
    return vmw__sydrd


def get_const_value_inner(func_ir, var, arg_types=None, typemap=None,
    updated_containers=None, file_info=None, pyobject_to_literal=False,
    literalize_args=True):
    require(isinstance(var, ir.Var))
    uosz__oqyf = get_definition(func_ir, var)
    szwm__efe = None
    if typemap is not None:
        szwm__efe = typemap.get(var.name, None)
    if isinstance(uosz__oqyf, ir.Arg) and arg_types is not None:
        szwm__efe = arg_types[uosz__oqyf.index]
    if updated_containers and var.name in updated_containers:
        raise BodoConstUpdatedError(
            f"variable '{var.name}' is updated inplace using '{updated_containers[var.name]}'"
            )
    if is_literal_type(szwm__efe):
        return get_literal_value(szwm__efe)
    if isinstance(uosz__oqyf, (ir.Const, ir.Global, ir.FreeVar)):
        vmw__sydrd = uosz__oqyf.value
        return vmw__sydrd
    if literalize_args and isinstance(uosz__oqyf, ir.Arg
        ) and can_literalize_type(szwm__efe, pyobject_to_literal):
        raise numba.core.errors.ForceLiteralArg({uosz__oqyf.index}, loc=var
            .loc, file_infos={uosz__oqyf.index: file_info} if file_info is not
            None else None)
    if is_expr(uosz__oqyf, 'binop'):
        if file_info and uosz__oqyf.fn == operator.add:
            try:
                cbjz__gwft = get_const_value_inner(func_ir, uosz__oqyf.lhs,
                    arg_types, typemap, updated_containers, literalize_args
                    =False)
                file_info.set_concat(cbjz__gwft, True)
                bji__wwzax = get_const_value_inner(func_ir, uosz__oqyf.rhs,
                    arg_types, typemap, updated_containers, file_info)
                return uosz__oqyf.fn(cbjz__gwft, bji__wwzax)
            except (GuardException, BodoConstUpdatedError) as fzeit__dlen:
                pass
            try:
                bji__wwzax = get_const_value_inner(func_ir, uosz__oqyf.rhs,
                    arg_types, typemap, updated_containers, literalize_args
                    =False)
                file_info.set_concat(bji__wwzax, False)
                cbjz__gwft = get_const_value_inner(func_ir, uosz__oqyf.lhs,
                    arg_types, typemap, updated_containers, file_info)
                return uosz__oqyf.fn(cbjz__gwft, bji__wwzax)
            except (GuardException, BodoConstUpdatedError) as fzeit__dlen:
                pass
        cbjz__gwft = get_const_value_inner(func_ir, uosz__oqyf.lhs,
            arg_types, typemap, updated_containers)
        bji__wwzax = get_const_value_inner(func_ir, uosz__oqyf.rhs,
            arg_types, typemap, updated_containers)
        return uosz__oqyf.fn(cbjz__gwft, bji__wwzax)
    if is_expr(uosz__oqyf, 'unary'):
        vmw__sydrd = get_const_value_inner(func_ir, uosz__oqyf.value,
            arg_types, typemap, updated_containers)
        return uosz__oqyf.fn(vmw__sydrd)
    if is_expr(uosz__oqyf, 'getattr') and typemap:
        eoic__xag = typemap.get(uosz__oqyf.value.name, None)
        if isinstance(eoic__xag, bodo.hiframes.pd_dataframe_ext.DataFrameType
            ) and uosz__oqyf.attr == 'columns':
            return pd.Index(eoic__xag.columns)
        if isinstance(eoic__xag, types.SliceType):
            zveev__rpwh = get_definition(func_ir, uosz__oqyf.value)
            require(is_call(zveev__rpwh))
            pec__qmqlz = find_callname(func_ir, zveev__rpwh)
            vykb__zsz = False
            if pec__qmqlz == ('_normalize_slice', 'numba.cpython.unicode'):
                require(uosz__oqyf.attr in ('start', 'step'))
                zveev__rpwh = get_definition(func_ir, zveev__rpwh.args[0])
                vykb__zsz = True
            require(find_callname(func_ir, zveev__rpwh) == ('slice',
                'builtins'))
            if len(zveev__rpwh.args) == 1:
                if uosz__oqyf.attr == 'start':
                    return 0
                if uosz__oqyf.attr == 'step':
                    return 1
                require(uosz__oqyf.attr == 'stop')
                return get_const_value_inner(func_ir, zveev__rpwh.args[0],
                    arg_types, typemap, updated_containers)
            if uosz__oqyf.attr == 'start':
                vmw__sydrd = get_const_value_inner(func_ir, zveev__rpwh.
                    args[0], arg_types, typemap, updated_containers)
                if vmw__sydrd is None:
                    vmw__sydrd = 0
                if vykb__zsz:
                    require(vmw__sydrd == 0)
                return vmw__sydrd
            if uosz__oqyf.attr == 'stop':
                assert not vykb__zsz
                return get_const_value_inner(func_ir, zveev__rpwh.args[1],
                    arg_types, typemap, updated_containers)
            require(uosz__oqyf.attr == 'step')
            if len(zveev__rpwh.args) == 2:
                return 1
            else:
                vmw__sydrd = get_const_value_inner(func_ir, zveev__rpwh.
                    args[2], arg_types, typemap, updated_containers)
                if vmw__sydrd is None:
                    vmw__sydrd = 1
                if vykb__zsz:
                    require(vmw__sydrd == 1)
                return vmw__sydrd
    if is_expr(uosz__oqyf, 'getattr'):
        return getattr(get_const_value_inner(func_ir, uosz__oqyf.value,
            arg_types, typemap, updated_containers), uosz__oqyf.attr)
    if is_expr(uosz__oqyf, 'getitem'):
        value = get_const_value_inner(func_ir, uosz__oqyf.value, arg_types,
            typemap, updated_containers)
        index = get_const_value_inner(func_ir, uosz__oqyf.index, arg_types,
            typemap, updated_containers)
        return value[index]
    rklel__sbmke = guard(find_callname, func_ir, uosz__oqyf, typemap)
    if rklel__sbmke is not None and len(rklel__sbmke) == 2 and rklel__sbmke[0
        ] == 'keys' and isinstance(rklel__sbmke[1], ir.Var):
        cjsli__bzkwt = uosz__oqyf.func
        uosz__oqyf = get_definition(func_ir, rklel__sbmke[1])
        tead__unzj = rklel__sbmke[1].name
        if updated_containers and tead__unzj in updated_containers:
            raise BodoConstUpdatedError(
                "variable '{}' is updated inplace using '{}'".format(
                tead__unzj, updated_containers[tead__unzj]))
        require(is_expr(uosz__oqyf, 'build_map'))
        vals = [rpigf__ntt[0] for rpigf__ntt in uosz__oqyf.items]
        difmk__bnjg = guard(get_definition, func_ir, cjsli__bzkwt)
        assert isinstance(difmk__bnjg, ir.Expr) and difmk__bnjg.attr == 'keys'
        difmk__bnjg.attr = 'copy'
        return [get_const_value_inner(func_ir, rpigf__ntt, arg_types,
            typemap, updated_containers) for rpigf__ntt in vals]
    if is_expr(uosz__oqyf, 'build_map'):
        return {get_const_value_inner(func_ir, rpigf__ntt[0], arg_types,
            typemap, updated_containers): get_const_value_inner(func_ir,
            rpigf__ntt[1], arg_types, typemap, updated_containers) for
            rpigf__ntt in uosz__oqyf.items}
    if is_expr(uosz__oqyf, 'build_tuple'):
        return tuple(get_const_value_inner(func_ir, rpigf__ntt, arg_types,
            typemap, updated_containers) for rpigf__ntt in uosz__oqyf.items)
    if is_expr(uosz__oqyf, 'build_list'):
        return [get_const_value_inner(func_ir, rpigf__ntt, arg_types,
            typemap, updated_containers) for rpigf__ntt in uosz__oqyf.items]
    if is_expr(uosz__oqyf, 'build_set'):
        return {get_const_value_inner(func_ir, rpigf__ntt, arg_types,
            typemap, updated_containers) for rpigf__ntt in uosz__oqyf.items}
    if rklel__sbmke == ('list', 'builtins'):
        values = get_const_value_inner(func_ir, uosz__oqyf.args[0],
            arg_types, typemap, updated_containers)
        if isinstance(values, set):
            values = sorted(values)
        return list(values)
    if rklel__sbmke == ('set', 'builtins'):
        return set(get_const_value_inner(func_ir, uosz__oqyf.args[0],
            arg_types, typemap, updated_containers))
    if rklel__sbmke == ('range', 'builtins') and len(uosz__oqyf.args) == 1:
        return range(get_const_value_inner(func_ir, uosz__oqyf.args[0],
            arg_types, typemap, updated_containers))
    if rklel__sbmke == ('slice', 'builtins'):
        return slice(*tuple(get_const_value_inner(func_ir, rpigf__ntt,
            arg_types, typemap, updated_containers) for rpigf__ntt in
            uosz__oqyf.args))
    if rklel__sbmke == ('str', 'builtins'):
        return str(get_const_value_inner(func_ir, uosz__oqyf.args[0],
            arg_types, typemap, updated_containers))
    if rklel__sbmke == ('bool', 'builtins'):
        return bool(get_const_value_inner(func_ir, uosz__oqyf.args[0],
            arg_types, typemap, updated_containers))
    if rklel__sbmke == ('format', 'builtins'):
        ovz__gck = get_const_value_inner(func_ir, uosz__oqyf.args[0],
            arg_types, typemap, updated_containers)
        sdt__yfaf = get_const_value_inner(func_ir, uosz__oqyf.args[1],
            arg_types, typemap, updated_containers) if len(uosz__oqyf.args
            ) > 1 else ''
        return format(ovz__gck, sdt__yfaf)
    if rklel__sbmke in (('init_binary_str_index',
        'bodo.hiframes.pd_index_ext'), ('init_numeric_index',
        'bodo.hiframes.pd_index_ext'), ('init_categorical_index',
        'bodo.hiframes.pd_index_ext'), ('init_datetime_index',
        'bodo.hiframes.pd_index_ext'), ('init_timedelta_index',
        'bodo.hiframes.pd_index_ext'), ('init_heter_index',
        'bodo.hiframes.pd_index_ext')):
        return pd.Index(get_const_value_inner(func_ir, uosz__oqyf.args[0],
            arg_types, typemap, updated_containers))
    if rklel__sbmke == ('str_arr_from_sequence', 'bodo.libs.str_arr_ext'):
        return np.array(get_const_value_inner(func_ir, uosz__oqyf.args[0],
            arg_types, typemap, updated_containers))
    if rklel__sbmke == ('init_range_index', 'bodo.hiframes.pd_index_ext'):
        return pd.RangeIndex(get_const_value_inner(func_ir, uosz__oqyf.args
            [0], arg_types, typemap, updated_containers),
            get_const_value_inner(func_ir, uosz__oqyf.args[1], arg_types,
            typemap, updated_containers), get_const_value_inner(func_ir,
            uosz__oqyf.args[2], arg_types, typemap, updated_containers))
    if rklel__sbmke == ('len', 'builtins') and typemap and isinstance(typemap
        .get(uosz__oqyf.args[0].name, None), types.BaseTuple):
        return len(typemap[uosz__oqyf.args[0].name])
    if rklel__sbmke == ('len', 'builtins'):
        psqgp__xrb = guard(get_definition, func_ir, uosz__oqyf.args[0])
        if isinstance(psqgp__xrb, ir.Expr) and psqgp__xrb.op in ('build_tuple',
            'build_list', 'build_set', 'build_map'):
            return len(psqgp__xrb.items)
        return len(get_const_value_inner(func_ir, uosz__oqyf.args[0],
            arg_types, typemap, updated_containers))
    if rklel__sbmke == ('CategoricalDtype', 'pandas'):
        kws = dict(uosz__oqyf.kws)
        hfqj__ssolj = get_call_expr_arg('CategoricalDtype', uosz__oqyf.args,
            kws, 0, 'categories', '')
        tfgd__lzw = get_call_expr_arg('CategoricalDtype', uosz__oqyf.args,
            kws, 1, 'ordered', False)
        if tfgd__lzw is not False:
            tfgd__lzw = get_const_value_inner(func_ir, tfgd__lzw, arg_types,
                typemap, updated_containers)
        if hfqj__ssolj == '':
            hfqj__ssolj = None
        else:
            hfqj__ssolj = get_const_value_inner(func_ir, hfqj__ssolj,
                arg_types, typemap, updated_containers)
        return pd.CategoricalDtype(hfqj__ssolj, tfgd__lzw)
    if rklel__sbmke == ('dtype', 'numpy'):
        return np.dtype(get_const_value_inner(func_ir, uosz__oqyf.args[0],
            arg_types, typemap, updated_containers))
    if rklel__sbmke is not None and len(rklel__sbmke) == 2 and rklel__sbmke[1
        ] == 'pandas' and rklel__sbmke[0] in ('Int8Dtype', 'Int16Dtype',
        'Int32Dtype', 'Int64Dtype', 'UInt8Dtype', 'UInt16Dtype',
        'UInt32Dtype', 'UInt64Dtype'):
        return getattr(pd, rklel__sbmke[0])()
    if rklel__sbmke is not None and len(rklel__sbmke) == 2 and isinstance(
        rklel__sbmke[1], ir.Var):
        vmw__sydrd = get_const_value_inner(func_ir, rklel__sbmke[1],
            arg_types, typemap, updated_containers)
        args = [get_const_value_inner(func_ir, rpigf__ntt, arg_types,
            typemap, updated_containers) for rpigf__ntt in uosz__oqyf.args]
        kws = {idx__onk[0]: get_const_value_inner(func_ir, idx__onk[1],
            arg_types, typemap, updated_containers) for idx__onk in
            uosz__oqyf.kws}
        return getattr(vmw__sydrd, rklel__sbmke[0])(*args, **kws)
    if rklel__sbmke is not None and len(rklel__sbmke) == 2 and rklel__sbmke[1
        ] == 'bodo' and rklel__sbmke[0] in bodo_types_with_params:
        args = tuple(get_const_value_inner(func_ir, rpigf__ntt, arg_types,
            typemap, updated_containers) for rpigf__ntt in uosz__oqyf.args)
        kwargs = {dvlel__vxcba: get_const_value_inner(func_ir, rpigf__ntt,
            arg_types, typemap, updated_containers) for dvlel__vxcba,
            rpigf__ntt in dict(uosz__oqyf.kws).items()}
        return getattr(bodo, rklel__sbmke[0])(*args, **kwargs)
    if is_call(uosz__oqyf) and typemap and isinstance(typemap.get(
        uosz__oqyf.func.name, None), types.Dispatcher):
        py_func = typemap[uosz__oqyf.func.name].dispatcher.py_func
        require(uosz__oqyf.vararg is None)
        args = tuple(get_const_value_inner(func_ir, rpigf__ntt, arg_types,
            typemap, updated_containers) for rpigf__ntt in uosz__oqyf.args)
        kwargs = {dvlel__vxcba: get_const_value_inner(func_ir, rpigf__ntt,
            arg_types, typemap, updated_containers) for dvlel__vxcba,
            rpigf__ntt in dict(uosz__oqyf.kws).items()}
        arg_types = tuple(bodo.typeof(rpigf__ntt) for rpigf__ntt in args)
        kw_types = {cux__hbms: bodo.typeof(rpigf__ntt) for cux__hbms,
            rpigf__ntt in kwargs.items()}
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
    f_ir, typemap, vlgy__avp, vlgy__avp = bodo.compiler.get_func_type_info(
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
                    rouxh__uesj = guard(get_definition, f_ir, rhs.func)
                    if isinstance(rouxh__uesj, ir.Const) and isinstance(
                        rouxh__uesj.value, numba.core.dispatcher.
                        ObjModeLiftedWith):
                        return False
                    czqil__sepmv = guard(find_callname, f_ir, rhs)
                    if czqil__sepmv is None:
                        return False
                    func_name, udz__kku = czqil__sepmv
                    if udz__kku == 'pandas' and func_name.startswith('read_'):
                        return False
                    if czqil__sepmv in (('fromfile', 'numpy'), ('file_read',
                        'bodo.io.np_io')):
                        return False
                    if czqil__sepmv == ('File', 'h5py'):
                        return False
                    if isinstance(udz__kku, ir.Var):
                        szwm__efe = typemap[udz__kku.name]
                        if isinstance(szwm__efe, (DataFrameType, SeriesType)
                            ) and func_name in ('to_csv', 'to_excel',
                            'to_json', 'to_sql', 'to_pickle', 'to_parquet',
                            'info'):
                            return False
                        if isinstance(szwm__efe, types.Array
                            ) and func_name == 'tofile':
                            return False
                        if isinstance(szwm__efe, bodo.LoggingLoggerType):
                            return False
                        if str(szwm__efe).startswith('Mpl'):
                            return False
                        if (func_name in container_update_method_names and
                            isinstance(guard(get_definition, f_ir, udz__kku
                            ), ir.Arg)):
                            return False
                    if udz__kku in ('numpy.random', 'time', 'logging',
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
        uouta__baj = func.literal_value.code
        pdba__qvwhf = {'np': np, 'pd': pd, 'numba': numba, 'bodo': bodo}
        if hasattr(func.literal_value, 'globals'):
            pdba__qvwhf = func.literal_value.globals
        f_ir = numba.core.ir_utils.get_ir_of_code(pdba__qvwhf, uouta__baj)
        fix_struct_return(f_ir)
        typemap, xdcxs__vrvm, hbmuq__pqx, vlgy__avp = (numba.core.
            typed_passes.type_inference_stage(typing_context,
            target_context, f_ir, arg_types, None))
    elif isinstance(func, bodo.utils.typing.FunctionLiteral):
        py_func = func.literal_value
        f_ir, typemap, hbmuq__pqx, xdcxs__vrvm = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    elif isinstance(func, CPUDispatcher):
        py_func = func.py_func
        f_ir, typemap, hbmuq__pqx, xdcxs__vrvm = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    else:
        if not isinstance(func, types.Dispatcher):
            if isinstance(func, types.Function):
                raise BodoError(
                    f'Bodo does not support built-in functions yet, {func}')
            else:
                raise BodoError(f'Function type expected, not {func}')
        py_func = func.dispatcher.py_func
        f_ir, typemap, hbmuq__pqx, xdcxs__vrvm = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    if is_udf and isinstance(xdcxs__vrvm, types.DictType):
        fyg__ryk = guard(get_struct_keynames, f_ir, typemap)
        if fyg__ryk is not None:
            xdcxs__vrvm = StructType((xdcxs__vrvm.value_type,) * len(
                fyg__ryk), fyg__ryk)
    if is_udf and isinstance(xdcxs__vrvm, (SeriesType, HeterogeneousSeriesType)
        ):
        dwif__usg = numba.core.registry.cpu_target.typing_context
        ccfq__ktyva = numba.core.registry.cpu_target.target_context
        ocw__bvea = bodo.transforms.series_pass.SeriesPass(f_ir, dwif__usg,
            ccfq__ktyva, typemap, hbmuq__pqx, {})
        ocw__bvea.run()
        ocw__bvea.run()
        ocw__bvea.run()
        wejht__nby = compute_cfg_from_blocks(f_ir.blocks)
        zfyqj__kqnl = [guard(_get_const_series_info, f_ir.blocks[fdx__meb],
            f_ir, typemap) for fdx__meb in wejht__nby.exit_points() if
            isinstance(f_ir.blocks[fdx__meb].body[-1], ir.Return)]
        if None in zfyqj__kqnl or len(pd.Series(zfyqj__kqnl).unique()) != 1:
            xdcxs__vrvm.const_info = None
        else:
            xdcxs__vrvm.const_info = zfyqj__kqnl[0]
    return xdcxs__vrvm


def _get_const_series_info(block, f_ir, typemap):
    from bodo.hiframes.pd_series_ext import HeterogeneousSeriesType
    assert isinstance(block.body[-1], ir.Return)
    wju__btoi = block.body[-1].value
    gxb__apr = get_definition(f_ir, wju__btoi)
    require(is_expr(gxb__apr, 'cast'))
    gxb__apr = get_definition(f_ir, gxb__apr.value)
    require(is_call(gxb__apr) and find_callname(f_ir, gxb__apr) == (
        'init_series', 'bodo.hiframes.pd_series_ext'))
    udgm__jon = gxb__apr.args[1]
    jcpg__hhudj = tuple(get_const_value_inner(f_ir, udgm__jon, typemap=typemap)
        )
    if isinstance(typemap[wju__btoi.name], HeterogeneousSeriesType):
        return len(typemap[wju__btoi.name].data), jcpg__hhudj
    iwrm__hylb = gxb__apr.args[0]
    uhlog__cmiw = get_definition(f_ir, iwrm__hylb)
    func_name, wcn__zhc = find_callname(f_ir, uhlog__cmiw)
    if is_call(uhlog__cmiw) and bodo.utils.utils.is_alloc_callname(func_name,
        wcn__zhc):
        uarx__himl = uhlog__cmiw.args[0]
        kbmm__ofs = get_const_value_inner(f_ir, uarx__himl, typemap=typemap)
        return kbmm__ofs, jcpg__hhudj
    if is_call(uhlog__cmiw) and find_callname(f_ir, uhlog__cmiw) in [(
        'asarray', 'numpy'), ('str_arr_from_sequence', 'bodo.libs.str_arr_ext')
        ]:
        iwrm__hylb = uhlog__cmiw.args[0]
        uhlog__cmiw = get_definition(f_ir, iwrm__hylb)
    require(is_expr(uhlog__cmiw, 'build_tuple') or is_expr(uhlog__cmiw,
        'build_list'))
    return len(uhlog__cmiw.items), jcpg__hhudj


def extract_keyvals_from_struct_map(f_ir, build_map, loc, scope, typemap=None):
    wbv__spyq = []
    mal__knn = []
    values = []
    for cux__hbms, rpigf__ntt in build_map.items:
        atg__zhk = find_const(f_ir, cux__hbms)
        require(isinstance(atg__zhk, str))
        mal__knn.append(atg__zhk)
        wbv__spyq.append(cux__hbms)
        values.append(rpigf__ntt)
    ffoe__jhlbn = ir.Var(scope, mk_unique_var('val_tup'), loc)
    jus__cda = ir.Assign(ir.Expr.build_tuple(values, loc), ffoe__jhlbn, loc)
    f_ir._definitions[ffoe__jhlbn.name] = [jus__cda.value]
    qpu__lsb = ir.Var(scope, mk_unique_var('key_tup'), loc)
    jfnyy__xavq = ir.Assign(ir.Expr.build_tuple(wbv__spyq, loc), qpu__lsb, loc)
    f_ir._definitions[qpu__lsb.name] = [jfnyy__xavq.value]
    if typemap is not None:
        typemap[ffoe__jhlbn.name] = types.Tuple([typemap[rpigf__ntt.name] for
            rpigf__ntt in values])
        typemap[qpu__lsb.name] = types.Tuple([typemap[rpigf__ntt.name] for
            rpigf__ntt in wbv__spyq])
    return mal__knn, ffoe__jhlbn, jus__cda, qpu__lsb, jfnyy__xavq


def _replace_const_map_return(f_ir, block, label):
    require(isinstance(block.body[-1], ir.Return))
    cmoaa__inb = block.body[-1].value
    xnx__fjk = guard(get_definition, f_ir, cmoaa__inb)
    require(is_expr(xnx__fjk, 'cast'))
    gxb__apr = guard(get_definition, f_ir, xnx__fjk.value)
    require(is_expr(gxb__apr, 'build_map'))
    require(len(gxb__apr.items) > 0)
    loc = block.loc
    scope = block.scope
    mal__knn, ffoe__jhlbn, jus__cda, qpu__lsb, jfnyy__xavq = (
        extract_keyvals_from_struct_map(f_ir, gxb__apr, loc, scope))
    fgy__yscq = ir.Var(scope, mk_unique_var('conv_call'), loc)
    bxo__tlrhy = ir.Assign(ir.Global('struct_if_heter_dict', bodo.utils.
        conversion.struct_if_heter_dict, loc), fgy__yscq, loc)
    f_ir._definitions[fgy__yscq.name] = [bxo__tlrhy.value]
    ayueh__tuj = ir.Var(scope, mk_unique_var('struct_val'), loc)
    qvnp__tua = ir.Assign(ir.Expr.call(fgy__yscq, [ffoe__jhlbn, qpu__lsb],
        {}, loc), ayueh__tuj, loc)
    f_ir._definitions[ayueh__tuj.name] = [qvnp__tua.value]
    xnx__fjk.value = ayueh__tuj
    gxb__apr.items = [(cux__hbms, cux__hbms) for cux__hbms, vlgy__avp in
        gxb__apr.items]
    block.body = block.body[:-2] + [jus__cda, jfnyy__xavq, bxo__tlrhy,
        qvnp__tua] + block.body[-2:]
    return tuple(mal__knn)


def get_struct_keynames(f_ir, typemap):
    wejht__nby = compute_cfg_from_blocks(f_ir.blocks)
    etsw__rzsd = list(wejht__nby.exit_points())[0]
    block = f_ir.blocks[etsw__rzsd]
    require(isinstance(block.body[-1], ir.Return))
    cmoaa__inb = block.body[-1].value
    xnx__fjk = guard(get_definition, f_ir, cmoaa__inb)
    require(is_expr(xnx__fjk, 'cast'))
    gxb__apr = guard(get_definition, f_ir, xnx__fjk.value)
    require(is_call(gxb__apr) and find_callname(f_ir, gxb__apr) == (
        'struct_if_heter_dict', 'bodo.utils.conversion'))
    return get_overload_const_list(typemap[gxb__apr.args[1].name])


def fix_struct_return(f_ir):
    otyma__qndg = None
    wejht__nby = compute_cfg_from_blocks(f_ir.blocks)
    for etsw__rzsd in wejht__nby.exit_points():
        otyma__qndg = guard(_replace_const_map_return, f_ir, f_ir.blocks[
            etsw__rzsd], etsw__rzsd)
    return otyma__qndg


def update_node_list_definitions(node_list, func_ir):
    loc = ir.Loc('', 0)
    tten__jbin = ir.Block(ir.Scope(None, loc), loc)
    tten__jbin.body = node_list
    build_definitions({(0): tten__jbin}, func_ir._definitions)
    return


NESTED_TUP_SENTINEL = '$BODO_NESTED_TUP'


def gen_const_val_str(c):
    if isinstance(c, tuple):
        return "'{}{}', ".format(NESTED_TUP_SENTINEL, len(c)) + ', '.join(
            gen_const_val_str(rpigf__ntt) for rpigf__ntt in c)
    if isinstance(c, str):
        return "'{}'".format(c)
    if isinstance(c, (pd.Timestamp, pd.Timedelta, float)):
        return "'{}'".format(c)
    return str(c)


def gen_const_tup(vals):
    iwg__gvsst = ', '.join(gen_const_val_str(c) for c in vals)
    return '({}{})'.format(iwg__gvsst, ',' if len(vals) == 1 else '')


def get_const_tup_vals(c_typ):
    vals = get_overload_const_list(c_typ)
    return _get_original_nested_tups(vals)


def _get_original_nested_tups(vals):
    for uaqan__wjvc in range(len(vals) - 1, -1, -1):
        rpigf__ntt = vals[uaqan__wjvc]
        if isinstance(rpigf__ntt, str) and rpigf__ntt.startswith(
            NESTED_TUP_SENTINEL):
            jpzw__oytn = int(rpigf__ntt[len(NESTED_TUP_SENTINEL):])
            return _get_original_nested_tups(tuple(vals[:uaqan__wjvc]) + (
                tuple(vals[uaqan__wjvc + 1:uaqan__wjvc + jpzw__oytn + 1]),) +
                tuple(vals[uaqan__wjvc + jpzw__oytn + 1:]))
    return tuple(vals)


def get_call_expr_arg(f_name, args, kws, arg_no, arg_name, default=None,
    err_msg=None, use_default=False):
    ovz__gck = None
    if len(args) > arg_no and arg_no >= 0:
        ovz__gck = args[arg_no]
        if arg_name in kws:
            err_msg = (
                f"{f_name}() got multiple values for argument '{arg_name}'")
            raise BodoError(err_msg)
    elif arg_name in kws:
        ovz__gck = kws[arg_name]
    if ovz__gck is None:
        if use_default or default is not None:
            return default
        if err_msg is None:
            err_msg = "{} requires '{}' argument".format(f_name, arg_name)
        raise BodoError(err_msg)
    return ovz__gck


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
    zmk__pqre = {'numba': numba, 'np': np, 'bodo': bodo, 'pd': pd}
    if extra_globals is not None:
        zmk__pqre.update(extra_globals)
    func.__globals__.update(zmk__pqre)
    if pysig is not None:
        pre_nodes = [] if pre_nodes is None else pre_nodes
        scope = next(iter(pass_info.func_ir.blocks.values())).scope
        loc = scope.loc

        def normal_handler(index, param, default):
            return default

        def default_handler(index, param, default):
            bbl__yukuc = ir.Var(scope, mk_unique_var('defaults'), loc)
            try:
                pass_info.typemap[bbl__yukuc.name] = types.literal(default)
            except:
                pass_info.typemap[bbl__yukuc.name] = numba.typeof(default)
            qdiq__nojr = ir.Assign(ir.Const(default, loc), bbl__yukuc, loc)
            pre_nodes.append(qdiq__nojr)
            return bbl__yukuc
        args = numba.core.typing.fold_arguments(pysig, args, kws,
            normal_handler, default_handler, normal_handler)
    gljh__vih = tuple(pass_info.typemap[rpigf__ntt.name] for rpigf__ntt in args
        )
    if const:
        tetm__jjx = []
        for uaqan__wjvc, ovz__gck in enumerate(args):
            vmw__sydrd = guard(find_const, pass_info.func_ir, ovz__gck)
            if vmw__sydrd:
                tetm__jjx.append(types.literal(vmw__sydrd))
            else:
                tetm__jjx.append(gljh__vih[uaqan__wjvc])
        gljh__vih = tuple(tetm__jjx)
    return ReplaceFunc(func, gljh__vih, args, zmk__pqre, inline_bodo_calls,
        run_full_pipeline, pre_nodes)


def is_var_size_item_array_type(t):
    assert is_array_typ(t, False)
    return t == string_array_type or isinstance(t, ArrayItemArrayType
        ) or isinstance(t, StructArrayType) and any(
        is_var_size_item_array_type(lescy__kbfo) for lescy__kbfo in t.data)


def gen_init_varsize_alloc_sizes(t):
    if t == string_array_type:
        vblv__xty = 'num_chars_{}'.format(ir_utils.next_label())
        return f'  {vblv__xty} = 0\n', (vblv__xty,)
    if isinstance(t, ArrayItemArrayType):
        foet__ulvns, fuvqy__kyho = gen_init_varsize_alloc_sizes(t.dtype)
        vblv__xty = 'num_items_{}'.format(ir_utils.next_label())
        return f'  {vblv__xty} = 0\n' + foet__ulvns, (vblv__xty,) + fuvqy__kyho
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
        return 1 + sum(get_type_alloc_counts(lescy__kbfo.dtype) for
            lescy__kbfo in t.data)
    if isinstance(t, ArrayItemArrayType) or t == string_array_type:
        return 1 + get_type_alloc_counts(t.dtype)
    if isinstance(t, MapArrayType):
        return get_type_alloc_counts(t.key_arr_type) + get_type_alloc_counts(t
            .value_arr_type)
    if bodo.utils.utils.is_array_typ(t, False) or t == bodo.string_type:
        return 1
    if isinstance(t, StructType):
        return sum(get_type_alloc_counts(lescy__kbfo) for lescy__kbfo in t.data
            )
    if isinstance(t, types.BaseTuple):
        return sum(get_type_alloc_counts(lescy__kbfo) for lescy__kbfo in t.
            types)
    return 0


def find_udf_str_name(obj_dtype, func_name, typing_context, caller_name):
    hpolt__vlj = typing_context.resolve_getattr(obj_dtype, func_name)
    if hpolt__vlj is None:
        lpsij__zrztl = types.misc.Module(np)
        try:
            hpolt__vlj = typing_context.resolve_getattr(lpsij__zrztl, func_name
                )
        except AttributeError as fzeit__dlen:
            hpolt__vlj = None
        if hpolt__vlj is None:
            raise BodoError(
                f"{caller_name}(): No Pandas method or Numpy function found with the name '{func_name}'."
                )
    return hpolt__vlj


def get_udf_str_return_type(obj_dtype, func_name, typing_context,
    caller_name, axis=None):
    hpolt__vlj = find_udf_str_name(obj_dtype, func_name, typing_context,
        caller_name)
    if isinstance(hpolt__vlj, types.BoundFunction):
        if axis is not None:
            choi__usnck = hpolt__vlj.get_call_type(typing_context, (), {
                'axis': axis})
        else:
            choi__usnck = hpolt__vlj.get_call_type(typing_context, (), {})
        return choi__usnck.return_type
    else:
        if bodo.utils.typing.is_numpy_ufunc(hpolt__vlj):
            choi__usnck = hpolt__vlj.get_call_type(typing_context, (
                obj_dtype,), {})
            return choi__usnck.return_type
        raise BodoError(
            f"{caller_name}(): Only Pandas methods and np.ufunc are supported as string literals. '{func_name}' not supported."
            )


def get_pandas_method_str_impl(obj_dtype, func_name, typing_context,
    caller_name, axis=None):
    hpolt__vlj = find_udf_str_name(obj_dtype, func_name, typing_context,
        caller_name)
    if isinstance(hpolt__vlj, types.BoundFunction):
        obgr__ljryi = hpolt__vlj.template
        if axis is not None:
            return obgr__ljryi._overload_func(obj_dtype, axis=axis)
        else:
            return obgr__ljryi._overload_func(obj_dtype)
    return None


def dict_to_const_keys_var_values_lists(dict_var, func_ir, arg_types,
    typemap, updated_containers, require_const_map, label):
    require(isinstance(dict_var, ir.Var))
    nizdd__fmx = get_definition(func_ir, dict_var)
    require(isinstance(nizdd__fmx, ir.Expr))
    require(nizdd__fmx.op == 'build_map')
    apxg__frthk = nizdd__fmx.items
    wbv__spyq = []
    values = []
    wxq__onjdb = False
    for uaqan__wjvc in range(len(apxg__frthk)):
        wnsn__uacjs, value = apxg__frthk[uaqan__wjvc]
        try:
            jkd__wtoqo = get_const_value_inner(func_ir, wnsn__uacjs,
                arg_types, typemap, updated_containers)
            wbv__spyq.append(jkd__wtoqo)
            values.append(value)
        except GuardException as fzeit__dlen:
            require_const_map[wnsn__uacjs] = label
            wxq__onjdb = True
    if wxq__onjdb:
        raise GuardException
    return wbv__spyq, values


def _get_const_keys_from_dict(args, func_ir, build_map, err_msg, loc):
    try:
        wbv__spyq = tuple(get_const_value_inner(func_ir, t[0], args) for t in
            build_map.items)
    except GuardException as fzeit__dlen:
        raise BodoError(err_msg, loc)
    if not all(isinstance(c, (str, int)) for c in wbv__spyq):
        raise BodoError(err_msg, loc)
    return wbv__spyq


def _convert_const_key_dict(args, func_ir, build_map, err_msg, scope, loc,
    output_sentinel_tuple=False):
    wbv__spyq = _get_const_keys_from_dict(args, func_ir, build_map, err_msg,
        loc)
    vxd__bzyq = []
    awq__hejma = [bodo.transforms.typing_pass._create_const_var(cux__hbms,
        'dict_key', scope, loc, vxd__bzyq) for cux__hbms in wbv__spyq]
    wrlxr__imuxz = [t[1] for t in build_map.items]
    if output_sentinel_tuple:
        sfwp__nlkqb = ir.Var(scope, mk_unique_var('sentinel'), loc)
        rxfg__xpv = ir.Var(scope, mk_unique_var('dict_tup'), loc)
        vxd__bzyq.append(ir.Assign(ir.Const('__bodo_tup', loc), sfwp__nlkqb,
            loc))
        bly__tvqq = [sfwp__nlkqb] + awq__hejma + wrlxr__imuxz
        vxd__bzyq.append(ir.Assign(ir.Expr.build_tuple(bly__tvqq, loc),
            rxfg__xpv, loc))
        return (rxfg__xpv,), vxd__bzyq
    else:
        hqfek__lvnh = ir.Var(scope, mk_unique_var('values_tup'), loc)
        alyb__gty = ir.Var(scope, mk_unique_var('idx_tup'), loc)
        vxd__bzyq.append(ir.Assign(ir.Expr.build_tuple(wrlxr__imuxz, loc),
            hqfek__lvnh, loc))
        vxd__bzyq.append(ir.Assign(ir.Expr.build_tuple(awq__hejma, loc),
            alyb__gty, loc))
        return (hqfek__lvnh, alyb__gty), vxd__bzyq
