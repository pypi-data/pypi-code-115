"""Array implementation for variable-size array items.
Corresponds to Spark's ArrayType: https://spark.apache.org/docs/latest/sql-reference.html
Corresponds to Arrow's Variable-size List: https://arrow.apache.org/docs/format/Columnar.html

The values are stored in a contingous data array, while an offsets array marks the
individual arrays. For example:
value:             [[1, 2], [3], None, [5, 4, 6], []]
data:              [1, 2, 3, 5, 4, 6]
offsets:           [0, 2, 3, 3, 6, 6]
"""
import operator
import llvmlite.binding as ll
import numba
import numpy as np
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import impl_ret_borrowed
from numba.extending import NativeValue, box, intrinsic, models, overload, overload_attribute, overload_method, register_model, unbox
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
from bodo.hiframes.datetime_date_ext import datetime_date_type
from bodo.libs import array_ext
from bodo.utils.cg_helpers import gen_allocate_array, get_array_elem_counts, get_bitmap_bit, is_na_value, pyarray_setitem, seq_getitem, set_bitmap_bit, to_arr_obj_if_list_obj
from bodo.utils.indexing import add_nested_counts, init_nested_counts
from bodo.utils.typing import BodoError, is_iterable_type, is_list_like_index_type
ll.add_symbol('count_total_elems_list_array', array_ext.
    count_total_elems_list_array)
ll.add_symbol('array_item_array_from_sequence', array_ext.
    array_item_array_from_sequence)
ll.add_symbol('np_array_from_array_item_array', array_ext.
    np_array_from_array_item_array)
offset_type = types.uint64
np_offset_type = numba.np.numpy_support.as_dtype(offset_type)


class ArrayItemArrayType(types.ArrayCompatible):

    def __init__(self, dtype):
        assert bodo.utils.utils.is_array_typ(dtype, False)
        self.dtype = dtype
        super(ArrayItemArrayType, self).__init__(name=
            'ArrayItemArrayType({})'.format(dtype))

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    def copy(self):
        return ArrayItemArrayType(self.dtype)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


class ArrayItemArrayPayloadType(types.Type):

    def __init__(self, array_type):
        self.array_type = array_type
        super(ArrayItemArrayPayloadType, self).__init__(name=
            'ArrayItemArrayPayloadType({})'.format(array_type))

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(ArrayItemArrayPayloadType)
class ArrayItemArrayPayloadModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        yfvl__nab = [('n_arrays', types.int64), ('data', fe_type.array_type
            .dtype), ('offsets', types.Array(offset_type, 1, 'C')), (
            'null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, yfvl__nab)


@register_model(ArrayItemArrayType)
class ArrayItemArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = ArrayItemArrayPayloadType(fe_type)
        yfvl__nab = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, yfvl__nab)


def define_array_item_dtor(context, builder, array_item_type, payload_type):
    gyq__enn = builder.module
    jhkvq__quyz = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    ygp__qpx = cgutils.get_or_insert_function(gyq__enn, jhkvq__quyz, name=
        '.dtor.array_item.{}'.format(array_item_type.dtype))
    if not ygp__qpx.is_declaration:
        return ygp__qpx
    ygp__qpx.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(ygp__qpx.append_basic_block())
    dww__kchal = ygp__qpx.args[0]
    bubb__kcr = context.get_value_type(payload_type).as_pointer()
    gvhrz__xwla = builder.bitcast(dww__kchal, bubb__kcr)
    hio__uyf = context.make_helper(builder, payload_type, ref=gvhrz__xwla)
    context.nrt.decref(builder, array_item_type.dtype, hio__uyf.data)
    context.nrt.decref(builder, types.Array(offset_type, 1, 'C'), hio__uyf.
        offsets)
    context.nrt.decref(builder, types.Array(types.uint8, 1, 'C'), hio__uyf.
        null_bitmap)
    builder.ret_void()
    return ygp__qpx


def construct_array_item_array(context, builder, array_item_type, n_arrays,
    n_elems, c=None):
    payload_type = ArrayItemArrayPayloadType(array_item_type)
    cdxqe__omo = context.get_value_type(payload_type)
    rwce__ihp = context.get_abi_sizeof(cdxqe__omo)
    hlu__lfh = define_array_item_dtor(context, builder, array_item_type,
        payload_type)
    zasi__ycgad = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, rwce__ihp), hlu__lfh)
    atkmw__vjsn = context.nrt.meminfo_data(builder, zasi__ycgad)
    umou__cuda = builder.bitcast(atkmw__vjsn, cdxqe__omo.as_pointer())
    hio__uyf = cgutils.create_struct_proxy(payload_type)(context, builder)
    hio__uyf.n_arrays = n_arrays
    dkyt__yyac = n_elems.type.count
    emfa__nbe = builder.extract_value(n_elems, 0)
    oaie__duxp = cgutils.alloca_once_value(builder, emfa__nbe)
    lpum__jml = builder.icmp_signed('==', emfa__nbe, lir.Constant(emfa__nbe
        .type, -1))
    with builder.if_then(lpum__jml):
        builder.store(n_arrays, oaie__duxp)
    n_elems = cgutils.pack_array(builder, [builder.load(oaie__duxp)] + [
        builder.extract_value(n_elems, wya__nmkwj) for wya__nmkwj in range(
        1, dkyt__yyac)])
    hio__uyf.data = gen_allocate_array(context, builder, array_item_type.
        dtype, n_elems, c)
    nox__hvn = builder.add(n_arrays, lir.Constant(lir.IntType(64), 1))
    vss__cdif = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(offset_type, 1, 'C'), [nox__hvn])
    offsets_ptr = vss__cdif.data
    builder.store(context.get_constant(offset_type, 0), offsets_ptr)
    builder.store(builder.trunc(builder.extract_value(n_elems, 0), lir.
        IntType(offset_type.bitwidth)), builder.gep(offsets_ptr, [n_arrays]))
    hio__uyf.offsets = vss__cdif._getvalue()
    ipm__kqcl = builder.udiv(builder.add(n_arrays, lir.Constant(lir.IntType
        (64), 7)), lir.Constant(lir.IntType(64), 8))
    tgun__bsz = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(types.uint8, 1, 'C'), [ipm__kqcl])
    null_bitmap_ptr = tgun__bsz.data
    hio__uyf.null_bitmap = tgun__bsz._getvalue()
    builder.store(hio__uyf._getvalue(), umou__cuda)
    return zasi__ycgad, hio__uyf.data, offsets_ptr, null_bitmap_ptr


def _unbox_array_item_array_copy_data(arr_typ, arr_obj, c, data_arr,
    item_ind, n_items):
    context = c.context
    builder = c.builder
    arr_obj = to_arr_obj_if_list_obj(c, context, builder, arr_obj, arr_typ)
    arr_val = c.pyapi.to_native_value(arr_typ, arr_obj).value
    sig = types.none(arr_typ, types.int64, types.int64, arr_typ)

    def copy_data(data_arr, item_ind, n_items, arr_val):
        data_arr[item_ind:item_ind + n_items] = arr_val
    jst__tqf, pzhc__yetjl = c.pyapi.call_jit_code(copy_data, sig, [data_arr,
        item_ind, n_items, arr_val])
    c.context.nrt.decref(builder, arr_typ, arr_val)


def _unbox_array_item_array_generic(typ, val, c, n_arrays, data_arr,
    offsets_ptr, null_bitmap_ptr):
    context = c.context
    builder = c.builder
    ssuai__goo = context.insert_const_string(builder.module, 'pandas')
    jaxgo__kyij = c.pyapi.import_module_noblock(ssuai__goo)
    bvae__uvpe = c.pyapi.object_getattr_string(jaxgo__kyij, 'NA')
    ycyhc__uyhls = c.context.get_constant(offset_type, 0)
    builder.store(ycyhc__uyhls, offsets_ptr)
    uooh__zsbo = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with cgutils.for_range(builder, n_arrays) as nhdj__mhf:
        yqo__ham = nhdj__mhf.index
        item_ind = builder.load(uooh__zsbo)
        builder.store(builder.trunc(item_ind, lir.IntType(offset_type.
            bitwidth)), builder.gep(offsets_ptr, [yqo__ham]))
        arr_obj = seq_getitem(builder, context, val, yqo__ham)
        set_bitmap_bit(builder, null_bitmap_ptr, yqo__ham, 0)
        tjri__yxoex = is_na_value(builder, context, arr_obj, bvae__uvpe)
        znh__sew = builder.icmp_unsigned('!=', tjri__yxoex, lir.Constant(
            tjri__yxoex.type, 1))
        with builder.if_then(znh__sew):
            set_bitmap_bit(builder, null_bitmap_ptr, yqo__ham, 1)
            n_items = bodo.utils.utils.object_length(c, arr_obj)
            _unbox_array_item_array_copy_data(typ.dtype, arr_obj, c,
                data_arr, item_ind, n_items)
            builder.store(builder.add(item_ind, n_items), uooh__zsbo)
        c.pyapi.decref(arr_obj)
    builder.store(builder.trunc(builder.load(uooh__zsbo), lir.IntType(
        offset_type.bitwidth)), builder.gep(offsets_ptr, [n_arrays]))
    c.pyapi.decref(jaxgo__kyij)
    c.pyapi.decref(bvae__uvpe)


@unbox(ArrayItemArrayType)
def unbox_array_item_array(typ, val, c):
    shs__uvx = isinstance(typ.dtype, types.Array) and typ.dtype.dtype in (types
        .int64, types.float64, types.bool_, datetime_date_type)
    n_arrays = bodo.utils.utils.object_length(c, val)
    if shs__uvx:
        jhkvq__quyz = lir.FunctionType(lir.IntType(64), [lir.IntType(8).
            as_pointer()])
        dhy__giwc = cgutils.get_or_insert_function(c.builder.module,
            jhkvq__quyz, name='count_total_elems_list_array')
        n_elems = cgutils.pack_array(c.builder, [c.builder.call(dhy__giwc,
            [val])])
    else:
        nfhnt__xit = get_array_elem_counts(c, c.builder, c.context, val, typ)
        n_elems = cgutils.pack_array(c.builder, [c.builder.extract_value(
            nfhnt__xit, wya__nmkwj) for wya__nmkwj in range(1, nfhnt__xit.
            type.count)])
    zasi__ycgad, data_arr, offsets_ptr, null_bitmap_ptr = (
        construct_array_item_array(c.context, c.builder, typ, n_arrays,
        n_elems, c))
    if shs__uvx:
        omfpv__pihv = bodo.utils.utils.numba_to_c_type(typ.dtype.dtype)
        rmhli__qeoz = c.context.make_array(typ.dtype)(c.context, c.builder,
            data_arr).data
        jhkvq__quyz = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(32)])
        ygp__qpx = cgutils.get_or_insert_function(c.builder.module,
            jhkvq__quyz, name='array_item_array_from_sequence')
        c.builder.call(ygp__qpx, [val, c.builder.bitcast(rmhli__qeoz, lir.
            IntType(8).as_pointer()), offsets_ptr, null_bitmap_ptr, lir.
            Constant(lir.IntType(32), omfpv__pihv)])
    else:
        _unbox_array_item_array_generic(typ, val, c, n_arrays, data_arr,
            offsets_ptr, null_bitmap_ptr)
    ypvo__aqutg = c.context.make_helper(c.builder, typ)
    ypvo__aqutg.meminfo = zasi__ycgad
    mve__dsoid = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(ypvo__aqutg._getvalue(), is_error=mve__dsoid)


def _get_array_item_arr_payload(context, builder, arr_typ, arr):
    ypvo__aqutg = context.make_helper(builder, arr_typ, arr)
    payload_type = ArrayItemArrayPayloadType(arr_typ)
    atkmw__vjsn = context.nrt.meminfo_data(builder, ypvo__aqutg.meminfo)
    umou__cuda = builder.bitcast(atkmw__vjsn, context.get_value_type(
        payload_type).as_pointer())
    hio__uyf = cgutils.create_struct_proxy(payload_type)(context, builder,
        builder.load(umou__cuda))
    return hio__uyf


def _box_array_item_array_generic(typ, c, n_arrays, data_arr, offsets_ptr,
    null_bitmap_ptr):
    context = c.context
    builder = c.builder
    ssuai__goo = context.insert_const_string(builder.module, 'numpy')
    oib__cotjw = c.pyapi.import_module_noblock(ssuai__goo)
    cab__trkf = c.pyapi.object_getattr_string(oib__cotjw, 'object_')
    hdooj__vhnc = c.pyapi.long_from_longlong(n_arrays)
    dnrno__dhy = c.pyapi.call_method(oib__cotjw, 'ndarray', (hdooj__vhnc,
        cab__trkf))
    lkj__mtmq = c.pyapi.object_getattr_string(oib__cotjw, 'nan')
    uooh__zsbo = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(64), 0))
    with cgutils.for_range(builder, n_arrays) as nhdj__mhf:
        yqo__ham = nhdj__mhf.index
        pyarray_setitem(builder, context, dnrno__dhy, yqo__ham, lkj__mtmq)
        hjzi__gij = get_bitmap_bit(builder, null_bitmap_ptr, yqo__ham)
        pvcze__vganf = builder.icmp_unsigned('!=', hjzi__gij, lir.Constant(
            lir.IntType(8), 0))
        with builder.if_then(pvcze__vganf):
            n_items = builder.sext(builder.sub(builder.load(builder.gep(
                offsets_ptr, [builder.add(yqo__ham, lir.Constant(yqo__ham.
                type, 1))])), builder.load(builder.gep(offsets_ptr, [
                yqo__ham]))), lir.IntType(64))
            item_ind = builder.load(uooh__zsbo)
            jst__tqf, qvnpk__gkwjk = c.pyapi.call_jit_code(lambda data_arr,
                item_ind, n_items: data_arr[item_ind:item_ind + n_items],
                typ.dtype(typ.dtype, types.int64, types.int64), [data_arr,
                item_ind, n_items])
            builder.store(builder.add(item_ind, n_items), uooh__zsbo)
            arr_obj = c.pyapi.from_native_value(typ.dtype, qvnpk__gkwjk, c.
                env_manager)
            pyarray_setitem(builder, context, dnrno__dhy, yqo__ham, arr_obj)
            c.pyapi.decref(arr_obj)
    c.pyapi.decref(oib__cotjw)
    c.pyapi.decref(cab__trkf)
    c.pyapi.decref(hdooj__vhnc)
    c.pyapi.decref(lkj__mtmq)
    return dnrno__dhy


@box(ArrayItemArrayType)
def box_array_item_arr(typ, val, c):
    hio__uyf = _get_array_item_arr_payload(c.context, c.builder, typ, val)
    data_arr = hio__uyf.data
    offsets_ptr = c.context.make_helper(c.builder, types.Array(offset_type,
        1, 'C'), hio__uyf.offsets).data
    null_bitmap_ptr = c.context.make_helper(c.builder, types.Array(types.
        uint8, 1, 'C'), hio__uyf.null_bitmap).data
    if isinstance(typ.dtype, types.Array) and typ.dtype.dtype in (types.
        int64, types.float64, types.bool_, datetime_date_type):
        omfpv__pihv = bodo.utils.utils.numba_to_c_type(typ.dtype.dtype)
        rmhli__qeoz = c.context.make_helper(c.builder, typ.dtype, data_arr
            ).data
        jhkvq__quyz = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(32)])
        sba__rmqf = cgutils.get_or_insert_function(c.builder.module,
            jhkvq__quyz, name='np_array_from_array_item_array')
        arr = c.builder.call(sba__rmqf, [hio__uyf.n_arrays, c.builder.
            bitcast(rmhli__qeoz, lir.IntType(8).as_pointer()), offsets_ptr,
            null_bitmap_ptr, lir.Constant(lir.IntType(32), omfpv__pihv)])
    else:
        arr = _box_array_item_array_generic(typ, c, hio__uyf.n_arrays,
            data_arr, offsets_ptr, null_bitmap_ptr)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def lower_pre_alloc_array_item_array(context, builder, sig, args):
    array_item_type = sig.return_type
    ogx__pjkjv, vhaj__wskkx, ewr__caub = args
    uoyi__zsi = bodo.utils.transform.get_type_alloc_counts(array_item_type.
        dtype)
    zwct__ogcsg = sig.args[1]
    if not isinstance(zwct__ogcsg, types.UniTuple):
        vhaj__wskkx = cgutils.pack_array(builder, [lir.Constant(lir.IntType
            (64), -1) for ewr__caub in range(uoyi__zsi)])
    elif zwct__ogcsg.count < uoyi__zsi:
        vhaj__wskkx = cgutils.pack_array(builder, [builder.extract_value(
            vhaj__wskkx, wya__nmkwj) for wya__nmkwj in range(zwct__ogcsg.
            count)] + [lir.Constant(lir.IntType(64), -1) for ewr__caub in
            range(uoyi__zsi - zwct__ogcsg.count)])
    zasi__ycgad, ewr__caub, ewr__caub, ewr__caub = construct_array_item_array(
        context, builder, array_item_type, ogx__pjkjv, vhaj__wskkx)
    ypvo__aqutg = context.make_helper(builder, array_item_type)
    ypvo__aqutg.meminfo = zasi__ycgad
    return ypvo__aqutg._getvalue()


@intrinsic
def pre_alloc_array_item_array(typingctx, num_arrs_typ, num_values_typ,
    dtype_typ=None):
    assert isinstance(num_arrs_typ, types.Integer)
    array_item_type = ArrayItemArrayType(dtype_typ.instance_type)
    num_values_typ = types.unliteral(num_values_typ)
    return array_item_type(types.int64, num_values_typ, dtype_typ
        ), lower_pre_alloc_array_item_array


def pre_alloc_array_item_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 3 and not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


(ArrayAnalysis.
    _analyze_op_call_bodo_libs_array_item_arr_ext_pre_alloc_array_item_array
    ) = pre_alloc_array_item_array_equiv


def init_array_item_array_codegen(context, builder, signature, args):
    n_arrays, lkwr__ltju, vss__cdif, tgun__bsz = args
    array_item_type = signature.return_type
    payload_type = ArrayItemArrayPayloadType(array_item_type)
    cdxqe__omo = context.get_value_type(payload_type)
    rwce__ihp = context.get_abi_sizeof(cdxqe__omo)
    hlu__lfh = define_array_item_dtor(context, builder, array_item_type,
        payload_type)
    zasi__ycgad = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, rwce__ihp), hlu__lfh)
    atkmw__vjsn = context.nrt.meminfo_data(builder, zasi__ycgad)
    umou__cuda = builder.bitcast(atkmw__vjsn, cdxqe__omo.as_pointer())
    hio__uyf = cgutils.create_struct_proxy(payload_type)(context, builder)
    hio__uyf.n_arrays = n_arrays
    hio__uyf.data = lkwr__ltju
    hio__uyf.offsets = vss__cdif
    hio__uyf.null_bitmap = tgun__bsz
    builder.store(hio__uyf._getvalue(), umou__cuda)
    context.nrt.incref(builder, signature.args[1], lkwr__ltju)
    context.nrt.incref(builder, signature.args[2], vss__cdif)
    context.nrt.incref(builder, signature.args[3], tgun__bsz)
    ypvo__aqutg = context.make_helper(builder, array_item_type)
    ypvo__aqutg.meminfo = zasi__ycgad
    return ypvo__aqutg._getvalue()


@intrinsic
def init_array_item_array(typingctx, n_arrays_typ, data_type, offsets_typ,
    null_bitmap_typ=None):
    assert null_bitmap_typ == types.Array(types.uint8, 1, 'C')
    dpx__tugzn = ArrayItemArrayType(data_type)
    sig = dpx__tugzn(types.int64, data_type, offsets_typ, null_bitmap_typ)
    return sig, init_array_item_array_codegen


@intrinsic
def get_offsets(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        hio__uyf = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            hio__uyf.offsets)
    return types.Array(offset_type, 1, 'C')(arr_typ), codegen


@intrinsic
def get_offsets_ind(typingctx, arr_typ, ind_t=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, ind = args
        hio__uyf = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        rmhli__qeoz = context.make_array(types.Array(offset_type, 1, 'C'))(
            context, builder, hio__uyf.offsets).data
        vss__cdif = builder.bitcast(rmhli__qeoz, lir.IntType(offset_type.
            bitwidth).as_pointer())
        return builder.load(builder.gep(vss__cdif, [ind]))
    return offset_type(arr_typ, types.int64), codegen


@intrinsic
def get_data(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        hio__uyf = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            hio__uyf.data)
    return arr_typ.dtype(arr_typ), codegen


@intrinsic
def get_null_bitmap(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        hio__uyf = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            hio__uyf.null_bitmap)
    return types.Array(types.uint8, 1, 'C')(arr_typ), codegen


def alias_ext_single_array(lhs_name, args, alias_map, arg_aliases):
    assert len(args) == 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['get_offsets',
    'bodo.libs.array_item_arr_ext'] = alias_ext_single_array
numba.core.ir_utils.alias_func_extensions['get_data',
    'bodo.libs.array_item_arr_ext'] = alias_ext_single_array
numba.core.ir_utils.alias_func_extensions['get_null_bitmap',
    'bodo.libs.array_item_arr_ext'] = alias_ext_single_array


@intrinsic
def get_n_arrays(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        hio__uyf = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        return hio__uyf.n_arrays
    return types.int64(arr_typ), codegen


@intrinsic
def replace_data_arr(typingctx, arr_typ, data_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType
        ) and data_typ == arr_typ.dtype

    def codegen(context, builder, sig, args):
        arr, nngcl__hhtx = args
        ypvo__aqutg = context.make_helper(builder, arr_typ, arr)
        payload_type = ArrayItemArrayPayloadType(arr_typ)
        atkmw__vjsn = context.nrt.meminfo_data(builder, ypvo__aqutg.meminfo)
        umou__cuda = builder.bitcast(atkmw__vjsn, context.get_value_type(
            payload_type).as_pointer())
        hio__uyf = cgutils.create_struct_proxy(payload_type)(context,
            builder, builder.load(umou__cuda))
        context.nrt.decref(builder, data_typ, hio__uyf.data)
        hio__uyf.data = nngcl__hhtx
        context.nrt.incref(builder, data_typ, nngcl__hhtx)
        builder.store(hio__uyf._getvalue(), umou__cuda)
    return types.none(arr_typ, data_typ), codegen


@numba.njit(no_cpython_wrapper=True)
def ensure_data_capacity(arr, old_size, new_size):
    lkwr__ltju = get_data(arr)
    nfk__xdnjb = len(lkwr__ltju)
    if nfk__xdnjb < new_size:
        mlm__ubmwl = max(2 * nfk__xdnjb, new_size)
        nngcl__hhtx = bodo.libs.array_kernels.resize_and_copy(lkwr__ltju,
            old_size, mlm__ubmwl)
        replace_data_arr(arr, nngcl__hhtx)


@numba.njit(no_cpython_wrapper=True)
def trim_excess_data(arr):
    lkwr__ltju = get_data(arr)
    vss__cdif = get_offsets(arr)
    smwjk__lmaw = len(lkwr__ltju)
    bjzl__ubjo = vss__cdif[-1]
    if smwjk__lmaw != bjzl__ubjo:
        nngcl__hhtx = bodo.libs.array_kernels.resize_and_copy(lkwr__ltju,
            bjzl__ubjo, bjzl__ubjo)
        replace_data_arr(arr, nngcl__hhtx)


@overload(len, no_unliteral=True)
def overload_array_item_arr_len(A):
    if isinstance(A, ArrayItemArrayType):
        return lambda A: get_n_arrays(A)


@overload_attribute(ArrayItemArrayType, 'shape')
def overload_array_item_arr_shape(A):
    return lambda A: (get_n_arrays(A),)


@overload_attribute(ArrayItemArrayType, 'dtype')
def overload_array_item_arr_dtype(A):
    return lambda A: np.object_


@overload_attribute(ArrayItemArrayType, 'ndim')
def overload_array_item_arr_ndim(A):
    return lambda A: 1


@overload_attribute(ArrayItemArrayType, 'nbytes')
def overload_array_item_arr_nbytes(A):
    return lambda A: get_data(A).nbytes + get_offsets(A
        ).nbytes + get_null_bitmap(A).nbytes


@overload(operator.getitem, no_unliteral=True)
def array_item_arr_getitem_array(arr, ind):
    if not isinstance(arr, ArrayItemArrayType):
        return
    if isinstance(ind, types.Integer):

        def array_item_arr_getitem_impl(arr, ind):
            if ind < 0:
                ind += len(arr)
            vss__cdif = get_offsets(arr)
            lkwr__ltju = get_data(arr)
            jdk__ajqmn = vss__cdif[ind]
            pdf__nksb = vss__cdif[ind + 1]
            return lkwr__ltju[jdk__ajqmn:pdf__nksb]
        return array_item_arr_getitem_impl
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        nhlnc__xjwi = arr.dtype

        def impl_bool(arr, ind):
            bdxf__crhcg = len(arr)
            if bdxf__crhcg != len(ind):
                raise IndexError(
                    'boolean index did not match indexed array along dimension 0'
                    )
            tgun__bsz = get_null_bitmap(arr)
            n_arrays = 0
            iesqk__whm = init_nested_counts(nhlnc__xjwi)
            for wya__nmkwj in range(bdxf__crhcg):
                if ind[wya__nmkwj]:
                    n_arrays += 1
                    esefr__jkzp = arr[wya__nmkwj]
                    iesqk__whm = add_nested_counts(iesqk__whm, esefr__jkzp)
            dnrno__dhy = pre_alloc_array_item_array(n_arrays, iesqk__whm,
                nhlnc__xjwi)
            guh__pjqx = get_null_bitmap(dnrno__dhy)
            smh__soj = 0
            for abq__eruu in range(bdxf__crhcg):
                if ind[abq__eruu]:
                    dnrno__dhy[smh__soj] = arr[abq__eruu]
                    oge__dvuz = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        tgun__bsz, abq__eruu)
                    bodo.libs.int_arr_ext.set_bit_to_arr(guh__pjqx,
                        smh__soj, oge__dvuz)
                    smh__soj += 1
            return dnrno__dhy
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        nhlnc__xjwi = arr.dtype

        def impl_int(arr, ind):
            tgun__bsz = get_null_bitmap(arr)
            bdxf__crhcg = len(ind)
            n_arrays = bdxf__crhcg
            iesqk__whm = init_nested_counts(nhlnc__xjwi)
            for qcs__imkd in range(bdxf__crhcg):
                wya__nmkwj = ind[qcs__imkd]
                esefr__jkzp = arr[wya__nmkwj]
                iesqk__whm = add_nested_counts(iesqk__whm, esefr__jkzp)
            dnrno__dhy = pre_alloc_array_item_array(n_arrays, iesqk__whm,
                nhlnc__xjwi)
            guh__pjqx = get_null_bitmap(dnrno__dhy)
            for iyo__fexdj in range(bdxf__crhcg):
                abq__eruu = ind[iyo__fexdj]
                dnrno__dhy[iyo__fexdj] = arr[abq__eruu]
                oge__dvuz = bodo.libs.int_arr_ext.get_bit_bitmap_arr(tgun__bsz,
                    abq__eruu)
                bodo.libs.int_arr_ext.set_bit_to_arr(guh__pjqx, iyo__fexdj,
                    oge__dvuz)
            return dnrno__dhy
        return impl_int
    if isinstance(ind, types.SliceType):

        def impl_slice(arr, ind):
            bdxf__crhcg = len(arr)
            knlt__hau = numba.cpython.unicode._normalize_slice(ind, bdxf__crhcg
                )
            pdmu__ztsm = np.arange(knlt__hau.start, knlt__hau.stop,
                knlt__hau.step)
            return arr[pdmu__ztsm]
        return impl_slice


@overload(operator.setitem)
def array_item_arr_setitem(A, idx, val):
    if not isinstance(A, ArrayItemArrayType):
        return
    if isinstance(idx, types.Integer):

        def impl_scalar(A, idx, val):
            vss__cdif = get_offsets(A)
            tgun__bsz = get_null_bitmap(A)
            if idx == 0:
                vss__cdif[0] = 0
            n_items = len(val)
            hqvjy__fuzag = vss__cdif[idx] + n_items
            ensure_data_capacity(A, vss__cdif[idx], hqvjy__fuzag)
            lkwr__ltju = get_data(A)
            vss__cdif[idx + 1] = vss__cdif[idx] + n_items
            lkwr__ltju[vss__cdif[idx]:vss__cdif[idx + 1]] = val
            bodo.libs.int_arr_ext.set_bit_to_arr(tgun__bsz, idx, 1)
        return impl_scalar
    if isinstance(idx, types.SliceType) and A.dtype == val:

        def impl_slice_elem(A, idx, val):
            knlt__hau = numba.cpython.unicode._normalize_slice(idx, len(A))
            for wya__nmkwj in range(knlt__hau.start, knlt__hau.stop,
                knlt__hau.step):
                A[wya__nmkwj] = val
        return impl_slice_elem
    if isinstance(idx, types.SliceType) and is_iterable_type(val):

        def impl_slice(A, idx, val):
            val = bodo.utils.conversion.coerce_to_array(val,
                use_nullable_array=True)
            vss__cdif = get_offsets(A)
            tgun__bsz = get_null_bitmap(A)
            fsetp__spf = get_offsets(val)
            wkq__esxcf = get_data(val)
            vsree__wqeou = get_null_bitmap(val)
            bdxf__crhcg = len(A)
            knlt__hau = numba.cpython.unicode._normalize_slice(idx, bdxf__crhcg
                )
            saqx__plsq, lpya__pwhev = knlt__hau.start, knlt__hau.stop
            assert knlt__hau.step == 1
            if saqx__plsq == 0:
                vss__cdif[saqx__plsq] = 0
            bzmrt__eiy = vss__cdif[saqx__plsq]
            hqvjy__fuzag = bzmrt__eiy + len(wkq__esxcf)
            ensure_data_capacity(A, bzmrt__eiy, hqvjy__fuzag)
            lkwr__ltju = get_data(A)
            lkwr__ltju[bzmrt__eiy:bzmrt__eiy + len(wkq__esxcf)] = wkq__esxcf
            vss__cdif[saqx__plsq:lpya__pwhev + 1] = fsetp__spf + bzmrt__eiy
            ngrh__uap = 0
            for wya__nmkwj in range(saqx__plsq, lpya__pwhev):
                oge__dvuz = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                    vsree__wqeou, ngrh__uap)
                bodo.libs.int_arr_ext.set_bit_to_arr(tgun__bsz, wya__nmkwj,
                    oge__dvuz)
                ngrh__uap += 1
        return impl_slice
    raise BodoError(
        'only setitem with scalar index is currently supported for list arrays'
        )


@overload_method(ArrayItemArrayType, 'copy', no_unliteral=True)
def overload_array_item_arr_copy(A):

    def copy_impl(A):
        return init_array_item_array(len(A), get_data(A).copy(),
            get_offsets(A).copy(), get_null_bitmap(A).copy())
    return copy_impl
