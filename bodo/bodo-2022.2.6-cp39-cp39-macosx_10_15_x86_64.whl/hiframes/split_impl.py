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
        gpqkk__yikvv = [('index_offsets', types.CPointer(offset_type)), (
            'data_offsets', types.CPointer(offset_type)), ('null_bitmap',
            types.CPointer(char_typ))]
        models.StructModel.__init__(self, dmm, fe_type, gpqkk__yikvv)


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
    oxv__tjkz = context.get_value_type(str_arr_split_view_payload_type)
    ieqo__elqsw = context.get_abi_sizeof(oxv__tjkz)
    vdmfi__aujb = context.get_value_type(types.voidptr)
    nnsbf__yiea = context.get_value_type(types.uintp)
    avni__xtudf = lir.FunctionType(lir.VoidType(), [vdmfi__aujb,
        nnsbf__yiea, vdmfi__aujb])
    ktz__rtrho = cgutils.get_or_insert_function(builder.module, avni__xtudf,
        name='dtor_str_arr_split_view')
    vxpvl__upzhl = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, ieqo__elqsw), ktz__rtrho)
    rncvc__tqme = context.nrt.meminfo_data(builder, vxpvl__upzhl)
    foqh__mluj = builder.bitcast(rncvc__tqme, oxv__tjkz.as_pointer())
    return vxpvl__upzhl, foqh__mluj


@intrinsic
def compute_split_view(typingctx, str_arr_typ, sep_typ=None):
    assert str_arr_typ == string_array_type and isinstance(sep_typ, types.
        StringLiteral)

    def codegen(context, builder, sig, args):
        oapfz__cxht, plixu__gcxtb = args
        vxpvl__upzhl, foqh__mluj = construct_str_arr_split_view(context,
            builder)
        jqpcu__nszq = _get_str_binary_arr_payload(context, builder,
            oapfz__cxht, string_array_type)
        ldmqf__zntqq = lir.FunctionType(lir.VoidType(), [foqh__mluj.type,
            lir.IntType(64), lir.IntType(offset_type.bitwidth).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8)])
        whho__vjc = cgutils.get_or_insert_function(builder.module,
            ldmqf__zntqq, name='str_arr_split_view_impl')
        yis__konip = context.make_helper(builder, offset_arr_type,
            jqpcu__nszq.offsets).data
        eac__ewgdx = context.make_helper(builder, char_arr_type,
            jqpcu__nszq.data).data
        wlfwo__ahw = context.make_helper(builder, null_bitmap_arr_type,
            jqpcu__nszq.null_bitmap).data
        avoyr__fluw = context.get_constant(types.int8, ord(sep_typ.
            literal_value))
        builder.call(whho__vjc, [foqh__mluj, jqpcu__nszq.n_arrays,
            yis__konip, eac__ewgdx, wlfwo__ahw, avoyr__fluw])
        ynkao__pcgsq = cgutils.create_struct_proxy(
            str_arr_split_view_payload_type)(context, builder, value=
            builder.load(foqh__mluj))
        eubkr__qnae = context.make_helper(builder, string_array_split_view_type
            )
        eubkr__qnae.num_items = jqpcu__nszq.n_arrays
        eubkr__qnae.index_offsets = ynkao__pcgsq.index_offsets
        eubkr__qnae.data_offsets = ynkao__pcgsq.data_offsets
        eubkr__qnae.data = context.compile_internal(builder, lambda S:
            get_data_ptr(S), data_ctypes_type(string_array_type), [oapfz__cxht]
            )
        eubkr__qnae.null_bitmap = ynkao__pcgsq.null_bitmap
        eubkr__qnae.meminfo = vxpvl__upzhl
        szo__rck = eubkr__qnae._getvalue()
        return impl_ret_new_ref(context, builder,
            string_array_split_view_type, szo__rck)
    return string_array_split_view_type(string_array_type, sep_typ), codegen


@box(StringArraySplitViewType)
def box_str_arr_split_view(typ, val, c):
    context = c.context
    builder = c.builder
    sraqr__vdel = context.make_helper(builder, string_array_split_view_type,
        val)
    qnf__ytcu = context.insert_const_string(builder.module, 'numpy')
    cafr__gvq = c.pyapi.import_module_noblock(qnf__ytcu)
    dtype = c.pyapi.object_getattr_string(cafr__gvq, 'object_')
    hgrn__qndv = builder.sext(sraqr__vdel.num_items, c.pyapi.longlong)
    fopsh__vxmah = c.pyapi.long_from_longlong(hgrn__qndv)
    lqrd__agnx = c.pyapi.call_method(cafr__gvq, 'ndarray', (fopsh__vxmah,
        dtype))
    kloq__mlwom = LLType.function(lir.IntType(8).as_pointer(), [c.pyapi.
        pyobj, c.pyapi.py_ssize_t])
    dxj__dnij = c.pyapi._get_function(kloq__mlwom, name='array_getptr1')
    dcjq__mlt = LLType.function(lir.VoidType(), [c.pyapi.pyobj, lir.IntType
        (8).as_pointer(), c.pyapi.pyobj])
    poz__ogwi = c.pyapi._get_function(dcjq__mlt, name='array_setitem')
    mpkj__xpo = c.pyapi.object_getattr_string(cafr__gvq, 'nan')
    with cgutils.for_range(builder, sraqr__vdel.num_items) as xqodk__rwya:
        str_ind = xqodk__rwya.index
        rca__mnuhb = builder.sext(builder.load(builder.gep(sraqr__vdel.
            index_offsets, [str_ind])), lir.IntType(64))
        miov__rbvd = builder.sext(builder.load(builder.gep(sraqr__vdel.
            index_offsets, [builder.add(str_ind, str_ind.type(1))])), lir.
            IntType(64))
        roz__peu = builder.lshr(str_ind, lir.Constant(lir.IntType(64), 3))
        qsh__zupdt = builder.gep(sraqr__vdel.null_bitmap, [roz__peu])
        hmlw__wwhpo = builder.load(qsh__zupdt)
        jeq__ctyt = builder.trunc(builder.and_(str_ind, lir.Constant(lir.
            IntType(64), 7)), lir.IntType(8))
        val = builder.and_(builder.lshr(hmlw__wwhpo, jeq__ctyt), lir.
            Constant(lir.IntType(8), 1))
        tcj__fntpz = builder.sub(miov__rbvd, rca__mnuhb)
        tcj__fntpz = builder.sub(tcj__fntpz, tcj__fntpz.type(1))
        tql__qlh = builder.call(dxj__dnij, [lqrd__agnx, str_ind])
        ckm__yfg = c.builder.icmp_unsigned('!=', val, val.type(0))
        with c.builder.if_else(ckm__yfg) as (obd__tdky, xta__iaq):
            with obd__tdky:
                ddou__tlwu = c.pyapi.list_new(tcj__fntpz)
                with c.builder.if_then(cgutils.is_not_null(c.builder,
                    ddou__tlwu), likely=True):
                    with cgutils.for_range(c.builder, tcj__fntpz
                        ) as xqodk__rwya:
                        pxn__cvbk = builder.add(rca__mnuhb, xqodk__rwya.index)
                        data_start = builder.load(builder.gep(sraqr__vdel.
                            data_offsets, [pxn__cvbk]))
                        data_start = builder.add(data_start, data_start.type(1)
                            )
                        bdly__cuusr = builder.load(builder.gep(sraqr__vdel.
                            data_offsets, [builder.add(pxn__cvbk, pxn__cvbk
                            .type(1))]))
                        ccz__lot = builder.gep(builder.extract_value(
                            sraqr__vdel.data, 0), [data_start])
                        tlmgj__eth = builder.sext(builder.sub(bdly__cuusr,
                            data_start), lir.IntType(64))
                        awqb__knjn = c.pyapi.string_from_string_and_size(
                            ccz__lot, tlmgj__eth)
                        c.pyapi.list_setitem(ddou__tlwu, xqodk__rwya.index,
                            awqb__knjn)
                builder.call(poz__ogwi, [lqrd__agnx, tql__qlh, ddou__tlwu])
            with xta__iaq:
                builder.call(poz__ogwi, [lqrd__agnx, tql__qlh, mpkj__xpo])
    c.pyapi.decref(cafr__gvq)
    c.pyapi.decref(dtype)
    c.pyapi.decref(mpkj__xpo)
    return lqrd__agnx


@intrinsic
def pre_alloc_str_arr_view(typingctx, num_items_t, num_offsets_t, data_t=None):
    assert num_items_t == types.intp and num_offsets_t == types.intp

    def codegen(context, builder, sig, args):
        tmpx__kula, bjlp__dfy, ccz__lot = args
        vxpvl__upzhl, foqh__mluj = construct_str_arr_split_view(context,
            builder)
        ldmqf__zntqq = lir.FunctionType(lir.VoidType(), [foqh__mluj.type,
            lir.IntType(64), lir.IntType(64)])
        whho__vjc = cgutils.get_or_insert_function(builder.module,
            ldmqf__zntqq, name='str_arr_split_view_alloc')
        builder.call(whho__vjc, [foqh__mluj, tmpx__kula, bjlp__dfy])
        ynkao__pcgsq = cgutils.create_struct_proxy(
            str_arr_split_view_payload_type)(context, builder, value=
            builder.load(foqh__mluj))
        eubkr__qnae = context.make_helper(builder, string_array_split_view_type
            )
        eubkr__qnae.num_items = tmpx__kula
        eubkr__qnae.index_offsets = ynkao__pcgsq.index_offsets
        eubkr__qnae.data_offsets = ynkao__pcgsq.data_offsets
        eubkr__qnae.data = ccz__lot
        eubkr__qnae.null_bitmap = ynkao__pcgsq.null_bitmap
        context.nrt.incref(builder, data_t, ccz__lot)
        eubkr__qnae.meminfo = vxpvl__upzhl
        szo__rck = eubkr__qnae._getvalue()
        return impl_ret_new_ref(context, builder,
            string_array_split_view_type, szo__rck)
    return string_array_split_view_type(types.intp, types.intp, data_t
        ), codegen


@intrinsic
def get_c_arr_ptr(typingctx, c_arr, ind_t=None):
    assert isinstance(c_arr, (types.CPointer, types.ArrayCTypes))

    def codegen(context, builder, sig, args):
        jjjcm__lvez, ind = args
        if isinstance(sig.args[0], types.ArrayCTypes):
            jjjcm__lvez = builder.extract_value(jjjcm__lvez, 0)
        return builder.bitcast(builder.gep(jjjcm__lvez, [ind]), lir.IntType
            (8).as_pointer())
    return types.voidptr(c_arr, ind_t), codegen


@intrinsic
def getitem_c_arr(typingctx, c_arr, ind_t=None):

    def codegen(context, builder, sig, args):
        jjjcm__lvez, ind = args
        if isinstance(sig.args[0], types.ArrayCTypes):
            jjjcm__lvez = builder.extract_value(jjjcm__lvez, 0)
        return builder.load(builder.gep(jjjcm__lvez, [ind]))
    return c_arr.dtype(c_arr, ind_t), codegen


@intrinsic
def setitem_c_arr(typingctx, c_arr, ind_t, item_t=None):

    def codegen(context, builder, sig, args):
        jjjcm__lvez, ind, uuzb__tvtc = args
        yedl__bsz = builder.gep(jjjcm__lvez, [ind])
        builder.store(uuzb__tvtc, yedl__bsz)
    return types.void(c_arr, ind_t, c_arr.dtype), codegen


@intrinsic
def get_array_ctypes_ptr(typingctx, arr_ctypes_t, ind_t=None):

    def codegen(context, builder, sig, args):
        tykta__prw, ind = args
        ojkzu__eish = context.make_helper(builder, arr_ctypes_t, tykta__prw)
        ayvp__ynnli = context.make_helper(builder, arr_ctypes_t)
        ayvp__ynnli.data = builder.gep(ojkzu__eish.data, [ind])
        ayvp__ynnli.meminfo = ojkzu__eish.meminfo
        oxixm__erhfd = ayvp__ynnli._getvalue()
        return impl_ret_borrowed(context, builder, arr_ctypes_t, oxixm__erhfd)
    return arr_ctypes_t(arr_ctypes_t, ind_t), codegen


@numba.njit(no_cpython_wrapper=True)
def get_split_view_index(arr, item_ind, str_ind):
    hqz__dnl = bodo.libs.int_arr_ext.get_bit_bitmap_arr(arr._null_bitmap,
        item_ind)
    if not hqz__dnl:
        return 0, 0, 0
    pxn__cvbk = getitem_c_arr(arr._index_offsets, item_ind)
    abvd__fxts = getitem_c_arr(arr._index_offsets, item_ind + 1) - 1
    gaowv__htv = abvd__fxts - pxn__cvbk
    if str_ind >= gaowv__htv:
        return 0, 0, 0
    data_start = getitem_c_arr(arr._data_offsets, pxn__cvbk + str_ind)
    data_start += 1
    if pxn__cvbk + str_ind == 0:
        data_start = 0
    bdly__cuusr = getitem_c_arr(arr._data_offsets, pxn__cvbk + str_ind + 1)
    tcdw__vsclc = bdly__cuusr - data_start
    return 1, data_start, tcdw__vsclc


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
        mkneo__qdd = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

        def _impl(A, ind):
            pxn__cvbk = getitem_c_arr(A._index_offsets, ind)
            abvd__fxts = getitem_c_arr(A._index_offsets, ind + 1)
            ozfn__jiosy = abvd__fxts - pxn__cvbk - 1
            oapfz__cxht = bodo.libs.str_arr_ext.pre_alloc_string_array(
                ozfn__jiosy, -1)
            for uaq__pkgr in range(ozfn__jiosy):
                data_start = getitem_c_arr(A._data_offsets, pxn__cvbk +
                    uaq__pkgr)
                data_start += 1
                if pxn__cvbk + uaq__pkgr == 0:
                    data_start = 0
                bdly__cuusr = getitem_c_arr(A._data_offsets, pxn__cvbk +
                    uaq__pkgr + 1)
                tcdw__vsclc = bdly__cuusr - data_start
                yedl__bsz = get_array_ctypes_ptr(A._data, data_start)
                twexh__rdpxt = bodo.libs.str_arr_ext.decode_utf8(yedl__bsz,
                    tcdw__vsclc)
                oapfz__cxht[uaq__pkgr] = twexh__rdpxt
            return oapfz__cxht
        return _impl
    if A == string_array_split_view_type and ind == types.Array(types.bool_,
        1, 'C'):
        mlzn__rsafc = offset_type.bitwidth // 8

        def _impl(A, ind):
            ozfn__jiosy = len(A)
            if ozfn__jiosy != len(ind):
                raise IndexError(
                    'boolean index did not match indexed array along dimension 0'
                    )
            tmpx__kula = 0
            bjlp__dfy = 0
            for uaq__pkgr in range(ozfn__jiosy):
                if ind[uaq__pkgr]:
                    tmpx__kula += 1
                    pxn__cvbk = getitem_c_arr(A._index_offsets, uaq__pkgr)
                    abvd__fxts = getitem_c_arr(A._index_offsets, uaq__pkgr + 1)
                    bjlp__dfy += abvd__fxts - pxn__cvbk
            lqrd__agnx = pre_alloc_str_arr_view(tmpx__kula, bjlp__dfy, A._data)
            item_ind = 0
            rzpib__olb = 0
            for uaq__pkgr in range(ozfn__jiosy):
                if ind[uaq__pkgr]:
                    pxn__cvbk = getitem_c_arr(A._index_offsets, uaq__pkgr)
                    abvd__fxts = getitem_c_arr(A._index_offsets, uaq__pkgr + 1)
                    gvfs__iwx = abvd__fxts - pxn__cvbk
                    setitem_c_arr(lqrd__agnx._index_offsets, item_ind,
                        rzpib__olb)
                    yedl__bsz = get_c_arr_ptr(A._data_offsets, pxn__cvbk)
                    gir__yot = get_c_arr_ptr(lqrd__agnx._data_offsets,
                        rzpib__olb)
                    _memcpy(gir__yot, yedl__bsz, gvfs__iwx, mlzn__rsafc)
                    hqz__dnl = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A.
                        _null_bitmap, uaq__pkgr)
                    bodo.libs.int_arr_ext.set_bit_to_arr(lqrd__agnx.
                        _null_bitmap, item_ind, hqz__dnl)
                    item_ind += 1
                    rzpib__olb += gvfs__iwx
            setitem_c_arr(lqrd__agnx._index_offsets, item_ind, rzpib__olb)
            return lqrd__agnx
        return _impl
