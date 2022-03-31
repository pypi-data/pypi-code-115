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
        uazf__jpthw = ArrayItemArrayType(char_arr_type)
        dhsor__pqkoj = [('data', uazf__jpthw)]
        models.StructModel.__init__(self, dmm, fe_type, dhsor__pqkoj)


make_attribute_wrapper(StringArrayType, 'data', '_data')
make_attribute_wrapper(BinaryArrayType, 'data', '_data')
lower_builtin('getiter', string_array_type)(numba.np.arrayobj.getiter_array)


@intrinsic
def init_str_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, ArrayItemArrayType
        ) and data_typ.dtype == types.Array(char_type, 1, 'C')

    def codegen(context, builder, sig, args):
        rqd__uxmdn, = args
        rxocx__zbi = context.make_helper(builder, string_array_type)
        rxocx__zbi.data = rqd__uxmdn
        context.nrt.incref(builder, data_typ, rqd__uxmdn)
        return rxocx__zbi._getvalue()
    return string_array_type(data_typ), codegen


class StringDtype(types.Number):

    def __init__(self):
        super(StringDtype, self).__init__('StringDtype')


string_dtype = StringDtype()
register_model(StringDtype)(models.OpaqueModel)


@box(StringDtype)
def box_string_dtype(typ, val, c):
    yvy__xer = c.context.insert_const_string(c.builder.module, 'pandas')
    nqfbd__nwb = c.pyapi.import_module_noblock(yvy__xer)
    phks__ucsdf = c.pyapi.call_method(nqfbd__nwb, 'StringDtype', ())
    c.pyapi.decref(nqfbd__nwb)
    return phks__ucsdf


@unbox(StringDtype)
def unbox_string_dtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


typeof_impl.register(pd.StringDtype)(lambda a, b: string_dtype)
type_callable(pd.StringDtype)(lambda c: lambda : string_dtype)
lower_builtin(pd.StringDtype)(lambda c, b, s, a: c.get_dummy_value())


def create_binary_op_overload(op):

    def overload_string_array_binary_op(lhs, rhs):
        hdbp__jnhz = bodo.libs.dict_arr_ext.get_binary_op_overload(op, lhs, rhs
            )
        if hdbp__jnhz is not None:
            return hdbp__jnhz
        if is_str_arr_type(lhs) and is_str_arr_type(rhs):

            def impl_both(lhs, rhs):
                numba.parfors.parfor.init_prange()
                wjp__wpah = len(lhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(wjp__wpah)
                for i in numba.parfors.parfor.internal_prange(wjp__wpah):
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
                wjp__wpah = len(lhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(wjp__wpah)
                for i in numba.parfors.parfor.internal_prange(wjp__wpah):
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
                wjp__wpah = len(rhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(wjp__wpah)
                for i in numba.parfors.parfor.internal_prange(wjp__wpah):
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
    lzw__zgozo = is_str_arr_type(lhs) or isinstance(lhs, types.Array
        ) and lhs.dtype == string_type
    lkzg__kvv = is_str_arr_type(rhs) or isinstance(rhs, types.Array
        ) and rhs.dtype == string_type
    if is_str_arr_type(lhs) and lkzg__kvv or lzw__zgozo and is_str_arr_type(rhs
        ):

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
    amxe__iltq = context.make_helper(builder, arr_typ, arr_value)
    uazf__jpthw = ArrayItemArrayType(char_arr_type)
    rtaxe__fyn = _get_array_item_arr_payload(context, builder, uazf__jpthw,
        amxe__iltq.data)
    return rtaxe__fyn


@intrinsic
def num_strings(typingctx, str_arr_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        return rtaxe__fyn.n_arrays
    return types.int64(string_array_type), codegen


def _get_num_total_chars(builder, offsets, num_strings):
    return builder.zext(builder.load(builder.gep(offsets, [num_strings])),
        lir.IntType(64))


@intrinsic
def num_total_chars(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        mbsnb__nrcdv = context.make_helper(builder, offset_arr_type,
            rtaxe__fyn.offsets).data
        return _get_num_total_chars(builder, mbsnb__nrcdv, rtaxe__fyn.n_arrays)
    return types.uint64(in_arr_typ), codegen


@intrinsic
def get_offset_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        dir__ymkt = context.make_helper(builder, offset_arr_type,
            rtaxe__fyn.offsets)
        icddr__qei = context.make_helper(builder, offset_ctypes_type)
        icddr__qei.data = builder.bitcast(dir__ymkt.data, lir.IntType(
            offset_type.bitwidth).as_pointer())
        icddr__qei.meminfo = dir__ymkt.meminfo
        phks__ucsdf = icddr__qei._getvalue()
        return impl_ret_borrowed(context, builder, offset_ctypes_type,
            phks__ucsdf)
    return offset_ctypes_type(in_arr_typ), codegen


@intrinsic
def get_data_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        rqd__uxmdn = context.make_helper(builder, char_arr_type, rtaxe__fyn
            .data)
        icddr__qei = context.make_helper(builder, data_ctypes_type)
        icddr__qei.data = rqd__uxmdn.data
        icddr__qei.meminfo = rqd__uxmdn.meminfo
        phks__ucsdf = icddr__qei._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type,
            phks__ucsdf)
    return data_ctypes_type(in_arr_typ), codegen


@intrinsic
def get_data_ptr_ind(typingctx, in_arr_typ, int_t=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        wjvvk__mry, ind = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            wjvvk__mry, sig.args[0])
        rqd__uxmdn = context.make_helper(builder, char_arr_type, rtaxe__fyn
            .data)
        icddr__qei = context.make_helper(builder, data_ctypes_type)
        icddr__qei.data = builder.gep(rqd__uxmdn.data, [ind])
        icddr__qei.meminfo = rqd__uxmdn.meminfo
        phks__ucsdf = icddr__qei._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type,
            phks__ucsdf)
    return data_ctypes_type(in_arr_typ, types.intp), codegen


@intrinsic
def copy_single_char(typingctx, dst_ptr_t, dst_ind_t, src_ptr_t, src_ind_t=None
    ):

    def codegen(context, builder, sig, args):
        liyqu__tudvx, mckx__ekx, pdyqu__qddk, qijnx__lqseu = args
        fcqip__tbn = builder.bitcast(builder.gep(liyqu__tudvx, [mckx__ekx]),
            lir.IntType(8).as_pointer())
        mzsb__qwyj = builder.bitcast(builder.gep(pdyqu__qddk, [qijnx__lqseu
            ]), lir.IntType(8).as_pointer())
        saoi__jnp = builder.load(mzsb__qwyj)
        builder.store(saoi__jnp, fcqip__tbn)
        return context.get_dummy_value()
    return types.void(types.voidptr, types.intp, types.voidptr, types.intp
        ), codegen


@intrinsic
def get_null_bitmap_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        rfq__mxj = context.make_helper(builder, null_bitmap_arr_type,
            rtaxe__fyn.null_bitmap)
        icddr__qei = context.make_helper(builder, data_ctypes_type)
        icddr__qei.data = rfq__mxj.data
        icddr__qei.meminfo = rfq__mxj.meminfo
        phks__ucsdf = icddr__qei._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type,
            phks__ucsdf)
    return data_ctypes_type(in_arr_typ), codegen


@intrinsic
def getitem_str_offset(typingctx, in_arr_typ, ind_t=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        mbsnb__nrcdv = context.make_helper(builder, offset_arr_type,
            rtaxe__fyn.offsets).data
        return builder.load(builder.gep(mbsnb__nrcdv, [ind]))
    return offset_type(in_arr_typ, ind_t), codegen


@intrinsic
def setitem_str_offset(typingctx, str_arr_typ, ind_t, val_t=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind, val = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        offsets = context.make_helper(builder, offset_arr_type, rtaxe__fyn.
            offsets).data
        builder.store(val, builder.gep(offsets, [ind]))
        return context.get_dummy_value()
    return types.void(string_array_type, ind_t, offset_type), codegen


@intrinsic
def getitem_str_bitmap(typingctx, in_bitmap_typ, ind_t=None):

    def codegen(context, builder, sig, args):
        qorn__onlp, ind = args
        if in_bitmap_typ == data_ctypes_type:
            icddr__qei = context.make_helper(builder, data_ctypes_type,
                qorn__onlp)
            qorn__onlp = icddr__qei.data
        return builder.load(builder.gep(qorn__onlp, [ind]))
    return char_type(in_bitmap_typ, ind_t), codegen


@intrinsic
def setitem_str_bitmap(typingctx, in_bitmap_typ, ind_t, val_t=None):

    def codegen(context, builder, sig, args):
        qorn__onlp, ind, val = args
        if in_bitmap_typ == data_ctypes_type:
            icddr__qei = context.make_helper(builder, data_ctypes_type,
                qorn__onlp)
            qorn__onlp = icddr__qei.data
        builder.store(val, builder.gep(qorn__onlp, [ind]))
        return context.get_dummy_value()
    return types.void(in_bitmap_typ, ind_t, char_type), codegen


@intrinsic
def copy_str_arr_slice(typingctx, out_str_arr_typ, in_str_arr_typ, ind_t=None):
    assert out_str_arr_typ == string_array_type and in_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr, ind = args
        uqrz__ctib = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        bos__epgbk = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        komc__uafq = context.make_helper(builder, offset_arr_type,
            uqrz__ctib.offsets).data
        zwzs__xfip = context.make_helper(builder, offset_arr_type,
            bos__epgbk.offsets).data
        aqglx__gxy = context.make_helper(builder, char_arr_type, uqrz__ctib
            .data).data
        bwxuf__gxq = context.make_helper(builder, char_arr_type, bos__epgbk
            .data).data
        fplyx__pib = context.make_helper(builder, null_bitmap_arr_type,
            uqrz__ctib.null_bitmap).data
        eai__fmtxj = context.make_helper(builder, null_bitmap_arr_type,
            bos__epgbk.null_bitmap).data
        let__tbvh = builder.add(ind, context.get_constant(types.intp, 1))
        cgutils.memcpy(builder, zwzs__xfip, komc__uafq, let__tbvh)
        cgutils.memcpy(builder, bwxuf__gxq, aqglx__gxy, builder.load(
            builder.gep(komc__uafq, [ind])))
        qoo__her = builder.add(ind, lir.Constant(lir.IntType(64), 7))
        kdt__qnn = builder.lshr(qoo__her, lir.Constant(lir.IntType(64), 3))
        cgutils.memcpy(builder, eai__fmtxj, fplyx__pib, kdt__qnn)
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type, ind_t), codegen


@intrinsic
def copy_data(typingctx, str_arr_typ, out_str_arr_typ=None):
    assert str_arr_typ == string_array_type and out_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr = args
        uqrz__ctib = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        bos__epgbk = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        komc__uafq = context.make_helper(builder, offset_arr_type,
            uqrz__ctib.offsets).data
        aqglx__gxy = context.make_helper(builder, char_arr_type, uqrz__ctib
            .data).data
        bwxuf__gxq = context.make_helper(builder, char_arr_type, bos__epgbk
            .data).data
        num_total_chars = _get_num_total_chars(builder, komc__uafq,
            uqrz__ctib.n_arrays)
        cgutils.memcpy(builder, bwxuf__gxq, aqglx__gxy, num_total_chars)
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type), codegen


@intrinsic
def copy_non_null_offsets(typingctx, str_arr_typ, out_str_arr_typ=None):
    assert str_arr_typ == string_array_type and out_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr = args
        uqrz__ctib = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        bos__epgbk = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        komc__uafq = context.make_helper(builder, offset_arr_type,
            uqrz__ctib.offsets).data
        zwzs__xfip = context.make_helper(builder, offset_arr_type,
            bos__epgbk.offsets).data
        fplyx__pib = context.make_helper(builder, null_bitmap_arr_type,
            uqrz__ctib.null_bitmap).data
        wjp__wpah = uqrz__ctib.n_arrays
        fvhqc__tqmnz = context.get_constant(offset_type, 0)
        gwls__tvk = cgutils.alloca_once_value(builder, fvhqc__tqmnz)
        with cgutils.for_range(builder, wjp__wpah) as dcwgr__mjep:
            kxcu__yet = lower_is_na(context, builder, fplyx__pib,
                dcwgr__mjep.index)
            with cgutils.if_likely(builder, builder.not_(kxcu__yet)):
                tkc__svvxv = builder.load(builder.gep(komc__uafq, [
                    dcwgr__mjep.index]))
                hlqf__yis = builder.load(gwls__tvk)
                builder.store(tkc__svvxv, builder.gep(zwzs__xfip, [hlqf__yis]))
                builder.store(builder.add(hlqf__yis, lir.Constant(context.
                    get_value_type(offset_type), 1)), gwls__tvk)
        hlqf__yis = builder.load(gwls__tvk)
        tkc__svvxv = builder.load(builder.gep(komc__uafq, [wjp__wpah]))
        builder.store(tkc__svvxv, builder.gep(zwzs__xfip, [hlqf__yis]))
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type), codegen


@intrinsic
def str_copy(typingctx, buff_arr_typ, ind_typ, str_typ, len_typ=None):

    def codegen(context, builder, sig, args):
        soi__vdv, ind, str, bboti__usq = args
        soi__vdv = context.make_array(sig.args[0])(context, builder, soi__vdv)
        xmi__nvx = builder.gep(soi__vdv.data, [ind])
        cgutils.raw_memcpy(builder, xmi__nvx, str, bboti__usq, 1)
        return context.get_dummy_value()
    return types.void(null_bitmap_arr_type, types.intp, types.voidptr,
        types.intp), codegen


@intrinsic
def str_copy_ptr(typingctx, ptr_typ, ind_typ, str_typ, len_typ=None):

    def codegen(context, builder, sig, args):
        xmi__nvx, ind, zsi__uhfi, bboti__usq = args
        xmi__nvx = builder.gep(xmi__nvx, [ind])
        cgutils.raw_memcpy(builder, xmi__nvx, zsi__uhfi, bboti__usq, 1)
        return context.get_dummy_value()
    return types.void(types.voidptr, types.intp, types.voidptr, types.intp
        ), codegen


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_length(A, i):
    return np.int64(getitem_str_offset(A, i + 1) - getitem_str_offset(A, i))


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_str_length(A, i):
    ggv__mydur = np.int64(getitem_str_offset(A, i))
    xgfw__nwcuh = np.int64(getitem_str_offset(A, i + 1))
    l = xgfw__nwcuh - ggv__mydur
    fyo__vgk = get_data_ptr_ind(A, ggv__mydur)
    for j in range(l):
        if bodo.hiframes.split_impl.getitem_c_arr(fyo__vgk, j) >= 128:
            return len(A[i])
    return l


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_ptr(A, i):
    return get_data_ptr_ind(A, getitem_str_offset(A, i))


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_copy(B, j, A, i):
    if j == 0:
        setitem_str_offset(B, 0, 0)
    dxrl__exq = getitem_str_offset(A, i)
    gdilp__pesui = getitem_str_offset(A, i + 1)
    iyf__nha = gdilp__pesui - dxrl__exq
    vpl__hiyj = getitem_str_offset(B, j)
    yiimv__lgg = vpl__hiyj + iyf__nha
    setitem_str_offset(B, j + 1, yiimv__lgg)
    if str_arr_is_na(A, i):
        str_arr_set_na(B, j)
    else:
        str_arr_set_not_na(B, j)
    if iyf__nha != 0:
        rqd__uxmdn = B._data
        bodo.libs.array_item_arr_ext.ensure_data_capacity(rqd__uxmdn, np.
            int64(vpl__hiyj), np.int64(yiimv__lgg))
        kekil__gnqs = get_data_ptr(B).data
        zmheb__rnhe = get_data_ptr(A).data
        memcpy_region(kekil__gnqs, vpl__hiyj, zmheb__rnhe, dxrl__exq,
            iyf__nha, 1)


@numba.njit(no_cpython_wrapper=True)
def get_str_null_bools(str_arr):
    wjp__wpah = len(str_arr)
    jjbu__mbog = np.empty(wjp__wpah, np.bool_)
    for i in range(wjp__wpah):
        jjbu__mbog[i] = bodo.libs.array_kernels.isna(str_arr, i)
    return jjbu__mbog


def to_list_if_immutable_arr(arr, str_null_bools=None):
    return arr


@overload(to_list_if_immutable_arr, no_unliteral=True)
def to_list_if_immutable_arr_overload(data, str_null_bools=None):
    if is_str_arr_type(data) or data == binary_array_type:

        def to_list_impl(data, str_null_bools=None):
            wjp__wpah = len(data)
            l = []
            for i in range(wjp__wpah):
                l.append(data[i])
            return l
        return to_list_impl
    if isinstance(data, types.BaseTuple):
        ngc__lpka = data.count
        zzj__txo = ['to_list_if_immutable_arr(data[{}])'.format(i) for i in
            range(ngc__lpka)]
        if is_overload_true(str_null_bools):
            zzj__txo += ['get_str_null_bools(data[{}])'.format(i) for i in
                range(ngc__lpka) if is_str_arr_type(data.types[i]) or data.
                types[i] == binary_array_type]
        lij__qmkfq = 'def f(data, str_null_bools=None):\n'
        lij__qmkfq += '  return ({}{})\n'.format(', '.join(zzj__txo), ',' if
            ngc__lpka == 1 else '')
        ehk__udtul = {}
        exec(lij__qmkfq, {'to_list_if_immutable_arr':
            to_list_if_immutable_arr, 'get_str_null_bools':
            get_str_null_bools, 'bodo': bodo}, ehk__udtul)
        pqwzj__skh = ehk__udtul['f']
        return pqwzj__skh
    return lambda data, str_null_bools=None: data


def cp_str_list_to_array(str_arr, str_list, str_null_bools=None):
    return


@overload(cp_str_list_to_array, no_unliteral=True)
def cp_str_list_to_array_overload(str_arr, list_data, str_null_bools=None):
    if str_arr == string_array_type:
        if is_overload_none(str_null_bools):

            def cp_str_list_impl(str_arr, list_data, str_null_bools=None):
                wjp__wpah = len(list_data)
                for i in range(wjp__wpah):
                    zsi__uhfi = list_data[i]
                    str_arr[i] = zsi__uhfi
            return cp_str_list_impl
        else:

            def cp_str_list_impl_null(str_arr, list_data, str_null_bools=None):
                wjp__wpah = len(list_data)
                for i in range(wjp__wpah):
                    zsi__uhfi = list_data[i]
                    str_arr[i] = zsi__uhfi
                    if str_null_bools[i]:
                        str_arr_set_na(str_arr, i)
                    else:
                        str_arr_set_not_na(str_arr, i)
            return cp_str_list_impl_null
    if isinstance(str_arr, types.BaseTuple):
        ngc__lpka = str_arr.count
        uzjj__dnwgz = 0
        lij__qmkfq = 'def f(str_arr, list_data, str_null_bools=None):\n'
        for i in range(ngc__lpka):
            if is_overload_true(str_null_bools) and str_arr.types[i
                ] == string_array_type:
                lij__qmkfq += (
                    '  cp_str_list_to_array(str_arr[{}], list_data[{}], list_data[{}])\n'
                    .format(i, i, ngc__lpka + uzjj__dnwgz))
                uzjj__dnwgz += 1
            else:
                lij__qmkfq += (
                    '  cp_str_list_to_array(str_arr[{}], list_data[{}])\n'.
                    format(i, i))
        lij__qmkfq += '  return\n'
        ehk__udtul = {}
        exec(lij__qmkfq, {'cp_str_list_to_array': cp_str_list_to_array},
            ehk__udtul)
        saw__hmim = ehk__udtul['f']
        return saw__hmim
    return lambda str_arr, list_data, str_null_bools=None: None


def str_list_to_array(str_list):
    return str_list


@overload(str_list_to_array, no_unliteral=True)
def str_list_to_array_overload(str_list):
    if isinstance(str_list, types.List) and str_list.dtype == bodo.string_type:

        def str_list_impl(str_list):
            wjp__wpah = len(str_list)
            str_arr = pre_alloc_string_array(wjp__wpah, -1)
            for i in range(wjp__wpah):
                zsi__uhfi = str_list[i]
                str_arr[i] = zsi__uhfi
            return str_arr
        return str_list_impl
    return lambda str_list: str_list


def get_num_total_chars(A):
    pass


@overload(get_num_total_chars)
def overload_get_num_total_chars(A):
    if isinstance(A, types.List) and A.dtype == string_type:

        def str_list_impl(A):
            wjp__wpah = len(A)
            qdovb__ligxv = 0
            for i in range(wjp__wpah):
                zsi__uhfi = A[i]
                qdovb__ligxv += get_utf8_size(zsi__uhfi)
            return qdovb__ligxv
        return str_list_impl
    assert A == string_array_type
    return lambda A: num_total_chars(A)


@overload_method(StringArrayType, 'copy', no_unliteral=True)
def str_arr_copy_overload(arr):

    def copy_impl(arr):
        wjp__wpah = len(arr)
        n_chars = num_total_chars(arr)
        hppi__vybei = pre_alloc_string_array(wjp__wpah, np.int64(n_chars))
        copy_str_arr_slice(hppi__vybei, arr, wjp__wpah)
        return hppi__vybei
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
    lij__qmkfq = 'def f(in_seq):\n'
    lij__qmkfq += '    n_strs = len(in_seq)\n'
    lij__qmkfq += '    A = pre_alloc_string_array(n_strs, -1)\n'
    lij__qmkfq += '    return A\n'
    ehk__udtul = {}
    exec(lij__qmkfq, {'pre_alloc_string_array': pre_alloc_string_array},
        ehk__udtul)
    kvir__qgeex = ehk__udtul['f']
    return kvir__qgeex


@numba.generated_jit(nopython=True)
def str_arr_from_sequence(in_seq):
    if in_seq.dtype == bodo.bytes_type:
        flo__aas = 'pre_alloc_binary_array'
    else:
        flo__aas = 'pre_alloc_string_array'
    lij__qmkfq = 'def f(in_seq):\n'
    lij__qmkfq += '    n_strs = len(in_seq)\n'
    lij__qmkfq += f'    A = {flo__aas}(n_strs, -1)\n'
    lij__qmkfq += '    for i in range(n_strs):\n'
    lij__qmkfq += '        A[i] = in_seq[i]\n'
    lij__qmkfq += '    return A\n'
    ehk__udtul = {}
    exec(lij__qmkfq, {'pre_alloc_string_array': pre_alloc_string_array,
        'pre_alloc_binary_array': pre_alloc_binary_array}, ehk__udtul)
    kvir__qgeex = ehk__udtul['f']
    return kvir__qgeex


@intrinsic
def set_all_offsets_to_0(typingctx, arr_typ=None):
    assert arr_typ in (string_array_type, binary_array_type
        ), 'set_all_offsets_to_0 requires a string or binary array'

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        ytlah__gel = builder.add(rtaxe__fyn.n_arrays, lir.Constant(lir.
            IntType(64), 1))
        vgex__xlqv = builder.lshr(lir.Constant(lir.IntType(64), offset_type
            .bitwidth), lir.Constant(lir.IntType(64), 3))
        kdt__qnn = builder.mul(ytlah__gel, vgex__xlqv)
        mldhi__zmi = context.make_array(offset_arr_type)(context, builder,
            rtaxe__fyn.offsets).data
        cgutils.memset(builder, mldhi__zmi, kdt__qnn, 0)
        return context.get_dummy_value()
    return types.none(arr_typ), codegen


@intrinsic
def set_bitmap_all_NA(typingctx, arr_typ=None):
    assert arr_typ in (string_array_type, binary_array_type
        ), 'set_bitmap_all_NA requires a string or binary array'

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        fxnu__gbhyj = rtaxe__fyn.n_arrays
        kdt__qnn = builder.lshr(builder.add(fxnu__gbhyj, lir.Constant(lir.
            IntType(64), 7)), lir.Constant(lir.IntType(64), 3))
        kly__bxxws = context.make_array(null_bitmap_arr_type)(context,
            builder, rtaxe__fyn.null_bitmap).data
        cgutils.memset(builder, kly__bxxws, kdt__qnn, 0)
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
    pncy__yzogp = 0
    if total_len == 0:
        for i in range(len(offsets)):
            offsets[i] = 0
    else:
        rvrmn__ptd = len(len_arr)
        for i in range(rvrmn__ptd):
            offsets[i] = pncy__yzogp
            pncy__yzogp += len_arr[i]
        offsets[rvrmn__ptd] = pncy__yzogp
    return str_arr


kBitmask = np.array([1, 2, 4, 8, 16, 32, 64, 128], dtype=np.uint8)


@numba.njit
def set_bit_to(bits, i, bit_is_set):
    tav__ocs = i // 8
    eex__ladt = getitem_str_bitmap(bits, tav__ocs)
    eex__ladt ^= np.uint8(-np.uint8(bit_is_set) ^ eex__ladt) & kBitmask[i % 8]
    setitem_str_bitmap(bits, tav__ocs, eex__ladt)


@numba.njit
def get_bit_bitmap(bits, i):
    return getitem_str_bitmap(bits, i >> 3) >> (i & 7) & 1


@numba.njit
def copy_nulls_range(out_str_arr, in_str_arr, out_start):
    orh__scmcn = get_null_bitmap_ptr(out_str_arr)
    utxbi__qitnv = get_null_bitmap_ptr(in_str_arr)
    for j in range(len(in_str_arr)):
        hfk__wqr = get_bit_bitmap(utxbi__qitnv, j)
        set_bit_to(orh__scmcn, out_start + j, hfk__wqr)


@intrinsic
def set_string_array_range(typingctx, out_typ, in_typ, curr_str_typ,
    curr_chars_typ=None):
    assert out_typ == string_array_type and in_typ == string_array_type or out_typ == binary_array_type and in_typ == binary_array_type, 'set_string_array_range requires string or binary arrays'
    assert isinstance(curr_str_typ, types.Integer) and isinstance(
        curr_chars_typ, types.Integer
        ), 'set_string_array_range requires integer indices'

    def codegen(context, builder, sig, args):
        out_arr, wjvvk__mry, ppj__peadb, wcg__fcje = args
        uqrz__ctib = _get_str_binary_arr_payload(context, builder,
            wjvvk__mry, string_array_type)
        bos__epgbk = _get_str_binary_arr_payload(context, builder, out_arr,
            string_array_type)
        komc__uafq = context.make_helper(builder, offset_arr_type,
            uqrz__ctib.offsets).data
        zwzs__xfip = context.make_helper(builder, offset_arr_type,
            bos__epgbk.offsets).data
        aqglx__gxy = context.make_helper(builder, char_arr_type, uqrz__ctib
            .data).data
        bwxuf__gxq = context.make_helper(builder, char_arr_type, bos__epgbk
            .data).data
        num_total_chars = _get_num_total_chars(builder, komc__uafq,
            uqrz__ctib.n_arrays)
        qkh__zklkg = lir.FunctionType(lir.VoidType(), [lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(64), lir.IntType(64), lir.IntType(64),
            lir.IntType(64)])
        ric__camll = cgutils.get_or_insert_function(builder.module,
            qkh__zklkg, name='set_string_array_range')
        builder.call(ric__camll, [zwzs__xfip, bwxuf__gxq, komc__uafq,
            aqglx__gxy, ppj__peadb, wcg__fcje, uqrz__ctib.n_arrays,
            num_total_chars])
        ztmwi__nfmnr = context.typing_context.resolve_value_type(
            copy_nulls_range)
        hoh__yat = ztmwi__nfmnr.get_call_type(context.typing_context, (
            string_array_type, string_array_type, types.int64), {})
        dlcp__smoho = context.get_function(ztmwi__nfmnr, hoh__yat)
        dlcp__smoho(builder, (out_arr, wjvvk__mry, ppj__peadb))
        return context.get_dummy_value()
    sig = types.void(out_typ, in_typ, types.intp, types.intp)
    return sig, codegen


@box(BinaryArrayType)
@box(StringArrayType)
def box_str_arr(typ, val, c):
    assert typ in [binary_array_type, string_array_type]
    gtgqi__ghqg = c.context.make_helper(c.builder, typ, val)
    uazf__jpthw = ArrayItemArrayType(char_arr_type)
    rtaxe__fyn = _get_array_item_arr_payload(c.context, c.builder,
        uazf__jpthw, gtgqi__ghqg.data)
    awi__elvi = c.context.get_constant(types.int32, int(typ ==
        binary_array_type))
    vmmor__wdvi = 'np_array_from_string_array'
    if use_pd_string_array and typ != binary_array_type:
        vmmor__wdvi = 'pd_array_from_string_array'
    qkh__zklkg = lir.FunctionType(c.context.get_argument_type(types.
        pyobject), [lir.IntType(64), lir.IntType(offset_type.bitwidth).
        as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
        as_pointer(), lir.IntType(32)])
    buxdy__yml = cgutils.get_or_insert_function(c.builder.module,
        qkh__zklkg, name=vmmor__wdvi)
    mbsnb__nrcdv = c.context.make_array(offset_arr_type)(c.context, c.
        builder, rtaxe__fyn.offsets).data
    fyo__vgk = c.context.make_array(char_arr_type)(c.context, c.builder,
        rtaxe__fyn.data).data
    kly__bxxws = c.context.make_array(null_bitmap_arr_type)(c.context, c.
        builder, rtaxe__fyn.null_bitmap).data
    arr = c.builder.call(buxdy__yml, [rtaxe__fyn.n_arrays, mbsnb__nrcdv,
        fyo__vgk, kly__bxxws, awi__elvi])
    c.context.nrt.decref(c.builder, typ, val)
    return arr


@intrinsic
def str_arr_is_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        kly__bxxws = context.make_array(null_bitmap_arr_type)(context,
            builder, rtaxe__fyn.null_bitmap).data
        rlkk__bqj = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        gyz__cpdhn = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        eex__ladt = builder.load(builder.gep(kly__bxxws, [rlkk__bqj],
            inbounds=True))
        ajwzj__fhnox = lir.ArrayType(lir.IntType(8), 8)
        xnpke__yibbb = cgutils.alloca_once_value(builder, lir.Constant(
            ajwzj__fhnox, (1, 2, 4, 8, 16, 32, 64, 128)))
        lov__szaiz = builder.load(builder.gep(xnpke__yibbb, [lir.Constant(
            lir.IntType(64), 0), gyz__cpdhn], inbounds=True))
        return builder.icmp_unsigned('==', builder.and_(eex__ladt,
            lov__szaiz), lir.Constant(lir.IntType(8), 0))
    return types.bool_(str_arr_typ, types.intp), codegen


@intrinsic
def str_arr_set_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        rlkk__bqj = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        gyz__cpdhn = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        kly__bxxws = context.make_array(null_bitmap_arr_type)(context,
            builder, rtaxe__fyn.null_bitmap).data
        offsets = context.make_helper(builder, offset_arr_type, rtaxe__fyn.
            offsets).data
        chqm__pdf = builder.gep(kly__bxxws, [rlkk__bqj], inbounds=True)
        eex__ladt = builder.load(chqm__pdf)
        ajwzj__fhnox = lir.ArrayType(lir.IntType(8), 8)
        xnpke__yibbb = cgutils.alloca_once_value(builder, lir.Constant(
            ajwzj__fhnox, (1, 2, 4, 8, 16, 32, 64, 128)))
        lov__szaiz = builder.load(builder.gep(xnpke__yibbb, [lir.Constant(
            lir.IntType(64), 0), gyz__cpdhn], inbounds=True))
        lov__szaiz = builder.xor(lov__szaiz, lir.Constant(lir.IntType(8), -1))
        builder.store(builder.and_(eex__ladt, lov__szaiz), chqm__pdf)
        if str_arr_typ == string_array_type:
            xfgkd__iowfu = builder.add(ind, lir.Constant(lir.IntType(64), 1))
            ozlxc__kfk = builder.icmp_unsigned('!=', xfgkd__iowfu,
                rtaxe__fyn.n_arrays)
            with builder.if_then(ozlxc__kfk):
                builder.store(builder.load(builder.gep(offsets, [ind])),
                    builder.gep(offsets, [xfgkd__iowfu]))
        return context.get_dummy_value()
    return types.void(str_arr_typ, types.intp), codegen


@intrinsic
def str_arr_set_not_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        rlkk__bqj = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        gyz__cpdhn = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        kly__bxxws = context.make_array(null_bitmap_arr_type)(context,
            builder, rtaxe__fyn.null_bitmap).data
        chqm__pdf = builder.gep(kly__bxxws, [rlkk__bqj], inbounds=True)
        eex__ladt = builder.load(chqm__pdf)
        ajwzj__fhnox = lir.ArrayType(lir.IntType(8), 8)
        xnpke__yibbb = cgutils.alloca_once_value(builder, lir.Constant(
            ajwzj__fhnox, (1, 2, 4, 8, 16, 32, 64, 128)))
        lov__szaiz = builder.load(builder.gep(xnpke__yibbb, [lir.Constant(
            lir.IntType(64), 0), gyz__cpdhn], inbounds=True))
        builder.store(builder.or_(eex__ladt, lov__szaiz), chqm__pdf)
        return context.get_dummy_value()
    return types.void(str_arr_typ, types.intp), codegen


@intrinsic
def set_null_bits_to_value(typingctx, arr_typ, value_typ=None):
    assert (arr_typ == string_array_type or arr_typ == binary_array_type
        ) and is_overload_constant_int(value_typ)

    def codegen(context, builder, sig, args):
        in_str_arr, value = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        kdt__qnn = builder.udiv(builder.add(rtaxe__fyn.n_arrays, lir.
            Constant(lir.IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
        kly__bxxws = context.make_array(null_bitmap_arr_type)(context,
            builder, rtaxe__fyn.null_bitmap).data
        cgutils.memset(builder, kly__bxxws, kdt__qnn, value)
        return context.get_dummy_value()
    return types.none(arr_typ, types.int8), codegen


def _get_str_binary_arr_data_payload_ptr(context, builder, str_arr):
    xslu__ktogm = context.make_helper(builder, string_array_type, str_arr)
    uazf__jpthw = ArrayItemArrayType(char_arr_type)
    frt__eclq = context.make_helper(builder, uazf__jpthw, xslu__ktogm.data)
    dpw__erxb = ArrayItemArrayPayloadType(uazf__jpthw)
    gvn__giz = context.nrt.meminfo_data(builder, frt__eclq.meminfo)
    eqrlt__zae = builder.bitcast(gvn__giz, context.get_value_type(dpw__erxb
        ).as_pointer())
    return eqrlt__zae


@intrinsic
def move_str_binary_arr_payload(typingctx, to_arr_typ, from_arr_typ=None):
    assert to_arr_typ == string_array_type and from_arr_typ == string_array_type or to_arr_typ == binary_array_type and from_arr_typ == binary_array_type

    def codegen(context, builder, sig, args):
        pamqm__ozym, qtwv__iun = args
        vbtk__wwi = _get_str_binary_arr_data_payload_ptr(context, builder,
            qtwv__iun)
        ycaq__wenwe = _get_str_binary_arr_data_payload_ptr(context, builder,
            pamqm__ozym)
        pktb__smixl = _get_str_binary_arr_payload(context, builder,
            qtwv__iun, sig.args[1])
        tph__jfenn = _get_str_binary_arr_payload(context, builder,
            pamqm__ozym, sig.args[0])
        context.nrt.incref(builder, char_arr_type, pktb__smixl.data)
        context.nrt.incref(builder, offset_arr_type, pktb__smixl.offsets)
        context.nrt.incref(builder, null_bitmap_arr_type, pktb__smixl.
            null_bitmap)
        context.nrt.decref(builder, char_arr_type, tph__jfenn.data)
        context.nrt.decref(builder, offset_arr_type, tph__jfenn.offsets)
        context.nrt.decref(builder, null_bitmap_arr_type, tph__jfenn.
            null_bitmap)
        builder.store(builder.load(vbtk__wwi), ycaq__wenwe)
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
        wjp__wpah = _get_utf8_size(s._data, s._length, s._kind)
        dummy_use(s)
        return wjp__wpah
    return impl


@intrinsic
def setitem_str_arr_ptr(typingctx, str_arr_t, ind_t, ptr_t, len_t=None):

    def codegen(context, builder, sig, args):
        arr, ind, xmi__nvx, spw__ftgmz = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder, arr, sig
            .args[0])
        offsets = context.make_helper(builder, offset_arr_type, rtaxe__fyn.
            offsets).data
        data = context.make_helper(builder, char_arr_type, rtaxe__fyn.data
            ).data
        qkh__zklkg = lir.FunctionType(lir.VoidType(), [lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(64),
            lir.IntType(32), lir.IntType(32), lir.IntType(64)])
        ckyx__emk = cgutils.get_or_insert_function(builder.module,
            qkh__zklkg, name='setitem_string_array')
        suvg__lbizn = context.get_constant(types.int32, -1)
        qhdg__gqfoo = context.get_constant(types.int32, 1)
        num_total_chars = _get_num_total_chars(builder, offsets, rtaxe__fyn
            .n_arrays)
        builder.call(ckyx__emk, [offsets, data, num_total_chars, builder.
            extract_value(xmi__nvx, 0), spw__ftgmz, suvg__lbizn,
            qhdg__gqfoo, ind])
        return context.get_dummy_value()
    return types.void(str_arr_t, ind_t, ptr_t, len_t), codegen


def lower_is_na(context, builder, bull_bitmap, ind):
    qkh__zklkg = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
        as_pointer(), lir.IntType(64)])
    oqmk__uqo = cgutils.get_or_insert_function(builder.module, qkh__zklkg,
        name='is_na')
    return builder.call(oqmk__uqo, [bull_bitmap, ind])


@intrinsic
def _memcpy(typingctx, dest_t, src_t, count_t, item_size_t=None):

    def codegen(context, builder, sig, args):
        fcqip__tbn, mzsb__qwyj, ngc__lpka, kzl__emcb = args
        cgutils.raw_memcpy(builder, fcqip__tbn, mzsb__qwyj, ngc__lpka,
            kzl__emcb)
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
        zcjbi__seknz, rkif__qlkv = unicode_to_utf8_and_len(val)
        wqx__fic = getitem_str_offset(A, ind)
        epar__wupoq = getitem_str_offset(A, ind + 1)
        cxauc__hgwhv = epar__wupoq - wqx__fic
        if cxauc__hgwhv != rkif__qlkv:
            return False
        xmi__nvx = get_data_ptr_ind(A, wqx__fic)
        return memcmp(xmi__nvx, zcjbi__seknz, rkif__qlkv) == 0
    return impl


def str_arr_setitem_int_to_str(A, ind, value):
    A[ind] = str(value)


@overload(str_arr_setitem_int_to_str)
def overload_str_arr_setitem_int_to_str(A, ind, val):

    def impl(A, ind, val):
        wqx__fic = getitem_str_offset(A, ind)
        cxauc__hgwhv = bodo.libs.str_ext.int_to_str_len(val)
        ylgj__vuw = wqx__fic + cxauc__hgwhv
        bodo.libs.array_item_arr_ext.ensure_data_capacity(A._data, wqx__fic,
            ylgj__vuw)
        xmi__nvx = get_data_ptr_ind(A, wqx__fic)
        inplace_int64_to_str(xmi__nvx, cxauc__hgwhv, val)
        setitem_str_offset(A, ind + 1, wqx__fic + cxauc__hgwhv)
        str_arr_set_not_na(A, ind)
    return impl


@intrinsic
def inplace_set_NA_str(typingctx, ptr_typ=None):

    def codegen(context, builder, sig, args):
        xmi__nvx, = args
        obgxe__mffso = context.insert_const_string(builder.module, '<NA>')
        jxfcz__eyiy = lir.Constant(lir.IntType(64), len('<NA>'))
        cgutils.raw_memcpy(builder, xmi__nvx, obgxe__mffso, jxfcz__eyiy, 1)
    return types.none(types.voidptr), codegen


def str_arr_setitem_NA_str(A, ind):
    A[ind] = '<NA>'


@overload(str_arr_setitem_NA_str)
def overload_str_arr_setitem_NA_str(A, ind):
    ptvah__gmia = len('<NA>')

    def impl(A, ind):
        wqx__fic = getitem_str_offset(A, ind)
        ylgj__vuw = wqx__fic + ptvah__gmia
        bodo.libs.array_item_arr_ext.ensure_data_capacity(A._data, wqx__fic,
            ylgj__vuw)
        xmi__nvx = get_data_ptr_ind(A, wqx__fic)
        inplace_set_NA_str(xmi__nvx)
        setitem_str_offset(A, ind + 1, wqx__fic + ptvah__gmia)
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
            wqx__fic = getitem_str_offset(A, ind)
            epar__wupoq = getitem_str_offset(A, ind + 1)
            spw__ftgmz = epar__wupoq - wqx__fic
            xmi__nvx = get_data_ptr_ind(A, wqx__fic)
            xyme__pmom = decode_utf8(xmi__nvx, spw__ftgmz)
            return xyme__pmom
        return str_arr_getitem_impl
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:

        def bool_impl(A, ind):
            ind = bodo.utils.conversion.coerce_to_ndarray(ind)
            wjp__wpah = len(A)
            n_strs = 0
            n_chars = 0
            for i in range(wjp__wpah):
                if not bodo.libs.array_kernels.isna(ind, i) and ind[i]:
                    n_strs += 1
                    n_chars += get_str_arr_item_length(A, i)
            out_arr = pre_alloc_string_array(n_strs, n_chars)
            kekil__gnqs = get_data_ptr(out_arr).data
            zmheb__rnhe = get_data_ptr(A).data
            uzjj__dnwgz = 0
            hlqf__yis = 0
            setitem_str_offset(out_arr, 0, 0)
            for i in range(wjp__wpah):
                if not bodo.libs.array_kernels.isna(ind, i) and ind[i]:
                    ogwso__vnzp = get_str_arr_item_length(A, i)
                    if ogwso__vnzp == 1:
                        copy_single_char(kekil__gnqs, hlqf__yis,
                            zmheb__rnhe, getitem_str_offset(A, i))
                    else:
                        memcpy_region(kekil__gnqs, hlqf__yis, zmheb__rnhe,
                            getitem_str_offset(A, i), ogwso__vnzp, 1)
                    hlqf__yis += ogwso__vnzp
                    setitem_str_offset(out_arr, uzjj__dnwgz + 1, hlqf__yis)
                    if str_arr_is_na(A, i):
                        str_arr_set_na(out_arr, uzjj__dnwgz)
                    else:
                        str_arr_set_not_na(out_arr, uzjj__dnwgz)
                    uzjj__dnwgz += 1
            return out_arr
        return bool_impl
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def str_arr_arr_impl(A, ind):
            wjp__wpah = len(ind)
            out_arr = pre_alloc_string_array(wjp__wpah, -1)
            uzjj__dnwgz = 0
            for i in range(wjp__wpah):
                zsi__uhfi = A[ind[i]]
                out_arr[uzjj__dnwgz] = zsi__uhfi
                if str_arr_is_na(A, ind[i]):
                    str_arr_set_na(out_arr, uzjj__dnwgz)
                uzjj__dnwgz += 1
            return out_arr
        return str_arr_arr_impl
    if isinstance(ind, types.SliceType):

        def str_arr_slice_impl(A, ind):
            wjp__wpah = len(A)
            adt__rhit = numba.cpython.unicode._normalize_slice(ind, wjp__wpah)
            qzaro__fao = numba.cpython.unicode._slice_span(adt__rhit)
            if adt__rhit.step == 1:
                wqx__fic = getitem_str_offset(A, adt__rhit.start)
                epar__wupoq = getitem_str_offset(A, adt__rhit.stop)
                n_chars = epar__wupoq - wqx__fic
                hppi__vybei = pre_alloc_string_array(qzaro__fao, np.int64(
                    n_chars))
                for i in range(qzaro__fao):
                    hppi__vybei[i] = A[adt__rhit.start + i]
                    if str_arr_is_na(A, adt__rhit.start + i):
                        str_arr_set_na(hppi__vybei, i)
                return hppi__vybei
            else:
                hppi__vybei = pre_alloc_string_array(qzaro__fao, -1)
                for i in range(qzaro__fao):
                    hppi__vybei[i] = A[adt__rhit.start + i * adt__rhit.step]
                    if str_arr_is_na(A, adt__rhit.start + i * adt__rhit.step):
                        str_arr_set_na(hppi__vybei, i)
                return hppi__vybei
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
    zfxaf__qhpzb = (
        f'StringArray setitem with index {idx} and value {val} not supported yet.'
        )
    if isinstance(idx, types.Integer):
        if val != string_type:
            raise BodoError(zfxaf__qhpzb)
        zpx__ahcv = 4

        def impl_scalar(A, idx, val):
            hximj__ica = (val._length if val._is_ascii else zpx__ahcv * val
                ._length)
            rqd__uxmdn = A._data
            wqx__fic = np.int64(getitem_str_offset(A, idx))
            ylgj__vuw = wqx__fic + hximj__ica
            bodo.libs.array_item_arr_ext.ensure_data_capacity(rqd__uxmdn,
                wqx__fic, ylgj__vuw)
            setitem_string_array(get_offset_ptr(A), get_data_ptr(A),
                ylgj__vuw, val._data, val._length, val._kind, val._is_ascii,
                idx)
            str_arr_set_not_na(A, idx)
            dummy_use(A)
            dummy_use(val)
        return impl_scalar
    if isinstance(idx, types.SliceType):
        if val == string_array_type:

            def impl_slice(A, idx, val):
                adt__rhit = numba.cpython.unicode._normalize_slice(idx, len(A))
                ggv__mydur = adt__rhit.start
                rqd__uxmdn = A._data
                wqx__fic = np.int64(getitem_str_offset(A, ggv__mydur))
                ylgj__vuw = wqx__fic + np.int64(num_total_chars(val))
                bodo.libs.array_item_arr_ext.ensure_data_capacity(rqd__uxmdn,
                    wqx__fic, ylgj__vuw)
                set_string_array_range(A, val, ggv__mydur, wqx__fic)
                gvlh__hzzr = 0
                for i in range(adt__rhit.start, adt__rhit.stop, adt__rhit.step
                    ):
                    if str_arr_is_na(val, gvlh__hzzr):
                        str_arr_set_na(A, i)
                    else:
                        str_arr_set_not_na(A, i)
                    gvlh__hzzr += 1
            return impl_slice
        elif isinstance(val, types.List) and val.dtype == string_type:

            def impl_slice_list(A, idx, val):
                lad__mvt = str_list_to_array(val)
                A[idx] = lad__mvt
            return impl_slice_list
        elif val == string_type:

            def impl_slice(A, idx, val):
                adt__rhit = numba.cpython.unicode._normalize_slice(idx, len(A))
                for i in range(adt__rhit.start, adt__rhit.stop, adt__rhit.step
                    ):
                    A[i] = val
            return impl_slice
        else:
            raise BodoError(zfxaf__qhpzb)
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        if val == string_type:

            def impl_bool_scalar(A, idx, val):
                wjp__wpah = len(A)
                idx = bodo.utils.conversion.coerce_to_ndarray(idx)
                out_arr = pre_alloc_string_array(wjp__wpah, -1)
                for i in numba.parfors.parfor.internal_prange(wjp__wpah):
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
                wjp__wpah = len(A)
                idx = bodo.utils.conversion.coerce_to_array(idx,
                    use_nullable_array=True)
                out_arr = pre_alloc_string_array(wjp__wpah, -1)
                ysbn__rzv = 0
                for i in numba.parfors.parfor.internal_prange(wjp__wpah):
                    if not bodo.libs.array_kernels.isna(idx, i) and idx[i]:
                        if bodo.libs.array_kernels.isna(val, ysbn__rzv):
                            out_arr[i] = ''
                            str_arr_set_na(out_arr, ysbn__rzv)
                        else:
                            out_arr[i] = str(val[ysbn__rzv])
                        ysbn__rzv += 1
                    elif bodo.libs.array_kernels.isna(A, i):
                        out_arr[i] = ''
                        str_arr_set_na(out_arr, i)
                    else:
                        get_str_arr_item_copy(out_arr, i, A, i)
                move_str_binary_arr_payload(A, out_arr)
            return impl_bool_arr
        else:
            raise BodoError(zfxaf__qhpzb)
    raise BodoError(zfxaf__qhpzb)


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
    qdc__fga = parse_dtype(dtype, 'StringArray.astype')
    if not isinstance(qdc__fga, (types.Float, types.Integer)):
        raise BodoError('invalid dtype in StringArray.astype()')
    if isinstance(qdc__fga, types.Float):

        def impl_float(A, dtype, copy=True):
            numba.parfors.parfor.init_prange()
            wjp__wpah = len(A)
            B = np.empty(wjp__wpah, qdc__fga)
            for i in numba.parfors.parfor.internal_prange(wjp__wpah):
                if bodo.libs.array_kernels.isna(A, i):
                    B[i] = np.nan
                else:
                    B[i] = float(A[i])
            return B
        return impl_float
    else:

        def impl_int(A, dtype, copy=True):
            numba.parfors.parfor.init_prange()
            wjp__wpah = len(A)
            B = np.empty(wjp__wpah, qdc__fga)
            for i in numba.parfors.parfor.internal_prange(wjp__wpah):
                B[i] = int(A[i])
            return B
        return impl_int


@intrinsic
def decode_utf8(typingctx, ptr_t, len_t=None):

    def codegen(context, builder, sig, args):
        xmi__nvx, spw__ftgmz = args
        kxzb__suk = context.get_python_api(builder)
        pmk__yrjb = kxzb__suk.string_from_string_and_size(xmi__nvx, spw__ftgmz)
        grll__jet = kxzb__suk.to_native_value(string_type, pmk__yrjb).value
        poz__otxw = cgutils.create_struct_proxy(string_type)(context,
            builder, grll__jet)
        poz__otxw.hash = poz__otxw.hash.type(-1)
        kxzb__suk.decref(pmk__yrjb)
        return poz__otxw._getvalue()
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
        dvn__mfs, arr, ind, bqu__rxdu = args
        rtaxe__fyn = _get_str_binary_arr_payload(context, builder, arr,
            string_array_type)
        offsets = context.make_helper(builder, offset_arr_type, rtaxe__fyn.
            offsets).data
        data = context.make_helper(builder, char_arr_type, rtaxe__fyn.data
            ).data
        qkh__zklkg = lir.FunctionType(lir.IntType(32), [dvn__mfs.type, lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(64)])
        zvy__qtx = 'str_arr_to_int64'
        if sig.args[3].dtype == types.float64:
            zvy__qtx = 'str_arr_to_float64'
        else:
            assert sig.args[3].dtype == types.int64
        jabo__zhj = cgutils.get_or_insert_function(builder.module,
            qkh__zklkg, zvy__qtx)
        return builder.call(jabo__zhj, [dvn__mfs, offsets, data, ind])
    return types.int32(out_ptr_t, string_array_type, types.int64, out_dtype_t
        ), codegen


@unbox(BinaryArrayType)
@unbox(StringArrayType)
def unbox_str_series(typ, val, c):
    awi__elvi = c.context.get_constant(types.int32, int(typ ==
        binary_array_type))
    qkh__zklkg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.IntType
        (8).as_pointer(), lir.IntType(32)])
    obhbl__oxis = cgutils.get_or_insert_function(c.builder.module,
        qkh__zklkg, name='string_array_from_sequence')
    axrs__rigc = c.builder.call(obhbl__oxis, [val, awi__elvi])
    uazf__jpthw = ArrayItemArrayType(char_arr_type)
    frt__eclq = c.context.make_helper(c.builder, uazf__jpthw)
    frt__eclq.meminfo = axrs__rigc
    xslu__ktogm = c.context.make_helper(c.builder, typ)
    rqd__uxmdn = frt__eclq._getvalue()
    xslu__ktogm.data = rqd__uxmdn
    pquim__ngwzb = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(xslu__ktogm._getvalue(), is_error=pquim__ngwzb)


@lower_constant(BinaryArrayType)
@lower_constant(StringArrayType)
def lower_constant_str_arr(context, builder, typ, pyval):
    wjp__wpah = len(pyval)
    hlqf__yis = 0
    xbmk__spwd = np.empty(wjp__wpah + 1, np_offset_type)
    cdi__oka = []
    egh__rop = np.empty(wjp__wpah + 7 >> 3, np.uint8)
    for i, s in enumerate(pyval):
        xbmk__spwd[i] = hlqf__yis
        lubai__tnkh = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(egh__rop, i, int(not lubai__tnkh))
        if lubai__tnkh:
            continue
        mdxgu__mdm = list(s.encode()) if isinstance(s, str) else list(s)
        cdi__oka.extend(mdxgu__mdm)
        hlqf__yis += len(mdxgu__mdm)
    xbmk__spwd[wjp__wpah] = hlqf__yis
    gxcbk__ngodw = np.array(cdi__oka, np.uint8)
    pxoxm__tilm = context.get_constant(types.int64, wjp__wpah)
    ank__gigb = context.get_constant_generic(builder, char_arr_type,
        gxcbk__ngodw)
    sruxf__tffo = context.get_constant_generic(builder, offset_arr_type,
        xbmk__spwd)
    etgkf__orziz = context.get_constant_generic(builder,
        null_bitmap_arr_type, egh__rop)
    rtaxe__fyn = lir.Constant.literal_struct([pxoxm__tilm, ank__gigb,
        sruxf__tffo, etgkf__orziz])
    rtaxe__fyn = cgutils.global_constant(builder, '.const.payload', rtaxe__fyn
        ).bitcast(cgutils.voidptr_t)
    bkzcn__vdba = context.get_constant(types.int64, -1)
    zjwq__tes = context.get_constant_null(types.voidptr)
    itf__iagyd = lir.Constant.literal_struct([bkzcn__vdba, zjwq__tes,
        zjwq__tes, rtaxe__fyn, bkzcn__vdba])
    itf__iagyd = cgutils.global_constant(builder, '.const.meminfo', itf__iagyd
        ).bitcast(cgutils.voidptr_t)
    rqd__uxmdn = lir.Constant.literal_struct([itf__iagyd])
    xslu__ktogm = lir.Constant.literal_struct([rqd__uxmdn])
    return xslu__ktogm


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
