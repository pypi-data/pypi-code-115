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
    kgfl__lqshh = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
    ucp__oigu = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
    letj__jwr = builder.gep(null_bitmap_ptr, [kgfl__lqshh], inbounds=True)
    jshgp__gnw = builder.load(letj__jwr)
    ohib__dpo = lir.ArrayType(lir.IntType(8), 8)
    vzd__pkiot = cgutils.alloca_once_value(builder, lir.Constant(ohib__dpo,
        (1, 2, 4, 8, 16, 32, 64, 128)))
    may__cey = builder.load(builder.gep(vzd__pkiot, [lir.Constant(lir.
        IntType(64), 0), ucp__oigu], inbounds=True))
    if val:
        builder.store(builder.or_(jshgp__gnw, may__cey), letj__jwr)
    else:
        may__cey = builder.xor(may__cey, lir.Constant(lir.IntType(8), -1))
        builder.store(builder.and_(jshgp__gnw, may__cey), letj__jwr)


def get_bitmap_bit(builder, null_bitmap_ptr, ind):
    kgfl__lqshh = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
    ucp__oigu = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
    jshgp__gnw = builder.load(builder.gep(null_bitmap_ptr, [kgfl__lqshh],
        inbounds=True))
    ohib__dpo = lir.ArrayType(lir.IntType(8), 8)
    vzd__pkiot = cgutils.alloca_once_value(builder, lir.Constant(ohib__dpo,
        (1, 2, 4, 8, 16, 32, 64, 128)))
    may__cey = builder.load(builder.gep(vzd__pkiot, [lir.Constant(lir.
        IntType(64), 0), ucp__oigu], inbounds=True))
    return builder.and_(jshgp__gnw, may__cey)


def pyarray_check(builder, context, obj):
    iivaf__rvjfb = context.get_argument_type(types.pyobject)
    dtx__fgtkc = lir.FunctionType(lir.IntType(32), [iivaf__rvjfb])
    gart__lwn = cgutils.get_or_insert_function(builder.module, dtx__fgtkc,
        name='is_np_array')
    return builder.call(gart__lwn, [obj])


def pyarray_getitem(builder, context, arr_obj, ind):
    iivaf__rvjfb = context.get_argument_type(types.pyobject)
    hsm__tuga = context.get_value_type(types.intp)
    qnsxe__ycxx = lir.FunctionType(lir.IntType(8).as_pointer(), [
        iivaf__rvjfb, hsm__tuga])
    qnyuk__dqm = cgutils.get_or_insert_function(builder.module, qnsxe__ycxx,
        name='array_getptr1')
    plul__vqkqh = lir.FunctionType(iivaf__rvjfb, [iivaf__rvjfb, lir.IntType
        (8).as_pointer()])
    ohst__maqo = cgutils.get_or_insert_function(builder.module, plul__vqkqh,
        name='array_getitem')
    dpoak__mer = builder.call(qnyuk__dqm, [arr_obj, ind])
    return builder.call(ohst__maqo, [arr_obj, dpoak__mer])


def pyarray_setitem(builder, context, arr_obj, ind, val_obj):
    iivaf__rvjfb = context.get_argument_type(types.pyobject)
    hsm__tuga = context.get_value_type(types.intp)
    qnsxe__ycxx = lir.FunctionType(lir.IntType(8).as_pointer(), [
        iivaf__rvjfb, hsm__tuga])
    qnyuk__dqm = cgutils.get_or_insert_function(builder.module, qnsxe__ycxx,
        name='array_getptr1')
    mlapn__qybyh = lir.FunctionType(lir.VoidType(), [iivaf__rvjfb, lir.
        IntType(8).as_pointer(), iivaf__rvjfb])
    pozw__hxa = cgutils.get_or_insert_function(builder.module, mlapn__qybyh,
        name='array_setitem')
    dpoak__mer = builder.call(qnyuk__dqm, [arr_obj, ind])
    builder.call(pozw__hxa, [arr_obj, dpoak__mer, val_obj])


def seq_getitem(builder, context, obj, ind):
    iivaf__rvjfb = context.get_argument_type(types.pyobject)
    hsm__tuga = context.get_value_type(types.intp)
    attf__iwuj = lir.FunctionType(iivaf__rvjfb, [iivaf__rvjfb, hsm__tuga])
    wrxik__xknmk = cgutils.get_or_insert_function(builder.module,
        attf__iwuj, name='seq_getitem')
    return builder.call(wrxik__xknmk, [obj, ind])


def is_na_value(builder, context, val, C_NA):
    iivaf__rvjfb = context.get_argument_type(types.pyobject)
    sms__xqrx = lir.FunctionType(lir.IntType(32), [iivaf__rvjfb, iivaf__rvjfb])
    lneb__xchm = cgutils.get_or_insert_function(builder.module, sms__xqrx,
        name='is_na_value')
    return builder.call(lneb__xchm, [val, C_NA])


def list_check(builder, context, obj):
    iivaf__rvjfb = context.get_argument_type(types.pyobject)
    evez__lrog = context.get_value_type(types.int32)
    cejhi__hfxfn = lir.FunctionType(evez__lrog, [iivaf__rvjfb])
    krue__oplav = cgutils.get_or_insert_function(builder.module,
        cejhi__hfxfn, name='list_check')
    return builder.call(krue__oplav, [obj])


def dict_keys(builder, context, obj):
    iivaf__rvjfb = context.get_argument_type(types.pyobject)
    cejhi__hfxfn = lir.FunctionType(iivaf__rvjfb, [iivaf__rvjfb])
    krue__oplav = cgutils.get_or_insert_function(builder.module,
        cejhi__hfxfn, name='dict_keys')
    return builder.call(krue__oplav, [obj])


def dict_values(builder, context, obj):
    iivaf__rvjfb = context.get_argument_type(types.pyobject)
    cejhi__hfxfn = lir.FunctionType(iivaf__rvjfb, [iivaf__rvjfb])
    krue__oplav = cgutils.get_or_insert_function(builder.module,
        cejhi__hfxfn, name='dict_values')
    return builder.call(krue__oplav, [obj])


def dict_merge_from_seq2(builder, context, dict_obj, seq2_obj):
    iivaf__rvjfb = context.get_argument_type(types.pyobject)
    cejhi__hfxfn = lir.FunctionType(lir.VoidType(), [iivaf__rvjfb,
        iivaf__rvjfb])
    krue__oplav = cgutils.get_or_insert_function(builder.module,
        cejhi__hfxfn, name='dict_merge_from_seq2')
    builder.call(krue__oplav, [dict_obj, seq2_obj])


def to_arr_obj_if_list_obj(c, context, builder, val, typ):
    if not (isinstance(typ, types.List) or bodo.utils.utils.is_array_typ(
        typ, False)):
        return val
    lff__hzh = cgutils.alloca_once_value(builder, val)
    brlw__dadid = list_check(builder, context, val)
    gjcce__wxiv = builder.icmp_unsigned('!=', brlw__dadid, lir.Constant(
        brlw__dadid.type, 0))
    with builder.if_then(gjcce__wxiv):
        uprwc__qusot = context.insert_const_string(builder.module, 'numpy')
        uqamf__mql = c.pyapi.import_module_noblock(uprwc__qusot)
        buoml__feh = 'object_'
        if isinstance(typ, types.Array) or isinstance(typ.dtype, types.Float):
            buoml__feh = str(typ.dtype)
        fgubh__fuenx = c.pyapi.object_getattr_string(uqamf__mql, buoml__feh)
        xrib__ngzy = builder.load(lff__hzh)
        yizm__cozvb = c.pyapi.call_method(uqamf__mql, 'asarray', (
            xrib__ngzy, fgubh__fuenx))
        builder.store(yizm__cozvb, lff__hzh)
        c.pyapi.decref(uqamf__mql)
        c.pyapi.decref(fgubh__fuenx)
    val = builder.load(lff__hzh)
    return val


def get_array_elem_counts(c, builder, context, arr_obj, typ):
    from bodo.libs.array_item_arr_ext import ArrayItemArrayType
    from bodo.libs.map_arr_ext import MapArrayType
    from bodo.libs.str_arr_ext import get_utf8_size, string_array_type
    from bodo.libs.struct_arr_ext import StructArrayType, StructType
    from bodo.libs.tuple_arr_ext import TupleArrayType
    if typ == bodo.string_type:
        rpr__iskqn = c.pyapi.to_native_value(bodo.string_type, arr_obj).value
        yurto__wgfqt, fteut__cucn = c.pyapi.call_jit_code(lambda a:
            get_utf8_size(a), types.int64(bodo.string_type), [rpr__iskqn])
        context.nrt.decref(builder, typ, rpr__iskqn)
        return cgutils.pack_array(builder, [fteut__cucn])
    if isinstance(typ, (StructType, types.BaseTuple)):
        uprwc__qusot = context.insert_const_string(builder.module, 'pandas')
        phs__iuru = c.pyapi.import_module_noblock(uprwc__qusot)
        C_NA = c.pyapi.object_getattr_string(phs__iuru, 'NA')
        tfsce__hwjob = bodo.utils.transform.get_type_alloc_counts(typ)
        dhf__ouryp = context.make_tuple(builder, types.Tuple(tfsce__hwjob *
            [types.int64]), tfsce__hwjob * [context.get_constant(types.
            int64, 0)])
        zvzvd__xphna = cgutils.alloca_once_value(builder, dhf__ouryp)
        dva__dxs = 0
        rvs__mzm = typ.data if isinstance(typ, StructType) else typ.types
        for aeuk__puakv, t in enumerate(rvs__mzm):
            vmyy__lyd = bodo.utils.transform.get_type_alloc_counts(t)
            if vmyy__lyd == 0:
                continue
            if isinstance(typ, StructType):
                val_obj = c.pyapi.dict_getitem_string(arr_obj, typ.names[
                    aeuk__puakv])
            else:
                val_obj = c.pyapi.tuple_getitem(arr_obj, aeuk__puakv)
            zbr__auq = is_na_value(builder, context, val_obj, C_NA)
            jeyy__zjdoc = builder.icmp_unsigned('!=', zbr__auq, lir.
                Constant(zbr__auq.type, 1))
            with builder.if_then(jeyy__zjdoc):
                dhf__ouryp = builder.load(zvzvd__xphna)
                gsp__bvy = get_array_elem_counts(c, builder, context,
                    val_obj, t)
                for aeuk__puakv in range(vmyy__lyd):
                    yzvo__qcjqv = builder.extract_value(dhf__ouryp, 
                        dva__dxs + aeuk__puakv)
                    iqa__jbhs = builder.extract_value(gsp__bvy, aeuk__puakv)
                    dhf__ouryp = builder.insert_value(dhf__ouryp, builder.
                        add(yzvo__qcjqv, iqa__jbhs), dva__dxs + aeuk__puakv)
                builder.store(dhf__ouryp, zvzvd__xphna)
            dva__dxs += vmyy__lyd
        c.pyapi.decref(phs__iuru)
        c.pyapi.decref(C_NA)
        return builder.load(zvzvd__xphna)
    if not bodo.utils.utils.is_array_typ(typ, False):
        return cgutils.pack_array(builder, [], lir.IntType(64))
    n = bodo.utils.utils.object_length(c, arr_obj)
    if not (isinstance(typ, (ArrayItemArrayType, StructArrayType,
        TupleArrayType, MapArrayType)) or typ == string_array_type):
        return cgutils.pack_array(builder, [n])
    uprwc__qusot = context.insert_const_string(builder.module, 'pandas')
    phs__iuru = c.pyapi.import_module_noblock(uprwc__qusot)
    C_NA = c.pyapi.object_getattr_string(phs__iuru, 'NA')
    tfsce__hwjob = bodo.utils.transform.get_type_alloc_counts(typ)
    dhf__ouryp = context.make_tuple(builder, types.Tuple(tfsce__hwjob * [
        types.int64]), [n] + (tfsce__hwjob - 1) * [context.get_constant(
        types.int64, 0)])
    zvzvd__xphna = cgutils.alloca_once_value(builder, dhf__ouryp)
    with cgutils.for_range(builder, n) as dlk__utgd:
        kqwgl__diuo = dlk__utgd.index
        umo__hui = seq_getitem(builder, context, arr_obj, kqwgl__diuo)
        zbr__auq = is_na_value(builder, context, umo__hui, C_NA)
        jeyy__zjdoc = builder.icmp_unsigned('!=', zbr__auq, lir.Constant(
            zbr__auq.type, 1))
        with builder.if_then(jeyy__zjdoc):
            if isinstance(typ, ArrayItemArrayType) or typ == string_array_type:
                dhf__ouryp = builder.load(zvzvd__xphna)
                gsp__bvy = get_array_elem_counts(c, builder, context,
                    umo__hui, typ.dtype)
                for aeuk__puakv in range(tfsce__hwjob - 1):
                    yzvo__qcjqv = builder.extract_value(dhf__ouryp, 
                        aeuk__puakv + 1)
                    iqa__jbhs = builder.extract_value(gsp__bvy, aeuk__puakv)
                    dhf__ouryp = builder.insert_value(dhf__ouryp, builder.
                        add(yzvo__qcjqv, iqa__jbhs), aeuk__puakv + 1)
                builder.store(dhf__ouryp, zvzvd__xphna)
            elif isinstance(typ, (StructArrayType, TupleArrayType)):
                dva__dxs = 1
                for aeuk__puakv, t in enumerate(typ.data):
                    vmyy__lyd = bodo.utils.transform.get_type_alloc_counts(t
                        .dtype)
                    if vmyy__lyd == 0:
                        continue
                    if isinstance(typ, TupleArrayType):
                        val_obj = c.pyapi.tuple_getitem(umo__hui, aeuk__puakv)
                    else:
                        val_obj = c.pyapi.dict_getitem_string(umo__hui, typ
                            .names[aeuk__puakv])
                    zbr__auq = is_na_value(builder, context, val_obj, C_NA)
                    jeyy__zjdoc = builder.icmp_unsigned('!=', zbr__auq, lir
                        .Constant(zbr__auq.type, 1))
                    with builder.if_then(jeyy__zjdoc):
                        dhf__ouryp = builder.load(zvzvd__xphna)
                        gsp__bvy = get_array_elem_counts(c, builder,
                            context, val_obj, t.dtype)
                        for aeuk__puakv in range(vmyy__lyd):
                            yzvo__qcjqv = builder.extract_value(dhf__ouryp,
                                dva__dxs + aeuk__puakv)
                            iqa__jbhs = builder.extract_value(gsp__bvy,
                                aeuk__puakv)
                            dhf__ouryp = builder.insert_value(dhf__ouryp,
                                builder.add(yzvo__qcjqv, iqa__jbhs), 
                                dva__dxs + aeuk__puakv)
                        builder.store(dhf__ouryp, zvzvd__xphna)
                    dva__dxs += vmyy__lyd
            else:
                assert isinstance(typ, MapArrayType), typ
                dhf__ouryp = builder.load(zvzvd__xphna)
                noo__jjem = dict_keys(builder, context, umo__hui)
                irhu__ind = dict_values(builder, context, umo__hui)
                tco__van = get_array_elem_counts(c, builder, context,
                    noo__jjem, typ.key_arr_type)
                pzz__rsni = bodo.utils.transform.get_type_alloc_counts(typ.
                    key_arr_type)
                for aeuk__puakv in range(1, pzz__rsni + 1):
                    yzvo__qcjqv = builder.extract_value(dhf__ouryp, aeuk__puakv
                        )
                    iqa__jbhs = builder.extract_value(tco__van, aeuk__puakv - 1
                        )
                    dhf__ouryp = builder.insert_value(dhf__ouryp, builder.
                        add(yzvo__qcjqv, iqa__jbhs), aeuk__puakv)
                vlg__qqeo = get_array_elem_counts(c, builder, context,
                    irhu__ind, typ.value_arr_type)
                for aeuk__puakv in range(pzz__rsni + 1, tfsce__hwjob):
                    yzvo__qcjqv = builder.extract_value(dhf__ouryp, aeuk__puakv
                        )
                    iqa__jbhs = builder.extract_value(vlg__qqeo, 
                        aeuk__puakv - pzz__rsni)
                    dhf__ouryp = builder.insert_value(dhf__ouryp, builder.
                        add(yzvo__qcjqv, iqa__jbhs), aeuk__puakv)
                builder.store(dhf__ouryp, zvzvd__xphna)
                c.pyapi.decref(noo__jjem)
                c.pyapi.decref(irhu__ind)
        c.pyapi.decref(umo__hui)
    c.pyapi.decref(phs__iuru)
    c.pyapi.decref(C_NA)
    return builder.load(zvzvd__xphna)


def gen_allocate_array(context, builder, arr_type, n_elems, c=None):
    scla__cgn = n_elems.type.count
    assert scla__cgn >= 1
    yookz__pffd = builder.extract_value(n_elems, 0)
    if scla__cgn != 1:
        nbxge__xro = cgutils.pack_array(builder, [builder.extract_value(
            n_elems, aeuk__puakv) for aeuk__puakv in range(1, scla__cgn)])
        eghm__lfd = types.Tuple([types.int64] * (scla__cgn - 1))
    else:
        nbxge__xro = context.get_dummy_value()
        eghm__lfd = types.none
    mtz__jker = types.TypeRef(arr_type)
    zlb__xey = arr_type(types.int64, mtz__jker, eghm__lfd)
    args = [yookz__pffd, context.get_dummy_value(), nbxge__xro]
    kffkj__nuh = lambda n, t, s: bodo.utils.utils.alloc_type(n, t, s)
    if c:
        yurto__wgfqt, wtc__cgkx = c.pyapi.call_jit_code(kffkj__nuh,
            zlb__xey, args)
    else:
        wtc__cgkx = context.compile_internal(builder, kffkj__nuh, zlb__xey,
            args)
    return wtc__cgkx


def is_ll_eq(builder, val1, val2):
    fsph__zgy = val1.type.pointee
    els__pit = val2.type.pointee
    assert fsph__zgy == els__pit, 'invalid llvm value comparison'
    if isinstance(fsph__zgy, (lir.BaseStructType, lir.ArrayType)):
        n_elems = len(fsph__zgy.elements) if isinstance(fsph__zgy, lir.
            BaseStructType) else fsph__zgy.count
        qzh__iuz = lir.Constant(lir.IntType(1), 1)
        for aeuk__puakv in range(n_elems):
            jnh__pybje = lir.IntType(32)(0)
            jwi__pja = lir.IntType(32)(aeuk__puakv)
            iql__rwi = builder.gep(val1, [jnh__pybje, jwi__pja], inbounds=True)
            cuuq__iefq = builder.gep(val2, [jnh__pybje, jwi__pja], inbounds
                =True)
            qzh__iuz = builder.and_(qzh__iuz, is_ll_eq(builder, iql__rwi,
                cuuq__iefq))
        return qzh__iuz
    zqmmp__lqk = builder.load(val1)
    bhpmq__xyk = builder.load(val2)
    if zqmmp__lqk.type in (lir.FloatType(), lir.DoubleType()):
        pugin__vvsut = 32 if zqmmp__lqk.type == lir.FloatType() else 64
        zqmmp__lqk = builder.bitcast(zqmmp__lqk, lir.IntType(pugin__vvsut))
        bhpmq__xyk = builder.bitcast(bhpmq__xyk, lir.IntType(pugin__vvsut))
    return builder.icmp_unsigned('==', zqmmp__lqk, bhpmq__xyk)
