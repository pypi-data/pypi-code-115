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
    tum__cmfn = tuple(val.columns.to_list())
    aotqq__cjqc = get_hiframes_dtypes(val)
    if (len(val.index) == 0 and val.index.dtype == np.dtype('O') and
        hasattr(val, '_bodo_meta') and val._bodo_meta is not None and 
        'type_metadata' in val._bodo_meta and val._bodo_meta[
        'type_metadata'] is not None and len(val._bodo_meta['type_metadata'
        ][1]) == len(val.columns) and val._bodo_meta['type_metadata'][0] is not
        None):
        fyvdf__jpx = _dtype_from_type_enum_list(val._bodo_meta[
            'type_metadata'][0])
    else:
        fyvdf__jpx = numba.typeof(val.index)
    dbs__exr = Distribution(val._bodo_meta['dist']) if hasattr(val,
        '_bodo_meta') and val._bodo_meta is not None else Distribution.REP
    kil__tkvte = len(aotqq__cjqc) >= TABLE_FORMAT_THRESHOLD
    return DataFrameType(aotqq__cjqc, fyvdf__jpx, tum__cmfn, dbs__exr,
        is_table_format=kil__tkvte)


@typeof_impl.register(pd.Series)
def typeof_pd_series(val, c):
    from bodo.transforms.distributed_analysis import Distribution
    dbs__exr = Distribution(val._bodo_meta['dist']) if hasattr(val,
        '_bodo_meta') and val._bodo_meta is not None else Distribution.REP
    if (len(val.index) == 0 and val.index.dtype == np.dtype('O') and
        hasattr(val, '_bodo_meta') and val._bodo_meta is not None and 
        'type_metadata' in val._bodo_meta and val._bodo_meta[
        'type_metadata'] is not None and val._bodo_meta['type_metadata'][0]
         is not None):
        mcp__ool = _dtype_from_type_enum_list(val._bodo_meta[
            'type_metadata'][0])
    else:
        mcp__ool = numba.typeof(val.index)
    dtype = _infer_series_dtype(val)
    lpayz__bamdz = dtype_to_array_type(dtype)
    if _use_dict_str_type and lpayz__bamdz == string_array_type:
        lpayz__bamdz = bodo.dict_str_arr_type
    return SeriesType(dtype, data=lpayz__bamdz, index=mcp__ool, name_typ=
        numba.typeof(val.name), dist=dbs__exr)


@unbox(DataFrameType)
def unbox_dataframe(typ, val, c):
    check_runtime_cols_unsupported(typ, 'Unboxing')
    dhfzp__ybfhe = c.pyapi.object_getattr_string(val, 'index')
    smfvh__xga = c.pyapi.to_native_value(typ.index, dhfzp__ybfhe).value
    c.pyapi.decref(dhfzp__ybfhe)
    if typ.is_table_format:
        amqsc__sbhxd = cgutils.create_struct_proxy(typ.table_type)(c.
            context, c.builder)
        amqsc__sbhxd.parent = val
        for njoo__lou, dyju__sgvo in typ.table_type.type_to_blk.items():
            uqqym__eoqct = c.context.get_constant(types.int64, len(typ.
                table_type.block_to_arr_ind[dyju__sgvo]))
            zdq__uzj, fogy__zmebw = ListInstance.allocate_ex(c.context, c.
                builder, types.List(njoo__lou), uqqym__eoqct)
            fogy__zmebw.size = uqqym__eoqct
            setattr(amqsc__sbhxd, f'block_{dyju__sgvo}', fogy__zmebw.value)
        fpoo__aeq = c.pyapi.call_method(val, '__len__', ())
        duf__rdysh = c.pyapi.long_as_longlong(fpoo__aeq)
        c.pyapi.decref(fpoo__aeq)
        amqsc__sbhxd.len = duf__rdysh
        nwljx__qha = c.context.make_tuple(c.builder, types.Tuple([typ.
            table_type]), [amqsc__sbhxd._getvalue()])
    else:
        cljv__jsrjx = [c.context.get_constant_null(njoo__lou) for njoo__lou in
            typ.data]
        nwljx__qha = c.context.make_tuple(c.builder, types.Tuple(typ.data),
            cljv__jsrjx)
    yallg__ggmi = construct_dataframe(c.context, c.builder, typ, nwljx__qha,
        smfvh__xga, val, None)
    return NativeValue(yallg__ggmi)


def get_hiframes_dtypes(df):
    if (hasattr(df, '_bodo_meta') and df._bodo_meta is not None and 
        'type_metadata' in df._bodo_meta and df._bodo_meta['type_metadata']
         is not None and len(df._bodo_meta['type_metadata'][1]) == len(df.
        columns)):
        tgfs__cjxj = df._bodo_meta['type_metadata'][1]
    else:
        tgfs__cjxj = [None] * len(df.columns)
    wnf__pgq = [dtype_to_array_type(_infer_series_dtype(df.iloc[:, i],
        array_metadata=tgfs__cjxj[i])) for i in range(len(df.columns))]
    wnf__pgq = [(bodo.dict_str_arr_type if _use_dict_str_type and njoo__lou ==
        string_array_type else njoo__lou) for njoo__lou in wnf__pgq]
    return tuple(wnf__pgq)


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
    veah__fdawn, typ = _dtype_from_type_enum_list_recursor(typ_enum_list)
    if len(veah__fdawn) != 0:
        raise_bodo_error(
            f"""Unexpected Internal Error while converting typing metadata: Dtype list was not fully consumed.
 Input typ_enum_list: {typ_enum_list}.
Remainder: {veah__fdawn}. Please file the error here: https://github.com/Bodo-inc/Feedback"""
            )
    return typ


def _dtype_from_type_enum_list_recursor(typ_enum_list):
    if len(typ_enum_list) == 0:
        raise_bodo_error('Unable to infer dtype from empty typ_enum_list')
    elif typ_enum_list[0] in _one_to_one_enum_to_type_map:
        return typ_enum_list[1:], _one_to_one_enum_to_type_map[typ_enum_list[0]
            ]
    elif typ_enum_list[0] == SeriesDtypeEnum.IntegerArray.value:
        mzpn__pzs, typ = _dtype_from_type_enum_list_recursor(typ_enum_list[1:])
        return mzpn__pzs, IntegerArrayType(typ)
    elif typ_enum_list[0] == SeriesDtypeEnum.ARRAY.value:
        mzpn__pzs, typ = _dtype_from_type_enum_list_recursor(typ_enum_list[1:])
        return mzpn__pzs, dtype_to_array_type(typ)
    elif typ_enum_list[0] == SeriesDtypeEnum.Decimal.value:
        mhw__bogw = typ_enum_list[1]
        zjqz__erc = typ_enum_list[2]
        return typ_enum_list[3:], Decimal128Type(mhw__bogw, zjqz__erc)
    elif typ_enum_list[0] == SeriesDtypeEnum.STRUCT.value:
        dhii__jtv = typ_enum_list[1]
        opi__oyx = tuple(typ_enum_list[2:2 + dhii__jtv])
        dvztr__owoku = typ_enum_list[2 + dhii__jtv:]
        qkp__cpf = []
        for i in range(dhii__jtv):
            dvztr__owoku, qkk__neym = _dtype_from_type_enum_list_recursor(
                dvztr__owoku)
            qkp__cpf.append(qkk__neym)
        return dvztr__owoku, StructType(tuple(qkp__cpf), opi__oyx)
    elif typ_enum_list[0] == SeriesDtypeEnum.Literal.value:
        if len(typ_enum_list) == 1:
            raise_bodo_error(
                f"Unexpected Internal Error while converting typing metadata: Encountered 'Literal' internal enum value with no value following it. Please file the error here: https://github.com/Bodo-inc/Feedback"
                )
        ciz__ucwvc = typ_enum_list[1]
        dvztr__owoku = typ_enum_list[2:]
        return dvztr__owoku, ciz__ucwvc
    elif typ_enum_list[0] == SeriesDtypeEnum.LiteralType.value:
        if len(typ_enum_list) == 1:
            raise_bodo_error(
                f"Unexpected Internal Error while converting typing metadata: Encountered 'LiteralType' internal enum value with no value following it. Please file the error here: https://github.com/Bodo-inc/Feedback"
                )
        ciz__ucwvc = typ_enum_list[1]
        dvztr__owoku = typ_enum_list[2:]
        return dvztr__owoku, numba.types.literal(ciz__ucwvc)
    elif typ_enum_list[0] == SeriesDtypeEnum.CategoricalType.value:
        dvztr__owoku, eivm__xkst = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        dvztr__owoku, hgjht__bzfh = _dtype_from_type_enum_list_recursor(
            dvztr__owoku)
        dvztr__owoku, lva__vdb = _dtype_from_type_enum_list_recursor(
            dvztr__owoku)
        dvztr__owoku, uhsbb__trdk = _dtype_from_type_enum_list_recursor(
            dvztr__owoku)
        dvztr__owoku, mdd__euvj = _dtype_from_type_enum_list_recursor(
            dvztr__owoku)
        return dvztr__owoku, PDCategoricalDtype(eivm__xkst, hgjht__bzfh,
            lva__vdb, uhsbb__trdk, mdd__euvj)
    elif typ_enum_list[0] == SeriesDtypeEnum.DatetimeIndexType.value:
        dvztr__owoku, zme__ytyb = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return dvztr__owoku, DatetimeIndexType(zme__ytyb)
    elif typ_enum_list[0] == SeriesDtypeEnum.NumericIndexType.value:
        dvztr__owoku, dtype = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        dvztr__owoku, zme__ytyb = _dtype_from_type_enum_list_recursor(
            dvztr__owoku)
        dvztr__owoku, uhsbb__trdk = _dtype_from_type_enum_list_recursor(
            dvztr__owoku)
        return dvztr__owoku, NumericIndexType(dtype, zme__ytyb, uhsbb__trdk)
    elif typ_enum_list[0] == SeriesDtypeEnum.PeriodIndexType.value:
        dvztr__owoku, foin__smizo = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        dvztr__owoku, zme__ytyb = _dtype_from_type_enum_list_recursor(
            dvztr__owoku)
        return dvztr__owoku, PeriodIndexType(foin__smizo, zme__ytyb)
    elif typ_enum_list[0] == SeriesDtypeEnum.CategoricalIndexType.value:
        dvztr__owoku, uhsbb__trdk = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        dvztr__owoku, zme__ytyb = _dtype_from_type_enum_list_recursor(
            dvztr__owoku)
        return dvztr__owoku, CategoricalIndexType(uhsbb__trdk, zme__ytyb)
    elif typ_enum_list[0] == SeriesDtypeEnum.RangeIndexType.value:
        dvztr__owoku, zme__ytyb = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return dvztr__owoku, RangeIndexType(zme__ytyb)
    elif typ_enum_list[0] == SeriesDtypeEnum.StringIndexType.value:
        dvztr__owoku, zme__ytyb = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return dvztr__owoku, StringIndexType(zme__ytyb)
    elif typ_enum_list[0] == SeriesDtypeEnum.BinaryIndexType.value:
        dvztr__owoku, zme__ytyb = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return dvztr__owoku, BinaryIndexType(zme__ytyb)
    elif typ_enum_list[0] == SeriesDtypeEnum.TimedeltaIndexType.value:
        dvztr__owoku, zme__ytyb = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return dvztr__owoku, TimedeltaIndexType(zme__ytyb)
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
        rcue__ompb = get_overload_const_int(typ)
        if numba.types.maybe_literal(rcue__ompb) == typ:
            return [SeriesDtypeEnum.LiteralType.value, rcue__ompb]
    elif is_overload_constant_str(typ):
        rcue__ompb = get_overload_const_str(typ)
        if numba.types.maybe_literal(rcue__ompb) == typ:
            return [SeriesDtypeEnum.LiteralType.value, rcue__ompb]
    elif is_overload_constant_bool(typ):
        rcue__ompb = get_overload_const_bool(typ)
        if numba.types.maybe_literal(rcue__ompb) == typ:
            return [SeriesDtypeEnum.LiteralType.value, rcue__ompb]
    elif isinstance(typ, IntegerArrayType):
        return [SeriesDtypeEnum.IntegerArray.value
            ] + _dtype_to_type_enum_list_recursor(typ.dtype)
    elif bodo.utils.utils.is_array_typ(typ, False):
        return [SeriesDtypeEnum.ARRAY.value
            ] + _dtype_to_type_enum_list_recursor(typ.dtype)
    elif isinstance(typ, StructType):
        zbyt__ocmhz = [SeriesDtypeEnum.STRUCT.value, len(typ.names)]
        for dew__ini in typ.names:
            zbyt__ocmhz.append(dew__ini)
        for rqbcf__xmjc in typ.data:
            zbyt__ocmhz += _dtype_to_type_enum_list_recursor(rqbcf__xmjc)
        return zbyt__ocmhz
    elif isinstance(typ, bodo.libs.decimal_arr_ext.Decimal128Type):
        return [SeriesDtypeEnum.Decimal.value, typ.precision, typ.scale]
    elif isinstance(typ, PDCategoricalDtype):
        mlmt__mny = _dtype_to_type_enum_list_recursor(typ.categories)
        aev__sflks = _dtype_to_type_enum_list_recursor(typ.elem_type)
        dvry__vqu = _dtype_to_type_enum_list_recursor(typ.ordered)
        rvojb__ybfyx = _dtype_to_type_enum_list_recursor(typ.data)
        dkv__mhgb = _dtype_to_type_enum_list_recursor(typ.int_type)
        return [SeriesDtypeEnum.CategoricalType.value
            ] + mlmt__mny + aev__sflks + dvry__vqu + rvojb__ybfyx + dkv__mhgb
    elif isinstance(typ, DatetimeIndexType):
        return [SeriesDtypeEnum.DatetimeIndexType.value
            ] + _dtype_to_type_enum_list_recursor(typ.name_typ)
    elif isinstance(typ, NumericIndexType):
        if upcast_numeric_index:
            if isinstance(typ.dtype, types.Float):
                pnj__psy = types.float64
                zcxcq__wnpbx = types.Array(pnj__psy, 1, 'C')
            elif typ.dtype in {types.int8, types.int16, types.int32, types.
                int64}:
                pnj__psy = types.int64
                zcxcq__wnpbx = types.Array(pnj__psy, 1, 'C')
            elif typ.dtype in {types.uint8, types.uint16, types.uint32,
                types.uint64}:
                pnj__psy = types.uint64
                zcxcq__wnpbx = types.Array(pnj__psy, 1, 'C')
            elif typ.dtype == types.bool_:
                pnj__psy = typ.dtype
                zcxcq__wnpbx = typ.data
            else:
                raise GuardException('Unable to convert type')
            return [SeriesDtypeEnum.NumericIndexType.value
                ] + _dtype_to_type_enum_list_recursor(pnj__psy
                ) + _dtype_to_type_enum_list_recursor(typ.name_typ
                ) + _dtype_to_type_enum_list_recursor(zcxcq__wnpbx)
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
                wsos__tuq = S._bodo_meta['type_metadata'][1]
                return _dtype_from_type_enum_list(wsos__tuq)
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
        yiuma__zuzxw = S.dtype.unit
        if yiuma__zuzxw != 'ns':
            raise BodoError("Timezone-aware datetime data requires 'ns' units")
        iqxjb__sdkeu = bodo.libs.pd_datetime_arr_ext.get_pytz_type_info(S.
            dtype.tz)
        return PandasDatetimeTZDtype(iqxjb__sdkeu)
    try:
        return numpy_support.from_dtype(S.dtype)
    except:
        raise BodoError(
            f'data type {S.dtype} for column {S.name} not supported yet')


def _get_use_df_parent_obj_flag(builder, context, pyapi, parent_obj, n_cols):
    if n_cols is None:
        return context.get_constant(types.bool_, False)
    cub__keuhi = cgutils.is_not_null(builder, parent_obj)
    zdeu__lyx = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with builder.if_then(cub__keuhi):
        vceea__nwikh = pyapi.object_getattr_string(parent_obj, 'columns')
        fpoo__aeq = pyapi.call_method(vceea__nwikh, '__len__', ())
        builder.store(pyapi.long_as_longlong(fpoo__aeq), zdeu__lyx)
        pyapi.decref(fpoo__aeq)
        pyapi.decref(vceea__nwikh)
    use_parent_obj = builder.and_(cub__keuhi, builder.icmp_unsigned('==',
        builder.load(zdeu__lyx), context.get_constant(types.int64, n_cols)))
    return use_parent_obj


def _get_df_columns_obj(c, builder, context, pyapi, df_typ, dataframe_payload):
    if df_typ.has_runtime_cols:
        atx__jkn = df_typ.runtime_colname_typ
        context.nrt.incref(builder, atx__jkn, dataframe_payload.columns)
        return pyapi.from_native_value(atx__jkn, dataframe_payload.columns,
            c.env_manager)
    if all(isinstance(c, int) for c in df_typ.columns):
        cccb__nzxa = np.array(df_typ.columns, 'int64')
    elif all(isinstance(c, str) for c in df_typ.columns):
        cccb__nzxa = pd.array(df_typ.columns, 'string')
    else:
        cccb__nzxa = df_typ.columns
    cchnn__mgdvq = numba.typeof(cccb__nzxa)
    ryg__wfiw = context.get_constant_generic(builder, cchnn__mgdvq, cccb__nzxa)
    vqqeb__lyq = pyapi.from_native_value(cchnn__mgdvq, ryg__wfiw, c.env_manager
        )
    return vqqeb__lyq


def _create_initial_df_object(builder, context, pyapi, c, df_typ, obj,
    dataframe_payload, res, use_parent_obj):
    with c.builder.if_else(use_parent_obj) as (oixyd__lrknx, jyyi__efabg):
        with oixyd__lrknx:
            pyapi.incref(obj)
            jcab__sohiq = context.insert_const_string(c.builder.module, 'numpy'
                )
            pismz__tikv = pyapi.import_module_noblock(jcab__sohiq)
            if df_typ.has_runtime_cols:
                ubkz__cmcr = 0
            else:
                ubkz__cmcr = len(df_typ.columns)
            qmcq__wfdq = pyapi.long_from_longlong(lir.Constant(lir.IntType(
                64), ubkz__cmcr))
            qvbtq__vsaff = pyapi.call_method(pismz__tikv, 'arange', (
                qmcq__wfdq,))
            pyapi.object_setattr_string(obj, 'columns', qvbtq__vsaff)
            pyapi.decref(pismz__tikv)
            pyapi.decref(qvbtq__vsaff)
            pyapi.decref(qmcq__wfdq)
        with jyyi__efabg:
            context.nrt.incref(builder, df_typ.index, dataframe_payload.index)
            saxh__segm = c.pyapi.from_native_value(df_typ.index,
                dataframe_payload.index, c.env_manager)
            jcab__sohiq = context.insert_const_string(c.builder.module,
                'pandas')
            pismz__tikv = pyapi.import_module_noblock(jcab__sohiq)
            df_obj = pyapi.call_method(pismz__tikv, 'DataFrame', (pyapi.
                borrow_none(), saxh__segm))
            pyapi.decref(pismz__tikv)
            pyapi.decref(saxh__segm)
            builder.store(df_obj, res)


@box(DataFrameType)
def box_dataframe(typ, val, c):
    from bodo.hiframes.table import box_table
    context = c.context
    builder = c.builder
    pyapi = c.pyapi
    dataframe_payload = bodo.hiframes.pd_dataframe_ext.get_dataframe_payload(c
        .context, c.builder, typ, val)
    ylcdu__xvn = cgutils.create_struct_proxy(typ)(context, builder, value=val)
    n_cols = len(typ.columns) if not typ.has_runtime_cols else None
    obj = ylcdu__xvn.parent
    res = cgutils.alloca_once_value(builder, obj)
    use_parent_obj = _get_use_df_parent_obj_flag(builder, context, pyapi,
        obj, n_cols)
    _create_initial_df_object(builder, context, pyapi, c, typ, obj,
        dataframe_payload, res, use_parent_obj)
    if typ.is_table_format:
        rge__pmup = typ.table_type
        amqsc__sbhxd = builder.extract_value(dataframe_payload.data, 0)
        context.nrt.incref(builder, rge__pmup, amqsc__sbhxd)
        vzhs__irlia = box_table(rge__pmup, amqsc__sbhxd, c, builder.not_(
            use_parent_obj))
        with builder.if_else(use_parent_obj) as (vsa__zhy, krsx__zraw):
            with vsa__zhy:
                acv__fzao = pyapi.object_getattr_string(vzhs__irlia, 'arrays')
                ppy__nkje = c.pyapi.make_none()
                if n_cols is None:
                    fpoo__aeq = pyapi.call_method(acv__fzao, '__len__', ())
                    uqqym__eoqct = pyapi.long_as_longlong(fpoo__aeq)
                    pyapi.decref(fpoo__aeq)
                else:
                    uqqym__eoqct = context.get_constant(types.int64, n_cols)
                with cgutils.for_range(builder, uqqym__eoqct) as xvjfr__yzuo:
                    i = xvjfr__yzuo.index
                    qgugw__wemf = pyapi.list_getitem(acv__fzao, i)
                    uul__tily = c.builder.icmp_unsigned('!=', qgugw__wemf,
                        ppy__nkje)
                    with builder.if_then(uul__tily):
                        vjqfa__qrj = pyapi.long_from_longlong(i)
                        df_obj = builder.load(res)
                        pyapi.object_setitem(df_obj, vjqfa__qrj, qgugw__wemf)
                        pyapi.decref(vjqfa__qrj)
                pyapi.decref(acv__fzao)
                pyapi.decref(ppy__nkje)
            with krsx__zraw:
                df_obj = builder.load(res)
                saxh__segm = pyapi.object_getattr_string(df_obj, 'index')
                mexh__wqtk = c.pyapi.call_method(vzhs__irlia, 'to_pandas',
                    (saxh__segm,))
                builder.store(mexh__wqtk, res)
                pyapi.decref(df_obj)
                pyapi.decref(saxh__segm)
        pyapi.decref(vzhs__irlia)
    else:
        djvyh__pudu = [builder.extract_value(dataframe_payload.data, i) for
            i in range(n_cols)]
        huth__gokx = typ.data
        for i, binb__qrw, lpayz__bamdz in zip(range(n_cols), djvyh__pudu,
            huth__gokx):
            tsn__gftpu = cgutils.alloca_once_value(builder, binb__qrw)
            jia__bwua = cgutils.alloca_once_value(builder, context.
                get_constant_null(lpayz__bamdz))
            uul__tily = builder.not_(is_ll_eq(builder, tsn__gftpu, jia__bwua))
            sezki__fbchv = builder.or_(builder.not_(use_parent_obj),
                builder.and_(use_parent_obj, uul__tily))
            with builder.if_then(sezki__fbchv):
                vjqfa__qrj = pyapi.long_from_longlong(context.get_constant(
                    types.int64, i))
                context.nrt.incref(builder, lpayz__bamdz, binb__qrw)
                arr_obj = pyapi.from_native_value(lpayz__bamdz, binb__qrw,
                    c.env_manager)
                df_obj = builder.load(res)
                pyapi.object_setitem(df_obj, vjqfa__qrj, arr_obj)
                pyapi.decref(arr_obj)
                pyapi.decref(vjqfa__qrj)
    df_obj = builder.load(res)
    vqqeb__lyq = _get_df_columns_obj(c, builder, context, pyapi, typ,
        dataframe_payload)
    pyapi.object_setattr_string(df_obj, 'columns', vqqeb__lyq)
    pyapi.decref(vqqeb__lyq)
    _set_bodo_meta_dataframe(c, df_obj, typ)
    c.context.nrt.decref(c.builder, typ, val)
    return df_obj


def get_df_obj_column_codegen(context, builder, pyapi, df_obj, col_ind,
    data_typ):
    ppy__nkje = pyapi.borrow_none()
    yyq__hcuc = pyapi.unserialize(pyapi.serialize_object(slice))
    srml__sxkmg = pyapi.call_function_objargs(yyq__hcuc, [ppy__nkje])
    bbyz__vfiti = pyapi.long_from_longlong(col_ind)
    drqx__gede = pyapi.tuple_pack([srml__sxkmg, bbyz__vfiti])
    qjfbb__ycf = pyapi.object_getattr_string(df_obj, 'iloc')
    ghjai__mly = pyapi.object_getitem(qjfbb__ycf, drqx__gede)
    if isinstance(data_typ, bodo.DatetimeArrayType):
        bleah__oxy = pyapi.object_getattr_string(ghjai__mly, 'array')
    else:
        bleah__oxy = pyapi.object_getattr_string(ghjai__mly, 'values')
    if isinstance(data_typ, types.Array):
        tgn__kvcec = context.insert_const_string(builder.module, 'numpy')
        kvmru__shag = pyapi.import_module_noblock(tgn__kvcec)
        arr_obj = pyapi.call_method(kvmru__shag, 'ascontiguousarray', (
            bleah__oxy,))
        pyapi.decref(bleah__oxy)
        pyapi.decref(kvmru__shag)
    else:
        arr_obj = bleah__oxy
    pyapi.decref(yyq__hcuc)
    pyapi.decref(srml__sxkmg)
    pyapi.decref(bbyz__vfiti)
    pyapi.decref(drqx__gede)
    pyapi.decref(qjfbb__ycf)
    pyapi.decref(ghjai__mly)
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
        ylcdu__xvn = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        arr_obj = get_df_obj_column_codegen(context, builder, pyapi,
            ylcdu__xvn.parent, args[1], data_typ)
        bzwem__omoom = _unbox_series_data(data_typ.dtype, data_typ, arr_obj, c)
        c.pyapi.decref(arr_obj)
        dataframe_payload = (bodo.hiframes.pd_dataframe_ext.
            get_dataframe_payload(c.context, c.builder, df_typ, args[0]))
        if df_typ.is_table_format:
            amqsc__sbhxd = cgutils.create_struct_proxy(df_typ.table_type)(c
                .context, c.builder, builder.extract_value(
                dataframe_payload.data, 0))
            dyju__sgvo = df_typ.table_type.type_to_blk[data_typ]
            ase__rahk = getattr(amqsc__sbhxd, f'block_{dyju__sgvo}')
            xcbp__vej = ListInstance(c.context, c.builder, types.List(
                data_typ), ase__rahk)
            fchh__azs = context.get_constant(types.int64, df_typ.table_type
                .block_offsets[col_ind])
            xcbp__vej.inititem(fchh__azs, bzwem__omoom.value, incref=False)
        else:
            dataframe_payload.data = builder.insert_value(dataframe_payload
                .data, bzwem__omoom.value, col_ind)
        hjqwx__qbi = DataFramePayloadType(df_typ)
        rdda__zqwe = context.nrt.meminfo_data(builder, ylcdu__xvn.meminfo)
        zvfx__zjtf = context.get_value_type(hjqwx__qbi).as_pointer()
        rdda__zqwe = builder.bitcast(rdda__zqwe, zvfx__zjtf)
        builder.store(dataframe_payload._getvalue(), rdda__zqwe)
    return signature(types.none, df, i), codegen


@numba.njit
def unbox_col_if_needed(df, i):
    if bodo.hiframes.pd_dataframe_ext.has_parent(df
        ) and bodo.hiframes.pd_dataframe_ext._column_needs_unboxing(df, i):
        bodo.hiframes.boxing.unbox_dataframe_column(df, i)


@unbox(SeriesType)
def unbox_series(typ, val, c):
    if isinstance(typ.data, DatetimeArrayType):
        bleah__oxy = c.pyapi.object_getattr_string(val, 'array')
    else:
        bleah__oxy = c.pyapi.object_getattr_string(val, 'values')
    if isinstance(typ.data, types.Array):
        tgn__kvcec = c.context.insert_const_string(c.builder.module, 'numpy')
        kvmru__shag = c.pyapi.import_module_noblock(tgn__kvcec)
        arr_obj = c.pyapi.call_method(kvmru__shag, 'ascontiguousarray', (
            bleah__oxy,))
        c.pyapi.decref(bleah__oxy)
        c.pyapi.decref(kvmru__shag)
    else:
        arr_obj = bleah__oxy
    amv__uxt = _unbox_series_data(typ.dtype, typ.data, arr_obj, c).value
    saxh__segm = c.pyapi.object_getattr_string(val, 'index')
    smfvh__xga = c.pyapi.to_native_value(typ.index, saxh__segm).value
    dwoeq__igs = c.pyapi.object_getattr_string(val, 'name')
    saen__max = c.pyapi.to_native_value(typ.name_typ, dwoeq__igs).value
    fozr__pxwxf = bodo.hiframes.pd_series_ext.construct_series(c.context, c
        .builder, typ, amv__uxt, smfvh__xga, saen__max)
    c.pyapi.decref(arr_obj)
    c.pyapi.decref(saxh__segm)
    c.pyapi.decref(dwoeq__igs)
    return NativeValue(fozr__pxwxf)


def _unbox_series_data(dtype, data_typ, arr_obj, c):
    if data_typ == string_array_split_view_type:
        ujah__nfaow = c.context.make_helper(c.builder,
            string_array_split_view_type)
        return NativeValue(ujah__nfaow._getvalue())
    return c.pyapi.to_native_value(data_typ, arr_obj)


@box(HeterogeneousSeriesType)
@box(SeriesType)
def box_series(typ, val, c):
    jcab__sohiq = c.context.insert_const_string(c.builder.module, 'pandas')
    nrxar__temx = c.pyapi.import_module_noblock(jcab__sohiq)
    eop__obcrd = bodo.hiframes.pd_series_ext.get_series_payload(c.context,
        c.builder, typ, val)
    c.context.nrt.incref(c.builder, typ.data, eop__obcrd.data)
    c.context.nrt.incref(c.builder, typ.index, eop__obcrd.index)
    c.context.nrt.incref(c.builder, typ.name_typ, eop__obcrd.name)
    arr_obj = c.pyapi.from_native_value(typ.data, eop__obcrd.data, c.
        env_manager)
    saxh__segm = c.pyapi.from_native_value(typ.index, eop__obcrd.index, c.
        env_manager)
    dwoeq__igs = c.pyapi.from_native_value(typ.name_typ, eop__obcrd.name, c
        .env_manager)
    if isinstance(typ, HeterogeneousSeriesType) and isinstance(typ.data,
        bodo.NullableTupleType):
        dtype = c.pyapi.unserialize(c.pyapi.serialize_object(object))
    else:
        dtype = c.pyapi.make_none()
    res = c.pyapi.call_method(nrxar__temx, 'Series', (arr_obj, saxh__segm,
        dtype, dwoeq__igs))
    c.pyapi.decref(arr_obj)
    c.pyapi.decref(saxh__segm)
    c.pyapi.decref(dwoeq__igs)
    if isinstance(typ, HeterogeneousSeriesType) and isinstance(typ.data,
        bodo.NullableTupleType):
        c.pyapi.decref(dtype)
    _set_bodo_meta_series(res, c, typ)
    c.pyapi.decref(nrxar__temx)
    c.context.nrt.decref(c.builder, typ, val)
    return res


def type_enum_list_to_py_list_obj(pyapi, context, builder, env_manager,
    typ_list):
    vgabq__hwhp = []
    for nfloa__uimwu in typ_list:
        if isinstance(nfloa__uimwu, int) and not isinstance(nfloa__uimwu, bool
            ):
            zqlg__csk = pyapi.long_from_longlong(lir.Constant(lir.IntType(
                64), nfloa__uimwu))
        else:
            kdj__mqaoy = numba.typeof(nfloa__uimwu)
            qxsg__idekq = context.get_constant_generic(builder, kdj__mqaoy,
                nfloa__uimwu)
            zqlg__csk = pyapi.from_native_value(kdj__mqaoy, qxsg__idekq,
                env_manager)
        vgabq__hwhp.append(zqlg__csk)
    cqo__owxx = pyapi.list_pack(vgabq__hwhp)
    for val in vgabq__hwhp:
        pyapi.decref(val)
    return cqo__owxx


def _set_bodo_meta_dataframe(c, obj, typ):
    pyapi = c.pyapi
    context = c.context
    builder = c.builder
    ooy__vbc = not typ.has_runtime_cols and (not typ.is_table_format or len
        (typ.columns) < TABLE_FORMAT_THRESHOLD)
    zygce__yrkc = 2 if ooy__vbc else 1
    gsqan__devx = pyapi.dict_new(zygce__yrkc)
    yimu__tlu = pyapi.long_from_longlong(lir.Constant(lir.IntType(64), typ.
        dist.value))
    pyapi.dict_setitem_string(gsqan__devx, 'dist', yimu__tlu)
    pyapi.decref(yimu__tlu)
    if ooy__vbc:
        has__zhl = _dtype_to_type_enum_list(typ.index)
        if has__zhl != None:
            jaynh__shbek = type_enum_list_to_py_list_obj(pyapi, context,
                builder, c.env_manager, has__zhl)
        else:
            jaynh__shbek = pyapi.make_none()
        rqzli__sha = []
        for dtype in typ.data:
            typ_list = _dtype_to_type_enum_list(dtype)
            if typ_list != None:
                cqo__owxx = type_enum_list_to_py_list_obj(pyapi, context,
                    builder, c.env_manager, typ_list)
            else:
                cqo__owxx = pyapi.make_none()
            rqzli__sha.append(cqo__owxx)
        vzjz__sbhvb = pyapi.list_pack(rqzli__sha)
        clsg__vxl = pyapi.list_pack([jaynh__shbek, vzjz__sbhvb])
        for val in rqzli__sha:
            pyapi.decref(val)
        pyapi.dict_setitem_string(gsqan__devx, 'type_metadata', clsg__vxl)
    pyapi.object_setattr_string(obj, '_bodo_meta', gsqan__devx)
    pyapi.decref(gsqan__devx)


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
    gsqan__devx = pyapi.dict_new(2)
    yimu__tlu = pyapi.long_from_longlong(lir.Constant(lir.IntType(64), typ.
        dist.value))
    has__zhl = _dtype_to_type_enum_list(typ.index)
    if has__zhl != None:
        jaynh__shbek = type_enum_list_to_py_list_obj(pyapi, context,
            builder, c.env_manager, has__zhl)
    else:
        jaynh__shbek = pyapi.make_none()
    dtype = get_series_dtype_handle_null_int_and_hetrogenous(typ)
    if dtype != None:
        typ_list = _dtype_to_type_enum_list(dtype)
        if typ_list != None:
            arze__twqj = type_enum_list_to_py_list_obj(pyapi, context,
                builder, c.env_manager, typ_list)
        else:
            arze__twqj = pyapi.make_none()
    else:
        arze__twqj = pyapi.make_none()
    ksnb__gkzmo = pyapi.list_pack([jaynh__shbek, arze__twqj])
    pyapi.dict_setitem_string(gsqan__devx, 'type_metadata', ksnb__gkzmo)
    pyapi.decref(ksnb__gkzmo)
    pyapi.dict_setitem_string(gsqan__devx, 'dist', yimu__tlu)
    pyapi.object_setattr_string(obj, '_bodo_meta', gsqan__devx)
    pyapi.decref(gsqan__devx)
    pyapi.decref(yimu__tlu)


@typeof_impl.register(np.ndarray)
def _typeof_ndarray(val, c):
    try:
        dtype = numba.np.numpy_support.from_dtype(val.dtype)
    except NotImplementedError as vvh__ulkcr:
        dtype = types.pyobject
    if dtype == types.pyobject:
        return _infer_ndarray_obj_dtype(val)
    pdi__ypevv = numba.np.numpy_support.map_layout(val)
    zdied__watvy = not val.flags.writeable
    return types.Array(dtype, val.ndim, pdi__ypevv, readonly=zdied__watvy)


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
    bonz__qrw = val[i]
    if isinstance(bonz__qrw, str):
        return (bodo.dict_str_arr_type if _use_dict_str_type else
            string_array_type)
    elif isinstance(bonz__qrw, bytes):
        return binary_array_type
    elif isinstance(bonz__qrw, bool):
        return bodo.libs.bool_arr_ext.boolean_array
    elif isinstance(bonz__qrw, (int, np.int32, np.int64)):
        return bodo.libs.int_arr_ext.IntegerArrayType(numba.typeof(bonz__qrw))
    elif isinstance(bonz__qrw, (dict, Dict)) and all(isinstance(azoo__aqs,
        str) for azoo__aqs in bonz__qrw.keys()):
        opi__oyx = tuple(bonz__qrw.keys())
        qshs__ocpvs = tuple(_get_struct_value_arr_type(v) for v in
            bonz__qrw.values())
        return StructArrayType(qshs__ocpvs, opi__oyx)
    elif isinstance(bonz__qrw, (dict, Dict)):
        iqu__etqer = numba.typeof(_value_to_array(list(bonz__qrw.keys())))
        qrn__ybftx = numba.typeof(_value_to_array(list(bonz__qrw.values())))
        iqu__etqer = to_str_arr_if_dict_array(iqu__etqer)
        qrn__ybftx = to_str_arr_if_dict_array(qrn__ybftx)
        return MapArrayType(iqu__etqer, qrn__ybftx)
    elif isinstance(bonz__qrw, tuple):
        qshs__ocpvs = tuple(_get_struct_value_arr_type(v) for v in bonz__qrw)
        return TupleArrayType(qshs__ocpvs)
    if isinstance(bonz__qrw, (list, np.ndarray, pd.arrays.BooleanArray, pd.
        arrays.IntegerArray, pd.arrays.StringArray)):
        if isinstance(bonz__qrw, list):
            bonz__qrw = _value_to_array(bonz__qrw)
        rgrig__ijigw = numba.typeof(bonz__qrw)
        rgrig__ijigw = to_str_arr_if_dict_array(rgrig__ijigw)
        return ArrayItemArrayType(rgrig__ijigw)
    if isinstance(bonz__qrw, datetime.date):
        return datetime_date_array_type
    if isinstance(bonz__qrw, datetime.timedelta):
        return datetime_timedelta_array_type
    if isinstance(bonz__qrw, decimal.Decimal):
        return DecimalArrayType(38, 18)
    raise BodoError(f'Unsupported object array with first value: {bonz__qrw}')


def _value_to_array(val):
    assert isinstance(val, (list, dict, Dict))
    if isinstance(val, (dict, Dict)):
        val = dict(val)
        return np.array([val], np.object_)
    wulya__jhbq = val.copy()
    wulya__jhbq.append(None)
    binb__qrw = np.array(wulya__jhbq, np.object_)
    if len(val) and isinstance(val[0], float):
        binb__qrw = np.array(val, np.float64)
    return binb__qrw


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
    lpayz__bamdz = dtype_to_array_type(numba.typeof(v))
    if isinstance(v, (int, bool)):
        lpayz__bamdz = to_nullable_type(lpayz__bamdz)
    return lpayz__bamdz
