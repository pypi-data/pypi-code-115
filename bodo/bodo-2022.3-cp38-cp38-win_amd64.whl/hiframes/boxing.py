"""
Boxing and unboxing support for DataFrame, Series, etc.
"""
import datetime
import decimal
import warnings
from enum import Enum
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.ir_utils import GuardException, guard
from numba.core.typing import signature
from numba.cpython.listobj import ListInstance
from numba.extending import NativeValue, box, intrinsic, typeof_impl, unbox
from numba.np import numpy_support
from numba.typed.typeddict import Dict
import bodo
from bodo.hiframes.datetime_date_ext import datetime_date_array_type
from bodo.hiframes.datetime_timedelta_ext import datetime_timedelta_array_type
from bodo.hiframes.pd_categorical_ext import PDCategoricalDtype
from bodo.hiframes.pd_dataframe_ext import DataFramePayloadType, DataFrameType, check_runtime_cols_unsupported, construct_dataframe
from bodo.hiframes.pd_index_ext import BinaryIndexType, CategoricalIndexType, DatetimeIndexType, NumericIndexType, PeriodIndexType, RangeIndexType, StringIndexType, TimedeltaIndexType
from bodo.hiframes.pd_series_ext import HeterogeneousSeriesType, SeriesType
from bodo.hiframes.split_impl import string_array_split_view_type
from bodo.libs import hstr_ext
from bodo.libs.array_item_arr_ext import ArrayItemArrayType
from bodo.libs.binary_arr_ext import binary_array_type, bytes_type
from bodo.libs.decimal_arr_ext import Decimal128Type, DecimalArrayType
from bodo.libs.int_arr_ext import IntDtype, IntegerArrayType, typeof_pd_int_dtype
from bodo.libs.map_arr_ext import MapArrayType
from bodo.libs.pd_datetime_arr_ext import DatetimeArrayType, PandasDatetimeTZDtype
from bodo.libs.str_arr_ext import string_array_type, string_type
from bodo.libs.str_ext import string_type
from bodo.libs.struct_arr_ext import StructArrayType, StructType
from bodo.libs.tuple_arr_ext import TupleArrayType
from bodo.utils.cg_helpers import is_ll_eq
from bodo.utils.typing import BodoError, BodoWarning, dtype_to_array_type, get_overload_const_bool, get_overload_const_int, get_overload_const_str, is_overload_constant_bool, is_overload_constant_int, is_overload_constant_str, raise_bodo_error, to_nullable_type, to_str_arr_if_dict_array
ll.add_symbol('is_np_array', hstr_ext.is_np_array)
ll.add_symbol('array_size', hstr_ext.array_size)
ll.add_symbol('array_getptr1', hstr_ext.array_getptr1)
TABLE_FORMAT_THRESHOLD = 20
_use_dict_str_type = False


def _set_bodo_meta_in_pandas():
    if '_bodo_meta' not in pd.Series._metadata:
        pd.Series._metadata.append('_bodo_meta')
    if '_bodo_meta' not in pd.DataFrame._metadata:
        pd.DataFrame._metadata.append('_bodo_meta')


_set_bodo_meta_in_pandas()


@typeof_impl.register(pd.DataFrame)
def typeof_pd_dataframe(val, c):
    from bodo.transforms.distributed_analysis import Distribution
    ysp__kqos = tuple(val.columns.to_list())
    hoh__ugs = get_hiframes_dtypes(val)
    if (len(val.index) == 0 and val.index.dtype == np.dtype('O') and
        hasattr(val, '_bodo_meta') and val._bodo_meta is not None and 
        'type_metadata' in val._bodo_meta and val._bodo_meta[
        'type_metadata'] is not None and len(val._bodo_meta['type_metadata'
        ][1]) == len(val.columns) and val._bodo_meta['type_metadata'][0] is not
        None):
        bgmcu__xsl = _dtype_from_type_enum_list(val._bodo_meta[
            'type_metadata'][0])
    else:
        bgmcu__xsl = numba.typeof(val.index)
    mmo__xkvg = Distribution(val._bodo_meta['dist']) if hasattr(val,
        '_bodo_meta') and val._bodo_meta is not None else Distribution.REP
    ljc__xslh = len(hoh__ugs) >= TABLE_FORMAT_THRESHOLD
    return DataFrameType(hoh__ugs, bgmcu__xsl, ysp__kqos, mmo__xkvg,
        is_table_format=ljc__xslh)


@typeof_impl.register(pd.Series)
def typeof_pd_series(val, c):
    from bodo.transforms.distributed_analysis import Distribution
    mmo__xkvg = Distribution(val._bodo_meta['dist']) if hasattr(val,
        '_bodo_meta') and val._bodo_meta is not None else Distribution.REP
    if (len(val.index) == 0 and val.index.dtype == np.dtype('O') and
        hasattr(val, '_bodo_meta') and val._bodo_meta is not None and 
        'type_metadata' in val._bodo_meta and val._bodo_meta[
        'type_metadata'] is not None and val._bodo_meta['type_metadata'][0]
         is not None):
        hmlu__zgbp = _dtype_from_type_enum_list(val._bodo_meta[
            'type_metadata'][0])
    else:
        hmlu__zgbp = numba.typeof(val.index)
    dtype = _infer_series_dtype(val)
    vxciv__dtxxu = dtype_to_array_type(dtype)
    if _use_dict_str_type and vxciv__dtxxu == string_array_type:
        vxciv__dtxxu = bodo.dict_str_arr_type
    return SeriesType(dtype, data=vxciv__dtxxu, index=hmlu__zgbp, name_typ=
        numba.typeof(val.name), dist=mmo__xkvg)


@unbox(DataFrameType)
def unbox_dataframe(typ, val, c):
    check_runtime_cols_unsupported(typ, 'Unboxing')
    jcwka__yha = c.pyapi.object_getattr_string(val, 'index')
    pnkvs__nzp = c.pyapi.to_native_value(typ.index, jcwka__yha).value
    c.pyapi.decref(jcwka__yha)
    if typ.is_table_format:
        krvkf__fvuo = cgutils.create_struct_proxy(typ.table_type)(c.context,
            c.builder)
        krvkf__fvuo.parent = val
        for rvb__lqic, dprv__yfvyh in typ.table_type.type_to_blk.items():
            lzwl__ckty = c.context.get_constant(types.int64, len(typ.
                table_type.block_to_arr_ind[dprv__yfvyh]))
            mpub__wxb, fdfe__bih = ListInstance.allocate_ex(c.context, c.
                builder, types.List(rvb__lqic), lzwl__ckty)
            fdfe__bih.size = lzwl__ckty
            setattr(krvkf__fvuo, f'block_{dprv__yfvyh}', fdfe__bih.value)
        wcu__nzdlx = c.pyapi.call_method(val, '__len__', ())
        iaqjf__zsvas = c.pyapi.long_as_longlong(wcu__nzdlx)
        c.pyapi.decref(wcu__nzdlx)
        krvkf__fvuo.len = iaqjf__zsvas
        whrxw__lozj = c.context.make_tuple(c.builder, types.Tuple([typ.
            table_type]), [krvkf__fvuo._getvalue()])
    else:
        yjf__yfxt = [c.context.get_constant_null(rvb__lqic) for rvb__lqic in
            typ.data]
        whrxw__lozj = c.context.make_tuple(c.builder, types.Tuple(typ.data),
            yjf__yfxt)
    thffc__aveo = construct_dataframe(c.context, c.builder, typ,
        whrxw__lozj, pnkvs__nzp, val, None)
    return NativeValue(thffc__aveo)


def get_hiframes_dtypes(df):
    if (hasattr(df, '_bodo_meta') and df._bodo_meta is not None and 
        'type_metadata' in df._bodo_meta and df._bodo_meta['type_metadata']
         is not None and len(df._bodo_meta['type_metadata'][1]) == len(df.
        columns)):
        bwj__kdf = df._bodo_meta['type_metadata'][1]
    else:
        bwj__kdf = [None] * len(df.columns)
    pmk__owso = [dtype_to_array_type(_infer_series_dtype(df.iloc[:, i],
        array_metadata=bwj__kdf[i])) for i in range(len(df.columns))]
    pmk__owso = [(bodo.dict_str_arr_type if _use_dict_str_type and 
        rvb__lqic == string_array_type else rvb__lqic) for rvb__lqic in
        pmk__owso]
    return tuple(pmk__owso)


class SeriesDtypeEnum(Enum):
    Int8 = 0
    UInt8 = 1
    Int32 = 2
    UInt32 = 3
    Int64 = 4
    UInt64 = 7
    Float32 = 5
    Float64 = 6
    Int16 = 8
    UInt16 = 9
    STRING = 10
    Bool = 11
    Decimal = 12
    Datime_Date = 13
    NP_Datetime64ns = 14
    NP_Timedelta64ns = 15
    Int128 = 16
    LIST = 18
    STRUCT = 19
    BINARY = 21
    ARRAY = 22
    PD_nullable_Int8 = 23
    PD_nullable_UInt8 = 24
    PD_nullable_Int16 = 25
    PD_nullable_UInt16 = 26
    PD_nullable_Int32 = 27
    PD_nullable_UInt32 = 28
    PD_nullable_Int64 = 29
    PD_nullable_UInt64 = 30
    PD_nullable_bool = 31
    CategoricalType = 32
    NoneType = 33
    Literal = 34
    IntegerArray = 35
    RangeIndexType = 36
    DatetimeIndexType = 37
    NumericIndexType = 38
    PeriodIndexType = 39
    IntervalIndexType = 40
    CategoricalIndexType = 41
    StringIndexType = 42
    BinaryIndexType = 43
    TimedeltaIndexType = 44
    LiteralType = 45


_one_to_one_type_to_enum_map = {types.int8: SeriesDtypeEnum.Int8.value,
    types.uint8: SeriesDtypeEnum.UInt8.value, types.int32: SeriesDtypeEnum.
    Int32.value, types.uint32: SeriesDtypeEnum.UInt32.value, types.int64:
    SeriesDtypeEnum.Int64.value, types.uint64: SeriesDtypeEnum.UInt64.value,
    types.float32: SeriesDtypeEnum.Float32.value, types.float64:
    SeriesDtypeEnum.Float64.value, types.NPDatetime('ns'): SeriesDtypeEnum.
    NP_Datetime64ns.value, types.NPTimedelta('ns'): SeriesDtypeEnum.
    NP_Timedelta64ns.value, types.bool_: SeriesDtypeEnum.Bool.value, types.
    int16: SeriesDtypeEnum.Int16.value, types.uint16: SeriesDtypeEnum.
    UInt16.value, types.Integer('int128', 128): SeriesDtypeEnum.Int128.
    value, bodo.hiframes.datetime_date_ext.datetime_date_type:
    SeriesDtypeEnum.Datime_Date.value, IntDtype(types.int8):
    SeriesDtypeEnum.PD_nullable_Int8.value, IntDtype(types.uint8):
    SeriesDtypeEnum.PD_nullable_UInt8.value, IntDtype(types.int16):
    SeriesDtypeEnum.PD_nullable_Int16.value, IntDtype(types.uint16):
    SeriesDtypeEnum.PD_nullable_UInt16.value, IntDtype(types.int32):
    SeriesDtypeEnum.PD_nullable_Int32.value, IntDtype(types.uint32):
    SeriesDtypeEnum.PD_nullable_UInt32.value, IntDtype(types.int64):
    SeriesDtypeEnum.PD_nullable_Int64.value, IntDtype(types.uint64):
    SeriesDtypeEnum.PD_nullable_UInt64.value, bytes_type: SeriesDtypeEnum.
    BINARY.value, string_type: SeriesDtypeEnum.STRING.value, bodo.bool_:
    SeriesDtypeEnum.Bool.value, types.none: SeriesDtypeEnum.NoneType.value}
_one_to_one_enum_to_type_map = {SeriesDtypeEnum.Int8.value: types.int8,
    SeriesDtypeEnum.UInt8.value: types.uint8, SeriesDtypeEnum.Int32.value:
    types.int32, SeriesDtypeEnum.UInt32.value: types.uint32,
    SeriesDtypeEnum.Int64.value: types.int64, SeriesDtypeEnum.UInt64.value:
    types.uint64, SeriesDtypeEnum.Float32.value: types.float32,
    SeriesDtypeEnum.Float64.value: types.float64, SeriesDtypeEnum.
    NP_Datetime64ns.value: types.NPDatetime('ns'), SeriesDtypeEnum.
    NP_Timedelta64ns.value: types.NPTimedelta('ns'), SeriesDtypeEnum.Int16.
    value: types.int16, SeriesDtypeEnum.UInt16.value: types.uint16,
    SeriesDtypeEnum.Int128.value: types.Integer('int128', 128),
    SeriesDtypeEnum.Datime_Date.value: bodo.hiframes.datetime_date_ext.
    datetime_date_type, SeriesDtypeEnum.PD_nullable_Int8.value: IntDtype(
    types.int8), SeriesDtypeEnum.PD_nullable_UInt8.value: IntDtype(types.
    uint8), SeriesDtypeEnum.PD_nullable_Int16.value: IntDtype(types.int16),
    SeriesDtypeEnum.PD_nullable_UInt16.value: IntDtype(types.uint16),
    SeriesDtypeEnum.PD_nullable_Int32.value: IntDtype(types.int32),
    SeriesDtypeEnum.PD_nullable_UInt32.value: IntDtype(types.uint32),
    SeriesDtypeEnum.PD_nullable_Int64.value: IntDtype(types.int64),
    SeriesDtypeEnum.PD_nullable_UInt64.value: IntDtype(types.uint64),
    SeriesDtypeEnum.BINARY.value: bytes_type, SeriesDtypeEnum.STRING.value:
    string_type, SeriesDtypeEnum.Bool.value: bodo.bool_, SeriesDtypeEnum.
    NoneType.value: types.none}


def _dtype_from_type_enum_list(typ_enum_list):
    tlfvf__fzvo, typ = _dtype_from_type_enum_list_recursor(typ_enum_list)
    if len(tlfvf__fzvo) != 0:
        raise_bodo_error(
            f"""Unexpected Internal Error while converting typing metadata: Dtype list was not fully consumed.
 Input typ_enum_list: {typ_enum_list}.
Remainder: {tlfvf__fzvo}. Please file the error here: https://github.com/Bodo-inc/Feedback"""
            )
    return typ


def _dtype_from_type_enum_list_recursor(typ_enum_list):
    if len(typ_enum_list) == 0:
        raise_bodo_error('Unable to infer dtype from empty typ_enum_list')
    elif typ_enum_list[0] in _one_to_one_enum_to_type_map:
        return typ_enum_list[1:], _one_to_one_enum_to_type_map[typ_enum_list[0]
            ]
    elif typ_enum_list[0] == SeriesDtypeEnum.IntegerArray.value:
        njftt__wbqw, typ = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        return njftt__wbqw, IntegerArrayType(typ)
    elif typ_enum_list[0] == SeriesDtypeEnum.ARRAY.value:
        njftt__wbqw, typ = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        return njftt__wbqw, dtype_to_array_type(typ)
    elif typ_enum_list[0] == SeriesDtypeEnum.Decimal.value:
        xfylv__rqkei = typ_enum_list[1]
        gzae__ctz = typ_enum_list[2]
        return typ_enum_list[3:], Decimal128Type(xfylv__rqkei, gzae__ctz)
    elif typ_enum_list[0] == SeriesDtypeEnum.STRUCT.value:
        pev__qil = typ_enum_list[1]
        gvapv__sbvq = tuple(typ_enum_list[2:2 + pev__qil])
        bcq__dsykh = typ_enum_list[2 + pev__qil:]
        pjmx__lxq = []
        for i in range(pev__qil):
            bcq__dsykh, lprhz__ynyqx = _dtype_from_type_enum_list_recursor(
                bcq__dsykh)
            pjmx__lxq.append(lprhz__ynyqx)
        return bcq__dsykh, StructType(tuple(pjmx__lxq), gvapv__sbvq)
    elif typ_enum_list[0] == SeriesDtypeEnum.Literal.value:
        if len(typ_enum_list) == 1:
            raise_bodo_error(
                f"Unexpected Internal Error while converting typing metadata: Encountered 'Literal' internal enum value with no value following it. Please file the error here: https://github.com/Bodo-inc/Feedback"
                )
        mtht__icut = typ_enum_list[1]
        bcq__dsykh = typ_enum_list[2:]
        return bcq__dsykh, mtht__icut
    elif typ_enum_list[0] == SeriesDtypeEnum.LiteralType.value:
        if len(typ_enum_list) == 1:
            raise_bodo_error(
                f"Unexpected Internal Error while converting typing metadata: Encountered 'LiteralType' internal enum value with no value following it. Please file the error here: https://github.com/Bodo-inc/Feedback"
                )
        mtht__icut = typ_enum_list[1]
        bcq__dsykh = typ_enum_list[2:]
        return bcq__dsykh, numba.types.literal(mtht__icut)
    elif typ_enum_list[0] == SeriesDtypeEnum.CategoricalType.value:
        bcq__dsykh, cub__lcuzu = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        bcq__dsykh, pdkm__heu = _dtype_from_type_enum_list_recursor(bcq__dsykh)
        bcq__dsykh, zgd__urg = _dtype_from_type_enum_list_recursor(bcq__dsykh)
        bcq__dsykh, dvba__ubr = _dtype_from_type_enum_list_recursor(bcq__dsykh)
        bcq__dsykh, sme__zlsqi = _dtype_from_type_enum_list_recursor(bcq__dsykh
            )
        return bcq__dsykh, PDCategoricalDtype(cub__lcuzu, pdkm__heu,
            zgd__urg, dvba__ubr, sme__zlsqi)
    elif typ_enum_list[0] == SeriesDtypeEnum.DatetimeIndexType.value:
        bcq__dsykh, binyw__ngvs = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return bcq__dsykh, DatetimeIndexType(binyw__ngvs)
    elif typ_enum_list[0] == SeriesDtypeEnum.NumericIndexType.value:
        bcq__dsykh, dtype = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        bcq__dsykh, binyw__ngvs = _dtype_from_type_enum_list_recursor(
            bcq__dsykh)
        bcq__dsykh, dvba__ubr = _dtype_from_type_enum_list_recursor(bcq__dsykh)
        return bcq__dsykh, NumericIndexType(dtype, binyw__ngvs, dvba__ubr)
    elif typ_enum_list[0] == SeriesDtypeEnum.PeriodIndexType.value:
        bcq__dsykh, pav__atuk = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        bcq__dsykh, binyw__ngvs = _dtype_from_type_enum_list_recursor(
            bcq__dsykh)
        return bcq__dsykh, PeriodIndexType(pav__atuk, binyw__ngvs)
    elif typ_enum_list[0] == SeriesDtypeEnum.CategoricalIndexType.value:
        bcq__dsykh, dvba__ubr = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        bcq__dsykh, binyw__ngvs = _dtype_from_type_enum_list_recursor(
            bcq__dsykh)
        return bcq__dsykh, CategoricalIndexType(dvba__ubr, binyw__ngvs)
    elif typ_enum_list[0] == SeriesDtypeEnum.RangeIndexType.value:
        bcq__dsykh, binyw__ngvs = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return bcq__dsykh, RangeIndexType(binyw__ngvs)
    elif typ_enum_list[0] == SeriesDtypeEnum.StringIndexType.value:
        bcq__dsykh, binyw__ngvs = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return bcq__dsykh, StringIndexType(binyw__ngvs)
    elif typ_enum_list[0] == SeriesDtypeEnum.BinaryIndexType.value:
        bcq__dsykh, binyw__ngvs = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return bcq__dsykh, BinaryIndexType(binyw__ngvs)
    elif typ_enum_list[0] == SeriesDtypeEnum.TimedeltaIndexType.value:
        bcq__dsykh, binyw__ngvs = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return bcq__dsykh, TimedeltaIndexType(binyw__ngvs)
    else:
        raise_bodo_error(
            f'Unexpected Internal Error while converting typing metadata: unable to infer dtype for type enum {typ_enum_list[0]}. Please file the error here: https://github.com/Bodo-inc/Feedback'
            )


def _dtype_to_type_enum_list(typ):
    return guard(_dtype_to_type_enum_list_recursor, typ)


def _dtype_to_type_enum_list_recursor(typ, upcast_numeric_index=True):
    if typ.__hash__ and typ in _one_to_one_type_to_enum_map:
        return [_one_to_one_type_to_enum_map[typ]]
    if isinstance(typ, (dict, int, list, tuple, str, bool, bytes, float)):
        return [SeriesDtypeEnum.Literal.value, typ]
    elif typ is None:
        return [SeriesDtypeEnum.Literal.value, typ]
    elif is_overload_constant_int(typ):
        bbp__xmv = get_overload_const_int(typ)
        if numba.types.maybe_literal(bbp__xmv) == typ:
            return [SeriesDtypeEnum.LiteralType.value, bbp__xmv]
    elif is_overload_constant_str(typ):
        bbp__xmv = get_overload_const_str(typ)
        if numba.types.maybe_literal(bbp__xmv) == typ:
            return [SeriesDtypeEnum.LiteralType.value, bbp__xmv]
    elif is_overload_constant_bool(typ):
        bbp__xmv = get_overload_const_bool(typ)
        if numba.types.maybe_literal(bbp__xmv) == typ:
            return [SeriesDtypeEnum.LiteralType.value, bbp__xmv]
    elif isinstance(typ, IntegerArrayType):
        return [SeriesDtypeEnum.IntegerArray.value
            ] + _dtype_to_type_enum_list_recursor(typ.dtype)
    elif bodo.utils.utils.is_array_typ(typ, False):
        return [SeriesDtypeEnum.ARRAY.value
            ] + _dtype_to_type_enum_list_recursor(typ.dtype)
    elif isinstance(typ, StructType):
        lusu__hgfx = [SeriesDtypeEnum.STRUCT.value, len(typ.names)]
        for vhoi__tlrjr in typ.names:
            lusu__hgfx.append(vhoi__tlrjr)
        for czfih__uaxww in typ.data:
            lusu__hgfx += _dtype_to_type_enum_list_recursor(czfih__uaxww)
        return lusu__hgfx
    elif isinstance(typ, bodo.libs.decimal_arr_ext.Decimal128Type):
        return [SeriesDtypeEnum.Decimal.value, typ.precision, typ.scale]
    elif isinstance(typ, PDCategoricalDtype):
        rmemv__ghg = _dtype_to_type_enum_list_recursor(typ.categories)
        jeb__afo = _dtype_to_type_enum_list_recursor(typ.elem_type)
        rfwh__kbhjq = _dtype_to_type_enum_list_recursor(typ.ordered)
        wgvl__ujjmj = _dtype_to_type_enum_list_recursor(typ.data)
        vmtpv__ejz = _dtype_to_type_enum_list_recursor(typ.int_type)
        return [SeriesDtypeEnum.CategoricalType.value
            ] + rmemv__ghg + jeb__afo + rfwh__kbhjq + wgvl__ujjmj + vmtpv__ejz
    elif isinstance(typ, DatetimeIndexType):
        return [SeriesDtypeEnum.DatetimeIndexType.value
            ] + _dtype_to_type_enum_list_recursor(typ.name_typ)
    elif isinstance(typ, NumericIndexType):
        if upcast_numeric_index:
            if isinstance(typ.dtype, types.Float):
                uatjt__fwp = types.float64
                zsirz__zfbcp = types.Array(uatjt__fwp, 1, 'C')
            elif typ.dtype in {types.int8, types.int16, types.int32, types.
                int64}:
                uatjt__fwp = types.int64
                zsirz__zfbcp = types.Array(uatjt__fwp, 1, 'C')
            elif typ.dtype in {types.uint8, types.uint16, types.uint32,
                types.uint64}:
                uatjt__fwp = types.uint64
                zsirz__zfbcp = types.Array(uatjt__fwp, 1, 'C')
            elif typ.dtype == types.bool_:
                uatjt__fwp = typ.dtype
                zsirz__zfbcp = typ.data
            else:
                raise GuardException('Unable to convert type')
            return [SeriesDtypeEnum.NumericIndexType.value
                ] + _dtype_to_type_enum_list_recursor(uatjt__fwp
                ) + _dtype_to_type_enum_list_recursor(typ.name_typ
                ) + _dtype_to_type_enum_list_recursor(zsirz__zfbcp)
        else:
            return [SeriesDtypeEnum.NumericIndexType.value
                ] + _dtype_to_type_enum_list_recursor(typ.dtype
                ) + _dtype_to_type_enum_list_recursor(typ.name_typ
                ) + _dtype_to_type_enum_list_recursor(typ.data)
    elif isinstance(typ, PeriodIndexType):
        return [SeriesDtypeEnum.PeriodIndexType.value
            ] + _dtype_to_type_enum_list_recursor(typ.freq
            ) + _dtype_to_type_enum_list_recursor(typ.name_typ)
    elif isinstance(typ, CategoricalIndexType):
        return [SeriesDtypeEnum.CategoricalIndexType.value
            ] + _dtype_to_type_enum_list_recursor(typ.data
            ) + _dtype_to_type_enum_list_recursor(typ.name_typ)
    elif isinstance(typ, RangeIndexType):
        return [SeriesDtypeEnum.RangeIndexType.value
            ] + _dtype_to_type_enum_list_recursor(typ.name_typ)
    elif isinstance(typ, StringIndexType):
        return [SeriesDtypeEnum.StringIndexType.value
            ] + _dtype_to_type_enum_list_recursor(typ.name_typ)
    elif isinstance(typ, BinaryIndexType):
        return [SeriesDtypeEnum.BinaryIndexType.value
            ] + _dtype_to_type_enum_list_recursor(typ.name_typ)
    elif isinstance(typ, TimedeltaIndexType):
        return [SeriesDtypeEnum.TimedeltaIndexType.value
            ] + _dtype_to_type_enum_list_recursor(typ.name_typ)
    else:
        raise GuardException('Unable to convert type')


def _infer_series_dtype(S, array_metadata=None):
    if S.dtype == np.dtype('O'):
        if len(S.values) == 0:
            if (hasattr(S, '_bodo_meta') and S._bodo_meta is not None and 
                'type_metadata' in S._bodo_meta and S._bodo_meta[
                'type_metadata'][1] is not None):
                kpbwf__hsbqe = S._bodo_meta['type_metadata'][1]
                return _dtype_from_type_enum_list(kpbwf__hsbqe)
            elif array_metadata != None:
                return _dtype_from_type_enum_list(array_metadata).dtype
        return numba.typeof(S.values).dtype
    if isinstance(S.dtype, pd.core.arrays.integer._IntegerDtype):
        return typeof_pd_int_dtype(S.dtype, None)
    elif isinstance(S.dtype, pd.CategoricalDtype):
        return bodo.typeof(S.dtype)
    elif isinstance(S.dtype, pd.StringDtype):
        return string_type
    elif isinstance(S.dtype, pd.BooleanDtype):
        return types.bool_
    if isinstance(S.dtype, pd.DatetimeTZDtype):
        yfqkk__hhbyg = S.dtype.unit
        if yfqkk__hhbyg != 'ns':
            raise BodoError("Timezone-aware datetime data requires 'ns' units")
        yuunb__duo = bodo.libs.pd_datetime_arr_ext.get_pytz_type_info(S.
            dtype.tz)
        return PandasDatetimeTZDtype(yuunb__duo)
    try:
        return numpy_support.from_dtype(S.dtype)
    except:
        raise BodoError(
            f'data type {S.dtype} for column {S.name} not supported yet')


def _get_use_df_parent_obj_flag(builder, context, pyapi, parent_obj, n_cols):
    if n_cols is None:
        return context.get_constant(types.bool_, False)
    ygray__ntu = cgutils.is_not_null(builder, parent_obj)
    vrdlc__eppv = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with builder.if_then(ygray__ntu):
        iurfi__kfc = pyapi.object_getattr_string(parent_obj, 'columns')
        wcu__nzdlx = pyapi.call_method(iurfi__kfc, '__len__', ())
        builder.store(pyapi.long_as_longlong(wcu__nzdlx), vrdlc__eppv)
        pyapi.decref(wcu__nzdlx)
        pyapi.decref(iurfi__kfc)
    use_parent_obj = builder.and_(ygray__ntu, builder.icmp_unsigned('==',
        builder.load(vrdlc__eppv), context.get_constant(types.int64, n_cols)))
    return use_parent_obj


def _get_df_columns_obj(c, builder, context, pyapi, df_typ, dataframe_payload):
    if df_typ.has_runtime_cols:
        ibpe__jwh = df_typ.runtime_colname_typ
        context.nrt.incref(builder, ibpe__jwh, dataframe_payload.columns)
        return pyapi.from_native_value(ibpe__jwh, dataframe_payload.columns,
            c.env_manager)
    if all(isinstance(c, int) for c in df_typ.columns):
        yhpap__lxt = np.array(df_typ.columns, 'int64')
    elif all(isinstance(c, str) for c in df_typ.columns):
        yhpap__lxt = pd.array(df_typ.columns, 'string')
    else:
        yhpap__lxt = df_typ.columns
    kjzq__jxiv = numba.typeof(yhpap__lxt)
    nul__wima = context.get_constant_generic(builder, kjzq__jxiv, yhpap__lxt)
    xvn__olxx = pyapi.from_native_value(kjzq__jxiv, nul__wima, c.env_manager)
    return xvn__olxx


def _create_initial_df_object(builder, context, pyapi, c, df_typ, obj,
    dataframe_payload, res, use_parent_obj):
    with c.builder.if_else(use_parent_obj) as (iys__inwpa, rgnk__zambz):
        with iys__inwpa:
            pyapi.incref(obj)
            dyq__pacp = context.insert_const_string(c.builder.module, 'numpy')
            izo__mcoy = pyapi.import_module_noblock(dyq__pacp)
            if df_typ.has_runtime_cols:
                osuxl__hlw = 0
            else:
                osuxl__hlw = len(df_typ.columns)
            hnse__porjc = pyapi.long_from_longlong(lir.Constant(lir.IntType
                (64), osuxl__hlw))
            hsbmb__nrkuy = pyapi.call_method(izo__mcoy, 'arange', (
                hnse__porjc,))
            pyapi.object_setattr_string(obj, 'columns', hsbmb__nrkuy)
            pyapi.decref(izo__mcoy)
            pyapi.decref(hsbmb__nrkuy)
            pyapi.decref(hnse__porjc)
        with rgnk__zambz:
            context.nrt.incref(builder, df_typ.index, dataframe_payload.index)
            gwpit__ghl = c.pyapi.from_native_value(df_typ.index,
                dataframe_payload.index, c.env_manager)
            dyq__pacp = context.insert_const_string(c.builder.module, 'pandas')
            izo__mcoy = pyapi.import_module_noblock(dyq__pacp)
            df_obj = pyapi.call_method(izo__mcoy, 'DataFrame', (pyapi.
                borrow_none(), gwpit__ghl))
            pyapi.decref(izo__mcoy)
            pyapi.decref(gwpit__ghl)
            builder.store(df_obj, res)


@box(DataFrameType)
def box_dataframe(typ, val, c):
    from bodo.hiframes.table import box_table
    context = c.context
    builder = c.builder
    pyapi = c.pyapi
    dataframe_payload = bodo.hiframes.pd_dataframe_ext.get_dataframe_payload(c
        .context, c.builder, typ, val)
    tndlt__slmu = cgutils.create_struct_proxy(typ)(context, builder, value=val)
    n_cols = len(typ.columns) if not typ.has_runtime_cols else None
    obj = tndlt__slmu.parent
    res = cgutils.alloca_once_value(builder, obj)
    use_parent_obj = _get_use_df_parent_obj_flag(builder, context, pyapi,
        obj, n_cols)
    _create_initial_df_object(builder, context, pyapi, c, typ, obj,
        dataframe_payload, res, use_parent_obj)
    if typ.is_table_format:
        jvp__yogg = typ.table_type
        krvkf__fvuo = builder.extract_value(dataframe_payload.data, 0)
        context.nrt.incref(builder, jvp__yogg, krvkf__fvuo)
        gvjbt__apv = box_table(jvp__yogg, krvkf__fvuo, c, builder.not_(
            use_parent_obj))
        with builder.if_else(use_parent_obj) as (wvqbt__mxqi, lxvf__yasrk):
            with wvqbt__mxqi:
                ajqor__rhy = pyapi.object_getattr_string(gvjbt__apv, 'arrays')
                babm__ikf = c.pyapi.make_none()
                if n_cols is None:
                    wcu__nzdlx = pyapi.call_method(ajqor__rhy, '__len__', ())
                    lzwl__ckty = pyapi.long_as_longlong(wcu__nzdlx)
                    pyapi.decref(wcu__nzdlx)
                else:
                    lzwl__ckty = context.get_constant(types.int64, n_cols)
                with cgutils.for_range(builder, lzwl__ckty) as hav__dnh:
                    i = hav__dnh.index
                    jxlb__xbzgf = pyapi.list_getitem(ajqor__rhy, i)
                    eqf__aqo = c.builder.icmp_unsigned('!=', jxlb__xbzgf,
                        babm__ikf)
                    with builder.if_then(eqf__aqo):
                        fipzd__hrw = pyapi.long_from_longlong(i)
                        df_obj = builder.load(res)
                        pyapi.object_setitem(df_obj, fipzd__hrw, jxlb__xbzgf)
                        pyapi.decref(fipzd__hrw)
                pyapi.decref(ajqor__rhy)
                pyapi.decref(babm__ikf)
            with lxvf__yasrk:
                df_obj = builder.load(res)
                gwpit__ghl = pyapi.object_getattr_string(df_obj, 'index')
                btsax__bjr = c.pyapi.call_method(gvjbt__apv, 'to_pandas', (
                    gwpit__ghl,))
                builder.store(btsax__bjr, res)
                pyapi.decref(df_obj)
                pyapi.decref(gwpit__ghl)
        pyapi.decref(gvjbt__apv)
    else:
        qkr__qltr = [builder.extract_value(dataframe_payload.data, i) for i in
            range(n_cols)]
        rrz__ktrd = typ.data
        for i, uxr__kxyb, vxciv__dtxxu in zip(range(n_cols), qkr__qltr,
            rrz__ktrd):
            wsel__yyhkn = cgutils.alloca_once_value(builder, uxr__kxyb)
            sixao__nso = cgutils.alloca_once_value(builder, context.
                get_constant_null(vxciv__dtxxu))
            eqf__aqo = builder.not_(is_ll_eq(builder, wsel__yyhkn, sixao__nso))
            fpqex__wyvxf = builder.or_(builder.not_(use_parent_obj),
                builder.and_(use_parent_obj, eqf__aqo))
            with builder.if_then(fpqex__wyvxf):
                fipzd__hrw = pyapi.long_from_longlong(context.get_constant(
                    types.int64, i))
                context.nrt.incref(builder, vxciv__dtxxu, uxr__kxyb)
                arr_obj = pyapi.from_native_value(vxciv__dtxxu, uxr__kxyb,
                    c.env_manager)
                df_obj = builder.load(res)
                pyapi.object_setitem(df_obj, fipzd__hrw, arr_obj)
                pyapi.decref(arr_obj)
                pyapi.decref(fipzd__hrw)
    df_obj = builder.load(res)
    xvn__olxx = _get_df_columns_obj(c, builder, context, pyapi, typ,
        dataframe_payload)
    pyapi.object_setattr_string(df_obj, 'columns', xvn__olxx)
    pyapi.decref(xvn__olxx)
    _set_bodo_meta_dataframe(c, df_obj, typ)
    c.context.nrt.decref(c.builder, typ, val)
    return df_obj


def get_df_obj_column_codegen(context, builder, pyapi, df_obj, col_ind,
    data_typ):
    babm__ikf = pyapi.borrow_none()
    yjx__bwnxl = pyapi.unserialize(pyapi.serialize_object(slice))
    xtj__gui = pyapi.call_function_objargs(yjx__bwnxl, [babm__ikf])
    mficm__ktpx = pyapi.long_from_longlong(col_ind)
    qszoz__qoxjg = pyapi.tuple_pack([xtj__gui, mficm__ktpx])
    zogfk__mjzk = pyapi.object_getattr_string(df_obj, 'iloc')
    kqx__zbopl = pyapi.object_getitem(zogfk__mjzk, qszoz__qoxjg)
    if isinstance(data_typ, bodo.DatetimeArrayType):
        xhjo__dbsby = pyapi.object_getattr_string(kqx__zbopl, 'array')
    else:
        xhjo__dbsby = pyapi.object_getattr_string(kqx__zbopl, 'values')
    if isinstance(data_typ, types.Array):
        lnb__oed = context.insert_const_string(builder.module, 'numpy')
        fmjl__hrh = pyapi.import_module_noblock(lnb__oed)
        arr_obj = pyapi.call_method(fmjl__hrh, 'ascontiguousarray', (
            xhjo__dbsby,))
        pyapi.decref(xhjo__dbsby)
        pyapi.decref(fmjl__hrh)
    else:
        arr_obj = xhjo__dbsby
    pyapi.decref(yjx__bwnxl)
    pyapi.decref(xtj__gui)
    pyapi.decref(mficm__ktpx)
    pyapi.decref(qszoz__qoxjg)
    pyapi.decref(zogfk__mjzk)
    pyapi.decref(kqx__zbopl)
    return arr_obj


@intrinsic
def unbox_dataframe_column(typingctx, df, i=None):
    assert isinstance(df, DataFrameType) and is_overload_constant_int(i)

    def codegen(context, builder, sig, args):
        pyapi = context.get_python_api(builder)
        c = numba.core.pythonapi._UnboxContext(context, builder, pyapi)
        df_typ = sig.args[0]
        col_ind = get_overload_const_int(sig.args[1])
        data_typ = df_typ.data[col_ind]
        tndlt__slmu = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        arr_obj = get_df_obj_column_codegen(context, builder, pyapi,
            tndlt__slmu.parent, args[1], data_typ)
        umnjf__khz = _unbox_series_data(data_typ.dtype, data_typ, arr_obj, c)
        c.pyapi.decref(arr_obj)
        dataframe_payload = (bodo.hiframes.pd_dataframe_ext.
            get_dataframe_payload(c.context, c.builder, df_typ, args[0]))
        if df_typ.is_table_format:
            krvkf__fvuo = cgutils.create_struct_proxy(df_typ.table_type)(c.
                context, c.builder, builder.extract_value(dataframe_payload
                .data, 0))
            dprv__yfvyh = df_typ.table_type.type_to_blk[data_typ]
            qcs__elkqj = getattr(krvkf__fvuo, f'block_{dprv__yfvyh}')
            sbggc__oouc = ListInstance(c.context, c.builder, types.List(
                data_typ), qcs__elkqj)
            jgg__ena = context.get_constant(types.int64, df_typ.table_type.
                block_offsets[col_ind])
            sbggc__oouc.inititem(jgg__ena, umnjf__khz.value, incref=False)
        else:
            dataframe_payload.data = builder.insert_value(dataframe_payload
                .data, umnjf__khz.value, col_ind)
        pjq__nvn = DataFramePayloadType(df_typ)
        nii__guqu = context.nrt.meminfo_data(builder, tndlt__slmu.meminfo)
        enu__yob = context.get_value_type(pjq__nvn).as_pointer()
        nii__guqu = builder.bitcast(nii__guqu, enu__yob)
        builder.store(dataframe_payload._getvalue(), nii__guqu)
    return signature(types.none, df, i), codegen


@numba.njit
def unbox_col_if_needed(df, i):
    if bodo.hiframes.pd_dataframe_ext.has_parent(df
        ) and bodo.hiframes.pd_dataframe_ext._column_needs_unboxing(df, i):
        bodo.hiframes.boxing.unbox_dataframe_column(df, i)


@unbox(SeriesType)
def unbox_series(typ, val, c):
    if isinstance(typ.data, DatetimeArrayType):
        xhjo__dbsby = c.pyapi.object_getattr_string(val, 'array')
    else:
        xhjo__dbsby = c.pyapi.object_getattr_string(val, 'values')
    if isinstance(typ.data, types.Array):
        lnb__oed = c.context.insert_const_string(c.builder.module, 'numpy')
        fmjl__hrh = c.pyapi.import_module_noblock(lnb__oed)
        arr_obj = c.pyapi.call_method(fmjl__hrh, 'ascontiguousarray', (
            xhjo__dbsby,))
        c.pyapi.decref(xhjo__dbsby)
        c.pyapi.decref(fmjl__hrh)
    else:
        arr_obj = xhjo__dbsby
    atln__zehpo = _unbox_series_data(typ.dtype, typ.data, arr_obj, c).value
    gwpit__ghl = c.pyapi.object_getattr_string(val, 'index')
    pnkvs__nzp = c.pyapi.to_native_value(typ.index, gwpit__ghl).value
    odki__yam = c.pyapi.object_getattr_string(val, 'name')
    anmj__wjnpq = c.pyapi.to_native_value(typ.name_typ, odki__yam).value
    tuhbt__irb = bodo.hiframes.pd_series_ext.construct_series(c.context, c.
        builder, typ, atln__zehpo, pnkvs__nzp, anmj__wjnpq)
    c.pyapi.decref(arr_obj)
    c.pyapi.decref(gwpit__ghl)
    c.pyapi.decref(odki__yam)
    return NativeValue(tuhbt__irb)


def _unbox_series_data(dtype, data_typ, arr_obj, c):
    if data_typ == string_array_split_view_type:
        gtedw__yyklu = c.context.make_helper(c.builder,
            string_array_split_view_type)
        return NativeValue(gtedw__yyklu._getvalue())
    return c.pyapi.to_native_value(data_typ, arr_obj)


@box(HeterogeneousSeriesType)
@box(SeriesType)
def box_series(typ, val, c):
    dyq__pacp = c.context.insert_const_string(c.builder.module, 'pandas')
    tak__zns = c.pyapi.import_module_noblock(dyq__pacp)
    biz__hzubk = bodo.hiframes.pd_series_ext.get_series_payload(c.context,
        c.builder, typ, val)
    c.context.nrt.incref(c.builder, typ.data, biz__hzubk.data)
    c.context.nrt.incref(c.builder, typ.index, biz__hzubk.index)
    c.context.nrt.incref(c.builder, typ.name_typ, biz__hzubk.name)
    arr_obj = c.pyapi.from_native_value(typ.data, biz__hzubk.data, c.
        env_manager)
    gwpit__ghl = c.pyapi.from_native_value(typ.index, biz__hzubk.index, c.
        env_manager)
    odki__yam = c.pyapi.from_native_value(typ.name_typ, biz__hzubk.name, c.
        env_manager)
    if isinstance(typ, HeterogeneousSeriesType) and isinstance(typ.data,
        bodo.NullableTupleType):
        dtype = c.pyapi.unserialize(c.pyapi.serialize_object(object))
    else:
        dtype = c.pyapi.make_none()
    res = c.pyapi.call_method(tak__zns, 'Series', (arr_obj, gwpit__ghl,
        dtype, odki__yam))
    c.pyapi.decref(arr_obj)
    c.pyapi.decref(gwpit__ghl)
    c.pyapi.decref(odki__yam)
    if isinstance(typ, HeterogeneousSeriesType) and isinstance(typ.data,
        bodo.NullableTupleType):
        c.pyapi.decref(dtype)
    _set_bodo_meta_series(res, c, typ)
    c.pyapi.decref(tak__zns)
    c.context.nrt.decref(c.builder, typ, val)
    return res


def type_enum_list_to_py_list_obj(pyapi, context, builder, env_manager,
    typ_list):
    qdn__kmfbp = []
    for jeunt__pytqk in typ_list:
        if isinstance(jeunt__pytqk, int) and not isinstance(jeunt__pytqk, bool
            ):
            wml__lugzx = pyapi.long_from_longlong(lir.Constant(lir.IntType(
                64), jeunt__pytqk))
        else:
            mojhw__ykb = numba.typeof(jeunt__pytqk)
            uwn__krabu = context.get_constant_generic(builder, mojhw__ykb,
                jeunt__pytqk)
            wml__lugzx = pyapi.from_native_value(mojhw__ykb, uwn__krabu,
                env_manager)
        qdn__kmfbp.append(wml__lugzx)
    omuni__xqmb = pyapi.list_pack(qdn__kmfbp)
    for val in qdn__kmfbp:
        pyapi.decref(val)
    return omuni__xqmb


def _set_bodo_meta_dataframe(c, obj, typ):
    pyapi = c.pyapi
    context = c.context
    builder = c.builder
    hxa__bus = not typ.has_runtime_cols and (not typ.is_table_format or len
        (typ.columns) < TABLE_FORMAT_THRESHOLD)
    imdro__wvm = 2 if hxa__bus else 1
    qidud__hjb = pyapi.dict_new(imdro__wvm)
    xyrd__fsz = pyapi.long_from_longlong(lir.Constant(lir.IntType(64), typ.
        dist.value))
    pyapi.dict_setitem_string(qidud__hjb, 'dist', xyrd__fsz)
    pyapi.decref(xyrd__fsz)
    if hxa__bus:
        hit__reoaq = _dtype_to_type_enum_list(typ.index)
        if hit__reoaq != None:
            fwbbm__kgyu = type_enum_list_to_py_list_obj(pyapi, context,
                builder, c.env_manager, hit__reoaq)
        else:
            fwbbm__kgyu = pyapi.make_none()
        pit__pip = []
        for dtype in typ.data:
            typ_list = _dtype_to_type_enum_list(dtype)
            if typ_list != None:
                omuni__xqmb = type_enum_list_to_py_list_obj(pyapi, context,
                    builder, c.env_manager, typ_list)
            else:
                omuni__xqmb = pyapi.make_none()
            pit__pip.append(omuni__xqmb)
        gxama__ewo = pyapi.list_pack(pit__pip)
        uyg__sbla = pyapi.list_pack([fwbbm__kgyu, gxama__ewo])
        for val in pit__pip:
            pyapi.decref(val)
        pyapi.dict_setitem_string(qidud__hjb, 'type_metadata', uyg__sbla)
    pyapi.object_setattr_string(obj, '_bodo_meta', qidud__hjb)
    pyapi.decref(qidud__hjb)


def get_series_dtype_handle_null_int_and_hetrogenous(series_typ):
    if isinstance(series_typ, HeterogeneousSeriesType):
        return None
    if isinstance(series_typ.dtype, types.Number) and isinstance(series_typ
        .data, IntegerArrayType):
        return IntDtype(series_typ.dtype)
    return series_typ.dtype


def _set_bodo_meta_series(obj, c, typ):
    pyapi = c.pyapi
    context = c.context
    builder = c.builder
    qidud__hjb = pyapi.dict_new(2)
    xyrd__fsz = pyapi.long_from_longlong(lir.Constant(lir.IntType(64), typ.
        dist.value))
    hit__reoaq = _dtype_to_type_enum_list(typ.index)
    if hit__reoaq != None:
        fwbbm__kgyu = type_enum_list_to_py_list_obj(pyapi, context, builder,
            c.env_manager, hit__reoaq)
    else:
        fwbbm__kgyu = pyapi.make_none()
    dtype = get_series_dtype_handle_null_int_and_hetrogenous(typ)
    if dtype != None:
        typ_list = _dtype_to_type_enum_list(dtype)
        if typ_list != None:
            tgd__kdifk = type_enum_list_to_py_list_obj(pyapi, context,
                builder, c.env_manager, typ_list)
        else:
            tgd__kdifk = pyapi.make_none()
    else:
        tgd__kdifk = pyapi.make_none()
    apx__orrr = pyapi.list_pack([fwbbm__kgyu, tgd__kdifk])
    pyapi.dict_setitem_string(qidud__hjb, 'type_metadata', apx__orrr)
    pyapi.decref(apx__orrr)
    pyapi.dict_setitem_string(qidud__hjb, 'dist', xyrd__fsz)
    pyapi.object_setattr_string(obj, '_bodo_meta', qidud__hjb)
    pyapi.decref(qidud__hjb)
    pyapi.decref(xyrd__fsz)


@typeof_impl.register(np.ndarray)
def _typeof_ndarray(val, c):
    try:
        dtype = numba.np.numpy_support.from_dtype(val.dtype)
    except NotImplementedError as zjh__nqyfi:
        dtype = types.pyobject
    if dtype == types.pyobject:
        return _infer_ndarray_obj_dtype(val)
    zcbaj__qyy = numba.np.numpy_support.map_layout(val)
    xit__ivgxi = not val.flags.writeable
    return types.Array(dtype, val.ndim, zcbaj__qyy, readonly=xit__ivgxi)


def _infer_ndarray_obj_dtype(val):
    if not val.dtype == np.dtype('O'):
        raise BodoError('Unsupported array dtype: {}'.format(val.dtype))
    i = 0
    while i < len(val) and (pd.api.types.is_scalar(val[i]) and pd.isna(val[
        i]) or not pd.api.types.is_scalar(val[i]) and len(val[i]) == 0):
        i += 1
    if i == len(val):
        warnings.warn(BodoWarning(
            'Empty object array passed to Bodo, which causes ambiguity in typing. This can cause errors in parallel execution.'
            ))
        return (bodo.dict_str_arr_type if _use_dict_str_type else
            string_array_type)
    eziz__vadxe = val[i]
    if isinstance(eziz__vadxe, str):
        return (bodo.dict_str_arr_type if _use_dict_str_type else
            string_array_type)
    elif isinstance(eziz__vadxe, bytes):
        return binary_array_type
    elif isinstance(eziz__vadxe, bool):
        return bodo.libs.bool_arr_ext.boolean_array
    elif isinstance(eziz__vadxe, (int, np.int32, np.int64)):
        return bodo.libs.int_arr_ext.IntegerArrayType(numba.typeof(eziz__vadxe)
            )
    elif isinstance(eziz__vadxe, (dict, Dict)) and all(isinstance(
        zcug__wnkc, str) for zcug__wnkc in eziz__vadxe.keys()):
        gvapv__sbvq = tuple(eziz__vadxe.keys())
        prt__bfvrb = tuple(_get_struct_value_arr_type(v) for v in
            eziz__vadxe.values())
        return StructArrayType(prt__bfvrb, gvapv__sbvq)
    elif isinstance(eziz__vadxe, (dict, Dict)):
        pckx__hadli = numba.typeof(_value_to_array(list(eziz__vadxe.keys())))
        mvxnf__cng = numba.typeof(_value_to_array(list(eziz__vadxe.values())))
        pckx__hadli = to_str_arr_if_dict_array(pckx__hadli)
        mvxnf__cng = to_str_arr_if_dict_array(mvxnf__cng)
        return MapArrayType(pckx__hadli, mvxnf__cng)
    elif isinstance(eziz__vadxe, tuple):
        prt__bfvrb = tuple(_get_struct_value_arr_type(v) for v in eziz__vadxe)
        return TupleArrayType(prt__bfvrb)
    if isinstance(eziz__vadxe, (list, np.ndarray, pd.arrays.BooleanArray,
        pd.arrays.IntegerArray, pd.arrays.StringArray)):
        if isinstance(eziz__vadxe, list):
            eziz__vadxe = _value_to_array(eziz__vadxe)
        iunvg__vtfqe = numba.typeof(eziz__vadxe)
        iunvg__vtfqe = to_str_arr_if_dict_array(iunvg__vtfqe)
        return ArrayItemArrayType(iunvg__vtfqe)
    if isinstance(eziz__vadxe, datetime.date):
        return datetime_date_array_type
    if isinstance(eziz__vadxe, datetime.timedelta):
        return datetime_timedelta_array_type
    if isinstance(eziz__vadxe, decimal.Decimal):
        return DecimalArrayType(38, 18)
    raise BodoError(f'Unsupported object array with first value: {eziz__vadxe}'
        )


def _value_to_array(val):
    assert isinstance(val, (list, dict, Dict))
    if isinstance(val, (dict, Dict)):
        val = dict(val)
        return np.array([val], np.object_)
    iqtnv__zaoq = val.copy()
    iqtnv__zaoq.append(None)
    uxr__kxyb = np.array(iqtnv__zaoq, np.object_)
    if len(val) and isinstance(val[0], float):
        uxr__kxyb = np.array(val, np.float64)
    return uxr__kxyb


def _get_struct_value_arr_type(v):
    if isinstance(v, (dict, Dict)):
        return numba.typeof(_value_to_array(v))
    if isinstance(v, list):
        return dtype_to_array_type(numba.typeof(_value_to_array(v)))
    if pd.api.types.is_scalar(v) and pd.isna(v):
        warnings.warn(BodoWarning(
            'Field value in struct array is NA, which causes ambiguity in typing. This can cause errors in parallel execution.'
            ))
        return string_array_type
    vxciv__dtxxu = dtype_to_array_type(numba.typeof(v))
    if isinstance(v, (int, bool)):
        vxciv__dtxxu = to_nullable_type(vxciv__dtxxu)
    return vxciv__dtxxu
