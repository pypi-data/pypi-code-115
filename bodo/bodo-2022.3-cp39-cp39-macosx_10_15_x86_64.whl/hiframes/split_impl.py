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
        jfkyu__yzsh = [('index_offsets', types.CPointer(offset_type)), (
            'data_offsets', types.CPointer(offset_type)), ('null_bitmap',
            types.CPointer(char_typ))]
        models.StructModel.__init__(self, dmm, fe_type, jfkyu__yzsh)


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
    bjruz__ffzo = context.get_value_type(str_arr_split_view_payload_type)
    owt__pee = context.get_abi_sizeof(bjruz__ffzo)
    ejos__lqn = context.get_value_type(types.voidptr)
    mswgq__siqtm = context.get_value_type(types.uintp)
    gqyj__ooyql = lir.FunctionType(lir.VoidType(), [ejos__lqn, mswgq__siqtm,
        ejos__lqn])
    kqq__ieaat = cgutils.get_or_insert_function(builder.module, gqyj__ooyql,
        name='dtor_str_arr_split_view')
    edib__nqxlk = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, owt__pee), kqq__ieaat)
    vev__uguq = context.nrt.meminfo_data(builder, edib__nqxlk)
    aunnu__mka = builder.bitcast(vev__uguq, bjruz__ffzo.as_pointer())
    return edib__nqxlk, aunnu__mka


@intrinsic
def compute_split_view(typingctx, str_arr_typ, sep_typ=None):
    assert str_arr_typ == string_array_type and isinstance(sep_typ, types.
        StringLiteral)

    def codegen(context, builder, sig, args):
        mqppa__qjwn, fjwms__dkb = args
        edib__nqxlk, aunnu__mka = construct_str_arr_split_view(context, builder
            )
        upmz__gkr = _get_str_binary_arr_payload(context, builder,
            mqppa__qjwn, string_array_type)
        clt__qmts = lir.FunctionType(lir.VoidType(), [aunnu__mka.type, lir.
            IntType(64), lir.IntType(offset_type.bitwidth).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8)])
        xbdty__pedol = cgutils.get_or_insert_function(builder.module,
            clt__qmts, name='str_arr_split_view_impl')
        xmhn__ljx = context.make_helper(builder, offset_arr_type, upmz__gkr
            .offsets).data
        xsdss__yak = context.make_helper(builder, char_arr_type, upmz__gkr.data
            ).data
        fbm__pkj = context.make_helper(builder, null_bitmap_arr_type,
            upmz__gkr.null_bitmap).data
        vdfh__rjg = context.get_constant(types.int8, ord(sep_typ.literal_value)
            )
        builder.call(xbdty__pedol, [aunnu__mka, upmz__gkr.n_arrays,
            xmhn__ljx, xsdss__yak, fbm__pkj, vdfh__rjg])
        kgazh__tnsit = cgutils.create_struct_proxy(
            str_arr_split_view_payload_type)(context, builder, value=
            builder.load(aunnu__mka))
        ifk__lbx = context.make_helper(builder, string_array_split_view_type)
        ifk__lbx.num_items = upmz__gkr.n_arrays
        ifk__lbx.index_offsets = kgazh__tnsit.index_offsets
        ifk__lbx.data_offsets = kgazh__tnsit.data_offsets
        ifk__lbx.data = context.compile_internal(builder, lambda S:
            get_data_ptr(S), data_ctypes_type(string_array_type), [mqppa__qjwn]
            )
        ifk__lbx.null_bitmap = kgazh__tnsit.null_bitmap
        ifk__lbx.meminfo = edib__nqxlk
        lgk__wircb = ifk__lbx._getvalue()
        return impl_ret_new_ref(context, builder,
            string_array_split_view_type, lgk__wircb)
    return string_array_split_view_type(string_array_type, sep_typ), codegen


@box(StringArraySplitViewType)
def box_str_arr_split_view(typ, val, c):
    context = c.context
    builder = c.builder
    bmj__wpdi = context.make_helper(builder, string_array_split_view_type, val)
    lnp__kks = context.insert_const_string(builder.module, 'numpy')
    sij__rank = c.pyapi.import_module_noblock(lnp__kks)
    dtype = c.pyapi.object_getattr_string(sij__rank, 'object_')
    yuncn__qtgw = builder.sext(bmj__wpdi.num_items, c.pyapi.longlong)
    kjs__pheg = c.pyapi.long_from_longlong(yuncn__qtgw)
    dclq__vtgrw = c.pyapi.call_method(sij__rank, 'ndarray', (kjs__pheg, dtype))
    txk__etin = LLType.function(lir.IntType(8).as_pointer(), [c.pyapi.pyobj,
        c.pyapi.py_ssize_t])
    fynnp__gzxf = c.pyapi._get_function(txk__etin, name='array_getptr1')
    cciyx__nyt = LLType.function(lir.VoidType(), [c.pyapi.pyobj, lir.
        IntType(8).as_pointer(), c.pyapi.pyobj])
    kezw__nmxff = c.pyapi._get_function(cciyx__nyt, name='array_setitem')
    fglp__zzi = c.pyapi.object_getattr_string(sij__rank, 'nan')
    with cgutils.for_range(builder, bmj__wpdi.num_items) as gixz__fyq:
        str_ind = gixz__fyq.index
        xgfmv__mpj = builder.sext(builder.load(builder.gep(bmj__wpdi.
            index_offsets, [str_ind])), lir.IntType(64))
        zdn__uvq = builder.sext(builder.load(builder.gep(bmj__wpdi.
            index_offsets, [builder.add(str_ind, str_ind.type(1))])), lir.
            IntType(64))
        gbayy__nnx = builder.lshr(str_ind, lir.Constant(lir.IntType(64), 3))
        loce__yplr = builder.gep(bmj__wpdi.null_bitmap, [gbayy__nnx])
        nwat__ofcyz = builder.load(loce__yplr)
        xfxq__yyvg = builder.trunc(builder.and_(str_ind, lir.Constant(lir.
            IntType(64), 7)), lir.IntType(8))
        val = builder.and_(builder.lshr(nwat__ofcyz, xfxq__yyvg), lir.
            Constant(lir.IntType(8), 1))
        tsjvb__rgh = builder.sub(zdn__uvq, xgfmv__mpj)
        tsjvb__rgh = builder.sub(tsjvb__rgh, tsjvb__rgh.type(1))
        oxc__nzrak = builder.call(fynnp__gzxf, [dclq__vtgrw, str_ind])
        svare__mcx = c.builder.icmp_unsigned('!=', val, val.type(0))
        with c.builder.if_else(svare__mcx) as (kxvy__osr, ugf__fmmai):
            with kxvy__osr:
                btko__edhk = c.pyapi.list_new(tsjvb__rgh)
                with c.builder.if_then(cgutils.is_not_null(c.builder,
                    btko__edhk), likely=True):
                    with cgutils.for_range(c.builder, tsjvb__rgh) as gixz__fyq:
                        uquk__bdv = builder.add(xgfmv__mpj, gixz__fyq.index)
                        data_start = builder.load(builder.gep(bmj__wpdi.
                            data_offsets, [uquk__bdv]))
                        data_start = builder.add(data_start, data_start.type(1)
                            )
                        wvb__kcu = builder.load(builder.gep(bmj__wpdi.
                            data_offsets, [builder.add(uquk__bdv, uquk__bdv
                            .type(1))]))
                        puho__gba = builder.gep(builder.extract_value(
                            bmj__wpdi.data, 0), [data_start])
                        zob__ltc = builder.sext(builder.sub(wvb__kcu,
                            data_start), lir.IntType(64))
                        mxep__pgquv = c.pyapi.string_from_string_and_size(
                            puho__gba, zob__ltc)
                        c.pyapi.list_setitem(btko__edhk, gixz__fyq.index,
                            mxep__pgquv)
                builder.call(kezw__nmxff, [dclq__vtgrw, oxc__nzrak, btko__edhk]
                    )
            with ugf__fmmai:
                builder.call(kezw__nmxff, [dclq__vtgrw, oxc__nzrak, fglp__zzi])
    c.pyapi.decref(sij__rank)
    c.pyapi.decref(dtype)
    c.pyapi.decref(fglp__zzi)
    return dclq__vtgrw


@intrinsic
def pre_alloc_str_arr_view(typingctx, num_items_t, num_offsets_t, data_t=None):
    assert num_items_t == types.intp and num_offsets_t == types.intp

    def codegen(context, builder, sig, args):
        usuz__ootbr, sjt__nvw, puho__gba = args
        edib__nqxlk, aunnu__mka = construct_str_arr_split_view(context, builder
            )
        clt__qmts = lir.FunctionType(lir.VoidType(), [aunnu__mka.type, lir.
            IntType(64), lir.IntType(64)])
        xbdty__pedol = cgutils.get_or_insert_function(builder.module,
            clt__qmts, name='str_arr_split_view_alloc')
        builder.call(xbdty__pedol, [aunnu__mka, usuz__ootbr, sjt__nvw])
        kgazh__tnsit = cgutils.create_struct_proxy(
            str_arr_split_view_payload_type)(context, builder, value=
            builder.load(aunnu__mka))
        ifk__lbx = context.make_helper(builder, string_array_split_view_type)
        ifk__lbx.num_items = usuz__ootbr
        ifk__lbx.index_offsets = kgazh__tnsit.index_offsets
        ifk__lbx.data_offsets = kgazh__tnsit.data_offsets
        ifk__lbx.data = puho__gba
        ifk__lbx.null_bitmap = kgazh__tnsit.null_bitmap
        context.nrt.incref(builder, data_t, puho__gba)
        ifk__lbx.meminfo = edib__nqxlk
        lgk__wircb = ifk__lbx._getvalue()
        return impl_ret_new_ref(context, builder,
            string_array_split_view_type, lgk__wircb)
    return string_array_split_view_type(types.intp, types.intp, data_t
        ), codegen


@intrinsic
def get_c_arr_ptr(typingctx, c_arr, ind_t=None):
    assert isinstance(c_arr, (types.CPointer, types.ArrayCTypes))

    def codegen(context, builder, sig, args):
        mijp__bbn, ind = args
        if isinstance(sig.args[0], types.ArrayCTypes):
            mijp__bbn = builder.extract_value(mijp__bbn, 0)
        return builder.bitcast(builder.gep(mijp__bbn, [ind]), lir.IntType(8
            ).as_pointer())
    return types.voidptr(c_arr, ind_t), codegen


@intrinsic
def getitem_c_arr(typingctx, c_arr, ind_t=None):

    def codegen(context, builder, sig, args):
        mijp__bbn, ind = args
        if isinstance(sig.args[0], types.ArrayCTypes):
            mijp__bbn = builder.extract_value(mijp__bbn, 0)
        return builder.load(builder.gep(mijp__bbn, [ind]))
    return c_arr.dtype(c_arr, ind_t), codegen


@intrinsic
def setitem_c_arr(typingctx, c_arr, ind_t, item_t=None):

    def codegen(context, builder, sig, args):
        mijp__bbn, ind, ajnd__kstc = args
        mobjg__yrbjh = builder.gep(mijp__bbn, [ind])
        builder.store(ajnd__kstc, mobjg__yrbjh)
    return types.void(c_arr, ind_t, c_arr.dtype), codegen


@intrinsic
def get_array_ctypes_ptr(typingctx, arr_ctypes_t, ind_t=None):

    def codegen(context, builder, sig, args):
        cmc__gfz, ind = args
        ldd__sbcj = context.make_helper(builder, arr_ctypes_t, cmc__gfz)
        ghi__synbc = context.make_helper(builder, arr_ctypes_t)
        ghi__synbc.data = builder.gep(ldd__sbcj.data, [ind])
        ghi__synbc.meminfo = ldd__sbcj.meminfo
        ayd__vth = ghi__synbc._getvalue()
        return impl_ret_borrowed(context, builder, arr_ctypes_t, ayd__vth)
    return arr_ctypes_t(arr_ctypes_t, ind_t), codegen


@numba.njit(no_cpython_wrapper=True)
def get_split_view_index(arr, item_ind, str_ind):
    amy__bko = bodo.libs.int_arr_ext.get_bit_bitmap_arr(arr._null_bitmap,
        item_ind)
    if not amy__bko:
        return 0, 0, 0
    uquk__bdv = getitem_c_arr(arr._index_offsets, item_ind)
    csdg__dex = getitem_c_arr(arr._index_offsets, item_ind + 1) - 1
    npjia__duokl = csdg__dex - uquk__bdv
    if str_ind >= npjia__duokl:
        return 0, 0, 0
    data_start = getitem_c_arr(arr._data_offsets, uquk__bdv + str_ind)
    data_start += 1
    if uquk__bdv + str_ind == 0:
        data_start = 0
    wvb__kcu = getitem_c_arr(arr._data_offsets, uquk__bdv + str_ind + 1)
    rgk__hxr = wvb__kcu - data_start
    return 1, data_start, rgk__hxr


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
        shg__hhrzw = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

        def _impl(A, ind):
            uquk__bdv = getitem_c_arr(A._index_offsets, ind)
            csdg__dex = getitem_c_arr(A._index_offsets, ind + 1)
            glzyu__qfpx = csdg__dex - uquk__bdv - 1
            mqppa__qjwn = bodo.libs.str_arr_ext.pre_alloc_string_array(
                glzyu__qfpx, -1)
            for lxwh__zeuy in range(glzyu__qfpx):
                data_start = getitem_c_arr(A._data_offsets, uquk__bdv +
                    lxwh__zeuy)
                data_start += 1
                if uquk__bdv + lxwh__zeuy == 0:
                    data_start = 0
                wvb__kcu = getitem_c_arr(A._data_offsets, uquk__bdv +
                    lxwh__zeuy + 1)
                rgk__hxr = wvb__kcu - data_start
                mobjg__yrbjh = get_array_ctypes_ptr(A._data, data_start)
                hnu__oftm = bodo.libs.str_arr_ext.decode_utf8(mobjg__yrbjh,
                    rgk__hxr)
                mqppa__qjwn[lxwh__zeuy] = hnu__oftm
            return mqppa__qjwn
        return _impl
    if A == string_array_split_view_type and ind == types.Array(types.bool_,
        1, 'C'):
        scis__nnt = offset_type.bitwidth // 8

        def _impl(A, ind):
            glzyu__qfpx = len(A)
            if glzyu__qfpx != len(ind):
                raise IndexError(
                    'boolean index did not match indexed array along dimension 0'
                    )
            usuz__ootbr = 0
            sjt__nvw = 0
            for lxwh__zeuy in range(glzyu__qfpx):
                if ind[lxwh__zeuy]:
                    usuz__ootbr += 1
                    uquk__bdv = getitem_c_arr(A._index_offsets, lxwh__zeuy)
                    csdg__dex = getitem_c_arr(A._index_offsets, lxwh__zeuy + 1)
                    sjt__nvw += csdg__dex - uquk__bdv
            dclq__vtgrw = pre_alloc_str_arr_view(usuz__ootbr, sjt__nvw, A._data
                )
            item_ind = 0
            ilbv__gem = 0
            for lxwh__zeuy in range(glzyu__qfpx):
                if ind[lxwh__zeuy]:
                    uquk__bdv = getitem_c_arr(A._index_offsets, lxwh__zeuy)
                    csdg__dex = getitem_c_arr(A._index_offsets, lxwh__zeuy + 1)
                    owsy__iujtb = csdg__dex - uquk__bdv
                    setitem_c_arr(dclq__vtgrw._index_offsets, item_ind,
                        ilbv__gem)
                    mobjg__yrbjh = get_c_arr_ptr(A._data_offsets, uquk__bdv)
                    voovo__rat = get_c_arr_ptr(dclq__vtgrw._data_offsets,
                        ilbv__gem)
                    _memcpy(voovo__rat, mobjg__yrbjh, owsy__iujtb, scis__nnt)
                    amy__bko = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A.
                        _null_bitmap, lxwh__zeuy)
                    bodo.libs.int_arr_ext.set_bit_to_arr(dclq__vtgrw.
                        _null_bitmap, item_ind, amy__bko)
                    item_ind += 1
                    ilbv__gem += owsy__iujtb
            setitem_c_arr(dclq__vtgrw._index_offsets, item_ind, ilbv__gem)
            return dclq__vtgrw
        return _impl
