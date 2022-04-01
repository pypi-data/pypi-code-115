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
        ksd__whvn = [('n_arrays', types.int64), ('data', fe_type.array_type
            .dtype), ('offsets', types.Array(offset_type, 1, 'C')), (
            'null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, ksd__whvn)


@register_model(ArrayItemArrayType)
class ArrayItemArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = ArrayItemArrayPayloadType(fe_type)
        ksd__whvn = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, ksd__whvn)


def define_array_item_dtor(context, builder, array_item_type, payload_type):
    sixim__uufpd = builder.module
    umyb__kpsxu = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    vbtcu__jklsw = cgutils.get_or_insert_function(sixim__uufpd, umyb__kpsxu,
        name='.dtor.array_item.{}'.format(array_item_type.dtype))
    if not vbtcu__jklsw.is_declaration:
        return vbtcu__jklsw
    vbtcu__jklsw.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(vbtcu__jklsw.append_basic_block())
    xdcg__zvgw = vbtcu__jklsw.args[0]
    zvnns__aeec = context.get_value_type(payload_type).as_pointer()
    osky__air = builder.bitcast(xdcg__zvgw, zvnns__aeec)
    qrp__bpyb = context.make_helper(builder, payload_type, ref=osky__air)
    context.nrt.decref(builder, array_item_type.dtype, qrp__bpyb.data)
    context.nrt.decref(builder, types.Array(offset_type, 1, 'C'), qrp__bpyb
        .offsets)
    context.nrt.decref(builder, types.Array(types.uint8, 1, 'C'), qrp__bpyb
        .null_bitmap)
    builder.ret_void()
    return vbtcu__jklsw


def construct_array_item_array(context, builder, array_item_type, n_arrays,
    n_elems, c=None):
    payload_type = ArrayItemArrayPayloadType(array_item_type)
    mcdac__xwp = context.get_value_type(payload_type)
    uoj__tbjqp = context.get_abi_sizeof(mcdac__xwp)
    mltru__izh = define_array_item_dtor(context, builder, array_item_type,
        payload_type)
    lnnq__toxy = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, uoj__tbjqp), mltru__izh)
    podc__wea = context.nrt.meminfo_data(builder, lnnq__toxy)
    fkdk__cgvyq = builder.bitcast(podc__wea, mcdac__xwp.as_pointer())
    qrp__bpyb = cgutils.create_struct_proxy(payload_type)(context, builder)
    qrp__bpyb.n_arrays = n_arrays
    ajocm__fexo = n_elems.type.count
    qett__roub = builder.extract_value(n_elems, 0)
    atux__hqn = cgutils.alloca_once_value(builder, qett__roub)
    fvxfx__rywi = builder.icmp_signed('==', qett__roub, lir.Constant(
        qett__roub.type, -1))
    with builder.if_then(fvxfx__rywi):
        builder.store(n_arrays, atux__hqn)
    n_elems = cgutils.pack_array(builder, [builder.load(atux__hqn)] + [
        builder.extract_value(n_elems, ausx__myrf) for ausx__myrf in range(
        1, ajocm__fexo)])
    qrp__bpyb.data = gen_allocate_array(context, builder, array_item_type.
        dtype, n_elems, c)
    zgy__udfp = builder.add(n_arrays, lir.Constant(lir.IntType(64), 1))
    fcdk__clwlz = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(offset_type, 1, 'C'), [zgy__udfp])
    offsets_ptr = fcdk__clwlz.data
    builder.store(context.get_constant(offset_type, 0), offsets_ptr)
    builder.store(builder.trunc(builder.extract_value(n_elems, 0), lir.
        IntType(offset_type.bitwidth)), builder.gep(offsets_ptr, [n_arrays]))
    qrp__bpyb.offsets = fcdk__clwlz._getvalue()
    kiz__yqpuf = builder.udiv(builder.add(n_arrays, lir.Constant(lir.
        IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
    dqb__wvpc = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(types.uint8, 1, 'C'), [kiz__yqpuf])
    null_bitmap_ptr = dqb__wvpc.data
    qrp__bpyb.null_bitmap = dqb__wvpc._getvalue()
    builder.store(qrp__bpyb._getvalue(), fkdk__cgvyq)
    return lnnq__toxy, qrp__bpyb.data, offsets_ptr, null_bitmap_ptr


def _unbox_array_item_array_copy_data(arr_typ, arr_obj, c, data_arr,
    item_ind, n_items):
    context = c.context
    builder = c.builder
    arr_obj = to_arr_obj_if_list_obj(c, context, builder, arr_obj, arr_typ)
    arr_val = c.pyapi.to_native_value(arr_typ, arr_obj).value
    sig = types.none(arr_typ, types.int64, types.int64, arr_typ)

    def copy_data(data_arr, item_ind, n_items, arr_val):
        data_arr[item_ind:item_ind + n_items] = arr_val
    ihbo__epbmf, lks__fkym = c.pyapi.call_jit_code(copy_data, sig, [
        data_arr, item_ind, n_items, arr_val])
    c.context.nrt.decref(builder, arr_typ, arr_val)


def _unbox_array_item_array_generic(typ, val, c, n_arrays, data_arr,
    offsets_ptr, null_bitmap_ptr):
    context = c.context
    builder = c.builder
    ntrrv__xznaf = context.insert_const_string(builder.module, 'pandas')
    eudm__wmot = c.pyapi.import_module_noblock(ntrrv__xznaf)
    mqa__rbvaw = c.pyapi.object_getattr_string(eudm__wmot, 'NA')
    tutvg__mpnyx = c.context.get_constant(offset_type, 0)
    builder.store(tutvg__mpnyx, offsets_ptr)
    ikmh__plo = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with cgutils.for_range(builder, n_arrays) as ilj__jpnk:
        eua__psajm = ilj__jpnk.index
        item_ind = builder.load(ikmh__plo)
        builder.store(builder.trunc(item_ind, lir.IntType(offset_type.
            bitwidth)), builder.gep(offsets_ptr, [eua__psajm]))
        arr_obj = seq_getitem(builder, context, val, eua__psajm)
        set_bitmap_bit(builder, null_bitmap_ptr, eua__psajm, 0)
        wgnvq__btp = is_na_value(builder, context, arr_obj, mqa__rbvaw)
        ngm__afgq = builder.icmp_unsigned('!=', wgnvq__btp, lir.Constant(
            wgnvq__btp.type, 1))
        with builder.if_then(ngm__afgq):
            set_bitmap_bit(builder, null_bitmap_ptr, eua__psajm, 1)
            n_items = bodo.utils.utils.object_length(c, arr_obj)
            _unbox_array_item_array_copy_data(typ.dtype, arr_obj, c,
                data_arr, item_ind, n_items)
            builder.store(builder.add(item_ind, n_items), ikmh__plo)
        c.pyapi.decref(arr_obj)
    builder.store(builder.trunc(builder.load(ikmh__plo), lir.IntType(
        offset_type.bitwidth)), builder.gep(offsets_ptr, [n_arrays]))
    c.pyapi.decref(eudm__wmot)
    c.pyapi.decref(mqa__rbvaw)


@unbox(ArrayItemArrayType)
def unbox_array_item_array(typ, val, c):
    obvz__cbdh = isinstance(typ.dtype, types.Array) and typ.dtype.dtype in (
        types.int64, types.float64, types.bool_, datetime_date_type)
    n_arrays = bodo.utils.utils.object_length(c, val)
    if obvz__cbdh:
        umyb__kpsxu = lir.FunctionType(lir.IntType(64), [lir.IntType(8).
            as_pointer()])
        wxe__qcb = cgutils.get_or_insert_function(c.builder.module,
            umyb__kpsxu, name='count_total_elems_list_array')
        n_elems = cgutils.pack_array(c.builder, [c.builder.call(wxe__qcb, [
            val])])
    else:
        hdkwh__frhx = get_array_elem_counts(c, c.builder, c.context, val, typ)
        n_elems = cgutils.pack_array(c.builder, [c.builder.extract_value(
            hdkwh__frhx, ausx__myrf) for ausx__myrf in range(1, hdkwh__frhx
            .type.count)])
    lnnq__toxy, data_arr, offsets_ptr, null_bitmap_ptr = (
        construct_array_item_array(c.context, c.builder, typ, n_arrays,
        n_elems, c))
    if obvz__cbdh:
        yaaz__xgz = bodo.utils.utils.numba_to_c_type(typ.dtype.dtype)
        avtk__gwacx = c.context.make_array(typ.dtype)(c.context, c.builder,
            data_arr).data
        umyb__kpsxu = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(32)])
        vbtcu__jklsw = cgutils.get_or_insert_function(c.builder.module,
            umyb__kpsxu, name='array_item_array_from_sequence')
        c.builder.call(vbtcu__jklsw, [val, c.builder.bitcast(avtk__gwacx,
            lir.IntType(8).as_pointer()), offsets_ptr, null_bitmap_ptr, lir
            .Constant(lir.IntType(32), yaaz__xgz)])
    else:
        _unbox_array_item_array_generic(typ, val, c, n_arrays, data_arr,
            offsets_ptr, null_bitmap_ptr)
    keky__fhx = c.context.make_helper(c.builder, typ)
    keky__fhx.meminfo = lnnq__toxy
    xkglx__etrwb = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(keky__fhx._getvalue(), is_error=xkglx__etrwb)


def _get_array_item_arr_payload(context, builder, arr_typ, arr):
    keky__fhx = context.make_helper(builder, arr_typ, arr)
    payload_type = ArrayItemArrayPayloadType(arr_typ)
    podc__wea = context.nrt.meminfo_data(builder, keky__fhx.meminfo)
    fkdk__cgvyq = builder.bitcast(podc__wea, context.get_value_type(
        payload_type).as_pointer())
    qrp__bpyb = cgutils.create_struct_proxy(payload_type)(context, builder,
        builder.load(fkdk__cgvyq))
    return qrp__bpyb


def _box_array_item_array_generic(typ, c, n_arrays, data_arr, offsets_ptr,
    null_bitmap_ptr):
    context = c.context
    builder = c.builder
    ntrrv__xznaf = context.insert_const_string(builder.module, 'numpy')
    rreh__cvcje = c.pyapi.import_module_noblock(ntrrv__xznaf)
    dyync__vasa = c.pyapi.object_getattr_string(rreh__cvcje, 'object_')
    cpmjp__iythp = c.pyapi.long_from_longlong(n_arrays)
    fdhqv__eukas = c.pyapi.call_method(rreh__cvcje, 'ndarray', (
        cpmjp__iythp, dyync__vasa))
    pzngu__nabm = c.pyapi.object_getattr_string(rreh__cvcje, 'nan')
    ikmh__plo = cgutils.alloca_once_value(builder, lir.Constant(lir.IntType
        (64), 0))
    with cgutils.for_range(builder, n_arrays) as ilj__jpnk:
        eua__psajm = ilj__jpnk.index
        pyarray_setitem(builder, context, fdhqv__eukas, eua__psajm, pzngu__nabm
            )
        goc__rlni = get_bitmap_bit(builder, null_bitmap_ptr, eua__psajm)
        igxgm__jqhxy = builder.icmp_unsigned('!=', goc__rlni, lir.Constant(
            lir.IntType(8), 0))
        with builder.if_then(igxgm__jqhxy):
            n_items = builder.sext(builder.sub(builder.load(builder.gep(
                offsets_ptr, [builder.add(eua__psajm, lir.Constant(
                eua__psajm.type, 1))])), builder.load(builder.gep(
                offsets_ptr, [eua__psajm]))), lir.IntType(64))
            item_ind = builder.load(ikmh__plo)
            ihbo__epbmf, mpxws__axrz = c.pyapi.call_jit_code(lambda
                data_arr, item_ind, n_items: data_arr[item_ind:item_ind +
                n_items], typ.dtype(typ.dtype, types.int64, types.int64), [
                data_arr, item_ind, n_items])
            builder.store(builder.add(item_ind, n_items), ikmh__plo)
            arr_obj = c.pyapi.from_native_value(typ.dtype, mpxws__axrz, c.
                env_manager)
            pyarray_setitem(builder, context, fdhqv__eukas, eua__psajm, arr_obj
                )
            c.pyapi.decref(arr_obj)
    c.pyapi.decref(rreh__cvcje)
    c.pyapi.decref(dyync__vasa)
    c.pyapi.decref(cpmjp__iythp)
    c.pyapi.decref(pzngu__nabm)
    return fdhqv__eukas


@box(ArrayItemArrayType)
def box_array_item_arr(typ, val, c):
    qrp__bpyb = _get_array_item_arr_payload(c.context, c.builder, typ, val)
    data_arr = qrp__bpyb.data
    offsets_ptr = c.context.make_helper(c.builder, types.Array(offset_type,
        1, 'C'), qrp__bpyb.offsets).data
    null_bitmap_ptr = c.context.make_helper(c.builder, types.Array(types.
        uint8, 1, 'C'), qrp__bpyb.null_bitmap).data
    if isinstance(typ.dtype, types.Array) and typ.dtype.dtype in (types.
        int64, types.float64, types.bool_, datetime_date_type):
        yaaz__xgz = bodo.utils.utils.numba_to_c_type(typ.dtype.dtype)
        avtk__gwacx = c.context.make_helper(c.builder, typ.dtype, data_arr
            ).data
        umyb__kpsxu = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(32)])
        ggp__ggeo = cgutils.get_or_insert_function(c.builder.module,
            umyb__kpsxu, name='np_array_from_array_item_array')
        arr = c.builder.call(ggp__ggeo, [qrp__bpyb.n_arrays, c.builder.
            bitcast(avtk__gwacx, lir.IntType(8).as_pointer()), offsets_ptr,
            null_bitmap_ptr, lir.Constant(lir.IntType(32), yaaz__xgz)])
    else:
        arr = _box_array_item_array_generic(typ, c, qrp__bpyb.n_arrays,
            data_arr, offsets_ptr, null_bitmap_ptr)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def lower_pre_alloc_array_item_array(context, builder, sig, args):
    array_item_type = sig.return_type
    cgb__mtj, orhc__rzk, nugzb__bgfqz = args
    utz__ouugg = bodo.utils.transform.get_type_alloc_counts(array_item_type
        .dtype)
    qju__avvjm = sig.args[1]
    if not isinstance(qju__avvjm, types.UniTuple):
        orhc__rzk = cgutils.pack_array(builder, [lir.Constant(lir.IntType(
            64), -1) for nugzb__bgfqz in range(utz__ouugg)])
    elif qju__avvjm.count < utz__ouugg:
        orhc__rzk = cgutils.pack_array(builder, [builder.extract_value(
            orhc__rzk, ausx__myrf) for ausx__myrf in range(qju__avvjm.count
            )] + [lir.Constant(lir.IntType(64), -1) for nugzb__bgfqz in
            range(utz__ouugg - qju__avvjm.count)])
    lnnq__toxy, nugzb__bgfqz, nugzb__bgfqz, nugzb__bgfqz = (
        construct_array_item_array(context, builder, array_item_type,
        cgb__mtj, orhc__rzk))
    keky__fhx = context.make_helper(builder, array_item_type)
    keky__fhx.meminfo = lnnq__toxy
    return keky__fhx._getvalue()


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
    n_arrays, sgnkq__ckcea, fcdk__clwlz, dqb__wvpc = args
    array_item_type = signature.return_type
    payload_type = ArrayItemArrayPayloadType(array_item_type)
    mcdac__xwp = context.get_value_type(payload_type)
    uoj__tbjqp = context.get_abi_sizeof(mcdac__xwp)
    mltru__izh = define_array_item_dtor(context, builder, array_item_type,
        payload_type)
    lnnq__toxy = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, uoj__tbjqp), mltru__izh)
    podc__wea = context.nrt.meminfo_data(builder, lnnq__toxy)
    fkdk__cgvyq = builder.bitcast(podc__wea, mcdac__xwp.as_pointer())
    qrp__bpyb = cgutils.create_struct_proxy(payload_type)(context, builder)
    qrp__bpyb.n_arrays = n_arrays
    qrp__bpyb.data = sgnkq__ckcea
    qrp__bpyb.offsets = fcdk__clwlz
    qrp__bpyb.null_bitmap = dqb__wvpc
    builder.store(qrp__bpyb._getvalue(), fkdk__cgvyq)
    context.nrt.incref(builder, signature.args[1], sgnkq__ckcea)
    context.nrt.incref(builder, signature.args[2], fcdk__clwlz)
    context.nrt.incref(builder, signature.args[3], dqb__wvpc)
    keky__fhx = context.make_helper(builder, array_item_type)
    keky__fhx.meminfo = lnnq__toxy
    return keky__fhx._getvalue()


@intrinsic
def init_array_item_array(typingctx, n_arrays_typ, data_type, offsets_typ,
    null_bitmap_typ=None):
    assert null_bitmap_typ == types.Array(types.uint8, 1, 'C')
    ziub__cfwdj = ArrayItemArrayType(data_type)
    sig = ziub__cfwdj(types.int64, data_type, offsets_typ, null_bitmap_typ)
    return sig, init_array_item_array_codegen


@intrinsic
def get_offsets(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        qrp__bpyb = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            qrp__bpyb.offsets)
    return types.Array(offset_type, 1, 'C')(arr_typ), codegen


@intrinsic
def get_offsets_ind(typingctx, arr_typ, ind_t=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, ind = args
        qrp__bpyb = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        avtk__gwacx = context.make_array(types.Array(offset_type, 1, 'C'))(
            context, builder, qrp__bpyb.offsets).data
        fcdk__clwlz = builder.bitcast(avtk__gwacx, lir.IntType(offset_type.
            bitwidth).as_pointer())
        return builder.load(builder.gep(fcdk__clwlz, [ind]))
    return offset_type(arr_typ, types.int64), codegen


@intrinsic
def get_data(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        qrp__bpyb = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            qrp__bpyb.data)
    return arr_typ.dtype(arr_typ), codegen


@intrinsic
def get_null_bitmap(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        qrp__bpyb = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            qrp__bpyb.null_bitmap)
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
        qrp__bpyb = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        return qrp__bpyb.n_arrays
    return types.int64(arr_typ), codegen


@intrinsic
def replace_data_arr(typingctx, arr_typ, data_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType
        ) and data_typ == arr_typ.dtype

    def codegen(context, builder, sig, args):
        arr, ebw__gix = args
        keky__fhx = context.make_helper(builder, arr_typ, arr)
        payload_type = ArrayItemArrayPayloadType(arr_typ)
        podc__wea = context.nrt.meminfo_data(builder, keky__fhx.meminfo)
        fkdk__cgvyq = builder.bitcast(podc__wea, context.get_value_type(
            payload_type).as_pointer())
        qrp__bpyb = cgutils.create_struct_proxy(payload_type)(context,
            builder, builder.load(fkdk__cgvyq))
        context.nrt.decref(builder, data_typ, qrp__bpyb.data)
        qrp__bpyb.data = ebw__gix
        context.nrt.incref(builder, data_typ, ebw__gix)
        builder.store(qrp__bpyb._getvalue(), fkdk__cgvyq)
    return types.none(arr_typ, data_typ), codegen


@numba.njit(no_cpython_wrapper=True)
def ensure_data_capacity(arr, old_size, new_size):
    sgnkq__ckcea = get_data(arr)
    hhlw__kiay = len(sgnkq__ckcea)
    if hhlw__kiay < new_size:
        sozd__vimx = max(2 * hhlw__kiay, new_size)
        ebw__gix = bodo.libs.array_kernels.resize_and_copy(sgnkq__ckcea,
            old_size, sozd__vimx)
        replace_data_arr(arr, ebw__gix)


@numba.njit(no_cpython_wrapper=True)
def trim_excess_data(arr):
    sgnkq__ckcea = get_data(arr)
    fcdk__clwlz = get_offsets(arr)
    fyje__lkc = len(sgnkq__ckcea)
    uuiql__wwptl = fcdk__clwlz[-1]
    if fyje__lkc != uuiql__wwptl:
        ebw__gix = bodo.libs.array_kernels.resize_and_copy(sgnkq__ckcea,
            uuiql__wwptl, uuiql__wwptl)
        replace_data_arr(arr, ebw__gix)


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
            fcdk__clwlz = get_offsets(arr)
            sgnkq__ckcea = get_data(arr)
            sgkcr__zvohc = fcdk__clwlz[ind]
            tjkoa__jwdw = fcdk__clwlz[ind + 1]
            return sgnkq__ckcea[sgkcr__zvohc:tjkoa__jwdw]
        return array_item_arr_getitem_impl
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        xgt__nfye = arr.dtype

        def impl_bool(arr, ind):
            atb__sbou = len(arr)
            if atb__sbou != len(ind):
                raise IndexError(
                    'boolean index did not match indexed array along dimension 0'
                    )
            dqb__wvpc = get_null_bitmap(arr)
            n_arrays = 0
            olcnr__empe = init_nested_counts(xgt__nfye)
            for ausx__myrf in range(atb__sbou):
                if ind[ausx__myrf]:
                    n_arrays += 1
                    enzoj__kfgfu = arr[ausx__myrf]
                    olcnr__empe = add_nested_counts(olcnr__empe, enzoj__kfgfu)
            fdhqv__eukas = pre_alloc_array_item_array(n_arrays, olcnr__empe,
                xgt__nfye)
            fxhne__vgaf = get_null_bitmap(fdhqv__eukas)
            kga__vnppm = 0
            for zppfo__kveta in range(atb__sbou):
                if ind[zppfo__kveta]:
                    fdhqv__eukas[kga__vnppm] = arr[zppfo__kveta]
                    dgffd__looo = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        dqb__wvpc, zppfo__kveta)
                    bodo.libs.int_arr_ext.set_bit_to_arr(fxhne__vgaf,
                        kga__vnppm, dgffd__looo)
                    kga__vnppm += 1
            return fdhqv__eukas
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        xgt__nfye = arr.dtype

        def impl_int(arr, ind):
            dqb__wvpc = get_null_bitmap(arr)
            atb__sbou = len(ind)
            n_arrays = atb__sbou
            olcnr__empe = init_nested_counts(xgt__nfye)
            for dgpmq__wqzzu in range(atb__sbou):
                ausx__myrf = ind[dgpmq__wqzzu]
                enzoj__kfgfu = arr[ausx__myrf]
                olcnr__empe = add_nested_counts(olcnr__empe, enzoj__kfgfu)
            fdhqv__eukas = pre_alloc_array_item_array(n_arrays, olcnr__empe,
                xgt__nfye)
            fxhne__vgaf = get_null_bitmap(fdhqv__eukas)
            for ysv__bbu in range(atb__sbou):
                zppfo__kveta = ind[ysv__bbu]
                fdhqv__eukas[ysv__bbu] = arr[zppfo__kveta]
                dgffd__looo = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                    dqb__wvpc, zppfo__kveta)
                bodo.libs.int_arr_ext.set_bit_to_arr(fxhne__vgaf, ysv__bbu,
                    dgffd__looo)
            return fdhqv__eukas
        return impl_int
    if isinstance(ind, types.SliceType):

        def impl_slice(arr, ind):
            atb__sbou = len(arr)
            yaer__rmwl = numba.cpython.unicode._normalize_slice(ind, atb__sbou)
            iob__hxcz = np.arange(yaer__rmwl.start, yaer__rmwl.stop,
                yaer__rmwl.step)
            return arr[iob__hxcz]
        return impl_slice


@overload(operator.setitem)
def array_item_arr_setitem(A, idx, val):
    if not isinstance(A, ArrayItemArrayType):
        return
    if isinstance(idx, types.Integer):

        def impl_scalar(A, idx, val):
            fcdk__clwlz = get_offsets(A)
            dqb__wvpc = get_null_bitmap(A)
            if idx == 0:
                fcdk__clwlz[0] = 0
            n_items = len(val)
            wyyjf__bwvz = fcdk__clwlz[idx] + n_items
            ensure_data_capacity(A, fcdk__clwlz[idx], wyyjf__bwvz)
            sgnkq__ckcea = get_data(A)
            fcdk__clwlz[idx + 1] = fcdk__clwlz[idx] + n_items
            sgnkq__ckcea[fcdk__clwlz[idx]:fcdk__clwlz[idx + 1]] = val
            bodo.libs.int_arr_ext.set_bit_to_arr(dqb__wvpc, idx, 1)
        return impl_scalar
    if isinstance(idx, types.SliceType) and A.dtype == val:

        def impl_slice_elem(A, idx, val):
            yaer__rmwl = numba.cpython.unicode._normalize_slice(idx, len(A))
            for ausx__myrf in range(yaer__rmwl.start, yaer__rmwl.stop,
                yaer__rmwl.step):
                A[ausx__myrf] = val
        return impl_slice_elem
    if isinstance(idx, types.SliceType) and is_iterable_type(val):

        def impl_slice(A, idx, val):
            val = bodo.utils.conversion.coerce_to_array(val,
                use_nullable_array=True)
            fcdk__clwlz = get_offsets(A)
            dqb__wvpc = get_null_bitmap(A)
            kerji__pbw = get_offsets(val)
            momrs__fhjlq = get_data(val)
            bqvex__uolcn = get_null_bitmap(val)
            atb__sbou = len(A)
            yaer__rmwl = numba.cpython.unicode._normalize_slice(idx, atb__sbou)
            jey__orp, hcewt__xivw = yaer__rmwl.start, yaer__rmwl.stop
            assert yaer__rmwl.step == 1
            if jey__orp == 0:
                fcdk__clwlz[jey__orp] = 0
            rgi__bxx = fcdk__clwlz[jey__orp]
            wyyjf__bwvz = rgi__bxx + len(momrs__fhjlq)
            ensure_data_capacity(A, rgi__bxx, wyyjf__bwvz)
            sgnkq__ckcea = get_data(A)
            sgnkq__ckcea[rgi__bxx:rgi__bxx + len(momrs__fhjlq)] = momrs__fhjlq
            fcdk__clwlz[jey__orp:hcewt__xivw + 1] = kerji__pbw + rgi__bxx
            mdr__rxm = 0
            for ausx__myrf in range(jey__orp, hcewt__xivw):
                dgffd__looo = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                    bqvex__uolcn, mdr__rxm)
                bodo.libs.int_arr_ext.set_bit_to_arr(dqb__wvpc, ausx__myrf,
                    dgffd__looo)
                mdr__rxm += 1
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
