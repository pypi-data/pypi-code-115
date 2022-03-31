"""
Collection of utility functions. Needs to be refactored in separate files.
"""
import hashlib
import inspect
import keyword
import re
import warnings
from enum import Enum
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, ir, ir_utils, types
from numba.core.imputils import lower_builtin, lower_constant
from numba.core.ir_utils import find_callname, find_const, get_definition, guard, mk_unique_var, require
from numba.core.typing import signature
from numba.core.typing.templates import AbstractTemplate, infer_global
from numba.extending import intrinsic, overload
from numba.np.arrayobj import get_itemsize, make_array, populate_array
import bodo
from bodo.libs.binary_arr_ext import bytes_type
from bodo.libs.bool_arr_ext import boolean_array
from bodo.libs.decimal_arr_ext import DecimalArrayType
from bodo.libs.int_arr_ext import IntegerArrayType
from bodo.libs.str_arr_ext import num_total_chars, pre_alloc_string_array, string_array_type
from bodo.libs.str_ext import string_type
from bodo.utils.cg_helpers import is_ll_eq
from bodo.utils.typing import NOT_CONSTANT, BodoError, BodoWarning, MetaType, is_str_arr_type
int128_type = types.Integer('int128', 128)


class CTypeEnum(Enum):
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
    Date = 13
    Datetime = 14
    Timedelta = 15
    Int128 = 16
    LIST = 18
    STRUCT = 19
    BINARY = 20


_numba_to_c_type_map = {types.int8: CTypeEnum.Int8.value, types.uint8:
    CTypeEnum.UInt8.value, types.int32: CTypeEnum.Int32.value, types.uint32:
    CTypeEnum.UInt32.value, types.int64: CTypeEnum.Int64.value, types.
    uint64: CTypeEnum.UInt64.value, types.float32: CTypeEnum.Float32.value,
    types.float64: CTypeEnum.Float64.value, types.NPDatetime('ns'):
    CTypeEnum.Datetime.value, types.NPTimedelta('ns'): CTypeEnum.Timedelta.
    value, types.bool_: CTypeEnum.Bool.value, types.int16: CTypeEnum.Int16.
    value, types.uint16: CTypeEnum.UInt16.value, int128_type: CTypeEnum.
    Int128.value}
numba.core.errors.error_extras = {'unsupported_error': '', 'typing': '',
    'reportable': '', 'interpreter': '', 'constant_inference': ''}
np_alloc_callnames = 'empty', 'zeros', 'ones', 'full'
CONST_DICT_SLOW_WARN_THRESHOLD = 100
CONST_LIST_SLOW_WARN_THRESHOLD = 100000


def unliteral_all(args):
    return tuple(types.unliteral(a) for a in args)


def get_constant(func_ir, var, default=NOT_CONSTANT):
    dae__alx = guard(get_definition, func_ir, var)
    if dae__alx is None:
        return default
    if isinstance(dae__alx, ir.Const):
        return dae__alx.value
    if isinstance(dae__alx, ir.Var):
        return get_constant(func_ir, dae__alx, default)
    return default


def numba_to_c_type(t):
    if isinstance(t, bodo.libs.decimal_arr_ext.Decimal128Type):
        return CTypeEnum.Decimal.value
    if t == bodo.hiframes.datetime_date_ext.datetime_date_type:
        return CTypeEnum.Date.value
    return _numba_to_c_type_map[t]


def is_alloc_callname(func_name, mod_name):
    return isinstance(mod_name, str) and (mod_name == 'numpy' and func_name in
        np_alloc_callnames or func_name == 'empty_inferred' and mod_name in
        ('numba.extending', 'numba.np.unsafe.ndarray') or func_name ==
        'pre_alloc_string_array' and mod_name == 'bodo.libs.str_arr_ext' or
        func_name == 'pre_alloc_binary_array' and mod_name ==
        'bodo.libs.binary_arr_ext' or func_name ==
        'alloc_random_access_string_array' and mod_name ==
        'bodo.libs.str_ext' or func_name == 'pre_alloc_array_item_array' and
        mod_name == 'bodo.libs.array_item_arr_ext' or func_name ==
        'pre_alloc_struct_array' and mod_name == 'bodo.libs.struct_arr_ext' or
        func_name == 'pre_alloc_map_array' and mod_name ==
        'bodo.libs.map_arr_ext' or func_name == 'pre_alloc_tuple_array' and
        mod_name == 'bodo.libs.tuple_arr_ext' or func_name ==
        'alloc_bool_array' and mod_name == 'bodo.libs.bool_arr_ext' or 
        func_name == 'alloc_int_array' and mod_name ==
        'bodo.libs.int_arr_ext' or func_name == 'alloc_datetime_date_array' and
        mod_name == 'bodo.hiframes.datetime_date_ext' or func_name ==
        'alloc_datetime_timedelta_array' and mod_name ==
        'bodo.hiframes.datetime_timedelta_ext' or func_name ==
        'alloc_decimal_array' and mod_name == 'bodo.libs.decimal_arr_ext' or
        func_name == 'alloc_categorical_array' and mod_name ==
        'bodo.hiframes.pd_categorical_ext' or func_name == 'gen_na_array' and
        mod_name == 'bodo.libs.array_kernels')


def find_build_tuple(func_ir, var):
    require(isinstance(var, (ir.Var, str)))
    zsqoh__kft = get_definition(func_ir, var)
    require(isinstance(zsqoh__kft, ir.Expr))
    require(zsqoh__kft.op == 'build_tuple')
    return zsqoh__kft.items


def cprint(*s):
    print(*s)


@infer_global(cprint)
class CprintInfer(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        return signature(types.none, *unliteral_all(args))


typ_to_format = {types.int32: 'd', types.uint32: 'u', types.int64: 'lld',
    types.uint64: 'llu', types.float32: 'f', types.float64: 'lf', types.
    voidptr: 's'}


@lower_builtin(cprint, types.VarArg(types.Any))
def cprint_lower(context, builder, sig, args):
    for bdm__nui, val in enumerate(args):
        typ = sig.args[bdm__nui]
        if isinstance(typ, types.ArrayCTypes):
            cgutils.printf(builder, '%p ', val)
            continue
        zti__byr = typ_to_format[typ]
        cgutils.printf(builder, '%{} '.format(zti__byr), val)
    cgutils.printf(builder, '\n')
    return context.get_dummy_value()


def is_whole_slice(typemap, func_ir, var, accept_stride=False):
    require(typemap[var.name] == types.slice2_type or accept_stride and 
        typemap[var.name] == types.slice3_type)
    ysmgh__dfob = get_definition(func_ir, var)
    require(isinstance(ysmgh__dfob, ir.Expr) and ysmgh__dfob.op == 'call')
    assert len(ysmgh__dfob.args) == 2 or accept_stride and len(ysmgh__dfob.args
        ) == 3
    assert find_callname(func_ir, ysmgh__dfob) == ('slice', 'builtins')
    rcbw__gzln = get_definition(func_ir, ysmgh__dfob.args[0])
    rvr__lat = get_definition(func_ir, ysmgh__dfob.args[1])
    require(isinstance(rcbw__gzln, ir.Const) and rcbw__gzln.value == None)
    require(isinstance(rvr__lat, ir.Const) and rvr__lat.value == None)
    return True


def is_slice_equiv_arr(arr_var, index_var, func_ir, equiv_set,
    accept_stride=False):
    ncg__qab = get_definition(func_ir, index_var)
    require(find_callname(func_ir, ncg__qab) == ('slice', 'builtins'))
    require(len(ncg__qab.args) in (2, 3))
    require(find_const(func_ir, ncg__qab.args[0]) in (0, None))
    require(equiv_set.is_equiv(ncg__qab.args[1], arr_var.name + '#0'))
    require(accept_stride or len(ncg__qab.args) == 2 or find_const(func_ir,
        ncg__qab.args[2]) == 1)
    return True


def get_slice_step(typemap, func_ir, var):
    require(typemap[var.name] == types.slice3_type)
    ysmgh__dfob = get_definition(func_ir, var)
    require(isinstance(ysmgh__dfob, ir.Expr) and ysmgh__dfob.op == 'call')
    assert len(ysmgh__dfob.args) == 3
    return ysmgh__dfob.args[2]


def is_array_typ(var_typ, include_index_series=True):
    return is_np_array_typ(var_typ) or var_typ in (string_array_type, bodo.
        binary_array_type, bodo.dict_str_arr_type, bodo.hiframes.split_impl
        .string_array_split_view_type, bodo.hiframes.datetime_date_ext.
        datetime_date_array_type, bodo.hiframes.datetime_timedelta_ext.
        datetime_timedelta_array_type, boolean_array, bodo.libs.str_ext.
        random_access_string_array) or isinstance(var_typ, (
        IntegerArrayType, bodo.libs.decimal_arr_ext.DecimalArrayType, bodo.
        hiframes.pd_categorical_ext.CategoricalArrayType, bodo.libs.
        array_item_arr_ext.ArrayItemArrayType, bodo.libs.struct_arr_ext.
        StructArrayType, bodo.libs.interval_arr_ext.IntervalArrayType, bodo
        .libs.tuple_arr_ext.TupleArrayType, bodo.libs.map_arr_ext.
        MapArrayType, bodo.libs.csr_matrix_ext.CSRMatrixType, bodo.
        DatetimeArrayType)) or include_index_series and (isinstance(var_typ,
        (bodo.hiframes.pd_series_ext.SeriesType, bodo.hiframes.
        pd_multi_index_ext.MultiIndexType)) or bodo.hiframes.pd_index_ext.
        is_pd_index_type(var_typ))


def is_np_array_typ(var_typ):
    return isinstance(var_typ, types.Array)


def is_distributable_typ(var_typ):
    return is_array_typ(var_typ) or isinstance(var_typ, bodo.hiframes.table
        .TableType) or isinstance(var_typ, bodo.hiframes.pd_dataframe_ext.
        DataFrameType) or isinstance(var_typ, types.List
        ) and is_distributable_typ(var_typ.dtype) or isinstance(var_typ,
        types.DictType) and is_distributable_typ(var_typ.value_type)


def is_distributable_tuple_typ(var_typ):
    return isinstance(var_typ, types.BaseTuple) and any(
        is_distributable_typ(t) or is_distributable_tuple_typ(t) for t in
        var_typ.types) or isinstance(var_typ, types.List
        ) and is_distributable_tuple_typ(var_typ.dtype) or isinstance(var_typ,
        types.DictType) and is_distributable_tuple_typ(var_typ.value_type
        ) or isinstance(var_typ, types.iterators.EnumerateType) and (
        is_distributable_typ(var_typ.yield_type[1]) or
        is_distributable_tuple_typ(var_typ.yield_type[1]))


@numba.generated_jit(nopython=True, cache=True)
def build_set_seen_na(A):

    def impl(A):
        s = dict()
        cxg__qdyjq = False
        for bdm__nui in range(len(A)):
            if bodo.libs.array_kernels.isna(A, bdm__nui):
                cxg__qdyjq = True
                continue
            s[A[bdm__nui]] = 0
        return s, cxg__qdyjq
    return impl


def empty_like_type(n, arr):
    return np.empty(n, arr.dtype)


@overload(empty_like_type, no_unliteral=True)
def empty_like_type_overload(n, arr):
    if isinstance(arr, bodo.hiframes.pd_categorical_ext.CategoricalArrayType):
        return (lambda n, arr: bodo.hiframes.pd_categorical_ext.
            alloc_categorical_array(n, arr.dtype))
    if isinstance(arr, types.Array):
        return lambda n, arr: np.empty(n, arr.dtype)
    if isinstance(arr, types.List) and arr.dtype == string_type:

        def empty_like_type_str_list(n, arr):
            return [''] * n
        return empty_like_type_str_list
    if isinstance(arr, types.List) and arr.dtype == bytes_type:

        def empty_like_type_binary_list(n, arr):
            return [b''] * n
        return empty_like_type_binary_list
    if isinstance(arr, IntegerArrayType):
        jlzk__zwsrv = arr.dtype

        def empty_like_type_int_arr(n, arr):
            return bodo.libs.int_arr_ext.alloc_int_array(n, jlzk__zwsrv)
        return empty_like_type_int_arr
    if arr == boolean_array:

        def empty_like_type_bool_arr(n, arr):
            return bodo.libs.bool_arr_ext.alloc_bool_array(n)
        return empty_like_type_bool_arr
    if arr == bodo.hiframes.datetime_date_ext.datetime_date_array_type:

        def empty_like_type_datetime_date_arr(n, arr):
            return bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(n)
        return empty_like_type_datetime_date_arr
    if (arr == bodo.hiframes.datetime_timedelta_ext.
        datetime_timedelta_array_type):

        def empty_like_type_datetime_timedelta_arr(n, arr):
            return (bodo.hiframes.datetime_timedelta_ext.
                alloc_datetime_timedelta_array(n))
        return empty_like_type_datetime_timedelta_arr
    if isinstance(arr, bodo.libs.decimal_arr_ext.DecimalArrayType):
        precision = arr.precision
        scale = arr.scale

        def empty_like_type_decimal_arr(n, arr):
            return bodo.libs.decimal_arr_ext.alloc_decimal_array(n,
                precision, scale)
        return empty_like_type_decimal_arr
    assert arr == string_array_type

    def empty_like_type_str_arr(n, arr):
        hqq__tmcg = 20
        if len(arr) != 0:
            hqq__tmcg = num_total_chars(arr) // len(arr)
        return pre_alloc_string_array(n, n * hqq__tmcg)
    return empty_like_type_str_arr


def _empty_nd_impl(context, builder, arrtype, shapes):
    iljf__lda = make_array(arrtype)
    htec__djbns = iljf__lda(context, builder)
    lgto__axns = context.get_data_type(arrtype.dtype)
    lwftn__lfbv = context.get_constant(types.intp, get_itemsize(context,
        arrtype))
    fwu__hqvc = context.get_constant(types.intp, 1)
    hmi__yewf = lir.Constant(lir.IntType(1), 0)
    for s in shapes:
        fxw__dffs = builder.smul_with_overflow(fwu__hqvc, s)
        fwu__hqvc = builder.extract_value(fxw__dffs, 0)
        hmi__yewf = builder.or_(hmi__yewf, builder.extract_value(fxw__dffs, 1))
    if arrtype.ndim == 0:
        hms__hnlo = ()
    elif arrtype.layout == 'C':
        hms__hnlo = [lwftn__lfbv]
        for jgctl__dkuel in reversed(shapes[1:]):
            hms__hnlo.append(builder.mul(hms__hnlo[-1], jgctl__dkuel))
        hms__hnlo = tuple(reversed(hms__hnlo))
    elif arrtype.layout == 'F':
        hms__hnlo = [lwftn__lfbv]
        for jgctl__dkuel in shapes[:-1]:
            hms__hnlo.append(builder.mul(hms__hnlo[-1], jgctl__dkuel))
        hms__hnlo = tuple(hms__hnlo)
    else:
        raise NotImplementedError(
            "Don't know how to allocate array with layout '{0}'.".format(
            arrtype.layout))
    eriex__kcl = builder.smul_with_overflow(fwu__hqvc, lwftn__lfbv)
    dfmo__hpi = builder.extract_value(eriex__kcl, 0)
    hmi__yewf = builder.or_(hmi__yewf, builder.extract_value(eriex__kcl, 1))
    with builder.if_then(hmi__yewf, likely=False):
        cgutils.printf(builder,
            'array is too big; `arr.size * arr.dtype.itemsize` is larger than the maximum possible size.'
            )
    dtype = arrtype.dtype
    gjlqx__rzi = context.get_preferred_array_alignment(dtype)
    vvp__odum = context.get_constant(types.uint32, gjlqx__rzi)
    wbu__uguv = context.nrt.meminfo_alloc_aligned(builder, size=dfmo__hpi,
        align=vvp__odum)
    data = context.nrt.meminfo_data(builder, wbu__uguv)
    xlh__cne = context.get_value_type(types.intp)
    boqsb__qlz = cgutils.pack_array(builder, shapes, ty=xlh__cne)
    qkj__cdxgc = cgutils.pack_array(builder, hms__hnlo, ty=xlh__cne)
    populate_array(htec__djbns, data=builder.bitcast(data, lgto__axns.
        as_pointer()), shape=boqsb__qlz, strides=qkj__cdxgc, itemsize=
        lwftn__lfbv, meminfo=wbu__uguv)
    return htec__djbns


if bodo.numba_compat._check_numba_change:
    lines = inspect.getsource(numba.np.arrayobj._empty_nd_impl)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b6a998927680caa35917a553c79704e9d813d8f1873d83a5f8513837c159fa29':
        warnings.warn('numba.np.arrayobj._empty_nd_impl has changed')


def alloc_arr_tup(n, arr_tup, init_vals=()):
    yrag__ubwf = []
    for xad__zvguy in arr_tup:
        yrag__ubwf.append(np.empty(n, xad__zvguy.dtype))
    return tuple(yrag__ubwf)


@overload(alloc_arr_tup, no_unliteral=True)
def alloc_arr_tup_overload(n, data, init_vals=()):
    gyrkq__xdqk = data.count
    orhes__ydjsq = ','.join(['empty_like_type(n, data[{}])'.format(bdm__nui
        ) for bdm__nui in range(gyrkq__xdqk)])
    if init_vals != ():
        orhes__ydjsq = ','.join([
            'np.full(n, init_vals[{}], data[{}].dtype)'.format(bdm__nui,
            bdm__nui) for bdm__nui in range(gyrkq__xdqk)])
    mpda__aksmt = 'def f(n, data, init_vals=()):\n'
    mpda__aksmt += '  return ({}{})\n'.format(orhes__ydjsq, ',' if 
        gyrkq__xdqk == 1 else '')
    auf__oyynw = {}
    exec(mpda__aksmt, {'empty_like_type': empty_like_type, 'np': np},
        auf__oyynw)
    qcex__hsua = auf__oyynw['f']
    return qcex__hsua


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def tuple_to_scalar(n):
    if isinstance(n, types.BaseTuple) and len(n.types) == 1:
        return lambda n: n[0]
    return lambda n: n


def alloc_type(n, t, s=None):
    return np.empty(n, t.dtype)


@overload(alloc_type)
def overload_alloc_type(n, t, s=None):
    typ = t.instance_type if isinstance(t, types.TypeRef) else t
    if is_str_arr_type(typ):
        return (lambda n, t, s=None: bodo.libs.str_arr_ext.
            pre_alloc_string_array(n, s[0]))
    if typ == bodo.binary_array_type:
        return (lambda n, t, s=None: bodo.libs.binary_arr_ext.
            pre_alloc_binary_array(n, s[0]))
    if isinstance(typ, bodo.libs.array_item_arr_ext.ArrayItemArrayType):
        dtype = typ.dtype
        return (lambda n, t, s=None: bodo.libs.array_item_arr_ext.
            pre_alloc_array_item_array(n, s, dtype))
    if isinstance(typ, bodo.libs.struct_arr_ext.StructArrayType):
        dtypes = typ.data
        names = typ.names
        return (lambda n, t, s=None: bodo.libs.struct_arr_ext.
            pre_alloc_struct_array(n, s, dtypes, names))
    if isinstance(typ, bodo.libs.map_arr_ext.MapArrayType):
        struct_typ = bodo.libs.struct_arr_ext.StructArrayType((typ.
            key_arr_type, typ.value_arr_type), ('key', 'value'))
        return lambda n, t, s=None: bodo.libs.map_arr_ext.pre_alloc_map_array(n
            , s, struct_typ)
    if isinstance(typ, bodo.libs.tuple_arr_ext.TupleArrayType):
        dtypes = typ.data
        return (lambda n, t, s=None: bodo.libs.tuple_arr_ext.
            pre_alloc_tuple_array(n, s, dtypes))
    if isinstance(typ, bodo.hiframes.pd_categorical_ext.CategoricalArrayType):
        if isinstance(t, types.TypeRef):
            if typ.dtype.categories is None:
                raise BodoError(
                    'UDFs or Groupbys that return Categorical values must have categories known at compile time.'
                    )
            is_ordered = typ.dtype.ordered
            int_type = typ.dtype.int_type
            new_cats_arr = pd.CategoricalDtype(typ.dtype.categories, is_ordered
                ).categories.values
            new_cats_tup = MetaType(tuple(new_cats_arr))
            return (lambda n, t, s=None: bodo.hiframes.pd_categorical_ext.
                alloc_categorical_array(n, bodo.hiframes.pd_categorical_ext
                .init_cat_dtype(bodo.utils.conversion.index_from_array(
                new_cats_arr), is_ordered, int_type, new_cats_tup)))
        else:
            return (lambda n, t, s=None: bodo.hiframes.pd_categorical_ext.
                alloc_categorical_array(n, t.dtype))
    if typ.dtype == bodo.hiframes.datetime_date_ext.datetime_date_type:
        return (lambda n, t, s=None: bodo.hiframes.datetime_date_ext.
            alloc_datetime_date_array(n))
    if (typ.dtype == bodo.hiframes.datetime_timedelta_ext.
        datetime_timedelta_type):
        return (lambda n, t, s=None: bodo.hiframes.datetime_timedelta_ext.
            alloc_datetime_timedelta_array(n))
    if isinstance(typ, DecimalArrayType):
        precision = typ.dtype.precision
        scale = typ.dtype.scale
        return (lambda n, t, s=None: bodo.libs.decimal_arr_ext.
            alloc_decimal_array(n, precision, scale))
    dtype = numba.np.numpy_support.as_dtype(typ.dtype)
    if isinstance(typ, IntegerArrayType):
        return lambda n, t, s=None: bodo.libs.int_arr_ext.alloc_int_array(n,
            dtype)
    if typ == boolean_array:
        return lambda n, t, s=None: bodo.libs.bool_arr_ext.alloc_bool_array(n)
    return lambda n, t, s=None: np.empty(n, dtype)


def astype(A, t):
    return A.astype(t.dtype)


@overload(astype, no_unliteral=True)
def overload_astype(A, t):
    typ = t.instance_type if isinstance(t, types.TypeRef) else t
    dtype = typ.dtype
    if A == typ:
        return lambda A, t: A
    if isinstance(A, (types.Array, IntegerArrayType)) and isinstance(typ,
        types.Array):
        return lambda A, t: A.astype(dtype)
    if isinstance(typ, IntegerArrayType):
        return lambda A, t: bodo.libs.int_arr_ext.init_integer_array(A.
            astype(dtype), np.full(len(A) + 7 >> 3, 255, np.uint8))
    if (A == bodo.libs.dict_arr_ext.dict_str_arr_type and typ == bodo.
        string_array_type):
        return lambda A, t: bodo.utils.typing.decode_if_dict_array(A)
    raise BodoError(f'cannot convert array type {A} to {typ}')


def full_type(n, val, t):
    return np.full(n, val, t.dtype)


@overload(full_type, no_unliteral=True)
def overload_full_type(n, val, t):
    typ = t.instance_type if isinstance(t, types.TypeRef) else t
    if isinstance(typ, types.Array):
        dtype = numba.np.numpy_support.as_dtype(typ.dtype)
        return lambda n, val, t: np.full(n, val, dtype)
    if isinstance(typ, IntegerArrayType):
        dtype = numba.np.numpy_support.as_dtype(typ.dtype)
        return lambda n, val, t: bodo.libs.int_arr_ext.init_integer_array(np
            .full(n, val, dtype), np.full(tuple_to_scalar(n) + 7 >> 3, 255,
            np.uint8))
    if typ == boolean_array:
        return lambda n, val, t: bodo.libs.bool_arr_ext.init_bool_array(np.
            full(n, val, np.bool_), np.full(tuple_to_scalar(n) + 7 >> 3, 
            255, np.uint8))
    if typ == string_array_type:

        def impl_str(n, val, t):
            iho__fmk = n * len(val)
            A = pre_alloc_string_array(n, iho__fmk)
            for bdm__nui in range(n):
                A[bdm__nui] = val
            return A
        return impl_str

    def impl(n, val, t):
        A = alloc_type(n, typ, (-1,))
        for bdm__nui in range(n):
            A[bdm__nui] = val
        return A
    return impl


@intrinsic
def is_null_pointer(typingctx, ptr_typ=None):

    def codegen(context, builder, signature, args):
        nmrv__xun, = args
        bxx__nhukq = context.get_constant_null(ptr_typ)
        return builder.icmp_unsigned('==', nmrv__xun, bxx__nhukq)
    return types.bool_(ptr_typ), codegen


@intrinsic
def is_null_value(typingctx, val_typ=None):

    def codegen(context, builder, signature, args):
        val, = args
        tbdyk__pbfi = cgutils.alloca_once_value(builder, val)
        xvqqo__wfz = cgutils.alloca_once_value(builder, context.
            get_constant_null(val_typ))
        return is_ll_eq(builder, tbdyk__pbfi, xvqqo__wfz)
    return types.bool_(val_typ), codegen


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def tuple_list_to_array(A, data, elem_type):
    elem_type = elem_type.instance_type if isinstance(elem_type, types.TypeRef
        ) else elem_type
    mpda__aksmt = 'def impl(A, data, elem_type):\n'
    mpda__aksmt += '  for i, d in enumerate(data):\n'
    if elem_type == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
        mpda__aksmt += (
            '    A[i] = bodo.utils.conversion.unbox_if_timestamp(d)\n')
    else:
        mpda__aksmt += '    A[i] = d\n'
    auf__oyynw = {}
    exec(mpda__aksmt, {'bodo': bodo}, auf__oyynw)
    impl = auf__oyynw['impl']
    return impl


def object_length(c, obj):
    mzrr__cqdj = c.context.get_argument_type(types.pyobject)
    xhvp__ldpg = lir.FunctionType(lir.IntType(64), [mzrr__cqdj])
    bmah__drhye = cgutils.get_or_insert_function(c.builder.module,
        xhvp__ldpg, name='PyObject_Length')
    return c.builder.call(bmah__drhye, (obj,))


@intrinsic
def incref(typingctx, data=None):

    def codegen(context, builder, signature, args):
        vec__obvbq, = args
        context.nrt.incref(builder, signature.args[0], vec__obvbq)
    return types.void(data), codegen


def gen_getitem(out_var, in_var, ind, calltypes, nodes):
    wmdr__sdwxz = out_var.loc
    tvem__gwj = ir.Expr.static_getitem(in_var, ind, None, wmdr__sdwxz)
    calltypes[tvem__gwj] = None
    nodes.append(ir.Assign(tvem__gwj, out_var, wmdr__sdwxz))


def is_static_getsetitem(node):
    return is_expr(node, 'static_getitem') or isinstance(node, ir.StaticSetItem
        )


def get_getsetitem_index_var(node, typemap, nodes):
    index_var = node.index_var if is_static_getsetitem(node) else node.index
    if index_var is None:
        assert is_static_getsetitem(node)
        try:
            cjwnn__jxd = types.literal(node.index)
        except:
            cjwnn__jxd = numba.typeof(node.index)
        index_var = ir.Var(node.value.scope, ir_utils.mk_unique_var(
            'dummy_index'), node.loc)
        typemap[index_var.name] = cjwnn__jxd
        nodes.append(ir.Assign(ir.Const(node.index, node.loc), index_var,
            node.loc))
    return index_var


import copy
ir.Const.__deepcopy__ = lambda self, memo: ir.Const(self.value, copy.
    deepcopy(self.loc))


def is_call_assign(stmt):
    return isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.Expr
        ) and stmt.value.op == 'call'


def is_call(expr):
    return isinstance(expr, ir.Expr) and expr.op == 'call'


def is_var_assign(inst):
    return isinstance(inst, ir.Assign) and isinstance(inst.value, ir.Var)


def is_assign(inst):
    return isinstance(inst, ir.Assign)


def is_expr(val, op):
    return isinstance(val, ir.Expr) and val.op == op


def sanitize_varname(varname):
    if isinstance(varname, (tuple, list)):
        varname = '_'.join(sanitize_varname(v) for v in varname)
    varname = str(varname)
    syh__itao = re.sub('\\W+', '_', varname)
    if not syh__itao or not syh__itao[0].isalpha():
        syh__itao = '_' + syh__itao
    if not syh__itao.isidentifier() or keyword.iskeyword(syh__itao):
        syh__itao = mk_unique_var('new_name').replace('.', '_')
    return syh__itao


def dump_node_list(node_list):
    for n in node_list:
        print('   ', n)


def debug_prints():
    return numba.core.config.DEBUG_ARRAY_OPT == 1


@overload(reversed)
def list_reverse(A):
    if isinstance(A, types.List):

        def impl_reversed(A):
            uman__vngq = len(A)
            for bdm__nui in range(uman__vngq):
                yield A[uman__vngq - 1 - bdm__nui]
        return impl_reversed


@numba.njit
def count_nonnan(a):
    return np.count_nonzero(~np.isnan(a))


@numba.njit
def nanvar_ddof1(a):
    cau__csai = count_nonnan(a)
    if cau__csai <= 1:
        return np.nan
    return np.nanvar(a) * (cau__csai / (cau__csai - 1))


@numba.njit
def nanstd_ddof1(a):
    return np.sqrt(nanvar_ddof1(a))


def has_supported_h5py():
    try:
        import h5py
        from bodo.io import _hdf5
    except ImportError as xnpx__tme:
        cxaet__doae = False
    else:
        cxaet__doae = h5py.version.hdf5_version_tuple[1] == 10
    return cxaet__doae


def check_h5py():
    if not has_supported_h5py():
        raise BodoError("install 'h5py' package to enable hdf5 support")


def has_pyarrow():
    try:
        import pyarrow
    except ImportError as xnpx__tme:
        axs__xwcr = False
    else:
        axs__xwcr = True
    return axs__xwcr


def has_scipy():
    try:
        import scipy
    except ImportError as xnpx__tme:
        eaqi__oseye = False
    else:
        eaqi__oseye = True
    return eaqi__oseye


@intrinsic
def check_and_propagate_cpp_exception(typingctx):

    def codegen(context, builder, sig, args):
        zqvmu__bcs = context.get_python_api(builder)
        azpa__cbovn = zqvmu__bcs.err_occurred()
        mcwmn__whl = cgutils.is_not_null(builder, azpa__cbovn)
        with builder.if_then(mcwmn__whl):
            builder.ret(numba.core.callconv.RETCODE_EXC)
    return types.void(), codegen


def inlined_check_and_propagate_cpp_exception(context, builder):
    zqvmu__bcs = context.get_python_api(builder)
    azpa__cbovn = zqvmu__bcs.err_occurred()
    mcwmn__whl = cgutils.is_not_null(builder, azpa__cbovn)
    with builder.if_then(mcwmn__whl):
        builder.ret(numba.core.callconv.RETCODE_EXC)


@numba.njit
def check_java_installation(fname):
    with numba.objmode():
        check_java_installation_(fname)


def check_java_installation_(fname):
    if not fname.startswith('hdfs://'):
        return
    import shutil
    if not shutil.which('java'):
        zsjs__sif = (
            "Java not found. Make sure openjdk is installed for hdfs. openjdk can be installed by calling 'conda install openjdk=8 -c conda-forge'."
            )
        raise BodoError(zsjs__sif)


dt_err = """
        If you are trying to set NULL values for timedelta64 in regular Python, 

        consider using np.timedelta64('nat') instead of None
        """


@lower_constant(types.List)
def lower_constant_list(context, builder, typ, pyval):
    if len(pyval) > CONST_LIST_SLOW_WARN_THRESHOLD:
        warnings.warn(BodoWarning(
            'Using large global lists can result in long compilation times. Please pass large lists as arguments to JIT functions or use arrays.'
            ))
    zrmj__nqiec = []
    for a in pyval:
        if bodo.typeof(a) != typ.dtype:
            raise BodoError(
                f'Values in list must have the same data type for type stability. Expected: {typ.dtype}, Actual: {bodo.typeof(a)}'
                )
        zrmj__nqiec.append(context.get_constant_generic(builder, typ.dtype, a))
    rtgd__uavr = context.get_constant_generic(builder, types.int64, len(pyval))
    kut__jvr = context.get_constant_generic(builder, types.bool_, False)
    prnz__bqxg = context.get_constant_null(types.pyobject)
    lti__wjv = lir.Constant.literal_struct([rtgd__uavr, rtgd__uavr,
        kut__jvr] + zrmj__nqiec)
    lti__wjv = cgutils.global_constant(builder, '.const.payload', lti__wjv
        ).bitcast(cgutils.voidptr_t)
    opcn__uhzz = context.get_constant(types.int64, -1)
    yefg__lrvsl = context.get_constant_null(types.voidptr)
    wbu__uguv = lir.Constant.literal_struct([opcn__uhzz, yefg__lrvsl,
        yefg__lrvsl, lti__wjv, opcn__uhzz])
    wbu__uguv = cgutils.global_constant(builder, '.const.meminfo', wbu__uguv
        ).bitcast(cgutils.voidptr_t)
    return lir.Constant.literal_struct([wbu__uguv, prnz__bqxg])


@lower_constant(types.Set)
def lower_constant_set(context, builder, typ, pyval):
    for a in pyval:
        if bodo.typeof(a) != typ.dtype:
            raise BodoError(
                f'Values in set must have the same data type for type stability. Expected: {typ.dtype}, Actual: {bodo.typeof(a)}'
                )
    urgk__prqcd = types.List(typ.dtype)
    qdjuv__vlnu = context.get_constant_generic(builder, urgk__prqcd, list(
        pyval))
    oktaa__dzsja = context.compile_internal(builder, lambda l: set(l),
        types.Set(typ.dtype)(urgk__prqcd), [qdjuv__vlnu])
    return oktaa__dzsja


def lower_const_dict_fast_path(context, builder, typ, pyval):
    from bodo.utils.typing import can_replace
    qetm__dlhf = pd.Series(pyval.keys()).values
    grhj__xpy = pd.Series(pyval.values()).values
    gwr__kuph = bodo.typeof(qetm__dlhf)
    lhm__qfpun = bodo.typeof(grhj__xpy)
    require(gwr__kuph.dtype == typ.key_type or can_replace(typ.key_type,
        gwr__kuph.dtype))
    require(lhm__qfpun.dtype == typ.value_type or can_replace(typ.
        value_type, lhm__qfpun.dtype))
    hku__lhhqf = context.get_constant_generic(builder, gwr__kuph, qetm__dlhf)
    yrtb__fyil = context.get_constant_generic(builder, lhm__qfpun, grhj__xpy)

    def create_dict(keys, vals):
        zhwj__mvua = {}
        for k, v in zip(keys, vals):
            zhwj__mvua[k] = v
        return zhwj__mvua
    ofbpa__mbbv = context.compile_internal(builder, create_dict, typ(
        gwr__kuph, lhm__qfpun), [hku__lhhqf, yrtb__fyil])
    return ofbpa__mbbv


@lower_constant(types.DictType)
def lower_constant_dict(context, builder, typ, pyval):
    try:
        return lower_const_dict_fast_path(context, builder, typ, pyval)
    except:
        pass
    if len(pyval) > CONST_DICT_SLOW_WARN_THRESHOLD:
        warnings.warn(BodoWarning(
            'Using large global dictionaries can result in long compilation times. Please pass large dictionaries as arguments to JIT functions.'
            ))
    svd__rde = typ.key_type
    zya__tszl = typ.value_type

    def make_dict():
        return numba.typed.Dict.empty(svd__rde, zya__tszl)
    ofbpa__mbbv = context.compile_internal(builder, make_dict, typ(), [])

    def set_dict_val(d, k, v):
        d[k] = v
    for k, v in pyval.items():
        inb__zbmkk = context.get_constant_generic(builder, svd__rde, k)
        fuute__bicv = context.get_constant_generic(builder, zya__tszl, v)
        context.compile_internal(builder, set_dict_val, types.none(typ,
            svd__rde, zya__tszl), [ofbpa__mbbv, inb__zbmkk, fuute__bicv])
    return ofbpa__mbbv
