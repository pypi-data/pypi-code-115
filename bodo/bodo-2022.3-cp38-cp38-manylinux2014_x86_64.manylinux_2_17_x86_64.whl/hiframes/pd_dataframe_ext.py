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
            oyr__zggpk = f'{len(self.data)} columns of types {set(self.data)}'
            ogw__otm = (
                f"('{self.columns[0]}', '{self.columns[1]}', ..., '{self.columns[-1]}')"
                )
            return (
                f'dataframe({oyr__zggpk}, {self.index}, {ogw__otm}, {self.dist}, {self.is_table_format})'
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
            qshy__gtgl = (self.index if self.index == other.index else self
                .index.unify(typingctx, other.index))
            data = tuple(ojy__jnz.unify(typingctx, vie__undh) if ojy__jnz !=
                vie__undh else ojy__jnz for ojy__jnz, vie__undh in zip(self
                .data, other.data))
            dist = Distribution(min(self.dist.value, other.dist.value))
            if qshy__gtgl is not None and None not in data:
                return DataFrameType(data, qshy__gtgl, self.columns, dist,
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
        return all(ojy__jnz.is_precise() for ojy__jnz in self.data
            ) and self.index.is_precise()

    def replace_col_type(self, col_name, new_type):
        if col_name not in self.columns:
            raise ValueError(
                f"DataFrameType.replace_col_type replaced column must be found in the DataFrameType. '{col_name}' not found in DataFrameType with columns {self.columns}"
                )
        qdsg__dwlab = self.columns.index(col_name)
        qzkdo__iqqs = tuple(list(self.data[:qdsg__dwlab]) + [new_type] +
            list(self.data[qdsg__dwlab + 1:]))
        return DataFrameType(qzkdo__iqqs, self.index, self.columns, self.
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
        rfem__dvt = [('data', data_typ), ('index', fe_type.df_type.index),
            ('parent', types.pyobject)]
        if fe_type.df_type.has_runtime_cols:
            rfem__dvt.append(('columns', fe_type.df_type.runtime_colname_typ))
        super(DataFramePayloadModel, self).__init__(dmm, fe_type, rfem__dvt)


@register_model(DataFrameType)
class DataFrameModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = DataFramePayloadType(fe_type)
        rfem__dvt = [('meminfo', types.MemInfoPointer(payload_type)), (
            'parent', types.pyobject)]
        super(DataFrameModel, self).__init__(dmm, fe_type, rfem__dvt)


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
        eejpl__omxc = 'n',
        qcsdd__jug = {'n': 5}
        kqnex__hrnp, dcq__foxvn = bodo.utils.typing.fold_typing_args(func_name,
            args, kws, eejpl__omxc, qcsdd__jug)
        dpdt__umbl = dcq__foxvn[0]
        if not is_overload_int(dpdt__umbl):
            raise BodoError(f"{func_name}(): 'n' must be an Integer")
        ickx__xgosv = df.copy(is_table_format=False)
        return ickx__xgosv(*dcq__foxvn).replace(pysig=kqnex__hrnp)

    @bound_function('df.corr')
    def resolve_corr(self, df, args, kws):
        func_name = 'DataFrame.corr'
        check_runtime_cols_unsupported(df, f'{func_name}()')
        wbsnt__iyo = (df,) + args
        eejpl__omxc = 'df', 'method', 'min_periods'
        qcsdd__jug = {'method': 'pearson', 'min_periods': 1}
        wdwk__uem = 'method',
        kqnex__hrnp, dcq__foxvn = bodo.utils.typing.fold_typing_args(func_name,
            wbsnt__iyo, kws, eejpl__omxc, qcsdd__jug, wdwk__uem)
        qto__mhojy = dcq__foxvn[2]
        if not is_overload_int(qto__mhojy):
            raise BodoError(f"{func_name}(): 'min_periods' must be an Integer")
        iail__jnaep = []
        feobi__kfe = []
        for fss__fls, kfeuq__quk in zip(df.columns, df.data):
            if bodo.utils.typing._is_pandas_numeric_dtype(kfeuq__quk.dtype):
                iail__jnaep.append(fss__fls)
                feobi__kfe.append(types.Array(types.float64, 1, 'A'))
        if len(iail__jnaep) == 0:
            raise_bodo_error('DataFrame.corr(): requires non-empty dataframe')
        feobi__kfe = tuple(feobi__kfe)
        iail__jnaep = tuple(iail__jnaep)
        index_typ = bodo.utils.typing.type_col_to_index(iail__jnaep)
        ickx__xgosv = DataFrameType(feobi__kfe, index_typ, iail__jnaep)
        return ickx__xgosv(*dcq__foxvn).replace(pysig=kqnex__hrnp)

    @bound_function('df.pipe', no_unliteral=True)
    def resolve_pipe(self, df, args, kws):
        check_runtime_cols_unsupported(df, 'DataFrame.pipe()')
        return bodo.hiframes.pd_groupby_ext.resolve_obj_pipe(self, df, args,
            kws, 'DataFrame')

    @bound_function('df.apply', no_unliteral=True)
    def resolve_apply(self, df, args, kws):
        check_runtime_cols_unsupported(df, 'DataFrame.apply()')
        kws = dict(kws)
        cqlmi__eamuo = args[0] if len(args) > 0 else kws.pop('func', None)
        axis = args[1] if len(args) > 1 else kws.pop('axis', types.literal(0))
        ofisq__kmcgl = args[2] if len(args) > 2 else kws.pop('raw', types.
            literal(False))
        nzt__fjmy = args[3] if len(args) > 3 else kws.pop('result_type',
            types.none)
        cko__wmehw = args[4] if len(args) > 4 else kws.pop('args', types.
            Tuple([]))
        qrmqv__kvh = dict(raw=ofisq__kmcgl, result_type=nzt__fjmy)
        uqoky__zbv = dict(raw=False, result_type=None)
        check_unsupported_args('Dataframe.apply', qrmqv__kvh, uqoky__zbv,
            package_name='pandas', module_name='DataFrame')
        rec__yaax = True
        if types.unliteral(cqlmi__eamuo) == types.unicode_type:
            if not is_overload_constant_str(cqlmi__eamuo):
                raise BodoError(
                    f'DataFrame.apply(): string argument (for builtins) must be a compile time constant'
                    )
            rec__yaax = False
        if not is_overload_constant_int(axis):
            raise BodoError(
                'Dataframe.apply(): axis argument must be a compile time constant.'
                )
        ntt__cmf = get_overload_const_int(axis)
        if rec__yaax and ntt__cmf != 1:
            raise BodoError(
                'Dataframe.apply(): only axis=1 supported for user-defined functions'
                )
        elif ntt__cmf not in (0, 1):
            raise BodoError('Dataframe.apply(): axis must be either 0 or 1')
        cdrdf__tiwb = []
        for arr_typ in df.data:
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(arr_typ,
                'DataFrame.apply()')
            etjk__bkdl = SeriesType(arr_typ.dtype, arr_typ, df.index,
                string_type)
            dsp__kbnj = self.context.resolve_function_type(operator.getitem,
                (SeriesIlocType(etjk__bkdl), types.int64), {}).return_type
            cdrdf__tiwb.append(dsp__kbnj)
        lzbu__whicp = types.none
        cqo__zcgkw = HeterogeneousIndexType(types.BaseTuple.from_types(
            tuple(types.literal(fss__fls) for fss__fls in df.columns)), None)
        kehv__eyxg = types.BaseTuple.from_types(cdrdf__tiwb)
        vaqhg__mloug = df.index.dtype
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df.index,
            'DataFrame.apply()')
        if vaqhg__mloug == types.NPDatetime('ns'):
            vaqhg__mloug = bodo.pd_timestamp_type
        if vaqhg__mloug == types.NPTimedelta('ns'):
            vaqhg__mloug = bodo.pd_timedelta_type
        if is_heterogeneous_tuple_type(kehv__eyxg):
            zxap__owe = HeterogeneousSeriesType(kehv__eyxg, cqo__zcgkw,
                vaqhg__mloug)
        else:
            zxap__owe = SeriesType(kehv__eyxg.dtype, kehv__eyxg, cqo__zcgkw,
                vaqhg__mloug)
        xrso__wkswx = zxap__owe,
        if cko__wmehw is not None:
            xrso__wkswx += tuple(cko__wmehw.types)
        try:
            if not rec__yaax:
                lfh__xclnd = bodo.utils.transform.get_udf_str_return_type(df,
                    get_overload_const_str(cqlmi__eamuo), self.context,
                    'DataFrame.apply', axis if ntt__cmf == 1 else None)
            else:
                lfh__xclnd = get_const_func_output_type(cqlmi__eamuo,
                    xrso__wkswx, kws, self.context, numba.core.registry.
                    cpu_target.target_context)
        except Exception as vxmz__hxad:
            raise_bodo_error(get_udf_error_msg('DataFrame.apply()', vxmz__hxad)
                )
        if rec__yaax:
            if not (is_overload_constant_int(axis) and 
                get_overload_const_int(axis) == 1):
                raise BodoError(
                    'Dataframe.apply(): only user-defined functions with axis=1 supported'
                    )
            if isinstance(lfh__xclnd, (SeriesType, HeterogeneousSeriesType)
                ) and lfh__xclnd.const_info is None:
                raise BodoError(
                    'Invalid Series output in UDF (Series with constant length and constant Index value expected)'
                    )
            if isinstance(lfh__xclnd, HeterogeneousSeriesType):
                zvkzz__bkzgb, jbt__kskaz = lfh__xclnd.const_info
                hpb__eefhh = tuple(dtype_to_array_type(cckrg__itgcc) for
                    cckrg__itgcc in lfh__xclnd.data.types)
                sixf__leqso = DataFrameType(hpb__eefhh, df.index, jbt__kskaz)
            elif isinstance(lfh__xclnd, SeriesType):
                gzkxu__mqt, jbt__kskaz = lfh__xclnd.const_info
                hpb__eefhh = tuple(dtype_to_array_type(lfh__xclnd.dtype) for
                    zvkzz__bkzgb in range(gzkxu__mqt))
                sixf__leqso = DataFrameType(hpb__eefhh, df.index, jbt__kskaz)
            else:
                uubce__wlxnw = get_udf_out_arr_type(lfh__xclnd)
                sixf__leqso = SeriesType(uubce__wlxnw.dtype, uubce__wlxnw,
                    df.index, None)
        else:
            sixf__leqso = lfh__xclnd
        try__zjy = ', '.join("{} = ''".format(ojy__jnz) for ojy__jnz in kws
            .keys())
        hegu__ztmzk = f"""def apply_stub(func, axis=0, raw=False, result_type=None, args=(), {try__zjy}):
"""
        hegu__ztmzk += '    pass\n'
        pok__oow = {}
        exec(hegu__ztmzk, {}, pok__oow)
        clw__tktff = pok__oow['apply_stub']
        kqnex__hrnp = numba.core.utils.pysignature(clw__tktff)
        fddo__zzzga = (cqlmi__eamuo, axis, ofisq__kmcgl, nzt__fjmy, cko__wmehw
            ) + tuple(kws.values())
        return signature(sixf__leqso, *fddo__zzzga).replace(pysig=kqnex__hrnp)

    @bound_function('df.plot', no_unliteral=True)
    def resolve_plot(self, df, args, kws):
        func_name = 'DataFrame.plot'
        check_runtime_cols_unsupported(df, f'{func_name}()')
        eejpl__omxc = ('x', 'y', 'kind', 'figsize', 'ax', 'subplots',
            'sharex', 'sharey', 'layout', 'use_index', 'title', 'grid',
            'legend', 'style', 'logx', 'logy', 'loglog', 'xticks', 'yticks',
            'xlim', 'ylim', 'rot', 'fontsize', 'colormap', 'table', 'yerr',
            'xerr', 'secondary_y', 'sort_columns', 'xlabel', 'ylabel',
            'position', 'stacked', 'mark_right', 'include_bool', 'backend')
        qcsdd__jug = {'x': None, 'y': None, 'kind': 'line', 'figsize': None,
            'ax': None, 'subplots': False, 'sharex': None, 'sharey': False,
            'layout': None, 'use_index': True, 'title': None, 'grid': None,
            'legend': True, 'style': None, 'logx': False, 'logy': False,
            'loglog': False, 'xticks': None, 'yticks': None, 'xlim': None,
            'ylim': None, 'rot': None, 'fontsize': None, 'colormap': None,
            'table': False, 'yerr': None, 'xerr': None, 'secondary_y': 
            False, 'sort_columns': False, 'xlabel': None, 'ylabel': None,
            'position': 0.5, 'stacked': False, 'mark_right': True,
            'include_bool': False, 'backend': None}
        wdwk__uem = ('subplots', 'sharex', 'sharey', 'layout', 'use_index',
            'grid', 'style', 'logx', 'logy', 'loglog', 'xlim', 'ylim',
            'rot', 'colormap', 'table', 'yerr', 'xerr', 'sort_columns',
            'secondary_y', 'colorbar', 'position', 'stacked', 'mark_right',
            'include_bool', 'backend')
        kqnex__hrnp, dcq__foxvn = bodo.utils.typing.fold_typing_args(func_name,
            args, kws, eejpl__omxc, qcsdd__jug, wdwk__uem)
        lyemk__gcohh = dcq__foxvn[2]
        if not is_overload_constant_str(lyemk__gcohh):
            raise BodoError(
                f"{func_name}: kind must be a constant string and one of ('line', 'scatter')."
                )
        ski__lvaw = dcq__foxvn[0]
        if not is_overload_none(ski__lvaw) and not (is_overload_int(
            ski__lvaw) or is_overload_constant_str(ski__lvaw)):
            raise BodoError(
                f'{func_name}: x must be a constant column name, constant integer, or None.'
                )
        if is_overload_constant_str(ski__lvaw):
            fzbtz__nllg = get_overload_const_str(ski__lvaw)
            if fzbtz__nllg not in df.columns:
                raise BodoError(f'{func_name}: {fzbtz__nllg} column not found.'
                    )
        elif is_overload_int(ski__lvaw):
            khqo__bivug = get_overload_const_int(ski__lvaw)
            if khqo__bivug > len(df.columns):
                raise BodoError(
                    f'{func_name}: x: {khqo__bivug} is out of bounds for axis 0 with size {len(df.columns)}'
                    )
            ski__lvaw = df.columns[ski__lvaw]
        nzpkm__tfgu = dcq__foxvn[1]
        if not is_overload_none(nzpkm__tfgu) and not (is_overload_int(
            nzpkm__tfgu) or is_overload_constant_str(nzpkm__tfgu)):
            raise BodoError(
                'df.plot(): y must be a constant column name, constant integer, or None.'
                )
        if is_overload_constant_str(nzpkm__tfgu):
            rvbx__vumxi = get_overload_const_str(nzpkm__tfgu)
            if rvbx__vumxi not in df.columns:
                raise BodoError(f'{func_name}: {rvbx__vumxi} column not found.'
                    )
        elif is_overload_int(nzpkm__tfgu):
            ufz__bjcwn = get_overload_const_int(nzpkm__tfgu)
            if ufz__bjcwn > len(df.columns):
                raise BodoError(
                    f'{func_name}: y: {ufz__bjcwn} is out of bounds for axis 0 with size {len(df.columns)}'
                    )
            nzpkm__tfgu = df.columns[nzpkm__tfgu]
        phk__hxkyb = dcq__foxvn[3]
        if not is_overload_none(phk__hxkyb) and not is_tuple_like_type(
            phk__hxkyb):
            raise BodoError(
                f'{func_name}: figsize must be a constant numeric tuple (width, height) or None.'
                )
        gzed__jcna = dcq__foxvn[10]
        if not is_overload_none(gzed__jcna) and not is_overload_constant_str(
            gzed__jcna):
            raise BodoError(
                f'{func_name}: title must be a constant string or None.')
        awurr__pbmvw = dcq__foxvn[12]
        if not is_overload_bool(awurr__pbmvw):
            raise BodoError(f'{func_name}: legend must be a boolean type.')
        osd__cfhul = dcq__foxvn[17]
        if not is_overload_none(osd__cfhul) and not is_tuple_like_type(
            osd__cfhul):
            raise BodoError(
                f'{func_name}: xticks must be a constant tuple or None.')
        dzfi__rru = dcq__foxvn[18]
        if not is_overload_none(dzfi__rru) and not is_tuple_like_type(dzfi__rru
            ):
            raise BodoError(
                f'{func_name}: yticks must be a constant tuple or None.')
        amf__zxur = dcq__foxvn[22]
        if not is_overload_none(amf__zxur) and not is_overload_int(amf__zxur):
            raise BodoError(
                f'{func_name}: fontsize must be an integer or None.')
        yvqh__wwq = dcq__foxvn[29]
        if not is_overload_none(yvqh__wwq) and not is_overload_constant_str(
            yvqh__wwq):
            raise BodoError(
                f'{func_name}: xlabel must be a constant string or None.')
        rauiz__wvgxg = dcq__foxvn[30]
        if not is_overload_none(rauiz__wvgxg) and not is_overload_constant_str(
            rauiz__wvgxg):
            raise BodoError(
                f'{func_name}: ylabel must be a constant string or None.')
        bwyp__pfaoa = types.List(types.mpl_line_2d_type)
        lyemk__gcohh = get_overload_const_str(lyemk__gcohh)
        if lyemk__gcohh == 'scatter':
            if is_overload_none(ski__lvaw) and is_overload_none(nzpkm__tfgu):
                raise BodoError(
                    f'{func_name}: {lyemk__gcohh} requires an x and y column.')
            elif is_overload_none(ski__lvaw):
                raise BodoError(
                    f'{func_name}: {lyemk__gcohh} x column is missing.')
            elif is_overload_none(nzpkm__tfgu):
                raise BodoError(
                    f'{func_name}: {lyemk__gcohh} y column is missing.')
            bwyp__pfaoa = types.mpl_path_collection_type
        elif lyemk__gcohh != 'line':
            raise BodoError(
                f'{func_name}: {lyemk__gcohh} plot is not supported.')
        return signature(bwyp__pfaoa, *dcq__foxvn).replace(pysig=kqnex__hrnp)

    def generic_resolve(self, df, attr):
        if self._is_existing_attr(attr):
            return
        check_runtime_cols_unsupported(df,
            'Acessing DataFrame columns by attribute')
        if attr in df.columns:
            yik__dhqh = df.columns.index(attr)
            arr_typ = df.data[yik__dhqh]
            return SeriesType(arr_typ.dtype, arr_typ, df.index, types.
                StringLiteral(attr))
        if len(df.columns) > 0 and isinstance(df.columns[0], tuple):
            oji__bdol = []
            qzkdo__iqqs = []
            honoa__twune = False
            for i, qigx__hadz in enumerate(df.columns):
                if qigx__hadz[0] != attr:
                    continue
                honoa__twune = True
                oji__bdol.append(qigx__hadz[1] if len(qigx__hadz) == 2 else
                    qigx__hadz[1:])
                qzkdo__iqqs.append(df.data[i])
            if honoa__twune:
                return DataFrameType(tuple(qzkdo__iqqs), df.index, tuple(
                    oji__bdol))


DataFrameAttribute._no_unliteral = True


@overload(operator.getitem, no_unliteral=True)
def namedtuple_getitem_overload(tup, idx):
    if isinstance(tup, types.BaseNamedTuple) and is_overload_constant_str(idx):
        svfie__lrzow = get_overload_const_str(idx)
        val_ind = tup.instance_class._fields.index(svfie__lrzow)
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
        xjeko__roma = builder.extract_value(payload.data, i)
        context.nrt.decref(builder, df_type.data[i], xjeko__roma)
    context.nrt.decref(builder, df_type.index, payload.index)


def define_df_dtor(context, builder, df_type, payload_type):
    pkyuv__jds = builder.module
    vvs__bam = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    koc__pggaq = cgutils.get_or_insert_function(pkyuv__jds, vvs__bam, name=
        '.dtor.df.{}'.format(df_type))
    if not koc__pggaq.is_declaration:
        return koc__pggaq
    koc__pggaq.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(koc__pggaq.append_basic_block())
    wmyn__tgvrc = koc__pggaq.args[0]
    ssgdx__railk = context.get_value_type(payload_type).as_pointer()
    hlvit__whny = builder.bitcast(wmyn__tgvrc, ssgdx__railk)
    payload = context.make_helper(builder, payload_type, ref=hlvit__whny)
    decref_df_data(context, builder, payload, df_type)
    has_parent = cgutils.is_not_null(builder, payload.parent)
    with builder.if_then(has_parent):
        hduy__oco = context.get_python_api(builder)
        osk__tsz = hduy__oco.gil_ensure()
        hduy__oco.decref(payload.parent)
        hduy__oco.gil_release(osk__tsz)
    builder.ret_void()
    return koc__pggaq


def construct_dataframe(context, builder, df_type, data_tup, index_val,
    parent=None, colnames=None):
    payload_type = DataFramePayloadType(df_type)
    etz__kwf = cgutils.create_struct_proxy(payload_type)(context, builder)
    etz__kwf.data = data_tup
    etz__kwf.index = index_val
    if colnames is not None:
        assert df_type.has_runtime_cols, 'construct_dataframe can only provide colnames if columns are determined at runtime'
        etz__kwf.columns = colnames
    rvfpr__golw = context.get_value_type(payload_type)
    shoct__rmkh = context.get_abi_sizeof(rvfpr__golw)
    iti__stk = define_df_dtor(context, builder, df_type, payload_type)
    rhpg__tnpn = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, shoct__rmkh), iti__stk)
    uhdc__dzk = context.nrt.meminfo_data(builder, rhpg__tnpn)
    nqoyk__wep = builder.bitcast(uhdc__dzk, rvfpr__golw.as_pointer())
    zhm__pui = cgutils.create_struct_proxy(df_type)(context, builder)
    zhm__pui.meminfo = rhpg__tnpn
    if parent is None:
        zhm__pui.parent = cgutils.get_null_value(zhm__pui.parent.type)
    else:
        zhm__pui.parent = parent
        etz__kwf.parent = parent
        has_parent = cgutils.is_not_null(builder, parent)
        with builder.if_then(has_parent):
            hduy__oco = context.get_python_api(builder)
            osk__tsz = hduy__oco.gil_ensure()
            hduy__oco.incref(parent)
            hduy__oco.gil_release(osk__tsz)
    builder.store(etz__kwf._getvalue(), nqoyk__wep)
    return zhm__pui._getvalue()


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
        zzwk__dkr = [data_typ.dtype.arr_types.dtype] * len(data_typ.dtype.
            arr_types)
    else:
        zzwk__dkr = [cckrg__itgcc for cckrg__itgcc in data_typ.dtype.arr_types]
    wcoae__vff = DataFrameType(tuple(zzwk__dkr + [colnames_index_typ]),
        index_typ, None, is_table_format=True)

    def codegen(context, builder, signature, args):
        df_type = signature.return_type
        data_tup, index, col_names = args
        parent = None
        vym__pbijg = construct_dataframe(context, builder, df_type,
            data_tup, index, parent, col_names)
        context.nrt.incref(builder, data_typ, data_tup)
        context.nrt.incref(builder, index_typ, index)
        context.nrt.incref(builder, colnames_index_typ, col_names)
        return vym__pbijg
    sig = signature(wcoae__vff, data_typ, index_typ, colnames_index_typ)
    return sig, codegen


@intrinsic
def init_dataframe(typingctx, data_tup_typ, index_typ, col_names_typ=None):
    assert is_pd_index_type(index_typ) or isinstance(index_typ, MultiIndexType
        ), 'init_dataframe(): invalid index type'
    gzkxu__mqt = len(data_tup_typ.types)
    if gzkxu__mqt == 0:
        column_names = ()
    elif isinstance(col_names_typ, types.TypeRef):
        column_names = col_names_typ.instance_type.columns
    else:
        column_names = get_const_tup_vals(col_names_typ)
    if gzkxu__mqt == 1 and isinstance(data_tup_typ.types[0], TableType):
        gzkxu__mqt = len(data_tup_typ.types[0].arr_types)
    assert len(column_names
        ) == gzkxu__mqt, 'init_dataframe(): number of column names does not match number of columns'
    is_table_format = False
    myis__jjs = data_tup_typ.types
    if gzkxu__mqt != 0 and isinstance(data_tup_typ.types[0], TableType):
        myis__jjs = data_tup_typ.types[0].arr_types
        is_table_format = True
    wcoae__vff = DataFrameType(myis__jjs, index_typ, column_names,
        is_table_format=is_table_format)

    def codegen(context, builder, signature, args):
        df_type = signature.return_type
        data_tup = args[0]
        index_val = args[1]
        parent = None
        if is_table_format:
            hecl__vcoag = cgutils.create_struct_proxy(wcoae__vff.table_type)(
                context, builder, builder.extract_value(data_tup, 0))
            parent = hecl__vcoag.parent
        vym__pbijg = construct_dataframe(context, builder, df_type,
            data_tup, index_val, parent, None)
        context.nrt.incref(builder, data_tup_typ, data_tup)
        context.nrt.incref(builder, index_typ, index_val)
        return vym__pbijg
    sig = signature(wcoae__vff, data_tup_typ, index_typ, col_names_typ)
    return sig, codegen


@intrinsic
def has_parent(typingctx, df=None):
    check_runtime_cols_unsupported(df, 'has_parent')

    def codegen(context, builder, sig, args):
        zhm__pui = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        return cgutils.is_not_null(builder, zhm__pui.parent)
    return signature(types.bool_, df), codegen


@intrinsic
def _column_needs_unboxing(typingctx, df_typ, i_typ=None):
    check_runtime_cols_unsupported(df_typ, '_column_needs_unboxing')
    assert isinstance(df_typ, DataFrameType) and is_overload_constant_int(i_typ
        )

    def codegen(context, builder, sig, args):
        etz__kwf = get_dataframe_payload(context, builder, df_typ, args[0])
        pjw__xrtnn = get_overload_const_int(i_typ)
        arr_typ = df_typ.data[pjw__xrtnn]
        if df_typ.is_table_format:
            hecl__vcoag = cgutils.create_struct_proxy(df_typ.table_type)(
                context, builder, builder.extract_value(etz__kwf.data, 0))
            lpm__xmas = df_typ.table_type.type_to_blk[arr_typ]
            ror__oljeg = getattr(hecl__vcoag, f'block_{lpm__xmas}')
            cbcnr__cane = ListInstance(context, builder, types.List(arr_typ
                ), ror__oljeg)
            llsyd__aryaw = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[pjw__xrtnn])
            xjeko__roma = cbcnr__cane.getitem(llsyd__aryaw)
        else:
            xjeko__roma = builder.extract_value(etz__kwf.data, pjw__xrtnn)
        alj__yvgg = cgutils.alloca_once_value(builder, xjeko__roma)
        hthj__hfuld = cgutils.alloca_once_value(builder, context.
            get_constant_null(arr_typ))
        return is_ll_eq(builder, alj__yvgg, hthj__hfuld)
    return signature(types.bool_, df_typ, i_typ), codegen


def get_dataframe_payload(context, builder, df_type, value):
    rhpg__tnpn = cgutils.create_struct_proxy(df_type)(context, builder, value
        ).meminfo
    payload_type = DataFramePayloadType(df_type)
    payload = context.nrt.meminfo_data(builder, rhpg__tnpn)
    ssgdx__railk = context.get_value_type(payload_type).as_pointer()
    payload = builder.bitcast(payload, ssgdx__railk)
    return context.make_helper(builder, payload_type, ref=payload)


@intrinsic
def _get_dataframe_data(typingctx, df_typ=None):
    check_runtime_cols_unsupported(df_typ, '_get_dataframe_data')
    wcoae__vff = types.Tuple(df_typ.data)
    if df_typ.is_table_format:
        wcoae__vff = types.Tuple([TableType(df_typ.data)])
    sig = signature(wcoae__vff, df_typ)

    def codegen(context, builder, signature, args):
        etz__kwf = get_dataframe_payload(context, builder, signature.args[0
            ], args[0])
        return impl_ret_borrowed(context, builder, signature.return_type,
            etz__kwf.data)
    return sig, codegen


@intrinsic
def get_dataframe_index(typingctx, df_typ=None):

    def codegen(context, builder, signature, args):
        etz__kwf = get_dataframe_payload(context, builder, signature.args[0
            ], args[0])
        return impl_ret_borrowed(context, builder, df_typ.index, etz__kwf.index
            )
    wcoae__vff = df_typ.index
    sig = signature(wcoae__vff, df_typ)
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
        ickx__xgosv = df.data[i]
        return ickx__xgosv(*args)


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
        etz__kwf = get_dataframe_payload(context, builder, signature.args[0
            ], args[0])
        return impl_ret_borrowed(context, builder, df_typ.table_type,
            builder.extract_value(etz__kwf.data, 0))
    return df_typ.table_type(df_typ), codegen


@intrinsic
def get_dataframe_column_names(typingctx, df_typ=None):
    assert df_typ.has_runtime_cols, 'get_dataframe_column_names() expects columns to be determined at runtime'

    def codegen(context, builder, signature, args):
        etz__kwf = get_dataframe_payload(context, builder, signature.args[0
            ], args[0])
        return impl_ret_borrowed(context, builder, df_typ.
            runtime_colname_typ, etz__kwf.columns)
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
    kehv__eyxg = self.typemap[data_tup.name]
    if any(is_tuple_like_type(cckrg__itgcc) for cckrg__itgcc in kehv__eyxg.
        types):
        return None
    if equiv_set.has_shape(data_tup):
        iyyal__ocsv = equiv_set.get_shape(data_tup)
        if len(iyyal__ocsv) > 1:
            equiv_set.insert_equiv(*iyyal__ocsv)
        if len(iyyal__ocsv) > 0:
            cqo__zcgkw = self.typemap[index.name]
            if not isinstance(cqo__zcgkw, HeterogeneousIndexType
                ) and equiv_set.has_shape(index):
                equiv_set.insert_equiv(iyyal__ocsv[0], index)
            return ArrayAnalysis.AnalyzeResult(shape=(iyyal__ocsv[0], len(
                iyyal__ocsv)), pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_dataframe_ext_init_dataframe
    ) = init_dataframe_equiv


def get_dataframe_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    njg__zaie = args[0]
    data_types = self.typemap[njg__zaie.name].data
    if any(is_tuple_like_type(cckrg__itgcc) for cckrg__itgcc in data_types):
        return None
    if equiv_set.has_shape(njg__zaie):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            njg__zaie)[0], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_data
    ) = get_dataframe_data_equiv


def get_dataframe_index_equiv(self, scope, equiv_set, loc, args, kws):
    from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
    assert len(args) == 1 and not kws
    njg__zaie = args[0]
    cqo__zcgkw = self.typemap[njg__zaie.name].index
    if isinstance(cqo__zcgkw, HeterogeneousIndexType):
        return None
    if equiv_set.has_shape(njg__zaie):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            njg__zaie)[0], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_index
    ) = get_dataframe_index_equiv


def get_dataframe_table_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    njg__zaie = args[0]
    if equiv_set.has_shape(njg__zaie):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            njg__zaie), pre=[])


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_table
    ) = get_dataframe_table_equiv


def get_dataframe_column_names_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    njg__zaie = args[0]
    if equiv_set.has_shape(njg__zaie):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            njg__zaie)[1], pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_dataframe_ext_get_dataframe_column_names
    ) = get_dataframe_column_names_equiv


@intrinsic
def set_dataframe_data(typingctx, df_typ, c_ind_typ, arr_typ=None):
    check_runtime_cols_unsupported(df_typ, 'set_dataframe_data')
    assert is_overload_constant_int(c_ind_typ)
    pjw__xrtnn = get_overload_const_int(c_ind_typ)
    if df_typ.data[pjw__xrtnn] != arr_typ:
        raise BodoError(
            'Changing dataframe column data type inplace is not supported in conditionals/loops or for dataframe arguments'
            )

    def codegen(context, builder, signature, args):
        jnch__roxo, zvkzz__bkzgb, rccqo__gwfx = args
        etz__kwf = get_dataframe_payload(context, builder, df_typ, jnch__roxo)
        if df_typ.is_table_format:
            hecl__vcoag = cgutils.create_struct_proxy(df_typ.table_type)(
                context, builder, builder.extract_value(etz__kwf.data, 0))
            lpm__xmas = df_typ.table_type.type_to_blk[arr_typ]
            ror__oljeg = getattr(hecl__vcoag, f'block_{lpm__xmas}')
            cbcnr__cane = ListInstance(context, builder, types.List(arr_typ
                ), ror__oljeg)
            llsyd__aryaw = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[pjw__xrtnn])
            cbcnr__cane.setitem(llsyd__aryaw, rccqo__gwfx, True)
        else:
            xjeko__roma = builder.extract_value(etz__kwf.data, pjw__xrtnn)
            context.nrt.decref(builder, df_typ.data[pjw__xrtnn], xjeko__roma)
            etz__kwf.data = builder.insert_value(etz__kwf.data, rccqo__gwfx,
                pjw__xrtnn)
            context.nrt.incref(builder, arr_typ, rccqo__gwfx)
        zhm__pui = cgutils.create_struct_proxy(df_typ)(context, builder,
            value=jnch__roxo)
        payload_type = DataFramePayloadType(df_typ)
        hlvit__whny = context.nrt.meminfo_data(builder, zhm__pui.meminfo)
        ssgdx__railk = context.get_value_type(payload_type).as_pointer()
        hlvit__whny = builder.bitcast(hlvit__whny, ssgdx__railk)
        builder.store(etz__kwf._getvalue(), hlvit__whny)
        return impl_ret_borrowed(context, builder, df_typ, jnch__roxo)
    sig = signature(df_typ, df_typ, c_ind_typ, arr_typ)
    return sig, codegen


@intrinsic
def set_df_index(typingctx, df_t, index_t=None):
    check_runtime_cols_unsupported(df_t, 'set_df_index')

    def codegen(context, builder, signature, args):
        bkq__oofx = args[0]
        index_val = args[1]
        df_typ = signature.args[0]
        uyn__hsicp = cgutils.create_struct_proxy(df_typ)(context, builder,
            value=bkq__oofx)
        moc__pfjla = get_dataframe_payload(context, builder, df_typ, bkq__oofx)
        zhm__pui = construct_dataframe(context, builder, signature.
            return_type, moc__pfjla.data, index_val, uyn__hsicp.parent, None)
        context.nrt.incref(builder, index_t, index_val)
        context.nrt.incref(builder, types.Tuple(df_t.data), moc__pfjla.data)
        return zhm__pui
    wcoae__vff = DataFrameType(df_t.data, index_t, df_t.columns, df_t.dist,
        df_t.is_table_format)
    sig = signature(wcoae__vff, df_t, index_t)
    return sig, codegen


@intrinsic
def set_df_column_with_reflect(typingctx, df_type, cname_type, arr_type=None):
    check_runtime_cols_unsupported(df_type, 'set_df_column_with_reflect')
    assert is_literal_type(cname_type), 'constant column name expected'
    col_name = get_literal_value(cname_type)
    gzkxu__mqt = len(df_type.columns)
    fxoql__xfu = gzkxu__mqt
    jycju__cok = df_type.data
    column_names = df_type.columns
    index_typ = df_type.index
    kknxy__bmf = col_name not in df_type.columns
    pjw__xrtnn = gzkxu__mqt
    if kknxy__bmf:
        jycju__cok += arr_type,
        column_names += col_name,
        fxoql__xfu += 1
    else:
        pjw__xrtnn = df_type.columns.index(col_name)
        jycju__cok = tuple(arr_type if i == pjw__xrtnn else jycju__cok[i] for
            i in range(gzkxu__mqt))

    def codegen(context, builder, signature, args):
        jnch__roxo, zvkzz__bkzgb, rccqo__gwfx = args
        in_dataframe_payload = get_dataframe_payload(context, builder,
            df_type, jnch__roxo)
        pgcih__vdvmu = cgutils.create_struct_proxy(df_type)(context,
            builder, value=jnch__roxo)
        if df_type.is_table_format:
            ovvy__czo = df_type.table_type
            dpgyx__hubk = builder.extract_value(in_dataframe_payload.data, 0)
            ciurp__oxkkr = TableType(jycju__cok)
            roka__dusjm = set_table_data_codegen(context, builder,
                ovvy__czo, dpgyx__hubk, ciurp__oxkkr, arr_type, rccqo__gwfx,
                pjw__xrtnn, kknxy__bmf)
            data_tup = context.make_tuple(builder, types.Tuple([
                ciurp__oxkkr]), [roka__dusjm])
        else:
            myis__jjs = [(builder.extract_value(in_dataframe_payload.data,
                i) if i != pjw__xrtnn else rccqo__gwfx) for i in range(
                gzkxu__mqt)]
            if kknxy__bmf:
                myis__jjs.append(rccqo__gwfx)
            for njg__zaie, pemy__ubs in zip(myis__jjs, jycju__cok):
                context.nrt.incref(builder, pemy__ubs, njg__zaie)
            data_tup = context.make_tuple(builder, types.Tuple(jycju__cok),
                myis__jjs)
        index_val = in_dataframe_payload.index
        context.nrt.incref(builder, index_typ, index_val)
        zvzjn__pdr = construct_dataframe(context, builder, signature.
            return_type, data_tup, index_val, pgcih__vdvmu.parent, None)
        if not kknxy__bmf and arr_type == df_type.data[pjw__xrtnn]:
            decref_df_data(context, builder, in_dataframe_payload, df_type)
            payload_type = DataFramePayloadType(df_type)
            hlvit__whny = context.nrt.meminfo_data(builder, pgcih__vdvmu.
                meminfo)
            ssgdx__railk = context.get_value_type(payload_type).as_pointer()
            hlvit__whny = builder.bitcast(hlvit__whny, ssgdx__railk)
            ayx__xvhlf = get_dataframe_payload(context, builder, df_type,
                zvzjn__pdr)
            builder.store(ayx__xvhlf._getvalue(), hlvit__whny)
            context.nrt.incref(builder, index_typ, index_val)
            if df_type.is_table_format:
                context.nrt.incref(builder, ciurp__oxkkr, builder.
                    extract_value(data_tup, 0))
            else:
                for njg__zaie, pemy__ubs in zip(myis__jjs, jycju__cok):
                    context.nrt.incref(builder, pemy__ubs, njg__zaie)
        has_parent = cgutils.is_not_null(builder, pgcih__vdvmu.parent)
        with builder.if_then(has_parent):
            hduy__oco = context.get_python_api(builder)
            osk__tsz = hduy__oco.gil_ensure()
            srh__dkw = context.get_env_manager(builder)
            context.nrt.incref(builder, arr_type, rccqo__gwfx)
            fss__fls = numba.core.pythonapi._BoxContext(context, builder,
                hduy__oco, srh__dkw)
            hucl__mtn = fss__fls.pyapi.from_native_value(arr_type,
                rccqo__gwfx, fss__fls.env_manager)
            if isinstance(col_name, str):
                smgq__hnb = context.insert_const_string(builder.module,
                    col_name)
                hfvw__vhq = hduy__oco.string_from_string(smgq__hnb)
            else:
                assert isinstance(col_name, int)
                hfvw__vhq = hduy__oco.long_from_longlong(context.
                    get_constant(types.intp, col_name))
            hduy__oco.object_setitem(pgcih__vdvmu.parent, hfvw__vhq, hucl__mtn)
            hduy__oco.decref(hucl__mtn)
            hduy__oco.decref(hfvw__vhq)
            hduy__oco.gil_release(osk__tsz)
        return zvzjn__pdr
    wcoae__vff = DataFrameType(jycju__cok, index_typ, column_names, df_type
        .dist, df_type.is_table_format)
    sig = signature(wcoae__vff, df_type, cname_type, arr_type)
    return sig, codegen


@lower_constant(DataFrameType)
def lower_constant_dataframe(context, builder, df_type, pyval):
    check_runtime_cols_unsupported(df_type, 'lowering a constant DataFrame')
    gzkxu__mqt = len(pyval.columns)
    myis__jjs = []
    for i in range(gzkxu__mqt):
        uhgvv__eng = pyval.iloc[:, i]
        if isinstance(df_type.data[i], bodo.DatetimeArrayType):
            hucl__mtn = uhgvv__eng.array
        else:
            hucl__mtn = uhgvv__eng.values
        myis__jjs.append(hucl__mtn)
    myis__jjs = tuple(myis__jjs)
    if df_type.is_table_format:
        hecl__vcoag = context.get_constant_generic(builder, df_type.
            table_type, Table(myis__jjs))
        data_tup = lir.Constant.literal_struct([hecl__vcoag])
    else:
        data_tup = lir.Constant.literal_struct([context.
            get_constant_generic(builder, df_type.data[i], qigx__hadz) for 
            i, qigx__hadz in enumerate(myis__jjs)])
    index_val = context.get_constant_generic(builder, df_type.index, pyval.
        index)
    vtln__pcb = context.get_constant_null(types.pyobject)
    payload = lir.Constant.literal_struct([data_tup, index_val, vtln__pcb])
    payload = cgutils.global_constant(builder, '.const.payload', payload
        ).bitcast(cgutils.voidptr_t)
    pnf__nzqnj = context.get_constant(types.int64, -1)
    cybtd__hkwz = context.get_constant_null(types.voidptr)
    rhpg__tnpn = lir.Constant.literal_struct([pnf__nzqnj, cybtd__hkwz,
        cybtd__hkwz, payload, pnf__nzqnj])
    rhpg__tnpn = cgutils.global_constant(builder, '.const.meminfo', rhpg__tnpn
        ).bitcast(cgutils.voidptr_t)
    return lir.Constant.literal_struct([rhpg__tnpn, vtln__pcb])


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
        qshy__gtgl = context.cast(builder, in_dataframe_payload.index,
            fromty.index, toty.index)
    else:
        qshy__gtgl = in_dataframe_payload.index
        context.nrt.incref(builder, fromty.index, qshy__gtgl)
    if (fromty.is_table_format == toty.is_table_format and fromty.data ==
        toty.data):
        qzkdo__iqqs = in_dataframe_payload.data
        if fromty.is_table_format:
            context.nrt.incref(builder, types.Tuple([fromty.table_type]),
                qzkdo__iqqs)
        else:
            context.nrt.incref(builder, types.BaseTuple.from_types(fromty.
                data), qzkdo__iqqs)
    elif not fromty.is_table_format and toty.is_table_format:
        qzkdo__iqqs = _cast_df_data_to_table_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    elif fromty.is_table_format and not toty.is_table_format:
        qzkdo__iqqs = _cast_df_data_to_tuple_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    elif fromty.is_table_format and toty.is_table_format:
        qzkdo__iqqs = _cast_df_data_keep_table_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    else:
        qzkdo__iqqs = _cast_df_data_keep_tuple_format(context, builder,
            fromty, toty, val, in_dataframe_payload)
    return construct_dataframe(context, builder, toty, qzkdo__iqqs,
        qshy__gtgl, in_dataframe_payload.parent, None)


def _cast_empty_df(context, builder, toty):
    yfom__cnljy = {}
    if isinstance(toty.index, RangeIndexType):
        index = 'bodo.hiframes.pd_index_ext.init_range_index(0, 0, 1, None)'
    else:
        nhqtu__tqma = get_index_data_arr_types(toty.index)[0]
        jhnwa__hsfqt = bodo.utils.transform.get_type_alloc_counts(nhqtu__tqma
            ) - 1
        cjcm__xxqmn = ', '.join('0' for zvkzz__bkzgb in range(jhnwa__hsfqt))
        index = (
            'bodo.utils.conversion.index_from_array(bodo.utils.utils.alloc_type(0, index_arr_type, ({}{})))'
            .format(cjcm__xxqmn, ', ' if jhnwa__hsfqt == 1 else ''))
        yfom__cnljy['index_arr_type'] = nhqtu__tqma
    oqb__xlofm = []
    for i, arr_typ in enumerate(toty.data):
        jhnwa__hsfqt = bodo.utils.transform.get_type_alloc_counts(arr_typ) - 1
        cjcm__xxqmn = ', '.join('0' for zvkzz__bkzgb in range(jhnwa__hsfqt))
        lga__qisec = ('bodo.utils.utils.alloc_type(0, arr_type{}, ({}{}))'.
            format(i, cjcm__xxqmn, ', ' if jhnwa__hsfqt == 1 else ''))
        oqb__xlofm.append(lga__qisec)
        yfom__cnljy[f'arr_type{i}'] = arr_typ
    oqb__xlofm = ', '.join(oqb__xlofm)
    hegu__ztmzk = 'def impl():\n'
    zao__vcl = bodo.hiframes.dataframe_impl._gen_init_df(hegu__ztmzk, toty.
        columns, oqb__xlofm, index, yfom__cnljy)
    df = context.compile_internal(builder, zao__vcl, toty(), [])
    return df


def _cast_df_data_to_table_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting traditional DataFrame to table format')
    uwvyf__teia = toty.table_type
    hecl__vcoag = cgutils.create_struct_proxy(uwvyf__teia)(context, builder)
    hecl__vcoag.parent = in_dataframe_payload.parent
    for cckrg__itgcc, lpm__xmas in uwvyf__teia.type_to_blk.items():
        tryso__hru = context.get_constant(types.int64, len(uwvyf__teia.
            block_to_arr_ind[lpm__xmas]))
        zvkzz__bkzgb, zsrj__lawyh = ListInstance.allocate_ex(context,
            builder, types.List(cckrg__itgcc), tryso__hru)
        zsrj__lawyh.size = tryso__hru
        setattr(hecl__vcoag, f'block_{lpm__xmas}', zsrj__lawyh.value)
    for i, cckrg__itgcc in enumerate(fromty.data):
        kkebo__nfn = toty.data[i]
        if cckrg__itgcc != kkebo__nfn:
            jmvfh__xxtp = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*jmvfh__xxtp)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        xjeko__roma = builder.extract_value(in_dataframe_payload.data, i)
        if cckrg__itgcc != kkebo__nfn:
            rqfjn__maty = context.cast(builder, xjeko__roma, cckrg__itgcc,
                kkebo__nfn)
            igbdo__mnai = False
        else:
            rqfjn__maty = xjeko__roma
            igbdo__mnai = True
        lpm__xmas = uwvyf__teia.type_to_blk[cckrg__itgcc]
        ror__oljeg = getattr(hecl__vcoag, f'block_{lpm__xmas}')
        cbcnr__cane = ListInstance(context, builder, types.List(
            cckrg__itgcc), ror__oljeg)
        llsyd__aryaw = context.get_constant(types.int64, uwvyf__teia.
            block_offsets[i])
        cbcnr__cane.setitem(llsyd__aryaw, rqfjn__maty, igbdo__mnai)
    data_tup = context.make_tuple(builder, types.Tuple([uwvyf__teia]), [
        hecl__vcoag._getvalue()])
    return data_tup


def _cast_df_data_keep_tuple_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting traditional DataFrame columns')
    myis__jjs = []
    for i in range(len(fromty.data)):
        if fromty.data[i] != toty.data[i]:
            jmvfh__xxtp = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*jmvfh__xxtp)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
            xjeko__roma = builder.extract_value(in_dataframe_payload.data, i)
            rqfjn__maty = context.cast(builder, xjeko__roma, fromty.data[i],
                toty.data[i])
            igbdo__mnai = False
        else:
            rqfjn__maty = builder.extract_value(in_dataframe_payload.data, i)
            igbdo__mnai = True
        if igbdo__mnai:
            context.nrt.incref(builder, toty.data[i], rqfjn__maty)
        myis__jjs.append(rqfjn__maty)
    data_tup = context.make_tuple(builder, types.Tuple(toty.data), myis__jjs)
    return data_tup


def _cast_df_data_keep_table_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(toty,
        'casting table format DataFrame columns')
    ovvy__czo = fromty.table_type
    dpgyx__hubk = cgutils.create_struct_proxy(ovvy__czo)(context, builder,
        builder.extract_value(in_dataframe_payload.data, 0))
    ciurp__oxkkr = toty.table_type
    roka__dusjm = cgutils.create_struct_proxy(ciurp__oxkkr)(context, builder)
    roka__dusjm.parent = in_dataframe_payload.parent
    for cckrg__itgcc, lpm__xmas in ciurp__oxkkr.type_to_blk.items():
        tryso__hru = context.get_constant(types.int64, len(ciurp__oxkkr.
            block_to_arr_ind[lpm__xmas]))
        zvkzz__bkzgb, zsrj__lawyh = ListInstance.allocate_ex(context,
            builder, types.List(cckrg__itgcc), tryso__hru)
        zsrj__lawyh.size = tryso__hru
        setattr(roka__dusjm, f'block_{lpm__xmas}', zsrj__lawyh.value)
    for i in range(len(fromty.data)):
        xvtw__tti = fromty.data[i]
        kkebo__nfn = toty.data[i]
        if xvtw__tti != kkebo__nfn:
            jmvfh__xxtp = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*jmvfh__xxtp)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        hhdqg__ffp = ovvy__czo.type_to_blk[xvtw__tti]
        bryp__gtx = getattr(dpgyx__hubk, f'block_{hhdqg__ffp}')
        vktg__fvb = ListInstance(context, builder, types.List(xvtw__tti),
            bryp__gtx)
        udosv__jvyv = context.get_constant(types.int64, ovvy__czo.
            block_offsets[i])
        xjeko__roma = vktg__fvb.getitem(udosv__jvyv)
        if xvtw__tti != kkebo__nfn:
            rqfjn__maty = context.cast(builder, xjeko__roma, xvtw__tti,
                kkebo__nfn)
            igbdo__mnai = False
        else:
            rqfjn__maty = xjeko__roma
            igbdo__mnai = True
        jocw__zgs = ciurp__oxkkr.type_to_blk[cckrg__itgcc]
        zsrj__lawyh = getattr(roka__dusjm, f'block_{jocw__zgs}')
        pqwo__opsud = ListInstance(context, builder, types.List(kkebo__nfn),
            zsrj__lawyh)
        lzvuu__esf = context.get_constant(types.int64, ciurp__oxkkr.
            block_offsets[i])
        pqwo__opsud.setitem(lzvuu__esf, rqfjn__maty, igbdo__mnai)
    data_tup = context.make_tuple(builder, types.Tuple([ciurp__oxkkr]), [
        roka__dusjm._getvalue()])
    return data_tup


def _cast_df_data_to_tuple_format(context, builder, fromty, toty, df,
    in_dataframe_payload):
    check_runtime_cols_unsupported(fromty,
        'casting table format to traditional DataFrame')
    uwvyf__teia = fromty.table_type
    hecl__vcoag = cgutils.create_struct_proxy(uwvyf__teia)(context, builder,
        builder.extract_value(in_dataframe_payload.data, 0))
    myis__jjs = []
    for i, cckrg__itgcc in enumerate(toty.data):
        xvtw__tti = fromty.data[i]
        if cckrg__itgcc != xvtw__tti:
            jmvfh__xxtp = fromty, types.literal(i)
            impl = lambda df, i: bodo.hiframes.boxing.unbox_col_if_needed(df, i
                )
            sig = types.none(*jmvfh__xxtp)
            args = df, context.get_constant(types.int64, i)
            context.compile_internal(builder, impl, sig, args)
        lpm__xmas = uwvyf__teia.type_to_blk[cckrg__itgcc]
        ror__oljeg = getattr(hecl__vcoag, f'block_{lpm__xmas}')
        cbcnr__cane = ListInstance(context, builder, types.List(
            cckrg__itgcc), ror__oljeg)
        llsyd__aryaw = context.get_constant(types.int64, uwvyf__teia.
            block_offsets[i])
        xjeko__roma = cbcnr__cane.getitem(llsyd__aryaw)
        if cckrg__itgcc != xvtw__tti:
            rqfjn__maty = context.cast(builder, xjeko__roma, xvtw__tti,
                cckrg__itgcc)
            igbdo__mnai = False
        else:
            rqfjn__maty = xjeko__roma
            igbdo__mnai = True
        if igbdo__mnai:
            context.nrt.incref(builder, cckrg__itgcc, rqfjn__maty)
        myis__jjs.append(rqfjn__maty)
    data_tup = context.make_tuple(builder, types.Tuple(toty.data), myis__jjs)
    return data_tup


@overload(pd.DataFrame, inline='always', no_unliteral=True)
def pd_dataframe_overload(data=None, index=None, columns=None, dtype=None,
    copy=False):
    if not is_overload_constant_bool(copy):
        raise BodoError(
            "pd.DataFrame(): 'copy' argument should be a constant boolean")
    copy = get_overload_const(copy)
    msw__xggs, oqb__xlofm, index_arg = _get_df_args(data, index, columns,
        dtype, copy)
    rpmr__veyhy = gen_const_tup(msw__xggs)
    hegu__ztmzk = (
        'def _init_df(data=None, index=None, columns=None, dtype=None, copy=False):\n'
        )
    hegu__ztmzk += (
        '  return bodo.hiframes.pd_dataframe_ext.init_dataframe({}, {}, {})\n'
        .format(oqb__xlofm, index_arg, rpmr__veyhy))
    pok__oow = {}
    exec(hegu__ztmzk, {'bodo': bodo, 'np': np}, pok__oow)
    bkyj__fcyq = pok__oow['_init_df']
    return bkyj__fcyq


@intrinsic
def _tuple_to_table_format_decoded(typingctx, df_typ):
    assert not df_typ.is_table_format, '_tuple_to_table_format requires a tuple format input'

    def codegen(context, builder, signature, args):
        return context.cast(builder, args[0], signature.args[0], signature.
            return_type)
    wcoae__vff = DataFrameType(to_str_arr_if_dict_array(df_typ.data),
        df_typ.index, df_typ.columns, dist=df_typ.dist, is_table_format=True)
    sig = signature(wcoae__vff, df_typ)
    return sig, codegen


@intrinsic
def _table_to_tuple_format_decoded(typingctx, df_typ):
    assert df_typ.is_table_format, '_tuple_to_table_format requires a table format input'

    def codegen(context, builder, signature, args):
        return context.cast(builder, args[0], signature.args[0], signature.
            return_type)
    wcoae__vff = DataFrameType(to_str_arr_if_dict_array(df_typ.data),
        df_typ.index, df_typ.columns, dist=df_typ.dist, is_table_format=False)
    sig = signature(wcoae__vff, df_typ)
    return sig, codegen


def _get_df_args(data, index, columns, dtype, copy):
    fsm__ynxu = ''
    if not is_overload_none(dtype):
        fsm__ynxu = '.astype(dtype)'
    index_is_none = is_overload_none(index)
    index_arg = 'bodo.utils.conversion.convert_to_index(index)'
    if isinstance(data, types.BaseTuple):
        if not data.types[0] == types.StringLiteral('__bodo_tup'):
            raise BodoError('pd.DataFrame tuple input data not supported yet')
        assert len(data.types) % 2 == 1, 'invalid const dict tuple structure'
        gzkxu__mqt = (len(data.types) - 1) // 2
        uexl__mhqai = [cckrg__itgcc.literal_value for cckrg__itgcc in data.
            types[1:gzkxu__mqt + 1]]
        data_val_types = dict(zip(uexl__mhqai, data.types[gzkxu__mqt + 1:]))
        myis__jjs = ['data[{}]'.format(i) for i in range(gzkxu__mqt + 1, 2 *
            gzkxu__mqt + 1)]
        data_dict = dict(zip(uexl__mhqai, myis__jjs))
        if is_overload_none(index):
            for i, cckrg__itgcc in enumerate(data.types[gzkxu__mqt + 1:]):
                if isinstance(cckrg__itgcc, SeriesType):
                    index_arg = (
                        'bodo.hiframes.pd_series_ext.get_series_index(data[{}])'
                        .format(gzkxu__mqt + 1 + i))
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
        mitqc__crj = '.copy()' if copy else ''
        hkev__qdp = get_overload_const_list(columns)
        gzkxu__mqt = len(hkev__qdp)
        data_val_types = {fss__fls: data.copy(ndim=1) for fss__fls in hkev__qdp
            }
        myis__jjs = ['data[:,{}]{}'.format(i, mitqc__crj) for i in range(
            gzkxu__mqt)]
        data_dict = dict(zip(hkev__qdp, myis__jjs))
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
    oqb__xlofm = '({},)'.format(', '.join(
        'bodo.utils.conversion.coerce_to_array({}, True, scalar_to_arr_len={}){}'
        .format(data_dict[fss__fls], df_len, fsm__ynxu) for fss__fls in
        col_names))
    if len(col_names) == 0:
        oqb__xlofm = '()'
    return col_names, oqb__xlofm, index_arg


def _get_df_len_from_info(data_dict, data_val_types, col_names,
    index_is_none, index_arg):
    df_len = '0'
    for fss__fls in col_names:
        if fss__fls in data_dict and is_iterable_type(data_val_types[fss__fls]
            ):
            df_len = 'len({})'.format(data_dict[fss__fls])
            break
    if df_len == '0' and not index_is_none:
        df_len = f'len({index_arg})'
    return df_len


def _fill_null_arrays(data_dict, col_names, df_len, dtype):
    if all(fss__fls in data_dict for fss__fls in col_names):
        return
    if is_overload_none(dtype):
        dtype = 'bodo.string_array_type'
    else:
        dtype = 'bodo.utils.conversion.array_type_from_dtype(dtype)'
    krv__byf = 'bodo.libs.array_kernels.gen_na_array({}, {})'.format(df_len,
        dtype)
    for fss__fls in col_names:
        if fss__fls not in data_dict:
            data_dict[fss__fls] = krv__byf


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
            cckrg__itgcc = bodo.hiframes.pd_dataframe_ext.get_dataframe_table(
                df)
            return len(cckrg__itgcc)
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
        essz__iio = idx.literal_value
        if isinstance(essz__iio, int):
            ickx__xgosv = tup.types[essz__iio]
        elif isinstance(essz__iio, slice):
            ickx__xgosv = types.BaseTuple.from_types(tup.types[essz__iio])
        return signature(ickx__xgosv, *args)


GetItemTuple.prefer_literal = True


@lower_builtin(operator.getitem, types.BaseTuple, types.IntegerLiteral)
@lower_builtin(operator.getitem, types.BaseTuple, types.SliceLiteral)
def getitem_tuple_lower(context, builder, sig, args):
    due__odic, idx = sig.args
    idx = idx.literal_value
    tup, zvkzz__bkzgb = args
    if isinstance(idx, int):
        if idx < 0:
            idx += len(due__odic)
        if not 0 <= idx < len(due__odic):
            raise IndexError('cannot index at %d in %s' % (idx, due__odic))
        snr__xrieg = builder.extract_value(tup, idx)
    elif isinstance(idx, slice):
        mmmi__pxqa = cgutils.unpack_tuple(builder, tup)[idx]
        snr__xrieg = context.make_tuple(builder, sig.return_type, mmmi__pxqa)
    else:
        raise NotImplementedError('unexpected index %r for %s' % (idx, sig.
            args[0]))
    return impl_ret_borrowed(context, builder, sig.return_type, snr__xrieg)


def join_dummy(left_df, right_df, left_on, right_on, how, suffix_x,
    suffix_y, is_join, indicator, _bodo_na_equal, gen_cond):
    return left_df


@infer_global(join_dummy)
class JoinTyper(AbstractTemplate):

    def generic(self, args, kws):
        from bodo.hiframes.pd_dataframe_ext import DataFrameType
        from bodo.utils.typing import is_overload_str
        assert not kws
        (left_df, right_df, left_on, right_on, mgy__oie, suffix_x, suffix_y,
            is_join, indicator, _bodo_na_equal, lydti__blggy) = args
        left_on = get_overload_const_list(left_on)
        right_on = get_overload_const_list(right_on)
        lhok__awf = set(left_on) & set(right_on)
        qnc__ehvl = set(left_df.columns) & set(right_df.columns)
        xixl__cnkf = qnc__ehvl - lhok__awf
        oqut__nlffv = '$_bodo_index_' in left_on
        vlw__mdi = '$_bodo_index_' in right_on
        how = get_overload_const_str(mgy__oie)
        kkpk__fzbf = how in {'left', 'outer'}
        gccl__hztt = how in {'right', 'outer'}
        columns = []
        data = []
        if oqut__nlffv:
            ctul__dvnt = bodo.utils.typing.get_index_data_arr_types(left_df
                .index)[0]
        else:
            ctul__dvnt = left_df.data[left_df.columns.index(left_on[0])]
        if vlw__mdi:
            obm__hxdf = bodo.utils.typing.get_index_data_arr_types(right_df
                .index)[0]
        else:
            obm__hxdf = right_df.data[right_df.columns.index(right_on[0])]
        if oqut__nlffv and not vlw__mdi and not is_join.literal_value:
            slzdi__kvi = right_on[0]
            if slzdi__kvi in left_df.columns:
                columns.append(slzdi__kvi)
                if (obm__hxdf == bodo.dict_str_arr_type and ctul__dvnt ==
                    bodo.string_array_type):
                    acyfw__loekf = bodo.string_array_type
                else:
                    acyfw__loekf = obm__hxdf
                data.append(acyfw__loekf)
        if vlw__mdi and not oqut__nlffv and not is_join.literal_value:
            gmu__ste = left_on[0]
            if gmu__ste in right_df.columns:
                columns.append(gmu__ste)
                if (ctul__dvnt == bodo.dict_str_arr_type and obm__hxdf ==
                    bodo.string_array_type):
                    acyfw__loekf = bodo.string_array_type
                else:
                    acyfw__loekf = ctul__dvnt
                data.append(acyfw__loekf)
        for xvtw__tti, uhgvv__eng in zip(left_df.data, left_df.columns):
            columns.append(str(uhgvv__eng) + suffix_x.literal_value if 
                uhgvv__eng in xixl__cnkf else uhgvv__eng)
            if uhgvv__eng in lhok__awf:
                if xvtw__tti == bodo.dict_str_arr_type:
                    xvtw__tti = right_df.data[right_df.columns.index(
                        uhgvv__eng)]
                data.append(xvtw__tti)
            else:
                if (xvtw__tti == bodo.dict_str_arr_type and uhgvv__eng in
                    left_on):
                    if vlw__mdi:
                        xvtw__tti = obm__hxdf
                    else:
                        oisgm__mrrcq = left_on.index(uhgvv__eng)
                        mud__rrog = right_on[oisgm__mrrcq]
                        xvtw__tti = right_df.data[right_df.columns.index(
                            mud__rrog)]
                if gccl__hztt:
                    xvtw__tti = to_nullable_type(xvtw__tti)
                data.append(xvtw__tti)
        for xvtw__tti, uhgvv__eng in zip(right_df.data, right_df.columns):
            if uhgvv__eng not in lhok__awf:
                columns.append(str(uhgvv__eng) + suffix_y.literal_value if 
                    uhgvv__eng in xixl__cnkf else uhgvv__eng)
                if (xvtw__tti == bodo.dict_str_arr_type and uhgvv__eng in
                    right_on):
                    if oqut__nlffv:
                        xvtw__tti = ctul__dvnt
                    else:
                        oisgm__mrrcq = right_on.index(uhgvv__eng)
                        xvxf__vump = left_on[oisgm__mrrcq]
                        xvtw__tti = left_df.data[left_df.columns.index(
                            xvxf__vump)]
                if kkpk__fzbf:
                    xvtw__tti = to_nullable_type(xvtw__tti)
                data.append(xvtw__tti)
        uzq__ldms = get_overload_const_bool(indicator)
        if uzq__ldms:
            columns.append('_merge')
            data.append(bodo.CategoricalArrayType(bodo.PDCategoricalDtype((
                'left_only', 'right_only', 'both'), bodo.string_type, False)))
        index_typ = RangeIndexType(types.none)
        if oqut__nlffv and vlw__mdi and not is_overload_str(how, 'asof'):
            index_typ = left_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        elif oqut__nlffv and not vlw__mdi:
            index_typ = right_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        elif vlw__mdi and not oqut__nlffv:
            index_typ = left_df.index
            if isinstance(index_typ, bodo.hiframes.pd_index_ext.RangeIndexType
                ):
                index_typ = bodo.hiframes.pd_index_ext.NumericIndexType(types
                    .int64)
        avuq__pvfje = DataFrameType(tuple(data), index_typ, tuple(columns))
        return signature(avuq__pvfje, *args)


JoinTyper._no_unliteral = True


@lower_builtin(join_dummy, types.VarArg(types.Any))
def lower_join_dummy(context, builder, sig, args):
    zhm__pui = cgutils.create_struct_proxy(sig.return_type)(context, builder)
    return zhm__pui._getvalue()


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
    qrmqv__kvh = dict(join=join, join_axes=join_axes, keys=keys, levels=
        levels, names=names, verify_integrity=verify_integrity, sort=sort,
        copy=copy)
    qcsdd__jug = dict(join='outer', join_axes=None, keys=None, levels=None,
        names=None, verify_integrity=False, sort=None, copy=True)
    check_unsupported_args('pandas.concat', qrmqv__kvh, qcsdd__jug,
        package_name='pandas', module_name='General')
    hegu__ztmzk = """def impl(objs, axis=0, join='outer', join_axes=None, ignore_index=False, keys=None, levels=None, names=None, verify_integrity=False, sort=None, copy=True):
"""
    if axis == 1:
        if not isinstance(objs, types.BaseTuple):
            raise_bodo_error(
                'Only tuple argument for pd.concat(axis=1) expected')
        index = (
            'bodo.hiframes.pd_index_ext.init_range_index(0, len(objs[0]), 1, None)'
            )
        zidv__uiezc = 0
        oqb__xlofm = []
        names = []
        for i, ymau__hgu in enumerate(objs.types):
            assert isinstance(ymau__hgu, (SeriesType, DataFrameType))
            check_runtime_cols_unsupported(ymau__hgu, 'pandas.concat()')
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(ymau__hgu
                , 'pandas.concat()')
            if isinstance(ymau__hgu, SeriesType):
                names.append(str(zidv__uiezc))
                zidv__uiezc += 1
                oqb__xlofm.append(
                    'bodo.hiframes.pd_series_ext.get_series_data(objs[{}])'
                    .format(i))
            else:
                names.extend(ymau__hgu.columns)
                for kspt__gdtup in range(len(ymau__hgu.data)):
                    oqb__xlofm.append(
                        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(objs[{}], {})'
                        .format(i, kspt__gdtup))
        return bodo.hiframes.dataframe_impl._gen_init_df(hegu__ztmzk, names,
            ', '.join(oqb__xlofm), index)
    if axis != 0:
        raise_bodo_error('pd.concat(): axis must be 0 or 1')
    if isinstance(objs, types.BaseTuple) and isinstance(objs.types[0],
        DataFrameType):
        assert all(isinstance(cckrg__itgcc, DataFrameType) for cckrg__itgcc in
            objs.types)
        nhc__mugxm = []
        for df in objs.types:
            check_runtime_cols_unsupported(df, 'pandas.concat()')
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(df,
                'pandas.concat()')
            nhc__mugxm.extend(df.columns)
        nhc__mugxm = list(dict.fromkeys(nhc__mugxm).keys())
        zzwk__dkr = {}
        for zidv__uiezc, fss__fls in enumerate(nhc__mugxm):
            for df in objs.types:
                if fss__fls in df.columns:
                    zzwk__dkr['arr_typ{}'.format(zidv__uiezc)] = df.data[df
                        .columns.index(fss__fls)]
                    break
        assert len(zzwk__dkr) == len(nhc__mugxm)
        jvmxl__cub = []
        for zidv__uiezc, fss__fls in enumerate(nhc__mugxm):
            args = []
            for i, df in enumerate(objs.types):
                if fss__fls in df.columns:
                    pjw__xrtnn = df.columns.index(fss__fls)
                    args.append(
                        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(objs[{}], {})'
                        .format(i, pjw__xrtnn))
                else:
                    args.append(
                        'bodo.libs.array_kernels.gen_na_array(len(objs[{}]), arr_typ{})'
                        .format(i, zidv__uiezc))
            hegu__ztmzk += ('  A{} = bodo.libs.array_kernels.concat(({},))\n'
                .format(zidv__uiezc, ', '.join(args)))
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
        return bodo.hiframes.dataframe_impl._gen_init_df(hegu__ztmzk,
            nhc__mugxm, ', '.join('A{}'.format(i) for i in range(len(
            nhc__mugxm))), index, zzwk__dkr)
    if isinstance(objs, types.BaseTuple) and isinstance(objs.types[0],
        SeriesType):
        assert all(isinstance(cckrg__itgcc, SeriesType) for cckrg__itgcc in
            objs.types)
        hegu__ztmzk += ('  out_arr = bodo.libs.array_kernels.concat(({},))\n'
            .format(', '.join(
            'bodo.hiframes.pd_series_ext.get_series_data(objs[{}])'.format(
            i) for i in range(len(objs.types)))))
        if ignore_index:
            hegu__ztmzk += """  index = bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr), 1, None)
"""
        else:
            hegu__ztmzk += (
                """  index = bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(({},)))
"""
                .format(', '.join(
                'bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(objs[{}]))'
                .format(i) for i in range(len(objs.types)))))
        hegu__ztmzk += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index)\n'
            )
        pok__oow = {}
        exec(hegu__ztmzk, {'bodo': bodo, 'np': np, 'numba': numba}, pok__oow)
        return pok__oow['impl']
    if isinstance(objs, types.List) and isinstance(objs.dtype, DataFrameType):
        check_runtime_cols_unsupported(objs.dtype, 'pandas.concat()')
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(objs.
            dtype, 'pandas.concat()')
        df_type = objs.dtype
        for zidv__uiezc, fss__fls in enumerate(df_type.columns):
            hegu__ztmzk += '  arrs{} = []\n'.format(zidv__uiezc)
            hegu__ztmzk += '  for i in range(len(objs)):\n'
            hegu__ztmzk += '    df = objs[i]\n'
            hegu__ztmzk += (
                """    arrs{0}.append(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {0}))
"""
                .format(zidv__uiezc))
            hegu__ztmzk += (
                '  out_arr{0} = bodo.libs.array_kernels.concat(arrs{0})\n'.
                format(zidv__uiezc))
        if ignore_index:
            index = (
                'bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr0), 1, None)'
                )
        else:
            hegu__ztmzk += '  arrs_index = []\n'
            hegu__ztmzk += '  for i in range(len(objs)):\n'
            hegu__ztmzk += '    df = objs[i]\n'
            hegu__ztmzk += """    arrs_index.append(bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)))
"""
            if objs.dtype.index.name_typ == types.none:
                name = None
            else:
                name = objs.dtype.index.name_typ.literal_value
            index = f"""bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(arrs_index), {name!r})
"""
        return bodo.hiframes.dataframe_impl._gen_init_df(hegu__ztmzk,
            df_type.columns, ', '.join('out_arr{}'.format(i) for i in range
            (len(df_type.columns))), index)
    if isinstance(objs, types.List) and isinstance(objs.dtype, SeriesType):
        hegu__ztmzk += '  arrs = []\n'
        hegu__ztmzk += '  for i in range(len(objs)):\n'
        hegu__ztmzk += (
            '    arrs.append(bodo.hiframes.pd_series_ext.get_series_data(objs[i]))\n'
            )
        hegu__ztmzk += '  out_arr = bodo.libs.array_kernels.concat(arrs)\n'
        if ignore_index:
            hegu__ztmzk += """  index = bodo.hiframes.pd_index_ext.init_range_index(0, len(out_arr), 1, None)
"""
        else:
            hegu__ztmzk += '  arrs_index = []\n'
            hegu__ztmzk += '  for i in range(len(objs)):\n'
            hegu__ztmzk += '    S = objs[i]\n'
            hegu__ztmzk += """    arrs_index.append(bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(S)))
"""
            hegu__ztmzk += """  index = bodo.utils.conversion.index_from_array(bodo.libs.array_kernels.concat(arrs_index))
"""
        hegu__ztmzk += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index)\n'
            )
        pok__oow = {}
        exec(hegu__ztmzk, {'bodo': bodo, 'np': np, 'numba': numba}, pok__oow)
        return pok__oow['impl']
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
        wcoae__vff = df.copy(index=index, is_table_format=False)
        return signature(wcoae__vff, *args)


SortDummyTyper._no_unliteral = True


@lower_builtin(sort_values_dummy, types.VarArg(types.Any))
def lower_sort_values_dummy(context, builder, sig, args):
    if sig.return_type == types.none:
        return
    nkwuw__hwmnm = cgutils.create_struct_proxy(sig.return_type)(context,
        builder)
    return nkwuw__hwmnm._getvalue()


@overload_method(DataFrameType, 'itertuples', inline='always', no_unliteral
    =True)
def itertuples_overload(df, index=True, name='Pandas'):
    check_runtime_cols_unsupported(df, 'DataFrame.itertuples()')
    qrmqv__kvh = dict(index=index, name=name)
    qcsdd__jug = dict(index=True, name='Pandas')
    check_unsupported_args('DataFrame.itertuples', qrmqv__kvh, qcsdd__jug,
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
        zzwk__dkr = (types.Array(types.int64, 1, 'C'),) + df.data
        xjq__hbq = bodo.hiframes.dataframe_impl.DataFrameTupleIterator(columns,
            zzwk__dkr)
        return signature(xjq__hbq, *args)


@lower_builtin(itertuples_dummy, types.VarArg(types.Any))
def lower_itertuples_dummy(context, builder, sig, args):
    nkwuw__hwmnm = cgutils.create_struct_proxy(sig.return_type)(context,
        builder)
    return nkwuw__hwmnm._getvalue()


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
    nkwuw__hwmnm = cgutils.create_struct_proxy(sig.return_type)(context,
        builder)
    return nkwuw__hwmnm._getvalue()


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
    nkwuw__hwmnm = cgutils.create_struct_proxy(sig.return_type)(context,
        builder)
    return nkwuw__hwmnm._getvalue()


@numba.generated_jit(nopython=True)
def pivot_impl(index_tup, columns_tup, values_tup, pivot_values,
    index_names, columns_name, value_names, check_duplicates=True, parallel
    =False):
    if not is_overload_constant_bool(check_duplicates):
        raise BodoError(
            'pivot_impl(): check_duplicates must be a constant boolean')
    fnk__kjcbx = get_overload_const_bool(check_duplicates)
    cgr__lhwhn = not is_overload_none(value_names)
    fnjx__msvo = isinstance(values_tup, types.UniTuple)
    if fnjx__msvo:
        mcyd__xpmof = [to_nullable_type(values_tup.dtype)]
    else:
        mcyd__xpmof = [to_nullable_type(pemy__ubs) for pemy__ubs in values_tup]
    hegu__ztmzk = 'def impl(\n'
    hegu__ztmzk += """    index_tup, columns_tup, values_tup, pivot_values, index_names, columns_name, value_names, check_duplicates=True, parallel=False
"""
    hegu__ztmzk += '):\n'
    hegu__ztmzk += '    if parallel:\n'
    rnj__bdw = ', '.join([f'array_to_info(index_tup[{i}])' for i in range(
        len(index_tup))] + [f'array_to_info(columns_tup[{i}])' for i in
        range(len(columns_tup))] + [f'array_to_info(values_tup[{i}])' for i in
        range(len(values_tup))])
    hegu__ztmzk += f'        info_list = [{rnj__bdw}]\n'
    hegu__ztmzk += '        cpp_table = arr_info_list_to_table(info_list)\n'
    hegu__ztmzk += f"""        out_cpp_table = shuffle_table(cpp_table, {len(index_tup)}, parallel, 0)
"""
    rzcy__kecee = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i}), index_tup[{i}])'
         for i in range(len(index_tup))])
    enitq__ces = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i + len(index_tup)}), columns_tup[{i}])'
         for i in range(len(columns_tup))])
    efhkj__cyawz = ', '.join([
        f'info_to_array(info_from_table(out_cpp_table, {i + len(index_tup) + len(columns_tup)}), values_tup[{i}])'
         for i in range(len(values_tup))])
    hegu__ztmzk += f'        index_tup = ({rzcy__kecee},)\n'
    hegu__ztmzk += f'        columns_tup = ({enitq__ces},)\n'
    hegu__ztmzk += f'        values_tup = ({efhkj__cyawz},)\n'
    hegu__ztmzk += '        delete_table(cpp_table)\n'
    hegu__ztmzk += '        delete_table(out_cpp_table)\n'
    hegu__ztmzk += '    columns_arr = columns_tup[0]\n'
    if fnjx__msvo:
        hegu__ztmzk += '    values_arrs = [arr for arr in values_tup]\n'
    hegu__ztmzk += """    unique_index_arr_tup, row_vector = bodo.libs.array_ops.array_unique_vector_map(
"""
    hegu__ztmzk += '        index_tup\n'
    hegu__ztmzk += '    )\n'
    hegu__ztmzk += '    n_rows = len(unique_index_arr_tup[0])\n'
    hegu__ztmzk += '    num_values_arrays = len(values_tup)\n'
    hegu__ztmzk += '    n_unique_pivots = len(pivot_values)\n'
    if fnjx__msvo:
        hegu__ztmzk += '    n_cols = num_values_arrays * n_unique_pivots\n'
    else:
        hegu__ztmzk += '    n_cols = n_unique_pivots\n'
    hegu__ztmzk += '    col_map = {}\n'
    hegu__ztmzk += '    for i in range(n_unique_pivots):\n'
    hegu__ztmzk += (
        '        if bodo.libs.array_kernels.isna(pivot_values, i):\n')
    hegu__ztmzk += '            raise ValueError(\n'
    hegu__ztmzk += """                "DataFrame.pivot(): NA values in 'columns' array not supported\"
"""
    hegu__ztmzk += '            )\n'
    hegu__ztmzk += '        col_map[pivot_values[i]] = i\n'
    vwhx__hjf = False
    for i, dht__dqwj in enumerate(mcyd__xpmof):
        if is_str_arr_type(dht__dqwj):
            vwhx__hjf = True
            hegu__ztmzk += f"""    len_arrs_{i} = [np.zeros(n_rows, np.int64) for _ in range(n_cols)]
"""
            hegu__ztmzk += f'    total_lens_{i} = np.zeros(n_cols, np.int64)\n'
    if vwhx__hjf:
        if fnk__kjcbx:
            hegu__ztmzk += '    nbytes = (n_rows + 7) >> 3\n'
            hegu__ztmzk += """    seen_bitmaps = [np.zeros(nbytes, np.int8) for _ in range(n_unique_pivots)]
"""
        hegu__ztmzk += '    for i in range(len(columns_arr)):\n'
        hegu__ztmzk += '        col_name = columns_arr[i]\n'
        hegu__ztmzk += '        pivot_idx = col_map[col_name]\n'
        hegu__ztmzk += '        row_idx = row_vector[i]\n'
        if fnk__kjcbx:
            hegu__ztmzk += '        seen_bitmap = seen_bitmaps[pivot_idx]\n'
            hegu__ztmzk += """        if bodo.libs.int_arr_ext.get_bit_bitmap_arr(seen_bitmap, row_idx):
"""
            hegu__ztmzk += """            raise ValueError("DataFrame.pivot(): 'index' contains duplicate entries for the same output column")
"""
            hegu__ztmzk += '        else:\n'
            hegu__ztmzk += """            bodo.libs.int_arr_ext.set_bit_to_arr(seen_bitmap, row_idx, 1)
"""
        if fnjx__msvo:
            hegu__ztmzk += '        for j in range(num_values_arrays):\n'
            hegu__ztmzk += (
                '            col_idx = (j * len(pivot_values)) + pivot_idx\n')
            hegu__ztmzk += '            len_arr = len_arrs_0[col_idx]\n'
            hegu__ztmzk += '            values_arr = values_arrs[j]\n'
            hegu__ztmzk += (
                '            if not bodo.libs.array_kernels.isna(values_arr, i):\n'
                )
            hegu__ztmzk += (
                '                len_arr[row_idx] = len(values_arr[i])\n')
            hegu__ztmzk += (
                '                total_lens_0[col_idx] += len(values_arr[i])\n'
                )
        else:
            for i, dht__dqwj in enumerate(mcyd__xpmof):
                if is_str_arr_type(dht__dqwj):
                    hegu__ztmzk += f"""        if not bodo.libs.array_kernels.isna(values_tup[{i}], i):
"""
                    hegu__ztmzk += f"""            len_arrs_{i}[pivot_idx][row_idx] = len(values_tup[{i}][i])
"""
                    hegu__ztmzk += f"""            total_lens_{i}[pivot_idx] += len(values_tup[{i}][i])
"""
    for i, dht__dqwj in enumerate(mcyd__xpmof):
        if is_str_arr_type(dht__dqwj):
            hegu__ztmzk += f'    data_arrs_{i} = [\n'
            hegu__ztmzk += (
                '        bodo.libs.str_arr_ext.gen_na_str_array_lens(\n')
            hegu__ztmzk += (
                f'            n_rows, total_lens_{i}[i], len_arrs_{i}[i]\n')
            hegu__ztmzk += '        )\n'
            hegu__ztmzk += '        for i in range(n_cols)\n'
            hegu__ztmzk += '    ]\n'
        else:
            hegu__ztmzk += f'    data_arrs_{i} = [\n'
            hegu__ztmzk += f"""        bodo.libs.array_kernels.gen_na_array(n_rows, data_arr_typ_{i})
"""
            hegu__ztmzk += '        for _ in range(n_cols)\n'
            hegu__ztmzk += '    ]\n'
    if not vwhx__hjf and fnk__kjcbx:
        hegu__ztmzk += '    nbytes = (n_rows + 7) >> 3\n'
        hegu__ztmzk += """    seen_bitmaps = [np.zeros(nbytes, np.int8) for _ in range(n_unique_pivots)]
"""
    hegu__ztmzk += '    for i in range(len(columns_arr)):\n'
    hegu__ztmzk += '        col_name = columns_arr[i]\n'
    hegu__ztmzk += '        pivot_idx = col_map[col_name]\n'
    hegu__ztmzk += '        row_idx = row_vector[i]\n'
    if not vwhx__hjf and fnk__kjcbx:
        hegu__ztmzk += '        seen_bitmap = seen_bitmaps[pivot_idx]\n'
        hegu__ztmzk += """        if bodo.libs.int_arr_ext.get_bit_bitmap_arr(seen_bitmap, row_idx):
"""
        hegu__ztmzk += """            raise ValueError("DataFrame.pivot(): 'index' contains duplicate entries for the same output column")
"""
        hegu__ztmzk += '        else:\n'
        hegu__ztmzk += """            bodo.libs.int_arr_ext.set_bit_to_arr(seen_bitmap, row_idx, 1)
"""
    if fnjx__msvo:
        hegu__ztmzk += '        for j in range(num_values_arrays):\n'
        hegu__ztmzk += (
            '            col_idx = (j * len(pivot_values)) + pivot_idx\n')
        hegu__ztmzk += '            col_arr = data_arrs_0[col_idx]\n'
        hegu__ztmzk += '            values_arr = values_arrs[j]\n'
        hegu__ztmzk += (
            '            if bodo.libs.array_kernels.isna(values_arr, i):\n')
        hegu__ztmzk += (
            '                bodo.libs.array_kernels.setna(col_arr, row_idx)\n'
            )
        hegu__ztmzk += '            else:\n'
        hegu__ztmzk += '                col_arr[row_idx] = values_arr[i]\n'
    else:
        for i, dht__dqwj in enumerate(mcyd__xpmof):
            hegu__ztmzk += f'        col_arr_{i} = data_arrs_{i}[pivot_idx]\n'
            hegu__ztmzk += (
                f'        if bodo.libs.array_kernels.isna(values_tup[{i}], i):\n'
                )
            hegu__ztmzk += (
                f'            bodo.libs.array_kernels.setna(col_arr_{i}, row_idx)\n'
                )
            hegu__ztmzk += f'        else:\n'
            hegu__ztmzk += (
                f'            col_arr_{i}[row_idx] = values_tup[{i}][i]\n')
    if len(index_tup) == 1:
        hegu__ztmzk += """    index = bodo.utils.conversion.index_from_array(unique_index_arr_tup[0], index_names[0])
"""
    else:
        hegu__ztmzk += """    index = bodo.hiframes.pd_multi_index_ext.init_multi_index(unique_index_arr_tup, index_names, None)
"""
    if cgr__lhwhn:
        hegu__ztmzk += '    num_rows = len(value_names) * len(pivot_values)\n'
        if is_str_arr_type(value_names):
            hegu__ztmzk += '    total_chars = 0\n'
            hegu__ztmzk += '    for i in range(len(value_names)):\n'
            hegu__ztmzk += '        total_chars += len(value_names[i])\n'
            hegu__ztmzk += """    new_value_names = bodo.libs.str_arr_ext.pre_alloc_string_array(num_rows, total_chars * len(pivot_values))
"""
        else:
            hegu__ztmzk += """    new_value_names = bodo.utils.utils.alloc_type(num_rows, value_names, (-1,))
"""
        if is_str_arr_type(pivot_values):
            hegu__ztmzk += '    total_chars = 0\n'
            hegu__ztmzk += '    for i in range(len(pivot_values)):\n'
            hegu__ztmzk += '        total_chars += len(pivot_values[i])\n'
            hegu__ztmzk += """    new_pivot_values = bodo.libs.str_arr_ext.pre_alloc_string_array(num_rows, total_chars * len(value_names))
"""
        else:
            hegu__ztmzk += """    new_pivot_values = bodo.utils.utils.alloc_type(num_rows, pivot_values, (-1,))
"""
        hegu__ztmzk += '    for i in range(len(value_names)):\n'
        hegu__ztmzk += '        for j in range(len(pivot_values)):\n'
        hegu__ztmzk += """            new_value_names[(i * len(pivot_values)) + j] = value_names[i]
"""
        hegu__ztmzk += """            new_pivot_values[(i * len(pivot_values)) + j] = pivot_values[j]
"""
        hegu__ztmzk += """    column_index = bodo.hiframes.pd_multi_index_ext.init_multi_index((new_value_names, new_pivot_values), (None, columns_name), None)
"""
    else:
        hegu__ztmzk += """    column_index =  bodo.utils.conversion.index_from_array(pivot_values, columns_name)
"""
    qmoi__blmv = ', '.join(f'data_arrs_{i}' for i in range(len(mcyd__xpmof)))
    hegu__ztmzk += f"""    table = bodo.hiframes.table.init_runtime_table_from_lists(({qmoi__blmv},), n_rows)
"""
    hegu__ztmzk += (
        '    return bodo.hiframes.pd_dataframe_ext.init_runtime_cols_dataframe(\n'
        )
    hegu__ztmzk += '        (table,), index, column_index\n'
    hegu__ztmzk += '    )\n'
    pok__oow = {}
    mhs__dywu = {f'data_arr_typ_{i}': dht__dqwj for i, dht__dqwj in
        enumerate(mcyd__xpmof)}
    ywmy__cneto = {'bodo': bodo, 'np': np, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table, 'shuffle_table':
        shuffle_table, 'info_to_array': info_to_array, 'delete_table':
        delete_table, 'info_from_table': info_from_table, **mhs__dywu}
    exec(hegu__ztmzk, ywmy__cneto, pok__oow)
    impl = pok__oow['impl']
    return impl


def gen_pandas_parquet_metadata(column_names, data_types, index,
    write_non_range_index_to_metadata, write_rangeindex_to_metadata,
    partition_cols=None, is_runtime_columns=False):
    nfse__cqr = {}
    nfse__cqr['columns'] = []
    if partition_cols is None:
        partition_cols = []
    for col_name, gqa__ywj in zip(column_names, data_types):
        if col_name in partition_cols:
            continue
        oquzy__iwv = None
        if isinstance(gqa__ywj, bodo.DatetimeArrayType):
            afz__xhf = 'datetimetz'
            lcbuj__botux = 'datetime64[ns]'
            if isinstance(gqa__ywj.tz, int):
                uozuw__zrw = (bodo.libs.pd_datetime_arr_ext.
                    nanoseconds_to_offset(gqa__ywj.tz))
            else:
                uozuw__zrw = pd.DatetimeTZDtype(tz=gqa__ywj.tz).tz
            oquzy__iwv = {'timezone': pa.lib.tzinfo_to_string(uozuw__zrw)}
        elif isinstance(gqa__ywj, types.Array) or gqa__ywj == boolean_array:
            afz__xhf = lcbuj__botux = gqa__ywj.dtype.name
            if lcbuj__botux.startswith('datetime'):
                afz__xhf = 'datetime'
        elif is_str_arr_type(gqa__ywj):
            afz__xhf = 'unicode'
            lcbuj__botux = 'object'
        elif gqa__ywj == binary_array_type:
            afz__xhf = 'bytes'
            lcbuj__botux = 'object'
        elif isinstance(gqa__ywj, DecimalArrayType):
            afz__xhf = lcbuj__botux = 'object'
        elif isinstance(gqa__ywj, IntegerArrayType):
            sszd__endna = gqa__ywj.dtype.name
            if sszd__endna.startswith('int'):
                afz__xhf = 'Int' + sszd__endna[3:]
            elif sszd__endna.startswith('uint'):
                afz__xhf = 'UInt' + sszd__endna[4:]
            else:
                if is_runtime_columns:
                    col_name = 'Runtime determined column of type'
                raise BodoError(
                    'to_parquet(): unknown dtype in nullable Integer column {} {}'
                    .format(col_name, gqa__ywj))
            lcbuj__botux = gqa__ywj.dtype.name
        elif gqa__ywj == datetime_date_array_type:
            afz__xhf = 'datetime'
            lcbuj__botux = 'object'
        elif isinstance(gqa__ywj, (StructArrayType, ArrayItemArrayType)):
            afz__xhf = 'object'
            lcbuj__botux = 'object'
        else:
            if is_runtime_columns:
                col_name = 'Runtime determined column of type'
            raise BodoError(
                'to_parquet(): unsupported column type for metadata generation : {} {}'
                .format(col_name, gqa__ywj))
        ygszd__fdqkw = {'name': col_name, 'field_name': col_name,
            'pandas_type': afz__xhf, 'numpy_type': lcbuj__botux, 'metadata':
            oquzy__iwv}
        nfse__cqr['columns'].append(ygszd__fdqkw)
    if write_non_range_index_to_metadata:
        if isinstance(index, MultiIndexType):
            raise BodoError('to_parquet: MultiIndex not supported yet')
        if 'none' in index.name:
            lwlu__yswgu = '__index_level_0__'
            gpjp__uxuhe = None
        else:
            lwlu__yswgu = '%s'
            gpjp__uxuhe = '%s'
        nfse__cqr['index_columns'] = [lwlu__yswgu]
        nfse__cqr['columns'].append({'name': gpjp__uxuhe, 'field_name':
            lwlu__yswgu, 'pandas_type': index.pandas_type_name,
            'numpy_type': index.numpy_type_name, 'metadata': None})
    elif write_rangeindex_to_metadata:
        nfse__cqr['index_columns'] = [{'kind': 'range', 'name': '%s',
            'start': '%d', 'stop': '%d', 'step': '%d'}]
    else:
        nfse__cqr['index_columns'] = []
    nfse__cqr['pandas_version'] = pd.__version__
    return nfse__cqr


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
        pawe__wcxp = []
        for qxrr__vxm in partition_cols:
            try:
                idx = df.columns.index(qxrr__vxm)
            except ValueError as gdf__qmyxt:
                raise BodoError(
                    f'Partition column {qxrr__vxm} is not in dataframe')
            pawe__wcxp.append(idx)
    else:
        partition_cols = None
    if not is_overload_none(index) and not is_overload_constant_bool(index):
        raise BodoError('to_parquet(): index must be a constant bool or None')
    from bodo.io.parquet_pio import parquet_write_table_cpp, parquet_write_table_partitioned_cpp
    hti__vrqhj = isinstance(df.index, bodo.hiframes.pd_index_ext.RangeIndexType
        )
    hmcr__fqk = df.index is not None and (is_overload_true(_is_parallel) or
        not is_overload_true(_is_parallel) and not hti__vrqhj)
    write_non_range_index_to_metadata = is_overload_true(index
        ) or is_overload_none(index) and (not hti__vrqhj or
        is_overload_true(_is_parallel))
    write_rangeindex_to_metadata = is_overload_none(index
        ) and hti__vrqhj and not is_overload_true(_is_parallel)
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
        swhb__remrq = df.runtime_data_types
        mgdht__jvfn = len(swhb__remrq)
        oquzy__iwv = gen_pandas_parquet_metadata([''] * mgdht__jvfn,
            swhb__remrq, df.index, write_non_range_index_to_metadata,
            write_rangeindex_to_metadata, partition_cols=partition_cols,
            is_runtime_columns=True)
        tmz__vth = oquzy__iwv['columns'][:mgdht__jvfn]
        oquzy__iwv['columns'] = oquzy__iwv['columns'][mgdht__jvfn:]
        tmz__vth = [json.dumps(ski__lvaw).replace('""', '{0}') for
            ski__lvaw in tmz__vth]
        gmldt__jjy = json.dumps(oquzy__iwv)
        zywjf__fjknv = '"columns": ['
        amdw__kvp = gmldt__jjy.find(zywjf__fjknv)
        if amdw__kvp == -1:
            raise BodoError(
                'DataFrame.to_parquet(): Unexpected metadata string for runtime columns.  Please return the DataFrame to regular Python to update typing information.'
                )
        jqkhp__oqw = amdw__kvp + len(zywjf__fjknv)
        phzfs__wie = gmldt__jjy[:jqkhp__oqw]
        gmldt__jjy = gmldt__jjy[jqkhp__oqw:]
        eigz__zkp = len(oquzy__iwv['columns'])
    else:
        gmldt__jjy = json.dumps(gen_pandas_parquet_metadata(df.columns, df.
            data, df.index, write_non_range_index_to_metadata,
            write_rangeindex_to_metadata, partition_cols=partition_cols,
            is_runtime_columns=False))
    if not is_overload_true(_is_parallel) and hti__vrqhj:
        gmldt__jjy = gmldt__jjy.replace('"%d"', '%d')
        if df.index.name == 'RangeIndexType(none)':
            gmldt__jjy = gmldt__jjy.replace('"%s"', '%s')
    if not df.is_table_format:
        oqb__xlofm = ', '.join(
            'array_to_info(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}))'
            .format(i) for i in range(len(df.columns)))
    hegu__ztmzk = """def df_to_parquet(df, fname, engine='auto', compression='snappy', index=None, partition_cols=None, storage_options=None, _is_parallel=False):
"""
    if df.is_table_format:
        hegu__ztmzk += '    py_table = get_dataframe_table(df)\n'
        hegu__ztmzk += (
            '    table = py_table_to_cpp_table(py_table, py_table_typ)\n')
    else:
        hegu__ztmzk += '    info_list = [{}]\n'.format(oqb__xlofm)
        hegu__ztmzk += '    table = arr_info_list_to_table(info_list)\n'
    if df.has_runtime_cols:
        hegu__ztmzk += '    columns_index = get_dataframe_column_names(df)\n'
        hegu__ztmzk += '    names_arr = index_to_array(columns_index)\n'
        hegu__ztmzk += '    col_names = array_to_info(names_arr)\n'
    else:
        hegu__ztmzk += '    col_names = array_to_info(col_names_arr)\n'
    if is_overload_true(index) or is_overload_none(index) and hmcr__fqk:
        hegu__ztmzk += """    index_col = array_to_info(index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)))
"""
        huqh__ivwa = True
    else:
        hegu__ztmzk += '    index_col = array_to_info(np.empty(0))\n'
        huqh__ivwa = False
    if df.has_runtime_cols:
        hegu__ztmzk += '    columns_lst = []\n'
        hegu__ztmzk += '    num_cols = 0\n'
        for i in range(len(df.runtime_data_types)):
            hegu__ztmzk += f'    for _ in range(len(py_table.block_{i})):\n'
            hegu__ztmzk += f"""        columns_lst.append({tmz__vth[i]!r}.replace('{{0}}', '"' + names_arr[num_cols] + '"'))
"""
            hegu__ztmzk += '        num_cols += 1\n'
        if eigz__zkp:
            hegu__ztmzk += "    columns_lst.append('')\n"
        hegu__ztmzk += '    columns_str = ", ".join(columns_lst)\n'
        hegu__ztmzk += ('    metadata = """' + phzfs__wie +
            '""" + columns_str + """' + gmldt__jjy + '"""\n')
    else:
        hegu__ztmzk += '    metadata = """' + gmldt__jjy + '"""\n'
    hegu__ztmzk += '    if compression is None:\n'
    hegu__ztmzk += "        compression = 'none'\n"
    hegu__ztmzk += '    if df.index.name is not None:\n'
    hegu__ztmzk += '        name_ptr = df.index.name\n'
    hegu__ztmzk += '    else:\n'
    hegu__ztmzk += "        name_ptr = 'null'\n"
    hegu__ztmzk += f"""    bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel=_is_parallel)
"""
    amatb__sebzh = None
    if partition_cols:
        amatb__sebzh = pd.array([col_name for col_name in df.columns if 
            col_name not in partition_cols])
        gbhpx__svp = ', '.join(
            f'array_to_info(bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {i}).dtype.categories.values)'
             for i in range(len(df.columns)) if isinstance(df.data[i],
            CategoricalArrayType) and i in pawe__wcxp)
        if gbhpx__svp:
            hegu__ztmzk += '    cat_info_list = [{}]\n'.format(gbhpx__svp)
            hegu__ztmzk += (
                '    cat_table = arr_info_list_to_table(cat_info_list)\n')
        else:
            hegu__ztmzk += '    cat_table = table\n'
        hegu__ztmzk += (
            '    col_names_no_partitions = array_to_info(col_names_no_parts_arr)\n'
            )
        hegu__ztmzk += (
            f'    part_cols_idxs = np.array({pawe__wcxp}, dtype=np.int32)\n')
        hegu__ztmzk += (
            '    parquet_write_table_partitioned_cpp(unicode_to_utf8(fname),\n'
            )
        hegu__ztmzk += """                            table, col_names, col_names_no_partitions, cat_table,
"""
        hegu__ztmzk += (
            '                            part_cols_idxs.ctypes, len(part_cols_idxs),\n'
            )
        hegu__ztmzk += (
            '                            unicode_to_utf8(compression),\n')
        hegu__ztmzk += '                            _is_parallel,\n'
        hegu__ztmzk += (
            '                            unicode_to_utf8(bucket_region))\n')
        hegu__ztmzk += '    delete_table_decref_arrays(table)\n'
        hegu__ztmzk += '    delete_info_decref_array(index_col)\n'
        hegu__ztmzk += (
            '    delete_info_decref_array(col_names_no_partitions)\n')
        hegu__ztmzk += '    delete_info_decref_array(col_names)\n'
        if gbhpx__svp:
            hegu__ztmzk += '    delete_table_decref_arrays(cat_table)\n'
    elif write_rangeindex_to_metadata:
        hegu__ztmzk += '    parquet_write_table_cpp(unicode_to_utf8(fname),\n'
        hegu__ztmzk += (
            '                            table, col_names, index_col,\n')
        hegu__ztmzk += '                            ' + str(huqh__ivwa) + ',\n'
        hegu__ztmzk += (
            '                            unicode_to_utf8(metadata),\n')
        hegu__ztmzk += (
            '                            unicode_to_utf8(compression),\n')
        hegu__ztmzk += (
            '                            _is_parallel, 1, df.index.start,\n')
        hegu__ztmzk += (
            '                            df.index.stop, df.index.step,\n')
        hegu__ztmzk += (
            '                            unicode_to_utf8(name_ptr),\n')
        hegu__ztmzk += (
            '                            unicode_to_utf8(bucket_region))\n')
        hegu__ztmzk += '    delete_table_decref_arrays(table)\n'
        hegu__ztmzk += '    delete_info_decref_array(index_col)\n'
        hegu__ztmzk += '    delete_info_decref_array(col_names)\n'
    else:
        hegu__ztmzk += '    parquet_write_table_cpp(unicode_to_utf8(fname),\n'
        hegu__ztmzk += (
            '                            table, col_names, index_col,\n')
        hegu__ztmzk += '                            ' + str(huqh__ivwa) + ',\n'
        hegu__ztmzk += (
            '                            unicode_to_utf8(metadata),\n')
        hegu__ztmzk += (
            '                            unicode_to_utf8(compression),\n')
        hegu__ztmzk += (
            '                            _is_parallel, 0, 0, 0, 0,\n')
        hegu__ztmzk += (
            '                            unicode_to_utf8(name_ptr),\n')
        hegu__ztmzk += (
            '                            unicode_to_utf8(bucket_region))\n')
        hegu__ztmzk += '    delete_table_decref_arrays(table)\n'
        hegu__ztmzk += '    delete_info_decref_array(index_col)\n'
        hegu__ztmzk += '    delete_info_decref_array(col_names)\n'
    pok__oow = {}
    if df.has_runtime_cols:
        pkm__ngpw = None
    else:
        for uhgvv__eng in df.columns:
            if not isinstance(uhgvv__eng, str):
                raise BodoError(
                    'DataFrame.to_parquet(): parquet must have string column names'
                    )
        pkm__ngpw = pd.array(df.columns)
    exec(hegu__ztmzk, {'np': np, 'bodo': bodo, 'unicode_to_utf8':
        unicode_to_utf8, 'array_to_info': array_to_info,
        'arr_info_list_to_table': arr_info_list_to_table,
        'str_arr_from_sequence': str_arr_from_sequence,
        'parquet_write_table_cpp': parquet_write_table_cpp,
        'parquet_write_table_partitioned_cpp':
        parquet_write_table_partitioned_cpp, 'index_to_array':
        index_to_array, 'delete_info_decref_array':
        delete_info_decref_array, 'delete_table_decref_arrays':
        delete_table_decref_arrays, 'col_names_arr': pkm__ngpw,
        'py_table_to_cpp_table': py_table_to_cpp_table, 'py_table_typ': df.
        table_type, 'get_dataframe_table': get_dataframe_table,
        'col_names_no_parts_arr': amatb__sebzh,
        'get_dataframe_column_names': get_dataframe_column_names,
        'fix_arr_dtype': fix_arr_dtype, 'decode_if_dict_array':
        decode_if_dict_array, 'decode_if_dict_table': decode_if_dict_table},
        pok__oow)
    hpili__gevtr = pok__oow['df_to_parquet']
    return hpili__gevtr


def to_sql_exception_guard(df, name, con, schema=None, if_exists='fail',
    index=True, index_label=None, chunksize=None, dtype=None, method=None,
    _is_table_create=False, _is_parallel=False):
    tqr__dabna = 'all_ok'
    eyq__labb = urlparse(con).scheme
    if _is_parallel and bodo.get_rank() == 0:
        gmexh__xfkwd = 100
        if chunksize is None:
            dibit__mou = gmexh__xfkwd
        else:
            dibit__mou = min(chunksize, gmexh__xfkwd)
        if _is_table_create:
            df = df.iloc[:dibit__mou, :]
        else:
            df = df.iloc[dibit__mou:, :]
            if len(df) == 0:
                return tqr__dabna
    if eyq__labb == 'snowflake':
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
            df.columns = [(fss__fls.upper() if fss__fls.islower() else
                fss__fls) for fss__fls in df.columns]
        except ImportError as gdf__qmyxt:
            tqr__dabna = (
                "Snowflake Python connector packages not found. Using 'to_sql' with Snowflake requires both snowflake-sqlalchemy and snowflake-connector-python. These can be installed by calling 'conda install -c conda-forge snowflake-sqlalchemy snowflake-connector-python' or 'pip install snowflake-sqlalchemy snowflake-connector-python'."
                )
            return tqr__dabna
    try:
        df.to_sql(name, con, schema, if_exists, index, index_label,
            chunksize, dtype, method)
    except Exception as vxmz__hxad:
        tqr__dabna = vxmz__hxad.args[0]
    return tqr__dabna


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
        jfkkb__imgdh = bodo.libs.distributed_api.get_rank()
        tqr__dabna = 'unset'
        if jfkkb__imgdh != 0:
            tqr__dabna = bcast_scalar(tqr__dabna)
        elif jfkkb__imgdh == 0:
            tqr__dabna = to_sql_exception_guard_encaps(df, name, con,
                schema, if_exists, index, index_label, chunksize, dtype,
                method, True, _is_parallel)
            tqr__dabna = bcast_scalar(tqr__dabna)
        if_exists = 'append'
        if _is_parallel and tqr__dabna == 'all_ok':
            tqr__dabna = to_sql_exception_guard_encaps(df, name, con,
                schema, if_exists, index, index_label, chunksize, dtype,
                method, False, _is_parallel)
        if tqr__dabna != 'all_ok':
            print('err_msg=', tqr__dabna)
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
        vdcv__kcmxf = get_overload_const_str(path_or_buf)
        if vdcv__kcmxf.endswith(('.gz', '.bz2', '.zip', '.xz')):
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
        mskmq__uttd = bodo.io.fs_io.get_s3_bucket_region_njit(path_or_buf,
            parallel=False)
        if lines and orient == 'records':
            bodo.hiframes.pd_dataframe_ext._json_write(unicode_to_utf8(
                path_or_buf), unicode_to_utf8(D), 0, len(D), False, True,
                unicode_to_utf8(mskmq__uttd))
            bodo.utils.utils.check_and_propagate_cpp_exception()
        else:
            bodo.hiframes.pd_dataframe_ext._json_write(unicode_to_utf8(
                path_or_buf), unicode_to_utf8(D), 0, len(D), False, False,
                unicode_to_utf8(mskmq__uttd))
            bodo.utils.utils.check_and_propagate_cpp_exception()
    return _impl


@overload(pd.get_dummies, inline='always', no_unliteral=True)
def get_dummies(data, prefix=None, prefix_sep='_', dummy_na=False, columns=
    None, sparse=False, drop_first=False, dtype=None):
    xlq__tawk = {'prefix': prefix, 'prefix_sep': prefix_sep, 'dummy_na':
        dummy_na, 'columns': columns, 'sparse': sparse, 'drop_first':
        drop_first, 'dtype': dtype}
    flprn__qbp = {'prefix': None, 'prefix_sep': '_', 'dummy_na': False,
        'columns': None, 'sparse': False, 'drop_first': False, 'dtype': None}
    check_unsupported_args('pandas.get_dummies', xlq__tawk, flprn__qbp,
        package_name='pandas', module_name='General')
    if not categorical_can_construct_dataframe(data):
        raise BodoError(
            'pandas.get_dummies() only support categorical data types with explicitly known categories'
            )
    hegu__ztmzk = """def impl(data, prefix=None, prefix_sep='_', dummy_na=False, columns=None, sparse=False, drop_first=False, dtype=None,):
"""
    if isinstance(data, SeriesType):
        xzty__xomt = data.data.dtype.categories
        hegu__ztmzk += (
            '  data_values = bodo.hiframes.pd_series_ext.get_series_data(data)\n'
            )
    else:
        xzty__xomt = data.dtype.categories
        hegu__ztmzk += '  data_values = data\n'
    gzkxu__mqt = len(xzty__xomt)
    hegu__ztmzk += """  codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(data_values)
"""
    hegu__ztmzk += '  numba.parfors.parfor.init_prange()\n'
    hegu__ztmzk += '  n = len(data_values)\n'
    for i in range(gzkxu__mqt):
        hegu__ztmzk += '  data_arr_{} = np.empty(n, np.uint8)\n'.format(i)
    hegu__ztmzk += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    hegu__ztmzk += '      if bodo.libs.array_kernels.isna(data_values, i):\n'
    for kspt__gdtup in range(gzkxu__mqt):
        hegu__ztmzk += '          data_arr_{}[i] = 0\n'.format(kspt__gdtup)
    hegu__ztmzk += '      else:\n'
    for ezkx__fjinp in range(gzkxu__mqt):
        hegu__ztmzk += '          data_arr_{0}[i] = codes[i] == {0}\n'.format(
            ezkx__fjinp)
    oqb__xlofm = ', '.join(f'data_arr_{i}' for i in range(gzkxu__mqt))
    index = 'bodo.hiframes.pd_index_ext.init_range_index(0, n, 1, None)'
    if isinstance(xzty__xomt[0], np.datetime64):
        xzty__xomt = tuple(pd.Timestamp(fss__fls) for fss__fls in xzty__xomt)
    elif isinstance(xzty__xomt[0], np.timedelta64):
        xzty__xomt = tuple(pd.Timedelta(fss__fls) for fss__fls in xzty__xomt)
    return bodo.hiframes.dataframe_impl._gen_init_df(hegu__ztmzk,
        xzty__xomt, oqb__xlofm, index)


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
    for ahe__ddpwj in pd_unsupported:
        fname = mod_name + '.' + ahe__ddpwj.__name__
        overload(ahe__ddpwj, no_unliteral=True)(create_unsupported_overload
            (fname))


def _install_dataframe_unsupported():
    for kwmz__jfq in dataframe_unsupported_attrs:
        enqc__pzo = 'DataFrame.' + kwmz__jfq
        overload_attribute(DataFrameType, kwmz__jfq)(
            create_unsupported_overload(enqc__pzo))
    for fname in dataframe_unsupported:
        enqc__pzo = 'DataFrame.' + fname + '()'
        overload_method(DataFrameType, fname)(create_unsupported_overload(
            enqc__pzo))


_install_pd_unsupported('pandas', pd_unsupported)
_install_pd_unsupported('pandas.util', pd_util_unsupported)
_install_dataframe_unsupported()
