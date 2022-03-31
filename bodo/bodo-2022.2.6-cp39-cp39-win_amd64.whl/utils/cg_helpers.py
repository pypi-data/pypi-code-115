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
    hzo__fhp = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
    zkomu__hsyqj = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
    sia__shj = builder.gep(null_bitmap_ptr, [hzo__fhp], inbounds=True)
    rlkk__hdan = builder.load(sia__shj)
    qlqt__kldo = lir.ArrayType(lir.IntType(8), 8)
    tjg__mom = cgutils.alloca_once_value(builder, lir.Constant(qlqt__kldo,
        (1, 2, 4, 8, 16, 32, 64, 128)))
    ead__udab = builder.load(builder.gep(tjg__mom, [lir.Constant(lir.
        IntType(64), 0), zkomu__hsyqj], inbounds=True))
    if val:
        builder.store(builder.or_(rlkk__hdan, ead__udab), sia__shj)
    else:
        ead__udab = builder.xor(ead__udab, lir.Constant(lir.IntType(8), -1))
        builder.store(builder.and_(rlkk__hdan, ead__udab), sia__shj)


def get_bitmap_bit(builder, null_bitmap_ptr, ind):
    hzo__fhp = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
    zkomu__hsyqj = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
    rlkk__hdan = builder.load(builder.gep(null_bitmap_ptr, [hzo__fhp],
        inbounds=True))
    qlqt__kldo = lir.ArrayType(lir.IntType(8), 8)
    tjg__mom = cgutils.alloca_once_value(builder, lir.Constant(qlqt__kldo,
        (1, 2, 4, 8, 16, 32, 64, 128)))
    ead__udab = builder.load(builder.gep(tjg__mom, [lir.Constant(lir.
        IntType(64), 0), zkomu__hsyqj], inbounds=True))
    return builder.and_(rlkk__hdan, ead__udab)


def pyarray_check(builder, context, obj):
    ckw__oofk = context.get_argument_type(types.pyobject)
    ldb__aur = lir.FunctionType(lir.IntType(32), [ckw__oofk])
    nct__gbhrl = cgutils.get_or_insert_function(builder.module, ldb__aur,
        name='is_np_array')
    return builder.call(nct__gbhrl, [obj])


def pyarray_getitem(builder, context, arr_obj, ind):
    ckw__oofk = context.get_argument_type(types.pyobject)
    iyund__qsm = context.get_value_type(types.intp)
    ccwn__iiisu = lir.FunctionType(lir.IntType(8).as_pointer(), [ckw__oofk,
        iyund__qsm])
    zacmg__vwhsk = cgutils.get_or_insert_function(builder.module,
        ccwn__iiisu, name='array_getptr1')
    fbrb__xmkt = lir.FunctionType(ckw__oofk, [ckw__oofk, lir.IntType(8).
        as_pointer()])
    xxrkv__burw = cgutils.get_or_insert_function(builder.module, fbrb__xmkt,
        name='array_getitem')
    axwkr__axn = builder.call(zacmg__vwhsk, [arr_obj, ind])
    return builder.call(xxrkv__burw, [arr_obj, axwkr__axn])


def pyarray_setitem(builder, context, arr_obj, ind, val_obj):
    ckw__oofk = context.get_argument_type(types.pyobject)
    iyund__qsm = context.get_value_type(types.intp)
    ccwn__iiisu = lir.FunctionType(lir.IntType(8).as_pointer(), [ckw__oofk,
        iyund__qsm])
    zacmg__vwhsk = cgutils.get_or_insert_function(builder.module,
        ccwn__iiisu, name='array_getptr1')
    yqoei__eaga = lir.FunctionType(lir.VoidType(), [ckw__oofk, lir.IntType(
        8).as_pointer(), ckw__oofk])
    ifddd__vaw = cgutils.get_or_insert_function(builder.module, yqoei__eaga,
        name='array_setitem')
    axwkr__axn = builder.call(zacmg__vwhsk, [arr_obj, ind])
    builder.call(ifddd__vaw, [arr_obj, axwkr__axn, val_obj])


def seq_getitem(builder, context, obj, ind):
    ckw__oofk = context.get_argument_type(types.pyobject)
    iyund__qsm = context.get_value_type(types.intp)
    jjcju__nfi = lir.FunctionType(ckw__oofk, [ckw__oofk, iyund__qsm])
    lxbg__sqjwp = cgutils.get_or_insert_function(builder.module, jjcju__nfi,
        name='seq_getitem')
    return builder.call(lxbg__sqjwp, [obj, ind])


def is_na_value(builder, context, val, C_NA):
    ckw__oofk = context.get_argument_type(types.pyobject)
    jhm__vugv = lir.FunctionType(lir.IntType(32), [ckw__oofk, ckw__oofk])
    fklr__tylb = cgutils.get_or_insert_function(builder.module, jhm__vugv,
        name='is_na_value')
    return builder.call(fklr__tylb, [val, C_NA])


def list_check(builder, context, obj):
    ckw__oofk = context.get_argument_type(types.pyobject)
    ghi__hzsj = context.get_value_type(types.int32)
    vwe__hiic = lir.FunctionType(ghi__hzsj, [ckw__oofk])
    omzwq__siacl = cgutils.get_or_insert_function(builder.module, vwe__hiic,
        name='list_check')
    return builder.call(omzwq__siacl, [obj])


def dict_keys(builder, context, obj):
    ckw__oofk = context.get_argument_type(types.pyobject)
    vwe__hiic = lir.FunctionType(ckw__oofk, [ckw__oofk])
    omzwq__siacl = cgutils.get_or_insert_function(builder.module, vwe__hiic,
        name='dict_keys')
    return builder.call(omzwq__siacl, [obj])


def dict_values(builder, context, obj):
    ckw__oofk = context.get_argument_type(types.pyobject)
    vwe__hiic = lir.FunctionType(ckw__oofk, [ckw__oofk])
    omzwq__siacl = cgutils.get_or_insert_function(builder.module, vwe__hiic,
        name='dict_values')
    return builder.call(omzwq__siacl, [obj])


def dict_merge_from_seq2(builder, context, dict_obj, seq2_obj):
    ckw__oofk = context.get_argument_type(types.pyobject)
    vwe__hiic = lir.FunctionType(lir.VoidType(), [ckw__oofk, ckw__oofk])
    omzwq__siacl = cgutils.get_or_insert_function(builder.module, vwe__hiic,
        name='dict_merge_from_seq2')
    builder.call(omzwq__siacl, [dict_obj, seq2_obj])


def to_arr_obj_if_list_obj(c, context, builder, val, typ):
    if not (isinstance(typ, types.List) or bodo.utils.utils.is_array_typ(
        typ, False)):
        return val
    wvaam__lzv = cgutils.alloca_once_value(builder, val)
    mjj__csga = list_check(builder, context, val)
    gtyxa__enlhs = builder.icmp_unsigned('!=', mjj__csga, lir.Constant(
        mjj__csga.type, 0))
    with builder.if_then(gtyxa__enlhs):
        gmv__mbida = context.insert_const_string(builder.module, 'numpy')
        sih__fcww = c.pyapi.import_module_noblock(gmv__mbida)
        rmdzq__galds = 'object_'
        if isinstance(typ, types.Array) or isinstance(typ.dtype, types.Float):
            rmdzq__galds = str(typ.dtype)
        ckdmx__boz = c.pyapi.object_getattr_string(sih__fcww, rmdzq__galds)
        ogc__tobk = builder.load(wvaam__lzv)
        xiv__csgat = c.pyapi.call_method(sih__fcww, 'asarray', (ogc__tobk,
            ckdmx__boz))
        builder.store(xiv__csgat, wvaam__lzv)
        c.pyapi.decref(sih__fcww)
        c.pyapi.decref(ckdmx__boz)
    val = builder.load(wvaam__lzv)
    return val


def get_array_elem_counts(c, builder, context, arr_obj, typ):
    from bodo.libs.array_item_arr_ext import ArrayItemArrayType
    from bodo.libs.map_arr_ext import MapArrayType
    from bodo.libs.str_arr_ext import get_utf8_size, string_array_type
    from bodo.libs.struct_arr_ext import StructArrayType, StructType
    from bodo.libs.tuple_arr_ext import TupleArrayType
    if typ == bodo.string_type:
        tzmqd__scafq = c.pyapi.to_native_value(bodo.string_type, arr_obj).value
        fsg__awn, jxuo__girfp = c.pyapi.call_jit_code(lambda a:
            get_utf8_size(a), types.int64(bodo.string_type), [tzmqd__scafq])
        context.nrt.decref(builder, typ, tzmqd__scafq)
        return cgutils.pack_array(builder, [jxuo__girfp])
    if isinstance(typ, (StructType, types.BaseTuple)):
        gmv__mbida = context.insert_const_string(builder.module, 'pandas')
        rnrc__wtg = c.pyapi.import_module_noblock(gmv__mbida)
        C_NA = c.pyapi.object_getattr_string(rnrc__wtg, 'NA')
        qtpu__rzv = bodo.utils.transform.get_type_alloc_counts(typ)
        svl__moyen = context.make_tuple(builder, types.Tuple(qtpu__rzv * [
            types.int64]), qtpu__rzv * [context.get_constant(types.int64, 0)])
        rne__mloa = cgutils.alloca_once_value(builder, svl__moyen)
        vgxsz__mswd = 0
        dcjvd__edxq = typ.data if isinstance(typ, StructType) else typ.types
        for idcys__dfio, t in enumerate(dcjvd__edxq):
            nzsmf__rgy = bodo.utils.transform.get_type_alloc_counts(t)
            if nzsmf__rgy == 0:
                continue
            if isinstance(typ, StructType):
                val_obj = c.pyapi.dict_getitem_string(arr_obj, typ.names[
                    idcys__dfio])
            else:
                val_obj = c.pyapi.tuple_getitem(arr_obj, idcys__dfio)
            phyc__nyos = is_na_value(builder, context, val_obj, C_NA)
            ekhl__ckn = builder.icmp_unsigned('!=', phyc__nyos, lir.
                Constant(phyc__nyos.type, 1))
            with builder.if_then(ekhl__ckn):
                svl__moyen = builder.load(rne__mloa)
                mgy__pzeze = get_array_elem_counts(c, builder, context,
                    val_obj, t)
                for idcys__dfio in range(nzsmf__rgy):
                    emabi__jlfw = builder.extract_value(svl__moyen, 
                        vgxsz__mswd + idcys__dfio)
                    xavh__lsxn = builder.extract_value(mgy__pzeze, idcys__dfio)
                    svl__moyen = builder.insert_value(svl__moyen, builder.
                        add(emabi__jlfw, xavh__lsxn), vgxsz__mswd + idcys__dfio
                        )
                builder.store(svl__moyen, rne__mloa)
            vgxsz__mswd += nzsmf__rgy
        c.pyapi.decref(rnrc__wtg)
        c.pyapi.decref(C_NA)
        return builder.load(rne__mloa)
    if not bodo.utils.utils.is_array_typ(typ, False):
        return cgutils.pack_array(builder, [], lir.IntType(64))
    n = bodo.utils.utils.object_length(c, arr_obj)
    if not (isinstance(typ, (ArrayItemArrayType, StructArrayType,
        TupleArrayType, MapArrayType)) or typ == string_array_type):
        return cgutils.pack_array(builder, [n])
    gmv__mbida = context.insert_const_string(builder.module, 'pandas')
    rnrc__wtg = c.pyapi.import_module_noblock(gmv__mbida)
    C_NA = c.pyapi.object_getattr_string(rnrc__wtg, 'NA')
    qtpu__rzv = bodo.utils.transform.get_type_alloc_counts(typ)
    svl__moyen = context.make_tuple(builder, types.Tuple(qtpu__rzv * [types
        .int64]), [n] + (qtpu__rzv - 1) * [context.get_constant(types.int64,
        0)])
    rne__mloa = cgutils.alloca_once_value(builder, svl__moyen)
    with cgutils.for_range(builder, n) as udytg__ynwss:
        pvua__lel = udytg__ynwss.index
        qmy__oze = seq_getitem(builder, context, arr_obj, pvua__lel)
        phyc__nyos = is_na_value(builder, context, qmy__oze, C_NA)
        ekhl__ckn = builder.icmp_unsigned('!=', phyc__nyos, lir.Constant(
            phyc__nyos.type, 1))
        with builder.if_then(ekhl__ckn):
            if isinstance(typ, ArrayItemArrayType) or typ == string_array_type:
                svl__moyen = builder.load(rne__mloa)
                mgy__pzeze = get_array_elem_counts(c, builder, context,
                    qmy__oze, typ.dtype)
                for idcys__dfio in range(qtpu__rzv - 1):
                    emabi__jlfw = builder.extract_value(svl__moyen, 
                        idcys__dfio + 1)
                    xavh__lsxn = builder.extract_value(mgy__pzeze, idcys__dfio)
                    svl__moyen = builder.insert_value(svl__moyen, builder.
                        add(emabi__jlfw, xavh__lsxn), idcys__dfio + 1)
                builder.store(svl__moyen, rne__mloa)
            elif isinstance(typ, (StructArrayType, TupleArrayType)):
                vgxsz__mswd = 1
                for idcys__dfio, t in enumerate(typ.data):
                    nzsmf__rgy = bodo.utils.transform.get_type_alloc_counts(t
                        .dtype)
                    if nzsmf__rgy == 0:
                        continue
                    if isinstance(typ, TupleArrayType):
                        val_obj = c.pyapi.tuple_getitem(qmy__oze, idcys__dfio)
                    else:
                        val_obj = c.pyapi.dict_getitem_string(qmy__oze, typ
                            .names[idcys__dfio])
                    phyc__nyos = is_na_value(builder, context, val_obj, C_NA)
                    ekhl__ckn = builder.icmp_unsigned('!=', phyc__nyos, lir
                        .Constant(phyc__nyos.type, 1))
                    with builder.if_then(ekhl__ckn):
                        svl__moyen = builder.load(rne__mloa)
                        mgy__pzeze = get_array_elem_counts(c, builder,
                            context, val_obj, t.dtype)
                        for idcys__dfio in range(nzsmf__rgy):
                            emabi__jlfw = builder.extract_value(svl__moyen,
                                vgxsz__mswd + idcys__dfio)
                            xavh__lsxn = builder.extract_value(mgy__pzeze,
                                idcys__dfio)
                            svl__moyen = builder.insert_value(svl__moyen,
                                builder.add(emabi__jlfw, xavh__lsxn), 
                                vgxsz__mswd + idcys__dfio)
                        builder.store(svl__moyen, rne__mloa)
                    vgxsz__mswd += nzsmf__rgy
            else:
                assert isinstance(typ, MapArrayType), typ
                svl__moyen = builder.load(rne__mloa)
                oqdae__ioox = dict_keys(builder, context, qmy__oze)
                igamp__cjn = dict_values(builder, context, qmy__oze)
                qvlxk__nibn = get_array_elem_counts(c, builder, context,
                    oqdae__ioox, typ.key_arr_type)
                dpwoe__uvlt = bodo.utils.transform.get_type_alloc_counts(typ
                    .key_arr_type)
                for idcys__dfio in range(1, dpwoe__uvlt + 1):
                    emabi__jlfw = builder.extract_value(svl__moyen, idcys__dfio
                        )
                    xavh__lsxn = builder.extract_value(qvlxk__nibn, 
                        idcys__dfio - 1)
                    svl__moyen = builder.insert_value(svl__moyen, builder.
                        add(emabi__jlfw, xavh__lsxn), idcys__dfio)
                vxy__bmpqz = get_array_elem_counts(c, builder, context,
                    igamp__cjn, typ.value_arr_type)
                for idcys__dfio in range(dpwoe__uvlt + 1, qtpu__rzv):
                    emabi__jlfw = builder.extract_value(svl__moyen, idcys__dfio
                        )
                    xavh__lsxn = builder.extract_value(vxy__bmpqz, 
                        idcys__dfio - dpwoe__uvlt)
                    svl__moyen = builder.insert_value(svl__moyen, builder.
                        add(emabi__jlfw, xavh__lsxn), idcys__dfio)
                builder.store(svl__moyen, rne__mloa)
                c.pyapi.decref(oqdae__ioox)
                c.pyapi.decref(igamp__cjn)
        c.pyapi.decref(qmy__oze)
    c.pyapi.decref(rnrc__wtg)
    c.pyapi.decref(C_NA)
    return builder.load(rne__mloa)


def gen_allocate_array(context, builder, arr_type, n_elems, c=None):
    mfrt__hyeu = n_elems.type.count
    assert mfrt__hyeu >= 1
    yjo__fsv = builder.extract_value(n_elems, 0)
    if mfrt__hyeu != 1:
        zdu__tjxmk = cgutils.pack_array(builder, [builder.extract_value(
            n_elems, idcys__dfio) for idcys__dfio in range(1, mfrt__hyeu)])
        bcsyr__mvjbw = types.Tuple([types.int64] * (mfrt__hyeu - 1))
    else:
        zdu__tjxmk = context.get_dummy_value()
        bcsyr__mvjbw = types.none
    rrkq__ymsb = types.TypeRef(arr_type)
    fzz__pbrru = arr_type(types.int64, rrkq__ymsb, bcsyr__mvjbw)
    args = [yjo__fsv, context.get_dummy_value(), zdu__tjxmk]
    fwhto__ivyq = lambda n, t, s: bodo.utils.utils.alloc_type(n, t, s)
    if c:
        fsg__awn, dkal__sfvce = c.pyapi.call_jit_code(fwhto__ivyq,
            fzz__pbrru, args)
    else:
        dkal__sfvce = context.compile_internal(builder, fwhto__ivyq,
            fzz__pbrru, args)
    return dkal__sfvce


def is_ll_eq(builder, val1, val2):
    xip__etzw = val1.type.pointee
    wqfsm__whi = val2.type.pointee
    assert xip__etzw == wqfsm__whi, 'invalid llvm value comparison'
    if isinstance(xip__etzw, (lir.BaseStructType, lir.ArrayType)):
        n_elems = len(xip__etzw.elements) if isinstance(xip__etzw, lir.
            BaseStructType) else xip__etzw.count
        juxzk__eelxf = lir.Constant(lir.IntType(1), 1)
        for idcys__dfio in range(n_elems):
            puhfs__ifh = lir.IntType(32)(0)
            gtswq__gwsq = lir.IntType(32)(idcys__dfio)
            gpjr__hsr = builder.gep(val1, [puhfs__ifh, gtswq__gwsq],
                inbounds=True)
            xlq__bucdz = builder.gep(val2, [puhfs__ifh, gtswq__gwsq],
                inbounds=True)
            juxzk__eelxf = builder.and_(juxzk__eelxf, is_ll_eq(builder,
                gpjr__hsr, xlq__bucdz))
        return juxzk__eelxf
    lwy__calt = builder.load(val1)
    kiu__erfat = builder.load(val2)
    if lwy__calt.type in (lir.FloatType(), lir.DoubleType()):
        kuntc__jfev = 32 if lwy__calt.type == lir.FloatType() else 64
        lwy__calt = builder.bitcast(lwy__calt, lir.IntType(kuntc__jfev))
        kiu__erfat = builder.bitcast(kiu__erfat, lir.IntType(kuntc__jfev))
    return builder.icmp_unsigned('==', lwy__calt, kiu__erfat)
