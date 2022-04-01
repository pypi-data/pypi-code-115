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
        xuu__szbt = ArrayItemArrayType(char_arr_type)
        ezuz__qeu = [('data', xuu__szbt)]
        models.StructModel.__init__(self, dmm, fe_type, ezuz__qeu)


make_attribute_wrapper(StringArrayType, 'data', '_data')
make_attribute_wrapper(BinaryArrayType, 'data', '_data')
lower_builtin('getiter', string_array_type)(numba.np.arrayobj.getiter_array)


@intrinsic
def init_str_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, ArrayItemArrayType
        ) and data_typ.dtype == types.Array(char_type, 1, 'C')

    def codegen(context, builder, sig, args):
        eptr__yzj, = args
        mzwtq__rxfmj = context.make_helper(builder, string_array_type)
        mzwtq__rxfmj.data = eptr__yzj
        context.nrt.incref(builder, data_typ, eptr__yzj)
        return mzwtq__rxfmj._getvalue()
    return string_array_type(data_typ), codegen


class StringDtype(types.Number):

    def __init__(self):
        super(StringDtype, self).__init__('StringDtype')


string_dtype = StringDtype()
register_model(StringDtype)(models.OpaqueModel)


@box(StringDtype)
def box_string_dtype(typ, val, c):
    tpmmn__vqbw = c.context.insert_const_string(c.builder.module, 'pandas')
    hjyb__nelp = c.pyapi.import_module_noblock(tpmmn__vqbw)
    jbyqi__rjqin = c.pyapi.call_method(hjyb__nelp, 'StringDtype', ())
    c.pyapi.decref(hjyb__nelp)
    return jbyqi__rjqin


@unbox(StringDtype)
def unbox_string_dtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


typeof_impl.register(pd.StringDtype)(lambda a, b: string_dtype)
type_callable(pd.StringDtype)(lambda c: lambda : string_dtype)
lower_builtin(pd.StringDtype)(lambda c, b, s, a: c.get_dummy_value())


def create_binary_op_overload(op):

    def overload_string_array_binary_op(lhs, rhs):
        ncmvg__swc = bodo.libs.dict_arr_ext.get_binary_op_overload(op, lhs, rhs
            )
        if ncmvg__swc is not None:
            return ncmvg__swc
        if is_str_arr_type(lhs) and is_str_arr_type(rhs):

            def impl_both(lhs, rhs):
                numba.parfors.parfor.init_prange()
                alhux__pqj = len(lhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(alhux__pqj)
                for i in numba.parfors.parfor.internal_prange(alhux__pqj):
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
                alhux__pqj = len(lhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(alhux__pqj)
                for i in numba.parfors.parfor.internal_prange(alhux__pqj):
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
                alhux__pqj = len(rhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(alhux__pqj)
                for i in numba.parfors.parfor.internal_prange(alhux__pqj):
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
    pjizl__stph = is_str_arr_type(lhs) or isinstance(lhs, types.Array
        ) and lhs.dtype == string_type
    bwr__xyln = is_str_arr_type(rhs) or isinstance(rhs, types.Array
        ) and rhs.dtype == string_type
    if is_str_arr_type(lhs) and bwr__xyln or pjizl__stph and is_str_arr_type(
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
    cjon__rqc = context.make_helper(builder, arr_typ, arr_value)
    xuu__szbt = ArrayItemArrayType(char_arr_type)
    vgwep__flvow = _get_array_item_arr_payload(context, builder, xuu__szbt,
        cjon__rqc.data)
    return vgwep__flvow


@intrinsic
def num_strings(typingctx, str_arr_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        return vgwep__flvow.n_arrays
    return types.int64(string_array_type), codegen


def _get_num_total_chars(builder, offsets, num_strings):
    return builder.zext(builder.load(builder.gep(offsets, [num_strings])),
        lir.IntType(64))


@intrinsic
def num_total_chars(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        paba__rnnny = context.make_helper(builder, offset_arr_type,
            vgwep__flvow.offsets).data
        return _get_num_total_chars(builder, paba__rnnny, vgwep__flvow.n_arrays
            )
    return types.uint64(in_arr_typ), codegen


@intrinsic
def get_offset_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        ijat__mlcm = context.make_helper(builder, offset_arr_type,
            vgwep__flvow.offsets)
        lifn__cnqut = context.make_helper(builder, offset_ctypes_type)
        lifn__cnqut.data = builder.bitcast(ijat__mlcm.data, lir.IntType(
            offset_type.bitwidth).as_pointer())
        lifn__cnqut.meminfo = ijat__mlcm.meminfo
        jbyqi__rjqin = lifn__cnqut._getvalue()
        return impl_ret_borrowed(context, builder, offset_ctypes_type,
            jbyqi__rjqin)
    return offset_ctypes_type(in_arr_typ), codegen


@intrinsic
def get_data_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        eptr__yzj = context.make_helper(builder, char_arr_type,
            vgwep__flvow.data)
        lifn__cnqut = context.make_helper(builder, data_ctypes_type)
        lifn__cnqut.data = eptr__yzj.data
        lifn__cnqut.meminfo = eptr__yzj.meminfo
        jbyqi__rjqin = lifn__cnqut._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type,
            jbyqi__rjqin)
    return data_ctypes_type(in_arr_typ), codegen


@intrinsic
def get_data_ptr_ind(typingctx, in_arr_typ, int_t=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        pzmy__rrw, ind = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            pzmy__rrw, sig.args[0])
        eptr__yzj = context.make_helper(builder, char_arr_type,
            vgwep__flvow.data)
        lifn__cnqut = context.make_helper(builder, data_ctypes_type)
        lifn__cnqut.data = builder.gep(eptr__yzj.data, [ind])
        lifn__cnqut.meminfo = eptr__yzj.meminfo
        jbyqi__rjqin = lifn__cnqut._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type,
            jbyqi__rjqin)
    return data_ctypes_type(in_arr_typ, types.intp), codegen


@intrinsic
def copy_single_char(typingctx, dst_ptr_t, dst_ind_t, src_ptr_t, src_ind_t=None
    ):

    def codegen(context, builder, sig, args):
        ceiiq__sjkru, vio__ucuqr, alb__wxtuo, ciy__zgj = args
        exshm__yprxo = builder.bitcast(builder.gep(ceiiq__sjkru, [
            vio__ucuqr]), lir.IntType(8).as_pointer())
        tldqo__pyepi = builder.bitcast(builder.gep(alb__wxtuo, [ciy__zgj]),
            lir.IntType(8).as_pointer())
        mkqyj__xmb = builder.load(tldqo__pyepi)
        builder.store(mkqyj__xmb, exshm__yprxo)
        return context.get_dummy_value()
    return types.void(types.voidptr, types.intp, types.voidptr, types.intp
        ), codegen


@intrinsic
def get_null_bitmap_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        mvuf__fgp = context.make_helper(builder, null_bitmap_arr_type,
            vgwep__flvow.null_bitmap)
        lifn__cnqut = context.make_helper(builder, data_ctypes_type)
        lifn__cnqut.data = mvuf__fgp.data
        lifn__cnqut.meminfo = mvuf__fgp.meminfo
        jbyqi__rjqin = lifn__cnqut._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type,
            jbyqi__rjqin)
    return data_ctypes_type(in_arr_typ), codegen


@intrinsic
def getitem_str_offset(typingctx, in_arr_typ, ind_t=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        paba__rnnny = context.make_helper(builder, offset_arr_type,
            vgwep__flvow.offsets).data
        return builder.load(builder.gep(paba__rnnny, [ind]))
    return offset_type(in_arr_typ, ind_t), codegen


@intrinsic
def setitem_str_offset(typingctx, str_arr_typ, ind_t, val_t=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind, val = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        offsets = context.make_helper(builder, offset_arr_type,
            vgwep__flvow.offsets).data
        builder.store(val, builder.gep(offsets, [ind]))
        return context.get_dummy_value()
    return types.void(string_array_type, ind_t, offset_type), codegen


@intrinsic
def getitem_str_bitmap(typingctx, in_bitmap_typ, ind_t=None):

    def codegen(context, builder, sig, args):
        zna__mtflv, ind = args
        if in_bitmap_typ == data_ctypes_type:
            lifn__cnqut = context.make_helper(builder, data_ctypes_type,
                zna__mtflv)
            zna__mtflv = lifn__cnqut.data
        return builder.load(builder.gep(zna__mtflv, [ind]))
    return char_type(in_bitmap_typ, ind_t), codegen


@intrinsic
def setitem_str_bitmap(typingctx, in_bitmap_typ, ind_t, val_t=None):

    def codegen(context, builder, sig, args):
        zna__mtflv, ind, val = args
        if in_bitmap_typ == data_ctypes_type:
            lifn__cnqut = context.make_helper(builder, data_ctypes_type,
                zna__mtflv)
            zna__mtflv = lifn__cnqut.data
        builder.store(val, builder.gep(zna__mtflv, [ind]))
        return context.get_dummy_value()
    return types.void(in_bitmap_typ, ind_t, char_type), codegen


@intrinsic
def copy_str_arr_slice(typingctx, out_str_arr_typ, in_str_arr_typ, ind_t=None):
    assert out_str_arr_typ == string_array_type and in_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr, ind = args
        qbqu__opyje = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        eolu__pxyo = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        ipwnx__mwuty = context.make_helper(builder, offset_arr_type,
            qbqu__opyje.offsets).data
        pxdh__cnosv = context.make_helper(builder, offset_arr_type,
            eolu__pxyo.offsets).data
        lkm__punuz = context.make_helper(builder, char_arr_type,
            qbqu__opyje.data).data
        qva__rtnx = context.make_helper(builder, char_arr_type, eolu__pxyo.data
            ).data
        ibrw__tpbp = context.make_helper(builder, null_bitmap_arr_type,
            qbqu__opyje.null_bitmap).data
        rgjz__igsnj = context.make_helper(builder, null_bitmap_arr_type,
            eolu__pxyo.null_bitmap).data
        oblc__sim = builder.add(ind, context.get_constant(types.intp, 1))
        cgutils.memcpy(builder, pxdh__cnosv, ipwnx__mwuty, oblc__sim)
        cgutils.memcpy(builder, qva__rtnx, lkm__punuz, builder.load(builder
            .gep(ipwnx__mwuty, [ind])))
        bhea__ceww = builder.add(ind, lir.Constant(lir.IntType(64), 7))
        urcpf__irzqk = builder.lshr(bhea__ceww, lir.Constant(lir.IntType(64
            ), 3))
        cgutils.memcpy(builder, rgjz__igsnj, ibrw__tpbp, urcpf__irzqk)
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type, ind_t), codegen


@intrinsic
def copy_data(typingctx, str_arr_typ, out_str_arr_typ=None):
    assert str_arr_typ == string_array_type and out_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr = args
        qbqu__opyje = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        eolu__pxyo = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        ipwnx__mwuty = context.make_helper(builder, offset_arr_type,
            qbqu__opyje.offsets).data
        lkm__punuz = context.make_helper(builder, char_arr_type,
            qbqu__opyje.data).data
        qva__rtnx = context.make_helper(builder, char_arr_type, eolu__pxyo.data
            ).data
        num_total_chars = _get_num_total_chars(builder, ipwnx__mwuty,
            qbqu__opyje.n_arrays)
        cgutils.memcpy(builder, qva__rtnx, lkm__punuz, num_total_chars)
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type), codegen


@intrinsic
def copy_non_null_offsets(typingctx, str_arr_typ, out_str_arr_typ=None):
    assert str_arr_typ == string_array_type and out_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr = args
        qbqu__opyje = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        eolu__pxyo = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        ipwnx__mwuty = context.make_helper(builder, offset_arr_type,
            qbqu__opyje.offsets).data
        pxdh__cnosv = context.make_helper(builder, offset_arr_type,
            eolu__pxyo.offsets).data
        ibrw__tpbp = context.make_helper(builder, null_bitmap_arr_type,
            qbqu__opyje.null_bitmap).data
        alhux__pqj = qbqu__opyje.n_arrays
        vomyu__why = context.get_constant(offset_type, 0)
        msn__ygm = cgutils.alloca_once_value(builder, vomyu__why)
        with cgutils.for_range(builder, alhux__pqj) as ogkm__ldn:
            ayfkh__toqy = lower_is_na(context, builder, ibrw__tpbp,
                ogkm__ldn.index)
            with cgutils.if_likely(builder, builder.not_(ayfkh__toqy)):
                hpyjm__gttj = builder.load(builder.gep(ipwnx__mwuty, [
                    ogkm__ldn.index]))
                ipt__hatl = builder.load(msn__ygm)
                builder.store(hpyjm__gttj, builder.gep(pxdh__cnosv, [
                    ipt__hatl]))
                builder.store(builder.add(ipt__hatl, lir.Constant(context.
                    get_value_type(offset_type), 1)), msn__ygm)
        ipt__hatl = builder.load(msn__ygm)
        hpyjm__gttj = builder.load(builder.gep(ipwnx__mwuty, [alhux__pqj]))
        builder.store(hpyjm__gttj, builder.gep(pxdh__cnosv, [ipt__hatl]))
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type), codegen


@intrinsic
def str_copy(typingctx, buff_arr_typ, ind_typ, str_typ, len_typ=None):

    def codegen(context, builder, sig, args):
        nrjg__dwgw, ind, str, dxhv__duwya = args
        nrjg__dwgw = context.make_array(sig.args[0])(context, builder,
            nrjg__dwgw)
        stuu__ufgdc = builder.gep(nrjg__dwgw.data, [ind])
        cgutils.raw_memcpy(builder, stuu__ufgdc, str, dxhv__duwya, 1)
        return context.get_dummy_value()
    return types.void(null_bitmap_arr_type, types.intp, types.voidptr,
        types.intp), codegen


@intrinsic
def str_copy_ptr(typingctx, ptr_typ, ind_typ, str_typ, len_typ=None):

    def codegen(context, builder, sig, args):
        stuu__ufgdc, ind, vwbny__ikl, dxhv__duwya = args
        stuu__ufgdc = builder.gep(stuu__ufgdc, [ind])
        cgutils.raw_memcpy(builder, stuu__ufgdc, vwbny__ikl, dxhv__duwya, 1)
        return context.get_dummy_value()
    return types.void(types.voidptr, types.intp, types.voidptr, types.intp
        ), codegen


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_length(A, i):
    return np.int64(getitem_str_offset(A, i + 1) - getitem_str_offset(A, i))


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_str_length(A, i):
    zsf__yll = np.int64(getitem_str_offset(A, i))
    pbedd__bxgjv = np.int64(getitem_str_offset(A, i + 1))
    l = pbedd__bxgjv - zsf__yll
    pyj__wfnwr = get_data_ptr_ind(A, zsf__yll)
    for j in range(l):
        if bodo.hiframes.split_impl.getitem_c_arr(pyj__wfnwr, j) >= 128:
            return len(A[i])
    return l


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_ptr(A, i):
    return get_data_ptr_ind(A, getitem_str_offset(A, i))


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_copy(B, j, A, i):
    if j == 0:
        setitem_str_offset(B, 0, 0)
    swq__itbbo = getitem_str_offset(A, i)
    qfkdw__tin = getitem_str_offset(A, i + 1)
    zwz__zud = qfkdw__tin - swq__itbbo
    fxcw__mkvsp = getitem_str_offset(B, j)
    urqm__epaex = fxcw__mkvsp + zwz__zud
    setitem_str_offset(B, j + 1, urqm__epaex)
    if str_arr_is_na(A, i):
        str_arr_set_na(B, j)
    else:
        str_arr_set_not_na(B, j)
    if zwz__zud != 0:
        eptr__yzj = B._data
        bodo.libs.array_item_arr_ext.ensure_data_capacity(eptr__yzj, np.
            int64(fxcw__mkvsp), np.int64(urqm__epaex))
        dhvjc__sqybj = get_data_ptr(B).data
        xdqsq__xec = get_data_ptr(A).data
        memcpy_region(dhvjc__sqybj, fxcw__mkvsp, xdqsq__xec, swq__itbbo,
            zwz__zud, 1)


@numba.njit(no_cpython_wrapper=True)
def get_str_null_bools(str_arr):
    alhux__pqj = len(str_arr)
    qageg__npy = np.empty(alhux__pqj, np.bool_)
    for i in range(alhux__pqj):
        qageg__npy[i] = bodo.libs.array_kernels.isna(str_arr, i)
    return qageg__npy


def to_list_if_immutable_arr(arr, str_null_bools=None):
    return arr


@overload(to_list_if_immutable_arr, no_unliteral=True)
def to_list_if_immutable_arr_overload(data, str_null_bools=None):
    if is_str_arr_type(data) or data == binary_array_type:

        def to_list_impl(data, str_null_bools=None):
            alhux__pqj = len(data)
            l = []
            for i in range(alhux__pqj):
                l.append(data[i])
            return l
        return to_list_impl
    if isinstance(data, types.BaseTuple):
        pfq__ujdft = data.count
        iiyiq__zpp = ['to_list_if_immutable_arr(data[{}])'.format(i) for i in
            range(pfq__ujdft)]
        if is_overload_true(str_null_bools):
            iiyiq__zpp += ['get_str_null_bools(data[{}])'.format(i) for i in
                range(pfq__ujdft) if is_str_arr_type(data.types[i]) or data
                .types[i] == binary_array_type]
        flqo__xuntj = 'def f(data, str_null_bools=None):\n'
        flqo__xuntj += '  return ({}{})\n'.format(', '.join(iiyiq__zpp), 
            ',' if pfq__ujdft == 1 else '')
        zzja__mhke = {}
        exec(flqo__xuntj, {'to_list_if_immutable_arr':
            to_list_if_immutable_arr, 'get_str_null_bools':
            get_str_null_bools, 'bodo': bodo}, zzja__mhke)
        ikx__los = zzja__mhke['f']
        return ikx__los
    return lambda data, str_null_bools=None: data


def cp_str_list_to_array(str_arr, str_list, str_null_bools=None):
    return


@overload(cp_str_list_to_array, no_unliteral=True)
def cp_str_list_to_array_overload(str_arr, list_data, str_null_bools=None):
    if str_arr == string_array_type:
        if is_overload_none(str_null_bools):

            def cp_str_list_impl(str_arr, list_data, str_null_bools=None):
                alhux__pqj = len(list_data)
                for i in range(alhux__pqj):
                    vwbny__ikl = list_data[i]
                    str_arr[i] = vwbny__ikl
            return cp_str_list_impl
        else:

            def cp_str_list_impl_null(str_arr, list_data, str_null_bools=None):
                alhux__pqj = len(list_data)
                for i in range(alhux__pqj):
                    vwbny__ikl = list_data[i]
                    str_arr[i] = vwbny__ikl
                    if str_null_bools[i]:
                        str_arr_set_na(str_arr, i)
                    else:
                        str_arr_set_not_na(str_arr, i)
            return cp_str_list_impl_null
    if isinstance(str_arr, types.BaseTuple):
        pfq__ujdft = str_arr.count
        nolp__jxqt = 0
        flqo__xuntj = 'def f(str_arr, list_data, str_null_bools=None):\n'
        for i in range(pfq__ujdft):
            if is_overload_true(str_null_bools) and str_arr.types[i
                ] == string_array_type:
                flqo__xuntj += (
                    """  cp_str_list_to_array(str_arr[{}], list_data[{}], list_data[{}])
"""
                    .format(i, i, pfq__ujdft + nolp__jxqt))
                nolp__jxqt += 1
            else:
                flqo__xuntj += (
                    '  cp_str_list_to_array(str_arr[{}], list_data[{}])\n'.
                    format(i, i))
        flqo__xuntj += '  return\n'
        zzja__mhke = {}
        exec(flqo__xuntj, {'cp_str_list_to_array': cp_str_list_to_array},
            zzja__mhke)
        pqsi__foci = zzja__mhke['f']
        return pqsi__foci
    return lambda str_arr, list_data, str_null_bools=None: None


def str_list_to_array(str_list):
    return str_list


@overload(str_list_to_array, no_unliteral=True)
def str_list_to_array_overload(str_list):
    if isinstance(str_list, types.List) and str_list.dtype == bodo.string_type:

        def str_list_impl(str_list):
            alhux__pqj = len(str_list)
            str_arr = pre_alloc_string_array(alhux__pqj, -1)
            for i in range(alhux__pqj):
                vwbny__ikl = str_list[i]
                str_arr[i] = vwbny__ikl
            return str_arr
        return str_list_impl
    return lambda str_list: str_list


def get_num_total_chars(A):
    pass


@overload(get_num_total_chars)
def overload_get_num_total_chars(A):
    if isinstance(A, types.List) and A.dtype == string_type:

        def str_list_impl(A):
            alhux__pqj = len(A)
            mbgxt__gtnd = 0
            for i in range(alhux__pqj):
                vwbny__ikl = A[i]
                mbgxt__gtnd += get_utf8_size(vwbny__ikl)
            return mbgxt__gtnd
        return str_list_impl
    assert A == string_array_type
    return lambda A: num_total_chars(A)


@overload_method(StringArrayType, 'copy', no_unliteral=True)
def str_arr_copy_overload(arr):

    def copy_impl(arr):
        alhux__pqj = len(arr)
        n_chars = num_total_chars(arr)
        qxwa__sjmfl = pre_alloc_string_array(alhux__pqj, np.int64(n_chars))
        copy_str_arr_slice(qxwa__sjmfl, arr, alhux__pqj)
        return qxwa__sjmfl
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
    flqo__xuntj = 'def f(in_seq):\n'
    flqo__xuntj += '    n_strs = len(in_seq)\n'
    flqo__xuntj += '    A = pre_alloc_string_array(n_strs, -1)\n'
    flqo__xuntj += '    return A\n'
    zzja__mhke = {}
    exec(flqo__xuntj, {'pre_alloc_string_array': pre_alloc_string_array},
        zzja__mhke)
    cfet__tfy = zzja__mhke['f']
    return cfet__tfy


@numba.generated_jit(nopython=True)
def str_arr_from_sequence(in_seq):
    if in_seq.dtype == bodo.bytes_type:
        epzry__oemen = 'pre_alloc_binary_array'
    else:
        epzry__oemen = 'pre_alloc_string_array'
    flqo__xuntj = 'def f(in_seq):\n'
    flqo__xuntj += '    n_strs = len(in_seq)\n'
    flqo__xuntj += f'    A = {epzry__oemen}(n_strs, -1)\n'
    flqo__xuntj += '    for i in range(n_strs):\n'
    flqo__xuntj += '        A[i] = in_seq[i]\n'
    flqo__xuntj += '    return A\n'
    zzja__mhke = {}
    exec(flqo__xuntj, {'pre_alloc_string_array': pre_alloc_string_array,
        'pre_alloc_binary_array': pre_alloc_binary_array}, zzja__mhke)
    cfet__tfy = zzja__mhke['f']
    return cfet__tfy


@intrinsic
def set_all_offsets_to_0(typingctx, arr_typ=None):
    assert arr_typ in (string_array_type, binary_array_type
        ), 'set_all_offsets_to_0 requires a string or binary array'

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        wwjm__egn = builder.add(vgwep__flvow.n_arrays, lir.Constant(lir.
            IntType(64), 1))
        uwj__geffx = builder.lshr(lir.Constant(lir.IntType(64), offset_type
            .bitwidth), lir.Constant(lir.IntType(64), 3))
        urcpf__irzqk = builder.mul(wwjm__egn, uwj__geffx)
        dgl__cqe = context.make_array(offset_arr_type)(context, builder,
            vgwep__flvow.offsets).data
        cgutils.memset(builder, dgl__cqe, urcpf__irzqk, 0)
        return context.get_dummy_value()
    return types.none(arr_typ), codegen


@intrinsic
def set_bitmap_all_NA(typingctx, arr_typ=None):
    assert arr_typ in (string_array_type, binary_array_type
        ), 'set_bitmap_all_NA requires a string or binary array'

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        cmx__jqh = vgwep__flvow.n_arrays
        urcpf__irzqk = builder.lshr(builder.add(cmx__jqh, lir.Constant(lir.
            IntType(64), 7)), lir.Constant(lir.IntType(64), 3))
        emjrr__ollb = context.make_array(null_bitmap_arr_type)(context,
            builder, vgwep__flvow.null_bitmap).data
        cgutils.memset(builder, emjrr__ollb, urcpf__irzqk, 0)
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
    nqxix__qyfu = 0
    if total_len == 0:
        for i in range(len(offsets)):
            offsets[i] = 0
    else:
        vpxvi__vxrm = len(len_arr)
        for i in range(vpxvi__vxrm):
            offsets[i] = nqxix__qyfu
            nqxix__qyfu += len_arr[i]
        offsets[vpxvi__vxrm] = nqxix__qyfu
    return str_arr


kBitmask = np.array([1, 2, 4, 8, 16, 32, 64, 128], dtype=np.uint8)


@numba.njit
def set_bit_to(bits, i, bit_is_set):
    xdtfe__isi = i // 8
    vod__fsxd = getitem_str_bitmap(bits, xdtfe__isi)
    vod__fsxd ^= np.uint8(-np.uint8(bit_is_set) ^ vod__fsxd) & kBitmask[i % 8]
    setitem_str_bitmap(bits, xdtfe__isi, vod__fsxd)


@numba.njit
def get_bit_bitmap(bits, i):
    return getitem_str_bitmap(bits, i >> 3) >> (i & 7) & 1


@numba.njit
def copy_nulls_range(out_str_arr, in_str_arr, out_start):
    xejgo__qzcpf = get_null_bitmap_ptr(out_str_arr)
    yoxfz__mvtf = get_null_bitmap_ptr(in_str_arr)
    for j in range(len(in_str_arr)):
        hfy__gefhk = get_bit_bitmap(yoxfz__mvtf, j)
        set_bit_to(xejgo__qzcpf, out_start + j, hfy__gefhk)


@intrinsic
def set_string_array_range(typingctx, out_typ, in_typ, curr_str_typ,
    curr_chars_typ=None):
    assert out_typ == string_array_type and in_typ == string_array_type or out_typ == binary_array_type and in_typ == binary_array_type, 'set_string_array_range requires string or binary arrays'
    assert isinstance(curr_str_typ, types.Integer) and isinstance(
        curr_chars_typ, types.Integer
        ), 'set_string_array_range requires integer indices'

    def codegen(context, builder, sig, args):
        out_arr, pzmy__rrw, kew__cybvf, yecsd__cvk = args
        qbqu__opyje = _get_str_binary_arr_payload(context, builder,
            pzmy__rrw, string_array_type)
        eolu__pxyo = _get_str_binary_arr_payload(context, builder, out_arr,
            string_array_type)
        ipwnx__mwuty = context.make_helper(builder, offset_arr_type,
            qbqu__opyje.offsets).data
        pxdh__cnosv = context.make_helper(builder, offset_arr_type,
            eolu__pxyo.offsets).data
        lkm__punuz = context.make_helper(builder, char_arr_type,
            qbqu__opyje.data).data
        qva__rtnx = context.make_helper(builder, char_arr_type, eolu__pxyo.data
            ).data
        num_total_chars = _get_num_total_chars(builder, ipwnx__mwuty,
            qbqu__opyje.n_arrays)
        fygnz__dbqps = lir.FunctionType(lir.VoidType(), [lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(64), lir.IntType(64), lir.IntType(64),
            lir.IntType(64)])
        sdeib__rtlbi = cgutils.get_or_insert_function(builder.module,
            fygnz__dbqps, name='set_string_array_range')
        builder.call(sdeib__rtlbi, [pxdh__cnosv, qva__rtnx, ipwnx__mwuty,
            lkm__punuz, kew__cybvf, yecsd__cvk, qbqu__opyje.n_arrays,
            num_total_chars])
        lgo__plyci = context.typing_context.resolve_value_type(copy_nulls_range
            )
        zyg__dskf = lgo__plyci.get_call_type(context.typing_context, (
            string_array_type, string_array_type, types.int64), {})
        wnm__bqipi = context.get_function(lgo__plyci, zyg__dskf)
        wnm__bqipi(builder, (out_arr, pzmy__rrw, kew__cybvf))
        return context.get_dummy_value()
    sig = types.void(out_typ, in_typ, types.intp, types.intp)
    return sig, codegen


@box(BinaryArrayType)
@box(StringArrayType)
def box_str_arr(typ, val, c):
    assert typ in [binary_array_type, string_array_type]
    zhrxv__ztvvh = c.context.make_helper(c.builder, typ, val)
    xuu__szbt = ArrayItemArrayType(char_arr_type)
    vgwep__flvow = _get_array_item_arr_payload(c.context, c.builder,
        xuu__szbt, zhrxv__ztvvh.data)
    osse__xfw = c.context.get_constant(types.int32, int(typ ==
        binary_array_type))
    erb__rya = 'np_array_from_string_array'
    if use_pd_string_array and typ != binary_array_type:
        erb__rya = 'pd_array_from_string_array'
    fygnz__dbqps = lir.FunctionType(c.context.get_argument_type(types.
        pyobject), [lir.IntType(64), lir.IntType(offset_type.bitwidth).
        as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
        as_pointer(), lir.IntType(32)])
    gcq__iczo = cgutils.get_or_insert_function(c.builder.module,
        fygnz__dbqps, name=erb__rya)
    paba__rnnny = c.context.make_array(offset_arr_type)(c.context, c.
        builder, vgwep__flvow.offsets).data
    pyj__wfnwr = c.context.make_array(char_arr_type)(c.context, c.builder,
        vgwep__flvow.data).data
    emjrr__ollb = c.context.make_array(null_bitmap_arr_type)(c.context, c.
        builder, vgwep__flvow.null_bitmap).data
    arr = c.builder.call(gcq__iczo, [vgwep__flvow.n_arrays, paba__rnnny,
        pyj__wfnwr, emjrr__ollb, osse__xfw])
    c.context.nrt.decref(c.builder, typ, val)
    return arr


@intrinsic
def str_arr_is_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        emjrr__ollb = context.make_array(null_bitmap_arr_type)(context,
            builder, vgwep__flvow.null_bitmap).data
        pink__vel = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        jffz__bltig = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        vod__fsxd = builder.load(builder.gep(emjrr__ollb, [pink__vel],
            inbounds=True))
        afoje__noh = lir.ArrayType(lir.IntType(8), 8)
        bakx__ginv = cgutils.alloca_once_value(builder, lir.Constant(
            afoje__noh, (1, 2, 4, 8, 16, 32, 64, 128)))
        obpb__rodwz = builder.load(builder.gep(bakx__ginv, [lir.Constant(
            lir.IntType(64), 0), jffz__bltig], inbounds=True))
        return builder.icmp_unsigned('==', builder.and_(vod__fsxd,
            obpb__rodwz), lir.Constant(lir.IntType(8), 0))
    return types.bool_(str_arr_typ, types.intp), codegen


@intrinsic
def str_arr_set_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        pink__vel = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        jffz__bltig = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        emjrr__ollb = context.make_array(null_bitmap_arr_type)(context,
            builder, vgwep__flvow.null_bitmap).data
        offsets = context.make_helper(builder, offset_arr_type,
            vgwep__flvow.offsets).data
        kgjdc__dzvf = builder.gep(emjrr__ollb, [pink__vel], inbounds=True)
        vod__fsxd = builder.load(kgjdc__dzvf)
        afoje__noh = lir.ArrayType(lir.IntType(8), 8)
        bakx__ginv = cgutils.alloca_once_value(builder, lir.Constant(
            afoje__noh, (1, 2, 4, 8, 16, 32, 64, 128)))
        obpb__rodwz = builder.load(builder.gep(bakx__ginv, [lir.Constant(
            lir.IntType(64), 0), jffz__bltig], inbounds=True))
        obpb__rodwz = builder.xor(obpb__rodwz, lir.Constant(lir.IntType(8), -1)
            )
        builder.store(builder.and_(vod__fsxd, obpb__rodwz), kgjdc__dzvf)
        if str_arr_typ == string_array_type:
            hkzl__uelav = builder.add(ind, lir.Constant(lir.IntType(64), 1))
            ajbi__saxp = builder.icmp_unsigned('!=', hkzl__uelav,
                vgwep__flvow.n_arrays)
            with builder.if_then(ajbi__saxp):
                builder.store(builder.load(builder.gep(offsets, [ind])),
                    builder.gep(offsets, [hkzl__uelav]))
        return context.get_dummy_value()
    return types.void(str_arr_typ, types.intp), codegen


@intrinsic
def str_arr_set_not_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        pink__vel = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        jffz__bltig = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        emjrr__ollb = context.make_array(null_bitmap_arr_type)(context,
            builder, vgwep__flvow.null_bitmap).data
        kgjdc__dzvf = builder.gep(emjrr__ollb, [pink__vel], inbounds=True)
        vod__fsxd = builder.load(kgjdc__dzvf)
        afoje__noh = lir.ArrayType(lir.IntType(8), 8)
        bakx__ginv = cgutils.alloca_once_value(builder, lir.Constant(
            afoje__noh, (1, 2, 4, 8, 16, 32, 64, 128)))
        obpb__rodwz = builder.load(builder.gep(bakx__ginv, [lir.Constant(
            lir.IntType(64), 0), jffz__bltig], inbounds=True))
        builder.store(builder.or_(vod__fsxd, obpb__rodwz), kgjdc__dzvf)
        return context.get_dummy_value()
    return types.void(str_arr_typ, types.intp), codegen


@intrinsic
def set_null_bits_to_value(typingctx, arr_typ, value_typ=None):
    assert (arr_typ == string_array_type or arr_typ == binary_array_type
        ) and is_overload_constant_int(value_typ)

    def codegen(context, builder, sig, args):
        in_str_arr, value = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        urcpf__irzqk = builder.udiv(builder.add(vgwep__flvow.n_arrays, lir.
            Constant(lir.IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
        emjrr__ollb = context.make_array(null_bitmap_arr_type)(context,
            builder, vgwep__flvow.null_bitmap).data
        cgutils.memset(builder, emjrr__ollb, urcpf__irzqk, value)
        return context.get_dummy_value()
    return types.none(arr_typ, types.int8), codegen


def _get_str_binary_arr_data_payload_ptr(context, builder, str_arr):
    qntos__rafa = context.make_helper(builder, string_array_type, str_arr)
    xuu__szbt = ArrayItemArrayType(char_arr_type)
    gwf__eiwzp = context.make_helper(builder, xuu__szbt, qntos__rafa.data)
    oyc__iok = ArrayItemArrayPayloadType(xuu__szbt)
    wjm__upef = context.nrt.meminfo_data(builder, gwf__eiwzp.meminfo)
    ymr__efdby = builder.bitcast(wjm__upef, context.get_value_type(oyc__iok
        ).as_pointer())
    return ymr__efdby


@intrinsic
def move_str_binary_arr_payload(typingctx, to_arr_typ, from_arr_typ=None):
    assert to_arr_typ == string_array_type and from_arr_typ == string_array_type or to_arr_typ == binary_array_type and from_arr_typ == binary_array_type

    def codegen(context, builder, sig, args):
        jkyaq__mjhbc, sesp__uado = args
        uumo__gomdh = _get_str_binary_arr_data_payload_ptr(context, builder,
            sesp__uado)
        hmjg__kux = _get_str_binary_arr_data_payload_ptr(context, builder,
            jkyaq__mjhbc)
        ouexy__hmil = _get_str_binary_arr_payload(context, builder,
            sesp__uado, sig.args[1])
        xltb__hcosr = _get_str_binary_arr_payload(context, builder,
            jkyaq__mjhbc, sig.args[0])
        context.nrt.incref(builder, char_arr_type, ouexy__hmil.data)
        context.nrt.incref(builder, offset_arr_type, ouexy__hmil.offsets)
        context.nrt.incref(builder, null_bitmap_arr_type, ouexy__hmil.
            null_bitmap)
        context.nrt.decref(builder, char_arr_type, xltb__hcosr.data)
        context.nrt.decref(builder, offset_arr_type, xltb__hcosr.offsets)
        context.nrt.decref(builder, null_bitmap_arr_type, xltb__hcosr.
            null_bitmap)
        builder.store(builder.load(uumo__gomdh), hmjg__kux)
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
        alhux__pqj = _get_utf8_size(s._data, s._length, s._kind)
        dummy_use(s)
        return alhux__pqj
    return impl


@intrinsic
def setitem_str_arr_ptr(typingctx, str_arr_t, ind_t, ptr_t, len_t=None):

    def codegen(context, builder, sig, args):
        arr, ind, stuu__ufgdc, cehh__cqlqi = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder, arr,
            sig.args[0])
        offsets = context.make_helper(builder, offset_arr_type,
            vgwep__flvow.offsets).data
        data = context.make_helper(builder, char_arr_type, vgwep__flvow.data
            ).data
        fygnz__dbqps = lir.FunctionType(lir.VoidType(), [lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(64),
            lir.IntType(32), lir.IntType(32), lir.IntType(64)])
        wckei__zfp = cgutils.get_or_insert_function(builder.module,
            fygnz__dbqps, name='setitem_string_array')
        wjks__iejar = context.get_constant(types.int32, -1)
        otd__yvfhv = context.get_constant(types.int32, 1)
        num_total_chars = _get_num_total_chars(builder, offsets,
            vgwep__flvow.n_arrays)
        builder.call(wckei__zfp, [offsets, data, num_total_chars, builder.
            extract_value(stuu__ufgdc, 0), cehh__cqlqi, wjks__iejar,
            otd__yvfhv, ind])
        return context.get_dummy_value()
    return types.void(str_arr_t, ind_t, ptr_t, len_t), codegen


def lower_is_na(context, builder, bull_bitmap, ind):
    fygnz__dbqps = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
        as_pointer(), lir.IntType(64)])
    dloy__lyo = cgutils.get_or_insert_function(builder.module, fygnz__dbqps,
        name='is_na')
    return builder.call(dloy__lyo, [bull_bitmap, ind])


@intrinsic
def _memcpy(typingctx, dest_t, src_t, count_t, item_size_t=None):

    def codegen(context, builder, sig, args):
        exshm__yprxo, tldqo__pyepi, pfq__ujdft, pdbwi__ludsc = args
        cgutils.raw_memcpy(builder, exshm__yprxo, tldqo__pyepi, pfq__ujdft,
            pdbwi__ludsc)
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
        jaqhg__rtu, oxb__imc = unicode_to_utf8_and_len(val)
        prdk__kcqtx = getitem_str_offset(A, ind)
        ktj__leiw = getitem_str_offset(A, ind + 1)
        jon__gbd = ktj__leiw - prdk__kcqtx
        if jon__gbd != oxb__imc:
            return False
        stuu__ufgdc = get_data_ptr_ind(A, prdk__kcqtx)
        return memcmp(stuu__ufgdc, jaqhg__rtu, oxb__imc) == 0
    return impl


def str_arr_setitem_int_to_str(A, ind, value):
    A[ind] = str(value)


@overload(str_arr_setitem_int_to_str)
def overload_str_arr_setitem_int_to_str(A, ind, val):

    def impl(A, ind, val):
        prdk__kcqtx = getitem_str_offset(A, ind)
        jon__gbd = bodo.libs.str_ext.int_to_str_len(val)
        jtqvi__xkttj = prdk__kcqtx + jon__gbd
        bodo.libs.array_item_arr_ext.ensure_data_capacity(A._data,
            prdk__kcqtx, jtqvi__xkttj)
        stuu__ufgdc = get_data_ptr_ind(A, prdk__kcqtx)
        inplace_int64_to_str(stuu__ufgdc, jon__gbd, val)
        setitem_str_offset(A, ind + 1, prdk__kcqtx + jon__gbd)
        str_arr_set_not_na(A, ind)
    return impl


@intrinsic
def inplace_set_NA_str(typingctx, ptr_typ=None):

    def codegen(context, builder, sig, args):
        stuu__ufgdc, = args
        qilb__hdtq = context.insert_const_string(builder.module, '<NA>')
        ogwuk__bqqj = lir.Constant(lir.IntType(64), len('<NA>'))
        cgutils.raw_memcpy(builder, stuu__ufgdc, qilb__hdtq, ogwuk__bqqj, 1)
    return types.none(types.voidptr), codegen


def str_arr_setitem_NA_str(A, ind):
    A[ind] = '<NA>'


@overload(str_arr_setitem_NA_str)
def overload_str_arr_setitem_NA_str(A, ind):
    gqeux__cljti = len('<NA>')

    def impl(A, ind):
        prdk__kcqtx = getitem_str_offset(A, ind)
        jtqvi__xkttj = prdk__kcqtx + gqeux__cljti
        bodo.libs.array_item_arr_ext.ensure_data_capacity(A._data,
            prdk__kcqtx, jtqvi__xkttj)
        stuu__ufgdc = get_data_ptr_ind(A, prdk__kcqtx)
        inplace_set_NA_str(stuu__ufgdc)
        setitem_str_offset(A, ind + 1, prdk__kcqtx + gqeux__cljti)
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
            prdk__kcqtx = getitem_str_offset(A, ind)
            ktj__leiw = getitem_str_offset(A, ind + 1)
            cehh__cqlqi = ktj__leiw - prdk__kcqtx
            stuu__ufgdc = get_data_ptr_ind(A, prdk__kcqtx)
            niy__tey = decode_utf8(stuu__ufgdc, cehh__cqlqi)
            return niy__tey
        return str_arr_getitem_impl
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:

        def bool_impl(A, ind):
            ind = bodo.utils.conversion.coerce_to_ndarray(ind)
            alhux__pqj = len(A)
            n_strs = 0
            n_chars = 0
            for i in range(alhux__pqj):
                if not bodo.libs.array_kernels.isna(ind, i) and ind[i]:
                    n_strs += 1
                    n_chars += get_str_arr_item_length(A, i)
            out_arr = pre_alloc_string_array(n_strs, n_chars)
            dhvjc__sqybj = get_data_ptr(out_arr).data
            xdqsq__xec = get_data_ptr(A).data
            nolp__jxqt = 0
            ipt__hatl = 0
            setitem_str_offset(out_arr, 0, 0)
            for i in range(alhux__pqj):
                if not bodo.libs.array_kernels.isna(ind, i) and ind[i]:
                    wqg__nypiz = get_str_arr_item_length(A, i)
                    if wqg__nypiz == 1:
                        copy_single_char(dhvjc__sqybj, ipt__hatl,
                            xdqsq__xec, getitem_str_offset(A, i))
                    else:
                        memcpy_region(dhvjc__sqybj, ipt__hatl, xdqsq__xec,
                            getitem_str_offset(A, i), wqg__nypiz, 1)
                    ipt__hatl += wqg__nypiz
                    setitem_str_offset(out_arr, nolp__jxqt + 1, ipt__hatl)
                    if str_arr_is_na(A, i):
                        str_arr_set_na(out_arr, nolp__jxqt)
                    else:
                        str_arr_set_not_na(out_arr, nolp__jxqt)
                    nolp__jxqt += 1
            return out_arr
        return bool_impl
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def str_arr_arr_impl(A, ind):
            alhux__pqj = len(ind)
            out_arr = pre_alloc_string_array(alhux__pqj, -1)
            nolp__jxqt = 0
            for i in range(alhux__pqj):
                vwbny__ikl = A[ind[i]]
                out_arr[nolp__jxqt] = vwbny__ikl
                if str_arr_is_na(A, ind[i]):
                    str_arr_set_na(out_arr, nolp__jxqt)
                nolp__jxqt += 1
            return out_arr
        return str_arr_arr_impl
    if isinstance(ind, types.SliceType):

        def str_arr_slice_impl(A, ind):
            alhux__pqj = len(A)
            vdqf__ndora = numba.cpython.unicode._normalize_slice(ind,
                alhux__pqj)
            kfkd__todc = numba.cpython.unicode._slice_span(vdqf__ndora)
            if vdqf__ndora.step == 1:
                prdk__kcqtx = getitem_str_offset(A, vdqf__ndora.start)
                ktj__leiw = getitem_str_offset(A, vdqf__ndora.stop)
                n_chars = ktj__leiw - prdk__kcqtx
                qxwa__sjmfl = pre_alloc_string_array(kfkd__todc, np.int64(
                    n_chars))
                for i in range(kfkd__todc):
                    qxwa__sjmfl[i] = A[vdqf__ndora.start + i]
                    if str_arr_is_na(A, vdqf__ndora.start + i):
                        str_arr_set_na(qxwa__sjmfl, i)
                return qxwa__sjmfl
            else:
                qxwa__sjmfl = pre_alloc_string_array(kfkd__todc, -1)
                for i in range(kfkd__todc):
                    qxwa__sjmfl[i] = A[vdqf__ndora.start + i * vdqf__ndora.step
                        ]
                    if str_arr_is_na(A, vdqf__ndora.start + i * vdqf__ndora
                        .step):
                        str_arr_set_na(qxwa__sjmfl, i)
                return qxwa__sjmfl
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
    wlp__sxi = (
        f'StringArray setitem with index {idx} and value {val} not supported yet.'
        )
    if isinstance(idx, types.Integer):
        if val != string_type:
            raise BodoError(wlp__sxi)
        kcii__xcvg = 4

        def impl_scalar(A, idx, val):
            ufvc__tiow = (val._length if val._is_ascii else kcii__xcvg *
                val._length)
            eptr__yzj = A._data
            prdk__kcqtx = np.int64(getitem_str_offset(A, idx))
            jtqvi__xkttj = prdk__kcqtx + ufvc__tiow
            bodo.libs.array_item_arr_ext.ensure_data_capacity(eptr__yzj,
                prdk__kcqtx, jtqvi__xkttj)
            setitem_string_array(get_offset_ptr(A), get_data_ptr(A),
                jtqvi__xkttj, val._data, val._length, val._kind, val.
                _is_ascii, idx)
            str_arr_set_not_na(A, idx)
            dummy_use(A)
            dummy_use(val)
        return impl_scalar
    if isinstance(idx, types.SliceType):
        if val == string_array_type:

            def impl_slice(A, idx, val):
                vdqf__ndora = numba.cpython.unicode._normalize_slice(idx,
                    len(A))
                zsf__yll = vdqf__ndora.start
                eptr__yzj = A._data
                prdk__kcqtx = np.int64(getitem_str_offset(A, zsf__yll))
                jtqvi__xkttj = prdk__kcqtx + np.int64(num_total_chars(val))
                bodo.libs.array_item_arr_ext.ensure_data_capacity(eptr__yzj,
                    prdk__kcqtx, jtqvi__xkttj)
                set_string_array_range(A, val, zsf__yll, prdk__kcqtx)
                odvho__uftw = 0
                for i in range(vdqf__ndora.start, vdqf__ndora.stop,
                    vdqf__ndora.step):
                    if str_arr_is_na(val, odvho__uftw):
                        str_arr_set_na(A, i)
                    else:
                        str_arr_set_not_na(A, i)
                    odvho__uftw += 1
            return impl_slice
        elif isinstance(val, types.List) and val.dtype == string_type:

            def impl_slice_list(A, idx, val):
                wkhw__ytez = str_list_to_array(val)
                A[idx] = wkhw__ytez
            return impl_slice_list
        elif val == string_type:

            def impl_slice(A, idx, val):
                vdqf__ndora = numba.cpython.unicode._normalize_slice(idx,
                    len(A))
                for i in range(vdqf__ndora.start, vdqf__ndora.stop,
                    vdqf__ndora.step):
                    A[i] = val
            return impl_slice
        else:
            raise BodoError(wlp__sxi)
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        if val == string_type:

            def impl_bool_scalar(A, idx, val):
                alhux__pqj = len(A)
                idx = bodo.utils.conversion.coerce_to_ndarray(idx)
                out_arr = pre_alloc_string_array(alhux__pqj, -1)
                for i in numba.parfors.parfor.internal_prange(alhux__pqj):
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
                alhux__pqj = len(A)
                idx = bodo.utils.conversion.coerce_to_array(idx,
                    use_nullable_array=True)
                out_arr = pre_alloc_string_array(alhux__pqj, -1)
                jvrm__uasli = 0
                for i in numba.parfors.parfor.internal_prange(alhux__pqj):
                    if not bodo.libs.array_kernels.isna(idx, i) and idx[i]:
                        if bodo.libs.array_kernels.isna(val, jvrm__uasli):
                            out_arr[i] = ''
                            str_arr_set_na(out_arr, jvrm__uasli)
                        else:
                            out_arr[i] = str(val[jvrm__uasli])
                        jvrm__uasli += 1
                    elif bodo.libs.array_kernels.isna(A, i):
                        out_arr[i] = ''
                        str_arr_set_na(out_arr, i)
                    else:
                        get_str_arr_item_copy(out_arr, i, A, i)
                move_str_binary_arr_payload(A, out_arr)
            return impl_bool_arr
        else:
            raise BodoError(wlp__sxi)
    raise BodoError(wlp__sxi)


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
    gqt__uugck = parse_dtype(dtype, 'StringArray.astype')
    if not isinstance(gqt__uugck, (types.Float, types.Integer)):
        raise BodoError('invalid dtype in StringArray.astype()')
    if isinstance(gqt__uugck, types.Float):

        def impl_float(A, dtype, copy=True):
            numba.parfors.parfor.init_prange()
            alhux__pqj = len(A)
            B = np.empty(alhux__pqj, gqt__uugck)
            for i in numba.parfors.parfor.internal_prange(alhux__pqj):
                if bodo.libs.array_kernels.isna(A, i):
                    B[i] = np.nan
                else:
                    B[i] = float(A[i])
            return B
        return impl_float
    else:

        def impl_int(A, dtype, copy=True):
            numba.parfors.parfor.init_prange()
            alhux__pqj = len(A)
            B = np.empty(alhux__pqj, gqt__uugck)
            for i in numba.parfors.parfor.internal_prange(alhux__pqj):
                B[i] = int(A[i])
            return B
        return impl_int


@intrinsic
def decode_utf8(typingctx, ptr_t, len_t=None):

    def codegen(context, builder, sig, args):
        stuu__ufgdc, cehh__cqlqi = args
        gkl__anspz = context.get_python_api(builder)
        iwm__wush = gkl__anspz.string_from_string_and_size(stuu__ufgdc,
            cehh__cqlqi)
        fglrt__zafmb = gkl__anspz.to_native_value(string_type, iwm__wush).value
        njgr__hjxo = cgutils.create_struct_proxy(string_type)(context,
            builder, fglrt__zafmb)
        njgr__hjxo.hash = njgr__hjxo.hash.type(-1)
        gkl__anspz.decref(iwm__wush)
        return njgr__hjxo._getvalue()
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
        ecs__oahrp, arr, ind, lym__enoz = args
        vgwep__flvow = _get_str_binary_arr_payload(context, builder, arr,
            string_array_type)
        offsets = context.make_helper(builder, offset_arr_type,
            vgwep__flvow.offsets).data
        data = context.make_helper(builder, char_arr_type, vgwep__flvow.data
            ).data
        fygnz__dbqps = lir.FunctionType(lir.IntType(32), [ecs__oahrp.type,
            lir.IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(64)])
        yodp__zersr = 'str_arr_to_int64'
        if sig.args[3].dtype == types.float64:
            yodp__zersr = 'str_arr_to_float64'
        else:
            assert sig.args[3].dtype == types.int64
        ouq__vhbs = cgutils.get_or_insert_function(builder.module,
            fygnz__dbqps, yodp__zersr)
        return builder.call(ouq__vhbs, [ecs__oahrp, offsets, data, ind])
    return types.int32(out_ptr_t, string_array_type, types.int64, out_dtype_t
        ), codegen


@unbox(BinaryArrayType)
@unbox(StringArrayType)
def unbox_str_series(typ, val, c):
    osse__xfw = c.context.get_constant(types.int32, int(typ ==
        binary_array_type))
    fygnz__dbqps = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
        IntType(8).as_pointer(), lir.IntType(32)])
    tvbm__seusd = cgutils.get_or_insert_function(c.builder.module,
        fygnz__dbqps, name='string_array_from_sequence')
    wrtl__lsxs = c.builder.call(tvbm__seusd, [val, osse__xfw])
    xuu__szbt = ArrayItemArrayType(char_arr_type)
    gwf__eiwzp = c.context.make_helper(c.builder, xuu__szbt)
    gwf__eiwzp.meminfo = wrtl__lsxs
    qntos__rafa = c.context.make_helper(c.builder, typ)
    eptr__yzj = gwf__eiwzp._getvalue()
    qntos__rafa.data = eptr__yzj
    tgmgk__huf = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(qntos__rafa._getvalue(), is_error=tgmgk__huf)


@lower_constant(BinaryArrayType)
@lower_constant(StringArrayType)
def lower_constant_str_arr(context, builder, typ, pyval):
    alhux__pqj = len(pyval)
    ipt__hatl = 0
    fgqsz__mez = np.empty(alhux__pqj + 1, np_offset_type)
    bvvd__afh = []
    ggo__lxd = np.empty(alhux__pqj + 7 >> 3, np.uint8)
    for i, s in enumerate(pyval):
        fgqsz__mez[i] = ipt__hatl
        wngyk__choa = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(ggo__lxd, i, int(not wngyk__choa))
        if wngyk__choa:
            continue
        tjrsm__sxk = list(s.encode()) if isinstance(s, str) else list(s)
        bvvd__afh.extend(tjrsm__sxk)
        ipt__hatl += len(tjrsm__sxk)
    fgqsz__mez[alhux__pqj] = ipt__hatl
    prfn__zuf = np.array(bvvd__afh, np.uint8)
    bvud__qrjtq = context.get_constant(types.int64, alhux__pqj)
    zegk__yabh = context.get_constant_generic(builder, char_arr_type, prfn__zuf
        )
    yyaow__rdf = context.get_constant_generic(builder, offset_arr_type,
        fgqsz__mez)
    hkb__iclsl = context.get_constant_generic(builder, null_bitmap_arr_type,
        ggo__lxd)
    vgwep__flvow = lir.Constant.literal_struct([bvud__qrjtq, zegk__yabh,
        yyaow__rdf, hkb__iclsl])
    vgwep__flvow = cgutils.global_constant(builder, '.const.payload',
        vgwep__flvow).bitcast(cgutils.voidptr_t)
    oso__vzco = context.get_constant(types.int64, -1)
    cdjpc__tkb = context.get_constant_null(types.voidptr)
    yph__ztc = lir.Constant.literal_struct([oso__vzco, cdjpc__tkb,
        cdjpc__tkb, vgwep__flvow, oso__vzco])
    yph__ztc = cgutils.global_constant(builder, '.const.meminfo', yph__ztc
        ).bitcast(cgutils.voidptr_t)
    eptr__yzj = lir.Constant.literal_struct([yph__ztc])
    qntos__rafa = lir.Constant.literal_struct([eptr__yzj])
    return qntos__rafa


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
