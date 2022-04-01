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
    fpnxk__pclm = tuple(call_list)
    if fpnxk__pclm in no_side_effect_call_tuples:
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
    if len(fpnxk__pclm) == 1 and tuple in getattr(fpnxk__pclm[0], '__mro__', ()
        ):
        return True
    return False


numba.core.ir_utils.remove_call_handlers.append(remove_hiframes)


def compile_func_single_block(func, args, ret_var, typing_info=None,
    extra_globals=None, infer_types=True, run_untyped_pass=False, flags=
    None, replace_globals=True):
    tgy__zlt = {'numba': numba, 'np': np, 'bodo': bodo, 'pd': pd, 'math': math}
    if extra_globals is not None:
        tgy__zlt.update(extra_globals)
    if not replace_globals:
        tgy__zlt = func.__globals__
    loc = ir.Loc('', 0)
    if ret_var:
        loc = ret_var.loc
    if typing_info and infer_types:
        loc = typing_info.curr_loc
        f_ir = compile_to_numba_ir(func, tgy__zlt, typingctx=typing_info.
            typingctx, targetctx=typing_info.targetctx, arg_typs=tuple(
            typing_info.typemap[ydgtn__mwavu.name] for ydgtn__mwavu in args
            ), typemap=typing_info.typemap, calltypes=typing_info.calltypes)
    else:
        f_ir = compile_to_numba_ir(func, tgy__zlt)
    assert len(f_ir.blocks
        ) == 1, 'only single block functions supported in compile_func_single_block()'
    if run_untyped_pass:
        qbc__cxa = tuple(typing_info.typemap[ydgtn__mwavu.name] for
            ydgtn__mwavu in args)
        rmcos__rkc = bodo.transforms.untyped_pass.UntypedPass(f_ir,
            typing_info.typingctx, qbc__cxa, {}, {}, flags)
        rmcos__rkc.run()
    xoec__apdjq = f_ir.blocks.popitem()[1]
    replace_arg_nodes(xoec__apdjq, args)
    grflo__tpqjq = xoec__apdjq.body[:-2]
    update_locs(grflo__tpqjq[len(args):], loc)
    for stmt in grflo__tpqjq[:len(args)]:
        stmt.target.loc = loc
    if ret_var is not None:
        pmqfo__onnf = xoec__apdjq.body[-2]
        assert is_assign(pmqfo__onnf) and is_expr(pmqfo__onnf.value, 'cast')
        fgl__gboh = pmqfo__onnf.value.value
        grflo__tpqjq.append(ir.Assign(fgl__gboh, ret_var, loc))
    return grflo__tpqjq


def update_locs(node_list, loc):
    for stmt in node_list:
        stmt.loc = loc
        for xnysm__jtbyv in stmt.list_vars():
            xnysm__jtbyv.loc = loc
        if is_assign(stmt):
            stmt.value.loc = loc


def get_stmt_defs(stmt):
    if is_assign(stmt):
        return set([stmt.target.name])
    if type(stmt) in numba.core.analysis.ir_extension_usedefs:
        hvu__mpz = numba.core.analysis.ir_extension_usedefs[type(stmt)]
        ahs__bdxyb, gfns__kst = hvu__mpz(stmt)
        return gfns__kst
    return set()


def get_const_value(var, func_ir, err_msg, typemap=None, arg_types=None,
    file_info=None):
    if hasattr(var, 'loc'):
        loc = var.loc
    else:
        loc = None
    try:
        prjp__prn = get_const_value_inner(func_ir, var, arg_types, typemap,
            file_info=file_info)
        if isinstance(prjp__prn, ir.UndefinedType):
            odvxu__nrdjn = func_ir.get_definition(var.name).name
            raise BodoError(f"name '{odvxu__nrdjn}' is not defined", loc=loc)
    except GuardException as ppac__oeamo:
        raise BodoError(err_msg, loc=loc)
    return prjp__prn


def get_const_value_inner(func_ir, var, arg_types=None, typemap=None,
    updated_containers=None, file_info=None, pyobject_to_literal=False,
    literalize_args=True):
    require(isinstance(var, ir.Var))
    lon__kfvsz = get_definition(func_ir, var)
    eqgh__hqv = None
    if typemap is not None:
        eqgh__hqv = typemap.get(var.name, None)
    if isinstance(lon__kfvsz, ir.Arg) and arg_types is not None:
        eqgh__hqv = arg_types[lon__kfvsz.index]
    if updated_containers and var.name in updated_containers:
        raise BodoConstUpdatedError(
            f"variable '{var.name}' is updated inplace using '{updated_containers[var.name]}'"
            )
    if is_literal_type(eqgh__hqv):
        return get_literal_value(eqgh__hqv)
    if isinstance(lon__kfvsz, (ir.Const, ir.Global, ir.FreeVar)):
        prjp__prn = lon__kfvsz.value
        return prjp__prn
    if literalize_args and isinstance(lon__kfvsz, ir.Arg
        ) and can_literalize_type(eqgh__hqv, pyobject_to_literal):
        raise numba.core.errors.ForceLiteralArg({lon__kfvsz.index}, loc=var
            .loc, file_infos={lon__kfvsz.index: file_info} if file_info is not
            None else None)
    if is_expr(lon__kfvsz, 'binop'):
        if file_info and lon__kfvsz.fn == operator.add:
            try:
                vek__ygk = get_const_value_inner(func_ir, lon__kfvsz.lhs,
                    arg_types, typemap, updated_containers, literalize_args
                    =False)
                file_info.set_concat(vek__ygk, True)
                yxjdj__dfkif = get_const_value_inner(func_ir, lon__kfvsz.
                    rhs, arg_types, typemap, updated_containers, file_info)
                return lon__kfvsz.fn(vek__ygk, yxjdj__dfkif)
            except (GuardException, BodoConstUpdatedError) as ppac__oeamo:
                pass
            try:
                yxjdj__dfkif = get_const_value_inner(func_ir, lon__kfvsz.
                    rhs, arg_types, typemap, updated_containers,
                    literalize_args=False)
                file_info.set_concat(yxjdj__dfkif, False)
                vek__ygk = get_const_value_inner(func_ir, lon__kfvsz.lhs,
                    arg_types, typemap, updated_containers, file_info)
                return lon__kfvsz.fn(vek__ygk, yxjdj__dfkif)
            except (GuardException, BodoConstUpdatedError) as ppac__oeamo:
                pass
        vek__ygk = get_const_value_inner(func_ir, lon__kfvsz.lhs, arg_types,
            typemap, updated_containers)
        yxjdj__dfkif = get_const_value_inner(func_ir, lon__kfvsz.rhs,
            arg_types, typemap, updated_containers)
        return lon__kfvsz.fn(vek__ygk, yxjdj__dfkif)
    if is_expr(lon__kfvsz, 'unary'):
        prjp__prn = get_const_value_inner(func_ir, lon__kfvsz.value,
            arg_types, typemap, updated_containers)
        return lon__kfvsz.fn(prjp__prn)
    if is_expr(lon__kfvsz, 'getattr') and typemap:
        nnamm__samqs = typemap.get(lon__kfvsz.value.name, None)
        if isinstance(nnamm__samqs, bodo.hiframes.pd_dataframe_ext.
            DataFrameType) and lon__kfvsz.attr == 'columns':
            return pd.Index(nnamm__samqs.columns)
        if isinstance(nnamm__samqs, types.SliceType):
            okmh__cay = get_definition(func_ir, lon__kfvsz.value)
            require(is_call(okmh__cay))
            ikn__kjc = find_callname(func_ir, okmh__cay)
            hymsr__ard = False
            if ikn__kjc == ('_normalize_slice', 'numba.cpython.unicode'):
                require(lon__kfvsz.attr in ('start', 'step'))
                okmh__cay = get_definition(func_ir, okmh__cay.args[0])
                hymsr__ard = True
            require(find_callname(func_ir, okmh__cay) == ('slice', 'builtins'))
            if len(okmh__cay.args) == 1:
                if lon__kfvsz.attr == 'start':
                    return 0
                if lon__kfvsz.attr == 'step':
                    return 1
                require(lon__kfvsz.attr == 'stop')
                return get_const_value_inner(func_ir, okmh__cay.args[0],
                    arg_types, typemap, updated_containers)
            if lon__kfvsz.attr == 'start':
                prjp__prn = get_const_value_inner(func_ir, okmh__cay.args[0
                    ], arg_types, typemap, updated_containers)
                if prjp__prn is None:
                    prjp__prn = 0
                if hymsr__ard:
                    require(prjp__prn == 0)
                return prjp__prn
            if lon__kfvsz.attr == 'stop':
                assert not hymsr__ard
                return get_const_value_inner(func_ir, okmh__cay.args[1],
                    arg_types, typemap, updated_containers)
            require(lon__kfvsz.attr == 'step')
            if len(okmh__cay.args) == 2:
                return 1
            else:
                prjp__prn = get_const_value_inner(func_ir, okmh__cay.args[2
                    ], arg_types, typemap, updated_containers)
                if prjp__prn is None:
                    prjp__prn = 1
                if hymsr__ard:
                    require(prjp__prn == 1)
                return prjp__prn
    if is_expr(lon__kfvsz, 'getattr'):
        return getattr(get_const_value_inner(func_ir, lon__kfvsz.value,
            arg_types, typemap, updated_containers), lon__kfvsz.attr)
    if is_expr(lon__kfvsz, 'getitem'):
        value = get_const_value_inner(func_ir, lon__kfvsz.value, arg_types,
            typemap, updated_containers)
        index = get_const_value_inner(func_ir, lon__kfvsz.index, arg_types,
            typemap, updated_containers)
        return value[index]
    bmwyq__fwm = guard(find_callname, func_ir, lon__kfvsz, typemap)
    if bmwyq__fwm is not None and len(bmwyq__fwm) == 2 and bmwyq__fwm[0
        ] == 'keys' and isinstance(bmwyq__fwm[1], ir.Var):
        egmc__qwkmc = lon__kfvsz.func
        lon__kfvsz = get_definition(func_ir, bmwyq__fwm[1])
        itzis__nbwl = bmwyq__fwm[1].name
        if updated_containers and itzis__nbwl in updated_containers:
            raise BodoConstUpdatedError(
                "variable '{}' is updated inplace using '{}'".format(
                itzis__nbwl, updated_containers[itzis__nbwl]))
        require(is_expr(lon__kfvsz, 'build_map'))
        vals = [xnysm__jtbyv[0] for xnysm__jtbyv in lon__kfvsz.items]
        mega__aivp = guard(get_definition, func_ir, egmc__qwkmc)
        assert isinstance(mega__aivp, ir.Expr) and mega__aivp.attr == 'keys'
        mega__aivp.attr = 'copy'
        return [get_const_value_inner(func_ir, xnysm__jtbyv, arg_types,
            typemap, updated_containers) for xnysm__jtbyv in vals]
    if is_expr(lon__kfvsz, 'build_map'):
        return {get_const_value_inner(func_ir, xnysm__jtbyv[0], arg_types,
            typemap, updated_containers): get_const_value_inner(func_ir,
            xnysm__jtbyv[1], arg_types, typemap, updated_containers) for
            xnysm__jtbyv in lon__kfvsz.items}
    if is_expr(lon__kfvsz, 'build_tuple'):
        return tuple(get_const_value_inner(func_ir, xnysm__jtbyv, arg_types,
            typemap, updated_containers) for xnysm__jtbyv in lon__kfvsz.items)
    if is_expr(lon__kfvsz, 'build_list'):
        return [get_const_value_inner(func_ir, xnysm__jtbyv, arg_types,
            typemap, updated_containers) for xnysm__jtbyv in lon__kfvsz.items]
    if is_expr(lon__kfvsz, 'build_set'):
        return {get_const_value_inner(func_ir, xnysm__jtbyv, arg_types,
            typemap, updated_containers) for xnysm__jtbyv in lon__kfvsz.items}
    if bmwyq__fwm == ('list', 'builtins'):
        values = get_const_value_inner(func_ir, lon__kfvsz.args[0],
            arg_types, typemap, updated_containers)
        if isinstance(values, set):
            values = sorted(values)
        return list(values)
    if bmwyq__fwm == ('set', 'builtins'):
        return set(get_const_value_inner(func_ir, lon__kfvsz.args[0],
            arg_types, typemap, updated_containers))
    if bmwyq__fwm == ('range', 'builtins') and len(lon__kfvsz.args) == 1:
        return range(get_const_value_inner(func_ir, lon__kfvsz.args[0],
            arg_types, typemap, updated_containers))
    if bmwyq__fwm == ('slice', 'builtins'):
        return slice(*tuple(get_const_value_inner(func_ir, xnysm__jtbyv,
            arg_types, typemap, updated_containers) for xnysm__jtbyv in
            lon__kfvsz.args))
    if bmwyq__fwm == ('str', 'builtins'):
        return str(get_const_value_inner(func_ir, lon__kfvsz.args[0],
            arg_types, typemap, updated_containers))
    if bmwyq__fwm == ('bool', 'builtins'):
        return bool(get_const_value_inner(func_ir, lon__kfvsz.args[0],
            arg_types, typemap, updated_containers))
    if bmwyq__fwm == ('format', 'builtins'):
        ydgtn__mwavu = get_const_value_inner(func_ir, lon__kfvsz.args[0],
            arg_types, typemap, updated_containers)
        gbea__segaa = get_const_value_inner(func_ir, lon__kfvsz.args[1],
            arg_types, typemap, updated_containers) if len(lon__kfvsz.args
            ) > 1 else ''
        return format(ydgtn__mwavu, gbea__segaa)
    if bmwyq__fwm in (('init_binary_str_index',
        'bodo.hiframes.pd_index_ext'), ('init_numeric_index',
        'bodo.hiframes.pd_index_ext'), ('init_categorical_index',
        'bodo.hiframes.pd_index_ext'), ('init_datetime_index',
        'bodo.hiframes.pd_index_ext'), ('init_timedelta_index',
        'bodo.hiframes.pd_index_ext'), ('init_heter_index',
        'bodo.hiframes.pd_index_ext')):
        return pd.Index(get_const_value_inner(func_ir, lon__kfvsz.args[0],
            arg_types, typemap, updated_containers))
    if bmwyq__fwm == ('str_arr_from_sequence', 'bodo.libs.str_arr_ext'):
        return np.array(get_const_value_inner(func_ir, lon__kfvsz.args[0],
            arg_types, typemap, updated_containers))
    if bmwyq__fwm == ('init_range_index', 'bodo.hiframes.pd_index_ext'):
        return pd.RangeIndex(get_const_value_inner(func_ir, lon__kfvsz.args
            [0], arg_types, typemap, updated_containers),
            get_const_value_inner(func_ir, lon__kfvsz.args[1], arg_types,
            typemap, updated_containers), get_const_value_inner(func_ir,
            lon__kfvsz.args[2], arg_types, typemap, updated_containers))
    if bmwyq__fwm == ('len', 'builtins') and typemap and isinstance(typemap
        .get(lon__kfvsz.args[0].name, None), types.BaseTuple):
        return len(typemap[lon__kfvsz.args[0].name])
    if bmwyq__fwm == ('len', 'builtins'):
        nkrt__nxexs = guard(get_definition, func_ir, lon__kfvsz.args[0])
        if isinstance(nkrt__nxexs, ir.Expr) and nkrt__nxexs.op in (
            'build_tuple', 'build_list', 'build_set', 'build_map'):
            return len(nkrt__nxexs.items)
        return len(get_const_value_inner(func_ir, lon__kfvsz.args[0],
            arg_types, typemap, updated_containers))
    if bmwyq__fwm == ('CategoricalDtype', 'pandas'):
        kws = dict(lon__kfvsz.kws)
        qnhz__yvzg = get_call_expr_arg('CategoricalDtype', lon__kfvsz.args,
            kws, 0, 'categories', '')
        hswb__kaf = get_call_expr_arg('CategoricalDtype', lon__kfvsz.args,
            kws, 1, 'ordered', False)
        if hswb__kaf is not False:
            hswb__kaf = get_const_value_inner(func_ir, hswb__kaf, arg_types,
                typemap, updated_containers)
        if qnhz__yvzg == '':
            qnhz__yvzg = None
        else:
            qnhz__yvzg = get_const_value_inner(func_ir, qnhz__yvzg,
                arg_types, typemap, updated_containers)
        return pd.CategoricalDtype(qnhz__yvzg, hswb__kaf)
    if bmwyq__fwm == ('dtype', 'numpy'):
        return np.dtype(get_const_value_inner(func_ir, lon__kfvsz.args[0],
            arg_types, typemap, updated_containers))
    if bmwyq__fwm is not None and len(bmwyq__fwm) == 2 and bmwyq__fwm[1
        ] == 'pandas' and bmwyq__fwm[0] in ('Int8Dtype', 'Int16Dtype',
        'Int32Dtype', 'Int64Dtype', 'UInt8Dtype', 'UInt16Dtype',
        'UInt32Dtype', 'UInt64Dtype'):
        return getattr(pd, bmwyq__fwm[0])()
    if bmwyq__fwm is not None and len(bmwyq__fwm) == 2 and isinstance(
        bmwyq__fwm[1], ir.Var):
        prjp__prn = get_const_value_inner(func_ir, bmwyq__fwm[1], arg_types,
            typemap, updated_containers)
        args = [get_const_value_inner(func_ir, xnysm__jtbyv, arg_types,
            typemap, updated_containers) for xnysm__jtbyv in lon__kfvsz.args]
        kws = {pzqwy__kfmxb[0]: get_const_value_inner(func_ir, pzqwy__kfmxb
            [1], arg_types, typemap, updated_containers) for pzqwy__kfmxb in
            lon__kfvsz.kws}
        return getattr(prjp__prn, bmwyq__fwm[0])(*args, **kws)
    if bmwyq__fwm is not None and len(bmwyq__fwm) == 2 and bmwyq__fwm[1
        ] == 'bodo' and bmwyq__fwm[0] in bodo_types_with_params:
        args = tuple(get_const_value_inner(func_ir, xnysm__jtbyv, arg_types,
            typemap, updated_containers) for xnysm__jtbyv in lon__kfvsz.args)
        kwargs = {odvxu__nrdjn: get_const_value_inner(func_ir, xnysm__jtbyv,
            arg_types, typemap, updated_containers) for odvxu__nrdjn,
            xnysm__jtbyv in dict(lon__kfvsz.kws).items()}
        return getattr(bodo, bmwyq__fwm[0])(*args, **kwargs)
    if is_call(lon__kfvsz) and typemap and isinstance(typemap.get(
        lon__kfvsz.func.name, None), types.Dispatcher):
        py_func = typemap[lon__kfvsz.func.name].dispatcher.py_func
        require(lon__kfvsz.vararg is None)
        args = tuple(get_const_value_inner(func_ir, xnysm__jtbyv, arg_types,
            typemap, updated_containers) for xnysm__jtbyv in lon__kfvsz.args)
        kwargs = {odvxu__nrdjn: get_const_value_inner(func_ir, xnysm__jtbyv,
            arg_types, typemap, updated_containers) for odvxu__nrdjn,
            xnysm__jtbyv in dict(lon__kfvsz.kws).items()}
        arg_types = tuple(bodo.typeof(xnysm__jtbyv) for xnysm__jtbyv in args)
        kw_types = {quo__itx: bodo.typeof(xnysm__jtbyv) for quo__itx,
            xnysm__jtbyv in kwargs.items()}
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
    f_ir, typemap, teyuv__eyk, teyuv__eyk = bodo.compiler.get_func_type_info(
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
                    uch__xea = guard(get_definition, f_ir, rhs.func)
                    if isinstance(uch__xea, ir.Const) and isinstance(uch__xea
                        .value, numba.core.dispatcher.ObjModeLiftedWith):
                        return False
                    xsgum__gufo = guard(find_callname, f_ir, rhs)
                    if xsgum__gufo is None:
                        return False
                    func_name, god__zcio = xsgum__gufo
                    if god__zcio == 'pandas' and func_name.startswith('read_'):
                        return False
                    if xsgum__gufo in (('fromfile', 'numpy'), ('file_read',
                        'bodo.io.np_io')):
                        return False
                    if xsgum__gufo == ('File', 'h5py'):
                        return False
                    if isinstance(god__zcio, ir.Var):
                        eqgh__hqv = typemap[god__zcio.name]
                        if isinstance(eqgh__hqv, (DataFrameType, SeriesType)
                            ) and func_name in ('to_csv', 'to_excel',
                            'to_json', 'to_sql', 'to_pickle', 'to_parquet',
                            'info'):
                            return False
                        if isinstance(eqgh__hqv, types.Array
                            ) and func_name == 'tofile':
                            return False
                        if isinstance(eqgh__hqv, bodo.LoggingLoggerType):
                            return False
                        if str(eqgh__hqv).startswith('Mpl'):
                            return False
                        if (func_name in container_update_method_names and
                            isinstance(guard(get_definition, f_ir,
                            god__zcio), ir.Arg)):
                            return False
                    if god__zcio in ('numpy.random', 'time', 'logging',
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
        urjy__uvyh = func.literal_value.code
        lvry__sznn = {'np': np, 'pd': pd, 'numba': numba, 'bodo': bodo}
        if hasattr(func.literal_value, 'globals'):
            lvry__sznn = func.literal_value.globals
        f_ir = numba.core.ir_utils.get_ir_of_code(lvry__sznn, urjy__uvyh)
        fix_struct_return(f_ir)
        typemap, qgv__iphr, qmclr__akrey, teyuv__eyk = (numba.core.
            typed_passes.type_inference_stage(typing_context,
            target_context, f_ir, arg_types, None))
    elif isinstance(func, bodo.utils.typing.FunctionLiteral):
        py_func = func.literal_value
        f_ir, typemap, qmclr__akrey, qgv__iphr = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    elif isinstance(func, CPUDispatcher):
        py_func = func.py_func
        f_ir, typemap, qmclr__akrey, qgv__iphr = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    else:
        if not isinstance(func, types.Dispatcher):
            if isinstance(func, types.Function):
                raise BodoError(
                    f'Bodo does not support built-in functions yet, {func}')
            else:
                raise BodoError(f'Function type expected, not {func}')
        py_func = func.dispatcher.py_func
        f_ir, typemap, qmclr__akrey, qgv__iphr = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    if is_udf and isinstance(qgv__iphr, types.DictType):
        txd__opz = guard(get_struct_keynames, f_ir, typemap)
        if txd__opz is not None:
            qgv__iphr = StructType((qgv__iphr.value_type,) * len(txd__opz),
                txd__opz)
    if is_udf and isinstance(qgv__iphr, (SeriesType, HeterogeneousSeriesType)):
        wtd__avaeq = numba.core.registry.cpu_target.typing_context
        gztd__otwcx = numba.core.registry.cpu_target.target_context
        wqc__rdww = bodo.transforms.series_pass.SeriesPass(f_ir, wtd__avaeq,
            gztd__otwcx, typemap, qmclr__akrey, {})
        wqc__rdww.run()
        wqc__rdww.run()
        wqc__rdww.run()
        cke__nzx = compute_cfg_from_blocks(f_ir.blocks)
        bhc__htj = [guard(_get_const_series_info, f_ir.blocks[tlmbe__vov],
            f_ir, typemap) for tlmbe__vov in cke__nzx.exit_points() if
            isinstance(f_ir.blocks[tlmbe__vov].body[-1], ir.Return)]
        if None in bhc__htj or len(pd.Series(bhc__htj).unique()) != 1:
            qgv__iphr.const_info = None
        else:
            qgv__iphr.const_info = bhc__htj[0]
    return qgv__iphr


def _get_const_series_info(block, f_ir, typemap):
    from bodo.hiframes.pd_series_ext import HeterogeneousSeriesType
    assert isinstance(block.body[-1], ir.Return)
    gkny__xdcp = block.body[-1].value
    niz__hupq = get_definition(f_ir, gkny__xdcp)
    require(is_expr(niz__hupq, 'cast'))
    niz__hupq = get_definition(f_ir, niz__hupq.value)
    require(is_call(niz__hupq) and find_callname(f_ir, niz__hupq) == (
        'init_series', 'bodo.hiframes.pd_series_ext'))
    oea__qofla = niz__hupq.args[1]
    wipr__ghotr = tuple(get_const_value_inner(f_ir, oea__qofla, typemap=
        typemap))
    if isinstance(typemap[gkny__xdcp.name], HeterogeneousSeriesType):
        return len(typemap[gkny__xdcp.name].data), wipr__ghotr
    hdcu__lujx = niz__hupq.args[0]
    hgg__jhv = get_definition(f_ir, hdcu__lujx)
    func_name, ojki__rxu = find_callname(f_ir, hgg__jhv)
    if is_call(hgg__jhv) and bodo.utils.utils.is_alloc_callname(func_name,
        ojki__rxu):
        zgkqv__ebkiy = hgg__jhv.args[0]
        lrp__hcj = get_const_value_inner(f_ir, zgkqv__ebkiy, typemap=typemap)
        return lrp__hcj, wipr__ghotr
    if is_call(hgg__jhv) and find_callname(f_ir, hgg__jhv) in [('asarray',
        'numpy'), ('str_arr_from_sequence', 'bodo.libs.str_arr_ext')]:
        hdcu__lujx = hgg__jhv.args[0]
        hgg__jhv = get_definition(f_ir, hdcu__lujx)
    require(is_expr(hgg__jhv, 'build_tuple') or is_expr(hgg__jhv, 'build_list')
        )
    return len(hgg__jhv.items), wipr__ghotr


def extract_keyvals_from_struct_map(f_ir, build_map, loc, scope, typemap=None):
    lla__vlpo = []
    mttxn__rovbz = []
    values = []
    for quo__itx, xnysm__jtbyv in build_map.items:
        ndr__coj = find_const(f_ir, quo__itx)
        require(isinstance(ndr__coj, str))
        mttxn__rovbz.append(ndr__coj)
        lla__vlpo.append(quo__itx)
        values.append(xnysm__jtbyv)
    givts__xsbv = ir.Var(scope, mk_unique_var('val_tup'), loc)
    goyc__jcps = ir.Assign(ir.Expr.build_tuple(values, loc), givts__xsbv, loc)
    f_ir._definitions[givts__xsbv.name] = [goyc__jcps.value]
    uqcb__uxd = ir.Var(scope, mk_unique_var('key_tup'), loc)
    ztf__irrg = ir.Assign(ir.Expr.build_tuple(lla__vlpo, loc), uqcb__uxd, loc)
    f_ir._definitions[uqcb__uxd.name] = [ztf__irrg.value]
    if typemap is not None:
        typemap[givts__xsbv.name] = types.Tuple([typemap[xnysm__jtbyv.name] for
            xnysm__jtbyv in values])
        typemap[uqcb__uxd.name] = types.Tuple([typemap[xnysm__jtbyv.name] for
            xnysm__jtbyv in lla__vlpo])
    return mttxn__rovbz, givts__xsbv, goyc__jcps, uqcb__uxd, ztf__irrg


def _replace_const_map_return(f_ir, block, label):
    require(isinstance(block.body[-1], ir.Return))
    whg__ffcfp = block.body[-1].value
    khsv__abw = guard(get_definition, f_ir, whg__ffcfp)
    require(is_expr(khsv__abw, 'cast'))
    niz__hupq = guard(get_definition, f_ir, khsv__abw.value)
    require(is_expr(niz__hupq, 'build_map'))
    require(len(niz__hupq.items) > 0)
    loc = block.loc
    scope = block.scope
    mttxn__rovbz, givts__xsbv, goyc__jcps, uqcb__uxd, ztf__irrg = (
        extract_keyvals_from_struct_map(f_ir, niz__hupq, loc, scope))
    yba__rkgw = ir.Var(scope, mk_unique_var('conv_call'), loc)
    erq__xvdb = ir.Assign(ir.Global('struct_if_heter_dict', bodo.utils.
        conversion.struct_if_heter_dict, loc), yba__rkgw, loc)
    f_ir._definitions[yba__rkgw.name] = [erq__xvdb.value]
    rfq__pyjqt = ir.Var(scope, mk_unique_var('struct_val'), loc)
    jxwrl__ini = ir.Assign(ir.Expr.call(yba__rkgw, [givts__xsbv, uqcb__uxd],
        {}, loc), rfq__pyjqt, loc)
    f_ir._definitions[rfq__pyjqt.name] = [jxwrl__ini.value]
    khsv__abw.value = rfq__pyjqt
    niz__hupq.items = [(quo__itx, quo__itx) for quo__itx, teyuv__eyk in
        niz__hupq.items]
    block.body = block.body[:-2] + [goyc__jcps, ztf__irrg, erq__xvdb,
        jxwrl__ini] + block.body[-2:]
    return tuple(mttxn__rovbz)


def get_struct_keynames(f_ir, typemap):
    cke__nzx = compute_cfg_from_blocks(f_ir.blocks)
    zco__wun = list(cke__nzx.exit_points())[0]
    block = f_ir.blocks[zco__wun]
    require(isinstance(block.body[-1], ir.Return))
    whg__ffcfp = block.body[-1].value
    khsv__abw = guard(get_definition, f_ir, whg__ffcfp)
    require(is_expr(khsv__abw, 'cast'))
    niz__hupq = guard(get_definition, f_ir, khsv__abw.value)
    require(is_call(niz__hupq) and find_callname(f_ir, niz__hupq) == (
        'struct_if_heter_dict', 'bodo.utils.conversion'))
    return get_overload_const_list(typemap[niz__hupq.args[1].name])


def fix_struct_return(f_ir):
    vhvh__gxa = None
    cke__nzx = compute_cfg_from_blocks(f_ir.blocks)
    for zco__wun in cke__nzx.exit_points():
        vhvh__gxa = guard(_replace_const_map_return, f_ir, f_ir.blocks[
            zco__wun], zco__wun)
    return vhvh__gxa


def update_node_list_definitions(node_list, func_ir):
    loc = ir.Loc('', 0)
    kwwun__mzrwo = ir.Block(ir.Scope(None, loc), loc)
    kwwun__mzrwo.body = node_list
    build_definitions({(0): kwwun__mzrwo}, func_ir._definitions)
    return


NESTED_TUP_SENTINEL = '$BODO_NESTED_TUP'


def gen_const_val_str(c):
    if isinstance(c, tuple):
        return "'{}{}', ".format(NESTED_TUP_SENTINEL, len(c)) + ', '.join(
            gen_const_val_str(xnysm__jtbyv) for xnysm__jtbyv in c)
    if isinstance(c, str):
        return "'{}'".format(c)
    if isinstance(c, (pd.Timestamp, pd.Timedelta, float)):
        return "'{}'".format(c)
    return str(c)


def gen_const_tup(vals):
    qojx__tmrue = ', '.join(gen_const_val_str(c) for c in vals)
    return '({}{})'.format(qojx__tmrue, ',' if len(vals) == 1 else '')


def get_const_tup_vals(c_typ):
    vals = get_overload_const_list(c_typ)
    return _get_original_nested_tups(vals)


def _get_original_nested_tups(vals):
    for lrdjx__dkl in range(len(vals) - 1, -1, -1):
        xnysm__jtbyv = vals[lrdjx__dkl]
        if isinstance(xnysm__jtbyv, str) and xnysm__jtbyv.startswith(
            NESTED_TUP_SENTINEL):
            nrz__ewhd = int(xnysm__jtbyv[len(NESTED_TUP_SENTINEL):])
            return _get_original_nested_tups(tuple(vals[:lrdjx__dkl]) + (
                tuple(vals[lrdjx__dkl + 1:lrdjx__dkl + nrz__ewhd + 1]),) +
                tuple(vals[lrdjx__dkl + nrz__ewhd + 1:]))
    return tuple(vals)


def get_call_expr_arg(f_name, args, kws, arg_no, arg_name, default=None,
    err_msg=None, use_default=False):
    ydgtn__mwavu = None
    if len(args) > arg_no and arg_no >= 0:
        ydgtn__mwavu = args[arg_no]
        if arg_name in kws:
            err_msg = (
                f"{f_name}() got multiple values for argument '{arg_name}'")
            raise BodoError(err_msg)
    elif arg_name in kws:
        ydgtn__mwavu = kws[arg_name]
    if ydgtn__mwavu is None:
        if use_default or default is not None:
            return default
        if err_msg is None:
            err_msg = "{} requires '{}' argument".format(f_name, arg_name)
        raise BodoError(err_msg)
    return ydgtn__mwavu


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
    tgy__zlt = {'numba': numba, 'np': np, 'bodo': bodo, 'pd': pd}
    if extra_globals is not None:
        tgy__zlt.update(extra_globals)
    func.__globals__.update(tgy__zlt)
    if pysig is not None:
        pre_nodes = [] if pre_nodes is None else pre_nodes
        scope = next(iter(pass_info.func_ir.blocks.values())).scope
        loc = scope.loc

        def normal_handler(index, param, default):
            return default

        def default_handler(index, param, default):
            gkvyt__ksnfz = ir.Var(scope, mk_unique_var('defaults'), loc)
            try:
                pass_info.typemap[gkvyt__ksnfz.name] = types.literal(default)
            except:
                pass_info.typemap[gkvyt__ksnfz.name] = numba.typeof(default)
            fkb__qzmly = ir.Assign(ir.Const(default, loc), gkvyt__ksnfz, loc)
            pre_nodes.append(fkb__qzmly)
            return gkvyt__ksnfz
        args = numba.core.typing.fold_arguments(pysig, args, kws,
            normal_handler, default_handler, normal_handler)
    qbc__cxa = tuple(pass_info.typemap[xnysm__jtbyv.name] for xnysm__jtbyv in
        args)
    if const:
        hvjbf__lva = []
        for lrdjx__dkl, ydgtn__mwavu in enumerate(args):
            prjp__prn = guard(find_const, pass_info.func_ir, ydgtn__mwavu)
            if prjp__prn:
                hvjbf__lva.append(types.literal(prjp__prn))
            else:
                hvjbf__lva.append(qbc__cxa[lrdjx__dkl])
        qbc__cxa = tuple(hvjbf__lva)
    return ReplaceFunc(func, qbc__cxa, args, tgy__zlt, inline_bodo_calls,
        run_full_pipeline, pre_nodes)


def is_var_size_item_array_type(t):
    assert is_array_typ(t, False)
    return t == string_array_type or isinstance(t, ArrayItemArrayType
        ) or isinstance(t, StructArrayType) and any(
        is_var_size_item_array_type(jftbx__affh) for jftbx__affh in t.data)


def gen_init_varsize_alloc_sizes(t):
    if t == string_array_type:
        oooia__bcwa = 'num_chars_{}'.format(ir_utils.next_label())
        return f'  {oooia__bcwa} = 0\n', (oooia__bcwa,)
    if isinstance(t, ArrayItemArrayType):
        xks__ujfkd, vgzl__rzhf = gen_init_varsize_alloc_sizes(t.dtype)
        oooia__bcwa = 'num_items_{}'.format(ir_utils.next_label())
        return f'  {oooia__bcwa} = 0\n' + xks__ujfkd, (oooia__bcwa,
            ) + vgzl__rzhf
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
        return 1 + sum(get_type_alloc_counts(jftbx__affh.dtype) for
            jftbx__affh in t.data)
    if isinstance(t, ArrayItemArrayType) or t == string_array_type:
        return 1 + get_type_alloc_counts(t.dtype)
    if isinstance(t, MapArrayType):
        return get_type_alloc_counts(t.key_arr_type) + get_type_alloc_counts(t
            .value_arr_type)
    if bodo.utils.utils.is_array_typ(t, False) or t == bodo.string_type:
        return 1
    if isinstance(t, StructType):
        return sum(get_type_alloc_counts(jftbx__affh) for jftbx__affh in t.data
            )
    if isinstance(t, types.BaseTuple):
        return sum(get_type_alloc_counts(jftbx__affh) for jftbx__affh in t.
            types)
    return 0


def find_udf_str_name(obj_dtype, func_name, typing_context, caller_name):
    aruug__vevd = typing_context.resolve_getattr(obj_dtype, func_name)
    if aruug__vevd is None:
        bop__ttun = types.misc.Module(np)
        try:
            aruug__vevd = typing_context.resolve_getattr(bop__ttun, func_name)
        except AttributeError as ppac__oeamo:
            aruug__vevd = None
        if aruug__vevd is None:
            raise BodoError(
                f"{caller_name}(): No Pandas method or Numpy function found with the name '{func_name}'."
                )
    return aruug__vevd


def get_udf_str_return_type(obj_dtype, func_name, typing_context,
    caller_name, axis=None):
    aruug__vevd = find_udf_str_name(obj_dtype, func_name, typing_context,
        caller_name)
    if isinstance(aruug__vevd, types.BoundFunction):
        if axis is not None:
            oxh__mhh = aruug__vevd.get_call_type(typing_context, (), {
                'axis': axis})
        else:
            oxh__mhh = aruug__vevd.get_call_type(typing_context, (), {})
        return oxh__mhh.return_type
    else:
        if bodo.utils.typing.is_numpy_ufunc(aruug__vevd):
            oxh__mhh = aruug__vevd.get_call_type(typing_context, (obj_dtype
                ,), {})
            return oxh__mhh.return_type
        raise BodoError(
            f"{caller_name}(): Only Pandas methods and np.ufunc are supported as string literals. '{func_name}' not supported."
            )


def get_pandas_method_str_impl(obj_dtype, func_name, typing_context,
    caller_name, axis=None):
    aruug__vevd = find_udf_str_name(obj_dtype, func_name, typing_context,
        caller_name)
    if isinstance(aruug__vevd, types.BoundFunction):
        vtl__tey = aruug__vevd.template
        if axis is not None:
            return vtl__tey._overload_func(obj_dtype, axis=axis)
        else:
            return vtl__tey._overload_func(obj_dtype)
    return None


def dict_to_const_keys_var_values_lists(dict_var, func_ir, arg_types,
    typemap, updated_containers, require_const_map, label):
    require(isinstance(dict_var, ir.Var))
    kdvo__ahcq = get_definition(func_ir, dict_var)
    require(isinstance(kdvo__ahcq, ir.Expr))
    require(kdvo__ahcq.op == 'build_map')
    cgwli__furhg = kdvo__ahcq.items
    lla__vlpo = []
    values = []
    zzb__xgo = False
    for lrdjx__dkl in range(len(cgwli__furhg)):
        wkfpl__zams, value = cgwli__furhg[lrdjx__dkl]
        try:
            qllq__roq = get_const_value_inner(func_ir, wkfpl__zams,
                arg_types, typemap, updated_containers)
            lla__vlpo.append(qllq__roq)
            values.append(value)
        except GuardException as ppac__oeamo:
            require_const_map[wkfpl__zams] = label
            zzb__xgo = True
    if zzb__xgo:
        raise GuardException
    return lla__vlpo, values


def _get_const_keys_from_dict(args, func_ir, build_map, err_msg, loc):
    try:
        lla__vlpo = tuple(get_const_value_inner(func_ir, t[0], args) for t in
            build_map.items)
    except GuardException as ppac__oeamo:
        raise BodoError(err_msg, loc)
    if not all(isinstance(c, (str, int)) for c in lla__vlpo):
        raise BodoError(err_msg, loc)
    return lla__vlpo


def _convert_const_key_dict(args, func_ir, build_map, err_msg, scope, loc,
    output_sentinel_tuple=False):
    lla__vlpo = _get_const_keys_from_dict(args, func_ir, build_map, err_msg,
        loc)
    ddjwz__tupp = []
    wcw__miac = [bodo.transforms.typing_pass._create_const_var(quo__itx,
        'dict_key', scope, loc, ddjwz__tupp) for quo__itx in lla__vlpo]
    rsmf__div = [t[1] for t in build_map.items]
    if output_sentinel_tuple:
        xpd__jwy = ir.Var(scope, mk_unique_var('sentinel'), loc)
        yja__ewngq = ir.Var(scope, mk_unique_var('dict_tup'), loc)
        ddjwz__tupp.append(ir.Assign(ir.Const('__bodo_tup', loc), xpd__jwy,
            loc))
        pao__zbf = [xpd__jwy] + wcw__miac + rsmf__div
        ddjwz__tupp.append(ir.Assign(ir.Expr.build_tuple(pao__zbf, loc),
            yja__ewngq, loc))
        return (yja__ewngq,), ddjwz__tupp
    else:
        pjyo__dtgv = ir.Var(scope, mk_unique_var('values_tup'), loc)
        rysil__vzawe = ir.Var(scope, mk_unique_var('idx_tup'), loc)
        ddjwz__tupp.append(ir.Assign(ir.Expr.build_tuple(rsmf__div, loc),
            pjyo__dtgv, loc))
        ddjwz__tupp.append(ir.Assign(ir.Expr.build_tuple(wcw__miac, loc),
            rysil__vzawe, loc))
        return (pjyo__dtgv, rysil__vzawe), ddjwz__tupp
