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
        rfmfa__kql = [('n_arrays', types.int64), ('data', fe_type.
            array_type.dtype), ('offsets', types.Array(offset_type, 1, 'C')
            ), ('null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, rfmfa__kql)


@register_model(ArrayItemArrayType)
class ArrayItemArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = ArrayItemArrayPayloadType(fe_type)
        rfmfa__kql = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, rfmfa__kql)


def define_array_item_dtor(context, builder, array_item_type, payload_type):
    ctfrz__ofrh = builder.module
    nrl__jhmnq = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    xlsmu__rcdc = cgutils.get_or_insert_function(ctfrz__ofrh, nrl__jhmnq,
        name='.dtor.array_item.{}'.format(array_item_type.dtype))
    if not xlsmu__rcdc.is_declaration:
        return xlsmu__rcdc
    xlsmu__rcdc.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(xlsmu__rcdc.append_basic_block())
    sek__lvygd = xlsmu__rcdc.args[0]
    wma__fwzh = context.get_value_type(payload_type).as_pointer()
    vps__wbxry = builder.bitcast(sek__lvygd, wma__fwzh)
    hxurn__mmjuh = context.make_helper(builder, payload_type, ref=vps__wbxry)
    context.nrt.decref(builder, array_item_type.dtype, hxurn__mmjuh.data)
    context.nrt.decref(builder, types.Array(offset_type, 1, 'C'),
        hxurn__mmjuh.offsets)
    context.nrt.decref(builder, types.Array(types.uint8, 1, 'C'),
        hxurn__mmjuh.null_bitmap)
    builder.ret_void()
    return xlsmu__rcdc


def construct_array_item_array(context, builder, array_item_type, n_arrays,
    n_elems, c=None):
    payload_type = ArrayItemArrayPayloadType(array_item_type)
    abm__ovhmo = context.get_value_type(payload_type)
    gqomi__ftl = context.get_abi_sizeof(abm__ovhmo)
    twi__kag = define_array_item_dtor(context, builder, array_item_type,
        payload_type)
    bhs__mlgt = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, gqomi__ftl), twi__kag)
    rvd__uua = context.nrt.meminfo_data(builder, bhs__mlgt)
    tmh__ddpk = builder.bitcast(rvd__uua, abm__ovhmo.as_pointer())
    hxurn__mmjuh = cgutils.create_struct_proxy(payload_type)(context, builder)
    hxurn__mmjuh.n_arrays = n_arrays
    petbq__tue = n_elems.type.count
    focw__bbikg = builder.extract_value(n_elems, 0)
    pqjc__jkt = cgutils.alloca_once_value(builder, focw__bbikg)
    ijaoc__jyuyy = builder.icmp_signed('==', focw__bbikg, lir.Constant(
        focw__bbikg.type, -1))
    with builder.if_then(ijaoc__jyuyy):
        builder.store(n_arrays, pqjc__jkt)
    n_elems = cgutils.pack_array(builder, [builder.load(pqjc__jkt)] + [
        builder.extract_value(n_elems, ykftl__cfzl) for ykftl__cfzl in
        range(1, petbq__tue)])
    hxurn__mmjuh.data = gen_allocate_array(context, builder,
        array_item_type.dtype, n_elems, c)
    gta__iukrk = builder.add(n_arrays, lir.Constant(lir.IntType(64), 1))
    ryn__vfst = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(offset_type, 1, 'C'), [gta__iukrk])
    offsets_ptr = ryn__vfst.data
    builder.store(context.get_constant(offset_type, 0), offsets_ptr)
    builder.store(builder.trunc(builder.extract_value(n_elems, 0), lir.
        IntType(offset_type.bitwidth)), builder.gep(offsets_ptr, [n_arrays]))
    hxurn__mmjuh.offsets = ryn__vfst._getvalue()
    jclbi__weyb = builder.udiv(builder.add(n_arrays, lir.Constant(lir.
        IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
    shiv__byzh = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(types.uint8, 1, 'C'), [jclbi__weyb])
    null_bitmap_ptr = shiv__byzh.data
    hxurn__mmjuh.null_bitmap = shiv__byzh._getvalue()
    builder.store(hxurn__mmjuh._getvalue(), tmh__ddpk)
    return bhs__mlgt, hxurn__mmjuh.data, offsets_ptr, null_bitmap_ptr


def _unbox_array_item_array_copy_data(arr_typ, arr_obj, c, data_arr,
    item_ind, n_items):
    context = c.context
    builder = c.builder
    arr_obj = to_arr_obj_if_list_obj(c, context, builder, arr_obj, arr_typ)
    arr_val = c.pyapi.to_native_value(arr_typ, arr_obj).value
    sig = types.none(arr_typ, types.int64, types.int64, arr_typ)

    def copy_data(data_arr, item_ind, n_items, arr_val):
        data_arr[item_ind:item_ind + n_items] = arr_val
    ecyv__xfsd, enhny__gipw = c.pyapi.call_jit_code(copy_data, sig, [
        data_arr, item_ind, n_items, arr_val])
    c.context.nrt.decref(builder, arr_typ, arr_val)


def _unbox_array_item_array_generic(typ, val, c, n_arrays, data_arr,
    offsets_ptr, null_bitmap_ptr):
    context = c.context
    builder = c.builder
    tfxwq__wat = context.insert_const_string(builder.module, 'pandas')
    lcr__jpu = c.pyapi.import_module_noblock(tfxwq__wat)
    sbd__hhgbj = c.pyapi.object_getattr_string(lcr__jpu, 'NA')
    vhv__ziy = c.context.get_constant(offset_type, 0)
    builder.store(vhv__ziy, offsets_ptr)
    zajl__ahve = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with cgutils.for_range(builder, n_arrays) as ylgj__odqpd:
        jpe__ifgj = ylgj__odqpd.index
        item_ind = builder.load(zajl__ahve)
        builder.store(builder.trunc(item_ind, lir.IntType(offset_type.
            bitwidth)), builder.gep(offsets_ptr, [jpe__ifgj]))
        arr_obj = seq_getitem(builder, context, val, jpe__ifgj)
        set_bitmap_bit(builder, null_bitmap_ptr, jpe__ifgj, 0)
        jiszo__vznm = is_na_value(builder, context, arr_obj, sbd__hhgbj)
        ynshb__cvne = builder.icmp_unsigned('!=', jiszo__vznm, lir.Constant
            (jiszo__vznm.type, 1))
        with builder.if_then(ynshb__cvne):
            set_bitmap_bit(builder, null_bitmap_ptr, jpe__ifgj, 1)
            n_items = bodo.utils.utils.object_length(c, arr_obj)
            _unbox_array_item_array_copy_data(typ.dtype, arr_obj, c,
                data_arr, item_ind, n_items)
            builder.store(builder.add(item_ind, n_items), zajl__ahve)
        c.pyapi.decref(arr_obj)
    builder.store(builder.trunc(builder.load(zajl__ahve), lir.IntType(
        offset_type.bitwidth)), builder.gep(offsets_ptr, [n_arrays]))
    c.pyapi.decref(lcr__jpu)
    c.pyapi.decref(sbd__hhgbj)


@unbox(ArrayItemArrayType)
def unbox_array_item_array(typ, val, c):
    wiysw__bmb = isinstance(typ.dtype, types.Array) and typ.dtype.dtype in (
        types.int64, types.float64, types.bool_, datetime_date_type)
    n_arrays = bodo.utils.utils.object_length(c, val)
    if wiysw__bmb:
        nrl__jhmnq = lir.FunctionType(lir.IntType(64), [lir.IntType(8).
            as_pointer()])
        yipc__eqwck = cgutils.get_or_insert_function(c.builder.module,
            nrl__jhmnq, name='count_total_elems_list_array')
        n_elems = cgutils.pack_array(c.builder, [c.builder.call(yipc__eqwck,
            [val])])
    else:
        qxx__oae = get_array_elem_counts(c, c.builder, c.context, val, typ)
        n_elems = cgutils.pack_array(c.builder, [c.builder.extract_value(
            qxx__oae, ykftl__cfzl) for ykftl__cfzl in range(1, qxx__oae.
            type.count)])
    bhs__mlgt, data_arr, offsets_ptr, null_bitmap_ptr = (
        construct_array_item_array(c.context, c.builder, typ, n_arrays,
        n_elems, c))
    if wiysw__bmb:
        jqrba__qgeld = bodo.utils.utils.numba_to_c_type(typ.dtype.dtype)
        mokx__ojlr = c.context.make_array(typ.dtype)(c.context, c.builder,
            data_arr).data
        nrl__jhmnq = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(32)])
        xlsmu__rcdc = cgutils.get_or_insert_function(c.builder.module,
            nrl__jhmnq, name='array_item_array_from_sequence')
        c.builder.call(xlsmu__rcdc, [val, c.builder.bitcast(mokx__ojlr, lir
            .IntType(8).as_pointer()), offsets_ptr, null_bitmap_ptr, lir.
            Constant(lir.IntType(32), jqrba__qgeld)])
    else:
        _unbox_array_item_array_generic(typ, val, c, n_arrays, data_arr,
            offsets_ptr, null_bitmap_ptr)
    tcyx__pylq = c.context.make_helper(c.builder, typ)
    tcyx__pylq.meminfo = bhs__mlgt
    xjda__ahob = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(tcyx__pylq._getvalue(), is_error=xjda__ahob)


def _get_array_item_arr_payload(context, builder, arr_typ, arr):
    tcyx__pylq = context.make_helper(builder, arr_typ, arr)
    payload_type = ArrayItemArrayPayloadType(arr_typ)
    rvd__uua = context.nrt.meminfo_data(builder, tcyx__pylq.meminfo)
    tmh__ddpk = builder.bitcast(rvd__uua, context.get_value_type(
        payload_type).as_pointer())
    hxurn__mmjuh = cgutils.create_struct_proxy(payload_type)(context,
        builder, builder.load(tmh__ddpk))
    return hxurn__mmjuh


def _box_array_item_array_generic(typ, c, n_arrays, data_arr, offsets_ptr,
    null_bitmap_ptr):
    context = c.context
    builder = c.builder
    tfxwq__wat = context.insert_const_string(builder.module, 'numpy')
    bkm__hmxip = c.pyapi.import_module_noblock(tfxwq__wat)
    wmu__karfc = c.pyapi.object_getattr_string(bkm__hmxip, 'object_')
    fzo__utea = c.pyapi.long_from_longlong(n_arrays)
    niogo__pgk = c.pyapi.call_method(bkm__hmxip, 'ndarray', (fzo__utea,
        wmu__karfc))
    bajhe__kqerq = c.pyapi.object_getattr_string(bkm__hmxip, 'nan')
    zajl__ahve = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(64), 0))
    with cgutils.for_range(builder, n_arrays) as ylgj__odqpd:
        jpe__ifgj = ylgj__odqpd.index
        pyarray_setitem(builder, context, niogo__pgk, jpe__ifgj, bajhe__kqerq)
        zguwu__aghhw = get_bitmap_bit(builder, null_bitmap_ptr, jpe__ifgj)
        aboit__dmhoh = builder.icmp_unsigned('!=', zguwu__aghhw, lir.
            Constant(lir.IntType(8), 0))
        with builder.if_then(aboit__dmhoh):
            n_items = builder.sext(builder.sub(builder.load(builder.gep(
                offsets_ptr, [builder.add(jpe__ifgj, lir.Constant(jpe__ifgj
                .type, 1))])), builder.load(builder.gep(offsets_ptr, [
                jpe__ifgj]))), lir.IntType(64))
            item_ind = builder.load(zajl__ahve)
            ecyv__xfsd, vhtt__tsgtr = c.pyapi.call_jit_code(lambda data_arr,
                item_ind, n_items: data_arr[item_ind:item_ind + n_items],
                typ.dtype(typ.dtype, types.int64, types.int64), [data_arr,
                item_ind, n_items])
            builder.store(builder.add(item_ind, n_items), zajl__ahve)
            arr_obj = c.pyapi.from_native_value(typ.dtype, vhtt__tsgtr, c.
                env_manager)
            pyarray_setitem(builder, context, niogo__pgk, jpe__ifgj, arr_obj)
            c.pyapi.decref(arr_obj)
    c.pyapi.decref(bkm__hmxip)
    c.pyapi.decref(wmu__karfc)
    c.pyapi.decref(fzo__utea)
    c.pyapi.decref(bajhe__kqerq)
    return niogo__pgk


@box(ArrayItemArrayType)
def box_array_item_arr(typ, val, c):
    hxurn__mmjuh = _get_array_item_arr_payload(c.context, c.builder, typ, val)
    data_arr = hxurn__mmjuh.data
    offsets_ptr = c.context.make_helper(c.builder, types.Array(offset_type,
        1, 'C'), hxurn__mmjuh.offsets).data
    null_bitmap_ptr = c.context.make_helper(c.builder, types.Array(types.
        uint8, 1, 'C'), hxurn__mmjuh.null_bitmap).data
    if isinstance(typ.dtype, types.Array) and typ.dtype.dtype in (types.
        int64, types.float64, types.bool_, datetime_date_type):
        jqrba__qgeld = bodo.utils.utils.numba_to_c_type(typ.dtype.dtype)
        mokx__ojlr = c.context.make_helper(c.builder, typ.dtype, data_arr).data
        nrl__jhmnq = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(32)])
        oowe__ewpf = cgutils.get_or_insert_function(c.builder.module,
            nrl__jhmnq, name='np_array_from_array_item_array')
        arr = c.builder.call(oowe__ewpf, [hxurn__mmjuh.n_arrays, c.builder.
            bitcast(mokx__ojlr, lir.IntType(8).as_pointer()), offsets_ptr,
            null_bitmap_ptr, lir.Constant(lir.IntType(32), jqrba__qgeld)])
    else:
        arr = _box_array_item_array_generic(typ, c, hxurn__mmjuh.n_arrays,
            data_arr, offsets_ptr, null_bitmap_ptr)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def lower_pre_alloc_array_item_array(context, builder, sig, args):
    array_item_type = sig.return_type
    kbqk__psryp, lohl__milrs, dlz__ulzzr = args
    ytl__jmvc = bodo.utils.transform.get_type_alloc_counts(array_item_type.
        dtype)
    kukha__xomb = sig.args[1]
    if not isinstance(kukha__xomb, types.UniTuple):
        lohl__milrs = cgutils.pack_array(builder, [lir.Constant(lir.IntType
            (64), -1) for dlz__ulzzr in range(ytl__jmvc)])
    elif kukha__xomb.count < ytl__jmvc:
        lohl__milrs = cgutils.pack_array(builder, [builder.extract_value(
            lohl__milrs, ykftl__cfzl) for ykftl__cfzl in range(kukha__xomb.
            count)] + [lir.Constant(lir.IntType(64), -1) for dlz__ulzzr in
            range(ytl__jmvc - kukha__xomb.count)])
    bhs__mlgt, dlz__ulzzr, dlz__ulzzr, dlz__ulzzr = construct_array_item_array(
        context, builder, array_item_type, kbqk__psryp, lohl__milrs)
    tcyx__pylq = context.make_helper(builder, array_item_type)
    tcyx__pylq.meminfo = bhs__mlgt
    return tcyx__pylq._getvalue()


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
    n_arrays, fjmj__bbfqp, ryn__vfst, shiv__byzh = args
    array_item_type = signature.return_type
    payload_type = ArrayItemArrayPayloadType(array_item_type)
    abm__ovhmo = context.get_value_type(payload_type)
    gqomi__ftl = context.get_abi_sizeof(abm__ovhmo)
    twi__kag = define_array_item_dtor(context, builder, array_item_type,
        payload_type)
    bhs__mlgt = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, gqomi__ftl), twi__kag)
    rvd__uua = context.nrt.meminfo_data(builder, bhs__mlgt)
    tmh__ddpk = builder.bitcast(rvd__uua, abm__ovhmo.as_pointer())
    hxurn__mmjuh = cgutils.create_struct_proxy(payload_type)(context, builder)
    hxurn__mmjuh.n_arrays = n_arrays
    hxurn__mmjuh.data = fjmj__bbfqp
    hxurn__mmjuh.offsets = ryn__vfst
    hxurn__mmjuh.null_bitmap = shiv__byzh
    builder.store(hxurn__mmjuh._getvalue(), tmh__ddpk)
    context.nrt.incref(builder, signature.args[1], fjmj__bbfqp)
    context.nrt.incref(builder, signature.args[2], ryn__vfst)
    context.nrt.incref(builder, signature.args[3], shiv__byzh)
    tcyx__pylq = context.make_helper(builder, array_item_type)
    tcyx__pylq.meminfo = bhs__mlgt
    return tcyx__pylq._getvalue()


@intrinsic
def init_array_item_array(typingctx, n_arrays_typ, data_type, offsets_typ,
    null_bitmap_typ=None):
    assert null_bitmap_typ == types.Array(types.uint8, 1, 'C')
    uke__ckg = ArrayItemArrayType(data_type)
    sig = uke__ckg(types.int64, data_type, offsets_typ, null_bitmap_typ)
    return sig, init_array_item_array_codegen


@intrinsic
def get_offsets(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        hxurn__mmjuh = _get_array_item_arr_payload(context, builder,
            arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            hxurn__mmjuh.offsets)
    return types.Array(offset_type, 1, 'C')(arr_typ), codegen


@intrinsic
def get_offsets_ind(typingctx, arr_typ, ind_t=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, ind = args
        hxurn__mmjuh = _get_array_item_arr_payload(context, builder,
            arr_typ, arr)
        mokx__ojlr = context.make_array(types.Array(offset_type, 1, 'C'))(
            context, builder, hxurn__mmjuh.offsets).data
        ryn__vfst = builder.bitcast(mokx__ojlr, lir.IntType(offset_type.
            bitwidth).as_pointer())
        return builder.load(builder.gep(ryn__vfst, [ind]))
    return offset_type(arr_typ, types.int64), codegen


@intrinsic
def get_data(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        hxurn__mmjuh = _get_array_item_arr_payload(context, builder,
            arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            hxurn__mmjuh.data)
    return arr_typ.dtype(arr_typ), codegen


@intrinsic
def get_null_bitmap(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        hxurn__mmjuh = _get_array_item_arr_payload(context, builder,
            arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            hxurn__mmjuh.null_bitmap)
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
        hxurn__mmjuh = _get_array_item_arr_payload(context, builder,
            arr_typ, arr)
        return hxurn__mmjuh.n_arrays
    return types.int64(arr_typ), codegen


@intrinsic
def replace_data_arr(typingctx, arr_typ, data_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType
        ) and data_typ == arr_typ.dtype

    def codegen(context, builder, sig, args):
        arr, wmqv__bukk = args
        tcyx__pylq = context.make_helper(builder, arr_typ, arr)
        payload_type = ArrayItemArrayPayloadType(arr_typ)
        rvd__uua = context.nrt.meminfo_data(builder, tcyx__pylq.meminfo)
        tmh__ddpk = builder.bitcast(rvd__uua, context.get_value_type(
            payload_type).as_pointer())
        hxurn__mmjuh = cgutils.create_struct_proxy(payload_type)(context,
            builder, builder.load(tmh__ddpk))
        context.nrt.decref(builder, data_typ, hxurn__mmjuh.data)
        hxurn__mmjuh.data = wmqv__bukk
        context.nrt.incref(builder, data_typ, wmqv__bukk)
        builder.store(hxurn__mmjuh._getvalue(), tmh__ddpk)
    return types.none(arr_typ, data_typ), codegen


@numba.njit(no_cpython_wrapper=True)
def ensure_data_capacity(arr, old_size, new_size):
    fjmj__bbfqp = get_data(arr)
    fpqlo__bxm = len(fjmj__bbfqp)
    if fpqlo__bxm < new_size:
        hovs__gtdcy = max(2 * fpqlo__bxm, new_size)
        wmqv__bukk = bodo.libs.array_kernels.resize_and_copy(fjmj__bbfqp,
            old_size, hovs__gtdcy)
        replace_data_arr(arr, wmqv__bukk)


@numba.njit(no_cpython_wrapper=True)
def trim_excess_data(arr):
    fjmj__bbfqp = get_data(arr)
    ryn__vfst = get_offsets(arr)
    phqam__fbx = len(fjmj__bbfqp)
    gsxi__gmsu = ryn__vfst[-1]
    if phqam__fbx != gsxi__gmsu:
        wmqv__bukk = bodo.libs.array_kernels.resize_and_copy(fjmj__bbfqp,
            gsxi__gmsu, gsxi__gmsu)
        replace_data_arr(arr, wmqv__bukk)


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
            ryn__vfst = get_offsets(arr)
            fjmj__bbfqp = get_data(arr)
            yhxl__jnag = ryn__vfst[ind]
            sja__zxna = ryn__vfst[ind + 1]
            return fjmj__bbfqp[yhxl__jnag:sja__zxna]
        return array_item_arr_getitem_impl
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        nbfk__moct = arr.dtype

        def impl_bool(arr, ind):
            lcqnv__fuhch = len(arr)
            if lcqnv__fuhch != len(ind):
                raise IndexError(
                    'boolean index did not match indexed array along dimension 0'
                    )
            shiv__byzh = get_null_bitmap(arr)
            n_arrays = 0
            fbjw__myafh = init_nested_counts(nbfk__moct)
            for ykftl__cfzl in range(lcqnv__fuhch):
                if ind[ykftl__cfzl]:
                    n_arrays += 1
                    rhr__mme = arr[ykftl__cfzl]
                    fbjw__myafh = add_nested_counts(fbjw__myafh, rhr__mme)
            niogo__pgk = pre_alloc_array_item_array(n_arrays, fbjw__myafh,
                nbfk__moct)
            hru__tvz = get_null_bitmap(niogo__pgk)
            zges__ectnf = 0
            for sal__jgo in range(lcqnv__fuhch):
                if ind[sal__jgo]:
                    niogo__pgk[zges__ectnf] = arr[sal__jgo]
                    xqhdk__atqi = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        shiv__byzh, sal__jgo)
                    bodo.libs.int_arr_ext.set_bit_to_arr(hru__tvz,
                        zges__ectnf, xqhdk__atqi)
                    zges__ectnf += 1
            return niogo__pgk
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        nbfk__moct = arr.dtype

        def impl_int(arr, ind):
            shiv__byzh = get_null_bitmap(arr)
            lcqnv__fuhch = len(ind)
            n_arrays = lcqnv__fuhch
            fbjw__myafh = init_nested_counts(nbfk__moct)
            for waqg__rbnzc in range(lcqnv__fuhch):
                ykftl__cfzl = ind[waqg__rbnzc]
                rhr__mme = arr[ykftl__cfzl]
                fbjw__myafh = add_nested_counts(fbjw__myafh, rhr__mme)
            niogo__pgk = pre_alloc_array_item_array(n_arrays, fbjw__myafh,
                nbfk__moct)
            hru__tvz = get_null_bitmap(niogo__pgk)
            for mbc__brt in range(lcqnv__fuhch):
                sal__jgo = ind[mbc__brt]
                niogo__pgk[mbc__brt] = arr[sal__jgo]
                xqhdk__atqi = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                    shiv__byzh, sal__jgo)
                bodo.libs.int_arr_ext.set_bit_to_arr(hru__tvz, mbc__brt,
                    xqhdk__atqi)
            return niogo__pgk
        return impl_int
    if isinstance(ind, types.SliceType):

        def impl_slice(arr, ind):
            lcqnv__fuhch = len(arr)
            rwiqg__rlrq = numba.cpython.unicode._normalize_slice(ind,
                lcqnv__fuhch)
            ddx__vkdri = np.arange(rwiqg__rlrq.start, rwiqg__rlrq.stop,
                rwiqg__rlrq.step)
            return arr[ddx__vkdri]
        return impl_slice


@overload(operator.setitem)
def array_item_arr_setitem(A, idx, val):
    if not isinstance(A, ArrayItemArrayType):
        return
    if isinstance(idx, types.Integer):

        def impl_scalar(A, idx, val):
            ryn__vfst = get_offsets(A)
            shiv__byzh = get_null_bitmap(A)
            if idx == 0:
                ryn__vfst[0] = 0
            n_items = len(val)
            gqc__eitm = ryn__vfst[idx] + n_items
            ensure_data_capacity(A, ryn__vfst[idx], gqc__eitm)
            fjmj__bbfqp = get_data(A)
            ryn__vfst[idx + 1] = ryn__vfst[idx] + n_items
            fjmj__bbfqp[ryn__vfst[idx]:ryn__vfst[idx + 1]] = val
            bodo.libs.int_arr_ext.set_bit_to_arr(shiv__byzh, idx, 1)
        return impl_scalar
    if isinstance(idx, types.SliceType) and A.dtype == val:

        def impl_slice_elem(A, idx, val):
            rwiqg__rlrq = numba.cpython.unicode._normalize_slice(idx, len(A))
            for ykftl__cfzl in range(rwiqg__rlrq.start, rwiqg__rlrq.stop,
                rwiqg__rlrq.step):
                A[ykftl__cfzl] = val
        return impl_slice_elem
    if isinstance(idx, types.SliceType) and is_iterable_type(val):

        def impl_slice(A, idx, val):
            val = bodo.utils.conversion.coerce_to_array(val,
                use_nullable_array=True)
            ryn__vfst = get_offsets(A)
            shiv__byzh = get_null_bitmap(A)
            csun__ljp = get_offsets(val)
            hbyvv__qly = get_data(val)
            pjjrp__smpbi = get_null_bitmap(val)
            lcqnv__fuhch = len(A)
            rwiqg__rlrq = numba.cpython.unicode._normalize_slice(idx,
                lcqnv__fuhch)
            hukj__vmak, galry__unqqe = rwiqg__rlrq.start, rwiqg__rlrq.stop
            assert rwiqg__rlrq.step == 1
            if hukj__vmak == 0:
                ryn__vfst[hukj__vmak] = 0
            bfyoo__qomo = ryn__vfst[hukj__vmak]
            gqc__eitm = bfyoo__qomo + len(hbyvv__qly)
            ensure_data_capacity(A, bfyoo__qomo, gqc__eitm)
            fjmj__bbfqp = get_data(A)
            fjmj__bbfqp[bfyoo__qomo:bfyoo__qomo + len(hbyvv__qly)] = hbyvv__qly
            ryn__vfst[hukj__vmak:galry__unqqe + 1] = csun__ljp + bfyoo__qomo
            olqq__brrwt = 0
            for ykftl__cfzl in range(hukj__vmak, galry__unqqe):
                xqhdk__atqi = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                    pjjrp__smpbi, olqq__brrwt)
                bodo.libs.int_arr_ext.set_bit_to_arr(shiv__byzh,
                    ykftl__cfzl, xqhdk__atqi)
                olqq__brrwt += 1
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
