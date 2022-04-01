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
    afpo__wfrzd = StructArrayType((map_type.key_arr_type, map_type.
        value_arr_type), ('key', 'value'))
    return ArrayItemArrayType(afpo__wfrzd)


@register_model(MapArrayType)
class MapArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        hltyu__brqz = _get_map_arr_data_type(fe_type)
        tcdjj__kcjt = [('data', hltyu__brqz)]
        models.StructModel.__init__(self, dmm, fe_type, tcdjj__kcjt)


make_attribute_wrapper(MapArrayType, 'data', '_data')


@unbox(MapArrayType)
def unbox_map_array(typ, val, c):
    n_maps = bodo.utils.utils.object_length(c, val)
    dgj__gxiwx = all(isinstance(ghq__kfbe, types.Array) and ghq__kfbe.dtype in
        (types.int64, types.float64, types.bool_, datetime_date_type) for
        ghq__kfbe in (typ.key_arr_type, typ.value_arr_type))
    if dgj__gxiwx:
        lozw__ixd = lir.FunctionType(lir.IntType(64), [lir.IntType(8).
            as_pointer()])
        veyth__bblw = cgutils.get_or_insert_function(c.builder.module,
            lozw__ixd, name='count_total_elems_list_array')
        npp__xqmr = cgutils.pack_array(c.builder, [n_maps, c.builder.call(
            veyth__bblw, [val])])
    else:
        npp__xqmr = get_array_elem_counts(c, c.builder, c.context, val, typ)
    hltyu__brqz = _get_map_arr_data_type(typ)
    data_arr = gen_allocate_array(c.context, c.builder, hltyu__brqz,
        npp__xqmr, c)
    apyn__mla = _get_array_item_arr_payload(c.context, c.builder,
        hltyu__brqz, data_arr)
    null_bitmap_ptr = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, apyn__mla.null_bitmap).data
    offsets_ptr = c.context.make_array(types.Array(offset_type, 1, 'C'))(c.
        context, c.builder, apyn__mla.offsets).data
    avp__xkley = _get_struct_arr_payload(c.context, c.builder, hltyu__brqz.
        dtype, apyn__mla.data)
    key_arr = c.builder.extract_value(avp__xkley.data, 0)
    value_arr = c.builder.extract_value(avp__xkley.data, 1)
    sig = types.none(types.Array(types.uint8, 1, 'C'))
    mcw__okfua, ixzoh__wjwax = c.pyapi.call_jit_code(lambda A: A.fill(255),
        sig, [avp__xkley.null_bitmap])
    if dgj__gxiwx:
        mmubu__qbaj = c.context.make_array(hltyu__brqz.dtype.data[0])(c.
            context, c.builder, key_arr).data
        uku__tjlyv = c.context.make_array(hltyu__brqz.dtype.data[1])(c.
            context, c.builder, value_arr).data
        lozw__ixd = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(offset_type.bitwidth).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(32), lir.IntType(32)])
        ixmyj__jssk = cgutils.get_or_insert_function(c.builder.module,
            lozw__ixd, name='map_array_from_sequence')
        nzntf__bon = bodo.utils.utils.numba_to_c_type(typ.key_arr_type.dtype)
        tia__zvr = bodo.utils.utils.numba_to_c_type(typ.value_arr_type.dtype)
        c.builder.call(ixmyj__jssk, [val, c.builder.bitcast(mmubu__qbaj,
            lir.IntType(8).as_pointer()), c.builder.bitcast(uku__tjlyv, lir
            .IntType(8).as_pointer()), offsets_ptr, null_bitmap_ptr, lir.
            Constant(lir.IntType(32), nzntf__bon), lir.Constant(lir.IntType
            (32), tia__zvr)])
    else:
        _unbox_map_array_generic(typ, val, c, n_maps, key_arr, value_arr,
            offsets_ptr, null_bitmap_ptr)
    kvoft__dov = c.context.make_helper(c.builder, typ)
    kvoft__dov.data = data_arr
    fzzh__isx = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(kvoft__dov._getvalue(), is_error=fzzh__isx)


def _unbox_map_array_generic(typ, val, c, n_maps, key_arr, value_arr,
    offsets_ptr, null_bitmap_ptr):
    from bodo.libs.array_item_arr_ext import _unbox_array_item_array_copy_data
    context = c.context
    builder = c.builder
    oppcx__cmr = context.insert_const_string(builder.module, 'pandas')
    kzha__fdxf = c.pyapi.import_module_noblock(oppcx__cmr)
    skoxv__zyo = c.pyapi.object_getattr_string(kzha__fdxf, 'NA')
    eti__dmv = c.context.get_constant(offset_type, 0)
    builder.store(eti__dmv, offsets_ptr)
    zsa__del = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with cgutils.for_range(builder, n_maps) as wxn__adxys:
        jxs__ujmk = wxn__adxys.index
        item_ind = builder.load(zsa__del)
        builder.store(builder.trunc(item_ind, lir.IntType(offset_type.
            bitwidth)), builder.gep(offsets_ptr, [jxs__ujmk]))
        oqzz__ngy = seq_getitem(builder, context, val, jxs__ujmk)
        set_bitmap_bit(builder, null_bitmap_ptr, jxs__ujmk, 0)
        yhaxk__ykmva = is_na_value(builder, context, oqzz__ngy, skoxv__zyo)
        ysjf__gabzr = builder.icmp_unsigned('!=', yhaxk__ykmva, lir.
            Constant(yhaxk__ykmva.type, 1))
        with builder.if_then(ysjf__gabzr):
            set_bitmap_bit(builder, null_bitmap_ptr, jxs__ujmk, 1)
            mds__uorjd = dict_keys(builder, context, oqzz__ngy)
            kmbmc__ivjdq = dict_values(builder, context, oqzz__ngy)
            n_items = bodo.utils.utils.object_length(c, mds__uorjd)
            _unbox_array_item_array_copy_data(typ.key_arr_type, mds__uorjd,
                c, key_arr, item_ind, n_items)
            _unbox_array_item_array_copy_data(typ.value_arr_type,
                kmbmc__ivjdq, c, value_arr, item_ind, n_items)
            builder.store(builder.add(item_ind, n_items), zsa__del)
            c.pyapi.decref(mds__uorjd)
            c.pyapi.decref(kmbmc__ivjdq)
        c.pyapi.decref(oqzz__ngy)
    builder.store(builder.trunc(builder.load(zsa__del), lir.IntType(
        offset_type.bitwidth)), builder.gep(offsets_ptr, [n_maps]))
    c.pyapi.decref(kzha__fdxf)
    c.pyapi.decref(skoxv__zyo)


@box(MapArrayType)
def box_map_arr(typ, val, c):
    kvoft__dov = c.context.make_helper(c.builder, typ, val)
    data_arr = kvoft__dov.data
    hltyu__brqz = _get_map_arr_data_type(typ)
    apyn__mla = _get_array_item_arr_payload(c.context, c.builder,
        hltyu__brqz, data_arr)
    null_bitmap_ptr = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, apyn__mla.null_bitmap).data
    offsets_ptr = c.context.make_array(types.Array(offset_type, 1, 'C'))(c.
        context, c.builder, apyn__mla.offsets).data
    avp__xkley = _get_struct_arr_payload(c.context, c.builder, hltyu__brqz.
        dtype, apyn__mla.data)
    key_arr = c.builder.extract_value(avp__xkley.data, 0)
    value_arr = c.builder.extract_value(avp__xkley.data, 1)
    if all(isinstance(ghq__kfbe, types.Array) and ghq__kfbe.dtype in (types
        .int64, types.float64, types.bool_, datetime_date_type) for
        ghq__kfbe in (typ.key_arr_type, typ.value_arr_type)):
        mmubu__qbaj = c.context.make_array(hltyu__brqz.dtype.data[0])(c.
            context, c.builder, key_arr).data
        uku__tjlyv = c.context.make_array(hltyu__brqz.dtype.data[1])(c.
            context, c.builder, value_arr).data
        lozw__ixd = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(offset_type.bitwidth).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32), lir
            .IntType(32)])
        kdkm__qrh = cgutils.get_or_insert_function(c.builder.module,
            lozw__ixd, name='np_array_from_map_array')
        nzntf__bon = bodo.utils.utils.numba_to_c_type(typ.key_arr_type.dtype)
        tia__zvr = bodo.utils.utils.numba_to_c_type(typ.value_arr_type.dtype)
        arr = c.builder.call(kdkm__qrh, [apyn__mla.n_arrays, c.builder.
            bitcast(mmubu__qbaj, lir.IntType(8).as_pointer()), c.builder.
            bitcast(uku__tjlyv, lir.IntType(8).as_pointer()), offsets_ptr,
            null_bitmap_ptr, lir.Constant(lir.IntType(32), nzntf__bon), lir
            .Constant(lir.IntType(32), tia__zvr)])
    else:
        arr = _box_map_array_generic(typ, c, apyn__mla.n_arrays, key_arr,
            value_arr, offsets_ptr, null_bitmap_ptr)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def _box_map_array_generic(typ, c, n_maps, key_arr, value_arr, offsets_ptr,
    null_bitmap_ptr):
    context = c.context
    builder = c.builder
    oppcx__cmr = context.insert_const_string(builder.module, 'numpy')
    apd__vtrla = c.pyapi.import_module_noblock(oppcx__cmr)
    xxtrn__otzjw = c.pyapi.object_getattr_string(apd__vtrla, 'object_')
    ixqnb__katn = c.pyapi.long_from_longlong(n_maps)
    qyye__rlr = c.pyapi.call_method(apd__vtrla, 'ndarray', (ixqnb__katn,
        xxtrn__otzjw))
    gmqk__sbr = c.pyapi.object_getattr_string(apd__vtrla, 'nan')
    plnrq__sagh = c.pyapi.unserialize(c.pyapi.serialize_object(zip))
    zsa__del = cgutils.alloca_once_value(builder, lir.Constant(lir.IntType(
        64), 0))
    with cgutils.for_range(builder, n_maps) as wxn__adxys:
        tlvqh__hghi = wxn__adxys.index
        pyarray_setitem(builder, context, qyye__rlr, tlvqh__hghi, gmqk__sbr)
        nkeay__hnvlt = get_bitmap_bit(builder, null_bitmap_ptr, tlvqh__hghi)
        eaonn__uqjyd = builder.icmp_unsigned('!=', nkeay__hnvlt, lir.
            Constant(lir.IntType(8), 0))
        with builder.if_then(eaonn__uqjyd):
            n_items = builder.sext(builder.sub(builder.load(builder.gep(
                offsets_ptr, [builder.add(tlvqh__hghi, lir.Constant(
                tlvqh__hghi.type, 1))])), builder.load(builder.gep(
                offsets_ptr, [tlvqh__hghi]))), lir.IntType(64))
            item_ind = builder.load(zsa__del)
            oqzz__ngy = c.pyapi.dict_new()
            whwmv__aih = lambda data_arr, item_ind, n_items: data_arr[item_ind
                :item_ind + n_items]
            mcw__okfua, tlucy__asuro = c.pyapi.call_jit_code(whwmv__aih,
                typ.key_arr_type(typ.key_arr_type, types.int64, types.int64
                ), [key_arr, item_ind, n_items])
            mcw__okfua, dlamx__rjyr = c.pyapi.call_jit_code(whwmv__aih, typ
                .value_arr_type(typ.value_arr_type, types.int64, types.
                int64), [value_arr, item_ind, n_items])
            rxx__tqo = c.pyapi.from_native_value(typ.key_arr_type,
                tlucy__asuro, c.env_manager)
            xnzlh__vgpzr = c.pyapi.from_native_value(typ.value_arr_type,
                dlamx__rjyr, c.env_manager)
            tqxq__mnkw = c.pyapi.call_function_objargs(plnrq__sagh, (
                rxx__tqo, xnzlh__vgpzr))
            dict_merge_from_seq2(builder, context, oqzz__ngy, tqxq__mnkw)
            builder.store(builder.add(item_ind, n_items), zsa__del)
            pyarray_setitem(builder, context, qyye__rlr, tlvqh__hghi, oqzz__ngy
                )
            c.pyapi.decref(tqxq__mnkw)
            c.pyapi.decref(rxx__tqo)
            c.pyapi.decref(xnzlh__vgpzr)
            c.pyapi.decref(oqzz__ngy)
    c.pyapi.decref(plnrq__sagh)
    c.pyapi.decref(apd__vtrla)
    c.pyapi.decref(xxtrn__otzjw)
    c.pyapi.decref(ixqnb__katn)
    c.pyapi.decref(gmqk__sbr)
    return qyye__rlr


def init_map_arr_codegen(context, builder, sig, args):
    data_arr, = args
    kvoft__dov = context.make_helper(builder, sig.return_type)
    kvoft__dov.data = data_arr
    context.nrt.incref(builder, sig.args[0], data_arr)
    return kvoft__dov._getvalue()


@intrinsic
def init_map_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, ArrayItemArrayType) and isinstance(data_typ
        .dtype, StructArrayType)
    bfzrq__boo = MapArrayType(data_typ.dtype.data[0], data_typ.dtype.data[1])
    return bfzrq__boo(data_typ), init_map_arr_codegen


def alias_ext_init_map_arr(lhs_name, args, alias_map, arg_aliases):
    assert len(args) == 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['init_map_arr',
    'bodo.libs.map_arr_ext'] = alias_ext_init_map_arr


@numba.njit
def pre_alloc_map_array(num_maps, nested_counts, struct_typ):
    helu__tjswz = bodo.libs.array_item_arr_ext.pre_alloc_array_item_array(
        num_maps, nested_counts, struct_typ)
    return init_map_arr(helu__tjswz)


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
    sqz__myvui = arr.key_arr_type, arr.value_arr_type
    if isinstance(ind, types.Integer):

        def map_arr_setitem_impl(arr, ind, val):
            stn__mcg = val.keys()
            euvlc__nkm = bodo.libs.struct_arr_ext.pre_alloc_struct_array(len
                (val), (-1,), sqz__myvui, ('key', 'value'))
            for cnqiq__batbx, cxzc__ubx in enumerate(stn__mcg):
                euvlc__nkm[cnqiq__batbx
                    ] = bodo.libs.struct_arr_ext.init_struct((cxzc__ubx,
                    val[cxzc__ubx]), ('key', 'value'))
            arr._data[ind] = euvlc__nkm
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
            dkn__xirny = dict()
            wqs__phkk = bodo.libs.array_item_arr_ext.get_offsets(arr._data)
            euvlc__nkm = bodo.libs.array_item_arr_ext.get_data(arr._data)
            wszb__dnctn, yxmdr__ureyi = bodo.libs.struct_arr_ext.get_data(
                euvlc__nkm)
            fil__eecl = wqs__phkk[ind]
            huiya__yxpug = wqs__phkk[ind + 1]
            for cnqiq__batbx in range(fil__eecl, huiya__yxpug):
                dkn__xirny[wszb__dnctn[cnqiq__batbx]] = yxmdr__ureyi[
                    cnqiq__batbx]
            return dkn__xirny
        return map_arr_getitem_impl
    raise BodoError(
        'operator.getitem with MapArrays is only supported with an integer index.'
        )
