"""Array implementation for structs of values.
Corresponds to Spark's StructType: https://spark.apache.org/docs/latest/sql-reference.html
Corresponds to Arrow's Struct arrays: https://arrow.apache.org/docs/format/Columnar.html

The values are stored in contiguous data arrays; one array per field. For example:
A:             ["AA", "B", "C"]
B:             [1, 2, 4]
"""
import operator
import llvmlite.binding as ll
import numpy as np
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import impl_ret_borrowed
from numba.extending import NativeValue, box, intrinsic, models, overload, overload_attribute, overload_method, register_model, unbox
from numba.parfors.array_analysis import ArrayAnalysis
from numba.typed.typedobjectutils import _cast
import bodo
from bodo.hiframes.datetime_date_ext import datetime_date_type
from bodo.libs import array_ext
from bodo.utils.cg_helpers import gen_allocate_array, get_array_elem_counts, get_bitmap_bit, is_na_value, pyarray_setitem, seq_getitem, set_bitmap_bit, to_arr_obj_if_list_obj
from bodo.utils.typing import BodoError, dtype_to_array_type, get_overload_const_int, get_overload_const_str, is_list_like_index_type, is_overload_constant_int, is_overload_constant_str, is_overload_none
ll.add_symbol('struct_array_from_sequence', array_ext.
    struct_array_from_sequence)
ll.add_symbol('np_array_from_struct_array', array_ext.
    np_array_from_struct_array)


class StructArrayType(types.ArrayCompatible):

    def __init__(self, data, names=None):
        assert isinstance(data, tuple) and len(data) > 0 and all(bodo.utils
            .utils.is_array_typ(umyv__ccrp, False) for umyv__ccrp in data)
        if names is not None:
            assert isinstance(names, tuple) and all(isinstance(umyv__ccrp,
                str) for umyv__ccrp in names) and len(names) == len(data)
        else:
            names = tuple('f{}'.format(i) for i in range(len(data)))
        self.data = data
        self.names = names
        super(StructArrayType, self).__init__(name=
            'StructArrayType({}, {})'.format(data, names))

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def dtype(self):
        return StructType(tuple(ugv__ptq.dtype for ugv__ptq in self.data),
            self.names)

    @classmethod
    def from_dict(cls, d):
        assert isinstance(d, dict)
        names = tuple(str(umyv__ccrp) for umyv__ccrp in d.keys())
        data = tuple(dtype_to_array_type(ugv__ptq) for ugv__ptq in d.values())
        return StructArrayType(data, names)

    def copy(self):
        return StructArrayType(self.data, self.names)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


class StructArrayPayloadType(types.Type):

    def __init__(self, data):
        assert isinstance(data, tuple) and all(bodo.utils.utils.
            is_array_typ(umyv__ccrp, False) for umyv__ccrp in data)
        self.data = data
        super(StructArrayPayloadType, self).__init__(name=
            'StructArrayPayloadType({})'.format(data))

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(StructArrayPayloadType)
class StructArrayPayloadModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        yrp__nhnyr = [('data', types.BaseTuple.from_types(fe_type.data)), (
            'null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, yrp__nhnyr)


@register_model(StructArrayType)
class StructArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = StructArrayPayloadType(fe_type.data)
        yrp__nhnyr = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, yrp__nhnyr)


def define_struct_arr_dtor(context, builder, struct_arr_type, payload_type):
    fjpd__oaag = builder.module
    rir__dxb = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    vserk__lsy = cgutils.get_or_insert_function(fjpd__oaag, rir__dxb, name=
        '.dtor.struct_arr.{}.{}.'.format(struct_arr_type.data,
        struct_arr_type.names))
    if not vserk__lsy.is_declaration:
        return vserk__lsy
    vserk__lsy.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(vserk__lsy.append_basic_block())
    szi__vhh = vserk__lsy.args[0]
    nxmr__wha = context.get_value_type(payload_type).as_pointer()
    qxlb__kyqlq = builder.bitcast(szi__vhh, nxmr__wha)
    zcl__omsqe = context.make_helper(builder, payload_type, ref=qxlb__kyqlq)
    context.nrt.decref(builder, types.BaseTuple.from_types(struct_arr_type.
        data), zcl__omsqe.data)
    context.nrt.decref(builder, types.Array(types.uint8, 1, 'C'),
        zcl__omsqe.null_bitmap)
    builder.ret_void()
    return vserk__lsy


def construct_struct_array(context, builder, struct_arr_type, n_structs,
    n_elems, c=None):
    payload_type = StructArrayPayloadType(struct_arr_type.data)
    fhq__axozt = context.get_value_type(payload_type)
    gfxq__ulw = context.get_abi_sizeof(fhq__axozt)
    gzhtq__bxn = define_struct_arr_dtor(context, builder, struct_arr_type,
        payload_type)
    xlnd__vdpz = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, gfxq__ulw), gzhtq__bxn)
    nrjoy__yrh = context.nrt.meminfo_data(builder, xlnd__vdpz)
    nhdj__fvf = builder.bitcast(nrjoy__yrh, fhq__axozt.as_pointer())
    zcl__omsqe = cgutils.create_struct_proxy(payload_type)(context, builder)
    pupxr__msdg = []
    nug__cic = 0
    for arr_typ in struct_arr_type.data:
        eitgh__blkb = bodo.utils.transform.get_type_alloc_counts(arr_typ.dtype)
        pkmsv__wjly = cgutils.pack_array(builder, [n_structs] + [builder.
            extract_value(n_elems, i) for i in range(nug__cic, nug__cic +
            eitgh__blkb)])
        arr = gen_allocate_array(context, builder, arr_typ, pkmsv__wjly, c)
        pupxr__msdg.append(arr)
        nug__cic += eitgh__blkb
    zcl__omsqe.data = cgutils.pack_array(builder, pupxr__msdg
        ) if types.is_homogeneous(*struct_arr_type.data
        ) else cgutils.pack_struct(builder, pupxr__msdg)
    lyh__tsrt = builder.udiv(builder.add(n_structs, lir.Constant(lir.
        IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
    lemjy__oueqy = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(types.uint8, 1, 'C'), [lyh__tsrt])
    null_bitmap_ptr = lemjy__oueqy.data
    zcl__omsqe.null_bitmap = lemjy__oueqy._getvalue()
    builder.store(zcl__omsqe._getvalue(), nhdj__fvf)
    return xlnd__vdpz, zcl__omsqe.data, null_bitmap_ptr


def _get_C_API_ptrs(c, data_tup, data_typ, names):
    imphc__ofeqc = []
    assert len(data_typ) > 0
    for i, arr_typ in enumerate(data_typ):
        biko__wble = c.builder.extract_value(data_tup, i)
        arr = c.context.make_array(arr_typ)(c.context, c.builder, value=
            biko__wble)
        imphc__ofeqc.append(arr.data)
    osh__sdgdp = cgutils.pack_array(c.builder, imphc__ofeqc
        ) if types.is_homogeneous(*data_typ) else cgutils.pack_struct(c.
        builder, imphc__ofeqc)
    hkfrf__rxf = cgutils.alloca_once_value(c.builder, osh__sdgdp)
    lpp__exf = [c.context.get_constant(types.int32, bodo.utils.utils.
        numba_to_c_type(umyv__ccrp.dtype)) for umyv__ccrp in data_typ]
    aslr__wsqec = cgutils.alloca_once_value(c.builder, cgutils.pack_array(c
        .builder, lpp__exf))
    wqlau__nqb = cgutils.pack_array(c.builder, [c.context.
        insert_const_string(c.builder.module, umyv__ccrp) for umyv__ccrp in
        names])
    vfov__uvw = cgutils.alloca_once_value(c.builder, wqlau__nqb)
    return hkfrf__rxf, aslr__wsqec, vfov__uvw


@unbox(StructArrayType)
def unbox_struct_array(typ, val, c, is_tuple_array=False):
    from bodo.libs.tuple_arr_ext import TupleArrayType
    n_structs = bodo.utils.utils.object_length(c, val)
    xvmxq__mftr = all(isinstance(ugv__ptq, types.Array) and ugv__ptq.dtype in
        (types.int64, types.float64, types.bool_, datetime_date_type) for
        ugv__ptq in typ.data)
    if xvmxq__mftr:
        n_elems = cgutils.pack_array(c.builder, [], lir.IntType(64))
    else:
        kbdw__kojg = get_array_elem_counts(c, c.builder, c.context, val, 
            TupleArrayType(typ.data) if is_tuple_array else typ)
        n_elems = cgutils.pack_array(c.builder, [c.builder.extract_value(
            kbdw__kojg, i) for i in range(1, kbdw__kojg.type.count)], lir.
            IntType(64))
    xlnd__vdpz, data_tup, null_bitmap_ptr = construct_struct_array(c.
        context, c.builder, typ, n_structs, n_elems, c)
    if xvmxq__mftr:
        hkfrf__rxf, aslr__wsqec, vfov__uvw = _get_C_API_ptrs(c, data_tup,
            typ.data, typ.names)
        rir__dxb = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(32), lir.IntType(8).as_pointer(), lir
            .IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1)])
        vserk__lsy = cgutils.get_or_insert_function(c.builder.module,
            rir__dxb, name='struct_array_from_sequence')
        c.builder.call(vserk__lsy, [val, c.context.get_constant(types.int32,
            len(typ.data)), c.builder.bitcast(hkfrf__rxf, lir.IntType(8).
            as_pointer()), null_bitmap_ptr, c.builder.bitcast(aslr__wsqec,
            lir.IntType(8).as_pointer()), c.builder.bitcast(vfov__uvw, lir.
            IntType(8).as_pointer()), c.context.get_constant(types.bool_,
            is_tuple_array)])
    else:
        _unbox_struct_array_generic(typ, val, c, n_structs, data_tup,
            null_bitmap_ptr, is_tuple_array)
    wvtu__huxba = c.context.make_helper(c.builder, typ)
    wvtu__huxba.meminfo = xlnd__vdpz
    rpmy__pmqa = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(wvtu__huxba._getvalue(), is_error=rpmy__pmqa)


def _unbox_struct_array_generic(typ, val, c, n_structs, data_tup,
    null_bitmap_ptr, is_tuple_array=False):
    context = c.context
    builder = c.builder
    jytfq__dzvp = context.insert_const_string(builder.module, 'pandas')
    hrk__rcds = c.pyapi.import_module_noblock(jytfq__dzvp)
    achq__nwv = c.pyapi.object_getattr_string(hrk__rcds, 'NA')
    with cgutils.for_range(builder, n_structs) as nlhzh__moujr:
        qilm__vcxlt = nlhzh__moujr.index
        miqaj__tleo = seq_getitem(builder, context, val, qilm__vcxlt)
        set_bitmap_bit(builder, null_bitmap_ptr, qilm__vcxlt, 0)
        for lmpvj__zxy in range(len(typ.data)):
            arr_typ = typ.data[lmpvj__zxy]
            data_arr = builder.extract_value(data_tup, lmpvj__zxy)

            def set_na(data_arr, i):
                bodo.libs.array_kernels.setna(data_arr, i)
            sig = types.none(arr_typ, types.int64)
            yaxc__jsaf, anb__xlp = c.pyapi.call_jit_code(set_na, sig, [
                data_arr, qilm__vcxlt])
        lah__fsqnv = is_na_value(builder, context, miqaj__tleo, achq__nwv)
        lfvh__jvzaw = builder.icmp_unsigned('!=', lah__fsqnv, lir.Constant(
            lah__fsqnv.type, 1))
        with builder.if_then(lfvh__jvzaw):
            set_bitmap_bit(builder, null_bitmap_ptr, qilm__vcxlt, 1)
            for lmpvj__zxy in range(len(typ.data)):
                arr_typ = typ.data[lmpvj__zxy]
                if is_tuple_array:
                    tex__nbncx = c.pyapi.tuple_getitem(miqaj__tleo, lmpvj__zxy)
                else:
                    tex__nbncx = c.pyapi.dict_getitem_string(miqaj__tleo,
                        typ.names[lmpvj__zxy])
                lah__fsqnv = is_na_value(builder, context, tex__nbncx,
                    achq__nwv)
                lfvh__jvzaw = builder.icmp_unsigned('!=', lah__fsqnv, lir.
                    Constant(lah__fsqnv.type, 1))
                with builder.if_then(lfvh__jvzaw):
                    tex__nbncx = to_arr_obj_if_list_obj(c, context, builder,
                        tex__nbncx, arr_typ.dtype)
                    field_val = c.pyapi.to_native_value(arr_typ.dtype,
                        tex__nbncx).value
                    data_arr = builder.extract_value(data_tup, lmpvj__zxy)

                    def set_data(data_arr, i, field_val):
                        data_arr[i] = field_val
                    sig = types.none(arr_typ, types.int64, arr_typ.dtype)
                    yaxc__jsaf, anb__xlp = c.pyapi.call_jit_code(set_data,
                        sig, [data_arr, qilm__vcxlt, field_val])
                    c.context.nrt.decref(builder, arr_typ.dtype, field_val)
        c.pyapi.decref(miqaj__tleo)
    c.pyapi.decref(hrk__rcds)
    c.pyapi.decref(achq__nwv)


def _get_struct_arr_payload(context, builder, arr_typ, arr):
    wvtu__huxba = context.make_helper(builder, arr_typ, arr)
    payload_type = StructArrayPayloadType(arr_typ.data)
    nrjoy__yrh = context.nrt.meminfo_data(builder, wvtu__huxba.meminfo)
    nhdj__fvf = builder.bitcast(nrjoy__yrh, context.get_value_type(
        payload_type).as_pointer())
    zcl__omsqe = cgutils.create_struct_proxy(payload_type)(context, builder,
        builder.load(nhdj__fvf))
    return zcl__omsqe


@box(StructArrayType)
def box_struct_arr(typ, val, c, is_tuple_array=False):
    zcl__omsqe = _get_struct_arr_payload(c.context, c.builder, typ, val)
    yaxc__jsaf, length = c.pyapi.call_jit_code(lambda A: len(A), types.
        int64(typ), [val])
    null_bitmap_ptr = c.context.make_helper(c.builder, types.Array(types.
        uint8, 1, 'C'), zcl__omsqe.null_bitmap).data
    xvmxq__mftr = all(isinstance(ugv__ptq, types.Array) and ugv__ptq.dtype in
        (types.int64, types.float64, types.bool_, datetime_date_type) for
        ugv__ptq in typ.data)
    if xvmxq__mftr:
        hkfrf__rxf, aslr__wsqec, vfov__uvw = _get_C_API_ptrs(c, zcl__omsqe.
            data, typ.data, typ.names)
        rir__dxb = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(32), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1)])
        xzpdn__mlu = cgutils.get_or_insert_function(c.builder.module,
            rir__dxb, name='np_array_from_struct_array')
        arr = c.builder.call(xzpdn__mlu, [length, c.context.get_constant(
            types.int32, len(typ.data)), c.builder.bitcast(hkfrf__rxf, lir.
            IntType(8).as_pointer()), null_bitmap_ptr, c.builder.bitcast(
            aslr__wsqec, lir.IntType(8).as_pointer()), c.builder.bitcast(
            vfov__uvw, lir.IntType(8).as_pointer()), c.context.get_constant
            (types.bool_, is_tuple_array)])
    else:
        arr = _box_struct_array_generic(typ, c, length, zcl__omsqe.data,
            null_bitmap_ptr, is_tuple_array)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def _box_struct_array_generic(typ, c, length, data_arrs_tup,
    null_bitmap_ptr, is_tuple_array=False):
    context = c.context
    builder = c.builder
    jytfq__dzvp = context.insert_const_string(builder.module, 'numpy')
    xkjb__bnocu = c.pyapi.import_module_noblock(jytfq__dzvp)
    zfvt__tslx = c.pyapi.object_getattr_string(xkjb__bnocu, 'object_')
    xsun__vqcf = c.pyapi.long_from_longlong(length)
    pdvvg__ozt = c.pyapi.call_method(xkjb__bnocu, 'ndarray', (xsun__vqcf,
        zfvt__tslx))
    fkzkc__yjro = c.pyapi.object_getattr_string(xkjb__bnocu, 'nan')
    with cgutils.for_range(builder, length) as nlhzh__moujr:
        qilm__vcxlt = nlhzh__moujr.index
        pyarray_setitem(builder, context, pdvvg__ozt, qilm__vcxlt, fkzkc__yjro)
        vkfb__uufph = get_bitmap_bit(builder, null_bitmap_ptr, qilm__vcxlt)
        dymrq__rheid = builder.icmp_unsigned('!=', vkfb__uufph, lir.
            Constant(lir.IntType(8), 0))
        with builder.if_then(dymrq__rheid):
            if is_tuple_array:
                miqaj__tleo = c.pyapi.tuple_new(len(typ.data))
            else:
                miqaj__tleo = c.pyapi.dict_new(len(typ.data))
            for i, arr_typ in enumerate(typ.data):
                if is_tuple_array:
                    c.pyapi.incref(fkzkc__yjro)
                    c.pyapi.tuple_setitem(miqaj__tleo, i, fkzkc__yjro)
                else:
                    c.pyapi.dict_setitem_string(miqaj__tleo, typ.names[i],
                        fkzkc__yjro)
                data_arr = c.builder.extract_value(data_arrs_tup, i)
                yaxc__jsaf, iikvw__ijmli = c.pyapi.call_jit_code(lambda
                    data_arr, ind: not bodo.libs.array_kernels.isna(
                    data_arr, ind), types.bool_(arr_typ, types.int64), [
                    data_arr, qilm__vcxlt])
                with builder.if_then(iikvw__ijmli):
                    yaxc__jsaf, field_val = c.pyapi.call_jit_code(lambda
                        data_arr, ind: data_arr[ind], arr_typ.dtype(arr_typ,
                        types.int64), [data_arr, qilm__vcxlt])
                    mywqi__kvjpo = c.pyapi.from_native_value(arr_typ.dtype,
                        field_val, c.env_manager)
                    if is_tuple_array:
                        c.pyapi.tuple_setitem(miqaj__tleo, i, mywqi__kvjpo)
                    else:
                        c.pyapi.dict_setitem_string(miqaj__tleo, typ.names[
                            i], mywqi__kvjpo)
                        c.pyapi.decref(mywqi__kvjpo)
            pyarray_setitem(builder, context, pdvvg__ozt, qilm__vcxlt,
                miqaj__tleo)
            c.pyapi.decref(miqaj__tleo)
    c.pyapi.decref(xkjb__bnocu)
    c.pyapi.decref(zfvt__tslx)
    c.pyapi.decref(xsun__vqcf)
    c.pyapi.decref(fkzkc__yjro)
    return pdvvg__ozt


def _fix_nested_counts(nested_counts, struct_arr_type, nested_counts_type,
    builder):
    nbvx__vvu = bodo.utils.transform.get_type_alloc_counts(struct_arr_type) - 1
    if nbvx__vvu == 0:
        return nested_counts
    if not isinstance(nested_counts_type, types.UniTuple):
        nested_counts = cgutils.pack_array(builder, [lir.Constant(lir.
            IntType(64), -1) for fqdk__ddgpe in range(nbvx__vvu)])
    elif nested_counts_type.count < nbvx__vvu:
        nested_counts = cgutils.pack_array(builder, [builder.extract_value(
            nested_counts, i) for i in range(nested_counts_type.count)] + [
            lir.Constant(lir.IntType(64), -1) for fqdk__ddgpe in range(
            nbvx__vvu - nested_counts_type.count)])
    return nested_counts


@intrinsic
def pre_alloc_struct_array(typingctx, num_structs_typ, nested_counts_typ,
    dtypes_typ, names_typ=None):
    assert isinstance(num_structs_typ, types.Integer) and isinstance(dtypes_typ
        , types.BaseTuple)
    if is_overload_none(names_typ):
        names = tuple(f'f{i}' for i in range(len(dtypes_typ)))
    else:
        names = tuple(get_overload_const_str(ugv__ptq) for ugv__ptq in
            names_typ.types)
    rhx__ddbmr = tuple(ugv__ptq.instance_type for ugv__ptq in dtypes_typ.types)
    struct_arr_type = StructArrayType(rhx__ddbmr, names)

    def codegen(context, builder, sig, args):
        ewe__fszty, nested_counts, fqdk__ddgpe, fqdk__ddgpe = args
        nested_counts_type = sig.args[1]
        nested_counts = _fix_nested_counts(nested_counts, struct_arr_type,
            nested_counts_type, builder)
        xlnd__vdpz, fqdk__ddgpe, fqdk__ddgpe = construct_struct_array(context,
            builder, struct_arr_type, ewe__fszty, nested_counts)
        wvtu__huxba = context.make_helper(builder, struct_arr_type)
        wvtu__huxba.meminfo = xlnd__vdpz
        return wvtu__huxba._getvalue()
    return struct_arr_type(num_structs_typ, nested_counts_typ, dtypes_typ,
        names_typ), codegen


def pre_alloc_struct_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 4 and not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


(ArrayAnalysis._analyze_op_call_bodo_libs_struct_arr_ext_pre_alloc_struct_array
    ) = pre_alloc_struct_array_equiv


class StructType(types.Type):

    def __init__(self, data, names):
        assert isinstance(data, tuple) and len(data) > 0
        assert isinstance(names, tuple) and all(isinstance(umyv__ccrp, str) for
            umyv__ccrp in names) and len(names) == len(data)
        self.data = data
        self.names = names
        super(StructType, self).__init__(name='StructType({}, {})'.format(
            data, names))

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


class StructPayloadType(types.Type):

    def __init__(self, data):
        assert isinstance(data, tuple)
        self.data = data
        super(StructPayloadType, self).__init__(name=
            'StructPayloadType({})'.format(data))

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(StructPayloadType)
class StructPayloadModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        yrp__nhnyr = [('data', types.BaseTuple.from_types(fe_type.data)), (
            'null_bitmap', types.UniTuple(types.int8, len(fe_type.data)))]
        models.StructModel.__init__(self, dmm, fe_type, yrp__nhnyr)


@register_model(StructType)
class StructModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = StructPayloadType(fe_type.data)
        yrp__nhnyr = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, yrp__nhnyr)


def define_struct_dtor(context, builder, struct_type, payload_type):
    fjpd__oaag = builder.module
    rir__dxb = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    vserk__lsy = cgutils.get_or_insert_function(fjpd__oaag, rir__dxb, name=
        '.dtor.struct.{}.{}.'.format(struct_type.data, struct_type.names))
    if not vserk__lsy.is_declaration:
        return vserk__lsy
    vserk__lsy.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(vserk__lsy.append_basic_block())
    szi__vhh = vserk__lsy.args[0]
    nxmr__wha = context.get_value_type(payload_type).as_pointer()
    qxlb__kyqlq = builder.bitcast(szi__vhh, nxmr__wha)
    zcl__omsqe = context.make_helper(builder, payload_type, ref=qxlb__kyqlq)
    for i in range(len(struct_type.data)):
        juk__tagdx = builder.extract_value(zcl__omsqe.null_bitmap, i)
        dymrq__rheid = builder.icmp_unsigned('==', juk__tagdx, lir.Constant
            (juk__tagdx.type, 1))
        with builder.if_then(dymrq__rheid):
            val = builder.extract_value(zcl__omsqe.data, i)
            context.nrt.decref(builder, struct_type.data[i], val)
    builder.ret_void()
    return vserk__lsy


def _get_struct_payload(context, builder, typ, struct):
    struct = context.make_helper(builder, typ, struct)
    payload_type = StructPayloadType(typ.data)
    nrjoy__yrh = context.nrt.meminfo_data(builder, struct.meminfo)
    nhdj__fvf = builder.bitcast(nrjoy__yrh, context.get_value_type(
        payload_type).as_pointer())
    zcl__omsqe = cgutils.create_struct_proxy(payload_type)(context, builder,
        builder.load(nhdj__fvf))
    return zcl__omsqe, nhdj__fvf


@unbox(StructType)
def unbox_struct(typ, val, c):
    context = c.context
    builder = c.builder
    jytfq__dzvp = context.insert_const_string(builder.module, 'pandas')
    hrk__rcds = c.pyapi.import_module_noblock(jytfq__dzvp)
    achq__nwv = c.pyapi.object_getattr_string(hrk__rcds, 'NA')
    tyrg__yehk = []
    nulls = []
    for i, ugv__ptq in enumerate(typ.data):
        mywqi__kvjpo = c.pyapi.dict_getitem_string(val, typ.names[i])
        lkdn__bzjpv = cgutils.alloca_once_value(c.builder, context.
            get_constant(types.uint8, 0))
        wuws__tmx = cgutils.alloca_once_value(c.builder, cgutils.
            get_null_value(context.get_value_type(ugv__ptq)))
        lah__fsqnv = is_na_value(builder, context, mywqi__kvjpo, achq__nwv)
        dymrq__rheid = builder.icmp_unsigned('!=', lah__fsqnv, lir.Constant
            (lah__fsqnv.type, 1))
        with builder.if_then(dymrq__rheid):
            builder.store(context.get_constant(types.uint8, 1), lkdn__bzjpv)
            field_val = c.pyapi.to_native_value(ugv__ptq, mywqi__kvjpo).value
            builder.store(field_val, wuws__tmx)
        tyrg__yehk.append(builder.load(wuws__tmx))
        nulls.append(builder.load(lkdn__bzjpv))
    c.pyapi.decref(hrk__rcds)
    c.pyapi.decref(achq__nwv)
    xlnd__vdpz = construct_struct(context, builder, typ, tyrg__yehk, nulls)
    struct = context.make_helper(builder, typ)
    struct.meminfo = xlnd__vdpz
    rpmy__pmqa = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(struct._getvalue(), is_error=rpmy__pmqa)


@box(StructType)
def box_struct(typ, val, c):
    cno__rgv = c.pyapi.dict_new(len(typ.data))
    zcl__omsqe, fqdk__ddgpe = _get_struct_payload(c.context, c.builder, typ,
        val)
    assert len(typ.data) > 0
    for i, val_typ in enumerate(typ.data):
        c.pyapi.dict_setitem_string(cno__rgv, typ.names[i], c.pyapi.
            borrow_none())
        juk__tagdx = c.builder.extract_value(zcl__omsqe.null_bitmap, i)
        dymrq__rheid = c.builder.icmp_unsigned('==', juk__tagdx, lir.
            Constant(juk__tagdx.type, 1))
        with c.builder.if_then(dymrq__rheid):
            jqwmw__nwm = c.builder.extract_value(zcl__omsqe.data, i)
            c.context.nrt.incref(c.builder, val_typ, jqwmw__nwm)
            tex__nbncx = c.pyapi.from_native_value(val_typ, jqwmw__nwm, c.
                env_manager)
            c.pyapi.dict_setitem_string(cno__rgv, typ.names[i], tex__nbncx)
            c.pyapi.decref(tex__nbncx)
    c.context.nrt.decref(c.builder, typ, val)
    return cno__rgv


@intrinsic
def init_struct(typingctx, data_typ, names_typ=None):
    names = tuple(get_overload_const_str(ugv__ptq) for ugv__ptq in
        names_typ.types)
    struct_type = StructType(data_typ.types, names)

    def codegen(context, builder, sig, args):
        data, tac__kok = args
        payload_type = StructPayloadType(struct_type.data)
        fhq__axozt = context.get_value_type(payload_type)
        gfxq__ulw = context.get_abi_sizeof(fhq__axozt)
        gzhtq__bxn = define_struct_dtor(context, builder, struct_type,
            payload_type)
        xlnd__vdpz = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, gfxq__ulw), gzhtq__bxn)
        nrjoy__yrh = context.nrt.meminfo_data(builder, xlnd__vdpz)
        nhdj__fvf = builder.bitcast(nrjoy__yrh, fhq__axozt.as_pointer())
        zcl__omsqe = cgutils.create_struct_proxy(payload_type)(context, builder
            )
        zcl__omsqe.data = data
        zcl__omsqe.null_bitmap = cgutils.pack_array(builder, [context.
            get_constant(types.uint8, 1) for fqdk__ddgpe in range(len(
            data_typ.types))])
        builder.store(zcl__omsqe._getvalue(), nhdj__fvf)
        context.nrt.incref(builder, data_typ, data)
        struct = context.make_helper(builder, struct_type)
        struct.meminfo = xlnd__vdpz
        return struct._getvalue()
    return struct_type(data_typ, names_typ), codegen


@intrinsic
def get_struct_data(typingctx, struct_typ=None):
    assert isinstance(struct_typ, StructType)

    def codegen(context, builder, sig, args):
        struct, = args
        zcl__omsqe, fqdk__ddgpe = _get_struct_payload(context, builder,
            struct_typ, struct)
        return impl_ret_borrowed(context, builder, sig.return_type,
            zcl__omsqe.data)
    return types.BaseTuple.from_types(struct_typ.data)(struct_typ), codegen


@intrinsic
def get_struct_null_bitmap(typingctx, struct_typ=None):
    assert isinstance(struct_typ, StructType)

    def codegen(context, builder, sig, args):
        struct, = args
        zcl__omsqe, fqdk__ddgpe = _get_struct_payload(context, builder,
            struct_typ, struct)
        return impl_ret_borrowed(context, builder, sig.return_type,
            zcl__omsqe.null_bitmap)
    mhk__nwznn = types.UniTuple(types.int8, len(struct_typ.data))
    return mhk__nwznn(struct_typ), codegen


@intrinsic
def set_struct_data(typingctx, struct_typ, field_ind_typ, val_typ=None):
    assert isinstance(struct_typ, StructType) and is_overload_constant_int(
        field_ind_typ)
    field_ind = get_overload_const_int(field_ind_typ)

    def codegen(context, builder, sig, args):
        struct, fqdk__ddgpe, val = args
        zcl__omsqe, nhdj__fvf = _get_struct_payload(context, builder,
            struct_typ, struct)
        dfyf__tdht = zcl__omsqe.data
        ugsw__uvf = builder.insert_value(dfyf__tdht, val, field_ind)
        vokb__wvv = types.BaseTuple.from_types(struct_typ.data)
        context.nrt.decref(builder, vokb__wvv, dfyf__tdht)
        context.nrt.incref(builder, vokb__wvv, ugsw__uvf)
        zcl__omsqe.data = ugsw__uvf
        builder.store(zcl__omsqe._getvalue(), nhdj__fvf)
        return context.get_dummy_value()
    return types.none(struct_typ, field_ind_typ, val_typ), codegen


def _get_struct_field_ind(struct, ind, op):
    if not is_overload_constant_str(ind):
        raise BodoError(
            'structs (from struct array) only support constant strings for {}, not {}'
            .format(op, ind))
    dwc__zqjsd = get_overload_const_str(ind)
    if dwc__zqjsd not in struct.names:
        raise BodoError('Field {} does not exist in struct {}'.format(
            dwc__zqjsd, struct))
    return struct.names.index(dwc__zqjsd)


def is_field_value_null(s, field_name):
    pass


@overload(is_field_value_null, no_unliteral=True)
def overload_is_field_value_null(s, field_name):
    field_ind = _get_struct_field_ind(s, field_name, 'element access (getitem)'
        )
    return lambda s, field_name: get_struct_null_bitmap(s)[field_ind] == 0


@overload(operator.getitem, no_unliteral=True)
def struct_getitem(struct, ind):
    if not isinstance(struct, StructType):
        return
    field_ind = _get_struct_field_ind(struct, ind, 'element access (getitem)')
    return lambda struct, ind: get_struct_data(struct)[field_ind]


@overload(operator.setitem, no_unliteral=True)
def struct_setitem(struct, ind, val):
    if not isinstance(struct, StructType):
        return
    field_ind = _get_struct_field_ind(struct, ind, 'item assignment (setitem)')
    field_typ = struct.data[field_ind]
    return lambda struct, ind, val: set_struct_data(struct, field_ind,
        _cast(val, field_typ))


@overload(len, no_unliteral=True)
def overload_struct_arr_len(struct):
    if isinstance(struct, StructType):
        num_fields = len(struct.data)
        return lambda struct: num_fields


def construct_struct(context, builder, struct_type, values, nulls):
    payload_type = StructPayloadType(struct_type.data)
    fhq__axozt = context.get_value_type(payload_type)
    gfxq__ulw = context.get_abi_sizeof(fhq__axozt)
    gzhtq__bxn = define_struct_dtor(context, builder, struct_type, payload_type
        )
    xlnd__vdpz = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, gfxq__ulw), gzhtq__bxn)
    nrjoy__yrh = context.nrt.meminfo_data(builder, xlnd__vdpz)
    nhdj__fvf = builder.bitcast(nrjoy__yrh, fhq__axozt.as_pointer())
    zcl__omsqe = cgutils.create_struct_proxy(payload_type)(context, builder)
    zcl__omsqe.data = cgutils.pack_array(builder, values
        ) if types.is_homogeneous(*struct_type.data) else cgutils.pack_struct(
        builder, values)
    zcl__omsqe.null_bitmap = cgutils.pack_array(builder, nulls)
    builder.store(zcl__omsqe._getvalue(), nhdj__fvf)
    return xlnd__vdpz


@intrinsic
def struct_array_get_struct(typingctx, struct_arr_typ, ind_typ=None):
    assert isinstance(struct_arr_typ, StructArrayType) and isinstance(ind_typ,
        types.Integer)
    jfczz__thsd = tuple(d.dtype for d in struct_arr_typ.data)
    yrma__ievzh = StructType(jfczz__thsd, struct_arr_typ.names)

    def codegen(context, builder, sig, args):
        uvx__mcd, ind = args
        zcl__omsqe = _get_struct_arr_payload(context, builder,
            struct_arr_typ, uvx__mcd)
        tyrg__yehk = []
        hiym__xas = []
        for i, arr_typ in enumerate(struct_arr_typ.data):
            biko__wble = builder.extract_value(zcl__omsqe.data, i)
            xurih__bys = context.compile_internal(builder, lambda arr, ind:
                np.uint8(0) if bodo.libs.array_kernels.isna(arr, ind) else
                np.uint8(1), types.uint8(arr_typ, types.int64), [biko__wble,
                ind])
            hiym__xas.append(xurih__bys)
            xda__lexid = cgutils.alloca_once_value(builder, context.
                get_constant_null(arr_typ.dtype))
            dymrq__rheid = builder.icmp_unsigned('==', xurih__bys, lir.
                Constant(xurih__bys.type, 1))
            with builder.if_then(dymrq__rheid):
                uldoq__fryqd = context.compile_internal(builder, lambda arr,
                    ind: arr[ind], arr_typ.dtype(arr_typ, types.int64), [
                    biko__wble, ind])
                builder.store(uldoq__fryqd, xda__lexid)
            tyrg__yehk.append(builder.load(xda__lexid))
        if isinstance(yrma__ievzh, types.DictType):
            wtu__lzoj = [context.insert_const_string(builder.module,
                hiz__ncxmk) for hiz__ncxmk in struct_arr_typ.names]
            nzxl__hvkfs = cgutils.pack_array(builder, tyrg__yehk)
            rpp__qsfw = cgutils.pack_array(builder, wtu__lzoj)

            def impl(names, vals):
                d = {}
                for i, hiz__ncxmk in enumerate(names):
                    d[hiz__ncxmk] = vals[i]
                return d
            bzsb__pvl = context.compile_internal(builder, impl, yrma__ievzh
                (types.Tuple(tuple(types.StringLiteral(hiz__ncxmk) for
                hiz__ncxmk in struct_arr_typ.names)), types.Tuple(
                jfczz__thsd)), [rpp__qsfw, nzxl__hvkfs])
            context.nrt.decref(builder, types.BaseTuple.from_types(
                jfczz__thsd), nzxl__hvkfs)
            return bzsb__pvl
        xlnd__vdpz = construct_struct(context, builder, yrma__ievzh,
            tyrg__yehk, hiym__xas)
        struct = context.make_helper(builder, yrma__ievzh)
        struct.meminfo = xlnd__vdpz
        return struct._getvalue()
    return yrma__ievzh(struct_arr_typ, ind_typ), codegen


@intrinsic
def get_data(typingctx, arr_typ=None):
    assert isinstance(arr_typ, StructArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        zcl__omsqe = _get_struct_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            zcl__omsqe.data)
    return types.BaseTuple.from_types(arr_typ.data)(arr_typ), codegen


@intrinsic
def get_null_bitmap(typingctx, arr_typ=None):
    assert isinstance(arr_typ, StructArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        zcl__omsqe = _get_struct_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            zcl__omsqe.null_bitmap)
    return types.Array(types.uint8, 1, 'C')(arr_typ), codegen


@intrinsic
def init_struct_arr(typingctx, data_typ, null_bitmap_typ, names_typ=None):
    names = tuple(get_overload_const_str(ugv__ptq) for ugv__ptq in
        names_typ.types)
    struct_arr_type = StructArrayType(data_typ.types, names)

    def codegen(context, builder, sig, args):
        data, lemjy__oueqy, tac__kok = args
        payload_type = StructArrayPayloadType(struct_arr_type.data)
        fhq__axozt = context.get_value_type(payload_type)
        gfxq__ulw = context.get_abi_sizeof(fhq__axozt)
        gzhtq__bxn = define_struct_arr_dtor(context, builder,
            struct_arr_type, payload_type)
        xlnd__vdpz = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, gfxq__ulw), gzhtq__bxn)
        nrjoy__yrh = context.nrt.meminfo_data(builder, xlnd__vdpz)
        nhdj__fvf = builder.bitcast(nrjoy__yrh, fhq__axozt.as_pointer())
        zcl__omsqe = cgutils.create_struct_proxy(payload_type)(context, builder
            )
        zcl__omsqe.data = data
        zcl__omsqe.null_bitmap = lemjy__oueqy
        builder.store(zcl__omsqe._getvalue(), nhdj__fvf)
        context.nrt.incref(builder, data_typ, data)
        context.nrt.incref(builder, null_bitmap_typ, lemjy__oueqy)
        wvtu__huxba = context.make_helper(builder, struct_arr_type)
        wvtu__huxba.meminfo = xlnd__vdpz
        return wvtu__huxba._getvalue()
    return struct_arr_type(data_typ, null_bitmap_typ, names_typ), codegen


@overload(operator.getitem, no_unliteral=True)
def struct_arr_getitem(arr, ind):
    if not isinstance(arr, StructArrayType):
        return
    if isinstance(ind, types.Integer):

        def struct_arr_getitem_impl(arr, ind):
            if ind < 0:
                ind += len(arr)
            return struct_array_get_struct(arr, ind)
        return struct_arr_getitem_impl
    qkt__rrg = len(arr.data)
    lzxuy__nfeg = 'def impl(arr, ind):\n'
    lzxuy__nfeg += '  data = get_data(arr)\n'
    lzxuy__nfeg += '  null_bitmap = get_null_bitmap(arr)\n'
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        lzxuy__nfeg += """  out_null_bitmap = get_new_null_mask_bool_index(null_bitmap, ind, len(data[0]))
"""
    elif is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        lzxuy__nfeg += """  out_null_bitmap = get_new_null_mask_int_index(null_bitmap, ind, len(data[0]))
"""
    elif isinstance(ind, types.SliceType):
        lzxuy__nfeg += """  out_null_bitmap = get_new_null_mask_slice_index(null_bitmap, ind, len(data[0]))
"""
    else:
        raise BodoError('invalid index {} in struct array indexing'.format(ind)
            )
    lzxuy__nfeg += ('  return init_struct_arr(({},), out_null_bitmap, ({},))\n'
        .format(', '.join('ensure_contig_if_np(data[{}][ind])'.format(i) for
        i in range(qkt__rrg)), ', '.join("'{}'".format(hiz__ncxmk) for
        hiz__ncxmk in arr.names)))
    tdaj__sgs = {}
    exec(lzxuy__nfeg, {'init_struct_arr': init_struct_arr, 'get_data':
        get_data, 'get_null_bitmap': get_null_bitmap, 'ensure_contig_if_np':
        bodo.utils.conversion.ensure_contig_if_np,
        'get_new_null_mask_bool_index': bodo.utils.indexing.
        get_new_null_mask_bool_index, 'get_new_null_mask_int_index': bodo.
        utils.indexing.get_new_null_mask_int_index,
        'get_new_null_mask_slice_index': bodo.utils.indexing.
        get_new_null_mask_slice_index}, tdaj__sgs)
    impl = tdaj__sgs['impl']
    return impl


@overload(operator.setitem, no_unliteral=True)
def struct_arr_setitem(arr, ind, val):
    if not isinstance(arr, StructArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    if isinstance(ind, types.Integer):
        qkt__rrg = len(arr.data)
        lzxuy__nfeg = 'def impl(arr, ind, val):\n'
        lzxuy__nfeg += '  data = get_data(arr)\n'
        lzxuy__nfeg += '  null_bitmap = get_null_bitmap(arr)\n'
        lzxuy__nfeg += '  set_bit_to_arr(null_bitmap, ind, 1)\n'
        for i in range(qkt__rrg):
            if isinstance(val, StructType):
                lzxuy__nfeg += "  if is_field_value_null(val, '{}'):\n".format(
                    arr.names[i])
                lzxuy__nfeg += (
                    '    bodo.libs.array_kernels.setna(data[{}], ind)\n'.
                    format(i))
                lzxuy__nfeg += '  else:\n'
                lzxuy__nfeg += "    data[{}][ind] = val['{}']\n".format(i,
                    arr.names[i])
            else:
                lzxuy__nfeg += "  data[{}][ind] = val['{}']\n".format(i,
                    arr.names[i])
        tdaj__sgs = {}
        exec(lzxuy__nfeg, {'bodo': bodo, 'get_data': get_data,
            'get_null_bitmap': get_null_bitmap, 'set_bit_to_arr': bodo.libs
            .int_arr_ext.set_bit_to_arr, 'is_field_value_null':
            is_field_value_null}, tdaj__sgs)
        impl = tdaj__sgs['impl']
        return impl
    if isinstance(ind, types.SliceType):
        qkt__rrg = len(arr.data)
        lzxuy__nfeg = 'def impl(arr, ind, val):\n'
        lzxuy__nfeg += '  data = get_data(arr)\n'
        lzxuy__nfeg += '  null_bitmap = get_null_bitmap(arr)\n'
        lzxuy__nfeg += '  val_data = get_data(val)\n'
        lzxuy__nfeg += '  val_null_bitmap = get_null_bitmap(val)\n'
        lzxuy__nfeg += """  setitem_slice_index_null_bits(null_bitmap, val_null_bitmap, ind, len(arr))
"""
        for i in range(qkt__rrg):
            lzxuy__nfeg += '  data[{0}][ind] = val_data[{0}]\n'.format(i)
        tdaj__sgs = {}
        exec(lzxuy__nfeg, {'bodo': bodo, 'get_data': get_data,
            'get_null_bitmap': get_null_bitmap, 'set_bit_to_arr': bodo.libs
            .int_arr_ext.set_bit_to_arr, 'setitem_slice_index_null_bits':
            bodo.utils.indexing.setitem_slice_index_null_bits}, tdaj__sgs)
        impl = tdaj__sgs['impl']
        return impl
    raise BodoError(
        'only setitem with scalar/slice index is currently supported for struct arrays'
        )


@overload(len, no_unliteral=True)
def overload_struct_arr_len(A):
    if isinstance(A, StructArrayType):
        return lambda A: len(get_data(A)[0])


@overload_attribute(StructArrayType, 'shape')
def overload_struct_arr_shape(A):
    return lambda A: (len(get_data(A)[0]),)


@overload_attribute(StructArrayType, 'dtype')
def overload_struct_arr_dtype(A):
    return lambda A: np.object_


@overload_attribute(StructArrayType, 'ndim')
def overload_struct_arr_ndim(A):
    return lambda A: 1


@overload_attribute(StructArrayType, 'nbytes')
def overload_struct_arr_nbytes(A):
    lzxuy__nfeg = 'def impl(A):\n'
    lzxuy__nfeg += '  total_nbytes = 0\n'
    lzxuy__nfeg += '  data = get_data(A)\n'
    for i in range(len(A.data)):
        lzxuy__nfeg += f'  total_nbytes += data[{i}].nbytes\n'
    lzxuy__nfeg += '  total_nbytes += get_null_bitmap(A).nbytes\n'
    lzxuy__nfeg += '  return total_nbytes\n'
    tdaj__sgs = {}
    exec(lzxuy__nfeg, {'get_data': get_data, 'get_null_bitmap':
        get_null_bitmap}, tdaj__sgs)
    impl = tdaj__sgs['impl']
    return impl


@overload_method(StructArrayType, 'copy', no_unliteral=True)
def overload_struct_arr_copy(A):
    names = A.names

    def copy_impl(A):
        data = get_data(A)
        lemjy__oueqy = get_null_bitmap(A)
        ruegp__ynr = bodo.ir.join.copy_arr_tup(data)
        walfs__qhkhf = lemjy__oueqy.copy()
        return init_struct_arr(ruegp__ynr, walfs__qhkhf, names)
    return copy_impl
