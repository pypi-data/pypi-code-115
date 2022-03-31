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
    zhud__xlfgw = guard(get_definition, func_ir, var)
    if zhud__xlfgw is None:
        return default
    if isinstance(zhud__xlfgw, ir.Const):
        return zhud__xlfgw.value
    if isinstance(zhud__xlfgw, ir.Var):
        return get_constant(func_ir, zhud__xlfgw, default)
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
    mxx__zuzxh = get_definition(func_ir, var)
    require(isinstance(mxx__zuzxh, ir.Expr))
    require(mxx__zuzxh.op == 'build_tuple')
    return mxx__zuzxh.items


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
    for nwufm__lsv, val in enumerate(args):
        typ = sig.args[nwufm__lsv]
        if isinstance(typ, types.ArrayCTypes):
            cgutils.printf(builder, '%p ', val)
            continue
        zivr__ppau = typ_to_format[typ]
        cgutils.printf(builder, '%{} '.format(zivr__ppau), val)
    cgutils.printf(builder, '\n')
    return context.get_dummy_value()


def is_whole_slice(typemap, func_ir, var, accept_stride=False):
    require(typemap[var.name] == types.slice2_type or accept_stride and 
        typemap[var.name] == types.slice3_type)
    lyll__okvc = get_definition(func_ir, var)
    require(isinstance(lyll__okvc, ir.Expr) and lyll__okvc.op == 'call')
    assert len(lyll__okvc.args) == 2 or accept_stride and len(lyll__okvc.args
        ) == 3
    assert find_callname(func_ir, lyll__okvc) == ('slice', 'builtins')
    shez__zjnhp = get_definition(func_ir, lyll__okvc.args[0])
    hkb__qag = get_definition(func_ir, lyll__okvc.args[1])
    require(isinstance(shez__zjnhp, ir.Const) and shez__zjnhp.value == None)
    require(isinstance(hkb__qag, ir.Const) and hkb__qag.value == None)
    return True


def is_slice_equiv_arr(arr_var, index_var, func_ir, equiv_set,
    accept_stride=False):
    lifww__gsl = get_definition(func_ir, index_var)
    require(find_callname(func_ir, lifww__gsl) == ('slice', 'builtins'))
    require(len(lifww__gsl.args) in (2, 3))
    require(find_const(func_ir, lifww__gsl.args[0]) in (0, None))
    require(equiv_set.is_equiv(lifww__gsl.args[1], arr_var.name + '#0'))
    require(accept_stride or len(lifww__gsl.args) == 2 or find_const(
        func_ir, lifww__gsl.args[2]) == 1)
    return True


def get_slice_step(typemap, func_ir, var):
    require(typemap[var.name] == types.slice3_type)
    lyll__okvc = get_definition(func_ir, var)
    require(isinstance(lyll__okvc, ir.Expr) and lyll__okvc.op == 'call')
    assert len(lyll__okvc.args) == 3
    return lyll__okvc.args[2]


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
        vdwmw__cxm = False
        for nwufm__lsv in range(len(A)):
            if bodo.libs.array_kernels.isna(A, nwufm__lsv):
                vdwmw__cxm = True
                continue
            s[A[nwufm__lsv]] = 0
        return s, vdwmw__cxm
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
        qou__jtms = arr.dtype

        def empty_like_type_int_arr(n, arr):
            return bodo.libs.int_arr_ext.alloc_int_array(n, qou__jtms)
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
        jgy__kqkf = 20
        if len(arr) != 0:
            jgy__kqkf = num_total_chars(arr) // len(arr)
        return pre_alloc_string_array(n, n * jgy__kqkf)
    return empty_like_type_str_arr


def _empty_nd_impl(context, builder, arrtype, shapes):
    eylh__gtlg = make_array(arrtype)
    hncxj__czjlb = eylh__gtlg(context, builder)
    tdc__xkta = context.get_data_type(arrtype.dtype)
    ybqgo__xrgjy = context.get_constant(types.intp, get_itemsize(context,
        arrtype))
    srd__zaxn = context.get_constant(types.intp, 1)
    hlgzs__ccw = lir.Constant(lir.IntType(1), 0)
    for s in shapes:
        cly__vrin = builder.smul_with_overflow(srd__zaxn, s)
        srd__zaxn = builder.extract_value(cly__vrin, 0)
        hlgzs__ccw = builder.or_(hlgzs__ccw, builder.extract_value(
            cly__vrin, 1))
    if arrtype.ndim == 0:
        dtwi__zhtmb = ()
    elif arrtype.layout == 'C':
        dtwi__zhtmb = [ybqgo__xrgjy]
        for thnii__axthe in reversed(shapes[1:]):
            dtwi__zhtmb.append(builder.mul(dtwi__zhtmb[-1], thnii__axthe))
        dtwi__zhtmb = tuple(reversed(dtwi__zhtmb))
    elif arrtype.layout == 'F':
        dtwi__zhtmb = [ybqgo__xrgjy]
        for thnii__axthe in shapes[:-1]:
            dtwi__zhtmb.append(builder.mul(dtwi__zhtmb[-1], thnii__axthe))
        dtwi__zhtmb = tuple(dtwi__zhtmb)
    else:
        raise NotImplementedError(
            "Don't know how to allocate array with layout '{0}'.".format(
            arrtype.layout))
    gyv__wcy = builder.smul_with_overflow(srd__zaxn, ybqgo__xrgjy)
    sukl__lsh = builder.extract_value(gyv__wcy, 0)
    hlgzs__ccw = builder.or_(hlgzs__ccw, builder.extract_value(gyv__wcy, 1))
    with builder.if_then(hlgzs__ccw, likely=False):
        cgutils.printf(builder,
            'array is too big; `arr.size * arr.dtype.itemsize` is larger than the maximum possible size.'
            )
    dtype = arrtype.dtype
    dqe__cpfpb = context.get_preferred_array_alignment(dtype)
    iwm__bhhpw = context.get_constant(types.uint32, dqe__cpfpb)
    dcrhw__agdqn = context.nrt.meminfo_alloc_aligned(builder, size=
        sukl__lsh, align=iwm__bhhpw)
    data = context.nrt.meminfo_data(builder, dcrhw__agdqn)
    naapm__nmvcn = context.get_value_type(types.intp)
    sqy__vyn = cgutils.pack_array(builder, shapes, ty=naapm__nmvcn)
    bzrx__amcsu = cgutils.pack_array(builder, dtwi__zhtmb, ty=naapm__nmvcn)
    populate_array(hncxj__czjlb, data=builder.bitcast(data, tdc__xkta.
        as_pointer()), shape=sqy__vyn, strides=bzrx__amcsu, itemsize=
        ybqgo__xrgjy, meminfo=dcrhw__agdqn)
    return hncxj__czjlb


if bodo.numba_compat._check_numba_change:
    lines = inspect.getsource(numba.np.arrayobj._empty_nd_impl)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b6a998927680caa35917a553c79704e9d813d8f1873d83a5f8513837c159fa29':
        warnings.warn('numba.np.arrayobj._empty_nd_impl has changed')


def alloc_arr_tup(n, arr_tup, init_vals=()):
    fgt__audp = []
    for djikb__vshu in arr_tup:
        fgt__audp.append(np.empty(n, djikb__vshu.dtype))
    return tuple(fgt__audp)


@overload(alloc_arr_tup, no_unliteral=True)
def alloc_arr_tup_overload(n, data, init_vals=()):
    syrc__ksw = data.count
    rscvd__dcn = ','.join(['empty_like_type(n, data[{}])'.format(nwufm__lsv
        ) for nwufm__lsv in range(syrc__ksw)])
    if init_vals != ():
        rscvd__dcn = ','.join(['np.full(n, init_vals[{}], data[{}].dtype)'.
            format(nwufm__lsv, nwufm__lsv) for nwufm__lsv in range(syrc__ksw)])
    jpj__njyau = 'def f(n, data, init_vals=()):\n'
    jpj__njyau += '  return ({}{})\n'.format(rscvd__dcn, ',' if syrc__ksw ==
        1 else '')
    rxd__mhlj = {}
    exec(jpj__njyau, {'empty_like_type': empty_like_type, 'np': np}, rxd__mhlj)
    ddgj__oxtyo = rxd__mhlj['f']
    return ddgj__oxtyo


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
            odzi__ajm = n * len(val)
            A = pre_alloc_string_array(n, odzi__ajm)
            for nwufm__lsv in range(n):
                A[nwufm__lsv] = val
            return A
        return impl_str

    def impl(n, val, t):
        A = alloc_type(n, typ, (-1,))
        for nwufm__lsv in range(n):
            A[nwufm__lsv] = val
        return A
    return impl


@intrinsic
def is_null_pointer(typingctx, ptr_typ=None):

    def codegen(context, builder, signature, args):
        ieh__yhczd, = args
        oqp__jpk = context.get_constant_null(ptr_typ)
        return builder.icmp_unsigned('==', ieh__yhczd, oqp__jpk)
    return types.bool_(ptr_typ), codegen


@intrinsic
def is_null_value(typingctx, val_typ=None):

    def codegen(context, builder, signature, args):
        val, = args
        gac__mrcz = cgutils.alloca_once_value(builder, val)
        oavby__ykrul = cgutils.alloca_once_value(builder, context.
            get_constant_null(val_typ))
        return is_ll_eq(builder, gac__mrcz, oavby__ykrul)
    return types.bool_(val_typ), codegen


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def tuple_list_to_array(A, data, elem_type):
    elem_type = elem_type.instance_type if isinstance(elem_type, types.TypeRef
        ) else elem_type
    jpj__njyau = 'def impl(A, data, elem_type):\n'
    jpj__njyau += '  for i, d in enumerate(data):\n'
    if elem_type == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
        jpj__njyau += (
            '    A[i] = bodo.utils.conversion.unbox_if_timestamp(d)\n')
    else:
        jpj__njyau += '    A[i] = d\n'
    rxd__mhlj = {}
    exec(jpj__njyau, {'bodo': bodo}, rxd__mhlj)
    impl = rxd__mhlj['impl']
    return impl


def object_length(c, obj):
    acuxm__qjz = c.context.get_argument_type(types.pyobject)
    sll__kiw = lir.FunctionType(lir.IntType(64), [acuxm__qjz])
    qcjl__tfp = cgutils.get_or_insert_function(c.builder.module, sll__kiw,
        name='PyObject_Length')
    return c.builder.call(qcjl__tfp, (obj,))


@intrinsic
def incref(typingctx, data=None):

    def codegen(context, builder, signature, args):
        xonli__ofms, = args
        context.nrt.incref(builder, signature.args[0], xonli__ofms)
    return types.void(data), codegen


def gen_getitem(out_var, in_var, ind, calltypes, nodes):
    acwbw__fsx = out_var.loc
    nzpjt__dygiz = ir.Expr.static_getitem(in_var, ind, None, acwbw__fsx)
    calltypes[nzpjt__dygiz] = None
    nodes.append(ir.Assign(nzpjt__dygiz, out_var, acwbw__fsx))


def is_static_getsetitem(node):
    return is_expr(node, 'static_getitem') or isinstance(node, ir.StaticSetItem
        )


def get_getsetitem_index_var(node, typemap, nodes):
    index_var = node.index_var if is_static_getsetitem(node) else node.index
    if index_var is None:
        assert is_static_getsetitem(node)
        try:
            pzn__pag = types.literal(node.index)
        except:
            pzn__pag = numba.typeof(node.index)
        index_var = ir.Var(node.value.scope, ir_utils.mk_unique_var(
            'dummy_index'), node.loc)
        typemap[index_var.name] = pzn__pag
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
    tblpg__xhf = re.sub('\\W+', '_', varname)
    if not tblpg__xhf or not tblpg__xhf[0].isalpha():
        tblpg__xhf = '_' + tblpg__xhf
    if not tblpg__xhf.isidentifier() or keyword.iskeyword(tblpg__xhf):
        tblpg__xhf = mk_unique_var('new_name').replace('.', '_')
    return tblpg__xhf


def dump_node_list(node_list):
    for n in node_list:
        print('   ', n)


def debug_prints():
    return numba.core.config.DEBUG_ARRAY_OPT == 1


@overload(reversed)
def list_reverse(A):
    if isinstance(A, types.List):

        def impl_reversed(A):
            ygkr__pidgu = len(A)
            for nwufm__lsv in range(ygkr__pidgu):
                yield A[ygkr__pidgu - 1 - nwufm__lsv]
        return impl_reversed


@numba.njit
def count_nonnan(a):
    return np.count_nonzero(~np.isnan(a))


@numba.njit
def nanvar_ddof1(a):
    wqiuz__wxqj = count_nonnan(a)
    if wqiuz__wxqj <= 1:
        return np.nan
    return np.nanvar(a) * (wqiuz__wxqj / (wqiuz__wxqj - 1))


@numba.njit
def nanstd_ddof1(a):
    return np.sqrt(nanvar_ddof1(a))


def has_supported_h5py():
    try:
        import h5py
        from bodo.io import _hdf5
    except ImportError as tsujl__mcqrq:
        cid__aiejg = False
    else:
        cid__aiejg = h5py.version.hdf5_version_tuple[1] == 10
    return cid__aiejg


def check_h5py():
    if not has_supported_h5py():
        raise BodoError("install 'h5py' package to enable hdf5 support")


def has_pyarrow():
    try:
        import pyarrow
    except ImportError as tsujl__mcqrq:
        mwcoi__cyhry = False
    else:
        mwcoi__cyhry = True
    return mwcoi__cyhry


def has_scipy():
    try:
        import scipy
    except ImportError as tsujl__mcqrq:
        qnx__lri = False
    else:
        qnx__lri = True
    return qnx__lri


@intrinsic
def check_and_propagate_cpp_exception(typingctx):

    def codegen(context, builder, sig, args):
        conwv__dsxng = context.get_python_api(builder)
        qepj__loo = conwv__dsxng.err_occurred()
        febhp__ufrjx = cgutils.is_not_null(builder, qepj__loo)
        with builder.if_then(febhp__ufrjx):
            builder.ret(numba.core.callconv.RETCODE_EXC)
    return types.void(), codegen


def inlined_check_and_propagate_cpp_exception(context, builder):
    conwv__dsxng = context.get_python_api(builder)
    qepj__loo = conwv__dsxng.err_occurred()
    febhp__ufrjx = cgutils.is_not_null(builder, qepj__loo)
    with builder.if_then(febhp__ufrjx):
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
        djz__llwue = (
            "Java not found. Make sure openjdk is installed for hdfs. openjdk can be installed by calling 'conda install openjdk=8 -c conda-forge'."
            )
        raise BodoError(djz__llwue)


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
    tkv__xcyo = []
    for a in pyval:
        if bodo.typeof(a) != typ.dtype:
            raise BodoError(
                f'Values in list must have the same data type for type stability. Expected: {typ.dtype}, Actual: {bodo.typeof(a)}'
                )
        tkv__xcyo.append(context.get_constant_generic(builder, typ.dtype, a))
    ihex__czif = context.get_constant_generic(builder, types.int64, len(pyval))
    teo__gvnnm = context.get_constant_generic(builder, types.bool_, False)
    ejlem__bvhe = context.get_constant_null(types.pyobject)
    epypn__hfn = lir.Constant.literal_struct([ihex__czif, ihex__czif,
        teo__gvnnm] + tkv__xcyo)
    epypn__hfn = cgutils.global_constant(builder, '.const.payload', epypn__hfn
        ).bitcast(cgutils.voidptr_t)
    ory__vbtrl = context.get_constant(types.int64, -1)
    aeeoa__klm = context.get_constant_null(types.voidptr)
    dcrhw__agdqn = lir.Constant.literal_struct([ory__vbtrl, aeeoa__klm,
        aeeoa__klm, epypn__hfn, ory__vbtrl])
    dcrhw__agdqn = cgutils.global_constant(builder, '.const.meminfo',
        dcrhw__agdqn).bitcast(cgutils.voidptr_t)
    return lir.Constant.literal_struct([dcrhw__agdqn, ejlem__bvhe])


@lower_constant(types.Set)
def lower_constant_set(context, builder, typ, pyval):
    for a in pyval:
        if bodo.typeof(a) != typ.dtype:
            raise BodoError(
                f'Values in set must have the same data type for type stability. Expected: {typ.dtype}, Actual: {bodo.typeof(a)}'
                )
    qmbwp__fwei = types.List(typ.dtype)
    lqg__uyn = context.get_constant_generic(builder, qmbwp__fwei, list(pyval))
    wnop__iha = context.compile_internal(builder, lambda l: set(l), types.
        Set(typ.dtype)(qmbwp__fwei), [lqg__uyn])
    return wnop__iha


def lower_const_dict_fast_path(context, builder, typ, pyval):
    from bodo.utils.typing import can_replace
    cvap__ddzcd = pd.Series(pyval.keys()).values
    pfbo__cyvc = pd.Series(pyval.values()).values
    fel__xfnyp = bodo.typeof(cvap__ddzcd)
    lkhpb__hhje = bodo.typeof(pfbo__cyvc)
    require(fel__xfnyp.dtype == typ.key_type or can_replace(typ.key_type,
        fel__xfnyp.dtype))
    require(lkhpb__hhje.dtype == typ.value_type or can_replace(typ.
        value_type, lkhpb__hhje.dtype))
    vaam__mbwbe = context.get_constant_generic(builder, fel__xfnyp, cvap__ddzcd
        )
    kjiko__kpg = context.get_constant_generic(builder, lkhpb__hhje, pfbo__cyvc)

    def create_dict(keys, vals):
        cwmq__klbzp = {}
        for k, v in zip(keys, vals):
            cwmq__klbzp[k] = v
        return cwmq__klbzp
    ssw__dxsp = context.compile_internal(builder, create_dict, typ(
        fel__xfnyp, lkhpb__hhje), [vaam__mbwbe, kjiko__kpg])
    return ssw__dxsp


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
    kme__hgpbm = typ.key_type
    cvqy__ujeoc = typ.value_type

    def make_dict():
        return numba.typed.Dict.empty(kme__hgpbm, cvqy__ujeoc)
    ssw__dxsp = context.compile_internal(builder, make_dict, typ(), [])

    def set_dict_val(d, k, v):
        d[k] = v
    for k, v in pyval.items():
        iawc__rxcqw = context.get_constant_generic(builder, kme__hgpbm, k)
        wscg__mggp = context.get_constant_generic(builder, cvqy__ujeoc, v)
        context.compile_internal(builder, set_dict_val, types.none(typ,
            kme__hgpbm, cvqy__ujeoc), [ssw__dxsp, iawc__rxcqw, wscg__mggp])
    return ssw__dxsp
