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
    aefvs__ixhp = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
    iqiul__ktt = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
    evc__fbc = builder.gep(null_bitmap_ptr, [aefvs__ixhp], inbounds=True)
    nns__fdyn = builder.load(evc__fbc)
    trhmb__sku = lir.ArrayType(lir.IntType(8), 8)
    dclu__xwh = cgutils.alloca_once_value(builder, lir.Constant(trhmb__sku,
        (1, 2, 4, 8, 16, 32, 64, 128)))
    hcc__knwl = builder.load(builder.gep(dclu__xwh, [lir.Constant(lir.
        IntType(64), 0), iqiul__ktt], inbounds=True))
    if val:
        builder.store(builder.or_(nns__fdyn, hcc__knwl), evc__fbc)
    else:
        hcc__knwl = builder.xor(hcc__knwl, lir.Constant(lir.IntType(8), -1))
        builder.store(builder.and_(nns__fdyn, hcc__knwl), evc__fbc)


def get_bitmap_bit(builder, null_bitmap_ptr, ind):
    aefvs__ixhp = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
    iqiul__ktt = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
    nns__fdyn = builder.load(builder.gep(null_bitmap_ptr, [aefvs__ixhp],
        inbounds=True))
    trhmb__sku = lir.ArrayType(lir.IntType(8), 8)
    dclu__xwh = cgutils.alloca_once_value(builder, lir.Constant(trhmb__sku,
        (1, 2, 4, 8, 16, 32, 64, 128)))
    hcc__knwl = builder.load(builder.gep(dclu__xwh, [lir.Constant(lir.
        IntType(64), 0), iqiul__ktt], inbounds=True))
    return builder.and_(nns__fdyn, hcc__knwl)


def pyarray_check(builder, context, obj):
    cyypv__qrp = context.get_argument_type(types.pyobject)
    tidx__bwyqg = lir.FunctionType(lir.IntType(32), [cyypv__qrp])
    qzlw__tnwqv = cgutils.get_or_insert_function(builder.module,
        tidx__bwyqg, name='is_np_array')
    return builder.call(qzlw__tnwqv, [obj])


def pyarray_getitem(builder, context, arr_obj, ind):
    cyypv__qrp = context.get_argument_type(types.pyobject)
    mpzs__dfxt = context.get_value_type(types.intp)
    wes__hdyfm = lir.FunctionType(lir.IntType(8).as_pointer(), [cyypv__qrp,
        mpzs__dfxt])
    gljs__vxa = cgutils.get_or_insert_function(builder.module, wes__hdyfm,
        name='array_getptr1')
    qinn__ilj = lir.FunctionType(cyypv__qrp, [cyypv__qrp, lir.IntType(8).
        as_pointer()])
    iflt__wbbh = cgutils.get_or_insert_function(builder.module, qinn__ilj,
        name='array_getitem')
    jekz__efmg = builder.call(gljs__vxa, [arr_obj, ind])
    return builder.call(iflt__wbbh, [arr_obj, jekz__efmg])


def pyarray_setitem(builder, context, arr_obj, ind, val_obj):
    cyypv__qrp = context.get_argument_type(types.pyobject)
    mpzs__dfxt = context.get_value_type(types.intp)
    wes__hdyfm = lir.FunctionType(lir.IntType(8).as_pointer(), [cyypv__qrp,
        mpzs__dfxt])
    gljs__vxa = cgutils.get_or_insert_function(builder.module, wes__hdyfm,
        name='array_getptr1')
    whv__mwhj = lir.FunctionType(lir.VoidType(), [cyypv__qrp, lir.IntType(8
        ).as_pointer(), cyypv__qrp])
    tkk__rff = cgutils.get_or_insert_function(builder.module, whv__mwhj,
        name='array_setitem')
    jekz__efmg = builder.call(gljs__vxa, [arr_obj, ind])
    builder.call(tkk__rff, [arr_obj, jekz__efmg, val_obj])


def seq_getitem(builder, context, obj, ind):
    cyypv__qrp = context.get_argument_type(types.pyobject)
    mpzs__dfxt = context.get_value_type(types.intp)
    folxy__xhrz = lir.FunctionType(cyypv__qrp, [cyypv__qrp, mpzs__dfxt])
    naj__tavb = cgutils.get_or_insert_function(builder.module, folxy__xhrz,
        name='seq_getitem')
    return builder.call(naj__tavb, [obj, ind])


def is_na_value(builder, context, val, C_NA):
    cyypv__qrp = context.get_argument_type(types.pyobject)
    rez__xmgfu = lir.FunctionType(lir.IntType(32), [cyypv__qrp, cyypv__qrp])
    gpkli__iferx = cgutils.get_or_insert_function(builder.module,
        rez__xmgfu, name='is_na_value')
    return builder.call(gpkli__iferx, [val, C_NA])


def list_check(builder, context, obj):
    cyypv__qrp = context.get_argument_type(types.pyobject)
    qeu__hjct = context.get_value_type(types.int32)
    vot__vgn = lir.FunctionType(qeu__hjct, [cyypv__qrp])
    pnsgr__cyrqj = cgutils.get_or_insert_function(builder.module, vot__vgn,
        name='list_check')
    return builder.call(pnsgr__cyrqj, [obj])


def dict_keys(builder, context, obj):
    cyypv__qrp = context.get_argument_type(types.pyobject)
    vot__vgn = lir.FunctionType(cyypv__qrp, [cyypv__qrp])
    pnsgr__cyrqj = cgutils.get_or_insert_function(builder.module, vot__vgn,
        name='dict_keys')
    return builder.call(pnsgr__cyrqj, [obj])


def dict_values(builder, context, obj):
    cyypv__qrp = context.get_argument_type(types.pyobject)
    vot__vgn = lir.FunctionType(cyypv__qrp, [cyypv__qrp])
    pnsgr__cyrqj = cgutils.get_or_insert_function(builder.module, vot__vgn,
        name='dict_values')
    return builder.call(pnsgr__cyrqj, [obj])


def dict_merge_from_seq2(builder, context, dict_obj, seq2_obj):
    cyypv__qrp = context.get_argument_type(types.pyobject)
    vot__vgn = lir.FunctionType(lir.VoidType(), [cyypv__qrp, cyypv__qrp])
    pnsgr__cyrqj = cgutils.get_or_insert_function(builder.module, vot__vgn,
        name='dict_merge_from_seq2')
    builder.call(pnsgr__cyrqj, [dict_obj, seq2_obj])


def to_arr_obj_if_list_obj(c, context, builder, val, typ):
    if not (isinstance(typ, types.List) or bodo.utils.utils.is_array_typ(
        typ, False)):
        return val
    xjwbi__bgt = cgutils.alloca_once_value(builder, val)
    tppo__fsur = list_check(builder, context, val)
    oqgf__rezen = builder.icmp_unsigned('!=', tppo__fsur, lir.Constant(
        tppo__fsur.type, 0))
    with builder.if_then(oqgf__rezen):
        qwvdm__isp = context.insert_const_string(builder.module, 'numpy')
        stu__bwpb = c.pyapi.import_module_noblock(qwvdm__isp)
        taumc__yhwix = 'object_'
        if isinstance(typ, types.Array) or isinstance(typ.dtype, types.Float):
            taumc__yhwix = str(typ.dtype)
        bhqvs__cqxol = c.pyapi.object_getattr_string(stu__bwpb, taumc__yhwix)
        lhab__nts = builder.load(xjwbi__bgt)
        rbkb__vbaxs = c.pyapi.call_method(stu__bwpb, 'asarray', (lhab__nts,
            bhqvs__cqxol))
        builder.store(rbkb__vbaxs, xjwbi__bgt)
        c.pyapi.decref(stu__bwpb)
        c.pyapi.decref(bhqvs__cqxol)
    val = builder.load(xjwbi__bgt)
    return val


def get_array_elem_counts(c, builder, context, arr_obj, typ):
    from bodo.libs.array_item_arr_ext import ArrayItemArrayType
    from bodo.libs.map_arr_ext import MapArrayType
    from bodo.libs.str_arr_ext import get_utf8_size, string_array_type
    from bodo.libs.struct_arr_ext import StructArrayType, StructType
    from bodo.libs.tuple_arr_ext import TupleArrayType
    if typ == bodo.string_type:
        yhfwl__dfppm = c.pyapi.to_native_value(bodo.string_type, arr_obj).value
        ydkrv__avck, bzll__iqv = c.pyapi.call_jit_code(lambda a:
            get_utf8_size(a), types.int64(bodo.string_type), [yhfwl__dfppm])
        context.nrt.decref(builder, typ, yhfwl__dfppm)
        return cgutils.pack_array(builder, [bzll__iqv])
    if isinstance(typ, (StructType, types.BaseTuple)):
        qwvdm__isp = context.insert_const_string(builder.module, 'pandas')
        rmvv__hsvsn = c.pyapi.import_module_noblock(qwvdm__isp)
        C_NA = c.pyapi.object_getattr_string(rmvv__hsvsn, 'NA')
        gnmk__rpgfm = bodo.utils.transform.get_type_alloc_counts(typ)
        bdtqk__toa = context.make_tuple(builder, types.Tuple(gnmk__rpgfm *
            [types.int64]), gnmk__rpgfm * [context.get_constant(types.int64,
            0)])
        gnymg__xcp = cgutils.alloca_once_value(builder, bdtqk__toa)
        oxwb__xgifd = 0
        vbsju__gqvk = typ.data if isinstance(typ, StructType) else typ.types
        for ukdc__fyyy, t in enumerate(vbsju__gqvk):
            lqsgc__egqpz = bodo.utils.transform.get_type_alloc_counts(t)
            if lqsgc__egqpz == 0:
                continue
            if isinstance(typ, StructType):
                val_obj = c.pyapi.dict_getitem_string(arr_obj, typ.names[
                    ukdc__fyyy])
            else:
                val_obj = c.pyapi.tuple_getitem(arr_obj, ukdc__fyyy)
            eex__zvv = is_na_value(builder, context, val_obj, C_NA)
            plgxx__dwu = builder.icmp_unsigned('!=', eex__zvv, lir.Constant
                (eex__zvv.type, 1))
            with builder.if_then(plgxx__dwu):
                bdtqk__toa = builder.load(gnymg__xcp)
                vboko__ljr = get_array_elem_counts(c, builder, context,
                    val_obj, t)
                for ukdc__fyyy in range(lqsgc__egqpz):
                    uxf__vzudi = builder.extract_value(bdtqk__toa, 
                        oxwb__xgifd + ukdc__fyyy)
                    caws__rinz = builder.extract_value(vboko__ljr, ukdc__fyyy)
                    bdtqk__toa = builder.insert_value(bdtqk__toa, builder.
                        add(uxf__vzudi, caws__rinz), oxwb__xgifd + ukdc__fyyy)
                builder.store(bdtqk__toa, gnymg__xcp)
            oxwb__xgifd += lqsgc__egqpz
        c.pyapi.decref(rmvv__hsvsn)
        c.pyapi.decref(C_NA)
        return builder.load(gnymg__xcp)
    if not bodo.utils.utils.is_array_typ(typ, False):
        return cgutils.pack_array(builder, [], lir.IntType(64))
    n = bodo.utils.utils.object_length(c, arr_obj)
    if not (isinstance(typ, (ArrayItemArrayType, StructArrayType,
        TupleArrayType, MapArrayType)) or typ == string_array_type):
        return cgutils.pack_array(builder, [n])
    qwvdm__isp = context.insert_const_string(builder.module, 'pandas')
    rmvv__hsvsn = c.pyapi.import_module_noblock(qwvdm__isp)
    C_NA = c.pyapi.object_getattr_string(rmvv__hsvsn, 'NA')
    gnmk__rpgfm = bodo.utils.transform.get_type_alloc_counts(typ)
    bdtqk__toa = context.make_tuple(builder, types.Tuple(gnmk__rpgfm * [
        types.int64]), [n] + (gnmk__rpgfm - 1) * [context.get_constant(
        types.int64, 0)])
    gnymg__xcp = cgutils.alloca_once_value(builder, bdtqk__toa)
    with cgutils.for_range(builder, n) as rmh__fln:
        kroww__akndf = rmh__fln.index
        yui__gywv = seq_getitem(builder, context, arr_obj, kroww__akndf)
        eex__zvv = is_na_value(builder, context, yui__gywv, C_NA)
        plgxx__dwu = builder.icmp_unsigned('!=', eex__zvv, lir.Constant(
            eex__zvv.type, 1))
        with builder.if_then(plgxx__dwu):
            if isinstance(typ, ArrayItemArrayType) or typ == string_array_type:
                bdtqk__toa = builder.load(gnymg__xcp)
                vboko__ljr = get_array_elem_counts(c, builder, context,
                    yui__gywv, typ.dtype)
                for ukdc__fyyy in range(gnmk__rpgfm - 1):
                    uxf__vzudi = builder.extract_value(bdtqk__toa, 
                        ukdc__fyyy + 1)
                    caws__rinz = builder.extract_value(vboko__ljr, ukdc__fyyy)
                    bdtqk__toa = builder.insert_value(bdtqk__toa, builder.
                        add(uxf__vzudi, caws__rinz), ukdc__fyyy + 1)
                builder.store(bdtqk__toa, gnymg__xcp)
            elif isinstance(typ, (StructArrayType, TupleArrayType)):
                oxwb__xgifd = 1
                for ukdc__fyyy, t in enumerate(typ.data):
                    lqsgc__egqpz = bodo.utils.transform.get_type_alloc_counts(t
                        .dtype)
                    if lqsgc__egqpz == 0:
                        continue
                    if isinstance(typ, TupleArrayType):
                        val_obj = c.pyapi.tuple_getitem(yui__gywv, ukdc__fyyy)
                    else:
                        val_obj = c.pyapi.dict_getitem_string(yui__gywv,
                            typ.names[ukdc__fyyy])
                    eex__zvv = is_na_value(builder, context, val_obj, C_NA)
                    plgxx__dwu = builder.icmp_unsigned('!=', eex__zvv, lir.
                        Constant(eex__zvv.type, 1))
                    with builder.if_then(plgxx__dwu):
                        bdtqk__toa = builder.load(gnymg__xcp)
                        vboko__ljr = get_array_elem_counts(c, builder,
                            context, val_obj, t.dtype)
                        for ukdc__fyyy in range(lqsgc__egqpz):
                            uxf__vzudi = builder.extract_value(bdtqk__toa, 
                                oxwb__xgifd + ukdc__fyyy)
                            caws__rinz = builder.extract_value(vboko__ljr,
                                ukdc__fyyy)
                            bdtqk__toa = builder.insert_value(bdtqk__toa,
                                builder.add(uxf__vzudi, caws__rinz), 
                                oxwb__xgifd + ukdc__fyyy)
                        builder.store(bdtqk__toa, gnymg__xcp)
                    oxwb__xgifd += lqsgc__egqpz
            else:
                assert isinstance(typ, MapArrayType), typ
                bdtqk__toa = builder.load(gnymg__xcp)
                ncjy__jmh = dict_keys(builder, context, yui__gywv)
                uqmjg__hesu = dict_values(builder, context, yui__gywv)
                yfsz__fiwi = get_array_elem_counts(c, builder, context,
                    ncjy__jmh, typ.key_arr_type)
                bgkcr__cta = bodo.utils.transform.get_type_alloc_counts(typ
                    .key_arr_type)
                for ukdc__fyyy in range(1, bgkcr__cta + 1):
                    uxf__vzudi = builder.extract_value(bdtqk__toa, ukdc__fyyy)
                    caws__rinz = builder.extract_value(yfsz__fiwi, 
                        ukdc__fyyy - 1)
                    bdtqk__toa = builder.insert_value(bdtqk__toa, builder.
                        add(uxf__vzudi, caws__rinz), ukdc__fyyy)
                zuwg__eyp = get_array_elem_counts(c, builder, context,
                    uqmjg__hesu, typ.value_arr_type)
                for ukdc__fyyy in range(bgkcr__cta + 1, gnmk__rpgfm):
                    uxf__vzudi = builder.extract_value(bdtqk__toa, ukdc__fyyy)
                    caws__rinz = builder.extract_value(zuwg__eyp, 
                        ukdc__fyyy - bgkcr__cta)
                    bdtqk__toa = builder.insert_value(bdtqk__toa, builder.
                        add(uxf__vzudi, caws__rinz), ukdc__fyyy)
                builder.store(bdtqk__toa, gnymg__xcp)
                c.pyapi.decref(ncjy__jmh)
                c.pyapi.decref(uqmjg__hesu)
        c.pyapi.decref(yui__gywv)
    c.pyapi.decref(rmvv__hsvsn)
    c.pyapi.decref(C_NA)
    return builder.load(gnymg__xcp)


def gen_allocate_array(context, builder, arr_type, n_elems, c=None):
    puwl__xyfh = n_elems.type.count
    assert puwl__xyfh >= 1
    wvpw__lna = builder.extract_value(n_elems, 0)
    if puwl__xyfh != 1:
        dig__rtmc = cgutils.pack_array(builder, [builder.extract_value(
            n_elems, ukdc__fyyy) for ukdc__fyyy in range(1, puwl__xyfh)])
        iywo__vbti = types.Tuple([types.int64] * (puwl__xyfh - 1))
    else:
        dig__rtmc = context.get_dummy_value()
        iywo__vbti = types.none
    tsvdg__qqpzn = types.TypeRef(arr_type)
    mws__pqwj = arr_type(types.int64, tsvdg__qqpzn, iywo__vbti)
    args = [wvpw__lna, context.get_dummy_value(), dig__rtmc]
    slvw__ufvqr = lambda n, t, s: bodo.utils.utils.alloc_type(n, t, s)
    if c:
        ydkrv__avck, iwukv__anyv = c.pyapi.call_jit_code(slvw__ufvqr,
            mws__pqwj, args)
    else:
        iwukv__anyv = context.compile_internal(builder, slvw__ufvqr,
            mws__pqwj, args)
    return iwukv__anyv


def is_ll_eq(builder, val1, val2):
    hyht__hgh = val1.type.pointee
    qshi__tulko = val2.type.pointee
    assert hyht__hgh == qshi__tulko, 'invalid llvm value comparison'
    if isinstance(hyht__hgh, (lir.BaseStructType, lir.ArrayType)):
        n_elems = len(hyht__hgh.elements) if isinstance(hyht__hgh, lir.
            BaseStructType) else hyht__hgh.count
        jsnz__jvp = lir.Constant(lir.IntType(1), 1)
        for ukdc__fyyy in range(n_elems):
            tihif__uhur = lir.IntType(32)(0)
            bkyzg__yllel = lir.IntType(32)(ukdc__fyyy)
            wyx__atb = builder.gep(val1, [tihif__uhur, bkyzg__yllel],
                inbounds=True)
            vfqnx__utsa = builder.gep(val2, [tihif__uhur, bkyzg__yllel],
                inbounds=True)
            jsnz__jvp = builder.and_(jsnz__jvp, is_ll_eq(builder, wyx__atb,
                vfqnx__utsa))
        return jsnz__jvp
    wcmt__hcdp = builder.load(val1)
    vdhi__erj = builder.load(val2)
    if wcmt__hcdp.type in (lir.FloatType(), lir.DoubleType()):
        feuj__tfyk = 32 if wcmt__hcdp.type == lir.FloatType() else 64
        wcmt__hcdp = builder.bitcast(wcmt__hcdp, lir.IntType(feuj__tfyk))
        vdhi__erj = builder.bitcast(vdhi__erj, lir.IntType(feuj__tfyk))
    return builder.icmp_unsigned('==', wcmt__hcdp, vdhi__erj)
