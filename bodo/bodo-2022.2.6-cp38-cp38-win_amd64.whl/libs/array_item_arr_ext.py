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
        uex__rczyj = [('n_arrays', types.int64), ('data', fe_type.
            array_type.dtype), ('offsets', types.Array(offset_type, 1, 'C')
            ), ('null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, uex__rczyj)


@register_model(ArrayItemArrayType)
class ArrayItemArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = ArrayItemArrayPayloadType(fe_type)
        uex__rczyj = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, uex__rczyj)


def define_array_item_dtor(context, builder, array_item_type, payload_type):
    qqx__kjhn = builder.module
    yoqw__raopt = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    qzt__hooq = cgutils.get_or_insert_function(qqx__kjhn, yoqw__raopt, name
        ='.dtor.array_item.{}'.format(array_item_type.dtype))
    if not qzt__hooq.is_declaration:
        return qzt__hooq
    qzt__hooq.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(qzt__hooq.append_basic_block())
    djitq__meuu = qzt__hooq.args[0]
    vxxr__cswii = context.get_value_type(payload_type).as_pointer()
    dtk__frsor = builder.bitcast(djitq__meuu, vxxr__cswii)
    ryv__oundt = context.make_helper(builder, payload_type, ref=dtk__frsor)
    context.nrt.decref(builder, array_item_type.dtype, ryv__oundt.data)
    context.nrt.decref(builder, types.Array(offset_type, 1, 'C'),
        ryv__oundt.offsets)
    context.nrt.decref(builder, types.Array(types.uint8, 1, 'C'),
        ryv__oundt.null_bitmap)
    builder.ret_void()
    return qzt__hooq


def construct_array_item_array(context, builder, array_item_type, n_arrays,
    n_elems, c=None):
    payload_type = ArrayItemArrayPayloadType(array_item_type)
    phtpy__rmbw = context.get_value_type(payload_type)
    fvz__yyiab = context.get_abi_sizeof(phtpy__rmbw)
    tqea__gtfx = define_array_item_dtor(context, builder, array_item_type,
        payload_type)
    exk__sgv = context.nrt.meminfo_alloc_dtor(builder, context.get_constant
        (types.uintp, fvz__yyiab), tqea__gtfx)
    pebdy__cur = context.nrt.meminfo_data(builder, exk__sgv)
    sodw__kgbxt = builder.bitcast(pebdy__cur, phtpy__rmbw.as_pointer())
    ryv__oundt = cgutils.create_struct_proxy(payload_type)(context, builder)
    ryv__oundt.n_arrays = n_arrays
    pofez__meble = n_elems.type.count
    tzn__odm = builder.extract_value(n_elems, 0)
    qvy__pza = cgutils.alloca_once_value(builder, tzn__odm)
    suu__vlx = builder.icmp_signed('==', tzn__odm, lir.Constant(tzn__odm.
        type, -1))
    with builder.if_then(suu__vlx):
        builder.store(n_arrays, qvy__pza)
    n_elems = cgutils.pack_array(builder, [builder.load(qvy__pza)] + [
        builder.extract_value(n_elems, zkui__qrnxq) for zkui__qrnxq in
        range(1, pofez__meble)])
    ryv__oundt.data = gen_allocate_array(context, builder, array_item_type.
        dtype, n_elems, c)
    xeog__ysa = builder.add(n_arrays, lir.Constant(lir.IntType(64), 1))
    mshyl__fbnv = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(offset_type, 1, 'C'), [xeog__ysa])
    offsets_ptr = mshyl__fbnv.data
    builder.store(context.get_constant(offset_type, 0), offsets_ptr)
    builder.store(builder.trunc(builder.extract_value(n_elems, 0), lir.
        IntType(offset_type.bitwidth)), builder.gep(offsets_ptr, [n_arrays]))
    ryv__oundt.offsets = mshyl__fbnv._getvalue()
    qxvwo__umgt = builder.udiv(builder.add(n_arrays, lir.Constant(lir.
        IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
    rde__attpo = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(types.uint8, 1, 'C'), [qxvwo__umgt])
    null_bitmap_ptr = rde__attpo.data
    ryv__oundt.null_bitmap = rde__attpo._getvalue()
    builder.store(ryv__oundt._getvalue(), sodw__kgbxt)
    return exk__sgv, ryv__oundt.data, offsets_ptr, null_bitmap_ptr


def _unbox_array_item_array_copy_data(arr_typ, arr_obj, c, data_arr,
    item_ind, n_items):
    context = c.context
    builder = c.builder
    arr_obj = to_arr_obj_if_list_obj(c, context, builder, arr_obj, arr_typ)
    arr_val = c.pyapi.to_native_value(arr_typ, arr_obj).value
    sig = types.none(arr_typ, types.int64, types.int64, arr_typ)

    def copy_data(data_arr, item_ind, n_items, arr_val):
        data_arr[item_ind:item_ind + n_items] = arr_val
    kmfgb__vno, oqhdf__nyt = c.pyapi.call_jit_code(copy_data, sig, [
        data_arr, item_ind, n_items, arr_val])
    c.context.nrt.decref(builder, arr_typ, arr_val)


def _unbox_array_item_array_generic(typ, val, c, n_arrays, data_arr,
    offsets_ptr, null_bitmap_ptr):
    context = c.context
    builder = c.builder
    nqg__ussqo = context.insert_const_string(builder.module, 'pandas')
    fesw__zhgl = c.pyapi.import_module_noblock(nqg__ussqo)
    cmbg__xjm = c.pyapi.object_getattr_string(fesw__zhgl, 'NA')
    iupub__rzh = c.context.get_constant(offset_type, 0)
    builder.store(iupub__rzh, offsets_ptr)
    yhw__mykd = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with cgutils.for_range(builder, n_arrays) as wkhtn__hoadi:
        rruik__veopg = wkhtn__hoadi.index
        item_ind = builder.load(yhw__mykd)
        builder.store(builder.trunc(item_ind, lir.IntType(offset_type.
            bitwidth)), builder.gep(offsets_ptr, [rruik__veopg]))
        arr_obj = seq_getitem(builder, context, val, rruik__veopg)
        set_bitmap_bit(builder, null_bitmap_ptr, rruik__veopg, 0)
        ncxfz__yzk = is_na_value(builder, context, arr_obj, cmbg__xjm)
        nippw__rig = builder.icmp_unsigned('!=', ncxfz__yzk, lir.Constant(
            ncxfz__yzk.type, 1))
        with builder.if_then(nippw__rig):
            set_bitmap_bit(builder, null_bitmap_ptr, rruik__veopg, 1)
            n_items = bodo.utils.utils.object_length(c, arr_obj)
            _unbox_array_item_array_copy_data(typ.dtype, arr_obj, c,
                data_arr, item_ind, n_items)
            builder.store(builder.add(item_ind, n_items), yhw__mykd)
        c.pyapi.decref(arr_obj)
    builder.store(builder.trunc(builder.load(yhw__mykd), lir.IntType(
        offset_type.bitwidth)), builder.gep(offsets_ptr, [n_arrays]))
    c.pyapi.decref(fesw__zhgl)
    c.pyapi.decref(cmbg__xjm)


@unbox(ArrayItemArrayType)
def unbox_array_item_array(typ, val, c):
    xrwty__yhog = isinstance(typ.dtype, types.Array) and typ.dtype.dtype in (
        types.int64, types.float64, types.bool_, datetime_date_type)
    n_arrays = bodo.utils.utils.object_length(c, val)
    if xrwty__yhog:
        yoqw__raopt = lir.FunctionType(lir.IntType(64), [lir.IntType(8).
            as_pointer()])
        xbywm__vtkc = cgutils.get_or_insert_function(c.builder.module,
            yoqw__raopt, name='count_total_elems_list_array')
        n_elems = cgutils.pack_array(c.builder, [c.builder.call(xbywm__vtkc,
            [val])])
    else:
        dyem__xzb = get_array_elem_counts(c, c.builder, c.context, val, typ)
        n_elems = cgutils.pack_array(c.builder, [c.builder.extract_value(
            dyem__xzb, zkui__qrnxq) for zkui__qrnxq in range(1, dyem__xzb.
            type.count)])
    exk__sgv, data_arr, offsets_ptr, null_bitmap_ptr = (
        construct_array_item_array(c.context, c.builder, typ, n_arrays,
        n_elems, c))
    if xrwty__yhog:
        cdtg__xrt = bodo.utils.utils.numba_to_c_type(typ.dtype.dtype)
        saz__man = c.context.make_array(typ.dtype)(c.context, c.builder,
            data_arr).data
        yoqw__raopt = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(
            offset_type.bitwidth).as_pointer(), lir.IntType(8).as_pointer(),
            lir.IntType(32)])
        qzt__hooq = cgutils.get_or_insert_function(c.builder.module,
            yoqw__raopt, name='array_item_array_from_sequence')
        c.builder.call(qzt__hooq, [val, c.builder.bitcast(saz__man, lir.
            IntType(8).as_pointer()), offsets_ptr, null_bitmap_ptr, lir.
            Constant(lir.IntType(32), cdtg__xrt)])
    else:
        _unbox_array_item_array_generic(typ, val, c, n_arrays, data_arr,
            offsets_ptr, null_bitmap_ptr)
    bmv__uegra = c.context.make_helper(c.builder, typ)
    bmv__uegra.meminfo = exk__sgv
    tkirl__mtnhm = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(bmv__uegra._getvalue(), is_error=tkirl__mtnhm)


def _get_array_item_arr_payload(context, builder, arr_typ, arr):
    bmv__uegra = context.make_helper(builder, arr_typ, arr)
    payload_type = ArrayItemArrayPayloadType(arr_typ)
    pebdy__cur = context.nrt.meminfo_data(builder, bmv__uegra.meminfo)
    sodw__kgbxt = builder.bitcast(pebdy__cur, context.get_value_type(
        payload_type).as_pointer())
    ryv__oundt = cgutils.create_struct_proxy(payload_type)(context, builder,
        builder.load(sodw__kgbxt))
    return ryv__oundt


def _box_array_item_array_generic(typ, c, n_arrays, data_arr, offsets_ptr,
    null_bitmap_ptr):
    context = c.context
    builder = c.builder
    nqg__ussqo = context.insert_const_string(builder.module, 'numpy')
    kndq__bpwl = c.pyapi.import_module_noblock(nqg__ussqo)
    ntrjo__bbnx = c.pyapi.object_getattr_string(kndq__bpwl, 'object_')
    xly__jlkqo = c.pyapi.long_from_longlong(n_arrays)
    crxwo__gwkh = c.pyapi.call_method(kndq__bpwl, 'ndarray', (xly__jlkqo,
        ntrjo__bbnx))
    bhapl__ogyo = c.pyapi.object_getattr_string(kndq__bpwl, 'nan')
    yhw__mykd = cgutils.alloca_once_value(builder, lir.Constant(lir.IntType
        (64), 0))
    with cgutils.for_range(builder, n_arrays) as wkhtn__hoadi:
        rruik__veopg = wkhtn__hoadi.index
        pyarray_setitem(builder, context, crxwo__gwkh, rruik__veopg,
            bhapl__ogyo)
        uzsob__lnsa = get_bitmap_bit(builder, null_bitmap_ptr, rruik__veopg)
        otcj__bbl = builder.icmp_unsigned('!=', uzsob__lnsa, lir.Constant(
            lir.IntType(8), 0))
        with builder.if_then(otcj__bbl):
            n_items = builder.sext(builder.sub(builder.load(builder.gep(
                offsets_ptr, [builder.add(rruik__veopg, lir.Constant(
                rruik__veopg.type, 1))])), builder.load(builder.gep(
                offsets_ptr, [rruik__veopg]))), lir.IntType(64))
            item_ind = builder.load(yhw__mykd)
            kmfgb__vno, hjq__acspz = c.pyapi.call_jit_code(lambda data_arr,
                item_ind, n_items: data_arr[item_ind:item_ind + n_items],
                typ.dtype(typ.dtype, types.int64, types.int64), [data_arr,
                item_ind, n_items])
            builder.store(builder.add(item_ind, n_items), yhw__mykd)
            arr_obj = c.pyapi.from_native_value(typ.dtype, hjq__acspz, c.
                env_manager)
            pyarray_setitem(builder, context, crxwo__gwkh, rruik__veopg,
                arr_obj)
            c.pyapi.decref(arr_obj)
    c.pyapi.decref(kndq__bpwl)
    c.pyapi.decref(ntrjo__bbnx)
    c.pyapi.decref(xly__jlkqo)
    c.pyapi.decref(bhapl__ogyo)
    return crxwo__gwkh


@box(ArrayItemArrayType)
def box_array_item_arr(typ, val, c):
    ryv__oundt = _get_array_item_arr_payload(c.context, c.builder, typ, val)
    data_arr = ryv__oundt.data
    offsets_ptr = c.context.make_helper(c.builder, types.Array(offset_type,
        1, 'C'), ryv__oundt.offsets).data
    null_bitmap_ptr = c.context.make_helper(c.builder, types.Array(types.
        uint8, 1, 'C'), ryv__oundt.null_bitmap).data
    if isinstance(typ.dtype, types.Array) and typ.dtype.dtype in (types.
        int64, types.float64, types.bool_, datetime_date_type):
        cdtg__xrt = bodo.utils.utils.numba_to_c_type(typ.dtype.dtype)
        saz__man = c.context.make_helper(c.builder, typ.dtype, data_arr).data
        yoqw__raopt = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(32)])
        fomjy__pqa = cgutils.get_or_insert_function(c.builder.module,
            yoqw__raopt, name='np_array_from_array_item_array')
        arr = c.builder.call(fomjy__pqa, [ryv__oundt.n_arrays, c.builder.
            bitcast(saz__man, lir.IntType(8).as_pointer()), offsets_ptr,
            null_bitmap_ptr, lir.Constant(lir.IntType(32), cdtg__xrt)])
    else:
        arr = _box_array_item_array_generic(typ, c, ryv__oundt.n_arrays,
            data_arr, offsets_ptr, null_bitmap_ptr)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def lower_pre_alloc_array_item_array(context, builder, sig, args):
    array_item_type = sig.return_type
    wtmt__knz, zxj__yvqn, ywkef__njhhq = args
    qfhs__yvp = bodo.utils.transform.get_type_alloc_counts(array_item_type.
        dtype)
    brnr__slhq = sig.args[1]
    if not isinstance(brnr__slhq, types.UniTuple):
        zxj__yvqn = cgutils.pack_array(builder, [lir.Constant(lir.IntType(
            64), -1) for ywkef__njhhq in range(qfhs__yvp)])
    elif brnr__slhq.count < qfhs__yvp:
        zxj__yvqn = cgutils.pack_array(builder, [builder.extract_value(
            zxj__yvqn, zkui__qrnxq) for zkui__qrnxq in range(brnr__slhq.
            count)] + [lir.Constant(lir.IntType(64), -1) for ywkef__njhhq in
            range(qfhs__yvp - brnr__slhq.count)])
    exk__sgv, ywkef__njhhq, ywkef__njhhq, ywkef__njhhq = (
        construct_array_item_array(context, builder, array_item_type,
        wtmt__knz, zxj__yvqn))
    bmv__uegra = context.make_helper(builder, array_item_type)
    bmv__uegra.meminfo = exk__sgv
    return bmv__uegra._getvalue()


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
    n_arrays, apf__uey, mshyl__fbnv, rde__attpo = args
    array_item_type = signature.return_type
    payload_type = ArrayItemArrayPayloadType(array_item_type)
    phtpy__rmbw = context.get_value_type(payload_type)
    fvz__yyiab = context.get_abi_sizeof(phtpy__rmbw)
    tqea__gtfx = define_array_item_dtor(context, builder, array_item_type,
        payload_type)
    exk__sgv = context.nrt.meminfo_alloc_dtor(builder, context.get_constant
        (types.uintp, fvz__yyiab), tqea__gtfx)
    pebdy__cur = context.nrt.meminfo_data(builder, exk__sgv)
    sodw__kgbxt = builder.bitcast(pebdy__cur, phtpy__rmbw.as_pointer())
    ryv__oundt = cgutils.create_struct_proxy(payload_type)(context, builder)
    ryv__oundt.n_arrays = n_arrays
    ryv__oundt.data = apf__uey
    ryv__oundt.offsets = mshyl__fbnv
    ryv__oundt.null_bitmap = rde__attpo
    builder.store(ryv__oundt._getvalue(), sodw__kgbxt)
    context.nrt.incref(builder, signature.args[1], apf__uey)
    context.nrt.incref(builder, signature.args[2], mshyl__fbnv)
    context.nrt.incref(builder, signature.args[3], rde__attpo)
    bmv__uegra = context.make_helper(builder, array_item_type)
    bmv__uegra.meminfo = exk__sgv
    return bmv__uegra._getvalue()


@intrinsic
def init_array_item_array(typingctx, n_arrays_typ, data_type, offsets_typ,
    null_bitmap_typ=None):
    assert null_bitmap_typ == types.Array(types.uint8, 1, 'C')
    aif__okxpu = ArrayItemArrayType(data_type)
    sig = aif__okxpu(types.int64, data_type, offsets_typ, null_bitmap_typ)
    return sig, init_array_item_array_codegen


@intrinsic
def get_offsets(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        ryv__oundt = _get_array_item_arr_payload(context, builder, arr_typ, arr
            )
        return impl_ret_borrowed(context, builder, sig.return_type,
            ryv__oundt.offsets)
    return types.Array(offset_type, 1, 'C')(arr_typ), codegen


@intrinsic
def get_offsets_ind(typingctx, arr_typ, ind_t=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, ind = args
        ryv__oundt = _get_array_item_arr_payload(context, builder, arr_typ, arr
            )
        saz__man = context.make_array(types.Array(offset_type, 1, 'C'))(context
            , builder, ryv__oundt.offsets).data
        mshyl__fbnv = builder.bitcast(saz__man, lir.IntType(offset_type.
            bitwidth).as_pointer())
        return builder.load(builder.gep(mshyl__fbnv, [ind]))
    return offset_type(arr_typ, types.int64), codegen


@intrinsic
def get_data(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        ryv__oundt = _get_array_item_arr_payload(context, builder, arr_typ, arr
            )
        return impl_ret_borrowed(context, builder, sig.return_type,
            ryv__oundt.data)
    return arr_typ.dtype(arr_typ), codegen


@intrinsic
def get_null_bitmap(typingctx, arr_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        ryv__oundt = _get_array_item_arr_payload(context, builder, arr_typ, arr
            )
        return impl_ret_borrowed(context, builder, sig.return_type,
            ryv__oundt.null_bitmap)
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
        ryv__oundt = _get_array_item_arr_payload(context, builder, arr_typ, arr
            )
        return ryv__oundt.n_arrays
    return types.int64(arr_typ), codegen


@intrinsic
def replace_data_arr(typingctx, arr_typ, data_typ=None):
    assert isinstance(arr_typ, ArrayItemArrayType
        ) and data_typ == arr_typ.dtype

    def codegen(context, builder, sig, args):
        arr, lat__ilp = args
        bmv__uegra = context.make_helper(builder, arr_typ, arr)
        payload_type = ArrayItemArrayPayloadType(arr_typ)
        pebdy__cur = context.nrt.meminfo_data(builder, bmv__uegra.meminfo)
        sodw__kgbxt = builder.bitcast(pebdy__cur, context.get_value_type(
            payload_type).as_pointer())
        ryv__oundt = cgutils.create_struct_proxy(payload_type)(context,
            builder, builder.load(sodw__kgbxt))
        context.nrt.decref(builder, data_typ, ryv__oundt.data)
        ryv__oundt.data = lat__ilp
        context.nrt.incref(builder, data_typ, lat__ilp)
        builder.store(ryv__oundt._getvalue(), sodw__kgbxt)
    return types.none(arr_typ, data_typ), codegen


@numba.njit(no_cpython_wrapper=True)
def ensure_data_capacity(arr, old_size, new_size):
    apf__uey = get_data(arr)
    dwrav__hghrp = len(apf__uey)
    if dwrav__hghrp < new_size:
        yzi__cxjtv = max(2 * dwrav__hghrp, new_size)
        lat__ilp = bodo.libs.array_kernels.resize_and_copy(apf__uey,
            old_size, yzi__cxjtv)
        replace_data_arr(arr, lat__ilp)


@numba.njit(no_cpython_wrapper=True)
def trim_excess_data(arr):
    apf__uey = get_data(arr)
    mshyl__fbnv = get_offsets(arr)
    kqtmk__bjfzp = len(apf__uey)
    nei__jcl = mshyl__fbnv[-1]
    if kqtmk__bjfzp != nei__jcl:
        lat__ilp = bodo.libs.array_kernels.resize_and_copy(apf__uey,
            nei__jcl, nei__jcl)
        replace_data_arr(arr, lat__ilp)


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
            mshyl__fbnv = get_offsets(arr)
            apf__uey = get_data(arr)
            qcrv__gcbdb = mshyl__fbnv[ind]
            kfk__cwky = mshyl__fbnv[ind + 1]
            return apf__uey[qcrv__gcbdb:kfk__cwky]
        return array_item_arr_getitem_impl
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        jvvao__ozast = arr.dtype

        def impl_bool(arr, ind):
            sjhr__hidb = len(arr)
            if sjhr__hidb != len(ind):
                raise IndexError(
                    'boolean index did not match indexed array along dimension 0'
                    )
            rde__attpo = get_null_bitmap(arr)
            n_arrays = 0
            wpu__ztkd = init_nested_counts(jvvao__ozast)
            for zkui__qrnxq in range(sjhr__hidb):
                if ind[zkui__qrnxq]:
                    n_arrays += 1
                    mykkv__oju = arr[zkui__qrnxq]
                    wpu__ztkd = add_nested_counts(wpu__ztkd, mykkv__oju)
            crxwo__gwkh = pre_alloc_array_item_array(n_arrays, wpu__ztkd,
                jvvao__ozast)
            utkxh__vol = get_null_bitmap(crxwo__gwkh)
            gdcqj__tztz = 0
            for rukck__qor in range(sjhr__hidb):
                if ind[rukck__qor]:
                    crxwo__gwkh[gdcqj__tztz] = arr[rukck__qor]
                    uuuqt__vvzvj = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                        rde__attpo, rukck__qor)
                    bodo.libs.int_arr_ext.set_bit_to_arr(utkxh__vol,
                        gdcqj__tztz, uuuqt__vvzvj)
                    gdcqj__tztz += 1
            return crxwo__gwkh
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        jvvao__ozast = arr.dtype

        def impl_int(arr, ind):
            rde__attpo = get_null_bitmap(arr)
            sjhr__hidb = len(ind)
            n_arrays = sjhr__hidb
            wpu__ztkd = init_nested_counts(jvvao__ozast)
            for mgn__you in range(sjhr__hidb):
                zkui__qrnxq = ind[mgn__you]
                mykkv__oju = arr[zkui__qrnxq]
                wpu__ztkd = add_nested_counts(wpu__ztkd, mykkv__oju)
            crxwo__gwkh = pre_alloc_array_item_array(n_arrays, wpu__ztkd,
                jvvao__ozast)
            utkxh__vol = get_null_bitmap(crxwo__gwkh)
            for zgmpu__mbchb in range(sjhr__hidb):
                rukck__qor = ind[zgmpu__mbchb]
                crxwo__gwkh[zgmpu__mbchb] = arr[rukck__qor]
                uuuqt__vvzvj = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                    rde__attpo, rukck__qor)
                bodo.libs.int_arr_ext.set_bit_to_arr(utkxh__vol,
                    zgmpu__mbchb, uuuqt__vvzvj)
            return crxwo__gwkh
        return impl_int
    if isinstance(ind, types.SliceType):

        def impl_slice(arr, ind):
            sjhr__hidb = len(arr)
            swv__cnut = numba.cpython.unicode._normalize_slice(ind, sjhr__hidb)
            snag__ctu = np.arange(swv__cnut.start, swv__cnut.stop,
                swv__cnut.step)
            return arr[snag__ctu]
        return impl_slice


@overload(operator.setitem)
def array_item_arr_setitem(A, idx, val):
    if not isinstance(A, ArrayItemArrayType):
        return
    if isinstance(idx, types.Integer):

        def impl_scalar(A, idx, val):
            mshyl__fbnv = get_offsets(A)
            rde__attpo = get_null_bitmap(A)
            if idx == 0:
                mshyl__fbnv[0] = 0
            n_items = len(val)
            frqo__pbftg = mshyl__fbnv[idx] + n_items
            ensure_data_capacity(A, mshyl__fbnv[idx], frqo__pbftg)
            apf__uey = get_data(A)
            mshyl__fbnv[idx + 1] = mshyl__fbnv[idx] + n_items
            apf__uey[mshyl__fbnv[idx]:mshyl__fbnv[idx + 1]] = val
            bodo.libs.int_arr_ext.set_bit_to_arr(rde__attpo, idx, 1)
        return impl_scalar
    if isinstance(idx, types.SliceType) and A.dtype == val:

        def impl_slice_elem(A, idx, val):
            swv__cnut = numba.cpython.unicode._normalize_slice(idx, len(A))
            for zkui__qrnxq in range(swv__cnut.start, swv__cnut.stop,
                swv__cnut.step):
                A[zkui__qrnxq] = val
        return impl_slice_elem
    if isinstance(idx, types.SliceType) and is_iterable_type(val):

        def impl_slice(A, idx, val):
            val = bodo.utils.conversion.coerce_to_array(val,
                use_nullable_array=True)
            mshyl__fbnv = get_offsets(A)
            rde__attpo = get_null_bitmap(A)
            iylwf__qwi = get_offsets(val)
            afwv__jezut = get_data(val)
            qwb__imz = get_null_bitmap(val)
            sjhr__hidb = len(A)
            swv__cnut = numba.cpython.unicode._normalize_slice(idx, sjhr__hidb)
            pxt__klz, botax__tmjvg = swv__cnut.start, swv__cnut.stop
            assert swv__cnut.step == 1
            if pxt__klz == 0:
                mshyl__fbnv[pxt__klz] = 0
            gqn__cccy = mshyl__fbnv[pxt__klz]
            frqo__pbftg = gqn__cccy + len(afwv__jezut)
            ensure_data_capacity(A, gqn__cccy, frqo__pbftg)
            apf__uey = get_data(A)
            apf__uey[gqn__cccy:gqn__cccy + len(afwv__jezut)] = afwv__jezut
            mshyl__fbnv[pxt__klz:botax__tmjvg + 1] = iylwf__qwi + gqn__cccy
            zmcq__yjf = 0
            for zkui__qrnxq in range(pxt__klz, botax__tmjvg):
                uuuqt__vvzvj = bodo.libs.int_arr_ext.get_bit_bitmap_arr(
                    qwb__imz, zmcq__yjf)
                bodo.libs.int_arr_ext.set_bit_to_arr(rde__attpo,
                    zkui__qrnxq, uuuqt__vvzvj)
                zmcq__yjf += 1
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
