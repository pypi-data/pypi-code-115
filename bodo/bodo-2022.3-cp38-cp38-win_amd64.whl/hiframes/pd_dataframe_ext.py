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
            hdha__atikg = f'{len(self.data)} columns of types {set(self.data)}'
            ggl__lyrwg = (
                f"('{self.columns[0]}', '{self.columns[1]}', ..., '{self.columns[-1]}')"
                )
            return (
                f'dataframe({hdha__atikg}, {self.index}, {ggl__lyrwg}, {self.dist}, {self.is_table_format})'
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
            qoxpz__rrbkr = (self.index if self.index == other.index else
                self.index.unify(typingctx, other.index))
            data = tuple(aqhan__xmu.unify(typingctx, jldvn__skgf) if 
                aqhan__xmu != jldvn__skgf else aqhan__xmu for aqhan__xmu,
                jldvn__skgf in zip(self.data, other.data))
            dist = Distribution(min(self.dist.value, other.dist.value))
            if qoxpz__rrbkr is not None and None not in data:
                return DataFrameType(data, qoxpz__rrbkr, self.columns, dist,
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
        return all(aqhan__xmu.is_precise() for aqhan__xmu in self.data
            ) and self.index.is_precise()

    def replace_col_type(self, col_name, new_type):
        if col_name not in self.columns:
            raise ValueError(
                f"DataFrameType.replace_col_type replaced column must be found in the DataFrameType. '{col_name}' not found in DataFrameType with columns {self.columns}"
                )
        kiigl__iyu = self.columns.index(col_name)
        ybhd__uzmp = tuple(list(self.data[:kiigl__iyu]) + [new_type] + list
            (self.data[kiigl__iyu + 1:]))
        return DataFrameType(ybhd__uzmp, self.index, self.columns, self.
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
        xqw__ovgqq = [('data', data_typ), ('index', fe_type.df_type.index),
            ('parent', types.pyobject)]
        if fe_type.df_type.has_runtime_cols:
            xqw__ovgqq.append(('columns', fe_type.df_type.runtime_colname_typ))
        super(DataFramePayloadModel, self).__init__(dmm, fe_type, xqw__ovgqq)


@register_model(DataFrameType)
class DataFrameModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = DataFramePayloadType(fe_type)
        xqw__ovgqq = [('meminfo', types.MemInfoPointer(payload_type)), (
            'parent', types.pyobject)]
        super(DataFrameModel, self).__init__(dmm, fe_type, xqw__ovgqq)


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
        lxwly__gwjon = 'n',
        glui__gec = {'n': 5}
        pfvhw__mryrj, yblhw__ezwc = bodo.utils.typing.fold_typing_args(
            func_name, args, kws, lxwly__gwjon, glui__gec)
        oga__teqa = yblhw__ezwc[0]
        if not is_overload_int(oga__teqa):
            raise BodoError(f"{func_name}(): 'n' must be an Integer")
        qzs__grqmr = df.copy(is_table_format=False)
        return qzs__grqmr(*yblhw__ezwc).replace(pysig=pfvhw__mryrj)

    @bound_function('df.corr')
    def resolve_corr(self, df, args, kws):
        func_name = 'DataFrame.corr'
        check_runtime_cols_unsupported(df, f'{func_name}()')
        ogez__fzo = (df,) + args
        lxwly__gwjon = 'df', 'method', 'min_periods'
        glui__gec = {'method': 'pearson', 'min_periods': 1}
        jqf__psy = 'method',
        pfvhw__mryrj, yblhw__ezwc = bodo.utils.typing.fold_typing_args(
            func_name, ogez__fzo, kws, lxwly__gwjon, glui__gec, jqf__psy)
        kce__sfofn = yblhw__ezwc[2]
        if not is_overload_int(kce__sfofn):
            raise BodoError(f"{func_name}(): 'min_periods' must be an Integer")
        dcd__aknr = []
        shnih__ide = []
        for htcp__ynkuq, nlljq__ayjd in zip(df.columns, df.data):
            if bodo.utils.typing._is_pandas_numeric_dtype(nlljq__ayjd.dtype):
                dcd__aknr.append(htcp__ynkuq)
                shnih__ide.append(types.Array(types.float64, 1, 'A'))
        if len(dcd__aknr) == 0:
            raise_bodo_error('DataFrame.corr(): requires non-empty dataframe')
        shnih__ide = tuple(shnih__ide)
        dcd__aknr = tuple(dcd__aknr)
        index_typ = bodo.utils.typing.type_col_to_index(dcd__aknr)
        qzs__grqmr = DataFrameType(shnih__ide, index_typ, dcd__aknr)
        return qzs__grqmr(*yblhw__ezwc).replace(pysig=pfvhw__mryrj)

    @bound_function('df.pipe', no_unliteral=True)
    def resolve_pipe(self, df, args, kws):
        check_runtime_cols_unsupported(df, 'DataFrame.pipe()')
        return bodo.hiframes.pd_groupby_ext.resolve_obj_pipe(self, df, args,
            kws, 'DataFrame')

    @bound_function('df.apply', no_unliteral=True)
    def resolve_apply(self, df, args, kws):
        check_runtime_cols_unsupported(df, 'DataFrame.apply()')
        kws = dict(kws)
        qww__zbj = args[0] if len(args) > 0 else kws.pop('func', None)
        axis = args[1] if len(args) > 1 else kws.pop('axis', types.literal(0))
        kvu__fhval = args[2] if len(args) > 2 else kws.pop('raw', types.
            literal(False))
        fvbrl__kkmku = args[3] if len(args) > 3 else kws.pop('result_type',
            types.none)
        ssr__wfr = args[4] if len(args) > 4 else kws.pop('args', types.
            Tuple([]))
        shsv__qfd = dict(raw=kvu__fhval, result_type=fvbrl__kkmku)
        jvie__gqiq = dict(raw=False, result_type=None)
        check_unsupported_args('Dataframe.apply', shsv__qfd, jvie__gqiq,
            package_name='pandas', module_name='DataFrame')
        aag__bsj = True
        if types.unliteral(qww__zbj) == types.unicode_type:
            if not is_overload_constant_str(qww__zbj):
                raise BodoError(
                    f'DataFrame.apply(): string argument (for builtins) must be a compile time constant'
                    )
            aag__bsj = False
        if not is_overload_constant_int(axis):
            raise BodoError(
                'Dataframe.apply(): axis argument must be a compile time constant.'
                )
        rvw__cfmqz = get_overload_const_int(axis)
        if aag__bsj and rvw__cfmqz != 1:
            raise BodoError(
                'Dataframe.apply(): only axis=1 supported for user-defined functions'
                )
        elif rvw__cfmqz not in (0, 1):
            raise BodoError('Dataframe.apply(): axis must be either 0 or 1')
        qymzh__dlop = []
        for arr_typ in df.data:
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(arr_typ,
                'DataFrame.apply()')
            xjs__rjf = SeriesType(arr_typ.dtype, arr_typ, df.index, string_type
                )
            ouh__cyc = self.context.resolve_function_type(operator.getitem,
                (SeriesIlocType(xjs__rjf), types.int64), {}).return_type
            qymzh__dlop.append(ouh__cyc)
        ahd__tvad = types.none
        trozu__wge = HeterogeneousIndexType(types.BaseTuple.from_types(
            tuple(types.literal(htcp__ynkuq) for htcp__ynkuq in df.columns)
            ), None)
        vxvf__sidby = types.BaseTuple.from_types(qymzh__dlop)
        yqz__rmhmu = df.index.dtype
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df.index,
            'DataFrame.apply()')
        if yqz__rmhmu == types.NPDatetime('ns'):
            yqz__rmhmu = bodo.pd_timestamp_type
        if yqz__rmhmu == types.NPTimedelta('ns'):
            yqz__rmhmu = bodo.pd_timedelta_type
        if is_heterogeneous_tuple_type(vxvf__sidby):
            zzv__eet = HeterogeneousSeriesType(vxvf__sidby, trozu__wge,
                yqz__rmhmu)
        else:
            zzv__eet = SeriesType(vxvf__sidby.dtype, vxvf__sidby,
                trozu__wge, yqz__rmhmu)
        nos__wnq = zzv__eet,
        if ssr__wfr is not None:
            nos__wnq += tuple(ssr__wfr.types)
        try:
            if not aag__bsj:
                gvk__iiran = bodo.utils.transform.get_udf_str_return_type(df,
                    get_overload_const_str(qww__zbj), self.context,
                    'DataFrame.apply', axis if rvw__cfmqz == 1 else None)
            else:
                gvk__iiran = get_const_func_output_type(qww__zbj, nos__wnq,
                    kws, self.context, numba.core.registry.cpu_target.
                    target_context)
        except Exception as wupt__ovq:
            raise_bodo_error(get_udf_error_msg('DataFrame.apply()', wupt__ovq))
        if aag__bsj:
            if not (is_overload_constant_int(axis) and 
                get_overload_const_int(axis) == 1):
                raise BodoError(
                    'Dataframe.apply(): only user-defined functions with axis=1 supported'
                    )
            if isinstance(gvk__iiran, (SeriesType, HeterogeneousSeriesType)
                ) and gvk__iiran.const_info is None:
                raise BodoError(
                    'Invalid Series output in UDF (Series with constant length and constant Index value expected)'
                    )
            if isinstance(gvk__iiran, HeterogeneousSeriesType):
                rbufs__ufq, prwje__ttxu = gvk__iiran.const_info
                tkjx__ntlt = tuple(dtype_to_array_type(adafk__lpo) for
                    adafk__lpo in gvk__iiran.data.types)
                ngv__gaara = DataFrameType(tkjx__ntlt, df.index, prwje__ttxu)
            elif isinstance(gvk__iiran, SeriesType):
                apbut__caxw, prwje__ttxu = gvk__iiran.const_info
                tkjx__ntlt = tuple(dtype_to_array_type(gvk__iiran.dtype) for
                    rbufs__ufq in range(apbut__caxw))
                ngv__gaara = DataFrameType(tkjx__ntlt, df.index, prwje__ttxu)
            else:
                gap__bdqzd = get_udf_out_arr_type(gvk__iiran)
                ngv__gaara = SeriesType(gap__bdqzd.dtype, gap__bdqzd, df.
                    index, None)
        else:
            ngv__gaara = gvk__iiran
        clfpn__gjc = ', '.join("{} = ''".format(aqhan__xmu) for aqhan__xmu in
            kws.keys())
        zlyfx__nnvh = f"""def apply_stub(func, axis=0, raw=False, result_type=None, args=(), {clfpn__gjc}):
"""
        zlyfx__nnvh += '    pass\n'
        dsp__znd = {}
        exec(zlyfx__nnvh, {}, dsp__znd)
        enf__qixlg = dsp__znd['apply_stub']
        pfvhw__mryrj = numba.core.utils.pysignature(enf__qixlg)
        tvb__sim = (qww__zbj, axis, kvu__fhval, fvbrl__kkmku, ssr__wfr
            ) + tuple(kws.values())
        return signature(ngv__gaara, *tvb__sim).replace(pysig=pfvhw__mryrj)

    @bound_function('df.plot', no_unliteral=True)
    def resolve_plot(self, df, args, kws):
        func_name = 'DataFrame.plot'
        check_runtime_cols_unsupported(df, f'{func_name}()')
        lxwly__gwjon = ('x', 'y', 'kind', 'figsize', 'ax', 'subplots',
            'sharex', 'sharey', 'layout', 'use_index', 'title', 'grid',
            'legend', 'style', 'logx', 'logy', 'loglog', 'xticks', 'yticks',
            'xlim', 'ylim', 'rot', 'fontsize', 'colormap', 'table', 'yerr',
            'xerr', 'secondary_y', 'sort_columns', 'xlabel', 'ylabel',
            'position', 'stacked', 'mark_right', 'include_bool', 'backend')
        glui__gec = {'x': None, 'y': None, 'kind': 'line', 'figsize': None,
            'ax': None, 'subplots': False, 'sharex': None, 'sharey': False,
            'layout': None, 'use_index': True, 'title': None, 'grid': None,
            'legend': True, 'style': None, 'logx': False, 'logy': False,
            'loglog': False, 'xticks': None, 'yticks': None, 'xlim': None,
            'ylim': None, 'rot': None, 'fontsize': None, 'colormap': None,
            'table': False, 'yerr': None, 'xerr': None, 'secondary_y': 
            False, 'sort_columns': False, 'xlabel': None, 'ylabel': None,
            'position': 0.5, 'stacked': False, 'mark_right': True,
            'include_bool': False, 'backend': None}
        jqf__psy = ('subplots', 'sharex', 'sharey', 'layout', 'use_index',
            'grid', 'style', 'logx', 'logy', 'loglog', 'xlim', 'ylim',
            'rot', 'colormap', 'table', 'yerr', 'xerr', 'sort_columns',
            'secondary_y', 'colorbar', 'position', 'stacked', 'mark_right',
            'include_bool', 'backend')
        pfvhw__mryrj, yblhw__ezwc = bodo.utils.typing.fold_typing_args(
            func_name, args, kws, lxwly__gwjon, glui__gec, jqf__psy)
        fvcye__mbg = yblhw__ezwc[2]
        if not is_overload_constant_str(fvcye__mbg):
            raise BodoError(
                f"{func_name}: kind must be a constant string and one of ('line', 'scatter')."
                )
        qfm__xqsb = yblhw__ezwc[0]
        if not is_overload_none(qfm__xqsb) and not (is_overload_int(
            qfm__xqsb) or is_overload_constant_str(qfm__xqsb)):
            raise BodoError(
                f'{func_name}: x must be a constant column name, constant integer, or None.'
                )
        if is_overload_constant_str(qfm__xqsb):
            ifhl__lltiu = get_overload_const_str(qfm__xqsb)
            if ifhl__lltiu not in df.columns:
                raise BodoError(f'{func_name}: {ifhl__lltiu} column not found.'
                    )
        elif is_overload_int(qfm__xqsb):
            gszuf__blay = get_overload_const_int(qfm__xqsb)
            if gszuf__blay > len(df.columns):
                raise BodoError(
                    f'{func_name}: x: {gszuf__blay} is out of bounds for axis 0 with size {len(df.columns)}'
                    )
            qfm__xqsb = df.columns[qfm__xqsb]
        fxiw__zvkfk = yblhw__ezwc[1]
        if not is_overload_none(fxiw__zvkfk) and not (is_overload_int(
            fxiw__zvkfk) or is_overload_constant_str(fxiw__zvkfk)):
            raise BodoError(
                'df.plot(): y must be a constant column name, constant integer, or None.'
                )
        if is_overload_constant_str(fxiw__zvkfk):
            jjc__wavr = get_overload_const_str(fxiw__zvkfk)
            if jjc__wavr not in df.columns:
                raise BodoError(f'{func_name}: {jjc__wavr} column not found.')
        elif is_overload_int(fxiw__zvkfk):
            gxtaw__bty = get_overload_const_int(fxiw__zvkfk)
            if gxtaw__bty > len(df.columns):
                raise BodoError(
                    f'{func_name}: y: {gxtaw__bty} is out of bounds for axis 0 with size {len(df.columns)}'
                    )
            fxiw__zvkfk = df.columns[fxiw__zvkfk]
        ydyyi__aavm = yblhw__ezwc[3]
        if not is_overload_none(ydyyi__aavm) and not is_tuple_like_type(
            ydyyi__aavm):
            raise BodoError(
                f'{func_name}: figsize must be a constant numeric tuple (width, height) or None.'
                )
        eokr__bqkkh = yblhw__ezwc[10]
        if not is_overload_none(eokr__bqkkh) and not is_overload_constant_str(
            eokr__bqkkh):
            raise BodoError(
                f'{func_name}: title must be a constant string or None.')
        rlrwv__pdywb = yblhw__ezwc[12]
        if not is_overload_bool(rlrwv__pdywb):
            raise BodoError(f'{func_name}: legend must be a boolean type.')
        ody__okr = yblhw__ezwc[17]
        if not is_overload_none(ody__okr) and not is_tuple_like_type(ody__okr):
            raise BodoError(
                f'{func_name}: xticks must be a constant tuple or None.')
        rtbo__xpmo = yblhw__ezwc[18]
        if not is_overload_none(rtbo__xpmo) and not is_tuple_like_type(
            rtbo__xpmo):
            raise BodoError(
                f'{func_name}: yticks must be a constant tuple or None.')
        wtwph__dlht = yblhw__ezwc[22]
        if not is_overload_none(wtwph__dlht) and not is_overload_int(
            wtwph__dlht):
            raise BodoError(
                f'{func_name}: fontsize must be an integer or None.')
        bpr__fxk = yblhw__ezwc[29]
        if not is_overload_none(bpr__fxk) and not is_overload_constant_str(
            bpr__fxk):
            raise BodoError(
                f'{func_name}: xlabel must be a constant string or None.')
        fzcvh__aoggp = yblhw__ezwc[30]
        if not is_overload_none(fzcvh__aoggp) and not is_overload_constant_str(
            fzcvh__aoggp):
            raise BodoError(
                f'{func_name}: ylabel must be a constant string or None.')
        soy__iyx = types.List(types.mpl_line_2d_type)
        fvcye__mbg = get_overload_const_str(fvcye__mbg)
        if fvcye__mbg == 'scatter':
            if is_overload_none(qfm__xqsb) and is_overload_none(fxiw__zvkfk):
                raise BodoError(
                    f'{func_name}: {fvcye__mbg} requires an x and y column.')
            elif is_overload_none(qfm__xqsb):
                raise BodoError(
                    f'{func_name}: {fvcye__mbg} x column is missing.')
            elif is_overload_none(fxiw__zvkfk):
                raise BodoError(
                    f'{func_name}: {fvcye__mbg} y column is missing.')
            soy__iyx = types.mpl_path_collection_type
        elif fvcye__mbg != 'line':
            raise BodoError(f'{func_name}: {fvcye__mbg} plot is not supported.'
                )
        return signature(soy__iyx, *yblhw__ezwc).replace(pysig=pfvhw__mryrj)

    def generic_resolve(self, df, attr):
        if self._is_existing_attr(attr):
            return
        check_runtime_cols_unsupported(df,
            'Acessing DataFrame columns by attribute')
        if attr in df.columns:
            enpxb__xuft = df.columns.index(attr)
            arr_typ = df.data[enpxb__xuft]
            return SeriesType(arr_typ.dtype, arr_typ, df.index, types.
                StringLiteral(attr))
        if len(df.columns) > 0 and isinstance(df.columns[0], tuple):
            lldmp__xqvxm = []
            ybhd__uzmp = []
            pmef__nrv = False
            for i, qqfu__nsz in enumerate(df.columns):
                if qqfu__nsz[0] != attr:
                    continue
                pmef__nrv = True
                lldmp__xqvxm.append(qqfu__nsz[1] if len(qqfu__nsz) == 2 else
                    qqfu__nsz[1:])
                ybhd__uzmp.append(df.data[i])
            if pmef__nrv:
                return DataFrameType(tuple(ybhd__uzmp), df.index, tuple(
                    lldmp__xqvxm))


DataFrameAttribute._no_unliteral = True


@overload(operator.getitem, no_unliteral=True)
def namedtuple_getitem_overload(tup, idx):
    if isinstance(tup, types.BaseNamedTuple) and is_overload_constant_str(idx):
        jiagx__pcona = get_overload_const_str(idx)
        val_ind = tup.instance_class._fields.index(jiagx__pcona)
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
        jhez__evp = builder.extract_value(payload.data, i)
        context.nrt.decref(builder, df_type.data[i], jhez__evp)
    context.nrt.decref(builder, df_type.index, payload.index)


def define_df_dtor(context, builder, df_type, payload_type):
    daceg__givvs = builder.module
    xocl__nnq = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    moxxg__tczg = cgutils.get_or_insert_function(daceg__givvs, xocl__nnq,
        name='.dtor.df.{}'.format(df_type))
    if not moxxg__tczg.is_declaration:
        return moxxg__tczg
    moxxg__tczg.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(moxxg__tczg.append_basic_block())
    redi__smdu = moxxg__tczg.args[0]
    kvig__cxm = context.get_value_type(payload_type).as_pointer()
    iayc__exq = builder.bitcast(redi__smdu, kvig__cxm)
    payload = context.make_helper(builder, payload_type, ref=iayc__exq)
    decref_df_data(context, builder, payload, df_type)
    has_parent = cgutils.is_not_null(builder, payload.parent)
    with builder.if_then(has_parent):
        jdjvx__luaf = context.get_python_api(builder)
        kkb__lhncy = jdjvx__luaf.gil_ensure()
        jdjvx__luaf.decref(payload.parent)
        jdjvx__luaf.gil_release(kkb__lhncy)
    builder.ret_void()
    return moxxg__tczg


def construct_dataframe(context, builder, df_type, data_tup, index_val,
    parent=None, colnames=None):
    payload_type = DataFramePayloadType(df_type)
    yxag__rgk = cgutils.create_struct_proxy(payload_type)(context, builder)
    yxag__rgk.data = data_tup
    yxag__rgk.index = index_val
    if colnames is not None:
        assert df_type.has_runtime_cols, 'construct_dataframe can only provide colnames if columns are determined at runtime'
        yxag__rgk.columns = colnames
    mvl__lfcjl = context.get_value_type(payload_type)
    zfyuk__dxalr = context.get_abi_sizeof(mvl__lfcjl)
    qzhz__kbmam = define_df_dtor(context, builder, df_type, payload_type)
    idfrd__xfmvt = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, zfyuk__dxalr), qzhz__kbmam)
    ryn__kedx = context.nrt.meminfo_data(builder, idfrd__xfmvt)
    esrlg__cyps = builder.bitcast(ryn__kedx, mvl__lfcjl.as_pointer())
    rkavi__nodb = cgutils.create_struct_proxy(df_type)(context, builder)
    rkavi__nodb.meminfo = idfrd__xfmvt
    if parent is None:
        rkavi__nodb.parent = cgutils.get_null_value(rkavi__nodb.parent.type)
    else:
        rkavi__nodb.parent = parent
        yxag__rgk.parent = parent
        has_parent = cgutils.is_not_null(builder, parent)
        with builder.if_then(has_parent):
            jdjvx__luaf = context.get_python_api(builder)
            kkb__lhncy = jdjvx__luaf.gil_ensure()
            jdjvx__luaf.incref(parent)
            jdjvx__luaf.gil_release(kkb__lhncy)
    builder.store(yxag__rgk._getvalue(), esrlg__cyps)
    return rkavi__nodb._getvalue()


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
        ugg__popv = [data_typ.dtype.arr_types.dtype] * len(data_typ.dtype.
            arr_types)
    else:
        ugg__popv = [adafk__lpo for adafk__lpo in data_typ.dtype.arr_types]
    eaao__nns = DataFrameType(tuple(ugg__popv + [colnames_index_typ]),
        index_typ, None, is_table_format=True)

    def codegen(context, builder, signature, args):
        df_type = signature.return_type
        data_tup, index, col_names = args
        parent = None
        gnim__rxui = construct_dataframe(context, builder, df_type,
            data_tup, index, parent, col_names)
        context.nrt.incref(builder, data_typ, data_tup)
        context.nrt.incref(builder, index_typ, index)
        context.nrt.incref(builder, colnames_index_typ, col_names)
        return gnim__rxui
    sig = signature(eaao__nns, data_typ, index_typ, colnames_index_typ)
    return sig, codegen


@intrinsic
def init_dataframe(typingctx, data_tup_typ, index_typ, col_names_typ=None):
    assert is_pd_index_type(index_typ) or isinstance(index_typ, MultiIndexType
        ), 'init_dataframe(): invalid index type'
    apbut__caxw = len(data_tup_typ.types)
    if apbut__caxw == 0:
        column_names = ()
    elif isinstance(col_names_typ, types.TypeRef):
        column_names = col_names_typ.instance_type.columns
    else:
        column_names = get_const_tup_vals(col_names_typ)
    if apbut__caxw == 1 and isinstance(data_tup_typ.types[0], TableType):
        apbut__caxw = len(data_tup_typ.types[0].arr_types)
    assert len(column_names
        ) == apbut__caxw, 'init_dataframe(): number of column names does not match number of columns'
    is_table_format = False
    fqscq__gwv = data_tup_typ.types
    if apbut__caxw != 0 and isinstance(data_tup_typ.types[0], TableType):
        fqscq__gwv = data_tup_typ.types[0].arr_types
        is_table_format = True
    eaao__nns = DataFrameType(fqscq__gwv, index_typ, column_names,
        is_table_format=is_table_format)

    def codegen(context, builder, signature, args):
        df_type = signature.return_type
        data_tup = args[0]
        index_val = args[1]
        parent = None
        if is_table_format:
            jru__qrtzx = cgutils.create_struct_proxy(eaao__nns.table_type)(
                context, builder, builder.extract_value(data_tup, 0))
            parent = jru__qrtzx.parent
        gnim__rxui = construct_dataframe(context, builder, df_type,
            data_tup, index_val, parent, None)
        context.nrt.incref(builder, data_tup_typ, data_tup)
        context.nrt.incref(builder, index_typ, index_val)
        return gnim__rxui
    sig = signature(eaao__nns, data_tup_typ, index_typ, col_names_typ)
    return sig, codegen


@intrinsic
def has_parent(typingctx, df=None):
    check_runtime_cols_unsupported(df, 'has_parent')

    def codegen(context, builder, sig, args):
        rkavi__nodb = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        return cgutils.is_not_null(builder, rkavi__nodb.parent)
    return signature(types.bool_, df), codegen


@intrinsic
def _column_needs_unboxing(typingctx, df_typ, i_typ=None):
    check_runtime_cols_unsupported(df_typ, '_column_needs_unboxing')
    assert isinstance(df_typ, DataFrameType) and is_overload_constant_int(i_typ
        )

    def codegen(context, builder, sig, args):
        yxag__rgk = get_dataframe_payload(context, builder, df_typ, args[0])
        hfmbg__uezxg = get_overload_const_int(i_typ)
        arr_typ = df_typ.data[hfmbg__uezxg]
        if df_typ.is_table_format:
            jru__qrtzx = cgutils.create_struct_proxy(df_typ.table_type)(context
                , builder, builder.extract_value(yxag__rgk.data, 0))
            emvr__nfisz = df_typ.table_type.type_to_blk[arr_typ]
            uabh__bdvp = getattr(jru__qrtzx, f'block_{emvr__nfisz}')
            vllre__xzwpp = ListInstance(context, builder, types.List(
                arr_typ), uabh__bdvp)
            wnfw__icns = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[hfmbg__uezxg])
            jhez__evp = vllre__xzwpp.getitem(wnfw__icns)
        else:
            jhez__evp = builder.extract_value(yxag__rgk.data, hfmbg__uezxg)
        cqds__pnd = cgutils.alloca_once_value(builder, jhez__evp)
        bkni__kmdzc = cgutils.alloca_once_value(builder, context.
            get_constant_null(arr_typ))
        return is_ll_eq(builder, cqds__pnd, bkni__kmdzc)
    return signature(types.bool_, df_typ, i_typ), codegen


def get_dataframe_payload(context, builder, df_type, value):
    idfrd__xfmvt = cgutils.create_struct_proxy(df_type)(context, builder, value
        ).meminfo
    payload_type = DataFramePayloadType(df_type)
    payload = context.nrt.meminfo_data(builder, idfrd__xfmvt)
    kvig__cxm = context.get_value_type(payload_type).as_pointer()
    payload = builder.bitcast(payload, kvig__cxm)
    return context.make_helper(builder, payload_type, ref=payload)


@intrinsic
def _get_dataframe_data(typingctx, df_typ=None):
    check_runtime_cols_unsupported(df_typ, '_get_dataframe_data')
    eaao__nns = types.Tuple(df_typ.data)
    if df_typ.is_table_format:
        eaao__nns = types.Tuple([TableType(df_typ.data)])
    sig = signature(eaao__nns, df_typ)

    def codegen(context, builder, signature, args):
        yxag__rgk = get_dataframe_payload(context, builder, signature.args[
            0], args[0])
        return impl_ret_borrowed(context, builder, signature.return_type,
            yxag__rgk.data)
    return sig, codegen


@intrinsic
def get_dataframe_index(typingctx, df_typ=None):

    def codegen(context, builder, signature, args):
        yxag__rgk = get_dataframe_payload(context, builder, signature.args[
            0], args[0])
        return impl_ret_borrowed(context, builder, df_typ.index, yxag__rgk.
            index)
    eaao__nns = df_typ.index
    sig = signature(eaao__nns, df_typ)
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
        qzs__grqmr = df.data[i]
        return qzs__grqmr(*args)


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
        yxag__rgk = get_dataframe_payload(context, builder, signature.args[
            0], args[0])
        return impl_ret_borrowed(context, builder, df_typ.table_type,
            builder.extract_value(yxag__rgk.data, 0))
    return df_typ.table_type(df_typ), codegen


@intrinsic
def get_dataframe_column_names(typingctx, df_typ=None):
    assert df_typ.has_runtime_cols, 'get_dataframe_column_names() expects columns to be determined at runtime'

    def codegen(context, builder, signature, args):
        yxag__rgk = get_dataframe_payload(context, builder, signature.args[
            0], args[0])
        return impl_ret_borrowed(context, builder, df_typ.
            runtime_colname_typ, yxag__rgk.columns)
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
    vxvf__sidby = self.typemap[data_tup.name]
    if any(is_tuple_like_type(adafk__lpo) for adafk__lpo in vxvf__sidby.types):
        return None
    if equiv_set.has_shape(data_tup):
        oayiw__zsylo = equiv_set.get_shape(data_tup)
        if len(oayiw__zsylo) > 1:
            equiv_set.insert_equiv(*oayiw__zsylo)
        if len(oayiw__zsylo) > 0:
            trozu__wge = self.typemap[index.name]
            if not isinstance(trozu__wge, HeterogeneousIndexType
                ) and equiv_set.has_shape(index):
                equiv_set.insert_equiv(oayiw__zsylo[0], index)
            return ArrayAnalysis.AnalyzeResult(shape=(oayiw__zsylo[0], len(
                oayiw__zsylo)), pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_dataframe_ext_init_dataframe
    ) = init_dataframe_equiv


def get_dataframe_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    aqs__nbwxh = args[0]
    data_types = self.typemap[aqs__nbwxh.name].data
    if any(is_tuple_like_type(adafk__lpo) for adafk__lpo in data_types):
        return None
    if equiv_set.has_shape(aqs__nbwxh):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            aqs__nbwxh)[0], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_data
    ) = get_dataframe_data_equiv


def get_dataframe_index_equiv(self, scope, equiv_set, loc, args, kws):
    from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
    assert len(args) == 1 and not kws
    aqs__nbwxh = args[0]
    trozu__wge = self.typemap[aqs__nbwxh.name].index
    if isinstance(trozu__wge, HeterogeneousIndexType):
        return None
    if equiv_set.has_shape(aqs__nbwxh):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            aqs__nbwxh)[0], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_index
    ) = get_dataframe_index_equiv


def get_dataframe_table_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    aqs__nbwxh = args[0]
    if equiv_set.has_shape(aqs__nbwxh):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            aqs__nbwxh), pre=[])


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_table
    ) = get_dataframe_table_equiv


def get_dataframe_column_names_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    aqs__nbwxh = args[0]
    if equiv_set.has_shape(aqs__nbwxh):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            aqs__nbwxh)[1], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_column_names
    ) = get_dataframe_column_names_equiv


@intrinsic
def set_dataframe_data(typingctx, df_typ, c_ind_typ, arr_typ=None):
    check_runtime_cols_unsupported(df_typ, 'set_dataframe_data')
    assert is_overload_constant_int(c_ind_typ)
    hfmbg__uezxg = get_overload_const_int(c_ind_typ)
    if df_typ.data[hfmbg__uezxg] != arr_typ:
        raise BodoError(
            'Changing dataframe column data type inplace is not supported in conditionals/loops or for dataframe arguments'
            )

    def codegen(context, builder, signature, args):
        yry__utfz, rbufs__ufq, usldy__lspa = args
        yxag__rgk = get_dataframe_payload(context, builder, df_typ, yry__utfz)
        if df_typ.is_table_format:
            jru__qrtzx = cgutils.create_struct_proxy(df_typ.table_type)(context
                , builder, builder.extract_value(yxag__rgk.data, 0))
            emvr__nfisz = df_typ.table_type.type_to_blk[arr_typ]
            uabh__bdvp = getattr(jru__qrtzx, f'block_{emvr__nfisz}')
            vllre__xzwpp = ListInstance(context, builder, types.List(
                arr_typ), uabh__bdvp)
            wnfw__icns = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[hfmbg__uezxg])
            vllre__xzwpp.setitem(wnfw__icns, usldy__lspa, True)
        else:
            jhez__evp = builder.extract_value(yxag__rgk.data, hfmbg__uezxg)
            context.nrt.decref(builder, df_typ.data[hfmbg__uezxg], jhez__evp)
            yxag__rgk.data = builder.insert_value(yxag__rgk.data,
                usldy__lspa, hfmbg__uezxg)
            context.nrt.incref(builder, arr_typ, usldy__lspa)
        rkavi__nodb = cgutils.create_struct_proxy(df_typ)(context, builder,
            value=yry__utfz)
        payload_type = DataFramePayloadType(df_typ)
        iayc__exq = context.nrt.meminfo_data(builder, rkavi__nodb.meminfo)
        kvig__cxm = context.get_value_type(payload_type).as_pointer()
        iayc__exq = builder.bitcast(iayc__exq, kvig__cxm)
        builder.store(yxag__rgk._getvalue(), iayc__exq)
        return impl_ret_borrowed(context, builder, df_typ, yry__utfz)
    sig = signature(df_typ, df_typ, c_ind_typ, arr_typ)
    return sig, codegen


@intrinsic
def set_df_index(typingctx, df_t, index_t=None):
    check_runtime_cols_unsupported(df_t, 'set_df_index')

    def codegen(context, builder, signature, args):
        pmg__ttamq = args[0]
        index_val = args[1]
        df_typ = signature.args[0]
        npur__flv = cgutils.create_struct_proxy(df_typ)(context, builder,
            value=pmg__ttamq)
        wyorq__thg = get_dataframe_payload(context, builder, df_typ, pmg__ttamq
            )
        rkavi__nodb = construct_dataframe(context, builder, signature.
            return_type, wyorq__thg.data, index_val, npur__flv.parent, None)
        context.nrt.incref(builder, index_t, index_val)
        context.nrt.incref(builder, types.Tuple(df_t.data), wyorq__thg.data)
        return rkavi__nodb
    eaao__nns = DataFrameType(df_t.data, index_t, df_t.columns, df_t.dist,
        df_t.is_table_format)
    sig = signature(eaao__nns, df_t, index_t)
    return sig, codegen


@intrinsic
def set_df_column_with_reflect(typingctx, df_type, cname_type, arr_type=None):
    check_runtime_cols_unsupported(df_type, 'set_df_column_with_reflect')
    assert is_literal_type(cname_type), 'constant column name expected'
    col_name = get_literal_value(cname_type)
    apbut__caxw = len(df_type.columns)
    tqez__eqy = apbut__caxw
    kkj__rwoko = df_type.data
    column_names = df_type.columns
    index_typ = df_type.index
    fmska__yajm = col_name not in df_type.columns
    hfmbg__uezxg = apbut__caxw
    if fmska__yajm:
        kkj__rwoko += arr_type,
        column_names += col_name,
        tqez__eqy += 1
    else:
        hfmbg__uezxg = df_type.columns.index(col_name)
        kkj__rwoko = tuple(arr_type if i == hfmbg__uezxg else kkj__rwoko[i] for
            i in range(apbut__caxw))

    def codegen(context, builder, signature, args):
        yry__utfz, rbufs__ufq, usldy__lspa = args
        in_dataframe_payload = get_dataframe_payload(context, builder,
            df_type, yry__utfz)
        bnnoh__sxhxt = cgutils.create_struct_proxy(df_type)(context,
            builder, value=yry__utfz)
        if df_type.is_table_format:
            vjzj__ouuze = df_type.table_type
            odscq__fpa = builder.extract_value(in_dataframe_payload.data, 0)
            kpw__yraz = TableType(kkj__rwoko)
            mskfk__kpg = set_table_data_codegen(context, builder,
                vjzj__ouuze, odscq__fpa, kpw__yraz, arr_type, usldy__lspa,
                hfmbg__uezxg, fmska__yajm)
            data_tup = context.make_tuple(builder, types.Tuple([kpw__yraz]),
                [mskfk__kpg])
        else:
            fqscq__gwv = [(builder.extract_value(in_dataframe_payload.data,
                i) if i != hfmbg__uezxg else usldy__lspa) for i in range(
                apbut__caxw)]
            if fmska__yajm:
                fqscq__gwv.append(usldy__lspa)
            for aqs__nbwxh, gjl__ewvh in zip(fqscq__gwv, kkj__rwoko):
                context.nrt.incref(builder, gjl__ewvh, aqs__nbwxh)
            data_tup = context.make_tuple(builder, types.Tuple(kkj__rwoko),
                fqscq__gwv)
        index_val = in_dataframe_payload.index
        context.nrt.incref(builder, index_typ, index_val)
        zadt__qneg = construct_dataframe(context, builder, signature.
            return_type, data_tup, index_val, bnnoh__sxhxt.parent, None)
        if not fmska__yajm and arr_type == df_type.data[hfmbg__uezxg]:
            decref_df_data(context, builder, in_dataframe_payload, df_type)
            payload_type = DataFramePayloadType(df_type)
            iayc__exq = context.nrt.meminfo_data(builder, bnnoh__sxhxt.meminfo)
            kvig__cxm = context.get_value_type(payload_type).as_pointer()
            iayc__exq = builder.bitcast(iayc__exq, kvig__cxm)
            yroc__ecw = get_dataframe_payload(context, builder, df_type,
                zadt__qneg)
            builder.store(yroc__ecw._getvalue(), iayc__exq)
            context.nrt.incref(builder, index_typ, index_val)
            if df_type.is_table_format:
                context.nrt.incref(builder, kpw__yraz, builder.
                    extract_value(data_tup, 0))
            else:
                for aqs__nbwxh, gjl__ewvh in zip(fqscq__gwv, kkj__rwoko):
                    context.nrt.incref(builder, gjl__ewvh, aqs__nbwxh)
        has_parent = cgutils.is_not_null(builder, bnnoh__sxhxt.parent)
        with builder.if_then(has_parent):
            jdjvx__luaf = context.get_python_api(builder)
            kkb__lhncy = jdjvx__luaf.gil_ensure()
            zbid__snl = context.get_env_manager(builder)
            context.nrt.incref(builder, arr_type, usldy__lspa)
            htcp__ynkuq = numba.core.pythonapi._BoxContext(context, builder,
                jdjvx__luaf, zbid__snl)
            lmkv__bbeqp = htcp__ynkuq.pyapi.from_native_value(arr_type,
                usldy__lspa, htcp__ynkuq.env_manager)
            if isinstance(col_name, str):
                weobv__nrm = context.insert_const_string(builder.module,
                    col_name)
                ddi__nmsg = jdjvx__luaf.string_from_string(weobv__nrm)
            else:
                assert isinstance(col_name, int)
                ddi__nmsg = jdjvx__luaf.long_from_longlong(context.
                    get_constant(types.intp, col_name))
            jdjvx__luaf.object_setitem(bnnoh__sxhxt.parent, ddi__nmsg,
                lmkv__bbeqp)
            jdjvx__luaf.decref(lmkv__bbeqp)
            jdjvx__luaf.decref(ddi__nmsg)
            jdjvx__luaf.gil_release(kkb__lhncy)
        return zadt__qneg
    eaao__nns = DataFrameType(kkj__rwoko, index_typ, column_names, df_type.
        dist, df_type.is_table_format)
    sig = signature(eaao__nns, df_type, cname_type, arr_type)
    return sig, codegen


@lower_constant(DataFrameType)
def lower_constant_dataframe(context, builder, df_type, pyval):
    check_runtime_cols_unsupported(df_type, 'lowering a constant DataFrame')
    apbut__caxw = len(pyval.columns)
    fqscq__gwv = []
    for i in range(apbut__caxw):
        wruo__kdlu = pyval.iloc[:, i]
        if isinstance(df_type.data[i], bodo.DatetimeArrayType):
            lmkv__bbeqp = wruo__kdlu.array
        else:
            lmkv__bbeqp = wruo__kdlu.values
        fqscq__gwv.append(lmkv__bbeqp)
    fqscq__gwv = tuple(fqscq__gwv)
    if df_type.is_table_format:
        jru__qrtzx = context.get_constant_generic(builder, df_type.
            table_type, Table(fqscq__gwv))
        data_tup = lir.Constant.literal_struct([jru__qrtzx])
    else:
        data_tup = lir.Constant.literal_struct([context.
            get_constant_generic(builder, df_type.data[i], qqfu__nsz) for i,
            qqfu__nsz in enumerate(fqscq__gwv)])
    index_val = context.get_constant_generic(builder, df_type.index, pyval.
        index)
    uerw__wkel = context.get_constant_null(types.pyobject)
    payload = lir.Constant.literal_struct([data_tup, index_val, uerw__wkel])
    payload = cgutils.global_constant(builder, '.const.payload', payload
        ).bitcast(cgutils.voidptr_t)
    prlbh__qzoo = context.get_constant(types.int64, -1)
    hwvk__htxo = context.get_constant_null(types.voidptr)
    idfrd__xfmvt = lir.Constant.literal_struct([prlbh__qzoo, hwvk__htxo,
        hwvk__htxo, payload, prlbh__qzoo])
    idfrd__xfmvt = cgutils.global_constant(builder, '.const.meminfo',
        idfrd__xfmvt).bitcast(cgutils.voidptr_t)
    return lir.Constant.literal_struct([idfrd__xfmvt, uerw__wkel])


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
        qoxpz__rrbkr = context.cast(builder, in_dataframe_payload.index,
            fromty.index, toty.index)
    else:
        qoxpz__rrbkr = in_dataframe_payload.index
        context.nrt.incref(builder, fromty.index, qoxpz__rrbkr)
    if (fromty.is_table_format == toty.is_table_format and fromty.data ==
        toty.data):
        ybhd__uzmp = in_dataframe_payload.data
        if fromty.is_table_format:
            context.nrt.incref(builder, types.Tuple([fromty.table_type]),
                ybhd__uzmp)
        else:
            context.nrt.incref(builder, types.BaseTuple.from_types(fromty.
                data), ybhd__uzmp)
    elif not fromty.is_table_format and toty.is_table_format:
        ybhd__uzmp = _cast_df_data_to_table_format(context, builder, fromty,
            toty, val, in_dataframe_payload)
    elif fromty.is_table_format and not toty.is_table_format:
        ybhd__uzmp = _cast_df_data_to_tuple_format(context, builder, fromty,
            toty, val, in_dataframe_payload)
    elif fromty.is_table_format and toty.is_table_format:
        ybhd__uzmp = _cast_df_data_keep_table_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    else:
        ybhd__uzmp = _cast_df_data_keep_tuple_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    return construct_dataframe(context, builder, toty, ybhd__uzmp,
        qoxpz__rrbkr, in_dataframe_payload.parent, None)


def _cast_empty_df(context, builder, toty):
    ivrjx__tbo = {}
    if isinstance(toty.index, RangeIndexType):
        index = 'bodo.hiframes.pd_index_ext.init_range_index(0, 0, 1, None)'
    else:
        vbum__bzou = get_index_data_arr_types(toty.index)[0]
        bia__xifb = bodo.utils.transform.get_type_alloc_counts(vbum__bzou) - 1
        kijz__vbk = ', '.join('0' for rbufs__ufq in range(bia__xifb))
        index = (
            'bodo.utils.conversion.index_from_array(bodo.utils.utils.alloc_type(0, index_arr_type, ({}{})))'
            .format(kijz__vbk, ', ' if bia__xifb == 1 else ''))
        ivrjx__tbo['index_arr_type'] = vbum__bzou
    zpla__lztor = []
    for i, arr_typ in enumerate(toty.data):
        bia__xifb = bodo.utils.transform.get_type_alloc_counts(arr_typ) - 1
        kijz__vbk = ', '.join('0' for rbufs__ufq in range(bia__xifb))
        tcqq__ngi = ('bodo.utils.utils.alloc_type(0, arr_type{}, ({}{}))'.
            format(i, kijz__vbk, ', ' if bia__xifb == 1 else ''))
        zpla__lztor.append(tcqq__ngi)
        ivrjx__tbo[f'arr_type{i}'] = arr_typ
    zpla__lztor = ', '.join(zpla__lztor)
    zlyfx__nnvh = 'def impl():\n'
    kizmb__ebnkg = bodo.hiframes.dataframe_impl._gen_init_df(zlyfx__nnvh,
        toty.columns, zpla__lztor, index, ivrjx__tbo)
    df = context.compile_internal(builder, kizmb__ebnkg, toty(), [])
    return df


def _cast_df_data_to_table_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting traditional DataFrame to table format')
    xsnko__sklv = toty.table_type
    jru__qrtzx = cgutils.create_struct_proxy(xsnko__sklv)(context, builder)
    jru__qrtzx.parent = in_dataframe_payload.parent
    for adafk__lpo, emvr__nfisz in xsnko__sklv.type_to_blk.items():
        vhb__hdfex = context.get_constant(types.int64, len(xsnko__sklv.
            block_to_arr_ind[emvr__nfisz]))
        rbufs__ufq, wdtn__objpc = ListInstance.allocate_ex(context, builder,
            types.List(adafk__lpo), vhb__hdfex)
        wdtn__objpc.size = vhb__hdfex
        setattr(jru__qrtzx, f'block_{emvr__nfisz}', wdtn__objpc.value)
    for i, adafk__lpo in enumerate(fromty.data):
        iurp__qjg = toty.data[i]
        if adafk__lpo != iurp__qjg:
            tqad__mxljb = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*tqad__mxljb)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        jhez__evp = builder.extract_value(in_dataframe_payload.data, i)
        if adafk__lpo != iurp__qjg:
            zoyt__gsot = context.cast(builder, jhez__evp, adafk__lpo, iurp__qjg
                )
            zjx__hrm = False
        else:
            zoyt__gsot = jhez__evp
            zjx__hrm = True
        emvr__nfisz = xsnko__sklv.type_to_blk[adafk__lpo]
        uabh__bdvp = getattr(jru__qrtzx, f'block_{emvr__nfisz}')
        vllre__xzwpp = ListInstance(context, builder, types.List(adafk__lpo
            ), uabh__bdvp)
        wnfw__icns = context.get_constant(types.int64, xsnko__sklv.
            block_offsets[i])
        vllre__xzwpp.setitem(wnfw__icns, zoyt__gsot, zjx__hrm)
    data_tup = context.make_tuple(builder, types.Tuple([xsnko__sklv]), [
        jru__qrtzx._getvalue()])
    return data_tup


def _cast_df_data_keep_tuple_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting traditional DataFrame columns')
    fqscq__gwv = []
    for i in range(len(fromty.data)):
        if fromty.data[i] != toty.data[i]:
            tqad__mxljb = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*tqad__mxljb)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
            jhez__evp = builder.extract_value(in_dataframe_payload.data, i)
            zoyt__gsot = context.cast(builder, jhez__evp, fromty.data[i],
                toty.data[i])
            zjx__hrm = False
        else:
            zoyt__gsot = builder.extract_value(in_dataframe_payload.data, i)
            zjx__hrm = True
        if zjx__hrm:
            context.nrt.incref(builder, toty.data[i], zoyt__gsot)
        fqscq__gwv.append(zoyt__gsot)
    data_tup = context.make_tuple(builder, types.Tuple(toty.data), fqscq__gwv)
    return data_tup


def _cast_df_data_keep_table_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting table format DataFrame columns')
    vjzj__ouuze = fromty.table_type
    odscq__fpa = cgutils.create_struct_proxy(vjzj__ouuze)(context, builder,
        builder.extract_value(in_dataframe_payload.data, 0))
    kpw__yraz = toty.table_type
    mskfk__kpg = cgutils.create_struct_proxy(kpw__yraz)(context, builder)
    mskfk__kpg.parent = in_dataframe_payload.parent
    for adafk__lpo, emvr__nfisz in kpw__yraz.type_to_blk.items():
        vhb__hdfex = context.get_constant(types.int64, len(kpw__yraz.
            block_to_arr_ind[emvr__nfisz]))
        rbufs__ufq, wdtn__objpc = ListInstance.allocate_ex(context, builder,
            types.List(adafk__lpo), vhb__hdfex)
        wdtn__objpc.size = vhb__hdfex
        setattr(mskfk__kpg, f'block_{emvr__nfisz}', wdtn__objpc.value)
    for i in range(len(fromty.data)):
        tbf__sasa = fromty.data[i]
        iurp__qjg = toty.data[i]
        if tbf__sasa != iurp__qjg:
            tqad__mxljb = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*tqad__mxljb)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        tkt__cxgft = vjzj__ouuze.type_to_blk[tbf__sasa]
        pknbo__gjt = getattr(odscq__fpa, f'block_{tkt__cxgft}')
        frj__gojo = ListInstance(context, builder, types.List(tbf__sasa),
            pknbo__gjt)
        gubc__qkrk = context.get_constant(types.int64, vjzj__ouuze.
            block_offsets[i])
        jhez__evp = frj__gojo.getitem(gubc__qkrk)
        if tbf__sasa != iurp__qjg:
            zoyt__gsot = context.cast(builder, jhez__evp, tbf__sasa, iurp__qjg)
            zjx__hrm = False
        else:
            zoyt__gsot = jhez__evp
            zjx__hrm = True
        gfcms__kra = kpw__yraz.type_to_blk[adafk__lpo]
        wdtn__objpc = getattr(mskfk__kpg, f'block_{gfcms__kra}')
        fqkva__pawdc = ListInstance(context, builder, types.List(iurp__qjg),
            wdtn__objpc)
        dtr__ypt = context.get_constant(types.int64, kpw__yraz.block_offsets[i]
            )
        fqkva__pawdc.setitem(dtr__ypt, zoyt__gsot, zjx__hrm)
    data_tup = context.make_tuple(builder, types.Tuple([kpw__yraz]), [
        mskfk__kpg._getvalue()])
    return data_tup


def _cast_df_data_to_tuple_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(fromty,
        'casting table format to traditional DataFrame')
    xsnko__sklv = fromty.table_type
    jru__qrtzx = cgutils.create_struct_proxy(xsnko__sklv)(context, builder,
        builder.extract_value(in_dataframe_payload.data, 0))
    fqscq__gwv = []
    for i, adafk__lpo in enumerate(toty.data):
        tbf__sasa = fromty.data[i]
        if adafk__lpo != tbf__sasa:
            tqad__mxljb = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*tqad__mxljb)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        emvr__nfisz = xsnko__sklv.type_to_blk[adafk__lpo]
        uabh__bdvp = getattr(jru__qrtzx, f'block_{emvr__nfisz}')
        vllre__xzwpp = ListInstance(context, builder, types.List(adafk__lpo
            ), uabh__bdvp)
        wnfw__icns = context.get_constant(types.int64, xsnko__sklv.
            block_offsets[i])
        jhez__evp = vllre__xzwpp.getitem(wnfw__icns)
        if adafk__lpo != tbf__sasa:
            zoyt__gsot = context.cast(builder, jhez__evp, tbf__sasa, adafk__lpo
                )
            zjx__hrm = False
        else:
            zoyt__gsot = jhez__evp
            zjx__hrm = True
        if zjx__hrm:
            context.nrt.incref(builder, adafk__lpo, zoyt__gsot)
        fqscq__gwv.append(zoyt__gsot)
    data_tup = context.make_tuple(builder, types.Tuple(toty.data), fqscq__gwv)
    return data_tup


@overload(pd.DataFrame, inline='always', no_unliteral=True)
def pd_dataframe_overload(data=None, index=None, columns=None, dtype=None,
    copy=False):
    if not is_overload_constant_bool(copy):
        raise BodoError(
            "pd.DataFrame(): 'copy' argument should be a constant boolean")
    copy = get_overload_const(copy)
    not__qzi, zpla__lztor, index_arg = _get_df_args(data, index, columns,
        dtype, copy)
    ujdnq__uqepv = gen_const_tup(not__qzi)
    zlyfx__nnvh = (
        'def _init_df(data=None, index=None, columns=None, dtype=None, copy=False):\n'
        )
    zlyfx__nnvh += (
        '  return bodo.hiframes.pd_dataframe_ext.init_dataframe({}, {}, {})\n'
        .format(zpla__lztor, index_arg, ujdnq__uqepv))
    dsp__znd = {}
    exec(zlyfx__nnvh, {'bodo': bodo, 'np': np}, dsp__znd)
    ppvp__actco = dsp__znd['_init_df']
    return ppvp__actco


@intrinsic
def _tuple_to_table_format_decoded(typingctx, df_typ):
    assert not df_typ.is_table_format, '_tuple_to_table_format requires a tuple format input'

    def codegen(context, builder, signature, args):
        return context.cast(builder, args[0], signature.args[0], signature.
            return_type)
    eaao__nns = DataFrameType(to_str_arr_if_dict_array(df_typ.data), df_typ
        .index, df_typ.columns, dist=df_typ.dist, is_table_format=True)
    sig = signature(eaao__nns, df_typ)
    return sig, codegen


@intrinsic
def _table_to_tuple_format_decoded(typingctx, df_typ):
    assert df_typ.is_table_format, '_tuple_to_table_format requires a table format input'

    def codegen(context, builder, signature, args):
        return context.cast(builder, args[0], signature.args[0], signature.
            return_type)
    eaao__nns = DataFrameType(to_str_arr_if_dict_array(df_typ.data), df_typ
        .index, df_typ.columns, dist=df_typ.dist, is_table_format=False)
    sig = signature(eaao__nns, df_typ)
    return sig, codegen


def _get_df_args(data, index, columns, dtype, copy):
    audem__flbh = ''
    if not is_overload_none(dtype):
        audem__flbh = '.astype(dtype)'
    index_is_none = is_overload_none(index)
    index_arg = 'bodo.utils.conversion.convert_to_index(index)'
    if isinstance(data, types.BaseTuple):
        if not data.types[0] == types.StringLiteral('__bodo_tup'):
            raise BodoError('pd.DataFrame tuple input data not supported yet')
        assert len(data.types) % 2 == 1, 'invalid const dict tuple structure'
        apbut__caxw = (len(data.types) - 1) // 2
        ontsr__yuxf = [adafk__lpo.literal_value for adafk__lpo in data.
            types[1:apbut__caxw + 1]]
        data_val_types = dict(zip(ontsr__yuxf, data.types[apbut__caxw + 1:]))
        fqscq__gwv = ['data[{}]'.format(i) for i in range(apbut__caxw + 1, 
            2 * apbut__caxw + 1)]
        data_dict = dict(zip(ontsr__yuxf, fqscq__gwv))
        if is_overload_none(index):
            for i, adafk__lpo in enumerate(data.types[apbut__caxw + 1:]):
                if isinstance(adafk__lpo, SeriesType):
                    index_arg = (
                        'bodo.hiframes.pd_series_ext.get_series_index(data[{}])'
                        .format(apbut__caxw + 1 + i))
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
        ridhb__dwg = '.copy()' if copy else ''
        wgw__kwl = get_overload_const_list(columns)
        apbut__caxw = len(wgw__kwl)
        data_val_types = {htcp__ynkuq: data.copy(ndim=1) for htcp__ynkuq in
            wgw__kwl}
        fqscq__gwv = ['data[:,{}]{}'.format(i, ridhb__dwg) for i in range(
            apbut__caxw)]
        data_dict = dict(zip(wgw__kwl, fqscq__gwv))
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
    zpla__lztor = '({},)'.format(', '.join(
        'bodo.utils.conversion.coerce_to_array({}, True, scalar_to_arr_len={}){}'
        .format(data_dict[htcp__ynkuq], df_len, audem__flbh) for
        htcp__ynkuq in col_names))
    if len(col_names) == 0:
        zpla__lztor = '()'
    return col_names, zpla__lztor, index_arg


def _get_df_len_from_info(data_dict, data_val_types, col_names,
    index_is_none, index_arg):
    df_len = '0'
    for htcp__ynkuq in col_names:
        if htcp__ynkuq in data_dict and is_iterable_type(data_val_types[
            htcp__ynkuq]):
            df_len = 'len({})'.format(data_dict[htcp__ynkuq])
            break
    if df_len == '0' and not index_is_none:
        df_len = f'len({index_arg})'
    return df_len


def _fill_null_arrays(data_dict, col_names, df_len, dtype):
    if all(htcp__ynkuq in data_dict for htcp__ynkuq in col_names):
        return
    if is_overload_none(dtype):
        dtype = 'bodo.string_array_type'
    else:
        dtype = 'bodo.utils.conversion.array_type_from_dtype(dtype)'
    xlpdp__eah = 'bodo.libs.array_kernels.gen_na_array({}, {})'.format(df_len,
        dtype)
    for htcp__ynkuq in col_names:
        if htcp__ynkuq not in data_dict:
            data_dict[htcp__ynkuq] = xlpdp__eah


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
            adafk__lpo = bodo.hiframes.pd_dataframe_ext.get_dataframe_table(df)
            return len(adafk__lpo)
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
        rmoq__iofer = idx.literal_value
        if isinstance(rmoq__iofer, int):
            qzs__grqmr = tup.types[rmoq__iofer]
        elif isinstance(rmoq__iofer, slice):
            qzs__grqmr = types.BaseTuple.from_types(tup.types[rmoq__iofer])
        return signature(qzs__grqmr, *args)


GetItemTuple.prefer_literal = True


@lower_builtin(operator.getitem, types.BaseTuple, types.IntegerLiteral)
@lower_builtin(operator.getitem, types.BaseTuple, types.SliceLiteral)
def getitem_tuple_lower(context, builder, sig, args):
    hbam__xubfo, idx = sig.args
    idx = idx.literal_value
    tup, rbufs__ufq = args
    if isinstance(idx, int):
        if idx < 0:
            idx += len(hbam__xubfo)
        if not 0 <= idx < len(hbam__xubfo):
            raise IndexError('cannot index at %d in %s' % (idx, hbam__xubfo))
        xrp__jitu = builder.extract_value(tup, idx)
    elif isinstance(idx, slice):
        fhpe__ervy = cgutils.unpack_tuple(builder, tup)[idx]
        xrp__jitu = context.make_tuple(builder, sig.return_type, fhpe__ervy)
    else:
        raise NotImplementedError('unexpected index %r for %s' % (idx, sig.
            args[0]))
    return impl_ret_borrowed(context, builder, sig.return_type, xrp__jitu)


def join_dummy(left_df, right_df, left_on, right_on, how, suffix_x,
    suffix_y, is_join, indicator, _bodo_na_equal, gen_cond):
    return left_df


@infer_global(join_dummy)
class JoinTyper(AbstractTemplate):

    def generic(self, args, kws):
        from bodo.hiframes.pd_dataframe_ext import DataFrameType
        from bodo.utils.typing import is_overload_str
        assert not kws
        (left_df, right_df, left_on, right_on, xfkmv__cuntu, suffix_x,
            suffix_y, is_join, indicator, _bodo_na_equal, piesg__zlog) = args
        left_on = get_overload_const_list(left_on)
        right_on = get_overload_const_list(right_on)
        xlq__tprqi = set(left_on) & set(right_on)
        qzfy__ioak = set(left_df.columns) & set(right_df.columns)
        jdtzd__csovo = qzfy__ioak - xlq__tprqi
        ymtao__ost = '$_bodo_index_' in left_on
        hjd__rfwkd = '$_bodo_index_' in right_on
        how = get_overload_const_str(xfkmv__cuntu)
        augp__wtnj = how in {'left', 'outer'}
        mpldr__ttz = how in {'right', 'outer'}
        columns = []
        data = []
        if ymtao__ost:
            fhox__dnd = bodo.utils.typing.get_index_data_arr_types(left_df.
                index)[0]
        else:
            fhox__dnd = left_df.data[left_df.columns.index(left_on[0])]
        if hjd__rfwkd:
            gaw__yyw = bodo.utils.typing.get_index_data_arr_types(right_df.
                index)[0]
        else:
            gaw__yyw = right_df.data[right_df.columns.index(right_on[0])]
        if ymtao__ost and not hjd__rfwkd and not is_join.literal_value:
            mjns__apwpj = right_on[0]
            if mjns__apwpj in left_df.columns:
                columns.append(mjns__apwpj)
                if (gaw__yyw == bodo.dict_str_arr_type and fhox__dnd ==
                    bodo.string_array_type):
                    skij__lektu = bodo.string_array_type
                else:
                    skij__lektu = gaw__yyw
                data.append(skij__lektu)
        if hjd__rfwkd and not ymtao__ost and not is_join.literal_value:
            jcxej__yyk = left_on[0]
            if jcxej__yyk in right_df.columns:
                columns.append(jcxej__yyk)
                if (fhox__dnd == bodo.dict_str_arr_type and gaw__yyw ==
                    bodo.string_array_type):
                    skij__lektu = bodo.string_array_type
                else:
                    skij__lektu = fhox__dnd
                data.append(skij__lektu)
        for tbf__sasa, wruo__kdlu in zip(left_df.data, left_df.columns):
            columns.append(str(wruo__kdlu) + suffix_x.literal_value if 
                wruo__kdlu in jdtzd__csovo else wruo__kdlu)
            if wruo__kdlu in xlq__tprqi:
                if tbf__sasa == bodo.dict_str_arr_type:
                    tbf__sasa = right_df.data[right_df.columns.index(
                        wruo__kdlu)]
                data.append(tbf__sasa)
            else:
                if (tbf__sasa == bodo.dict_str_arr_type and wruo__kdlu in
                    left_on):
                    if hjd__rfwkd:
                        tbf__sasa = gaw__yyw
                    else:
                        tpeyj__gnen = left_on.index(wruo__kdlu)
                        cxbwq__zcfoa = right_on[tpeyj__gnen]
                        tbf__sasa = right_df.data[right_df.columns.index(
                            cxbwq__zcfoa)]
                if mpldr__ttz:
                    tbf__sasa = to_nullable_type(tbf__sasa)
                data.append(tbf__sasa)
        for tbf__sasa, wruo__kdlu in zip(right_df.data, right_df.columns):
            if wruo__kdlu not in xlq__tprqi:
                columns.append(str(wruo__kdlu) + suffix_y.literal_value if 
                    wruo__kdlu in jdtzd__csovo else wruo__kdlu)
                if (tbf__sasa == bodo.dict_str_arr_type and wruo__kdlu in
                    right_on):
                    if ymtao__ost:
                        tbf__sasa = fhox__dnd
                    else:
                        tpeyj__gnen = right_on.index(wruo__kdlu)
                        tmfe__katgq = left_on[tpeyj__gnen]
                        tbf__sasa = left_df.data[left_df.columns.index(
                            tmfe__katgq)]
                if augp__wtnj:
                    tbf__sasa = to_nullable_type(tbf__sasa)
                data.append(tbf__sasa)
        ohcjc__pkoy = get_overload_const_bool(indicator)
        if ohcjc__pkoy:
            columns.append('_merge')
            data.append(bodo.CategoricalArrayType(bodo.PDCategoricalDtype((
                'left_only', 'right_only', 'both'), bodo.string_type, False)))
        index_typ = RangeIndexType(types.none)
        if ymtao__ost and hjd__rfwkd and not is_overload_str(how, 'asof'):
            index_typ = left_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        elif ymtao__ost and not hjd__rfwkd:
            index_typ = right_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        elif hjd__rfwkd and not ymtao__ost:
            index_typ = left_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        ehbsv__wibo = DataFrameType(tuple(data), index_typ, tuple(columns))
        return signature(ehbsv__wibo, *args)


JoinTyper._no_unliteral = True


@lower_builtin(join_dummy, types.VarArg(types.Any))
def lower_join_dummy(context, builder, sig, args):
    rkavi__nodb = cgutils.create_struct_proxy(sig.return_type)(context, builder
        )
    return rkavi__nodb._getvalue()


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
    shsv__qfd = dict(join=join, join_axes=join_axes, keys=keys, levels=
        levels, names=names, verify_integrity=verify_integrity, sort=sort,
        copy=copy)
    glui__gec = dict(join='outer', join_axes=None, keys=None, levels=None,
        names=None, verify_integrity=False, sort=None, copy=True)
    check_unsupported_args('pandas.concat', shsv__qfd, glui__gec,
        package_name='pandas', module_name='General')
    zlyfx__nnvh = """def impl(objs, axis=0, join='outer', join_axes=None, ignore_index=False, keys=None, levels=None, names=None, verify_integrity=False, sort=None, copy=True):
"""
    if axis == 1:
        if not isinstance(objs, types.BaseTuple):
            raise_bodo_error(
                'Only tuple argument for pd.concat(axis=1) expected')
        index = (
            'bodo.hiframes.pd_index_ext.init_range_index(0, len(objs[0]), 1, None)'
            )
        gjpag__dmxf = 0
        zpla__lztor = []
        names = []
        for i, llc__urg in enumerate(objs.types):
            assert isinstance(llc__urg, (SeriesType, DataFrameType))
            check_runtime_cols_unsupported(llc__urg, 'pandas.concat()')
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(llc__urg,
                'pandas.concat()')
            if isinstance(llc__urg, SeriesType):
                names.append(str(gjpag__dmxf))
                gjpag__dmxf += 1
                zpla__lztor.append(
                    'bodo.hiframes.pd_series_ext.get_series_data(objs[{}])'
                    .format(i))
            else:
                names.extend(llc__urg.columns)
                for aepqy__mdmkv in range(len(llc__urg.data)):
                    zpla__lztor.append(
                        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(objs[{}], {})'
                        .format(i, aepqy__mdmkv))
        return bodo.hiframes.dataframe_impl._gen_init_df(zlyfx__nnvh, names,
            ', '.join(zpla__lztor), index)
    if axis != 0:
        raise_bodo_error('pd.concat(): axis must be 0 or 1')
    if isinstance(objs, types.BaseTuple) and isinstance(objs.types[0],
        DataFrameType):
        assert all(isinstance(adafk__lpo, DataFrameType) for adafk__lpo in
            objs.types)
        uwfjy__fozc = []
        for df in objs.types:
            check_runtime_cols_unsupported(df, 'pandas.concat()')
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
                'pandas.concat()')
            uwfjy__fozc.extend(df.columns)
        uwfjy__fozc = list(dict.fromkeys(uwfjy__fozc).keys())
        ugg__popv = {}
        for gjpag__dmxf, htcp__ynkuq in enumerate(uwfjy__fozc):
            for df in objs.types:
                if htcp__ynkuq in df.columns:
                    ugg__popv['arr_typ{}'.format(gjpag__dmxf)] = df.data[df
                        .columns.index(htcp__ynkuq)]
                    break
        assert len(ugg__popv) == len(uwfjy__fozc)
        arch__uyj = []
        for gjpag__dmxf, htcp__ynkuq in enumerate(uwfjy__fozc):
            args = []
            for i, df in enumerate(objs.types):
                if htcp__ynkuq in df.columns:
                    hfmbg__uezxg = df.columns.index(htcp__ynkuq)
                    args.append(
                        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(objs[{}], {})'
                        .format(i, hfmbg__uezxg))
                else:
                    args.append(
                        'bodo.libs.array_kernels.gen_na_array(len(objs[{}]), arr_typ{})'
                        .format(i, gjpag__dmxf))
            zlyfx__nnvh += ('  A{} = bodo.libs.array_kernels.concat(({},))\n'
                .format(gjpag__dmxf, ', '.join(args)))
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
        return bodo.hiframes.dataframe_impl._gen_init_df(zlyfx__nnvh,
            uwfjy__fozc, ', '.join('A{}'.format(i) for i in range(len(
            uwfjy__fozc))), index, ugg__popv)
    if isinstance(objs, types.BaseTuple) and isinstance(objs.types[0],
        SeriesType):
        assert all(isinstance(adafk__lpo, SeriesType) for adafk__lpo in
            objs.types)
        zlyfx__nnvh += ('  out_arr = bodo.libs.array_kernels.concat(({},))\n'
            .format(', '.join(
            'bodo.hiframes.pd_series_ext.get_series_data(objs[{}])'.format(
            i) for i in range(len(objs.types)))))
        if ignore_index:
            zlyfx__nnvh += """  index = bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr), 1, None)
"""
        else:
            zlyfx__nnvh += (
                """  index = bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(({},)))
"""
                .format(', '.join(
                'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(objs[{}]))'
                .format(i) for i in range(len(objs.types)))))
        zlyfx__nnvh += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index)\n'
            )
        dsp__znd = {}
        exec(zlyfx__nnvh, {'bodo': bodo, 'np': np, 'numba': numba}, dsp__znd)
        return dsp__znd['impl']
    if isinstance(objs, types.List) and isinstance(objs.dtype, DataFrameType):
        check_runtime_cols_unsupported(objs.dtype, 'pandas.concat()')
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(objs.
            dtype, 'pandas.concat()')
        df_type = objs.dtype
        for gjpag__dmxf, htcp__ynkuq in enumerate(df_type.columns):
            zlyfx__nnvh += '  arrs{} = []\n'.format(gjpag__dmxf)
            zlyfx__nnvh += '  for i in range(len(objs)):\n'
            zlyfx__nnvh += '    df = objs[i]\n'
            zlyfx__nnvh += (
                """    arrs{0}.append(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0}))
"""
                .format(gjpag__dmxf))
            zlyfx__nnvh += (
                '  out_arr{0} = bodo.libs.array_kernels.concat(arrs{0})\n'.
                format(gjpag__dmxf))
        if ignore_index:
            index = (
                'bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr0), 1, None)'
                )
        else:
            zlyfx__nnvh += '  arrs_index = []\n'
            zlyfx__nnvh += '  for i in range(len(objs)):\n'
            zlyfx__nnvh += '    df = objs[i]\n'
            zlyfx__nnvh += """    arrs_index.append(bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)))
"""
            if objs.dtype.index.name_typ == types.none:
                name = None
            else:
                name = objs.dtype.index.name_typ.literal_value
            index = f"""bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(arrs_index), {name!r})
"""
        return bodo.hiframes.dataframe_impl._gen_init_df(zlyfx__nnvh,
            df_type.columns, ', '.join('out_arr{}'.format(i) for i in range
            (len(df_type.columns))), index)
    if isinstance(objs, types.List) and isinstance(objs.dtype, SeriesType):
        zlyfx__nnvh += '  arrs = []\n'
        zlyfx__nnvh += '  for i in range(len(objs)):\n'
        zlyfx__nnvh += (
            '    arrs.append(bodo.hiframes.pd_series_ext.get_series_data(objs[i]))\n'
            )
        zlyfx__nnvh += '  out_arr = bodo.libs.array_kernels.concat(arrs)\n'
        if ignore_index:
            zlyfx__nnvh += """  index = bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr), 1, None)
"""
        else:
            zlyfx__nnvh += '  arrs_index = []\n'
            zlyfx__nnvh += '  for i in range(len(objs)):\n'
            zlyfx__nnvh += '    S = objs[i]\n'
            zlyfx__nnvh += """    arrs_index.append(bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(S)))
"""
            zlyfx__nnvh += """  index = bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(arrs_index))
"""
        zlyfx__nnvh += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index)\n'
            )
        dsp__znd = {}
        exec(zlyfx__nnvh, {'bodo': bodo, 'np': np, 'numba': numba}, dsp__znd)
        return dsp__znd['impl']
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
        eaao__nns = df.copy(index=index, is_table_format=False)
        return signature(eaao__nns, *args)


SortDummyTyper._no_unliteral = True


@lower_builtin(sort_values_dummy, types.VarArg(types.Any))
def lower_sort_values_dummy(context, builder, sig, args):
    if sig.return_type == types.none:
        return
    wkgdl__fttgr = cgutils.create_struct_proxy(sig.return_type)(context,
        builder)
    return wkgdl__fttgr._getvalue()


@overload_method(DataFrameType, 'itertuples', inline='always', no_unliteral
    =True)
def itertuples_overload(df, index=True, name='Pandas'):
    check_runtime_cols_unsupported(df, 'DataFrame.itertuples()')
    shsv__qfd = dict(index=index, name=name)
    glui__gec = dict(index=True, name='Pandas')
    check_unsupported_args('DataFrame.itertuples', shsv__qfd, glui__gec,
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
        ugg__popv = (types.Array(types.int64, 1, 'C'),) + df.data
        nutov__oyqz = bodo.hiframes.dataframe_impl.DataFrameTupleIterator(
            columns, ugg__popv)
        return signature(nutov__oyqz, *args)


@lower_builtin(itertuples_dummy, types.VarArg(types.Any))
def lower_itertuples_dummy(context, builder, sig, args):
    wkgdl__fttgr = cgutils.create_struct_proxy(sig.return_type)(context,
        builder)
    return wkgdl__fttgr._getvalue()


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
    wkgdl__fttgr = cgutils.create_struct_proxy(sig.return_type)(context,
        builder)
    return wkgdl__fttgr._getvalue()


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
    wkgdl__fttgr = cgutils.create_struct_proxy(sig.return_type)(context,
        builder)
    return wkgdl__fttgr._getvalue()


@numba.generated_jit(nopython=True)
def pivot_impl(index_tup, columns_tup, values_tup, pivot_values,
    index_names, columns_name, value_names, check_duplicates=True, parallel
    =False):
    if not is_overload_constant_bool(check_duplicates):
        raise BodoError(
            'pivot_impl(): check_duplicates must be a constant boolean')
    udtd__bprwy = get_overload_const_bool(check_duplicates)
    igp__uggg = not is_overload_none(value_names)
    app__lly = isinstance(values_tup, types.UniTuple)
    if app__lly:
        knwed__lsaa = [to_nullable_type(values_tup.dtype)]
    else:
        knwed__lsaa = [to_nullable_type(gjl__ewvh) for gjl__ewvh in values_tup]
    zlyfx__nnvh = 'def impl(\n'
    zlyfx__nnvh += """    index_tup, columns_tup, values_tup, pivot_values, index_names, columns_name, value_names, check_duplicates=True, parallel=False
"""
    zlyfx__nnvh += '):\n'
    zlyfx__nnvh += '    if parallel:\n'
    dniy__sjg = ', '.join([f'array_to_info(index_tup[{i}])' for i in range(
        len(index_tup))] + [f'array_to_info(columns_tup[{i}])' for i in
        range(len(columns_tup))] + [f'array_to_info(values_tup[{i}])' for i in
        range(len(values_tup))])
    zlyfx__nnvh += f'        info_list = [{dniy__sjg}]\n'
    zlyfx__nnvh += '        cpp_table = arr_info_list_to_table(info_list)\n'
    zlyfx__nnvh += f"""        out_cpp_table = shuffle_table(cpp_table, {len(index_tup)}, parallel, 0)
"""
    gmrf__vvfia = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i}), index_tup[{i}])'
         for i in range(len(index_tup))])
    jyn__qvy = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i + len(index_tup)}), columns_tup[{i}])'
         for i in range(len(columns_tup))])
    ewq__pbko = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i + len(index_tup) + len(columns_tup)}), values_tup[{i}])'
         for i in range(len(values_tup))])
    zlyfx__nnvh += f'        index_tup = ({gmrf__vvfia},)\n'
    zlyfx__nnvh += f'        columns_tup = ({jyn__qvy},)\n'
    zlyfx__nnvh += f'        values_tup = ({ewq__pbko},)\n'
    zlyfx__nnvh += '        delete_table(cpp_table)\n'
    zlyfx__nnvh += '        delete_table(out_cpp_table)\n'
    zlyfx__nnvh += '    columns_arr = columns_tup[0]\n'
    if app__lly:
        zlyfx__nnvh += '    values_arrs = [arr for arr in values_tup]\n'
    zlyfx__nnvh += """    unique_index_arr_tup, row_vector = bodo.libs.array_ops.array_unique_vector_map(
"""
    zlyfx__nnvh += '        index_tup\n'
    zlyfx__nnvh += '    )\n'
    zlyfx__nnvh += '    n_rows = len(unique_index_arr_tup[0])\n'
    zlyfx__nnvh += '    num_values_arrays = len(values_tup)\n'
    zlyfx__nnvh += '    n_unique_pivots = len(pivot_values)\n'
    if app__lly:
        zlyfx__nnvh += '    n_cols = num_values_arrays * n_unique_pivots\n'
    else:
        zlyfx__nnvh += '    n_cols = n_unique_pivots\n'
    zlyfx__nnvh += '    col_map = {}\n'
    zlyfx__nnvh += '    for i in range(n_unique_pivots):\n'
    zlyfx__nnvh += (
        '        if bodo.libs.array_kernels.isna(pivot_values, i):\n')
    zlyfx__nnvh += '            raise ValueError(\n'
    zlyfx__nnvh += """                "DataFrame.pivot(): NA values in 'columns' array not supported\"
"""
    zlyfx__nnvh += '            )\n'
    zlyfx__nnvh += '        col_map[pivot_values[i]] = i\n'
    knhm__kzege = False
    for i, nzib__zzlc in enumerate(knwed__lsaa):
        if is_str_arr_type(nzib__zzlc):
            knhm__kzege = True
            zlyfx__nnvh += f"""    len_arrs_{i} = [np.zeros(n_rows, np.int64) for _ in range(n_cols)]
"""
            zlyfx__nnvh += f'    total_lens_{i} = np.zeros(n_cols, np.int64)\n'
    if knhm__kzege:
        if udtd__bprwy:
            zlyfx__nnvh += '    nbytes = (n_rows + 7) >> 3\n'
            zlyfx__nnvh += """    seen_bitmaps = [np.zeros(nbytes, np.int8) for _ in range(n_unique_pivots)]
"""
        zlyfx__nnvh += '    for i in range(len(columns_arr)):\n'
        zlyfx__nnvh += '        col_name = columns_arr[i]\n'
        zlyfx__nnvh += '        pivot_idx = col_map[col_name]\n'
        zlyfx__nnvh += '        row_idx = row_vector[i]\n'
        if udtd__bprwy:
            zlyfx__nnvh += '        seen_bitmap = seen_bitmaps[pivot_idx]\n'
            zlyfx__nnvh += """        if bodo.libs.int_arr_ext.get_bit_bitmap_arr(seen_bitmap, row_idx):
"""
            zlyfx__nnvh += """            raise ValueError("DataFrame.pivot(): 'index' contains duplicate entries for the same output column")
"""
            zlyfx__nnvh += '        else:\n'
            zlyfx__nnvh += """            bodo.libs.int_arr_ext.set_bit_to_arr(seen_bitmap, row_idx, 1)
"""
        if app__lly:
            zlyfx__nnvh += '        for j in range(num_values_arrays):\n'
            zlyfx__nnvh += (
                '            col_idx = (j * len(pivot_values)) + pivot_idx\n')
            zlyfx__nnvh += '            len_arr = len_arrs_0[col_idx]\n'
            zlyfx__nnvh += '            values_arr = values_arrs[j]\n'
            zlyfx__nnvh += (
                '            if not bodo.libs.array_kernels.isna(values_arr, i):\n'
                )
            zlyfx__nnvh += (
                '                len_arr[row_idx] = len(values_arr[i])\n')
            zlyfx__nnvh += (
                '                total_lens_0[col_idx] += len(values_arr[i])\n'
                )
        else:
            for i, nzib__zzlc in enumerate(knwed__lsaa):
                if is_str_arr_type(nzib__zzlc):
                    zlyfx__nnvh += f"""        if not bodo.libs.array_kernels.isna(values_tup[{i}], i):
"""
                    zlyfx__nnvh += f"""            len_arrs_{i}[pivot_idx][row_idx] = len(values_tup[{i}][i])
"""
                    zlyfx__nnvh += f"""            total_lens_{i}[pivot_idx] += len(values_tup[{i}][i])
"""
    for i, nzib__zzlc in enumerate(knwed__lsaa):
        if is_str_arr_type(nzib__zzlc):
            zlyfx__nnvh += f'    data_arrs_{i} = [\n'
            zlyfx__nnvh += (
                '        bodo.libs.str_arr_ext.gen_na_str_array_lens(\n')
            zlyfx__nnvh += (
                f'            n_rows, total_lens_{i}[i], len_arrs_{i}[i]\n')
            zlyfx__nnvh += '        )\n'
            zlyfx__nnvh += '        for i in range(n_cols)\n'
            zlyfx__nnvh += '    ]\n'
        else:
            zlyfx__nnvh += f'    data_arrs_{i} = [\n'
            zlyfx__nnvh += f"""        bodo.libs.array_kernels.gen_na_array(n_rows, data_arr_typ_{i})
"""
            zlyfx__nnvh += '        for _ in range(n_cols)\n'
            zlyfx__nnvh += '    ]\n'
    if not knhm__kzege and udtd__bprwy:
        zlyfx__nnvh += '    nbytes = (n_rows + 7) >> 3\n'
        zlyfx__nnvh += """    seen_bitmaps = [np.zeros(nbytes, np.int8) for _ in range(n_unique_pivots)]
"""
    zlyfx__nnvh += '    for i in range(len(columns_arr)):\n'
    zlyfx__nnvh += '        col_name = columns_arr[i]\n'
    zlyfx__nnvh += '        pivot_idx = col_map[col_name]\n'
    zlyfx__nnvh += '        row_idx = row_vector[i]\n'
    if not knhm__kzege and udtd__bprwy:
        zlyfx__nnvh += '        seen_bitmap = seen_bitmaps[pivot_idx]\n'
        zlyfx__nnvh += """        if bodo.libs.int_arr_ext.get_bit_bitmap_arr(seen_bitmap, row_idx):
"""
        zlyfx__nnvh += """            raise ValueError("DataFrame.pivot(): 'index' contains duplicate entries for the same output column")
"""
        zlyfx__nnvh += '        else:\n'
        zlyfx__nnvh += """            bodo.libs.int_arr_ext.set_bit_to_arr(seen_bitmap, row_idx, 1)
"""
    if app__lly:
        zlyfx__nnvh += '        for j in range(num_values_arrays):\n'
        zlyfx__nnvh += (
            '            col_idx = (j * len(pivot_values)) + pivot_idx\n')
        zlyfx__nnvh += '            col_arr = data_arrs_0[col_idx]\n'
        zlyfx__nnvh += '            values_arr = values_arrs[j]\n'
        zlyfx__nnvh += (
            '            if bodo.libs.array_kernels.isna(values_arr, i):\n')
        zlyfx__nnvh += (
            '                bodo.libs.array_kernels.setna(col_arr, row_idx)\n'
            )
        zlyfx__nnvh += '            else:\n'
        zlyfx__nnvh += '                col_arr[row_idx] = values_arr[i]\n'
    else:
        for i, nzib__zzlc in enumerate(knwed__lsaa):
            zlyfx__nnvh += f'        col_arr_{i} = data_arrs_{i}[pivot_idx]\n'
            zlyfx__nnvh += (
                f'        if bodo.libs.array_kernels.isna(values_tup[{i}], i):\n'
                )
            zlyfx__nnvh += (
                f'            bodo.libs.array_kernels.setna(col_arr_{i}, row_idx)\n'
                )
            zlyfx__nnvh += f'        else:\n'
            zlyfx__nnvh += (
                f'            col_arr_{i}[row_idx] = values_tup[{i}][i]\n')
    if len(index_tup) == 1:
        zlyfx__nnvh += """    index = bodo.utils.conversion.index_from_array(unique_index_arr_tup[0], index_names[0])
"""
    else:
        zlyfx__nnvh += """    index = bodo.hiframes.pd_multi_index_ext.init_multi_index(unique_index_arr_tup, index_names, None)
"""
    if igp__uggg:
        zlyfx__nnvh += '    num_rows = len(value_names) * len(pivot_values)\n'
        if is_str_arr_type(value_names):
            zlyfx__nnvh += '    total_chars = 0\n'
            zlyfx__nnvh += '    for i in range(len(value_names)):\n'
            zlyfx__nnvh += '        total_chars += len(value_names[i])\n'
            zlyfx__nnvh += """    new_value_names = bodo.libs.str_arr_ext.pre_alloc_string_array(num_rows, total_chars * len(pivot_values))
"""
        else:
            zlyfx__nnvh += """    new_value_names = bodo.utils.utils.alloc_type(num_rows, value_names, (-1,))
"""
        if is_str_arr_type(pivot_values):
            zlyfx__nnvh += '    total_chars = 0\n'
            zlyfx__nnvh += '    for i in range(len(pivot_values)):\n'
            zlyfx__nnvh += '        total_chars += len(pivot_values[i])\n'
            zlyfx__nnvh += """    new_pivot_values = bodo.libs.str_arr_ext.pre_alloc_string_array(num_rows, total_chars * len(value_names))
"""
        else:
            zlyfx__nnvh += """    new_pivot_values = bodo.utils.utils.alloc_type(num_rows, pivot_values, (-1,))
"""
        zlyfx__nnvh += '    for i in range(len(value_names)):\n'
        zlyfx__nnvh += '        for j in range(len(pivot_values)):\n'
        zlyfx__nnvh += """            new_value_names[(i * len(pivot_values)) + j] = value_names[i]
"""
        zlyfx__nnvh += """            new_pivot_values[(i * len(pivot_values)) + j] = pivot_values[j]
"""
        zlyfx__nnvh += """    column_index = bodo.hiframes.pd_multi_index_ext.init_multi_index((new_value_names, new_pivot_values), (None, columns_name), None)
"""
    else:
        zlyfx__nnvh += """    column_index =  bodo.utils.conversion.index_from_array(pivot_values, columns_name)
"""
    zvq__mkcow = ', '.join(f'data_arrs_{i}' for i in range(len(knwed__lsaa)))
    zlyfx__nnvh += f"""    table = bodo.hiframes.table.init_runtime_table_from_lists(({zvq__mkcow},), n_rows)
"""
    zlyfx__nnvh += (
        '    return bodo.hiframes.pd_dataframe_ext.init_runtime_cols_dataframe(\n'
        )
    zlyfx__nnvh += '        (table,), index, column_index\n'
    zlyfx__nnvh += '    )\n'
    dsp__znd = {}
    rcml__iyov = {f'data_arr_typ_{i}': nzib__zzlc for i, nzib__zzlc in
        enumerate(knwed__lsaa)}
    nxbh__glwwb = {'bodo': bodo, 'np': np, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'shuffle_table':
        shuffle_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'info_from_table': info_from_table, **rcml__iyov}
    exec(zlyfx__nnvh, nxbh__glwwb, dsp__znd)
    impl = dsp__znd['impl']
    return impl


def gen_pandas_parquet_metadata(column_names, data_types, index,
    write_non_range_index_to_metadata, write_rangeindex_to_metadata,
    partition_cols=None, is_runtime_columns=False):
    xufrb__suh = {}
    xufrb__suh['columns'] = []
    if partition_cols is None:
        partition_cols = []
    for col_name, xngs__fxm in zip(column_names, data_types):
        if col_name in partition_cols:
            continue
        yms__mww = None
        if isinstance(xngs__fxm, bodo.DatetimeArrayType):
            lgu__rbxi = 'datetimetz'
            lafq__dpaw = 'datetime64[ns]'
            if isinstance(xngs__fxm.tz, int):
                gvf__mgv = bodo.libs.pd_datetime_arr_ext.nanoseconds_to_offset(
                    xngs__fxm.tz)
            else:
                gvf__mgv = pd.DatetimeTZDtype(tz=xngs__fxm.tz).tz
            yms__mww = {'timezone': pa.lib.tzinfo_to_string(gvf__mgv)}
        elif isinstance(xngs__fxm, types.Array) or xngs__fxm == boolean_array:
            lgu__rbxi = lafq__dpaw = xngs__fxm.dtype.name
            if lafq__dpaw.startswith('datetime'):
                lgu__rbxi = 'datetime'
        elif is_str_arr_type(xngs__fxm):
            lgu__rbxi = 'unicode'
            lafq__dpaw = 'object'
        elif xngs__fxm == binary_array_type:
            lgu__rbxi = 'bytes'
            lafq__dpaw = 'object'
        elif isinstance(xngs__fxm, DecimalArrayType):
            lgu__rbxi = lafq__dpaw = 'object'
        elif isinstance(xngs__fxm, IntegerArrayType):
            rii__dgc = xngs__fxm.dtype.name
            if rii__dgc.startswith('int'):
                lgu__rbxi = 'Int' + rii__dgc[3:]
            elif rii__dgc.startswith('uint'):
                lgu__rbxi = 'UInt' + rii__dgc[4:]
            else:
                if is_runtime_columns:
                    col_name = 'Runtime determined column of type'
                raise BodoError(
                    'to_parquet(): unknown dtype in nullable Integer column {} {}'
                    .format(col_name, xngs__fxm))
            lafq__dpaw = xngs__fxm.dtype.name
        elif xngs__fxm == datetime_date_array_type:
            lgu__rbxi = 'datetime'
            lafq__dpaw = 'object'
        elif isinstance(xngs__fxm, (StructArrayType, ArrayItemArrayType)):
            lgu__rbxi = 'object'
            lafq__dpaw = 'object'
        else:
            if is_runtime_columns:
                col_name = 'Runtime determined column of type'
            raise BodoError(
                'to_parquet(): unsupported column type for metadata generation : {} {}'
                .format(col_name, xngs__fxm))
        sjrph__ezws = {'name': col_name, 'field_name': col_name,
            'pandas_type': lgu__rbxi, 'numpy_type': lafq__dpaw, 'metadata':
            yms__mww}
        xufrb__suh['columns'].append(sjrph__ezws)
    if write_non_range_index_to_metadata:
        if isinstance(index, MultiIndexType):
            raise BodoError('to_parquet: MultiIndex not supported yet')
        if 'none' in index.name:
            rwuds__uer = '__index_level_0__'
            tfi__cuwz = None
        else:
            rwuds__uer = '%s'
            tfi__cuwz = '%s'
        xufrb__suh['index_columns'] = [rwuds__uer]
        xufrb__suh['columns'].append({'name': tfi__cuwz, 'field_name':
            rwuds__uer, 'pandas_type': index.pandas_type_name, 'numpy_type':
            index.numpy_type_name, 'metadata': None})
    elif write_rangeindex_to_metadata:
        xufrb__suh['index_columns'] = [{'kind': 'range', 'name': '%s',
            'start': '%d', 'stop': '%d', 'step': '%d'}]
    else:
        xufrb__suh['index_columns'] = []
    xufrb__suh['pandas_version'] = pd.__version__
    return xufrb__suh


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
        rfez__pfgcx = []
        for rfbet__zky in partition_cols:
            try:
                idx = df.columns.index(rfbet__zky)
            except ValueError as fyyet__jdg:
                raise BodoError(
                    f'Partition column {rfbet__zky} is not in dataframe')
            rfez__pfgcx.append(idx)
    else:
        partition_cols = None
    if not is_overload_none(index) and not is_overload_constant_bool(index):
        raise BodoError('to_parquet(): index must be a constant bool or None')
    from bodo.io.parquet_pio import parquet_write_table_cpp, parquet_write_table_partitioned_cpp
    gbr__kfw = isinstance(df.index, bodo.hiframes.pd_index_ext.RangeIndexType)
    hon__dvqrp = df.index is not None and (is_overload_true(_is_parallel) or
        not is_overload_true(_is_parallel) and not gbr__kfw)
    write_non_range_index_to_metadata = is_overload_true(index
        ) or is_overload_none(index) and (not gbr__kfw or is_overload_true(
        _is_parallel))
    write_rangeindex_to_metadata = is_overload_none(index
        ) and gbr__kfw and not is_overload_true(_is_parallel)
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
        dqkam__kdqxa = df.runtime_data_types
        kcsaq__hwof = len(dqkam__kdqxa)
        yms__mww = gen_pandas_parquet_metadata([''] * kcsaq__hwof,
            dqkam__kdqxa, df.index, write_non_range_index_to_metadata,
            write_rangeindex_to_metadata, partition_cols=partition_cols,
            is_runtime_columns=True)
        hxul__qdr = yms__mww['columns'][:kcsaq__hwof]
        yms__mww['columns'] = yms__mww['columns'][kcsaq__hwof:]
        hxul__qdr = [json.dumps(qfm__xqsb).replace('""', '{0}') for
            qfm__xqsb in hxul__qdr]
        umi__bcnl = json.dumps(yms__mww)
        naj__cgz = '"columns": ['
        hkkp__zffut = umi__bcnl.find(naj__cgz)
        if hkkp__zffut == -1:
            raise BodoError(
                'DataFrame.to_parquet(): Unexpected metadata string for runtime columns.  Please return the DataFrame to regular Python to update typing information.'
                )
        nrqnp__utf = hkkp__zffut + len(naj__cgz)
        dgmbb__jdni = umi__bcnl[:nrqnp__utf]
        umi__bcnl = umi__bcnl[nrqnp__utf:]
        nsyd__umspe = len(yms__mww['columns'])
    else:
        umi__bcnl = json.dumps(gen_pandas_parquet_metadata(df.columns, df.
            data, df.index, write_non_range_index_to_metadata,
            write_rangeindex_to_metadata, partition_cols=partition_cols,
            is_runtime_columns=False))
    if not is_overload_true(_is_parallel) and gbr__kfw:
        umi__bcnl = umi__bcnl.replace('"%d"', '%d')
        if df.index.name == 'RangeIndexType(none)':
            umi__bcnl = umi__bcnl.replace('"%s"', '%s')
    if not df.is_table_format:
        zpla__lztor = ', '.join(
            'array_to_info(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}))'
            .format(i) for i in range(len(df.columns)))
    zlyfx__nnvh = """def df_to_parquet(df, fname, engine='auto', compression='snappy', index=None, partition_cols=None, storage_options=None, _is_parallel=False):
"""
    if df.is_table_format:
        zlyfx__nnvh += '    py_table = get_dataframe_table(df)\n'
        zlyfx__nnvh += (
            '    table = py_table_to_cpp_table(py_table, py_table_typ)\n')
    else:
        zlyfx__nnvh += '    info_list = [{}]\n'.format(zpla__lztor)
        zlyfx__nnvh += '    table = arr_info_list_to_table(info_list)\n'
    if df.has_runtime_cols:
        zlyfx__nnvh += '    columns_index = get_dataframe_column_names(df)\n'
        zlyfx__nnvh += '    names_arr = index_to_array(columns_index)\n'
        zlyfx__nnvh += '    col_names = array_to_info(names_arr)\n'
    else:
        zlyfx__nnvh += '    col_names = array_to_info(col_names_arr)\n'
    if is_overload_true(index) or is_overload_none(index) and hon__dvqrp:
        zlyfx__nnvh += """    index_col = array_to_info(index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)))
"""
        cakh__pyf = True
    else:
        zlyfx__nnvh += '    index_col = array_to_info(np.empty(0))\n'
        cakh__pyf = False
    if df.has_runtime_cols:
        zlyfx__nnvh += '    columns_lst = []\n'
        zlyfx__nnvh += '    num_cols = 0\n'
        for i in range(len(df.runtime_data_types)):
            zlyfx__nnvh += f'    for _ in range(len(py_table.block_{i})):\n'
            zlyfx__nnvh += f"""        columns_lst.append({hxul__qdr[i]!r}.replace('{{0}}', '"' + names_arr[num_cols] + '"'))
"""
            zlyfx__nnvh += '        num_cols += 1\n'
        if nsyd__umspe:
            zlyfx__nnvh += "    columns_lst.append('')\n"
        zlyfx__nnvh += '    columns_str = ", ".join(columns_lst)\n'
        zlyfx__nnvh += ('    metadata = """' + dgmbb__jdni +
            '""" + columns_str + """' + umi__bcnl + '"""\n')
    else:
        zlyfx__nnvh += '    metadata = """' + umi__bcnl + '"""\n'
    zlyfx__nnvh += '    if compression is None:\n'
    zlyfx__nnvh += "        compression = 'none'\n"
    zlyfx__nnvh += '    if df.index.name is not None:\n'
    zlyfx__nnvh += '        name_ptr = df.index.name\n'
    zlyfx__nnvh += '    else:\n'
    zlyfx__nnvh += "        name_ptr = 'null'\n"
    zlyfx__nnvh += f"""    bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel=_is_parallel)
"""
    xfsua__zovp = None
    if partition_cols:
        xfsua__zovp = pd.array([col_name for col_name in df.columns if 
            col_name not in partition_cols])
        bqjr__qqcqy = ', '.join(
            f'array_to_info(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).dtype.categories.values)'
             for i in range(len(df.columns)) if isinstance(df.data[i],
            CategoricalArrayType) and i in rfez__pfgcx)
        if bqjr__qqcqy:
            zlyfx__nnvh += '    cat_info_list = [{}]\n'.format(bqjr__qqcqy)
            zlyfx__nnvh += (
                '    cat_table = arr_info_list_to_table(cat_info_list)\n')
        else:
            zlyfx__nnvh += '    cat_table = table\n'
        zlyfx__nnvh += (
            '    col_names_no_partitions = array_to_info(col_names_no_parts_arr)\n'
            )
        zlyfx__nnvh += (
            f'    part_cols_idxs = np.array({rfez__pfgcx}, dtype=np.int32)\n')
        zlyfx__nnvh += (
            '    parquet_write_table_partitioned_cpp(unicode_to_utf8(fname),\n'
            )
        zlyfx__nnvh += """                            table, col_names, col_names_no_partitions, cat_table,
"""
        zlyfx__nnvh += (
            '                            part_cols_idxs.ctypes, len(part_cols_idxs),\n'
            )
        zlyfx__nnvh += (
            '                            unicode_to_utf8(compression),\n')
        zlyfx__nnvh += '                            _is_parallel,\n'
        zlyfx__nnvh += (
            '                            unicode_to_utf8(bucket_region))\n')
        zlyfx__nnvh += '    delete_table_decref_arrays(table)\n'
        zlyfx__nnvh += '    delete_info_decref_array(index_col)\n'
        zlyfx__nnvh += (
            '    delete_info_decref_array(col_names_no_partitions)\n')
        zlyfx__nnvh += '    delete_info_decref_array(col_names)\n'
        if bqjr__qqcqy:
            zlyfx__nnvh += '    delete_table_decref_arrays(cat_table)\n'
    elif write_rangeindex_to_metadata:
        zlyfx__nnvh += '    parquet_write_table_cpp(unicode_to_utf8(fname),\n'
        zlyfx__nnvh += (
            '                            table, col_names, index_col,\n')
        zlyfx__nnvh += '                            ' + str(cakh__pyf) + ',\n'
        zlyfx__nnvh += (
            '                            unicode_to_utf8(metadata),\n')
        zlyfx__nnvh += (
            '                            unicode_to_utf8(compression),\n')
        zlyfx__nnvh += (
            '                            _is_parallel, 1, df.index.start,\n')
        zlyfx__nnvh += (
            '                            df.index.stop, df.index.step,\n')
        zlyfx__nnvh += (
            '                            unicode_to_utf8(name_ptr),\n')
        zlyfx__nnvh += (
            '                            unicode_to_utf8(bucket_region))\n')
        zlyfx__nnvh += '    delete_table_decref_arrays(table)\n'
        zlyfx__nnvh += '    delete_info_decref_array(index_col)\n'
        zlyfx__nnvh += '    delete_info_decref_array(col_names)\n'
    else:
        zlyfx__nnvh += '    parquet_write_table_cpp(unicode_to_utf8(fname),\n'
        zlyfx__nnvh += (
            '                            table, col_names, index_col,\n')
        zlyfx__nnvh += '                            ' + str(cakh__pyf) + ',\n'
        zlyfx__nnvh += (
            '                            unicode_to_utf8(metadata),\n')
        zlyfx__nnvh += (
            '                            unicode_to_utf8(compression),\n')
        zlyfx__nnvh += (
            '                            _is_parallel, 0, 0, 0, 0,\n')
        zlyfx__nnvh += (
            '                            unicode_to_utf8(name_ptr),\n')
        zlyfx__nnvh += (
            '                            unicode_to_utf8(bucket_region))\n')
        zlyfx__nnvh += '    delete_table_decref_arrays(table)\n'
        zlyfx__nnvh += '    delete_info_decref_array(index_col)\n'
        zlyfx__nnvh += '    delete_info_decref_array(col_names)\n'
    dsp__znd = {}
    if df.has_runtime_cols:
        hem__xrq = None
    else:
        for wruo__kdlu in df.columns:
            if not isinstance(wruo__kdlu, str):
                raise BodoError(
                    'DataFrame.to_parquet(): parquet must have string column names'
                    )
        hem__xrq = pd.array(df.columns)
    exec(zlyfx__nnvh, {'np': np, 'bodo': bodo, 'unicode_to_utf8':
        unicode_to_utf8, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table,
        'str_arr_from_sequence': str_arr_from_sequence,
        'parquet_write_table_cpp': parquet_write_table_cpp,
        'parquet_write_table_partitioned_cpp':
        parquet_write_table_partitioned_cpp, 'index_to_array':
        index_to_array, 'delete_info_decref_array':
        delete_info_decref_array, 'delete_table_decref_arrays':
        delete_table_decref_arrays, 'col_names_arr': hem__xrq,
        'py_table_to_cpp_table': py_table_to_cpp_table, 'py_table_typ': df.
        table_type, 'get_dataframe_table': get_dataframe_table,
        'col_names_no_parts_arr': xfsua__zovp, 'get_dataframe_column_names':
        get_dataframe_column_names, 'fix_arr_dtype': fix_arr_dtype,
        'decode_if_dict_array': decode_if_dict_array,
        'decode_if_dict_table': decode_if_dict_table}, dsp__znd)
    bpvj__ypnt = dsp__znd['df_to_parquet']
    return bpvj__ypnt


def to_sql_exception_guard(df, name, con, schema=None, if_exists='fail',
    index=True, index_label=None, chunksize=None, dtype=None, method=None,
    _is_table_create=False, _is_parallel=False):
    zlq__imopt = 'all_ok'
    clzjy__xbh = urlparse(con).scheme
    if _is_parallel and bodo.get_rank() == 0:
        bncwg__eqe = 100
        if chunksize is None:
            zhj__kvglu = bncwg__eqe
        else:
            zhj__kvglu = min(chunksize, bncwg__eqe)
        if _is_table_create:
            df = df.iloc[:zhj__kvglu, :]
        else:
            df = df.iloc[zhj__kvglu:, :]
            if len(df) == 0:
                return zlq__imopt
    if clzjy__xbh == 'snowflake':
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
            df.columns = [(htcp__ynkuq.upper() if htcp__ynkuq.islower() else
                htcp__ynkuq) for htcp__ynkuq in df.columns]
        except ImportError as fyyet__jdg:
            zlq__imopt = (
                "Snowflake Python connector packages not found. Using 'to_sql' with Snowflake requires both snowflake-sqlalchemy and snowflake-connector-python. These can be installed by calling 'conda install -c conda-forge snowflake-sqlalchemy snowflake-connector-python' or 'pip install snowflake-sqlalchemy snowflake-connector-python'."
                )
            return zlq__imopt
    try:
        df.to_sql(name, con, schema, if_exists, index, index_label,
            chunksize, dtype, method)
    except Exception as wupt__ovq:
        zlq__imopt = wupt__ovq.args[0]
    return zlq__imopt


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
        xqvml__vfgr = bodo.libs.distributed_api.get_rank()
        zlq__imopt = 'unset'
        if xqvml__vfgr != 0:
            zlq__imopt = bcast_scalar(zlq__imopt)
        elif xqvml__vfgr == 0:
            zlq__imopt = to_sql_exception_guard_encaps(df, name, con,
                schema, if_exists, index, index_label, chunksize, dtype,
                method, True, _is_parallel)
            zlq__imopt = bcast_scalar(zlq__imopt)
        if_exists = 'append'
        if _is_parallel and zlq__imopt == 'all_ok':
            zlq__imopt = to_sql_exception_guard_encaps(df, name, con,
                schema, if_exists, index, index_label, chunksize, dtype,
                method, False, _is_parallel)
        if zlq__imopt != 'all_ok':
            print('err_msg=', zlq__imopt)
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
        krpm__dirt = get_overload_const_str(path_or_buf)
        if krpm__dirt.endswith(('.gz', '.bz2', '.zip', '.xz')):
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
        ysb__hdxz = bodo.io.fs_io.get_s3_bucket_region_njit(path_or_buf,
            parallel=False)
        if lines and orient == 'records':
            bodo.hiframes.pd_dataframe_ext._json_write(unicode_to_utf8(
                path_or_buf), unicode_to_utf8(D), 0, len(D), False, True,
                unicode_to_utf8(ysb__hdxz))
            bodo.utils.utils.check_and_propagate_cpp_exception()
        else:
            bodo.hiframes.pd_dataframe_ext._json_write(unicode_to_utf8(
                path_or_buf), unicode_to_utf8(D), 0, len(D), False, False,
                unicode_to_utf8(ysb__hdxz))
            bodo.utils.utils.check_and_propagate_cpp_exception()
    return _impl


@overload(pd.get_dummies, inline='always', no_unliteral=True)
def get_dummies(data, prefix=None, prefix_sep='_', dummy_na=False, columns=
    None, sparse=False, drop_first=False, dtype=None):
    qmbp__segg = {'prefix': prefix, 'prefix_sep': prefix_sep, 'dummy_na':
        dummy_na, 'columns': columns, 'sparse': sparse, 'drop_first':
        drop_first, 'dtype': dtype}
    hxaw__hxany = {'prefix': None, 'prefix_sep': '_', 'dummy_na': False,
        'columns': None, 'sparse': False, 'drop_first': False, 'dtype': None}
    check_unsupported_args('pandas.get_dummies', qmbp__segg, hxaw__hxany,
        package_name='pandas', module_name='General')
    if not categorical_can_construct_dataframe(data):
        raise BodoError(
            'pandas.get_dummies() only support categorical data types with explicitly known categories'
            )
    zlyfx__nnvh = """def impl(data, prefix=None, prefix_sep='_', dummy_na=False, columns=None, sparse=False, drop_first=False, dtype=None,):
"""
    if isinstance(data, SeriesType):
        sewp__bzmeo = data.data.dtype.categories
        zlyfx__nnvh += (
            '  data_values = bodo.hiframes.pd_series_ext.get_series_data(data)\n'
            )
    else:
        sewp__bzmeo = data.dtype.categories
        zlyfx__nnvh += '  data_values = data\n'
    apbut__caxw = len(sewp__bzmeo)
    zlyfx__nnvh += """  codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(data_values)
"""
    zlyfx__nnvh += '  numba.parfors.parfor.init_prange()\n'
    zlyfx__nnvh += '  n = len(data_values)\n'
    for i in range(apbut__caxw):
        zlyfx__nnvh += '  data_arr_{} = np.empty(n, np.uint8)\n'.format(i)
    zlyfx__nnvh += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    zlyfx__nnvh += '      if bodo.libs.array_kernels.isna(data_values, i):\n'
    for aepqy__mdmkv in range(apbut__caxw):
        zlyfx__nnvh += '          data_arr_{}[i] = 0\n'.format(aepqy__mdmkv)
    zlyfx__nnvh += '      else:\n'
    for jsois__argt in range(apbut__caxw):
        zlyfx__nnvh += '          data_arr_{0}[i] = codes[i] == {0}\n'.format(
            jsois__argt)
    zpla__lztor = ', '.join(f'data_arr_{i}' for i in range(apbut__caxw))
    index = 'bodo.hiframes.pd_index_ext.init_range_index(0, n, 1, None)'
    if isinstance(sewp__bzmeo[0], np.datetime64):
        sewp__bzmeo = tuple(pd.Timestamp(htcp__ynkuq) for htcp__ynkuq in
            sewp__bzmeo)
    elif isinstance(sewp__bzmeo[0], np.timedelta64):
        sewp__bzmeo = tuple(pd.Timedelta(htcp__ynkuq) for htcp__ynkuq in
            sewp__bzmeo)
    return bodo.hiframes.dataframe_impl._gen_init_df(zlyfx__nnvh,
        sewp__bzmeo, zpla__lztor, index)


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
    for hmvyx__wahx in pd_unsupported:
        fname = mod_name + '.' + hmvyx__wahx.__name__
        overload(hmvyx__wahx, no_unliteral=True)(create_unsupported_overload
            (fname))


def _install_dataframe_unsupported():
    for ruog__klsc in dataframe_unsupported_attrs:
        ypomm__muec = 'DataFrame.' + ruog__klsc
        overload_attribute(DataFrameType, ruog__klsc)(
            create_unsupported_overload(ypomm__muec))
    for fname in dataframe_unsupported:
        ypomm__muec = 'DataFrame.' + fname + '()'
        overload_method(DataFrameType, fname)(create_unsupported_overload(
            ypomm__muec))


_install_pd_unsupported('pandas', pd_unsupported)
_install_pd_unsupported('pandas.util', pd_util_unsupported)
_install_dataframe_unsupported()
