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
    vaf__krykp = tuple(call_list)
    if vaf__krykp in no_side_effect_call_tuples:
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
    if len(vaf__krykp) == 1 and tuple in getattr(vaf__krykp[0], '__mro__', ()):
        return True
    return False


numba.core.ir_utils.remove_call_handlers.append(remove_hiframes)


def compile_func_single_block(func, args, ret_var, typing_info=None,
    extra_globals=None, infer_types=True, run_untyped_pass=False, flags=
    None, replace_globals=True):
    pkwh__qufht = {'numba': numba, 'np': np, 'bodo': bodo, 'pd': pd, 'math':
        math}
    if extra_globals is not None:
        pkwh__qufht.update(extra_globals)
    if not replace_globals:
        pkwh__qufht = func.__globals__
    loc = ir.Loc('', 0)
    if ret_var:
        loc = ret_var.loc
    if typing_info and infer_types:
        loc = typing_info.curr_loc
        f_ir = compile_to_numba_ir(func, pkwh__qufht, typingctx=typing_info
            .typingctx, targetctx=typing_info.targetctx, arg_typs=tuple(
            typing_info.typemap[crn__icffd.name] for crn__icffd in args),
            typemap=typing_info.typemap, calltypes=typing_info.calltypes)
    else:
        f_ir = compile_to_numba_ir(func, pkwh__qufht)
    assert len(f_ir.blocks
        ) == 1, 'only single block functions supported in compile_func_single_block()'
    if run_untyped_pass:
        rzqap__exfaf = tuple(typing_info.typemap[crn__icffd.name] for
            crn__icffd in args)
        ukwmx__wlcx = bodo.transforms.untyped_pass.UntypedPass(f_ir,
            typing_info.typingctx, rzqap__exfaf, {}, {}, flags)
        ukwmx__wlcx.run()
    yjiw__mmtzv = f_ir.blocks.popitem()[1]
    replace_arg_nodes(yjiw__mmtzv, args)
    zrmgn__beqwh = yjiw__mmtzv.body[:-2]
    update_locs(zrmgn__beqwh[len(args):], loc)
    for stmt in zrmgn__beqwh[:len(args)]:
        stmt.target.loc = loc
    if ret_var is not None:
        lsx__guod = yjiw__mmtzv.body[-2]
        assert is_assign(lsx__guod) and is_expr(lsx__guod.value, 'cast')
        qui__phfc = lsx__guod.value.value
        zrmgn__beqwh.append(ir.Assign(qui__phfc, ret_var, loc))
    return zrmgn__beqwh


def update_locs(node_list, loc):
    for stmt in node_list:
        stmt.loc = loc
        for jyn__gohb in stmt.list_vars():
            jyn__gohb.loc = loc
        if is_assign(stmt):
            stmt.value.loc = loc


def get_stmt_defs(stmt):
    if is_assign(stmt):
        return set([stmt.target.name])
    if type(stmt) in numba.core.analysis.ir_extension_usedefs:
        unn__cfnk = numba.core.analysis.ir_extension_usedefs[type(stmt)]
        hryo__pae, fmj__zyim = unn__cfnk(stmt)
        return fmj__zyim
    return set()


def get_const_value(var, func_ir, err_msg, typemap=None, arg_types=None,
    file_info=None):
    if hasattr(var, 'loc'):
        loc = var.loc
    else:
        loc = None
    try:
        zaoc__yjtog = get_const_value_inner(func_ir, var, arg_types,
            typemap, file_info=file_info)
        if isinstance(zaoc__yjtog, ir.UndefinedType):
            gjgx__gxk = func_ir.get_definition(var.name).name
            raise BodoError(f"name '{gjgx__gxk}' is not defined", loc=loc)
    except GuardException as nvb__mao:
        raise BodoError(err_msg, loc=loc)
    return zaoc__yjtog


def get_const_value_inner(func_ir, var, arg_types=None, typemap=None,
    updated_containers=None, file_info=None, pyobject_to_literal=False,
    literalize_args=True):
    require(isinstance(var, ir.Var))
    yzx__jmv = get_definition(func_ir, var)
    zycys__jvk = None
    if typemap is not None:
        zycys__jvk = typemap.get(var.name, None)
    if isinstance(yzx__jmv, ir.Arg) and arg_types is not None:
        zycys__jvk = arg_types[yzx__jmv.index]
    if updated_containers and var.name in updated_containers:
        raise BodoConstUpdatedError(
            f"variable '{var.name}' is updated inplace using '{updated_containers[var.name]}'"
            )
    if is_literal_type(zycys__jvk):
        return get_literal_value(zycys__jvk)
    if isinstance(yzx__jmv, (ir.Const, ir.Global, ir.FreeVar)):
        zaoc__yjtog = yzx__jmv.value
        return zaoc__yjtog
    if literalize_args and isinstance(yzx__jmv, ir.Arg
        ) and can_literalize_type(zycys__jvk, pyobject_to_literal):
        raise numba.core.errors.ForceLiteralArg({yzx__jmv.index}, loc=var.
            loc, file_infos={yzx__jmv.index: file_info} if file_info is not
            None else None)
    if is_expr(yzx__jmv, 'binop'):
        if file_info and yzx__jmv.fn == operator.add:
            try:
                fqtjc__wrqd = get_const_value_inner(func_ir, yzx__jmv.lhs,
                    arg_types, typemap, updated_containers, literalize_args
                    =False)
                file_info.set_concat(fqtjc__wrqd, True)
                jlln__zashw = get_const_value_inner(func_ir, yzx__jmv.rhs,
                    arg_types, typemap, updated_containers, file_info)
                return yzx__jmv.fn(fqtjc__wrqd, jlln__zashw)
            except (GuardException, BodoConstUpdatedError) as nvb__mao:
                pass
            try:
                jlln__zashw = get_const_value_inner(func_ir, yzx__jmv.rhs,
                    arg_types, typemap, updated_containers, literalize_args
                    =False)
                file_info.set_concat(jlln__zashw, False)
                fqtjc__wrqd = get_const_value_inner(func_ir, yzx__jmv.lhs,
                    arg_types, typemap, updated_containers, file_info)
                return yzx__jmv.fn(fqtjc__wrqd, jlln__zashw)
            except (GuardException, BodoConstUpdatedError) as nvb__mao:
                pass
        fqtjc__wrqd = get_const_value_inner(func_ir, yzx__jmv.lhs,
            arg_types, typemap, updated_containers)
        jlln__zashw = get_const_value_inner(func_ir, yzx__jmv.rhs,
            arg_types, typemap, updated_containers)
        return yzx__jmv.fn(fqtjc__wrqd, jlln__zashw)
    if is_expr(yzx__jmv, 'unary'):
        zaoc__yjtog = get_const_value_inner(func_ir, yzx__jmv.value,
            arg_types, typemap, updated_containers)
        return yzx__jmv.fn(zaoc__yjtog)
    if is_expr(yzx__jmv, 'getattr') and typemap:
        ult__jcexq = typemap.get(yzx__jmv.value.name, None)
        if isinstance(ult__jcexq, bodo.hiframes.pd_dataframe_ext.DataFrameType
            ) and yzx__jmv.attr == 'columns':
            return pd.Index(ult__jcexq.columns)
        if isinstance(ult__jcexq, types.SliceType):
            kweok__kmj = get_definition(func_ir, yzx__jmv.value)
            require(is_call(kweok__kmj))
            cjl__dtc = find_callname(func_ir, kweok__kmj)
            xiiee__hsk = False
            if cjl__dtc == ('_normalize_slice', 'numba.cpython.unicode'):
                require(yzx__jmv.attr in ('start', 'step'))
                kweok__kmj = get_definition(func_ir, kweok__kmj.args[0])
                xiiee__hsk = True
            require(find_callname(func_ir, kweok__kmj) == ('slice', 'builtins')
                )
            if len(kweok__kmj.args) == 1:
                if yzx__jmv.attr == 'start':
                    return 0
                if yzx__jmv.attr == 'step':
                    return 1
                require(yzx__jmv.attr == 'stop')
                return get_const_value_inner(func_ir, kweok__kmj.args[0],
                    arg_types, typemap, updated_containers)
            if yzx__jmv.attr == 'start':
                zaoc__yjtog = get_const_value_inner(func_ir, kweok__kmj.
                    args[0], arg_types, typemap, updated_containers)
                if zaoc__yjtog is None:
                    zaoc__yjtog = 0
                if xiiee__hsk:
                    require(zaoc__yjtog == 0)
                return zaoc__yjtog
            if yzx__jmv.attr == 'stop':
                assert not xiiee__hsk
                return get_const_value_inner(func_ir, kweok__kmj.args[1],
                    arg_types, typemap, updated_containers)
            require(yzx__jmv.attr == 'step')
            if len(kweok__kmj.args) == 2:
                return 1
            else:
                zaoc__yjtog = get_const_value_inner(func_ir, kweok__kmj.
                    args[2], arg_types, typemap, updated_containers)
                if zaoc__yjtog is None:
                    zaoc__yjtog = 1
                if xiiee__hsk:
                    require(zaoc__yjtog == 1)
                return zaoc__yjtog
    if is_expr(yzx__jmv, 'getattr'):
        return getattr(get_const_value_inner(func_ir, yzx__jmv.value,
            arg_types, typemap, updated_containers), yzx__jmv.attr)
    if is_expr(yzx__jmv, 'getitem'):
        value = get_const_value_inner(func_ir, yzx__jmv.value, arg_types,
            typemap, updated_containers)
        index = get_const_value_inner(func_ir, yzx__jmv.index, arg_types,
            typemap, updated_containers)
        return value[index]
    brn__nrhoh = guard(find_callname, func_ir, yzx__jmv, typemap)
    if brn__nrhoh is not None and len(brn__nrhoh) == 2 and brn__nrhoh[0
        ] == 'keys' and isinstance(brn__nrhoh[1], ir.Var):
        kweq__qsezr = yzx__jmv.func
        yzx__jmv = get_definition(func_ir, brn__nrhoh[1])
        kdqz__dqv = brn__nrhoh[1].name
        if updated_containers and kdqz__dqv in updated_containers:
            raise BodoConstUpdatedError(
                "variable '{}' is updated inplace using '{}'".format(
                kdqz__dqv, updated_containers[kdqz__dqv]))
        require(is_expr(yzx__jmv, 'build_map'))
        vals = [jyn__gohb[0] for jyn__gohb in yzx__jmv.items]
        nqy__xbood = guard(get_definition, func_ir, kweq__qsezr)
        assert isinstance(nqy__xbood, ir.Expr) and nqy__xbood.attr == 'keys'
        nqy__xbood.attr = 'copy'
        return [get_const_value_inner(func_ir, jyn__gohb, arg_types,
            typemap, updated_containers) for jyn__gohb in vals]
    if is_expr(yzx__jmv, 'build_map'):
        return {get_const_value_inner(func_ir, jyn__gohb[0], arg_types,
            typemap, updated_containers): get_const_value_inner(func_ir,
            jyn__gohb[1], arg_types, typemap, updated_containers) for
            jyn__gohb in yzx__jmv.items}
    if is_expr(yzx__jmv, 'build_tuple'):
        return tuple(get_const_value_inner(func_ir, jyn__gohb, arg_types,
            typemap, updated_containers) for jyn__gohb in yzx__jmv.items)
    if is_expr(yzx__jmv, 'build_list'):
        return [get_const_value_inner(func_ir, jyn__gohb, arg_types,
            typemap, updated_containers) for jyn__gohb in yzx__jmv.items]
    if is_expr(yzx__jmv, 'build_set'):
        return {get_const_value_inner(func_ir, jyn__gohb, arg_types,
            typemap, updated_containers) for jyn__gohb in yzx__jmv.items}
    if brn__nrhoh == ('list', 'builtins'):
        values = get_const_value_inner(func_ir, yzx__jmv.args[0], arg_types,
            typemap, updated_containers)
        if isinstance(values, set):
            values = sorted(values)
        return list(values)
    if brn__nrhoh == ('set', 'builtins'):
        return set(get_const_value_inner(func_ir, yzx__jmv.args[0],
            arg_types, typemap, updated_containers))
    if brn__nrhoh == ('range', 'builtins') and len(yzx__jmv.args) == 1:
        return range(get_const_value_inner(func_ir, yzx__jmv.args[0],
            arg_types, typemap, updated_containers))
    if brn__nrhoh == ('slice', 'builtins'):
        return slice(*tuple(get_const_value_inner(func_ir, jyn__gohb,
            arg_types, typemap, updated_containers) for jyn__gohb in
            yzx__jmv.args))
    if brn__nrhoh == ('str', 'builtins'):
        return str(get_const_value_inner(func_ir, yzx__jmv.args[0],
            arg_types, typemap, updated_containers))
    if brn__nrhoh == ('bool', 'builtins'):
        return bool(get_const_value_inner(func_ir, yzx__jmv.args[0],
            arg_types, typemap, updated_containers))
    if brn__nrhoh == ('format', 'builtins'):
        crn__icffd = get_const_value_inner(func_ir, yzx__jmv.args[0],
            arg_types, typemap, updated_containers)
        zdew__pasl = get_const_value_inner(func_ir, yzx__jmv.args[1],
            arg_types, typemap, updated_containers) if len(yzx__jmv.args
            ) > 1 else ''
        return format(crn__icffd, zdew__pasl)
    if brn__nrhoh in (('init_binary_str_index',
        'bodo.hiframes.pd_index_ext'), ('init_numeric_index',
        'bodo.hiframes.pd_index_ext'), ('init_categorical_index',
        'bodo.hiframes.pd_index_ext'), ('init_datetime_index',
        'bodo.hiframes.pd_index_ext'), ('init_timedelta_index',
        'bodo.hiframes.pd_index_ext'), ('init_heter_index',
        'bodo.hiframes.pd_index_ext')):
        return pd.Index(get_const_value_inner(func_ir, yzx__jmv.args[0],
            arg_types, typemap, updated_containers))
    if brn__nrhoh == ('str_arr_from_sequence', 'bodo.libs.str_arr_ext'):
        return np.array(get_const_value_inner(func_ir, yzx__jmv.args[0],
            arg_types, typemap, updated_containers))
    if brn__nrhoh == ('init_range_index', 'bodo.hiframes.pd_index_ext'):
        return pd.RangeIndex(get_const_value_inner(func_ir, yzx__jmv.args[0
            ], arg_types, typemap, updated_containers),
            get_const_value_inner(func_ir, yzx__jmv.args[1], arg_types,
            typemap, updated_containers), get_const_value_inner(func_ir,
            yzx__jmv.args[2], arg_types, typemap, updated_containers))
    if brn__nrhoh == ('len', 'builtins') and typemap and isinstance(typemap
        .get(yzx__jmv.args[0].name, None), types.BaseTuple):
        return len(typemap[yzx__jmv.args[0].name])
    if brn__nrhoh == ('len', 'builtins'):
        tlrzf__ltojm = guard(get_definition, func_ir, yzx__jmv.args[0])
        if isinstance(tlrzf__ltojm, ir.Expr) and tlrzf__ltojm.op in (
            'build_tuple', 'build_list', 'build_set', 'build_map'):
            return len(tlrzf__ltojm.items)
        return len(get_const_value_inner(func_ir, yzx__jmv.args[0],
            arg_types, typemap, updated_containers))
    if brn__nrhoh == ('CategoricalDtype', 'pandas'):
        kws = dict(yzx__jmv.kws)
        jffnw__cal = get_call_expr_arg('CategoricalDtype', yzx__jmv.args,
            kws, 0, 'categories', '')
        acav__flwhp = get_call_expr_arg('CategoricalDtype', yzx__jmv.args,
            kws, 1, 'ordered', False)
        if acav__flwhp is not False:
            acav__flwhp = get_const_value_inner(func_ir, acav__flwhp,
                arg_types, typemap, updated_containers)
        if jffnw__cal == '':
            jffnw__cal = None
        else:
            jffnw__cal = get_const_value_inner(func_ir, jffnw__cal,
                arg_types, typemap, updated_containers)
        return pd.CategoricalDtype(jffnw__cal, acav__flwhp)
    if brn__nrhoh == ('dtype', 'numpy'):
        return np.dtype(get_const_value_inner(func_ir, yzx__jmv.args[0],
            arg_types, typemap, updated_containers))
    if brn__nrhoh is not None and len(brn__nrhoh) == 2 and brn__nrhoh[1
        ] == 'pandas' and brn__nrhoh[0] in ('Int8Dtype', 'Int16Dtype',
        'Int32Dtype', 'Int64Dtype', 'UInt8Dtype', 'UInt16Dtype',
        'UInt32Dtype', 'UInt64Dtype'):
        return getattr(pd, brn__nrhoh[0])()
    if brn__nrhoh is not None and len(brn__nrhoh) == 2 and isinstance(
        brn__nrhoh[1], ir.Var):
        zaoc__yjtog = get_const_value_inner(func_ir, brn__nrhoh[1],
            arg_types, typemap, updated_containers)
        args = [get_const_value_inner(func_ir, jyn__gohb, arg_types,
            typemap, updated_containers) for jyn__gohb in yzx__jmv.args]
        kws = {coya__cyxvd[0]: get_const_value_inner(func_ir, coya__cyxvd[1
            ], arg_types, typemap, updated_containers) for coya__cyxvd in
            yzx__jmv.kws}
        return getattr(zaoc__yjtog, brn__nrhoh[0])(*args, **kws)
    if brn__nrhoh is not None and len(brn__nrhoh) == 2 and brn__nrhoh[1
        ] == 'bodo' and brn__nrhoh[0] in bodo_types_with_params:
        args = tuple(get_const_value_inner(func_ir, jyn__gohb, arg_types,
            typemap, updated_containers) for jyn__gohb in yzx__jmv.args)
        kwargs = {gjgx__gxk: get_const_value_inner(func_ir, jyn__gohb,
            arg_types, typemap, updated_containers) for gjgx__gxk,
            jyn__gohb in dict(yzx__jmv.kws).items()}
        return getattr(bodo, brn__nrhoh[0])(*args, **kwargs)
    if is_call(yzx__jmv) and typemap and isinstance(typemap.get(yzx__jmv.
        func.name, None), types.Dispatcher):
        py_func = typemap[yzx__jmv.func.name].dispatcher.py_func
        require(yzx__jmv.vararg is None)
        args = tuple(get_const_value_inner(func_ir, jyn__gohb, arg_types,
            typemap, updated_containers) for jyn__gohb in yzx__jmv.args)
        kwargs = {gjgx__gxk: get_const_value_inner(func_ir, jyn__gohb,
            arg_types, typemap, updated_containers) for gjgx__gxk,
            jyn__gohb in dict(yzx__jmv.kws).items()}
        arg_types = tuple(bodo.typeof(jyn__gohb) for jyn__gohb in args)
        kw_types = {suych__yzkz: bodo.typeof(jyn__gohb) for suych__yzkz,
            jyn__gohb in kwargs.items()}
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
    f_ir, typemap, kgxot__wgc, kgxot__wgc = bodo.compiler.get_func_type_info(
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
                    nlqj__rknq = guard(get_definition, f_ir, rhs.func)
                    if isinstance(nlqj__rknq, ir.Const) and isinstance(
                        nlqj__rknq.value, numba.core.dispatcher.
                        ObjModeLiftedWith):
                        return False
                    gani__fyif = guard(find_callname, f_ir, rhs)
                    if gani__fyif is None:
                        return False
                    func_name, azl__odu = gani__fyif
                    if azl__odu == 'pandas' and func_name.startswith('read_'):
                        return False
                    if gani__fyif in (('fromfile', 'numpy'), ('file_read',
                        'bodo.io.np_io')):
                        return False
                    if gani__fyif == ('File', 'h5py'):
                        return False
                    if isinstance(azl__odu, ir.Var):
                        zycys__jvk = typemap[azl__odu.name]
                        if isinstance(zycys__jvk, (DataFrameType, SeriesType)
                            ) and func_name in ('to_csv', 'to_excel',
                            'to_json', 'to_sql', 'to_pickle', 'to_parquet',
                            'info'):
                            return False
                        if isinstance(zycys__jvk, types.Array
                            ) and func_name == 'tofile':
                            return False
                        if isinstance(zycys__jvk, bodo.LoggingLoggerType):
                            return False
                        if str(zycys__jvk).startswith('Mpl'):
                            return False
                        if (func_name in container_update_method_names and
                            isinstance(guard(get_definition, f_ir, azl__odu
                            ), ir.Arg)):
                            return False
                    if azl__odu in ('numpy.random', 'time', 'logging',
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
        xcen__vvxnd = func.literal_value.code
        hmh__irak = {'np': np, 'pd': pd, 'numba': numba, 'bodo': bodo}
        if hasattr(func.literal_value, 'globals'):
            hmh__irak = func.literal_value.globals
        f_ir = numba.core.ir_utils.get_ir_of_code(hmh__irak, xcen__vvxnd)
        fix_struct_return(f_ir)
        typemap, hfunm__hdzr, cyy__ujuy, kgxot__wgc = (numba.core.
            typed_passes.type_inference_stage(typing_context,
            target_context, f_ir, arg_types, None))
    elif isinstance(func, bodo.utils.typing.FunctionLiteral):
        py_func = func.literal_value
        f_ir, typemap, cyy__ujuy, hfunm__hdzr = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    elif isinstance(func, CPUDispatcher):
        py_func = func.py_func
        f_ir, typemap, cyy__ujuy, hfunm__hdzr = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    else:
        if not isinstance(func, types.Dispatcher):
            if isinstance(func, types.Function):
                raise BodoError(
                    f'Bodo does not support built-in functions yet, {func}')
            else:
                raise BodoError(f'Function type expected, not {func}')
        py_func = func.dispatcher.py_func
        f_ir, typemap, cyy__ujuy, hfunm__hdzr = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    if is_udf and isinstance(hfunm__hdzr, types.DictType):
        qnc__taozv = guard(get_struct_keynames, f_ir, typemap)
        if qnc__taozv is not None:
            hfunm__hdzr = StructType((hfunm__hdzr.value_type,) * len(
                qnc__taozv), qnc__taozv)
    if is_udf and isinstance(hfunm__hdzr, (SeriesType, HeterogeneousSeriesType)
        ):
        czid__pcrya = numba.core.registry.cpu_target.typing_context
        nohbs__otw = numba.core.registry.cpu_target.target_context
        hbtg__lxh = bodo.transforms.series_pass.SeriesPass(f_ir,
            czid__pcrya, nohbs__otw, typemap, cyy__ujuy, {})
        hbtg__lxh.run()
        hbtg__lxh.run()
        hbtg__lxh.run()
        nux__nplay = compute_cfg_from_blocks(f_ir.blocks)
        abzco__ilaaf = [guard(_get_const_series_info, f_ir.blocks[
            cjyy__fdfzs], f_ir, typemap) for cjyy__fdfzs in nux__nplay.
            exit_points() if isinstance(f_ir.blocks[cjyy__fdfzs].body[-1],
            ir.Return)]
        if None in abzco__ilaaf or len(pd.Series(abzco__ilaaf).unique()) != 1:
            hfunm__hdzr.const_info = None
        else:
            hfunm__hdzr.const_info = abzco__ilaaf[0]
    return hfunm__hdzr


def _get_const_series_info(block, f_ir, typemap):
    from bodo.hiframes.pd_series_ext import HeterogeneousSeriesType
    assert isinstance(block.body[-1], ir.Return)
    xzxz__ble = block.body[-1].value
    rhh__grc = get_definition(f_ir, xzxz__ble)
    require(is_expr(rhh__grc, 'cast'))
    rhh__grc = get_definition(f_ir, rhh__grc.value)
    require(is_call(rhh__grc) and find_callname(f_ir, rhh__grc) == (
        'init_series', 'bodo.hiframes.pd_series_ext'))
    waj__tgt = rhh__grc.args[1]
    slr__sqx = tuple(get_const_value_inner(f_ir, waj__tgt, typemap=typemap))
    if isinstance(typemap[xzxz__ble.name], HeterogeneousSeriesType):
        return len(typemap[xzxz__ble.name].data), slr__sqx
    ahoxk__nmk = rhh__grc.args[0]
    bsq__erapx = get_definition(f_ir, ahoxk__nmk)
    func_name, kapx__thn = find_callname(f_ir, bsq__erapx)
    if is_call(bsq__erapx) and bodo.utils.utils.is_alloc_callname(func_name,
        kapx__thn):
        hnvb__gqbiv = bsq__erapx.args[0]
        sqo__iep = get_const_value_inner(f_ir, hnvb__gqbiv, typemap=typemap)
        return sqo__iep, slr__sqx
    if is_call(bsq__erapx) and find_callname(f_ir, bsq__erapx) in [(
        'asarray', 'numpy'), ('str_arr_from_sequence', 'bodo.libs.str_arr_ext')
        ]:
        ahoxk__nmk = bsq__erapx.args[0]
        bsq__erapx = get_definition(f_ir, ahoxk__nmk)
    require(is_expr(bsq__erapx, 'build_tuple') or is_expr(bsq__erapx,
        'build_list'))
    return len(bsq__erapx.items), slr__sqx


def extract_keyvals_from_struct_map(f_ir, build_map, loc, scope, typemap=None):
    arig__dzqr = []
    cqd__iokb = []
    values = []
    for suych__yzkz, jyn__gohb in build_map.items:
        tdbk__cxg = find_const(f_ir, suych__yzkz)
        require(isinstance(tdbk__cxg, str))
        cqd__iokb.append(tdbk__cxg)
        arig__dzqr.append(suych__yzkz)
        values.append(jyn__gohb)
    xcao__jaupo = ir.Var(scope, mk_unique_var('val_tup'), loc)
    mzl__ogqi = ir.Assign(ir.Expr.build_tuple(values, loc), xcao__jaupo, loc)
    f_ir._definitions[xcao__jaupo.name] = [mzl__ogqi.value]
    sxkcp__okifn = ir.Var(scope, mk_unique_var('key_tup'), loc)
    inf__ajjri = ir.Assign(ir.Expr.build_tuple(arig__dzqr, loc),
        sxkcp__okifn, loc)
    f_ir._definitions[sxkcp__okifn.name] = [inf__ajjri.value]
    if typemap is not None:
        typemap[xcao__jaupo.name] = types.Tuple([typemap[jyn__gohb.name] for
            jyn__gohb in values])
        typemap[sxkcp__okifn.name] = types.Tuple([typemap[jyn__gohb.name] for
            jyn__gohb in arig__dzqr])
    return cqd__iokb, xcao__jaupo, mzl__ogqi, sxkcp__okifn, inf__ajjri


def _replace_const_map_return(f_ir, block, label):
    require(isinstance(block.body[-1], ir.Return))
    gbsu__usjzn = block.body[-1].value
    crat__tafr = guard(get_definition, f_ir, gbsu__usjzn)
    require(is_expr(crat__tafr, 'cast'))
    rhh__grc = guard(get_definition, f_ir, crat__tafr.value)
    require(is_expr(rhh__grc, 'build_map'))
    require(len(rhh__grc.items) > 0)
    loc = block.loc
    scope = block.scope
    cqd__iokb, xcao__jaupo, mzl__ogqi, sxkcp__okifn, inf__ajjri = (
        extract_keyvals_from_struct_map(f_ir, rhh__grc, loc, scope))
    ywb__awh = ir.Var(scope, mk_unique_var('conv_call'), loc)
    uirfn__ismmo = ir.Assign(ir.Global('struct_if_heter_dict', bodo.utils.
        conversion.struct_if_heter_dict, loc), ywb__awh, loc)
    f_ir._definitions[ywb__awh.name] = [uirfn__ismmo.value]
    tlzfp__xpcp = ir.Var(scope, mk_unique_var('struct_val'), loc)
    jkmpy__cofvy = ir.Assign(ir.Expr.call(ywb__awh, [xcao__jaupo,
        sxkcp__okifn], {}, loc), tlzfp__xpcp, loc)
    f_ir._definitions[tlzfp__xpcp.name] = [jkmpy__cofvy.value]
    crat__tafr.value = tlzfp__xpcp
    rhh__grc.items = [(suych__yzkz, suych__yzkz) for suych__yzkz,
        kgxot__wgc in rhh__grc.items]
    block.body = block.body[:-2] + [mzl__ogqi, inf__ajjri, uirfn__ismmo,
        jkmpy__cofvy] + block.body[-2:]
    return tuple(cqd__iokb)


def get_struct_keynames(f_ir, typemap):
    nux__nplay = compute_cfg_from_blocks(f_ir.blocks)
    gwmvk__veys = list(nux__nplay.exit_points())[0]
    block = f_ir.blocks[gwmvk__veys]
    require(isinstance(block.body[-1], ir.Return))
    gbsu__usjzn = block.body[-1].value
    crat__tafr = guard(get_definition, f_ir, gbsu__usjzn)
    require(is_expr(crat__tafr, 'cast'))
    rhh__grc = guard(get_definition, f_ir, crat__tafr.value)
    require(is_call(rhh__grc) and find_callname(f_ir, rhh__grc) == (
        'struct_if_heter_dict', 'bodo.utils.conversion'))
    return get_overload_const_list(typemap[rhh__grc.args[1].name])


def fix_struct_return(f_ir):
    bwxm__mgwit = None
    nux__nplay = compute_cfg_from_blocks(f_ir.blocks)
    for gwmvk__veys in nux__nplay.exit_points():
        bwxm__mgwit = guard(_replace_const_map_return, f_ir, f_ir.blocks[
            gwmvk__veys], gwmvk__veys)
    return bwxm__mgwit


def update_node_list_definitions(node_list, func_ir):
    loc = ir.Loc('', 0)
    jrgxl__ffhvw = ir.Block(ir.Scope(None, loc), loc)
    jrgxl__ffhvw.body = node_list
    build_definitions({(0): jrgxl__ffhvw}, func_ir._definitions)
    return


NESTED_TUP_SENTINEL = '$BODO_NESTED_TUP'


def gen_const_val_str(c):
    if isinstance(c, tuple):
        return "'{}{}', ".format(NESTED_TUP_SENTINEL, len(c)) + ', '.join(
            gen_const_val_str(jyn__gohb) for jyn__gohb in c)
    if isinstance(c, str):
        return "'{}'".format(c)
    if isinstance(c, (pd.Timestamp, pd.Timedelta, float)):
        return "'{}'".format(c)
    return str(c)


def gen_const_tup(vals):
    aqlj__faht = ', '.join(gen_const_val_str(c) for c in vals)
    return '({}{})'.format(aqlj__faht, ',' if len(vals) == 1 else '')


def get_const_tup_vals(c_typ):
    vals = get_overload_const_list(c_typ)
    return _get_original_nested_tups(vals)


def _get_original_nested_tups(vals):
    for pztc__biyrm in range(len(vals) - 1, -1, -1):
        jyn__gohb = vals[pztc__biyrm]
        if isinstance(jyn__gohb, str) and jyn__gohb.startswith(
            NESTED_TUP_SENTINEL):
            hus__chd = int(jyn__gohb[len(NESTED_TUP_SENTINEL):])
            return _get_original_nested_tups(tuple(vals[:pztc__biyrm]) + (
                tuple(vals[pztc__biyrm + 1:pztc__biyrm + hus__chd + 1]),) +
                tuple(vals[pztc__biyrm + hus__chd + 1:]))
    return tuple(vals)


def get_call_expr_arg(f_name, args, kws, arg_no, arg_name, default=None,
    err_msg=None, use_default=False):
    crn__icffd = None
    if len(args) > arg_no and arg_no >= 0:
        crn__icffd = args[arg_no]
        if arg_name in kws:
            err_msg = (
                f"{f_name}() got multiple values for argument '{arg_name}'")
            raise BodoError(err_msg)
    elif arg_name in kws:
        crn__icffd = kws[arg_name]
    if crn__icffd is None:
        if use_default or default is not None:
            return default
        if err_msg is None:
            err_msg = "{} requires '{}' argument".format(f_name, arg_name)
        raise BodoError(err_msg)
    return crn__icffd


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
    pkwh__qufht = {'numba': numba, 'np': np, 'bodo': bodo, 'pd': pd}
    if extra_globals is not None:
        pkwh__qufht.update(extra_globals)
    func.__globals__.update(pkwh__qufht)
    if pysig is not None:
        pre_nodes = [] if pre_nodes is None else pre_nodes
        scope = next(iter(pass_info.func_ir.blocks.values())).scope
        loc = scope.loc

        def normal_handler(index, param, default):
            return default

        def default_handler(index, param, default):
            pqdkm__nur = ir.Var(scope, mk_unique_var('defaults'), loc)
            try:
                pass_info.typemap[pqdkm__nur.name] = types.literal(default)
            except:
                pass_info.typemap[pqdkm__nur.name] = numba.typeof(default)
            kel__rew = ir.Assign(ir.Const(default, loc), pqdkm__nur, loc)
            pre_nodes.append(kel__rew)
            return pqdkm__nur
        args = numba.core.typing.fold_arguments(pysig, args, kws,
            normal_handler, default_handler, normal_handler)
    rzqap__exfaf = tuple(pass_info.typemap[jyn__gohb.name] for jyn__gohb in
        args)
    if const:
        ugecw__istb = []
        for pztc__biyrm, crn__icffd in enumerate(args):
            zaoc__yjtog = guard(find_const, pass_info.func_ir, crn__icffd)
            if zaoc__yjtog:
                ugecw__istb.append(types.literal(zaoc__yjtog))
            else:
                ugecw__istb.append(rzqap__exfaf[pztc__biyrm])
        rzqap__exfaf = tuple(ugecw__istb)
    return ReplaceFunc(func, rzqap__exfaf, args, pkwh__qufht,
        inline_bodo_calls, run_full_pipeline, pre_nodes)


def is_var_size_item_array_type(t):
    assert is_array_typ(t, False)
    return t == string_array_type or isinstance(t, ArrayItemArrayType
        ) or isinstance(t, StructArrayType) and any(
        is_var_size_item_array_type(kkula__dlwm) for kkula__dlwm in t.data)


def gen_init_varsize_alloc_sizes(t):
    if t == string_array_type:
        hau__ixkr = 'num_chars_{}'.format(ir_utils.next_label())
        return f'  {hau__ixkr} = 0\n', (hau__ixkr,)
    if isinstance(t, ArrayItemArrayType):
        derzh__imkj, lia__qqnjs = gen_init_varsize_alloc_sizes(t.dtype)
        hau__ixkr = 'num_items_{}'.format(ir_utils.next_label())
        return f'  {hau__ixkr} = 0\n' + derzh__imkj, (hau__ixkr,) + lia__qqnjs
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
        return 1 + sum(get_type_alloc_counts(kkula__dlwm.dtype) for
            kkula__dlwm in t.data)
    if isinstance(t, ArrayItemArrayType) or t == string_array_type:
        return 1 + get_type_alloc_counts(t.dtype)
    if isinstance(t, MapArrayType):
        return get_type_alloc_counts(t.key_arr_type) + get_type_alloc_counts(t
            .value_arr_type)
    if bodo.utils.utils.is_array_typ(t, False) or t == bodo.string_type:
        return 1
    if isinstance(t, StructType):
        return sum(get_type_alloc_counts(kkula__dlwm) for kkula__dlwm in t.data
            )
    if isinstance(t, types.BaseTuple):
        return sum(get_type_alloc_counts(kkula__dlwm) for kkula__dlwm in t.
            types)
    return 0


def find_udf_str_name(obj_dtype, func_name, typing_context, caller_name):
    nec__iel = typing_context.resolve_getattr(obj_dtype, func_name)
    if nec__iel is None:
        wwr__sgbw = types.misc.Module(np)
        try:
            nec__iel = typing_context.resolve_getattr(wwr__sgbw, func_name)
        except AttributeError as nvb__mao:
            nec__iel = None
        if nec__iel is None:
            raise BodoError(
                f"{caller_name}(): No Pandas method or Numpy function found with the name '{func_name}'."
                )
    return nec__iel


def get_udf_str_return_type(obj_dtype, func_name, typing_context,
    caller_name, axis=None):
    nec__iel = find_udf_str_name(obj_dtype, func_name, typing_context,
        caller_name)
    if isinstance(nec__iel, types.BoundFunction):
        if axis is not None:
            gvqdi__emakk = nec__iel.get_call_type(typing_context, (), {
                'axis': axis})
        else:
            gvqdi__emakk = nec__iel.get_call_type(typing_context, (), {})
        return gvqdi__emakk.return_type
    else:
        if bodo.utils.typing.is_numpy_ufunc(nec__iel):
            gvqdi__emakk = nec__iel.get_call_type(typing_context, (
                obj_dtype,), {})
            return gvqdi__emakk.return_type
        raise BodoError(
            f"{caller_name}(): Only Pandas methods and np.ufunc are supported as string literals. '{func_name}' not supported."
            )


def get_pandas_method_str_impl(obj_dtype, func_name, typing_context,
    caller_name, axis=None):
    nec__iel = find_udf_str_name(obj_dtype, func_name, typing_context,
        caller_name)
    if isinstance(nec__iel, types.BoundFunction):
        dqyp__zxpx = nec__iel.template
        if axis is not None:
            return dqyp__zxpx._overload_func(obj_dtype, axis=axis)
        else:
            return dqyp__zxpx._overload_func(obj_dtype)
    return None


def dict_to_const_keys_var_values_lists(dict_var, func_ir, arg_types,
    typemap, updated_containers, require_const_map, label):
    require(isinstance(dict_var, ir.Var))
    nkyl__qjhuk = get_definition(func_ir, dict_var)
    require(isinstance(nkyl__qjhuk, ir.Expr))
    require(nkyl__qjhuk.op == 'build_map')
    jtqn__ssnf = nkyl__qjhuk.items
    arig__dzqr = []
    values = []
    kffy__awjj = False
    for pztc__biyrm in range(len(jtqn__ssnf)):
        mqafr__yvcq, value = jtqn__ssnf[pztc__biyrm]
        try:
            vglb__yfi = get_const_value_inner(func_ir, mqafr__yvcq,
                arg_types, typemap, updated_containers)
            arig__dzqr.append(vglb__yfi)
            values.append(value)
        except GuardException as nvb__mao:
            require_const_map[mqafr__yvcq] = label
            kffy__awjj = True
    if kffy__awjj:
        raise GuardException
    return arig__dzqr, values


def _get_const_keys_from_dict(args, func_ir, build_map, err_msg, loc):
    try:
        arig__dzqr = tuple(get_const_value_inner(func_ir, t[0], args) for t in
            build_map.items)
    except GuardException as nvb__mao:
        raise BodoError(err_msg, loc)
    if not all(isinstance(c, (str, int)) for c in arig__dzqr):
        raise BodoError(err_msg, loc)
    return arig__dzqr


def _convert_const_key_dict(args, func_ir, build_map, err_msg, scope, loc,
    output_sentinel_tuple=False):
    arig__dzqr = _get_const_keys_from_dict(args, func_ir, build_map,
        err_msg, loc)
    ewr__zrzh = []
    yafu__irmql = [bodo.transforms.typing_pass._create_const_var(
        suych__yzkz, 'dict_key', scope, loc, ewr__zrzh) for suych__yzkz in
        arig__dzqr]
    tglma__mmzkb = [t[1] for t in build_map.items]
    if output_sentinel_tuple:
        tbk__zdl = ir.Var(scope, mk_unique_var('sentinel'), loc)
        cklay__pxqo = ir.Var(scope, mk_unique_var('dict_tup'), loc)
        ewr__zrzh.append(ir.Assign(ir.Const('__bodo_tup', loc), tbk__zdl, loc))
        bpgo__eoc = [tbk__zdl] + yafu__irmql + tglma__mmzkb
        ewr__zrzh.append(ir.Assign(ir.Expr.build_tuple(bpgo__eoc, loc),
            cklay__pxqo, loc))
        return (cklay__pxqo,), ewr__zrzh
    else:
        itcv__dxmco = ir.Var(scope, mk_unique_var('values_tup'), loc)
        irz__xwbrk = ir.Var(scope, mk_unique_var('idx_tup'), loc)
        ewr__zrzh.append(ir.Assign(ir.Expr.build_tuple(tglma__mmzkb, loc),
            itcv__dxmco, loc))
        ewr__zrzh.append(ir.Assign(ir.Expr.build_tuple(yafu__irmql, loc),
            irz__xwbrk, loc))
        return (itcv__dxmco, irz__xwbrk), ewr__zrzh
