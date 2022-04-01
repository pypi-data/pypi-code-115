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
    dnx__cquq = tuple(call_list)
    if dnx__cquq in no_side_effect_call_tuples:
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
    if len(dnx__cquq) == 1 and tuple in getattr(dnx__cquq[0], '__mro__', ()):
        return True
    return False


numba.core.ir_utils.remove_call_handlers.append(remove_hiframes)


def compile_func_single_block(func, args, ret_var, typing_info=None,
    extra_globals=None, infer_types=True, run_untyped_pass=False, flags=
    None, replace_globals=True):
    fhp__psu = {'numba': numba, 'np': np, 'bodo': bodo, 'pd': pd, 'math': math}
    if extra_globals is not None:
        fhp__psu.update(extra_globals)
    if not replace_globals:
        fhp__psu = func.__globals__
    loc = ir.Loc('', 0)
    if ret_var:
        loc = ret_var.loc
    if typing_info and infer_types:
        loc = typing_info.curr_loc
        f_ir = compile_to_numba_ir(func, fhp__psu, typingctx=typing_info.
            typingctx, targetctx=typing_info.targetctx, arg_typs=tuple(
            typing_info.typemap[mzev__owmbl.name] for mzev__owmbl in args),
            typemap=typing_info.typemap, calltypes=typing_info.calltypes)
    else:
        f_ir = compile_to_numba_ir(func, fhp__psu)
    assert len(f_ir.blocks
        ) == 1, 'only single block functions supported in compile_func_single_block()'
    if run_untyped_pass:
        ozhby__licq = tuple(typing_info.typemap[mzev__owmbl.name] for
            mzev__owmbl in args)
        dkr__qnoi = bodo.transforms.untyped_pass.UntypedPass(f_ir,
            typing_info.typingctx, ozhby__licq, {}, {}, flags)
        dkr__qnoi.run()
    rrjr__cuy = f_ir.blocks.popitem()[1]
    replace_arg_nodes(rrjr__cuy, args)
    daex__ryyx = rrjr__cuy.body[:-2]
    update_locs(daex__ryyx[len(args):], loc)
    for stmt in daex__ryyx[:len(args)]:
        stmt.target.loc = loc
    if ret_var is not None:
        lgo__zjr = rrjr__cuy.body[-2]
        assert is_assign(lgo__zjr) and is_expr(lgo__zjr.value, 'cast')
        rvm__rahjm = lgo__zjr.value.value
        daex__ryyx.append(ir.Assign(rvm__rahjm, ret_var, loc))
    return daex__ryyx


def update_locs(node_list, loc):
    for stmt in node_list:
        stmt.loc = loc
        for kgtv__sdzpm in stmt.list_vars():
            kgtv__sdzpm.loc = loc
        if is_assign(stmt):
            stmt.value.loc = loc


def get_stmt_defs(stmt):
    if is_assign(stmt):
        return set([stmt.target.name])
    if type(stmt) in numba.core.analysis.ir_extension_usedefs:
        ssn__gwd = numba.core.analysis.ir_extension_usedefs[type(stmt)]
        niy__szrmj, uxqoc__auz = ssn__gwd(stmt)
        return uxqoc__auz
    return set()


def get_const_value(var, func_ir, err_msg, typemap=None, arg_types=None,
    file_info=None):
    if hasattr(var, 'loc'):
        loc = var.loc
    else:
        loc = None
    try:
        eydlz__ogf = get_const_value_inner(func_ir, var, arg_types, typemap,
            file_info=file_info)
        if isinstance(eydlz__ogf, ir.UndefinedType):
            wmr__xljpt = func_ir.get_definition(var.name).name
            raise BodoError(f"name '{wmr__xljpt}' is not defined", loc=loc)
    except GuardException as sji__lrlog:
        raise BodoError(err_msg, loc=loc)
    return eydlz__ogf


def get_const_value_inner(func_ir, var, arg_types=None, typemap=None,
    updated_containers=None, file_info=None, pyobject_to_literal=False,
    literalize_args=True):
    require(isinstance(var, ir.Var))
    nte__dbqbn = get_definition(func_ir, var)
    hwezx__mry = None
    if typemap is not None:
        hwezx__mry = typemap.get(var.name, None)
    if isinstance(nte__dbqbn, ir.Arg) and arg_types is not None:
        hwezx__mry = arg_types[nte__dbqbn.index]
    if updated_containers and var.name in updated_containers:
        raise BodoConstUpdatedError(
            f"variable '{var.name}' is updated inplace using '{updated_containers[var.name]}'"
            )
    if is_literal_type(hwezx__mry):
        return get_literal_value(hwezx__mry)
    if isinstance(nte__dbqbn, (ir.Const, ir.Global, ir.FreeVar)):
        eydlz__ogf = nte__dbqbn.value
        return eydlz__ogf
    if literalize_args and isinstance(nte__dbqbn, ir.Arg
        ) and can_literalize_type(hwezx__mry, pyobject_to_literal):
        raise numba.core.errors.ForceLiteralArg({nte__dbqbn.index}, loc=var
            .loc, file_infos={nte__dbqbn.index: file_info} if file_info is not
            None else None)
    if is_expr(nte__dbqbn, 'binop'):
        if file_info and nte__dbqbn.fn == operator.add:
            try:
                lnl__cgizw = get_const_value_inner(func_ir, nte__dbqbn.lhs,
                    arg_types, typemap, updated_containers, literalize_args
                    =False)
                file_info.set_concat(lnl__cgizw, True)
                lynki__icwi = get_const_value_inner(func_ir, nte__dbqbn.rhs,
                    arg_types, typemap, updated_containers, file_info)
                return nte__dbqbn.fn(lnl__cgizw, lynki__icwi)
            except (GuardException, BodoConstUpdatedError) as sji__lrlog:
                pass
            try:
                lynki__icwi = get_const_value_inner(func_ir, nte__dbqbn.rhs,
                    arg_types, typemap, updated_containers, literalize_args
                    =False)
                file_info.set_concat(lynki__icwi, False)
                lnl__cgizw = get_const_value_inner(func_ir, nte__dbqbn.lhs,
                    arg_types, typemap, updated_containers, file_info)
                return nte__dbqbn.fn(lnl__cgizw, lynki__icwi)
            except (GuardException, BodoConstUpdatedError) as sji__lrlog:
                pass
        lnl__cgizw = get_const_value_inner(func_ir, nte__dbqbn.lhs,
            arg_types, typemap, updated_containers)
        lynki__icwi = get_const_value_inner(func_ir, nte__dbqbn.rhs,
            arg_types, typemap, updated_containers)
        return nte__dbqbn.fn(lnl__cgizw, lynki__icwi)
    if is_expr(nte__dbqbn, 'unary'):
        eydlz__ogf = get_const_value_inner(func_ir, nte__dbqbn.value,
            arg_types, typemap, updated_containers)
        return nte__dbqbn.fn(eydlz__ogf)
    if is_expr(nte__dbqbn, 'getattr') and typemap:
        isr__tpbq = typemap.get(nte__dbqbn.value.name, None)
        if isinstance(isr__tpbq, bodo.hiframes.pd_dataframe_ext.DataFrameType
            ) and nte__dbqbn.attr == 'columns':
            return pd.Index(isr__tpbq.columns)
        if isinstance(isr__tpbq, types.SliceType):
            snuum__wicew = get_definition(func_ir, nte__dbqbn.value)
            require(is_call(snuum__wicew))
            qvfl__iafie = find_callname(func_ir, snuum__wicew)
            zwwsq__hzgel = False
            if qvfl__iafie == ('_normalize_slice', 'numba.cpython.unicode'):
                require(nte__dbqbn.attr in ('start', 'step'))
                snuum__wicew = get_definition(func_ir, snuum__wicew.args[0])
                zwwsq__hzgel = True
            require(find_callname(func_ir, snuum__wicew) == ('slice',
                'builtins'))
            if len(snuum__wicew.args) == 1:
                if nte__dbqbn.attr == 'start':
                    return 0
                if nte__dbqbn.attr == 'step':
                    return 1
                require(nte__dbqbn.attr == 'stop')
                return get_const_value_inner(func_ir, snuum__wicew.args[0],
                    arg_types, typemap, updated_containers)
            if nte__dbqbn.attr == 'start':
                eydlz__ogf = get_const_value_inner(func_ir, snuum__wicew.
                    args[0], arg_types, typemap, updated_containers)
                if eydlz__ogf is None:
                    eydlz__ogf = 0
                if zwwsq__hzgel:
                    require(eydlz__ogf == 0)
                return eydlz__ogf
            if nte__dbqbn.attr == 'stop':
                assert not zwwsq__hzgel
                return get_const_value_inner(func_ir, snuum__wicew.args[1],
                    arg_types, typemap, updated_containers)
            require(nte__dbqbn.attr == 'step')
            if len(snuum__wicew.args) == 2:
                return 1
            else:
                eydlz__ogf = get_const_value_inner(func_ir, snuum__wicew.
                    args[2], arg_types, typemap, updated_containers)
                if eydlz__ogf is None:
                    eydlz__ogf = 1
                if zwwsq__hzgel:
                    require(eydlz__ogf == 1)
                return eydlz__ogf
    if is_expr(nte__dbqbn, 'getattr'):
        return getattr(get_const_value_inner(func_ir, nte__dbqbn.value,
            arg_types, typemap, updated_containers), nte__dbqbn.attr)
    if is_expr(nte__dbqbn, 'getitem'):
        value = get_const_value_inner(func_ir, nte__dbqbn.value, arg_types,
            typemap, updated_containers)
        index = get_const_value_inner(func_ir, nte__dbqbn.index, arg_types,
            typemap, updated_containers)
        return value[index]
    dlbs__rbsh = guard(find_callname, func_ir, nte__dbqbn, typemap)
    if dlbs__rbsh is not None and len(dlbs__rbsh) == 2 and dlbs__rbsh[0
        ] == 'keys' and isinstance(dlbs__rbsh[1], ir.Var):
        fdw__aqaz = nte__dbqbn.func
        nte__dbqbn = get_definition(func_ir, dlbs__rbsh[1])
        auf__ceija = dlbs__rbsh[1].name
        if updated_containers and auf__ceija in updated_containers:
            raise BodoConstUpdatedError(
                "variable '{}' is updated inplace using '{}'".format(
                auf__ceija, updated_containers[auf__ceija]))
        require(is_expr(nte__dbqbn, 'build_map'))
        vals = [kgtv__sdzpm[0] for kgtv__sdzpm in nte__dbqbn.items]
        zharg__qnov = guard(get_definition, func_ir, fdw__aqaz)
        assert isinstance(zharg__qnov, ir.Expr) and zharg__qnov.attr == 'keys'
        zharg__qnov.attr = 'copy'
        return [get_const_value_inner(func_ir, kgtv__sdzpm, arg_types,
            typemap, updated_containers) for kgtv__sdzpm in vals]
    if is_expr(nte__dbqbn, 'build_map'):
        return {get_const_value_inner(func_ir, kgtv__sdzpm[0], arg_types,
            typemap, updated_containers): get_const_value_inner(func_ir,
            kgtv__sdzpm[1], arg_types, typemap, updated_containers) for
            kgtv__sdzpm in nte__dbqbn.items}
    if is_expr(nte__dbqbn, 'build_tuple'):
        return tuple(get_const_value_inner(func_ir, kgtv__sdzpm, arg_types,
            typemap, updated_containers) for kgtv__sdzpm in nte__dbqbn.items)
    if is_expr(nte__dbqbn, 'build_list'):
        return [get_const_value_inner(func_ir, kgtv__sdzpm, arg_types,
            typemap, updated_containers) for kgtv__sdzpm in nte__dbqbn.items]
    if is_expr(nte__dbqbn, 'build_set'):
        return {get_const_value_inner(func_ir, kgtv__sdzpm, arg_types,
            typemap, updated_containers) for kgtv__sdzpm in nte__dbqbn.items}
    if dlbs__rbsh == ('list', 'builtins'):
        values = get_const_value_inner(func_ir, nte__dbqbn.args[0],
            arg_types, typemap, updated_containers)
        if isinstance(values, set):
            values = sorted(values)
        return list(values)
    if dlbs__rbsh == ('set', 'builtins'):
        return set(get_const_value_inner(func_ir, nte__dbqbn.args[0],
            arg_types, typemap, updated_containers))
    if dlbs__rbsh == ('range', 'builtins') and len(nte__dbqbn.args) == 1:
        return range(get_const_value_inner(func_ir, nte__dbqbn.args[0],
            arg_types, typemap, updated_containers))
    if dlbs__rbsh == ('slice', 'builtins'):
        return slice(*tuple(get_const_value_inner(func_ir, kgtv__sdzpm,
            arg_types, typemap, updated_containers) for kgtv__sdzpm in
            nte__dbqbn.args))
    if dlbs__rbsh == ('str', 'builtins'):
        return str(get_const_value_inner(func_ir, nte__dbqbn.args[0],
            arg_types, typemap, updated_containers))
    if dlbs__rbsh == ('bool', 'builtins'):
        return bool(get_const_value_inner(func_ir, nte__dbqbn.args[0],
            arg_types, typemap, updated_containers))
    if dlbs__rbsh == ('format', 'builtins'):
        mzev__owmbl = get_const_value_inner(func_ir, nte__dbqbn.args[0],
            arg_types, typemap, updated_containers)
        kufvk__lfvi = get_const_value_inner(func_ir, nte__dbqbn.args[1],
            arg_types, typemap, updated_containers) if len(nte__dbqbn.args
            ) > 1 else ''
        return format(mzev__owmbl, kufvk__lfvi)
    if dlbs__rbsh in (('init_binary_str_index',
        'bodo.hiframes.pd_index_ext'), ('init_numeric_index',
        'bodo.hiframes.pd_index_ext'), ('init_categorical_index',
        'bodo.hiframes.pd_index_ext'), ('init_datetime_index',
        'bodo.hiframes.pd_index_ext'), ('init_timedelta_index',
        'bodo.hiframes.pd_index_ext'), ('init_heter_index',
        'bodo.hiframes.pd_index_ext')):
        return pd.Index(get_const_value_inner(func_ir, nte__dbqbn.args[0],
            arg_types, typemap, updated_containers))
    if dlbs__rbsh == ('str_arr_from_sequence', 'bodo.libs.str_arr_ext'):
        return np.array(get_const_value_inner(func_ir, nte__dbqbn.args[0],
            arg_types, typemap, updated_containers))
    if dlbs__rbsh == ('init_range_index', 'bodo.hiframes.pd_index_ext'):
        return pd.RangeIndex(get_const_value_inner(func_ir, nte__dbqbn.args
            [0], arg_types, typemap, updated_containers),
            get_const_value_inner(func_ir, nte__dbqbn.args[1], arg_types,
            typemap, updated_containers), get_const_value_inner(func_ir,
            nte__dbqbn.args[2], arg_types, typemap, updated_containers))
    if dlbs__rbsh == ('len', 'builtins') and typemap and isinstance(typemap
        .get(nte__dbqbn.args[0].name, None), types.BaseTuple):
        return len(typemap[nte__dbqbn.args[0].name])
    if dlbs__rbsh == ('len', 'builtins'):
        cfyed__imvza = guard(get_definition, func_ir, nte__dbqbn.args[0])
        if isinstance(cfyed__imvza, ir.Expr) and cfyed__imvza.op in (
            'build_tuple', 'build_list', 'build_set', 'build_map'):
            return len(cfyed__imvza.items)
        return len(get_const_value_inner(func_ir, nte__dbqbn.args[0],
            arg_types, typemap, updated_containers))
    if dlbs__rbsh == ('CategoricalDtype', 'pandas'):
        kws = dict(nte__dbqbn.kws)
        hxhub__ynxlf = get_call_expr_arg('CategoricalDtype', nte__dbqbn.
            args, kws, 0, 'categories', '')
        hsmp__vgq = get_call_expr_arg('CategoricalDtype', nte__dbqbn.args,
            kws, 1, 'ordered', False)
        if hsmp__vgq is not False:
            hsmp__vgq = get_const_value_inner(func_ir, hsmp__vgq, arg_types,
                typemap, updated_containers)
        if hxhub__ynxlf == '':
            hxhub__ynxlf = None
        else:
            hxhub__ynxlf = get_const_value_inner(func_ir, hxhub__ynxlf,
                arg_types, typemap, updated_containers)
        return pd.CategoricalDtype(hxhub__ynxlf, hsmp__vgq)
    if dlbs__rbsh == ('dtype', 'numpy'):
        return np.dtype(get_const_value_inner(func_ir, nte__dbqbn.args[0],
            arg_types, typemap, updated_containers))
    if dlbs__rbsh is not None and len(dlbs__rbsh) == 2 and dlbs__rbsh[1
        ] == 'pandas' and dlbs__rbsh[0] in ('Int8Dtype', 'Int16Dtype',
        'Int32Dtype', 'Int64Dtype', 'UInt8Dtype', 'UInt16Dtype',
        'UInt32Dtype', 'UInt64Dtype'):
        return getattr(pd, dlbs__rbsh[0])()
    if dlbs__rbsh is not None and len(dlbs__rbsh) == 2 and isinstance(
        dlbs__rbsh[1], ir.Var):
        eydlz__ogf = get_const_value_inner(func_ir, dlbs__rbsh[1],
            arg_types, typemap, updated_containers)
        args = [get_const_value_inner(func_ir, kgtv__sdzpm, arg_types,
            typemap, updated_containers) for kgtv__sdzpm in nte__dbqbn.args]
        kws = {fqoo__poaqa[0]: get_const_value_inner(func_ir, fqoo__poaqa[1
            ], arg_types, typemap, updated_containers) for fqoo__poaqa in
            nte__dbqbn.kws}
        return getattr(eydlz__ogf, dlbs__rbsh[0])(*args, **kws)
    if dlbs__rbsh is not None and len(dlbs__rbsh) == 2 and dlbs__rbsh[1
        ] == 'bodo' and dlbs__rbsh[0] in bodo_types_with_params:
        args = tuple(get_const_value_inner(func_ir, kgtv__sdzpm, arg_types,
            typemap, updated_containers) for kgtv__sdzpm in nte__dbqbn.args)
        kwargs = {wmr__xljpt: get_const_value_inner(func_ir, kgtv__sdzpm,
            arg_types, typemap, updated_containers) for wmr__xljpt,
            kgtv__sdzpm in dict(nte__dbqbn.kws).items()}
        return getattr(bodo, dlbs__rbsh[0])(*args, **kwargs)
    if is_call(nte__dbqbn) and typemap and isinstance(typemap.get(
        nte__dbqbn.func.name, None), types.Dispatcher):
        py_func = typemap[nte__dbqbn.func.name].dispatcher.py_func
        require(nte__dbqbn.vararg is None)
        args = tuple(get_const_value_inner(func_ir, kgtv__sdzpm, arg_types,
            typemap, updated_containers) for kgtv__sdzpm in nte__dbqbn.args)
        kwargs = {wmr__xljpt: get_const_value_inner(func_ir, kgtv__sdzpm,
            arg_types, typemap, updated_containers) for wmr__xljpt,
            kgtv__sdzpm in dict(nte__dbqbn.kws).items()}
        arg_types = tuple(bodo.typeof(kgtv__sdzpm) for kgtv__sdzpm in args)
        kw_types = {xcywr__sodp: bodo.typeof(kgtv__sdzpm) for xcywr__sodp,
            kgtv__sdzpm in kwargs.items()}
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
    f_ir, typemap, deklf__itu, deklf__itu = bodo.compiler.get_func_type_info(
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
                    esfkg__gqpn = guard(get_definition, f_ir, rhs.func)
                    if isinstance(esfkg__gqpn, ir.Const) and isinstance(
                        esfkg__gqpn.value, numba.core.dispatcher.
                        ObjModeLiftedWith):
                        return False
                    oiww__yysx = guard(find_callname, f_ir, rhs)
                    if oiww__yysx is None:
                        return False
                    func_name, zuvib__xtfi = oiww__yysx
                    if zuvib__xtfi == 'pandas' and func_name.startswith('read_'
                        ):
                        return False
                    if oiww__yysx in (('fromfile', 'numpy'), ('file_read',
                        'bodo.io.np_io')):
                        return False
                    if oiww__yysx == ('File', 'h5py'):
                        return False
                    if isinstance(zuvib__xtfi, ir.Var):
                        hwezx__mry = typemap[zuvib__xtfi.name]
                        if isinstance(hwezx__mry, (DataFrameType, SeriesType)
                            ) and func_name in ('to_csv', 'to_excel',
                            'to_json', 'to_sql', 'to_pickle', 'to_parquet',
                            'info'):
                            return False
                        if isinstance(hwezx__mry, types.Array
                            ) and func_name == 'tofile':
                            return False
                        if isinstance(hwezx__mry, bodo.LoggingLoggerType):
                            return False
                        if str(hwezx__mry).startswith('Mpl'):
                            return False
                        if (func_name in container_update_method_names and
                            isinstance(guard(get_definition, f_ir,
                            zuvib__xtfi), ir.Arg)):
                            return False
                    if zuvib__xtfi in ('numpy.random', 'time', 'logging',
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
        kcrr__okl = func.literal_value.code
        todax__vhfs = {'np': np, 'pd': pd, 'numba': numba, 'bodo': bodo}
        if hasattr(func.literal_value, 'globals'):
            todax__vhfs = func.literal_value.globals
        f_ir = numba.core.ir_utils.get_ir_of_code(todax__vhfs, kcrr__okl)
        fix_struct_return(f_ir)
        typemap, gipla__uygaj, bht__tabyp, deklf__itu = (numba.core.
            typed_passes.type_inference_stage(typing_context,
            target_context, f_ir, arg_types, None))
    elif isinstance(func, bodo.utils.typing.FunctionLiteral):
        py_func = func.literal_value
        f_ir, typemap, bht__tabyp, gipla__uygaj = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    elif isinstance(func, CPUDispatcher):
        py_func = func.py_func
        f_ir, typemap, bht__tabyp, gipla__uygaj = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    else:
        if not isinstance(func, types.Dispatcher):
            if isinstance(func, types.Function):
                raise BodoError(
                    f'Bodo does not support built-in functions yet, {func}')
            else:
                raise BodoError(f'Function type expected, not {func}')
        py_func = func.dispatcher.py_func
        f_ir, typemap, bht__tabyp, gipla__uygaj = (bodo.compiler.
            get_func_type_info(py_func, arg_types, kw_types))
    if is_udf and isinstance(gipla__uygaj, types.DictType):
        uovp__wubph = guard(get_struct_keynames, f_ir, typemap)
        if uovp__wubph is not None:
            gipla__uygaj = StructType((gipla__uygaj.value_type,) * len(
                uovp__wubph), uovp__wubph)
    if is_udf and isinstance(gipla__uygaj, (SeriesType,
        HeterogeneousSeriesType)):
        ztmxd__ooml = numba.core.registry.cpu_target.typing_context
        fndah__nzf = numba.core.registry.cpu_target.target_context
        vgi__qjxt = bodo.transforms.series_pass.SeriesPass(f_ir,
            ztmxd__ooml, fndah__nzf, typemap, bht__tabyp, {})
        vgi__qjxt.run()
        vgi__qjxt.run()
        vgi__qjxt.run()
        nldqk__pvlp = compute_cfg_from_blocks(f_ir.blocks)
        qudu__qzgj = [guard(_get_const_series_info, f_ir.blocks[uwbm__xle],
            f_ir, typemap) for uwbm__xle in nldqk__pvlp.exit_points() if
            isinstance(f_ir.blocks[uwbm__xle].body[-1], ir.Return)]
        if None in qudu__qzgj or len(pd.Series(qudu__qzgj).unique()) != 1:
            gipla__uygaj.const_info = None
        else:
            gipla__uygaj.const_info = qudu__qzgj[0]
    return gipla__uygaj


def _get_const_series_info(block, f_ir, typemap):
    from bodo.hiframes.pd_series_ext import HeterogeneousSeriesType
    assert isinstance(block.body[-1], ir.Return)
    vrcv__tdvcx = block.body[-1].value
    fqa__jenwr = get_definition(f_ir, vrcv__tdvcx)
    require(is_expr(fqa__jenwr, 'cast'))
    fqa__jenwr = get_definition(f_ir, fqa__jenwr.value)
    require(is_call(fqa__jenwr) and find_callname(f_ir, fqa__jenwr) == (
        'init_series', 'bodo.hiframes.pd_series_ext'))
    jlxap__lnly = fqa__jenwr.args[1]
    fcrj__vdeiz = tuple(get_const_value_inner(f_ir, jlxap__lnly, typemap=
        typemap))
    if isinstance(typemap[vrcv__tdvcx.name], HeterogeneousSeriesType):
        return len(typemap[vrcv__tdvcx.name].data), fcrj__vdeiz
    uzxwd__ztg = fqa__jenwr.args[0]
    yvk__zjxvr = get_definition(f_ir, uzxwd__ztg)
    func_name, qwqv__vuwz = find_callname(f_ir, yvk__zjxvr)
    if is_call(yvk__zjxvr) and bodo.utils.utils.is_alloc_callname(func_name,
        qwqv__vuwz):
        ndbg__kltrr = yvk__zjxvr.args[0]
        pzbk__fmlob = get_const_value_inner(f_ir, ndbg__kltrr, typemap=typemap)
        return pzbk__fmlob, fcrj__vdeiz
    if is_call(yvk__zjxvr) and find_callname(f_ir, yvk__zjxvr) in [(
        'asarray', 'numpy'), ('str_arr_from_sequence', 'bodo.libs.str_arr_ext')
        ]:
        uzxwd__ztg = yvk__zjxvr.args[0]
        yvk__zjxvr = get_definition(f_ir, uzxwd__ztg)
    require(is_expr(yvk__zjxvr, 'build_tuple') or is_expr(yvk__zjxvr,
        'build_list'))
    return len(yvk__zjxvr.items), fcrj__vdeiz


def extract_keyvals_from_struct_map(f_ir, build_map, loc, scope, typemap=None):
    ogemt__xzm = []
    iuc__acm = []
    values = []
    for xcywr__sodp, kgtv__sdzpm in build_map.items:
        mkq__vkcy = find_const(f_ir, xcywr__sodp)
        require(isinstance(mkq__vkcy, str))
        iuc__acm.append(mkq__vkcy)
        ogemt__xzm.append(xcywr__sodp)
        values.append(kgtv__sdzpm)
    lolr__fiqh = ir.Var(scope, mk_unique_var('val_tup'), loc)
    eyh__nvnma = ir.Assign(ir.Expr.build_tuple(values, loc), lolr__fiqh, loc)
    f_ir._definitions[lolr__fiqh.name] = [eyh__nvnma.value]
    mojmq__yaq = ir.Var(scope, mk_unique_var('key_tup'), loc)
    mznxf__jvtx = ir.Assign(ir.Expr.build_tuple(ogemt__xzm, loc),
        mojmq__yaq, loc)
    f_ir._definitions[mojmq__yaq.name] = [mznxf__jvtx.value]
    if typemap is not None:
        typemap[lolr__fiqh.name] = types.Tuple([typemap[kgtv__sdzpm.name] for
            kgtv__sdzpm in values])
        typemap[mojmq__yaq.name] = types.Tuple([typemap[kgtv__sdzpm.name] for
            kgtv__sdzpm in ogemt__xzm])
    return iuc__acm, lolr__fiqh, eyh__nvnma, mojmq__yaq, mznxf__jvtx


def _replace_const_map_return(f_ir, block, label):
    require(isinstance(block.body[-1], ir.Return))
    kzaai__rxcxv = block.body[-1].value
    rcc__fps = guard(get_definition, f_ir, kzaai__rxcxv)
    require(is_expr(rcc__fps, 'cast'))
    fqa__jenwr = guard(get_definition, f_ir, rcc__fps.value)
    require(is_expr(fqa__jenwr, 'build_map'))
    require(len(fqa__jenwr.items) > 0)
    loc = block.loc
    scope = block.scope
    iuc__acm, lolr__fiqh, eyh__nvnma, mojmq__yaq, mznxf__jvtx = (
        extract_keyvals_from_struct_map(f_ir, fqa__jenwr, loc, scope))
    hkob__dwe = ir.Var(scope, mk_unique_var('conv_call'), loc)
    sxvdj__kmsa = ir.Assign(ir.Global('struct_if_heter_dict', bodo.utils.
        conversion.struct_if_heter_dict, loc), hkob__dwe, loc)
    f_ir._definitions[hkob__dwe.name] = [sxvdj__kmsa.value]
    mxnk__mph = ir.Var(scope, mk_unique_var('struct_val'), loc)
    uzqsr__mgva = ir.Assign(ir.Expr.call(hkob__dwe, [lolr__fiqh, mojmq__yaq
        ], {}, loc), mxnk__mph, loc)
    f_ir._definitions[mxnk__mph.name] = [uzqsr__mgva.value]
    rcc__fps.value = mxnk__mph
    fqa__jenwr.items = [(xcywr__sodp, xcywr__sodp) for xcywr__sodp,
        deklf__itu in fqa__jenwr.items]
    block.body = block.body[:-2] + [eyh__nvnma, mznxf__jvtx, sxvdj__kmsa,
        uzqsr__mgva] + block.body[-2:]
    return tuple(iuc__acm)


def get_struct_keynames(f_ir, typemap):
    nldqk__pvlp = compute_cfg_from_blocks(f_ir.blocks)
    tqbdr__sla = list(nldqk__pvlp.exit_points())[0]
    block = f_ir.blocks[tqbdr__sla]
    require(isinstance(block.body[-1], ir.Return))
    kzaai__rxcxv = block.body[-1].value
    rcc__fps = guard(get_definition, f_ir, kzaai__rxcxv)
    require(is_expr(rcc__fps, 'cast'))
    fqa__jenwr = guard(get_definition, f_ir, rcc__fps.value)
    require(is_call(fqa__jenwr) and find_callname(f_ir, fqa__jenwr) == (
        'struct_if_heter_dict', 'bodo.utils.conversion'))
    return get_overload_const_list(typemap[fqa__jenwr.args[1].name])


def fix_struct_return(f_ir):
    cat__lqbgu = None
    nldqk__pvlp = compute_cfg_from_blocks(f_ir.blocks)
    for tqbdr__sla in nldqk__pvlp.exit_points():
        cat__lqbgu = guard(_replace_const_map_return, f_ir, f_ir.blocks[
            tqbdr__sla], tqbdr__sla)
    return cat__lqbgu


def update_node_list_definitions(node_list, func_ir):
    loc = ir.Loc('', 0)
    koba__vqsww = ir.Block(ir.Scope(None, loc), loc)
    koba__vqsww.body = node_list
    build_definitions({(0): koba__vqsww}, func_ir._definitions)
    return


NESTED_TUP_SENTINEL = '$BODO_NESTED_TUP'


def gen_const_val_str(c):
    if isinstance(c, tuple):
        return "'{}{}', ".format(NESTED_TUP_SENTINEL, len(c)) + ', '.join(
            gen_const_val_str(kgtv__sdzpm) for kgtv__sdzpm in c)
    if isinstance(c, str):
        return "'{}'".format(c)
    if isinstance(c, (pd.Timestamp, pd.Timedelta, float)):
        return "'{}'".format(c)
    return str(c)


def gen_const_tup(vals):
    zxbwz__kth = ', '.join(gen_const_val_str(c) for c in vals)
    return '({}{})'.format(zxbwz__kth, ',' if len(vals) == 1 else '')


def get_const_tup_vals(c_typ):
    vals = get_overload_const_list(c_typ)
    return _get_original_nested_tups(vals)


def _get_original_nested_tups(vals):
    for rpxtw__udu in range(len(vals) - 1, -1, -1):
        kgtv__sdzpm = vals[rpxtw__udu]
        if isinstance(kgtv__sdzpm, str) and kgtv__sdzpm.startswith(
            NESTED_TUP_SENTINEL):
            haiu__ketb = int(kgtv__sdzpm[len(NESTED_TUP_SENTINEL):])
            return _get_original_nested_tups(tuple(vals[:rpxtw__udu]) + (
                tuple(vals[rpxtw__udu + 1:rpxtw__udu + haiu__ketb + 1]),) +
                tuple(vals[rpxtw__udu + haiu__ketb + 1:]))
    return tuple(vals)


def get_call_expr_arg(f_name, args, kws, arg_no, arg_name, default=None,
    err_msg=None, use_default=False):
    mzev__owmbl = None
    if len(args) > arg_no and arg_no >= 0:
        mzev__owmbl = args[arg_no]
        if arg_name in kws:
            err_msg = (
                f"{f_name}() got multiple values for argument '{arg_name}'")
            raise BodoError(err_msg)
    elif arg_name in kws:
        mzev__owmbl = kws[arg_name]
    if mzev__owmbl is None:
        if use_default or default is not None:
            return default
        if err_msg is None:
            err_msg = "{} requires '{}' argument".format(f_name, arg_name)
        raise BodoError(err_msg)
    return mzev__owmbl


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
    fhp__psu = {'numba': numba, 'np': np, 'bodo': bodo, 'pd': pd}
    if extra_globals is not None:
        fhp__psu.update(extra_globals)
    func.__globals__.update(fhp__psu)
    if pysig is not None:
        pre_nodes = [] if pre_nodes is None else pre_nodes
        scope = next(iter(pass_info.func_ir.blocks.values())).scope
        loc = scope.loc

        def normal_handler(index, param, default):
            return default

        def default_handler(index, param, default):
            fgg__fzv = ir.Var(scope, mk_unique_var('defaults'), loc)
            try:
                pass_info.typemap[fgg__fzv.name] = types.literal(default)
            except:
                pass_info.typemap[fgg__fzv.name] = numba.typeof(default)
            qnas__zunzq = ir.Assign(ir.Const(default, loc), fgg__fzv, loc)
            pre_nodes.append(qnas__zunzq)
            return fgg__fzv
        args = numba.core.typing.fold_arguments(pysig, args, kws,
            normal_handler, default_handler, normal_handler)
    ozhby__licq = tuple(pass_info.typemap[kgtv__sdzpm.name] for kgtv__sdzpm in
        args)
    if const:
        qcnqs__idbz = []
        for rpxtw__udu, mzev__owmbl in enumerate(args):
            eydlz__ogf = guard(find_const, pass_info.func_ir, mzev__owmbl)
            if eydlz__ogf:
                qcnqs__idbz.append(types.literal(eydlz__ogf))
            else:
                qcnqs__idbz.append(ozhby__licq[rpxtw__udu])
        ozhby__licq = tuple(qcnqs__idbz)
    return ReplaceFunc(func, ozhby__licq, args, fhp__psu, inline_bodo_calls,
        run_full_pipeline, pre_nodes)


def is_var_size_item_array_type(t):
    assert is_array_typ(t, False)
    return t == string_array_type or isinstance(t, ArrayItemArrayType
        ) or isinstance(t, StructArrayType) and any(
        is_var_size_item_array_type(uby__cuh) for uby__cuh in t.data)


def gen_init_varsize_alloc_sizes(t):
    if t == string_array_type:
        hkh__scpb = 'num_chars_{}'.format(ir_utils.next_label())
        return f'  {hkh__scpb} = 0\n', (hkh__scpb,)
    if isinstance(t, ArrayItemArrayType):
        rdee__ekt, snef__szk = gen_init_varsize_alloc_sizes(t.dtype)
        hkh__scpb = 'num_items_{}'.format(ir_utils.next_label())
        return f'  {hkh__scpb} = 0\n' + rdee__ekt, (hkh__scpb,) + snef__szk
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
        return 1 + sum(get_type_alloc_counts(uby__cuh.dtype) for uby__cuh in
            t.data)
    if isinstance(t, ArrayItemArrayType) or t == string_array_type:
        return 1 + get_type_alloc_counts(t.dtype)
    if isinstance(t, MapArrayType):
        return get_type_alloc_counts(t.key_arr_type) + get_type_alloc_counts(t
            .value_arr_type)
    if bodo.utils.utils.is_array_typ(t, False) or t == bodo.string_type:
        return 1
    if isinstance(t, StructType):
        return sum(get_type_alloc_counts(uby__cuh) for uby__cuh in t.data)
    if isinstance(t, types.BaseTuple):
        return sum(get_type_alloc_counts(uby__cuh) for uby__cuh in t.types)
    return 0


def find_udf_str_name(obj_dtype, func_name, typing_context, caller_name):
    vycw__legkt = typing_context.resolve_getattr(obj_dtype, func_name)
    if vycw__legkt is None:
        zofu__whevb = types.misc.Module(np)
        try:
            vycw__legkt = typing_context.resolve_getattr(zofu__whevb, func_name
                )
        except AttributeError as sji__lrlog:
            vycw__legkt = None
        if vycw__legkt is None:
            raise BodoError(
                f"{caller_name}(): No Pandas method or Numpy function found with the name '{func_name}'."
                )
    return vycw__legkt


def get_udf_str_return_type(obj_dtype, func_name, typing_context,
    caller_name, axis=None):
    vycw__legkt = find_udf_str_name(obj_dtype, func_name, typing_context,
        caller_name)
    if isinstance(vycw__legkt, types.BoundFunction):
        if axis is not None:
            gpg__llkm = vycw__legkt.get_call_type(typing_context, (), {
                'axis': axis})
        else:
            gpg__llkm = vycw__legkt.get_call_type(typing_context, (), {})
        return gpg__llkm.return_type
    else:
        if bodo.utils.typing.is_numpy_ufunc(vycw__legkt):
            gpg__llkm = vycw__legkt.get_call_type(typing_context, (
                obj_dtype,), {})
            return gpg__llkm.return_type
        raise BodoError(
            f"{caller_name}(): Only Pandas methods and np.ufunc are supported as string literals. '{func_name}' not supported."
            )


def get_pandas_method_str_impl(obj_dtype, func_name, typing_context,
    caller_name, axis=None):
    vycw__legkt = find_udf_str_name(obj_dtype, func_name, typing_context,
        caller_name)
    if isinstance(vycw__legkt, types.BoundFunction):
        qvj__qim = vycw__legkt.template
        if axis is not None:
            return qvj__qim._overload_func(obj_dtype, axis=axis)
        else:
            return qvj__qim._overload_func(obj_dtype)
    return None


def dict_to_const_keys_var_values_lists(dict_var, func_ir, arg_types,
    typemap, updated_containers, require_const_map, label):
    require(isinstance(dict_var, ir.Var))
    wka__vwugp = get_definition(func_ir, dict_var)
    require(isinstance(wka__vwugp, ir.Expr))
    require(wka__vwugp.op == 'build_map')
    hsy__vdx = wka__vwugp.items
    ogemt__xzm = []
    values = []
    wusz__uhtln = False
    for rpxtw__udu in range(len(hsy__vdx)):
        dydm__ysnsq, value = hsy__vdx[rpxtw__udu]
        try:
            pygys__pod = get_const_value_inner(func_ir, dydm__ysnsq,
                arg_types, typemap, updated_containers)
            ogemt__xzm.append(pygys__pod)
            values.append(value)
        except GuardException as sji__lrlog:
            require_const_map[dydm__ysnsq] = label
            wusz__uhtln = True
    if wusz__uhtln:
        raise GuardException
    return ogemt__xzm, values


def _get_const_keys_from_dict(args, func_ir, build_map, err_msg, loc):
    try:
        ogemt__xzm = tuple(get_const_value_inner(func_ir, t[0], args) for t in
            build_map.items)
    except GuardException as sji__lrlog:
        raise BodoError(err_msg, loc)
    if not all(isinstance(c, (str, int)) for c in ogemt__xzm):
        raise BodoError(err_msg, loc)
    return ogemt__xzm


def _convert_const_key_dict(args, func_ir, build_map, err_msg, scope, loc,
    output_sentinel_tuple=False):
    ogemt__xzm = _get_const_keys_from_dict(args, func_ir, build_map,
        err_msg, loc)
    qbruq__spvxh = []
    bovz__gufv = [bodo.transforms.typing_pass._create_const_var(xcywr__sodp,
        'dict_key', scope, loc, qbruq__spvxh) for xcywr__sodp in ogemt__xzm]
    qjk__cltg = [t[1] for t in build_map.items]
    if output_sentinel_tuple:
        grbbr__rjq = ir.Var(scope, mk_unique_var('sentinel'), loc)
        mbefw__wyhlr = ir.Var(scope, mk_unique_var('dict_tup'), loc)
        qbruq__spvxh.append(ir.Assign(ir.Const('__bodo_tup', loc),
            grbbr__rjq, loc))
        qmuta__dpq = [grbbr__rjq] + bovz__gufv + qjk__cltg
        qbruq__spvxh.append(ir.Assign(ir.Expr.build_tuple(qmuta__dpq, loc),
            mbefw__wyhlr, loc))
        return (mbefw__wyhlr,), qbruq__spvxh
    else:
        uhug__icds = ir.Var(scope, mk_unique_var('values_tup'), loc)
        sdnw__ohv = ir.Var(scope, mk_unique_var('idx_tup'), loc)
        qbruq__spvxh.append(ir.Assign(ir.Expr.build_tuple(qjk__cltg, loc),
            uhug__icds, loc))
        qbruq__spvxh.append(ir.Assign(ir.Expr.build_tuple(bovz__gufv, loc),
            sdnw__ohv, loc))
        return (uhug__icds, sdnw__ohv), qbruq__spvxh
