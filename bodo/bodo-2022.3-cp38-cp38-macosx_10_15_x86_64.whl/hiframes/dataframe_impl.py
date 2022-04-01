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
        cpzru__asehb = f'bodo.utils.conversion.coerce_to_array({col_names})'
        return (
            f'bodo.hiframes.pd_index_ext.init_binary_str_index({cpzru__asehb})\n'
            )
    elif all(isinstance(a, (int, float)) for a in col_names):
        arr = f'bodo.utils.conversion.coerce_to_array({col_names})'
        return f'bodo.hiframes.pd_index_ext.init_numeric_index({arr})\n'
    else:
        return f'bodo.hiframes.pd_index_ext.init_heter_index({col_names})\n'


@overload_attribute(DataFrameType, 'columns', inline='always')
def overload_dataframe_columns(df):
    aws__itxkg = 'def impl(df):\n'
    if df.has_runtime_cols:
        aws__itxkg += (
            '  return bodo.hiframes.pd_dataframe_ext.get_dataframe_column_names(df)\n'
            )
    else:
        cowvu__tyvel = (bodo.hiframes.dataframe_impl.
            generate_col_to_index_func_text(df.columns))
        aws__itxkg += f'  return {cowvu__tyvel}'
    xcyfk__phy = {}
    exec(aws__itxkg, {'bodo': bodo}, xcyfk__phy)
    impl = xcyfk__phy['impl']
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
    ioz__fzl = len(df.columns)
    rcj__ohq = set(i for i in range(ioz__fzl) if isinstance(df.data[i],
        IntegerArrayType))
    data_args = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(i, '.astype(float)' if i in rcj__ohq else '') for i in range
        (ioz__fzl))
    aws__itxkg = 'def f(df):\n'.format()
    aws__itxkg += '    return np.stack(({},), 1)\n'.format(data_args)
    xcyfk__phy = {}
    exec(aws__itxkg, {'bodo': bodo, 'np': np}, xcyfk__phy)
    blk__mezef = xcyfk__phy['f']
    return blk__mezef


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
    qto__lty = {'dtype': dtype, 'na_value': na_value}
    olakn__senkx = {'dtype': None, 'na_value': _no_input}
    check_unsupported_args('DataFrame.to_numpy', qto__lty, olakn__senkx,
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
            jrxw__dcif = bodo.hiframes.table.compute_num_runtime_columns(t)
            return jrxw__dcif * len(t)
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
            jrxw__dcif = bodo.hiframes.table.compute_num_runtime_columns(t)
            return len(t), jrxw__dcif
        return impl
    ncols = len(df.columns)
    return lambda df: (len(df), types.int64(ncols))


@overload_attribute(DataFrameType, 'dtypes')
def overload_dataframe_dtypes(df):
    check_runtime_cols_unsupported(df, 'DataFrame.dtypes')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.dtypes')
    aws__itxkg = 'def impl(df):\n'
    data = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).dtype\n'
         for i in range(len(df.columns)))
    uxgi__qsyou = ',' if len(df.columns) == 1 else ''
    index = f'bodo.hiframes.pd_index_ext.init_heter_index({df.columns})'
    aws__itxkg += f"""  return bodo.hiframes.pd_series_ext.init_series(({data}{uxgi__qsyou}), {index}, None)
"""
    xcyfk__phy = {}
    exec(aws__itxkg, {'bodo': bodo}, xcyfk__phy)
    impl = xcyfk__phy['impl']
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
    qto__lty = {'copy': copy, 'errors': errors}
    olakn__senkx = {'copy': True, 'errors': 'raise'}
    check_unsupported_args('df.astype', qto__lty, olakn__senkx,
        package_name='pandas', module_name='DataFrame')
    if dtype == types.unicode_type:
        raise_bodo_error(
            "DataFrame.astype(): 'dtype' when passed as string must be a constant value"
            )
    extra_globals = None
    if _bodo_object_typeref is not None:
        assert isinstance(_bodo_object_typeref, types.TypeRef
            ), 'Bodo schema used in DataFrame.astype should be a TypeRef'
        lkugl__cwna = _bodo_object_typeref.instance_type
        assert isinstance(lkugl__cwna, DataFrameType
            ), 'Bodo schema used in DataFrame.astype is only supported for DataFrame schemas'
        extra_globals = {}
        kucni__rfuzi = {}
        for i, name in enumerate(lkugl__cwna.columns):
            arr_typ = lkugl__cwna.data[i]
            if isinstance(arr_typ, IntegerArrayType):
                ejj__oyk = bodo.libs.int_arr_ext.IntDtype(arr_typ.dtype)
            elif arr_typ == boolean_array:
                ejj__oyk = boolean_dtype
            else:
                ejj__oyk = arr_typ.dtype
            extra_globals[f'_bodo_schema{i}'] = ejj__oyk
            kucni__rfuzi[name] = f'_bodo_schema{i}'
        data_args = ', '.join(
            f'bodo.utils.conversion.fix_arr_dtype(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), {kucni__rfuzi[pwc__oyq]}, copy, nan_to_str=_bodo_nan_to_str, from_series=True)'
             if pwc__oyq in kucni__rfuzi else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})' for
            i, pwc__oyq in enumerate(df.columns))
    elif is_overload_constant_dict(dtype) or is_overload_constant_series(dtype
        ):
        ppvf__bsr = get_overload_constant_dict(dtype
            ) if is_overload_constant_dict(dtype) else dict(
            get_overload_constant_series(dtype))
        data_args = ', '.join(
            f'bodo.utils.conversion.fix_arr_dtype(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), {_get_dtype_str(ppvf__bsr[pwc__oyq])}, copy, nan_to_str=_bodo_nan_to_str, from_series=True)'
             if pwc__oyq in ppvf__bsr else
            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})' for
            i, pwc__oyq in enumerate(df.columns))
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
    lbr__bjdiw = []
    for i in range(len(df.columns)):
        arr = f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})'
        if is_overload_true(deep):
            lbr__bjdiw.append(arr + '.copy()')
        elif is_overload_false(deep):
            lbr__bjdiw.append(arr)
        else:
            lbr__bjdiw.append(f'{arr}.copy() if deep else {arr}')
    header = 'def impl(df, deep=True):\n'
    return _gen_init_df(header, df.columns, ', '.join(lbr__bjdiw))


@overload_method(DataFrameType, 'rename', inline='always', no_unliteral=True)
def overload_dataframe_rename(df, mapper=None, index=None, columns=None,
    axis=None, copy=True, inplace=False, level=None, errors='ignore',
    _bodo_transformed=False):
    check_runtime_cols_unsupported(df, 'DataFrame.rename()')
    handle_inplace_df_type_change(inplace, _bodo_transformed, 'rename')
    qto__lty = {'index': index, 'level': level, 'errors': errors}
    olakn__senkx = {'index': None, 'level': None, 'errors': 'ignore'}
    check_unsupported_args('DataFrame.rename', qto__lty, olakn__senkx,
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
        flmng__dfifg = get_overload_constant_dict(mapper)
    elif not is_overload_none(columns):
        if not is_overload_none(axis):
            raise BodoError(
                "DataFrame.rename(): Cannot specify both 'axis' and 'columns'")
        if not is_overload_constant_dict(columns):
            raise_bodo_error(
                "'columns' argument to DataFrame.rename() should be a constant dictionary"
                )
        flmng__dfifg = get_overload_constant_dict(columns)
    else:
        raise_bodo_error(
            "DataFrame.rename(): must pass columns either via 'mapper' and 'axis'=1 or 'columns'"
            )
    tykx__rax = [flmng__dfifg.get(df.columns[i], df.columns[i]) for i in
        range(len(df.columns))]
    lbr__bjdiw = []
    for i in range(len(df.columns)):
        arr = f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})'
        if is_overload_true(copy):
            lbr__bjdiw.append(arr + '.copy()')
        elif is_overload_false(copy):
            lbr__bjdiw.append(arr)
        else:
            lbr__bjdiw.append(f'{arr}.copy() if copy else {arr}')
    header = """def impl(df, mapper=None, index=None, columns=None, axis=None, copy=True, inplace=False, level=None, errors='ignore', _bodo_transformed=False):
"""
    return _gen_init_df(header, tykx__rax, ', '.join(lbr__bjdiw))


@overload_method(DataFrameType, 'filter', no_unliteral=True)
def overload_dataframe_filter(df, items=None, like=None, regex=None, axis=None
    ):
    check_runtime_cols_unsupported(df, 'DataFrame.filter()')
    szdgd__fuah = not is_overload_none(items)
    stum__qrn = not is_overload_none(like)
    irm__jsyzl = not is_overload_none(regex)
    qnek__uoxv = szdgd__fuah ^ stum__qrn ^ irm__jsyzl
    shmr__fsk = not (szdgd__fuah or stum__qrn or irm__jsyzl)
    if shmr__fsk:
        raise BodoError(
            'DataFrame.filter(): one of keyword arguments `items`, `like`, and `regex` must be supplied'
            )
    if not qnek__uoxv:
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
        itjvk__dfmby = 0 if axis == 'index' else 1
    elif is_overload_constant_int(axis):
        axis = get_overload_const_int(axis)
        if axis not in {0, 1}:
            raise_bodo_error(
                'DataFrame.filter(): keyword arguments `axis` must be either 0 or 1 if integer'
                )
        itjvk__dfmby = axis
    else:
        raise_bodo_error(
            'DataFrame.filter(): keyword arguments `axis` must be constant string or integer'
            )
    assert itjvk__dfmby in {0, 1}
    aws__itxkg = (
        'def impl(df, items=None, like=None, regex=None, axis=None):\n')
    if itjvk__dfmby == 0:
        raise BodoError(
            'DataFrame.filter(): filtering based on index is not supported.')
    if itjvk__dfmby == 1:
        ivqcb__riyw = []
        klq__sjt = []
        opa__fyes = []
        if szdgd__fuah:
            if is_overload_constant_list(items):
                byhss__uiqrq = get_overload_const_list(items)
            else:
                raise BodoError(
                    "Dataframe.filter(): argument 'items' must be a list of constant strings."
                    )
        if stum__qrn:
            if is_overload_constant_str(like):
                xqh__ypma = get_overload_const_str(like)
            else:
                raise BodoError(
                    "Dataframe.filter(): argument 'like' must be a constant string."
                    )
        if irm__jsyzl:
            if is_overload_constant_str(regex):
                kdbml__lezmc = get_overload_const_str(regex)
                vhwb__youu = re.compile(kdbml__lezmc)
            else:
                raise BodoError(
                    "Dataframe.filter(): argument 'regex' must be a constant string."
                    )
        for i, pwc__oyq in enumerate(df.columns):
            if not is_overload_none(items
                ) and pwc__oyq in byhss__uiqrq or not is_overload_none(like
                ) and xqh__ypma in str(pwc__oyq) or not is_overload_none(regex
                ) and vhwb__youu.search(str(pwc__oyq)):
                klq__sjt.append(pwc__oyq)
                opa__fyes.append(i)
        for i in opa__fyes:
            uhyu__ovcwu = f'data_{i}'
            ivqcb__riyw.append(uhyu__ovcwu)
            aws__itxkg += f"""  {uhyu__ovcwu} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})
"""
        data_args = ', '.join(ivqcb__riyw)
        return _gen_init_df(aws__itxkg, klq__sjt, data_args)


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
    wbebg__kcg = is_overload_none(include)
    yyxgu__ryze = is_overload_none(exclude)
    lhmhg__rnss = 'DataFrame.select_dtypes'
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.select_dtypes()')
    if wbebg__kcg and yyxgu__ryze:
        raise_bodo_error(
            'DataFrame.select_dtypes() At least one of include or exclude must not be none'
            )

    def is_legal_input(elem):
        return is_overload_constant_str(elem) or isinstance(elem, types.
            DTypeSpec) or isinstance(elem, types.Function)
    if not wbebg__kcg:
        if is_overload_constant_list(include):
            include = get_overload_const_list(include)
            bxqn__tvy = [dtype_to_array_type(parse_dtype(elem, lhmhg__rnss)
                ) for elem in include]
        elif is_legal_input(include):
            bxqn__tvy = [dtype_to_array_type(parse_dtype(include, lhmhg__rnss))
                ]
        else:
            raise_bodo_error(
                'DataFrame.select_dtypes() only supports constant strings or types as arguments'
                )
        bxqn__tvy = get_nullable_and_non_nullable_types(bxqn__tvy)
        kcrzc__ojv = tuple(pwc__oyq for i, pwc__oyq in enumerate(df.columns
            ) if df.data[i] in bxqn__tvy)
    else:
        kcrzc__ojv = df.columns
    if not yyxgu__ryze:
        if is_overload_constant_list(exclude):
            exclude = get_overload_const_list(exclude)
            byen__pbr = [dtype_to_array_type(parse_dtype(elem, lhmhg__rnss)
                ) for elem in exclude]
        elif is_legal_input(exclude):
            byen__pbr = [dtype_to_array_type(parse_dtype(exclude, lhmhg__rnss))
                ]
        else:
            raise_bodo_error(
                'DataFrame.select_dtypes() only supports constant strings or types as arguments'
                )
        byen__pbr = get_nullable_and_non_nullable_types(byen__pbr)
        kcrzc__ojv = tuple(pwc__oyq for pwc__oyq in kcrzc__ojv if df.data[
            df.columns.index(pwc__oyq)] not in byen__pbr)
    data_args = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(pwc__oyq)})'
         for pwc__oyq in kcrzc__ojv)
    header = 'def impl(df, include=None, exclude=None):\n'
    return _gen_init_df(header, kcrzc__ojv, data_args)


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
    dhlki__bujxi = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if not isinstance(df.index, DatetimeIndexType):
        raise BodoError(
            'DataFrame.first(): only supports a DatetimeIndex index')
    if types.unliteral(offset) not in dhlki__bujxi:
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
    dhlki__bujxi = (types.unicode_type, bodo.month_begin_type, bodo.
        month_end_type, bodo.week_type, bodo.date_offset_type)
    if not isinstance(df.index, DatetimeIndexType):
        raise BodoError('DataFrame.last(): only supports a DatetimeIndex index'
            )
    if types.unliteral(offset) not in dhlki__bujxi:
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
    aws__itxkg = 'def impl(df, values):\n'
    epytk__peji = {}
    bvp__ttyhp = False
    if isinstance(values, DataFrameType):
        bvp__ttyhp = True
        for i, pwc__oyq in enumerate(df.columns):
            if pwc__oyq in values.columns:
                isr__zhthr = 'val{}'.format(i)
                aws__itxkg += (
                    """  {} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(values, {})
"""
                    .format(isr__zhthr, values.columns.index(pwc__oyq)))
                epytk__peji[pwc__oyq] = isr__zhthr
    elif is_iterable_type(values) and not isinstance(values, SeriesType):
        epytk__peji = {pwc__oyq: 'values' for pwc__oyq in df.columns}
    else:
        raise_bodo_error(f'pd.isin(): not supported for type {values}')
    data = []
    for i in range(len(df.columns)):
        isr__zhthr = 'data{}'.format(i)
        aws__itxkg += (
            '  {} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})\n'
            .format(isr__zhthr, i))
        data.append(isr__zhthr)
    nmtux__smwd = ['out{}'.format(i) for i in range(len(df.columns))]
    sdkro__bhnjp = """
  numba.parfors.parfor.init_prange()
  n = len({0})
  m = len({1})
  {2} = np.empty(n, np.bool_)
  for i in numba.parfors.parfor.internal_prange(n):
    {2}[i] = {0}[i] == {1}[i] if i < m else False
"""
    wtjy__uxx = """
  numba.parfors.parfor.init_prange()
  n = len({0})
  {2} = np.empty(n, np.bool_)
  for i in numba.parfors.parfor.internal_prange(n):
    {2}[i] = {0}[i] in {1}
"""
    zjn__iyxik = '  {} = np.zeros(len(df), np.bool_)\n'
    for i, (cname, vdp__tqm) in enumerate(zip(df.columns, data)):
        if cname in epytk__peji:
            nht__dcp = epytk__peji[cname]
            if bvp__ttyhp:
                aws__itxkg += sdkro__bhnjp.format(vdp__tqm, nht__dcp,
                    nmtux__smwd[i])
            else:
                aws__itxkg += wtjy__uxx.format(vdp__tqm, nht__dcp,
                    nmtux__smwd[i])
        else:
            aws__itxkg += zjn__iyxik.format(nmtux__smwd[i])
    return _gen_init_df(aws__itxkg, df.columns, ','.join(nmtux__smwd))


@overload_method(DataFrameType, 'abs', inline='always', no_unliteral=True)
def overload_dataframe_abs(df):
    check_runtime_cols_unsupported(df, 'DataFrame.abs()')
    for arr_typ in df.data:
        if not (isinstance(arr_typ.dtype, types.Number) or arr_typ.dtype ==
            bodo.timedelta64ns):
            raise_bodo_error(
                f'DataFrame.abs(): Only supported for numeric and Timedelta. Encountered array with dtype {arr_typ.dtype}'
                )
    ioz__fzl = len(df.columns)
    data_args = ', '.join(
        'np.abs(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}))'
        .format(i) for i in range(ioz__fzl))
    header = 'def impl(df):\n'
    return _gen_init_df(header, df.columns, data_args)


def overload_dataframe_corr(df, method='pearson', min_periods=1):
    bxpjo__kbh = [pwc__oyq for pwc__oyq, elfy__zxawf in zip(df.columns, df.
        data) if bodo.utils.typing._is_pandas_numeric_dtype(elfy__zxawf.dtype)]
    assert len(bxpjo__kbh) != 0
    tdw__rfwzs = ''
    if not any(elfy__zxawf == types.float64 for elfy__zxawf in df.data):
        tdw__rfwzs = '.astype(np.float64)'
    out__selsx = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(df.columns.index(pwc__oyq), '.astype(np.float64)' if 
        isinstance(df.data[df.columns.index(pwc__oyq)], IntegerArrayType) or
        df.data[df.columns.index(pwc__oyq)] == boolean_array else '') for
        pwc__oyq in bxpjo__kbh)
    encme__rfxd = 'np.stack(({},), 1){}'.format(out__selsx, tdw__rfwzs)
    data_args = ', '.join('res[:,{}]'.format(i) for i in range(len(bxpjo__kbh))
        )
    index = f'{generate_col_to_index_func_text(bxpjo__kbh)}\n'
    header = "def impl(df, method='pearson', min_periods=1):\n"
    header += '  mat = {}\n'.format(encme__rfxd)
    header += '  res = bodo.libs.array_kernels.nancorr(mat, 0, min_periods)\n'
    return _gen_init_df(header, bxpjo__kbh, data_args, index)


@lower_builtin('df.corr', DataFrameType, types.VarArg(types.Any))
def dataframe_corr_lower(context, builder, sig, args):
    impl = overload_dataframe_corr(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


@overload_method(DataFrameType, 'cov', inline='always', no_unliteral=True)
def overload_dataframe_cov(df, min_periods=None, ddof=1):
    check_runtime_cols_unsupported(df, 'DataFrame.cov()')
    icgbi__oqex = dict(ddof=ddof)
    glq__vnex = dict(ddof=1)
    check_unsupported_args('DataFrame.cov', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    nyx__hej = '1' if is_overload_none(min_periods) else 'min_periods'
    bxpjo__kbh = [pwc__oyq for pwc__oyq, elfy__zxawf in zip(df.columns, df.
        data) if bodo.utils.typing._is_pandas_numeric_dtype(elfy__zxawf.dtype)]
    if len(bxpjo__kbh) == 0:
        raise_bodo_error('DataFrame.cov(): requires non-empty dataframe')
    tdw__rfwzs = ''
    if not any(elfy__zxawf == types.float64 for elfy__zxawf in df.data):
        tdw__rfwzs = '.astype(np.float64)'
    out__selsx = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(df.columns.index(pwc__oyq), '.astype(np.float64)' if 
        isinstance(df.data[df.columns.index(pwc__oyq)], IntegerArrayType) or
        df.data[df.columns.index(pwc__oyq)] == boolean_array else '') for
        pwc__oyq in bxpjo__kbh)
    encme__rfxd = 'np.stack(({},), 1){}'.format(out__selsx, tdw__rfwzs)
    data_args = ', '.join('res[:,{}]'.format(i) for i in range(len(bxpjo__kbh))
        )
    index = f'pd.Index({bxpjo__kbh})\n'
    header = 'def impl(df, min_periods=None, ddof=1):\n'
    header += '  mat = {}\n'.format(encme__rfxd)
    header += '  res = bodo.libs.array_kernels.nancorr(mat, 1, {})\n'.format(
        nyx__hej)
    return _gen_init_df(header, bxpjo__kbh, data_args, index)


@overload_method(DataFrameType, 'count', inline='always', no_unliteral=True)
def overload_dataframe_count(df, axis=0, level=None, numeric_only=False):
    check_runtime_cols_unsupported(df, 'DataFrame.count()')
    icgbi__oqex = dict(axis=axis, level=level, numeric_only=numeric_only)
    glq__vnex = dict(axis=0, level=None, numeric_only=False)
    check_unsupported_args('DataFrame.count', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'bodo.libs.array_ops.array_op_count(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}))'
         for i in range(len(df.columns)))
    aws__itxkg = 'def impl(df, axis=0, level=None, numeric_only=False):\n'
    aws__itxkg += '  data = np.array([{}])\n'.format(data_args)
    cowvu__tyvel = (bodo.hiframes.dataframe_impl.
        generate_col_to_index_func_text(df.columns))
    aws__itxkg += (
        f'  return bodo.hiframes.pd_series_ext.init_series(data, {cowvu__tyvel})\n'
        )
    xcyfk__phy = {}
    exec(aws__itxkg, {'bodo': bodo, 'np': np}, xcyfk__phy)
    impl = xcyfk__phy['impl']
    return impl


@overload_method(DataFrameType, 'nunique', inline='always', no_unliteral=True)
def overload_dataframe_nunique(df, axis=0, dropna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.unique()')
    icgbi__oqex = dict(axis=axis)
    glq__vnex = dict(axis=0)
    if not is_overload_bool(dropna):
        raise BodoError('DataFrame.nunique: dropna must be a boolean value')
    check_unsupported_args('DataFrame.nunique', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'bodo.libs.array_kernels.nunique(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), dropna)'
         for i in range(len(df.columns)))
    aws__itxkg = 'def impl(df, axis=0, dropna=True):\n'
    aws__itxkg += '  data = np.asarray(({},))\n'.format(data_args)
    cowvu__tyvel = (bodo.hiframes.dataframe_impl.
        generate_col_to_index_func_text(df.columns))
    aws__itxkg += (
        f'  return bodo.hiframes.pd_series_ext.init_series(data, {cowvu__tyvel})\n'
        )
    xcyfk__phy = {}
    exec(aws__itxkg, {'bodo': bodo, 'np': np}, xcyfk__phy)
    impl = xcyfk__phy['impl']
    return impl


@overload_method(DataFrameType, 'prod', inline='always', no_unliteral=True)
@overload_method(DataFrameType, 'product', inline='always', no_unliteral=True)
def overload_dataframe_prod(df, axis=None, skipna=None, level=None,
    numeric_only=None, min_count=0):
    check_runtime_cols_unsupported(df, 'DataFrame.prod()')
    icgbi__oqex = dict(skipna=skipna, level=level, numeric_only=
        numeric_only, min_count=min_count)
    glq__vnex = dict(skipna=None, level=None, numeric_only=None, min_count=0)
    check_unsupported_args('DataFrame.prod', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.product()')
    return _gen_reduce_impl(df, 'prod', axis=axis)


@overload_method(DataFrameType, 'sum', inline='always', no_unliteral=True)
def overload_dataframe_sum(df, axis=None, skipna=None, level=None,
    numeric_only=None, min_count=0):
    check_runtime_cols_unsupported(df, 'DataFrame.sum()')
    icgbi__oqex = dict(skipna=skipna, level=level, numeric_only=
        numeric_only, min_count=min_count)
    glq__vnex = dict(skipna=None, level=None, numeric_only=None, min_count=0)
    check_unsupported_args('DataFrame.sum', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.sum()')
    return _gen_reduce_impl(df, 'sum', axis=axis)


@overload_method(DataFrameType, 'max', inline='always', no_unliteral=True)
def overload_dataframe_max(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.max()')
    icgbi__oqex = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    glq__vnex = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.max', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.max()')
    return _gen_reduce_impl(df, 'max', axis=axis)


@overload_method(DataFrameType, 'min', inline='always', no_unliteral=True)
def overload_dataframe_min(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.min()')
    icgbi__oqex = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    glq__vnex = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.min', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.min()')
    return _gen_reduce_impl(df, 'min', axis=axis)


@overload_method(DataFrameType, 'mean', inline='always', no_unliteral=True)
def overload_dataframe_mean(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.mean()')
    icgbi__oqex = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    glq__vnex = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.mean', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.mean()')
    return _gen_reduce_impl(df, 'mean', axis=axis)


@overload_method(DataFrameType, 'var', inline='always', no_unliteral=True)
def overload_dataframe_var(df, axis=None, skipna=None, level=None, ddof=1,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.var()')
    icgbi__oqex = dict(skipna=skipna, level=level, ddof=ddof, numeric_only=
        numeric_only)
    glq__vnex = dict(skipna=None, level=None, ddof=1, numeric_only=None)
    check_unsupported_args('DataFrame.var', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.var()')
    return _gen_reduce_impl(df, 'var', axis=axis)


@overload_method(DataFrameType, 'std', inline='always', no_unliteral=True)
def overload_dataframe_std(df, axis=None, skipna=None, level=None, ddof=1,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.std()')
    icgbi__oqex = dict(skipna=skipna, level=level, ddof=ddof, numeric_only=
        numeric_only)
    glq__vnex = dict(skipna=None, level=None, ddof=1, numeric_only=None)
    check_unsupported_args('DataFrame.std', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.std()')
    return _gen_reduce_impl(df, 'std', axis=axis)


@overload_method(DataFrameType, 'median', inline='always', no_unliteral=True)
def overload_dataframe_median(df, axis=None, skipna=None, level=None,
    numeric_only=None):
    check_runtime_cols_unsupported(df, 'DataFrame.median()')
    icgbi__oqex = dict(skipna=skipna, level=level, numeric_only=numeric_only)
    glq__vnex = dict(skipna=None, level=None, numeric_only=None)
    check_unsupported_args('DataFrame.median', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.median()')
    return _gen_reduce_impl(df, 'median', axis=axis)


@overload_method(DataFrameType, 'quantile', inline='always', no_unliteral=True)
def overload_dataframe_quantile(df, q=0.5, axis=0, numeric_only=True,
    interpolation='linear'):
    check_runtime_cols_unsupported(df, 'DataFrame.quantile()')
    icgbi__oqex = dict(numeric_only=numeric_only, interpolation=interpolation)
    glq__vnex = dict(numeric_only=True, interpolation='linear')
    check_unsupported_args('DataFrame.quantile', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.quantile()')
    return _gen_reduce_impl(df, 'quantile', 'q', axis=axis)


@overload_method(DataFrameType, 'idxmax', inline='always', no_unliteral=True)
def overload_dataframe_idxmax(df, axis=0, skipna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.idxmax()')
    icgbi__oqex = dict(axis=axis, skipna=skipna)
    glq__vnex = dict(axis=0, skipna=True)
    check_unsupported_args('DataFrame.idxmax', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.idxmax()')
    for vcgfx__gnefm in df.data:
        if not (bodo.utils.utils.is_np_array_typ(vcgfx__gnefm) and (
            vcgfx__gnefm.dtype in [bodo.datetime64ns, bodo.timedelta64ns] or
            isinstance(vcgfx__gnefm.dtype, (types.Number, types.Boolean))) or
            isinstance(vcgfx__gnefm, (bodo.IntegerArrayType, bodo.
            CategoricalArrayType)) or vcgfx__gnefm in [bodo.boolean_array,
            bodo.datetime_date_array_type]):
            raise BodoError(
                f'DataFrame.idxmax() only supported for numeric column types. Column type: {vcgfx__gnefm} not supported.'
                )
        if isinstance(vcgfx__gnefm, bodo.CategoricalArrayType
            ) and not vcgfx__gnefm.dtype.ordered:
            raise BodoError(
                'DataFrame.idxmax(): categorical columns must be ordered')
    return _gen_reduce_impl(df, 'idxmax', axis=axis)


@overload_method(DataFrameType, 'idxmin', inline='always', no_unliteral=True)
def overload_dataframe_idxmin(df, axis=0, skipna=True):
    check_runtime_cols_unsupported(df, 'DataFrame.idxmin()')
    icgbi__oqex = dict(axis=axis, skipna=skipna)
    glq__vnex = dict(axis=0, skipna=True)
    check_unsupported_args('DataFrame.idxmin', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.idxmin()')
    for vcgfx__gnefm in df.data:
        if not (bodo.utils.utils.is_np_array_typ(vcgfx__gnefm) and (
            vcgfx__gnefm.dtype in [bodo.datetime64ns, bodo.timedelta64ns] or
            isinstance(vcgfx__gnefm.dtype, (types.Number, types.Boolean))) or
            isinstance(vcgfx__gnefm, (bodo.IntegerArrayType, bodo.
            CategoricalArrayType)) or vcgfx__gnefm in [bodo.boolean_array,
            bodo.datetime_date_array_type]):
            raise BodoError(
                f'DataFrame.idxmin() only supported for numeric column types. Column type: {vcgfx__gnefm} not supported.'
                )
        if isinstance(vcgfx__gnefm, bodo.CategoricalArrayType
            ) and not vcgfx__gnefm.dtype.ordered:
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
        bxpjo__kbh = tuple(pwc__oyq for pwc__oyq, elfy__zxawf in zip(df.
            columns, df.data) if bodo.utils.typing._is_pandas_numeric_dtype
            (elfy__zxawf.dtype))
        out_colnames = bxpjo__kbh
    assert len(out_colnames) != 0
    try:
        if func_name in ('idxmax', 'idxmin') and axis == 0:
            comm_dtype = None
        else:
            huod__fes = [numba.np.numpy_support.as_dtype(df.data[df.columns
                .index(pwc__oyq)].dtype) for pwc__oyq in out_colnames]
            comm_dtype = numba.np.numpy_support.from_dtype(np.
                find_common_type(huod__fes, []))
    except NotImplementedError as fpx__whla:
        raise BodoError(
            f'Dataframe.{func_name}() with column types: {df.data} could not be merged to a common type.'
            )
    dtn__zhb = ''
    if func_name in ('sum', 'prod'):
        dtn__zhb = ', min_count=0'
    ddof = ''
    if func_name in ('var', 'std'):
        ddof = 'ddof=1, '
    aws__itxkg = (
        'def impl(df, axis=None, skipna=None, level=None,{} numeric_only=None{}):\n'
        .format(ddof, dtn__zhb))
    if func_name == 'quantile':
        aws__itxkg = (
            "def impl(df, q=0.5, axis=0, numeric_only=True, interpolation='linear'):\n"
            )
    if func_name in ('idxmax', 'idxmin'):
        aws__itxkg = 'def impl(df, axis=0, skipna=True):\n'
    if axis == 0:
        aws__itxkg += _gen_reduce_impl_axis0(df, func_name, out_colnames,
            comm_dtype, args)
    else:
        aws__itxkg += _gen_reduce_impl_axis1(func_name, out_colnames,
            comm_dtype, df)
    xcyfk__phy = {}
    exec(aws__itxkg, {'bodo': bodo, 'np': np, 'pd': pd, 'numba': numba},
        xcyfk__phy)
    impl = xcyfk__phy['impl']
    return impl


def _gen_reduce_impl_axis0(df, func_name, out_colnames, comm_dtype, args):
    fax__toool = ''
    if func_name in ('min', 'max'):
        fax__toool = ', dtype=np.{}'.format(comm_dtype)
    if comm_dtype == types.float32 and func_name in ('sum', 'prod', 'mean',
        'var', 'std', 'median'):
        fax__toool = ', dtype=np.float32'
    rrxje__lqvnn = f'bodo.libs.array_ops.array_op_{func_name}'
    vbm__lxli = ''
    if func_name in ['sum', 'prod']:
        vbm__lxli = 'True, min_count'
    elif func_name in ['idxmax', 'idxmin']:
        vbm__lxli = 'index'
    elif func_name == 'quantile':
        vbm__lxli = 'q'
    elif func_name in ['std', 'var']:
        vbm__lxli = 'True, ddof'
    elif func_name == 'median':
        vbm__lxli = 'True'
    data_args = ', '.join(
        f'{rrxje__lqvnn}(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(pwc__oyq)}), {vbm__lxli})'
         for pwc__oyq in out_colnames)
    aws__itxkg = ''
    if func_name in ('idxmax', 'idxmin'):
        aws__itxkg += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
            )
        aws__itxkg += (
            '  data = bodo.utils.conversion.coerce_to_array(({},))\n'.
            format(data_args))
    else:
        aws__itxkg += '  data = np.asarray(({},){})\n'.format(data_args,
            fax__toool)
    aws__itxkg += f"""  return bodo.hiframes.pd_series_ext.init_series(data, pd.Index({out_colnames}))
"""
    return aws__itxkg


def _gen_reduce_impl_axis1(func_name, out_colnames, comm_dtype, df_type):
    men__fsgtp = [df_type.columns.index(pwc__oyq) for pwc__oyq in out_colnames]
    index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
    data_args = '\n    '.join(
        'arr_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})'
        .format(i) for i in men__fsgtp)
    gxcrc__thtog = '\n        '.join(f'row[{i}] = arr_{men__fsgtp[i]}[i]' for
        i in range(len(out_colnames)))
    assert len(data_args) > 0, f'empty dataframe in DataFrame.{func_name}()'
    dmlz__uqwm = f'len(arr_{men__fsgtp[0]})'
    ely__hypo = {'max': 'np.nanmax', 'min': 'np.nanmin', 'sum': 'np.nansum',
        'prod': 'np.nanprod', 'mean': 'np.nanmean', 'median':
        'np.nanmedian', 'var': 'bodo.utils.utils.nanvar_ddof1', 'std':
        'bodo.utils.utils.nanstd_ddof1'}
    if func_name in ely__hypo:
        xpm__nwl = ely__hypo[func_name]
        chfm__nbxv = 'float64' if func_name in ['mean', 'median', 'std', 'var'
            ] else comm_dtype
        aws__itxkg = f"""
    {data_args}
    numba.parfors.parfor.init_prange()
    n = {dmlz__uqwm}
    row = np.empty({len(out_colnames)}, np.{comm_dtype})
    A = np.empty(n, np.{chfm__nbxv})
    for i in numba.parfors.parfor.internal_prange(n):
        {gxcrc__thtog}
        A[i] = {xpm__nwl}(row)
    return bodo.hiframes.pd_series_ext.init_series(A, {index})
"""
        return aws__itxkg
    else:
        raise BodoError(f'DataFrame.{func_name}(): Not supported for axis=1')


@overload_method(DataFrameType, 'pct_change', inline='always', no_unliteral
    =True)
def overload_dataframe_pct_change(df, periods=1, fill_method='pad', limit=
    None, freq=None):
    check_runtime_cols_unsupported(df, 'DataFrame.pct_change()')
    icgbi__oqex = dict(fill_method=fill_method, limit=limit, freq=freq)
    glq__vnex = dict(fill_method='pad', limit=None, freq=None)
    check_unsupported_args('DataFrame.pct_change', icgbi__oqex, glq__vnex,
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
    icgbi__oqex = dict(axis=axis, skipna=skipna)
    glq__vnex = dict(axis=None, skipna=True)
    check_unsupported_args('DataFrame.cumprod', icgbi__oqex, glq__vnex,
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
    icgbi__oqex = dict(skipna=skipna)
    glq__vnex = dict(skipna=True)
    check_unsupported_args('DataFrame.cumsum', icgbi__oqex, glq__vnex,
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
    icgbi__oqex = dict(percentiles=percentiles, include=include, exclude=
        exclude, datetime_is_numeric=datetime_is_numeric)
    glq__vnex = dict(percentiles=None, include=None, exclude=None,
        datetime_is_numeric=True)
    check_unsupported_args('DataFrame.describe', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.describe()')
    bxpjo__kbh = [pwc__oyq for pwc__oyq, elfy__zxawf in zip(df.columns, df.
        data) if _is_describe_type(elfy__zxawf)]
    if len(bxpjo__kbh) == 0:
        raise BodoError('df.describe() only supports numeric columns')
    wlq__ufot = sum(df.data[df.columns.index(pwc__oyq)].dtype == bodo.
        datetime64ns for pwc__oyq in bxpjo__kbh)

    def _get_describe(col_ind):
        now__izq = df.data[col_ind].dtype == bodo.datetime64ns
        if wlq__ufot and wlq__ufot != len(bxpjo__kbh):
            if now__izq:
                return f'des_{col_ind} + (np.nan,)'
            return (
                f'des_{col_ind}[:2] + des_{col_ind}[3:] + (des_{col_ind}[2],)')
        return f'des_{col_ind}'
    header = """def impl(df, percentiles=None, include=None, exclude=None, datetime_is_numeric=True):
"""
    for pwc__oyq in bxpjo__kbh:
        col_ind = df.columns.index(pwc__oyq)
        header += f"""  des_{col_ind} = bodo.libs.array_ops.array_op_describe(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {col_ind}))
"""
    data_args = ', '.join(_get_describe(df.columns.index(pwc__oyq)) for
        pwc__oyq in bxpjo__kbh)
    uztq__zlv = "['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']"
    if wlq__ufot == len(bxpjo__kbh):
        uztq__zlv = "['count', 'mean', 'min', '25%', '50%', '75%', 'max']"
    elif wlq__ufot:
        uztq__zlv = (
            "['count', 'mean', 'min', '25%', '50%', '75%', 'max', 'std']")
    index = f'bodo.utils.conversion.convert_to_index({uztq__zlv})'
    return _gen_init_df(header, bxpjo__kbh, data_args, index)


@overload_method(DataFrameType, 'take', inline='always', no_unliteral=True)
def overload_dataframe_take(df, indices, axis=0, convert=None, is_copy=True):
    check_runtime_cols_unsupported(df, 'DataFrame.take()')
    icgbi__oqex = dict(axis=axis, convert=convert, is_copy=is_copy)
    glq__vnex = dict(axis=0, convert=None, is_copy=True)
    check_unsupported_args('DataFrame.take', icgbi__oqex, glq__vnex,
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
    icgbi__oqex = dict(freq=freq, axis=axis, fill_value=fill_value)
    glq__vnex = dict(freq=None, axis=0, fill_value=None)
    check_unsupported_args('DataFrame.shift', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.shift()')
    for kinqc__wfw in df.data:
        if not is_supported_shift_array_type(kinqc__wfw):
            raise BodoError(
                f'Dataframe.shift() column input type {kinqc__wfw.dtype} not supported yet.'
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
    icgbi__oqex = dict(axis=axis)
    glq__vnex = dict(axis=0)
    check_unsupported_args('DataFrame.diff', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.diff()')
    for kinqc__wfw in df.data:
        if not (isinstance(kinqc__wfw, types.Array) and (isinstance(
            kinqc__wfw.dtype, types.Number) or kinqc__wfw.dtype == bodo.
            datetime64ns)):
            raise BodoError(
                f'DataFrame.diff() column input type {kinqc__wfw.dtype} not supported.'
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
    msen__iuxr = (
        "DataFrame.explode(): 'column' must a constant label or list of labels"
        )
    if not is_literal_type(column):
        raise_bodo_error(msen__iuxr)
    if is_overload_constant_list(column) or is_overload_constant_tuple(column):
        zhu__mhtzg = get_overload_const_list(column)
    else:
        zhu__mhtzg = [get_literal_value(column)]
    edp__mby = {pwc__oyq: i for i, pwc__oyq in enumerate(df.columns)}
    eupak__klo = [edp__mby[pwc__oyq] for pwc__oyq in zhu__mhtzg]
    for i in eupak__klo:
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
        f'  counts = bodo.libs.array_kernels.get_arr_lens(data{eupak__klo[0]})\n'
        )
    for i in range(n):
        if i in eupak__klo:
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
    qto__lty = {'inplace': inplace, 'append': append, 'verify_integrity':
        verify_integrity}
    olakn__senkx = {'inplace': False, 'append': False, 'verify_integrity': 
        False}
    check_unsupported_args('DataFrame.set_index', qto__lty, olakn__senkx,
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
    columns = tuple(pwc__oyq for pwc__oyq in df.columns if pwc__oyq != col_name
        )
    index = (
        'bodo.utils.conversion.index_from_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}), {})'
        .format(col_ind, f"'{col_name}'" if isinstance(col_name, str) else
        col_name))
    return _gen_init_df(header, columns, data_args, index)


@overload_method(DataFrameType, 'query', no_unliteral=True)
def overload_dataframe_query(df, expr, inplace=False):
    check_runtime_cols_unsupported(df, 'DataFrame.query()')
    qto__lty = {'inplace': inplace}
    olakn__senkx = {'inplace': False}
    check_unsupported_args('query', qto__lty, olakn__senkx, package_name=
        'pandas', module_name='DataFrame')
    if not isinstance(expr, (types.StringLiteral, types.UnicodeType)):
        raise BodoError('query(): expr argument should be a string')

    def impl(df, expr, inplace=False):
        qvlk__izx = bodo.hiframes.pd_dataframe_ext.query_dummy(df, expr)
        return df[qvlk__izx]
    return impl


@overload_method(DataFrameType, 'duplicated', inline='always', no_unliteral
    =True)
def overload_dataframe_duplicated(df, subset=None, keep='first'):
    check_runtime_cols_unsupported(df, 'DataFrame.duplicated()')
    qto__lty = {'subset': subset, 'keep': keep}
    olakn__senkx = {'subset': None, 'keep': 'first'}
    check_unsupported_args('DataFrame.duplicated', qto__lty, olakn__senkx,
        package_name='pandas', module_name='DataFrame')
    ioz__fzl = len(df.columns)
    aws__itxkg = "def impl(df, subset=None, keep='first'):\n"
    for i in range(ioz__fzl):
        aws__itxkg += (
            '  data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})\n'
            .format(i))
    nszbe__jennt = ', '.join(f'data_{i}' for i in range(ioz__fzl))
    nszbe__jennt += ',' if ioz__fzl == 1 else ''
    aws__itxkg += (
        f'  duplicated = bodo.libs.array_kernels.duplicated(({nszbe__jennt}))\n'
        )
    aws__itxkg += (
        '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n')
    aws__itxkg += (
        '  return bodo.hiframes.pd_series_ext.init_series(duplicated, index)\n'
        )
    xcyfk__phy = {}
    exec(aws__itxkg, {'bodo': bodo}, xcyfk__phy)
    impl = xcyfk__phy['impl']
    return impl


@overload_method(DataFrameType, 'drop_duplicates', inline='always',
    no_unliteral=True)
def overload_dataframe_drop_duplicates(df, subset=None, keep='first',
    inplace=False, ignore_index=False):
    check_runtime_cols_unsupported(df, 'DataFrame.drop_duplicates()')
    qto__lty = {'keep': keep, 'inplace': inplace, 'ignore_index': ignore_index}
    olakn__senkx = {'keep': 'first', 'inplace': False, 'ignore_index': False}
    foxb__iko = []
    if is_overload_constant_list(subset):
        foxb__iko = get_overload_const_list(subset)
    elif is_overload_constant_str(subset):
        foxb__iko = [get_overload_const_str(subset)]
    elif is_overload_constant_int(subset):
        foxb__iko = [get_overload_const_int(subset)]
    elif not is_overload_none(subset):
        raise_bodo_error(
            'DataFrame.drop_duplicates(): subset must be a constant column name, constant list of column names or None'
            )
    qzkic__cbqal = []
    for col_name in foxb__iko:
        if col_name not in df.columns:
            raise BodoError(
                'DataFrame.drop_duplicates(): All subset columns must be found in the DataFrame.'
                 +
                f'Column {col_name} not found in DataFrame columns {df.columns}'
                )
        qzkic__cbqal.append(df.columns.index(col_name))
    check_unsupported_args('DataFrame.drop_duplicates', qto__lty,
        olakn__senkx, package_name='pandas', module_name='DataFrame')
    wcarf__wpg = []
    if qzkic__cbqal:
        for ugib__jbnb in qzkic__cbqal:
            if isinstance(df.data[ugib__jbnb], bodo.MapArrayType):
                wcarf__wpg.append(df.columns[ugib__jbnb])
    else:
        for i, col_name in enumerate(df.columns):
            if isinstance(df.data[i], bodo.MapArrayType):
                wcarf__wpg.append(col_name)
    if wcarf__wpg:
        raise BodoError(
            f'DataFrame.drop_duplicates(): Columns {wcarf__wpg} ' +
            f'have dictionary types which cannot be used to drop duplicates. '
             +
            "Please consider using the 'subset' argument to skip these columns."
            )
    ioz__fzl = len(df.columns)
    njmf__cqq = ['data_{}'.format(i) for i in qzkic__cbqal]
    phdeb__bufdm = ['data_{}'.format(i) for i in range(ioz__fzl) if i not in
        qzkic__cbqal]
    if njmf__cqq:
        qfsl__petsy = len(njmf__cqq)
    else:
        qfsl__petsy = ioz__fzl
    uhi__swes = ', '.join(njmf__cqq + phdeb__bufdm)
    data_args = ', '.join('data_{}'.format(i) for i in range(ioz__fzl))
    aws__itxkg = (
        "def impl(df, subset=None, keep='first', inplace=False, ignore_index=False):\n"
        )
    for i in range(ioz__fzl):
        aws__itxkg += (
            '  data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})\n'
            .format(i))
    index = (
        'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
        )
    aws__itxkg += (
        """  ({0},), index_arr = bodo.libs.array_kernels.drop_duplicates(({0},), {1}, {2})
"""
        .format(uhi__swes, index, qfsl__petsy))
    aws__itxkg += (
        '  index = bodo.utils.conversion.index_from_array(index_arr)\n')
    return _gen_init_df(aws__itxkg, df.columns, data_args, 'index')


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
                ifn__eqf = {pwc__oyq: i for i, pwc__oyq in enumerate(cond.
                    columns)}

                def cond_str(i, gen_all_false):
                    if df.columns[i] in ifn__eqf:
                        return (
                            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(cond, {ifn__eqf[df.columns[i]]})'
                            )
                    else:
                        gen_all_false[0] = True
                        return 'all_false'
            elif isinstance(cond, types.Array):
                cond_str = lambda i, _: f'cond[:,{i}]'
        if not hasattr(other, 'ndim') or other.ndim == 1:
            gdxv__urpke = lambda i: 'other'
        elif other.ndim == 2:
            if isinstance(other, DataFrameType):
                other_map = {pwc__oyq: i for i, pwc__oyq in enumerate(other
                    .columns)}
                gdxv__urpke = (lambda i: 
                    f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(other, {other_map[df.columns[i]]})'
                     if df.columns[i] in other_map else 'None')
            elif isinstance(other, types.Array):
                gdxv__urpke = lambda i: f'other[:,{i}]'
        ioz__fzl = len(df.columns)
        data_args = ', '.join(
            f'bodo.hiframes.series_impl.where_impl({cond_str(i, gen_all_false)}, bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}), {gdxv__urpke(i)})'
             for i in range(ioz__fzl))
        if gen_all_false[0]:
            header += '  all_false = np.zeros(len(df), dtype=bool)\n'
        return _gen_init_df(header, df.columns, data_args)
    return overload_dataframe_mask_where


def _install_dataframe_mask_where_overload():
    for func_name in ('mask', 'where'):
        kgv__buoqp = create_dataframe_mask_where_overload(func_name)
        overload_method(DataFrameType, func_name, no_unliteral=True)(kgv__buoqp
            )


_install_dataframe_mask_where_overload()


def _validate_arguments_mask_where(func_name, df, cond, other, inplace,
    axis, level, errors, try_cast):
    icgbi__oqex = dict(inplace=inplace, level=level, errors=errors,
        try_cast=try_cast)
    glq__vnex = dict(inplace=False, level=None, errors='raise', try_cast=False)
    check_unsupported_args(f'{func_name}', icgbi__oqex, glq__vnex,
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
    ioz__fzl = len(df.columns)
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
        other_map = {pwc__oyq: i for i, pwc__oyq in enumerate(other.columns)}
        for i in range(ioz__fzl):
            if df.columns[i] in other_map:
                bodo.hiframes.series_impl._validate_self_other_mask_where(
                    func_name, df.data[i], other.data[other_map[df.columns[i]]]
                    )
            else:
                bodo.hiframes.series_impl._validate_self_other_mask_where(
                    func_name, df.data[i], None, is_default=True)
    elif isinstance(other, SeriesType):
        for i in range(ioz__fzl):
            bodo.hiframes.series_impl._validate_self_other_mask_where(func_name
                , df.data[i], other.data)
    else:
        for i in range(ioz__fzl):
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
        lvwpy__xwheb = 'out_df_type'
    else:
        lvwpy__xwheb = gen_const_tup(columns)
    data_args = '({}{})'.format(data_args, ',' if data_args else '')
    aws__itxkg = f"""{header}  return bodo.hiframes.pd_dataframe_ext.init_dataframe({data_args}, {index}, {lvwpy__xwheb})
"""
    xcyfk__phy = {}
    rqmba__dmhyi = {'bodo': bodo, 'np': np, 'pd': pd, 'numba': numba}
    rqmba__dmhyi.update(extra_globals)
    exec(aws__itxkg, rqmba__dmhyi, xcyfk__phy)
    impl = xcyfk__phy['impl']
    return impl


def _get_binop_columns(lhs, rhs, is_inplace=False):
    if lhs.columns != rhs.columns:
        pjy__kgtli = pd.Index(lhs.columns)
        xdhvh__qvyo = pd.Index(rhs.columns)
        otl__dygz, xrqe__qlt, yba__hffh = pjy__kgtli.join(xdhvh__qvyo, how=
            'left' if is_inplace else 'outer', level=None, return_indexers=True
            )
        return tuple(otl__dygz), xrqe__qlt, yba__hffh
    return lhs.columns, range(len(lhs.columns)), range(len(lhs.columns))


def create_binary_op_overload(op):

    def overload_dataframe_binary_op(lhs, rhs):
        zdd__jjjv = numba.core.utils.OPERATORS_TO_BUILTINS[op]
        gzrbh__zkc = operator.eq, operator.ne
        check_runtime_cols_unsupported(lhs, zdd__jjjv)
        check_runtime_cols_unsupported(rhs, zdd__jjjv)
        if isinstance(lhs, DataFrameType):
            if isinstance(rhs, DataFrameType):
                otl__dygz, xrqe__qlt, yba__hffh = _get_binop_columns(lhs, rhs)
                data_args = ', '.join(
                    f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(lhs, {exe__fnvr}) {zdd__jjjv}bodo.hiframes.pd_dataframe_ext.get_dataframe_data(rhs, {olas__chtvc})'
                     if exe__fnvr != -1 and olas__chtvc != -1 else
                    f'bodo.libs.array_kernels.gen_na_array(len(lhs), float64_arr_type)'
                     for exe__fnvr, olas__chtvc in zip(xrqe__qlt, yba__hffh))
                header = 'def impl(lhs, rhs):\n'
                index = (
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(lhs)')
                return _gen_init_df(header, otl__dygz, data_args, index,
                    extra_globals={'float64_arr_type': types.Array(types.
                    float64, 1, 'C')})
            yekcw__flpgr = []
            xqu__lbdz = []
            if op in gzrbh__zkc:
                for i, uzzf__ugz in enumerate(lhs.data):
                    if is_common_scalar_dtype([uzzf__ugz.dtype, rhs]):
                        yekcw__flpgr.append(
                            f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(lhs, {i}) {zdd__jjjv} rhs'
                            )
                    else:
                        uim__utv = f'arr{i}'
                        xqu__lbdz.append(uim__utv)
                        yekcw__flpgr.append(uim__utv)
                data_args = ', '.join(yekcw__flpgr)
            else:
                data_args = ', '.join(
                    f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(lhs, {i}) {zdd__jjjv} rhs'
                     for i in range(len(lhs.columns)))
            header = 'def impl(lhs, rhs):\n'
            if len(xqu__lbdz) > 0:
                header += '  numba.parfors.parfor.init_prange()\n'
                header += '  n = len(lhs)\n'
                header += ''.join(
                    f'  {uim__utv} = np.empty(n, dtype=np.bool_)\n' for
                    uim__utv in xqu__lbdz)
                header += (
                    '  for i in numba.parfors.parfor.internal_prange(n):\n')
                header += ''.join('    {0}[i] = {1}\n'.format(uim__utv, op ==
                    operator.ne) for uim__utv in xqu__lbdz)
            index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(lhs)'
            return _gen_init_df(header, lhs.columns, data_args, index)
        if isinstance(rhs, DataFrameType):
            yekcw__flpgr = []
            xqu__lbdz = []
            if op in gzrbh__zkc:
                for i, uzzf__ugz in enumerate(rhs.data):
                    if is_common_scalar_dtype([lhs, uzzf__ugz.dtype]):
                        yekcw__flpgr.append(
                            f'lhs {zdd__jjjv} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(rhs, {i})'
                            )
                    else:
                        uim__utv = f'arr{i}'
                        xqu__lbdz.append(uim__utv)
                        yekcw__flpgr.append(uim__utv)
                data_args = ', '.join(yekcw__flpgr)
            else:
                data_args = ', '.join(
                    'lhs {1} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(rhs, {0})'
                    .format(i, zdd__jjjv) for i in range(len(rhs.columns)))
            header = 'def impl(lhs, rhs):\n'
            if len(xqu__lbdz) > 0:
                header += '  numba.parfors.parfor.init_prange()\n'
                header += '  n = len(rhs)\n'
                header += ''.join('  {0} = np.empty(n, dtype=np.bool_)\n'.
                    format(uim__utv) for uim__utv in xqu__lbdz)
                header += (
                    '  for i in numba.parfors.parfor.internal_prange(n):\n')
                header += ''.join('    {0}[i] = {1}\n'.format(uim__utv, op ==
                    operator.ne) for uim__utv in xqu__lbdz)
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
        kgv__buoqp = create_binary_op_overload(op)
        overload(op)(kgv__buoqp)


_install_binary_ops()


def create_inplace_binary_op_overload(op):

    def overload_dataframe_inplace_binary_op(left, right):
        zdd__jjjv = numba.core.utils.OPERATORS_TO_BUILTINS[op]
        check_runtime_cols_unsupported(left, zdd__jjjv)
        check_runtime_cols_unsupported(right, zdd__jjjv)
        if isinstance(left, DataFrameType):
            if isinstance(right, DataFrameType):
                otl__dygz, _, yba__hffh = _get_binop_columns(left, right, True)
                aws__itxkg = 'def impl(left, right):\n'
                for i, olas__chtvc in enumerate(yba__hffh):
                    if olas__chtvc == -1:
                        aws__itxkg += f"""  df_arr{i} = bodo.libs.array_kernels.gen_na_array(len(left), float64_arr_type)
"""
                        continue
                    aws__itxkg += f"""  df_arr{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(left, {i})
"""
                    aws__itxkg += f"""  df_arr{i} {zdd__jjjv} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(right, {olas__chtvc})
"""
                data_args = ', '.join(f'df_arr{i}' for i in range(len(
                    otl__dygz)))
                index = (
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(left)')
                return _gen_init_df(aws__itxkg, otl__dygz, data_args, index,
                    extra_globals={'float64_arr_type': types.Array(types.
                    float64, 1, 'C')})
            aws__itxkg = 'def impl(left, right):\n'
            for i in range(len(left.columns)):
                aws__itxkg += (
                    """  df_arr{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(left, {0})
"""
                    .format(i))
                aws__itxkg += '  df_arr{0} {1} right\n'.format(i, zdd__jjjv)
            data_args = ', '.join('df_arr{}'.format(i) for i in range(len(
                left.columns)))
            index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(left)'
            return _gen_init_df(aws__itxkg, left.columns, data_args, index)
    return overload_dataframe_inplace_binary_op


def _install_inplace_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_inplace_binary_ops:
        kgv__buoqp = create_inplace_binary_op_overload(op)
        overload(op, no_unliteral=True)(kgv__buoqp)


_install_inplace_binary_ops()


def create_unary_op_overload(op):

    def overload_dataframe_unary_op(df):
        if isinstance(df, DataFrameType):
            zdd__jjjv = numba.core.utils.OPERATORS_TO_BUILTINS[op]
            check_runtime_cols_unsupported(df, zdd__jjjv)
            data_args = ', '.join(
                '{1} bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})'
                .format(i, zdd__jjjv) for i in range(len(df.columns)))
            header = 'def impl(df):\n'
            return _gen_init_df(header, df.columns, data_args)
    return overload_dataframe_unary_op


def _install_unary_ops():
    for op in bodo.hiframes.pd_series_ext.series_unary_ops:
        kgv__buoqp = create_unary_op_overload(op)
        overload(op, no_unliteral=True)(kgv__buoqp)


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
            akz__pymqh = np.empty(n, np.bool_)
            for i in numba.parfors.parfor.internal_prange(n):
                akz__pymqh[i] = bodo.libs.array_kernels.isna(obj, i)
            return akz__pymqh
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
            akz__pymqh = np.empty(n, np.bool_)
            for i in range(n):
                akz__pymqh[i] = pd.isna(obj[i])
            return akz__pymqh
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
    qto__lty = {'inplace': inplace, 'limit': limit, 'regex': regex,
        'method': method}
    olakn__senkx = {'inplace': False, 'limit': None, 'regex': False,
        'method': 'pad'}
    check_unsupported_args('replace', qto__lty, olakn__senkx, package_name=
        'pandas', module_name='DataFrame')
    data_args = ', '.join(
        f'df.iloc[:, {i}].replace(to_replace, value).values' for i in range
        (len(df.columns)))
    header = """def impl(df, to_replace=None, value=None, inplace=False, limit=None, regex=False, method='pad'):
"""
    return _gen_init_df(header, df.columns, data_args)


def _is_col_access(expr_node):
    hiyhs__frxeb = str(expr_node)
    return hiyhs__frxeb.startswith('left.') or hiyhs__frxeb.startswith('right.'
        )


def _insert_NA_cond(expr_node, left_columns, left_data, right_columns,
    right_data):
    ken__icsp = {'left': 0, 'right': 0, 'NOT_NA': 0}
    env = pd.core.computation.scope.ensure_scope(2, {}, {}, (ken__icsp,))
    kyg__kwi = pd.core.computation.parsing.clean_column_name

    def append_null_checks(expr_node, null_set):
        if not null_set:
            return expr_node
        rtxy__qsap = ' & '.join([('NOT_NA.`' + x + '`') for x in null_set])
        kjhe__uqwyu = {('NOT_NA', kyg__kwi(uzzf__ugz)): uzzf__ugz for
            uzzf__ugz in null_set}
        ulodm__qfytr, _, _ = _parse_query_expr(rtxy__qsap, env, [], [],
            None, join_cleaned_cols=kjhe__uqwyu)
        jtue__fqrkj = (pd.core.computation.ops.BinOp.
            _disallow_scalar_only_bool_ops)
        pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops = (lambda
            self: None)
        try:
            qhgt__timng = pd.core.computation.ops.BinOp('&', ulodm__qfytr,
                expr_node)
        finally:
            (pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops
                ) = jtue__fqrkj
        return qhgt__timng

    def _insert_NA_cond_body(expr_node, null_set):
        if isinstance(expr_node, pd.core.computation.ops.BinOp):
            if expr_node.op == '|':
                goy__jbv = set()
                xkoz__nbfpz = set()
                hirko__ytv = _insert_NA_cond_body(expr_node.lhs, goy__jbv)
                ticvq__uvue = _insert_NA_cond_body(expr_node.rhs, xkoz__nbfpz)
                moelp__nfbh = goy__jbv.intersection(xkoz__nbfpz)
                goy__jbv.difference_update(moelp__nfbh)
                xkoz__nbfpz.difference_update(moelp__nfbh)
                null_set.update(moelp__nfbh)
                expr_node.lhs = append_null_checks(hirko__ytv, goy__jbv)
                expr_node.rhs = append_null_checks(ticvq__uvue, xkoz__nbfpz)
                expr_node.operands = expr_node.lhs, expr_node.rhs
            else:
                expr_node.lhs = _insert_NA_cond_body(expr_node.lhs, null_set)
                expr_node.rhs = _insert_NA_cond_body(expr_node.rhs, null_set)
        elif _is_col_access(expr_node):
            haqol__vsja = expr_node.name
            njet__wyeqa, col_name = haqol__vsja.split('.')
            if njet__wyeqa == 'left':
                bocqq__hvz = left_columns
                data = left_data
            else:
                bocqq__hvz = right_columns
                data = right_data
            yjxcq__tlyi = data[bocqq__hvz.index(col_name)]
            if bodo.utils.typing.is_nullable(yjxcq__tlyi):
                null_set.add(expr_node.name)
        return expr_node
    null_set = set()
    qxcb__vbk = _insert_NA_cond_body(expr_node, null_set)
    return append_null_checks(expr_node, null_set)


def _extract_equal_conds(expr_node):
    if not hasattr(expr_node, 'op'):
        return [], [], expr_node
    if expr_node.op == '==' and _is_col_access(expr_node.lhs
        ) and _is_col_access(expr_node.rhs):
        miib__zbei = str(expr_node.lhs)
        hmdo__zzfac = str(expr_node.rhs)
        if miib__zbei.startswith('left.') and hmdo__zzfac.startswith('left.'
            ) or miib__zbei.startswith('right.') and hmdo__zzfac.startswith(
            'right.'):
            return [], [], expr_node
        left_on = [miib__zbei.split('.')[1]]
        right_on = [hmdo__zzfac.split('.')[1]]
        if miib__zbei.startswith('right.'):
            return right_on, left_on, None
        return left_on, right_on, None
    if expr_node.op == '&':
        iukm__rzk, kofpz__qcu, nha__ihpnb = _extract_equal_conds(expr_node.lhs)
        cgaln__dij, omm__xyjc, ajcwa__lfk = _extract_equal_conds(expr_node.rhs)
        left_on = iukm__rzk + cgaln__dij
        right_on = kofpz__qcu + omm__xyjc
        if nha__ihpnb is None:
            return left_on, right_on, ajcwa__lfk
        if ajcwa__lfk is None:
            return left_on, right_on, nha__ihpnb
        expr_node.lhs = nha__ihpnb
        expr_node.rhs = ajcwa__lfk
        expr_node.operands = expr_node.lhs, expr_node.rhs
        return left_on, right_on, expr_node
    return [], [], expr_node


def _parse_merge_cond(on_str, left_columns, left_data, right_columns,
    right_data):
    ken__icsp = {'left': 0, 'right': 0}
    env = pd.core.computation.scope.ensure_scope(2, {}, {}, (ken__icsp,))
    flmng__dfifg = dict()
    kyg__kwi = pd.core.computation.parsing.clean_column_name
    for name, fdd__atk in (('left', left_columns), ('right', right_columns)):
        for uzzf__ugz in fdd__atk:
            swsry__flqlt = kyg__kwi(uzzf__ugz)
            pcibk__dfrg = name, swsry__flqlt
            if pcibk__dfrg in flmng__dfifg:
                raise_bodo_error(
                    f"pd.merge(): {name} table contains two columns that are escaped to the same Python identifier '{uzzf__ugz}' and '{flmng__dfifg[swsry__flqlt]}' Please rename one of these columns. To avoid this issue, please use names that are valid Python identifiers."
                    )
            flmng__dfifg[pcibk__dfrg] = uzzf__ugz
    ddab__myv, _, _ = _parse_query_expr(on_str, env, [], [], None,
        join_cleaned_cols=flmng__dfifg)
    left_on, right_on, hyyg__lrsdj = _extract_equal_conds(ddab__myv.terms)
    return left_on, right_on, _insert_NA_cond(hyyg__lrsdj, left_columns,
        left_data, right_columns, right_data)


@overload_method(DataFrameType, 'merge', inline='always', no_unliteral=True)
@overload(pd.merge, inline='always', no_unliteral=True)
def overload_dataframe_merge(left, right, how='inner', on=None, left_on=
    None, right_on=None, left_index=False, right_index=False, sort=False,
    suffixes=('_x', '_y'), copy=True, indicator=False, validate=None,
    _bodo_na_equal=True):
    check_runtime_cols_unsupported(left, 'DataFrame.merge()')
    check_runtime_cols_unsupported(right, 'DataFrame.merge()')
    icgbi__oqex = dict(sort=sort, copy=copy, validate=validate)
    glq__vnex = dict(sort=False, copy=True, validate=None)
    check_unsupported_args('DataFrame.merge', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    validate_merge_spec(left, right, how, on, left_on, right_on, left_index,
        right_index, sort, suffixes, copy, indicator, validate)
    how = get_overload_const_str(how)
    khpbk__ltrfr = tuple(sorted(set(left.columns) & set(right.columns), key
        =lambda k: str(k)))
    ksyw__enaim = ''
    if not is_overload_none(on):
        left_on = right_on = on
        if is_overload_constant_str(on):
            on_str = get_overload_const_str(on)
            if on_str not in khpbk__ltrfr and ('left.' in on_str or 
                'right.' in on_str):
                left_on, right_on, qwhw__sfo = _parse_merge_cond(on_str,
                    left.columns, left.data, right.columns, right.data)
                if qwhw__sfo is None:
                    ksyw__enaim = ''
                else:
                    ksyw__enaim = str(qwhw__sfo)
    if is_overload_none(on) and is_overload_none(left_on) and is_overload_none(
        right_on) and is_overload_false(left_index) and is_overload_false(
        right_index):
        left_keys = khpbk__ltrfr
        right_keys = khpbk__ltrfr
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
    dwtg__euwxb = get_overload_const_bool(_bodo_na_equal)
    validate_keys_length(left_index, right_index, left_keys, right_keys)
    validate_keys_dtypes(left, right, left_index, right_index, left_keys,
        right_keys)
    if is_overload_constant_tuple(suffixes):
        whol__kibmk = get_overload_const_tuple(suffixes)
    if is_overload_constant_list(suffixes):
        whol__kibmk = list(get_overload_const_list(suffixes))
    suffix_x = whol__kibmk[0]
    suffix_y = whol__kibmk[1]
    validate_unicity_output_column_names(suffix_x, suffix_y, left_keys,
        right_keys, left.columns, right.columns, indicator_val)
    left_keys = gen_const_tup(left_keys)
    right_keys = gen_const_tup(right_keys)
    aws__itxkg = "def _impl(left, right, how='inner', on=None, left_on=None,\n"
    aws__itxkg += (
        '    right_on=None, left_index=False, right_index=False, sort=False,\n'
        )
    aws__itxkg += """    suffixes=('_x', '_y'), copy=True, indicator=False, validate=None, _bodo_na_equal=True):
"""
    aws__itxkg += (
        """  return bodo.hiframes.pd_dataframe_ext.join_dummy(left, right, {}, {}, '{}', '{}', '{}', False, {}, {}, '{}')
"""
        .format(left_keys, right_keys, how, suffix_x, suffix_y,
        indicator_val, dwtg__euwxb, ksyw__enaim))
    xcyfk__phy = {}
    exec(aws__itxkg, {'bodo': bodo}, xcyfk__phy)
    _impl = xcyfk__phy['_impl']
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
    lcb__cxcsk = {string_array_type, dict_str_arr_type, binary_array_type,
        datetime_date_array_type, datetime_timedelta_array_type, boolean_array}
    csxq__tmqbe = {get_overload_const_str(ribo__dggn) for ribo__dggn in (
        left_on, right_on, on) if is_overload_constant_str(ribo__dggn)}
    for df in (left, right):
        for i, uzzf__ugz in enumerate(df.data):
            if not isinstance(uzzf__ugz, valid_dataframe_column_types
                ) and uzzf__ugz not in lcb__cxcsk:
                raise BodoError(
                    f'{name_func}(): use of column with {type(uzzf__ugz)} in merge unsupported'
                    )
            if df.columns[i] in csxq__tmqbe and isinstance(uzzf__ugz,
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
        whol__kibmk = get_overload_const_tuple(suffixes)
    if is_overload_constant_list(suffixes):
        whol__kibmk = list(get_overload_const_list(suffixes))
    if len(whol__kibmk) != 2:
        raise BodoError(name_func +
            '(): The number of suffixes should be exactly 2')
    khpbk__ltrfr = tuple(set(left.columns) & set(right.columns))
    if not is_overload_none(on):
        xnacc__gqvd = False
        if is_overload_constant_str(on):
            on_str = get_overload_const_str(on)
            xnacc__gqvd = on_str not in khpbk__ltrfr and ('left.' in on_str or
                'right.' in on_str)
        if len(khpbk__ltrfr) == 0 and not xnacc__gqvd:
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
    tfo__ors = numba.core.registry.cpu_target.typing_context
    if is_overload_true(left_index) or is_overload_true(right_index):
        if is_overload_true(left_index) and is_overload_true(right_index):
            gmosb__viy = left.index
            bxg__vqzjd = isinstance(gmosb__viy, StringIndexType)
            sfrd__pfee = right.index
            zhnsd__zmkpp = isinstance(sfrd__pfee, StringIndexType)
        elif is_overload_true(left_index):
            gmosb__viy = left.index
            bxg__vqzjd = isinstance(gmosb__viy, StringIndexType)
            sfrd__pfee = right.data[right.columns.index(right_keys[0])]
            zhnsd__zmkpp = sfrd__pfee.dtype == string_type
        elif is_overload_true(right_index):
            gmosb__viy = left.data[left.columns.index(left_keys[0])]
            bxg__vqzjd = gmosb__viy.dtype == string_type
            sfrd__pfee = right.index
            zhnsd__zmkpp = isinstance(sfrd__pfee, StringIndexType)
        if bxg__vqzjd and zhnsd__zmkpp:
            return
        gmosb__viy = gmosb__viy.dtype
        sfrd__pfee = sfrd__pfee.dtype
        try:
            eunqn__ihfj = tfo__ors.resolve_function_type(operator.eq, (
                gmosb__viy, sfrd__pfee), {})
        except:
            raise_bodo_error(
                'merge: You are trying to merge on {lk_dtype} and {rk_dtype} columns. If you wish to proceed you should use pd.concat'
                .format(lk_dtype=gmosb__viy, rk_dtype=sfrd__pfee))
    else:
        for ovhe__muuk, hfyju__aar in zip(left_keys, right_keys):
            gmosb__viy = left.data[left.columns.index(ovhe__muuk)].dtype
            rex__rfxfr = left.data[left.columns.index(ovhe__muuk)]
            sfrd__pfee = right.data[right.columns.index(hfyju__aar)].dtype
            xxlx__vfz = right.data[right.columns.index(hfyju__aar)]
            if rex__rfxfr == xxlx__vfz:
                continue
            wdbvh__bdhzr = (
                'merge: You are trying to merge on column {lk} of {lk_dtype} and column {rk} of {rk_dtype}. If you wish to proceed you should use pd.concat'
                .format(lk=ovhe__muuk, lk_dtype=gmosb__viy, rk=hfyju__aar,
                rk_dtype=sfrd__pfee))
            cmq__wfsj = gmosb__viy == string_type
            wrcpf__hnyqn = sfrd__pfee == string_type
            if cmq__wfsj ^ wrcpf__hnyqn:
                raise_bodo_error(wdbvh__bdhzr)
            try:
                eunqn__ihfj = tfo__ors.resolve_function_type(operator.eq, (
                    gmosb__viy, sfrd__pfee), {})
            except:
                raise_bodo_error(wdbvh__bdhzr)


def validate_keys(keys, df):
    gvpew__udto = set(keys).difference(set(df.columns))
    if len(gvpew__udto) > 0:
        if is_overload_constant_str(df.index.name_typ
            ) and get_overload_const_str(df.index.name_typ) in gvpew__udto:
            raise_bodo_error(
                f'merge(): use of index {df.index.name_typ} as key for on/left_on/right_on is unsupported'
                )
        raise_bodo_error(
            f"""merge(): invalid key {gvpew__udto} for on/left_on/right_on
merge supports only valid column names {df.columns}"""
            )


@overload_method(DataFrameType, 'join', inline='always', no_unliteral=True)
def overload_dataframe_join(left, other, on=None, how='left', lsuffix='',
    rsuffix='', sort=False):
    check_runtime_cols_unsupported(left, 'DataFrame.join()')
    check_runtime_cols_unsupported(other, 'DataFrame.join()')
    icgbi__oqex = dict(lsuffix=lsuffix, rsuffix=rsuffix)
    glq__vnex = dict(lsuffix='', rsuffix='')
    check_unsupported_args('DataFrame.join', icgbi__oqex, glq__vnex,
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
    aws__itxkg = "def _impl(left, other, on=None, how='left',\n"
    aws__itxkg += "    lsuffix='', rsuffix='', sort=False):\n"
    aws__itxkg += (
        """  return bodo.hiframes.pd_dataframe_ext.join_dummy(left, other, {}, {}, '{}', '{}', '{}', True, False, True, '')
"""
        .format(left_keys, right_keys, how, lsuffix, rsuffix))
    xcyfk__phy = {}
    exec(aws__itxkg, {'bodo': bodo}, xcyfk__phy)
    _impl = xcyfk__phy['_impl']
    return _impl


def validate_join_spec(left, other, on, how, lsuffix, rsuffix, sort):
    if not isinstance(other, DataFrameType):
        raise BodoError('join() requires dataframe inputs')
    ensure_constant_values('merge', 'how', how, ('left', 'right', 'outer',
        'inner'))
    if not is_overload_none(on) and len(get_overload_const_list(on)) != 1:
        raise BodoError('join(): len(on) must equals to 1 when specified.')
    if not is_overload_none(on):
        sgugy__wokwh = get_overload_const_list(on)
        validate_keys(sgugy__wokwh, left)
    if not is_overload_false(sort):
        raise BodoError(
            'join(): sort parameter only supports default value False')
    khpbk__ltrfr = tuple(set(left.columns) & set(other.columns))
    if len(khpbk__ltrfr) > 0:
        raise_bodo_error(
            'join(): not supporting joining on overlapping columns:{cols} Use DataFrame.merge() instead.'
            .format(cols=khpbk__ltrfr))


def validate_unicity_output_column_names(suffix_x, suffix_y, left_keys,
    right_keys, left_columns, right_columns, indicator_val):
    swj__oiwdt = set(left_keys) & set(right_keys)
    ltpd__bxm = set(left_columns) & set(right_columns)
    ffji__baqk = ltpd__bxm - swj__oiwdt
    xewq__okrai = set(left_columns) - ltpd__bxm
    xgjdb__wfdjk = set(right_columns) - ltpd__bxm
    vjgi__mazj = {}

    def insertOutColumn(col_name):
        if col_name in vjgi__mazj:
            raise_bodo_error(
                'join(): two columns happen to have the same name : {}'.
                format(col_name))
        vjgi__mazj[col_name] = 0
    for ucm__kvuzo in swj__oiwdt:
        insertOutColumn(ucm__kvuzo)
    for ucm__kvuzo in ffji__baqk:
        ridnz__ecn = str(ucm__kvuzo) + suffix_x
        fljpv__jymor = str(ucm__kvuzo) + suffix_y
        insertOutColumn(ridnz__ecn)
        insertOutColumn(fljpv__jymor)
    for ucm__kvuzo in xewq__okrai:
        insertOutColumn(ucm__kvuzo)
    for ucm__kvuzo in xgjdb__wfdjk:
        insertOutColumn(ucm__kvuzo)
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
    khpbk__ltrfr = tuple(sorted(set(left.columns) & set(right.columns), key
        =lambda k: str(k)))
    if not is_overload_none(on):
        left_on = right_on = on
    if is_overload_none(on) and is_overload_none(left_on) and is_overload_none(
        right_on) and is_overload_false(left_index) and is_overload_false(
        right_index):
        left_keys = khpbk__ltrfr
        right_keys = khpbk__ltrfr
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
        whol__kibmk = suffixes
    if is_overload_constant_list(suffixes):
        whol__kibmk = list(get_overload_const_list(suffixes))
    if isinstance(suffixes, types.Omitted):
        whol__kibmk = suffixes.value
    suffix_x = whol__kibmk[0]
    suffix_y = whol__kibmk[1]
    aws__itxkg = (
        'def _impl(left, right, on=None, left_on=None, right_on=None,\n')
    aws__itxkg += (
        '    left_index=False, right_index=False, by=None, left_by=None,\n')
    aws__itxkg += "    right_by=None, suffixes=('_x', '_y'), tolerance=None,\n"
    aws__itxkg += "    allow_exact_matches=True, direction='backward'):\n"
    aws__itxkg += '  suffix_x = suffixes[0]\n'
    aws__itxkg += '  suffix_y = suffixes[1]\n'
    aws__itxkg += (
        """  return bodo.hiframes.pd_dataframe_ext.join_dummy(left, right, {}, {}, 'asof', '{}', '{}', False, False, True, '')
"""
        .format(left_keys, right_keys, suffix_x, suffix_y))
    xcyfk__phy = {}
    exec(aws__itxkg, {'bodo': bodo}, xcyfk__phy)
    _impl = xcyfk__phy['_impl']
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
    icgbi__oqex = dict(sort=sort, group_keys=group_keys, squeeze=squeeze,
        observed=observed)
    htskp__kqice = dict(sort=False, group_keys=True, squeeze=False,
        observed=True)
    check_unsupported_args('Dataframe.groupby', icgbi__oqex, htskp__kqice,
        package_name='pandas', module_name='GroupBy')


def pivot_error_checking(df, index, columns, values, func_name):
    tih__evqks = func_name == 'DataFrame.pivot_table'
    if tih__evqks:
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
    fgoen__ztaj = get_literal_value(columns)
    if isinstance(fgoen__ztaj, (list, tuple)):
        if len(fgoen__ztaj) > 1:
            raise BodoError(
                f"{func_name}(): 'columns' argument must be a constant column label not a {fgoen__ztaj}"
                )
        fgoen__ztaj = fgoen__ztaj[0]
    if fgoen__ztaj not in df.columns:
        raise BodoError(
            f"{func_name}(): 'columns' column {fgoen__ztaj} not found in DataFrame {df}."
            )
    axpt__vyrsj = {pwc__oyq: i for i, pwc__oyq in enumerate(df.columns)}
    jfc__xyxng = axpt__vyrsj[fgoen__ztaj]
    if is_overload_none(index):
        rcmu__mvghf = []
        siffb__haso = []
    else:
        siffb__haso = get_literal_value(index)
        if not isinstance(siffb__haso, (list, tuple)):
            siffb__haso = [siffb__haso]
        rcmu__mvghf = []
        for index in siffb__haso:
            if index not in axpt__vyrsj:
                raise BodoError(
                    f"{func_name}(): 'index' column {index} not found in DataFrame {df}."
                    )
            rcmu__mvghf.append(axpt__vyrsj[index])
    if not (all(isinstance(pwc__oyq, int) for pwc__oyq in siffb__haso) or
        all(isinstance(pwc__oyq, str) for pwc__oyq in siffb__haso)):
        raise BodoError(
            f"{func_name}(): column names selected for 'index' must all share a common int or string type. Please convert your names to a common type using DataFrame.rename()"
            )
    if is_overload_none(values):
        vgcn__mueol = []
        nxduz__tgwqa = []
        udig__bykc = rcmu__mvghf + [jfc__xyxng]
        for i, pwc__oyq in enumerate(df.columns):
            if i not in udig__bykc:
                vgcn__mueol.append(i)
                nxduz__tgwqa.append(pwc__oyq)
    else:
        nxduz__tgwqa = get_literal_value(values)
        if not isinstance(nxduz__tgwqa, (list, tuple)):
            nxduz__tgwqa = [nxduz__tgwqa]
        vgcn__mueol = []
        for val in nxduz__tgwqa:
            if val not in axpt__vyrsj:
                raise BodoError(
                    f"{func_name}(): 'values' column {val} not found in DataFrame {df}."
                    )
            vgcn__mueol.append(axpt__vyrsj[val])
    if all(isinstance(pwc__oyq, int) for pwc__oyq in nxduz__tgwqa):
        nxduz__tgwqa = np.array(nxduz__tgwqa, 'int64')
    elif all(isinstance(pwc__oyq, str) for pwc__oyq in nxduz__tgwqa):
        nxduz__tgwqa = pd.array(nxduz__tgwqa, 'string')
    else:
        raise BodoError(
            f"{func_name}(): column names selected for 'values' must all share a common int or string type. Please convert your names to a common type using DataFrame.rename()"
            )
    sjae__wlz = set(vgcn__mueol) | set(rcmu__mvghf) | {jfc__xyxng}
    if len(sjae__wlz) != len(vgcn__mueol) + len(rcmu__mvghf) + 1:
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
    if len(rcmu__mvghf) == 0:
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
        for eizy__vfh in rcmu__mvghf:
            index_column = df.data[eizy__vfh]
            check_valid_index_typ(index_column)
    ntop__ynl = df.data[jfc__xyxng]
    if isinstance(ntop__ynl, (bodo.ArrayItemArrayType, bodo.MapArrayType,
        bodo.StructArrayType, bodo.TupleArrayType, bodo.IntervalArrayType)):
        raise BodoError(
            f"{func_name}(): 'columns' DataFrame column must have scalar rows")
    if isinstance(ntop__ynl, bodo.CategoricalArrayType):
        raise BodoError(
            f"{func_name}(): 'columns' DataFrame column does not support categorical data"
            )
    for csptk__toc in vgcn__mueol:
        qtx__kepl = df.data[csptk__toc]
        if isinstance(qtx__kepl, (bodo.ArrayItemArrayType, bodo.
            MapArrayType, bodo.StructArrayType, bodo.TupleArrayType)
            ) or qtx__kepl == bodo.binary_array_type:
            raise BodoError(
                f"{func_name}(): 'values' DataFrame column must have scalar rows"
                )
    return (siffb__haso, fgoen__ztaj, nxduz__tgwqa, rcmu__mvghf, jfc__xyxng,
        vgcn__mueol)


@overload(pd.pivot, inline='always', no_unliteral=True)
@overload_method(DataFrameType, 'pivot', inline='always', no_unliteral=True)
def overload_dataframe_pivot(data, index=None, columns=None, values=None):
    check_runtime_cols_unsupported(data, 'DataFrame.pivot()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
        'DataFrame.pivot()')
    if not isinstance(data, DataFrameType):
        raise BodoError("pandas.pivot(): 'data' argument must be a DataFrame")
    (siffb__haso, fgoen__ztaj, nxduz__tgwqa, eizy__vfh, jfc__xyxng, hxn__nxb
        ) = (pivot_error_checking(data, index, columns, values,
        'DataFrame.pivot'))
    if len(siffb__haso) == 0:
        if is_overload_none(data.index.name_typ):
            siffb__haso = [None]
        else:
            siffb__haso = [get_literal_value(data.index.name_typ)]
    if len(nxduz__tgwqa) == 1:
        ryomf__dkbvy = None
    else:
        ryomf__dkbvy = nxduz__tgwqa
    aws__itxkg = 'def impl(data, index=None, columns=None, values=None):\n'
    aws__itxkg += f'    pivot_values = data.iloc[:, {jfc__xyxng}].unique()\n'
    aws__itxkg += '    return bodo.hiframes.pd_dataframe_ext.pivot_impl(\n'
    if len(eizy__vfh) == 0:
        aws__itxkg += f"""        (bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)),),
"""
    else:
        aws__itxkg += '        (\n'
        for cpiec__mwkzd in eizy__vfh:
            aws__itxkg += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {cpiec__mwkzd}),
"""
        aws__itxkg += '        ),\n'
    aws__itxkg += f"""        (bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {jfc__xyxng}),),
"""
    aws__itxkg += '        (\n'
    for csptk__toc in hxn__nxb:
        aws__itxkg += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {csptk__toc}),
"""
    aws__itxkg += '        ),\n'
    aws__itxkg += '        pivot_values,\n'
    aws__itxkg += '        index_lit_tup,\n'
    aws__itxkg += '        columns_lit,\n'
    aws__itxkg += '        values_name_const,\n'
    aws__itxkg += '    )\n'
    xcyfk__phy = {}
    exec(aws__itxkg, {'bodo': bodo, 'index_lit_tup': tuple(siffb__haso),
        'columns_lit': fgoen__ztaj, 'values_name_const': ryomf__dkbvy},
        xcyfk__phy)
    impl = xcyfk__phy['impl']
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
    icgbi__oqex = dict(fill_value=fill_value, margins=margins, dropna=
        dropna, margins_name=margins_name, observed=observed, sort=sort)
    glq__vnex = dict(fill_value=None, margins=False, dropna=True,
        margins_name='All', observed=False, sort=True)
    check_unsupported_args('DataFrame.pivot_table', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    if not isinstance(data, DataFrameType):
        raise BodoError(
            "pandas.pivot_table(): 'data' argument must be a DataFrame")
    if _pivot_values is None:
        (siffb__haso, fgoen__ztaj, nxduz__tgwqa, eizy__vfh, jfc__xyxng,
            hxn__nxb) = (pivot_error_checking(data, index, columns, values,
            'DataFrame.pivot_table'))
        if len(nxduz__tgwqa) == 1:
            ryomf__dkbvy = None
        else:
            ryomf__dkbvy = nxduz__tgwqa
        aws__itxkg = 'def impl(\n'
        aws__itxkg += '    data,\n'
        aws__itxkg += '    values=None,\n'
        aws__itxkg += '    index=None,\n'
        aws__itxkg += '    columns=None,\n'
        aws__itxkg += '    aggfunc="mean",\n'
        aws__itxkg += '    fill_value=None,\n'
        aws__itxkg += '    margins=False,\n'
        aws__itxkg += '    dropna=True,\n'
        aws__itxkg += '    margins_name="All",\n'
        aws__itxkg += '    observed=False,\n'
        aws__itxkg += '    sort=True,\n'
        aws__itxkg += '    _pivot_values=None,\n'
        aws__itxkg += '):\n'
        rtf__lfjs = eizy__vfh + [jfc__xyxng] + hxn__nxb
        aws__itxkg += f'    data = data.iloc[:, {rtf__lfjs}]\n'
        ojhw__spy = siffb__haso + [fgoen__ztaj]
        aws__itxkg += (
            f'    data = data.groupby({ojhw__spy!r}, as_index=False).agg(aggfunc)\n'
            )
        aws__itxkg += (
            f'    pivot_values = data.iloc[:, {len(eizy__vfh)}].unique()\n')
        aws__itxkg += '    return bodo.hiframes.pd_dataframe_ext.pivot_impl(\n'
        aws__itxkg += '        (\n'
        for i in range(0, len(eizy__vfh)):
            aws__itxkg += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {i}),
"""
        aws__itxkg += '        ),\n'
        aws__itxkg += f"""        (bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {len(eizy__vfh)}),),
"""
        aws__itxkg += '        (\n'
        for i in range(len(eizy__vfh) + 1, len(hxn__nxb) + len(eizy__vfh) + 1):
            aws__itxkg += f"""            bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {i}),
"""
        aws__itxkg += '        ),\n'
        aws__itxkg += '        pivot_values,\n'
        aws__itxkg += '        index_lit_tup,\n'
        aws__itxkg += '        columns_lit,\n'
        aws__itxkg += '        values_name_const,\n'
        aws__itxkg += '        check_duplicates=False,\n'
        aws__itxkg += '    )\n'
        xcyfk__phy = {}
        exec(aws__itxkg, {'bodo': bodo, 'numba': numba, 'index_lit_tup':
            tuple(siffb__haso), 'columns_lit': fgoen__ztaj,
            'values_name_const': ryomf__dkbvy}, xcyfk__phy)
        impl = xcyfk__phy['impl']
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
    icgbi__oqex = dict(values=values, rownames=rownames, colnames=colnames,
        aggfunc=aggfunc, margins=margins, margins_name=margins_name, dropna
        =dropna, normalize=normalize)
    glq__vnex = dict(values=None, rownames=None, colnames=None, aggfunc=
        None, margins=False, margins_name='All', dropna=True, normalize=False)
    check_unsupported_args('pandas.crosstab', icgbi__oqex, glq__vnex,
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
    icgbi__oqex = dict(ignore_index=ignore_index, key=key)
    glq__vnex = dict(ignore_index=False, key=None)
    check_unsupported_args('DataFrame.sort_values', icgbi__oqex, glq__vnex,
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
    hycl__kgrs = set(df.columns)
    if is_overload_constant_str(df.index.name_typ):
        hycl__kgrs.add(get_overload_const_str(df.index.name_typ))
    if is_overload_constant_tuple(by):
        hhtsr__ytt = [get_overload_const_tuple(by)]
    else:
        hhtsr__ytt = get_overload_const_list(by)
    hhtsr__ytt = set((k, '') if (k, '') in hycl__kgrs else k for k in
        hhtsr__ytt)
    if len(hhtsr__ytt.difference(hycl__kgrs)) > 0:
        yiigu__xkpis = list(set(get_overload_const_list(by)).difference(
            hycl__kgrs))
        raise_bodo_error(f'sort_values(): invalid keys {yiigu__xkpis} for by.')
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
        hzron__entc = get_overload_const_list(na_position)
        for na_position in hzron__entc:
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
    icgbi__oqex = dict(axis=axis, level=level, kind=kind, sort_remaining=
        sort_remaining, ignore_index=ignore_index, key=key)
    glq__vnex = dict(axis=0, level=None, kind='quicksort', sort_remaining=
        True, ignore_index=False, key=None)
    check_unsupported_args('DataFrame.sort_index', icgbi__oqex, glq__vnex,
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
    icgbi__oqex = dict(limit=limit, downcast=downcast)
    glq__vnex = dict(limit=None, downcast=None)
    check_unsupported_args('DataFrame.fillna', icgbi__oqex, glq__vnex,
        package_name='pandas', module_name='DataFrame')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
        'DataFrame.fillna()')
    if not (is_overload_none(axis) or is_overload_zero(axis)):
        raise BodoError("DataFrame.fillna(): 'axis' argument not supported.")
    tdljd__wms = not is_overload_none(value)
    gfg__dqaby = not is_overload_none(method)
    if tdljd__wms and gfg__dqaby:
        raise BodoError(
            "DataFrame.fillna(): Cannot specify both 'value' and 'method'.")
    if not tdljd__wms and not gfg__dqaby:
        raise BodoError(
            "DataFrame.fillna(): Must specify one of 'value' and 'method'.")
    if tdljd__wms:
        rjdzc__bdtt = 'value=value'
    else:
        rjdzc__bdtt = 'method=method'
    data_args = [(
        f"df['{pwc__oyq}'].fillna({rjdzc__bdtt}, inplace=inplace)" if
        isinstance(pwc__oyq, str) else
        f'df[{pwc__oyq}].fillna({rjdzc__bdtt}, inplace=inplace)') for
        pwc__oyq in df.columns]
    aws__itxkg = """def impl(df, value=None, method=None, axis=None, inplace=False, limit=None, downcast=None):
"""
    if is_overload_true(inplace):
        aws__itxkg += '  ' + '  \n'.join(data_args) + '\n'
        xcyfk__phy = {}
        exec(aws__itxkg, {}, xcyfk__phy)
        impl = xcyfk__phy['impl']
        return impl
    else:
        return _gen_init_df(aws__itxkg, df.columns, ', '.join(elfy__zxawf +
            '.values' for elfy__zxawf in data_args))


@overload_method(DataFrameType, 'reset_index', inline='always',
    no_unliteral=True)
def overload_dataframe_reset_index(df, level=None, drop=False, inplace=
    False, col_level=0, col_fill='', _bodo_transformed=False):
    check_runtime_cols_unsupported(df, 'DataFrame.reset_index()')
    icgbi__oqex = dict(col_level=col_level, col_fill=col_fill)
    glq__vnex = dict(col_level=0, col_fill='')
    check_unsupported_args('DataFrame.reset_index', icgbi__oqex, glq__vnex,
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
    aws__itxkg = """def impl(df, level=None, drop=False, inplace=False, col_level=0, col_fill='', _bodo_transformed=False,):
"""
    aws__itxkg += (
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
        crus__glt = 'index' if 'index' not in columns else 'level_0'
        index_names = get_index_names(df.index, 'DataFrame.reset_index()',
            crus__glt)
        columns = index_names + columns
        if isinstance(df.index, MultiIndexType):
            aws__itxkg += (
                '  m_index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
                )
            zdlt__peob = ['m_index._data[{}]'.format(i) for i in range(df.
                index.nlevels)]
            data_args = zdlt__peob + data_args
        else:
            muqr__fbzgs = (
                'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
                )
            data_args = [muqr__fbzgs] + data_args
    return _gen_init_df(aws__itxkg, columns, ', '.join(data_args), 'index')


def _is_all_levels(df, level):
    kesvt__bro = len(get_index_data_arr_types(df.index))
    return is_overload_none(level) or is_overload_constant_int(level
        ) and get_overload_const_int(level
        ) == 0 and kesvt__bro == 1 or is_overload_constant_list(level
        ) and list(get_overload_const_list(level)) == list(range(kesvt__bro))


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
        yiyt__djfeg = list(range(len(df.columns)))
    elif not is_overload_constant_list(subset):
        raise_bodo_error(
            f'df.dropna(): subset argument should a constant list, not {subset}'
            )
    else:
        yddmv__edhup = get_overload_const_list(subset)
        yiyt__djfeg = []
        for brqcz__nwz in yddmv__edhup:
            if brqcz__nwz not in df.columns:
                raise_bodo_error(
                    f"df.dropna(): column '{brqcz__nwz}' not in data frame columns {df}"
                    )
            yiyt__djfeg.append(df.columns.index(brqcz__nwz))
    ioz__fzl = len(df.columns)
    data_args = ', '.join('data_{}'.format(i) for i in range(ioz__fzl))
    aws__itxkg = (
        "def impl(df, axis=0, how='any', thresh=None, subset=None, inplace=False):\n"
        )
    for i in range(ioz__fzl):
        aws__itxkg += (
            '  data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})\n'
            .format(i))
    index = (
        'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
        )
    aws__itxkg += (
        """  ({0}, index_arr) = bodo.libs.array_kernels.dropna(({0}, {1}), how, thresh, ({2},))
"""
        .format(data_args, index, ', '.join(str(a) for a in yiyt__djfeg)))
    aws__itxkg += (
        '  index = bodo.utils.conversion.index_from_array(index_arr)\n')
    return _gen_init_df(aws__itxkg, df.columns, data_args, 'index')


@overload_method(DataFrameType, 'drop', inline='always', no_unliteral=True)
def overload_dataframe_drop(df, labels=None, axis=0, index=None, columns=
    None, level=None, inplace=False, errors='raise', _bodo_transformed=False):
    check_runtime_cols_unsupported(df, 'DataFrame.drop()')
    icgbi__oqex = dict(index=index, level=level, errors=errors)
    glq__vnex = dict(index=None, level=None, errors='raise')
    check_unsupported_args('DataFrame.drop', icgbi__oqex, glq__vnex,
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
            mxowj__mplog = get_overload_const_str(labels),
        elif is_overload_constant_list(labels):
            mxowj__mplog = get_overload_const_list(labels)
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
            mxowj__mplog = get_overload_const_str(columns),
        elif is_overload_constant_list(columns):
            mxowj__mplog = get_overload_const_list(columns)
        else:
            raise_bodo_error(
                'constant list of columns expected for labels in DataFrame.drop()'
                )
    for pwc__oyq in mxowj__mplog:
        if pwc__oyq not in df.columns:
            raise_bodo_error(
                'DataFrame.drop(): column {} not in DataFrame columns {}'.
                format(pwc__oyq, df.columns))
    if len(set(mxowj__mplog)) == len(df.columns):
        raise BodoError('DataFrame.drop(): Dropping all columns not supported.'
            )
    inplace = is_overload_true(inplace)
    tykx__rax = tuple(pwc__oyq for pwc__oyq in df.columns if pwc__oyq not in
        mxowj__mplog)
    data_args = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}){}'.
        format(df.columns.index(pwc__oyq), '.copy()' if not inplace else ''
        ) for pwc__oyq in tykx__rax)
    aws__itxkg = (
        'def impl(df, labels=None, axis=0, index=None, columns=None,\n')
    aws__itxkg += (
        "     level=None, inplace=False, errors='raise', _bodo_transformed=False):\n"
        )
    index = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
    return _gen_init_df(aws__itxkg, tykx__rax, data_args, index)


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
    icgbi__oqex = dict(random_state=random_state, weights=weights, axis=
        axis, ignore_index=ignore_index)
    bhufk__bcba = dict(random_state=None, weights=None, axis=None,
        ignore_index=False)
    check_unsupported_args('DataFrame.sample', icgbi__oqex, bhufk__bcba,
        package_name='pandas', module_name='DataFrame')
    if not is_overload_none(n) and not is_overload_none(frac):
        raise BodoError(
            'DataFrame.sample(): only one of n and frac option can be selected'
            )
    ioz__fzl = len(df.columns)
    data_args = ', '.join('data_{}'.format(i) for i in range(ioz__fzl))
    tsm__pkv = ', '.join('rhs_data_{}'.format(i) for i in range(ioz__fzl))
    aws__itxkg = """def impl(df, n=None, frac=None, replace=False, weights=None, random_state=None, axis=None, ignore_index=False):
"""
    aws__itxkg += '  if (frac == 1 or n == len(df)) and not replace:\n'
    aws__itxkg += (
        '    return bodo.allgatherv(bodo.random_shuffle(df), False)\n')
    for i in range(ioz__fzl):
        aws__itxkg += (
            """  rhs_data_{0} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0})
"""
            .format(i))
    aws__itxkg += '  if frac is None:\n'
    aws__itxkg += '    frac_d = -1.0\n'
    aws__itxkg += '  else:\n'
    aws__itxkg += '    frac_d = frac\n'
    aws__itxkg += '  if n is None:\n'
    aws__itxkg += '    n_i = 0\n'
    aws__itxkg += '  else:\n'
    aws__itxkg += '    n_i = n\n'
    index = (
        'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))'
        )
    aws__itxkg += f"""  ({data_args},), index_arr = bodo.libs.array_kernels.sample_table_operation(({tsm__pkv},), {index}, n_i, frac_d, replace)
"""
    aws__itxkg += (
        '  index = bodo.utils.conversion.index_from_array(index_arr)\n')
    return bodo.hiframes.dataframe_impl._gen_init_df(aws__itxkg, df.columns,
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
    qto__lty = {'verbose': verbose, 'buf': buf, 'max_cols': max_cols,
        'memory_usage': memory_usage, 'show_counts': show_counts,
        'null_counts': null_counts}
    olakn__senkx = {'verbose': None, 'buf': None, 'max_cols': None,
        'memory_usage': None, 'show_counts': None, 'null_counts': None}
    check_unsupported_args('DataFrame.info', qto__lty, olakn__senkx,
        package_name='pandas', module_name='DataFrame')
    awxwa__gtalv = f"<class '{str(type(df)).split('.')[-1]}"
    if len(df.columns) == 0:

        def _info_impl(df, verbose=None, buf=None, max_cols=None,
            memory_usage=None, show_counts=None, null_counts=None):
            hmlh__nkwf = awxwa__gtalv + '\n'
            hmlh__nkwf += 'Index: 0 entries\n'
            hmlh__nkwf += 'Empty DataFrame'
            print(hmlh__nkwf)
        return _info_impl
    else:
        aws__itxkg = """def _info_impl(df, verbose=None, buf=None, max_cols=None, memory_usage=None, show_counts=None, null_counts=None): #pragma: no cover
"""
        aws__itxkg += '    ncols = df.shape[1]\n'
        aws__itxkg += f'    lines = "{awxwa__gtalv}\\n"\n'
        aws__itxkg += f'    lines += "{df.index}: "\n'
        aws__itxkg += (
            '    index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)\n'
            )
        if isinstance(df.index, bodo.hiframes.pd_index_ext.RangeIndexType):
            aws__itxkg += """    lines += f"{len(index)} entries, {index.start} to {index.stop-1}\\n\"
"""
        elif isinstance(df.index, bodo.hiframes.pd_index_ext.StringIndexType):
            aws__itxkg += """    lines += f"{len(index)} entries, {index[0]} to {index[len(index)-1]}\\n\"
"""
        else:
            aws__itxkg += (
                '    lines += f"{len(index)} entries, {index[0]} to {index[-1]}\\n"\n'
                )
        aws__itxkg += (
            '    lines += f"Data columns (total {ncols} columns):\\n"\n')
        aws__itxkg += (
            f'    space = {max(len(str(k)) for k in df.columns) + 1}\n')
        aws__itxkg += '    column_width = max(space, 7)\n'
        aws__itxkg += '    column= "Column"\n'
        aws__itxkg += '    underl= "------"\n'
        aws__itxkg += (
            '    lines += f"#   {column:<{column_width}} Non-Null Count  Dtype\\n"\n'
            )
        aws__itxkg += (
            '    lines += f"--- {underl:<{column_width}} --------------  -----\\n"\n'
            )
        aws__itxkg += '    mem_size = 0\n'
        aws__itxkg += (
            '    col_name = bodo.libs.str_arr_ext.pre_alloc_string_array(ncols, -1)\n'
            )
        aws__itxkg += """    non_null_count = bodo.libs.str_arr_ext.pre_alloc_string_array(ncols, -1)
"""
        aws__itxkg += (
            '    col_dtype = bodo.libs.str_arr_ext.pre_alloc_string_array(ncols, -1)\n'
            )
        rbx__tcl = dict()
        for i in range(len(df.columns)):
            aws__itxkg += f"""    non_null_count[{i}] = str(bodo.libs.array_ops.array_op_count(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i})))
"""
            mfav__adzin = f'{df.data[i].dtype}'
            if isinstance(df.data[i], bodo.CategoricalArrayType):
                mfav__adzin = 'category'
            elif isinstance(df.data[i], bodo.IntegerArrayType):
                hxg__xjfa = bodo.libs.int_arr_ext.IntDtype(df.data[i].dtype
                    ).name
                mfav__adzin = f'{hxg__xjfa[:-7]}'
            aws__itxkg += f'    col_dtype[{i}] = "{mfav__adzin}"\n'
            if mfav__adzin in rbx__tcl:
                rbx__tcl[mfav__adzin] += 1
            else:
                rbx__tcl[mfav__adzin] = 1
            aws__itxkg += f'    col_name[{i}] = "{df.columns[i]}"\n'
            aws__itxkg += f"""    mem_size += bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).nbytes
"""
        aws__itxkg += """    column_info = [f'{i:^3} {name:<{column_width}} {count} non-null      {dtype}' for i, (name, count, dtype) in enumerate(zip(col_name, non_null_count, col_dtype))]
"""
        aws__itxkg += '    for i in column_info:\n'
        aws__itxkg += "        lines += f'{i}\\n'\n"
        njce__dhgxr = ', '.join(f'{k}({rbx__tcl[k]})' for k in sorted(rbx__tcl)
            )
        aws__itxkg += f"    lines += 'dtypes: {njce__dhgxr}\\n'\n"
        aws__itxkg += '    mem_size += df.index.nbytes\n'
        aws__itxkg += '    total_size = _sizeof_fmt(mem_size)\n'
        aws__itxkg += "    lines += f'memory usage: {total_size}'\n"
        aws__itxkg += '    print(lines)\n'
        xcyfk__phy = {}
        exec(aws__itxkg, {'_sizeof_fmt': _sizeof_fmt, 'pd': pd, 'bodo':
            bodo, 'np': np}, xcyfk__phy)
        _info_impl = xcyfk__phy['_info_impl']
        return _info_impl


@overload_method(DataFrameType, 'memory_usage', inline='always',
    no_unliteral=True)
def overload_dataframe_memory_usage(df, index=True, deep=False):
    check_runtime_cols_unsupported(df, 'DataFrame.memory_usage()')
    aws__itxkg = 'def impl(df, index=True, deep=False):\n'
    data = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).nbytes'
         for i in range(len(df.columns)))
    if is_overload_true(index):
        hvp__msylw = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df).nbytes\n,')
        kylfc__fbcru = ','.join(f"'{pwc__oyq}'" for pwc__oyq in df.columns)
        arr = (
            f"bodo.utils.conversion.coerce_to_array(('Index',{kylfc__fbcru}))")
        index = f'bodo.hiframes.pd_index_ext.init_binary_str_index({arr})'
        aws__itxkg += f"""  return bodo.hiframes.pd_series_ext.init_series(({hvp__msylw}{data}), {index}, None)
"""
    else:
        uxgi__qsyou = ',' if len(df.columns) == 1 else ''
        lvwpy__xwheb = gen_const_tup(df.columns)
        aws__itxkg += f"""  return bodo.hiframes.pd_series_ext.init_series(({data}{uxgi__qsyou}), pd.Index({lvwpy__xwheb}), None)
"""
    xcyfk__phy = {}
    exec(aws__itxkg, {'bodo': bodo, 'pd': pd}, xcyfk__phy)
    impl = xcyfk__phy['impl']
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
    olmk__kzv = 'read_excel_df{}'.format(next_label())
    setattr(types, olmk__kzv, df_type)
    wwju__kayp = False
    if is_overload_constant_list(parse_dates):
        wwju__kayp = get_overload_const_list(parse_dates)
    yyqnw__elmv = ', '.join(["'{}':{}".format(cname, _get_pd_dtype_str(t)) for
        cname, t in zip(df_type.columns, df_type.data)])
    aws__itxkg = (
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
        .format(olmk__kzv, list(df_type.columns), yyqnw__elmv, wwju__kayp))
    xcyfk__phy = {}
    exec(aws__itxkg, globals(), xcyfk__phy)
    impl = xcyfk__phy['impl']
    return impl


def overload_dataframe_plot(df, x=None, y=None, kind='line', figsize=None,
    xlabel=None, ylabel=None, title=None, legend=True, fontsize=None,
    xticks=None, yticks=None, ax=None):
    try:
        import matplotlib.pyplot as plt
    except ImportError as fpx__whla:
        raise BodoError('df.plot needs matplotllib which is not installed.')
    aws__itxkg = (
        "def impl(df, x=None, y=None, kind='line', figsize=None, xlabel=None, \n"
        )
    aws__itxkg += '    ylabel=None, title=None, legend=True, fontsize=None, \n'
    aws__itxkg += '    xticks=None, yticks=None, ax=None):\n'
    if is_overload_none(ax):
        aws__itxkg += '   fig, ax = plt.subplots()\n'
    else:
        aws__itxkg += '   fig = ax.get_figure()\n'
    if not is_overload_none(figsize):
        aws__itxkg += '   fig.set_figwidth(figsize[0])\n'
        aws__itxkg += '   fig.set_figheight(figsize[1])\n'
    if is_overload_none(xlabel):
        aws__itxkg += '   xlabel = x\n'
    aws__itxkg += '   ax.set_xlabel(xlabel)\n'
    if is_overload_none(ylabel):
        aws__itxkg += '   ylabel = y\n'
    else:
        aws__itxkg += '   ax.set_ylabel(ylabel)\n'
    if not is_overload_none(title):
        aws__itxkg += '   ax.set_title(title)\n'
    if not is_overload_none(fontsize):
        aws__itxkg += '   ax.tick_params(labelsize=fontsize)\n'
    kind = get_overload_const_str(kind)
    if kind == 'line':
        if is_overload_none(x) and is_overload_none(y):
            for i in range(len(df.columns)):
                if isinstance(df.data[i], (types.Array, IntegerArrayType)
                    ) and isinstance(df.data[i].dtype, (types.Integer,
                    types.Float)):
                    aws__itxkg += (
                        f'   ax.plot(df.iloc[:, {i}], label=df.columns[{i}])\n'
                        )
        elif is_overload_none(x):
            aws__itxkg += '   ax.plot(df[y], label=y)\n'
        elif is_overload_none(y):
            jxm__byto = get_overload_const_str(x)
            xgdo__jnll = df.columns.index(jxm__byto)
            for i in range(len(df.columns)):
                if isinstance(df.data[i], (types.Array, IntegerArrayType)
                    ) and isinstance(df.data[i].dtype, (types.Integer,
                    types.Float)):
                    if xgdo__jnll != i:
                        aws__itxkg += (
                            f'   ax.plot(df[x], df.iloc[:, {i}], label=df.columns[{i}])\n'
                            )
        else:
            aws__itxkg += '   ax.plot(df[x], df[y], label=y)\n'
    elif kind == 'scatter':
        legend = False
        aws__itxkg += '   ax.scatter(df[x], df[y], s=20)\n'
        aws__itxkg += '   ax.set_ylabel(ylabel)\n'
    if not is_overload_none(xticks):
        aws__itxkg += '   ax.set_xticks(xticks)\n'
    if not is_overload_none(yticks):
        aws__itxkg += '   ax.set_yticks(yticks)\n'
    if is_overload_true(legend):
        aws__itxkg += '   ax.legend()\n'
    aws__itxkg += '   return ax\n'
    xcyfk__phy = {}
    exec(aws__itxkg, {'bodo': bodo, 'plt': plt}, xcyfk__phy)
    impl = xcyfk__phy['impl']
    return impl


@lower_builtin('df.plot', DataFrameType, types.VarArg(types.Any))
def dataframe_plot_low(context, builder, sig, args):
    impl = overload_dataframe_plot(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


def is_df_values_numpy_supported_dftyp(df_typ):
    for ktnhi__wtjv in df_typ.data:
        if not (isinstance(ktnhi__wtjv, IntegerArrayType) or isinstance(
            ktnhi__wtjv.dtype, types.Number) or ktnhi__wtjv.dtype in (bodo.
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
        sow__omk = args[0]
        bihg__smk = args[1].literal_value
        val = args[2]
        assert val != types.unknown
        lcqd__rlhp = sow__omk
        check_runtime_cols_unsupported(sow__omk, 'set_df_col()')
        if isinstance(sow__omk, DataFrameType):
            index = sow__omk.index
            if len(sow__omk.columns) == 0:
                index = bodo.hiframes.pd_index_ext.RangeIndexType(types.none)
            if isinstance(val, SeriesType):
                if len(sow__omk.columns) == 0:
                    index = val.index
                val = val.data
            if is_pd_index_type(val):
                val = bodo.utils.typing.get_index_data_arr_types(val)[0]
            if isinstance(val, types.List):
                val = dtype_to_array_type(val.dtype)
            if not is_array_typ(val):
                val = dtype_to_array_type(val)
            if bihg__smk in sow__omk.columns:
                tykx__rax = sow__omk.columns
                ehbj__rgt = sow__omk.columns.index(bihg__smk)
                zxjoc__zupzc = list(sow__omk.data)
                zxjoc__zupzc[ehbj__rgt] = val
                zxjoc__zupzc = tuple(zxjoc__zupzc)
            else:
                tykx__rax = sow__omk.columns + (bihg__smk,)
                zxjoc__zupzc = sow__omk.data + (val,)
            lcqd__rlhp = DataFrameType(zxjoc__zupzc, index, tykx__rax,
                sow__omk.dist, sow__omk.is_table_format)
        return lcqd__rlhp(*args)


SetDfColInfer.prefer_literal = True


def _parse_query_expr(expr, env, columns, cleaned_columns, index_name=None,
    join_cleaned_cols=()):
    adkbw__pww = {}

    def _rewrite_membership_op(self, node, left, right):
        tlo__bzih = node.op
        op = self.visit(tlo__bzih)
        return op, tlo__bzih, left, right

    def _maybe_evaluate_binop(self, op, op_class, lhs, rhs, eval_in_python=
        ('in', 'not in'), maybe_eval_in_python=('==', '!=', '<', '>', '<=',
        '>=')):
        res = op(lhs, rhs)
        return res
    ihwp__pag = []


    class NewFuncNode(pd.core.computation.ops.FuncNode):

        def __init__(self, name):
            if (name not in pd.core.computation.ops.MATHOPS or pd.core.
                computation.check._NUMEXPR_INSTALLED and pd.core.
                computation.check_NUMEXPR_VERSION < pd.core.computation.ops
                .LooseVersion('2.6.9') and name in ('floor', 'ceil')):
                if name not in ihwp__pag:
                    raise BodoError('"{0}" is not a supported function'.
                        format(name))
            self.name = name
            if name in ihwp__pag:
                self.func = name
            else:
                self.func = getattr(np, name)

        def __call__(self, *args):
            return pd.core.computation.ops.MathCall(self, args)

        def __repr__(self):
            return pd.io.formats.printing.pprint_thing(self.name)

    def visit_Attribute(self, node, **kwargs):
        ajx__pztq = node.attr
        value = node.value
        wlcko__gotq = pd.core.computation.ops.LOCAL_TAG
        if ajx__pztq in ('str', 'dt'):
            try:
                ppsy__bsitt = str(self.visit(value))
            except pd.core.computation.ops.UndefinedVariableError as vtko__rvb:
                col_name = vtko__rvb.args[0].split("'")[1]
                raise BodoError(
                    'df.query(): column {} is not found in dataframe columns {}'
                    .format(col_name, columns))
        else:
            ppsy__bsitt = str(self.visit(value))
        pcibk__dfrg = ppsy__bsitt, ajx__pztq
        if pcibk__dfrg in join_cleaned_cols:
            ajx__pztq = join_cleaned_cols[pcibk__dfrg]
        name = ppsy__bsitt + '.' + ajx__pztq
        if name.startswith(wlcko__gotq):
            name = name[len(wlcko__gotq):]
        if ajx__pztq in ('str', 'dt'):
            qhss__bry = columns[cleaned_columns.index(ppsy__bsitt)]
            adkbw__pww[qhss__bry] = ppsy__bsitt
            self.env.scope[name] = 0
            return self.term_type(wlcko__gotq + name, self.env)
        ihwp__pag.append(name)
        return NewFuncNode(name)

    def __str__(self):
        if isinstance(self.value, list):
            return '{}'.format(self.value)
        if isinstance(self.value, str):
            return "'{}'".format(self.value)
        return pd.io.formats.printing.pprint_thing(self.name)

    def math__str__(self):
        if self.op in ihwp__pag:
            return pd.io.formats.printing.pprint_thing('{0}({1})'.format(
                self.op, ','.join(map(str, self.operands))))
        mpy__badyh = map(lambda a:
            'bodo.hiframes.pd_series_ext.get_series_data({})'.format(str(a)
            ), self.operands)
        op = 'np.{}'.format(self.op)
        bihg__smk = (
            'bodo.hiframes.pd_index_ext.init_range_index(0, len({}), 1, None)'
            .format(str(self.operands[0])))
        return pd.io.formats.printing.pprint_thing(
            'bodo.hiframes.pd_series_ext.init_series({0}({1}), {2})'.format
            (op, ','.join(mpy__badyh), bihg__smk))

    def op__str__(self):
        qdehv__vlam = ('({0})'.format(pd.io.formats.printing.pprint_thing(
            dhnm__jqzr)) for dhnm__jqzr in self.operands)
        if self.op == 'in':
            return pd.io.formats.printing.pprint_thing(
                'bodo.hiframes.pd_dataframe_ext.val_isin_dummy({})'.format(
                ', '.join(qdehv__vlam)))
        if self.op == 'not in':
            return pd.io.formats.printing.pprint_thing(
                'bodo.hiframes.pd_dataframe_ext.val_notin_dummy({})'.format
                (', '.join(qdehv__vlam)))
        return pd.io.formats.printing.pprint_thing(' {0} '.format(self.op).
            join(qdehv__vlam))
    mhayg__qjoq = (pd.core.computation.expr.BaseExprVisitor.
        _rewrite_membership_op)
    pxz__ugke = pd.core.computation.expr.BaseExprVisitor._maybe_evaluate_binop
    cao__gqa = pd.core.computation.expr.BaseExprVisitor.visit_Attribute
    foned__ceyin = (pd.core.computation.expr.BaseExprVisitor.
        _maybe_downcast_constants)
    nfev__gqy = pd.core.computation.ops.Term.__str__
    tybs__nmbv = pd.core.computation.ops.MathCall.__str__
    fkmw__woc = pd.core.computation.ops.Op.__str__
    jtue__fqrkj = pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops
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
        ddab__myv = pd.core.computation.expr.Expr(expr, env=env)
        tdi__qza = str(ddab__myv)
    except pd.core.computation.ops.UndefinedVariableError as vtko__rvb:
        if not is_overload_none(index_name) and get_overload_const_str(
            index_name) == vtko__rvb.args[0].split("'")[1]:
            raise BodoError(
                "df.query(): Refering to named index ('{}') by name is not supported"
                .format(get_overload_const_str(index_name)))
        else:
            raise BodoError(f'df.query(): undefined variable, {vtko__rvb}')
    finally:
        pd.core.computation.expr.BaseExprVisitor._rewrite_membership_op = (
            mhayg__qjoq)
        pd.core.computation.expr.BaseExprVisitor._maybe_evaluate_binop = (
            pxz__ugke)
        pd.core.computation.expr.BaseExprVisitor.visit_Attribute = cao__gqa
        (pd.core.computation.expr.BaseExprVisitor._maybe_downcast_constants
            ) = foned__ceyin
        pd.core.computation.ops.Term.__str__ = nfev__gqy
        pd.core.computation.ops.MathCall.__str__ = tybs__nmbv
        pd.core.computation.ops.Op.__str__ = fkmw__woc
        pd.core.computation.ops.BinOp._disallow_scalar_only_bool_ops = (
            jtue__fqrkj)
    dsns__najx = pd.core.computation.parsing.clean_column_name
    adkbw__pww.update({pwc__oyq: dsns__najx(pwc__oyq) for pwc__oyq in
        columns if dsns__najx(pwc__oyq) in ddab__myv.names})
    return ddab__myv, tdi__qza, adkbw__pww


class DataFrameTupleIterator(types.SimpleIteratorType):

    def __init__(self, col_names, arr_typs):
        self.array_types = arr_typs
        self.col_names = col_names
        yig__uco = ['{}={}'.format(col_names[i], arr_typs[i]) for i in
            range(len(col_names))]
        name = 'itertuples({})'.format(','.join(yig__uco))
        upuy__jerw = namedtuple('Pandas', col_names)
        kriz__dnkaa = types.NamedTuple([_get_series_dtype(a) for a in
            arr_typs], upuy__jerw)
        super(DataFrameTupleIterator, self).__init__(name, kriz__dnkaa)

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
        ecut__qtp = [if_series_to_array_type(a) for a in args[len(args) // 2:]]
        assert 'Index' not in col_names[0]
        col_names = ['Index'] + col_names
        ecut__qtp = [types.Array(types.int64, 1, 'C')] + ecut__qtp
        euide__gbmv = DataFrameTupleIterator(col_names, ecut__qtp)
        return euide__gbmv(*args)


TypeIterTuples.prefer_literal = True


@register_model(DataFrameTupleIterator)
class DataFrameTupleIteratorModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        iyvu__fes = [('index', types.EphemeralPointer(types.uintp))] + [(
            'array{}'.format(i), arr) for i, arr in enumerate(fe_type.
            array_types[1:])]
        super(DataFrameTupleIteratorModel, self).__init__(dmm, fe_type,
            iyvu__fes)

    def from_return(self, builder, value):
        return value


@lower_builtin(get_itertuples, types.VarArg(types.Any))
def get_itertuples_impl(context, builder, sig, args):
    bth__pjgem = args[len(args) // 2:]
    pyv__hyagk = sig.args[len(sig.args) // 2:]
    ntjou__igyzt = context.make_helper(builder, sig.return_type)
    wgm__ibhlj = context.get_constant(types.intp, 0)
    dug__riw = cgutils.alloca_once_value(builder, wgm__ibhlj)
    ntjou__igyzt.index = dug__riw
    for i, arr in enumerate(bth__pjgem):
        setattr(ntjou__igyzt, 'array{}'.format(i), arr)
    for arr, arr_typ in zip(bth__pjgem, pyv__hyagk):
        context.nrt.incref(builder, arr_typ, arr)
    res = ntjou__igyzt._getvalue()
    return impl_ret_new_ref(context, builder, sig.return_type, res)


@lower_builtin('getiter', DataFrameTupleIterator)
def getiter_itertuples(context, builder, sig, args):
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@lower_builtin('iternext', DataFrameTupleIterator)
@iternext_impl(RefType.UNTRACKED)
def iternext_itertuples(context, builder, sig, args, result):
    kykm__rgx, = sig.args
    ivxk__hcd, = args
    ntjou__igyzt = context.make_helper(builder, kykm__rgx, value=ivxk__hcd)
    lyosb__itxx = signature(types.intp, kykm__rgx.array_types[1])
    vjhm__geee = context.compile_internal(builder, lambda a: len(a),
        lyosb__itxx, [ntjou__igyzt.array0])
    index = builder.load(ntjou__igyzt.index)
    qopwx__aokdo = builder.icmp(lc.ICMP_SLT, index, vjhm__geee)
    result.set_valid(qopwx__aokdo)
    with builder.if_then(qopwx__aokdo):
        values = [index]
        for i, arr_typ in enumerate(kykm__rgx.array_types[1:]):
            wrmrd__vtspf = getattr(ntjou__igyzt, 'array{}'.format(i))
            if arr_typ == types.Array(types.NPDatetime('ns'), 1, 'C'):
                vbfb__fiqfr = signature(pd_timestamp_type, arr_typ, types.intp)
                val = context.compile_internal(builder, lambda a, i: bodo.
                    hiframes.pd_timestamp_ext.
                    convert_datetime64_to_timestamp(np.int64(a[i])),
                    vbfb__fiqfr, [wrmrd__vtspf, index])
            else:
                vbfb__fiqfr = signature(arr_typ.dtype, arr_typ, types.intp)
                val = context.compile_internal(builder, lambda a, i: a[i],
                    vbfb__fiqfr, [wrmrd__vtspf, index])
            values.append(val)
        value = context.make_tuple(builder, kykm__rgx.yield_type, values)
        result.yield_(value)
        xqa__dless = cgutils.increment_index(builder, index)
        builder.store(xqa__dless, ntjou__igyzt.index)


def _analyze_op_pair_first(self, scope, equiv_set, expr, lhs):
    typ = self.typemap[expr.value.name].first_type
    if not isinstance(typ, types.NamedTuple):
        return None
    lhs = ir.Var(scope, mk_unique_var('tuple_var'), expr.loc)
    self.typemap[lhs.name] = typ
    rhs = ir.Expr.pair_first(expr.value, expr.loc)
    bpf__ate = ir.Assign(rhs, lhs, expr.loc)
    kdhea__aisq = lhs
    wnuv__keflg = []
    ylgja__ghng = []
    rxw__sstgi = typ.count
    for i in range(rxw__sstgi):
        ucs__uufwa = ir.Var(kdhea__aisq.scope, mk_unique_var('{}_size{}'.
            format(kdhea__aisq.name, i)), kdhea__aisq.loc)
        airqa__gbmrs = ir.Expr.static_getitem(lhs, i, None, kdhea__aisq.loc)
        self.calltypes[airqa__gbmrs] = None
        wnuv__keflg.append(ir.Assign(airqa__gbmrs, ucs__uufwa, kdhea__aisq.loc)
            )
        self._define(equiv_set, ucs__uufwa, types.intp, airqa__gbmrs)
        ylgja__ghng.append(ucs__uufwa)
    qoqht__anu = tuple(ylgja__ghng)
    return numba.parfors.array_analysis.ArrayAnalysis.AnalyzeResult(shape=
        qoqht__anu, pre=[bpf__ate] + wnuv__keflg)


numba.parfors.array_analysis.ArrayAnalysis._analyze_op_pair_first = (
    _analyze_op_pair_first)
