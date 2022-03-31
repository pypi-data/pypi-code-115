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
        zhg__qtojl = [('data', types.Array(fe_type.dtype, 1, 'C')), (
            'null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, zhg__qtojl)


make_attribute_wrapper(IntegerArrayType, 'data', '_data')
make_attribute_wrapper(IntegerArrayType, 'null_bitmap', '_null_bitmap')


@typeof_impl.register(pd.arrays.IntegerArray)
def _typeof_pd_int_array(val, c):
    wih__dit = 8 * val.dtype.itemsize
    fto__fklws = '' if val.dtype.kind == 'i' else 'u'
    dtype = getattr(types, '{}int{}'.format(fto__fklws, wih__dit))
    return IntegerArrayType(dtype)


class IntDtype(types.Number):

    def __init__(self, dtype):
        assert isinstance(dtype, types.Integer)
        self.dtype = dtype
        cwn__zjcte = '{}Int{}Dtype()'.format('' if dtype.signed else 'U',
            dtype.bitwidth)
        super(IntDtype, self).__init__(cwn__zjcte)


register_model(IntDtype)(models.OpaqueModel)


@box(IntDtype)
def box_intdtype(typ, val, c):
    jwag__hnn = c.context.insert_const_string(c.builder.module, 'pandas')
    obdt__iokqt = c.pyapi.import_module_noblock(jwag__hnn)
    czbc__nojsb = c.pyapi.call_method(obdt__iokqt, str(typ)[:-2], ())
    c.pyapi.decref(obdt__iokqt)
    return czbc__nojsb


@unbox(IntDtype)
def unbox_intdtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


def typeof_pd_int_dtype(val, c):
    wih__dit = 8 * val.itemsize
    fto__fklws = '' if val.kind == 'i' else 'u'
    dtype = getattr(types, '{}int{}'.format(fto__fklws, wih__dit))
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
    dez__nxasr = n + 7 >> 3
    pncld__ril = np.empty(dez__nxasr, np.uint8)
    for i in range(n):
        ogub__vxgwd = i // 8
        pncld__ril[ogub__vxgwd] ^= np.uint8(-np.uint8(not mask_arr[i]) ^
            pncld__ril[ogub__vxgwd]) & kBitmask[i % 8]
    return pncld__ril


@unbox(IntegerArrayType)
def unbox_int_array(typ, obj, c):
    yyj__dgjhr = c.pyapi.call_method(obj, '__len__', ())
    n = c.pyapi.long_as_longlong(yyj__dgjhr)
    c.pyapi.decref(yyj__dgjhr)
    zinnz__sgtdi = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    dez__nxasr = c.builder.udiv(c.builder.add(n, lir.Constant(lir.IntType(
        64), 7)), lir.Constant(lir.IntType(64), 8))
    suri__fkjxg = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        types.Array(types.uint8, 1, 'C'), [dez__nxasr])
    waj__zly = lir.FunctionType(lir.IntType(32), [lir.IntType(8).as_pointer()])
    obuaw__wxirp = cgutils.get_or_insert_function(c.builder.module,
        waj__zly, name='is_pd_int_array')
    xge__trgja = c.builder.call(obuaw__wxirp, [obj])
    qbxhb__mwfpd = c.builder.icmp_unsigned('!=', xge__trgja, xge__trgja.type(0)
        )
    with c.builder.if_else(qbxhb__mwfpd) as (aklwm__esap, xxdnq__ixyb):
        with aklwm__esap:
            aajmy__ezwx = c.pyapi.object_getattr_string(obj, '_data')
            zinnz__sgtdi.data = c.pyapi.to_native_value(types.Array(typ.
                dtype, 1, 'C'), aajmy__ezwx).value
            znv__xec = c.pyapi.object_getattr_string(obj, '_mask')
            mask_arr = c.pyapi.to_native_value(types.Array(types.bool_, 1,
                'C'), znv__xec).value
            c.pyapi.decref(aajmy__ezwx)
            c.pyapi.decref(znv__xec)
            nnmc__kmxnl = c.context.make_array(types.Array(types.bool_, 1, 'C')
                )(c.context, c.builder, mask_arr)
            waj__zly = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
            obuaw__wxirp = cgutils.get_or_insert_function(c.builder.module,
                waj__zly, name='mask_arr_to_bitmap')
            c.builder.call(obuaw__wxirp, [suri__fkjxg.data, nnmc__kmxnl.
                data, n])
            c.context.nrt.decref(c.builder, types.Array(types.bool_, 1, 'C'
                ), mask_arr)
        with xxdnq__ixyb:
            gdnku__njv = bodo.utils.utils._empty_nd_impl(c.context, c.
                builder, types.Array(typ.dtype, 1, 'C'), [n])
            waj__zly = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
                as_pointer()])
            fpxv__hli = cgutils.get_or_insert_function(c.builder.module,
                waj__zly, name='int_array_from_sequence')
            c.builder.call(fpxv__hli, [obj, c.builder.bitcast(gdnku__njv.
                data, lir.IntType(8).as_pointer()), suri__fkjxg.data])
            zinnz__sgtdi.data = gdnku__njv._getvalue()
    zinnz__sgtdi.null_bitmap = suri__fkjxg._getvalue()
    iukbn__nnh = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(zinnz__sgtdi._getvalue(), is_error=iukbn__nnh)


@box(IntegerArrayType)
def box_int_arr(typ, val, c):
    zinnz__sgtdi = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    data = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        zinnz__sgtdi.data, c.env_manager)
    vllq__glf = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, zinnz__sgtdi.null_bitmap).data
    yyj__dgjhr = c.pyapi.call_method(data, '__len__', ())
    n = c.pyapi.long_as_longlong(yyj__dgjhr)
    jwag__hnn = c.context.insert_const_string(c.builder.module, 'numpy')
    orxmc__jmp = c.pyapi.import_module_noblock(jwag__hnn)
    knngr__bdpco = c.pyapi.object_getattr_string(orxmc__jmp, 'bool_')
    mask_arr = c.pyapi.call_method(orxmc__jmp, 'empty', (yyj__dgjhr,
        knngr__bdpco))
    dkf__xpd = c.pyapi.object_getattr_string(mask_arr, 'ctypes')
    mxsah__jmwkh = c.pyapi.object_getattr_string(dkf__xpd, 'data')
    inmfw__ontw = c.builder.inttoptr(c.pyapi.long_as_longlong(mxsah__jmwkh),
        lir.IntType(8).as_pointer())
    with cgutils.for_range(c.builder, n) as prizp__noh:
        i = prizp__noh.index
        bdjc__ifwuj = c.builder.lshr(i, lir.Constant(lir.IntType(64), 3))
        ogsr__jigrr = c.builder.load(cgutils.gep(c.builder, vllq__glf,
            bdjc__ifwuj))
        mix__memu = c.builder.trunc(c.builder.and_(i, lir.Constant(lir.
            IntType(64), 7)), lir.IntType(8))
        val = c.builder.and_(c.builder.lshr(ogsr__jigrr, mix__memu), lir.
            Constant(lir.IntType(8), 1))
        val = c.builder.xor(val, lir.Constant(lir.IntType(8), 1))
        tsw__hswe = cgutils.gep(c.builder, inmfw__ontw, i)
        c.builder.store(val, tsw__hswe)
    c.context.nrt.decref(c.builder, types.Array(types.uint8, 1, 'C'),
        zinnz__sgtdi.null_bitmap)
    jwag__hnn = c.context.insert_const_string(c.builder.module, 'pandas')
    obdt__iokqt = c.pyapi.import_module_noblock(jwag__hnn)
    ecoh__lonkd = c.pyapi.object_getattr_string(obdt__iokqt, 'arrays')
    czbc__nojsb = c.pyapi.call_method(ecoh__lonkd, 'IntegerArray', (data,
        mask_arr))
    c.pyapi.decref(obdt__iokqt)
    c.pyapi.decref(yyj__dgjhr)
    c.pyapi.decref(orxmc__jmp)
    c.pyapi.decref(knngr__bdpco)
    c.pyapi.decref(dkf__xpd)
    c.pyapi.decref(mxsah__jmwkh)
    c.pyapi.decref(ecoh__lonkd)
    c.pyapi.decref(data)
    c.pyapi.decref(mask_arr)
    return czbc__nojsb


@intrinsic
def init_integer_array(typingctx, data, null_bitmap=None):
    assert isinstance(data, types.Array)
    assert null_bitmap == types.Array(types.uint8, 1, 'C')

    def codegen(context, builder, signature, args):
        gvv__jwijr, lbwlu__vwr = args
        zinnz__sgtdi = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        zinnz__sgtdi.data = gvv__jwijr
        zinnz__sgtdi.null_bitmap = lbwlu__vwr
        context.nrt.incref(builder, signature.args[0], gvv__jwijr)
        context.nrt.incref(builder, signature.args[1], lbwlu__vwr)
        return zinnz__sgtdi._getvalue()
    tljs__fbiq = IntegerArrayType(data.dtype)
    fryuw__sknhv = tljs__fbiq(data, null_bitmap)
    return fryuw__sknhv, codegen


@lower_constant(IntegerArrayType)
def lower_constant_int_arr(context, builder, typ, pyval):
    n = len(pyval)
    siabg__hod = np.empty(n, pyval.dtype.type)
    axrsh__qkgu = np.empty(n + 7 >> 3, np.uint8)
    for i, s in enumerate(pyval):
        ekv__stot = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(axrsh__qkgu, i, int(not ekv__stot)
            )
        if not ekv__stot:
            siabg__hod[i] = s
    nzmte__aebl = context.get_constant_generic(builder, types.Array(typ.
        dtype, 1, 'C'), siabg__hod)
    yby__ogml = context.get_constant_generic(builder, types.Array(types.
        uint8, 1, 'C'), axrsh__qkgu)
    return lir.Constant.literal_struct([nzmte__aebl, yby__ogml])


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_int_arr_data(A):
    return lambda A: A._data


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_int_arr_bitmap(A):
    return lambda A: A._null_bitmap


def get_int_arr_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    ink__jpfwv = args[0]
    if equiv_set.has_shape(ink__jpfwv):
        return ArrayAnalysis.AnalyzeResult(shape=ink__jpfwv, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_libs_int_arr_ext_get_int_arr_data = (
    get_int_arr_data_equiv)


def init_integer_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    ink__jpfwv = args[0]
    if equiv_set.has_shape(ink__jpfwv):
        return ArrayAnalysis.AnalyzeResult(shape=ink__jpfwv, pre=[])
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
    siabg__hod = np.empty(n, dtype)
    oyr__jhbvi = np.empty(n + 7 >> 3, dtype=np.uint8)
    return init_integer_array(siabg__hod, oyr__jhbvi)


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
            nspxi__tkf, cic__jqqne = array_getitem_bool_index(A, ind)
            return init_integer_array(nspxi__tkf, cic__jqqne)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            nspxi__tkf, cic__jqqne = array_getitem_int_index(A, ind)
            return init_integer_array(nspxi__tkf, cic__jqqne)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            nspxi__tkf, cic__jqqne = array_getitem_slice_index(A, ind)
            return init_integer_array(nspxi__tkf, cic__jqqne)
        return impl_slice
    raise BodoError(
        f'getitem for IntegerArray with indexing type {ind} not supported.')


@overload(operator.setitem, no_unliteral=True)
def int_arr_setitem(A, idx, val):
    if not isinstance(A, IntegerArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    etx__nll = (
        f"setitem for IntegerArray with indexing type {idx} received an incorrect 'value' type {val}."
        )
    gyj__uwt = isinstance(val, (types.Integer, types.Boolean))
    if isinstance(idx, types.Integer):
        if gyj__uwt:

            def impl_scalar(A, idx, val):
                A._data[idx] = val
                bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap, idx, 1)
            return impl_scalar
        else:
            raise BodoError(etx__nll)
    if not (is_iterable_type(val) and isinstance(val.dtype, (types.Integer,
        types.Boolean)) or gyj__uwt):
        raise BodoError(etx__nll)
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
            pjzzp__rpd = np.empty(n, nb_dtype)
            for i in numba.parfors.parfor.internal_prange(n):
                pjzzp__rpd[i] = data[i]
                if bodo.libs.array_kernels.isna(A, i):
                    pjzzp__rpd[i] = np.nan
            return pjzzp__rpd
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
                khmw__yml = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B1, i)
                jtez__ssko = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B2, i)
                eviai__ayo = khmw__yml & jtez__ssko
                bodo.libs.int_arr_ext.set_bit_to_arr(B1, i, eviai__ayo)
            return B1
        return impl_inplace

    def impl(B1, B2, n, inplace):
        numba.parfors.parfor.init_prange()
        dez__nxasr = n + 7 >> 3
        pjzzp__rpd = np.empty(dez__nxasr, np.uint8)
        for i in numba.parfors.parfor.internal_prange(n):
            khmw__yml = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B1, i)
            jtez__ssko = bodo.libs.int_arr_ext.get_bit_bitmap_arr(B2, i)
            eviai__ayo = khmw__yml & jtez__ssko
            bodo.libs.int_arr_ext.set_bit_to_arr(pjzzp__rpd, i, eviai__ayo)
        return pjzzp__rpd
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
    for kaar__nysvk in numba.np.ufunc_db.get_ufuncs():
        jwle__qyzvm = create_op_overload(kaar__nysvk, kaar__nysvk.nin)
        overload(kaar__nysvk, no_unliteral=True)(jwle__qyzvm)


_install_np_ufuncs()
skips = [operator.lt, operator.le, operator.eq, operator.ne, operator.gt,
    operator.ge, operator.add, operator.sub, operator.mul, operator.truediv,
    operator.floordiv, operator.pow, operator.mod]


def _install_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesArrayOperator._op_map.keys():
        if op in skips:
            continue
        jwle__qyzvm = create_op_overload(op, 2)
        overload(op)(jwle__qyzvm)


_install_binary_ops()


def _install_inplace_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesInplaceArrayOperator._op_map.keys(
        ):
        jwle__qyzvm = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(jwle__qyzvm)


_install_inplace_binary_ops()


def _install_unary_ops():
    for op in (operator.neg, operator.invert, operator.pos):
        jwle__qyzvm = create_op_overload(op, 1)
        overload(op, no_unliteral=True)(jwle__qyzvm)


_install_unary_ops()


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_int_arr_data_tup(arrs):
    kkik__ikwta = len(arrs.types)
    rpf__ncdp = 'def f(arrs):\n'
    czbc__nojsb = ', '.join('arrs[{}]._data'.format(i) for i in range(
        kkik__ikwta))
    rpf__ncdp += '  return ({}{})\n'.format(czbc__nojsb, ',' if kkik__ikwta ==
        1 else '')
    aoj__ssmk = {}
    exec(rpf__ncdp, {}, aoj__ssmk)
    impl = aoj__ssmk['f']
    return impl


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def concat_bitmap_tup(arrs):
    kkik__ikwta = len(arrs.types)
    yqds__vfpuy = '+'.join('len(arrs[{}]._data)'.format(i) for i in range(
        kkik__ikwta))
    rpf__ncdp = 'def f(arrs):\n'
    rpf__ncdp += '  n = {}\n'.format(yqds__vfpuy)
    rpf__ncdp += '  n_bytes = (n + 7) >> 3\n'
    rpf__ncdp += '  new_mask = np.empty(n_bytes, np.uint8)\n'
    rpf__ncdp += '  curr_bit = 0\n'
    for i in range(kkik__ikwta):
        rpf__ncdp += '  old_mask = arrs[{}]._null_bitmap\n'.format(i)
        rpf__ncdp += '  for j in range(len(arrs[{}])):\n'.format(i)
        rpf__ncdp += (
            '    bit = bodo.libs.int_arr_ext.get_bit_bitmap_arr(old_mask, j)\n'
            )
        rpf__ncdp += (
            '    bodo.libs.int_arr_ext.set_bit_to_arr(new_mask, curr_bit, bit)\n'
            )
        rpf__ncdp += '    curr_bit += 1\n'
    rpf__ncdp += '  return new_mask\n'
    aoj__ssmk = {}
    exec(rpf__ncdp, {'np': np, 'bodo': bodo}, aoj__ssmk)
    impl = aoj__ssmk['f']
    return impl


@overload_method(IntegerArrayType, 'sum', no_unliteral=True)
def overload_int_arr_sum(A, skipna=True, min_count=0):
    rvloe__qnza = dict(skipna=skipna, min_count=min_count)
    jxs__eiv = dict(skipna=True, min_count=0)
    check_unsupported_args('IntegerArray.sum', rvloe__qnza, jxs__eiv)

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
        mix__memu = []
        kxmhp__cpf = False
        s = set()
        for i in range(len(A)):
            val = A[i]
            if bodo.libs.array_kernels.isna(A, i):
                if not kxmhp__cpf:
                    data.append(dtype(1))
                    mix__memu.append(False)
                    kxmhp__cpf = True
                continue
            if val not in s:
                s.add(val)
                data.append(val)
                mix__memu.append(True)
        nspxi__tkf = np.array(data)
        n = len(nspxi__tkf)
        dez__nxasr = n + 7 >> 3
        cic__jqqne = np.empty(dez__nxasr, np.uint8)
        for yaz__qtdsr in range(n):
            set_bit_to_arr(cic__jqqne, yaz__qtdsr, mix__memu[yaz__qtdsr])
        return init_integer_array(nspxi__tkf, cic__jqqne)
    return impl_int_arr


def get_nullable_array_unary_impl(op, A):
    ujmaw__ixger = numba.core.registry.cpu_target.typing_context
    vays__fcm = ujmaw__ixger.resolve_function_type(op, (types.Array(A.dtype,
        1, 'C'),), {}).return_type
    vays__fcm = to_nullable_type(vays__fcm)

    def impl(A):
        n = len(A)
        hblay__kxv = bodo.utils.utils.alloc_type(n, vays__fcm, None)
        for i in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(A, i):
                bodo.libs.array_kernels.setna(hblay__kxv, i)
                continue
            hblay__kxv[i] = op(A[i])
        return hblay__kxv
    return impl


def get_nullable_array_binary_impl(op, lhs, rhs):
    inplace = (op in numba.core.typing.npydecl.
        NumpyRulesInplaceArrayOperator._op_map.keys())
    shhhd__pwdah = isinstance(lhs, (types.Number, types.Boolean))
    txgsg__uyfvm = isinstance(rhs, (types.Number, types.Boolean))
    pwdw__qjri = types.Array(getattr(lhs, 'dtype', lhs), 1, 'C')
    kkdoa__bopzi = types.Array(getattr(rhs, 'dtype', rhs), 1, 'C')
    ujmaw__ixger = numba.core.registry.cpu_target.typing_context
    vays__fcm = ujmaw__ixger.resolve_function_type(op, (pwdw__qjri,
        kkdoa__bopzi), {}).return_type
    vays__fcm = to_nullable_type(vays__fcm)
    if op in (operator.truediv, operator.itruediv):
        op = np.true_divide
    elif op in (operator.floordiv, operator.ifloordiv):
        op = np.floor_divide
    ujno__vbp = 'lhs' if shhhd__pwdah else 'lhs[i]'
    tlbkb__nncu = 'rhs' if txgsg__uyfvm else 'rhs[i]'
    lhull__sycp = ('False' if shhhd__pwdah else
        'bodo.libs.array_kernels.isna(lhs, i)')
    fujw__iyu = ('False' if txgsg__uyfvm else
        'bodo.libs.array_kernels.isna(rhs, i)')
    rpf__ncdp = 'def impl(lhs, rhs):\n'
    rpf__ncdp += '  n = len({})\n'.format('lhs' if not shhhd__pwdah else 'rhs')
    if inplace:
        rpf__ncdp += '  out_arr = {}\n'.format('lhs' if not shhhd__pwdah else
            'rhs')
    else:
        rpf__ncdp += (
            '  out_arr = bodo.utils.utils.alloc_type(n, ret_dtype, None)\n')
    rpf__ncdp += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    rpf__ncdp += '    if ({}\n'.format(lhull__sycp)
    rpf__ncdp += '        or {}):\n'.format(fujw__iyu)
    rpf__ncdp += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
    rpf__ncdp += '      continue\n'
    rpf__ncdp += (
        '    out_arr[i] = bodo.utils.conversion.unbox_if_timestamp(op({}, {}))\n'
        .format(ujno__vbp, tlbkb__nncu))
    rpf__ncdp += '  return out_arr\n'
    aoj__ssmk = {}
    exec(rpf__ncdp, {'bodo': bodo, 'numba': numba, 'np': np, 'ret_dtype':
        vays__fcm, 'op': op}, aoj__ssmk)
    impl = aoj__ssmk['impl']
    return impl


def get_int_array_op_pd_td(op):

    def impl(lhs, rhs):
        shhhd__pwdah = lhs in [pd_timedelta_type]
        txgsg__uyfvm = rhs in [pd_timedelta_type]
        if shhhd__pwdah:

            def impl(lhs, rhs):
                n = len(rhs)
                hblay__kxv = np.empty(n, 'timedelta64[ns]')
                for i in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(rhs, i):
                        bodo.libs.array_kernels.setna(hblay__kxv, i)
                        continue
                    hblay__kxv[i] = bodo.utils.conversion.unbox_if_timestamp(op
                        (lhs, rhs[i]))
                return hblay__kxv
            return impl
        elif txgsg__uyfvm:

            def impl(lhs, rhs):
                n = len(lhs)
                hblay__kxv = np.empty(n, 'timedelta64[ns]')
                for i in numba.parfors.parfor.internal_prange(n):
                    if bodo.libs.array_kernels.isna(lhs, i):
                        bodo.libs.array_kernels.setna(hblay__kxv, i)
                        continue
                    hblay__kxv[i] = bodo.utils.conversion.unbox_if_timestamp(op
                        (lhs[i], rhs))
                return hblay__kxv
            return impl
    return impl
