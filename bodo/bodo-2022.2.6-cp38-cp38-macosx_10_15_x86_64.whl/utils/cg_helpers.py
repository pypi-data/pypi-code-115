"""helper functions for code generation with llvmlite
"""
import llvmlite.binding as ll
from llvmlite import ir as lir
from numba.core import cgutils, types
import bodo
from bodo.libs import array_ext, hdist
ll.add_symbol('array_getitem', array_ext.array_getitem)
ll.add_symbol('seq_getitem', array_ext.seq_getitem)
ll.add_symbol('list_check', array_ext.list_check)
ll.add_symbol('dict_keys', array_ext.dict_keys)
ll.add_symbol('dict_values', array_ext.dict_values)
ll.add_symbol('dict_merge_from_seq2', array_ext.dict_merge_from_seq2)
ll.add_symbol('is_na_value', array_ext.is_na_value)


def set_bitmap_bit(builder, null_bitmap_ptr, ind, val):
    pufjd__fviw = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
    yeui__ltt = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
    ebqm__lhyk = builder.gep(null_bitmap_ptr, [pufjd__fviw], inbounds=True)
    krg__lhrry = builder.load(ebqm__lhyk)
    cnw__fvh = lir.ArrayType(lir.IntType(8), 8)
    qymhi__pjbd = cgutils.alloca_once_value(builder, lir.Constant(cnw__fvh,
        (1, 2, 4, 8, 16, 32, 64, 128)))
    vjl__bdtc = builder.load(builder.gep(qymhi__pjbd, [lir.Constant(lir.
        IntType(64), 0), yeui__ltt], inbounds=True))
    if val:
        builder.store(builder.or_(krg__lhrry, vjl__bdtc), ebqm__lhyk)
    else:
        vjl__bdtc = builder.xor(vjl__bdtc, lir.Constant(lir.IntType(8), -1))
        builder.store(builder.and_(krg__lhrry, vjl__bdtc), ebqm__lhyk)


def get_bitmap_bit(builder, null_bitmap_ptr, ind):
    pufjd__fviw = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
    yeui__ltt = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
    krg__lhrry = builder.load(builder.gep(null_bitmap_ptr, [pufjd__fviw],
        inbounds=True))
    cnw__fvh = lir.ArrayType(lir.IntType(8), 8)
    qymhi__pjbd = cgutils.alloca_once_value(builder, lir.Constant(cnw__fvh,
        (1, 2, 4, 8, 16, 32, 64, 128)))
    vjl__bdtc = builder.load(builder.gep(qymhi__pjbd, [lir.Constant(lir.
        IntType(64), 0), yeui__ltt], inbounds=True))
    return builder.and_(krg__lhrry, vjl__bdtc)


def pyarray_check(builder, context, obj):
    ucju__kmrj = context.get_argument_type(types.pyobject)
    gocie__cbwn = lir.FunctionType(lir.IntType(32), [ucju__kmrj])
    zgkl__jhvb = cgutils.get_or_insert_function(builder.module, gocie__cbwn,
        name='is_np_array')
    return builder.call(zgkl__jhvb, [obj])


def pyarray_getitem(builder, context, arr_obj, ind):
    ucju__kmrj = context.get_argument_type(types.pyobject)
    tkxc__asuf = context.get_value_type(types.intp)
    ozza__dxrwf = lir.FunctionType(lir.IntType(8).as_pointer(), [ucju__kmrj,
        tkxc__asuf])
    kguw__gznif = cgutils.get_or_insert_function(builder.module,
        ozza__dxrwf, name='array_getptr1')
    nhd__qneh = lir.FunctionType(ucju__kmrj, [ucju__kmrj, lir.IntType(8).
        as_pointer()])
    cyog__hzue = cgutils.get_or_insert_function(builder.module, nhd__qneh,
        name='array_getitem')
    zjdp__izf = builder.call(kguw__gznif, [arr_obj, ind])
    return builder.call(cyog__hzue, [arr_obj, zjdp__izf])


def pyarray_setitem(builder, context, arr_obj, ind, val_obj):
    ucju__kmrj = context.get_argument_type(types.pyobject)
    tkxc__asuf = context.get_value_type(types.intp)
    ozza__dxrwf = lir.FunctionType(lir.IntType(8).as_pointer(), [ucju__kmrj,
        tkxc__asuf])
    kguw__gznif = cgutils.get_or_insert_function(builder.module,
        ozza__dxrwf, name='array_getptr1')
    bmto__fjd = lir.FunctionType(lir.VoidType(), [ucju__kmrj, lir.IntType(8
        ).as_pointer(), ucju__kmrj])
    htw__igve = cgutils.get_or_insert_function(builder.module, bmto__fjd,
        name='array_setitem')
    zjdp__izf = builder.call(kguw__gznif, [arr_obj, ind])
    builder.call(htw__igve, [arr_obj, zjdp__izf, val_obj])


def seq_getitem(builder, context, obj, ind):
    ucju__kmrj = context.get_argument_type(types.pyobject)
    tkxc__asuf = context.get_value_type(types.intp)
    rmzx__gblz = lir.FunctionType(ucju__kmrj, [ucju__kmrj, tkxc__asuf])
    axr__gcqsj = cgutils.get_or_insert_function(builder.module, rmzx__gblz,
        name='seq_getitem')
    return builder.call(axr__gcqsj, [obj, ind])


def is_na_value(builder, context, val, C_NA):
    ucju__kmrj = context.get_argument_type(types.pyobject)
    ughtj__cvdi = lir.FunctionType(lir.IntType(32), [ucju__kmrj, ucju__kmrj])
    lcq__htua = cgutils.get_or_insert_function(builder.module, ughtj__cvdi,
        name='is_na_value')
    return builder.call(lcq__htua, [val, C_NA])


def list_check(builder, context, obj):
    ucju__kmrj = context.get_argument_type(types.pyobject)
    dxr__rvlo = context.get_value_type(types.int32)
    ltl__wmri = lir.FunctionType(dxr__rvlo, [ucju__kmrj])
    zhqi__nrx = cgutils.get_or_insert_function(builder.module, ltl__wmri,
        name='list_check')
    return builder.call(zhqi__nrx, [obj])


def dict_keys(builder, context, obj):
    ucju__kmrj = context.get_argument_type(types.pyobject)
    ltl__wmri = lir.FunctionType(ucju__kmrj, [ucju__kmrj])
    zhqi__nrx = cgutils.get_or_insert_function(builder.module, ltl__wmri,
        name='dict_keys')
    return builder.call(zhqi__nrx, [obj])


def dict_values(builder, context, obj):
    ucju__kmrj = context.get_argument_type(types.pyobject)
    ltl__wmri = lir.FunctionType(ucju__kmrj, [ucju__kmrj])
    zhqi__nrx = cgutils.get_or_insert_function(builder.module, ltl__wmri,
        name='dict_values')
    return builder.call(zhqi__nrx, [obj])


def dict_merge_from_seq2(builder, context, dict_obj, seq2_obj):
    ucju__kmrj = context.get_argument_type(types.pyobject)
    ltl__wmri = lir.FunctionType(lir.VoidType(), [ucju__kmrj, ucju__kmrj])
    zhqi__nrx = cgutils.get_or_insert_function(builder.module, ltl__wmri,
        name='dict_merge_from_seq2')
    builder.call(zhqi__nrx, [dict_obj, seq2_obj])


def to_arr_obj_if_list_obj(c, context, builder, val, typ):
    if not (isinstance(typ, types.List) or bodo.utils.utils.is_array_typ(
        typ, False)):
        return val
    jffz__gktvf = cgutils.alloca_once_value(builder, val)
    hiehx__hldys = list_check(builder, context, val)
    hxu__ikj = builder.icmp_unsigned('!=', hiehx__hldys, lir.Constant(
        hiehx__hldys.type, 0))
    with builder.if_then(hxu__ikj):
        iep__wkjab = context.insert_const_string(builder.module, 'numpy')
        ehv__ciqqg = c.pyapi.import_module_noblock(iep__wkjab)
        cun__laiwk = 'object_'
        if isinstance(typ, types.Array) or isinstance(typ.dtype, types.Float):
            cun__laiwk = str(typ.dtype)
        rvbkd__kbgcp = c.pyapi.object_getattr_string(ehv__ciqqg, cun__laiwk)
        pqos__izx = builder.load(jffz__gktvf)
        celvz__xjhgu = c.pyapi.call_method(ehv__ciqqg, 'asarray', (
            pqos__izx, rvbkd__kbgcp))
        builder.store(celvz__xjhgu, jffz__gktvf)
        c.pyapi.decref(ehv__ciqqg)
        c.pyapi.decref(rvbkd__kbgcp)
    val = builder.load(jffz__gktvf)
    return val


def get_array_elem_counts(c, builder, context, arr_obj, typ):
    from bodo.libs.array_item_arr_ext import ArrayItemArrayType
    from bodo.libs.map_arr_ext import MapArrayType
    from bodo.libs.str_arr_ext import get_utf8_size, string_array_type
    from bodo.libs.struct_arr_ext import StructArrayType, StructType
    from bodo.libs.tuple_arr_ext import TupleArrayType
    if typ == bodo.string_type:
        twqu__mymvn = c.pyapi.to_native_value(bodo.string_type, arr_obj).value
        abjcm__aui, qzy__wjius = c.pyapi.call_jit_code(lambda a:
            get_utf8_size(a), types.int64(bodo.string_type), [twqu__mymvn])
        context.nrt.decref(builder, typ, twqu__mymvn)
        return cgutils.pack_array(builder, [qzy__wjius])
    if isinstance(typ, (StructType, types.BaseTuple)):
        iep__wkjab = context.insert_const_string(builder.module, 'pandas')
        bof__vqhd = c.pyapi.import_module_noblock(iep__wkjab)
        C_NA = c.pyapi.object_getattr_string(bof__vqhd, 'NA')
        mrgfq__trni = bodo.utils.transform.get_type_alloc_counts(typ)
        onrq__xmwv = context.make_tuple(builder, types.Tuple(mrgfq__trni *
            [types.int64]), mrgfq__trni * [context.get_constant(types.int64,
            0)])
        vpgay__geqj = cgutils.alloca_once_value(builder, onrq__xmwv)
        htp__dbr = 0
        gfpt__lioxu = typ.data if isinstance(typ, StructType) else typ.types
        for pnolu__yays, t in enumerate(gfpt__lioxu):
            gorrd__dvvli = bodo.utils.transform.get_type_alloc_counts(t)
            if gorrd__dvvli == 0:
                continue
            if isinstance(typ, StructType):
                val_obj = c.pyapi.dict_getitem_string(arr_obj, typ.names[
                    pnolu__yays])
            else:
                val_obj = c.pyapi.tuple_getitem(arr_obj, pnolu__yays)
            pxm__fujw = is_na_value(builder, context, val_obj, C_NA)
            xdlx__ksp = builder.icmp_unsigned('!=', pxm__fujw, lir.Constant
                (pxm__fujw.type, 1))
            with builder.if_then(xdlx__ksp):
                onrq__xmwv = builder.load(vpgay__geqj)
                slf__jnz = get_array_elem_counts(c, builder, context,
                    val_obj, t)
                for pnolu__yays in range(gorrd__dvvli):
                    esod__tnsw = builder.extract_value(onrq__xmwv, htp__dbr +
                        pnolu__yays)
                    knpkc__lertb = builder.extract_value(slf__jnz, pnolu__yays)
                    onrq__xmwv = builder.insert_value(onrq__xmwv, builder.
                        add(esod__tnsw, knpkc__lertb), htp__dbr + pnolu__yays)
                builder.store(onrq__xmwv, vpgay__geqj)
            htp__dbr += gorrd__dvvli
        c.pyapi.decref(bof__vqhd)
        c.pyapi.decref(C_NA)
        return builder.load(vpgay__geqj)
    if not bodo.utils.utils.is_array_typ(typ, False):
        return cgutils.pack_array(builder, [], lir.IntType(64))
    n = bodo.utils.utils.object_length(c, arr_obj)
    if not (isinstance(typ, (ArrayItemArrayType, StructArrayType,
        TupleArrayType, MapArrayType)) or typ == string_array_type):
        return cgutils.pack_array(builder, [n])
    iep__wkjab = context.insert_const_string(builder.module, 'pandas')
    bof__vqhd = c.pyapi.import_module_noblock(iep__wkjab)
    C_NA = c.pyapi.object_getattr_string(bof__vqhd, 'NA')
    mrgfq__trni = bodo.utils.transform.get_type_alloc_counts(typ)
    onrq__xmwv = context.make_tuple(builder, types.Tuple(mrgfq__trni * [
        types.int64]), [n] + (mrgfq__trni - 1) * [context.get_constant(
        types.int64, 0)])
    vpgay__geqj = cgutils.alloca_once_value(builder, onrq__xmwv)
    with cgutils.for_range(builder, n) as lde__tjwc:
        xmr__rdnd = lde__tjwc.index
        hhqjr__phwfl = seq_getitem(builder, context, arr_obj, xmr__rdnd)
        pxm__fujw = is_na_value(builder, context, hhqjr__phwfl, C_NA)
        xdlx__ksp = builder.icmp_unsigned('!=', pxm__fujw, lir.Constant(
            pxm__fujw.type, 1))
        with builder.if_then(xdlx__ksp):
            if isinstance(typ, ArrayItemArrayType) or typ == string_array_type:
                onrq__xmwv = builder.load(vpgay__geqj)
                slf__jnz = get_array_elem_counts(c, builder, context,
                    hhqjr__phwfl, typ.dtype)
                for pnolu__yays in range(mrgfq__trni - 1):
                    esod__tnsw = builder.extract_value(onrq__xmwv, 
                        pnolu__yays + 1)
                    knpkc__lertb = builder.extract_value(slf__jnz, pnolu__yays)
                    onrq__xmwv = builder.insert_value(onrq__xmwv, builder.
                        add(esod__tnsw, knpkc__lertb), pnolu__yays + 1)
                builder.store(onrq__xmwv, vpgay__geqj)
            elif isinstance(typ, (StructArrayType, TupleArrayType)):
                htp__dbr = 1
                for pnolu__yays, t in enumerate(typ.data):
                    gorrd__dvvli = bodo.utils.transform.get_type_alloc_counts(t
                        .dtype)
                    if gorrd__dvvli == 0:
                        continue
                    if isinstance(typ, TupleArrayType):
                        val_obj = c.pyapi.tuple_getitem(hhqjr__phwfl,
                            pnolu__yays)
                    else:
                        val_obj = c.pyapi.dict_getitem_string(hhqjr__phwfl,
                            typ.names[pnolu__yays])
                    pxm__fujw = is_na_value(builder, context, val_obj, C_NA)
                    xdlx__ksp = builder.icmp_unsigned('!=', pxm__fujw, lir.
                        Constant(pxm__fujw.type, 1))
                    with builder.if_then(xdlx__ksp):
                        onrq__xmwv = builder.load(vpgay__geqj)
                        slf__jnz = get_array_elem_counts(c, builder,
                            context, val_obj, t.dtype)
                        for pnolu__yays in range(gorrd__dvvli):
                            esod__tnsw = builder.extract_value(onrq__xmwv, 
                                htp__dbr + pnolu__yays)
                            knpkc__lertb = builder.extract_value(slf__jnz,
                                pnolu__yays)
                            onrq__xmwv = builder.insert_value(onrq__xmwv,
                                builder.add(esod__tnsw, knpkc__lertb), 
                                htp__dbr + pnolu__yays)
                        builder.store(onrq__xmwv, vpgay__geqj)
                    htp__dbr += gorrd__dvvli
            else:
                assert isinstance(typ, MapArrayType), typ
                onrq__xmwv = builder.load(vpgay__geqj)
                qisz__ija = dict_keys(builder, context, hhqjr__phwfl)
                cppr__wli = dict_values(builder, context, hhqjr__phwfl)
                gkh__wjj = get_array_elem_counts(c, builder, context,
                    qisz__ija, typ.key_arr_type)
                xuexq__sanii = bodo.utils.transform.get_type_alloc_counts(typ
                    .key_arr_type)
                for pnolu__yays in range(1, xuexq__sanii + 1):
                    esod__tnsw = builder.extract_value(onrq__xmwv, pnolu__yays)
                    knpkc__lertb = builder.extract_value(gkh__wjj, 
                        pnolu__yays - 1)
                    onrq__xmwv = builder.insert_value(onrq__xmwv, builder.
                        add(esod__tnsw, knpkc__lertb), pnolu__yays)
                hlx__myns = get_array_elem_counts(c, builder, context,
                    cppr__wli, typ.value_arr_type)
                for pnolu__yays in range(xuexq__sanii + 1, mrgfq__trni):
                    esod__tnsw = builder.extract_value(onrq__xmwv, pnolu__yays)
                    knpkc__lertb = builder.extract_value(hlx__myns, 
                        pnolu__yays - xuexq__sanii)
                    onrq__xmwv = builder.insert_value(onrq__xmwv, builder.
                        add(esod__tnsw, knpkc__lertb), pnolu__yays)
                builder.store(onrq__xmwv, vpgay__geqj)
                c.pyapi.decref(qisz__ija)
                c.pyapi.decref(cppr__wli)
        c.pyapi.decref(hhqjr__phwfl)
    c.pyapi.decref(bof__vqhd)
    c.pyapi.decref(C_NA)
    return builder.load(vpgay__geqj)


def gen_allocate_array(context, builder, arr_type, n_elems, c=None):
    qkp__xyvio = n_elems.type.count
    assert qkp__xyvio >= 1
    ybsnq__nhq = builder.extract_value(n_elems, 0)
    if qkp__xyvio != 1:
        qzekj__zkgml = cgutils.pack_array(builder, [builder.extract_value(
            n_elems, pnolu__yays) for pnolu__yays in range(1, qkp__xyvio)])
        cdg__ygzn = types.Tuple([types.int64] * (qkp__xyvio - 1))
    else:
        qzekj__zkgml = context.get_dummy_value()
        cdg__ygzn = types.none
    kzu__bgitm = types.TypeRef(arr_type)
    flo__nplfk = arr_type(types.int64, kzu__bgitm, cdg__ygzn)
    args = [ybsnq__nhq, context.get_dummy_value(), qzekj__zkgml]
    nqxym__cofx = lambda n, t, s: bodo.utils.utils.alloc_type(n, t, s)
    if c:
        abjcm__aui, oqlf__nom = c.pyapi.call_jit_code(nqxym__cofx,
            flo__nplfk, args)
    else:
        oqlf__nom = context.compile_internal(builder, nqxym__cofx,
            flo__nplfk, args)
    return oqlf__nom


def is_ll_eq(builder, val1, val2):
    pmkai__vfad = val1.type.pointee
    nkr__vmwh = val2.type.pointee
    assert pmkai__vfad == nkr__vmwh, 'invalid llvm value comparison'
    if isinstance(pmkai__vfad, (lir.BaseStructType, lir.ArrayType)):
        n_elems = len(pmkai__vfad.elements) if isinstance(pmkai__vfad, lir.
            BaseStructType) else pmkai__vfad.count
        zcf__evpv = lir.Constant(lir.IntType(1), 1)
        for pnolu__yays in range(n_elems):
            qfur__hod = lir.IntType(32)(0)
            duuim__bxzpc = lir.IntType(32)(pnolu__yays)
            lrk__cjg = builder.gep(val1, [qfur__hod, duuim__bxzpc],
                inbounds=True)
            aanj__dfjs = builder.gep(val2, [qfur__hod, duuim__bxzpc],
                inbounds=True)
            zcf__evpv = builder.and_(zcf__evpv, is_ll_eq(builder, lrk__cjg,
                aanj__dfjs))
        return zcf__evpv
    bupb__kdf = builder.load(val1)
    pslq__tkxur = builder.load(val2)
    if bupb__kdf.type in (lir.FloatType(), lir.DoubleType()):
        xbm__wzt = 32 if bupb__kdf.type == lir.FloatType() else 64
        bupb__kdf = builder.bitcast(bupb__kdf, lir.IntType(xbm__wzt))
        pslq__tkxur = builder.bitcast(pslq__tkxur, lir.IntType(xbm__wzt))
    return builder.icmp_unsigned('==', bupb__kdf, pslq__tkxur)
