"""Array implementation for string objects, which are usually immutable.
The characters are stored in a contingous data array, and an offsets array marks the
the individual strings. For example:
value:             ['a', 'bc', '', 'abc', None, 'bb']
data:              [a, b, c, a, b, c, b, b]
offsets:           [0, 1, 3, 3, 6, 6, 8]
"""
import glob
import operator
import numba
import numba.core.typing.typeof
import numpy as np
import pandas as pd
from numba.core import cgutils, types
from numba.core.imputils import impl_ret_borrowed, lower_constant
from numba.core.unsafe.bytes import memcpy_region
from numba.extending import NativeValue, box, intrinsic, lower_builtin, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_jitable, register_model, type_callable, typeof_impl, unbox
import bodo
from bodo.libs.array_item_arr_ext import ArrayItemArrayPayloadType, ArrayItemArrayType, _get_array_item_arr_payload, np_offset_type, offset_type
from bodo.libs.binary_arr_ext import BinaryArrayType, binary_array_type, pre_alloc_binary_array
from bodo.libs.str_ext import memcmp, string_type, unicode_to_utf8_and_len
from bodo.utils.typing import BodoArrayIterator, BodoError, decode_if_dict_array, is_list_like_index_type, is_overload_constant_int, is_overload_none, is_overload_true, is_str_arr_type, parse_dtype, raise_bodo_error
use_pd_string_array = False
char_type = types.uint8
char_arr_type = types.Array(char_type, 1, 'C')
offset_arr_type = types.Array(offset_type, 1, 'C')
null_bitmap_arr_type = types.Array(types.uint8, 1, 'C')
data_ctypes_type = types.ArrayCTypes(char_arr_type)
offset_ctypes_type = types.ArrayCTypes(offset_arr_type)


class StringArrayType(types.IterableType, types.ArrayCompatible):

    def __init__(self):
        super(StringArrayType, self).__init__(name='StringArrayType()')

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def dtype(self):
        return string_type

    @property
    def iterator_type(self):
        return BodoArrayIterator(self)

    def copy(self):
        return StringArrayType()


string_array_type = StringArrayType()


@typeof_impl.register(pd.arrays.StringArray)
def typeof_string_array(val, c):
    return string_array_type


@register_model(BinaryArrayType)
@register_model(StringArrayType)
class StringArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        pbvvq__xaxe = ArrayItemArrayType(char_arr_type)
        menux__rwu = [('data', pbvvq__xaxe)]
        models.StructModel.__init__(self, dmm, fe_type, menux__rwu)


make_attribute_wrapper(StringArrayType, 'data', '_data')
make_attribute_wrapper(BinaryArrayType, 'data', '_data')
lower_builtin('getiter', string_array_type)(numba.np.arrayobj.getiter_array)


@intrinsic
def init_str_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, ArrayItemArrayType
        ) and data_typ.dtype == types.Array(char_type, 1, 'C')

    def codegen(context, builder, sig, args):
        xxd__qqpvf, = args
        gke__wts = context.make_helper(builder, string_array_type)
        gke__wts.data = xxd__qqpvf
        context.nrt.incref(builder, data_typ, xxd__qqpvf)
        return gke__wts._getvalue()
    return string_array_type(data_typ), codegen


class StringDtype(types.Number):

    def __init__(self):
        super(StringDtype, self).__init__('StringDtype')


string_dtype = StringDtype()
register_model(StringDtype)(models.OpaqueModel)


@box(StringDtype)
def box_string_dtype(typ, val, c):
    pul__rlgo = c.context.insert_const_string(c.builder.module, 'pandas')
    mnga__rqd = c.pyapi.import_module_noblock(pul__rlgo)
    ryda__fjbq = c.pyapi.call_method(mnga__rqd, 'StringDtype', ())
    c.pyapi.decref(mnga__rqd)
    return ryda__fjbq


@unbox(StringDtype)
def unbox_string_dtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


typeof_impl.register(pd.StringDtype)(lambda a, b: string_dtype)
type_callable(pd.StringDtype)(lambda c: lambda : string_dtype)
lower_builtin(pd.StringDtype)(lambda c, b, s, a: c.get_dummy_value())


def create_binary_op_overload(op):

    def overload_string_array_binary_op(lhs, rhs):
        rsygt__ybfp = bodo.libs.dict_arr_ext.get_binary_op_overload(op, lhs,
            rhs)
        if rsygt__ybfp is not None:
            return rsygt__ybfp
        if is_str_arr_type(lhs) and is_str_arr_type(rhs):

            def impl_both(lhs, rhs):
                numba.parfors.parfor.init_prange()
                hpkyx__vuzv = len(lhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(hpkyx__vuzv)
                for i in numba.parfors.parfor.internal_prange(hpkyx__vuzv):
                    if bodo.libs.array_kernels.isna(lhs, i
                        ) or bodo.libs.array_kernels.isna(rhs, i):
                        bodo.libs.array_kernels.setna(out_arr, i)
                        continue
                    val = op(lhs[i], rhs[i])
                    out_arr[i] = val
                return out_arr
            return impl_both
        if is_str_arr_type(lhs) and types.unliteral(rhs) == string_type:

            def impl_left(lhs, rhs):
                numba.parfors.parfor.init_prange()
                hpkyx__vuzv = len(lhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(hpkyx__vuzv)
                for i in numba.parfors.parfor.internal_prange(hpkyx__vuzv):
                    if bodo.libs.array_kernels.isna(lhs, i):
                        bodo.libs.array_kernels.setna(out_arr, i)
                        continue
                    val = op(lhs[i], rhs)
                    out_arr[i] = val
                return out_arr
            return impl_left
        if types.unliteral(lhs) == string_type and is_str_arr_type(rhs):

            def impl_right(lhs, rhs):
                numba.parfors.parfor.init_prange()
                hpkyx__vuzv = len(rhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(hpkyx__vuzv)
                for i in numba.parfors.parfor.internal_prange(hpkyx__vuzv):
                    if bodo.libs.array_kernels.isna(rhs, i):
                        bodo.libs.array_kernels.setna(out_arr, i)
                        continue
                    val = op(lhs, rhs[i])
                    out_arr[i] = val
                return out_arr
            return impl_right
        raise_bodo_error(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_string_array_binary_op


def overload_add_operator_string_array(lhs, rhs):
    zvi__kxuei = is_str_arr_type(lhs) or isinstance(lhs, types.Array
        ) and lhs.dtype == string_type
    ysotb__soopx = is_str_arr_type(rhs) or isinstance(rhs, types.Array
        ) and rhs.dtype == string_type
    if is_str_arr_type(lhs) and ysotb__soopx or zvi__kxuei and is_str_arr_type(
        rhs):

        def impl_both(lhs, rhs):
            numba.parfors.parfor.init_prange()
            l = len(lhs)
            out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(l, -1)
            for j in numba.parfors.parfor.internal_prange(l):
                if bodo.libs.array_kernels.isna(lhs, j
                    ) or bodo.libs.array_kernels.isna(rhs, j):
                    out_arr[j] = ''
                    bodo.libs.array_kernels.setna(out_arr, j)
                else:
                    out_arr[j] = lhs[j] + rhs[j]
            return out_arr
        return impl_both
    if is_str_arr_type(lhs) and types.unliteral(rhs) == string_type:

        def impl_left(lhs, rhs):
            numba.parfors.parfor.init_prange()
            l = len(lhs)
            out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(l, -1)
            for j in numba.parfors.parfor.internal_prange(l):
                if bodo.libs.array_kernels.isna(lhs, j):
                    out_arr[j] = ''
                    bodo.libs.array_kernels.setna(out_arr, j)
                else:
                    out_arr[j] = lhs[j] + rhs
            return out_arr
        return impl_left
    if types.unliteral(lhs) == string_type and is_str_arr_type(rhs):

        def impl_right(lhs, rhs):
            numba.parfors.parfor.init_prange()
            l = len(rhs)
            out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(l, -1)
            for j in numba.parfors.parfor.internal_prange(l):
                if bodo.libs.array_kernels.isna(rhs, j):
                    out_arr[j] = ''
                    bodo.libs.array_kernels.setna(out_arr, j)
                else:
                    out_arr[j] = lhs + rhs[j]
            return out_arr
        return impl_right


def overload_mul_operator_str_arr(lhs, rhs):
    if is_str_arr_type(lhs) and isinstance(rhs, types.Integer):

        def impl(lhs, rhs):
            numba.parfors.parfor.init_prange()
            l = len(lhs)
            out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(l, -1)
            for j in numba.parfors.parfor.internal_prange(l):
                if bodo.libs.array_kernels.isna(lhs, j):
                    out_arr[j] = ''
                    bodo.libs.array_kernels.setna(out_arr, j)
                else:
                    out_arr[j] = lhs[j] * rhs
            return out_arr
        return impl
    if isinstance(lhs, types.Integer) and is_str_arr_type(rhs):

        def impl(lhs, rhs):
            return rhs * lhs
        return impl


def _get_str_binary_arr_payload(context, builder, arr_value, arr_typ):
    assert arr_typ == string_array_type or arr_typ == binary_array_type
    cvfk__tyro = context.make_helper(builder, arr_typ, arr_value)
    pbvvq__xaxe = ArrayItemArrayType(char_arr_type)
    ygx__twt = _get_array_item_arr_payload(context, builder, pbvvq__xaxe,
        cvfk__tyro.data)
    return ygx__twt


@intrinsic
def num_strings(typingctx, str_arr_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, in_str_arr,
            string_array_type)
        return ygx__twt.n_arrays
    return types.int64(string_array_type), codegen


def _get_num_total_chars(builder, offsets, num_strings):
    return builder.zext(builder.load(builder.gep(offsets, [num_strings])),
        lir.IntType(64))


@intrinsic
def num_total_chars(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, in_str_arr,
            sig.args[0])
        bqdsh__hvs = context.make_helper(builder, offset_arr_type, ygx__twt
            .offsets).data
        return _get_num_total_chars(builder, bqdsh__hvs, ygx__twt.n_arrays)
    return types.uint64(in_arr_typ), codegen


@intrinsic
def get_offset_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, in_str_arr,
            sig.args[0])
        aprq__yfd = context.make_helper(builder, offset_arr_type, ygx__twt.
            offsets)
        tfb__ugnrx = context.make_helper(builder, offset_ctypes_type)
        tfb__ugnrx.data = builder.bitcast(aprq__yfd.data, lir.IntType(
            offset_type.bitwidth).as_pointer())
        tfb__ugnrx.meminfo = aprq__yfd.meminfo
        ryda__fjbq = tfb__ugnrx._getvalue()
        return impl_ret_borrowed(context, builder, offset_ctypes_type,
            ryda__fjbq)
    return offset_ctypes_type(in_arr_typ), codegen


@intrinsic
def get_data_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, in_str_arr,
            sig.args[0])
        xxd__qqpvf = context.make_helper(builder, char_arr_type, ygx__twt.data)
        tfb__ugnrx = context.make_helper(builder, data_ctypes_type)
        tfb__ugnrx.data = xxd__qqpvf.data
        tfb__ugnrx.meminfo = xxd__qqpvf.meminfo
        ryda__fjbq = tfb__ugnrx._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type, ryda__fjbq
            )
    return data_ctypes_type(in_arr_typ), codegen


@intrinsic
def get_data_ptr_ind(typingctx, in_arr_typ, int_t=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        nuyh__xhb, ind = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, nuyh__xhb,
            sig.args[0])
        xxd__qqpvf = context.make_helper(builder, char_arr_type, ygx__twt.data)
        tfb__ugnrx = context.make_helper(builder, data_ctypes_type)
        tfb__ugnrx.data = builder.gep(xxd__qqpvf.data, [ind])
        tfb__ugnrx.meminfo = xxd__qqpvf.meminfo
        ryda__fjbq = tfb__ugnrx._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type, ryda__fjbq
            )
    return data_ctypes_type(in_arr_typ, types.intp), codegen


@intrinsic
def copy_single_char(typingctx, dst_ptr_t, dst_ind_t, src_ptr_t, src_ind_t=None
    ):

    def codegen(context, builder, sig, args):
        vwb__eud, dqg__qlc, ocr__qfxb, nhhvs__vae = args
        vbv__ldcy = builder.bitcast(builder.gep(vwb__eud, [dqg__qlc]), lir.
            IntType(8).as_pointer())
        wdf__lrbr = builder.bitcast(builder.gep(ocr__qfxb, [nhhvs__vae]),
            lir.IntType(8).as_pointer())
        bhxp__bus = builder.load(wdf__lrbr)
        builder.store(bhxp__bus, vbv__ldcy)
        return context.get_dummy_value()
    return types.void(types.voidptr, types.intp, types.voidptr, types.intp
        ), codegen


@intrinsic
def get_null_bitmap_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, in_str_arr,
            sig.args[0])
        hmip__rbmq = context.make_helper(builder, null_bitmap_arr_type,
            ygx__twt.null_bitmap)
        tfb__ugnrx = context.make_helper(builder, data_ctypes_type)
        tfb__ugnrx.data = hmip__rbmq.data
        tfb__ugnrx.meminfo = hmip__rbmq.meminfo
        ryda__fjbq = tfb__ugnrx._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type, ryda__fjbq
            )
    return data_ctypes_type(in_arr_typ), codegen


@intrinsic
def getitem_str_offset(typingctx, in_arr_typ, ind_t=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, in_str_arr,
            sig.args[0])
        bqdsh__hvs = context.make_helper(builder, offset_arr_type, ygx__twt
            .offsets).data
        return builder.load(builder.gep(bqdsh__hvs, [ind]))
    return offset_type(in_arr_typ, ind_t), codegen


@intrinsic
def setitem_str_offset(typingctx, str_arr_typ, ind_t, val_t=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind, val = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, in_str_arr,
            string_array_type)
        offsets = context.make_helper(builder, offset_arr_type, ygx__twt.
            offsets).data
        builder.store(val, builder.gep(offsets, [ind]))
        return context.get_dummy_value()
    return types.void(string_array_type, ind_t, offset_type), codegen


@intrinsic
def getitem_str_bitmap(typingctx, in_bitmap_typ, ind_t=None):

    def codegen(context, builder, sig, args):
        uldzy__yodw, ind = args
        if in_bitmap_typ == data_ctypes_type:
            tfb__ugnrx = context.make_helper(builder, data_ctypes_type,
                uldzy__yodw)
            uldzy__yodw = tfb__ugnrx.data
        return builder.load(builder.gep(uldzy__yodw, [ind]))
    return char_type(in_bitmap_typ, ind_t), codegen


@intrinsic
def setitem_str_bitmap(typingctx, in_bitmap_typ, ind_t, val_t=None):

    def codegen(context, builder, sig, args):
        uldzy__yodw, ind, val = args
        if in_bitmap_typ == data_ctypes_type:
            tfb__ugnrx = context.make_helper(builder, data_ctypes_type,
                uldzy__yodw)
            uldzy__yodw = tfb__ugnrx.data
        builder.store(val, builder.gep(uldzy__yodw, [ind]))
        return context.get_dummy_value()
    return types.void(in_bitmap_typ, ind_t, char_type), codegen


@intrinsic
def copy_str_arr_slice(typingctx, out_str_arr_typ, in_str_arr_typ, ind_t=None):
    assert out_str_arr_typ == string_array_type and in_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr, ind = args
        onzre__uzlzf = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        eopd__vdup = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        idf__ncdk = context.make_helper(builder, offset_arr_type,
            onzre__uzlzf.offsets).data
        oqj__dugv = context.make_helper(builder, offset_arr_type,
            eopd__vdup.offsets).data
        hdjpc__bihcl = context.make_helper(builder, char_arr_type,
            onzre__uzlzf.data).data
        crq__gdck = context.make_helper(builder, char_arr_type, eopd__vdup.data
            ).data
        hbw__wnlp = context.make_helper(builder, null_bitmap_arr_type,
            onzre__uzlzf.null_bitmap).data
        nru__pto = context.make_helper(builder, null_bitmap_arr_type,
            eopd__vdup.null_bitmap).data
        xdgtt__sppmc = builder.add(ind, context.get_constant(types.intp, 1))
        cgutils.memcpy(builder, oqj__dugv, idf__ncdk, xdgtt__sppmc)
        cgutils.memcpy(builder, crq__gdck, hdjpc__bihcl, builder.load(
            builder.gep(idf__ncdk, [ind])))
        kxl__cabx = builder.add(ind, lir.Constant(lir.IntType(64), 7))
        kcbo__rpdd = builder.lshr(kxl__cabx, lir.Constant(lir.IntType(64), 3))
        cgutils.memcpy(builder, nru__pto, hbw__wnlp, kcbo__rpdd)
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type, ind_t), codegen


@intrinsic
def copy_data(typingctx, str_arr_typ, out_str_arr_typ=None):
    assert str_arr_typ == string_array_type and out_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr = args
        onzre__uzlzf = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        eopd__vdup = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        idf__ncdk = context.make_helper(builder, offset_arr_type,
            onzre__uzlzf.offsets).data
        hdjpc__bihcl = context.make_helper(builder, char_arr_type,
            onzre__uzlzf.data).data
        crq__gdck = context.make_helper(builder, char_arr_type, eopd__vdup.data
            ).data
        num_total_chars = _get_num_total_chars(builder, idf__ncdk,
            onzre__uzlzf.n_arrays)
        cgutils.memcpy(builder, crq__gdck, hdjpc__bihcl, num_total_chars)
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type), codegen


@intrinsic
def copy_non_null_offsets(typingctx, str_arr_typ, out_str_arr_typ=None):
    assert str_arr_typ == string_array_type and out_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr = args
        onzre__uzlzf = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        eopd__vdup = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        idf__ncdk = context.make_helper(builder, offset_arr_type,
            onzre__uzlzf.offsets).data
        oqj__dugv = context.make_helper(builder, offset_arr_type,
            eopd__vdup.offsets).data
        hbw__wnlp = context.make_helper(builder, null_bitmap_arr_type,
            onzre__uzlzf.null_bitmap).data
        hpkyx__vuzv = onzre__uzlzf.n_arrays
        uemp__rtor = context.get_constant(offset_type, 0)
        hxaeg__eze = cgutils.alloca_once_value(builder, uemp__rtor)
        with cgutils.for_range(builder, hpkyx__vuzv) as aerb__fma:
            ggdz__ujobe = lower_is_na(context, builder, hbw__wnlp,
                aerb__fma.index)
            with cgutils.if_likely(builder, builder.not_(ggdz__ujobe)):
                rxz__awpg = builder.load(builder.gep(idf__ncdk, [aerb__fma.
                    index]))
                ovcxg__yeead = builder.load(hxaeg__eze)
                builder.store(rxz__awpg, builder.gep(oqj__dugv, [ovcxg__yeead])
                    )
                builder.store(builder.add(ovcxg__yeead, lir.Constant(
                    context.get_value_type(offset_type), 1)), hxaeg__eze)
        ovcxg__yeead = builder.load(hxaeg__eze)
        rxz__awpg = builder.load(builder.gep(idf__ncdk, [hpkyx__vuzv]))
        builder.store(rxz__awpg, builder.gep(oqj__dugv, [ovcxg__yeead]))
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type), codegen


@intrinsic
def str_copy(typingctx, buff_arr_typ, ind_typ, str_typ, len_typ=None):

    def codegen(context, builder, sig, args):
        pciqs__kuzol, ind, str, abol__sqeib = args
        pciqs__kuzol = context.make_array(sig.args[0])(context, builder,
            pciqs__kuzol)
        fsrtd__dhd = builder.gep(pciqs__kuzol.data, [ind])
        cgutils.raw_memcpy(builder, fsrtd__dhd, str, abol__sqeib, 1)
        return context.get_dummy_value()
    return types.void(null_bitmap_arr_type, types.intp, types.voidptr,
        types.intp), codegen


@intrinsic
def str_copy_ptr(typingctx, ptr_typ, ind_typ, str_typ, len_typ=None):

    def codegen(context, builder, sig, args):
        fsrtd__dhd, ind, tzy__vtre, abol__sqeib = args
        fsrtd__dhd = builder.gep(fsrtd__dhd, [ind])
        cgutils.raw_memcpy(builder, fsrtd__dhd, tzy__vtre, abol__sqeib, 1)
        return context.get_dummy_value()
    return types.void(types.voidptr, types.intp, types.voidptr, types.intp
        ), codegen


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_length(A, i):
    return np.int64(getitem_str_offset(A, i + 1) - getitem_str_offset(A, i))


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_str_length(A, i):
    maf__wjoho = np.int64(getitem_str_offset(A, i))
    hkg__uia = np.int64(getitem_str_offset(A, i + 1))
    l = hkg__uia - maf__wjoho
    msf__tuzg = get_data_ptr_ind(A, maf__wjoho)
    for j in range(l):
        if bodo.hiframes.split_impl.getitem_c_arr(msf__tuzg, j) >= 128:
            return len(A[i])
    return l


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_ptr(A, i):
    return get_data_ptr_ind(A, getitem_str_offset(A, i))


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_copy(B, j, A, i):
    if j == 0:
        setitem_str_offset(B, 0, 0)
    dkz__gdqz = getitem_str_offset(A, i)
    ioqx__yroc = getitem_str_offset(A, i + 1)
    wbm__rleyc = ioqx__yroc - dkz__gdqz
    noqfg__vvvu = getitem_str_offset(B, j)
    ebsan__zwn = noqfg__vvvu + wbm__rleyc
    setitem_str_offset(B, j + 1, ebsan__zwn)
    if str_arr_is_na(A, i):
        str_arr_set_na(B, j)
    else:
        str_arr_set_not_na(B, j)
    if wbm__rleyc != 0:
        xxd__qqpvf = B._data
        bodo.libs.array_item_arr_ext.ensure_data_capacity(xxd__qqpvf, np.
            int64(noqfg__vvvu), np.int64(ebsan__zwn))
        zthsg__ugudi = get_data_ptr(B).data
        cglbz__znp = get_data_ptr(A).data
        memcpy_region(zthsg__ugudi, noqfg__vvvu, cglbz__znp, dkz__gdqz,
            wbm__rleyc, 1)


@numba.njit(no_cpython_wrapper=True)
def get_str_null_bools(str_arr):
    hpkyx__vuzv = len(str_arr)
    hqs__azdsg = np.empty(hpkyx__vuzv, np.bool_)
    for i in range(hpkyx__vuzv):
        hqs__azdsg[i] = bodo.libs.array_kernels.isna(str_arr, i)
    return hqs__azdsg


def to_list_if_immutable_arr(arr, str_null_bools=None):
    return arr


@overload(to_list_if_immutable_arr, no_unliteral=True)
def to_list_if_immutable_arr_overload(data, str_null_bools=None):
    if is_str_arr_type(data) or data == binary_array_type:

        def to_list_impl(data, str_null_bools=None):
            hpkyx__vuzv = len(data)
            l = []
            for i in range(hpkyx__vuzv):
                l.append(data[i])
            return l
        return to_list_impl
    if isinstance(data, types.BaseTuple):
        efb__loxp = data.count
        unlbi__rpfj = ['to_list_if_immutable_arr(data[{}])'.format(i) for i in
            range(efb__loxp)]
        if is_overload_true(str_null_bools):
            unlbi__rpfj += ['get_str_null_bools(data[{}])'.format(i) for i in
                range(efb__loxp) if is_str_arr_type(data.types[i]) or data.
                types[i] == binary_array_type]
        wtwuc__guiqd = 'def f(data, str_null_bools=None):\n'
        wtwuc__guiqd += '  return ({}{})\n'.format(', '.join(unlbi__rpfj), 
            ',' if efb__loxp == 1 else '')
        sum__rulhu = {}
        exec(wtwuc__guiqd, {'to_list_if_immutable_arr':
            to_list_if_immutable_arr, 'get_str_null_bools':
            get_str_null_bools, 'bodo': bodo}, sum__rulhu)
        vprn__yla = sum__rulhu['f']
        return vprn__yla
    return lambda data, str_null_bools=None: data


def cp_str_list_to_array(str_arr, str_list, str_null_bools=None):
    return


@overload(cp_str_list_to_array, no_unliteral=True)
def cp_str_list_to_array_overload(str_arr, list_data, str_null_bools=None):
    if str_arr == string_array_type:
        if is_overload_none(str_null_bools):

            def cp_str_list_impl(str_arr, list_data, str_null_bools=None):
                hpkyx__vuzv = len(list_data)
                for i in range(hpkyx__vuzv):
                    tzy__vtre = list_data[i]
                    str_arr[i] = tzy__vtre
            return cp_str_list_impl
        else:

            def cp_str_list_impl_null(str_arr, list_data, str_null_bools=None):
                hpkyx__vuzv = len(list_data)
                for i in range(hpkyx__vuzv):
                    tzy__vtre = list_data[i]
                    str_arr[i] = tzy__vtre
                    if str_null_bools[i]:
                        str_arr_set_na(str_arr, i)
                    else:
                        str_arr_set_not_na(str_arr, i)
            return cp_str_list_impl_null
    if isinstance(str_arr, types.BaseTuple):
        efb__loxp = str_arr.count
        kpa__bcbr = 0
        wtwuc__guiqd = 'def f(str_arr, list_data, str_null_bools=None):\n'
        for i in range(efb__loxp):
            if is_overload_true(str_null_bools) and str_arr.types[i
                ] == string_array_type:
                wtwuc__guiqd += (
                    """  cp_str_list_to_array(str_arr[{}], list_data[{}], list_data[{}])
"""
                    .format(i, i, efb__loxp + kpa__bcbr))
                kpa__bcbr += 1
            else:
                wtwuc__guiqd += (
                    '  cp_str_list_to_array(str_arr[{}], list_data[{}])\n'.
                    format(i, i))
        wtwuc__guiqd += '  return\n'
        sum__rulhu = {}
        exec(wtwuc__guiqd, {'cp_str_list_to_array': cp_str_list_to_array},
            sum__rulhu)
        pstc__mxtn = sum__rulhu['f']
        return pstc__mxtn
    return lambda str_arr, list_data, str_null_bools=None: None


def str_list_to_array(str_list):
    return str_list


@overload(str_list_to_array, no_unliteral=True)
def str_list_to_array_overload(str_list):
    if isinstance(str_list, types.List) and str_list.dtype == bodo.string_type:

        def str_list_impl(str_list):
            hpkyx__vuzv = len(str_list)
            str_arr = pre_alloc_string_array(hpkyx__vuzv, -1)
            for i in range(hpkyx__vuzv):
                tzy__vtre = str_list[i]
                str_arr[i] = tzy__vtre
            return str_arr
        return str_list_impl
    return lambda str_list: str_list


def get_num_total_chars(A):
    pass


@overload(get_num_total_chars)
def overload_get_num_total_chars(A):
    if isinstance(A, types.List) and A.dtype == string_type:

        def str_list_impl(A):
            hpkyx__vuzv = len(A)
            odse__ytw = 0
            for i in range(hpkyx__vuzv):
                tzy__vtre = A[i]
                odse__ytw += get_utf8_size(tzy__vtre)
            return odse__ytw
        return str_list_impl
    assert A == string_array_type
    return lambda A: num_total_chars(A)


@overload_method(StringArrayType, 'copy', no_unliteral=True)
def str_arr_copy_overload(arr):

    def copy_impl(arr):
        hpkyx__vuzv = len(arr)
        n_chars = num_total_chars(arr)
        iclgt__bjzl = pre_alloc_string_array(hpkyx__vuzv, np.int64(n_chars))
        copy_str_arr_slice(iclgt__bjzl, arr, hpkyx__vuzv)
        return iclgt__bjzl
    return copy_impl


@overload(len, no_unliteral=True)
def str_arr_len_overload(str_arr):
    if str_arr == string_array_type:

        def str_arr_len(str_arr):
            return str_arr.size
        return str_arr_len


@overload_attribute(StringArrayType, 'size')
def str_arr_size_overload(str_arr):
    return lambda str_arr: len(str_arr._data)


@overload_attribute(StringArrayType, 'shape')
def str_arr_shape_overload(str_arr):
    return lambda str_arr: (str_arr.size,)


@overload_attribute(StringArrayType, 'nbytes')
def str_arr_nbytes_overload(str_arr):
    return lambda str_arr: str_arr._data.nbytes


@overload_method(types.Array, 'tolist', no_unliteral=True)
@overload_method(StringArrayType, 'tolist', no_unliteral=True)
def overload_to_list(arr):
    return lambda arr: list(arr)


import llvmlite.binding as ll
from llvmlite import ir as lir
from bodo.libs import array_ext, hstr_ext
ll.add_symbol('get_str_len', hstr_ext.get_str_len)
ll.add_symbol('setitem_string_array', hstr_ext.setitem_string_array)
ll.add_symbol('is_na', hstr_ext.is_na)
ll.add_symbol('string_array_from_sequence', array_ext.
    string_array_from_sequence)
ll.add_symbol('pd_array_from_string_array', hstr_ext.pd_array_from_string_array
    )
ll.add_symbol('np_array_from_string_array', hstr_ext.np_array_from_string_array
    )
ll.add_symbol('convert_len_arr_to_offset32', hstr_ext.
    convert_len_arr_to_offset32)
ll.add_symbol('convert_len_arr_to_offset', hstr_ext.convert_len_arr_to_offset)
ll.add_symbol('set_string_array_range', hstr_ext.set_string_array_range)
ll.add_symbol('str_arr_to_int64', hstr_ext.str_arr_to_int64)
ll.add_symbol('str_arr_to_float64', hstr_ext.str_arr_to_float64)
ll.add_symbol('get_utf8_size', hstr_ext.get_utf8_size)
ll.add_symbol('print_str_arr', hstr_ext.print_str_arr)
ll.add_symbol('inplace_int64_to_str', hstr_ext.inplace_int64_to_str)
inplace_int64_to_str = types.ExternalFunction('inplace_int64_to_str', types
    .void(types.voidptr, types.int64, types.int64))
convert_len_arr_to_offset32 = types.ExternalFunction(
    'convert_len_arr_to_offset32', types.void(types.voidptr, types.intp))
convert_len_arr_to_offset = types.ExternalFunction('convert_len_arr_to_offset',
    types.void(types.voidptr, types.voidptr, types.intp))
setitem_string_array = types.ExternalFunction('setitem_string_array', types
    .void(types.CPointer(offset_type), types.CPointer(char_type), types.
    uint64, types.voidptr, types.intp, offset_type, offset_type, types.intp))
_get_utf8_size = types.ExternalFunction('get_utf8_size', types.intp(types.
    voidptr, types.intp, offset_type))
_print_str_arr = types.ExternalFunction('print_str_arr', types.void(types.
    uint64, types.uint64, types.CPointer(offset_type), types.CPointer(
    char_type)))


@numba.generated_jit(nopython=True)
def empty_str_arr(in_seq):
    wtwuc__guiqd = 'def f(in_seq):\n'
    wtwuc__guiqd += '    n_strs = len(in_seq)\n'
    wtwuc__guiqd += '    A = pre_alloc_string_array(n_strs, -1)\n'
    wtwuc__guiqd += '    return A\n'
    sum__rulhu = {}
    exec(wtwuc__guiqd, {'pre_alloc_string_array': pre_alloc_string_array},
        sum__rulhu)
    miat__mgq = sum__rulhu['f']
    return miat__mgq


@numba.generated_jit(nopython=True)
def str_arr_from_sequence(in_seq):
    if in_seq.dtype == bodo.bytes_type:
        kxyt__foxrz = 'pre_alloc_binary_array'
    else:
        kxyt__foxrz = 'pre_alloc_string_array'
    wtwuc__guiqd = 'def f(in_seq):\n'
    wtwuc__guiqd += '    n_strs = len(in_seq)\n'
    wtwuc__guiqd += f'    A = {kxyt__foxrz}(n_strs, -1)\n'
    wtwuc__guiqd += '    for i in range(n_strs):\n'
    wtwuc__guiqd += '        A[i] = in_seq[i]\n'
    wtwuc__guiqd += '    return A\n'
    sum__rulhu = {}
    exec(wtwuc__guiqd, {'pre_alloc_string_array': pre_alloc_string_array,
        'pre_alloc_binary_array': pre_alloc_binary_array}, sum__rulhu)
    miat__mgq = sum__rulhu['f']
    return miat__mgq


@intrinsic
def set_all_offsets_to_0(typingctx, arr_typ=None):
    assert arr_typ in (string_array_type, binary_array_type
        ), 'set_all_offsets_to_0 requires a string or binary array'

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, in_str_arr,
            sig.args[0])
        qben__bxirw = builder.add(ygx__twt.n_arrays, lir.Constant(lir.
            IntType(64), 1))
        zlar__dumi = builder.lshr(lir.Constant(lir.IntType(64), offset_type
            .bitwidth), lir.Constant(lir.IntType(64), 3))
        kcbo__rpdd = builder.mul(qben__bxirw, zlar__dumi)
        fbd__afhn = context.make_array(offset_arr_type)(context, builder,
            ygx__twt.offsets).data
        cgutils.memset(builder, fbd__afhn, kcbo__rpdd, 0)
        return context.get_dummy_value()
    return types.none(arr_typ), codegen


@intrinsic
def set_bitmap_all_NA(typingctx, arr_typ=None):
    assert arr_typ in (string_array_type, binary_array_type
        ), 'set_bitmap_all_NA requires a string or binary array'

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, in_str_arr,
            sig.args[0])
        xyj__riin = ygx__twt.n_arrays
        kcbo__rpdd = builder.lshr(builder.add(xyj__riin, lir.Constant(lir.
            IntType(64), 7)), lir.Constant(lir.IntType(64), 3))
        hxooo__ixau = context.make_array(null_bitmap_arr_type)(context,
            builder, ygx__twt.null_bitmap).data
        cgutils.memset(builder, hxooo__ixau, kcbo__rpdd, 0)
        return context.get_dummy_value()
    return types.none(arr_typ), codegen


@numba.njit
def pre_alloc_string_array(n_strs, n_chars):
    if n_chars is None:
        n_chars = -1
    str_arr = init_str_arr(bodo.libs.array_item_arr_ext.
        pre_alloc_array_item_array(np.int64(n_strs), (np.int64(n_chars),),
        char_arr_type))
    if n_chars == 0:
        set_all_offsets_to_0(str_arr)
    return str_arr


@register_jitable
def gen_na_str_array_lens(n_strs, total_len, len_arr):
    str_arr = pre_alloc_string_array(n_strs, total_len)
    set_bitmap_all_NA(str_arr)
    offsets = bodo.libs.array_item_arr_ext.get_offsets(str_arr._data)
    qdd__qyads = 0
    if total_len == 0:
        for i in range(len(offsets)):
            offsets[i] = 0
    else:
        sur__nmj = len(len_arr)
        for i in range(sur__nmj):
            offsets[i] = qdd__qyads
            qdd__qyads += len_arr[i]
        offsets[sur__nmj] = qdd__qyads
    return str_arr


kBitmask = np.array([1, 2, 4, 8, 16, 32, 64, 128], dtype=np.uint8)


@numba.njit
def set_bit_to(bits, i, bit_is_set):
    ctl__oxt = i // 8
    bdfr__hzmw = getitem_str_bitmap(bits, ctl__oxt)
    bdfr__hzmw ^= np.uint8(-np.uint8(bit_is_set) ^ bdfr__hzmw) & kBitmask[i % 8
        ]
    setitem_str_bitmap(bits, ctl__oxt, bdfr__hzmw)


@numba.njit
def get_bit_bitmap(bits, i):
    return getitem_str_bitmap(bits, i >> 3) >> (i & 7) & 1


@numba.njit
def copy_nulls_range(out_str_arr, in_str_arr, out_start):
    ortcs__eryvo = get_null_bitmap_ptr(out_str_arr)
    jtyqk__uig = get_null_bitmap_ptr(in_str_arr)
    for j in range(len(in_str_arr)):
        bpxzh__rmh = get_bit_bitmap(jtyqk__uig, j)
        set_bit_to(ortcs__eryvo, out_start + j, bpxzh__rmh)


@intrinsic
def set_string_array_range(typingctx, out_typ, in_typ, curr_str_typ,
    curr_chars_typ=None):
    assert out_typ == string_array_type and in_typ == string_array_type or out_typ == binary_array_type and in_typ == binary_array_type, 'set_string_array_range requires string or binary arrays'
    assert isinstance(curr_str_typ, types.Integer) and isinstance(
        curr_chars_typ, types.Integer
        ), 'set_string_array_range requires integer indices'

    def codegen(context, builder, sig, args):
        out_arr, nuyh__xhb, focb__dnt, txozr__gwe = args
        onzre__uzlzf = _get_str_binary_arr_payload(context, builder,
            nuyh__xhb, string_array_type)
        eopd__vdup = _get_str_binary_arr_payload(context, builder, out_arr,
            string_array_type)
        idf__ncdk = context.make_helper(builder, offset_arr_type,
            onzre__uzlzf.offsets).data
        oqj__dugv = context.make_helper(builder, offset_arr_type,
            eopd__vdup.offsets).data
        hdjpc__bihcl = context.make_helper(builder, char_arr_type,
            onzre__uzlzf.data).data
        crq__gdck = context.make_helper(builder, char_arr_type, eopd__vdup.data
            ).data
        num_total_chars = _get_num_total_chars(builder, idf__ncdk,
            onzre__uzlzf.n_arrays)
        jmn__zsnhc = lir.FunctionType(lir.VoidType(), [lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(64), lir.IntType(64), lir.IntType(64),
            lir.IntType(64)])
        ugzwp__lcc = cgutils.get_or_insert_function(builder.module,
            jmn__zsnhc, name='set_string_array_range')
        builder.call(ugzwp__lcc, [oqj__dugv, crq__gdck, idf__ncdk,
            hdjpc__bihcl, focb__dnt, txozr__gwe, onzre__uzlzf.n_arrays,
            num_total_chars])
        zhk__qayq = context.typing_context.resolve_value_type(copy_nulls_range)
        euq__turm = zhk__qayq.get_call_type(context.typing_context, (
            string_array_type, string_array_type, types.int64), {})
        ppq__tstmb = context.get_function(zhk__qayq, euq__turm)
        ppq__tstmb(builder, (out_arr, nuyh__xhb, focb__dnt))
        return context.get_dummy_value()
    sig = types.void(out_typ, in_typ, types.intp, types.intp)
    return sig, codegen


@box(BinaryArrayType)
@box(StringArrayType)
def box_str_arr(typ, val, c):
    assert typ in [binary_array_type, string_array_type]
    zpe__awp = c.context.make_helper(c.builder, typ, val)
    pbvvq__xaxe = ArrayItemArrayType(char_arr_type)
    ygx__twt = _get_array_item_arr_payload(c.context, c.builder,
        pbvvq__xaxe, zpe__awp.data)
    hjyto__vnr = c.context.get_constant(types.int32, int(typ ==
        binary_array_type))
    gsl__oiidp = 'np_array_from_string_array'
    if use_pd_string_array and typ != binary_array_type:
        gsl__oiidp = 'pd_array_from_string_array'
    jmn__zsnhc = lir.FunctionType(c.context.get_argument_type(types.
        pyobject), [lir.IntType(64), lir.IntType(offset_type.bitwidth).
        as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
        as_pointer(), lir.IntType(32)])
    yzy__tei = cgutils.get_or_insert_function(c.builder.module, jmn__zsnhc,
        name=gsl__oiidp)
    bqdsh__hvs = c.context.make_array(offset_arr_type)(c.context, c.builder,
        ygx__twt.offsets).data
    msf__tuzg = c.context.make_array(char_arr_type)(c.context, c.builder,
        ygx__twt.data).data
    hxooo__ixau = c.context.make_array(null_bitmap_arr_type)(c.context, c.
        builder, ygx__twt.null_bitmap).data
    arr = c.builder.call(yzy__tei, [ygx__twt.n_arrays, bqdsh__hvs,
        msf__tuzg, hxooo__ixau, hjyto__vnr])
    c.context.nrt.decref(c.builder, typ, val)
    return arr


@intrinsic
def str_arr_is_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, in_str_arr,
            string_array_type)
        hxooo__ixau = context.make_array(null_bitmap_arr_type)(context,
            builder, ygx__twt.null_bitmap).data
        gjhw__krkyw = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        nxixv__gqfn = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        bdfr__hzmw = builder.load(builder.gep(hxooo__ixau, [gjhw__krkyw],
            inbounds=True))
        mwr__btq = lir.ArrayType(lir.IntType(8), 8)
        zdexk__jcdc = cgutils.alloca_once_value(builder, lir.Constant(
            mwr__btq, (1, 2, 4, 8, 16, 32, 64, 128)))
        nww__gst = builder.load(builder.gep(zdexk__jcdc, [lir.Constant(lir.
            IntType(64), 0), nxixv__gqfn], inbounds=True))
        return builder.icmp_unsigned('==', builder.and_(bdfr__hzmw,
            nww__gst), lir.Constant(lir.IntType(8), 0))
    return types.bool_(str_arr_typ, types.intp), codegen


@intrinsic
def str_arr_set_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, in_str_arr,
            string_array_type)
        gjhw__krkyw = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        nxixv__gqfn = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        hxooo__ixau = context.make_array(null_bitmap_arr_type)(context,
            builder, ygx__twt.null_bitmap).data
        offsets = context.make_helper(builder, offset_arr_type, ygx__twt.
            offsets).data
        mqwme__nilx = builder.gep(hxooo__ixau, [gjhw__krkyw], inbounds=True)
        bdfr__hzmw = builder.load(mqwme__nilx)
        mwr__btq = lir.ArrayType(lir.IntType(8), 8)
        zdexk__jcdc = cgutils.alloca_once_value(builder, lir.Constant(
            mwr__btq, (1, 2, 4, 8, 16, 32, 64, 128)))
        nww__gst = builder.load(builder.gep(zdexk__jcdc, [lir.Constant(lir.
            IntType(64), 0), nxixv__gqfn], inbounds=True))
        nww__gst = builder.xor(nww__gst, lir.Constant(lir.IntType(8), -1))
        builder.store(builder.and_(bdfr__hzmw, nww__gst), mqwme__nilx)
        if str_arr_typ == string_array_type:
            lrptr__ncyv = builder.add(ind, lir.Constant(lir.IntType(64), 1))
            lvg__kguib = builder.icmp_unsigned('!=', lrptr__ncyv, ygx__twt.
                n_arrays)
            with builder.if_then(lvg__kguib):
                builder.store(builder.load(builder.gep(offsets, [ind])),
                    builder.gep(offsets, [lrptr__ncyv]))
        return context.get_dummy_value()
    return types.void(str_arr_typ, types.intp), codegen


@intrinsic
def str_arr_set_not_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, in_str_arr,
            string_array_type)
        gjhw__krkyw = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        nxixv__gqfn = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        hxooo__ixau = context.make_array(null_bitmap_arr_type)(context,
            builder, ygx__twt.null_bitmap).data
        mqwme__nilx = builder.gep(hxooo__ixau, [gjhw__krkyw], inbounds=True)
        bdfr__hzmw = builder.load(mqwme__nilx)
        mwr__btq = lir.ArrayType(lir.IntType(8), 8)
        zdexk__jcdc = cgutils.alloca_once_value(builder, lir.Constant(
            mwr__btq, (1, 2, 4, 8, 16, 32, 64, 128)))
        nww__gst = builder.load(builder.gep(zdexk__jcdc, [lir.Constant(lir.
            IntType(64), 0), nxixv__gqfn], inbounds=True))
        builder.store(builder.or_(bdfr__hzmw, nww__gst), mqwme__nilx)
        return context.get_dummy_value()
    return types.void(str_arr_typ, types.intp), codegen


@intrinsic
def set_null_bits_to_value(typingctx, arr_typ, value_typ=None):
    assert (arr_typ == string_array_type or arr_typ == binary_array_type
        ) and is_overload_constant_int(value_typ)

    def codegen(context, builder, sig, args):
        in_str_arr, value = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, in_str_arr,
            string_array_type)
        kcbo__rpdd = builder.udiv(builder.add(ygx__twt.n_arrays, lir.
            Constant(lir.IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
        hxooo__ixau = context.make_array(null_bitmap_arr_type)(context,
            builder, ygx__twt.null_bitmap).data
        cgutils.memset(builder, hxooo__ixau, kcbo__rpdd, value)
        return context.get_dummy_value()
    return types.none(arr_typ, types.int8), codegen


def _get_str_binary_arr_data_payload_ptr(context, builder, str_arr):
    pgbsn__gik = context.make_helper(builder, string_array_type, str_arr)
    pbvvq__xaxe = ArrayItemArrayType(char_arr_type)
    blwxw__luaj = context.make_helper(builder, pbvvq__xaxe, pgbsn__gik.data)
    oqacp__vqha = ArrayItemArrayPayloadType(pbvvq__xaxe)
    mfcc__dke = context.nrt.meminfo_data(builder, blwxw__luaj.meminfo)
    lckuu__qrq = builder.bitcast(mfcc__dke, context.get_value_type(
        oqacp__vqha).as_pointer())
    return lckuu__qrq


@intrinsic
def move_str_binary_arr_payload(typingctx, to_arr_typ, from_arr_typ=None):
    assert to_arr_typ == string_array_type and from_arr_typ == string_array_type or to_arr_typ == binary_array_type and from_arr_typ == binary_array_type

    def codegen(context, builder, sig, args):
        mtak__pcg, bxies__ohoy = args
        zbui__wyjj = _get_str_binary_arr_data_payload_ptr(context, builder,
            bxies__ohoy)
        zbt__hnyg = _get_str_binary_arr_data_payload_ptr(context, builder,
            mtak__pcg)
        xbeo__ksi = _get_str_binary_arr_payload(context, builder,
            bxies__ohoy, sig.args[1])
        nxsa__rrit = _get_str_binary_arr_payload(context, builder,
            mtak__pcg, sig.args[0])
        context.nrt.incref(builder, char_arr_type, xbeo__ksi.data)
        context.nrt.incref(builder, offset_arr_type, xbeo__ksi.offsets)
        context.nrt.incref(builder, null_bitmap_arr_type, xbeo__ksi.null_bitmap
            )
        context.nrt.decref(builder, char_arr_type, nxsa__rrit.data)
        context.nrt.decref(builder, offset_arr_type, nxsa__rrit.offsets)
        context.nrt.decref(builder, null_bitmap_arr_type, nxsa__rrit.
            null_bitmap)
        builder.store(builder.load(zbui__wyjj), zbt__hnyg)
        return context.get_dummy_value()
    return types.none(to_arr_typ, from_arr_typ), codegen


dummy_use = numba.njit(lambda a: None)


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_utf8_size(s):
    if isinstance(s, types.StringLiteral):
        l = len(s.literal_value.encode())
        return lambda s: l

    def impl(s):
        if s is None:
            return 0
        s = bodo.utils.indexing.unoptional(s)
        if s._is_ascii == 1:
            return len(s)
        hpkyx__vuzv = _get_utf8_size(s._data, s._length, s._kind)
        dummy_use(s)
        return hpkyx__vuzv
    return impl


@intrinsic
def setitem_str_arr_ptr(typingctx, str_arr_t, ind_t, ptr_t, len_t=None):

    def codegen(context, builder, sig, args):
        arr, ind, fsrtd__dhd, dqe__pospt = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, arr, sig.
            args[0])
        offsets = context.make_helper(builder, offset_arr_type, ygx__twt.
            offsets).data
        data = context.make_helper(builder, char_arr_type, ygx__twt.data).data
        jmn__zsnhc = lir.FunctionType(lir.VoidType(), [lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(64),
            lir.IntType(32), lir.IntType(32), lir.IntType(64)])
        ukyn__tfvuw = cgutils.get_or_insert_function(builder.module,
            jmn__zsnhc, name='setitem_string_array')
        ssyjo__tjbed = context.get_constant(types.int32, -1)
        ldek__zjlew = context.get_constant(types.int32, 1)
        num_total_chars = _get_num_total_chars(builder, offsets, ygx__twt.
            n_arrays)
        builder.call(ukyn__tfvuw, [offsets, data, num_total_chars, builder.
            extract_value(fsrtd__dhd, 0), dqe__pospt, ssyjo__tjbed,
            ldek__zjlew, ind])
        return context.get_dummy_value()
    return types.void(str_arr_t, ind_t, ptr_t, len_t), codegen


def lower_is_na(context, builder, bull_bitmap, ind):
    jmn__zsnhc = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
        as_pointer(), lir.IntType(64)])
    sabv__rmp = cgutils.get_or_insert_function(builder.module, jmn__zsnhc,
        name='is_na')
    return builder.call(sabv__rmp, [bull_bitmap, ind])


@intrinsic
def _memcpy(typingctx, dest_t, src_t, count_t, item_size_t=None):

    def codegen(context, builder, sig, args):
        vbv__ldcy, wdf__lrbr, efb__loxp, sdc__vceg = args
        cgutils.raw_memcpy(builder, vbv__ldcy, wdf__lrbr, efb__loxp, sdc__vceg)
        return context.get_dummy_value()
    return types.void(types.voidptr, types.voidptr, types.intp, types.intp
        ), codegen


@numba.njit
def print_str_arr(arr):
    _print_str_arr(num_strings(arr), num_total_chars(arr), get_offset_ptr(
        arr), get_data_ptr(arr))


def inplace_eq(A, i, val):
    return A[i] == val


@overload(inplace_eq)
def inplace_eq_overload(A, ind, val):

    def impl(A, ind, val):
        ohqs__jyqb, hzr__sqx = unicode_to_utf8_and_len(val)
        gxj__drxk = getitem_str_offset(A, ind)
        crolf__pyk = getitem_str_offset(A, ind + 1)
        eel__mon = crolf__pyk - gxj__drxk
        if eel__mon != hzr__sqx:
            return False
        fsrtd__dhd = get_data_ptr_ind(A, gxj__drxk)
        return memcmp(fsrtd__dhd, ohqs__jyqb, hzr__sqx) == 0
    return impl


def str_arr_setitem_int_to_str(A, ind, value):
    A[ind] = str(value)


@overload(str_arr_setitem_int_to_str)
def overload_str_arr_setitem_int_to_str(A, ind, val):

    def impl(A, ind, val):
        gxj__drxk = getitem_str_offset(A, ind)
        eel__mon = bodo.libs.str_ext.int_to_str_len(val)
        mmbf__bxif = gxj__drxk + eel__mon
        bodo.libs.array_item_arr_ext.ensure_data_capacity(A._data,
            gxj__drxk, mmbf__bxif)
        fsrtd__dhd = get_data_ptr_ind(A, gxj__drxk)
        inplace_int64_to_str(fsrtd__dhd, eel__mon, val)
        setitem_str_offset(A, ind + 1, gxj__drxk + eel__mon)
        str_arr_set_not_na(A, ind)
    return impl


@intrinsic
def inplace_set_NA_str(typingctx, ptr_typ=None):

    def codegen(context, builder, sig, args):
        fsrtd__dhd, = args
        gcw__vbxvt = context.insert_const_string(builder.module, '<NA>')
        izov__ppjkv = lir.Constant(lir.IntType(64), len('<NA>'))
        cgutils.raw_memcpy(builder, fsrtd__dhd, gcw__vbxvt, izov__ppjkv, 1)
    return types.none(types.voidptr), codegen


def str_arr_setitem_NA_str(A, ind):
    A[ind] = '<NA>'


@overload(str_arr_setitem_NA_str)
def overload_str_arr_setitem_NA_str(A, ind):
    lep__iqyf = len('<NA>')

    def impl(A, ind):
        gxj__drxk = getitem_str_offset(A, ind)
        mmbf__bxif = gxj__drxk + lep__iqyf
        bodo.libs.array_item_arr_ext.ensure_data_capacity(A._data,
            gxj__drxk, mmbf__bxif)
        fsrtd__dhd = get_data_ptr_ind(A, gxj__drxk)
        inplace_set_NA_str(fsrtd__dhd)
        setitem_str_offset(A, ind + 1, gxj__drxk + lep__iqyf)
        str_arr_set_not_na(A, ind)
    return impl


@overload(operator.getitem, no_unliteral=True)
def str_arr_getitem_int(A, ind):
    if A != string_array_type:
        return
    if isinstance(ind, types.Integer):

        def str_arr_getitem_impl(A, ind):
            if ind < 0:
                ind += A.size
            gxj__drxk = getitem_str_offset(A, ind)
            crolf__pyk = getitem_str_offset(A, ind + 1)
            dqe__pospt = crolf__pyk - gxj__drxk
            fsrtd__dhd = get_data_ptr_ind(A, gxj__drxk)
            xbh__aji = decode_utf8(fsrtd__dhd, dqe__pospt)
            return xbh__aji
        return str_arr_getitem_impl
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:

        def bool_impl(A, ind):
            ind = bodo.utils.conversion.coerce_to_ndarray(ind)
            hpkyx__vuzv = len(A)
            n_strs = 0
            n_chars = 0
            for i in range(hpkyx__vuzv):
                if not bodo.libs.array_kernels.isna(ind, i) and ind[i]:
                    n_strs += 1
                    n_chars += get_str_arr_item_length(A, i)
            out_arr = pre_alloc_string_array(n_strs, n_chars)
            zthsg__ugudi = get_data_ptr(out_arr).data
            cglbz__znp = get_data_ptr(A).data
            kpa__bcbr = 0
            ovcxg__yeead = 0
            setitem_str_offset(out_arr, 0, 0)
            for i in range(hpkyx__vuzv):
                if not bodo.libs.array_kernels.isna(ind, i) and ind[i]:
                    xiaf__opa = get_str_arr_item_length(A, i)
                    if xiaf__opa == 1:
                        copy_single_char(zthsg__ugudi, ovcxg__yeead,
                            cglbz__znp, getitem_str_offset(A, i))
                    else:
                        memcpy_region(zthsg__ugudi, ovcxg__yeead,
                            cglbz__znp, getitem_str_offset(A, i), xiaf__opa, 1)
                    ovcxg__yeead += xiaf__opa
                    setitem_str_offset(out_arr, kpa__bcbr + 1, ovcxg__yeead)
                    if str_arr_is_na(A, i):
                        str_arr_set_na(out_arr, kpa__bcbr)
                    else:
                        str_arr_set_not_na(out_arr, kpa__bcbr)
                    kpa__bcbr += 1
            return out_arr
        return bool_impl
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def str_arr_arr_impl(A, ind):
            hpkyx__vuzv = len(ind)
            out_arr = pre_alloc_string_array(hpkyx__vuzv, -1)
            kpa__bcbr = 0
            for i in range(hpkyx__vuzv):
                tzy__vtre = A[ind[i]]
                out_arr[kpa__bcbr] = tzy__vtre
                if str_arr_is_na(A, ind[i]):
                    str_arr_set_na(out_arr, kpa__bcbr)
                kpa__bcbr += 1
            return out_arr
        return str_arr_arr_impl
    if isinstance(ind, types.SliceType):

        def str_arr_slice_impl(A, ind):
            hpkyx__vuzv = len(A)
            qucie__pquj = numba.cpython.unicode._normalize_slice(ind,
                hpkyx__vuzv)
            nbz__spfx = numba.cpython.unicode._slice_span(qucie__pquj)
            if qucie__pquj.step == 1:
                gxj__drxk = getitem_str_offset(A, qucie__pquj.start)
                crolf__pyk = getitem_str_offset(A, qucie__pquj.stop)
                n_chars = crolf__pyk - gxj__drxk
                iclgt__bjzl = pre_alloc_string_array(nbz__spfx, np.int64(
                    n_chars))
                for i in range(nbz__spfx):
                    iclgt__bjzl[i] = A[qucie__pquj.start + i]
                    if str_arr_is_na(A, qucie__pquj.start + i):
                        str_arr_set_na(iclgt__bjzl, i)
                return iclgt__bjzl
            else:
                iclgt__bjzl = pre_alloc_string_array(nbz__spfx, -1)
                for i in range(nbz__spfx):
                    iclgt__bjzl[i] = A[qucie__pquj.start + i * qucie__pquj.step
                        ]
                    if str_arr_is_na(A, qucie__pquj.start + i * qucie__pquj
                        .step):
                        str_arr_set_na(iclgt__bjzl, i)
                return iclgt__bjzl
        return str_arr_slice_impl
    raise BodoError(
        f'getitem for StringArray with indexing type {ind} not supported.')


dummy_use = numba.njit(lambda a: None)


@overload(operator.setitem)
def str_arr_setitem(A, idx, val):
    if A != string_array_type:
        return
    if val == types.none or isinstance(val, types.optional):
        return
    flwh__wxzt = (
        f'StringArray setitem with index {idx} and value {val} not supported yet.'
        )
    if isinstance(idx, types.Integer):
        if val != string_type:
            raise BodoError(flwh__wxzt)
        sltx__tgx = 4

        def impl_scalar(A, idx, val):
            ykkws__rnfw = (val._length if val._is_ascii else sltx__tgx *
                val._length)
            xxd__qqpvf = A._data
            gxj__drxk = np.int64(getitem_str_offset(A, idx))
            mmbf__bxif = gxj__drxk + ykkws__rnfw
            bodo.libs.array_item_arr_ext.ensure_data_capacity(xxd__qqpvf,
                gxj__drxk, mmbf__bxif)
            setitem_string_array(get_offset_ptr(A), get_data_ptr(A),
                mmbf__bxif, val._data, val._length, val._kind, val.
                _is_ascii, idx)
            str_arr_set_not_na(A, idx)
            dummy_use(A)
            dummy_use(val)
        return impl_scalar
    if isinstance(idx, types.SliceType):
        if val == string_array_type:

            def impl_slice(A, idx, val):
                qucie__pquj = numba.cpython.unicode._normalize_slice(idx,
                    len(A))
                maf__wjoho = qucie__pquj.start
                xxd__qqpvf = A._data
                gxj__drxk = np.int64(getitem_str_offset(A, maf__wjoho))
                mmbf__bxif = gxj__drxk + np.int64(num_total_chars(val))
                bodo.libs.array_item_arr_ext.ensure_data_capacity(xxd__qqpvf,
                    gxj__drxk, mmbf__bxif)
                set_string_array_range(A, val, maf__wjoho, gxj__drxk)
                rlu__ets = 0
                for i in range(qucie__pquj.start, qucie__pquj.stop,
                    qucie__pquj.step):
                    if str_arr_is_na(val, rlu__ets):
                        str_arr_set_na(A, i)
                    else:
                        str_arr_set_not_na(A, i)
                    rlu__ets += 1
            return impl_slice
        elif isinstance(val, types.List) and val.dtype == string_type:

            def impl_slice_list(A, idx, val):
                fzciq__gmnw = str_list_to_array(val)
                A[idx] = fzciq__gmnw
            return impl_slice_list
        elif val == string_type:

            def impl_slice(A, idx, val):
                qucie__pquj = numba.cpython.unicode._normalize_slice(idx,
                    len(A))
                for i in range(qucie__pquj.start, qucie__pquj.stop,
                    qucie__pquj.step):
                    A[i] = val
            return impl_slice
        else:
            raise BodoError(flwh__wxzt)
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        if val == string_type:

            def impl_bool_scalar(A, idx, val):
                hpkyx__vuzv = len(A)
                idx = bodo.utils.conversion.coerce_to_ndarray(idx)
                out_arr = pre_alloc_string_array(hpkyx__vuzv, -1)
                for i in numba.parfors.parfor.internal_prange(hpkyx__vuzv):
                    if not bodo.libs.array_kernels.isna(idx, i) and idx[i]:
                        out_arr[i] = val
                    elif bodo.libs.array_kernels.isna(A, i):
                        out_arr[i] = ''
                        str_arr_set_na(out_arr, i)
                    else:
                        get_str_arr_item_copy(out_arr, i, A, i)
                move_str_binary_arr_payload(A, out_arr)
            return impl_bool_scalar
        elif val == string_array_type or isinstance(val, types.Array
            ) and isinstance(val.dtype, types.UnicodeCharSeq):

            def impl_bool_arr(A, idx, val):
                hpkyx__vuzv = len(A)
                idx = bodo.utils.conversion.coerce_to_array(idx,
                    use_nullable_array=True)
                out_arr = pre_alloc_string_array(hpkyx__vuzv, -1)
                ioakp__caf = 0
                for i in numba.parfors.parfor.internal_prange(hpkyx__vuzv):
                    if not bodo.libs.array_kernels.isna(idx, i) and idx[i]:
                        if bodo.libs.array_kernels.isna(val, ioakp__caf):
                            out_arr[i] = ''
                            str_arr_set_na(out_arr, ioakp__caf)
                        else:
                            out_arr[i] = str(val[ioakp__caf])
                        ioakp__caf += 1
                    elif bodo.libs.array_kernels.isna(A, i):
                        out_arr[i] = ''
                        str_arr_set_na(out_arr, i)
                    else:
                        get_str_arr_item_copy(out_arr, i, A, i)
                move_str_binary_arr_payload(A, out_arr)
            return impl_bool_arr
        else:
            raise BodoError(flwh__wxzt)
    raise BodoError(flwh__wxzt)


@overload_attribute(StringArrayType, 'dtype')
def overload_str_arr_dtype(A):
    return lambda A: pd.StringDtype()


@overload_attribute(StringArrayType, 'ndim')
def overload_str_arr_ndim(A):
    return lambda A: 1


@overload_method(StringArrayType, 'astype', no_unliteral=True)
def overload_str_arr_astype(A, dtype, copy=True):
    if dtype == types.unicode_type:
        raise_bodo_error(
            "StringArray.astype(): 'dtype' when passed as string must be a constant value"
            )
    if isinstance(dtype, types.Function) and dtype.key[0] == str:
        return lambda A, dtype, copy=True: A
    smfv__itp = parse_dtype(dtype, 'StringArray.astype')
    if not isinstance(smfv__itp, (types.Float, types.Integer)):
        raise BodoError('invalid dtype in StringArray.astype()')
    if isinstance(smfv__itp, types.Float):

        def impl_float(A, dtype, copy=True):
            numba.parfors.parfor.init_prange()
            hpkyx__vuzv = len(A)
            B = np.empty(hpkyx__vuzv, smfv__itp)
            for i in numba.parfors.parfor.internal_prange(hpkyx__vuzv):
                if bodo.libs.array_kernels.isna(A, i):
                    B[i] = np.nan
                else:
                    B[i] = float(A[i])
            return B
        return impl_float
    else:

        def impl_int(A, dtype, copy=True):
            numba.parfors.parfor.init_prange()
            hpkyx__vuzv = len(A)
            B = np.empty(hpkyx__vuzv, smfv__itp)
            for i in numba.parfors.parfor.internal_prange(hpkyx__vuzv):
                B[i] = int(A[i])
            return B
        return impl_int


@intrinsic
def decode_utf8(typingctx, ptr_t, len_t=None):

    def codegen(context, builder, sig, args):
        fsrtd__dhd, dqe__pospt = args
        plrch__yxg = context.get_python_api(builder)
        dbooi__pyfs = plrch__yxg.string_from_string_and_size(fsrtd__dhd,
            dqe__pospt)
        mph__bkt = plrch__yxg.to_native_value(string_type, dbooi__pyfs).value
        gzj__mks = cgutils.create_struct_proxy(string_type)(context,
            builder, mph__bkt)
        gzj__mks.hash = gzj__mks.hash.type(-1)
        plrch__yxg.decref(dbooi__pyfs)
        return gzj__mks._getvalue()
    return string_type(types.voidptr, types.intp), codegen


def get_arr_data_ptr(arr, ind):
    return arr


@overload(get_arr_data_ptr, no_unliteral=True)
def overload_get_arr_data_ptr(arr, ind):
    assert isinstance(types.unliteral(ind), types.Integer)
    if isinstance(arr, bodo.libs.int_arr_ext.IntegerArrayType):

        def impl_int(arr, ind):
            return bodo.hiframes.split_impl.get_c_arr_ptr(arr._data.ctypes, ind
                )
        return impl_int
    assert isinstance(arr, types.Array)

    def impl_np(arr, ind):
        return bodo.hiframes.split_impl.get_c_arr_ptr(arr.ctypes, ind)
    return impl_np


def set_to_numeric_out_na_err(out_arr, out_ind, err_code):
    pass


@overload(set_to_numeric_out_na_err)
def set_to_numeric_out_na_err_overload(out_arr, out_ind, err_code):
    if isinstance(out_arr, bodo.libs.int_arr_ext.IntegerArrayType):

        def impl_int(out_arr, out_ind, err_code):
            bodo.libs.int_arr_ext.set_bit_to_arr(out_arr._null_bitmap,
                out_ind, 0 if err_code == -1 else 1)
        return impl_int
    assert isinstance(out_arr, types.Array)
    if isinstance(out_arr.dtype, types.Float):

        def impl_np(out_arr, out_ind, err_code):
            if err_code == -1:
                out_arr[out_ind] = np.nan
        return impl_np
    return lambda out_arr, out_ind, err_code: None


@numba.njit(no_cpython_wrapper=True)
def str_arr_item_to_numeric(out_arr, out_ind, str_arr, ind):
    str_arr = decode_if_dict_array(str_arr)
    err_code = _str_arr_item_to_numeric(get_arr_data_ptr(out_arr, out_ind),
        str_arr, ind, out_arr.dtype)
    set_to_numeric_out_na_err(out_arr, out_ind, err_code)


@intrinsic
def _str_arr_item_to_numeric(typingctx, out_ptr_t, str_arr_t, ind_t,
    out_dtype_t=None):
    assert str_arr_t == string_array_type, '_str_arr_item_to_numeric: str arr expected'
    assert ind_t == types.int64, '_str_arr_item_to_numeric: integer index expected'

    def codegen(context, builder, sig, args):
        daxh__sdfl, arr, ind, xsqoc__fkjr = args
        ygx__twt = _get_str_binary_arr_payload(context, builder, arr,
            string_array_type)
        offsets = context.make_helper(builder, offset_arr_type, ygx__twt.
            offsets).data
        data = context.make_helper(builder, char_arr_type, ygx__twt.data).data
        jmn__zsnhc = lir.FunctionType(lir.IntType(32), [daxh__sdfl.type,
            lir.IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(64)])
        mpvcw__qkr = 'str_arr_to_int64'
        if sig.args[3].dtype == types.float64:
            mpvcw__qkr = 'str_arr_to_float64'
        else:
            assert sig.args[3].dtype == types.int64
        fohw__khste = cgutils.get_or_insert_function(builder.module,
            jmn__zsnhc, mpvcw__qkr)
        return builder.call(fohw__khste, [daxh__sdfl, offsets, data, ind])
    return types.int32(out_ptr_t, string_array_type, types.int64, out_dtype_t
        ), codegen


@unbox(BinaryArrayType)
@unbox(StringArrayType)
def unbox_str_series(typ, val, c):
    hjyto__vnr = c.context.get_constant(types.int32, int(typ ==
        binary_array_type))
    jmn__zsnhc = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.IntType
        (8).as_pointer(), lir.IntType(32)])
    hotdb__scnq = cgutils.get_or_insert_function(c.builder.module,
        jmn__zsnhc, name='string_array_from_sequence')
    gzpy__xtabd = c.builder.call(hotdb__scnq, [val, hjyto__vnr])
    pbvvq__xaxe = ArrayItemArrayType(char_arr_type)
    blwxw__luaj = c.context.make_helper(c.builder, pbvvq__xaxe)
    blwxw__luaj.meminfo = gzpy__xtabd
    pgbsn__gik = c.context.make_helper(c.builder, typ)
    xxd__qqpvf = blwxw__luaj._getvalue()
    pgbsn__gik.data = xxd__qqpvf
    puf__zyvcm = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(pgbsn__gik._getvalue(), is_error=puf__zyvcm)


@lower_constant(BinaryArrayType)
@lower_constant(StringArrayType)
def lower_constant_str_arr(context, builder, typ, pyval):
    hpkyx__vuzv = len(pyval)
    ovcxg__yeead = 0
    egcb__sgamm = np.empty(hpkyx__vuzv + 1, np_offset_type)
    gbb__vuk = []
    tyci__fchuz = np.empty(hpkyx__vuzv + 7 >> 3, np.uint8)
    for i, s in enumerate(pyval):
        egcb__sgamm[i] = ovcxg__yeead
        yvdz__gihgu = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(tyci__fchuz, i, int(not
            yvdz__gihgu))
        if yvdz__gihgu:
            continue
        fbf__aebzx = list(s.encode()) if isinstance(s, str) else list(s)
        gbb__vuk.extend(fbf__aebzx)
        ovcxg__yeead += len(fbf__aebzx)
    egcb__sgamm[hpkyx__vuzv] = ovcxg__yeead
    yxpn__auqsz = np.array(gbb__vuk, np.uint8)
    hqvru__kvsdv = context.get_constant(types.int64, hpkyx__vuzv)
    hqzb__yjvrp = context.get_constant_generic(builder, char_arr_type,
        yxpn__auqsz)
    heyia__mxjns = context.get_constant_generic(builder, offset_arr_type,
        egcb__sgamm)
    pcvza__ehz = context.get_constant_generic(builder, null_bitmap_arr_type,
        tyci__fchuz)
    ygx__twt = lir.Constant.literal_struct([hqvru__kvsdv, hqzb__yjvrp,
        heyia__mxjns, pcvza__ehz])
    ygx__twt = cgutils.global_constant(builder, '.const.payload', ygx__twt
        ).bitcast(cgutils.voidptr_t)
    pjz__ocrc = context.get_constant(types.int64, -1)
    oxtcs__lxykd = context.get_constant_null(types.voidptr)
    teyoe__keokp = lir.Constant.literal_struct([pjz__ocrc, oxtcs__lxykd,
        oxtcs__lxykd, ygx__twt, pjz__ocrc])
    teyoe__keokp = cgutils.global_constant(builder, '.const.meminfo',
        teyoe__keokp).bitcast(cgutils.voidptr_t)
    xxd__qqpvf = lir.Constant.literal_struct([teyoe__keokp])
    pgbsn__gik = lir.Constant.literal_struct([xxd__qqpvf])
    return pgbsn__gik


def pre_alloc_str_arr_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


from numba.parfors.array_analysis import ArrayAnalysis
(ArrayAnalysis._analyze_op_call_bodo_libs_str_arr_ext_pre_alloc_string_array
    ) = pre_alloc_str_arr_equiv


@overload(glob.glob, no_unliteral=True)
def overload_glob_glob(pathname, recursive=False):

    def _glob_glob_impl(pathname, recursive=False):
        with numba.objmode(l='list_str_type'):
            l = glob.glob(pathname, recursive=recursive)
        return l
    return _glob_glob_impl
