"""Array implementation for map values.
Corresponds to Spark's MapType: https://spark.apache.org/docs/latest/sql-reference.html
Corresponds to Arrow's Map arrays: https://github.com/apache/arrow/blob/master/format/Schema.fbs

The implementation uses an array(struct) array underneath similar to Spark and Arrow.
For example: [{1: 2.1, 3: 1.1}, {5: -1.0}]
[[{"key": 1, "value" 2.1}, {"key": 3, "value": 1.1}], [{"key": 5, "value": -1.0}]]
"""
import operator
import llvmlite.binding as ll
import numba
import numpy as np
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.extending import NativeValue, box, intrinsic, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_model, unbox
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
from bodo.hiframes.datetime_date_ext import datetime_date_type
from bodo.libs.array_item_arr_ext import ArrayItemArrayType, _get_array_item_arr_payload, offset_type
from bodo.libs.struct_arr_ext import StructArrayType, _get_struct_arr_payload
from bodo.utils.cg_helpers import dict_keys, dict_merge_from_seq2, dict_values, gen_allocate_array, get_array_elem_counts, get_bitmap_bit, is_na_value, pyarray_setitem, seq_getitem, set_bitmap_bit
from bodo.utils.typing import BodoError
from bodo.libs import array_ext, hdist
ll.add_symbol('count_total_elems_list_array', array_ext.
    count_total_elems_list_array)
ll.add_symbol('map_array_from_sequence', array_ext.map_array_from_sequence)
ll.add_symbol('np_array_from_map_array', array_ext.np_array_from_map_array)


class MapArrayType(types.ArrayCompatible):

    def __init__(self, key_arr_type, value_arr_type):
        self.key_arr_type = key_arr_type
        self.value_arr_type = value_arr_type
        super(MapArrayType, self).__init__(name='MapArrayType({}, {})'.
            format(key_arr_type, value_arr_type))

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def dtype(self):
        return types.DictType(self.key_arr_type.dtype, self.value_arr_type.
            dtype)

    def copy(self):
        return MapArrayType(self.key_arr_type, self.value_arr_type)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


def _get_map_arr_data_type(map_type):
    npa__ntew = StructArrayType((map_type.key_arr_type, map_type.
        value_arr_type), ('key', 'value'))
    return ArrayItemArrayType(npa__ntew)


@register_model(MapArrayType)
class MapArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        cyt__xeoh = _get_map_arr_data_type(fe_type)
        svx__oee = [('data', cyt__xeoh)]
        models.StructModel.__init__(self, dmm, fe_type, svx__oee)


make_attribute_wrapper(MapArrayType, 'data', '_data')


@unbox(MapArrayType)
def unbox_map_array(typ, val, c):
    n_maps = bodo.utils.utils.object_length(c, val)
    qvc__qvp = all(isinstance(kncp__ngrp, types.Array) and kncp__ngrp.dtype in
        (types.int64, types.float64, types.bool_, datetime_date_type) for
        kncp__ngrp in (typ.key_arr_type, typ.value_arr_type))
    if qvc__qvp:
        lqyf__onaln = lir.FunctionType(lir.IntType(64), [lir.IntType(8).
            as_pointer()])
        rarz__afjl = cgutils.get_or_insert_function(c.builder.module,
            lqyf__onaln, name='count_total_elems_list_array')
        uwb__xzqqr = cgutils.pack_array(c.builder, [n_maps, c.builder.call(
            rarz__afjl, [val])])
    else:
        uwb__xzqqr = get_array_elem_counts(c, c.builder, c.context, val, typ)
    cyt__xeoh = _get_map_arr_data_type(typ)
    data_arr = gen_allocate_array(c.context, c.builder, cyt__xeoh,
        uwb__xzqqr, c)
    eehkq__voden = _get_array_item_arr_payload(c.context, c.builder,
        cyt__xeoh, data_arr)
    null_bitmap_ptr = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, eehkq__voden.null_bitmap).data
    offsets_ptr = c.context.make_array(types.Array(offset_type, 1, 'C'))(c.
        context, c.builder, eehkq__voden.offsets).data
    losbb__mox = _get_struct_arr_payload(c.context, c.builder, cyt__xeoh.
        dtype, eehkq__voden.data)
    key_arr = c.builder.extract_value(losbb__mox.data, 0)
    value_arr = c.builder.extract_value(losbb__mox.data, 1)
    sig = types.none(types.Array(types.uint8, 1, 'C'))
    pni__nwlsr, hxfod__kvrvy = c.pyapi.call_jit_code(lambda A: A.fill(255),
        sig, [losbb__mox.null_bitmap])
    if qvc__qvp:
        dpq__dvtja = c.context.make_array(cyt__xeoh.dtype.data[0])(c.
            context, c.builder, key_arr).data
        afik__zrdmp = c.context.make_array(cyt__xeoh.dtype.data[1])(c.
            context, c.builder, value_arr).data
        lqyf__onaln = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(offset_type.bitwidth).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(32), lir.IntType(32)])
        wbjhd__jzvwj = cgutils.get_or_insert_function(c.builder.module,
            lqyf__onaln, name='map_array_from_sequence')
        shi__hswqu = bodo.utils.utils.numba_to_c_type(typ.key_arr_type.dtype)
        azdz__gfdg = bodo.utils.utils.numba_to_c_type(typ.value_arr_type.dtype)
        c.builder.call(wbjhd__jzvwj, [val, c.builder.bitcast(dpq__dvtja,
            lir.IntType(8).as_pointer()), c.builder.bitcast(afik__zrdmp,
            lir.IntType(8).as_pointer()), offsets_ptr, null_bitmap_ptr, lir
            .Constant(lir.IntType(32), shi__hswqu), lir.Constant(lir.
            IntType(32), azdz__gfdg)])
    else:
        _unbox_map_array_generic(typ, val, c, n_maps, key_arr, value_arr,
            offsets_ptr, null_bitmap_ptr)
    xtsk__pkn = c.context.make_helper(c.builder, typ)
    xtsk__pkn.data = data_arr
    muor__rpgco = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(xtsk__pkn._getvalue(), is_error=muor__rpgco)


def _unbox_map_array_generic(typ, val, c, n_maps, key_arr, value_arr,
    offsets_ptr, null_bitmap_ptr):
    from bodo.libs.array_item_arr_ext import _unbox_array_item_array_copy_data
    context = c.context
    builder = c.builder
    tqjxu__kvsw = context.insert_const_string(builder.module, 'pandas')
    tegdo__cykq = c.pyapi.import_module_noblock(tqjxu__kvsw)
    khon__nxbfr = c.pyapi.object_getattr_string(tegdo__cykq, 'NA')
    ufzuf__zskvj = c.context.get_constant(offset_type, 0)
    builder.store(ufzuf__zskvj, offsets_ptr)
    tgl__alt = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with cgutils.for_range(builder, n_maps) as kpfn__eylgb:
        alwk__sefou = kpfn__eylgb.index
        item_ind = builder.load(tgl__alt)
        builder.store(builder.trunc(item_ind, lir.IntType(offset_type.
            bitwidth)), builder.gep(offsets_ptr, [alwk__sefou]))
        qzhyz__wkuo = seq_getitem(builder, context, val, alwk__sefou)
        set_bitmap_bit(builder, null_bitmap_ptr, alwk__sefou, 0)
        qqca__vhoeu = is_na_value(builder, context, qzhyz__wkuo, khon__nxbfr)
        ptkn__ldapd = builder.icmp_unsigned('!=', qqca__vhoeu, lir.Constant
            (qqca__vhoeu.type, 1))
        with builder.if_then(ptkn__ldapd):
            set_bitmap_bit(builder, null_bitmap_ptr, alwk__sefou, 1)
            sxht__zjn = dict_keys(builder, context, qzhyz__wkuo)
            wty__iuwu = dict_values(builder, context, qzhyz__wkuo)
            n_items = bodo.utils.utils.object_length(c, sxht__zjn)
            _unbox_array_item_array_copy_data(typ.key_arr_type, sxht__zjn,
                c, key_arr, item_ind, n_items)
            _unbox_array_item_array_copy_data(typ.value_arr_type, wty__iuwu,
                c, value_arr, item_ind, n_items)
            builder.store(builder.add(item_ind, n_items), tgl__alt)
            c.pyapi.decref(sxht__zjn)
            c.pyapi.decref(wty__iuwu)
        c.pyapi.decref(qzhyz__wkuo)
    builder.store(builder.trunc(builder.load(tgl__alt), lir.IntType(
        offset_type.bitwidth)), builder.gep(offsets_ptr, [n_maps]))
    c.pyapi.decref(tegdo__cykq)
    c.pyapi.decref(khon__nxbfr)


@box(MapArrayType)
def box_map_arr(typ, val, c):
    xtsk__pkn = c.context.make_helper(c.builder, typ, val)
    data_arr = xtsk__pkn.data
    cyt__xeoh = _get_map_arr_data_type(typ)
    eehkq__voden = _get_array_item_arr_payload(c.context, c.builder,
        cyt__xeoh, data_arr)
    null_bitmap_ptr = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, eehkq__voden.null_bitmap).data
    offsets_ptr = c.context.make_array(types.Array(offset_type, 1, 'C'))(c.
        context, c.builder, eehkq__voden.offsets).data
    losbb__mox = _get_struct_arr_payload(c.context, c.builder, cyt__xeoh.
        dtype, eehkq__voden.data)
    key_arr = c.builder.extract_value(losbb__mox.data, 0)
    value_arr = c.builder.extract_value(losbb__mox.data, 1)
    if all(isinstance(kncp__ngrp, types.Array) and kncp__ngrp.dtype in (
        types.int64, types.float64, types.bool_, datetime_date_type) for
        kncp__ngrp in (typ.key_arr_type, typ.value_arr_type)):
        dpq__dvtja = c.context.make_array(cyt__xeoh.dtype.data[0])(c.
            context, c.builder, key_arr).data
        afik__zrdmp = c.context.make_array(cyt__xeoh.dtype.data[1])(c.
            context, c.builder, value_arr).data
        lqyf__onaln = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(offset_type.bitwidth).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32), lir
            .IntType(32)])
        rrfla__hgk = cgutils.get_or_insert_function(c.builder.module,
            lqyf__onaln, name='np_array_from_map_array')
        shi__hswqu = bodo.utils.utils.numba_to_c_type(typ.key_arr_type.dtype)
        azdz__gfdg = bodo.utils.utils.numba_to_c_type(typ.value_arr_type.dtype)
        arr = c.builder.call(rrfla__hgk, [eehkq__voden.n_arrays, c.builder.
            bitcast(dpq__dvtja, lir.IntType(8).as_pointer()), c.builder.
            bitcast(afik__zrdmp, lir.IntType(8).as_pointer()), offsets_ptr,
            null_bitmap_ptr, lir.Constant(lir.IntType(32), shi__hswqu), lir
            .Constant(lir.IntType(32), azdz__gfdg)])
    else:
        arr = _box_map_array_generic(typ, c, eehkq__voden.n_arrays, key_arr,
            value_arr, offsets_ptr, null_bitmap_ptr)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def _box_map_array_generic(typ, c, n_maps, key_arr, value_arr, offsets_ptr,
    null_bitmap_ptr):
    context = c.context
    builder = c.builder
    tqjxu__kvsw = context.insert_const_string(builder.module, 'numpy')
    ubtmp__ffduz = c.pyapi.import_module_noblock(tqjxu__kvsw)
    txqey__pdoyc = c.pyapi.object_getattr_string(ubtmp__ffduz, 'object_')
    cdzbs__yer = c.pyapi.long_from_longlong(n_maps)
    wefqd__vlk = c.pyapi.call_method(ubtmp__ffduz, 'ndarray', (cdzbs__yer,
        txqey__pdoyc))
    gfvgp__xkkk = c.pyapi.object_getattr_string(ubtmp__ffduz, 'nan')
    tcxd__fdbq = c.pyapi.unserialize(c.pyapi.serialize_object(zip))
    tgl__alt = cgutils.alloca_once_value(builder, lir.Constant(lir.IntType(
        64), 0))
    with cgutils.for_range(builder, n_maps) as kpfn__eylgb:
        ipr__wwv = kpfn__eylgb.index
        pyarray_setitem(builder, context, wefqd__vlk, ipr__wwv, gfvgp__xkkk)
        kmu__kdz = get_bitmap_bit(builder, null_bitmap_ptr, ipr__wwv)
        cefpy__dxf = builder.icmp_unsigned('!=', kmu__kdz, lir.Constant(lir
            .IntType(8), 0))
        with builder.if_then(cefpy__dxf):
            n_items = builder.sext(builder.sub(builder.load(builder.gep(
                offsets_ptr, [builder.add(ipr__wwv, lir.Constant(ipr__wwv.
                type, 1))])), builder.load(builder.gep(offsets_ptr, [
                ipr__wwv]))), lir.IntType(64))
            item_ind = builder.load(tgl__alt)
            qzhyz__wkuo = c.pyapi.dict_new()
            kyzy__caskf = lambda data_arr, item_ind, n_items: data_arr[item_ind
                :item_ind + n_items]
            pni__nwlsr, oqb__rvnrm = c.pyapi.call_jit_code(kyzy__caskf, typ
                .key_arr_type(typ.key_arr_type, types.int64, types.int64),
                [key_arr, item_ind, n_items])
            pni__nwlsr, pooeb__vmgv = c.pyapi.call_jit_code(kyzy__caskf,
                typ.value_arr_type(typ.value_arr_type, types.int64, types.
                int64), [value_arr, item_ind, n_items])
            pgh__gzs = c.pyapi.from_native_value(typ.key_arr_type,
                oqb__rvnrm, c.env_manager)
            wcc__yog = c.pyapi.from_native_value(typ.value_arr_type,
                pooeb__vmgv, c.env_manager)
            rxg__cbn = c.pyapi.call_function_objargs(tcxd__fdbq, (pgh__gzs,
                wcc__yog))
            dict_merge_from_seq2(builder, context, qzhyz__wkuo, rxg__cbn)
            builder.store(builder.add(item_ind, n_items), tgl__alt)
            pyarray_setitem(builder, context, wefqd__vlk, ipr__wwv, qzhyz__wkuo
                )
            c.pyapi.decref(rxg__cbn)
            c.pyapi.decref(pgh__gzs)
            c.pyapi.decref(wcc__yog)
            c.pyapi.decref(qzhyz__wkuo)
    c.pyapi.decref(tcxd__fdbq)
    c.pyapi.decref(ubtmp__ffduz)
    c.pyapi.decref(txqey__pdoyc)
    c.pyapi.decref(cdzbs__yer)
    c.pyapi.decref(gfvgp__xkkk)
    return wefqd__vlk


def init_map_arr_codegen(context, builder, sig, args):
    data_arr, = args
    xtsk__pkn = context.make_helper(builder, sig.return_type)
    xtsk__pkn.data = data_arr
    context.nrt.incref(builder, sig.args[0], data_arr)
    return xtsk__pkn._getvalue()


@intrinsic
def init_map_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, ArrayItemArrayType) and isinstance(data_typ
        .dtype, StructArrayType)
    ltdye__xmxb = MapArrayType(data_typ.dtype.data[0], data_typ.dtype.data[1])
    return ltdye__xmxb(data_typ), init_map_arr_codegen


def alias_ext_init_map_arr(lhs_name, args, alias_map, arg_aliases):
    assert len(args) == 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['init_map_arr',
    'bodo.libs.map_arr_ext'] = alias_ext_init_map_arr


@numba.njit
def pre_alloc_map_array(num_maps, nested_counts, struct_typ):
    fxsnn__ustaj = bodo.libs.array_item_arr_ext.pre_alloc_array_item_array(
        num_maps, nested_counts, struct_typ)
    return init_map_arr(fxsnn__ustaj)


def pre_alloc_map_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 3 and not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


(ArrayAnalysis._analyze_op_call_bodo_libs_map_arr_ext_pre_alloc_map_array
    ) = pre_alloc_map_array_equiv


@overload(len, no_unliteral=True)
def overload_map_arr_len(A):
    if isinstance(A, MapArrayType):
        return lambda A: len(A._data)


@overload_attribute(MapArrayType, 'shape')
def overload_map_arr_shape(A):
    return lambda A: (len(A._data),)


@overload_attribute(MapArrayType, 'dtype')
def overload_map_arr_dtype(A):
    return lambda A: np.object_


@overload_attribute(MapArrayType, 'ndim')
def overload_map_arr_ndim(A):
    return lambda A: 1


@overload_attribute(MapArrayType, 'nbytes')
def overload_map_arr_nbytes(A):
    return lambda A: A._data.nbytes


@overload_method(MapArrayType, 'copy')
def overload_map_arr_copy(A):
    return lambda A: init_map_arr(A._data.copy())


@overload(operator.setitem, no_unliteral=True)
def map_arr_setitem(arr, ind, val):
    if not isinstance(arr, MapArrayType):
        return
    diti__kdmvj = arr.key_arr_type, arr.value_arr_type
    if isinstance(ind, types.Integer):

        def map_arr_setitem_impl(arr, ind, val):
            zpgff__rykxe = val.keys()
            jvl__vcwj = bodo.libs.struct_arr_ext.pre_alloc_struct_array(len
                (val), (-1,), diti__kdmvj, ('key', 'value'))
            for pqjmd__zej, bgwj__glyz in enumerate(zpgff__rykxe):
                jvl__vcwj[pqjmd__zej] = bodo.libs.struct_arr_ext.init_struct((
                    bgwj__glyz, val[bgwj__glyz]), ('key', 'value'))
            arr._data[ind] = jvl__vcwj
        return map_arr_setitem_impl
    raise BodoError(
        'operator.setitem with MapArrays is only supported with an integer index.'
        )


@overload(operator.getitem, no_unliteral=True)
def map_arr_getitem(arr, ind):
    if not isinstance(arr, MapArrayType):
        return
    if isinstance(ind, types.Integer):

        def map_arr_getitem_impl(arr, ind):
            if ind < 0:
                ind += len(arr)
            pfb__cvac = dict()
            wldp__dalbc = bodo.libs.array_item_arr_ext.get_offsets(arr._data)
            jvl__vcwj = bodo.libs.array_item_arr_ext.get_data(arr._data)
            lbd__zrcs, rjsh__fwgqb = bodo.libs.struct_arr_ext.get_data(
                jvl__vcwj)
            fph__owmns = wldp__dalbc[ind]
            rsmo__wzie = wldp__dalbc[ind + 1]
            for pqjmd__zej in range(fph__owmns, rsmo__wzie):
                pfb__cvac[lbd__zrcs[pqjmd__zej]] = rjsh__fwgqb[pqjmd__zej]
            return pfb__cvac
        return map_arr_getitem_impl
    raise BodoError(
        'operator.getitem with MapArrays is only supported with an integer index.'
        )
