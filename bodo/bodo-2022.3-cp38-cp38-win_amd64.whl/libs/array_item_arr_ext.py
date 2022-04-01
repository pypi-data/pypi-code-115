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
        dxbr__yirdf = [('n_arrays', types.int64), ('data', fe_type.
            array_type.dtype), ('offsets', types.Array(offset_type, 1, 'C')
            ), ('null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, dxbr__yirdf)


@register_model(ArrayItemArrayType)
class ArrayItemArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = ArrayItemArrayPayloadType(fe_type)
        dxbr__yirdf = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, dxbr__yirdf)


def define_array_item_dtor(context, builder, array_item_type, payload_type):
    dhb__kewih = builder.module
    ssyvp__xpdr = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    acth__asgy = cgutils.get_or_insert_function(dhb__kewih, ssyvp__xpdr,
        name='.dtor.array_item.{}'.format(array_item_type.dtype))
    if not acth__asgy.is_declaration:
        return acth__asgy
    acth__asgy.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(acth__asgy.append_basic_block())
    xdfs__ghahy = acth__asgy.args[0]
    bkf__rcbi = context.get_value_type(payload_type).as_pointer()
    lzrw__hgwh = builder.bitcast(xdfs__ghahy, bkf__rcbi)
    fnh__sgti = context.make_helper(builder, payload_type, ref=lzrw__hgwh)
    context.nrt.decref(builder, array_item_type.dtype, fnh__sgti.data)
    context.nrt.decref(builder, types.Array(offset_type, 1, 'C'), fnh__sgti
        .offsets)
    context.nrt.decref(builder, types.Array(types.uint8, 1, 'C'), fnh__sgti
        .null_bitmap)
    builder.ret_void()
    return acth__asgy


def construct_array_item_array(context, builder, array_item_type, n_arrays,
    n_elems, c=None):
    payload_type = ArrayItemArrayPayloadType(array_item_type)
    tvyv__flf = context.get_value_type(payload_type)
    oxm__hsvly = context.get_abi_sizeof(tvyv__flf)
    xow__qut = define_array_item_dtor(context, builder, array_item_type,
        payload_type)
    bth__xbbj = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, oxm__hsvly), xow__qut)
    kbu__ktfy = context.nrt.meminfo_data(builder, bth__xbbj)
    ieoq__usz = builder.bitcast(kbu__ktfy, tvyv__flf.as_pointer())
    fnh__sgti = cgutils.create_struct_proxy(payload_type)(context, builder)
    fnh__sgti.n_arrays = n_arrays
    yoyon__reapg = n_elems.type.count
    drw__pdi = builder.extract_value(n_elems, 0)
    ycji__yrpy = cgutils.alloca_once_value(builder, drw__pdi)
    rcvmr__gufvx = builder.icmp_signed('==', drw__pdi, lir.Constant(
        drw__pdi.type, -1))
    with builder.if_then(rcvmr__gufvx):
        builder.store(n_arrays, ycji__yrpy)
    n_elems = cgutils.pack_array(builder, [builder.load(ycji__yrpy)] + [
        builder.extract_value(n_elems, qfuv__nvggi) for qfuv__nvggi in
        range(1, yoyon__reapg)])
    fnh__sgti.data = gen_allocate_array(context, builder, array_item_type.
        dtype, n_elems, c)
    eztex__yevzc = builder.add(n_arrays, lir.Constant(lir.IntType(64), 1))
    alak__civyd = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(offset_type, 1, 'C'), [eztex__yevzc])
    offsets_ptr = alak__civyd.data
    builder.store(context.get_constant(offset_type, 0), offsets_ptr)
    builder.store(builder.trunc(builder.extract_value(n_elems, 0), lir.
        IntType(offset_type.bitwidth)), builder.gep(offsets_ptr, [n_arrays]))
    fnh__sgti.offsets = alak__civyd._getvalue()
    gxn__tyhv = builder.udiv(builder.add(n_arrays, lir.Constant(lir.IntType
        (64), 7)), lir.Constant(lir.IntType(64), 8))
    zmvp__jeeu = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(types.uint8, 1, 'C'), [gxn__tyhv])
    null_bitmap_ptr = zmvp__jeeu.data
    fnh__sgti.null_bitmap = zmvp__jeeu._getvalue()
    builder.store(fnh__sgti._getvalue(), ieoq__usz)
    return bth__xbbj, fnh__sgti.data, offsets_ptr, null_bitmap_ptr


def _unbox_array_item_array_copy_data(arr_typ, arr_obj, c, data_arr,
    item_ind, n_items):
    context = c.context
    builder = c.builder
    arr_obj = to_arr_obj_if_list_obj(c, context, builder, arr_obj, arr_typ)
    arr_val = c.pyapi.to_native_value(arr_typ, arr_obj).value
    sig = types.none(arr_typ, types.int64, types.int64, arr_typ)

    def copy_data(data_arr, item_ind, n_items, arr_val):
        data_arr[item_ind:item_ind + n_items] = arr_val
    fodg__wepny, auj__iykam = c.pyapi.call_jit_code(copy_data, sig, [
        data_arr, item_ind, n_items, arr_val])
    c.context.nrt.decref(builder, arr_typ, arr_val)


def _unbox_array_item_array_generic(typ, val, c, n_arrays, data_arr,
    offsets_ptr, null_bitmap_ptr):
    context = c.context
    builder = c.builder
    rfocx__nkax = context.insert_const_string(builder.module, 'pandas')
    spix__ubx = c.pyapi.import_module_noblock(rfocx__nkax)
    mpof__wvzz = c.pyapi.object_getattr_string(spix__ubx, 'NA')
    smvd__uyzcs = c.context.get_constant(offset_type, 0)
    builder.store(smvd__uyzcs, offsets_ptr)
    ogr__nfvx = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with cgutils.for_range(builder, n_arrays) as syzxs__kie:
        mipma__itvv = syzxs__kie.index
        item_ind = builder.load(ogr__nfvx)
        builder.store(builder.trunc(item_ind, lir.IntType(offset_type.
            bitwidth)), builder.gep(offsets_ptr, [mipma__itvv]))
        arr_obj = seq_getitem(builder, context, val, mipma__itvv)
        set_bitmap_bit(builder, null_bitmap_ptr, mipma__itvv, 0)
        sfp__hgg = is_na_value(builder, context, arr_obj, mpof__wvzz)
        dew__zipny = builder.icmp_unsigned('!=', sfp__hgg, lir.Constant(
            sfp__hgg.type, 1))
        with builder.if_then(dew__zipny):
            set_bitmap_bit(builder, null_bitmap_ptr, mipma__itvv, 1)
            n_items = bodo.utils.utils.object_length(c, arr_obj)
            _unbox_array_item_array_copy_data(typ.dtype, arr_obj, c,
                data_arr, item_ind, n_items)
            builder.store(builder.add(item_ind, n_items), ogr__nfvx)
        c.pyapi.decref(arr_obj)
    builder.store(builder.trunc(builder.load(ogr__nfvx), lir.IntType(
        offset_type.bitwidth)), builder.gep(offsets_ptr, [n_arrays]))
    c.pyapi.decref(spix__ubx)
    c.pyapi.decref(mpof__wvzz)


@unbox(ArrayItemArrayType)
def unbox_array_item_array(typ, val, c):
    qttb__eot = isinstance(typ.dtype, types.Array) and typ.dtype.dtype in (
        types.int64, types.float64, types.bool_, datetime_date_type)
    n_arrays = bodo.utils.utils.object_length(c, val)
    if qttb__eot:
        ssyvp__xpdr = lir.FunctionType(lir.IntType(64), [lir.IntType(8).
            as_pointer()])
        gxoyg__ttka = cgutils.get_or_insert_function(c.builder.module,
            ssyvp__xpdr, name='count_total_elems_list_array')
        n_elems = cgutils.pack_array(c.builder, [c.builder.call(gxoyg__ttka,
            [val])])
    else:
        brdnz__kbr = get_array_elem_counts(c, c.builder, c.context, val, typ)
        n_elems = cgutils.pack_array(c.builder, [c.builder.extract_value(
            brdnz__kbr, qfuv__nvggi) for qfuv__nvggi in range(1, brdnz__kbr
            .type.count)])
    bth__xbbj, data_arr, offsets_ptr, null_bitmap_ptr = (
        construct_array_item_array(c.context, c.builder, typ, n_arrays,
        n_elems, c))
    if qttb__eot:
        cdx__nufbz = bodo.utils.utils.numba_to_c_type(typ.dtype.dtype)
        clpi__ctqfj = c.context.make_array(typ.dtype)(c.context, c.builder,
            data_arr).data
        ssyvp__xpdr = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(32)])
        acth__asgy = cgutils.get_or_insert_function(c.builder.module,
            ssyvp__xpdr, name='array_item_array_from_sequence')
        c.builder.call(acth__asgy, [val, c.builder.bitcast(clpi__ctqfj, lir
            .IntType(8).as_pointer()), offsets_ptr, null_bitmap_ptr, lir.
            Constant(lir.IntType(32), cdx__nufbz)])
    else:
        _unbox_array_item_array_generic(typ, val, c, n_arrays, data_arr,
            offsets_ptr, null_bitmap_ptr)
    rkw__thw = c.context.make_helper(c.builder, typ)
    rkw__thw.meminfo = bth__xbbj
    hoc__brliw = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(rkw__thw._getvalue(), is_error=hoc__brliw)


def _get_array_item_arr_payload(context, builder, arr_typ, arr):
    rkw__thw = context.make_helper(builder, arr_typ, arr)
    payload_type = ArrayItemArrayPayloadType(arr_typ)
    kbu__ktfy = context.nrt.meminfo_data(builder, rkw__thw.meminfo)
    ieoq__usz = builder.bitcast(kbu__ktfy, context.get_value_type(
        payload_type).as_pointer())
    fnh__sgti = cgutils.create_struct_proxy(payload_type)(context, builder,
        builder.load(ieoq__usz))
    return fnh__sgti


def _box_array_item_array_generic(typ, c, n_arrays, data_arr, offsets_ptr,
    null_bitmap_ptr):
    context = c.context
    builder = c.builder
    rfocx__nkax = context.insert_const_string(builder.module, 'numpy')
    rpjh__wux = c.pyapi.import_module_noblock(rfocx__nkax)
    tciot__oyn = c.pyapi.object_getattr_string(rpjh__wux, 'object_')
    sysoj__tmjh = c.pyapi.long_from_longlong(n_arrays)
    lildm__matwp = c.pyapi.call_method(rpjh__wux, 'ndarray', (sysoj__tmjh,
        tciot__oyn))
    nbw__ysg = c.pyapi.object_getattr_string(rpjh__wux, 'nan')
    ogr__nfvx = cgutils.alloca_once_value(builder, lir.Constant(lir.IntType
        (64), 0))
    with cgutils.for_range(builder, n_arrays) as syzxs__kie:
        mipma__itvv = syzxs__kie.index
        pyarray_setitem(builder, context, lildm__matwp, mipma__itvv, nbw__ysg)
        xsdk__cqww = get_bitmap_bit(builder, null_bitmap_ptr, mipma__itvv)
        lqgqa__yth = builder.icmp_unsigned('!=', xsdk__cqww, lir.Constant(
            lir.IntType(8), 0))
        with builder.if_then(lqgqa__yth):
            n_items = builder.sext(builder.sub(builder.load(builder.gep(
                offsets_ptr, [builder.add(mipma__itvv, lir.Constant(
                mipma__itvv.type, 1))])), builder.load(builder.gep(
                offsets_ptr, [mipma__itvv]))), lir.IntType(64))
            item_ind = builder.load(ogr__nfvx)
            fodg__wepny, ozc__mteip = c.pyapi.call_jit_code(lambda data_arr,
                item_ind, n_items: data_arr[item_ind:item_ind + n_items],
                typ.dtype(typ.dtype, types.int64, types.int64), [data_arr,
                item_ind, n_items])
            builder.store(builder.add(item_ind, n_items), ogr__nfvx)
            arr_obj = c.pyapi.from_native_value(typ.dtype, ozc__mteip, c.
                env_manager)
            pyarray_setitem(builder, context, lildm__matwp, mipma__itvv,
                arr_obj)
            c.pyapi.decref(arr_obj)
    c.pyapi.decref(rpjh__wux)
    c.pyapi.decref(tciot__oyn)
    c.pyapi.decref(sysoj__tmjh)
    c.pyapi.decref(nbw__ysg)
    return lildm__matwp


@box(ArrayItemArrayType)
def box_array_item_arr(typ, val, c):
    fnh__sgti = _get_array_item_arr_payload(c.context, c.builder, typ, val)
    data_arr = fnh__sgti.data
    offsets_ptr = c.context.make_helper(c.builder, types.Array(offset_type,
        1, 'C'), fnh__sgti.offsets).data
    null_bitmap_ptr = c.context.make_helper(c.builder, types.Array(types.
        uint8, 1, 'C'), fnh__sgti.null_bitmap).data
    if isinstance(typ.dtype, types.Array) and typ.dtype.dtype in (types.
        int64, types.float64, types.bool_, datetime_date_type):
        cdx__nufbz = bodo.utils.utils.numba_to_c_type(typ.dtype.dtype)
        clpi__ctqfj = c.context.make_helper(c.builder, typ.dtype, data_arr
            ).data
        ssyvp__xpdr = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(32)])
        rcbiu__vybd = cgutils.get_or_insert_function(c.builder.module,
            ssyvp__xpdr, name='np_array_from_array_item_array')
        arr = c.builder.call(rcbiu__vybd, [fnh__sgti.n_arrays, c.builder.
            bitcast(clpi__ctqfj, lir.IntType(8).as_pointer()), offsets_ptr,
            null_bitmap_ptr, lir.Constant(lir.IntType(32), cdx__nufbz)])
    else:
        arr = _box_array_item_array_generic(typ, c, fnh__sgti.n_arrays,
            data_arr, offsets_ptr, null_bitmap_ptr)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def lower_pre_alloc_array_item_array(context, builder, sig, args):
    array_item_type = sig.return_type
    vwgjc__tbp, bhtm__qwkcj, ozxu__pjom = args
    xgmh__ugy = bodo.utils.transform.get_type_alloc_counts(array_item_type.
        dtype)
    nlxi__jhoa = sig.args[1]
    if not isinstance(nlxi__jhoa, types.UniTuple):
        bhtm__qwkcj = cgutils.pack_array(builder, [lir.Constant(lir.IntType
            (64), -1) for ozxu__pjom in range(xgmh__ugy)])
    elif nlxi__jhoa.count < xgmh__ugy:
        bhtm__qwkcj = cgutils.pack_array(builder, [builder.extract_value(
            bhtm__qwkcj, qfuv__nvggi) for qfuv__nvggi in range(nlxi__jhoa.
            count)] + [lir.Constant(lir.IntType(64), -1) for ozxu__pjom in
            range(xgmh__ugy - nlxi__jhoa.count)])
    bth__xbbj, ozxu__pjom, ozxu__pjom, ozxu__pjom = construct_array_item_array(
        context, builder, array_item_type, vwgjc__tbp, bhtm__qwkcj)
    rkw__thw = context.make_helper(builder, array_item_type)
    rkw__thw.meminfo = bth__xbbj
    return rkw__thw._getvalue()


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
    n_arrays, eycja__sguy, alak__civyd, zmvp__jeeu = args
    array_item_type = signature.return_type
    payload_type = ArrayItemArrayPayloadType(array_item_type)
    tvyv__flf = context.get_value_type(payload_type)
    oxm__hsvly = context.get_abi_sizeof(tvyv__flf)
    xow__qut = define_array_item_dtor(context, builder, array_item_type,
        payload_type)
    bth__xbbj = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, oxm__hsvly), xow__qut)
    kbu__ktfy = context.nrt.meminfo_data(builder, bth__xbbj)
    ieoq__usz = builder.bitcast(kbu__ktfy, tvyv__flf.as_pointer())
    fnh__sgti = cgutils.create_struct_proxy(payload_type)(context, builder)
    fnh__sgti.n_arrays = n_arrays
    fnh__sgti.data = eycja__sguy
    fnh__sgti.offsets = alak__civyd
    fnh__sgti.null_bitmap = zmvp__jeeu
    builder.store(fnh__sgti._getvalue(), ieoq__usz)
    context.nrt.incref(builder, signature.args[1], eycja__sguy)
    context.nrt.incref(builder, signature.args[2], alak__civyd)
    context.nrt.incref(builder, signature.args[3], zmvp__jeeu)
    rkw__thw = context.make_helper(builder, array_item_type)
    rkw__thw.meminfo = bth__xbbj
    return rkw__thw._getvalue()


@intrinsic
def init_array_item_array(typingctx, n_arrays_typ, data_type, offsets_typ,
    null_bitmap_typ=None):
    assert null_bitmap_typ == types.Array(types.uint8, 1, 'C')
    dov__wekzr = ArrayItemArrayType(data_type)
    sig = dov__wekzr(types.int64, data_type, offsets_typ, null_bitmap_typ)
    return sig, init_array_item_array_codegen


@intrinsic
def get_offsets(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        fnh__sgti = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            fnh__sgti.offsets)
    return types.Array(offset_type, 1, 'C')(arr_typ), codegen


@intrinsic
def get_offsets_ind(typingctx, arr_typ, ind_t=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, ind = args
        fnh__sgti = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        clpi__ctqfj = context.make_array(types.Array(offset_type, 1, 'C'))(
            context, builder, fnh__sgti.offsets).data
        alak__civyd = builder.bitcast(clpi__ctqfj, lir.IntType(offset_type.
            bitwidth).as_pointer())
        return builder.load(builder.gep(alak__civyd, [ind]))
    return offset_type(arr_typ, types.int64), codegen


@intrinsic
def get_data(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        fnh__sgti = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            fnh__sgti.data)
    return arr_typ.dtype(arr_typ), codegen


@intrinsic
def get_null_bitmap(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        fnh__sgti = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            fnh__sgti.null_bitmap)
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
        fnh__sgti = _get_array_item_arr_payload(context, builder, arr_typ, arr)
        return fnh__sgti.n_arrays
    return types.int64(arr_typ), codegen


@intrinsic
def replace_data_arr(typingctx, arr_typ, data_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType
        ) and data_typ == arr_typ.dtype

    def codegen(context, builder, sig, args):
        arr, byk__aco = args
        rkw__thw = context.make_helper(builder, arr_typ, arr)
        payload_type = ArrayItemArrayPayloadType(arr_typ)
        kbu__ktfy = context.nrt.meminfo_data(builder, rkw__thw.meminfo)
        ieoq__usz = builder.bitcast(kbu__ktfy, context.get_value_type(
            payload_type).as_pointer())
        fnh__sgti = cgutils.create_struct_proxy(payload_type)(context,
            builder, builder.load(ieoq__usz))
        context.nrt.decref(builder, data_typ, fnh__sgti.data)
        fnh__sgti.data = byk__aco
        context.nrt.incref(builder, data_typ, byk__aco)
        builder.store(fnh__sgti._getvalue(), ieoq__usz)
    return types.none(arr_typ, data_typ), codegen


@numba.njit(no_cpython_wrapper=True)
def ensure_data_capacity(arr, old_size, new_size):
    eycja__sguy = get_data(arr)
    ekcl__cuc = len(eycja__sguy)
    if ekcl__cuc < new_size:
        bsf__gyekg = max(2 * ekcl__cuc, new_size)
        byk__aco = bodo.libs.array_kernels.resize_and_copy(eycja__sguy,
            old_size, bsf__gyekg)
        replace_data_arr(arr, byk__aco)


@numba.njit(no_cpython_wrapper=True)
def trim_excess_data(arr):
    eycja__sguy = get_data(arr)
    alak__civyd = get_offsets(arr)
    fzc__ucby = len(eycja__sguy)
    bxpx__nzgs = alak__civyd[-1]
    if fzc__ucby != bxpx__nzgs:
        byk__aco = bodo.libs.array_kernels.resize_and_copy(eycja__sguy,
            bxpx__nzgs, bxpx__nzgs)
        replace_data_arr(arr, byk__aco)


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
            alak__civyd = get_offsets(arr)
            eycja__sguy = get_data(arr)
            lqb__dqsk = alak__civyd[ind]
            yum__etj = alak__civyd[ind + 1]
            return eycja__sguy[lqb__dqsk:yum__etj]
        return array_item_arr_getitem_impl
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        zubb__xsg = arr.dtype

        def impl_bool(arr, ind):
            kqf__cpp = len(arr)
            if kqf__cpp != len(ind):
                raise IndexError(
                    'boolean index did not match indexed array along dimension 0'
                    )
            zmvp__jeeu = get_null_bitmap(arr)
            n_arrays = 0
            oxrra__iwfsw = init_nested_counts(zubb__xsg)
            for qfuv__nvggi in range(kqf__cpp):
                if ind[qfuv__nvggi]:
                    n_arrays += 1
                    kge__wocuw = arr[qfuv__nvggi]
                    oxrra__iwfsw = add_nested_counts(oxrra__iwfsw, kge__wocuw)
            lildm__matwp = pre_alloc_array_item_array(n_arrays,
                oxrra__iwfsw, zubb__xsg)
            pvbiy__usycs = get_null_bitmap(lildm__matwp)
            ajsfv__dlgvt = 0
            for cfht__lfi in range(kqf__cpp):
                if ind[cfht__lfi]:
                    lildm__matwp[ajsfv__dlgvt] = arr[cfht__lfi]
                    wmu__kaq = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        zmvp__jeeu, cfht__lfi)
                    bodo.libs.int_arr_ext.set_bit_to_arr(pvbiy__usycs,
                        ajsfv__dlgvt, wmu__kaq)
                    ajsfv__dlgvt += 1
            return lildm__matwp
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        zubb__xsg = arr.dtype

        def impl_int(arr, ind):
            zmvp__jeeu = get_null_bitmap(arr)
            kqf__cpp = len(ind)
            n_arrays = kqf__cpp
            oxrra__iwfsw = init_nested_counts(zubb__xsg)
            for fztq__bvx in range(kqf__cpp):
                qfuv__nvggi = ind[fztq__bvx]
                kge__wocuw = arr[qfuv__nvggi]
                oxrra__iwfsw = add_nested_counts(oxrra__iwfsw, kge__wocuw)
            lildm__matwp = pre_alloc_array_item_array(n_arrays,
                oxrra__iwfsw, zubb__xsg)
            pvbiy__usycs = get_null_bitmap(lildm__matwp)
            for luwmd__isq in range(kqf__cpp):
                cfht__lfi = ind[luwmd__isq]
                lildm__matwp[luwmd__isq] = arr[cfht__lfi]
                wmu__kaq = bodo.libs.int_arr_ext.get_bit_bitmap_arr(zmvp__jeeu,
                    cfht__lfi)
                bodo.libs.int_arr_ext.set_bit_to_arr(pvbiy__usycs,
                    luwmd__isq, wmu__kaq)
            return lildm__matwp
        return impl_int
    if isinstance(ind, types.SliceType):

        def impl_slice(arr, ind):
            kqf__cpp = len(arr)
            oexif__vbf = numba.cpython.unicode._normalize_slice(ind, kqf__cpp)
            mulxl__efj = np.arange(oexif__vbf.start, oexif__vbf.stop,
                oexif__vbf.step)
            return arr[mulxl__efj]
        return impl_slice


@overload(operator.setitem)
def array_item_arr_setitem(A, idx, val):
    if not isinstance(A, ArrayItemArrayType):
        return
    if isinstance(idx, types.Integer):

        def impl_scalar(A, idx, val):
            alak__civyd = get_offsets(A)
            zmvp__jeeu = get_null_bitmap(A)
            if idx == 0:
                alak__civyd[0] = 0
            n_items = len(val)
            qag__hbp = alak__civyd[idx] + n_items
            ensure_data_capacity(A, alak__civyd[idx], qag__hbp)
            eycja__sguy = get_data(A)
            alak__civyd[idx + 1] = alak__civyd[idx] + n_items
            eycja__sguy[alak__civyd[idx]:alak__civyd[idx + 1]] = val
            bodo.libs.int_arr_ext.set_bit_to_arr(zmvp__jeeu, idx, 1)
        return impl_scalar
    if isinstance(idx, types.SliceType) and A.dtype == val:

        def impl_slice_elem(A, idx, val):
            oexif__vbf = numba.cpython.unicode._normalize_slice(idx, len(A))
            for qfuv__nvggi in range(oexif__vbf.start, oexif__vbf.stop,
                oexif__vbf.step):
                A[qfuv__nvggi] = val
        return impl_slice_elem
    if isinstance(idx, types.SliceType) and is_iterable_type(val):

        def impl_slice(A, idx, val):
            val = bodo.utils.conversion.coerce_to_array(val,
                use_nullable_array=True)
            alak__civyd = get_offsets(A)
            zmvp__jeeu = get_null_bitmap(A)
            jztli__hnmxg = get_offsets(val)
            isei__bxlj = get_data(val)
            lwhh__tak = get_null_bitmap(val)
            kqf__cpp = len(A)
            oexif__vbf = numba.cpython.unicode._normalize_slice(idx, kqf__cpp)
            somhz__orboe, zogb__qgwi = oexif__vbf.start, oexif__vbf.stop
            assert oexif__vbf.step == 1
            if somhz__orboe == 0:
                alak__civyd[somhz__orboe] = 0
            gerh__emlx = alak__civyd[somhz__orboe]
            qag__hbp = gerh__emlx + len(isei__bxlj)
            ensure_data_capacity(A, gerh__emlx, qag__hbp)
            eycja__sguy = get_data(A)
            eycja__sguy[gerh__emlx:gerh__emlx + len(isei__bxlj)] = isei__bxlj
            alak__civyd[somhz__orboe:zogb__qgwi + 1
                ] = jztli__hnmxg + gerh__emlx
            etw__irnvp = 0
            for qfuv__nvggi in range(somhz__orboe, zogb__qgwi):
                wmu__kaq = bodo.libs.int_arr_ext.get_bit_bitmap_arr(lwhh__tak,
                    etw__irnvp)
                bodo.libs.int_arr_ext.set_bit_to_arr(zmvp__jeeu,
                    qfuv__nvggi, wmu__kaq)
                etw__irnvp += 1
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
