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
            .utils.is_array_typ(vfu__eci, False) for vfu__eci in data)
        if names is not None:
            assert isinstance(names, tuple) and all(isinstance(vfu__eci,
                str) for vfu__eci in names) and len(names) == len(data)
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
        return StructType(tuple(ofvl__pnsg.dtype for ofvl__pnsg in self.
            data), self.names)

    @classmethod
    def from_dict(cls, d):
        assert isinstance(d, dict)
        names = tuple(str(vfu__eci) for vfu__eci in d.keys())
        data = tuple(dtype_to_array_type(ofvl__pnsg) for ofvl__pnsg in d.
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
            is_array_typ(vfu__eci, False) for vfu__eci in data)
        self.data = data
        super(StructArrayPayloadType, self).__init__(name=
            'StructArrayPayloadType({})'.format(data))

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(StructArrayPayloadType)
class StructArrayPayloadModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        qiu__swihs = [('data', types.BaseTuple.from_types(fe_type.data)), (
            'null_bitmap', types.Array(types.uint8, 1, 'C'))]
        models.StructModel.__init__(self, dmm, fe_type, qiu__swihs)


@register_model(StructArrayType)
class StructArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = StructArrayPayloadType(fe_type.data)
        qiu__swihs = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, qiu__swihs)


def define_struct_arr_dtor(context, builder, struct_arr_type, payload_type):
    gzmq__yccy = builder.module
    njf__mcuk = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    mzxg__rua = cgutils.get_or_insert_function(gzmq__yccy, njf__mcuk, name=
        '.dtor.struct_arr.{}.{}.'.format(struct_arr_type.data,
        struct_arr_type.names))
    if not mzxg__rua.is_declaration:
        return mzxg__rua
    mzxg__rua.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(mzxg__rua.append_basic_block())
    wjqpq__ftlmn = mzxg__rua.args[0]
    hll__ufrla = context.get_value_type(payload_type).as_pointer()
    rfsei__kdav = builder.bitcast(wjqpq__ftlmn, hll__ufrla)
    woia__hcbcv = context.make_helper(builder, payload_type, ref=rfsei__kdav)
    context.nrt.decref(builder, types.BaseTuple.from_types(struct_arr_type.
        data), woia__hcbcv.data)
    context.nrt.decref(builder, types.Array(types.uint8, 1, 'C'),
        woia__hcbcv.null_bitmap)
    builder.ret_void()
    return mzxg__rua


def construct_struct_array(context, builder, struct_arr_type, n_structs,
    n_elems, c=None):
    payload_type = StructArrayPayloadType(struct_arr_type.data)
    mdzzq__ulvk = context.get_value_type(payload_type)
    wyy__rktwr = context.get_abi_sizeof(mdzzq__ulvk)
    dqska__hvsus = define_struct_arr_dtor(context, builder, struct_arr_type,
        payload_type)
    mvbsr__rwjud = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, wyy__rktwr), dqska__hvsus)
    srqzl__kpaxt = context.nrt.meminfo_data(builder, mvbsr__rwjud)
    yqz__kpm = builder.bitcast(srqzl__kpaxt, mdzzq__ulvk.as_pointer())
    woia__hcbcv = cgutils.create_struct_proxy(payload_type)(context, builder)
    bpb__xqr = []
    fzls__xpmk = 0
    for arr_typ in struct_arr_type.data:
        sxiid__vzlde = bodo.utils.transform.get_type_alloc_counts(arr_typ.dtype
            )
        hcqs__phxm = cgutils.pack_array(builder, [n_structs] + [builder.
            extract_value(n_elems, i) for i in range(fzls__xpmk, fzls__xpmk +
            sxiid__vzlde)])
        arr = gen_allocate_array(context, builder, arr_typ, hcqs__phxm, c)
        bpb__xqr.append(arr)
        fzls__xpmk += sxiid__vzlde
    woia__hcbcv.data = cgutils.pack_array(builder, bpb__xqr
        ) if types.is_homogeneous(*struct_arr_type.data
        ) else cgutils.pack_struct(builder, bpb__xqr)
    eyp__hss = builder.udiv(builder.add(n_structs, lir.Constant(lir.IntType
        (64), 7)), lir.Constant(lir.IntType(64), 8))
    usmc__alo = bodo.utils.utils._empty_nd_impl(context, builder, types.
        Array(types.uint8, 1, 'C'), [eyp__hss])
    null_bitmap_ptr = usmc__alo.data
    woia__hcbcv.null_bitmap = usmc__alo._getvalue()
    builder.store(woia__hcbcv._getvalue(), yqz__kpm)
    return mvbsr__rwjud, woia__hcbcv.data, null_bitmap_ptr


def _get_C_API_ptrs(c, data_tup, data_typ, names):
    bxzf__lofdo = []
    assert len(data_typ) > 0
    for i, arr_typ in enumerate(data_typ):
        qik__edhh = c.builder.extract_value(data_tup, i)
        arr = c.context.make_array(arr_typ)(c.context, c.builder, value=
            qik__edhh)
        bxzf__lofdo.append(arr.data)
    aldck__yih = cgutils.pack_array(c.builder, bxzf__lofdo
        ) if types.is_homogeneous(*data_typ) else cgutils.pack_struct(c.
        builder, bxzf__lofdo)
    njhs__ics = cgutils.alloca_once_value(c.builder, aldck__yih)
    hum__libb = [c.context.get_constant(types.int32, bodo.utils.utils.
        numba_to_c_type(vfu__eci.dtype)) for vfu__eci in data_typ]
    jytuz__yqji = cgutils.alloca_once_value(c.builder, cgutils.pack_array(c
        .builder, hum__libb))
    yrw__flkyg = cgutils.pack_array(c.builder, [c.context.
        insert_const_string(c.builder.module, vfu__eci) for vfu__eci in names])
    mznvv__ifx = cgutils.alloca_once_value(c.builder, yrw__flkyg)
    return njhs__ics, jytuz__yqji, mznvv__ifx


@unbox(StructArrayType)
def unbox_struct_array(typ, val, c, is_tuple_array=False):
    from bodo.libs.tuple_arr_ext import TupleArrayType
    n_structs = bodo.utils.utils.object_length(c, val)
    vqreq__xfl = all(isinstance(ofvl__pnsg, types.Array) and ofvl__pnsg.
        dtype in (types.int64, types.float64, types.bool_,
        datetime_date_type) for ofvl__pnsg in typ.data)
    if vqreq__xfl:
        n_elems = cgutils.pack_array(c.builder, [], lir.IntType(64))
    else:
        ndwjz__xhfun = get_array_elem_counts(c, c.builder, c.context, val, 
            TupleArrayType(typ.data) if is_tuple_array else typ)
        n_elems = cgutils.pack_array(c.builder, [c.builder.extract_value(
            ndwjz__xhfun, i) for i in range(1, ndwjz__xhfun.type.count)],
            lir.IntType(64))
    mvbsr__rwjud, data_tup, null_bitmap_ptr = construct_struct_array(c.
        context, c.builder, typ, n_structs, n_elems, c)
    if vqreq__xfl:
        njhs__ics, jytuz__yqji, mznvv__ifx = _get_C_API_ptrs(c, data_tup,
            typ.data, typ.names)
        njf__mcuk = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(32), lir.IntType(8).as_pointer(), lir
            .IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1)])
        mzxg__rua = cgutils.get_or_insert_function(c.builder.module,
            njf__mcuk, name='struct_array_from_sequence')
        c.builder.call(mzxg__rua, [val, c.context.get_constant(types.int32,
            len(typ.data)), c.builder.bitcast(njhs__ics, lir.IntType(8).
            as_pointer()), null_bitmap_ptr, c.builder.bitcast(jytuz__yqji,
            lir.IntType(8).as_pointer()), c.builder.bitcast(mznvv__ifx, lir
            .IntType(8).as_pointer()), c.context.get_constant(types.bool_,
            is_tuple_array)])
    else:
        _unbox_struct_array_generic(typ, val, c, n_structs, data_tup,
            null_bitmap_ptr, is_tuple_array)
    hsoc__mnkza = c.context.make_helper(c.builder, typ)
    hsoc__mnkza.meminfo = mvbsr__rwjud
    wvu__zsvfx = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(hsoc__mnkza._getvalue(), is_error=wvu__zsvfx)


def _unbox_struct_array_generic(typ, val, c, n_structs, data_tup,
    null_bitmap_ptr, is_tuple_array=False):
    context = c.context
    builder = c.builder
    utp__oeaf = context.insert_const_string(builder.module, 'pandas')
    wsfkb__cmkx = c.pyapi.import_module_noblock(utp__oeaf)
    cml__rbjtf = c.pyapi.object_getattr_string(wsfkb__cmkx, 'NA')
    with cgutils.for_range(builder, n_structs) as lnf__hgtdu:
        qmroj__rwkv = lnf__hgtdu.index
        ofenh__bgfq = seq_getitem(builder, context, val, qmroj__rwkv)
        set_bitmap_bit(builder, null_bitmap_ptr, qmroj__rwkv, 0)
        for kvnxm__jzk in range(len(typ.data)):
            arr_typ = typ.data[kvnxm__jzk]
            data_arr = builder.extract_value(data_tup, kvnxm__jzk)

            def set_na(data_arr, i):
                bodo.libs.array_kernels.setna(data_arr, i)
            sig = types.none(arr_typ, types.int64)
            vpp__lkr, wkgu__kfq = c.pyapi.call_jit_code(set_na, sig, [
                data_arr, qmroj__rwkv])
        ebqf__rejwo = is_na_value(builder, context, ofenh__bgfq, cml__rbjtf)
        axga__dys = builder.icmp_unsigned('!=', ebqf__rejwo, lir.Constant(
            ebqf__rejwo.type, 1))
        with builder.if_then(axga__dys):
            set_bitmap_bit(builder, null_bitmap_ptr, qmroj__rwkv, 1)
            for kvnxm__jzk in range(len(typ.data)):
                arr_typ = typ.data[kvnxm__jzk]
                if is_tuple_array:
                    szr__uzbst = c.pyapi.tuple_getitem(ofenh__bgfq, kvnxm__jzk)
                else:
                    szr__uzbst = c.pyapi.dict_getitem_string(ofenh__bgfq,
                        typ.names[kvnxm__jzk])
                ebqf__rejwo = is_na_value(builder, context, szr__uzbst,
                    cml__rbjtf)
                axga__dys = builder.icmp_unsigned('!=', ebqf__rejwo, lir.
                    Constant(ebqf__rejwo.type, 1))
                with builder.if_then(axga__dys):
                    szr__uzbst = to_arr_obj_if_list_obj(c, context, builder,
                        szr__uzbst, arr_typ.dtype)
                    field_val = c.pyapi.to_native_value(arr_typ.dtype,
                        szr__uzbst).value
                    data_arr = builder.extract_value(data_tup, kvnxm__jzk)

                    def set_data(data_arr, i, field_val):
                        data_arr[i] = field_val
                    sig = types.none(arr_typ, types.int64, arr_typ.dtype)
                    vpp__lkr, wkgu__kfq = c.pyapi.call_jit_code(set_data,
                        sig, [data_arr, qmroj__rwkv, field_val])
                    c.context.nrt.decref(builder, arr_typ.dtype, field_val)
        c.pyapi.decref(ofenh__bgfq)
    c.pyapi.decref(wsfkb__cmkx)
    c.pyapi.decref(cml__rbjtf)


def _get_struct_arr_payload(context, builder, arr_typ, arr):
    hsoc__mnkza = context.make_helper(builder, arr_typ, arr)
    payload_type = StructArrayPayloadType(arr_typ.data)
    srqzl__kpaxt = context.nrt.meminfo_data(builder, hsoc__mnkza.meminfo)
    yqz__kpm = builder.bitcast(srqzl__kpaxt, context.get_value_type(
        payload_type).as_pointer())
    woia__hcbcv = cgutils.create_struct_proxy(payload_type)(context,
        builder, builder.load(yqz__kpm))
    return woia__hcbcv


@box(StructArrayType)
def box_struct_arr(typ, val, c, is_tuple_array=False):
    woia__hcbcv = _get_struct_arr_payload(c.context, c.builder, typ, val)
    vpp__lkr, length = c.pyapi.call_jit_code(lambda A: len(A), types.int64(
        typ), [val])
    null_bitmap_ptr = c.context.make_helper(c.builder, types.Array(types.
        uint8, 1, 'C'), woia__hcbcv.null_bitmap).data
    vqreq__xfl = all(isinstance(ofvl__pnsg, types.Array) and ofvl__pnsg.
        dtype in (types.int64, types.float64, types.bool_,
        datetime_date_type) for ofvl__pnsg in typ.data)
    if vqreq__xfl:
        njhs__ics, jytuz__yqji, mznvv__ifx = _get_C_API_ptrs(c, woia__hcbcv
            .data, typ.data, typ.names)
        njf__mcuk = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(32), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1)])
        bay__upuy = cgutils.get_or_insert_function(c.builder.module,
            njf__mcuk, name='np_array_from_struct_array')
        arr = c.builder.call(bay__upuy, [length, c.context.get_constant(
            types.int32, len(typ.data)), c.builder.bitcast(njhs__ics, lir.
            IntType(8).as_pointer()), null_bitmap_ptr, c.builder.bitcast(
            jytuz__yqji, lir.IntType(8).as_pointer()), c.builder.bitcast(
            mznvv__ifx, lir.IntType(8).as_pointer()), c.context.
            get_constant(types.bool_, is_tuple_array)])
    else:
        arr = _box_struct_array_generic(typ, c, length, woia__hcbcv.data,
            null_bitmap_ptr, is_tuple_array)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def _box_struct_array_generic(typ, c, length, data_arrs_tup,
    null_bitmap_ptr, is_tuple_array=False):
    context = c.context
    builder = c.builder
    utp__oeaf = context.insert_const_string(builder.module, 'numpy')
    kgmta__thoqd = c.pyapi.import_module_noblock(utp__oeaf)
    gmoo__ercv = c.pyapi.object_getattr_string(kgmta__thoqd, 'object_')
    odh__ywu = c.pyapi.long_from_longlong(length)
    pnq__sqf = c.pyapi.call_method(kgmta__thoqd, 'ndarray', (odh__ywu,
        gmoo__ercv))
    gqtkc__imkmw = c.pyapi.object_getattr_string(kgmta__thoqd, 'nan')
    with cgutils.for_range(builder, length) as lnf__hgtdu:
        qmroj__rwkv = lnf__hgtdu.index
        pyarray_setitem(builder, context, pnq__sqf, qmroj__rwkv, gqtkc__imkmw)
        cbpdz__bnr = get_bitmap_bit(builder, null_bitmap_ptr, qmroj__rwkv)
        orbp__vygqg = builder.icmp_unsigned('!=', cbpdz__bnr, lir.Constant(
            lir.IntType(8), 0))
        with builder.if_then(orbp__vygqg):
            if is_tuple_array:
                ofenh__bgfq = c.pyapi.tuple_new(len(typ.data))
            else:
                ofenh__bgfq = c.pyapi.dict_new(len(typ.data))
            for i, arr_typ in enumerate(typ.data):
                if is_tuple_array:
                    c.pyapi.incref(gqtkc__imkmw)
                    c.pyapi.tuple_setitem(ofenh__bgfq, i, gqtkc__imkmw)
                else:
                    c.pyapi.dict_setitem_string(ofenh__bgfq, typ.names[i],
                        gqtkc__imkmw)
                data_arr = c.builder.extract_value(data_arrs_tup, i)
                vpp__lkr, dtz__ppv = c.pyapi.call_jit_code(lambda data_arr,
                    ind: not bodo.libs.array_kernels.isna(data_arr, ind),
                    types.bool_(arr_typ, types.int64), [data_arr, qmroj__rwkv])
                with builder.if_then(dtz__ppv):
                    vpp__lkr, field_val = c.pyapi.call_jit_code(lambda
                        data_arr, ind: data_arr[ind], arr_typ.dtype(arr_typ,
                        types.int64), [data_arr, qmroj__rwkv])
                    mzko__wfdy = c.pyapi.from_native_value(arr_typ.dtype,
                        field_val, c.env_manager)
                    if is_tuple_array:
                        c.pyapi.tuple_setitem(ofenh__bgfq, i, mzko__wfdy)
                    else:
                        c.pyapi.dict_setitem_string(ofenh__bgfq, typ.names[
                            i], mzko__wfdy)
                        c.pyapi.decref(mzko__wfdy)
            pyarray_setitem(builder, context, pnq__sqf, qmroj__rwkv,
                ofenh__bgfq)
            c.pyapi.decref(ofenh__bgfq)
    c.pyapi.decref(kgmta__thoqd)
    c.pyapi.decref(gmoo__ercv)
    c.pyapi.decref(odh__ywu)
    c.pyapi.decref(gqtkc__imkmw)
    return pnq__sqf


def _fix_nested_counts(nested_counts, struct_arr_type, nested_counts_type,
    builder):
    lhul__opqj = bodo.utils.transform.get_type_alloc_counts(struct_arr_type
        ) - 1
    if lhul__opqj == 0:
        return nested_counts
    if not isinstance(nested_counts_type, types.UniTuple):
        nested_counts = cgutils.pack_array(builder, [lir.Constant(lir.
            IntType(64), -1) for yombk__wmrhn in range(lhul__opqj)])
    elif nested_counts_type.count < lhul__opqj:
        nested_counts = cgutils.pack_array(builder, [builder.extract_value(
            nested_counts, i) for i in range(nested_counts_type.count)] + [
            lir.Constant(lir.IntType(64), -1) for yombk__wmrhn in range(
            lhul__opqj - nested_counts_type.count)])
    return nested_counts


@intrinsic
def pre_alloc_struct_array(typingctx, num_structs_typ, nested_counts_typ,
    dtypes_typ, names_typ=None):
    assert isinstance(num_structs_typ, types.Integer) and isinstance(dtypes_typ
        , types.BaseTuple)
    if is_overload_none(names_typ):
        names = tuple(f'f{i}' for i in range(len(dtypes_typ)))
    else:
        names = tuple(get_overload_const_str(ofvl__pnsg) for ofvl__pnsg in
            names_typ.types)
    rkoj__oeurl = tuple(ofvl__pnsg.instance_type for ofvl__pnsg in
        dtypes_typ.types)
    struct_arr_type = StructArrayType(rkoj__oeurl, names)

    def codegen(context, builder, sig, args):
        xbrma__zxc, nested_counts, yombk__wmrhn, yombk__wmrhn = args
        nested_counts_type = sig.args[1]
        nested_counts = _fix_nested_counts(nested_counts, struct_arr_type,
            nested_counts_type, builder)
        mvbsr__rwjud, yombk__wmrhn, yombk__wmrhn = construct_struct_array(
            context, builder, struct_arr_type, xbrma__zxc, nested_counts)
        hsoc__mnkza = context.make_helper(builder, struct_arr_type)
        hsoc__mnkza.meminfo = mvbsr__rwjud
        return hsoc__mnkza._getvalue()
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
        assert isinstance(names, tuple) and all(isinstance(vfu__eci, str) for
            vfu__eci in names) and len(names) == len(data)
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
        qiu__swihs = [('data', types.BaseTuple.from_types(fe_type.data)), (
            'null_bitmap', types.UniTuple(types.int8, len(fe_type.data)))]
        models.StructModel.__init__(self, dmm, fe_type, qiu__swihs)


@register_model(StructType)
class StructModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = StructPayloadType(fe_type.data)
        qiu__swihs = [('meminfo', types.MemInfoPointer(payload_type))]
        models.StructModel.__init__(self, dmm, fe_type, qiu__swihs)


def define_struct_dtor(context, builder, struct_type, payload_type):
    gzmq__yccy = builder.module
    njf__mcuk = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    mzxg__rua = cgutils.get_or_insert_function(gzmq__yccy, njf__mcuk, name=
        '.dtor.struct.{}.{}.'.format(struct_type.data, struct_type.names))
    if not mzxg__rua.is_declaration:
        return mzxg__rua
    mzxg__rua.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(mzxg__rua.append_basic_block())
    wjqpq__ftlmn = mzxg__rua.args[0]
    hll__ufrla = context.get_value_type(payload_type).as_pointer()
    rfsei__kdav = builder.bitcast(wjqpq__ftlmn, hll__ufrla)
    woia__hcbcv = context.make_helper(builder, payload_type, ref=rfsei__kdav)
    for i in range(len(struct_type.data)):
        hpual__eyjxu = builder.extract_value(woia__hcbcv.null_bitmap, i)
        orbp__vygqg = builder.icmp_unsigned('==', hpual__eyjxu, lir.
            Constant(hpual__eyjxu.type, 1))
        with builder.if_then(orbp__vygqg):
            val = builder.extract_value(woia__hcbcv.data, i)
            context.nrt.decref(builder, struct_type.data[i], val)
    builder.ret_void()
    return mzxg__rua


def _get_struct_payload(context, builder, typ, struct):
    struct = context.make_helper(builder, typ, struct)
    payload_type = StructPayloadType(typ.data)
    srqzl__kpaxt = context.nrt.meminfo_data(builder, struct.meminfo)
    yqz__kpm = builder.bitcast(srqzl__kpaxt, context.get_value_type(
        payload_type).as_pointer())
    woia__hcbcv = cgutils.create_struct_proxy(payload_type)(context,
        builder, builder.load(yqz__kpm))
    return woia__hcbcv, yqz__kpm


@unbox(StructType)
def unbox_struct(typ, val, c):
    context = c.context
    builder = c.builder
    utp__oeaf = context.insert_const_string(builder.module, 'pandas')
    wsfkb__cmkx = c.pyapi.import_module_noblock(utp__oeaf)
    cml__rbjtf = c.pyapi.object_getattr_string(wsfkb__cmkx, 'NA')
    gdd__ntf = []
    nulls = []
    for i, ofvl__pnsg in enumerate(typ.data):
        mzko__wfdy = c.pyapi.dict_getitem_string(val, typ.names[i])
        jndjt__eumsu = cgutils.alloca_once_value(c.builder, context.
            get_constant(types.uint8, 0))
        oxtrp__lumv = cgutils.alloca_once_value(c.builder, cgutils.
            get_null_value(context.get_value_type(ofvl__pnsg)))
        ebqf__rejwo = is_na_value(builder, context, mzko__wfdy, cml__rbjtf)
        orbp__vygqg = builder.icmp_unsigned('!=', ebqf__rejwo, lir.Constant
            (ebqf__rejwo.type, 1))
        with builder.if_then(orbp__vygqg):
            builder.store(context.get_constant(types.uint8, 1), jndjt__eumsu)
            field_val = c.pyapi.to_native_value(ofvl__pnsg, mzko__wfdy).value
            builder.store(field_val, oxtrp__lumv)
        gdd__ntf.append(builder.load(oxtrp__lumv))
        nulls.append(builder.load(jndjt__eumsu))
    c.pyapi.decref(wsfkb__cmkx)
    c.pyapi.decref(cml__rbjtf)
    mvbsr__rwjud = construct_struct(context, builder, typ, gdd__ntf, nulls)
    struct = context.make_helper(builder, typ)
    struct.meminfo = mvbsr__rwjud
    wvu__zsvfx = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(struct._getvalue(), is_error=wvu__zsvfx)


@box(StructType)
def box_struct(typ, val, c):
    dss__aqoca = c.pyapi.dict_new(len(typ.data))
    woia__hcbcv, yombk__wmrhn = _get_struct_payload(c.context, c.builder,
        typ, val)
    assert len(typ.data) > 0
    for i, val_typ in enumerate(typ.data):
        c.pyapi.dict_setitem_string(dss__aqoca, typ.names[i], c.pyapi.
            borrow_none())
        hpual__eyjxu = c.builder.extract_value(woia__hcbcv.null_bitmap, i)
        orbp__vygqg = c.builder.icmp_unsigned('==', hpual__eyjxu, lir.
            Constant(hpual__eyjxu.type, 1))
        with c.builder.if_then(orbp__vygqg):
            klxj__uzm = c.builder.extract_value(woia__hcbcv.data, i)
            c.context.nrt.incref(c.builder, val_typ, klxj__uzm)
            szr__uzbst = c.pyapi.from_native_value(val_typ, klxj__uzm, c.
                env_manager)
            c.pyapi.dict_setitem_string(dss__aqoca, typ.names[i], szr__uzbst)
            c.pyapi.decref(szr__uzbst)
    c.context.nrt.decref(c.builder, typ, val)
    return dss__aqoca


@intrinsic
def init_struct(typingctx, data_typ, names_typ=None):
    names = tuple(get_overload_const_str(ofvl__pnsg) for ofvl__pnsg in
        names_typ.types)
    struct_type = StructType(data_typ.types, names)

    def codegen(context, builder, sig, args):
        data, jro__gwcsa = args
        payload_type = StructPayloadType(struct_type.data)
        mdzzq__ulvk = context.get_value_type(payload_type)
        wyy__rktwr = context.get_abi_sizeof(mdzzq__ulvk)
        dqska__hvsus = define_struct_dtor(context, builder, struct_type,
            payload_type)
        mvbsr__rwjud = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, wyy__rktwr), dqska__hvsus)
        srqzl__kpaxt = context.nrt.meminfo_data(builder, mvbsr__rwjud)
        yqz__kpm = builder.bitcast(srqzl__kpaxt, mdzzq__ulvk.as_pointer())
        woia__hcbcv = cgutils.create_struct_proxy(payload_type)(context,
            builder)
        woia__hcbcv.data = data
        woia__hcbcv.null_bitmap = cgutils.pack_array(builder, [context.
            get_constant(types.uint8, 1) for yombk__wmrhn in range(len(
            data_typ.types))])
        builder.store(woia__hcbcv._getvalue(), yqz__kpm)
        context.nrt.incref(builder, data_typ, data)
        struct = context.make_helper(builder, struct_type)
        struct.meminfo = mvbsr__rwjud
        return struct._getvalue()
    return struct_type(data_typ, names_typ), codegen


@intrinsic
def get_struct_data(typingctx, struct_typ=None):
    assert isinstance(struct_typ, StructType)

    def codegen(context, builder, sig, args):
        struct, = args
        woia__hcbcv, yombk__wmrhn = _get_struct_payload(context, builder,
            struct_typ, struct)
        return impl_ret_borrowed(context, builder, sig.return_type,
            woia__hcbcv.data)
    return types.BaseTuple.from_types(struct_typ.data)(struct_typ), codegen


@intrinsic
def get_struct_null_bitmap(typingctx, struct_typ=None):
    assert isinstance(struct_typ, StructType)

    def codegen(context, builder, sig, args):
        struct, = args
        woia__hcbcv, yombk__wmrhn = _get_struct_payload(context, builder,
            struct_typ, struct)
        return impl_ret_borrowed(context, builder, sig.return_type,
            woia__hcbcv.null_bitmap)
    pinft__etrx = types.UniTuple(types.int8, len(struct_typ.data))
    return pinft__etrx(struct_typ), codegen


@intrinsic
def set_struct_data(typingctx, struct_typ, field_ind_typ, val_typ=None):
    assert isinstance(struct_typ, StructType) and is_overload_constant_int(
        field_ind_typ)
    field_ind = get_overload_const_int(field_ind_typ)

    def codegen(context, builder, sig, args):
        struct, yombk__wmrhn, val = args
        woia__hcbcv, yqz__kpm = _get_struct_payload(context, builder,
            struct_typ, struct)
        qin__pddhw = woia__hcbcv.data
        spdbb__xnhd = builder.insert_value(qin__pddhw, val, field_ind)
        ula__kqmtx = types.BaseTuple.from_types(struct_typ.data)
        context.nrt.decref(builder, ula__kqmtx, qin__pddhw)
        context.nrt.incref(builder, ula__kqmtx, spdbb__xnhd)
        woia__hcbcv.data = spdbb__xnhd
        builder.store(woia__hcbcv._getvalue(), yqz__kpm)
        return context.get_dummy_value()
    return types.none(struct_typ, field_ind_typ, val_typ), codegen


def _get_struct_field_ind(struct, ind, op):
    if not is_overload_constant_str(ind):
        raise BodoError(
            'structs (from struct array) only support constant strings for {}, not {}'
            .format(op, ind))
    aaqrd__edda = get_overload_const_str(ind)
    if aaqrd__edda not in struct.names:
        raise BodoError('Field {} does not exist in struct {}'.format(
            aaqrd__edda, struct))
    return struct.names.index(aaqrd__edda)


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
    mdzzq__ulvk = context.get_value_type(payload_type)
    wyy__rktwr = context.get_abi_sizeof(mdzzq__ulvk)
    dqska__hvsus = define_struct_dtor(context, builder, struct_type,
        payload_type)
    mvbsr__rwjud = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, wyy__rktwr), dqska__hvsus)
    srqzl__kpaxt = context.nrt.meminfo_data(builder, mvbsr__rwjud)
    yqz__kpm = builder.bitcast(srqzl__kpaxt, mdzzq__ulvk.as_pointer())
    woia__hcbcv = cgutils.create_struct_proxy(payload_type)(context, builder)
    woia__hcbcv.data = cgutils.pack_array(builder, values
        ) if types.is_homogeneous(*struct_type.data) else cgutils.pack_struct(
        builder, values)
    woia__hcbcv.null_bitmap = cgutils.pack_array(builder, nulls)
    builder.store(woia__hcbcv._getvalue(), yqz__kpm)
    return mvbsr__rwjud


@intrinsic
def struct_array_get_struct(typingctx, struct_arr_typ, ind_typ=None):
    assert isinstance(struct_arr_typ, StructArrayType) and isinstance(ind_typ,
        types.Integer)
    lkwzi__bjwc = tuple(d.dtype for d in struct_arr_typ.data)
    yiddu__arelo = StructType(lkwzi__bjwc, struct_arr_typ.names)

    def codegen(context, builder, sig, args):
        eqk__chdm, ind = args
        woia__hcbcv = _get_struct_arr_payload(context, builder,
            struct_arr_typ, eqk__chdm)
        gdd__ntf = []
        uptu__zzqmw = []
        for i, arr_typ in enumerate(struct_arr_typ.data):
            qik__edhh = builder.extract_value(woia__hcbcv.data, i)
            wyi__sas = context.compile_internal(builder, lambda arr, ind: 
                np.uint8(0) if bodo.libs.array_kernels.isna(arr, ind) else
                np.uint8(1), types.uint8(arr_typ, types.int64), [qik__edhh,
                ind])
            uptu__zzqmw.append(wyi__sas)
            ahau__sbszg = cgutils.alloca_once_value(builder, context.
                get_constant_null(arr_typ.dtype))
            orbp__vygqg = builder.icmp_unsigned('==', wyi__sas, lir.
                Constant(wyi__sas.type, 1))
            with builder.if_then(orbp__vygqg):
                nlz__puex = context.compile_internal(builder, lambda arr,
                    ind: arr[ind], arr_typ.dtype(arr_typ, types.int64), [
                    qik__edhh, ind])
                builder.store(nlz__puex, ahau__sbszg)
            gdd__ntf.append(builder.load(ahau__sbszg))
        if isinstance(yiddu__arelo, types.DictType):
            bna__tjkdy = [context.insert_const_string(builder.module,
                sqin__ltvcs) for sqin__ltvcs in struct_arr_typ.names]
            tio__gwuf = cgutils.pack_array(builder, gdd__ntf)
            tsu__myw = cgutils.pack_array(builder, bna__tjkdy)

            def impl(names, vals):
                d = {}
                for i, sqin__ltvcs in enumerate(names):
                    d[sqin__ltvcs] = vals[i]
                return d
            vmpou__ojef = context.compile_internal(builder, impl,
                yiddu__arelo(types.Tuple(tuple(types.StringLiteral(
                sqin__ltvcs) for sqin__ltvcs in struct_arr_typ.names)),
                types.Tuple(lkwzi__bjwc)), [tsu__myw, tio__gwuf])
            context.nrt.decref(builder, types.BaseTuple.from_types(
                lkwzi__bjwc), tio__gwuf)
            return vmpou__ojef
        mvbsr__rwjud = construct_struct(context, builder, yiddu__arelo,
            gdd__ntf, uptu__zzqmw)
        struct = context.make_helper(builder, yiddu__arelo)
        struct.meminfo = mvbsr__rwjud
        return struct._getvalue()
    return yiddu__arelo(struct_arr_typ, ind_typ), codegen


@intrinsic
def get_data(typingctx, arr_typ=None):
    assert isinstance(arr_typ, StructArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        woia__hcbcv = _get_struct_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            woia__hcbcv.data)
    return types.BaseTuple.from_types(arr_typ.data)(arr_typ), codegen


@intrinsic
def get_null_bitmap(typingctx, arr_typ=None):
    assert isinstance(arr_typ, StructArrayType)

    def codegen(context, builder, sig, args):
        arr, = args
        woia__hcbcv = _get_struct_arr_payload(context, builder, arr_typ, arr)
        return impl_ret_borrowed(context, builder, sig.return_type,
            woia__hcbcv.null_bitmap)
    return types.Array(types.uint8, 1, 'C')(arr_typ), codegen


@intrinsic
def init_struct_arr(typingctx, data_typ, null_bitmap_typ, names_typ=None):
    names = tuple(get_overload_const_str(ofvl__pnsg) for ofvl__pnsg in
        names_typ.types)
    struct_arr_type = StructArrayType(data_typ.types, names)

    def codegen(context, builder, sig, args):
        data, usmc__alo, jro__gwcsa = args
        payload_type = StructArrayPayloadType(struct_arr_type.data)
        mdzzq__ulvk = context.get_value_type(payload_type)
        wyy__rktwr = context.get_abi_sizeof(mdzzq__ulvk)
        dqska__hvsus = define_struct_arr_dtor(context, builder,
            struct_arr_type, payload_type)
        mvbsr__rwjud = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, wyy__rktwr), dqska__hvsus)
        srqzl__kpaxt = context.nrt.meminfo_data(builder, mvbsr__rwjud)
        yqz__kpm = builder.bitcast(srqzl__kpaxt, mdzzq__ulvk.as_pointer())
        woia__hcbcv = cgutils.create_struct_proxy(payload_type)(context,
            builder)
        woia__hcbcv.data = data
        woia__hcbcv.null_bitmap = usmc__alo
        builder.store(woia__hcbcv._getvalue(), yqz__kpm)
        context.nrt.incref(builder, data_typ, data)
        context.nrt.incref(builder, null_bitmap_typ, usmc__alo)
        hsoc__mnkza = context.make_helper(builder, struct_arr_type)
        hsoc__mnkza.meminfo = mvbsr__rwjud
        return hsoc__mnkza._getvalue()
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
    iny__xryxd = len(arr.data)
    ddhlu__mvn = 'def impl(arr, ind):\n'
    ddhlu__mvn += '  data = get_data(arr)\n'
    ddhlu__mvn += '  null_bitmap = get_null_bitmap(arr)\n'
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        ddhlu__mvn += """  out_null_bitmap = get_new_null_mask_bool_index(null_bitmap, ind, len(data[0]))
"""
    elif is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        ddhlu__mvn += """  out_null_bitmap = get_new_null_mask_int_index(null_bitmap, ind, len(data[0]))
"""
    elif isinstance(ind, types.SliceType):
        ddhlu__mvn += """  out_null_bitmap = get_new_null_mask_slice_index(null_bitmap, ind, len(data[0]))
"""
    else:
        raise BodoError('invalid index {} in struct array indexing'.format(ind)
            )
    ddhlu__mvn += ('  return init_struct_arr(({},), out_null_bitmap, ({},))\n'
        .format(', '.join('ensure_contig_if_np(data[{}][ind])'.format(i) for
        i in range(iny__xryxd)), ', '.join("'{}'".format(sqin__ltvcs) for
        sqin__ltvcs in arr.names)))
    bnu__mjhsf = {}
    exec(ddhlu__mvn, {'init_struct_arr': init_struct_arr, 'get_data':
        get_data, 'get_null_bitmap': get_null_bitmap, 'ensure_contig_if_np':
        bodo.utils.conversion.ensure_contig_if_np,
        'get_new_null_mask_bool_index': bodo.utils.indexing.
        get_new_null_mask_bool_index, 'get_new_null_mask_int_index': bodo.
        utils.indexing.get_new_null_mask_int_index,
        'get_new_null_mask_slice_index': bodo.utils.indexing.
        get_new_null_mask_slice_index}, bnu__mjhsf)
    impl = bnu__mjhsf['impl']
    return impl


@overload(operator.setitem, no_unliteral=True)
def struct_arr_setitem(arr, ind, val):
    if not isinstance(arr, StructArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    if isinstance(ind, types.Integer):
        iny__xryxd = len(arr.data)
        ddhlu__mvn = 'def impl(arr, ind, val):\n'
        ddhlu__mvn += '  data = get_data(arr)\n'
        ddhlu__mvn += '  null_bitmap = get_null_bitmap(arr)\n'
        ddhlu__mvn += '  set_bit_to_arr(null_bitmap, ind, 1)\n'
        for i in range(iny__xryxd):
            if isinstance(val, StructType):
                ddhlu__mvn += "  if is_field_value_null(val, '{}'):\n".format(
                    arr.names[i])
                ddhlu__mvn += (
                    '    bodo.libs.array_kernels.setna(data[{}], ind)\n'.
                    format(i))
                ddhlu__mvn += '  else:\n'
                ddhlu__mvn += "    data[{}][ind] = val['{}']\n".format(i,
                    arr.names[i])
            else:
                ddhlu__mvn += "  data[{}][ind] = val['{}']\n".format(i, arr
                    .names[i])
        bnu__mjhsf = {}
        exec(ddhlu__mvn, {'bodo': bodo, 'get_data': get_data,
            'get_null_bitmap': get_null_bitmap, 'set_bit_to_arr': bodo.libs
            .int_arr_ext.set_bit_to_arr, 'is_field_value_null':
            is_field_value_null}, bnu__mjhsf)
        impl = bnu__mjhsf['impl']
        return impl
    if isinstance(ind, types.SliceType):
        iny__xryxd = len(arr.data)
        ddhlu__mvn = 'def impl(arr, ind, val):\n'
        ddhlu__mvn += '  data = get_data(arr)\n'
        ddhlu__mvn += '  null_bitmap = get_null_bitmap(arr)\n'
        ddhlu__mvn += '  val_data = get_data(val)\n'
        ddhlu__mvn += '  val_null_bitmap = get_null_bitmap(val)\n'
        ddhlu__mvn += """  setitem_slice_index_null_bits(null_bitmap, val_null_bitmap, ind, len(arr))
"""
        for i in range(iny__xryxd):
            ddhlu__mvn += '  data[{0}][ind] = val_data[{0}]\n'.format(i)
        bnu__mjhsf = {}
        exec(ddhlu__mvn, {'bodo': bodo, 'get_data': get_data,
            'get_null_bitmap': get_null_bitmap, 'set_bit_to_arr': bodo.libs
            .int_arr_ext.set_bit_to_arr, 'setitem_slice_index_null_bits':
            bodo.utils.indexing.setitem_slice_index_null_bits}, bnu__mjhsf)
        impl = bnu__mjhsf['impl']
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
    ddhlu__mvn = 'def impl(A):\n'
    ddhlu__mvn += '  total_nbytes = 0\n'
    ddhlu__mvn += '  data = get_data(A)\n'
    for i in range(len(A.data)):
        ddhlu__mvn += f'  total_nbytes += data[{i}].nbytes\n'
    ddhlu__mvn += '  total_nbytes += get_null_bitmap(A).nbytes\n'
    ddhlu__mvn += '  return total_nbytes\n'
    bnu__mjhsf = {}
    exec(ddhlu__mvn, {'get_data': get_data, 'get_null_bitmap':
        get_null_bitmap}, bnu__mjhsf)
    impl = bnu__mjhsf['impl']
    return impl


@overload_method(StructArrayType, 'copy', no_unliteral=True)
def overload_struct_arr_copy(A):
    names = A.names

    def copy_impl(A):
        data = get_data(A)
        usmc__alo = get_null_bitmap(A)
        xsst__wpdyp = bodo.ir.join.copy_arr_tup(data)
        oox__vbf = usmc__alo.copy()
        return init_struct_arr(xsst__wpdyp, oox__vbf, names)
    return copy_impl
