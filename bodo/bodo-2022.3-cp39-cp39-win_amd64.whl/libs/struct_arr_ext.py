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
            .utils.is_array_typ(jweb__uuda, False) for jweb__uuda in data)
        if names is not None:
            assert isinstance(names, tuple) and all(isinstance(jweb__uuda,
                str) for jweb__uuda in names) and len(names) == len(data)
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
        return StructType(tuple(jfwd__iiwoo.dtype for jfwd__iiwoo in self.
            data), self.names)

    @classmethod
    def from_dict(cls, d):
        assert isinstance(d, dict)
        names = tuple(str(jweb__uuda) for jweb__uuda in d.keys())
        data = tuple(dtype_to_array_type(jfwd__iiwoo) for jfwd__iiwoo in d.
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
            is_array_typ(jweb__uuda, False) for jweb__uuda in data)
        self.data = data
        super(StructArrayPayloadType, self).__init__(name=
            'StructArrayPayloadType({})'.format(data))

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(StructArrayPayloadType)
class StructArrayPayloadModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        bhai__trkk = [('data', types.BaseTuple.from_types(fe_type.data)), (
            'null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, bhai__trkk)


@register_model(StructArrayType)
class StructArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = StructArrayPayloadType(fe_type.data)
        bhai__trkk = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, bhai__trkk)


def define_struct_arr_dtor(context, builder, struct_arr_type, payload_type):
    diimp__caee = builder.module
    svyw__gwr = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    vtue__vpjnd = cgutils.get_or_insert_function(diimp__caee, svyw__gwr,
        name='.dtor.struct_arr.{}.{}.'.format(struct_arr_type.data,
        struct_arr_type.names))
    if not vtue__vpjnd.is_declaration:
        return vtue__vpjnd
    vtue__vpjnd.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(vtue__vpjnd.append_basic_block())
    bddwh__byomg = vtue__vpjnd.args[0]
    mciff__gwibn = context.get_value_type(payload_type).as_pointer()
    jeua__hxpy = builder.bitcast(bddwh__byomg, mciff__gwibn)
    hmxg__fzfib = context.make_helper(builder, payload_type, ref=jeua__hxpy)
    context.nrt.decref(builder, types.BaseTuple.from_types(struct_arr_type.
        data), hmxg__fzfib.data)
    context.nrt.decref(builder, types.Array(types.uint8, 1, 'C'),
        hmxg__fzfib.null_bitmap)
    builder.ret_void()
    return vtue__vpjnd


def construct_struct_array(context, builder, struct_arr_type, n_structs,
    n_elems, c=None):
    payload_type = StructArrayPayloadType(struct_arr_type.data)
    kfjpg__ebhg = context.get_value_type(payload_type)
    vqzrg__xirc = context.get_abi_sizeof(kfjpg__ebhg)
    mffu__qlnn = define_struct_arr_dtor(context, builder, struct_arr_type,
        payload_type)
    xmagr__ogxx = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, vqzrg__xirc), mffu__qlnn)
    ungf__cdrft = context.nrt.meminfo_data(builder, xmagr__ogxx)
    feohl__wrfiv = builder.bitcast(ungf__cdrft, kfjpg__ebhg.as_pointer())
    hmxg__fzfib = cgutils.create_struct_proxy(payload_type)(context, builder)
    sikmn__hlte = []
    fnppn__blfpk = 0
    for arr_typ in struct_arr_type.data:
        hsx__uzte = bodo.utils.transform.get_type_alloc_counts(arr_typ.dtype)
        kmfe__wauxz = cgutils.pack_array(builder, [n_structs] + [builder.
            extract_value(n_elems, i) for i in range(fnppn__blfpk, 
            fnppn__blfpk + hsx__uzte)])
        arr = gen_allocate_array(context, builder, arr_typ, kmfe__wauxz, c)
        sikmn__hlte.append(arr)
        fnppn__blfpk += hsx__uzte
    hmxg__fzfib.data = cgutils.pack_array(builder, sikmn__hlte
        ) if types.is_homogeneous(*struct_arr_type.data
        ) else cgutils.pack_struct(builder, sikmn__hlte)
    hnqtf__akcdj = builder.udiv(builder.add(n_structs, lir.Constant(lir.
        IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
    ychdj__oxywp = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(types.uint8, 1, 'C'), [hnqtf__akcdj])
    null_bitmap_ptr = ychdj__oxywp.data
    hmxg__fzfib.null_bitmap = ychdj__oxywp._getvalue()
    builder.store(hmxg__fzfib._getvalue(), feohl__wrfiv)
    return xmagr__ogxx, hmxg__fzfib.data, null_bitmap_ptr


def _get_C_API_ptrs(c, data_tup, data_typ, names):
    qubr__ezlo = []
    assert len(data_typ) > 0
    for i, arr_typ in enumerate(data_typ):
        vxje__kgpor = c.builder.extract_value(data_tup, i)
        arr = c.context.make_array(arr_typ)(c.context, c.builder, value=
            vxje__kgpor)
        qubr__ezlo.append(arr.data)
    mbdvn__oqm = cgutils.pack_array(c.builder, qubr__ezlo
        ) if types.is_homogeneous(*data_typ) else cgutils.pack_struct(c.
        builder, qubr__ezlo)
    omxn__bhi = cgutils.alloca_once_value(c.builder, mbdvn__oqm)
    urr__mrd = [c.context.get_constant(types.int32, bodo.utils.utils.
        numba_to_c_type(jweb__uuda.dtype)) for jweb__uuda in data_typ]
    yapmg__hgtxe = cgutils.alloca_once_value(c.builder, cgutils.pack_array(
        c.builder, urr__mrd))
    jlqsd__mnr = cgutils.pack_array(c.builder, [c.context.
        insert_const_string(c.builder.module, jweb__uuda) for jweb__uuda in
        names])
    bvsf__dewv = cgutils.alloca_once_value(c.builder, jlqsd__mnr)
    return omxn__bhi, yapmg__hgtxe, bvsf__dewv


@unbox(StructArrayType)
def unbox_struct_array(typ, val, c, is_tuple_array=False):
    from bodo.libs.tuple_arr_ext import TupleArrayType
    n_structs = bodo.utils.utils.object_length(c, val)
    fiyhi__rdkl = all(isinstance(jfwd__iiwoo, types.Array) and jfwd__iiwoo.
        dtype in (types.int64, types.float64, types.bool_,
        datetime_date_type) for jfwd__iiwoo in typ.data)
    if fiyhi__rdkl:
        n_elems = cgutils.pack_array(c.builder, [], lir.IntType(64))
    else:
        oqoe__xbu = get_array_elem_counts(c, c.builder, c.context, val, 
            TupleArrayType(typ.data) if is_tuple_array else typ)
        n_elems = cgutils.pack_array(c.builder, [c.builder.extract_value(
            oqoe__xbu, i) for i in range(1, oqoe__xbu.type.count)], lir.
            IntType(64))
    xmagr__ogxx, data_tup, null_bitmap_ptr = construct_struct_array(c.
        context, c.builder, typ, n_structs, n_elems, c)
    if fiyhi__rdkl:
        omxn__bhi, yapmg__hgtxe, bvsf__dewv = _get_C_API_ptrs(c, data_tup,
            typ.data, typ.names)
        svyw__gwr = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(32), lir.IntType(8).as_pointer(), lir
            .IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1)])
        vtue__vpjnd = cgutils.get_or_insert_function(c.builder.module,
            svyw__gwr, name='struct_array_from_sequence')
        c.builder.call(vtue__vpjnd, [val, c.context.get_constant(types.
            int32, len(typ.data)), c.builder.bitcast(omxn__bhi, lir.IntType
            (8).as_pointer()), null_bitmap_ptr, c.builder.bitcast(
            yapmg__hgtxe, lir.IntType(8).as_pointer()), c.builder.bitcast(
            bvsf__dewv, lir.IntType(8).as_pointer()), c.context.
            get_constant(types.bool_, is_tuple_array)])
    else:
        _unbox_struct_array_generic(typ, val, c, n_structs, data_tup,
            null_bitmap_ptr, is_tuple_array)
    huof__feej = c.context.make_helper(c.builder, typ)
    huof__feej.meminfo = xmagr__ogxx
    pacf__ybkp = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(huof__feej._getvalue(), is_error=pacf__ybkp)


def _unbox_struct_array_generic(typ, val, c, n_structs, data_tup,
    null_bitmap_ptr, is_tuple_array=False):
    context = c.context
    builder = c.builder
    zuhf__jwto = context.insert_const_string(builder.module, 'pandas')
    omj__edffy = c.pyapi.import_module_noblock(zuhf__jwto)
    xayh__wmgq = c.pyapi.object_getattr_string(omj__edffy, 'NA')
    with cgutils.for_range(builder, n_structs) as grvn__awi:
        xib__cbaku = grvn__awi.index
        oyr__scfoq = seq_getitem(builder, context, val, xib__cbaku)
        set_bitmap_bit(builder, null_bitmap_ptr, xib__cbaku, 0)
        for wfr__puhvd in range(len(typ.data)):
            arr_typ = typ.data[wfr__puhvd]
            data_arr = builder.extract_value(data_tup, wfr__puhvd)

            def set_na(data_arr, i):
                bodo.libs.array_kernels.setna(data_arr, i)
            sig = types.none(arr_typ, types.int64)
            ogeve__dgx, toi__tlhkf = c.pyapi.call_jit_code(set_na, sig, [
                data_arr, xib__cbaku])
        ato__eory = is_na_value(builder, context, oyr__scfoq, xayh__wmgq)
        wfwf__ldkvs = builder.icmp_unsigned('!=', ato__eory, lir.Constant(
            ato__eory.type, 1))
        with builder.if_then(wfwf__ldkvs):
            set_bitmap_bit(builder, null_bitmap_ptr, xib__cbaku, 1)
            for wfr__puhvd in range(len(typ.data)):
                arr_typ = typ.data[wfr__puhvd]
                if is_tuple_array:
                    efvb__ffzr = c.pyapi.tuple_getitem(oyr__scfoq, wfr__puhvd)
                else:
                    efvb__ffzr = c.pyapi.dict_getitem_string(oyr__scfoq,
                        typ.names[wfr__puhvd])
                ato__eory = is_na_value(builder, context, efvb__ffzr,
                    xayh__wmgq)
                wfwf__ldkvs = builder.icmp_unsigned('!=', ato__eory, lir.
                    Constant(ato__eory.type, 1))
                with builder.if_then(wfwf__ldkvs):
                    efvb__ffzr = to_arr_obj_if_list_obj(c, context, builder,
                        efvb__ffzr, arr_typ.dtype)
                    field_val = c.pyapi.to_native_value(arr_typ.dtype,
                        efvb__ffzr).value
                    data_arr = builder.extract_value(data_tup, wfr__puhvd)

                    def set_data(data_arr, i, field_val):
                        data_arr[i] = field_val
                    sig = types.none(arr_typ, types.int64, arr_typ.dtype)
                    ogeve__dgx, toi__tlhkf = c.pyapi.call_jit_code(set_data,
                        sig, [data_arr, xib__cbaku, field_val])
                    c.context.nrt.decref(builder, arr_typ.dtype, field_val)
        c.pyapi.decref(oyr__scfoq)
    c.pyapi.decref(omj__edffy)
    c.pyapi.decref(xayh__wmgq)


def _get_struct_arr_payload(context, builder, arr_typ, arr):
    huof__feej = context.make_helper(builder, arr_typ, arr)
    payload_type = StructArrayPayloadType(arr_typ.data)
    ungf__cdrft = context.nrt.meminfo_data(builder, huof__feej.meminfo)
    feohl__wrfiv = builder.bitcast(ungf__cdrft, context.get_value_type(
        payload_type).as_pointer())
    hmxg__fzfib = cgutils.create_struct_proxy(payload_type)(context,
        builder, builder.load(feohl__wrfiv))
    return hmxg__fzfib


@box(StructArrayType)
def box_struct_arr(typ, val, c, is_tuple_array=False):
    hmxg__fzfib = _get_struct_arr_payload(c.context, c.builder, typ, val)
    ogeve__dgx, length = c.pyapi.call_jit_code(lambda A: len(A), types.
        int64(typ), [val])
    null_bitmap_ptr = c.context.make_helper(c.builder, types.Array(types.
        uint8, 1, 'C'), hmxg__fzfib.null_bitmap).data
    fiyhi__rdkl = all(isinstance(jfwd__iiwoo, types.Array) and jfwd__iiwoo.
        dtype in (types.int64, types.float64, types.bool_,
        datetime_date_type) for jfwd__iiwoo in typ.data)
    if fiyhi__rdkl:
        omxn__bhi, yapmg__hgtxe, bvsf__dewv = _get_C_API_ptrs(c,
            hmxg__fzfib.data, typ.data, typ.names)
        svyw__gwr = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(32), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1)])
        yij__xnzyc = cgutils.get_or_insert_function(c.builder.module,
            svyw__gwr, name='np_array_from_struct_array')
        arr = c.builder.call(yij__xnzyc, [length, c.context.get_constant(
            types.int32, len(typ.data)), c.builder.bitcast(omxn__bhi, lir.
            IntType(8).as_pointer()), null_bitmap_ptr, c.builder.bitcast(
            yapmg__hgtxe, lir.IntType(8).as_pointer()), c.builder.bitcast(
            bvsf__dewv, lir.IntType(8).as_pointer()), c.context.
            get_constant(types.bool_, is_tuple_array)])
    else:
        arr = _box_struct_array_generic(typ, c, length, hmxg__fzfib.data,
            null_bitmap_ptr, is_tuple_array)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def _box_struct_array_generic(typ, c, length, data_arrs_tup,
    null_bitmap_ptr, is_tuple_array=False):
    context = c.context
    builder = c.builder
    zuhf__jwto = context.insert_const_string(builder.module, 'numpy')
    wqk__fhlz = c.pyapi.import_module_noblock(zuhf__jwto)
    vhu__wpmau = c.pyapi.object_getattr_string(wqk__fhlz, 'object_')
    xhls__ksxex = c.pyapi.long_from_longlong(length)
    yxhoo__iptwk = c.pyapi.call_method(wqk__fhlz, 'ndarray', (xhls__ksxex,
        vhu__wpmau))
    etueb__aytv = c.pyapi.object_getattr_string(wqk__fhlz, 'nan')
    with cgutils.for_range(builder, length) as grvn__awi:
        xib__cbaku = grvn__awi.index
        pyarray_setitem(builder, context, yxhoo__iptwk, xib__cbaku, etueb__aytv
            )
        fnau__wurq = get_bitmap_bit(builder, null_bitmap_ptr, xib__cbaku)
        vbyf__fkju = builder.icmp_unsigned('!=', fnau__wurq, lir.Constant(
            lir.IntType(8), 0))
        with builder.if_then(vbyf__fkju):
            if is_tuple_array:
                oyr__scfoq = c.pyapi.tuple_new(len(typ.data))
            else:
                oyr__scfoq = c.pyapi.dict_new(len(typ.data))
            for i, arr_typ in enumerate(typ.data):
                if is_tuple_array:
                    c.pyapi.incref(etueb__aytv)
                    c.pyapi.tuple_setitem(oyr__scfoq, i, etueb__aytv)
                else:
                    c.pyapi.dict_setitem_string(oyr__scfoq, typ.names[i],
                        etueb__aytv)
                data_arr = c.builder.extract_value(data_arrs_tup, i)
                ogeve__dgx, xpj__uglai = c.pyapi.call_jit_code(lambda
                    data_arr, ind: not bodo.libs.array_kernels.isna(
                    data_arr, ind), types.bool_(arr_typ, types.int64), [
                    data_arr, xib__cbaku])
                with builder.if_then(xpj__uglai):
                    ogeve__dgx, field_val = c.pyapi.call_jit_code(lambda
                        data_arr, ind: data_arr[ind], arr_typ.dtype(arr_typ,
                        types.int64), [data_arr, xib__cbaku])
                    tks__xky = c.pyapi.from_native_value(arr_typ.dtype,
                        field_val, c.env_manager)
                    if is_tuple_array:
                        c.pyapi.tuple_setitem(oyr__scfoq, i, tks__xky)
                    else:
                        c.pyapi.dict_setitem_string(oyr__scfoq, typ.names[i
                            ], tks__xky)
                        c.pyapi.decref(tks__xky)
            pyarray_setitem(builder, context, yxhoo__iptwk, xib__cbaku,
                oyr__scfoq)
            c.pyapi.decref(oyr__scfoq)
    c.pyapi.decref(wqk__fhlz)
    c.pyapi.decref(vhu__wpmau)
    c.pyapi.decref(xhls__ksxex)
    c.pyapi.decref(etueb__aytv)
    return yxhoo__iptwk


def _fix_nested_counts(nested_counts, struct_arr_type, nested_counts_type,
    builder):
    krb__wherf = bodo.utils.transform.get_type_alloc_counts(struct_arr_type
        ) - 1
    if krb__wherf == 0:
        return nested_counts
    if not isinstance(nested_counts_type, types.UniTuple):
        nested_counts = cgutils.pack_array(builder, [lir.Constant(lir.
            IntType(64), -1) for yrx__sirg in range(krb__wherf)])
    elif nested_counts_type.count < krb__wherf:
        nested_counts = cgutils.pack_array(builder, [builder.extract_value(
            nested_counts, i) for i in range(nested_counts_type.count)] + [
            lir.Constant(lir.IntType(64), -1) for yrx__sirg in range(
            krb__wherf - nested_counts_type.count)])
    return nested_counts


@intrinsic
def pre_alloc_struct_array(typingctx, num_structs_typ, nested_counts_typ,
    dtypes_typ, names_typ=None):
    assert isinstance(num_structs_typ, types.Integer) and isinstance(dtypes_typ
        , types.BaseTuple)
    if is_overload_none(names_typ):
        names = tuple(f'f{i}' for i in range(len(dtypes_typ)))
    else:
        names = tuple(get_overload_const_str(jfwd__iiwoo) for jfwd__iiwoo in
            names_typ.types)
    brq__daswm = tuple(jfwd__iiwoo.instance_type for jfwd__iiwoo in
        dtypes_typ.types)
    struct_arr_type = StructArrayType(brq__daswm, names)

    def codegen(context, builder, sig, args):
        visdb__sqxhx, nested_counts, yrx__sirg, yrx__sirg = args
        nested_counts_type = sig.args[1]
        nested_counts = _fix_nested_counts(nested_counts, struct_arr_type,
            nested_counts_type, builder)
        xmagr__ogxx, yrx__sirg, yrx__sirg = construct_struct_array(context,
            builder, struct_arr_type, visdb__sqxhx, nested_counts)
        huof__feej = context.make_helper(builder, struct_arr_type)
        huof__feej.meminfo = xmagr__ogxx
        return huof__feej._getvalue()
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
        assert isinstance(names, tuple) and all(isinstance(jweb__uuda, str) for
            jweb__uuda in names) and len(names) == len(data)
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
        bhai__trkk = [('data', types.BaseTuple.from_types(fe_type.data)), (
            'null_bitmap', types.UniTuple(types.int8, len(fe_type.data)))]
        models.StructModel.__init__(self, dmm, fe_type, bhai__trkk)


@register_model(StructType)
class StructModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = StructPayloadType(fe_type.data)
        bhai__trkk = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, bhai__trkk)


def define_struct_dtor(context, builder, struct_type, payload_type):
    diimp__caee = builder.module
    svyw__gwr = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    vtue__vpjnd = cgutils.get_or_insert_function(diimp__caee, svyw__gwr,
        name='.dtor.struct.{}.{}.'.format(struct_type.data, struct_type.names))
    if not vtue__vpjnd.is_declaration:
        return vtue__vpjnd
    vtue__vpjnd.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(vtue__vpjnd.append_basic_block())
    bddwh__byomg = vtue__vpjnd.args[0]
    mciff__gwibn = context.get_value_type(payload_type).as_pointer()
    jeua__hxpy = builder.bitcast(bddwh__byomg, mciff__gwibn)
    hmxg__fzfib = context.make_helper(builder, payload_type, ref=jeua__hxpy)
    for i in range(len(struct_type.data)):
        hxwww__evdw = builder.extract_value(hmxg__fzfib.null_bitmap, i)
        vbyf__fkju = builder.icmp_unsigned('==', hxwww__evdw, lir.Constant(
            hxwww__evdw.type, 1))
        with builder.if_then(vbyf__fkju):
            val = builder.extract_value(hmxg__fzfib.data, i)
            context.nrt.decref(builder, struct_type.data[i], val)
    builder.ret_void()
    return vtue__vpjnd


def _get_struct_payload(context, builder, typ, struct):
    struct = context.make_helper(builder, typ, struct)
    payload_type = StructPayloadType(typ.data)
    ungf__cdrft = context.nrt.meminfo_data(builder, struct.meminfo)
    feohl__wrfiv = builder.bitcast(ungf__cdrft, context.get_value_type(
        payload_type).as_pointer())
    hmxg__fzfib = cgutils.create_struct_proxy(payload_type)(context,
        builder, builder.load(feohl__wrfiv))
    return hmxg__fzfib, feohl__wrfiv


@unbox(StructType)
def unbox_struct(typ, val, c):
    context = c.context
    builder = c.builder
    zuhf__jwto = context.insert_const_string(builder.module, 'pandas')
    omj__edffy = c.pyapi.import_module_noblock(zuhf__jwto)
    xayh__wmgq = c.pyapi.object_getattr_string(omj__edffy, 'NA')
    ovny__tynzx = []
    nulls = []
    for i, jfwd__iiwoo in enumerate(typ.data):
        tks__xky = c.pyapi.dict_getitem_string(val, typ.names[i])
        sba__nebxv = cgutils.alloca_once_value(c.builder, context.
            get_constant(types.uint8, 0))
        tioex__avm = cgutils.alloca_once_value(c.builder, cgutils.
            get_null_value(context.get_value_type(jfwd__iiwoo)))
        ato__eory = is_na_value(builder, context, tks__xky, xayh__wmgq)
        vbyf__fkju = builder.icmp_unsigned('!=', ato__eory, lir.Constant(
            ato__eory.type, 1))
        with builder.if_then(vbyf__fkju):
            builder.store(context.get_constant(types.uint8, 1), sba__nebxv)
            field_val = c.pyapi.to_native_value(jfwd__iiwoo, tks__xky).value
            builder.store(field_val, tioex__avm)
        ovny__tynzx.append(builder.load(tioex__avm))
        nulls.append(builder.load(sba__nebxv))
    c.pyapi.decref(omj__edffy)
    c.pyapi.decref(xayh__wmgq)
    xmagr__ogxx = construct_struct(context, builder, typ, ovny__tynzx, nulls)
    struct = context.make_helper(builder, typ)
    struct.meminfo = xmagr__ogxx
    pacf__ybkp = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(struct._getvalue(), is_error=pacf__ybkp)


@box(StructType)
def box_struct(typ, val, c):
    rtll__ept = c.pyapi.dict_new(len(typ.data))
    hmxg__fzfib, yrx__sirg = _get_struct_payload(c.context, c.builder, typ, val
        )
    assert len(typ.data) > 0
    for i, val_typ in enumerate(typ.data):
        c.pyapi.dict_setitem_string(rtll__ept, typ.names[i], c.pyapi.
            borrow_none())
        hxwww__evdw = c.builder.extract_value(hmxg__fzfib.null_bitmap, i)
        vbyf__fkju = c.builder.icmp_unsigned('==', hxwww__evdw, lir.
            Constant(hxwww__evdw.type, 1))
        with c.builder.if_then(vbyf__fkju):
            vcu__cwg = c.builder.extract_value(hmxg__fzfib.data, i)
            c.context.nrt.incref(c.builder, val_typ, vcu__cwg)
            efvb__ffzr = c.pyapi.from_native_value(val_typ, vcu__cwg, c.
                env_manager)
            c.pyapi.dict_setitem_string(rtll__ept, typ.names[i], efvb__ffzr)
            c.pyapi.decref(efvb__ffzr)
    c.context.nrt.decref(c.builder, typ, val)
    return rtll__ept


@intrinsic
def init_struct(typingctx, data_typ, names_typ=None):
    names = tuple(get_overload_const_str(jfwd__iiwoo) for jfwd__iiwoo in
        names_typ.types)
    struct_type = StructType(data_typ.types, names)

    def codegen(context, builder, sig, args):
        data, qobxi__zdos = args
        payload_type = StructPayloadType(struct_type.data)
        kfjpg__ebhg = context.get_value_type(payload_type)
        vqzrg__xirc = context.get_abi_sizeof(kfjpg__ebhg)
        mffu__qlnn = define_struct_dtor(context, builder, struct_type,
            payload_type)
        xmagr__ogxx = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, vqzrg__xirc), mffu__qlnn)
        ungf__cdrft = context.nrt.meminfo_data(builder, xmagr__ogxx)
        feohl__wrfiv = builder.bitcast(ungf__cdrft, kfjpg__ebhg.as_pointer())
        hmxg__fzfib = cgutils.create_struct_proxy(payload_type)(context,
            builder)
        hmxg__fzfib.data = data
        hmxg__fzfib.null_bitmap = cgutils.pack_array(builder, [context.
            get_constant(types.uint8, 1) for yrx__sirg in range(len(
            data_typ.types))])
        builder.store(hmxg__fzfib._getvalue(), feohl__wrfiv)
        context.nrt.incref(builder, data_typ, data)
        struct = context.make_helper(builder, struct_type)
        struct.meminfo = xmagr__ogxx
        return struct._getvalue()
    return struct_type(data_typ, names_typ), codegen


@intrinsic
def get_struct_data(typingctx, struct_typ=None):
    assert isinstance(struct_typ, StructType)

    def codegen(context, builder, sig, args):
        struct, = args
        hmxg__fzfib, yrx__sirg = _get_struct_payload(context, builder,
            struct_typ, struct)
        return impl_ret_borrowed(context, builder, sig.return_type,
            hmxg__fzfib.data)
    return types.BaseTuple.from_types(struct_typ.data)(struct_typ), codegen


@intrinsic
def get_struct_null_bitmap(typingctx, struct_typ=None):
    assert isinstance(struct_typ, StructType)

    def codegen(context, builder, sig, args):
        struct, = args
        hmxg__fzfib, yrx__sirg = _get_struct_payload(context, builder,
            struct_typ, struct)
        return impl_ret_borrowed(context, builder, sig.return_type,
            hmxg__fzfib.null_bitmap)
    xht__ttc = types.UniTuple(types.int8, len(struct_typ.data))
    return xht__ttc(struct_typ), codegen


@intrinsic
def set_struct_data(typingctx, struct_typ, field_ind_typ, val_typ=None):
    assert isinstance(struct_typ, StructType) and is_overload_constant_int(
        field_ind_typ)
    field_ind = get_overload_const_int(field_ind_typ)

    def codegen(context, builder, sig, args):
        struct, yrx__sirg, val = args
        hmxg__fzfib, feohl__wrfiv = _get_struct_payload(context, builder,
            struct_typ, struct)
        wepk__wco = hmxg__fzfib.data
        akm__vii = builder.insert_value(wepk__wco, val, field_ind)
        tietg__qypo = types.BaseTuple.from_types(struct_typ.data)
        context.nrt.decref(builder, tietg__qypo, wepk__wco)
        context.nrt.incref(builder, tietg__qypo, akm__vii)
        hmxg__fzfib.data = akm__vii
        builder.store(hmxg__fzfib._getvalue(), feohl__wrfiv)
        return context.get_dummy_value()
    return types.none(struct_typ, field_ind_typ, val_typ), codegen


def _get_struct_field_ind(struct, ind, op):
    if not is_overload_constant_str(ind):
        raise BodoError(
            'structs (from struct array) only support constant strings for {}, not {}'
            .format(op, ind))
    jsijc__ijhy = get_overload_const_str(ind)
    if jsijc__ijhy not in struct.names:
        raise BodoError('Field {} does not exist in struct {}'.format(
            jsijc__ijhy, struct))
    return struct.names.index(jsijc__ijhy)


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
    kfjpg__ebhg = context.get_value_type(payload_type)
    vqzrg__xirc = context.get_abi_sizeof(kfjpg__ebhg)
    mffu__qlnn = define_struct_dtor(context, builder, struct_type, payload_type
        )
    xmagr__ogxx = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, vqzrg__xirc), mffu__qlnn)
    ungf__cdrft = context.nrt.meminfo_data(builder, xmagr__ogxx)
    feohl__wrfiv = builder.bitcast(ungf__cdrft, kfjpg__ebhg.as_pointer())
    hmxg__fzfib = cgutils.create_struct_proxy(payload_type)(context, builder)
    hmxg__fzfib.data = cgutils.pack_array(builder, values
        ) if types.is_homogeneous(*struct_type.data) else cgutils.pack_struct(
        builder, values)
    hmxg__fzfib.null_bitmap = cgutils.pack_array(builder, nulls)
    builder.store(hmxg__fzfib._getvalue(), feohl__wrfiv)
    return xmagr__ogxx


@intrinsic
def struct_array_get_struct(typingctx, struct_arr_typ, ind_typ=None):
    assert isinstance(struct_arr_typ, StructArrayType) and isinstance(ind_typ,
        types.Integer)
    mfpi__wijt = tuple(d.dtype for d in struct_arr_typ.data)
    cbhpz__pjnbp = StructType(mfpi__wijt, struct_arr_typ.names)

    def codegen(context, builder, sig, args):
        ytshq__oqgo, ind = args
        hmxg__fzfib = _get_struct_arr_payload(context, builder,
            struct_arr_typ, ytshq__oqgo)
        ovny__tynzx = []
        cyzig__gow = []
        for i, arr_typ in enumerate(struct_arr_typ.data):
            vxje__kgpor = builder.extract_value(hmxg__fzfib.data, i)
            dstp__pntu = context.compile_internal(builder, lambda arr, ind:
                np.uint8(0) if bodo.libs.array_kernels.isna(arr, ind) else
                np.uint8(1), types.uint8(arr_typ, types.int64), [
                vxje__kgpor, ind])
            cyzig__gow.append(dstp__pntu)
            mvx__wcyu = cgutils.alloca_once_value(builder, context.
                get_constant_null(arr_typ.dtype))
            vbyf__fkju = builder.icmp_unsigned('==', dstp__pntu, lir.
                Constant(dstp__pntu.type, 1))
            with builder.if_then(vbyf__fkju):
                ngcx__pyp = context.compile_internal(builder, lambda arr,
                    ind: arr[ind], arr_typ.dtype(arr_typ, types.int64), [
                    vxje__kgpor, ind])
                builder.store(ngcx__pyp, mvx__wcyu)
            ovny__tynzx.append(builder.load(mvx__wcyu))
        if isinstance(cbhpz__pjnbp, types.DictType):
            nfwnj__tarau = [context.insert_const_string(builder.module,
                qono__wfqp) for qono__wfqp in struct_arr_typ.names]
            feqbr__yezk = cgutils.pack_array(builder, ovny__tynzx)
            glc__vemhu = cgutils.pack_array(builder, nfwnj__tarau)

            def impl(names, vals):
                d = {}
                for i, qono__wfqp in enumerate(names):
                    d[qono__wfqp] = vals[i]
                return d
            qsqf__rwz = context.compile_internal(builder, impl,
                cbhpz__pjnbp(types.Tuple(tuple(types.StringLiteral(
                qono__wfqp) for qono__wfqp in struct_arr_typ.names)), types
                .Tuple(mfpi__wijt)), [glc__vemhu, feqbr__yezk])
            context.nrt.decref(builder, types.BaseTuple.from_types(
                mfpi__wijt), feqbr__yezk)
            return qsqf__rwz
        xmagr__ogxx = construct_struct(context, builder, cbhpz__pjnbp,
            ovny__tynzx, cyzig__gow)
        struct = context.make_helper(builder, cbhpz__pjnbp)
        struct.meminfo = xmagr__ogxx
        return struct._getvalue()
    return cbhpz__pjnbp(struct_arr_typ, ind_typ), codegen


@intrinsic
def get_data(typingctx, arr_typ=None):
    assert isinstance(arr_typ, StructArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        hmxg__fzfib = _get_struct_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            hmxg__fzfib.data)
    return types.BaseTuple.from_types(arr_typ.data)(arr_typ), codegen


@intrinsic
def get_null_bitmap(typingctx, arr_typ=None):
    assert isinstance(arr_typ, StructArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        hmxg__fzfib = _get_struct_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            hmxg__fzfib.null_bitmap)
    return types.Array(types.uint8, 1, 'C')(arr_typ), codegen


@intrinsic
def init_struct_arr(typingctx, data_typ, null_bitmap_typ, names_typ=None):
    names = tuple(get_overload_const_str(jfwd__iiwoo) for jfwd__iiwoo in
        names_typ.types)
    struct_arr_type = StructArrayType(data_typ.types, names)

    def codegen(context, builder, sig, args):
        data, ychdj__oxywp, qobxi__zdos = args
        payload_type = StructArrayPayloadType(struct_arr_type.data)
        kfjpg__ebhg = context.get_value_type(payload_type)
        vqzrg__xirc = context.get_abi_sizeof(kfjpg__ebhg)
        mffu__qlnn = define_struct_arr_dtor(context, builder,
            struct_arr_type, payload_type)
        xmagr__ogxx = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, vqzrg__xirc), mffu__qlnn)
        ungf__cdrft = context.nrt.meminfo_data(builder, xmagr__ogxx)
        feohl__wrfiv = builder.bitcast(ungf__cdrft, kfjpg__ebhg.as_pointer())
        hmxg__fzfib = cgutils.create_struct_proxy(payload_type)(context,
            builder)
        hmxg__fzfib.data = data
        hmxg__fzfib.null_bitmap = ychdj__oxywp
        builder.store(hmxg__fzfib._getvalue(), feohl__wrfiv)
        context.nrt.incref(builder, data_typ, data)
        context.nrt.incref(builder, null_bitmap_typ, ychdj__oxywp)
        huof__feej = context.make_helper(builder, struct_arr_type)
        huof__feej.meminfo = xmagr__ogxx
        return huof__feej._getvalue()
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
    zfyb__tpff = len(arr.data)
    rbn__qrxl = 'def impl(arr, ind):\n'
    rbn__qrxl += '  data = get_data(arr)\n'
    rbn__qrxl += '  null_bitmap = get_null_bitmap(arr)\n'
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        rbn__qrxl += """  out_null_bitmap = get_new_null_mask_bool_index(null_bitmap, ind, len(data[0]))
"""
    elif is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        rbn__qrxl += """  out_null_bitmap = get_new_null_mask_int_index(null_bitmap, ind, len(data[0]))
"""
    elif isinstance(ind, types.SliceType):
        rbn__qrxl += """  out_null_bitmap = get_new_null_mask_slice_index(null_bitmap, ind, len(data[0]))
"""
    else:
        raise BodoError('invalid index {} in struct array indexing'.format(ind)
            )
    rbn__qrxl += ('  return init_struct_arr(({},), out_null_bitmap, ({},))\n'
        .format(', '.join('ensure_contig_if_np(data[{}][ind])'.format(i) for
        i in range(zfyb__tpff)), ', '.join("'{}'".format(qono__wfqp) for
        qono__wfqp in arr.names)))
    svfyd__osu = {}
    exec(rbn__qrxl, {'init_struct_arr': init_struct_arr, 'get_data':
        get_data, 'get_null_bitmap': get_null_bitmap, 'ensure_contig_if_np':
        bodo.utils.conversion.ensure_contig_if_np,
        'get_new_null_mask_bool_index': bodo.utils.indexing.
        get_new_null_mask_bool_index, 'get_new_null_mask_int_index': bodo.
        utils.indexing.get_new_null_mask_int_index,
        'get_new_null_mask_slice_index': bodo.utils.indexing.
        get_new_null_mask_slice_index}, svfyd__osu)
    impl = svfyd__osu['impl']
    return impl


@overload(operator.setitem, no_unliteral=True)
def struct_arr_setitem(arr, ind, val):
    if not isinstance(arr, StructArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    if isinstance(ind, types.Integer):
        zfyb__tpff = len(arr.data)
        rbn__qrxl = 'def impl(arr, ind, val):\n'
        rbn__qrxl += '  data = get_data(arr)\n'
        rbn__qrxl += '  null_bitmap = get_null_bitmap(arr)\n'
        rbn__qrxl += '  set_bit_to_arr(null_bitmap, ind, 1)\n'
        for i in range(zfyb__tpff):
            if isinstance(val, StructType):
                rbn__qrxl += "  if is_field_value_null(val, '{}'):\n".format(
                    arr.names[i])
                rbn__qrxl += (
                    '    bodo.libs.array_kernels.setna(data[{}], ind)\n'.
                    format(i))
                rbn__qrxl += '  else:\n'
                rbn__qrxl += "    data[{}][ind] = val['{}']\n".format(i,
                    arr.names[i])
            else:
                rbn__qrxl += "  data[{}][ind] = val['{}']\n".format(i, arr.
                    names[i])
        svfyd__osu = {}
        exec(rbn__qrxl, {'bodo': bodo, 'get_data': get_data,
            'get_null_bitmap': get_null_bitmap, 'set_bit_to_arr': bodo.libs
            .int_arr_ext.set_bit_to_arr, 'is_field_value_null':
            is_field_value_null}, svfyd__osu)
        impl = svfyd__osu['impl']
        return impl
    if isinstance(ind, types.SliceType):
        zfyb__tpff = len(arr.data)
        rbn__qrxl = 'def impl(arr, ind, val):\n'
        rbn__qrxl += '  data = get_data(arr)\n'
        rbn__qrxl += '  null_bitmap = get_null_bitmap(arr)\n'
        rbn__qrxl += '  val_data = get_data(val)\n'
        rbn__qrxl += '  val_null_bitmap = get_null_bitmap(val)\n'
        rbn__qrxl += """  setitem_slice_index_null_bits(null_bitmap, val_null_bitmap, ind, len(arr))
"""
        for i in range(zfyb__tpff):
            rbn__qrxl += '  data[{0}][ind] = val_data[{0}]\n'.format(i)
        svfyd__osu = {}
        exec(rbn__qrxl, {'bodo': bodo, 'get_data': get_data,
            'get_null_bitmap': get_null_bitmap, 'set_bit_to_arr': bodo.libs
            .int_arr_ext.set_bit_to_arr, 'setitem_slice_index_null_bits':
            bodo.utils.indexing.setitem_slice_index_null_bits}, svfyd__osu)
        impl = svfyd__osu['impl']
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
    rbn__qrxl = 'def impl(A):\n'
    rbn__qrxl += '  total_nbytes = 0\n'
    rbn__qrxl += '  data = get_data(A)\n'
    for i in range(len(A.data)):
        rbn__qrxl += f'  total_nbytes += data[{i}].nbytes\n'
    rbn__qrxl += '  total_nbytes += get_null_bitmap(A).nbytes\n'
    rbn__qrxl += '  return total_nbytes\n'
    svfyd__osu = {}
    exec(rbn__qrxl, {'get_data': get_data, 'get_null_bitmap':
        get_null_bitmap}, svfyd__osu)
    impl = svfyd__osu['impl']
    return impl


@overload_method(StructArrayType, 'copy', no_unliteral=True)
def overload_struct_arr_copy(A):
    names = A.names

    def copy_impl(A):
        data = get_data(A)
        ychdj__oxywp = get_null_bitmap(A)
        mympt__wurm = bodo.ir.join.copy_arr_tup(data)
        ongwk__kwtj = ychdj__oxywp.copy()
        return init_struct_arr(mympt__wurm, ongwk__kwtj, names)
    return copy_impl
