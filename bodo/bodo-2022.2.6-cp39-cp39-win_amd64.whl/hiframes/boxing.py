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
    ipxud__wfrkj = tuple(val.columns.to_list())
    aefs__odcli = get_hiframes_dtypes(val)
    if (len(val.index) == 0 and val.index.dtype == np.dtype('O') and
        hasattr(val, '_bodo_meta') and val._bodo_meta is not None and 
        'type_metadata' in val._bodo_meta and val._bodo_meta[
        'type_metadata'] is not None and len(val._bodo_meta['type_metadata'
        ][1]) == len(val.columns) and val._bodo_meta['type_metadata'][0] is not
        None):
        bmr__dla = _dtype_from_type_enum_list(val._bodo_meta[
            'type_metadata'][0])
    else:
        bmr__dla = numba.typeof(val.index)
    eayv__ueupi = Distribution(val._bodo_meta['dist']) if hasattr(val,
        '_bodo_meta') and val._bodo_meta is not None else Distribution.REP
    kag__cvdk = len(aefs__odcli) >= TABLE_FORMAT_THRESHOLD
    return DataFrameType(aefs__odcli, bmr__dla, ipxud__wfrkj, eayv__ueupi,
        is_table_format=kag__cvdk)


@typeof_impl.register(pd.Series)
def typeof_pd_series(val, c):
    from bodo.transforms.distributed_analysis import Distribution
    eayv__ueupi = Distribution(val._bodo_meta['dist']) if hasattr(val,
        '_bodo_meta') and val._bodo_meta is not None else Distribution.REP
    if (len(val.index) == 0 and val.index.dtype == np.dtype('O') and
        hasattr(val, '_bodo_meta') and val._bodo_meta is not None and 
        'type_metadata' in val._bodo_meta and val._bodo_meta[
        'type_metadata'] is not None and val._bodo_meta['type_metadata'][0]
         is not None):
        kxmx__ekgqw = _dtype_from_type_enum_list(val._bodo_meta[
            'type_metadata'][0])
    else:
        kxmx__ekgqw = numba.typeof(val.index)
    dtype = _infer_series_dtype(val)
    pjub__rwefy = dtype_to_array_type(dtype)
    if _use_dict_str_type and pjub__rwefy == string_array_type:
        pjub__rwefy = bodo.dict_str_arr_type
    return SeriesType(dtype, data=pjub__rwefy, index=kxmx__ekgqw, name_typ=
        numba.typeof(val.name), dist=eayv__ueupi)


@unbox(DataFrameType)
def unbox_dataframe(typ, val, c):
    check_runtime_cols_unsupported(typ, 'Unboxing')
    ygjmq__ppflk = c.pyapi.object_getattr_string(val, 'index')
    hjxnv__zbz = c.pyapi.to_native_value(typ.index, ygjmq__ppflk).value
    c.pyapi.decref(ygjmq__ppflk)
    if typ.is_table_format:
        pirh__wofae = cgutils.create_struct_proxy(typ.table_type)(c.context,
            c.builder)
        pirh__wofae.parent = val
        for qtgx__wxmqs, pmdcc__iyeh in typ.table_type.type_to_blk.items():
            prkt__idcic = c.context.get_constant(types.int64, len(typ.
                table_type.block_to_arr_ind[pmdcc__iyeh]))
            kzsj__mtn, qdw__xtw = ListInstance.allocate_ex(c.context, c.
                builder, types.List(qtgx__wxmqs), prkt__idcic)
            qdw__xtw.size = prkt__idcic
            setattr(pirh__wofae, f'block_{pmdcc__iyeh}', qdw__xtw.value)
        acsh__jeo = c.pyapi.call_method(val, '__len__', ())
        qyfd__eadg = c.pyapi.long_as_longlong(acsh__jeo)
        c.pyapi.decref(acsh__jeo)
        pirh__wofae.len = qyfd__eadg
        eflg__dan = c.context.make_tuple(c.builder, types.Tuple([typ.
            table_type]), [pirh__wofae._getvalue()])
    else:
        cdfm__idvis = [c.context.get_constant_null(qtgx__wxmqs) for
            qtgx__wxmqs in typ.data]
        eflg__dan = c.context.make_tuple(c.builder, types.Tuple(typ.data),
            cdfm__idvis)
    jcq__zvn = construct_dataframe(c.context, c.builder, typ, eflg__dan,
        hjxnv__zbz, val, None)
    return NativeValue(jcq__zvn)


def get_hiframes_dtypes(df):
    if (hasattr(df, '_bodo_meta') and df._bodo_meta is not None and 
        'type_metadata' in df._bodo_meta and df._bodo_meta['type_metadata']
         is not None and len(df._bodo_meta['type_metadata'][1]) == len(df.
        columns)):
        qyvlq__dtit = df._bodo_meta['type_metadata'][1]
    else:
        qyvlq__dtit = [None] * len(df.columns)
    goja__dqi = [dtype_to_array_type(_infer_series_dtype(df.iloc[:, i],
        array_metadata=qyvlq__dtit[i])) for i in range(len(df.columns))]
    goja__dqi = [(bodo.dict_str_arr_type if _use_dict_str_type and 
        qtgx__wxmqs == string_array_type else qtgx__wxmqs) for qtgx__wxmqs in
        goja__dqi]
    return tuple(goja__dqi)


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
    ecdm__bbe, typ = _dtype_from_type_enum_list_recursor(typ_enum_list)
    if len(ecdm__bbe) != 0:
        raise_bodo_error(
            f"""Unexpected Internal Error while converting typing metadata: Dtype list was not fully consumed.
 Input typ_enum_list: {typ_enum_list}.
Remainder: {ecdm__bbe}. Please file the error here: https://github.com/Bodo-inc/Feedback"""
            )
    return typ


def _dtype_from_type_enum_list_recursor(typ_enum_list):
    if len(typ_enum_list) == 0:
        raise_bodo_error('Unable to infer dtype from empty typ_enum_list')
    elif typ_enum_list[0] in _one_to_one_enum_to_type_map:
        return typ_enum_list[1:], _one_to_one_enum_to_type_map[typ_enum_list[0]
            ]
    elif typ_enum_list[0] == SeriesDtypeEnum.IntegerArray.value:
        hpdo__vamj, typ = _dtype_from_type_enum_list_recursor(typ_enum_list[1:]
            )
        return hpdo__vamj, IntegerArrayType(typ)
    elif typ_enum_list[0] == SeriesDtypeEnum.ARRAY.value:
        hpdo__vamj, typ = _dtype_from_type_enum_list_recursor(typ_enum_list[1:]
            )
        return hpdo__vamj, dtype_to_array_type(typ)
    elif typ_enum_list[0] == SeriesDtypeEnum.Decimal.value:
        myfj__bou = typ_enum_list[1]
        vmiob__mqmfb = typ_enum_list[2]
        return typ_enum_list[3:], Decimal128Type(myfj__bou, vmiob__mqmfb)
    elif typ_enum_list[0] == SeriesDtypeEnum.STRUCT.value:
        ftqx__ebv = typ_enum_list[1]
        pskbi__bstoo = tuple(typ_enum_list[2:2 + ftqx__ebv])
        bhk__dwd = typ_enum_list[2 + ftqx__ebv:]
        aym__uwbhk = []
        for i in range(ftqx__ebv):
            bhk__dwd, ybqba__thk = _dtype_from_type_enum_list_recursor(bhk__dwd
                )
            aym__uwbhk.append(ybqba__thk)
        return bhk__dwd, StructType(tuple(aym__uwbhk), pskbi__bstoo)
    elif typ_enum_list[0] == SeriesDtypeEnum.Literal.value:
        if len(typ_enum_list) == 1:
            raise_bodo_error(
                f"Unexpected Internal Error while converting typing metadata: Encountered 'Literal' internal enum value with no value following it. Please file the error here: https://github.com/Bodo-inc/Feedback"
                )
        icuv__ikw = typ_enum_list[1]
        bhk__dwd = typ_enum_list[2:]
        return bhk__dwd, icuv__ikw
    elif typ_enum_list[0] == SeriesDtypeEnum.LiteralType.value:
        if len(typ_enum_list) == 1:
            raise_bodo_error(
                f"Unexpected Internal Error while converting typing metadata: Encountered 'LiteralType' internal enum value with no value following it. Please file the error here: https://github.com/Bodo-inc/Feedback"
                )
        icuv__ikw = typ_enum_list[1]
        bhk__dwd = typ_enum_list[2:]
        return bhk__dwd, numba.types.literal(icuv__ikw)
    elif typ_enum_list[0] == SeriesDtypeEnum.CategoricalType.value:
        bhk__dwd, qfy__imqly = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        bhk__dwd, efqa__whqrk = _dtype_from_type_enum_list_recursor(bhk__dwd)
        bhk__dwd, jbv__ccl = _dtype_from_type_enum_list_recursor(bhk__dwd)
        bhk__dwd, ykr__znot = _dtype_from_type_enum_list_recursor(bhk__dwd)
        bhk__dwd, taoqx__jvw = _dtype_from_type_enum_list_recursor(bhk__dwd)
        return bhk__dwd, PDCategoricalDtype(qfy__imqly, efqa__whqrk,
            jbv__ccl, ykr__znot, taoqx__jvw)
    elif typ_enum_list[0] == SeriesDtypeEnum.DatetimeIndexType.value:
        bhk__dwd, tzl__emo = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        return bhk__dwd, DatetimeIndexType(tzl__emo)
    elif typ_enum_list[0] == SeriesDtypeEnum.NumericIndexType.value:
        bhk__dwd, dtype = _dtype_from_type_enum_list_recursor(typ_enum_list[1:]
            )
        bhk__dwd, tzl__emo = _dtype_from_type_enum_list_recursor(bhk__dwd)
        bhk__dwd, ykr__znot = _dtype_from_type_enum_list_recursor(bhk__dwd)
        return bhk__dwd, NumericIndexType(dtype, tzl__emo, ykr__znot)
    elif typ_enum_list[0] == SeriesDtypeEnum.PeriodIndexType.value:
        bhk__dwd, fff__lxznm = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        bhk__dwd, tzl__emo = _dtype_from_type_enum_list_recursor(bhk__dwd)
        return bhk__dwd, PeriodIndexType(fff__lxznm, tzl__emo)
    elif typ_enum_list[0] == SeriesDtypeEnum.CategoricalIndexType.value:
        bhk__dwd, ykr__znot = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        bhk__dwd, tzl__emo = _dtype_from_type_enum_list_recursor(bhk__dwd)
        return bhk__dwd, CategoricalIndexType(ykr__znot, tzl__emo)
    elif typ_enum_list[0] == SeriesDtypeEnum.RangeIndexType.value:
        bhk__dwd, tzl__emo = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        return bhk__dwd, RangeIndexType(tzl__emo)
    elif typ_enum_list[0] == SeriesDtypeEnum.StringIndexType.value:
        bhk__dwd, tzl__emo = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        return bhk__dwd, StringIndexType(tzl__emo)
    elif typ_enum_list[0] == SeriesDtypeEnum.BinaryIndexType.value:
        bhk__dwd, tzl__emo = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        return bhk__dwd, BinaryIndexType(tzl__emo)
    elif typ_enum_list[0] == SeriesDtypeEnum.TimedeltaIndexType.value:
        bhk__dwd, tzl__emo = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        return bhk__dwd, TimedeltaIndexType(tzl__emo)
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
        rak__eur = get_overload_const_int(typ)
        if numba.types.maybe_literal(rak__eur) == typ:
            return [SeriesDtypeEnum.LiteralType.value, rak__eur]
    elif is_overload_constant_str(typ):
        rak__eur = get_overload_const_str(typ)
        if numba.types.maybe_literal(rak__eur) == typ:
            return [SeriesDtypeEnum.LiteralType.value, rak__eur]
    elif is_overload_constant_bool(typ):
        rak__eur = get_overload_const_bool(typ)
        if numba.types.maybe_literal(rak__eur) == typ:
            return [SeriesDtypeEnum.LiteralType.value, rak__eur]
    elif isinstance(typ, IntegerArrayType):
        return [SeriesDtypeEnum.IntegerArray.value
            ] + _dtype_to_type_enum_list_recursor(typ.dtype)
    elif bodo.utils.utils.is_array_typ(typ, False):
        return [SeriesDtypeEnum.ARRAY.value
            ] + _dtype_to_type_enum_list_recursor(typ.dtype)
    elif isinstance(typ, StructType):
        dnv__ggzt = [SeriesDtypeEnum.STRUCT.value, len(typ.names)]
        for ehu__uzwvt in typ.names:
            dnv__ggzt.append(ehu__uzwvt)
        for huak__jcrz in typ.data:
            dnv__ggzt += _dtype_to_type_enum_list_recursor(huak__jcrz)
        return dnv__ggzt
    elif isinstance(typ, bodo.libs.decimal_arr_ext.Decimal128Type):
        return [SeriesDtypeEnum.Decimal.value, typ.precision, typ.scale]
    elif isinstance(typ, PDCategoricalDtype):
        xekny__fcmxk = _dtype_to_type_enum_list_recursor(typ.categories)
        yzxbd__snzq = _dtype_to_type_enum_list_recursor(typ.elem_type)
        eapyk__mxmuu = _dtype_to_type_enum_list_recursor(typ.ordered)
        uvnh__woel = _dtype_to_type_enum_list_recursor(typ.data)
        lwhz__fkw = _dtype_to_type_enum_list_recursor(typ.int_type)
        return [SeriesDtypeEnum.CategoricalType.value
            ] + xekny__fcmxk + yzxbd__snzq + eapyk__mxmuu + uvnh__woel + lwhz__fkw
    elif isinstance(typ, DatetimeIndexType):
        return [SeriesDtypeEnum.DatetimeIndexType.value
            ] + _dtype_to_type_enum_list_recursor(typ.name_typ)
    elif isinstance(typ, NumericIndexType):
        if upcast_numeric_index:
            if isinstance(typ.dtype, types.Float):
                bvu__yedp = types.float64
                bnxe__sjj = types.Array(bvu__yedp, 1, 'C')
            elif typ.dtype in {types.int8, types.int16, types.int32, types.
                int64}:
                bvu__yedp = types.int64
                bnxe__sjj = types.Array(bvu__yedp, 1, 'C')
            elif typ.dtype in {types.uint8, types.uint16, types.uint32,
                types.uint64}:
                bvu__yedp = types.uint64
                bnxe__sjj = types.Array(bvu__yedp, 1, 'C')
            elif typ.dtype == types.bool_:
                bvu__yedp = typ.dtype
                bnxe__sjj = typ.data
            else:
                raise GuardException('Unable to convert type')
            return [SeriesDtypeEnum.NumericIndexType.value
                ] + _dtype_to_type_enum_list_recursor(bvu__yedp
                ) + _dtype_to_type_enum_list_recursor(typ.name_typ
                ) + _dtype_to_type_enum_list_recursor(bnxe__sjj)
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
                ewr__lfd = S._bodo_meta['type_metadata'][1]
                return _dtype_from_type_enum_list(ewr__lfd)
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
        oaudg__exs = S.dtype.unit
        if oaudg__exs != 'ns':
            raise BodoError("Timezone-aware datetime data requires 'ns' units")
        fkm__ezsqc = bodo.libs.pd_datetime_arr_ext.get_pytz_type_info(S.
            dtype.tz)
        return PandasDatetimeTZDtype(fkm__ezsqc)
    try:
        return numpy_support.from_dtype(S.dtype)
    except:
        raise BodoError(
            f'data type {S.dtype} for column {S.name} not supported yet')


def _get_use_df_parent_obj_flag(builder, context, pyapi, parent_obj, n_cols):
    if n_cols is None:
        return context.get_constant(types.bool_, False)
    thaen__pmxli = cgutils.is_not_null(builder, parent_obj)
    komzi__xprw = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with builder.if_then(thaen__pmxli):
        wua__jzq = pyapi.object_getattr_string(parent_obj, 'columns')
        acsh__jeo = pyapi.call_method(wua__jzq, '__len__', ())
        builder.store(pyapi.long_as_longlong(acsh__jeo), komzi__xprw)
        pyapi.decref(acsh__jeo)
        pyapi.decref(wua__jzq)
    use_parent_obj = builder.and_(thaen__pmxli, builder.icmp_unsigned('==',
        builder.load(komzi__xprw), context.get_constant(types.int64, n_cols)))
    return use_parent_obj


def _get_df_columns_obj(c, builder, context, pyapi, df_typ, dataframe_payload):
    if df_typ.has_runtime_cols:
        eed__qbzyg = df_typ.runtime_colname_typ
        context.nrt.incref(builder, eed__qbzyg, dataframe_payload.columns)
        return pyapi.from_native_value(eed__qbzyg, dataframe_payload.
            columns, c.env_manager)
    if all(isinstance(c, int) for c in df_typ.columns):
        gmu__ovlf = np.array(df_typ.columns, 'int64')
    elif all(isinstance(c, str) for c in df_typ.columns):
        gmu__ovlf = pd.array(df_typ.columns, 'string')
    else:
        gmu__ovlf = df_typ.columns
    jkh__omgsr = numba.typeof(gmu__ovlf)
    ozkv__sbtxf = context.get_constant_generic(builder, jkh__omgsr, gmu__ovlf)
    tenu__bnmno = pyapi.from_native_value(jkh__omgsr, ozkv__sbtxf, c.
        env_manager)
    return tenu__bnmno


def _create_initial_df_object(builder, context, pyapi, c, df_typ, obj,
    dataframe_payload, res, use_parent_obj):
    with c.builder.if_else(use_parent_obj) as (gpu__yszor, ktjug__xnvbo):
        with gpu__yszor:
            pyapi.incref(obj)
            gbq__fll = context.insert_const_string(c.builder.module, 'numpy')
            evly__qnul = pyapi.import_module_noblock(gbq__fll)
            if df_typ.has_runtime_cols:
                moiub__ufhl = 0
            else:
                moiub__ufhl = len(df_typ.columns)
            ibt__haxz = pyapi.long_from_longlong(lir.Constant(lir.IntType(
                64), moiub__ufhl))
            edj__ubpvk = pyapi.call_method(evly__qnul, 'arange', (ibt__haxz,))
            pyapi.object_setattr_string(obj, 'columns', edj__ubpvk)
            pyapi.decref(evly__qnul)
            pyapi.decref(edj__ubpvk)
            pyapi.decref(ibt__haxz)
        with ktjug__xnvbo:
            context.nrt.incref(builder, df_typ.index, dataframe_payload.index)
            bjnbg__ybr = c.pyapi.from_native_value(df_typ.index,
                dataframe_payload.index, c.env_manager)
            gbq__fll = context.insert_const_string(c.builder.module, 'pandas')
            evly__qnul = pyapi.import_module_noblock(gbq__fll)
            df_obj = pyapi.call_method(evly__qnul, 'DataFrame', (pyapi.
                borrow_none(), bjnbg__ybr))
            pyapi.decref(evly__qnul)
            pyapi.decref(bjnbg__ybr)
            builder.store(df_obj, res)


@box(DataFrameType)
def box_dataframe(typ, val, c):
    from bodo.hiframes.table import box_table
    context = c.context
    builder = c.builder
    pyapi = c.pyapi
    dataframe_payload = bodo.hiframes.pd_dataframe_ext.get_dataframe_payload(c
        .context, c.builder, typ, val)
    yuf__jpyv = cgutils.create_struct_proxy(typ)(context, builder, value=val)
    n_cols = len(typ.columns) if not typ.has_runtime_cols else None
    obj = yuf__jpyv.parent
    res = cgutils.alloca_once_value(builder, obj)
    use_parent_obj = _get_use_df_parent_obj_flag(builder, context, pyapi,
        obj, n_cols)
    _create_initial_df_object(builder, context, pyapi, c, typ, obj,
        dataframe_payload, res, use_parent_obj)
    if typ.is_table_format:
        qixm__lqip = typ.table_type
        pirh__wofae = builder.extract_value(dataframe_payload.data, 0)
        context.nrt.incref(builder, qixm__lqip, pirh__wofae)
        kar__hli = box_table(qixm__lqip, pirh__wofae, c, builder.not_(
            use_parent_obj))
        with builder.if_else(use_parent_obj) as (xpnz__yrrfv, zjwb__cpbub):
            with xpnz__yrrfv:
                jtuj__xys = pyapi.object_getattr_string(kar__hli, 'arrays')
                zark__adoi = c.pyapi.make_none()
                if n_cols is None:
                    acsh__jeo = pyapi.call_method(jtuj__xys, '__len__', ())
                    prkt__idcic = pyapi.long_as_longlong(acsh__jeo)
                    pyapi.decref(acsh__jeo)
                else:
                    prkt__idcic = context.get_constant(types.int64, n_cols)
                with cgutils.for_range(builder, prkt__idcic) as vjzau__uaq:
                    i = vjzau__uaq.index
                    dtpt__mgi = pyapi.list_getitem(jtuj__xys, i)
                    bwqh__swt = c.builder.icmp_unsigned('!=', dtpt__mgi,
                        zark__adoi)
                    with builder.if_then(bwqh__swt):
                        rtlxn__qtlk = pyapi.long_from_longlong(i)
                        df_obj = builder.load(res)
                        pyapi.object_setitem(df_obj, rtlxn__qtlk, dtpt__mgi)
                        pyapi.decref(rtlxn__qtlk)
                pyapi.decref(jtuj__xys)
                pyapi.decref(zark__adoi)
            with zjwb__cpbub:
                df_obj = builder.load(res)
                bjnbg__ybr = pyapi.object_getattr_string(df_obj, 'index')
                ummw__dvj = c.pyapi.call_method(kar__hli, 'to_pandas', (
                    bjnbg__ybr,))
                builder.store(ummw__dvj, res)
                pyapi.decref(df_obj)
                pyapi.decref(bjnbg__ybr)
        pyapi.decref(kar__hli)
    else:
        sfc__fczgf = [builder.extract_value(dataframe_payload.data, i) for
            i in range(n_cols)]
        jxes__lmcx = typ.data
        for i, ktkj__eqp, pjub__rwefy in zip(range(n_cols), sfc__fczgf,
            jxes__lmcx):
            otq__clzf = cgutils.alloca_once_value(builder, ktkj__eqp)
            rivvh__odim = cgutils.alloca_once_value(builder, context.
                get_constant_null(pjub__rwefy))
            bwqh__swt = builder.not_(is_ll_eq(builder, otq__clzf, rivvh__odim))
            otr__pig = builder.or_(builder.not_(use_parent_obj), builder.
                and_(use_parent_obj, bwqh__swt))
            with builder.if_then(otr__pig):
                rtlxn__qtlk = pyapi.long_from_longlong(context.get_constant
                    (types.int64, i))
                context.nrt.incref(builder, pjub__rwefy, ktkj__eqp)
                arr_obj = pyapi.from_native_value(pjub__rwefy, ktkj__eqp, c
                    .env_manager)
                df_obj = builder.load(res)
                pyapi.object_setitem(df_obj, rtlxn__qtlk, arr_obj)
                pyapi.decref(arr_obj)
                pyapi.decref(rtlxn__qtlk)
    df_obj = builder.load(res)
    tenu__bnmno = _get_df_columns_obj(c, builder, context, pyapi, typ,
        dataframe_payload)
    pyapi.object_setattr_string(df_obj, 'columns', tenu__bnmno)
    pyapi.decref(tenu__bnmno)
    _set_bodo_meta_dataframe(c, df_obj, typ)
    c.context.nrt.decref(c.builder, typ, val)
    return df_obj


def get_df_obj_column_codegen(context, builder, pyapi, df_obj, col_ind,
    data_typ):
    zark__adoi = pyapi.borrow_none()
    elk__haf = pyapi.unserialize(pyapi.serialize_object(slice))
    msdxo__rcohw = pyapi.call_function_objargs(elk__haf, [zark__adoi])
    hamh__nuhr = pyapi.long_from_longlong(col_ind)
    nqlkl__ixkec = pyapi.tuple_pack([msdxo__rcohw, hamh__nuhr])
    vcz__pfwu = pyapi.object_getattr_string(df_obj, 'iloc')
    ifjw__namfx = pyapi.object_getitem(vcz__pfwu, nqlkl__ixkec)
    if isinstance(data_typ, bodo.DatetimeArrayType):
        tgp__btyjz = pyapi.object_getattr_string(ifjw__namfx, 'array')
    else:
        tgp__btyjz = pyapi.object_getattr_string(ifjw__namfx, 'values')
    if isinstance(data_typ, types.Array):
        imvei__vwky = context.insert_const_string(builder.module, 'numpy')
        otu__umbws = pyapi.import_module_noblock(imvei__vwky)
        arr_obj = pyapi.call_method(otu__umbws, 'ascontiguousarray', (
            tgp__btyjz,))
        pyapi.decref(tgp__btyjz)
        pyapi.decref(otu__umbws)
    else:
        arr_obj = tgp__btyjz
    pyapi.decref(elk__haf)
    pyapi.decref(msdxo__rcohw)
    pyapi.decref(hamh__nuhr)
    pyapi.decref(nqlkl__ixkec)
    pyapi.decref(vcz__pfwu)
    pyapi.decref(ifjw__namfx)
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
        yuf__jpyv = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        arr_obj = get_df_obj_column_codegen(context, builder, pyapi,
            yuf__jpyv.parent, args[1], data_typ)
        snmuu__vocte = _unbox_series_data(data_typ.dtype, data_typ, arr_obj, c)
        c.pyapi.decref(arr_obj)
        dataframe_payload = (bodo.hiframes.pd_dataframe_ext.
            get_dataframe_payload(c.context, c.builder, df_typ, args[0]))
        if df_typ.is_table_format:
            pirh__wofae = cgutils.create_struct_proxy(df_typ.table_type)(c.
                context, c.builder, builder.extract_value(dataframe_payload
                .data, 0))
            pmdcc__iyeh = df_typ.table_type.type_to_blk[data_typ]
            zsdiu__kpfdn = getattr(pirh__wofae, f'block_{pmdcc__iyeh}')
            patpx__ebu = ListInstance(c.context, c.builder, types.List(
                data_typ), zsdiu__kpfdn)
            nuke__fbelw = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[col_ind])
            patpx__ebu.inititem(nuke__fbelw, snmuu__vocte.value, incref=False)
        else:
            dataframe_payload.data = builder.insert_value(dataframe_payload
                .data, snmuu__vocte.value, col_ind)
        xyxhu__hnmi = DataFramePayloadType(df_typ)
        wjq__jmhrs = context.nrt.meminfo_data(builder, yuf__jpyv.meminfo)
        pqg__pkq = context.get_value_type(xyxhu__hnmi).as_pointer()
        wjq__jmhrs = builder.bitcast(wjq__jmhrs, pqg__pkq)
        builder.store(dataframe_payload._getvalue(), wjq__jmhrs)
    return signature(types.none, df, i), codegen


@numba.njit
def unbox_col_if_needed(df, i):
    if bodo.hiframes.pd_dataframe_ext.has_parent(df
        ) and bodo.hiframes.pd_dataframe_ext._column_needs_unboxing(df, i):
        bodo.hiframes.boxing.unbox_dataframe_column(df, i)


@unbox(SeriesType)
def unbox_series(typ, val, c):
    if isinstance(typ.data, DatetimeArrayType):
        tgp__btyjz = c.pyapi.object_getattr_string(val, 'array')
    else:
        tgp__btyjz = c.pyapi.object_getattr_string(val, 'values')
    if isinstance(typ.data, types.Array):
        imvei__vwky = c.context.insert_const_string(c.builder.module, 'numpy')
        otu__umbws = c.pyapi.import_module_noblock(imvei__vwky)
        arr_obj = c.pyapi.call_method(otu__umbws, 'ascontiguousarray', (
            tgp__btyjz,))
        c.pyapi.decref(tgp__btyjz)
        c.pyapi.decref(otu__umbws)
    else:
        arr_obj = tgp__btyjz
    jmtg__xrw = _unbox_series_data(typ.dtype, typ.data, arr_obj, c).value
    bjnbg__ybr = c.pyapi.object_getattr_string(val, 'index')
    hjxnv__zbz = c.pyapi.to_native_value(typ.index, bjnbg__ybr).value
    uiu__qmlia = c.pyapi.object_getattr_string(val, 'name')
    cpz__qflpi = c.pyapi.to_native_value(typ.name_typ, uiu__qmlia).value
    qvgdw__stelj = bodo.hiframes.pd_series_ext.construct_series(c.context,
        c.builder, typ, jmtg__xrw, hjxnv__zbz, cpz__qflpi)
    c.pyapi.decref(arr_obj)
    c.pyapi.decref(bjnbg__ybr)
    c.pyapi.decref(uiu__qmlia)
    return NativeValue(qvgdw__stelj)


def _unbox_series_data(dtype, data_typ, arr_obj, c):
    if data_typ == string_array_split_view_type:
        opsy__nhu = c.context.make_helper(c.builder,
            string_array_split_view_type)
        return NativeValue(opsy__nhu._getvalue())
    return c.pyapi.to_native_value(data_typ, arr_obj)


@box(HeterogeneousSeriesType)
@box(SeriesType)
def box_series(typ, val, c):
    gbq__fll = c.context.insert_const_string(c.builder.module, 'pandas')
    pld__yqzul = c.pyapi.import_module_noblock(gbq__fll)
    ffjho__twzq = bodo.hiframes.pd_series_ext.get_series_payload(c.context,
        c.builder, typ, val)
    c.context.nrt.incref(c.builder, typ.data, ffjho__twzq.data)
    c.context.nrt.incref(c.builder, typ.index, ffjho__twzq.index)
    c.context.nrt.incref(c.builder, typ.name_typ, ffjho__twzq.name)
    arr_obj = c.pyapi.from_native_value(typ.data, ffjho__twzq.data, c.
        env_manager)
    bjnbg__ybr = c.pyapi.from_native_value(typ.index, ffjho__twzq.index, c.
        env_manager)
    uiu__qmlia = c.pyapi.from_native_value(typ.name_typ, ffjho__twzq.name,
        c.env_manager)
    if isinstance(typ, HeterogeneousSeriesType) and isinstance(typ.data,
        bodo.NullableTupleType):
        dtype = c.pyapi.unserialize(c.pyapi.serialize_object(object))
    else:
        dtype = c.pyapi.make_none()
    res = c.pyapi.call_method(pld__yqzul, 'Series', (arr_obj, bjnbg__ybr,
        dtype, uiu__qmlia))
    c.pyapi.decref(arr_obj)
    c.pyapi.decref(bjnbg__ybr)
    c.pyapi.decref(uiu__qmlia)
    if isinstance(typ, HeterogeneousSeriesType) and isinstance(typ.data,
        bodo.NullableTupleType):
        c.pyapi.decref(dtype)
    _set_bodo_meta_series(res, c, typ)
    c.pyapi.decref(pld__yqzul)
    c.context.nrt.decref(c.builder, typ, val)
    return res


def type_enum_list_to_py_list_obj(pyapi, context, builder, env_manager,
    typ_list):
    wwve__xujo = []
    for pvkwz__lqbg in typ_list:
        if isinstance(pvkwz__lqbg, int) and not isinstance(pvkwz__lqbg, bool):
            vawyb__sczig = pyapi.long_from_longlong(lir.Constant(lir.
                IntType(64), pvkwz__lqbg))
        else:
            lvpo__rfb = numba.typeof(pvkwz__lqbg)
            uybg__xgapc = context.get_constant_generic(builder, lvpo__rfb,
                pvkwz__lqbg)
            vawyb__sczig = pyapi.from_native_value(lvpo__rfb, uybg__xgapc,
                env_manager)
        wwve__xujo.append(vawyb__sczig)
    geqcf__akb = pyapi.list_pack(wwve__xujo)
    for val in wwve__xujo:
        pyapi.decref(val)
    return geqcf__akb


def _set_bodo_meta_dataframe(c, obj, typ):
    pyapi = c.pyapi
    context = c.context
    builder = c.builder
    vvj__uuik = not typ.has_runtime_cols and (not typ.is_table_format or 
        len(typ.columns) < TABLE_FORMAT_THRESHOLD)
    jvkc__dtj = 2 if vvj__uuik else 1
    kwaq__myniu = pyapi.dict_new(jvkc__dtj)
    fbyj__bov = pyapi.long_from_longlong(lir.Constant(lir.IntType(64), typ.
        dist.value))
    pyapi.dict_setitem_string(kwaq__myniu, 'dist', fbyj__bov)
    pyapi.decref(fbyj__bov)
    if vvj__uuik:
        cud__jev = _dtype_to_type_enum_list(typ.index)
        if cud__jev != None:
            lcces__tsa = type_enum_list_to_py_list_obj(pyapi, context,
                builder, c.env_manager, cud__jev)
        else:
            lcces__tsa = pyapi.make_none()
        znnd__bflm = []
        for dtype in typ.data:
            typ_list = _dtype_to_type_enum_list(dtype)
            if typ_list != None:
                geqcf__akb = type_enum_list_to_py_list_obj(pyapi, context,
                    builder, c.env_manager, typ_list)
            else:
                geqcf__akb = pyapi.make_none()
            znnd__bflm.append(geqcf__akb)
        hifns__xvqoj = pyapi.list_pack(znnd__bflm)
        zqlor__app = pyapi.list_pack([lcces__tsa, hifns__xvqoj])
        for val in znnd__bflm:
            pyapi.decref(val)
        pyapi.dict_setitem_string(kwaq__myniu, 'type_metadata', zqlor__app)
    pyapi.object_setattr_string(obj, '_bodo_meta', kwaq__myniu)
    pyapi.decref(kwaq__myniu)


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
    kwaq__myniu = pyapi.dict_new(2)
    fbyj__bov = pyapi.long_from_longlong(lir.Constant(lir.IntType(64), typ.
        dist.value))
    cud__jev = _dtype_to_type_enum_list(typ.index)
    if cud__jev != None:
        lcces__tsa = type_enum_list_to_py_list_obj(pyapi, context, builder,
            c.env_manager, cud__jev)
    else:
        lcces__tsa = pyapi.make_none()
    dtype = get_series_dtype_handle_null_int_and_hetrogenous(typ)
    if dtype != None:
        typ_list = _dtype_to_type_enum_list(dtype)
        if typ_list != None:
            zcq__mrv = type_enum_list_to_py_list_obj(pyapi, context,
                builder, c.env_manager, typ_list)
        else:
            zcq__mrv = pyapi.make_none()
    else:
        zcq__mrv = pyapi.make_none()
    cmdth__aeeq = pyapi.list_pack([lcces__tsa, zcq__mrv])
    pyapi.dict_setitem_string(kwaq__myniu, 'type_metadata', cmdth__aeeq)
    pyapi.decref(cmdth__aeeq)
    pyapi.dict_setitem_string(kwaq__myniu, 'dist', fbyj__bov)
    pyapi.object_setattr_string(obj, '_bodo_meta', kwaq__myniu)
    pyapi.decref(kwaq__myniu)
    pyapi.decref(fbyj__bov)


@typeof_impl.register(np.ndarray)
def _typeof_ndarray(val, c):
    try:
        dtype = numba.np.numpy_support.from_dtype(val.dtype)
    except NotImplementedError as mqno__zkfy:
        dtype = types.pyobject
    if dtype == types.pyobject:
        return _infer_ndarray_obj_dtype(val)
    pxwrn__kzx = numba.np.numpy_support.map_layout(val)
    vpgj__snkmp = not val.flags.writeable
    return types.Array(dtype, val.ndim, pxwrn__kzx, readonly=vpgj__snkmp)


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
    fam__egm = val[i]
    if isinstance(fam__egm, str):
        return (bodo.dict_str_arr_type if _use_dict_str_type else
            string_array_type)
    elif isinstance(fam__egm, bytes):
        return binary_array_type
    elif isinstance(fam__egm, bool):
        return bodo.libs.bool_arr_ext.boolean_array
    elif isinstance(fam__egm, (int, np.int32, np.int64)):
        return bodo.libs.int_arr_ext.IntegerArrayType(numba.typeof(fam__egm))
    elif isinstance(fam__egm, (dict, Dict)) and all(isinstance(yvmmq__airys,
        str) for yvmmq__airys in fam__egm.keys()):
        pskbi__bstoo = tuple(fam__egm.keys())
        bogzy__jxfra = tuple(_get_struct_value_arr_type(v) for v in
            fam__egm.values())
        return StructArrayType(bogzy__jxfra, pskbi__bstoo)
    elif isinstance(fam__egm, (dict, Dict)):
        fba__vggpf = numba.typeof(_value_to_array(list(fam__egm.keys())))
        nizrh__yykf = numba.typeof(_value_to_array(list(fam__egm.values())))
        fba__vggpf = to_str_arr_if_dict_array(fba__vggpf)
        nizrh__yykf = to_str_arr_if_dict_array(nizrh__yykf)
        return MapArrayType(fba__vggpf, nizrh__yykf)
    elif isinstance(fam__egm, tuple):
        bogzy__jxfra = tuple(_get_struct_value_arr_type(v) for v in fam__egm)
        return TupleArrayType(bogzy__jxfra)
    if isinstance(fam__egm, (list, np.ndarray, pd.arrays.BooleanArray, pd.
        arrays.IntegerArray, pd.arrays.StringArray)):
        if isinstance(fam__egm, list):
            fam__egm = _value_to_array(fam__egm)
        fhtlb__tepe = numba.typeof(fam__egm)
        fhtlb__tepe = to_str_arr_if_dict_array(fhtlb__tepe)
        return ArrayItemArrayType(fhtlb__tepe)
    if isinstance(fam__egm, datetime.date):
        return datetime_date_array_type
    if isinstance(fam__egm, datetime.timedelta):
        return datetime_timedelta_array_type
    if isinstance(fam__egm, decimal.Decimal):
        return DecimalArrayType(38, 18)
    raise BodoError(f'Unsupported object array with first value: {fam__egm}')


def _value_to_array(val):
    assert isinstance(val, (list, dict, Dict))
    if isinstance(val, (dict, Dict)):
        val = dict(val)
        return np.array([val], np.object_)
    kqiae__qvz = val.copy()
    kqiae__qvz.append(None)
    ktkj__eqp = np.array(kqiae__qvz, np.object_)
    if len(val) and isinstance(val[0], float):
        ktkj__eqp = np.array(val, np.float64)
    return ktkj__eqp


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
    pjub__rwefy = dtype_to_array_type(numba.typeof(v))
    if isinstance(v, (int, bool)):
        pjub__rwefy = to_nullable_type(pjub__rwefy)
    return pjub__rwefy
