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
    ruit__dfvc = StructArrayType((map_type.key_arr_type, map_type.
        value_arr_type), ('key', 'value'))
    return ArrayItemArrayType(ruit__dfvc)


@register_model(MapArrayType)
class MapArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        nzk__nvnj = _get_map_arr_data_type(fe_type)
        gzn__buovn = [('data', nzk__nvnj)]
        models.StructModel.__init__(self, dmm, fe_type, gzn__buovn)


make_attribute_wrapper(MapArrayType, 'data', '_data')


@unbox(MapArrayType)
def unbox_map_array(typ, val, c):
    n_maps = bodo.utils.utils.object_length(c, val)
    nvqwl__inlna = all(isinstance(cog__zxi, types.Array) and cog__zxi.dtype in
        (types.int64, types.float64, types.bool_, datetime_date_type) for
        cog__zxi in (typ.key_arr_type, typ.value_arr_type))
    if nvqwl__inlna:
        cjog__pfob = lir.FunctionType(lir.IntType(64), [lir.IntType(8).
            as_pointer()])
        qslh__fyrd = cgutils.get_or_insert_function(c.builder.module,
            cjog__pfob, name='count_total_elems_list_array')
        qgrhu__rjbb = cgutils.pack_array(c.builder, [n_maps, c.builder.call
            (qslh__fyrd, [val])])
    else:
        qgrhu__rjbb = get_array_elem_counts(c, c.builder, c.context, val, typ)
    nzk__nvnj = _get_map_arr_data_type(typ)
    data_arr = gen_allocate_array(c.context, c.builder, nzk__nvnj,
        qgrhu__rjbb, c)
    ynh__lkar = _get_array_item_arr_payload(c.context, c.builder, nzk__nvnj,
        data_arr)
    null_bitmap_ptr = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, ynh__lkar.null_bitmap).data
    offsets_ptr = c.context.make_array(types.Array(offset_type, 1, 'C'))(c.
        context, c.builder, ynh__lkar.offsets).data
    tvm__fgbi = _get_struct_arr_payload(c.context, c.builder, nzk__nvnj.
        dtype, ynh__lkar.data)
    key_arr = c.builder.extract_value(tvm__fgbi.data, 0)
    value_arr = c.builder.extract_value(tvm__fgbi.data, 1)
    sig = types.none(types.Array(types.uint8, 1, 'C'))
    chc__rmpy, fwd__svsvk = c.pyapi.call_jit_code(lambda A: A.fill(255),
        sig, [tvm__fgbi.null_bitmap])
    if nvqwl__inlna:
        wow__zqq = c.context.make_array(nzk__nvnj.dtype.data[0])(c.context,
            c.builder, key_arr).data
        xyp__wsx = c.context.make_array(nzk__nvnj.dtype.data[1])(c.context,
            c.builder, value_arr).data
        cjog__pfob = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(offset_type.bitwidth).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(32), lir.IntType(32)])
        zyx__ndel = cgutils.get_or_insert_function(c.builder.module,
            cjog__pfob, name='map_array_from_sequence')
        hguad__bnsp = bodo.utils.utils.numba_to_c_type(typ.key_arr_type.dtype)
        bnvfy__nzfgi = bodo.utils.utils.numba_to_c_type(typ.value_arr_type.
            dtype)
        c.builder.call(zyx__ndel, [val, c.builder.bitcast(wow__zqq, lir.
            IntType(8).as_pointer()), c.builder.bitcast(xyp__wsx, lir.
            IntType(8).as_pointer()), offsets_ptr, null_bitmap_ptr, lir.
            Constant(lir.IntType(32), hguad__bnsp), lir.Constant(lir.
            IntType(32), bnvfy__nzfgi)])
    else:
        _unbox_map_array_generic(typ, val, c, n_maps, key_arr, value_arr,
            offsets_ptr, null_bitmap_ptr)
    cxc__gmuuo = c.context.make_helper(c.builder, typ)
    cxc__gmuuo.data = data_arr
    jushs__legqk = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(cxc__gmuuo._getvalue(), is_error=jushs__legqk)


def _unbox_map_array_generic(typ, val, c, n_maps, key_arr, value_arr,
    offsets_ptr, null_bitmap_ptr):
    from bodo.libs.array_item_arr_ext import _unbox_array_item_array_copy_data
    context = c.context
    builder = c.builder
    ppylk__tezwt = context.insert_const_string(builder.module, 'pandas')
    epl__bzav = c.pyapi.import_module_noblock(ppylk__tezwt)
    jre__yarae = c.pyapi.object_getattr_string(epl__bzav, 'NA')
    oxit__wbfq = c.context.get_constant(offset_type, 0)
    builder.store(oxit__wbfq, offsets_ptr)
    lnl__xglwf = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with cgutils.for_range(builder, n_maps) as dre__ixjj:
        zwa__ugni = dre__ixjj.index
        item_ind = builder.load(lnl__xglwf)
        builder.store(builder.trunc(item_ind, lir.IntType(offset_type.
            bitwidth)), builder.gep(offsets_ptr, [zwa__ugni]))
        wijw__mlcoe = seq_getitem(builder, context, val, zwa__ugni)
        set_bitmap_bit(builder, null_bitmap_ptr, zwa__ugni, 0)
        hdzg__fcvrs = is_na_value(builder, context, wijw__mlcoe, jre__yarae)
        pbnfj__tkfeu = builder.icmp_unsigned('!=', hdzg__fcvrs, lir.
            Constant(hdzg__fcvrs.type, 1))
        with builder.if_then(pbnfj__tkfeu):
            set_bitmap_bit(builder, null_bitmap_ptr, zwa__ugni, 1)
            gmsn__asy = dict_keys(builder, context, wijw__mlcoe)
            bzyyz__nos = dict_values(builder, context, wijw__mlcoe)
            n_items = bodo.utils.utils.object_length(c, gmsn__asy)
            _unbox_array_item_array_copy_data(typ.key_arr_type, gmsn__asy,
                c, key_arr, item_ind, n_items)
            _unbox_array_item_array_copy_data(typ.value_arr_type,
                bzyyz__nos, c, value_arr, item_ind, n_items)
            builder.store(builder.add(item_ind, n_items), lnl__xglwf)
            c.pyapi.decref(gmsn__asy)
            c.pyapi.decref(bzyyz__nos)
        c.pyapi.decref(wijw__mlcoe)
    builder.store(builder.trunc(builder.load(lnl__xglwf), lir.IntType(
        offset_type.bitwidth)), builder.gep(offsets_ptr, [n_maps]))
    c.pyapi.decref(epl__bzav)
    c.pyapi.decref(jre__yarae)


@box(MapArrayType)
def box_map_arr(typ, val, c):
    cxc__gmuuo = c.context.make_helper(c.builder, typ, val)
    data_arr = cxc__gmuuo.data
    nzk__nvnj = _get_map_arr_data_type(typ)
    ynh__lkar = _get_array_item_arr_payload(c.context, c.builder, nzk__nvnj,
        data_arr)
    null_bitmap_ptr = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, ynh__lkar.null_bitmap).data
    offsets_ptr = c.context.make_array(types.Array(offset_type, 1, 'C'))(c.
        context, c.builder, ynh__lkar.offsets).data
    tvm__fgbi = _get_struct_arr_payload(c.context, c.builder, nzk__nvnj.
        dtype, ynh__lkar.data)
    key_arr = c.builder.extract_value(tvm__fgbi.data, 0)
    value_arr = c.builder.extract_value(tvm__fgbi.data, 1)
    if all(isinstance(cog__zxi, types.Array) and cog__zxi.dtype in (types.
        int64, types.float64, types.bool_, datetime_date_type) for cog__zxi in
        (typ.key_arr_type, typ.value_arr_type)):
        wow__zqq = c.context.make_array(nzk__nvnj.dtype.data[0])(c.context,
            c.builder, key_arr).data
        xyp__wsx = c.context.make_array(nzk__nvnj.dtype.data[1])(c.context,
            c.builder, value_arr).data
        cjog__pfob = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(offset_type.bitwidth).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32), lir
            .IntType(32)])
        rhlw__rlyy = cgutils.get_or_insert_function(c.builder.module,
            cjog__pfob, name='np_array_from_map_array')
        hguad__bnsp = bodo.utils.utils.numba_to_c_type(typ.key_arr_type.dtype)
        bnvfy__nzfgi = bodo.utils.utils.numba_to_c_type(typ.value_arr_type.
            dtype)
        arr = c.builder.call(rhlw__rlyy, [ynh__lkar.n_arrays, c.builder.
            bitcast(wow__zqq, lir.IntType(8).as_pointer()), c.builder.
            bitcast(xyp__wsx, lir.IntType(8).as_pointer()), offsets_ptr,
            null_bitmap_ptr, lir.Constant(lir.IntType(32), hguad__bnsp),
            lir.Constant(lir.IntType(32), bnvfy__nzfgi)])
    else:
        arr = _box_map_array_generic(typ, c, ynh__lkar.n_arrays, key_arr,
            value_arr, offsets_ptr, null_bitmap_ptr)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def _box_map_array_generic(typ, c, n_maps, key_arr, value_arr, offsets_ptr,
    null_bitmap_ptr):
    context = c.context
    builder = c.builder
    ppylk__tezwt = context.insert_const_string(builder.module, 'numpy')
    dba__pmh = c.pyapi.import_module_noblock(ppylk__tezwt)
    sbmg__evorj = c.pyapi.object_getattr_string(dba__pmh, 'object_')
    czigw__xfkl = c.pyapi.long_from_longlong(n_maps)
    ukynm__vjye = c.pyapi.call_method(dba__pmh, 'ndarray', (czigw__xfkl,
        sbmg__evorj))
    xms__tgsm = c.pyapi.object_getattr_string(dba__pmh, 'nan')
    hyvhr__oqbqw = c.pyapi.unserialize(c.pyapi.serialize_object(zip))
    lnl__xglwf = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(64), 0))
    with cgutils.for_range(builder, n_maps) as dre__ixjj:
        sbxh__pys = dre__ixjj.index
        pyarray_setitem(builder, context, ukynm__vjye, sbxh__pys, xms__tgsm)
        nof__wlf = get_bitmap_bit(builder, null_bitmap_ptr, sbxh__pys)
        gpv__yuyh = builder.icmp_unsigned('!=', nof__wlf, lir.Constant(lir.
            IntType(8), 0))
        with builder.if_then(gpv__yuyh):
            n_items = builder.sext(builder.sub(builder.load(builder.gep(
                offsets_ptr, [builder.add(sbxh__pys, lir.Constant(sbxh__pys
                .type, 1))])), builder.load(builder.gep(offsets_ptr, [
                sbxh__pys]))), lir.IntType(64))
            item_ind = builder.load(lnl__xglwf)
            wijw__mlcoe = c.pyapi.dict_new()
            fuql__zdv = lambda data_arr, item_ind, n_items: data_arr[item_ind
                :item_ind + n_items]
            chc__rmpy, yhmfe__ezee = c.pyapi.call_jit_code(fuql__zdv, typ.
                key_arr_type(typ.key_arr_type, types.int64, types.int64), [
                key_arr, item_ind, n_items])
            chc__rmpy, rhju__muyfc = c.pyapi.call_jit_code(fuql__zdv, typ.
                value_arr_type(typ.value_arr_type, types.int64, types.int64
                ), [value_arr, item_ind, n_items])
            gvf__hfhfg = c.pyapi.from_native_value(typ.key_arr_type,
                yhmfe__ezee, c.env_manager)
            wqk__aqj = c.pyapi.from_native_value(typ.value_arr_type,
                rhju__muyfc, c.env_manager)
            qwzji__ovein = c.pyapi.call_function_objargs(hyvhr__oqbqw, (
                gvf__hfhfg, wqk__aqj))
            dict_merge_from_seq2(builder, context, wijw__mlcoe, qwzji__ovein)
            builder.store(builder.add(item_ind, n_items), lnl__xglwf)
            pyarray_setitem(builder, context, ukynm__vjye, sbxh__pys,
                wijw__mlcoe)
            c.pyapi.decref(qwzji__ovein)
            c.pyapi.decref(gvf__hfhfg)
            c.pyapi.decref(wqk__aqj)
            c.pyapi.decref(wijw__mlcoe)
    c.pyapi.decref(hyvhr__oqbqw)
    c.pyapi.decref(dba__pmh)
    c.pyapi.decref(sbmg__evorj)
    c.pyapi.decref(czigw__xfkl)
    c.pyapi.decref(xms__tgsm)
    return ukynm__vjye


def init_map_arr_codegen(context, builder, sig, args):
    data_arr, = args
    cxc__gmuuo = context.make_helper(builder, sig.return_type)
    cxc__gmuuo.data = data_arr
    context.nrt.incref(builder, sig.args[0], data_arr)
    return cxc__gmuuo._getvalue()


@intrinsic
def init_map_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, ArrayItemArrayType) and isinstance(data_typ
        .dtype, StructArrayType)
    qpo__eksc = MapArrayType(data_typ.dtype.data[0], data_typ.dtype.data[1])
    return qpo__eksc(data_typ), init_map_arr_codegen


def alias_ext_init_map_arr(lhs_name, args, alias_map, arg_aliases):
    assert len(args) == 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['init_map_arr',
    'bodo.libs.map_arr_ext'] = alias_ext_init_map_arr


@numba.njit
def pre_alloc_map_array(num_maps, nested_counts, struct_typ):
    wclt__giny = bodo.libs.array_item_arr_ext.pre_alloc_array_item_array(
        num_maps, nested_counts, struct_typ)
    return init_map_arr(wclt__giny)


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
    wpii__addvb = arr.key_arr_type, arr.value_arr_type
    if isinstance(ind, types.Integer):

        def map_arr_setitem_impl(arr, ind, val):
            hpcin__naaf = val.keys()
            utzmj__cga = bodo.libs.struct_arr_ext.pre_alloc_struct_array(len
                (val), (-1,), wpii__addvb, ('key', 'value'))
            for uuz__fhnx, uqxxi__wkpw in enumerate(hpcin__naaf):
                utzmj__cga[uuz__fhnx] = bodo.libs.struct_arr_ext.init_struct((
                    uqxxi__wkpw, val[uqxxi__wkpw]), ('key', 'value'))
            arr._data[ind] = utzmj__cga
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
            gija__ipdt = dict()
            mbog__pnak = bodo.libs.array_item_arr_ext.get_offsets(arr._data)
            utzmj__cga = bodo.libs.array_item_arr_ext.get_data(arr._data)
            azx__yfdd, ugmma__uioby = bodo.libs.struct_arr_ext.get_data(
                utzmj__cga)
            ubf__oqob = mbog__pnak[ind]
            jcnz__auyg = mbog__pnak[ind + 1]
            for uuz__fhnx in range(ubf__oqob, jcnz__auyg):
                gija__ipdt[azx__yfdd[uuz__fhnx]] = ugmma__uioby[uuz__fhnx]
            return gija__ipdt
        return map_arr_getitem_impl
    raise BodoError(
        'operator.getitem with MapArrays is only supported with an integer index.'
        )
