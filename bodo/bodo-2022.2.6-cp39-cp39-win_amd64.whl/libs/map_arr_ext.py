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
    hki__twn = StructArrayType((map_type.key_arr_type, map_type.
        value_arr_type), ('key', 'value'))
    return ArrayItemArrayType(hki__twn)


@register_model(MapArrayType)
class MapArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        kaqv__lzc = _get_map_arr_data_type(fe_type)
        nqmc__ctm = [('data', kaqv__lzc)]
        models.StructModel.__init__(self, dmm, fe_type, nqmc__ctm)


make_attribute_wrapper(MapArrayType, 'data', '_data')


@unbox(MapArrayType)
def unbox_map_array(typ, val, c):
    n_maps = bodo.utils.utils.object_length(c, val)
    zfuq__ksm = all(isinstance(lrlbh__uqen, types.Array) and lrlbh__uqen.
        dtype in (types.int64, types.float64, types.bool_,
        datetime_date_type) for lrlbh__uqen in (typ.key_arr_type, typ.
        value_arr_type))
    if zfuq__ksm:
        ussxz__xwsdz = lir.FunctionType(lir.IntType(64), [lir.IntType(8).
            as_pointer()])
        ehj__bazd = cgutils.get_or_insert_function(c.builder.module,
            ussxz__xwsdz, name='count_total_elems_list_array')
        iqq__oychn = cgutils.pack_array(c.builder, [n_maps, c.builder.call(
            ehj__bazd, [val])])
    else:
        iqq__oychn = get_array_elem_counts(c, c.builder, c.context, val, typ)
    kaqv__lzc = _get_map_arr_data_type(typ)
    data_arr = gen_allocate_array(c.context, c.builder, kaqv__lzc,
        iqq__oychn, c)
    qrf__jifkl = _get_array_item_arr_payload(c.context, c.builder,
        kaqv__lzc, data_arr)
    null_bitmap_ptr = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, qrf__jifkl.null_bitmap).data
    offsets_ptr = c.context.make_array(types.Array(offset_type, 1, 'C'))(c.
        context, c.builder, qrf__jifkl.offsets).data
    zkko__uslqy = _get_struct_arr_payload(c.context, c.builder, kaqv__lzc.
        dtype, qrf__jifkl.data)
    key_arr = c.builder.extract_value(zkko__uslqy.data, 0)
    value_arr = c.builder.extract_value(zkko__uslqy.data, 1)
    sig = types.none(types.Array(types.uint8, 1, 'C'))
    vxr__vaoq, ojhh__jkukw = c.pyapi.call_jit_code(lambda A: A.fill(255),
        sig, [zkko__uslqy.null_bitmap])
    if zfuq__ksm:
        fmxrx__piefm = c.context.make_array(kaqv__lzc.dtype.data[0])(c.
            context, c.builder, key_arr).data
        tkcg__ablo = c.context.make_array(kaqv__lzc.dtype.data[1])(c.
            context, c.builder, value_arr).data
        ussxz__xwsdz = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(offset_type.bitwidth).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(32), lir.IntType(32)])
        kjujt__mlbg = cgutils.get_or_insert_function(c.builder.module,
            ussxz__xwsdz, name='map_array_from_sequence')
        dapz__nwh = bodo.utils.utils.numba_to_c_type(typ.key_arr_type.dtype)
        axxb__wwuf = bodo.utils.utils.numba_to_c_type(typ.value_arr_type.dtype)
        c.builder.call(kjujt__mlbg, [val, c.builder.bitcast(fmxrx__piefm,
            lir.IntType(8).as_pointer()), c.builder.bitcast(tkcg__ablo, lir
            .IntType(8).as_pointer()), offsets_ptr, null_bitmap_ptr, lir.
            Constant(lir.IntType(32), dapz__nwh), lir.Constant(lir.IntType(
            32), axxb__wwuf)])
    else:
        _unbox_map_array_generic(typ, val, c, n_maps, key_arr, value_arr,
            offsets_ptr, null_bitmap_ptr)
    ghor__ilx = c.context.make_helper(c.builder, typ)
    ghor__ilx.data = data_arr
    csnel__vqt = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(ghor__ilx._getvalue(), is_error=csnel__vqt)


def _unbox_map_array_generic(typ, val, c, n_maps, key_arr, value_arr,
    offsets_ptr, null_bitmap_ptr):
    from bodo.libs.array_item_arr_ext import _unbox_array_item_array_copy_data
    context = c.context
    builder = c.builder
    ppy__nycr = context.insert_const_string(builder.module, 'pandas')
    nigx__uhr = c.pyapi.import_module_noblock(ppy__nycr)
    stii__bczwn = c.pyapi.object_getattr_string(nigx__uhr, 'NA')
    hefo__bqv = c.context.get_constant(offset_type, 0)
    builder.store(hefo__bqv, offsets_ptr)
    xtda__dgj = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with cgutils.for_range(builder, n_maps) as apus__pgxox:
        gduz__yruh = apus__pgxox.index
        item_ind = builder.load(xtda__dgj)
        builder.store(builder.trunc(item_ind, lir.IntType(offset_type.
            bitwidth)), builder.gep(offsets_ptr, [gduz__yruh]))
        ioess__nljr = seq_getitem(builder, context, val, gduz__yruh)
        set_bitmap_bit(builder, null_bitmap_ptr, gduz__yruh, 0)
        eqkd__jrz = is_na_value(builder, context, ioess__nljr, stii__bczwn)
        kpwk__qagn = builder.icmp_unsigned('!=', eqkd__jrz, lir.Constant(
            eqkd__jrz.type, 1))
        with builder.if_then(kpwk__qagn):
            set_bitmap_bit(builder, null_bitmap_ptr, gduz__yruh, 1)
            eqpz__mvujp = dict_keys(builder, context, ioess__nljr)
            ghybi__hrb = dict_values(builder, context, ioess__nljr)
            n_items = bodo.utils.utils.object_length(c, eqpz__mvujp)
            _unbox_array_item_array_copy_data(typ.key_arr_type, eqpz__mvujp,
                c, key_arr, item_ind, n_items)
            _unbox_array_item_array_copy_data(typ.value_arr_type,
                ghybi__hrb, c, value_arr, item_ind, n_items)
            builder.store(builder.add(item_ind, n_items), xtda__dgj)
            c.pyapi.decref(eqpz__mvujp)
            c.pyapi.decref(ghybi__hrb)
        c.pyapi.decref(ioess__nljr)
    builder.store(builder.trunc(builder.load(xtda__dgj), lir.IntType(
        offset_type.bitwidth)), builder.gep(offsets_ptr, [n_maps]))
    c.pyapi.decref(nigx__uhr)
    c.pyapi.decref(stii__bczwn)


@box(MapArrayType)
def box_map_arr(typ, val, c):
    ghor__ilx = c.context.make_helper(c.builder, typ, val)
    data_arr = ghor__ilx.data
    kaqv__lzc = _get_map_arr_data_type(typ)
    qrf__jifkl = _get_array_item_arr_payload(c.context, c.builder,
        kaqv__lzc, data_arr)
    null_bitmap_ptr = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, qrf__jifkl.null_bitmap).data
    offsets_ptr = c.context.make_array(types.Array(offset_type, 1, 'C'))(c.
        context, c.builder, qrf__jifkl.offsets).data
    zkko__uslqy = _get_struct_arr_payload(c.context, c.builder, kaqv__lzc.
        dtype, qrf__jifkl.data)
    key_arr = c.builder.extract_value(zkko__uslqy.data, 0)
    value_arr = c.builder.extract_value(zkko__uslqy.data, 1)
    if all(isinstance(lrlbh__uqen, types.Array) and lrlbh__uqen.dtype in (
        types.int64, types.float64, types.bool_, datetime_date_type) for
        lrlbh__uqen in (typ.key_arr_type, typ.value_arr_type)):
        fmxrx__piefm = c.context.make_array(kaqv__lzc.dtype.data[0])(c.
            context, c.builder, key_arr).data
        tkcg__ablo = c.context.make_array(kaqv__lzc.dtype.data[1])(c.
            context, c.builder, value_arr).data
        ussxz__xwsdz = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(offset_type.bitwidth).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32), lir
            .IntType(32)])
        mohxj__tmnxl = cgutils.get_or_insert_function(c.builder.module,
            ussxz__xwsdz, name='np_array_from_map_array')
        dapz__nwh = bodo.utils.utils.numba_to_c_type(typ.key_arr_type.dtype)
        axxb__wwuf = bodo.utils.utils.numba_to_c_type(typ.value_arr_type.dtype)
        arr = c.builder.call(mohxj__tmnxl, [qrf__jifkl.n_arrays, c.builder.
            bitcast(fmxrx__piefm, lir.IntType(8).as_pointer()), c.builder.
            bitcast(tkcg__ablo, lir.IntType(8).as_pointer()), offsets_ptr,
            null_bitmap_ptr, lir.Constant(lir.IntType(32), dapz__nwh), lir.
            Constant(lir.IntType(32), axxb__wwuf)])
    else:
        arr = _box_map_array_generic(typ, c, qrf__jifkl.n_arrays, key_arr,
            value_arr, offsets_ptr, null_bitmap_ptr)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def _box_map_array_generic(typ, c, n_maps, key_arr, value_arr, offsets_ptr,
    null_bitmap_ptr):
    context = c.context
    builder = c.builder
    ppy__nycr = context.insert_const_string(builder.module, 'numpy')
    viab__shd = c.pyapi.import_module_noblock(ppy__nycr)
    zmhpv__rgyo = c.pyapi.object_getattr_string(viab__shd, 'object_')
    tfs__xxf = c.pyapi.long_from_longlong(n_maps)
    zryt__iicf = c.pyapi.call_method(viab__shd, 'ndarray', (tfs__xxf,
        zmhpv__rgyo))
    osd__rtosw = c.pyapi.object_getattr_string(viab__shd, 'nan')
    cpq__vcs = c.pyapi.unserialize(c.pyapi.serialize_object(zip))
    xtda__dgj = cgutils.alloca_once_value(builder, lir.Constant(lir.IntType
        (64), 0))
    with cgutils.for_range(builder, n_maps) as apus__pgxox:
        mwtb__kfy = apus__pgxox.index
        pyarray_setitem(builder, context, zryt__iicf, mwtb__kfy, osd__rtosw)
        fxg__rki = get_bitmap_bit(builder, null_bitmap_ptr, mwtb__kfy)
        hpzbq__jocy = builder.icmp_unsigned('!=', fxg__rki, lir.Constant(
            lir.IntType(8), 0))
        with builder.if_then(hpzbq__jocy):
            n_items = builder.sext(builder.sub(builder.load(builder.gep(
                offsets_ptr, [builder.add(mwtb__kfy, lir.Constant(mwtb__kfy
                .type, 1))])), builder.load(builder.gep(offsets_ptr, [
                mwtb__kfy]))), lir.IntType(64))
            item_ind = builder.load(xtda__dgj)
            ioess__nljr = c.pyapi.dict_new()
            gtcv__aur = lambda data_arr, item_ind, n_items: data_arr[item_ind
                :item_ind + n_items]
            vxr__vaoq, pomp__nknv = c.pyapi.call_jit_code(gtcv__aur, typ.
                key_arr_type(typ.key_arr_type, types.int64, types.int64), [
                key_arr, item_ind, n_items])
            vxr__vaoq, lgdr__trb = c.pyapi.call_jit_code(gtcv__aur, typ.
                value_arr_type(typ.value_arr_type, types.int64, types.int64
                ), [value_arr, item_ind, n_items])
            oihpc__xbhd = c.pyapi.from_native_value(typ.key_arr_type,
                pomp__nknv, c.env_manager)
            uhz__obgrn = c.pyapi.from_native_value(typ.value_arr_type,
                lgdr__trb, c.env_manager)
            qaeby__jexq = c.pyapi.call_function_objargs(cpq__vcs, (
                oihpc__xbhd, uhz__obgrn))
            dict_merge_from_seq2(builder, context, ioess__nljr, qaeby__jexq)
            builder.store(builder.add(item_ind, n_items), xtda__dgj)
            pyarray_setitem(builder, context, zryt__iicf, mwtb__kfy,
                ioess__nljr)
            c.pyapi.decref(qaeby__jexq)
            c.pyapi.decref(oihpc__xbhd)
            c.pyapi.decref(uhz__obgrn)
            c.pyapi.decref(ioess__nljr)
    c.pyapi.decref(cpq__vcs)
    c.pyapi.decref(viab__shd)
    c.pyapi.decref(zmhpv__rgyo)
    c.pyapi.decref(tfs__xxf)
    c.pyapi.decref(osd__rtosw)
    return zryt__iicf


def init_map_arr_codegen(context, builder, sig, args):
    data_arr, = args
    ghor__ilx = context.make_helper(builder, sig.return_type)
    ghor__ilx.data = data_arr
    context.nrt.incref(builder, sig.args[0], data_arr)
    return ghor__ilx._getvalue()


@intrinsic
def init_map_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, ArrayItemArrayType) and isinstance(data_typ
        .dtype, StructArrayType)
    cnr__knlaf = MapArrayType(data_typ.dtype.data[0], data_typ.dtype.data[1])
    return cnr__knlaf(data_typ), init_map_arr_codegen


def alias_ext_init_map_arr(lhs_name, args, alias_map, arg_aliases):
    assert len(args) == 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['init_map_arr',
    'bodo.libs.map_arr_ext'] = alias_ext_init_map_arr


@numba.njit
def pre_alloc_map_array(num_maps, nested_counts, struct_typ):
    iam__hwazl = bodo.libs.array_item_arr_ext.pre_alloc_array_item_array(
        num_maps, nested_counts, struct_typ)
    return init_map_arr(iam__hwazl)


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
    eoqx__zvk = arr.key_arr_type, arr.value_arr_type
    if isinstance(ind, types.Integer):

        def map_arr_setitem_impl(arr, ind, val):
            atz__kse = val.keys()
            ogmr__zdhyp = bodo.libs.struct_arr_ext.pre_alloc_struct_array(len
                (val), (-1,), eoqx__zvk, ('key', 'value'))
            for bdx__whrw, yauq__eyojh in enumerate(atz__kse):
                ogmr__zdhyp[bdx__whrw] = bodo.libs.struct_arr_ext.init_struct((
                    yauq__eyojh, val[yauq__eyojh]), ('key', 'value'))
            arr._data[ind] = ogmr__zdhyp
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
            fcadu__jalxh = dict()
            xpxc__jbied = bodo.libs.array_item_arr_ext.get_offsets(arr._data)
            ogmr__zdhyp = bodo.libs.array_item_arr_ext.get_data(arr._data)
            eyho__eest, kbpbm__twv = bodo.libs.struct_arr_ext.get_data(
                ogmr__zdhyp)
            ebgwn__kuyp = xpxc__jbied[ind]
            qvbd__hkt = xpxc__jbied[ind + 1]
            for bdx__whrw in range(ebgwn__kuyp, qvbd__hkt):
                fcadu__jalxh[eyho__eest[bdx__whrw]] = kbpbm__twv[bdx__whrw]
            return fcadu__jalxh
        return map_arr_getitem_impl
    raise BodoError(
        'operator.getitem with MapArrays is only supported with an integer index.'
        )
