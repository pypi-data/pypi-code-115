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
        krmp__uyndo = [('data', types.Array(fe_type.dtype, 1, 'C')), (
            'null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, krmp__uyndo)


make_attribute_wrapper(IntegerArrayType, 'data', '_data')
make_attribute_wrapper(IntegerArrayType, 'null_bitmap', '_null_bitmap')


@typeof_impl.register(pd.arrays.IntegerArray)
def _typeof_pd_int_array(val, c):
    kzr__uoyh = 8 * val.dtype.itemsize
    iruks__gkaw = '' if val.dtype.kind == 'i' else 'u'
    dtype = getattr(types, '{}int{}'.format(iruks__gkaw, kzr__uoyh))
    return IntegerArrayType(dtype)


class IntDtype(types.Number):

    def __init__(self, dtype):
        assert isinstance(dtype, types.Integer)
        self.dtype = dtype
        wfopa__qfl = '{}Int{}Dtype()'.format('' if dtype.signed else 'U',
            dtype.bitwidth)
        super(IntDtype, self).__init__(wfopa__qfl)


register_model(IntDtype)(models.OpaqueModel)


@box(IntDtype)
def box_intdtype(typ, val, c):
    fde__iyx = c.context.insert_const_string(c.builder.module, 'pandas')
    trr__zaxx = c.pyapi.import_module_noblock(fde__iyx)
    drmwn__oqh = c.pyapi.call_method(trr__zaxx, str(typ)[:-2], ())
    c.pyapi.decref(trr__zaxx)
    return drmwn__oqh


@unbox(IntDtype)
def unbox_intdtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


def typeof_pd_int_dtype(val, c):
    kzr__uoyh = 8 * val.itemsize
    iruks__gkaw = '' if val.kind == 'i' else 'u'
    dtype = getattr(types, '{}int{}'.format(iruks__gkaw, kzr__uoyh))
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
    wfju__nxix = n + 7 >> 3
    wse__zafw = np.empty(wfju__nxix, np.uint8)
    for i in range(n):
        dodfm__hda = i // 8
        wse__zafw[dodfm__hda] ^= np.uint8(-np.uint8(not mask_arr[i]) ^
            wse__zafw[dodfm__hda]) & kBitmask[i % 8]
    return wse__zafw


@unbox(IntegerArrayType)
def unbox_int_array(typ, obj, c):
    gclkv__zfls = c.pyapi.call_method(obj, '__len__', ())
    n = c.pyapi.long_as_longlong(gclkv__zfls)
    c.pyapi.decref(gclkv__zfls)
    kjhhg__yfx = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    wfju__nxix = c.builder.udiv(c.builder.add(n, lir.Constant(lir.IntType(
        64), 7)), lir.Constant(lir.IntType(64), 8))
    bqzm__xpf = bodo.utils.utils._empty_nd_impl(c.context, c.builder, types
        .Array(types.uint8, 1, 'C'), [wfju__nxix])
    zgwjs__gtlso = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
        as_pointer()])
    driz__nkwjk = cgutils.get_or_insert_function(c.builder.module,
        zgwjs__gtlso, name='is_pd_int_array')
    eepc__osl = c.builder.call(driz__nkwjk, [obj])
    xbnzs__hftk = c.builder.icmp_unsigned('!=', eepc__osl, eepc__osl.type(0))
    with c.builder.if_else(xbnzs__hftk) as (xpd__mxlu, kuu__xafdv):
        with xpd__mxlu:
            yvec__oegl = c.pyapi.object_getattr_string(obj, '_data')
            kjhhg__yfx.data = c.pyapi.to_native_value(types.Array(typ.dtype,
                1, 'C'), yvec__oegl).value
            bdc__rqpr = c.pyapi.object_getattr_string(obj, '_mask')
            mask_arr = c.pyapi.to_native_value(types.Array(types.bool_, 1,
                'C'), bdc__rqpr).value
            c.pyapi.decref(yvec__oegl)
            c.pyapi.decref(bdc__rqpr)
            hmbx__mqm = c.context.make_array(types.Array(types.bool_, 1, 'C'))(
                c.context, c.builder, mask_arr)
            zgwjs__gtlso = lir.FunctionType(lir.VoidType(), [lir.IntType(8)
                .as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
            driz__nkwjk = cgutils.get_or_insert_function(c.builder.module,
                zgwjs__gtlso, name='mask_arr_to_bitmap')
            c.builder.call(driz__nkwjk, [bqzm__xpf.data, hmbx__mqm.data, n])
            c.context.nrt.decref(c.builder, types.Array(types.bool_, 1, 'C'
                ), mask_arr)
        with kuu__xafdv:
            lipne__nwv = bodo.utils.utils._empty_nd_impl(c.context, c.
                builder, types.Array(typ.dtype, 1, 'C'), [n])
            zgwjs__gtlso = lir.FunctionType(lir.IntType(32), [lir.IntType(8
                ).as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8)
                .as_pointer()])
            xhdxr__aqnce = cgutils.get_or_insert_function(c.builder.module,
                zgwjs__gtlso, name='int_array_from_sequence')
            c.builder.call(xhdxr__aqnce, [obj, c.builder.bitcast(lipne__nwv
                .data, lir.IntType(8).as_pointer()), bqzm__xpf.data])
            kjhhg__yfx.data = lipne__nwv._getvalue()
    kjhhg__yfx.null_bitmap = bqzm__xpf._getvalue()
    mscf__pxbg = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(kjhhg__yfx._getvalue(), is_error=mscf__pxbg)


@box(IntegerArrayType)
def box_int_arr(typ, val, c):
    kjhhg__yfx = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    data = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        kjhhg__yfx.data, c.env_manager)
    uybk__rwlh = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, kjhhg__yfx.null_bitmap).data
    gclkv__zfls = c.pyapi.call_method(data, '__len__', ())
    n = c.pyapi.long_as_longlong(gclkv__zfls)
    fde__iyx = c.context.insert_const_string(c.builder.module, 'numpy')
    zlc__gcymx = c.pyapi.import_module_noblock(fde__iyx)
    mgv__mmtm = c.pyapi.object_getattr_string(zlc__gcymx, 'bool_')
    mask_arr = c.pyapi.call_method(zlc__gcymx, 'empty', (gclkv__zfls,
        mgv__mmtm))
    ihu__mvwa = c.pyapi.object_getattr_string(mask_arr, 'ctypes')
    ehmgy__xadq = c.pyapi.object_getattr_string(ihu__mvwa, 'data')
    xeo__olqw = c.builder.inttoptr(c.pyapi.long_as_longlong(ehmgy__xadq),
        lir.IntType(8).as_pointer())
    with cgutils.for_range(c.builder, n) as damhw__symyc:
        i = damhw__symyc.index
        ell__sujlc = c.builder.lshr(i, lir.Constant(lir.IntType(64), 3))
        vken__gubxg = c.builder.load(cgutils.gep(c.builder, uybk__rwlh,
            ell__sujlc))
        yjt__qbcy = c.builder.trunc(c.builder.and_(i, lir.Constant(lir.
            IntType(64), 7)), lir.IntType(8))
        val = c.builder.and_(c.builder.lshr(vken__gubxg, yjt__qbcy), lir.
            Constant(lir.IntType(8), 1))
        val = c.builder.xor(val, lir.Constant(lir.IntType(8), 1))
        rvj__mmmx = cgutils.gep(c.builder, xeo__olqw, i)
        c.builder.store(val, rvj__mmmx)
    c.context.nrt.decref(c.builder, types.Array(types.uint8, 1, 'C'),
        kjhhg__yfx.null_bitmap)
    fde__iyx = c.context.insert_const_string(c.builder.module, 'pandas')
    trr__zaxx = c.pyapi.import_module_noblock(fde__iyx)
    xdpkg__wxrro = c.pyapi.object_getattr_string(trr__zaxx, 'arrays')
    drmwn__oqh = c.pyapi.call_method(xdpkg__wxrro, 'IntegerArray', (data,
        mask_arr))
    c.pyapi.decref(trr__zaxx)
    c.pyapi.decref(gclkv__zfls)
    c.pyapi.decref(zlc__gcymx)
    c.pyapi.decref(mgv__mmtm)
    c.pyapi.decref(ihu__mvwa)
    c.pyapi.decref(ehmgy__xadq)
    c.pyapi.decref(xdpkg__wxrro)
    c.pyapi.decref(data)
    c.pyapi.decref(mask_arr)
    return drmwn__oqh


@intrinsic
def init_integer_array(typingctx, data, null_bitmap=None):
    assert isinstance(data, types.Array)
    assert null_bitmap == types.Array(types.uint8, 1, 'C')

    def codegen(context, builder, signature, args):
        yke__ehm, djf__xvwfd = args
        kjhhg__yfx = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        kjhhg__yfx.data = yke__ehm
        kjhhg__yfx.null_bitmap = djf__xvwfd
        context.nrt.incref(builder, signature.args[0], yke__ehm)
        context.nrt.incref(builder, signature.args[1], djf__xvwfd)
        return kjhhg__yfx._getvalue()
    dddbk__pmwzw = IntegerArrayType(data.dtype)
    pmpx__osghe = dddbk__pmwzw(data, null_bitmap)
    return pmpx__osghe, codegen


@lower_constant(IntegerArrayType)
def lower_constant_int_arr(context, builder, typ, pyval):
    n = len(pyval)
    ggm__abdf = np.empty(n, pyval.dtype.type)
    jucxu__itdr = np.empty(n + 7 >> 3, np.uint8)
    for i, s in enumerate(pyval):
        rmc__ncqf = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(jucxu__itdr, i, int(not rmc__ncqf)
            )
        if not rmc__ncqf:
            ggm__abdf[i] = s
    ijf__fag = context.get_constant_generic(builder, types.Array(typ.dtype,
        1, 'C'), ggm__abdf)
    qny__kii = context.get_constant_generic(builder, types.Array(types.
        uint8, 1, 'C'), jucxu__itdr)
    return lir.Constant.literal_struct([ijf__fag, qny__kii])


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_int_arr_data(A):
    return lambda A: A._data


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_int_arr_bitmap(A):
    return lambda A: A._null_bitmap


def get_int_arr_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    ldok__yvm = args[0]
    if equiv_set.has_shape(ldok__yvm):
        return ArrayAnalysis.AnalyzeResult(shape=ldok__yvm, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_libs_int_arr_ext_get_int_arr_data = (
    get_int_arr_data_equiv)


def init_integer_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    ldok__yvm = args[0]
    if equiv_set.has_shape(ldok__yvm):
        return ArrayAnalysis.AnalyzeResult(shape=ldok__yvm, pre=[])
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
    ggm__abdf = np.empty(n, dtype)
    twn__lub = np.empty(n + 7 >> 3, dtype=np.uint8)
    return init_integer_array(ggm__abdf, twn__lub)


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
            xtyaa__dhpxy, snaa__xvoh = array_getitem_bool_index(A, ind)
            return init_integer_array(xtyaa__dhpxy, snaa__xvoh)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            xtyaa__dhpxy, snaa__xvoh = array_getitem_int_index(A, ind)
            return init_integer_array(xtyaa__dhpxy, snaa__xvoh)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            xtyaa__dhpxy, snaa__xvoh = array_getitem_slice_index(A, ind)
            return init_integer_array(xtyaa__dhpxy, snaa__xvoh)
        return impl_slice
    raise BodoError(
        f'getitem for IntegerArray with indexing type {ind} not supported.')


@overload(operator.setitem, no_unliteral=True)
def int_arr_setitem(A, idx, val):
    if not isinstance(A, IntegerArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    kehm__hbpy = (
        f"setitem for IntegerArray with indexing type {idx} received an incorrect 'value' type {val}."
        )
    itiu__rkm = isinstance(val, (types.Integer, types.Boolean))
    if isinstance(idx, types.Integer):
        if itiu__rkm:

            def impl_scalar(A, idx, val):
                A._data[idx] = val
                bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap, idx, 1)
            return impl_scalar
        else:
            raise BodoError(kehm__hbpy)
    if not (is_iterable_type(val) and isinstance(val.dtype, (types.Integer,
        types.Boolean)) or itiu__rkm):
        raise BodoError(kehm__hbpy)
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
            hrbr__urg = np.empty(n, nb_dtype)
            for i in numba.parfors.parfor.internal_prange(n):
                hrbr__urg[i] = data[i]
                if bodo.libs.array_kernels.isna(A, i):
                    hrbr__urg[i] = np.nan
            return hrbr__urg
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
                kyfa__sxkdp = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B1, i)
                mqxxx__azxg = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B2, i)
                ilbu__qxc = kyfa__sxkdp & mqxxx__azxg
                bodo.libs.int_arr_ext.set_bit_to_arr(B1, i, ilbu__qxc)
            return B1
        return impl_inplace

    def impl(B1, B2, n, inplace):
        numba.parfors.parfor.init_prange()
        wfju__nxix = n + 7 >> 3
        hrbr__urg = np.empty(wfju__nxix, np.uint8)
        for i in numba.parfors.parfor.internal_prange(n):
            kyfa__sxkdp = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B1, i)
            mqxxx__azxg = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B2, i)
            ilbu__qxc = kyfa__sxkdp & mqxxx__azxg
            bodo.libs.int_arr_ext.set_bit_to_arr(hrbr__urg, i, ilbu__qxc)
        return hrbr__urg
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
    for vcgyr__rnz in numba.np.ufunc_db.get_ufuncs():
        pdiv__hdr = create_op_overload(vcgyr__rnz, vcgyr__rnz.nin)
        overload(vcgyr__rnz, no_unliteral=True)(pdiv__hdr)


_install_np_ufuncs()
skips = [operator.lt, operator.le, operator.eq, operator.ne, operator.gt,
    operator.ge, operator.add, operator.sub, operator.mul, operator.truediv,
    operator.floordiv, operator.pow, operator.mod]


def _install_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesArrayOperator._op_map.keys():
        if op in skips:
            continue
        pdiv__hdr = create_op_overload(op, 2)
        overload(op)(pdiv__hdr)


_install_binary_ops()


def _install_inplace_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesInplaceArrayOperator._op_map.keys(
        ):
        pdiv__hdr = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(pdiv__hdr)


_install_inplace_binary_ops()


def _install_unary_ops():
    for op in (operator.neg, operator.invert, operator.pos):
        pdiv__hdr = create_op_overload(op, 1)
        overload(op, no_unliteral=True)(pdiv__hdr)


_install_unary_ops()


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_int_arr_data_tup(arrs):
    bajpa__wzoca = len(arrs.types)
    kzj__iph = 'def f(arrs):\n'
    drmwn__oqh = ', '.join('arrs[{}]._data'.format(i) for i in range(
        bajpa__wzoca))
    kzj__iph += '  return ({}{})\n'.format(drmwn__oqh, ',' if bajpa__wzoca ==
        1 else '')
    fdlq__izidh = {}
    exec(kzj__iph, {}, fdlq__izidh)
    impl = fdlq__izidh['f']
    return impl


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def concat_bitmap_tup(arrs):
    bajpa__wzoca = len(arrs.types)
    uzl__dizp = '+'.join('len(arrs[{}]._data)'.format(i) for i in range(
        bajpa__wzoca))
    kzj__iph = 'def f(arrs):\n'
    kzj__iph += '  n = {}\n'.format(uzl__dizp)
    kzj__iph += '  n_bytes = (n + 7) >> 3\n'
    kzj__iph += '  new_mask = np.empty(n_bytes, np.uint8)\n'
    kzj__iph += '  curr_bit = 0\n'
    for i in range(bajpa__wzoca):
        kzj__iph += '  old_mask = arrs[{}]._null_bitmap\n'.format(i)
        kzj__iph += '  for j in range(len(arrs[{}])):\n'.format(i)
        kzj__iph += (
            '    bit = bodo.libs.int_arr_ext.get_bit_bitmap_arr(old_mask, j)\n'
            )
        kzj__iph += (
            '    bodo.libs.int_arr_ext.set_bit_to_arr(new_mask, curr_bit, bit)\n'
            )
        kzj__iph += '    curr_bit += 1\n'
    kzj__iph += '  return new_mask\n'
    fdlq__izidh = {}
    exec(kzj__iph, {'np': np, 'bodo': bodo}, fdlq__izidh)
    impl = fdlq__izidh['f']
    return impl


@overload_method(IntegerArrayType, 'sum', no_unliteral=True)
def overload_int_arr_sum(A, skipna=True, min_count=0):
    cyx__eyyha = dict(skipna=skipna, min_count=min_count)
    lolyu__fsgq = dict(skipna=True, min_count=0)
    check_unsupported_args('IntegerArray.sum', cyx__eyyha, lolyu__fsgq)

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
        yjt__qbcy = []
        ishuf__aqp = False
        s = set()
        for i in range(len(A)):
            val = A[i]
            if bodo.libs.array_kernels.isna(A, i):
                if not ishuf__aqp:
                    data.append(dtype(1))
                    yjt__qbcy.append(False)
                    ishuf__aqp = True
                continue
            if val not in s:
                s.add(val)
                data.append(val)
                yjt__qbcy.append(True)
        xtyaa__dhpxy = np.array(data)
        n = len(xtyaa__dhpxy)
        wfju__nxix = n + 7 >> 3
        snaa__xvoh = np.empty(wfju__nxix, np.uint8)
        for prk__zpl in range(n):
            set_bit_to_arr(snaa__xvoh, prk__zpl, yjt__qbcy[prk__zpl])
        return init_integer_array(xtyaa__dhpxy, snaa__xvoh)
    return impl_int_arr


def get_nullable_array_unary_impl(op, A):
    iuh__vtr = numba.core.registry.cpu_target.typing_context
    vxra__wfc = iuh__vtr.resolve_function_type(op, (types.Array(A.dtype, 1,
        'C'),), {}).return_type
    vxra__wfc = to_nullable_type(vxra__wfc)

    def impl(A):
        n = len(A)
        acm__euhgn = bodo.utils.utils.alloc_type(n, vxra__wfc, None)
        for i in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(A, i):
                bodo.libs.array_kernels.setna(acm__euhgn, i)
                continue
            acm__euhgn[i] = op(A[i])
        return acm__euhgn
    return impl


def get_nullable_array_binary_impl(op, lhs, rhs):
    inplace = (op in numba.core.typing.npydecl.
        NumpyRulesInplaceArrayOperator._op_map.keys())
    jwrhk__oyv = isinstance(lhs, (types.Number, types.Boolean))
    txfad__gyubx = isinstance(rhs, (types.Number, types.Boolean))
    stwfk__ism = types.Array(getattr(lhs, 'dtype', lhs), 1, 'C')
    zduac__knc = types.Array(getattr(rhs, 'dtype', rhs), 1, 'C')
    iuh__vtr = numba.core.registry.cpu_target.typing_context
    vxra__wfc = iuh__vtr.resolve_function_type(op, (stwfk__ism, zduac__knc), {}
        ).return_type
    vxra__wfc = to_nullable_type(vxra__wfc)
    if op in (operator.truediv, operator.itruediv):
        op = np.true_divide
    elif op in (operator.floordiv, operator.ifloordiv):
        op = np.floor_divide
    xocb__qlgbq = 'lhs' if jwrhk__oyv else 'lhs[i]'
    tmje__myt = 'rhs' if txfad__gyubx else 'rhs[i]'
    rie__ugt = ('False' if jwrhk__oyv else
        'bodo.libs.array_kernels.isna(lhs, i)')
    ulz__ptc = ('False' if txfad__gyubx else
        'bodo.libs.array_kernels.isna(rhs, i)')
    kzj__iph = 'def impl(lhs, rhs):\n'
    kzj__iph += '  n = len({})\n'.format('lhs' if not jwrhk__oyv else 'rhs')
    if inplace:
        kzj__iph += '  out_arr = {}\n'.format('lhs' if not jwrhk__oyv else
            'rhs')
    else:
        kzj__iph += (
            '  out_arr = bodo.utils.utils.alloc_type(n, ret_dtype, None)\n')
    kzj__iph += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    kzj__iph += '    if ({}\n'.format(rie__ugt)
    kzj__iph += '        or {}):\n'.format(ulz__ptc)
    kzj__iph += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    kzj__iph += '      continue\n'
    kzj__iph += (
        '    out_arr[i] = bodo.utils.conversion.unbox_if_timestamp(op({}, {}))\n'
        .format(xocb__qlgbq, tmje__myt))
    kzj__iph += '  return out_arr\n'
    fdlq__izidh = {}
    exec(kzj__iph, {'bodo': bodo, 'numba': numba, 'np': np, 'ret_dtype':
        vxra__wfc, 'op': op}, fdlq__izidh)
    impl = fdlq__izidh['impl']
    return impl


def get_int_array_op_pd_td(op):

    def impl(lhs, rhs):
        jwrhk__oyv = lhs in [pd_timedelta_type]
        txfad__gyubx = rhs in [pd_timedelta_type]
        if jwrhk__oyv:

            def impl(lhs, rhs):
                n = len(rhs)
                acm__euhgn = np.empty(n, 'timedelta64[ns]')
                for i in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(rhs, i):
                        bodo.libs.array_kernels.setna(acm__euhgn, i)
                        continue
                    acm__euhgn[i] = bodo.utils.conversion.unbox_if_timestamp(op
                        (lhs, rhs[i]))
                return acm__euhgn
            return impl
        elif txfad__gyubx:

            def impl(lhs, rhs):
                n = len(lhs)
                acm__euhgn = np.empty(n, 'timedelta64[ns]')
                for i in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(lhs, i):
                        bodo.libs.array_kernels.setna(acm__euhgn, i)
                        continue
                    acm__euhgn[i] = bodo.utils.conversion.unbox_if_timestamp(op
                        (lhs[i], rhs))
                return acm__euhgn
            return impl
    return impl
