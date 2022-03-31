"""
Implement pd.DataFrame typing and data model handling.
"""
import json
import operator
from urllib.parse import urlparse
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
import pyarrow as pa
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import impl_ret_borrowed, lower_constant
from numba.core.typing.templates import AbstractTemplate, bound_function, infer_global, signature
from numba.cpython.listobj import ListInstance
from numba.extending import infer_getattr, intrinsic, lower_builtin, lower_cast, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_model
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
from bodo.hiframes.datetime_date_ext import datetime_date_array_type
from bodo.hiframes.pd_categorical_ext import CategoricalArrayType
from bodo.hiframes.pd_index_ext import HeterogeneousIndexType, NumericIndexType, RangeIndexType, is_pd_index_type
from bodo.hiframes.pd_multi_index_ext import MultiIndexType
from bodo.hiframes.pd_series_ext import HeterogeneousSeriesType, SeriesType
from bodo.hiframes.series_indexing import SeriesIlocType
from bodo.hiframes.table import Table, TableType, decode_if_dict_table, get_table_data, set_table_data_codegen
from bodo.io import json_cpp
from bodo.libs.array import arr_info_list_to_table, array_to_info, delete_info_decref_array, delete_table, delete_table_decref_arrays, info_from_table, info_to_array, py_table_to_cpp_table, shuffle_table
from bodo.libs.array_item_arr_ext import ArrayItemArrayType
from bodo.libs.binary_arr_ext import binary_array_type
from bodo.libs.bool_arr_ext import boolean_array
from bodo.libs.decimal_arr_ext import DecimalArrayType
from bodo.libs.distributed_api import bcast_scalar
from bodo.libs.int_arr_ext import IntegerArrayType
from bodo.libs.str_arr_ext import str_arr_from_sequence
from bodo.libs.str_ext import string_type, unicode_to_utf8
from bodo.libs.struct_arr_ext import StructArrayType
from bodo.utils.cg_helpers import is_ll_eq
from bodo.utils.conversion import fix_arr_dtype, index_to_array
from bodo.utils.templates import OverloadedKeyAttributeTemplate
from bodo.utils.transform import gen_const_tup, get_const_func_output_type, get_const_tup_vals
from bodo.utils.typing import BodoError, BodoWarning, check_unsupported_args, create_unsupported_overload, decode_if_dict_array, dtype_to_array_type, get_index_data_arr_types, get_literal_value, get_overload_const, get_overload_const_bool, get_overload_const_int, get_overload_const_list, get_overload_const_str, get_udf_error_msg, get_udf_out_arr_type, is_heterogeneous_tuple_type, is_iterable_type, is_literal_type, is_overload_bool, is_overload_constant_bool, is_overload_constant_int, is_overload_constant_str, is_overload_false, is_overload_int, is_overload_none, is_overload_true, is_str_arr_type, is_tuple_like_type, raise_bodo_error, to_nullable_type, to_str_arr_if_dict_array
from bodo.utils.utils import is_null_pointer
_json_write = types.ExternalFunction('json_write', types.void(types.voidptr,
    types.voidptr, types.int64, types.int64, types.bool_, types.bool_,
    types.voidptr))
ll.add_symbol('json_write', json_cpp.json_write)


class DataFrameType(types.ArrayCompatible):
    ndim = 2

    def __init__(self, data=None, index=None, columns=None, dist=None,
        is_table_format=False):
        from bodo.transforms.distributed_analysis import Distribution
        self.data = data
        if index is None:
            index = RangeIndexType(types.none)
        self.index = index
        self.columns = columns
        dist = Distribution.OneD_Var if dist is None else dist
        self.dist = dist
        self.is_table_format = is_table_format
        if columns is None:
            assert is_table_format, 'Determining columns at runtime is only supported for DataFrame with table format'
            self.table_type = TableType(tuple(data[:-1]), True)
        else:
            self.table_type = TableType(data) if is_table_format else None
        super(DataFrameType, self).__init__(name=
            f'dataframe({data}, {index}, {columns}, {dist}, {is_table_format})'
            )

    def __str__(self):
        if not self.has_runtime_cols and len(self.columns) > 20:
            tdw__estcd = f'{len(self.data)} columns of types {set(self.data)}'
            ohcau__xhdv = (
                f"('{self.columns[0]}', '{self.columns[1]}', ..., '{self.columns[-1]}')"
                )
            return (
                f'dataframe({tdw__estcd}, {self.index}, {ohcau__xhdv}, {self.dist}, {self.is_table_format})'
                )
        return super().__str__()

    def copy(self, data=None, index=None, columns=None, dist=None,
        is_table_format=None):
        if data is None:
            data = self.data
        if columns is None:
            columns = self.columns
        if index is None:
            index = self.index
        if dist is None:
            dist = self.dist
        if is_table_format is None:
            is_table_format = self.is_table_format
        return DataFrameType(data, index, columns, dist, is_table_format)

    @property
    def has_runtime_cols(self):
        return self.columns is None

    @property
    def runtime_colname_typ(self):
        return self.data[-1] if self.has_runtime_cols else None

    @property
    def runtime_data_types(self):
        return self.data[:-1] if self.has_runtime_cols else self.data

    @property
    def as_array(self):
        return types.Array(types.undefined, 2, 'C')

    @property
    def key(self):
        return (self.data, self.index, self.columns, self.dist, self.
            is_table_format)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)

    def unify(self, typingctx, other):
        from bodo.transforms.distributed_analysis import Distribution
        if (isinstance(other, DataFrameType) and len(other.data) == len(
            self.data) and other.columns == self.columns and other.
            has_runtime_cols == self.has_runtime_cols):
            tqy__mgy = (self.index if self.index == other.index else self.
                index.unify(typingctx, other.index))
            data = tuple(slc__krutd.unify(typingctx, euim__skjul) if 
                slc__krutd != euim__skjul else slc__krutd for slc__krutd,
                euim__skjul in zip(self.data, other.data))
            dist = Distribution(min(self.dist.value, other.dist.value))
            if tqy__mgy is not None and None not in data:
                return DataFrameType(data, tqy__mgy, self.columns, dist,
                    self.is_table_format)
        if isinstance(other, DataFrameType) and len(self.data
            ) == 0 and not self.has_runtime_cols:
            return other

    def can_convert_to(self, typingctx, other):
        from numba.core.typeconv import Conversion
        if (isinstance(other, DataFrameType) and self.data == other.data and
            self.index == other.index and self.columns == other.columns and
            self.dist != other.dist and self.has_runtime_cols == other.
            has_runtime_cols):
            return Conversion.safe

    def is_precise(self):
        return all(slc__krutd.is_precise() for slc__krutd in self.data
            ) and self.index.is_precise()

    def replace_col_type(self, col_name, new_type):
        if col_name not in self.columns:
            raise ValueError(
                f"DataFrameType.replace_col_type replaced column must be found in the DataFrameType. '{col_name}' not found in DataFrameType with columns {self.columns}"
                )
        huhg__yqx = self.columns.index(col_name)
        ikd__vmoed = tuple(list(self.data[:huhg__yqx]) + [new_type] + list(
            self.data[huhg__yqx + 1:]))
        return DataFrameType(ikd__vmoed, self.index, self.columns, self.
            dist, self.is_table_format)


def check_runtime_cols_unsupported(df, func_name):
    if isinstance(df, DataFrameType) and df.has_runtime_cols:
        raise BodoError(
            f'{func_name} on DataFrames with columns determined at runtime is not yet supported. Please return the DataFrame to regular Python to update typing information.'
            )


class DataFramePayloadType(types.Type):

    def __init__(self, df_type):
        self.df_type = df_type
        super(DataFramePayloadType, self).__init__(name=
            f'DataFramePayloadType({df_type})')

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(DataFramePayloadType)
class DataFramePayloadModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        data_typ = types.Tuple(fe_type.df_type.data)
        if fe_type.df_type.is_table_format:
            data_typ = types.Tuple([fe_type.df_type.table_type])
        uij__gfbny = [('data', data_typ), ('index', fe_type.df_type.index),
            ('parent', types.pyobject)]
        if fe_type.df_type.has_runtime_cols:
            uij__gfbny.append(('columns', fe_type.df_type.runtime_colname_typ))
        super(DataFramePayloadModel, self).__init__(dmm, fe_type, uij__gfbny)


@register_model(DataFrameType)
class DataFrameModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = DataFramePayloadType(fe_type)
        uij__gfbny = [('meminfo', types.MemInfoPointer(payload_type)), (
            'parent', types.pyobject)]
        super(DataFrameModel, self).__init__(dmm, fe_type, uij__gfbny)


make_attribute_wrapper(DataFrameType, 'meminfo', '_meminfo')


@infer_getattr
class DataFrameAttribute(OverloadedKeyAttributeTemplate):
    key = DataFrameType

    def resolve_shape(self, df):
        return types.Tuple([types.int64, types.int64])

    @bound_function('df.head')
    def resolve_head(self, df, args, kws):
        func_name = 'DataFrame.head'
        check_runtime_cols_unsupported(df, f'{func_name}()')
        qxa__zxlfh = 'n',
        yuzp__dbgwm = {'n': 5}
        zcdb__jqfq, argj__xwint = bodo.utils.typing.fold_typing_args(func_name,
            args, kws, qxa__zxlfh, yuzp__dbgwm)
        lnqm__yifb = argj__xwint[0]
        if not is_overload_int(lnqm__yifb):
            raise BodoError(f"{func_name}(): 'n' must be an Integer")
        qkt__hck = df.copy(is_table_format=False)
        return qkt__hck(*argj__xwint).replace(pysig=zcdb__jqfq)

    @bound_function('df.corr')
    def resolve_corr(self, df, args, kws):
        func_name = 'DataFrame.corr'
        check_runtime_cols_unsupported(df, f'{func_name}()')
        amkn__bmx = (df,) + args
        qxa__zxlfh = 'df', 'method', 'min_periods'
        yuzp__dbgwm = {'method': 'pearson', 'min_periods': 1}
        cnal__jkw = 'method',
        zcdb__jqfq, argj__xwint = bodo.utils.typing.fold_typing_args(func_name,
            amkn__bmx, kws, qxa__zxlfh, yuzp__dbgwm, cnal__jkw)
        zrewe__hhby = argj__xwint[2]
        if not is_overload_int(zrewe__hhby):
            raise BodoError(f"{func_name}(): 'min_periods' must be an Integer")
        rwv__uhsjn = []
        xhqrn__kfpch = []
        for ixz__sio, myf__hqqss in zip(df.columns, df.data):
            if bodo.utils.typing._is_pandas_numeric_dtype(myf__hqqss.dtype):
                rwv__uhsjn.append(ixz__sio)
                xhqrn__kfpch.append(types.Array(types.float64, 1, 'A'))
        if len(rwv__uhsjn) == 0:
            raise_bodo_error('DataFrame.corr(): requires non-empty dataframe')
        xhqrn__kfpch = tuple(xhqrn__kfpch)
        rwv__uhsjn = tuple(rwv__uhsjn)
        index_typ = bodo.utils.typing.type_col_to_index(rwv__uhsjn)
        qkt__hck = DataFrameType(xhqrn__kfpch, index_typ, rwv__uhsjn)
        return qkt__hck(*argj__xwint).replace(pysig=zcdb__jqfq)

    @bound_function('df.pipe', no_unliteral=True)
    def resolve_pipe(self, df, args, kws):
        check_runtime_cols_unsupported(df, 'DataFrame.pipe()')
        return bodo.hiframes.pd_groupby_ext.resolve_obj_pipe(self, df, args,
            kws, 'DataFrame')

    @bound_function('df.apply', no_unliteral=True)
    def resolve_apply(self, df, args, kws):
        check_runtime_cols_unsupported(df, 'DataFrame.apply()')
        kws = dict(kws)
        tap__zszz = args[0] if len(args) > 0 else kws.pop('func', None)
        axis = args[1] if len(args) > 1 else kws.pop('axis', types.literal(0))
        laee__hky = args[2] if len(args) > 2 else kws.pop('raw', types.
            literal(False))
        bdz__jsx = args[3] if len(args) > 3 else kws.pop('result_type',
            types.none)
        niid__tjwm = args[4] if len(args) > 4 else kws.pop('args', types.
            Tuple([]))
        wnn__mqqx = dict(raw=laee__hky, result_type=bdz__jsx)
        hizyl__pqo = dict(raw=False, result_type=None)
        check_unsupported_args('Dataframe.apply', wnn__mqqx, hizyl__pqo,
            package_name='pandas', module_name='DataFrame')
        omsw__ojco = True
        if types.unliteral(tap__zszz) == types.unicode_type:
            if not is_overload_constant_str(tap__zszz):
                raise BodoError(
                    f'DataFrame.apply(): string argument (for builtins) must be a compile time constant'
                    )
            omsw__ojco = False
        if not is_overload_constant_int(axis):
            raise BodoError(
                'Dataframe.apply(): axis argument must be a compile time constant.'
                )
        byvsq__bzlpr = get_overload_const_int(axis)
        if omsw__ojco and byvsq__bzlpr != 1:
            raise BodoError(
                'Dataframe.apply(): only axis=1 supported for user-defined functions'
                )
        elif byvsq__bzlpr not in (0, 1):
            raise BodoError('Dataframe.apply(): axis must be either 0 or 1')
        kqn__fuks = []
        for arr_typ in df.data:
            njrp__fpnn = SeriesType(arr_typ.dtype, arr_typ, df.index,
                string_type)
            bcj__nkdsz = self.context.resolve_function_type(operator.
                getitem, (SeriesIlocType(njrp__fpnn), types.int64), {}
                ).return_type
            kqn__fuks.append(bcj__nkdsz)
        jeazx__ccg = types.none
        yzcrv__ghhkt = HeterogeneousIndexType(types.BaseTuple.from_types(
            tuple(types.literal(ixz__sio) for ixz__sio in df.columns)), None)
        snqlz__rqxx = types.BaseTuple.from_types(kqn__fuks)
        tqz__tlr = df.index.dtype
        if tqz__tlr == types.NPDatetime('ns'):
            tqz__tlr = bodo.pd_timestamp_type
        if tqz__tlr == types.NPTimedelta('ns'):
            tqz__tlr = bodo.pd_timedelta_type
        if is_heterogeneous_tuple_type(snqlz__rqxx):
            rmd__qoj = HeterogeneousSeriesType(snqlz__rqxx, yzcrv__ghhkt,
                tqz__tlr)
        else:
            rmd__qoj = SeriesType(snqlz__rqxx.dtype, snqlz__rqxx,
                yzcrv__ghhkt, tqz__tlr)
        supvs__lzvo = rmd__qoj,
        if niid__tjwm is not None:
            supvs__lzvo += tuple(niid__tjwm.types)
        try:
            if not omsw__ojco:
                khwvv__zuryd = bodo.utils.transform.get_udf_str_return_type(df,
                    get_overload_const_str(tap__zszz), self.context,
                    'DataFrame.apply', axis if byvsq__bzlpr == 1 else None)
            else:
                khwvv__zuryd = get_const_func_output_type(tap__zszz,
                    supvs__lzvo, kws, self.context, numba.core.registry.
                    cpu_target.target_context)
        except Exception as isto__sluin:
            raise_bodo_error(get_udf_error_msg('DataFrame.apply()',
                isto__sluin))
        if omsw__ojco:
            if not (is_overload_constant_int(axis) and 
                get_overload_const_int(axis) == 1):
                raise BodoError(
                    'Dataframe.apply(): only user-defined functions with axis=1 supported'
                    )
            if isinstance(khwvv__zuryd, (SeriesType, HeterogeneousSeriesType)
                ) and khwvv__zuryd.const_info is None:
                raise BodoError(
                    'Invalid Series output in UDF (Series with constant length and constant Index value expected)'
                    )
            if isinstance(khwvv__zuryd, HeterogeneousSeriesType):
                bivm__wzvzy, xwip__oilqk = khwvv__zuryd.const_info
                qnwhk__ockuy = tuple(dtype_to_array_type(xsj__yrh) for
                    xsj__yrh in khwvv__zuryd.data.types)
                akmt__dyxo = DataFrameType(qnwhk__ockuy, df.index, xwip__oilqk)
            elif isinstance(khwvv__zuryd, SeriesType):
                cnsg__sdwvq, xwip__oilqk = khwvv__zuryd.const_info
                qnwhk__ockuy = tuple(dtype_to_array_type(khwvv__zuryd.dtype
                    ) for bivm__wzvzy in range(cnsg__sdwvq))
                akmt__dyxo = DataFrameType(qnwhk__ockuy, df.index, xwip__oilqk)
            else:
                ciev__wzl = get_udf_out_arr_type(khwvv__zuryd)
                akmt__dyxo = SeriesType(ciev__wzl.dtype, ciev__wzl, df.
                    index, None)
        else:
            akmt__dyxo = khwvv__zuryd
        mxu__cezwb = ', '.join("{} = ''".format(slc__krutd) for slc__krutd in
            kws.keys())
        tzeyj__jjmo = f"""def apply_stub(func, axis=0, raw=False, result_type=None, args=(), {mxu__cezwb}):
"""
        tzeyj__jjmo += '    pass\n'
        gcyu__prty = {}
        exec(tzeyj__jjmo, {}, gcyu__prty)
        qsqif__afy = gcyu__prty['apply_stub']
        zcdb__jqfq = numba.core.utils.pysignature(qsqif__afy)
        rxvy__hymu = (tap__zszz, axis, laee__hky, bdz__jsx, niid__tjwm
            ) + tuple(kws.values())
        return signature(akmt__dyxo, *rxvy__hymu).replace(pysig=zcdb__jqfq)

    @bound_function('df.plot', no_unliteral=True)
    def resolve_plot(self, df, args, kws):
        func_name = 'DataFrame.plot'
        check_runtime_cols_unsupported(df, f'{func_name}()')
        qxa__zxlfh = ('x', 'y', 'kind', 'figsize', 'ax', 'subplots',
            'sharex', 'sharey', 'layout', 'use_index', 'title', 'grid',
            'legend', 'style', 'logx', 'logy', 'loglog', 'xticks', 'yticks',
            'xlim', 'ylim', 'rot', 'fontsize', 'colormap', 'table', 'yerr',
            'xerr', 'secondary_y', 'sort_columns', 'xlabel', 'ylabel',
            'position', 'stacked', 'mark_right', 'include_bool', 'backend')
        yuzp__dbgwm = {'x': None, 'y': None, 'kind': 'line', 'figsize':
            None, 'ax': None, 'subplots': False, 'sharex': None, 'sharey': 
            False, 'layout': None, 'use_index': True, 'title': None, 'grid':
            None, 'legend': True, 'style': None, 'logx': False, 'logy': 
            False, 'loglog': False, 'xticks': None, 'yticks': None, 'xlim':
            None, 'ylim': None, 'rot': None, 'fontsize': None, 'colormap':
            None, 'table': False, 'yerr': None, 'xerr': None, 'secondary_y':
            False, 'sort_columns': False, 'xlabel': None, 'ylabel': None,
            'position': 0.5, 'stacked': False, 'mark_right': True,
            'include_bool': False, 'backend': None}
        cnal__jkw = ('subplots', 'sharex', 'sharey', 'layout', 'use_index',
            'grid', 'style', 'logx', 'logy', 'loglog', 'xlim', 'ylim',
            'rot', 'colormap', 'table', 'yerr', 'xerr', 'sort_columns',
            'secondary_y', 'colorbar', 'position', 'stacked', 'mark_right',
            'include_bool', 'backend')
        zcdb__jqfq, argj__xwint = bodo.utils.typing.fold_typing_args(func_name,
            args, kws, qxa__zxlfh, yuzp__dbgwm, cnal__jkw)
        dypgx__lho = argj__xwint[2]
        if not is_overload_constant_str(dypgx__lho):
            raise BodoError(
                f"{func_name}: kind must be a constant string and one of ('line', 'scatter')."
                )
        ledbu__lptbj = argj__xwint[0]
        if not is_overload_none(ledbu__lptbj) and not (is_overload_int(
            ledbu__lptbj) or is_overload_constant_str(ledbu__lptbj)):
            raise BodoError(
                f'{func_name}: x must be a constant column name, constant integer, or None.'
                )
        if is_overload_constant_str(ledbu__lptbj):
            pffb__xcpb = get_overload_const_str(ledbu__lptbj)
            if pffb__xcpb not in df.columns:
                raise BodoError(f'{func_name}: {pffb__xcpb} column not found.')
        elif is_overload_int(ledbu__lptbj):
            qalkt__nvoso = get_overload_const_int(ledbu__lptbj)
            if qalkt__nvoso > len(df.columns):
                raise BodoError(
                    f'{func_name}: x: {qalkt__nvoso} is out of bounds for axis 0 with size {len(df.columns)}'
                    )
            ledbu__lptbj = df.columns[ledbu__lptbj]
        ero__pfgam = argj__xwint[1]
        if not is_overload_none(ero__pfgam) and not (is_overload_int(
            ero__pfgam) or is_overload_constant_str(ero__pfgam)):
            raise BodoError(
                'df.plot(): y must be a constant column name, constant integer, or None.'
                )
        if is_overload_constant_str(ero__pfgam):
            pvc__aadk = get_overload_const_str(ero__pfgam)
            if pvc__aadk not in df.columns:
                raise BodoError(f'{func_name}: {pvc__aadk} column not found.')
        elif is_overload_int(ero__pfgam):
            rus__qee = get_overload_const_int(ero__pfgam)
            if rus__qee > len(df.columns):
                raise BodoError(
                    f'{func_name}: y: {rus__qee} is out of bounds for axis 0 with size {len(df.columns)}'
                    )
            ero__pfgam = df.columns[ero__pfgam]
        eyjbe__tsat = argj__xwint[3]
        if not is_overload_none(eyjbe__tsat) and not is_tuple_like_type(
            eyjbe__tsat):
            raise BodoError(
                f'{func_name}: figsize must be a constant numeric tuple (width, height) or None.'
                )
        anpxg__wbn = argj__xwint[10]
        if not is_overload_none(anpxg__wbn) and not is_overload_constant_str(
            anpxg__wbn):
            raise BodoError(
                f'{func_name}: title must be a constant string or None.')
        wzjil__zoy = argj__xwint[12]
        if not is_overload_bool(wzjil__zoy):
            raise BodoError(f'{func_name}: legend must be a boolean type.')
        wxuba__gbxw = argj__xwint[17]
        if not is_overload_none(wxuba__gbxw) and not is_tuple_like_type(
            wxuba__gbxw):
            raise BodoError(
                f'{func_name}: xticks must be a constant tuple or None.')
        mdls__qzre = argj__xwint[18]
        if not is_overload_none(mdls__qzre) and not is_tuple_like_type(
            mdls__qzre):
            raise BodoError(
                f'{func_name}: yticks must be a constant tuple or None.')
        jvi__amm = argj__xwint[22]
        if not is_overload_none(jvi__amm) and not is_overload_int(jvi__amm):
            raise BodoError(
                f'{func_name}: fontsize must be an integer or None.')
        hvd__odp = argj__xwint[29]
        if not is_overload_none(hvd__odp) and not is_overload_constant_str(
            hvd__odp):
            raise BodoError(
                f'{func_name}: xlabel must be a constant string or None.')
        uyzkz__rpfpy = argj__xwint[30]
        if not is_overload_none(uyzkz__rpfpy) and not is_overload_constant_str(
            uyzkz__rpfpy):
            raise BodoError(
                f'{func_name}: ylabel must be a constant string or None.')
        tfkk__qfc = types.List(types.mpl_line_2d_type)
        dypgx__lho = get_overload_const_str(dypgx__lho)
        if dypgx__lho == 'scatter':
            if is_overload_none(ledbu__lptbj) and is_overload_none(ero__pfgam):
                raise BodoError(
                    f'{func_name}: {dypgx__lho} requires an x and y column.')
            elif is_overload_none(ledbu__lptbj):
                raise BodoError(
                    f'{func_name}: {dypgx__lho} x column is missing.')
            elif is_overload_none(ero__pfgam):
                raise BodoError(
                    f'{func_name}: {dypgx__lho} y column is missing.')
            tfkk__qfc = types.mpl_path_collection_type
        elif dypgx__lho != 'line':
            raise BodoError(f'{func_name}: {dypgx__lho} plot is not supported.'
                )
        return signature(tfkk__qfc, *argj__xwint).replace(pysig=zcdb__jqfq)

    def generic_resolve(self, df, attr):
        if self._is_existing_attr(attr):
            return
        check_runtime_cols_unsupported(df,
            'Acessing DataFrame columns by attribute')
        if attr in df.columns:
            bod__qisa = df.columns.index(attr)
            arr_typ = df.data[bod__qisa]
            return SeriesType(arr_typ.dtype, arr_typ, df.index, types.
                StringLiteral(attr))
        if len(df.columns) > 0 and isinstance(df.columns[0], tuple):
            ahev__sufax = []
            ikd__vmoed = []
            pevf__tzf = False
            for i, nile__tgtn in enumerate(df.columns):
                if nile__tgtn[0] != attr:
                    continue
                pevf__tzf = True
                ahev__sufax.append(nile__tgtn[1] if len(nile__tgtn) == 2 else
                    nile__tgtn[1:])
                ikd__vmoed.append(df.data[i])
            if pevf__tzf:
                return DataFrameType(tuple(ikd__vmoed), df.index, tuple(
                    ahev__sufax))


DataFrameAttribute._no_unliteral = True


@overload(operator.getitem, no_unliteral=True)
def namedtuple_getitem_overload(tup, idx):
    if isinstance(tup, types.BaseNamedTuple) and is_overload_constant_str(idx):
        ppnbe__idmeh = get_overload_const_str(idx)
        val_ind = tup.instance_class._fields.index(ppnbe__idmeh)
        return lambda tup, idx: tup[val_ind]


def decref_df_data(context, builder, payload, df_type):
    if df_type.is_table_format:
        context.nrt.decref(builder, df_type.table_type, builder.
            extract_value(payload.data, 0))
        context.nrt.decref(builder, df_type.index, payload.index)
        if df_type.has_runtime_cols:
            context.nrt.decref(builder, df_type.data[-1], payload.columns)
        return
    for i in range(len(df_type.data)):
        hkarx__aycqp = builder.extract_value(payload.data, i)
        context.nrt.decref(builder, df_type.data[i], hkarx__aycqp)
    context.nrt.decref(builder, df_type.index, payload.index)


def define_df_dtor(context, builder, df_type, payload_type):
    gnuq__kjnn = builder.module
    jljz__dpfkq = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    kzzbp__gbu = cgutils.get_or_insert_function(gnuq__kjnn, jljz__dpfkq,
        name='.dtor.df.{}'.format(df_type))
    if not kzzbp__gbu.is_declaration:
        return kzzbp__gbu
    kzzbp__gbu.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(kzzbp__gbu.append_basic_block())
    rrvik__jhg = kzzbp__gbu.args[0]
    hcp__mtuan = context.get_value_type(payload_type).as_pointer()
    cyj__eovjb = builder.bitcast(rrvik__jhg, hcp__mtuan)
    payload = context.make_helper(builder, payload_type, ref=cyj__eovjb)
    decref_df_data(context, builder, payload, df_type)
    has_parent = cgutils.is_not_null(builder, payload.parent)
    with builder.if_then(has_parent):
        gqiiw__bdecn = context.get_python_api(builder)
        tao__xop = gqiiw__bdecn.gil_ensure()
        gqiiw__bdecn.decref(payload.parent)
        gqiiw__bdecn.gil_release(tao__xop)
    builder.ret_void()
    return kzzbp__gbu


def construct_dataframe(context, builder, df_type, data_tup, index_val,
    parent=None, colnames=None):
    payload_type = DataFramePayloadType(df_type)
    myw__lvx = cgutils.create_struct_proxy(payload_type)(context, builder)
    myw__lvx.data = data_tup
    myw__lvx.index = index_val
    if colnames is not None:
        assert df_type.has_runtime_cols, 'construct_dataframe can only provide colnames if columns are determined at runtime'
        myw__lvx.columns = colnames
    sfr__xitd = context.get_value_type(payload_type)
    emgi__ans = context.get_abi_sizeof(sfr__xitd)
    kmwe__fof = define_df_dtor(context, builder, df_type, payload_type)
    ibwjf__kwo = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, emgi__ans), kmwe__fof)
    rgzm__ynqyc = context.nrt.meminfo_data(builder, ibwjf__kwo)
    lyw__finm = builder.bitcast(rgzm__ynqyc, sfr__xitd.as_pointer())
    rzsq__styt = cgutils.create_struct_proxy(df_type)(context, builder)
    rzsq__styt.meminfo = ibwjf__kwo
    if parent is None:
        rzsq__styt.parent = cgutils.get_null_value(rzsq__styt.parent.type)
    else:
        rzsq__styt.parent = parent
        myw__lvx.parent = parent
        has_parent = cgutils.is_not_null(builder, parent)
        with builder.if_then(has_parent):
            gqiiw__bdecn = context.get_python_api(builder)
            tao__xop = gqiiw__bdecn.gil_ensure()
            gqiiw__bdecn.incref(parent)
            gqiiw__bdecn.gil_release(tao__xop)
    builder.store(myw__lvx._getvalue(), lyw__finm)
    return rzsq__styt._getvalue()


@intrinsic
def init_runtime_cols_dataframe(typingctx, data_typ, index_typ,
    colnames_index_typ=None):
    assert isinstance(data_typ, types.BaseTuple) and isinstance(data_typ.
        dtype, TableType
        ) and data_typ.dtype.has_runtime_cols, 'init_runtime_cols_dataframe must be called with a table that determines columns at runtime.'
    assert bodo.hiframes.pd_index_ext.is_pd_index_type(colnames_index_typ
        ) or isinstance(colnames_index_typ, bodo.hiframes.
        pd_multi_index_ext.MultiIndexType), 'Column names must be an index'
    if isinstance(data_typ.dtype.arr_types, types.UniTuple):
        bcc__lrfrw = [data_typ.dtype.arr_types.dtype] * len(data_typ.dtype.
            arr_types)
    else:
        bcc__lrfrw = [xsj__yrh for xsj__yrh in data_typ.dtype.arr_types]
    obzc__jfmz = DataFrameType(tuple(bcc__lrfrw + [colnames_index_typ]),
        index_typ, None, is_table_format=True)

    def codegen(context, builder, signature, args):
        df_type = signature.return_type
        data_tup, index, col_names = args
        parent = None
        dagq__wbb = construct_dataframe(context, builder, df_type, data_tup,
            index, parent, col_names)
        context.nrt.incref(builder, data_typ, data_tup)
        context.nrt.incref(builder, index_typ, index)
        context.nrt.incref(builder, colnames_index_typ, col_names)
        return dagq__wbb
    sig = signature(obzc__jfmz, data_typ, index_typ, colnames_index_typ)
    return sig, codegen


@intrinsic
def init_dataframe(typingctx, data_tup_typ, index_typ, col_names_typ=None):
    assert is_pd_index_type(index_typ) or isinstance(index_typ, MultiIndexType
        ), 'init_dataframe(): invalid index type'
    cnsg__sdwvq = len(data_tup_typ.types)
    if cnsg__sdwvq == 0:
        column_names = ()
    elif isinstance(col_names_typ, types.TypeRef):
        column_names = col_names_typ.instance_type.columns
    else:
        column_names = get_const_tup_vals(col_names_typ)
    if cnsg__sdwvq == 1 and isinstance(data_tup_typ.types[0], TableType):
        cnsg__sdwvq = len(data_tup_typ.types[0].arr_types)
    assert len(column_names
        ) == cnsg__sdwvq, 'init_dataframe(): number of column names does not match number of columns'
    is_table_format = False
    yiks__fnxa = data_tup_typ.types
    if cnsg__sdwvq != 0 and isinstance(data_tup_typ.types[0], TableType):
        yiks__fnxa = data_tup_typ.types[0].arr_types
        is_table_format = True
    obzc__jfmz = DataFrameType(yiks__fnxa, index_typ, column_names,
        is_table_format=is_table_format)

    def codegen(context, builder, signature, args):
        df_type = signature.return_type
        data_tup = args[0]
        index_val = args[1]
        parent = None
        if is_table_format:
            jfr__cqos = cgutils.create_struct_proxy(obzc__jfmz.table_type)(
                context, builder, builder.extract_value(data_tup, 0))
            parent = jfr__cqos.parent
        dagq__wbb = construct_dataframe(context, builder, df_type, data_tup,
            index_val, parent, None)
        context.nrt.incref(builder, data_tup_typ, data_tup)
        context.nrt.incref(builder, index_typ, index_val)
        return dagq__wbb
    sig = signature(obzc__jfmz, data_tup_typ, index_typ, col_names_typ)
    return sig, codegen


@intrinsic
def has_parent(typingctx, df=None):
    check_runtime_cols_unsupported(df, 'has_parent')

    def codegen(context, builder, sig, args):
        rzsq__styt = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        return cgutils.is_not_null(builder, rzsq__styt.parent)
    return signature(types.bool_, df), codegen


@intrinsic
def _column_needs_unboxing(typingctx, df_typ, i_typ=None):
    check_runtime_cols_unsupported(df_typ, '_column_needs_unboxing')
    assert isinstance(df_typ, DataFrameType) and is_overload_constant_int(i_typ
        )

    def codegen(context, builder, sig, args):
        myw__lvx = get_dataframe_payload(context, builder, df_typ, args[0])
        clbzz__svbgc = get_overload_const_int(i_typ)
        arr_typ = df_typ.data[clbzz__svbgc]
        if df_typ.is_table_format:
            jfr__cqos = cgutils.create_struct_proxy(df_typ.table_type)(context,
                builder, builder.extract_value(myw__lvx.data, 0))
            geq__aypmi = df_typ.table_type.type_to_blk[arr_typ]
            xey__qjhct = getattr(jfr__cqos, f'block_{geq__aypmi}')
            bfvq__qty = ListInstance(context, builder, types.List(arr_typ),
                xey__qjhct)
            axkvh__jqwji = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[clbzz__svbgc])
            hkarx__aycqp = bfvq__qty.getitem(axkvh__jqwji)
        else:
            hkarx__aycqp = builder.extract_value(myw__lvx.data, clbzz__svbgc)
        zimcx__gocnq = cgutils.alloca_once_value(builder, hkarx__aycqp)
        szqx__bxyjn = cgutils.alloca_once_value(builder, context.
            get_constant_null(arr_typ))
        return is_ll_eq(builder, zimcx__gocnq, szqx__bxyjn)
    return signature(types.bool_, df_typ, i_typ), codegen


def get_dataframe_payload(context, builder, df_type, value):
    ibwjf__kwo = cgutils.create_struct_proxy(df_type)(context, builder, value
        ).meminfo
    payload_type = DataFramePayloadType(df_type)
    payload = context.nrt.meminfo_data(builder, ibwjf__kwo)
    hcp__mtuan = context.get_value_type(payload_type).as_pointer()
    payload = builder.bitcast(payload, hcp__mtuan)
    return context.make_helper(builder, payload_type, ref=payload)


@intrinsic
def _get_dataframe_data(typingctx, df_typ=None):
    check_runtime_cols_unsupported(df_typ, '_get_dataframe_data')
    obzc__jfmz = types.Tuple(df_typ.data)
    if df_typ.is_table_format:
        obzc__jfmz = types.Tuple([TableType(df_typ.data)])
    sig = signature(obzc__jfmz, df_typ)

    def codegen(context, builder, signature, args):
        myw__lvx = get_dataframe_payload(context, builder, signature.args[0
            ], args[0])
        return impl_ret_borrowed(context, builder, signature.return_type,
            myw__lvx.data)
    return sig, codegen


@intrinsic
def get_dataframe_index(typingctx, df_typ=None):

    def codegen(context, builder, signature, args):
        myw__lvx = get_dataframe_payload(context, builder, signature.args[0
            ], args[0])
        return impl_ret_borrowed(context, builder, df_typ.index, myw__lvx.index
            )
    obzc__jfmz = df_typ.index
    sig = signature(obzc__jfmz, df_typ)
    return sig, codegen


def get_dataframe_data(df, i):
    return df[i]


@infer_global(get_dataframe_data)
class GetDataFrameDataInfer(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 2
        if not is_overload_constant_int(args[1]):
            raise_bodo_error(
                'Selecting a DataFrame column requires a constant column label'
                )
        df = args[0]
        check_runtime_cols_unsupported(df, 'get_dataframe_data')
        i = get_overload_const_int(args[1])
        qkt__hck = df.data[i]
        return qkt__hck(*args)


GetDataFrameDataInfer.prefer_literal = True


def get_dataframe_data_impl(df, i):
    if df.is_table_format:

        def _impl(df, i):
            if has_parent(df) and _column_needs_unboxing(df, i):
                bodo.hiframes.boxing.unbox_dataframe_column(df, i)
            return get_table_data(_get_dataframe_data(df)[0], i)
        return _impl

    def _impl(df, i):
        if has_parent(df) and _column_needs_unboxing(df, i):
            bodo.hiframes.boxing.unbox_dataframe_column(df, i)
        return _get_dataframe_data(df)[i]
    return _impl


@intrinsic
def get_dataframe_table(typingctx, df_typ=None):
    assert df_typ.is_table_format, 'get_dataframe_table() expects table format'

    def codegen(context, builder, signature, args):
        myw__lvx = get_dataframe_payload(context, builder, signature.args[0
            ], args[0])
        return impl_ret_borrowed(context, builder, df_typ.table_type,
            builder.extract_value(myw__lvx.data, 0))
    return df_typ.table_type(df_typ), codegen


@intrinsic
def get_dataframe_column_names(typingctx, df_typ=None):
    assert df_typ.has_runtime_cols, 'get_dataframe_column_names() expects columns to be determined at runtime'

    def codegen(context, builder, signature, args):
        myw__lvx = get_dataframe_payload(context, builder, signature.args[0
            ], args[0])
        return impl_ret_borrowed(context, builder, df_typ.
            runtime_colname_typ, myw__lvx.columns)
    return df_typ.runtime_colname_typ(df_typ), codegen


@lower_builtin(get_dataframe_data, DataFrameType, types.IntegerLiteral)
def lower_get_dataframe_data(context, builder, sig, args):
    impl = get_dataframe_data_impl(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


def alias_ext_dummy_func(lhs_name, args, alias_map, arg_aliases):
    assert len(args) >= 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['get_dataframe_data',
    'bodo.hiframes.pd_dataframe_ext'] = alias_ext_dummy_func
numba.core.ir_utils.alias_func_extensions['get_dataframe_index',
    'bodo.hiframes.pd_dataframe_ext'] = alias_ext_dummy_func
numba.core.ir_utils.alias_func_extensions['get_dataframe_table',
    'bodo.hiframes.pd_dataframe_ext'] = alias_ext_dummy_func


def alias_ext_init_dataframe(lhs_name, args, alias_map, arg_aliases):
    assert len(args) == 3
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)
    numba.core.ir_utils._add_alias(lhs_name, args[1].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['init_dataframe',
    'bodo.hiframes.pd_dataframe_ext'] = alias_ext_init_dataframe


def init_dataframe_equiv(self, scope, equiv_set, loc, args, kws):
    from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
    assert len(args) == 3 and not kws
    data_tup = args[0]
    index = args[1]
    snqlz__rqxx = self.typemap[data_tup.name]
    if any(is_tuple_like_type(xsj__yrh) for xsj__yrh in snqlz__rqxx.types):
        return None
    if equiv_set.has_shape(data_tup):
        jtg__bwqy = equiv_set.get_shape(data_tup)
        if len(jtg__bwqy) > 1:
            equiv_set.insert_equiv(*jtg__bwqy)
        if len(jtg__bwqy) > 0:
            yzcrv__ghhkt = self.typemap[index.name]
            if not isinstance(yzcrv__ghhkt, HeterogeneousIndexType
                ) and equiv_set.has_shape(index):
                equiv_set.insert_equiv(jtg__bwqy[0], index)
            return ArrayAnalysis.AnalyzeResult(shape=(jtg__bwqy[0], len(
                jtg__bwqy)), pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_dataframe_ext_init_dataframe
    ) = init_dataframe_equiv


def get_dataframe_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    wmin__yotlo = args[0]
    data_types = self.typemap[wmin__yotlo.name].data
    if any(is_tuple_like_type(xsj__yrh) for xsj__yrh in data_types):
        return None
    if equiv_set.has_shape(wmin__yotlo):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            wmin__yotlo)[0], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_data
    ) = get_dataframe_data_equiv


def get_dataframe_index_equiv(self, scope, equiv_set, loc, args, kws):
    from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
    assert len(args) == 1 and not kws
    wmin__yotlo = args[0]
    yzcrv__ghhkt = self.typemap[wmin__yotlo.name].index
    if isinstance(yzcrv__ghhkt, HeterogeneousIndexType):
        return None
    if equiv_set.has_shape(wmin__yotlo):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            wmin__yotlo)[0], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_index
    ) = get_dataframe_index_equiv


def get_dataframe_table_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    wmin__yotlo = args[0]
    if equiv_set.has_shape(wmin__yotlo):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            wmin__yotlo), pre=[])


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_table
    ) = get_dataframe_table_equiv


def get_dataframe_column_names_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    wmin__yotlo = args[0]
    if equiv_set.has_shape(wmin__yotlo):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            wmin__yotlo)[1], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_column_names
    ) = get_dataframe_column_names_equiv


@intrinsic
def set_dataframe_data(typingctx, df_typ, c_ind_typ, arr_typ=None):
    check_runtime_cols_unsupported(df_typ, 'set_dataframe_data')
    assert is_overload_constant_int(c_ind_typ)
    clbzz__svbgc = get_overload_const_int(c_ind_typ)
    if df_typ.data[clbzz__svbgc] != arr_typ:
        raise BodoError(
            'Changing dataframe column data type inplace is not supported in conditionals/loops or for dataframe arguments'
            )

    def codegen(context, builder, signature, args):
        zzfu__luu, bivm__wzvzy, reus__dfo = args
        myw__lvx = get_dataframe_payload(context, builder, df_typ, zzfu__luu)
        if df_typ.is_table_format:
            jfr__cqos = cgutils.create_struct_proxy(df_typ.table_type)(context,
                builder, builder.extract_value(myw__lvx.data, 0))
            geq__aypmi = df_typ.table_type.type_to_blk[arr_typ]
            xey__qjhct = getattr(jfr__cqos, f'block_{geq__aypmi}')
            bfvq__qty = ListInstance(context, builder, types.List(arr_typ),
                xey__qjhct)
            axkvh__jqwji = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[clbzz__svbgc])
            bfvq__qty.setitem(axkvh__jqwji, reus__dfo, True)
        else:
            hkarx__aycqp = builder.extract_value(myw__lvx.data, clbzz__svbgc)
            context.nrt.decref(builder, df_typ.data[clbzz__svbgc], hkarx__aycqp
                )
            myw__lvx.data = builder.insert_value(myw__lvx.data, reus__dfo,
                clbzz__svbgc)
            context.nrt.incref(builder, arr_typ, reus__dfo)
        rzsq__styt = cgutils.create_struct_proxy(df_typ)(context, builder,
            value=zzfu__luu)
        payload_type = DataFramePayloadType(df_typ)
        cyj__eovjb = context.nrt.meminfo_data(builder, rzsq__styt.meminfo)
        hcp__mtuan = context.get_value_type(payload_type).as_pointer()
        cyj__eovjb = builder.bitcast(cyj__eovjb, hcp__mtuan)
        builder.store(myw__lvx._getvalue(), cyj__eovjb)
        return impl_ret_borrowed(context, builder, df_typ, zzfu__luu)
    sig = signature(df_typ, df_typ, c_ind_typ, arr_typ)
    return sig, codegen


@intrinsic
def set_df_index(typingctx, df_t, index_t=None):
    check_runtime_cols_unsupported(df_t, 'set_df_index')

    def codegen(context, builder, signature, args):
        yyty__eeexs = args[0]
        index_val = args[1]
        df_typ = signature.args[0]
        ygrn__sfp = cgutils.create_struct_proxy(df_typ)(context, builder,
            value=yyty__eeexs)
        wylr__abalt = get_dataframe_payload(context, builder, df_typ,
            yyty__eeexs)
        rzsq__styt = construct_dataframe(context, builder, signature.
            return_type, wylr__abalt.data, index_val, ygrn__sfp.parent, None)
        context.nrt.incref(builder, index_t, index_val)
        context.nrt.incref(builder, types.Tuple(df_t.data), wylr__abalt.data)
        return rzsq__styt
    obzc__jfmz = DataFrameType(df_t.data, index_t, df_t.columns, df_t.dist,
        df_t.is_table_format)
    sig = signature(obzc__jfmz, df_t, index_t)
    return sig, codegen


@intrinsic
def set_df_column_with_reflect(typingctx, df_type, cname_type, arr_type=None):
    check_runtime_cols_unsupported(df_type, 'set_df_column_with_reflect')
    assert is_literal_type(cname_type), 'constant column name expected'
    col_name = get_literal_value(cname_type)
    cnsg__sdwvq = len(df_type.columns)
    fzly__rpum = cnsg__sdwvq
    uofj__scl = df_type.data
    column_names = df_type.columns
    index_typ = df_type.index
    gbkm__sbxc = col_name not in df_type.columns
    clbzz__svbgc = cnsg__sdwvq
    if gbkm__sbxc:
        uofj__scl += arr_type,
        column_names += col_name,
        fzly__rpum += 1
    else:
        clbzz__svbgc = df_type.columns.index(col_name)
        uofj__scl = tuple(arr_type if i == clbzz__svbgc else uofj__scl[i] for
            i in range(cnsg__sdwvq))

    def codegen(context, builder, signature, args):
        zzfu__luu, bivm__wzvzy, reus__dfo = args
        in_dataframe_payload = get_dataframe_payload(context, builder,
            df_type, zzfu__luu)
        smjwx__hpkd = cgutils.create_struct_proxy(df_type)(context, builder,
            value=zzfu__luu)
        if df_type.is_table_format:
            kpyvk__kgjho = df_type.table_type
            qfkus__ljcp = builder.extract_value(in_dataframe_payload.data, 0)
            ufva__ffsf = TableType(uofj__scl)
            xrv__sya = set_table_data_codegen(context, builder,
                kpyvk__kgjho, qfkus__ljcp, ufva__ffsf, arr_type, reus__dfo,
                clbzz__svbgc, gbkm__sbxc)
            data_tup = context.make_tuple(builder, types.Tuple([ufva__ffsf]
                ), [xrv__sya])
        else:
            yiks__fnxa = [(builder.extract_value(in_dataframe_payload.data,
                i) if i != clbzz__svbgc else reus__dfo) for i in range(
                cnsg__sdwvq)]
            if gbkm__sbxc:
                yiks__fnxa.append(reus__dfo)
            for wmin__yotlo, suhhd__nlef in zip(yiks__fnxa, uofj__scl):
                context.nrt.incref(builder, suhhd__nlef, wmin__yotlo)
            data_tup = context.make_tuple(builder, types.Tuple(uofj__scl),
                yiks__fnxa)
        index_val = in_dataframe_payload.index
        context.nrt.incref(builder, index_typ, index_val)
        fwxsj__jtmwn = construct_dataframe(context, builder, signature.
            return_type, data_tup, index_val, smjwx__hpkd.parent, None)
        if not gbkm__sbxc and arr_type == df_type.data[clbzz__svbgc]:
            decref_df_data(context, builder, in_dataframe_payload, df_type)
            payload_type = DataFramePayloadType(df_type)
            cyj__eovjb = context.nrt.meminfo_data(builder, smjwx__hpkd.meminfo)
            hcp__mtuan = context.get_value_type(payload_type).as_pointer()
            cyj__eovjb = builder.bitcast(cyj__eovjb, hcp__mtuan)
            mpxfb__nvsj = get_dataframe_payload(context, builder, df_type,
                fwxsj__jtmwn)
            builder.store(mpxfb__nvsj._getvalue(), cyj__eovjb)
            context.nrt.incref(builder, index_typ, index_val)
            if df_type.is_table_format:
                context.nrt.incref(builder, ufva__ffsf, builder.
                    extract_value(data_tup, 0))
            else:
                for wmin__yotlo, suhhd__nlef in zip(yiks__fnxa, uofj__scl):
                    context.nrt.incref(builder, suhhd__nlef, wmin__yotlo)
        has_parent = cgutils.is_not_null(builder, smjwx__hpkd.parent)
        with builder.if_then(has_parent):
            gqiiw__bdecn = context.get_python_api(builder)
            tao__xop = gqiiw__bdecn.gil_ensure()
            mlwdq__lugyg = context.get_env_manager(builder)
            context.nrt.incref(builder, arr_type, reus__dfo)
            ixz__sio = numba.core.pythonapi._BoxContext(context, builder,
                gqiiw__bdecn, mlwdq__lugyg)
            uujm__wzxu = ixz__sio.pyapi.from_native_value(arr_type,
                reus__dfo, ixz__sio.env_manager)
            if isinstance(col_name, str):
                xozq__qsb = context.insert_const_string(builder.module,
                    col_name)
                irnb__klfh = gqiiw__bdecn.string_from_string(xozq__qsb)
            else:
                assert isinstance(col_name, int)
                irnb__klfh = gqiiw__bdecn.long_from_longlong(context.
                    get_constant(types.intp, col_name))
            gqiiw__bdecn.object_setitem(smjwx__hpkd.parent, irnb__klfh,
                uujm__wzxu)
            gqiiw__bdecn.decref(uujm__wzxu)
            gqiiw__bdecn.decref(irnb__klfh)
            gqiiw__bdecn.gil_release(tao__xop)
        return fwxsj__jtmwn
    obzc__jfmz = DataFrameType(uofj__scl, index_typ, column_names, df_type.
        dist, df_type.is_table_format)
    sig = signature(obzc__jfmz, df_type, cname_type, arr_type)
    return sig, codegen


@lower_constant(DataFrameType)
def lower_constant_dataframe(context, builder, df_type, pyval):
    check_runtime_cols_unsupported(df_type, 'lowering a constant DataFrame')
    cnsg__sdwvq = len(pyval.columns)
    yiks__fnxa = tuple(pyval.iloc[:, i].values for i in range(cnsg__sdwvq))
    if df_type.is_table_format:
        jfr__cqos = context.get_constant_generic(builder, df_type.
            table_type, Table(yiks__fnxa))
        data_tup = lir.Constant.literal_struct([jfr__cqos])
    else:
        data_tup = lir.Constant.literal_struct([context.
            get_constant_generic(builder, df_type.data[i], nile__tgtn) for 
            i, nile__tgtn in enumerate(yiks__fnxa)])
    index_val = context.get_constant_generic(builder, df_type.index, pyval.
        index)
    hxezj__belzn = context.get_constant_null(types.pyobject)
    payload = lir.Constant.literal_struct([data_tup, index_val, hxezj__belzn])
    payload = cgutils.global_constant(builder, '.const.payload', payload
        ).bitcast(cgutils.voidptr_t)
    dryg__qfc = context.get_constant(types.int64, -1)
    ppp__bxu = context.get_constant_null(types.voidptr)
    ibwjf__kwo = lir.Constant.literal_struct([dryg__qfc, ppp__bxu, ppp__bxu,
        payload, dryg__qfc])
    ibwjf__kwo = cgutils.global_constant(builder, '.const.meminfo', ibwjf__kwo
        ).bitcast(cgutils.voidptr_t)
    return lir.Constant.literal_struct([ibwjf__kwo, hxezj__belzn])


@lower_cast(DataFrameType, DataFrameType)
def cast_df_to_df(context, builder, fromty, toty, val):
    if (fromty.data == toty.data and fromty.index == toty.index and fromty.
        columns == toty.columns and fromty.is_table_format == toty.
        is_table_format and fromty.dist != toty.dist and fromty.
        has_runtime_cols == toty.has_runtime_cols):
        return val
    if not fromty.has_runtime_cols and not toty.has_runtime_cols and len(fromty
        .data) == 0 and len(toty.columns):
        return _cast_empty_df(context, builder, toty)
    if len(fromty.data) != len(toty.data) or fromty.data != toty.data and any(
        context.typing_context.unify_pairs(fromty.data[i], toty.data[i]) is
        None for i in range(len(fromty.data))
        ) or fromty.has_runtime_cols != toty.has_runtime_cols:
        raise BodoError(f'Invalid dataframe cast from {fromty} to {toty}')
    in_dataframe_payload = get_dataframe_payload(context, builder, fromty, val)
    if isinstance(fromty.index, RangeIndexType) and isinstance(toty.index,
        NumericIndexType):
        tqy__mgy = context.cast(builder, in_dataframe_payload.index, fromty
            .index, toty.index)
    else:
        tqy__mgy = in_dataframe_payload.index
        context.nrt.incref(builder, fromty.index, tqy__mgy)
    if (fromty.is_table_format == toty.is_table_format and fromty.data ==
        toty.data):
        ikd__vmoed = in_dataframe_payload.data
        if fromty.is_table_format:
            context.nrt.incref(builder, types.Tuple([fromty.table_type]),
                ikd__vmoed)
        else:
            context.nrt.incref(builder, types.BaseTuple.from_types(fromty.
                data), ikd__vmoed)
    elif not fromty.is_table_format and toty.is_table_format:
        ikd__vmoed = _cast_df_data_to_table_format(context, builder, fromty,
            toty, val, in_dataframe_payload)
    elif fromty.is_table_format and not toty.is_table_format:
        ikd__vmoed = _cast_df_data_to_tuple_format(context, builder, fromty,
            toty, val, in_dataframe_payload)
    elif fromty.is_table_format and toty.is_table_format:
        ikd__vmoed = _cast_df_data_keep_table_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    else:
        ikd__vmoed = _cast_df_data_keep_tuple_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    return construct_dataframe(context, builder, toty, ikd__vmoed, tqy__mgy,
        in_dataframe_payload.parent, None)


def _cast_empty_df(context, builder, toty):
    ibk__qbfax = {}
    if isinstance(toty.index, RangeIndexType):
        index = 'bodo.hiframes.pd_index_ext.init_range_index(0, 0, 1, None)'
    else:
        qaxio__vfg = get_index_data_arr_types(toty.index)[0]
        txkbm__atpv = bodo.utils.transform.get_type_alloc_counts(qaxio__vfg
            ) - 1
        nzbh__klps = ', '.join('0' for bivm__wzvzy in range(txkbm__atpv))
        index = (
            'bodo.utils.conversion.index_from_array(bodo.utils.utils.alloc_type(0, index_arr_type, ({}{})))'
            .format(nzbh__klps, ', ' if txkbm__atpv == 1 else ''))
        ibk__qbfax['index_arr_type'] = qaxio__vfg
    lfn__fdkiz = []
    for i, arr_typ in enumerate(toty.data):
        txkbm__atpv = bodo.utils.transform.get_type_alloc_counts(arr_typ) - 1
        nzbh__klps = ', '.join('0' for bivm__wzvzy in range(txkbm__atpv))
        ake__axa = 'bodo.utils.utils.alloc_type(0, arr_type{}, ({}{}))'.format(
            i, nzbh__klps, ', ' if txkbm__atpv == 1 else '')
        lfn__fdkiz.append(ake__axa)
        ibk__qbfax[f'arr_type{i}'] = arr_typ
    lfn__fdkiz = ', '.join(lfn__fdkiz)
    tzeyj__jjmo = 'def impl():\n'
    tcsru__aad = bodo.hiframes.dataframe_impl._gen_init_df(tzeyj__jjmo,
        toty.columns, lfn__fdkiz, index, ibk__qbfax)
    df = context.compile_internal(builder, tcsru__aad, toty(), [])
    return df


def _cast_df_data_to_table_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting traditional DataFrame to table format')
    wvk__tjtu = toty.table_type
    jfr__cqos = cgutils.create_struct_proxy(wvk__tjtu)(context, builder)
    jfr__cqos.parent = in_dataframe_payload.parent
    for xsj__yrh, geq__aypmi in wvk__tjtu.type_to_blk.items():
        bog__fktki = context.get_constant(types.int64, len(wvk__tjtu.
            block_to_arr_ind[geq__aypmi]))
        bivm__wzvzy, yujt__sydf = ListInstance.allocate_ex(context, builder,
            types.List(xsj__yrh), bog__fktki)
        yujt__sydf.size = bog__fktki
        setattr(jfr__cqos, f'block_{geq__aypmi}', yujt__sydf.value)
    for i, xsj__yrh in enumerate(fromty.data):
        jsjkx__isrtr = toty.data[i]
        if xsj__yrh != jsjkx__isrtr:
            etva__khxc = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*etva__khxc)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        hkarx__aycqp = builder.extract_value(in_dataframe_payload.data, i)
        if xsj__yrh != jsjkx__isrtr:
            zwx__cyupq = context.cast(builder, hkarx__aycqp, xsj__yrh,
                jsjkx__isrtr)
            hlzvw__umrqt = False
        else:
            zwx__cyupq = hkarx__aycqp
            hlzvw__umrqt = True
        geq__aypmi = wvk__tjtu.type_to_blk[xsj__yrh]
        xey__qjhct = getattr(jfr__cqos, f'block_{geq__aypmi}')
        bfvq__qty = ListInstance(context, builder, types.List(xsj__yrh),
            xey__qjhct)
        axkvh__jqwji = context.get_constant(types.int64, wvk__tjtu.
            block_offsets[i])
        bfvq__qty.setitem(axkvh__jqwji, zwx__cyupq, hlzvw__umrqt)
    data_tup = context.make_tuple(builder, types.Tuple([wvk__tjtu]), [
        jfr__cqos._getvalue()])
    return data_tup


def _cast_df_data_keep_tuple_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting traditional DataFrame columns')
    yiks__fnxa = []
    for i in range(len(fromty.data)):
        if fromty.data[i] != toty.data[i]:
            etva__khxc = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*etva__khxc)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
            hkarx__aycqp = builder.extract_value(in_dataframe_payload.data, i)
            zwx__cyupq = context.cast(builder, hkarx__aycqp, fromty.data[i],
                toty.data[i])
            hlzvw__umrqt = False
        else:
            zwx__cyupq = builder.extract_value(in_dataframe_payload.data, i)
            hlzvw__umrqt = True
        if hlzvw__umrqt:
            context.nrt.incref(builder, toty.data[i], zwx__cyupq)
        yiks__fnxa.append(zwx__cyupq)
    data_tup = context.make_tuple(builder, types.Tuple(toty.data), yiks__fnxa)
    return data_tup


def _cast_df_data_keep_table_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting table format DataFrame columns')
    kpyvk__kgjho = fromty.table_type
    qfkus__ljcp = cgutils.create_struct_proxy(kpyvk__kgjho)(context,
        builder, builder.extract_value(in_dataframe_payload.data, 0))
    ufva__ffsf = toty.table_type
    xrv__sya = cgutils.create_struct_proxy(ufva__ffsf)(context, builder)
    xrv__sya.parent = in_dataframe_payload.parent
    for xsj__yrh, geq__aypmi in ufva__ffsf.type_to_blk.items():
        bog__fktki = context.get_constant(types.int64, len(ufva__ffsf.
            block_to_arr_ind[geq__aypmi]))
        bivm__wzvzy, yujt__sydf = ListInstance.allocate_ex(context, builder,
            types.List(xsj__yrh), bog__fktki)
        yujt__sydf.size = bog__fktki
        setattr(xrv__sya, f'block_{geq__aypmi}', yujt__sydf.value)
    for i in range(len(fromty.data)):
        htyy__zgmvk = fromty.data[i]
        jsjkx__isrtr = toty.data[i]
        if htyy__zgmvk != jsjkx__isrtr:
            etva__khxc = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*etva__khxc)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        ztdbe__tyqz = kpyvk__kgjho.type_to_blk[htyy__zgmvk]
        gjsl__nja = getattr(qfkus__ljcp, f'block_{ztdbe__tyqz}')
        aay__bmgft = ListInstance(context, builder, types.List(htyy__zgmvk),
            gjsl__nja)
        yphz__pwk = context.get_constant(types.int64, kpyvk__kgjho.
            block_offsets[i])
        hkarx__aycqp = aay__bmgft.getitem(yphz__pwk)
        if htyy__zgmvk != jsjkx__isrtr:
            zwx__cyupq = context.cast(builder, hkarx__aycqp, htyy__zgmvk,
                jsjkx__isrtr)
            hlzvw__umrqt = False
        else:
            zwx__cyupq = hkarx__aycqp
            hlzvw__umrqt = True
        ffjfs__zhv = ufva__ffsf.type_to_blk[xsj__yrh]
        yujt__sydf = getattr(xrv__sya, f'block_{ffjfs__zhv}')
        ytcj__bdbhq = ListInstance(context, builder, types.List(
            jsjkx__isrtr), yujt__sydf)
        ilt__qeus = context.get_constant(types.int64, ufva__ffsf.
            block_offsets[i])
        ytcj__bdbhq.setitem(ilt__qeus, zwx__cyupq, hlzvw__umrqt)
    data_tup = context.make_tuple(builder, types.Tuple([ufva__ffsf]), [
        xrv__sya._getvalue()])
    return data_tup


def _cast_df_data_to_tuple_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(fromty,
        'casting table format to traditional DataFrame')
    wvk__tjtu = fromty.table_type
    jfr__cqos = cgutils.create_struct_proxy(wvk__tjtu)(context, builder,
        builder.extract_value(in_dataframe_payload.data, 0))
    yiks__fnxa = []
    for i, xsj__yrh in enumerate(toty.data):
        htyy__zgmvk = fromty.data[i]
        if xsj__yrh != htyy__zgmvk:
            etva__khxc = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*etva__khxc)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        geq__aypmi = wvk__tjtu.type_to_blk[xsj__yrh]
        xey__qjhct = getattr(jfr__cqos, f'block_{geq__aypmi}')
        bfvq__qty = ListInstance(context, builder, types.List(xsj__yrh),
            xey__qjhct)
        axkvh__jqwji = context.get_constant(types.int64, wvk__tjtu.
            block_offsets[i])
        hkarx__aycqp = bfvq__qty.getitem(axkvh__jqwji)
        if xsj__yrh != htyy__zgmvk:
            zwx__cyupq = context.cast(builder, hkarx__aycqp, htyy__zgmvk,
                xsj__yrh)
            hlzvw__umrqt = False
        else:
            zwx__cyupq = hkarx__aycqp
            hlzvw__umrqt = True
        if hlzvw__umrqt:
            context.nrt.incref(builder, xsj__yrh, zwx__cyupq)
        yiks__fnxa.append(zwx__cyupq)
    data_tup = context.make_tuple(builder, types.Tuple(toty.data), yiks__fnxa)
    return data_tup


@overload(pd.DataFrame, inline='always', no_unliteral=True)
def pd_dataframe_overload(data=None, index=None, columns=None, dtype=None,
    copy=False):
    if not is_overload_constant_bool(copy):
        raise BodoError(
            "pd.DataFrame(): 'copy' argument should be a constant boolean")
    copy = get_overload_const(copy)
    hjysd__cnqc, lfn__fdkiz, index_arg = _get_df_args(data, index, columns,
        dtype, copy)
    lqpw__umf = gen_const_tup(hjysd__cnqc)
    tzeyj__jjmo = (
        'def _init_df(data=None, index=None, columns=None, dtype=None, copy=False):\n'
        )
    tzeyj__jjmo += (
        '  return bodo.hiframes.pd_dataframe_ext.init_dataframe({}, {}, {})\n'
        .format(lfn__fdkiz, index_arg, lqpw__umf))
    gcyu__prty = {}
    exec(tzeyj__jjmo, {'bodo': bodo, 'np': np}, gcyu__prty)
    dcb__daya = gcyu__prty['_init_df']
    return dcb__daya


@intrinsic
def _tuple_to_table_format_decoded(typingctx, df_typ):
    assert not df_typ.is_table_format, '_tuple_to_table_format requires a tuple format input'

    def codegen(context, builder, signature, args):
        return context.cast(builder, args[0], signature.args[0], signature.
            return_type)
    obzc__jfmz = DataFrameType(to_str_arr_if_dict_array(df_typ.data),
        df_typ.index, df_typ.columns, dist=df_typ.dist, is_table_format=True)
    sig = signature(obzc__jfmz, df_typ)
    return sig, codegen


@intrinsic
def _table_to_tuple_format_decoded(typingctx, df_typ):
    assert df_typ.is_table_format, '_tuple_to_table_format requires a table format input'

    def codegen(context, builder, signature, args):
        return context.cast(builder, args[0], signature.args[0], signature.
            return_type)
    obzc__jfmz = DataFrameType(to_str_arr_if_dict_array(df_typ.data),
        df_typ.index, df_typ.columns, dist=df_typ.dist, is_table_format=False)
    sig = signature(obzc__jfmz, df_typ)
    return sig, codegen


def _get_df_args(data, index, columns, dtype, copy):
    vzqx__qxv = ''
    if not is_overload_none(dtype):
        vzqx__qxv = '.astype(dtype)'
    index_is_none = is_overload_none(index)
    index_arg = 'bodo.utils.conversion.convert_to_index(index)'
    if isinstance(data, types.BaseTuple):
        if not data.types[0] == types.StringLiteral('__bodo_tup'):
            raise BodoError('pd.DataFrame tuple input data not supported yet')
        assert len(data.types) % 2 == 1, 'invalid const dict tuple structure'
        cnsg__sdwvq = (len(data.types) - 1) // 2
        otzas__hfzub = [xsj__yrh.literal_value for xsj__yrh in data.types[1
            :cnsg__sdwvq + 1]]
        data_val_types = dict(zip(otzas__hfzub, data.types[cnsg__sdwvq + 1:]))
        yiks__fnxa = ['data[{}]'.format(i) for i in range(cnsg__sdwvq + 1, 
            2 * cnsg__sdwvq + 1)]
        data_dict = dict(zip(otzas__hfzub, yiks__fnxa))
        if is_overload_none(index):
            for i, xsj__yrh in enumerate(data.types[cnsg__sdwvq + 1:]):
                if isinstance(xsj__yrh, SeriesType):
                    index_arg = (
                        'bodo.hiframes.pd_series_ext.get_series_index(data[{}])'
                        .format(cnsg__sdwvq + 1 + i))
                    index_is_none = False
                    break
    elif is_overload_none(data):
        data_dict = {}
        data_val_types = {}
    else:
        if not (isinstance(data, types.Array) and data.ndim == 2):
            raise BodoError(
                'pd.DataFrame() only supports constant dictionary and array input'
                )
        if is_overload_none(columns):
            raise BodoError(
                "pd.DataFrame() 'columns' argument is required when an array is passed as data"
                )
        jpil__ssup = '.copy()' if copy else ''
        eraxb__jphq = get_overload_const_list(columns)
        cnsg__sdwvq = len(eraxb__jphq)
        data_val_types = {ixz__sio: data.copy(ndim=1) for ixz__sio in
            eraxb__jphq}
        yiks__fnxa = ['data[:,{}]{}'.format(i, jpil__ssup) for i in range(
            cnsg__sdwvq)]
        data_dict = dict(zip(eraxb__jphq, yiks__fnxa))
    if is_overload_none(columns):
        col_names = data_dict.keys()
    else:
        col_names = get_overload_const_list(columns)
    df_len = _get_df_len_from_info(data_dict, data_val_types, col_names,
        index_is_none, index_arg)
    _fill_null_arrays(data_dict, col_names, df_len, dtype)
    if index_is_none:
        if is_overload_none(data):
            index_arg = (
                'bodo.hiframes.pd_index_ext.init_binary_str_index(bodo.libs.str_arr_ext.pre_alloc_string_array(0, 0))'
                )
        else:
            index_arg = (
                'bodo.hiframes.pd_index_ext.init_range_index(0, {}, 1, None)'
                .format(df_len))
    lfn__fdkiz = '({},)'.format(', '.join(
        'bodo.utils.conversion.coerce_to_array({}, True, scalar_to_arr_len={}){}'
        .format(data_dict[ixz__sio], df_len, vzqx__qxv) for ixz__sio in
        col_names))
    if len(col_names) == 0:
        lfn__fdkiz = '()'
    return col_names, lfn__fdkiz, index_arg


def _get_df_len_from_info(data_dict, data_val_types, col_names,
    index_is_none, index_arg):
    df_len = '0'
    for ixz__sio in col_names:
        if ixz__sio in data_dict and is_iterable_type(data_val_types[ixz__sio]
            ):
            df_len = 'len({})'.format(data_dict[ixz__sio])
            break
    if df_len == '0' and not index_is_none:
        df_len = f'len({index_arg})'
    return df_len


def _fill_null_arrays(data_dict, col_names, df_len, dtype):
    if all(ixz__sio in data_dict for ixz__sio in col_names):
        return
    if is_overload_none(dtype):
        dtype = 'bodo.string_array_type'
    else:
        dtype = 'bodo.utils.conversion.array_type_from_dtype(dtype)'
    nlr__fbhox = 'bodo.libs.array_kernels.gen_na_array({}, {})'.format(df_len,
        dtype)
    for ixz__sio in col_names:
        if ixz__sio not in data_dict:
            data_dict[ixz__sio] = nlr__fbhox


@infer_global(len)
class LenTemplate(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 1
        if isinstance(args[0], (DataFrameType, bodo.TableType)):
            return types.int64(*args)


@lower_builtin(len, DataFrameType)
def table_len_lower(context, builder, sig, args):
    impl = df_len_overload(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


def df_len_overload(df):
    if not isinstance(df, DataFrameType):
        return
    if df.has_runtime_cols:

        def impl(df):
            if is_null_pointer(df._meminfo):
                return 0
            xsj__yrh = bodo.hiframes.pd_dataframe_ext.get_dataframe_table(df)
            return len(xsj__yrh)
        return impl
    if len(df.columns) == 0:

        def impl(df):
            if is_null_pointer(df._meminfo):
                return 0
            return len(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df))
        return impl

    def impl(df):
        if is_null_pointer(df._meminfo):
            return 0
        return len(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, 0))
    return impl


@infer_global(operator.getitem)
class GetItemTuple(AbstractTemplate):
    key = operator.getitem

    def generic(self, args, kws):
        tup, idx = args
        if not isinstance(tup, types.BaseTuple) or not isinstance(idx,
            types.IntegerLiteral):
            return
        xwngy__dclqn = idx.literal_value
        if isinstance(xwngy__dclqn, int):
            qkt__hck = tup.types[xwngy__dclqn]
        elif isinstance(xwngy__dclqn, slice):
            qkt__hck = types.BaseTuple.from_types(tup.types[xwngy__dclqn])
        return signature(qkt__hck, *args)


GetItemTuple.prefer_literal = True


@lower_builtin(operator.getitem, types.BaseTuple, types.IntegerLiteral)
@lower_builtin(operator.getitem, types.BaseTuple, types.SliceLiteral)
def getitem_tuple_lower(context, builder, sig, args):
    iey__qri, idx = sig.args
    idx = idx.literal_value
    tup, bivm__wzvzy = args
    if isinstance(idx, int):
        if idx < 0:
            idx += len(iey__qri)
        if not 0 <= idx < len(iey__qri):
            raise IndexError('cannot index at %d in %s' % (idx, iey__qri))
        oqrm__dqocw = builder.extract_value(tup, idx)
    elif isinstance(idx, slice):
        hqx__zcf = cgutils.unpack_tuple(builder, tup)[idx]
        oqrm__dqocw = context.make_tuple(builder, sig.return_type, hqx__zcf)
    else:
        raise NotImplementedError('unexpected index %r for %s' % (idx, sig.
            args[0]))
    return impl_ret_borrowed(context, builder, sig.return_type, oqrm__dqocw)


def join_dummy(left_df, right_df, left_on, right_on, how, suffix_x,
    suffix_y, is_join, indicator, _bodo_na_equal, gen_cond):
    return left_df


@infer_global(join_dummy)
class JoinTyper(AbstractTemplate):

    def generic(self, args, kws):
        from bodo.hiframes.pd_dataframe_ext import DataFrameType
        from bodo.utils.typing import is_overload_str
        assert not kws
        (left_df, right_df, left_on, right_on, vcakg__xio, suffix_x,
            suffix_y, is_join, indicator, _bodo_na_equal, tey__ptgtx) = args
        left_on = get_overload_const_list(left_on)
        right_on = get_overload_const_list(right_on)
        rtcf__ckj = set(left_on) & set(right_on)
        bzjr__qncts = set(left_df.columns) & set(right_df.columns)
        ssb__tsjm = bzjr__qncts - rtcf__ckj
        pjrwt__maj = '$_bodo_index_' in left_on
        zcxzc__knv = '$_bodo_index_' in right_on
        how = get_overload_const_str(vcakg__xio)
        vigww__kgsef = how in {'left', 'outer'}
        derao__qzvbk = how in {'right', 'outer'}
        columns = []
        data = []
        if pjrwt__maj:
            fuozs__kxtos = bodo.utils.typing.get_index_data_arr_types(left_df
                .index)[0]
        else:
            fuozs__kxtos = left_df.data[left_df.columns.index(left_on[0])]
        if zcxzc__knv:
            urri__klpz = bodo.utils.typing.get_index_data_arr_types(right_df
                .index)[0]
        else:
            urri__klpz = right_df.data[right_df.columns.index(right_on[0])]
        if pjrwt__maj and not zcxzc__knv and not is_join.literal_value:
            waxx__ispv = right_on[0]
            if waxx__ispv in left_df.columns:
                columns.append(waxx__ispv)
                if (urri__klpz == bodo.dict_str_arr_type and fuozs__kxtos ==
                    bodo.string_array_type):
                    jegz__gsqa = bodo.string_array_type
                else:
                    jegz__gsqa = urri__klpz
                data.append(jegz__gsqa)
        if zcxzc__knv and not pjrwt__maj and not is_join.literal_value:
            woyr__ancl = left_on[0]
            if woyr__ancl in right_df.columns:
                columns.append(woyr__ancl)
                if (fuozs__kxtos == bodo.dict_str_arr_type and urri__klpz ==
                    bodo.string_array_type):
                    jegz__gsqa = bodo.string_array_type
                else:
                    jegz__gsqa = fuozs__kxtos
                data.append(jegz__gsqa)
        for htyy__zgmvk, tda__xwke in zip(left_df.data, left_df.columns):
            columns.append(str(tda__xwke) + suffix_x.literal_value if 
                tda__xwke in ssb__tsjm else tda__xwke)
            if tda__xwke in rtcf__ckj:
                if htyy__zgmvk == bodo.dict_str_arr_type:
                    htyy__zgmvk = right_df.data[right_df.columns.index(
                        tda__xwke)]
                data.append(htyy__zgmvk)
            else:
                if (htyy__zgmvk == bodo.dict_str_arr_type and tda__xwke in
                    left_on):
                    if zcxzc__knv:
                        htyy__zgmvk = urri__klpz
                    else:
                        umnq__eao = left_on.index(tda__xwke)
                        wgm__zfri = right_on[umnq__eao]
                        htyy__zgmvk = right_df.data[right_df.columns.index(
                            wgm__zfri)]
                if derao__qzvbk:
                    htyy__zgmvk = to_nullable_type(htyy__zgmvk)
                data.append(htyy__zgmvk)
        for htyy__zgmvk, tda__xwke in zip(right_df.data, right_df.columns):
            if tda__xwke not in rtcf__ckj:
                columns.append(str(tda__xwke) + suffix_y.literal_value if 
                    tda__xwke in ssb__tsjm else tda__xwke)
                if (htyy__zgmvk == bodo.dict_str_arr_type and tda__xwke in
                    right_on):
                    if pjrwt__maj:
                        htyy__zgmvk = fuozs__kxtos
                    else:
                        umnq__eao = right_on.index(tda__xwke)
                        emv__zyn = left_on[umnq__eao]
                        htyy__zgmvk = left_df.data[left_df.columns.index(
                            emv__zyn)]
                if vigww__kgsef:
                    htyy__zgmvk = to_nullable_type(htyy__zgmvk)
                data.append(htyy__zgmvk)
        ijxhp__ezi = get_overload_const_bool(indicator)
        if ijxhp__ezi:
            columns.append('_merge')
            data.append(bodo.CategoricalArrayType(bodo.PDCategoricalDtype((
                'left_only', 'right_only', 'both'), bodo.string_type, False)))
        index_typ = RangeIndexType(types.none)
        if pjrwt__maj and zcxzc__knv and not is_overload_str(how, 'asof'):
            index_typ = left_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        elif pjrwt__maj and not zcxzc__knv:
            index_typ = right_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        elif zcxzc__knv and not pjrwt__maj:
            index_typ = left_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        ojye__rilu = DataFrameType(tuple(data), index_typ, tuple(columns))
        return signature(ojye__rilu, *args)


JoinTyper._no_unliteral = True


@lower_builtin(join_dummy, types.VarArg(types.Any))
def lower_join_dummy(context, builder, sig, args):
    rzsq__styt = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return rzsq__styt._getvalue()


@overload(pd.concat, inline='always', no_unliteral=True)
def concat_overload(objs, axis=0, join='outer', join_axes=None,
    ignore_index=False, keys=None, levels=None, names=None,
    verify_integrity=False, sort=None, copy=True):
    if not is_overload_constant_int(axis):
        raise BodoError("pd.concat(): 'axis' should be a constant integer")
    if not is_overload_constant_bool(ignore_index):
        raise BodoError(
            "pd.concat(): 'ignore_index' should be a constant boolean")
    axis = get_overload_const_int(axis)
    ignore_index = is_overload_true(ignore_index)
    wnn__mqqx = dict(join=join, join_axes=join_axes, keys=keys, levels=
        levels, names=names, verify_integrity=verify_integrity, sort=sort,
        copy=copy)
    yuzp__dbgwm = dict(join='outer', join_axes=None, keys=None, levels=None,
        names=None, verify_integrity=False, sort=None, copy=True)
    check_unsupported_args('pandas.concat', wnn__mqqx, yuzp__dbgwm,
        package_name='pandas', module_name='General')
    tzeyj__jjmo = """def impl(objs, axis=0, join='outer', join_axes=None, ignore_index=False, keys=None, levels=None, names=None, verify_integrity=False, sort=None, copy=True):
"""
    if axis == 1:
        if not isinstance(objs, types.BaseTuple):
            raise_bodo_error(
                'Only tuple argument for pd.concat(axis=1) expected')
        index = (
            'bodo.hiframes.pd_index_ext.init_range_index(0, len(objs[0]), 1, None)'
            )
        sgd__qkfln = 0
        lfn__fdkiz = []
        names = []
        for i, dwn__pwtiv in enumerate(objs.types):
            assert isinstance(dwn__pwtiv, (SeriesType, DataFrameType))
            check_runtime_cols_unsupported(dwn__pwtiv, 'pd.concat()')
            if isinstance(dwn__pwtiv, SeriesType):
                names.append(str(sgd__qkfln))
                sgd__qkfln += 1
                lfn__fdkiz.append(
                    'bodo.hiframes.pd_series_ext.get_series_data(objs[{}])'
                    .format(i))
            else:
                names.extend(dwn__pwtiv.columns)
                for bfof__stevo in range(len(dwn__pwtiv.data)):
                    lfn__fdkiz.append(
                        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(objs[{}], {})'
                        .format(i, bfof__stevo))
        return bodo.hiframes.dataframe_impl._gen_init_df(tzeyj__jjmo, names,
            ', '.join(lfn__fdkiz), index)
    if axis != 0:
        raise_bodo_error('pd.concat(): axis must be 0 or 1')
    if isinstance(objs, types.BaseTuple) and isinstance(objs.types[0],
        DataFrameType):
        assert all(isinstance(xsj__yrh, DataFrameType) for xsj__yrh in objs
            .types)
        zyqz__pxxc = []
        for df in objs.types:
            check_runtime_cols_unsupported(df, 'pd.concat()')
            zyqz__pxxc.extend(df.columns)
        zyqz__pxxc = list(dict.fromkeys(zyqz__pxxc).keys())
        bcc__lrfrw = {}
        for sgd__qkfln, ixz__sio in enumerate(zyqz__pxxc):
            for df in objs.types:
                if ixz__sio in df.columns:
                    bcc__lrfrw['arr_typ{}'.format(sgd__qkfln)] = df.data[df
                        .columns.index(ixz__sio)]
                    break
        assert len(bcc__lrfrw) == len(zyqz__pxxc)
        jgo__oxi = []
        for sgd__qkfln, ixz__sio in enumerate(zyqz__pxxc):
            args = []
            for i, df in enumerate(objs.types):
                if ixz__sio in df.columns:
                    clbzz__svbgc = df.columns.index(ixz__sio)
                    args.append(
                        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(objs[{}], {})'
                        .format(i, clbzz__svbgc))
                else:
                    args.append(
                        'bodo.libs.array_kernels.gen_na_array(len(objs[{}]), arr_typ{})'
                        .format(i, sgd__qkfln))
            tzeyj__jjmo += ('  A{} = bodo.libs.array_kernels.concat(({},))\n'
                .format(sgd__qkfln, ', '.join(args)))
        if ignore_index:
            index = (
                'bodo.hiframes.pd_index_ext.init_range_index(0, len(A0), 1, None)'
                )
        else:
            index = (
                """bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(({},)))
"""
                .format(', '.join(
                'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(objs[{}]))'
                .format(i) for i in range(len(objs.types)) if len(objs[i].
                columns) > 0)))
        return bodo.hiframes.dataframe_impl._gen_init_df(tzeyj__jjmo,
            zyqz__pxxc, ', '.join('A{}'.format(i) for i in range(len(
            zyqz__pxxc))), index, bcc__lrfrw)
    if isinstance(objs, types.BaseTuple) and isinstance(objs.types[0],
        SeriesType):
        assert all(isinstance(xsj__yrh, SeriesType) for xsj__yrh in objs.types)
        tzeyj__jjmo += ('  out_arr = bodo.libs.array_kernels.concat(({},))\n'
            .format(', '.join(
            'bodo.hiframes.pd_series_ext.get_series_data(objs[{}])'.format(
            i) for i in range(len(objs.types)))))
        if ignore_index:
            tzeyj__jjmo += """  index = bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr), 1, None)
"""
        else:
            tzeyj__jjmo += (
                """  index = bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(({},)))
"""
                .format(', '.join(
                'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(objs[{}]))'
                .format(i) for i in range(len(objs.types)))))
        tzeyj__jjmo += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index)\n'
            )
        gcyu__prty = {}
        exec(tzeyj__jjmo, {'bodo': bodo, 'np': np, 'numba': numba}, gcyu__prty)
        return gcyu__prty['impl']
    if isinstance(objs, types.List) and isinstance(objs.dtype, DataFrameType):
        check_runtime_cols_unsupported(objs.dtype, 'pd.concat()')
        df_type = objs.dtype
        for sgd__qkfln, ixz__sio in enumerate(df_type.columns):
            tzeyj__jjmo += '  arrs{} = []\n'.format(sgd__qkfln)
            tzeyj__jjmo += '  for i in range(len(objs)):\n'
            tzeyj__jjmo += '    df = objs[i]\n'
            tzeyj__jjmo += (
                """    arrs{0}.append(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0}))
"""
                .format(sgd__qkfln))
            tzeyj__jjmo += (
                '  out_arr{0} = bodo.libs.array_kernels.concat(arrs{0})\n'.
                format(sgd__qkfln))
        if ignore_index:
            index = (
                'bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr0), 1, None)'
                )
        else:
            tzeyj__jjmo += '  arrs_index = []\n'
            tzeyj__jjmo += '  for i in range(len(objs)):\n'
            tzeyj__jjmo += '    df = objs[i]\n'
            tzeyj__jjmo += """    arrs_index.append(bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)))
"""
            if objs.dtype.index.name_typ == types.none:
                name = None
            else:
                name = objs.dtype.index.name_typ.literal_value
            index = f"""bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(arrs_index), {name!r})
"""
        return bodo.hiframes.dataframe_impl._gen_init_df(tzeyj__jjmo,
            df_type.columns, ', '.join('out_arr{}'.format(i) for i in range
            (len(df_type.columns))), index)
    if isinstance(objs, types.List) and isinstance(objs.dtype, SeriesType):
        tzeyj__jjmo += '  arrs = []\n'
        tzeyj__jjmo += '  for i in range(len(objs)):\n'
        tzeyj__jjmo += (
            '    arrs.append(bodo.hiframes.pd_series_ext.get_series_data(objs[i]))\n'
            )
        tzeyj__jjmo += '  out_arr = bodo.libs.array_kernels.concat(arrs)\n'
        if ignore_index:
            tzeyj__jjmo += """  index = bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr), 1, None)
"""
        else:
            tzeyj__jjmo += '  arrs_index = []\n'
            tzeyj__jjmo += '  for i in range(len(objs)):\n'
            tzeyj__jjmo += '    S = objs[i]\n'
            tzeyj__jjmo += """    arrs_index.append(bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(S)))
"""
            tzeyj__jjmo += """  index = bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(arrs_index))
"""
        tzeyj__jjmo += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index)\n'
            )
        gcyu__prty = {}
        exec(tzeyj__jjmo, {'bodo': bodo, 'np': np, 'numba': numba}, gcyu__prty)
        return gcyu__prty['impl']
    raise BodoError('pd.concat(): input type {} not supported yet'.format(objs)
        )


def sort_values_dummy(df, by, ascending, inplace, na_position):
    return df.sort_values(by, ascending=ascending, inplace=inplace,
        na_position=na_position)


@infer_global(sort_values_dummy)
class SortDummyTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        df, by, ascending, inplace, na_position = args
        index = df.index
        if isinstance(index, bodo.hiframes.pd_index_ext.RangeIndexType):
            index = bodo.hiframes.pd_index_ext.NumericIndexType(types.int64)
        obzc__jfmz = df.copy(index=index, is_table_format=False)
        return signature(obzc__jfmz, *args)


SortDummyTyper._no_unliteral = True


@lower_builtin(sort_values_dummy, types.VarArg(types.Any))
def lower_sort_values_dummy(context, builder, sig, args):
    if sig.return_type == types.none:
        return
    fhm__xyj = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return fhm__xyj._getvalue()


@overload_method(DataFrameType, 'itertuples', inline='always', no_unliteral
    =True)
def itertuples_overload(df, index=True, name='Pandas'):
    check_runtime_cols_unsupported(df, 'DataFrame.itertuples()')
    wnn__mqqx = dict(index=index, name=name)
    yuzp__dbgwm = dict(index=True, name='Pandas')
    check_unsupported_args('DataFrame.itertuples', wnn__mqqx, yuzp__dbgwm,
        package_name='pandas', module_name='DataFrame')

    def _impl(df, index=True, name='Pandas'):
        return bodo.hiframes.pd_dataframe_ext.itertuples_dummy(df)
    return _impl


def itertuples_dummy(df):
    return df


@infer_global(itertuples_dummy)
class ItertuplesDummyTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        df, = args
        assert 'Index' not in df.columns
        columns = ('Index',) + df.columns
        bcc__lrfrw = (types.Array(types.int64, 1, 'C'),) + df.data
        bio__jgsfw = bodo.hiframes.dataframe_impl.DataFrameTupleIterator(
            columns, bcc__lrfrw)
        return signature(bio__jgsfw, *args)


@lower_builtin(itertuples_dummy, types.VarArg(types.Any))
def lower_itertuples_dummy(context, builder, sig, args):
    fhm__xyj = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return fhm__xyj._getvalue()


def query_dummy(df, expr):
    return df.eval(expr)


@infer_global(query_dummy)
class QueryDummyTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        return signature(SeriesType(types.bool_, index=RangeIndexType(types
            .none)), *args)


@lower_builtin(query_dummy, types.VarArg(types.Any))
def lower_query_dummy(context, builder, sig, args):
    fhm__xyj = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return fhm__xyj._getvalue()


def val_isin_dummy(S, vals):
    return S in vals


def val_notin_dummy(S, vals):
    return S not in vals


@infer_global(val_isin_dummy)
@infer_global(val_notin_dummy)
class ValIsinTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        return signature(SeriesType(types.bool_, index=args[0].index), *args)


@lower_builtin(val_isin_dummy, types.VarArg(types.Any))
@lower_builtin(val_notin_dummy, types.VarArg(types.Any))
def lower_val_isin_dummy(context, builder, sig, args):
    fhm__xyj = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return fhm__xyj._getvalue()


@numba.generated_jit(nopython=True)
def pivot_impl(index_tup, columns_tup, values_tup, pivot_values,
    index_names, columns_name, value_names, check_duplicates=True, parallel
    =False):
    if not is_overload_constant_bool(check_duplicates):
        raise BodoError(
            'pivot_impl(): check_duplicates must be a constant boolean')
    lvdbu__fcx = get_overload_const_bool(check_duplicates)
    qiru__vqk = not is_overload_none(value_names)
    yrwz__dgz = isinstance(values_tup, types.UniTuple)
    if yrwz__dgz:
        qbx__kjrv = [to_nullable_type(values_tup.dtype)]
    else:
        qbx__kjrv = [to_nullable_type(suhhd__nlef) for suhhd__nlef in
            values_tup]
    tzeyj__jjmo = 'def impl(\n'
    tzeyj__jjmo += """    index_tup, columns_tup, values_tup, pivot_values, index_names, columns_name, value_names, check_duplicates=True, parallel=False
"""
    tzeyj__jjmo += '):\n'
    tzeyj__jjmo += '    if parallel:\n'
    yqrl__oeqew = ', '.join([f'array_to_info(index_tup[{i}])' for i in
        range(len(index_tup))] + [f'array_to_info(columns_tup[{i}])' for i in
        range(len(columns_tup))] + [f'array_to_info(values_tup[{i}])' for i in
        range(len(values_tup))])
    tzeyj__jjmo += f'        info_list = [{yqrl__oeqew}]\n'
    tzeyj__jjmo += '        cpp_table = arr_info_list_to_table(info_list)\n'
    tzeyj__jjmo += f"""        out_cpp_table = shuffle_table(cpp_table, {len(index_tup)}, parallel, 0)
"""
    gge__ojlsa = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i}), index_tup[{i}])'
         for i in range(len(index_tup))])
    supz__ofqin = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i + len(index_tup)}), columns_tup[{i}])'
         for i in range(len(columns_tup))])
    zfk__gilj = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i + len(index_tup) + len(columns_tup)}), values_tup[{i}])'
         for i in range(len(values_tup))])
    tzeyj__jjmo += f'        index_tup = ({gge__ojlsa},)\n'
    tzeyj__jjmo += f'        columns_tup = ({supz__ofqin},)\n'
    tzeyj__jjmo += f'        values_tup = ({zfk__gilj},)\n'
    tzeyj__jjmo += '        delete_table(cpp_table)\n'
    tzeyj__jjmo += '        delete_table(out_cpp_table)\n'
    tzeyj__jjmo += '    columns_arr = columns_tup[0]\n'
    if yrwz__dgz:
        tzeyj__jjmo += '    values_arrs = [arr for arr in values_tup]\n'
    tzeyj__jjmo += """    unique_index_arr_tup, row_vector = bodo.libs.array_ops.array_unique_vector_map(
"""
    tzeyj__jjmo += '        index_tup\n'
    tzeyj__jjmo += '    )\n'
    tzeyj__jjmo += '    n_rows = len(unique_index_arr_tup[0])\n'
    tzeyj__jjmo += '    num_values_arrays = len(values_tup)\n'
    tzeyj__jjmo += '    n_unique_pivots = len(pivot_values)\n'
    if yrwz__dgz:
        tzeyj__jjmo += '    n_cols = num_values_arrays * n_unique_pivots\n'
    else:
        tzeyj__jjmo += '    n_cols = n_unique_pivots\n'
    tzeyj__jjmo += '    col_map = {}\n'
    tzeyj__jjmo += '    for i in range(n_unique_pivots):\n'
    tzeyj__jjmo += (
        '        if bodo.libs.array_kernels.isna(pivot_values, i):\n')
    tzeyj__jjmo += '            raise ValueError(\n'
    tzeyj__jjmo += """                "DataFrame.pivot(): NA values in 'columns' array not supported\"
"""
    tzeyj__jjmo += '            )\n'
    tzeyj__jjmo += '        col_map[pivot_values[i]] = i\n'
    aej__qljp = False
    for i, zmovz__vijv in enumerate(qbx__kjrv):
        if is_str_arr_type(zmovz__vijv):
            aej__qljp = True
            tzeyj__jjmo += f"""    len_arrs_{i} = [np.zeros(n_rows, np.int64) for _ in range(n_cols)]
"""
            tzeyj__jjmo += f'    total_lens_{i} = np.zeros(n_cols, np.int64)\n'
    if aej__qljp:
        if lvdbu__fcx:
            tzeyj__jjmo += '    nbytes = (n_rows + 7) >> 3\n'
            tzeyj__jjmo += """    seen_bitmaps = [np.zeros(nbytes, np.int8) for _ in range(n_unique_pivots)]
"""
        tzeyj__jjmo += '    for i in range(len(columns_arr)):\n'
        tzeyj__jjmo += '        col_name = columns_arr[i]\n'
        tzeyj__jjmo += '        pivot_idx = col_map[col_name]\n'
        tzeyj__jjmo += '        row_idx = row_vector[i]\n'
        if lvdbu__fcx:
            tzeyj__jjmo += '        seen_bitmap = seen_bitmaps[pivot_idx]\n'
            tzeyj__jjmo += """        if bodo.libs.int_arr_ext.get_bit_bitmap_arr(seen_bitmap, row_idx):
"""
            tzeyj__jjmo += """            raise ValueError("DataFrame.pivot(): 'index' contains duplicate entries for the same output column")
"""
            tzeyj__jjmo += '        else:\n'
            tzeyj__jjmo += """            bodo.libs.int_arr_ext.set_bit_to_arr(seen_bitmap, row_idx, 1)
"""
        if yrwz__dgz:
            tzeyj__jjmo += '        for j in range(num_values_arrays):\n'
            tzeyj__jjmo += (
                '            col_idx = (j * len(pivot_values)) + pivot_idx\n')
            tzeyj__jjmo += '            len_arr = len_arrs_0[col_idx]\n'
            tzeyj__jjmo += '            values_arr = values_arrs[j]\n'
            tzeyj__jjmo += (
                '            if not bodo.libs.array_kernels.isna(values_arr, i):\n'
                )
            tzeyj__jjmo += (
                '                len_arr[row_idx] = len(values_arr[i])\n')
            tzeyj__jjmo += (
                '                total_lens_0[col_idx] += len(values_arr[i])\n'
                )
        else:
            for i, zmovz__vijv in enumerate(qbx__kjrv):
                if is_str_arr_type(zmovz__vijv):
                    tzeyj__jjmo += f"""        if not bodo.libs.array_kernels.isna(values_tup[{i}], i):
"""
                    tzeyj__jjmo += f"""            len_arrs_{i}[pivot_idx][row_idx] = len(values_tup[{i}][i])
"""
                    tzeyj__jjmo += f"""            total_lens_{i}[pivot_idx] += len(values_tup[{i}][i])
"""
    for i, zmovz__vijv in enumerate(qbx__kjrv):
        if is_str_arr_type(zmovz__vijv):
            tzeyj__jjmo += f'    data_arrs_{i} = [\n'
            tzeyj__jjmo += (
                '        bodo.libs.str_arr_ext.gen_na_str_array_lens(\n')
            tzeyj__jjmo += (
                f'            n_rows, total_lens_{i}[i], len_arrs_{i}[i]\n')
            tzeyj__jjmo += '        )\n'
            tzeyj__jjmo += '        for i in range(n_cols)\n'
            tzeyj__jjmo += '    ]\n'
        else:
            tzeyj__jjmo += f'    data_arrs_{i} = [\n'
            tzeyj__jjmo += f"""        bodo.libs.array_kernels.gen_na_array(n_rows, data_arr_typ_{i})
"""
            tzeyj__jjmo += '        for _ in range(n_cols)\n'
            tzeyj__jjmo += '    ]\n'
    if not aej__qljp and lvdbu__fcx:
        tzeyj__jjmo += '    nbytes = (n_rows + 7) >> 3\n'
        tzeyj__jjmo += """    seen_bitmaps = [np.zeros(nbytes, np.int8) for _ in range(n_unique_pivots)]
"""
    tzeyj__jjmo += '    for i in range(len(columns_arr)):\n'
    tzeyj__jjmo += '        col_name = columns_arr[i]\n'
    tzeyj__jjmo += '        pivot_idx = col_map[col_name]\n'
    tzeyj__jjmo += '        row_idx = row_vector[i]\n'
    if not aej__qljp and lvdbu__fcx:
        tzeyj__jjmo += '        seen_bitmap = seen_bitmaps[pivot_idx]\n'
        tzeyj__jjmo += """        if bodo.libs.int_arr_ext.get_bit_bitmap_arr(seen_bitmap, row_idx):
"""
        tzeyj__jjmo += """            raise ValueError("DataFrame.pivot(): 'index' contains duplicate entries for the same output column")
"""
        tzeyj__jjmo += '        else:\n'
        tzeyj__jjmo += """            bodo.libs.int_arr_ext.set_bit_to_arr(seen_bitmap, row_idx, 1)
"""
    if yrwz__dgz:
        tzeyj__jjmo += '        for j in range(num_values_arrays):\n'
        tzeyj__jjmo += (
            '            col_idx = (j * len(pivot_values)) + pivot_idx\n')
        tzeyj__jjmo += '            col_arr = data_arrs_0[col_idx]\n'
        tzeyj__jjmo += '            values_arr = values_arrs[j]\n'
        tzeyj__jjmo += (
            '            if bodo.libs.array_kernels.isna(values_arr, i):\n')
        tzeyj__jjmo += (
            '                bodo.libs.array_kernels.setna(col_arr, row_idx)\n'
            )
        tzeyj__jjmo += '            else:\n'
        tzeyj__jjmo += '                col_arr[row_idx] = values_arr[i]\n'
    else:
        for i, zmovz__vijv in enumerate(qbx__kjrv):
            tzeyj__jjmo += f'        col_arr_{i} = data_arrs_{i}[pivot_idx]\n'
            tzeyj__jjmo += (
                f'        if bodo.libs.array_kernels.isna(values_tup[{i}], i):\n'
                )
            tzeyj__jjmo += (
                f'            bodo.libs.array_kernels.setna(col_arr_{i}, row_idx)\n'
                )
            tzeyj__jjmo += f'        else:\n'
            tzeyj__jjmo += (
                f'            col_arr_{i}[row_idx] = values_tup[{i}][i]\n')
    if len(index_tup) == 1:
        tzeyj__jjmo += """    index = bodo.utils.conversion.index_from_array(unique_index_arr_tup[0], index_names[0])
"""
    else:
        tzeyj__jjmo += """    index = bodo.hiframes.pd_multi_index_ext.init_multi_index(unique_index_arr_tup, index_names, None)
"""
    if qiru__vqk:
        tzeyj__jjmo += '    num_rows = len(value_names) * len(pivot_values)\n'
        if is_str_arr_type(value_names):
            tzeyj__jjmo += '    total_chars = 0\n'
            tzeyj__jjmo += '    for i in range(len(value_names)):\n'
            tzeyj__jjmo += '        total_chars += len(value_names[i])\n'
            tzeyj__jjmo += """    new_value_names = bodo.libs.str_arr_ext.pre_alloc_string_array(num_rows, total_chars * len(pivot_values))
"""
        else:
            tzeyj__jjmo += """    new_value_names = bodo.utils.utils.alloc_type(num_rows, value_names, (-1,))
"""
        if is_str_arr_type(pivot_values):
            tzeyj__jjmo += '    total_chars = 0\n'
            tzeyj__jjmo += '    for i in range(len(pivot_values)):\n'
            tzeyj__jjmo += '        total_chars += len(pivot_values[i])\n'
            tzeyj__jjmo += """    new_pivot_values = bodo.libs.str_arr_ext.pre_alloc_string_array(num_rows, total_chars * len(value_names))
"""
        else:
            tzeyj__jjmo += """    new_pivot_values = bodo.utils.utils.alloc_type(num_rows, pivot_values, (-1,))
"""
        tzeyj__jjmo += '    for i in range(len(value_names)):\n'
        tzeyj__jjmo += '        for j in range(len(pivot_values)):\n'
        tzeyj__jjmo += """            new_value_names[(i * len(pivot_values)) + j] = value_names[i]
"""
        tzeyj__jjmo += """            new_pivot_values[(i * len(pivot_values)) + j] = pivot_values[j]
"""
        tzeyj__jjmo += """    column_index = bodo.hiframes.pd_multi_index_ext.init_multi_index((new_value_names, new_pivot_values), (None, columns_name), None)
"""
    else:
        tzeyj__jjmo += """    column_index =  bodo.utils.conversion.index_from_array(pivot_values, columns_name)
"""
    xfy__zhgw = ', '.join(f'data_arrs_{i}' for i in range(len(qbx__kjrv)))
    tzeyj__jjmo += f"""    table = bodo.hiframes.table.init_runtime_table_from_lists(({xfy__zhgw},), n_rows)
"""
    tzeyj__jjmo += (
        '    return bodo.hiframes.pd_dataframe_ext.init_runtime_cols_dataframe(\n'
        )
    tzeyj__jjmo += '        (table,), index, column_index\n'
    tzeyj__jjmo += '    )\n'
    gcyu__prty = {}
    zuvl__kdec = {f'data_arr_typ_{i}': zmovz__vijv for i, zmovz__vijv in
        enumerate(qbx__kjrv)}
    drz__wxog = {'bodo': bodo, 'np': np, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'shuffle_table':
        shuffle_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'info_from_table': info_from_table, **zuvl__kdec}
    exec(tzeyj__jjmo, drz__wxog, gcyu__prty)
    impl = gcyu__prty['impl']
    return impl


def gen_pandas_parquet_metadata(column_names, data_types, index,
    write_non_range_index_to_metadata, write_rangeindex_to_metadata,
    partition_cols=None, is_runtime_columns=False):
    pdl__iil = {}
    pdl__iil['columns'] = []
    if partition_cols is None:
        partition_cols = []
    for col_name, pkxx__hukua in zip(column_names, data_types):
        if col_name in partition_cols:
            continue
        whp__hgbpf = None
        if isinstance(pkxx__hukua, bodo.DatetimeArrayType):
            iod__agaqx = 'datetimetz'
            jsu__msief = 'datetime64[ns]'
            if isinstance(pkxx__hukua.tz, int):
                tvvl__vdkt = (bodo.libs.pd_datetime_arr_ext.
                    nanoseconds_to_offset(pkxx__hukua.tz))
            else:
                tvvl__vdkt = pd.DatetimeTZDtype(tz=pkxx__hukua.tz).tz
            whp__hgbpf = {'timezone': pa.lib.tzinfo_to_string(tvvl__vdkt)}
        elif isinstance(pkxx__hukua, types.Array
            ) or pkxx__hukua == boolean_array:
            iod__agaqx = jsu__msief = pkxx__hukua.dtype.name
            if jsu__msief.startswith('datetime'):
                iod__agaqx = 'datetime'
        elif is_str_arr_type(pkxx__hukua):
            iod__agaqx = 'unicode'
            jsu__msief = 'object'
        elif pkxx__hukua == binary_array_type:
            iod__agaqx = 'bytes'
            jsu__msief = 'object'
        elif isinstance(pkxx__hukua, DecimalArrayType):
            iod__agaqx = jsu__msief = 'object'
        elif isinstance(pkxx__hukua, IntegerArrayType):
            mxlnv__pjovq = pkxx__hukua.dtype.name
            if mxlnv__pjovq.startswith('int'):
                iod__agaqx = 'Int' + mxlnv__pjovq[3:]
            elif mxlnv__pjovq.startswith('uint'):
                iod__agaqx = 'UInt' + mxlnv__pjovq[4:]
            else:
                if is_runtime_columns:
                    col_name = 'Runtime determined column of type'
                raise BodoError(
                    'to_parquet(): unknown dtype in nullable Integer column {} {}'
                    .format(col_name, pkxx__hukua))
            jsu__msief = pkxx__hukua.dtype.name
        elif pkxx__hukua == datetime_date_array_type:
            iod__agaqx = 'datetime'
            jsu__msief = 'object'
        elif isinstance(pkxx__hukua, (StructArrayType, ArrayItemArrayType)):
            iod__agaqx = 'object'
            jsu__msief = 'object'
        else:
            if is_runtime_columns:
                col_name = 'Runtime determined column of type'
            raise BodoError(
                'to_parquet(): unsupported column type for metadata generation : {} {}'
                .format(col_name, pkxx__hukua))
        cbiwb__hgnz = {'name': col_name, 'field_name': col_name,
            'pandas_type': iod__agaqx, 'numpy_type': jsu__msief, 'metadata':
            whp__hgbpf}
        pdl__iil['columns'].append(cbiwb__hgnz)
    if write_non_range_index_to_metadata:
        if isinstance(index, MultiIndexType):
            raise BodoError('to_parquet: MultiIndex not supported yet')
        if 'none' in index.name:
            cdmv__zdfw = '__index_level_0__'
            nwijx__qwzll = None
        else:
            cdmv__zdfw = '%s'
            nwijx__qwzll = '%s'
        pdl__iil['index_columns'] = [cdmv__zdfw]
        pdl__iil['columns'].append({'name': nwijx__qwzll, 'field_name':
            cdmv__zdfw, 'pandas_type': index.pandas_type_name, 'numpy_type':
            index.numpy_type_name, 'metadata': None})
    elif write_rangeindex_to_metadata:
        pdl__iil['index_columns'] = [{'kind': 'range', 'name': '%s',
            'start': '%d', 'stop': '%d', 'step': '%d'}]
    else:
        pdl__iil['index_columns'] = []
    pdl__iil['pandas_version'] = pd.__version__
    return pdl__iil


@overload_method(DataFrameType, 'to_parquet', no_unliteral=True)
def to_parquet_overload(df, fname, engine='auto', compression='snappy',
    index=None, partition_cols=None, storage_options=None, _is_parallel=False):
    check_unsupported_args('DataFrame.to_parquet', {'storage_options':
        storage_options}, {'storage_options': None}, package_name='pandas',
        module_name='IO')
    if df.has_runtime_cols and not is_overload_none(partition_cols):
        raise BodoError(
            f"DataFrame.to_parquet(): Providing 'partition_cols' on DataFrames with columns determined at runtime is not yet supported. Please return the DataFrame to regular Python to update typing information."
            )
    if not is_overload_none(engine) and get_overload_const_str(engine) not in (
        'auto', 'pyarrow'):
        raise BodoError('DataFrame.to_parquet(): only pyarrow engine supported'
            )
    if not is_overload_none(compression) and get_overload_const_str(compression
        ) not in {'snappy', 'gzip', 'brotli'}:
        raise BodoError('to_parquet(): Unsupported compression: ' + str(
            get_overload_const_str(compression)))
    if not is_overload_none(partition_cols):
        partition_cols = get_overload_const_list(partition_cols)
        kbq__fnh = []
        for dig__uiubj in partition_cols:
            try:
                idx = df.columns.index(dig__uiubj)
            except ValueError as rsgy__pps:
                raise BodoError(
                    f'Partition column {dig__uiubj} is not in dataframe')
            kbq__fnh.append(idx)
    else:
        partition_cols = None
    if not is_overload_none(index) and not is_overload_constant_bool(index):
        raise BodoError('to_parquet(): index must be a constant bool or None')
    from bodo.io.parquet_pio import parquet_write_table_cpp, parquet_write_table_partitioned_cpp
    yrkn__argc = isinstance(df.index, bodo.hiframes.pd_index_ext.RangeIndexType
        )
    pymd__sxvt = df.index is not None and (is_overload_true(_is_parallel) or
        not is_overload_true(_is_parallel) and not yrkn__argc)
    write_non_range_index_to_metadata = is_overload_true(index
        ) or is_overload_none(index) and (not yrkn__argc or
        is_overload_true(_is_parallel))
    write_rangeindex_to_metadata = is_overload_none(index
        ) and yrkn__argc and not is_overload_true(_is_parallel)
    if df.has_runtime_cols:
        if isinstance(df.runtime_colname_typ, MultiIndexType):
            raise BodoError(
                'DataFrame.to_parquet(): Not supported with MultiIndex runtime column names. Please return the DataFrame to regular Python to update typing information.'
                )
        if not isinstance(df.runtime_colname_typ, bodo.hiframes.
            pd_index_ext.StringIndexType):
            raise BodoError(
                'DataFrame.to_parquet(): parquet must have string column names. Please return the DataFrame with runtime column names to regular Python to modify column names.'
                )
        zuqa__tvgu = df.runtime_data_types
        sel__bfo = len(zuqa__tvgu)
        whp__hgbpf = gen_pandas_parquet_metadata([''] * sel__bfo,
            zuqa__tvgu, df.index, write_non_range_index_to_metadata,
            write_rangeindex_to_metadata, partition_cols=partition_cols,
            is_runtime_columns=True)
        feva__fjk = whp__hgbpf['columns'][:sel__bfo]
        whp__hgbpf['columns'] = whp__hgbpf['columns'][sel__bfo:]
        feva__fjk = [json.dumps(ledbu__lptbj).replace('""', '{0}') for
            ledbu__lptbj in feva__fjk]
        kgpi__vnci = json.dumps(whp__hgbpf)
        jwvnq__bsbd = '"columns": ['
        war__ewiit = kgpi__vnci.find(jwvnq__bsbd)
        if war__ewiit == -1:
            raise BodoError(
                'DataFrame.to_parquet(): Unexpected metadata string for runtime columns.  Please return the DataFrame to regular Python to update typing information.'
                )
        zivv__ghb = war__ewiit + len(jwvnq__bsbd)
        gkoj__dnsvc = kgpi__vnci[:zivv__ghb]
        kgpi__vnci = kgpi__vnci[zivv__ghb:]
        kvq__ybqak = len(whp__hgbpf['columns'])
    else:
        kgpi__vnci = json.dumps(gen_pandas_parquet_metadata(df.columns, df.
            data, df.index, write_non_range_index_to_metadata,
            write_rangeindex_to_metadata, partition_cols=partition_cols,
            is_runtime_columns=False))
    if not is_overload_true(_is_parallel) and yrkn__argc:
        kgpi__vnci = kgpi__vnci.replace('"%d"', '%d')
        if df.index.name == 'RangeIndexType(none)':
            kgpi__vnci = kgpi__vnci.replace('"%s"', '%s')
    if not df.is_table_format:
        lfn__fdkiz = ', '.join(
            'array_to_info(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}))'
            .format(i) for i in range(len(df.columns)))
    tzeyj__jjmo = """def df_to_parquet(df, fname, engine='auto', compression='snappy', index=None, partition_cols=None, storage_options=None, _is_parallel=False):
"""
    if df.is_table_format:
        tzeyj__jjmo += '    py_table = get_dataframe_table(df)\n'
        tzeyj__jjmo += (
            '    table = py_table_to_cpp_table(py_table, py_table_typ)\n')
    else:
        tzeyj__jjmo += '    info_list = [{}]\n'.format(lfn__fdkiz)
        tzeyj__jjmo += '    table = arr_info_list_to_table(info_list)\n'
    if df.has_runtime_cols:
        tzeyj__jjmo += '    columns_index = get_dataframe_column_names(df)\n'
        tzeyj__jjmo += '    names_arr = index_to_array(columns_index)\n'
        tzeyj__jjmo += '    col_names = array_to_info(names_arr)\n'
    else:
        tzeyj__jjmo += '    col_names = array_to_info(col_names_arr)\n'
    if is_overload_true(index) or is_overload_none(index) and pymd__sxvt:
        tzeyj__jjmo += """    index_col = array_to_info(index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)))
"""
        zlsyg__fvyj = True
    else:
        tzeyj__jjmo += '    index_col = array_to_info(np.empty(0))\n'
        zlsyg__fvyj = False
    if df.has_runtime_cols:
        tzeyj__jjmo += '    columns_lst = []\n'
        tzeyj__jjmo += '    num_cols = 0\n'
        for i in range(len(df.runtime_data_types)):
            tzeyj__jjmo += f'    for _ in range(len(py_table.block_{i})):\n'
            tzeyj__jjmo += f"""        columns_lst.append({feva__fjk[i]!r}.replace('{{0}}', '"' + names_arr[num_cols] + '"'))
"""
            tzeyj__jjmo += '        num_cols += 1\n'
        if kvq__ybqak:
            tzeyj__jjmo += "    columns_lst.append('')\n"
        tzeyj__jjmo += '    columns_str = ", ".join(columns_lst)\n'
        tzeyj__jjmo += ('    metadata = """' + gkoj__dnsvc +
            '""" + columns_str + """' + kgpi__vnci + '"""\n')
    else:
        tzeyj__jjmo += '    metadata = """' + kgpi__vnci + '"""\n'
    tzeyj__jjmo += '    if compression is None:\n'
    tzeyj__jjmo += "        compression = 'none'\n"
    tzeyj__jjmo += '    if df.index.name is not None:\n'
    tzeyj__jjmo += '        name_ptr = df.index.name\n'
    tzeyj__jjmo += '    else:\n'
    tzeyj__jjmo += "        name_ptr = 'null'\n"
    tzeyj__jjmo += f"""    bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel=_is_parallel)
"""
    ykqnc__uooy = None
    if partition_cols:
        ykqnc__uooy = pd.array([col_name for col_name in df.columns if 
            col_name not in partition_cols])
        xhmm__slyo = ', '.join(
            f'array_to_info(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).dtype.categories.values)'
             for i in range(len(df.columns)) if isinstance(df.data[i],
            CategoricalArrayType) and i in kbq__fnh)
        if xhmm__slyo:
            tzeyj__jjmo += '    cat_info_list = [{}]\n'.format(xhmm__slyo)
            tzeyj__jjmo += (
                '    cat_table = arr_info_list_to_table(cat_info_list)\n')
        else:
            tzeyj__jjmo += '    cat_table = table\n'
        tzeyj__jjmo += (
            '    col_names_no_partitions = array_to_info(col_names_no_parts_arr)\n'
            )
        tzeyj__jjmo += (
            f'    part_cols_idxs = np.array({kbq__fnh}, dtype=np.int32)\n')
        tzeyj__jjmo += (
            '    parquet_write_table_partitioned_cpp(unicode_to_utf8(fname),\n'
            )
        tzeyj__jjmo += """                            table, col_names, col_names_no_partitions, cat_table,
"""
        tzeyj__jjmo += (
            '                            part_cols_idxs.ctypes, len(part_cols_idxs),\n'
            )
        tzeyj__jjmo += (
            '                            unicode_to_utf8(compression),\n')
        tzeyj__jjmo += '                            _is_parallel,\n'
        tzeyj__jjmo += (
            '                            unicode_to_utf8(bucket_region))\n')
        tzeyj__jjmo += '    delete_table_decref_arrays(table)\n'
        tzeyj__jjmo += '    delete_info_decref_array(index_col)\n'
        tzeyj__jjmo += (
            '    delete_info_decref_array(col_names_no_partitions)\n')
        tzeyj__jjmo += '    delete_info_decref_array(col_names)\n'
        if xhmm__slyo:
            tzeyj__jjmo += '    delete_table_decref_arrays(cat_table)\n'
    elif write_rangeindex_to_metadata:
        tzeyj__jjmo += '    parquet_write_table_cpp(unicode_to_utf8(fname),\n'
        tzeyj__jjmo += (
            '                            table, col_names, index_col,\n')
        tzeyj__jjmo += '                            ' + str(zlsyg__fvyj
            ) + ',\n'
        tzeyj__jjmo += (
            '                            unicode_to_utf8(metadata),\n')
        tzeyj__jjmo += (
            '                            unicode_to_utf8(compression),\n')
        tzeyj__jjmo += (
            '                            _is_parallel, 1, df.index.start,\n')
        tzeyj__jjmo += (
            '                            df.index.stop, df.index.step,\n')
        tzeyj__jjmo += (
            '                            unicode_to_utf8(name_ptr),\n')
        tzeyj__jjmo += (
            '                            unicode_to_utf8(bucket_region))\n')
        tzeyj__jjmo += '    delete_table_decref_arrays(table)\n'
        tzeyj__jjmo += '    delete_info_decref_array(index_col)\n'
        tzeyj__jjmo += '    delete_info_decref_array(col_names)\n'
    else:
        tzeyj__jjmo += '    parquet_write_table_cpp(unicode_to_utf8(fname),\n'
        tzeyj__jjmo += (
            '                            table, col_names, index_col,\n')
        tzeyj__jjmo += '                            ' + str(zlsyg__fvyj
            ) + ',\n'
        tzeyj__jjmo += (
            '                            unicode_to_utf8(metadata),\n')
        tzeyj__jjmo += (
            '                            unicode_to_utf8(compression),\n')
        tzeyj__jjmo += (
            '                            _is_parallel, 0, 0, 0, 0,\n')
        tzeyj__jjmo += (
            '                            unicode_to_utf8(name_ptr),\n')
        tzeyj__jjmo += (
            '                            unicode_to_utf8(bucket_region))\n')
        tzeyj__jjmo += '    delete_table_decref_arrays(table)\n'
        tzeyj__jjmo += '    delete_info_decref_array(index_col)\n'
        tzeyj__jjmo += '    delete_info_decref_array(col_names)\n'
    gcyu__prty = {}
    if df.has_runtime_cols:
        hdc__sjrsd = None
    else:
        for tda__xwke in df.columns:
            if not isinstance(tda__xwke, str):
                raise BodoError(
                    'DataFrame.to_parquet(): parquet must have string column names'
                    )
        hdc__sjrsd = pd.array(df.columns)
    exec(tzeyj__jjmo, {'np': np, 'bodo': bodo, 'unicode_to_utf8':
        unicode_to_utf8, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table,
        'str_arr_from_sequence': str_arr_from_sequence,
        'parquet_write_table_cpp': parquet_write_table_cpp,
        'parquet_write_table_partitioned_cpp':
        parquet_write_table_partitioned_cpp, 'index_to_array':
        index_to_array, 'delete_info_decref_array':
        delete_info_decref_array, 'delete_table_decref_arrays':
        delete_table_decref_arrays, 'col_names_arr': hdc__sjrsd,
        'py_table_to_cpp_table': py_table_to_cpp_table, 'py_table_typ': df.
        table_type, 'get_dataframe_table': get_dataframe_table,
        'col_names_no_parts_arr': ykqnc__uooy, 'get_dataframe_column_names':
        get_dataframe_column_names, 'fix_arr_dtype': fix_arr_dtype,
        'decode_if_dict_array': decode_if_dict_array,
        'decode_if_dict_table': decode_if_dict_table}, gcyu__prty)
    vlioa__sffky = gcyu__prty['df_to_parquet']
    return vlioa__sffky


def to_sql_exception_guard(df, name, con, schema=None, if_exists='fail',
    index=True, index_label=None, chunksize=None, dtype=None, method=None,
    _is_table_create=False, _is_parallel=False):
    ahrww__icg = 'all_ok'
    lfrf__gkwoy = urlparse(con).scheme
    if _is_parallel and bodo.get_rank() == 0:
        hdz__roh = 100
        if chunksize is None:
            mcprw__phol = hdz__roh
        else:
            mcprw__phol = min(chunksize, hdz__roh)
        if _is_table_create:
            df = df.iloc[:mcprw__phol, :]
        else:
            df = df.iloc[mcprw__phol:, :]
            if len(df) == 0:
                return ahrww__icg
    if lfrf__gkwoy == 'snowflake':
        try:
            from snowflake.connector.pandas_tools import pd_writer
            from bodo import snowflake_sqlalchemy_compat
            if method is not None and _is_table_create and bodo.get_rank(
                ) == 0:
                import warnings
                from bodo.utils.typing import BodoWarning
                warnings.warn(BodoWarning(
                    'DataFrame.to_sql(): method argument is not supported with Snowflake. Bodo always uses snowflake.connector.pandas_tools.pd_writer to write data.'
                    ))
            method = pd_writer
            df.columns = [(ixz__sio.upper() if ixz__sio.islower() else
                ixz__sio) for ixz__sio in df.columns]
        except ImportError as rsgy__pps:
            ahrww__icg = (
                "Snowflake Python connector packages not found. Using 'to_sql' with Snowflake requires both snowflake-sqlalchemy and snowflake-connector-python. These can be installed by calling 'conda install -c conda-forge snowflake-sqlalchemy snowflake-connector-python' or 'pip install snowflake-sqlalchemy snowflake-connector-python'."
                )
            return ahrww__icg
    try:
        df.to_sql(name, con, schema, if_exists, index, index_label,
            chunksize, dtype, method)
    except Exception as isto__sluin:
        ahrww__icg = isto__sluin.args[0]
    return ahrww__icg


@numba.njit
def to_sql_exception_guard_encaps(df, name, con, schema=None, if_exists=
    'fail', index=True, index_label=None, chunksize=None, dtype=None,
    method=None, _is_table_create=False, _is_parallel=False):
    with numba.objmode(out='unicode_type'):
        out = to_sql_exception_guard(df, name, con, schema, if_exists,
            index, index_label, chunksize, dtype, method, _is_table_create,
            _is_parallel)
    return out


@overload_method(DataFrameType, 'to_sql')
def to_sql_overload(df, name, con, schema=None, if_exists='fail', index=
    True, index_label=None, chunksize=None, dtype=None, method=None,
    _is_parallel=False):
    check_runtime_cols_unsupported(df, 'DataFrame.to_sql()')
    if is_overload_none(schema):
        if bodo.get_rank() == 0:
            import warnings
            warnings.warn(BodoWarning(
                f'DataFrame.to_sql(): schema argument is recommended to avoid permission issues when writing the table.'
                ))
    if not (is_overload_none(chunksize) or isinstance(chunksize, types.Integer)
        ):
        raise BodoError(
            "DataFrame.to_sql(): 'chunksize' argument must be an integer if provided."
            )

    def _impl(df, name, con, schema=None, if_exists='fail', index=True,
        index_label=None, chunksize=None, dtype=None, method=None,
        _is_parallel=False):
        qel__wizb = bodo.libs.distributed_api.get_rank()
        ahrww__icg = 'unset'
        if qel__wizb != 0:
            ahrww__icg = bcast_scalar(ahrww__icg)
        elif qel__wizb == 0:
            ahrww__icg = to_sql_exception_guard_encaps(df, name, con,
                schema, if_exists, index, index_label, chunksize, dtype,
                method, True, _is_parallel)
            ahrww__icg = bcast_scalar(ahrww__icg)
        if_exists = 'append'
        if _is_parallel and ahrww__icg == 'all_ok':
            ahrww__icg = to_sql_exception_guard_encaps(df, name, con,
                schema, if_exists, index, index_label, chunksize, dtype,
                method, False, _is_parallel)
        if ahrww__icg != 'all_ok':
            print('err_msg=', ahrww__icg)
            raise ValueError('error in to_sql() operation')
    return _impl


@overload_method(DataFrameType, 'to_csv', no_unliteral=True)
def to_csv_overload(df, path_or_buf=None, sep=',', na_rep='', float_format=
    None, columns=None, header=True, index=True, index_label=None, mode='w',
    encoding=None, compression=None, quoting=None, quotechar='"',
    line_terminator=None, chunksize=None, date_format=None, doublequote=
    True, escapechar=None, decimal='.', errors='strict', storage_options=None):
    check_runtime_cols_unsupported(df, 'DataFrame.to_csv()')
    check_unsupported_args('DataFrame.to_csv', {'encoding': encoding,
        'mode': mode, 'errors': errors, 'storage_options': storage_options},
        {'encoding': None, 'mode': 'w', 'errors': 'strict',
        'storage_options': None}, package_name='pandas', module_name='IO')
    if not (is_overload_none(path_or_buf) or is_overload_constant_str(
        path_or_buf) or path_or_buf == string_type):
        raise BodoError(
            "DataFrame.to_csv(): 'path_or_buf' argument should be None or string"
            )
    if not is_overload_none(compression):
        raise BodoError(
            "DataFrame.to_csv(): 'compression' argument supports only None, which is the default in JIT code."
            )
    if is_overload_constant_str(path_or_buf):
        oor__glj = get_overload_const_str(path_or_buf)
        if oor__glj.endswith(('.gz', '.bz2', '.zip', '.xz')):
            import warnings
            from bodo.utils.typing import BodoWarning
            warnings.warn(BodoWarning(
                "DataFrame.to_csv(): 'compression' argument defaults to None in JIT code, which is the only supported value."
                ))
    if not (is_overload_none(columns) or isinstance(columns, (types.List,
        types.Tuple))):
        raise BodoError(
            "DataFrame.to_csv(): 'columns' argument must be list a or tuple type."
            )
    if is_overload_none(path_or_buf):

        def _impl(df, path_or_buf=None, sep=',', na_rep='', float_format=
            None, columns=None, header=True, index=True, index_label=None,
            mode='w', encoding=None, compression=None, quoting=None,
            quotechar='"', line_terminator=None, chunksize=None,
            date_format=None, doublequote=True, escapechar=None, decimal=
            '.', errors='strict', storage_options=None):
            with numba.objmode(D='unicode_type'):
                D = df.to_csv(path_or_buf, sep, na_rep, float_format,
                    columns, header, index, index_label, mode, encoding,
                    compression, quoting, quotechar, line_terminator,
                    chunksize, date_format, doublequote, escapechar,
                    decimal, errors, storage_options)
            return D
        return _impl

    def _impl(df, path_or_buf=None, sep=',', na_rep='', float_format=None,
        columns=None, header=True, index=True, index_label=None, mode='w',
        encoding=None, compression=None, quoting=None, quotechar='"',
        line_terminator=None, chunksize=None, date_format=None, doublequote
        =True, escapechar=None, decimal='.', errors='strict',
        storage_options=None):
        with numba.objmode(D='unicode_type'):
            D = df.to_csv(None, sep, na_rep, float_format, columns, header,
                index, index_label, mode, encoding, compression, quoting,
                quotechar, line_terminator, chunksize, date_format,
                doublequote, escapechar, decimal, errors, storage_options)
        bodo.io.fs_io.csv_write(path_or_buf, D)
    return _impl


@overload_method(DataFrameType, 'to_json', no_unliteral=True)
def to_json_overload(df, path_or_buf=None, orient='records', date_format=
    None, double_precision=10, force_ascii=True, date_unit='ms',
    default_handler=None, lines=True, compression='infer', index=True,
    indent=None, storage_options=None):
    check_runtime_cols_unsupported(df, 'DataFrame.to_json()')
    check_unsupported_args('DataFrame.to_json', {'storage_options':
        storage_options}, {'storage_options': None}, package_name='pandas',
        module_name='IO')
    if path_or_buf is None or path_or_buf == types.none:

        def _impl(df, path_or_buf=None, orient='records', date_format=None,
            double_precision=10, force_ascii=True, date_unit='ms',
            default_handler=None, lines=True, compression='infer', index=
            True, indent=None, storage_options=None):
            with numba.objmode(D='unicode_type'):
                D = df.to_json(path_or_buf, orient, date_format,
                    double_precision, force_ascii, date_unit,
                    default_handler, lines, compression, index, indent,
                    storage_options)
            return D
        return _impl

    def _impl(df, path_or_buf=None, orient='records', date_format=None,
        double_precision=10, force_ascii=True, date_unit='ms',
        default_handler=None, lines=True, compression='infer', index=True,
        indent=None, storage_options=None):
        with numba.objmode(D='unicode_type'):
            D = df.to_json(None, orient, date_format, double_precision,
                force_ascii, date_unit, default_handler, lines, compression,
                index, indent, storage_options)
        blge__mtda = bodo.io.fs_io.get_s3_bucket_region_njit(path_or_buf,
            parallel=False)
        if lines and orient == 'records':
            bodo.hiframes.pd_dataframe_ext._json_write(unicode_to_utf8(
                path_or_buf), unicode_to_utf8(D), 0, len(D), False, True,
                unicode_to_utf8(blge__mtda))
            bodo.utils.utils.check_and_propagate_cpp_exception()
        else:
            bodo.hiframes.pd_dataframe_ext._json_write(unicode_to_utf8(
                path_or_buf), unicode_to_utf8(D), 0, len(D), False, False,
                unicode_to_utf8(blge__mtda))
            bodo.utils.utils.check_and_propagate_cpp_exception()
    return _impl


@overload(pd.get_dummies, inline='always', no_unliteral=True)
def get_dummies(data, prefix=None, prefix_sep='_', dummy_na=False, columns=
    None, sparse=False, drop_first=False, dtype=None):
    yevbm__fnd = {'prefix': prefix, 'prefix_sep': prefix_sep, 'dummy_na':
        dummy_na, 'columns': columns, 'sparse': sparse, 'drop_first':
        drop_first, 'dtype': dtype}
    hkcy__hmt = {'prefix': None, 'prefix_sep': '_', 'dummy_na': False,
        'columns': None, 'sparse': False, 'drop_first': False, 'dtype': None}
    check_unsupported_args('pandas.get_dummies', yevbm__fnd, hkcy__hmt,
        package_name='pandas', module_name='General')
    if not categorical_can_construct_dataframe(data):
        raise BodoError(
            'pandas.get_dummies() only support categorical data types with explicitly known categories'
            )
    tzeyj__jjmo = """def impl(data, prefix=None, prefix_sep='_', dummy_na=False, columns=None, sparse=False, drop_first=False, dtype=None,):
"""
    if isinstance(data, SeriesType):
        wbng__lpr = data.data.dtype.categories
        tzeyj__jjmo += (
            '  data_values = bodo.hiframes.pd_series_ext.get_series_data(data)\n'
            )
    else:
        wbng__lpr = data.dtype.categories
        tzeyj__jjmo += '  data_values = data\n'
    cnsg__sdwvq = len(wbng__lpr)
    tzeyj__jjmo += """  codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(data_values)
"""
    tzeyj__jjmo += '  numba.parfors.parfor.init_prange()\n'
    tzeyj__jjmo += '  n = len(data_values)\n'
    for i in range(cnsg__sdwvq):
        tzeyj__jjmo += '  data_arr_{} = np.empty(n, np.uint8)\n'.format(i)
    tzeyj__jjmo += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    tzeyj__jjmo += '      if bodo.libs.array_kernels.isna(data_values, i):\n'
    for bfof__stevo in range(cnsg__sdwvq):
        tzeyj__jjmo += '          data_arr_{}[i] = 0\n'.format(bfof__stevo)
    tzeyj__jjmo += '      else:\n'
    for xkd__omszr in range(cnsg__sdwvq):
        tzeyj__jjmo += '          data_arr_{0}[i] = codes[i] == {0}\n'.format(
            xkd__omszr)
    lfn__fdkiz = ', '.join(f'data_arr_{i}' for i in range(cnsg__sdwvq))
    index = 'bodo.hiframes.pd_index_ext.init_range_index(0, n, 1, None)'
    if isinstance(wbng__lpr[0], np.datetime64):
        wbng__lpr = tuple(pd.Timestamp(ixz__sio) for ixz__sio in wbng__lpr)
    elif isinstance(wbng__lpr[0], np.timedelta64):
        wbng__lpr = tuple(pd.Timedelta(ixz__sio) for ixz__sio in wbng__lpr)
    return bodo.hiframes.dataframe_impl._gen_init_df(tzeyj__jjmo, wbng__lpr,
        lfn__fdkiz, index)


def categorical_can_construct_dataframe(val):
    if isinstance(val, CategoricalArrayType):
        return val.dtype.categories is not None
    elif isinstance(val, SeriesType) and isinstance(val.data,
        CategoricalArrayType):
        return val.data.dtype.categories is not None
    return False


def handle_inplace_df_type_change(inplace, _bodo_transformed, func_name):
    if is_overload_false(_bodo_transformed
        ) and bodo.transforms.typing_pass.in_partial_typing and (
        is_overload_true(inplace) or not is_overload_constant_bool(inplace)):
        bodo.transforms.typing_pass.typing_transform_required = True
        raise Exception('DataFrame.{}(): transform necessary for inplace'.
            format(func_name))


pd_unsupported = (pd.read_pickle, pd.read_table, pd.read_fwf, pd.
    read_clipboard, pd.ExcelFile, pd.read_html, pd.read_xml, pd.read_hdf,
    pd.read_feather, pd.read_orc, pd.read_sas, pd.read_spss, pd.
    read_sql_table, pd.read_sql_query, pd.read_gbq, pd.read_stata, pd.
    ExcelWriter, pd.json_normalize, pd.melt, pd.merge_ordered, pd.factorize,
    pd.wide_to_long, pd.bdate_range, pd.period_range, pd.infer_freq, pd.
    interval_range, pd.eval, pd.test, pd.Grouper)
pd_util_unsupported = pd.util.hash_array, pd.util.hash_pandas_object
dataframe_unsupported = ['set_flags', 'convert_dtypes', 'bool', '__iter__',
    'items', 'iteritems', 'keys', 'iterrows', 'lookup', 'pop', 'xs', 'get',
    'add', 'sub', 'mul', 'div', 'truediv', 'floordiv', 'mod', 'pow', 'dot',
    'radd', 'rsub', 'rmul', 'rdiv', 'rtruediv', 'rfloordiv', 'rmod', 'rpow',
    'lt', 'gt', 'le', 'ge', 'ne', 'eq', 'combine', 'combine_first',
    'subtract', 'divide', 'multiply', 'applymap', 'agg', 'aggregate',
    'transform', 'expanding', 'ewm', 'all', 'any', 'clip', 'corrwith',
    'cummax', 'cummin', 'eval', 'kurt', 'kurtosis', 'mad', 'mode', 'rank',
    'round', 'sem', 'skew', 'value_counts', 'add_prefix', 'add_suffix',
    'align', 'at_time', 'between_time', 'equals', 'reindex', 'reindex_like',
    'rename_axis', 'set_axis', 'truncate', 'backfill', 'bfill', 'ffill',
    'interpolate', 'pad', 'droplevel', 'reorder_levels', 'nlargest',
    'nsmallest', 'swaplevel', 'stack', 'unstack', 'swapaxes', 'melt',
    'squeeze', 'to_xarray', 'T', 'transpose', 'compare', 'update', 'asfreq',
    'asof', 'slice_shift', 'tshift', 'first_valid_index',
    'last_valid_index', 'resample', 'to_period', 'to_timestamp',
    'tz_convert', 'tz_localize', 'boxplot', 'hist', 'from_dict',
    'from_records', 'to_pickle', 'to_hdf', 'to_dict', 'to_excel', 'to_html',
    'to_feather', 'to_latex', 'to_stata', 'to_gbq', 'to_records',
    'to_clipboard', 'to_markdown', 'to_xml']
dataframe_unsupported_attrs = ['at', 'attrs', 'axes', 'flags', 'style',
    'sparse']


def _install_pd_unsupported(mod_name, pd_unsupported):
    for hlat__pbgum in pd_unsupported:
        fname = mod_name + '.' + hlat__pbgum.__name__
        overload(hlat__pbgum, no_unliteral=True)(create_unsupported_overload
            (fname))


def _install_dataframe_unsupported():
    for eaz__pvcs in dataframe_unsupported_attrs:
        maa__ayo = 'DataFrame.' + eaz__pvcs
        overload_attribute(DataFrameType, eaz__pvcs)(
            create_unsupported_overload(maa__ayo))
    for fname in dataframe_unsupported:
        maa__ayo = 'DataFrame.' + fname + '()'
        overload_method(DataFrameType, fname)(create_unsupported_overload(
            maa__ayo))


_install_pd_unsupported('pandas', pd_unsupported)
_install_pd_unsupported('pandas.util', pd_util_unsupported)
_install_dataframe_unsupported()
