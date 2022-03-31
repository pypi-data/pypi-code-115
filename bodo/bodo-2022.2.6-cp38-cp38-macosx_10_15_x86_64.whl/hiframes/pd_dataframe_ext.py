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
            hwusw__jmhu = f'{len(self.data)} columns of types {set(self.data)}'
            pyhxm__jcx = (
                f"('{self.columns[0]}', '{self.columns[1]}', ..., '{self.columns[-1]}')"
                )
            return (
                f'dataframe({hwusw__jmhu}, {self.index}, {pyhxm__jcx}, {self.dist}, {self.is_table_format})'
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
            gslec__cxcv = (self.index if self.index == other.index else
                self.index.unify(typingctx, other.index))
            data = tuple(ogyki__hqjh.unify(typingctx, ykw__wxcd) if 
                ogyki__hqjh != ykw__wxcd else ogyki__hqjh for ogyki__hqjh,
                ykw__wxcd in zip(self.data, other.data))
            dist = Distribution(min(self.dist.value, other.dist.value))
            if gslec__cxcv is not None and None not in data:
                return DataFrameType(data, gslec__cxcv, self.columns, dist,
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
        return all(ogyki__hqjh.is_precise() for ogyki__hqjh in self.data
            ) and self.index.is_precise()

    def replace_col_type(self, col_name, new_type):
        if col_name not in self.columns:
            raise ValueError(
                f"DataFrameType.replace_col_type replaced column must be found in the DataFrameType. '{col_name}' not found in DataFrameType with columns {self.columns}"
                )
        odvsv__pvaj = self.columns.index(col_name)
        hdhs__ddyj = tuple(list(self.data[:odvsv__pvaj]) + [new_type] +
            list(self.data[odvsv__pvaj + 1:]))
        return DataFrameType(hdhs__ddyj, self.index, self.columns, self.
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
        owwoj__iiyob = [('data', data_typ), ('index', fe_type.df_type.index
            ), ('parent', types.pyobject)]
        if fe_type.df_type.has_runtime_cols:
            owwoj__iiyob.append(('columns', fe_type.df_type.
                runtime_colname_typ))
        super(DataFramePayloadModel, self).__init__(dmm, fe_type, owwoj__iiyob)


@register_model(DataFrameType)
class DataFrameModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = DataFramePayloadType(fe_type)
        owwoj__iiyob = [('meminfo', types.MemInfoPointer(payload_type)), (
            'parent', types.pyobject)]
        super(DataFrameModel, self).__init__(dmm, fe_type, owwoj__iiyob)


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
        ple__kdfwo = 'n',
        vlzf__akmb = {'n': 5}
        qna__lah, hul__dly = bodo.utils.typing.fold_typing_args(func_name,
            args, kws, ple__kdfwo, vlzf__akmb)
        lurvv__tmcmx = hul__dly[0]
        if not is_overload_int(lurvv__tmcmx):
            raise BodoError(f"{func_name}(): 'n' must be an Integer")
        soc__ffi = df.copy(is_table_format=False)
        return soc__ffi(*hul__dly).replace(pysig=qna__lah)

    @bound_function('df.corr')
    def resolve_corr(self, df, args, kws):
        func_name = 'DataFrame.corr'
        check_runtime_cols_unsupported(df, f'{func_name}()')
        rmv__lfter = (df,) + args
        ple__kdfwo = 'df', 'method', 'min_periods'
        vlzf__akmb = {'method': 'pearson', 'min_periods': 1}
        lmr__kdj = 'method',
        qna__lah, hul__dly = bodo.utils.typing.fold_typing_args(func_name,
            rmv__lfter, kws, ple__kdfwo, vlzf__akmb, lmr__kdj)
        wznr__pms = hul__dly[2]
        if not is_overload_int(wznr__pms):
            raise BodoError(f"{func_name}(): 'min_periods' must be an Integer")
        vxe__cwpka = []
        oqbe__scu = []
        for plvey__qmn, ovt__nsz in zip(df.columns, df.data):
            if bodo.utils.typing._is_pandas_numeric_dtype(ovt__nsz.dtype):
                vxe__cwpka.append(plvey__qmn)
                oqbe__scu.append(types.Array(types.float64, 1, 'A'))
        if len(vxe__cwpka) == 0:
            raise_bodo_error('DataFrame.corr(): requires non-empty dataframe')
        oqbe__scu = tuple(oqbe__scu)
        vxe__cwpka = tuple(vxe__cwpka)
        index_typ = bodo.utils.typing.type_col_to_index(vxe__cwpka)
        soc__ffi = DataFrameType(oqbe__scu, index_typ, vxe__cwpka)
        return soc__ffi(*hul__dly).replace(pysig=qna__lah)

    @bound_function('df.pipe', no_unliteral=True)
    def resolve_pipe(self, df, args, kws):
        check_runtime_cols_unsupported(df, 'DataFrame.pipe()')
        return bodo.hiframes.pd_groupby_ext.resolve_obj_pipe(self, df, args,
            kws, 'DataFrame')

    @bound_function('df.apply', no_unliteral=True)
    def resolve_apply(self, df, args, kws):
        check_runtime_cols_unsupported(df, 'DataFrame.apply()')
        kws = dict(kws)
        mtd__yuvj = args[0] if len(args) > 0 else kws.pop('func', None)
        axis = args[1] if len(args) > 1 else kws.pop('axis', types.literal(0))
        mok__fwpgg = args[2] if len(args) > 2 else kws.pop('raw', types.
            literal(False))
        qfbnx__lser = args[3] if len(args) > 3 else kws.pop('result_type',
            types.none)
        qqo__nzm = args[4] if len(args) > 4 else kws.pop('args', types.
            Tuple([]))
        tkr__lpb = dict(raw=mok__fwpgg, result_type=qfbnx__lser)
        frjah__leqsm = dict(raw=False, result_type=None)
        check_unsupported_args('Dataframe.apply', tkr__lpb, frjah__leqsm,
            package_name='pandas', module_name='DataFrame')
        ymcu__xsfpm = True
        if types.unliteral(mtd__yuvj) == types.unicode_type:
            if not is_overload_constant_str(mtd__yuvj):
                raise BodoError(
                    f'DataFrame.apply(): string argument (for builtins) must be a compile time constant'
                    )
            ymcu__xsfpm = False
        if not is_overload_constant_int(axis):
            raise BodoError(
                'Dataframe.apply(): axis argument must be a compile time constant.'
                )
        ejn__oshhf = get_overload_const_int(axis)
        if ymcu__xsfpm and ejn__oshhf != 1:
            raise BodoError(
                'Dataframe.apply(): only axis=1 supported for user-defined functions'
                )
        elif ejn__oshhf not in (0, 1):
            raise BodoError('Dataframe.apply(): axis must be either 0 or 1')
        wdc__lag = []
        for arr_typ in df.data:
            cmc__pfbhq = SeriesType(arr_typ.dtype, arr_typ, df.index,
                string_type)
            vsn__kny = self.context.resolve_function_type(operator.getitem,
                (SeriesIlocType(cmc__pfbhq), types.int64), {}).return_type
            wdc__lag.append(vsn__kny)
        qua__hius = types.none
        qczha__uxfc = HeterogeneousIndexType(types.BaseTuple.from_types(
            tuple(types.literal(plvey__qmn) for plvey__qmn in df.columns)),
            None)
        kxkp__ldux = types.BaseTuple.from_types(wdc__lag)
        njia__trlfd = df.index.dtype
        if njia__trlfd == types.NPDatetime('ns'):
            njia__trlfd = bodo.pd_timestamp_type
        if njia__trlfd == types.NPTimedelta('ns'):
            njia__trlfd = bodo.pd_timedelta_type
        if is_heterogeneous_tuple_type(kxkp__ldux):
            fykuy__igact = HeterogeneousSeriesType(kxkp__ldux, qczha__uxfc,
                njia__trlfd)
        else:
            fykuy__igact = SeriesType(kxkp__ldux.dtype, kxkp__ldux,
                qczha__uxfc, njia__trlfd)
        plmfv__vsege = fykuy__igact,
        if qqo__nzm is not None:
            plmfv__vsege += tuple(qqo__nzm.types)
        try:
            if not ymcu__xsfpm:
                ujoqc__mehav = bodo.utils.transform.get_udf_str_return_type(df,
                    get_overload_const_str(mtd__yuvj), self.context,
                    'DataFrame.apply', axis if ejn__oshhf == 1 else None)
            else:
                ujoqc__mehav = get_const_func_output_type(mtd__yuvj,
                    plmfv__vsege, kws, self.context, numba.core.registry.
                    cpu_target.target_context)
        except Exception as ngs__urc:
            raise_bodo_error(get_udf_error_msg('DataFrame.apply()', ngs__urc))
        if ymcu__xsfpm:
            if not (is_overload_constant_int(axis) and 
                get_overload_const_int(axis) == 1):
                raise BodoError(
                    'Dataframe.apply(): only user-defined functions with axis=1 supported'
                    )
            if isinstance(ujoqc__mehav, (SeriesType, HeterogeneousSeriesType)
                ) and ujoqc__mehav.const_info is None:
                raise BodoError(
                    'Invalid Series output in UDF (Series with constant length and constant Index value expected)'
                    )
            if isinstance(ujoqc__mehav, HeterogeneousSeriesType):
                pwxc__xkvxw, pxzvx__ldor = ujoqc__mehav.const_info
                ffbn__xtnhj = tuple(dtype_to_array_type(pdklh__qnhno) for
                    pdklh__qnhno in ujoqc__mehav.data.types)
                jeoi__ccck = DataFrameType(ffbn__xtnhj, df.index, pxzvx__ldor)
            elif isinstance(ujoqc__mehav, SeriesType):
                ubymi__eclpt, pxzvx__ldor = ujoqc__mehav.const_info
                ffbn__xtnhj = tuple(dtype_to_array_type(ujoqc__mehav.dtype) for
                    pwxc__xkvxw in range(ubymi__eclpt))
                jeoi__ccck = DataFrameType(ffbn__xtnhj, df.index, pxzvx__ldor)
            else:
                smsy__fro = get_udf_out_arr_type(ujoqc__mehav)
                jeoi__ccck = SeriesType(smsy__fro.dtype, smsy__fro, df.
                    index, None)
        else:
            jeoi__ccck = ujoqc__mehav
        jsea__vjfyp = ', '.join("{} = ''".format(ogyki__hqjh) for
            ogyki__hqjh in kws.keys())
        trlpj__orgjg = f"""def apply_stub(func, axis=0, raw=False, result_type=None, args=(), {jsea__vjfyp}):
"""
        trlpj__orgjg += '    pass\n'
        ozh__jhzmb = {}
        exec(trlpj__orgjg, {}, ozh__jhzmb)
        eqnwi__gqea = ozh__jhzmb['apply_stub']
        qna__lah = numba.core.utils.pysignature(eqnwi__gqea)
        pbqhm__ngi = (mtd__yuvj, axis, mok__fwpgg, qfbnx__lser, qqo__nzm
            ) + tuple(kws.values())
        return signature(jeoi__ccck, *pbqhm__ngi).replace(pysig=qna__lah)

    @bound_function('df.plot', no_unliteral=True)
    def resolve_plot(self, df, args, kws):
        func_name = 'DataFrame.plot'
        check_runtime_cols_unsupported(df, f'{func_name}()')
        ple__kdfwo = ('x', 'y', 'kind', 'figsize', 'ax', 'subplots',
            'sharex', 'sharey', 'layout', 'use_index', 'title', 'grid',
            'legend', 'style', 'logx', 'logy', 'loglog', 'xticks', 'yticks',
            'xlim', 'ylim', 'rot', 'fontsize', 'colormap', 'table', 'yerr',
            'xerr', 'secondary_y', 'sort_columns', 'xlabel', 'ylabel',
            'position', 'stacked', 'mark_right', 'include_bool', 'backend')
        vlzf__akmb = {'x': None, 'y': None, 'kind': 'line', 'figsize': None,
            'ax': None, 'subplots': False, 'sharex': None, 'sharey': False,
            'layout': None, 'use_index': True, 'title': None, 'grid': None,
            'legend': True, 'style': None, 'logx': False, 'logy': False,
            'loglog': False, 'xticks': None, 'yticks': None, 'xlim': None,
            'ylim': None, 'rot': None, 'fontsize': None, 'colormap': None,
            'table': False, 'yerr': None, 'xerr': None, 'secondary_y': 
            False, 'sort_columns': False, 'xlabel': None, 'ylabel': None,
            'position': 0.5, 'stacked': False, 'mark_right': True,
            'include_bool': False, 'backend': None}
        lmr__kdj = ('subplots', 'sharex', 'sharey', 'layout', 'use_index',
            'grid', 'style', 'logx', 'logy', 'loglog', 'xlim', 'ylim',
            'rot', 'colormap', 'table', 'yerr', 'xerr', 'sort_columns',
            'secondary_y', 'colorbar', 'position', 'stacked', 'mark_right',
            'include_bool', 'backend')
        qna__lah, hul__dly = bodo.utils.typing.fold_typing_args(func_name,
            args, kws, ple__kdfwo, vlzf__akmb, lmr__kdj)
        owzy__uoot = hul__dly[2]
        if not is_overload_constant_str(owzy__uoot):
            raise BodoError(
                f"{func_name}: kind must be a constant string and one of ('line', 'scatter')."
                )
        oach__ygt = hul__dly[0]
        if not is_overload_none(oach__ygt) and not (is_overload_int(
            oach__ygt) or is_overload_constant_str(oach__ygt)):
            raise BodoError(
                f'{func_name}: x must be a constant column name, constant integer, or None.'
                )
        if is_overload_constant_str(oach__ygt):
            xlux__idbz = get_overload_const_str(oach__ygt)
            if xlux__idbz not in df.columns:
                raise BodoError(f'{func_name}: {xlux__idbz} column not found.')
        elif is_overload_int(oach__ygt):
            grcqh__bly = get_overload_const_int(oach__ygt)
            if grcqh__bly > len(df.columns):
                raise BodoError(
                    f'{func_name}: x: {grcqh__bly} is out of bounds for axis 0 with size {len(df.columns)}'
                    )
            oach__ygt = df.columns[oach__ygt]
        wyioi__hpvg = hul__dly[1]
        if not is_overload_none(wyioi__hpvg) and not (is_overload_int(
            wyioi__hpvg) or is_overload_constant_str(wyioi__hpvg)):
            raise BodoError(
                'df.plot(): y must be a constant column name, constant integer, or None.'
                )
        if is_overload_constant_str(wyioi__hpvg):
            uqszp__yle = get_overload_const_str(wyioi__hpvg)
            if uqszp__yle not in df.columns:
                raise BodoError(f'{func_name}: {uqszp__yle} column not found.')
        elif is_overload_int(wyioi__hpvg):
            ekmof__skn = get_overload_const_int(wyioi__hpvg)
            if ekmof__skn > len(df.columns):
                raise BodoError(
                    f'{func_name}: y: {ekmof__skn} is out of bounds for axis 0 with size {len(df.columns)}'
                    )
            wyioi__hpvg = df.columns[wyioi__hpvg]
        ame__xkvz = hul__dly[3]
        if not is_overload_none(ame__xkvz) and not is_tuple_like_type(ame__xkvz
            ):
            raise BodoError(
                f'{func_name}: figsize must be a constant numeric tuple (width, height) or None.'
                )
        ajfhb__zxa = hul__dly[10]
        if not is_overload_none(ajfhb__zxa) and not is_overload_constant_str(
            ajfhb__zxa):
            raise BodoError(
                f'{func_name}: title must be a constant string or None.')
        dipc__pds = hul__dly[12]
        if not is_overload_bool(dipc__pds):
            raise BodoError(f'{func_name}: legend must be a boolean type.')
        behyu__gva = hul__dly[17]
        if not is_overload_none(behyu__gva) and not is_tuple_like_type(
            behyu__gva):
            raise BodoError(
                f'{func_name}: xticks must be a constant tuple or None.')
        zsqs__zxypw = hul__dly[18]
        if not is_overload_none(zsqs__zxypw) and not is_tuple_like_type(
            zsqs__zxypw):
            raise BodoError(
                f'{func_name}: yticks must be a constant tuple or None.')
        lqx__vku = hul__dly[22]
        if not is_overload_none(lqx__vku) and not is_overload_int(lqx__vku):
            raise BodoError(
                f'{func_name}: fontsize must be an integer or None.')
        pnic__ecle = hul__dly[29]
        if not is_overload_none(pnic__ecle) and not is_overload_constant_str(
            pnic__ecle):
            raise BodoError(
                f'{func_name}: xlabel must be a constant string or None.')
        hskd__ewi = hul__dly[30]
        if not is_overload_none(hskd__ewi) and not is_overload_constant_str(
            hskd__ewi):
            raise BodoError(
                f'{func_name}: ylabel must be a constant string or None.')
        htd__czo = types.List(types.mpl_line_2d_type)
        owzy__uoot = get_overload_const_str(owzy__uoot)
        if owzy__uoot == 'scatter':
            if is_overload_none(oach__ygt) and is_overload_none(wyioi__hpvg):
                raise BodoError(
                    f'{func_name}: {owzy__uoot} requires an x and y column.')
            elif is_overload_none(oach__ygt):
                raise BodoError(
                    f'{func_name}: {owzy__uoot} x column is missing.')
            elif is_overload_none(wyioi__hpvg):
                raise BodoError(
                    f'{func_name}: {owzy__uoot} y column is missing.')
            htd__czo = types.mpl_path_collection_type
        elif owzy__uoot != 'line':
            raise BodoError(f'{func_name}: {owzy__uoot} plot is not supported.'
                )
        return signature(htd__czo, *hul__dly).replace(pysig=qna__lah)

    def generic_resolve(self, df, attr):
        if self._is_existing_attr(attr):
            return
        check_runtime_cols_unsupported(df,
            'Acessing DataFrame columns by attribute')
        if attr in df.columns:
            cnm__dwdcn = df.columns.index(attr)
            arr_typ = df.data[cnm__dwdcn]
            return SeriesType(arr_typ.dtype, arr_typ, df.index, types.
                StringLiteral(attr))
        if len(df.columns) > 0 and isinstance(df.columns[0], tuple):
            hchpz__cud = []
            hdhs__ddyj = []
            rszc__utrs = False
            for i, rxd__dwzzq in enumerate(df.columns):
                if rxd__dwzzq[0] != attr:
                    continue
                rszc__utrs = True
                hchpz__cud.append(rxd__dwzzq[1] if len(rxd__dwzzq) == 2 else
                    rxd__dwzzq[1:])
                hdhs__ddyj.append(df.data[i])
            if rszc__utrs:
                return DataFrameType(tuple(hdhs__ddyj), df.index, tuple(
                    hchpz__cud))


DataFrameAttribute._no_unliteral = True


@overload(operator.getitem, no_unliteral=True)
def namedtuple_getitem_overload(tup, idx):
    if isinstance(tup, types.BaseNamedTuple) and is_overload_constant_str(idx):
        buzjt__braqw = get_overload_const_str(idx)
        val_ind = tup.instance_class._fields.index(buzjt__braqw)
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
        agft__ktapd = builder.extract_value(payload.data, i)
        context.nrt.decref(builder, df_type.data[i], agft__ktapd)
    context.nrt.decref(builder, df_type.index, payload.index)


def define_df_dtor(context, builder, df_type, payload_type):
    gwd__ybghn = builder.module
    ltl__undm = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    doqz__gst = cgutils.get_or_insert_function(gwd__ybghn, ltl__undm, name=
        '.dtor.df.{}'.format(df_type))
    if not doqz__gst.is_declaration:
        return doqz__gst
    doqz__gst.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(doqz__gst.append_basic_block())
    exhyd__ukfst = doqz__gst.args[0]
    osygu__uwwyx = context.get_value_type(payload_type).as_pointer()
    miq__rsdit = builder.bitcast(exhyd__ukfst, osygu__uwwyx)
    payload = context.make_helper(builder, payload_type, ref=miq__rsdit)
    decref_df_data(context, builder, payload, df_type)
    has_parent = cgutils.is_not_null(builder, payload.parent)
    with builder.if_then(has_parent):
        dbdu__itq = context.get_python_api(builder)
        qgjh__byy = dbdu__itq.gil_ensure()
        dbdu__itq.decref(payload.parent)
        dbdu__itq.gil_release(qgjh__byy)
    builder.ret_void()
    return doqz__gst


def construct_dataframe(context, builder, df_type, data_tup, index_val,
    parent=None, colnames=None):
    payload_type = DataFramePayloadType(df_type)
    sqd__ggxk = cgutils.create_struct_proxy(payload_type)(context, builder)
    sqd__ggxk.data = data_tup
    sqd__ggxk.index = index_val
    if colnames is not None:
        assert df_type.has_runtime_cols, 'construct_dataframe can only provide colnames if columns are determined at runtime'
        sqd__ggxk.columns = colnames
    mxdpv__pbojq = context.get_value_type(payload_type)
    rqfm__vqspb = context.get_abi_sizeof(mxdpv__pbojq)
    puk__jyq = define_df_dtor(context, builder, df_type, payload_type)
    hxox__awdw = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, rqfm__vqspb), puk__jyq)
    lvr__sggw = context.nrt.meminfo_data(builder, hxox__awdw)
    yfj__rgwo = builder.bitcast(lvr__sggw, mxdpv__pbojq.as_pointer())
    xoqyj__mncw = cgutils.create_struct_proxy(df_type)(context, builder)
    xoqyj__mncw.meminfo = hxox__awdw
    if parent is None:
        xoqyj__mncw.parent = cgutils.get_null_value(xoqyj__mncw.parent.type)
    else:
        xoqyj__mncw.parent = parent
        sqd__ggxk.parent = parent
        has_parent = cgutils.is_not_null(builder, parent)
        with builder.if_then(has_parent):
            dbdu__itq = context.get_python_api(builder)
            qgjh__byy = dbdu__itq.gil_ensure()
            dbdu__itq.incref(parent)
            dbdu__itq.gil_release(qgjh__byy)
    builder.store(sqd__ggxk._getvalue(), yfj__rgwo)
    return xoqyj__mncw._getvalue()


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
        ldavd__bbut = [data_typ.dtype.arr_types.dtype] * len(data_typ.dtype
            .arr_types)
    else:
        ldavd__bbut = [pdklh__qnhno for pdklh__qnhno in data_typ.dtype.
            arr_types]
    wtfw__swadk = DataFrameType(tuple(ldavd__bbut + [colnames_index_typ]),
        index_typ, None, is_table_format=True)

    def codegen(context, builder, signature, args):
        df_type = signature.return_type
        data_tup, index, col_names = args
        parent = None
        dhdtf__jof = construct_dataframe(context, builder, df_type,
            data_tup, index, parent, col_names)
        context.nrt.incref(builder, data_typ, data_tup)
        context.nrt.incref(builder, index_typ, index)
        context.nrt.incref(builder, colnames_index_typ, col_names)
        return dhdtf__jof
    sig = signature(wtfw__swadk, data_typ, index_typ, colnames_index_typ)
    return sig, codegen


@intrinsic
def init_dataframe(typingctx, data_tup_typ, index_typ, col_names_typ=None):
    assert is_pd_index_type(index_typ) or isinstance(index_typ, MultiIndexType
        ), 'init_dataframe(): invalid index type'
    ubymi__eclpt = len(data_tup_typ.types)
    if ubymi__eclpt == 0:
        column_names = ()
    elif isinstance(col_names_typ, types.TypeRef):
        column_names = col_names_typ.instance_type.columns
    else:
        column_names = get_const_tup_vals(col_names_typ)
    if ubymi__eclpt == 1 and isinstance(data_tup_typ.types[0], TableType):
        ubymi__eclpt = len(data_tup_typ.types[0].arr_types)
    assert len(column_names
        ) == ubymi__eclpt, 'init_dataframe(): number of column names does not match number of columns'
    is_table_format = False
    cfvf__qsr = data_tup_typ.types
    if ubymi__eclpt != 0 and isinstance(data_tup_typ.types[0], TableType):
        cfvf__qsr = data_tup_typ.types[0].arr_types
        is_table_format = True
    wtfw__swadk = DataFrameType(cfvf__qsr, index_typ, column_names,
        is_table_format=is_table_format)

    def codegen(context, builder, signature, args):
        df_type = signature.return_type
        data_tup = args[0]
        index_val = args[1]
        parent = None
        if is_table_format:
            lru__vndzx = cgutils.create_struct_proxy(wtfw__swadk.table_type)(
                context, builder, builder.extract_value(data_tup, 0))
            parent = lru__vndzx.parent
        dhdtf__jof = construct_dataframe(context, builder, df_type,
            data_tup, index_val, parent, None)
        context.nrt.incref(builder, data_tup_typ, data_tup)
        context.nrt.incref(builder, index_typ, index_val)
        return dhdtf__jof
    sig = signature(wtfw__swadk, data_tup_typ, index_typ, col_names_typ)
    return sig, codegen


@intrinsic
def has_parent(typingctx, df=None):
    check_runtime_cols_unsupported(df, 'has_parent')

    def codegen(context, builder, sig, args):
        xoqyj__mncw = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        return cgutils.is_not_null(builder, xoqyj__mncw.parent)
    return signature(types.bool_, df), codegen


@intrinsic
def _column_needs_unboxing(typingctx, df_typ, i_typ=None):
    check_runtime_cols_unsupported(df_typ, '_column_needs_unboxing')
    assert isinstance(df_typ, DataFrameType) and is_overload_constant_int(i_typ
        )

    def codegen(context, builder, sig, args):
        sqd__ggxk = get_dataframe_payload(context, builder, df_typ, args[0])
        cufnj__taj = get_overload_const_int(i_typ)
        arr_typ = df_typ.data[cufnj__taj]
        if df_typ.is_table_format:
            lru__vndzx = cgutils.create_struct_proxy(df_typ.table_type)(context
                , builder, builder.extract_value(sqd__ggxk.data, 0))
            rkjtu__zypi = df_typ.table_type.type_to_blk[arr_typ]
            hqfzx__ainar = getattr(lru__vndzx, f'block_{rkjtu__zypi}')
            cxsm__rpkc = ListInstance(context, builder, types.List(arr_typ),
                hqfzx__ainar)
            xfpx__qonf = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[cufnj__taj])
            agft__ktapd = cxsm__rpkc.getitem(xfpx__qonf)
        else:
            agft__ktapd = builder.extract_value(sqd__ggxk.data, cufnj__taj)
        fnjqu__wrdhy = cgutils.alloca_once_value(builder, agft__ktapd)
        eitk__bmqzo = cgutils.alloca_once_value(builder, context.
            get_constant_null(arr_typ))
        return is_ll_eq(builder, fnjqu__wrdhy, eitk__bmqzo)
    return signature(types.bool_, df_typ, i_typ), codegen


def get_dataframe_payload(context, builder, df_type, value):
    hxox__awdw = cgutils.create_struct_proxy(df_type)(context, builder, value
        ).meminfo
    payload_type = DataFramePayloadType(df_type)
    payload = context.nrt.meminfo_data(builder, hxox__awdw)
    osygu__uwwyx = context.get_value_type(payload_type).as_pointer()
    payload = builder.bitcast(payload, osygu__uwwyx)
    return context.make_helper(builder, payload_type, ref=payload)


@intrinsic
def _get_dataframe_data(typingctx, df_typ=None):
    check_runtime_cols_unsupported(df_typ, '_get_dataframe_data')
    wtfw__swadk = types.Tuple(df_typ.data)
    if df_typ.is_table_format:
        wtfw__swadk = types.Tuple([TableType(df_typ.data)])
    sig = signature(wtfw__swadk, df_typ)

    def codegen(context, builder, signature, args):
        sqd__ggxk = get_dataframe_payload(context, builder, signature.args[
            0], args[0])
        return impl_ret_borrowed(context, builder, signature.return_type,
            sqd__ggxk.data)
    return sig, codegen


@intrinsic
def get_dataframe_index(typingctx, df_typ=None):

    def codegen(context, builder, signature, args):
        sqd__ggxk = get_dataframe_payload(context, builder, signature.args[
            0], args[0])
        return impl_ret_borrowed(context, builder, df_typ.index, sqd__ggxk.
            index)
    wtfw__swadk = df_typ.index
    sig = signature(wtfw__swadk, df_typ)
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
        soc__ffi = df.data[i]
        return soc__ffi(*args)


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
        sqd__ggxk = get_dataframe_payload(context, builder, signature.args[
            0], args[0])
        return impl_ret_borrowed(context, builder, df_typ.table_type,
            builder.extract_value(sqd__ggxk.data, 0))
    return df_typ.table_type(df_typ), codegen


@intrinsic
def get_dataframe_column_names(typingctx, df_typ=None):
    assert df_typ.has_runtime_cols, 'get_dataframe_column_names() expects columns to be determined at runtime'

    def codegen(context, builder, signature, args):
        sqd__ggxk = get_dataframe_payload(context, builder, signature.args[
            0], args[0])
        return impl_ret_borrowed(context, builder, df_typ.
            runtime_colname_typ, sqd__ggxk.columns)
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
    kxkp__ldux = self.typemap[data_tup.name]
    if any(is_tuple_like_type(pdklh__qnhno) for pdklh__qnhno in kxkp__ldux.
        types):
        return None
    if equiv_set.has_shape(data_tup):
        atng__ghesd = equiv_set.get_shape(data_tup)
        if len(atng__ghesd) > 1:
            equiv_set.insert_equiv(*atng__ghesd)
        if len(atng__ghesd) > 0:
            qczha__uxfc = self.typemap[index.name]
            if not isinstance(qczha__uxfc, HeterogeneousIndexType
                ) and equiv_set.has_shape(index):
                equiv_set.insert_equiv(atng__ghesd[0], index)
            return ArrayAnalysis.AnalyzeResult(shape=(atng__ghesd[0], len(
                atng__ghesd)), pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_dataframe_ext_init_dataframe
    ) = init_dataframe_equiv


def get_dataframe_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    ynam__lhgf = args[0]
    data_types = self.typemap[ynam__lhgf.name].data
    if any(is_tuple_like_type(pdklh__qnhno) for pdklh__qnhno in data_types):
        return None
    if equiv_set.has_shape(ynam__lhgf):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            ynam__lhgf)[0], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_data
    ) = get_dataframe_data_equiv


def get_dataframe_index_equiv(self, scope, equiv_set, loc, args, kws):
    from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
    assert len(args) == 1 and not kws
    ynam__lhgf = args[0]
    qczha__uxfc = self.typemap[ynam__lhgf.name].index
    if isinstance(qczha__uxfc, HeterogeneousIndexType):
        return None
    if equiv_set.has_shape(ynam__lhgf):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            ynam__lhgf)[0], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_index
    ) = get_dataframe_index_equiv


def get_dataframe_table_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    ynam__lhgf = args[0]
    if equiv_set.has_shape(ynam__lhgf):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            ynam__lhgf), pre=[])


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_table
    ) = get_dataframe_table_equiv


def get_dataframe_column_names_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    ynam__lhgf = args[0]
    if equiv_set.has_shape(ynam__lhgf):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            ynam__lhgf)[1], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_column_names
    ) = get_dataframe_column_names_equiv


@intrinsic
def set_dataframe_data(typingctx, df_typ, c_ind_typ, arr_typ=None):
    check_runtime_cols_unsupported(df_typ, 'set_dataframe_data')
    assert is_overload_constant_int(c_ind_typ)
    cufnj__taj = get_overload_const_int(c_ind_typ)
    if df_typ.data[cufnj__taj] != arr_typ:
        raise BodoError(
            'Changing dataframe column data type inplace is not supported in conditionals/loops or for dataframe arguments'
            )

    def codegen(context, builder, signature, args):
        fif__auhvo, pwxc__xkvxw, szgqz__xhdcx = args
        sqd__ggxk = get_dataframe_payload(context, builder, df_typ, fif__auhvo)
        if df_typ.is_table_format:
            lru__vndzx = cgutils.create_struct_proxy(df_typ.table_type)(context
                , builder, builder.extract_value(sqd__ggxk.data, 0))
            rkjtu__zypi = df_typ.table_type.type_to_blk[arr_typ]
            hqfzx__ainar = getattr(lru__vndzx, f'block_{rkjtu__zypi}')
            cxsm__rpkc = ListInstance(context, builder, types.List(arr_typ),
                hqfzx__ainar)
            xfpx__qonf = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[cufnj__taj])
            cxsm__rpkc.setitem(xfpx__qonf, szgqz__xhdcx, True)
        else:
            agft__ktapd = builder.extract_value(sqd__ggxk.data, cufnj__taj)
            context.nrt.decref(builder, df_typ.data[cufnj__taj], agft__ktapd)
            sqd__ggxk.data = builder.insert_value(sqd__ggxk.data,
                szgqz__xhdcx, cufnj__taj)
            context.nrt.incref(builder, arr_typ, szgqz__xhdcx)
        xoqyj__mncw = cgutils.create_struct_proxy(df_typ)(context, builder,
            value=fif__auhvo)
        payload_type = DataFramePayloadType(df_typ)
        miq__rsdit = context.nrt.meminfo_data(builder, xoqyj__mncw.meminfo)
        osygu__uwwyx = context.get_value_type(payload_type).as_pointer()
        miq__rsdit = builder.bitcast(miq__rsdit, osygu__uwwyx)
        builder.store(sqd__ggxk._getvalue(), miq__rsdit)
        return impl_ret_borrowed(context, builder, df_typ, fif__auhvo)
    sig = signature(df_typ, df_typ, c_ind_typ, arr_typ)
    return sig, codegen


@intrinsic
def set_df_index(typingctx, df_t, index_t=None):
    check_runtime_cols_unsupported(df_t, 'set_df_index')

    def codegen(context, builder, signature, args):
        ayy__vcet = args[0]
        index_val = args[1]
        df_typ = signature.args[0]
        ulip__exa = cgutils.create_struct_proxy(df_typ)(context, builder,
            value=ayy__vcet)
        xuxom__nwk = get_dataframe_payload(context, builder, df_typ, ayy__vcet)
        xoqyj__mncw = construct_dataframe(context, builder, signature.
            return_type, xuxom__nwk.data, index_val, ulip__exa.parent, None)
        context.nrt.incref(builder, index_t, index_val)
        context.nrt.incref(builder, types.Tuple(df_t.data), xuxom__nwk.data)
        return xoqyj__mncw
    wtfw__swadk = DataFrameType(df_t.data, index_t, df_t.columns, df_t.dist,
        df_t.is_table_format)
    sig = signature(wtfw__swadk, df_t, index_t)
    return sig, codegen


@intrinsic
def set_df_column_with_reflect(typingctx, df_type, cname_type, arr_type=None):
    check_runtime_cols_unsupported(df_type, 'set_df_column_with_reflect')
    assert is_literal_type(cname_type), 'constant column name expected'
    col_name = get_literal_value(cname_type)
    ubymi__eclpt = len(df_type.columns)
    yywr__gpa = ubymi__eclpt
    xlxve__aoh = df_type.data
    column_names = df_type.columns
    index_typ = df_type.index
    jtd__zth = col_name not in df_type.columns
    cufnj__taj = ubymi__eclpt
    if jtd__zth:
        xlxve__aoh += arr_type,
        column_names += col_name,
        yywr__gpa += 1
    else:
        cufnj__taj = df_type.columns.index(col_name)
        xlxve__aoh = tuple(arr_type if i == cufnj__taj else xlxve__aoh[i] for
            i in range(ubymi__eclpt))

    def codegen(context, builder, signature, args):
        fif__auhvo, pwxc__xkvxw, szgqz__xhdcx = args
        in_dataframe_payload = get_dataframe_payload(context, builder,
            df_type, fif__auhvo)
        wkfp__bxbb = cgutils.create_struct_proxy(df_type)(context, builder,
            value=fif__auhvo)
        if df_type.is_table_format:
            qbmsa__kis = df_type.table_type
            ryg__uoc = builder.extract_value(in_dataframe_payload.data, 0)
            mnb__qgu = TableType(xlxve__aoh)
            gafmd__tnjxl = set_table_data_codegen(context, builder,
                qbmsa__kis, ryg__uoc, mnb__qgu, arr_type, szgqz__xhdcx,
                cufnj__taj, jtd__zth)
            data_tup = context.make_tuple(builder, types.Tuple([mnb__qgu]),
                [gafmd__tnjxl])
        else:
            cfvf__qsr = [(builder.extract_value(in_dataframe_payload.data,
                i) if i != cufnj__taj else szgqz__xhdcx) for i in range(
                ubymi__eclpt)]
            if jtd__zth:
                cfvf__qsr.append(szgqz__xhdcx)
            for ynam__lhgf, omht__beclc in zip(cfvf__qsr, xlxve__aoh):
                context.nrt.incref(builder, omht__beclc, ynam__lhgf)
            data_tup = context.make_tuple(builder, types.Tuple(xlxve__aoh),
                cfvf__qsr)
        index_val = in_dataframe_payload.index
        context.nrt.incref(builder, index_typ, index_val)
        zxg__gdbcv = construct_dataframe(context, builder, signature.
            return_type, data_tup, index_val, wkfp__bxbb.parent, None)
        if not jtd__zth and arr_type == df_type.data[cufnj__taj]:
            decref_df_data(context, builder, in_dataframe_payload, df_type)
            payload_type = DataFramePayloadType(df_type)
            miq__rsdit = context.nrt.meminfo_data(builder, wkfp__bxbb.meminfo)
            osygu__uwwyx = context.get_value_type(payload_type).as_pointer()
            miq__rsdit = builder.bitcast(miq__rsdit, osygu__uwwyx)
            uim__hmcb = get_dataframe_payload(context, builder, df_type,
                zxg__gdbcv)
            builder.store(uim__hmcb._getvalue(), miq__rsdit)
            context.nrt.incref(builder, index_typ, index_val)
            if df_type.is_table_format:
                context.nrt.incref(builder, mnb__qgu, builder.extract_value
                    (data_tup, 0))
            else:
                for ynam__lhgf, omht__beclc in zip(cfvf__qsr, xlxve__aoh):
                    context.nrt.incref(builder, omht__beclc, ynam__lhgf)
        has_parent = cgutils.is_not_null(builder, wkfp__bxbb.parent)
        with builder.if_then(has_parent):
            dbdu__itq = context.get_python_api(builder)
            qgjh__byy = dbdu__itq.gil_ensure()
            ppp__kgwr = context.get_env_manager(builder)
            context.nrt.incref(builder, arr_type, szgqz__xhdcx)
            plvey__qmn = numba.core.pythonapi._BoxContext(context, builder,
                dbdu__itq, ppp__kgwr)
            ibt__trd = plvey__qmn.pyapi.from_native_value(arr_type,
                szgqz__xhdcx, plvey__qmn.env_manager)
            if isinstance(col_name, str):
                tnof__mhgkv = context.insert_const_string(builder.module,
                    col_name)
                yhh__uvrup = dbdu__itq.string_from_string(tnof__mhgkv)
            else:
                assert isinstance(col_name, int)
                yhh__uvrup = dbdu__itq.long_from_longlong(context.
                    get_constant(types.intp, col_name))
            dbdu__itq.object_setitem(wkfp__bxbb.parent, yhh__uvrup, ibt__trd)
            dbdu__itq.decref(ibt__trd)
            dbdu__itq.decref(yhh__uvrup)
            dbdu__itq.gil_release(qgjh__byy)
        return zxg__gdbcv
    wtfw__swadk = DataFrameType(xlxve__aoh, index_typ, column_names,
        df_type.dist, df_type.is_table_format)
    sig = signature(wtfw__swadk, df_type, cname_type, arr_type)
    return sig, codegen


@lower_constant(DataFrameType)
def lower_constant_dataframe(context, builder, df_type, pyval):
    check_runtime_cols_unsupported(df_type, 'lowering a constant DataFrame')
    ubymi__eclpt = len(pyval.columns)
    cfvf__qsr = tuple(pyval.iloc[:, i].values for i in range(ubymi__eclpt))
    if df_type.is_table_format:
        lru__vndzx = context.get_constant_generic(builder, df_type.
            table_type, Table(cfvf__qsr))
        data_tup = lir.Constant.literal_struct([lru__vndzx])
    else:
        data_tup = lir.Constant.literal_struct([context.
            get_constant_generic(builder, df_type.data[i], rxd__dwzzq) for 
            i, rxd__dwzzq in enumerate(cfvf__qsr)])
    index_val = context.get_constant_generic(builder, df_type.index, pyval.
        index)
    aqbc__nkjc = context.get_constant_null(types.pyobject)
    payload = lir.Constant.literal_struct([data_tup, index_val, aqbc__nkjc])
    payload = cgutils.global_constant(builder, '.const.payload', payload
        ).bitcast(cgutils.voidptr_t)
    jqcvx__tuwz = context.get_constant(types.int64, -1)
    glzyi__pzqh = context.get_constant_null(types.voidptr)
    hxox__awdw = lir.Constant.literal_struct([jqcvx__tuwz, glzyi__pzqh,
        glzyi__pzqh, payload, jqcvx__tuwz])
    hxox__awdw = cgutils.global_constant(builder, '.const.meminfo', hxox__awdw
        ).bitcast(cgutils.voidptr_t)
    return lir.Constant.literal_struct([hxox__awdw, aqbc__nkjc])


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
        gslec__cxcv = context.cast(builder, in_dataframe_payload.index,
            fromty.index, toty.index)
    else:
        gslec__cxcv = in_dataframe_payload.index
        context.nrt.incref(builder, fromty.index, gslec__cxcv)
    if (fromty.is_table_format == toty.is_table_format and fromty.data ==
        toty.data):
        hdhs__ddyj = in_dataframe_payload.data
        if fromty.is_table_format:
            context.nrt.incref(builder, types.Tuple([fromty.table_type]),
                hdhs__ddyj)
        else:
            context.nrt.incref(builder, types.BaseTuple.from_types(fromty.
                data), hdhs__ddyj)
    elif not fromty.is_table_format and toty.is_table_format:
        hdhs__ddyj = _cast_df_data_to_table_format(context, builder, fromty,
            toty, val, in_dataframe_payload)
    elif fromty.is_table_format and not toty.is_table_format:
        hdhs__ddyj = _cast_df_data_to_tuple_format(context, builder, fromty,
            toty, val, in_dataframe_payload)
    elif fromty.is_table_format and toty.is_table_format:
        hdhs__ddyj = _cast_df_data_keep_table_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    else:
        hdhs__ddyj = _cast_df_data_keep_tuple_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    return construct_dataframe(context, builder, toty, hdhs__ddyj,
        gslec__cxcv, in_dataframe_payload.parent, None)


def _cast_empty_df(context, builder, toty):
    eze__bbfsh = {}
    if isinstance(toty.index, RangeIndexType):
        index = 'bodo.hiframes.pd_index_ext.init_range_index(0, 0, 1, None)'
    else:
        qqm__uxyl = get_index_data_arr_types(toty.index)[0]
        iiu__lwts = bodo.utils.transform.get_type_alloc_counts(qqm__uxyl) - 1
        agi__vkc = ', '.join('0' for pwxc__xkvxw in range(iiu__lwts))
        index = (
            'bodo.utils.conversion.index_from_array(bodo.utils.utils.alloc_type(0, index_arr_type, ({}{})))'
            .format(agi__vkc, ', ' if iiu__lwts == 1 else ''))
        eze__bbfsh['index_arr_type'] = qqm__uxyl
    geyhd__bxdy = []
    for i, arr_typ in enumerate(toty.data):
        iiu__lwts = bodo.utils.transform.get_type_alloc_counts(arr_typ) - 1
        agi__vkc = ', '.join('0' for pwxc__xkvxw in range(iiu__lwts))
        zjdc__yqhyk = ('bodo.utils.utils.alloc_type(0, arr_type{}, ({}{}))'
            .format(i, agi__vkc, ', ' if iiu__lwts == 1 else ''))
        geyhd__bxdy.append(zjdc__yqhyk)
        eze__bbfsh[f'arr_type{i}'] = arr_typ
    geyhd__bxdy = ', '.join(geyhd__bxdy)
    trlpj__orgjg = 'def impl():\n'
    bsdxi__llai = bodo.hiframes.dataframe_impl._gen_init_df(trlpj__orgjg,
        toty.columns, geyhd__bxdy, index, eze__bbfsh)
    df = context.compile_internal(builder, bsdxi__llai, toty(), [])
    return df


def _cast_df_data_to_table_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting traditional DataFrame to table format')
    cst__oihzc = toty.table_type
    lru__vndzx = cgutils.create_struct_proxy(cst__oihzc)(context, builder)
    lru__vndzx.parent = in_dataframe_payload.parent
    for pdklh__qnhno, rkjtu__zypi in cst__oihzc.type_to_blk.items():
        twfql__hwpc = context.get_constant(types.int64, len(cst__oihzc.
            block_to_arr_ind[rkjtu__zypi]))
        pwxc__xkvxw, kzcml__vnv = ListInstance.allocate_ex(context, builder,
            types.List(pdklh__qnhno), twfql__hwpc)
        kzcml__vnv.size = twfql__hwpc
        setattr(lru__vndzx, f'block_{rkjtu__zypi}', kzcml__vnv.value)
    for i, pdklh__qnhno in enumerate(fromty.data):
        hfpwx__upvw = toty.data[i]
        if pdklh__qnhno != hfpwx__upvw:
            gskpm__bevhs = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*gskpm__bevhs)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        agft__ktapd = builder.extract_value(in_dataframe_payload.data, i)
        if pdklh__qnhno != hfpwx__upvw:
            pjai__mvwk = context.cast(builder, agft__ktapd, pdklh__qnhno,
                hfpwx__upvw)
            gwfky__elpm = False
        else:
            pjai__mvwk = agft__ktapd
            gwfky__elpm = True
        rkjtu__zypi = cst__oihzc.type_to_blk[pdklh__qnhno]
        hqfzx__ainar = getattr(lru__vndzx, f'block_{rkjtu__zypi}')
        cxsm__rpkc = ListInstance(context, builder, types.List(pdklh__qnhno
            ), hqfzx__ainar)
        xfpx__qonf = context.get_constant(types.int64, cst__oihzc.
            block_offsets[i])
        cxsm__rpkc.setitem(xfpx__qonf, pjai__mvwk, gwfky__elpm)
    data_tup = context.make_tuple(builder, types.Tuple([cst__oihzc]), [
        lru__vndzx._getvalue()])
    return data_tup


def _cast_df_data_keep_tuple_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting traditional DataFrame columns')
    cfvf__qsr = []
    for i in range(len(fromty.data)):
        if fromty.data[i] != toty.data[i]:
            gskpm__bevhs = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*gskpm__bevhs)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
            agft__ktapd = builder.extract_value(in_dataframe_payload.data, i)
            pjai__mvwk = context.cast(builder, agft__ktapd, fromty.data[i],
                toty.data[i])
            gwfky__elpm = False
        else:
            pjai__mvwk = builder.extract_value(in_dataframe_payload.data, i)
            gwfky__elpm = True
        if gwfky__elpm:
            context.nrt.incref(builder, toty.data[i], pjai__mvwk)
        cfvf__qsr.append(pjai__mvwk)
    data_tup = context.make_tuple(builder, types.Tuple(toty.data), cfvf__qsr)
    return data_tup


def _cast_df_data_keep_table_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting table format DataFrame columns')
    qbmsa__kis = fromty.table_type
    ryg__uoc = cgutils.create_struct_proxy(qbmsa__kis)(context, builder,
        builder.extract_value(in_dataframe_payload.data, 0))
    mnb__qgu = toty.table_type
    gafmd__tnjxl = cgutils.create_struct_proxy(mnb__qgu)(context, builder)
    gafmd__tnjxl.parent = in_dataframe_payload.parent
    for pdklh__qnhno, rkjtu__zypi in mnb__qgu.type_to_blk.items():
        twfql__hwpc = context.get_constant(types.int64, len(mnb__qgu.
            block_to_arr_ind[rkjtu__zypi]))
        pwxc__xkvxw, kzcml__vnv = ListInstance.allocate_ex(context, builder,
            types.List(pdklh__qnhno), twfql__hwpc)
        kzcml__vnv.size = twfql__hwpc
        setattr(gafmd__tnjxl, f'block_{rkjtu__zypi}', kzcml__vnv.value)
    for i in range(len(fromty.data)):
        hrpc__yzkyu = fromty.data[i]
        hfpwx__upvw = toty.data[i]
        if hrpc__yzkyu != hfpwx__upvw:
            gskpm__bevhs = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*gskpm__bevhs)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        wfgd__bgv = qbmsa__kis.type_to_blk[hrpc__yzkyu]
        tupy__mqat = getattr(ryg__uoc, f'block_{wfgd__bgv}')
        hbm__gkjgo = ListInstance(context, builder, types.List(hrpc__yzkyu),
            tupy__mqat)
        nhqzp__gzcsb = context.get_constant(types.int64, qbmsa__kis.
            block_offsets[i])
        agft__ktapd = hbm__gkjgo.getitem(nhqzp__gzcsb)
        if hrpc__yzkyu != hfpwx__upvw:
            pjai__mvwk = context.cast(builder, agft__ktapd, hrpc__yzkyu,
                hfpwx__upvw)
            gwfky__elpm = False
        else:
            pjai__mvwk = agft__ktapd
            gwfky__elpm = True
        oddvm__yyvs = mnb__qgu.type_to_blk[pdklh__qnhno]
        kzcml__vnv = getattr(gafmd__tnjxl, f'block_{oddvm__yyvs}')
        jikg__gqtp = ListInstance(context, builder, types.List(hfpwx__upvw),
            kzcml__vnv)
        akkn__vnp = context.get_constant(types.int64, mnb__qgu.block_offsets[i]
            )
        jikg__gqtp.setitem(akkn__vnp, pjai__mvwk, gwfky__elpm)
    data_tup = context.make_tuple(builder, types.Tuple([mnb__qgu]), [
        gafmd__tnjxl._getvalue()])
    return data_tup


def _cast_df_data_to_tuple_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(fromty,
        'casting table format to traditional DataFrame')
    cst__oihzc = fromty.table_type
    lru__vndzx = cgutils.create_struct_proxy(cst__oihzc)(context, builder,
        builder.extract_value(in_dataframe_payload.data, 0))
    cfvf__qsr = []
    for i, pdklh__qnhno in enumerate(toty.data):
        hrpc__yzkyu = fromty.data[i]
        if pdklh__qnhno != hrpc__yzkyu:
            gskpm__bevhs = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*gskpm__bevhs)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        rkjtu__zypi = cst__oihzc.type_to_blk[pdklh__qnhno]
        hqfzx__ainar = getattr(lru__vndzx, f'block_{rkjtu__zypi}')
        cxsm__rpkc = ListInstance(context, builder, types.List(pdklh__qnhno
            ), hqfzx__ainar)
        xfpx__qonf = context.get_constant(types.int64, cst__oihzc.
            block_offsets[i])
        agft__ktapd = cxsm__rpkc.getitem(xfpx__qonf)
        if pdklh__qnhno != hrpc__yzkyu:
            pjai__mvwk = context.cast(builder, agft__ktapd, hrpc__yzkyu,
                pdklh__qnhno)
            gwfky__elpm = False
        else:
            pjai__mvwk = agft__ktapd
            gwfky__elpm = True
        if gwfky__elpm:
            context.nrt.incref(builder, pdklh__qnhno, pjai__mvwk)
        cfvf__qsr.append(pjai__mvwk)
    data_tup = context.make_tuple(builder, types.Tuple(toty.data), cfvf__qsr)
    return data_tup


@overload(pd.DataFrame, inline='always', no_unliteral=True)
def pd_dataframe_overload(data=None, index=None, columns=None, dtype=None,
    copy=False):
    if not is_overload_constant_bool(copy):
        raise BodoError(
            "pd.DataFrame(): 'copy' argument should be a constant boolean")
    copy = get_overload_const(copy)
    ijeo__nsf, geyhd__bxdy, index_arg = _get_df_args(data, index, columns,
        dtype, copy)
    ongbg__xyly = gen_const_tup(ijeo__nsf)
    trlpj__orgjg = (
        'def _init_df(data=None, index=None, columns=None, dtype=None, copy=False):\n'
        )
    trlpj__orgjg += (
        '  return bodo.hiframes.pd_dataframe_ext.init_dataframe({}, {}, {})\n'
        .format(geyhd__bxdy, index_arg, ongbg__xyly))
    ozh__jhzmb = {}
    exec(trlpj__orgjg, {'bodo': bodo, 'np': np}, ozh__jhzmb)
    ipl__ohydg = ozh__jhzmb['_init_df']
    return ipl__ohydg


@intrinsic
def _tuple_to_table_format_decoded(typingctx, df_typ):
    assert not df_typ.is_table_format, '_tuple_to_table_format requires a tuple format input'

    def codegen(context, builder, signature, args):
        return context.cast(builder, args[0], signature.args[0], signature.
            return_type)
    wtfw__swadk = DataFrameType(to_str_arr_if_dict_array(df_typ.data),
        df_typ.index, df_typ.columns, dist=df_typ.dist, is_table_format=True)
    sig = signature(wtfw__swadk, df_typ)
    return sig, codegen


@intrinsic
def _table_to_tuple_format_decoded(typingctx, df_typ):
    assert df_typ.is_table_format, '_tuple_to_table_format requires a table format input'

    def codegen(context, builder, signature, args):
        return context.cast(builder, args[0], signature.args[0], signature.
            return_type)
    wtfw__swadk = DataFrameType(to_str_arr_if_dict_array(df_typ.data),
        df_typ.index, df_typ.columns, dist=df_typ.dist, is_table_format=False)
    sig = signature(wtfw__swadk, df_typ)
    return sig, codegen


def _get_df_args(data, index, columns, dtype, copy):
    isy__treat = ''
    if not is_overload_none(dtype):
        isy__treat = '.astype(dtype)'
    index_is_none = is_overload_none(index)
    index_arg = 'bodo.utils.conversion.convert_to_index(index)'
    if isinstance(data, types.BaseTuple):
        if not data.types[0] == types.StringLiteral('__bodo_tup'):
            raise BodoError('pd.DataFrame tuple input data not supported yet')
        assert len(data.types) % 2 == 1, 'invalid const dict tuple structure'
        ubymi__eclpt = (len(data.types) - 1) // 2
        pqch__uzabr = [pdklh__qnhno.literal_value for pdklh__qnhno in data.
            types[1:ubymi__eclpt + 1]]
        data_val_types = dict(zip(pqch__uzabr, data.types[ubymi__eclpt + 1:]))
        cfvf__qsr = ['data[{}]'.format(i) for i in range(ubymi__eclpt + 1, 
            2 * ubymi__eclpt + 1)]
        data_dict = dict(zip(pqch__uzabr, cfvf__qsr))
        if is_overload_none(index):
            for i, pdklh__qnhno in enumerate(data.types[ubymi__eclpt + 1:]):
                if isinstance(pdklh__qnhno, SeriesType):
                    index_arg = (
                        'bodo.hiframes.pd_series_ext.get_series_index(data[{}])'
                        .format(ubymi__eclpt + 1 + i))
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
        zeggp__gvey = '.copy()' if copy else ''
        duzu__illti = get_overload_const_list(columns)
        ubymi__eclpt = len(duzu__illti)
        data_val_types = {plvey__qmn: data.copy(ndim=1) for plvey__qmn in
            duzu__illti}
        cfvf__qsr = ['data[:,{}]{}'.format(i, zeggp__gvey) for i in range(
            ubymi__eclpt)]
        data_dict = dict(zip(duzu__illti, cfvf__qsr))
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
    geyhd__bxdy = '({},)'.format(', '.join(
        'bodo.utils.conversion.coerce_to_array({}, True, scalar_to_arr_len={}){}'
        .format(data_dict[plvey__qmn], df_len, isy__treat) for plvey__qmn in
        col_names))
    if len(col_names) == 0:
        geyhd__bxdy = '()'
    return col_names, geyhd__bxdy, index_arg


def _get_df_len_from_info(data_dict, data_val_types, col_names,
    index_is_none, index_arg):
    df_len = '0'
    for plvey__qmn in col_names:
        if plvey__qmn in data_dict and is_iterable_type(data_val_types[
            plvey__qmn]):
            df_len = 'len({})'.format(data_dict[plvey__qmn])
            break
    if df_len == '0' and not index_is_none:
        df_len = f'len({index_arg})'
    return df_len


def _fill_null_arrays(data_dict, col_names, df_len, dtype):
    if all(plvey__qmn in data_dict for plvey__qmn in col_names):
        return
    if is_overload_none(dtype):
        dtype = 'bodo.string_array_type'
    else:
        dtype = 'bodo.utils.conversion.array_type_from_dtype(dtype)'
    fntky__mkqo = 'bodo.libs.array_kernels.gen_na_array({}, {})'.format(df_len,
        dtype)
    for plvey__qmn in col_names:
        if plvey__qmn not in data_dict:
            data_dict[plvey__qmn] = fntky__mkqo


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
            pdklh__qnhno = bodo.hiframes.pd_dataframe_ext.get_dataframe_table(
                df)
            return len(pdklh__qnhno)
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
        zioy__rywuo = idx.literal_value
        if isinstance(zioy__rywuo, int):
            soc__ffi = tup.types[zioy__rywuo]
        elif isinstance(zioy__rywuo, slice):
            soc__ffi = types.BaseTuple.from_types(tup.types[zioy__rywuo])
        return signature(soc__ffi, *args)


GetItemTuple.prefer_literal = True


@lower_builtin(operator.getitem, types.BaseTuple, types.IntegerLiteral)
@lower_builtin(operator.getitem, types.BaseTuple, types.SliceLiteral)
def getitem_tuple_lower(context, builder, sig, args):
    wqlbi__uzfgf, idx = sig.args
    idx = idx.literal_value
    tup, pwxc__xkvxw = args
    if isinstance(idx, int):
        if idx < 0:
            idx += len(wqlbi__uzfgf)
        if not 0 <= idx < len(wqlbi__uzfgf):
            raise IndexError('cannot index at %d in %s' % (idx, wqlbi__uzfgf))
        pxis__lmz = builder.extract_value(tup, idx)
    elif isinstance(idx, slice):
        dgoc__jcs = cgutils.unpack_tuple(builder, tup)[idx]
        pxis__lmz = context.make_tuple(builder, sig.return_type, dgoc__jcs)
    else:
        raise NotImplementedError('unexpected index %r for %s' % (idx, sig.
            args[0]))
    return impl_ret_borrowed(context, builder, sig.return_type, pxis__lmz)


def join_dummy(left_df, right_df, left_on, right_on, how, suffix_x,
    suffix_y, is_join, indicator, _bodo_na_equal, gen_cond):
    return left_df


@infer_global(join_dummy)
class JoinTyper(AbstractTemplate):

    def generic(self, args, kws):
        from bodo.hiframes.pd_dataframe_ext import DataFrameType
        from bodo.utils.typing import is_overload_str
        assert not kws
        (left_df, right_df, left_on, right_on, vej__cxh, suffix_x, suffix_y,
            is_join, indicator, _bodo_na_equal, wvvvb__abqp) = args
        left_on = get_overload_const_list(left_on)
        right_on = get_overload_const_list(right_on)
        zgmdo__qovy = set(left_on) & set(right_on)
        xkvby__yjq = set(left_df.columns) & set(right_df.columns)
        bsd__qtvpj = xkvby__yjq - zgmdo__qovy
        epbhb__jnzs = '$_bodo_index_' in left_on
        kwvhg__geg = '$_bodo_index_' in right_on
        how = get_overload_const_str(vej__cxh)
        pcib__vbp = how in {'left', 'outer'}
        fuoqm__dje = how in {'right', 'outer'}
        columns = []
        data = []
        if epbhb__jnzs:
            dfpk__qpp = bodo.utils.typing.get_index_data_arr_types(left_df.
                index)[0]
        else:
            dfpk__qpp = left_df.data[left_df.columns.index(left_on[0])]
        if kwvhg__geg:
            ktikm__zisg = bodo.utils.typing.get_index_data_arr_types(right_df
                .index)[0]
        else:
            ktikm__zisg = right_df.data[right_df.columns.index(right_on[0])]
        if epbhb__jnzs and not kwvhg__geg and not is_join.literal_value:
            bbgia__hwg = right_on[0]
            if bbgia__hwg in left_df.columns:
                columns.append(bbgia__hwg)
                if (ktikm__zisg == bodo.dict_str_arr_type and dfpk__qpp ==
                    bodo.string_array_type):
                    vav__udar = bodo.string_array_type
                else:
                    vav__udar = ktikm__zisg
                data.append(vav__udar)
        if kwvhg__geg and not epbhb__jnzs and not is_join.literal_value:
            btsp__ggpxu = left_on[0]
            if btsp__ggpxu in right_df.columns:
                columns.append(btsp__ggpxu)
                if (dfpk__qpp == bodo.dict_str_arr_type and ktikm__zisg ==
                    bodo.string_array_type):
                    vav__udar = bodo.string_array_type
                else:
                    vav__udar = dfpk__qpp
                data.append(vav__udar)
        for hrpc__yzkyu, jkd__khbk in zip(left_df.data, left_df.columns):
            columns.append(str(jkd__khbk) + suffix_x.literal_value if 
                jkd__khbk in bsd__qtvpj else jkd__khbk)
            if jkd__khbk in zgmdo__qovy:
                if hrpc__yzkyu == bodo.dict_str_arr_type:
                    hrpc__yzkyu = right_df.data[right_df.columns.index(
                        jkd__khbk)]
                data.append(hrpc__yzkyu)
            else:
                if (hrpc__yzkyu == bodo.dict_str_arr_type and jkd__khbk in
                    left_on):
                    if kwvhg__geg:
                        hrpc__yzkyu = ktikm__zisg
                    else:
                        yxob__vqipn = left_on.index(jkd__khbk)
                        kvxc__lbn = right_on[yxob__vqipn]
                        hrpc__yzkyu = right_df.data[right_df.columns.index(
                            kvxc__lbn)]
                if fuoqm__dje:
                    hrpc__yzkyu = to_nullable_type(hrpc__yzkyu)
                data.append(hrpc__yzkyu)
        for hrpc__yzkyu, jkd__khbk in zip(right_df.data, right_df.columns):
            if jkd__khbk not in zgmdo__qovy:
                columns.append(str(jkd__khbk) + suffix_y.literal_value if 
                    jkd__khbk in bsd__qtvpj else jkd__khbk)
                if (hrpc__yzkyu == bodo.dict_str_arr_type and jkd__khbk in
                    right_on):
                    if epbhb__jnzs:
                        hrpc__yzkyu = dfpk__qpp
                    else:
                        yxob__vqipn = right_on.index(jkd__khbk)
                        hds__zybc = left_on[yxob__vqipn]
                        hrpc__yzkyu = left_df.data[left_df.columns.index(
                            hds__zybc)]
                if pcib__vbp:
                    hrpc__yzkyu = to_nullable_type(hrpc__yzkyu)
                data.append(hrpc__yzkyu)
        vbs__mvyhl = get_overload_const_bool(indicator)
        if vbs__mvyhl:
            columns.append('_merge')
            data.append(bodo.CategoricalArrayType(bodo.PDCategoricalDtype((
                'left_only', 'right_only', 'both'), bodo.string_type, False)))
        index_typ = RangeIndexType(types.none)
        if epbhb__jnzs and kwvhg__geg and not is_overload_str(how, 'asof'):
            index_typ = left_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        elif epbhb__jnzs and not kwvhg__geg:
            index_typ = right_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        elif kwvhg__geg and not epbhb__jnzs:
            index_typ = left_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        bep__kgb = DataFrameType(tuple(data), index_typ, tuple(columns))
        return signature(bep__kgb, *args)


JoinTyper._no_unliteral = True


@lower_builtin(join_dummy, types.VarArg(types.Any))
def lower_join_dummy(context, builder, sig, args):
    xoqyj__mncw = cgutils.create_struct_proxy(sig.return_type)(context, builder
        )
    return xoqyj__mncw._getvalue()


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
    tkr__lpb = dict(join=join, join_axes=join_axes, keys=keys, levels=
        levels, names=names, verify_integrity=verify_integrity, sort=sort,
        copy=copy)
    vlzf__akmb = dict(join='outer', join_axes=None, keys=None, levels=None,
        names=None, verify_integrity=False, sort=None, copy=True)
    check_unsupported_args('pandas.concat', tkr__lpb, vlzf__akmb,
        package_name='pandas', module_name='General')
    trlpj__orgjg = """def impl(objs, axis=0, join='outer', join_axes=None, ignore_index=False, keys=None, levels=None, names=None, verify_integrity=False, sort=None, copy=True):
"""
    if axis == 1:
        if not isinstance(objs, types.BaseTuple):
            raise_bodo_error(
                'Only tuple argument for pd.concat(axis=1) expected')
        index = (
            'bodo.hiframes.pd_index_ext.init_range_index(0, len(objs[0]), 1, None)'
            )
        gxfj__mnf = 0
        geyhd__bxdy = []
        names = []
        for i, oofk__gyy in enumerate(objs.types):
            assert isinstance(oofk__gyy, (SeriesType, DataFrameType))
            check_runtime_cols_unsupported(oofk__gyy, 'pd.concat()')
            if isinstance(oofk__gyy, SeriesType):
                names.append(str(gxfj__mnf))
                gxfj__mnf += 1
                geyhd__bxdy.append(
                    'bodo.hiframes.pd_series_ext.get_series_data(objs[{}])'
                    .format(i))
            else:
                names.extend(oofk__gyy.columns)
                for kdg__iwebl in range(len(oofk__gyy.data)):
                    geyhd__bxdy.append(
                        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(objs[{}], {})'
                        .format(i, kdg__iwebl))
        return bodo.hiframes.dataframe_impl._gen_init_df(trlpj__orgjg,
            names, ', '.join(geyhd__bxdy), index)
    if axis != 0:
        raise_bodo_error('pd.concat(): axis must be 0 or 1')
    if isinstance(objs, types.BaseTuple) and isinstance(objs.types[0],
        DataFrameType):
        assert all(isinstance(pdklh__qnhno, DataFrameType) for pdklh__qnhno in
            objs.types)
        dtrc__uwb = []
        for df in objs.types:
            check_runtime_cols_unsupported(df, 'pd.concat()')
            dtrc__uwb.extend(df.columns)
        dtrc__uwb = list(dict.fromkeys(dtrc__uwb).keys())
        ldavd__bbut = {}
        for gxfj__mnf, plvey__qmn in enumerate(dtrc__uwb):
            for df in objs.types:
                if plvey__qmn in df.columns:
                    ldavd__bbut['arr_typ{}'.format(gxfj__mnf)] = df.data[df
                        .columns.index(plvey__qmn)]
                    break
        assert len(ldavd__bbut) == len(dtrc__uwb)
        crxhy__rfrff = []
        for gxfj__mnf, plvey__qmn in enumerate(dtrc__uwb):
            args = []
            for i, df in enumerate(objs.types):
                if plvey__qmn in df.columns:
                    cufnj__taj = df.columns.index(plvey__qmn)
                    args.append(
                        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(objs[{}], {})'
                        .format(i, cufnj__taj))
                else:
                    args.append(
                        'bodo.libs.array_kernels.gen_na_array(len(objs[{}]), arr_typ{})'
                        .format(i, gxfj__mnf))
            trlpj__orgjg += ('  A{} = bodo.libs.array_kernels.concat(({},))\n'
                .format(gxfj__mnf, ', '.join(args)))
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
        return bodo.hiframes.dataframe_impl._gen_init_df(trlpj__orgjg,
            dtrc__uwb, ', '.join('A{}'.format(i) for i in range(len(
            dtrc__uwb))), index, ldavd__bbut)
    if isinstance(objs, types.BaseTuple) and isinstance(objs.types[0],
        SeriesType):
        assert all(isinstance(pdklh__qnhno, SeriesType) for pdklh__qnhno in
            objs.types)
        trlpj__orgjg += ('  out_arr = bodo.libs.array_kernels.concat(({},))\n'
            .format(', '.join(
            'bodo.hiframes.pd_series_ext.get_series_data(objs[{}])'.format(
            i) for i in range(len(objs.types)))))
        if ignore_index:
            trlpj__orgjg += """  index = bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr), 1, None)
"""
        else:
            trlpj__orgjg += (
                """  index = bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(({},)))
"""
                .format(', '.join(
                'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(objs[{}]))'
                .format(i) for i in range(len(objs.types)))))
        trlpj__orgjg += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index)\n'
            )
        ozh__jhzmb = {}
        exec(trlpj__orgjg, {'bodo': bodo, 'np': np, 'numba': numba}, ozh__jhzmb
            )
        return ozh__jhzmb['impl']
    if isinstance(objs, types.List) and isinstance(objs.dtype, DataFrameType):
        check_runtime_cols_unsupported(objs.dtype, 'pd.concat()')
        df_type = objs.dtype
        for gxfj__mnf, plvey__qmn in enumerate(df_type.columns):
            trlpj__orgjg += '  arrs{} = []\n'.format(gxfj__mnf)
            trlpj__orgjg += '  for i in range(len(objs)):\n'
            trlpj__orgjg += '    df = objs[i]\n'
            trlpj__orgjg += (
                """    arrs{0}.append(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0}))
"""
                .format(gxfj__mnf))
            trlpj__orgjg += (
                '  out_arr{0} = bodo.libs.array_kernels.concat(arrs{0})\n'.
                format(gxfj__mnf))
        if ignore_index:
            index = (
                'bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr0), 1, None)'
                )
        else:
            trlpj__orgjg += '  arrs_index = []\n'
            trlpj__orgjg += '  for i in range(len(objs)):\n'
            trlpj__orgjg += '    df = objs[i]\n'
            trlpj__orgjg += """    arrs_index.append(bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)))
"""
            if objs.dtype.index.name_typ == types.none:
                name = None
            else:
                name = objs.dtype.index.name_typ.literal_value
            index = f"""bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(arrs_index), {name!r})
"""
        return bodo.hiframes.dataframe_impl._gen_init_df(trlpj__orgjg,
            df_type.columns, ', '.join('out_arr{}'.format(i) for i in range
            (len(df_type.columns))), index)
    if isinstance(objs, types.List) and isinstance(objs.dtype, SeriesType):
        trlpj__orgjg += '  arrs = []\n'
        trlpj__orgjg += '  for i in range(len(objs)):\n'
        trlpj__orgjg += (
            '    arrs.append(bodo.hiframes.pd_series_ext.get_series_data(objs[i]))\n'
            )
        trlpj__orgjg += '  out_arr = bodo.libs.array_kernels.concat(arrs)\n'
        if ignore_index:
            trlpj__orgjg += """  index = bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr), 1, None)
"""
        else:
            trlpj__orgjg += '  arrs_index = []\n'
            trlpj__orgjg += '  for i in range(len(objs)):\n'
            trlpj__orgjg += '    S = objs[i]\n'
            trlpj__orgjg += """    arrs_index.append(bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(S)))
"""
            trlpj__orgjg += """  index = bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(arrs_index))
"""
        trlpj__orgjg += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index)\n'
            )
        ozh__jhzmb = {}
        exec(trlpj__orgjg, {'bodo': bodo, 'np': np, 'numba': numba}, ozh__jhzmb
            )
        return ozh__jhzmb['impl']
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
        wtfw__swadk = df.copy(index=index, is_table_format=False)
        return signature(wtfw__swadk, *args)


SortDummyTyper._no_unliteral = True


@lower_builtin(sort_values_dummy, types.VarArg(types.Any))
def lower_sort_values_dummy(context, builder, sig, args):
    if sig.return_type == types.none:
        return
    oqzn__abp = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return oqzn__abp._getvalue()


@overload_method(DataFrameType, 'itertuples', inline='always', no_unliteral
    =True)
def itertuples_overload(df, index=True, name='Pandas'):
    check_runtime_cols_unsupported(df, 'DataFrame.itertuples()')
    tkr__lpb = dict(index=index, name=name)
    vlzf__akmb = dict(index=True, name='Pandas')
    check_unsupported_args('DataFrame.itertuples', tkr__lpb, vlzf__akmb,
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
        ldavd__bbut = (types.Array(types.int64, 1, 'C'),) + df.data
        rlfvx__ilc = bodo.hiframes.dataframe_impl.DataFrameTupleIterator(
            columns, ldavd__bbut)
        return signature(rlfvx__ilc, *args)


@lower_builtin(itertuples_dummy, types.VarArg(types.Any))
def lower_itertuples_dummy(context, builder, sig, args):
    oqzn__abp = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return oqzn__abp._getvalue()


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
    oqzn__abp = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return oqzn__abp._getvalue()


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
    oqzn__abp = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return oqzn__abp._getvalue()


@numba.generated_jit(nopython=True)
def pivot_impl(index_tup, columns_tup, values_tup, pivot_values,
    index_names, columns_name, value_names, check_duplicates=True, parallel
    =False):
    if not is_overload_constant_bool(check_duplicates):
        raise BodoError(
            'pivot_impl(): check_duplicates must be a constant boolean')
    xdh__mggmc = get_overload_const_bool(check_duplicates)
    gscy__tglfk = not is_overload_none(value_names)
    humlv__eqor = isinstance(values_tup, types.UniTuple)
    if humlv__eqor:
        euqya__tnw = [to_nullable_type(values_tup.dtype)]
    else:
        euqya__tnw = [to_nullable_type(omht__beclc) for omht__beclc in
            values_tup]
    trlpj__orgjg = 'def impl(\n'
    trlpj__orgjg += """    index_tup, columns_tup, values_tup, pivot_values, index_names, columns_name, value_names, check_duplicates=True, parallel=False
"""
    trlpj__orgjg += '):\n'
    trlpj__orgjg += '    if parallel:\n'
    sscrr__vrnb = ', '.join([f'array_to_info(index_tup[{i}])' for i in
        range(len(index_tup))] + [f'array_to_info(columns_tup[{i}])' for i in
        range(len(columns_tup))] + [f'array_to_info(values_tup[{i}])' for i in
        range(len(values_tup))])
    trlpj__orgjg += f'        info_list = [{sscrr__vrnb}]\n'
    trlpj__orgjg += '        cpp_table = arr_info_list_to_table(info_list)\n'
    trlpj__orgjg += f"""        out_cpp_table = shuffle_table(cpp_table, {len(index_tup)}, parallel, 0)
"""
    mbf__ggjmg = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i}), index_tup[{i}])'
         for i in range(len(index_tup))])
    xoc__yaai = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i + len(index_tup)}), columns_tup[{i}])'
         for i in range(len(columns_tup))])
    obwin__zuew = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i + len(index_tup) + len(columns_tup)}), values_tup[{i}])'
         for i in range(len(values_tup))])
    trlpj__orgjg += f'        index_tup = ({mbf__ggjmg},)\n'
    trlpj__orgjg += f'        columns_tup = ({xoc__yaai},)\n'
    trlpj__orgjg += f'        values_tup = ({obwin__zuew},)\n'
    trlpj__orgjg += '        delete_table(cpp_table)\n'
    trlpj__orgjg += '        delete_table(out_cpp_table)\n'
    trlpj__orgjg += '    columns_arr = columns_tup[0]\n'
    if humlv__eqor:
        trlpj__orgjg += '    values_arrs = [arr for arr in values_tup]\n'
    trlpj__orgjg += """    unique_index_arr_tup, row_vector = bodo.libs.array_ops.array_unique_vector_map(
"""
    trlpj__orgjg += '        index_tup\n'
    trlpj__orgjg += '    )\n'
    trlpj__orgjg += '    n_rows = len(unique_index_arr_tup[0])\n'
    trlpj__orgjg += '    num_values_arrays = len(values_tup)\n'
    trlpj__orgjg += '    n_unique_pivots = len(pivot_values)\n'
    if humlv__eqor:
        trlpj__orgjg += '    n_cols = num_values_arrays * n_unique_pivots\n'
    else:
        trlpj__orgjg += '    n_cols = n_unique_pivots\n'
    trlpj__orgjg += '    col_map = {}\n'
    trlpj__orgjg += '    for i in range(n_unique_pivots):\n'
    trlpj__orgjg += (
        '        if bodo.libs.array_kernels.isna(pivot_values, i):\n')
    trlpj__orgjg += '            raise ValueError(\n'
    trlpj__orgjg += """                "DataFrame.pivot(): NA values in 'columns' array not supported\"
"""
    trlpj__orgjg += '            )\n'
    trlpj__orgjg += '        col_map[pivot_values[i]] = i\n'
    drgz__ixa = False
    for i, apymp__tsh in enumerate(euqya__tnw):
        if is_str_arr_type(apymp__tsh):
            drgz__ixa = True
            trlpj__orgjg += f"""    len_arrs_{i} = [np.zeros(n_rows, np.int64) for _ in range(n_cols)]
"""
            trlpj__orgjg += (
                f'    total_lens_{i} = np.zeros(n_cols, np.int64)\n')
    if drgz__ixa:
        if xdh__mggmc:
            trlpj__orgjg += '    nbytes = (n_rows + 7) >> 3\n'
            trlpj__orgjg += """    seen_bitmaps = [np.zeros(nbytes, np.int8) for _ in range(n_unique_pivots)]
"""
        trlpj__orgjg += '    for i in range(len(columns_arr)):\n'
        trlpj__orgjg += '        col_name = columns_arr[i]\n'
        trlpj__orgjg += '        pivot_idx = col_map[col_name]\n'
        trlpj__orgjg += '        row_idx = row_vector[i]\n'
        if xdh__mggmc:
            trlpj__orgjg += '        seen_bitmap = seen_bitmaps[pivot_idx]\n'
            trlpj__orgjg += """        if bodo.libs.int_arr_ext.get_bit_bitmap_arr(seen_bitmap, row_idx):
"""
            trlpj__orgjg += """            raise ValueError("DataFrame.pivot(): 'index' contains duplicate entries for the same output column")
"""
            trlpj__orgjg += '        else:\n'
            trlpj__orgjg += """            bodo.libs.int_arr_ext.set_bit_to_arr(seen_bitmap, row_idx, 1)
"""
        if humlv__eqor:
            trlpj__orgjg += '        for j in range(num_values_arrays):\n'
            trlpj__orgjg += (
                '            col_idx = (j * len(pivot_values)) + pivot_idx\n')
            trlpj__orgjg += '            len_arr = len_arrs_0[col_idx]\n'
            trlpj__orgjg += '            values_arr = values_arrs[j]\n'
            trlpj__orgjg += (
                '            if not bodo.libs.array_kernels.isna(values_arr, i):\n'
                )
            trlpj__orgjg += (
                '                len_arr[row_idx] = len(values_arr[i])\n')
            trlpj__orgjg += (
                '                total_lens_0[col_idx] += len(values_arr[i])\n'
                )
        else:
            for i, apymp__tsh in enumerate(euqya__tnw):
                if is_str_arr_type(apymp__tsh):
                    trlpj__orgjg += f"""        if not bodo.libs.array_kernels.isna(values_tup[{i}], i):
"""
                    trlpj__orgjg += f"""            len_arrs_{i}[pivot_idx][row_idx] = len(values_tup[{i}][i])
"""
                    trlpj__orgjg += f"""            total_lens_{i}[pivot_idx] += len(values_tup[{i}][i])
"""
    for i, apymp__tsh in enumerate(euqya__tnw):
        if is_str_arr_type(apymp__tsh):
            trlpj__orgjg += f'    data_arrs_{i} = [\n'
            trlpj__orgjg += (
                '        bodo.libs.str_arr_ext.gen_na_str_array_lens(\n')
            trlpj__orgjg += (
                f'            n_rows, total_lens_{i}[i], len_arrs_{i}[i]\n')
            trlpj__orgjg += '        )\n'
            trlpj__orgjg += '        for i in range(n_cols)\n'
            trlpj__orgjg += '    ]\n'
        else:
            trlpj__orgjg += f'    data_arrs_{i} = [\n'
            trlpj__orgjg += f"""        bodo.libs.array_kernels.gen_na_array(n_rows, data_arr_typ_{i})
"""
            trlpj__orgjg += '        for _ in range(n_cols)\n'
            trlpj__orgjg += '    ]\n'
    if not drgz__ixa and xdh__mggmc:
        trlpj__orgjg += '    nbytes = (n_rows + 7) >> 3\n'
        trlpj__orgjg += """    seen_bitmaps = [np.zeros(nbytes, np.int8) for _ in range(n_unique_pivots)]
"""
    trlpj__orgjg += '    for i in range(len(columns_arr)):\n'
    trlpj__orgjg += '        col_name = columns_arr[i]\n'
    trlpj__orgjg += '        pivot_idx = col_map[col_name]\n'
    trlpj__orgjg += '        row_idx = row_vector[i]\n'
    if not drgz__ixa and xdh__mggmc:
        trlpj__orgjg += '        seen_bitmap = seen_bitmaps[pivot_idx]\n'
        trlpj__orgjg += """        if bodo.libs.int_arr_ext.get_bit_bitmap_arr(seen_bitmap, row_idx):
"""
        trlpj__orgjg += """            raise ValueError("DataFrame.pivot(): 'index' contains duplicate entries for the same output column")
"""
        trlpj__orgjg += '        else:\n'
        trlpj__orgjg += """            bodo.libs.int_arr_ext.set_bit_to_arr(seen_bitmap, row_idx, 1)
"""
    if humlv__eqor:
        trlpj__orgjg += '        for j in range(num_values_arrays):\n'
        trlpj__orgjg += (
            '            col_idx = (j * len(pivot_values)) + pivot_idx\n')
        trlpj__orgjg += '            col_arr = data_arrs_0[col_idx]\n'
        trlpj__orgjg += '            values_arr = values_arrs[j]\n'
        trlpj__orgjg += (
            '            if bodo.libs.array_kernels.isna(values_arr, i):\n')
        trlpj__orgjg += (
            '                bodo.libs.array_kernels.setna(col_arr, row_idx)\n'
            )
        trlpj__orgjg += '            else:\n'
        trlpj__orgjg += '                col_arr[row_idx] = values_arr[i]\n'
    else:
        for i, apymp__tsh in enumerate(euqya__tnw):
            trlpj__orgjg += f'        col_arr_{i} = data_arrs_{i}[pivot_idx]\n'
            trlpj__orgjg += (
                f'        if bodo.libs.array_kernels.isna(values_tup[{i}], i):\n'
                )
            trlpj__orgjg += (
                f'            bodo.libs.array_kernels.setna(col_arr_{i}, row_idx)\n'
                )
            trlpj__orgjg += f'        else:\n'
            trlpj__orgjg += (
                f'            col_arr_{i}[row_idx] = values_tup[{i}][i]\n')
    if len(index_tup) == 1:
        trlpj__orgjg += """    index = bodo.utils.conversion.index_from_array(unique_index_arr_tup[0], index_names[0])
"""
    else:
        trlpj__orgjg += """    index = bodo.hiframes.pd_multi_index_ext.init_multi_index(unique_index_arr_tup, index_names, None)
"""
    if gscy__tglfk:
        trlpj__orgjg += '    num_rows = len(value_names) * len(pivot_values)\n'
        if is_str_arr_type(value_names):
            trlpj__orgjg += '    total_chars = 0\n'
            trlpj__orgjg += '    for i in range(len(value_names)):\n'
            trlpj__orgjg += '        total_chars += len(value_names[i])\n'
            trlpj__orgjg += """    new_value_names = bodo.libs.str_arr_ext.pre_alloc_string_array(num_rows, total_chars * len(pivot_values))
"""
        else:
            trlpj__orgjg += """    new_value_names = bodo.utils.utils.alloc_type(num_rows, value_names, (-1,))
"""
        if is_str_arr_type(pivot_values):
            trlpj__orgjg += '    total_chars = 0\n'
            trlpj__orgjg += '    for i in range(len(pivot_values)):\n'
            trlpj__orgjg += '        total_chars += len(pivot_values[i])\n'
            trlpj__orgjg += """    new_pivot_values = bodo.libs.str_arr_ext.pre_alloc_string_array(num_rows, total_chars * len(value_names))
"""
        else:
            trlpj__orgjg += """    new_pivot_values = bodo.utils.utils.alloc_type(num_rows, pivot_values, (-1,))
"""
        trlpj__orgjg += '    for i in range(len(value_names)):\n'
        trlpj__orgjg += '        for j in range(len(pivot_values)):\n'
        trlpj__orgjg += """            new_value_names[(i * len(pivot_values)) + j] = value_names[i]
"""
        trlpj__orgjg += """            new_pivot_values[(i * len(pivot_values)) + j] = pivot_values[j]
"""
        trlpj__orgjg += """    column_index = bodo.hiframes.pd_multi_index_ext.init_multi_index((new_value_names, new_pivot_values), (None, columns_name), None)
"""
    else:
        trlpj__orgjg += """    column_index =  bodo.utils.conversion.index_from_array(pivot_values, columns_name)
"""
    wajhd__hibj = ', '.join(f'data_arrs_{i}' for i in range(len(euqya__tnw)))
    trlpj__orgjg += f"""    table = bodo.hiframes.table.init_runtime_table_from_lists(({wajhd__hibj},), n_rows)
"""
    trlpj__orgjg += (
        '    return bodo.hiframes.pd_dataframe_ext.init_runtime_cols_dataframe(\n'
        )
    trlpj__orgjg += '        (table,), index, column_index\n'
    trlpj__orgjg += '    )\n'
    ozh__jhzmb = {}
    uozrf__pnicx = {f'data_arr_typ_{i}': apymp__tsh for i, apymp__tsh in
        enumerate(euqya__tnw)}
    pwzc__lcl = {'bodo': bodo, 'np': np, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'shuffle_table':
        shuffle_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'info_from_table': info_from_table, **uozrf__pnicx}
    exec(trlpj__orgjg, pwzc__lcl, ozh__jhzmb)
    impl = ozh__jhzmb['impl']
    return impl


def gen_pandas_parquet_metadata(column_names, data_types, index,
    write_non_range_index_to_metadata, write_rangeindex_to_metadata,
    partition_cols=None, is_runtime_columns=False):
    gpg__eklp = {}
    gpg__eklp['columns'] = []
    if partition_cols is None:
        partition_cols = []
    for col_name, wab__vswxc in zip(column_names, data_types):
        if col_name in partition_cols:
            continue
        uzd__fdwz = None
        if isinstance(wab__vswxc, bodo.DatetimeArrayType):
            ecsts__jnsa = 'datetimetz'
            udt__hcoi = 'datetime64[ns]'
            if isinstance(wab__vswxc.tz, int):
                ksfom__kdscg = (bodo.libs.pd_datetime_arr_ext.
                    nanoseconds_to_offset(wab__vswxc.tz))
            else:
                ksfom__kdscg = pd.DatetimeTZDtype(tz=wab__vswxc.tz).tz
            uzd__fdwz = {'timezone': pa.lib.tzinfo_to_string(ksfom__kdscg)}
        elif isinstance(wab__vswxc, types.Array
            ) or wab__vswxc == boolean_array:
            ecsts__jnsa = udt__hcoi = wab__vswxc.dtype.name
            if udt__hcoi.startswith('datetime'):
                ecsts__jnsa = 'datetime'
        elif is_str_arr_type(wab__vswxc):
            ecsts__jnsa = 'unicode'
            udt__hcoi = 'object'
        elif wab__vswxc == binary_array_type:
            ecsts__jnsa = 'bytes'
            udt__hcoi = 'object'
        elif isinstance(wab__vswxc, DecimalArrayType):
            ecsts__jnsa = udt__hcoi = 'object'
        elif isinstance(wab__vswxc, IntegerArrayType):
            cjb__pjxlt = wab__vswxc.dtype.name
            if cjb__pjxlt.startswith('int'):
                ecsts__jnsa = 'Int' + cjb__pjxlt[3:]
            elif cjb__pjxlt.startswith('uint'):
                ecsts__jnsa = 'UInt' + cjb__pjxlt[4:]
            else:
                if is_runtime_columns:
                    col_name = 'Runtime determined column of type'
                raise BodoError(
                    'to_parquet(): unknown dtype in nullable Integer column {} {}'
                    .format(col_name, wab__vswxc))
            udt__hcoi = wab__vswxc.dtype.name
        elif wab__vswxc == datetime_date_array_type:
            ecsts__jnsa = 'datetime'
            udt__hcoi = 'object'
        elif isinstance(wab__vswxc, (StructArrayType, ArrayItemArrayType)):
            ecsts__jnsa = 'object'
            udt__hcoi = 'object'
        else:
            if is_runtime_columns:
                col_name = 'Runtime determined column of type'
            raise BodoError(
                'to_parquet(): unsupported column type for metadata generation : {} {}'
                .format(col_name, wab__vswxc))
        hbkwu__ggqhd = {'name': col_name, 'field_name': col_name,
            'pandas_type': ecsts__jnsa, 'numpy_type': udt__hcoi, 'metadata':
            uzd__fdwz}
        gpg__eklp['columns'].append(hbkwu__ggqhd)
    if write_non_range_index_to_metadata:
        if isinstance(index, MultiIndexType):
            raise BodoError('to_parquet: MultiIndex not supported yet')
        if 'none' in index.name:
            iwn__ztxr = '__index_level_0__'
            wmgym__maq = None
        else:
            iwn__ztxr = '%s'
            wmgym__maq = '%s'
        gpg__eklp['index_columns'] = [iwn__ztxr]
        gpg__eklp['columns'].append({'name': wmgym__maq, 'field_name':
            iwn__ztxr, 'pandas_type': index.pandas_type_name, 'numpy_type':
            index.numpy_type_name, 'metadata': None})
    elif write_rangeindex_to_metadata:
        gpg__eklp['index_columns'] = [{'kind': 'range', 'name': '%s',
            'start': '%d', 'stop': '%d', 'step': '%d'}]
    else:
        gpg__eklp['index_columns'] = []
    gpg__eklp['pandas_version'] = pd.__version__
    return gpg__eklp


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
        oohxo__pdwsc = []
        for nbrug__sqx in partition_cols:
            try:
                idx = df.columns.index(nbrug__sqx)
            except ValueError as vexy__qmjcz:
                raise BodoError(
                    f'Partition column {nbrug__sqx} is not in dataframe')
            oohxo__pdwsc.append(idx)
    else:
        partition_cols = None
    if not is_overload_none(index) and not is_overload_constant_bool(index):
        raise BodoError('to_parquet(): index must be a constant bool or None')
    from bodo.io.parquet_pio import parquet_write_table_cpp, parquet_write_table_partitioned_cpp
    mycqy__usqe = isinstance(df.index, bodo.hiframes.pd_index_ext.
        RangeIndexType)
    wbuse__mihi = df.index is not None and (is_overload_true(_is_parallel) or
        not is_overload_true(_is_parallel) and not mycqy__usqe)
    write_non_range_index_to_metadata = is_overload_true(index
        ) or is_overload_none(index) and (not mycqy__usqe or
        is_overload_true(_is_parallel))
    write_rangeindex_to_metadata = is_overload_none(index
        ) and mycqy__usqe and not is_overload_true(_is_parallel)
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
        plfgl__cansm = df.runtime_data_types
        fsta__mkqh = len(plfgl__cansm)
        uzd__fdwz = gen_pandas_parquet_metadata([''] * fsta__mkqh,
            plfgl__cansm, df.index, write_non_range_index_to_metadata,
            write_rangeindex_to_metadata, partition_cols=partition_cols,
            is_runtime_columns=True)
        own__ljcnl = uzd__fdwz['columns'][:fsta__mkqh]
        uzd__fdwz['columns'] = uzd__fdwz['columns'][fsta__mkqh:]
        own__ljcnl = [json.dumps(oach__ygt).replace('""', '{0}') for
            oach__ygt in own__ljcnl]
        lxd__ryk = json.dumps(uzd__fdwz)
        nrfb__qyjfh = '"columns": ['
        avxb__jatke = lxd__ryk.find(nrfb__qyjfh)
        if avxb__jatke == -1:
            raise BodoError(
                'DataFrame.to_parquet(): Unexpected metadata string for runtime columns.  Please return the DataFrame to regular Python to update typing information.'
                )
        ruob__hcp = avxb__jatke + len(nrfb__qyjfh)
        nsxhe__atiz = lxd__ryk[:ruob__hcp]
        lxd__ryk = lxd__ryk[ruob__hcp:]
        ics__bapbw = len(uzd__fdwz['columns'])
    else:
        lxd__ryk = json.dumps(gen_pandas_parquet_metadata(df.columns, df.
            data, df.index, write_non_range_index_to_metadata,
            write_rangeindex_to_metadata, partition_cols=partition_cols,
            is_runtime_columns=False))
    if not is_overload_true(_is_parallel) and mycqy__usqe:
        lxd__ryk = lxd__ryk.replace('"%d"', '%d')
        if df.index.name == 'RangeIndexType(none)':
            lxd__ryk = lxd__ryk.replace('"%s"', '%s')
    if not df.is_table_format:
        geyhd__bxdy = ', '.join(
            'array_to_info(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}))'
            .format(i) for i in range(len(df.columns)))
    trlpj__orgjg = """def df_to_parquet(df, fname, engine='auto', compression='snappy', index=None, partition_cols=None, storage_options=None, _is_parallel=False):
"""
    if df.is_table_format:
        trlpj__orgjg += '    py_table = get_dataframe_table(df)\n'
        trlpj__orgjg += (
            '    table = py_table_to_cpp_table(py_table, py_table_typ)\n')
    else:
        trlpj__orgjg += '    info_list = [{}]\n'.format(geyhd__bxdy)
        trlpj__orgjg += '    table = arr_info_list_to_table(info_list)\n'
    if df.has_runtime_cols:
        trlpj__orgjg += '    columns_index = get_dataframe_column_names(df)\n'
        trlpj__orgjg += '    names_arr = index_to_array(columns_index)\n'
        trlpj__orgjg += '    col_names = array_to_info(names_arr)\n'
    else:
        trlpj__orgjg += '    col_names = array_to_info(col_names_arr)\n'
    if is_overload_true(index) or is_overload_none(index) and wbuse__mihi:
        trlpj__orgjg += """    index_col = array_to_info(index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)))
"""
        yunxj__ccp = True
    else:
        trlpj__orgjg += '    index_col = array_to_info(np.empty(0))\n'
        yunxj__ccp = False
    if df.has_runtime_cols:
        trlpj__orgjg += '    columns_lst = []\n'
        trlpj__orgjg += '    num_cols = 0\n'
        for i in range(len(df.runtime_data_types)):
            trlpj__orgjg += f'    for _ in range(len(py_table.block_{i})):\n'
            trlpj__orgjg += f"""        columns_lst.append({own__ljcnl[i]!r}.replace('{{0}}', '"' + names_arr[num_cols] + '"'))
"""
            trlpj__orgjg += '        num_cols += 1\n'
        if ics__bapbw:
            trlpj__orgjg += "    columns_lst.append('')\n"
        trlpj__orgjg += '    columns_str = ", ".join(columns_lst)\n'
        trlpj__orgjg += ('    metadata = """' + nsxhe__atiz +
            '""" + columns_str + """' + lxd__ryk + '"""\n')
    else:
        trlpj__orgjg += '    metadata = """' + lxd__ryk + '"""\n'
    trlpj__orgjg += '    if compression is None:\n'
    trlpj__orgjg += "        compression = 'none'\n"
    trlpj__orgjg += '    if df.index.name is not None:\n'
    trlpj__orgjg += '        name_ptr = df.index.name\n'
    trlpj__orgjg += '    else:\n'
    trlpj__orgjg += "        name_ptr = 'null'\n"
    trlpj__orgjg += f"""    bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel=_is_parallel)
"""
    wmfak__zbd = None
    if partition_cols:
        wmfak__zbd = pd.array([col_name for col_name in df.columns if 
            col_name not in partition_cols])
        pkzal__bsyp = ', '.join(
            f'array_to_info(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).dtype.categories.values)'
             for i in range(len(df.columns)) if isinstance(df.data[i],
            CategoricalArrayType) and i in oohxo__pdwsc)
        if pkzal__bsyp:
            trlpj__orgjg += '    cat_info_list = [{}]\n'.format(pkzal__bsyp)
            trlpj__orgjg += (
                '    cat_table = arr_info_list_to_table(cat_info_list)\n')
        else:
            trlpj__orgjg += '    cat_table = table\n'
        trlpj__orgjg += (
            '    col_names_no_partitions = array_to_info(col_names_no_parts_arr)\n'
            )
        trlpj__orgjg += (
            f'    part_cols_idxs = np.array({oohxo__pdwsc}, dtype=np.int32)\n')
        trlpj__orgjg += (
            '    parquet_write_table_partitioned_cpp(unicode_to_utf8(fname),\n'
            )
        trlpj__orgjg += """                            table, col_names, col_names_no_partitions, cat_table,
"""
        trlpj__orgjg += (
            '                            part_cols_idxs.ctypes, len(part_cols_idxs),\n'
            )
        trlpj__orgjg += (
            '                            unicode_to_utf8(compression),\n')
        trlpj__orgjg += '                            _is_parallel,\n'
        trlpj__orgjg += (
            '                            unicode_to_utf8(bucket_region))\n')
        trlpj__orgjg += '    delete_table_decref_arrays(table)\n'
        trlpj__orgjg += '    delete_info_decref_array(index_col)\n'
        trlpj__orgjg += (
            '    delete_info_decref_array(col_names_no_partitions)\n')
        trlpj__orgjg += '    delete_info_decref_array(col_names)\n'
        if pkzal__bsyp:
            trlpj__orgjg += '    delete_table_decref_arrays(cat_table)\n'
    elif write_rangeindex_to_metadata:
        trlpj__orgjg += '    parquet_write_table_cpp(unicode_to_utf8(fname),\n'
        trlpj__orgjg += (
            '                            table, col_names, index_col,\n')
        trlpj__orgjg += '                            ' + str(yunxj__ccp
            ) + ',\n'
        trlpj__orgjg += (
            '                            unicode_to_utf8(metadata),\n')
        trlpj__orgjg += (
            '                            unicode_to_utf8(compression),\n')
        trlpj__orgjg += (
            '                            _is_parallel, 1, df.index.start,\n')
        trlpj__orgjg += (
            '                            df.index.stop, df.index.step,\n')
        trlpj__orgjg += (
            '                            unicode_to_utf8(name_ptr),\n')
        trlpj__orgjg += (
            '                            unicode_to_utf8(bucket_region))\n')
        trlpj__orgjg += '    delete_table_decref_arrays(table)\n'
        trlpj__orgjg += '    delete_info_decref_array(index_col)\n'
        trlpj__orgjg += '    delete_info_decref_array(col_names)\n'
    else:
        trlpj__orgjg += '    parquet_write_table_cpp(unicode_to_utf8(fname),\n'
        trlpj__orgjg += (
            '                            table, col_names, index_col,\n')
        trlpj__orgjg += '                            ' + str(yunxj__ccp
            ) + ',\n'
        trlpj__orgjg += (
            '                            unicode_to_utf8(metadata),\n')
        trlpj__orgjg += (
            '                            unicode_to_utf8(compression),\n')
        trlpj__orgjg += (
            '                            _is_parallel, 0, 0, 0, 0,\n')
        trlpj__orgjg += (
            '                            unicode_to_utf8(name_ptr),\n')
        trlpj__orgjg += (
            '                            unicode_to_utf8(bucket_region))\n')
        trlpj__orgjg += '    delete_table_decref_arrays(table)\n'
        trlpj__orgjg += '    delete_info_decref_array(index_col)\n'
        trlpj__orgjg += '    delete_info_decref_array(col_names)\n'
    ozh__jhzmb = {}
    if df.has_runtime_cols:
        letrc__qwzz = None
    else:
        for jkd__khbk in df.columns:
            if not isinstance(jkd__khbk, str):
                raise BodoError(
                    'DataFrame.to_parquet(): parquet must have string column names'
                    )
        letrc__qwzz = pd.array(df.columns)
    exec(trlpj__orgjg, {'np': np, 'bodo': bodo, 'unicode_to_utf8':
        unicode_to_utf8, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table,
        'str_arr_from_sequence': str_arr_from_sequence,
        'parquet_write_table_cpp': parquet_write_table_cpp,
        'parquet_write_table_partitioned_cpp':
        parquet_write_table_partitioned_cpp, 'index_to_array':
        index_to_array, 'delete_info_decref_array':
        delete_info_decref_array, 'delete_table_decref_arrays':
        delete_table_decref_arrays, 'col_names_arr': letrc__qwzz,
        'py_table_to_cpp_table': py_table_to_cpp_table, 'py_table_typ': df.
        table_type, 'get_dataframe_table': get_dataframe_table,
        'col_names_no_parts_arr': wmfak__zbd, 'get_dataframe_column_names':
        get_dataframe_column_names, 'fix_arr_dtype': fix_arr_dtype,
        'decode_if_dict_array': decode_if_dict_array,
        'decode_if_dict_table': decode_if_dict_table}, ozh__jhzmb)
    sqnbm__sanxe = ozh__jhzmb['df_to_parquet']
    return sqnbm__sanxe


def to_sql_exception_guard(df, name, con, schema=None, if_exists='fail',
    index=True, index_label=None, chunksize=None, dtype=None, method=None,
    _is_table_create=False, _is_parallel=False):
    pmho__huee = 'all_ok'
    oyv__jxy = urlparse(con).scheme
    if _is_parallel and bodo.get_rank() == 0:
        zxo__kod = 100
        if chunksize is None:
            ezn__ckc = zxo__kod
        else:
            ezn__ckc = min(chunksize, zxo__kod)
        if _is_table_create:
            df = df.iloc[:ezn__ckc, :]
        else:
            df = df.iloc[ezn__ckc:, :]
            if len(df) == 0:
                return pmho__huee
    if oyv__jxy == 'snowflake':
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
            df.columns = [(plvey__qmn.upper() if plvey__qmn.islower() else
                plvey__qmn) for plvey__qmn in df.columns]
        except ImportError as vexy__qmjcz:
            pmho__huee = (
                "Snowflake Python connector packages not found. Using 'to_sql' with Snowflake requires both snowflake-sqlalchemy and snowflake-connector-python. These can be installed by calling 'conda install -c conda-forge snowflake-sqlalchemy snowflake-connector-python' or 'pip install snowflake-sqlalchemy snowflake-connector-python'."
                )
            return pmho__huee
    try:
        df.to_sql(name, con, schema, if_exists, index, index_label,
            chunksize, dtype, method)
    except Exception as ngs__urc:
        pmho__huee = ngs__urc.args[0]
    return pmho__huee


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
        scut__jsi = bodo.libs.distributed_api.get_rank()
        pmho__huee = 'unset'
        if scut__jsi != 0:
            pmho__huee = bcast_scalar(pmho__huee)
        elif scut__jsi == 0:
            pmho__huee = to_sql_exception_guard_encaps(df, name, con,
                schema, if_exists, index, index_label, chunksize, dtype,
                method, True, _is_parallel)
            pmho__huee = bcast_scalar(pmho__huee)
        if_exists = 'append'
        if _is_parallel and pmho__huee == 'all_ok':
            pmho__huee = to_sql_exception_guard_encaps(df, name, con,
                schema, if_exists, index, index_label, chunksize, dtype,
                method, False, _is_parallel)
        if pmho__huee != 'all_ok':
            print('err_msg=', pmho__huee)
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
        pmb__alfgd = get_overload_const_str(path_or_buf)
        if pmb__alfgd.endswith(('.gz', '.bz2', '.zip', '.xz')):
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
        qupgr__zhmbh = bodo.io.fs_io.get_s3_bucket_region_njit(path_or_buf,
            parallel=False)
        if lines and orient == 'records':
            bodo.hiframes.pd_dataframe_ext._json_write(unicode_to_utf8(
                path_or_buf), unicode_to_utf8(D), 0, len(D), False, True,
                unicode_to_utf8(qupgr__zhmbh))
            bodo.utils.utils.check_and_propagate_cpp_exception()
        else:
            bodo.hiframes.pd_dataframe_ext._json_write(unicode_to_utf8(
                path_or_buf), unicode_to_utf8(D), 0, len(D), False, False,
                unicode_to_utf8(qupgr__zhmbh))
            bodo.utils.utils.check_and_propagate_cpp_exception()
    return _impl


@overload(pd.get_dummies, inline='always', no_unliteral=True)
def get_dummies(data, prefix=None, prefix_sep='_', dummy_na=False, columns=
    None, sparse=False, drop_first=False, dtype=None):
    dwsba__uzg = {'prefix': prefix, 'prefix_sep': prefix_sep, 'dummy_na':
        dummy_na, 'columns': columns, 'sparse': sparse, 'drop_first':
        drop_first, 'dtype': dtype}
    ajbxh__rddhh = {'prefix': None, 'prefix_sep': '_', 'dummy_na': False,
        'columns': None, 'sparse': False, 'drop_first': False, 'dtype': None}
    check_unsupported_args('pandas.get_dummies', dwsba__uzg, ajbxh__rddhh,
        package_name='pandas', module_name='General')
    if not categorical_can_construct_dataframe(data):
        raise BodoError(
            'pandas.get_dummies() only support categorical data types with explicitly known categories'
            )
    trlpj__orgjg = """def impl(data, prefix=None, prefix_sep='_', dummy_na=False, columns=None, sparse=False, drop_first=False, dtype=None,):
"""
    if isinstance(data, SeriesType):
        umnoo__inxzp = data.data.dtype.categories
        trlpj__orgjg += (
            '  data_values = bodo.hiframes.pd_series_ext.get_series_data(data)\n'
            )
    else:
        umnoo__inxzp = data.dtype.categories
        trlpj__orgjg += '  data_values = data\n'
    ubymi__eclpt = len(umnoo__inxzp)
    trlpj__orgjg += """  codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(data_values)
"""
    trlpj__orgjg += '  numba.parfors.parfor.init_prange()\n'
    trlpj__orgjg += '  n = len(data_values)\n'
    for i in range(ubymi__eclpt):
        trlpj__orgjg += '  data_arr_{} = np.empty(n, np.uint8)\n'.format(i)
    trlpj__orgjg += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    trlpj__orgjg += '      if bodo.libs.array_kernels.isna(data_values, i):\n'
    for kdg__iwebl in range(ubymi__eclpt):
        trlpj__orgjg += '          data_arr_{}[i] = 0\n'.format(kdg__iwebl)
    trlpj__orgjg += '      else:\n'
    for nyt__gdib in range(ubymi__eclpt):
        trlpj__orgjg += '          data_arr_{0}[i] = codes[i] == {0}\n'.format(
            nyt__gdib)
    geyhd__bxdy = ', '.join(f'data_arr_{i}' for i in range(ubymi__eclpt))
    index = 'bodo.hiframes.pd_index_ext.init_range_index(0, n, 1, None)'
    if isinstance(umnoo__inxzp[0], np.datetime64):
        umnoo__inxzp = tuple(pd.Timestamp(plvey__qmn) for plvey__qmn in
            umnoo__inxzp)
    elif isinstance(umnoo__inxzp[0], np.timedelta64):
        umnoo__inxzp = tuple(pd.Timedelta(plvey__qmn) for plvey__qmn in
            umnoo__inxzp)
    return bodo.hiframes.dataframe_impl._gen_init_df(trlpj__orgjg,
        umnoo__inxzp, geyhd__bxdy, index)


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
    for azhe__hrh in pd_unsupported:
        fname = mod_name + '.' + azhe__hrh.__name__
        overload(azhe__hrh, no_unliteral=True)(create_unsupported_overload(
            fname))


def _install_dataframe_unsupported():
    for kkeg__zixe in dataframe_unsupported_attrs:
        mlik__ostp = 'DataFrame.' + kkeg__zixe
        overload_attribute(DataFrameType, kkeg__zixe)(
            create_unsupported_overload(mlik__ostp))
    for fname in dataframe_unsupported:
        mlik__ostp = 'DataFrame.' + fname + '()'
        overload_method(DataFrameType, fname)(create_unsupported_overload(
            mlik__ostp))


_install_pd_unsupported('pandas', pd_unsupported)
_install_pd_unsupported('pandas.util', pd_util_unsupported)
_install_dataframe_unsupported()
