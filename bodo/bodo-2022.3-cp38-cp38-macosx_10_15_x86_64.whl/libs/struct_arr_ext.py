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
            .utils.is_array_typ(vpgrr__jsoq, False) for vpgrr__jsoq in data)
        if names is not None:
            assert isinstance(names, tuple) and all(isinstance(vpgrr__jsoq,
                str) for vpgrr__jsoq in names) and len(names) == len(data)
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
        return StructType(tuple(xkeql__eoi.dtype for xkeql__eoi in self.
            data), self.names)

    @classmethod
    def from_dict(cls, d):
        assert isinstance(d, dict)
        names = tuple(str(vpgrr__jsoq) for vpgrr__jsoq in d.keys())
        data = tuple(dtype_to_array_type(xkeql__eoi) for xkeql__eoi in d.
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
            is_array_typ(vpgrr__jsoq, False) for vpgrr__jsoq in data)
        self.data = data
        super(StructArrayPayloadType, self).__init__(name=
            'StructArrayPayloadType({})'.format(data))

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(StructArrayPayloadType)
class StructArrayPayloadModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        kpk__gldf = [('data', types.BaseTuple.from_types(fe_type.data)), (
            'null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, kpk__gldf)


@register_model(StructArrayType)
class StructArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = StructArrayPayloadType(fe_type.data)
        kpk__gldf = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, kpk__gldf)


def define_struct_arr_dtor(context, builder, struct_arr_type, payload_type):
    tencb__bqn = builder.module
    nlzfy__mss = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    crgau__rix = cgutils.get_or_insert_function(tencb__bqn, nlzfy__mss,
        name='.dtor.struct_arr.{}.{}.'.format(struct_arr_type.data,
        struct_arr_type.names))
    if not crgau__rix.is_declaration:
        return crgau__rix
    crgau__rix.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(crgau__rix.append_basic_block())
    ftwuy__ksb = crgau__rix.args[0]
    rjgfn__vbkt = context.get_value_type(payload_type).as_pointer()
    btbq__elh = builder.bitcast(ftwuy__ksb, rjgfn__vbkt)
    qse__ljv = context.make_helper(builder, payload_type, ref=btbq__elh)
    context.nrt.decref(builder, types.BaseTuple.from_types(struct_arr_type.
        data), qse__ljv.data)
    context.nrt.decref(builder, types.Array(types.uint8, 1, 'C'), qse__ljv.
        null_bitmap)
    builder.ret_void()
    return crgau__rix


def construct_struct_array(context, builder, struct_arr_type, n_structs,
    n_elems, c=None):
    payload_type = StructArrayPayloadType(struct_arr_type.data)
    bpo__sfa = context.get_value_type(payload_type)
    rgq__vde = context.get_abi_sizeof(bpo__sfa)
    oqvq__zjzg = define_struct_arr_dtor(context, builder, struct_arr_type,
        payload_type)
    kivur__swcjd = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, rgq__vde), oqvq__zjzg)
    fpopq__adeuv = context.nrt.meminfo_data(builder, kivur__swcjd)
    dee__frgp = builder.bitcast(fpopq__adeuv, bpo__sfa.as_pointer())
    qse__ljv = cgutils.create_struct_proxy(payload_type)(context, builder)
    hcxs__mgxmp = []
    ihi__bhcon = 0
    for arr_typ in struct_arr_type.data:
        wmfqp__awcg = bodo.utils.transform.get_type_alloc_counts(arr_typ.dtype)
        puayl__gcsnx = cgutils.pack_array(builder, [n_structs] + [builder.
            extract_value(n_elems, i) for i in range(ihi__bhcon, ihi__bhcon +
            wmfqp__awcg)])
        arr = gen_allocate_array(context, builder, arr_typ, puayl__gcsnx, c)
        hcxs__mgxmp.append(arr)
        ihi__bhcon += wmfqp__awcg
    qse__ljv.data = cgutils.pack_array(builder, hcxs__mgxmp
        ) if types.is_homogeneous(*struct_arr_type.data
        ) else cgutils.pack_struct(builder, hcxs__mgxmp)
    xddgy__fqjz = builder.udiv(builder.add(n_structs, lir.Constant(lir.
        IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
    itycp__hmb = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(types.uint8, 1, 'C'), [xddgy__fqjz])
    null_bitmap_ptr = itycp__hmb.data
    qse__ljv.null_bitmap = itycp__hmb._getvalue()
    builder.store(qse__ljv._getvalue(), dee__frgp)
    return kivur__swcjd, qse__ljv.data, null_bitmap_ptr


def _get_C_API_ptrs(c, data_tup, data_typ, names):
    zhdl__uesde = []
    assert len(data_typ) > 0
    for i, arr_typ in enumerate(data_typ):
        kxb__zeduq = c.builder.extract_value(data_tup, i)
        arr = c.context.make_array(arr_typ)(c.context, c.builder, value=
            kxb__zeduq)
        zhdl__uesde.append(arr.data)
    pnipj__etsrd = cgutils.pack_array(c.builder, zhdl__uesde
        ) if types.is_homogeneous(*data_typ) else cgutils.pack_struct(c.
        builder, zhdl__uesde)
    dbzn__elqd = cgutils.alloca_once_value(c.builder, pnipj__etsrd)
    wtfno__ohoo = [c.context.get_constant(types.int32, bodo.utils.utils.
        numba_to_c_type(vpgrr__jsoq.dtype)) for vpgrr__jsoq in data_typ]
    dcuq__fcvog = cgutils.alloca_once_value(c.builder, cgutils.pack_array(c
        .builder, wtfno__ohoo))
    uyms__zujp = cgutils.pack_array(c.builder, [c.context.
        insert_const_string(c.builder.module, vpgrr__jsoq) for vpgrr__jsoq in
        names])
    lfap__crhb = cgutils.alloca_once_value(c.builder, uyms__zujp)
    return dbzn__elqd, dcuq__fcvog, lfap__crhb


@unbox(StructArrayType)
def unbox_struct_array(typ, val, c, is_tuple_array=False):
    from bodo.libs.tuple_arr_ext import TupleArrayType
    n_structs = bodo.utils.utils.object_length(c, val)
    xpy__ziwu = all(isinstance(xkeql__eoi, types.Array) and xkeql__eoi.
        dtype in (types.int64, types.float64, types.bool_,
        datetime_date_type) for xkeql__eoi in typ.data)
    if xpy__ziwu:
        n_elems = cgutils.pack_array(c.builder, [], lir.IntType(64))
    else:
        twawj__scto = get_array_elem_counts(c, c.builder, c.context, val, 
            TupleArrayType(typ.data) if is_tuple_array else typ)
        n_elems = cgutils.pack_array(c.builder, [c.builder.extract_value(
            twawj__scto, i) for i in range(1, twawj__scto.type.count)], lir
            .IntType(64))
    kivur__swcjd, data_tup, null_bitmap_ptr = construct_struct_array(c.
        context, c.builder, typ, n_structs, n_elems, c)
    if xpy__ziwu:
        dbzn__elqd, dcuq__fcvog, lfap__crhb = _get_C_API_ptrs(c, data_tup,
            typ.data, typ.names)
        nlzfy__mss = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(32), lir.IntType(8).as_pointer(), lir
            .IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1)])
        crgau__rix = cgutils.get_or_insert_function(c.builder.module,
            nlzfy__mss, name='struct_array_from_sequence')
        c.builder.call(crgau__rix, [val, c.context.get_constant(types.int32,
            len(typ.data)), c.builder.bitcast(dbzn__elqd, lir.IntType(8).
            as_pointer()), null_bitmap_ptr, c.builder.bitcast(dcuq__fcvog,
            lir.IntType(8).as_pointer()), c.builder.bitcast(lfap__crhb, lir
            .IntType(8).as_pointer()), c.context.get_constant(types.bool_,
            is_tuple_array)])
    else:
        _unbox_struct_array_generic(typ, val, c, n_structs, data_tup,
            null_bitmap_ptr, is_tuple_array)
    qbknz__ptd = c.context.make_helper(c.builder, typ)
    qbknz__ptd.meminfo = kivur__swcjd
    dwdg__anjbp = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(qbknz__ptd._getvalue(), is_error=dwdg__anjbp)


def _unbox_struct_array_generic(typ, val, c, n_structs, data_tup,
    null_bitmap_ptr, is_tuple_array=False):
    context = c.context
    builder = c.builder
    els__seuc = context.insert_const_string(builder.module, 'pandas')
    zexa__eepx = c.pyapi.import_module_noblock(els__seuc)
    bgk__sutx = c.pyapi.object_getattr_string(zexa__eepx, 'NA')
    with cgutils.for_range(builder, n_structs) as xujfn__rfq:
        jadqt__ehhcj = xujfn__rfq.index
        qxbe__nnrgo = seq_getitem(builder, context, val, jadqt__ehhcj)
        set_bitmap_bit(builder, null_bitmap_ptr, jadqt__ehhcj, 0)
        for oldna__jmjvk in range(len(typ.data)):
            arr_typ = typ.data[oldna__jmjvk]
            data_arr = builder.extract_value(data_tup, oldna__jmjvk)

            def set_na(data_arr, i):
                bodo.libs.array_kernels.setna(data_arr, i)
            sig = types.none(arr_typ, types.int64)
            qnq__qedp, hse__rqwsk = c.pyapi.call_jit_code(set_na, sig, [
                data_arr, jadqt__ehhcj])
        emaba__nduhq = is_na_value(builder, context, qxbe__nnrgo, bgk__sutx)
        dxvqj__zqzkp = builder.icmp_unsigned('!=', emaba__nduhq, lir.
            Constant(emaba__nduhq.type, 1))
        with builder.if_then(dxvqj__zqzkp):
            set_bitmap_bit(builder, null_bitmap_ptr, jadqt__ehhcj, 1)
            for oldna__jmjvk in range(len(typ.data)):
                arr_typ = typ.data[oldna__jmjvk]
                if is_tuple_array:
                    xnx__bsyp = c.pyapi.tuple_getitem(qxbe__nnrgo, oldna__jmjvk
                        )
                else:
                    xnx__bsyp = c.pyapi.dict_getitem_string(qxbe__nnrgo,
                        typ.names[oldna__jmjvk])
                emaba__nduhq = is_na_value(builder, context, xnx__bsyp,
                    bgk__sutx)
                dxvqj__zqzkp = builder.icmp_unsigned('!=', emaba__nduhq,
                    lir.Constant(emaba__nduhq.type, 1))
                with builder.if_then(dxvqj__zqzkp):
                    xnx__bsyp = to_arr_obj_if_list_obj(c, context, builder,
                        xnx__bsyp, arr_typ.dtype)
                    field_val = c.pyapi.to_native_value(arr_typ.dtype,
                        xnx__bsyp).value
                    data_arr = builder.extract_value(data_tup, oldna__jmjvk)

                    def set_data(data_arr, i, field_val):
                        data_arr[i] = field_val
                    sig = types.none(arr_typ, types.int64, arr_typ.dtype)
                    qnq__qedp, hse__rqwsk = c.pyapi.call_jit_code(set_data,
                        sig, [data_arr, jadqt__ehhcj, field_val])
                    c.context.nrt.decref(builder, arr_typ.dtype, field_val)
        c.pyapi.decref(qxbe__nnrgo)
    c.pyapi.decref(zexa__eepx)
    c.pyapi.decref(bgk__sutx)


def _get_struct_arr_payload(context, builder, arr_typ, arr):
    qbknz__ptd = context.make_helper(builder, arr_typ, arr)
    payload_type = StructArrayPayloadType(arr_typ.data)
    fpopq__adeuv = context.nrt.meminfo_data(builder, qbknz__ptd.meminfo)
    dee__frgp = builder.bitcast(fpopq__adeuv, context.get_value_type(
        payload_type).as_pointer())
    qse__ljv = cgutils.create_struct_proxy(payload_type)(context, builder,
        builder.load(dee__frgp))
    return qse__ljv


@box(StructArrayType)
def box_struct_arr(typ, val, c, is_tuple_array=False):
    qse__ljv = _get_struct_arr_payload(c.context, c.builder, typ, val)
    qnq__qedp, length = c.pyapi.call_jit_code(lambda A: len(A), types.int64
        (typ), [val])
    null_bitmap_ptr = c.context.make_helper(c.builder, types.Array(types.
        uint8, 1, 'C'), qse__ljv.null_bitmap).data
    xpy__ziwu = all(isinstance(xkeql__eoi, types.Array) and xkeql__eoi.
        dtype in (types.int64, types.float64, types.bool_,
        datetime_date_type) for xkeql__eoi in typ.data)
    if xpy__ziwu:
        dbzn__elqd, dcuq__fcvog, lfap__crhb = _get_C_API_ptrs(c, qse__ljv.
            data, typ.data, typ.names)
        nlzfy__mss = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(32), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1)])
        uipv__bauc = cgutils.get_or_insert_function(c.builder.module,
            nlzfy__mss, name='np_array_from_struct_array')
        arr = c.builder.call(uipv__bauc, [length, c.context.get_constant(
            types.int32, len(typ.data)), c.builder.bitcast(dbzn__elqd, lir.
            IntType(8).as_pointer()), null_bitmap_ptr, c.builder.bitcast(
            dcuq__fcvog, lir.IntType(8).as_pointer()), c.builder.bitcast(
            lfap__crhb, lir.IntType(8).as_pointer()), c.context.
            get_constant(types.bool_, is_tuple_array)])
    else:
        arr = _box_struct_array_generic(typ, c, length, qse__ljv.data,
            null_bitmap_ptr, is_tuple_array)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def _box_struct_array_generic(typ, c, length, data_arrs_tup,
    null_bitmap_ptr, is_tuple_array=False):
    context = c.context
    builder = c.builder
    els__seuc = context.insert_const_string(builder.module, 'numpy')
    auuww__lobvp = c.pyapi.import_module_noblock(els__seuc)
    htp__zxr = c.pyapi.object_getattr_string(auuww__lobvp, 'object_')
    gnrfy__gxpru = c.pyapi.long_from_longlong(length)
    luq__qxu = c.pyapi.call_method(auuww__lobvp, 'ndarray', (gnrfy__gxpru,
        htp__zxr))
    wsiq__dwrl = c.pyapi.object_getattr_string(auuww__lobvp, 'nan')
    with cgutils.for_range(builder, length) as xujfn__rfq:
        jadqt__ehhcj = xujfn__rfq.index
        pyarray_setitem(builder, context, luq__qxu, jadqt__ehhcj, wsiq__dwrl)
        ceuf__xtvwm = get_bitmap_bit(builder, null_bitmap_ptr, jadqt__ehhcj)
        lckx__nes = builder.icmp_unsigned('!=', ceuf__xtvwm, lir.Constant(
            lir.IntType(8), 0))
        with builder.if_then(lckx__nes):
            if is_tuple_array:
                qxbe__nnrgo = c.pyapi.tuple_new(len(typ.data))
            else:
                qxbe__nnrgo = c.pyapi.dict_new(len(typ.data))
            for i, arr_typ in enumerate(typ.data):
                if is_tuple_array:
                    c.pyapi.incref(wsiq__dwrl)
                    c.pyapi.tuple_setitem(qxbe__nnrgo, i, wsiq__dwrl)
                else:
                    c.pyapi.dict_setitem_string(qxbe__nnrgo, typ.names[i],
                        wsiq__dwrl)
                data_arr = c.builder.extract_value(data_arrs_tup, i)
                qnq__qedp, tzkix__jyp = c.pyapi.call_jit_code(lambda
                    data_arr, ind: not bodo.libs.array_kernels.isna(
                    data_arr, ind), types.bool_(arr_typ, types.int64), [
                    data_arr, jadqt__ehhcj])
                with builder.if_then(tzkix__jyp):
                    qnq__qedp, field_val = c.pyapi.call_jit_code(lambda
                        data_arr, ind: data_arr[ind], arr_typ.dtype(arr_typ,
                        types.int64), [data_arr, jadqt__ehhcj])
                    srp__mhqwn = c.pyapi.from_native_value(arr_typ.dtype,
                        field_val, c.env_manager)
                    if is_tuple_array:
                        c.pyapi.tuple_setitem(qxbe__nnrgo, i, srp__mhqwn)
                    else:
                        c.pyapi.dict_setitem_string(qxbe__nnrgo, typ.names[
                            i], srp__mhqwn)
                        c.pyapi.decref(srp__mhqwn)
            pyarray_setitem(builder, context, luq__qxu, jadqt__ehhcj,
                qxbe__nnrgo)
            c.pyapi.decref(qxbe__nnrgo)
    c.pyapi.decref(auuww__lobvp)
    c.pyapi.decref(htp__zxr)
    c.pyapi.decref(gnrfy__gxpru)
    c.pyapi.decref(wsiq__dwrl)
    return luq__qxu


def _fix_nested_counts(nested_counts, struct_arr_type, nested_counts_type,
    builder):
    ppye__lrka = bodo.utils.transform.get_type_alloc_counts(struct_arr_type
        ) - 1
    if ppye__lrka == 0:
        return nested_counts
    if not isinstance(nested_counts_type, types.UniTuple):
        nested_counts = cgutils.pack_array(builder, [lir.Constant(lir.
            IntType(64), -1) for clkok__abrz in range(ppye__lrka)])
    elif nested_counts_type.count < ppye__lrka:
        nested_counts = cgutils.pack_array(builder, [builder.extract_value(
            nested_counts, i) for i in range(nested_counts_type.count)] + [
            lir.Constant(lir.IntType(64), -1) for clkok__abrz in range(
            ppye__lrka - nested_counts_type.count)])
    return nested_counts


@intrinsic
def pre_alloc_struct_array(typingctx, num_structs_typ, nested_counts_typ,
    dtypes_typ, names_typ=None):
    assert isinstance(num_structs_typ, types.Integer) and isinstance(dtypes_typ
        , types.BaseTuple)
    if is_overload_none(names_typ):
        names = tuple(f'f{i}' for i in range(len(dtypes_typ)))
    else:
        names = tuple(get_overload_const_str(xkeql__eoi) for xkeql__eoi in
            names_typ.types)
    vfvpq__iguu = tuple(xkeql__eoi.instance_type for xkeql__eoi in
        dtypes_typ.types)
    struct_arr_type = StructArrayType(vfvpq__iguu, names)

    def codegen(context, builder, sig, args):
        hbwoq__oqxa, nested_counts, clkok__abrz, clkok__abrz = args
        nested_counts_type = sig.args[1]
        nested_counts = _fix_nested_counts(nested_counts, struct_arr_type,
            nested_counts_type, builder)
        kivur__swcjd, clkok__abrz, clkok__abrz = construct_struct_array(context
            , builder, struct_arr_type, hbwoq__oqxa, nested_counts)
        qbknz__ptd = context.make_helper(builder, struct_arr_type)
        qbknz__ptd.meminfo = kivur__swcjd
        return qbknz__ptd._getvalue()
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
        assert isinstance(names, tuple) and all(isinstance(vpgrr__jsoq, str
            ) for vpgrr__jsoq in names) and len(names) == len(data)
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
        kpk__gldf = [('data', types.BaseTuple.from_types(fe_type.data)), (
            'null_bitmap', types.UniTuple(types.int8, len(fe_type.data)))]
        models.StructModel.__init__(self, dmm, fe_type, kpk__gldf)


@register_model(StructType)
class StructModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = StructPayloadType(fe_type.data)
        kpk__gldf = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, kpk__gldf)


def define_struct_dtor(context, builder, struct_type, payload_type):
    tencb__bqn = builder.module
    nlzfy__mss = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    crgau__rix = cgutils.get_or_insert_function(tencb__bqn, nlzfy__mss,
        name='.dtor.struct.{}.{}.'.format(struct_type.data, struct_type.names))
    if not crgau__rix.is_declaration:
        return crgau__rix
    crgau__rix.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(crgau__rix.append_basic_block())
    ftwuy__ksb = crgau__rix.args[0]
    rjgfn__vbkt = context.get_value_type(payload_type).as_pointer()
    btbq__elh = builder.bitcast(ftwuy__ksb, rjgfn__vbkt)
    qse__ljv = context.make_helper(builder, payload_type, ref=btbq__elh)
    for i in range(len(struct_type.data)):
        mglwe__ymrj = builder.extract_value(qse__ljv.null_bitmap, i)
        lckx__nes = builder.icmp_unsigned('==', mglwe__ymrj, lir.Constant(
            mglwe__ymrj.type, 1))
        with builder.if_then(lckx__nes):
            val = builder.extract_value(qse__ljv.data, i)
            context.nrt.decref(builder, struct_type.data[i], val)
    builder.ret_void()
    return crgau__rix


def _get_struct_payload(context, builder, typ, struct):
    struct = context.make_helper(builder, typ, struct)
    payload_type = StructPayloadType(typ.data)
    fpopq__adeuv = context.nrt.meminfo_data(builder, struct.meminfo)
    dee__frgp = builder.bitcast(fpopq__adeuv, context.get_value_type(
        payload_type).as_pointer())
    qse__ljv = cgutils.create_struct_proxy(payload_type)(context, builder,
        builder.load(dee__frgp))
    return qse__ljv, dee__frgp


@unbox(StructType)
def unbox_struct(typ, val, c):
    context = c.context
    builder = c.builder
    els__seuc = context.insert_const_string(builder.module, 'pandas')
    zexa__eepx = c.pyapi.import_module_noblock(els__seuc)
    bgk__sutx = c.pyapi.object_getattr_string(zexa__eepx, 'NA')
    pyhyw__rqo = []
    nulls = []
    for i, xkeql__eoi in enumerate(typ.data):
        srp__mhqwn = c.pyapi.dict_getitem_string(val, typ.names[i])
        etijd__wswjv = cgutils.alloca_once_value(c.builder, context.
            get_constant(types.uint8, 0))
        gkcke__idy = cgutils.alloca_once_value(c.builder, cgutils.
            get_null_value(context.get_value_type(xkeql__eoi)))
        emaba__nduhq = is_na_value(builder, context, srp__mhqwn, bgk__sutx)
        lckx__nes = builder.icmp_unsigned('!=', emaba__nduhq, lir.Constant(
            emaba__nduhq.type, 1))
        with builder.if_then(lckx__nes):
            builder.store(context.get_constant(types.uint8, 1), etijd__wswjv)
            field_val = c.pyapi.to_native_value(xkeql__eoi, srp__mhqwn).value
            builder.store(field_val, gkcke__idy)
        pyhyw__rqo.append(builder.load(gkcke__idy))
        nulls.append(builder.load(etijd__wswjv))
    c.pyapi.decref(zexa__eepx)
    c.pyapi.decref(bgk__sutx)
    kivur__swcjd = construct_struct(context, builder, typ, pyhyw__rqo, nulls)
    struct = context.make_helper(builder, typ)
    struct.meminfo = kivur__swcjd
    dwdg__anjbp = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(struct._getvalue(), is_error=dwdg__anjbp)


@box(StructType)
def box_struct(typ, val, c):
    hhyvm__culg = c.pyapi.dict_new(len(typ.data))
    qse__ljv, clkok__abrz = _get_struct_payload(c.context, c.builder, typ, val)
    assert len(typ.data) > 0
    for i, val_typ in enumerate(typ.data):
        c.pyapi.dict_setitem_string(hhyvm__culg, typ.names[i], c.pyapi.
            borrow_none())
        mglwe__ymrj = c.builder.extract_value(qse__ljv.null_bitmap, i)
        lckx__nes = c.builder.icmp_unsigned('==', mglwe__ymrj, lir.Constant
            (mglwe__ymrj.type, 1))
        with c.builder.if_then(lckx__nes):
            rnm__bqv = c.builder.extract_value(qse__ljv.data, i)
            c.context.nrt.incref(c.builder, val_typ, rnm__bqv)
            xnx__bsyp = c.pyapi.from_native_value(val_typ, rnm__bqv, c.
                env_manager)
            c.pyapi.dict_setitem_string(hhyvm__culg, typ.names[i], xnx__bsyp)
            c.pyapi.decref(xnx__bsyp)
    c.context.nrt.decref(c.builder, typ, val)
    return hhyvm__culg


@intrinsic
def init_struct(typingctx, data_typ, names_typ=None):
    names = tuple(get_overload_const_str(xkeql__eoi) for xkeql__eoi in
        names_typ.types)
    struct_type = StructType(data_typ.types, names)

    def codegen(context, builder, sig, args):
        data, wnbap__xyza = args
        payload_type = StructPayloadType(struct_type.data)
        bpo__sfa = context.get_value_type(payload_type)
        rgq__vde = context.get_abi_sizeof(bpo__sfa)
        oqvq__zjzg = define_struct_dtor(context, builder, struct_type,
            payload_type)
        kivur__swcjd = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, rgq__vde), oqvq__zjzg)
        fpopq__adeuv = context.nrt.meminfo_data(builder, kivur__swcjd)
        dee__frgp = builder.bitcast(fpopq__adeuv, bpo__sfa.as_pointer())
        qse__ljv = cgutils.create_struct_proxy(payload_type)(context, builder)
        qse__ljv.data = data
        qse__ljv.null_bitmap = cgutils.pack_array(builder, [context.
            get_constant(types.uint8, 1) for clkok__abrz in range(len(
            data_typ.types))])
        builder.store(qse__ljv._getvalue(), dee__frgp)
        context.nrt.incref(builder, data_typ, data)
        struct = context.make_helper(builder, struct_type)
        struct.meminfo = kivur__swcjd
        return struct._getvalue()
    return struct_type(data_typ, names_typ), codegen


@intrinsic
def get_struct_data(typingctx, struct_typ=None):
    assert isinstance(struct_typ, StructType)

    def codegen(context, builder, sig, args):
        struct, = args
        qse__ljv, clkok__abrz = _get_struct_payload(context, builder,
            struct_typ, struct)
        return impl_ret_borrowed(context, builder, sig.return_type,
            qse__ljv.data)
    return types.BaseTuple.from_types(struct_typ.data)(struct_typ), codegen


@intrinsic
def get_struct_null_bitmap(typingctx, struct_typ=None):
    assert isinstance(struct_typ, StructType)

    def codegen(context, builder, sig, args):
        struct, = args
        qse__ljv, clkok__abrz = _get_struct_payload(context, builder,
            struct_typ, struct)
        return impl_ret_borrowed(context, builder, sig.return_type,
            qse__ljv.null_bitmap)
    cuab__qogt = types.UniTuple(types.int8, len(struct_typ.data))
    return cuab__qogt(struct_typ), codegen


@intrinsic
def set_struct_data(typingctx, struct_typ, field_ind_typ, val_typ=None):
    assert isinstance(struct_typ, StructType) and is_overload_constant_int(
        field_ind_typ)
    field_ind = get_overload_const_int(field_ind_typ)

    def codegen(context, builder, sig, args):
        struct, clkok__abrz, val = args
        qse__ljv, dee__frgp = _get_struct_payload(context, builder,
            struct_typ, struct)
        zslj__cnqtl = qse__ljv.data
        mag__ille = builder.insert_value(zslj__cnqtl, val, field_ind)
        gjkz__nwlbq = types.BaseTuple.from_types(struct_typ.data)
        context.nrt.decref(builder, gjkz__nwlbq, zslj__cnqtl)
        context.nrt.incref(builder, gjkz__nwlbq, mag__ille)
        qse__ljv.data = mag__ille
        builder.store(qse__ljv._getvalue(), dee__frgp)
        return context.get_dummy_value()
    return types.none(struct_typ, field_ind_typ, val_typ), codegen


def _get_struct_field_ind(struct, ind, op):
    if not is_overload_constant_str(ind):
        raise BodoError(
            'structs (from struct array) only support constant strings for {}, not {}'
            .format(op, ind))
    uazig__lhice = get_overload_const_str(ind)
    if uazig__lhice not in struct.names:
        raise BodoError('Field {} does not exist in struct {}'.format(
            uazig__lhice, struct))
    return struct.names.index(uazig__lhice)


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
    bpo__sfa = context.get_value_type(payload_type)
    rgq__vde = context.get_abi_sizeof(bpo__sfa)
    oqvq__zjzg = define_struct_dtor(context, builder, struct_type, payload_type
        )
    kivur__swcjd = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, rgq__vde), oqvq__zjzg)
    fpopq__adeuv = context.nrt.meminfo_data(builder, kivur__swcjd)
    dee__frgp = builder.bitcast(fpopq__adeuv, bpo__sfa.as_pointer())
    qse__ljv = cgutils.create_struct_proxy(payload_type)(context, builder)
    qse__ljv.data = cgutils.pack_array(builder, values
        ) if types.is_homogeneous(*struct_type.data) else cgutils.pack_struct(
        builder, values)
    qse__ljv.null_bitmap = cgutils.pack_array(builder, nulls)
    builder.store(qse__ljv._getvalue(), dee__frgp)
    return kivur__swcjd


@intrinsic
def struct_array_get_struct(typingctx, struct_arr_typ, ind_typ=None):
    assert isinstance(struct_arr_typ, StructArrayType) and isinstance(ind_typ,
        types.Integer)
    udb__nnjs = tuple(d.dtype for d in struct_arr_typ.data)
    tmy__gduoz = StructType(udb__nnjs, struct_arr_typ.names)

    def codegen(context, builder, sig, args):
        ybhsl__kak, ind = args
        qse__ljv = _get_struct_arr_payload(context, builder, struct_arr_typ,
            ybhsl__kak)
        pyhyw__rqo = []
        lqwlq__hsw = []
        for i, arr_typ in enumerate(struct_arr_typ.data):
            kxb__zeduq = builder.extract_value(qse__ljv.data, i)
            edkox__wylv = context.compile_internal(builder, lambda arr, ind:
                np.uint8(0) if bodo.libs.array_kernels.isna(arr, ind) else
                np.uint8(1), types.uint8(arr_typ, types.int64), [kxb__zeduq,
                ind])
            lqwlq__hsw.append(edkox__wylv)
            rgur__vqlb = cgutils.alloca_once_value(builder, context.
                get_constant_null(arr_typ.dtype))
            lckx__nes = builder.icmp_unsigned('==', edkox__wylv, lir.
                Constant(edkox__wylv.type, 1))
            with builder.if_then(lckx__nes):
                jode__wgxa = context.compile_internal(builder, lambda arr,
                    ind: arr[ind], arr_typ.dtype(arr_typ, types.int64), [
                    kxb__zeduq, ind])
                builder.store(jode__wgxa, rgur__vqlb)
            pyhyw__rqo.append(builder.load(rgur__vqlb))
        if isinstance(tmy__gduoz, types.DictType):
            wwhl__lzv = [context.insert_const_string(builder.module,
                fvh__wobkc) for fvh__wobkc in struct_arr_typ.names]
            mkbb__sjgoz = cgutils.pack_array(builder, pyhyw__rqo)
            yxq__nkruv = cgutils.pack_array(builder, wwhl__lzv)

            def impl(names, vals):
                d = {}
                for i, fvh__wobkc in enumerate(names):
                    d[fvh__wobkc] = vals[i]
                return d
            ecnp__ytr = context.compile_internal(builder, impl, tmy__gduoz(
                types.Tuple(tuple(types.StringLiteral(fvh__wobkc) for
                fvh__wobkc in struct_arr_typ.names)), types.Tuple(udb__nnjs
                )), [yxq__nkruv, mkbb__sjgoz])
            context.nrt.decref(builder, types.BaseTuple.from_types(
                udb__nnjs), mkbb__sjgoz)
            return ecnp__ytr
        kivur__swcjd = construct_struct(context, builder, tmy__gduoz,
            pyhyw__rqo, lqwlq__hsw)
        struct = context.make_helper(builder, tmy__gduoz)
        struct.meminfo = kivur__swcjd
        return struct._getvalue()
    return tmy__gduoz(struct_arr_typ, ind_typ), codegen


@intrinsic
def get_data(typingctx, arr_typ=None):
    assert isinstance(arr_typ, StructArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        qse__ljv = _get_struct_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            qse__ljv.data)
    return types.BaseTuple.from_types(arr_typ.data)(arr_typ), codegen


@intrinsic
def get_null_bitmap(typingctx, arr_typ=None):
    assert isinstance(arr_typ, StructArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        qse__ljv = _get_struct_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            qse__ljv.null_bitmap)
    return types.Array(types.uint8, 1, 'C')(arr_typ), codegen


@intrinsic
def init_struct_arr(typingctx, data_typ, null_bitmap_typ, names_typ=None):
    names = tuple(get_overload_const_str(xkeql__eoi) for xkeql__eoi in
        names_typ.types)
    struct_arr_type = StructArrayType(data_typ.types, names)

    def codegen(context, builder, sig, args):
        data, itycp__hmb, wnbap__xyza = args
        payload_type = StructArrayPayloadType(struct_arr_type.data)
        bpo__sfa = context.get_value_type(payload_type)
        rgq__vde = context.get_abi_sizeof(bpo__sfa)
        oqvq__zjzg = define_struct_arr_dtor(context, builder,
            struct_arr_type, payload_type)
        kivur__swcjd = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, rgq__vde), oqvq__zjzg)
        fpopq__adeuv = context.nrt.meminfo_data(builder, kivur__swcjd)
        dee__frgp = builder.bitcast(fpopq__adeuv, bpo__sfa.as_pointer())
        qse__ljv = cgutils.create_struct_proxy(payload_type)(context, builder)
        qse__ljv.data = data
        qse__ljv.null_bitmap = itycp__hmb
        builder.store(qse__ljv._getvalue(), dee__frgp)
        context.nrt.incref(builder, data_typ, data)
        context.nrt.incref(builder, null_bitmap_typ, itycp__hmb)
        qbknz__ptd = context.make_helper(builder, struct_arr_type)
        qbknz__ptd.meminfo = kivur__swcjd
        return qbknz__ptd._getvalue()
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
    mqu__gpbs = len(arr.data)
    ifob__fgnh = 'def impl(arr, ind):\n'
    ifob__fgnh += '  data = get_data(arr)\n'
    ifob__fgnh += '  null_bitmap = get_null_bitmap(arr)\n'
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        ifob__fgnh += """  out_null_bitmap = get_new_null_mask_bool_index(null_bitmap, ind, len(data[0]))
"""
    elif is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        ifob__fgnh += """  out_null_bitmap = get_new_null_mask_int_index(null_bitmap, ind, len(data[0]))
"""
    elif isinstance(ind, types.SliceType):
        ifob__fgnh += """  out_null_bitmap = get_new_null_mask_slice_index(null_bitmap, ind, len(data[0]))
"""
    else:
        raise BodoError('invalid index {} in struct array indexing'.format(ind)
            )
    ifob__fgnh += ('  return init_struct_arr(({},), out_null_bitmap, ({},))\n'
        .format(', '.join('ensure_contig_if_np(data[{}][ind])'.format(i) for
        i in range(mqu__gpbs)), ', '.join("'{}'".format(fvh__wobkc) for
        fvh__wobkc in arr.names)))
    tnmgm__rlka = {}
    exec(ifob__fgnh, {'init_struct_arr': init_struct_arr, 'get_data':
        get_data, 'get_null_bitmap': get_null_bitmap, 'ensure_contig_if_np':
        bodo.utils.conversion.ensure_contig_if_np,
        'get_new_null_mask_bool_index': bodo.utils.indexing.
        get_new_null_mask_bool_index, 'get_new_null_mask_int_index': bodo.
        utils.indexing.get_new_null_mask_int_index,
        'get_new_null_mask_slice_index': bodo.utils.indexing.
        get_new_null_mask_slice_index}, tnmgm__rlka)
    impl = tnmgm__rlka['impl']
    return impl


@overload(operator.setitem, no_unliteral=True)
def struct_arr_setitem(arr, ind, val):
    if not isinstance(arr, StructArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    if isinstance(ind, types.Integer):
        mqu__gpbs = len(arr.data)
        ifob__fgnh = 'def impl(arr, ind, val):\n'
        ifob__fgnh += '  data = get_data(arr)\n'
        ifob__fgnh += '  null_bitmap = get_null_bitmap(arr)\n'
        ifob__fgnh += '  set_bit_to_arr(null_bitmap, ind, 1)\n'
        for i in range(mqu__gpbs):
            if isinstance(val, StructType):
                ifob__fgnh += "  if is_field_value_null(val, '{}'):\n".format(
                    arr.names[i])
                ifob__fgnh += (
                    '    bodo.libs.array_kernels.setna(data[{}], ind)\n'.
                    format(i))
                ifob__fgnh += '  else:\n'
                ifob__fgnh += "    data[{}][ind] = val['{}']\n".format(i,
                    arr.names[i])
            else:
                ifob__fgnh += "  data[{}][ind] = val['{}']\n".format(i, arr
                    .names[i])
        tnmgm__rlka = {}
        exec(ifob__fgnh, {'bodo': bodo, 'get_data': get_data,
            'get_null_bitmap': get_null_bitmap, 'set_bit_to_arr': bodo.libs
            .int_arr_ext.set_bit_to_arr, 'is_field_value_null':
            is_field_value_null}, tnmgm__rlka)
        impl = tnmgm__rlka['impl']
        return impl
    if isinstance(ind, types.SliceType):
        mqu__gpbs = len(arr.data)
        ifob__fgnh = 'def impl(arr, ind, val):\n'
        ifob__fgnh += '  data = get_data(arr)\n'
        ifob__fgnh += '  null_bitmap = get_null_bitmap(arr)\n'
        ifob__fgnh += '  val_data = get_data(val)\n'
        ifob__fgnh += '  val_null_bitmap = get_null_bitmap(val)\n'
        ifob__fgnh += """  setitem_slice_index_null_bits(null_bitmap, val_null_bitmap, ind, len(arr))
"""
        for i in range(mqu__gpbs):
            ifob__fgnh += '  data[{0}][ind] = val_data[{0}]\n'.format(i)
        tnmgm__rlka = {}
        exec(ifob__fgnh, {'bodo': bodo, 'get_data': get_data,
            'get_null_bitmap': get_null_bitmap, 'set_bit_to_arr': bodo.libs
            .int_arr_ext.set_bit_to_arr, 'setitem_slice_index_null_bits':
            bodo.utils.indexing.setitem_slice_index_null_bits}, tnmgm__rlka)
        impl = tnmgm__rlka['impl']
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
    ifob__fgnh = 'def impl(A):\n'
    ifob__fgnh += '  total_nbytes = 0\n'
    ifob__fgnh += '  data = get_data(A)\n'
    for i in range(len(A.data)):
        ifob__fgnh += f'  total_nbytes += data[{i}].nbytes\n'
    ifob__fgnh += '  total_nbytes += get_null_bitmap(A).nbytes\n'
    ifob__fgnh += '  return total_nbytes\n'
    tnmgm__rlka = {}
    exec(ifob__fgnh, {'get_data': get_data, 'get_null_bitmap':
        get_null_bitmap}, tnmgm__rlka)
    impl = tnmgm__rlka['impl']
    return impl


@overload_method(StructArrayType, 'copy', no_unliteral=True)
def overload_struct_arr_copy(A):
    names = A.names

    def copy_impl(A):
        data = get_data(A)
        itycp__hmb = get_null_bitmap(A)
        tspjm__knama = bodo.ir.join.copy_arr_tup(data)
        unm__mbjji = itycp__hmb.copy()
        return init_struct_arr(tspjm__knama, unm__mbjji, names)
    return copy_impl
