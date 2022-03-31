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
        aroi__zfywn = f'bodo.utils.conversion.coerce_to_array({col_names})'
        return (
            f'bodo.hiframes.pd_index_ext.init_binary_str_index({aroi__zfywn})\n'
            )
    elif all(isinstance(a, (int, float)) for a in col_names):
        arr = f'bodo.utils.conversion.coerce_to_array({col_names})'
        return f'bodo.hiframes.pd_index_ext.init_numeric_index({arr})\n'
    else:
        return f'bodo.hiframes.pd_index_ext.init_heter_index({col_names})\n'


@overload_attribute(DataFrameType, 'columns', inline='always')
def overload_dataframe_columns(df):
    usel__pbrbf = 'def impl(df):\n'
    if df.has_runtime_cols:
        usel__pbrbf += (
            '  return bodo.hiframes.pd_dataframe_ext.get_dataframe_column_names(df)\n'
            )
    else:
        vgu__hyqn = (bodo.hiframes.dataframe_impl.
            generate_col_to_index_func_text(df.columns))
        usel__pbrbf += f'  return {vgu__hyqn}'
    ueciy__bmwpg = {}
    exec(usel__pbrbf, {'bodo': bodo}, ueciy__bmwpg)
    impl = ueciy__bmwpg['impl']
    return impl


@overload_attribute(DataFrameType, 'values')
def overload_dataframe_values(df):
    check_runtime_cols_unsupported(df, 'DataFrame.values')
    if not is_df_values_numpy_supported_dftyp(df):
        raise_bodo_error(
            'DataFrame.values: only supported for dataframes containing numeric values'
            )
    becjd__uza = len(df.columns)
    ayi__syg = set(i for i in range(becjd__uza) if isinstance(df.data[i],
        IntegerArrayType))
    data_args = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(i, '.astype(float)' if i in ayi__syg else '') for i in range
        (becjd__uza))
    usel__pbrbf = 'def f(df):\n'.format()
    usel__pbrbf += '    return np.stack(({},), 1)\n'.format(data_args)
    ueciy__bmwpg = {}
    exec(usel__pbrbf, {'bodo': bodo, 'np': np}, ueciy__bmwpg)
    xvpg__nuusw = ueciy__bmwpg['f']
    return xvpg__nuusw


@overload_method(DataFrameType, 'to_numpy', inline='always', no_unliteral=True)
def overload_dataframe_to_numpy(df, dtype=None, copy=False, na_value=_no_input
    ):
    check_runtime_cols_unsupported(df, 'DataFrame.to_numpy()')
    if not is_df_values_numpy_supported_dftyp(df):
        raise_bodo_error(
            'DataFrame.to_numpy(): only supported for dataframes containing numeric values'
            )
    ynck__rzkua = {'dtype': dtype, 'na_value': na_value}
    rbimy__wpi = {'dtype': None, 'na_value': _no_input}
    check_unsupported_args('DataFrame.to_numpy', ynck__rzkua, rbimy__wpi,
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
            vzne__iwtw = bodo.hiframes.table.compute_num_runtime_columns(t)
            return vzne__iwtw * len(t)
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
            vzne__iwtw = bodo.hiframes.table.compute_num_runtime_columns(t)
            return len(t), vzne__iwtw
        return impl
    ncols = len(df.columns)
    return lambda df: (len(df), types.int64(ncols))


@overload_attribute(DataFrameType, 'dtypes')
def overload_dataframe_dtypes(df):
    check_runtime_cols_unsupported(df, 'DataFrame.dtypes')
    usel__pbrbf = 'def impl(df):\n'
    data = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).dtype\n'
         for i in range(len(df.columns)))
    phub__yfpaq = ',' if len(df.columns) == 1 else ''
    index = f'bodo.hiframes.pd_index_ext.init_heter_index({df.columns})'
    usel__pbrbf += f"""  return bodo.hiframes.pd_series_ext.init_series(({data}{phub__yfpaq}), {index}, None)
"""
    ueciy__bmwpg = {}
    exec(usel__pbrbf, {'bodo': bodo}, ueciy__bmwpg)
    impl = ueciy__bmwpg['impl']
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
    ynck__rzkua = {'copy': copy, 'errors': errors}
    rbimy__wpi = {'copy': True, 'errors': 'raise'}
    check_unsupported_args('df.astype', ynck__rzkua, rbimy__wpi,
        package_name='pandas', module_name='DataFrame')
    if dtype == types.unicode_type:
        raise_bodo_error(
            "DataFrame.astype(): 'dtype' when passed as string must be a constant value"
            )
    extra_globals = None
    if _bodo_object_typeref is not None:
        assert isinstance(_bodo_object_typeref, types.TypeRef
            ), 'Bodo schema used in DataFrame.astype should be a TypeRef'
        hzic__ygobz = _bodo_object_typeref.instance_type
        assert isinstance(hzic__ygobz, DataFrameType
            ), 'Bodo schema used in DataFrame.astype is only supported for DataFrame schemas'
        extra_globals = {}
        qrkoz__cwo = {}
        for i, name in enumerate(hzic__ygobz.columns):
            arr_typ = hzic__ygobz.data[i]
            if isinstance(arr_typ, IntegerArrayType):
                rfyvf__aue = bodo.libs.int_arr_ext.IntDtype(arr_typ.dtype)
            elif arr_typ == boolean_array:
                rfyvf__aue = boolean_dtype
            else:
                rfyvf__aue = arr_typ.dtype
            extra_globals[f'_bodo_schema{i}'] = rfyvf__aue
            qrkoz__cwo[name] = f'_bodo_schema{i}'
        data_args = ', '.join(
            f'bodo.utils.conversion.fix_arr_dtype(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), {qrkoz__cwo[gtcss__vpd]}, copy, nan_to_str=_bodo_nan_to_str, from_series=True)'
             if gtcss__vpd in qrkoz__cwo else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})' for
            i, gtcss__vpd in enumerate(df.columns))
    elif is_overload_constant_dict(dtype) or is_overload_constant_series(dtype
        ):
        gmld__crum = get_overload_constant_dict(dtype
            ) if is_overload_constant_dict(dtype) else dict(
            get_overload_constant_series(dtype))
        data_args = ', '.join(
            f'bodo.utils.conversion.fix_arr_dtype(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), {_get_dtype_str(gmld__crum[gtcss__vpd])}, copy, nan_to_str=_bodo_nan_to_str, from_series=True)'
             if gtcss__vpd in gmld__crum else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})' for
            i, gtcss__vpd in enumerate(df.columns))
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
    poz__fjmun = []
    for i in range(len(df.columns)):
        arr = f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})'
        if is_overload_true(deep):
            poz__fjmun.append(arr + '.copy()')
        elif is_overload_false(deep):
            poz__fjmun.append(arr)
        else:
            poz__fjmun.append(f'{arr}.copy() if deep else {arr}')
    header = 'def impl(df, deep=True):\n'
    return _gen_init_df(header, df.columns, ', '.join(poz__fjmun))


@overload_method(DataFrameType, 'rename', inline='always', no_unliteral=True)
def overload_dataframe_rename(df, mapper=None, index=None, columns=None,
    axis=None, copy=True, inplace=False, level=None, errors='ignore',
    _bodo_transformed=False):
    check_runtime_cols_unsupported(df, 'DataFrame.rename()')
    handle_inplace_df_type_change(inplace, _bodo_transformed, 'rename')
    ynck__rzkua = {'index': index, 'level': level, 'errors': errors}
    rbimy__wpi = {'index': None, 'level': None, 'errors': 'ignore'}
    check_unsupported_args('DataFrame.rename', ynck__rzkua, rbimy__wpi,
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
        hkk__qfg = get_overload_constant_dict(mapper)
    elif not is_overload_none(columns):
        if not is_overload_none(axis):
            raise BodoError(
                "DataFrame.rename(): Cannot specify both 'axis' and 'columns'")
        if not is_overload_constant_dict(columns):
            raise_bodo_error(
                "'columns' argument to DataFrame.rename() should be a constant dictionary"
                )
        hkk__qfg = get_overload_constant_dict(columns)
    else:
        raise_bodo_error(
            "DataFrame.rename(): must pass columns either via 'mapper' and 'axis'=1 or 'columns'"
            )
    dgw__zpqk = [hkk__qfg.get(df.columns[i], df.columns[i]) for i in range(
        len(df.columns))]
    poz__fjmun = []
    for i in range(len(df.columns)):
        arr = f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})'
        if is_overload_true(copy):
            poz__fjmun.append(arr + '.copy()')
        elif is_overload_false(copy):
            poz__fjmun.append(arr)
        else:
            poz__fjmun.append(f'{arr}.copy() if copy else {arr}')
    header = """def impl(df, mapper=None, index=None, columns=None, axis=None, copy=True, inplace=False, level=None, errors='ignore', _bodo_transformed=False):
"""
    return _gen_init_df(header, dgw__zpqk, ', '.join(poz__fjmun))


@overload_method(DataFrameType, 'filter', no_unliteral=True)
def overload_dataframe_filter(df, items=None, like=None, regex=None, axis=None
    ):
    check_runtime_cols_unsupported(df, 'DataFrame.filter()')
    hpf__rfco = not is_overload_none(items)
    rdmh__jthg = not is_overload_none(like)
    vwwy__hwnh = not is_overload_none(regex)
    hlxlt__zginl = hpf__rfco ^ rdmh__jthg ^ vwwy__hwnh
    yvqf__iohx = not (hpf__rfco or rdmh__jthg or vwwy__hwnh)
    if yvqf__iohx:
        raise BodoError(
            'DataFrame.filter(): one of keyword arguments `items`, `like`, and `regex` must be supplied'
            )
    if not hlxlt__zginl:
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
        htx__bglzz = 0 if axis == 'index' else 1
    elif is_overload_constant_int(axis):
        axis = get_overload_const_int(axis)
        if axis not in {0, 1}:
            raise_bodo_error(
                'DataFrame.filter(): keyword arguments `axis` must be either 0 or 1 if integer'
                )
        htx__bglzz = axis
    else:
        raise_bodo_error(
            'DataFrame.filter(): keyword arguments `axis` must be constant string or integer'
            )
    assert htx__bglzz in {0, 1}
    usel__pbrbf = (
        'def impl(df, items=None, like=None, regex=None, axis=None):\n')
    if htx__bglzz == 0:
        raise BodoError(
            'DataFrame.filter(): filtering based on index is not supported.')
    if htx__bglzz == 1:
        orzr__ccods = []
        dwopi__dxio = []
        bhd__umc = []
        if hpf__rfco:
            if is_overload_constant_list(items):
                jnmln__azwi = get_overload_const_list(items)
            else:
                raise BodoError(
                    "Dataframe.filter(): argument 'items' must be a list of constant strings."
                    )
        if rdmh__jthg:
            if is_overload_constant_str(like):
                qsiv__omqn = get_overload_const_str(like)
            else:
                raise BodoError(
                    "Dataframe.filter(): argument 'like' must be a constant string."
                    )
        if vwwy__hwnh:
            if is_overload_constant_str(regex):
                ibsgu__wuyw = get_overload_const_str(regex)
                iac__rpgva = re.compile(ibsgu__wuyw)
            else:
                raise BodoError(
                    "Dataframe.filter(): argument 'regex' must be a constant string."
                    )
        for i, gtcss__vpd in enumerate(df.columns):
            if not is_overload_none(items
                ) and gtcss__vpd in jnmln__azwi or not is_overload_none(like
                ) and qsiv__omqn in str(gtcss__vpd) or not is_overload_none(
                regex) and iac__rpgva.search(str(gtcss__vpd)):
                dwopi__dxio.append(gtcss__vpd)
                bhd__umc.append(i)
        for i in bhd__umc:
            rnqoj__azt = f'data_{i}'
            orzr__ccods.append(rnqoj__azt)
            usel__pbrbf += f"""  {rnqoj__azt} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})
"""
        data_args = ', '.join(orzr__ccods)
        return _gen_init_df(usel__pbrbf, dwopi__dxio, data_args)


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
    nmv__zzzw = is_overload_none(include)
    rqz__ibqt = is_overload_none(exclude)
    qaku__xue = 'DataFrame.select_dtypes'
    if nmv__zzzw and rqz__ibqt:
        raise_bodo_error(
            'DataFrame.select_dtypes() At least one of include or exclude must not be none'
            )

    def is_legal_input(elem):
        return is_overload_constant_str(elem) or isinstance(elem, types.
            DTypeSpec) or isinstance(elem, types.Function)
    if not nmv__zzzw:
        if is_overload_constant_list(include):
            include = get_overload_const_list(include)
            iew__zis = [dtype_to_array_type(parse_dtype(elem, qaku__xue)) for
                elem in include]
        elif is_legal_input(include):
            iew__zis = [dtype_to_array_type(parse_dtype(include, qaku__xue))]
        else:
            raise_bodo_error(
                'DataFrame.select_dtypes() only supports constant strings or types as arguments'
                )
        iew__zis = get_nullable_and_non_nullable_types(iew__zis)
        ficj__sye = tuple(gtcss__vpd for i, gtcss__vpd in enumerate(df.
            columns) if df.data[i] in iew__zis)
    else:
        ficj__sye = df.columns
    if not rqz__ibqt:
        if is_overload_constant_list(exclude):
            exclude = get_overload_const_list(exclude)
            kca__bquht = [dtype_to_array_type(parse_dtype(elem, qaku__xue)) for
                elem in exclude]
        elif is_legal_input(exclude):
            kca__bquht = [dtype_to_array_type(parse_dtype(exclude, qaku__xue))]
        else:
            raise_bodo_error(
                'DataFrame.select_dtypes() only supports constant strings or types as arguments'
                )
        kca__bquht = get_nullable_and_non_nullable_types(kca__bquht)
        ficj__sye = tuple(gtcss__vpd for gtcss__vpd in ficj__sye if df.data
            [df.columns.index(gtcss__vpd)] not in kca__bquht)
    data_args = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(gtcss__vpd)})'
         for gtcss__vpd in ficj__sye)
    header = 'def impl(df, include=None, exclude=None):\n'
    return _gen_init_df(header, ficj__sye, data_args)


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
    wbl__cffl = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if not isinstance(df.index, DatetimeIndexType):
        raise BodoError(
            'DataFrame.first(): only supports a DatetimeIndex index')
    if types.unliteral(offset) not in wbl__cffl:
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
    wbl__cffl = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if not isinstance(df.index, DatetimeIndexType):
        raise BodoError('DataFrame.last(): only supports a DatetimeIndex index'
            )
    if types.unliteral(offset) not in wbl__cffl:
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
    usel__pbrbf = 'def impl(df, values):\n'
    kzrxa__yye = {}
    xxpwn__vqgdg = False
    if isinstance(values, DataFrameType):
        xxpwn__vqgdg = True
        for i, gtcss__vpd in enumerate(df.columns):
            if gtcss__vpd in values.columns:
                xmvtn__aesp = 'val{}'.format(i)
                usel__pbrbf += (
                    """  {} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(values, {})
"""
                    .format(xmvtn__aesp, values.columns.index(gtcss__vpd)))
                kzrxa__yye[gtcss__vpd] = xmvtn__aesp
    elif is_iterable_type(values) and not isinstance(values, SeriesType):
        kzrxa__yye = {gtcss__vpd: 'values' for gtcss__vpd in df.columns}
    else:
        raise_bodo_error(f'pd.isin(): not supported for type {values}')
    data = []
    for i in range(len(df.columns)):
        xmvtn__aesp = 'data{}'.format(i)
        usel__pbrbf += (
            '  {} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})\n'
            .format(xmvtn__aesp, i))
        data.append(xmvtn__aesp)
    rjph__lgeml = ['out{}'.format(i) for i in range(len(df.columns))]
    fwrrb__chte = """
  numba.parfors.parfor.init_prange()
  n = len({0})
  m = len({1})
  {2} = np.empty(n, np.bool_)
  for i in numba.parfors.parfor.internal_prange(n):
    {2}[i] = {0}[i] == {1}[i] if i < m else False
"""
    vvzxm__uivj = """
  numba.parfors.parfor.init_prange()
  n = len({0})
  {2} = np.empty(n, np.bool_)
  for i in numba.parfors.parfor.internal_prange(n):
    {2}[i] = {0}[i] in {1}
"""
    djc__ccn = '  {} = np.zeros(len(df), np.bool_)\n'
    for i, (cname, rddyk__uhno) in enumerate(zip(df.columns, data)):
        if cname in kzrxa__yye:
            zyw__nkgeg = kzrxa__yye[cname]
            if xxpwn__vqgdg:
                usel__pbrbf += fwrrb__chte.format(rddyk__uhno, zyw__nkgeg,
                    rjph__lgeml[i])
            else:
                usel__pbrbf += vvzxm__uivj.format(rddyk__uhno, zyw__nkgeg,
                    rjph__lgeml[i])
        else:
            usel__pbrbf += djc__ccn.format(rjph__lgeml[i])
    return _gen_init_df(usel__pbrbf, df.columns, ','.join(rjph__lgeml))


@overload_method(DataFrameType, 'abs', inline='always', no_unliteral=True)
def overload_dataframe_abs(df):
    check_runtime_cols_unsupported(df, 'DataFrame.abs()')
    for arr_typ in df.data:
        if not (isinstance(arr_typ.dtype, types.Number) or arr_typ.dtype ==
            bodo.timedelta64ns):
            raise_bodo_error(
                f'DataFrame.abs(): Only supported for numeric and Timedelta. Encountered array with dtype {arr_typ.dtype}'
                )
    becjd__uza = len(df.columns)
    data_args = ', '.join(
        'np.abs(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}))'
        .format(i) for i in range(becjd__uza))
    header = 'def impl(df):\n'
    return _gen_init_df(header, df.columns, data_args)


def overload_dataframe_corr(df, method='pearson', min_periods=1):
    lalb__hjudb = [gtcss__vpd for gtcss__vpd, spgux__zcyx in zip(df.columns,
        df.data) if bodo.utils.typing._is_pandas_numeric_dtype(spgux__zcyx.
        dtype)]
    assert len(lalb__hjudb) != 0
    ggrbb__bate = ''
    if not any(spgux__zcyx == types.float64 for spgux__zcyx in df.data):
        ggrbb__bate = '.astype(np.float64)'
    ugdo__ecm = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(df.columns.index(gtcss__vpd), '.astype(np.float64)' if 
        isinstance(df.data[df.columns.index(gtcss__vpd)], IntegerArrayType) or
        df.data[df.columns.index(gtcss__vpd)] == boolean_array else '') for
        gtcss__vpd in lalb__hjudb)
    ens__krrg = 'np.stack(({},), 1){}'.format(ugdo__ecm, ggrbb__bate)
    data_args = ', '.join('res[:,{}]'.format(i) for i in range(len(
        lalb__hjudb)))
    index = f'{generate_col_to_index_func_text(lalb__hjudb)}\n'
    header = "def impl(df, method='pearson', min_periods=1):\n"
    header += '  mat = {}\n'.format(ens__krrg)
    header += '  res = bodo.libs.array_kernels.nancorr(mat, 0, min_periods)\n'
    return _gen_init_df(header, lalb__hjudb, data_args, index)


@lower_builtin('df.corr', DataFrameType, types.VarArg(types.Any))
def dataframe_corr_lower(context, builder, sig, args):
    impl = overload_dataframe_corr(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


@overload_method(DataFrameType, 'cov', inline='always', no_unliteral=True)
def overload_dataframe_cov(df, min_periods=None, ddof=1):
    check_runtime_cols_unsupported(df, 'DataFrame.cov()')
    bfo__gopwz = dict(ddof=ddof)
    anw__xjql = dict(ddof=1)
    check_unsupported_args('DataFrame.cov', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    dzpb__qdfjv = '1' if is_overload_none(min_periods) else 'min_periods'
    lalb__hjudb = [gtcss__vpd for gtcss__vpd, spgux__zcyx in zip(df.columns,
        df.data) if bodo.utils.typing._is_pandas_numeric_dtype(spgux__zcyx.
        dtype)]
    if len(lalb__hjudb) == 0:
        raise_bodo_error('DataFrame.cov(): requires non-empty dataframe')
    ggrbb__bate = ''
    if not any(spgux__zcyx == types.float64 for spgux__zcyx in df.data):
        ggrbb__bate = '.astype(np.float64)'
    ugdo__ecm = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(df.columns.index(gtcss__vpd), '.astype(np.float64)' if 
        isinstance(df.data[df.columns.index(gtcss__vpd)], IntegerArrayType) or
        df.data[df.columns.index(gtcss__vpd)] == boolean_array else '') for
        gtcss__vpd in lalb__hjudb)
    ens__krrg = 'np.stack(({},), 1){}'.format(ugdo__ecm, ggrbb__bate)
    data_args = ', '.join('res[:,{}]'.format(i) for i in range(len(
        lalb__hjudb)))
    index = f'pd.Index({lalb__hjudb})\n'
    header = 'def impl(df, min_periods=None, ddof=1):\n'
    header += '  mat = {}\n'.format(ens__krrg)
    header += '  res = bodo.libs.array_kernels.nancorr(mat, 1, {})\n'.format(
        dzpb__qdfjv)
    return _gen_init_df(header, lalb__hjudb, data_args, index)


@overload_method(DataFrameType, 'count', inline='always', no_unliteral=True)
def overload_dataframe_count(df, axis=0, level=None, numeric_only=False):
    check_runtime_cols_unsupported(df, 'DataFrame.count()')
    bfo__gopwz = dict(axis=axis, level=level, numeric_only=numeric_only)
    anw__xjql = dict(axis=0, level=None, numeric_only=False)
    check_unsupported_args('DataFrame.count', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'bodo.libs.array_ops.array_op_count(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}))'
         for i in range(len(df.columns)))
    usel__pbrbf = 'def impl(df, axis=0, level=None, numeric_only=False):\n'
    usel__pbrbf += '  data = np.array([{}])\n'.format(data_args)
    vgu__hyqn = bodo.hiframes.dataframe_impl.generate_col_to_index_func_text(df
        .columns)
    usel__pbrbf += (
        f'  return bodo.hiframes.pd_series_ext.init_series(data, {vgu__hyqn})\n'
        )
    ueciy__bmwpg = {}
    exec(usel__pbrbf, {'bodo': bodo, 'np': np}, ueciy__bmwpg)
    impl = ueciy__bmwpg['impl']
    return impl


@overload_method(DataFrameType, 'nunique', inline='always', no_unliteral=True)
def overload_dataframe_nunique(df, axis=0, dropna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.unique()')
    bfo__gopwz = dict(axis=axis)
    anw__xjql = dict(axis=0)
    if not is_overload_bool(dropna):
        raise BodoError('DataFrame.nunique: dropna must be a boolean value')
    check_unsupported_args('DataFrame.nunique', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'bodo.libs.array_kernels.nunique(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), dropna)'
         for i in range(len(df.columns)))
    usel__pbrbf = 'def impl(df, axis=0, dropna=True):\n'
    usel__pbrbf += '  data = np.asarray(({},))\n'.format(data_args)
    vgu__hyqn = bodo.hiframes.dataframe_impl.generate_col_to_index_func_text(df
        .columns)
    usel__pbrbf += (
        f'  return bodo.hiframes.pd_series_ext.init_series(data, {vgu__hyqn})\n'
        )
    ueciy__bmwpg = {}
    exec(usel__pbrbf, {'bodo': bodo, 'np': np}, ueciy__bmwpg)
    impl = ueciy__bmwpg['impl']
    return impl


@overload_method(DataFrameType, 'prod', inline='always', no_unliteral=True)
@overload_method(DataFrameType, 'product', inline='always', no_unliteral=True)
def overload_dataframe_prod(df, axis=None, skipna=None, level=None,
    numeric_only=None, min_count=0):
    check_runtime_cols_unsupported(df, 'DataFrame.prod()')
    bfo__gopwz = dict(skipna=skipna, level=level, numeric_only=numeric_only,
        min_count=min_count)
    anw__xjql = dict(skipna=None, level=None, numeric_only=None, min_count=0)
    check_unsupported_args('DataFrame.prod', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'prod', axis=axis)


@overload_method(DataFrameType, 'sum', inline='always', no_unliteral=True)
def overload_dataframe_sum(df, axis=None, skipna=None, level=None,
    numeric_only=None, min_count=0):
    check_runtime_cols_unsupported(df, 'DataFrame.sum()')
    bfo__gopwz = dict(skipna=skipna, level=level, numeric_only=numeric_only,
        min_count=min_count)
    anw__xjql = dict(skipna=None, level=None, numeric_only=None, min_count=0)
    check_unsupported_args('DataFrame.sum', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'sum', axis=axis)


@overload_method(DataFrameType, 'max', inline='always', no_unliteral=True)
def overload_dataframe_max(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.max()')
    bfo__gopwz = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    anw__xjql = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.max', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'max', axis=axis)


@overload_method(DataFrameType, 'min', inline='always', no_unliteral=True)
def overload_dataframe_min(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.min()')
    bfo__gopwz = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    anw__xjql = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.min', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'min', axis=axis)


@overload_method(DataFrameType, 'mean', inline='always', no_unliteral=True)
def overload_dataframe_mean(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.mean()')
    bfo__gopwz = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    anw__xjql = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.mean', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'mean', axis=axis)


@overload_method(DataFrameType, 'var', inline='always', no_unliteral=True)
def overload_dataframe_var(df, axis=None, skipna=None, level=None, ddof=1,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.var()')
    bfo__gopwz = dict(skipna=skipna, level=level, ddof=ddof, numeric_only=
        numeric_only)
    anw__xjql = dict(skipna=None, level=None, ddof=1, numeric_only=None)
    check_unsupported_args('DataFrame.var', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'var', axis=axis)


@overload_method(DataFrameType, 'std', inline='always', no_unliteral=True)
def overload_dataframe_std(df, axis=None, skipna=None, level=None, ddof=1,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.std()')
    bfo__gopwz = dict(skipna=skipna, level=level, ddof=ddof, numeric_only=
        numeric_only)
    anw__xjql = dict(skipna=None, level=None, ddof=1, numeric_only=None)
    check_unsupported_args('DataFrame.std', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'std', axis=axis)


@overload_method(DataFrameType, 'median', inline='always', no_unliteral=True)
def overload_dataframe_median(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.median()')
    bfo__gopwz = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    anw__xjql = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.median', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'median', axis=axis)


@overload_method(DataFrameType, 'quantile', inline='always', no_unliteral=True)
def overload_dataframe_quantile(df, q=0.5, axis=0, numeric_only=True,
    interpolation='linear'):
    check_runtime_cols_unsupported(df, 'DataFrame.quantile()')
    bfo__gopwz = dict(numeric_only=numeric_only, interpolation=interpolation)
    anw__xjql = dict(numeric_only=True, interpolation='linear')
    check_unsupported_args('DataFrame.quantile', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    return _gen_reduce_impl(df, 'quantile', 'q', axis=axis)


@overload_method(DataFrameType, 'idxmax', inline='always', no_unliteral=True)
def overload_dataframe_idxmax(df, axis=0, skipna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.idxmax()')
    bfo__gopwz = dict(axis=axis, skipna=skipna)
    anw__xjql = dict(axis=0, skipna=True)
    check_unsupported_args('DataFrame.idxmax', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    for orgrp__zkp in df.data:
        if not (bodo.utils.utils.is_np_array_typ(orgrp__zkp) and (
            orgrp__zkp.dtype in [bodo.datetime64ns, bodo.timedelta64ns] or
            isinstance(orgrp__zkp.dtype, (types.Number, types.Boolean))) or
            isinstance(orgrp__zkp, (bodo.IntegerArrayType, bodo.
            CategoricalArrayType)) or orgrp__zkp in [bodo.boolean_array,
            bodo.datetime_date_array_type]):
            raise BodoError(
                f'DataFrame.idxmax() only supported for numeric column types. Column type: {orgrp__zkp} not supported.'
                )
        if isinstance(orgrp__zkp, bodo.CategoricalArrayType
            ) and not orgrp__zkp.dtype.ordered:
            raise BodoError(
                'DataFrame.idxmax(): categorical columns must be ordered')
    return _gen_reduce_impl(df, 'idxmax', axis=axis)


@overload_method(DataFrameType, 'idxmin', inline='always', no_unliteral=True)
def overload_dataframe_idxmin(df, axis=0, skipna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.idxmin()')
    bfo__gopwz = dict(axis=axis, skipna=skipna)
    anw__xjql = dict(axis=0, skipna=True)
    check_unsupported_args('DataFrame.idxmin', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    for orgrp__zkp in df.data:
        if not (bodo.utils.utils.is_np_array_typ(orgrp__zkp) and (
            orgrp__zkp.dtype in [bodo.datetime64ns, bodo.timedelta64ns] or
            isinstance(orgrp__zkp.dtype, (types.Number, types.Boolean))) or
            isinstance(orgrp__zkp, (bodo.IntegerArrayType, bodo.
            CategoricalArrayType)) or orgrp__zkp in [bodo.boolean_array,
            bodo.datetime_date_array_type]):
            raise BodoError(
                f'DataFrame.idxmin() only supported for numeric column types. Column type: {orgrp__zkp} not supported.'
                )
        if isinstance(orgrp__zkp, bodo.CategoricalArrayType
            ) and not orgrp__zkp.dtype.ordered:
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
        lalb__hjudb = tuple(gtcss__vpd for gtcss__vpd, spgux__zcyx in zip(
            df.columns, df.data) if bodo.utils.typing.
            _is_pandas_numeric_dtype(spgux__zcyx.dtype))
        out_colnames = lalb__hjudb
    assert len(out_colnames) != 0
    try:
        if func_name in ('idxmax', 'idxmin') and axis == 0:
            comm_dtype = None
        else:
            mnyq__kiuqb = [numba.np.numpy_support.as_dtype(df.data[df.
                columns.index(gtcss__vpd)].dtype) for gtcss__vpd in
                out_colnames]
            comm_dtype = numba.np.numpy_support.from_dtype(np.
                find_common_type(mnyq__kiuqb, []))
    except NotImplementedError as mvrtq__ghku:
        raise BodoError(
            f'Dataframe.{func_name}() with column types: {df.data} could not be merged to a common type.'
            )
    vxh__sjpk = ''
    if func_name in ('sum', 'prod'):
        vxh__sjpk = ', min_count=0'
    ddof = ''
    if func_name in ('var', 'std'):
        ddof = 'ddof=1, '
    usel__pbrbf = (
        'def impl(df, axis=None, skipna=None, level=None,{} numeric_only=None{}):\n'
        .format(ddof, vxh__sjpk))
    if func_name == 'quantile':
        usel__pbrbf = (
            "def impl(df, q=0.5, axis=0, numeric_only=True, interpolation='linear'):\n"
            )
    if func_name in ('idxmax', 'idxmin'):
        usel__pbrbf = 'def impl(df, axis=0, skipna=True):\n'
    if axis == 0:
        usel__pbrbf += _gen_reduce_impl_axis0(df, func_name, out_colnames,
            comm_dtype, args)
    else:
        usel__pbrbf += _gen_reduce_impl_axis1(func_name, out_colnames,
            comm_dtype, df)
    ueciy__bmwpg = {}
    exec(usel__pbrbf, {'bodo': bodo, 'np': np, 'pd': pd, 'numba': numba},
        ueciy__bmwpg)
    impl = ueciy__bmwpg['impl']
    return impl


def _gen_reduce_impl_axis0(df, func_name, out_colnames, comm_dtype, args):
    yhnop__lzwhe = ''
    if func_name in ('min', 'max'):
        yhnop__lzwhe = ', dtype=np.{}'.format(comm_dtype)
    if comm_dtype == types.float32 and func_name in ('sum', 'prod', 'mean',
        'var', 'std', 'median'):
        yhnop__lzwhe = ', dtype=np.float32'
    xucr__mhd = f'bodo.libs.array_ops.array_op_{func_name}'
    hcrec__xiy = ''
    if func_name in ['sum', 'prod']:
        hcrec__xiy = 'True, min_count'
    elif func_name in ['idxmax', 'idxmin']:
        hcrec__xiy = 'index'
    elif func_name == 'quantile':
        hcrec__xiy = 'q'
    elif func_name in ['std', 'var']:
        hcrec__xiy = 'True, ddof'
    elif func_name == 'median':
        hcrec__xiy = 'True'
    data_args = ', '.join(
        f'{xucr__mhd}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(gtcss__vpd)}), {hcrec__xiy})'
         for gtcss__vpd in out_colnames)
    usel__pbrbf = ''
    if func_name in ('idxmax', 'idxmin'):
        usel__pbrbf += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
            )
        usel__pbrbf += (
            '  data = bodo.utils.conversion.coerce_to_array(({},))\n'.
            format(data_args))
    else:
        usel__pbrbf += '  data = np.asarray(({},){})\n'.format(data_args,
            yhnop__lzwhe)
    usel__pbrbf += f"""  return bodo.hiframes.pd_series_ext.init_series(data, pd.Index({out_colnames}))
"""
    return usel__pbrbf


def _gen_reduce_impl_axis1(func_name, out_colnames, comm_dtype, df_type):
    osrw__fnb = [df_type.columns.index(gtcss__vpd) for gtcss__vpd in
        out_colnames]
    index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
    data_args = '\n    '.join(
        'arr_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})'
        .format(i) for i in osrw__fnb)
    aqke__blvai = '\n        '.join(f'row[{i}] = arr_{osrw__fnb[i]}[i]' for
        i in range(len(out_colnames)))
    assert len(data_args) > 0, f'empty dataframe in DataFrame.{func_name}()'
    aoz__nvz = f'len(arr_{osrw__fnb[0]})'
    zstj__vchm = {'max': 'np.nanmax', 'min': 'np.nanmin', 'sum':
        'np.nansum', 'prod': 'np.nanprod', 'mean': 'np.nanmean', 'median':
        'np.nanmedian', 'var': 'bodo.utils.utils.nanvar_ddof1', 'std':
        'bodo.utils.utils.nanstd_ddof1'}
    if func_name in zstj__vchm:
        tcs__stw = zstj__vchm[func_name]
        yrd__ahva = 'float64' if func_name in ['mean', 'median', 'std', 'var'
            ] else comm_dtype
        usel__pbrbf = f"""
    {data_args}
    numba.parfors.parfor.init_prange()
    n = {aoz__nvz}
    row = np.empty({len(out_colnames)}, np.{comm_dtype})
    A = np.empty(n, np.{yrd__ahva})
    for i in numba.parfors.parfor.internal_prange(n):
        {aqke__blvai}
        A[i] = {tcs__stw}(row)
    return bodo.hiframes.pd_series_ext.init_series(A, {index})
"""
        return usel__pbrbf
    else:
        raise BodoError(f'DataFrame.{func_name}(): Not supported for axis=1')


@overload_method(DataFrameType, 'pct_change', inline='always', no_unliteral
    =True)
def overload_dataframe_pct_change(df, periods=1, fill_method='pad', limit=
    None, freq=None):
    check_runtime_cols_unsupported(df, 'DataFrame.pct_change()')
    bfo__gopwz = dict(fill_method=fill_method, limit=limit, freq=freq)
    anw__xjql = dict(fill_method='pad', limit=None, freq=None)
    check_unsupported_args('DataFrame.pct_change', bfo__gopwz, anw__xjql,
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
    bfo__gopwz = dict(axis=axis, skipna=skipna)
    anw__xjql = dict(axis=None, skipna=True)
    check_unsupported_args('DataFrame.cumprod', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).cumprod()'
         for i in range(len(df.columns)))
    header = 'def impl(df, axis=None, skipna=True):\n'
    return _gen_init_df(header, df.columns, data_args)


@overload_method(DataFrameType, 'cumsum', inline='always', no_unliteral=True)
def overload_dataframe_cumsum(df, axis=None, skipna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.cumsum()')
    bfo__gopwz = dict(skipna=skipna)
    anw__xjql = dict(skipna=True)
    check_unsupported_args('DataFrame.cumsum', bfo__gopwz, anw__xjql,
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
    bfo__gopwz = dict(percentiles=percentiles, include=include, exclude=
        exclude, datetime_is_numeric=datetime_is_numeric)
    anw__xjql = dict(percentiles=None, include=None, exclude=None,
        datetime_is_numeric=True)
    check_unsupported_args('DataFrame.describe', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    lalb__hjudb = [gtcss__vpd for gtcss__vpd, spgux__zcyx in zip(df.columns,
        df.data) if _is_describe_type(spgux__zcyx)]
    if len(lalb__hjudb) == 0:
        raise BodoError('df.describe() only supports numeric columns')
    apb__jze = sum(df.data[df.columns.index(gtcss__vpd)].dtype == bodo.
        datetime64ns for gtcss__vpd in lalb__hjudb)

    def _get_describe(col_ind):
        evkwz__bnf = df.data[col_ind].dtype == bodo.datetime64ns
        if apb__jze and apb__jze != len(lalb__hjudb):
            if evkwz__bnf:
                return f'des_{col_ind} + (np.nan,)'
            return (
                f'des_{col_ind}[:2] + des_{col_ind}[3:] + (des_{col_ind}[2],)')
        return f'des_{col_ind}'
    header = """def impl(df, percentiles=None, include=None, exclude=None, datetime_is_numeric=True):
"""
    for gtcss__vpd in lalb__hjudb:
        col_ind = df.columns.index(gtcss__vpd)
        header += f"""  des_{col_ind} = bodo.libs.array_ops.array_op_describe(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {col_ind}))
"""
    data_args = ', '.join(_get_describe(df.columns.index(gtcss__vpd)) for
        gtcss__vpd in lalb__hjudb)
    uwii__tkc = "['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']"
    if apb__jze == len(lalb__hjudb):
        uwii__tkc = "['count', 'mean', 'min', '25%', '50%', '75%', 'max']"
    elif apb__jze:
        uwii__tkc = (
            "['count', 'mean', 'min', '25%', '50%', '75%', 'max', 'std']")
    index = f'bodo.utils.conversion.convert_to_index({uwii__tkc})'
    return _gen_init_df(header, lalb__hjudb, data_args, index)


@overload_method(DataFrameType, 'take', inline='always', no_unliteral=True)
def overload_dataframe_take(df, indices, axis=0, convert=None, is_copy=True):
    check_runtime_cols_unsupported(df, 'DataFrame.take()')
    bfo__gopwz = dict(axis=axis, convert=convert, is_copy=is_copy)
    anw__xjql = dict(axis=0, convert=None, is_copy=True)
    check_unsupported_args('DataFrame.take', bfo__gopwz, anw__xjql,
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
    bfo__gopwz = dict(freq=freq, axis=axis, fill_value=fill_value)
    anw__xjql = dict(freq=None, axis=0, fill_value=None)
    check_unsupported_args('DataFrame.shift', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    for mhc__kvo in df.data:
        if not is_supported_shift_array_type(mhc__kvo):
            raise BodoError(
                f'Dataframe.shift() column input type {mhc__kvo.dtype} not supported yet.'
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
    bfo__gopwz = dict(axis=axis)
    anw__xjql = dict(axis=0)
    check_unsupported_args('DataFrame.diff', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    for mhc__kvo in df.data:
        if not (isinstance(mhc__kvo, types.Array) and (isinstance(mhc__kvo.
            dtype, types.Number) or mhc__kvo.dtype == bodo.datetime64ns)):
            raise BodoError(
                f'DataFrame.diff() column input type {mhc__kvo.dtype} not supported.'
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
    ocy__tent = (
        "DataFrame.explode(): 'column' must a constant label or list of labels"
        )
    if not is_literal_type(column):
        raise_bodo_error(ocy__tent)
    if is_overload_constant_list(column) or is_overload_constant_tuple(column):
        husqi__vsa = get_overload_const_list(column)
    else:
        husqi__vsa = [get_literal_value(column)]
    wpj__ctuzv = {gtcss__vpd: i for i, gtcss__vpd in enumerate(df.columns)}
    xhp__dhfi = [wpj__ctuzv[gtcss__vpd] for gtcss__vpd in husqi__vsa]
    for i in xhp__dhfi:
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
        f'  counts = bodo.libs.array_kernels.get_arr_lens(data{xhp__dhfi[0]})\n'
        )
    for i in range(n):
        if i in xhp__dhfi:
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
    ynck__rzkua = {'inplace': inplace, 'append': append, 'verify_integrity':
        verify_integrity}
    rbimy__wpi = {'inplace': False, 'append': False, 'verify_integrity': False}
    check_unsupported_args('DataFrame.set_index', ynck__rzkua, rbimy__wpi,
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
    columns = tuple(gtcss__vpd for gtcss__vpd in df.columns if gtcss__vpd !=
        col_name)
    index = (
        'bodo.utils.conversion.index_from_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}), {})'
        .format(col_ind, f"'{col_name}'" if isinstance(col_name, str) else
        col_name))
    return _gen_init_df(header, columns, data_args, index)


@overload_method(DataFrameType, 'query', no_unliteral=True)
def overload_dataframe_query(df, expr, inplace=False):
    check_runtime_cols_unsupported(df, 'DataFrame.query()')
    ynck__rzkua = {'inplace': inplace}
    rbimy__wpi = {'inplace': False}
    check_unsupported_args('query', ynck__rzkua, rbimy__wpi, package_name=
        'pandas', module_name='DataFrame')
    if not isinstance(expr, (types.StringLiteral, types.UnicodeType)):
        raise BodoError('query(): expr argument should be a string')

    def impl(df, expr, inplace=False):
        vgsv__rra = bodo.hiframes.pd_dataframe_ext.query_dummy(df, expr)
        return df[vgsv__rra]
    return impl


@overload_method(DataFrameType, 'duplicated', inline='always', no_unliteral
    =True)
def overload_dataframe_duplicated(df, subset=None, keep='first'):
    check_runtime_cols_unsupported(df, 'DataFrame.duplicated()')
    ynck__rzkua = {'subset': subset, 'keep': keep}
    rbimy__wpi = {'subset': None, 'keep': 'first'}
    check_unsupported_args('DataFrame.duplicated', ynck__rzkua, rbimy__wpi,
        package_name='pandas', module_name='DataFrame')
    becjd__uza = len(df.columns)
    usel__pbrbf = "def impl(df, subset=None, keep='first'):\n"
    for i in range(becjd__uza):
        usel__pbrbf += (
            '  data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})\n'
            .format(i))
    omr__ofaks = ', '.join(f'data_{i}' for i in range(becjd__uza))
    omr__ofaks += ',' if becjd__uza == 1 else ''
    usel__pbrbf += (
        f'  duplicated = bodo.libs.array_kernels.duplicated(({omr__ofaks}))\n')
    usel__pbrbf += (
        '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n')
    usel__pbrbf += (
        '  return bodo.hiframes.pd_series_ext.init_series(duplicated, index)\n'
        )
    ueciy__bmwpg = {}
    exec(usel__pbrbf, {'bodo': bodo}, ueciy__bmwpg)
    impl = ueciy__bmwpg['impl']
    return impl


@overload_method(DataFrameType, 'drop_duplicates', inline='always',
    no_unliteral=True)
def overload_dataframe_drop_duplicates(df, subset=None, keep='first',
    inplace=False, ignore_index=False):
    check_runtime_cols_unsupported(df, 'DataFrame.drop_duplicates()')
    ynck__rzkua = {'keep': keep, 'inplace': inplace, 'ignore_index':
        ignore_index}
    rbimy__wpi = {'keep': 'first', 'inplace': False, 'ignore_index': False}
    jonkx__qnj = []
    if is_overload_constant_list(subset):
        jonkx__qnj = get_overload_const_list(subset)
    elif is_overload_constant_str(subset):
        jonkx__qnj = [get_overload_const_str(subset)]
    elif is_overload_constant_int(subset):
        jonkx__qnj = [get_overload_const_int(subset)]
    elif not is_overload_none(subset):
        raise_bodo_error(
            'DataFrame.drop_duplicates(): subset must be a constant column name, constant list of column names or None'
            )
    mnvtu__csrg = []
    for col_name in jonkx__qnj:
        if col_name not in df.columns:
            raise BodoError(
                'DataFrame.drop_duplicates(): All subset columns must be found in the DataFrame.'
                 +
                f'Column {col_name} not found in DataFrame columns {df.columns}'
                )
        mnvtu__csrg.append(df.columns.index(col_name))
    check_unsupported_args('DataFrame.drop_duplicates', ynck__rzkua,
        rbimy__wpi, package_name='pandas', module_name='DataFrame')
    ftwv__umsv = []
    if mnvtu__csrg:
        for pshrm__pmg in mnvtu__csrg:
            if isinstance(df.data[pshrm__pmg], bodo.MapArrayType):
                ftwv__umsv.append(df.columns[pshrm__pmg])
    else:
        for i, col_name in enumerate(df.columns):
            if isinstance(df.data[i], bodo.MapArrayType):
                ftwv__umsv.append(col_name)
    if ftwv__umsv:
        raise BodoError(
            f'DataFrame.drop_duplicates(): Columns {ftwv__umsv} ' +
            f'have dictionary types which cannot be used to drop duplicates. '
             +
            "Please consider using the 'subset' argument to skip these columns."
            )
    becjd__uza = len(df.columns)
    fewet__rbd = ['data_{}'.format(i) for i in mnvtu__csrg]
    rxq__jizg = ['data_{}'.format(i) for i in range(becjd__uza) if i not in
        mnvtu__csrg]
    if fewet__rbd:
        kwpd__jvyw = len(fewet__rbd)
    else:
        kwpd__jvyw = becjd__uza
    rjx__myopx = ', '.join(fewet__rbd + rxq__jizg)
    data_args = ', '.join('data_{}'.format(i) for i in range(becjd__uza))
    usel__pbrbf = (
        "def impl(df, subset=None, keep='first', inplace=False, ignore_index=False):\n"
        )
    for i in range(becjd__uza):
        usel__pbrbf += (
            '  data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})\n'
            .format(i))
    index = (
        'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
        )
    usel__pbrbf += (
        """  ({0},), index_arr = bodo.libs.array_kernels.drop_duplicates(({0},), {1}, {2})
"""
        .format(rjx__myopx, index, kwpd__jvyw))
    usel__pbrbf += (
        '  index = bodo.utils.conversion.index_from_array(index_arr)\n')
    return _gen_init_df(usel__pbrbf, df.columns, data_args, 'index')


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
                qkgvo__gywb = {gtcss__vpd: i for i, gtcss__vpd in enumerate
                    (cond.columns)}

                def cond_str(i, gen_all_false):
                    if df.columns[i] in qkgvo__gywb:
                        return (
                            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(cond, {qkgvo__gywb[df.columns[i]]})'
                            )
                    else:
                        gen_all_false[0] = True
                        return 'all_false'
            elif isinstance(cond, types.Array):
                cond_str = lambda i, _: f'cond[:,{i}]'
        if not hasattr(other, 'ndim') or other.ndim == 1:
            ofj__rztnk = lambda i: 'other'
        elif other.ndim == 2:
            if isinstance(other, DataFrameType):
                other_map = {gtcss__vpd: i for i, gtcss__vpd in enumerate(
                    other.columns)}
                ofj__rztnk = (lambda i: 
                    f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(other, {other_map[df.columns[i]]})'
                     if df.columns[i] in other_map else 'None')
            elif isinstance(other, types.Array):
                ofj__rztnk = lambda i: f'other[:,{i}]'
        becjd__uza = len(df.columns)
        data_args = ', '.join(
            f'bodo.hiframes.series_impl.where_impl({cond_str(i, gen_all_false)}, bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), {ofj__rztnk(i)})'
             for i in range(becjd__uza))
        if gen_all_false[0]:
            header += '  all_false = np.zeros(len(df), dtype=bool)\n'
        return _gen_init_df(header, df.columns, data_args)
    return overload_dataframe_mask_where


def _install_dataframe_mask_where_overload():
    for func_name in ('mask', 'where'):
        omtj__odh = create_dataframe_mask_where_overload(func_name)
        overload_method(DataFrameType, func_name, no_unliteral=True)(omtj__odh)


_install_dataframe_mask_where_overload()


def _validate_arguments_mask_where(func_name, df, cond, other, inplace,
    axis, level, errors, try_cast):
    bfo__gopwz = dict(inplace=inplace, level=level, errors=errors, try_cast
        =try_cast)
    anw__xjql = dict(inplace=False, level=None, errors='raise', try_cast=False)
    check_unsupported_args(f'{func_name}', bfo__gopwz, anw__xjql,
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
    becjd__uza = len(df.columns)
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
        other_map = {gtcss__vpd: i for i, gtcss__vpd in enumerate(other.
            columns)}
        for i in range(becjd__uza):
            if df.columns[i] in other_map:
                bodo.hiframes.series_impl._validate_self_other_mask_where(
                    func_name, df.data[i], other.data[other_map[df.columns[i]]]
                    )
            else:
                bodo.hiframes.series_impl._validate_self_other_mask_where(
                    func_name, df.data[i], None, is_default=True)
    elif isinstance(other, SeriesType):
        for i in range(becjd__uza):
            bodo.hiframes.series_impl._validate_self_other_mask_where(func_name
                , df.data[i], other.data)
    else:
        for i in range(becjd__uza):
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
        lyc__dpayt = 'out_df_type'
    else:
        lyc__dpayt = gen_const_tup(columns)
    data_args = '({}{})'.format(data_args, ',' if data_args else '')
    usel__pbrbf = f"""{header}  return bodo.hiframes.pd_dataframe_ext.init_dataframe({data_args}, {index}, {lyc__dpayt})
"""
    ueciy__bmwpg = {}
    czjmf__ndr = {'bodo': bodo, 'np': np, 'pd': pd, 'numba': numba}
    czjmf__ndr.update(extra_globals)
    exec(usel__pbrbf, czjmf__ndr, ueciy__bmwpg)
    impl = ueciy__bmwpg['impl']
    return impl


def _get_binop_columns(lhs, rhs, is_inplace=False):
    if lhs.columns != rhs.columns:
        nble__zackx = pd.Index(lhs.columns)
        zsq__buj = pd.Index(rhs.columns)
        phb__dhds, swsgf__jynmr, upnpd__wvv = nble__zackx.join(zsq__buj,
            how='left' if is_inplace else 'outer', level=None,
            return_indexers=True)
        return tuple(phb__dhds), swsgf__jynmr, upnpd__wvv
    return lhs.columns, range(len(lhs.columns)), range(len(lhs.columns))


def create_binary_op_overload(op):

    def overload_dataframe_binary_op(lhs, rhs):
        kflmu__hgmnz = numba.core.utils.OPERATORS_TO_BUILTINS[op]
        cgic__iolyh = operator.eq, operator.ne
        check_runtime_cols_unsupported(lhs, kflmu__hgmnz)
        check_runtime_cols_unsupported(rhs, kflmu__hgmnz)
        if isinstance(lhs, DataFrameType):
            if isinstance(rhs, DataFrameType):
                phb__dhds, swsgf__jynmr, upnpd__wvv = _get_binop_columns(lhs,
                    rhs)
                data_args = ', '.join(
                    f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(lhs, {lhg__ruij}) {kflmu__hgmnz}bodo.hiframes.pd_dataframe_ext.get_dataframe_data(rhs, {roxqh__kxy})'
                     if lhg__ruij != -1 and roxqh__kxy != -1 else
                    f'bodo.libs.array_kernels.gen_na_array(len(lhs), float64_arr_type)'
                     for lhg__ruij, roxqh__kxy in zip(swsgf__jynmr, upnpd__wvv)
                    )
                header = 'def impl(lhs, rhs):\n'
                index = (
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(lhs)')
                return _gen_init_df(header, phb__dhds, data_args, index,
                    extra_globals={'float64_arr_type': types.Array(types.
                    float64, 1, 'C')})
            pljpr__xaz = []
            pzaa__siyg = []
            if op in cgic__iolyh:
                for i, cgsa__bmve in enumerate(lhs.data):
                    if is_common_scalar_dtype([cgsa__bmve.dtype, rhs]):
                        pljpr__xaz.append(
                            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(lhs, {i}) {kflmu__hgmnz} rhs'
                            )
                    else:
                        iur__rig = f'arr{i}'
                        pzaa__siyg.append(iur__rig)
                        pljpr__xaz.append(iur__rig)
                data_args = ', '.join(pljpr__xaz)
            else:
                data_args = ', '.join(
                    f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(lhs, {i}) {kflmu__hgmnz} rhs'
                     for i in range(len(lhs.columns)))
            header = 'def impl(lhs, rhs):\n'
            if len(pzaa__siyg) > 0:
                header += '  numba.parfors.parfor.init_prange()\n'
                header += '  n = len(lhs)\n'
                header += ''.join(
                    f'  {iur__rig} = np.empty(n, dtype=np.bool_)\n' for
                    iur__rig in pzaa__siyg)
                header += (
                    '  for i in numba.parfors.parfor.internal_prange(n):\n')
                header += ''.join('    {0}[i] = {1}\n'.format(iur__rig, op ==
                    operator.ne) for iur__rig in pzaa__siyg)
            index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(lhs)'
            return _gen_init_df(header, lhs.columns, data_args, index)
        if isinstance(rhs, DataFrameType):
            pljpr__xaz = []
            pzaa__siyg = []
            if op in cgic__iolyh:
                for i, cgsa__bmve in enumerate(rhs.data):
                    if is_common_scalar_dtype([lhs, cgsa__bmve.dtype]):
                        pljpr__xaz.append(
                            f'lhs {kflmu__hgmnz} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(rhs, {i})'
                            )
                    else:
                        iur__rig = f'arr{i}'
                        pzaa__siyg.append(iur__rig)
                        pljpr__xaz.append(iur__rig)
                data_args = ', '.join(pljpr__xaz)
            else:
                data_args = ', '.join(
                    'lhs {1} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(rhs, {0})'
                    .format(i, kflmu__hgmnz) for i in range(len(rhs.columns)))
            header = 'def impl(lhs, rhs):\n'
            if len(pzaa__siyg) > 0:
                header += '  numba.parfors.parfor.init_prange()\n'
                header += '  n = len(rhs)\n'
                header += ''.join('  {0} = np.empty(n, dtype=np.bool_)\n'.
                    format(iur__rig) for iur__rig in pzaa__siyg)
                header += (
                    '  for i in numba.parfors.parfor.internal_prange(n):\n')
                header += ''.join('    {0}[i] = {1}\n'.format(iur__rig, op ==
                    operator.ne) for iur__rig in pzaa__siyg)
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
        omtj__odh = create_binary_op_overload(op)
        overload(op)(omtj__odh)


_install_binary_ops()


def create_inplace_binary_op_overload(op):

    def overload_dataframe_inplace_binary_op(left, right):
        kflmu__hgmnz = numba.core.utils.OPERATORS_TO_BUILTINS[op]
        check_runtime_cols_unsupported(left, kflmu__hgmnz)
        check_runtime_cols_unsupported(right, kflmu__hgmnz)
        if isinstance(left, DataFrameType):
            if isinstance(right, DataFrameType):
                phb__dhds, _, upnpd__wvv = _get_binop_columns(left, right, True
                    )
                usel__pbrbf = 'def impl(left, right):\n'
                for i, roxqh__kxy in enumerate(upnpd__wvv):
                    if roxqh__kxy == -1:
                        usel__pbrbf += f"""  df_arr{i} = bodo.libs.array_kernels.gen_na_array(len(left), float64_arr_type)
"""
                        continue
                    usel__pbrbf += f"""  df_arr{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(left, {i})
"""
                    usel__pbrbf += f"""  df_arr{i} {kflmu__hgmnz} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(right, {roxqh__kxy})
"""
                data_args = ', '.join(f'df_arr{i}' for i in range(len(
                    phb__dhds)))
                index = (
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(left)')
                return _gen_init_df(usel__pbrbf, phb__dhds, data_args,
                    index, extra_globals={'float64_arr_type': types.Array(
                    types.float64, 1, 'C')})
            usel__pbrbf = 'def impl(left, right):\n'
            for i in range(len(left.columns)):
                usel__pbrbf += (
                    """  df_arr{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(left, {0})
"""
                    .format(i))
                usel__pbrbf += '  df_arr{0} {1} right\n'.format(i, kflmu__hgmnz
                    )
            data_args = ', '.join('df_arr{}'.format(i) for i in range(len(
                left.columns)))
            index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(left)'
            return _gen_init_df(usel__pbrbf, left.columns, data_args, index)
    return overload_dataframe_inplace_binary_op


def _install_inplace_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_inplace_binary_ops:
        omtj__odh = create_inplace_binary_op_overload(op)
        overload(op, no_unliteral=True)(omtj__odh)


_install_inplace_binary_ops()


def create_unary_op_overload(op):

    def overload_dataframe_unary_op(df):
        if isinstance(df, DataFrameType):
            kflmu__hgmnz = numba.core.utils.OPERATORS_TO_BUILTINS[op]
            check_runtime_cols_unsupported(df, kflmu__hgmnz)
            data_args = ', '.join(
                '{1} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})'
                .format(i, kflmu__hgmnz) for i in range(len(df.columns)))
            header = 'def impl(df):\n'
            return _gen_init_df(header, df.columns, data_args)
    return overload_dataframe_unary_op


def _install_unary_ops():
    for op in bodo.hiframes.pd_series_ext.series_unary_ops:
        omtj__odh = create_unary_op_overload(op)
        overload(op, no_unliteral=True)(omtj__odh)


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
            zymv__yjj = np.empty(n, np.bool_)
            for i in numba.parfors.parfor.internal_prange(n):
                zymv__yjj[i] = bodo.libs.array_kernels.isna(obj, i)
            return zymv__yjj
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
            zymv__yjj = np.empty(n, np.bool_)
            for i in range(n):
                zymv__yjj[i] = pd.isna(obj[i])
            return zymv__yjj
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
    ynck__rzkua = {'inplace': inplace, 'limit': limit, 'regex': regex,
        'method': method}
    rbimy__wpi = {'inplace': False, 'limit': None, 'regex': False, 'method':
        'pad'}
    check_unsupported_args('replace', ynck__rzkua, rbimy__wpi, package_name
        ='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'df.iloc[:, {i}].replace(to_replace, value).values' for i in range
        (len(df.columns)))
    header = """def impl(df, to_replace=None, value=None, inplace=False, limit=None, regex=False, method='pad'):
"""
    return _gen_init_df(header, df.columns, data_args)


def _is_col_access(expr_node):
    bpayi__zir = str(expr_node)
    return bpayi__zir.startswith('left.') or bpayi__zir.startswith('right.')


def _insert_NA_cond(expr_node, left_columns, left_data, right_columns,
    right_data):
    ctg__kqsxx = {'left': 0, 'right': 0, 'NOT_NA': 0}
    env = pd.core.computation.scope.ensure_scope(2, {}, {}, (ctg__kqsxx,))
    akbz__blmjq = pd.core.computation.parsing.clean_column_name

    def append_null_checks(expr_node, null_set):
        if not null_set:
            return expr_node
        chmkn__hdawk = ' & '.join([('NOT_NA.`' + x + '`') for x in null_set])
        vriar__uzd = {('NOT_NA', akbz__blmjq(cgsa__bmve)): cgsa__bmve for
            cgsa__bmve in null_set}
        lmo__app, _, _ = _parse_query_expr(chmkn__hdawk, env, [], [], None,
            join_cleaned_cols=vriar__uzd)
        gpax__kradn = (pd.core.computation.ops.BinOp.
            _disallow_scalar_only_bool_ops)
        pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops = (lambda
            self: None)
        try:
            gqgbc__qmto = pd.core.computation.ops.BinOp('&', lmo__app,
                expr_node)
        finally:
            (pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops
                ) = gpax__kradn
        return gqgbc__qmto

    def _insert_NA_cond_body(expr_node, null_set):
        if isinstance(expr_node, pd.core.computation.ops.BinOp):
            if expr_node.op == '|':
                mnaa__edry = set()
                rhpaa__umhbc = set()
                dixmq__yqb = _insert_NA_cond_body(expr_node.lhs, mnaa__edry)
                yjbz__khkbk = _insert_NA_cond_body(expr_node.rhs, rhpaa__umhbc)
                rjqbr__yml = mnaa__edry.intersection(rhpaa__umhbc)
                mnaa__edry.difference_update(rjqbr__yml)
                rhpaa__umhbc.difference_update(rjqbr__yml)
                null_set.update(rjqbr__yml)
                expr_node.lhs = append_null_checks(dixmq__yqb, mnaa__edry)
                expr_node.rhs = append_null_checks(yjbz__khkbk, rhpaa__umhbc)
                expr_node.operands = expr_node.lhs, expr_node.rhs
            else:
                expr_node.lhs = _insert_NA_cond_body(expr_node.lhs, null_set)
                expr_node.rhs = _insert_NA_cond_body(expr_node.rhs, null_set)
        elif _is_col_access(expr_node):
            gyufh__zzwzb = expr_node.name
            ezm__zckw, col_name = gyufh__zzwzb.split('.')
            if ezm__zckw == 'left':
                qhjml__itc = left_columns
                data = left_data
            else:
                qhjml__itc = right_columns
                data = right_data
            wciq__ocxtk = data[qhjml__itc.index(col_name)]
            if bodo.utils.typing.is_nullable(wciq__ocxtk):
                null_set.add(expr_node.name)
        return expr_node
    null_set = set()
    xny__uhh = _insert_NA_cond_body(expr_node, null_set)
    return append_null_checks(expr_node, null_set)


def _extract_equal_conds(expr_node):
    if not hasattr(expr_node, 'op'):
        return [], [], expr_node
    if expr_node.op == '==' and _is_col_access(expr_node.lhs
        ) and _is_col_access(expr_node.rhs):
        ndgp__yeeg = str(expr_node.lhs)
        qwbm__fip = str(expr_node.rhs)
        if ndgp__yeeg.startswith('left.') and qwbm__fip.startswith('left.'
            ) or ndgp__yeeg.startswith('right.') and qwbm__fip.startswith(
            'right.'):
            return [], [], expr_node
        left_on = [ndgp__yeeg.split('.')[1]]
        right_on = [qwbm__fip.split('.')[1]]
        if ndgp__yeeg.startswith('right.'):
            return right_on, left_on, None
        return left_on, right_on, None
    if expr_node.op == '&':
        rlpss__holn, mmiv__ubpc, zoii__wsp = _extract_equal_conds(expr_node.lhs
            )
        rqpi__hbebv, fvls__uop, osj__zxah = _extract_equal_conds(expr_node.rhs)
        left_on = rlpss__holn + rqpi__hbebv
        right_on = mmiv__ubpc + fvls__uop
        if zoii__wsp is None:
            return left_on, right_on, osj__zxah
        if osj__zxah is None:
            return left_on, right_on, zoii__wsp
        expr_node.lhs = zoii__wsp
        expr_node.rhs = osj__zxah
        expr_node.operands = expr_node.lhs, expr_node.rhs
        return left_on, right_on, expr_node
    return [], [], expr_node


def _parse_merge_cond(on_str, left_columns, left_data, right_columns,
    right_data):
    ctg__kqsxx = {'left': 0, 'right': 0}
    env = pd.core.computation.scope.ensure_scope(2, {}, {}, (ctg__kqsxx,))
    hkk__qfg = dict()
    akbz__blmjq = pd.core.computation.parsing.clean_column_name
    for name, nqvm__alf in (('left', left_columns), ('right', right_columns)):
        for cgsa__bmve in nqvm__alf:
            rsj__crrjz = akbz__blmjq(cgsa__bmve)
            bqo__mabp = name, rsj__crrjz
            if bqo__mabp in hkk__qfg:
                raise_bodo_error(
                    f"pd.merge(): {name} table contains two columns that are escaped to the same Python identifier '{cgsa__bmve}' and '{hkk__qfg[rsj__crrjz]}' Please rename one of these columns. To avoid this issue, please use names that are valid Python identifiers."
                    )
            hkk__qfg[bqo__mabp] = cgsa__bmve
    azf__thh, _, _ = _parse_query_expr(on_str, env, [], [], None,
        join_cleaned_cols=hkk__qfg)
    left_on, right_on, odvp__llr = _extract_equal_conds(azf__thh.terms)
    return left_on, right_on, _insert_NA_cond(odvp__llr, left_columns,
        left_data, right_columns, right_data)


@overload_method(DataFrameType, 'merge', inline='always', no_unliteral=True)
@overload(pd.merge, inline='always', no_unliteral=True)
def overload_dataframe_merge(left, right, how='inner', on=None, left_on=
    None, right_on=None, left_index=False, right_index=False, sort=False,
    suffixes=('_x', '_y'), copy=True, indicator=False, validate=None,
    _bodo_na_equal=True):
    check_runtime_cols_unsupported(left, 'DataFrame.merge()')
    check_runtime_cols_unsupported(right, 'DataFrame.merge()')
    bfo__gopwz = dict(sort=sort, copy=copy, validate=validate)
    anw__xjql = dict(sort=False, copy=True, validate=None)
    check_unsupported_args('DataFrame.merge', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    validate_merge_spec(left, right, how, on, left_on, right_on, left_index,
        right_index, sort, suffixes, copy, indicator, validate)
    how = get_overload_const_str(how)
    zkkkq__beel = tuple(sorted(set(left.columns) & set(right.columns), key=
        lambda k: str(k)))
    zvjq__xxt = ''
    if not is_overload_none(on):
        left_on = right_on = on
        if is_overload_constant_str(on):
            on_str = get_overload_const_str(on)
            if on_str not in zkkkq__beel and ('left.' in on_str or 'right.' in
                on_str):
                left_on, right_on, bwve__hxi = _parse_merge_cond(on_str,
                    left.columns, left.data, right.columns, right.data)
                if bwve__hxi is None:
                    zvjq__xxt = ''
                else:
                    zvjq__xxt = str(bwve__hxi)
    if is_overload_none(on) and is_overload_none(left_on) and is_overload_none(
        right_on) and is_overload_false(left_index) and is_overload_false(
        right_index):
        left_keys = zkkkq__beel
        right_keys = zkkkq__beel
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
    ixh__hfbcx = get_overload_const_bool(_bodo_na_equal)
    validate_keys_length(left_index, right_index, left_keys, right_keys)
    validate_keys_dtypes(left, right, left_index, right_index, left_keys,
        right_keys)
    if is_overload_constant_tuple(suffixes):
        ziupz__uyu = get_overload_const_tuple(suffixes)
    if is_overload_constant_list(suffixes):
        ziupz__uyu = list(get_overload_const_list(suffixes))
    suffix_x = ziupz__uyu[0]
    suffix_y = ziupz__uyu[1]
    validate_unicity_output_column_names(suffix_x, suffix_y, left_keys,
        right_keys, left.columns, right.columns, indicator_val)
    left_keys = gen_const_tup(left_keys)
    right_keys = gen_const_tup(right_keys)
    usel__pbrbf = (
        "def _impl(left, right, how='inner', on=None, left_on=None,\n")
    usel__pbrbf += (
        '    right_on=None, left_index=False, right_index=False, sort=False,\n'
        )
    usel__pbrbf += """    suffixes=('_x', '_y'), copy=True, indicator=False, validate=None, _bodo_na_equal=True):
"""
    usel__pbrbf += (
        """  return bodo.hiframes.pd_dataframe_ext.join_dummy(left, right, {}, {}, '{}', '{}', '{}', False, {}, {}, '{}')
"""
        .format(left_keys, right_keys, how, suffix_x, suffix_y,
        indicator_val, ixh__hfbcx, zvjq__xxt))
    ueciy__bmwpg = {}
    exec(usel__pbrbf, {'bodo': bodo}, ueciy__bmwpg)
    _impl = ueciy__bmwpg['_impl']
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
    vrkpc__evjpd = {string_array_type, dict_str_arr_type, binary_array_type,
        datetime_date_array_type, datetime_timedelta_array_type, boolean_array}
    mnvlq__iidbb = {get_overload_const_str(vkv__vsoyy) for vkv__vsoyy in (
        left_on, right_on, on) if is_overload_constant_str(vkv__vsoyy)}
    for df in (left, right):
        for i, cgsa__bmve in enumerate(df.data):
            if not isinstance(cgsa__bmve, valid_dataframe_column_types
                ) and cgsa__bmve not in vrkpc__evjpd:
                raise BodoError(
                    f'{name_func}(): use of column with {type(cgsa__bmve)} in merge unsupported'
                    )
            if df.columns[i] in mnvlq__iidbb and isinstance(cgsa__bmve,
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
        ziupz__uyu = get_overload_const_tuple(suffixes)
    if is_overload_constant_list(suffixes):
        ziupz__uyu = list(get_overload_const_list(suffixes))
    if len(ziupz__uyu) != 2:
        raise BodoError(name_func +
            '(): The number of suffixes should be exactly 2')
    zkkkq__beel = tuple(set(left.columns) & set(right.columns))
    if not is_overload_none(on):
        quqtk__uwo = False
        if is_overload_constant_str(on):
            on_str = get_overload_const_str(on)
            quqtk__uwo = on_str not in zkkkq__beel and ('left.' in on_str or
                'right.' in on_str)
        if len(zkkkq__beel) == 0 and not quqtk__uwo:
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
    cnstu__aga = numba.core.registry.cpu_target.typing_context
    if is_overload_true(left_index) or is_overload_true(right_index):
        if is_overload_true(left_index) and is_overload_true(right_index):
            rwa__bux = left.index
            ykbjo__sjwlq = isinstance(rwa__bux, StringIndexType)
            vpma__mioi = right.index
            gpz__knll = isinstance(vpma__mioi, StringIndexType)
        elif is_overload_true(left_index):
            rwa__bux = left.index
            ykbjo__sjwlq = isinstance(rwa__bux, StringIndexType)
            vpma__mioi = right.data[right.columns.index(right_keys[0])]
            gpz__knll = vpma__mioi.dtype == string_type
        elif is_overload_true(right_index):
            rwa__bux = left.data[left.columns.index(left_keys[0])]
            ykbjo__sjwlq = rwa__bux.dtype == string_type
            vpma__mioi = right.index
            gpz__knll = isinstance(vpma__mioi, StringIndexType)
        if ykbjo__sjwlq and gpz__knll:
            return
        rwa__bux = rwa__bux.dtype
        vpma__mioi = vpma__mioi.dtype
        try:
            iqqx__ohy = cnstu__aga.resolve_function_type(operator.eq, (
                rwa__bux, vpma__mioi), {})
        except:
            raise_bodo_error(
                'merge: You are trying to merge on {lk_dtype} and {rk_dtype} columns. If you wish to proceed you should use pd.concat'
                .format(lk_dtype=rwa__bux, rk_dtype=vpma__mioi))
    else:
        for bnc__zkypo, ztruq__mbikx in zip(left_keys, right_keys):
            rwa__bux = left.data[left.columns.index(bnc__zkypo)].dtype
            cxly__azegz = left.data[left.columns.index(bnc__zkypo)]
            vpma__mioi = right.data[right.columns.index(ztruq__mbikx)].dtype
            znyyl__ljj = right.data[right.columns.index(ztruq__mbikx)]
            if cxly__azegz == znyyl__ljj:
                continue
            fxio__arwt = (
                'merge: You are trying to merge on column {lk} of {lk_dtype} and column {rk} of {rk_dtype}. If you wish to proceed you should use pd.concat'
                .format(lk=bnc__zkypo, lk_dtype=rwa__bux, rk=ztruq__mbikx,
                rk_dtype=vpma__mioi))
            qxtdp__uolh = rwa__bux == string_type
            rhtn__dwff = vpma__mioi == string_type
            if qxtdp__uolh ^ rhtn__dwff:
                raise_bodo_error(fxio__arwt)
            try:
                iqqx__ohy = cnstu__aga.resolve_function_type(operator.eq, (
                    rwa__bux, vpma__mioi), {})
            except:
                raise_bodo_error(fxio__arwt)


def validate_keys(keys, df):
    izad__lns = set(keys).difference(set(df.columns))
    if len(izad__lns) > 0:
        if is_overload_constant_str(df.index.name_typ
            ) and get_overload_const_str(df.index.name_typ) in izad__lns:
            raise_bodo_error(
                f'merge(): use of index {df.index.name_typ} as key for on/left_on/right_on is unsupported'
                )
        raise_bodo_error(
            f"""merge(): invalid key {izad__lns} for on/left_on/right_on
merge supports only valid column names {df.columns}"""
            )


@overload_method(DataFrameType, 'join', inline='always', no_unliteral=True)
def overload_dataframe_join(left, other, on=None, how='left', lsuffix='',
    rsuffix='', sort=False):
    check_runtime_cols_unsupported(left, 'DataFrame.join()')
    check_runtime_cols_unsupported(other, 'DataFrame.join()')
    bfo__gopwz = dict(lsuffix=lsuffix, rsuffix=rsuffix)
    anw__xjql = dict(lsuffix='', rsuffix='')
    check_unsupported_args('DataFrame.join', bfo__gopwz, anw__xjql,
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
    usel__pbrbf = "def _impl(left, other, on=None, how='left',\n"
    usel__pbrbf += "    lsuffix='', rsuffix='', sort=False):\n"
    usel__pbrbf += (
        """  return bodo.hiframes.pd_dataframe_ext.join_dummy(left, other, {}, {}, '{}', '{}', '{}', True, False, True, '')
"""
        .format(left_keys, right_keys, how, lsuffix, rsuffix))
    ueciy__bmwpg = {}
    exec(usel__pbrbf, {'bodo': bodo}, ueciy__bmwpg)
    _impl = ueciy__bmwpg['_impl']
    return _impl


def validate_join_spec(left, other, on, how, lsuffix, rsuffix, sort):
    if not isinstance(other, DataFrameType):
        raise BodoError('join() requires dataframe inputs')
    ensure_constant_values('merge', 'how', how, ('left', 'right', 'outer',
        'inner'))
    if not is_overload_none(on) and len(get_overload_const_list(on)) != 1:
        raise BodoError('join(): len(on) must equals to 1 when specified.')
    if not is_overload_none(on):
        sxsnr__dhahe = get_overload_const_list(on)
        validate_keys(sxsnr__dhahe, left)
    if not is_overload_false(sort):
        raise BodoError(
            'join(): sort parameter only supports default value False')
    zkkkq__beel = tuple(set(left.columns) & set(other.columns))
    if len(zkkkq__beel) > 0:
        raise_bodo_error(
            'join(): not supporting joining on overlapping columns:{cols} Use DataFrame.merge() instead.'
            .format(cols=zkkkq__beel))


def validate_unicity_output_column_names(suffix_x, suffix_y, left_keys,
    right_keys, left_columns, right_columns, indicator_val):
    qfkl__ghaqo = set(left_keys) & set(right_keys)
    fslg__neb = set(left_columns) & set(right_columns)
    gvr__oau = fslg__neb - qfkl__ghaqo
    bcsw__kmn = set(left_columns) - fslg__neb
    nfae__fwmll = set(right_columns) - fslg__neb
    gca__pfn = {}

    def insertOutColumn(col_name):
        if col_name in gca__pfn:
            raise_bodo_error(
                'join(): two columns happen to have the same name : {}'.
                format(col_name))
        gca__pfn[col_name] = 0
    for skvy__qsd in qfkl__ghaqo:
        insertOutColumn(skvy__qsd)
    for skvy__qsd in gvr__oau:
        thg__xmy = str(skvy__qsd) + suffix_x
        dobst__wxp = str(skvy__qsd) + suffix_y
        insertOutColumn(thg__xmy)
        insertOutColumn(dobst__wxp)
    for skvy__qsd in bcsw__kmn:
        insertOutColumn(skvy__qsd)
    for skvy__qsd in nfae__fwmll:
        insertOutColumn(skvy__qsd)
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
    zkkkq__beel = tuple(sorted(set(left.columns) & set(right.columns), key=
        lambda k: str(k)))
    if not is_overload_none(on):
        left_on = right_on = on
    if is_overload_none(on) and is_overload_none(left_on) and is_overload_none(
        right_on) and is_overload_false(left_index) and is_overload_false(
        right_index):
        left_keys = zkkkq__beel
        right_keys = zkkkq__beel
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
        ziupz__uyu = suffixes
    if is_overload_constant_list(suffixes):
        ziupz__uyu = list(get_overload_const_list(suffixes))
    if isinstance(suffixes, types.Omitted):
        ziupz__uyu = suffixes.value
    suffix_x = ziupz__uyu[0]
    suffix_y = ziupz__uyu[1]
    usel__pbrbf = (
        'def _impl(left, right, on=None, left_on=None, right_on=None,\n')
    usel__pbrbf += (
        '    left_index=False, right_index=False, by=None, left_by=None,\n')
    usel__pbrbf += (
        "    right_by=None, suffixes=('_x', '_y'), tolerance=None,\n")
    usel__pbrbf += "    allow_exact_matches=True, direction='backward'):\n"
    usel__pbrbf += '  suffix_x = suffixes[0]\n'
    usel__pbrbf += '  suffix_y = suffixes[1]\n'
    usel__pbrbf += (
        """  return bodo.hiframes.pd_dataframe_ext.join_dummy(left, right, {}, {}, 'asof', '{}', '{}', False, False, True, '')
"""
        .format(left_keys, right_keys, suffix_x, suffix_y))
    ueciy__bmwpg = {}
    exec(usel__pbrbf, {'bodo': bodo}, ueciy__bmwpg)
    _impl = ueciy__bmwpg['_impl']
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
    bfo__gopwz = dict(sort=sort, group_keys=group_keys, squeeze=squeeze,
        observed=observed)
    qwyrr__igu = dict(sort=False, group_keys=True, squeeze=False, observed=True
        )
    check_unsupported_args('Dataframe.groupby', bfo__gopwz, qwyrr__igu,
        package_name='pandas', module_name='GroupBy')


def pivot_error_checking(df, index, columns, values, func_name):
    rtfm__kmlhe = func_name == 'DataFrame.pivot_table'
    if rtfm__kmlhe:
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
    qfto__runp = get_literal_value(columns)
    if isinstance(qfto__runp, (list, tuple)):
        if len(qfto__runp) > 1:
            raise BodoError(
                f"{func_name}(): 'columns' argument must be a constant column label not a {qfto__runp}"
                )
        qfto__runp = qfto__runp[0]
    if qfto__runp not in df.columns:
        raise BodoError(
            f"{func_name}(): 'columns' column {qfto__runp} not found in DataFrame {df}."
            )
    rdvft__xekp = {gtcss__vpd: i for i, gtcss__vpd in enumerate(df.columns)}
    xpy__vnux = rdvft__xekp[qfto__runp]
    if is_overload_none(index):
        xgcwx__dasu = []
        yub__mdur = []
    else:
        yub__mdur = get_literal_value(index)
        if not isinstance(yub__mdur, (list, tuple)):
            yub__mdur = [yub__mdur]
        xgcwx__dasu = []
        for index in yub__mdur:
            if index not in rdvft__xekp:
                raise BodoError(
                    f"{func_name}(): 'index' column {index} not found in DataFrame {df}."
                    )
            xgcwx__dasu.append(rdvft__xekp[index])
    if not (all(isinstance(gtcss__vpd, int) for gtcss__vpd in yub__mdur) or
        all(isinstance(gtcss__vpd, str) for gtcss__vpd in yub__mdur)):
        raise BodoError(
            f"{func_name}(): column names selected for 'index' must all share a common int or string type. Please convert your names to a common type using DataFrame.rename()"
            )
    if is_overload_none(values):
        namih__hlw = []
        goe__tvbhu = []
        eok__wmq = xgcwx__dasu + [xpy__vnux]
        for i, gtcss__vpd in enumerate(df.columns):
            if i not in eok__wmq:
                namih__hlw.append(i)
                goe__tvbhu.append(gtcss__vpd)
    else:
        goe__tvbhu = get_literal_value(values)
        if not isinstance(goe__tvbhu, (list, tuple)):
            goe__tvbhu = [goe__tvbhu]
        namih__hlw = []
        for val in goe__tvbhu:
            if val not in rdvft__xekp:
                raise BodoError(
                    f"{func_name}(): 'values' column {val} not found in DataFrame {df}."
                    )
            namih__hlw.append(rdvft__xekp[val])
    if all(isinstance(gtcss__vpd, int) for gtcss__vpd in goe__tvbhu):
        goe__tvbhu = np.array(goe__tvbhu, 'int64')
    elif all(isinstance(gtcss__vpd, str) for gtcss__vpd in goe__tvbhu):
        goe__tvbhu = pd.array(goe__tvbhu, 'string')
    else:
        raise BodoError(
            f"{func_name}(): column names selected for 'values' must all share a common int or string type. Please convert your names to a common type using DataFrame.rename()"
            )
    rbf__sfazv = set(namih__hlw) | set(xgcwx__dasu) | {xpy__vnux}
    if len(rbf__sfazv) != len(namih__hlw) + len(xgcwx__dasu) + 1:
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
    if len(xgcwx__dasu) == 0:
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
        for jgakc__xhkzd in xgcwx__dasu:
            index_column = df.data[jgakc__xhkzd]
            check_valid_index_typ(index_column)
    bqhue__msnw = df.data[xpy__vnux]
    if isinstance(bqhue__msnw, (bodo.ArrayItemArrayType, bodo.MapArrayType,
        bodo.StructArrayType, bodo.TupleArrayType, bodo.IntervalArrayType)):
        raise BodoError(
            f"{func_name}(): 'columns' DataFrame column must have scalar rows")
    if isinstance(bqhue__msnw, bodo.CategoricalArrayType):
        raise BodoError(
            f"{func_name}(): 'columns' DataFrame column does not support categorical data"
            )
    for qgk__ptehi in namih__hlw:
        qgtqv__acs = df.data[qgk__ptehi]
        if isinstance(qgtqv__acs, (bodo.ArrayItemArrayType, bodo.
            MapArrayType, bodo.StructArrayType, bodo.TupleArrayType)
            ) or qgtqv__acs == bodo.binary_array_type:
            raise BodoError(
                f"{func_name}(): 'values' DataFrame column must have scalar rows"
                )
    return (yub__mdur, qfto__runp, goe__tvbhu, xgcwx__dasu, xpy__vnux,
        namih__hlw)


@overload(pd.pivot, inline='always', no_unliteral=True)
@overload_method(DataFrameType, 'pivot', inline='always', no_unliteral=True)
def overload_dataframe_pivot(data, index=None, columns=None, values=None):
    check_runtime_cols_unsupported(data, 'DataFrame.pivot()')
    if not isinstance(data, DataFrameType):
        raise BodoError("pandas.pivot(): 'data' argument must be a DataFrame")
    (yub__mdur, qfto__runp, goe__tvbhu, jgakc__xhkzd, xpy__vnux, ofbsp__wbnc
        ) = (pivot_error_checking(data, index, columns, values,
        'DataFrame.pivot'))
    if len(yub__mdur) == 0:
        if is_overload_none(data.index.name_typ):
            yub__mdur = [None]
        else:
            yub__mdur = [get_literal_value(data.index.name_typ)]
    if len(goe__tvbhu) == 1:
        qbmhg__rsmb = None
    else:
        qbmhg__rsmb = goe__tvbhu
    usel__pbrbf = 'def impl(data, index=None, columns=None, values=None):\n'
    usel__pbrbf += f'    pivot_values = data.iloc[:, {xpy__vnux}].unique()\n'
    usel__pbrbf += '    return bodo.hiframes.pd_dataframe_ext.pivot_impl(\n'
    if len(jgakc__xhkzd) == 0:
        usel__pbrbf += f"""        (bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)),),
"""
    else:
        usel__pbrbf += '        (\n'
        for ueh__lfbv in jgakc__xhkzd:
            usel__pbrbf += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {ueh__lfbv}),
"""
        usel__pbrbf += '        ),\n'
    usel__pbrbf += f"""        (bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {xpy__vnux}),),
"""
    usel__pbrbf += '        (\n'
    for qgk__ptehi in ofbsp__wbnc:
        usel__pbrbf += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {qgk__ptehi}),
"""
    usel__pbrbf += '        ),\n'
    usel__pbrbf += '        pivot_values,\n'
    usel__pbrbf += '        index_lit_tup,\n'
    usel__pbrbf += '        columns_lit,\n'
    usel__pbrbf += '        values_name_const,\n'
    usel__pbrbf += '    )\n'
    ueciy__bmwpg = {}
    exec(usel__pbrbf, {'bodo': bodo, 'index_lit_tup': tuple(yub__mdur),
        'columns_lit': qfto__runp, 'values_name_const': qbmhg__rsmb},
        ueciy__bmwpg)
    impl = ueciy__bmwpg['impl']
    return impl


@overload(pd.pivot_table, inline='always', no_unliteral=True)
@overload_method(DataFrameType, 'pivot_table', inline='always',
    no_unliteral=True)
def overload_dataframe_pivot_table(data, values=None, index=None, columns=
    None, aggfunc='mean', fill_value=None, margins=False, dropna=True,
    margins_name='All', observed=False, sort=True, _pivot_values=None):
    check_runtime_cols_unsupported(data, 'DataFrame.pivot_table()')
    bfo__gopwz = dict(fill_value=fill_value, margins=margins, dropna=dropna,
        margins_name=margins_name, observed=observed, sort=sort)
    anw__xjql = dict(fill_value=None, margins=False, dropna=True,
        margins_name='All', observed=False, sort=True)
    check_unsupported_args('DataFrame.pivot_table', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    if not isinstance(data, DataFrameType):
        raise BodoError(
            "pandas.pivot_table(): 'data' argument must be a DataFrame")
    if _pivot_values is None:
        (yub__mdur, qfto__runp, goe__tvbhu, jgakc__xhkzd, xpy__vnux,
            ofbsp__wbnc) = (pivot_error_checking(data, index, columns,
            values, 'DataFrame.pivot_table'))
        if len(goe__tvbhu) == 1:
            qbmhg__rsmb = None
        else:
            qbmhg__rsmb = goe__tvbhu
        usel__pbrbf = 'def impl(\n'
        usel__pbrbf += '    data,\n'
        usel__pbrbf += '    values=None,\n'
        usel__pbrbf += '    index=None,\n'
        usel__pbrbf += '    columns=None,\n'
        usel__pbrbf += '    aggfunc="mean",\n'
        usel__pbrbf += '    fill_value=None,\n'
        usel__pbrbf += '    margins=False,\n'
        usel__pbrbf += '    dropna=True,\n'
        usel__pbrbf += '    margins_name="All",\n'
        usel__pbrbf += '    observed=False,\n'
        usel__pbrbf += '    sort=True,\n'
        usel__pbrbf += '    _pivot_values=None,\n'
        usel__pbrbf += '):\n'
        jks__anwjx = jgakc__xhkzd + [xpy__vnux] + ofbsp__wbnc
        usel__pbrbf += f'    data = data.iloc[:, {jks__anwjx}]\n'
        cdg__tre = yub__mdur + [qfto__runp]
        usel__pbrbf += (
            f'    data = data.groupby({cdg__tre!r}, as_index=False).agg(aggfunc)\n'
            )
        usel__pbrbf += (
            f'    pivot_values = data.iloc[:, {len(jgakc__xhkzd)}].unique()\n')
        usel__pbrbf += (
            '    return bodo.hiframes.pd_dataframe_ext.pivot_impl(\n')
        usel__pbrbf += '        (\n'
        for i in range(0, len(jgakc__xhkzd)):
            usel__pbrbf += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {i}),
"""
        usel__pbrbf += '        ),\n'
        usel__pbrbf += f"""        (bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {len(jgakc__xhkzd)}),),
"""
        usel__pbrbf += '        (\n'
        for i in range(len(jgakc__xhkzd) + 1, len(ofbsp__wbnc) + len(
            jgakc__xhkzd) + 1):
            usel__pbrbf += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {i}),
"""
        usel__pbrbf += '        ),\n'
        usel__pbrbf += '        pivot_values,\n'
        usel__pbrbf += '        index_lit_tup,\n'
        usel__pbrbf += '        columns_lit,\n'
        usel__pbrbf += '        values_name_const,\n'
        usel__pbrbf += '        check_duplicates=False,\n'
        usel__pbrbf += '    )\n'
        ueciy__bmwpg = {}
        exec(usel__pbrbf, {'bodo': bodo, 'numba': numba, 'index_lit_tup':
            tuple(yub__mdur), 'columns_lit': qfto__runp,
            'values_name_const': qbmhg__rsmb}, ueciy__bmwpg)
        impl = ueciy__bmwpg['impl']
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
    bfo__gopwz = dict(values=values, rownames=rownames, colnames=colnames,
        aggfunc=aggfunc, margins=margins, margins_name=margins_name, dropna
        =dropna, normalize=normalize)
    anw__xjql = dict(values=None, rownames=None, colnames=None, aggfunc=
        None, margins=False, margins_name='All', dropna=True, normalize=False)
    check_unsupported_args('pandas.crosstab', bfo__gopwz, anw__xjql,
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
    bfo__gopwz = dict(ignore_index=ignore_index, key=key)
    anw__xjql = dict(ignore_index=False, key=None)
    check_unsupported_args('DataFrame.sort_values', bfo__gopwz, anw__xjql,
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
    kepwm__wgz = set(df.columns)
    if is_overload_constant_str(df.index.name_typ):
        kepwm__wgz.add(get_overload_const_str(df.index.name_typ))
    if is_overload_constant_tuple(by):
        ymnw__ccm = [get_overload_const_tuple(by)]
    else:
        ymnw__ccm = get_overload_const_list(by)
    ymnw__ccm = set((k, '') if (k, '') in kepwm__wgz else k for k in ymnw__ccm)
    if len(ymnw__ccm.difference(kepwm__wgz)) > 0:
        alkqp__twub = list(set(get_overload_const_list(by)).difference(
            kepwm__wgz))
        raise_bodo_error(f'sort_values(): invalid keys {alkqp__twub} for by.')
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
        iocm__dugr = get_overload_const_list(na_position)
        for na_position in iocm__dugr:
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
    bfo__gopwz = dict(axis=axis, level=level, kind=kind, sort_remaining=
        sort_remaining, ignore_index=ignore_index, key=key)
    anw__xjql = dict(axis=0, level=None, kind='quicksort', sort_remaining=
        True, ignore_index=False, key=None)
    check_unsupported_args('DataFrame.sort_index', bfo__gopwz, anw__xjql,
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
    bfo__gopwz = dict(limit=limit, downcast=downcast)
    anw__xjql = dict(limit=None, downcast=None)
    check_unsupported_args('DataFrame.fillna', bfo__gopwz, anw__xjql,
        package_name='pandas', module_name='DataFrame')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise BodoError("DataFrame.fillna(): 'axis' argument not supported.")
    ldz__pbua = not is_overload_none(value)
    hjp__ibg = not is_overload_none(method)
    if ldz__pbua and hjp__ibg:
        raise BodoError(
            "DataFrame.fillna(): Cannot specify both 'value' and 'method'.")
    if not ldz__pbua and not hjp__ibg:
        raise BodoError(
            "DataFrame.fillna(): Must specify one of 'value' and 'method'.")
    if ldz__pbua:
        ddhxl__cdiy = 'value=value'
    else:
        ddhxl__cdiy = 'method=method'
    data_args = [(
        f"df['{gtcss__vpd}'].fillna({ddhxl__cdiy}, inplace=inplace)" if
        isinstance(gtcss__vpd, str) else
        f'df[{gtcss__vpd}].fillna({ddhxl__cdiy}, inplace=inplace)') for
        gtcss__vpd in df.columns]
    usel__pbrbf = """def impl(df, value=None, method=None, axis=None, inplace=False, limit=None, downcast=None):
"""
    if is_overload_true(inplace):
        usel__pbrbf += '  ' + '  \n'.join(data_args) + '\n'
        ueciy__bmwpg = {}
        exec(usel__pbrbf, {}, ueciy__bmwpg)
        impl = ueciy__bmwpg['impl']
        return impl
    else:
        return _gen_init_df(usel__pbrbf, df.columns, ', '.join(spgux__zcyx +
            '.values' for spgux__zcyx in data_args))


@overload_method(DataFrameType, 'reset_index', inline='always',
    no_unliteral=True)
def overload_dataframe_reset_index(df, level=None, drop=False, inplace=
    False, col_level=0, col_fill='', _bodo_transformed=False):
    check_runtime_cols_unsupported(df, 'DataFrame.reset_index()')
    bfo__gopwz = dict(col_level=col_level, col_fill=col_fill)
    anw__xjql = dict(col_level=0, col_fill='')
    check_unsupported_args('DataFrame.reset_index', bfo__gopwz, anw__xjql,
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
    usel__pbrbf = """def impl(df, level=None, drop=False, inplace=False, col_level=0, col_fill='', _bodo_transformed=False,):
"""
    usel__pbrbf += (
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
        slpv__aivnx = 'index' if 'index' not in columns else 'level_0'
        index_names = get_index_names(df.index, 'DataFrame.reset_index()',
            slpv__aivnx)
        columns = index_names + columns
        if isinstance(df.index, MultiIndexType):
            usel__pbrbf += (
                '  m_index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
                )
            lwcn__luzc = ['m_index._data[{}]'.format(i) for i in range(df.
                index.nlevels)]
            data_args = lwcn__luzc + data_args
        else:
            cyz__mgzb = (
                'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
                )
            data_args = [cyz__mgzb] + data_args
    return _gen_init_df(usel__pbrbf, columns, ', '.join(data_args), 'index')


def _is_all_levels(df, level):
    ghr__lef = len(get_index_data_arr_types(df.index))
    return is_overload_none(level) or is_overload_constant_int(level
        ) and get_overload_const_int(level
        ) == 0 and ghr__lef == 1 or is_overload_constant_list(level) and list(
        get_overload_const_list(level)) == list(range(ghr__lef))


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
        wxfhj__dpuo = list(range(len(df.columns)))
    elif not is_overload_constant_list(subset):
        raise_bodo_error(
            f'df.dropna(): subset argument should a constant list, not {subset}'
            )
    else:
        sann__qjwp = get_overload_const_list(subset)
        wxfhj__dpuo = []
        for ahepz__tzh in sann__qjwp:
            if ahepz__tzh not in df.columns:
                raise_bodo_error(
                    f"df.dropna(): column '{ahepz__tzh}' not in data frame columns {df}"
                    )
            wxfhj__dpuo.append(df.columns.index(ahepz__tzh))
    becjd__uza = len(df.columns)
    data_args = ', '.join('data_{}'.format(i) for i in range(becjd__uza))
    usel__pbrbf = (
        "def impl(df, axis=0, how='any', thresh=None, subset=None, inplace=False):\n"
        )
    for i in range(becjd__uza):
        usel__pbrbf += (
            '  data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})\n'
            .format(i))
    index = (
        'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
        )
    usel__pbrbf += (
        """  ({0}, index_arr) = bodo.libs.array_kernels.dropna(({0}, {1}), how, thresh, ({2},))
"""
        .format(data_args, index, ', '.join(str(a) for a in wxfhj__dpuo)))
    usel__pbrbf += (
        '  index = bodo.utils.conversion.index_from_array(index_arr)\n')
    return _gen_init_df(usel__pbrbf, df.columns, data_args, 'index')


@overload_method(DataFrameType, 'drop', inline='always', no_unliteral=True)
def overload_dataframe_drop(df, labels=None, axis=0, index=None, columns=
    None, level=None, inplace=False, errors='raise', _bodo_transformed=False):
    check_runtime_cols_unsupported(df, 'DataFrame.drop()')
    bfo__gopwz = dict(index=index, level=level, errors=errors)
    anw__xjql = dict(index=None, level=None, errors='raise')
    check_unsupported_args('DataFrame.drop', bfo__gopwz, anw__xjql,
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
            jecv__tpikw = get_overload_const_str(labels),
        elif is_overload_constant_list(labels):
            jecv__tpikw = get_overload_const_list(labels)
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
            jecv__tpikw = get_overload_const_str(columns),
        elif is_overload_constant_list(columns):
            jecv__tpikw = get_overload_const_list(columns)
        else:
            raise_bodo_error(
                'constant list of columns expected for labels in DataFrame.drop()'
                )
    for gtcss__vpd in jecv__tpikw:
        if gtcss__vpd not in df.columns:
            raise_bodo_error(
                'DataFrame.drop(): column {} not in DataFrame columns {}'.
                format(gtcss__vpd, df.columns))
    if len(set(jecv__tpikw)) == len(df.columns):
        raise BodoError('DataFrame.drop(): Dropping all columns not supported.'
            )
    inplace = is_overload_true(inplace)
    dgw__zpqk = tuple(gtcss__vpd for gtcss__vpd in df.columns if gtcss__vpd
         not in jecv__tpikw)
    data_args = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(df.columns.index(gtcss__vpd), '.copy()' if not inplace else
        '') for gtcss__vpd in dgw__zpqk)
    usel__pbrbf = (
        'def impl(df, labels=None, axis=0, index=None, columns=None,\n')
    usel__pbrbf += (
        "     level=None, inplace=False, errors='raise', _bodo_transformed=False):\n"
        )
    index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
    return _gen_init_df(usel__pbrbf, dgw__zpqk, data_args, index)


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
    bfo__gopwz = dict(random_state=random_state, weights=weights, axis=axis,
        ignore_index=ignore_index)
    wgzo__gbhc = dict(random_state=None, weights=None, axis=None,
        ignore_index=False)
    check_unsupported_args('DataFrame.sample', bfo__gopwz, wgzo__gbhc,
        package_name='pandas', module_name='DataFrame')
    if not is_overload_none(n) and not is_overload_none(frac):
        raise BodoError(
            'DataFrame.sample(): only one of n and frac option can be selected'
            )
    becjd__uza = len(df.columns)
    data_args = ', '.join('data_{}'.format(i) for i in range(becjd__uza))
    ixtqy__vhn = ', '.join('rhs_data_{}'.format(i) for i in range(becjd__uza))
    usel__pbrbf = """def impl(df, n=None, frac=None, replace=False, weights=None, random_state=None, axis=None, ignore_index=False):
"""
    usel__pbrbf += '  if (frac == 1 or n == len(df)) and not replace:\n'
    usel__pbrbf += (
        '    return bodo.allgatherv(bodo.random_shuffle(df), False)\n')
    for i in range(becjd__uza):
        usel__pbrbf += (
            """  rhs_data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})
"""
            .format(i))
    usel__pbrbf += '  if frac is None:\n'
    usel__pbrbf += '    frac_d = -1.0\n'
    usel__pbrbf += '  else:\n'
    usel__pbrbf += '    frac_d = frac\n'
    usel__pbrbf += '  if n is None:\n'
    usel__pbrbf += '    n_i = 0\n'
    usel__pbrbf += '  else:\n'
    usel__pbrbf += '    n_i = n\n'
    index = (
        'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
        )
    usel__pbrbf += f"""  ({data_args},), index_arr = bodo.libs.array_kernels.sample_table_operation(({ixtqy__vhn},), {index}, n_i, frac_d, replace)
"""
    usel__pbrbf += (
        '  index = bodo.utils.conversion.index_from_array(index_arr)\n')
    return bodo.hiframes.dataframe_impl._gen_init_df(usel__pbrbf, df.
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
    ynck__rzkua = {'verbose': verbose, 'buf': buf, 'max_cols': max_cols,
        'memory_usage': memory_usage, 'show_counts': show_counts,
        'null_counts': null_counts}
    rbimy__wpi = {'verbose': None, 'buf': None, 'max_cols': None,
        'memory_usage': None, 'show_counts': None, 'null_counts': None}
    check_unsupported_args('DataFrame.info', ynck__rzkua, rbimy__wpi,
        package_name='pandas', module_name='DataFrame')
    cqm__tqum = f"<class '{str(type(df)).split('.')[-1]}"
    if len(df.columns) == 0:

        def _info_impl(df, verbose=None, buf=None, max_cols=None,
            memory_usage=None, show_counts=None, null_counts=None):
            yge__oqkcd = cqm__tqum + '\n'
            yge__oqkcd += 'Index: 0 entries\n'
            yge__oqkcd += 'Empty DataFrame'
            print(yge__oqkcd)
        return _info_impl
    else:
        usel__pbrbf = """def _info_impl(df, verbose=None, buf=None, max_cols=None, memory_usage=None, show_counts=None, null_counts=None): #pragma: no cover
"""
        usel__pbrbf += '    ncols = df.shape[1]\n'
        usel__pbrbf += f'    lines = "{cqm__tqum}\\n"\n'
        usel__pbrbf += f'    lines += "{df.index}: "\n'
        usel__pbrbf += (
            '    index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
            )
        if isinstance(df.index, bodo.hiframes.pd_index_ext.RangeIndexType):
            usel__pbrbf += """    lines += f"{len(index)} entries, {index.start} to {index.stop-1}\\n\"
"""
        elif isinstance(df.index, bodo.hiframes.pd_index_ext.StringIndexType):
            usel__pbrbf += """    lines += f"{len(index)} entries, {index[0]} to {index[len(index)-1]}\\n\"
"""
        else:
            usel__pbrbf += (
                '    lines += f"{len(index)} entries, {index[0]} to {index[-1]}\\n"\n'
                )
        usel__pbrbf += (
            '    lines += f"Data columns (total {ncols} columns):\\n"\n')
        usel__pbrbf += (
            f'    space = {max(len(str(k)) for k in df.columns) + 1}\n')
        usel__pbrbf += '    column_width = max(space, 7)\n'
        usel__pbrbf += '    column= "Column"\n'
        usel__pbrbf += '    underl= "------"\n'
        usel__pbrbf += (
            '    lines += f"#   {column:<{column_width}} Non-Null Count  Dtype\\n"\n'
            )
        usel__pbrbf += (
            '    lines += f"--- {underl:<{column_width}} --------------  -----\\n"\n'
            )
        usel__pbrbf += '    mem_size = 0\n'
        usel__pbrbf += (
            '    col_name = bodo.libs.str_arr_ext.pre_alloc_string_array(ncols, -1)\n'
            )
        usel__pbrbf += """    non_null_count = bodo.libs.str_arr_ext.pre_alloc_string_array(ncols, -1)
"""
        usel__pbrbf += (
            '    col_dtype = bodo.libs.str_arr_ext.pre_alloc_string_array(ncols, -1)\n'
            )
        zedmn__fuj = dict()
        for i in range(len(df.columns)):
            usel__pbrbf += f"""    non_null_count[{i}] = str(bodo.libs.array_ops.array_op_count(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})))
"""
            ymesw__yicgd = f'{df.data[i].dtype}'
            if isinstance(df.data[i], bodo.CategoricalArrayType):
                ymesw__yicgd = 'category'
            elif isinstance(df.data[i], bodo.IntegerArrayType):
                rbn__zxgks = bodo.libs.int_arr_ext.IntDtype(df.data[i].dtype
                    ).name
                ymesw__yicgd = f'{rbn__zxgks[:-7]}'
            usel__pbrbf += f'    col_dtype[{i}] = "{ymesw__yicgd}"\n'
            if ymesw__yicgd in zedmn__fuj:
                zedmn__fuj[ymesw__yicgd] += 1
            else:
                zedmn__fuj[ymesw__yicgd] = 1
            usel__pbrbf += f'    col_name[{i}] = "{df.columns[i]}"\n'
            usel__pbrbf += f"""    mem_size += bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).nbytes
"""
        usel__pbrbf += """    column_info = [f'{i:^3} {name:<{column_width}} {count} non-null      {dtype}' for i, (name, count, dtype) in enumerate(zip(col_name, non_null_count, col_dtype))]
"""
        usel__pbrbf += '    for i in column_info:\n'
        usel__pbrbf += "        lines += f'{i}\\n'\n"
        ord__znnux = ', '.join(f'{k}({zedmn__fuj[k]})' for k in sorted(
            zedmn__fuj))
        usel__pbrbf += f"    lines += 'dtypes: {ord__znnux}\\n'\n"
        usel__pbrbf += '    mem_size += df.index.nbytes\n'
        usel__pbrbf += '    total_size = _sizeof_fmt(mem_size)\n'
        usel__pbrbf += "    lines += f'memory usage: {total_size}'\n"
        usel__pbrbf += '    print(lines)\n'
        ueciy__bmwpg = {}
        exec(usel__pbrbf, {'_sizeof_fmt': _sizeof_fmt, 'pd': pd, 'bodo':
            bodo, 'np': np}, ueciy__bmwpg)
        _info_impl = ueciy__bmwpg['_info_impl']
        return _info_impl


@overload_method(DataFrameType, 'memory_usage', inline='always',
    no_unliteral=True)
def overload_dataframe_memory_usage(df, index=True, deep=False):
    check_runtime_cols_unsupported(df, 'DataFrame.memory_usage()')
    usel__pbrbf = 'def impl(df, index=True, deep=False):\n'
    data = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).nbytes'
         for i in range(len(df.columns)))
    if is_overload_true(index):
        maj__iwv = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df).nbytes\n,')
        elvu__bwqbf = ','.join(f"'{gtcss__vpd}'" for gtcss__vpd in df.columns)
        arr = f"bodo.utils.conversion.coerce_to_array(('Index',{elvu__bwqbf}))"
        index = f'bodo.hiframes.pd_index_ext.init_binary_str_index({arr})'
        usel__pbrbf += f"""  return bodo.hiframes.pd_series_ext.init_series(({maj__iwv}{data}), {index}, None)
"""
    else:
        phub__yfpaq = ',' if len(df.columns) == 1 else ''
        lyc__dpayt = gen_const_tup(df.columns)
        usel__pbrbf += f"""  return bodo.hiframes.pd_series_ext.init_series(({data}{phub__yfpaq}), pd.Index({lyc__dpayt}), None)
"""
    ueciy__bmwpg = {}
    exec(usel__pbrbf, {'bodo': bodo, 'pd': pd}, ueciy__bmwpg)
    impl = ueciy__bmwpg['impl']
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
    yvgfk__ywt = 'read_excel_df{}'.format(next_label())
    setattr(types, yvgfk__ywt, df_type)
    lce__qpvdg = False
    if is_overload_constant_list(parse_dates):
        lce__qpvdg = get_overload_const_list(parse_dates)
    extm__zact = ', '.join(["'{}':{}".format(cname, _get_pd_dtype_str(t)) for
        cname, t in zip(df_type.columns, df_type.data)])
    usel__pbrbf = (
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
        .format(yvgfk__ywt, list(df_type.columns), extm__zact, lce__qpvdg))
    ueciy__bmwpg = {}
    exec(usel__pbrbf, globals(), ueciy__bmwpg)
    impl = ueciy__bmwpg['impl']
    return impl


def overload_dataframe_plot(df, x=None, y=None, kind='line', figsize=None,
    xlabel=None, ylabel=None, title=None, legend=True, fontsize=None,
    xticks=None, yticks=None, ax=None):
    try:
        import matplotlib.pyplot as plt
    except ImportError as mvrtq__ghku:
        raise BodoError('df.plot needs matplotllib which is not installed.')
    usel__pbrbf = (
        "def impl(df, x=None, y=None, kind='line', figsize=None, xlabel=None, \n"
        )
    usel__pbrbf += (
        '    ylabel=None, title=None, legend=True, fontsize=None, \n')
    usel__pbrbf += '    xticks=None, yticks=None, ax=None):\n'
    if is_overload_none(ax):
        usel__pbrbf += '   fig, ax = plt.subplots()\n'
    else:
        usel__pbrbf += '   fig = ax.get_figure()\n'
    if not is_overload_none(figsize):
        usel__pbrbf += '   fig.set_figwidth(figsize[0])\n'
        usel__pbrbf += '   fig.set_figheight(figsize[1])\n'
    if is_overload_none(xlabel):
        usel__pbrbf += '   xlabel = x\n'
    usel__pbrbf += '   ax.set_xlabel(xlabel)\n'
    if is_overload_none(ylabel):
        usel__pbrbf += '   ylabel = y\n'
    else:
        usel__pbrbf += '   ax.set_ylabel(ylabel)\n'
    if not is_overload_none(title):
        usel__pbrbf += '   ax.set_title(title)\n'
    if not is_overload_none(fontsize):
        usel__pbrbf += '   ax.tick_params(labelsize=fontsize)\n'
    kind = get_overload_const_str(kind)
    if kind == 'line':
        if is_overload_none(x) and is_overload_none(y):
            for i in range(len(df.columns)):
                if isinstance(df.data[i], (types.Array, IntegerArrayType)
                    ) and isinstance(df.data[i].dtype, (types.Integer,
                    types.Float)):
                    usel__pbrbf += (
                        f'   ax.plot(df.iloc[:, {i}], label=df.columns[{i}])\n'
                        )
        elif is_overload_none(x):
            usel__pbrbf += '   ax.plot(df[y], label=y)\n'
        elif is_overload_none(y):
            xnqw__eyuih = get_overload_const_str(x)
            kknu__sbg = df.columns.index(xnqw__eyuih)
            for i in range(len(df.columns)):
                if isinstance(df.data[i], (types.Array, IntegerArrayType)
                    ) and isinstance(df.data[i].dtype, (types.Integer,
                    types.Float)):
                    if kknu__sbg != i:
                        usel__pbrbf += f"""   ax.plot(df[x], df.iloc[:, {i}], label=df.columns[{i}])
"""
        else:
            usel__pbrbf += '   ax.plot(df[x], df[y], label=y)\n'
    elif kind == 'scatter':
        legend = False
        usel__pbrbf += '   ax.scatter(df[x], df[y], s=20)\n'
        usel__pbrbf += '   ax.set_ylabel(ylabel)\n'
    if not is_overload_none(xticks):
        usel__pbrbf += '   ax.set_xticks(xticks)\n'
    if not is_overload_none(yticks):
        usel__pbrbf += '   ax.set_yticks(yticks)\n'
    if is_overload_true(legend):
        usel__pbrbf += '   ax.legend()\n'
    usel__pbrbf += '   return ax\n'
    ueciy__bmwpg = {}
    exec(usel__pbrbf, {'bodo': bodo, 'plt': plt}, ueciy__bmwpg)
    impl = ueciy__bmwpg['impl']
    return impl


@lower_builtin('df.plot', DataFrameType, types.VarArg(types.Any))
def dataframe_plot_low(context, builder, sig, args):
    impl = overload_dataframe_plot(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


def is_df_values_numpy_supported_dftyp(df_typ):
    for bmtim__ftcc in df_typ.data:
        if not (isinstance(bmtim__ftcc, IntegerArrayType) or isinstance(
            bmtim__ftcc.dtype, types.Number) or bmtim__ftcc.dtype in (bodo.
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
        kutbg__vqpi = args[0]
        inajq__zrt = args[1].literal_value
        val = args[2]
        assert val != types.unknown
        foko__nzin = kutbg__vqpi
        check_runtime_cols_unsupported(kutbg__vqpi, 'set_df_col()')
        if isinstance(kutbg__vqpi, DataFrameType):
            index = kutbg__vqpi.index
            if len(kutbg__vqpi.columns) == 0:
                index = bodo.hiframes.pd_index_ext.RangeIndexType(types.none)
            if isinstance(val, SeriesType):
                if len(kutbg__vqpi.columns) == 0:
                    index = val.index
                val = val.data
            if is_pd_index_type(val):
                val = bodo.utils.typing.get_index_data_arr_types(val)[0]
            if isinstance(val, types.List):
                val = dtype_to_array_type(val.dtype)
            if not is_array_typ(val):
                val = dtype_to_array_type(val)
            if inajq__zrt in kutbg__vqpi.columns:
                dgw__zpqk = kutbg__vqpi.columns
                xqq__xfqq = kutbg__vqpi.columns.index(inajq__zrt)
                rpxec__zygbx = list(kutbg__vqpi.data)
                rpxec__zygbx[xqq__xfqq] = val
                rpxec__zygbx = tuple(rpxec__zygbx)
            else:
                dgw__zpqk = kutbg__vqpi.columns + (inajq__zrt,)
                rpxec__zygbx = kutbg__vqpi.data + (val,)
            foko__nzin = DataFrameType(rpxec__zygbx, index, dgw__zpqk,
                kutbg__vqpi.dist, kutbg__vqpi.is_table_format)
        return foko__nzin(*args)


SetDfColInfer.prefer_literal = True


def _parse_query_expr(expr, env, columns, cleaned_columns, index_name=None,
    join_cleaned_cols=()):
    qlz__cfr = {}

    def _rewrite_membership_op(self, node, left, right):
        pmpe__kxszu = node.op
        op = self.visit(pmpe__kxszu)
        return op, pmpe__kxszu, left, right

    def _maybe_evaluate_binop(self, op, op_class, lhs, rhs, eval_in_python=
        ('in', 'not in'), maybe_eval_in_python=('==', '!=', '<', '>', '<=',
        '>=')):
        res = op(lhs, rhs)
        return res
    lmj__hal = []


    class NewFuncNode(pd.core.computation.ops.FuncNode):

        def __init__(self, name):
            if (name not in pd.core.computation.ops.MATHOPS or pd.core.
                computation.check._NUMEXPR_INSTALLED and pd.core.
                computation.check_NUMEXPR_VERSION < pd.core.computation.ops
                .LooseVersion('2.6.9') and name in ('floor', 'ceil')):
                if name not in lmj__hal:
                    raise BodoError('"{0}" is not a supported function'.
                        format(name))
            self.name = name
            if name in lmj__hal:
                self.func = name
            else:
                self.func = getattr(np, name)

        def __call__(self, *args):
            return pd.core.computation.ops.MathCall(self, args)

        def __repr__(self):
            return pd.io.formats.printing.pprint_thing(self.name)

    def visit_Attribute(self, node, **kwargs):
        qqkq__arpo = node.attr
        value = node.value
        oohdn__rlbbr = pd.core.computation.ops.LOCAL_TAG
        if qqkq__arpo in ('str', 'dt'):
            try:
                ccbfm__ywpp = str(self.visit(value))
            except pd.core.computation.ops.UndefinedVariableError as srgvy__tjoq:
                col_name = srgvy__tjoq.args[0].split("'")[1]
                raise BodoError(
                    'df.query(): column {} is not found in dataframe columns {}'
                    .format(col_name, columns))
        else:
            ccbfm__ywpp = str(self.visit(value))
        bqo__mabp = ccbfm__ywpp, qqkq__arpo
        if bqo__mabp in join_cleaned_cols:
            qqkq__arpo = join_cleaned_cols[bqo__mabp]
        name = ccbfm__ywpp + '.' + qqkq__arpo
        if name.startswith(oohdn__rlbbr):
            name = name[len(oohdn__rlbbr):]
        if qqkq__arpo in ('str', 'dt'):
            dshl__avz = columns[cleaned_columns.index(ccbfm__ywpp)]
            qlz__cfr[dshl__avz] = ccbfm__ywpp
            self.env.scope[name] = 0
            return self.term_type(oohdn__rlbbr + name, self.env)
        lmj__hal.append(name)
        return NewFuncNode(name)

    def __str__(self):
        if isinstance(self.value, list):
            return '{}'.format(self.value)
        if isinstance(self.value, str):
            return "'{}'".format(self.value)
        return pd.io.formats.printing.pprint_thing(self.name)

    def math__str__(self):
        if self.op in lmj__hal:
            return pd.io.formats.printing.pprint_thing('{0}({1})'.format(
                self.op, ','.join(map(str, self.operands))))
        spj__evt = map(lambda a:
            'bodo.hiframes.pd_series_ext.get_series_data({})'.format(str(a)
            ), self.operands)
        op = 'np.{}'.format(self.op)
        inajq__zrt = (
            'bodo.hiframes.pd_index_ext.init_range_index(0, len({}), 1, None)'
            .format(str(self.operands[0])))
        return pd.io.formats.printing.pprint_thing(
            'bodo.hiframes.pd_series_ext.init_series({0}({1}), {2})'.format
            (op, ','.join(spj__evt), inajq__zrt))

    def op__str__(self):
        kqw__jdeff = ('({0})'.format(pd.io.formats.printing.pprint_thing(
            wru__edwkr)) for wru__edwkr in self.operands)
        if self.op == 'in':
            return pd.io.formats.printing.pprint_thing(
                'bodo.hiframes.pd_dataframe_ext.val_isin_dummy({})'.format(
                ', '.join(kqw__jdeff)))
        if self.op == 'not in':
            return pd.io.formats.printing.pprint_thing(
                'bodo.hiframes.pd_dataframe_ext.val_notin_dummy({})'.format
                (', '.join(kqw__jdeff)))
        return pd.io.formats.printing.pprint_thing(' {0} '.format(self.op).
            join(kqw__jdeff))
    obclh__wxva = (pd.core.computation.expr.BaseExprVisitor.
        _rewrite_membership_op)
    hrj__tukji = pd.core.computation.expr.BaseExprVisitor._maybe_evaluate_binop
    iqf__tec = pd.core.computation.expr.BaseExprVisitor.visit_Attribute
    yfhul__yhk = (pd.core.computation.expr.BaseExprVisitor.
        _maybe_downcast_constants)
    fye__kansu = pd.core.computation.ops.Term.__str__
    oml__yquq = pd.core.computation.ops.MathCall.__str__
    gunup__hzm = pd.core.computation.ops.Op.__str__
    gpax__kradn = pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops
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
        azf__thh = pd.core.computation.expr.Expr(expr, env=env)
        qaw__yyyi = str(azf__thh)
    except pd.core.computation.ops.UndefinedVariableError as srgvy__tjoq:
        if not is_overload_none(index_name) and get_overload_const_str(
            index_name) == srgvy__tjoq.args[0].split("'")[1]:
            raise BodoError(
                "df.query(): Refering to named index ('{}') by name is not supported"
                .format(get_overload_const_str(index_name)))
        else:
            raise BodoError(f'df.query(): undefined variable, {srgvy__tjoq}')
    finally:
        pd.core.computation.expr.BaseExprVisitor._rewrite_membership_op = (
            obclh__wxva)
        pd.core.computation.expr.BaseExprVisitor._maybe_evaluate_binop = (
            hrj__tukji)
        pd.core.computation.expr.BaseExprVisitor.visit_Attribute = iqf__tec
        (pd.core.computation.expr.BaseExprVisitor._maybe_downcast_constants
            ) = yfhul__yhk
        pd.core.computation.ops.Term.__str__ = fye__kansu
        pd.core.computation.ops.MathCall.__str__ = oml__yquq
        pd.core.computation.ops.Op.__str__ = gunup__hzm
        pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops = (
            gpax__kradn)
    fksla__gtxt = pd.core.computation.parsing.clean_column_name
    qlz__cfr.update({gtcss__vpd: fksla__gtxt(gtcss__vpd) for gtcss__vpd in
        columns if fksla__gtxt(gtcss__vpd) in azf__thh.names})
    return azf__thh, qaw__yyyi, qlz__cfr


class DataFrameTupleIterator(types.SimpleIteratorType):

    def __init__(self, col_names, arr_typs):
        self.array_types = arr_typs
        self.col_names = col_names
        iiilm__oyjem = ['{}={}'.format(col_names[i], arr_typs[i]) for i in
            range(len(col_names))]
        name = 'itertuples({})'.format(','.join(iiilm__oyjem))
        ley__gxyff = namedtuple('Pandas', col_names)
        thns__xtg = types.NamedTuple([_get_series_dtype(a) for a in
            arr_typs], ley__gxyff)
        super(DataFrameTupleIterator, self).__init__(name, thns__xtg)

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
        icy__nct = [if_series_to_array_type(a) for a in args[len(args) // 2:]]
        assert 'Index' not in col_names[0]
        col_names = ['Index'] + col_names
        icy__nct = [types.Array(types.int64, 1, 'C')] + icy__nct
        hdpnu__hhk = DataFrameTupleIterator(col_names, icy__nct)
        return hdpnu__hhk(*args)


TypeIterTuples.prefer_literal = True


@register_model(DataFrameTupleIterator)
class DataFrameTupleIteratorModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        vyyq__pdg = [('index', types.EphemeralPointer(types.uintp))] + [(
            'array{}'.format(i), arr) for i, arr in enumerate(fe_type.
            array_types[1:])]
        super(DataFrameTupleIteratorModel, self).__init__(dmm, fe_type,
            vyyq__pdg)

    def from_return(self, builder, value):
        return value


@lower_builtin(get_itertuples, types.VarArg(types.Any))
def get_itertuples_impl(context, builder, sig, args):
    ahjb__jwuz = args[len(args) // 2:]
    ueu__htlf = sig.args[len(sig.args) // 2:]
    ktqw__hwsj = context.make_helper(builder, sig.return_type)
    lgl__hxetg = context.get_constant(types.intp, 0)
    guh__ptef = cgutils.alloca_once_value(builder, lgl__hxetg)
    ktqw__hwsj.index = guh__ptef
    for i, arr in enumerate(ahjb__jwuz):
        setattr(ktqw__hwsj, 'array{}'.format(i), arr)
    for arr, arr_typ in zip(ahjb__jwuz, ueu__htlf):
        context.nrt.incref(builder, arr_typ, arr)
    res = ktqw__hwsj._getvalue()
    return impl_ret_new_ref(context, builder, sig.return_type, res)


@lower_builtin('getiter', DataFrameTupleIterator)
def getiter_itertuples(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@lower_builtin('iternext', DataFrameTupleIterator)
@iternext_impl(RefType.UNTRACKED)
def iternext_itertuples(context, builder, sig, args, result):
    pzvt__tjzf, = sig.args
    nur__nuy, = args
    ktqw__hwsj = context.make_helper(builder, pzvt__tjzf, value=nur__nuy)
    uig__pciwv = signature(types.intp, pzvt__tjzf.array_types[1])
    xoew__twtol = context.compile_internal(builder, lambda a: len(a),
        uig__pciwv, [ktqw__hwsj.array0])
    index = builder.load(ktqw__hwsj.index)
    eqjmy__kdgt = builder.icmp(lc.ICMP_SLT, index, xoew__twtol)
    result.set_valid(eqjmy__kdgt)
    with builder.if_then(eqjmy__kdgt):
        values = [index]
        for i, arr_typ in enumerate(pzvt__tjzf.array_types[1:]):
            akprv__pjbhf = getattr(ktqw__hwsj, 'array{}'.format(i))
            if arr_typ == types.Array(types.NPDatetime('ns'), 1, 'C'):
                dxqx__kuw = signature(pd_timestamp_type, arr_typ, types.intp)
                val = context.compile_internal(builder, lambda a, i: bodo.
                    hiframes.pd_timestamp_ext.
                    convert_datetime64_to_timestamp(np.int64(a[i])),
                    dxqx__kuw, [akprv__pjbhf, index])
            else:
                dxqx__kuw = signature(arr_typ.dtype, arr_typ, types.intp)
                val = context.compile_internal(builder, lambda a, i: a[i],
                    dxqx__kuw, [akprv__pjbhf, index])
            values.append(val)
        value = context.make_tuple(builder, pzvt__tjzf.yield_type, values)
        result.yield_(value)
        mjl__zeqhi = cgutils.increment_index(builder, index)
        builder.store(mjl__zeqhi, ktqw__hwsj.index)


def _analyze_op_pair_first(self, scope, equiv_set, expr, lhs):
    typ = self.typemap[expr.value.name].first_type
    if not isinstance(typ, types.NamedTuple):
        return None
    lhs = ir.Var(scope, mk_unique_var('tuple_var'), expr.loc)
    self.typemap[lhs.name] = typ
    rhs = ir.Expr.pair_first(expr.value, expr.loc)
    czfnw__dxnp = ir.Assign(rhs, lhs, expr.loc)
    vbgaa__acqyy = lhs
    oskr__nbciv = []
    ptss__maby = []
    fbsp__ehw = typ.count
    for i in range(fbsp__ehw):
        mkooz__swp = ir.Var(vbgaa__acqyy.scope, mk_unique_var('{}_size{}'.
            format(vbgaa__acqyy.name, i)), vbgaa__acqyy.loc)
        stt__ncb = ir.Expr.static_getitem(lhs, i, None, vbgaa__acqyy.loc)
        self.calltypes[stt__ncb] = None
        oskr__nbciv.append(ir.Assign(stt__ncb, mkooz__swp, vbgaa__acqyy.loc))
        self._define(equiv_set, mkooz__swp, types.intp, stt__ncb)
        ptss__maby.append(mkooz__swp)
    eroq__ltp = tuple(ptss__maby)
    return numba.parfors.array_analysis.ArrayAnalysis.AnalyzeResult(shape=
        eroq__ltp, pre=[czfnw__dxnp] + oskr__nbciv)


numba.parfors.array_analysis.ArrayAnalysis._analyze_op_pair_first = (
    _analyze_op_pair_first)
