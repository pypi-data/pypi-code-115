"""Nullable boolean array that stores data in Numpy format (1 byte per value)
but nulls are stored in bit arrays (1 bit per value) similar to Arrow's nulls.
Pandas converts boolean array to object when NAs are introduced.
"""
import operator
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import impl_ret_borrowed, lower_constant
from numba.core.typing.templates import AbstractTemplate, infer_global
from numba.extending import NativeValue, box, intrinsic, lower_builtin, lower_cast, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_model, type_callable, typeof_impl, unbox
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
from bodo.libs import hstr_ext
from bodo.libs.str_arr_ext import string_array_type
from bodo.utils.typing import is_list_like_index_type
ll.add_symbol('is_bool_array', hstr_ext.is_bool_array)
ll.add_symbol('is_pd_boolean_array', hstr_ext.is_pd_boolean_array)
ll.add_symbol('unbox_bool_array_obj', hstr_ext.unbox_bool_array_obj)
from bodo.utils.indexing import array_getitem_bool_index, array_getitem_int_index, array_getitem_slice_index, array_setitem_bool_index, array_setitem_int_index, array_setitem_slice_index
from bodo.utils.typing import BodoError, is_iterable_type, is_overload_false, is_overload_true, parse_dtype, raise_bodo_error


class BooleanArrayType(types.ArrayCompatible):

    def __init__(self):
        super(BooleanArrayType, self).__init__(name='BooleanArrayType()')

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def dtype(self):
        return types.bool_

    def copy(self):
        return BooleanArrayType()


boolean_array = BooleanArrayType()


@typeof_impl.register(pd.arrays.BooleanArray)
def typeof_boolean_array(val, c):
    return boolean_array


data_type = types.Array(types.bool_, 1, 'C')
nulls_type = types.Array(types.uint8, 1, 'C')


@register_model(BooleanArrayType)
class BooleanArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        dvvyc__rnw = [('data', data_type), ('null_bitmap', nulls_type)]
        models.StructModel.__init__(self, dmm, fe_type, dvvyc__rnw)


make_attribute_wrapper(BooleanArrayType, 'data', '_data')
make_attribute_wrapper(BooleanArrayType, 'null_bitmap', '_null_bitmap')


class BooleanDtype(types.Number):

    def __init__(self):
        self.dtype = types.bool_
        super(BooleanDtype, self).__init__('BooleanDtype')


boolean_dtype = BooleanDtype()
register_model(BooleanDtype)(models.OpaqueModel)


@box(BooleanDtype)
def box_boolean_dtype(typ, val, c):
    fkp__nozm = c.context.insert_const_string(c.builder.module, 'pandas')
    hxixm__lbe = c.pyapi.import_module_noblock(fkp__nozm)
    laoz__qqc = c.pyapi.call_method(hxixm__lbe, 'BooleanDtype', ())
    c.pyapi.decref(hxixm__lbe)
    return laoz__qqc


@unbox(BooleanDtype)
def unbox_boolean_dtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


typeof_impl.register(pd.BooleanDtype)(lambda a, b: boolean_dtype)
type_callable(pd.BooleanDtype)(lambda c: lambda : boolean_dtype)
lower_builtin(pd.BooleanDtype)(lambda c, b, s, a: c.get_dummy_value())


@numba.njit
def gen_full_bitmap(n):
    vms__wbeod = n + 7 >> 3
    return np.full(vms__wbeod, 255, np.uint8)


def call_func_in_unbox(func, args, arg_typs, c):
    mbabi__bkumx = c.context.typing_context.resolve_value_type(func)
    wzt__kedpw = mbabi__bkumx.get_call_type(c.context.typing_context,
        arg_typs, {})
    qhqd__ebrs = c.context.get_function(mbabi__bkumx, wzt__kedpw)
    oumf__henns = c.context.call_conv.get_function_type(wzt__kedpw.
        return_type, wzt__kedpw.args)
    gcowu__vge = c.builder.module
    kzxm__pogbp = lir.Function(gcowu__vge, oumf__henns, name=gcowu__vge.
        get_unique_name('.func_conv'))
    kzxm__pogbp.linkage = 'internal'
    tkag__tvq = lir.IRBuilder(kzxm__pogbp.append_basic_block())
    crznq__teps = c.context.call_conv.decode_arguments(tkag__tvq,
        wzt__kedpw.args, kzxm__pogbp)
    hoj__yfxo = qhqd__ebrs(tkag__tvq, crznq__teps)
    c.context.call_conv.return_value(tkag__tvq, hoj__yfxo)
    ahwkv__izext, qyg__oxu = c.context.call_conv.call_function(c.builder,
        kzxm__pogbp, wzt__kedpw.return_type, wzt__kedpw.args, args)
    return qyg__oxu


@unbox(BooleanArrayType)
def unbox_bool_array(typ, obj, c):
    zhm__ywk = c.pyapi.call_method(obj, '__len__', ())
    n = c.pyapi.long_as_longlong(zhm__ywk)
    c.pyapi.decref(zhm__ywk)
    oumf__henns = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
        as_pointer()])
    zfame__oyeh = cgutils.get_or_insert_function(c.builder.module,
        oumf__henns, name='is_bool_array')
    oumf__henns = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
        as_pointer()])
    kzxm__pogbp = cgutils.get_or_insert_function(c.builder.module,
        oumf__henns, name='is_pd_boolean_array')
    jkbu__inft = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    vstqm__nqjji = c.builder.call(kzxm__pogbp, [obj])
    mfg__jyv = c.builder.icmp_unsigned('!=', vstqm__nqjji, vstqm__nqjji.type(0)
        )
    with c.builder.if_else(mfg__jyv) as (xjwbu__yfjx, ceun__vvkg):
        with xjwbu__yfjx:
            har__mhrl = c.pyapi.object_getattr_string(obj, '_data')
            jkbu__inft.data = c.pyapi.to_native_value(types.Array(types.
                bool_, 1, 'C'), har__mhrl).value
            bbx__ebwa = c.pyapi.object_getattr_string(obj, '_mask')
            sqvng__qlsc = c.pyapi.to_native_value(types.Array(types.bool_, 
                1, 'C'), bbx__ebwa).value
            vms__wbeod = c.builder.udiv(c.builder.add(n, lir.Constant(lir.
                IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
            uxv__ntnu = c.context.make_array(types.Array(types.bool_, 1, 'C'))(
                c.context, c.builder, sqvng__qlsc)
            npt__zkqmj = bodo.utils.utils._empty_nd_impl(c.context, c.
                builder, types.Array(types.uint8, 1, 'C'), [vms__wbeod])
            oumf__henns = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
            kzxm__pogbp = cgutils.get_or_insert_function(c.builder.module,
                oumf__henns, name='mask_arr_to_bitmap')
            c.builder.call(kzxm__pogbp, [npt__zkqmj.data, uxv__ntnu.data, n])
            jkbu__inft.null_bitmap = npt__zkqmj._getvalue()
            c.context.nrt.decref(c.builder, types.Array(types.bool_, 1, 'C'
                ), sqvng__qlsc)
            c.pyapi.decref(har__mhrl)
            c.pyapi.decref(bbx__ebwa)
        with ceun__vvkg:
            jwnam__rdsuf = c.builder.call(zfame__oyeh, [obj])
            kcrk__cexqm = c.builder.icmp_unsigned('!=', jwnam__rdsuf,
                jwnam__rdsuf.type(0))
            with c.builder.if_else(kcrk__cexqm) as (zjlt__eov, eli__qvlll):
                with zjlt__eov:
                    jkbu__inft.data = c.pyapi.to_native_value(types.Array(
                        types.bool_, 1, 'C'), obj).value
                    jkbu__inft.null_bitmap = call_func_in_unbox(gen_full_bitmap
                        , (n,), (types.int64,), c)
                with eli__qvlll:
                    jkbu__inft.data = bodo.utils.utils._empty_nd_impl(c.
                        context, c.builder, types.Array(types.bool_, 1, 'C'
                        ), [n])._getvalue()
                    vms__wbeod = c.builder.udiv(c.builder.add(n, lir.
                        Constant(lir.IntType(64), 7)), lir.Constant(lir.
                        IntType(64), 8))
                    jkbu__inft.null_bitmap = bodo.utils.utils._empty_nd_impl(c
                        .context, c.builder, types.Array(types.uint8, 1,
                        'C'), [vms__wbeod])._getvalue()
                    kqk__kdo = c.context.make_array(types.Array(types.bool_,
                        1, 'C'))(c.context, c.builder, jkbu__inft.data).data
                    xmfsd__ddvtu = c.context.make_array(types.Array(types.
                        uint8, 1, 'C'))(c.context, c.builder, jkbu__inft.
                        null_bitmap).data
                    oumf__henns = lir.FunctionType(lir.VoidType(), [lir.
                        IntType(8).as_pointer(), lir.IntType(8).as_pointer(
                        ), lir.IntType(8).as_pointer(), lir.IntType(64)])
                    kzxm__pogbp = cgutils.get_or_insert_function(c.builder.
                        module, oumf__henns, name='unbox_bool_array_obj')
                    c.builder.call(kzxm__pogbp, [obj, kqk__kdo,
                        xmfsd__ddvtu, n])
    return NativeValue(jkbu__inft._getvalue())


@box(BooleanArrayType)
def box_bool_arr(typ, val, c):
    jkbu__inft = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    data = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        jkbu__inft.data, c.env_manager)
    yuj__bkck = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, jkbu__inft.null_bitmap).data
    zhm__ywk = c.pyapi.call_method(data, '__len__', ())
    n = c.pyapi.long_as_longlong(zhm__ywk)
    fkp__nozm = c.context.insert_const_string(c.builder.module, 'numpy')
    yvbm__qmuv = c.pyapi.import_module_noblock(fkp__nozm)
    itz__vcs = c.pyapi.object_getattr_string(yvbm__qmuv, 'bool_')
    sqvng__qlsc = c.pyapi.call_method(yvbm__qmuv, 'empty', (zhm__ywk, itz__vcs)
        )
    lzbc__iouu = c.pyapi.object_getattr_string(sqvng__qlsc, 'ctypes')
    nqfnc__hywd = c.pyapi.object_getattr_string(lzbc__iouu, 'data')
    ttx__lzqxt = c.builder.inttoptr(c.pyapi.long_as_longlong(nqfnc__hywd),
        lir.IntType(8).as_pointer())
    with cgutils.for_range(c.builder, n) as fbl__hjvbo:
        erryk__wykq = fbl__hjvbo.index
        hqq__uowx = c.builder.lshr(erryk__wykq, lir.Constant(lir.IntType(64
            ), 3))
        uki__fzkok = c.builder.load(cgutils.gep(c.builder, yuj__bkck,
            hqq__uowx))
        plm__inufc = c.builder.trunc(c.builder.and_(erryk__wykq, lir.
            Constant(lir.IntType(64), 7)), lir.IntType(8))
        val = c.builder.and_(c.builder.lshr(uki__fzkok, plm__inufc), lir.
            Constant(lir.IntType(8), 1))
        val = c.builder.xor(val, lir.Constant(lir.IntType(8), 1))
        yvw__ydpct = cgutils.gep(c.builder, ttx__lzqxt, erryk__wykq)
        c.builder.store(val, yvw__ydpct)
    c.context.nrt.decref(c.builder, types.Array(types.uint8, 1, 'C'),
        jkbu__inft.null_bitmap)
    fkp__nozm = c.context.insert_const_string(c.builder.module, 'pandas')
    hxixm__lbe = c.pyapi.import_module_noblock(fkp__nozm)
    odlp__dnmi = c.pyapi.object_getattr_string(hxixm__lbe, 'arrays')
    laoz__qqc = c.pyapi.call_method(odlp__dnmi, 'BooleanArray', (data,
        sqvng__qlsc))
    c.pyapi.decref(hxixm__lbe)
    c.pyapi.decref(zhm__ywk)
    c.pyapi.decref(yvbm__qmuv)
    c.pyapi.decref(itz__vcs)
    c.pyapi.decref(lzbc__iouu)
    c.pyapi.decref(nqfnc__hywd)
    c.pyapi.decref(odlp__dnmi)
    c.pyapi.decref(data)
    c.pyapi.decref(sqvng__qlsc)
    return laoz__qqc


@lower_constant(BooleanArrayType)
def lower_constant_bool_arr(context, builder, typ, pyval):
    n = len(pyval)
    yiick__xznc = np.empty(n, np.bool_)
    arh__nxof = np.empty(n + 7 >> 3, np.uint8)
    for erryk__wykq, s in enumerate(pyval):
        hcnln__ntmf = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(arh__nxof, erryk__wykq, int(
            not hcnln__ntmf))
        if not hcnln__ntmf:
            yiick__xznc[erryk__wykq] = s
    wcbuv__fllmv = context.get_constant_generic(builder, data_type, yiick__xznc
        )
    wqm__ddjl = context.get_constant_generic(builder, nulls_type, arh__nxof)
    return lir.Constant.literal_struct([wcbuv__fllmv, wqm__ddjl])


def lower_init_bool_array(context, builder, signature, args):
    jjxqh__jaxb, pysro__pxt = args
    jkbu__inft = cgutils.create_struct_proxy(signature.return_type)(context,
        builder)
    jkbu__inft.data = jjxqh__jaxb
    jkbu__inft.null_bitmap = pysro__pxt
    context.nrt.incref(builder, signature.args[0], jjxqh__jaxb)
    context.nrt.incref(builder, signature.args[1], pysro__pxt)
    return jkbu__inft._getvalue()


@intrinsic
def init_bool_array(typingctx, data, null_bitmap=None):
    assert data == types.Array(types.bool_, 1, 'C')
    assert null_bitmap == types.Array(types.uint8, 1, 'C')
    sig = boolean_array(data, null_bitmap)
    return sig, lower_init_bool_array


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_bool_arr_data(A):
    return lambda A: A._data


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_bool_arr_bitmap(A):
    return lambda A: A._null_bitmap


def get_bool_arr_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    kdqm__xgzp = args[0]
    if equiv_set.has_shape(kdqm__xgzp):
        return ArrayAnalysis.AnalyzeResult(shape=kdqm__xgzp, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_libs_bool_arr_ext_get_bool_arr_data = (
    get_bool_arr_data_equiv)


def init_bool_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    kdqm__xgzp = args[0]
    if equiv_set.has_shape(kdqm__xgzp):
        return ArrayAnalysis.AnalyzeResult(shape=kdqm__xgzp, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_libs_bool_arr_ext_init_bool_array = (
    init_bool_array_equiv)


def alias_ext_dummy_func(lhs_name, args, alias_map, arg_aliases):
    assert len(args) >= 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


def alias_ext_init_bool_array(lhs_name, args, alias_map, arg_aliases):
    assert len(args) == 2
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)
    numba.core.ir_utils._add_alias(lhs_name, args[1].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['init_bool_array',
    'bodo.libs.bool_arr_ext'] = alias_ext_init_bool_array
numba.core.ir_utils.alias_func_extensions['get_bool_arr_data',
    'bodo.libs.bool_arr_ext'] = alias_ext_dummy_func
numba.core.ir_utils.alias_func_extensions['get_bool_arr_bitmap',
    'bodo.libs.bool_arr_ext'] = alias_ext_dummy_func


@numba.njit(no_cpython_wrapper=True)
def alloc_bool_array(n):
    yiick__xznc = np.empty(n, dtype=np.bool_)
    zrm__ttatx = np.empty(n + 7 >> 3, dtype=np.uint8)
    return init_bool_array(yiick__xznc, zrm__ttatx)


def alloc_bool_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


ArrayAnalysis._analyze_op_call_bodo_libs_bool_arr_ext_alloc_bool_array = (
    alloc_bool_array_equiv)


@overload(operator.getitem, no_unliteral=True)
def bool_arr_getitem(A, ind):
    if A != boolean_array:
        return
    if isinstance(types.unliteral(ind), types.Integer):
        return lambda A, ind: A._data[ind]
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:

        def impl_bool(A, ind):
            qzuw__qalpj, cvg__mvegs = array_getitem_bool_index(A, ind)
            return init_bool_array(qzuw__qalpj, cvg__mvegs)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            qzuw__qalpj, cvg__mvegs = array_getitem_int_index(A, ind)
            return init_bool_array(qzuw__qalpj, cvg__mvegs)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            qzuw__qalpj, cvg__mvegs = array_getitem_slice_index(A, ind)
            return init_bool_array(qzuw__qalpj, cvg__mvegs)
        return impl_slice
    raise BodoError(
        f'getitem for BooleanArray with indexing type {ind} not supported.')


@overload(operator.setitem, no_unliteral=True)
def bool_arr_setitem(A, idx, val):
    if A != boolean_array:
        return
    if val == types.none or isinstance(val, types.optional):
        return
    psl__tvsty = (
        f"setitem for BooleanArray with indexing type {idx} received an incorrect 'value' type {val}."
        )
    if isinstance(idx, types.Integer):
        if types.unliteral(val) == types.bool_:

            def impl_scalar(A, idx, val):
                A._data[idx] = val
                bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap, idx, 1)
            return impl_scalar
        else:
            raise BodoError(psl__tvsty)
    if not (is_iterable_type(val) and val.dtype == types.bool_ or types.
        unliteral(val) == types.bool_):
        raise BodoError(psl__tvsty)
    if is_list_like_index_type(idx) and isinstance(idx.dtype, types.Integer):

        def impl_arr_ind_mask(A, idx, val):
            array_setitem_int_index(A, idx, val)
        return impl_arr_ind_mask
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:

        def impl_bool_ind_mask(A, idx, val):
            array_setitem_bool_index(A, idx, val)
        return impl_bool_ind_mask
    if isinstance(idx, types.SliceType):

        def impl_slice_mask(A, idx, val):
            array_setitem_slice_index(A, idx, val)
        return impl_slice_mask
    raise BodoError(
        f'setitem for BooleanArray with indexing type {idx} not supported.')


@overload(len, no_unliteral=True)
def overload_bool_arr_len(A):
    if A == boolean_array:
        return lambda A: len(A._data)


@overload_attribute(BooleanArrayType, 'shape')
def overload_bool_arr_shape(A):
    return lambda A: (len(A._data),)


@overload_attribute(BooleanArrayType, 'dtype')
def overload_bool_arr_dtype(A):
    return lambda A: pd.BooleanDtype()


@overload_attribute(BooleanArrayType, 'ndim')
def overload_bool_arr_ndim(A):
    return lambda A: 1


@overload_attribute(BooleanArrayType, 'nbytes')
def bool_arr_nbytes_overload(A):
    return lambda A: A._data.nbytes + A._null_bitmap.nbytes


@overload_method(BooleanArrayType, 'copy', no_unliteral=True)
def overload_bool_arr_copy(A):
    return lambda A: bodo.libs.bool_arr_ext.init_bool_array(bodo.libs.
        bool_arr_ext.get_bool_arr_data(A).copy(), bodo.libs.bool_arr_ext.
        get_bool_arr_bitmap(A).copy())


@overload_method(BooleanArrayType, 'sum', no_unliteral=True, inline='always')
def overload_bool_sum(A):

    def impl(A):
        numba.parfors.parfor.init_prange()
        s = 0
        for erryk__wykq in numba.parfors.parfor.internal_prange(len(A)):
            val = 0
            if not bodo.libs.array_kernels.isna(A, erryk__wykq):
                val = A[erryk__wykq]
            s += val
        return s
    return impl


@overload_method(BooleanArrayType, 'astype', no_unliteral=True)
def overload_bool_arr_astype(A, dtype, copy=True):
    if dtype == types.unicode_type:
        raise_bodo_error(
            "BooleanArray.astype(): 'dtype' when passed as string must be a constant value"
            )
    if dtype == types.bool_:
        if is_overload_false(copy):
            return lambda A, dtype, copy=True: A
        elif is_overload_true(copy):
            return lambda A, dtype, copy=True: A.copy()
        else:

            def impl(A, dtype, copy=True):
                if copy:
                    return A.copy()
                else:
                    return A
            return impl
    nb_dtype = parse_dtype(dtype, 'BooleanArray.astype')
    if isinstance(nb_dtype, types.Float):

        def impl_float(A, dtype, copy=True):
            data = bodo.libs.bool_arr_ext.get_bool_arr_data(A)
            n = len(data)
            jxi__xbef = np.empty(n, nb_dtype)
            for erryk__wykq in numba.parfors.parfor.internal_prange(n):
                jxi__xbef[erryk__wykq] = data[erryk__wykq]
                if bodo.libs.array_kernels.isna(A, erryk__wykq):
                    jxi__xbef[erryk__wykq] = np.nan
            return jxi__xbef
        return impl_float
    return (lambda A, dtype, copy=True: bodo.libs.bool_arr_ext.
        get_bool_arr_data(A).astype(nb_dtype))


@overload(str, no_unliteral=True)
def overload_str_bool(val):
    if val == types.bool_:

        def impl(val):
            if val:
                return 'True'
            return 'False'
        return impl


ufunc_aliases = {'equal': 'eq', 'not_equal': 'ne', 'less': 'lt',
    'less_equal': 'le', 'greater': 'gt', 'greater_equal': 'ge'}


def create_op_overload(op, n_inputs):
    kemsc__uhuw = op.__name__
    kemsc__uhuw = ufunc_aliases.get(kemsc__uhuw, kemsc__uhuw)
    if n_inputs == 1:

        def overload_bool_arr_op_nin_1(A):
            if isinstance(A, BooleanArrayType):
                return bodo.libs.int_arr_ext.get_nullable_array_unary_impl(op,
                    A)
        return overload_bool_arr_op_nin_1
    elif n_inputs == 2:

        def overload_bool_arr_op_nin_2(lhs, rhs):
            if lhs == boolean_array or rhs == boolean_array:
                return bodo.libs.int_arr_ext.get_nullable_array_binary_impl(op,
                    lhs, rhs)
        return overload_bool_arr_op_nin_2
    else:
        raise RuntimeError(
            "Don't know how to register ufuncs from ufunc_db with arity > 2")


def _install_np_ufuncs():
    import numba.np.ufunc_db
    for vcu__cgeda in numba.np.ufunc_db.get_ufuncs():
        ltqxj__naszh = create_op_overload(vcu__cgeda, vcu__cgeda.nin)
        overload(vcu__cgeda, no_unliteral=True)(ltqxj__naszh)


_install_np_ufuncs()
skips = [operator.lt, operator.le, operator.eq, operator.ne, operator.gt,
    operator.ge, operator.add, operator.sub, operator.mul, operator.truediv,
    operator.floordiv, operator.pow, operator.mod, operator.or_, operator.and_]


def _install_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesArrayOperator._op_map.keys():
        if op in skips:
            continue
        ltqxj__naszh = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(ltqxj__naszh)


_install_binary_ops()


def _install_inplace_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesInplaceArrayOperator._op_map.keys(
        ):
        ltqxj__naszh = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(ltqxj__naszh)


_install_inplace_binary_ops()


def _install_unary_ops():
    for op in (operator.neg, operator.invert, operator.pos):
        ltqxj__naszh = create_op_overload(op, 1)
        overload(op, no_unliteral=True)(ltqxj__naszh)


_install_unary_ops()


@overload_method(BooleanArrayType, 'unique', no_unliteral=True)
def overload_unique(A):

    def impl_bool_arr(A):
        data = []
        plm__inufc = []
        zgt__yesx = False
        psaq__qorwx = False
        rso__ohx = False
        for erryk__wykq in range(len(A)):
            if bodo.libs.array_kernels.isna(A, erryk__wykq):
                if not zgt__yesx:
                    data.append(False)
                    plm__inufc.append(False)
                    zgt__yesx = True
                continue
            val = A[erryk__wykq]
            if val and not psaq__qorwx:
                data.append(True)
                plm__inufc.append(True)
                psaq__qorwx = True
            if not val and not rso__ohx:
                data.append(False)
                plm__inufc.append(True)
                rso__ohx = True
            if zgt__yesx and psaq__qorwx and rso__ohx:
                break
        qzuw__qalpj = np.array(data)
        n = len(qzuw__qalpj)
        vms__wbeod = 1
        cvg__mvegs = np.empty(vms__wbeod, np.uint8)
        for otw__zbcp in range(n):
            bodo.libs.int_arr_ext.set_bit_to_arr(cvg__mvegs, otw__zbcp,
                plm__inufc[otw__zbcp])
        return init_bool_array(qzuw__qalpj, cvg__mvegs)
    return impl_bool_arr


@overload(operator.getitem, no_unliteral=True)
def bool_arr_ind_getitem(A, ind):
    if ind == boolean_array and (isinstance(A, (types.Array, bodo.libs.
        int_arr_ext.IntegerArrayType)) or isinstance(A, bodo.libs.
        struct_arr_ext.StructArrayType) or isinstance(A, bodo.libs.
        array_item_arr_ext.ArrayItemArrayType) or isinstance(A, bodo.libs.
        map_arr_ext.MapArrayType) or A in (string_array_type, bodo.hiframes
        .split_impl.string_array_split_view_type, boolean_array)):
        return lambda A, ind: A[ind._data]


@lower_cast(types.Array(types.bool_, 1, 'C'), boolean_array)
def cast_np_bool_arr_to_bool_arr(context, builder, fromty, toty, val):
    func = lambda A: bodo.libs.bool_arr_ext.init_bool_array(A, np.full(len(
        A) + 7 >> 3, 255, np.uint8))
    laoz__qqc = context.compile_internal(builder, func, toty(fromty), [val])
    return impl_ret_borrowed(context, builder, toty, laoz__qqc)


@overload(operator.setitem, no_unliteral=True)
def overload_np_array_setitem_bool_arr(A, idx, val):
    if isinstance(A, types.Array) and idx == boolean_array:

        def impl(A, idx, val):
            A[idx._data] = val
        return impl


def create_nullable_logical_op_overload(op):
    qpa__thdvo = op == operator.or_

    def bool_array_impl(val1, val2):
        if not is_valid_boolean_array_logical_op(val1, val2):
            return
        ffx__add = bodo.utils.utils.is_array_typ(val1, False)
        uprti__dnv = bodo.utils.utils.is_array_typ(val2, False)
        pxerg__rhcq = 'val1' if ffx__add else 'val2'
        ckdp__eeosn = 'def impl(val1, val2):\n'
        ckdp__eeosn += f'  n = len({pxerg__rhcq})\n'
        ckdp__eeosn += (
            '  out_arr = bodo.utils.utils.alloc_type(n, bodo.boolean_array, (-1,))\n'
            )
        ckdp__eeosn += '  for i in numba.parfors.parfor.internal_prange(n):\n'
        if ffx__add:
            null1 = 'bodo.libs.array_kernels.isna(val1, i)\n'
            kpsqv__tsz = 'val1[i]'
        else:
            null1 = 'False\n'
            kpsqv__tsz = 'val1'
        if uprti__dnv:
            null2 = 'bodo.libs.array_kernels.isna(val2, i)\n'
            bgl__pwssi = 'val2[i]'
        else:
            null2 = 'False\n'
            bgl__pwssi = 'val2'
        if qpa__thdvo:
            ckdp__eeosn += f"""    result, isna_val = compute_or_body({null1}, {null2}, {kpsqv__tsz}, {bgl__pwssi})
"""
        else:
            ckdp__eeosn += f"""    result, isna_val = compute_and_body({null1}, {null2}, {kpsqv__tsz}, {bgl__pwssi})
"""
        ckdp__eeosn += '    out_arr[i] = result\n'
        ckdp__eeosn += '    if isna_val:\n'
        ckdp__eeosn += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
        ckdp__eeosn += '      continue\n'
        ckdp__eeosn += '  return out_arr\n'
        kbpy__wfnxq = {}
        exec(ckdp__eeosn, {'bodo': bodo, 'numba': numba, 'compute_and_body':
            compute_and_body, 'compute_or_body': compute_or_body}, kbpy__wfnxq)
        impl = kbpy__wfnxq['impl']
        return impl
    return bool_array_impl


def compute_or_body(null1, null2, val1, val2):
    pass


@overload(compute_or_body)
def overload_compute_or_body(null1, null2, val1, val2):

    def impl(null1, null2, val1, val2):
        if null1 and null2:
            return False, True
        elif null1:
            return val2, val2 == False
        elif null2:
            return val1, val1 == False
        else:
            return val1 | val2, False
    return impl


def compute_and_body(null1, null2, val1, val2):
    pass


@overload(compute_and_body)
def overload_compute_and_body(null1, null2, val1, val2):

    def impl(null1, null2, val1, val2):
        if null1 and null2:
            return False, True
        elif null1:
            return val2, val2 == True
        elif null2:
            return val1, val1 == True
        else:
            return val1 & val2, False
    return impl


def create_boolean_array_logical_lower_impl(op):

    def logical_lower_impl(context, builder, sig, args):
        impl = create_nullable_logical_op_overload(op)(*sig.args)
        return context.compile_internal(builder, impl, sig, args)
    return logical_lower_impl


class BooleanArrayLogicalOperatorTemplate(AbstractTemplate):

    def generic(self, args, kws):
        assert len(args) == 2
        assert not kws
        if not is_valid_boolean_array_logical_op(args[0], args[1]):
            return
        tygs__tzfg = boolean_array
        return tygs__tzfg(*args)


def is_valid_boolean_array_logical_op(typ1, typ2):
    crf__paich = (typ1 == bodo.boolean_array or typ2 == bodo.boolean_array
        ) and (bodo.utils.utils.is_array_typ(typ1, False) and typ1.dtype ==
        types.bool_ or typ1 == types.bool_) and (bodo.utils.utils.
        is_array_typ(typ2, False) and typ2.dtype == types.bool_ or typ2 ==
        types.bool_)
    return crf__paich


def _install_nullable_logical_lowering():
    for op in (operator.and_, operator.or_):
        auy__yoand = create_boolean_array_logical_lower_impl(op)
        infer_global(op)(BooleanArrayLogicalOperatorTemplate)
        for typ1, typ2 in [(boolean_array, boolean_array), (boolean_array,
            types.bool_), (boolean_array, types.Array(types.bool_, 1, 'C'))]:
            lower_builtin(op, typ1, typ2)(auy__yoand)
            if typ1 != typ2:
                lower_builtin(op, typ2, typ1)(auy__yoand)


_install_nullable_logical_lowering()
