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
    kncbk__wwyf = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
    xsuyd__lonuc = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
    weuz__zcsox = builder.gep(null_bitmap_ptr, [kncbk__wwyf], inbounds=True)
    exxak__nyola = builder.load(weuz__zcsox)
    dze__nsjef = lir.ArrayType(lir.IntType(8), 8)
    jsfxp__uzgoa = cgutils.alloca_once_value(builder, lir.Constant(
        dze__nsjef, (1, 2, 4, 8, 16, 32, 64, 128)))
    ircuy__crht = builder.load(builder.gep(jsfxp__uzgoa, [lir.Constant(lir.
        IntType(64), 0), xsuyd__lonuc], inbounds=True))
    if val:
        builder.store(builder.or_(exxak__nyola, ircuy__crht), weuz__zcsox)
    else:
        ircuy__crht = builder.xor(ircuy__crht, lir.Constant(lir.IntType(8), -1)
            )
        builder.store(builder.and_(exxak__nyola, ircuy__crht), weuz__zcsox)


def get_bitmap_bit(builder, null_bitmap_ptr, ind):
    kncbk__wwyf = builder.lshr(ind, lir.Constant(lir.IntType(64), 3))
    xsuyd__lonuc = builder.urem(ind, lir.Constant(lir.IntType(64), 8))
    exxak__nyola = builder.load(builder.gep(null_bitmap_ptr, [kncbk__wwyf],
        inbounds=True))
    dze__nsjef = lir.ArrayType(lir.IntType(8), 8)
    jsfxp__uzgoa = cgutils.alloca_once_value(builder, lir.Constant(
        dze__nsjef, (1, 2, 4, 8, 16, 32, 64, 128)))
    ircuy__crht = builder.load(builder.gep(jsfxp__uzgoa, [lir.Constant(lir.
        IntType(64), 0), xsuyd__lonuc], inbounds=True))
    return builder.and_(exxak__nyola, ircuy__crht)


def pyarray_check(builder, context, obj):
    psre__ewirb = context.get_argument_type(types.pyobject)
    sgm__orpa = lir.FunctionType(lir.IntType(32), [psre__ewirb])
    tazv__osexh = cgutils.get_or_insert_function(builder.module, sgm__orpa,
        name='is_np_array')
    return builder.call(tazv__osexh, [obj])


def pyarray_getitem(builder, context, arr_obj, ind):
    psre__ewirb = context.get_argument_type(types.pyobject)
    zsk__qmjps = context.get_value_type(types.intp)
    llacb__pdyba = lir.FunctionType(lir.IntType(8).as_pointer(), [
        psre__ewirb, zsk__qmjps])
    hreko__todv = cgutils.get_or_insert_function(builder.module,
        llacb__pdyba, name='array_getptr1')
    aeq__pmdb = lir.FunctionType(psre__ewirb, [psre__ewirb, lir.IntType(8).
        as_pointer()])
    ikx__yaml = cgutils.get_or_insert_function(builder.module, aeq__pmdb,
        name='array_getitem')
    bihk__waj = builder.call(hreko__todv, [arr_obj, ind])
    return builder.call(ikx__yaml, [arr_obj, bihk__waj])


def pyarray_setitem(builder, context, arr_obj, ind, val_obj):
    psre__ewirb = context.get_argument_type(types.pyobject)
    zsk__qmjps = context.get_value_type(types.intp)
    llacb__pdyba = lir.FunctionType(lir.IntType(8).as_pointer(), [
        psre__ewirb, zsk__qmjps])
    hreko__todv = cgutils.get_or_insert_function(builder.module,
        llacb__pdyba, name='array_getptr1')
    jvjr__dvkl = lir.FunctionType(lir.VoidType(), [psre__ewirb, lir.IntType
        (8).as_pointer(), psre__ewirb])
    slypy__yvno = cgutils.get_or_insert_function(builder.module, jvjr__dvkl,
        name='array_setitem')
    bihk__waj = builder.call(hreko__todv, [arr_obj, ind])
    builder.call(slypy__yvno, [arr_obj, bihk__waj, val_obj])


def seq_getitem(builder, context, obj, ind):
    psre__ewirb = context.get_argument_type(types.pyobject)
    zsk__qmjps = context.get_value_type(types.intp)
    opz__hrohu = lir.FunctionType(psre__ewirb, [psre__ewirb, zsk__qmjps])
    ehz__vlhn = cgutils.get_or_insert_function(builder.module, opz__hrohu,
        name='seq_getitem')
    return builder.call(ehz__vlhn, [obj, ind])


def is_na_value(builder, context, val, C_NA):
    psre__ewirb = context.get_argument_type(types.pyobject)
    ypjxm__wghy = lir.FunctionType(lir.IntType(32), [psre__ewirb, psre__ewirb])
    rbr__wta = cgutils.get_or_insert_function(builder.module, ypjxm__wghy,
        name='is_na_value')
    return builder.call(rbr__wta, [val, C_NA])


def list_check(builder, context, obj):
    psre__ewirb = context.get_argument_type(types.pyobject)
    fon__mrhtd = context.get_value_type(types.int32)
    dnw__dhc = lir.FunctionType(fon__mrhtd, [psre__ewirb])
    icouk__pnw = cgutils.get_or_insert_function(builder.module, dnw__dhc,
        name='list_check')
    return builder.call(icouk__pnw, [obj])


def dict_keys(builder, context, obj):
    psre__ewirb = context.get_argument_type(types.pyobject)
    dnw__dhc = lir.FunctionType(psre__ewirb, [psre__ewirb])
    icouk__pnw = cgutils.get_or_insert_function(builder.module, dnw__dhc,
        name='dict_keys')
    return builder.call(icouk__pnw, [obj])


def dict_values(builder, context, obj):
    psre__ewirb = context.get_argument_type(types.pyobject)
    dnw__dhc = lir.FunctionType(psre__ewirb, [psre__ewirb])
    icouk__pnw = cgutils.get_or_insert_function(builder.module, dnw__dhc,
        name='dict_values')
    return builder.call(icouk__pnw, [obj])


def dict_merge_from_seq2(builder, context, dict_obj, seq2_obj):
    psre__ewirb = context.get_argument_type(types.pyobject)
    dnw__dhc = lir.FunctionType(lir.VoidType(), [psre__ewirb, psre__ewirb])
    icouk__pnw = cgutils.get_or_insert_function(builder.module, dnw__dhc,
        name='dict_merge_from_seq2')
    builder.call(icouk__pnw, [dict_obj, seq2_obj])


def to_arr_obj_if_list_obj(c, context, builder, val, typ):
    if not (isinstance(typ, types.List) or bodo.utils.utils.is_array_typ(
        typ, False)):
        return val
    reb__zyr = cgutils.alloca_once_value(builder, val)
    ulna__yzg = list_check(builder, context, val)
    rav__zlsvt = builder.icmp_unsigned('!=', ulna__yzg, lir.Constant(
        ulna__yzg.type, 0))
    with builder.if_then(rav__zlsvt):
        iwhpg__ufvxc = context.insert_const_string(builder.module, 'numpy')
        pve__pplyk = c.pyapi.import_module_noblock(iwhpg__ufvxc)
        sybz__dera = 'object_'
        if isinstance(typ, types.Array) or isinstance(typ.dtype, types.Float):
            sybz__dera = str(typ.dtype)
        htjna__awcie = c.pyapi.object_getattr_string(pve__pplyk, sybz__dera)
        ssak__nzglc = builder.load(reb__zyr)
        zoaoy__kzlll = c.pyapi.call_method(pve__pplyk, 'asarray', (
            ssak__nzglc, htjna__awcie))
        builder.store(zoaoy__kzlll, reb__zyr)
        c.pyapi.decref(pve__pplyk)
        c.pyapi.decref(htjna__awcie)
    val = builder.load(reb__zyr)
    return val


def get_array_elem_counts(c, builder, context, arr_obj, typ):
    from bodo.libs.array_item_arr_ext import ArrayItemArrayType
    from bodo.libs.map_arr_ext import MapArrayType
    from bodo.libs.str_arr_ext import get_utf8_size, string_array_type
    from bodo.libs.struct_arr_ext import StructArrayType, StructType
    from bodo.libs.tuple_arr_ext import TupleArrayType
    if typ == bodo.string_type:
        ecuzp__cbj = c.pyapi.to_native_value(bodo.string_type, arr_obj).value
        lzkx__zwmmw, qjier__wutze = c.pyapi.call_jit_code(lambda a:
            get_utf8_size(a), types.int64(bodo.string_type), [ecuzp__cbj])
        context.nrt.decref(builder, typ, ecuzp__cbj)
        return cgutils.pack_array(builder, [qjier__wutze])
    if isinstance(typ, (StructType, types.BaseTuple)):
        iwhpg__ufvxc = context.insert_const_string(builder.module, 'pandas')
        efnj__rku = c.pyapi.import_module_noblock(iwhpg__ufvxc)
        C_NA = c.pyapi.object_getattr_string(efnj__rku, 'NA')
        dzpt__wjr = bodo.utils.transform.get_type_alloc_counts(typ)
        vemcn__aevd = context.make_tuple(builder, types.Tuple(dzpt__wjr * [
            types.int64]), dzpt__wjr * [context.get_constant(types.int64, 0)])
        vzedg__afd = cgutils.alloca_once_value(builder, vemcn__aevd)
        uubpa__rou = 0
        iibxj__gycu = typ.data if isinstance(typ, StructType) else typ.types
        for dgoof__btc, t in enumerate(iibxj__gycu):
            icchc__eaf = bodo.utils.transform.get_type_alloc_counts(t)
            if icchc__eaf == 0:
                continue
            if isinstance(typ, StructType):
                val_obj = c.pyapi.dict_getitem_string(arr_obj, typ.names[
                    dgoof__btc])
            else:
                val_obj = c.pyapi.tuple_getitem(arr_obj, dgoof__btc)
            gzjq__brg = is_na_value(builder, context, val_obj, C_NA)
            gdta__buu = builder.icmp_unsigned('!=', gzjq__brg, lir.Constant
                (gzjq__brg.type, 1))
            with builder.if_then(gdta__buu):
                vemcn__aevd = builder.load(vzedg__afd)
                gbgtg__alz = get_array_elem_counts(c, builder, context,
                    val_obj, t)
                for dgoof__btc in range(icchc__eaf):
                    wfnua__jjhc = builder.extract_value(vemcn__aevd, 
                        uubpa__rou + dgoof__btc)
                    advmx__xcqy = builder.extract_value(gbgtg__alz, dgoof__btc)
                    vemcn__aevd = builder.insert_value(vemcn__aevd, builder
                        .add(wfnua__jjhc, advmx__xcqy), uubpa__rou + dgoof__btc
                        )
                builder.store(vemcn__aevd, vzedg__afd)
            uubpa__rou += icchc__eaf
        c.pyapi.decref(efnj__rku)
        c.pyapi.decref(C_NA)
        return builder.load(vzedg__afd)
    if not bodo.utils.utils.is_array_typ(typ, False):
        return cgutils.pack_array(builder, [], lir.IntType(64))
    n = bodo.utils.utils.object_length(c, arr_obj)
    if not (isinstance(typ, (ArrayItemArrayType, StructArrayType,
        TupleArrayType, MapArrayType)) or typ == string_array_type):
        return cgutils.pack_array(builder, [n])
    iwhpg__ufvxc = context.insert_const_string(builder.module, 'pandas')
    efnj__rku = c.pyapi.import_module_noblock(iwhpg__ufvxc)
    C_NA = c.pyapi.object_getattr_string(efnj__rku, 'NA')
    dzpt__wjr = bodo.utils.transform.get_type_alloc_counts(typ)
    vemcn__aevd = context.make_tuple(builder, types.Tuple(dzpt__wjr * [
        types.int64]), [n] + (dzpt__wjr - 1) * [context.get_constant(types.
        int64, 0)])
    vzedg__afd = cgutils.alloca_once_value(builder, vemcn__aevd)
    with cgutils.for_range(builder, n) as scrt__esozd:
        xndo__mlhp = scrt__esozd.index
        ipyfl__vya = seq_getitem(builder, context, arr_obj, xndo__mlhp)
        gzjq__brg = is_na_value(builder, context, ipyfl__vya, C_NA)
        gdta__buu = builder.icmp_unsigned('!=', gzjq__brg, lir.Constant(
            gzjq__brg.type, 1))
        with builder.if_then(gdta__buu):
            if isinstance(typ, ArrayItemArrayType) or typ == string_array_type:
                vemcn__aevd = builder.load(vzedg__afd)
                gbgtg__alz = get_array_elem_counts(c, builder, context,
                    ipyfl__vya, typ.dtype)
                for dgoof__btc in range(dzpt__wjr - 1):
                    wfnua__jjhc = builder.extract_value(vemcn__aevd, 
                        dgoof__btc + 1)
                    advmx__xcqy = builder.extract_value(gbgtg__alz, dgoof__btc)
                    vemcn__aevd = builder.insert_value(vemcn__aevd, builder
                        .add(wfnua__jjhc, advmx__xcqy), dgoof__btc + 1)
                builder.store(vemcn__aevd, vzedg__afd)
            elif isinstance(typ, (StructArrayType, TupleArrayType)):
                uubpa__rou = 1
                for dgoof__btc, t in enumerate(typ.data):
                    icchc__eaf = bodo.utils.transform.get_type_alloc_counts(t
                        .dtype)
                    if icchc__eaf == 0:
                        continue
                    if isinstance(typ, TupleArrayType):
                        val_obj = c.pyapi.tuple_getitem(ipyfl__vya, dgoof__btc)
                    else:
                        val_obj = c.pyapi.dict_getitem_string(ipyfl__vya,
                            typ.names[dgoof__btc])
                    gzjq__brg = is_na_value(builder, context, val_obj, C_NA)
                    gdta__buu = builder.icmp_unsigned('!=', gzjq__brg, lir.
                        Constant(gzjq__brg.type, 1))
                    with builder.if_then(gdta__buu):
                        vemcn__aevd = builder.load(vzedg__afd)
                        gbgtg__alz = get_array_elem_counts(c, builder,
                            context, val_obj, t.dtype)
                        for dgoof__btc in range(icchc__eaf):
                            wfnua__jjhc = builder.extract_value(vemcn__aevd,
                                uubpa__rou + dgoof__btc)
                            advmx__xcqy = builder.extract_value(gbgtg__alz,
                                dgoof__btc)
                            vemcn__aevd = builder.insert_value(vemcn__aevd,
                                builder.add(wfnua__jjhc, advmx__xcqy), 
                                uubpa__rou + dgoof__btc)
                        builder.store(vemcn__aevd, vzedg__afd)
                    uubpa__rou += icchc__eaf
            else:
                assert isinstance(typ, MapArrayType), typ
                vemcn__aevd = builder.load(vzedg__afd)
                qbgj__oxgij = dict_keys(builder, context, ipyfl__vya)
                uohpn__ngp = dict_values(builder, context, ipyfl__vya)
                pga__jugbw = get_array_elem_counts(c, builder, context,
                    qbgj__oxgij, typ.key_arr_type)
                jip__xta = bodo.utils.transform.get_type_alloc_counts(typ.
                    key_arr_type)
                for dgoof__btc in range(1, jip__xta + 1):
                    wfnua__jjhc = builder.extract_value(vemcn__aevd, dgoof__btc
                        )
                    advmx__xcqy = builder.extract_value(pga__jugbw, 
                        dgoof__btc - 1)
                    vemcn__aevd = builder.insert_value(vemcn__aevd, builder
                        .add(wfnua__jjhc, advmx__xcqy), dgoof__btc)
                peutu__pukl = get_array_elem_counts(c, builder, context,
                    uohpn__ngp, typ.value_arr_type)
                for dgoof__btc in range(jip__xta + 1, dzpt__wjr):
                    wfnua__jjhc = builder.extract_value(vemcn__aevd, dgoof__btc
                        )
                    advmx__xcqy = builder.extract_value(peutu__pukl, 
                        dgoof__btc - jip__xta)
                    vemcn__aevd = builder.insert_value(vemcn__aevd, builder
                        .add(wfnua__jjhc, advmx__xcqy), dgoof__btc)
                builder.store(vemcn__aevd, vzedg__afd)
                c.pyapi.decref(qbgj__oxgij)
                c.pyapi.decref(uohpn__ngp)
        c.pyapi.decref(ipyfl__vya)
    c.pyapi.decref(efnj__rku)
    c.pyapi.decref(C_NA)
    return builder.load(vzedg__afd)


def gen_allocate_array(context, builder, arr_type, n_elems, c=None):
    bgm__cdu = n_elems.type.count
    assert bgm__cdu >= 1
    epsw__lisdz = builder.extract_value(n_elems, 0)
    if bgm__cdu != 1:
        gonuk__zvfkj = cgutils.pack_array(builder, [builder.extract_value(
            n_elems, dgoof__btc) for dgoof__btc in range(1, bgm__cdu)])
        gbngj__mge = types.Tuple([types.int64] * (bgm__cdu - 1))
    else:
        gonuk__zvfkj = context.get_dummy_value()
        gbngj__mge = types.none
    gktbk__lnap = types.TypeRef(arr_type)
    keou__lkt = arr_type(types.int64, gktbk__lnap, gbngj__mge)
    args = [epsw__lisdz, context.get_dummy_value(), gonuk__zvfkj]
    fron__xih = lambda n, t, s: bodo.utils.utils.alloc_type(n, t, s)
    if c:
        lzkx__zwmmw, flgq__tijy = c.pyapi.call_jit_code(fron__xih,
            keou__lkt, args)
    else:
        flgq__tijy = context.compile_internal(builder, fron__xih, keou__lkt,
            args)
    return flgq__tijy


def is_ll_eq(builder, val1, val2):
    eyfqf__zqt = val1.type.pointee
    uhif__ner = val2.type.pointee
    assert eyfqf__zqt == uhif__ner, 'invalid llvm value comparison'
    if isinstance(eyfqf__zqt, (lir.BaseStructType, lir.ArrayType)):
        n_elems = len(eyfqf__zqt.elements) if isinstance(eyfqf__zqt, lir.
            BaseStructType) else eyfqf__zqt.count
        vkxjr__cibb = lir.Constant(lir.IntType(1), 1)
        for dgoof__btc in range(n_elems):
            cfonp__hxbx = lir.IntType(32)(0)
            sevb__kqsdy = lir.IntType(32)(dgoof__btc)
            yhur__gooz = builder.gep(val1, [cfonp__hxbx, sevb__kqsdy],
                inbounds=True)
            aaea__afa = builder.gep(val2, [cfonp__hxbx, sevb__kqsdy],
                inbounds=True)
            vkxjr__cibb = builder.and_(vkxjr__cibb, is_ll_eq(builder,
                yhur__gooz, aaea__afa))
        return vkxjr__cibb
    nobkl__fuhky = builder.load(val1)
    plctq__lyj = builder.load(val2)
    if nobkl__fuhky.type in (lir.FloatType(), lir.DoubleType()):
        ufhd__zyud = 32 if nobkl__fuhky.type == lir.FloatType() else 64
        nobkl__fuhky = builder.bitcast(nobkl__fuhky, lir.IntType(ufhd__zyud))
        plctq__lyj = builder.bitcast(plctq__lyj, lir.IntType(ufhd__zyud))
    return builder.icmp_unsigned('==', nobkl__fuhky, plctq__lyj)
