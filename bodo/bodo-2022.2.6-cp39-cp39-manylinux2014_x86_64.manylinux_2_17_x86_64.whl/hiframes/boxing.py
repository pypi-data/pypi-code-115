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
    hug__jxxj = tuple(val.columns.to_list())
    qby__eos = get_hiframes_dtypes(val)
    if (len(val.index) == 0 and val.index.dtype == np.dtype('O') and
        hasattr(val, '_bodo_meta') and val._bodo_meta is not None and 
        'type_metadata' in val._bodo_meta and val._bodo_meta[
        'type_metadata'] is not None and len(val._bodo_meta['type_metadata'
        ][1]) == len(val.columns) and val._bodo_meta['type_metadata'][0] is not
        None):
        cap__hdc = _dtype_from_type_enum_list(val._bodo_meta[
            'type_metadata'][0])
    else:
        cap__hdc = numba.typeof(val.index)
    lcrt__uxg = Distribution(val._bodo_meta['dist']) if hasattr(val,
        '_bodo_meta') and val._bodo_meta is not None else Distribution.REP
    mwfsx__ysbw = len(qby__eos) >= TABLE_FORMAT_THRESHOLD
    return DataFrameType(qby__eos, cap__hdc, hug__jxxj, lcrt__uxg,
        is_table_format=mwfsx__ysbw)


@typeof_impl.register(pd.Series)
def typeof_pd_series(val, c):
    from bodo.transforms.distributed_analysis import Distribution
    lcrt__uxg = Distribution(val._bodo_meta['dist']) if hasattr(val,
        '_bodo_meta') and val._bodo_meta is not None else Distribution.REP
    if (len(val.index) == 0 and val.index.dtype == np.dtype('O') and
        hasattr(val, '_bodo_meta') and val._bodo_meta is not None and 
        'type_metadata' in val._bodo_meta and val._bodo_meta[
        'type_metadata'] is not None and val._bodo_meta['type_metadata'][0]
         is not None):
        gyqr__upa = _dtype_from_type_enum_list(val._bodo_meta[
            'type_metadata'][0])
    else:
        gyqr__upa = numba.typeof(val.index)
    dtype = _infer_series_dtype(val)
    ofyyx__dydsz = dtype_to_array_type(dtype)
    if _use_dict_str_type and ofyyx__dydsz == string_array_type:
        ofyyx__dydsz = bodo.dict_str_arr_type
    return SeriesType(dtype, data=ofyyx__dydsz, index=gyqr__upa, name_typ=
        numba.typeof(val.name), dist=lcrt__uxg)


@unbox(DataFrameType)
def unbox_dataframe(typ, val, c):
    check_runtime_cols_unsupported(typ, 'Unboxing')
    pbwss__svye = c.pyapi.object_getattr_string(val, 'index')
    jfdw__duozj = c.pyapi.to_native_value(typ.index, pbwss__svye).value
    c.pyapi.decref(pbwss__svye)
    if typ.is_table_format:
        zzuyw__wolxp = cgutils.create_struct_proxy(typ.table_type)(c.
            context, c.builder)
        zzuyw__wolxp.parent = val
        for lajzn__seqs, gdey__kltk in typ.table_type.type_to_blk.items():
            kiiq__ytaxi = c.context.get_constant(types.int64, len(typ.
                table_type.block_to_arr_ind[gdey__kltk]))
            ijlo__ijnhd, timkw__hpm = ListInstance.allocate_ex(c.context, c
                .builder, types.List(lajzn__seqs), kiiq__ytaxi)
            timkw__hpm.size = kiiq__ytaxi
            setattr(zzuyw__wolxp, f'block_{gdey__kltk}', timkw__hpm.value)
        ncu__jozta = c.pyapi.call_method(val, '__len__', ())
        fowro__nobfu = c.pyapi.long_as_longlong(ncu__jozta)
        c.pyapi.decref(ncu__jozta)
        zzuyw__wolxp.len = fowro__nobfu
        eefea__ergol = c.context.make_tuple(c.builder, types.Tuple([typ.
            table_type]), [zzuyw__wolxp._getvalue()])
    else:
        uih__xmyvg = [c.context.get_constant_null(lajzn__seqs) for
            lajzn__seqs in typ.data]
        eefea__ergol = c.context.make_tuple(c.builder, types.Tuple(typ.data
            ), uih__xmyvg)
    bung__pptny = construct_dataframe(c.context, c.builder, typ,
        eefea__ergol, jfdw__duozj, val, None)
    return NativeValue(bung__pptny)


def get_hiframes_dtypes(df):
    if (hasattr(df, '_bodo_meta') and df._bodo_meta is not None and 
        'type_metadata' in df._bodo_meta and df._bodo_meta['type_metadata']
         is not None and len(df._bodo_meta['type_metadata'][1]) == len(df.
        columns)):
        jce__xfm = df._bodo_meta['type_metadata'][1]
    else:
        jce__xfm = [None] * len(df.columns)
    mbm__jekig = [dtype_to_array_type(_infer_series_dtype(df.iloc[:, i],
        array_metadata=jce__xfm[i])) for i in range(len(df.columns))]
    mbm__jekig = [(bodo.dict_str_arr_type if _use_dict_str_type and 
        lajzn__seqs == string_array_type else lajzn__seqs) for lajzn__seqs in
        mbm__jekig]
    return tuple(mbm__jekig)


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
    fiex__rylq, typ = _dtype_from_type_enum_list_recursor(typ_enum_list)
    if len(fiex__rylq) != 0:
        raise_bodo_error(
            f"""Unexpected Internal Error while converting typing metadata: Dtype list was not fully consumed.
 Input typ_enum_list: {typ_enum_list}.
Remainder: {fiex__rylq}. Please file the error here: https://github.com/Bodo-inc/Feedback"""
            )
    return typ


def _dtype_from_type_enum_list_recursor(typ_enum_list):
    if len(typ_enum_list) == 0:
        raise_bodo_error('Unable to infer dtype from empty typ_enum_list')
    elif typ_enum_list[0] in _one_to_one_enum_to_type_map:
        return typ_enum_list[1:], _one_to_one_enum_to_type_map[typ_enum_list[0]
            ]
    elif typ_enum_list[0] == SeriesDtypeEnum.IntegerArray.value:
        mysb__llj, typ = _dtype_from_type_enum_list_recursor(typ_enum_list[1:])
        return mysb__llj, IntegerArrayType(typ)
    elif typ_enum_list[0] == SeriesDtypeEnum.ARRAY.value:
        mysb__llj, typ = _dtype_from_type_enum_list_recursor(typ_enum_list[1:])
        return mysb__llj, dtype_to_array_type(typ)
    elif typ_enum_list[0] == SeriesDtypeEnum.Decimal.value:
        sme__fufww = typ_enum_list[1]
        pqh__gjl = typ_enum_list[2]
        return typ_enum_list[3:], Decimal128Type(sme__fufww, pqh__gjl)
    elif typ_enum_list[0] == SeriesDtypeEnum.STRUCT.value:
        suvme__ckgzn = typ_enum_list[1]
        lziyn__xjkp = tuple(typ_enum_list[2:2 + suvme__ckgzn])
        dhtv__oqudn = typ_enum_list[2 + suvme__ckgzn:]
        vncp__ctz = []
        for i in range(suvme__ckgzn):
            dhtv__oqudn, ucmy__piotl = _dtype_from_type_enum_list_recursor(
                dhtv__oqudn)
            vncp__ctz.append(ucmy__piotl)
        return dhtv__oqudn, StructType(tuple(vncp__ctz), lziyn__xjkp)
    elif typ_enum_list[0] == SeriesDtypeEnum.Literal.value:
        if len(typ_enum_list) == 1:
            raise_bodo_error(
                f"Unexpected Internal Error while converting typing metadata: Encountered 'Literal' internal enum value with no value following it. Please file the error here: https://github.com/Bodo-inc/Feedback"
                )
        fnkz__lvq = typ_enum_list[1]
        dhtv__oqudn = typ_enum_list[2:]
        return dhtv__oqudn, fnkz__lvq
    elif typ_enum_list[0] == SeriesDtypeEnum.LiteralType.value:
        if len(typ_enum_list) == 1:
            raise_bodo_error(
                f"Unexpected Internal Error while converting typing metadata: Encountered 'LiteralType' internal enum value with no value following it. Please file the error here: https://github.com/Bodo-inc/Feedback"
                )
        fnkz__lvq = typ_enum_list[1]
        dhtv__oqudn = typ_enum_list[2:]
        return dhtv__oqudn, numba.types.literal(fnkz__lvq)
    elif typ_enum_list[0] == SeriesDtypeEnum.CategoricalType.value:
        dhtv__oqudn, uddp__aycat = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        dhtv__oqudn, bdd__chhza = _dtype_from_type_enum_list_recursor(
            dhtv__oqudn)
        dhtv__oqudn, roj__ywoqa = _dtype_from_type_enum_list_recursor(
            dhtv__oqudn)
        dhtv__oqudn, qofo__pmvye = _dtype_from_type_enum_list_recursor(
            dhtv__oqudn)
        dhtv__oqudn, usw__hlrui = _dtype_from_type_enum_list_recursor(
            dhtv__oqudn)
        return dhtv__oqudn, PDCategoricalDtype(uddp__aycat, bdd__chhza,
            roj__ywoqa, qofo__pmvye, usw__hlrui)
    elif typ_enum_list[0] == SeriesDtypeEnum.DatetimeIndexType.value:
        dhtv__oqudn, lre__dwght = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return dhtv__oqudn, DatetimeIndexType(lre__dwght)
    elif typ_enum_list[0] == SeriesDtypeEnum.NumericIndexType.value:
        dhtv__oqudn, dtype = _dtype_from_type_enum_list_recursor(typ_enum_list
            [1:])
        dhtv__oqudn, lre__dwght = _dtype_from_type_enum_list_recursor(
            dhtv__oqudn)
        dhtv__oqudn, qofo__pmvye = _dtype_from_type_enum_list_recursor(
            dhtv__oqudn)
        return dhtv__oqudn, NumericIndexType(dtype, lre__dwght, qofo__pmvye)
    elif typ_enum_list[0] == SeriesDtypeEnum.PeriodIndexType.value:
        dhtv__oqudn, okv__jtl = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        dhtv__oqudn, lre__dwght = _dtype_from_type_enum_list_recursor(
            dhtv__oqudn)
        return dhtv__oqudn, PeriodIndexType(okv__jtl, lre__dwght)
    elif typ_enum_list[0] == SeriesDtypeEnum.CategoricalIndexType.value:
        dhtv__oqudn, qofo__pmvye = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        dhtv__oqudn, lre__dwght = _dtype_from_type_enum_list_recursor(
            dhtv__oqudn)
        return dhtv__oqudn, CategoricalIndexType(qofo__pmvye, lre__dwght)
    elif typ_enum_list[0] == SeriesDtypeEnum.RangeIndexType.value:
        dhtv__oqudn, lre__dwght = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return dhtv__oqudn, RangeIndexType(lre__dwght)
    elif typ_enum_list[0] == SeriesDtypeEnum.StringIndexType.value:
        dhtv__oqudn, lre__dwght = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return dhtv__oqudn, StringIndexType(lre__dwght)
    elif typ_enum_list[0] == SeriesDtypeEnum.BinaryIndexType.value:
        dhtv__oqudn, lre__dwght = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return dhtv__oqudn, BinaryIndexType(lre__dwght)
    elif typ_enum_list[0] == SeriesDtypeEnum.TimedeltaIndexType.value:
        dhtv__oqudn, lre__dwght = _dtype_from_type_enum_list_recursor(
            typ_enum_list[1:])
        return dhtv__oqudn, TimedeltaIndexType(lre__dwght)
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
        xikj__hyav = get_overload_const_int(typ)
        if numba.types.maybe_literal(xikj__hyav) == typ:
            return [SeriesDtypeEnum.LiteralType.value, xikj__hyav]
    elif is_overload_constant_str(typ):
        xikj__hyav = get_overload_const_str(typ)
        if numba.types.maybe_literal(xikj__hyav) == typ:
            return [SeriesDtypeEnum.LiteralType.value, xikj__hyav]
    elif is_overload_constant_bool(typ):
        xikj__hyav = get_overload_const_bool(typ)
        if numba.types.maybe_literal(xikj__hyav) == typ:
            return [SeriesDtypeEnum.LiteralType.value, xikj__hyav]
    elif isinstance(typ, IntegerArrayType):
        return [SeriesDtypeEnum.IntegerArray.value
            ] + _dtype_to_type_enum_list_recursor(typ.dtype)
    elif bodo.utils.utils.is_array_typ(typ, False):
        return [SeriesDtypeEnum.ARRAY.value
            ] + _dtype_to_type_enum_list_recursor(typ.dtype)
    elif isinstance(typ, StructType):
        dmwj__pmkb = [SeriesDtypeEnum.STRUCT.value, len(typ.names)]
        for nynwc__echba in typ.names:
            dmwj__pmkb.append(nynwc__echba)
        for hjs__ifv in typ.data:
            dmwj__pmkb += _dtype_to_type_enum_list_recursor(hjs__ifv)
        return dmwj__pmkb
    elif isinstance(typ, bodo.libs.decimal_arr_ext.Decimal128Type):
        return [SeriesDtypeEnum.Decimal.value, typ.precision, typ.scale]
    elif isinstance(typ, PDCategoricalDtype):
        akobu__ugegb = _dtype_to_type_enum_list_recursor(typ.categories)
        amxnu__eubg = _dtype_to_type_enum_list_recursor(typ.elem_type)
        ldsi__iahw = _dtype_to_type_enum_list_recursor(typ.ordered)
        svz__nfv = _dtype_to_type_enum_list_recursor(typ.data)
        xbuy__nvjez = _dtype_to_type_enum_list_recursor(typ.int_type)
        return [SeriesDtypeEnum.CategoricalType.value
            ] + akobu__ugegb + amxnu__eubg + ldsi__iahw + svz__nfv + xbuy__nvjez
    elif isinstance(typ, DatetimeIndexType):
        return [SeriesDtypeEnum.DatetimeIndexType.value
            ] + _dtype_to_type_enum_list_recursor(typ.name_typ)
    elif isinstance(typ, NumericIndexType):
        if upcast_numeric_index:
            if isinstance(typ.dtype, types.Float):
                nep__kjb = types.float64
                qalb__kkk = types.Array(nep__kjb, 1, 'C')
            elif typ.dtype in {types.int8, types.int16, types.int32, types.
                int64}:
                nep__kjb = types.int64
                qalb__kkk = types.Array(nep__kjb, 1, 'C')
            elif typ.dtype in {types.uint8, types.uint16, types.uint32,
                types.uint64}:
                nep__kjb = types.uint64
                qalb__kkk = types.Array(nep__kjb, 1, 'C')
            elif typ.dtype == types.bool_:
                nep__kjb = typ.dtype
                qalb__kkk = typ.data
            else:
                raise GuardException('Unable to convert type')
            return [SeriesDtypeEnum.NumericIndexType.value
                ] + _dtype_to_type_enum_list_recursor(nep__kjb
                ) + _dtype_to_type_enum_list_recursor(typ.name_typ
                ) + _dtype_to_type_enum_list_recursor(qalb__kkk)
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
                fkw__ppmv = S._bodo_meta['type_metadata'][1]
                return _dtype_from_type_enum_list(fkw__ppmv)
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
        lgbcn__hnbi = S.dtype.unit
        if lgbcn__hnbi != 'ns':
            raise BodoError("Timezone-aware datetime data requires 'ns' units")
        bcqu__xzo = bodo.libs.pd_datetime_arr_ext.get_pytz_type_info(S.dtype.tz
            )
        return PandasDatetimeTZDtype(bcqu__xzo)
    try:
        return numpy_support.from_dtype(S.dtype)
    except:
        raise BodoError(
            f'data type {S.dtype} for column {S.name} not supported yet')


def _get_use_df_parent_obj_flag(builder, context, pyapi, parent_obj, n_cols):
    if n_cols is None:
        return context.get_constant(types.bool_, False)
    iio__yliiq = cgutils.is_not_null(builder, parent_obj)
    eqv__vatst = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with builder.if_then(iio__yliiq):
        rze__kvgum = pyapi.object_getattr_string(parent_obj, 'columns')
        ncu__jozta = pyapi.call_method(rze__kvgum, '__len__', ())
        builder.store(pyapi.long_as_longlong(ncu__jozta), eqv__vatst)
        pyapi.decref(ncu__jozta)
        pyapi.decref(rze__kvgum)
    use_parent_obj = builder.and_(iio__yliiq, builder.icmp_unsigned('==',
        builder.load(eqv__vatst), context.get_constant(types.int64, n_cols)))
    return use_parent_obj


def _get_df_columns_obj(c, builder, context, pyapi, df_typ, dataframe_payload):
    if df_typ.has_runtime_cols:
        gniy__msq = df_typ.runtime_colname_typ
        context.nrt.incref(builder, gniy__msq, dataframe_payload.columns)
        return pyapi.from_native_value(gniy__msq, dataframe_payload.columns,
            c.env_manager)
    if all(isinstance(c, int) for c in df_typ.columns):
        ufz__hmk = np.array(df_typ.columns, 'int64')
    elif all(isinstance(c, str) for c in df_typ.columns):
        ufz__hmk = pd.array(df_typ.columns, 'string')
    else:
        ufz__hmk = df_typ.columns
    tplee__ops = numba.typeof(ufz__hmk)
    pskv__zyqb = context.get_constant_generic(builder, tplee__ops, ufz__hmk)
    gelfp__yfh = pyapi.from_native_value(tplee__ops, pskv__zyqb, c.env_manager)
    return gelfp__yfh


def _create_initial_df_object(builder, context, pyapi, c, df_typ, obj,
    dataframe_payload, res, use_parent_obj):
    with c.builder.if_else(use_parent_obj) as (oroz__jzxrw, kldlo__mnh):
        with oroz__jzxrw:
            pyapi.incref(obj)
            rsd__bcds = context.insert_const_string(c.builder.module, 'numpy')
            tewjb__uabe = pyapi.import_module_noblock(rsd__bcds)
            if df_typ.has_runtime_cols:
                udtk__pgzs = 0
            else:
                udtk__pgzs = len(df_typ.columns)
            qstdg__dgy = pyapi.long_from_longlong(lir.Constant(lir.IntType(
                64), udtk__pgzs))
            dfp__nuxz = pyapi.call_method(tewjb__uabe, 'arange', (qstdg__dgy,))
            pyapi.object_setattr_string(obj, 'columns', dfp__nuxz)
            pyapi.decref(tewjb__uabe)
            pyapi.decref(dfp__nuxz)
            pyapi.decref(qstdg__dgy)
        with kldlo__mnh:
            context.nrt.incref(builder, df_typ.index, dataframe_payload.index)
            okkvy__cbq = c.pyapi.from_native_value(df_typ.index,
                dataframe_payload.index, c.env_manager)
            rsd__bcds = context.insert_const_string(c.builder.module, 'pandas')
            tewjb__uabe = pyapi.import_module_noblock(rsd__bcds)
            df_obj = pyapi.call_method(tewjb__uabe, 'DataFrame', (pyapi.
                borrow_none(), okkvy__cbq))
            pyapi.decref(tewjb__uabe)
            pyapi.decref(okkvy__cbq)
            builder.store(df_obj, res)


@box(DataFrameType)
def box_dataframe(typ, val, c):
    from bodo.hiframes.table import box_table
    context = c.context
    builder = c.builder
    pyapi = c.pyapi
    dataframe_payload = bodo.hiframes.pd_dataframe_ext.get_dataframe_payload(c
        .context, c.builder, typ, val)
    awnj__euuxk = cgutils.create_struct_proxy(typ)(context, builder, value=val)
    n_cols = len(typ.columns) if not typ.has_runtime_cols else None
    obj = awnj__euuxk.parent
    res = cgutils.alloca_once_value(builder, obj)
    use_parent_obj = _get_use_df_parent_obj_flag(builder, context, pyapi,
        obj, n_cols)
    _create_initial_df_object(builder, context, pyapi, c, typ, obj,
        dataframe_payload, res, use_parent_obj)
    if typ.is_table_format:
        liug__bnb = typ.table_type
        zzuyw__wolxp = builder.extract_value(dataframe_payload.data, 0)
        context.nrt.incref(builder, liug__bnb, zzuyw__wolxp)
        lhthz__xad = box_table(liug__bnb, zzuyw__wolxp, c, builder.not_(
            use_parent_obj))
        with builder.if_else(use_parent_obj) as (cqs__wnkt, spa__omo):
            with cqs__wnkt:
                rsa__izu = pyapi.object_getattr_string(lhthz__xad, 'arrays')
                vzdnd__ozqs = c.pyapi.make_none()
                if n_cols is None:
                    ncu__jozta = pyapi.call_method(rsa__izu, '__len__', ())
                    kiiq__ytaxi = pyapi.long_as_longlong(ncu__jozta)
                    pyapi.decref(ncu__jozta)
                else:
                    kiiq__ytaxi = context.get_constant(types.int64, n_cols)
                with cgutils.for_range(builder, kiiq__ytaxi) as vvzjr__aer:
                    i = vvzjr__aer.index
                    tmkn__nkm = pyapi.list_getitem(rsa__izu, i)
                    tfa__ixn = c.builder.icmp_unsigned('!=', tmkn__nkm,
                        vzdnd__ozqs)
                    with builder.if_then(tfa__ixn):
                        bah__fotw = pyapi.long_from_longlong(i)
                        df_obj = builder.load(res)
                        pyapi.object_setitem(df_obj, bah__fotw, tmkn__nkm)
                        pyapi.decref(bah__fotw)
                pyapi.decref(rsa__izu)
                pyapi.decref(vzdnd__ozqs)
            with spa__omo:
                df_obj = builder.load(res)
                okkvy__cbq = pyapi.object_getattr_string(df_obj, 'index')
                mlg__oodyr = c.pyapi.call_method(lhthz__xad, 'to_pandas', (
                    okkvy__cbq,))
                builder.store(mlg__oodyr, res)
                pyapi.decref(df_obj)
                pyapi.decref(okkvy__cbq)
        pyapi.decref(lhthz__xad)
    else:
        xww__iyvlo = [builder.extract_value(dataframe_payload.data, i) for
            i in range(n_cols)]
        iwo__knmd = typ.data
        for i, llwd__bzse, ofyyx__dydsz in zip(range(n_cols), xww__iyvlo,
            iwo__knmd):
            tfyas__klo = cgutils.alloca_once_value(builder, llwd__bzse)
            dvwo__tqz = cgutils.alloca_once_value(builder, context.
                get_constant_null(ofyyx__dydsz))
            tfa__ixn = builder.not_(is_ll_eq(builder, tfyas__klo, dvwo__tqz))
            kxr__fsu = builder.or_(builder.not_(use_parent_obj), builder.
                and_(use_parent_obj, tfa__ixn))
            with builder.if_then(kxr__fsu):
                bah__fotw = pyapi.long_from_longlong(context.get_constant(
                    types.int64, i))
                context.nrt.incref(builder, ofyyx__dydsz, llwd__bzse)
                arr_obj = pyapi.from_native_value(ofyyx__dydsz, llwd__bzse,
                    c.env_manager)
                df_obj = builder.load(res)
                pyapi.object_setitem(df_obj, bah__fotw, arr_obj)
                pyapi.decref(arr_obj)
                pyapi.decref(bah__fotw)
    df_obj = builder.load(res)
    gelfp__yfh = _get_df_columns_obj(c, builder, context, pyapi, typ,
        dataframe_payload)
    pyapi.object_setattr_string(df_obj, 'columns', gelfp__yfh)
    pyapi.decref(gelfp__yfh)
    _set_bodo_meta_dataframe(c, df_obj, typ)
    c.context.nrt.decref(c.builder, typ, val)
    return df_obj


def get_df_obj_column_codegen(context, builder, pyapi, df_obj, col_ind,
    data_typ):
    vzdnd__ozqs = pyapi.borrow_none()
    evsg__ysmlh = pyapi.unserialize(pyapi.serialize_object(slice))
    tditc__bzm = pyapi.call_function_objargs(evsg__ysmlh, [vzdnd__ozqs])
    wur__lmujt = pyapi.long_from_longlong(col_ind)
    ggj__kvahq = pyapi.tuple_pack([tditc__bzm, wur__lmujt])
    ysr__afm = pyapi.object_getattr_string(df_obj, 'iloc')
    flak__yomp = pyapi.object_getitem(ysr__afm, ggj__kvahq)
    if isinstance(data_typ, bodo.DatetimeArrayType):
        byppm__roe = pyapi.object_getattr_string(flak__yomp, 'array')
    else:
        byppm__roe = pyapi.object_getattr_string(flak__yomp, 'values')
    if isinstance(data_typ, types.Array):
        lgy__ynfd = context.insert_const_string(builder.module, 'numpy')
        hdia__icaq = pyapi.import_module_noblock(lgy__ynfd)
        arr_obj = pyapi.call_method(hdia__icaq, 'ascontiguousarray', (
            byppm__roe,))
        pyapi.decref(byppm__roe)
        pyapi.decref(hdia__icaq)
    else:
        arr_obj = byppm__roe
    pyapi.decref(evsg__ysmlh)
    pyapi.decref(tditc__bzm)
    pyapi.decref(wur__lmujt)
    pyapi.decref(ggj__kvahq)
    pyapi.decref(ysr__afm)
    pyapi.decref(flak__yomp)
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
        awnj__euuxk = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        arr_obj = get_df_obj_column_codegen(context, builder, pyapi,
            awnj__euuxk.parent, args[1], data_typ)
        qczo__dbufb = _unbox_series_data(data_typ.dtype, data_typ, arr_obj, c)
        c.pyapi.decref(arr_obj)
        dataframe_payload = (bodo.hiframes.pd_dataframe_ext.
            get_dataframe_payload(c.context, c.builder, df_typ, args[0]))
        if df_typ.is_table_format:
            zzuyw__wolxp = cgutils.create_struct_proxy(df_typ.table_type)(c
                .context, c.builder, builder.extract_value(
                dataframe_payload.data, 0))
            gdey__kltk = df_typ.table_type.type_to_blk[data_typ]
            eez__jzdz = getattr(zzuyw__wolxp, f'block_{gdey__kltk}')
            cwqja__wjnzq = ListInstance(c.context, c.builder, types.List(
                data_typ), eez__jzdz)
            nnfpm__ykh = context.get_constant(types.int64, df_typ.
                table_type.block_offsets[col_ind])
            cwqja__wjnzq.inititem(nnfpm__ykh, qczo__dbufb.value, incref=False)
        else:
            dataframe_payload.data = builder.insert_value(dataframe_payload
                .data, qczo__dbufb.value, col_ind)
        aejm__hbzuf = DataFramePayloadType(df_typ)
        odmlj__pitnk = context.nrt.meminfo_data(builder, awnj__euuxk.meminfo)
        oayy__knnmu = context.get_value_type(aejm__hbzuf).as_pointer()
        odmlj__pitnk = builder.bitcast(odmlj__pitnk, oayy__knnmu)
        builder.store(dataframe_payload._getvalue(), odmlj__pitnk)
    return signature(types.none, df, i), codegen


@numba.njit
def unbox_col_if_needed(df, i):
    if bodo.hiframes.pd_dataframe_ext.has_parent(df
        ) and bodo.hiframes.pd_dataframe_ext._column_needs_unboxing(df, i):
        bodo.hiframes.boxing.unbox_dataframe_column(df, i)


@unbox(SeriesType)
def unbox_series(typ, val, c):
    if isinstance(typ.data, DatetimeArrayType):
        byppm__roe = c.pyapi.object_getattr_string(val, 'array')
    else:
        byppm__roe = c.pyapi.object_getattr_string(val, 'values')
    if isinstance(typ.data, types.Array):
        lgy__ynfd = c.context.insert_const_string(c.builder.module, 'numpy')
        hdia__icaq = c.pyapi.import_module_noblock(lgy__ynfd)
        arr_obj = c.pyapi.call_method(hdia__icaq, 'ascontiguousarray', (
            byppm__roe,))
        c.pyapi.decref(byppm__roe)
        c.pyapi.decref(hdia__icaq)
    else:
        arr_obj = byppm__roe
    uvi__xbfxz = _unbox_series_data(typ.dtype, typ.data, arr_obj, c).value
    okkvy__cbq = c.pyapi.object_getattr_string(val, 'index')
    jfdw__duozj = c.pyapi.to_native_value(typ.index, okkvy__cbq).value
    wmi__muc = c.pyapi.object_getattr_string(val, 'name')
    rzfby__xwiyc = c.pyapi.to_native_value(typ.name_typ, wmi__muc).value
    ehors__okk = bodo.hiframes.pd_series_ext.construct_series(c.context, c.
        builder, typ, uvi__xbfxz, jfdw__duozj, rzfby__xwiyc)
    c.pyapi.decref(arr_obj)
    c.pyapi.decref(okkvy__cbq)
    c.pyapi.decref(wmi__muc)
    return NativeValue(ehors__okk)


def _unbox_series_data(dtype, data_typ, arr_obj, c):
    if data_typ == string_array_split_view_type:
        pbrn__qax = c.context.make_helper(c.builder,
            string_array_split_view_type)
        return NativeValue(pbrn__qax._getvalue())
    return c.pyapi.to_native_value(data_typ, arr_obj)


@box(HeterogeneousSeriesType)
@box(SeriesType)
def box_series(typ, val, c):
    rsd__bcds = c.context.insert_const_string(c.builder.module, 'pandas')
    kpc__mqlj = c.pyapi.import_module_noblock(rsd__bcds)
    std__sbc = bodo.hiframes.pd_series_ext.get_series_payload(c.context, c.
        builder, typ, val)
    c.context.nrt.incref(c.builder, typ.data, std__sbc.data)
    c.context.nrt.incref(c.builder, typ.index, std__sbc.index)
    c.context.nrt.incref(c.builder, typ.name_typ, std__sbc.name)
    arr_obj = c.pyapi.from_native_value(typ.data, std__sbc.data, c.env_manager)
    okkvy__cbq = c.pyapi.from_native_value(typ.index, std__sbc.index, c.
        env_manager)
    wmi__muc = c.pyapi.from_native_value(typ.name_typ, std__sbc.name, c.
        env_manager)
    if isinstance(typ, HeterogeneousSeriesType) and isinstance(typ.data,
        bodo.NullableTupleType):
        dtype = c.pyapi.unserialize(c.pyapi.serialize_object(object))
    else:
        dtype = c.pyapi.make_none()
    res = c.pyapi.call_method(kpc__mqlj, 'Series', (arr_obj, okkvy__cbq,
        dtype, wmi__muc))
    c.pyapi.decref(arr_obj)
    c.pyapi.decref(okkvy__cbq)
    c.pyapi.decref(wmi__muc)
    if isinstance(typ, HeterogeneousSeriesType) and isinstance(typ.data,
        bodo.NullableTupleType):
        c.pyapi.decref(dtype)
    _set_bodo_meta_series(res, c, typ)
    c.pyapi.decref(kpc__mqlj)
    c.context.nrt.decref(c.builder, typ, val)
    return res


def type_enum_list_to_py_list_obj(pyapi, context, builder, env_manager,
    typ_list):
    hsaap__evj = []
    for tmo__zlxa in typ_list:
        if isinstance(tmo__zlxa, int) and not isinstance(tmo__zlxa, bool):
            aprce__jqyf = pyapi.long_from_longlong(lir.Constant(lir.IntType
                (64), tmo__zlxa))
        else:
            hly__zikd = numba.typeof(tmo__zlxa)
            qqyag__mxsrm = context.get_constant_generic(builder, hly__zikd,
                tmo__zlxa)
            aprce__jqyf = pyapi.from_native_value(hly__zikd, qqyag__mxsrm,
                env_manager)
        hsaap__evj.append(aprce__jqyf)
    fzi__rypao = pyapi.list_pack(hsaap__evj)
    for val in hsaap__evj:
        pyapi.decref(val)
    return fzi__rypao


def _set_bodo_meta_dataframe(c, obj, typ):
    pyapi = c.pyapi
    context = c.context
    builder = c.builder
    tjez__ozxut = not typ.has_runtime_cols and (not typ.is_table_format or 
        len(typ.columns) < TABLE_FORMAT_THRESHOLD)
    wgtg__txyy = 2 if tjez__ozxut else 1
    lvf__lsjxp = pyapi.dict_new(wgtg__txyy)
    rrvh__fqj = pyapi.long_from_longlong(lir.Constant(lir.IntType(64), typ.
        dist.value))
    pyapi.dict_setitem_string(lvf__lsjxp, 'dist', rrvh__fqj)
    pyapi.decref(rrvh__fqj)
    if tjez__ozxut:
        ijhm__lwmjy = _dtype_to_type_enum_list(typ.index)
        if ijhm__lwmjy != None:
            ula__lbut = type_enum_list_to_py_list_obj(pyapi, context,
                builder, c.env_manager, ijhm__lwmjy)
        else:
            ula__lbut = pyapi.make_none()
        kktxc__neqir = []
        for dtype in typ.data:
            typ_list = _dtype_to_type_enum_list(dtype)
            if typ_list != None:
                fzi__rypao = type_enum_list_to_py_list_obj(pyapi, context,
                    builder, c.env_manager, typ_list)
            else:
                fzi__rypao = pyapi.make_none()
            kktxc__neqir.append(fzi__rypao)
        agta__vbax = pyapi.list_pack(kktxc__neqir)
        wfp__hrp = pyapi.list_pack([ula__lbut, agta__vbax])
        for val in kktxc__neqir:
            pyapi.decref(val)
        pyapi.dict_setitem_string(lvf__lsjxp, 'type_metadata', wfp__hrp)
    pyapi.object_setattr_string(obj, '_bodo_meta', lvf__lsjxp)
    pyapi.decref(lvf__lsjxp)


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
    lvf__lsjxp = pyapi.dict_new(2)
    rrvh__fqj = pyapi.long_from_longlong(lir.Constant(lir.IntType(64), typ.
        dist.value))
    ijhm__lwmjy = _dtype_to_type_enum_list(typ.index)
    if ijhm__lwmjy != None:
        ula__lbut = type_enum_list_to_py_list_obj(pyapi, context, builder,
            c.env_manager, ijhm__lwmjy)
    else:
        ula__lbut = pyapi.make_none()
    dtype = get_series_dtype_handle_null_int_and_hetrogenous(typ)
    if dtype != None:
        typ_list = _dtype_to_type_enum_list(dtype)
        if typ_list != None:
            ozttz__hegiq = type_enum_list_to_py_list_obj(pyapi, context,
                builder, c.env_manager, typ_list)
        else:
            ozttz__hegiq = pyapi.make_none()
    else:
        ozttz__hegiq = pyapi.make_none()
    lsoa__awct = pyapi.list_pack([ula__lbut, ozttz__hegiq])
    pyapi.dict_setitem_string(lvf__lsjxp, 'type_metadata', lsoa__awct)
    pyapi.decref(lsoa__awct)
    pyapi.dict_setitem_string(lvf__lsjxp, 'dist', rrvh__fqj)
    pyapi.object_setattr_string(obj, '_bodo_meta', lvf__lsjxp)
    pyapi.decref(lvf__lsjxp)
    pyapi.decref(rrvh__fqj)


@typeof_impl.register(np.ndarray)
def _typeof_ndarray(val, c):
    try:
        dtype = numba.np.numpy_support.from_dtype(val.dtype)
    except NotImplementedError as jcbgz__tijd:
        dtype = types.pyobject
    if dtype == types.pyobject:
        return _infer_ndarray_obj_dtype(val)
    gipcd__sdn = numba.np.numpy_support.map_layout(val)
    xajkm__knny = not val.flags.writeable
    return types.Array(dtype, val.ndim, gipcd__sdn, readonly=xajkm__knny)


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
    yqrx__ickgn = val[i]
    if isinstance(yqrx__ickgn, str):
        return (bodo.dict_str_arr_type if _use_dict_str_type else
            string_array_type)
    elif isinstance(yqrx__ickgn, bytes):
        return binary_array_type
    elif isinstance(yqrx__ickgn, bool):
        return bodo.libs.bool_arr_ext.boolean_array
    elif isinstance(yqrx__ickgn, (int, np.int32, np.int64)):
        return bodo.libs.int_arr_ext.IntegerArrayType(numba.typeof(yqrx__ickgn)
            )
    elif isinstance(yqrx__ickgn, (dict, Dict)) and all(isinstance(
        aczu__xyyvo, str) for aczu__xyyvo in yqrx__ickgn.keys()):
        lziyn__xjkp = tuple(yqrx__ickgn.keys())
        rcivw__ebsx = tuple(_get_struct_value_arr_type(v) for v in
            yqrx__ickgn.values())
        return StructArrayType(rcivw__ebsx, lziyn__xjkp)
    elif isinstance(yqrx__ickgn, (dict, Dict)):
        jjdhe__tsu = numba.typeof(_value_to_array(list(yqrx__ickgn.keys())))
        iriav__xnfxj = numba.typeof(_value_to_array(list(yqrx__ickgn.values()))
            )
        jjdhe__tsu = to_str_arr_if_dict_array(jjdhe__tsu)
        iriav__xnfxj = to_str_arr_if_dict_array(iriav__xnfxj)
        return MapArrayType(jjdhe__tsu, iriav__xnfxj)
    elif isinstance(yqrx__ickgn, tuple):
        rcivw__ebsx = tuple(_get_struct_value_arr_type(v) for v in yqrx__ickgn)
        return TupleArrayType(rcivw__ebsx)
    if isinstance(yqrx__ickgn, (list, np.ndarray, pd.arrays.BooleanArray,
        pd.arrays.IntegerArray, pd.arrays.StringArray)):
        if isinstance(yqrx__ickgn, list):
            yqrx__ickgn = _value_to_array(yqrx__ickgn)
        jrid__tbrio = numba.typeof(yqrx__ickgn)
        jrid__tbrio = to_str_arr_if_dict_array(jrid__tbrio)
        return ArrayItemArrayType(jrid__tbrio)
    if isinstance(yqrx__ickgn, datetime.date):
        return datetime_date_array_type
    if isinstance(yqrx__ickgn, datetime.timedelta):
        return datetime_timedelta_array_type
    if isinstance(yqrx__ickgn, decimal.Decimal):
        return DecimalArrayType(38, 18)
    raise BodoError(f'Unsupported object array with first value: {yqrx__ickgn}'
        )


def _value_to_array(val):
    assert isinstance(val, (list, dict, Dict))
    if isinstance(val, (dict, Dict)):
        val = dict(val)
        return np.array([val], np.object_)
    fhymi__roysy = val.copy()
    fhymi__roysy.append(None)
    llwd__bzse = np.array(fhymi__roysy, np.object_)
    if len(val) and isinstance(val[0], float):
        llwd__bzse = np.array(val, np.float64)
    return llwd__bzse


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
    ofyyx__dydsz = dtype_to_array_type(numba.typeof(v))
    if isinstance(v, (int, bool)):
        ofyyx__dydsz = to_nullable_type(ofyyx__dydsz)
    return ofyyx__dydsz
