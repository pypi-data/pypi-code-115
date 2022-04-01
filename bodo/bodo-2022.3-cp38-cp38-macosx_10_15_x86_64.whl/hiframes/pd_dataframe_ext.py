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
            axkr__gxz = f'{len(self.data)} columns of types {set(self.data)}'
            oyxuz__kndw = (
                f"('{self.columns[0]}', '{self.columns[1]}', ..., '{self.columns[-1]}')"
                )
            return (
                f'dataframe({axkr__gxz}, {self.index}, {oyxuz__kndw}, {self.dist}, {self.is_table_format})'
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
            mati__wnwu = (self.index if self.index == other.index else self
                .index.unify(typingctx, other.index))
            data = tuple(ujhf__dkyw.unify(typingctx, jkxfr__bflxd) if 
                ujhf__dkyw != jkxfr__bflxd else ujhf__dkyw for ujhf__dkyw,
                jkxfr__bflxd in zip(self.data, other.data))
            dist = Distribution(min(self.dist.value, other.dist.value))
            if mati__wnwu is not None and None not in data:
                return DataFrameType(data, mati__wnwu, self.columns, dist,
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
        return all(ujhf__dkyw.is_precise() for ujhf__dkyw in self.data
            ) and self.index.is_precise()

    def replace_col_type(self, col_name, new_type):
        if col_name not in self.columns:
            raise ValueError(
                f"DataFrameType.replace_col_type replaced column must be found in the DataFrameType. '{col_name}' not found in DataFrameType with columns {self.columns}"
                )
        tseps__uvfj = self.columns.index(col_name)
        clbpb__twus = tuple(list(self.data[:tseps__uvfj]) + [new_type] +
            list(self.data[tseps__uvfj + 1:]))
        return DataFrameType(clbpb__twus, self.index, self.columns, self.
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
        lrob__ybx = [('data', data_typ), ('index', fe_type.df_type.index),
            ('parent', types.pyobject)]
        if fe_type.df_type.has_runtime_cols:
            lrob__ybx.append(('columns', fe_type.df_type.runtime_colname_typ))
        super(DataFramePayloadModel, self).__init__(dmm, fe_type, lrob__ybx)


@register_model(DataFrameType)
class DataFrameModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = DataFramePayloadType(fe_type)
        lrob__ybx = [('meminfo', types.MemInfoPointer(payload_type)), (
            'parent', types.pyobject)]
        super(DataFrameModel, self).__init__(dmm, fe_type, lrob__ybx)


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
        bqwc__nun = 'n',
        qyyrd__exh = {'n': 5}
        gfbn__rpj, czinn__pmuuh = bodo.utils.typing.fold_typing_args(func_name,
            args, kws, bqwc__nun, qyyrd__exh)
        bta__adffe = czinn__pmuuh[0]
        if not is_overload_int(bta__adffe):
            raise BodoError(f"{func_name}(): 'n' must be an Integer")
        vxr__ivs = df.copy(is_table_format=False)
        return vxr__ivs(*czinn__pmuuh).replace(pysig=gfbn__rpj)

    @bound_function('df.corr')
    def resolve_corr(self, df, args, kws):
        func_name = 'DataFrame.corr'
        check_runtime_cols_unsupported(df, f'{func_name}()')
        dss__pvdbj = (df,) + args
        bqwc__nun = 'df', 'method', 'min_periods'
        qyyrd__exh = {'method': 'pearson', 'min_periods': 1}
        jzu__eoajn = 'method',
        gfbn__rpj, czinn__pmuuh = bodo.utils.typing.fold_typing_args(func_name,
            dss__pvdbj, kws, bqwc__nun, qyyrd__exh, jzu__eoajn)
        nhncn__emuku = czinn__pmuuh[2]
        if not is_overload_int(nhncn__emuku):
            raise BodoError(f"{func_name}(): 'min_periods' must be an Integer")
        ydtgi__nyc = []
        ddx__pwug = []
        for yhx__kwv, jnw__rnz in zip(df.columns, df.data):
            if bodo.utils.typing._is_pandas_numeric_dtype(jnw__rnz.dtype):
                ydtgi__nyc.append(yhx__kwv)
                ddx__pwug.append(types.Array(types.float64, 1, 'A'))
        if len(ydtgi__nyc) == 0:
            raise_bodo_error('DataFrame.corr(): requires non-empty dataframe')
        ddx__pwug = tuple(ddx__pwug)
        ydtgi__nyc = tuple(ydtgi__nyc)
        index_typ = bodo.utils.typing.type_col_to_index(ydtgi__nyc)
        vxr__ivs = DataFrameType(ddx__pwug, index_typ, ydtgi__nyc)
        return vxr__ivs(*czinn__pmuuh).replace(pysig=gfbn__rpj)

    @bound_function('df.pipe', no_unliteral=True)
    def resolve_pipe(self, df, args, kws):
        check_runtime_cols_unsupported(df, 'DataFrame.pipe()')
        return bodo.hiframes.pd_groupby_ext.resolve_obj_pipe(self, df, args,
            kws, 'DataFrame')

    @bound_function('df.apply', no_unliteral=True)
    def resolve_apply(self, df, args, kws):
        check_runtime_cols_unsupported(df, 'DataFrame.apply()')
        kws = dict(kws)
        jyksr__zdab = args[0] if len(args) > 0 else kws.pop('func', None)
        axis = args[1] if len(args) > 1 else kws.pop('axis', types.literal(0))
        wujnk__bizg = args[2] if len(args) > 2 else kws.pop('raw', types.
            literal(False))
        pzt__jmdm = args[3] if len(args) > 3 else kws.pop('result_type',
            types.none)
        hpf__vod = args[4] if len(args) > 4 else kws.pop('args', types.
            Tuple([]))
        yomkl__uos = dict(raw=wujnk__bizg, result_type=pzt__jmdm)
        ajuu__mphl = dict(raw=False, result_type=None)
        check_unsupported_args('Dataframe.apply', yomkl__uos, ajuu__mphl,
            package_name='pandas', module_name='DataFrame')
        exgj__wga = True
        if types.unliteral(jyksr__zdab) == types.unicode_type:
            if not is_overload_constant_str(jyksr__zdab):
                raise BodoError(
                    f'DataFrame.apply(): string argument (for builtins) must be a compile time constant'
                    )
            exgj__wga = False
        if not is_overload_constant_int(axis):
            raise BodoError(
                'Dataframe.apply(): axis argument must be a compile time constant.'
                )
        yup__qlixf = get_overload_const_int(axis)
        if exgj__wga and yup__qlixf != 1:
            raise BodoError(
                'Dataframe.apply(): only axis=1 supported for user-defined functions'
                )
        elif yup__qlixf not in (0, 1):
            raise BodoError('Dataframe.apply(): axis must be either 0 or 1')
        epm__xha = []
        for arr_typ in df.data:
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(arr_typ,
                'DataFrame.apply()')
            xyo__yyycy = SeriesType(arr_typ.dtype, arr_typ, df.index,
                string_type)
            pwqy__zlqx = self.context.resolve_function_type(operator.
                getitem, (SeriesIlocType(xyo__yyycy), types.int64), {}
                ).return_type
            epm__xha.append(pwqy__zlqx)
        wzbcw__wik = types.none
        bkrpn__cwa = HeterogeneousIndexType(types.BaseTuple.from_types(
            tuple(types.literal(yhx__kwv) for yhx__kwv in df.columns)), None)
        bgipj__blq = types.BaseTuple.from_types(epm__xha)
        opvl__mdyr = df.index.dtype
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df.index,
            'DataFrame.apply()')
        if opvl__mdyr == types.NPDatetime('ns'):
            opvl__mdyr = bodo.pd_timestamp_type
        if opvl__mdyr == types.NPTimedelta('ns'):
            opvl__mdyr = bodo.pd_timedelta_type
        if is_heterogeneous_tuple_type(bgipj__blq):
            ifghb__lft = HeterogeneousSeriesType(bgipj__blq, bkrpn__cwa,
                opvl__mdyr)
        else:
            ifghb__lft = SeriesType(bgipj__blq.dtype, bgipj__blq,
                bkrpn__cwa, opvl__mdyr)
        ser__kbny = ifghb__lft,
        if hpf__vod is not None:
            ser__kbny += tuple(hpf__vod.types)
        try:
            if not exgj__wga:
                ujecw__yczv = bodo.utils.transform.get_udf_str_return_type(df,
                    get_overload_const_str(jyksr__zdab), self.context,
                    'DataFrame.apply', axis if yup__qlixf == 1 else None)
            else:
                ujecw__yczv = get_const_func_output_type(jyksr__zdab,
                    ser__kbny, kws, self.context, numba.core.registry.
                    cpu_target.target_context)
        except Exception as tnxo__oowg:
            raise_bodo_error(get_udf_error_msg('DataFrame.apply()', tnxo__oowg)
                )
        if exgj__wga:
            if not (is_overload_constant_int(axis) and 
                get_overload_const_int(axis) == 1):
                raise BodoError(
                    'Dataframe.apply(): only user-defined functions with axis=1 supported'
                    )
            if isinstance(ujecw__yczv, (SeriesType, HeterogeneousSeriesType)
                ) and ujecw__yczv.const_info is None:
                raise BodoError(
                    'Invalid Series output in UDF (Series with constant length and constant Index value expected)'
                    )
            if isinstance(ujecw__yczv, HeterogeneousSeriesType):
                wxf__rfh, kcpp__tztka = ujecw__yczv.const_info
                kkp__kkzfs = tuple(dtype_to_array_type(rgqji__lceb) for
                    rgqji__lceb in ujecw__yczv.data.types)
                bldjo__sxmg = DataFrameType(kkp__kkzfs, df.index, kcpp__tztka)
            elif isinstance(ujecw__yczv, SeriesType):
                xou__mhnu, kcpp__tztka = ujecw__yczv.const_info
                kkp__kkzfs = tuple(dtype_to_array_type(ujecw__yczv.dtype) for
                    wxf__rfh in range(xou__mhnu))
                bldjo__sxmg = DataFrameType(kkp__kkzfs, df.index, kcpp__tztka)
            else:
                poc__wwk = get_udf_out_arr_type(ujecw__yczv)
                bldjo__sxmg = SeriesType(poc__wwk.dtype, poc__wwk, df.index,
                    None)
        else:
            bldjo__sxmg = ujecw__yczv
        irffa__szus = ', '.join("{} = ''".format(ujhf__dkyw) for ujhf__dkyw in
            kws.keys())
        iqkj__cxo = f"""def apply_stub(func, axis=0, raw=False, result_type=None, args=(), {irffa__szus}):
"""
        iqkj__cxo += '    pass\n'
        leo__uscw = {}
        exec(iqkj__cxo, {}, leo__uscw)
        hhyws__vtp = leo__uscw['apply_stub']
        gfbn__rpj = numba.core.utils.pysignature(hhyws__vtp)
        nsi__idii = (jyksr__zdab, axis, wujnk__bizg, pzt__jmdm, hpf__vod
            ) + tuple(kws.values())
        return signature(bldjo__sxmg, *nsi__idii).replace(pysig=gfbn__rpj)

    @bound_function('df.plot', no_unliteral=True)
    def resolve_plot(self, df, args, kws):
        func_name = 'DataFrame.plot'
        check_runtime_cols_unsupported(df, f'{func_name}()')
        bqwc__nun = ('x', 'y', 'kind', 'figsize', 'ax', 'subplots',
            'sharex', 'sharey', 'layout', 'use_index', 'title', 'grid',
            'legend', 'style', 'logx', 'logy', 'loglog', 'xticks', 'yticks',
            'xlim', 'ylim', 'rot', 'fontsize', 'colormap', 'table', 'yerr',
            'xerr', 'secondary_y', 'sort_columns', 'xlabel', 'ylabel',
            'position', 'stacked', 'mark_right', 'include_bool', 'backend')
        qyyrd__exh = {'x': None, 'y': None, 'kind': 'line', 'figsize': None,
            'ax': None, 'subplots': False, 'sharex': None, 'sharey': False,
            'layout': None, 'use_index': True, 'title': None, 'grid': None,
            'legend': True, 'style': None, 'logx': False, 'logy': False,
            'loglog': False, 'xticks': None, 'yticks': None, 'xlim': None,
            'ylim': None, 'rot': None, 'fontsize': None, 'colormap': None,
            'table': False, 'yerr': None, 'xerr': None, 'secondary_y': 
            False, 'sort_columns': False, 'xlabel': None, 'ylabel': None,
            'position': 0.5, 'stacked': False, 'mark_right': True,
            'include_bool': False, 'backend': None}
        jzu__eoajn = ('subplots', 'sharex', 'sharey', 'layout', 'use_index',
            'grid', 'style', 'logx', 'logy', 'loglog', 'xlim', 'ylim',
            'rot', 'colormap', 'table', 'yerr', 'xerr', 'sort_columns',
            'secondary_y', 'colorbar', 'position', 'stacked', 'mark_right',
            'include_bool', 'backend')
        gfbn__rpj, czinn__pmuuh = bodo.utils.typing.fold_typing_args(func_name,
            args, kws, bqwc__nun, qyyrd__exh, jzu__eoajn)
        uen__mlwps = czinn__pmuuh[2]
        if not is_overload_constant_str(uen__mlwps):
            raise BodoError(
                f"{func_name}: kind must be a constant string and one of ('line', 'scatter')."
                )
        anfsa__bqb = czinn__pmuuh[0]
        if not is_overload_none(anfsa__bqb) and not (is_overload_int(
            anfsa__bqb) or is_overload_constant_str(anfsa__bqb)):
            raise BodoError(
                f'{func_name}: x must be a constant column name, constant integer, or None.'
                )
        if is_overload_constant_str(anfsa__bqb):
            xewcu__ycfa = get_overload_const_str(anfsa__bqb)
            if xewcu__ycfa not in df.columns:
                raise BodoError(f'{func_name}: {xewcu__ycfa} column not found.'
                    )
        elif is_overload_int(anfsa__bqb):
            lwrno__vuixq = get_overload_const_int(anfsa__bqb)
            if lwrno__vuixq > len(df.columns):
                raise BodoError(
                    f'{func_name}: x: {lwrno__vuixq} is out of bounds for axis 0 with size {len(df.columns)}'
                    )
            anfsa__bqb = df.columns[anfsa__bqb]
        wysbs__sndzi = czinn__pmuuh[1]
        if not is_overload_none(wysbs__sndzi) and not (is_overload_int(
            wysbs__sndzi) or is_overload_constant_str(wysbs__sndzi)):
            raise BodoError(
                'df.plot(): y must be a constant column name, constant integer, or None.'
                )
        if is_overload_constant_str(wysbs__sndzi):
            ojj__uasew = get_overload_const_str(wysbs__sndzi)
            if ojj__uasew not in df.columns:
                raise BodoError(f'{func_name}: {ojj__uasew} column not found.')
        elif is_overload_int(wysbs__sndzi):
            azab__kewd = get_overload_const_int(wysbs__sndzi)
            if azab__kewd > len(df.columns):
                raise BodoError(
                    f'{func_name}: y: {azab__kewd} is out of bounds for axis 0 with size {len(df.columns)}'
                    )
            wysbs__sndzi = df.columns[wysbs__sndzi]
        gji__angll = czinn__pmuuh[3]
        if not is_overload_none(gji__angll) and not is_tuple_like_type(
            gji__angll):
            raise BodoError(
                f'{func_name}: figsize must be a constant numeric tuple (width, height) or None.'
                )
        nonw__ujdaj = czinn__pmuuh[10]
        if not is_overload_none(nonw__ujdaj) and not is_overload_constant_str(
            nonw__ujdaj):
            raise BodoError(
                f'{func_name}: title must be a constant string or None.')
        xnuy__pkdt = czinn__pmuuh[12]
        if not is_overload_bool(xnuy__pkdt):
            raise BodoError(f'{func_name}: legend must be a boolean type.')
        btnn__daero = czinn__pmuuh[17]
        if not is_overload_none(btnn__daero) and not is_tuple_like_type(
            btnn__daero):
            raise BodoError(
                f'{func_name}: xticks must be a constant tuple or None.')
        wibiy__hocl = czinn__pmuuh[18]
        if not is_overload_none(wibiy__hocl) and not is_tuple_like_type(
            wibiy__hocl):
            raise BodoError(
                f'{func_name}: yticks must be a constant tuple or None.')
        gsvvi__fkl = czinn__pmuuh[22]
        if not is_overload_none(gsvvi__fkl) and not is_overload_int(gsvvi__fkl
            ):
            raise BodoError(
                f'{func_name}: fontsize must be an integer or None.')
        jisl__ujyg = czinn__pmuuh[29]
        if not is_overload_none(jisl__ujyg) and not is_overload_constant_str(
            jisl__ujyg):
            raise BodoError(
                f'{func_name}: xlabel must be a constant string or None.')
        mfzk__fip = czinn__pmuuh[30]
        if not is_overload_none(mfzk__fip) and not is_overload_constant_str(
            mfzk__fip):
            raise BodoError(
                f'{func_name}: ylabel must be a constant string or None.')
        gbjt__hsm = types.List(types.mpl_line_2d_type)
        uen__mlwps = get_overload_const_str(uen__mlwps)
        if uen__mlwps == 'scatter':
            if is_overload_none(anfsa__bqb) and is_overload_none(wysbs__sndzi):
                raise BodoError(
                    f'{func_name}: {uen__mlwps} requires an x and y column.')
            elif is_overload_none(anfsa__bqb):
                raise BodoError(
                    f'{func_name}: {uen__mlwps} x column is missing.')
            elif is_overload_none(wysbs__sndzi):
                raise BodoError(
                    f'{func_name}: {uen__mlwps} y column is missing.')
            gbjt__hsm = types.mpl_path_collection_type
        elif uen__mlwps != 'line':
            raise BodoError(f'{func_name}: {uen__mlwps} plot is not supported.'
                )
        return signature(gbjt__hsm, *czinn__pmuuh).replace(pysig=gfbn__rpj)

    def generic_resolve(self, df, attr):
        if self._is_existing_attr(attr):
            return
        check_runtime_cols_unsupported(df,
            'Acessing DataFrame columns by attribute')
        if attr in df.columns:
            cbta__kzieh = df.columns.index(attr)
            arr_typ = df.data[cbta__kzieh]
            return SeriesType(arr_typ.dtype, arr_typ, df.index, types.
                StringLiteral(attr))
        if len(df.columns) > 0 and isinstance(df.columns[0], tuple):
            tcx__iacau = []
            clbpb__twus = []
            dhfyu__rdeim = False
            for i, iurle__vtgpl in enumerate(df.columns):
                if iurle__vtgpl[0] != attr:
                    continue
                dhfyu__rdeim = True
                tcx__iacau.append(iurle__vtgpl[1] if len(iurle__vtgpl) == 2
                     else iurle__vtgpl[1:])
                clbpb__twus.append(df.data[i])
            if dhfyu__rdeim:
                return DataFrameType(tuple(clbpb__twus), df.index, tuple(
                    tcx__iacau))


DataFrameAttribute._no_unliteral = True


@overload(operator.getitem, no_unliteral=True)
def namedtuple_getitem_overload(tup, idx):
    if isinstance(tup, types.BaseNamedTuple) and is_overload_constant_str(idx):
        erexo__tvkie = get_overload_const_str(idx)
        val_ind = tup.instance_class._fields.index(erexo__tvkie)
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
        xnztt__kwm = builder.extract_value(payload.data, i)
        context.nrt.decref(builder, df_type.data[i], xnztt__kwm)
    context.nrt.decref(builder, df_type.index, payload.index)


def define_df_dtor(context, builder, df_type, payload_type):
    wcu__hfwgv = builder.module
    xhic__cszlo = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    elpj__epray = cgutils.get_or_insert_function(wcu__hfwgv, xhic__cszlo,
        name='.dtor.df.{}'.format(df_type))
    if not elpj__epray.is_declaration:
        return elpj__epray
    elpj__epray.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(elpj__epray.append_basic_block())
    fnb__pwrm = elpj__epray.args[0]
    awjgh__bytso = context.get_value_type(payload_type).as_pointer()
    pvgd__olkq = builder.bitcast(fnb__pwrm, awjgh__bytso)
    payload = context.make_helper(builder, payload_type, ref=pvgd__olkq)
    decref_df_data(context, builder, payload, df_type)
    has_parent = cgutils.is_not_null(builder, payload.parent)
    with builder.if_then(has_parent):
        wqe__sgl = context.get_python_api(builder)
        ewlif__lvpkq = wqe__sgl.gil_ensure()
        wqe__sgl.decref(payload.parent)
        wqe__sgl.gil_release(ewlif__lvpkq)
    builder.ret_void()
    return elpj__epray


def construct_dataframe(context, builder, df_type, data_tup, index_val,
    parent=None, colnames=None):
    payload_type = DataFramePayloadType(df_type)
    luddy__ija = cgutils.create_struct_proxy(payload_type)(context, builder)
    luddy__ija.data = data_tup
    luddy__ija.index = index_val
    if colnames is not None:
        assert df_type.has_runtime_cols, 'construct_dataframe can only provide colnames if columns are determined at runtime'
        luddy__ija.columns = colnames
    xapm__vhzi = context.get_value_type(payload_type)
    ccwdm__jkhq = context.get_abi_sizeof(xapm__vhzi)
    udo__wdo = define_df_dtor(context, builder, df_type, payload_type)
    bnltv__cbn = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, ccwdm__jkhq), udo__wdo)
    mfw__cxu = context.nrt.meminfo_data(builder, bnltv__cbn)
    nrxu__ris = builder.bitcast(mfw__cxu, xapm__vhzi.as_pointer())
    znv__qqe = cgutils.create_struct_proxy(df_type)(context, builder)
    znv__qqe.meminfo = bnltv__cbn
    if parent is None:
        znv__qqe.parent = cgutils.get_null_value(znv__qqe.parent.type)
    else:
        znv__qqe.parent = parent
        luddy__ija.parent = parent
        has_parent = cgutils.is_not_null(builder, parent)
        with builder.if_then(has_parent):
            wqe__sgl = context.get_python_api(builder)
            ewlif__lvpkq = wqe__sgl.gil_ensure()
            wqe__sgl.incref(parent)
            wqe__sgl.gil_release(ewlif__lvpkq)
    builder.store(luddy__ija._getvalue(), nrxu__ris)
    return znv__qqe._getvalue()


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
        gaes__wubmj = [data_typ.dtype.arr_types.dtype] * len(data_typ.dtype
            .arr_types)
    else:
        gaes__wubmj = [rgqji__lceb for rgqji__lceb in data_typ.dtype.arr_types]
    smy__ilgvz = DataFrameType(tuple(gaes__wubmj + [colnames_index_typ]),
        index_typ, None, is_table_format=True)

    def codegen(context, builder, signature, args):
        df_type = signature.return_type
        data_tup, index, col_names = args
        parent = None
        ngqq__vfay = construct_dataframe(context, builder, df_type,
            data_tup, index, parent, col_names)
        context.nrt.incref(builder, data_typ, data_tup)
        context.nrt.incref(builder, index_typ, index)
        context.nrt.incref(builder, colnames_index_typ, col_names)
        return ngqq__vfay
    sig = signature(smy__ilgvz, data_typ, index_typ, colnames_index_typ)
    return sig, codegen


@intrinsic
def init_dataframe(typingctx, data_tup_typ, index_typ, col_names_typ=None):
    assert is_pd_index_type(index_typ) or isinstance(index_typ, MultiIndexType
        ), 'init_dataframe(): invalid index type'
    xou__mhnu = len(data_tup_typ.types)
    if xou__mhnu == 0:
        column_names = ()
    elif isinstance(col_names_typ, types.TypeRef):
        column_names = col_names_typ.instance_type.columns
    else:
        column_names = get_const_tup_vals(col_names_typ)
    if xou__mhnu == 1 and isinstance(data_tup_typ.types[0], TableType):
        xou__mhnu = len(data_tup_typ.types[0].arr_types)
    assert len(column_names
        ) == xou__mhnu, 'init_dataframe(): number of column names does not match number of columns'
    is_table_format = False
    wmk__ujd = data_tup_typ.types
    if xou__mhnu != 0 and isinstance(data_tup_typ.types[0], TableType):
        wmk__ujd = data_tup_typ.types[0].arr_types
        is_table_format = True
    smy__ilgvz = DataFrameType(wmk__ujd, index_typ, column_names,
        is_table_format=is_table_format)

    def codegen(context, builder, signature, args):
        df_type = signature.return_type
        data_tup = args[0]
        index_val = args[1]
        parent = None
        if is_table_format:
            xxx__sxphl = cgutils.create_struct_proxy(smy__ilgvz.table_type)(
                context, builder, builder.extract_value(data_tup, 0))
            parent = xxx__sxphl.parent
        ngqq__vfay = construct_dataframe(context, builder, df_type,
            data_tup, index_val, parent, None)
        context.nrt.incref(builder, data_tup_typ, data_tup)
        context.nrt.incref(builder, index_typ, index_val)
        return ngqq__vfay
    sig = signature(smy__ilgvz, data_tup_typ, index_typ, col_names_typ)
    return sig, codegen


@intrinsic
def has_parent(typingctx, df=None):
    check_runtime_cols_unsupported(df, 'has_parent')

    def codegen(context, builder, sig, args):
        znv__qqe = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        return cgutils.is_not_null(builder, znv__qqe.parent)
    return signature(types.bool_, df), codegen


@intrinsic
def _column_needs_unboxing(typingctx, df_typ, i_typ=None):
    check_runtime_cols_unsupported(df_typ, '_column_needs_unboxing')
    assert isinstance(df_typ, DataFrameType) and is_overload_constant_int(i_typ
        )

    def codegen(context, builder, sig, args):
        luddy__ija = get_dataframe_payload(context, builder, df_typ, args[0])
        mit__hyzgc = get_overload_const_int(i_typ)
        arr_typ = df_typ.data[mit__hyzgc]
        if df_typ.is_table_format:
            xxx__sxphl = cgutils.create_struct_proxy(df_typ.table_type)(context
                , builder, builder.extract_value(luddy__ija.data, 0))
            ibce__xquns = df_typ.table_type.type_to_blk[arr_typ]
            bowj__joo = getattr(xxx__sxphl, f'block_{ibce__xquns}')
            mqhsh__vdqe = ListInstance(context, builder, types.List(arr_typ
                ), bowj__joo)
            ksdz__jockh = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[mit__hyzgc])
            xnztt__kwm = mqhsh__vdqe.getitem(ksdz__jockh)
        else:
            xnztt__kwm = builder.extract_value(luddy__ija.data, mit__hyzgc)
        qdh__skl = cgutils.alloca_once_value(builder, xnztt__kwm)
        efszq__dnsdj = cgutils.alloca_once_value(builder, context.
            get_constant_null(arr_typ))
        return is_ll_eq(builder, qdh__skl, efszq__dnsdj)
    return signature(types.bool_, df_typ, i_typ), codegen


def get_dataframe_payload(context, builder, df_type, value):
    bnltv__cbn = cgutils.create_struct_proxy(df_type)(context, builder, value
        ).meminfo
    payload_type = DataFramePayloadType(df_type)
    payload = context.nrt.meminfo_data(builder, bnltv__cbn)
    awjgh__bytso = context.get_value_type(payload_type).as_pointer()
    payload = builder.bitcast(payload, awjgh__bytso)
    return context.make_helper(builder, payload_type, ref=payload)


@intrinsic
def _get_dataframe_data(typingctx, df_typ=None):
    check_runtime_cols_unsupported(df_typ, '_get_dataframe_data')
    smy__ilgvz = types.Tuple(df_typ.data)
    if df_typ.is_table_format:
        smy__ilgvz = types.Tuple([TableType(df_typ.data)])
    sig = signature(smy__ilgvz, df_typ)

    def codegen(context, builder, signature, args):
        luddy__ija = get_dataframe_payload(context, builder, signature.args
            [0], args[0])
        return impl_ret_borrowed(context, builder, signature.return_type,
            luddy__ija.data)
    return sig, codegen


@intrinsic
def get_dataframe_index(typingctx, df_typ=None):

    def codegen(context, builder, signature, args):
        luddy__ija = get_dataframe_payload(context, builder, signature.args
            [0], args[0])
        return impl_ret_borrowed(context, builder, df_typ.index, luddy__ija
            .index)
    smy__ilgvz = df_typ.index
    sig = signature(smy__ilgvz, df_typ)
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
        vxr__ivs = df.data[i]
        return vxr__ivs(*args)


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
        luddy__ija = get_dataframe_payload(context, builder, signature.args
            [0], args[0])
        return impl_ret_borrowed(context, builder, df_typ.table_type,
            builder.extract_value(luddy__ija.data, 0))
    return df_typ.table_type(df_typ), codegen


@intrinsic
def get_dataframe_column_names(typingctx, df_typ=None):
    assert df_typ.has_runtime_cols, 'get_dataframe_column_names() expects columns to be determined at runtime'

    def codegen(context, builder, signature, args):
        luddy__ija = get_dataframe_payload(context, builder, signature.args
            [0], args[0])
        return impl_ret_borrowed(context, builder, df_typ.
            runtime_colname_typ, luddy__ija.columns)
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
    bgipj__blq = self.typemap[data_tup.name]
    if any(is_tuple_like_type(rgqji__lceb) for rgqji__lceb in bgipj__blq.types
        ):
        return None
    if equiv_set.has_shape(data_tup):
        pcv__kki = equiv_set.get_shape(data_tup)
        if len(pcv__kki) > 1:
            equiv_set.insert_equiv(*pcv__kki)
        if len(pcv__kki) > 0:
            bkrpn__cwa = self.typemap[index.name]
            if not isinstance(bkrpn__cwa, HeterogeneousIndexType
                ) and equiv_set.has_shape(index):
                equiv_set.insert_equiv(pcv__kki[0], index)
            return ArrayAnalysis.AnalyzeResult(shape=(pcv__kki[0], len(
                pcv__kki)), pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_dataframe_ext_init_dataframe
    ) = init_dataframe_equiv


def get_dataframe_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    bgknt__hxfgr = args[0]
    data_types = self.typemap[bgknt__hxfgr.name].data
    if any(is_tuple_like_type(rgqji__lceb) for rgqji__lceb in data_types):
        return None
    if equiv_set.has_shape(bgknt__hxfgr):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            bgknt__hxfgr)[0], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_data
    ) = get_dataframe_data_equiv


def get_dataframe_index_equiv(self, scope, equiv_set, loc, args, kws):
    from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
    assert len(args) == 1 and not kws
    bgknt__hxfgr = args[0]
    bkrpn__cwa = self.typemap[bgknt__hxfgr.name].index
    if isinstance(bkrpn__cwa, HeterogeneousIndexType):
        return None
    if equiv_set.has_shape(bgknt__hxfgr):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            bgknt__hxfgr)[0], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_index
    ) = get_dataframe_index_equiv


def get_dataframe_table_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    bgknt__hxfgr = args[0]
    if equiv_set.has_shape(bgknt__hxfgr):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            bgknt__hxfgr), pre=[])


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_table
    ) = get_dataframe_table_equiv


def get_dataframe_column_names_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    bgknt__hxfgr = args[0]
    if equiv_set.has_shape(bgknt__hxfgr):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            bgknt__hxfgr)[1], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_column_names
    ) = get_dataframe_column_names_equiv


@intrinsic
def set_dataframe_data(typingctx, df_typ, c_ind_typ, arr_typ=None):
    check_runtime_cols_unsupported(df_typ, 'set_dataframe_data')
    assert is_overload_constant_int(c_ind_typ)
    mit__hyzgc = get_overload_const_int(c_ind_typ)
    if df_typ.data[mit__hyzgc] != arr_typ:
        raise BodoError(
            'Changing dataframe column data type inplace is not supported in conditionals/loops or for dataframe arguments'
            )

    def codegen(context, builder, signature, args):
        xpij__upb, wxf__rfh, eqjo__bld = args
        luddy__ija = get_dataframe_payload(context, builder, df_typ, xpij__upb)
        if df_typ.is_table_format:
            xxx__sxphl = cgutils.create_struct_proxy(df_typ.table_type)(context
                , builder, builder.extract_value(luddy__ija.data, 0))
            ibce__xquns = df_typ.table_type.type_to_blk[arr_typ]
            bowj__joo = getattr(xxx__sxphl, f'block_{ibce__xquns}')
            mqhsh__vdqe = ListInstance(context, builder, types.List(arr_typ
                ), bowj__joo)
            ksdz__jockh = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[mit__hyzgc])
            mqhsh__vdqe.setitem(ksdz__jockh, eqjo__bld, True)
        else:
            xnztt__kwm = builder.extract_value(luddy__ija.data, mit__hyzgc)
            context.nrt.decref(builder, df_typ.data[mit__hyzgc], xnztt__kwm)
            luddy__ija.data = builder.insert_value(luddy__ija.data,
                eqjo__bld, mit__hyzgc)
            context.nrt.incref(builder, arr_typ, eqjo__bld)
        znv__qqe = cgutils.create_struct_proxy(df_typ)(context, builder,
            value=xpij__upb)
        payload_type = DataFramePayloadType(df_typ)
        pvgd__olkq = context.nrt.meminfo_data(builder, znv__qqe.meminfo)
        awjgh__bytso = context.get_value_type(payload_type).as_pointer()
        pvgd__olkq = builder.bitcast(pvgd__olkq, awjgh__bytso)
        builder.store(luddy__ija._getvalue(), pvgd__olkq)
        return impl_ret_borrowed(context, builder, df_typ, xpij__upb)
    sig = signature(df_typ, df_typ, c_ind_typ, arr_typ)
    return sig, codegen


@intrinsic
def set_df_index(typingctx, df_t, index_t=None):
    check_runtime_cols_unsupported(df_t, 'set_df_index')

    def codegen(context, builder, signature, args):
        ufpu__vvfoq = args[0]
        index_val = args[1]
        df_typ = signature.args[0]
        ohd__rawlu = cgutils.create_struct_proxy(df_typ)(context, builder,
            value=ufpu__vvfoq)
        lylmr__kom = get_dataframe_payload(context, builder, df_typ,
            ufpu__vvfoq)
        znv__qqe = construct_dataframe(context, builder, signature.
            return_type, lylmr__kom.data, index_val, ohd__rawlu.parent, None)
        context.nrt.incref(builder, index_t, index_val)
        context.nrt.incref(builder, types.Tuple(df_t.data), lylmr__kom.data)
        return znv__qqe
    smy__ilgvz = DataFrameType(df_t.data, index_t, df_t.columns, df_t.dist,
        df_t.is_table_format)
    sig = signature(smy__ilgvz, df_t, index_t)
    return sig, codegen


@intrinsic
def set_df_column_with_reflect(typingctx, df_type, cname_type, arr_type=None):
    check_runtime_cols_unsupported(df_type, 'set_df_column_with_reflect')
    assert is_literal_type(cname_type), 'constant column name expected'
    col_name = get_literal_value(cname_type)
    xou__mhnu = len(df_type.columns)
    snz__xefr = xou__mhnu
    snqo__qni = df_type.data
    column_names = df_type.columns
    index_typ = df_type.index
    ajxp__ckz = col_name not in df_type.columns
    mit__hyzgc = xou__mhnu
    if ajxp__ckz:
        snqo__qni += arr_type,
        column_names += col_name,
        snz__xefr += 1
    else:
        mit__hyzgc = df_type.columns.index(col_name)
        snqo__qni = tuple(arr_type if i == mit__hyzgc else snqo__qni[i] for
            i in range(xou__mhnu))

    def codegen(context, builder, signature, args):
        xpij__upb, wxf__rfh, eqjo__bld = args
        in_dataframe_payload = get_dataframe_payload(context, builder,
            df_type, xpij__upb)
        fnl__aqw = cgutils.create_struct_proxy(df_type)(context, builder,
            value=xpij__upb)
        if df_type.is_table_format:
            adgtw__nxz = df_type.table_type
            abct__yqwk = builder.extract_value(in_dataframe_payload.data, 0)
            qwyn__bizxn = TableType(snqo__qni)
            fvhk__zzmlk = set_table_data_codegen(context, builder,
                adgtw__nxz, abct__yqwk, qwyn__bizxn, arr_type, eqjo__bld,
                mit__hyzgc, ajxp__ckz)
            data_tup = context.make_tuple(builder, types.Tuple([qwyn__bizxn
                ]), [fvhk__zzmlk])
        else:
            wmk__ujd = [(builder.extract_value(in_dataframe_payload.data, i
                ) if i != mit__hyzgc else eqjo__bld) for i in range(xou__mhnu)]
            if ajxp__ckz:
                wmk__ujd.append(eqjo__bld)
            for bgknt__hxfgr, qqc__xkvk in zip(wmk__ujd, snqo__qni):
                context.nrt.incref(builder, qqc__xkvk, bgknt__hxfgr)
            data_tup = context.make_tuple(builder, types.Tuple(snqo__qni),
                wmk__ujd)
        index_val = in_dataframe_payload.index
        context.nrt.incref(builder, index_typ, index_val)
        lolde__lsedt = construct_dataframe(context, builder, signature.
            return_type, data_tup, index_val, fnl__aqw.parent, None)
        if not ajxp__ckz and arr_type == df_type.data[mit__hyzgc]:
            decref_df_data(context, builder, in_dataframe_payload, df_type)
            payload_type = DataFramePayloadType(df_type)
            pvgd__olkq = context.nrt.meminfo_data(builder, fnl__aqw.meminfo)
            awjgh__bytso = context.get_value_type(payload_type).as_pointer()
            pvgd__olkq = builder.bitcast(pvgd__olkq, awjgh__bytso)
            gwj__ertrc = get_dataframe_payload(context, builder, df_type,
                lolde__lsedt)
            builder.store(gwj__ertrc._getvalue(), pvgd__olkq)
            context.nrt.incref(builder, index_typ, index_val)
            if df_type.is_table_format:
                context.nrt.incref(builder, qwyn__bizxn, builder.
                    extract_value(data_tup, 0))
            else:
                for bgknt__hxfgr, qqc__xkvk in zip(wmk__ujd, snqo__qni):
                    context.nrt.incref(builder, qqc__xkvk, bgknt__hxfgr)
        has_parent = cgutils.is_not_null(builder, fnl__aqw.parent)
        with builder.if_then(has_parent):
            wqe__sgl = context.get_python_api(builder)
            ewlif__lvpkq = wqe__sgl.gil_ensure()
            xqzun__irvxd = context.get_env_manager(builder)
            context.nrt.incref(builder, arr_type, eqjo__bld)
            yhx__kwv = numba.core.pythonapi._BoxContext(context, builder,
                wqe__sgl, xqzun__irvxd)
            hyll__clnbi = yhx__kwv.pyapi.from_native_value(arr_type,
                eqjo__bld, yhx__kwv.env_manager)
            if isinstance(col_name, str):
                bxarj__ozmg = context.insert_const_string(builder.module,
                    col_name)
                mcues__mek = wqe__sgl.string_from_string(bxarj__ozmg)
            else:
                assert isinstance(col_name, int)
                mcues__mek = wqe__sgl.long_from_longlong(context.
                    get_constant(types.intp, col_name))
            wqe__sgl.object_setitem(fnl__aqw.parent, mcues__mek, hyll__clnbi)
            wqe__sgl.decref(hyll__clnbi)
            wqe__sgl.decref(mcues__mek)
            wqe__sgl.gil_release(ewlif__lvpkq)
        return lolde__lsedt
    smy__ilgvz = DataFrameType(snqo__qni, index_typ, column_names, df_type.
        dist, df_type.is_table_format)
    sig = signature(smy__ilgvz, df_type, cname_type, arr_type)
    return sig, codegen


@lower_constant(DataFrameType)
def lower_constant_dataframe(context, builder, df_type, pyval):
    check_runtime_cols_unsupported(df_type, 'lowering a constant DataFrame')
    xou__mhnu = len(pyval.columns)
    wmk__ujd = []
    for i in range(xou__mhnu):
        bftle__fyalp = pyval.iloc[:, i]
        if isinstance(df_type.data[i], bodo.DatetimeArrayType):
            hyll__clnbi = bftle__fyalp.array
        else:
            hyll__clnbi = bftle__fyalp.values
        wmk__ujd.append(hyll__clnbi)
    wmk__ujd = tuple(wmk__ujd)
    if df_type.is_table_format:
        xxx__sxphl = context.get_constant_generic(builder, df_type.
            table_type, Table(wmk__ujd))
        data_tup = lir.Constant.literal_struct([xxx__sxphl])
    else:
        data_tup = lir.Constant.literal_struct([context.
            get_constant_generic(builder, df_type.data[i], iurle__vtgpl) for
            i, iurle__vtgpl in enumerate(wmk__ujd)])
    index_val = context.get_constant_generic(builder, df_type.index, pyval.
        index)
    pmpag__bov = context.get_constant_null(types.pyobject)
    payload = lir.Constant.literal_struct([data_tup, index_val, pmpag__bov])
    payload = cgutils.global_constant(builder, '.const.payload', payload
        ).bitcast(cgutils.voidptr_t)
    tlus__mslms = context.get_constant(types.int64, -1)
    nhlu__wcva = context.get_constant_null(types.voidptr)
    bnltv__cbn = lir.Constant.literal_struct([tlus__mslms, nhlu__wcva,
        nhlu__wcva, payload, tlus__mslms])
    bnltv__cbn = cgutils.global_constant(builder, '.const.meminfo', bnltv__cbn
        ).bitcast(cgutils.voidptr_t)
    return lir.Constant.literal_struct([bnltv__cbn, pmpag__bov])


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
        mati__wnwu = context.cast(builder, in_dataframe_payload.index,
            fromty.index, toty.index)
    else:
        mati__wnwu = in_dataframe_payload.index
        context.nrt.incref(builder, fromty.index, mati__wnwu)
    if (fromty.is_table_format == toty.is_table_format and fromty.data ==
        toty.data):
        clbpb__twus = in_dataframe_payload.data
        if fromty.is_table_format:
            context.nrt.incref(builder, types.Tuple([fromty.table_type]),
                clbpb__twus)
        else:
            context.nrt.incref(builder, types.BaseTuple.from_types(fromty.
                data), clbpb__twus)
    elif not fromty.is_table_format and toty.is_table_format:
        clbpb__twus = _cast_df_data_to_table_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    elif fromty.is_table_format and not toty.is_table_format:
        clbpb__twus = _cast_df_data_to_tuple_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    elif fromty.is_table_format and toty.is_table_format:
        clbpb__twus = _cast_df_data_keep_table_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    else:
        clbpb__twus = _cast_df_data_keep_tuple_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    return construct_dataframe(context, builder, toty, clbpb__twus,
        mati__wnwu, in_dataframe_payload.parent, None)


def _cast_empty_df(context, builder, toty):
    detjn__bfdgg = {}
    if isinstance(toty.index, RangeIndexType):
        index = 'bodo.hiframes.pd_index_ext.init_range_index(0, 0, 1, None)'
    else:
        vui__eyq = get_index_data_arr_types(toty.index)[0]
        bdnpl__dexq = bodo.utils.transform.get_type_alloc_counts(vui__eyq) - 1
        ulv__uuwi = ', '.join('0' for wxf__rfh in range(bdnpl__dexq))
        index = (
            'bodo.utils.conversion.index_from_array(bodo.utils.utils.alloc_type(0, index_arr_type, ({}{})))'
            .format(ulv__uuwi, ', ' if bdnpl__dexq == 1 else ''))
        detjn__bfdgg['index_arr_type'] = vui__eyq
    galfd__qpjij = []
    for i, arr_typ in enumerate(toty.data):
        bdnpl__dexq = bodo.utils.transform.get_type_alloc_counts(arr_typ) - 1
        ulv__uuwi = ', '.join('0' for wxf__rfh in range(bdnpl__dexq))
        mmv__zgkpz = ('bodo.utils.utils.alloc_type(0, arr_type{}, ({}{}))'.
            format(i, ulv__uuwi, ', ' if bdnpl__dexq == 1 else ''))
        galfd__qpjij.append(mmv__zgkpz)
        detjn__bfdgg[f'arr_type{i}'] = arr_typ
    galfd__qpjij = ', '.join(galfd__qpjij)
    iqkj__cxo = 'def impl():\n'
    sgxfk__bwzw = bodo.hiframes.dataframe_impl._gen_init_df(iqkj__cxo, toty
        .columns, galfd__qpjij, index, detjn__bfdgg)
    df = context.compile_internal(builder, sgxfk__bwzw, toty(), [])
    return df


def _cast_df_data_to_table_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting traditional DataFrame to table format')
    fho__ikdb = toty.table_type
    xxx__sxphl = cgutils.create_struct_proxy(fho__ikdb)(context, builder)
    xxx__sxphl.parent = in_dataframe_payload.parent
    for rgqji__lceb, ibce__xquns in fho__ikdb.type_to_blk.items():
        zwteb__famf = context.get_constant(types.int64, len(fho__ikdb.
            block_to_arr_ind[ibce__xquns]))
        wxf__rfh, ebp__ywbpj = ListInstance.allocate_ex(context, builder,
            types.List(rgqji__lceb), zwteb__famf)
        ebp__ywbpj.size = zwteb__famf
        setattr(xxx__sxphl, f'block_{ibce__xquns}', ebp__ywbpj.value)
    for i, rgqji__lceb in enumerate(fromty.data):
        tnxcr__dmcw = toty.data[i]
        if rgqji__lceb != tnxcr__dmcw:
            ranc__tmpt = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*ranc__tmpt)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        xnztt__kwm = builder.extract_value(in_dataframe_payload.data, i)
        if rgqji__lceb != tnxcr__dmcw:
            ueyyn__nvz = context.cast(builder, xnztt__kwm, rgqji__lceb,
                tnxcr__dmcw)
            ahid__ceqg = False
        else:
            ueyyn__nvz = xnztt__kwm
            ahid__ceqg = True
        ibce__xquns = fho__ikdb.type_to_blk[rgqji__lceb]
        bowj__joo = getattr(xxx__sxphl, f'block_{ibce__xquns}')
        mqhsh__vdqe = ListInstance(context, builder, types.List(rgqji__lceb
            ), bowj__joo)
        ksdz__jockh = context.get_constant(types.int64, fho__ikdb.
            block_offsets[i])
        mqhsh__vdqe.setitem(ksdz__jockh, ueyyn__nvz, ahid__ceqg)
    data_tup = context.make_tuple(builder, types.Tuple([fho__ikdb]), [
        xxx__sxphl._getvalue()])
    return data_tup


def _cast_df_data_keep_tuple_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting traditional DataFrame columns')
    wmk__ujd = []
    for i in range(len(fromty.data)):
        if fromty.data[i] != toty.data[i]:
            ranc__tmpt = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*ranc__tmpt)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
            xnztt__kwm = builder.extract_value(in_dataframe_payload.data, i)
            ueyyn__nvz = context.cast(builder, xnztt__kwm, fromty.data[i],
                toty.data[i])
            ahid__ceqg = False
        else:
            ueyyn__nvz = builder.extract_value(in_dataframe_payload.data, i)
            ahid__ceqg = True
        if ahid__ceqg:
            context.nrt.incref(builder, toty.data[i], ueyyn__nvz)
        wmk__ujd.append(ueyyn__nvz)
    data_tup = context.make_tuple(builder, types.Tuple(toty.data), wmk__ujd)
    return data_tup


def _cast_df_data_keep_table_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting table format DataFrame columns')
    adgtw__nxz = fromty.table_type
    abct__yqwk = cgutils.create_struct_proxy(adgtw__nxz)(context, builder,
        builder.extract_value(in_dataframe_payload.data, 0))
    qwyn__bizxn = toty.table_type
    fvhk__zzmlk = cgutils.create_struct_proxy(qwyn__bizxn)(context, builder)
    fvhk__zzmlk.parent = in_dataframe_payload.parent
    for rgqji__lceb, ibce__xquns in qwyn__bizxn.type_to_blk.items():
        zwteb__famf = context.get_constant(types.int64, len(qwyn__bizxn.
            block_to_arr_ind[ibce__xquns]))
        wxf__rfh, ebp__ywbpj = ListInstance.allocate_ex(context, builder,
            types.List(rgqji__lceb), zwteb__famf)
        ebp__ywbpj.size = zwteb__famf
        setattr(fvhk__zzmlk, f'block_{ibce__xquns}', ebp__ywbpj.value)
    for i in range(len(fromty.data)):
        qsr__qvqp = fromty.data[i]
        tnxcr__dmcw = toty.data[i]
        if qsr__qvqp != tnxcr__dmcw:
            ranc__tmpt = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*ranc__tmpt)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        zaax__wkw = adgtw__nxz.type_to_blk[qsr__qvqp]
        its__wvqhp = getattr(abct__yqwk, f'block_{zaax__wkw}')
        bgch__mdf = ListInstance(context, builder, types.List(qsr__qvqp),
            its__wvqhp)
        vab__coxfd = context.get_constant(types.int64, adgtw__nxz.
            block_offsets[i])
        xnztt__kwm = bgch__mdf.getitem(vab__coxfd)
        if qsr__qvqp != tnxcr__dmcw:
            ueyyn__nvz = context.cast(builder, xnztt__kwm, qsr__qvqp,
                tnxcr__dmcw)
            ahid__ceqg = False
        else:
            ueyyn__nvz = xnztt__kwm
            ahid__ceqg = True
        aayb__yqmnk = qwyn__bizxn.type_to_blk[rgqji__lceb]
        ebp__ywbpj = getattr(fvhk__zzmlk, f'block_{aayb__yqmnk}')
        sug__kthv = ListInstance(context, builder, types.List(tnxcr__dmcw),
            ebp__ywbpj)
        amgx__gakq = context.get_constant(types.int64, qwyn__bizxn.
            block_offsets[i])
        sug__kthv.setitem(amgx__gakq, ueyyn__nvz, ahid__ceqg)
    data_tup = context.make_tuple(builder, types.Tuple([qwyn__bizxn]), [
        fvhk__zzmlk._getvalue()])
    return data_tup


def _cast_df_data_to_tuple_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(fromty,
        'casting table format to traditional DataFrame')
    fho__ikdb = fromty.table_type
    xxx__sxphl = cgutils.create_struct_proxy(fho__ikdb)(context, builder,
        builder.extract_value(in_dataframe_payload.data, 0))
    wmk__ujd = []
    for i, rgqji__lceb in enumerate(toty.data):
        qsr__qvqp = fromty.data[i]
        if rgqji__lceb != qsr__qvqp:
            ranc__tmpt = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*ranc__tmpt)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        ibce__xquns = fho__ikdb.type_to_blk[rgqji__lceb]
        bowj__joo = getattr(xxx__sxphl, f'block_{ibce__xquns}')
        mqhsh__vdqe = ListInstance(context, builder, types.List(rgqji__lceb
            ), bowj__joo)
        ksdz__jockh = context.get_constant(types.int64, fho__ikdb.
            block_offsets[i])
        xnztt__kwm = mqhsh__vdqe.getitem(ksdz__jockh)
        if rgqji__lceb != qsr__qvqp:
            ueyyn__nvz = context.cast(builder, xnztt__kwm, qsr__qvqp,
                rgqji__lceb)
            ahid__ceqg = False
        else:
            ueyyn__nvz = xnztt__kwm
            ahid__ceqg = True
        if ahid__ceqg:
            context.nrt.incref(builder, rgqji__lceb, ueyyn__nvz)
        wmk__ujd.append(ueyyn__nvz)
    data_tup = context.make_tuple(builder, types.Tuple(toty.data), wmk__ujd)
    return data_tup


@overload(pd.DataFrame, inline='always', no_unliteral=True)
def pd_dataframe_overload(data=None, index=None, columns=None, dtype=None,
    copy=False):
    if not is_overload_constant_bool(copy):
        raise BodoError(
            "pd.DataFrame(): 'copy' argument should be a constant boolean")
    copy = get_overload_const(copy)
    rqvek__tfp, galfd__qpjij, index_arg = _get_df_args(data, index, columns,
        dtype, copy)
    rdbe__ulm = gen_const_tup(rqvek__tfp)
    iqkj__cxo = (
        'def _init_df(data=None, index=None, columns=None, dtype=None, copy=False):\n'
        )
    iqkj__cxo += (
        '  return bodo.hiframes.pd_dataframe_ext.init_dataframe({}, {}, {})\n'
        .format(galfd__qpjij, index_arg, rdbe__ulm))
    leo__uscw = {}
    exec(iqkj__cxo, {'bodo': bodo, 'np': np}, leo__uscw)
    iii__donx = leo__uscw['_init_df']
    return iii__donx


@intrinsic
def _tuple_to_table_format_decoded(typingctx, df_typ):
    assert not df_typ.is_table_format, '_tuple_to_table_format requires a tuple format input'

    def codegen(context, builder, signature, args):
        return context.cast(builder, args[0], signature.args[0], signature.
            return_type)
    smy__ilgvz = DataFrameType(to_str_arr_if_dict_array(df_typ.data),
        df_typ.index, df_typ.columns, dist=df_typ.dist, is_table_format=True)
    sig = signature(smy__ilgvz, df_typ)
    return sig, codegen


@intrinsic
def _table_to_tuple_format_decoded(typingctx, df_typ):
    assert df_typ.is_table_format, '_tuple_to_table_format requires a table format input'

    def codegen(context, builder, signature, args):
        return context.cast(builder, args[0], signature.args[0], signature.
            return_type)
    smy__ilgvz = DataFrameType(to_str_arr_if_dict_array(df_typ.data),
        df_typ.index, df_typ.columns, dist=df_typ.dist, is_table_format=False)
    sig = signature(smy__ilgvz, df_typ)
    return sig, codegen


def _get_df_args(data, index, columns, dtype, copy):
    kct__itp = ''
    if not is_overload_none(dtype):
        kct__itp = '.astype(dtype)'
    index_is_none = is_overload_none(index)
    index_arg = 'bodo.utils.conversion.convert_to_index(index)'
    if isinstance(data, types.BaseTuple):
        if not data.types[0] == types.StringLiteral('__bodo_tup'):
            raise BodoError('pd.DataFrame tuple input data not supported yet')
        assert len(data.types) % 2 == 1, 'invalid const dict tuple structure'
        xou__mhnu = (len(data.types) - 1) // 2
        wflc__qvg = [rgqji__lceb.literal_value for rgqji__lceb in data.
            types[1:xou__mhnu + 1]]
        data_val_types = dict(zip(wflc__qvg, data.types[xou__mhnu + 1:]))
        wmk__ujd = ['data[{}]'.format(i) for i in range(xou__mhnu + 1, 2 *
            xou__mhnu + 1)]
        data_dict = dict(zip(wflc__qvg, wmk__ujd))
        if is_overload_none(index):
            for i, rgqji__lceb in enumerate(data.types[xou__mhnu + 1:]):
                if isinstance(rgqji__lceb, SeriesType):
                    index_arg = (
                        'bodo.hiframes.pd_series_ext.get_series_index(data[{}])'
                        .format(xou__mhnu + 1 + i))
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
        ivur__fuid = '.copy()' if copy else ''
        ojfk__kjdug = get_overload_const_list(columns)
        xou__mhnu = len(ojfk__kjdug)
        data_val_types = {yhx__kwv: data.copy(ndim=1) for yhx__kwv in
            ojfk__kjdug}
        wmk__ujd = ['data[:,{}]{}'.format(i, ivur__fuid) for i in range(
            xou__mhnu)]
        data_dict = dict(zip(ojfk__kjdug, wmk__ujd))
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
    galfd__qpjij = '({},)'.format(', '.join(
        'bodo.utils.conversion.coerce_to_array({}, True, scalar_to_arr_len={}){}'
        .format(data_dict[yhx__kwv], df_len, kct__itp) for yhx__kwv in
        col_names))
    if len(col_names) == 0:
        galfd__qpjij = '()'
    return col_names, galfd__qpjij, index_arg


def _get_df_len_from_info(data_dict, data_val_types, col_names,
    index_is_none, index_arg):
    df_len = '0'
    for yhx__kwv in col_names:
        if yhx__kwv in data_dict and is_iterable_type(data_val_types[yhx__kwv]
            ):
            df_len = 'len({})'.format(data_dict[yhx__kwv])
            break
    if df_len == '0' and not index_is_none:
        df_len = f'len({index_arg})'
    return df_len


def _fill_null_arrays(data_dict, col_names, df_len, dtype):
    if all(yhx__kwv in data_dict for yhx__kwv in col_names):
        return
    if is_overload_none(dtype):
        dtype = 'bodo.string_array_type'
    else:
        dtype = 'bodo.utils.conversion.array_type_from_dtype(dtype)'
    zuudy__eyg = 'bodo.libs.array_kernels.gen_na_array({}, {})'.format(df_len,
        dtype)
    for yhx__kwv in col_names:
        if yhx__kwv not in data_dict:
            data_dict[yhx__kwv] = zuudy__eyg


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
            rgqji__lceb = bodo.hiframes.pd_dataframe_ext.get_dataframe_table(df
                )
            return len(rgqji__lceb)
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
        brqo__vgjo = idx.literal_value
        if isinstance(brqo__vgjo, int):
            vxr__ivs = tup.types[brqo__vgjo]
        elif isinstance(brqo__vgjo, slice):
            vxr__ivs = types.BaseTuple.from_types(tup.types[brqo__vgjo])
        return signature(vxr__ivs, *args)


GetItemTuple.prefer_literal = True


@lower_builtin(operator.getitem, types.BaseTuple, types.IntegerLiteral)
@lower_builtin(operator.getitem, types.BaseTuple, types.SliceLiteral)
def getitem_tuple_lower(context, builder, sig, args):
    wxyi__dtv, idx = sig.args
    idx = idx.literal_value
    tup, wxf__rfh = args
    if isinstance(idx, int):
        if idx < 0:
            idx += len(wxyi__dtv)
        if not 0 <= idx < len(wxyi__dtv):
            raise IndexError('cannot index at %d in %s' % (idx, wxyi__dtv))
        rcknv__jcjk = builder.extract_value(tup, idx)
    elif isinstance(idx, slice):
        btfi__pgmyf = cgutils.unpack_tuple(builder, tup)[idx]
        rcknv__jcjk = context.make_tuple(builder, sig.return_type, btfi__pgmyf)
    else:
        raise NotImplementedError('unexpected index %r for %s' % (idx, sig.
            args[0]))
    return impl_ret_borrowed(context, builder, sig.return_type, rcknv__jcjk)


def join_dummy(left_df, right_df, left_on, right_on, how, suffix_x,
    suffix_y, is_join, indicator, _bodo_na_equal, gen_cond):
    return left_df


@infer_global(join_dummy)
class JoinTyper(AbstractTemplate):

    def generic(self, args, kws):
        from bodo.hiframes.pd_dataframe_ext import DataFrameType
        from bodo.utils.typing import is_overload_str
        assert not kws
        (left_df, right_df, left_on, right_on, tkh__euc, suffix_x, suffix_y,
            is_join, indicator, _bodo_na_equal, sau__byxq) = args
        left_on = get_overload_const_list(left_on)
        right_on = get_overload_const_list(right_on)
        zbvp__iye = set(left_on) & set(right_on)
        qxtu__rir = set(left_df.columns) & set(right_df.columns)
        flt__xxc = qxtu__rir - zbvp__iye
        yllhh__nobrj = '$_bodo_index_' in left_on
        deza__bhm = '$_bodo_index_' in right_on
        how = get_overload_const_str(tkh__euc)
        xtrjn__spkgt = how in {'left', 'outer'}
        wfz__unmpc = how in {'right', 'outer'}
        columns = []
        data = []
        if yllhh__nobrj:
            kln__aetle = bodo.utils.typing.get_index_data_arr_types(left_df
                .index)[0]
        else:
            kln__aetle = left_df.data[left_df.columns.index(left_on[0])]
        if deza__bhm:
            rpblq__cry = bodo.utils.typing.get_index_data_arr_types(right_df
                .index)[0]
        else:
            rpblq__cry = right_df.data[right_df.columns.index(right_on[0])]
        if yllhh__nobrj and not deza__bhm and not is_join.literal_value:
            npoj__hege = right_on[0]
            if npoj__hege in left_df.columns:
                columns.append(npoj__hege)
                if (rpblq__cry == bodo.dict_str_arr_type and kln__aetle ==
                    bodo.string_array_type):
                    ebq__zbji = bodo.string_array_type
                else:
                    ebq__zbji = rpblq__cry
                data.append(ebq__zbji)
        if deza__bhm and not yllhh__nobrj and not is_join.literal_value:
            ctx__lfmf = left_on[0]
            if ctx__lfmf in right_df.columns:
                columns.append(ctx__lfmf)
                if (kln__aetle == bodo.dict_str_arr_type and rpblq__cry ==
                    bodo.string_array_type):
                    ebq__zbji = bodo.string_array_type
                else:
                    ebq__zbji = kln__aetle
                data.append(ebq__zbji)
        for qsr__qvqp, bftle__fyalp in zip(left_df.data, left_df.columns):
            columns.append(str(bftle__fyalp) + suffix_x.literal_value if 
                bftle__fyalp in flt__xxc else bftle__fyalp)
            if bftle__fyalp in zbvp__iye:
                if qsr__qvqp == bodo.dict_str_arr_type:
                    qsr__qvqp = right_df.data[right_df.columns.index(
                        bftle__fyalp)]
                data.append(qsr__qvqp)
            else:
                if (qsr__qvqp == bodo.dict_str_arr_type and bftle__fyalp in
                    left_on):
                    if deza__bhm:
                        qsr__qvqp = rpblq__cry
                    else:
                        tjal__tmxnj = left_on.index(bftle__fyalp)
                        qrvi__uhlw = right_on[tjal__tmxnj]
                        qsr__qvqp = right_df.data[right_df.columns.index(
                            qrvi__uhlw)]
                if wfz__unmpc:
                    qsr__qvqp = to_nullable_type(qsr__qvqp)
                data.append(qsr__qvqp)
        for qsr__qvqp, bftle__fyalp in zip(right_df.data, right_df.columns):
            if bftle__fyalp not in zbvp__iye:
                columns.append(str(bftle__fyalp) + suffix_y.literal_value if
                    bftle__fyalp in flt__xxc else bftle__fyalp)
                if (qsr__qvqp == bodo.dict_str_arr_type and bftle__fyalp in
                    right_on):
                    if yllhh__nobrj:
                        qsr__qvqp = kln__aetle
                    else:
                        tjal__tmxnj = right_on.index(bftle__fyalp)
                        uru__fma = left_on[tjal__tmxnj]
                        qsr__qvqp = left_df.data[left_df.columns.index(
                            uru__fma)]
                if xtrjn__spkgt:
                    qsr__qvqp = to_nullable_type(qsr__qvqp)
                data.append(qsr__qvqp)
        hkyo__aiy = get_overload_const_bool(indicator)
        if hkyo__aiy:
            columns.append('_merge')
            data.append(bodo.CategoricalArrayType(bodo.PDCategoricalDtype((
                'left_only', 'right_only', 'both'), bodo.string_type, False)))
        index_typ = RangeIndexType(types.none)
        if yllhh__nobrj and deza__bhm and not is_overload_str(how, 'asof'):
            index_typ = left_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        elif yllhh__nobrj and not deza__bhm:
            index_typ = right_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        elif deza__bhm and not yllhh__nobrj:
            index_typ = left_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        bqay__fwjd = DataFrameType(tuple(data), index_typ, tuple(columns))
        return signature(bqay__fwjd, *args)


JoinTyper._no_unliteral = True


@lower_builtin(join_dummy, types.VarArg(types.Any))
def lower_join_dummy(context, builder, sig, args):
    znv__qqe = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return znv__qqe._getvalue()


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
    yomkl__uos = dict(join=join, join_axes=join_axes, keys=keys, levels=
        levels, names=names, verify_integrity=verify_integrity, sort=sort,
        copy=copy)
    qyyrd__exh = dict(join='outer', join_axes=None, keys=None, levels=None,
        names=None, verify_integrity=False, sort=None, copy=True)
    check_unsupported_args('pandas.concat', yomkl__uos, qyyrd__exh,
        package_name='pandas', module_name='General')
    iqkj__cxo = """def impl(objs, axis=0, join='outer', join_axes=None, ignore_index=False, keys=None, levels=None, names=None, verify_integrity=False, sort=None, copy=True):
"""
    if axis == 1:
        if not isinstance(objs, types.BaseTuple):
            raise_bodo_error(
                'Only tuple argument for pd.concat(axis=1) expected')
        index = (
            'bodo.hiframes.pd_index_ext.init_range_index(0, len(objs[0]), 1, None)'
            )
        bsra__rtbgz = 0
        galfd__qpjij = []
        names = []
        for i, mxtu__njcvv in enumerate(objs.types):
            assert isinstance(mxtu__njcvv, (SeriesType, DataFrameType))
            check_runtime_cols_unsupported(mxtu__njcvv, 'pandas.concat()')
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(
                mxtu__njcvv, 'pandas.concat()')
            if isinstance(mxtu__njcvv, SeriesType):
                names.append(str(bsra__rtbgz))
                bsra__rtbgz += 1
                galfd__qpjij.append(
                    'bodo.hiframes.pd_series_ext.get_series_data(objs[{}])'
                    .format(i))
            else:
                names.extend(mxtu__njcvv.columns)
                for wjj__xaah in range(len(mxtu__njcvv.data)):
                    galfd__qpjij.append(
                        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(objs[{}], {})'
                        .format(i, wjj__xaah))
        return bodo.hiframes.dataframe_impl._gen_init_df(iqkj__cxo, names,
            ', '.join(galfd__qpjij), index)
    if axis != 0:
        raise_bodo_error('pd.concat(): axis must be 0 or 1')
    if isinstance(objs, types.BaseTuple) and isinstance(objs.types[0],
        DataFrameType):
        assert all(isinstance(rgqji__lceb, DataFrameType) for rgqji__lceb in
            objs.types)
        qdu__ymulx = []
        for df in objs.types:
            check_runtime_cols_unsupported(df, 'pandas.concat()')
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
                'pandas.concat()')
            qdu__ymulx.extend(df.columns)
        qdu__ymulx = list(dict.fromkeys(qdu__ymulx).keys())
        gaes__wubmj = {}
        for bsra__rtbgz, yhx__kwv in enumerate(qdu__ymulx):
            for df in objs.types:
                if yhx__kwv in df.columns:
                    gaes__wubmj['arr_typ{}'.format(bsra__rtbgz)] = df.data[df
                        .columns.index(yhx__kwv)]
                    break
        assert len(gaes__wubmj) == len(qdu__ymulx)
        fbbd__hvzih = []
        for bsra__rtbgz, yhx__kwv in enumerate(qdu__ymulx):
            args = []
            for i, df in enumerate(objs.types):
                if yhx__kwv in df.columns:
                    mit__hyzgc = df.columns.index(yhx__kwv)
                    args.append(
                        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(objs[{}], {})'
                        .format(i, mit__hyzgc))
                else:
                    args.append(
                        'bodo.libs.array_kernels.gen_na_array(len(objs[{}]), arr_typ{})'
                        .format(i, bsra__rtbgz))
            iqkj__cxo += ('  A{} = bodo.libs.array_kernels.concat(({},))\n'
                .format(bsra__rtbgz, ', '.join(args)))
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
        return bodo.hiframes.dataframe_impl._gen_init_df(iqkj__cxo,
            qdu__ymulx, ', '.join('A{}'.format(i) for i in range(len(
            qdu__ymulx))), index, gaes__wubmj)
    if isinstance(objs, types.BaseTuple) and isinstance(objs.types[0],
        SeriesType):
        assert all(isinstance(rgqji__lceb, SeriesType) for rgqji__lceb in
            objs.types)
        iqkj__cxo += ('  out_arr = bodo.libs.array_kernels.concat(({},))\n'
            .format(', '.join(
            'bodo.hiframes.pd_series_ext.get_series_data(objs[{}])'.format(
            i) for i in range(len(objs.types)))))
        if ignore_index:
            iqkj__cxo += """  index = bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr), 1, None)
"""
        else:
            iqkj__cxo += (
                """  index = bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(({},)))
"""
                .format(', '.join(
                'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(objs[{}]))'
                .format(i) for i in range(len(objs.types)))))
        iqkj__cxo += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index)\n'
            )
        leo__uscw = {}
        exec(iqkj__cxo, {'bodo': bodo, 'np': np, 'numba': numba}, leo__uscw)
        return leo__uscw['impl']
    if isinstance(objs, types.List) and isinstance(objs.dtype, DataFrameType):
        check_runtime_cols_unsupported(objs.dtype, 'pandas.concat()')
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(objs.
            dtype, 'pandas.concat()')
        df_type = objs.dtype
        for bsra__rtbgz, yhx__kwv in enumerate(df_type.columns):
            iqkj__cxo += '  arrs{} = []\n'.format(bsra__rtbgz)
            iqkj__cxo += '  for i in range(len(objs)):\n'
            iqkj__cxo += '    df = objs[i]\n'
            iqkj__cxo += (
                """    arrs{0}.append(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0}))
"""
                .format(bsra__rtbgz))
            iqkj__cxo += (
                '  out_arr{0} = bodo.libs.array_kernels.concat(arrs{0})\n'.
                format(bsra__rtbgz))
        if ignore_index:
            index = (
                'bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr0), 1, None)'
                )
        else:
            iqkj__cxo += '  arrs_index = []\n'
            iqkj__cxo += '  for i in range(len(objs)):\n'
            iqkj__cxo += '    df = objs[i]\n'
            iqkj__cxo += """    arrs_index.append(bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)))
"""
            if objs.dtype.index.name_typ == types.none:
                name = None
            else:
                name = objs.dtype.index.name_typ.literal_value
            index = f"""bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(arrs_index), {name!r})
"""
        return bodo.hiframes.dataframe_impl._gen_init_df(iqkj__cxo, df_type
            .columns, ', '.join('out_arr{}'.format(i) for i in range(len(
            df_type.columns))), index)
    if isinstance(objs, types.List) and isinstance(objs.dtype, SeriesType):
        iqkj__cxo += '  arrs = []\n'
        iqkj__cxo += '  for i in range(len(objs)):\n'
        iqkj__cxo += (
            '    arrs.append(bodo.hiframes.pd_series_ext.get_series_data(objs[i]))\n'
            )
        iqkj__cxo += '  out_arr = bodo.libs.array_kernels.concat(arrs)\n'
        if ignore_index:
            iqkj__cxo += """  index = bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr), 1, None)
"""
        else:
            iqkj__cxo += '  arrs_index = []\n'
            iqkj__cxo += '  for i in range(len(objs)):\n'
            iqkj__cxo += '    S = objs[i]\n'
            iqkj__cxo += """    arrs_index.append(bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(S)))
"""
            iqkj__cxo += """  index = bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(arrs_index))
"""
        iqkj__cxo += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index)\n'
            )
        leo__uscw = {}
        exec(iqkj__cxo, {'bodo': bodo, 'np': np, 'numba': numba}, leo__uscw)
        return leo__uscw['impl']
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
        smy__ilgvz = df.copy(index=index, is_table_format=False)
        return signature(smy__ilgvz, *args)


SortDummyTyper._no_unliteral = True


@lower_builtin(sort_values_dummy, types.VarArg(types.Any))
def lower_sort_values_dummy(context, builder, sig, args):
    if sig.return_type == types.none:
        return
    siu__xaqyd = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return siu__xaqyd._getvalue()


@overload_method(DataFrameType, 'itertuples', inline='always', no_unliteral
    =True)
def itertuples_overload(df, index=True, name='Pandas'):
    check_runtime_cols_unsupported(df, 'DataFrame.itertuples()')
    yomkl__uos = dict(index=index, name=name)
    qyyrd__exh = dict(index=True, name='Pandas')
    check_unsupported_args('DataFrame.itertuples', yomkl__uos, qyyrd__exh,
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
        gaes__wubmj = (types.Array(types.int64, 1, 'C'),) + df.data
        zyj__wayw = bodo.hiframes.dataframe_impl.DataFrameTupleIterator(columns
            , gaes__wubmj)
        return signature(zyj__wayw, *args)


@lower_builtin(itertuples_dummy, types.VarArg(types.Any))
def lower_itertuples_dummy(context, builder, sig, args):
    siu__xaqyd = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return siu__xaqyd._getvalue()


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
    siu__xaqyd = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return siu__xaqyd._getvalue()


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
    siu__xaqyd = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return siu__xaqyd._getvalue()


@numba.generated_jit(nopython=True)
def pivot_impl(index_tup, columns_tup, values_tup, pivot_values,
    index_names, columns_name, value_names, check_duplicates=True, parallel
    =False):
    if not is_overload_constant_bool(check_duplicates):
        raise BodoError(
            'pivot_impl(): check_duplicates must be a constant boolean')
    jijqn__rqvi = get_overload_const_bool(check_duplicates)
    qnq__utxy = not is_overload_none(value_names)
    iffod__igfc = isinstance(values_tup, types.UniTuple)
    if iffod__igfc:
        atldf__kpwps = [to_nullable_type(values_tup.dtype)]
    else:
        atldf__kpwps = [to_nullable_type(qqc__xkvk) for qqc__xkvk in values_tup
            ]
    iqkj__cxo = 'def impl(\n'
    iqkj__cxo += """    index_tup, columns_tup, values_tup, pivot_values, index_names, columns_name, value_names, check_duplicates=True, parallel=False
"""
    iqkj__cxo += '):\n'
    iqkj__cxo += '    if parallel:\n'
    zcu__xegte = ', '.join([f'array_to_info(index_tup[{i}])' for i in range
        (len(index_tup))] + [f'array_to_info(columns_tup[{i}])' for i in
        range(len(columns_tup))] + [f'array_to_info(values_tup[{i}])' for i in
        range(len(values_tup))])
    iqkj__cxo += f'        info_list = [{zcu__xegte}]\n'
    iqkj__cxo += '        cpp_table = arr_info_list_to_table(info_list)\n'
    iqkj__cxo += f"""        out_cpp_table = shuffle_table(cpp_table, {len(index_tup)}, parallel, 0)
"""
    isyk__jxkuy = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i}), index_tup[{i}])'
         for i in range(len(index_tup))])
    lur__ykzpt = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i + len(index_tup)}), columns_tup[{i}])'
         for i in range(len(columns_tup))])
    dmemf__vrzmp = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i + len(index_tup) + len(columns_tup)}), values_tup[{i}])'
         for i in range(len(values_tup))])
    iqkj__cxo += f'        index_tup = ({isyk__jxkuy},)\n'
    iqkj__cxo += f'        columns_tup = ({lur__ykzpt},)\n'
    iqkj__cxo += f'        values_tup = ({dmemf__vrzmp},)\n'
    iqkj__cxo += '        delete_table(cpp_table)\n'
    iqkj__cxo += '        delete_table(out_cpp_table)\n'
    iqkj__cxo += '    columns_arr = columns_tup[0]\n'
    if iffod__igfc:
        iqkj__cxo += '    values_arrs = [arr for arr in values_tup]\n'
    iqkj__cxo += """    unique_index_arr_tup, row_vector = bodo.libs.array_ops.array_unique_vector_map(
"""
    iqkj__cxo += '        index_tup\n'
    iqkj__cxo += '    )\n'
    iqkj__cxo += '    n_rows = len(unique_index_arr_tup[0])\n'
    iqkj__cxo += '    num_values_arrays = len(values_tup)\n'
    iqkj__cxo += '    n_unique_pivots = len(pivot_values)\n'
    if iffod__igfc:
        iqkj__cxo += '    n_cols = num_values_arrays * n_unique_pivots\n'
    else:
        iqkj__cxo += '    n_cols = n_unique_pivots\n'
    iqkj__cxo += '    col_map = {}\n'
    iqkj__cxo += '    for i in range(n_unique_pivots):\n'
    iqkj__cxo += '        if bodo.libs.array_kernels.isna(pivot_values, i):\n'
    iqkj__cxo += '            raise ValueError(\n'
    iqkj__cxo += """                "DataFrame.pivot(): NA values in 'columns' array not supported\"
"""
    iqkj__cxo += '            )\n'
    iqkj__cxo += '        col_map[pivot_values[i]] = i\n'
    fudb__uwnf = False
    for i, pigb__thjn in enumerate(atldf__kpwps):
        if is_str_arr_type(pigb__thjn):
            fudb__uwnf = True
            iqkj__cxo += (
                f'    len_arrs_{i} = [np.zeros(n_rows, np.int64) for _ in range(n_cols)]\n'
                )
            iqkj__cxo += f'    total_lens_{i} = np.zeros(n_cols, np.int64)\n'
    if fudb__uwnf:
        if jijqn__rqvi:
            iqkj__cxo += '    nbytes = (n_rows + 7) >> 3\n'
            iqkj__cxo += """    seen_bitmaps = [np.zeros(nbytes, np.int8) for _ in range(n_unique_pivots)]
"""
        iqkj__cxo += '    for i in range(len(columns_arr)):\n'
        iqkj__cxo += '        col_name = columns_arr[i]\n'
        iqkj__cxo += '        pivot_idx = col_map[col_name]\n'
        iqkj__cxo += '        row_idx = row_vector[i]\n'
        if jijqn__rqvi:
            iqkj__cxo += '        seen_bitmap = seen_bitmaps[pivot_idx]\n'
            iqkj__cxo += """        if bodo.libs.int_arr_ext.get_bit_bitmap_arr(seen_bitmap, row_idx):
"""
            iqkj__cxo += """            raise ValueError("DataFrame.pivot(): 'index' contains duplicate entries for the same output column")
"""
            iqkj__cxo += '        else:\n'
            iqkj__cxo += """            bodo.libs.int_arr_ext.set_bit_to_arr(seen_bitmap, row_idx, 1)
"""
        if iffod__igfc:
            iqkj__cxo += '        for j in range(num_values_arrays):\n'
            iqkj__cxo += (
                '            col_idx = (j * len(pivot_values)) + pivot_idx\n')
            iqkj__cxo += '            len_arr = len_arrs_0[col_idx]\n'
            iqkj__cxo += '            values_arr = values_arrs[j]\n'
            iqkj__cxo += (
                '            if not bodo.libs.array_kernels.isna(values_arr, i):\n'
                )
            iqkj__cxo += (
                '                len_arr[row_idx] = len(values_arr[i])\n')
            iqkj__cxo += (
                '                total_lens_0[col_idx] += len(values_arr[i])\n'
                )
        else:
            for i, pigb__thjn in enumerate(atldf__kpwps):
                if is_str_arr_type(pigb__thjn):
                    iqkj__cxo += f"""        if not bodo.libs.array_kernels.isna(values_tup[{i}], i):
"""
                    iqkj__cxo += f"""            len_arrs_{i}[pivot_idx][row_idx] = len(values_tup[{i}][i])
"""
                    iqkj__cxo += f"""            total_lens_{i}[pivot_idx] += len(values_tup[{i}][i])
"""
    for i, pigb__thjn in enumerate(atldf__kpwps):
        if is_str_arr_type(pigb__thjn):
            iqkj__cxo += f'    data_arrs_{i} = [\n'
            iqkj__cxo += (
                '        bodo.libs.str_arr_ext.gen_na_str_array_lens(\n')
            iqkj__cxo += (
                f'            n_rows, total_lens_{i}[i], len_arrs_{i}[i]\n')
            iqkj__cxo += '        )\n'
            iqkj__cxo += '        for i in range(n_cols)\n'
            iqkj__cxo += '    ]\n'
        else:
            iqkj__cxo += f'    data_arrs_{i} = [\n'
            iqkj__cxo += (
                f'        bodo.libs.array_kernels.gen_na_array(n_rows, data_arr_typ_{i})\n'
                )
            iqkj__cxo += '        for _ in range(n_cols)\n'
            iqkj__cxo += '    ]\n'
    if not fudb__uwnf and jijqn__rqvi:
        iqkj__cxo += '    nbytes = (n_rows + 7) >> 3\n'
        iqkj__cxo += """    seen_bitmaps = [np.zeros(nbytes, np.int8) for _ in range(n_unique_pivots)]
"""
    iqkj__cxo += '    for i in range(len(columns_arr)):\n'
    iqkj__cxo += '        col_name = columns_arr[i]\n'
    iqkj__cxo += '        pivot_idx = col_map[col_name]\n'
    iqkj__cxo += '        row_idx = row_vector[i]\n'
    if not fudb__uwnf and jijqn__rqvi:
        iqkj__cxo += '        seen_bitmap = seen_bitmaps[pivot_idx]\n'
        iqkj__cxo += (
            '        if bodo.libs.int_arr_ext.get_bit_bitmap_arr(seen_bitmap, row_idx):\n'
            )
        iqkj__cxo += """            raise ValueError("DataFrame.pivot(): 'index' contains duplicate entries for the same output column")
"""
        iqkj__cxo += '        else:\n'
        iqkj__cxo += (
            '            bodo.libs.int_arr_ext.set_bit_to_arr(seen_bitmap, row_idx, 1)\n'
            )
    if iffod__igfc:
        iqkj__cxo += '        for j in range(num_values_arrays):\n'
        iqkj__cxo += (
            '            col_idx = (j * len(pivot_values)) + pivot_idx\n')
        iqkj__cxo += '            col_arr = data_arrs_0[col_idx]\n'
        iqkj__cxo += '            values_arr = values_arrs[j]\n'
        iqkj__cxo += (
            '            if bodo.libs.array_kernels.isna(values_arr, i):\n')
        iqkj__cxo += (
            '                bodo.libs.array_kernels.setna(col_arr, row_idx)\n'
            )
        iqkj__cxo += '            else:\n'
        iqkj__cxo += '                col_arr[row_idx] = values_arr[i]\n'
    else:
        for i, pigb__thjn in enumerate(atldf__kpwps):
            iqkj__cxo += f'        col_arr_{i} = data_arrs_{i}[pivot_idx]\n'
            iqkj__cxo += (
                f'        if bodo.libs.array_kernels.isna(values_tup[{i}], i):\n'
                )
            iqkj__cxo += (
                f'            bodo.libs.array_kernels.setna(col_arr_{i}, row_idx)\n'
                )
            iqkj__cxo += f'        else:\n'
            iqkj__cxo += (
                f'            col_arr_{i}[row_idx] = values_tup[{i}][i]\n')
    if len(index_tup) == 1:
        iqkj__cxo += """    index = bodo.utils.conversion.index_from_array(unique_index_arr_tup[0], index_names[0])
"""
    else:
        iqkj__cxo += """    index = bodo.hiframes.pd_multi_index_ext.init_multi_index(unique_index_arr_tup, index_names, None)
"""
    if qnq__utxy:
        iqkj__cxo += '    num_rows = len(value_names) * len(pivot_values)\n'
        if is_str_arr_type(value_names):
            iqkj__cxo += '    total_chars = 0\n'
            iqkj__cxo += '    for i in range(len(value_names)):\n'
            iqkj__cxo += '        total_chars += len(value_names[i])\n'
            iqkj__cxo += """    new_value_names = bodo.libs.str_arr_ext.pre_alloc_string_array(num_rows, total_chars * len(pivot_values))
"""
        else:
            iqkj__cxo += """    new_value_names = bodo.utils.utils.alloc_type(num_rows, value_names, (-1,))
"""
        if is_str_arr_type(pivot_values):
            iqkj__cxo += '    total_chars = 0\n'
            iqkj__cxo += '    for i in range(len(pivot_values)):\n'
            iqkj__cxo += '        total_chars += len(pivot_values[i])\n'
            iqkj__cxo += """    new_pivot_values = bodo.libs.str_arr_ext.pre_alloc_string_array(num_rows, total_chars * len(value_names))
"""
        else:
            iqkj__cxo += """    new_pivot_values = bodo.utils.utils.alloc_type(num_rows, pivot_values, (-1,))
"""
        iqkj__cxo += '    for i in range(len(value_names)):\n'
        iqkj__cxo += '        for j in range(len(pivot_values)):\n'
        iqkj__cxo += (
            '            new_value_names[(i * len(pivot_values)) + j] = value_names[i]\n'
            )
        iqkj__cxo += """            new_pivot_values[(i * len(pivot_values)) + j] = pivot_values[j]
"""
        iqkj__cxo += """    column_index = bodo.hiframes.pd_multi_index_ext.init_multi_index((new_value_names, new_pivot_values), (None, columns_name), None)
"""
    else:
        iqkj__cxo += """    column_index =  bodo.utils.conversion.index_from_array(pivot_values, columns_name)
"""
    kasso__kmb = ', '.join(f'data_arrs_{i}' for i in range(len(atldf__kpwps)))
    iqkj__cxo += f"""    table = bodo.hiframes.table.init_runtime_table_from_lists(({kasso__kmb},), n_rows)
"""
    iqkj__cxo += (
        '    return bodo.hiframes.pd_dataframe_ext.init_runtime_cols_dataframe(\n'
        )
    iqkj__cxo += '        (table,), index, column_index\n'
    iqkj__cxo += '    )\n'
    leo__uscw = {}
    ubp__oeyc = {f'data_arr_typ_{i}': pigb__thjn for i, pigb__thjn in
        enumerate(atldf__kpwps)}
    tduig__leplg = {'bodo': bodo, 'np': np, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'shuffle_table':
        shuffle_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'info_from_table': info_from_table, **ubp__oeyc}
    exec(iqkj__cxo, tduig__leplg, leo__uscw)
    impl = leo__uscw['impl']
    return impl


def gen_pandas_parquet_metadata(column_names, data_types, index,
    write_non_range_index_to_metadata, write_rangeindex_to_metadata,
    partition_cols=None, is_runtime_columns=False):
    rvm__acu = {}
    rvm__acu['columns'] = []
    if partition_cols is None:
        partition_cols = []
    for col_name, noi__pzn in zip(column_names, data_types):
        if col_name in partition_cols:
            continue
        hia__pzt = None
        if isinstance(noi__pzn, bodo.DatetimeArrayType):
            rgx__fena = 'datetimetz'
            ows__weeud = 'datetime64[ns]'
            if isinstance(noi__pzn.tz, int):
                opjde__vcoh = (bodo.libs.pd_datetime_arr_ext.
                    nanoseconds_to_offset(noi__pzn.tz))
            else:
                opjde__vcoh = pd.DatetimeTZDtype(tz=noi__pzn.tz).tz
            hia__pzt = {'timezone': pa.lib.tzinfo_to_string(opjde__vcoh)}
        elif isinstance(noi__pzn, types.Array) or noi__pzn == boolean_array:
            rgx__fena = ows__weeud = noi__pzn.dtype.name
            if ows__weeud.startswith('datetime'):
                rgx__fena = 'datetime'
        elif is_str_arr_type(noi__pzn):
            rgx__fena = 'unicode'
            ows__weeud = 'object'
        elif noi__pzn == binary_array_type:
            rgx__fena = 'bytes'
            ows__weeud = 'object'
        elif isinstance(noi__pzn, DecimalArrayType):
            rgx__fena = ows__weeud = 'object'
        elif isinstance(noi__pzn, IntegerArrayType):
            odp__ybxbc = noi__pzn.dtype.name
            if odp__ybxbc.startswith('int'):
                rgx__fena = 'Int' + odp__ybxbc[3:]
            elif odp__ybxbc.startswith('uint'):
                rgx__fena = 'UInt' + odp__ybxbc[4:]
            else:
                if is_runtime_columns:
                    col_name = 'Runtime determined column of type'
                raise BodoError(
                    'to_parquet(): unknown dtype in nullable Integer column {} {}'
                    .format(col_name, noi__pzn))
            ows__weeud = noi__pzn.dtype.name
        elif noi__pzn == datetime_date_array_type:
            rgx__fena = 'datetime'
            ows__weeud = 'object'
        elif isinstance(noi__pzn, (StructArrayType, ArrayItemArrayType)):
            rgx__fena = 'object'
            ows__weeud = 'object'
        else:
            if is_runtime_columns:
                col_name = 'Runtime determined column of type'
            raise BodoError(
                'to_parquet(): unsupported column type for metadata generation : {} {}'
                .format(col_name, noi__pzn))
        ubw__mdmyk = {'name': col_name, 'field_name': col_name,
            'pandas_type': rgx__fena, 'numpy_type': ows__weeud, 'metadata':
            hia__pzt}
        rvm__acu['columns'].append(ubw__mdmyk)
    if write_non_range_index_to_metadata:
        if isinstance(index, MultiIndexType):
            raise BodoError('to_parquet: MultiIndex not supported yet')
        if 'none' in index.name:
            fwcs__wwct = '__index_level_0__'
            osdzw__avy = None
        else:
            fwcs__wwct = '%s'
            osdzw__avy = '%s'
        rvm__acu['index_columns'] = [fwcs__wwct]
        rvm__acu['columns'].append({'name': osdzw__avy, 'field_name':
            fwcs__wwct, 'pandas_type': index.pandas_type_name, 'numpy_type':
            index.numpy_type_name, 'metadata': None})
    elif write_rangeindex_to_metadata:
        rvm__acu['index_columns'] = [{'kind': 'range', 'name': '%s',
            'start': '%d', 'stop': '%d', 'step': '%d'}]
    else:
        rvm__acu['index_columns'] = []
    rvm__acu['pandas_version'] = pd.__version__
    return rvm__acu


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
        jtds__kcnhp = []
        for jmbmf__tjx in partition_cols:
            try:
                idx = df.columns.index(jmbmf__tjx)
            except ValueError as ijs__lmihm:
                raise BodoError(
                    f'Partition column {jmbmf__tjx} is not in dataframe')
            jtds__kcnhp.append(idx)
    else:
        partition_cols = None
    if not is_overload_none(index) and not is_overload_constant_bool(index):
        raise BodoError('to_parquet(): index must be a constant bool or None')
    from bodo.io.parquet_pio import parquet_write_table_cpp, parquet_write_table_partitioned_cpp
    qeptr__qisac = isinstance(df.index, bodo.hiframes.pd_index_ext.
        RangeIndexType)
    dbfq__hbolv = df.index is not None and (is_overload_true(_is_parallel) or
        not is_overload_true(_is_parallel) and not qeptr__qisac)
    write_non_range_index_to_metadata = is_overload_true(index
        ) or is_overload_none(index) and (not qeptr__qisac or
        is_overload_true(_is_parallel))
    write_rangeindex_to_metadata = is_overload_none(index
        ) and qeptr__qisac and not is_overload_true(_is_parallel)
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
        koa__dlk = df.runtime_data_types
        mtn__nmge = len(koa__dlk)
        hia__pzt = gen_pandas_parquet_metadata([''] * mtn__nmge, koa__dlk,
            df.index, write_non_range_index_to_metadata,
            write_rangeindex_to_metadata, partition_cols=partition_cols,
            is_runtime_columns=True)
        gpmtm__stnp = hia__pzt['columns'][:mtn__nmge]
        hia__pzt['columns'] = hia__pzt['columns'][mtn__nmge:]
        gpmtm__stnp = [json.dumps(anfsa__bqb).replace('""', '{0}') for
            anfsa__bqb in gpmtm__stnp]
        rfpyl__lon = json.dumps(hia__pzt)
        tww__hqdl = '"columns": ['
        qvkwd__udjzh = rfpyl__lon.find(tww__hqdl)
        if qvkwd__udjzh == -1:
            raise BodoError(
                'DataFrame.to_parquet(): Unexpected metadata string for runtime columns.  Please return the DataFrame to regular Python to update typing information.'
                )
        tguhl__aogst = qvkwd__udjzh + len(tww__hqdl)
        dszy__rtiv = rfpyl__lon[:tguhl__aogst]
        rfpyl__lon = rfpyl__lon[tguhl__aogst:]
        xhy__sqxk = len(hia__pzt['columns'])
    else:
        rfpyl__lon = json.dumps(gen_pandas_parquet_metadata(df.columns, df.
            data, df.index, write_non_range_index_to_metadata,
            write_rangeindex_to_metadata, partition_cols=partition_cols,
            is_runtime_columns=False))
    if not is_overload_true(_is_parallel) and qeptr__qisac:
        rfpyl__lon = rfpyl__lon.replace('"%d"', '%d')
        if df.index.name == 'RangeIndexType(none)':
            rfpyl__lon = rfpyl__lon.replace('"%s"', '%s')
    if not df.is_table_format:
        galfd__qpjij = ', '.join(
            'array_to_info(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}))'
            .format(i) for i in range(len(df.columns)))
    iqkj__cxo = """def df_to_parquet(df, fname, engine='auto', compression='snappy', index=None, partition_cols=None, storage_options=None, _is_parallel=False):
"""
    if df.is_table_format:
        iqkj__cxo += '    py_table = get_dataframe_table(df)\n'
        iqkj__cxo += (
            '    table = py_table_to_cpp_table(py_table, py_table_typ)\n')
    else:
        iqkj__cxo += '    info_list = [{}]\n'.format(galfd__qpjij)
        iqkj__cxo += '    table = arr_info_list_to_table(info_list)\n'
    if df.has_runtime_cols:
        iqkj__cxo += '    columns_index = get_dataframe_column_names(df)\n'
        iqkj__cxo += '    names_arr = index_to_array(columns_index)\n'
        iqkj__cxo += '    col_names = array_to_info(names_arr)\n'
    else:
        iqkj__cxo += '    col_names = array_to_info(col_names_arr)\n'
    if is_overload_true(index) or is_overload_none(index) and dbfq__hbolv:
        iqkj__cxo += """    index_col = array_to_info(index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)))
"""
        fxgv__fmees = True
    else:
        iqkj__cxo += '    index_col = array_to_info(np.empty(0))\n'
        fxgv__fmees = False
    if df.has_runtime_cols:
        iqkj__cxo += '    columns_lst = []\n'
        iqkj__cxo += '    num_cols = 0\n'
        for i in range(len(df.runtime_data_types)):
            iqkj__cxo += f'    for _ in range(len(py_table.block_{i})):\n'
            iqkj__cxo += f"""        columns_lst.append({gpmtm__stnp[i]!r}.replace('{{0}}', '"' + names_arr[num_cols] + '"'))
"""
            iqkj__cxo += '        num_cols += 1\n'
        if xhy__sqxk:
            iqkj__cxo += "    columns_lst.append('')\n"
        iqkj__cxo += '    columns_str = ", ".join(columns_lst)\n'
        iqkj__cxo += ('    metadata = """' + dszy__rtiv +
            '""" + columns_str + """' + rfpyl__lon + '"""\n')
    else:
        iqkj__cxo += '    metadata = """' + rfpyl__lon + '"""\n'
    iqkj__cxo += '    if compression is None:\n'
    iqkj__cxo += "        compression = 'none'\n"
    iqkj__cxo += '    if df.index.name is not None:\n'
    iqkj__cxo += '        name_ptr = df.index.name\n'
    iqkj__cxo += '    else:\n'
    iqkj__cxo += "        name_ptr = 'null'\n"
    iqkj__cxo += f"""    bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel=_is_parallel)
"""
    ywco__dvhtw = None
    if partition_cols:
        ywco__dvhtw = pd.array([col_name for col_name in df.columns if 
            col_name not in partition_cols])
        yymm__cky = ', '.join(
            f'array_to_info(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).dtype.categories.values)'
             for i in range(len(df.columns)) if isinstance(df.data[i],
            CategoricalArrayType) and i in jtds__kcnhp)
        if yymm__cky:
            iqkj__cxo += '    cat_info_list = [{}]\n'.format(yymm__cky)
            iqkj__cxo += (
                '    cat_table = arr_info_list_to_table(cat_info_list)\n')
        else:
            iqkj__cxo += '    cat_table = table\n'
        iqkj__cxo += (
            '    col_names_no_partitions = array_to_info(col_names_no_parts_arr)\n'
            )
        iqkj__cxo += (
            f'    part_cols_idxs = np.array({jtds__kcnhp}, dtype=np.int32)\n')
        iqkj__cxo += (
            '    parquet_write_table_partitioned_cpp(unicode_to_utf8(fname),\n'
            )
        iqkj__cxo += """                            table, col_names, col_names_no_partitions, cat_table,
"""
        iqkj__cxo += (
            '                            part_cols_idxs.ctypes, len(part_cols_idxs),\n'
            )
        iqkj__cxo += (
            '                            unicode_to_utf8(compression),\n')
        iqkj__cxo += '                            _is_parallel,\n'
        iqkj__cxo += (
            '                            unicode_to_utf8(bucket_region))\n')
        iqkj__cxo += '    delete_table_decref_arrays(table)\n'
        iqkj__cxo += '    delete_info_decref_array(index_col)\n'
        iqkj__cxo += '    delete_info_decref_array(col_names_no_partitions)\n'
        iqkj__cxo += '    delete_info_decref_array(col_names)\n'
        if yymm__cky:
            iqkj__cxo += '    delete_table_decref_arrays(cat_table)\n'
    elif write_rangeindex_to_metadata:
        iqkj__cxo += '    parquet_write_table_cpp(unicode_to_utf8(fname),\n'
        iqkj__cxo += (
            '                            table, col_names, index_col,\n')
        iqkj__cxo += '                            ' + str(fxgv__fmees) + ',\n'
        iqkj__cxo += '                            unicode_to_utf8(metadata),\n'
        iqkj__cxo += (
            '                            unicode_to_utf8(compression),\n')
        iqkj__cxo += (
            '                            _is_parallel, 1, df.index.start,\n')
        iqkj__cxo += (
            '                            df.index.stop, df.index.step,\n')
        iqkj__cxo += '                            unicode_to_utf8(name_ptr),\n'
        iqkj__cxo += (
            '                            unicode_to_utf8(bucket_region))\n')
        iqkj__cxo += '    delete_table_decref_arrays(table)\n'
        iqkj__cxo += '    delete_info_decref_array(index_col)\n'
        iqkj__cxo += '    delete_info_decref_array(col_names)\n'
    else:
        iqkj__cxo += '    parquet_write_table_cpp(unicode_to_utf8(fname),\n'
        iqkj__cxo += (
            '                            table, col_names, index_col,\n')
        iqkj__cxo += '                            ' + str(fxgv__fmees) + ',\n'
        iqkj__cxo += '                            unicode_to_utf8(metadata),\n'
        iqkj__cxo += (
            '                            unicode_to_utf8(compression),\n')
        iqkj__cxo += '                            _is_parallel, 0, 0, 0, 0,\n'
        iqkj__cxo += '                            unicode_to_utf8(name_ptr),\n'
        iqkj__cxo += (
            '                            unicode_to_utf8(bucket_region))\n')
        iqkj__cxo += '    delete_table_decref_arrays(table)\n'
        iqkj__cxo += '    delete_info_decref_array(index_col)\n'
        iqkj__cxo += '    delete_info_decref_array(col_names)\n'
    leo__uscw = {}
    if df.has_runtime_cols:
        kry__syah = None
    else:
        for bftle__fyalp in df.columns:
            if not isinstance(bftle__fyalp, str):
                raise BodoError(
                    'DataFrame.to_parquet(): parquet must have string column names'
                    )
        kry__syah = pd.array(df.columns)
    exec(iqkj__cxo, {'np': np, 'bodo': bodo, 'unicode_to_utf8':
        unicode_to_utf8, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table,
        'str_arr_from_sequence': str_arr_from_sequence,
        'parquet_write_table_cpp': parquet_write_table_cpp,
        'parquet_write_table_partitioned_cpp':
        parquet_write_table_partitioned_cpp, 'index_to_array':
        index_to_array, 'delete_info_decref_array':
        delete_info_decref_array, 'delete_table_decref_arrays':
        delete_table_decref_arrays, 'col_names_arr': kry__syah,
        'py_table_to_cpp_table': py_table_to_cpp_table, 'py_table_typ': df.
        table_type, 'get_dataframe_table': get_dataframe_table,
        'col_names_no_parts_arr': ywco__dvhtw, 'get_dataframe_column_names':
        get_dataframe_column_names, 'fix_arr_dtype': fix_arr_dtype,
        'decode_if_dict_array': decode_if_dict_array,
        'decode_if_dict_table': decode_if_dict_table}, leo__uscw)
    dktt__nsjl = leo__uscw['df_to_parquet']
    return dktt__nsjl


def to_sql_exception_guard(df, name, con, schema=None, if_exists='fail',
    index=True, index_label=None, chunksize=None, dtype=None, method=None,
    _is_table_create=False, _is_parallel=False):
    mhvcx__ufgwo = 'all_ok'
    ennfa__gunr = urlparse(con).scheme
    if _is_parallel and bodo.get_rank() == 0:
        wpcal__oij = 100
        if chunksize is None:
            yuv__aaj = wpcal__oij
        else:
            yuv__aaj = min(chunksize, wpcal__oij)
        if _is_table_create:
            df = df.iloc[:yuv__aaj, :]
        else:
            df = df.iloc[yuv__aaj:, :]
            if len(df) == 0:
                return mhvcx__ufgwo
    if ennfa__gunr == 'snowflake':
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
            df.columns = [(yhx__kwv.upper() if yhx__kwv.islower() else
                yhx__kwv) for yhx__kwv in df.columns]
        except ImportError as ijs__lmihm:
            mhvcx__ufgwo = (
                "Snowflake Python connector packages not found. Using 'to_sql' with Snowflake requires both snowflake-sqlalchemy and snowflake-connector-python. These can be installed by calling 'conda install -c conda-forge snowflake-sqlalchemy snowflake-connector-python' or 'pip install snowflake-sqlalchemy snowflake-connector-python'."
                )
            return mhvcx__ufgwo
    try:
        df.to_sql(name, con, schema, if_exists, index, index_label,
            chunksize, dtype, method)
    except Exception as tnxo__oowg:
        mhvcx__ufgwo = tnxo__oowg.args[0]
    return mhvcx__ufgwo


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
        nef__kkw = bodo.libs.distributed_api.get_rank()
        mhvcx__ufgwo = 'unset'
        if nef__kkw != 0:
            mhvcx__ufgwo = bcast_scalar(mhvcx__ufgwo)
        elif nef__kkw == 0:
            mhvcx__ufgwo = to_sql_exception_guard_encaps(df, name, con,
                schema, if_exists, index, index_label, chunksize, dtype,
                method, True, _is_parallel)
            mhvcx__ufgwo = bcast_scalar(mhvcx__ufgwo)
        if_exists = 'append'
        if _is_parallel and mhvcx__ufgwo == 'all_ok':
            mhvcx__ufgwo = to_sql_exception_guard_encaps(df, name, con,
                schema, if_exists, index, index_label, chunksize, dtype,
                method, False, _is_parallel)
        if mhvcx__ufgwo != 'all_ok':
            print('err_msg=', mhvcx__ufgwo)
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
        kxokk__yzjfm = get_overload_const_str(path_or_buf)
        if kxokk__yzjfm.endswith(('.gz', '.bz2', '.zip', '.xz')):
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
        nwzn__baz = bodo.io.fs_io.get_s3_bucket_region_njit(path_or_buf,
            parallel=False)
        if lines and orient == 'records':
            bodo.hiframes.pd_dataframe_ext._json_write(unicode_to_utf8(
                path_or_buf), unicode_to_utf8(D), 0, len(D), False, True,
                unicode_to_utf8(nwzn__baz))
            bodo.utils.utils.check_and_propagate_cpp_exception()
        else:
            bodo.hiframes.pd_dataframe_ext._json_write(unicode_to_utf8(
                path_or_buf), unicode_to_utf8(D), 0, len(D), False, False,
                unicode_to_utf8(nwzn__baz))
            bodo.utils.utils.check_and_propagate_cpp_exception()
    return _impl


@overload(pd.get_dummies, inline='always', no_unliteral=True)
def get_dummies(data, prefix=None, prefix_sep='_', dummy_na=False, columns=
    None, sparse=False, drop_first=False, dtype=None):
    daldj__zistv = {'prefix': prefix, 'prefix_sep': prefix_sep, 'dummy_na':
        dummy_na, 'columns': columns, 'sparse': sparse, 'drop_first':
        drop_first, 'dtype': dtype}
    vrjqo__vqd = {'prefix': None, 'prefix_sep': '_', 'dummy_na': False,
        'columns': None, 'sparse': False, 'drop_first': False, 'dtype': None}
    check_unsupported_args('pandas.get_dummies', daldj__zistv, vrjqo__vqd,
        package_name='pandas', module_name='General')
    if not categorical_can_construct_dataframe(data):
        raise BodoError(
            'pandas.get_dummies() only support categorical data types with explicitly known categories'
            )
    iqkj__cxo = """def impl(data, prefix=None, prefix_sep='_', dummy_na=False, columns=None, sparse=False, drop_first=False, dtype=None,):
"""
    if isinstance(data, SeriesType):
        oxqc__almov = data.data.dtype.categories
        iqkj__cxo += (
            '  data_values = bodo.hiframes.pd_series_ext.get_series_data(data)\n'
            )
    else:
        oxqc__almov = data.dtype.categories
        iqkj__cxo += '  data_values = data\n'
    xou__mhnu = len(oxqc__almov)
    iqkj__cxo += """  codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(data_values)
"""
    iqkj__cxo += '  numba.parfors.parfor.init_prange()\n'
    iqkj__cxo += '  n = len(data_values)\n'
    for i in range(xou__mhnu):
        iqkj__cxo += '  data_arr_{} = np.empty(n, np.uint8)\n'.format(i)
    iqkj__cxo += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    iqkj__cxo += '      if bodo.libs.array_kernels.isna(data_values, i):\n'
    for wjj__xaah in range(xou__mhnu):
        iqkj__cxo += '          data_arr_{}[i] = 0\n'.format(wjj__xaah)
    iqkj__cxo += '      else:\n'
    for dkks__wxwaj in range(xou__mhnu):
        iqkj__cxo += '          data_arr_{0}[i] = codes[i] == {0}\n'.format(
            dkks__wxwaj)
    galfd__qpjij = ', '.join(f'data_arr_{i}' for i in range(xou__mhnu))
    index = 'bodo.hiframes.pd_index_ext.init_range_index(0, n, 1, None)'
    if isinstance(oxqc__almov[0], np.datetime64):
        oxqc__almov = tuple(pd.Timestamp(yhx__kwv) for yhx__kwv in oxqc__almov)
    elif isinstance(oxqc__almov[0], np.timedelta64):
        oxqc__almov = tuple(pd.Timedelta(yhx__kwv) for yhx__kwv in oxqc__almov)
    return bodo.hiframes.dataframe_impl._gen_init_df(iqkj__cxo, oxqc__almov,
        galfd__qpjij, index)


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
    for nscfi__ghco in pd_unsupported:
        fname = mod_name + '.' + nscfi__ghco.__name__
        overload(nscfi__ghco, no_unliteral=True)(create_unsupported_overload
            (fname))


def _install_dataframe_unsupported():
    for mzgyv__oiq in dataframe_unsupported_attrs:
        evtc__lubz = 'DataFrame.' + mzgyv__oiq
        overload_attribute(DataFrameType, mzgyv__oiq)(
            create_unsupported_overload(evtc__lubz))
    for fname in dataframe_unsupported:
        evtc__lubz = 'DataFrame.' + fname + '()'
        overload_method(DataFrameType, fname)(create_unsupported_overload(
            evtc__lubz))


_install_pd_unsupported('pandas', pd_unsupported)
_install_pd_unsupported('pandas.util', pd_util_unsupported)
_install_dataframe_unsupported()
