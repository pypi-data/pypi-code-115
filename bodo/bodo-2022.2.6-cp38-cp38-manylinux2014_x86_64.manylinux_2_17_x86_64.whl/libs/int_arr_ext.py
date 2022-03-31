"""Nullable integer array corresponding to Pandas IntegerArray.
However, nulls are stored in bit arrays similar to Arrow's arrays.
"""
import operator
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import lower_constant
from numba.extending import NativeValue, box, intrinsic, lower_builtin, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_model, type_callable, typeof_impl, unbox
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
from bodo.libs.str_arr_ext import kBitmask
from bodo.libs import array_ext, hstr_ext
ll.add_symbol('mask_arr_to_bitmap', hstr_ext.mask_arr_to_bitmap)
ll.add_symbol('is_pd_int_array', array_ext.is_pd_int_array)
ll.add_symbol('int_array_from_sequence', array_ext.int_array_from_sequence)
from bodo.hiframes.datetime_timedelta_ext import pd_timedelta_type
from bodo.utils.indexing import array_getitem_bool_index, array_getitem_int_index, array_getitem_slice_index, array_setitem_bool_index, array_setitem_int_index, array_setitem_slice_index
from bodo.utils.typing import BodoError, check_unsupported_args, is_iterable_type, is_list_like_index_type, is_overload_false, is_overload_none, is_overload_true, parse_dtype, raise_bodo_error, to_nullable_type


class IntegerArrayType(types.ArrayCompatible):

    def __init__(self, dtype):
        self.dtype = dtype
        super(IntegerArrayType, self).__init__(name=
            f'IntegerArrayType({dtype})')

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    def copy(self):
        return IntegerArrayType(self.dtype)


@register_model(IntegerArrayType)
class IntegerArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        kxrm__mons = [('data', types.Array(fe_type.dtype, 1, 'C')), (
            'null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, kxrm__mons)


make_attribute_wrapper(IntegerArrayType, 'data', '_data')
make_attribute_wrapper(IntegerArrayType, 'null_bitmap', '_null_bitmap')


@typeof_impl.register(pd.arrays.IntegerArray)
def _typeof_pd_int_array(val, c):
    zhur__ioiq = 8 * val.dtype.itemsize
    emr__qaevy = '' if val.dtype.kind == 'i' else 'u'
    dtype = getattr(types, '{}int{}'.format(emr__qaevy, zhur__ioiq))
    return IntegerArrayType(dtype)


class IntDtype(types.Number):

    def __init__(self, dtype):
        assert isinstance(dtype, types.Integer)
        self.dtype = dtype
        wusjg__svs = '{}Int{}Dtype()'.format('' if dtype.signed else 'U',
            dtype.bitwidth)
        super(IntDtype, self).__init__(wusjg__svs)


register_model(IntDtype)(models.OpaqueModel)


@box(IntDtype)
def box_intdtype(typ, val, c):
    hjvlf__ajrc = c.context.insert_const_string(c.builder.module, 'pandas')
    pze__pedpa = c.pyapi.import_module_noblock(hjvlf__ajrc)
    hoc__drfe = c.pyapi.call_method(pze__pedpa, str(typ)[:-2], ())
    c.pyapi.decref(pze__pedpa)
    return hoc__drfe


@unbox(IntDtype)
def unbox_intdtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


def typeof_pd_int_dtype(val, c):
    zhur__ioiq = 8 * val.itemsize
    emr__qaevy = '' if val.kind == 'i' else 'u'
    dtype = getattr(types, '{}int{}'.format(emr__qaevy, zhur__ioiq))
    return IntDtype(dtype)


def _register_int_dtype(t):
    typeof_impl.register(t)(typeof_pd_int_dtype)
    int_dtype = typeof_pd_int_dtype(t(), None)
    type_callable(t)(lambda c: lambda : int_dtype)
    lower_builtin(t)(lambda c, b, s, a: c.get_dummy_value())


pd_int_dtype_classes = (pd.Int8Dtype, pd.Int16Dtype, pd.Int32Dtype, pd.
    Int64Dtype, pd.UInt8Dtype, pd.UInt16Dtype, pd.UInt32Dtype, pd.UInt64Dtype)
for t in pd_int_dtype_classes:
    _register_int_dtype(t)


@numba.extending.register_jitable
def mask_arr_to_bitmap(mask_arr):
    n = len(mask_arr)
    xztn__ptoq = n + 7 >> 3
    byz__bxfr = np.empty(xztn__ptoq, np.uint8)
    for i in range(n):
        pftg__hvc = i // 8
        byz__bxfr[pftg__hvc] ^= np.uint8(-np.uint8(not mask_arr[i]) ^
            byz__bxfr[pftg__hvc]) & kBitmask[i % 8]
    return byz__bxfr


@unbox(IntegerArrayType)
def unbox_int_array(typ, obj, c):
    pgfax__akx = c.pyapi.call_method(obj, '__len__', ())
    n = c.pyapi.long_as_longlong(pgfax__akx)
    c.pyapi.decref(pgfax__akx)
    lyv__eiku = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    xztn__ptoq = c.builder.udiv(c.builder.add(n, lir.Constant(lir.IntType(
        64), 7)), lir.Constant(lir.IntType(64), 8))
    gfxk__nwiti = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        types.Array(types.uint8, 1, 'C'), [xztn__ptoq])
    favr__ubjim = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
        as_pointer()])
    wzq__bityc = cgutils.get_or_insert_function(c.builder.module,
        favr__ubjim, name='is_pd_int_array')
    bgo__ebqh = c.builder.call(wzq__bityc, [obj])
    wjvrq__bdbjq = c.builder.icmp_unsigned('!=', bgo__ebqh, bgo__ebqh.type(0))
    with c.builder.if_else(wjvrq__bdbjq) as (orw__qhlz, tsyl__tkdt):
        with orw__qhlz:
            cmduj__toscc = c.pyapi.object_getattr_string(obj, '_data')
            lyv__eiku.data = c.pyapi.to_native_value(types.Array(typ.dtype,
                1, 'C'), cmduj__toscc).value
            dnhx__sorcp = c.pyapi.object_getattr_string(obj, '_mask')
            mask_arr = c.pyapi.to_native_value(types.Array(types.bool_, 1,
                'C'), dnhx__sorcp).value
            c.pyapi.decref(cmduj__toscc)
            c.pyapi.decref(dnhx__sorcp)
            ghj__ulgc = c.context.make_array(types.Array(types.bool_, 1, 'C'))(
                c.context, c.builder, mask_arr)
            favr__ubjim = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
            wzq__bityc = cgutils.get_or_insert_function(c.builder.module,
                favr__ubjim, name='mask_arr_to_bitmap')
            c.builder.call(wzq__bityc, [gfxk__nwiti.data, ghj__ulgc.data, n])
            c.context.nrt.decref(c.builder, types.Array(types.bool_, 1, 'C'
                ), mask_arr)
        with tsyl__tkdt:
            byj__mbnjt = bodo.utils.utils._empty_nd_impl(c.context, c.
                builder, types.Array(typ.dtype, 1, 'C'), [n])
            favr__ubjim = lir.FunctionType(lir.IntType(32), [lir.IntType(8)
                .as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
                as_pointer()])
            eln__hpkb = cgutils.get_or_insert_function(c.builder.module,
                favr__ubjim, name='int_array_from_sequence')
            c.builder.call(eln__hpkb, [obj, c.builder.bitcast(byj__mbnjt.
                data, lir.IntType(8).as_pointer()), gfxk__nwiti.data])
            lyv__eiku.data = byj__mbnjt._getvalue()
    lyv__eiku.null_bitmap = gfxk__nwiti._getvalue()
    ciwuw__kkr = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(lyv__eiku._getvalue(), is_error=ciwuw__kkr)


@box(IntegerArrayType)
def box_int_arr(typ, val, c):
    lyv__eiku = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    data = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        lyv__eiku.data, c.env_manager)
    kickd__eruot = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, lyv__eiku.null_bitmap).data
    pgfax__akx = c.pyapi.call_method(data, '__len__', ())
    n = c.pyapi.long_as_longlong(pgfax__akx)
    hjvlf__ajrc = c.context.insert_const_string(c.builder.module, 'numpy')
    hyah__kme = c.pyapi.import_module_noblock(hjvlf__ajrc)
    vfqwp__kbyz = c.pyapi.object_getattr_string(hyah__kme, 'bool_')
    mask_arr = c.pyapi.call_method(hyah__kme, 'empty', (pgfax__akx,
        vfqwp__kbyz))
    fuk__evk = c.pyapi.object_getattr_string(mask_arr, 'ctypes')
    xdwf__zmg = c.pyapi.object_getattr_string(fuk__evk, 'data')
    kvxnx__zqklm = c.builder.inttoptr(c.pyapi.long_as_longlong(xdwf__zmg),
        lir.IntType(8).as_pointer())
    with cgutils.for_range(c.builder, n) as dlq__vkd:
        i = dlq__vkd.index
        fsr__qjuwc = c.builder.lshr(i, lir.Constant(lir.IntType(64), 3))
        aor__zidg = c.builder.load(cgutils.gep(c.builder, kickd__eruot,
            fsr__qjuwc))
        plj__qsefa = c.builder.trunc(c.builder.and_(i, lir.Constant(lir.
            IntType(64), 7)), lir.IntType(8))
        val = c.builder.and_(c.builder.lshr(aor__zidg, plj__qsefa), lir.
            Constant(lir.IntType(8), 1))
        val = c.builder.xor(val, lir.Constant(lir.IntType(8), 1))
        cok__dwhe = cgutils.gep(c.builder, kvxnx__zqklm, i)
        c.builder.store(val, cok__dwhe)
    c.context.nrt.decref(c.builder, types.Array(types.uint8, 1, 'C'),
        lyv__eiku.null_bitmap)
    hjvlf__ajrc = c.context.insert_const_string(c.builder.module, 'pandas')
    pze__pedpa = c.pyapi.import_module_noblock(hjvlf__ajrc)
    hilt__etj = c.pyapi.object_getattr_string(pze__pedpa, 'arrays')
    hoc__drfe = c.pyapi.call_method(hilt__etj, 'IntegerArray', (data, mask_arr)
        )
    c.pyapi.decref(pze__pedpa)
    c.pyapi.decref(pgfax__akx)
    c.pyapi.decref(hyah__kme)
    c.pyapi.decref(vfqwp__kbyz)
    c.pyapi.decref(fuk__evk)
    c.pyapi.decref(xdwf__zmg)
    c.pyapi.decref(hilt__etj)
    c.pyapi.decref(data)
    c.pyapi.decref(mask_arr)
    return hoc__drfe


@intrinsic
def init_integer_array(typingctx, data, null_bitmap=None):
    assert isinstance(data, types.Array)
    assert null_bitmap == types.Array(types.uint8, 1, 'C')

    def codegen(context, builder, signature, args):
        qqwsh__wvn, fwh__xssr = args
        lyv__eiku = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        lyv__eiku.data = qqwsh__wvn
        lyv__eiku.null_bitmap = fwh__xssr
        context.nrt.incref(builder, signature.args[0], qqwsh__wvn)
        context.nrt.incref(builder, signature.args[1], fwh__xssr)
        return lyv__eiku._getvalue()
    czq__ziexw = IntegerArrayType(data.dtype)
    zdr__oqqg = czq__ziexw(data, null_bitmap)
    return zdr__oqqg, codegen


@lower_constant(IntegerArrayType)
def lower_constant_int_arr(context, builder, typ, pyval):
    n = len(pyval)
    ebe__rolj = np.empty(n, pyval.dtype.type)
    iljsu__shpi = np.empty(n + 7 >> 3, np.uint8)
    for i, s in enumerate(pyval):
        jik__rlst = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(iljsu__shpi, i, int(not jik__rlst)
            )
        if not jik__rlst:
            ebe__rolj[i] = s
    vzr__wysd = context.get_constant_generic(builder, types.Array(typ.dtype,
        1, 'C'), ebe__rolj)
    shdp__wfkj = context.get_constant_generic(builder, types.Array(types.
        uint8, 1, 'C'), iljsu__shpi)
    return lir.Constant.literal_struct([vzr__wysd, shdp__wfkj])


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_int_arr_data(A):
    return lambda A: A._data


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_int_arr_bitmap(A):
    return lambda A: A._null_bitmap


def get_int_arr_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    wnoi__vle = args[0]
    if equiv_set.has_shape(wnoi__vle):
        return ArrayAnalysis.AnalyzeResult(shape=wnoi__vle, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_libs_int_arr_ext_get_int_arr_data = (
    get_int_arr_data_equiv)


def init_integer_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    wnoi__vle = args[0]
    if equiv_set.has_shape(wnoi__vle):
        return ArrayAnalysis.AnalyzeResult(shape=wnoi__vle, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_libs_int_arr_ext_init_integer_array = (
    init_integer_array_equiv)


def alias_ext_dummy_func(lhs_name, args, alias_map, arg_aliases):
    assert len(args) >= 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


def alias_ext_init_integer_array(lhs_name, args, alias_map, arg_aliases):
    assert len(args) == 2
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)
    numba.core.ir_utils._add_alias(lhs_name, args[1].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['init_integer_array',
    'bodo.libs.int_arr_ext'] = alias_ext_init_integer_array
numba.core.ir_utils.alias_func_extensions['get_int_arr_data',
    'bodo.libs.int_arr_ext'] = alias_ext_dummy_func
numba.core.ir_utils.alias_func_extensions['get_int_arr_bitmap',
    'bodo.libs.int_arr_ext'] = alias_ext_dummy_func


@numba.njit(no_cpython_wrapper=True)
def alloc_int_array(n, dtype):
    ebe__rolj = np.empty(n, dtype)
    vus__ltkdb = np.empty(n + 7 >> 3, dtype=np.uint8)
    return init_integer_array(ebe__rolj, vus__ltkdb)


def alloc_int_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


ArrayAnalysis._analyze_op_call_bodo_libs_int_arr_ext_alloc_int_array = (
    alloc_int_array_equiv)


@numba.extending.register_jitable
def set_bit_to_arr(bits, i, bit_is_set):
    bits[i // 8] ^= np.uint8(-np.uint8(bit_is_set) ^ bits[i // 8]) & kBitmask[
        i % 8]


@numba.extending.register_jitable
def get_bit_bitmap_arr(bits, i):
    return bits[i >> 3] >> (i & 7) & 1


@overload(operator.getitem, no_unliteral=True)
def int_arr_getitem(A, ind):
    if not isinstance(A, IntegerArrayType):
        return
    if isinstance(ind, types.Integer):
        return lambda A, ind: A._data[ind]
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:

        def impl_bool(A, ind):
            aiuzm__gbeci, vgj__ysqoc = array_getitem_bool_index(A, ind)
            return init_integer_array(aiuzm__gbeci, vgj__ysqoc)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            aiuzm__gbeci, vgj__ysqoc = array_getitem_int_index(A, ind)
            return init_integer_array(aiuzm__gbeci, vgj__ysqoc)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            aiuzm__gbeci, vgj__ysqoc = array_getitem_slice_index(A, ind)
            return init_integer_array(aiuzm__gbeci, vgj__ysqoc)
        return impl_slice
    raise BodoError(
        f'getitem for IntegerArray with indexing type {ind} not supported.')


@overload(operator.setitem, no_unliteral=True)
def int_arr_setitem(A, idx, val):
    if not isinstance(A, IntegerArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    cudy__mbbzy = (
        f"setitem for IntegerArray with indexing type {idx} received an incorrect 'value' type {val}."
        )
    kdrq__xpw = isinstance(val, (types.Integer, types.Boolean))
    if isinstance(idx, types.Integer):
        if kdrq__xpw:

            def impl_scalar(A, idx, val):
                A._data[idx] = val
                bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap, idx, 1)
            return impl_scalar
        else:
            raise BodoError(cudy__mbbzy)
    if not (is_iterable_type(val) and isinstance(val.dtype, (types.Integer,
        types.Boolean)) or kdrq__xpw):
        raise BodoError(cudy__mbbzy)
    if is_list_like_index_type(idx) and isinstance(idx.dtype, types.Integer):

        def impl_arr_ind_mask(A, idx, val):
            array_setitem_int_index(A, idx, val)
        return impl_arr_ind_mask
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:

        def impl_bool_ind_mask(A, idx, val):
            array_setitem_bool_index(A, idx, val)
        return impl_bool_ind_mask
    if isinstance(idx, types.SliceType):

        def impl_slice_mask(A, idx, val):
            array_setitem_slice_index(A, idx, val)
        return impl_slice_mask
    raise BodoError(
        f'setitem for IntegerArray with indexing type {idx} not supported.')


@overload(len, no_unliteral=True)
def overload_int_arr_len(A):
    if isinstance(A, IntegerArrayType):
        return lambda A: len(A._data)


@overload_attribute(IntegerArrayType, 'shape')
def overload_int_arr_shape(A):
    return lambda A: (len(A._data),)


@overload_attribute(IntegerArrayType, 'dtype')
def overload_int_arr_dtype(A):
    dtype_class = getattr(pd, '{}Int{}Dtype'.format('' if A.dtype.signed else
        'U', A.dtype.bitwidth))
    return lambda A: dtype_class()


@overload_attribute(IntegerArrayType, 'ndim')
def overload_int_arr_ndim(A):
    return lambda A: 1


@overload_attribute(IntegerArrayType, 'nbytes')
def int_arr_nbytes_overload(A):
    return lambda A: A._data.nbytes + A._null_bitmap.nbytes


@overload_method(IntegerArrayType, 'copy', no_unliteral=True)
def overload_int_arr_copy(A, dtype=None):
    if not is_overload_none(dtype):
        return lambda A, dtype=None: A.astype(dtype, copy=True)
    else:
        return lambda A, dtype=None: bodo.libs.int_arr_ext.init_integer_array(
            bodo.libs.int_arr_ext.get_int_arr_data(A).copy(), bodo.libs.
            int_arr_ext.get_int_arr_bitmap(A).copy())


@overload_method(IntegerArrayType, 'astype', no_unliteral=True)
def overload_int_arr_astype(A, dtype, copy=True):
    if dtype == types.unicode_type:
        raise_bodo_error(
            "IntegerArray.astype(): 'dtype' when passed as string must be a constant value"
            )
    if isinstance(dtype, types.NumberClass):
        dtype = dtype.dtype
    if isinstance(dtype, IntDtype) and A.dtype == dtype.dtype:
        if is_overload_false(copy):
            return lambda A, dtype, copy=True: A
        elif is_overload_true(copy):
            return lambda A, dtype, copy=True: A.copy()
        else:

            def impl(A, dtype, copy=True):
                if copy:
                    return A.copy()
                else:
                    return A
            return impl
    if isinstance(dtype, IntDtype):
        np_dtype = dtype.dtype
        return (lambda A, dtype, copy=True: bodo.libs.int_arr_ext.
            init_integer_array(bodo.libs.int_arr_ext.get_int_arr_data(A).
            astype(np_dtype), bodo.libs.int_arr_ext.get_int_arr_bitmap(A).
            copy()))
    nb_dtype = parse_dtype(dtype, 'IntegerArray.astype')
    if isinstance(nb_dtype, types.Float):

        def impl_float(A, dtype, copy=True):
            data = bodo.libs.int_arr_ext.get_int_arr_data(A)
            n = len(data)
            gsv__xiyu = np.empty(n, nb_dtype)
            for i in numba.parfors.parfor.internal_prange(n):
                gsv__xiyu[i] = data[i]
                if bodo.libs.array_kernels.isna(A, i):
                    gsv__xiyu[i] = np.nan
            return gsv__xiyu
        return impl_float
    return lambda A, dtype, copy=True: bodo.libs.int_arr_ext.get_int_arr_data(A
        ).astype(nb_dtype)


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def apply_null_mask(arr, bitmap, mask_fill, inplace):
    assert isinstance(arr, types.Array)
    if isinstance(arr.dtype, types.Integer):
        if is_overload_none(inplace):
            return (lambda arr, bitmap, mask_fill, inplace: bodo.libs.
                int_arr_ext.init_integer_array(arr, bitmap.copy()))
        else:
            return (lambda arr, bitmap, mask_fill, inplace: bodo.libs.
                int_arr_ext.init_integer_array(arr, bitmap))
    if isinstance(arr.dtype, types.Float):

        def impl(arr, bitmap, mask_fill, inplace):
            n = len(arr)
            for i in numba.parfors.parfor.internal_prange(n):
                if not bodo.libs.int_arr_ext.get_bit_bitmap_arr(bitmap, i):
                    arr[i] = np.nan
            return arr
        return impl
    if arr.dtype == types.bool_:

        def impl_bool(arr, bitmap, mask_fill, inplace):
            n = len(arr)
            for i in numba.parfors.parfor.internal_prange(n):
                if not bodo.libs.int_arr_ext.get_bit_bitmap_arr(bitmap, i):
                    arr[i] = mask_fill
            return arr
        return impl_bool
    return lambda arr, bitmap, mask_fill, inplace: arr


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def merge_bitmaps(B1, B2, n, inplace):
    assert B1 == types.Array(types.uint8, 1, 'C')
    assert B2 == types.Array(types.uint8, 1, 'C')
    if not is_overload_none(inplace):

        def impl_inplace(B1, B2, n, inplace):
            for i in numba.parfors.parfor.internal_prange(n):
                lar__loucr = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B1, i)
                lvl__wvht = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B2, i)
                jcsu__nhh = lar__loucr & lvl__wvht
                bodo.libs.int_arr_ext.set_bit_to_arr(B1, i, jcsu__nhh)
            return B1
        return impl_inplace

    def impl(B1, B2, n, inplace):
        numba.parfors.parfor.init_prange()
        xztn__ptoq = n + 7 >> 3
        gsv__xiyu = np.empty(xztn__ptoq, np.uint8)
        for i in numba.parfors.parfor.internal_prange(n):
            lar__loucr = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B1, i)
            lvl__wvht = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B2, i)
            jcsu__nhh = lar__loucr & lvl__wvht
            bodo.libs.int_arr_ext.set_bit_to_arr(gsv__xiyu, i, jcsu__nhh)
        return gsv__xiyu
    return impl


ufunc_aliases = {'subtract': 'sub', 'multiply': 'mul', 'floor_divide':
    'floordiv', 'true_divide': 'truediv', 'power': 'pow', 'remainder':
    'mod', 'divide': 'div', 'equal': 'eq', 'not_equal': 'ne', 'less': 'lt',
    'less_equal': 'le', 'greater': 'gt', 'greater_equal': 'ge'}


def create_op_overload(op, n_inputs):
    if n_inputs == 1:

        def overload_int_arr_op_nin_1(A):
            if isinstance(A, IntegerArrayType):
                return get_nullable_array_unary_impl(op, A)
        return overload_int_arr_op_nin_1
    elif n_inputs == 2:

        def overload_series_op_nin_2(lhs, rhs):
            if isinstance(lhs, IntegerArrayType) or isinstance(rhs,
                IntegerArrayType):
                return get_nullable_array_binary_impl(op, lhs, rhs)
        return overload_series_op_nin_2
    else:
        raise RuntimeError(
            "Don't know how to register ufuncs from ufunc_db with arity > 2")


def _install_np_ufuncs():
    import numba.np.ufunc_db
    for ith__mbzsi in numba.np.ufunc_db.get_ufuncs():
        qtmk__skne = create_op_overload(ith__mbzsi, ith__mbzsi.nin)
        overload(ith__mbzsi, no_unliteral=True)(qtmk__skne)


_install_np_ufuncs()
skips = [operator.lt, operator.le, operator.eq, operator.ne, operator.gt,
    operator.ge, operator.add, operator.sub, operator.mul, operator.truediv,
    operator.floordiv, operator.pow, operator.mod]


def _install_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesArrayOperator._op_map.keys():
        if op in skips:
            continue
        qtmk__skne = create_op_overload(op, 2)
        overload(op)(qtmk__skne)


_install_binary_ops()


def _install_inplace_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesInplaceArrayOperator._op_map.keys(
        ):
        qtmk__skne = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(qtmk__skne)


_install_inplace_binary_ops()


def _install_unary_ops():
    for op in (operator.neg, operator.invert, operator.pos):
        qtmk__skne = create_op_overload(op, 1)
        overload(op, no_unliteral=True)(qtmk__skne)


_install_unary_ops()


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_int_arr_data_tup(arrs):
    clgov__jva = len(arrs.types)
    oyl__ctmj = 'def f(arrs):\n'
    hoc__drfe = ', '.join('arrs[{}]._data'.format(i) for i in range(clgov__jva)
        )
    oyl__ctmj += '  return ({}{})\n'.format(hoc__drfe, ',' if clgov__jva ==
        1 else '')
    glv__bfta = {}
    exec(oyl__ctmj, {}, glv__bfta)
    impl = glv__bfta['f']
    return impl


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def concat_bitmap_tup(arrs):
    clgov__jva = len(arrs.types)
    ieeir__xes = '+'.join('len(arrs[{}]._data)'.format(i) for i in range(
        clgov__jva))
    oyl__ctmj = 'def f(arrs):\n'
    oyl__ctmj += '  n = {}\n'.format(ieeir__xes)
    oyl__ctmj += '  n_bytes = (n + 7) >> 3\n'
    oyl__ctmj += '  new_mask = np.empty(n_bytes, np.uint8)\n'
    oyl__ctmj += '  curr_bit = 0\n'
    for i in range(clgov__jva):
        oyl__ctmj += '  old_mask = arrs[{}]._null_bitmap\n'.format(i)
        oyl__ctmj += '  for j in range(len(arrs[{}])):\n'.format(i)
        oyl__ctmj += (
            '    bit = bodo.libs.int_arr_ext.get_bit_bitmap_arr(old_mask, j)\n'
            )
        oyl__ctmj += (
            '    bodo.libs.int_arr_ext.set_bit_to_arr(new_mask, curr_bit, bit)\n'
            )
        oyl__ctmj += '    curr_bit += 1\n'
    oyl__ctmj += '  return new_mask\n'
    glv__bfta = {}
    exec(oyl__ctmj, {'np': np, 'bodo': bodo}, glv__bfta)
    impl = glv__bfta['f']
    return impl


@overload_method(IntegerArrayType, 'sum', no_unliteral=True)
def overload_int_arr_sum(A, skipna=True, min_count=0):
    mmk__wgs = dict(skipna=skipna, min_count=min_count)
    wcs__fzm = dict(skipna=True, min_count=0)
    check_unsupported_args('IntegerArray.sum', mmk__wgs, wcs__fzm)

    def impl(A, skipna=True, min_count=0):
        numba.parfors.parfor.init_prange()
        s = 0
        for i in numba.parfors.parfor.internal_prange(len(A)):
            val = 0
            if not bodo.libs.array_kernels.isna(A, i):
                val = A[i]
            s += val
        return s
    return impl


@overload_method(IntegerArrayType, 'unique', no_unliteral=True)
def overload_unique(A):
    dtype = A.dtype

    def impl_int_arr(A):
        data = []
        plj__qsefa = []
        tlxc__nbvj = False
        s = set()
        for i in range(len(A)):
            val = A[i]
            if bodo.libs.array_kernels.isna(A, i):
                if not tlxc__nbvj:
                    data.append(dtype(1))
                    plj__qsefa.append(False)
                    tlxc__nbvj = True
                continue
            if val not in s:
                s.add(val)
                data.append(val)
                plj__qsefa.append(True)
        aiuzm__gbeci = np.array(data)
        n = len(aiuzm__gbeci)
        xztn__ptoq = n + 7 >> 3
        vgj__ysqoc = np.empty(xztn__ptoq, np.uint8)
        for nmis__urj in range(n):
            set_bit_to_arr(vgj__ysqoc, nmis__urj, plj__qsefa[nmis__urj])
        return init_integer_array(aiuzm__gbeci, vgj__ysqoc)
    return impl_int_arr


def get_nullable_array_unary_impl(op, A):
    yvo__swmv = numba.core.registry.cpu_target.typing_context
    dtfph__rrb = yvo__swmv.resolve_function_type(op, (types.Array(A.dtype, 
        1, 'C'),), {}).return_type
    dtfph__rrb = to_nullable_type(dtfph__rrb)

    def impl(A):
        n = len(A)
        kkw__cfx = bodo.utils.utils.alloc_type(n, dtfph__rrb, None)
        for i in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(A, i):
                bodo.libs.array_kernels.setna(kkw__cfx, i)
                continue
            kkw__cfx[i] = op(A[i])
        return kkw__cfx
    return impl


def get_nullable_array_binary_impl(op, lhs, rhs):
    inplace = (op in numba.core.typing.npydecl.
        NumpyRulesInplaceArrayOperator._op_map.keys())
    mtarv__hfh = isinstance(lhs, (types.Number, types.Boolean))
    awx__hnw = isinstance(rhs, (types.Number, types.Boolean))
    bss__ryx = types.Array(getattr(lhs, 'dtype', lhs), 1, 'C')
    fyc__bnh = types.Array(getattr(rhs, 'dtype', rhs), 1, 'C')
    yvo__swmv = numba.core.registry.cpu_target.typing_context
    dtfph__rrb = yvo__swmv.resolve_function_type(op, (bss__ryx, fyc__bnh), {}
        ).return_type
    dtfph__rrb = to_nullable_type(dtfph__rrb)
    if op in (operator.truediv, operator.itruediv):
        op = np.true_divide
    elif op in (operator.floordiv, operator.ifloordiv):
        op = np.floor_divide
    mrz__ajov = 'lhs' if mtarv__hfh else 'lhs[i]'
    xiei__cvtjo = 'rhs' if awx__hnw else 'rhs[i]'
    brjia__sgopw = ('False' if mtarv__hfh else
        'bodo.libs.array_kernels.isna(lhs, i)')
    tgw__xwa = 'False' if awx__hnw else 'bodo.libs.array_kernels.isna(rhs, i)'
    oyl__ctmj = 'def impl(lhs, rhs):\n'
    oyl__ctmj += '  n = len({})\n'.format('lhs' if not mtarv__hfh else 'rhs')
    if inplace:
        oyl__ctmj += '  out_arr = {}\n'.format('lhs' if not mtarv__hfh else
            'rhs')
    else:
        oyl__ctmj += (
            '  out_arr = bodo.utils.utils.alloc_type(n, ret_dtype, None)\n')
    oyl__ctmj += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    oyl__ctmj += '    if ({}\n'.format(brjia__sgopw)
    oyl__ctmj += '        or {}):\n'.format(tgw__xwa)
    oyl__ctmj += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    oyl__ctmj += '      continue\n'
    oyl__ctmj += (
        '    out_arr[i] = bodo.utils.conversion.unbox_if_timestamp(op({}, {}))\n'
        .format(mrz__ajov, xiei__cvtjo))
    oyl__ctmj += '  return out_arr\n'
    glv__bfta = {}
    exec(oyl__ctmj, {'bodo': bodo, 'numba': numba, 'np': np, 'ret_dtype':
        dtfph__rrb, 'op': op}, glv__bfta)
    impl = glv__bfta['impl']
    return impl


def get_int_array_op_pd_td(op):

    def impl(lhs, rhs):
        mtarv__hfh = lhs in [pd_timedelta_type]
        awx__hnw = rhs in [pd_timedelta_type]
        if mtarv__hfh:

            def impl(lhs, rhs):
                n = len(rhs)
                kkw__cfx = np.empty(n, 'timedelta64[ns]')
                for i in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(rhs, i):
                        bodo.libs.array_kernels.setna(kkw__cfx, i)
                        continue
                    kkw__cfx[i] = bodo.utils.conversion.unbox_if_timestamp(op
                        (lhs, rhs[i]))
                return kkw__cfx
            return impl
        elif awx__hnw:

            def impl(lhs, rhs):
                n = len(lhs)
                kkw__cfx = np.empty(n, 'timedelta64[ns]')
                for i in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(lhs, i):
                        bodo.libs.array_kernels.setna(kkw__cfx, i)
                        continue
                    kkw__cfx[i] = bodo.utils.conversion.unbox_if_timestamp(op
                        (lhs[i], rhs))
                return kkw__cfx
            return impl
    return impl
