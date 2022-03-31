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
            ltvb__itaq = f'{len(self.data)} columns of types {set(self.data)}'
            yofdm__mejtb = (
                f"('{self.columns[0]}', '{self.columns[1]}', ..., '{self.columns[-1]}')"
                )
            return (
                f'dataframe({ltvb__itaq}, {self.index}, {yofdm__mejtb}, {self.dist}, {self.is_table_format})'
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
            tlna__netdd = (self.index if self.index == other.index else
                self.index.unify(typingctx, other.index))
            data = tuple(izkh__ufk.unify(typingctx, lpgj__nqbfq) if 
                izkh__ufk != lpgj__nqbfq else izkh__ufk for izkh__ufk,
                lpgj__nqbfq in zip(self.data, other.data))
            dist = Distribution(min(self.dist.value, other.dist.value))
            if tlna__netdd is not None and None not in data:
                return DataFrameType(data, tlna__netdd, self.columns, dist,
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
        return all(izkh__ufk.is_precise() for izkh__ufk in self.data
            ) and self.index.is_precise()

    def replace_col_type(self, col_name, new_type):
        if col_name not in self.columns:
            raise ValueError(
                f"DataFrameType.replace_col_type replaced column must be found in the DataFrameType. '{col_name}' not found in DataFrameType with columns {self.columns}"
                )
        thpy__kmss = self.columns.index(col_name)
        torgi__shps = tuple(list(self.data[:thpy__kmss]) + [new_type] +
            list(self.data[thpy__kmss + 1:]))
        return DataFrameType(torgi__shps, self.index, self.columns, self.
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
        zzwtj__stwa = [('data', data_typ), ('index', fe_type.df_type.index),
            ('parent', types.pyobject)]
        if fe_type.df_type.has_runtime_cols:
            zzwtj__stwa.append(('columns', fe_type.df_type.runtime_colname_typ)
                )
        super(DataFramePayloadModel, self).__init__(dmm, fe_type, zzwtj__stwa)


@register_model(DataFrameType)
class DataFrameModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = DataFramePayloadType(fe_type)
        zzwtj__stwa = [('meminfo', types.MemInfoPointer(payload_type)), (
            'parent', types.pyobject)]
        super(DataFrameModel, self).__init__(dmm, fe_type, zzwtj__stwa)


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
        hzkl__cux = 'n',
        xtocr__kkfz = {'n': 5}
        uclgf__pls, yjo__sbpi = bodo.utils.typing.fold_typing_args(func_name,
            args, kws, hzkl__cux, xtocr__kkfz)
        uhrsu__pmam = yjo__sbpi[0]
        if not is_overload_int(uhrsu__pmam):
            raise BodoError(f"{func_name}(): 'n' must be an Integer")
        uvcm__rwvj = df.copy(is_table_format=False)
        return uvcm__rwvj(*yjo__sbpi).replace(pysig=uclgf__pls)

    @bound_function('df.corr')
    def resolve_corr(self, df, args, kws):
        func_name = 'DataFrame.corr'
        check_runtime_cols_unsupported(df, f'{func_name}()')
        jga__uja = (df,) + args
        hzkl__cux = 'df', 'method', 'min_periods'
        xtocr__kkfz = {'method': 'pearson', 'min_periods': 1}
        ojwnp__osurv = 'method',
        uclgf__pls, yjo__sbpi = bodo.utils.typing.fold_typing_args(func_name,
            jga__uja, kws, hzkl__cux, xtocr__kkfz, ojwnp__osurv)
        naxcf__tevyd = yjo__sbpi[2]
        if not is_overload_int(naxcf__tevyd):
            raise BodoError(f"{func_name}(): 'min_periods' must be an Integer")
        shsw__apxst = []
        jvs__bzkt = []
        for twp__cwjmx, nhya__mhsr in zip(df.columns, df.data):
            if bodo.utils.typing._is_pandas_numeric_dtype(nhya__mhsr.dtype):
                shsw__apxst.append(twp__cwjmx)
                jvs__bzkt.append(types.Array(types.float64, 1, 'A'))
        if len(shsw__apxst) == 0:
            raise_bodo_error('DataFrame.corr(): requires non-empty dataframe')
        jvs__bzkt = tuple(jvs__bzkt)
        shsw__apxst = tuple(shsw__apxst)
        index_typ = bodo.utils.typing.type_col_to_index(shsw__apxst)
        uvcm__rwvj = DataFrameType(jvs__bzkt, index_typ, shsw__apxst)
        return uvcm__rwvj(*yjo__sbpi).replace(pysig=uclgf__pls)

    @bound_function('df.pipe', no_unliteral=True)
    def resolve_pipe(self, df, args, kws):
        check_runtime_cols_unsupported(df, 'DataFrame.pipe()')
        return bodo.hiframes.pd_groupby_ext.resolve_obj_pipe(self, df, args,
            kws, 'DataFrame')

    @bound_function('df.apply', no_unliteral=True)
    def resolve_apply(self, df, args, kws):
        check_runtime_cols_unsupported(df, 'DataFrame.apply()')
        kws = dict(kws)
        cjcm__mclgg = args[0] if len(args) > 0 else kws.pop('func', None)
        axis = args[1] if len(args) > 1 else kws.pop('axis', types.literal(0))
        qkky__ijfy = args[2] if len(args) > 2 else kws.pop('raw', types.
            literal(False))
        hypi__jcw = args[3] if len(args) > 3 else kws.pop('result_type',
            types.none)
        ccx__zvb = args[4] if len(args) > 4 else kws.pop('args', types.
            Tuple([]))
        zhaar__ahwmy = dict(raw=qkky__ijfy, result_type=hypi__jcw)
        gti__rufvh = dict(raw=False, result_type=None)
        check_unsupported_args('Dataframe.apply', zhaar__ahwmy, gti__rufvh,
            package_name='pandas', module_name='DataFrame')
        mte__swp = True
        if types.unliteral(cjcm__mclgg) == types.unicode_type:
            if not is_overload_constant_str(cjcm__mclgg):
                raise BodoError(
                    f'DataFrame.apply(): string argument (for builtins) must be a compile time constant'
                    )
            mte__swp = False
        if not is_overload_constant_int(axis):
            raise BodoError(
                'Dataframe.apply(): axis argument must be a compile time constant.'
                )
        zqp__fvdy = get_overload_const_int(axis)
        if mte__swp and zqp__fvdy != 1:
            raise BodoError(
                'Dataframe.apply(): only axis=1 supported for user-defined functions'
                )
        elif zqp__fvdy not in (0, 1):
            raise BodoError('Dataframe.apply(): axis must be either 0 or 1')
        qcc__gavr = []
        for arr_typ in df.data:
            prpe__vlrnw = SeriesType(arr_typ.dtype, arr_typ, df.index,
                string_type)
            sibp__omy = self.context.resolve_function_type(operator.getitem,
                (SeriesIlocType(prpe__vlrnw), types.int64), {}).return_type
            qcc__gavr.append(sibp__omy)
        fniw__iwfwx = types.none
        qplm__odbic = HeterogeneousIndexType(types.BaseTuple.from_types(
            tuple(types.literal(twp__cwjmx) for twp__cwjmx in df.columns)),
            None)
        bpxif__nwvdd = types.BaseTuple.from_types(qcc__gavr)
        tsjr__yrj = df.index.dtype
        if tsjr__yrj == types.NPDatetime('ns'):
            tsjr__yrj = bodo.pd_timestamp_type
        if tsjr__yrj == types.NPTimedelta('ns'):
            tsjr__yrj = bodo.pd_timedelta_type
        if is_heterogeneous_tuple_type(bpxif__nwvdd):
            cldo__rae = HeterogeneousSeriesType(bpxif__nwvdd, qplm__odbic,
                tsjr__yrj)
        else:
            cldo__rae = SeriesType(bpxif__nwvdd.dtype, bpxif__nwvdd,
                qplm__odbic, tsjr__yrj)
        pdj__qjmk = cldo__rae,
        if ccx__zvb is not None:
            pdj__qjmk += tuple(ccx__zvb.types)
        try:
            if not mte__swp:
                kundk__aen = bodo.utils.transform.get_udf_str_return_type(df,
                    get_overload_const_str(cjcm__mclgg), self.context,
                    'DataFrame.apply', axis if zqp__fvdy == 1 else None)
            else:
                kundk__aen = get_const_func_output_type(cjcm__mclgg,
                    pdj__qjmk, kws, self.context, numba.core.registry.
                    cpu_target.target_context)
        except Exception as jrqxn__saypg:
            raise_bodo_error(get_udf_error_msg('DataFrame.apply()',
                jrqxn__saypg))
        if mte__swp:
            if not (is_overload_constant_int(axis) and 
                get_overload_const_int(axis) == 1):
                raise BodoError(
                    'Dataframe.apply(): only user-defined functions with axis=1 supported'
                    )
            if isinstance(kundk__aen, (SeriesType, HeterogeneousSeriesType)
                ) and kundk__aen.const_info is None:
                raise BodoError(
                    'Invalid Series output in UDF (Series with constant length and constant Index value expected)'
                    )
            if isinstance(kundk__aen, HeterogeneousSeriesType):
                pkgco__seop, knno__ytt = kundk__aen.const_info
                jcggj__rwrk = tuple(dtype_to_array_type(rskso__itevd) for
                    rskso__itevd in kundk__aen.data.types)
                yvv__siokz = DataFrameType(jcggj__rwrk, df.index, knno__ytt)
            elif isinstance(kundk__aen, SeriesType):
                mbdx__zpxsp, knno__ytt = kundk__aen.const_info
                jcggj__rwrk = tuple(dtype_to_array_type(kundk__aen.dtype) for
                    pkgco__seop in range(mbdx__zpxsp))
                yvv__siokz = DataFrameType(jcggj__rwrk, df.index, knno__ytt)
            else:
                crrc__iqnc = get_udf_out_arr_type(kundk__aen)
                yvv__siokz = SeriesType(crrc__iqnc.dtype, crrc__iqnc, df.
                    index, None)
        else:
            yvv__siokz = kundk__aen
        fmzom__ttj = ', '.join("{} = ''".format(izkh__ufk) for izkh__ufk in
            kws.keys())
        quscx__gktco = f"""def apply_stub(func, axis=0, raw=False, result_type=None, args=(), {fmzom__ttj}):
"""
        quscx__gktco += '    pass\n'
        erl__khvv = {}
        exec(quscx__gktco, {}, erl__khvv)
        bsho__mvlpj = erl__khvv['apply_stub']
        uclgf__pls = numba.core.utils.pysignature(bsho__mvlpj)
        pszsd__mmci = (cjcm__mclgg, axis, qkky__ijfy, hypi__jcw, ccx__zvb
            ) + tuple(kws.values())
        return signature(yvv__siokz, *pszsd__mmci).replace(pysig=uclgf__pls)

    @bound_function('df.plot', no_unliteral=True)
    def resolve_plot(self, df, args, kws):
        func_name = 'DataFrame.plot'
        check_runtime_cols_unsupported(df, f'{func_name}()')
        hzkl__cux = ('x', 'y', 'kind', 'figsize', 'ax', 'subplots',
            'sharex', 'sharey', 'layout', 'use_index', 'title', 'grid',
            'legend', 'style', 'logx', 'logy', 'loglog', 'xticks', 'yticks',
            'xlim', 'ylim', 'rot', 'fontsize', 'colormap', 'table', 'yerr',
            'xerr', 'secondary_y', 'sort_columns', 'xlabel', 'ylabel',
            'position', 'stacked', 'mark_right', 'include_bool', 'backend')
        xtocr__kkfz = {'x': None, 'y': None, 'kind': 'line', 'figsize':
            None, 'ax': None, 'subplots': False, 'sharex': None, 'sharey': 
            False, 'layout': None, 'use_index': True, 'title': None, 'grid':
            None, 'legend': True, 'style': None, 'logx': False, 'logy': 
            False, 'loglog': False, 'xticks': None, 'yticks': None, 'xlim':
            None, 'ylim': None, 'rot': None, 'fontsize': None, 'colormap':
            None, 'table': False, 'yerr': None, 'xerr': None, 'secondary_y':
            False, 'sort_columns': False, 'xlabel': None, 'ylabel': None,
            'position': 0.5, 'stacked': False, 'mark_right': True,
            'include_bool': False, 'backend': None}
        ojwnp__osurv = ('subplots', 'sharex', 'sharey', 'layout',
            'use_index', 'grid', 'style', 'logx', 'logy', 'loglog', 'xlim',
            'ylim', 'rot', 'colormap', 'table', 'yerr', 'xerr',
            'sort_columns', 'secondary_y', 'colorbar', 'position',
            'stacked', 'mark_right', 'include_bool', 'backend')
        uclgf__pls, yjo__sbpi = bodo.utils.typing.fold_typing_args(func_name,
            args, kws, hzkl__cux, xtocr__kkfz, ojwnp__osurv)
        vbmj__fpfql = yjo__sbpi[2]
        if not is_overload_constant_str(vbmj__fpfql):
            raise BodoError(
                f"{func_name}: kind must be a constant string and one of ('line', 'scatter')."
                )
        dxfd__ixcyv = yjo__sbpi[0]
        if not is_overload_none(dxfd__ixcyv) and not (is_overload_int(
            dxfd__ixcyv) or is_overload_constant_str(dxfd__ixcyv)):
            raise BodoError(
                f'{func_name}: x must be a constant column name, constant integer, or None.'
                )
        if is_overload_constant_str(dxfd__ixcyv):
            poyxl__rxvg = get_overload_const_str(dxfd__ixcyv)
            if poyxl__rxvg not in df.columns:
                raise BodoError(f'{func_name}: {poyxl__rxvg} column not found.'
                    )
        elif is_overload_int(dxfd__ixcyv):
            ezm__pxa = get_overload_const_int(dxfd__ixcyv)
            if ezm__pxa > len(df.columns):
                raise BodoError(
                    f'{func_name}: x: {ezm__pxa} is out of bounds for axis 0 with size {len(df.columns)}'
                    )
            dxfd__ixcyv = df.columns[dxfd__ixcyv]
        ftyx__jzo = yjo__sbpi[1]
        if not is_overload_none(ftyx__jzo) and not (is_overload_int(
            ftyx__jzo) or is_overload_constant_str(ftyx__jzo)):
            raise BodoError(
                'df.plot(): y must be a constant column name, constant integer, or None.'
                )
        if is_overload_constant_str(ftyx__jzo):
            mpsv__hfl = get_overload_const_str(ftyx__jzo)
            if mpsv__hfl not in df.columns:
                raise BodoError(f'{func_name}: {mpsv__hfl} column not found.')
        elif is_overload_int(ftyx__jzo):
            zie__nlas = get_overload_const_int(ftyx__jzo)
            if zie__nlas > len(df.columns):
                raise BodoError(
                    f'{func_name}: y: {zie__nlas} is out of bounds for axis 0 with size {len(df.columns)}'
                    )
            ftyx__jzo = df.columns[ftyx__jzo]
        dpt__berku = yjo__sbpi[3]
        if not is_overload_none(dpt__berku) and not is_tuple_like_type(
            dpt__berku):
            raise BodoError(
                f'{func_name}: figsize must be a constant numeric tuple (width, height) or None.'
                )
        bpyxl__kngc = yjo__sbpi[10]
        if not is_overload_none(bpyxl__kngc) and not is_overload_constant_str(
            bpyxl__kngc):
            raise BodoError(
                f'{func_name}: title must be a constant string or None.')
        gan__fcwu = yjo__sbpi[12]
        if not is_overload_bool(gan__fcwu):
            raise BodoError(f'{func_name}: legend must be a boolean type.')
        afxz__sliuw = yjo__sbpi[17]
        if not is_overload_none(afxz__sliuw) and not is_tuple_like_type(
            afxz__sliuw):
            raise BodoError(
                f'{func_name}: xticks must be a constant tuple or None.')
        sbjx__kywaj = yjo__sbpi[18]
        if not is_overload_none(sbjx__kywaj) and not is_tuple_like_type(
            sbjx__kywaj):
            raise BodoError(
                f'{func_name}: yticks must be a constant tuple or None.')
        wwsx__qae = yjo__sbpi[22]
        if not is_overload_none(wwsx__qae) and not is_overload_int(wwsx__qae):
            raise BodoError(
                f'{func_name}: fontsize must be an integer or None.')
        ltghb__rpisq = yjo__sbpi[29]
        if not is_overload_none(ltghb__rpisq) and not is_overload_constant_str(
            ltghb__rpisq):
            raise BodoError(
                f'{func_name}: xlabel must be a constant string or None.')
        cxro__hfwok = yjo__sbpi[30]
        if not is_overload_none(cxro__hfwok) and not is_overload_constant_str(
            cxro__hfwok):
            raise BodoError(
                f'{func_name}: ylabel must be a constant string or None.')
        mar__cwv = types.List(types.mpl_line_2d_type)
        vbmj__fpfql = get_overload_const_str(vbmj__fpfql)
        if vbmj__fpfql == 'scatter':
            if is_overload_none(dxfd__ixcyv) and is_overload_none(ftyx__jzo):
                raise BodoError(
                    f'{func_name}: {vbmj__fpfql} requires an x and y column.')
            elif is_overload_none(dxfd__ixcyv):
                raise BodoError(
                    f'{func_name}: {vbmj__fpfql} x column is missing.')
            elif is_overload_none(ftyx__jzo):
                raise BodoError(
                    f'{func_name}: {vbmj__fpfql} y column is missing.')
            mar__cwv = types.mpl_path_collection_type
        elif vbmj__fpfql != 'line':
            raise BodoError(
                f'{func_name}: {vbmj__fpfql} plot is not supported.')
        return signature(mar__cwv, *yjo__sbpi).replace(pysig=uclgf__pls)

    def generic_resolve(self, df, attr):
        if self._is_existing_attr(attr):
            return
        check_runtime_cols_unsupported(df,
            'Acessing DataFrame columns by attribute')
        if attr in df.columns:
            wwncr__eemc = df.columns.index(attr)
            arr_typ = df.data[wwncr__eemc]
            return SeriesType(arr_typ.dtype, arr_typ, df.index, types.
                StringLiteral(attr))
        if len(df.columns) > 0 and isinstance(df.columns[0], tuple):
            lpdxq__zbin = []
            torgi__shps = []
            tmpxx__jgye = False
            for i, sqnnt__ebrig in enumerate(df.columns):
                if sqnnt__ebrig[0] != attr:
                    continue
                tmpxx__jgye = True
                lpdxq__zbin.append(sqnnt__ebrig[1] if len(sqnnt__ebrig) == 
                    2 else sqnnt__ebrig[1:])
                torgi__shps.append(df.data[i])
            if tmpxx__jgye:
                return DataFrameType(tuple(torgi__shps), df.index, tuple(
                    lpdxq__zbin))


DataFrameAttribute._no_unliteral = True


@overload(operator.getitem, no_unliteral=True)
def namedtuple_getitem_overload(tup, idx):
    if isinstance(tup, types.BaseNamedTuple) and is_overload_constant_str(idx):
        mzzk__tmus = get_overload_const_str(idx)
        val_ind = tup.instance_class._fields.index(mzzk__tmus)
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
        dxo__jtg = builder.extract_value(payload.data, i)
        context.nrt.decref(builder, df_type.data[i], dxo__jtg)
    context.nrt.decref(builder, df_type.index, payload.index)


def define_df_dtor(context, builder, df_type, payload_type):
    pfw__sesq = builder.module
    gyy__mouhq = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    iny__mda = cgutils.get_or_insert_function(pfw__sesq, gyy__mouhq, name=
        '.dtor.df.{}'.format(df_type))
    if not iny__mda.is_declaration:
        return iny__mda
    iny__mda.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(iny__mda.append_basic_block())
    qljq__pzorj = iny__mda.args[0]
    jasua__ysz = context.get_value_type(payload_type).as_pointer()
    bmdnc__khg = builder.bitcast(qljq__pzorj, jasua__ysz)
    payload = context.make_helper(builder, payload_type, ref=bmdnc__khg)
    decref_df_data(context, builder, payload, df_type)
    has_parent = cgutils.is_not_null(builder, payload.parent)
    with builder.if_then(has_parent):
        hvpg__mcq = context.get_python_api(builder)
        mvbs__yai = hvpg__mcq.gil_ensure()
        hvpg__mcq.decref(payload.parent)
        hvpg__mcq.gil_release(mvbs__yai)
    builder.ret_void()
    return iny__mda


def construct_dataframe(context, builder, df_type, data_tup, index_val,
    parent=None, colnames=None):
    payload_type = DataFramePayloadType(df_type)
    wlzld__iuf = cgutils.create_struct_proxy(payload_type)(context, builder)
    wlzld__iuf.data = data_tup
    wlzld__iuf.index = index_val
    if colnames is not None:
        assert df_type.has_runtime_cols, 'construct_dataframe can only provide colnames if columns are determined at runtime'
        wlzld__iuf.columns = colnames
    afx__per = context.get_value_type(payload_type)
    lxu__ljtm = context.get_abi_sizeof(afx__per)
    wnpuo__rmvs = define_df_dtor(context, builder, df_type, payload_type)
    eqehz__vhzwi = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, lxu__ljtm), wnpuo__rmvs)
    nqku__ekuw = context.nrt.meminfo_data(builder, eqehz__vhzwi)
    qtcf__jjs = builder.bitcast(nqku__ekuw, afx__per.as_pointer())
    rrie__zdaoj = cgutils.create_struct_proxy(df_type)(context, builder)
    rrie__zdaoj.meminfo = eqehz__vhzwi
    if parent is None:
        rrie__zdaoj.parent = cgutils.get_null_value(rrie__zdaoj.parent.type)
    else:
        rrie__zdaoj.parent = parent
        wlzld__iuf.parent = parent
        has_parent = cgutils.is_not_null(builder, parent)
        with builder.if_then(has_parent):
            hvpg__mcq = context.get_python_api(builder)
            mvbs__yai = hvpg__mcq.gil_ensure()
            hvpg__mcq.incref(parent)
            hvpg__mcq.gil_release(mvbs__yai)
    builder.store(wlzld__iuf._getvalue(), qtcf__jjs)
    return rrie__zdaoj._getvalue()


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
        rltw__kpq = [data_typ.dtype.arr_types.dtype] * len(data_typ.dtype.
            arr_types)
    else:
        rltw__kpq = [rskso__itevd for rskso__itevd in data_typ.dtype.arr_types]
    pxzzj__xlf = DataFrameType(tuple(rltw__kpq + [colnames_index_typ]),
        index_typ, None, is_table_format=True)

    def codegen(context, builder, signature, args):
        df_type = signature.return_type
        data_tup, index, col_names = args
        parent = None
        ozvvk__fmcre = construct_dataframe(context, builder, df_type,
            data_tup, index, parent, col_names)
        context.nrt.incref(builder, data_typ, data_tup)
        context.nrt.incref(builder, index_typ, index)
        context.nrt.incref(builder, colnames_index_typ, col_names)
        return ozvvk__fmcre
    sig = signature(pxzzj__xlf, data_typ, index_typ, colnames_index_typ)
    return sig, codegen


@intrinsic
def init_dataframe(typingctx, data_tup_typ, index_typ, col_names_typ=None):
    assert is_pd_index_type(index_typ) or isinstance(index_typ, MultiIndexType
        ), 'init_dataframe(): invalid index type'
    mbdx__zpxsp = len(data_tup_typ.types)
    if mbdx__zpxsp == 0:
        column_names = ()
    elif isinstance(col_names_typ, types.TypeRef):
        column_names = col_names_typ.instance_type.columns
    else:
        column_names = get_const_tup_vals(col_names_typ)
    if mbdx__zpxsp == 1 and isinstance(data_tup_typ.types[0], TableType):
        mbdx__zpxsp = len(data_tup_typ.types[0].arr_types)
    assert len(column_names
        ) == mbdx__zpxsp, 'init_dataframe(): number of column names does not match number of columns'
    is_table_format = False
    eoukz__odxg = data_tup_typ.types
    if mbdx__zpxsp != 0 and isinstance(data_tup_typ.types[0], TableType):
        eoukz__odxg = data_tup_typ.types[0].arr_types
        is_table_format = True
    pxzzj__xlf = DataFrameType(eoukz__odxg, index_typ, column_names,
        is_table_format=is_table_format)

    def codegen(context, builder, signature, args):
        df_type = signature.return_type
        data_tup = args[0]
        index_val = args[1]
        parent = None
        if is_table_format:
            nvool__ocz = cgutils.create_struct_proxy(pxzzj__xlf.table_type)(
                context, builder, builder.extract_value(data_tup, 0))
            parent = nvool__ocz.parent
        ozvvk__fmcre = construct_dataframe(context, builder, df_type,
            data_tup, index_val, parent, None)
        context.nrt.incref(builder, data_tup_typ, data_tup)
        context.nrt.incref(builder, index_typ, index_val)
        return ozvvk__fmcre
    sig = signature(pxzzj__xlf, data_tup_typ, index_typ, col_names_typ)
    return sig, codegen


@intrinsic
def has_parent(typingctx, df=None):
    check_runtime_cols_unsupported(df, 'has_parent')

    def codegen(context, builder, sig, args):
        rrie__zdaoj = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        return cgutils.is_not_null(builder, rrie__zdaoj.parent)
    return signature(types.bool_, df), codegen


@intrinsic
def _column_needs_unboxing(typingctx, df_typ, i_typ=None):
    check_runtime_cols_unsupported(df_typ, '_column_needs_unboxing')
    assert isinstance(df_typ, DataFrameType) and is_overload_constant_int(i_typ
        )

    def codegen(context, builder, sig, args):
        wlzld__iuf = get_dataframe_payload(context, builder, df_typ, args[0])
        pfa__pmko = get_overload_const_int(i_typ)
        arr_typ = df_typ.data[pfa__pmko]
        if df_typ.is_table_format:
            nvool__ocz = cgutils.create_struct_proxy(df_typ.table_type)(context
                , builder, builder.extract_value(wlzld__iuf.data, 0))
            wfbx__shdi = df_typ.table_type.type_to_blk[arr_typ]
            epjr__zyzks = getattr(nvool__ocz, f'block_{wfbx__shdi}')
            zqex__ofat = ListInstance(context, builder, types.List(arr_typ),
                epjr__zyzks)
            mllv__jdgn = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[pfa__pmko])
            dxo__jtg = zqex__ofat.getitem(mllv__jdgn)
        else:
            dxo__jtg = builder.extract_value(wlzld__iuf.data, pfa__pmko)
        kpspg__kovpp = cgutils.alloca_once_value(builder, dxo__jtg)
        wwqxb__bwn = cgutils.alloca_once_value(builder, context.
            get_constant_null(arr_typ))
        return is_ll_eq(builder, kpspg__kovpp, wwqxb__bwn)
    return signature(types.bool_, df_typ, i_typ), codegen


def get_dataframe_payload(context, builder, df_type, value):
    eqehz__vhzwi = cgutils.create_struct_proxy(df_type)(context, builder, value
        ).meminfo
    payload_type = DataFramePayloadType(df_type)
    payload = context.nrt.meminfo_data(builder, eqehz__vhzwi)
    jasua__ysz = context.get_value_type(payload_type).as_pointer()
    payload = builder.bitcast(payload, jasua__ysz)
    return context.make_helper(builder, payload_type, ref=payload)


@intrinsic
def _get_dataframe_data(typingctx, df_typ=None):
    check_runtime_cols_unsupported(df_typ, '_get_dataframe_data')
    pxzzj__xlf = types.Tuple(df_typ.data)
    if df_typ.is_table_format:
        pxzzj__xlf = types.Tuple([TableType(df_typ.data)])
    sig = signature(pxzzj__xlf, df_typ)

    def codegen(context, builder, signature, args):
        wlzld__iuf = get_dataframe_payload(context, builder, signature.args
            [0], args[0])
        return impl_ret_borrowed(context, builder, signature.return_type,
            wlzld__iuf.data)
    return sig, codegen


@intrinsic
def get_dataframe_index(typingctx, df_typ=None):

    def codegen(context, builder, signature, args):
        wlzld__iuf = get_dataframe_payload(context, builder, signature.args
            [0], args[0])
        return impl_ret_borrowed(context, builder, df_typ.index, wlzld__iuf
            .index)
    pxzzj__xlf = df_typ.index
    sig = signature(pxzzj__xlf, df_typ)
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
        uvcm__rwvj = df.data[i]
        return uvcm__rwvj(*args)


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
        wlzld__iuf = get_dataframe_payload(context, builder, signature.args
            [0], args[0])
        return impl_ret_borrowed(context, builder, df_typ.table_type,
            builder.extract_value(wlzld__iuf.data, 0))
    return df_typ.table_type(df_typ), codegen


@intrinsic
def get_dataframe_column_names(typingctx, df_typ=None):
    assert df_typ.has_runtime_cols, 'get_dataframe_column_names() expects columns to be determined at runtime'

    def codegen(context, builder, signature, args):
        wlzld__iuf = get_dataframe_payload(context, builder, signature.args
            [0], args[0])
        return impl_ret_borrowed(context, builder, df_typ.
            runtime_colname_typ, wlzld__iuf.columns)
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
    bpxif__nwvdd = self.typemap[data_tup.name]
    if any(is_tuple_like_type(rskso__itevd) for rskso__itevd in
        bpxif__nwvdd.types):
        return None
    if equiv_set.has_shape(data_tup):
        qwitn__yth = equiv_set.get_shape(data_tup)
        if len(qwitn__yth) > 1:
            equiv_set.insert_equiv(*qwitn__yth)
        if len(qwitn__yth) > 0:
            qplm__odbic = self.typemap[index.name]
            if not isinstance(qplm__odbic, HeterogeneousIndexType
                ) and equiv_set.has_shape(index):
                equiv_set.insert_equiv(qwitn__yth[0], index)
            return ArrayAnalysis.AnalyzeResult(shape=(qwitn__yth[0], len(
                qwitn__yth)), pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_dataframe_ext_init_dataframe
    ) = init_dataframe_equiv


def get_dataframe_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    itzo__qblim = args[0]
    data_types = self.typemap[itzo__qblim.name].data
    if any(is_tuple_like_type(rskso__itevd) for rskso__itevd in data_types):
        return None
    if equiv_set.has_shape(itzo__qblim):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            itzo__qblim)[0], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_data
    ) = get_dataframe_data_equiv


def get_dataframe_index_equiv(self, scope, equiv_set, loc, args, kws):
    from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
    assert len(args) == 1 and not kws
    itzo__qblim = args[0]
    qplm__odbic = self.typemap[itzo__qblim.name].index
    if isinstance(qplm__odbic, HeterogeneousIndexType):
        return None
    if equiv_set.has_shape(itzo__qblim):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            itzo__qblim)[0], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_index
    ) = get_dataframe_index_equiv


def get_dataframe_table_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    itzo__qblim = args[0]
    if equiv_set.has_shape(itzo__qblim):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            itzo__qblim), pre=[])


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_table
    ) = get_dataframe_table_equiv


def get_dataframe_column_names_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    itzo__qblim = args[0]
    if equiv_set.has_shape(itzo__qblim):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            itzo__qblim)[1], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_column_names
    ) = get_dataframe_column_names_equiv


@intrinsic
def set_dataframe_data(typingctx, df_typ, c_ind_typ, arr_typ=None):
    check_runtime_cols_unsupported(df_typ, 'set_dataframe_data')
    assert is_overload_constant_int(c_ind_typ)
    pfa__pmko = get_overload_const_int(c_ind_typ)
    if df_typ.data[pfa__pmko] != arr_typ:
        raise BodoError(
            'Changing dataframe column data type inplace is not supported in conditionals/loops or for dataframe arguments'
            )

    def codegen(context, builder, signature, args):
        udfa__axivr, pkgco__seop, oebx__alp = args
        wlzld__iuf = get_dataframe_payload(context, builder, df_typ,
            udfa__axivr)
        if df_typ.is_table_format:
            nvool__ocz = cgutils.create_struct_proxy(df_typ.table_type)(context
                , builder, builder.extract_value(wlzld__iuf.data, 0))
            wfbx__shdi = df_typ.table_type.type_to_blk[arr_typ]
            epjr__zyzks = getattr(nvool__ocz, f'block_{wfbx__shdi}')
            zqex__ofat = ListInstance(context, builder, types.List(arr_typ),
                epjr__zyzks)
            mllv__jdgn = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[pfa__pmko])
            zqex__ofat.setitem(mllv__jdgn, oebx__alp, True)
        else:
            dxo__jtg = builder.extract_value(wlzld__iuf.data, pfa__pmko)
            context.nrt.decref(builder, df_typ.data[pfa__pmko], dxo__jtg)
            wlzld__iuf.data = builder.insert_value(wlzld__iuf.data,
                oebx__alp, pfa__pmko)
            context.nrt.incref(builder, arr_typ, oebx__alp)
        rrie__zdaoj = cgutils.create_struct_proxy(df_typ)(context, builder,
            value=udfa__axivr)
        payload_type = DataFramePayloadType(df_typ)
        bmdnc__khg = context.nrt.meminfo_data(builder, rrie__zdaoj.meminfo)
        jasua__ysz = context.get_value_type(payload_type).as_pointer()
        bmdnc__khg = builder.bitcast(bmdnc__khg, jasua__ysz)
        builder.store(wlzld__iuf._getvalue(), bmdnc__khg)
        return impl_ret_borrowed(context, builder, df_typ, udfa__axivr)
    sig = signature(df_typ, df_typ, c_ind_typ, arr_typ)
    return sig, codegen


@intrinsic
def set_df_index(typingctx, df_t, index_t=None):
    check_runtime_cols_unsupported(df_t, 'set_df_index')

    def codegen(context, builder, signature, args):
        gogv__etwbz = args[0]
        index_val = args[1]
        df_typ = signature.args[0]
        lmky__wvscw = cgutils.create_struct_proxy(df_typ)(context, builder,
            value=gogv__etwbz)
        pkb__wjvyl = get_dataframe_payload(context, builder, df_typ,
            gogv__etwbz)
        rrie__zdaoj = construct_dataframe(context, builder, signature.
            return_type, pkb__wjvyl.data, index_val, lmky__wvscw.parent, None)
        context.nrt.incref(builder, index_t, index_val)
        context.nrt.incref(builder, types.Tuple(df_t.data), pkb__wjvyl.data)
        return rrie__zdaoj
    pxzzj__xlf = DataFrameType(df_t.data, index_t, df_t.columns, df_t.dist,
        df_t.is_table_format)
    sig = signature(pxzzj__xlf, df_t, index_t)
    return sig, codegen


@intrinsic
def set_df_column_with_reflect(typingctx, df_type, cname_type, arr_type=None):
    check_runtime_cols_unsupported(df_type, 'set_df_column_with_reflect')
    assert is_literal_type(cname_type), 'constant column name expected'
    col_name = get_literal_value(cname_type)
    mbdx__zpxsp = len(df_type.columns)
    vgfz__uvhx = mbdx__zpxsp
    sls__jdq = df_type.data
    column_names = df_type.columns
    index_typ = df_type.index
    rwth__gca = col_name not in df_type.columns
    pfa__pmko = mbdx__zpxsp
    if rwth__gca:
        sls__jdq += arr_type,
        column_names += col_name,
        vgfz__uvhx += 1
    else:
        pfa__pmko = df_type.columns.index(col_name)
        sls__jdq = tuple(arr_type if i == pfa__pmko else sls__jdq[i] for i in
            range(mbdx__zpxsp))

    def codegen(context, builder, signature, args):
        udfa__axivr, pkgco__seop, oebx__alp = args
        in_dataframe_payload = get_dataframe_payload(context, builder,
            df_type, udfa__axivr)
        rjtb__chb = cgutils.create_struct_proxy(df_type)(context, builder,
            value=udfa__axivr)
        if df_type.is_table_format:
            njp__mql = df_type.table_type
            eymse__quvy = builder.extract_value(in_dataframe_payload.data, 0)
            exr__hwle = TableType(sls__jdq)
            dxxs__nzhs = set_table_data_codegen(context, builder, njp__mql,
                eymse__quvy, exr__hwle, arr_type, oebx__alp, pfa__pmko,
                rwth__gca)
            data_tup = context.make_tuple(builder, types.Tuple([exr__hwle]),
                [dxxs__nzhs])
        else:
            eoukz__odxg = [(builder.extract_value(in_dataframe_payload.data,
                i) if i != pfa__pmko else oebx__alp) for i in range(
                mbdx__zpxsp)]
            if rwth__gca:
                eoukz__odxg.append(oebx__alp)
            for itzo__qblim, eyora__vim in zip(eoukz__odxg, sls__jdq):
                context.nrt.incref(builder, eyora__vim, itzo__qblim)
            data_tup = context.make_tuple(builder, types.Tuple(sls__jdq),
                eoukz__odxg)
        index_val = in_dataframe_payload.index
        context.nrt.incref(builder, index_typ, index_val)
        eqcd__tiz = construct_dataframe(context, builder, signature.
            return_type, data_tup, index_val, rjtb__chb.parent, None)
        if not rwth__gca and arr_type == df_type.data[pfa__pmko]:
            decref_df_data(context, builder, in_dataframe_payload, df_type)
            payload_type = DataFramePayloadType(df_type)
            bmdnc__khg = context.nrt.meminfo_data(builder, rjtb__chb.meminfo)
            jasua__ysz = context.get_value_type(payload_type).as_pointer()
            bmdnc__khg = builder.bitcast(bmdnc__khg, jasua__ysz)
            wstxy__gled = get_dataframe_payload(context, builder, df_type,
                eqcd__tiz)
            builder.store(wstxy__gled._getvalue(), bmdnc__khg)
            context.nrt.incref(builder, index_typ, index_val)
            if df_type.is_table_format:
                context.nrt.incref(builder, exr__hwle, builder.
                    extract_value(data_tup, 0))
            else:
                for itzo__qblim, eyora__vim in zip(eoukz__odxg, sls__jdq):
                    context.nrt.incref(builder, eyora__vim, itzo__qblim)
        has_parent = cgutils.is_not_null(builder, rjtb__chb.parent)
        with builder.if_then(has_parent):
            hvpg__mcq = context.get_python_api(builder)
            mvbs__yai = hvpg__mcq.gil_ensure()
            onmut__upga = context.get_env_manager(builder)
            context.nrt.incref(builder, arr_type, oebx__alp)
            twp__cwjmx = numba.core.pythonapi._BoxContext(context, builder,
                hvpg__mcq, onmut__upga)
            twsty__fzyw = twp__cwjmx.pyapi.from_native_value(arr_type,
                oebx__alp, twp__cwjmx.env_manager)
            if isinstance(col_name, str):
                lyt__xzy = context.insert_const_string(builder.module, col_name
                    )
                xlq__lfrb = hvpg__mcq.string_from_string(lyt__xzy)
            else:
                assert isinstance(col_name, int)
                xlq__lfrb = hvpg__mcq.long_from_longlong(context.
                    get_constant(types.intp, col_name))
            hvpg__mcq.object_setitem(rjtb__chb.parent, xlq__lfrb, twsty__fzyw)
            hvpg__mcq.decref(twsty__fzyw)
            hvpg__mcq.decref(xlq__lfrb)
            hvpg__mcq.gil_release(mvbs__yai)
        return eqcd__tiz
    pxzzj__xlf = DataFrameType(sls__jdq, index_typ, column_names, df_type.
        dist, df_type.is_table_format)
    sig = signature(pxzzj__xlf, df_type, cname_type, arr_type)
    return sig, codegen


@lower_constant(DataFrameType)
def lower_constant_dataframe(context, builder, df_type, pyval):
    check_runtime_cols_unsupported(df_type, 'lowering a constant DataFrame')
    mbdx__zpxsp = len(pyval.columns)
    eoukz__odxg = tuple(pyval.iloc[:, i].values for i in range(mbdx__zpxsp))
    if df_type.is_table_format:
        nvool__ocz = context.get_constant_generic(builder, df_type.
            table_type, Table(eoukz__odxg))
        data_tup = lir.Constant.literal_struct([nvool__ocz])
    else:
        data_tup = lir.Constant.literal_struct([context.
            get_constant_generic(builder, df_type.data[i], sqnnt__ebrig) for
            i, sqnnt__ebrig in enumerate(eoukz__odxg)])
    index_val = context.get_constant_generic(builder, df_type.index, pyval.
        index)
    vokbk__qfjdp = context.get_constant_null(types.pyobject)
    payload = lir.Constant.literal_struct([data_tup, index_val, vokbk__qfjdp])
    payload = cgutils.global_constant(builder, '.const.payload', payload
        ).bitcast(cgutils.voidptr_t)
    qei__ueb = context.get_constant(types.int64, -1)
    jzfud__nzlv = context.get_constant_null(types.voidptr)
    eqehz__vhzwi = lir.Constant.literal_struct([qei__ueb, jzfud__nzlv,
        jzfud__nzlv, payload, qei__ueb])
    eqehz__vhzwi = cgutils.global_constant(builder, '.const.meminfo',
        eqehz__vhzwi).bitcast(cgutils.voidptr_t)
    return lir.Constant.literal_struct([eqehz__vhzwi, vokbk__qfjdp])


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
        tlna__netdd = context.cast(builder, in_dataframe_payload.index,
            fromty.index, toty.index)
    else:
        tlna__netdd = in_dataframe_payload.index
        context.nrt.incref(builder, fromty.index, tlna__netdd)
    if (fromty.is_table_format == toty.is_table_format and fromty.data ==
        toty.data):
        torgi__shps = in_dataframe_payload.data
        if fromty.is_table_format:
            context.nrt.incref(builder, types.Tuple([fromty.table_type]),
                torgi__shps)
        else:
            context.nrt.incref(builder, types.BaseTuple.from_types(fromty.
                data), torgi__shps)
    elif not fromty.is_table_format and toty.is_table_format:
        torgi__shps = _cast_df_data_to_table_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    elif fromty.is_table_format and not toty.is_table_format:
        torgi__shps = _cast_df_data_to_tuple_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    elif fromty.is_table_format and toty.is_table_format:
        torgi__shps = _cast_df_data_keep_table_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    else:
        torgi__shps = _cast_df_data_keep_tuple_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    return construct_dataframe(context, builder, toty, torgi__shps,
        tlna__netdd, in_dataframe_payload.parent, None)


def _cast_empty_df(context, builder, toty):
    eyu__btllx = {}
    if isinstance(toty.index, RangeIndexType):
        index = 'bodo.hiframes.pd_index_ext.init_range_index(0, 0, 1, None)'
    else:
        nci__wymc = get_index_data_arr_types(toty.index)[0]
        mvhz__nqpb = bodo.utils.transform.get_type_alloc_counts(nci__wymc) - 1
        zahhi__dqzx = ', '.join('0' for pkgco__seop in range(mvhz__nqpb))
        index = (
            'bodo.utils.conversion.index_from_array(bodo.utils.utils.alloc_type(0, index_arr_type, ({}{})))'
            .format(zahhi__dqzx, ', ' if mvhz__nqpb == 1 else ''))
        eyu__btllx['index_arr_type'] = nci__wymc
    gun__zcbnf = []
    for i, arr_typ in enumerate(toty.data):
        mvhz__nqpb = bodo.utils.transform.get_type_alloc_counts(arr_typ) - 1
        zahhi__dqzx = ', '.join('0' for pkgco__seop in range(mvhz__nqpb))
        abbcw__oxggk = ('bodo.utils.utils.alloc_type(0, arr_type{}, ({}{}))'
            .format(i, zahhi__dqzx, ', ' if mvhz__nqpb == 1 else ''))
        gun__zcbnf.append(abbcw__oxggk)
        eyu__btllx[f'arr_type{i}'] = arr_typ
    gun__zcbnf = ', '.join(gun__zcbnf)
    quscx__gktco = 'def impl():\n'
    kvvb__eixo = bodo.hiframes.dataframe_impl._gen_init_df(quscx__gktco,
        toty.columns, gun__zcbnf, index, eyu__btllx)
    df = context.compile_internal(builder, kvvb__eixo, toty(), [])
    return df


def _cast_df_data_to_table_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting traditional DataFrame to table format')
    lfvvh__zywzc = toty.table_type
    nvool__ocz = cgutils.create_struct_proxy(lfvvh__zywzc)(context, builder)
    nvool__ocz.parent = in_dataframe_payload.parent
    for rskso__itevd, wfbx__shdi in lfvvh__zywzc.type_to_blk.items():
        guqc__mvpn = context.get_constant(types.int64, len(lfvvh__zywzc.
            block_to_arr_ind[wfbx__shdi]))
        pkgco__seop, olne__qjsb = ListInstance.allocate_ex(context, builder,
            types.List(rskso__itevd), guqc__mvpn)
        olne__qjsb.size = guqc__mvpn
        setattr(nvool__ocz, f'block_{wfbx__shdi}', olne__qjsb.value)
    for i, rskso__itevd in enumerate(fromty.data):
        gwe__ggvxi = toty.data[i]
        if rskso__itevd != gwe__ggvxi:
            uozcx__phu = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*uozcx__phu)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        dxo__jtg = builder.extract_value(in_dataframe_payload.data, i)
        if rskso__itevd != gwe__ggvxi:
            vcpd__dfbin = context.cast(builder, dxo__jtg, rskso__itevd,
                gwe__ggvxi)
            wpf__myu = False
        else:
            vcpd__dfbin = dxo__jtg
            wpf__myu = True
        wfbx__shdi = lfvvh__zywzc.type_to_blk[rskso__itevd]
        epjr__zyzks = getattr(nvool__ocz, f'block_{wfbx__shdi}')
        zqex__ofat = ListInstance(context, builder, types.List(rskso__itevd
            ), epjr__zyzks)
        mllv__jdgn = context.get_constant(types.int64, lfvvh__zywzc.
            block_offsets[i])
        zqex__ofat.setitem(mllv__jdgn, vcpd__dfbin, wpf__myu)
    data_tup = context.make_tuple(builder, types.Tuple([lfvvh__zywzc]), [
        nvool__ocz._getvalue()])
    return data_tup


def _cast_df_data_keep_tuple_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting traditional DataFrame columns')
    eoukz__odxg = []
    for i in range(len(fromty.data)):
        if fromty.data[i] != toty.data[i]:
            uozcx__phu = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*uozcx__phu)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
            dxo__jtg = builder.extract_value(in_dataframe_payload.data, i)
            vcpd__dfbin = context.cast(builder, dxo__jtg, fromty.data[i],
                toty.data[i])
            wpf__myu = False
        else:
            vcpd__dfbin = builder.extract_value(in_dataframe_payload.data, i)
            wpf__myu = True
        if wpf__myu:
            context.nrt.incref(builder, toty.data[i], vcpd__dfbin)
        eoukz__odxg.append(vcpd__dfbin)
    data_tup = context.make_tuple(builder, types.Tuple(toty.data), eoukz__odxg)
    return data_tup


def _cast_df_data_keep_table_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting table format DataFrame columns')
    njp__mql = fromty.table_type
    eymse__quvy = cgutils.create_struct_proxy(njp__mql)(context, builder,
        builder.extract_value(in_dataframe_payload.data, 0))
    exr__hwle = toty.table_type
    dxxs__nzhs = cgutils.create_struct_proxy(exr__hwle)(context, builder)
    dxxs__nzhs.parent = in_dataframe_payload.parent
    for rskso__itevd, wfbx__shdi in exr__hwle.type_to_blk.items():
        guqc__mvpn = context.get_constant(types.int64, len(exr__hwle.
            block_to_arr_ind[wfbx__shdi]))
        pkgco__seop, olne__qjsb = ListInstance.allocate_ex(context, builder,
            types.List(rskso__itevd), guqc__mvpn)
        olne__qjsb.size = guqc__mvpn
        setattr(dxxs__nzhs, f'block_{wfbx__shdi}', olne__qjsb.value)
    for i in range(len(fromty.data)):
        gaf__adgd = fromty.data[i]
        gwe__ggvxi = toty.data[i]
        if gaf__adgd != gwe__ggvxi:
            uozcx__phu = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*uozcx__phu)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        xyfn__qoqkz = njp__mql.type_to_blk[gaf__adgd]
        tzv__kvqry = getattr(eymse__quvy, f'block_{xyfn__qoqkz}')
        ateo__mzyv = ListInstance(context, builder, types.List(gaf__adgd),
            tzv__kvqry)
        qhrjk__vyb = context.get_constant(types.int64, njp__mql.
            block_offsets[i])
        dxo__jtg = ateo__mzyv.getitem(qhrjk__vyb)
        if gaf__adgd != gwe__ggvxi:
            vcpd__dfbin = context.cast(builder, dxo__jtg, gaf__adgd, gwe__ggvxi
                )
            wpf__myu = False
        else:
            vcpd__dfbin = dxo__jtg
            wpf__myu = True
        hrhrf__zkogf = exr__hwle.type_to_blk[rskso__itevd]
        olne__qjsb = getattr(dxxs__nzhs, f'block_{hrhrf__zkogf}')
        lztdo__rkfnc = ListInstance(context, builder, types.List(gwe__ggvxi
            ), olne__qjsb)
        cvjsg__vfa = context.get_constant(types.int64, exr__hwle.
            block_offsets[i])
        lztdo__rkfnc.setitem(cvjsg__vfa, vcpd__dfbin, wpf__myu)
    data_tup = context.make_tuple(builder, types.Tuple([exr__hwle]), [
        dxxs__nzhs._getvalue()])
    return data_tup


def _cast_df_data_to_tuple_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(fromty,
        'casting table format to traditional DataFrame')
    lfvvh__zywzc = fromty.table_type
    nvool__ocz = cgutils.create_struct_proxy(lfvvh__zywzc)(context, builder,
        builder.extract_value(in_dataframe_payload.data, 0))
    eoukz__odxg = []
    for i, rskso__itevd in enumerate(toty.data):
        gaf__adgd = fromty.data[i]
        if rskso__itevd != gaf__adgd:
            uozcx__phu = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*uozcx__phu)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        wfbx__shdi = lfvvh__zywzc.type_to_blk[rskso__itevd]
        epjr__zyzks = getattr(nvool__ocz, f'block_{wfbx__shdi}')
        zqex__ofat = ListInstance(context, builder, types.List(rskso__itevd
            ), epjr__zyzks)
        mllv__jdgn = context.get_constant(types.int64, lfvvh__zywzc.
            block_offsets[i])
        dxo__jtg = zqex__ofat.getitem(mllv__jdgn)
        if rskso__itevd != gaf__adgd:
            vcpd__dfbin = context.cast(builder, dxo__jtg, gaf__adgd,
                rskso__itevd)
            wpf__myu = False
        else:
            vcpd__dfbin = dxo__jtg
            wpf__myu = True
        if wpf__myu:
            context.nrt.incref(builder, rskso__itevd, vcpd__dfbin)
        eoukz__odxg.append(vcpd__dfbin)
    data_tup = context.make_tuple(builder, types.Tuple(toty.data), eoukz__odxg)
    return data_tup


@overload(pd.DataFrame, inline='always', no_unliteral=True)
def pd_dataframe_overload(data=None, index=None, columns=None, dtype=None,
    copy=False):
    if not is_overload_constant_bool(copy):
        raise BodoError(
            "pd.DataFrame(): 'copy' argument should be a constant boolean")
    copy = get_overload_const(copy)
    imkxq__ryj, gun__zcbnf, index_arg = _get_df_args(data, index, columns,
        dtype, copy)
    pynr__klez = gen_const_tup(imkxq__ryj)
    quscx__gktco = (
        'def _init_df(data=None, index=None, columns=None, dtype=None, copy=False):\n'
        )
    quscx__gktco += (
        '  return bodo.hiframes.pd_dataframe_ext.init_dataframe({}, {}, {})\n'
        .format(gun__zcbnf, index_arg, pynr__klez))
    erl__khvv = {}
    exec(quscx__gktco, {'bodo': bodo, 'np': np}, erl__khvv)
    bum__dkda = erl__khvv['_init_df']
    return bum__dkda


@intrinsic
def _tuple_to_table_format_decoded(typingctx, df_typ):
    assert not df_typ.is_table_format, '_tuple_to_table_format requires a tuple format input'

    def codegen(context, builder, signature, args):
        return context.cast(builder, args[0], signature.args[0], signature.
            return_type)
    pxzzj__xlf = DataFrameType(to_str_arr_if_dict_array(df_typ.data),
        df_typ.index, df_typ.columns, dist=df_typ.dist, is_table_format=True)
    sig = signature(pxzzj__xlf, df_typ)
    return sig, codegen


@intrinsic
def _table_to_tuple_format_decoded(typingctx, df_typ):
    assert df_typ.is_table_format, '_tuple_to_table_format requires a table format input'

    def codegen(context, builder, signature, args):
        return context.cast(builder, args[0], signature.args[0], signature.
            return_type)
    pxzzj__xlf = DataFrameType(to_str_arr_if_dict_array(df_typ.data),
        df_typ.index, df_typ.columns, dist=df_typ.dist, is_table_format=False)
    sig = signature(pxzzj__xlf, df_typ)
    return sig, codegen


def _get_df_args(data, index, columns, dtype, copy):
    tgbh__alx = ''
    if not is_overload_none(dtype):
        tgbh__alx = '.astype(dtype)'
    index_is_none = is_overload_none(index)
    index_arg = 'bodo.utils.conversion.convert_to_index(index)'
    if isinstance(data, types.BaseTuple):
        if not data.types[0] == types.StringLiteral('__bodo_tup'):
            raise BodoError('pd.DataFrame tuple input data not supported yet')
        assert len(data.types) % 2 == 1, 'invalid const dict tuple structure'
        mbdx__zpxsp = (len(data.types) - 1) // 2
        tpp__iufa = [rskso__itevd.literal_value for rskso__itevd in data.
            types[1:mbdx__zpxsp + 1]]
        data_val_types = dict(zip(tpp__iufa, data.types[mbdx__zpxsp + 1:]))
        eoukz__odxg = ['data[{}]'.format(i) for i in range(mbdx__zpxsp + 1,
            2 * mbdx__zpxsp + 1)]
        data_dict = dict(zip(tpp__iufa, eoukz__odxg))
        if is_overload_none(index):
            for i, rskso__itevd in enumerate(data.types[mbdx__zpxsp + 1:]):
                if isinstance(rskso__itevd, SeriesType):
                    index_arg = (
                        'bodo.hiframes.pd_series_ext.get_series_index(data[{}])'
                        .format(mbdx__zpxsp + 1 + i))
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
        kpra__mcpq = '.copy()' if copy else ''
        qfd__inu = get_overload_const_list(columns)
        mbdx__zpxsp = len(qfd__inu)
        data_val_types = {twp__cwjmx: data.copy(ndim=1) for twp__cwjmx in
            qfd__inu}
        eoukz__odxg = ['data[:,{}]{}'.format(i, kpra__mcpq) for i in range(
            mbdx__zpxsp)]
        data_dict = dict(zip(qfd__inu, eoukz__odxg))
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
    gun__zcbnf = '({},)'.format(', '.join(
        'bodo.utils.conversion.coerce_to_array({}, True, scalar_to_arr_len={}){}'
        .format(data_dict[twp__cwjmx], df_len, tgbh__alx) for twp__cwjmx in
        col_names))
    if len(col_names) == 0:
        gun__zcbnf = '()'
    return col_names, gun__zcbnf, index_arg


def _get_df_len_from_info(data_dict, data_val_types, col_names,
    index_is_none, index_arg):
    df_len = '0'
    for twp__cwjmx in col_names:
        if twp__cwjmx in data_dict and is_iterable_type(data_val_types[
            twp__cwjmx]):
            df_len = 'len({})'.format(data_dict[twp__cwjmx])
            break
    if df_len == '0' and not index_is_none:
        df_len = f'len({index_arg})'
    return df_len


def _fill_null_arrays(data_dict, col_names, df_len, dtype):
    if all(twp__cwjmx in data_dict for twp__cwjmx in col_names):
        return
    if is_overload_none(dtype):
        dtype = 'bodo.string_array_type'
    else:
        dtype = 'bodo.utils.conversion.array_type_from_dtype(dtype)'
    htqrv__hyi = 'bodo.libs.array_kernels.gen_na_array({}, {})'.format(df_len,
        dtype)
    for twp__cwjmx in col_names:
        if twp__cwjmx not in data_dict:
            data_dict[twp__cwjmx] = htqrv__hyi


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
            rskso__itevd = bodo.hiframes.pd_dataframe_ext.get_dataframe_table(
                df)
            return len(rskso__itevd)
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
        ypaqm__dxr = idx.literal_value
        if isinstance(ypaqm__dxr, int):
            uvcm__rwvj = tup.types[ypaqm__dxr]
        elif isinstance(ypaqm__dxr, slice):
            uvcm__rwvj = types.BaseTuple.from_types(tup.types[ypaqm__dxr])
        return signature(uvcm__rwvj, *args)


GetItemTuple.prefer_literal = True


@lower_builtin(operator.getitem, types.BaseTuple, types.IntegerLiteral)
@lower_builtin(operator.getitem, types.BaseTuple, types.SliceLiteral)
def getitem_tuple_lower(context, builder, sig, args):
    cvzc__qflk, idx = sig.args
    idx = idx.literal_value
    tup, pkgco__seop = args
    if isinstance(idx, int):
        if idx < 0:
            idx += len(cvzc__qflk)
        if not 0 <= idx < len(cvzc__qflk):
            raise IndexError('cannot index at %d in %s' % (idx, cvzc__qflk))
        alggl__wevzl = builder.extract_value(tup, idx)
    elif isinstance(idx, slice):
        wwjva__dsi = cgutils.unpack_tuple(builder, tup)[idx]
        alggl__wevzl = context.make_tuple(builder, sig.return_type, wwjva__dsi)
    else:
        raise NotImplementedError('unexpected index %r for %s' % (idx, sig.
            args[0]))
    return impl_ret_borrowed(context, builder, sig.return_type, alggl__wevzl)


def join_dummy(left_df, right_df, left_on, right_on, how, suffix_x,
    suffix_y, is_join, indicator, _bodo_na_equal, gen_cond):
    return left_df


@infer_global(join_dummy)
class JoinTyper(AbstractTemplate):

    def generic(self, args, kws):
        from bodo.hiframes.pd_dataframe_ext import DataFrameType
        from bodo.utils.typing import is_overload_str
        assert not kws
        (left_df, right_df, left_on, right_on, fob__zxcbe, suffix_x,
            suffix_y, is_join, indicator, _bodo_na_equal, jnsaz__bnd) = args
        left_on = get_overload_const_list(left_on)
        right_on = get_overload_const_list(right_on)
        tpvy__jnfos = set(left_on) & set(right_on)
        vzxe__snlt = set(left_df.columns) & set(right_df.columns)
        itc__tqvm = vzxe__snlt - tpvy__jnfos
        stxck__zizv = '$_bodo_index_' in left_on
        syo__vman = '$_bodo_index_' in right_on
        how = get_overload_const_str(fob__zxcbe)
        wirg__gvzfg = how in {'left', 'outer'}
        oep__eskl = how in {'right', 'outer'}
        columns = []
        data = []
        if stxck__zizv:
            vko__ppnh = bodo.utils.typing.get_index_data_arr_types(left_df.
                index)[0]
        else:
            vko__ppnh = left_df.data[left_df.columns.index(left_on[0])]
        if syo__vman:
            jvi__kwmp = bodo.utils.typing.get_index_data_arr_types(right_df
                .index)[0]
        else:
            jvi__kwmp = right_df.data[right_df.columns.index(right_on[0])]
        if stxck__zizv and not syo__vman and not is_join.literal_value:
            yaapg__hbde = right_on[0]
            if yaapg__hbde in left_df.columns:
                columns.append(yaapg__hbde)
                if (jvi__kwmp == bodo.dict_str_arr_type and vko__ppnh ==
                    bodo.string_array_type):
                    sdy__qkgpp = bodo.string_array_type
                else:
                    sdy__qkgpp = jvi__kwmp
                data.append(sdy__qkgpp)
        if syo__vman and not stxck__zizv and not is_join.literal_value:
            orgqd__snwv = left_on[0]
            if orgqd__snwv in right_df.columns:
                columns.append(orgqd__snwv)
                if (vko__ppnh == bodo.dict_str_arr_type and jvi__kwmp ==
                    bodo.string_array_type):
                    sdy__qkgpp = bodo.string_array_type
                else:
                    sdy__qkgpp = vko__ppnh
                data.append(sdy__qkgpp)
        for gaf__adgd, fomb__bobl in zip(left_df.data, left_df.columns):
            columns.append(str(fomb__bobl) + suffix_x.literal_value if 
                fomb__bobl in itc__tqvm else fomb__bobl)
            if fomb__bobl in tpvy__jnfos:
                if gaf__adgd == bodo.dict_str_arr_type:
                    gaf__adgd = right_df.data[right_df.columns.index(
                        fomb__bobl)]
                data.append(gaf__adgd)
            else:
                if (gaf__adgd == bodo.dict_str_arr_type and fomb__bobl in
                    left_on):
                    if syo__vman:
                        gaf__adgd = jvi__kwmp
                    else:
                        oqz__bzy = left_on.index(fomb__bobl)
                        rnkjf__lmu = right_on[oqz__bzy]
                        gaf__adgd = right_df.data[right_df.columns.index(
                            rnkjf__lmu)]
                if oep__eskl:
                    gaf__adgd = to_nullable_type(gaf__adgd)
                data.append(gaf__adgd)
        for gaf__adgd, fomb__bobl in zip(right_df.data, right_df.columns):
            if fomb__bobl not in tpvy__jnfos:
                columns.append(str(fomb__bobl) + suffix_y.literal_value if 
                    fomb__bobl in itc__tqvm else fomb__bobl)
                if (gaf__adgd == bodo.dict_str_arr_type and fomb__bobl in
                    right_on):
                    if stxck__zizv:
                        gaf__adgd = vko__ppnh
                    else:
                        oqz__bzy = right_on.index(fomb__bobl)
                        ony__pus = left_on[oqz__bzy]
                        gaf__adgd = left_df.data[left_df.columns.index(
                            ony__pus)]
                if wirg__gvzfg:
                    gaf__adgd = to_nullable_type(gaf__adgd)
                data.append(gaf__adgd)
        zrct__susz = get_overload_const_bool(indicator)
        if zrct__susz:
            columns.append('_merge')
            data.append(bodo.CategoricalArrayType(bodo.PDCategoricalDtype((
                'left_only', 'right_only', 'both'), bodo.string_type, False)))
        index_typ = RangeIndexType(types.none)
        if stxck__zizv and syo__vman and not is_overload_str(how, 'asof'):
            index_typ = left_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        elif stxck__zizv and not syo__vman:
            index_typ = right_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        elif syo__vman and not stxck__zizv:
            index_typ = left_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        okt__mznh = DataFrameType(tuple(data), index_typ, tuple(columns))
        return signature(okt__mznh, *args)


JoinTyper._no_unliteral = True


@lower_builtin(join_dummy, types.VarArg(types.Any))
def lower_join_dummy(context, builder, sig, args):
    rrie__zdaoj = cgutils.create_struct_proxy(sig.return_type)(context, builder
        )
    return rrie__zdaoj._getvalue()


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
    zhaar__ahwmy = dict(join=join, join_axes=join_axes, keys=keys, levels=
        levels, names=names, verify_integrity=verify_integrity, sort=sort,
        copy=copy)
    xtocr__kkfz = dict(join='outer', join_axes=None, keys=None, levels=None,
        names=None, verify_integrity=False, sort=None, copy=True)
    check_unsupported_args('pandas.concat', zhaar__ahwmy, xtocr__kkfz,
        package_name='pandas', module_name='General')
    quscx__gktco = """def impl(objs, axis=0, join='outer', join_axes=None, ignore_index=False, keys=None, levels=None, names=None, verify_integrity=False, sort=None, copy=True):
"""
    if axis == 1:
        if not isinstance(objs, types.BaseTuple):
            raise_bodo_error(
                'Only tuple argument for pd.concat(axis=1) expected')
        index = (
            'bodo.hiframes.pd_index_ext.init_range_index(0, len(objs[0]), 1, None)'
            )
        okunt__bqurq = 0
        gun__zcbnf = []
        names = []
        for i, jaxjc__txu in enumerate(objs.types):
            assert isinstance(jaxjc__txu, (SeriesType, DataFrameType))
            check_runtime_cols_unsupported(jaxjc__txu, 'pd.concat()')
            if isinstance(jaxjc__txu, SeriesType):
                names.append(str(okunt__bqurq))
                okunt__bqurq += 1
                gun__zcbnf.append(
                    'bodo.hiframes.pd_series_ext.get_series_data(objs[{}])'
                    .format(i))
            else:
                names.extend(jaxjc__txu.columns)
                for bbng__uptmt in range(len(jaxjc__txu.data)):
                    gun__zcbnf.append(
                        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(objs[{}], {})'
                        .format(i, bbng__uptmt))
        return bodo.hiframes.dataframe_impl._gen_init_df(quscx__gktco,
            names, ', '.join(gun__zcbnf), index)
    if axis != 0:
        raise_bodo_error('pd.concat(): axis must be 0 or 1')
    if isinstance(objs, types.BaseTuple) and isinstance(objs.types[0],
        DataFrameType):
        assert all(isinstance(rskso__itevd, DataFrameType) for rskso__itevd in
            objs.types)
        ledqa__agypp = []
        for df in objs.types:
            check_runtime_cols_unsupported(df, 'pd.concat()')
            ledqa__agypp.extend(df.columns)
        ledqa__agypp = list(dict.fromkeys(ledqa__agypp).keys())
        rltw__kpq = {}
        for okunt__bqurq, twp__cwjmx in enumerate(ledqa__agypp):
            for df in objs.types:
                if twp__cwjmx in df.columns:
                    rltw__kpq['arr_typ{}'.format(okunt__bqurq)] = df.data[df
                        .columns.index(twp__cwjmx)]
                    break
        assert len(rltw__kpq) == len(ledqa__agypp)
        psbbq__wgoiy = []
        for okunt__bqurq, twp__cwjmx in enumerate(ledqa__agypp):
            args = []
            for i, df in enumerate(objs.types):
                if twp__cwjmx in df.columns:
                    pfa__pmko = df.columns.index(twp__cwjmx)
                    args.append(
                        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(objs[{}], {})'
                        .format(i, pfa__pmko))
                else:
                    args.append(
                        'bodo.libs.array_kernels.gen_na_array(len(objs[{}]), arr_typ{})'
                        .format(i, okunt__bqurq))
            quscx__gktco += ('  A{} = bodo.libs.array_kernels.concat(({},))\n'
                .format(okunt__bqurq, ', '.join(args)))
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
        return bodo.hiframes.dataframe_impl._gen_init_df(quscx__gktco,
            ledqa__agypp, ', '.join('A{}'.format(i) for i in range(len(
            ledqa__agypp))), index, rltw__kpq)
    if isinstance(objs, types.BaseTuple) and isinstance(objs.types[0],
        SeriesType):
        assert all(isinstance(rskso__itevd, SeriesType) for rskso__itevd in
            objs.types)
        quscx__gktco += ('  out_arr = bodo.libs.array_kernels.concat(({},))\n'
            .format(', '.join(
            'bodo.hiframes.pd_series_ext.get_series_data(objs[{}])'.format(
            i) for i in range(len(objs.types)))))
        if ignore_index:
            quscx__gktco += """  index = bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr), 1, None)
"""
        else:
            quscx__gktco += (
                """  index = bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(({},)))
"""
                .format(', '.join(
                'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(objs[{}]))'
                .format(i) for i in range(len(objs.types)))))
        quscx__gktco += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index)\n'
            )
        erl__khvv = {}
        exec(quscx__gktco, {'bodo': bodo, 'np': np, 'numba': numba}, erl__khvv)
        return erl__khvv['impl']
    if isinstance(objs, types.List) and isinstance(objs.dtype, DataFrameType):
        check_runtime_cols_unsupported(objs.dtype, 'pd.concat()')
        df_type = objs.dtype
        for okunt__bqurq, twp__cwjmx in enumerate(df_type.columns):
            quscx__gktco += '  arrs{} = []\n'.format(okunt__bqurq)
            quscx__gktco += '  for i in range(len(objs)):\n'
            quscx__gktco += '    df = objs[i]\n'
            quscx__gktco += (
                """    arrs{0}.append(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0}))
"""
                .format(okunt__bqurq))
            quscx__gktco += (
                '  out_arr{0} = bodo.libs.array_kernels.concat(arrs{0})\n'.
                format(okunt__bqurq))
        if ignore_index:
            index = (
                'bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr0), 1, None)'
                )
        else:
            quscx__gktco += '  arrs_index = []\n'
            quscx__gktco += '  for i in range(len(objs)):\n'
            quscx__gktco += '    df = objs[i]\n'
            quscx__gktco += """    arrs_index.append(bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)))
"""
            if objs.dtype.index.name_typ == types.none:
                name = None
            else:
                name = objs.dtype.index.name_typ.literal_value
            index = f"""bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(arrs_index), {name!r})
"""
        return bodo.hiframes.dataframe_impl._gen_init_df(quscx__gktco,
            df_type.columns, ', '.join('out_arr{}'.format(i) for i in range
            (len(df_type.columns))), index)
    if isinstance(objs, types.List) and isinstance(objs.dtype, SeriesType):
        quscx__gktco += '  arrs = []\n'
        quscx__gktco += '  for i in range(len(objs)):\n'
        quscx__gktco += (
            '    arrs.append(bodo.hiframes.pd_series_ext.get_series_data(objs[i]))\n'
            )
        quscx__gktco += '  out_arr = bodo.libs.array_kernels.concat(arrs)\n'
        if ignore_index:
            quscx__gktco += """  index = bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr), 1, None)
"""
        else:
            quscx__gktco += '  arrs_index = []\n'
            quscx__gktco += '  for i in range(len(objs)):\n'
            quscx__gktco += '    S = objs[i]\n'
            quscx__gktco += """    arrs_index.append(bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(S)))
"""
            quscx__gktco += """  index = bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(arrs_index))
"""
        quscx__gktco += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index)\n'
            )
        erl__khvv = {}
        exec(quscx__gktco, {'bodo': bodo, 'np': np, 'numba': numba}, erl__khvv)
        return erl__khvv['impl']
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
        pxzzj__xlf = df.copy(index=index, is_table_format=False)
        return signature(pxzzj__xlf, *args)


SortDummyTyper._no_unliteral = True


@lower_builtin(sort_values_dummy, types.VarArg(types.Any))
def lower_sort_values_dummy(context, builder, sig, args):
    if sig.return_type == types.none:
        return
    zgxx__okpn = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return zgxx__okpn._getvalue()


@overload_method(DataFrameType, 'itertuples', inline='always', no_unliteral
    =True)
def itertuples_overload(df, index=True, name='Pandas'):
    check_runtime_cols_unsupported(df, 'DataFrame.itertuples()')
    zhaar__ahwmy = dict(index=index, name=name)
    xtocr__kkfz = dict(index=True, name='Pandas')
    check_unsupported_args('DataFrame.itertuples', zhaar__ahwmy,
        xtocr__kkfz, package_name='pandas', module_name='DataFrame')

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
        rltw__kpq = (types.Array(types.int64, 1, 'C'),) + df.data
        nnvu__zntfh = bodo.hiframes.dataframe_impl.DataFrameTupleIterator(
            columns, rltw__kpq)
        return signature(nnvu__zntfh, *args)


@lower_builtin(itertuples_dummy, types.VarArg(types.Any))
def lower_itertuples_dummy(context, builder, sig, args):
    zgxx__okpn = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return zgxx__okpn._getvalue()


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
    zgxx__okpn = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return zgxx__okpn._getvalue()


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
    zgxx__okpn = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return zgxx__okpn._getvalue()


@numba.generated_jit(nopython=True)
def pivot_impl(index_tup, columns_tup, values_tup, pivot_values,
    index_names, columns_name, value_names, check_duplicates=True, parallel
    =False):
    if not is_overload_constant_bool(check_duplicates):
        raise BodoError(
            'pivot_impl(): check_duplicates must be a constant boolean')
    ifbwe__uqkb = get_overload_const_bool(check_duplicates)
    bwbb__ylrad = not is_overload_none(value_names)
    nqb__fvgst = isinstance(values_tup, types.UniTuple)
    if nqb__fvgst:
        fhpwf__yyuk = [to_nullable_type(values_tup.dtype)]
    else:
        fhpwf__yyuk = [to_nullable_type(eyora__vim) for eyora__vim in
            values_tup]
    quscx__gktco = 'def impl(\n'
    quscx__gktco += """    index_tup, columns_tup, values_tup, pivot_values, index_names, columns_name, value_names, check_duplicates=True, parallel=False
"""
    quscx__gktco += '):\n'
    quscx__gktco += '    if parallel:\n'
    anl__qmwqm = ', '.join([f'array_to_info(index_tup[{i}])' for i in range
        (len(index_tup))] + [f'array_to_info(columns_tup[{i}])' for i in
        range(len(columns_tup))] + [f'array_to_info(values_tup[{i}])' for i in
        range(len(values_tup))])
    quscx__gktco += f'        info_list = [{anl__qmwqm}]\n'
    quscx__gktco += '        cpp_table = arr_info_list_to_table(info_list)\n'
    quscx__gktco += f"""        out_cpp_table = shuffle_table(cpp_table, {len(index_tup)}, parallel, 0)
"""
    cdlih__nvl = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i}), index_tup[{i}])'
         for i in range(len(index_tup))])
    mwcvg__idkib = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i + len(index_tup)}), columns_tup[{i}])'
         for i in range(len(columns_tup))])
    cionm__nqejn = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i + len(index_tup) + len(columns_tup)}), values_tup[{i}])'
         for i in range(len(values_tup))])
    quscx__gktco += f'        index_tup = ({cdlih__nvl},)\n'
    quscx__gktco += f'        columns_tup = ({mwcvg__idkib},)\n'
    quscx__gktco += f'        values_tup = ({cionm__nqejn},)\n'
    quscx__gktco += '        delete_table(cpp_table)\n'
    quscx__gktco += '        delete_table(out_cpp_table)\n'
    quscx__gktco += '    columns_arr = columns_tup[0]\n'
    if nqb__fvgst:
        quscx__gktco += '    values_arrs = [arr for arr in values_tup]\n'
    quscx__gktco += """    unique_index_arr_tup, row_vector = bodo.libs.array_ops.array_unique_vector_map(
"""
    quscx__gktco += '        index_tup\n'
    quscx__gktco += '    )\n'
    quscx__gktco += '    n_rows = len(unique_index_arr_tup[0])\n'
    quscx__gktco += '    num_values_arrays = len(values_tup)\n'
    quscx__gktco += '    n_unique_pivots = len(pivot_values)\n'
    if nqb__fvgst:
        quscx__gktco += '    n_cols = num_values_arrays * n_unique_pivots\n'
    else:
        quscx__gktco += '    n_cols = n_unique_pivots\n'
    quscx__gktco += '    col_map = {}\n'
    quscx__gktco += '    for i in range(n_unique_pivots):\n'
    quscx__gktco += (
        '        if bodo.libs.array_kernels.isna(pivot_values, i):\n')
    quscx__gktco += '            raise ValueError(\n'
    quscx__gktco += """                "DataFrame.pivot(): NA values in 'columns' array not supported\"
"""
    quscx__gktco += '            )\n'
    quscx__gktco += '        col_map[pivot_values[i]] = i\n'
    kxha__pvox = False
    for i, dstt__cyvo in enumerate(fhpwf__yyuk):
        if is_str_arr_type(dstt__cyvo):
            kxha__pvox = True
            quscx__gktco += f"""    len_arrs_{i} = [np.zeros(n_rows, np.int64) for _ in range(n_cols)]
"""
            quscx__gktco += (
                f'    total_lens_{i} = np.zeros(n_cols, np.int64)\n')
    if kxha__pvox:
        if ifbwe__uqkb:
            quscx__gktco += '    nbytes = (n_rows + 7) >> 3\n'
            quscx__gktco += """    seen_bitmaps = [np.zeros(nbytes, np.int8) for _ in range(n_unique_pivots)]
"""
        quscx__gktco += '    for i in range(len(columns_arr)):\n'
        quscx__gktco += '        col_name = columns_arr[i]\n'
        quscx__gktco += '        pivot_idx = col_map[col_name]\n'
        quscx__gktco += '        row_idx = row_vector[i]\n'
        if ifbwe__uqkb:
            quscx__gktco += '        seen_bitmap = seen_bitmaps[pivot_idx]\n'
            quscx__gktco += """        if bodo.libs.int_arr_ext.get_bit_bitmap_arr(seen_bitmap, row_idx):
"""
            quscx__gktco += """            raise ValueError("DataFrame.pivot(): 'index' contains duplicate entries for the same output column")
"""
            quscx__gktco += '        else:\n'
            quscx__gktco += """            bodo.libs.int_arr_ext.set_bit_to_arr(seen_bitmap, row_idx, 1)
"""
        if nqb__fvgst:
            quscx__gktco += '        for j in range(num_values_arrays):\n'
            quscx__gktco += (
                '            col_idx = (j * len(pivot_values)) + pivot_idx\n')
            quscx__gktco += '            len_arr = len_arrs_0[col_idx]\n'
            quscx__gktco += '            values_arr = values_arrs[j]\n'
            quscx__gktco += (
                '            if not bodo.libs.array_kernels.isna(values_arr, i):\n'
                )
            quscx__gktco += (
                '                len_arr[row_idx] = len(values_arr[i])\n')
            quscx__gktco += (
                '                total_lens_0[col_idx] += len(values_arr[i])\n'
                )
        else:
            for i, dstt__cyvo in enumerate(fhpwf__yyuk):
                if is_str_arr_type(dstt__cyvo):
                    quscx__gktco += f"""        if not bodo.libs.array_kernels.isna(values_tup[{i}], i):
"""
                    quscx__gktco += f"""            len_arrs_{i}[pivot_idx][row_idx] = len(values_tup[{i}][i])
"""
                    quscx__gktco += f"""            total_lens_{i}[pivot_idx] += len(values_tup[{i}][i])
"""
    for i, dstt__cyvo in enumerate(fhpwf__yyuk):
        if is_str_arr_type(dstt__cyvo):
            quscx__gktco += f'    data_arrs_{i} = [\n'
            quscx__gktco += (
                '        bodo.libs.str_arr_ext.gen_na_str_array_lens(\n')
            quscx__gktco += (
                f'            n_rows, total_lens_{i}[i], len_arrs_{i}[i]\n')
            quscx__gktco += '        )\n'
            quscx__gktco += '        for i in range(n_cols)\n'
            quscx__gktco += '    ]\n'
        else:
            quscx__gktco += f'    data_arrs_{i} = [\n'
            quscx__gktco += f"""        bodo.libs.array_kernels.gen_na_array(n_rows, data_arr_typ_{i})
"""
            quscx__gktco += '        for _ in range(n_cols)\n'
            quscx__gktco += '    ]\n'
    if not kxha__pvox and ifbwe__uqkb:
        quscx__gktco += '    nbytes = (n_rows + 7) >> 3\n'
        quscx__gktco += """    seen_bitmaps = [np.zeros(nbytes, np.int8) for _ in range(n_unique_pivots)]
"""
    quscx__gktco += '    for i in range(len(columns_arr)):\n'
    quscx__gktco += '        col_name = columns_arr[i]\n'
    quscx__gktco += '        pivot_idx = col_map[col_name]\n'
    quscx__gktco += '        row_idx = row_vector[i]\n'
    if not kxha__pvox and ifbwe__uqkb:
        quscx__gktco += '        seen_bitmap = seen_bitmaps[pivot_idx]\n'
        quscx__gktco += """        if bodo.libs.int_arr_ext.get_bit_bitmap_arr(seen_bitmap, row_idx):
"""
        quscx__gktco += """            raise ValueError("DataFrame.pivot(): 'index' contains duplicate entries for the same output column")
"""
        quscx__gktco += '        else:\n'
        quscx__gktco += """            bodo.libs.int_arr_ext.set_bit_to_arr(seen_bitmap, row_idx, 1)
"""
    if nqb__fvgst:
        quscx__gktco += '        for j in range(num_values_arrays):\n'
        quscx__gktco += (
            '            col_idx = (j * len(pivot_values)) + pivot_idx\n')
        quscx__gktco += '            col_arr = data_arrs_0[col_idx]\n'
        quscx__gktco += '            values_arr = values_arrs[j]\n'
        quscx__gktco += (
            '            if bodo.libs.array_kernels.isna(values_arr, i):\n')
        quscx__gktco += (
            '                bodo.libs.array_kernels.setna(col_arr, row_idx)\n'
            )
        quscx__gktco += '            else:\n'
        quscx__gktco += '                col_arr[row_idx] = values_arr[i]\n'
    else:
        for i, dstt__cyvo in enumerate(fhpwf__yyuk):
            quscx__gktco += f'        col_arr_{i} = data_arrs_{i}[pivot_idx]\n'
            quscx__gktco += (
                f'        if bodo.libs.array_kernels.isna(values_tup[{i}], i):\n'
                )
            quscx__gktco += (
                f'            bodo.libs.array_kernels.setna(col_arr_{i}, row_idx)\n'
                )
            quscx__gktco += f'        else:\n'
            quscx__gktco += (
                f'            col_arr_{i}[row_idx] = values_tup[{i}][i]\n')
    if len(index_tup) == 1:
        quscx__gktco += """    index = bodo.utils.conversion.index_from_array(unique_index_arr_tup[0], index_names[0])
"""
    else:
        quscx__gktco += """    index = bodo.hiframes.pd_multi_index_ext.init_multi_index(unique_index_arr_tup, index_names, None)
"""
    if bwbb__ylrad:
        quscx__gktco += '    num_rows = len(value_names) * len(pivot_values)\n'
        if is_str_arr_type(value_names):
            quscx__gktco += '    total_chars = 0\n'
            quscx__gktco += '    for i in range(len(value_names)):\n'
            quscx__gktco += '        total_chars += len(value_names[i])\n'
            quscx__gktco += """    new_value_names = bodo.libs.str_arr_ext.pre_alloc_string_array(num_rows, total_chars * len(pivot_values))
"""
        else:
            quscx__gktco += """    new_value_names = bodo.utils.utils.alloc_type(num_rows, value_names, (-1,))
"""
        if is_str_arr_type(pivot_values):
            quscx__gktco += '    total_chars = 0\n'
            quscx__gktco += '    for i in range(len(pivot_values)):\n'
            quscx__gktco += '        total_chars += len(pivot_values[i])\n'
            quscx__gktco += """    new_pivot_values = bodo.libs.str_arr_ext.pre_alloc_string_array(num_rows, total_chars * len(value_names))
"""
        else:
            quscx__gktco += """    new_pivot_values = bodo.utils.utils.alloc_type(num_rows, pivot_values, (-1,))
"""
        quscx__gktco += '    for i in range(len(value_names)):\n'
        quscx__gktco += '        for j in range(len(pivot_values)):\n'
        quscx__gktco += """            new_value_names[(i * len(pivot_values)) + j] = value_names[i]
"""
        quscx__gktco += """            new_pivot_values[(i * len(pivot_values)) + j] = pivot_values[j]
"""
        quscx__gktco += """    column_index = bodo.hiframes.pd_multi_index_ext.init_multi_index((new_value_names, new_pivot_values), (None, columns_name), None)
"""
    else:
        quscx__gktco += """    column_index =  bodo.utils.conversion.index_from_array(pivot_values, columns_name)
"""
    gqgl__gtay = ', '.join(f'data_arrs_{i}' for i in range(len(fhpwf__yyuk)))
    quscx__gktco += f"""    table = bodo.hiframes.table.init_runtime_table_from_lists(({gqgl__gtay},), n_rows)
"""
    quscx__gktco += (
        '    return bodo.hiframes.pd_dataframe_ext.init_runtime_cols_dataframe(\n'
        )
    quscx__gktco += '        (table,), index, column_index\n'
    quscx__gktco += '    )\n'
    erl__khvv = {}
    aft__tul = {f'data_arr_typ_{i}': dstt__cyvo for i, dstt__cyvo in
        enumerate(fhpwf__yyuk)}
    yzgo__rgrzc = {'bodo': bodo, 'np': np, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'shuffle_table':
        shuffle_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'info_from_table': info_from_table, **aft__tul}
    exec(quscx__gktco, yzgo__rgrzc, erl__khvv)
    impl = erl__khvv['impl']
    return impl


def gen_pandas_parquet_metadata(column_names, data_types, index,
    write_non_range_index_to_metadata, write_rangeindex_to_metadata,
    partition_cols=None, is_runtime_columns=False):
    cwv__sgdn = {}
    cwv__sgdn['columns'] = []
    if partition_cols is None:
        partition_cols = []
    for col_name, gebsr__gyowj in zip(column_names, data_types):
        if col_name in partition_cols:
            continue
        xtyf__xpp = None
        if isinstance(gebsr__gyowj, bodo.DatetimeArrayType):
            quvso__btxq = 'datetimetz'
            ijfew__rub = 'datetime64[ns]'
            if isinstance(gebsr__gyowj.tz, int):
                rcqu__nsb = (bodo.libs.pd_datetime_arr_ext.
                    nanoseconds_to_offset(gebsr__gyowj.tz))
            else:
                rcqu__nsb = pd.DatetimeTZDtype(tz=gebsr__gyowj.tz).tz
            xtyf__xpp = {'timezone': pa.lib.tzinfo_to_string(rcqu__nsb)}
        elif isinstance(gebsr__gyowj, types.Array
            ) or gebsr__gyowj == boolean_array:
            quvso__btxq = ijfew__rub = gebsr__gyowj.dtype.name
            if ijfew__rub.startswith('datetime'):
                quvso__btxq = 'datetime'
        elif is_str_arr_type(gebsr__gyowj):
            quvso__btxq = 'unicode'
            ijfew__rub = 'object'
        elif gebsr__gyowj == binary_array_type:
            quvso__btxq = 'bytes'
            ijfew__rub = 'object'
        elif isinstance(gebsr__gyowj, DecimalArrayType):
            quvso__btxq = ijfew__rub = 'object'
        elif isinstance(gebsr__gyowj, IntegerArrayType):
            oazhz__pozi = gebsr__gyowj.dtype.name
            if oazhz__pozi.startswith('int'):
                quvso__btxq = 'Int' + oazhz__pozi[3:]
            elif oazhz__pozi.startswith('uint'):
                quvso__btxq = 'UInt' + oazhz__pozi[4:]
            else:
                if is_runtime_columns:
                    col_name = 'Runtime determined column of type'
                raise BodoError(
                    'to_parquet(): unknown dtype in nullable Integer column {} {}'
                    .format(col_name, gebsr__gyowj))
            ijfew__rub = gebsr__gyowj.dtype.name
        elif gebsr__gyowj == datetime_date_array_type:
            quvso__btxq = 'datetime'
            ijfew__rub = 'object'
        elif isinstance(gebsr__gyowj, (StructArrayType, ArrayItemArrayType)):
            quvso__btxq = 'object'
            ijfew__rub = 'object'
        else:
            if is_runtime_columns:
                col_name = 'Runtime determined column of type'
            raise BodoError(
                'to_parquet(): unsupported column type for metadata generation : {} {}'
                .format(col_name, gebsr__gyowj))
        fqcap__oxb = {'name': col_name, 'field_name': col_name,
            'pandas_type': quvso__btxq, 'numpy_type': ijfew__rub,
            'metadata': xtyf__xpp}
        cwv__sgdn['columns'].append(fqcap__oxb)
    if write_non_range_index_to_metadata:
        if isinstance(index, MultiIndexType):
            raise BodoError('to_parquet: MultiIndex not supported yet')
        if 'none' in index.name:
            tiake__lmq = '__index_level_0__'
            zre__qbh = None
        else:
            tiake__lmq = '%s'
            zre__qbh = '%s'
        cwv__sgdn['index_columns'] = [tiake__lmq]
        cwv__sgdn['columns'].append({'name': zre__qbh, 'field_name':
            tiake__lmq, 'pandas_type': index.pandas_type_name, 'numpy_type':
            index.numpy_type_name, 'metadata': None})
    elif write_rangeindex_to_metadata:
        cwv__sgdn['index_columns'] = [{'kind': 'range', 'name': '%s',
            'start': '%d', 'stop': '%d', 'step': '%d'}]
    else:
        cwv__sgdn['index_columns'] = []
    cwv__sgdn['pandas_version'] = pd.__version__
    return cwv__sgdn


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
        vbhgk__uuxot = []
        for gsf__hlcrc in partition_cols:
            try:
                idx = df.columns.index(gsf__hlcrc)
            except ValueError as hjox__flr:
                raise BodoError(
                    f'Partition column {gsf__hlcrc} is not in dataframe')
            vbhgk__uuxot.append(idx)
    else:
        partition_cols = None
    if not is_overload_none(index) and not is_overload_constant_bool(index):
        raise BodoError('to_parquet(): index must be a constant bool or None')
    from bodo.io.parquet_pio import parquet_write_table_cpp, parquet_write_table_partitioned_cpp
    ynk__djueo = isinstance(df.index, bodo.hiframes.pd_index_ext.RangeIndexType
        )
    fsnfm__lnsu = df.index is not None and (is_overload_true(_is_parallel) or
        not is_overload_true(_is_parallel) and not ynk__djueo)
    write_non_range_index_to_metadata = is_overload_true(index
        ) or is_overload_none(index) and (not ynk__djueo or
        is_overload_true(_is_parallel))
    write_rangeindex_to_metadata = is_overload_none(index
        ) and ynk__djueo and not is_overload_true(_is_parallel)
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
        jyfh__ikd = df.runtime_data_types
        wsla__fsji = len(jyfh__ikd)
        xtyf__xpp = gen_pandas_parquet_metadata([''] * wsla__fsji,
            jyfh__ikd, df.index, write_non_range_index_to_metadata,
            write_rangeindex_to_metadata, partition_cols=partition_cols,
            is_runtime_columns=True)
        spr__tdjfk = xtyf__xpp['columns'][:wsla__fsji]
        xtyf__xpp['columns'] = xtyf__xpp['columns'][wsla__fsji:]
        spr__tdjfk = [json.dumps(dxfd__ixcyv).replace('""', '{0}') for
            dxfd__ixcyv in spr__tdjfk]
        jxlb__ifyt = json.dumps(xtyf__xpp)
        jommk__oyski = '"columns": ['
        ozx__suk = jxlb__ifyt.find(jommk__oyski)
        if ozx__suk == -1:
            raise BodoError(
                'DataFrame.to_parquet(): Unexpected metadata string for runtime columns.  Please return the DataFrame to regular Python to update typing information.'
                )
        kuyu__enw = ozx__suk + len(jommk__oyski)
        xlin__jud = jxlb__ifyt[:kuyu__enw]
        jxlb__ifyt = jxlb__ifyt[kuyu__enw:]
        ixrc__jaau = len(xtyf__xpp['columns'])
    else:
        jxlb__ifyt = json.dumps(gen_pandas_parquet_metadata(df.columns, df.
            data, df.index, write_non_range_index_to_metadata,
            write_rangeindex_to_metadata, partition_cols=partition_cols,
            is_runtime_columns=False))
    if not is_overload_true(_is_parallel) and ynk__djueo:
        jxlb__ifyt = jxlb__ifyt.replace('"%d"', '%d')
        if df.index.name == 'RangeIndexType(none)':
            jxlb__ifyt = jxlb__ifyt.replace('"%s"', '%s')
    if not df.is_table_format:
        gun__zcbnf = ', '.join(
            'array_to_info(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}))'
            .format(i) for i in range(len(df.columns)))
    quscx__gktco = """def df_to_parquet(df, fname, engine='auto', compression='snappy', index=None, partition_cols=None, storage_options=None, _is_parallel=False):
"""
    if df.is_table_format:
        quscx__gktco += '    py_table = get_dataframe_table(df)\n'
        quscx__gktco += (
            '    table = py_table_to_cpp_table(py_table, py_table_typ)\n')
    else:
        quscx__gktco += '    info_list = [{}]\n'.format(gun__zcbnf)
        quscx__gktco += '    table = arr_info_list_to_table(info_list)\n'
    if df.has_runtime_cols:
        quscx__gktco += '    columns_index = get_dataframe_column_names(df)\n'
        quscx__gktco += '    names_arr = index_to_array(columns_index)\n'
        quscx__gktco += '    col_names = array_to_info(names_arr)\n'
    else:
        quscx__gktco += '    col_names = array_to_info(col_names_arr)\n'
    if is_overload_true(index) or is_overload_none(index) and fsnfm__lnsu:
        quscx__gktco += """    index_col = array_to_info(index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)))
"""
        mst__jzhx = True
    else:
        quscx__gktco += '    index_col = array_to_info(np.empty(0))\n'
        mst__jzhx = False
    if df.has_runtime_cols:
        quscx__gktco += '    columns_lst = []\n'
        quscx__gktco += '    num_cols = 0\n'
        for i in range(len(df.runtime_data_types)):
            quscx__gktco += f'    for _ in range(len(py_table.block_{i})):\n'
            quscx__gktco += f"""        columns_lst.append({spr__tdjfk[i]!r}.replace('{{0}}', '"' + names_arr[num_cols] + '"'))
"""
            quscx__gktco += '        num_cols += 1\n'
        if ixrc__jaau:
            quscx__gktco += "    columns_lst.append('')\n"
        quscx__gktco += '    columns_str = ", ".join(columns_lst)\n'
        quscx__gktco += ('    metadata = """' + xlin__jud +
            '""" + columns_str + """' + jxlb__ifyt + '"""\n')
    else:
        quscx__gktco += '    metadata = """' + jxlb__ifyt + '"""\n'
    quscx__gktco += '    if compression is None:\n'
    quscx__gktco += "        compression = 'none'\n"
    quscx__gktco += '    if df.index.name is not None:\n'
    quscx__gktco += '        name_ptr = df.index.name\n'
    quscx__gktco += '    else:\n'
    quscx__gktco += "        name_ptr = 'null'\n"
    quscx__gktco += f"""    bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel=_is_parallel)
"""
    ciizj__utrx = None
    if partition_cols:
        ciizj__utrx = pd.array([col_name for col_name in df.columns if 
            col_name not in partition_cols])
        hfet__wlcbt = ', '.join(
            f'array_to_info(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).dtype.categories.values)'
             for i in range(len(df.columns)) if isinstance(df.data[i],
            CategoricalArrayType) and i in vbhgk__uuxot)
        if hfet__wlcbt:
            quscx__gktco += '    cat_info_list = [{}]\n'.format(hfet__wlcbt)
            quscx__gktco += (
                '    cat_table = arr_info_list_to_table(cat_info_list)\n')
        else:
            quscx__gktco += '    cat_table = table\n'
        quscx__gktco += (
            '    col_names_no_partitions = array_to_info(col_names_no_parts_arr)\n'
            )
        quscx__gktco += (
            f'    part_cols_idxs = np.array({vbhgk__uuxot}, dtype=np.int32)\n')
        quscx__gktco += (
            '    parquet_write_table_partitioned_cpp(unicode_to_utf8(fname),\n'
            )
        quscx__gktco += """                            table, col_names, col_names_no_partitions, cat_table,
"""
        quscx__gktco += (
            '                            part_cols_idxs.ctypes, len(part_cols_idxs),\n'
            )
        quscx__gktco += (
            '                            unicode_to_utf8(compression),\n')
        quscx__gktco += '                            _is_parallel,\n'
        quscx__gktco += (
            '                            unicode_to_utf8(bucket_region))\n')
        quscx__gktco += '    delete_table_decref_arrays(table)\n'
        quscx__gktco += '    delete_info_decref_array(index_col)\n'
        quscx__gktco += (
            '    delete_info_decref_array(col_names_no_partitions)\n')
        quscx__gktco += '    delete_info_decref_array(col_names)\n'
        if hfet__wlcbt:
            quscx__gktco += '    delete_table_decref_arrays(cat_table)\n'
    elif write_rangeindex_to_metadata:
        quscx__gktco += '    parquet_write_table_cpp(unicode_to_utf8(fname),\n'
        quscx__gktco += (
            '                            table, col_names, index_col,\n')
        quscx__gktco += '                            ' + str(mst__jzhx) + ',\n'
        quscx__gktco += (
            '                            unicode_to_utf8(metadata),\n')
        quscx__gktco += (
            '                            unicode_to_utf8(compression),\n')
        quscx__gktco += (
            '                            _is_parallel, 1, df.index.start,\n')
        quscx__gktco += (
            '                            df.index.stop, df.index.step,\n')
        quscx__gktco += (
            '                            unicode_to_utf8(name_ptr),\n')
        quscx__gktco += (
            '                            unicode_to_utf8(bucket_region))\n')
        quscx__gktco += '    delete_table_decref_arrays(table)\n'
        quscx__gktco += '    delete_info_decref_array(index_col)\n'
        quscx__gktco += '    delete_info_decref_array(col_names)\n'
    else:
        quscx__gktco += '    parquet_write_table_cpp(unicode_to_utf8(fname),\n'
        quscx__gktco += (
            '                            table, col_names, index_col,\n')
        quscx__gktco += '                            ' + str(mst__jzhx) + ',\n'
        quscx__gktco += (
            '                            unicode_to_utf8(metadata),\n')
        quscx__gktco += (
            '                            unicode_to_utf8(compression),\n')
        quscx__gktco += (
            '                            _is_parallel, 0, 0, 0, 0,\n')
        quscx__gktco += (
            '                            unicode_to_utf8(name_ptr),\n')
        quscx__gktco += (
            '                            unicode_to_utf8(bucket_region))\n')
        quscx__gktco += '    delete_table_decref_arrays(table)\n'
        quscx__gktco += '    delete_info_decref_array(index_col)\n'
        quscx__gktco += '    delete_info_decref_array(col_names)\n'
    erl__khvv = {}
    if df.has_runtime_cols:
        nayr__unhe = None
    else:
        for fomb__bobl in df.columns:
            if not isinstance(fomb__bobl, str):
                raise BodoError(
                    'DataFrame.to_parquet(): parquet must have string column names'
                    )
        nayr__unhe = pd.array(df.columns)
    exec(quscx__gktco, {'np': np, 'bodo': bodo, 'unicode_to_utf8':
        unicode_to_utf8, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table,
        'str_arr_from_sequence': str_arr_from_sequence,
        'parquet_write_table_cpp': parquet_write_table_cpp,
        'parquet_write_table_partitioned_cpp':
        parquet_write_table_partitioned_cpp, 'index_to_array':
        index_to_array, 'delete_info_decref_array':
        delete_info_decref_array, 'delete_table_decref_arrays':
        delete_table_decref_arrays, 'col_names_arr': nayr__unhe,
        'py_table_to_cpp_table': py_table_to_cpp_table, 'py_table_typ': df.
        table_type, 'get_dataframe_table': get_dataframe_table,
        'col_names_no_parts_arr': ciizj__utrx, 'get_dataframe_column_names':
        get_dataframe_column_names, 'fix_arr_dtype': fix_arr_dtype,
        'decode_if_dict_array': decode_if_dict_array,
        'decode_if_dict_table': decode_if_dict_table}, erl__khvv)
    oteoz__izcv = erl__khvv['df_to_parquet']
    return oteoz__izcv


def to_sql_exception_guard(df, name, con, schema=None, if_exists='fail',
    index=True, index_label=None, chunksize=None, dtype=None, method=None,
    _is_table_create=False, _is_parallel=False):
    nerpc__wpcc = 'all_ok'
    lfr__ong = urlparse(con).scheme
    if _is_parallel and bodo.get_rank() == 0:
        zhbmc__shnrr = 100
        if chunksize is None:
            svgdh__onbv = zhbmc__shnrr
        else:
            svgdh__onbv = min(chunksize, zhbmc__shnrr)
        if _is_table_create:
            df = df.iloc[:svgdh__onbv, :]
        else:
            df = df.iloc[svgdh__onbv:, :]
            if len(df) == 0:
                return nerpc__wpcc
    if lfr__ong == 'snowflake':
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
            df.columns = [(twp__cwjmx.upper() if twp__cwjmx.islower() else
                twp__cwjmx) for twp__cwjmx in df.columns]
        except ImportError as hjox__flr:
            nerpc__wpcc = (
                "Snowflake Python connector packages not found. Using 'to_sql' with Snowflake requires both snowflake-sqlalchemy and snowflake-connector-python. These can be installed by calling 'conda install -c conda-forge snowflake-sqlalchemy snowflake-connector-python' or 'pip install snowflake-sqlalchemy snowflake-connector-python'."
                )
            return nerpc__wpcc
    try:
        df.to_sql(name, con, schema, if_exists, index, index_label,
            chunksize, dtype, method)
    except Exception as jrqxn__saypg:
        nerpc__wpcc = jrqxn__saypg.args[0]
    return nerpc__wpcc


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
        yfhmi__ahkx = bodo.libs.distributed_api.get_rank()
        nerpc__wpcc = 'unset'
        if yfhmi__ahkx != 0:
            nerpc__wpcc = bcast_scalar(nerpc__wpcc)
        elif yfhmi__ahkx == 0:
            nerpc__wpcc = to_sql_exception_guard_encaps(df, name, con,
                schema, if_exists, index, index_label, chunksize, dtype,
                method, True, _is_parallel)
            nerpc__wpcc = bcast_scalar(nerpc__wpcc)
        if_exists = 'append'
        if _is_parallel and nerpc__wpcc == 'all_ok':
            nerpc__wpcc = to_sql_exception_guard_encaps(df, name, con,
                schema, if_exists, index, index_label, chunksize, dtype,
                method, False, _is_parallel)
        if nerpc__wpcc != 'all_ok':
            print('err_msg=', nerpc__wpcc)
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
        lwfkt__oruiy = get_overload_const_str(path_or_buf)
        if lwfkt__oruiy.endswith(('.gz', '.bz2', '.zip', '.xz')):
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
        qojh__fokdg = bodo.io.fs_io.get_s3_bucket_region_njit(path_or_buf,
            parallel=False)
        if lines and orient == 'records':
            bodo.hiframes.pd_dataframe_ext._json_write(unicode_to_utf8(
                path_or_buf), unicode_to_utf8(D), 0, len(D), False, True,
                unicode_to_utf8(qojh__fokdg))
            bodo.utils.utils.check_and_propagate_cpp_exception()
        else:
            bodo.hiframes.pd_dataframe_ext._json_write(unicode_to_utf8(
                path_or_buf), unicode_to_utf8(D), 0, len(D), False, False,
                unicode_to_utf8(qojh__fokdg))
            bodo.utils.utils.check_and_propagate_cpp_exception()
    return _impl


@overload(pd.get_dummies, inline='always', no_unliteral=True)
def get_dummies(data, prefix=None, prefix_sep='_', dummy_na=False, columns=
    None, sparse=False, drop_first=False, dtype=None):
    fcx__lwqnq = {'prefix': prefix, 'prefix_sep': prefix_sep, 'dummy_na':
        dummy_na, 'columns': columns, 'sparse': sparse, 'drop_first':
        drop_first, 'dtype': dtype}
    eimv__ttylq = {'prefix': None, 'prefix_sep': '_', 'dummy_na': False,
        'columns': None, 'sparse': False, 'drop_first': False, 'dtype': None}
    check_unsupported_args('pandas.get_dummies', fcx__lwqnq, eimv__ttylq,
        package_name='pandas', module_name='General')
    if not categorical_can_construct_dataframe(data):
        raise BodoError(
            'pandas.get_dummies() only support categorical data types with explicitly known categories'
            )
    quscx__gktco = """def impl(data, prefix=None, prefix_sep='_', dummy_na=False, columns=None, sparse=False, drop_first=False, dtype=None,):
"""
    if isinstance(data, SeriesType):
        vcrg__hxtj = data.data.dtype.categories
        quscx__gktco += (
            '  data_values = bodo.hiframes.pd_series_ext.get_series_data(data)\n'
            )
    else:
        vcrg__hxtj = data.dtype.categories
        quscx__gktco += '  data_values = data\n'
    mbdx__zpxsp = len(vcrg__hxtj)
    quscx__gktco += """  codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(data_values)
"""
    quscx__gktco += '  numba.parfors.parfor.init_prange()\n'
    quscx__gktco += '  n = len(data_values)\n'
    for i in range(mbdx__zpxsp):
        quscx__gktco += '  data_arr_{} = np.empty(n, np.uint8)\n'.format(i)
    quscx__gktco += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    quscx__gktco += '      if bodo.libs.array_kernels.isna(data_values, i):\n'
    for bbng__uptmt in range(mbdx__zpxsp):
        quscx__gktco += '          data_arr_{}[i] = 0\n'.format(bbng__uptmt)
    quscx__gktco += '      else:\n'
    for djl__blux in range(mbdx__zpxsp):
        quscx__gktco += '          data_arr_{0}[i] = codes[i] == {0}\n'.format(
            djl__blux)
    gun__zcbnf = ', '.join(f'data_arr_{i}' for i in range(mbdx__zpxsp))
    index = 'bodo.hiframes.pd_index_ext.init_range_index(0, n, 1, None)'
    if isinstance(vcrg__hxtj[0], np.datetime64):
        vcrg__hxtj = tuple(pd.Timestamp(twp__cwjmx) for twp__cwjmx in
            vcrg__hxtj)
    elif isinstance(vcrg__hxtj[0], np.timedelta64):
        vcrg__hxtj = tuple(pd.Timedelta(twp__cwjmx) for twp__cwjmx in
            vcrg__hxtj)
    return bodo.hiframes.dataframe_impl._gen_init_df(quscx__gktco,
        vcrg__hxtj, gun__zcbnf, index)


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
    for rall__snv in pd_unsupported:
        fname = mod_name + '.' + rall__snv.__name__
        overload(rall__snv, no_unliteral=True)(create_unsupported_overload(
            fname))


def _install_dataframe_unsupported():
    for bmzv__vskn in dataframe_unsupported_attrs:
        buq__mskbr = 'DataFrame.' + bmzv__vskn
        overload_attribute(DataFrameType, bmzv__vskn)(
            create_unsupported_overload(buq__mskbr))
    for fname in dataframe_unsupported:
        buq__mskbr = 'DataFrame.' + fname + '()'
        overload_method(DataFrameType, fname)(create_unsupported_overload(
            buq__mskbr))


_install_pd_unsupported('pandas', pd_unsupported)
_install_pd_unsupported('pandas.util', pd_util_unsupported)
_install_dataframe_unsupported()
