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
        hwzc__itse = [('index_offsets', types.CPointer(offset_type)), (
            'data_offsets', types.CPointer(offset_type)), ('null_bitmap',
            types.CPointer(char_typ))]
        models.StructModel.__init__(self, dmm, fe_type, hwzc__itse)


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
    xpct__hvd = context.get_value_type(str_arr_split_view_payload_type)
    sni__slk = context.get_abi_sizeof(xpct__hvd)
    fgif__yhhon = context.get_value_type(types.voidptr)
    iqs__rlfp = context.get_value_type(types.uintp)
    hbuui__amtq = lir.FunctionType(lir.VoidType(), [fgif__yhhon, iqs__rlfp,
        fgif__yhhon])
    rct__ung = cgutils.get_or_insert_function(builder.module, hbuui__amtq,
        name='dtor_str_arr_split_view')
    ainck__ydhsv = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, sni__slk), rct__ung)
    brhkd__xphig = context.nrt.meminfo_data(builder, ainck__ydhsv)
    xilqi__hcge = builder.bitcast(brhkd__xphig, xpct__hvd.as_pointer())
    return ainck__ydhsv, xilqi__hcge


@intrinsic
def compute_split_view(typingctx, str_arr_typ, sep_typ=None):
    assert str_arr_typ == string_array_type and isinstance(sep_typ, types.
        StringLiteral)

    def codegen(context, builder, sig, args):
        xut__hlo, olv__wcgus = args
        ainck__ydhsv, xilqi__hcge = construct_str_arr_split_view(context,
            builder)
        wkq__rlt = _get_str_binary_arr_payload(context, builder, xut__hlo,
            string_array_type)
        prb__tec = lir.FunctionType(lir.VoidType(), [xilqi__hcge.type, lir.
            IntType(64), lir.IntType(offset_type.bitwidth).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8)])
        etqnf__ohglq = cgutils.get_or_insert_function(builder.module,
            prb__tec, name='str_arr_split_view_impl')
        skri__dwojb = context.make_helper(builder, offset_arr_type,
            wkq__rlt.offsets).data
        vcwli__nrfmm = context.make_helper(builder, char_arr_type, wkq__rlt
            .data).data
        dwudb__fcu = context.make_helper(builder, null_bitmap_arr_type,
            wkq__rlt.null_bitmap).data
        hlmvi__iphf = context.get_constant(types.int8, ord(sep_typ.
            literal_value))
        builder.call(etqnf__ohglq, [xilqi__hcge, wkq__rlt.n_arrays,
            skri__dwojb, vcwli__nrfmm, dwudb__fcu, hlmvi__iphf])
        lbxd__gqlw = cgutils.create_struct_proxy(
            str_arr_split_view_payload_type)(context, builder, value=
            builder.load(xilqi__hcge))
        hpld__gvk = context.make_helper(builder, string_array_split_view_type)
        hpld__gvk.num_items = wkq__rlt.n_arrays
        hpld__gvk.index_offsets = lbxd__gqlw.index_offsets
        hpld__gvk.data_offsets = lbxd__gqlw.data_offsets
        hpld__gvk.data = context.compile_internal(builder, lambda S:
            get_data_ptr(S), data_ctypes_type(string_array_type), [xut__hlo])
        hpld__gvk.null_bitmap = lbxd__gqlw.null_bitmap
        hpld__gvk.meminfo = ainck__ydhsv
        nfob__lugr = hpld__gvk._getvalue()
        return impl_ret_new_ref(context, builder,
            string_array_split_view_type, nfob__lugr)
    return string_array_split_view_type(string_array_type, sep_typ), codegen


@box(StringArraySplitViewType)
def box_str_arr_split_view(typ, val, c):
    context = c.context
    builder = c.builder
    zfdgy__qzvkh = context.make_helper(builder,
        string_array_split_view_type, val)
    jhr__vro = context.insert_const_string(builder.module, 'numpy')
    ihjd__kvap = c.pyapi.import_module_noblock(jhr__vro)
    dtype = c.pyapi.object_getattr_string(ihjd__kvap, 'object_')
    rgci__ciyis = builder.sext(zfdgy__qzvkh.num_items, c.pyapi.longlong)
    kehs__rpgq = c.pyapi.long_from_longlong(rgci__ciyis)
    dvn__zmh = c.pyapi.call_method(ihjd__kvap, 'ndarray', (kehs__rpgq, dtype))
    xklzb__oiy = LLType.function(lir.IntType(8).as_pointer(), [c.pyapi.
        pyobj, c.pyapi.py_ssize_t])
    kqe__asc = c.pyapi._get_function(xklzb__oiy, name='array_getptr1')
    ldz__ujn = LLType.function(lir.VoidType(), [c.pyapi.pyobj, lir.IntType(
        8).as_pointer(), c.pyapi.pyobj])
    zabnr__tpxfq = c.pyapi._get_function(ldz__ujn, name='array_setitem')
    dkgg__ymc = c.pyapi.object_getattr_string(ihjd__kvap, 'nan')
    with cgutils.for_range(builder, zfdgy__qzvkh.num_items) as nneuh__fnv:
        str_ind = nneuh__fnv.index
        mbi__vnnr = builder.sext(builder.load(builder.gep(zfdgy__qzvkh.
            index_offsets, [str_ind])), lir.IntType(64))
        rap__ywxym = builder.sext(builder.load(builder.gep(zfdgy__qzvkh.
            index_offsets, [builder.add(str_ind, str_ind.type(1))])), lir.
            IntType(64))
        mwvej__xhxa = builder.lshr(str_ind, lir.Constant(lir.IntType(64), 3))
        ldpb__mio = builder.gep(zfdgy__qzvkh.null_bitmap, [mwvej__xhxa])
        vhnyd__buic = builder.load(ldpb__mio)
        ydvs__cssy = builder.trunc(builder.and_(str_ind, lir.Constant(lir.
            IntType(64), 7)), lir.IntType(8))
        val = builder.and_(builder.lshr(vhnyd__buic, ydvs__cssy), lir.
            Constant(lir.IntType(8), 1))
        pxp__nrrps = builder.sub(rap__ywxym, mbi__vnnr)
        pxp__nrrps = builder.sub(pxp__nrrps, pxp__nrrps.type(1))
        verm__rkp = builder.call(kqe__asc, [dvn__zmh, str_ind])
        bmg__pukmq = c.builder.icmp_unsigned('!=', val, val.type(0))
        with c.builder.if_else(bmg__pukmq) as (gdulv__riaa, amqqz__cyikp):
            with gdulv__riaa:
                xip__ywht = c.pyapi.list_new(pxp__nrrps)
                with c.builder.if_then(cgutils.is_not_null(c.builder,
                    xip__ywht), likely=True):
                    with cgutils.for_range(c.builder, pxp__nrrps
                        ) as nneuh__fnv:
                        mteji__mkz = builder.add(mbi__vnnr, nneuh__fnv.index)
                        data_start = builder.load(builder.gep(zfdgy__qzvkh.
                            data_offsets, [mteji__mkz]))
                        data_start = builder.add(data_start, data_start.type(1)
                            )
                        miw__iqyua = builder.load(builder.gep(zfdgy__qzvkh.
                            data_offsets, [builder.add(mteji__mkz,
                            mteji__mkz.type(1))]))
                        nck__pjv = builder.gep(builder.extract_value(
                            zfdgy__qzvkh.data, 0), [data_start])
                        rwuq__ckbca = builder.sext(builder.sub(miw__iqyua,
                            data_start), lir.IntType(64))
                        fejbm__nbalc = c.pyapi.string_from_string_and_size(
                            nck__pjv, rwuq__ckbca)
                        c.pyapi.list_setitem(xip__ywht, nneuh__fnv.index,
                            fejbm__nbalc)
                builder.call(zabnr__tpxfq, [dvn__zmh, verm__rkp, xip__ywht])
            with amqqz__cyikp:
                builder.call(zabnr__tpxfq, [dvn__zmh, verm__rkp, dkgg__ymc])
    c.pyapi.decref(ihjd__kvap)
    c.pyapi.decref(dtype)
    c.pyapi.decref(dkgg__ymc)
    return dvn__zmh


@intrinsic
def pre_alloc_str_arr_view(typingctx, num_items_t, num_offsets_t, data_t=None):
    assert num_items_t == types.intp and num_offsets_t == types.intp

    def codegen(context, builder, sig, args):
        zjwei__hjof, gquu__mfh, nck__pjv = args
        ainck__ydhsv, xilqi__hcge = construct_str_arr_split_view(context,
            builder)
        prb__tec = lir.FunctionType(lir.VoidType(), [xilqi__hcge.type, lir.
            IntType(64), lir.IntType(64)])
        etqnf__ohglq = cgutils.get_or_insert_function(builder.module,
            prb__tec, name='str_arr_split_view_alloc')
        builder.call(etqnf__ohglq, [xilqi__hcge, zjwei__hjof, gquu__mfh])
        lbxd__gqlw = cgutils.create_struct_proxy(
            str_arr_split_view_payload_type)(context, builder, value=
            builder.load(xilqi__hcge))
        hpld__gvk = context.make_helper(builder, string_array_split_view_type)
        hpld__gvk.num_items = zjwei__hjof
        hpld__gvk.index_offsets = lbxd__gqlw.index_offsets
        hpld__gvk.data_offsets = lbxd__gqlw.data_offsets
        hpld__gvk.data = nck__pjv
        hpld__gvk.null_bitmap = lbxd__gqlw.null_bitmap
        context.nrt.incref(builder, data_t, nck__pjv)
        hpld__gvk.meminfo = ainck__ydhsv
        nfob__lugr = hpld__gvk._getvalue()
        return impl_ret_new_ref(context, builder,
            string_array_split_view_type, nfob__lugr)
    return string_array_split_view_type(types.intp, types.intp, data_t
        ), codegen


@intrinsic
def get_c_arr_ptr(typingctx, c_arr, ind_t=None):
    assert isinstance(c_arr, (types.CPointer, types.ArrayCTypes))

    def codegen(context, builder, sig, args):
        ztoj__ebnhr, ind = args
        if isinstance(sig.args[0], types.ArrayCTypes):
            ztoj__ebnhr = builder.extract_value(ztoj__ebnhr, 0)
        return builder.bitcast(builder.gep(ztoj__ebnhr, [ind]), lir.IntType
            (8).as_pointer())
    return types.voidptr(c_arr, ind_t), codegen


@intrinsic
def getitem_c_arr(typingctx, c_arr, ind_t=None):

    def codegen(context, builder, sig, args):
        ztoj__ebnhr, ind = args
        if isinstance(sig.args[0], types.ArrayCTypes):
            ztoj__ebnhr = builder.extract_value(ztoj__ebnhr, 0)
        return builder.load(builder.gep(ztoj__ebnhr, [ind]))
    return c_arr.dtype(c_arr, ind_t), codegen


@intrinsic
def setitem_c_arr(typingctx, c_arr, ind_t, item_t=None):

    def codegen(context, builder, sig, args):
        ztoj__ebnhr, ind, xcen__kavhu = args
        lulql__rcvba = builder.gep(ztoj__ebnhr, [ind])
        builder.store(xcen__kavhu, lulql__rcvba)
    return types.void(c_arr, ind_t, c_arr.dtype), codegen


@intrinsic
def get_array_ctypes_ptr(typingctx, arr_ctypes_t, ind_t=None):

    def codegen(context, builder, sig, args):
        oqxk__rwml, ind = args
        usn__pdhmp = context.make_helper(builder, arr_ctypes_t, oqxk__rwml)
        dfk__uzes = context.make_helper(builder, arr_ctypes_t)
        dfk__uzes.data = builder.gep(usn__pdhmp.data, [ind])
        dfk__uzes.meminfo = usn__pdhmp.meminfo
        typ__fzwp = dfk__uzes._getvalue()
        return impl_ret_borrowed(context, builder, arr_ctypes_t, typ__fzwp)
    return arr_ctypes_t(arr_ctypes_t, ind_t), codegen


@numba.njit(no_cpython_wrapper=True)
def get_split_view_index(arr, item_ind, str_ind):
    sxqbe__mgc = bodo.libs.int_arr_ext.get_bit_bitmap_arr(arr._null_bitmap,
        item_ind)
    if not sxqbe__mgc:
        return 0, 0, 0
    mteji__mkz = getitem_c_arr(arr._index_offsets, item_ind)
    dtu__brjil = getitem_c_arr(arr._index_offsets, item_ind + 1) - 1
    rcy__usbg = dtu__brjil - mteji__mkz
    if str_ind >= rcy__usbg:
        return 0, 0, 0
    data_start = getitem_c_arr(arr._data_offsets, mteji__mkz + str_ind)
    data_start += 1
    if mteji__mkz + str_ind == 0:
        data_start = 0
    miw__iqyua = getitem_c_arr(arr._data_offsets, mteji__mkz + str_ind + 1)
    zovcr__tgkxd = miw__iqyua - data_start
    return 1, data_start, zovcr__tgkxd


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
        cfb__uywpz = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

        def _impl(A, ind):
            mteji__mkz = getitem_c_arr(A._index_offsets, ind)
            dtu__brjil = getitem_c_arr(A._index_offsets, ind + 1)
            bpoor__bsvh = dtu__brjil - mteji__mkz - 1
            xut__hlo = bodo.libs.str_arr_ext.pre_alloc_string_array(bpoor__bsvh
                , -1)
            for dlk__fjl in range(bpoor__bsvh):
                data_start = getitem_c_arr(A._data_offsets, mteji__mkz +
                    dlk__fjl)
                data_start += 1
                if mteji__mkz + dlk__fjl == 0:
                    data_start = 0
                miw__iqyua = getitem_c_arr(A._data_offsets, mteji__mkz +
                    dlk__fjl + 1)
                zovcr__tgkxd = miw__iqyua - data_start
                lulql__rcvba = get_array_ctypes_ptr(A._data, data_start)
                bofbi__ijitr = bodo.libs.str_arr_ext.decode_utf8(lulql__rcvba,
                    zovcr__tgkxd)
                xut__hlo[dlk__fjl] = bofbi__ijitr
            return xut__hlo
        return _impl
    if A == string_array_split_view_type and ind == types.Array(types.bool_,
        1, 'C'):
        mioyn__agii = offset_type.bitwidth // 8

        def _impl(A, ind):
            bpoor__bsvh = len(A)
            if bpoor__bsvh != len(ind):
                raise IndexError(
                    'boolean index did not match indexed array along dimension 0'
                    )
            zjwei__hjof = 0
            gquu__mfh = 0
            for dlk__fjl in range(bpoor__bsvh):
                if ind[dlk__fjl]:
                    zjwei__hjof += 1
                    mteji__mkz = getitem_c_arr(A._index_offsets, dlk__fjl)
                    dtu__brjil = getitem_c_arr(A._index_offsets, dlk__fjl + 1)
                    gquu__mfh += dtu__brjil - mteji__mkz
            dvn__zmh = pre_alloc_str_arr_view(zjwei__hjof, gquu__mfh, A._data)
            item_ind = 0
            hjjno__zzh = 0
            for dlk__fjl in range(bpoor__bsvh):
                if ind[dlk__fjl]:
                    mteji__mkz = getitem_c_arr(A._index_offsets, dlk__fjl)
                    dtu__brjil = getitem_c_arr(A._index_offsets, dlk__fjl + 1)
                    bvdhb__mcwo = dtu__brjil - mteji__mkz
                    setitem_c_arr(dvn__zmh._index_offsets, item_ind, hjjno__zzh
                        )
                    lulql__rcvba = get_c_arr_ptr(A._data_offsets, mteji__mkz)
                    eimdn__rnsde = get_c_arr_ptr(dvn__zmh._data_offsets,
                        hjjno__zzh)
                    _memcpy(eimdn__rnsde, lulql__rcvba, bvdhb__mcwo,
                        mioyn__agii)
                    sxqbe__mgc = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, dlk__fjl)
                    bodo.libs.int_arr_ext.set_bit_to_arr(dvn__zmh.
                        _null_bitmap, item_ind, sxqbe__mgc)
                    item_ind += 1
                    hjjno__zzh += bvdhb__mcwo
            setitem_c_arr(dvn__zmh._index_offsets, item_ind, hjjno__zzh)
            return dvn__zmh
        return _impl
