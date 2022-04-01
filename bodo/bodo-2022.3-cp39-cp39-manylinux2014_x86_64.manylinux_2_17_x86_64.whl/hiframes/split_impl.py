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
        vstm__vdluh = [('index_offsets', types.CPointer(offset_type)), (
            'data_offsets', types.CPointer(offset_type)), ('null_bitmap',
            types.CPointer(char_typ))]
        models.StructModel.__init__(self, dmm, fe_type, vstm__vdluh)


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
    dzsw__lnsf = context.get_value_type(str_arr_split_view_payload_type)
    iis__mylm = context.get_abi_sizeof(dzsw__lnsf)
    rew__nzce = context.get_value_type(types.voidptr)
    ugown__fayg = context.get_value_type(types.uintp)
    ohy__gkbim = lir.FunctionType(lir.VoidType(), [rew__nzce, ugown__fayg,
        rew__nzce])
    sop__hrc = cgutils.get_or_insert_function(builder.module, ohy__gkbim,
        name='dtor_str_arr_split_view')
    sqlwr__qqo = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, iis__mylm), sop__hrc)
    ghxi__vwzri = context.nrt.meminfo_data(builder, sqlwr__qqo)
    hlxkq__qgch = builder.bitcast(ghxi__vwzri, dzsw__lnsf.as_pointer())
    return sqlwr__qqo, hlxkq__qgch


@intrinsic
def compute_split_view(typingctx, str_arr_typ, sep_typ=None):
    assert str_arr_typ == string_array_type and isinstance(sep_typ, types.
        StringLiteral)

    def codegen(context, builder, sig, args):
        mxi__jtfo, spfzl__kql = args
        sqlwr__qqo, hlxkq__qgch = construct_str_arr_split_view(context, builder
            )
        vwc__jew = _get_str_binary_arr_payload(context, builder, mxi__jtfo,
            string_array_type)
        oqruh__vcz = lir.FunctionType(lir.VoidType(), [hlxkq__qgch.type,
            lir.IntType(64), lir.IntType(offset_type.bitwidth).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8)])
        chidt__qbls = cgutils.get_or_insert_function(builder.module,
            oqruh__vcz, name='str_arr_split_view_impl')
        dco__dgaq = context.make_helper(builder, offset_arr_type, vwc__jew.
            offsets).data
        ynbz__gbtx = context.make_helper(builder, char_arr_type, vwc__jew.data
            ).data
        dkvpg__rojzs = context.make_helper(builder, null_bitmap_arr_type,
            vwc__jew.null_bitmap).data
        fqcn__ktkll = context.get_constant(types.int8, ord(sep_typ.
            literal_value))
        builder.call(chidt__qbls, [hlxkq__qgch, vwc__jew.n_arrays,
            dco__dgaq, ynbz__gbtx, dkvpg__rojzs, fqcn__ktkll])
        szf__cuump = cgutils.create_struct_proxy(
            str_arr_split_view_payload_type)(context, builder, value=
            builder.load(hlxkq__qgch))
        uqa__fef = context.make_helper(builder, string_array_split_view_type)
        uqa__fef.num_items = vwc__jew.n_arrays
        uqa__fef.index_offsets = szf__cuump.index_offsets
        uqa__fef.data_offsets = szf__cuump.data_offsets
        uqa__fef.data = context.compile_internal(builder, lambda S:
            get_data_ptr(S), data_ctypes_type(string_array_type), [mxi__jtfo])
        uqa__fef.null_bitmap = szf__cuump.null_bitmap
        uqa__fef.meminfo = sqlwr__qqo
        esl__glfx = uqa__fef._getvalue()
        return impl_ret_new_ref(context, builder,
            string_array_split_view_type, esl__glfx)
    return string_array_split_view_type(string_array_type, sep_typ), codegen


@box(StringArraySplitViewType)
def box_str_arr_split_view(typ, val, c):
    context = c.context
    builder = c.builder
    tuu__zudqk = context.make_helper(builder, string_array_split_view_type, val
        )
    utf__xpjz = context.insert_const_string(builder.module, 'numpy')
    ivdmd__hbsi = c.pyapi.import_module_noblock(utf__xpjz)
    dtype = c.pyapi.object_getattr_string(ivdmd__hbsi, 'object_')
    gjgyv__xwti = builder.sext(tuu__zudqk.num_items, c.pyapi.longlong)
    qevri__zbomj = c.pyapi.long_from_longlong(gjgyv__xwti)
    mmwz__rul = c.pyapi.call_method(ivdmd__hbsi, 'ndarray', (qevri__zbomj,
        dtype))
    mbbw__bvz = LLType.function(lir.IntType(8).as_pointer(), [c.pyapi.pyobj,
        c.pyapi.py_ssize_t])
    kbxys__mjh = c.pyapi._get_function(mbbw__bvz, name='array_getptr1')
    teby__hiwgc = LLType.function(lir.VoidType(), [c.pyapi.pyobj, lir.
        IntType(8).as_pointer(), c.pyapi.pyobj])
    icsgy__xzzmw = c.pyapi._get_function(teby__hiwgc, name='array_setitem')
    zssw__amn = c.pyapi.object_getattr_string(ivdmd__hbsi, 'nan')
    with cgutils.for_range(builder, tuu__zudqk.num_items) as xvta__faeo:
        str_ind = xvta__faeo.index
        cpx__lwbx = builder.sext(builder.load(builder.gep(tuu__zudqk.
            index_offsets, [str_ind])), lir.IntType(64))
        wxj__qlmy = builder.sext(builder.load(builder.gep(tuu__zudqk.
            index_offsets, [builder.add(str_ind, str_ind.type(1))])), lir.
            IntType(64))
        uze__xgi = builder.lshr(str_ind, lir.Constant(lir.IntType(64), 3))
        htvgt__bdh = builder.gep(tuu__zudqk.null_bitmap, [uze__xgi])
        wsqgd__kxbay = builder.load(htvgt__bdh)
        xkmrp__viz = builder.trunc(builder.and_(str_ind, lir.Constant(lir.
            IntType(64), 7)), lir.IntType(8))
        val = builder.and_(builder.lshr(wsqgd__kxbay, xkmrp__viz), lir.
            Constant(lir.IntType(8), 1))
        oqwq__wik = builder.sub(wxj__qlmy, cpx__lwbx)
        oqwq__wik = builder.sub(oqwq__wik, oqwq__wik.type(1))
        jax__gpfq = builder.call(kbxys__mjh, [mmwz__rul, str_ind])
        fbt__ynp = c.builder.icmp_unsigned('!=', val, val.type(0))
        with c.builder.if_else(fbt__ynp) as (voz__jplda, nha__rfbqy):
            with voz__jplda:
                jbmz__ulec = c.pyapi.list_new(oqwq__wik)
                with c.builder.if_then(cgutils.is_not_null(c.builder,
                    jbmz__ulec), likely=True):
                    with cgutils.for_range(c.builder, oqwq__wik) as xvta__faeo:
                        fcv__sskx = builder.add(cpx__lwbx, xvta__faeo.index)
                        data_start = builder.load(builder.gep(tuu__zudqk.
                            data_offsets, [fcv__sskx]))
                        data_start = builder.add(data_start, data_start.type(1)
                            )
                        leu__dei = builder.load(builder.gep(tuu__zudqk.
                            data_offsets, [builder.add(fcv__sskx, fcv__sskx
                            .type(1))]))
                        cbkcj__pwuf = builder.gep(builder.extract_value(
                            tuu__zudqk.data, 0), [data_start])
                        afumf__wyq = builder.sext(builder.sub(leu__dei,
                            data_start), lir.IntType(64))
                        fwzo__xfab = c.pyapi.string_from_string_and_size(
                            cbkcj__pwuf, afumf__wyq)
                        c.pyapi.list_setitem(jbmz__ulec, xvta__faeo.index,
                            fwzo__xfab)
                builder.call(icsgy__xzzmw, [mmwz__rul, jax__gpfq, jbmz__ulec])
            with nha__rfbqy:
                builder.call(icsgy__xzzmw, [mmwz__rul, jax__gpfq, zssw__amn])
    c.pyapi.decref(ivdmd__hbsi)
    c.pyapi.decref(dtype)
    c.pyapi.decref(zssw__amn)
    return mmwz__rul


@intrinsic
def pre_alloc_str_arr_view(typingctx, num_items_t, num_offsets_t, data_t=None):
    assert num_items_t == types.intp and num_offsets_t == types.intp

    def codegen(context, builder, sig, args):
        xjkmu__rolhu, ihqq__cik, cbkcj__pwuf = args
        sqlwr__qqo, hlxkq__qgch = construct_str_arr_split_view(context, builder
            )
        oqruh__vcz = lir.FunctionType(lir.VoidType(), [hlxkq__qgch.type,
            lir.IntType(64), lir.IntType(64)])
        chidt__qbls = cgutils.get_or_insert_function(builder.module,
            oqruh__vcz, name='str_arr_split_view_alloc')
        builder.call(chidt__qbls, [hlxkq__qgch, xjkmu__rolhu, ihqq__cik])
        szf__cuump = cgutils.create_struct_proxy(
            str_arr_split_view_payload_type)(context, builder, value=
            builder.load(hlxkq__qgch))
        uqa__fef = context.make_helper(builder, string_array_split_view_type)
        uqa__fef.num_items = xjkmu__rolhu
        uqa__fef.index_offsets = szf__cuump.index_offsets
        uqa__fef.data_offsets = szf__cuump.data_offsets
        uqa__fef.data = cbkcj__pwuf
        uqa__fef.null_bitmap = szf__cuump.null_bitmap
        context.nrt.incref(builder, data_t, cbkcj__pwuf)
        uqa__fef.meminfo = sqlwr__qqo
        esl__glfx = uqa__fef._getvalue()
        return impl_ret_new_ref(context, builder,
            string_array_split_view_type, esl__glfx)
    return string_array_split_view_type(types.intp, types.intp, data_t
        ), codegen


@intrinsic
def get_c_arr_ptr(typingctx, c_arr, ind_t=None):
    assert isinstance(c_arr, (types.CPointer, types.ArrayCTypes))

    def codegen(context, builder, sig, args):
        fvkef__hixdt, ind = args
        if isinstance(sig.args[0], types.ArrayCTypes):
            fvkef__hixdt = builder.extract_value(fvkef__hixdt, 0)
        return builder.bitcast(builder.gep(fvkef__hixdt, [ind]), lir.
            IntType(8).as_pointer())
    return types.voidptr(c_arr, ind_t), codegen


@intrinsic
def getitem_c_arr(typingctx, c_arr, ind_t=None):

    def codegen(context, builder, sig, args):
        fvkef__hixdt, ind = args
        if isinstance(sig.args[0], types.ArrayCTypes):
            fvkef__hixdt = builder.extract_value(fvkef__hixdt, 0)
        return builder.load(builder.gep(fvkef__hixdt, [ind]))
    return c_arr.dtype(c_arr, ind_t), codegen


@intrinsic
def setitem_c_arr(typingctx, c_arr, ind_t, item_t=None):

    def codegen(context, builder, sig, args):
        fvkef__hixdt, ind, sus__heodp = args
        nubrf__tqbus = builder.gep(fvkef__hixdt, [ind])
        builder.store(sus__heodp, nubrf__tqbus)
    return types.void(c_arr, ind_t, c_arr.dtype), codegen


@intrinsic
def get_array_ctypes_ptr(typingctx, arr_ctypes_t, ind_t=None):

    def codegen(context, builder, sig, args):
        umlk__qqt, ind = args
        curm__ziok = context.make_helper(builder, arr_ctypes_t, umlk__qqt)
        eupgr__pjyj = context.make_helper(builder, arr_ctypes_t)
        eupgr__pjyj.data = builder.gep(curm__ziok.data, [ind])
        eupgr__pjyj.meminfo = curm__ziok.meminfo
        nvp__hzbbz = eupgr__pjyj._getvalue()
        return impl_ret_borrowed(context, builder, arr_ctypes_t, nvp__hzbbz)
    return arr_ctypes_t(arr_ctypes_t, ind_t), codegen


@numba.njit(no_cpython_wrapper=True)
def get_split_view_index(arr, item_ind, str_ind):
    elt__nxtev = bodo.libs.int_arr_ext.get_bit_bitmap_arr(arr._null_bitmap,
        item_ind)
    if not elt__nxtev:
        return 0, 0, 0
    fcv__sskx = getitem_c_arr(arr._index_offsets, item_ind)
    gpod__ynzhs = getitem_c_arr(arr._index_offsets, item_ind + 1) - 1
    kiq__stl = gpod__ynzhs - fcv__sskx
    if str_ind >= kiq__stl:
        return 0, 0, 0
    data_start = getitem_c_arr(arr._data_offsets, fcv__sskx + str_ind)
    data_start += 1
    if fcv__sskx + str_ind == 0:
        data_start = 0
    leu__dei = getitem_c_arr(arr._data_offsets, fcv__sskx + str_ind + 1)
    ozmq__xauzu = leu__dei - data_start
    return 1, data_start, ozmq__xauzu


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
        tcp__vige = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

        def _impl(A, ind):
            fcv__sskx = getitem_c_arr(A._index_offsets, ind)
            gpod__ynzhs = getitem_c_arr(A._index_offsets, ind + 1)
            rwsf__mhetf = gpod__ynzhs - fcv__sskx - 1
            mxi__jtfo = bodo.libs.str_arr_ext.pre_alloc_string_array(
                rwsf__mhetf, -1)
            for pvwt__zhnfi in range(rwsf__mhetf):
                data_start = getitem_c_arr(A._data_offsets, fcv__sskx +
                    pvwt__zhnfi)
                data_start += 1
                if fcv__sskx + pvwt__zhnfi == 0:
                    data_start = 0
                leu__dei = getitem_c_arr(A._data_offsets, fcv__sskx +
                    pvwt__zhnfi + 1)
                ozmq__xauzu = leu__dei - data_start
                nubrf__tqbus = get_array_ctypes_ptr(A._data, data_start)
                jfjns__xli = bodo.libs.str_arr_ext.decode_utf8(nubrf__tqbus,
                    ozmq__xauzu)
                mxi__jtfo[pvwt__zhnfi] = jfjns__xli
            return mxi__jtfo
        return _impl
    if A == string_array_split_view_type and ind == types.Array(types.bool_,
        1, 'C'):
        wtas__xjudw = offset_type.bitwidth // 8

        def _impl(A, ind):
            rwsf__mhetf = len(A)
            if rwsf__mhetf != len(ind):
                raise IndexError(
                    'boolean index did not match indexed array along dimension 0'
                    )
            xjkmu__rolhu = 0
            ihqq__cik = 0
            for pvwt__zhnfi in range(rwsf__mhetf):
                if ind[pvwt__zhnfi]:
                    xjkmu__rolhu += 1
                    fcv__sskx = getitem_c_arr(A._index_offsets, pvwt__zhnfi)
                    gpod__ynzhs = getitem_c_arr(A._index_offsets, 
                        pvwt__zhnfi + 1)
                    ihqq__cik += gpod__ynzhs - fcv__sskx
            mmwz__rul = pre_alloc_str_arr_view(xjkmu__rolhu, ihqq__cik, A._data
                )
            item_ind = 0
            yfyry__tffhe = 0
            for pvwt__zhnfi in range(rwsf__mhetf):
                if ind[pvwt__zhnfi]:
                    fcv__sskx = getitem_c_arr(A._index_offsets, pvwt__zhnfi)
                    gpod__ynzhs = getitem_c_arr(A._index_offsets, 
                        pvwt__zhnfi + 1)
                    fogc__mficy = gpod__ynzhs - fcv__sskx
                    setitem_c_arr(mmwz__rul._index_offsets, item_ind,
                        yfyry__tffhe)
                    nubrf__tqbus = get_c_arr_ptr(A._data_offsets, fcv__sskx)
                    xycz__css = get_c_arr_ptr(mmwz__rul._data_offsets,
                        yfyry__tffhe)
                    _memcpy(xycz__css, nubrf__tqbus, fogc__mficy, wtas__xjudw)
                    elt__nxtev = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, pvwt__zhnfi)
                    bodo.libs.int_arr_ext.set_bit_to_arr(mmwz__rul.
                        _null_bitmap, item_ind, elt__nxtev)
                    item_ind += 1
                    yfyry__tffhe += fogc__mficy
            setitem_c_arr(mmwz__rul._index_offsets, item_ind, yfyry__tffhe)
            return mmwz__rul
        return _impl
