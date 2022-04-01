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
    ekx__eqjje = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
    uuoqy__vtbj = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
    rtcq__lwtmj = builder.gep(null_bitmap_ptr, [ekx__eqjje], inbounds=True)
    tkn__mgspd = builder.load(rtcq__lwtmj)
    lhb__tmdc = lir.ArrayType(lir.IntType(8), 8)
    jmg__wypj = cgutils.alloca_once_value(builder, lir.Constant(lhb__tmdc,
        (1, 2, 4, 8, 16, 32, 64, 128)))
    mhks__nut = builder.load(builder.gep(jmg__wypj, [lir.Constant(lir.
        IntType(64), 0), uuoqy__vtbj], inbounds=True))
    if val:
        builder.store(builder.or_(tkn__mgspd, mhks__nut), rtcq__lwtmj)
    else:
        mhks__nut = builder.xor(mhks__nut, lir.Constant(lir.IntType(8), -1))
        builder.store(builder.and_(tkn__mgspd, mhks__nut), rtcq__lwtmj)


def get_bitmap_bit(builder, null_bitmap_ptr, ind):
    ekx__eqjje = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
    uuoqy__vtbj = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
    tkn__mgspd = builder.load(builder.gep(null_bitmap_ptr, [ekx__eqjje],
        inbounds=True))
    lhb__tmdc = lir.ArrayType(lir.IntType(8), 8)
    jmg__wypj = cgutils.alloca_once_value(builder, lir.Constant(lhb__tmdc,
        (1, 2, 4, 8, 16, 32, 64, 128)))
    mhks__nut = builder.load(builder.gep(jmg__wypj, [lir.Constant(lir.
        IntType(64), 0), uuoqy__vtbj], inbounds=True))
    return builder.and_(tkn__mgspd, mhks__nut)


def pyarray_check(builder, context, obj):
    kwlv__krtx = context.get_argument_type(types.pyobject)
    nzhq__fijq = lir.FunctionType(lir.IntType(32), [kwlv__krtx])
    iui__arsb = cgutils.get_or_insert_function(builder.module, nzhq__fijq,
        name='is_np_array')
    return builder.call(iui__arsb, [obj])


def pyarray_getitem(builder, context, arr_obj, ind):
    kwlv__krtx = context.get_argument_type(types.pyobject)
    xwmuk__cmw = context.get_value_type(types.intp)
    ifvug__igvge = lir.FunctionType(lir.IntType(8).as_pointer(), [
        kwlv__krtx, xwmuk__cmw])
    asbpm__hoxtf = cgutils.get_or_insert_function(builder.module,
        ifvug__igvge, name='array_getptr1')
    tqk__wrf = lir.FunctionType(kwlv__krtx, [kwlv__krtx, lir.IntType(8).
        as_pointer()])
    nxdi__kzc = cgutils.get_or_insert_function(builder.module, tqk__wrf,
        name='array_getitem')
    ouvl__efm = builder.call(asbpm__hoxtf, [arr_obj, ind])
    return builder.call(nxdi__kzc, [arr_obj, ouvl__efm])


def pyarray_setitem(builder, context, arr_obj, ind, val_obj):
    kwlv__krtx = context.get_argument_type(types.pyobject)
    xwmuk__cmw = context.get_value_type(types.intp)
    ifvug__igvge = lir.FunctionType(lir.IntType(8).as_pointer(), [
        kwlv__krtx, xwmuk__cmw])
    asbpm__hoxtf = cgutils.get_or_insert_function(builder.module,
        ifvug__igvge, name='array_getptr1')
    gezrq__zesb = lir.FunctionType(lir.VoidType(), [kwlv__krtx, lir.IntType
        (8).as_pointer(), kwlv__krtx])
    pst__kaq = cgutils.get_or_insert_function(builder.module, gezrq__zesb,
        name='array_setitem')
    ouvl__efm = builder.call(asbpm__hoxtf, [arr_obj, ind])
    builder.call(pst__kaq, [arr_obj, ouvl__efm, val_obj])


def seq_getitem(builder, context, obj, ind):
    kwlv__krtx = context.get_argument_type(types.pyobject)
    xwmuk__cmw = context.get_value_type(types.intp)
    ali__qlww = lir.FunctionType(kwlv__krtx, [kwlv__krtx, xwmuk__cmw])
    tdtql__nmia = cgutils.get_or_insert_function(builder.module, ali__qlww,
        name='seq_getitem')
    return builder.call(tdtql__nmia, [obj, ind])


def is_na_value(builder, context, val, C_NA):
    kwlv__krtx = context.get_argument_type(types.pyobject)
    sqp__pyfzz = lir.FunctionType(lir.IntType(32), [kwlv__krtx, kwlv__krtx])
    qrbq__zapuy = cgutils.get_or_insert_function(builder.module, sqp__pyfzz,
        name='is_na_value')
    return builder.call(qrbq__zapuy, [val, C_NA])


def list_check(builder, context, obj):
    kwlv__krtx = context.get_argument_type(types.pyobject)
    gxysq__uzj = context.get_value_type(types.int32)
    cicei__otujk = lir.FunctionType(gxysq__uzj, [kwlv__krtx])
    kfmc__ovqw = cgutils.get_or_insert_function(builder.module,
        cicei__otujk, name='list_check')
    return builder.call(kfmc__ovqw, [obj])


def dict_keys(builder, context, obj):
    kwlv__krtx = context.get_argument_type(types.pyobject)
    cicei__otujk = lir.FunctionType(kwlv__krtx, [kwlv__krtx])
    kfmc__ovqw = cgutils.get_or_insert_function(builder.module,
        cicei__otujk, name='dict_keys')
    return builder.call(kfmc__ovqw, [obj])


def dict_values(builder, context, obj):
    kwlv__krtx = context.get_argument_type(types.pyobject)
    cicei__otujk = lir.FunctionType(kwlv__krtx, [kwlv__krtx])
    kfmc__ovqw = cgutils.get_or_insert_function(builder.module,
        cicei__otujk, name='dict_values')
    return builder.call(kfmc__ovqw, [obj])


def dict_merge_from_seq2(builder, context, dict_obj, seq2_obj):
    kwlv__krtx = context.get_argument_type(types.pyobject)
    cicei__otujk = lir.FunctionType(lir.VoidType(), [kwlv__krtx, kwlv__krtx])
    kfmc__ovqw = cgutils.get_or_insert_function(builder.module,
        cicei__otujk, name='dict_merge_from_seq2')
    builder.call(kfmc__ovqw, [dict_obj, seq2_obj])


def to_arr_obj_if_list_obj(c, context, builder, val, typ):
    if not (isinstance(typ, types.List) or bodo.utils.utils.is_array_typ(
        typ, False)):
        return val
    zyjx__klme = cgutils.alloca_once_value(builder, val)
    htyhn__kvzrp = list_check(builder, context, val)
    hir__fwxnk = builder.icmp_unsigned('!=', htyhn__kvzrp, lir.Constant(
        htyhn__kvzrp.type, 0))
    with builder.if_then(hir__fwxnk):
        wtx__rbgo = context.insert_const_string(builder.module, 'numpy')
        oxchw__ywch = c.pyapi.import_module_noblock(wtx__rbgo)
        evqq__qomax = 'object_'
        if isinstance(typ, types.Array) or isinstance(typ.dtype, types.Float):
            evqq__qomax = str(typ.dtype)
        umh__wfs = c.pyapi.object_getattr_string(oxchw__ywch, evqq__qomax)
        ymo__ldqib = builder.load(zyjx__klme)
        ijhb__jhq = c.pyapi.call_method(oxchw__ywch, 'asarray', (ymo__ldqib,
            umh__wfs))
        builder.store(ijhb__jhq, zyjx__klme)
        c.pyapi.decref(oxchw__ywch)
        c.pyapi.decref(umh__wfs)
    val = builder.load(zyjx__klme)
    return val


def get_array_elem_counts(c, builder, context, arr_obj, typ):
    from bodo.libs.array_item_arr_ext import ArrayItemArrayType
    from bodo.libs.map_arr_ext import MapArrayType
    from bodo.libs.str_arr_ext import get_utf8_size, string_array_type
    from bodo.libs.struct_arr_ext import StructArrayType, StructType
    from bodo.libs.tuple_arr_ext import TupleArrayType
    if typ == bodo.string_type:
        oymga__nvesk = c.pyapi.to_native_value(bodo.string_type, arr_obj).value
        bhwzj__fei, vabsf__kec = c.pyapi.call_jit_code(lambda a:
            get_utf8_size(a), types.int64(bodo.string_type), [oymga__nvesk])
        context.nrt.decref(builder, typ, oymga__nvesk)
        return cgutils.pack_array(builder, [vabsf__kec])
    if isinstance(typ, (StructType, types.BaseTuple)):
        wtx__rbgo = context.insert_const_string(builder.module, 'pandas')
        ooh__zjdo = c.pyapi.import_module_noblock(wtx__rbgo)
        C_NA = c.pyapi.object_getattr_string(ooh__zjdo, 'NA')
        yka__sxq = bodo.utils.transform.get_type_alloc_counts(typ)
        juqxg__umua = context.make_tuple(builder, types.Tuple(yka__sxq * [
            types.int64]), yka__sxq * [context.get_constant(types.int64, 0)])
        yzibm__rtxun = cgutils.alloca_once_value(builder, juqxg__umua)
        pqoj__ufw = 0
        nvtup__yqp = typ.data if isinstance(typ, StructType) else typ.types
        for leir__qyji, t in enumerate(nvtup__yqp):
            qnfal__syyh = bodo.utils.transform.get_type_alloc_counts(t)
            if qnfal__syyh == 0:
                continue
            if isinstance(typ, StructType):
                val_obj = c.pyapi.dict_getitem_string(arr_obj, typ.names[
                    leir__qyji])
            else:
                val_obj = c.pyapi.tuple_getitem(arr_obj, leir__qyji)
            chn__pkh = is_na_value(builder, context, val_obj, C_NA)
            psgck__pmk = builder.icmp_unsigned('!=', chn__pkh, lir.Constant
                (chn__pkh.type, 1))
            with builder.if_then(psgck__pmk):
                juqxg__umua = builder.load(yzibm__rtxun)
                uir__sptjq = get_array_elem_counts(c, builder, context,
                    val_obj, t)
                for leir__qyji in range(qnfal__syyh):
                    hsqul__tkb = builder.extract_value(juqxg__umua, 
                        pqoj__ufw + leir__qyji)
                    sibdz__qgm = builder.extract_value(uir__sptjq, leir__qyji)
                    juqxg__umua = builder.insert_value(juqxg__umua, builder
                        .add(hsqul__tkb, sibdz__qgm), pqoj__ufw + leir__qyji)
                builder.store(juqxg__umua, yzibm__rtxun)
            pqoj__ufw += qnfal__syyh
        c.pyapi.decref(ooh__zjdo)
        c.pyapi.decref(C_NA)
        return builder.load(yzibm__rtxun)
    if not bodo.utils.utils.is_array_typ(typ, False):
        return cgutils.pack_array(builder, [], lir.IntType(64))
    n = bodo.utils.utils.object_length(c, arr_obj)
    if not (isinstance(typ, (ArrayItemArrayType, StructArrayType,
        TupleArrayType, MapArrayType)) or typ == string_array_type):
        return cgutils.pack_array(builder, [n])
    wtx__rbgo = context.insert_const_string(builder.module, 'pandas')
    ooh__zjdo = c.pyapi.import_module_noblock(wtx__rbgo)
    C_NA = c.pyapi.object_getattr_string(ooh__zjdo, 'NA')
    yka__sxq = bodo.utils.transform.get_type_alloc_counts(typ)
    juqxg__umua = context.make_tuple(builder, types.Tuple(yka__sxq * [types
        .int64]), [n] + (yka__sxq - 1) * [context.get_constant(types.int64, 0)]
        )
    yzibm__rtxun = cgutils.alloca_once_value(builder, juqxg__umua)
    with cgutils.for_range(builder, n) as cnrjo__ohig:
        ihr__xjtx = cnrjo__ohig.index
        prij__jzppd = seq_getitem(builder, context, arr_obj, ihr__xjtx)
        chn__pkh = is_na_value(builder, context, prij__jzppd, C_NA)
        psgck__pmk = builder.icmp_unsigned('!=', chn__pkh, lir.Constant(
            chn__pkh.type, 1))
        with builder.if_then(psgck__pmk):
            if isinstance(typ, ArrayItemArrayType) or typ == string_array_type:
                juqxg__umua = builder.load(yzibm__rtxun)
                uir__sptjq = get_array_elem_counts(c, builder, context,
                    prij__jzppd, typ.dtype)
                for leir__qyji in range(yka__sxq - 1):
                    hsqul__tkb = builder.extract_value(juqxg__umua, 
                        leir__qyji + 1)
                    sibdz__qgm = builder.extract_value(uir__sptjq, leir__qyji)
                    juqxg__umua = builder.insert_value(juqxg__umua, builder
                        .add(hsqul__tkb, sibdz__qgm), leir__qyji + 1)
                builder.store(juqxg__umua, yzibm__rtxun)
            elif isinstance(typ, (StructArrayType, TupleArrayType)):
                pqoj__ufw = 1
                for leir__qyji, t in enumerate(typ.data):
                    qnfal__syyh = bodo.utils.transform.get_type_alloc_counts(t
                        .dtype)
                    if qnfal__syyh == 0:
                        continue
                    if isinstance(typ, TupleArrayType):
                        val_obj = c.pyapi.tuple_getitem(prij__jzppd, leir__qyji
                            )
                    else:
                        val_obj = c.pyapi.dict_getitem_string(prij__jzppd,
                            typ.names[leir__qyji])
                    chn__pkh = is_na_value(builder, context, val_obj, C_NA)
                    psgck__pmk = builder.icmp_unsigned('!=', chn__pkh, lir.
                        Constant(chn__pkh.type, 1))
                    with builder.if_then(psgck__pmk):
                        juqxg__umua = builder.load(yzibm__rtxun)
                        uir__sptjq = get_array_elem_counts(c, builder,
                            context, val_obj, t.dtype)
                        for leir__qyji in range(qnfal__syyh):
                            hsqul__tkb = builder.extract_value(juqxg__umua,
                                pqoj__ufw + leir__qyji)
                            sibdz__qgm = builder.extract_value(uir__sptjq,
                                leir__qyji)
                            juqxg__umua = builder.insert_value(juqxg__umua,
                                builder.add(hsqul__tkb, sibdz__qgm), 
                                pqoj__ufw + leir__qyji)
                        builder.store(juqxg__umua, yzibm__rtxun)
                    pqoj__ufw += qnfal__syyh
            else:
                assert isinstance(typ, MapArrayType), typ
                juqxg__umua = builder.load(yzibm__rtxun)
                tqu__ujrfn = dict_keys(builder, context, prij__jzppd)
                mewid__dsamk = dict_values(builder, context, prij__jzppd)
                quax__simj = get_array_elem_counts(c, builder, context,
                    tqu__ujrfn, typ.key_arr_type)
                vhcg__aofi = bodo.utils.transform.get_type_alloc_counts(typ
                    .key_arr_type)
                for leir__qyji in range(1, vhcg__aofi + 1):
                    hsqul__tkb = builder.extract_value(juqxg__umua, leir__qyji)
                    sibdz__qgm = builder.extract_value(quax__simj, 
                        leir__qyji - 1)
                    juqxg__umua = builder.insert_value(juqxg__umua, builder
                        .add(hsqul__tkb, sibdz__qgm), leir__qyji)
                nwj__hlkdh = get_array_elem_counts(c, builder, context,
                    mewid__dsamk, typ.value_arr_type)
                for leir__qyji in range(vhcg__aofi + 1, yka__sxq):
                    hsqul__tkb = builder.extract_value(juqxg__umua, leir__qyji)
                    sibdz__qgm = builder.extract_value(nwj__hlkdh, 
                        leir__qyji - vhcg__aofi)
                    juqxg__umua = builder.insert_value(juqxg__umua, builder
                        .add(hsqul__tkb, sibdz__qgm), leir__qyji)
                builder.store(juqxg__umua, yzibm__rtxun)
                c.pyapi.decref(tqu__ujrfn)
                c.pyapi.decref(mewid__dsamk)
        c.pyapi.decref(prij__jzppd)
    c.pyapi.decref(ooh__zjdo)
    c.pyapi.decref(C_NA)
    return builder.load(yzibm__rtxun)


def gen_allocate_array(context, builder, arr_type, n_elems, c=None):
    hkpmu__kkvm = n_elems.type.count
    assert hkpmu__kkvm >= 1
    gug__lgnmz = builder.extract_value(n_elems, 0)
    if hkpmu__kkvm != 1:
        ztw__pau = cgutils.pack_array(builder, [builder.extract_value(
            n_elems, leir__qyji) for leir__qyji in range(1, hkpmu__kkvm)])
        xcxx__hma = types.Tuple([types.int64] * (hkpmu__kkvm - 1))
    else:
        ztw__pau = context.get_dummy_value()
        xcxx__hma = types.none
    rin__dpv = types.TypeRef(arr_type)
    sng__najao = arr_type(types.int64, rin__dpv, xcxx__hma)
    args = [gug__lgnmz, context.get_dummy_value(), ztw__pau]
    rbjr__eaw = lambda n, t, s: bodo.utils.utils.alloc_type(n, t, s)
    if c:
        bhwzj__fei, vcho__kmn = c.pyapi.call_jit_code(rbjr__eaw, sng__najao,
            args)
    else:
        vcho__kmn = context.compile_internal(builder, rbjr__eaw, sng__najao,
            args)
    return vcho__kmn


def is_ll_eq(builder, val1, val2):
    npu__asupm = val1.type.pointee
    bsrhe__bnt = val2.type.pointee
    assert npu__asupm == bsrhe__bnt, 'invalid llvm value comparison'
    if isinstance(npu__asupm, (lir.BaseStructType, lir.ArrayType)):
        n_elems = len(npu__asupm.elements) if isinstance(npu__asupm, lir.
            BaseStructType) else npu__asupm.count
        rbimu__liys = lir.Constant(lir.IntType(1), 1)
        for leir__qyji in range(n_elems):
            nqpb__bukwg = lir.IntType(32)(0)
            foegw__mnizg = lir.IntType(32)(leir__qyji)
            symqu__jyh = builder.gep(val1, [nqpb__bukwg, foegw__mnizg],
                inbounds=True)
            lfwxo__wob = builder.gep(val2, [nqpb__bukwg, foegw__mnizg],
                inbounds=True)
            rbimu__liys = builder.and_(rbimu__liys, is_ll_eq(builder,
                symqu__jyh, lfwxo__wob))
        return rbimu__liys
    mzklc__btj = builder.load(val1)
    zlqkt__scyrj = builder.load(val2)
    if mzklc__btj.type in (lir.FloatType(), lir.DoubleType()):
        xtsq__ick = 32 if mzklc__btj.type == lir.FloatType() else 64
        mzklc__btj = builder.bitcast(mzklc__btj, lir.IntType(xtsq__ick))
        zlqkt__scyrj = builder.bitcast(zlqkt__scyrj, lir.IntType(xtsq__ick))
    return builder.icmp_unsigned('==', mzklc__btj, zlqkt__scyrj)
