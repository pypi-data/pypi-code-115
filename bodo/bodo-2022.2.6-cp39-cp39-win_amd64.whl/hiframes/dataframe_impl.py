"""
Implementation of DataFrame attributes and methods using overload.
"""
import operator
import re
import warnings
from collections import namedtuple
from typing import Tuple
import llvmlite.llvmpy.core as lc
import numba
import numpy as np
import pandas as pd
from numba.core import cgutils, ir, types
from numba.core.imputils import RefType, impl_ret_borrowed, impl_ret_new_ref, iternext_impl, lower_builtin
from numba.core.ir_utils import mk_unique_var, next_label
from numba.core.typing import signature
from numba.core.typing.templates import AbstractTemplate, infer_global
from numba.extending import lower_getattr, models, overload, overload_attribute, overload_method, register_model, type_callable
import bodo
from bodo.hiframes.datetime_date_ext import datetime_date_array_type
from bodo.hiframes.datetime_timedelta_ext import _no_input, datetime_timedelta_array_type
from bodo.hiframes.pd_categorical_ext import CategoricalArrayType
from bodo.hiframes.pd_dataframe_ext import DataFrameType, check_runtime_cols_unsupported, handle_inplace_df_type_change
from bodo.hiframes.pd_index_ext import DatetimeIndexType, RangeIndexType, StringIndexType, is_pd_index_type
from bodo.hiframes.pd_multi_index_ext import MultiIndexType
from bodo.hiframes.pd_series_ext import SeriesType, if_series_to_array_type
from bodo.hiframes.pd_timestamp_ext import pd_timestamp_type
from bodo.hiframes.rolling import is_supported_shift_array_type
from bodo.hiframes.split_impl import string_array_split_view_type
from bodo.libs.array_item_arr_ext import ArrayItemArrayType
from bodo.libs.binary_arr_ext import binary_array_type
from bodo.libs.bool_arr_ext import BooleanArrayType, boolean_array, boolean_dtype
from bodo.libs.decimal_arr_ext import DecimalArrayType
from bodo.libs.dict_arr_ext import dict_str_arr_type
from bodo.libs.int_arr_ext import IntegerArrayType
from bodo.libs.interval_arr_ext import IntervalArrayType
from bodo.libs.map_arr_ext import MapArrayType
from bodo.libs.str_arr_ext import string_array_type
from bodo.libs.str_ext import string_type
from bodo.libs.struct_arr_ext import StructArrayType
from bodo.utils.transform import bodo_types_with_params, gen_const_tup, no_side_effect_call_tuples
from bodo.utils.typing import BodoError, BodoWarning, check_unsupported_args, dtype_to_array_type, ensure_constant_arg, ensure_constant_values, get_index_data_arr_types, get_index_names, get_literal_value, get_nullable_and_non_nullable_types, get_overload_const_bool, get_overload_const_int, get_overload_const_list, get_overload_const_str, get_overload_const_tuple, get_overload_constant_dict, get_overload_constant_series, is_common_scalar_dtype, is_literal_type, is_overload_bool, is_overload_bool_list, is_overload_constant_bool, is_overload_constant_dict, is_overload_constant_int, is_overload_constant_list, is_overload_constant_series, is_overload_constant_str, is_overload_constant_tuple, is_overload_false, is_overload_int, is_overload_none, is_overload_true, is_overload_zero, parse_dtype, raise_bodo_error, unliteral_val
from bodo.utils.utils import is_array_typ


@overload_attribute(DataFrameType, 'index', inline='always')
def overload_dataframe_index(df):
    return lambda df: bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)


def generate_col_to_index_func_text(col_names: Tuple):
    if all(isinstance(a, str) for a in col_names) or all(isinstance(a,
        bytes) for a in col_names):
        roiko__zpquk = f'bodo.utils.conversion.coerce_to_array({col_names})'
        return (
            f'bodo.hiframes.pd_index_ext.init_binary_str_index({roiko__zpquk})\n'
            )
    elif all(isinstance(a, (int, float)) for a in col_names):
        arr = f'bodo.utils.conversion.coerce_to_array({col_names})'
        return f'bodo.hiframes.pd_index_ext.init_numeric_index({arr})\n'
    else:
        return f'bodo.hiframes.pd_index_ext.init_heter_index({col_names})\n'


@overload_attribute(DataFrameType, 'columns', inline='always')
def overload_dataframe_columns(df):
    zhuuz__rnab = 'def impl(df):\n'
    if df.has_runtime_cols:
        zhuuz__rnab += (
            '  return bodo.hiframes.pd_dataframe_ext.get_dataframe_column_names(df)\n'
            )
    else:
        xixpt__rgpqd = (bodo.hiframes.dataframe_impl.
            generate_col_to_index_func_text(df.columns))
        zhuuz__rnab += f'  return {xixpt__rgpqd}'
    vowd__xeiyc = {}
    exec(zhuuz__rnab, {'bodo': bodo}, vowd__xeiyc)
    impl = vowd__xeiyc['impl']
    return impl


@overload_attribute(DataFrameType, 'values')
def overload_dataframe_values(df):
    check_runtime_cols_unsupported(df, 'DataFrame.values')
    if not is_df_values_numpy_supported_dftyp(df):
        raise_bodo_error(
            'DataFrame.values: only supported for dataframes containing numeric values'
            )
    fji__ulh = len(df.columns)
    hoy__opz = set(i for i in range(fji__ulh) if isinstance(df.data[i],
        IntegerArrayType))
    data_args = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(i, '.astype(float)' if i in hoy__opz else '') for i in range
        (fji__ulh))
    zhuuz__rnab = 'def f(df):\n'.format()
    zhuuz__rnab += '    return np.stack(({},), 1)\n'.format(data_args)
    vowd__xeiyc = {}
    exec(zhuuz__rnab, {'bodo': bodo, 'np': np}, vowd__xeiyc)
    azl__lzkx = vowd__xeiyc['f']
    return azl__lzkx


@overload_method(DataFrameType, 'to_numpy', inline='always', no_unliteral=True)
def overload_dataframe_to_numpy(df, dtype=None, copy=False, na_value=_no_input
    ):
    check_runtime_cols_unsupported(df, 'DataFrame.to_numpy()')
    if not is_df_values_numpy_supported_dftyp(df):
        raise_bodo_error(
            'DataFrame.to_numpy(): only supported for dataframes containing numeric values'
            )
    bxk__ruyqa = {'dtype': dtype, 'na_value': na_value}
    fyzts__uqjd = {'dtype': None, 'na_value': _no_input}
    check_unsupported_args('DataFrame.to_numpy', bxk__ruyqa, fyzts__uqjd,
        package_name='pandas', module_name='DataFrame')

    def impl(df, dtype=None, copy=False, na_value=_no_input):
        return df.values
    return impl


@overload_attribute(DataFrameType, 'ndim', inline='always')
def overload_dataframe_ndim(df):
    return lambda df: 2


@overload_attribute(DataFrameType, 'size')
def overload_dataframe_size(df):
    if df.has_runtime_cols:

        def impl(df):
            t = bodo.hiframes.pd_dataframe_ext.get_dataframe_table(df)
            auec__prjl = bodo.hiframes.table.compute_num_runtime_columns(t)
            return auec__prjl * len(t)
        return impl
    ncols = len(df.columns)
    return lambda df: ncols * len(df)


@lower_getattr(DataFrameType, 'shape')
def lower_dataframe_shape(context, builder, typ, val):
    impl = overload_dataframe_shape(typ)
    return context.compile_internal(builder, impl, types.Tuple([types.int64,
        types.int64])(typ), (val,))


def overload_dataframe_shape(df):
    if df.has_runtime_cols:

        def impl(df):
            t = bodo.hiframes.pd_dataframe_ext.get_dataframe_table(df)
            auec__prjl = bodo.hiframes.table.compute_num_runtime_columns(t)
            return len(t), auec__prjl
        return impl
    ncols = len(df.columns)
    return lambda df: (len(df), types.int64(ncols))


@overload_attribute(DataFrameType, 'dtypes')
def overload_dataframe_dtypes(df):
    check_runtime_cols_unsupported(df, 'DataFrame.dtypes')
    zhuuz__rnab = 'def impl(df):\n'
    data = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).dtype\n'
         for i in range(len(df.columns)))
    emfl__hfbdu = ',' if len(df.columns) == 1 else ''
    index = f'bodo.hiframes.pd_index_ext.init_heter_index({df.columns})'
    zhuuz__rnab += f"""  return bodo.hiframes.pd_series_ext.init_series(({data}{emfl__hfbdu}), {index}, None)
"""
    vowd__xeiyc = {}
    exec(zhuuz__rnab, {'bodo': bodo}, vowd__xeiyc)
    impl = vowd__xeiyc['impl']
    return impl


@overload_attribute(DataFrameType, 'empty')
def overload_dataframe_empty(df):
    check_runtime_cols_unsupported(df, 'DataFrame.empty')
    if len(df.columns) == 0:
        return lambda df: True
    return lambda df: len(df) == 0


@overload_method(DataFrameType, 'assign', no_unliteral=True)
def overload_dataframe_assign(df, **kwargs):
    check_runtime_cols_unsupported(df, 'DataFrame.assign()')
    raise_bodo_error('Invalid df.assign() call')


@overload_method(DataFrameType, 'insert', no_unliteral=True)
def overload_dataframe_insert(df, loc, column, value, allow_duplicates=False):
    check_runtime_cols_unsupported(df, 'DataFrame.insert()')
    raise_bodo_error('Invalid df.insert() call')


def _get_dtype_str(dtype):
    if isinstance(dtype, types.Function):
        if dtype.key[0] == str:
            return "'str'"
        elif dtype.key[0] == float:
            return 'float'
        elif dtype.key[0] == int:
            return 'int'
        elif dtype.key[0] == bool:
            return 'bool'
        else:
            raise BodoError(f'invalid dtype: {dtype}')
    if isinstance(dtype, types.DTypeSpec):
        dtype = dtype.dtype
    if isinstance(dtype, types.functions.NumberClass):
        return f"'{dtype.key}'"
    if isinstance(dtype, types.PyObject) or dtype in (object, 'object'):
        return "'object'"
    if dtype in (bodo.libs.str_arr_ext.string_dtype, pd.StringDtype()):
        return 'str'
    return f"'{dtype}'"


@overload_method(DataFrameType, 'astype', inline='always', no_unliteral=True)
def overload_dataframe_astype(df, dtype, copy=True, errors='raise',
    _bodo_nan_to_str=True, _bodo_object_typeref=None):
    check_runtime_cols_unsupported(df, 'DataFrame.astype()')
    bxk__ruyqa = {'copy': copy, 'errors': errors}
    fyzts__uqjd = {'copy': True, 'errors': 'raise'}
    check_unsupported_args('df.astype', bxk__ruyqa, fyzts__uqjd,
        package_name='pandas', module_name='DataFrame')
    if dtype == types.unicode_type:
        raise_bodo_error(
            "DataFrame.astype(): 'dtype' when passed as string must be a constant value"
            )
    extra_globals = None
    if _bodo_object_typeref is not None:
        assert isinstance(_bodo_object_typeref, types.TypeRef
            ), 'Bodo schema used in DataFrame.astype should be a TypeRef'
        djv__kvlm = _bodo_object_typeref.instance_type
        assert isinstance(djv__kvlm, DataFrameType
            ), 'Bodo schema used in DataFrame.astype is only supported for DataFrame schemas'
        extra_globals = {}
        hnp__jxp = {}
        for i, name in enumerate(djv__kvlm.columns):
            arr_typ = djv__kvlm.data[i]
            if isinstance(arr_typ, IntegerArrayType):
                mdn__hzy = bodo.libs.int_arr_ext.IntDtype(arr_typ.dtype)
            elif arr_typ == boolean_array:
                mdn__hzy = boolean_dtype
            else:
                mdn__hzy = arr_typ.dtype
            extra_globals[f'_bodo_schema{i}'] = mdn__hzy
            hnp__jxp[name] = f'_bodo_schema{i}'
        data_args = ', '.join(
            f'bodo.utils.conversion.fix_arr_dtype(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), {hnp__jxp[sijzc__erm]}, copy, nan_to_str=_bodo_nan_to_str, from_series=True)'
             if sijzc__erm in hnp__jxp else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})' for
            i, sijzc__erm in enumerate(df.columns))
    elif is_overload_constant_dict(dtype) or is_overload_constant_series(dtype
        ):
        hgz__neyub = get_overload_constant_dict(dtype
            ) if is_overload_constant_dict(dtype) else dict(
            get_overload_constant_series(dtype))
        data_args = ', '.join(
            f'bodo.utils.conversion.fix_arr_dtype(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), {_get_dtype_str(hgz__neyub[sijzc__erm])}, copy, nan_to_str=_bodo_nan_to_str, from_series=True)'
             if sijzc__erm in hgz__neyub else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})' for
            i, sijzc__erm in enumerate(df.columns))
    else:
        data_args = ', '.join(
            f'bodo.utils.conversion.fix_arr_dtype(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), dtype, copy, nan_to_str=_bodo_nan_to_str, from_series=True)'
             for i in range(len(df.columns)))
    header = """def impl(df, dtype, copy=True, errors='raise', _bodo_nan_to_str=True, _bodo_object_typeref=None):
"""
    return _gen_init_df(header, df.columns, data_args, extra_globals=
        extra_globals)


@overload_method(DataFrameType, 'copy', inline='always', no_unliteral=True)
def overload_dataframe_copy(df, deep=True):
    check_runtime_cols_unsupported(df, 'DataFrame.copy()')
    vcny__gqvr = []
    for i in range(len(df.columns)):
        arr = f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})'
        if is_overload_true(deep):
            vcny__gqvr.append(arr + '.copy()')
        elif is_overload_false(deep):
            vcny__gqvr.append(arr)
        else:
            vcny__gqvr.append(f'{arr}.copy() if deep else {arr}')
    header = 'def impl(df, deep=True):\n'
    return _gen_init_df(header, df.columns, ', '.join(vcny__gqvr))


@overload_method(DataFrameType, 'rename', inline='always', no_unliteral=True)
def overload_dataframe_rename(df, mapper=None, index=None, columns=None,
    axis=None, copy=True, inplace=False, level=None, errors='ignore',
    _bodo_transformed=False):
    check_runtime_cols_unsupported(df, 'DataFrame.rename()')
    handle_inplace_df_type_change(inplace, _bodo_transformed, 'rename')
    bxk__ruyqa = {'index': index, 'level': level, 'errors': errors}
    fyzts__uqjd = {'index': None, 'level': None, 'errors': 'ignore'}
    check_unsupported_args('DataFrame.rename', bxk__ruyqa, fyzts__uqjd,
        package_name='pandas', module_name='DataFrame')
    if not is_overload_constant_bool(inplace):
        raise BodoError(
            "DataFrame.rename(): 'inplace' keyword only supports boolean constant assignment"
            )
    if not is_overload_none(mapper):
        if not is_overload_none(columns):
            raise BodoError(
                "DataFrame.rename(): Cannot specify both 'mapper' and 'columns'"
                )
        if not (is_overload_constant_int(axis) and get_overload_const_int(
            axis) == 1):
            raise BodoError(
                "DataFrame.rename(): 'mapper' only supported with axis=1")
        if not is_overload_constant_dict(mapper):
            raise_bodo_error(
                "'mapper' argument to DataFrame.rename() should be a constant dictionary"
                )
        mzaas__ynfm = get_overload_constant_dict(mapper)
    elif not is_overload_none(columns):
        if not is_overload_none(axis):
            raise BodoError(
                "DataFrame.rename(): Cannot specify both 'axis' and 'columns'")
        if not is_overload_constant_dict(columns):
            raise_bodo_error(
                "'columns' argument to DataFrame.rename() should be a constant dictionary"
                )
        mzaas__ynfm = get_overload_constant_dict(columns)
    else:
        raise_bodo_error(
            "DataFrame.rename(): must pass columns either via 'mapper' and 'axis'=1 or 'columns'"
            )
    yvexc__ncpx = [mzaas__ynfm.get(df.columns[i], df.columns[i]) for i in
        range(len(df.columns))]
    vcny__gqvr = []
    for i in range(len(df.columns)):
        arr = f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})'
        if is_overload_true(copy):
            vcny__gqvr.append(arr + '.copy()')
        elif is_overload_false(copy):
            vcny__gqvr.append(arr)
        else:
            vcny__gqvr.append(f'{arr}.copy() if copy else {arr}')
    header = """def impl(df, mapper=None, index=None, columns=None, axis=None, copy=True, inplace=False, level=None, errors='ignore', _bodo_transformed=False):
"""
    return _gen_init_df(header, yvexc__ncpx, ', '.join(vcny__gqvr))


@overload_method(DataFrameType, 'filter', no_unliteral=True)
def overload_dataframe_filter(df, items=None, like=None, regex=None, axis=None
    ):
    check_runtime_cols_unsupported(df, 'DataFrame.filter()')
    avbye__kqd = not is_overload_none(items)
    wjc__dmu = not is_overload_none(like)
    rcx__ytm = not is_overload_none(regex)
    qzlyu__zjlbp = avbye__kqd ^ wjc__dmu ^ rcx__ytm
    cvgji__jsno = not (avbye__kqd or wjc__dmu or rcx__ytm)
    if cvgji__jsno:
        raise BodoError(
            'DataFrame.filter(): one of keyword arguments `items`, `like`, and `regex` must be supplied'
            )
    if not qzlyu__zjlbp:
        raise BodoError(
            'DataFrame.filter(): keyword arguments `items`, `like`, and `regex` are mutually exclusive'
            )
    if is_overload_none(axis):
        axis = 'columns'
    if is_overload_constant_str(axis):
        axis = get_overload_const_str(axis)
        if axis not in {'index', 'columns'}:
            raise_bodo_error(
                'DataFrame.filter(): keyword arguments `axis` must be either "index" or "columns" if string'
                )
        rgitg__sarjb = 0 if axis == 'index' else 1
    elif is_overload_constant_int(axis):
        axis = get_overload_const_int(axis)
        if axis not in {0, 1}:
            raise_bodo_error(
                'DataFrame.filter(): keyword arguments `axis` must be either 0 or 1 if integer'
                )
        rgitg__sarjb = axis
    else:
        raise_bodo_error(
            'DataFrame.filter(): keyword arguments `axis` must be constant string or integer'
            )
    assert rgitg__sarjb in {0, 1}
    zhuuz__rnab = (
        'def impl(df, items=None, like=None, regex=None, axis=None):\n')
    if rgitg__sarjb == 0:
        raise BodoError(
            'DataFrame.filter(): filtering based on index is not supported.')
    if rgitg__sarjb == 1:
        bii__mlmg = []
        awics__zfxf = []
        avhmr__gxiwe = []
        if avbye__kqd:
            if is_overload_constant_list(items):
                gar__ktit = get_overload_const_list(items)
            else:
                raise BodoError(
                    "Dataframe.filter(): argument 'items' must be a list of constant strings."
                    )
        if wjc__dmu:
            if is_overload_constant_str(like):
                azbgc__epxz = get_overload_const_str(like)
            else:
                raise BodoError(
                    "Dataframe.filter(): argument 'like' must be a constant string."
                    )
        if rcx__ytm:
            if is_overload_constant_str(regex):
                shpjh__gynjn = get_overload_const_str(regex)
                dad__vgbp = re.compile(shpjh__gynjn)
            else:
                raise BodoError(
                    "Dataframe.filter(): argument 'regex' must be a constant string."
                    )
        for i, sijzc__erm in enumerate(df.columns):
            if not is_overload_none(items
                ) and sijzc__erm in gar__ktit or not is_overload_none(like
                ) and azbgc__epxz in str(sijzc__erm) or not is_overload_none(
                regex) and dad__vgbp.search(str(sijzc__erm)):
                awics__zfxf.append(sijzc__erm)
                avhmr__gxiwe.append(i)
        for i in avhmr__gxiwe:
            xhzgu__wjk = f'data_{i}'
            bii__mlmg.append(xhzgu__wjk)
            zhuuz__rnab += f"""  {xhzgu__wjk} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})
"""
        data_args = ', '.join(bii__mlmg)
        return _gen_init_df(zhuuz__rnab, awics__zfxf, data_args)


@overload_method(DataFrameType, 'isna', inline='always', no_unliteral=True)
@overload_method(DataFrameType, 'isnull', inline='always', no_unliteral=True)
def overload_dataframe_isna(df):
    check_runtime_cols_unsupported(df, 'DataFrame.isna()')
    data_args = ', '.join(
        f'bodo.libs.array_ops.array_op_isna(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}))'
         for i in range(len(df.columns)))
    header = 'def impl(df):\n'
    return _gen_init_df(header, df.columns, data_args)


@overload_method(DataFrameType, 'select_dtypes', inline='always',
    no_unliteral=True)
def overload_dataframe_select_dtypes(df, include=None, exclude=None):
    check_runtime_cols_unsupported(df, 'DataFrame.select_dtypes')
    ccxkj__ryazg = is_overload_none(include)
    qmmfs__agujd = is_overload_none(exclude)
    dtnjn__avuw = 'DataFrame.select_dtypes'
    if ccxkj__ryazg and qmmfs__agujd:
        raise_bodo_error(
            'DataFrame.select_dtypes() At least one of include or exclude must not be none'
            )

    def is_legal_input(elem):
        return is_overload_constant_str(elem) or isinstance(elem, types.
            DTypeSpec) or isinstance(elem, types.Function)
    if not ccxkj__ryazg:
        if is_overload_constant_list(include):
            include = get_overload_const_list(include)
            tffce__prkb = [dtype_to_array_type(parse_dtype(elem,
                dtnjn__avuw)) for elem in include]
        elif is_legal_input(include):
            tffce__prkb = [dtype_to_array_type(parse_dtype(include,
                dtnjn__avuw))]
        else:
            raise_bodo_error(
                'DataFrame.select_dtypes() only supports constant strings or types as arguments'
                )
        tffce__prkb = get_nullable_and_non_nullable_types(tffce__prkb)
        ghe__nhqdb = tuple(sijzc__erm for i, sijzc__erm in enumerate(df.
            columns) if df.data[i] in tffce__prkb)
    else:
        ghe__nhqdb = df.columns
    if not qmmfs__agujd:
        if is_overload_constant_list(exclude):
            exclude = get_overload_const_list(exclude)
            pul__ook = [dtype_to_array_type(parse_dtype(elem, dtnjn__avuw)) for
                elem in exclude]
        elif is_legal_input(exclude):
            pul__ook = [dtype_to_array_type(parse_dtype(exclude, dtnjn__avuw))]
        else:
            raise_bodo_error(
                'DataFrame.select_dtypes() only supports constant strings or types as arguments'
                )
        pul__ook = get_nullable_and_non_nullable_types(pul__ook)
        ghe__nhqdb = tuple(sijzc__erm for sijzc__erm in ghe__nhqdb if df.
            data[df.columns.index(sijzc__erm)] not in pul__ook)
    data_args = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(sijzc__erm)})'
         for sijzc__erm in ghe__nhqdb)
    header = 'def impl(df, include=None, exclude=None):\n'
    return _gen_init_df(header, ghe__nhqdb, data_args)


@overload_method(DataFrameType, 'notna', inline='always', no_unliteral=True)
@overload_method(DataFrameType, 'notnull', inline='always', no_unliteral=True)
def overload_dataframe_notna(df):
    check_runtime_cols_unsupported(df, 'DataFrame.notna()')
    data_args = ', '.join(
        f'bodo.libs.array_ops.array_op_isna(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})) == False'
         for i in range(len(df.columns)))
    header = 'def impl(df):\n'
    return _gen_init_df(header, df.columns, data_args)


def overload_dataframe_head(df, n=5):
    data_args = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})[:n]' for
        i in range(len(df.columns)))
    header = 'def impl(df, n=5):\n'
    index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[:n]'
    return _gen_init_df(header, df.columns, data_args, index)


@lower_builtin('df.head', DataFrameType, types.Integer)
@lower_builtin('df.head', DataFrameType, types.Omitted)
def dataframe_head_lower(context, builder, sig, args):
    impl = overload_dataframe_head(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


@overload_method(DataFrameType, 'tail', inline='always', no_unliteral=True)
def overload_dataframe_tail(df, n=5):
    check_runtime_cols_unsupported(df, 'DataFrame.tail()')
    if not is_overload_int(n):
        raise BodoError("Dataframe.tail(): 'n' must be an Integer")
    data_args = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})[m:]' for
        i in range(len(df.columns)))
    header = 'def impl(df, n=5):\n'
    header += '  m = bodo.hiframes.series_impl.tail_slice(len(df), n)\n'
    index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[m:]'
    return _gen_init_df(header, df.columns, data_args, index)


@overload_method(DataFrameType, 'first', inline='always', no_unliteral=True)
def overload_dataframe_first(df, offset):
    check_runtime_cols_unsupported(df, 'DataFrame.first()')
    kms__zzxuy = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if not isinstance(df.index, DatetimeIndexType):
        raise BodoError(
            'DataFrame.first(): only supports a DatetimeIndex index')
    if types.unliteral(offset) not in kms__zzxuy:
        raise BodoError(
            "DataFrame.first(): 'offset' must be an string or DateOffset")
    index = (
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[:valid_entries]'
        )
    data_args = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})[:valid_entries]'
         for i in range(len(df.columns)))
    header = 'def impl(df, offset):\n'
    header += (
        '  df_index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
        )
    header += '  if len(df_index):\n'
    header += '    start_date = df_index[0]\n'
    header += """    valid_entries = bodo.libs.array_kernels.get_valid_entries_from_date_offset(df_index, offset, start_date, False)
"""
    header += '  else:\n'
    header += '    valid_entries = 0\n'
    return _gen_init_df(header, df.columns, data_args, index)


@overload_method(DataFrameType, 'last', inline='always', no_unliteral=True)
def overload_dataframe_last(df, offset):
    check_runtime_cols_unsupported(df, 'DataFrame.last()')
    kms__zzxuy = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if not isinstance(df.index, DatetimeIndexType):
        raise BodoError('DataFrame.last(): only supports a DatetimeIndex index'
            )
    if types.unliteral(offset) not in kms__zzxuy:
        raise BodoError(
            "DataFrame.last(): 'offset' must be an string or DateOffset")
    index = (
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[len(df)-valid_entries:]'
        )
    data_args = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})[len(df)-valid_entries:]'
         for i in range(len(df.columns)))
    header = 'def impl(df, offset):\n'
    header += (
        '  df_index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
        )
    header += '  if len(df_index):\n'
    header += '    final_date = df_index[-1]\n'
    header += """    valid_entries = bodo.libs.array_kernels.get_valid_entries_from_date_offset(df_index, offset, final_date, True)
"""
    header += '  else:\n'
    header += '    valid_entries = 0\n'
    return _gen_init_df(header, df.columns, data_args, index)


@overload_method(DataFrameType, 'to_string', no_unliteral=True)
def to_string_overload(df, buf=None, columns=None, col_space=None, header=
    True, index=True, na_rep='NaN', formatters=None, float_format=None,
    sparsify=None, index_names=True, justify=None, max_rows=None, min_rows=
    None, max_cols=None, show_dimensions=False, decimal='.', line_width=
    None, max_colwidth=None, encoding=None):
    check_runtime_cols_unsupported(df, 'DataFrame.to_string()')

    def impl(df, buf=None, columns=None, col_space=None, header=True, index
        =True, na_rep='NaN', formatters=None, float_format=None, sparsify=
        None, index_names=True, justify=None, max_rows=None, min_rows=None,
        max_cols=None, show_dimensions=False, decimal='.', line_width=None,
        max_colwidth=None, encoding=None):
        with numba.objmode(res='string'):
            res = df.to_string(buf=buf, columns=columns, col_space=
                col_space, header=header, index=index, na_rep=na_rep,
                formatters=formatters, float_format=float_format, sparsify=
                sparsify, index_names=index_names, justify=justify,
                max_rows=max_rows, min_rows=min_rows, max_cols=max_cols,
                show_dimensions=show_dimensions, decimal=decimal,
                line_width=line_width, max_colwidth=max_colwidth, encoding=
                encoding)
        return res
    return impl


@overload_method(DataFrameType, 'isin', inline='always', no_unliteral=True)
def overload_dataframe_isin(df, values):
    check_runtime_cols_unsupported(df, 'DataFrame.isin()')
    from bodo.utils.typing import is_iterable_type
    zhuuz__rnab = 'def impl(df, values):\n'
    zdlx__kpj = {}
    bnc__hoxq = False
    if isinstance(values, DataFrameType):
        bnc__hoxq = True
        for i, sijzc__erm in enumerate(df.columns):
            if sijzc__erm in values.columns:
                beq__uwx = 'val{}'.format(i)
                zhuuz__rnab += (
                    """  {} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(values, {})
"""
                    .format(beq__uwx, values.columns.index(sijzc__erm)))
                zdlx__kpj[sijzc__erm] = beq__uwx
    elif is_iterable_type(values) and not isinstance(values, SeriesType):
        zdlx__kpj = {sijzc__erm: 'values' for sijzc__erm in df.columns}
    else:
        raise_bodo_error(f'pd.isin(): not supported for type {values}')
    data = []
    for i in range(len(df.columns)):
        beq__uwx = 'data{}'.format(i)
        zhuuz__rnab += (
            '  {} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})\n'
            .format(beq__uwx, i))
        data.append(beq__uwx)
    qqedk__vlx = ['out{}'.format(i) for i in range(len(df.columns))]
    hfuw__crz = """
  numba.parfors.parfor.init_prange()
  n = len({0})
  m = len({1})
  {2} = np.empty(n, np.bool_)
  for i in numba.parfors.parfor.internal_prange(n):
    {2}[i] = {0}[i] == {1}[i] if i < m else False
"""
    xdhr__dabhe = """
  numba.parfors.parfor.init_prange()
  n = len({0})
  {2} = np.empty(n, np.bool_)
  for i in numba.parfors.parfor.internal_prange(n):
    {2}[i] = {0}[i] in {1}
"""
    tjagr__grqn = '  {} = np.zeros(len(df), np.bool_)\n'
    for i, (cname, dvq__hgcu) in enumerate(zip(df.columns, data)):
        if cname in zdlx__kpj:
            lbwfa__aspm = zdlx__kpj[cname]
            if bnc__hoxq:
                zhuuz__rnab += hfuw__crz.format(dvq__hgcu, lbwfa__aspm,
                    qqedk__vlx[i])
            else:
                zhuuz__rnab += xdhr__dabhe.format(dvq__hgcu, lbwfa__aspm,
                    qqedk__vlx[i])
        else:
            zhuuz__rnab += tjagr__grqn.format(qqedk__vlx[i])
    return _gen_init_df(zhuuz__rnab, df.columns, ','.join(qqedk__vlx))


@overload_method(DataFrameType, 'abs', inline='always', no_unliteral=True)
def overload_dataframe_abs(df):
    check_runtime_cols_unsupported(df, 'DataFrame.abs()')
    for arr_typ in df.data:
        if not (isinstance(arr_typ.dtype, types.Number) or arr_typ.dtype ==
            bodo.timedelta64ns):
            raise_bodo_error(
                f'DataFrame.abs(): Only supported for numeric and Timedelta. Encountered array with dtype {arr_typ.dtype}'
                )
    fji__ulh = len(df.columns)
    data_args = ', '.join(
        'np.abs(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}))'
        .format(i) for i in range(fji__ulh))
    header = 'def impl(df):\n'
    return _gen_init_df(header, df.columns, data_args)


def overload_dataframe_corr(df, method='pearson', min_periods=1):
    fig__hfwch = [sijzc__erm for sijzc__erm, jyhv__ayze in zip(df.columns,
        df.data) if bodo.utils.typing._is_pandas_numeric_dtype(jyhv__ayze.
        dtype)]
    assert len(fig__hfwch) != 0
    achye__idf = ''
    if not any(jyhv__ayze == types.float64 for jyhv__ayze in df.data):
        achye__idf = '.astype(np.float64)'
    qms__fkfkr = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(df.columns.index(sijzc__erm), '.astype(np.float64)' if 
        isinstance(df.data[df.columns.index(sijzc__erm)], IntegerArrayType) or
        df.data[df.columns.index(sijzc__erm)] == boolean_array else '') for
        sijzc__erm in fig__hfwch)
    rotre__uwgch = 'np.stack(({},), 1){}'.format(qms__fkfkr, achye__idf)
    data_args = ', '.join('res[:,{}]'.format(i) for i in range(len(fig__hfwch))
        )
    index = f'{generate_col_to_index_func_text(fig__hfwch)}\n'
    header = "def impl(df, method='pearson', min_periods=1):\n"
    header += '  mat = {}\n'.format(rotre__uwgch)
    header += '  res = bodo.libs.array_kernels.nancorr(mat, 0, min_periods)\n'
    return _gen_init_df(header, fig__hfwch, data_args, index)


@lower_builtin('df.corr', DataFrameType, types.VarArg(types.Any))
def dataframe_corr_lower(context, builder, sig, args):
    impl = overload_dataframe_corr(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


@overload_method(DataFrameType, 'cov', inline='always', no_unliteral=True)
def overload_dataframe_cov(df, min_periods=None, ddof=1):
    check_runtime_cols_unsupported(df, 'DataFrame.cov()')
    gqx__cck = dict(ddof=ddof)
    syjmu__lkfvy = dict(ddof=1)
    check_unsupported_args('DataFrame.cov', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    qqnzy__oynz = '1' if is_overload_none(min_periods) else 'min_periods'
    fig__hfwch = [sijzc__erm for sijzc__erm, jyhv__ayze in zip(df.columns,
        df.data) if bodo.utils.typing._is_pandas_numeric_dtype(jyhv__ayze.
        dtype)]
    if len(fig__hfwch) == 0:
        raise_bodo_error('DataFrame.cov(): requires non-empty dataframe')
    achye__idf = ''
    if not any(jyhv__ayze == types.float64 for jyhv__ayze in df.data):
        achye__idf = '.astype(np.float64)'
    qms__fkfkr = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(df.columns.index(sijzc__erm), '.astype(np.float64)' if 
        isinstance(df.data[df.columns.index(sijzc__erm)], IntegerArrayType) or
        df.data[df.columns.index(sijzc__erm)] == boolean_array else '') for
        sijzc__erm in fig__hfwch)
    rotre__uwgch = 'np.stack(({},), 1){}'.format(qms__fkfkr, achye__idf)
    data_args = ', '.join('res[:,{}]'.format(i) for i in range(len(fig__hfwch))
        )
    index = f'pd.Index({fig__hfwch})\n'
    header = 'def impl(df, min_periods=None, ddof=1):\n'
    header += '  mat = {}\n'.format(rotre__uwgch)
    header += '  res = bodo.libs.array_kernels.nancorr(mat, 1, {})\n'.format(
        qqnzy__oynz)
    return _gen_init_df(header, fig__hfwch, data_args, index)


@overload_method(DataFrameType, 'count', inline='always', no_unliteral=True)
def overload_dataframe_count(df, axis=0, level=None, numeric_only=False):
    check_runtime_cols_unsupported(df, 'DataFrame.count()')
    gqx__cck = dict(axis=axis, level=level, numeric_only=numeric_only)
    syjmu__lkfvy = dict(axis=0, level=None, numeric_only=False)
    check_unsupported_args('DataFrame.count', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'bodo.libs.array_ops.array_op_count(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}))'
         for i in range(len(df.columns)))
    zhuuz__rnab = 'def impl(df, axis=0, level=None, numeric_only=False):\n'
    zhuuz__rnab += '  data = np.array([{}])\n'.format(data_args)
    xixpt__rgpqd = (bodo.hiframes.dataframe_impl.
        generate_col_to_index_func_text(df.columns))
    zhuuz__rnab += (
        f'  return bodo.hiframes.pd_series_ext.init_series(data, {xixpt__rgpqd})\n'
        )
    vowd__xeiyc = {}
    exec(zhuuz__rnab, {'bodo': bodo, 'np': np}, vowd__xeiyc)
    impl = vowd__xeiyc['impl']
    return impl


@overload_method(DataFrameType, 'nunique', inline='always', no_unliteral=True)
def overload_dataframe_nunique(df, axis=0, dropna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.unique()')
    gqx__cck = dict(axis=axis)
    syjmu__lkfvy = dict(axis=0)
    if not is_overload_bool(dropna):
        raise BodoError('DataFrame.nunique: dropna must be a boolean value')
    check_unsupported_args('DataFrame.nunique', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'bodo.libs.array_kernels.nunique(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), dropna)'
         for i in range(len(df.columns)))
    zhuuz__rnab = 'def impl(df, axis=0, dropna=True):\n'
    zhuuz__rnab += '  data = np.asarray(({},))\n'.format(data_args)
    xixpt__rgpqd = (bodo.hiframes.dataframe_impl.
        generate_col_to_index_func_text(df.columns))
    zhuuz__rnab += (
        f'  return bodo.hiframes.pd_series_ext.init_series(data, {xixpt__rgpqd})\n'
        )
    vowd__xeiyc = {}
    exec(zhuuz__rnab, {'bodo': bodo, 'np': np}, vowd__xeiyc)
    impl = vowd__xeiyc['impl']
    return impl


@overload_method(DataFrameType, 'prod', inline='always', no_unliteral=True)
@overload_method(DataFrameType, 'product', inline='always', no_unliteral=True)
def overload_dataframe_prod(df, axis=None, skipna=None, level=None,
    numeric_only=None, min_count=0):
    check_runtime_cols_unsupported(df, 'DataFrame.prod()')
    gqx__cck = dict(skipna=skipna, level=level, numeric_only=numeric_only,
        min_count=min_count)
    syjmu__lkfvy = dict(skipna=None, level=None, numeric_only=None, min_count=0
        )
    check_unsupported_args('DataFrame.prod', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'prod', axis=axis)


@overload_method(DataFrameType, 'sum', inline='always', no_unliteral=True)
def overload_dataframe_sum(df, axis=None, skipna=None, level=None,
    numeric_only=None, min_count=0):
    check_runtime_cols_unsupported(df, 'DataFrame.sum()')
    gqx__cck = dict(skipna=skipna, level=level, numeric_only=numeric_only,
        min_count=min_count)
    syjmu__lkfvy = dict(skipna=None, level=None, numeric_only=None, min_count=0
        )
    check_unsupported_args('DataFrame.sum', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'sum', axis=axis)


@overload_method(DataFrameType, 'max', inline='always', no_unliteral=True)
def overload_dataframe_max(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.max()')
    gqx__cck = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    syjmu__lkfvy = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.max', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'max', axis=axis)


@overload_method(DataFrameType, 'min', inline='always', no_unliteral=True)
def overload_dataframe_min(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.min()')
    gqx__cck = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    syjmu__lkfvy = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.min', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'min', axis=axis)


@overload_method(DataFrameType, 'mean', inline='always', no_unliteral=True)
def overload_dataframe_mean(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.mean()')
    gqx__cck = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    syjmu__lkfvy = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.mean', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'mean', axis=axis)


@overload_method(DataFrameType, 'var', inline='always', no_unliteral=True)
def overload_dataframe_var(df, axis=None, skipna=None, level=None, ddof=1,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.var()')
    gqx__cck = dict(skipna=skipna, level=level, ddof=ddof, numeric_only=
        numeric_only)
    syjmu__lkfvy = dict(skipna=None, level=None, ddof=1, numeric_only=None)
    check_unsupported_args('DataFrame.var', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'var', axis=axis)


@overload_method(DataFrameType, 'std', inline='always', no_unliteral=True)
def overload_dataframe_std(df, axis=None, skipna=None, level=None, ddof=1,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.std()')
    gqx__cck = dict(skipna=skipna, level=level, ddof=ddof, numeric_only=
        numeric_only)
    syjmu__lkfvy = dict(skipna=None, level=None, ddof=1, numeric_only=None)
    check_unsupported_args('DataFrame.std', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'std', axis=axis)


@overload_method(DataFrameType, 'median', inline='always', no_unliteral=True)
def overload_dataframe_median(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.median()')
    gqx__cck = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    syjmu__lkfvy = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.median', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'median', axis=axis)


@overload_method(DataFrameType, 'quantile', inline='always', no_unliteral=True)
def overload_dataframe_quantile(df, q=0.5, axis=0, numeric_only=True,
    interpolation='linear'):
    check_runtime_cols_unsupported(df, 'DataFrame.quantile()')
    gqx__cck = dict(numeric_only=numeric_only, interpolation=interpolation)
    syjmu__lkfvy = dict(numeric_only=True, interpolation='linear')
    check_unsupported_args('DataFrame.quantile', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'quantile', 'q', axis=axis)


@overload_method(DataFrameType, 'idxmax', inline='always', no_unliteral=True)
def overload_dataframe_idxmax(df, axis=0, skipna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.idxmax()')
    gqx__cck = dict(axis=axis, skipna=skipna)
    syjmu__lkfvy = dict(axis=0, skipna=True)
    check_unsupported_args('DataFrame.idxmax', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    for vfbg__axkm in df.data:
        if not (bodo.utils.utils.is_np_array_typ(vfbg__axkm) and (
            vfbg__axkm.dtype in [bodo.datetime64ns, bodo.timedelta64ns] or
            isinstance(vfbg__axkm.dtype, (types.Number, types.Boolean))) or
            isinstance(vfbg__axkm, (bodo.IntegerArrayType, bodo.
            CategoricalArrayType)) or vfbg__axkm in [bodo.boolean_array,
            bodo.datetime_date_array_type]):
            raise BodoError(
                f'DataFrame.idxmax() only supported for numeric column types. Column type: {vfbg__axkm} not supported.'
                )
        if isinstance(vfbg__axkm, bodo.CategoricalArrayType
            ) and not vfbg__axkm.dtype.ordered:
            raise BodoError(
                'DataFrame.idxmax(): categorical columns must be ordered')
    return _gen_reduce_impl(df, 'idxmax', axis=axis)


@overload_method(DataFrameType, 'idxmin', inline='always', no_unliteral=True)
def overload_dataframe_idxmin(df, axis=0, skipna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.idxmin()')
    gqx__cck = dict(axis=axis, skipna=skipna)
    syjmu__lkfvy = dict(axis=0, skipna=True)
    check_unsupported_args('DataFrame.idxmin', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    for vfbg__axkm in df.data:
        if not (bodo.utils.utils.is_np_array_typ(vfbg__axkm) and (
            vfbg__axkm.dtype in [bodo.datetime64ns, bodo.timedelta64ns] or
            isinstance(vfbg__axkm.dtype, (types.Number, types.Boolean))) or
            isinstance(vfbg__axkm, (bodo.IntegerArrayType, bodo.
            CategoricalArrayType)) or vfbg__axkm in [bodo.boolean_array,
            bodo.datetime_date_array_type]):
            raise BodoError(
                f'DataFrame.idxmin() only supported for numeric column types. Column type: {vfbg__axkm} not supported.'
                )
        if isinstance(vfbg__axkm, bodo.CategoricalArrayType
            ) and not vfbg__axkm.dtype.ordered:
            raise BodoError(
                'DataFrame.idxmin(): categorical columns must be ordered')
    return _gen_reduce_impl(df, 'idxmin', axis=axis)


@overload_method(DataFrameType, 'infer_objects', inline='always')
def overload_dataframe_infer_objects(df):
    check_runtime_cols_unsupported(df, 'DataFrame.infer_objects()')
    return lambda df: df.copy()


def _gen_reduce_impl(df, func_name, args=None, axis=None):
    args = '' if is_overload_none(args) else args
    if is_overload_none(axis):
        axis = 0
    elif is_overload_constant_int(axis):
        axis = get_overload_const_int(axis)
    else:
        raise_bodo_error(
            f'DataFrame.{func_name}: axis must be a constant Integer')
    assert axis in (0, 1), f'invalid axis argument for DataFrame.{func_name}'
    if func_name in ('idxmax', 'idxmin'):
        out_colnames = df.columns
    else:
        fig__hfwch = tuple(sijzc__erm for sijzc__erm, jyhv__ayze in zip(df.
            columns, df.data) if bodo.utils.typing._is_pandas_numeric_dtype
            (jyhv__ayze.dtype))
        out_colnames = fig__hfwch
    assert len(out_colnames) != 0
    try:
        if func_name in ('idxmax', 'idxmin') and axis == 0:
            comm_dtype = None
        else:
            obcoh__snanc = [numba.np.numpy_support.as_dtype(df.data[df.
                columns.index(sijzc__erm)].dtype) for sijzc__erm in
                out_colnames]
            comm_dtype = numba.np.numpy_support.from_dtype(np.
                find_common_type(obcoh__snanc, []))
    except NotImplementedError as yxp__zatb:
        raise BodoError(
            f'Dataframe.{func_name}() with column types: {df.data} could not be merged to a common type.'
            )
    naycy__oodur = ''
    if func_name in ('sum', 'prod'):
        naycy__oodur = ', min_count=0'
    ddof = ''
    if func_name in ('var', 'std'):
        ddof = 'ddof=1, '
    zhuuz__rnab = (
        'def impl(df, axis=None, skipna=None, level=None,{} numeric_only=None{}):\n'
        .format(ddof, naycy__oodur))
    if func_name == 'quantile':
        zhuuz__rnab = (
            "def impl(df, q=0.5, axis=0, numeric_only=True, interpolation='linear'):\n"
            )
    if func_name in ('idxmax', 'idxmin'):
        zhuuz__rnab = 'def impl(df, axis=0, skipna=True):\n'
    if axis == 0:
        zhuuz__rnab += _gen_reduce_impl_axis0(df, func_name, out_colnames,
            comm_dtype, args)
    else:
        zhuuz__rnab += _gen_reduce_impl_axis1(func_name, out_colnames,
            comm_dtype, df)
    vowd__xeiyc = {}
    exec(zhuuz__rnab, {'bodo': bodo, 'np': np, 'pd': pd, 'numba': numba},
        vowd__xeiyc)
    impl = vowd__xeiyc['impl']
    return impl


def _gen_reduce_impl_axis0(df, func_name, out_colnames, comm_dtype, args):
    plec__izitm = ''
    if func_name in ('min', 'max'):
        plec__izitm = ', dtype=np.{}'.format(comm_dtype)
    if comm_dtype == types.float32 and func_name in ('sum', 'prod', 'mean',
        'var', 'std', 'median'):
        plec__izitm = ', dtype=np.float32'
    koj__ocob = f'bodo.libs.array_ops.array_op_{func_name}'
    bfaft__rky = ''
    if func_name in ['sum', 'prod']:
        bfaft__rky = 'True, min_count'
    elif func_name in ['idxmax', 'idxmin']:
        bfaft__rky = 'index'
    elif func_name == 'quantile':
        bfaft__rky = 'q'
    elif func_name in ['std', 'var']:
        bfaft__rky = 'True, ddof'
    elif func_name == 'median':
        bfaft__rky = 'True'
    data_args = ', '.join(
        f'{koj__ocob}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(sijzc__erm)}), {bfaft__rky})'
         for sijzc__erm in out_colnames)
    zhuuz__rnab = ''
    if func_name in ('idxmax', 'idxmin'):
        zhuuz__rnab += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
            )
        zhuuz__rnab += (
            '  data = bodo.utils.conversion.coerce_to_array(({},))\n'.
            format(data_args))
    else:
        zhuuz__rnab += '  data = np.asarray(({},){})\n'.format(data_args,
            plec__izitm)
    zhuuz__rnab += f"""  return bodo.hiframes.pd_series_ext.init_series(data, pd.Index({out_colnames}))
"""
    return zhuuz__rnab


def _gen_reduce_impl_axis1(func_name, out_colnames, comm_dtype, df_type):
    czql__mkwi = [df_type.columns.index(sijzc__erm) for sijzc__erm in
        out_colnames]
    index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
    data_args = '\n    '.join(
        'arr_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})'
        .format(i) for i in czql__mkwi)
    fpcu__xeo = '\n        '.join(f'row[{i}] = arr_{czql__mkwi[i]}[i]' for
        i in range(len(out_colnames)))
    assert len(data_args) > 0, f'empty dataframe in DataFrame.{func_name}()'
    kwweo__was = f'len(arr_{czql__mkwi[0]})'
    dug__ziudu = {'max': 'np.nanmax', 'min': 'np.nanmin', 'sum':
        'np.nansum', 'prod': 'np.nanprod', 'mean': 'np.nanmean', 'median':
        'np.nanmedian', 'var': 'bodo.utils.utils.nanvar_ddof1', 'std':
        'bodo.utils.utils.nanstd_ddof1'}
    if func_name in dug__ziudu:
        idzgd__jqxo = dug__ziudu[func_name]
        etf__edpa = 'float64' if func_name in ['mean', 'median', 'std', 'var'
            ] else comm_dtype
        zhuuz__rnab = f"""
    {data_args}
    numba.parfors.parfor.init_prange()
    n = {kwweo__was}
    row = np.empty({len(out_colnames)}, np.{comm_dtype})
    A = np.empty(n, np.{etf__edpa})
    for i in numba.parfors.parfor.internal_prange(n):
        {fpcu__xeo}
        A[i] = {idzgd__jqxo}(row)
    return bodo.hiframes.pd_series_ext.init_series(A, {index})
"""
        return zhuuz__rnab
    else:
        raise BodoError(f'DataFrame.{func_name}(): Not supported for axis=1')


@overload_method(DataFrameType, 'pct_change', inline='always', no_unliteral
    =True)
def overload_dataframe_pct_change(df, periods=1, fill_method='pad', limit=
    None, freq=None):
    check_runtime_cols_unsupported(df, 'DataFrame.pct_change()')
    gqx__cck = dict(fill_method=fill_method, limit=limit, freq=freq)
    syjmu__lkfvy = dict(fill_method='pad', limit=None, freq=None)
    check_unsupported_args('DataFrame.pct_change', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'bodo.hiframes.rolling.pct_change(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), periods, False)'
         for i in range(len(df.columns)))
    header = (
        "def impl(df, periods=1, fill_method='pad', limit=None, freq=None):\n")
    return _gen_init_df(header, df.columns, data_args)


@overload_method(DataFrameType, 'cumprod', inline='always', no_unliteral=True)
def overload_dataframe_cumprod(df, axis=None, skipna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.cumprod()')
    gqx__cck = dict(axis=axis, skipna=skipna)
    syjmu__lkfvy = dict(axis=None, skipna=True)
    check_unsupported_args('DataFrame.cumprod', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).cumprod()'
         for i in range(len(df.columns)))
    header = 'def impl(df, axis=None, skipna=True):\n'
    return _gen_init_df(header, df.columns, data_args)


@overload_method(DataFrameType, 'cumsum', inline='always', no_unliteral=True)
def overload_dataframe_cumsum(df, axis=None, skipna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.cumsum()')
    gqx__cck = dict(skipna=skipna)
    syjmu__lkfvy = dict(skipna=True)
    check_unsupported_args('DataFrame.cumsum', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).cumsum()'
         for i in range(len(df.columns)))
    header = 'def impl(df, axis=None, skipna=True):\n'
    return _gen_init_df(header, df.columns, data_args)


def _is_describe_type(data):
    return isinstance(data, IntegerArrayType) or isinstance(data, types.Array
        ) and isinstance(data.dtype, types.Number
        ) or data.dtype == bodo.datetime64ns


@overload_method(DataFrameType, 'describe', inline='always', no_unliteral=True)
def overload_dataframe_describe(df, percentiles=None, include=None, exclude
    =None, datetime_is_numeric=True):
    check_runtime_cols_unsupported(df, 'DataFrame.describe()')
    gqx__cck = dict(percentiles=percentiles, include=include, exclude=
        exclude, datetime_is_numeric=datetime_is_numeric)
    syjmu__lkfvy = dict(percentiles=None, include=None, exclude=None,
        datetime_is_numeric=True)
    check_unsupported_args('DataFrame.describe', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    fig__hfwch = [sijzc__erm for sijzc__erm, jyhv__ayze in zip(df.columns,
        df.data) if _is_describe_type(jyhv__ayze)]
    if len(fig__hfwch) == 0:
        raise BodoError('df.describe() only supports numeric columns')
    nsb__bjrmh = sum(df.data[df.columns.index(sijzc__erm)].dtype == bodo.
        datetime64ns for sijzc__erm in fig__hfwch)

    def _get_describe(col_ind):
        mkt__lejew = df.data[col_ind].dtype == bodo.datetime64ns
        if nsb__bjrmh and nsb__bjrmh != len(fig__hfwch):
            if mkt__lejew:
                return f'des_{col_ind} + (np.nan,)'
            return (
                f'des_{col_ind}[:2] + des_{col_ind}[3:] + (des_{col_ind}[2],)')
        return f'des_{col_ind}'
    header = """def impl(df, percentiles=None, include=None, exclude=None, datetime_is_numeric=True):
"""
    for sijzc__erm in fig__hfwch:
        col_ind = df.columns.index(sijzc__erm)
        header += f"""  des_{col_ind} = bodo.libs.array_ops.array_op_describe(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {col_ind}))
"""
    data_args = ', '.join(_get_describe(df.columns.index(sijzc__erm)) for
        sijzc__erm in fig__hfwch)
    ntnko__vnxwu = (
        "['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']")
    if nsb__bjrmh == len(fig__hfwch):
        ntnko__vnxwu = "['count', 'mean', 'min', '25%', '50%', '75%', 'max']"
    elif nsb__bjrmh:
        ntnko__vnxwu = (
            "['count', 'mean', 'min', '25%', '50%', '75%', 'max', 'std']")
    index = f'bodo.utils.conversion.convert_to_index({ntnko__vnxwu})'
    return _gen_init_df(header, fig__hfwch, data_args, index)


@overload_method(DataFrameType, 'take', inline='always', no_unliteral=True)
def overload_dataframe_take(df, indices, axis=0, convert=None, is_copy=True):
    check_runtime_cols_unsupported(df, 'DataFrame.take()')
    gqx__cck = dict(axis=axis, convert=convert, is_copy=is_copy)
    syjmu__lkfvy = dict(axis=0, convert=None, is_copy=True)
    check_unsupported_args('DataFrame.take', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    data_args = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})[indices_t]'
        .format(i) for i in range(len(df.columns)))
    header = 'def impl(df, indices, axis=0, convert=None, is_copy=True):\n'
    header += (
        '  indices_t = bodo.utils.conversion.coerce_to_ndarray(indices)\n')
    index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[indices_t]'
    return _gen_init_df(header, df.columns, data_args, index)


@overload_method(DataFrameType, 'shift', inline='always', no_unliteral=True)
def overload_dataframe_shift(df, periods=1, freq=None, axis=0, fill_value=None
    ):
    check_runtime_cols_unsupported(df, 'DataFrame.shift()')
    gqx__cck = dict(freq=freq, axis=axis, fill_value=fill_value)
    syjmu__lkfvy = dict(freq=None, axis=0, fill_value=None)
    check_unsupported_args('DataFrame.shift', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    for lye__vsgbo in df.data:
        if not is_supported_shift_array_type(lye__vsgbo):
            raise BodoError(
                f'Dataframe.shift() column input type {lye__vsgbo.dtype} not supported yet.'
                )
    if not is_overload_int(periods):
        raise BodoError(
            "DataFrame.shift(): 'periods' input must be an integer.")
    data_args = ', '.join(
        f'bodo.hiframes.rolling.shift(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), periods, False)'
         for i in range(len(df.columns)))
    header = 'def impl(df, periods=1, freq=None, axis=0, fill_value=None):\n'
    return _gen_init_df(header, df.columns, data_args)


@overload_method(DataFrameType, 'diff', inline='always', no_unliteral=True)
def overload_dataframe_diff(df, periods=1, axis=0):
    check_runtime_cols_unsupported(df, 'DataFrame.diff()')
    gqx__cck = dict(axis=axis)
    syjmu__lkfvy = dict(axis=0)
    check_unsupported_args('DataFrame.diff', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    for lye__vsgbo in df.data:
        if not (isinstance(lye__vsgbo, types.Array) and (isinstance(
            lye__vsgbo.dtype, types.Number) or lye__vsgbo.dtype == bodo.
            datetime64ns)):
            raise BodoError(
                f'DataFrame.diff() column input type {lye__vsgbo.dtype} not supported.'
                )
    if not is_overload_int(periods):
        raise BodoError("DataFrame.diff(): 'periods' input must be an integer."
            )
    header = 'def impl(df, periods=1, axis= 0):\n'
    for i in range(len(df.columns)):
        header += (
            f'  data_{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})\n'
            )
    data_args = ', '.join(
        f'bodo.hiframes.series_impl.dt64_arr_sub(data_{i}, bodo.hiframes.rolling.shift(data_{i}, periods, False))'
         if df.data[i] == types.Array(bodo.datetime64ns, 1, 'C') else
        f'data_{i} - bodo.hiframes.rolling.shift(data_{i}, periods, False)' for
        i in range(len(df.columns)))
    return _gen_init_df(header, df.columns, data_args)


@overload_method(DataFrameType, 'explode', inline='always', no_unliteral=True)
def overload_dataframe_explode(df, column, ignore_index=False):
    bba__nyr = (
        "DataFrame.explode(): 'column' must a constant label or list of labels"
        )
    if not is_literal_type(column):
        raise_bodo_error(bba__nyr)
    if is_overload_constant_list(column) or is_overload_constant_tuple(column):
        qfhcj__bbz = get_overload_const_list(column)
    else:
        qfhcj__bbz = [get_literal_value(column)]
    jqph__lwiif = {sijzc__erm: i for i, sijzc__erm in enumerate(df.columns)}
    zrjin__irpys = [jqph__lwiif[sijzc__erm] for sijzc__erm in qfhcj__bbz]
    for i in zrjin__irpys:
        if not isinstance(df.data[i], ArrayItemArrayType) and df.data[i
            ].dtype != string_array_split_view_type:
            raise BodoError(
                f'DataFrame.explode(): columns must have array-like entries')
    n = len(df.columns)
    header = 'def impl(df, column, ignore_index=False):\n'
    header += (
        '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n')
    header += '  index_arr = bodo.utils.conversion.index_to_array(index)\n'
    for i in range(n):
        header += (
            f'  data{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})\n'
            )
    header += (
        f'  counts = bodo.libs.array_kernels.get_arr_lens(data{zrjin__irpys[0]})\n'
        )
    for i in range(n):
        if i in zrjin__irpys:
            header += (
                f'  out_data{i} = bodo.libs.array_kernels.explode_no_index(data{i}, counts)\n'
                )
        else:
            header += (
                f'  out_data{i} = bodo.libs.array_kernels.repeat_kernel(data{i}, counts)\n'
                )
    header += (
        '  new_index = bodo.libs.array_kernels.repeat_kernel(index_arr, counts)\n'
        )
    data_args = ', '.join(f'out_data{i}' for i in range(n))
    index = 'bodo.utils.conversion.convert_to_index(new_index)'
    return _gen_init_df(header, df.columns, data_args, index)


@overload_method(DataFrameType, 'set_index', inline='always', no_unliteral=True
    )
def overload_dataframe_set_index(df, keys, drop=True, append=False, inplace
    =False, verify_integrity=False):
    check_runtime_cols_unsupported(df, 'DataFrame.set_index()')
    bxk__ruyqa = {'inplace': inplace, 'append': append, 'verify_integrity':
        verify_integrity}
    fyzts__uqjd = {'inplace': False, 'append': False, 'verify_integrity': False
        }
    check_unsupported_args('DataFrame.set_index', bxk__ruyqa, fyzts__uqjd,
        package_name='pandas', module_name='DataFrame')
    if not is_overload_constant_str(keys):
        raise_bodo_error(
            "DataFrame.set_index(): 'keys' must be a constant string")
    col_name = get_overload_const_str(keys)
    col_ind = df.columns.index(col_name)
    header = """def impl(df, keys, drop=True, append=False, inplace=False, verify_integrity=False):
"""
    data_args = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})'.format(
        i) for i in range(len(df.columns)) if i != col_ind)
    columns = tuple(sijzc__erm for sijzc__erm in df.columns if sijzc__erm !=
        col_name)
    index = (
        'bodo.utils.conversion.index_from_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}), {})'
        .format(col_ind, f"'{col_name}'" if isinstance(col_name, str) else
        col_name))
    return _gen_init_df(header, columns, data_args, index)


@overload_method(DataFrameType, 'query', no_unliteral=True)
def overload_dataframe_query(df, expr, inplace=False):
    check_runtime_cols_unsupported(df, 'DataFrame.query()')
    bxk__ruyqa = {'inplace': inplace}
    fyzts__uqjd = {'inplace': False}
    check_unsupported_args('query', bxk__ruyqa, fyzts__uqjd, package_name=
        'pandas', module_name='DataFrame')
    if not isinstance(expr, (types.StringLiteral, types.UnicodeType)):
        raise BodoError('query(): expr argument should be a string')

    def impl(df, expr, inplace=False):
        ikn__xbxtx = bodo.hiframes.pd_dataframe_ext.query_dummy(df, expr)
        return df[ikn__xbxtx]
    return impl


@overload_method(DataFrameType, 'duplicated', inline='always', no_unliteral
    =True)
def overload_dataframe_duplicated(df, subset=None, keep='first'):
    check_runtime_cols_unsupported(df, 'DataFrame.duplicated()')
    bxk__ruyqa = {'subset': subset, 'keep': keep}
    fyzts__uqjd = {'subset': None, 'keep': 'first'}
    check_unsupported_args('DataFrame.duplicated', bxk__ruyqa, fyzts__uqjd,
        package_name='pandas', module_name='DataFrame')
    fji__ulh = len(df.columns)
    zhuuz__rnab = "def impl(df, subset=None, keep='first'):\n"
    for i in range(fji__ulh):
        zhuuz__rnab += (
            '  data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})\n'
            .format(i))
    valwk__bjdje = ', '.join(f'data_{i}' for i in range(fji__ulh))
    valwk__bjdje += ',' if fji__ulh == 1 else ''
    zhuuz__rnab += (
        f'  duplicated = bodo.libs.array_kernels.duplicated(({valwk__bjdje}))\n'
        )
    zhuuz__rnab += (
        '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n')
    zhuuz__rnab += (
        '  return bodo.hiframes.pd_series_ext.init_series(duplicated, index)\n'
        )
    vowd__xeiyc = {}
    exec(zhuuz__rnab, {'bodo': bodo}, vowd__xeiyc)
    impl = vowd__xeiyc['impl']
    return impl


@overload_method(DataFrameType, 'drop_duplicates', inline='always',
    no_unliteral=True)
def overload_dataframe_drop_duplicates(df, subset=None, keep='first',
    inplace=False, ignore_index=False):
    check_runtime_cols_unsupported(df, 'DataFrame.drop_duplicates()')
    bxk__ruyqa = {'keep': keep, 'inplace': inplace, 'ignore_index':
        ignore_index}
    fyzts__uqjd = {'keep': 'first', 'inplace': False, 'ignore_index': False}
    haiks__zay = []
    if is_overload_constant_list(subset):
        haiks__zay = get_overload_const_list(subset)
    elif is_overload_constant_str(subset):
        haiks__zay = [get_overload_const_str(subset)]
    elif is_overload_constant_int(subset):
        haiks__zay = [get_overload_const_int(subset)]
    elif not is_overload_none(subset):
        raise_bodo_error(
            'DataFrame.drop_duplicates(): subset must be a constant column name, constant list of column names or None'
            )
    yghkw__qxr = []
    for col_name in haiks__zay:
        if col_name not in df.columns:
            raise BodoError(
                'DataFrame.drop_duplicates(): All subset columns must be found in the DataFrame.'
                 +
                f'Column {col_name} not found in DataFrame columns {df.columns}'
                )
        yghkw__qxr.append(df.columns.index(col_name))
    check_unsupported_args('DataFrame.drop_duplicates', bxk__ruyqa,
        fyzts__uqjd, package_name='pandas', module_name='DataFrame')
    sfg__iyj = []
    if yghkw__qxr:
        for ipsu__pmg in yghkw__qxr:
            if isinstance(df.data[ipsu__pmg], bodo.MapArrayType):
                sfg__iyj.append(df.columns[ipsu__pmg])
    else:
        for i, col_name in enumerate(df.columns):
            if isinstance(df.data[i], bodo.MapArrayType):
                sfg__iyj.append(col_name)
    if sfg__iyj:
        raise BodoError(f'DataFrame.drop_duplicates(): Columns {sfg__iyj} ' +
            f'have dictionary types which cannot be used to drop duplicates. '
             +
            "Please consider using the 'subset' argument to skip these columns."
            )
    fji__ulh = len(df.columns)
    cxpha__lvntb = ['data_{}'.format(i) for i in yghkw__qxr]
    qbxnd__xxye = ['data_{}'.format(i) for i in range(fji__ulh) if i not in
        yghkw__qxr]
    if cxpha__lvntb:
        mmij__hxwy = len(cxpha__lvntb)
    else:
        mmij__hxwy = fji__ulh
    kggp__asjnf = ', '.join(cxpha__lvntb + qbxnd__xxye)
    data_args = ', '.join('data_{}'.format(i) for i in range(fji__ulh))
    zhuuz__rnab = (
        "def impl(df, subset=None, keep='first', inplace=False, ignore_index=False):\n"
        )
    for i in range(fji__ulh):
        zhuuz__rnab += (
            '  data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})\n'
            .format(i))
    index = (
        'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
        )
    zhuuz__rnab += (
        """  ({0},), index_arr = bodo.libs.array_kernels.drop_duplicates(({0},), {1}, {2})
"""
        .format(kggp__asjnf, index, mmij__hxwy))
    zhuuz__rnab += (
        '  index = bodo.utils.conversion.index_from_array(index_arr)\n')
    return _gen_init_df(zhuuz__rnab, df.columns, data_args, 'index')


def create_dataframe_mask_where_overload(func_name):

    def overload_dataframe_mask_where(df, cond, other=np.nan, inplace=False,
        axis=None, level=None, errors='raise', try_cast=False):
        _validate_arguments_mask_where(f'DataFrame.{func_name}', df, cond,
            other, inplace, axis, level, errors, try_cast)
        header = """def impl(df, cond, other=np.nan, inplace=False, axis=None, level=None, errors='raise', try_cast=False):
"""
        if func_name == 'mask':
            header += '  cond = ~cond\n'
        gen_all_false = [False]
        if cond.ndim == 1:
            cond_str = lambda i, _: 'cond'
        elif cond.ndim == 2:
            if isinstance(cond, DataFrameType):
                gxl__ydihz = {sijzc__erm: i for i, sijzc__erm in enumerate(
                    cond.columns)}

                def cond_str(i, gen_all_false):
                    if df.columns[i] in gxl__ydihz:
                        return (
                            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(cond, {gxl__ydihz[df.columns[i]]})'
                            )
                    else:
                        gen_all_false[0] = True
                        return 'all_false'
            elif isinstance(cond, types.Array):
                cond_str = lambda i, _: f'cond[:,{i}]'
        if not hasattr(other, 'ndim') or other.ndim == 1:
            auos__hxng = lambda i: 'other'
        elif other.ndim == 2:
            if isinstance(other, DataFrameType):
                other_map = {sijzc__erm: i for i, sijzc__erm in enumerate(
                    other.columns)}
                auos__hxng = (lambda i: 
                    f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(other, {other_map[df.columns[i]]})'
                     if df.columns[i] in other_map else 'None')
            elif isinstance(other, types.Array):
                auos__hxng = lambda i: f'other[:,{i}]'
        fji__ulh = len(df.columns)
        data_args = ', '.join(
            f'bodo.hiframes.series_impl.where_impl({cond_str(i, gen_all_false)}, bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), {auos__hxng(i)})'
             for i in range(fji__ulh))
        if gen_all_false[0]:
            header += '  all_false = np.zeros(len(df), dtype=bool)\n'
        return _gen_init_df(header, df.columns, data_args)
    return overload_dataframe_mask_where


def _install_dataframe_mask_where_overload():
    for func_name in ('mask', 'where'):
        fbul__ncy = create_dataframe_mask_where_overload(func_name)
        overload_method(DataFrameType, func_name, no_unliteral=True)(fbul__ncy)


_install_dataframe_mask_where_overload()


def _validate_arguments_mask_where(func_name, df, cond, other, inplace,
    axis, level, errors, try_cast):
    gqx__cck = dict(inplace=inplace, level=level, errors=errors, try_cast=
        try_cast)
    syjmu__lkfvy = dict(inplace=False, level=None, errors='raise', try_cast
        =False)
    check_unsupported_args(f'{func_name}', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise_bodo_error(f'{func_name}(): axis argument not supported')
    if not (isinstance(cond, (SeriesType, types.Array, BooleanArrayType)) and
        (cond.ndim == 1 or cond.ndim == 2) and cond.dtype == types.bool_
        ) and not (isinstance(cond, DataFrameType) and cond.ndim == 2 and
        all(cond.data[i].dtype == types.bool_ for i in range(len(df.columns)))
        ):
        raise BodoError(
            f"{func_name}(): 'cond' argument must be a DataFrame, Series, 1- or 2-dimensional array of booleans"
            )
    fji__ulh = len(df.columns)
    if hasattr(other, 'ndim') and (other.ndim != 1 or other.ndim != 2):
        if other.ndim == 2:
            if not isinstance(other, (DataFrameType, types.Array)):
                raise BodoError(
                    f"{func_name}(): 'other', if 2-dimensional, must be a DataFrame or array."
                    )
        elif other.ndim != 1:
            raise BodoError(
                f"{func_name}(): 'other' must be either 1 or 2-dimensional")
    if isinstance(other, DataFrameType):
        other_map = {sijzc__erm: i for i, sijzc__erm in enumerate(other.
            columns)}
        for i in range(fji__ulh):
            if df.columns[i] in other_map:
                bodo.hiframes.series_impl._validate_self_other_mask_where(
                    func_name, df.data[i], other.data[other_map[df.columns[i]]]
                    )
            else:
                bodo.hiframes.series_impl._validate_self_other_mask_where(
                    func_name, df.data[i], None, is_default=True)
    elif isinstance(other, SeriesType):
        for i in range(fji__ulh):
            bodo.hiframes.series_impl._validate_self_other_mask_where(func_name
                , df.data[i], other.data)
    else:
        for i in range(fji__ulh):
            bodo.hiframes.series_impl._validate_self_other_mask_where(func_name
                , df.data[i], other, max_ndim=2)


def _gen_init_df(header, columns, data_args, index=None, extra_globals=None,
    out_df_type=None):
    if index is None:
        index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
    if extra_globals is None:
        extra_globals = {}
    if out_df_type is not None:
        extra_globals['out_df_type'] = out_df_type
        xjol__duc = 'out_df_type'
    else:
        xjol__duc = gen_const_tup(columns)
    data_args = '({}{})'.format(data_args, ',' if data_args else '')
    zhuuz__rnab = f"""{header}  return bodo.hiframes.pd_dataframe_ext.init_dataframe({data_args}, {index}, {xjol__duc})
"""
    vowd__xeiyc = {}
    uupr__kqpz = {'bodo': bodo, 'np': np, 'pd': pd, 'numba': numba}
    uupr__kqpz.update(extra_globals)
    exec(zhuuz__rnab, uupr__kqpz, vowd__xeiyc)
    impl = vowd__xeiyc['impl']
    return impl


def _get_binop_columns(lhs, rhs, is_inplace=False):
    if lhs.columns != rhs.columns:
        usysa__igiy = pd.Index(lhs.columns)
        earl__nzn = pd.Index(rhs.columns)
        map__jno, gmndb__mbxsm, rui__lbgi = usysa__igiy.join(earl__nzn, how
            ='left' if is_inplace else 'outer', level=None, return_indexers
            =True)
        return tuple(map__jno), gmndb__mbxsm, rui__lbgi
    return lhs.columns, range(len(lhs.columns)), range(len(lhs.columns))


def create_binary_op_overload(op):

    def overload_dataframe_binary_op(lhs, rhs):
        gltq__prgll = numba.core.utils.OPERATORS_TO_BUILTINS[op]
        wva__ansqr = operator.eq, operator.ne
        check_runtime_cols_unsupported(lhs, gltq__prgll)
        check_runtime_cols_unsupported(rhs, gltq__prgll)
        if isinstance(lhs, DataFrameType):
            if isinstance(rhs, DataFrameType):
                map__jno, gmndb__mbxsm, rui__lbgi = _get_binop_columns(lhs, rhs
                    )
                data_args = ', '.join(
                    f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(lhs, {nck__goqsz}) {gltq__prgll}bodo.hiframes.pd_dataframe_ext.get_dataframe_data(rhs, {hzt__mepa})'
                     if nck__goqsz != -1 and hzt__mepa != -1 else
                    f'bodo.libs.array_kernels.gen_na_array(len(lhs), float64_arr_type)'
                     for nck__goqsz, hzt__mepa in zip(gmndb__mbxsm, rui__lbgi))
                header = 'def impl(lhs, rhs):\n'
                index = (
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(lhs)')
                return _gen_init_df(header, map__jno, data_args, index,
                    extra_globals={'float64_arr_type': types.Array(types.
                    float64, 1, 'C')})
            qun__texc = []
            kivk__uvat = []
            if op in wva__ansqr:
                for i, ewtur__ysq in enumerate(lhs.data):
                    if is_common_scalar_dtype([ewtur__ysq.dtype, rhs]):
                        qun__texc.append(
                            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(lhs, {i}) {gltq__prgll} rhs'
                            )
                    else:
                        keyu__ugw = f'arr{i}'
                        kivk__uvat.append(keyu__ugw)
                        qun__texc.append(keyu__ugw)
                data_args = ', '.join(qun__texc)
            else:
                data_args = ', '.join(
                    f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(lhs, {i}) {gltq__prgll} rhs'
                     for i in range(len(lhs.columns)))
            header = 'def impl(lhs, rhs):\n'
            if len(kivk__uvat) > 0:
                header += '  numba.parfors.parfor.init_prange()\n'
                header += '  n = len(lhs)\n'
                header += ''.join(
                    f'  {keyu__ugw} = np.empty(n, dtype=np.bool_)\n' for
                    keyu__ugw in kivk__uvat)
                header += (
                    '  for i in numba.parfors.parfor.internal_prange(n):\n')
                header += ''.join('    {0}[i] = {1}\n'.format(keyu__ugw, op ==
                    operator.ne) for keyu__ugw in kivk__uvat)
            index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(lhs)'
            return _gen_init_df(header, lhs.columns, data_args, index)
        if isinstance(rhs, DataFrameType):
            qun__texc = []
            kivk__uvat = []
            if op in wva__ansqr:
                for i, ewtur__ysq in enumerate(rhs.data):
                    if is_common_scalar_dtype([lhs, ewtur__ysq.dtype]):
                        qun__texc.append(
                            f'lhs {gltq__prgll} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(rhs, {i})'
                            )
                    else:
                        keyu__ugw = f'arr{i}'
                        kivk__uvat.append(keyu__ugw)
                        qun__texc.append(keyu__ugw)
                data_args = ', '.join(qun__texc)
            else:
                data_args = ', '.join(
                    'lhs {1} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(rhs, {0})'
                    .format(i, gltq__prgll) for i in range(len(rhs.columns)))
            header = 'def impl(lhs, rhs):\n'
            if len(kivk__uvat) > 0:
                header += '  numba.parfors.parfor.init_prange()\n'
                header += '  n = len(rhs)\n'
                header += ''.join('  {0} = np.empty(n, dtype=np.bool_)\n'.
                    format(keyu__ugw) for keyu__ugw in kivk__uvat)
                header += (
                    '  for i in numba.parfors.parfor.internal_prange(n):\n')
                header += ''.join('    {0}[i] = {1}\n'.format(keyu__ugw, op ==
                    operator.ne) for keyu__ugw in kivk__uvat)
            index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(rhs)'
            return _gen_init_df(header, rhs.columns, data_args, index)
    return overload_dataframe_binary_op


skips = [operator.lt, operator.le, operator.eq, operator.ne, operator.gt,
    operator.ge, operator.add, operator.sub, operator.mul, operator.truediv,
    operator.floordiv, operator.pow, operator.mod]


def _install_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_binary_ops:
        if op in skips:
            continue
        fbul__ncy = create_binary_op_overload(op)
        overload(op)(fbul__ncy)


_install_binary_ops()


def create_inplace_binary_op_overload(op):

    def overload_dataframe_inplace_binary_op(left, right):
        gltq__prgll = numba.core.utils.OPERATORS_TO_BUILTINS[op]
        check_runtime_cols_unsupported(left, gltq__prgll)
        check_runtime_cols_unsupported(right, gltq__prgll)
        if isinstance(left, DataFrameType):
            if isinstance(right, DataFrameType):
                map__jno, _, rui__lbgi = _get_binop_columns(left, right, True)
                zhuuz__rnab = 'def impl(left, right):\n'
                for i, hzt__mepa in enumerate(rui__lbgi):
                    if hzt__mepa == -1:
                        zhuuz__rnab += f"""  df_arr{i} = bodo.libs.array_kernels.gen_na_array(len(left), float64_arr_type)
"""
                        continue
                    zhuuz__rnab += f"""  df_arr{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(left, {i})
"""
                    zhuuz__rnab += f"""  df_arr{i} {gltq__prgll} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(right, {hzt__mepa})
"""
                data_args = ', '.join(f'df_arr{i}' for i in range(len(
                    map__jno)))
                index = (
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(left)')
                return _gen_init_df(zhuuz__rnab, map__jno, data_args, index,
                    extra_globals={'float64_arr_type': types.Array(types.
                    float64, 1, 'C')})
            zhuuz__rnab = 'def impl(left, right):\n'
            for i in range(len(left.columns)):
                zhuuz__rnab += (
                    """  df_arr{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(left, {0})
"""
                    .format(i))
                zhuuz__rnab += '  df_arr{0} {1} right\n'.format(i, gltq__prgll)
            data_args = ', '.join('df_arr{}'.format(i) for i in range(len(
                left.columns)))
            index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(left)'
            return _gen_init_df(zhuuz__rnab, left.columns, data_args, index)
    return overload_dataframe_inplace_binary_op


def _install_inplace_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_inplace_binary_ops:
        fbul__ncy = create_inplace_binary_op_overload(op)
        overload(op, no_unliteral=True)(fbul__ncy)


_install_inplace_binary_ops()


def create_unary_op_overload(op):

    def overload_dataframe_unary_op(df):
        if isinstance(df, DataFrameType):
            gltq__prgll = numba.core.utils.OPERATORS_TO_BUILTINS[op]
            check_runtime_cols_unsupported(df, gltq__prgll)
            data_args = ', '.join(
                '{1} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})'
                .format(i, gltq__prgll) for i in range(len(df.columns)))
            header = 'def impl(df):\n'
            return _gen_init_df(header, df.columns, data_args)
    return overload_dataframe_unary_op


def _install_unary_ops():
    for op in bodo.hiframes.pd_series_ext.series_unary_ops:
        fbul__ncy = create_unary_op_overload(op)
        overload(op, no_unliteral=True)(fbul__ncy)


_install_unary_ops()


def overload_isna(obj):
    check_runtime_cols_unsupported(obj, 'pd.isna()')
    if isinstance(obj, (DataFrameType, SeriesType)
        ) or bodo.hiframes.pd_index_ext.is_pd_index_type(obj):
        return lambda obj: obj.isna()
    if is_array_typ(obj):

        def impl(obj):
            numba.parfors.parfor.init_prange()
            n = len(obj)
            hvroy__kuf = np.empty(n, np.bool_)
            for i in numba.parfors.parfor.internal_prange(n):
                hvroy__kuf[i] = bodo.libs.array_kernels.isna(obj, i)
            return hvroy__kuf
        return impl


overload(pd.isna, inline='always')(overload_isna)
overload(pd.isnull, inline='always')(overload_isna)


@overload(pd.isna)
@overload(pd.isnull)
def overload_isna_scalar(obj):
    if isinstance(obj, (DataFrameType, SeriesType)
        ) or bodo.hiframes.pd_index_ext.is_pd_index_type(obj) or is_array_typ(
        obj):
        return
    if isinstance(obj, (types.List, types.UniTuple)):

        def impl(obj):
            n = len(obj)
            hvroy__kuf = np.empty(n, np.bool_)
            for i in range(n):
                hvroy__kuf[i] = pd.isna(obj[i])
            return hvroy__kuf
        return impl
    obj = types.unliteral(obj)
    if obj == bodo.string_type:
        return lambda obj: unliteral_val(False)
    if isinstance(obj, types.Integer):
        return lambda obj: unliteral_val(False)
    if isinstance(obj, types.Float):
        return lambda obj: np.isnan(obj)
    if isinstance(obj, (types.NPDatetime, types.NPTimedelta)):
        return lambda obj: np.isnat(obj)
    if obj == types.none:
        return lambda obj: unliteral_val(True)
    if obj == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
        return lambda obj: np.isnat(bodo.hiframes.pd_timestamp_ext.
            integer_to_dt64(obj.value))
    if obj == bodo.hiframes.datetime_timedelta_ext.pd_timedelta_type:
        return lambda obj: np.isnat(bodo.hiframes.pd_timestamp_ext.
            integer_to_timedelta64(obj.value))
    if isinstance(obj, types.Optional):
        return lambda obj: obj is None
    return lambda obj: unliteral_val(False)


@overload(operator.setitem, no_unliteral=True)
def overload_setitem_arr_none(A, idx, val):
    if is_array_typ(A, False) and isinstance(idx, types.Integer
        ) and val == types.none:
        return lambda A, idx, val: bodo.libs.array_kernels.setna(A, idx)


def overload_notna(obj):
    check_runtime_cols_unsupported(obj, 'pd.notna()')
    if isinstance(obj, (DataFrameType, SeriesType)):
        return lambda obj: obj.notna()
    if isinstance(obj, (types.List, types.UniTuple)) or is_array_typ(obj,
        include_index_series=True):
        return lambda obj: ~pd.isna(obj)
    return lambda obj: not pd.isna(obj)


overload(pd.notna, inline='always', no_unliteral=True)(overload_notna)
overload(pd.notnull, inline='always', no_unliteral=True)(overload_notna)


def _get_pd_dtype_str(t):
    if t.dtype == types.NPDatetime('ns'):
        return "'datetime64[ns]'"
    return bodo.ir.csv_ext._get_pd_dtype_str(t)


@overload_method(DataFrameType, 'replace', inline='always', no_unliteral=True)
def overload_dataframe_replace(df, to_replace=None, value=None, inplace=
    False, limit=None, regex=False, method='pad'):
    check_runtime_cols_unsupported(df, 'DataFrame.replace()')
    if is_overload_none(to_replace):
        raise BodoError('replace(): to_replace value of None is not supported')
    bxk__ruyqa = {'inplace': inplace, 'limit': limit, 'regex': regex,
        'method': method}
    fyzts__uqjd = {'inplace': False, 'limit': None, 'regex': False,
        'method': 'pad'}
    check_unsupported_args('replace', bxk__ruyqa, fyzts__uqjd, package_name
        ='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'df.iloc[:, {i}].replace(to_replace, value).values' for i in range
        (len(df.columns)))
    header = """def impl(df, to_replace=None, value=None, inplace=False, limit=None, regex=False, method='pad'):
"""
    return _gen_init_df(header, df.columns, data_args)


def _is_col_access(expr_node):
    hmv__puuit = str(expr_node)
    return hmv__puuit.startswith('left.') or hmv__puuit.startswith('right.')


def _insert_NA_cond(expr_node, left_columns, left_data, right_columns,
    right_data):
    ocm__kywg = {'left': 0, 'right': 0, 'NOT_NA': 0}
    env = pd.core.computation.scope.ensure_scope(2, {}, {}, (ocm__kywg,))
    trf__eunga = pd.core.computation.parsing.clean_column_name

    def append_null_checks(expr_node, null_set):
        if not null_set:
            return expr_node
        yfq__mue = ' & '.join([('NOT_NA.`' + x + '`') for x in null_set])
        npiwr__jxhx = {('NOT_NA', trf__eunga(ewtur__ysq)): ewtur__ysq for
            ewtur__ysq in null_set}
        jsba__ved, _, _ = _parse_query_expr(yfq__mue, env, [], [], None,
            join_cleaned_cols=npiwr__jxhx)
        ywj__sfk = pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops
        pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops = (lambda
            self: None)
        try:
            rzi__ipzz = pd.core.computation.ops.BinOp('&', jsba__ved, expr_node
                )
        finally:
            (pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops
                ) = ywj__sfk
        return rzi__ipzz

    def _insert_NA_cond_body(expr_node, null_set):
        if isinstance(expr_node, pd.core.computation.ops.BinOp):
            if expr_node.op == '|':
                sfexf__tstr = set()
                kclwy__pprgv = set()
                qqf__qofl = _insert_NA_cond_body(expr_node.lhs, sfexf__tstr)
                bfqz__wxndn = _insert_NA_cond_body(expr_node.rhs, kclwy__pprgv)
                lrhch__hakqu = sfexf__tstr.intersection(kclwy__pprgv)
                sfexf__tstr.difference_update(lrhch__hakqu)
                kclwy__pprgv.difference_update(lrhch__hakqu)
                null_set.update(lrhch__hakqu)
                expr_node.lhs = append_null_checks(qqf__qofl, sfexf__tstr)
                expr_node.rhs = append_null_checks(bfqz__wxndn, kclwy__pprgv)
                expr_node.operands = expr_node.lhs, expr_node.rhs
            else:
                expr_node.lhs = _insert_NA_cond_body(expr_node.lhs, null_set)
                expr_node.rhs = _insert_NA_cond_body(expr_node.rhs, null_set)
        elif _is_col_access(expr_node):
            xnrje__cpfbr = expr_node.name
            crr__wjalr, col_name = xnrje__cpfbr.split('.')
            if crr__wjalr == 'left':
                iusoy__kigza = left_columns
                data = left_data
            else:
                iusoy__kigza = right_columns
                data = right_data
            ditdz__beo = data[iusoy__kigza.index(col_name)]
            if bodo.utils.typing.is_nullable(ditdz__beo):
                null_set.add(expr_node.name)
        return expr_node
    null_set = set()
    osxxo__uihx = _insert_NA_cond_body(expr_node, null_set)
    return append_null_checks(expr_node, null_set)


def _extract_equal_conds(expr_node):
    if not hasattr(expr_node, 'op'):
        return [], [], expr_node
    if expr_node.op == '==' and _is_col_access(expr_node.lhs
        ) and _is_col_access(expr_node.rhs):
        xrsjz__xgdzk = str(expr_node.lhs)
        wznsp__ojp = str(expr_node.rhs)
        if xrsjz__xgdzk.startswith('left.') and wznsp__ojp.startswith('left.'
            ) or xrsjz__xgdzk.startswith('right.') and wznsp__ojp.startswith(
            'right.'):
            return [], [], expr_node
        left_on = [xrsjz__xgdzk.split('.')[1]]
        right_on = [wznsp__ojp.split('.')[1]]
        if xrsjz__xgdzk.startswith('right.'):
            return right_on, left_on, None
        return left_on, right_on, None
    if expr_node.op == '&':
        cnuws__uzfkx, odn__pik, xzol__eroc = _extract_equal_conds(expr_node.lhs
            )
        vjak__zgon, uha__dowkh, tynwc__gsg = _extract_equal_conds(expr_node.rhs
            )
        left_on = cnuws__uzfkx + vjak__zgon
        right_on = odn__pik + uha__dowkh
        if xzol__eroc is None:
            return left_on, right_on, tynwc__gsg
        if tynwc__gsg is None:
            return left_on, right_on, xzol__eroc
        expr_node.lhs = xzol__eroc
        expr_node.rhs = tynwc__gsg
        expr_node.operands = expr_node.lhs, expr_node.rhs
        return left_on, right_on, expr_node
    return [], [], expr_node


def _parse_merge_cond(on_str, left_columns, left_data, right_columns,
    right_data):
    ocm__kywg = {'left': 0, 'right': 0}
    env = pd.core.computation.scope.ensure_scope(2, {}, {}, (ocm__kywg,))
    mzaas__ynfm = dict()
    trf__eunga = pd.core.computation.parsing.clean_column_name
    for name, vegj__xkky in (('left', left_columns), ('right', right_columns)):
        for ewtur__ysq in vegj__xkky:
            okvle__tjn = trf__eunga(ewtur__ysq)
            dif__irqwv = name, okvle__tjn
            if dif__irqwv in mzaas__ynfm:
                raise_bodo_error(
                    f"pd.merge(): {name} table contains two columns that are escaped to the same Python identifier '{ewtur__ysq}' and '{mzaas__ynfm[okvle__tjn]}' Please rename one of these columns. To avoid this issue, please use names that are valid Python identifiers."
                    )
            mzaas__ynfm[dif__irqwv] = ewtur__ysq
    wbjqq__wyfl, _, _ = _parse_query_expr(on_str, env, [], [], None,
        join_cleaned_cols=mzaas__ynfm)
    left_on, right_on, idwaz__hegn = _extract_equal_conds(wbjqq__wyfl.terms)
    return left_on, right_on, _insert_NA_cond(idwaz__hegn, left_columns,
        left_data, right_columns, right_data)


@overload_method(DataFrameType, 'merge', inline='always', no_unliteral=True)
@overload(pd.merge, inline='always', no_unliteral=True)
def overload_dataframe_merge(left, right, how='inner', on=None, left_on=
    None, right_on=None, left_index=False, right_index=False, sort=False,
    suffixes=('_x', '_y'), copy=True, indicator=False, validate=None,
    _bodo_na_equal=True):
    check_runtime_cols_unsupported(left, 'DataFrame.merge()')
    check_runtime_cols_unsupported(right, 'DataFrame.merge()')
    gqx__cck = dict(sort=sort, copy=copy, validate=validate)
    syjmu__lkfvy = dict(sort=False, copy=True, validate=None)
    check_unsupported_args('DataFrame.merge', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    validate_merge_spec(left, right, how, on, left_on, right_on, left_index,
        right_index, sort, suffixes, copy, indicator, validate)
    how = get_overload_const_str(how)
    zkfw__elnj = tuple(sorted(set(left.columns) & set(right.columns), key=
        lambda k: str(k)))
    kci__dzt = ''
    if not is_overload_none(on):
        left_on = right_on = on
        if is_overload_constant_str(on):
            on_str = get_overload_const_str(on)
            if on_str not in zkfw__elnj and ('left.' in on_str or 'right.' in
                on_str):
                left_on, right_on, sof__chp = _parse_merge_cond(on_str,
                    left.columns, left.data, right.columns, right.data)
                if sof__chp is None:
                    kci__dzt = ''
                else:
                    kci__dzt = str(sof__chp)
    if is_overload_none(on) and is_overload_none(left_on) and is_overload_none(
        right_on) and is_overload_false(left_index) and is_overload_false(
        right_index):
        left_keys = zkfw__elnj
        right_keys = zkfw__elnj
    else:
        if is_overload_true(left_index):
            left_keys = ['$_bodo_index_']
        else:
            left_keys = get_overload_const_list(left_on)
            validate_keys(left_keys, left)
        if is_overload_true(right_index):
            right_keys = ['$_bodo_index_']
        else:
            right_keys = get_overload_const_list(right_on)
            validate_keys(right_keys, right)
    if (not left_on or not right_on) and not is_overload_none(on):
        raise BodoError(
            f"DataFrame.merge(): Merge condition '{get_overload_const_str(on)}' requires a cross join to implement, but cross join is not supported."
            )
    if not is_overload_bool(indicator):
        raise_bodo_error(
            'DataFrame.merge(): indicator must be a constant boolean')
    indicator_val = get_overload_const_bool(indicator)
    if not is_overload_bool(_bodo_na_equal):
        raise_bodo_error(
            'DataFrame.merge(): bodo extension _bodo_na_equal must be a constant boolean'
            )
    asrc__ztstm = get_overload_const_bool(_bodo_na_equal)
    validate_keys_length(left_index, right_index, left_keys, right_keys)
    validate_keys_dtypes(left, right, left_index, right_index, left_keys,
        right_keys)
    if is_overload_constant_tuple(suffixes):
        ysugx__gbjf = get_overload_const_tuple(suffixes)
    if is_overload_constant_list(suffixes):
        ysugx__gbjf = list(get_overload_const_list(suffixes))
    suffix_x = ysugx__gbjf[0]
    suffix_y = ysugx__gbjf[1]
    validate_unicity_output_column_names(suffix_x, suffix_y, left_keys,
        right_keys, left.columns, right.columns, indicator_val)
    left_keys = gen_const_tup(left_keys)
    right_keys = gen_const_tup(right_keys)
    zhuuz__rnab = (
        "def _impl(left, right, how='inner', on=None, left_on=None,\n")
    zhuuz__rnab += (
        '    right_on=None, left_index=False, right_index=False, sort=False,\n'
        )
    zhuuz__rnab += """    suffixes=('_x', '_y'), copy=True, indicator=False, validate=None, _bodo_na_equal=True):
"""
    zhuuz__rnab += (
        """  return bodo.hiframes.pd_dataframe_ext.join_dummy(left, right, {}, {}, '{}', '{}', '{}', False, {}, {}, '{}')
"""
        .format(left_keys, right_keys, how, suffix_x, suffix_y,
        indicator_val, asrc__ztstm, kci__dzt))
    vowd__xeiyc = {}
    exec(zhuuz__rnab, {'bodo': bodo}, vowd__xeiyc)
    _impl = vowd__xeiyc['_impl']
    return _impl


def common_validate_merge_merge_asof_spec(name_func, left, right, on,
    left_on, right_on, left_index, right_index, suffixes):
    if not isinstance(left, DataFrameType) or not isinstance(right,
        DataFrameType):
        raise BodoError(name_func + '() requires dataframe inputs')
    valid_dataframe_column_types = (ArrayItemArrayType, MapArrayType,
        StructArrayType, CategoricalArrayType, types.Array,
        IntegerArrayType, DecimalArrayType, IntervalArrayType, bodo.
        DatetimeArrayType)
    ikik__xplus = {string_array_type, dict_str_arr_type, binary_array_type,
        datetime_date_array_type, datetime_timedelta_array_type, boolean_array}
    jiow__kope = {get_overload_const_str(pfl__jof) for pfl__jof in (left_on,
        right_on, on) if is_overload_constant_str(pfl__jof)}
    for df in (left, right):
        for i, ewtur__ysq in enumerate(df.data):
            if not isinstance(ewtur__ysq, valid_dataframe_column_types
                ) and ewtur__ysq not in ikik__xplus:
                raise BodoError(
                    f'{name_func}(): use of column with {type(ewtur__ysq)} in merge unsupported'
                    )
            if df.columns[i] in jiow__kope and isinstance(ewtur__ysq,
                MapArrayType):
                raise BodoError(
                    f'{name_func}(): merge on MapArrayType unsupported')
    ensure_constant_arg(name_func, 'left_index', left_index, bool)
    ensure_constant_arg(name_func, 'right_index', right_index, bool)
    if not is_overload_constant_tuple(suffixes
        ) and not is_overload_constant_list(suffixes):
        raise_bodo_error(name_func +
            "(): suffixes parameters should be ['_left', '_right']")
    if is_overload_constant_tuple(suffixes):
        ysugx__gbjf = get_overload_const_tuple(suffixes)
    if is_overload_constant_list(suffixes):
        ysugx__gbjf = list(get_overload_const_list(suffixes))
    if len(ysugx__gbjf) != 2:
        raise BodoError(name_func +
            '(): The number of suffixes should be exactly 2')
    zkfw__elnj = tuple(set(left.columns) & set(right.columns))
    if not is_overload_none(on):
        ltt__jhapo = False
        if is_overload_constant_str(on):
            on_str = get_overload_const_str(on)
            ltt__jhapo = on_str not in zkfw__elnj and ('left.' in on_str or
                'right.' in on_str)
        if len(zkfw__elnj) == 0 and not ltt__jhapo:
            raise_bodo_error(name_func +
                '(): No common columns to perform merge on. Merge options: left_on={lon}, right_on={ron}, left_index={lidx}, right_index={ridx}'
                .format(lon=is_overload_true(left_on), ron=is_overload_true
                (right_on), lidx=is_overload_true(left_index), ridx=
                is_overload_true(right_index)))
        if not is_overload_none(left_on) or not is_overload_none(right_on):
            raise BodoError(name_func +
                '(): Can only pass argument "on" OR "left_on" and "right_on", not a combination of both.'
                )
    if (is_overload_true(left_index) or not is_overload_none(left_on)
        ) and is_overload_none(right_on) and not is_overload_true(right_index):
        raise BodoError(name_func +
            '(): Must pass right_on or right_index=True')
    if (is_overload_true(right_index) or not is_overload_none(right_on)
        ) and is_overload_none(left_on) and not is_overload_true(left_index):
        raise BodoError(name_func + '(): Must pass left_on or left_index=True')


def validate_merge_spec(left, right, how, on, left_on, right_on, left_index,
    right_index, sort, suffixes, copy, indicator, validate):
    common_validate_merge_merge_asof_spec('merge', left, right, on, left_on,
        right_on, left_index, right_index, suffixes)
    ensure_constant_values('merge', 'how', how, ('left', 'right', 'outer',
        'inner'))


def validate_merge_asof_spec(left, right, on, left_on, right_on, left_index,
    right_index, by, left_by, right_by, suffixes, tolerance,
    allow_exact_matches, direction):
    common_validate_merge_merge_asof_spec('merge_asof', left, right, on,
        left_on, right_on, left_index, right_index, suffixes)
    if not is_overload_true(allow_exact_matches):
        raise BodoError(
            'merge_asof(): allow_exact_matches parameter only supports default value True'
            )
    if not is_overload_none(tolerance):
        raise BodoError(
            'merge_asof(): tolerance parameter only supports default value None'
            )
    if not is_overload_none(by):
        raise BodoError(
            'merge_asof(): by parameter only supports default value None')
    if not is_overload_none(left_by):
        raise BodoError(
            'merge_asof(): left_by parameter only supports default value None')
    if not is_overload_none(right_by):
        raise BodoError(
            'merge_asof(): right_by parameter only supports default value None'
            )
    if not is_overload_constant_str(direction):
        raise BodoError(
            'merge_asof(): direction parameter should be of type str')
    else:
        direction = get_overload_const_str(direction)
        if direction != 'backward':
            raise BodoError(
                "merge_asof(): direction parameter only supports default value 'backward'"
                )


def validate_merge_asof_keys_length(left_on, right_on, left_index,
    right_index, left_keys, right_keys):
    if not is_overload_true(left_index) and not is_overload_true(right_index):
        if len(right_keys) != len(left_keys):
            raise BodoError('merge(): len(right_on) must equal len(left_on)')
    if not is_overload_none(left_on) and is_overload_true(right_index):
        raise BodoError(
            'merge(): right_index = True and specifying left_on is not suppported yet.'
            )
    if not is_overload_none(right_on) and is_overload_true(left_index):
        raise BodoError(
            'merge(): left_index = True and specifying right_on is not suppported yet.'
            )


def validate_keys_length(left_index, right_index, left_keys, right_keys):
    if not is_overload_true(left_index) and not is_overload_true(right_index):
        if len(right_keys) != len(left_keys):
            raise BodoError('merge(): len(right_on) must equal len(left_on)')
    if is_overload_true(right_index):
        if len(left_keys) != 1:
            raise BodoError(
                'merge(): len(left_on) must equal the number of levels in the index of "right", which is 1'
                )
    if is_overload_true(left_index):
        if len(right_keys) != 1:
            raise BodoError(
                'merge(): len(right_on) must equal the number of levels in the index of "left", which is 1'
                )


def validate_keys_dtypes(left, right, left_index, right_index, left_keys,
    right_keys):
    wawqi__ppgk = numba.core.registry.cpu_target.typing_context
    if is_overload_true(left_index) or is_overload_true(right_index):
        if is_overload_true(left_index) and is_overload_true(right_index):
            zcfuw__qfip = left.index
            pon__txlst = isinstance(zcfuw__qfip, StringIndexType)
            kxwpu__vos = right.index
            lpe__mpc = isinstance(kxwpu__vos, StringIndexType)
        elif is_overload_true(left_index):
            zcfuw__qfip = left.index
            pon__txlst = isinstance(zcfuw__qfip, StringIndexType)
            kxwpu__vos = right.data[right.columns.index(right_keys[0])]
            lpe__mpc = kxwpu__vos.dtype == string_type
        elif is_overload_true(right_index):
            zcfuw__qfip = left.data[left.columns.index(left_keys[0])]
            pon__txlst = zcfuw__qfip.dtype == string_type
            kxwpu__vos = right.index
            lpe__mpc = isinstance(kxwpu__vos, StringIndexType)
        if pon__txlst and lpe__mpc:
            return
        zcfuw__qfip = zcfuw__qfip.dtype
        kxwpu__vos = kxwpu__vos.dtype
        try:
            vwcf__jxc = wawqi__ppgk.resolve_function_type(operator.eq, (
                zcfuw__qfip, kxwpu__vos), {})
        except:
            raise_bodo_error(
                'merge: You are trying to merge on {lk_dtype} and {rk_dtype} columns. If you wish to proceed you should use pd.concat'
                .format(lk_dtype=zcfuw__qfip, rk_dtype=kxwpu__vos))
    else:
        for fsodu__nvsbi, dps__hdm in zip(left_keys, right_keys):
            zcfuw__qfip = left.data[left.columns.index(fsodu__nvsbi)].dtype
            taswi__neq = left.data[left.columns.index(fsodu__nvsbi)]
            kxwpu__vos = right.data[right.columns.index(dps__hdm)].dtype
            cwdv__omst = right.data[right.columns.index(dps__hdm)]
            if taswi__neq == cwdv__omst:
                continue
            szdv__jtmo = (
                'merge: You are trying to merge on column {lk} of {lk_dtype} and column {rk} of {rk_dtype}. If you wish to proceed you should use pd.concat'
                .format(lk=fsodu__nvsbi, lk_dtype=zcfuw__qfip, rk=dps__hdm,
                rk_dtype=kxwpu__vos))
            bhdj__cabmz = zcfuw__qfip == string_type
            jrk__ebtts = kxwpu__vos == string_type
            if bhdj__cabmz ^ jrk__ebtts:
                raise_bodo_error(szdv__jtmo)
            try:
                vwcf__jxc = wawqi__ppgk.resolve_function_type(operator.eq,
                    (zcfuw__qfip, kxwpu__vos), {})
            except:
                raise_bodo_error(szdv__jtmo)


def validate_keys(keys, df):
    ttzwt__rofy = set(keys).difference(set(df.columns))
    if len(ttzwt__rofy) > 0:
        if is_overload_constant_str(df.index.name_typ
            ) and get_overload_const_str(df.index.name_typ) in ttzwt__rofy:
            raise_bodo_error(
                f'merge(): use of index {df.index.name_typ} as key for on/left_on/right_on is unsupported'
                )
        raise_bodo_error(
            f"""merge(): invalid key {ttzwt__rofy} for on/left_on/right_on
merge supports only valid column names {df.columns}"""
            )


@overload_method(DataFrameType, 'join', inline='always', no_unliteral=True)
def overload_dataframe_join(left, other, on=None, how='left', lsuffix='',
    rsuffix='', sort=False):
    check_runtime_cols_unsupported(left, 'DataFrame.join()')
    check_runtime_cols_unsupported(other, 'DataFrame.join()')
    gqx__cck = dict(lsuffix=lsuffix, rsuffix=rsuffix)
    syjmu__lkfvy = dict(lsuffix='', rsuffix='')
    check_unsupported_args('DataFrame.join', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    validate_join_spec(left, other, on, how, lsuffix, rsuffix, sort)
    how = get_overload_const_str(how)
    if not is_overload_none(on):
        left_keys = get_overload_const_list(on)
    else:
        left_keys = ['$_bodo_index_']
    right_keys = ['$_bodo_index_']
    left_keys = gen_const_tup(left_keys)
    right_keys = gen_const_tup(right_keys)
    zhuuz__rnab = "def _impl(left, other, on=None, how='left',\n"
    zhuuz__rnab += "    lsuffix='', rsuffix='', sort=False):\n"
    zhuuz__rnab += (
        """  return bodo.hiframes.pd_dataframe_ext.join_dummy(left, other, {}, {}, '{}', '{}', '{}', True, False, True, '')
"""
        .format(left_keys, right_keys, how, lsuffix, rsuffix))
    vowd__xeiyc = {}
    exec(zhuuz__rnab, {'bodo': bodo}, vowd__xeiyc)
    _impl = vowd__xeiyc['_impl']
    return _impl


def validate_join_spec(left, other, on, how, lsuffix, rsuffix, sort):
    if not isinstance(other, DataFrameType):
        raise BodoError('join() requires dataframe inputs')
    ensure_constant_values('merge', 'how', how, ('left', 'right', 'outer',
        'inner'))
    if not is_overload_none(on) and len(get_overload_const_list(on)) != 1:
        raise BodoError('join(): len(on) must equals to 1 when specified.')
    if not is_overload_none(on):
        jcx__chum = get_overload_const_list(on)
        validate_keys(jcx__chum, left)
    if not is_overload_false(sort):
        raise BodoError(
            'join(): sort parameter only supports default value False')
    zkfw__elnj = tuple(set(left.columns) & set(other.columns))
    if len(zkfw__elnj) > 0:
        raise_bodo_error(
            'join(): not supporting joining on overlapping columns:{cols} Use DataFrame.merge() instead.'
            .format(cols=zkfw__elnj))


def validate_unicity_output_column_names(suffix_x, suffix_y, left_keys,
    right_keys, left_columns, right_columns, indicator_val):
    xik__saaj = set(left_keys) & set(right_keys)
    fiwny__qwkc = set(left_columns) & set(right_columns)
    dkrlo__jsh = fiwny__qwkc - xik__saaj
    bwv__hlm = set(left_columns) - fiwny__qwkc
    dbpwe__oms = set(right_columns) - fiwny__qwkc
    bhcy__aki = {}

    def insertOutColumn(col_name):
        if col_name in bhcy__aki:
            raise_bodo_error(
                'join(): two columns happen to have the same name : {}'.
                format(col_name))
        bhcy__aki[col_name] = 0
    for vsq__xms in xik__saaj:
        insertOutColumn(vsq__xms)
    for vsq__xms in dkrlo__jsh:
        zlu__tuenb = str(vsq__xms) + suffix_x
        iyhf__hpyxp = str(vsq__xms) + suffix_y
        insertOutColumn(zlu__tuenb)
        insertOutColumn(iyhf__hpyxp)
    for vsq__xms in bwv__hlm:
        insertOutColumn(vsq__xms)
    for vsq__xms in dbpwe__oms:
        insertOutColumn(vsq__xms)
    if indicator_val:
        insertOutColumn('_merge')


@overload(pd.merge_asof, inline='always', no_unliteral=True)
def overload_dataframe_merge_asof(left, right, on=None, left_on=None,
    right_on=None, left_index=False, right_index=False, by=None, left_by=
    None, right_by=None, suffixes=('_x', '_y'), tolerance=None,
    allow_exact_matches=True, direction='backward'):
    validate_merge_asof_spec(left, right, on, left_on, right_on, left_index,
        right_index, by, left_by, right_by, suffixes, tolerance,
        allow_exact_matches, direction)
    if not isinstance(left, DataFrameType) or not isinstance(right,
        DataFrameType):
        raise BodoError('merge_asof() requires dataframe inputs')
    zkfw__elnj = tuple(sorted(set(left.columns) & set(right.columns), key=
        lambda k: str(k)))
    if not is_overload_none(on):
        left_on = right_on = on
    if is_overload_none(on) and is_overload_none(left_on) and is_overload_none(
        right_on) and is_overload_false(left_index) and is_overload_false(
        right_index):
        left_keys = zkfw__elnj
        right_keys = zkfw__elnj
    else:
        if is_overload_true(left_index):
            left_keys = ['$_bodo_index_']
        else:
            left_keys = get_overload_const_list(left_on)
            validate_keys(left_keys, left)
        if is_overload_true(right_index):
            right_keys = ['$_bodo_index_']
        else:
            right_keys = get_overload_const_list(right_on)
            validate_keys(right_keys, right)
    validate_merge_asof_keys_length(left_on, right_on, left_index,
        right_index, left_keys, right_keys)
    validate_keys_dtypes(left, right, left_index, right_index, left_keys,
        right_keys)
    left_keys = gen_const_tup(left_keys)
    right_keys = gen_const_tup(right_keys)
    if isinstance(suffixes, tuple):
        ysugx__gbjf = suffixes
    if is_overload_constant_list(suffixes):
        ysugx__gbjf = list(get_overload_const_list(suffixes))
    if isinstance(suffixes, types.Omitted):
        ysugx__gbjf = suffixes.value
    suffix_x = ysugx__gbjf[0]
    suffix_y = ysugx__gbjf[1]
    zhuuz__rnab = (
        'def _impl(left, right, on=None, left_on=None, right_on=None,\n')
    zhuuz__rnab += (
        '    left_index=False, right_index=False, by=None, left_by=None,\n')
    zhuuz__rnab += (
        "    right_by=None, suffixes=('_x', '_y'), tolerance=None,\n")
    zhuuz__rnab += "    allow_exact_matches=True, direction='backward'):\n"
    zhuuz__rnab += '  suffix_x = suffixes[0]\n'
    zhuuz__rnab += '  suffix_y = suffixes[1]\n'
    zhuuz__rnab += (
        """  return bodo.hiframes.pd_dataframe_ext.join_dummy(left, right, {}, {}, 'asof', '{}', '{}', False, False, True, '')
"""
        .format(left_keys, right_keys, suffix_x, suffix_y))
    vowd__xeiyc = {}
    exec(zhuuz__rnab, {'bodo': bodo}, vowd__xeiyc)
    _impl = vowd__xeiyc['_impl']
    return _impl


@overload_method(DataFrameType, 'groupby', inline='always', no_unliteral=True)
def overload_dataframe_groupby(df, by=None, axis=0, level=None, as_index=
    True, sort=False, group_keys=True, squeeze=False, observed=True, dropna
    =True):
    check_runtime_cols_unsupported(df, 'DataFrame.groupby()')
    validate_groupby_spec(df, by, axis, level, as_index, sort, group_keys,
        squeeze, observed, dropna)

    def _impl(df, by=None, axis=0, level=None, as_index=True, sort=False,
        group_keys=True, squeeze=False, observed=True, dropna=True):
        return bodo.hiframes.pd_groupby_ext.init_groupby(df, by, as_index,
            dropna)
    return _impl


def validate_groupby_spec(df, by, axis, level, as_index, sort, group_keys,
    squeeze, observed, dropna):
    if is_overload_none(by):
        raise BodoError("groupby(): 'by' must be supplied.")
    if not is_overload_zero(axis):
        raise BodoError(
            "groupby(): 'axis' parameter only supports integer value 0.")
    if not is_overload_none(level):
        raise BodoError(
            "groupby(): 'level' is not supported since MultiIndex is not supported."
            )
    if not is_literal_type(by) and not is_overload_constant_list(by):
        raise_bodo_error(
            f"groupby(): 'by' parameter only supports a constant column label or column labels, not {by}."
            )
    if len(set(get_overload_const_list(by)).difference(set(df.columns))) > 0:
        raise_bodo_error(
            "groupby(): invalid key {} for 'by' (not available in columns {})."
            .format(get_overload_const_list(by), df.columns))
    if not is_overload_constant_bool(as_index):
        raise_bodo_error(
            "groupby(): 'as_index' parameter must be a constant bool, not {}."
            .format(as_index))
    if not is_overload_constant_bool(dropna):
        raise_bodo_error(
            "groupby(): 'dropna' parameter must be a constant bool, not {}."
            .format(dropna))
    gqx__cck = dict(sort=sort, group_keys=group_keys, squeeze=squeeze,
        observed=observed)
    qompd__wymhe = dict(sort=False, group_keys=True, squeeze=False,
        observed=True)
    check_unsupported_args('Dataframe.groupby', gqx__cck, qompd__wymhe,
        package_name='pandas', module_name='GroupBy')


def pivot_error_checking(df, index, columns, values, func_name):
    narag__dwqjl = func_name == 'DataFrame.pivot_table'
    if narag__dwqjl:
        if is_overload_none(index) or not is_literal_type(index):
            raise BodoError(
                f"DataFrame.pivot_table(): 'index' argument is required and must be constant column labels"
                )
    elif not is_overload_none(index) and not is_literal_type(index):
        raise BodoError(
            f"{func_name}(): if 'index' argument is provided it must be constant column labels"
            )
    if is_overload_none(columns) or not is_literal_type(columns):
        raise BodoError(
            f"{func_name}(): 'columns' argument is required and must be a constant column label"
            )
    if not is_overload_none(values) and not is_literal_type(values):
        raise BodoError(
            f"{func_name}(): if 'values' argument is provided it must be constant column labels"
            )
    nyvz__naftv = get_literal_value(columns)
    if isinstance(nyvz__naftv, (list, tuple)):
        if len(nyvz__naftv) > 1:
            raise BodoError(
                f"{func_name}(): 'columns' argument must be a constant column label not a {nyvz__naftv}"
                )
        nyvz__naftv = nyvz__naftv[0]
    if nyvz__naftv not in df.columns:
        raise BodoError(
            f"{func_name}(): 'columns' column {nyvz__naftv} not found in DataFrame {df}."
            )
    nojj__nbovu = {sijzc__erm: i for i, sijzc__erm in enumerate(df.columns)}
    osz__nlvv = nojj__nbovu[nyvz__naftv]
    if is_overload_none(index):
        dbjjm__pal = []
        gxcq__xdzm = []
    else:
        gxcq__xdzm = get_literal_value(index)
        if not isinstance(gxcq__xdzm, (list, tuple)):
            gxcq__xdzm = [gxcq__xdzm]
        dbjjm__pal = []
        for index in gxcq__xdzm:
            if index not in nojj__nbovu:
                raise BodoError(
                    f"{func_name}(): 'index' column {index} not found in DataFrame {df}."
                    )
            dbjjm__pal.append(nojj__nbovu[index])
    if not (all(isinstance(sijzc__erm, int) for sijzc__erm in gxcq__xdzm) or
        all(isinstance(sijzc__erm, str) for sijzc__erm in gxcq__xdzm)):
        raise BodoError(
            f"{func_name}(): column names selected for 'index' must all share a common int or string type. Please convert your names to a common type using DataFrame.rename()"
            )
    if is_overload_none(values):
        uhrl__dwb = []
        lboji__nmdl = []
        bgo__ddrx = dbjjm__pal + [osz__nlvv]
        for i, sijzc__erm in enumerate(df.columns):
            if i not in bgo__ddrx:
                uhrl__dwb.append(i)
                lboji__nmdl.append(sijzc__erm)
    else:
        lboji__nmdl = get_literal_value(values)
        if not isinstance(lboji__nmdl, (list, tuple)):
            lboji__nmdl = [lboji__nmdl]
        uhrl__dwb = []
        for val in lboji__nmdl:
            if val not in nojj__nbovu:
                raise BodoError(
                    f"{func_name}(): 'values' column {val} not found in DataFrame {df}."
                    )
            uhrl__dwb.append(nojj__nbovu[val])
    if all(isinstance(sijzc__erm, int) for sijzc__erm in lboji__nmdl):
        lboji__nmdl = np.array(lboji__nmdl, 'int64')
    elif all(isinstance(sijzc__erm, str) for sijzc__erm in lboji__nmdl):
        lboji__nmdl = pd.array(lboji__nmdl, 'string')
    else:
        raise BodoError(
            f"{func_name}(): column names selected for 'values' must all share a common int or string type. Please convert your names to a common type using DataFrame.rename()"
            )
    ncqx__rsoi = set(uhrl__dwb) | set(dbjjm__pal) | {osz__nlvv}
    if len(ncqx__rsoi) != len(uhrl__dwb) + len(dbjjm__pal) + 1:
        raise BodoError(
            f"{func_name}(): 'index', 'columns', and 'values' must all refer to different columns"
            )

    def check_valid_index_typ(index_column):
        if isinstance(index_column, (bodo.ArrayItemArrayType, bodo.
            MapArrayType, bodo.StructArrayType, bodo.TupleArrayType, bodo.
            IntervalArrayType)):
            raise BodoError(
                f"{func_name}(): 'index' DataFrame column must have scalar rows"
                )
        if isinstance(index_column, bodo.CategoricalArrayType):
            raise BodoError(
                f"{func_name}(): 'index' DataFrame column does not support categorical data"
                )
    if len(dbjjm__pal) == 0:
        index = df.index
        if isinstance(index, MultiIndexType):
            raise BodoError(
                f"{func_name}(): 'index' cannot be None with a DataFrame with a multi-index"
                )
        if not isinstance(index, RangeIndexType):
            check_valid_index_typ(index.data)
        if not is_literal_type(df.index.name_typ):
            raise BodoError(
                f"{func_name}(): If 'index' is None, the name of the DataFrame's Index must be constant at compile-time"
                )
    else:
        for plp__sjn in dbjjm__pal:
            index_column = df.data[plp__sjn]
            check_valid_index_typ(index_column)
    zrqc__opnf = df.data[osz__nlvv]
    if isinstance(zrqc__opnf, (bodo.ArrayItemArrayType, bodo.MapArrayType,
        bodo.StructArrayType, bodo.TupleArrayType, bodo.IntervalArrayType)):
        raise BodoError(
            f"{func_name}(): 'columns' DataFrame column must have scalar rows")
    if isinstance(zrqc__opnf, bodo.CategoricalArrayType):
        raise BodoError(
            f"{func_name}(): 'columns' DataFrame column does not support categorical data"
            )
    for kmf__yjz in uhrl__dwb:
        iza__viexq = df.data[kmf__yjz]
        if isinstance(iza__viexq, (bodo.ArrayItemArrayType, bodo.
            MapArrayType, bodo.StructArrayType, bodo.TupleArrayType)
            ) or iza__viexq == bodo.binary_array_type:
            raise BodoError(
                f"{func_name}(): 'values' DataFrame column must have scalar rows"
                )
    return (gxcq__xdzm, nyvz__naftv, lboji__nmdl, dbjjm__pal, osz__nlvv,
        uhrl__dwb)


@overload(pd.pivot, inline='always', no_unliteral=True)
@overload_method(DataFrameType, 'pivot', inline='always', no_unliteral=True)
def overload_dataframe_pivot(data, index=None, columns=None, values=None):
    check_runtime_cols_unsupported(data, 'DataFrame.pivot()')
    if not isinstance(data, DataFrameType):
        raise BodoError("pandas.pivot(): 'data' argument must be a DataFrame")
    gxcq__xdzm, nyvz__naftv, lboji__nmdl, plp__sjn, osz__nlvv, wfd__hhh = (
        pivot_error_checking(data, index, columns, values, 'DataFrame.pivot'))
    if len(gxcq__xdzm) == 0:
        if is_overload_none(data.index.name_typ):
            gxcq__xdzm = [None]
        else:
            gxcq__xdzm = [get_literal_value(data.index.name_typ)]
    if len(lboji__nmdl) == 1:
        cot__tvwx = None
    else:
        cot__tvwx = lboji__nmdl
    zhuuz__rnab = 'def impl(data, index=None, columns=None, values=None):\n'
    zhuuz__rnab += f'    pivot_values = data.iloc[:, {osz__nlvv}].unique()\n'
    zhuuz__rnab += '    return bodo.hiframes.pd_dataframe_ext.pivot_impl(\n'
    if len(plp__sjn) == 0:
        zhuuz__rnab += f"""        (bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)),),
"""
    else:
        zhuuz__rnab += '        (\n'
        for gopfg__vykm in plp__sjn:
            zhuuz__rnab += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {gopfg__vykm}),
"""
        zhuuz__rnab += '        ),\n'
    zhuuz__rnab += f"""        (bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {osz__nlvv}),),
"""
    zhuuz__rnab += '        (\n'
    for kmf__yjz in wfd__hhh:
        zhuuz__rnab += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {kmf__yjz}),
"""
    zhuuz__rnab += '        ),\n'
    zhuuz__rnab += '        pivot_values,\n'
    zhuuz__rnab += '        index_lit_tup,\n'
    zhuuz__rnab += '        columns_lit,\n'
    zhuuz__rnab += '        values_name_const,\n'
    zhuuz__rnab += '    )\n'
    vowd__xeiyc = {}
    exec(zhuuz__rnab, {'bodo': bodo, 'index_lit_tup': tuple(gxcq__xdzm),
        'columns_lit': nyvz__naftv, 'values_name_const': cot__tvwx},
        vowd__xeiyc)
    impl = vowd__xeiyc['impl']
    return impl


@overload(pd.pivot_table, inline='always', no_unliteral=True)
@overload_method(DataFrameType, 'pivot_table', inline='always',
    no_unliteral=True)
def overload_dataframe_pivot_table(data, values=None, index=None, columns=
    None, aggfunc='mean', fill_value=None, margins=False, dropna=True,
    margins_name='All', observed=False, sort=True, _pivot_values=None):
    check_runtime_cols_unsupported(data, 'DataFrame.pivot_table()')
    gqx__cck = dict(fill_value=fill_value, margins=margins, dropna=dropna,
        margins_name=margins_name, observed=observed, sort=sort)
    syjmu__lkfvy = dict(fill_value=None, margins=False, dropna=True,
        margins_name='All', observed=False, sort=True)
    check_unsupported_args('DataFrame.pivot_table', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    if not isinstance(data, DataFrameType):
        raise BodoError(
            "pandas.pivot_table(): 'data' argument must be a DataFrame")
    if _pivot_values is None:
        (gxcq__xdzm, nyvz__naftv, lboji__nmdl, plp__sjn, osz__nlvv, wfd__hhh
            ) = (pivot_error_checking(data, index, columns, values,
            'DataFrame.pivot_table'))
        if len(lboji__nmdl) == 1:
            cot__tvwx = None
        else:
            cot__tvwx = lboji__nmdl
        zhuuz__rnab = 'def impl(\n'
        zhuuz__rnab += '    data,\n'
        zhuuz__rnab += '    values=None,\n'
        zhuuz__rnab += '    index=None,\n'
        zhuuz__rnab += '    columns=None,\n'
        zhuuz__rnab += '    aggfunc="mean",\n'
        zhuuz__rnab += '    fill_value=None,\n'
        zhuuz__rnab += '    margins=False,\n'
        zhuuz__rnab += '    dropna=True,\n'
        zhuuz__rnab += '    margins_name="All",\n'
        zhuuz__rnab += '    observed=False,\n'
        zhuuz__rnab += '    sort=True,\n'
        zhuuz__rnab += '    _pivot_values=None,\n'
        zhuuz__rnab += '):\n'
        nps__bxift = plp__sjn + [osz__nlvv] + wfd__hhh
        zhuuz__rnab += f'    data = data.iloc[:, {nps__bxift}]\n'
        hljlc__rvm = gxcq__xdzm + [nyvz__naftv]
        zhuuz__rnab += (
            f'    data = data.groupby({hljlc__rvm!r}, as_index=False).agg(aggfunc)\n'
            )
        zhuuz__rnab += (
            f'    pivot_values = data.iloc[:, {len(plp__sjn)}].unique()\n')
        zhuuz__rnab += (
            '    return bodo.hiframes.pd_dataframe_ext.pivot_impl(\n')
        zhuuz__rnab += '        (\n'
        for i in range(0, len(plp__sjn)):
            zhuuz__rnab += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {i}),
"""
        zhuuz__rnab += '        ),\n'
        zhuuz__rnab += f"""        (bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {len(plp__sjn)}),),
"""
        zhuuz__rnab += '        (\n'
        for i in range(len(plp__sjn) + 1, len(wfd__hhh) + len(plp__sjn) + 1):
            zhuuz__rnab += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {i}),
"""
        zhuuz__rnab += '        ),\n'
        zhuuz__rnab += '        pivot_values,\n'
        zhuuz__rnab += '        index_lit_tup,\n'
        zhuuz__rnab += '        columns_lit,\n'
        zhuuz__rnab += '        values_name_const,\n'
        zhuuz__rnab += '        check_duplicates=False,\n'
        zhuuz__rnab += '    )\n'
        vowd__xeiyc = {}
        exec(zhuuz__rnab, {'bodo': bodo, 'numba': numba, 'index_lit_tup':
            tuple(gxcq__xdzm), 'columns_lit': nyvz__naftv,
            'values_name_const': cot__tvwx}, vowd__xeiyc)
        impl = vowd__xeiyc['impl']
        return impl
    if aggfunc == 'mean':

        def _impl(data, values=None, index=None, columns=None, aggfunc=
            'mean', fill_value=None, margins=False, dropna=True,
            margins_name='All', observed=False, sort=True, _pivot_values=None):
            return bodo.hiframes.pd_groupby_ext.pivot_table_dummy(data,
                values, index, columns, 'mean', _pivot_values)
        return _impl

    def _impl(data, values=None, index=None, columns=None, aggfunc='mean',
        fill_value=None, margins=False, dropna=True, margins_name='All',
        observed=False, sort=True, _pivot_values=None):
        return bodo.hiframes.pd_groupby_ext.pivot_table_dummy(data, values,
            index, columns, aggfunc, _pivot_values)
    return _impl


@overload(pd.crosstab, inline='always', no_unliteral=True)
def crosstab_overload(index, columns, values=None, rownames=None, colnames=
    None, aggfunc=None, margins=False, margins_name='All', dropna=True,
    normalize=False, _pivot_values=None):
    gqx__cck = dict(values=values, rownames=rownames, colnames=colnames,
        aggfunc=aggfunc, margins=margins, margins_name=margins_name, dropna
        =dropna, normalize=normalize)
    syjmu__lkfvy = dict(values=None, rownames=None, colnames=None, aggfunc=
        None, margins=False, margins_name='All', dropna=True, normalize=False)
    check_unsupported_args('pandas.crosstab', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    if not isinstance(index, SeriesType):
        raise BodoError(
            f"pandas.crosstab(): 'index' argument only supported for Series types, found {index}"
            )
    if not isinstance(columns, SeriesType):
        raise BodoError(
            f"pandas.crosstab(): 'columns' argument only supported for Series types, found {columns}"
            )

    def _impl(index, columns, values=None, rownames=None, colnames=None,
        aggfunc=None, margins=False, margins_name='All', dropna=True,
        normalize=False, _pivot_values=None):
        return bodo.hiframes.pd_groupby_ext.crosstab_dummy(index, columns,
            _pivot_values)
    return _impl


@overload_method(DataFrameType, 'sort_values', inline='always',
    no_unliteral=True)
def overload_dataframe_sort_values(df, by, axis=0, ascending=True, inplace=
    False, kind='quicksort', na_position='last', ignore_index=False, key=
    None, _bodo_transformed=False):
    check_runtime_cols_unsupported(df, 'DataFrame.sort_values()')
    gqx__cck = dict(ignore_index=ignore_index, key=key)
    syjmu__lkfvy = dict(ignore_index=False, key=None)
    check_unsupported_args('DataFrame.sort_values', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    handle_inplace_df_type_change(inplace, _bodo_transformed, 'sort_values')
    validate_sort_values_spec(df, by, axis, ascending, inplace, kind,
        na_position)

    def _impl(df, by, axis=0, ascending=True, inplace=False, kind=
        'quicksort', na_position='last', ignore_index=False, key=None,
        _bodo_transformed=False):
        return bodo.hiframes.pd_dataframe_ext.sort_values_dummy(df, by,
            ascending, inplace, na_position)
    return _impl


def validate_sort_values_spec(df, by, axis, ascending, inplace, kind,
    na_position):
    if is_overload_none(by) or not is_literal_type(by
        ) and not is_overload_constant_list(by):
        raise_bodo_error(
            "sort_values(): 'by' parameter only supports a constant column label or column labels. by={}"
            .format(by))
    tad__thana = set(df.columns)
    if is_overload_constant_str(df.index.name_typ):
        tad__thana.add(get_overload_const_str(df.index.name_typ))
    if is_overload_constant_tuple(by):
        husps__eju = [get_overload_const_tuple(by)]
    else:
        husps__eju = get_overload_const_list(by)
    husps__eju = set((k, '') if (k, '') in tad__thana else k for k in
        husps__eju)
    if len(husps__eju.difference(tad__thana)) > 0:
        evfev__wqw = list(set(get_overload_const_list(by)).difference(
            tad__thana))
        raise_bodo_error(f'sort_values(): invalid keys {evfev__wqw} for by.')
    if not is_overload_zero(axis):
        raise_bodo_error(
            "sort_values(): 'axis' parameter only supports integer value 0.")
    if not is_overload_bool(ascending) and not is_overload_bool_list(ascending
        ):
        raise_bodo_error(
            "sort_values(): 'ascending' parameter must be of type bool or list of bool, not {}."
            .format(ascending))
    if not is_overload_bool(inplace):
        raise_bodo_error(
            "sort_values(): 'inplace' parameter must be of type bool, not {}."
            .format(inplace))
    if kind != 'quicksort' and not isinstance(kind, types.Omitted):
        warnings.warn(BodoWarning(
            'sort_values(): specifying sorting algorithm is not supported in Bodo. Bodo uses stable sort.'
            ))
    if is_overload_constant_str(na_position):
        na_position = get_overload_const_str(na_position)
        if na_position not in ('first', 'last'):
            raise BodoError(
                "sort_values(): na_position should either be 'first' or 'last'"
                )
    elif is_overload_constant_list(na_position):
        kwyxo__dchka = get_overload_const_list(na_position)
        for na_position in kwyxo__dchka:
            if na_position not in ('first', 'last'):
                raise BodoError(
                    "sort_values(): Every value in na_position should either be 'first' or 'last'"
                    )
    else:
        raise_bodo_error(
            f'sort_values(): na_position parameter must be a literal constant of type str or a constant list of str with 1 entry per key column, not {na_position}'
            )
    na_position = get_overload_const_str(na_position)
    if na_position not in ['first', 'last']:
        raise BodoError(
            "sort_values(): na_position should either be 'first' or 'last'")


@overload_method(DataFrameType, 'sort_index', inline='always', no_unliteral
    =True)
def overload_dataframe_sort_index(df, axis=0, level=None, ascending=True,
    inplace=False, kind='quicksort', na_position='last', sort_remaining=
    True, ignore_index=False, key=None):
    check_runtime_cols_unsupported(df, 'DataFrame.sort_index()')
    gqx__cck = dict(axis=axis, level=level, kind=kind, sort_remaining=
        sort_remaining, ignore_index=ignore_index, key=key)
    syjmu__lkfvy = dict(axis=0, level=None, kind='quicksort',
        sort_remaining=True, ignore_index=False, key=None)
    check_unsupported_args('DataFrame.sort_index', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    if not is_overload_bool(ascending):
        raise BodoError(
            "DataFrame.sort_index(): 'ascending' parameter must be of type bool"
            )
    if not is_overload_bool(inplace):
        raise BodoError(
            "DataFrame.sort_index(): 'inplace' parameter must be of type bool")
    if not is_overload_constant_str(na_position) or get_overload_const_str(
        na_position) not in ('first', 'last'):
        raise_bodo_error(
            "DataFrame.sort_index(): 'na_position' should either be 'first' or 'last'"
            )

    def _impl(df, axis=0, level=None, ascending=True, inplace=False, kind=
        'quicksort', na_position='last', sort_remaining=True, ignore_index=
        False, key=None):
        return bodo.hiframes.pd_dataframe_ext.sort_values_dummy(df,
            '$_bodo_index_', ascending, inplace, na_position)
    return _impl


@overload_method(DataFrameType, 'fillna', inline='always', no_unliteral=True)
def overload_dataframe_fillna(df, value=None, method=None, axis=None,
    inplace=False, limit=None, downcast=None):
    check_runtime_cols_unsupported(df, 'DataFrame.fillna()')
    gqx__cck = dict(limit=limit, downcast=downcast)
    syjmu__lkfvy = dict(limit=None, downcast=None)
    check_unsupported_args('DataFrame.fillna', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise BodoError("DataFrame.fillna(): 'axis' argument not supported.")
    bfrj__kkw = not is_overload_none(value)
    tygnj__faz = not is_overload_none(method)
    if bfrj__kkw and tygnj__faz:
        raise BodoError(
            "DataFrame.fillna(): Cannot specify both 'value' and 'method'.")
    if not bfrj__kkw and not tygnj__faz:
        raise BodoError(
            "DataFrame.fillna(): Must specify one of 'value' and 'method'.")
    if bfrj__kkw:
        xiono__wdcx = 'value=value'
    else:
        xiono__wdcx = 'method=method'
    data_args = [(
        f"df['{sijzc__erm}'].fillna({xiono__wdcx}, inplace=inplace)" if
        isinstance(sijzc__erm, str) else
        f'df[{sijzc__erm}].fillna({xiono__wdcx}, inplace=inplace)') for
        sijzc__erm in df.columns]
    zhuuz__rnab = """def impl(df, value=None, method=None, axis=None, inplace=False, limit=None, downcast=None):
"""
    if is_overload_true(inplace):
        zhuuz__rnab += '  ' + '  \n'.join(data_args) + '\n'
        vowd__xeiyc = {}
        exec(zhuuz__rnab, {}, vowd__xeiyc)
        impl = vowd__xeiyc['impl']
        return impl
    else:
        return _gen_init_df(zhuuz__rnab, df.columns, ', '.join(jyhv__ayze +
            '.values' for jyhv__ayze in data_args))


@overload_method(DataFrameType, 'reset_index', inline='always',
    no_unliteral=True)
def overload_dataframe_reset_index(df, level=None, drop=False, inplace=
    False, col_level=0, col_fill='', _bodo_transformed=False):
    check_runtime_cols_unsupported(df, 'DataFrame.reset_index()')
    gqx__cck = dict(col_level=col_level, col_fill=col_fill)
    syjmu__lkfvy = dict(col_level=0, col_fill='')
    check_unsupported_args('DataFrame.reset_index', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    handle_inplace_df_type_change(inplace, _bodo_transformed, 'reset_index')
    if not _is_all_levels(df, level):
        raise_bodo_error(
            'DataFrame.reset_index(): only dropping all index levels supported'
            )
    if not is_overload_constant_bool(drop):
        raise BodoError(
            "DataFrame.reset_index(): 'drop' parameter should be a constant boolean value"
            )
    if not is_overload_constant_bool(inplace):
        raise BodoError(
            "DataFrame.reset_index(): 'inplace' parameter should be a constant boolean value"
            )
    zhuuz__rnab = """def impl(df, level=None, drop=False, inplace=False, col_level=0, col_fill='', _bodo_transformed=False,):
"""
    zhuuz__rnab += (
        '  index = bodo.hiframes.pd_index_ext.init_range_index(0, len(df), 1, None)\n'
        )
    drop = is_overload_true(drop)
    inplace = is_overload_true(inplace)
    columns = df.columns
    data_args = [
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}\n'.
        format(i, '' if inplace else '.copy()') for i in range(len(df.columns))
        ]
    if not drop:
        ecr__nfxyz = 'index' if 'index' not in columns else 'level_0'
        index_names = get_index_names(df.index, 'DataFrame.reset_index()',
            ecr__nfxyz)
        columns = index_names + columns
        if isinstance(df.index, MultiIndexType):
            zhuuz__rnab += (
                '  m_index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
                )
            qeuv__hpop = ['m_index._data[{}]'.format(i) for i in range(df.
                index.nlevels)]
            data_args = qeuv__hpop + data_args
        else:
            jho__cbuo = (
                'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
                )
            data_args = [jho__cbuo] + data_args
    return _gen_init_df(zhuuz__rnab, columns, ', '.join(data_args), 'index')


def _is_all_levels(df, level):
    flr__ffg = len(get_index_data_arr_types(df.index))
    return is_overload_none(level) or is_overload_constant_int(level
        ) and get_overload_const_int(level
        ) == 0 and flr__ffg == 1 or is_overload_constant_list(level) and list(
        get_overload_const_list(level)) == list(range(flr__ffg))


@overload_method(DataFrameType, 'dropna', inline='always', no_unliteral=True)
def overload_dataframe_dropna(df, axis=0, how='any', thresh=None, subset=
    None, inplace=False):
    check_runtime_cols_unsupported(df, 'DataFrame.dropna()')
    if not is_overload_constant_bool(inplace) or is_overload_true(inplace):
        raise BodoError('DataFrame.dropna(): inplace=True is not supported')
    if not is_overload_zero(axis):
        raise_bodo_error(f'df.dropna(): only axis=0 supported')
    ensure_constant_values('dropna', 'how', how, ('any', 'all'))
    if is_overload_none(subset):
        xzli__tjzs = list(range(len(df.columns)))
    elif not is_overload_constant_list(subset):
        raise_bodo_error(
            f'df.dropna(): subset argument should a constant list, not {subset}'
            )
    else:
        hwee__mpko = get_overload_const_list(subset)
        xzli__tjzs = []
        for nyrj__yxhzz in hwee__mpko:
            if nyrj__yxhzz not in df.columns:
                raise_bodo_error(
                    f"df.dropna(): column '{nyrj__yxhzz}' not in data frame columns {df}"
                    )
            xzli__tjzs.append(df.columns.index(nyrj__yxhzz))
    fji__ulh = len(df.columns)
    data_args = ', '.join('data_{}'.format(i) for i in range(fji__ulh))
    zhuuz__rnab = (
        "def impl(df, axis=0, how='any', thresh=None, subset=None, inplace=False):\n"
        )
    for i in range(fji__ulh):
        zhuuz__rnab += (
            '  data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})\n'
            .format(i))
    index = (
        'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
        )
    zhuuz__rnab += (
        """  ({0}, index_arr) = bodo.libs.array_kernels.dropna(({0}, {1}), how, thresh, ({2},))
"""
        .format(data_args, index, ', '.join(str(a) for a in xzli__tjzs)))
    zhuuz__rnab += (
        '  index = bodo.utils.conversion.index_from_array(index_arr)\n')
    return _gen_init_df(zhuuz__rnab, df.columns, data_args, 'index')


@overload_method(DataFrameType, 'drop', inline='always', no_unliteral=True)
def overload_dataframe_drop(df, labels=None, axis=0, index=None, columns=
    None, level=None, inplace=False, errors='raise', _bodo_transformed=False):
    check_runtime_cols_unsupported(df, 'DataFrame.drop()')
    gqx__cck = dict(index=index, level=level, errors=errors)
    syjmu__lkfvy = dict(index=None, level=None, errors='raise')
    check_unsupported_args('DataFrame.drop', gqx__cck, syjmu__lkfvy,
        package_name='pandas', module_name='DataFrame')
    handle_inplace_df_type_change(inplace, _bodo_transformed, 'drop')
    if not is_overload_constant_bool(inplace):
        raise_bodo_error(
            "DataFrame.drop(): 'inplace' parameter should be a constant bool")
    if not is_overload_none(labels):
        if not is_overload_none(columns):
            raise BodoError(
                "Dataframe.drop(): Cannot specify both 'labels' and 'columns'")
        if not is_overload_constant_int(axis) or get_overload_const_int(axis
            ) != 1:
            raise_bodo_error('DataFrame.drop(): only axis=1 supported')
        if is_overload_constant_str(labels):
            iiqo__eglk = get_overload_const_str(labels),
        elif is_overload_constant_list(labels):
            iiqo__eglk = get_overload_const_list(labels)
        else:
            raise_bodo_error(
                'constant list of columns expected for labels in DataFrame.drop()'
                )
    else:
        if is_overload_none(columns):
            raise BodoError(
                "DataFrame.drop(): Need to specify at least one of 'labels' or 'columns'"
                )
        if is_overload_constant_str(columns):
            iiqo__eglk = get_overload_const_str(columns),
        elif is_overload_constant_list(columns):
            iiqo__eglk = get_overload_const_list(columns)
        else:
            raise_bodo_error(
                'constant list of columns expected for labels in DataFrame.drop()'
                )
    for sijzc__erm in iiqo__eglk:
        if sijzc__erm not in df.columns:
            raise_bodo_error(
                'DataFrame.drop(): column {} not in DataFrame columns {}'.
                format(sijzc__erm, df.columns))
    if len(set(iiqo__eglk)) == len(df.columns):
        raise BodoError('DataFrame.drop(): Dropping all columns not supported.'
            )
    inplace = is_overload_true(inplace)
    yvexc__ncpx = tuple(sijzc__erm for sijzc__erm in df.columns if 
        sijzc__erm not in iiqo__eglk)
    data_args = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(df.columns.index(sijzc__erm), '.copy()' if not inplace else
        '') for sijzc__erm in yvexc__ncpx)
    zhuuz__rnab = (
        'def impl(df, labels=None, axis=0, index=None, columns=None,\n')
    zhuuz__rnab += (
        "     level=None, inplace=False, errors='raise', _bodo_transformed=False):\n"
        )
    index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
    return _gen_init_df(zhuuz__rnab, yvexc__ncpx, data_args, index)


@overload_method(DataFrameType, 'append', inline='always', no_unliteral=True)
def overload_dataframe_append(df, other, ignore_index=False,
    verify_integrity=False, sort=None):
    check_runtime_cols_unsupported(df, 'DataFrame.append()')
    check_runtime_cols_unsupported(other, 'DataFrame.append()')
    if isinstance(other, DataFrameType):
        return (lambda df, other, ignore_index=False, verify_integrity=
            False, sort=None: pd.concat((df, other), ignore_index=
            ignore_index, verify_integrity=verify_integrity))
    if isinstance(other, types.BaseTuple):
        return (lambda df, other, ignore_index=False, verify_integrity=
            False, sort=None: pd.concat((df,) + other, ignore_index=
            ignore_index, verify_integrity=verify_integrity))
    if isinstance(other, types.List) and isinstance(other.dtype, DataFrameType
        ):
        return (lambda df, other, ignore_index=False, verify_integrity=
            False, sort=None: pd.concat([df] + other, ignore_index=
            ignore_index, verify_integrity=verify_integrity))
    raise BodoError(
        'invalid df.append() input. Only dataframe and list/tuple of dataframes supported'
        )


@overload_method(DataFrameType, 'sample', inline='always', no_unliteral=True)
def overload_dataframe_sample(df, n=None, frac=None, replace=False, weights
    =None, random_state=None, axis=None, ignore_index=False):
    check_runtime_cols_unsupported(df, 'DataFrame.sample()')
    gqx__cck = dict(random_state=random_state, weights=weights, axis=axis,
        ignore_index=ignore_index)
    rzd__uzh = dict(random_state=None, weights=None, axis=None,
        ignore_index=False)
    check_unsupported_args('DataFrame.sample', gqx__cck, rzd__uzh,
        package_name='pandas', module_name='DataFrame')
    if not is_overload_none(n) and not is_overload_none(frac):
        raise BodoError(
            'DataFrame.sample(): only one of n and frac option can be selected'
            )
    fji__ulh = len(df.columns)
    data_args = ', '.join('data_{}'.format(i) for i in range(fji__ulh))
    gppn__dch = ', '.join('rhs_data_{}'.format(i) for i in range(fji__ulh))
    zhuuz__rnab = """def impl(df, n=None, frac=None, replace=False, weights=None, random_state=None, axis=None, ignore_index=False):
"""
    zhuuz__rnab += '  if (frac == 1 or n == len(df)) and not replace:\n'
    zhuuz__rnab += (
        '    return bodo.allgatherv(bodo.random_shuffle(df), False)\n')
    for i in range(fji__ulh):
        zhuuz__rnab += (
            """  rhs_data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})
"""
            .format(i))
    zhuuz__rnab += '  if frac is None:\n'
    zhuuz__rnab += '    frac_d = -1.0\n'
    zhuuz__rnab += '  else:\n'
    zhuuz__rnab += '    frac_d = frac\n'
    zhuuz__rnab += '  if n is None:\n'
    zhuuz__rnab += '    n_i = 0\n'
    zhuuz__rnab += '  else:\n'
    zhuuz__rnab += '    n_i = n\n'
    index = (
        'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
        )
    zhuuz__rnab += f"""  ({data_args},), index_arr = bodo.libs.array_kernels.sample_table_operation(({gppn__dch},), {index}, n_i, frac_d, replace)
"""
    zhuuz__rnab += (
        '  index = bodo.utils.conversion.index_from_array(index_arr)\n')
    return bodo.hiframes.dataframe_impl._gen_init_df(zhuuz__rnab, df.
        columns, data_args, 'index')


@numba.njit
def _sizeof_fmt(num, size_qualifier=''):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return f'{num:3.1f}{size_qualifier} {x}'
        num /= 1024.0
    return f'{num:3.1f}{size_qualifier} PB'


@overload_method(DataFrameType, 'info', no_unliteral=True)
def overload_dataframe_info(df, verbose=None, buf=None, max_cols=None,
    memory_usage=None, show_counts=None, null_counts=None):
    check_runtime_cols_unsupported(df, 'DataFrame.info()')
    bxk__ruyqa = {'verbose': verbose, 'buf': buf, 'max_cols': max_cols,
        'memory_usage': memory_usage, 'show_counts': show_counts,
        'null_counts': null_counts}
    fyzts__uqjd = {'verbose': None, 'buf': None, 'max_cols': None,
        'memory_usage': None, 'show_counts': None, 'null_counts': None}
    check_unsupported_args('DataFrame.info', bxk__ruyqa, fyzts__uqjd,
        package_name='pandas', module_name='DataFrame')
    uks__row = f"<class '{str(type(df)).split('.')[-1]}"
    if len(df.columns) == 0:

        def _info_impl(df, verbose=None, buf=None, max_cols=None,
            memory_usage=None, show_counts=None, null_counts=None):
            wqs__mht = uks__row + '\n'
            wqs__mht += 'Index: 0 entries\n'
            wqs__mht += 'Empty DataFrame'
            print(wqs__mht)
        return _info_impl
    else:
        zhuuz__rnab = """def _info_impl(df, verbose=None, buf=None, max_cols=None, memory_usage=None, show_counts=None, null_counts=None): #pragma: no cover
"""
        zhuuz__rnab += '    ncols = df.shape[1]\n'
        zhuuz__rnab += f'    lines = "{uks__row}\\n"\n'
        zhuuz__rnab += f'    lines += "{df.index}: "\n'
        zhuuz__rnab += (
            '    index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
            )
        if isinstance(df.index, bodo.hiframes.pd_index_ext.RangeIndexType):
            zhuuz__rnab += """    lines += f"{len(index)} entries, {index.start} to {index.stop-1}\\n\"
"""
        elif isinstance(df.index, bodo.hiframes.pd_index_ext.StringIndexType):
            zhuuz__rnab += """    lines += f"{len(index)} entries, {index[0]} to {index[len(index)-1]}\\n\"
"""
        else:
            zhuuz__rnab += (
                '    lines += f"{len(index)} entries, {index[0]} to {index[-1]}\\n"\n'
                )
        zhuuz__rnab += (
            '    lines += f"Data columns (total {ncols} columns):\\n"\n')
        zhuuz__rnab += (
            f'    space = {max(len(str(k)) for k in df.columns) + 1}\n')
        zhuuz__rnab += '    column_width = max(space, 7)\n'
        zhuuz__rnab += '    column= "Column"\n'
        zhuuz__rnab += '    underl= "------"\n'
        zhuuz__rnab += (
            '    lines += f"#   {column:<{column_width}} Non-Null Count  Dtype\\n"\n'
            )
        zhuuz__rnab += (
            '    lines += f"--- {underl:<{column_width}} --------------  -----\\n"\n'
            )
        zhuuz__rnab += '    mem_size = 0\n'
        zhuuz__rnab += (
            '    col_name = bodo.libs.str_arr_ext.pre_alloc_string_array(ncols, -1)\n'
            )
        zhuuz__rnab += """    non_null_count = bodo.libs.str_arr_ext.pre_alloc_string_array(ncols, -1)
"""
        zhuuz__rnab += (
            '    col_dtype = bodo.libs.str_arr_ext.pre_alloc_string_array(ncols, -1)\n'
            )
        eiyiv__xmuxv = dict()
        for i in range(len(df.columns)):
            zhuuz__rnab += f"""    non_null_count[{i}] = str(bodo.libs.array_ops.array_op_count(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})))
"""
            xtaa__wrp = f'{df.data[i].dtype}'
            if isinstance(df.data[i], bodo.CategoricalArrayType):
                xtaa__wrp = 'category'
            elif isinstance(df.data[i], bodo.IntegerArrayType):
                isgl__ymbi = bodo.libs.int_arr_ext.IntDtype(df.data[i].dtype
                    ).name
                xtaa__wrp = f'{isgl__ymbi[:-7]}'
            zhuuz__rnab += f'    col_dtype[{i}] = "{xtaa__wrp}"\n'
            if xtaa__wrp in eiyiv__xmuxv:
                eiyiv__xmuxv[xtaa__wrp] += 1
            else:
                eiyiv__xmuxv[xtaa__wrp] = 1
            zhuuz__rnab += f'    col_name[{i}] = "{df.columns[i]}"\n'
            zhuuz__rnab += f"""    mem_size += bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).nbytes
"""
        zhuuz__rnab += """    column_info = [f'{i:^3} {name:<{column_width}} {count} non-null      {dtype}' for i, (name, count, dtype) in enumerate(zip(col_name, non_null_count, col_dtype))]
"""
        zhuuz__rnab += '    for i in column_info:\n'
        zhuuz__rnab += "        lines += f'{i}\\n'\n"
        zeu__hbiux = ', '.join(f'{k}({eiyiv__xmuxv[k]})' for k in sorted(
            eiyiv__xmuxv))
        zhuuz__rnab += f"    lines += 'dtypes: {zeu__hbiux}\\n'\n"
        zhuuz__rnab += '    mem_size += df.index.nbytes\n'
        zhuuz__rnab += '    total_size = _sizeof_fmt(mem_size)\n'
        zhuuz__rnab += "    lines += f'memory usage: {total_size}'\n"
        zhuuz__rnab += '    print(lines)\n'
        vowd__xeiyc = {}
        exec(zhuuz__rnab, {'_sizeof_fmt': _sizeof_fmt, 'pd': pd, 'bodo':
            bodo, 'np': np}, vowd__xeiyc)
        _info_impl = vowd__xeiyc['_info_impl']
        return _info_impl


@overload_method(DataFrameType, 'memory_usage', inline='always',
    no_unliteral=True)
def overload_dataframe_memory_usage(df, index=True, deep=False):
    check_runtime_cols_unsupported(df, 'DataFrame.memory_usage()')
    zhuuz__rnab = 'def impl(df, index=True, deep=False):\n'
    data = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).nbytes'
         for i in range(len(df.columns)))
    if is_overload_true(index):
        ysyj__lyedp = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df).nbytes\n,')
        oibtu__biwaw = ','.join(f"'{sijzc__erm}'" for sijzc__erm in df.columns)
        arr = (
            f"bodo.utils.conversion.coerce_to_array(('Index',{oibtu__biwaw}))")
        index = f'bodo.hiframes.pd_index_ext.init_binary_str_index({arr})'
        zhuuz__rnab += f"""  return bodo.hiframes.pd_series_ext.init_series(({ysyj__lyedp}{data}), {index}, None)
"""
    else:
        emfl__hfbdu = ',' if len(df.columns) == 1 else ''
        xjol__duc = gen_const_tup(df.columns)
        zhuuz__rnab += f"""  return bodo.hiframes.pd_series_ext.init_series(({data}{emfl__hfbdu}), pd.Index({xjol__duc}), None)
"""
    vowd__xeiyc = {}
    exec(zhuuz__rnab, {'bodo': bodo, 'pd': pd}, vowd__xeiyc)
    impl = vowd__xeiyc['impl']
    return impl


@overload(pd.read_excel, no_unliteral=True)
def overload_read_excel(io, sheet_name=0, header=0, names=None, index_col=
    None, usecols=None, squeeze=False, dtype=None, engine=None, converters=
    None, true_values=None, false_values=None, skiprows=None, nrows=None,
    na_values=None, keep_default_na=True, na_filter=True, verbose=False,
    parse_dates=False, date_parser=None, thousands=None, comment=None,
    skipfooter=0, convert_float=True, mangle_dupe_cols=True, _bodo_df_type=None
    ):
    df_type = _bodo_df_type.instance_type
    ugwpn__mvout = 'read_excel_df{}'.format(next_label())
    setattr(types, ugwpn__mvout, df_type)
    afeez__tdx = False
    if is_overload_constant_list(parse_dates):
        afeez__tdx = get_overload_const_list(parse_dates)
    mquar__oyt = ', '.join(["'{}':{}".format(cname, _get_pd_dtype_str(t)) for
        cname, t in zip(df_type.columns, df_type.data)])
    zhuuz__rnab = (
        """
def impl(
    io,
    sheet_name=0,
    header=0,
    names=None,
    index_col=None,
    usecols=None,
    squeeze=False,
    dtype=None,
    engine=None,
    converters=None,
    true_values=None,
    false_values=None,
    skiprows=None,
    nrows=None,
    na_values=None,
    keep_default_na=True,
    na_filter=True,
    verbose=False,
    parse_dates=False,
    date_parser=None,
    thousands=None,
    comment=None,
    skipfooter=0,
    convert_float=True,
    mangle_dupe_cols=True,
    _bodo_df_type=None,
):
    with numba.objmode(df="{}"):
        df = pd.read_excel(
            io,
            sheet_name,
            header,
            {},
            index_col,
            usecols,
            squeeze,
            {{{}}},
            engine,
            converters,
            true_values,
            false_values,
            skiprows,
            nrows,
            na_values,
            keep_default_na,
            na_filter,
            verbose,
            {},
            date_parser,
            thousands,
            comment,
            skipfooter,
            convert_float,
            mangle_dupe_cols,
        )
    return df
    """
        .format(ugwpn__mvout, list(df_type.columns), mquar__oyt, afeez__tdx))
    vowd__xeiyc = {}
    exec(zhuuz__rnab, globals(), vowd__xeiyc)
    impl = vowd__xeiyc['impl']
    return impl


def overload_dataframe_plot(df, x=None, y=None, kind='line', figsize=None,
    xlabel=None, ylabel=None, title=None, legend=True, fontsize=None,
    xticks=None, yticks=None, ax=None):
    try:
        import matplotlib.pyplot as plt
    except ImportError as yxp__zatb:
        raise BodoError('df.plot needs matplotllib which is not installed.')
    zhuuz__rnab = (
        "def impl(df, x=None, y=None, kind='line', figsize=None, xlabel=None, \n"
        )
    zhuuz__rnab += (
        '    ylabel=None, title=None, legend=True, fontsize=None, \n')
    zhuuz__rnab += '    xticks=None, yticks=None, ax=None):\n'
    if is_overload_none(ax):
        zhuuz__rnab += '   fig, ax = plt.subplots()\n'
    else:
        zhuuz__rnab += '   fig = ax.get_figure()\n'
    if not is_overload_none(figsize):
        zhuuz__rnab += '   fig.set_figwidth(figsize[0])\n'
        zhuuz__rnab += '   fig.set_figheight(figsize[1])\n'
    if is_overload_none(xlabel):
        zhuuz__rnab += '   xlabel = x\n'
    zhuuz__rnab += '   ax.set_xlabel(xlabel)\n'
    if is_overload_none(ylabel):
        zhuuz__rnab += '   ylabel = y\n'
    else:
        zhuuz__rnab += '   ax.set_ylabel(ylabel)\n'
    if not is_overload_none(title):
        zhuuz__rnab += '   ax.set_title(title)\n'
    if not is_overload_none(fontsize):
        zhuuz__rnab += '   ax.tick_params(labelsize=fontsize)\n'
    kind = get_overload_const_str(kind)
    if kind == 'line':
        if is_overload_none(x) and is_overload_none(y):
            for i in range(len(df.columns)):
                if isinstance(df.data[i], (types.Array, IntegerArrayType)
                    ) and isinstance(df.data[i].dtype, (types.Integer,
                    types.Float)):
                    zhuuz__rnab += (
                        f'   ax.plot(df.iloc[:, {i}], label=df.columns[{i}])\n'
                        )
        elif is_overload_none(x):
            zhuuz__rnab += '   ax.plot(df[y], label=y)\n'
        elif is_overload_none(y):
            lqi__zmnj = get_overload_const_str(x)
            alb__bba = df.columns.index(lqi__zmnj)
            for i in range(len(df.columns)):
                if isinstance(df.data[i], (types.Array, IntegerArrayType)
                    ) and isinstance(df.data[i].dtype, (types.Integer,
                    types.Float)):
                    if alb__bba != i:
                        zhuuz__rnab += f"""   ax.plot(df[x], df.iloc[:, {i}], label=df.columns[{i}])
"""
        else:
            zhuuz__rnab += '   ax.plot(df[x], df[y], label=y)\n'
    elif kind == 'scatter':
        legend = False
        zhuuz__rnab += '   ax.scatter(df[x], df[y], s=20)\n'
        zhuuz__rnab += '   ax.set_ylabel(ylabel)\n'
    if not is_overload_none(xticks):
        zhuuz__rnab += '   ax.set_xticks(xticks)\n'
    if not is_overload_none(yticks):
        zhuuz__rnab += '   ax.set_yticks(yticks)\n'
    if is_overload_true(legend):
        zhuuz__rnab += '   ax.legend()\n'
    zhuuz__rnab += '   return ax\n'
    vowd__xeiyc = {}
    exec(zhuuz__rnab, {'bodo': bodo, 'plt': plt}, vowd__xeiyc)
    impl = vowd__xeiyc['impl']
    return impl


@lower_builtin('df.plot', DataFrameType, types.VarArg(types.Any))
def dataframe_plot_low(context, builder, sig, args):
    impl = overload_dataframe_plot(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


def is_df_values_numpy_supported_dftyp(df_typ):
    for pkuxr__oyiws in df_typ.data:
        if not (isinstance(pkuxr__oyiws, IntegerArrayType) or isinstance(
            pkuxr__oyiws.dtype, types.Number) or pkuxr__oyiws.dtype in (
            bodo.datetime64ns, bodo.timedelta64ns)):
            return False
    return True


def typeref_to_type(v):
    if isinstance(v, types.BaseTuple):
        return types.BaseTuple.from_types(tuple(typeref_to_type(a) for a in v))
    return v.instance_type if isinstance(v, (types.TypeRef, types.NumberClass)
        ) else v


def _install_typer_for_type(type_name, typ):

    @type_callable(typ)
    def type_call_type(context):

        def typer(*args, **kws):
            args = tuple(typeref_to_type(v) for v in args)
            kws = {name: typeref_to_type(v) for name, v in kws.items()}
            return types.TypeRef(typ(*args, **kws))
        return typer
    no_side_effect_call_tuples.add((type_name, bodo))
    no_side_effect_call_tuples.add((typ,))


def _install_type_call_typers():
    for type_name in bodo_types_with_params:
        typ = getattr(bodo, type_name)
        _install_typer_for_type(type_name, typ)


_install_type_call_typers()


def set_df_col(df, cname, arr, inplace):
    df[cname] = arr


@infer_global(set_df_col)
class SetDfColInfer(AbstractTemplate):

    def generic(self, args, kws):
        from bodo.hiframes.pd_dataframe_ext import DataFrameType
        assert not kws
        assert len(args) == 4
        assert isinstance(args[1], types.Literal)
        nrb__tivem = args[0]
        hihca__iqddm = args[1].literal_value
        val = args[2]
        assert val != types.unknown
        iutp__lxyo = nrb__tivem
        check_runtime_cols_unsupported(nrb__tivem, 'set_df_col()')
        if isinstance(nrb__tivem, DataFrameType):
            index = nrb__tivem.index
            if len(nrb__tivem.columns) == 0:
                index = bodo.hiframes.pd_index_ext.RangeIndexType(types.none)
            if isinstance(val, SeriesType):
                if len(nrb__tivem.columns) == 0:
                    index = val.index
                val = val.data
            if is_pd_index_type(val):
                val = bodo.utils.typing.get_index_data_arr_types(val)[0]
            if isinstance(val, types.List):
                val = dtype_to_array_type(val.dtype)
            if not is_array_typ(val):
                val = dtype_to_array_type(val)
            if hihca__iqddm in nrb__tivem.columns:
                yvexc__ncpx = nrb__tivem.columns
                iwv__zigwb = nrb__tivem.columns.index(hihca__iqddm)
                ncn__owa = list(nrb__tivem.data)
                ncn__owa[iwv__zigwb] = val
                ncn__owa = tuple(ncn__owa)
            else:
                yvexc__ncpx = nrb__tivem.columns + (hihca__iqddm,)
                ncn__owa = nrb__tivem.data + (val,)
            iutp__lxyo = DataFrameType(ncn__owa, index, yvexc__ncpx,
                nrb__tivem.dist, nrb__tivem.is_table_format)
        return iutp__lxyo(*args)


SetDfColInfer.prefer_literal = True


def _parse_query_expr(expr, env, columns, cleaned_columns, index_name=None,
    join_cleaned_cols=()):
    lih__kgvwo = {}

    def _rewrite_membership_op(self, node, left, right):
        zbyl__cwgoe = node.op
        op = self.visit(zbyl__cwgoe)
        return op, zbyl__cwgoe, left, right

    def _maybe_evaluate_binop(self, op, op_class, lhs, rhs, eval_in_python=
        ('in', 'not in'), maybe_eval_in_python=('==', '!=', '<', '>', '<=',
        '>=')):
        res = op(lhs, rhs)
        return res
    ibdv__lyd = []


    class NewFuncNode(pd.core.computation.ops.FuncNode):

        def __init__(self, name):
            if (name not in pd.core.computation.ops.MATHOPS or pd.core.
                computation.check._NUMEXPR_INSTALLED and pd.core.
                computation.check_NUMEXPR_VERSION < pd.core.computation.ops
                .LooseVersion('2.6.9') and name in ('floor', 'ceil')):
                if name not in ibdv__lyd:
                    raise BodoError('"{0}" is not a supported function'.
                        format(name))
            self.name = name
            if name in ibdv__lyd:
                self.func = name
            else:
                self.func = getattr(np, name)

        def __call__(self, *args):
            return pd.core.computation.ops.MathCall(self, args)

        def __repr__(self):
            return pd.io.formats.printing.pprint_thing(self.name)

    def visit_Attribute(self, node, **kwargs):
        zhhf__nxke = node.attr
        value = node.value
        kqz__xvs = pd.core.computation.ops.LOCAL_TAG
        if zhhf__nxke in ('str', 'dt'):
            try:
                bsda__wtp = str(self.visit(value))
            except pd.core.computation.ops.UndefinedVariableError as kecd__yuyw:
                col_name = kecd__yuyw.args[0].split("'")[1]
                raise BodoError(
                    'df.query(): column {} is not found in dataframe columns {}'
                    .format(col_name, columns))
        else:
            bsda__wtp = str(self.visit(value))
        dif__irqwv = bsda__wtp, zhhf__nxke
        if dif__irqwv in join_cleaned_cols:
            zhhf__nxke = join_cleaned_cols[dif__irqwv]
        name = bsda__wtp + '.' + zhhf__nxke
        if name.startswith(kqz__xvs):
            name = name[len(kqz__xvs):]
        if zhhf__nxke in ('str', 'dt'):
            cldx__ckhwr = columns[cleaned_columns.index(bsda__wtp)]
            lih__kgvwo[cldx__ckhwr] = bsda__wtp
            self.env.scope[name] = 0
            return self.term_type(kqz__xvs + name, self.env)
        ibdv__lyd.append(name)
        return NewFuncNode(name)

    def __str__(self):
        if isinstance(self.value, list):
            return '{}'.format(self.value)
        if isinstance(self.value, str):
            return "'{}'".format(self.value)
        return pd.io.formats.printing.pprint_thing(self.name)

    def math__str__(self):
        if self.op in ibdv__lyd:
            return pd.io.formats.printing.pprint_thing('{0}({1})'.format(
                self.op, ','.join(map(str, self.operands))))
        ygra__hcdl = map(lambda a:
            'bodo.hiframes.pd_series_ext.get_series_data({})'.format(str(a)
            ), self.operands)
        op = 'np.{}'.format(self.op)
        hihca__iqddm = (
            'bodo.hiframes.pd_index_ext.init_range_index(0, len({}), 1, None)'
            .format(str(self.operands[0])))
        return pd.io.formats.printing.pprint_thing(
            'bodo.hiframes.pd_series_ext.init_series({0}({1}), {2})'.format
            (op, ','.join(ygra__hcdl), hihca__iqddm))

    def op__str__(self):
        vwp__rsqd = ('({0})'.format(pd.io.formats.printing.pprint_thing(
            csg__qijg)) for csg__qijg in self.operands)
        if self.op == 'in':
            return pd.io.formats.printing.pprint_thing(
                'bodo.hiframes.pd_dataframe_ext.val_isin_dummy({})'.format(
                ', '.join(vwp__rsqd)))
        if self.op == 'not in':
            return pd.io.formats.printing.pprint_thing(
                'bodo.hiframes.pd_dataframe_ext.val_notin_dummy({})'.format
                (', '.join(vwp__rsqd)))
        return pd.io.formats.printing.pprint_thing(' {0} '.format(self.op).
            join(vwp__rsqd))
    ysf__cboiy = (pd.core.computation.expr.BaseExprVisitor.
        _rewrite_membership_op)
    wwxy__igje = pd.core.computation.expr.BaseExprVisitor._maybe_evaluate_binop
    epw__jlm = pd.core.computation.expr.BaseExprVisitor.visit_Attribute
    yjwo__jxelh = (pd.core.computation.expr.BaseExprVisitor.
        _maybe_downcast_constants)
    prn__fsu = pd.core.computation.ops.Term.__str__
    bof__tbmhe = pd.core.computation.ops.MathCall.__str__
    hcmsz__mnvu = pd.core.computation.ops.Op.__str__
    ywj__sfk = pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops
    try:
        pd.core.computation.expr.BaseExprVisitor._rewrite_membership_op = (
            _rewrite_membership_op)
        pd.core.computation.expr.BaseExprVisitor._maybe_evaluate_binop = (
            _maybe_evaluate_binop)
        pd.core.computation.expr.BaseExprVisitor.visit_Attribute = (
            visit_Attribute)
        (pd.core.computation.expr.BaseExprVisitor._maybe_downcast_constants
            ) = lambda self, left, right: (left, right)
        pd.core.computation.ops.Term.__str__ = __str__
        pd.core.computation.ops.MathCall.__str__ = math__str__
        pd.core.computation.ops.Op.__str__ = op__str__
        pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops = (lambda
            self: None)
        wbjqq__wyfl = pd.core.computation.expr.Expr(expr, env=env)
        cwcsr__wpz = str(wbjqq__wyfl)
    except pd.core.computation.ops.UndefinedVariableError as kecd__yuyw:
        if not is_overload_none(index_name) and get_overload_const_str(
            index_name) == kecd__yuyw.args[0].split("'")[1]:
            raise BodoError(
                "df.query(): Refering to named index ('{}') by name is not supported"
                .format(get_overload_const_str(index_name)))
        else:
            raise BodoError(f'df.query(): undefined variable, {kecd__yuyw}')
    finally:
        pd.core.computation.expr.BaseExprVisitor._rewrite_membership_op = (
            ysf__cboiy)
        pd.core.computation.expr.BaseExprVisitor._maybe_evaluate_binop = (
            wwxy__igje)
        pd.core.computation.expr.BaseExprVisitor.visit_Attribute = epw__jlm
        (pd.core.computation.expr.BaseExprVisitor._maybe_downcast_constants
            ) = yjwo__jxelh
        pd.core.computation.ops.Term.__str__ = prn__fsu
        pd.core.computation.ops.MathCall.__str__ = bof__tbmhe
        pd.core.computation.ops.Op.__str__ = hcmsz__mnvu
        pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops = ywj__sfk
    mum__kqf = pd.core.computation.parsing.clean_column_name
    lih__kgvwo.update({sijzc__erm: mum__kqf(sijzc__erm) for sijzc__erm in
        columns if mum__kqf(sijzc__erm) in wbjqq__wyfl.names})
    return wbjqq__wyfl, cwcsr__wpz, lih__kgvwo


class DataFrameTupleIterator(types.SimpleIteratorType):

    def __init__(self, col_names, arr_typs):
        self.array_types = arr_typs
        self.col_names = col_names
        cvin__mgxms = ['{}={}'.format(col_names[i], arr_typs[i]) for i in
            range(len(col_names))]
        name = 'itertuples({})'.format(','.join(cvin__mgxms))
        szb__krj = namedtuple('Pandas', col_names)
        wxor__bpqcv = types.NamedTuple([_get_series_dtype(a) for a in
            arr_typs], szb__krj)
        super(DataFrameTupleIterator, self).__init__(name, wxor__bpqcv)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


def _get_series_dtype(arr_typ):
    if arr_typ == types.Array(types.NPDatetime('ns'), 1, 'C'):
        return pd_timestamp_type
    return arr_typ.dtype


def get_itertuples():
    pass


@infer_global(get_itertuples)
class TypeIterTuples(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) % 2 == 0, 'name and column pairs expected'
        col_names = [a.literal_value for a in args[:len(args) // 2]]
        gdiyy__dwf = [if_series_to_array_type(a) for a in args[len(args) // 2:]
            ]
        assert 'Index' not in col_names[0]
        col_names = ['Index'] + col_names
        gdiyy__dwf = [types.Array(types.int64, 1, 'C')] + gdiyy__dwf
        jvxr__xsjo = DataFrameTupleIterator(col_names, gdiyy__dwf)
        return jvxr__xsjo(*args)


TypeIterTuples.prefer_literal = True


@register_model(DataFrameTupleIterator)
class DataFrameTupleIteratorModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        pgia__kjpsa = [('index', types.EphemeralPointer(types.uintp))] + [(
            'array{}'.format(i), arr) for i, arr in enumerate(fe_type.
            array_types[1:])]
        super(DataFrameTupleIteratorModel, self).__init__(dmm, fe_type,
            pgia__kjpsa)

    def from_return(self, builder, value):
        return value


@lower_builtin(get_itertuples, types.VarArg(types.Any))
def get_itertuples_impl(context, builder, sig, args):
    dpw__jjv = args[len(args) // 2:]
    fpxn__omjlb = sig.args[len(sig.args) // 2:]
    rmc__aaxev = context.make_helper(builder, sig.return_type)
    peic__zgunw = context.get_constant(types.intp, 0)
    bioh__ajkh = cgutils.alloca_once_value(builder, peic__zgunw)
    rmc__aaxev.index = bioh__ajkh
    for i, arr in enumerate(dpw__jjv):
        setattr(rmc__aaxev, 'array{}'.format(i), arr)
    for arr, arr_typ in zip(dpw__jjv, fpxn__omjlb):
        context.nrt.incref(builder, arr_typ, arr)
    res = rmc__aaxev._getvalue()
    return impl_ret_new_ref(context, builder, sig.return_type, res)


@lower_builtin('getiter', DataFrameTupleIterator)
def getiter_itertuples(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@lower_builtin('iternext', DataFrameTupleIterator)
@iternext_impl(RefType.UNTRACKED)
def iternext_itertuples(context, builder, sig, args, result):
    wjumi__dfzbq, = sig.args
    tfoy__amh, = args
    rmc__aaxev = context.make_helper(builder, wjumi__dfzbq, value=tfoy__amh)
    ndu__alt = signature(types.intp, wjumi__dfzbq.array_types[1])
    usipt__adyz = context.compile_internal(builder, lambda a: len(a),
        ndu__alt, [rmc__aaxev.array0])
    index = builder.load(rmc__aaxev.index)
    zyeb__lka = builder.icmp(lc.ICMP_SLT, index, usipt__adyz)
    result.set_valid(zyeb__lka)
    with builder.if_then(zyeb__lka):
        values = [index]
        for i, arr_typ in enumerate(wjumi__dfzbq.array_types[1:]):
            hwld__zhsm = getattr(rmc__aaxev, 'array{}'.format(i))
            if arr_typ == types.Array(types.NPDatetime('ns'), 1, 'C'):
                jaorb__putdt = signature(pd_timestamp_type, arr_typ, types.intp
                    )
                val = context.compile_internal(builder, lambda a, i: bodo.
                    hiframes.pd_timestamp_ext.
                    convert_datetime64_to_timestamp(np.int64(a[i])),
                    jaorb__putdt, [hwld__zhsm, index])
            else:
                jaorb__putdt = signature(arr_typ.dtype, arr_typ, types.intp)
                val = context.compile_internal(builder, lambda a, i: a[i],
                    jaorb__putdt, [hwld__zhsm, index])
            values.append(val)
        value = context.make_tuple(builder, wjumi__dfzbq.yield_type, values)
        result.yield_(value)
        qzlx__cuyq = cgutils.increment_index(builder, index)
        builder.store(qzlx__cuyq, rmc__aaxev.index)


def _analyze_op_pair_first(self, scope, equiv_set, expr, lhs):
    typ = self.typemap[expr.value.name].first_type
    if not isinstance(typ, types.NamedTuple):
        return None
    lhs = ir.Var(scope, mk_unique_var('tuple_var'), expr.loc)
    self.typemap[lhs.name] = typ
    rhs = ir.Expr.pair_first(expr.value, expr.loc)
    ocqa__kbi = ir.Assign(rhs, lhs, expr.loc)
    dipli__mll = lhs
    mpryr__xlc = []
    zxiz__pwfh = []
    agjf__scivf = typ.count
    for i in range(agjf__scivf):
        ptyc__oato = ir.Var(dipli__mll.scope, mk_unique_var('{}_size{}'.
            format(dipli__mll.name, i)), dipli__mll.loc)
        zbl__vogwa = ir.Expr.static_getitem(lhs, i, None, dipli__mll.loc)
        self.calltypes[zbl__vogwa] = None
        mpryr__xlc.append(ir.Assign(zbl__vogwa, ptyc__oato, dipli__mll.loc))
        self._define(equiv_set, ptyc__oato, types.intp, zbl__vogwa)
        zxiz__pwfh.append(ptyc__oato)
    ubbz__kjdj = tuple(zxiz__pwfh)
    return numba.parfors.array_analysis.ArrayAnalysis.AnalyzeResult(shape=
        ubbz__kjdj, pre=[ocqa__kbi] + mpryr__xlc)


numba.parfors.array_analysis.ArrayAnalysis._analyze_op_pair_first = (
    _analyze_op_pair_first)
