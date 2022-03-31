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
        yvsmn__csx = ArrayItemArrayType(char_arr_type)
        kxzrw__xdb = [('data', yvsmn__csx)]
        models.StructModel.__init__(self, dmm, fe_type, kxzrw__xdb)


make_attribute_wrapper(StringArrayType, 'data', '_data')
make_attribute_wrapper(BinaryArrayType, 'data', '_data')
lower_builtin('getiter', string_array_type)(numba.np.arrayobj.getiter_array)


@intrinsic
def init_str_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, ArrayItemArrayType
        ) and data_typ.dtype == types.Array(char_type, 1, 'C')

    def codegen(context, builder, sig, args):
        sobff__mxs, = args
        gazfg__lggv = context.make_helper(builder, string_array_type)
        gazfg__lggv.data = sobff__mxs
        context.nrt.incref(builder, data_typ, sobff__mxs)
        return gazfg__lggv._getvalue()
    return string_array_type(data_typ), codegen


class StringDtype(types.Number):

    def __init__(self):
        super(StringDtype, self).__init__('StringDtype')


string_dtype = StringDtype()
register_model(StringDtype)(models.OpaqueModel)


@box(StringDtype)
def box_string_dtype(typ, val, c):
    wxpe__lft = c.context.insert_const_string(c.builder.module, 'pandas')
    rnvde__fossj = c.pyapi.import_module_noblock(wxpe__lft)
    whxk__nbc = c.pyapi.call_method(rnvde__fossj, 'StringDtype', ())
    c.pyapi.decref(rnvde__fossj)
    return whxk__nbc


@unbox(StringDtype)
def unbox_string_dtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


typeof_impl.register(pd.StringDtype)(lambda a, b: string_dtype)
type_callable(pd.StringDtype)(lambda c: lambda : string_dtype)
lower_builtin(pd.StringDtype)(lambda c, b, s, a: c.get_dummy_value())


def create_binary_op_overload(op):

    def overload_string_array_binary_op(lhs, rhs):
        uui__xrew = bodo.libs.dict_arr_ext.get_binary_op_overload(op, lhs, rhs)
        if uui__xrew is not None:
            return uui__xrew
        if is_str_arr_type(lhs) and is_str_arr_type(rhs):

            def impl_both(lhs, rhs):
                numba.parfors.parfor.init_prange()
                iai__tjc = len(lhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(iai__tjc)
                for i in numba.parfors.parfor.internal_prange(iai__tjc):
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
                iai__tjc = len(lhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(iai__tjc)
                for i in numba.parfors.parfor.internal_prange(iai__tjc):
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
                iai__tjc = len(rhs)
                out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(iai__tjc)
                for i in numba.parfors.parfor.internal_prange(iai__tjc):
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
    wfzmj__yvyit = is_str_arr_type(lhs) or isinstance(lhs, types.Array
        ) and lhs.dtype == string_type
    smw__yarko = is_str_arr_type(rhs) or isinstance(rhs, types.Array
        ) and rhs.dtype == string_type
    if is_str_arr_type(lhs) and smw__yarko or wfzmj__yvyit and is_str_arr_type(
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
    sla__zqcyl = context.make_helper(builder, arr_typ, arr_value)
    yvsmn__csx = ArrayItemArrayType(char_arr_type)
    plhle__yfld = _get_array_item_arr_payload(context, builder, yvsmn__csx,
        sla__zqcyl.data)
    return plhle__yfld


@intrinsic
def num_strings(typingctx, str_arr_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        return plhle__yfld.n_arrays
    return types.int64(string_array_type), codegen


def _get_num_total_chars(builder, offsets, num_strings):
    return builder.zext(builder.load(builder.gep(offsets, [num_strings])),
        lir.IntType(64))


@intrinsic
def num_total_chars(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        ruuu__dnkyq = context.make_helper(builder, offset_arr_type,
            plhle__yfld.offsets).data
        return _get_num_total_chars(builder, ruuu__dnkyq, plhle__yfld.n_arrays)
    return types.uint64(in_arr_typ), codegen


@intrinsic
def get_offset_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        liuj__doc = context.make_helper(builder, offset_arr_type,
            plhle__yfld.offsets)
        btnd__mlcdb = context.make_helper(builder, offset_ctypes_type)
        btnd__mlcdb.data = builder.bitcast(liuj__doc.data, lir.IntType(
            offset_type.bitwidth).as_pointer())
        btnd__mlcdb.meminfo = liuj__doc.meminfo
        whxk__nbc = btnd__mlcdb._getvalue()
        return impl_ret_borrowed(context, builder, offset_ctypes_type,
            whxk__nbc)
    return offset_ctypes_type(in_arr_typ), codegen


@intrinsic
def get_data_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        sobff__mxs = context.make_helper(builder, char_arr_type,
            plhle__yfld.data)
        btnd__mlcdb = context.make_helper(builder, data_ctypes_type)
        btnd__mlcdb.data = sobff__mxs.data
        btnd__mlcdb.meminfo = sobff__mxs.meminfo
        whxk__nbc = btnd__mlcdb._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type, whxk__nbc)
    return data_ctypes_type(in_arr_typ), codegen


@intrinsic
def get_data_ptr_ind(typingctx, in_arr_typ, int_t=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        zuzpg__yafs, ind = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            zuzpg__yafs, sig.args[0])
        sobff__mxs = context.make_helper(builder, char_arr_type,
            plhle__yfld.data)
        btnd__mlcdb = context.make_helper(builder, data_ctypes_type)
        btnd__mlcdb.data = builder.gep(sobff__mxs.data, [ind])
        btnd__mlcdb.meminfo = sobff__mxs.meminfo
        whxk__nbc = btnd__mlcdb._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type, whxk__nbc)
    return data_ctypes_type(in_arr_typ, types.intp), codegen


@intrinsic
def copy_single_char(typingctx, dst_ptr_t, dst_ind_t, src_ptr_t, src_ind_t=None
    ):

    def codegen(context, builder, sig, args):
        yyvt__xtfm, uoi__xgvld, bmxn__aqdw, tpsj__smo = args
        tfngl__pbel = builder.bitcast(builder.gep(yyvt__xtfm, [uoi__xgvld]),
            lir.IntType(8).as_pointer())
        eghd__sqf = builder.bitcast(builder.gep(bmxn__aqdw, [tpsj__smo]),
            lir.IntType(8).as_pointer())
        wjdrf__yzala = builder.load(eghd__sqf)
        builder.store(wjdrf__yzala, tfngl__pbel)
        return context.get_dummy_value()
    return types.void(types.voidptr, types.intp, types.voidptr, types.intp
        ), codegen


@intrinsic
def get_null_bitmap_ptr(typingctx, in_arr_typ=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        dyks__nkjfz = context.make_helper(builder, null_bitmap_arr_type,
            plhle__yfld.null_bitmap)
        btnd__mlcdb = context.make_helper(builder, data_ctypes_type)
        btnd__mlcdb.data = dyks__nkjfz.data
        btnd__mlcdb.meminfo = dyks__nkjfz.meminfo
        whxk__nbc = btnd__mlcdb._getvalue()
        return impl_ret_borrowed(context, builder, data_ctypes_type, whxk__nbc)
    return data_ctypes_type(in_arr_typ), codegen


@intrinsic
def getitem_str_offset(typingctx, in_arr_typ, ind_t=None):
    assert in_arr_typ in [binary_array_type, string_array_type]

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        ruuu__dnkyq = context.make_helper(builder, offset_arr_type,
            plhle__yfld.offsets).data
        return builder.load(builder.gep(ruuu__dnkyq, [ind]))
    return offset_type(in_arr_typ, ind_t), codegen


@intrinsic
def setitem_str_offset(typingctx, str_arr_typ, ind_t, val_t=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind, val = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        offsets = context.make_helper(builder, offset_arr_type, plhle__yfld
            .offsets).data
        builder.store(val, builder.gep(offsets, [ind]))
        return context.get_dummy_value()
    return types.void(string_array_type, ind_t, offset_type), codegen


@intrinsic
def getitem_str_bitmap(typingctx, in_bitmap_typ, ind_t=None):

    def codegen(context, builder, sig, args):
        uct__psvg, ind = args
        if in_bitmap_typ == data_ctypes_type:
            btnd__mlcdb = context.make_helper(builder, data_ctypes_type,
                uct__psvg)
            uct__psvg = btnd__mlcdb.data
        return builder.load(builder.gep(uct__psvg, [ind]))
    return char_type(in_bitmap_typ, ind_t), codegen


@intrinsic
def setitem_str_bitmap(typingctx, in_bitmap_typ, ind_t, val_t=None):

    def codegen(context, builder, sig, args):
        uct__psvg, ind, val = args
        if in_bitmap_typ == data_ctypes_type:
            btnd__mlcdb = context.make_helper(builder, data_ctypes_type,
                uct__psvg)
            uct__psvg = btnd__mlcdb.data
        builder.store(val, builder.gep(uct__psvg, [ind]))
        return context.get_dummy_value()
    return types.void(in_bitmap_typ, ind_t, char_type), codegen


@intrinsic
def copy_str_arr_slice(typingctx, out_str_arr_typ, in_str_arr_typ, ind_t=None):
    assert out_str_arr_typ == string_array_type and in_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr, ind = args
        qnqhw__yxx = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        xud__wxd = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        alizl__ctydl = context.make_helper(builder, offset_arr_type,
            qnqhw__yxx.offsets).data
        dzxc__nwzu = context.make_helper(builder, offset_arr_type, xud__wxd
            .offsets).data
        tsg__zrpvb = context.make_helper(builder, char_arr_type, qnqhw__yxx
            .data).data
        rborq__dqn = context.make_helper(builder, char_arr_type, xud__wxd.data
            ).data
        wlus__hvt = context.make_helper(builder, null_bitmap_arr_type,
            qnqhw__yxx.null_bitmap).data
        ujtw__ogb = context.make_helper(builder, null_bitmap_arr_type,
            xud__wxd.null_bitmap).data
        zkchq__xlkdo = builder.add(ind, context.get_constant(types.intp, 1))
        cgutils.memcpy(builder, dzxc__nwzu, alizl__ctydl, zkchq__xlkdo)
        cgutils.memcpy(builder, rborq__dqn, tsg__zrpvb, builder.load(
            builder.gep(alizl__ctydl, [ind])))
        dgq__idsyo = builder.add(ind, lir.Constant(lir.IntType(64), 7))
        hfkil__frbs = builder.lshr(dgq__idsyo, lir.Constant(lir.IntType(64), 3)
            )
        cgutils.memcpy(builder, ujtw__ogb, wlus__hvt, hfkil__frbs)
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type, ind_t), codegen


@intrinsic
def copy_data(typingctx, str_arr_typ, out_str_arr_typ=None):
    assert str_arr_typ == string_array_type and out_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr = args
        qnqhw__yxx = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        xud__wxd = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        alizl__ctydl = context.make_helper(builder, offset_arr_type,
            qnqhw__yxx.offsets).data
        tsg__zrpvb = context.make_helper(builder, char_arr_type, qnqhw__yxx
            .data).data
        rborq__dqn = context.make_helper(builder, char_arr_type, xud__wxd.data
            ).data
        num_total_chars = _get_num_total_chars(builder, alizl__ctydl,
            qnqhw__yxx.n_arrays)
        cgutils.memcpy(builder, rborq__dqn, tsg__zrpvb, num_total_chars)
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type), codegen


@intrinsic
def copy_non_null_offsets(typingctx, str_arr_typ, out_str_arr_typ=None):
    assert str_arr_typ == string_array_type and out_str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        out_str_arr, in_str_arr = args
        qnqhw__yxx = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        xud__wxd = _get_str_binary_arr_payload(context, builder,
            out_str_arr, string_array_type)
        alizl__ctydl = context.make_helper(builder, offset_arr_type,
            qnqhw__yxx.offsets).data
        dzxc__nwzu = context.make_helper(builder, offset_arr_type, xud__wxd
            .offsets).data
        wlus__hvt = context.make_helper(builder, null_bitmap_arr_type,
            qnqhw__yxx.null_bitmap).data
        iai__tjc = qnqhw__yxx.n_arrays
        zooth__yie = context.get_constant(offset_type, 0)
        roe__lgl = cgutils.alloca_once_value(builder, zooth__yie)
        with cgutils.for_range(builder, iai__tjc) as rrd__jvz:
            wsfji__yrzqv = lower_is_na(context, builder, wlus__hvt,
                rrd__jvz.index)
            with cgutils.if_likely(builder, builder.not_(wsfji__yrzqv)):
                fyjvk__fkcmu = builder.load(builder.gep(alizl__ctydl, [
                    rrd__jvz.index]))
                vdtud__qdt = builder.load(roe__lgl)
                builder.store(fyjvk__fkcmu, builder.gep(dzxc__nwzu, [
                    vdtud__qdt]))
                builder.store(builder.add(vdtud__qdt, lir.Constant(context.
                    get_value_type(offset_type), 1)), roe__lgl)
        vdtud__qdt = builder.load(roe__lgl)
        fyjvk__fkcmu = builder.load(builder.gep(alizl__ctydl, [iai__tjc]))
        builder.store(fyjvk__fkcmu, builder.gep(dzxc__nwzu, [vdtud__qdt]))
        return context.get_dummy_value()
    return types.void(string_array_type, string_array_type), codegen


@intrinsic
def str_copy(typingctx, buff_arr_typ, ind_typ, str_typ, len_typ=None):

    def codegen(context, builder, sig, args):
        axnwa__mugw, ind, str, lgyvn__vdfvn = args
        axnwa__mugw = context.make_array(sig.args[0])(context, builder,
            axnwa__mugw)
        maf__rtihz = builder.gep(axnwa__mugw.data, [ind])
        cgutils.raw_memcpy(builder, maf__rtihz, str, lgyvn__vdfvn, 1)
        return context.get_dummy_value()
    return types.void(null_bitmap_arr_type, types.intp, types.voidptr,
        types.intp), codegen


@intrinsic
def str_copy_ptr(typingctx, ptr_typ, ind_typ, str_typ, len_typ=None):

    def codegen(context, builder, sig, args):
        maf__rtihz, ind, vjor__pckyv, lgyvn__vdfvn = args
        maf__rtihz = builder.gep(maf__rtihz, [ind])
        cgutils.raw_memcpy(builder, maf__rtihz, vjor__pckyv, lgyvn__vdfvn, 1)
        return context.get_dummy_value()
    return types.void(types.voidptr, types.intp, types.voidptr, types.intp
        ), codegen


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_length(A, i):
    return np.int64(getitem_str_offset(A, i + 1) - getitem_str_offset(A, i))


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_str_length(A, i):
    bqnsh__xwjt = np.int64(getitem_str_offset(A, i))
    gur__mauss = np.int64(getitem_str_offset(A, i + 1))
    l = gur__mauss - bqnsh__xwjt
    yqehl__tfmw = get_data_ptr_ind(A, bqnsh__xwjt)
    for j in range(l):
        if bodo.hiframes.split_impl.getitem_c_arr(yqehl__tfmw, j) >= 128:
            return len(A[i])
    return l


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_ptr(A, i):
    return get_data_ptr_ind(A, getitem_str_offset(A, i))


@numba.njit(no_cpython_wrapper=True)
def get_str_arr_item_copy(B, j, A, i):
    if j == 0:
        setitem_str_offset(B, 0, 0)
    zjtc__lfel = getitem_str_offset(A, i)
    dbda__avc = getitem_str_offset(A, i + 1)
    ydxkg__tamnr = dbda__avc - zjtc__lfel
    onzmi__knp = getitem_str_offset(B, j)
    ttnrc__drdk = onzmi__knp + ydxkg__tamnr
    setitem_str_offset(B, j + 1, ttnrc__drdk)
    if str_arr_is_na(A, i):
        str_arr_set_na(B, j)
    else:
        str_arr_set_not_na(B, j)
    if ydxkg__tamnr != 0:
        sobff__mxs = B._data
        bodo.libs.array_item_arr_ext.ensure_data_capacity(sobff__mxs, np.
            int64(onzmi__knp), np.int64(ttnrc__drdk))
        bqp__stl = get_data_ptr(B).data
        qmxld__hgqwh = get_data_ptr(A).data
        memcpy_region(bqp__stl, onzmi__knp, qmxld__hgqwh, zjtc__lfel,
            ydxkg__tamnr, 1)


@numba.njit(no_cpython_wrapper=True)
def get_str_null_bools(str_arr):
    iai__tjc = len(str_arr)
    cvxd__zwua = np.empty(iai__tjc, np.bool_)
    for i in range(iai__tjc):
        cvxd__zwua[i] = bodo.libs.array_kernels.isna(str_arr, i)
    return cvxd__zwua


def to_list_if_immutable_arr(arr, str_null_bools=None):
    return arr


@overload(to_list_if_immutable_arr, no_unliteral=True)
def to_list_if_immutable_arr_overload(data, str_null_bools=None):
    if is_str_arr_type(data) or data == binary_array_type:

        def to_list_impl(data, str_null_bools=None):
            iai__tjc = len(data)
            l = []
            for i in range(iai__tjc):
                l.append(data[i])
            return l
        return to_list_impl
    if isinstance(data, types.BaseTuple):
        dkkl__yqg = data.count
        iamv__tvds = ['to_list_if_immutable_arr(data[{}])'.format(i) for i in
            range(dkkl__yqg)]
        if is_overload_true(str_null_bools):
            iamv__tvds += ['get_str_null_bools(data[{}])'.format(i) for i in
                range(dkkl__yqg) if is_str_arr_type(data.types[i]) or data.
                types[i] == binary_array_type]
        vqpbl__jmtf = 'def f(data, str_null_bools=None):\n'
        vqpbl__jmtf += '  return ({}{})\n'.format(', '.join(iamv__tvds), 
            ',' if dkkl__yqg == 1 else '')
        wiz__ddvmd = {}
        exec(vqpbl__jmtf, {'to_list_if_immutable_arr':
            to_list_if_immutable_arr, 'get_str_null_bools':
            get_str_null_bools, 'bodo': bodo}, wiz__ddvmd)
        urfot__jwk = wiz__ddvmd['f']
        return urfot__jwk
    return lambda data, str_null_bools=None: data


def cp_str_list_to_array(str_arr, str_list, str_null_bools=None):
    return


@overload(cp_str_list_to_array, no_unliteral=True)
def cp_str_list_to_array_overload(str_arr, list_data, str_null_bools=None):
    if str_arr == string_array_type:
        if is_overload_none(str_null_bools):

            def cp_str_list_impl(str_arr, list_data, str_null_bools=None):
                iai__tjc = len(list_data)
                for i in range(iai__tjc):
                    vjor__pckyv = list_data[i]
                    str_arr[i] = vjor__pckyv
            return cp_str_list_impl
        else:

            def cp_str_list_impl_null(str_arr, list_data, str_null_bools=None):
                iai__tjc = len(list_data)
                for i in range(iai__tjc):
                    vjor__pckyv = list_data[i]
                    str_arr[i] = vjor__pckyv
                    if str_null_bools[i]:
                        str_arr_set_na(str_arr, i)
                    else:
                        str_arr_set_not_na(str_arr, i)
            return cp_str_list_impl_null
    if isinstance(str_arr, types.BaseTuple):
        dkkl__yqg = str_arr.count
        xwg__kut = 0
        vqpbl__jmtf = 'def f(str_arr, list_data, str_null_bools=None):\n'
        for i in range(dkkl__yqg):
            if is_overload_true(str_null_bools) and str_arr.types[i
                ] == string_array_type:
                vqpbl__jmtf += (
                    """  cp_str_list_to_array(str_arr[{}], list_data[{}], list_data[{}])
"""
                    .format(i, i, dkkl__yqg + xwg__kut))
                xwg__kut += 1
            else:
                vqpbl__jmtf += (
                    '  cp_str_list_to_array(str_arr[{}], list_data[{}])\n'.
                    format(i, i))
        vqpbl__jmtf += '  return\n'
        wiz__ddvmd = {}
        exec(vqpbl__jmtf, {'cp_str_list_to_array': cp_str_list_to_array},
            wiz__ddvmd)
        kov__iuc = wiz__ddvmd['f']
        return kov__iuc
    return lambda str_arr, list_data, str_null_bools=None: None


def str_list_to_array(str_list):
    return str_list


@overload(str_list_to_array, no_unliteral=True)
def str_list_to_array_overload(str_list):
    if isinstance(str_list, types.List) and str_list.dtype == bodo.string_type:

        def str_list_impl(str_list):
            iai__tjc = len(str_list)
            str_arr = pre_alloc_string_array(iai__tjc, -1)
            for i in range(iai__tjc):
                vjor__pckyv = str_list[i]
                str_arr[i] = vjor__pckyv
            return str_arr
        return str_list_impl
    return lambda str_list: str_list


def get_num_total_chars(A):
    pass


@overload(get_num_total_chars)
def overload_get_num_total_chars(A):
    if isinstance(A, types.List) and A.dtype == string_type:

        def str_list_impl(A):
            iai__tjc = len(A)
            ydgn__fptu = 0
            for i in range(iai__tjc):
                vjor__pckyv = A[i]
                ydgn__fptu += get_utf8_size(vjor__pckyv)
            return ydgn__fptu
        return str_list_impl
    assert A == string_array_type
    return lambda A: num_total_chars(A)


@overload_method(StringArrayType, 'copy', no_unliteral=True)
def str_arr_copy_overload(arr):

    def copy_impl(arr):
        iai__tjc = len(arr)
        n_chars = num_total_chars(arr)
        zlwgq__gtufw = pre_alloc_string_array(iai__tjc, np.int64(n_chars))
        copy_str_arr_slice(zlwgq__gtufw, arr, iai__tjc)
        return zlwgq__gtufw
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
    vqpbl__jmtf = 'def f(in_seq):\n'
    vqpbl__jmtf += '    n_strs = len(in_seq)\n'
    vqpbl__jmtf += '    A = pre_alloc_string_array(n_strs, -1)\n'
    vqpbl__jmtf += '    return A\n'
    wiz__ddvmd = {}
    exec(vqpbl__jmtf, {'pre_alloc_string_array': pre_alloc_string_array},
        wiz__ddvmd)
    pgvn__jnlth = wiz__ddvmd['f']
    return pgvn__jnlth


@numba.generated_jit(nopython=True)
def str_arr_from_sequence(in_seq):
    if in_seq.dtype == bodo.bytes_type:
        mvr__ochg = 'pre_alloc_binary_array'
    else:
        mvr__ochg = 'pre_alloc_string_array'
    vqpbl__jmtf = 'def f(in_seq):\n'
    vqpbl__jmtf += '    n_strs = len(in_seq)\n'
    vqpbl__jmtf += f'    A = {mvr__ochg}(n_strs, -1)\n'
    vqpbl__jmtf += '    for i in range(n_strs):\n'
    vqpbl__jmtf += '        A[i] = in_seq[i]\n'
    vqpbl__jmtf += '    return A\n'
    wiz__ddvmd = {}
    exec(vqpbl__jmtf, {'pre_alloc_string_array': pre_alloc_string_array,
        'pre_alloc_binary_array': pre_alloc_binary_array}, wiz__ddvmd)
    pgvn__jnlth = wiz__ddvmd['f']
    return pgvn__jnlth


@intrinsic
def set_all_offsets_to_0(typingctx, arr_typ=None):
    assert arr_typ in (string_array_type, binary_array_type
        ), 'set_all_offsets_to_0 requires a string or binary array'

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        ctrbl__zdol = builder.add(plhle__yfld.n_arrays, lir.Constant(lir.
            IntType(64), 1))
        ihezx__dur = builder.lshr(lir.Constant(lir.IntType(64), offset_type
            .bitwidth), lir.Constant(lir.IntType(64), 3))
        hfkil__frbs = builder.mul(ctrbl__zdol, ihezx__dur)
        xnh__ayd = context.make_array(offset_arr_type)(context, builder,
            plhle__yfld.offsets).data
        cgutils.memset(builder, xnh__ayd, hfkil__frbs, 0)
        return context.get_dummy_value()
    return types.none(arr_typ), codegen


@intrinsic
def set_bitmap_all_NA(typingctx, arr_typ=None):
    assert arr_typ in (string_array_type, binary_array_type
        ), 'set_bitmap_all_NA requires a string or binary array'

    def codegen(context, builder, sig, args):
        in_str_arr, = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            in_str_arr, sig.args[0])
        cso__trlks = plhle__yfld.n_arrays
        hfkil__frbs = builder.lshr(builder.add(cso__trlks, lir.Constant(lir
            .IntType(64), 7)), lir.Constant(lir.IntType(64), 3))
        ttqom__nuzp = context.make_array(null_bitmap_arr_type)(context,
            builder, plhle__yfld.null_bitmap).data
        cgutils.memset(builder, ttqom__nuzp, hfkil__frbs, 0)
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
    eiho__drnx = 0
    if total_len == 0:
        for i in range(len(offsets)):
            offsets[i] = 0
    else:
        abim__dxx = len(len_arr)
        for i in range(abim__dxx):
            offsets[i] = eiho__drnx
            eiho__drnx += len_arr[i]
        offsets[abim__dxx] = eiho__drnx
    return str_arr


kBitmask = np.array([1, 2, 4, 8, 16, 32, 64, 128], dtype=np.uint8)


@numba.njit
def set_bit_to(bits, i, bit_is_set):
    pef__irk = i // 8
    fpweg__haldj = getitem_str_bitmap(bits, pef__irk)
    fpweg__haldj ^= np.uint8(-np.uint8(bit_is_set) ^ fpweg__haldj) & kBitmask[
        i % 8]
    setitem_str_bitmap(bits, pef__irk, fpweg__haldj)


@numba.njit
def get_bit_bitmap(bits, i):
    return getitem_str_bitmap(bits, i >> 3) >> (i & 7) & 1


@numba.njit
def copy_nulls_range(out_str_arr, in_str_arr, out_start):
    savw__vdlys = get_null_bitmap_ptr(out_str_arr)
    yrrhi__jzt = get_null_bitmap_ptr(in_str_arr)
    for j in range(len(in_str_arr)):
        llozy__uaqec = get_bit_bitmap(yrrhi__jzt, j)
        set_bit_to(savw__vdlys, out_start + j, llozy__uaqec)


@intrinsic
def set_string_array_range(typingctx, out_typ, in_typ, curr_str_typ,
    curr_chars_typ=None):
    assert out_typ == string_array_type and in_typ == string_array_type or out_typ == binary_array_type and in_typ == binary_array_type, 'set_string_array_range requires string or binary arrays'
    assert isinstance(curr_str_typ, types.Integer) and isinstance(
        curr_chars_typ, types.Integer
        ), 'set_string_array_range requires integer indices'

    def codegen(context, builder, sig, args):
        out_arr, zuzpg__yafs, unii__tuieu, ijyo__rukl = args
        qnqhw__yxx = _get_str_binary_arr_payload(context, builder,
            zuzpg__yafs, string_array_type)
        xud__wxd = _get_str_binary_arr_payload(context, builder, out_arr,
            string_array_type)
        alizl__ctydl = context.make_helper(builder, offset_arr_type,
            qnqhw__yxx.offsets).data
        dzxc__nwzu = context.make_helper(builder, offset_arr_type, xud__wxd
            .offsets).data
        tsg__zrpvb = context.make_helper(builder, char_arr_type, qnqhw__yxx
            .data).data
        rborq__dqn = context.make_helper(builder, char_arr_type, xud__wxd.data
            ).data
        num_total_chars = _get_num_total_chars(builder, alizl__ctydl,
            qnqhw__yxx.n_arrays)
        elf__ozcml = lir.FunctionType(lir.VoidType(), [lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(64), lir.IntType(64), lir.IntType(64),
            lir.IntType(64)])
        nzv__hnkfa = cgutils.get_or_insert_function(builder.module,
            elf__ozcml, name='set_string_array_range')
        builder.call(nzv__hnkfa, [dzxc__nwzu, rborq__dqn, alizl__ctydl,
            tsg__zrpvb, unii__tuieu, ijyo__rukl, qnqhw__yxx.n_arrays,
            num_total_chars])
        bxx__svrib = context.typing_context.resolve_value_type(copy_nulls_range
            )
        xwm__ycp = bxx__svrib.get_call_type(context.typing_context, (
            string_array_type, string_array_type, types.int64), {})
        clro__xdioa = context.get_function(bxx__svrib, xwm__ycp)
        clro__xdioa(builder, (out_arr, zuzpg__yafs, unii__tuieu))
        return context.get_dummy_value()
    sig = types.void(out_typ, in_typ, types.intp, types.intp)
    return sig, codegen


@box(BinaryArrayType)
@box(StringArrayType)
def box_str_arr(typ, val, c):
    assert typ in [binary_array_type, string_array_type]
    oyg__jmia = c.context.make_helper(c.builder, typ, val)
    yvsmn__csx = ArrayItemArrayType(char_arr_type)
    plhle__yfld = _get_array_item_arr_payload(c.context, c.builder,
        yvsmn__csx, oyg__jmia.data)
    mtguj__wvei = c.context.get_constant(types.int32, int(typ ==
        binary_array_type))
    lpj__odmb = 'np_array_from_string_array'
    if use_pd_string_array and typ != binary_array_type:
        lpj__odmb = 'pd_array_from_string_array'
    elf__ozcml = lir.FunctionType(c.context.get_argument_type(types.
        pyobject), [lir.IntType(64), lir.IntType(offset_type.bitwidth).
        as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
        as_pointer(), lir.IntType(32)])
    pxodj__moluv = cgutils.get_or_insert_function(c.builder.module,
        elf__ozcml, name=lpj__odmb)
    ruuu__dnkyq = c.context.make_array(offset_arr_type)(c.context, c.
        builder, plhle__yfld.offsets).data
    yqehl__tfmw = c.context.make_array(char_arr_type)(c.context, c.builder,
        plhle__yfld.data).data
    ttqom__nuzp = c.context.make_array(null_bitmap_arr_type)(c.context, c.
        builder, plhle__yfld.null_bitmap).data
    arr = c.builder.call(pxodj__moluv, [plhle__yfld.n_arrays, ruuu__dnkyq,
        yqehl__tfmw, ttqom__nuzp, mtguj__wvei])
    c.context.nrt.decref(c.builder, typ, val)
    return arr


@intrinsic
def str_arr_is_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        ttqom__nuzp = context.make_array(null_bitmap_arr_type)(context,
            builder, plhle__yfld.null_bitmap).data
        gbnqc__rxz = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        yhq__ccct = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        fpweg__haldj = builder.load(builder.gep(ttqom__nuzp, [gbnqc__rxz],
            inbounds=True))
        eakwu__oepiw = lir.ArrayType(lir.IntType(8), 8)
        yzjtc__cdt = cgutils.alloca_once_value(builder, lir.Constant(
            eakwu__oepiw, (1, 2, 4, 8, 16, 32, 64, 128)))
        gkflb__mbe = builder.load(builder.gep(yzjtc__cdt, [lir.Constant(lir
            .IntType(64), 0), yhq__ccct], inbounds=True))
        return builder.icmp_unsigned('==', builder.and_(fpweg__haldj,
            gkflb__mbe), lir.Constant(lir.IntType(8), 0))
    return types.bool_(str_arr_typ, types.intp), codegen


@intrinsic
def str_arr_set_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        gbnqc__rxz = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        yhq__ccct = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        ttqom__nuzp = context.make_array(null_bitmap_arr_type)(context,
            builder, plhle__yfld.null_bitmap).data
        offsets = context.make_helper(builder, offset_arr_type, plhle__yfld
            .offsets).data
        gwl__nnjjw = builder.gep(ttqom__nuzp, [gbnqc__rxz], inbounds=True)
        fpweg__haldj = builder.load(gwl__nnjjw)
        eakwu__oepiw = lir.ArrayType(lir.IntType(8), 8)
        yzjtc__cdt = cgutils.alloca_once_value(builder, lir.Constant(
            eakwu__oepiw, (1, 2, 4, 8, 16, 32, 64, 128)))
        gkflb__mbe = builder.load(builder.gep(yzjtc__cdt, [lir.Constant(lir
            .IntType(64), 0), yhq__ccct], inbounds=True))
        gkflb__mbe = builder.xor(gkflb__mbe, lir.Constant(lir.IntType(8), -1))
        builder.store(builder.and_(fpweg__haldj, gkflb__mbe), gwl__nnjjw)
        if str_arr_typ == string_array_type:
            wdho__cis = builder.add(ind, lir.Constant(lir.IntType(64), 1))
            jasea__giyls = builder.icmp_unsigned('!=', wdho__cis,
                plhle__yfld.n_arrays)
            with builder.if_then(jasea__giyls):
                builder.store(builder.load(builder.gep(offsets, [ind])),
                    builder.gep(offsets, [wdho__cis]))
        return context.get_dummy_value()
    return types.void(str_arr_typ, types.intp), codegen


@intrinsic
def str_arr_set_not_na(typingctx, str_arr_typ, ind_typ=None):
    assert str_arr_typ == string_array_type

    def codegen(context, builder, sig, args):
        in_str_arr, ind = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        gbnqc__rxz = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
        yhq__ccct = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
        ttqom__nuzp = context.make_array(null_bitmap_arr_type)(context,
            builder, plhle__yfld.null_bitmap).data
        gwl__nnjjw = builder.gep(ttqom__nuzp, [gbnqc__rxz], inbounds=True)
        fpweg__haldj = builder.load(gwl__nnjjw)
        eakwu__oepiw = lir.ArrayType(lir.IntType(8), 8)
        yzjtc__cdt = cgutils.alloca_once_value(builder, lir.Constant(
            eakwu__oepiw, (1, 2, 4, 8, 16, 32, 64, 128)))
        gkflb__mbe = builder.load(builder.gep(yzjtc__cdt, [lir.Constant(lir
            .IntType(64), 0), yhq__ccct], inbounds=True))
        builder.store(builder.or_(fpweg__haldj, gkflb__mbe), gwl__nnjjw)
        return context.get_dummy_value()
    return types.void(str_arr_typ, types.intp), codegen


@intrinsic
def set_null_bits_to_value(typingctx, arr_typ, value_typ=None):
    assert (arr_typ == string_array_type or arr_typ == binary_array_type
        ) and is_overload_constant_int(value_typ)

    def codegen(context, builder, sig, args):
        in_str_arr, value = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder,
            in_str_arr, string_array_type)
        hfkil__frbs = builder.udiv(builder.add(plhle__yfld.n_arrays, lir.
            Constant(lir.IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
        ttqom__nuzp = context.make_array(null_bitmap_arr_type)(context,
            builder, plhle__yfld.null_bitmap).data
        cgutils.memset(builder, ttqom__nuzp, hfkil__frbs, value)
        return context.get_dummy_value()
    return types.none(arr_typ, types.int8), codegen


def _get_str_binary_arr_data_payload_ptr(context, builder, str_arr):
    bzcj__dvbj = context.make_helper(builder, string_array_type, str_arr)
    yvsmn__csx = ArrayItemArrayType(char_arr_type)
    zuct__ubmt = context.make_helper(builder, yvsmn__csx, bzcj__dvbj.data)
    gbowv__gwjkl = ArrayItemArrayPayloadType(yvsmn__csx)
    fwhww__ows = context.nrt.meminfo_data(builder, zuct__ubmt.meminfo)
    kdra__osy = builder.bitcast(fwhww__ows, context.get_value_type(
        gbowv__gwjkl).as_pointer())
    return kdra__osy


@intrinsic
def move_str_binary_arr_payload(typingctx, to_arr_typ, from_arr_typ=None):
    assert to_arr_typ == string_array_type and from_arr_typ == string_array_type or to_arr_typ == binary_array_type and from_arr_typ == binary_array_type

    def codegen(context, builder, sig, args):
        rkwir__ekm, btl__fgua = args
        fni__vgtf = _get_str_binary_arr_data_payload_ptr(context, builder,
            btl__fgua)
        knz__tgqgv = _get_str_binary_arr_data_payload_ptr(context, builder,
            rkwir__ekm)
        xmd__qma = _get_str_binary_arr_payload(context, builder, btl__fgua,
            sig.args[1])
        yenqe__nhlvl = _get_str_binary_arr_payload(context, builder,
            rkwir__ekm, sig.args[0])
        context.nrt.incref(builder, char_arr_type, xmd__qma.data)
        context.nrt.incref(builder, offset_arr_type, xmd__qma.offsets)
        context.nrt.incref(builder, null_bitmap_arr_type, xmd__qma.null_bitmap)
        context.nrt.decref(builder, char_arr_type, yenqe__nhlvl.data)
        context.nrt.decref(builder, offset_arr_type, yenqe__nhlvl.offsets)
        context.nrt.decref(builder, null_bitmap_arr_type, yenqe__nhlvl.
            null_bitmap)
        builder.store(builder.load(fni__vgtf), knz__tgqgv)
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
        iai__tjc = _get_utf8_size(s._data, s._length, s._kind)
        dummy_use(s)
        return iai__tjc
    return impl


@intrinsic
def setitem_str_arr_ptr(typingctx, str_arr_t, ind_t, ptr_t, len_t=None):

    def codegen(context, builder, sig, args):
        arr, ind, maf__rtihz, zbik__ktq = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder, arr,
            sig.args[0])
        offsets = context.make_helper(builder, offset_arr_type, plhle__yfld
            .offsets).data
        data = context.make_helper(builder, char_arr_type, plhle__yfld.data
            ).data
        elf__ozcml = lir.FunctionType(lir.VoidType(), [lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(64),
            lir.IntType(32), lir.IntType(32), lir.IntType(64)])
        jtz__bwvkx = cgutils.get_or_insert_function(builder.module,
            elf__ozcml, name='setitem_string_array')
        ofltw__mfesp = context.get_constant(types.int32, -1)
        nzpsx__vlaws = context.get_constant(types.int32, 1)
        num_total_chars = _get_num_total_chars(builder, offsets,
            plhle__yfld.n_arrays)
        builder.call(jtz__bwvkx, [offsets, data, num_total_chars, builder.
            extract_value(maf__rtihz, 0), zbik__ktq, ofltw__mfesp,
            nzpsx__vlaws, ind])
        return context.get_dummy_value()
    return types.void(str_arr_t, ind_t, ptr_t, len_t), codegen


def lower_is_na(context, builder, bull_bitmap, ind):
    elf__ozcml = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
        as_pointer(), lir.IntType(64)])
    ngkxq__shxz = cgutils.get_or_insert_function(builder.module, elf__ozcml,
        name='is_na')
    return builder.call(ngkxq__shxz, [bull_bitmap, ind])


@intrinsic
def _memcpy(typingctx, dest_t, src_t, count_t, item_size_t=None):

    def codegen(context, builder, sig, args):
        tfngl__pbel, eghd__sqf, dkkl__yqg, mibzb__vem = args
        cgutils.raw_memcpy(builder, tfngl__pbel, eghd__sqf, dkkl__yqg,
            mibzb__vem)
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
        scbg__cse, uigcs__fhe = unicode_to_utf8_and_len(val)
        rzfrm__hbnpo = getitem_str_offset(A, ind)
        ggdd__swsf = getitem_str_offset(A, ind + 1)
        tjxj__gdr = ggdd__swsf - rzfrm__hbnpo
        if tjxj__gdr != uigcs__fhe:
            return False
        maf__rtihz = get_data_ptr_ind(A, rzfrm__hbnpo)
        return memcmp(maf__rtihz, scbg__cse, uigcs__fhe) == 0
    return impl


def str_arr_setitem_int_to_str(A, ind, value):
    A[ind] = str(value)


@overload(str_arr_setitem_int_to_str)
def overload_str_arr_setitem_int_to_str(A, ind, val):

    def impl(A, ind, val):
        rzfrm__hbnpo = getitem_str_offset(A, ind)
        tjxj__gdr = bodo.libs.str_ext.int_to_str_len(val)
        lyzfb__nbm = rzfrm__hbnpo + tjxj__gdr
        bodo.libs.array_item_arr_ext.ensure_data_capacity(A._data,
            rzfrm__hbnpo, lyzfb__nbm)
        maf__rtihz = get_data_ptr_ind(A, rzfrm__hbnpo)
        inplace_int64_to_str(maf__rtihz, tjxj__gdr, val)
        setitem_str_offset(A, ind + 1, rzfrm__hbnpo + tjxj__gdr)
        str_arr_set_not_na(A, ind)
    return impl


@intrinsic
def inplace_set_NA_str(typingctx, ptr_typ=None):

    def codegen(context, builder, sig, args):
        maf__rtihz, = args
        iydl__rmw = context.insert_const_string(builder.module, '<NA>')
        vcc__pws = lir.Constant(lir.IntType(64), len('<NA>'))
        cgutils.raw_memcpy(builder, maf__rtihz, iydl__rmw, vcc__pws, 1)
    return types.none(types.voidptr), codegen


def str_arr_setitem_NA_str(A, ind):
    A[ind] = '<NA>'


@overload(str_arr_setitem_NA_str)
def overload_str_arr_setitem_NA_str(A, ind):
    qhf__dfmi = len('<NA>')

    def impl(A, ind):
        rzfrm__hbnpo = getitem_str_offset(A, ind)
        lyzfb__nbm = rzfrm__hbnpo + qhf__dfmi
        bodo.libs.array_item_arr_ext.ensure_data_capacity(A._data,
            rzfrm__hbnpo, lyzfb__nbm)
        maf__rtihz = get_data_ptr_ind(A, rzfrm__hbnpo)
        inplace_set_NA_str(maf__rtihz)
        setitem_str_offset(A, ind + 1, rzfrm__hbnpo + qhf__dfmi)
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
            rzfrm__hbnpo = getitem_str_offset(A, ind)
            ggdd__swsf = getitem_str_offset(A, ind + 1)
            zbik__ktq = ggdd__swsf - rzfrm__hbnpo
            maf__rtihz = get_data_ptr_ind(A, rzfrm__hbnpo)
            kgjzf__sar = decode_utf8(maf__rtihz, zbik__ktq)
            return kgjzf__sar
        return str_arr_getitem_impl
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:

        def bool_impl(A, ind):
            ind = bodo.utils.conversion.coerce_to_ndarray(ind)
            iai__tjc = len(A)
            n_strs = 0
            n_chars = 0
            for i in range(iai__tjc):
                if not bodo.libs.array_kernels.isna(ind, i) and ind[i]:
                    n_strs += 1
                    n_chars += get_str_arr_item_length(A, i)
            out_arr = pre_alloc_string_array(n_strs, n_chars)
            bqp__stl = get_data_ptr(out_arr).data
            qmxld__hgqwh = get_data_ptr(A).data
            xwg__kut = 0
            vdtud__qdt = 0
            setitem_str_offset(out_arr, 0, 0)
            for i in range(iai__tjc):
                if not bodo.libs.array_kernels.isna(ind, i) and ind[i]:
                    nzm__iip = get_str_arr_item_length(A, i)
                    if nzm__iip == 1:
                        copy_single_char(bqp__stl, vdtud__qdt, qmxld__hgqwh,
                            getitem_str_offset(A, i))
                    else:
                        memcpy_region(bqp__stl, vdtud__qdt, qmxld__hgqwh,
                            getitem_str_offset(A, i), nzm__iip, 1)
                    vdtud__qdt += nzm__iip
                    setitem_str_offset(out_arr, xwg__kut + 1, vdtud__qdt)
                    if str_arr_is_na(A, i):
                        str_arr_set_na(out_arr, xwg__kut)
                    else:
                        str_arr_set_not_na(out_arr, xwg__kut)
                    xwg__kut += 1
            return out_arr
        return bool_impl
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def str_arr_arr_impl(A, ind):
            iai__tjc = len(ind)
            out_arr = pre_alloc_string_array(iai__tjc, -1)
            xwg__kut = 0
            for i in range(iai__tjc):
                vjor__pckyv = A[ind[i]]
                out_arr[xwg__kut] = vjor__pckyv
                if str_arr_is_na(A, ind[i]):
                    str_arr_set_na(out_arr, xwg__kut)
                xwg__kut += 1
            return out_arr
        return str_arr_arr_impl
    if isinstance(ind, types.SliceType):

        def str_arr_slice_impl(A, ind):
            iai__tjc = len(A)
            yiab__dtn = numba.cpython.unicode._normalize_slice(ind, iai__tjc)
            txpvs__wfeh = numba.cpython.unicode._slice_span(yiab__dtn)
            if yiab__dtn.step == 1:
                rzfrm__hbnpo = getitem_str_offset(A, yiab__dtn.start)
                ggdd__swsf = getitem_str_offset(A, yiab__dtn.stop)
                n_chars = ggdd__swsf - rzfrm__hbnpo
                zlwgq__gtufw = pre_alloc_string_array(txpvs__wfeh, np.int64
                    (n_chars))
                for i in range(txpvs__wfeh):
                    zlwgq__gtufw[i] = A[yiab__dtn.start + i]
                    if str_arr_is_na(A, yiab__dtn.start + i):
                        str_arr_set_na(zlwgq__gtufw, i)
                return zlwgq__gtufw
            else:
                zlwgq__gtufw = pre_alloc_string_array(txpvs__wfeh, -1)
                for i in range(txpvs__wfeh):
                    zlwgq__gtufw[i] = A[yiab__dtn.start + i * yiab__dtn.step]
                    if str_arr_is_na(A, yiab__dtn.start + i * yiab__dtn.step):
                        str_arr_set_na(zlwgq__gtufw, i)
                return zlwgq__gtufw
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
    vguz__xvz = (
        f'StringArray setitem with index {idx} and value {val} not supported yet.'
        )
    if isinstance(idx, types.Integer):
        if val != string_type:
            raise BodoError(vguz__xvz)
        seglm__lhr = 4

        def impl_scalar(A, idx, val):
            clo__mpoq = (val._length if val._is_ascii else seglm__lhr * val
                ._length)
            sobff__mxs = A._data
            rzfrm__hbnpo = np.int64(getitem_str_offset(A, idx))
            lyzfb__nbm = rzfrm__hbnpo + clo__mpoq
            bodo.libs.array_item_arr_ext.ensure_data_capacity(sobff__mxs,
                rzfrm__hbnpo, lyzfb__nbm)
            setitem_string_array(get_offset_ptr(A), get_data_ptr(A),
                lyzfb__nbm, val._data, val._length, val._kind, val.
                _is_ascii, idx)
            str_arr_set_not_na(A, idx)
            dummy_use(A)
            dummy_use(val)
        return impl_scalar
    if isinstance(idx, types.SliceType):
        if val == string_array_type:

            def impl_slice(A, idx, val):
                yiab__dtn = numba.cpython.unicode._normalize_slice(idx, len(A))
                bqnsh__xwjt = yiab__dtn.start
                sobff__mxs = A._data
                rzfrm__hbnpo = np.int64(getitem_str_offset(A, bqnsh__xwjt))
                lyzfb__nbm = rzfrm__hbnpo + np.int64(num_total_chars(val))
                bodo.libs.array_item_arr_ext.ensure_data_capacity(sobff__mxs,
                    rzfrm__hbnpo, lyzfb__nbm)
                set_string_array_range(A, val, bqnsh__xwjt, rzfrm__hbnpo)
                eue__mqm = 0
                for i in range(yiab__dtn.start, yiab__dtn.stop, yiab__dtn.step
                    ):
                    if str_arr_is_na(val, eue__mqm):
                        str_arr_set_na(A, i)
                    else:
                        str_arr_set_not_na(A, i)
                    eue__mqm += 1
            return impl_slice
        elif isinstance(val, types.List) and val.dtype == string_type:

            def impl_slice_list(A, idx, val):
                otne__ijy = str_list_to_array(val)
                A[idx] = otne__ijy
            return impl_slice_list
        elif val == string_type:

            def impl_slice(A, idx, val):
                yiab__dtn = numba.cpython.unicode._normalize_slice(idx, len(A))
                for i in range(yiab__dtn.start, yiab__dtn.stop, yiab__dtn.step
                    ):
                    A[i] = val
            return impl_slice
        else:
            raise BodoError(vguz__xvz)
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        if val == string_type:

            def impl_bool_scalar(A, idx, val):
                iai__tjc = len(A)
                idx = bodo.utils.conversion.coerce_to_ndarray(idx)
                out_arr = pre_alloc_string_array(iai__tjc, -1)
                for i in numba.parfors.parfor.internal_prange(iai__tjc):
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
                iai__tjc = len(A)
                idx = bodo.utils.conversion.coerce_to_array(idx,
                    use_nullable_array=True)
                out_arr = pre_alloc_string_array(iai__tjc, -1)
                znpj__kcjx = 0
                for i in numba.parfors.parfor.internal_prange(iai__tjc):
                    if not bodo.libs.array_kernels.isna(idx, i) and idx[i]:
                        if bodo.libs.array_kernels.isna(val, znpj__kcjx):
                            out_arr[i] = ''
                            str_arr_set_na(out_arr, znpj__kcjx)
                        else:
                            out_arr[i] = str(val[znpj__kcjx])
                        znpj__kcjx += 1
                    elif bodo.libs.array_kernels.isna(A, i):
                        out_arr[i] = ''
                        str_arr_set_na(out_arr, i)
                    else:
                        get_str_arr_item_copy(out_arr, i, A, i)
                move_str_binary_arr_payload(A, out_arr)
            return impl_bool_arr
        else:
            raise BodoError(vguz__xvz)
    raise BodoError(vguz__xvz)


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
    qdafw__kjaks = parse_dtype(dtype, 'StringArray.astype')
    if not isinstance(qdafw__kjaks, (types.Float, types.Integer)):
        raise BodoError('invalid dtype in StringArray.astype()')
    if isinstance(qdafw__kjaks, types.Float):

        def impl_float(A, dtype, copy=True):
            numba.parfors.parfor.init_prange()
            iai__tjc = len(A)
            B = np.empty(iai__tjc, qdafw__kjaks)
            for i in numba.parfors.parfor.internal_prange(iai__tjc):
                if bodo.libs.array_kernels.isna(A, i):
                    B[i] = np.nan
                else:
                    B[i] = float(A[i])
            return B
        return impl_float
    else:

        def impl_int(A, dtype, copy=True):
            numba.parfors.parfor.init_prange()
            iai__tjc = len(A)
            B = np.empty(iai__tjc, qdafw__kjaks)
            for i in numba.parfors.parfor.internal_prange(iai__tjc):
                B[i] = int(A[i])
            return B
        return impl_int


@intrinsic
def decode_utf8(typingctx, ptr_t, len_t=None):

    def codegen(context, builder, sig, args):
        maf__rtihz, zbik__ktq = args
        ehwu__tot = context.get_python_api(builder)
        brv__cldco = ehwu__tot.string_from_string_and_size(maf__rtihz,
            zbik__ktq)
        rcs__omta = ehwu__tot.to_native_value(string_type, brv__cldco).value
        knac__sag = cgutils.create_struct_proxy(string_type)(context,
            builder, rcs__omta)
        knac__sag.hash = knac__sag.hash.type(-1)
        ehwu__tot.decref(brv__cldco)
        return knac__sag._getvalue()
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
        win__enyt, arr, ind, nhys__pftdd = args
        plhle__yfld = _get_str_binary_arr_payload(context, builder, arr,
            string_array_type)
        offsets = context.make_helper(builder, offset_arr_type, plhle__yfld
            .offsets).data
        data = context.make_helper(builder, char_arr_type, plhle__yfld.data
            ).data
        elf__ozcml = lir.FunctionType(lir.IntType(32), [win__enyt.type, lir
            .IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(64)])
        hdn__wlj = 'str_arr_to_int64'
        if sig.args[3].dtype == types.float64:
            hdn__wlj = 'str_arr_to_float64'
        else:
            assert sig.args[3].dtype == types.int64
        arzw__oaq = cgutils.get_or_insert_function(builder.module,
            elf__ozcml, hdn__wlj)
        return builder.call(arzw__oaq, [win__enyt, offsets, data, ind])
    return types.int32(out_ptr_t, string_array_type, types.int64, out_dtype_t
        ), codegen


@unbox(BinaryArrayType)
@unbox(StringArrayType)
def unbox_str_series(typ, val, c):
    mtguj__wvei = c.context.get_constant(types.int32, int(typ ==
        binary_array_type))
    elf__ozcml = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.IntType
        (8).as_pointer(), lir.IntType(32)])
    cmhvf__kqzsr = cgutils.get_or_insert_function(c.builder.module,
        elf__ozcml, name='string_array_from_sequence')
    fif__ycog = c.builder.call(cmhvf__kqzsr, [val, mtguj__wvei])
    yvsmn__csx = ArrayItemArrayType(char_arr_type)
    zuct__ubmt = c.context.make_helper(c.builder, yvsmn__csx)
    zuct__ubmt.meminfo = fif__ycog
    bzcj__dvbj = c.context.make_helper(c.builder, typ)
    sobff__mxs = zuct__ubmt._getvalue()
    bzcj__dvbj.data = sobff__mxs
    nzz__vcege = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(bzcj__dvbj._getvalue(), is_error=nzz__vcege)


@lower_constant(BinaryArrayType)
@lower_constant(StringArrayType)
def lower_constant_str_arr(context, builder, typ, pyval):
    iai__tjc = len(pyval)
    vdtud__qdt = 0
    slks__joyp = np.empty(iai__tjc + 1, np_offset_type)
    bsa__iam = []
    kclja__vjbhv = np.empty(iai__tjc + 7 >> 3, np.uint8)
    for i, s in enumerate(pyval):
        slks__joyp[i] = vdtud__qdt
        pjj__sof = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(kclja__vjbhv, i, int(not pjj__sof)
            )
        if pjj__sof:
            continue
        pzrda__iilbt = list(s.encode()) if isinstance(s, str) else list(s)
        bsa__iam.extend(pzrda__iilbt)
        vdtud__qdt += len(pzrda__iilbt)
    slks__joyp[iai__tjc] = vdtud__qdt
    mgew__osbfv = np.array(bsa__iam, np.uint8)
    xfq__ffjb = context.get_constant(types.int64, iai__tjc)
    rprkp__yjy = context.get_constant_generic(builder, char_arr_type,
        mgew__osbfv)
    rrttz__jokpo = context.get_constant_generic(builder, offset_arr_type,
        slks__joyp)
    qovkq__afmt = context.get_constant_generic(builder,
        null_bitmap_arr_type, kclja__vjbhv)
    plhle__yfld = lir.Constant.literal_struct([xfq__ffjb, rprkp__yjy,
        rrttz__jokpo, qovkq__afmt])
    plhle__yfld = cgutils.global_constant(builder, '.const.payload',
        plhle__yfld).bitcast(cgutils.voidptr_t)
    vqpee__xxpul = context.get_constant(types.int64, -1)
    srbtu__ubms = context.get_constant_null(types.voidptr)
    eupp__yceb = lir.Constant.literal_struct([vqpee__xxpul, srbtu__ubms,
        srbtu__ubms, plhle__yfld, vqpee__xxpul])
    eupp__yceb = cgutils.global_constant(builder, '.const.meminfo', eupp__yceb
        ).bitcast(cgutils.voidptr_t)
    sobff__mxs = lir.Constant.literal_struct([eupp__yceb])
    bzcj__dvbj = lir.Constant.literal_struct([sobff__mxs])
    return bzcj__dvbj


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
