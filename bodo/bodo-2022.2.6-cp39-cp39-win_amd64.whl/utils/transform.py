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
    gvagy__vnl = tuple(call_list)
    if gvagy__vnl in no_side_effect_call_tuples:
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
    if len(gvagy__vnl) == 1 and tuple in getattr(gvagy__vnl[0], '__mro__', ()):
        return True
    return False


numba.core.ir_utils.remove_call_handlers.append(remove_hiframes)


def compile_func_single_block(func, args, ret_var, typing_info=None,
    extra_globals=None, infer_types=True, run_untyped_pass=False, flags=
    None, replace_globals=True):
    bdql__ubbo = {'numba': numba, 'np': np, 'bodo': bodo, 'pd': pd, 'math':
        math}
    if extra_globals is not None:
        bdql__ubbo.update(extra_globals)
    if not replace_globals:
        bdql__ubbo = func.__globals__
    loc = ir.Loc('', 0)
    if ret_var:
        loc = ret_var.loc
    if typing_info and infer_types:
        loc = typing_info.curr_loc
        f_ir = compile_to_numba_ir(func, bdql__ubbo, typingctx=typing_info.
            typingctx, targetctx=typing_info.targetctx, arg_typs=tuple(
            typing_info.typemap[fpf__jbp.name] for fpf__jbp in args),
            typemap=typing_info.typemap, calltypes=typing_info.calltypes)
    else:
        f_ir = compile_to_numba_ir(func, bdql__ubbo)
    assert len(f_ir.blocks
        ) == 1, 'only single block functions supported in compile_func_single_block()'
    if run_untyped_pass:
        hgg__jwezu = tuple(typing_info.typemap[fpf__jbp.name] for fpf__jbp in
            args)
        dwwp__uruoo = bodo.transforms.untyped_pass.UntypedPass(f_ir,
            typing_info.typingctx, hgg__jwezu, {}, {}, flags)
        dwwp__uruoo.run()
    avtf__ovdz = f_ir.blocks.popitem()[1]
    replace_arg_nodes(avtf__ovdz, args)
    gdphq__rhl = avtf__ovdz.body[:-2]
    update_locs(gdphq__rhl[len(args):], loc)
    for stmt in gdphq__rhl[:len(args)]:
        stmt.target.loc = loc
    if ret_var is not None:
        ruzsl__mwnq = avtf__ovdz.body[-2]
        assert is_assign(ruzsl__mwnq) and is_expr(ruzsl__mwnq.value, 'cast')
        fiw__yxx = ruzsl__mwnq.value.value
        gdphq__rhl.append(ir.Assign(fiw__yxx, ret_var, loc))
    return gdphq__rhl


def update_locs(node_list, loc):
    for stmt in node_list:
        stmt.loc = loc
        for lfe__mww in stmt.list_vars():
            lfe__mww.loc = loc
        if is_assign(stmt):
            stmt.value.loc = loc


def get_stmt_defs(stmt):
    if is_assign(stmt):
        return set([stmt.target.name])
    if type(stmt) in numba.core.analysis.ir_extension_usedefs:
        kkq__tui = numba.core.analysis.ir_extension_usedefs[type(stmt)]
        yuu__asa, wujt__alspa = kkq__tui(stmt)
        return wujt__alspa
    return set()


def get_const_value(var, func_ir, err_msg, typemap=None, arg_types=None,
    file_info=None):
    if hasattr(var, 'loc'):
        loc = var.loc
    else:
        loc = None
    try:
        jch__wbbtr = get_const_value_inner(func_ir, var, arg_types, typemap,
            file_info=file_info)
        if isinstance(jch__wbbtr, ir.UndefinedType):
            ujubz__mamwq = func_ir.get_definition(var.name).name
            raise BodoError(f"name '{ujubz__mamwq}' is not defined", loc=loc)
    except GuardException as pealo__nqhf:
        raise BodoError(err_msg, loc=loc)
    return jch__wbbtr


def get_const_value_inner(func_ir, var, arg_types=None, typemap=None,
    updated_containers=None, file_info=None, pyobject_to_literal=False,
    literalize_args=True):
    require(isinstance(var, ir.Var))
    oldt__rqqeu = get_definition(func_ir, var)
    oewp__lyhas = None
    if typemap is not None:
        oewp__lyhas = typemap.get(var.name, None)
    if isinstance(oldt__rqqeu, ir.Arg) and arg_types is not None:
        oewp__lyhas = arg_types[oldt__rqqeu.index]
    if updated_containers and var.name in updated_containers:
        raise BodoConstUpdatedError(
            f"variable '{var.name}' is updated inplace using '{updated_containers[var.name]}'"
            )
    if is_literal_type(oewp__lyhas):
        return get_literal_value(oewp__lyhas)
    if isinstance(oldt__rqqeu, (ir.Const, ir.Global, ir.FreeVar)):
        jch__wbbtr = oldt__rqqeu.value
        return jch__wbbtr
    if literalize_args and isinstance(oldt__rqqeu, ir.Arg
        ) and can_literalize_type(oewp__lyhas, pyobject_to_literal):
        raise numba.core.errors.ForceLiteralArg({oldt__rqqeu.index}, loc=
            var.loc, file_infos={oldt__rqqeu.index: file_info} if file_info
             is not None else None)
    if is_expr(oldt__rqqeu, 'binop'):
        if file_info and oldt__rqqeu.fn == operator.add:
            try:
                ztre__uahgq = get_const_value_inner(func_ir, oldt__rqqeu.
                    lhs, arg_types, typemap, updated_containers,
                    literalize_args=False)
                file_info.set_concat(ztre__uahgq, True)
                jja__widt = get_const_value_inner(func_ir, oldt__rqqeu.rhs,
                    arg_types, typemap, updated_containers, file_info)
                return oldt__rqqeu.fn(ztre__uahgq, jja__widt)
            except (GuardException, BodoConstUpdatedError) as pealo__nqhf:
                pass
            try:
                jja__widt = get_const_value_inner(func_ir, oldt__rqqeu.rhs,
                    arg_types, typemap, updated_containers, literalize_args
                    =False)
                file_info.set_concat(jja__widt, False)
                ztre__uahgq = get_const_value_inner(func_ir, oldt__rqqeu.
                    lhs, arg_types, typemap, updated_containers, file_info)
                return oldt__rqqeu.fn(ztre__uahgq, jja__widt)
            except (GuardException, BodoConstUpdatedError) as pealo__nqhf:
                pass
        ztre__uahgq = get_const_value_inner(func_ir, oldt__rqqeu.lhs,
            arg_types, typemap, updated_containers)
        jja__widt = get_const_value_inner(func_ir, oldt__rqqeu.rhs,
            arg_types, typemap, updated_containers)
        return oldt__rqqeu.fn(ztre__uahgq, jja__widt)
    if is_expr(oldt__rqqeu, 'unary'):
        jch__wbbtr = get_const_value_inner(func_ir, oldt__rqqeu.value,
            arg_types, typemap, updated_containers)
        return oldt__rqqeu.fn(jch__wbbtr)
    if is_expr(oldt__rqqeu, 'getattr') and typemap:
        cyu__exyzn = typemap.get(oldt__rqqeu.value.name, None)
        if isinstance(cyu__exyzn, bodo.hiframes.pd_dataframe_ext.DataFrameType
            ) and oldt__rqqeu.attr == 'columns':
            return pd.Index(cyu__exyzn.columns)
        if isinstance(cyu__exyzn, types.SliceType):
            ztafu__wmkjp = get_definition(func_ir, oldt__rqqeu.value)
            require(is_call(ztafu__wmkjp))
            tdxl__rnjfo = find_callname(func_ir, ztafu__wmkjp)
            zhdf__hbyta = False
            if tdxl__rnjfo == ('_normalize_slice', 'numba.cpython.unicode'):
                require(oldt__rqqeu.attr in ('start', 'step'))
                ztafu__wmkjp = get_definition(func_ir, ztafu__wmkjp.args[0])
                zhdf__hbyta = True
            require(find_callname(func_ir, ztafu__wmkjp) == ('slice',
                'builtins'))
            if len(ztafu__wmkjp.args) == 1:
                if oldt__rqqeu.attr == 'start':
                    return 0
                if oldt__rqqeu.attr == 'step':
                    return 1
                require(oldt__rqqeu.attr == 'stop')
                return get_const_value_inner(func_ir, ztafu__wmkjp.args[0],
                    arg_types, typemap, updated_containers)
            if oldt__rqqeu.attr == 'start':
                jch__wbbtr = get_const_value_inner(func_ir, ztafu__wmkjp.
                    args[0], arg_types, typemap, updated_containers)
                if jch__wbbtr is None:
                    jch__wbbtr = 0
                if zhdf__hbyta:
                    require(jch__wbbtr == 0)
                return jch__wbbtr
            if oldt__rqqeu.attr == 'stop':
                assert not zhdf__hbyta
                return get_const_value_inner(func_ir, ztafu__wmkjp.args[1],
                    arg_types, typemap, updated_containers)
            require(oldt__rqqeu.attr == 'step')
            if len(ztafu__wmkjp.args) == 2:
                return 1
            else:
                jch__wbbtr = get_const_value_inner(func_ir, ztafu__wmkjp.
                    args[2], arg_types, typemap, updated_containers)
                if jch__wbbtr is None:
                    jch__wbbtr = 1
                if zhdf__hbyta:
                    require(jch__wbbtr == 1)
                return jch__wbbtr
    if is_expr(oldt__rqqeu, 'getattr'):
        return getattr(get_const_value_inner(func_ir, oldt__rqqeu.value,
            arg_types, typemap, updated_containers), oldt__rqqeu.attr)
    if is_expr(oldt__rqqeu, 'getitem'):
        value = get_const_value_inner(func_ir, oldt__rqqeu.value, arg_types,
            typemap, updated_containers)
        index = get_const_value_inner(func_ir, oldt__rqqeu.index, arg_types,
            typemap, updated_containers)
        return value[index]
    xrnqr__wyv = guard(find_callname, func_ir, oldt__rqqeu, typemap)
    if xrnqr__wyv is not None and len(xrnqr__wyv) == 2 and xrnqr__wyv[0
        ] == 'keys' and isinstance(xrnqr__wyv[1], ir.Var):
        oal__okc = oldt__rqqeu.func
        oldt__rqqeu = get_definition(func_ir, xrnqr__wyv[1])
        iwtok__swy = xrnqr__wyv[1].name
        if updated_containers and iwtok__swy in updated_containers:
            raise BodoConstUpdatedError(
                "variable '{}' is updated inplace using '{}'".format(
                iwtok__swy, updated_containers[iwtok__swy]))
        require(is_expr(oldt__rqqeu, 'build_map'))
        vals = [lfe__mww[0] for lfe__mww in oldt__rqqeu.items]
        ttjhx__ript = guard(get_definition, func_ir, oal__okc)
        assert isinstance(ttjhx__ript, ir.Expr) and ttjhx__ript.attr == 'keys'
        ttjhx__ript.attr = 'copy'
        return [get_const_value_inner(func_ir, lfe__mww, arg_types, typemap,
            updated_containers) for lfe__mww in vals]
    if is_expr(oldt__rqqeu, 'build_map'):
        return {get_const_value_inner(func_ir, lfe__mww[0], arg_types,
            typemap, updated_containers): get_const_value_inner(func_ir,
            lfe__mww[1], arg_types, typemap, updated_containers) for
            lfe__mww in oldt__rqqeu.items}
    if is_expr(oldt__rqqeu, 'build_tuple'):
        return tuple(get_const_value_inner(func_ir, lfe__mww, arg_types,
            typemap, updated_containers) for lfe__mww in oldt__rqqeu.items)
    if is_expr(oldt__rqqeu, 'build_list'):
        return [get_const_value_inner(func_ir, lfe__mww, arg_types, typemap,
            updated_containers) for lfe__mww in oldt__rqqeu.items]
    if is_expr(oldt__rqqeu, 'build_set'):
        return {get_const_value_inner(func_ir, lfe__mww, arg_types, typemap,
            updated_containers) for lfe__mww in oldt__rqqeu.items}
    if xrnqr__wyv == ('list', 'builtins'):
        values = get_const_value_inner(func_ir, oldt__rqqeu.args[0],
            arg_types, typemap, updated_containers)
        if isinstance(values, set):
            values = sorted(values)
        return list(values)
    if xrnqr__wyv == ('set', 'builtins'):
        return set(get_const_value_inner(func_ir, oldt__rqqeu.args[0],
            arg_types, typemap, updated_containers))
    if xrnqr__wyv == ('range', 'builtins') and len(oldt__rqqeu.args) == 1:
        return range(get_const_value_inner(func_ir, oldt__rqqeu.args[0],
            arg_types, typemap, updated_containers))
    if xrnqr__wyv == ('slice', 'builtins'):
        return slice(*tuple(get_const_value_inner(func_ir, lfe__mww,
            arg_types, typemap, updated_containers) for lfe__mww in
            oldt__rqqeu.args))
    if xrnqr__wyv == ('str', 'builtins'):
        return str(get_const_value_inner(func_ir, oldt__rqqeu.args[0],
            arg_types, typemap, updated_containers))
    if xrnqr__wyv == ('bool', 'builtins'):
        return bool(get_const_value_inner(func_ir, oldt__rqqeu.args[0],
            arg_types, typemap, updated_containers))
    if xrnqr__wyv == ('format', 'builtins'):
        fpf__jbp = get_const_value_inner(func_ir, oldt__rqqeu.args[0],
            arg_types, typemap, updated_containers)
        ogl__csg = get_const_value_inner(func_ir, oldt__rqqeu.args[1],
            arg_types, typemap, updated_containers) if len(oldt__rqqeu.args
            ) > 1 else ''
        return format(fpf__jbp, ogl__csg)
    if xrnqr__wyv in (('init_binary_str_index',
        'bodo.hiframes.pd_index_ext'), ('init_numeric_index',
        'bodo.hiframes.pd_index_ext'), ('init_categorical_index',
        'bodo.hiframes.pd_index_ext'), ('init_datetime_index',
        'bodo.hiframes.pd_index_ext'), ('init_timedelta_index',
        'bodo.hiframes.pd_index_ext'), ('init_heter_index',
        'bodo.hiframes.pd_index_ext')):
        return pd.Index(get_const_value_inner(func_ir, oldt__rqqeu.args[0],
            arg_types, typemap, updated_containers))
    if xrnqr__wyv == ('str_arr_from_sequence', 'bodo.libs.str_arr_ext'):
        return np.array(get_const_value_inner(func_ir, oldt__rqqeu.args[0],
            arg_types, typemap, updated_containers))
    if xrnqr__wyv == ('init_range_index', 'bodo.hiframes.pd_index_ext'):
        return pd.RangeIndex(get_const_value_inner(func_ir, oldt__rqqeu.
            args[0], arg_types, typemap, updated_containers),
            get_const_value_inner(func_ir, oldt__rqqeu.args[1], arg_types,
            typemap, updated_containers), get_const_value_inner(func_ir,
            oldt__rqqeu.args[2], arg_types, typemap, updated_containers))
    if xrnqr__wyv == ('len', 'builtins') and typemap and isinstance(typemap
        .get(oldt__rqqeu.args[0].name, None), types.BaseTuple):
        return len(typemap[oldt__rqqeu.args[0].name])
    if xrnqr__wyv == ('len', 'builtins'):
        gzmw__htraa = guard(get_definition, func_ir, oldt__rqqeu.args[0])
        if isinstance(gzmw__htraa, ir.Expr) and gzmw__htraa.op in (
            'build_tuple', 'build_list', 'build_set', 'build_map'):
            return len(gzmw__htraa.items)
        return len(get_const_value_inner(func_ir, oldt__rqqeu.args[0],
            arg_types, typemap, updated_containers))
    if xrnqr__wyv == ('CategoricalDtype', 'pandas'):
        kws = dict(oldt__rqqeu.kws)
        ssin__rhm = get_call_expr_arg('CategoricalDtype', oldt__rqqeu.args,
            kws, 0, 'categories', '')
        xgyof__dliqx = get_call_expr_arg('CategoricalDtype', oldt__rqqeu.
            args, kws, 1, 'ordered', False)
        if xgyof__dliqx is not False:
            xgyof__dliqx = get_const_value_inner(func_ir, xgyof__dliqx,
                arg_types, typemap, updated_containers)
        if ssin__rhm == '':
            ssin__rhm = None
        else:
            ssin__rhm = get_const_value_inner(func_ir, ssin__rhm, arg_types,
                typemap, updated_containers)
        return pd.CategoricalDtype(ssin__rhm, xgyof__dliqx)
    if xrnqr__wyv == ('dtype', 'numpy'):
        return np.dtype(get_const_value_inner(func_ir, oldt__rqqeu.args[0],
            arg_types, typemap, updated_containers))
    if xrnqr__wyv is not None and len(xrnqr__wyv) == 2 and xrnqr__wyv[1
        ] == 'pandas' and xrnqr__wyv[0] in ('Int8Dtype', 'Int16Dtype',
        'Int32Dtype', 'Int64Dtype', 'UInt8Dtype', 'UInt16Dtype',
        'UInt32Dtype', 'UInt64Dtype'):
        return getattr(pd, xrnqr__wyv[0])()
    if xrnqr__wyv is not None and len(xrnqr__wyv) == 2 and isinstance(
        xrnqr__wyv[1], ir.Var):
        jch__wbbtr = get_const_value_inner(func_ir, xrnqr__wyv[1],
            arg_types, typemap, updated_containers)
        args = [get_const_value_inner(func_ir, lfe__mww, arg_types, typemap,
            updated_containers) for lfe__mww in oldt__rqqeu.args]
        kws = {qlfc__swtf[0]: get_const_value_inner(func_ir, qlfc__swtf[1],
            arg_types, typemap, updated_containers) for qlfc__swtf in
            oldt__rqqeu.kws}
        return getattr(jch__wbbtr, xrnqr__wyv[0])(*args, **kws)
    if xrnqr__wyv is not None and len(xrnqr__wyv) == 2 and xrnqr__wyv[1
        ] == 'bodo' and xrnqr__wyv[0] in bodo_types_with_params:
        args = tuple(get_const_value_inner(func_ir, lfe__mww, arg_types,
            typemap, updated_containers) for lfe__mww in oldt__rqqeu.args)
        kwargs = {ujubz__mamwq: get_const_value_inner(func_ir, lfe__mww,
            arg_types, typemap, updated_containers) for ujubz__mamwq,
            lfe__mww in dict(oldt__rqqeu.kws).items()}
        return getattr(bodo, xrnqr__wyv[0])(*args, **kwargs)
    if is_call(oldt__rqqeu) and typemap and isinstance(typemap.get(
        oldt__rqqeu.func.name, None), types.Dispatcher):
        py_func = typemap[oldt__rqqeu.func.name].dispatcher.py_func
        require(oldt__rqqeu.vararg is None)
        args = tuple(get_const_value_inner(func_ir, lfe__mww, arg_types,
            typemap, updated_containers) for lfe__mww in oldt__rqqeu.args)
        kwargs = {ujubz__mamwq: get_const_value_inner(func_ir, lfe__mww,
            arg_types, typemap, updated_containers) for ujubz__mamwq,
            lfe__mww in dict(oldt__rqqeu.kws).items()}
        arg_types = tuple(bodo.typeof(lfe__mww) for lfe__mww in args)
        kw_types = {whx__ssfp: bodo.typeof(lfe__mww) for whx__ssfp,
            lfe__mww in kwargs.items()}
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
    f_ir, typemap, tueth__dhfoh, tueth__dhfoh = (bodo.compiler.
        get_func_type_info(py_func, arg_types, kw_types))
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
                    hdvvh__ewdco = guard(get_definition, f_ir, rhs.func)
                    if isinstance(hdvvh__ewdco, ir.Const) and isinstance(
                        hdvvh__ewdco.value, numba.core.dispatcher.
                        ObjModeLiftedWith):
                        return False
                    hfu__dxqgl = guard(find_callname, f_ir, rhs)
                    if hfu__dxqgl is None:
                        return False
                    func_name, mnjw__cyim = hfu__dxqgl
                    if mnjw__cyim == 'pandas' and func_name.startswith('read_'
                        ):
                        return False
                    if hfu__dxqgl in (('fromfile', 'numpy'), ('file_read',
                        'bodo.io.np_io')):
                        return False
                    if hfu__dxqgl == ('File', 'h5py'):
                        return False
                    if isinstance(mnjw__cyim, ir.Var):
                        oewp__lyhas = typemap[mnjw__cyim.name]
                        if isinstance(oewp__lyhas, (DataFrameType, SeriesType)
                            ) and func_name in ('to_csv', 'to_excel',
                            'to_json', 'to_sql', 'to_pickle', 'to_parquet',
                            'info'):
                            return False
                        if isinstance(oewp__lyhas, types.Array
                            ) and func_name == 'tofile':
                            return False
                        if isinstance(oewp__lyhas, bodo.LoggingLoggerType):
                            return False
                        if str(oewp__lyhas).startswith('Mpl'):
                            return False
                        if (func_name in container_update_method_names and
                            isinstance(guard(get_definition, f_ir,
                            mnjw__cyim), ir.Arg)):
                            return False
                    if mnjw__cyim in ('numpy.random', 'time', 'logging',
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
        avget__lgbat = func.literal_value.code
        xqpp__bmnlm = {'np': np, 'pd': pd, 'numba': numba, 'bodo': bodo}
        if hasattr(func.literal_value, 'globals'):
            xqpp__bmnlm = func.literal_value.globals
        f_ir = numba.core.ir_utils.get_ir_of_code(xqpp__bmnlm, avget__lgbat)
        fix_struct_return(f_ir)
        typemap, wgqnd__lrxjj, nkzk__etkzq, tueth__dhfoh = (numba.core.
            typed_passes.type_inference_stage(typing_context,
            target_context, f_ir, arg_types, None))
    elif isinstance(func, bodo.utils.typing.FunctionLiteral):
        py_func = func.literal_value
        f_ir, typemap, nkzk__etkzq, wgqnd__lrxjj = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    elif isinstance(func, CPUDispatcher):
        py_func = func.py_func
        f_ir, typemap, nkzk__etkzq, wgqnd__lrxjj = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    else:
        if not isinstance(func, types.Dispatcher):
            if isinstance(func, types.Function):
                raise BodoError(
                    f'Bodo does not support built-in functions yet, {func}')
            else:
                raise BodoError(f'Function type expected, not {func}')
        py_func = func.dispatcher.py_func
        f_ir, typemap, nkzk__etkzq, wgqnd__lrxjj = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    if is_udf and isinstance(wgqnd__lrxjj, types.DictType):
        hqff__udg = guard(get_struct_keynames, f_ir, typemap)
        if hqff__udg is not None:
            wgqnd__lrxjj = StructType((wgqnd__lrxjj.value_type,) * len(
                hqff__udg), hqff__udg)
    if is_udf and isinstance(wgqnd__lrxjj, (SeriesType,
        HeterogeneousSeriesType)):
        xzeng__fwlhl = numba.core.registry.cpu_target.typing_context
        vypim__hwu = numba.core.registry.cpu_target.target_context
        yfb__rovot = bodo.transforms.series_pass.SeriesPass(f_ir,
            xzeng__fwlhl, vypim__hwu, typemap, nkzk__etkzq, {})
        yfb__rovot.run()
        yfb__rovot.run()
        yfb__rovot.run()
        aev__pma = compute_cfg_from_blocks(f_ir.blocks)
        rmn__lusru = [guard(_get_const_series_info, f_ir.blocks[rzlo__yzc],
            f_ir, typemap) for rzlo__yzc in aev__pma.exit_points() if
            isinstance(f_ir.blocks[rzlo__yzc].body[-1], ir.Return)]
        if None in rmn__lusru or len(pd.Series(rmn__lusru).unique()) != 1:
            wgqnd__lrxjj.const_info = None
        else:
            wgqnd__lrxjj.const_info = rmn__lusru[0]
    return wgqnd__lrxjj


def _get_const_series_info(block, f_ir, typemap):
    from bodo.hiframes.pd_series_ext import HeterogeneousSeriesType
    assert isinstance(block.body[-1], ir.Return)
    kqtf__vvj = block.body[-1].value
    qdcep__avf = get_definition(f_ir, kqtf__vvj)
    require(is_expr(qdcep__avf, 'cast'))
    qdcep__avf = get_definition(f_ir, qdcep__avf.value)
    require(is_call(qdcep__avf) and find_callname(f_ir, qdcep__avf) == (
        'init_series', 'bodo.hiframes.pd_series_ext'))
    jhlm__rwm = qdcep__avf.args[1]
    ekl__aeqcg = tuple(get_const_value_inner(f_ir, jhlm__rwm, typemap=typemap))
    if isinstance(typemap[kqtf__vvj.name], HeterogeneousSeriesType):
        return len(typemap[kqtf__vvj.name].data), ekl__aeqcg
    odsed__ccjc = qdcep__avf.args[0]
    vnmix__vpnq = get_definition(f_ir, odsed__ccjc)
    func_name, qydu__hgz = find_callname(f_ir, vnmix__vpnq)
    if is_call(vnmix__vpnq) and bodo.utils.utils.is_alloc_callname(func_name,
        qydu__hgz):
        fdjlk__czyno = vnmix__vpnq.args[0]
        zuh__vwle = get_const_value_inner(f_ir, fdjlk__czyno, typemap=typemap)
        return zuh__vwle, ekl__aeqcg
    if is_call(vnmix__vpnq) and find_callname(f_ir, vnmix__vpnq) in [(
        'asarray', 'numpy'), ('str_arr_from_sequence', 'bodo.libs.str_arr_ext')
        ]:
        odsed__ccjc = vnmix__vpnq.args[0]
        vnmix__vpnq = get_definition(f_ir, odsed__ccjc)
    require(is_expr(vnmix__vpnq, 'build_tuple') or is_expr(vnmix__vpnq,
        'build_list'))
    return len(vnmix__vpnq.items), ekl__aeqcg


def extract_keyvals_from_struct_map(f_ir, build_map, loc, scope, typemap=None):
    cfykg__ecy = []
    pivub__zvla = []
    values = []
    for whx__ssfp, lfe__mww in build_map.items:
        hdhs__jtg = find_const(f_ir, whx__ssfp)
        require(isinstance(hdhs__jtg, str))
        pivub__zvla.append(hdhs__jtg)
        cfykg__ecy.append(whx__ssfp)
        values.append(lfe__mww)
    oog__fsa = ir.Var(scope, mk_unique_var('val_tup'), loc)
    rrf__cuu = ir.Assign(ir.Expr.build_tuple(values, loc), oog__fsa, loc)
    f_ir._definitions[oog__fsa.name] = [rrf__cuu.value]
    akrsh__rcq = ir.Var(scope, mk_unique_var('key_tup'), loc)
    aotz__rbodl = ir.Assign(ir.Expr.build_tuple(cfykg__ecy, loc),
        akrsh__rcq, loc)
    f_ir._definitions[akrsh__rcq.name] = [aotz__rbodl.value]
    if typemap is not None:
        typemap[oog__fsa.name] = types.Tuple([typemap[lfe__mww.name] for
            lfe__mww in values])
        typemap[akrsh__rcq.name] = types.Tuple([typemap[lfe__mww.name] for
            lfe__mww in cfykg__ecy])
    return pivub__zvla, oog__fsa, rrf__cuu, akrsh__rcq, aotz__rbodl


def _replace_const_map_return(f_ir, block, label):
    require(isinstance(block.body[-1], ir.Return))
    hjal__kfep = block.body[-1].value
    xlu__zka = guard(get_definition, f_ir, hjal__kfep)
    require(is_expr(xlu__zka, 'cast'))
    qdcep__avf = guard(get_definition, f_ir, xlu__zka.value)
    require(is_expr(qdcep__avf, 'build_map'))
    require(len(qdcep__avf.items) > 0)
    loc = block.loc
    scope = block.scope
    pivub__zvla, oog__fsa, rrf__cuu, akrsh__rcq, aotz__rbodl = (
        extract_keyvals_from_struct_map(f_ir, qdcep__avf, loc, scope))
    iifqg__yzh = ir.Var(scope, mk_unique_var('conv_call'), loc)
    rnh__lyg = ir.Assign(ir.Global('struct_if_heter_dict', bodo.utils.
        conversion.struct_if_heter_dict, loc), iifqg__yzh, loc)
    f_ir._definitions[iifqg__yzh.name] = [rnh__lyg.value]
    jeker__mcvla = ir.Var(scope, mk_unique_var('struct_val'), loc)
    mpdg__potf = ir.Assign(ir.Expr.call(iifqg__yzh, [oog__fsa, akrsh__rcq],
        {}, loc), jeker__mcvla, loc)
    f_ir._definitions[jeker__mcvla.name] = [mpdg__potf.value]
    xlu__zka.value = jeker__mcvla
    qdcep__avf.items = [(whx__ssfp, whx__ssfp) for whx__ssfp, tueth__dhfoh in
        qdcep__avf.items]
    block.body = block.body[:-2] + [rrf__cuu, aotz__rbodl, rnh__lyg, mpdg__potf
        ] + block.body[-2:]
    return tuple(pivub__zvla)


def get_struct_keynames(f_ir, typemap):
    aev__pma = compute_cfg_from_blocks(f_ir.blocks)
    nps__hwq = list(aev__pma.exit_points())[0]
    block = f_ir.blocks[nps__hwq]
    require(isinstance(block.body[-1], ir.Return))
    hjal__kfep = block.body[-1].value
    xlu__zka = guard(get_definition, f_ir, hjal__kfep)
    require(is_expr(xlu__zka, 'cast'))
    qdcep__avf = guard(get_definition, f_ir, xlu__zka.value)
    require(is_call(qdcep__avf) and find_callname(f_ir, qdcep__avf) == (
        'struct_if_heter_dict', 'bodo.utils.conversion'))
    return get_overload_const_list(typemap[qdcep__avf.args[1].name])


def fix_struct_return(f_ir):
    bwl__lxy = None
    aev__pma = compute_cfg_from_blocks(f_ir.blocks)
    for nps__hwq in aev__pma.exit_points():
        bwl__lxy = guard(_replace_const_map_return, f_ir, f_ir.blocks[
            nps__hwq], nps__hwq)
    return bwl__lxy


def update_node_list_definitions(node_list, func_ir):
    loc = ir.Loc('', 0)
    xix__naenx = ir.Block(ir.Scope(None, loc), loc)
    xix__naenx.body = node_list
    build_definitions({(0): xix__naenx}, func_ir._definitions)
    return


NESTED_TUP_SENTINEL = '$BODO_NESTED_TUP'


def gen_const_val_str(c):
    if isinstance(c, tuple):
        return "'{}{}', ".format(NESTED_TUP_SENTINEL, len(c)) + ', '.join(
            gen_const_val_str(lfe__mww) for lfe__mww in c)
    if isinstance(c, str):
        return "'{}'".format(c)
    if isinstance(c, (pd.Timestamp, pd.Timedelta, float)):
        return "'{}'".format(c)
    return str(c)


def gen_const_tup(vals):
    wzuz__aty = ', '.join(gen_const_val_str(c) for c in vals)
    return '({}{})'.format(wzuz__aty, ',' if len(vals) == 1 else '')


def get_const_tup_vals(c_typ):
    vals = get_overload_const_list(c_typ)
    return _get_original_nested_tups(vals)


def _get_original_nested_tups(vals):
    for hal__lyv in range(len(vals) - 1, -1, -1):
        lfe__mww = vals[hal__lyv]
        if isinstance(lfe__mww, str) and lfe__mww.startswith(
            NESTED_TUP_SENTINEL):
            yzar__plebs = int(lfe__mww[len(NESTED_TUP_SENTINEL):])
            return _get_original_nested_tups(tuple(vals[:hal__lyv]) + (
                tuple(vals[hal__lyv + 1:hal__lyv + yzar__plebs + 1]),) +
                tuple(vals[hal__lyv + yzar__plebs + 1:]))
    return tuple(vals)


def get_call_expr_arg(f_name, args, kws, arg_no, arg_name, default=None,
    err_msg=None, use_default=False):
    fpf__jbp = None
    if len(args) > arg_no and arg_no >= 0:
        fpf__jbp = args[arg_no]
        if arg_name in kws:
            err_msg = (
                f"{f_name}() got multiple values for argument '{arg_name}'")
            raise BodoError(err_msg)
    elif arg_name in kws:
        fpf__jbp = kws[arg_name]
    if fpf__jbp is None:
        if use_default or default is not None:
            return default
        if err_msg is None:
            err_msg = "{} requires '{}' argument".format(f_name, arg_name)
        raise BodoError(err_msg)
    return fpf__jbp


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
    bdql__ubbo = {'numba': numba, 'np': np, 'bodo': bodo, 'pd': pd}
    if extra_globals is not None:
        bdql__ubbo.update(extra_globals)
    func.__globals__.update(bdql__ubbo)
    if pysig is not None:
        pre_nodes = [] if pre_nodes is None else pre_nodes
        scope = next(iter(pass_info.func_ir.blocks.values())).scope
        loc = scope.loc

        def normal_handler(index, param, default):
            return default

        def default_handler(index, param, default):
            pymed__havly = ir.Var(scope, mk_unique_var('defaults'), loc)
            try:
                pass_info.typemap[pymed__havly.name] = types.literal(default)
            except:
                pass_info.typemap[pymed__havly.name] = numba.typeof(default)
            lpa__wgt = ir.Assign(ir.Const(default, loc), pymed__havly, loc)
            pre_nodes.append(lpa__wgt)
            return pymed__havly
        args = numba.core.typing.fold_arguments(pysig, args, kws,
            normal_handler, default_handler, normal_handler)
    hgg__jwezu = tuple(pass_info.typemap[lfe__mww.name] for lfe__mww in args)
    if const:
        kbv__ziwty = []
        for hal__lyv, fpf__jbp in enumerate(args):
            jch__wbbtr = guard(find_const, pass_info.func_ir, fpf__jbp)
            if jch__wbbtr:
                kbv__ziwty.append(types.literal(jch__wbbtr))
            else:
                kbv__ziwty.append(hgg__jwezu[hal__lyv])
        hgg__jwezu = tuple(kbv__ziwty)
    return ReplaceFunc(func, hgg__jwezu, args, bdql__ubbo,
        inline_bodo_calls, run_full_pipeline, pre_nodes)


def is_var_size_item_array_type(t):
    assert is_array_typ(t, False)
    return t == string_array_type or isinstance(t, ArrayItemArrayType
        ) or isinstance(t, StructArrayType) and any(
        is_var_size_item_array_type(qeyjy__jmt) for qeyjy__jmt in t.data)


def gen_init_varsize_alloc_sizes(t):
    if t == string_array_type:
        trn__hea = 'num_chars_{}'.format(ir_utils.next_label())
        return f'  {trn__hea} = 0\n', (trn__hea,)
    if isinstance(t, ArrayItemArrayType):
        aaon__khyx, ceecp__iea = gen_init_varsize_alloc_sizes(t.dtype)
        trn__hea = 'num_items_{}'.format(ir_utils.next_label())
        return f'  {trn__hea} = 0\n' + aaon__khyx, (trn__hea,) + ceecp__iea
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
        return 1 + sum(get_type_alloc_counts(qeyjy__jmt.dtype) for
            qeyjy__jmt in t.data)
    if isinstance(t, ArrayItemArrayType) or t == string_array_type:
        return 1 + get_type_alloc_counts(t.dtype)
    if isinstance(t, MapArrayType):
        return get_type_alloc_counts(t.key_arr_type) + get_type_alloc_counts(t
            .value_arr_type)
    if bodo.utils.utils.is_array_typ(t, False) or t == bodo.string_type:
        return 1
    if isinstance(t, StructType):
        return sum(get_type_alloc_counts(qeyjy__jmt) for qeyjy__jmt in t.data)
    if isinstance(t, types.BaseTuple):
        return sum(get_type_alloc_counts(qeyjy__jmt) for qeyjy__jmt in t.types)
    return 0


def find_udf_str_name(obj_dtype, func_name, typing_context, caller_name):
    ubf__hbd = typing_context.resolve_getattr(obj_dtype, func_name)
    if ubf__hbd is None:
        onpir__rfw = types.misc.Module(np)
        try:
            ubf__hbd = typing_context.resolve_getattr(onpir__rfw, func_name)
        except AttributeError as pealo__nqhf:
            ubf__hbd = None
        if ubf__hbd is None:
            raise BodoError(
                f"{caller_name}(): No Pandas method or Numpy function found with the name '{func_name}'."
                )
    return ubf__hbd


def get_udf_str_return_type(obj_dtype, func_name, typing_context,
    caller_name, axis=None):
    ubf__hbd = find_udf_str_name(obj_dtype, func_name, typing_context,
        caller_name)
    if isinstance(ubf__hbd, types.BoundFunction):
        if axis is not None:
            tvgh__evrx = ubf__hbd.get_call_type(typing_context, (), {'axis':
                axis})
        else:
            tvgh__evrx = ubf__hbd.get_call_type(typing_context, (), {})
        return tvgh__evrx.return_type
    else:
        if bodo.utils.typing.is_numpy_ufunc(ubf__hbd):
            tvgh__evrx = ubf__hbd.get_call_type(typing_context, (obj_dtype,
                ), {})
            return tvgh__evrx.return_type
        raise BodoError(
            f"{caller_name}(): Only Pandas methods and np.ufunc are supported as string literals. '{func_name}' not supported."
            )


def get_pandas_method_str_impl(obj_dtype, func_name, typing_context,
    caller_name, axis=None):
    ubf__hbd = find_udf_str_name(obj_dtype, func_name, typing_context,
        caller_name)
    if isinstance(ubf__hbd, types.BoundFunction):
        dhefe__uoum = ubf__hbd.template
        if axis is not None:
            return dhefe__uoum._overload_func(obj_dtype, axis=axis)
        else:
            return dhefe__uoum._overload_func(obj_dtype)
    return None


def dict_to_const_keys_var_values_lists(dict_var, func_ir, arg_types,
    typemap, updated_containers, require_const_map, label):
    require(isinstance(dict_var, ir.Var))
    xaq__vfhc = get_definition(func_ir, dict_var)
    require(isinstance(xaq__vfhc, ir.Expr))
    require(xaq__vfhc.op == 'build_map')
    qevz__xhjuf = xaq__vfhc.items
    cfykg__ecy = []
    values = []
    ait__vfzad = False
    for hal__lyv in range(len(qevz__xhjuf)):
        inxy__bmv, value = qevz__xhjuf[hal__lyv]
        try:
            pyw__pvz = get_const_value_inner(func_ir, inxy__bmv, arg_types,
                typemap, updated_containers)
            cfykg__ecy.append(pyw__pvz)
            values.append(value)
        except GuardException as pealo__nqhf:
            require_const_map[inxy__bmv] = label
            ait__vfzad = True
    if ait__vfzad:
        raise GuardException
    return cfykg__ecy, values


def _get_const_keys_from_dict(args, func_ir, build_map, err_msg, loc):
    try:
        cfykg__ecy = tuple(get_const_value_inner(func_ir, t[0], args) for t in
            build_map.items)
    except GuardException as pealo__nqhf:
        raise BodoError(err_msg, loc)
    if not all(isinstance(c, (str, int)) for c in cfykg__ecy):
        raise BodoError(err_msg, loc)
    return cfykg__ecy


def _convert_const_key_dict(args, func_ir, build_map, err_msg, scope, loc,
    output_sentinel_tuple=False):
    cfykg__ecy = _get_const_keys_from_dict(args, func_ir, build_map,
        err_msg, loc)
    fpg__ilvi = []
    rrl__ltx = [bodo.transforms.typing_pass._create_const_var(whx__ssfp,
        'dict_key', scope, loc, fpg__ilvi) for whx__ssfp in cfykg__ecy]
    snwn__kgc = [t[1] for t in build_map.items]
    if output_sentinel_tuple:
        zmiyt__jyeuq = ir.Var(scope, mk_unique_var('sentinel'), loc)
        fdq__gvs = ir.Var(scope, mk_unique_var('dict_tup'), loc)
        fpg__ilvi.append(ir.Assign(ir.Const('__bodo_tup', loc),
            zmiyt__jyeuq, loc))
        xmfm__gxoe = [zmiyt__jyeuq] + rrl__ltx + snwn__kgc
        fpg__ilvi.append(ir.Assign(ir.Expr.build_tuple(xmfm__gxoe, loc),
            fdq__gvs, loc))
        return (fdq__gvs,), fpg__ilvi
    else:
        rjnt__pgi = ir.Var(scope, mk_unique_var('values_tup'), loc)
        tapl__vypcm = ir.Var(scope, mk_unique_var('idx_tup'), loc)
        fpg__ilvi.append(ir.Assign(ir.Expr.build_tuple(snwn__kgc, loc),
            rjnt__pgi, loc))
        fpg__ilvi.append(ir.Assign(ir.Expr.build_tuple(rrl__ltx, loc),
            tapl__vypcm, loc))
        return (rjnt__pgi, tapl__vypcm), fpg__ilvi
