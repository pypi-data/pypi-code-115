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
        lgo__kbs = [('index_offsets', types.CPointer(offset_type)), (
            'data_offsets', types.CPointer(offset_type)), ('null_bitmap',
            types.CPointer(char_typ))]
        models.StructModel.__init__(self, dmm, fe_type, lgo__kbs)


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
    smzyd__mfpp = context.get_value_type(str_arr_split_view_payload_type)
    fwrkl__bfb = context.get_abi_sizeof(smzyd__mfpp)
    usj__yhhsm = context.get_value_type(types.voidptr)
    xly__mfebt = context.get_value_type(types.uintp)
    zrd__giwf = lir.FunctionType(lir.VoidType(), [usj__yhhsm, xly__mfebt,
        usj__yhhsm])
    qkdc__npda = cgutils.get_or_insert_function(builder.module, zrd__giwf,
        name='dtor_str_arr_split_view')
    hyis__nnj = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, fwrkl__bfb), qkdc__npda)
    iuqvw__kws = context.nrt.meminfo_data(builder, hyis__nnj)
    ifahm__fcpth = builder.bitcast(iuqvw__kws, smzyd__mfpp.as_pointer())
    return hyis__nnj, ifahm__fcpth


@intrinsic
def compute_split_view(typingctx, str_arr_typ, sep_typ=None):
    assert str_arr_typ == string_array_type and isinstance(sep_typ, types.
        StringLiteral)

    def codegen(context, builder, sig, args):
        gputz__rmm, mkwki__dupg = args
        hyis__nnj, ifahm__fcpth = construct_str_arr_split_view(context, builder
            )
        gawpr__ewwr = _get_str_binary_arr_payload(context, builder,
            gputz__rmm, string_array_type)
        fve__axdm = lir.FunctionType(lir.VoidType(), [ifahm__fcpth.type,
            lir.IntType(64), lir.IntType(offset_type.bitwidth).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8)])
        ufb__dpzgf = cgutils.get_or_insert_function(builder.module,
            fve__axdm, name='str_arr_split_view_impl')
        wyi__xpc = context.make_helper(builder, offset_arr_type,
            gawpr__ewwr.offsets).data
        fotd__ermu = context.make_helper(builder, char_arr_type,
            gawpr__ewwr.data).data
        zpa__rrmuc = context.make_helper(builder, null_bitmap_arr_type,
            gawpr__ewwr.null_bitmap).data
        lke__uxkob = context.get_constant(types.int8, ord(sep_typ.
            literal_value))
        builder.call(ufb__dpzgf, [ifahm__fcpth, gawpr__ewwr.n_arrays,
            wyi__xpc, fotd__ermu, zpa__rrmuc, lke__uxkob])
        drqc__aduft = cgutils.create_struct_proxy(
            str_arr_split_view_payload_type)(context, builder, value=
            builder.load(ifahm__fcpth))
        uyt__skr = context.make_helper(builder, string_array_split_view_type)
        uyt__skr.num_items = gawpr__ewwr.n_arrays
        uyt__skr.index_offsets = drqc__aduft.index_offsets
        uyt__skr.data_offsets = drqc__aduft.data_offsets
        uyt__skr.data = context.compile_internal(builder, lambda S:
            get_data_ptr(S), data_ctypes_type(string_array_type), [gputz__rmm])
        uyt__skr.null_bitmap = drqc__aduft.null_bitmap
        uyt__skr.meminfo = hyis__nnj
        vuws__ydoa = uyt__skr._getvalue()
        return impl_ret_new_ref(context, builder,
            string_array_split_view_type, vuws__ydoa)
    return string_array_split_view_type(string_array_type, sep_typ), codegen


@box(StringArraySplitViewType)
def box_str_arr_split_view(typ, val, c):
    context = c.context
    builder = c.builder
    mjf__jdh = context.make_helper(builder, string_array_split_view_type, val)
    sfg__uajiw = context.insert_const_string(builder.module, 'numpy')
    bzd__ljbt = c.pyapi.import_module_noblock(sfg__uajiw)
    dtype = c.pyapi.object_getattr_string(bzd__ljbt, 'object_')
    feq__paij = builder.sext(mjf__jdh.num_items, c.pyapi.longlong)
    hsusi__tmmb = c.pyapi.long_from_longlong(feq__paij)
    cok__ngdv = c.pyapi.call_method(bzd__ljbt, 'ndarray', (hsusi__tmmb, dtype))
    xeqxn__qtmb = LLType.function(lir.IntType(8).as_pointer(), [c.pyapi.
        pyobj, c.pyapi.py_ssize_t])
    inxk__eqjsn = c.pyapi._get_function(xeqxn__qtmb, name='array_getptr1')
    jxfns__efyeh = LLType.function(lir.VoidType(), [c.pyapi.pyobj, lir.
        IntType(8).as_pointer(), c.pyapi.pyobj])
    kcb__dvn = c.pyapi._get_function(jxfns__efyeh, name='array_setitem')
    ojlhj__pknd = c.pyapi.object_getattr_string(bzd__ljbt, 'nan')
    with cgutils.for_range(builder, mjf__jdh.num_items) as bbykb__nbvzz:
        str_ind = bbykb__nbvzz.index
        egz__kiaol = builder.sext(builder.load(builder.gep(mjf__jdh.
            index_offsets, [str_ind])), lir.IntType(64))
        octk__sww = builder.sext(builder.load(builder.gep(mjf__jdh.
            index_offsets, [builder.add(str_ind, str_ind.type(1))])), lir.
            IntType(64))
        vxyr__snpdi = builder.lshr(str_ind, lir.Constant(lir.IntType(64), 3))
        nubdx__fbraa = builder.gep(mjf__jdh.null_bitmap, [vxyr__snpdi])
        orey__bnnvh = builder.load(nubdx__fbraa)
        xks__pdzx = builder.trunc(builder.and_(str_ind, lir.Constant(lir.
            IntType(64), 7)), lir.IntType(8))
        val = builder.and_(builder.lshr(orey__bnnvh, xks__pdzx), lir.
            Constant(lir.IntType(8), 1))
        lbghe__jyp = builder.sub(octk__sww, egz__kiaol)
        lbghe__jyp = builder.sub(lbghe__jyp, lbghe__jyp.type(1))
        qrecc__tdw = builder.call(inxk__eqjsn, [cok__ngdv, str_ind])
        uytk__zsamt = c.builder.icmp_unsigned('!=', val, val.type(0))
        with c.builder.if_else(uytk__zsamt) as (ilq__ldtvu, gqp__suoy):
            with ilq__ldtvu:
                vnny__qpuw = c.pyapi.list_new(lbghe__jyp)
                with c.builder.if_then(cgutils.is_not_null(c.builder,
                    vnny__qpuw), likely=True):
                    with cgutils.for_range(c.builder, lbghe__jyp
                        ) as bbykb__nbvzz:
                        hjlx__zjrhf = builder.add(egz__kiaol, bbykb__nbvzz.
                            index)
                        data_start = builder.load(builder.gep(mjf__jdh.
                            data_offsets, [hjlx__zjrhf]))
                        data_start = builder.add(data_start, data_start.type(1)
                            )
                        conw__alqmg = builder.load(builder.gep(mjf__jdh.
                            data_offsets, [builder.add(hjlx__zjrhf,
                            hjlx__zjrhf.type(1))]))
                        uqgx__jok = builder.gep(builder.extract_value(
                            mjf__jdh.data, 0), [data_start])
                        cgez__zzu = builder.sext(builder.sub(conw__alqmg,
                            data_start), lir.IntType(64))
                        puz__hfj = c.pyapi.string_from_string_and_size(
                            uqgx__jok, cgez__zzu)
                        c.pyapi.list_setitem(vnny__qpuw, bbykb__nbvzz.index,
                            puz__hfj)
                builder.call(kcb__dvn, [cok__ngdv, qrecc__tdw, vnny__qpuw])
            with gqp__suoy:
                builder.call(kcb__dvn, [cok__ngdv, qrecc__tdw, ojlhj__pknd])
    c.pyapi.decref(bzd__ljbt)
    c.pyapi.decref(dtype)
    c.pyapi.decref(ojlhj__pknd)
    return cok__ngdv


@intrinsic
def pre_alloc_str_arr_view(typingctx, num_items_t, num_offsets_t, data_t=None):
    assert num_items_t == types.intp and num_offsets_t == types.intp

    def codegen(context, builder, sig, args):
        etenr__xhv, oye__njwpp, uqgx__jok = args
        hyis__nnj, ifahm__fcpth = construct_str_arr_split_view(context, builder
            )
        fve__axdm = lir.FunctionType(lir.VoidType(), [ifahm__fcpth.type,
            lir.IntType(64), lir.IntType(64)])
        ufb__dpzgf = cgutils.get_or_insert_function(builder.module,
            fve__axdm, name='str_arr_split_view_alloc')
        builder.call(ufb__dpzgf, [ifahm__fcpth, etenr__xhv, oye__njwpp])
        drqc__aduft = cgutils.create_struct_proxy(
            str_arr_split_view_payload_type)(context, builder, value=
            builder.load(ifahm__fcpth))
        uyt__skr = context.make_helper(builder, string_array_split_view_type)
        uyt__skr.num_items = etenr__xhv
        uyt__skr.index_offsets = drqc__aduft.index_offsets
        uyt__skr.data_offsets = drqc__aduft.data_offsets
        uyt__skr.data = uqgx__jok
        uyt__skr.null_bitmap = drqc__aduft.null_bitmap
        context.nrt.incref(builder, data_t, uqgx__jok)
        uyt__skr.meminfo = hyis__nnj
        vuws__ydoa = uyt__skr._getvalue()
        return impl_ret_new_ref(context, builder,
            string_array_split_view_type, vuws__ydoa)
    return string_array_split_view_type(types.intp, types.intp, data_t
        ), codegen


@intrinsic
def get_c_arr_ptr(typingctx, c_arr, ind_t=None):
    assert isinstance(c_arr, (types.CPointer, types.ArrayCTypes))

    def codegen(context, builder, sig, args):
        ekbxq__kvn, ind = args
        if isinstance(sig.args[0], types.ArrayCTypes):
            ekbxq__kvn = builder.extract_value(ekbxq__kvn, 0)
        return builder.bitcast(builder.gep(ekbxq__kvn, [ind]), lir.IntType(
            8).as_pointer())
    return types.voidptr(c_arr, ind_t), codegen


@intrinsic
def getitem_c_arr(typingctx, c_arr, ind_t=None):

    def codegen(context, builder, sig, args):
        ekbxq__kvn, ind = args
        if isinstance(sig.args[0], types.ArrayCTypes):
            ekbxq__kvn = builder.extract_value(ekbxq__kvn, 0)
        return builder.load(builder.gep(ekbxq__kvn, [ind]))
    return c_arr.dtype(c_arr, ind_t), codegen


@intrinsic
def setitem_c_arr(typingctx, c_arr, ind_t, item_t=None):

    def codegen(context, builder, sig, args):
        ekbxq__kvn, ind, enze__ooxp = args
        vfqfh__htl = builder.gep(ekbxq__kvn, [ind])
        builder.store(enze__ooxp, vfqfh__htl)
    return types.void(c_arr, ind_t, c_arr.dtype), codegen


@intrinsic
def get_array_ctypes_ptr(typingctx, arr_ctypes_t, ind_t=None):

    def codegen(context, builder, sig, args):
        tmhd__tht, ind = args
        liv__snshc = context.make_helper(builder, arr_ctypes_t, tmhd__tht)
        kml__thdq = context.make_helper(builder, arr_ctypes_t)
        kml__thdq.data = builder.gep(liv__snshc.data, [ind])
        kml__thdq.meminfo = liv__snshc.meminfo
        srqo__nejl = kml__thdq._getvalue()
        return impl_ret_borrowed(context, builder, arr_ctypes_t, srqo__nejl)
    return arr_ctypes_t(arr_ctypes_t, ind_t), codegen


@numba.njit(no_cpython_wrapper=True)
def get_split_view_index(arr, item_ind, str_ind):
    zoayy__vsp = bodo.libs.int_arr_ext.get_bit_bitmap_arr(arr._null_bitmap,
        item_ind)
    if not zoayy__vsp:
        return 0, 0, 0
    hjlx__zjrhf = getitem_c_arr(arr._index_offsets, item_ind)
    izge__cbj = getitem_c_arr(arr._index_offsets, item_ind + 1) - 1
    ymtqn__xqk = izge__cbj - hjlx__zjrhf
    if str_ind >= ymtqn__xqk:
        return 0, 0, 0
    data_start = getitem_c_arr(arr._data_offsets, hjlx__zjrhf + str_ind)
    data_start += 1
    if hjlx__zjrhf + str_ind == 0:
        data_start = 0
    conw__alqmg = getitem_c_arr(arr._data_offsets, hjlx__zjrhf + str_ind + 1)
    soubk__sogak = conw__alqmg - data_start
    return 1, data_start, soubk__sogak


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
        nmt__lnn = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

        def _impl(A, ind):
            hjlx__zjrhf = getitem_c_arr(A._index_offsets, ind)
            izge__cbj = getitem_c_arr(A._index_offsets, ind + 1)
            exige__nwugx = izge__cbj - hjlx__zjrhf - 1
            gputz__rmm = bodo.libs.str_arr_ext.pre_alloc_string_array(
                exige__nwugx, -1)
            for iod__ktsra in range(exige__nwugx):
                data_start = getitem_c_arr(A._data_offsets, hjlx__zjrhf +
                    iod__ktsra)
                data_start += 1
                if hjlx__zjrhf + iod__ktsra == 0:
                    data_start = 0
                conw__alqmg = getitem_c_arr(A._data_offsets, hjlx__zjrhf +
                    iod__ktsra + 1)
                soubk__sogak = conw__alqmg - data_start
                vfqfh__htl = get_array_ctypes_ptr(A._data, data_start)
                ndtrr__ezuch = bodo.libs.str_arr_ext.decode_utf8(vfqfh__htl,
                    soubk__sogak)
                gputz__rmm[iod__ktsra] = ndtrr__ezuch
            return gputz__rmm
        return _impl
    if A == string_array_split_view_type and ind == types.Array(types.bool_,
        1, 'C'):
        wzgxa__ehdk = offset_type.bitwidth // 8

        def _impl(A, ind):
            exige__nwugx = len(A)
            if exige__nwugx != len(ind):
                raise IndexError(
                    'boolean index did not match indexed array along dimension 0'
                    )
            etenr__xhv = 0
            oye__njwpp = 0
            for iod__ktsra in range(exige__nwugx):
                if ind[iod__ktsra]:
                    etenr__xhv += 1
                    hjlx__zjrhf = getitem_c_arr(A._index_offsets, iod__ktsra)
                    izge__cbj = getitem_c_arr(A._index_offsets, iod__ktsra + 1)
                    oye__njwpp += izge__cbj - hjlx__zjrhf
            cok__ngdv = pre_alloc_str_arr_view(etenr__xhv, oye__njwpp, A._data)
            item_ind = 0
            qkoy__esgyt = 0
            for iod__ktsra in range(exige__nwugx):
                if ind[iod__ktsra]:
                    hjlx__zjrhf = getitem_c_arr(A._index_offsets, iod__ktsra)
                    izge__cbj = getitem_c_arr(A._index_offsets, iod__ktsra + 1)
                    zvzox__yjo = izge__cbj - hjlx__zjrhf
                    setitem_c_arr(cok__ngdv._index_offsets, item_ind,
                        qkoy__esgyt)
                    vfqfh__htl = get_c_arr_ptr(A._data_offsets, hjlx__zjrhf)
                    wuqih__bmd = get_c_arr_ptr(cok__ngdv._data_offsets,
                        qkoy__esgyt)
                    _memcpy(wuqih__bmd, vfqfh__htl, zvzox__yjo, wzgxa__ehdk)
                    zoayy__vsp = bodo.libs.int_arr_ext.get_bit_bitmap_arr(A
                        ._null_bitmap, iod__ktsra)
                    bodo.libs.int_arr_ext.set_bit_to_arr(cok__ngdv.
                        _null_bitmap, item_ind, zoayy__vsp)
                    item_ind += 1
                    qkoy__esgyt += zvzox__yjo
            setitem_c_arr(cok__ngdv._index_offsets, item_ind, qkoy__esgyt)
            return cok__ngdv
        return _impl
