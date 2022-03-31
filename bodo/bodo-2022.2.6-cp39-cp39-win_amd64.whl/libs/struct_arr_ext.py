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
            .utils.is_array_typ(nxvmf__ndvos, False) for nxvmf__ndvos in data)
        if names is not None:
            assert isinstance(names, tuple) and all(isinstance(nxvmf__ndvos,
                str) for nxvmf__ndvos in names) and len(names) == len(data)
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
        return StructType(tuple(vat__seh.dtype for vat__seh in self.data),
            self.names)

    @classmethod
    def from_dict(cls, d):
        assert isinstance(d, dict)
        names = tuple(str(nxvmf__ndvos) for nxvmf__ndvos in d.keys())
        data = tuple(dtype_to_array_type(vat__seh) for vat__seh in d.values())
        return StructArrayType(data, names)

    def copy(self):
        return StructArrayType(self.data, self.names)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


class StructArrayPayloadType(types.Type):

    def __init__(self, data):
        assert isinstance(data, tuple) and all(bodo.utils.utils.
            is_array_typ(nxvmf__ndvos, False) for nxvmf__ndvos in data)
        self.data = data
        super(StructArrayPayloadType, self).__init__(name=
            'StructArrayPayloadType({})'.format(data))

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(StructArrayPayloadType)
class StructArrayPayloadModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        uiaro__lwsfm = [('data', types.BaseTuple.from_types(fe_type.data)),
            ('null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, uiaro__lwsfm)


@register_model(StructArrayType)
class StructArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = StructArrayPayloadType(fe_type.data)
        uiaro__lwsfm = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, uiaro__lwsfm)


def define_struct_arr_dtor(context, builder, struct_arr_type, payload_type):
    dnxcz__qzt = builder.module
    rpy__xiy = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    vevjh__rlepn = cgutils.get_or_insert_function(dnxcz__qzt, rpy__xiy,
        name='.dtor.struct_arr.{}.{}.'.format(struct_arr_type.data,
        struct_arr_type.names))
    if not vevjh__rlepn.is_declaration:
        return vevjh__rlepn
    vevjh__rlepn.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(vevjh__rlepn.append_basic_block())
    jdz__gna = vevjh__rlepn.args[0]
    zwmcw__dscce = context.get_value_type(payload_type).as_pointer()
    lru__knl = builder.bitcast(jdz__gna, zwmcw__dscce)
    zvp__ttr = context.make_helper(builder, payload_type, ref=lru__knl)
    context.nrt.decref(builder, types.BaseTuple.from_types(struct_arr_type.
        data), zvp__ttr.data)
    context.nrt.decref(builder, types.Array(types.uint8, 1, 'C'), zvp__ttr.
        null_bitmap)
    builder.ret_void()
    return vevjh__rlepn


def construct_struct_array(context, builder, struct_arr_type, n_structs,
    n_elems, c=None):
    payload_type = StructArrayPayloadType(struct_arr_type.data)
    swvr__rgvmy = context.get_value_type(payload_type)
    pla__mewxx = context.get_abi_sizeof(swvr__rgvmy)
    zgh__dezy = define_struct_arr_dtor(context, builder, struct_arr_type,
        payload_type)
    bvd__ybkde = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, pla__mewxx), zgh__dezy)
    rso__xfp = context.nrt.meminfo_data(builder, bvd__ybkde)
    fenmu__kcy = builder.bitcast(rso__xfp, swvr__rgvmy.as_pointer())
    zvp__ttr = cgutils.create_struct_proxy(payload_type)(context, builder)
    raax__jrfxp = []
    umryv__poiu = 0
    for arr_typ in struct_arr_type.data:
        yeko__dhfa = bodo.utils.transform.get_type_alloc_counts(arr_typ.dtype)
        kzsp__qbknl = cgutils.pack_array(builder, [n_structs] + [builder.
            extract_value(n_elems, i) for i in range(umryv__poiu, 
            umryv__poiu + yeko__dhfa)])
        arr = gen_allocate_array(context, builder, arr_typ, kzsp__qbknl, c)
        raax__jrfxp.append(arr)
        umryv__poiu += yeko__dhfa
    zvp__ttr.data = cgutils.pack_array(builder, raax__jrfxp
        ) if types.is_homogeneous(*struct_arr_type.data
        ) else cgutils.pack_struct(builder, raax__jrfxp)
    godm__htc = builder.udiv(builder.add(n_structs, lir.Constant(lir.
        IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
    rcmv__lviyi = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(types.uint8, 1, 'C'), [godm__htc])
    null_bitmap_ptr = rcmv__lviyi.data
    zvp__ttr.null_bitmap = rcmv__lviyi._getvalue()
    builder.store(zvp__ttr._getvalue(), fenmu__kcy)
    return bvd__ybkde, zvp__ttr.data, null_bitmap_ptr


def _get_C_API_ptrs(c, data_tup, data_typ, names):
    zme__telk = []
    assert len(data_typ) > 0
    for i, arr_typ in enumerate(data_typ):
        gdhf__gfntw = c.builder.extract_value(data_tup, i)
        arr = c.context.make_array(arr_typ)(c.context, c.builder, value=
            gdhf__gfntw)
        zme__telk.append(arr.data)
    vyxe__ogla = cgutils.pack_array(c.builder, zme__telk
        ) if types.is_homogeneous(*data_typ) else cgutils.pack_struct(c.
        builder, zme__telk)
    ltl__mil = cgutils.alloca_once_value(c.builder, vyxe__ogla)
    iknal__uyqm = [c.context.get_constant(types.int32, bodo.utils.utils.
        numba_to_c_type(nxvmf__ndvos.dtype)) for nxvmf__ndvos in data_typ]
    fbar__wwlhm = cgutils.alloca_once_value(c.builder, cgutils.pack_array(c
        .builder, iknal__uyqm))
    jbvac__dzp = cgutils.pack_array(c.builder, [c.context.
        insert_const_string(c.builder.module, nxvmf__ndvos) for
        nxvmf__ndvos in names])
    tbxee__ubazb = cgutils.alloca_once_value(c.builder, jbvac__dzp)
    return ltl__mil, fbar__wwlhm, tbxee__ubazb


@unbox(StructArrayType)
def unbox_struct_array(typ, val, c, is_tuple_array=False):
    from bodo.libs.tuple_arr_ext import TupleArrayType
    n_structs = bodo.utils.utils.object_length(c, val)
    gxz__tmjy = all(isinstance(vat__seh, types.Array) and vat__seh.dtype in
        (types.int64, types.float64, types.bool_, datetime_date_type) for
        vat__seh in typ.data)
    if gxz__tmjy:
        n_elems = cgutils.pack_array(c.builder, [], lir.IntType(64))
    else:
        cdz__pqsr = get_array_elem_counts(c, c.builder, c.context, val, 
            TupleArrayType(typ.data) if is_tuple_array else typ)
        n_elems = cgutils.pack_array(c.builder, [c.builder.extract_value(
            cdz__pqsr, i) for i in range(1, cdz__pqsr.type.count)], lir.
            IntType(64))
    bvd__ybkde, data_tup, null_bitmap_ptr = construct_struct_array(c.
        context, c.builder, typ, n_structs, n_elems, c)
    if gxz__tmjy:
        ltl__mil, fbar__wwlhm, tbxee__ubazb = _get_C_API_ptrs(c, data_tup,
            typ.data, typ.names)
        rpy__xiy = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(32), lir.IntType(8).as_pointer(), lir
            .IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1)])
        vevjh__rlepn = cgutils.get_or_insert_function(c.builder.module,
            rpy__xiy, name='struct_array_from_sequence')
        c.builder.call(vevjh__rlepn, [val, c.context.get_constant(types.
            int32, len(typ.data)), c.builder.bitcast(ltl__mil, lir.IntType(
            8).as_pointer()), null_bitmap_ptr, c.builder.bitcast(
            fbar__wwlhm, lir.IntType(8).as_pointer()), c.builder.bitcast(
            tbxee__ubazb, lir.IntType(8).as_pointer()), c.context.
            get_constant(types.bool_, is_tuple_array)])
    else:
        _unbox_struct_array_generic(typ, val, c, n_structs, data_tup,
            null_bitmap_ptr, is_tuple_array)
    zlpa__rry = c.context.make_helper(c.builder, typ)
    zlpa__rry.meminfo = bvd__ybkde
    xdhh__erz = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(zlpa__rry._getvalue(), is_error=xdhh__erz)


def _unbox_struct_array_generic(typ, val, c, n_structs, data_tup,
    null_bitmap_ptr, is_tuple_array=False):
    context = c.context
    builder = c.builder
    lzt__dosix = context.insert_const_string(builder.module, 'pandas')
    yebj__rjslm = c.pyapi.import_module_noblock(lzt__dosix)
    eeiwf__dkan = c.pyapi.object_getattr_string(yebj__rjslm, 'NA')
    with cgutils.for_range(builder, n_structs) as kpeux__jagx:
        gifme__gdyd = kpeux__jagx.index
        wmlm__tzgyw = seq_getitem(builder, context, val, gifme__gdyd)
        set_bitmap_bit(builder, null_bitmap_ptr, gifme__gdyd, 0)
        for zpx__orl in range(len(typ.data)):
            arr_typ = typ.data[zpx__orl]
            data_arr = builder.extract_value(data_tup, zpx__orl)

            def set_na(data_arr, i):
                bodo.libs.array_kernels.setna(data_arr, i)
            sig = types.none(arr_typ, types.int64)
            cpdji__kbd, qexe__lhbmq = c.pyapi.call_jit_code(set_na, sig, [
                data_arr, gifme__gdyd])
        ylpz__qgfl = is_na_value(builder, context, wmlm__tzgyw, eeiwf__dkan)
        yfgo__gbg = builder.icmp_unsigned('!=', ylpz__qgfl, lir.Constant(
            ylpz__qgfl.type, 1))
        with builder.if_then(yfgo__gbg):
            set_bitmap_bit(builder, null_bitmap_ptr, gifme__gdyd, 1)
            for zpx__orl in range(len(typ.data)):
                arr_typ = typ.data[zpx__orl]
                if is_tuple_array:
                    fjvs__bxh = c.pyapi.tuple_getitem(wmlm__tzgyw, zpx__orl)
                else:
                    fjvs__bxh = c.pyapi.dict_getitem_string(wmlm__tzgyw,
                        typ.names[zpx__orl])
                ylpz__qgfl = is_na_value(builder, context, fjvs__bxh,
                    eeiwf__dkan)
                yfgo__gbg = builder.icmp_unsigned('!=', ylpz__qgfl, lir.
                    Constant(ylpz__qgfl.type, 1))
                with builder.if_then(yfgo__gbg):
                    fjvs__bxh = to_arr_obj_if_list_obj(c, context, builder,
                        fjvs__bxh, arr_typ.dtype)
                    field_val = c.pyapi.to_native_value(arr_typ.dtype,
                        fjvs__bxh).value
                    data_arr = builder.extract_value(data_tup, zpx__orl)

                    def set_data(data_arr, i, field_val):
                        data_arr[i] = field_val
                    sig = types.none(arr_typ, types.int64, arr_typ.dtype)
                    cpdji__kbd, qexe__lhbmq = c.pyapi.call_jit_code(set_data,
                        sig, [data_arr, gifme__gdyd, field_val])
                    c.context.nrt.decref(builder, arr_typ.dtype, field_val)
        c.pyapi.decref(wmlm__tzgyw)
    c.pyapi.decref(yebj__rjslm)
    c.pyapi.decref(eeiwf__dkan)


def _get_struct_arr_payload(context, builder, arr_typ, arr):
    zlpa__rry = context.make_helper(builder, arr_typ, arr)
    payload_type = StructArrayPayloadType(arr_typ.data)
    rso__xfp = context.nrt.meminfo_data(builder, zlpa__rry.meminfo)
    fenmu__kcy = builder.bitcast(rso__xfp, context.get_value_type(
        payload_type).as_pointer())
    zvp__ttr = cgutils.create_struct_proxy(payload_type)(context, builder,
        builder.load(fenmu__kcy))
    return zvp__ttr


@box(StructArrayType)
def box_struct_arr(typ, val, c, is_tuple_array=False):
    zvp__ttr = _get_struct_arr_payload(c.context, c.builder, typ, val)
    cpdji__kbd, length = c.pyapi.call_jit_code(lambda A: len(A), types.
        int64(typ), [val])
    null_bitmap_ptr = c.context.make_helper(c.builder, types.Array(types.
        uint8, 1, 'C'), zvp__ttr.null_bitmap).data
    gxz__tmjy = all(isinstance(vat__seh, types.Array) and vat__seh.dtype in
        (types.int64, types.float64, types.bool_, datetime_date_type) for
        vat__seh in typ.data)
    if gxz__tmjy:
        ltl__mil, fbar__wwlhm, tbxee__ubazb = _get_C_API_ptrs(c, zvp__ttr.
            data, typ.data, typ.names)
        rpy__xiy = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(32), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1)])
        smai__roj = cgutils.get_or_insert_function(c.builder.module,
            rpy__xiy, name='np_array_from_struct_array')
        arr = c.builder.call(smai__roj, [length, c.context.get_constant(
            types.int32, len(typ.data)), c.builder.bitcast(ltl__mil, lir.
            IntType(8).as_pointer()), null_bitmap_ptr, c.builder.bitcast(
            fbar__wwlhm, lir.IntType(8).as_pointer()), c.builder.bitcast(
            tbxee__ubazb, lir.IntType(8).as_pointer()), c.context.
            get_constant(types.bool_, is_tuple_array)])
    else:
        arr = _box_struct_array_generic(typ, c, length, zvp__ttr.data,
            null_bitmap_ptr, is_tuple_array)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def _box_struct_array_generic(typ, c, length, data_arrs_tup,
    null_bitmap_ptr, is_tuple_array=False):
    context = c.context
    builder = c.builder
    lzt__dosix = context.insert_const_string(builder.module, 'numpy')
    frhq__zuk = c.pyapi.import_module_noblock(lzt__dosix)
    fokz__fcfi = c.pyapi.object_getattr_string(frhq__zuk, 'object_')
    irxqz__tgmn = c.pyapi.long_from_longlong(length)
    xrbik__culg = c.pyapi.call_method(frhq__zuk, 'ndarray', (irxqz__tgmn,
        fokz__fcfi))
    rxu__sbf = c.pyapi.object_getattr_string(frhq__zuk, 'nan')
    with cgutils.for_range(builder, length) as kpeux__jagx:
        gifme__gdyd = kpeux__jagx.index
        pyarray_setitem(builder, context, xrbik__culg, gifme__gdyd, rxu__sbf)
        gym__zsgvu = get_bitmap_bit(builder, null_bitmap_ptr, gifme__gdyd)
        bcvb__szm = builder.icmp_unsigned('!=', gym__zsgvu, lir.Constant(
            lir.IntType(8), 0))
        with builder.if_then(bcvb__szm):
            if is_tuple_array:
                wmlm__tzgyw = c.pyapi.tuple_new(len(typ.data))
            else:
                wmlm__tzgyw = c.pyapi.dict_new(len(typ.data))
            for i, arr_typ in enumerate(typ.data):
                if is_tuple_array:
                    c.pyapi.incref(rxu__sbf)
                    c.pyapi.tuple_setitem(wmlm__tzgyw, i, rxu__sbf)
                else:
                    c.pyapi.dict_setitem_string(wmlm__tzgyw, typ.names[i],
                        rxu__sbf)
                data_arr = c.builder.extract_value(data_arrs_tup, i)
                cpdji__kbd, iakq__qjjwx = c.pyapi.call_jit_code(lambda
                    data_arr, ind: not bodo.libs.array_kernels.isna(
                    data_arr, ind), types.bool_(arr_typ, types.int64), [
                    data_arr, gifme__gdyd])
                with builder.if_then(iakq__qjjwx):
                    cpdji__kbd, field_val = c.pyapi.call_jit_code(lambda
                        data_arr, ind: data_arr[ind], arr_typ.dtype(arr_typ,
                        types.int64), [data_arr, gifme__gdyd])
                    rbhqq__tyf = c.pyapi.from_native_value(arr_typ.dtype,
                        field_val, c.env_manager)
                    if is_tuple_array:
                        c.pyapi.tuple_setitem(wmlm__tzgyw, i, rbhqq__tyf)
                    else:
                        c.pyapi.dict_setitem_string(wmlm__tzgyw, typ.names[
                            i], rbhqq__tyf)
                        c.pyapi.decref(rbhqq__tyf)
            pyarray_setitem(builder, context, xrbik__culg, gifme__gdyd,
                wmlm__tzgyw)
            c.pyapi.decref(wmlm__tzgyw)
    c.pyapi.decref(frhq__zuk)
    c.pyapi.decref(fokz__fcfi)
    c.pyapi.decref(irxqz__tgmn)
    c.pyapi.decref(rxu__sbf)
    return xrbik__culg


def _fix_nested_counts(nested_counts, struct_arr_type, nested_counts_type,
    builder):
    uewyy__qbb = bodo.utils.transform.get_type_alloc_counts(struct_arr_type
        ) - 1
    if uewyy__qbb == 0:
        return nested_counts
    if not isinstance(nested_counts_type, types.UniTuple):
        nested_counts = cgutils.pack_array(builder, [lir.Constant(lir.
            IntType(64), -1) for snh__jxgwy in range(uewyy__qbb)])
    elif nested_counts_type.count < uewyy__qbb:
        nested_counts = cgutils.pack_array(builder, [builder.extract_value(
            nested_counts, i) for i in range(nested_counts_type.count)] + [
            lir.Constant(lir.IntType(64), -1) for snh__jxgwy in range(
            uewyy__qbb - nested_counts_type.count)])
    return nested_counts


@intrinsic
def pre_alloc_struct_array(typingctx, num_structs_typ, nested_counts_typ,
    dtypes_typ, names_typ=None):
    assert isinstance(num_structs_typ, types.Integer) and isinstance(dtypes_typ
        , types.BaseTuple)
    if is_overload_none(names_typ):
        names = tuple(f'f{i}' for i in range(len(dtypes_typ)))
    else:
        names = tuple(get_overload_const_str(vat__seh) for vat__seh in
            names_typ.types)
    spxee__gxvzr = tuple(vat__seh.instance_type for vat__seh in dtypes_typ.
        types)
    struct_arr_type = StructArrayType(spxee__gxvzr, names)

    def codegen(context, builder, sig, args):
        zrnw__uagx, nested_counts, snh__jxgwy, snh__jxgwy = args
        nested_counts_type = sig.args[1]
        nested_counts = _fix_nested_counts(nested_counts, struct_arr_type,
            nested_counts_type, builder)
        bvd__ybkde, snh__jxgwy, snh__jxgwy = construct_struct_array(context,
            builder, struct_arr_type, zrnw__uagx, nested_counts)
        zlpa__rry = context.make_helper(builder, struct_arr_type)
        zlpa__rry.meminfo = bvd__ybkde
        return zlpa__rry._getvalue()
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
        assert isinstance(names, tuple) and all(isinstance(nxvmf__ndvos,
            str) for nxvmf__ndvos in names) and len(names) == len(data)
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
        uiaro__lwsfm = [('data', types.BaseTuple.from_types(fe_type.data)),
            ('null_bitmap', types.UniTuple(types.int8, len(fe_type.data)))]
        models.StructModel.__init__(self, dmm, fe_type, uiaro__lwsfm)


@register_model(StructType)
class StructModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = StructPayloadType(fe_type.data)
        uiaro__lwsfm = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, uiaro__lwsfm)


def define_struct_dtor(context, builder, struct_type, payload_type):
    dnxcz__qzt = builder.module
    rpy__xiy = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    vevjh__rlepn = cgutils.get_or_insert_function(dnxcz__qzt, rpy__xiy,
        name='.dtor.struct.{}.{}.'.format(struct_type.data, struct_type.names))
    if not vevjh__rlepn.is_declaration:
        return vevjh__rlepn
    vevjh__rlepn.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(vevjh__rlepn.append_basic_block())
    jdz__gna = vevjh__rlepn.args[0]
    zwmcw__dscce = context.get_value_type(payload_type).as_pointer()
    lru__knl = builder.bitcast(jdz__gna, zwmcw__dscce)
    zvp__ttr = context.make_helper(builder, payload_type, ref=lru__knl)
    for i in range(len(struct_type.data)):
        njahr__ampe = builder.extract_value(zvp__ttr.null_bitmap, i)
        bcvb__szm = builder.icmp_unsigned('==', njahr__ampe, lir.Constant(
            njahr__ampe.type, 1))
        with builder.if_then(bcvb__szm):
            val = builder.extract_value(zvp__ttr.data, i)
            context.nrt.decref(builder, struct_type.data[i], val)
    builder.ret_void()
    return vevjh__rlepn


def _get_struct_payload(context, builder, typ, struct):
    struct = context.make_helper(builder, typ, struct)
    payload_type = StructPayloadType(typ.data)
    rso__xfp = context.nrt.meminfo_data(builder, struct.meminfo)
    fenmu__kcy = builder.bitcast(rso__xfp, context.get_value_type(
        payload_type).as_pointer())
    zvp__ttr = cgutils.create_struct_proxy(payload_type)(context, builder,
        builder.load(fenmu__kcy))
    return zvp__ttr, fenmu__kcy


@unbox(StructType)
def unbox_struct(typ, val, c):
    context = c.context
    builder = c.builder
    lzt__dosix = context.insert_const_string(builder.module, 'pandas')
    yebj__rjslm = c.pyapi.import_module_noblock(lzt__dosix)
    eeiwf__dkan = c.pyapi.object_getattr_string(yebj__rjslm, 'NA')
    kmbkd__fwbyn = []
    nulls = []
    for i, vat__seh in enumerate(typ.data):
        rbhqq__tyf = c.pyapi.dict_getitem_string(val, typ.names[i])
        jlzha__iyuyp = cgutils.alloca_once_value(c.builder, context.
            get_constant(types.uint8, 0))
        pqhr__oufct = cgutils.alloca_once_value(c.builder, cgutils.
            get_null_value(context.get_value_type(vat__seh)))
        ylpz__qgfl = is_na_value(builder, context, rbhqq__tyf, eeiwf__dkan)
        bcvb__szm = builder.icmp_unsigned('!=', ylpz__qgfl, lir.Constant(
            ylpz__qgfl.type, 1))
        with builder.if_then(bcvb__szm):
            builder.store(context.get_constant(types.uint8, 1), jlzha__iyuyp)
            field_val = c.pyapi.to_native_value(vat__seh, rbhqq__tyf).value
            builder.store(field_val, pqhr__oufct)
        kmbkd__fwbyn.append(builder.load(pqhr__oufct))
        nulls.append(builder.load(jlzha__iyuyp))
    c.pyapi.decref(yebj__rjslm)
    c.pyapi.decref(eeiwf__dkan)
    bvd__ybkde = construct_struct(context, builder, typ, kmbkd__fwbyn, nulls)
    struct = context.make_helper(builder, typ)
    struct.meminfo = bvd__ybkde
    xdhh__erz = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(struct._getvalue(), is_error=xdhh__erz)


@box(StructType)
def box_struct(typ, val, c):
    dvzsx__dmdeh = c.pyapi.dict_new(len(typ.data))
    zvp__ttr, snh__jxgwy = _get_struct_payload(c.context, c.builder, typ, val)
    assert len(typ.data) > 0
    for i, val_typ in enumerate(typ.data):
        c.pyapi.dict_setitem_string(dvzsx__dmdeh, typ.names[i], c.pyapi.
            borrow_none())
        njahr__ampe = c.builder.extract_value(zvp__ttr.null_bitmap, i)
        bcvb__szm = c.builder.icmp_unsigned('==', njahr__ampe, lir.Constant
            (njahr__ampe.type, 1))
        with c.builder.if_then(bcvb__szm):
            rzuh__totc = c.builder.extract_value(zvp__ttr.data, i)
            c.context.nrt.incref(c.builder, val_typ, rzuh__totc)
            fjvs__bxh = c.pyapi.from_native_value(val_typ, rzuh__totc, c.
                env_manager)
            c.pyapi.dict_setitem_string(dvzsx__dmdeh, typ.names[i], fjvs__bxh)
            c.pyapi.decref(fjvs__bxh)
    c.context.nrt.decref(c.builder, typ, val)
    return dvzsx__dmdeh


@intrinsic
def init_struct(typingctx, data_typ, names_typ=None):
    names = tuple(get_overload_const_str(vat__seh) for vat__seh in
        names_typ.types)
    struct_type = StructType(data_typ.types, names)

    def codegen(context, builder, sig, args):
        data, hkp__vfyyr = args
        payload_type = StructPayloadType(struct_type.data)
        swvr__rgvmy = context.get_value_type(payload_type)
        pla__mewxx = context.get_abi_sizeof(swvr__rgvmy)
        zgh__dezy = define_struct_dtor(context, builder, struct_type,
            payload_type)
        bvd__ybkde = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, pla__mewxx), zgh__dezy)
        rso__xfp = context.nrt.meminfo_data(builder, bvd__ybkde)
        fenmu__kcy = builder.bitcast(rso__xfp, swvr__rgvmy.as_pointer())
        zvp__ttr = cgutils.create_struct_proxy(payload_type)(context, builder)
        zvp__ttr.data = data
        zvp__ttr.null_bitmap = cgutils.pack_array(builder, [context.
            get_constant(types.uint8, 1) for snh__jxgwy in range(len(
            data_typ.types))])
        builder.store(zvp__ttr._getvalue(), fenmu__kcy)
        context.nrt.incref(builder, data_typ, data)
        struct = context.make_helper(builder, struct_type)
        struct.meminfo = bvd__ybkde
        return struct._getvalue()
    return struct_type(data_typ, names_typ), codegen


@intrinsic
def get_struct_data(typingctx, struct_typ=None):
    assert isinstance(struct_typ, StructType)

    def codegen(context, builder, sig, args):
        struct, = args
        zvp__ttr, snh__jxgwy = _get_struct_payload(context, builder,
            struct_typ, struct)
        return impl_ret_borrowed(context, builder, sig.return_type,
            zvp__ttr.data)
    return types.BaseTuple.from_types(struct_typ.data)(struct_typ), codegen


@intrinsic
def get_struct_null_bitmap(typingctx, struct_typ=None):
    assert isinstance(struct_typ, StructType)

    def codegen(context, builder, sig, args):
        struct, = args
        zvp__ttr, snh__jxgwy = _get_struct_payload(context, builder,
            struct_typ, struct)
        return impl_ret_borrowed(context, builder, sig.return_type,
            zvp__ttr.null_bitmap)
    ptzv__adwe = types.UniTuple(types.int8, len(struct_typ.data))
    return ptzv__adwe(struct_typ), codegen


@intrinsic
def set_struct_data(typingctx, struct_typ, field_ind_typ, val_typ=None):
    assert isinstance(struct_typ, StructType) and is_overload_constant_int(
        field_ind_typ)
    field_ind = get_overload_const_int(field_ind_typ)

    def codegen(context, builder, sig, args):
        struct, snh__jxgwy, val = args
        zvp__ttr, fenmu__kcy = _get_struct_payload(context, builder,
            struct_typ, struct)
        trmn__wurh = zvp__ttr.data
        zgw__zxqvo = builder.insert_value(trmn__wurh, val, field_ind)
        qzrji__npzw = types.BaseTuple.from_types(struct_typ.data)
        context.nrt.decref(builder, qzrji__npzw, trmn__wurh)
        context.nrt.incref(builder, qzrji__npzw, zgw__zxqvo)
        zvp__ttr.data = zgw__zxqvo
        builder.store(zvp__ttr._getvalue(), fenmu__kcy)
        return context.get_dummy_value()
    return types.none(struct_typ, field_ind_typ, val_typ), codegen


def _get_struct_field_ind(struct, ind, op):
    if not is_overload_constant_str(ind):
        raise BodoError(
            'structs (from struct array) only support constant strings for {}, not {}'
            .format(op, ind))
    chce__kppsz = get_overload_const_str(ind)
    if chce__kppsz not in struct.names:
        raise BodoError('Field {} does not exist in struct {}'.format(
            chce__kppsz, struct))
    return struct.names.index(chce__kppsz)


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
    swvr__rgvmy = context.get_value_type(payload_type)
    pla__mewxx = context.get_abi_sizeof(swvr__rgvmy)
    zgh__dezy = define_struct_dtor(context, builder, struct_type, payload_type)
    bvd__ybkde = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, pla__mewxx), zgh__dezy)
    rso__xfp = context.nrt.meminfo_data(builder, bvd__ybkde)
    fenmu__kcy = builder.bitcast(rso__xfp, swvr__rgvmy.as_pointer())
    zvp__ttr = cgutils.create_struct_proxy(payload_type)(context, builder)
    zvp__ttr.data = cgutils.pack_array(builder, values
        ) if types.is_homogeneous(*struct_type.data) else cgutils.pack_struct(
        builder, values)
    zvp__ttr.null_bitmap = cgutils.pack_array(builder, nulls)
    builder.store(zvp__ttr._getvalue(), fenmu__kcy)
    return bvd__ybkde


@intrinsic
def struct_array_get_struct(typingctx, struct_arr_typ, ind_typ=None):
    assert isinstance(struct_arr_typ, StructArrayType) and isinstance(ind_typ,
        types.Integer)
    lfxn__zgk = tuple(d.dtype for d in struct_arr_typ.data)
    qvhpd__heoyb = StructType(lfxn__zgk, struct_arr_typ.names)

    def codegen(context, builder, sig, args):
        qpvog__oad, ind = args
        zvp__ttr = _get_struct_arr_payload(context, builder, struct_arr_typ,
            qpvog__oad)
        kmbkd__fwbyn = []
        ije__xvy = []
        for i, arr_typ in enumerate(struct_arr_typ.data):
            gdhf__gfntw = builder.extract_value(zvp__ttr.data, i)
            ysidj__wbig = context.compile_internal(builder, lambda arr, ind:
                np.uint8(0) if bodo.libs.array_kernels.isna(arr, ind) else
                np.uint8(1), types.uint8(arr_typ, types.int64), [
                gdhf__gfntw, ind])
            ije__xvy.append(ysidj__wbig)
            tvdn__xopp = cgutils.alloca_once_value(builder, context.
                get_constant_null(arr_typ.dtype))
            bcvb__szm = builder.icmp_unsigned('==', ysidj__wbig, lir.
                Constant(ysidj__wbig.type, 1))
            with builder.if_then(bcvb__szm):
                dpvs__ceukh = context.compile_internal(builder, lambda arr,
                    ind: arr[ind], arr_typ.dtype(arr_typ, types.int64), [
                    gdhf__gfntw, ind])
                builder.store(dpvs__ceukh, tvdn__xopp)
            kmbkd__fwbyn.append(builder.load(tvdn__xopp))
        if isinstance(qvhpd__heoyb, types.DictType):
            emvht__jgl = [context.insert_const_string(builder.module,
                oex__fvc) for oex__fvc in struct_arr_typ.names]
            tfwi__ahr = cgutils.pack_array(builder, kmbkd__fwbyn)
            umrrt__xtsvv = cgutils.pack_array(builder, emvht__jgl)

            def impl(names, vals):
                d = {}
                for i, oex__fvc in enumerate(names):
                    d[oex__fvc] = vals[i]
                return d
            giak__bgwlg = context.compile_internal(builder, impl,
                qvhpd__heoyb(types.Tuple(tuple(types.StringLiteral(oex__fvc
                ) for oex__fvc in struct_arr_typ.names)), types.Tuple(
                lfxn__zgk)), [umrrt__xtsvv, tfwi__ahr])
            context.nrt.decref(builder, types.BaseTuple.from_types(
                lfxn__zgk), tfwi__ahr)
            return giak__bgwlg
        bvd__ybkde = construct_struct(context, builder, qvhpd__heoyb,
            kmbkd__fwbyn, ije__xvy)
        struct = context.make_helper(builder, qvhpd__heoyb)
        struct.meminfo = bvd__ybkde
        return struct._getvalue()
    return qvhpd__heoyb(struct_arr_typ, ind_typ), codegen


@intrinsic
def get_data(typingctx, arr_typ=None):
    assert isinstance(arr_typ, StructArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        zvp__ttr = _get_struct_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            zvp__ttr.data)
    return types.BaseTuple.from_types(arr_typ.data)(arr_typ), codegen


@intrinsic
def get_null_bitmap(typingctx, arr_typ=None):
    assert isinstance(arr_typ, StructArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        zvp__ttr = _get_struct_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            zvp__ttr.null_bitmap)
    return types.Array(types.uint8, 1, 'C')(arr_typ), codegen


@intrinsic
def init_struct_arr(typingctx, data_typ, null_bitmap_typ, names_typ=None):
    names = tuple(get_overload_const_str(vat__seh) for vat__seh in
        names_typ.types)
    struct_arr_type = StructArrayType(data_typ.types, names)

    def codegen(context, builder, sig, args):
        data, rcmv__lviyi, hkp__vfyyr = args
        payload_type = StructArrayPayloadType(struct_arr_type.data)
        swvr__rgvmy = context.get_value_type(payload_type)
        pla__mewxx = context.get_abi_sizeof(swvr__rgvmy)
        zgh__dezy = define_struct_arr_dtor(context, builder,
            struct_arr_type, payload_type)
        bvd__ybkde = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, pla__mewxx), zgh__dezy)
        rso__xfp = context.nrt.meminfo_data(builder, bvd__ybkde)
        fenmu__kcy = builder.bitcast(rso__xfp, swvr__rgvmy.as_pointer())
        zvp__ttr = cgutils.create_struct_proxy(payload_type)(context, builder)
        zvp__ttr.data = data
        zvp__ttr.null_bitmap = rcmv__lviyi
        builder.store(zvp__ttr._getvalue(), fenmu__kcy)
        context.nrt.incref(builder, data_typ, data)
        context.nrt.incref(builder, null_bitmap_typ, rcmv__lviyi)
        zlpa__rry = context.make_helper(builder, struct_arr_type)
        zlpa__rry.meminfo = bvd__ybkde
        return zlpa__rry._getvalue()
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
    jijwv__mnib = len(arr.data)
    kkjmf__yjvq = 'def impl(arr, ind):\n'
    kkjmf__yjvq += '  data = get_data(arr)\n'
    kkjmf__yjvq += '  null_bitmap = get_null_bitmap(arr)\n'
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        kkjmf__yjvq += """  out_null_bitmap = get_new_null_mask_bool_index(null_bitmap, ind, len(data[0]))
"""
    elif is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        kkjmf__yjvq += """  out_null_bitmap = get_new_null_mask_int_index(null_bitmap, ind, len(data[0]))
"""
    elif isinstance(ind, types.SliceType):
        kkjmf__yjvq += """  out_null_bitmap = get_new_null_mask_slice_index(null_bitmap, ind, len(data[0]))
"""
    else:
        raise BodoError('invalid index {} in struct array indexing'.format(ind)
            )
    kkjmf__yjvq += ('  return init_struct_arr(({},), out_null_bitmap, ({},))\n'
        .format(', '.join('ensure_contig_if_np(data[{}][ind])'.format(i) for
        i in range(jijwv__mnib)), ', '.join("'{}'".format(oex__fvc) for
        oex__fvc in arr.names)))
    kwt__ditgx = {}
    exec(kkjmf__yjvq, {'init_struct_arr': init_struct_arr, 'get_data':
        get_data, 'get_null_bitmap': get_null_bitmap, 'ensure_contig_if_np':
        bodo.utils.conversion.ensure_contig_if_np,
        'get_new_null_mask_bool_index': bodo.utils.indexing.
        get_new_null_mask_bool_index, 'get_new_null_mask_int_index': bodo.
        utils.indexing.get_new_null_mask_int_index,
        'get_new_null_mask_slice_index': bodo.utils.indexing.
        get_new_null_mask_slice_index}, kwt__ditgx)
    impl = kwt__ditgx['impl']
    return impl


@overload(operator.setitem, no_unliteral=True)
def struct_arr_setitem(arr, ind, val):
    if not isinstance(arr, StructArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    if isinstance(ind, types.Integer):
        jijwv__mnib = len(arr.data)
        kkjmf__yjvq = 'def impl(arr, ind, val):\n'
        kkjmf__yjvq += '  data = get_data(arr)\n'
        kkjmf__yjvq += '  null_bitmap = get_null_bitmap(arr)\n'
        kkjmf__yjvq += '  set_bit_to_arr(null_bitmap, ind, 1)\n'
        for i in range(jijwv__mnib):
            if isinstance(val, StructType):
                kkjmf__yjvq += "  if is_field_value_null(val, '{}'):\n".format(
                    arr.names[i])
                kkjmf__yjvq += (
                    '    bodo.libs.array_kernels.setna(data[{}], ind)\n'.
                    format(i))
                kkjmf__yjvq += '  else:\n'
                kkjmf__yjvq += "    data[{}][ind] = val['{}']\n".format(i,
                    arr.names[i])
            else:
                kkjmf__yjvq += "  data[{}][ind] = val['{}']\n".format(i,
                    arr.names[i])
        kwt__ditgx = {}
        exec(kkjmf__yjvq, {'bodo': bodo, 'get_data': get_data,
            'get_null_bitmap': get_null_bitmap, 'set_bit_to_arr': bodo.libs
            .int_arr_ext.set_bit_to_arr, 'is_field_value_null':
            is_field_value_null}, kwt__ditgx)
        impl = kwt__ditgx['impl']
        return impl
    if isinstance(ind, types.SliceType):
        jijwv__mnib = len(arr.data)
        kkjmf__yjvq = 'def impl(arr, ind, val):\n'
        kkjmf__yjvq += '  data = get_data(arr)\n'
        kkjmf__yjvq += '  null_bitmap = get_null_bitmap(arr)\n'
        kkjmf__yjvq += '  val_data = get_data(val)\n'
        kkjmf__yjvq += '  val_null_bitmap = get_null_bitmap(val)\n'
        kkjmf__yjvq += """  setitem_slice_index_null_bits(null_bitmap, val_null_bitmap, ind, len(arr))
"""
        for i in range(jijwv__mnib):
            kkjmf__yjvq += '  data[{0}][ind] = val_data[{0}]\n'.format(i)
        kwt__ditgx = {}
        exec(kkjmf__yjvq, {'bodo': bodo, 'get_data': get_data,
            'get_null_bitmap': get_null_bitmap, 'set_bit_to_arr': bodo.libs
            .int_arr_ext.set_bit_to_arr, 'setitem_slice_index_null_bits':
            bodo.utils.indexing.setitem_slice_index_null_bits}, kwt__ditgx)
        impl = kwt__ditgx['impl']
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
    kkjmf__yjvq = 'def impl(A):\n'
    kkjmf__yjvq += '  total_nbytes = 0\n'
    kkjmf__yjvq += '  data = get_data(A)\n'
    for i in range(len(A.data)):
        kkjmf__yjvq += f'  total_nbytes += data[{i}].nbytes\n'
    kkjmf__yjvq += '  total_nbytes += get_null_bitmap(A).nbytes\n'
    kkjmf__yjvq += '  return total_nbytes\n'
    kwt__ditgx = {}
    exec(kkjmf__yjvq, {'get_data': get_data, 'get_null_bitmap':
        get_null_bitmap}, kwt__ditgx)
    impl = kwt__ditgx['impl']
    return impl


@overload_method(StructArrayType, 'copy', no_unliteral=True)
def overload_struct_arr_copy(A):
    names = A.names

    def copy_impl(A):
        data = get_data(A)
        rcmv__lviyi = get_null_bitmap(A)
        jyz__ntb = bodo.ir.join.copy_arr_tup(data)
        dqg__ureux = rcmv__lviyi.copy()
        return init_struct_arr(jyz__ntb, dqg__ureux, names)
    return copy_impl
