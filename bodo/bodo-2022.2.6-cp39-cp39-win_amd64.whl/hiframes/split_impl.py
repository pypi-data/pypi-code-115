import operator
import llvmlite.binding as ll
import numba
import numba.core.typing.typeof
import numpy as np
from llvmlite import ir as lir
from llvmlite.llvmpy.core import Type as LLType
from numba.core import cgutils, types
from numba.core.imputils import impl_ret_borrowed, impl_ret_new_ref
from numba.extending import box, intrinsic, make_attribute_wrapper, models, overload, overload_attribute, register_model
import bodo
from bodo.libs import hstr_ext
from bodo.libs.array_item_arr_ext import offset_type
from bodo.libs.str_arr_ext import _get_str_binary_arr_payload, _memcpy, char_arr_type, get_data_ptr, null_bitmap_arr_type, offset_arr_type, string_array_type
ll.add_symbol('array_setitem', hstr_ext.array_setitem)
ll.add_symbol('array_getptr1', hstr_ext.array_getptr1)
ll.add_symbol('dtor_str_arr_split_view', hstr_ext.dtor_str_arr_split_view)
ll.add_symbol('str_arr_split_view_impl', hstr_ext.str_arr_split_view_impl)
ll.add_symbol('str_arr_split_view_alloc', hstr_ext.str_arr_split_view_alloc)
char_typ = types.uint8
data_ctypes_type = types.ArrayCTypes(types.Array(char_typ, 1, 'C'))
offset_ctypes_type = types.ArrayCTypes(types.Array(offset_type, 1, 'C'))


class StringArraySplitViewType(types.ArrayCompatible):

    def __init__(self):
        super(StringArraySplitViewType, self).__init__(name=
            'StringArraySplitViewType()')

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def dtype(self):
        return string_array_type

    def copy(self):
        return StringArraySplitViewType()


string_array_split_view_type = StringArraySplitViewType()


class StringArraySplitViewPayloadType(types.Type):

    def __init__(self):
        super(StringArraySplitViewPayloadType, self).__init__(name=
            'StringArraySplitViewPayloadType()')


str_arr_split_view_payload_type = StringArraySplitViewPayloadType()


@register_model(StringArraySplitViewPayloadType)
class StringArrayPayloadModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        lkt__tpzdi = [('index_offsets', types.CPointer(offset_type)), (
            'data_offsets', types.CPointer(offset_type)), ('null_bitmap',
            types.CPointer(char_typ))]
        models.StructModel.__init__(self, dmm, fe_type, lkt__tpzdi)


str_arr_model_members = [('num_items', types.uint64), ('index_offsets',
    types.CPointer(offset_type)), ('data_offsets', types.CPointer(
    offset_type)), ('data', data_ctypes_type), ('null_bitmap', types.
    CPointer(char_typ)), ('meminfo', types.MemInfoPointer(
    str_arr_split_view_payload_type))]


@register_model(StringArraySplitViewType)
class StringArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        models.StructModel.__init__(self, dmm, fe_type, str_arr_model_members)


make_attribute_wrapper(StringArraySplitViewType, 'num_items', '_num_items')
make_attribute_wrapper(StringArraySplitViewType, 'index_offsets',
    '_index_offsets')
make_attribute_wrapper(StringArraySplitViewType, 'data_offsets',
    '_data_offsets')
make_attribute_wrapper(StringArraySplitViewType, 'data', '_data')
make_attribute_wrapper(StringArraySplitViewType, 'null_bitmap', '_null_bitmap')


def construct_str_arr_split_view(context, builder):
    dkje__qyd = context.get_value_type(str_arr_split_view_payload_type)
    foh__rlet = context.get_abi_sizeof(dkje__qyd)
    exv__tzyco = context.get_value_type(types.voidptr)
    sce__cns = context.get_value_type(types.uintp)
    buhk__yfop = lir.FunctionType(lir.VoidType(), [exv__tzyco, sce__cns,
        exv__tzyco])
    xqgh__jso = cgutils.get_or_insert_function(builder.module, buhk__yfop,
        name='dtor_str_arr_split_view')
    rbtl__yvtts = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, foh__rlet), xqgh__jso)
    piuyo__aruv = context.nrt.meminfo_data(builder, rbtl__yvtts)
    fhk__ktugi = builder.bitcast(piuyo__aruv, dkje__qyd.as_pointer())
    return rbtl__yvtts, fhk__ktugi


@intrinsic
def compute_split_view(typingctx, str_arr_typ, sep_typ=None):
    assert str_arr_typ == string_array_type and isinstance(sep_typ, types.
        StringLiteral)

    def codegen(context, builder, sig, args):
        lhp__uvu, ulvx__mvzyj = args
        rbtl__yvtts, fhk__ktugi = construct_str_arr_split_view(context, builder
            )
        vxvmy__qcn = _get_str_binary_arr_payload(context, builder, lhp__uvu,
            string_array_type)
        qlbfx__qffno = lir.FunctionType(lir.VoidType(), [fhk__ktugi.type,
            lir.IntType(64), lir.IntType(offset_type.bitwidth).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8)])
        boonz__negi = cgutils.get_or_insert_function(builder.module,
            qlbfx__qffno, name='str_arr_split_view_impl')
        yppt__enio = context.make_helper(builder, offset_arr_type,
            vxvmy__qcn.offsets).data
        eaa__bpv = context.make_helper(builder, char_arr_type, vxvmy__qcn.data
            ).data
        mzkgc__xicth = context.make_helper(builder, null_bitmap_arr_type,
            vxvmy__qcn.null_bitmap).data
        hboe__lys = context.get_constant(types.int8, ord(sep_typ.literal_value)
            )
        builder.call(boonz__negi, [fhk__ktugi, vxvmy__qcn.n_arrays,
            yppt__enio, eaa__bpv, mzkgc__xicth, hboe__lys])
        wcec__hanum = cgutils.create_struct_proxy(
            str_arr_split_view_payload_type)(context, builder, value=
            builder.load(fhk__ktugi))
        ina__hccaa = context.make_helper(builder, string_array_split_view_type)
        ina__hccaa.num_items = vxvmy__qcn.n_arrays
        ina__hccaa.index_offsets = wcec__hanum.index_offsets
        ina__hccaa.data_offsets = wcec__hanum.data_offsets
        ina__hccaa.data = context.compile_internal(builder, lambda S:
            get_data_ptr(S), data_ctypes_type(string_array_type), [lhp__uvu])
        ina__hccaa.null_bitmap = wcec__hanum.null_bitmap
        ina__hccaa.meminfo = rbtl__yvtts
        inas__itu = ina__hccaa._getvalue()
        return impl_ret_new_ref(context, builder,
            string_array_split_view_type, inas__itu)
    return string_array_split_view_type(string_array_type, sep_typ), codegen


@box(StringArraySplitViewType)
def box_str_arr_split_view(typ, val, c):
    context = c.context
    builder = c.builder
    zccpz__izm = context.make_helper(builder, string_array_split_view_type, val
        )
    hvuad__sete = context.insert_const_string(builder.module, 'numpy')
    ysld__pfw = c.pyapi.import_module_noblock(hvuad__sete)
    dtype = c.pyapi.object_getattr_string(ysld__pfw, 'object_')
    svqj__ftb = builder.sext(zccpz__izm.num_items, c.pyapi.longlong)
    pte__rccc = c.pyapi.long_from_longlong(svqj__ftb)
    zwmbd__dyvuc = c.pyapi.call_method(ysld__pfw, 'ndarray', (pte__rccc, dtype)
        )
    rmix__ppqzk = LLType.function(lir.IntType(8).as_pointer(), [c.pyapi.
        pyobj, c.pyapi.py_ssize_t])
    enp__udo = c.pyapi._get_function(rmix__ppqzk, name='array_getptr1')
    gje__bpwch = LLType.function(lir.VoidType(), [c.pyapi.pyobj, lir.
        IntType(8).as_pointer(), c.pyapi.pyobj])
    vvq__yrx = c.pyapi._get_function(gje__bpwch, name='array_setitem')
    ddq__vxqe = c.pyapi.object_getattr_string(ysld__pfw, 'nan')
    with cgutils.for_range(builder, zccpz__izm.num_items) as gyq__rpzv:
        str_ind = gyq__rpzv.index
        vfw__diwb = builder.sext(builder.load(builder.gep(zccpz__izm.
            index_offsets, [str_ind])), lir.IntType(64))
        ktmo__recbs = builder.sext(builder.load(builder.gep(zccpz__izm.
            index_offsets, [builder.add(str_ind, str_ind.type(1))])), lir.
            IntType(64))
        ndeag__wwnh = builder.lshr(str_ind, lir.Constant(lir.IntType(64), 3))
        ldi__qhw = builder.gep(zccpz__izm.null_bitmap, [ndeag__wwnh])
        ycf__cfgrk = builder.load(ldi__qhw)
        sekyr__hav = builder.trunc(builder.and_(str_ind, lir.Constant(lir.
            IntType(64), 7)), lir.IntType(8))
        val = builder.and_(builder.lshr(ycf__cfgrk, sekyr__hav), lir.
            Constant(lir.IntType(8), 1))
        rbf__ppoog = builder.sub(ktmo__recbs, vfw__diwb)
        rbf__ppoog = builder.sub(rbf__ppoog, rbf__ppoog.type(1))
        bud__tubw = builder.call(enp__udo, [zwmbd__dyvuc, str_ind])
        qtsx__fef = c.builder.icmp_unsigned('!=', val, val.type(0))
        with c.builder.if_else(qtsx__fef) as (icq__zwp, erc__gyn):
            with icq__zwp:
                jnb__cwbs = c.pyapi.list_new(rbf__ppoog)
                with c.builder.if_then(cgutils.is_not_null(c.builder,
                    jnb__cwbs), likely=True):
                    with cgutils.for_range(c.builder, rbf__ppoog) as gyq__rpzv:
                        brd__hawj = builder.add(vfw__diwb, gyq__rpzv.index)
                        data_start = builder.load(builder.gep(zccpz__izm.
                            data_offsets, [brd__hawj]))
                        data_start = builder.add(data_start, data_start.type(1)
                            )
                        mfbb__pyu = builder.load(builder.gep(zccpz__izm.
                            data_offsets, [builder.add(brd__hawj, brd__hawj
                            .type(1))]))
                        msh__txps = builder.gep(builder.extract_value(
                            zccpz__izm.data, 0), [data_start])
                        qpwp__xmjum = builder.sext(builder.sub(mfbb__pyu,
                            data_start), lir.IntType(64))
                        leea__malqd = c.pyapi.string_from_string_and_size(
                            msh__txps, qpwp__xmjum)
                        c.pyapi.list_setitem(jnb__cwbs, gyq__rpzv.index,
                            leea__malqd)
                builder.call(vvq__yrx, [zwmbd__dyvuc, bud__tubw, jnb__cwbs])
            with erc__gyn:
                builder.call(vvq__yrx, [zwmbd__dyvuc, bud__tubw, ddq__vxqe])
    c.pyapi.decref(ysld__pfw)
    c.pyapi.decref(dtype)
    c.pyapi.decref(ddq__vxqe)
    return zwmbd__dyvuc


@intrinsic
def pre_alloc_str_arr_view(typingctx, num_items_t, num_offsets_t, data_t=None):
    assert num_items_t == types.intp and num_offsets_t == types.intp

    def codegen(context, builder, sig, args):
        sarje__pzea, xacs__atuw, msh__txps = args
        rbtl__yvtts, fhk__ktugi = construct_str_arr_split_view(context, builder
            )
        qlbfx__qffno = lir.FunctionType(lir.VoidType(), [fhk__ktugi.type,
            lir.IntType(64), lir.IntType(64)])
        boonz__negi = cgutils.get_or_insert_function(builder.module,
            qlbfx__qffno, name='str_arr_split_view_alloc')
        builder.call(boonz__negi, [fhk__ktugi, sarje__pzea, xacs__atuw])
        wcec__hanum = cgutils.create_struct_proxy(
            str_arr_split_view_payload_type)(context, builder, value=
            builder.load(fhk__ktugi))
        ina__hccaa = context.make_helper(builder, string_array_split_view_type)
        ina__hccaa.num_items = sarje__pzea
        ina__hccaa.index_offsets = wcec__hanum.index_offsets
        ina__hccaa.data_offsets = wcec__hanum.data_offsets
        ina__hccaa.data = msh__txps
        ina__hccaa.null_bitmap = wcec__hanum.null_bitmap
        context.nrt.incref(builder, data_t, msh__txps)
        ina__hccaa.meminfo = rbtl__yvtts
        inas__itu = ina__hccaa._getvalue()
        return impl_ret_new_ref(context, builder,
            string_array_split_view_type, inas__itu)
    return string_array_split_view_type(types.intp, types.intp, data_t
        ), codegen


@intrinsic
def get_c_arr_ptr(typingctx, c_arr, ind_t=None):
    assert isinstance(c_arr, (types.CPointer, types.ArrayCTypes))

    def codegen(context, builder, sig, args):
        mbj__pkxd, ind = args
        if isinstance(sig.args[0], types.ArrayCTypes):
            mbj__pkxd = builder.extract_value(mbj__pkxd, 0)
        return builder.bitcast(builder.gep(mbj__pkxd, [ind]), lir.IntType(8
            ).as_pointer())
    return types.voidptr(c_arr, ind_t), codegen


@intrinsic
def getitem_c_arr(typingctx, c_arr, ind_t=None):

    def codegen(context, builder, sig, args):
        mbj__pkxd, ind = args
        if isinstance(sig.args[0], types.ArrayCTypes):
            mbj__pkxd = builder.extract_value(mbj__pkxd, 0)
        return builder.load(builder.gep(mbj__pkxd, [ind]))
    return c_arr.dtype(c_arr, ind_t), codegen


@intrinsic
def setitem_c_arr(typingctx, c_arr, ind_t, item_t=None):

    def codegen(context, builder, sig, args):
        mbj__pkxd, ind, bmo__ppa = args
        soy__qadac = builder.gep(mbj__pkxd, [ind])
        builder.store(bmo__ppa, soy__qadac)
    return types.void(c_arr, ind_t, c_arr.dtype), codegen


@intrinsic
def get_array_ctypes_ptr(typingctx, arr_ctypes_t, ind_t=None):

    def codegen(context, builder, sig, args):
        akyht__xvvx, ind = args
        tgpir__othl = context.make_helper(builder, arr_ctypes_t, akyht__xvvx)
        dewzl__rkk = context.make_helper(builder, arr_ctypes_t)
        dewzl__rkk.data = builder.gep(tgpir__othl.data, [ind])
        dewzl__rkk.meminfo = tgpir__othl.meminfo
        fwids__vguge = dewzl__rkk._getvalue()
        return impl_ret_borrowed(context, builder, arr_ctypes_t, fwids__vguge)
    return arr_ctypes_t(arr_ctypes_t, ind_t), codegen


@numba.njit(no_cpython_wrapper=True)
def get_split_view_index(arr, item_ind, str_ind):
    cap__kkgbw = bodo.libs.int_arr_ext.get_bit_bitmap_arr(arr._null_bitmap,
        item_ind)
    if not cap__kkgbw:
        return 0, 0, 0
    brd__hawj = getitem_c_arr(arr._index_offsets, item_ind)
    syg__cqnbu = getitem_c_arr(arr._index_offsets, item_ind + 1) - 1
    uex__gtb = syg__cqnbu - brd__hawj
    if str_ind >= uex__gtb:
        return 0, 0, 0
    data_start = getitem_c_arr(arr._data_offsets, brd__hawj + str_ind)
    data_start += 1
    if brd__hawj + str_ind == 0:
        data_start = 0
    mfbb__pyu = getitem_c_arr(arr._data_offsets, brd__hawj + str_ind + 1)
    mxds__vzp = mfbb__pyu - data_start
    return 1, data_start, mxds__vzp


@numba.njit(no_cpython_wrapper=True)
def get_split_view_data_ptr(arr, data_start):
    return get_array_ctypes_ptr(arr._data, data_start)


@overload(len, no_unliteral=True)
def str_arr_split_view_len_overload(arr):
    if arr == string_array_split_view_type:
        return lambda arr: np.int64(arr._num_items)


@overload_attribute(StringArraySplitViewType, 'shape')
def overload_split_view_arr_shape(A):
    return lambda A: (np.int64(A._num_items),)


@overload(operator.getitem, no_unliteral=True)
def str_arr_split_view_getitem_overload(A, ind):
    if A != string_array_split_view_type:
        return
    if A == string_array_split_view_type and isinstance(ind, types.Integer):
        rsvga__vrqw = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

        def _impl(A, ind):
            brd__hawj = getitem_c_arr(A._index_offsets, ind)
            syg__cqnbu = getitem_c_arr(A._index_offsets, ind + 1)
            lem__ius = syg__cqnbu - brd__hawj - 1
            lhp__uvu = bodo.libs.str_arr_ext.pre_alloc_string_array(lem__ius,
                -1)
            for uxvi__zdo in range(lem__ius):
                data_start = getitem_c_arr(A._data_offsets, brd__hawj +
                    uxvi__zdo)
                data_start += 1
                if brd__hawj + uxvi__zdo == 0:
                    data_start = 0
                mfbb__pyu = getitem_c_arr(A._data_offsets, brd__hawj +
                    uxvi__zdo + 1)
                mxds__vzp = mfbb__pyu - data_start
                soy__qadac = get_array_ctypes_ptr(A._data, data_start)
                ixzxd__mfjah = bodo.libs.str_arr_ext.decode_utf8(soy__qadac,
                    mxds__vzp)
                lhp__uvu[uxvi__zdo] = ixzxd__mfjah
            return lhp__uvu
        return _impl
    if A == string_array_split_view_type and ind == types.Array(types.bool_,
        1, 'C'):
        hww__wqqn = offset_type.bitwidth // 8

        def _impl(A, ind):
            lem__ius = len(A)
            if lem__ius != len(ind):
                raise IndexError(
                    'boolean index did not match indexed array along dimension 0'
                    )
            sarje__pzea = 0
            xacs__atuw = 0
            for uxvi__zdo in range(lem__ius):
                if ind[uxvi__zdo]:
                    sarje__pzea += 1
                    brd__hawj = getitem_c_arr(A._index_offsets, uxvi__zdo)
                    syg__cqnbu = getitem_c_arr(A._index_offsets, uxvi__zdo + 1)
                    xacs__atuw += syg__cqnbu - brd__hawj
            zwmbd__dyvuc = pre_alloc_str_arr_view(sarje__pzea, xacs__atuw,
                A._data)
            item_ind = 0
            wugrc__wyx = 0
            for uxvi__zdo in range(lem__ius):
                if ind[uxvi__zdo]:
                    brd__hawj = getitem_c_arr(A._index_offsets, uxvi__zdo)
                    syg__cqnbu = getitem_c_arr(A._index_offsets, uxvi__zdo + 1)
                    urmw__ecqnh = syg__cqnbu - brd__hawj
                    setitem_c_arr(zwmbd__dyvuc._index_offsets, item_ind,
                        wugrc__wyx)
                    soy__qadac = get_c_arr_ptr(A._data_offsets, brd__hawj)
                    kpc__ehm = get_c_arr_ptr(zwmbd__dyvuc._data_offsets,
                        wugrc__wyx)
                    _memcpy(kpc__ehm, soy__qadac, urmw__ecqnh, hww__wqqn)
                    cap__kkgbw = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, uxvi__zdo)
                    bodo.libs.int_arr_ext.set_bit_to_arr(zwmbd__dyvuc.
                        _null_bitmap, item_ind, cap__kkgbw)
                    item_ind += 1
                    wugrc__wyx += urmw__ecqnh
            setitem_c_arr(zwmbd__dyvuc._index_offsets, item_ind, wugrc__wyx)
            return zwmbd__dyvuc
        return _impl
