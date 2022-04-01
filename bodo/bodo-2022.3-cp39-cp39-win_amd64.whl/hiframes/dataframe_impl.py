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
        fgvcx__agx = f'bodo.utils.conversion.coerce_to_array({col_names})'
        return (
            f'bodo.hiframes.pd_index_ext.init_binary_str_index({fgvcx__agx})\n'
            )
    elif all(isinstance(a, (int, float)) for a in col_names):
        arr = f'bodo.utils.conversion.coerce_to_array({col_names})'
        return f'bodo.hiframes.pd_index_ext.init_numeric_index({arr})\n'
    else:
        return f'bodo.hiframes.pd_index_ext.init_heter_index({col_names})\n'


@overload_attribute(DataFrameType, 'columns', inline='always')
def overload_dataframe_columns(df):
    aqh__aifei = 'def impl(df):\n'
    if df.has_runtime_cols:
        aqh__aifei += (
            '  return bodo.hiframes.pd_dataframe_ext.get_dataframe_column_names(df)\n'
            )
    else:
        gzm__knc = (bodo.hiframes.dataframe_impl.
            generate_col_to_index_func_text(df.columns))
        aqh__aifei += f'  return {gzm__knc}'
    iyph__amgxq = {}
    exec(aqh__aifei, {'bodo': bodo}, iyph__amgxq)
    impl = iyph__amgxq['impl']
    return impl


@overload_attribute(DataFrameType, 'values')
def overload_dataframe_values(df):
    check_runtime_cols_unsupported(df, 'DataFrame.values')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.values')
    if not is_df_values_numpy_supported_dftyp(df):
        raise_bodo_error(
            'DataFrame.values: only supported for dataframes containing numeric values'
            )
    gac__vkh = len(df.columns)
    wcf__hjjsx = set(i for i in range(gac__vkh) if isinstance(df.data[i],
        IntegerArrayType))
    data_args = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(i, '.astype(float)' if i in wcf__hjjsx else '') for i in
        range(gac__vkh))
    aqh__aifei = 'def f(df):\n'.format()
    aqh__aifei += '    return np.stack(({},), 1)\n'.format(data_args)
    iyph__amgxq = {}
    exec(aqh__aifei, {'bodo': bodo, 'np': np}, iyph__amgxq)
    fso__eemq = iyph__amgxq['f']
    return fso__eemq


@overload_method(DataFrameType, 'to_numpy', inline='always', no_unliteral=True)
def overload_dataframe_to_numpy(df, dtype=None, copy=False, na_value=_no_input
    ):
    check_runtime_cols_unsupported(df, 'DataFrame.to_numpy()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.to_numpy()')
    if not is_df_values_numpy_supported_dftyp(df):
        raise_bodo_error(
            'DataFrame.to_numpy(): only supported for dataframes containing numeric values'
            )
    vbjk__zasha = {'dtype': dtype, 'na_value': na_value}
    pwrz__jhve = {'dtype': None, 'na_value': _no_input}
    check_unsupported_args('DataFrame.to_numpy', vbjk__zasha, pwrz__jhve,
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
            lzutk__cxqi = bodo.hiframes.table.compute_num_runtime_columns(t)
            return lzutk__cxqi * len(t)
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
            lzutk__cxqi = bodo.hiframes.table.compute_num_runtime_columns(t)
            return len(t), lzutk__cxqi
        return impl
    ncols = len(df.columns)
    return lambda df: (len(df), types.int64(ncols))


@overload_attribute(DataFrameType, 'dtypes')
def overload_dataframe_dtypes(df):
    check_runtime_cols_unsupported(df, 'DataFrame.dtypes')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.dtypes')
    aqh__aifei = 'def impl(df):\n'
    data = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).dtype\n'
         for i in range(len(df.columns)))
    srg__bttm = ',' if len(df.columns) == 1 else ''
    index = f'bodo.hiframes.pd_index_ext.init_heter_index({df.columns})'
    aqh__aifei += f"""  return bodo.hiframes.pd_series_ext.init_series(({data}{srg__bttm}), {index}, None)
"""
    iyph__amgxq = {}
    exec(aqh__aifei, {'bodo': bodo}, iyph__amgxq)
    impl = iyph__amgxq['impl']
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
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.astype()')
    vbjk__zasha = {'copy': copy, 'errors': errors}
    pwrz__jhve = {'copy': True, 'errors': 'raise'}
    check_unsupported_args('df.astype', vbjk__zasha, pwrz__jhve,
        package_name='pandas', module_name='DataFrame')
    if dtype == types.unicode_type:
        raise_bodo_error(
            "DataFrame.astype(): 'dtype' when passed as string must be a constant value"
            )
    extra_globals = None
    if _bodo_object_typeref is not None:
        assert isinstance(_bodo_object_typeref, types.TypeRef
            ), 'Bodo schema used in DataFrame.astype should be a TypeRef'
        dqqk__zgwkk = _bodo_object_typeref.instance_type
        assert isinstance(dqqk__zgwkk, DataFrameType
            ), 'Bodo schema used in DataFrame.astype is only supported for DataFrame schemas'
        extra_globals = {}
        gju__xco = {}
        for i, name in enumerate(dqqk__zgwkk.columns):
            arr_typ = dqqk__zgwkk.data[i]
            if isinstance(arr_typ, IntegerArrayType):
                yjju__rgzdz = bodo.libs.int_arr_ext.IntDtype(arr_typ.dtype)
            elif arr_typ == boolean_array:
                yjju__rgzdz = boolean_dtype
            else:
                yjju__rgzdz = arr_typ.dtype
            extra_globals[f'_bodo_schema{i}'] = yjju__rgzdz
            gju__xco[name] = f'_bodo_schema{i}'
        data_args = ', '.join(
            f'bodo.utils.conversion.fix_arr_dtype(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), {gju__xco[ejinc__sxyv]}, copy, nan_to_str=_bodo_nan_to_str, from_series=True)'
             if ejinc__sxyv in gju__xco else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})' for
            i, ejinc__sxyv in enumerate(df.columns))
    elif is_overload_constant_dict(dtype) or is_overload_constant_series(dtype
        ):
        jkyrn__njw = get_overload_constant_dict(dtype
            ) if is_overload_constant_dict(dtype) else dict(
            get_overload_constant_series(dtype))
        data_args = ', '.join(
            f'bodo.utils.conversion.fix_arr_dtype(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), {_get_dtype_str(jkyrn__njw[ejinc__sxyv])}, copy, nan_to_str=_bodo_nan_to_str, from_series=True)'
             if ejinc__sxyv in jkyrn__njw else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})' for
            i, ejinc__sxyv in enumerate(df.columns))
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
    lii__janj = []
    for i in range(len(df.columns)):
        arr = f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})'
        if is_overload_true(deep):
            lii__janj.append(arr + '.copy()')
        elif is_overload_false(deep):
            lii__janj.append(arr)
        else:
            lii__janj.append(f'{arr}.copy() if deep else {arr}')
    header = 'def impl(df, deep=True):\n'
    return _gen_init_df(header, df.columns, ', '.join(lii__janj))


@overload_method(DataFrameType, 'rename', inline='always', no_unliteral=True)
def overload_dataframe_rename(df, mapper=None, index=None, columns=None,
    axis=None, copy=True, inplace=False, level=None, errors='ignore',
    _bodo_transformed=False):
    check_runtime_cols_unsupported(df, 'DataFrame.rename()')
    handle_inplace_df_type_change(inplace, _bodo_transformed, 'rename')
    vbjk__zasha = {'index': index, 'level': level, 'errors': errors}
    pwrz__jhve = {'index': None, 'level': None, 'errors': 'ignore'}
    check_unsupported_args('DataFrame.rename', vbjk__zasha, pwrz__jhve,
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
        jhu__qro = get_overload_constant_dict(mapper)
    elif not is_overload_none(columns):
        if not is_overload_none(axis):
            raise BodoError(
                "DataFrame.rename(): Cannot specify both 'axis' and 'columns'")
        if not is_overload_constant_dict(columns):
            raise_bodo_error(
                "'columns' argument to DataFrame.rename() should be a constant dictionary"
                )
        jhu__qro = get_overload_constant_dict(columns)
    else:
        raise_bodo_error(
            "DataFrame.rename(): must pass columns either via 'mapper' and 'axis'=1 or 'columns'"
            )
    lklz__ohn = [jhu__qro.get(df.columns[i], df.columns[i]) for i in range(
        len(df.columns))]
    lii__janj = []
    for i in range(len(df.columns)):
        arr = f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})'
        if is_overload_true(copy):
            lii__janj.append(arr + '.copy()')
        elif is_overload_false(copy):
            lii__janj.append(arr)
        else:
            lii__janj.append(f'{arr}.copy() if copy else {arr}')
    header = """def impl(df, mapper=None, index=None, columns=None, axis=None, copy=True, inplace=False, level=None, errors='ignore', _bodo_transformed=False):
"""
    return _gen_init_df(header, lklz__ohn, ', '.join(lii__janj))


@overload_method(DataFrameType, 'filter', no_unliteral=True)
def overload_dataframe_filter(df, items=None, like=None, regex=None, axis=None
    ):
    check_runtime_cols_unsupported(df, 'DataFrame.filter()')
    zam__ksoya = not is_overload_none(items)
    vkqpj__qjxvs = not is_overload_none(like)
    vii__lme = not is_overload_none(regex)
    mgf__jfve = zam__ksoya ^ vkqpj__qjxvs ^ vii__lme
    ajyy__qbx = not (zam__ksoya or vkqpj__qjxvs or vii__lme)
    if ajyy__qbx:
        raise BodoError(
            'DataFrame.filter(): one of keyword arguments `items`, `like`, and `regex` must be supplied'
            )
    if not mgf__jfve:
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
        fgoew__cwykz = 0 if axis == 'index' else 1
    elif is_overload_constant_int(axis):
        axis = get_overload_const_int(axis)
        if axis not in {0, 1}:
            raise_bodo_error(
                'DataFrame.filter(): keyword arguments `axis` must be either 0 or 1 if integer'
                )
        fgoew__cwykz = axis
    else:
        raise_bodo_error(
            'DataFrame.filter(): keyword arguments `axis` must be constant string or integer'
            )
    assert fgoew__cwykz in {0, 1}
    aqh__aifei = (
        'def impl(df, items=None, like=None, regex=None, axis=None):\n')
    if fgoew__cwykz == 0:
        raise BodoError(
            'DataFrame.filter(): filtering based on index is not supported.')
    if fgoew__cwykz == 1:
        voksx__mqzz = []
        bnrmi__uqieg = []
        uxrlw__uveqi = []
        if zam__ksoya:
            if is_overload_constant_list(items):
                nyzxs__qgc = get_overload_const_list(items)
            else:
                raise BodoError(
                    "Dataframe.filter(): argument 'items' must be a list of constant strings."
                    )
        if vkqpj__qjxvs:
            if is_overload_constant_str(like):
                ohue__hyovq = get_overload_const_str(like)
            else:
                raise BodoError(
                    "Dataframe.filter(): argument 'like' must be a constant string."
                    )
        if vii__lme:
            if is_overload_constant_str(regex):
                vwlm__pjvr = get_overload_const_str(regex)
                ovhr__rdxop = re.compile(vwlm__pjvr)
            else:
                raise BodoError(
                    "Dataframe.filter(): argument 'regex' must be a constant string."
                    )
        for i, ejinc__sxyv in enumerate(df.columns):
            if not is_overload_none(items
                ) and ejinc__sxyv in nyzxs__qgc or not is_overload_none(like
                ) and ohue__hyovq in str(ejinc__sxyv) or not is_overload_none(
                regex) and ovhr__rdxop.search(str(ejinc__sxyv)):
                bnrmi__uqieg.append(ejinc__sxyv)
                uxrlw__uveqi.append(i)
        for i in uxrlw__uveqi:
            pxt__pbkzl = f'data_{i}'
            voksx__mqzz.append(pxt__pbkzl)
            aqh__aifei += f"""  {pxt__pbkzl} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})
"""
        data_args = ', '.join(voksx__mqzz)
        return _gen_init_df(aqh__aifei, bnrmi__uqieg, data_args)


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
    fjm__gew = is_overload_none(include)
    gyyni__udyde = is_overload_none(exclude)
    blk__pvrf = 'DataFrame.select_dtypes'
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.select_dtypes()')
    if fjm__gew and gyyni__udyde:
        raise_bodo_error(
            'DataFrame.select_dtypes() At least one of include or exclude must not be none'
            )

    def is_legal_input(elem):
        return is_overload_constant_str(elem) or isinstance(elem, types.
            DTypeSpec) or isinstance(elem, types.Function)
    if not fjm__gew:
        if is_overload_constant_list(include):
            include = get_overload_const_list(include)
            pff__vfen = [dtype_to_array_type(parse_dtype(elem, blk__pvrf)) for
                elem in include]
        elif is_legal_input(include):
            pff__vfen = [dtype_to_array_type(parse_dtype(include, blk__pvrf))]
        else:
            raise_bodo_error(
                'DataFrame.select_dtypes() only supports constant strings or types as arguments'
                )
        pff__vfen = get_nullable_and_non_nullable_types(pff__vfen)
        pfm__loix = tuple(ejinc__sxyv for i, ejinc__sxyv in enumerate(df.
            columns) if df.data[i] in pff__vfen)
    else:
        pfm__loix = df.columns
    if not gyyni__udyde:
        if is_overload_constant_list(exclude):
            exclude = get_overload_const_list(exclude)
            prvab__twpsp = [dtype_to_array_type(parse_dtype(elem, blk__pvrf
                )) for elem in exclude]
        elif is_legal_input(exclude):
            prvab__twpsp = [dtype_to_array_type(parse_dtype(exclude,
                blk__pvrf))]
        else:
            raise_bodo_error(
                'DataFrame.select_dtypes() only supports constant strings or types as arguments'
                )
        prvab__twpsp = get_nullable_and_non_nullable_types(prvab__twpsp)
        pfm__loix = tuple(ejinc__sxyv for ejinc__sxyv in pfm__loix if df.
            data[df.columns.index(ejinc__sxyv)] not in prvab__twpsp)
    data_args = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(ejinc__sxyv)})'
         for ejinc__sxyv in pfm__loix)
    header = 'def impl(df, include=None, exclude=None):\n'
    return _gen_init_df(header, pfm__loix, data_args)


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
    fqowr__oyzk = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if not isinstance(df.index, DatetimeIndexType):
        raise BodoError(
            'DataFrame.first(): only supports a DatetimeIndex index')
    if types.unliteral(offset) not in fqowr__oyzk:
        raise BodoError(
            "DataFrame.first(): 'offset' must be an string or DateOffset")
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.first()')
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
    fqowr__oyzk = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if not isinstance(df.index, DatetimeIndexType):
        raise BodoError('DataFrame.last(): only supports a DatetimeIndex index'
            )
    if types.unliteral(offset) not in fqowr__oyzk:
        raise BodoError(
            "DataFrame.last(): 'offset' must be an string or DateOffset")
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.last()')
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
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.isin()')
    aqh__aifei = 'def impl(df, values):\n'
    fca__vjvo = {}
    jvmlb__kko = False
    if isinstance(values, DataFrameType):
        jvmlb__kko = True
        for i, ejinc__sxyv in enumerate(df.columns):
            if ejinc__sxyv in values.columns:
                uju__tzesp = 'val{}'.format(i)
                aqh__aifei += (
                    """  {} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(values, {})
"""
                    .format(uju__tzesp, values.columns.index(ejinc__sxyv)))
                fca__vjvo[ejinc__sxyv] = uju__tzesp
    elif is_iterable_type(values) and not isinstance(values, SeriesType):
        fca__vjvo = {ejinc__sxyv: 'values' for ejinc__sxyv in df.columns}
    else:
        raise_bodo_error(f'pd.isin(): not supported for type {values}')
    data = []
    for i in range(len(df.columns)):
        uju__tzesp = 'data{}'.format(i)
        aqh__aifei += (
            '  {} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})\n'
            .format(uju__tzesp, i))
        data.append(uju__tzesp)
    nyfki__kdgmr = ['out{}'.format(i) for i in range(len(df.columns))]
    fce__xuhej = """
  numba.parfors.parfor.init_prange()
  n = len({0})
  m = len({1})
  {2} = np.empty(n, np.bool_)
  for i in numba.parfors.parfor.internal_prange(n):
    {2}[i] = {0}[i] == {1}[i] if i < m else False
"""
    yuart__jgezd = """
  numba.parfors.parfor.init_prange()
  n = len({0})
  {2} = np.empty(n, np.bool_)
  for i in numba.parfors.parfor.internal_prange(n):
    {2}[i] = {0}[i] in {1}
"""
    xyto__iyce = '  {} = np.zeros(len(df), np.bool_)\n'
    for i, (cname, mjsr__swfj) in enumerate(zip(df.columns, data)):
        if cname in fca__vjvo:
            dgruw__tfej = fca__vjvo[cname]
            if jvmlb__kko:
                aqh__aifei += fce__xuhej.format(mjsr__swfj, dgruw__tfej,
                    nyfki__kdgmr[i])
            else:
                aqh__aifei += yuart__jgezd.format(mjsr__swfj, dgruw__tfej,
                    nyfki__kdgmr[i])
        else:
            aqh__aifei += xyto__iyce.format(nyfki__kdgmr[i])
    return _gen_init_df(aqh__aifei, df.columns, ','.join(nyfki__kdgmr))


@overload_method(DataFrameType, 'abs', inline='always', no_unliteral=True)
def overload_dataframe_abs(df):
    check_runtime_cols_unsupported(df, 'DataFrame.abs()')
    for arr_typ in df.data:
        if not (isinstance(arr_typ.dtype, types.Number) or arr_typ.dtype ==
            bodo.timedelta64ns):
            raise_bodo_error(
                f'DataFrame.abs(): Only supported for numeric and Timedelta. Encountered array with dtype {arr_typ.dtype}'
                )
    gac__vkh = len(df.columns)
    data_args = ', '.join(
        'np.abs(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}))'
        .format(i) for i in range(gac__vkh))
    header = 'def impl(df):\n'
    return _gen_init_df(header, df.columns, data_args)


def overload_dataframe_corr(df, method='pearson', min_periods=1):
    qyeu__qcpr = [ejinc__sxyv for ejinc__sxyv, uyel__uly in zip(df.columns,
        df.data) if bodo.utils.typing._is_pandas_numeric_dtype(uyel__uly.dtype)
        ]
    assert len(qyeu__qcpr) != 0
    fxcz__xbdl = ''
    if not any(uyel__uly == types.float64 for uyel__uly in df.data):
        fxcz__xbdl = '.astype(np.float64)'
    qbgmt__zqafz = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(df.columns.index(ejinc__sxyv), '.astype(np.float64)' if 
        isinstance(df.data[df.columns.index(ejinc__sxyv)], IntegerArrayType
        ) or df.data[df.columns.index(ejinc__sxyv)] == boolean_array else
        '') for ejinc__sxyv in qyeu__qcpr)
    izkgx__qfmf = 'np.stack(({},), 1){}'.format(qbgmt__zqafz, fxcz__xbdl)
    data_args = ', '.join('res[:,{}]'.format(i) for i in range(len(qyeu__qcpr))
        )
    index = f'{generate_col_to_index_func_text(qyeu__qcpr)}\n'
    header = "def impl(df, method='pearson', min_periods=1):\n"
    header += '  mat = {}\n'.format(izkgx__qfmf)
    header += '  res = bodo.libs.array_kernels.nancorr(mat, 0, min_periods)\n'
    return _gen_init_df(header, qyeu__qcpr, data_args, index)


@lower_builtin('df.corr', DataFrameType, types.VarArg(types.Any))
def dataframe_corr_lower(context, builder, sig, args):
    impl = overload_dataframe_corr(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


@overload_method(DataFrameType, 'cov', inline='always', no_unliteral=True)
def overload_dataframe_cov(df, min_periods=None, ddof=1):
    check_runtime_cols_unsupported(df, 'DataFrame.cov()')
    anq__ivbcd = dict(ddof=ddof)
    tsx__frrxz = dict(ddof=1)
    check_unsupported_args('DataFrame.cov', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    cmoo__yuxin = '1' if is_overload_none(min_periods) else 'min_periods'
    qyeu__qcpr = [ejinc__sxyv for ejinc__sxyv, uyel__uly in zip(df.columns,
        df.data) if bodo.utils.typing._is_pandas_numeric_dtype(uyel__uly.dtype)
        ]
    if len(qyeu__qcpr) == 0:
        raise_bodo_error('DataFrame.cov(): requires non-empty dataframe')
    fxcz__xbdl = ''
    if not any(uyel__uly == types.float64 for uyel__uly in df.data):
        fxcz__xbdl = '.astype(np.float64)'
    qbgmt__zqafz = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(df.columns.index(ejinc__sxyv), '.astype(np.float64)' if 
        isinstance(df.data[df.columns.index(ejinc__sxyv)], IntegerArrayType
        ) or df.data[df.columns.index(ejinc__sxyv)] == boolean_array else
        '') for ejinc__sxyv in qyeu__qcpr)
    izkgx__qfmf = 'np.stack(({},), 1){}'.format(qbgmt__zqafz, fxcz__xbdl)
    data_args = ', '.join('res[:,{}]'.format(i) for i in range(len(qyeu__qcpr))
        )
    index = f'pd.Index({qyeu__qcpr})\n'
    header = 'def impl(df, min_periods=None, ddof=1):\n'
    header += '  mat = {}\n'.format(izkgx__qfmf)
    header += '  res = bodo.libs.array_kernels.nancorr(mat, 1, {})\n'.format(
        cmoo__yuxin)
    return _gen_init_df(header, qyeu__qcpr, data_args, index)


@overload_method(DataFrameType, 'count', inline='always', no_unliteral=True)
def overload_dataframe_count(df, axis=0, level=None, numeric_only=False):
    check_runtime_cols_unsupported(df, 'DataFrame.count()')
    anq__ivbcd = dict(axis=axis, level=level, numeric_only=numeric_only)
    tsx__frrxz = dict(axis=0, level=None, numeric_only=False)
    check_unsupported_args('DataFrame.count', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'bodo.libs.array_ops.array_op_count(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}))'
         for i in range(len(df.columns)))
    aqh__aifei = 'def impl(df, axis=0, level=None, numeric_only=False):\n'
    aqh__aifei += '  data = np.array([{}])\n'.format(data_args)
    gzm__knc = bodo.hiframes.dataframe_impl.generate_col_to_index_func_text(df
        .columns)
    aqh__aifei += (
        f'  return bodo.hiframes.pd_series_ext.init_series(data, {gzm__knc})\n'
        )
    iyph__amgxq = {}
    exec(aqh__aifei, {'bodo': bodo, 'np': np}, iyph__amgxq)
    impl = iyph__amgxq['impl']
    return impl


@overload_method(DataFrameType, 'nunique', inline='always', no_unliteral=True)
def overload_dataframe_nunique(df, axis=0, dropna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.unique()')
    anq__ivbcd = dict(axis=axis)
    tsx__frrxz = dict(axis=0)
    if not is_overload_bool(dropna):
        raise BodoError('DataFrame.nunique: dropna must be a boolean value')
    check_unsupported_args('DataFrame.nunique', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'bodo.libs.array_kernels.nunique(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), dropna)'
         for i in range(len(df.columns)))
    aqh__aifei = 'def impl(df, axis=0, dropna=True):\n'
    aqh__aifei += '  data = np.asarray(({},))\n'.format(data_args)
    gzm__knc = bodo.hiframes.dataframe_impl.generate_col_to_index_func_text(df
        .columns)
    aqh__aifei += (
        f'  return bodo.hiframes.pd_series_ext.init_series(data, {gzm__knc})\n'
        )
    iyph__amgxq = {}
    exec(aqh__aifei, {'bodo': bodo, 'np': np}, iyph__amgxq)
    impl = iyph__amgxq['impl']
    return impl


@overload_method(DataFrameType, 'prod', inline='always', no_unliteral=True)
@overload_method(DataFrameType, 'product', inline='always', no_unliteral=True)
def overload_dataframe_prod(df, axis=None, skipna=None, level=None,
    numeric_only=None, min_count=0):
    check_runtime_cols_unsupported(df, 'DataFrame.prod()')
    anq__ivbcd = dict(skipna=skipna, level=level, numeric_only=numeric_only,
        min_count=min_count)
    tsx__frrxz = dict(skipna=None, level=None, numeric_only=None, min_count=0)
    check_unsupported_args('DataFrame.prod', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.product()')
    return _gen_reduce_impl(df, 'prod', axis=axis)


@overload_method(DataFrameType, 'sum', inline='always', no_unliteral=True)
def overload_dataframe_sum(df, axis=None, skipna=None, level=None,
    numeric_only=None, min_count=0):
    check_runtime_cols_unsupported(df, 'DataFrame.sum()')
    anq__ivbcd = dict(skipna=skipna, level=level, numeric_only=numeric_only,
        min_count=min_count)
    tsx__frrxz = dict(skipna=None, level=None, numeric_only=None, min_count=0)
    check_unsupported_args('DataFrame.sum', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.sum()')
    return _gen_reduce_impl(df, 'sum', axis=axis)


@overload_method(DataFrameType, 'max', inline='always', no_unliteral=True)
def overload_dataframe_max(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.max()')
    anq__ivbcd = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    tsx__frrxz = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.max', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.max()')
    return _gen_reduce_impl(df, 'max', axis=axis)


@overload_method(DataFrameType, 'min', inline='always', no_unliteral=True)
def overload_dataframe_min(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.min()')
    anq__ivbcd = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    tsx__frrxz = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.min', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.min()')
    return _gen_reduce_impl(df, 'min', axis=axis)


@overload_method(DataFrameType, 'mean', inline='always', no_unliteral=True)
def overload_dataframe_mean(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.mean()')
    anq__ivbcd = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    tsx__frrxz = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.mean', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.mean()')
    return _gen_reduce_impl(df, 'mean', axis=axis)


@overload_method(DataFrameType, 'var', inline='always', no_unliteral=True)
def overload_dataframe_var(df, axis=None, skipna=None, level=None, ddof=1,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.var()')
    anq__ivbcd = dict(skipna=skipna, level=level, ddof=ddof, numeric_only=
        numeric_only)
    tsx__frrxz = dict(skipna=None, level=None, ddof=1, numeric_only=None)
    check_unsupported_args('DataFrame.var', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.var()')
    return _gen_reduce_impl(df, 'var', axis=axis)


@overload_method(DataFrameType, 'std', inline='always', no_unliteral=True)
def overload_dataframe_std(df, axis=None, skipna=None, level=None, ddof=1,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.std()')
    anq__ivbcd = dict(skipna=skipna, level=level, ddof=ddof, numeric_only=
        numeric_only)
    tsx__frrxz = dict(skipna=None, level=None, ddof=1, numeric_only=None)
    check_unsupported_args('DataFrame.std', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.std()')
    return _gen_reduce_impl(df, 'std', axis=axis)


@overload_method(DataFrameType, 'median', inline='always', no_unliteral=True)
def overload_dataframe_median(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.median()')
    anq__ivbcd = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    tsx__frrxz = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.median', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.median()')
    return _gen_reduce_impl(df, 'median', axis=axis)


@overload_method(DataFrameType, 'quantile', inline='always', no_unliteral=True)
def overload_dataframe_quantile(df, q=0.5, axis=0, numeric_only=True,
    interpolation='linear'):
    check_runtime_cols_unsupported(df, 'DataFrame.quantile()')
    anq__ivbcd = dict(numeric_only=numeric_only, interpolation=interpolation)
    tsx__frrxz = dict(numeric_only=True, interpolation='linear')
    check_unsupported_args('DataFrame.quantile', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.quantile()')
    return _gen_reduce_impl(df, 'quantile', 'q', axis=axis)


@overload_method(DataFrameType, 'idxmax', inline='always', no_unliteral=True)
def overload_dataframe_idxmax(df, axis=0, skipna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.idxmax()')
    anq__ivbcd = dict(axis=axis, skipna=skipna)
    tsx__frrxz = dict(axis=0, skipna=True)
    check_unsupported_args('DataFrame.idxmax', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.idxmax()')
    for slhis__yonij in df.data:
        if not (bodo.utils.utils.is_np_array_typ(slhis__yonij) and (
            slhis__yonij.dtype in [bodo.datetime64ns, bodo.timedelta64ns] or
            isinstance(slhis__yonij.dtype, (types.Number, types.Boolean))) or
            isinstance(slhis__yonij, (bodo.IntegerArrayType, bodo.
            CategoricalArrayType)) or slhis__yonij in [bodo.boolean_array,
            bodo.datetime_date_array_type]):
            raise BodoError(
                f'DataFrame.idxmax() only supported for numeric column types. Column type: {slhis__yonij} not supported.'
                )
        if isinstance(slhis__yonij, bodo.CategoricalArrayType
            ) and not slhis__yonij.dtype.ordered:
            raise BodoError(
                'DataFrame.idxmax(): categorical columns must be ordered')
    return _gen_reduce_impl(df, 'idxmax', axis=axis)


@overload_method(DataFrameType, 'idxmin', inline='always', no_unliteral=True)
def overload_dataframe_idxmin(df, axis=0, skipna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.idxmin()')
    anq__ivbcd = dict(axis=axis, skipna=skipna)
    tsx__frrxz = dict(axis=0, skipna=True)
    check_unsupported_args('DataFrame.idxmin', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.idxmin()')
    for slhis__yonij in df.data:
        if not (bodo.utils.utils.is_np_array_typ(slhis__yonij) and (
            slhis__yonij.dtype in [bodo.datetime64ns, bodo.timedelta64ns] or
            isinstance(slhis__yonij.dtype, (types.Number, types.Boolean))) or
            isinstance(slhis__yonij, (bodo.IntegerArrayType, bodo.
            CategoricalArrayType)) or slhis__yonij in [bodo.boolean_array,
            bodo.datetime_date_array_type]):
            raise BodoError(
                f'DataFrame.idxmin() only supported for numeric column types. Column type: {slhis__yonij} not supported.'
                )
        if isinstance(slhis__yonij, bodo.CategoricalArrayType
            ) and not slhis__yonij.dtype.ordered:
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
        qyeu__qcpr = tuple(ejinc__sxyv for ejinc__sxyv, uyel__uly in zip(df
            .columns, df.data) if bodo.utils.typing.
            _is_pandas_numeric_dtype(uyel__uly.dtype))
        out_colnames = qyeu__qcpr
    assert len(out_colnames) != 0
    try:
        if func_name in ('idxmax', 'idxmin') and axis == 0:
            comm_dtype = None
        else:
            zcudg__qht = [numba.np.numpy_support.as_dtype(df.data[df.
                columns.index(ejinc__sxyv)].dtype) for ejinc__sxyv in
                out_colnames]
            comm_dtype = numba.np.numpy_support.from_dtype(np.
                find_common_type(zcudg__qht, []))
    except NotImplementedError as bld__ufizx:
        raise BodoError(
            f'Dataframe.{func_name}() with column types: {df.data} could not be merged to a common type.'
            )
    yykb__scm = ''
    if func_name in ('sum', 'prod'):
        yykb__scm = ', min_count=0'
    ddof = ''
    if func_name in ('var', 'std'):
        ddof = 'ddof=1, '
    aqh__aifei = (
        'def impl(df, axis=None, skipna=None, level=None,{} numeric_only=None{}):\n'
        .format(ddof, yykb__scm))
    if func_name == 'quantile':
        aqh__aifei = (
            "def impl(df, q=0.5, axis=0, numeric_only=True, interpolation='linear'):\n"
            )
    if func_name in ('idxmax', 'idxmin'):
        aqh__aifei = 'def impl(df, axis=0, skipna=True):\n'
    if axis == 0:
        aqh__aifei += _gen_reduce_impl_axis0(df, func_name, out_colnames,
            comm_dtype, args)
    else:
        aqh__aifei += _gen_reduce_impl_axis1(func_name, out_colnames,
            comm_dtype, df)
    iyph__amgxq = {}
    exec(aqh__aifei, {'bodo': bodo, 'np': np, 'pd': pd, 'numba': numba},
        iyph__amgxq)
    impl = iyph__amgxq['impl']
    return impl


def _gen_reduce_impl_axis0(df, func_name, out_colnames, comm_dtype, args):
    ptxxz__mgbj = ''
    if func_name in ('min', 'max'):
        ptxxz__mgbj = ', dtype=np.{}'.format(comm_dtype)
    if comm_dtype == types.float32 and func_name in ('sum', 'prod', 'mean',
        'var', 'std', 'median'):
        ptxxz__mgbj = ', dtype=np.float32'
    ckduf__ihc = f'bodo.libs.array_ops.array_op_{func_name}'
    yruaj__tva = ''
    if func_name in ['sum', 'prod']:
        yruaj__tva = 'True, min_count'
    elif func_name in ['idxmax', 'idxmin']:
        yruaj__tva = 'index'
    elif func_name == 'quantile':
        yruaj__tva = 'q'
    elif func_name in ['std', 'var']:
        yruaj__tva = 'True, ddof'
    elif func_name == 'median':
        yruaj__tva = 'True'
    data_args = ', '.join(
        f'{ckduf__ihc}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(ejinc__sxyv)}), {yruaj__tva})'
         for ejinc__sxyv in out_colnames)
    aqh__aifei = ''
    if func_name in ('idxmax', 'idxmin'):
        aqh__aifei += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
            )
        aqh__aifei += (
            '  data = bodo.utils.conversion.coerce_to_array(({},))\n'.
            format(data_args))
    else:
        aqh__aifei += '  data = np.asarray(({},){})\n'.format(data_args,
            ptxxz__mgbj)
    aqh__aifei += f"""  return bodo.hiframes.pd_series_ext.init_series(data, pd.Index({out_colnames}))
"""
    return aqh__aifei


def _gen_reduce_impl_axis1(func_name, out_colnames, comm_dtype, df_type):
    vfcjo__lprqm = [df_type.columns.index(ejinc__sxyv) for ejinc__sxyv in
        out_colnames]
    index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
    data_args = '\n    '.join(
        'arr_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})'
        .format(i) for i in vfcjo__lprqm)
    qlr__mtw = '\n        '.join(f'row[{i}] = arr_{vfcjo__lprqm[i]}[i]' for
        i in range(len(out_colnames)))
    assert len(data_args) > 0, f'empty dataframe in DataFrame.{func_name}()'
    vqgmr__llgi = f'len(arr_{vfcjo__lprqm[0]})'
    rfaaf__rotvi = {'max': 'np.nanmax', 'min': 'np.nanmin', 'sum':
        'np.nansum', 'prod': 'np.nanprod', 'mean': 'np.nanmean', 'median':
        'np.nanmedian', 'var': 'bodo.utils.utils.nanvar_ddof1', 'std':
        'bodo.utils.utils.nanstd_ddof1'}
    if func_name in rfaaf__rotvi:
        ums__btt = rfaaf__rotvi[func_name]
        qmztw__tkgmu = 'float64' if func_name in ['mean', 'median', 'std',
            'var'] else comm_dtype
        aqh__aifei = f"""
    {data_args}
    numba.parfors.parfor.init_prange()
    n = {vqgmr__llgi}
    row = np.empty({len(out_colnames)}, np.{comm_dtype})
    A = np.empty(n, np.{qmztw__tkgmu})
    for i in numba.parfors.parfor.internal_prange(n):
        {qlr__mtw}
        A[i] = {ums__btt}(row)
    return bodo.hiframes.pd_series_ext.init_series(A, {index})
"""
        return aqh__aifei
    else:
        raise BodoError(f'DataFrame.{func_name}(): Not supported for axis=1')


@overload_method(DataFrameType, 'pct_change', inline='always', no_unliteral
    =True)
def overload_dataframe_pct_change(df, periods=1, fill_method='pad', limit=
    None, freq=None):
    check_runtime_cols_unsupported(df, 'DataFrame.pct_change()')
    anq__ivbcd = dict(fill_method=fill_method, limit=limit, freq=freq)
    tsx__frrxz = dict(fill_method='pad', limit=None, freq=None)
    check_unsupported_args('DataFrame.pct_change', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.pct_change()')
    data_args = ', '.join(
        f'bodo.hiframes.rolling.pct_change(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), periods, False)'
         for i in range(len(df.columns)))
    header = (
        "def impl(df, periods=1, fill_method='pad', limit=None, freq=None):\n")
    return _gen_init_df(header, df.columns, data_args)


@overload_method(DataFrameType, 'cumprod', inline='always', no_unliteral=True)
def overload_dataframe_cumprod(df, axis=None, skipna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.cumprod()')
    anq__ivbcd = dict(axis=axis, skipna=skipna)
    tsx__frrxz = dict(axis=None, skipna=True)
    check_unsupported_args('DataFrame.cumprod', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.cumprod()')
    data_args = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).cumprod()'
         for i in range(len(df.columns)))
    header = 'def impl(df, axis=None, skipna=True):\n'
    return _gen_init_df(header, df.columns, data_args)


@overload_method(DataFrameType, 'cumsum', inline='always', no_unliteral=True)
def overload_dataframe_cumsum(df, axis=None, skipna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.cumsum()')
    anq__ivbcd = dict(skipna=skipna)
    tsx__frrxz = dict(skipna=True)
    check_unsupported_args('DataFrame.cumsum', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.cumsum()')
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
    anq__ivbcd = dict(percentiles=percentiles, include=include, exclude=
        exclude, datetime_is_numeric=datetime_is_numeric)
    tsx__frrxz = dict(percentiles=None, include=None, exclude=None,
        datetime_is_numeric=True)
    check_unsupported_args('DataFrame.describe', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.describe()')
    qyeu__qcpr = [ejinc__sxyv for ejinc__sxyv, uyel__uly in zip(df.columns,
        df.data) if _is_describe_type(uyel__uly)]
    if len(qyeu__qcpr) == 0:
        raise BodoError('df.describe() only supports numeric columns')
    hku__deo = sum(df.data[df.columns.index(ejinc__sxyv)].dtype == bodo.
        datetime64ns for ejinc__sxyv in qyeu__qcpr)

    def _get_describe(col_ind):
        yvg__gkbp = df.data[col_ind].dtype == bodo.datetime64ns
        if hku__deo and hku__deo != len(qyeu__qcpr):
            if yvg__gkbp:
                return f'des_{col_ind} + (np.nan,)'
            return (
                f'des_{col_ind}[:2] + des_{col_ind}[3:] + (des_{col_ind}[2],)')
        return f'des_{col_ind}'
    header = """def impl(df, percentiles=None, include=None, exclude=None, datetime_is_numeric=True):
"""
    for ejinc__sxyv in qyeu__qcpr:
        col_ind = df.columns.index(ejinc__sxyv)
        header += f"""  des_{col_ind} = bodo.libs.array_ops.array_op_describe(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {col_ind}))
"""
    data_args = ', '.join(_get_describe(df.columns.index(ejinc__sxyv)) for
        ejinc__sxyv in qyeu__qcpr)
    jvrr__kfwbu = "['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']"
    if hku__deo == len(qyeu__qcpr):
        jvrr__kfwbu = "['count', 'mean', 'min', '25%', '50%', '75%', 'max']"
    elif hku__deo:
        jvrr__kfwbu = (
            "['count', 'mean', 'min', '25%', '50%', '75%', 'max', 'std']")
    index = f'bodo.utils.conversion.convert_to_index({jvrr__kfwbu})'
    return _gen_init_df(header, qyeu__qcpr, data_args, index)


@overload_method(DataFrameType, 'take', inline='always', no_unliteral=True)
def overload_dataframe_take(df, indices, axis=0, convert=None, is_copy=True):
    check_runtime_cols_unsupported(df, 'DataFrame.take()')
    anq__ivbcd = dict(axis=axis, convert=convert, is_copy=is_copy)
    tsx__frrxz = dict(axis=0, convert=None, is_copy=True)
    check_unsupported_args('DataFrame.take', anq__ivbcd, tsx__frrxz,
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
    anq__ivbcd = dict(freq=freq, axis=axis, fill_value=fill_value)
    tsx__frrxz = dict(freq=None, axis=0, fill_value=None)
    check_unsupported_args('DataFrame.shift', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.shift()')
    for oge__mnvtu in df.data:
        if not is_supported_shift_array_type(oge__mnvtu):
            raise BodoError(
                f'Dataframe.shift() column input type {oge__mnvtu.dtype} not supported yet.'
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
    anq__ivbcd = dict(axis=axis)
    tsx__frrxz = dict(axis=0)
    check_unsupported_args('DataFrame.diff', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.diff()')
    for oge__mnvtu in df.data:
        if not (isinstance(oge__mnvtu, types.Array) and (isinstance(
            oge__mnvtu.dtype, types.Number) or oge__mnvtu.dtype == bodo.
            datetime64ns)):
            raise BodoError(
                f'DataFrame.diff() column input type {oge__mnvtu.dtype} not supported.'
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
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.explode()')
    vtuok__wgma = (
        "DataFrame.explode(): 'column' must a constant label or list of labels"
        )
    if not is_literal_type(column):
        raise_bodo_error(vtuok__wgma)
    if is_overload_constant_list(column) or is_overload_constant_tuple(column):
        phh__wqg = get_overload_const_list(column)
    else:
        phh__wqg = [get_literal_value(column)]
    hbru__aap = {ejinc__sxyv: i for i, ejinc__sxyv in enumerate(df.columns)}
    pvdh__xogd = [hbru__aap[ejinc__sxyv] for ejinc__sxyv in phh__wqg]
    for i in pvdh__xogd:
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
        f'  counts = bodo.libs.array_kernels.get_arr_lens(data{pvdh__xogd[0]})\n'
        )
    for i in range(n):
        if i in pvdh__xogd:
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
    vbjk__zasha = {'inplace': inplace, 'append': append, 'verify_integrity':
        verify_integrity}
    pwrz__jhve = {'inplace': False, 'append': False, 'verify_integrity': False}
    check_unsupported_args('DataFrame.set_index', vbjk__zasha, pwrz__jhve,
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
    columns = tuple(ejinc__sxyv for ejinc__sxyv in df.columns if 
        ejinc__sxyv != col_name)
    index = (
        'bodo.utils.conversion.index_from_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}), {})'
        .format(col_ind, f"'{col_name}'" if isinstance(col_name, str) else
        col_name))
    return _gen_init_df(header, columns, data_args, index)


@overload_method(DataFrameType, 'query', no_unliteral=True)
def overload_dataframe_query(df, expr, inplace=False):
    check_runtime_cols_unsupported(df, 'DataFrame.query()')
    vbjk__zasha = {'inplace': inplace}
    pwrz__jhve = {'inplace': False}
    check_unsupported_args('query', vbjk__zasha, pwrz__jhve, package_name=
        'pandas', module_name='DataFrame')
    if not isinstance(expr, (types.StringLiteral, types.UnicodeType)):
        raise BodoError('query(): expr argument should be a string')

    def impl(df, expr, inplace=False):
        eicde__trjra = bodo.hiframes.pd_dataframe_ext.query_dummy(df, expr)
        return df[eicde__trjra]
    return impl


@overload_method(DataFrameType, 'duplicated', inline='always', no_unliteral
    =True)
def overload_dataframe_duplicated(df, subset=None, keep='first'):
    check_runtime_cols_unsupported(df, 'DataFrame.duplicated()')
    vbjk__zasha = {'subset': subset, 'keep': keep}
    pwrz__jhve = {'subset': None, 'keep': 'first'}
    check_unsupported_args('DataFrame.duplicated', vbjk__zasha, pwrz__jhve,
        package_name='pandas', module_name='DataFrame')
    gac__vkh = len(df.columns)
    aqh__aifei = "def impl(df, subset=None, keep='first'):\n"
    for i in range(gac__vkh):
        aqh__aifei += (
            '  data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})\n'
            .format(i))
    nipb__zyapr = ', '.join(f'data_{i}' for i in range(gac__vkh))
    nipb__zyapr += ',' if gac__vkh == 1 else ''
    aqh__aifei += (
        f'  duplicated = bodo.libs.array_kernels.duplicated(({nipb__zyapr}))\n'
        )
    aqh__aifei += (
        '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n')
    aqh__aifei += (
        '  return bodo.hiframes.pd_series_ext.init_series(duplicated, index)\n'
        )
    iyph__amgxq = {}
    exec(aqh__aifei, {'bodo': bodo}, iyph__amgxq)
    impl = iyph__amgxq['impl']
    return impl


@overload_method(DataFrameType, 'drop_duplicates', inline='always',
    no_unliteral=True)
def overload_dataframe_drop_duplicates(df, subset=None, keep='first',
    inplace=False, ignore_index=False):
    check_runtime_cols_unsupported(df, 'DataFrame.drop_duplicates()')
    vbjk__zasha = {'keep': keep, 'inplace': inplace, 'ignore_index':
        ignore_index}
    pwrz__jhve = {'keep': 'first', 'inplace': False, 'ignore_index': False}
    dkui__apqv = []
    if is_overload_constant_list(subset):
        dkui__apqv = get_overload_const_list(subset)
    elif is_overload_constant_str(subset):
        dkui__apqv = [get_overload_const_str(subset)]
    elif is_overload_constant_int(subset):
        dkui__apqv = [get_overload_const_int(subset)]
    elif not is_overload_none(subset):
        raise_bodo_error(
            'DataFrame.drop_duplicates(): subset must be a constant column name, constant list of column names or None'
            )
    pphm__hysus = []
    for col_name in dkui__apqv:
        if col_name not in df.columns:
            raise BodoError(
                'DataFrame.drop_duplicates(): All subset columns must be found in the DataFrame.'
                 +
                f'Column {col_name} not found in DataFrame columns {df.columns}'
                )
        pphm__hysus.append(df.columns.index(col_name))
    check_unsupported_args('DataFrame.drop_duplicates', vbjk__zasha,
        pwrz__jhve, package_name='pandas', module_name='DataFrame')
    ufqda__spk = []
    if pphm__hysus:
        for pnqcr__jtqm in pphm__hysus:
            if isinstance(df.data[pnqcr__jtqm], bodo.MapArrayType):
                ufqda__spk.append(df.columns[pnqcr__jtqm])
    else:
        for i, col_name in enumerate(df.columns):
            if isinstance(df.data[i], bodo.MapArrayType):
                ufqda__spk.append(col_name)
    if ufqda__spk:
        raise BodoError(
            f'DataFrame.drop_duplicates(): Columns {ufqda__spk} ' +
            f'have dictionary types which cannot be used to drop duplicates. '
             +
            "Please consider using the 'subset' argument to skip these columns."
            )
    gac__vkh = len(df.columns)
    qurp__oekle = ['data_{}'.format(i) for i in pphm__hysus]
    ncmb__qhx = ['data_{}'.format(i) for i in range(gac__vkh) if i not in
        pphm__hysus]
    if qurp__oekle:
        wbkm__xisaa = len(qurp__oekle)
    else:
        wbkm__xisaa = gac__vkh
    yoade__jopcz = ', '.join(qurp__oekle + ncmb__qhx)
    data_args = ', '.join('data_{}'.format(i) for i in range(gac__vkh))
    aqh__aifei = (
        "def impl(df, subset=None, keep='first', inplace=False, ignore_index=False):\n"
        )
    for i in range(gac__vkh):
        aqh__aifei += (
            '  data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})\n'
            .format(i))
    index = (
        'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
        )
    aqh__aifei += (
        """  ({0},), index_arr = bodo.libs.array_kernels.drop_duplicates(({0},), {1}, {2})
"""
        .format(yoade__jopcz, index, wbkm__xisaa))
    aqh__aifei += (
        '  index = bodo.utils.conversion.index_from_array(index_arr)\n')
    return _gen_init_df(aqh__aifei, df.columns, data_args, 'index')


def create_dataframe_mask_where_overload(func_name):

    def overload_dataframe_mask_where(df, cond, other=np.nan, inplace=False,
        axis=None, level=None, errors='raise', try_cast=False):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
            f'DataFrame.{func_name}()')
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
                qaz__pypci = {ejinc__sxyv: i for i, ejinc__sxyv in
                    enumerate(cond.columns)}

                def cond_str(i, gen_all_false):
                    if df.columns[i] in qaz__pypci:
                        return (
                            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(cond, {qaz__pypci[df.columns[i]]})'
                            )
                    else:
                        gen_all_false[0] = True
                        return 'all_false'
            elif isinstance(cond, types.Array):
                cond_str = lambda i, _: f'cond[:,{i}]'
        if not hasattr(other, 'ndim') or other.ndim == 1:
            gpzd__wre = lambda i: 'other'
        elif other.ndim == 2:
            if isinstance(other, DataFrameType):
                other_map = {ejinc__sxyv: i for i, ejinc__sxyv in enumerate
                    (other.columns)}
                gpzd__wre = (lambda i: 
                    f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(other, {other_map[df.columns[i]]})'
                     if df.columns[i] in other_map else 'None')
            elif isinstance(other, types.Array):
                gpzd__wre = lambda i: f'other[:,{i}]'
        gac__vkh = len(df.columns)
        data_args = ', '.join(
            f'bodo.hiframes.series_impl.where_impl({cond_str(i, gen_all_false)}, bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), {gpzd__wre(i)})'
             for i in range(gac__vkh))
        if gen_all_false[0]:
            header += '  all_false = np.zeros(len(df), dtype=bool)\n'
        return _gen_init_df(header, df.columns, data_args)
    return overload_dataframe_mask_where


def _install_dataframe_mask_where_overload():
    for func_name in ('mask', 'where'):
        gas__xew = create_dataframe_mask_where_overload(func_name)
        overload_method(DataFrameType, func_name, no_unliteral=True)(gas__xew)


_install_dataframe_mask_where_overload()


def _validate_arguments_mask_where(func_name, df, cond, other, inplace,
    axis, level, errors, try_cast):
    anq__ivbcd = dict(inplace=inplace, level=level, errors=errors, try_cast
        =try_cast)
    tsx__frrxz = dict(inplace=False, level=None, errors='raise', try_cast=False
        )
    check_unsupported_args(f'{func_name}', anq__ivbcd, tsx__frrxz,
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
    gac__vkh = len(df.columns)
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
        other_map = {ejinc__sxyv: i for i, ejinc__sxyv in enumerate(other.
            columns)}
        for i in range(gac__vkh):
            if df.columns[i] in other_map:
                bodo.hiframes.series_impl._validate_self_other_mask_where(
                    func_name, df.data[i], other.data[other_map[df.columns[i]]]
                    )
            else:
                bodo.hiframes.series_impl._validate_self_other_mask_where(
                    func_name, df.data[i], None, is_default=True)
    elif isinstance(other, SeriesType):
        for i in range(gac__vkh):
            bodo.hiframes.series_impl._validate_self_other_mask_where(func_name
                , df.data[i], other.data)
    else:
        for i in range(gac__vkh):
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
        lspz__gwug = 'out_df_type'
    else:
        lspz__gwug = gen_const_tup(columns)
    data_args = '({}{})'.format(data_args, ',' if data_args else '')
    aqh__aifei = f"""{header}  return bodo.hiframes.pd_dataframe_ext.init_dataframe({data_args}, {index}, {lspz__gwug})
"""
    iyph__amgxq = {}
    easj__ytu = {'bodo': bodo, 'np': np, 'pd': pd, 'numba': numba}
    easj__ytu.update(extra_globals)
    exec(aqh__aifei, easj__ytu, iyph__amgxq)
    impl = iyph__amgxq['impl']
    return impl


def _get_binop_columns(lhs, rhs, is_inplace=False):
    if lhs.columns != rhs.columns:
        pgm__xjp = pd.Index(lhs.columns)
        lctw__txs = pd.Index(rhs.columns)
        lbfr__gutfv, wbql__wdd, bncml__uuy = pgm__xjp.join(lctw__txs, how=
            'left' if is_inplace else 'outer', level=None, return_indexers=True
            )
        return tuple(lbfr__gutfv), wbql__wdd, bncml__uuy
    return lhs.columns, range(len(lhs.columns)), range(len(lhs.columns))


def create_binary_op_overload(op):

    def overload_dataframe_binary_op(lhs, rhs):
        dcmmb__ufb = numba.core.utils.OPERATORS_TO_BUILTINS[op]
        msz__mqo = operator.eq, operator.ne
        check_runtime_cols_unsupported(lhs, dcmmb__ufb)
        check_runtime_cols_unsupported(rhs, dcmmb__ufb)
        if isinstance(lhs, DataFrameType):
            if isinstance(rhs, DataFrameType):
                lbfr__gutfv, wbql__wdd, bncml__uuy = _get_binop_columns(lhs,
                    rhs)
                data_args = ', '.join(
                    f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(lhs, {zae__pfj}) {dcmmb__ufb}bodo.hiframes.pd_dataframe_ext.get_dataframe_data(rhs, {zyu__dlmd})'
                     if zae__pfj != -1 and zyu__dlmd != -1 else
                    f'bodo.libs.array_kernels.gen_na_array(len(lhs), float64_arr_type)'
                     for zae__pfj, zyu__dlmd in zip(wbql__wdd, bncml__uuy))
                header = 'def impl(lhs, rhs):\n'
                index = (
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(lhs)')
                return _gen_init_df(header, lbfr__gutfv, data_args, index,
                    extra_globals={'float64_arr_type': types.Array(types.
                    float64, 1, 'C')})
            rws__aikqf = []
            wpe__zqdb = []
            if op in msz__mqo:
                for i, wzaok__ceul in enumerate(lhs.data):
                    if is_common_scalar_dtype([wzaok__ceul.dtype, rhs]):
                        rws__aikqf.append(
                            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(lhs, {i}) {dcmmb__ufb} rhs'
                            )
                    else:
                        dyx__bsth = f'arr{i}'
                        wpe__zqdb.append(dyx__bsth)
                        rws__aikqf.append(dyx__bsth)
                data_args = ', '.join(rws__aikqf)
            else:
                data_args = ', '.join(
                    f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(lhs, {i}) {dcmmb__ufb} rhs'
                     for i in range(len(lhs.columns)))
            header = 'def impl(lhs, rhs):\n'
            if len(wpe__zqdb) > 0:
                header += '  numba.parfors.parfor.init_prange()\n'
                header += '  n = len(lhs)\n'
                header += ''.join(
                    f'  {dyx__bsth} = np.empty(n, dtype=np.bool_)\n' for
                    dyx__bsth in wpe__zqdb)
                header += (
                    '  for i in numba.parfors.parfor.internal_prange(n):\n')
                header += ''.join('    {0}[i] = {1}\n'.format(dyx__bsth, op ==
                    operator.ne) for dyx__bsth in wpe__zqdb)
            index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(lhs)'
            return _gen_init_df(header, lhs.columns, data_args, index)
        if isinstance(rhs, DataFrameType):
            rws__aikqf = []
            wpe__zqdb = []
            if op in msz__mqo:
                for i, wzaok__ceul in enumerate(rhs.data):
                    if is_common_scalar_dtype([lhs, wzaok__ceul.dtype]):
                        rws__aikqf.append(
                            f'lhs {dcmmb__ufb} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(rhs, {i})'
                            )
                    else:
                        dyx__bsth = f'arr{i}'
                        wpe__zqdb.append(dyx__bsth)
                        rws__aikqf.append(dyx__bsth)
                data_args = ', '.join(rws__aikqf)
            else:
                data_args = ', '.join(
                    'lhs {1} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(rhs, {0})'
                    .format(i, dcmmb__ufb) for i in range(len(rhs.columns)))
            header = 'def impl(lhs, rhs):\n'
            if len(wpe__zqdb) > 0:
                header += '  numba.parfors.parfor.init_prange()\n'
                header += '  n = len(rhs)\n'
                header += ''.join('  {0} = np.empty(n, dtype=np.bool_)\n'.
                    format(dyx__bsth) for dyx__bsth in wpe__zqdb)
                header += (
                    '  for i in numba.parfors.parfor.internal_prange(n):\n')
                header += ''.join('    {0}[i] = {1}\n'.format(dyx__bsth, op ==
                    operator.ne) for dyx__bsth in wpe__zqdb)
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
        gas__xew = create_binary_op_overload(op)
        overload(op)(gas__xew)


_install_binary_ops()


def create_inplace_binary_op_overload(op):

    def overload_dataframe_inplace_binary_op(left, right):
        dcmmb__ufb = numba.core.utils.OPERATORS_TO_BUILTINS[op]
        check_runtime_cols_unsupported(left, dcmmb__ufb)
        check_runtime_cols_unsupported(right, dcmmb__ufb)
        if isinstance(left, DataFrameType):
            if isinstance(right, DataFrameType):
                lbfr__gutfv, _, bncml__uuy = _get_binop_columns(left, right,
                    True)
                aqh__aifei = 'def impl(left, right):\n'
                for i, zyu__dlmd in enumerate(bncml__uuy):
                    if zyu__dlmd == -1:
                        aqh__aifei += f"""  df_arr{i} = bodo.libs.array_kernels.gen_na_array(len(left), float64_arr_type)
"""
                        continue
                    aqh__aifei += f"""  df_arr{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(left, {i})
"""
                    aqh__aifei += f"""  df_arr{i} {dcmmb__ufb} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(right, {zyu__dlmd})
"""
                data_args = ', '.join(f'df_arr{i}' for i in range(len(
                    lbfr__gutfv)))
                index = (
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(left)')
                return _gen_init_df(aqh__aifei, lbfr__gutfv, data_args,
                    index, extra_globals={'float64_arr_type': types.Array(
                    types.float64, 1, 'C')})
            aqh__aifei = 'def impl(left, right):\n'
            for i in range(len(left.columns)):
                aqh__aifei += (
                    """  df_arr{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(left, {0})
"""
                    .format(i))
                aqh__aifei += '  df_arr{0} {1} right\n'.format(i, dcmmb__ufb)
            data_args = ', '.join('df_arr{}'.format(i) for i in range(len(
                left.columns)))
            index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(left)'
            return _gen_init_df(aqh__aifei, left.columns, data_args, index)
    return overload_dataframe_inplace_binary_op


def _install_inplace_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_inplace_binary_ops:
        gas__xew = create_inplace_binary_op_overload(op)
        overload(op, no_unliteral=True)(gas__xew)


_install_inplace_binary_ops()


def create_unary_op_overload(op):

    def overload_dataframe_unary_op(df):
        if isinstance(df, DataFrameType):
            dcmmb__ufb = numba.core.utils.OPERATORS_TO_BUILTINS[op]
            check_runtime_cols_unsupported(df, dcmmb__ufb)
            data_args = ', '.join(
                '{1} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})'
                .format(i, dcmmb__ufb) for i in range(len(df.columns)))
            header = 'def impl(df):\n'
            return _gen_init_df(header, df.columns, data_args)
    return overload_dataframe_unary_op


def _install_unary_ops():
    for op in bodo.hiframes.pd_series_ext.series_unary_ops:
        gas__xew = create_unary_op_overload(op)
        overload(op, no_unliteral=True)(gas__xew)


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
            rav__axfor = np.empty(n, np.bool_)
            for i in numba.parfors.parfor.internal_prange(n):
                rav__axfor[i] = bodo.libs.array_kernels.isna(obj, i)
            return rav__axfor
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
            rav__axfor = np.empty(n, np.bool_)
            for i in range(n):
                rav__axfor[i] = pd.isna(obj[i])
            return rav__axfor
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
    if isinstance(obj, bodo.hiframes.pd_timestamp_ext.PandasTimestampType):
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
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.replace()')
    if is_overload_none(to_replace):
        raise BodoError('replace(): to_replace value of None is not supported')
    vbjk__zasha = {'inplace': inplace, 'limit': limit, 'regex': regex,
        'method': method}
    pwrz__jhve = {'inplace': False, 'limit': None, 'regex': False, 'method':
        'pad'}
    check_unsupported_args('replace', vbjk__zasha, pwrz__jhve, package_name
        ='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'df.iloc[:, {i}].replace(to_replace, value).values' for i in range
        (len(df.columns)))
    header = """def impl(df, to_replace=None, value=None, inplace=False, limit=None, regex=False, method='pad'):
"""
    return _gen_init_df(header, df.columns, data_args)


def _is_col_access(expr_node):
    shg__rttc = str(expr_node)
    return shg__rttc.startswith('left.') or shg__rttc.startswith('right.')


def _insert_NA_cond(expr_node, left_columns, left_data, right_columns,
    right_data):
    syse__hco = {'left': 0, 'right': 0, 'NOT_NA': 0}
    env = pd.core.computation.scope.ensure_scope(2, {}, {}, (syse__hco,))
    dgm__kdsar = pd.core.computation.parsing.clean_column_name

    def append_null_checks(expr_node, null_set):
        if not null_set:
            return expr_node
        ozmhk__qwu = ' & '.join([('NOT_NA.`' + x + '`') for x in null_set])
        higse__ycqe = {('NOT_NA', dgm__kdsar(wzaok__ceul)): wzaok__ceul for
            wzaok__ceul in null_set}
        kgee__asdgr, _, _ = _parse_query_expr(ozmhk__qwu, env, [], [], None,
            join_cleaned_cols=higse__ycqe)
        gajw__xos = (pd.core.computation.ops.BinOp.
            _disallow_scalar_only_bool_ops)
        pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops = (lambda
            self: None)
        try:
            tjvfr__gacrx = pd.core.computation.ops.BinOp('&', kgee__asdgr,
                expr_node)
        finally:
            (pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops
                ) = gajw__xos
        return tjvfr__gacrx

    def _insert_NA_cond_body(expr_node, null_set):
        if isinstance(expr_node, pd.core.computation.ops.BinOp):
            if expr_node.op == '|':
                zapo__seyi = set()
                swcbv__zxis = set()
                gyfv__lja = _insert_NA_cond_body(expr_node.lhs, zapo__seyi)
                dwxa__khgfr = _insert_NA_cond_body(expr_node.rhs, swcbv__zxis)
                rhdnz__tvxcv = zapo__seyi.intersection(swcbv__zxis)
                zapo__seyi.difference_update(rhdnz__tvxcv)
                swcbv__zxis.difference_update(rhdnz__tvxcv)
                null_set.update(rhdnz__tvxcv)
                expr_node.lhs = append_null_checks(gyfv__lja, zapo__seyi)
                expr_node.rhs = append_null_checks(dwxa__khgfr, swcbv__zxis)
                expr_node.operands = expr_node.lhs, expr_node.rhs
            else:
                expr_node.lhs = _insert_NA_cond_body(expr_node.lhs, null_set)
                expr_node.rhs = _insert_NA_cond_body(expr_node.rhs, null_set)
        elif _is_col_access(expr_node):
            mokqw__dysyo = expr_node.name
            koh__depu, col_name = mokqw__dysyo.split('.')
            if koh__depu == 'left':
                hpvos__otvye = left_columns
                data = left_data
            else:
                hpvos__otvye = right_columns
                data = right_data
            vacr__edvt = data[hpvos__otvye.index(col_name)]
            if bodo.utils.typing.is_nullable(vacr__edvt):
                null_set.add(expr_node.name)
        return expr_node
    null_set = set()
    klla__tga = _insert_NA_cond_body(expr_node, null_set)
    return append_null_checks(expr_node, null_set)


def _extract_equal_conds(expr_node):
    if not hasattr(expr_node, 'op'):
        return [], [], expr_node
    if expr_node.op == '==' and _is_col_access(expr_node.lhs
        ) and _is_col_access(expr_node.rhs):
        leq__vatav = str(expr_node.lhs)
        hymr__zrav = str(expr_node.rhs)
        if leq__vatav.startswith('left.') and hymr__zrav.startswith('left.'
            ) or leq__vatav.startswith('right.') and hymr__zrav.startswith(
            'right.'):
            return [], [], expr_node
        left_on = [leq__vatav.split('.')[1]]
        right_on = [hymr__zrav.split('.')[1]]
        if leq__vatav.startswith('right.'):
            return right_on, left_on, None
        return left_on, right_on, None
    if expr_node.op == '&':
        gzlpp__xvs, kidaa__dhbax, pkf__obhz = _extract_equal_conds(expr_node
            .lhs)
        epk__liakh, hdqe__xdvd, ifp__kfwbs = _extract_equal_conds(expr_node.rhs
            )
        left_on = gzlpp__xvs + epk__liakh
        right_on = kidaa__dhbax + hdqe__xdvd
        if pkf__obhz is None:
            return left_on, right_on, ifp__kfwbs
        if ifp__kfwbs is None:
            return left_on, right_on, pkf__obhz
        expr_node.lhs = pkf__obhz
        expr_node.rhs = ifp__kfwbs
        expr_node.operands = expr_node.lhs, expr_node.rhs
        return left_on, right_on, expr_node
    return [], [], expr_node


def _parse_merge_cond(on_str, left_columns, left_data, right_columns,
    right_data):
    syse__hco = {'left': 0, 'right': 0}
    env = pd.core.computation.scope.ensure_scope(2, {}, {}, (syse__hco,))
    jhu__qro = dict()
    dgm__kdsar = pd.core.computation.parsing.clean_column_name
    for name, dmjhh__yszt in (('left', left_columns), ('right', right_columns)
        ):
        for wzaok__ceul in dmjhh__yszt:
            iiwz__crl = dgm__kdsar(wzaok__ceul)
            suq__wusvp = name, iiwz__crl
            if suq__wusvp in jhu__qro:
                raise_bodo_error(
                    f"pd.merge(): {name} table contains two columns that are escaped to the same Python identifier '{wzaok__ceul}' and '{jhu__qro[iiwz__crl]}' Please rename one of these columns. To avoid this issue, please use names that are valid Python identifiers."
                    )
            jhu__qro[suq__wusvp] = wzaok__ceul
    knl__juyur, _, _ = _parse_query_expr(on_str, env, [], [], None,
        join_cleaned_cols=jhu__qro)
    left_on, right_on, aojj__jqj = _extract_equal_conds(knl__juyur.terms)
    return left_on, right_on, _insert_NA_cond(aojj__jqj, left_columns,
        left_data, right_columns, right_data)


@overload_method(DataFrameType, 'merge', inline='always', no_unliteral=True)
@overload(pd.merge, inline='always', no_unliteral=True)
def overload_dataframe_merge(left, right, how='inner', on=None, left_on=
    None, right_on=None, left_index=False, right_index=False, sort=False,
    suffixes=('_x', '_y'), copy=True, indicator=False, validate=None,
    _bodo_na_equal=True):
    check_runtime_cols_unsupported(left, 'DataFrame.merge()')
    check_runtime_cols_unsupported(right, 'DataFrame.merge()')
    anq__ivbcd = dict(sort=sort, copy=copy, validate=validate)
    tsx__frrxz = dict(sort=False, copy=True, validate=None)
    check_unsupported_args('DataFrame.merge', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    validate_merge_spec(left, right, how, on, left_on, right_on, left_index,
        right_index, sort, suffixes, copy, indicator, validate)
    how = get_overload_const_str(how)
    pqn__uoh = tuple(sorted(set(left.columns) & set(right.columns), key=lambda
        k: str(k)))
    pobij__mpqu = ''
    if not is_overload_none(on):
        left_on = right_on = on
        if is_overload_constant_str(on):
            on_str = get_overload_const_str(on)
            if on_str not in pqn__uoh and ('left.' in on_str or 'right.' in
                on_str):
                left_on, right_on, nhdny__paeqq = _parse_merge_cond(on_str,
                    left.columns, left.data, right.columns, right.data)
                if nhdny__paeqq is None:
                    pobij__mpqu = ''
                else:
                    pobij__mpqu = str(nhdny__paeqq)
    if is_overload_none(on) and is_overload_none(left_on) and is_overload_none(
        right_on) and is_overload_false(left_index) and is_overload_false(
        right_index):
        left_keys = pqn__uoh
        right_keys = pqn__uoh
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
    xvhqb__ywx = get_overload_const_bool(_bodo_na_equal)
    validate_keys_length(left_index, right_index, left_keys, right_keys)
    validate_keys_dtypes(left, right, left_index, right_index, left_keys,
        right_keys)
    if is_overload_constant_tuple(suffixes):
        numcw__lta = get_overload_const_tuple(suffixes)
    if is_overload_constant_list(suffixes):
        numcw__lta = list(get_overload_const_list(suffixes))
    suffix_x = numcw__lta[0]
    suffix_y = numcw__lta[1]
    validate_unicity_output_column_names(suffix_x, suffix_y, left_keys,
        right_keys, left.columns, right.columns, indicator_val)
    left_keys = gen_const_tup(left_keys)
    right_keys = gen_const_tup(right_keys)
    aqh__aifei = "def _impl(left, right, how='inner', on=None, left_on=None,\n"
    aqh__aifei += (
        '    right_on=None, left_index=False, right_index=False, sort=False,\n'
        )
    aqh__aifei += """    suffixes=('_x', '_y'), copy=True, indicator=False, validate=None, _bodo_na_equal=True):
"""
    aqh__aifei += (
        """  return bodo.hiframes.pd_dataframe_ext.join_dummy(left, right, {}, {}, '{}', '{}', '{}', False, {}, {}, '{}')
"""
        .format(left_keys, right_keys, how, suffix_x, suffix_y,
        indicator_val, xvhqb__ywx, pobij__mpqu))
    iyph__amgxq = {}
    exec(aqh__aifei, {'bodo': bodo}, iyph__amgxq)
    _impl = iyph__amgxq['_impl']
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
    awk__jar = {string_array_type, dict_str_arr_type, binary_array_type,
        datetime_date_array_type, datetime_timedelta_array_type, boolean_array}
    csfti__htgu = {get_overload_const_str(gsz__ezyhx) for gsz__ezyhx in (
        left_on, right_on, on) if is_overload_constant_str(gsz__ezyhx)}
    for df in (left, right):
        for i, wzaok__ceul in enumerate(df.data):
            if not isinstance(wzaok__ceul, valid_dataframe_column_types
                ) and wzaok__ceul not in awk__jar:
                raise BodoError(
                    f'{name_func}(): use of column with {type(wzaok__ceul)} in merge unsupported'
                    )
            if df.columns[i] in csfti__htgu and isinstance(wzaok__ceul,
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
        numcw__lta = get_overload_const_tuple(suffixes)
    if is_overload_constant_list(suffixes):
        numcw__lta = list(get_overload_const_list(suffixes))
    if len(numcw__lta) != 2:
        raise BodoError(name_func +
            '(): The number of suffixes should be exactly 2')
    pqn__uoh = tuple(set(left.columns) & set(right.columns))
    if not is_overload_none(on):
        bfafy__tve = False
        if is_overload_constant_str(on):
            on_str = get_overload_const_str(on)
            bfafy__tve = on_str not in pqn__uoh and ('left.' in on_str or 
                'right.' in on_str)
        if len(pqn__uoh) == 0 and not bfafy__tve:
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
    hvm__ylgv = numba.core.registry.cpu_target.typing_context
    if is_overload_true(left_index) or is_overload_true(right_index):
        if is_overload_true(left_index) and is_overload_true(right_index):
            dah__ucsgn = left.index
            rrp__jibgo = isinstance(dah__ucsgn, StringIndexType)
            ypogz__vebx = right.index
            nacv__ugm = isinstance(ypogz__vebx, StringIndexType)
        elif is_overload_true(left_index):
            dah__ucsgn = left.index
            rrp__jibgo = isinstance(dah__ucsgn, StringIndexType)
            ypogz__vebx = right.data[right.columns.index(right_keys[0])]
            nacv__ugm = ypogz__vebx.dtype == string_type
        elif is_overload_true(right_index):
            dah__ucsgn = left.data[left.columns.index(left_keys[0])]
            rrp__jibgo = dah__ucsgn.dtype == string_type
            ypogz__vebx = right.index
            nacv__ugm = isinstance(ypogz__vebx, StringIndexType)
        if rrp__jibgo and nacv__ugm:
            return
        dah__ucsgn = dah__ucsgn.dtype
        ypogz__vebx = ypogz__vebx.dtype
        try:
            ytzlc__snc = hvm__ylgv.resolve_function_type(operator.eq, (
                dah__ucsgn, ypogz__vebx), {})
        except:
            raise_bodo_error(
                'merge: You are trying to merge on {lk_dtype} and {rk_dtype} columns. If you wish to proceed you should use pd.concat'
                .format(lk_dtype=dah__ucsgn, rk_dtype=ypogz__vebx))
    else:
        for wtsrk__wdwv, ibx__mtdpy in zip(left_keys, right_keys):
            dah__ucsgn = left.data[left.columns.index(wtsrk__wdwv)].dtype
            hfux__yhjce = left.data[left.columns.index(wtsrk__wdwv)]
            ypogz__vebx = right.data[right.columns.index(ibx__mtdpy)].dtype
            qggb__eay = right.data[right.columns.index(ibx__mtdpy)]
            if hfux__yhjce == qggb__eay:
                continue
            slxsx__kovk = (
                'merge: You are trying to merge on column {lk} of {lk_dtype} and column {rk} of {rk_dtype}. If you wish to proceed you should use pd.concat'
                .format(lk=wtsrk__wdwv, lk_dtype=dah__ucsgn, rk=ibx__mtdpy,
                rk_dtype=ypogz__vebx))
            ltr__ruu = dah__ucsgn == string_type
            jmx__kmcd = ypogz__vebx == string_type
            if ltr__ruu ^ jmx__kmcd:
                raise_bodo_error(slxsx__kovk)
            try:
                ytzlc__snc = hvm__ylgv.resolve_function_type(operator.eq, (
                    dah__ucsgn, ypogz__vebx), {})
            except:
                raise_bodo_error(slxsx__kovk)


def validate_keys(keys, df):
    tzfd__ajuxp = set(keys).difference(set(df.columns))
    if len(tzfd__ajuxp) > 0:
        if is_overload_constant_str(df.index.name_typ
            ) and get_overload_const_str(df.index.name_typ) in tzfd__ajuxp:
            raise_bodo_error(
                f'merge(): use of index {df.index.name_typ} as key for on/left_on/right_on is unsupported'
                )
        raise_bodo_error(
            f"""merge(): invalid key {tzfd__ajuxp} for on/left_on/right_on
merge supports only valid column names {df.columns}"""
            )


@overload_method(DataFrameType, 'join', inline='always', no_unliteral=True)
def overload_dataframe_join(left, other, on=None, how='left', lsuffix='',
    rsuffix='', sort=False):
    check_runtime_cols_unsupported(left, 'DataFrame.join()')
    check_runtime_cols_unsupported(other, 'DataFrame.join()')
    anq__ivbcd = dict(lsuffix=lsuffix, rsuffix=rsuffix)
    tsx__frrxz = dict(lsuffix='', rsuffix='')
    check_unsupported_args('DataFrame.join', anq__ivbcd, tsx__frrxz,
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
    aqh__aifei = "def _impl(left, other, on=None, how='left',\n"
    aqh__aifei += "    lsuffix='', rsuffix='', sort=False):\n"
    aqh__aifei += (
        """  return bodo.hiframes.pd_dataframe_ext.join_dummy(left, other, {}, {}, '{}', '{}', '{}', True, False, True, '')
"""
        .format(left_keys, right_keys, how, lsuffix, rsuffix))
    iyph__amgxq = {}
    exec(aqh__aifei, {'bodo': bodo}, iyph__amgxq)
    _impl = iyph__amgxq['_impl']
    return _impl


def validate_join_spec(left, other, on, how, lsuffix, rsuffix, sort):
    if not isinstance(other, DataFrameType):
        raise BodoError('join() requires dataframe inputs')
    ensure_constant_values('merge', 'how', how, ('left', 'right', 'outer',
        'inner'))
    if not is_overload_none(on) and len(get_overload_const_list(on)) != 1:
        raise BodoError('join(): len(on) must equals to 1 when specified.')
    if not is_overload_none(on):
        zwfot__zvva = get_overload_const_list(on)
        validate_keys(zwfot__zvva, left)
    if not is_overload_false(sort):
        raise BodoError(
            'join(): sort parameter only supports default value False')
    pqn__uoh = tuple(set(left.columns) & set(other.columns))
    if len(pqn__uoh) > 0:
        raise_bodo_error(
            'join(): not supporting joining on overlapping columns:{cols} Use DataFrame.merge() instead.'
            .format(cols=pqn__uoh))


def validate_unicity_output_column_names(suffix_x, suffix_y, left_keys,
    right_keys, left_columns, right_columns, indicator_val):
    epjl__elk = set(left_keys) & set(right_keys)
    yim__qos = set(left_columns) & set(right_columns)
    lqiy__plppd = yim__qos - epjl__elk
    odw__jjubp = set(left_columns) - yim__qos
    oeud__bji = set(right_columns) - yim__qos
    jhen__lhtv = {}

    def insertOutColumn(col_name):
        if col_name in jhen__lhtv:
            raise_bodo_error(
                'join(): two columns happen to have the same name : {}'.
                format(col_name))
        jhen__lhtv[col_name] = 0
    for xuq__rckkt in epjl__elk:
        insertOutColumn(xuq__rckkt)
    for xuq__rckkt in lqiy__plppd:
        kno__ynw = str(xuq__rckkt) + suffix_x
        codbu__vyd = str(xuq__rckkt) + suffix_y
        insertOutColumn(kno__ynw)
        insertOutColumn(codbu__vyd)
    for xuq__rckkt in odw__jjubp:
        insertOutColumn(xuq__rckkt)
    for xuq__rckkt in oeud__bji:
        insertOutColumn(xuq__rckkt)
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
    pqn__uoh = tuple(sorted(set(left.columns) & set(right.columns), key=lambda
        k: str(k)))
    if not is_overload_none(on):
        left_on = right_on = on
    if is_overload_none(on) and is_overload_none(left_on) and is_overload_none(
        right_on) and is_overload_false(left_index) and is_overload_false(
        right_index):
        left_keys = pqn__uoh
        right_keys = pqn__uoh
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
        numcw__lta = suffixes
    if is_overload_constant_list(suffixes):
        numcw__lta = list(get_overload_const_list(suffixes))
    if isinstance(suffixes, types.Omitted):
        numcw__lta = suffixes.value
    suffix_x = numcw__lta[0]
    suffix_y = numcw__lta[1]
    aqh__aifei = (
        'def _impl(left, right, on=None, left_on=None, right_on=None,\n')
    aqh__aifei += (
        '    left_index=False, right_index=False, by=None, left_by=None,\n')
    aqh__aifei += "    right_by=None, suffixes=('_x', '_y'), tolerance=None,\n"
    aqh__aifei += "    allow_exact_matches=True, direction='backward'):\n"
    aqh__aifei += '  suffix_x = suffixes[0]\n'
    aqh__aifei += '  suffix_y = suffixes[1]\n'
    aqh__aifei += (
        """  return bodo.hiframes.pd_dataframe_ext.join_dummy(left, right, {}, {}, 'asof', '{}', '{}', False, False, True, '')
"""
        .format(left_keys, right_keys, suffix_x, suffix_y))
    iyph__amgxq = {}
    exec(aqh__aifei, {'bodo': bodo}, iyph__amgxq)
    _impl = iyph__amgxq['_impl']
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
    anq__ivbcd = dict(sort=sort, group_keys=group_keys, squeeze=squeeze,
        observed=observed)
    juyc__vvs = dict(sort=False, group_keys=True, squeeze=False, observed=True)
    check_unsupported_args('Dataframe.groupby', anq__ivbcd, juyc__vvs,
        package_name='pandas', module_name='GroupBy')


def pivot_error_checking(df, index, columns, values, func_name):
    uapzf__kdyo = func_name == 'DataFrame.pivot_table'
    if uapzf__kdyo:
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
    pzh__mqdb = get_literal_value(columns)
    if isinstance(pzh__mqdb, (list, tuple)):
        if len(pzh__mqdb) > 1:
            raise BodoError(
                f"{func_name}(): 'columns' argument must be a constant column label not a {pzh__mqdb}"
                )
        pzh__mqdb = pzh__mqdb[0]
    if pzh__mqdb not in df.columns:
        raise BodoError(
            f"{func_name}(): 'columns' column {pzh__mqdb} not found in DataFrame {df}."
            )
    qrrjy__ksdgw = {ejinc__sxyv: i for i, ejinc__sxyv in enumerate(df.columns)}
    qhxz__dlb = qrrjy__ksdgw[pzh__mqdb]
    if is_overload_none(index):
        jfv__dedjr = []
        bce__isrqm = []
    else:
        bce__isrqm = get_literal_value(index)
        if not isinstance(bce__isrqm, (list, tuple)):
            bce__isrqm = [bce__isrqm]
        jfv__dedjr = []
        for index in bce__isrqm:
            if index not in qrrjy__ksdgw:
                raise BodoError(
                    f"{func_name}(): 'index' column {index} not found in DataFrame {df}."
                    )
            jfv__dedjr.append(qrrjy__ksdgw[index])
    if not (all(isinstance(ejinc__sxyv, int) for ejinc__sxyv in bce__isrqm) or
        all(isinstance(ejinc__sxyv, str) for ejinc__sxyv in bce__isrqm)):
        raise BodoError(
            f"{func_name}(): column names selected for 'index' must all share a common int or string type. Please convert your names to a common type using DataFrame.rename()"
            )
    if is_overload_none(values):
        chwk__byw = []
        dcip__cag = []
        zmev__ywa = jfv__dedjr + [qhxz__dlb]
        for i, ejinc__sxyv in enumerate(df.columns):
            if i not in zmev__ywa:
                chwk__byw.append(i)
                dcip__cag.append(ejinc__sxyv)
    else:
        dcip__cag = get_literal_value(values)
        if not isinstance(dcip__cag, (list, tuple)):
            dcip__cag = [dcip__cag]
        chwk__byw = []
        for val in dcip__cag:
            if val not in qrrjy__ksdgw:
                raise BodoError(
                    f"{func_name}(): 'values' column {val} not found in DataFrame {df}."
                    )
            chwk__byw.append(qrrjy__ksdgw[val])
    if all(isinstance(ejinc__sxyv, int) for ejinc__sxyv in dcip__cag):
        dcip__cag = np.array(dcip__cag, 'int64')
    elif all(isinstance(ejinc__sxyv, str) for ejinc__sxyv in dcip__cag):
        dcip__cag = pd.array(dcip__cag, 'string')
    else:
        raise BodoError(
            f"{func_name}(): column names selected for 'values' must all share a common int or string type. Please convert your names to a common type using DataFrame.rename()"
            )
    wrmii__fxn = set(chwk__byw) | set(jfv__dedjr) | {qhxz__dlb}
    if len(wrmii__fxn) != len(chwk__byw) + len(jfv__dedjr) + 1:
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
    if len(jfv__dedjr) == 0:
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
        for qgve__ccfip in jfv__dedjr:
            index_column = df.data[qgve__ccfip]
            check_valid_index_typ(index_column)
    uezz__cmf = df.data[qhxz__dlb]
    if isinstance(uezz__cmf, (bodo.ArrayItemArrayType, bodo.MapArrayType,
        bodo.StructArrayType, bodo.TupleArrayType, bodo.IntervalArrayType)):
        raise BodoError(
            f"{func_name}(): 'columns' DataFrame column must have scalar rows")
    if isinstance(uezz__cmf, bodo.CategoricalArrayType):
        raise BodoError(
            f"{func_name}(): 'columns' DataFrame column does not support categorical data"
            )
    for aon__qpu in chwk__byw:
        mwvo__mtea = df.data[aon__qpu]
        if isinstance(mwvo__mtea, (bodo.ArrayItemArrayType, bodo.
            MapArrayType, bodo.StructArrayType, bodo.TupleArrayType)
            ) or mwvo__mtea == bodo.binary_array_type:
            raise BodoError(
                f"{func_name}(): 'values' DataFrame column must have scalar rows"
                )
    return bce__isrqm, pzh__mqdb, dcip__cag, jfv__dedjr, qhxz__dlb, chwk__byw


@overload(pd.pivot, inline='always', no_unliteral=True)
@overload_method(DataFrameType, 'pivot', inline='always', no_unliteral=True)
def overload_dataframe_pivot(data, index=None, columns=None, values=None):
    check_runtime_cols_unsupported(data, 'DataFrame.pivot()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
        'DataFrame.pivot()')
    if not isinstance(data, DataFrameType):
        raise BodoError("pandas.pivot(): 'data' argument must be a DataFrame")
    (bce__isrqm, pzh__mqdb, dcip__cag, qgve__ccfip, qhxz__dlb, ugwu__ixka) = (
        pivot_error_checking(data, index, columns, values, 'DataFrame.pivot'))
    if len(bce__isrqm) == 0:
        if is_overload_none(data.index.name_typ):
            bce__isrqm = [None]
        else:
            bce__isrqm = [get_literal_value(data.index.name_typ)]
    if len(dcip__cag) == 1:
        jbto__loycy = None
    else:
        jbto__loycy = dcip__cag
    aqh__aifei = 'def impl(data, index=None, columns=None, values=None):\n'
    aqh__aifei += f'    pivot_values = data.iloc[:, {qhxz__dlb}].unique()\n'
    aqh__aifei += '    return bodo.hiframes.pd_dataframe_ext.pivot_impl(\n'
    if len(qgve__ccfip) == 0:
        aqh__aifei += f"""        (bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)),),
"""
    else:
        aqh__aifei += '        (\n'
        for vfwqg__cdlq in qgve__ccfip:
            aqh__aifei += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {vfwqg__cdlq}),
"""
        aqh__aifei += '        ),\n'
    aqh__aifei += f"""        (bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {qhxz__dlb}),),
"""
    aqh__aifei += '        (\n'
    for aon__qpu in ugwu__ixka:
        aqh__aifei += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {aon__qpu}),
"""
    aqh__aifei += '        ),\n'
    aqh__aifei += '        pivot_values,\n'
    aqh__aifei += '        index_lit_tup,\n'
    aqh__aifei += '        columns_lit,\n'
    aqh__aifei += '        values_name_const,\n'
    aqh__aifei += '    )\n'
    iyph__amgxq = {}
    exec(aqh__aifei, {'bodo': bodo, 'index_lit_tup': tuple(bce__isrqm),
        'columns_lit': pzh__mqdb, 'values_name_const': jbto__loycy},
        iyph__amgxq)
    impl = iyph__amgxq['impl']
    return impl


@overload(pd.pivot_table, inline='always', no_unliteral=True)
@overload_method(DataFrameType, 'pivot_table', inline='always',
    no_unliteral=True)
def overload_dataframe_pivot_table(data, values=None, index=None, columns=
    None, aggfunc='mean', fill_value=None, margins=False, dropna=True,
    margins_name='All', observed=False, sort=True, _pivot_values=None):
    check_runtime_cols_unsupported(data, 'DataFrame.pivot_table()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
        'DataFrame.pivot_table()')
    anq__ivbcd = dict(fill_value=fill_value, margins=margins, dropna=dropna,
        margins_name=margins_name, observed=observed, sort=sort)
    tsx__frrxz = dict(fill_value=None, margins=False, dropna=True,
        margins_name='All', observed=False, sort=True)
    check_unsupported_args('DataFrame.pivot_table', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    if not isinstance(data, DataFrameType):
        raise BodoError(
            "pandas.pivot_table(): 'data' argument must be a DataFrame")
    if _pivot_values is None:
        (bce__isrqm, pzh__mqdb, dcip__cag, qgve__ccfip, qhxz__dlb, ugwu__ixka
            ) = (pivot_error_checking(data, index, columns, values,
            'DataFrame.pivot_table'))
        if len(dcip__cag) == 1:
            jbto__loycy = None
        else:
            jbto__loycy = dcip__cag
        aqh__aifei = 'def impl(\n'
        aqh__aifei += '    data,\n'
        aqh__aifei += '    values=None,\n'
        aqh__aifei += '    index=None,\n'
        aqh__aifei += '    columns=None,\n'
        aqh__aifei += '    aggfunc="mean",\n'
        aqh__aifei += '    fill_value=None,\n'
        aqh__aifei += '    margins=False,\n'
        aqh__aifei += '    dropna=True,\n'
        aqh__aifei += '    margins_name="All",\n'
        aqh__aifei += '    observed=False,\n'
        aqh__aifei += '    sort=True,\n'
        aqh__aifei += '    _pivot_values=None,\n'
        aqh__aifei += '):\n'
        lmzx__dpa = qgve__ccfip + [qhxz__dlb] + ugwu__ixka
        aqh__aifei += f'    data = data.iloc[:, {lmzx__dpa}]\n'
        pwavz__scu = bce__isrqm + [pzh__mqdb]
        aqh__aifei += (
            f'    data = data.groupby({pwavz__scu!r}, as_index=False).agg(aggfunc)\n'
            )
        aqh__aifei += (
            f'    pivot_values = data.iloc[:, {len(qgve__ccfip)}].unique()\n')
        aqh__aifei += '    return bodo.hiframes.pd_dataframe_ext.pivot_impl(\n'
        aqh__aifei += '        (\n'
        for i in range(0, len(qgve__ccfip)):
            aqh__aifei += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {i}),
"""
        aqh__aifei += '        ),\n'
        aqh__aifei += f"""        (bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {len(qgve__ccfip)}),),
"""
        aqh__aifei += '        (\n'
        for i in range(len(qgve__ccfip) + 1, len(ugwu__ixka) + len(
            qgve__ccfip) + 1):
            aqh__aifei += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {i}),
"""
        aqh__aifei += '        ),\n'
        aqh__aifei += '        pivot_values,\n'
        aqh__aifei += '        index_lit_tup,\n'
        aqh__aifei += '        columns_lit,\n'
        aqh__aifei += '        values_name_const,\n'
        aqh__aifei += '        check_duplicates=False,\n'
        aqh__aifei += '    )\n'
        iyph__amgxq = {}
        exec(aqh__aifei, {'bodo': bodo, 'numba': numba, 'index_lit_tup':
            tuple(bce__isrqm), 'columns_lit': pzh__mqdb,
            'values_name_const': jbto__loycy}, iyph__amgxq)
        impl = iyph__amgxq['impl']
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
    anq__ivbcd = dict(values=values, rownames=rownames, colnames=colnames,
        aggfunc=aggfunc, margins=margins, margins_name=margins_name, dropna
        =dropna, normalize=normalize)
    tsx__frrxz = dict(values=None, rownames=None, colnames=None, aggfunc=
        None, margins=False, margins_name='All', dropna=True, normalize=False)
    check_unsupported_args('pandas.crosstab', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(index,
        'pandas.crosstab()')
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
    anq__ivbcd = dict(ignore_index=ignore_index, key=key)
    tsx__frrxz = dict(ignore_index=False, key=None)
    check_unsupported_args('DataFrame.sort_values', anq__ivbcd, tsx__frrxz,
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
    cofgf__yvcue = set(df.columns)
    if is_overload_constant_str(df.index.name_typ):
        cofgf__yvcue.add(get_overload_const_str(df.index.name_typ))
    if is_overload_constant_tuple(by):
        phjc__enwr = [get_overload_const_tuple(by)]
    else:
        phjc__enwr = get_overload_const_list(by)
    phjc__enwr = set((k, '') if (k, '') in cofgf__yvcue else k for k in
        phjc__enwr)
    if len(phjc__enwr.difference(cofgf__yvcue)) > 0:
        zwhrk__qab = list(set(get_overload_const_list(by)).difference(
            cofgf__yvcue))
        raise_bodo_error(f'sort_values(): invalid keys {zwhrk__qab} for by.')
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
        wxdh__yci = get_overload_const_list(na_position)
        for na_position in wxdh__yci:
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
    anq__ivbcd = dict(axis=axis, level=level, kind=kind, sort_remaining=
        sort_remaining, ignore_index=ignore_index, key=key)
    tsx__frrxz = dict(axis=0, level=None, kind='quicksort', sort_remaining=
        True, ignore_index=False, key=None)
    check_unsupported_args('DataFrame.sort_index', anq__ivbcd, tsx__frrxz,
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
    anq__ivbcd = dict(limit=limit, downcast=downcast)
    tsx__frrxz = dict(limit=None, downcast=None)
    check_unsupported_args('DataFrame.fillna', anq__ivbcd, tsx__frrxz,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.fillna()')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise BodoError("DataFrame.fillna(): 'axis' argument not supported.")
    gsem__tlg = not is_overload_none(value)
    uly__htus = not is_overload_none(method)
    if gsem__tlg and uly__htus:
        raise BodoError(
            "DataFrame.fillna(): Cannot specify both 'value' and 'method'.")
    if not gsem__tlg and not uly__htus:
        raise BodoError(
            "DataFrame.fillna(): Must specify one of 'value' and 'method'.")
    if gsem__tlg:
        yyvfs__iyhu = 'value=value'
    else:
        yyvfs__iyhu = 'method=method'
    data_args = [(
        f"df['{ejinc__sxyv}'].fillna({yyvfs__iyhu}, inplace=inplace)" if
        isinstance(ejinc__sxyv, str) else
        f'df[{ejinc__sxyv}].fillna({yyvfs__iyhu}, inplace=inplace)') for
        ejinc__sxyv in df.columns]
    aqh__aifei = """def impl(df, value=None, method=None, axis=None, inplace=False, limit=None, downcast=None):
"""
    if is_overload_true(inplace):
        aqh__aifei += '  ' + '  \n'.join(data_args) + '\n'
        iyph__amgxq = {}
        exec(aqh__aifei, {}, iyph__amgxq)
        impl = iyph__amgxq['impl']
        return impl
    else:
        return _gen_init_df(aqh__aifei, df.columns, ', '.join(uyel__uly +
            '.values' for uyel__uly in data_args))


@overload_method(DataFrameType, 'reset_index', inline='always',
    no_unliteral=True)
def overload_dataframe_reset_index(df, level=None, drop=False, inplace=
    False, col_level=0, col_fill='', _bodo_transformed=False):
    check_runtime_cols_unsupported(df, 'DataFrame.reset_index()')
    anq__ivbcd = dict(col_level=col_level, col_fill=col_fill)
    tsx__frrxz = dict(col_level=0, col_fill='')
    check_unsupported_args('DataFrame.reset_index', anq__ivbcd, tsx__frrxz,
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
    aqh__aifei = """def impl(df, level=None, drop=False, inplace=False, col_level=0, col_fill='', _bodo_transformed=False,):
"""
    aqh__aifei += (
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
        lmn__idxt = 'index' if 'index' not in columns else 'level_0'
        index_names = get_index_names(df.index, 'DataFrame.reset_index()',
            lmn__idxt)
        columns = index_names + columns
        if isinstance(df.index, MultiIndexType):
            aqh__aifei += (
                '  m_index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
                )
            xlip__zgf = ['m_index._data[{}]'.format(i) for i in range(df.
                index.nlevels)]
            data_args = xlip__zgf + data_args
        else:
            orpgb__bmhh = (
                'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
                )
            data_args = [orpgb__bmhh] + data_args
    return _gen_init_df(aqh__aifei, columns, ', '.join(data_args), 'index')


def _is_all_levels(df, level):
    imbbc__gnlfk = len(get_index_data_arr_types(df.index))
    return is_overload_none(level) or is_overload_constant_int(level
        ) and get_overload_const_int(level
        ) == 0 and imbbc__gnlfk == 1 or is_overload_constant_list(level
        ) and list(get_overload_const_list(level)) == list(range(imbbc__gnlfk))


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
        gtw__ehd = list(range(len(df.columns)))
    elif not is_overload_constant_list(subset):
        raise_bodo_error(
            f'df.dropna(): subset argument should a constant list, not {subset}'
            )
    else:
        yaz__pgwmc = get_overload_const_list(subset)
        gtw__ehd = []
        for uhfq__parau in yaz__pgwmc:
            if uhfq__parau not in df.columns:
                raise_bodo_error(
                    f"df.dropna(): column '{uhfq__parau}' not in data frame columns {df}"
                    )
            gtw__ehd.append(df.columns.index(uhfq__parau))
    gac__vkh = len(df.columns)
    data_args = ', '.join('data_{}'.format(i) for i in range(gac__vkh))
    aqh__aifei = (
        "def impl(df, axis=0, how='any', thresh=None, subset=None, inplace=False):\n"
        )
    for i in range(gac__vkh):
        aqh__aifei += (
            '  data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})\n'
            .format(i))
    index = (
        'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
        )
    aqh__aifei += (
        """  ({0}, index_arr) = bodo.libs.array_kernels.dropna(({0}, {1}), how, thresh, ({2},))
"""
        .format(data_args, index, ', '.join(str(a) for a in gtw__ehd)))
    aqh__aifei += (
        '  index = bodo.utils.conversion.index_from_array(index_arr)\n')
    return _gen_init_df(aqh__aifei, df.columns, data_args, 'index')


@overload_method(DataFrameType, 'drop', inline='always', no_unliteral=True)
def overload_dataframe_drop(df, labels=None, axis=0, index=None, columns=
    None, level=None, inplace=False, errors='raise', _bodo_transformed=False):
    check_runtime_cols_unsupported(df, 'DataFrame.drop()')
    anq__ivbcd = dict(index=index, level=level, errors=errors)
    tsx__frrxz = dict(index=None, level=None, errors='raise')
    check_unsupported_args('DataFrame.drop', anq__ivbcd, tsx__frrxz,
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
            bat__rbz = get_overload_const_str(labels),
        elif is_overload_constant_list(labels):
            bat__rbz = get_overload_const_list(labels)
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
            bat__rbz = get_overload_const_str(columns),
        elif is_overload_constant_list(columns):
            bat__rbz = get_overload_const_list(columns)
        else:
            raise_bodo_error(
                'constant list of columns expected for labels in DataFrame.drop()'
                )
    for ejinc__sxyv in bat__rbz:
        if ejinc__sxyv not in df.columns:
            raise_bodo_error(
                'DataFrame.drop(): column {} not in DataFrame columns {}'.
                format(ejinc__sxyv, df.columns))
    if len(set(bat__rbz)) == len(df.columns):
        raise BodoError('DataFrame.drop(): Dropping all columns not supported.'
            )
    inplace = is_overload_true(inplace)
    lklz__ohn = tuple(ejinc__sxyv for ejinc__sxyv in df.columns if 
        ejinc__sxyv not in bat__rbz)
    data_args = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(df.columns.index(ejinc__sxyv), '.copy()' if not inplace else
        '') for ejinc__sxyv in lklz__ohn)
    aqh__aifei = (
        'def impl(df, labels=None, axis=0, index=None, columns=None,\n')
    aqh__aifei += (
        "     level=None, inplace=False, errors='raise', _bodo_transformed=False):\n"
        )
    index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
    return _gen_init_df(aqh__aifei, lklz__ohn, data_args, index)


@overload_method(DataFrameType, 'append', inline='always', no_unliteral=True)
def overload_dataframe_append(df, other, ignore_index=False,
    verify_integrity=False, sort=None):
    check_runtime_cols_unsupported(df, 'DataFrame.append()')
    check_runtime_cols_unsupported(other, 'DataFrame.append()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.append()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(other,
        'DataFrame.append()')
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
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.sample()')
    anq__ivbcd = dict(random_state=random_state, weights=weights, axis=axis,
        ignore_index=ignore_index)
    wtsa__ygb = dict(random_state=None, weights=None, axis=None,
        ignore_index=False)
    check_unsupported_args('DataFrame.sample', anq__ivbcd, wtsa__ygb,
        package_name='pandas', module_name='DataFrame')
    if not is_overload_none(n) and not is_overload_none(frac):
        raise BodoError(
            'DataFrame.sample(): only one of n and frac option can be selected'
            )
    gac__vkh = len(df.columns)
    data_args = ', '.join('data_{}'.format(i) for i in range(gac__vkh))
    bzve__owk = ', '.join('rhs_data_{}'.format(i) for i in range(gac__vkh))
    aqh__aifei = """def impl(df, n=None, frac=None, replace=False, weights=None, random_state=None, axis=None, ignore_index=False):
"""
    aqh__aifei += '  if (frac == 1 or n == len(df)) and not replace:\n'
    aqh__aifei += (
        '    return bodo.allgatherv(bodo.random_shuffle(df), False)\n')
    for i in range(gac__vkh):
        aqh__aifei += (
            """  rhs_data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})
"""
            .format(i))
    aqh__aifei += '  if frac is None:\n'
    aqh__aifei += '    frac_d = -1.0\n'
    aqh__aifei += '  else:\n'
    aqh__aifei += '    frac_d = frac\n'
    aqh__aifei += '  if n is None:\n'
    aqh__aifei += '    n_i = 0\n'
    aqh__aifei += '  else:\n'
    aqh__aifei += '    n_i = n\n'
    index = (
        'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
        )
    aqh__aifei += f"""  ({data_args},), index_arr = bodo.libs.array_kernels.sample_table_operation(({bzve__owk},), {index}, n_i, frac_d, replace)
"""
    aqh__aifei += (
        '  index = bodo.utils.conversion.index_from_array(index_arr)\n')
    return bodo.hiframes.dataframe_impl._gen_init_df(aqh__aifei, df.columns,
        data_args, 'index')


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
    vbjk__zasha = {'verbose': verbose, 'buf': buf, 'max_cols': max_cols,
        'memory_usage': memory_usage, 'show_counts': show_counts,
        'null_counts': null_counts}
    pwrz__jhve = {'verbose': None, 'buf': None, 'max_cols': None,
        'memory_usage': None, 'show_counts': None, 'null_counts': None}
    check_unsupported_args('DataFrame.info', vbjk__zasha, pwrz__jhve,
        package_name='pandas', module_name='DataFrame')
    ilm__rqecr = f"<class '{str(type(df)).split('.')[-1]}"
    if len(df.columns) == 0:

        def _info_impl(df, verbose=None, buf=None, max_cols=None,
            memory_usage=None, show_counts=None, null_counts=None):
            rgcwu__jrxvb = ilm__rqecr + '\n'
            rgcwu__jrxvb += 'Index: 0 entries\n'
            rgcwu__jrxvb += 'Empty DataFrame'
            print(rgcwu__jrxvb)
        return _info_impl
    else:
        aqh__aifei = """def _info_impl(df, verbose=None, buf=None, max_cols=None, memory_usage=None, show_counts=None, null_counts=None): #pragma: no cover
"""
        aqh__aifei += '    ncols = df.shape[1]\n'
        aqh__aifei += f'    lines = "{ilm__rqecr}\\n"\n'
        aqh__aifei += f'    lines += "{df.index}: "\n'
        aqh__aifei += (
            '    index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
            )
        if isinstance(df.index, bodo.hiframes.pd_index_ext.RangeIndexType):
            aqh__aifei += """    lines += f"{len(index)} entries, {index.start} to {index.stop-1}\\n\"
"""
        elif isinstance(df.index, bodo.hiframes.pd_index_ext.StringIndexType):
            aqh__aifei += """    lines += f"{len(index)} entries, {index[0]} to {index[len(index)-1]}\\n\"
"""
        else:
            aqh__aifei += (
                '    lines += f"{len(index)} entries, {index[0]} to {index[-1]}\\n"\n'
                )
        aqh__aifei += (
            '    lines += f"Data columns (total {ncols} columns):\\n"\n')
        aqh__aifei += (
            f'    space = {max(len(str(k)) for k in df.columns) + 1}\n')
        aqh__aifei += '    column_width = max(space, 7)\n'
        aqh__aifei += '    column= "Column"\n'
        aqh__aifei += '    underl= "------"\n'
        aqh__aifei += (
            '    lines += f"#   {column:<{column_width}} Non-Null Count  Dtype\\n"\n'
            )
        aqh__aifei += (
            '    lines += f"--- {underl:<{column_width}} --------------  -----\\n"\n'
            )
        aqh__aifei += '    mem_size = 0\n'
        aqh__aifei += (
            '    col_name = bodo.libs.str_arr_ext.pre_alloc_string_array(ncols, -1)\n'
            )
        aqh__aifei += """    non_null_count = bodo.libs.str_arr_ext.pre_alloc_string_array(ncols, -1)
"""
        aqh__aifei += (
            '    col_dtype = bodo.libs.str_arr_ext.pre_alloc_string_array(ncols, -1)\n'
            )
        lvhx__spc = dict()
        for i in range(len(df.columns)):
            aqh__aifei += f"""    non_null_count[{i}] = str(bodo.libs.array_ops.array_op_count(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})))
"""
            gktxl__mddhv = f'{df.data[i].dtype}'
            if isinstance(df.data[i], bodo.CategoricalArrayType):
                gktxl__mddhv = 'category'
            elif isinstance(df.data[i], bodo.IntegerArrayType):
                iwd__srb = bodo.libs.int_arr_ext.IntDtype(df.data[i].dtype
                    ).name
                gktxl__mddhv = f'{iwd__srb[:-7]}'
            aqh__aifei += f'    col_dtype[{i}] = "{gktxl__mddhv}"\n'
            if gktxl__mddhv in lvhx__spc:
                lvhx__spc[gktxl__mddhv] += 1
            else:
                lvhx__spc[gktxl__mddhv] = 1
            aqh__aifei += f'    col_name[{i}] = "{df.columns[i]}"\n'
            aqh__aifei += f"""    mem_size += bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).nbytes
"""
        aqh__aifei += """    column_info = [f'{i:^3} {name:<{column_width}} {count} non-null      {dtype}' for i, (name, count, dtype) in enumerate(zip(col_name, non_null_count, col_dtype))]
"""
        aqh__aifei += '    for i in column_info:\n'
        aqh__aifei += "        lines += f'{i}\\n'\n"
        jrcg__spb = ', '.join(f'{k}({lvhx__spc[k]})' for k in sorted(lvhx__spc)
            )
        aqh__aifei += f"    lines += 'dtypes: {jrcg__spb}\\n'\n"
        aqh__aifei += '    mem_size += df.index.nbytes\n'
        aqh__aifei += '    total_size = _sizeof_fmt(mem_size)\n'
        aqh__aifei += "    lines += f'memory usage: {total_size}'\n"
        aqh__aifei += '    print(lines)\n'
        iyph__amgxq = {}
        exec(aqh__aifei, {'_sizeof_fmt': _sizeof_fmt, 'pd': pd, 'bodo':
            bodo, 'np': np}, iyph__amgxq)
        _info_impl = iyph__amgxq['_info_impl']
        return _info_impl


@overload_method(DataFrameType, 'memory_usage', inline='always',
    no_unliteral=True)
def overload_dataframe_memory_usage(df, index=True, deep=False):
    check_runtime_cols_unsupported(df, 'DataFrame.memory_usage()')
    aqh__aifei = 'def impl(df, index=True, deep=False):\n'
    data = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).nbytes'
         for i in range(len(df.columns)))
    if is_overload_true(index):
        udzfc__fen = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df).nbytes\n,')
        abxwd__gfi = ','.join(f"'{ejinc__sxyv}'" for ejinc__sxyv in df.columns)
        arr = f"bodo.utils.conversion.coerce_to_array(('Index',{abxwd__gfi}))"
        index = f'bodo.hiframes.pd_index_ext.init_binary_str_index({arr})'
        aqh__aifei += f"""  return bodo.hiframes.pd_series_ext.init_series(({udzfc__fen}{data}), {index}, None)
"""
    else:
        srg__bttm = ',' if len(df.columns) == 1 else ''
        lspz__gwug = gen_const_tup(df.columns)
        aqh__aifei += f"""  return bodo.hiframes.pd_series_ext.init_series(({data}{srg__bttm}), pd.Index({lspz__gwug}), None)
"""
    iyph__amgxq = {}
    exec(aqh__aifei, {'bodo': bodo, 'pd': pd}, iyph__amgxq)
    impl = iyph__amgxq['impl']
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
    eneqg__qwqtp = 'read_excel_df{}'.format(next_label())
    setattr(types, eneqg__qwqtp, df_type)
    rwgd__gue = False
    if is_overload_constant_list(parse_dates):
        rwgd__gue = get_overload_const_list(parse_dates)
    ybzfe__krx = ', '.join(["'{}':{}".format(cname, _get_pd_dtype_str(t)) for
        cname, t in zip(df_type.columns, df_type.data)])
    aqh__aifei = (
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
        .format(eneqg__qwqtp, list(df_type.columns), ybzfe__krx, rwgd__gue))
    iyph__amgxq = {}
    exec(aqh__aifei, globals(), iyph__amgxq)
    impl = iyph__amgxq['impl']
    return impl


def overload_dataframe_plot(df, x=None, y=None, kind='line', figsize=None,
    xlabel=None, ylabel=None, title=None, legend=True, fontsize=None,
    xticks=None, yticks=None, ax=None):
    try:
        import matplotlib.pyplot as plt
    except ImportError as bld__ufizx:
        raise BodoError('df.plot needs matplotllib which is not installed.')
    aqh__aifei = (
        "def impl(df, x=None, y=None, kind='line', figsize=None, xlabel=None, \n"
        )
    aqh__aifei += '    ylabel=None, title=None, legend=True, fontsize=None, \n'
    aqh__aifei += '    xticks=None, yticks=None, ax=None):\n'
    if is_overload_none(ax):
        aqh__aifei += '   fig, ax = plt.subplots()\n'
    else:
        aqh__aifei += '   fig = ax.get_figure()\n'
    if not is_overload_none(figsize):
        aqh__aifei += '   fig.set_figwidth(figsize[0])\n'
        aqh__aifei += '   fig.set_figheight(figsize[1])\n'
    if is_overload_none(xlabel):
        aqh__aifei += '   xlabel = x\n'
    aqh__aifei += '   ax.set_xlabel(xlabel)\n'
    if is_overload_none(ylabel):
        aqh__aifei += '   ylabel = y\n'
    else:
        aqh__aifei += '   ax.set_ylabel(ylabel)\n'
    if not is_overload_none(title):
        aqh__aifei += '   ax.set_title(title)\n'
    if not is_overload_none(fontsize):
        aqh__aifei += '   ax.tick_params(labelsize=fontsize)\n'
    kind = get_overload_const_str(kind)
    if kind == 'line':
        if is_overload_none(x) and is_overload_none(y):
            for i in range(len(df.columns)):
                if isinstance(df.data[i], (types.Array, IntegerArrayType)
                    ) and isinstance(df.data[i].dtype, (types.Integer,
                    types.Float)):
                    aqh__aifei += (
                        f'   ax.plot(df.iloc[:, {i}], label=df.columns[{i}])\n'
                        )
        elif is_overload_none(x):
            aqh__aifei += '   ax.plot(df[y], label=y)\n'
        elif is_overload_none(y):
            xmb__zhatf = get_overload_const_str(x)
            olj__jvbsj = df.columns.index(xmb__zhatf)
            for i in range(len(df.columns)):
                if isinstance(df.data[i], (types.Array, IntegerArrayType)
                    ) and isinstance(df.data[i].dtype, (types.Integer,
                    types.Float)):
                    if olj__jvbsj != i:
                        aqh__aifei += (
                            f'   ax.plot(df[x], df.iloc[:, {i}], label=df.columns[{i}])\n'
                            )
        else:
            aqh__aifei += '   ax.plot(df[x], df[y], label=y)\n'
    elif kind == 'scatter':
        legend = False
        aqh__aifei += '   ax.scatter(df[x], df[y], s=20)\n'
        aqh__aifei += '   ax.set_ylabel(ylabel)\n'
    if not is_overload_none(xticks):
        aqh__aifei += '   ax.set_xticks(xticks)\n'
    if not is_overload_none(yticks):
        aqh__aifei += '   ax.set_yticks(yticks)\n'
    if is_overload_true(legend):
        aqh__aifei += '   ax.legend()\n'
    aqh__aifei += '   return ax\n'
    iyph__amgxq = {}
    exec(aqh__aifei, {'bodo': bodo, 'plt': plt}, iyph__amgxq)
    impl = iyph__amgxq['impl']
    return impl


@lower_builtin('df.plot', DataFrameType, types.VarArg(types.Any))
def dataframe_plot_low(context, builder, sig, args):
    impl = overload_dataframe_plot(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


def is_df_values_numpy_supported_dftyp(df_typ):
    for cxfc__zcsiw in df_typ.data:
        if not (isinstance(cxfc__zcsiw, IntegerArrayType) or isinstance(
            cxfc__zcsiw.dtype, types.Number) or cxfc__zcsiw.dtype in (bodo.
            datetime64ns, bodo.timedelta64ns)):
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
        wcux__zcg = args[0]
        ncyj__snirv = args[1].literal_value
        val = args[2]
        assert val != types.unknown
        bazs__ioly = wcux__zcg
        check_runtime_cols_unsupported(wcux__zcg, 'set_df_col()')
        if isinstance(wcux__zcg, DataFrameType):
            index = wcux__zcg.index
            if len(wcux__zcg.columns) == 0:
                index = bodo.hiframes.pd_index_ext.RangeIndexType(types.none)
            if isinstance(val, SeriesType):
                if len(wcux__zcg.columns) == 0:
                    index = val.index
                val = val.data
            if is_pd_index_type(val):
                val = bodo.utils.typing.get_index_data_arr_types(val)[0]
            if isinstance(val, types.List):
                val = dtype_to_array_type(val.dtype)
            if not is_array_typ(val):
                val = dtype_to_array_type(val)
            if ncyj__snirv in wcux__zcg.columns:
                lklz__ohn = wcux__zcg.columns
                iiilg__vtggv = wcux__zcg.columns.index(ncyj__snirv)
                ccead__dbig = list(wcux__zcg.data)
                ccead__dbig[iiilg__vtggv] = val
                ccead__dbig = tuple(ccead__dbig)
            else:
                lklz__ohn = wcux__zcg.columns + (ncyj__snirv,)
                ccead__dbig = wcux__zcg.data + (val,)
            bazs__ioly = DataFrameType(ccead__dbig, index, lklz__ohn,
                wcux__zcg.dist, wcux__zcg.is_table_format)
        return bazs__ioly(*args)


SetDfColInfer.prefer_literal = True


def _parse_query_expr(expr, env, columns, cleaned_columns, index_name=None,
    join_cleaned_cols=()):
    ugeol__ycf = {}

    def _rewrite_membership_op(self, node, left, right):
        cghcv__igbtb = node.op
        op = self.visit(cghcv__igbtb)
        return op, cghcv__igbtb, left, right

    def _maybe_evaluate_binop(self, op, op_class, lhs, rhs, eval_in_python=
        ('in', 'not in'), maybe_eval_in_python=('==', '!=', '<', '>', '<=',
        '>=')):
        res = op(lhs, rhs)
        return res
    sjq__qtdp = []


    class NewFuncNode(pd.core.computation.ops.FuncNode):

        def __init__(self, name):
            if (name not in pd.core.computation.ops.MATHOPS or pd.core.
                computation.check._NUMEXPR_INSTALLED and pd.core.
                computation.check_NUMEXPR_VERSION < pd.core.computation.ops
                .LooseVersion('2.6.9') and name in ('floor', 'ceil')):
                if name not in sjq__qtdp:
                    raise BodoError('"{0}" is not a supported function'.
                        format(name))
            self.name = name
            if name in sjq__qtdp:
                self.func = name
            else:
                self.func = getattr(np, name)

        def __call__(self, *args):
            return pd.core.computation.ops.MathCall(self, args)

        def __repr__(self):
            return pd.io.formats.printing.pprint_thing(self.name)

    def visit_Attribute(self, node, **kwargs):
        omho__vkkqs = node.attr
        value = node.value
        vav__svdga = pd.core.computation.ops.LOCAL_TAG
        if omho__vkkqs in ('str', 'dt'):
            try:
                sbi__nax = str(self.visit(value))
            except pd.core.computation.ops.UndefinedVariableError as fmoqa__bss:
                col_name = fmoqa__bss.args[0].split("'")[1]
                raise BodoError(
                    'df.query(): column {} is not found in dataframe columns {}'
                    .format(col_name, columns))
        else:
            sbi__nax = str(self.visit(value))
        suq__wusvp = sbi__nax, omho__vkkqs
        if suq__wusvp in join_cleaned_cols:
            omho__vkkqs = join_cleaned_cols[suq__wusvp]
        name = sbi__nax + '.' + omho__vkkqs
        if name.startswith(vav__svdga):
            name = name[len(vav__svdga):]
        if omho__vkkqs in ('str', 'dt'):
            bgz__uuv = columns[cleaned_columns.index(sbi__nax)]
            ugeol__ycf[bgz__uuv] = sbi__nax
            self.env.scope[name] = 0
            return self.term_type(vav__svdga + name, self.env)
        sjq__qtdp.append(name)
        return NewFuncNode(name)

    def __str__(self):
        if isinstance(self.value, list):
            return '{}'.format(self.value)
        if isinstance(self.value, str):
            return "'{}'".format(self.value)
        return pd.io.formats.printing.pprint_thing(self.name)

    def math__str__(self):
        if self.op in sjq__qtdp:
            return pd.io.formats.printing.pprint_thing('{0}({1})'.format(
                self.op, ','.join(map(str, self.operands))))
        oobqt__mwl = map(lambda a:
            'bodo.hiframes.pd_series_ext.get_series_data({})'.format(str(a)
            ), self.operands)
        op = 'np.{}'.format(self.op)
        ncyj__snirv = (
            'bodo.hiframes.pd_index_ext.init_range_index(0, len({}), 1, None)'
            .format(str(self.operands[0])))
        return pd.io.formats.printing.pprint_thing(
            'bodo.hiframes.pd_series_ext.init_series({0}({1}), {2})'.format
            (op, ','.join(oobqt__mwl), ncyj__snirv))

    def op__str__(self):
        uisx__prwc = ('({0})'.format(pd.io.formats.printing.pprint_thing(
            abgg__ffbs)) for abgg__ffbs in self.operands)
        if self.op == 'in':
            return pd.io.formats.printing.pprint_thing(
                'bodo.hiframes.pd_dataframe_ext.val_isin_dummy({})'.format(
                ', '.join(uisx__prwc)))
        if self.op == 'not in':
            return pd.io.formats.printing.pprint_thing(
                'bodo.hiframes.pd_dataframe_ext.val_notin_dummy({})'.format
                (', '.join(uisx__prwc)))
        return pd.io.formats.printing.pprint_thing(' {0} '.format(self.op).
            join(uisx__prwc))
    zpug__ofyl = (pd.core.computation.expr.BaseExprVisitor.
        _rewrite_membership_op)
    goby__jtboo = (pd.core.computation.expr.BaseExprVisitor.
        _maybe_evaluate_binop)
    begk__ugyae = pd.core.computation.expr.BaseExprVisitor.visit_Attribute
    jsdve__lzg = (pd.core.computation.expr.BaseExprVisitor.
        _maybe_downcast_constants)
    cqpno__fxb = pd.core.computation.ops.Term.__str__
    mpwml__xoq = pd.core.computation.ops.MathCall.__str__
    aukox__fwhoy = pd.core.computation.ops.Op.__str__
    gajw__xos = pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops
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
        knl__juyur = pd.core.computation.expr.Expr(expr, env=env)
        ckigk__iagyg = str(knl__juyur)
    except pd.core.computation.ops.UndefinedVariableError as fmoqa__bss:
        if not is_overload_none(index_name) and get_overload_const_str(
            index_name) == fmoqa__bss.args[0].split("'")[1]:
            raise BodoError(
                "df.query(): Refering to named index ('{}') by name is not supported"
                .format(get_overload_const_str(index_name)))
        else:
            raise BodoError(f'df.query(): undefined variable, {fmoqa__bss}')
    finally:
        pd.core.computation.expr.BaseExprVisitor._rewrite_membership_op = (
            zpug__ofyl)
        pd.core.computation.expr.BaseExprVisitor._maybe_evaluate_binop = (
            goby__jtboo)
        pd.core.computation.expr.BaseExprVisitor.visit_Attribute = begk__ugyae
        (pd.core.computation.expr.BaseExprVisitor._maybe_downcast_constants
            ) = jsdve__lzg
        pd.core.computation.ops.Term.__str__ = cqpno__fxb
        pd.core.computation.ops.MathCall.__str__ = mpwml__xoq
        pd.core.computation.ops.Op.__str__ = aukox__fwhoy
        pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops = (
            gajw__xos)
    kigjw__gix = pd.core.computation.parsing.clean_column_name
    ugeol__ycf.update({ejinc__sxyv: kigjw__gix(ejinc__sxyv) for ejinc__sxyv in
        columns if kigjw__gix(ejinc__sxyv) in knl__juyur.names})
    return knl__juyur, ckigk__iagyg, ugeol__ycf


class DataFrameTupleIterator(types.SimpleIteratorType):

    def __init__(self, col_names, arr_typs):
        self.array_types = arr_typs
        self.col_names = col_names
        ceclz__busim = ['{}={}'.format(col_names[i], arr_typs[i]) for i in
            range(len(col_names))]
        name = 'itertuples({})'.format(','.join(ceclz__busim))
        mtspj__atg = namedtuple('Pandas', col_names)
        qpa__vdy = types.NamedTuple([_get_series_dtype(a) for a in arr_typs
            ], mtspj__atg)
        super(DataFrameTupleIterator, self).__init__(name, qpa__vdy)

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
        emhmu__ryvpy = [if_series_to_array_type(a) for a in args[len(args) //
            2:]]
        assert 'Index' not in col_names[0]
        col_names = ['Index'] + col_names
        emhmu__ryvpy = [types.Array(types.int64, 1, 'C')] + emhmu__ryvpy
        kmu__avtth = DataFrameTupleIterator(col_names, emhmu__ryvpy)
        return kmu__avtth(*args)


TypeIterTuples.prefer_literal = True


@register_model(DataFrameTupleIterator)
class DataFrameTupleIteratorModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        navpx__vdz = [('index', types.EphemeralPointer(types.uintp))] + [(
            'array{}'.format(i), arr) for i, arr in enumerate(fe_type.
            array_types[1:])]
        super(DataFrameTupleIteratorModel, self).__init__(dmm, fe_type,
            navpx__vdz)

    def from_return(self, builder, value):
        return value


@lower_builtin(get_itertuples, types.VarArg(types.Any))
def get_itertuples_impl(context, builder, sig, args):
    slw__bqyu = args[len(args) // 2:]
    imko__fvjru = sig.args[len(sig.args) // 2:]
    jzo__qdo = context.make_helper(builder, sig.return_type)
    tfy__dlpqm = context.get_constant(types.intp, 0)
    tnbet__xppw = cgutils.alloca_once_value(builder, tfy__dlpqm)
    jzo__qdo.index = tnbet__xppw
    for i, arr in enumerate(slw__bqyu):
        setattr(jzo__qdo, 'array{}'.format(i), arr)
    for arr, arr_typ in zip(slw__bqyu, imko__fvjru):
        context.nrt.incref(builder, arr_typ, arr)
    res = jzo__qdo._getvalue()
    return impl_ret_new_ref(context, builder, sig.return_type, res)


@lower_builtin('getiter', DataFrameTupleIterator)
def getiter_itertuples(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@lower_builtin('iternext', DataFrameTupleIterator)
@iternext_impl(RefType.UNTRACKED)
def iternext_itertuples(context, builder, sig, args, result):
    ocig__qljx, = sig.args
    yzxa__wwi, = args
    jzo__qdo = context.make_helper(builder, ocig__qljx, value=yzxa__wwi)
    qcsv__mmo = signature(types.intp, ocig__qljx.array_types[1])
    gbxu__wdc = context.compile_internal(builder, lambda a: len(a),
        qcsv__mmo, [jzo__qdo.array0])
    index = builder.load(jzo__qdo.index)
    wigyh__scmi = builder.icmp(lc.ICMP_SLT, index, gbxu__wdc)
    result.set_valid(wigyh__scmi)
    with builder.if_then(wigyh__scmi):
        values = [index]
        for i, arr_typ in enumerate(ocig__qljx.array_types[1:]):
            tja__rsei = getattr(jzo__qdo, 'array{}'.format(i))
            if arr_typ == types.Array(types.NPDatetime('ns'), 1, 'C'):
                yzv__ymsr = signature(pd_timestamp_type, arr_typ, types.intp)
                val = context.compile_internal(builder, lambda a, i: bodo.
                    hiframes.pd_timestamp_ext.
                    convert_datetime64_to_timestamp(np.int64(a[i])),
                    yzv__ymsr, [tja__rsei, index])
            else:
                yzv__ymsr = signature(arr_typ.dtype, arr_typ, types.intp)
                val = context.compile_internal(builder, lambda a, i: a[i],
                    yzv__ymsr, [tja__rsei, index])
            values.append(val)
        value = context.make_tuple(builder, ocig__qljx.yield_type, values)
        result.yield_(value)
        rhibu__xbriy = cgutils.increment_index(builder, index)
        builder.store(rhibu__xbriy, jzo__qdo.index)


def _analyze_op_pair_first(self, scope, equiv_set, expr, lhs):
    typ = self.typemap[expr.value.name].first_type
    if not isinstance(typ, types.NamedTuple):
        return None
    lhs = ir.Var(scope, mk_unique_var('tuple_var'), expr.loc)
    self.typemap[lhs.name] = typ
    rhs = ir.Expr.pair_first(expr.value, expr.loc)
    ufo__nqf = ir.Assign(rhs, lhs, expr.loc)
    wvf__edumu = lhs
    dbs__lvyi = []
    ywa__knc = []
    gfiz__utnmz = typ.count
    for i in range(gfiz__utnmz):
        max__lzs = ir.Var(wvf__edumu.scope, mk_unique_var('{}_size{}'.
            format(wvf__edumu.name, i)), wvf__edumu.loc)
        zruki__uagmr = ir.Expr.static_getitem(lhs, i, None, wvf__edumu.loc)
        self.calltypes[zruki__uagmr] = None
        dbs__lvyi.append(ir.Assign(zruki__uagmr, max__lzs, wvf__edumu.loc))
        self._define(equiv_set, max__lzs, types.intp, zruki__uagmr)
        ywa__knc.append(max__lzs)
    lnci__wxa = tuple(ywa__knc)
    return numba.parfors.array_analysis.ArrayAnalysis.AnalyzeResult(shape=
        lnci__wxa, pre=[ufo__nqf] + dbs__lvyi)


numba.parfors.array_analysis.ArrayAnalysis._analyze_op_pair_first = (
    _analyze_op_pair_first)
