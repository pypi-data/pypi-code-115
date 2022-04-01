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
        tbwpl__rzck = ArrayItemArrayType(char_arr_type)
        qns__ljkj = [('data', tbwpl__rzck)]
        models.StructModel.__init__(self, dmm, fe_type, qns__ljkj)


make_attribute_wrapper(StringArrayType, 'data', '_data')
make_attribute_wrapper(BinaryArrayType, 'data', '_data')
lower_builtin('getiter', string_array_type)(numba.np.arrayobj.getiter_array)


@intrinsic
def init_str_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, ArrayItemArrayType
        ) and data_typ.dtype == types.Array(char_type, 1, 'C')

    def codegen(context, builder, sig, args):
        icm__dkueb, = args
        twx__sau = context.make_helper(builder, string_array_type)
        twx__sau.data = icm__dkueb
        context.nrt.incref(builder, data_typ, icm__dkueb)
        return twx__sau._getvalue()
    return string_array_type(data_typ), codegen


class StringDtype(types.Number):

    def __init__(self):
        super(StringDtype, self).__init__('StringDtype')


string_dtype = StringDtype()
register_model(StringDtype)(models.OpaqueModel)


@box(StringDtype)
def box_string_dtype(typ, val, c):
    whdu__kinm = c.context.insert_const_string(c.builder.module, 'pandas')
    ucpdt__lzdq = c.pyapi.import_module_noblock(whdu__kinm)
    aft__tyrzr = c.pyapi.call_method(ucpdt__lzdq, 'StringDtype', ())
    c.pyapi.decref(ucpdt__lzdq)
    return aft__tyrzr


@unbox(StringDtype)
def unbox_string_dtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


typeof_impl.register(pd.StringDtype)(lambda a, b: string_dtype)
type_callable(pd.StringDtype)(lambda c: lambda : string_dtype)
lower_builtin(pd.StringDtype)(lambda c, b, s, a: c.get_dummy_value())


def create_binary_op_overload(op):

    def overload_string_array_binary_op(lhs, rhs):
        jeelp__eubg = bodo.libs.dict_arr_ext.get_binary_op_overload(op, lhs,
            rhs)
        if jeelp__eubg is not None:
            return jeelp__eubg
        if is_str_arr_type(lhs) and is_str_arr_type(rhs):

            def impl_both(lhs, rhs):
                numba.parfors.parfor.init_prange()
                phhby__ywnd = len(lhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(phhby__ywnd)
                for i in numba.parfors.parfor.internal_prange(phhby__ywnd):
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
                phhby__ywnd = len(lhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(phhby__ywnd)
                for i in numba.parfors.parfor.internal_prange(phhby__ywnd):
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
                phhby__ywnd = len(rhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(phhby__ywnd)
                for i in numba.parfors.parfor.internal_prange(phhby__ywnd):
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
    ytjqq__boh = is_str_arr_type(lhs) or isinstance(lhs, types.Array
        ) and lhs.dtype == string_type
    bhiu__ehop = is_str_arr_type(rhs) or isinstance(rhs, types.Array
        ) and rhs.dtype == string_type
    if is_str_arr_type(lhs) and bhiu__ehop or ytjqq__boh and is_str_arr_type(
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
    cgiga__qtjio = context.make_helper(builder, arr_typ, arr_value)
    tbwpl__rzck = ArrayItemArrayType(char_arr_type)
    xmqu__iobda = _get_array_item_arr_payload(context, builder, tbwpl__rzck,
        cgiga__qtjio.data)
    return xmqu__iobda


@intrinsic
def num_strings(typingctx, str_arr_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        return xmqu__iobda.n_arrays
    return types.int64(string_array_type), codegen


def _get_num_total_chars(builder, offsets, num_strings):
    return builder.zext(builder.load(builder.gep(offsets, [num_strings])),
        lir.IntType(64))


@intrinsic
def num_total_chars(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        cvv__kymp = context.make_helper(builder, offset_arr_type,
            xmqu__iobda.offsets).data
        return _get_num_total_chars(builder, cvv__kymp, xmqu__iobda.n_arrays)
    return types.uint64(in_arr_typ), codegen


@intrinsic
def get_offset_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        sqrn__wyj = context.make_helper(builder, offset_arr_type,
            xmqu__iobda.offsets)
        uunok__dbhut = context.make_helper(builder, offset_ctypes_type)
        uunok__dbhut.data = builder.bitcast(sqrn__wyj.data, lir.IntType(
            offset_type.bitwidth).as_pointer())
        uunok__dbhut.meminfo = sqrn__wyj.meminfo
        aft__tyrzr = uunok__dbhut._getvalue()
        return impl_ret_borrowed(context, builder, offset_ctypes_type,
            aft__tyrzr)
    return offset_ctypes_type(in_arr_typ), codegen


@intrinsic
def get_data_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        icm__dkueb = context.make_helper(builder, char_arr_type,
            xmqu__iobda.data)
        uunok__dbhut = context.make_helper(builder, data_ctypes_type)
        uunok__dbhut.data = icm__dkueb.data
        uunok__dbhut.meminfo = icm__dkueb.meminfo
        aft__tyrzr = uunok__dbhut._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type, aft__tyrzr
            )
    return data_ctypes_type(in_arr_typ), codegen


@intrinsic
def get_data_ptr_ind(typingctx, in_arr_typ, int_t=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        hdlzl__rfnb, ind = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            hdlzl__rfnb, sig.args[0])
        icm__dkueb = context.make_helper(builder, char_arr_type,
            xmqu__iobda.data)
        uunok__dbhut = context.make_helper(builder, data_ctypes_type)
        uunok__dbhut.data = builder.gep(icm__dkueb.data, [ind])
        uunok__dbhut.meminfo = icm__dkueb.meminfo
        aft__tyrzr = uunok__dbhut._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type, aft__tyrzr
            )
    return data_ctypes_type(in_arr_typ, types.intp), codegen


@intrinsic
def copy_single_char(typingctx, dst_ptr_t, dst_ind_t, src_ptr_t, src_ind_t=None
    ):

    def codegen(context, builder, sig, args):
        xgo__ldqdi, oqz__mftjg, ymqv__abggk, cjy__hjtjg = args
        qru__qxxen = builder.bitcast(builder.gep(xgo__ldqdi, [oqz__mftjg]),
            lir.IntType(8).as_pointer())
        vem__ijyhl = builder.bitcast(builder.gep(ymqv__abggk, [cjy__hjtjg]),
            lir.IntType(8).as_pointer())
        hsbds__dnme = builder.load(vem__ijyhl)
        builder.store(hsbds__dnme, qru__qxxen)
        return context.get_dummy_value()
    return types.void(types.voidptr, types.intp, types.voidptr, types.intp
        ), codegen


@intrinsic
def get_null_bitmap_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        wsdth__leoba = context.make_helper(builder, null_bitmap_arr_type,
            xmqu__iobda.null_bitmap)
        uunok__dbhut = context.make_helper(builder, data_ctypes_type)
        uunok__dbhut.data = wsdth__leoba.data
        uunok__dbhut.meminfo = wsdth__leoba.meminfo
        aft__tyrzr = uunok__dbhut._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type, aft__tyrzr
            )
    return data_ctypes_type(in_arr_typ), codegen


@intrinsic
def getitem_str_offset(typingctx, in_arr_typ, ind_t=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        cvv__kymp = context.make_helper(builder, offset_arr_type,
            xmqu__iobda.offsets).data
        return builder.load(builder.gep(cvv__kymp, [ind]))
    return offset_type(in_arr_typ, ind_t), codegen


@intrinsic
def setitem_str_offset(typingctx, str_arr_typ, ind_t, val_t=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind, val = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        offsets = context.make_helper(builder, offset_arr_type, xmqu__iobda
            .offsets).data
        builder.store(val, builder.gep(offsets, [ind]))
        return context.get_dummy_value()
    return types.void(string_array_type, ind_t, offset_type), codegen


@intrinsic
def getitem_str_bitmap(typingctx, in_bitmap_typ, ind_t=None):

    def codegen(context, builder, sig, args):
        pvce__ismgq, ind = args
        if in_bitmap_typ == data_ctypes_type:
            uunok__dbhut = context.make_helper(builder, data_ctypes_type,
                pvce__ismgq)
            pvce__ismgq = uunok__dbhut.data
        return builder.load(builder.gep(pvce__ismgq, [ind]))
    return char_type(in_bitmap_typ, ind_t), codegen


@intrinsic
def setitem_str_bitmap(typingctx, in_bitmap_typ, ind_t, val_t=None):

    def codegen(context, builder, sig, args):
        pvce__ismgq, ind, val = args
        if in_bitmap_typ == data_ctypes_type:
            uunok__dbhut = context.make_helper(builder, data_ctypes_type,
                pvce__ismgq)
            pvce__ismgq = uunok__dbhut.data
        builder.store(val, builder.gep(pvce__ismgq, [ind]))
        return context.get_dummy_value()
    return types.void(in_bitmap_typ, ind_t, char_type), codegen


@intrinsic
def copy_str_arr_slice(typingctx, out_str_arr_typ, in_str_arr_typ, ind_t=None):
    assert out_str_arr_typ == string_array_type and in_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr, ind = args
        hqi__ocm = _get_str_binary_arr_payload(context, builder, in_str_arr,
            string_array_type)
        uen__zvv = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        sjee__nja = context.make_helper(builder, offset_arr_type, hqi__ocm.
            offsets).data
        pdwup__wkgh = context.make_helper(builder, offset_arr_type,
            uen__zvv.offsets).data
        senh__kcnim = context.make_helper(builder, char_arr_type, hqi__ocm.data
            ).data
        rlnnz__yqo = context.make_helper(builder, char_arr_type, uen__zvv.data
            ).data
        etmvh__wnhg = context.make_helper(builder, null_bitmap_arr_type,
            hqi__ocm.null_bitmap).data
        cwrst__nzg = context.make_helper(builder, null_bitmap_arr_type,
            uen__zvv.null_bitmap).data
        gwoxa__trbyz = builder.add(ind, context.get_constant(types.intp, 1))
        cgutils.memcpy(builder, pdwup__wkgh, sjee__nja, gwoxa__trbyz)
        cgutils.memcpy(builder, rlnnz__yqo, senh__kcnim, builder.load(
            builder.gep(sjee__nja, [ind])))
        givo__sffi = builder.add(ind, lir.Constant(lir.IntType(64), 7))
        apsjx__prlo = builder.lshr(givo__sffi, lir.Constant(lir.IntType(64), 3)
            )
        cgutils.memcpy(builder, cwrst__nzg, etmvh__wnhg, apsjx__prlo)
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type, ind_t), codegen


@intrinsic
def copy_data(typingctx, str_arr_typ, out_str_arr_typ=None):
    assert str_arr_typ == string_array_type and out_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr = args
        hqi__ocm = _get_str_binary_arr_payload(context, builder, in_str_arr,
            string_array_type)
        uen__zvv = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        sjee__nja = context.make_helper(builder, offset_arr_type, hqi__ocm.
            offsets).data
        senh__kcnim = context.make_helper(builder, char_arr_type, hqi__ocm.data
            ).data
        rlnnz__yqo = context.make_helper(builder, char_arr_type, uen__zvv.data
            ).data
        num_total_chars = _get_num_total_chars(builder, sjee__nja, hqi__ocm
            .n_arrays)
        cgutils.memcpy(builder, rlnnz__yqo, senh__kcnim, num_total_chars)
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type), codegen


@intrinsic
def copy_non_null_offsets(typingctx, str_arr_typ, out_str_arr_typ=None):
    assert str_arr_typ == string_array_type and out_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr = args
        hqi__ocm = _get_str_binary_arr_payload(context, builder, in_str_arr,
            string_array_type)
        uen__zvv = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        sjee__nja = context.make_helper(builder, offset_arr_type, hqi__ocm.
            offsets).data
        pdwup__wkgh = context.make_helper(builder, offset_arr_type,
            uen__zvv.offsets).data
        etmvh__wnhg = context.make_helper(builder, null_bitmap_arr_type,
            hqi__ocm.null_bitmap).data
        phhby__ywnd = hqi__ocm.n_arrays
        utiyz__kddn = context.get_constant(offset_type, 0)
        tfgkc__mla = cgutils.alloca_once_value(builder, utiyz__kddn)
        with cgutils.for_range(builder, phhby__ywnd) as yex__htna:
            qxm__wlgoa = lower_is_na(context, builder, etmvh__wnhg,
                yex__htna.index)
            with cgutils.if_likely(builder, builder.not_(qxm__wlgoa)):
                uwm__opw = builder.load(builder.gep(sjee__nja, [yex__htna.
                    index]))
                gxqe__ztpve = builder.load(tfgkc__mla)
                builder.store(uwm__opw, builder.gep(pdwup__wkgh, [gxqe__ztpve])
                    )
                builder.store(builder.add(gxqe__ztpve, lir.Constant(context
                    .get_value_type(offset_type), 1)), tfgkc__mla)
        gxqe__ztpve = builder.load(tfgkc__mla)
        uwm__opw = builder.load(builder.gep(sjee__nja, [phhby__ywnd]))
        builder.store(uwm__opw, builder.gep(pdwup__wkgh, [gxqe__ztpve]))
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type), codegen


@intrinsic
def str_copy(typingctx, buff_arr_typ, ind_typ, str_typ, len_typ=None):

    def codegen(context, builder, sig, args):
        guagn__usj, ind, str, qxb__jkkd = args
        guagn__usj = context.make_array(sig.args[0])(context, builder,
            guagn__usj)
        llyy__bvcw = builder.gep(guagn__usj.data, [ind])
        cgutils.raw_memcpy(builder, llyy__bvcw, str, qxb__jkkd, 1)
        return context.get_dummy_value()
    return types.void(null_bitmap_arr_type, types.intp, types.voidptr,
        types.intp), codegen


@intrinsic
def str_copy_ptr(typingctx, ptr_typ, ind_typ, str_typ, len_typ=None):

    def codegen(context, builder, sig, args):
        llyy__bvcw, ind, tysnd__hfsh, qxb__jkkd = args
        llyy__bvcw = builder.gep(llyy__bvcw, [ind])
        cgutils.raw_memcpy(builder, llyy__bvcw, tysnd__hfsh, qxb__jkkd, 1)
        return context.get_dummy_value()
    return types.void(types.voidptr, types.intp, types.voidptr, types.intp
        ), codegen


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_length(A, i):
    return np.int64(getitem_str_offset(A, i + 1) - getitem_str_offset(A, i))


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_str_length(A, i):
    rukuk__tfqb = np.int64(getitem_str_offset(A, i))
    qyyx__smn = np.int64(getitem_str_offset(A, i + 1))
    l = qyyx__smn - rukuk__tfqb
    jlp__cef = get_data_ptr_ind(A, rukuk__tfqb)
    for j in range(l):
        if bodo.hiframes.split_impl.getitem_c_arr(jlp__cef, j) >= 128:
            return len(A[i])
    return l


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_ptr(A, i):
    return get_data_ptr_ind(A, getitem_str_offset(A, i))


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_copy(B, j, A, i):
    if j == 0:
        setitem_str_offset(B, 0, 0)
    atev__mdbdv = getitem_str_offset(A, i)
    qdriu__nkho = getitem_str_offset(A, i + 1)
    vdreo__ufulo = qdriu__nkho - atev__mdbdv
    aoclp__kqf = getitem_str_offset(B, j)
    dycb__bviz = aoclp__kqf + vdreo__ufulo
    setitem_str_offset(B, j + 1, dycb__bviz)
    if str_arr_is_na(A, i):
        str_arr_set_na(B, j)
    else:
        str_arr_set_not_na(B, j)
    if vdreo__ufulo != 0:
        icm__dkueb = B._data
        bodo.libs.array_item_arr_ext.ensure_data_capacity(icm__dkueb, np.
            int64(aoclp__kqf), np.int64(dycb__bviz))
        ori__heus = get_data_ptr(B).data
        sdmvg__tmcb = get_data_ptr(A).data
        memcpy_region(ori__heus, aoclp__kqf, sdmvg__tmcb, atev__mdbdv,
            vdreo__ufulo, 1)


@numba.njit(no_cpython_wrapper=True)
def get_str_null_bools(str_arr):
    phhby__ywnd = len(str_arr)
    lnxt__ubcnv = np.empty(phhby__ywnd, np.bool_)
    for i in range(phhby__ywnd):
        lnxt__ubcnv[i] = bodo.libs.array_kernels.isna(str_arr, i)
    return lnxt__ubcnv


def to_list_if_immutable_arr(arr, str_null_bools=None):
    return arr


@overload(to_list_if_immutable_arr, no_unliteral=True)
def to_list_if_immutable_arr_overload(data, str_null_bools=None):
    if is_str_arr_type(data) or data == binary_array_type:

        def to_list_impl(data, str_null_bools=None):
            phhby__ywnd = len(data)
            l = []
            for i in range(phhby__ywnd):
                l.append(data[i])
            return l
        return to_list_impl
    if isinstance(data, types.BaseTuple):
        lmz__gdb = data.count
        lgwix__mjw = ['to_list_if_immutable_arr(data[{}])'.format(i) for i in
            range(lmz__gdb)]
        if is_overload_true(str_null_bools):
            lgwix__mjw += ['get_str_null_bools(data[{}])'.format(i) for i in
                range(lmz__gdb) if is_str_arr_type(data.types[i]) or data.
                types[i] == binary_array_type]
        esmh__gqp = 'def f(data, str_null_bools=None):\n'
        esmh__gqp += '  return ({}{})\n'.format(', '.join(lgwix__mjw), ',' if
            lmz__gdb == 1 else '')
        ajlfk__tnynd = {}
        exec(esmh__gqp, {'to_list_if_immutable_arr':
            to_list_if_immutable_arr, 'get_str_null_bools':
            get_str_null_bools, 'bodo': bodo}, ajlfk__tnynd)
        olvc__pdvr = ajlfk__tnynd['f']
        return olvc__pdvr
    return lambda data, str_null_bools=None: data


def cp_str_list_to_array(str_arr, str_list, str_null_bools=None):
    return


@overload(cp_str_list_to_array, no_unliteral=True)
def cp_str_list_to_array_overload(str_arr, list_data, str_null_bools=None):
    if str_arr == string_array_type:
        if is_overload_none(str_null_bools):

            def cp_str_list_impl(str_arr, list_data, str_null_bools=None):
                phhby__ywnd = len(list_data)
                for i in range(phhby__ywnd):
                    tysnd__hfsh = list_data[i]
                    str_arr[i] = tysnd__hfsh
            return cp_str_list_impl
        else:

            def cp_str_list_impl_null(str_arr, list_data, str_null_bools=None):
                phhby__ywnd = len(list_data)
                for i in range(phhby__ywnd):
                    tysnd__hfsh = list_data[i]
                    str_arr[i] = tysnd__hfsh
                    if str_null_bools[i]:
                        str_arr_set_na(str_arr, i)
                    else:
                        str_arr_set_not_na(str_arr, i)
            return cp_str_list_impl_null
    if isinstance(str_arr, types.BaseTuple):
        lmz__gdb = str_arr.count
        ewfu__lxlmu = 0
        esmh__gqp = 'def f(str_arr, list_data, str_null_bools=None):\n'
        for i in range(lmz__gdb):
            if is_overload_true(str_null_bools) and str_arr.types[i
                ] == string_array_type:
                esmh__gqp += (
                    '  cp_str_list_to_array(str_arr[{}], list_data[{}], list_data[{}])\n'
                    .format(i, i, lmz__gdb + ewfu__lxlmu))
                ewfu__lxlmu += 1
            else:
                esmh__gqp += (
                    '  cp_str_list_to_array(str_arr[{}], list_data[{}])\n'.
                    format(i, i))
        esmh__gqp += '  return\n'
        ajlfk__tnynd = {}
        exec(esmh__gqp, {'cp_str_list_to_array': cp_str_list_to_array},
            ajlfk__tnynd)
        urnew__exgt = ajlfk__tnynd['f']
        return urnew__exgt
    return lambda str_arr, list_data, str_null_bools=None: None


def str_list_to_array(str_list):
    return str_list


@overload(str_list_to_array, no_unliteral=True)
def str_list_to_array_overload(str_list):
    if isinstance(str_list, types.List) and str_list.dtype == bodo.string_type:

        def str_list_impl(str_list):
            phhby__ywnd = len(str_list)
            str_arr = pre_alloc_string_array(phhby__ywnd, -1)
            for i in range(phhby__ywnd):
                tysnd__hfsh = str_list[i]
                str_arr[i] = tysnd__hfsh
            return str_arr
        return str_list_impl
    return lambda str_list: str_list


def get_num_total_chars(A):
    pass


@overload(get_num_total_chars)
def overload_get_num_total_chars(A):
    if isinstance(A, types.List) and A.dtype == string_type:

        def str_list_impl(A):
            phhby__ywnd = len(A)
            kwr__qwq = 0
            for i in range(phhby__ywnd):
                tysnd__hfsh = A[i]
                kwr__qwq += get_utf8_size(tysnd__hfsh)
            return kwr__qwq
        return str_list_impl
    assert A == string_array_type
    return lambda A: num_total_chars(A)


@overload_method(StringArrayType, 'copy', no_unliteral=True)
def str_arr_copy_overload(arr):

    def copy_impl(arr):
        phhby__ywnd = len(arr)
        n_chars = num_total_chars(arr)
        dumw__hxh = pre_alloc_string_array(phhby__ywnd, np.int64(n_chars))
        copy_str_arr_slice(dumw__hxh, arr, phhby__ywnd)
        return dumw__hxh
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
    esmh__gqp = 'def f(in_seq):\n'
    esmh__gqp += '    n_strs = len(in_seq)\n'
    esmh__gqp += '    A = pre_alloc_string_array(n_strs, -1)\n'
    esmh__gqp += '    return A\n'
    ajlfk__tnynd = {}
    exec(esmh__gqp, {'pre_alloc_string_array': pre_alloc_string_array},
        ajlfk__tnynd)
    djvf__uwp = ajlfk__tnynd['f']
    return djvf__uwp


@numba.generated_jit(nopython=True)
def str_arr_from_sequence(in_seq):
    if in_seq.dtype == bodo.bytes_type:
        hheos__vjfxr = 'pre_alloc_binary_array'
    else:
        hheos__vjfxr = 'pre_alloc_string_array'
    esmh__gqp = 'def f(in_seq):\n'
    esmh__gqp += '    n_strs = len(in_seq)\n'
    esmh__gqp += f'    A = {hheos__vjfxr}(n_strs, -1)\n'
    esmh__gqp += '    for i in range(n_strs):\n'
    esmh__gqp += '        A[i] = in_seq[i]\n'
    esmh__gqp += '    return A\n'
    ajlfk__tnynd = {}
    exec(esmh__gqp, {'pre_alloc_string_array': pre_alloc_string_array,
        'pre_alloc_binary_array': pre_alloc_binary_array}, ajlfk__tnynd)
    djvf__uwp = ajlfk__tnynd['f']
    return djvf__uwp


@intrinsic
def set_all_offsets_to_0(typingctx, arr_typ=None):
    assert arr_typ in (string_array_type, binary_array_type
        ), 'set_all_offsets_to_0 requires a string or binary array'

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        wfp__wjio = builder.add(xmqu__iobda.n_arrays, lir.Constant(lir.
            IntType(64), 1))
        bbjx__yoxyb = builder.lshr(lir.Constant(lir.IntType(64),
            offset_type.bitwidth), lir.Constant(lir.IntType(64), 3))
        apsjx__prlo = builder.mul(wfp__wjio, bbjx__yoxyb)
        hfu__xelw = context.make_array(offset_arr_type)(context, builder,
            xmqu__iobda.offsets).data
        cgutils.memset(builder, hfu__xelw, apsjx__prlo, 0)
        return context.get_dummy_value()
    return types.none(arr_typ), codegen


@intrinsic
def set_bitmap_all_NA(typingctx, arr_typ=None):
    assert arr_typ in (string_array_type, binary_array_type
        ), 'set_bitmap_all_NA requires a string or binary array'

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        lbdp__vpdt = xmqu__iobda.n_arrays
        apsjx__prlo = builder.lshr(builder.add(lbdp__vpdt, lir.Constant(lir
            .IntType(64), 7)), lir.Constant(lir.IntType(64), 3))
        vylst__ngo = context.make_array(null_bitmap_arr_type)(context,
            builder, xmqu__iobda.null_bitmap).data
        cgutils.memset(builder, vylst__ngo, apsjx__prlo, 0)
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
    jfy__fvnxl = 0
    if total_len == 0:
        for i in range(len(offsets)):
            offsets[i] = 0
    else:
        zwe__bcsjt = len(len_arr)
        for i in range(zwe__bcsjt):
            offsets[i] = jfy__fvnxl
            jfy__fvnxl += len_arr[i]
        offsets[zwe__bcsjt] = jfy__fvnxl
    return str_arr


kBitmask = np.array([1, 2, 4, 8, 16, 32, 64, 128], dtype=np.uint8)


@numba.njit
def set_bit_to(bits, i, bit_is_set):
    ulzsx__xpd = i // 8
    zzp__zjqze = getitem_str_bitmap(bits, ulzsx__xpd)
    zzp__zjqze ^= np.uint8(-np.uint8(bit_is_set) ^ zzp__zjqze) & kBitmask[i % 8
        ]
    setitem_str_bitmap(bits, ulzsx__xpd, zzp__zjqze)


@numba.njit
def get_bit_bitmap(bits, i):
    return getitem_str_bitmap(bits, i >> 3) >> (i & 7) & 1


@numba.njit
def copy_nulls_range(out_str_arr, in_str_arr, out_start):
    eps__cfunt = get_null_bitmap_ptr(out_str_arr)
    pygmd__tzsm = get_null_bitmap_ptr(in_str_arr)
    for j in range(len(in_str_arr)):
        swbj__wpmrr = get_bit_bitmap(pygmd__tzsm, j)
        set_bit_to(eps__cfunt, out_start + j, swbj__wpmrr)


@intrinsic
def set_string_array_range(typingctx, out_typ, in_typ, curr_str_typ,
    curr_chars_typ=None):
    assert out_typ == string_array_type and in_typ == string_array_type or out_typ == binary_array_type and in_typ == binary_array_type, 'set_string_array_range requires string or binary arrays'
    assert isinstance(curr_str_typ, types.Integer) and isinstance(
        curr_chars_typ, types.Integer
        ), 'set_string_array_range requires integer indices'

    def codegen(context, builder, sig, args):
        out_arr, hdlzl__rfnb, dqwwm__sul, vzng__opd = args
        hqi__ocm = _get_str_binary_arr_payload(context, builder,
            hdlzl__rfnb, string_array_type)
        uen__zvv = _get_str_binary_arr_payload(context, builder, out_arr,
            string_array_type)
        sjee__nja = context.make_helper(builder, offset_arr_type, hqi__ocm.
            offsets).data
        pdwup__wkgh = context.make_helper(builder, offset_arr_type,
            uen__zvv.offsets).data
        senh__kcnim = context.make_helper(builder, char_arr_type, hqi__ocm.data
            ).data
        rlnnz__yqo = context.make_helper(builder, char_arr_type, uen__zvv.data
            ).data
        num_total_chars = _get_num_total_chars(builder, sjee__nja, hqi__ocm
            .n_arrays)
        grxt__jrgt = lir.FunctionType(lir.VoidType(), [lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(64), lir.IntType(64), lir.IntType(64),
            lir.IntType(64)])
        foj__eokuj = cgutils.get_or_insert_function(builder.module,
            grxt__jrgt, name='set_string_array_range')
        builder.call(foj__eokuj, [pdwup__wkgh, rlnnz__yqo, sjee__nja,
            senh__kcnim, dqwwm__sul, vzng__opd, hqi__ocm.n_arrays,
            num_total_chars])
        aomgw__gssj = context.typing_context.resolve_value_type(
            copy_nulls_range)
        wei__kgs = aomgw__gssj.get_call_type(context.typing_context, (
            string_array_type, string_array_type, types.int64), {})
        mysh__tvmem = context.get_function(aomgw__gssj, wei__kgs)
        mysh__tvmem(builder, (out_arr, hdlzl__rfnb, dqwwm__sul))
        return context.get_dummy_value()
    sig = types.void(out_typ, in_typ, types.intp, types.intp)
    return sig, codegen


@box(BinaryArrayType)
@box(StringArrayType)
def box_str_arr(typ, val, c):
    assert typ in [binary_array_type, string_array_type]
    nst__cyci = c.context.make_helper(c.builder, typ, val)
    tbwpl__rzck = ArrayItemArrayType(char_arr_type)
    xmqu__iobda = _get_array_item_arr_payload(c.context, c.builder,
        tbwpl__rzck, nst__cyci.data)
    mztj__lsoj = c.context.get_constant(types.int32, int(typ ==
        binary_array_type))
    epe__yco = 'np_array_from_string_array'
    if use_pd_string_array and typ != binary_array_type:
        epe__yco = 'pd_array_from_string_array'
    grxt__jrgt = lir.FunctionType(c.context.get_argument_type(types.
        pyobject), [lir.IntType(64), lir.IntType(offset_type.bitwidth).
        as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
        as_pointer(), lir.IntType(32)])
    npi__lbiza = cgutils.get_or_insert_function(c.builder.module,
        grxt__jrgt, name=epe__yco)
    cvv__kymp = c.context.make_array(offset_arr_type)(c.context, c.builder,
        xmqu__iobda.offsets).data
    jlp__cef = c.context.make_array(char_arr_type)(c.context, c.builder,
        xmqu__iobda.data).data
    vylst__ngo = c.context.make_array(null_bitmap_arr_type)(c.context, c.
        builder, xmqu__iobda.null_bitmap).data
    arr = c.builder.call(npi__lbiza, [xmqu__iobda.n_arrays, cvv__kymp,
        jlp__cef, vylst__ngo, mztj__lsoj])
    c.context.nrt.decref(c.builder, typ, val)
    return arr


@intrinsic
def str_arr_is_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        vylst__ngo = context.make_array(null_bitmap_arr_type)(context,
            builder, xmqu__iobda.null_bitmap).data
        pczr__jlxq = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        qetux__urowc = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        zzp__zjqze = builder.load(builder.gep(vylst__ngo, [pczr__jlxq],
            inbounds=True))
        mgph__oxsv = lir.ArrayType(lir.IntType(8), 8)
        wrzr__wmbm = cgutils.alloca_once_value(builder, lir.Constant(
            mgph__oxsv, (1, 2, 4, 8, 16, 32, 64, 128)))
        msh__gmc = builder.load(builder.gep(wrzr__wmbm, [lir.Constant(lir.
            IntType(64), 0), qetux__urowc], inbounds=True))
        return builder.icmp_unsigned('==', builder.and_(zzp__zjqze,
            msh__gmc), lir.Constant(lir.IntType(8), 0))
    return types.bool_(str_arr_typ, types.intp), codegen


@intrinsic
def str_arr_set_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        pczr__jlxq = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        qetux__urowc = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        vylst__ngo = context.make_array(null_bitmap_arr_type)(context,
            builder, xmqu__iobda.null_bitmap).data
        offsets = context.make_helper(builder, offset_arr_type, xmqu__iobda
            .offsets).data
        kbsn__oyf = builder.gep(vylst__ngo, [pczr__jlxq], inbounds=True)
        zzp__zjqze = builder.load(kbsn__oyf)
        mgph__oxsv = lir.ArrayType(lir.IntType(8), 8)
        wrzr__wmbm = cgutils.alloca_once_value(builder, lir.Constant(
            mgph__oxsv, (1, 2, 4, 8, 16, 32, 64, 128)))
        msh__gmc = builder.load(builder.gep(wrzr__wmbm, [lir.Constant(lir.
            IntType(64), 0), qetux__urowc], inbounds=True))
        msh__gmc = builder.xor(msh__gmc, lir.Constant(lir.IntType(8), -1))
        builder.store(builder.and_(zzp__zjqze, msh__gmc), kbsn__oyf)
        if str_arr_typ == string_array_type:
            daag__hxfpa = builder.add(ind, lir.Constant(lir.IntType(64), 1))
            ibl__xqzvv = builder.icmp_unsigned('!=', daag__hxfpa,
                xmqu__iobda.n_arrays)
            with builder.if_then(ibl__xqzvv):
                builder.store(builder.load(builder.gep(offsets, [ind])),
                    builder.gep(offsets, [daag__hxfpa]))
        return context.get_dummy_value()
    return types.void(str_arr_typ, types.intp), codegen


@intrinsic
def str_arr_set_not_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        pczr__jlxq = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        qetux__urowc = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        vylst__ngo = context.make_array(null_bitmap_arr_type)(context,
            builder, xmqu__iobda.null_bitmap).data
        kbsn__oyf = builder.gep(vylst__ngo, [pczr__jlxq], inbounds=True)
        zzp__zjqze = builder.load(kbsn__oyf)
        mgph__oxsv = lir.ArrayType(lir.IntType(8), 8)
        wrzr__wmbm = cgutils.alloca_once_value(builder, lir.Constant(
            mgph__oxsv, (1, 2, 4, 8, 16, 32, 64, 128)))
        msh__gmc = builder.load(builder.gep(wrzr__wmbm, [lir.Constant(lir.
            IntType(64), 0), qetux__urowc], inbounds=True))
        builder.store(builder.or_(zzp__zjqze, msh__gmc), kbsn__oyf)
        return context.get_dummy_value()
    return types.void(str_arr_typ, types.intp), codegen


@intrinsic
def set_null_bits_to_value(typingctx, arr_typ, value_typ=None):
    assert (arr_typ == string_array_type or arr_typ == binary_array_type
        ) and is_overload_constant_int(value_typ)

    def codegen(context, builder, sig, args):
        in_str_arr, value = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        apsjx__prlo = builder.udiv(builder.add(xmqu__iobda.n_arrays, lir.
            Constant(lir.IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
        vylst__ngo = context.make_array(null_bitmap_arr_type)(context,
            builder, xmqu__iobda.null_bitmap).data
        cgutils.memset(builder, vylst__ngo, apsjx__prlo, value)
        return context.get_dummy_value()
    return types.none(arr_typ, types.int8), codegen


def _get_str_binary_arr_data_payload_ptr(context, builder, str_arr):
    kfcdm__rzyxm = context.make_helper(builder, string_array_type, str_arr)
    tbwpl__rzck = ArrayItemArrayType(char_arr_type)
    lifaw__kvwpa = context.make_helper(builder, tbwpl__rzck, kfcdm__rzyxm.data)
    fswgk__rzi = ArrayItemArrayPayloadType(tbwpl__rzck)
    xrtbg__iwap = context.nrt.meminfo_data(builder, lifaw__kvwpa.meminfo)
    groa__khnu = builder.bitcast(xrtbg__iwap, context.get_value_type(
        fswgk__rzi).as_pointer())
    return groa__khnu


@intrinsic
def move_str_binary_arr_payload(typingctx, to_arr_typ, from_arr_typ=None):
    assert to_arr_typ == string_array_type and from_arr_typ == string_array_type or to_arr_typ == binary_array_type and from_arr_typ == binary_array_type

    def codegen(context, builder, sig, args):
        qpmdw__yrokd, jdcd__lzerh = args
        pja__usbvb = _get_str_binary_arr_data_payload_ptr(context, builder,
            jdcd__lzerh)
        eod__dvodh = _get_str_binary_arr_data_payload_ptr(context, builder,
            qpmdw__yrokd)
        dwmj__vdxgh = _get_str_binary_arr_payload(context, builder,
            jdcd__lzerh, sig.args[1])
        avgbe__etrq = _get_str_binary_arr_payload(context, builder,
            qpmdw__yrokd, sig.args[0])
        context.nrt.incref(builder, char_arr_type, dwmj__vdxgh.data)
        context.nrt.incref(builder, offset_arr_type, dwmj__vdxgh.offsets)
        context.nrt.incref(builder, null_bitmap_arr_type, dwmj__vdxgh.
            null_bitmap)
        context.nrt.decref(builder, char_arr_type, avgbe__etrq.data)
        context.nrt.decref(builder, offset_arr_type, avgbe__etrq.offsets)
        context.nrt.decref(builder, null_bitmap_arr_type, avgbe__etrq.
            null_bitmap)
        builder.store(builder.load(pja__usbvb), eod__dvodh)
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
        phhby__ywnd = _get_utf8_size(s._data, s._length, s._kind)
        dummy_use(s)
        return phhby__ywnd
    return impl


@intrinsic
def setitem_str_arr_ptr(typingctx, str_arr_t, ind_t, ptr_t, len_t=None):

    def codegen(context, builder, sig, args):
        arr, ind, llyy__bvcw, wesg__mjte = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder, arr,
            sig.args[0])
        offsets = context.make_helper(builder, offset_arr_type, xmqu__iobda
            .offsets).data
        data = context.make_helper(builder, char_arr_type, xmqu__iobda.data
            ).data
        grxt__jrgt = lir.FunctionType(lir.VoidType(), [lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(64),
            lir.IntType(32), lir.IntType(32), lir.IntType(64)])
        dqw__dcztn = cgutils.get_or_insert_function(builder.module,
            grxt__jrgt, name='setitem_string_array')
        npetv__ovpy = context.get_constant(types.int32, -1)
        est__txmg = context.get_constant(types.int32, 1)
        num_total_chars = _get_num_total_chars(builder, offsets,
            xmqu__iobda.n_arrays)
        builder.call(dqw__dcztn, [offsets, data, num_total_chars, builder.
            extract_value(llyy__bvcw, 0), wesg__mjte, npetv__ovpy,
            est__txmg, ind])
        return context.get_dummy_value()
    return types.void(str_arr_t, ind_t, ptr_t, len_t), codegen


def lower_is_na(context, builder, bull_bitmap, ind):
    grxt__jrgt = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
        as_pointer(), lir.IntType(64)])
    gvyjh__nbjls = cgutils.get_or_insert_function(builder.module,
        grxt__jrgt, name='is_na')
    return builder.call(gvyjh__nbjls, [bull_bitmap, ind])


@intrinsic
def _memcpy(typingctx, dest_t, src_t, count_t, item_size_t=None):

    def codegen(context, builder, sig, args):
        qru__qxxen, vem__ijyhl, lmz__gdb, dxx__xwu = args
        cgutils.raw_memcpy(builder, qru__qxxen, vem__ijyhl, lmz__gdb, dxx__xwu)
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
        buti__vao, jdkse__gavr = unicode_to_utf8_and_len(val)
        vil__cxvjj = getitem_str_offset(A, ind)
        awmnv__jxhm = getitem_str_offset(A, ind + 1)
        vvsl__utt = awmnv__jxhm - vil__cxvjj
        if vvsl__utt != jdkse__gavr:
            return False
        llyy__bvcw = get_data_ptr_ind(A, vil__cxvjj)
        return memcmp(llyy__bvcw, buti__vao, jdkse__gavr) == 0
    return impl


def str_arr_setitem_int_to_str(A, ind, value):
    A[ind] = str(value)


@overload(str_arr_setitem_int_to_str)
def overload_str_arr_setitem_int_to_str(A, ind, val):

    def impl(A, ind, val):
        vil__cxvjj = getitem_str_offset(A, ind)
        vvsl__utt = bodo.libs.str_ext.int_to_str_len(val)
        qke__wxov = vil__cxvjj + vvsl__utt
        bodo.libs.array_item_arr_ext.ensure_data_capacity(A._data,
            vil__cxvjj, qke__wxov)
        llyy__bvcw = get_data_ptr_ind(A, vil__cxvjj)
        inplace_int64_to_str(llyy__bvcw, vvsl__utt, val)
        setitem_str_offset(A, ind + 1, vil__cxvjj + vvsl__utt)
        str_arr_set_not_na(A, ind)
    return impl


@intrinsic
def inplace_set_NA_str(typingctx, ptr_typ=None):

    def codegen(context, builder, sig, args):
        llyy__bvcw, = args
        jhqhb__isels = context.insert_const_string(builder.module, '<NA>')
        dru__kjv = lir.Constant(lir.IntType(64), len('<NA>'))
        cgutils.raw_memcpy(builder, llyy__bvcw, jhqhb__isels, dru__kjv, 1)
    return types.none(types.voidptr), codegen


def str_arr_setitem_NA_str(A, ind):
    A[ind] = '<NA>'


@overload(str_arr_setitem_NA_str)
def overload_str_arr_setitem_NA_str(A, ind):
    dmw__tjsv = len('<NA>')

    def impl(A, ind):
        vil__cxvjj = getitem_str_offset(A, ind)
        qke__wxov = vil__cxvjj + dmw__tjsv
        bodo.libs.array_item_arr_ext.ensure_data_capacity(A._data,
            vil__cxvjj, qke__wxov)
        llyy__bvcw = get_data_ptr_ind(A, vil__cxvjj)
        inplace_set_NA_str(llyy__bvcw)
        setitem_str_offset(A, ind + 1, vil__cxvjj + dmw__tjsv)
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
            vil__cxvjj = getitem_str_offset(A, ind)
            awmnv__jxhm = getitem_str_offset(A, ind + 1)
            wesg__mjte = awmnv__jxhm - vil__cxvjj
            llyy__bvcw = get_data_ptr_ind(A, vil__cxvjj)
            xpnm__mzghi = decode_utf8(llyy__bvcw, wesg__mjte)
            return xpnm__mzghi
        return str_arr_getitem_impl
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:

        def bool_impl(A, ind):
            ind = bodo.utils.conversion.coerce_to_ndarray(ind)
            phhby__ywnd = len(A)
            n_strs = 0
            n_chars = 0
            for i in range(phhby__ywnd):
                if not bodo.libs.array_kernels.isna(ind, i) and ind[i]:
                    n_strs += 1
                    n_chars += get_str_arr_item_length(A, i)
            out_arr = pre_alloc_string_array(n_strs, n_chars)
            ori__heus = get_data_ptr(out_arr).data
            sdmvg__tmcb = get_data_ptr(A).data
            ewfu__lxlmu = 0
            gxqe__ztpve = 0
            setitem_str_offset(out_arr, 0, 0)
            for i in range(phhby__ywnd):
                if not bodo.libs.array_kernels.isna(ind, i) and ind[i]:
                    qkf__xjwxi = get_str_arr_item_length(A, i)
                    if qkf__xjwxi == 1:
                        copy_single_char(ori__heus, gxqe__ztpve,
                            sdmvg__tmcb, getitem_str_offset(A, i))
                    else:
                        memcpy_region(ori__heus, gxqe__ztpve, sdmvg__tmcb,
                            getitem_str_offset(A, i), qkf__xjwxi, 1)
                    gxqe__ztpve += qkf__xjwxi
                    setitem_str_offset(out_arr, ewfu__lxlmu + 1, gxqe__ztpve)
                    if str_arr_is_na(A, i):
                        str_arr_set_na(out_arr, ewfu__lxlmu)
                    else:
                        str_arr_set_not_na(out_arr, ewfu__lxlmu)
                    ewfu__lxlmu += 1
            return out_arr
        return bool_impl
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def str_arr_arr_impl(A, ind):
            phhby__ywnd = len(ind)
            out_arr = pre_alloc_string_array(phhby__ywnd, -1)
            ewfu__lxlmu = 0
            for i in range(phhby__ywnd):
                tysnd__hfsh = A[ind[i]]
                out_arr[ewfu__lxlmu] = tysnd__hfsh
                if str_arr_is_na(A, ind[i]):
                    str_arr_set_na(out_arr, ewfu__lxlmu)
                ewfu__lxlmu += 1
            return out_arr
        return str_arr_arr_impl
    if isinstance(ind, types.SliceType):

        def str_arr_slice_impl(A, ind):
            phhby__ywnd = len(A)
            dqnk__xyqps = numba.cpython.unicode._normalize_slice(ind,
                phhby__ywnd)
            mamz__oquz = numba.cpython.unicode._slice_span(dqnk__xyqps)
            if dqnk__xyqps.step == 1:
                vil__cxvjj = getitem_str_offset(A, dqnk__xyqps.start)
                awmnv__jxhm = getitem_str_offset(A, dqnk__xyqps.stop)
                n_chars = awmnv__jxhm - vil__cxvjj
                dumw__hxh = pre_alloc_string_array(mamz__oquz, np.int64(
                    n_chars))
                for i in range(mamz__oquz):
                    dumw__hxh[i] = A[dqnk__xyqps.start + i]
                    if str_arr_is_na(A, dqnk__xyqps.start + i):
                        str_arr_set_na(dumw__hxh, i)
                return dumw__hxh
            else:
                dumw__hxh = pre_alloc_string_array(mamz__oquz, -1)
                for i in range(mamz__oquz):
                    dumw__hxh[i] = A[dqnk__xyqps.start + i * dqnk__xyqps.step]
                    if str_arr_is_na(A, dqnk__xyqps.start + i * dqnk__xyqps
                        .step):
                        str_arr_set_na(dumw__hxh, i)
                return dumw__hxh
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
    rnup__wrgvy = (
        f'StringArray setitem with index {idx} and value {val} not supported yet.'
        )
    if isinstance(idx, types.Integer):
        if val != string_type:
            raise BodoError(rnup__wrgvy)
        favq__vhqr = 4

        def impl_scalar(A, idx, val):
            ogcf__akeac = (val._length if val._is_ascii else favq__vhqr *
                val._length)
            icm__dkueb = A._data
            vil__cxvjj = np.int64(getitem_str_offset(A, idx))
            qke__wxov = vil__cxvjj + ogcf__akeac
            bodo.libs.array_item_arr_ext.ensure_data_capacity(icm__dkueb,
                vil__cxvjj, qke__wxov)
            setitem_string_array(get_offset_ptr(A), get_data_ptr(A),
                qke__wxov, val._data, val._length, val._kind, val._is_ascii,
                idx)
            str_arr_set_not_na(A, idx)
            dummy_use(A)
            dummy_use(val)
        return impl_scalar
    if isinstance(idx, types.SliceType):
        if val == string_array_type:

            def impl_slice(A, idx, val):
                dqnk__xyqps = numba.cpython.unicode._normalize_slice(idx,
                    len(A))
                rukuk__tfqb = dqnk__xyqps.start
                icm__dkueb = A._data
                vil__cxvjj = np.int64(getitem_str_offset(A, rukuk__tfqb))
                qke__wxov = vil__cxvjj + np.int64(num_total_chars(val))
                bodo.libs.array_item_arr_ext.ensure_data_capacity(icm__dkueb,
                    vil__cxvjj, qke__wxov)
                set_string_array_range(A, val, rukuk__tfqb, vil__cxvjj)
                ldcsh__uwzv = 0
                for i in range(dqnk__xyqps.start, dqnk__xyqps.stop,
                    dqnk__xyqps.step):
                    if str_arr_is_na(val, ldcsh__uwzv):
                        str_arr_set_na(A, i)
                    else:
                        str_arr_set_not_na(A, i)
                    ldcsh__uwzv += 1
            return impl_slice
        elif isinstance(val, types.List) and val.dtype == string_type:

            def impl_slice_list(A, idx, val):
                cwluk__lkmr = str_list_to_array(val)
                A[idx] = cwluk__lkmr
            return impl_slice_list
        elif val == string_type:

            def impl_slice(A, idx, val):
                dqnk__xyqps = numba.cpython.unicode._normalize_slice(idx,
                    len(A))
                for i in range(dqnk__xyqps.start, dqnk__xyqps.stop,
                    dqnk__xyqps.step):
                    A[i] = val
            return impl_slice
        else:
            raise BodoError(rnup__wrgvy)
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        if val == string_type:

            def impl_bool_scalar(A, idx, val):
                phhby__ywnd = len(A)
                idx = bodo.utils.conversion.coerce_to_ndarray(idx)
                out_arr = pre_alloc_string_array(phhby__ywnd, -1)
                for i in numba.parfors.parfor.internal_prange(phhby__ywnd):
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
                phhby__ywnd = len(A)
                idx = bodo.utils.conversion.coerce_to_array(idx,
                    use_nullable_array=True)
                out_arr = pre_alloc_string_array(phhby__ywnd, -1)
                ynk__owo = 0
                for i in numba.parfors.parfor.internal_prange(phhby__ywnd):
                    if not bodo.libs.array_kernels.isna(idx, i) and idx[i]:
                        if bodo.libs.array_kernels.isna(val, ynk__owo):
                            out_arr[i] = ''
                            str_arr_set_na(out_arr, ynk__owo)
                        else:
                            out_arr[i] = str(val[ynk__owo])
                        ynk__owo += 1
                    elif bodo.libs.array_kernels.isna(A, i):
                        out_arr[i] = ''
                        str_arr_set_na(out_arr, i)
                    else:
                        get_str_arr_item_copy(out_arr, i, A, i)
                move_str_binary_arr_payload(A, out_arr)
            return impl_bool_arr
        else:
            raise BodoError(rnup__wrgvy)
    raise BodoError(rnup__wrgvy)


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
    addin__whjpw = parse_dtype(dtype, 'StringArray.astype')
    if not isinstance(addin__whjpw, (types.Float, types.Integer)):
        raise BodoError('invalid dtype in StringArray.astype()')
    if isinstance(addin__whjpw, types.Float):

        def impl_float(A, dtype, copy=True):
            numba.parfors.parfor.init_prange()
            phhby__ywnd = len(A)
            B = np.empty(phhby__ywnd, addin__whjpw)
            for i in numba.parfors.parfor.internal_prange(phhby__ywnd):
                if bodo.libs.array_kernels.isna(A, i):
                    B[i] = np.nan
                else:
                    B[i] = float(A[i])
            return B
        return impl_float
    else:

        def impl_int(A, dtype, copy=True):
            numba.parfors.parfor.init_prange()
            phhby__ywnd = len(A)
            B = np.empty(phhby__ywnd, addin__whjpw)
            for i in numba.parfors.parfor.internal_prange(phhby__ywnd):
                B[i] = int(A[i])
            return B
        return impl_int


@intrinsic
def decode_utf8(typingctx, ptr_t, len_t=None):

    def codegen(context, builder, sig, args):
        llyy__bvcw, wesg__mjte = args
        setdg__jlk = context.get_python_api(builder)
        byzsr__rljb = setdg__jlk.string_from_string_and_size(llyy__bvcw,
            wesg__mjte)
        ypfm__nahef = setdg__jlk.to_native_value(string_type, byzsr__rljb
            ).value
        nrrvy__jdcz = cgutils.create_struct_proxy(string_type)(context,
            builder, ypfm__nahef)
        nrrvy__jdcz.hash = nrrvy__jdcz.hash.type(-1)
        setdg__jlk.decref(byzsr__rljb)
        return nrrvy__jdcz._getvalue()
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
        ics__jvw, arr, ind, mkqld__vghq = args
        xmqu__iobda = _get_str_binary_arr_payload(context, builder, arr,
            string_array_type)
        offsets = context.make_helper(builder, offset_arr_type, xmqu__iobda
            .offsets).data
        data = context.make_helper(builder, char_arr_type, xmqu__iobda.data
            ).data
        grxt__jrgt = lir.FunctionType(lir.IntType(32), [ics__jvw.type, lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(64)])
        oywre__zby = 'str_arr_to_int64'
        if sig.args[3].dtype == types.float64:
            oywre__zby = 'str_arr_to_float64'
        else:
            assert sig.args[3].dtype == types.int64
        sdvu__nyw = cgutils.get_or_insert_function(builder.module,
            grxt__jrgt, oywre__zby)
        return builder.call(sdvu__nyw, [ics__jvw, offsets, data, ind])
    return types.int32(out_ptr_t, string_array_type, types.int64, out_dtype_t
        ), codegen


@unbox(BinaryArrayType)
@unbox(StringArrayType)
def unbox_str_series(typ, val, c):
    mztj__lsoj = c.context.get_constant(types.int32, int(typ ==
        binary_array_type))
    grxt__jrgt = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.IntType
        (8).as_pointer(), lir.IntType(32)])
    ennpn__osygx = cgutils.get_or_insert_function(c.builder.module,
        grxt__jrgt, name='string_array_from_sequence')
    hzr__ltro = c.builder.call(ennpn__osygx, [val, mztj__lsoj])
    tbwpl__rzck = ArrayItemArrayType(char_arr_type)
    lifaw__kvwpa = c.context.make_helper(c.builder, tbwpl__rzck)
    lifaw__kvwpa.meminfo = hzr__ltro
    kfcdm__rzyxm = c.context.make_helper(c.builder, typ)
    icm__dkueb = lifaw__kvwpa._getvalue()
    kfcdm__rzyxm.data = icm__dkueb
    tmv__baqh = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(kfcdm__rzyxm._getvalue(), is_error=tmv__baqh)


@lower_constant(BinaryArrayType)
@lower_constant(StringArrayType)
def lower_constant_str_arr(context, builder, typ, pyval):
    phhby__ywnd = len(pyval)
    gxqe__ztpve = 0
    vlguk__uqmn = np.empty(phhby__ywnd + 1, np_offset_type)
    eodkw__mwbe = []
    uhvd__wckfr = np.empty(phhby__ywnd + 7 >> 3, np.uint8)
    for i, s in enumerate(pyval):
        vlguk__uqmn[i] = gxqe__ztpve
        msq__zph = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(uhvd__wckfr, i, int(not msq__zph))
        if msq__zph:
            continue
        hjvaq__zqg = list(s.encode()) if isinstance(s, str) else list(s)
        eodkw__mwbe.extend(hjvaq__zqg)
        gxqe__ztpve += len(hjvaq__zqg)
    vlguk__uqmn[phhby__ywnd] = gxqe__ztpve
    fpo__praxf = np.array(eodkw__mwbe, np.uint8)
    frhd__cezl = context.get_constant(types.int64, phhby__ywnd)
    lzvv__yud = context.get_constant_generic(builder, char_arr_type, fpo__praxf
        )
    orbzp__rui = context.get_constant_generic(builder, offset_arr_type,
        vlguk__uqmn)
    sls__luojx = context.get_constant_generic(builder, null_bitmap_arr_type,
        uhvd__wckfr)
    xmqu__iobda = lir.Constant.literal_struct([frhd__cezl, lzvv__yud,
        orbzp__rui, sls__luojx])
    xmqu__iobda = cgutils.global_constant(builder, '.const.payload',
        xmqu__iobda).bitcast(cgutils.voidptr_t)
    hhrdr__wot = context.get_constant(types.int64, -1)
    hrean__smr = context.get_constant_null(types.voidptr)
    ojaz__eefh = lir.Constant.literal_struct([hhrdr__wot, hrean__smr,
        hrean__smr, xmqu__iobda, hhrdr__wot])
    ojaz__eefh = cgutils.global_constant(builder, '.const.meminfo', ojaz__eefh
        ).bitcast(cgutils.voidptr_t)
    icm__dkueb = lir.Constant.literal_struct([ojaz__eefh])
    kfcdm__rzyxm = lir.Constant.literal_struct([icm__dkueb])
    return kfcdm__rzyxm


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
