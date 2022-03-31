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
            .utils.is_array_typ(abgs__odgi, False) for abgs__odgi in data)
        if names is not None:
            assert isinstance(names, tuple) and all(isinstance(abgs__odgi,
                str) for abgs__odgi in names) and len(names) == len(data)
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
        return StructType(tuple(jvtfn__fsx.dtype for jvtfn__fsx in self.
            data), self.names)

    @classmethod
    def from_dict(cls, d):
        assert isinstance(d, dict)
        names = tuple(str(abgs__odgi) for abgs__odgi in d.keys())
        data = tuple(dtype_to_array_type(jvtfn__fsx) for jvtfn__fsx in d.
            values())
        return StructArrayType(data, names)

    def copy(self):
        return StructArrayType(self.data, self.names)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


class StructArrayPayloadType(types.Type):

    def __init__(self, data):
        assert isinstance(data, tuple) and all(bodo.utils.utils.
            is_array_typ(abgs__odgi, False) for abgs__odgi in data)
        self.data = data
        super(StructArrayPayloadType, self).__init__(name=
            'StructArrayPayloadType({})'.format(data))

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(StructArrayPayloadType)
class StructArrayPayloadModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        fwt__rmao = [('data', types.BaseTuple.from_types(fe_type.data)), (
            'null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, fwt__rmao)


@register_model(StructArrayType)
class StructArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = StructArrayPayloadType(fe_type.data)
        fwt__rmao = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, fwt__rmao)


def define_struct_arr_dtor(context, builder, struct_arr_type, payload_type):
    bwflh__wzjt = builder.module
    ewt__bor = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    fftt__xyo = cgutils.get_or_insert_function(bwflh__wzjt, ewt__bor, name=
        '.dtor.struct_arr.{}.{}.'.format(struct_arr_type.data,
        struct_arr_type.names))
    if not fftt__xyo.is_declaration:
        return fftt__xyo
    fftt__xyo.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(fftt__xyo.append_basic_block())
    cpip__kiwbl = fftt__xyo.args[0]
    gsgm__uygw = context.get_value_type(payload_type).as_pointer()
    dtgtw__qaz = builder.bitcast(cpip__kiwbl, gsgm__uygw)
    rhd__huhvv = context.make_helper(builder, payload_type, ref=dtgtw__qaz)
    context.nrt.decref(builder, types.BaseTuple.from_types(struct_arr_type.
        data), rhd__huhvv.data)
    context.nrt.decref(builder, types.Array(types.uint8, 1, 'C'),
        rhd__huhvv.null_bitmap)
    builder.ret_void()
    return fftt__xyo


def construct_struct_array(context, builder, struct_arr_type, n_structs,
    n_elems, c=None):
    payload_type = StructArrayPayloadType(struct_arr_type.data)
    flc__bas = context.get_value_type(payload_type)
    cfyv__kpu = context.get_abi_sizeof(flc__bas)
    zit__porks = define_struct_arr_dtor(context, builder, struct_arr_type,
        payload_type)
    mvt__ltky = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, cfyv__kpu), zit__porks)
    dgbl__onrg = context.nrt.meminfo_data(builder, mvt__ltky)
    kjgdq__jmwn = builder.bitcast(dgbl__onrg, flc__bas.as_pointer())
    rhd__huhvv = cgutils.create_struct_proxy(payload_type)(context, builder)
    iecpv__zpww = []
    vdqv__orq = 0
    for arr_typ in struct_arr_type.data:
        wjdw__fab = bodo.utils.transform.get_type_alloc_counts(arr_typ.dtype)
        crn__ojbnl = cgutils.pack_array(builder, [n_structs] + [builder.
            extract_value(n_elems, i) for i in range(vdqv__orq, vdqv__orq +
            wjdw__fab)])
        arr = gen_allocate_array(context, builder, arr_typ, crn__ojbnl, c)
        iecpv__zpww.append(arr)
        vdqv__orq += wjdw__fab
    rhd__huhvv.data = cgutils.pack_array(builder, iecpv__zpww
        ) if types.is_homogeneous(*struct_arr_type.data
        ) else cgutils.pack_struct(builder, iecpv__zpww)
    qex__jwfug = builder.udiv(builder.add(n_structs, lir.Constant(lir.
        IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
    zhxay__kmky = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(types.uint8, 1, 'C'), [qex__jwfug])
    null_bitmap_ptr = zhxay__kmky.data
    rhd__huhvv.null_bitmap = zhxay__kmky._getvalue()
    builder.store(rhd__huhvv._getvalue(), kjgdq__jmwn)
    return mvt__ltky, rhd__huhvv.data, null_bitmap_ptr


def _get_C_API_ptrs(c, data_tup, data_typ, names):
    pdwm__ggq = []
    assert len(data_typ) > 0
    for i, arr_typ in enumerate(data_typ):
        llplb__rau = c.builder.extract_value(data_tup, i)
        arr = c.context.make_array(arr_typ)(c.context, c.builder, value=
            llplb__rau)
        pdwm__ggq.append(arr.data)
    hirm__retow = cgutils.pack_array(c.builder, pdwm__ggq
        ) if types.is_homogeneous(*data_typ) else cgutils.pack_struct(c.
        builder, pdwm__ggq)
    caxi__fkih = cgutils.alloca_once_value(c.builder, hirm__retow)
    ykhl__gmhp = [c.context.get_constant(types.int32, bodo.utils.utils.
        numba_to_c_type(abgs__odgi.dtype)) for abgs__odgi in data_typ]
    qefrr__ocxg = cgutils.alloca_once_value(c.builder, cgutils.pack_array(c
        .builder, ykhl__gmhp))
    ncqt__gjaov = cgutils.pack_array(c.builder, [c.context.
        insert_const_string(c.builder.module, abgs__odgi) for abgs__odgi in
        names])
    tjktq__xdzp = cgutils.alloca_once_value(c.builder, ncqt__gjaov)
    return caxi__fkih, qefrr__ocxg, tjktq__xdzp


@unbox(StructArrayType)
def unbox_struct_array(typ, val, c, is_tuple_array=False):
    from bodo.libs.tuple_arr_ext import TupleArrayType
    n_structs = bodo.utils.utils.object_length(c, val)
    hqkg__dlcs = all(isinstance(jvtfn__fsx, types.Array) and jvtfn__fsx.
        dtype in (types.int64, types.float64, types.bool_,
        datetime_date_type) for jvtfn__fsx in typ.data)
    if hqkg__dlcs:
        n_elems = cgutils.pack_array(c.builder, [], lir.IntType(64))
    else:
        fwf__cpnx = get_array_elem_counts(c, c.builder, c.context, val, 
            TupleArrayType(typ.data) if is_tuple_array else typ)
        n_elems = cgutils.pack_array(c.builder, [c.builder.extract_value(
            fwf__cpnx, i) for i in range(1, fwf__cpnx.type.count)], lir.
            IntType(64))
    mvt__ltky, data_tup, null_bitmap_ptr = construct_struct_array(c.context,
        c.builder, typ, n_structs, n_elems, c)
    if hqkg__dlcs:
        caxi__fkih, qefrr__ocxg, tjktq__xdzp = _get_C_API_ptrs(c, data_tup,
            typ.data, typ.names)
        ewt__bor = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(32), lir.IntType(8).as_pointer(), lir
            .IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1)])
        fftt__xyo = cgutils.get_or_insert_function(c.builder.module,
            ewt__bor, name='struct_array_from_sequence')
        c.builder.call(fftt__xyo, [val, c.context.get_constant(types.int32,
            len(typ.data)), c.builder.bitcast(caxi__fkih, lir.IntType(8).
            as_pointer()), null_bitmap_ptr, c.builder.bitcast(qefrr__ocxg,
            lir.IntType(8).as_pointer()), c.builder.bitcast(tjktq__xdzp,
            lir.IntType(8).as_pointer()), c.context.get_constant(types.
            bool_, is_tuple_array)])
    else:
        _unbox_struct_array_generic(typ, val, c, n_structs, data_tup,
            null_bitmap_ptr, is_tuple_array)
    lifzj__ffxlv = c.context.make_helper(c.builder, typ)
    lifzj__ffxlv.meminfo = mvt__ltky
    bsl__kqm = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(lifzj__ffxlv._getvalue(), is_error=bsl__kqm)


def _unbox_struct_array_generic(typ, val, c, n_structs, data_tup,
    null_bitmap_ptr, is_tuple_array=False):
    context = c.context
    builder = c.builder
    tqzk__vahjf = context.insert_const_string(builder.module, 'pandas')
    xxll__gvet = c.pyapi.import_module_noblock(tqzk__vahjf)
    bkyx__xtrb = c.pyapi.object_getattr_string(xxll__gvet, 'NA')
    with cgutils.for_range(builder, n_structs) as lyvb__yjbco:
        wywi__odn = lyvb__yjbco.index
        dyg__mhu = seq_getitem(builder, context, val, wywi__odn)
        set_bitmap_bit(builder, null_bitmap_ptr, wywi__odn, 0)
        for dufhv__vzeqk in range(len(typ.data)):
            arr_typ = typ.data[dufhv__vzeqk]
            data_arr = builder.extract_value(data_tup, dufhv__vzeqk)

            def set_na(data_arr, i):
                bodo.libs.array_kernels.setna(data_arr, i)
            sig = types.none(arr_typ, types.int64)
            anubc__gzud, kuxmk__lfhj = c.pyapi.call_jit_code(set_na, sig, [
                data_arr, wywi__odn])
        jcfiv__aqil = is_na_value(builder, context, dyg__mhu, bkyx__xtrb)
        dgm__jta = builder.icmp_unsigned('!=', jcfiv__aqil, lir.Constant(
            jcfiv__aqil.type, 1))
        with builder.if_then(dgm__jta):
            set_bitmap_bit(builder, null_bitmap_ptr, wywi__odn, 1)
            for dufhv__vzeqk in range(len(typ.data)):
                arr_typ = typ.data[dufhv__vzeqk]
                if is_tuple_array:
                    ioejv__gps = c.pyapi.tuple_getitem(dyg__mhu, dufhv__vzeqk)
                else:
                    ioejv__gps = c.pyapi.dict_getitem_string(dyg__mhu, typ.
                        names[dufhv__vzeqk])
                jcfiv__aqil = is_na_value(builder, context, ioejv__gps,
                    bkyx__xtrb)
                dgm__jta = builder.icmp_unsigned('!=', jcfiv__aqil, lir.
                    Constant(jcfiv__aqil.type, 1))
                with builder.if_then(dgm__jta):
                    ioejv__gps = to_arr_obj_if_list_obj(c, context, builder,
                        ioejv__gps, arr_typ.dtype)
                    field_val = c.pyapi.to_native_value(arr_typ.dtype,
                        ioejv__gps).value
                    data_arr = builder.extract_value(data_tup, dufhv__vzeqk)

                    def set_data(data_arr, i, field_val):
                        data_arr[i] = field_val
                    sig = types.none(arr_typ, types.int64, arr_typ.dtype)
                    anubc__gzud, kuxmk__lfhj = c.pyapi.call_jit_code(set_data,
                        sig, [data_arr, wywi__odn, field_val])
                    c.context.nrt.decref(builder, arr_typ.dtype, field_val)
        c.pyapi.decref(dyg__mhu)
    c.pyapi.decref(xxll__gvet)
    c.pyapi.decref(bkyx__xtrb)


def _get_struct_arr_payload(context, builder, arr_typ, arr):
    lifzj__ffxlv = context.make_helper(builder, arr_typ, arr)
    payload_type = StructArrayPayloadType(arr_typ.data)
    dgbl__onrg = context.nrt.meminfo_data(builder, lifzj__ffxlv.meminfo)
    kjgdq__jmwn = builder.bitcast(dgbl__onrg, context.get_value_type(
        payload_type).as_pointer())
    rhd__huhvv = cgutils.create_struct_proxy(payload_type)(context, builder,
        builder.load(kjgdq__jmwn))
    return rhd__huhvv


@box(StructArrayType)
def box_struct_arr(typ, val, c, is_tuple_array=False):
    rhd__huhvv = _get_struct_arr_payload(c.context, c.builder, typ, val)
    anubc__gzud, length = c.pyapi.call_jit_code(lambda A: len(A), types.
        int64(typ), [val])
    null_bitmap_ptr = c.context.make_helper(c.builder, types.Array(types.
        uint8, 1, 'C'), rhd__huhvv.null_bitmap).data
    hqkg__dlcs = all(isinstance(jvtfn__fsx, types.Array) and jvtfn__fsx.
        dtype in (types.int64, types.float64, types.bool_,
        datetime_date_type) for jvtfn__fsx in typ.data)
    if hqkg__dlcs:
        caxi__fkih, qefrr__ocxg, tjktq__xdzp = _get_C_API_ptrs(c,
            rhd__huhvv.data, typ.data, typ.names)
        ewt__bor = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(32), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1)])
        rzkgc__ivwuk = cgutils.get_or_insert_function(c.builder.module,
            ewt__bor, name='np_array_from_struct_array')
        arr = c.builder.call(rzkgc__ivwuk, [length, c.context.get_constant(
            types.int32, len(typ.data)), c.builder.bitcast(caxi__fkih, lir.
            IntType(8).as_pointer()), null_bitmap_ptr, c.builder.bitcast(
            qefrr__ocxg, lir.IntType(8).as_pointer()), c.builder.bitcast(
            tjktq__xdzp, lir.IntType(8).as_pointer()), c.context.
            get_constant(types.bool_, is_tuple_array)])
    else:
        arr = _box_struct_array_generic(typ, c, length, rhd__huhvv.data,
            null_bitmap_ptr, is_tuple_array)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def _box_struct_array_generic(typ, c, length, data_arrs_tup,
    null_bitmap_ptr, is_tuple_array=False):
    context = c.context
    builder = c.builder
    tqzk__vahjf = context.insert_const_string(builder.module, 'numpy')
    xpzym__bcp = c.pyapi.import_module_noblock(tqzk__vahjf)
    ftt__stux = c.pyapi.object_getattr_string(xpzym__bcp, 'object_')
    gzf__vdpav = c.pyapi.long_from_longlong(length)
    tine__orkje = c.pyapi.call_method(xpzym__bcp, 'ndarray', (gzf__vdpav,
        ftt__stux))
    lxy__sfjhy = c.pyapi.object_getattr_string(xpzym__bcp, 'nan')
    with cgutils.for_range(builder, length) as lyvb__yjbco:
        wywi__odn = lyvb__yjbco.index
        pyarray_setitem(builder, context, tine__orkje, wywi__odn, lxy__sfjhy)
        gdwn__kbe = get_bitmap_bit(builder, null_bitmap_ptr, wywi__odn)
        zucay__zafbx = builder.icmp_unsigned('!=', gdwn__kbe, lir.Constant(
            lir.IntType(8), 0))
        with builder.if_then(zucay__zafbx):
            if is_tuple_array:
                dyg__mhu = c.pyapi.tuple_new(len(typ.data))
            else:
                dyg__mhu = c.pyapi.dict_new(len(typ.data))
            for i, arr_typ in enumerate(typ.data):
                if is_tuple_array:
                    c.pyapi.incref(lxy__sfjhy)
                    c.pyapi.tuple_setitem(dyg__mhu, i, lxy__sfjhy)
                else:
                    c.pyapi.dict_setitem_string(dyg__mhu, typ.names[i],
                        lxy__sfjhy)
                data_arr = c.builder.extract_value(data_arrs_tup, i)
                anubc__gzud, mnws__ykz = c.pyapi.call_jit_code(lambda
                    data_arr, ind: not bodo.libs.array_kernels.isna(
                    data_arr, ind), types.bool_(arr_typ, types.int64), [
                    data_arr, wywi__odn])
                with builder.if_then(mnws__ykz):
                    anubc__gzud, field_val = c.pyapi.call_jit_code(lambda
                        data_arr, ind: data_arr[ind], arr_typ.dtype(arr_typ,
                        types.int64), [data_arr, wywi__odn])
                    umtba__rtisi = c.pyapi.from_native_value(arr_typ.dtype,
                        field_val, c.env_manager)
                    if is_tuple_array:
                        c.pyapi.tuple_setitem(dyg__mhu, i, umtba__rtisi)
                    else:
                        c.pyapi.dict_setitem_string(dyg__mhu, typ.names[i],
                            umtba__rtisi)
                        c.pyapi.decref(umtba__rtisi)
            pyarray_setitem(builder, context, tine__orkje, wywi__odn, dyg__mhu)
            c.pyapi.decref(dyg__mhu)
    c.pyapi.decref(xpzym__bcp)
    c.pyapi.decref(ftt__stux)
    c.pyapi.decref(gzf__vdpav)
    c.pyapi.decref(lxy__sfjhy)
    return tine__orkje


def _fix_nested_counts(nested_counts, struct_arr_type, nested_counts_type,
    builder):
    wumh__atn = bodo.utils.transform.get_type_alloc_counts(struct_arr_type) - 1
    if wumh__atn == 0:
        return nested_counts
    if not isinstance(nested_counts_type, types.UniTuple):
        nested_counts = cgutils.pack_array(builder, [lir.Constant(lir.
            IntType(64), -1) for fds__xwel in range(wumh__atn)])
    elif nested_counts_type.count < wumh__atn:
        nested_counts = cgutils.pack_array(builder, [builder.extract_value(
            nested_counts, i) for i in range(nested_counts_type.count)] + [
            lir.Constant(lir.IntType(64), -1) for fds__xwel in range(
            wumh__atn - nested_counts_type.count)])
    return nested_counts


@intrinsic
def pre_alloc_struct_array(typingctx, num_structs_typ, nested_counts_typ,
    dtypes_typ, names_typ=None):
    assert isinstance(num_structs_typ, types.Integer) and isinstance(dtypes_typ
        , types.BaseTuple)
    if is_overload_none(names_typ):
        names = tuple(f'f{i}' for i in range(len(dtypes_typ)))
    else:
        names = tuple(get_overload_const_str(jvtfn__fsx) for jvtfn__fsx in
            names_typ.types)
    ywk__lvr = tuple(jvtfn__fsx.instance_type for jvtfn__fsx in dtypes_typ.
        types)
    struct_arr_type = StructArrayType(ywk__lvr, names)

    def codegen(context, builder, sig, args):
        vaz__lcy, nested_counts, fds__xwel, fds__xwel = args
        nested_counts_type = sig.args[1]
        nested_counts = _fix_nested_counts(nested_counts, struct_arr_type,
            nested_counts_type, builder)
        mvt__ltky, fds__xwel, fds__xwel = construct_struct_array(context,
            builder, struct_arr_type, vaz__lcy, nested_counts)
        lifzj__ffxlv = context.make_helper(builder, struct_arr_type)
        lifzj__ffxlv.meminfo = mvt__ltky
        return lifzj__ffxlv._getvalue()
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
        assert isinstance(names, tuple) and all(isinstance(abgs__odgi, str) for
            abgs__odgi in names) and len(names) == len(data)
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
        fwt__rmao = [('data', types.BaseTuple.from_types(fe_type.data)), (
            'null_bitmap', types.UniTuple(types.int8, len(fe_type.data)))]
        models.StructModel.__init__(self, dmm, fe_type, fwt__rmao)


@register_model(StructType)
class StructModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = StructPayloadType(fe_type.data)
        fwt__rmao = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, fwt__rmao)


def define_struct_dtor(context, builder, struct_type, payload_type):
    bwflh__wzjt = builder.module
    ewt__bor = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    fftt__xyo = cgutils.get_or_insert_function(bwflh__wzjt, ewt__bor, name=
        '.dtor.struct.{}.{}.'.format(struct_type.data, struct_type.names))
    if not fftt__xyo.is_declaration:
        return fftt__xyo
    fftt__xyo.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(fftt__xyo.append_basic_block())
    cpip__kiwbl = fftt__xyo.args[0]
    gsgm__uygw = context.get_value_type(payload_type).as_pointer()
    dtgtw__qaz = builder.bitcast(cpip__kiwbl, gsgm__uygw)
    rhd__huhvv = context.make_helper(builder, payload_type, ref=dtgtw__qaz)
    for i in range(len(struct_type.data)):
        mlc__xvzbo = builder.extract_value(rhd__huhvv.null_bitmap, i)
        zucay__zafbx = builder.icmp_unsigned('==', mlc__xvzbo, lir.Constant
            (mlc__xvzbo.type, 1))
        with builder.if_then(zucay__zafbx):
            val = builder.extract_value(rhd__huhvv.data, i)
            context.nrt.decref(builder, struct_type.data[i], val)
    builder.ret_void()
    return fftt__xyo


def _get_struct_payload(context, builder, typ, struct):
    struct = context.make_helper(builder, typ, struct)
    payload_type = StructPayloadType(typ.data)
    dgbl__onrg = context.nrt.meminfo_data(builder, struct.meminfo)
    kjgdq__jmwn = builder.bitcast(dgbl__onrg, context.get_value_type(
        payload_type).as_pointer())
    rhd__huhvv = cgutils.create_struct_proxy(payload_type)(context, builder,
        builder.load(kjgdq__jmwn))
    return rhd__huhvv, kjgdq__jmwn


@unbox(StructType)
def unbox_struct(typ, val, c):
    context = c.context
    builder = c.builder
    tqzk__vahjf = context.insert_const_string(builder.module, 'pandas')
    xxll__gvet = c.pyapi.import_module_noblock(tqzk__vahjf)
    bkyx__xtrb = c.pyapi.object_getattr_string(xxll__gvet, 'NA')
    zeigq__adtk = []
    nulls = []
    for i, jvtfn__fsx in enumerate(typ.data):
        umtba__rtisi = c.pyapi.dict_getitem_string(val, typ.names[i])
        qdwm__ykvtz = cgutils.alloca_once_value(c.builder, context.
            get_constant(types.uint8, 0))
        uopv__pegu = cgutils.alloca_once_value(c.builder, cgutils.
            get_null_value(context.get_value_type(jvtfn__fsx)))
        jcfiv__aqil = is_na_value(builder, context, umtba__rtisi, bkyx__xtrb)
        zucay__zafbx = builder.icmp_unsigned('!=', jcfiv__aqil, lir.
            Constant(jcfiv__aqil.type, 1))
        with builder.if_then(zucay__zafbx):
            builder.store(context.get_constant(types.uint8, 1), qdwm__ykvtz)
            field_val = c.pyapi.to_native_value(jvtfn__fsx, umtba__rtisi).value
            builder.store(field_val, uopv__pegu)
        zeigq__adtk.append(builder.load(uopv__pegu))
        nulls.append(builder.load(qdwm__ykvtz))
    c.pyapi.decref(xxll__gvet)
    c.pyapi.decref(bkyx__xtrb)
    mvt__ltky = construct_struct(context, builder, typ, zeigq__adtk, nulls)
    struct = context.make_helper(builder, typ)
    struct.meminfo = mvt__ltky
    bsl__kqm = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(struct._getvalue(), is_error=bsl__kqm)


@box(StructType)
def box_struct(typ, val, c):
    jqoy__ish = c.pyapi.dict_new(len(typ.data))
    rhd__huhvv, fds__xwel = _get_struct_payload(c.context, c.builder, typ, val)
    assert len(typ.data) > 0
    for i, val_typ in enumerate(typ.data):
        c.pyapi.dict_setitem_string(jqoy__ish, typ.names[i], c.pyapi.
            borrow_none())
        mlc__xvzbo = c.builder.extract_value(rhd__huhvv.null_bitmap, i)
        zucay__zafbx = c.builder.icmp_unsigned('==', mlc__xvzbo, lir.
            Constant(mlc__xvzbo.type, 1))
        with c.builder.if_then(zucay__zafbx):
            evh__utk = c.builder.extract_value(rhd__huhvv.data, i)
            c.context.nrt.incref(c.builder, val_typ, evh__utk)
            ioejv__gps = c.pyapi.from_native_value(val_typ, evh__utk, c.
                env_manager)
            c.pyapi.dict_setitem_string(jqoy__ish, typ.names[i], ioejv__gps)
            c.pyapi.decref(ioejv__gps)
    c.context.nrt.decref(c.builder, typ, val)
    return jqoy__ish


@intrinsic
def init_struct(typingctx, data_typ, names_typ=None):
    names = tuple(get_overload_const_str(jvtfn__fsx) for jvtfn__fsx in
        names_typ.types)
    struct_type = StructType(data_typ.types, names)

    def codegen(context, builder, sig, args):
        data, zwgrj__bxdv = args
        payload_type = StructPayloadType(struct_type.data)
        flc__bas = context.get_value_type(payload_type)
        cfyv__kpu = context.get_abi_sizeof(flc__bas)
        zit__porks = define_struct_dtor(context, builder, struct_type,
            payload_type)
        mvt__ltky = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, cfyv__kpu), zit__porks)
        dgbl__onrg = context.nrt.meminfo_data(builder, mvt__ltky)
        kjgdq__jmwn = builder.bitcast(dgbl__onrg, flc__bas.as_pointer())
        rhd__huhvv = cgutils.create_struct_proxy(payload_type)(context, builder
            )
        rhd__huhvv.data = data
        rhd__huhvv.null_bitmap = cgutils.pack_array(builder, [context.
            get_constant(types.uint8, 1) for fds__xwel in range(len(
            data_typ.types))])
        builder.store(rhd__huhvv._getvalue(), kjgdq__jmwn)
        context.nrt.incref(builder, data_typ, data)
        struct = context.make_helper(builder, struct_type)
        struct.meminfo = mvt__ltky
        return struct._getvalue()
    return struct_type(data_typ, names_typ), codegen


@intrinsic
def get_struct_data(typingctx, struct_typ=None):
    assert isinstance(struct_typ, StructType)

    def codegen(context, builder, sig, args):
        struct, = args
        rhd__huhvv, fds__xwel = _get_struct_payload(context, builder,
            struct_typ, struct)
        return impl_ret_borrowed(context, builder, sig.return_type,
            rhd__huhvv.data)
    return types.BaseTuple.from_types(struct_typ.data)(struct_typ), codegen


@intrinsic
def get_struct_null_bitmap(typingctx, struct_typ=None):
    assert isinstance(struct_typ, StructType)

    def codegen(context, builder, sig, args):
        struct, = args
        rhd__huhvv, fds__xwel = _get_struct_payload(context, builder,
            struct_typ, struct)
        return impl_ret_borrowed(context, builder, sig.return_type,
            rhd__huhvv.null_bitmap)
    zjk__tuxnh = types.UniTuple(types.int8, len(struct_typ.data))
    return zjk__tuxnh(struct_typ), codegen


@intrinsic
def set_struct_data(typingctx, struct_typ, field_ind_typ, val_typ=None):
    assert isinstance(struct_typ, StructType) and is_overload_constant_int(
        field_ind_typ)
    field_ind = get_overload_const_int(field_ind_typ)

    def codegen(context, builder, sig, args):
        struct, fds__xwel, val = args
        rhd__huhvv, kjgdq__jmwn = _get_struct_payload(context, builder,
            struct_typ, struct)
        dlwz__ivmsm = rhd__huhvv.data
        ntl__sxz = builder.insert_value(dlwz__ivmsm, val, field_ind)
        thtv__xyomj = types.BaseTuple.from_types(struct_typ.data)
        context.nrt.decref(builder, thtv__xyomj, dlwz__ivmsm)
        context.nrt.incref(builder, thtv__xyomj, ntl__sxz)
        rhd__huhvv.data = ntl__sxz
        builder.store(rhd__huhvv._getvalue(), kjgdq__jmwn)
        return context.get_dummy_value()
    return types.none(struct_typ, field_ind_typ, val_typ), codegen


def _get_struct_field_ind(struct, ind, op):
    if not is_overload_constant_str(ind):
        raise BodoError(
            'structs (from struct array) only support constant strings for {}, not {}'
            .format(op, ind))
    lsrkn__oaem = get_overload_const_str(ind)
    if lsrkn__oaem not in struct.names:
        raise BodoError('Field {} does not exist in struct {}'.format(
            lsrkn__oaem, struct))
    return struct.names.index(lsrkn__oaem)


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
    flc__bas = context.get_value_type(payload_type)
    cfyv__kpu = context.get_abi_sizeof(flc__bas)
    zit__porks = define_struct_dtor(context, builder, struct_type, payload_type
        )
    mvt__ltky = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, cfyv__kpu), zit__porks)
    dgbl__onrg = context.nrt.meminfo_data(builder, mvt__ltky)
    kjgdq__jmwn = builder.bitcast(dgbl__onrg, flc__bas.as_pointer())
    rhd__huhvv = cgutils.create_struct_proxy(payload_type)(context, builder)
    rhd__huhvv.data = cgutils.pack_array(builder, values
        ) if types.is_homogeneous(*struct_type.data) else cgutils.pack_struct(
        builder, values)
    rhd__huhvv.null_bitmap = cgutils.pack_array(builder, nulls)
    builder.store(rhd__huhvv._getvalue(), kjgdq__jmwn)
    return mvt__ltky


@intrinsic
def struct_array_get_struct(typingctx, struct_arr_typ, ind_typ=None):
    assert isinstance(struct_arr_typ, StructArrayType) and isinstance(ind_typ,
        types.Integer)
    czx__gbx = tuple(d.dtype for d in struct_arr_typ.data)
    tdjqg__iwif = StructType(czx__gbx, struct_arr_typ.names)

    def codegen(context, builder, sig, args):
        ehf__bjh, ind = args
        rhd__huhvv = _get_struct_arr_payload(context, builder,
            struct_arr_typ, ehf__bjh)
        zeigq__adtk = []
        wxv__qkntj = []
        for i, arr_typ in enumerate(struct_arr_typ.data):
            llplb__rau = builder.extract_value(rhd__huhvv.data, i)
            olkxm__hqxo = context.compile_internal(builder, lambda arr, ind:
                np.uint8(0) if bodo.libs.array_kernels.isna(arr, ind) else
                np.uint8(1), types.uint8(arr_typ, types.int64), [llplb__rau,
                ind])
            wxv__qkntj.append(olkxm__hqxo)
            czjz__yhf = cgutils.alloca_once_value(builder, context.
                get_constant_null(arr_typ.dtype))
            zucay__zafbx = builder.icmp_unsigned('==', olkxm__hqxo, lir.
                Constant(olkxm__hqxo.type, 1))
            with builder.if_then(zucay__zafbx):
                evn__tloa = context.compile_internal(builder, lambda arr,
                    ind: arr[ind], arr_typ.dtype(arr_typ, types.int64), [
                    llplb__rau, ind])
                builder.store(evn__tloa, czjz__yhf)
            zeigq__adtk.append(builder.load(czjz__yhf))
        if isinstance(tdjqg__iwif, types.DictType):
            jpsq__she = [context.insert_const_string(builder.module,
                ycvzb__aqvog) for ycvzb__aqvog in struct_arr_typ.names]
            xrel__anxw = cgutils.pack_array(builder, zeigq__adtk)
            gox__guxgc = cgutils.pack_array(builder, jpsq__she)

            def impl(names, vals):
                d = {}
                for i, ycvzb__aqvog in enumerate(names):
                    d[ycvzb__aqvog] = vals[i]
                return d
            ias__rme = context.compile_internal(builder, impl, tdjqg__iwif(
                types.Tuple(tuple(types.StringLiteral(ycvzb__aqvog) for
                ycvzb__aqvog in struct_arr_typ.names)), types.Tuple(
                czx__gbx)), [gox__guxgc, xrel__anxw])
            context.nrt.decref(builder, types.BaseTuple.from_types(czx__gbx
                ), xrel__anxw)
            return ias__rme
        mvt__ltky = construct_struct(context, builder, tdjqg__iwif,
            zeigq__adtk, wxv__qkntj)
        struct = context.make_helper(builder, tdjqg__iwif)
        struct.meminfo = mvt__ltky
        return struct._getvalue()
    return tdjqg__iwif(struct_arr_typ, ind_typ), codegen


@intrinsic
def get_data(typingctx, arr_typ=None):
    assert isinstance(arr_typ, StructArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        rhd__huhvv = _get_struct_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            rhd__huhvv.data)
    return types.BaseTuple.from_types(arr_typ.data)(arr_typ), codegen


@intrinsic
def get_null_bitmap(typingctx, arr_typ=None):
    assert isinstance(arr_typ, StructArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        rhd__huhvv = _get_struct_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            rhd__huhvv.null_bitmap)
    return types.Array(types.uint8, 1, 'C')(arr_typ), codegen


@intrinsic
def init_struct_arr(typingctx, data_typ, null_bitmap_typ, names_typ=None):
    names = tuple(get_overload_const_str(jvtfn__fsx) for jvtfn__fsx in
        names_typ.types)
    struct_arr_type = StructArrayType(data_typ.types, names)

    def codegen(context, builder, sig, args):
        data, zhxay__kmky, zwgrj__bxdv = args
        payload_type = StructArrayPayloadType(struct_arr_type.data)
        flc__bas = context.get_value_type(payload_type)
        cfyv__kpu = context.get_abi_sizeof(flc__bas)
        zit__porks = define_struct_arr_dtor(context, builder,
            struct_arr_type, payload_type)
        mvt__ltky = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, cfyv__kpu), zit__porks)
        dgbl__onrg = context.nrt.meminfo_data(builder, mvt__ltky)
        kjgdq__jmwn = builder.bitcast(dgbl__onrg, flc__bas.as_pointer())
        rhd__huhvv = cgutils.create_struct_proxy(payload_type)(context, builder
            )
        rhd__huhvv.data = data
        rhd__huhvv.null_bitmap = zhxay__kmky
        builder.store(rhd__huhvv._getvalue(), kjgdq__jmwn)
        context.nrt.incref(builder, data_typ, data)
        context.nrt.incref(builder, null_bitmap_typ, zhxay__kmky)
        lifzj__ffxlv = context.make_helper(builder, struct_arr_type)
        lifzj__ffxlv.meminfo = mvt__ltky
        return lifzj__ffxlv._getvalue()
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
    mrbh__xkakd = len(arr.data)
    atn__cdfj = 'def impl(arr, ind):\n'
    atn__cdfj += '  data = get_data(arr)\n'
    atn__cdfj += '  null_bitmap = get_null_bitmap(arr)\n'
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        atn__cdfj += """  out_null_bitmap = get_new_null_mask_bool_index(null_bitmap, ind, len(data[0]))
"""
    elif is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        atn__cdfj += """  out_null_bitmap = get_new_null_mask_int_index(null_bitmap, ind, len(data[0]))
"""
    elif isinstance(ind, types.SliceType):
        atn__cdfj += """  out_null_bitmap = get_new_null_mask_slice_index(null_bitmap, ind, len(data[0]))
"""
    else:
        raise BodoError('invalid index {} in struct array indexing'.format(ind)
            )
    atn__cdfj += ('  return init_struct_arr(({},), out_null_bitmap, ({},))\n'
        .format(', '.join('ensure_contig_if_np(data[{}][ind])'.format(i) for
        i in range(mrbh__xkakd)), ', '.join("'{}'".format(ycvzb__aqvog) for
        ycvzb__aqvog in arr.names)))
    srl__hqkl = {}
    exec(atn__cdfj, {'init_struct_arr': init_struct_arr, 'get_data':
        get_data, 'get_null_bitmap': get_null_bitmap, 'ensure_contig_if_np':
        bodo.utils.conversion.ensure_contig_if_np,
        'get_new_null_mask_bool_index': bodo.utils.indexing.
        get_new_null_mask_bool_index, 'get_new_null_mask_int_index': bodo.
        utils.indexing.get_new_null_mask_int_index,
        'get_new_null_mask_slice_index': bodo.utils.indexing.
        get_new_null_mask_slice_index}, srl__hqkl)
    impl = srl__hqkl['impl']
    return impl


@overload(operator.setitem, no_unliteral=True)
def struct_arr_setitem(arr, ind, val):
    if not isinstance(arr, StructArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    if isinstance(ind, types.Integer):
        mrbh__xkakd = len(arr.data)
        atn__cdfj = 'def impl(arr, ind, val):\n'
        atn__cdfj += '  data = get_data(arr)\n'
        atn__cdfj += '  null_bitmap = get_null_bitmap(arr)\n'
        atn__cdfj += '  set_bit_to_arr(null_bitmap, ind, 1)\n'
        for i in range(mrbh__xkakd):
            if isinstance(val, StructType):
                atn__cdfj += "  if is_field_value_null(val, '{}'):\n".format(
                    arr.names[i])
                atn__cdfj += (
                    '    bodo.libs.array_kernels.setna(data[{}], ind)\n'.
                    format(i))
                atn__cdfj += '  else:\n'
                atn__cdfj += "    data[{}][ind] = val['{}']\n".format(i,
                    arr.names[i])
            else:
                atn__cdfj += "  data[{}][ind] = val['{}']\n".format(i, arr.
                    names[i])
        srl__hqkl = {}
        exec(atn__cdfj, {'bodo': bodo, 'get_data': get_data,
            'get_null_bitmap': get_null_bitmap, 'set_bit_to_arr': bodo.libs
            .int_arr_ext.set_bit_to_arr, 'is_field_value_null':
            is_field_value_null}, srl__hqkl)
        impl = srl__hqkl['impl']
        return impl
    if isinstance(ind, types.SliceType):
        mrbh__xkakd = len(arr.data)
        atn__cdfj = 'def impl(arr, ind, val):\n'
        atn__cdfj += '  data = get_data(arr)\n'
        atn__cdfj += '  null_bitmap = get_null_bitmap(arr)\n'
        atn__cdfj += '  val_data = get_data(val)\n'
        atn__cdfj += '  val_null_bitmap = get_null_bitmap(val)\n'
        atn__cdfj += """  setitem_slice_index_null_bits(null_bitmap, val_null_bitmap, ind, len(arr))
"""
        for i in range(mrbh__xkakd):
            atn__cdfj += '  data[{0}][ind] = val_data[{0}]\n'.format(i)
        srl__hqkl = {}
        exec(atn__cdfj, {'bodo': bodo, 'get_data': get_data,
            'get_null_bitmap': get_null_bitmap, 'set_bit_to_arr': bodo.libs
            .int_arr_ext.set_bit_to_arr, 'setitem_slice_index_null_bits':
            bodo.utils.indexing.setitem_slice_index_null_bits}, srl__hqkl)
        impl = srl__hqkl['impl']
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
    atn__cdfj = 'def impl(A):\n'
    atn__cdfj += '  total_nbytes = 0\n'
    atn__cdfj += '  data = get_data(A)\n'
    for i in range(len(A.data)):
        atn__cdfj += f'  total_nbytes += data[{i}].nbytes\n'
    atn__cdfj += '  total_nbytes += get_null_bitmap(A).nbytes\n'
    atn__cdfj += '  return total_nbytes\n'
    srl__hqkl = {}
    exec(atn__cdfj, {'get_data': get_data, 'get_null_bitmap':
        get_null_bitmap}, srl__hqkl)
    impl = srl__hqkl['impl']
    return impl


@overload_method(StructArrayType, 'copy', no_unliteral=True)
def overload_struct_arr_copy(A):
    names = A.names

    def copy_impl(A):
        data = get_data(A)
        zhxay__kmky = get_null_bitmap(A)
        wryn__innit = bodo.ir.join.copy_arr_tup(data)
        tbb__gkpx = zhxay__kmky.copy()
        return init_struct_arr(wryn__innit, tbb__gkpx, names)
    return copy_impl
