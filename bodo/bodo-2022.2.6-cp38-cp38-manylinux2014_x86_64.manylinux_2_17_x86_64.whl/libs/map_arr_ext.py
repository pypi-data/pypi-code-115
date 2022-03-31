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
    ojwg__ynkdu = StructArrayType((map_type.key_arr_type, map_type.
        value_arr_type), ('key', 'value'))
    return ArrayItemArrayType(ojwg__ynkdu)


@register_model(MapArrayType)
class MapArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        lnf__xvyw = _get_map_arr_data_type(fe_type)
        alx__roo = [('data', lnf__xvyw)]
        models.StructModel.__init__(self, dmm, fe_type, alx__roo)


make_attribute_wrapper(MapArrayType, 'data', '_data')


@unbox(MapArrayType)
def unbox_map_array(typ, val, c):
    n_maps = bodo.utils.utils.object_length(c, val)
    ljad__lebl = all(isinstance(giqtb__pkevl, types.Array) and giqtb__pkevl
        .dtype in (types.int64, types.float64, types.bool_,
        datetime_date_type) for giqtb__pkevl in (typ.key_arr_type, typ.
        value_arr_type))
    if ljad__lebl:
        wgllk__gaw = lir.FunctionType(lir.IntType(64), [lir.IntType(8).
            as_pointer()])
        dgpx__ncc = cgutils.get_or_insert_function(c.builder.module,
            wgllk__gaw, name='count_total_elems_list_array')
        cpy__uxe = cgutils.pack_array(c.builder, [n_maps, c.builder.call(
            dgpx__ncc, [val])])
    else:
        cpy__uxe = get_array_elem_counts(c, c.builder, c.context, val, typ)
    lnf__xvyw = _get_map_arr_data_type(typ)
    data_arr = gen_allocate_array(c.context, c.builder, lnf__xvyw, cpy__uxe, c)
    ljr__bnp = _get_array_item_arr_payload(c.context, c.builder, lnf__xvyw,
        data_arr)
    null_bitmap_ptr = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, ljr__bnp.null_bitmap).data
    offsets_ptr = c.context.make_array(types.Array(offset_type, 1, 'C'))(c.
        context, c.builder, ljr__bnp.offsets).data
    nqh__swahb = _get_struct_arr_payload(c.context, c.builder, lnf__xvyw.
        dtype, ljr__bnp.data)
    key_arr = c.builder.extract_value(nqh__swahb.data, 0)
    value_arr = c.builder.extract_value(nqh__swahb.data, 1)
    sig = types.none(types.Array(types.uint8, 1, 'C'))
    jxktr__cdyv, xeej__ddfdh = c.pyapi.call_jit_code(lambda A: A.fill(255),
        sig, [nqh__swahb.null_bitmap])
    if ljad__lebl:
        qaq__qxkrz = c.context.make_array(lnf__xvyw.dtype.data[0])(c.
            context, c.builder, key_arr).data
        xvp__tcb = c.context.make_array(lnf__xvyw.dtype.data[1])(c.context,
            c.builder, value_arr).data
        wgllk__gaw = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(offset_type.bitwidth).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(32), lir.IntType(32)])
        axzex__rrbt = cgutils.get_or_insert_function(c.builder.module,
            wgllk__gaw, name='map_array_from_sequence')
        jghmq__jqb = bodo.utils.utils.numba_to_c_type(typ.key_arr_type.dtype)
        acixc__zohoz = bodo.utils.utils.numba_to_c_type(typ.value_arr_type.
            dtype)
        c.builder.call(axzex__rrbt, [val, c.builder.bitcast(qaq__qxkrz, lir
            .IntType(8).as_pointer()), c.builder.bitcast(xvp__tcb, lir.
            IntType(8).as_pointer()), offsets_ptr, null_bitmap_ptr, lir.
            Constant(lir.IntType(32), jghmq__jqb), lir.Constant(lir.IntType
            (32), acixc__zohoz)])
    else:
        _unbox_map_array_generic(typ, val, c, n_maps, key_arr, value_arr,
            offsets_ptr, null_bitmap_ptr)
    nvw__hfwm = c.context.make_helper(c.builder, typ)
    nvw__hfwm.data = data_arr
    ytiw__isisu = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(nvw__hfwm._getvalue(), is_error=ytiw__isisu)


def _unbox_map_array_generic(typ, val, c, n_maps, key_arr, value_arr,
    offsets_ptr, null_bitmap_ptr):
    from bodo.libs.array_item_arr_ext import _unbox_array_item_array_copy_data
    context = c.context
    builder = c.builder
    twdcw__ylj = context.insert_const_string(builder.module, 'pandas')
    kvn__iliy = c.pyapi.import_module_noblock(twdcw__ylj)
    xrgy__hbc = c.pyapi.object_getattr_string(kvn__iliy, 'NA')
    jyfh__vzln = c.context.get_constant(offset_type, 0)
    builder.store(jyfh__vzln, offsets_ptr)
    hzcb__qovnx = cgutils.alloca_once_value(builder, context.get_constant(
        types.int64, 0))
    with cgutils.for_range(builder, n_maps) as cyac__aaovv:
        mbabe__azd = cyac__aaovv.index
        item_ind = builder.load(hzcb__qovnx)
        builder.store(builder.trunc(item_ind, lir.IntType(offset_type.
            bitwidth)), builder.gep(offsets_ptr, [mbabe__azd]))
        mlap__axk = seq_getitem(builder, context, val, mbabe__azd)
        set_bitmap_bit(builder, null_bitmap_ptr, mbabe__azd, 0)
        lpxfp__qln = is_na_value(builder, context, mlap__axk, xrgy__hbc)
        zszgw__hroxi = builder.icmp_unsigned('!=', lpxfp__qln, lir.Constant
            (lpxfp__qln.type, 1))
        with builder.if_then(zszgw__hroxi):
            set_bitmap_bit(builder, null_bitmap_ptr, mbabe__azd, 1)
            adncm__mhrx = dict_keys(builder, context, mlap__axk)
            abbl__voqgo = dict_values(builder, context, mlap__axk)
            n_items = bodo.utils.utils.object_length(c, adncm__mhrx)
            _unbox_array_item_array_copy_data(typ.key_arr_type, adncm__mhrx,
                c, key_arr, item_ind, n_items)
            _unbox_array_item_array_copy_data(typ.value_arr_type,
                abbl__voqgo, c, value_arr, item_ind, n_items)
            builder.store(builder.add(item_ind, n_items), hzcb__qovnx)
            c.pyapi.decref(adncm__mhrx)
            c.pyapi.decref(abbl__voqgo)
        c.pyapi.decref(mlap__axk)
    builder.store(builder.trunc(builder.load(hzcb__qovnx), lir.IntType(
        offset_type.bitwidth)), builder.gep(offsets_ptr, [n_maps]))
    c.pyapi.decref(kvn__iliy)
    c.pyapi.decref(xrgy__hbc)


@box(MapArrayType)
def box_map_arr(typ, val, c):
    nvw__hfwm = c.context.make_helper(c.builder, typ, val)
    data_arr = nvw__hfwm.data
    lnf__xvyw = _get_map_arr_data_type(typ)
    ljr__bnp = _get_array_item_arr_payload(c.context, c.builder, lnf__xvyw,
        data_arr)
    null_bitmap_ptr = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, ljr__bnp.null_bitmap).data
    offsets_ptr = c.context.make_array(types.Array(offset_type, 1, 'C'))(c.
        context, c.builder, ljr__bnp.offsets).data
    nqh__swahb = _get_struct_arr_payload(c.context, c.builder, lnf__xvyw.
        dtype, ljr__bnp.data)
    key_arr = c.builder.extract_value(nqh__swahb.data, 0)
    value_arr = c.builder.extract_value(nqh__swahb.data, 1)
    if all(isinstance(giqtb__pkevl, types.Array) and giqtb__pkevl.dtype in
        (types.int64, types.float64, types.bool_, datetime_date_type) for
        giqtb__pkevl in (typ.key_arr_type, typ.value_arr_type)):
        qaq__qxkrz = c.context.make_array(lnf__xvyw.dtype.data[0])(c.
            context, c.builder, key_arr).data
        xvp__tcb = c.context.make_array(lnf__xvyw.dtype.data[1])(c.context,
            c.builder, value_arr).data
        wgllk__gaw = lir.FunctionType(c.context.get_argument_type(types.
            pyobject), [lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(offset_type.bitwidth).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32), lir
            .IntType(32)])
        atagu__qqsl = cgutils.get_or_insert_function(c.builder.module,
            wgllk__gaw, name='np_array_from_map_array')
        jghmq__jqb = bodo.utils.utils.numba_to_c_type(typ.key_arr_type.dtype)
        acixc__zohoz = bodo.utils.utils.numba_to_c_type(typ.value_arr_type.
            dtype)
        arr = c.builder.call(atagu__qqsl, [ljr__bnp.n_arrays, c.builder.
            bitcast(qaq__qxkrz, lir.IntType(8).as_pointer()), c.builder.
            bitcast(xvp__tcb, lir.IntType(8).as_pointer()), offsets_ptr,
            null_bitmap_ptr, lir.Constant(lir.IntType(32), jghmq__jqb), lir
            .Constant(lir.IntType(32), acixc__zohoz)])
    else:
        arr = _box_map_array_generic(typ, c, ljr__bnp.n_arrays, key_arr,
            value_arr, offsets_ptr, null_bitmap_ptr)
    c.context.nrt.decref(c.builder, typ, val)
    return arr


def _box_map_array_generic(typ, c, n_maps, key_arr, value_arr, offsets_ptr,
    null_bitmap_ptr):
    context = c.context
    builder = c.builder
    twdcw__ylj = context.insert_const_string(builder.module, 'numpy')
    gtrt__hflz = c.pyapi.import_module_noblock(twdcw__ylj)
    wxezf__tud = c.pyapi.object_getattr_string(gtrt__hflz, 'object_')
    fnhtf__vap = c.pyapi.long_from_longlong(n_maps)
    hmh__uiur = c.pyapi.call_method(gtrt__hflz, 'ndarray', (fnhtf__vap,
        wxezf__tud))
    ahl__evo = c.pyapi.object_getattr_string(gtrt__hflz, 'nan')
    iivlw__cxfz = c.pyapi.unserialize(c.pyapi.serialize_object(zip))
    hzcb__qovnx = cgutils.alloca_once_value(builder, lir.Constant(lir.
        IntType(64), 0))
    with cgutils.for_range(builder, n_maps) as cyac__aaovv:
        mwo__ihzs = cyac__aaovv.index
        pyarray_setitem(builder, context, hmh__uiur, mwo__ihzs, ahl__evo)
        mwifj__jpe = get_bitmap_bit(builder, null_bitmap_ptr, mwo__ihzs)
        pbjkk__zrhm = builder.icmp_unsigned('!=', mwifj__jpe, lir.Constant(
            lir.IntType(8), 0))
        with builder.if_then(pbjkk__zrhm):
            n_items = builder.sext(builder.sub(builder.load(builder.gep(
                offsets_ptr, [builder.add(mwo__ihzs, lir.Constant(mwo__ihzs
                .type, 1))])), builder.load(builder.gep(offsets_ptr, [
                mwo__ihzs]))), lir.IntType(64))
            item_ind = builder.load(hzcb__qovnx)
            mlap__axk = c.pyapi.dict_new()
            cfo__ypxzf = lambda data_arr, item_ind, n_items: data_arr[item_ind
                :item_ind + n_items]
            jxktr__cdyv, lshoh__virg = c.pyapi.call_jit_code(cfo__ypxzf,
                typ.key_arr_type(typ.key_arr_type, types.int64, types.int64
                ), [key_arr, item_ind, n_items])
            jxktr__cdyv, idrbo__jxohh = c.pyapi.call_jit_code(cfo__ypxzf,
                typ.value_arr_type(typ.value_arr_type, types.int64, types.
                int64), [value_arr, item_ind, n_items])
            gaf__spfmr = c.pyapi.from_native_value(typ.key_arr_type,
                lshoh__virg, c.env_manager)
            shb__kumll = c.pyapi.from_native_value(typ.value_arr_type,
                idrbo__jxohh, c.env_manager)
            kqsvh__tcx = c.pyapi.call_function_objargs(iivlw__cxfz, (
                gaf__spfmr, shb__kumll))
            dict_merge_from_seq2(builder, context, mlap__axk, kqsvh__tcx)
            builder.store(builder.add(item_ind, n_items), hzcb__qovnx)
            pyarray_setitem(builder, context, hmh__uiur, mwo__ihzs, mlap__axk)
            c.pyapi.decref(kqsvh__tcx)
            c.pyapi.decref(gaf__spfmr)
            c.pyapi.decref(shb__kumll)
            c.pyapi.decref(mlap__axk)
    c.pyapi.decref(iivlw__cxfz)
    c.pyapi.decref(gtrt__hflz)
    c.pyapi.decref(wxezf__tud)
    c.pyapi.decref(fnhtf__vap)
    c.pyapi.decref(ahl__evo)
    return hmh__uiur


def init_map_arr_codegen(context, builder, sig, args):
    data_arr, = args
    nvw__hfwm = context.make_helper(builder, sig.return_type)
    nvw__hfwm.data = data_arr
    context.nrt.incref(builder, sig.args[0], data_arr)
    return nvw__hfwm._getvalue()


@intrinsic
def init_map_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, ArrayItemArrayType) and isinstance(data_typ
        .dtype, StructArrayType)
    spdo__faat = MapArrayType(data_typ.dtype.data[0], data_typ.dtype.data[1])
    return spdo__faat(data_typ), init_map_arr_codegen


def alias_ext_init_map_arr(lhs_name, args, alias_map, arg_aliases):
    assert len(args) == 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['init_map_arr',
    'bodo.libs.map_arr_ext'] = alias_ext_init_map_arr


@numba.njit
def pre_alloc_map_array(num_maps, nested_counts, struct_typ):
    icgs__pvbg = bodo.libs.array_item_arr_ext.pre_alloc_array_item_array(
        num_maps, nested_counts, struct_typ)
    return init_map_arr(icgs__pvbg)


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
    mtgt__chgzs = arr.key_arr_type, arr.value_arr_type
    if isinstance(ind, types.Integer):

        def map_arr_setitem_impl(arr, ind, val):
            fgw__wnvu = val.keys()
            bchqz__ynde = bodo.libs.struct_arr_ext.pre_alloc_struct_array(len
                (val), (-1,), mtgt__chgzs, ('key', 'value'))
            for rwqzv__aieiu, nplwj__fwyve in enumerate(fgw__wnvu):
                bchqz__ynde[rwqzv__aieiu
                    ] = bodo.libs.struct_arr_ext.init_struct((nplwj__fwyve,
                    val[nplwj__fwyve]), ('key', 'value'))
            arr._data[ind] = bchqz__ynde
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
            cgs__hcxjg = dict()
            yss__qpp = bodo.libs.array_item_arr_ext.get_offsets(arr._data)
            bchqz__ynde = bodo.libs.array_item_arr_ext.get_data(arr._data)
            bukv__vfrvz, vfy__xlf = bodo.libs.struct_arr_ext.get_data(
                bchqz__ynde)
            cfbin__bhr = yss__qpp[ind]
            qzt__bfv = yss__qpp[ind + 1]
            for rwqzv__aieiu in range(cfbin__bhr, qzt__bfv):
                cgs__hcxjg[bukv__vfrvz[rwqzv__aieiu]] = vfy__xlf[rwqzv__aieiu]
            return cgs__hcxjg
        return map_arr_getitem_impl
    raise BodoError(
        'operator.getitem with MapArrays is only supported with an integer index.'
        )
