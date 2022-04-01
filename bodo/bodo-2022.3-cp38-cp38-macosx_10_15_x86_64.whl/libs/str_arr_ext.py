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
        wcs__rqnq = ArrayItemArrayType(char_arr_type)
        bimw__pqc = [('data', wcs__rqnq)]
        models.StructModel.__init__(self, dmm, fe_type, bimw__pqc)


make_attribute_wrapper(StringArrayType, 'data', '_data')
make_attribute_wrapper(BinaryArrayType, 'data', '_data')
lower_builtin('getiter', string_array_type)(numba.np.arrayobj.getiter_array)


@intrinsic
def init_str_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, ArrayItemArrayType
        ) and data_typ.dtype == types.Array(char_type, 1, 'C')

    def codegen(context, builder, sig, args):
        vnun__uxj, = args
        ipee__sodrz = context.make_helper(builder, string_array_type)
        ipee__sodrz.data = vnun__uxj
        context.nrt.incref(builder, data_typ, vnun__uxj)
        return ipee__sodrz._getvalue()
    return string_array_type(data_typ), codegen


class StringDtype(types.Number):

    def __init__(self):
        super(StringDtype, self).__init__('StringDtype')


string_dtype = StringDtype()
register_model(StringDtype)(models.OpaqueModel)


@box(StringDtype)
def box_string_dtype(typ, val, c):
    yjc__bkhk = c.context.insert_const_string(c.builder.module, 'pandas')
    odpv__awe = c.pyapi.import_module_noblock(yjc__bkhk)
    drxtg__qrc = c.pyapi.call_method(odpv__awe, 'StringDtype', ())
    c.pyapi.decref(odpv__awe)
    return drxtg__qrc


@unbox(StringDtype)
def unbox_string_dtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


typeof_impl.register(pd.StringDtype)(lambda a, b: string_dtype)
type_callable(pd.StringDtype)(lambda c: lambda : string_dtype)
lower_builtin(pd.StringDtype)(lambda c, b, s, a: c.get_dummy_value())


def create_binary_op_overload(op):

    def overload_string_array_binary_op(lhs, rhs):
        inzao__wsvoo = bodo.libs.dict_arr_ext.get_binary_op_overload(op,
            lhs, rhs)
        if inzao__wsvoo is not None:
            return inzao__wsvoo
        if is_str_arr_type(lhs) and is_str_arr_type(rhs):

            def impl_both(lhs, rhs):
                numba.parfors.parfor.init_prange()
                eztjm__lvuv = len(lhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(eztjm__lvuv)
                for i in numba.parfors.parfor.internal_prange(eztjm__lvuv):
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
                eztjm__lvuv = len(lhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(eztjm__lvuv)
                for i in numba.parfors.parfor.internal_prange(eztjm__lvuv):
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
                eztjm__lvuv = len(rhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(eztjm__lvuv)
                for i in numba.parfors.parfor.internal_prange(eztjm__lvuv):
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
    ryjo__dkit = is_str_arr_type(lhs) or isinstance(lhs, types.Array
        ) and lhs.dtype == string_type
    nqtce__nrc = is_str_arr_type(rhs) or isinstance(rhs, types.Array
        ) and rhs.dtype == string_type
    if is_str_arr_type(lhs) and nqtce__nrc or ryjo__dkit and is_str_arr_type(
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
    rnx__izvzv = context.make_helper(builder, arr_typ, arr_value)
    wcs__rqnq = ArrayItemArrayType(char_arr_type)
    pjiq__nurzh = _get_array_item_arr_payload(context, builder, wcs__rqnq,
        rnx__izvzv.data)
    return pjiq__nurzh


@intrinsic
def num_strings(typingctx, str_arr_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        return pjiq__nurzh.n_arrays
    return types.int64(string_array_type), codegen


def _get_num_total_chars(builder, offsets, num_strings):
    return builder.zext(builder.load(builder.gep(offsets, [num_strings])),
        lir.IntType(64))


@intrinsic
def num_total_chars(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        jszt__zrup = context.make_helper(builder, offset_arr_type,
            pjiq__nurzh.offsets).data
        return _get_num_total_chars(builder, jszt__zrup, pjiq__nurzh.n_arrays)
    return types.uint64(in_arr_typ), codegen


@intrinsic
def get_offset_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        ybtvf__fpon = context.make_helper(builder, offset_arr_type,
            pjiq__nurzh.offsets)
        jrek__fbl = context.make_helper(builder, offset_ctypes_type)
        jrek__fbl.data = builder.bitcast(ybtvf__fpon.data, lir.IntType(
            offset_type.bitwidth).as_pointer())
        jrek__fbl.meminfo = ybtvf__fpon.meminfo
        drxtg__qrc = jrek__fbl._getvalue()
        return impl_ret_borrowed(context, builder, offset_ctypes_type,
            drxtg__qrc)
    return offset_ctypes_type(in_arr_typ), codegen


@intrinsic
def get_data_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        vnun__uxj = context.make_helper(builder, char_arr_type, pjiq__nurzh
            .data)
        jrek__fbl = context.make_helper(builder, data_ctypes_type)
        jrek__fbl.data = vnun__uxj.data
        jrek__fbl.meminfo = vnun__uxj.meminfo
        drxtg__qrc = jrek__fbl._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type, drxtg__qrc
            )
    return data_ctypes_type(in_arr_typ), codegen


@intrinsic
def get_data_ptr_ind(typingctx, in_arr_typ, int_t=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        hyq__tjlo, ind = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            hyq__tjlo, sig.args[0])
        vnun__uxj = context.make_helper(builder, char_arr_type, pjiq__nurzh
            .data)
        jrek__fbl = context.make_helper(builder, data_ctypes_type)
        jrek__fbl.data = builder.gep(vnun__uxj.data, [ind])
        jrek__fbl.meminfo = vnun__uxj.meminfo
        drxtg__qrc = jrek__fbl._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type, drxtg__qrc
            )
    return data_ctypes_type(in_arr_typ, types.intp), codegen


@intrinsic
def copy_single_char(typingctx, dst_ptr_t, dst_ind_t, src_ptr_t, src_ind_t=None
    ):

    def codegen(context, builder, sig, args):
        ouqw__yzxhi, sdwbz__hpk, kwgly__fdd, rdocx__qcecj = args
        eje__tzil = builder.bitcast(builder.gep(ouqw__yzxhi, [sdwbz__hpk]),
            lir.IntType(8).as_pointer())
        wjf__htszo = builder.bitcast(builder.gep(kwgly__fdd, [rdocx__qcecj]
            ), lir.IntType(8).as_pointer())
        aikmi__minv = builder.load(wjf__htszo)
        builder.store(aikmi__minv, eje__tzil)
        return context.get_dummy_value()
    return types.void(types.voidptr, types.intp, types.voidptr, types.intp
        ), codegen


@intrinsic
def get_null_bitmap_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        guh__mkrjr = context.make_helper(builder, null_bitmap_arr_type,
            pjiq__nurzh.null_bitmap)
        jrek__fbl = context.make_helper(builder, data_ctypes_type)
        jrek__fbl.data = guh__mkrjr.data
        jrek__fbl.meminfo = guh__mkrjr.meminfo
        drxtg__qrc = jrek__fbl._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type, drxtg__qrc
            )
    return data_ctypes_type(in_arr_typ), codegen


@intrinsic
def getitem_str_offset(typingctx, in_arr_typ, ind_t=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        jszt__zrup = context.make_helper(builder, offset_arr_type,
            pjiq__nurzh.offsets).data
        return builder.load(builder.gep(jszt__zrup, [ind]))
    return offset_type(in_arr_typ, ind_t), codegen


@intrinsic
def setitem_str_offset(typingctx, str_arr_typ, ind_t, val_t=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind, val = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        offsets = context.make_helper(builder, offset_arr_type, pjiq__nurzh
            .offsets).data
        builder.store(val, builder.gep(offsets, [ind]))
        return context.get_dummy_value()
    return types.void(string_array_type, ind_t, offset_type), codegen


@intrinsic
def getitem_str_bitmap(typingctx, in_bitmap_typ, ind_t=None):

    def codegen(context, builder, sig, args):
        xexsa__hsjx, ind = args
        if in_bitmap_typ == data_ctypes_type:
            jrek__fbl = context.make_helper(builder, data_ctypes_type,
                xexsa__hsjx)
            xexsa__hsjx = jrek__fbl.data
        return builder.load(builder.gep(xexsa__hsjx, [ind]))
    return char_type(in_bitmap_typ, ind_t), codegen


@intrinsic
def setitem_str_bitmap(typingctx, in_bitmap_typ, ind_t, val_t=None):

    def codegen(context, builder, sig, args):
        xexsa__hsjx, ind, val = args
        if in_bitmap_typ == data_ctypes_type:
            jrek__fbl = context.make_helper(builder, data_ctypes_type,
                xexsa__hsjx)
            xexsa__hsjx = jrek__fbl.data
        builder.store(val, builder.gep(xexsa__hsjx, [ind]))
        return context.get_dummy_value()
    return types.void(in_bitmap_typ, ind_t, char_type), codegen


@intrinsic
def copy_str_arr_slice(typingctx, out_str_arr_typ, in_str_arr_typ, ind_t=None):
    assert out_str_arr_typ == string_array_type and in_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr, ind = args
        ffmg__kfyu = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        ocv__cqt = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        dai__giksm = context.make_helper(builder, offset_arr_type,
            ffmg__kfyu.offsets).data
        bbi__lifni = context.make_helper(builder, offset_arr_type, ocv__cqt
            .offsets).data
        yexw__txgjx = context.make_helper(builder, char_arr_type,
            ffmg__kfyu.data).data
        xxo__bxhm = context.make_helper(builder, char_arr_type, ocv__cqt.data
            ).data
        afl__bxtux = context.make_helper(builder, null_bitmap_arr_type,
            ffmg__kfyu.null_bitmap).data
        mkrw__vlrmm = context.make_helper(builder, null_bitmap_arr_type,
            ocv__cqt.null_bitmap).data
        ovds__qsfms = builder.add(ind, context.get_constant(types.intp, 1))
        cgutils.memcpy(builder, bbi__lifni, dai__giksm, ovds__qsfms)
        cgutils.memcpy(builder, xxo__bxhm, yexw__txgjx, builder.load(
            builder.gep(dai__giksm, [ind])))
        svag__skjzf = builder.add(ind, lir.Constant(lir.IntType(64), 7))
        jvdrh__pfo = builder.lshr(svag__skjzf, lir.Constant(lir.IntType(64), 3)
            )
        cgutils.memcpy(builder, mkrw__vlrmm, afl__bxtux, jvdrh__pfo)
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type, ind_t), codegen


@intrinsic
def copy_data(typingctx, str_arr_typ, out_str_arr_typ=None):
    assert str_arr_typ == string_array_type and out_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr = args
        ffmg__kfyu = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        ocv__cqt = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        dai__giksm = context.make_helper(builder, offset_arr_type,
            ffmg__kfyu.offsets).data
        yexw__txgjx = context.make_helper(builder, char_arr_type,
            ffmg__kfyu.data).data
        xxo__bxhm = context.make_helper(builder, char_arr_type, ocv__cqt.data
            ).data
        num_total_chars = _get_num_total_chars(builder, dai__giksm,
            ffmg__kfyu.n_arrays)
        cgutils.memcpy(builder, xxo__bxhm, yexw__txgjx, num_total_chars)
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type), codegen


@intrinsic
def copy_non_null_offsets(typingctx, str_arr_typ, out_str_arr_typ=None):
    assert str_arr_typ == string_array_type and out_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr = args
        ffmg__kfyu = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        ocv__cqt = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        dai__giksm = context.make_helper(builder, offset_arr_type,
            ffmg__kfyu.offsets).data
        bbi__lifni = context.make_helper(builder, offset_arr_type, ocv__cqt
            .offsets).data
        afl__bxtux = context.make_helper(builder, null_bitmap_arr_type,
            ffmg__kfyu.null_bitmap).data
        eztjm__lvuv = ffmg__kfyu.n_arrays
        irfyo__loxsr = context.get_constant(offset_type, 0)
        zyr__bjiqo = cgutils.alloca_once_value(builder, irfyo__loxsr)
        with cgutils.for_range(builder, eztjm__lvuv) as zkuz__tapv:
            txz__downa = lower_is_na(context, builder, afl__bxtux,
                zkuz__tapv.index)
            with cgutils.if_likely(builder, builder.not_(txz__downa)):
                wlc__lll = builder.load(builder.gep(dai__giksm, [zkuz__tapv
                    .index]))
                paye__xee = builder.load(zyr__bjiqo)
                builder.store(wlc__lll, builder.gep(bbi__lifni, [paye__xee]))
                builder.store(builder.add(paye__xee, lir.Constant(context.
                    get_value_type(offset_type), 1)), zyr__bjiqo)
        paye__xee = builder.load(zyr__bjiqo)
        wlc__lll = builder.load(builder.gep(dai__giksm, [eztjm__lvuv]))
        builder.store(wlc__lll, builder.gep(bbi__lifni, [paye__xee]))
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type), codegen


@intrinsic
def str_copy(typingctx, buff_arr_typ, ind_typ, str_typ, len_typ=None):

    def codegen(context, builder, sig, args):
        hriny__tyt, ind, str, xfey__risi = args
        hriny__tyt = context.make_array(sig.args[0])(context, builder,
            hriny__tyt)
        nvk__tgas = builder.gep(hriny__tyt.data, [ind])
        cgutils.raw_memcpy(builder, nvk__tgas, str, xfey__risi, 1)
        return context.get_dummy_value()
    return types.void(null_bitmap_arr_type, types.intp, types.voidptr,
        types.intp), codegen


@intrinsic
def str_copy_ptr(typingctx, ptr_typ, ind_typ, str_typ, len_typ=None):

    def codegen(context, builder, sig, args):
        nvk__tgas, ind, cghxe__vlpj, xfey__risi = args
        nvk__tgas = builder.gep(nvk__tgas, [ind])
        cgutils.raw_memcpy(builder, nvk__tgas, cghxe__vlpj, xfey__risi, 1)
        return context.get_dummy_value()
    return types.void(types.voidptr, types.intp, types.voidptr, types.intp
        ), codegen


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_length(A, i):
    return np.int64(getitem_str_offset(A, i + 1) - getitem_str_offset(A, i))


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_str_length(A, i):
    rmty__bgb = np.int64(getitem_str_offset(A, i))
    ohvyj__ubp = np.int64(getitem_str_offset(A, i + 1))
    l = ohvyj__ubp - rmty__bgb
    exsb__bqwa = get_data_ptr_ind(A, rmty__bgb)
    for j in range(l):
        if bodo.hiframes.split_impl.getitem_c_arr(exsb__bqwa, j) >= 128:
            return len(A[i])
    return l


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_ptr(A, i):
    return get_data_ptr_ind(A, getitem_str_offset(A, i))


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_copy(B, j, A, i):
    if j == 0:
        setitem_str_offset(B, 0, 0)
    uea__yezi = getitem_str_offset(A, i)
    vfpl__kcs = getitem_str_offset(A, i + 1)
    giph__pcd = vfpl__kcs - uea__yezi
    aqz__uyd = getitem_str_offset(B, j)
    qws__aevk = aqz__uyd + giph__pcd
    setitem_str_offset(B, j + 1, qws__aevk)
    if str_arr_is_na(A, i):
        str_arr_set_na(B, j)
    else:
        str_arr_set_not_na(B, j)
    if giph__pcd != 0:
        vnun__uxj = B._data
        bodo.libs.array_item_arr_ext.ensure_data_capacity(vnun__uxj, np.
            int64(aqz__uyd), np.int64(qws__aevk))
        bgurn__petn = get_data_ptr(B).data
        nzyp__nlg = get_data_ptr(A).data
        memcpy_region(bgurn__petn, aqz__uyd, nzyp__nlg, uea__yezi, giph__pcd, 1
            )


@numba.njit(no_cpython_wrapper=True)
def get_str_null_bools(str_arr):
    eztjm__lvuv = len(str_arr)
    eht__xeu = np.empty(eztjm__lvuv, np.bool_)
    for i in range(eztjm__lvuv):
        eht__xeu[i] = bodo.libs.array_kernels.isna(str_arr, i)
    return eht__xeu


def to_list_if_immutable_arr(arr, str_null_bools=None):
    return arr


@overload(to_list_if_immutable_arr, no_unliteral=True)
def to_list_if_immutable_arr_overload(data, str_null_bools=None):
    if is_str_arr_type(data) or data == binary_array_type:

        def to_list_impl(data, str_null_bools=None):
            eztjm__lvuv = len(data)
            l = []
            for i in range(eztjm__lvuv):
                l.append(data[i])
            return l
        return to_list_impl
    if isinstance(data, types.BaseTuple):
        sjti__mdtf = data.count
        obrws__ulhig = ['to_list_if_immutable_arr(data[{}])'.format(i) for
            i in range(sjti__mdtf)]
        if is_overload_true(str_null_bools):
            obrws__ulhig += ['get_str_null_bools(data[{}])'.format(i) for i in
                range(sjti__mdtf) if is_str_arr_type(data.types[i]) or data
                .types[i] == binary_array_type]
        lrv__klt = 'def f(data, str_null_bools=None):\n'
        lrv__klt += '  return ({}{})\n'.format(', '.join(obrws__ulhig), ',' if
            sjti__mdtf == 1 else '')
        ctlvv__gfa = {}
        exec(lrv__klt, {'to_list_if_immutable_arr':
            to_list_if_immutable_arr, 'get_str_null_bools':
            get_str_null_bools, 'bodo': bodo}, ctlvv__gfa)
        sti__bfxgj = ctlvv__gfa['f']
        return sti__bfxgj
    return lambda data, str_null_bools=None: data


def cp_str_list_to_array(str_arr, str_list, str_null_bools=None):
    return


@overload(cp_str_list_to_array, no_unliteral=True)
def cp_str_list_to_array_overload(str_arr, list_data, str_null_bools=None):
    if str_arr == string_array_type:
        if is_overload_none(str_null_bools):

            def cp_str_list_impl(str_arr, list_data, str_null_bools=None):
                eztjm__lvuv = len(list_data)
                for i in range(eztjm__lvuv):
                    cghxe__vlpj = list_data[i]
                    str_arr[i] = cghxe__vlpj
            return cp_str_list_impl
        else:

            def cp_str_list_impl_null(str_arr, list_data, str_null_bools=None):
                eztjm__lvuv = len(list_data)
                for i in range(eztjm__lvuv):
                    cghxe__vlpj = list_data[i]
                    str_arr[i] = cghxe__vlpj
                    if str_null_bools[i]:
                        str_arr_set_na(str_arr, i)
                    else:
                        str_arr_set_not_na(str_arr, i)
            return cp_str_list_impl_null
    if isinstance(str_arr, types.BaseTuple):
        sjti__mdtf = str_arr.count
        tdb__vlf = 0
        lrv__klt = 'def f(str_arr, list_data, str_null_bools=None):\n'
        for i in range(sjti__mdtf):
            if is_overload_true(str_null_bools) and str_arr.types[i
                ] == string_array_type:
                lrv__klt += (
                    '  cp_str_list_to_array(str_arr[{}], list_data[{}], list_data[{}])\n'
                    .format(i, i, sjti__mdtf + tdb__vlf))
                tdb__vlf += 1
            else:
                lrv__klt += (
                    '  cp_str_list_to_array(str_arr[{}], list_data[{}])\n'.
                    format(i, i))
        lrv__klt += '  return\n'
        ctlvv__gfa = {}
        exec(lrv__klt, {'cp_str_list_to_array': cp_str_list_to_array},
            ctlvv__gfa)
        cvqf__knifu = ctlvv__gfa['f']
        return cvqf__knifu
    return lambda str_arr, list_data, str_null_bools=None: None


def str_list_to_array(str_list):
    return str_list


@overload(str_list_to_array, no_unliteral=True)
def str_list_to_array_overload(str_list):
    if isinstance(str_list, types.List) and str_list.dtype == bodo.string_type:

        def str_list_impl(str_list):
            eztjm__lvuv = len(str_list)
            str_arr = pre_alloc_string_array(eztjm__lvuv, -1)
            for i in range(eztjm__lvuv):
                cghxe__vlpj = str_list[i]
                str_arr[i] = cghxe__vlpj
            return str_arr
        return str_list_impl
    return lambda str_list: str_list


def get_num_total_chars(A):
    pass


@overload(get_num_total_chars)
def overload_get_num_total_chars(A):
    if isinstance(A, types.List) and A.dtype == string_type:

        def str_list_impl(A):
            eztjm__lvuv = len(A)
            gtcs__oqrbz = 0
            for i in range(eztjm__lvuv):
                cghxe__vlpj = A[i]
                gtcs__oqrbz += get_utf8_size(cghxe__vlpj)
            return gtcs__oqrbz
        return str_list_impl
    assert A == string_array_type
    return lambda A: num_total_chars(A)


@overload_method(StringArrayType, 'copy', no_unliteral=True)
def str_arr_copy_overload(arr):

    def copy_impl(arr):
        eztjm__lvuv = len(arr)
        n_chars = num_total_chars(arr)
        pqb__dmi = pre_alloc_string_array(eztjm__lvuv, np.int64(n_chars))
        copy_str_arr_slice(pqb__dmi, arr, eztjm__lvuv)
        return pqb__dmi
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
    lrv__klt = 'def f(in_seq):\n'
    lrv__klt += '    n_strs = len(in_seq)\n'
    lrv__klt += '    A = pre_alloc_string_array(n_strs, -1)\n'
    lrv__klt += '    return A\n'
    ctlvv__gfa = {}
    exec(lrv__klt, {'pre_alloc_string_array': pre_alloc_string_array},
        ctlvv__gfa)
    dlybf__qcca = ctlvv__gfa['f']
    return dlybf__qcca


@numba.generated_jit(nopython=True)
def str_arr_from_sequence(in_seq):
    if in_seq.dtype == bodo.bytes_type:
        zshd__gei = 'pre_alloc_binary_array'
    else:
        zshd__gei = 'pre_alloc_string_array'
    lrv__klt = 'def f(in_seq):\n'
    lrv__klt += '    n_strs = len(in_seq)\n'
    lrv__klt += f'    A = {zshd__gei}(n_strs, -1)\n'
    lrv__klt += '    for i in range(n_strs):\n'
    lrv__klt += '        A[i] = in_seq[i]\n'
    lrv__klt += '    return A\n'
    ctlvv__gfa = {}
    exec(lrv__klt, {'pre_alloc_string_array': pre_alloc_string_array,
        'pre_alloc_binary_array': pre_alloc_binary_array}, ctlvv__gfa)
    dlybf__qcca = ctlvv__gfa['f']
    return dlybf__qcca


@intrinsic
def set_all_offsets_to_0(typingctx, arr_typ=None):
    assert arr_typ in (string_array_type, binary_array_type
        ), 'set_all_offsets_to_0 requires a string or binary array'

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        dgdfo__mcm = builder.add(pjiq__nurzh.n_arrays, lir.Constant(lir.
            IntType(64), 1))
        vtunw__pbrrq = builder.lshr(lir.Constant(lir.IntType(64),
            offset_type.bitwidth), lir.Constant(lir.IntType(64), 3))
        jvdrh__pfo = builder.mul(dgdfo__mcm, vtunw__pbrrq)
        hos__eyz = context.make_array(offset_arr_type)(context, builder,
            pjiq__nurzh.offsets).data
        cgutils.memset(builder, hos__eyz, jvdrh__pfo, 0)
        return context.get_dummy_value()
    return types.none(arr_typ), codegen


@intrinsic
def set_bitmap_all_NA(typingctx, arr_typ=None):
    assert arr_typ in (string_array_type, binary_array_type
        ), 'set_bitmap_all_NA requires a string or binary array'

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        hncp__hgwhf = pjiq__nurzh.n_arrays
        jvdrh__pfo = builder.lshr(builder.add(hncp__hgwhf, lir.Constant(lir
            .IntType(64), 7)), lir.Constant(lir.IntType(64), 3))
        vcuiu__qxr = context.make_array(null_bitmap_arr_type)(context,
            builder, pjiq__nurzh.null_bitmap).data
        cgutils.memset(builder, vcuiu__qxr, jvdrh__pfo, 0)
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
    ktn__oij = 0
    if total_len == 0:
        for i in range(len(offsets)):
            offsets[i] = 0
    else:
        grt__zdri = len(len_arr)
        for i in range(grt__zdri):
            offsets[i] = ktn__oij
            ktn__oij += len_arr[i]
        offsets[grt__zdri] = ktn__oij
    return str_arr


kBitmask = np.array([1, 2, 4, 8, 16, 32, 64, 128], dtype=np.uint8)


@numba.njit
def set_bit_to(bits, i, bit_is_set):
    srf__cxe = i // 8
    inlhm__uhwm = getitem_str_bitmap(bits, srf__cxe)
    inlhm__uhwm ^= np.uint8(-np.uint8(bit_is_set) ^ inlhm__uhwm) & kBitmask[
        i % 8]
    setitem_str_bitmap(bits, srf__cxe, inlhm__uhwm)


@numba.njit
def get_bit_bitmap(bits, i):
    return getitem_str_bitmap(bits, i >> 3) >> (i & 7) & 1


@numba.njit
def copy_nulls_range(out_str_arr, in_str_arr, out_start):
    tddx__kqt = get_null_bitmap_ptr(out_str_arr)
    nushc__fisr = get_null_bitmap_ptr(in_str_arr)
    for j in range(len(in_str_arr)):
        ntj__uyw = get_bit_bitmap(nushc__fisr, j)
        set_bit_to(tddx__kqt, out_start + j, ntj__uyw)


@intrinsic
def set_string_array_range(typingctx, out_typ, in_typ, curr_str_typ,
    curr_chars_typ=None):
    assert out_typ == string_array_type and in_typ == string_array_type or out_typ == binary_array_type and in_typ == binary_array_type, 'set_string_array_range requires string or binary arrays'
    assert isinstance(curr_str_typ, types.Integer) and isinstance(
        curr_chars_typ, types.Integer
        ), 'set_string_array_range requires integer indices'

    def codegen(context, builder, sig, args):
        out_arr, hyq__tjlo, yqevg__rnp, xojgu__gbq = args
        ffmg__kfyu = _get_str_binary_arr_payload(context, builder,
            hyq__tjlo, string_array_type)
        ocv__cqt = _get_str_binary_arr_payload(context, builder, out_arr,
            string_array_type)
        dai__giksm = context.make_helper(builder, offset_arr_type,
            ffmg__kfyu.offsets).data
        bbi__lifni = context.make_helper(builder, offset_arr_type, ocv__cqt
            .offsets).data
        yexw__txgjx = context.make_helper(builder, char_arr_type,
            ffmg__kfyu.data).data
        xxo__bxhm = context.make_helper(builder, char_arr_type, ocv__cqt.data
            ).data
        num_total_chars = _get_num_total_chars(builder, dai__giksm,
            ffmg__kfyu.n_arrays)
        fwoln__jytq = lir.FunctionType(lir.VoidType(), [lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(64), lir.IntType(64), lir.IntType(64),
            lir.IntType(64)])
        tmwy__tatdf = cgutils.get_or_insert_function(builder.module,
            fwoln__jytq, name='set_string_array_range')
        builder.call(tmwy__tatdf, [bbi__lifni, xxo__bxhm, dai__giksm,
            yexw__txgjx, yqevg__rnp, xojgu__gbq, ffmg__kfyu.n_arrays,
            num_total_chars])
        vonn__istl = context.typing_context.resolve_value_type(copy_nulls_range
            )
        lidii__wfv = vonn__istl.get_call_type(context.typing_context, (
            string_array_type, string_array_type, types.int64), {})
        rqox__jvx = context.get_function(vonn__istl, lidii__wfv)
        rqox__jvx(builder, (out_arr, hyq__tjlo, yqevg__rnp))
        return context.get_dummy_value()
    sig = types.void(out_typ, in_typ, types.intp, types.intp)
    return sig, codegen


@box(BinaryArrayType)
@box(StringArrayType)
def box_str_arr(typ, val, c):
    assert typ in [binary_array_type, string_array_type]
    snuk__oijbf = c.context.make_helper(c.builder, typ, val)
    wcs__rqnq = ArrayItemArrayType(char_arr_type)
    pjiq__nurzh = _get_array_item_arr_payload(c.context, c.builder,
        wcs__rqnq, snuk__oijbf.data)
    dypy__gsah = c.context.get_constant(types.int32, int(typ ==
        binary_array_type))
    cja__ock = 'np_array_from_string_array'
    if use_pd_string_array and typ != binary_array_type:
        cja__ock = 'pd_array_from_string_array'
    fwoln__jytq = lir.FunctionType(c.context.get_argument_type(types.
        pyobject), [lir.IntType(64), lir.IntType(offset_type.bitwidth).
        as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
        as_pointer(), lir.IntType(32)])
    qvjry__fcgt = cgutils.get_or_insert_function(c.builder.module,
        fwoln__jytq, name=cja__ock)
    jszt__zrup = c.context.make_array(offset_arr_type)(c.context, c.builder,
        pjiq__nurzh.offsets).data
    exsb__bqwa = c.context.make_array(char_arr_type)(c.context, c.builder,
        pjiq__nurzh.data).data
    vcuiu__qxr = c.context.make_array(null_bitmap_arr_type)(c.context, c.
        builder, pjiq__nurzh.null_bitmap).data
    arr = c.builder.call(qvjry__fcgt, [pjiq__nurzh.n_arrays, jszt__zrup,
        exsb__bqwa, vcuiu__qxr, dypy__gsah])
    c.context.nrt.decref(c.builder, typ, val)
    return arr


@intrinsic
def str_arr_is_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        vcuiu__qxr = context.make_array(null_bitmap_arr_type)(context,
            builder, pjiq__nurzh.null_bitmap).data
        kbx__ypvi = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        alo__djbl = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        inlhm__uhwm = builder.load(builder.gep(vcuiu__qxr, [kbx__ypvi],
            inbounds=True))
        fztyd__irm = lir.ArrayType(lir.IntType(8), 8)
        wwil__yeau = cgutils.alloca_once_value(builder, lir.Constant(
            fztyd__irm, (1, 2, 4, 8, 16, 32, 64, 128)))
        okaot__alxgz = builder.load(builder.gep(wwil__yeau, [lir.Constant(
            lir.IntType(64), 0), alo__djbl], inbounds=True))
        return builder.icmp_unsigned('==', builder.and_(inlhm__uhwm,
            okaot__alxgz), lir.Constant(lir.IntType(8), 0))
    return types.bool_(str_arr_typ, types.intp), codegen


@intrinsic
def str_arr_set_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        kbx__ypvi = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        alo__djbl = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        vcuiu__qxr = context.make_array(null_bitmap_arr_type)(context,
            builder, pjiq__nurzh.null_bitmap).data
        offsets = context.make_helper(builder, offset_arr_type, pjiq__nurzh
            .offsets).data
        vbogc__voy = builder.gep(vcuiu__qxr, [kbx__ypvi], inbounds=True)
        inlhm__uhwm = builder.load(vbogc__voy)
        fztyd__irm = lir.ArrayType(lir.IntType(8), 8)
        wwil__yeau = cgutils.alloca_once_value(builder, lir.Constant(
            fztyd__irm, (1, 2, 4, 8, 16, 32, 64, 128)))
        okaot__alxgz = builder.load(builder.gep(wwil__yeau, [lir.Constant(
            lir.IntType(64), 0), alo__djbl], inbounds=True))
        okaot__alxgz = builder.xor(okaot__alxgz, lir.Constant(lir.IntType(8
            ), -1))
        builder.store(builder.and_(inlhm__uhwm, okaot__alxgz), vbogc__voy)
        if str_arr_typ == string_array_type:
            eal__xeghn = builder.add(ind, lir.Constant(lir.IntType(64), 1))
            bhey__kom = builder.icmp_unsigned('!=', eal__xeghn, pjiq__nurzh
                .n_arrays)
            with builder.if_then(bhey__kom):
                builder.store(builder.load(builder.gep(offsets, [ind])),
                    builder.gep(offsets, [eal__xeghn]))
        return context.get_dummy_value()
    return types.void(str_arr_typ, types.intp), codegen


@intrinsic
def str_arr_set_not_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        kbx__ypvi = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        alo__djbl = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        vcuiu__qxr = context.make_array(null_bitmap_arr_type)(context,
            builder, pjiq__nurzh.null_bitmap).data
        vbogc__voy = builder.gep(vcuiu__qxr, [kbx__ypvi], inbounds=True)
        inlhm__uhwm = builder.load(vbogc__voy)
        fztyd__irm = lir.ArrayType(lir.IntType(8), 8)
        wwil__yeau = cgutils.alloca_once_value(builder, lir.Constant(
            fztyd__irm, (1, 2, 4, 8, 16, 32, 64, 128)))
        okaot__alxgz = builder.load(builder.gep(wwil__yeau, [lir.Constant(
            lir.IntType(64), 0), alo__djbl], inbounds=True))
        builder.store(builder.or_(inlhm__uhwm, okaot__alxgz), vbogc__voy)
        return context.get_dummy_value()
    return types.void(str_arr_typ, types.intp), codegen


@intrinsic
def set_null_bits_to_value(typingctx, arr_typ, value_typ=None):
    assert (arr_typ == string_array_type or arr_typ == binary_array_type
        ) and is_overload_constant_int(value_typ)

    def codegen(context, builder, sig, args):
        in_str_arr, value = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        jvdrh__pfo = builder.udiv(builder.add(pjiq__nurzh.n_arrays, lir.
            Constant(lir.IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
        vcuiu__qxr = context.make_array(null_bitmap_arr_type)(context,
            builder, pjiq__nurzh.null_bitmap).data
        cgutils.memset(builder, vcuiu__qxr, jvdrh__pfo, value)
        return context.get_dummy_value()
    return types.none(arr_typ, types.int8), codegen


def _get_str_binary_arr_data_payload_ptr(context, builder, str_arr):
    uxbu__ggro = context.make_helper(builder, string_array_type, str_arr)
    wcs__rqnq = ArrayItemArrayType(char_arr_type)
    bpjw__gqp = context.make_helper(builder, wcs__rqnq, uxbu__ggro.data)
    zcfj__ianz = ArrayItemArrayPayloadType(wcs__rqnq)
    cbis__kju = context.nrt.meminfo_data(builder, bpjw__gqp.meminfo)
    dco__ykfx = builder.bitcast(cbis__kju, context.get_value_type(
        zcfj__ianz).as_pointer())
    return dco__ykfx


@intrinsic
def move_str_binary_arr_payload(typingctx, to_arr_typ, from_arr_typ=None):
    assert to_arr_typ == string_array_type and from_arr_typ == string_array_type or to_arr_typ == binary_array_type and from_arr_typ == binary_array_type

    def codegen(context, builder, sig, args):
        ghim__yam, ijmi__rvyc = args
        lou__epcao = _get_str_binary_arr_data_payload_ptr(context, builder,
            ijmi__rvyc)
        ocq__dnjfo = _get_str_binary_arr_data_payload_ptr(context, builder,
            ghim__yam)
        tbv__xqnc = _get_str_binary_arr_payload(context, builder,
            ijmi__rvyc, sig.args[1])
        pnb__nilwc = _get_str_binary_arr_payload(context, builder,
            ghim__yam, sig.args[0])
        context.nrt.incref(builder, char_arr_type, tbv__xqnc.data)
        context.nrt.incref(builder, offset_arr_type, tbv__xqnc.offsets)
        context.nrt.incref(builder, null_bitmap_arr_type, tbv__xqnc.null_bitmap
            )
        context.nrt.decref(builder, char_arr_type, pnb__nilwc.data)
        context.nrt.decref(builder, offset_arr_type, pnb__nilwc.offsets)
        context.nrt.decref(builder, null_bitmap_arr_type, pnb__nilwc.
            null_bitmap)
        builder.store(builder.load(lou__epcao), ocq__dnjfo)
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
        eztjm__lvuv = _get_utf8_size(s._data, s._length, s._kind)
        dummy_use(s)
        return eztjm__lvuv
    return impl


@intrinsic
def setitem_str_arr_ptr(typingctx, str_arr_t, ind_t, ptr_t, len_t=None):

    def codegen(context, builder, sig, args):
        arr, ind, nvk__tgas, dho__utg = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder, arr,
            sig.args[0])
        offsets = context.make_helper(builder, offset_arr_type, pjiq__nurzh
            .offsets).data
        data = context.make_helper(builder, char_arr_type, pjiq__nurzh.data
            ).data
        fwoln__jytq = lir.FunctionType(lir.VoidType(), [lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(64),
            lir.IntType(32), lir.IntType(32), lir.IntType(64)])
        fapfa__lqmm = cgutils.get_or_insert_function(builder.module,
            fwoln__jytq, name='setitem_string_array')
        csyo__frjvz = context.get_constant(types.int32, -1)
        hnr__grodf = context.get_constant(types.int32, 1)
        num_total_chars = _get_num_total_chars(builder, offsets,
            pjiq__nurzh.n_arrays)
        builder.call(fapfa__lqmm, [offsets, data, num_total_chars, builder.
            extract_value(nvk__tgas, 0), dho__utg, csyo__frjvz, hnr__grodf,
            ind])
        return context.get_dummy_value()
    return types.void(str_arr_t, ind_t, ptr_t, len_t), codegen


def lower_is_na(context, builder, bull_bitmap, ind):
    fwoln__jytq = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
        as_pointer(), lir.IntType(64)])
    vtyq__utv = cgutils.get_or_insert_function(builder.module, fwoln__jytq,
        name='is_na')
    return builder.call(vtyq__utv, [bull_bitmap, ind])


@intrinsic
def _memcpy(typingctx, dest_t, src_t, count_t, item_size_t=None):

    def codegen(context, builder, sig, args):
        eje__tzil, wjf__htszo, sjti__mdtf, gblpm__uodlf = args
        cgutils.raw_memcpy(builder, eje__tzil, wjf__htszo, sjti__mdtf,
            gblpm__uodlf)
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
        tsau__oiqkr, xnekp__dfxqf = unicode_to_utf8_and_len(val)
        ynjfk__wcbl = getitem_str_offset(A, ind)
        xyjis__jvff = getitem_str_offset(A, ind + 1)
        hgsv__hzwx = xyjis__jvff - ynjfk__wcbl
        if hgsv__hzwx != xnekp__dfxqf:
            return False
        nvk__tgas = get_data_ptr_ind(A, ynjfk__wcbl)
        return memcmp(nvk__tgas, tsau__oiqkr, xnekp__dfxqf) == 0
    return impl


def str_arr_setitem_int_to_str(A, ind, value):
    A[ind] = str(value)


@overload(str_arr_setitem_int_to_str)
def overload_str_arr_setitem_int_to_str(A, ind, val):

    def impl(A, ind, val):
        ynjfk__wcbl = getitem_str_offset(A, ind)
        hgsv__hzwx = bodo.libs.str_ext.int_to_str_len(val)
        mhfy__cbel = ynjfk__wcbl + hgsv__hzwx
        bodo.libs.array_item_arr_ext.ensure_data_capacity(A._data,
            ynjfk__wcbl, mhfy__cbel)
        nvk__tgas = get_data_ptr_ind(A, ynjfk__wcbl)
        inplace_int64_to_str(nvk__tgas, hgsv__hzwx, val)
        setitem_str_offset(A, ind + 1, ynjfk__wcbl + hgsv__hzwx)
        str_arr_set_not_na(A, ind)
    return impl


@intrinsic
def inplace_set_NA_str(typingctx, ptr_typ=None):

    def codegen(context, builder, sig, args):
        nvk__tgas, = args
        cpe__woe = context.insert_const_string(builder.module, '<NA>')
        qzzhf__ovazi = lir.Constant(lir.IntType(64), len('<NA>'))
        cgutils.raw_memcpy(builder, nvk__tgas, cpe__woe, qzzhf__ovazi, 1)
    return types.none(types.voidptr), codegen


def str_arr_setitem_NA_str(A, ind):
    A[ind] = '<NA>'


@overload(str_arr_setitem_NA_str)
def overload_str_arr_setitem_NA_str(A, ind):
    tpoi__pbdyz = len('<NA>')

    def impl(A, ind):
        ynjfk__wcbl = getitem_str_offset(A, ind)
        mhfy__cbel = ynjfk__wcbl + tpoi__pbdyz
        bodo.libs.array_item_arr_ext.ensure_data_capacity(A._data,
            ynjfk__wcbl, mhfy__cbel)
        nvk__tgas = get_data_ptr_ind(A, ynjfk__wcbl)
        inplace_set_NA_str(nvk__tgas)
        setitem_str_offset(A, ind + 1, ynjfk__wcbl + tpoi__pbdyz)
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
            ynjfk__wcbl = getitem_str_offset(A, ind)
            xyjis__jvff = getitem_str_offset(A, ind + 1)
            dho__utg = xyjis__jvff - ynjfk__wcbl
            nvk__tgas = get_data_ptr_ind(A, ynjfk__wcbl)
            mnrm__lpm = decode_utf8(nvk__tgas, dho__utg)
            return mnrm__lpm
        return str_arr_getitem_impl
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:

        def bool_impl(A, ind):
            ind = bodo.utils.conversion.coerce_to_ndarray(ind)
            eztjm__lvuv = len(A)
            n_strs = 0
            n_chars = 0
            for i in range(eztjm__lvuv):
                if not bodo.libs.array_kernels.isna(ind, i) and ind[i]:
                    n_strs += 1
                    n_chars += get_str_arr_item_length(A, i)
            out_arr = pre_alloc_string_array(n_strs, n_chars)
            bgurn__petn = get_data_ptr(out_arr).data
            nzyp__nlg = get_data_ptr(A).data
            tdb__vlf = 0
            paye__xee = 0
            setitem_str_offset(out_arr, 0, 0)
            for i in range(eztjm__lvuv):
                if not bodo.libs.array_kernels.isna(ind, i) and ind[i]:
                    objyt__bspb = get_str_arr_item_length(A, i)
                    if objyt__bspb == 1:
                        copy_single_char(bgurn__petn, paye__xee, nzyp__nlg,
                            getitem_str_offset(A, i))
                    else:
                        memcpy_region(bgurn__petn, paye__xee, nzyp__nlg,
                            getitem_str_offset(A, i), objyt__bspb, 1)
                    paye__xee += objyt__bspb
                    setitem_str_offset(out_arr, tdb__vlf + 1, paye__xee)
                    if str_arr_is_na(A, i):
                        str_arr_set_na(out_arr, tdb__vlf)
                    else:
                        str_arr_set_not_na(out_arr, tdb__vlf)
                    tdb__vlf += 1
            return out_arr
        return bool_impl
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def str_arr_arr_impl(A, ind):
            eztjm__lvuv = len(ind)
            out_arr = pre_alloc_string_array(eztjm__lvuv, -1)
            tdb__vlf = 0
            for i in range(eztjm__lvuv):
                cghxe__vlpj = A[ind[i]]
                out_arr[tdb__vlf] = cghxe__vlpj
                if str_arr_is_na(A, ind[i]):
                    str_arr_set_na(out_arr, tdb__vlf)
                tdb__vlf += 1
            return out_arr
        return str_arr_arr_impl
    if isinstance(ind, types.SliceType):

        def str_arr_slice_impl(A, ind):
            eztjm__lvuv = len(A)
            jkmh__ncihv = numba.cpython.unicode._normalize_slice(ind,
                eztjm__lvuv)
            tljo__lykp = numba.cpython.unicode._slice_span(jkmh__ncihv)
            if jkmh__ncihv.step == 1:
                ynjfk__wcbl = getitem_str_offset(A, jkmh__ncihv.start)
                xyjis__jvff = getitem_str_offset(A, jkmh__ncihv.stop)
                n_chars = xyjis__jvff - ynjfk__wcbl
                pqb__dmi = pre_alloc_string_array(tljo__lykp, np.int64(n_chars)
                    )
                for i in range(tljo__lykp):
                    pqb__dmi[i] = A[jkmh__ncihv.start + i]
                    if str_arr_is_na(A, jkmh__ncihv.start + i):
                        str_arr_set_na(pqb__dmi, i)
                return pqb__dmi
            else:
                pqb__dmi = pre_alloc_string_array(tljo__lykp, -1)
                for i in range(tljo__lykp):
                    pqb__dmi[i] = A[jkmh__ncihv.start + i * jkmh__ncihv.step]
                    if str_arr_is_na(A, jkmh__ncihv.start + i * jkmh__ncihv
                        .step):
                        str_arr_set_na(pqb__dmi, i)
                return pqb__dmi
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
    dcq__jzk = (
        f'StringArray setitem with index {idx} and value {val} not supported yet.'
        )
    if isinstance(idx, types.Integer):
        if val != string_type:
            raise BodoError(dcq__jzk)
        kre__vlut = 4

        def impl_scalar(A, idx, val):
            jsv__vjcss = (val._length if val._is_ascii else kre__vlut * val
                ._length)
            vnun__uxj = A._data
            ynjfk__wcbl = np.int64(getitem_str_offset(A, idx))
            mhfy__cbel = ynjfk__wcbl + jsv__vjcss
            bodo.libs.array_item_arr_ext.ensure_data_capacity(vnun__uxj,
                ynjfk__wcbl, mhfy__cbel)
            setitem_string_array(get_offset_ptr(A), get_data_ptr(A),
                mhfy__cbel, val._data, val._length, val._kind, val.
                _is_ascii, idx)
            str_arr_set_not_na(A, idx)
            dummy_use(A)
            dummy_use(val)
        return impl_scalar
    if isinstance(idx, types.SliceType):
        if val == string_array_type:

            def impl_slice(A, idx, val):
                jkmh__ncihv = numba.cpython.unicode._normalize_slice(idx,
                    len(A))
                rmty__bgb = jkmh__ncihv.start
                vnun__uxj = A._data
                ynjfk__wcbl = np.int64(getitem_str_offset(A, rmty__bgb))
                mhfy__cbel = ynjfk__wcbl + np.int64(num_total_chars(val))
                bodo.libs.array_item_arr_ext.ensure_data_capacity(vnun__uxj,
                    ynjfk__wcbl, mhfy__cbel)
                set_string_array_range(A, val, rmty__bgb, ynjfk__wcbl)
                dke__dkl = 0
                for i in range(jkmh__ncihv.start, jkmh__ncihv.stop,
                    jkmh__ncihv.step):
                    if str_arr_is_na(val, dke__dkl):
                        str_arr_set_na(A, i)
                    else:
                        str_arr_set_not_na(A, i)
                    dke__dkl += 1
            return impl_slice
        elif isinstance(val, types.List) and val.dtype == string_type:

            def impl_slice_list(A, idx, val):
                vgr__rgwiv = str_list_to_array(val)
                A[idx] = vgr__rgwiv
            return impl_slice_list
        elif val == string_type:

            def impl_slice(A, idx, val):
                jkmh__ncihv = numba.cpython.unicode._normalize_slice(idx,
                    len(A))
                for i in range(jkmh__ncihv.start, jkmh__ncihv.stop,
                    jkmh__ncihv.step):
                    A[i] = val
            return impl_slice
        else:
            raise BodoError(dcq__jzk)
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        if val == string_type:

            def impl_bool_scalar(A, idx, val):
                eztjm__lvuv = len(A)
                idx = bodo.utils.conversion.coerce_to_ndarray(idx)
                out_arr = pre_alloc_string_array(eztjm__lvuv, -1)
                for i in numba.parfors.parfor.internal_prange(eztjm__lvuv):
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
                eztjm__lvuv = len(A)
                idx = bodo.utils.conversion.coerce_to_array(idx,
                    use_nullable_array=True)
                out_arr = pre_alloc_string_array(eztjm__lvuv, -1)
                xvd__ant = 0
                for i in numba.parfors.parfor.internal_prange(eztjm__lvuv):
                    if not bodo.libs.array_kernels.isna(idx, i) and idx[i]:
                        if bodo.libs.array_kernels.isna(val, xvd__ant):
                            out_arr[i] = ''
                            str_arr_set_na(out_arr, xvd__ant)
                        else:
                            out_arr[i] = str(val[xvd__ant])
                        xvd__ant += 1
                    elif bodo.libs.array_kernels.isna(A, i):
                        out_arr[i] = ''
                        str_arr_set_na(out_arr, i)
                    else:
                        get_str_arr_item_copy(out_arr, i, A, i)
                move_str_binary_arr_payload(A, out_arr)
            return impl_bool_arr
        else:
            raise BodoError(dcq__jzk)
    raise BodoError(dcq__jzk)


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
    vpjy__ptsk = parse_dtype(dtype, 'StringArray.astype')
    if not isinstance(vpjy__ptsk, (types.Float, types.Integer)):
        raise BodoError('invalid dtype in StringArray.astype()')
    if isinstance(vpjy__ptsk, types.Float):

        def impl_float(A, dtype, copy=True):
            numba.parfors.parfor.init_prange()
            eztjm__lvuv = len(A)
            B = np.empty(eztjm__lvuv, vpjy__ptsk)
            for i in numba.parfors.parfor.internal_prange(eztjm__lvuv):
                if bodo.libs.array_kernels.isna(A, i):
                    B[i] = np.nan
                else:
                    B[i] = float(A[i])
            return B
        return impl_float
    else:

        def impl_int(A, dtype, copy=True):
            numba.parfors.parfor.init_prange()
            eztjm__lvuv = len(A)
            B = np.empty(eztjm__lvuv, vpjy__ptsk)
            for i in numba.parfors.parfor.internal_prange(eztjm__lvuv):
                B[i] = int(A[i])
            return B
        return impl_int


@intrinsic
def decode_utf8(typingctx, ptr_t, len_t=None):

    def codegen(context, builder, sig, args):
        nvk__tgas, dho__utg = args
        jfrit__rcif = context.get_python_api(builder)
        gor__qorsv = jfrit__rcif.string_from_string_and_size(nvk__tgas,
            dho__utg)
        xoy__chs = jfrit__rcif.to_native_value(string_type, gor__qorsv).value
        jxind__ugkxw = cgutils.create_struct_proxy(string_type)(context,
            builder, xoy__chs)
        jxind__ugkxw.hash = jxind__ugkxw.hash.type(-1)
        jfrit__rcif.decref(gor__qorsv)
        return jxind__ugkxw._getvalue()
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
        keffs__fdexx, arr, ind, ulco__ydqk = args
        pjiq__nurzh = _get_str_binary_arr_payload(context, builder, arr,
            string_array_type)
        offsets = context.make_helper(builder, offset_arr_type, pjiq__nurzh
            .offsets).data
        data = context.make_helper(builder, char_arr_type, pjiq__nurzh.data
            ).data
        fwoln__jytq = lir.FunctionType(lir.IntType(32), [keffs__fdexx.type,
            lir.IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(64)])
        jvv__bwpz = 'str_arr_to_int64'
        if sig.args[3].dtype == types.float64:
            jvv__bwpz = 'str_arr_to_float64'
        else:
            assert sig.args[3].dtype == types.int64
        enzgk__vnngw = cgutils.get_or_insert_function(builder.module,
            fwoln__jytq, jvv__bwpz)
        return builder.call(enzgk__vnngw, [keffs__fdexx, offsets, data, ind])
    return types.int32(out_ptr_t, string_array_type, types.int64, out_dtype_t
        ), codegen


@unbox(BinaryArrayType)
@unbox(StringArrayType)
def unbox_str_series(typ, val, c):
    dypy__gsah = c.context.get_constant(types.int32, int(typ ==
        binary_array_type))
    fwoln__jytq = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
        IntType(8).as_pointer(), lir.IntType(32)])
    tmpg__txhw = cgutils.get_or_insert_function(c.builder.module,
        fwoln__jytq, name='string_array_from_sequence')
    grp__absn = c.builder.call(tmpg__txhw, [val, dypy__gsah])
    wcs__rqnq = ArrayItemArrayType(char_arr_type)
    bpjw__gqp = c.context.make_helper(c.builder, wcs__rqnq)
    bpjw__gqp.meminfo = grp__absn
    uxbu__ggro = c.context.make_helper(c.builder, typ)
    vnun__uxj = bpjw__gqp._getvalue()
    uxbu__ggro.data = vnun__uxj
    eivh__plgj = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(uxbu__ggro._getvalue(), is_error=eivh__plgj)


@lower_constant(BinaryArrayType)
@lower_constant(StringArrayType)
def lower_constant_str_arr(context, builder, typ, pyval):
    eztjm__lvuv = len(pyval)
    paye__xee = 0
    eyjcq__yns = np.empty(eztjm__lvuv + 1, np_offset_type)
    mrm__akzfp = []
    fity__rve = np.empty(eztjm__lvuv + 7 >> 3, np.uint8)
    for i, s in enumerate(pyval):
        eyjcq__yns[i] = paye__xee
        ovtts__bypg = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(fity__rve, i, int(not ovtts__bypg)
            )
        if ovtts__bypg:
            continue
        vqrnm__lmgj = list(s.encode()) if isinstance(s, str) else list(s)
        mrm__akzfp.extend(vqrnm__lmgj)
        paye__xee += len(vqrnm__lmgj)
    eyjcq__yns[eztjm__lvuv] = paye__xee
    eqg__bmmjc = np.array(mrm__akzfp, np.uint8)
    tdcvf__rly = context.get_constant(types.int64, eztjm__lvuv)
    wosuf__phtgh = context.get_constant_generic(builder, char_arr_type,
        eqg__bmmjc)
    knie__jkp = context.get_constant_generic(builder, offset_arr_type,
        eyjcq__yns)
    aklh__xbxfd = context.get_constant_generic(builder,
        null_bitmap_arr_type, fity__rve)
    pjiq__nurzh = lir.Constant.literal_struct([tdcvf__rly, wosuf__phtgh,
        knie__jkp, aklh__xbxfd])
    pjiq__nurzh = cgutils.global_constant(builder, '.const.payload',
        pjiq__nurzh).bitcast(cgutils.voidptr_t)
    hwld__cjzh = context.get_constant(types.int64, -1)
    aeyq__zyzxp = context.get_constant_null(types.voidptr)
    pzk__jhd = lir.Constant.literal_struct([hwld__cjzh, aeyq__zyzxp,
        aeyq__zyzxp, pjiq__nurzh, hwld__cjzh])
    pzk__jhd = cgutils.global_constant(builder, '.const.meminfo', pzk__jhd
        ).bitcast(cgutils.voidptr_t)
    vnun__uxj = lir.Constant.literal_struct([pzk__jhd])
    uxbu__ggro = lir.Constant.literal_struct([vnun__uxj])
    return uxbu__ggro


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
