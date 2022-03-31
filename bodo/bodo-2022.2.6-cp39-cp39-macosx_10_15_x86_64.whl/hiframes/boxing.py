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
    wku__lvvf = tuple(val.columns.to_list())
    gzyo__zki = get_hiframes_dtypes(val)
    if (len(val.index) == 0 and val.index.dtype == np.dtype('O') and
        hasattr(val, '_bodo_meta') and val._bodo_meta is not None and 
        'type_metadata' in val._bodo_meta and val._bodo_meta[
        'type_metadata'] is not None and len(val._bodo_meta['type_metadata'
        ][1]) == len(val.columns) and val._bodo_meta['type_metadata'][0] is not
        None):
        vsdy__liu = _dtype_from_type_enum_list(val._bodo_meta[
            'type_metadata'][0])
    else:
        vsdy__liu = numba.typeof(val.index)
    tejpl__zvf = Distribution(val._bodo_meta['dist']) if hasattr(val,
        '_bodo_meta') and val._bodo_meta is not None else Distribution.REP
    ypgp__erx = len(gzyo__zki) >= TABLE_FORMAT_THRESHOLD
    return DataFrameType(gzyo__zki, vsdy__liu, wku__lvvf, tejpl__zvf,
        is_table_format=ypgp__erx)


@typeof_impl.register(pd.Series)
def typeof_pd_series(val, c):
    from bodo.transforms.distributed_analysis import Distribution
    tejpl__zvf = Distribution(val._bodo_meta['dist']) if hasattr(val,
        '_bodo_meta') and val._bodo_meta is not None else Distribution.REP
    if (len(val.index) == 0 and val.index.dtype == np.dtype('O') and
        hasattr(val, '_bodo_meta') and val._bodo_meta is not None and 
        'type_metadata' in val._bodo_meta and val._bodo_meta[
        'type_metadata'] is not None and val._bodo_meta['type_metadata'][0]
         is not None):
        hgd__xoy = _dtype_from_type_enum_list(val._bodo_meta[
            'type_metadata'][0])
    else:
        hgd__xoy = numba.typeof(val.index)
    dtype = _infer_series_dtype(val)
    clg__rbdi = dtype_to_array_type(dtype)
    if _use_dict_str_type and clg__rbdi == string_array_type:
        clg__rbdi = bodo.dict_str_arr_type
    return SeriesType(dtype, data=clg__rbdi, index=hgd__xoy, name_typ=numba
        .typeof(val.name), dist=tejpl__zvf)


@unbox(DataFrameType)
def unbox_dataframe(typ, val, c):
    check_runtime_cols_unsupported(typ, 'Unboxing')
    mngez__egdz = c.pyapi.object_getattr_string(val, 'index')
    rsj__kdxuy = c.pyapi.to_native_value(typ.index, mngez__egdz).value
    c.pyapi.decref(mngez__egdz)
    if typ.is_table_format:
        daih__xmc = cgutils.create_struct_proxy(typ.table_type)(c.context,
            c.builder)
        daih__xmc.parent = val
        for dyuw__oxb, kntja__yan in typ.table_type.type_to_blk.items():
            ufdt__nmwu = c.context.get_constant(types.int64, len(typ.
                table_type.block_to_arr_ind[kntja__yan]))
            nko__xwwsr, eexd__imjx = ListInstance.allocate_ex(c.context, c.
                builder, types.List(dyuw__oxb), ufdt__nmwu)
            eexd__imjx.size = ufdt__nmwu
            setattr(daih__xmc, f'block_{kntja__yan}', eexd__imjx.value)
        swsq__fmbc = c.pyapi.call_method(val, '__len__', ())
        jlvty__hjpkd = c.pyapi.long_as_longlong(swsq__fmbc)
        c.pyapi.decref(swsq__fmbc)
        daih__xmc.len = jlvty__hjpkd
        diqz__yxrs = c.context.make_tuple(c.builder, types.Tuple([typ.
            table_type]), [daih__xmc._getvalue()])
    else:
        bmk__jithn = [c.context.get_constant_null(dyuw__oxb) for dyuw__oxb in
            typ.data]
        diqz__yxrs = c.context.make_tuple(c.builder, types.Tuple(typ.data),
            bmk__jithn)
    zqy__bnvfh = construct_dataframe(c.context, c.builder, typ, diqz__yxrs,
        rsj__kdxuy, val, None)
    return NativeValue(zqy__bnvfh)


def get_hiframes_dtypes(df):
    if (hasattr(df, '_bodo_meta') and df._bodo_meta is not None and 
        'type_metadata' in df._bodo_meta and df._bodo_meta['type_metadata']
         is not None and len(df._bodo_meta['type_metadata'][1]) == len(df.
        columns)):
        xzub__syb = df._bodo_meta['type_metadata'][1]
    else:
        xzub__syb = [None] * len(df.columns)
    bihx__ytyd = [dtype_to_array_type(_infer_series_dtype(df.iloc[:, i],
        array_metadata=xzub__syb[i])) for i in range(len(df.columns))]
    bihx__ytyd = [(bodo.dict_str_arr_type if _use_dict_str_type and 
        dyuw__oxb == string_array_type else dyuw__oxb) for dyuw__oxb in
        bihx__ytyd]
    return tuple(bihx__ytyd)


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
    anbyj__wxvcg, typ = _dtype_from_type_enum_list_recursor(typ_enum_list)
    if len(anbyj__wxvcg) != 0:
        raise_bodo_error(
            f"""Unexpected Internal Error while converting typing metadata: Dtype list was not fully consumed.
 Input typ_enum_list: {typ_enum_list}.
Remainder: {anbyj__wxvcg}. Please file the error here: https://github.com/Bodo-inc/Feedback"""
            )
    return typ


def _dtype_from_type_enum_list_recursor(typ_enum_list):
    if len(typ_enum_list) == 0:
        raise_bodo_error('Unable to infer dtype from empty typ_enum_list')
    elif typ_enum_list[0] in _one_to_one_enum_to_type_map:
        return typ_enum_list[1:], _one_to_one_enum_to_type_map[typ_enum_list[0]
            ]
    elif typ_enum_list[0] == SeriesDtypeEnum.IntegerArray.value:
        iwny__zrif, typ = _dtype_from_type_enum_list_recursor(typ_enum_list[1:]
            )
        return iwny__zrif, IntegerArrayType(typ)
    elif typ_enum_list[0] == SeriesDtypeEnum.ARRAY.value:
        iwny__zrif, typ = _dtype_from_type_enum_list_recursor(typ_enum_list[1:]
            )
        return iwny__zrif, dtype_to_array_type(typ)
    elif typ_enum_list[0] == SeriesDtypeEnum.Decimal.value:
        yiwas__dea = typ_enum_list[1]
        xyc__cvyr = typ_enum_list[2]
        return typ_enum_list[3:], Decimal128Type(yiwas__dea, xyc__cvyr)
    elif typ_enum_list[0] == SeriesDtypeEnum.STRUCT.value:
        ewiz__beobs = typ_enum_list[1]
        mtn__iah = tuple(typ_enum_list[2:2 + ewiz__beobs])
        xahs__nmdz = typ_enum_list[2 + ewiz__beobs:]
        lzkw__irs = []
        for i in range(ewiz__beobs):
            xahs__nmdz, lwtp__rudp = _dtype_from_type_enum_list_recursor(
                xahs__nmdz)
            lzkw__irs.append(lwtp__rudp)
        return xahs__nmdz, StructType(tuple(lzkw__irs), mtn__iah)
    elif typ_enum_list[0] == SeriesDtypeEnum.Literal.value:
        if len(typ_enum_list) == 1:
            raise_bodo_error(
                f"Unexpected Internal Error while converting typing metadata: Encountered 'Literal' internal enum value with no value following it. Please file the error here: https://github.com/Bodo-inc/Feedback"
                )
        iqjs__atlu = typ_enum_list[1]
        xahs__nmdz = typ_enum_list[2:]
        return xahs__nmdz, iqjs__atlu
    elif typ_enum_list[0] == SeriesDtypeEnum.LiteralType.value:
        if len(typ_enum_list) == 1:
            raise_bodo_error(
                f"Unexpected Internal Error while converting typing metadata: Encountered 'LiteralType' internal enum value with no value following it. Please file the error here: https://github.com/Bodo-inc/Feedback"
                )
        iqjs__atlu = typ_enum_list[1]
        xahs__nmdz = typ_enum_list[2:]
        return xahs__nmdz, numba.types.literal(iqjs__atlu)
    elif typ_enum_list[0] == SeriesDtypeEnum.CategoricalType.value:
        xahs__nmdz, fys__oltdt = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        xahs__nmdz, hfgx__zhml = _dtype_from_type_enum_list_recursor(xahs__nmdz
            )
        xahs__nmdz, fxxi__ltyme = _dtype_from_type_enum_list_recursor(
            xahs__nmdz)
        xahs__nmdz, tfb__sdxr = _dtype_from_type_enum_list_recursor(xahs__nmdz)
        xahs__nmdz, nrh__egh = _dtype_from_type_enum_list_recursor(xahs__nmdz)
        return xahs__nmdz, PDCategoricalDtype(fys__oltdt, hfgx__zhml,
            fxxi__ltyme, tfb__sdxr, nrh__egh)
    elif typ_enum_list[0] == SeriesDtypeEnum.DatetimeIndexType.value:
        xahs__nmdz, srfz__fdih = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return xahs__nmdz, DatetimeIndexType(srfz__fdih)
    elif typ_enum_list[0] == SeriesDtypeEnum.NumericIndexType.value:
        xahs__nmdz, dtype = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        xahs__nmdz, srfz__fdih = _dtype_from_type_enum_list_recursor(xahs__nmdz
            )
        xahs__nmdz, tfb__sdxr = _dtype_from_type_enum_list_recursor(xahs__nmdz)
        return xahs__nmdz, NumericIndexType(dtype, srfz__fdih, tfb__sdxr)
    elif typ_enum_list[0] == SeriesDtypeEnum.PeriodIndexType.value:
        xahs__nmdz, xtqtf__sdgo = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        xahs__nmdz, srfz__fdih = _dtype_from_type_enum_list_recursor(xahs__nmdz
            )
        return xahs__nmdz, PeriodIndexType(xtqtf__sdgo, srfz__fdih)
    elif typ_enum_list[0] == SeriesDtypeEnum.CategoricalIndexType.value:
        xahs__nmdz, tfb__sdxr = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        xahs__nmdz, srfz__fdih = _dtype_from_type_enum_list_recursor(xahs__nmdz
            )
        return xahs__nmdz, CategoricalIndexType(tfb__sdxr, srfz__fdih)
    elif typ_enum_list[0] == SeriesDtypeEnum.RangeIndexType.value:
        xahs__nmdz, srfz__fdih = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return xahs__nmdz, RangeIndexType(srfz__fdih)
    elif typ_enum_list[0] == SeriesDtypeEnum.StringIndexType.value:
        xahs__nmdz, srfz__fdih = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return xahs__nmdz, StringIndexType(srfz__fdih)
    elif typ_enum_list[0] == SeriesDtypeEnum.BinaryIndexType.value:
        xahs__nmdz, srfz__fdih = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return xahs__nmdz, BinaryIndexType(srfz__fdih)
    elif typ_enum_list[0] == SeriesDtypeEnum.TimedeltaIndexType.value:
        xahs__nmdz, srfz__fdih = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return xahs__nmdz, TimedeltaIndexType(srfz__fdih)
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
        tasf__czquq = get_overload_const_int(typ)
        if numba.types.maybe_literal(tasf__czquq) == typ:
            return [SeriesDtypeEnum.LiteralType.value, tasf__czquq]
    elif is_overload_constant_str(typ):
        tasf__czquq = get_overload_const_str(typ)
        if numba.types.maybe_literal(tasf__czquq) == typ:
            return [SeriesDtypeEnum.LiteralType.value, tasf__czquq]
    elif is_overload_constant_bool(typ):
        tasf__czquq = get_overload_const_bool(typ)
        if numba.types.maybe_literal(tasf__czquq) == typ:
            return [SeriesDtypeEnum.LiteralType.value, tasf__czquq]
    elif isinstance(typ, IntegerArrayType):
        return [SeriesDtypeEnum.IntegerArray.value
            ] + _dtype_to_type_enum_list_recursor(typ.dtype)
    elif bodo.utils.utils.is_array_typ(typ, False):
        return [SeriesDtypeEnum.ARRAY.value
            ] + _dtype_to_type_enum_list_recursor(typ.dtype)
    elif isinstance(typ, StructType):
        ocwio__niczq = [SeriesDtypeEnum.STRUCT.value, len(typ.names)]
        for cly__utr in typ.names:
            ocwio__niczq.append(cly__utr)
        for hkzl__xrzgy in typ.data:
            ocwio__niczq += _dtype_to_type_enum_list_recursor(hkzl__xrzgy)
        return ocwio__niczq
    elif isinstance(typ, bodo.libs.decimal_arr_ext.Decimal128Type):
        return [SeriesDtypeEnum.Decimal.value, typ.precision, typ.scale]
    elif isinstance(typ, PDCategoricalDtype):
        vjdly__kyxi = _dtype_to_type_enum_list_recursor(typ.categories)
        nlp__isnkw = _dtype_to_type_enum_list_recursor(typ.elem_type)
        qivoj__rhw = _dtype_to_type_enum_list_recursor(typ.ordered)
        vbl__bogdp = _dtype_to_type_enum_list_recursor(typ.data)
        ygih__hxcf = _dtype_to_type_enum_list_recursor(typ.int_type)
        return [SeriesDtypeEnum.CategoricalType.value
            ] + vjdly__kyxi + nlp__isnkw + qivoj__rhw + vbl__bogdp + ygih__hxcf
    elif isinstance(typ, DatetimeIndexType):
        return [SeriesDtypeEnum.DatetimeIndexType.value
            ] + _dtype_to_type_enum_list_recursor(typ.name_typ)
    elif isinstance(typ, NumericIndexType):
        if upcast_numeric_index:
            if isinstance(typ.dtype, types.Float):
                xpizm__jmef = types.float64
                axbm__rggt = types.Array(xpizm__jmef, 1, 'C')
            elif typ.dtype in {types.int8, types.int16, types.int32, types.
                int64}:
                xpizm__jmef = types.int64
                axbm__rggt = types.Array(xpizm__jmef, 1, 'C')
            elif typ.dtype in {types.uint8, types.uint16, types.uint32,
                types.uint64}:
                xpizm__jmef = types.uint64
                axbm__rggt = types.Array(xpizm__jmef, 1, 'C')
            elif typ.dtype == types.bool_:
                xpizm__jmef = typ.dtype
                axbm__rggt = typ.data
            else:
                raise GuardException('Unable to convert type')
            return [SeriesDtypeEnum.NumericIndexType.value
                ] + _dtype_to_type_enum_list_recursor(xpizm__jmef
                ) + _dtype_to_type_enum_list_recursor(typ.name_typ
                ) + _dtype_to_type_enum_list_recursor(axbm__rggt)
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
                zzj__fhyq = S._bodo_meta['type_metadata'][1]
                return _dtype_from_type_enum_list(zzj__fhyq)
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
        wbi__dqog = S.dtype.unit
        if wbi__dqog != 'ns':
            raise BodoError("Timezone-aware datetime data requires 'ns' units")
        pmdt__vwenu = bodo.libs.pd_datetime_arr_ext.get_pytz_type_info(S.
            dtype.tz)
        return PandasDatetimeTZDtype(pmdt__vwenu)
    try:
        return numpy_support.from_dtype(S.dtype)
    except:
        raise BodoError(
            f'data type {S.dtype} for column {S.name} not supported yet')


def _get_use_df_parent_obj_flag(builder, context, pyapi, parent_obj, n_cols):
    if n_cols is None:
        return context.get_constant(types.bool_, False)
    ykgip__tcowi = cgutils.is_not_null(builder, parent_obj)
    yitbc__fql = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with builder.if_then(ykgip__tcowi):
        sde__gyy = pyapi.object_getattr_string(parent_obj, 'columns')
        swsq__fmbc = pyapi.call_method(sde__gyy, '__len__', ())
        builder.store(pyapi.long_as_longlong(swsq__fmbc), yitbc__fql)
        pyapi.decref(swsq__fmbc)
        pyapi.decref(sde__gyy)
    use_parent_obj = builder.and_(ykgip__tcowi, builder.icmp_unsigned('==',
        builder.load(yitbc__fql), context.get_constant(types.int64, n_cols)))
    return use_parent_obj


def _get_df_columns_obj(c, builder, context, pyapi, df_typ, dataframe_payload):
    if df_typ.has_runtime_cols:
        vhdtu__mcbzy = df_typ.runtime_colname_typ
        context.nrt.incref(builder, vhdtu__mcbzy, dataframe_payload.columns)
        return pyapi.from_native_value(vhdtu__mcbzy, dataframe_payload.
            columns, c.env_manager)
    if all(isinstance(c, int) for c in df_typ.columns):
        iih__ygdv = np.array(df_typ.columns, 'int64')
    elif all(isinstance(c, str) for c in df_typ.columns):
        iih__ygdv = pd.array(df_typ.columns, 'string')
    else:
        iih__ygdv = df_typ.columns
    unjgm__jqyxq = numba.typeof(iih__ygdv)
    ukwg__kwd = context.get_constant_generic(builder, unjgm__jqyxq, iih__ygdv)
    pufq__woy = pyapi.from_native_value(unjgm__jqyxq, ukwg__kwd, c.env_manager)
    return pufq__woy


def _create_initial_df_object(builder, context, pyapi, c, df_typ, obj,
    dataframe_payload, res, use_parent_obj):
    with c.builder.if_else(use_parent_obj) as (yaod__egbgu, ercgt__azk):
        with yaod__egbgu:
            pyapi.incref(obj)
            mue__oiag = context.insert_const_string(c.builder.module, 'numpy')
            tqzpl__siq = pyapi.import_module_noblock(mue__oiag)
            if df_typ.has_runtime_cols:
                vih__egwe = 0
            else:
                vih__egwe = len(df_typ.columns)
            sfvz__ubwi = pyapi.long_from_longlong(lir.Constant(lir.IntType(
                64), vih__egwe))
            efa__wiu = pyapi.call_method(tqzpl__siq, 'arange', (sfvz__ubwi,))
            pyapi.object_setattr_string(obj, 'columns', efa__wiu)
            pyapi.decref(tqzpl__siq)
            pyapi.decref(efa__wiu)
            pyapi.decref(sfvz__ubwi)
        with ercgt__azk:
            context.nrt.incref(builder, df_typ.index, dataframe_payload.index)
            mfyoe__lovev = c.pyapi.from_native_value(df_typ.index,
                dataframe_payload.index, c.env_manager)
            mue__oiag = context.insert_const_string(c.builder.module, 'pandas')
            tqzpl__siq = pyapi.import_module_noblock(mue__oiag)
            df_obj = pyapi.call_method(tqzpl__siq, 'DataFrame', (pyapi.
                borrow_none(), mfyoe__lovev))
            pyapi.decref(tqzpl__siq)
            pyapi.decref(mfyoe__lovev)
            builder.store(df_obj, res)


@box(DataFrameType)
def box_dataframe(typ, val, c):
    from bodo.hiframes.table import box_table
    context = c.context
    builder = c.builder
    pyapi = c.pyapi
    dataframe_payload = bodo.hiframes.pd_dataframe_ext.get_dataframe_payload(c
        .context, c.builder, typ, val)
    wjuw__dqd = cgutils.create_struct_proxy(typ)(context, builder, value=val)
    n_cols = len(typ.columns) if not typ.has_runtime_cols else None
    obj = wjuw__dqd.parent
    res = cgutils.alloca_once_value(builder, obj)
    use_parent_obj = _get_use_df_parent_obj_flag(builder, context, pyapi,
        obj, n_cols)
    _create_initial_df_object(builder, context, pyapi, c, typ, obj,
        dataframe_payload, res, use_parent_obj)
    if typ.is_table_format:
        yekfy__gds = typ.table_type
        daih__xmc = builder.extract_value(dataframe_payload.data, 0)
        context.nrt.incref(builder, yekfy__gds, daih__xmc)
        ldgar__lwctm = box_table(yekfy__gds, daih__xmc, c, builder.not_(
            use_parent_obj))
        with builder.if_else(use_parent_obj) as (krum__ovg, cyuoo__jik):
            with krum__ovg:
                kcq__leoro = pyapi.object_getattr_string(ldgar__lwctm, 'arrays'
                    )
                dsi__zdny = c.pyapi.make_none()
                if n_cols is None:
                    swsq__fmbc = pyapi.call_method(kcq__leoro, '__len__', ())
                    ufdt__nmwu = pyapi.long_as_longlong(swsq__fmbc)
                    pyapi.decref(swsq__fmbc)
                else:
                    ufdt__nmwu = context.get_constant(types.int64, n_cols)
                with cgutils.for_range(builder, ufdt__nmwu) as sryce__uxha:
                    i = sryce__uxha.index
                    gsxl__kwp = pyapi.list_getitem(kcq__leoro, i)
                    ozmf__jkr = c.builder.icmp_unsigned('!=', gsxl__kwp,
                        dsi__zdny)
                    with builder.if_then(ozmf__jkr):
                        iatq__dbq = pyapi.long_from_longlong(i)
                        df_obj = builder.load(res)
                        pyapi.object_setitem(df_obj, iatq__dbq, gsxl__kwp)
                        pyapi.decref(iatq__dbq)
                pyapi.decref(kcq__leoro)
                pyapi.decref(dsi__zdny)
            with cyuoo__jik:
                df_obj = builder.load(res)
                mfyoe__lovev = pyapi.object_getattr_string(df_obj, 'index')
                waz__req = c.pyapi.call_method(ldgar__lwctm, 'to_pandas', (
                    mfyoe__lovev,))
                builder.store(waz__req, res)
                pyapi.decref(df_obj)
                pyapi.decref(mfyoe__lovev)
        pyapi.decref(ldgar__lwctm)
    else:
        olkt__vdwjw = [builder.extract_value(dataframe_payload.data, i) for
            i in range(n_cols)]
        ktzv__jhxtd = typ.data
        for i, mqp__pfhu, clg__rbdi in zip(range(n_cols), olkt__vdwjw,
            ktzv__jhxtd):
            etfy__kauxu = cgutils.alloca_once_value(builder, mqp__pfhu)
            vtvjs__waq = cgutils.alloca_once_value(builder, context.
                get_constant_null(clg__rbdi))
            ozmf__jkr = builder.not_(is_ll_eq(builder, etfy__kauxu, vtvjs__waq)
                )
            thzt__nxp = builder.or_(builder.not_(use_parent_obj), builder.
                and_(use_parent_obj, ozmf__jkr))
            with builder.if_then(thzt__nxp):
                iatq__dbq = pyapi.long_from_longlong(context.get_constant(
                    types.int64, i))
                context.nrt.incref(builder, clg__rbdi, mqp__pfhu)
                arr_obj = pyapi.from_native_value(clg__rbdi, mqp__pfhu, c.
                    env_manager)
                df_obj = builder.load(res)
                pyapi.object_setitem(df_obj, iatq__dbq, arr_obj)
                pyapi.decref(arr_obj)
                pyapi.decref(iatq__dbq)
    df_obj = builder.load(res)
    pufq__woy = _get_df_columns_obj(c, builder, context, pyapi, typ,
        dataframe_payload)
    pyapi.object_setattr_string(df_obj, 'columns', pufq__woy)
    pyapi.decref(pufq__woy)
    _set_bodo_meta_dataframe(c, df_obj, typ)
    c.context.nrt.decref(c.builder, typ, val)
    return df_obj


def get_df_obj_column_codegen(context, builder, pyapi, df_obj, col_ind,
    data_typ):
    dsi__zdny = pyapi.borrow_none()
    fzjo__mndi = pyapi.unserialize(pyapi.serialize_object(slice))
    jxg__qnpn = pyapi.call_function_objargs(fzjo__mndi, [dsi__zdny])
    lrr__mmtcf = pyapi.long_from_longlong(col_ind)
    fyzfz__mahal = pyapi.tuple_pack([jxg__qnpn, lrr__mmtcf])
    yqd__qrxr = pyapi.object_getattr_string(df_obj, 'iloc')
    uylk__yeqbh = pyapi.object_getitem(yqd__qrxr, fyzfz__mahal)
    if isinstance(data_typ, bodo.DatetimeArrayType):
        cxjxi__idz = pyapi.object_getattr_string(uylk__yeqbh, 'array')
    else:
        cxjxi__idz = pyapi.object_getattr_string(uylk__yeqbh, 'values')
    if isinstance(data_typ, types.Array):
        hjzf__uevq = context.insert_const_string(builder.module, 'numpy')
        tsof__ljdj = pyapi.import_module_noblock(hjzf__uevq)
        arr_obj = pyapi.call_method(tsof__ljdj, 'ascontiguousarray', (
            cxjxi__idz,))
        pyapi.decref(cxjxi__idz)
        pyapi.decref(tsof__ljdj)
    else:
        arr_obj = cxjxi__idz
    pyapi.decref(fzjo__mndi)
    pyapi.decref(jxg__qnpn)
    pyapi.decref(lrr__mmtcf)
    pyapi.decref(fyzfz__mahal)
    pyapi.decref(yqd__qrxr)
    pyapi.decref(uylk__yeqbh)
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
        wjuw__dqd = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        arr_obj = get_df_obj_column_codegen(context, builder, pyapi,
            wjuw__dqd.parent, args[1], data_typ)
        glzk__hhjy = _unbox_series_data(data_typ.dtype, data_typ, arr_obj, c)
        c.pyapi.decref(arr_obj)
        dataframe_payload = (bodo.hiframes.pd_dataframe_ext.
            get_dataframe_payload(c.context, c.builder, df_typ, args[0]))
        if df_typ.is_table_format:
            daih__xmc = cgutils.create_struct_proxy(df_typ.table_type)(c.
                context, c.builder, builder.extract_value(dataframe_payload
                .data, 0))
            kntja__yan = df_typ.table_type.type_to_blk[data_typ]
            klw__jtwi = getattr(daih__xmc, f'block_{kntja__yan}')
            nnduk__ejh = ListInstance(c.context, c.builder, types.List(
                data_typ), klw__jtwi)
            jvjdl__qbtcs = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[col_ind])
            nnduk__ejh.inititem(jvjdl__qbtcs, glzk__hhjy.value, incref=False)
        else:
            dataframe_payload.data = builder.insert_value(dataframe_payload
                .data, glzk__hhjy.value, col_ind)
        dsh__mihw = DataFramePayloadType(df_typ)
        btldq__mqenr = context.nrt.meminfo_data(builder, wjuw__dqd.meminfo)
        iljxx__racz = context.get_value_type(dsh__mihw).as_pointer()
        btldq__mqenr = builder.bitcast(btldq__mqenr, iljxx__racz)
        builder.store(dataframe_payload._getvalue(), btldq__mqenr)
    return signature(types.none, df, i), codegen


@numba.njit
def unbox_col_if_needed(df, i):
    if bodo.hiframes.pd_dataframe_ext.has_parent(df
        ) and bodo.hiframes.pd_dataframe_ext._column_needs_unboxing(df, i):
        bodo.hiframes.boxing.unbox_dataframe_column(df, i)


@unbox(SeriesType)
def unbox_series(typ, val, c):
    if isinstance(typ.data, DatetimeArrayType):
        cxjxi__idz = c.pyapi.object_getattr_string(val, 'array')
    else:
        cxjxi__idz = c.pyapi.object_getattr_string(val, 'values')
    if isinstance(typ.data, types.Array):
        hjzf__uevq = c.context.insert_const_string(c.builder.module, 'numpy')
        tsof__ljdj = c.pyapi.import_module_noblock(hjzf__uevq)
        arr_obj = c.pyapi.call_method(tsof__ljdj, 'ascontiguousarray', (
            cxjxi__idz,))
        c.pyapi.decref(cxjxi__idz)
        c.pyapi.decref(tsof__ljdj)
    else:
        arr_obj = cxjxi__idz
    tyhm__kxfjk = _unbox_series_data(typ.dtype, typ.data, arr_obj, c).value
    mfyoe__lovev = c.pyapi.object_getattr_string(val, 'index')
    rsj__kdxuy = c.pyapi.to_native_value(typ.index, mfyoe__lovev).value
    qwh__xhsvv = c.pyapi.object_getattr_string(val, 'name')
    denem__psy = c.pyapi.to_native_value(typ.name_typ, qwh__xhsvv).value
    fsxn__hume = bodo.hiframes.pd_series_ext.construct_series(c.context, c.
        builder, typ, tyhm__kxfjk, rsj__kdxuy, denem__psy)
    c.pyapi.decref(arr_obj)
    c.pyapi.decref(mfyoe__lovev)
    c.pyapi.decref(qwh__xhsvv)
    return NativeValue(fsxn__hume)


def _unbox_series_data(dtype, data_typ, arr_obj, c):
    if data_typ == string_array_split_view_type:
        ruza__rwvyp = c.context.make_helper(c.builder,
            string_array_split_view_type)
        return NativeValue(ruza__rwvyp._getvalue())
    return c.pyapi.to_native_value(data_typ, arr_obj)


@box(HeterogeneousSeriesType)
@box(SeriesType)
def box_series(typ, val, c):
    mue__oiag = c.context.insert_const_string(c.builder.module, 'pandas')
    ibn__gvcoa = c.pyapi.import_module_noblock(mue__oiag)
    slwy__keqq = bodo.hiframes.pd_series_ext.get_series_payload(c.context,
        c.builder, typ, val)
    c.context.nrt.incref(c.builder, typ.data, slwy__keqq.data)
    c.context.nrt.incref(c.builder, typ.index, slwy__keqq.index)
    c.context.nrt.incref(c.builder, typ.name_typ, slwy__keqq.name)
    arr_obj = c.pyapi.from_native_value(typ.data, slwy__keqq.data, c.
        env_manager)
    mfyoe__lovev = c.pyapi.from_native_value(typ.index, slwy__keqq.index, c
        .env_manager)
    qwh__xhsvv = c.pyapi.from_native_value(typ.name_typ, slwy__keqq.name, c
        .env_manager)
    if isinstance(typ, HeterogeneousSeriesType) and isinstance(typ.data,
        bodo.NullableTupleType):
        dtype = c.pyapi.unserialize(c.pyapi.serialize_object(object))
    else:
        dtype = c.pyapi.make_none()
    res = c.pyapi.call_method(ibn__gvcoa, 'Series', (arr_obj, mfyoe__lovev,
        dtype, qwh__xhsvv))
    c.pyapi.decref(arr_obj)
    c.pyapi.decref(mfyoe__lovev)
    c.pyapi.decref(qwh__xhsvv)
    if isinstance(typ, HeterogeneousSeriesType) and isinstance(typ.data,
        bodo.NullableTupleType):
        c.pyapi.decref(dtype)
    _set_bodo_meta_series(res, c, typ)
    c.pyapi.decref(ibn__gvcoa)
    c.context.nrt.decref(c.builder, typ, val)
    return res


def type_enum_list_to_py_list_obj(pyapi, context, builder, env_manager,
    typ_list):
    img__swg = []
    for zryj__uhw in typ_list:
        if isinstance(zryj__uhw, int) and not isinstance(zryj__uhw, bool):
            lbsrd__avb = pyapi.long_from_longlong(lir.Constant(lir.IntType(
                64), zryj__uhw))
        else:
            gqf__jyy = numba.typeof(zryj__uhw)
            jku__veyl = context.get_constant_generic(builder, gqf__jyy,
                zryj__uhw)
            lbsrd__avb = pyapi.from_native_value(gqf__jyy, jku__veyl,
                env_manager)
        img__swg.append(lbsrd__avb)
    azkv__wjmnn = pyapi.list_pack(img__swg)
    for val in img__swg:
        pyapi.decref(val)
    return azkv__wjmnn


def _set_bodo_meta_dataframe(c, obj, typ):
    pyapi = c.pyapi
    context = c.context
    builder = c.builder
    nygq__nqy = not typ.has_runtime_cols and (not typ.is_table_format or 
        len(typ.columns) < TABLE_FORMAT_THRESHOLD)
    ugvik__jixr = 2 if nygq__nqy else 1
    rhkoj__ayfe = pyapi.dict_new(ugvik__jixr)
    coc__ths = pyapi.long_from_longlong(lir.Constant(lir.IntType(64), typ.
        dist.value))
    pyapi.dict_setitem_string(rhkoj__ayfe, 'dist', coc__ths)
    pyapi.decref(coc__ths)
    if nygq__nqy:
        emwq__fngrm = _dtype_to_type_enum_list(typ.index)
        if emwq__fngrm != None:
            ddmf__lpd = type_enum_list_to_py_list_obj(pyapi, context,
                builder, c.env_manager, emwq__fngrm)
        else:
            ddmf__lpd = pyapi.make_none()
        jirqx__logv = []
        for dtype in typ.data:
            typ_list = _dtype_to_type_enum_list(dtype)
            if typ_list != None:
                azkv__wjmnn = type_enum_list_to_py_list_obj(pyapi, context,
                    builder, c.env_manager, typ_list)
            else:
                azkv__wjmnn = pyapi.make_none()
            jirqx__logv.append(azkv__wjmnn)
        ngys__tvy = pyapi.list_pack(jirqx__logv)
        ecy__mnu = pyapi.list_pack([ddmf__lpd, ngys__tvy])
        for val in jirqx__logv:
            pyapi.decref(val)
        pyapi.dict_setitem_string(rhkoj__ayfe, 'type_metadata', ecy__mnu)
    pyapi.object_setattr_string(obj, '_bodo_meta', rhkoj__ayfe)
    pyapi.decref(rhkoj__ayfe)


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
    rhkoj__ayfe = pyapi.dict_new(2)
    coc__ths = pyapi.long_from_longlong(lir.Constant(lir.IntType(64), typ.
        dist.value))
    emwq__fngrm = _dtype_to_type_enum_list(typ.index)
    if emwq__fngrm != None:
        ddmf__lpd = type_enum_list_to_py_list_obj(pyapi, context, builder,
            c.env_manager, emwq__fngrm)
    else:
        ddmf__lpd = pyapi.make_none()
    dtype = get_series_dtype_handle_null_int_and_hetrogenous(typ)
    if dtype != None:
        typ_list = _dtype_to_type_enum_list(dtype)
        if typ_list != None:
            lypuy__ijvtk = type_enum_list_to_py_list_obj(pyapi, context,
                builder, c.env_manager, typ_list)
        else:
            lypuy__ijvtk = pyapi.make_none()
    else:
        lypuy__ijvtk = pyapi.make_none()
    uwpnc__thet = pyapi.list_pack([ddmf__lpd, lypuy__ijvtk])
    pyapi.dict_setitem_string(rhkoj__ayfe, 'type_metadata', uwpnc__thet)
    pyapi.decref(uwpnc__thet)
    pyapi.dict_setitem_string(rhkoj__ayfe, 'dist', coc__ths)
    pyapi.object_setattr_string(obj, '_bodo_meta', rhkoj__ayfe)
    pyapi.decref(rhkoj__ayfe)
    pyapi.decref(coc__ths)


@typeof_impl.register(np.ndarray)
def _typeof_ndarray(val, c):
    try:
        dtype = numba.np.numpy_support.from_dtype(val.dtype)
    except NotImplementedError as viytt__ssqx:
        dtype = types.pyobject
    if dtype == types.pyobject:
        return _infer_ndarray_obj_dtype(val)
    gbty__zqk = numba.np.numpy_support.map_layout(val)
    dngf__jplb = not val.flags.writeable
    return types.Array(dtype, val.ndim, gbty__zqk, readonly=dngf__jplb)


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
    rwxc__tspbk = val[i]
    if isinstance(rwxc__tspbk, str):
        return (bodo.dict_str_arr_type if _use_dict_str_type else
            string_array_type)
    elif isinstance(rwxc__tspbk, bytes):
        return binary_array_type
    elif isinstance(rwxc__tspbk, bool):
        return bodo.libs.bool_arr_ext.boolean_array
    elif isinstance(rwxc__tspbk, (int, np.int32, np.int64)):
        return bodo.libs.int_arr_ext.IntegerArrayType(numba.typeof(rwxc__tspbk)
            )
    elif isinstance(rwxc__tspbk, (dict, Dict)) and all(isinstance(
        wvyet__ezixm, str) for wvyet__ezixm in rwxc__tspbk.keys()):
        mtn__iah = tuple(rwxc__tspbk.keys())
        zykch__hbj = tuple(_get_struct_value_arr_type(v) for v in
            rwxc__tspbk.values())
        return StructArrayType(zykch__hbj, mtn__iah)
    elif isinstance(rwxc__tspbk, (dict, Dict)):
        ingd__vhu = numba.typeof(_value_to_array(list(rwxc__tspbk.keys())))
        lggfv__usmuo = numba.typeof(_value_to_array(list(rwxc__tspbk.values()))
            )
        ingd__vhu = to_str_arr_if_dict_array(ingd__vhu)
        lggfv__usmuo = to_str_arr_if_dict_array(lggfv__usmuo)
        return MapArrayType(ingd__vhu, lggfv__usmuo)
    elif isinstance(rwxc__tspbk, tuple):
        zykch__hbj = tuple(_get_struct_value_arr_type(v) for v in rwxc__tspbk)
        return TupleArrayType(zykch__hbj)
    if isinstance(rwxc__tspbk, (list, np.ndarray, pd.arrays.BooleanArray,
        pd.arrays.IntegerArray, pd.arrays.StringArray)):
        if isinstance(rwxc__tspbk, list):
            rwxc__tspbk = _value_to_array(rwxc__tspbk)
        zpznd__cehre = numba.typeof(rwxc__tspbk)
        zpznd__cehre = to_str_arr_if_dict_array(zpznd__cehre)
        return ArrayItemArrayType(zpznd__cehre)
    if isinstance(rwxc__tspbk, datetime.date):
        return datetime_date_array_type
    if isinstance(rwxc__tspbk, datetime.timedelta):
        return datetime_timedelta_array_type
    if isinstance(rwxc__tspbk, decimal.Decimal):
        return DecimalArrayType(38, 18)
    raise BodoError(f'Unsupported object array with first value: {rwxc__tspbk}'
        )


def _value_to_array(val):
    assert isinstance(val, (list, dict, Dict))
    if isinstance(val, (dict, Dict)):
        val = dict(val)
        return np.array([val], np.object_)
    lbs__oojqj = val.copy()
    lbs__oojqj.append(None)
    mqp__pfhu = np.array(lbs__oojqj, np.object_)
    if len(val) and isinstance(val[0], float):
        mqp__pfhu = np.array(val, np.float64)
    return mqp__pfhu


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
    clg__rbdi = dtype_to_array_type(numba.typeof(v))
    if isinstance(v, (int, bool)):
        clg__rbdi = to_nullable_type(clg__rbdi)
    return clg__rbdi
