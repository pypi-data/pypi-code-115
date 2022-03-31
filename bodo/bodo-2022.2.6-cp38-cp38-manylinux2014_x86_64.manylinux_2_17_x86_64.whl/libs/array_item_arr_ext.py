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
        nlgz__eimvo = [('n_arrays', types.int64), ('data', fe_type.
            array_type.dtype), ('offsets', types.Array(offset_type, 1, 'C')
            ), ('null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, nlgz__eimvo)


@register_model(ArrayItemArrayType)
class ArrayItemArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = ArrayItemArrayPayloadType(fe_type)
        nlgz__eimvo = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, nlgz__eimvo)


def define_array_item_dtor(context, builder, array_item_type, payload_type):
    cfb__ihkjo = builder.module
    wrlrc__ebf = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    wmuw__vux = cgutils.get_or_insert_function(cfb__ihkjo, wrlrc__ebf, name
        ='.dtor.array_item.{}'.format(array_item_type.dtype))
    if not wmuw__vux.is_declaration:
        return wmuw__vux
    wmuw__vux.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(wmuw__vux.append_basic_block())
    dsj__lpt = wmuw__vux.args[0]
    amgx__uchx = context.get_value_type(payload_type).as_pointer()
    azzip__xqhuq = builder.bitcast(dsj__lpt, amgx__uchx)
    inw__xvzex = context.make_helper(builder, payload_type, ref=azzip__xqhuq)
    context.nrt.decref(builder, array_item_type.dtype, inw__xvzex.data)
    context.nrt.decref(builder, types.Array(offset_type, 1, 'C'),
        inw__xvzex.offsets)
    context.nrt.decref(builder, types.Array(types.uint8, 1, 'C'),
        inw__xvzex.null_bitmap)
    builder.ret_void()
    return wmuw__vux


def construct_array_item_array(context, builder, array_item_type, n_arrays,
    n_elems, c=None):
    payload_type = ArrayItemArrayPayloadType(array_item_type)
    phe__lkp = context.get_value_type(payload_type)
    mbbe__pfpcn = context.get_abi_sizeof(phe__lkp)
    jmjav__dye = define_array_item_dtor(context, builder, array_item_type,
        payload_type)
    otthi__mgl = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, mbbe__pfpcn), jmjav__dye)
    akpzd__afx = context.nrt.meminfo_data(builder, otthi__mgl)
    uklvl__jllld = builder.bitcast(akpzd__afx, phe__lkp.as_pointer())
    inw__xvzex = cgutils.create_struct_proxy(payload_type)(context, builder)
    inw__xvzex.n_arrays = n_arrays
    brahl__sdlgk = n_elems.type.count
    bonc__buiox = builder.extract_value(n_elems, 0)
    gnjuc__elvx = cgutils.alloca_once_value(builder, bonc__buiox)
    xmnep__hlemp = builder.icmp_signed('==', bonc__buiox, lir.Constant(
        bonc__buiox.type, -1))
    with builder.if_then(xmnep__hlemp):
        builder.store(n_arrays, gnjuc__elvx)
    n_elems = cgutils.pack_array(builder, [builder.load(gnjuc__elvx)] + [
        builder.extract_value(n_elems, havc__nnr) for havc__nnr in range(1,
        brahl__sdlgk)])
    inw__xvzex.data = gen_allocate_array(context, builder, array_item_type.
        dtype, n_elems, c)
    azpyo__dmrx = builder.add(n_arrays, lir.Constant(lir.IntType(64), 1))
    ltj__vrud = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(offset_type, 1, 'C'), [azpyo__dmrx])
    offsets_ptr = ltj__vrud.data
    builder.store(context.get_constant(offset_type, 0), offsets_ptr)
    builder.store(builder.trunc(builder.extract_value(n_elems, 0), lir.
        IntType(offset_type.bitwidth)), builder.gep(offsets_ptr, [n_arrays]))
    inw__xvzex.offsets = ltj__vrud._getvalue()
    cvida__myi = builder.udiv(builder.add(n_arrays, lir.Constant(lir.
        IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
    pnmm__zvx = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(types.uint8, 1, 'C'), [cvida__myi])
    null_bitmap_ptr = pnmm__zvx.data
    inw__xvzex.null_bitmap = pnmm__zvx._getvalue()
    builder.store(inw__xvzex._getvalue(), uklvl__jllld)
    return otthi__mgl, inw__xvzex.data, offsets_ptr, null_bitmap_ptr


def _unbox_array_item_array_copy_data(arr_typ, arr_obj, c, data_arr,
    item_ind, n_items):
    context = c.context
    builder = c.builder
    arr_obj = to_arr_obj_if_list_obj(c, context, builder, arr_obj, arr_typ)
    arr_val = c.pyapi.to_native_value(arr_typ, arr_obj).value
    sig = types.none(arr_typ, types.int64, types.int64, arr_typ)

    def copy_data(data_arr, item_ind, n_items, arr_val):
        data_arr[item_ind:item_ind + n_items] = arr_val
    uza__nrqvd, uynlb__dys = c.pyapi.call_jit_code(copy_data, sig, [
        data_arr, item_ind, n_items, arr_val])
    c.context.nrt.decref(builder, arr_typ, arr_val)


def _unbox_array_item_array_generic(typ, val, c, n_arrays, data_arr,
    offsets_ptr, null_bitmap_ptr):
    context = c.context
    builder = c.builder
    ybe__ixp = context.insert_const_string(builder.module, 'pandas')
    nev__pzr = c.pyapi.import_module_noblock(ybe__ixp)
    dubt__vmux = c.pyapi.object_getattr_string(nev__pzr, 'NA')
    ywq__xhpk = c.context.get_constant(offset_type, 0)
    builder.store(ywq__xhpk, offsets_ptr)
    rvlf__opwai = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with cgutils.for_range(builder, n_arrays) as cnsp__nzzx:
        ktna__aumpm = cnsp__nzzx.index
        item_ind = builder.load(rvlf__opwai)
        builder.store(builder.trunc(item_ind, lir.IntType(offset_type.
            bitwidth)), builder.gep(offsets_ptr, [ktna__aumpm]))
        arr_obj = seq_getitem(builder, context, val, ktna__aumpm)
        set_bitmap_bit(builder, null_bitmap_ptr, ktna__aumpm, 0)
        uvjf__ckv = is_na_value(builder, context, arr_obj, dubt__vmux)
        sdan__sig = builder.icmp_unsigned('!=', uvjf__ckv, lir.Constant(
            uvjf__ckv.type, 1))
        with builder.if_then(sdan__sig):
            set_bitmap_bit(builder, null_bitmap_ptr, ktna__aumpm, 1)
            n_items = bodo.utils.utils.object_length(c, arr_obj)
            _unbox_array_item_array_copy_data(typ.dtype, arr_obj, c,
                data_arr, item_ind, n_items)
            builder.store(builder.add(item_ind, n_items), rvlf__opwai)
        c.pyapi.decref(arr_obj)
    builder.store(builder.trunc(builder.load(rvlf__opwai), lir.IntType(
        offset_type.bitwidth)), builder.gep(offsets_ptr, [n_arrays]))
    c.pyapi.decref(nev__pzr)
    c.pyapi.decref(dubt__vmux)


@unbox(ArrayItemArrayType)
def unbox_array_item_array(typ, val, c):
    peaa__qiuq = isinstance(typ.dtype, types.Array) and typ.dtype.dtype in (
        types.int64, types.float64, types.bool_, datetime_date_type)
    n_arrays = bodo.utils.utils.object_length(c, val)
    if peaa__qiuq:
        wrlrc__ebf = lir.FunctionType(lir.IntType(64), [lir.IntType(8).
            as_pointer()])
        vcmol__yzkr = cgutils.get_or_insert_function(c.builder.module,
            wrlrc__ebf, name='count_total_elems_list_array')
        n_elems = cgutils.pack_array(c.builder, [c.builder.call(vcmol__yzkr,
            [val])])
    else:
        sfd__atbp = get_array_elem_counts(c, c.builder, c.context, val, typ)
        n_elems = cgutils.pack_array(c.builder, [c.builder.extract_value(
            sfd__atbp, havc__nnr) for havc__nnr in range(1, sfd__atbp.type.
            count)])
    otthi__mgl, data_arr, offsets_ptr, null_bitmap_ptr = (
        construct_array_item_array(c.context, c.builder, typ, n_arrays,
        n_elems, c))
    if peaa__qiuq:
        oodb__xbnpy = bodo.utils.utils.numba_to_c_type(typ.dtype.dtype)
        ndb__pbjpz = c.context.make_array(typ.dtype)(c.context, c.builder,
            data_arr).data
        wrlrc__ebf = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(32)])
        wmuw__vux = cgutils.get_or_insert_function(c.builder.module,
            wrlrc__ebf, name='array_item_array_from_sequence')
        c.builder.call(wmuw__vux, [val, c.builder.bitcast(ndb__pbjpz, lir.
            IntType(8).as_pointer()), offsets_ptr, null_bitmap_ptr, lir.
            Constant(lir.IntType(32), oodb__xbnpy)])
    else:
        _unbox_array_item_array_generic(typ, val, c, n_arrays, data_arr,
            offsets_ptr, null_bitmap_ptr)
    mgao__nvkv = c.context.make_helper(c.builder, typ)
    mgao__nvkv.meminfo = otthi__mgl
    dfjw__ecpow = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(mgao__nvkv._getvalue(), is_error=dfjw__ecpow)


def _get_array_item_arr_payload(context, builder, arr_typ, arr):
    mgao__nvkv = context.make_helper(builder, arr_typ, arr)
    payload_type = ArrayItemArrayPayloadType(arr_typ)
    akpzd__afx = context.nrt.meminfo_data(builder, mgao__nvkv.meminfo)
    uklvl__jllld = builder.bitcast(akpzd__afx, context.get_value_type(
        payload_type).as_pointer())
    inw__xvzex = cgutils.create_struct_proxy(payload_type)(context, builder,
        builder.load(uklvl__jllld))
    return inw__xvzex


def _box_array_item_array_generic(typ, c, n_arrays, data_arr, offsets_ptr,
    null_bitmap_ptr):
    context = c.context
    builder = c.builder
    ybe__ixp = context.insert_const_string(builder.module, 'numpy')
    zbui__ghddp = c.pyapi.import_module_noblock(ybe__ixp)
    enhq__tax = c.pyapi.object_getattr_string(zbui__ghddp, 'object_')
    yvz__zvwzy = c.pyapi.long_from_longlong(n_arrays)
    orves__yvnv = c.pyapi.call_method(zbui__ghddp, 'ndarray', (yvz__zvwzy,
        enhq__tax))
    qxu__zrgs = c.pyapi.object_getattr_string(zbui__ghddp, 'nan')
    rvlf__opwai = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(64), 0))
    with cgutils.for_range(builder, n_arrays) as cnsp__nzzx:
        ktna__aumpm = cnsp__nzzx.index
        pyarray_setitem(builder, context, orves__yvnv, ktna__aumpm, qxu__zrgs)
        fch__sjmzg = get_bitmap_bit(builder, null_bitmap_ptr, ktna__aumpm)
        quo__fpivr = builder.icmp_unsigned('!=', fch__sjmzg, lir.Constant(
            lir.IntType(8), 0))
        with builder.if_then(quo__fpivr):
            n_items = builder.sext(builder.sub(builder.load(builder.gep(
                offsets_ptr, [builder.add(ktna__aumpm, lir.Constant(
                ktna__aumpm.type, 1))])), builder.load(builder.gep(
                offsets_ptr, [ktna__aumpm]))), lir.IntType(64))
            item_ind = builder.load(rvlf__opwai)
            uza__nrqvd, qcpny__tartt = c.pyapi.call_jit_code(lambda
                data_arr, item_ind, n_items: data_arr[item_ind:item_ind +
                n_items], typ.dtype(typ.dtype, types.int64, types.int64), [
                data_arr, item_ind, n_items])
            builder.store(builder.add(item_ind, n_items), rvlf__opwai)
            arr_obj = c.pyapi.from_native_value(typ.dtype, qcpny__tartt, c.
                env_manager)
            pyarray_setitem(builder, context, orves__yvnv, ktna__aumpm, arr_obj
                )
            c.pyapi.decref(arr_obj)
    c.pyapi.decref(zbui__ghddp)
    c.pyapi.decref(enhq__tax)
    c.pyapi.decref(yvz__zvwzy)
    c.pyapi.decref(qxu__zrgs)
    return orves__yvnv


@box(ArrayItemArrayType)
def box_array_item_arr(typ, val, c):
    inw__xvzex = _get_array_item_arr_payload(c.context, c.builder, typ, val)
    data_arr = inw__xvzex.data
    offsets_ptr = c.context.make_helper(c.builder, types.Array(offset_type,
        1, 'C'), inw__xvzex.offsets).data
    null_bitmap_ptr = c.context.make_helper(c.builder, types.Array(types.
        uint8, 1, 'C'), inw__xvzex.null_bitmap).data
    if isinstance(typ.dtype, types.Array) and typ.dtype.dtype in (types.
        int64, types.float64, types.bool_, datetime_date_type):
        oodb__xbnpy = bodo.utils.utils.numba_to_c_type(typ.dtype.dtype)
        ndb__pbjpz = c.context.make_helper(c.builder, typ.dtype, data_arr).data
        wrlrc__ebf = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(32)])
        owpf__sin = cgutils.get_or_insert_function(c.builder.module,
            wrlrc__ebf, name='np_array_from_array_item_array')
        arr = c.builder.call(owpf__sin, [inw__xvzex.n_arrays, c.builder.
            bitcast(ndb__pbjpz, lir.IntType(8).as_pointer()), offsets_ptr,
            null_bitmap_ptr, lir.Constant(lir.IntType(32), oodb__xbnpy)])
    else:
        arr = _box_array_item_array_generic(typ, c, inw__xvzex.n_arrays,
            data_arr, offsets_ptr, null_bitmap_ptr)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def lower_pre_alloc_array_item_array(context, builder, sig, args):
    array_item_type = sig.return_type
    cbq__xiu, zkdhi__tdn, unra__bteai = args
    ydh__isyeh = bodo.utils.transform.get_type_alloc_counts(array_item_type
        .dtype)
    jgbe__sxubj = sig.args[1]
    if not isinstance(jgbe__sxubj, types.UniTuple):
        zkdhi__tdn = cgutils.pack_array(builder, [lir.Constant(lir.IntType(
            64), -1) for unra__bteai in range(ydh__isyeh)])
    elif jgbe__sxubj.count < ydh__isyeh:
        zkdhi__tdn = cgutils.pack_array(builder, [builder.extract_value(
            zkdhi__tdn, havc__nnr) for havc__nnr in range(jgbe__sxubj.count
            )] + [lir.Constant(lir.IntType(64), -1) for unra__bteai in
            range(ydh__isyeh - jgbe__sxubj.count)])
    otthi__mgl, unra__bteai, unra__bteai, unra__bteai = (
        construct_array_item_array(context, builder, array_item_type,
        cbq__xiu, zkdhi__tdn))
    mgao__nvkv = context.make_helper(builder, array_item_type)
    mgao__nvkv.meminfo = otthi__mgl
    return mgao__nvkv._getvalue()


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
    n_arrays, ioofw__gxp, ltj__vrud, pnmm__zvx = args
    array_item_type = signature.return_type
    payload_type = ArrayItemArrayPayloadType(array_item_type)
    phe__lkp = context.get_value_type(payload_type)
    mbbe__pfpcn = context.get_abi_sizeof(phe__lkp)
    jmjav__dye = define_array_item_dtor(context, builder, array_item_type,
        payload_type)
    otthi__mgl = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, mbbe__pfpcn), jmjav__dye)
    akpzd__afx = context.nrt.meminfo_data(builder, otthi__mgl)
    uklvl__jllld = builder.bitcast(akpzd__afx, phe__lkp.as_pointer())
    inw__xvzex = cgutils.create_struct_proxy(payload_type)(context, builder)
    inw__xvzex.n_arrays = n_arrays
    inw__xvzex.data = ioofw__gxp
    inw__xvzex.offsets = ltj__vrud
    inw__xvzex.null_bitmap = pnmm__zvx
    builder.store(inw__xvzex._getvalue(), uklvl__jllld)
    context.nrt.incref(builder, signature.args[1], ioofw__gxp)
    context.nrt.incref(builder, signature.args[2], ltj__vrud)
    context.nrt.incref(builder, signature.args[3], pnmm__zvx)
    mgao__nvkv = context.make_helper(builder, array_item_type)
    mgao__nvkv.meminfo = otthi__mgl
    return mgao__nvkv._getvalue()


@intrinsic
def init_array_item_array(typingctx, n_arrays_typ, data_type, offsets_typ,
    null_bitmap_typ=None):
    assert null_bitmap_typ == types.Array(types.uint8, 1, 'C')
    tqbch__sccro = ArrayItemArrayType(data_type)
    sig = tqbch__sccro(types.int64, data_type, offsets_typ, null_bitmap_typ)
    return sig, init_array_item_array_codegen


@intrinsic
def get_offsets(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        inw__xvzex = _get_array_item_arr_payload(context, builder, arr_typ, arr
            )
        return impl_ret_borrowed(context, builder, sig.return_type,
            inw__xvzex.offsets)
    return types.Array(offset_type, 1, 'C')(arr_typ), codegen


@intrinsic
def get_offsets_ind(typingctx, arr_typ, ind_t=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, ind = args
        inw__xvzex = _get_array_item_arr_payload(context, builder, arr_typ, arr
            )
        ndb__pbjpz = context.make_array(types.Array(offset_type, 1, 'C'))(
            context, builder, inw__xvzex.offsets).data
        ltj__vrud = builder.bitcast(ndb__pbjpz, lir.IntType(offset_type.
            bitwidth).as_pointer())
        return builder.load(builder.gep(ltj__vrud, [ind]))
    return offset_type(arr_typ, types.int64), codegen


@intrinsic
def get_data(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        inw__xvzex = _get_array_item_arr_payload(context, builder, arr_typ, arr
            )
        return impl_ret_borrowed(context, builder, sig.return_type,
            inw__xvzex.data)
    return arr_typ.dtype(arr_typ), codegen


@intrinsic
def get_null_bitmap(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        inw__xvzex = _get_array_item_arr_payload(context, builder, arr_typ, arr
            )
        return impl_ret_borrowed(context, builder, sig.return_type,
            inw__xvzex.null_bitmap)
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
        inw__xvzex = _get_array_item_arr_payload(context, builder, arr_typ, arr
            )
        return inw__xvzex.n_arrays
    return types.int64(arr_typ), codegen


@intrinsic
def replace_data_arr(typingctx, arr_typ, data_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType
        ) and data_typ == arr_typ.dtype

    def codegen(context, builder, sig, args):
        arr, zcaq__odsq = args
        mgao__nvkv = context.make_helper(builder, arr_typ, arr)
        payload_type = ArrayItemArrayPayloadType(arr_typ)
        akpzd__afx = context.nrt.meminfo_data(builder, mgao__nvkv.meminfo)
        uklvl__jllld = builder.bitcast(akpzd__afx, context.get_value_type(
            payload_type).as_pointer())
        inw__xvzex = cgutils.create_struct_proxy(payload_type)(context,
            builder, builder.load(uklvl__jllld))
        context.nrt.decref(builder, data_typ, inw__xvzex.data)
        inw__xvzex.data = zcaq__odsq
        context.nrt.incref(builder, data_typ, zcaq__odsq)
        builder.store(inw__xvzex._getvalue(), uklvl__jllld)
    return types.none(arr_typ, data_typ), codegen


@numba.njit(no_cpython_wrapper=True)
def ensure_data_capacity(arr, old_size, new_size):
    ioofw__gxp = get_data(arr)
    xosvi__vlals = len(ioofw__gxp)
    if xosvi__vlals < new_size:
        jkuo__azi = max(2 * xosvi__vlals, new_size)
        zcaq__odsq = bodo.libs.array_kernels.resize_and_copy(ioofw__gxp,
            old_size, jkuo__azi)
        replace_data_arr(arr, zcaq__odsq)


@numba.njit(no_cpython_wrapper=True)
def trim_excess_data(arr):
    ioofw__gxp = get_data(arr)
    ltj__vrud = get_offsets(arr)
    ujzxm__cnm = len(ioofw__gxp)
    aid__apfwv = ltj__vrud[-1]
    if ujzxm__cnm != aid__apfwv:
        zcaq__odsq = bodo.libs.array_kernels.resize_and_copy(ioofw__gxp,
            aid__apfwv, aid__apfwv)
        replace_data_arr(arr, zcaq__odsq)


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
            ltj__vrud = get_offsets(arr)
            ioofw__gxp = get_data(arr)
            ena__uif = ltj__vrud[ind]
            stzml__dllr = ltj__vrud[ind + 1]
            return ioofw__gxp[ena__uif:stzml__dllr]
        return array_item_arr_getitem_impl
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        vcdel__xusy = arr.dtype

        def impl_bool(arr, ind):
            exrej__iwm = len(arr)
            if exrej__iwm != len(ind):
                raise IndexError(
                    'boolean index did not match indexed array along dimension 0'
                    )
            pnmm__zvx = get_null_bitmap(arr)
            n_arrays = 0
            lys__qtpq = init_nested_counts(vcdel__xusy)
            for havc__nnr in range(exrej__iwm):
                if ind[havc__nnr]:
                    n_arrays += 1
                    dan__lnmqw = arr[havc__nnr]
                    lys__qtpq = add_nested_counts(lys__qtpq, dan__lnmqw)
            orves__yvnv = pre_alloc_array_item_array(n_arrays, lys__qtpq,
                vcdel__xusy)
            wawrq__oevo = get_null_bitmap(orves__yvnv)
            qbuy__emgs = 0
            for eaqne__rtaye in range(exrej__iwm):
                if ind[eaqne__rtaye]:
                    orves__yvnv[qbuy__emgs] = arr[eaqne__rtaye]
                    boxe__chxm = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        pnmm__zvx, eaqne__rtaye)
                    bodo.libs.int_arr_ext.set_bit_to_arr(wawrq__oevo,
                        qbuy__emgs, boxe__chxm)
                    qbuy__emgs += 1
            return orves__yvnv
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        vcdel__xusy = arr.dtype

        def impl_int(arr, ind):
            pnmm__zvx = get_null_bitmap(arr)
            exrej__iwm = len(ind)
            n_arrays = exrej__iwm
            lys__qtpq = init_nested_counts(vcdel__xusy)
            for iofc__beu in range(exrej__iwm):
                havc__nnr = ind[iofc__beu]
                dan__lnmqw = arr[havc__nnr]
                lys__qtpq = add_nested_counts(lys__qtpq, dan__lnmqw)
            orves__yvnv = pre_alloc_array_item_array(n_arrays, lys__qtpq,
                vcdel__xusy)
            wawrq__oevo = get_null_bitmap(orves__yvnv)
            for tuw__fuxa in range(exrej__iwm):
                eaqne__rtaye = ind[tuw__fuxa]
                orves__yvnv[tuw__fuxa] = arr[eaqne__rtaye]
                boxe__chxm = bodo.libs.int_arr_ext.get_bit_bitmap_arr(pnmm__zvx
                    , eaqne__rtaye)
                bodo.libs.int_arr_ext.set_bit_to_arr(wawrq__oevo, tuw__fuxa,
                    boxe__chxm)
            return orves__yvnv
        return impl_int
    if isinstance(ind, types.SliceType):

        def impl_slice(arr, ind):
            exrej__iwm = len(arr)
            wzqe__vdjip = numba.cpython.unicode._normalize_slice(ind,
                exrej__iwm)
            mzqb__zur = np.arange(wzqe__vdjip.start, wzqe__vdjip.stop,
                wzqe__vdjip.step)
            return arr[mzqb__zur]
        return impl_slice


@overload(operator.setitem)
def array_item_arr_setitem(A, idx, val):
    if not isinstance(A, ArrayItemArrayType):
        return
    if isinstance(idx, types.Integer):

        def impl_scalar(A, idx, val):
            ltj__vrud = get_offsets(A)
            pnmm__zvx = get_null_bitmap(A)
            if idx == 0:
                ltj__vrud[0] = 0
            n_items = len(val)
            cjq__aupg = ltj__vrud[idx] + n_items
            ensure_data_capacity(A, ltj__vrud[idx], cjq__aupg)
            ioofw__gxp = get_data(A)
            ltj__vrud[idx + 1] = ltj__vrud[idx] + n_items
            ioofw__gxp[ltj__vrud[idx]:ltj__vrud[idx + 1]] = val
            bodo.libs.int_arr_ext.set_bit_to_arr(pnmm__zvx, idx, 1)
        return impl_scalar
    if isinstance(idx, types.SliceType) and A.dtype == val:

        def impl_slice_elem(A, idx, val):
            wzqe__vdjip = numba.cpython.unicode._normalize_slice(idx, len(A))
            for havc__nnr in range(wzqe__vdjip.start, wzqe__vdjip.stop,
                wzqe__vdjip.step):
                A[havc__nnr] = val
        return impl_slice_elem
    if isinstance(idx, types.SliceType) and is_iterable_type(val):

        def impl_slice(A, idx, val):
            val = bodo.utils.conversion.coerce_to_array(val,
                use_nullable_array=True)
            ltj__vrud = get_offsets(A)
            pnmm__zvx = get_null_bitmap(A)
            krl__haoyw = get_offsets(val)
            spt__horq = get_data(val)
            dte__qtt = get_null_bitmap(val)
            exrej__iwm = len(A)
            wzqe__vdjip = numba.cpython.unicode._normalize_slice(idx,
                exrej__iwm)
            uvkb__vsqz, wdo__wmki = wzqe__vdjip.start, wzqe__vdjip.stop
            assert wzqe__vdjip.step == 1
            if uvkb__vsqz == 0:
                ltj__vrud[uvkb__vsqz] = 0
            fffyc__lkf = ltj__vrud[uvkb__vsqz]
            cjq__aupg = fffyc__lkf + len(spt__horq)
            ensure_data_capacity(A, fffyc__lkf, cjq__aupg)
            ioofw__gxp = get_data(A)
            ioofw__gxp[fffyc__lkf:fffyc__lkf + len(spt__horq)] = spt__horq
            ltj__vrud[uvkb__vsqz:wdo__wmki + 1] = krl__haoyw + fffyc__lkf
            ans__oawf = 0
            for havc__nnr in range(uvkb__vsqz, wdo__wmki):
                boxe__chxm = bodo.libs.int_arr_ext.get_bit_bitmap_arr(dte__qtt,
                    ans__oawf)
                bodo.libs.int_arr_ext.set_bit_to_arr(pnmm__zvx, havc__nnr,
                    boxe__chxm)
                ans__oawf += 1
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
