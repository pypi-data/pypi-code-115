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
    ynjb__xekr = tuple(val.columns.to_list())
    hjmj__mcj = get_hiframes_dtypes(val)
    if (len(val.index) == 0 and val.index.dtype == np.dtype('O') and
        hasattr(val, '_bodo_meta') and val._bodo_meta is not None and 
        'type_metadata' in val._bodo_meta and val._bodo_meta[
        'type_metadata'] is not None and len(val._bodo_meta['type_metadata'
        ][1]) == len(val.columns) and val._bodo_meta['type_metadata'][0] is not
        None):
        osff__sxjv = _dtype_from_type_enum_list(val._bodo_meta[
            'type_metadata'][0])
    else:
        osff__sxjv = numba.typeof(val.index)
    mfby__bqp = Distribution(val._bodo_meta['dist']) if hasattr(val,
        '_bodo_meta') and val._bodo_meta is not None else Distribution.REP
    lcmby__ngne = len(hjmj__mcj) >= TABLE_FORMAT_THRESHOLD
    return DataFrameType(hjmj__mcj, osff__sxjv, ynjb__xekr, mfby__bqp,
        is_table_format=lcmby__ngne)


@typeof_impl.register(pd.Series)
def typeof_pd_series(val, c):
    from bodo.transforms.distributed_analysis import Distribution
    mfby__bqp = Distribution(val._bodo_meta['dist']) if hasattr(val,
        '_bodo_meta') and val._bodo_meta is not None else Distribution.REP
    if (len(val.index) == 0 and val.index.dtype == np.dtype('O') and
        hasattr(val, '_bodo_meta') and val._bodo_meta is not None and 
        'type_metadata' in val._bodo_meta and val._bodo_meta[
        'type_metadata'] is not None and val._bodo_meta['type_metadata'][0]
         is not None):
        pxl__obbb = _dtype_from_type_enum_list(val._bodo_meta[
            'type_metadata'][0])
    else:
        pxl__obbb = numba.typeof(val.index)
    dtype = _infer_series_dtype(val)
    ytu__vnna = dtype_to_array_type(dtype)
    if _use_dict_str_type and ytu__vnna == string_array_type:
        ytu__vnna = bodo.dict_str_arr_type
    return SeriesType(dtype, data=ytu__vnna, index=pxl__obbb, name_typ=
        numba.typeof(val.name), dist=mfby__bqp)


@unbox(DataFrameType)
def unbox_dataframe(typ, val, c):
    check_runtime_cols_unsupported(typ, 'Unboxing')
    dbny__tcsm = c.pyapi.object_getattr_string(val, 'index')
    ecz__httl = c.pyapi.to_native_value(typ.index, dbny__tcsm).value
    c.pyapi.decref(dbny__tcsm)
    if typ.is_table_format:
        jkzk__djwkd = cgutils.create_struct_proxy(typ.table_type)(c.context,
            c.builder)
        jkzk__djwkd.parent = val
        for shyjr__uqp, pzih__dbhg in typ.table_type.type_to_blk.items():
            ugl__wct = c.context.get_constant(types.int64, len(typ.
                table_type.block_to_arr_ind[pzih__dbhg]))
            tpltf__qxwb, jmaw__rltm = ListInstance.allocate_ex(c.context, c
                .builder, types.List(shyjr__uqp), ugl__wct)
            jmaw__rltm.size = ugl__wct
            setattr(jkzk__djwkd, f'block_{pzih__dbhg}', jmaw__rltm.value)
        fgakq__hcilb = c.pyapi.call_method(val, '__len__', ())
        jhjk__wpz = c.pyapi.long_as_longlong(fgakq__hcilb)
        c.pyapi.decref(fgakq__hcilb)
        jkzk__djwkd.len = jhjk__wpz
        dufw__adep = c.context.make_tuple(c.builder, types.Tuple([typ.
            table_type]), [jkzk__djwkd._getvalue()])
    else:
        vfob__jhez = [c.context.get_constant_null(shyjr__uqp) for
            shyjr__uqp in typ.data]
        dufw__adep = c.context.make_tuple(c.builder, types.Tuple(typ.data),
            vfob__jhez)
    dxmw__uvka = construct_dataframe(c.context, c.builder, typ, dufw__adep,
        ecz__httl, val, None)
    return NativeValue(dxmw__uvka)


def get_hiframes_dtypes(df):
    if (hasattr(df, '_bodo_meta') and df._bodo_meta is not None and 
        'type_metadata' in df._bodo_meta and df._bodo_meta['type_metadata']
         is not None and len(df._bodo_meta['type_metadata'][1]) == len(df.
        columns)):
        wqu__mfklx = df._bodo_meta['type_metadata'][1]
    else:
        wqu__mfklx = [None] * len(df.columns)
    rac__wod = [dtype_to_array_type(_infer_series_dtype(df.iloc[:, i],
        array_metadata=wqu__mfklx[i])) for i in range(len(df.columns))]
    rac__wod = [(bodo.dict_str_arr_type if _use_dict_str_type and 
        shyjr__uqp == string_array_type else shyjr__uqp) for shyjr__uqp in
        rac__wod]
    return tuple(rac__wod)


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
    iczgs__lsulw, typ = _dtype_from_type_enum_list_recursor(typ_enum_list)
    if len(iczgs__lsulw) != 0:
        raise_bodo_error(
            f"""Unexpected Internal Error while converting typing metadata: Dtype list was not fully consumed.
 Input typ_enum_list: {typ_enum_list}.
Remainder: {iczgs__lsulw}. Please file the error here: https://github.com/Bodo-inc/Feedback"""
            )
    return typ


def _dtype_from_type_enum_list_recursor(typ_enum_list):
    if len(typ_enum_list) == 0:
        raise_bodo_error('Unable to infer dtype from empty typ_enum_list')
    elif typ_enum_list[0] in _one_to_one_enum_to_type_map:
        return typ_enum_list[1:], _one_to_one_enum_to_type_map[typ_enum_list[0]
            ]
    elif typ_enum_list[0] == SeriesDtypeEnum.IntegerArray.value:
        pdje__arjtq, typ = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        return pdje__arjtq, IntegerArrayType(typ)
    elif typ_enum_list[0] == SeriesDtypeEnum.ARRAY.value:
        pdje__arjtq, typ = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        return pdje__arjtq, dtype_to_array_type(typ)
    elif typ_enum_list[0] == SeriesDtypeEnum.Decimal.value:
        usij__fsr = typ_enum_list[1]
        yytq__hqkk = typ_enum_list[2]
        return typ_enum_list[3:], Decimal128Type(usij__fsr, yytq__hqkk)
    elif typ_enum_list[0] == SeriesDtypeEnum.STRUCT.value:
        qbtcu__gtoaz = typ_enum_list[1]
        psx__soe = tuple(typ_enum_list[2:2 + qbtcu__gtoaz])
        koifd__mho = typ_enum_list[2 + qbtcu__gtoaz:]
        cwe__ixkmi = []
        for i in range(qbtcu__gtoaz):
            koifd__mho, tlyy__erio = _dtype_from_type_enum_list_recursor(
                koifd__mho)
            cwe__ixkmi.append(tlyy__erio)
        return koifd__mho, StructType(tuple(cwe__ixkmi), psx__soe)
    elif typ_enum_list[0] == SeriesDtypeEnum.Literal.value:
        if len(typ_enum_list) == 1:
            raise_bodo_error(
                f"Unexpected Internal Error while converting typing metadata: Encountered 'Literal' internal enum value with no value following it. Please file the error here: https://github.com/Bodo-inc/Feedback"
                )
        wjxos__cwi = typ_enum_list[1]
        koifd__mho = typ_enum_list[2:]
        return koifd__mho, wjxos__cwi
    elif typ_enum_list[0] == SeriesDtypeEnum.LiteralType.value:
        if len(typ_enum_list) == 1:
            raise_bodo_error(
                f"Unexpected Internal Error while converting typing metadata: Encountered 'LiteralType' internal enum value with no value following it. Please file the error here: https://github.com/Bodo-inc/Feedback"
                )
        wjxos__cwi = typ_enum_list[1]
        koifd__mho = typ_enum_list[2:]
        return koifd__mho, numba.types.literal(wjxos__cwi)
    elif typ_enum_list[0] == SeriesDtypeEnum.CategoricalType.value:
        koifd__mho, exy__hmogk = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        koifd__mho, scbhv__pxob = _dtype_from_type_enum_list_recursor(
            koifd__mho)
        koifd__mho, rqw__nbqn = _dtype_from_type_enum_list_recursor(koifd__mho)
        koifd__mho, ltps__zyfs = _dtype_from_type_enum_list_recursor(koifd__mho
            )
        koifd__mho, wcjj__qvvfg = _dtype_from_type_enum_list_recursor(
            koifd__mho)
        return koifd__mho, PDCategoricalDtype(exy__hmogk, scbhv__pxob,
            rqw__nbqn, ltps__zyfs, wcjj__qvvfg)
    elif typ_enum_list[0] == SeriesDtypeEnum.DatetimeIndexType.value:
        koifd__mho, xewg__welg = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return koifd__mho, DatetimeIndexType(xewg__welg)
    elif typ_enum_list[0] == SeriesDtypeEnum.NumericIndexType.value:
        koifd__mho, dtype = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        koifd__mho, xewg__welg = _dtype_from_type_enum_list_recursor(koifd__mho
            )
        koifd__mho, ltps__zyfs = _dtype_from_type_enum_list_recursor(koifd__mho
            )
        return koifd__mho, NumericIndexType(dtype, xewg__welg, ltps__zyfs)
    elif typ_enum_list[0] == SeriesDtypeEnum.PeriodIndexType.value:
        koifd__mho, teyx__qns = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        koifd__mho, xewg__welg = _dtype_from_type_enum_list_recursor(koifd__mho
            )
        return koifd__mho, PeriodIndexType(teyx__qns, xewg__welg)
    elif typ_enum_list[0] == SeriesDtypeEnum.CategoricalIndexType.value:
        koifd__mho, ltps__zyfs = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        koifd__mho, xewg__welg = _dtype_from_type_enum_list_recursor(koifd__mho
            )
        return koifd__mho, CategoricalIndexType(ltps__zyfs, xewg__welg)
    elif typ_enum_list[0] == SeriesDtypeEnum.RangeIndexType.value:
        koifd__mho, xewg__welg = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return koifd__mho, RangeIndexType(xewg__welg)
    elif typ_enum_list[0] == SeriesDtypeEnum.StringIndexType.value:
        koifd__mho, xewg__welg = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return koifd__mho, StringIndexType(xewg__welg)
    elif typ_enum_list[0] == SeriesDtypeEnum.BinaryIndexType.value:
        koifd__mho, xewg__welg = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return koifd__mho, BinaryIndexType(xewg__welg)
    elif typ_enum_list[0] == SeriesDtypeEnum.TimedeltaIndexType.value:
        koifd__mho, xewg__welg = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return koifd__mho, TimedeltaIndexType(xewg__welg)
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
        umgiw__vwy = get_overload_const_int(typ)
        if numba.types.maybe_literal(umgiw__vwy) == typ:
            return [SeriesDtypeEnum.LiteralType.value, umgiw__vwy]
    elif is_overload_constant_str(typ):
        umgiw__vwy = get_overload_const_str(typ)
        if numba.types.maybe_literal(umgiw__vwy) == typ:
            return [SeriesDtypeEnum.LiteralType.value, umgiw__vwy]
    elif is_overload_constant_bool(typ):
        umgiw__vwy = get_overload_const_bool(typ)
        if numba.types.maybe_literal(umgiw__vwy) == typ:
            return [SeriesDtypeEnum.LiteralType.value, umgiw__vwy]
    elif isinstance(typ, IntegerArrayType):
        return [SeriesDtypeEnum.IntegerArray.value
            ] + _dtype_to_type_enum_list_recursor(typ.dtype)
    elif bodo.utils.utils.is_array_typ(typ, False):
        return [SeriesDtypeEnum.ARRAY.value
            ] + _dtype_to_type_enum_list_recursor(typ.dtype)
    elif isinstance(typ, StructType):
        xsvb__pqi = [SeriesDtypeEnum.STRUCT.value, len(typ.names)]
        for xhg__wgc in typ.names:
            xsvb__pqi.append(xhg__wgc)
        for hgbkr__njfof in typ.data:
            xsvb__pqi += _dtype_to_type_enum_list_recursor(hgbkr__njfof)
        return xsvb__pqi
    elif isinstance(typ, bodo.libs.decimal_arr_ext.Decimal128Type):
        return [SeriesDtypeEnum.Decimal.value, typ.precision, typ.scale]
    elif isinstance(typ, PDCategoricalDtype):
        ttsg__tvge = _dtype_to_type_enum_list_recursor(typ.categories)
        afo__swsdi = _dtype_to_type_enum_list_recursor(typ.elem_type)
        cfnr__wsnzr = _dtype_to_type_enum_list_recursor(typ.ordered)
        umzi__inm = _dtype_to_type_enum_list_recursor(typ.data)
        vdz__qzauc = _dtype_to_type_enum_list_recursor(typ.int_type)
        return [SeriesDtypeEnum.CategoricalType.value
            ] + ttsg__tvge + afo__swsdi + cfnr__wsnzr + umzi__inm + vdz__qzauc
    elif isinstance(typ, DatetimeIndexType):
        return [SeriesDtypeEnum.DatetimeIndexType.value
            ] + _dtype_to_type_enum_list_recursor(typ.name_typ)
    elif isinstance(typ, NumericIndexType):
        if upcast_numeric_index:
            if isinstance(typ.dtype, types.Float):
                hxcca__dkx = types.float64
                wfqca__zuel = types.Array(hxcca__dkx, 1, 'C')
            elif typ.dtype in {types.int8, types.int16, types.int32, types.
                int64}:
                hxcca__dkx = types.int64
                wfqca__zuel = types.Array(hxcca__dkx, 1, 'C')
            elif typ.dtype in {types.uint8, types.uint16, types.uint32,
                types.uint64}:
                hxcca__dkx = types.uint64
                wfqca__zuel = types.Array(hxcca__dkx, 1, 'C')
            elif typ.dtype == types.bool_:
                hxcca__dkx = typ.dtype
                wfqca__zuel = typ.data
            else:
                raise GuardException('Unable to convert type')
            return [SeriesDtypeEnum.NumericIndexType.value
                ] + _dtype_to_type_enum_list_recursor(hxcca__dkx
                ) + _dtype_to_type_enum_list_recursor(typ.name_typ
                ) + _dtype_to_type_enum_list_recursor(wfqca__zuel)
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
                jfvo__sze = S._bodo_meta['type_metadata'][1]
                return _dtype_from_type_enum_list(jfvo__sze)
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
        zuzxr__bmc = S.dtype.unit
        if zuzxr__bmc != 'ns':
            raise BodoError("Timezone-aware datetime data requires 'ns' units")
        dwx__gon = bodo.libs.pd_datetime_arr_ext.get_pytz_type_info(S.dtype.tz)
        return PandasDatetimeTZDtype(dwx__gon)
    try:
        return numpy_support.from_dtype(S.dtype)
    except:
        raise BodoError(
            f'data type {S.dtype} for column {S.name} not supported yet')


def _get_use_df_parent_obj_flag(builder, context, pyapi, parent_obj, n_cols):
    if n_cols is None:
        return context.get_constant(types.bool_, False)
    drrvd__kxrl = cgutils.is_not_null(builder, parent_obj)
    gyi__drq = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with builder.if_then(drrvd__kxrl):
        ibov__oncmz = pyapi.object_getattr_string(parent_obj, 'columns')
        fgakq__hcilb = pyapi.call_method(ibov__oncmz, '__len__', ())
        builder.store(pyapi.long_as_longlong(fgakq__hcilb), gyi__drq)
        pyapi.decref(fgakq__hcilb)
        pyapi.decref(ibov__oncmz)
    use_parent_obj = builder.and_(drrvd__kxrl, builder.icmp_unsigned('==',
        builder.load(gyi__drq), context.get_constant(types.int64, n_cols)))
    return use_parent_obj


def _get_df_columns_obj(c, builder, context, pyapi, df_typ, dataframe_payload):
    if df_typ.has_runtime_cols:
        pjy__xcpl = df_typ.runtime_colname_typ
        context.nrt.incref(builder, pjy__xcpl, dataframe_payload.columns)
        return pyapi.from_native_value(pjy__xcpl, dataframe_payload.columns,
            c.env_manager)
    if all(isinstance(c, int) for c in df_typ.columns):
        lwqp__bjw = np.array(df_typ.columns, 'int64')
    elif all(isinstance(c, str) for c in df_typ.columns):
        lwqp__bjw = pd.array(df_typ.columns, 'string')
    else:
        lwqp__bjw = df_typ.columns
    uwc__ehhup = numba.typeof(lwqp__bjw)
    ahj__rss = context.get_constant_generic(builder, uwc__ehhup, lwqp__bjw)
    girsq__iorqc = pyapi.from_native_value(uwc__ehhup, ahj__rss, c.env_manager)
    return girsq__iorqc


def _create_initial_df_object(builder, context, pyapi, c, df_typ, obj,
    dataframe_payload, res, use_parent_obj):
    with c.builder.if_else(use_parent_obj) as (nthvm__lfze, weius__yurr):
        with nthvm__lfze:
            pyapi.incref(obj)
            uqvhf__amz = context.insert_const_string(c.builder.module, 'numpy')
            fqqi__ijiq = pyapi.import_module_noblock(uqvhf__amz)
            if df_typ.has_runtime_cols:
                psiub__bhcr = 0
            else:
                psiub__bhcr = len(df_typ.columns)
            fjpmw__runil = pyapi.long_from_longlong(lir.Constant(lir.
                IntType(64), psiub__bhcr))
            erzh__eqk = pyapi.call_method(fqqi__ijiq, 'arange', (fjpmw__runil,)
                )
            pyapi.object_setattr_string(obj, 'columns', erzh__eqk)
            pyapi.decref(fqqi__ijiq)
            pyapi.decref(erzh__eqk)
            pyapi.decref(fjpmw__runil)
        with weius__yurr:
            context.nrt.incref(builder, df_typ.index, dataframe_payload.index)
            fjzt__yygpu = c.pyapi.from_native_value(df_typ.index,
                dataframe_payload.index, c.env_manager)
            uqvhf__amz = context.insert_const_string(c.builder.module, 'pandas'
                )
            fqqi__ijiq = pyapi.import_module_noblock(uqvhf__amz)
            df_obj = pyapi.call_method(fqqi__ijiq, 'DataFrame', (pyapi.
                borrow_none(), fjzt__yygpu))
            pyapi.decref(fqqi__ijiq)
            pyapi.decref(fjzt__yygpu)
            builder.store(df_obj, res)


@box(DataFrameType)
def box_dataframe(typ, val, c):
    from bodo.hiframes.table import box_table
    context = c.context
    builder = c.builder
    pyapi = c.pyapi
    dataframe_payload = bodo.hiframes.pd_dataframe_ext.get_dataframe_payload(c
        .context, c.builder, typ, val)
    yvym__uyum = cgutils.create_struct_proxy(typ)(context, builder, value=val)
    n_cols = len(typ.columns) if not typ.has_runtime_cols else None
    obj = yvym__uyum.parent
    res = cgutils.alloca_once_value(builder, obj)
    use_parent_obj = _get_use_df_parent_obj_flag(builder, context, pyapi,
        obj, n_cols)
    _create_initial_df_object(builder, context, pyapi, c, typ, obj,
        dataframe_payload, res, use_parent_obj)
    if typ.is_table_format:
        miwq__ktyt = typ.table_type
        jkzk__djwkd = builder.extract_value(dataframe_payload.data, 0)
        context.nrt.incref(builder, miwq__ktyt, jkzk__djwkd)
        aaq__ifc = box_table(miwq__ktyt, jkzk__djwkd, c, builder.not_(
            use_parent_obj))
        with builder.if_else(use_parent_obj) as (rgql__hta, pjc__khcmb):
            with rgql__hta:
                pbhrb__yagsr = pyapi.object_getattr_string(aaq__ifc, 'arrays')
                knd__lutdx = c.pyapi.make_none()
                if n_cols is None:
                    fgakq__hcilb = pyapi.call_method(pbhrb__yagsr,
                        '__len__', ())
                    ugl__wct = pyapi.long_as_longlong(fgakq__hcilb)
                    pyapi.decref(fgakq__hcilb)
                else:
                    ugl__wct = context.get_constant(types.int64, n_cols)
                with cgutils.for_range(builder, ugl__wct) as kfs__liwq:
                    i = kfs__liwq.index
                    zyhvm__bzxwx = pyapi.list_getitem(pbhrb__yagsr, i)
                    llcl__ekz = c.builder.icmp_unsigned('!=', zyhvm__bzxwx,
                        knd__lutdx)
                    with builder.if_then(llcl__ekz):
                        iwpkx__npzh = pyapi.long_from_longlong(i)
                        df_obj = builder.load(res)
                        pyapi.object_setitem(df_obj, iwpkx__npzh, zyhvm__bzxwx)
                        pyapi.decref(iwpkx__npzh)
                pyapi.decref(pbhrb__yagsr)
                pyapi.decref(knd__lutdx)
            with pjc__khcmb:
                df_obj = builder.load(res)
                fjzt__yygpu = pyapi.object_getattr_string(df_obj, 'index')
                oedo__xbl = c.pyapi.call_method(aaq__ifc, 'to_pandas', (
                    fjzt__yygpu,))
                builder.store(oedo__xbl, res)
                pyapi.decref(df_obj)
                pyapi.decref(fjzt__yygpu)
        pyapi.decref(aaq__ifc)
    else:
        ljqzv__tyo = [builder.extract_value(dataframe_payload.data, i) for
            i in range(n_cols)]
        migbh__wahl = typ.data
        for i, urpq__rho, ytu__vnna in zip(range(n_cols), ljqzv__tyo,
            migbh__wahl):
            gcsue__qvox = cgutils.alloca_once_value(builder, urpq__rho)
            ldb__ujgnr = cgutils.alloca_once_value(builder, context.
                get_constant_null(ytu__vnna))
            llcl__ekz = builder.not_(is_ll_eq(builder, gcsue__qvox, ldb__ujgnr)
                )
            jxhse__skbrp = builder.or_(builder.not_(use_parent_obj),
                builder.and_(use_parent_obj, llcl__ekz))
            with builder.if_then(jxhse__skbrp):
                iwpkx__npzh = pyapi.long_from_longlong(context.get_constant
                    (types.int64, i))
                context.nrt.incref(builder, ytu__vnna, urpq__rho)
                arr_obj = pyapi.from_native_value(ytu__vnna, urpq__rho, c.
                    env_manager)
                df_obj = builder.load(res)
                pyapi.object_setitem(df_obj, iwpkx__npzh, arr_obj)
                pyapi.decref(arr_obj)
                pyapi.decref(iwpkx__npzh)
    df_obj = builder.load(res)
    girsq__iorqc = _get_df_columns_obj(c, builder, context, pyapi, typ,
        dataframe_payload)
    pyapi.object_setattr_string(df_obj, 'columns', girsq__iorqc)
    pyapi.decref(girsq__iorqc)
    _set_bodo_meta_dataframe(c, df_obj, typ)
    c.context.nrt.decref(c.builder, typ, val)
    return df_obj


def get_df_obj_column_codegen(context, builder, pyapi, df_obj, col_ind,
    data_typ):
    knd__lutdx = pyapi.borrow_none()
    pfq__offr = pyapi.unserialize(pyapi.serialize_object(slice))
    eveb__iymt = pyapi.call_function_objargs(pfq__offr, [knd__lutdx])
    svnlg__ejzbu = pyapi.long_from_longlong(col_ind)
    plqar__vzr = pyapi.tuple_pack([eveb__iymt, svnlg__ejzbu])
    nkidj__vged = pyapi.object_getattr_string(df_obj, 'iloc')
    qrr__ippr = pyapi.object_getitem(nkidj__vged, plqar__vzr)
    if isinstance(data_typ, bodo.DatetimeArrayType):
        ponn__coz = pyapi.object_getattr_string(qrr__ippr, 'array')
    else:
        ponn__coz = pyapi.object_getattr_string(qrr__ippr, 'values')
    if isinstance(data_typ, types.Array):
        bwls__ceeyf = context.insert_const_string(builder.module, 'numpy')
        ftdpe__vfz = pyapi.import_module_noblock(bwls__ceeyf)
        arr_obj = pyapi.call_method(ftdpe__vfz, 'ascontiguousarray', (
            ponn__coz,))
        pyapi.decref(ponn__coz)
        pyapi.decref(ftdpe__vfz)
    else:
        arr_obj = ponn__coz
    pyapi.decref(pfq__offr)
    pyapi.decref(eveb__iymt)
    pyapi.decref(svnlg__ejzbu)
    pyapi.decref(plqar__vzr)
    pyapi.decref(nkidj__vged)
    pyapi.decref(qrr__ippr)
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
        yvym__uyum = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        arr_obj = get_df_obj_column_codegen(context, builder, pyapi,
            yvym__uyum.parent, args[1], data_typ)
        uts__eerf = _unbox_series_data(data_typ.dtype, data_typ, arr_obj, c)
        c.pyapi.decref(arr_obj)
        dataframe_payload = (bodo.hiframes.pd_dataframe_ext.
            get_dataframe_payload(c.context, c.builder, df_typ, args[0]))
        if df_typ.is_table_format:
            jkzk__djwkd = cgutils.create_struct_proxy(df_typ.table_type)(c.
                context, c.builder, builder.extract_value(dataframe_payload
                .data, 0))
            pzih__dbhg = df_typ.table_type.type_to_blk[data_typ]
            zgxy__iyi = getattr(jkzk__djwkd, f'block_{pzih__dbhg}')
            cgr__fdty = ListInstance(c.context, c.builder, types.List(
                data_typ), zgxy__iyi)
            oye__wdye = context.get_constant(types.int64, df_typ.table_type
                .block_offsets[col_ind])
            cgr__fdty.inititem(oye__wdye, uts__eerf.value, incref=False)
        else:
            dataframe_payload.data = builder.insert_value(dataframe_payload
                .data, uts__eerf.value, col_ind)
        srrad__sgrey = DataFramePayloadType(df_typ)
        cuzai__dfcd = context.nrt.meminfo_data(builder, yvym__uyum.meminfo)
        hwev__muakx = context.get_value_type(srrad__sgrey).as_pointer()
        cuzai__dfcd = builder.bitcast(cuzai__dfcd, hwev__muakx)
        builder.store(dataframe_payload._getvalue(), cuzai__dfcd)
    return signature(types.none, df, i), codegen


@numba.njit
def unbox_col_if_needed(df, i):
    if bodo.hiframes.pd_dataframe_ext.has_parent(df
        ) and bodo.hiframes.pd_dataframe_ext._column_needs_unboxing(df, i):
        bodo.hiframes.boxing.unbox_dataframe_column(df, i)


@unbox(SeriesType)
def unbox_series(typ, val, c):
    if isinstance(typ.data, DatetimeArrayType):
        ponn__coz = c.pyapi.object_getattr_string(val, 'array')
    else:
        ponn__coz = c.pyapi.object_getattr_string(val, 'values')
    if isinstance(typ.data, types.Array):
        bwls__ceeyf = c.context.insert_const_string(c.builder.module, 'numpy')
        ftdpe__vfz = c.pyapi.import_module_noblock(bwls__ceeyf)
        arr_obj = c.pyapi.call_method(ftdpe__vfz, 'ascontiguousarray', (
            ponn__coz,))
        c.pyapi.decref(ponn__coz)
        c.pyapi.decref(ftdpe__vfz)
    else:
        arr_obj = ponn__coz
    ehwgn__rttdd = _unbox_series_data(typ.dtype, typ.data, arr_obj, c).value
    fjzt__yygpu = c.pyapi.object_getattr_string(val, 'index')
    ecz__httl = c.pyapi.to_native_value(typ.index, fjzt__yygpu).value
    lrt__ibnt = c.pyapi.object_getattr_string(val, 'name')
    pxseq__gqyy = c.pyapi.to_native_value(typ.name_typ, lrt__ibnt).value
    jid__apjr = bodo.hiframes.pd_series_ext.construct_series(c.context, c.
        builder, typ, ehwgn__rttdd, ecz__httl, pxseq__gqyy)
    c.pyapi.decref(arr_obj)
    c.pyapi.decref(fjzt__yygpu)
    c.pyapi.decref(lrt__ibnt)
    return NativeValue(jid__apjr)


def _unbox_series_data(dtype, data_typ, arr_obj, c):
    if data_typ == string_array_split_view_type:
        afvad__yycf = c.context.make_helper(c.builder,
            string_array_split_view_type)
        return NativeValue(afvad__yycf._getvalue())
    return c.pyapi.to_native_value(data_typ, arr_obj)


@box(HeterogeneousSeriesType)
@box(SeriesType)
def box_series(typ, val, c):
    uqvhf__amz = c.context.insert_const_string(c.builder.module, 'pandas')
    fhxm__gncy = c.pyapi.import_module_noblock(uqvhf__amz)
    vvldv__ekn = bodo.hiframes.pd_series_ext.get_series_payload(c.context,
        c.builder, typ, val)
    c.context.nrt.incref(c.builder, typ.data, vvldv__ekn.data)
    c.context.nrt.incref(c.builder, typ.index, vvldv__ekn.index)
    c.context.nrt.incref(c.builder, typ.name_typ, vvldv__ekn.name)
    arr_obj = c.pyapi.from_native_value(typ.data, vvldv__ekn.data, c.
        env_manager)
    fjzt__yygpu = c.pyapi.from_native_value(typ.index, vvldv__ekn.index, c.
        env_manager)
    lrt__ibnt = c.pyapi.from_native_value(typ.name_typ, vvldv__ekn.name, c.
        env_manager)
    if isinstance(typ, HeterogeneousSeriesType) and isinstance(typ.data,
        bodo.NullableTupleType):
        dtype = c.pyapi.unserialize(c.pyapi.serialize_object(object))
    else:
        dtype = c.pyapi.make_none()
    res = c.pyapi.call_method(fhxm__gncy, 'Series', (arr_obj, fjzt__yygpu,
        dtype, lrt__ibnt))
    c.pyapi.decref(arr_obj)
    c.pyapi.decref(fjzt__yygpu)
    c.pyapi.decref(lrt__ibnt)
    if isinstance(typ, HeterogeneousSeriesType) and isinstance(typ.data,
        bodo.NullableTupleType):
        c.pyapi.decref(dtype)
    _set_bodo_meta_series(res, c, typ)
    c.pyapi.decref(fhxm__gncy)
    c.context.nrt.decref(c.builder, typ, val)
    return res


def type_enum_list_to_py_list_obj(pyapi, context, builder, env_manager,
    typ_list):
    ynyr__tvsi = []
    for ezbe__zaoub in typ_list:
        if isinstance(ezbe__zaoub, int) and not isinstance(ezbe__zaoub, bool):
            nfzur__rum = pyapi.long_from_longlong(lir.Constant(lir.IntType(
                64), ezbe__zaoub))
        else:
            nofr__ojzxb = numba.typeof(ezbe__zaoub)
            aame__njkg = context.get_constant_generic(builder, nofr__ojzxb,
                ezbe__zaoub)
            nfzur__rum = pyapi.from_native_value(nofr__ojzxb, aame__njkg,
                env_manager)
        ynyr__tvsi.append(nfzur__rum)
    ensai__gzdt = pyapi.list_pack(ynyr__tvsi)
    for val in ynyr__tvsi:
        pyapi.decref(val)
    return ensai__gzdt


def _set_bodo_meta_dataframe(c, obj, typ):
    pyapi = c.pyapi
    context = c.context
    builder = c.builder
    obnd__obi = not typ.has_runtime_cols and (not typ.is_table_format or 
        len(typ.columns) < TABLE_FORMAT_THRESHOLD)
    kekg__jwyn = 2 if obnd__obi else 1
    jyzgc__fod = pyapi.dict_new(kekg__jwyn)
    tubj__kqoz = pyapi.long_from_longlong(lir.Constant(lir.IntType(64), typ
        .dist.value))
    pyapi.dict_setitem_string(jyzgc__fod, 'dist', tubj__kqoz)
    pyapi.decref(tubj__kqoz)
    if obnd__obi:
        kyep__lsxea = _dtype_to_type_enum_list(typ.index)
        if kyep__lsxea != None:
            mrd__fyrxr = type_enum_list_to_py_list_obj(pyapi, context,
                builder, c.env_manager, kyep__lsxea)
        else:
            mrd__fyrxr = pyapi.make_none()
        hmlq__szqgy = []
        for dtype in typ.data:
            typ_list = _dtype_to_type_enum_list(dtype)
            if typ_list != None:
                ensai__gzdt = type_enum_list_to_py_list_obj(pyapi, context,
                    builder, c.env_manager, typ_list)
            else:
                ensai__gzdt = pyapi.make_none()
            hmlq__szqgy.append(ensai__gzdt)
        hix__izxew = pyapi.list_pack(hmlq__szqgy)
        pwmj__ipyr = pyapi.list_pack([mrd__fyrxr, hix__izxew])
        for val in hmlq__szqgy:
            pyapi.decref(val)
        pyapi.dict_setitem_string(jyzgc__fod, 'type_metadata', pwmj__ipyr)
    pyapi.object_setattr_string(obj, '_bodo_meta', jyzgc__fod)
    pyapi.decref(jyzgc__fod)


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
    jyzgc__fod = pyapi.dict_new(2)
    tubj__kqoz = pyapi.long_from_longlong(lir.Constant(lir.IntType(64), typ
        .dist.value))
    kyep__lsxea = _dtype_to_type_enum_list(typ.index)
    if kyep__lsxea != None:
        mrd__fyrxr = type_enum_list_to_py_list_obj(pyapi, context, builder,
            c.env_manager, kyep__lsxea)
    else:
        mrd__fyrxr = pyapi.make_none()
    dtype = get_series_dtype_handle_null_int_and_hetrogenous(typ)
    if dtype != None:
        typ_list = _dtype_to_type_enum_list(dtype)
        if typ_list != None:
            ibggm__ppamr = type_enum_list_to_py_list_obj(pyapi, context,
                builder, c.env_manager, typ_list)
        else:
            ibggm__ppamr = pyapi.make_none()
    else:
        ibggm__ppamr = pyapi.make_none()
    ojxr__okjs = pyapi.list_pack([mrd__fyrxr, ibggm__ppamr])
    pyapi.dict_setitem_string(jyzgc__fod, 'type_metadata', ojxr__okjs)
    pyapi.decref(ojxr__okjs)
    pyapi.dict_setitem_string(jyzgc__fod, 'dist', tubj__kqoz)
    pyapi.object_setattr_string(obj, '_bodo_meta', jyzgc__fod)
    pyapi.decref(jyzgc__fod)
    pyapi.decref(tubj__kqoz)


@typeof_impl.register(np.ndarray)
def _typeof_ndarray(val, c):
    try:
        dtype = numba.np.numpy_support.from_dtype(val.dtype)
    except NotImplementedError as puz__zyd:
        dtype = types.pyobject
    if dtype == types.pyobject:
        return _infer_ndarray_obj_dtype(val)
    qpzg__wfuk = numba.np.numpy_support.map_layout(val)
    auowr__xvevl = not val.flags.writeable
    return types.Array(dtype, val.ndim, qpzg__wfuk, readonly=auowr__xvevl)


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
    tgi__uyu = val[i]
    if isinstance(tgi__uyu, str):
        return (bodo.dict_str_arr_type if _use_dict_str_type else
            string_array_type)
    elif isinstance(tgi__uyu, bytes):
        return binary_array_type
    elif isinstance(tgi__uyu, bool):
        return bodo.libs.bool_arr_ext.boolean_array
    elif isinstance(tgi__uyu, (int, np.int32, np.int64)):
        return bodo.libs.int_arr_ext.IntegerArrayType(numba.typeof(tgi__uyu))
    elif isinstance(tgi__uyu, (dict, Dict)) and all(isinstance(xjobb__ixv,
        str) for xjobb__ixv in tgi__uyu.keys()):
        psx__soe = tuple(tgi__uyu.keys())
        ymgln__gzst = tuple(_get_struct_value_arr_type(v) for v in tgi__uyu
            .values())
        return StructArrayType(ymgln__gzst, psx__soe)
    elif isinstance(tgi__uyu, (dict, Dict)):
        eogcr__eva = numba.typeof(_value_to_array(list(tgi__uyu.keys())))
        rcca__esk = numba.typeof(_value_to_array(list(tgi__uyu.values())))
        eogcr__eva = to_str_arr_if_dict_array(eogcr__eva)
        rcca__esk = to_str_arr_if_dict_array(rcca__esk)
        return MapArrayType(eogcr__eva, rcca__esk)
    elif isinstance(tgi__uyu, tuple):
        ymgln__gzst = tuple(_get_struct_value_arr_type(v) for v in tgi__uyu)
        return TupleArrayType(ymgln__gzst)
    if isinstance(tgi__uyu, (list, np.ndarray, pd.arrays.BooleanArray, pd.
        arrays.IntegerArray, pd.arrays.StringArray)):
        if isinstance(tgi__uyu, list):
            tgi__uyu = _value_to_array(tgi__uyu)
        ckk__ihggl = numba.typeof(tgi__uyu)
        ckk__ihggl = to_str_arr_if_dict_array(ckk__ihggl)
        return ArrayItemArrayType(ckk__ihggl)
    if isinstance(tgi__uyu, datetime.date):
        return datetime_date_array_type
    if isinstance(tgi__uyu, datetime.timedelta):
        return datetime_timedelta_array_type
    if isinstance(tgi__uyu, decimal.Decimal):
        return DecimalArrayType(38, 18)
    raise BodoError(f'Unsupported object array with first value: {tgi__uyu}')


def _value_to_array(val):
    assert isinstance(val, (list, dict, Dict))
    if isinstance(val, (dict, Dict)):
        val = dict(val)
        return np.array([val], np.object_)
    fdh__hwvu = val.copy()
    fdh__hwvu.append(None)
    urpq__rho = np.array(fdh__hwvu, np.object_)
    if len(val) and isinstance(val[0], float):
        urpq__rho = np.array(val, np.float64)
    return urpq__rho


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
    ytu__vnna = dtype_to_array_type(numba.typeof(v))
    if isinstance(v, (int, bool)):
        ytu__vnna = to_nullable_type(ytu__vnna)
    return ytu__vnna
