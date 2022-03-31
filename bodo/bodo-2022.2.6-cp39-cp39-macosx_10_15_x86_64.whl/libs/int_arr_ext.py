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
        fpa__vacii = [('data', types.Array(fe_type.dtype, 1, 'C')), (
            'null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, fpa__vacii)


make_attribute_wrapper(IntegerArrayType, 'data', '_data')
make_attribute_wrapper(IntegerArrayType, 'null_bitmap', '_null_bitmap')


@typeof_impl.register(pd.arrays.IntegerArray)
def _typeof_pd_int_array(val, c):
    vslms__psole = 8 * val.dtype.itemsize
    qjmae__rcpky = '' if val.dtype.kind == 'i' else 'u'
    dtype = getattr(types, '{}int{}'.format(qjmae__rcpky, vslms__psole))
    return IntegerArrayType(dtype)


class IntDtype(types.Number):

    def __init__(self, dtype):
        assert isinstance(dtype, types.Integer)
        self.dtype = dtype
        lgbs__thyv = '{}Int{}Dtype()'.format('' if dtype.signed else 'U',
            dtype.bitwidth)
        super(IntDtype, self).__init__(lgbs__thyv)


register_model(IntDtype)(models.OpaqueModel)


@box(IntDtype)
def box_intdtype(typ, val, c):
    ovxtm__phi = c.context.insert_const_string(c.builder.module, 'pandas')
    wqwqy__npill = c.pyapi.import_module_noblock(ovxtm__phi)
    dojzj__khk = c.pyapi.call_method(wqwqy__npill, str(typ)[:-2], ())
    c.pyapi.decref(wqwqy__npill)
    return dojzj__khk


@unbox(IntDtype)
def unbox_intdtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


def typeof_pd_int_dtype(val, c):
    vslms__psole = 8 * val.itemsize
    qjmae__rcpky = '' if val.kind == 'i' else 'u'
    dtype = getattr(types, '{}int{}'.format(qjmae__rcpky, vslms__psole))
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
    jysig__fxhy = n + 7 >> 3
    mcufd__ijw = np.empty(jysig__fxhy, np.uint8)
    for i in range(n):
        rltbv__zwlk = i // 8
        mcufd__ijw[rltbv__zwlk] ^= np.uint8(-np.uint8(not mask_arr[i]) ^
            mcufd__ijw[rltbv__zwlk]) & kBitmask[i % 8]
    return mcufd__ijw


@unbox(IntegerArrayType)
def unbox_int_array(typ, obj, c):
    qhjg__mdsi = c.pyapi.call_method(obj, '__len__', ())
    n = c.pyapi.long_as_longlong(qhjg__mdsi)
    c.pyapi.decref(qhjg__mdsi)
    zeg__ufyr = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    jysig__fxhy = c.builder.udiv(c.builder.add(n, lir.Constant(lir.IntType(
        64), 7)), lir.Constant(lir.IntType(64), 8))
    tdesa__xfy = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        types.Array(types.uint8, 1, 'C'), [jysig__fxhy])
    iqj__vxdpz = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
        as_pointer()])
    qgjr__nay = cgutils.get_or_insert_function(c.builder.module, iqj__vxdpz,
        name='is_pd_int_array')
    nau__nokql = c.builder.call(qgjr__nay, [obj])
    ogow__oxj = c.builder.icmp_unsigned('!=', nau__nokql, nau__nokql.type(0))
    with c.builder.if_else(ogow__oxj) as (slmxd__sxaj, bicg__bvw):
        with slmxd__sxaj:
            mejh__alcy = c.pyapi.object_getattr_string(obj, '_data')
            zeg__ufyr.data = c.pyapi.to_native_value(types.Array(typ.dtype,
                1, 'C'), mejh__alcy).value
            crx__pvesi = c.pyapi.object_getattr_string(obj, '_mask')
            mask_arr = c.pyapi.to_native_value(types.Array(types.bool_, 1,
                'C'), crx__pvesi).value
            c.pyapi.decref(mejh__alcy)
            c.pyapi.decref(crx__pvesi)
            jjs__ile = c.context.make_array(types.Array(types.bool_, 1, 'C'))(c
                .context, c.builder, mask_arr)
            iqj__vxdpz = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
            qgjr__nay = cgutils.get_or_insert_function(c.builder.module,
                iqj__vxdpz, name='mask_arr_to_bitmap')
            c.builder.call(qgjr__nay, [tdesa__xfy.data, jjs__ile.data, n])
            c.context.nrt.decref(c.builder, types.Array(types.bool_, 1, 'C'
                ), mask_arr)
        with bicg__bvw:
            oeolg__aqe = bodo.utils.utils._empty_nd_impl(c.context, c.
                builder, types.Array(typ.dtype, 1, 'C'), [n])
            iqj__vxdpz = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
                as_pointer()])
            xjuu__ejpe = cgutils.get_or_insert_function(c.builder.module,
                iqj__vxdpz, name='int_array_from_sequence')
            c.builder.call(xjuu__ejpe, [obj, c.builder.bitcast(oeolg__aqe.
                data, lir.IntType(8).as_pointer()), tdesa__xfy.data])
            zeg__ufyr.data = oeolg__aqe._getvalue()
    zeg__ufyr.null_bitmap = tdesa__xfy._getvalue()
    ktfv__drsml = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(zeg__ufyr._getvalue(), is_error=ktfv__drsml)


@box(IntegerArrayType)
def box_int_arr(typ, val, c):
    zeg__ufyr = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    data = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        zeg__ufyr.data, c.env_manager)
    bco__ukvic = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, zeg__ufyr.null_bitmap).data
    qhjg__mdsi = c.pyapi.call_method(data, '__len__', ())
    n = c.pyapi.long_as_longlong(qhjg__mdsi)
    ovxtm__phi = c.context.insert_const_string(c.builder.module, 'numpy')
    rqo__ttkxk = c.pyapi.import_module_noblock(ovxtm__phi)
    wdws__jqdig = c.pyapi.object_getattr_string(rqo__ttkxk, 'bool_')
    mask_arr = c.pyapi.call_method(rqo__ttkxk, 'empty', (qhjg__mdsi,
        wdws__jqdig))
    adkz__cgiok = c.pyapi.object_getattr_string(mask_arr, 'ctypes')
    yyw__oil = c.pyapi.object_getattr_string(adkz__cgiok, 'data')
    aoneo__davyi = c.builder.inttoptr(c.pyapi.long_as_longlong(yyw__oil),
        lir.IntType(8).as_pointer())
    with cgutils.for_range(c.builder, n) as sft__cql:
        i = sft__cql.index
        orp__vygve = c.builder.lshr(i, lir.Constant(lir.IntType(64), 3))
        hbouw__wtyd = c.builder.load(cgutils.gep(c.builder, bco__ukvic,
            orp__vygve))
        afr__etp = c.builder.trunc(c.builder.and_(i, lir.Constant(lir.
            IntType(64), 7)), lir.IntType(8))
        val = c.builder.and_(c.builder.lshr(hbouw__wtyd, afr__etp), lir.
            Constant(lir.IntType(8), 1))
        val = c.builder.xor(val, lir.Constant(lir.IntType(8), 1))
        zuljp__fkbt = cgutils.gep(c.builder, aoneo__davyi, i)
        c.builder.store(val, zuljp__fkbt)
    c.context.nrt.decref(c.builder, types.Array(types.uint8, 1, 'C'),
        zeg__ufyr.null_bitmap)
    ovxtm__phi = c.context.insert_const_string(c.builder.module, 'pandas')
    wqwqy__npill = c.pyapi.import_module_noblock(ovxtm__phi)
    ftjh__kfed = c.pyapi.object_getattr_string(wqwqy__npill, 'arrays')
    dojzj__khk = c.pyapi.call_method(ftjh__kfed, 'IntegerArray', (data,
        mask_arr))
    c.pyapi.decref(wqwqy__npill)
    c.pyapi.decref(qhjg__mdsi)
    c.pyapi.decref(rqo__ttkxk)
    c.pyapi.decref(wdws__jqdig)
    c.pyapi.decref(adkz__cgiok)
    c.pyapi.decref(yyw__oil)
    c.pyapi.decref(ftjh__kfed)
    c.pyapi.decref(data)
    c.pyapi.decref(mask_arr)
    return dojzj__khk


@intrinsic
def init_integer_array(typingctx, data, null_bitmap=None):
    assert isinstance(data, types.Array)
    assert null_bitmap == types.Array(types.uint8, 1, 'C')

    def codegen(context, builder, signature, args):
        xrw__ykwe, agg__izxn = args
        zeg__ufyr = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        zeg__ufyr.data = xrw__ykwe
        zeg__ufyr.null_bitmap = agg__izxn
        context.nrt.incref(builder, signature.args[0], xrw__ykwe)
        context.nrt.incref(builder, signature.args[1], agg__izxn)
        return zeg__ufyr._getvalue()
    uqgh__epn = IntegerArrayType(data.dtype)
    qkx__wxkw = uqgh__epn(data, null_bitmap)
    return qkx__wxkw, codegen


@lower_constant(IntegerArrayType)
def lower_constant_int_arr(context, builder, typ, pyval):
    n = len(pyval)
    udd__qlq = np.empty(n, pyval.dtype.type)
    vod__mabp = np.empty(n + 7 >> 3, np.uint8)
    for i, s in enumerate(pyval):
        fueb__wjp = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(vod__mabp, i, int(not fueb__wjp))
        if not fueb__wjp:
            udd__qlq[i] = s
    jru__xoy = context.get_constant_generic(builder, types.Array(typ.dtype,
        1, 'C'), udd__qlq)
    jra__zvthg = context.get_constant_generic(builder, types.Array(types.
        uint8, 1, 'C'), vod__mabp)
    return lir.Constant.literal_struct([jru__xoy, jra__zvthg])


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_int_arr_data(A):
    return lambda A: A._data


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_int_arr_bitmap(A):
    return lambda A: A._null_bitmap


def get_int_arr_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    idgx__szh = args[0]
    if equiv_set.has_shape(idgx__szh):
        return ArrayAnalysis.AnalyzeResult(shape=idgx__szh, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_libs_int_arr_ext_get_int_arr_data = (
    get_int_arr_data_equiv)


def init_integer_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    idgx__szh = args[0]
    if equiv_set.has_shape(idgx__szh):
        return ArrayAnalysis.AnalyzeResult(shape=idgx__szh, pre=[])
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
    udd__qlq = np.empty(n, dtype)
    zhcmq__kxaxk = np.empty(n + 7 >> 3, dtype=np.uint8)
    return init_integer_array(udd__qlq, zhcmq__kxaxk)


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
            jmg__ygac, ycsu__rhds = array_getitem_bool_index(A, ind)
            return init_integer_array(jmg__ygac, ycsu__rhds)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            jmg__ygac, ycsu__rhds = array_getitem_int_index(A, ind)
            return init_integer_array(jmg__ygac, ycsu__rhds)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            jmg__ygac, ycsu__rhds = array_getitem_slice_index(A, ind)
            return init_integer_array(jmg__ygac, ycsu__rhds)
        return impl_slice
    raise BodoError(
        f'getitem for IntegerArray with indexing type {ind} not supported.')


@overload(operator.setitem, no_unliteral=True)
def int_arr_setitem(A, idx, val):
    if not isinstance(A, IntegerArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    apw__mcdf = (
        f"setitem for IntegerArray with indexing type {idx} received an incorrect 'value' type {val}."
        )
    lsuk__xhxeh = isinstance(val, (types.Integer, types.Boolean))
    if isinstance(idx, types.Integer):
        if lsuk__xhxeh:

            def impl_scalar(A, idx, val):
                A._data[idx] = val
                bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap, idx, 1)
            return impl_scalar
        else:
            raise BodoError(apw__mcdf)
    if not (is_iterable_type(val) and isinstance(val.dtype, (types.Integer,
        types.Boolean)) or lsuk__xhxeh):
        raise BodoError(apw__mcdf)
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
            qjl__wsq = np.empty(n, nb_dtype)
            for i in numba.parfors.parfor.internal_prange(n):
                qjl__wsq[i] = data[i]
                if bodo.libs.array_kernels.isna(A, i):
                    qjl__wsq[i] = np.nan
            return qjl__wsq
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
                vwd__jqkm = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B1, i)
                eigdx__izwm = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B2, i)
                jpqn__lbxct = vwd__jqkm & eigdx__izwm
                bodo.libs.int_arr_ext.set_bit_to_arr(B1, i, jpqn__lbxct)
            return B1
        return impl_inplace

    def impl(B1, B2, n, inplace):
        numba.parfors.parfor.init_prange()
        jysig__fxhy = n + 7 >> 3
        qjl__wsq = np.empty(jysig__fxhy, np.uint8)
        for i in numba.parfors.parfor.internal_prange(n):
            vwd__jqkm = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B1, i)
            eigdx__izwm = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B2, i)
            jpqn__lbxct = vwd__jqkm & eigdx__izwm
            bodo.libs.int_arr_ext.set_bit_to_arr(qjl__wsq, i, jpqn__lbxct)
        return qjl__wsq
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
    for nlp__tiy in numba.np.ufunc_db.get_ufuncs():
        rkvrd__xnu = create_op_overload(nlp__tiy, nlp__tiy.nin)
        overload(nlp__tiy, no_unliteral=True)(rkvrd__xnu)


_install_np_ufuncs()
skips = [operator.lt, operator.le, operator.eq, operator.ne, operator.gt,
    operator.ge, operator.add, operator.sub, operator.mul, operator.truediv,
    operator.floordiv, operator.pow, operator.mod]


def _install_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesArrayOperator._op_map.keys():
        if op in skips:
            continue
        rkvrd__xnu = create_op_overload(op, 2)
        overload(op)(rkvrd__xnu)


_install_binary_ops()


def _install_inplace_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesInplaceArrayOperator._op_map.keys(
        ):
        rkvrd__xnu = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(rkvrd__xnu)


_install_inplace_binary_ops()


def _install_unary_ops():
    for op in (operator.neg, operator.invert, operator.pos):
        rkvrd__xnu = create_op_overload(op, 1)
        overload(op, no_unliteral=True)(rkvrd__xnu)


_install_unary_ops()


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_int_arr_data_tup(arrs):
    mgxn__dhdyh = len(arrs.types)
    mqk__lmko = 'def f(arrs):\n'
    dojzj__khk = ', '.join('arrs[{}]._data'.format(i) for i in range(
        mgxn__dhdyh))
    mqk__lmko += '  return ({}{})\n'.format(dojzj__khk, ',' if mgxn__dhdyh ==
        1 else '')
    yumu__vyp = {}
    exec(mqk__lmko, {}, yumu__vyp)
    impl = yumu__vyp['f']
    return impl


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def concat_bitmap_tup(arrs):
    mgxn__dhdyh = len(arrs.types)
    pge__tuco = '+'.join('len(arrs[{}]._data)'.format(i) for i in range(
        mgxn__dhdyh))
    mqk__lmko = 'def f(arrs):\n'
    mqk__lmko += '  n = {}\n'.format(pge__tuco)
    mqk__lmko += '  n_bytes = (n + 7) >> 3\n'
    mqk__lmko += '  new_mask = np.empty(n_bytes, np.uint8)\n'
    mqk__lmko += '  curr_bit = 0\n'
    for i in range(mgxn__dhdyh):
        mqk__lmko += '  old_mask = arrs[{}]._null_bitmap\n'.format(i)
        mqk__lmko += '  for j in range(len(arrs[{}])):\n'.format(i)
        mqk__lmko += (
            '    bit = bodo.libs.int_arr_ext.get_bit_bitmap_arr(old_mask, j)\n'
            )
        mqk__lmko += (
            '    bodo.libs.int_arr_ext.set_bit_to_arr(new_mask, curr_bit, bit)\n'
            )
        mqk__lmko += '    curr_bit += 1\n'
    mqk__lmko += '  return new_mask\n'
    yumu__vyp = {}
    exec(mqk__lmko, {'np': np, 'bodo': bodo}, yumu__vyp)
    impl = yumu__vyp['f']
    return impl


@overload_method(IntegerArrayType, 'sum', no_unliteral=True)
def overload_int_arr_sum(A, skipna=True, min_count=0):
    wuya__rxoa = dict(skipna=skipna, min_count=min_count)
    dkye__zqwqw = dict(skipna=True, min_count=0)
    check_unsupported_args('IntegerArray.sum', wuya__rxoa, dkye__zqwqw)

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
        afr__etp = []
        snvxg__mkvn = False
        s = set()
        for i in range(len(A)):
            val = A[i]
            if bodo.libs.array_kernels.isna(A, i):
                if not snvxg__mkvn:
                    data.append(dtype(1))
                    afr__etp.append(False)
                    snvxg__mkvn = True
                continue
            if val not in s:
                s.add(val)
                data.append(val)
                afr__etp.append(True)
        jmg__ygac = np.array(data)
        n = len(jmg__ygac)
        jysig__fxhy = n + 7 >> 3
        ycsu__rhds = np.empty(jysig__fxhy, np.uint8)
        for aihe__oykcj in range(n):
            set_bit_to_arr(ycsu__rhds, aihe__oykcj, afr__etp[aihe__oykcj])
        return init_integer_array(jmg__ygac, ycsu__rhds)
    return impl_int_arr


def get_nullable_array_unary_impl(op, A):
    sptf__zky = numba.core.registry.cpu_target.typing_context
    twes__gmjqn = sptf__zky.resolve_function_type(op, (types.Array(A.dtype,
        1, 'C'),), {}).return_type
    twes__gmjqn = to_nullable_type(twes__gmjqn)

    def impl(A):
        n = len(A)
        rwx__raa = bodo.utils.utils.alloc_type(n, twes__gmjqn, None)
        for i in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(A, i):
                bodo.libs.array_kernels.setna(rwx__raa, i)
                continue
            rwx__raa[i] = op(A[i])
        return rwx__raa
    return impl


def get_nullable_array_binary_impl(op, lhs, rhs):
    inplace = (op in numba.core.typing.npydecl.
        NumpyRulesInplaceArrayOperator._op_map.keys())
    msu__jcfxy = isinstance(lhs, (types.Number, types.Boolean))
    plus__vndbj = isinstance(rhs, (types.Number, types.Boolean))
    blhw__iozdq = types.Array(getattr(lhs, 'dtype', lhs), 1, 'C')
    tlo__hdhq = types.Array(getattr(rhs, 'dtype', rhs), 1, 'C')
    sptf__zky = numba.core.registry.cpu_target.typing_context
    twes__gmjqn = sptf__zky.resolve_function_type(op, (blhw__iozdq,
        tlo__hdhq), {}).return_type
    twes__gmjqn = to_nullable_type(twes__gmjqn)
    if op in (operator.truediv, operator.itruediv):
        op = np.true_divide
    elif op in (operator.floordiv, operator.ifloordiv):
        op = np.floor_divide
    ywe__rkukg = 'lhs' if msu__jcfxy else 'lhs[i]'
    qsvhf__nlxh = 'rhs' if plus__vndbj else 'rhs[i]'
    maumh__wdbx = ('False' if msu__jcfxy else
        'bodo.libs.array_kernels.isna(lhs, i)')
    uta__vydm = ('False' if plus__vndbj else
        'bodo.libs.array_kernels.isna(rhs, i)')
    mqk__lmko = 'def impl(lhs, rhs):\n'
    mqk__lmko += '  n = len({})\n'.format('lhs' if not msu__jcfxy else 'rhs')
    if inplace:
        mqk__lmko += '  out_arr = {}\n'.format('lhs' if not msu__jcfxy else
            'rhs')
    else:
        mqk__lmko += (
            '  out_arr = bodo.utils.utils.alloc_type(n, ret_dtype, None)\n')
    mqk__lmko += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    mqk__lmko += '    if ({}\n'.format(maumh__wdbx)
    mqk__lmko += '        or {}):\n'.format(uta__vydm)
    mqk__lmko += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    mqk__lmko += '      continue\n'
    mqk__lmko += (
        '    out_arr[i] = bodo.utils.conversion.unbox_if_timestamp(op({}, {}))\n'
        .format(ywe__rkukg, qsvhf__nlxh))
    mqk__lmko += '  return out_arr\n'
    yumu__vyp = {}
    exec(mqk__lmko, {'bodo': bodo, 'numba': numba, 'np': np, 'ret_dtype':
        twes__gmjqn, 'op': op}, yumu__vyp)
    impl = yumu__vyp['impl']
    return impl


def get_int_array_op_pd_td(op):

    def impl(lhs, rhs):
        msu__jcfxy = lhs in [pd_timedelta_type]
        plus__vndbj = rhs in [pd_timedelta_type]
        if msu__jcfxy:

            def impl(lhs, rhs):
                n = len(rhs)
                rwx__raa = np.empty(n, 'timedelta64[ns]')
                for i in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(rhs, i):
                        bodo.libs.array_kernels.setna(rwx__raa, i)
                        continue
                    rwx__raa[i] = bodo.utils.conversion.unbox_if_timestamp(op
                        (lhs, rhs[i]))
                return rwx__raa
            return impl
        elif plus__vndbj:

            def impl(lhs, rhs):
                n = len(lhs)
                rwx__raa = np.empty(n, 'timedelta64[ns]')
                for i in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(lhs, i):
                        bodo.libs.array_kernels.setna(rwx__raa, i)
                        continue
                    rwx__raa[i] = bodo.utils.conversion.unbox_if_timestamp(op
                        (lhs[i], rhs))
                return rwx__raa
            return impl
    return impl
