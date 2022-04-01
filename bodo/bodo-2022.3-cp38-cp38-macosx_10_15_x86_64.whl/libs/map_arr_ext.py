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
    udidb__zrwzz = StructArrayType((map_type.key_arr_type, map_type.
        value_arr_type), ('key', 'value'))
    return ArrayItemArrayType(udidb__zrwzz)


@register_model(MapArrayType)
class MapArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        lwuy__kxaqs = _get_map_arr_data_type(fe_type)
        ueacx__saoz = [('data', lwuy__kxaqs)]
        models.StructModel.__init__(self, dmm, fe_type, ueacx__saoz)


make_attribute_wrapper(MapArrayType, 'data', '_data')


@unbox(MapArrayType)
def unbox_map_array(typ, val, c):
    n_maps = bodo.utils.utils.object_length(c, val)
    vpie__pjbt = all(isinstance(zvke__aqpio, types.Array) and zvke__aqpio.
        dtype in (types.int64, types.float64, types.bool_,
        datetime_date_type) for zvke__aqpio in (typ.key_arr_type, typ.
        value_arr_type))
    if vpie__pjbt:
        tqdbd__lrs = lir.FunctionType(lir.IntType(64), [lir.IntType(8).
            as_pointer()])
        saas__izqwe = cgutils.get_or_insert_function(c.builder.module,
            tqdbd__lrs, name='count_total_elems_list_array')
        vtlen__xljeh = cgutils.pack_array(c.builder, [n_maps, c.builder.
            call(saas__izqwe, [val])])
    else:
        vtlen__xljeh = get_array_elem_counts(c, c.builder, c.context, val, typ)
    lwuy__kxaqs = _get_map_arr_data_type(typ)
    data_arr = gen_allocate_array(c.context, c.builder, lwuy__kxaqs,
        vtlen__xljeh, c)
    tzwaj__tho = _get_array_item_arr_payload(c.context, c.builder,
        lwuy__kxaqs, data_arr)
    null_bitmap_ptr = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, tzwaj__tho.null_bitmap).data
    offsets_ptr = c.context.make_array(types.Array(offset_type, 1, 'C'))(c.
        context, c.builder, tzwaj__tho.offsets).data
    tghc__fbja = _get_struct_arr_payload(c.context, c.builder, lwuy__kxaqs.
        dtype, tzwaj__tho.data)
    key_arr = c.builder.extract_value(tghc__fbja.data, 0)
    value_arr = c.builder.extract_value(tghc__fbja.data, 1)
    sig = types.none(types.Array(types.uint8, 1, 'C'))
    zhqb__mqx, jrsiq__abde = c.pyapi.call_jit_code(lambda A: A.fill(255),
        sig, [tghc__fbja.null_bitmap])
    if vpie__pjbt:
        axrtd__hya = c.context.make_array(lwuy__kxaqs.dtype.data[0])(c.
            context, c.builder, key_arr).data
        fvpsa__szqpr = c.context.make_array(lwuy__kxaqs.dtype.data[1])(c.
            context, c.builder, value_arr).data
        tqdbd__lrs = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(offset_type.bitwidth).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(32), lir.IntType(32)])
        idi__qjiet = cgutils.get_or_insert_function(c.builder.module,
            tqdbd__lrs, name='map_array_from_sequence')
        tknc__yyrap = bodo.utils.utils.numba_to_c_type(typ.key_arr_type.dtype)
        sgel__tehb = bodo.utils.utils.numba_to_c_type(typ.value_arr_type.dtype)
        c.builder.call(idi__qjiet, [val, c.builder.bitcast(axrtd__hya, lir.
            IntType(8).as_pointer()), c.builder.bitcast(fvpsa__szqpr, lir.
            IntType(8).as_pointer()), offsets_ptr, null_bitmap_ptr, lir.
            Constant(lir.IntType(32), tknc__yyrap), lir.Constant(lir.
            IntType(32), sgel__tehb)])
    else:
        _unbox_map_array_generic(typ, val, c, n_maps, key_arr, value_arr,
            offsets_ptr, null_bitmap_ptr)
    ghig__dtpw = c.context.make_helper(c.builder, typ)
    ghig__dtpw.data = data_arr
    bexob__wlhn = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(ghig__dtpw._getvalue(), is_error=bexob__wlhn)


def _unbox_map_array_generic(typ, val, c, n_maps, key_arr, value_arr,
    offsets_ptr, null_bitmap_ptr):
    from bodo.libs.array_item_arr_ext import _unbox_array_item_array_copy_data
    context = c.context
    builder = c.builder
    tjxs__bee = context.insert_const_string(builder.module, 'pandas')
    homf__zkcev = c.pyapi.import_module_noblock(tjxs__bee)
    ndiy__wir = c.pyapi.object_getattr_string(homf__zkcev, 'NA')
    wkl__qigy = c.context.get_constant(offset_type, 0)
    builder.store(wkl__qigy, offsets_ptr)
    vnpq__wdufi = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with cgutils.for_range(builder, n_maps) as bco__bnusk:
        olyen__vputj = bco__bnusk.index
        item_ind = builder.load(vnpq__wdufi)
        builder.store(builder.trunc(item_ind, lir.IntType(offset_type.
            bitwidth)), builder.gep(offsets_ptr, [olyen__vputj]))
        nlzb__xnrps = seq_getitem(builder, context, val, olyen__vputj)
        set_bitmap_bit(builder, null_bitmap_ptr, olyen__vputj, 0)
        mjkju__bomq = is_na_value(builder, context, nlzb__xnrps, ndiy__wir)
        rrve__wuel = builder.icmp_unsigned('!=', mjkju__bomq, lir.Constant(
            mjkju__bomq.type, 1))
        with builder.if_then(rrve__wuel):
            set_bitmap_bit(builder, null_bitmap_ptr, olyen__vputj, 1)
            lxbz__xpm = dict_keys(builder, context, nlzb__xnrps)
            gxe__tif = dict_values(builder, context, nlzb__xnrps)
            n_items = bodo.utils.utils.object_length(c, lxbz__xpm)
            _unbox_array_item_array_copy_data(typ.key_arr_type, lxbz__xpm,
                c, key_arr, item_ind, n_items)
            _unbox_array_item_array_copy_data(typ.value_arr_type, gxe__tif,
                c, value_arr, item_ind, n_items)
            builder.store(builder.add(item_ind, n_items), vnpq__wdufi)
            c.pyapi.decref(lxbz__xpm)
            c.pyapi.decref(gxe__tif)
        c.pyapi.decref(nlzb__xnrps)
    builder.store(builder.trunc(builder.load(vnpq__wdufi), lir.IntType(
        offset_type.bitwidth)), builder.gep(offsets_ptr, [n_maps]))
    c.pyapi.decref(homf__zkcev)
    c.pyapi.decref(ndiy__wir)


@box(MapArrayType)
def box_map_arr(typ, val, c):
    ghig__dtpw = c.context.make_helper(c.builder, typ, val)
    data_arr = ghig__dtpw.data
    lwuy__kxaqs = _get_map_arr_data_type(typ)
    tzwaj__tho = _get_array_item_arr_payload(c.context, c.builder,
        lwuy__kxaqs, data_arr)
    null_bitmap_ptr = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, tzwaj__tho.null_bitmap).data
    offsets_ptr = c.context.make_array(types.Array(offset_type, 1, 'C'))(c.
        context, c.builder, tzwaj__tho.offsets).data
    tghc__fbja = _get_struct_arr_payload(c.context, c.builder, lwuy__kxaqs.
        dtype, tzwaj__tho.data)
    key_arr = c.builder.extract_value(tghc__fbja.data, 0)
    value_arr = c.builder.extract_value(tghc__fbja.data, 1)
    if all(isinstance(zvke__aqpio, types.Array) and zvke__aqpio.dtype in (
        types.int64, types.float64, types.bool_, datetime_date_type) for
        zvke__aqpio in (typ.key_arr_type, typ.value_arr_type)):
        axrtd__hya = c.context.make_array(lwuy__kxaqs.dtype.data[0])(c.
            context, c.builder, key_arr).data
        fvpsa__szqpr = c.context.make_array(lwuy__kxaqs.dtype.data[1])(c.
            context, c.builder, value_arr).data
        tqdbd__lrs = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(offset_type.bitwidth).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32), lir
            .IntType(32)])
        bcu__knrx = cgutils.get_or_insert_function(c.builder.module,
            tqdbd__lrs, name='np_array_from_map_array')
        tknc__yyrap = bodo.utils.utils.numba_to_c_type(typ.key_arr_type.dtype)
        sgel__tehb = bodo.utils.utils.numba_to_c_type(typ.value_arr_type.dtype)
        arr = c.builder.call(bcu__knrx, [tzwaj__tho.n_arrays, c.builder.
            bitcast(axrtd__hya, lir.IntType(8).as_pointer()), c.builder.
            bitcast(fvpsa__szqpr, lir.IntType(8).as_pointer()), offsets_ptr,
            null_bitmap_ptr, lir.Constant(lir.IntType(32), tknc__yyrap),
            lir.Constant(lir.IntType(32), sgel__tehb)])
    else:
        arr = _box_map_array_generic(typ, c, tzwaj__tho.n_arrays, key_arr,
            value_arr, offsets_ptr, null_bitmap_ptr)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def _box_map_array_generic(typ, c, n_maps, key_arr, value_arr, offsets_ptr,
    null_bitmap_ptr):
    context = c.context
    builder = c.builder
    tjxs__bee = context.insert_const_string(builder.module, 'numpy')
    bqx__ywh = c.pyapi.import_module_noblock(tjxs__bee)
    toqz__puco = c.pyapi.object_getattr_string(bqx__ywh, 'object_')
    kwve__sjeq = c.pyapi.long_from_longlong(n_maps)
    lmal__kkwmt = c.pyapi.call_method(bqx__ywh, 'ndarray', (kwve__sjeq,
        toqz__puco))
    cugs__ahgs = c.pyapi.object_getattr_string(bqx__ywh, 'nan')
    snoi__afroo = c.pyapi.unserialize(c.pyapi.serialize_object(zip))
    vnpq__wdufi = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(64), 0))
    with cgutils.for_range(builder, n_maps) as bco__bnusk:
        owemp__kdo = bco__bnusk.index
        pyarray_setitem(builder, context, lmal__kkwmt, owemp__kdo, cugs__ahgs)
        ccx__nydwc = get_bitmap_bit(builder, null_bitmap_ptr, owemp__kdo)
        jsx__evh = builder.icmp_unsigned('!=', ccx__nydwc, lir.Constant(lir
            .IntType(8), 0))
        with builder.if_then(jsx__evh):
            n_items = builder.sext(builder.sub(builder.load(builder.gep(
                offsets_ptr, [builder.add(owemp__kdo, lir.Constant(
                owemp__kdo.type, 1))])), builder.load(builder.gep(
                offsets_ptr, [owemp__kdo]))), lir.IntType(64))
            item_ind = builder.load(vnpq__wdufi)
            nlzb__xnrps = c.pyapi.dict_new()
            bkk__zfk = lambda data_arr, item_ind, n_items: data_arr[item_ind
                :item_ind + n_items]
            zhqb__mqx, rwjdo__kdh = c.pyapi.call_jit_code(bkk__zfk, typ.
                key_arr_type(typ.key_arr_type, types.int64, types.int64), [
                key_arr, item_ind, n_items])
            zhqb__mqx, liw__bau = c.pyapi.call_jit_code(bkk__zfk, typ.
                value_arr_type(typ.value_arr_type, types.int64, types.int64
                ), [value_arr, item_ind, n_items])
            mrrxb__qiuk = c.pyapi.from_native_value(typ.key_arr_type,
                rwjdo__kdh, c.env_manager)
            blfah__wwz = c.pyapi.from_native_value(typ.value_arr_type,
                liw__bau, c.env_manager)
            zpxy__ybjx = c.pyapi.call_function_objargs(snoi__afroo, (
                mrrxb__qiuk, blfah__wwz))
            dict_merge_from_seq2(builder, context, nlzb__xnrps, zpxy__ybjx)
            builder.store(builder.add(item_ind, n_items), vnpq__wdufi)
            pyarray_setitem(builder, context, lmal__kkwmt, owemp__kdo,
                nlzb__xnrps)
            c.pyapi.decref(zpxy__ybjx)
            c.pyapi.decref(mrrxb__qiuk)
            c.pyapi.decref(blfah__wwz)
            c.pyapi.decref(nlzb__xnrps)
    c.pyapi.decref(snoi__afroo)
    c.pyapi.decref(bqx__ywh)
    c.pyapi.decref(toqz__puco)
    c.pyapi.decref(kwve__sjeq)
    c.pyapi.decref(cugs__ahgs)
    return lmal__kkwmt


def init_map_arr_codegen(context, builder, sig, args):
    data_arr, = args
    ghig__dtpw = context.make_helper(builder, sig.return_type)
    ghig__dtpw.data = data_arr
    context.nrt.incref(builder, sig.args[0], data_arr)
    return ghig__dtpw._getvalue()


@intrinsic
def init_map_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, ArrayItemArrayType) and isinstance(data_typ
        .dtype, StructArrayType)
    wmrq__dvq = MapArrayType(data_typ.dtype.data[0], data_typ.dtype.data[1])
    return wmrq__dvq(data_typ), init_map_arr_codegen


def alias_ext_init_map_arr(lhs_name, args, alias_map, arg_aliases):
    assert len(args) == 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['init_map_arr',
    'bodo.libs.map_arr_ext'] = alias_ext_init_map_arr


@numba.njit
def pre_alloc_map_array(num_maps, nested_counts, struct_typ):
    kgv__pkj = bodo.libs.array_item_arr_ext.pre_alloc_array_item_array(num_maps
        , nested_counts, struct_typ)
    return init_map_arr(kgv__pkj)


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
    mkkiu__vbzm = arr.key_arr_type, arr.value_arr_type
    if isinstance(ind, types.Integer):

        def map_arr_setitem_impl(arr, ind, val):
            tuxj__nles = val.keys()
            omt__uttib = bodo.libs.struct_arr_ext.pre_alloc_struct_array(len
                (val), (-1,), mkkiu__vbzm, ('key', 'value'))
            for yxvu__cjjl, tmqu__dpv in enumerate(tuxj__nles):
                omt__uttib[yxvu__cjjl] = bodo.libs.struct_arr_ext.init_struct((
                    tmqu__dpv, val[tmqu__dpv]), ('key', 'value'))
            arr._data[ind] = omt__uttib
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
            kyijg__ywaz = dict()
            kuh__hfrqk = bodo.libs.array_item_arr_ext.get_offsets(arr._data)
            omt__uttib = bodo.libs.array_item_arr_ext.get_data(arr._data)
            okvua__wjfoh, zom__drpmv = bodo.libs.struct_arr_ext.get_data(
                omt__uttib)
            zzypw__hwa = kuh__hfrqk[ind]
            ggt__tar = kuh__hfrqk[ind + 1]
            for yxvu__cjjl in range(zzypw__hwa, ggt__tar):
                kyijg__ywaz[okvua__wjfoh[yxvu__cjjl]] = zom__drpmv[yxvu__cjjl]
            return kyijg__ywaz
        return map_arr_getitem_impl
    raise BodoError(
        'operator.getitem with MapArrays is only supported with an integer index.'
        )
