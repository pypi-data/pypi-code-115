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
        drxpi__cvsg = [('data', data_type), ('null_bitmap', nulls_type)]
        models.StructModel.__init__(self, dmm, fe_type, drxpi__cvsg)


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
    gqmq__ywvq = c.context.insert_const_string(c.builder.module, 'pandas')
    cfrkj__atnmx = c.pyapi.import_module_noblock(gqmq__ywvq)
    sae__aun = c.pyapi.call_method(cfrkj__atnmx, 'BooleanDtype', ())
    c.pyapi.decref(cfrkj__atnmx)
    return sae__aun


@unbox(BooleanDtype)
def unbox_boolean_dtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


typeof_impl.register(pd.BooleanDtype)(lambda a, b: boolean_dtype)
type_callable(pd.BooleanDtype)(lambda c: lambda : boolean_dtype)
lower_builtin(pd.BooleanDtype)(lambda c, b, s, a: c.get_dummy_value())


@numba.njit
def gen_full_bitmap(n):
    buh__miq = n + 7 >> 3
    return np.full(buh__miq, 255, np.uint8)


def call_func_in_unbox(func, args, arg_typs, c):
    uudcx__eppx = c.context.typing_context.resolve_value_type(func)
    idj__lnexf = uudcx__eppx.get_call_type(c.context.typing_context,
        arg_typs, {})
    fgqxe__iscqt = c.context.get_function(uudcx__eppx, idj__lnexf)
    xzgic__udxfh = c.context.call_conv.get_function_type(idj__lnexf.
        return_type, idj__lnexf.args)
    kwwz__gpwwx = c.builder.module
    pfrv__ivgj = lir.Function(kwwz__gpwwx, xzgic__udxfh, name=kwwz__gpwwx.
        get_unique_name('.func_conv'))
    pfrv__ivgj.linkage = 'internal'
    siis__xtlo = lir.IRBuilder(pfrv__ivgj.append_basic_block())
    evtzp__exkl = c.context.call_conv.decode_arguments(siis__xtlo,
        idj__lnexf.args, pfrv__ivgj)
    soz__xvi = fgqxe__iscqt(siis__xtlo, evtzp__exkl)
    c.context.call_conv.return_value(siis__xtlo, soz__xvi)
    haj__zsyrd, jgqn__atwio = c.context.call_conv.call_function(c.builder,
        pfrv__ivgj, idj__lnexf.return_type, idj__lnexf.args, args)
    return jgqn__atwio


@unbox(BooleanArrayType)
def unbox_bool_array(typ, obj, c):
    tzwx__pvm = c.pyapi.call_method(obj, '__len__', ())
    n = c.pyapi.long_as_longlong(tzwx__pvm)
    c.pyapi.decref(tzwx__pvm)
    xzgic__udxfh = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
        as_pointer()])
    xnr__qlu = cgutils.get_or_insert_function(c.builder.module,
        xzgic__udxfh, name='is_bool_array')
    xzgic__udxfh = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
        as_pointer()])
    pfrv__ivgj = cgutils.get_or_insert_function(c.builder.module,
        xzgic__udxfh, name='is_pd_boolean_array')
    dvgzi__chqd = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    diac__utiv = c.builder.call(pfrv__ivgj, [obj])
    ujd__pmi = c.builder.icmp_unsigned('!=', diac__utiv, diac__utiv.type(0))
    with c.builder.if_else(ujd__pmi) as (amivh__hen, bkx__jyy):
        with amivh__hen:
            gfd__lpq = c.pyapi.object_getattr_string(obj, '_data')
            dvgzi__chqd.data = c.pyapi.to_native_value(types.Array(types.
                bool_, 1, 'C'), gfd__lpq).value
            rjxnm__qxr = c.pyapi.object_getattr_string(obj, '_mask')
            jjpv__zzfx = c.pyapi.to_native_value(types.Array(types.bool_, 1,
                'C'), rjxnm__qxr).value
            buh__miq = c.builder.udiv(c.builder.add(n, lir.Constant(lir.
                IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
            zcum__mzq = c.context.make_array(types.Array(types.bool_, 1, 'C'))(
                c.context, c.builder, jjpv__zzfx)
            zupq__ibb = bodo.utils.utils._empty_nd_impl(c.context, c.
                builder, types.Array(types.uint8, 1, 'C'), [buh__miq])
            xzgic__udxfh = lir.FunctionType(lir.VoidType(), [lir.IntType(8)
                .as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
            pfrv__ivgj = cgutils.get_or_insert_function(c.builder.module,
                xzgic__udxfh, name='mask_arr_to_bitmap')
            c.builder.call(pfrv__ivgj, [zupq__ibb.data, zcum__mzq.data, n])
            dvgzi__chqd.null_bitmap = zupq__ibb._getvalue()
            c.context.nrt.decref(c.builder, types.Array(types.bool_, 1, 'C'
                ), jjpv__zzfx)
            c.pyapi.decref(gfd__lpq)
            c.pyapi.decref(rjxnm__qxr)
        with bkx__jyy:
            xomgn__sjpd = c.builder.call(xnr__qlu, [obj])
            jon__jixym = c.builder.icmp_unsigned('!=', xomgn__sjpd,
                xomgn__sjpd.type(0))
            with c.builder.if_else(jon__jixym) as (qxaua__akb, bud__ufat):
                with qxaua__akb:
                    dvgzi__chqd.data = c.pyapi.to_native_value(types.Array(
                        types.bool_, 1, 'C'), obj).value
                    dvgzi__chqd.null_bitmap = call_func_in_unbox(
                        gen_full_bitmap, (n,), (types.int64,), c)
                with bud__ufat:
                    dvgzi__chqd.data = bodo.utils.utils._empty_nd_impl(c.
                        context, c.builder, types.Array(types.bool_, 1, 'C'
                        ), [n])._getvalue()
                    buh__miq = c.builder.udiv(c.builder.add(n, lir.Constant
                        (lir.IntType(64), 7)), lir.Constant(lir.IntType(64), 8)
                        )
                    dvgzi__chqd.null_bitmap = bodo.utils.utils._empty_nd_impl(c
                        .context, c.builder, types.Array(types.uint8, 1,
                        'C'), [buh__miq])._getvalue()
                    grizr__bru = c.context.make_array(types.Array(types.
                        bool_, 1, 'C'))(c.context, c.builder, dvgzi__chqd.data
                        ).data
                    cer__sbp = c.context.make_array(types.Array(types.uint8,
                        1, 'C'))(c.context, c.builder, dvgzi__chqd.null_bitmap
                        ).data
                    xzgic__udxfh = lir.FunctionType(lir.VoidType(), [lir.
                        IntType(8).as_pointer(), lir.IntType(8).as_pointer(
                        ), lir.IntType(8).as_pointer(), lir.IntType(64)])
                    pfrv__ivgj = cgutils.get_or_insert_function(c.builder.
                        module, xzgic__udxfh, name='unbox_bool_array_obj')
                    c.builder.call(pfrv__ivgj, [obj, grizr__bru, cer__sbp, n])
    return NativeValue(dvgzi__chqd._getvalue())


@box(BooleanArrayType)
def box_bool_arr(typ, val, c):
    dvgzi__chqd = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    data = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        dvgzi__chqd.data, c.env_manager)
    cxigc__rbxvy = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c
        .context, c.builder, dvgzi__chqd.null_bitmap).data
    tzwx__pvm = c.pyapi.call_method(data, '__len__', ())
    n = c.pyapi.long_as_longlong(tzwx__pvm)
    gqmq__ywvq = c.context.insert_const_string(c.builder.module, 'numpy')
    cfi__reca = c.pyapi.import_module_noblock(gqmq__ywvq)
    giqv__gqy = c.pyapi.object_getattr_string(cfi__reca, 'bool_')
    jjpv__zzfx = c.pyapi.call_method(cfi__reca, 'empty', (tzwx__pvm, giqv__gqy)
        )
    dfmb__danpf = c.pyapi.object_getattr_string(jjpv__zzfx, 'ctypes')
    dwry__maya = c.pyapi.object_getattr_string(dfmb__danpf, 'data')
    xtjy__rsdty = c.builder.inttoptr(c.pyapi.long_as_longlong(dwry__maya),
        lir.IntType(8).as_pointer())
    with cgutils.for_range(c.builder, n) as tbfad__hkl:
        zntq__whoj = tbfad__hkl.index
        amad__bvcvb = c.builder.lshr(zntq__whoj, lir.Constant(lir.IntType(
            64), 3))
        lxbn__mpqx = c.builder.load(cgutils.gep(c.builder, cxigc__rbxvy,
            amad__bvcvb))
        zxjb__dgcog = c.builder.trunc(c.builder.and_(zntq__whoj, lir.
            Constant(lir.IntType(64), 7)), lir.IntType(8))
        val = c.builder.and_(c.builder.lshr(lxbn__mpqx, zxjb__dgcog), lir.
            Constant(lir.IntType(8), 1))
        val = c.builder.xor(val, lir.Constant(lir.IntType(8), 1))
        pbork__odxke = cgutils.gep(c.builder, xtjy__rsdty, zntq__whoj)
        c.builder.store(val, pbork__odxke)
    c.context.nrt.decref(c.builder, types.Array(types.uint8, 1, 'C'),
        dvgzi__chqd.null_bitmap)
    gqmq__ywvq = c.context.insert_const_string(c.builder.module, 'pandas')
    cfrkj__atnmx = c.pyapi.import_module_noblock(gqmq__ywvq)
    ehztd__lwvev = c.pyapi.object_getattr_string(cfrkj__atnmx, 'arrays')
    sae__aun = c.pyapi.call_method(ehztd__lwvev, 'BooleanArray', (data,
        jjpv__zzfx))
    c.pyapi.decref(cfrkj__atnmx)
    c.pyapi.decref(tzwx__pvm)
    c.pyapi.decref(cfi__reca)
    c.pyapi.decref(giqv__gqy)
    c.pyapi.decref(dfmb__danpf)
    c.pyapi.decref(dwry__maya)
    c.pyapi.decref(ehztd__lwvev)
    c.pyapi.decref(data)
    c.pyapi.decref(jjpv__zzfx)
    return sae__aun


@lower_constant(BooleanArrayType)
def lower_constant_bool_arr(context, builder, typ, pyval):
    n = len(pyval)
    mdand__zgbl = np.empty(n, np.bool_)
    jiuqx__pgfpj = np.empty(n + 7 >> 3, np.uint8)
    for zntq__whoj, s in enumerate(pyval):
        xqyp__vsiwj = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(jiuqx__pgfpj, zntq__whoj, int(
            not xqyp__vsiwj))
        if not xqyp__vsiwj:
            mdand__zgbl[zntq__whoj] = s
    ibd__qqztf = context.get_constant_generic(builder, data_type, mdand__zgbl)
    ifcjq__hjxan = context.get_constant_generic(builder, nulls_type,
        jiuqx__pgfpj)
    return lir.Constant.literal_struct([ibd__qqztf, ifcjq__hjxan])


def lower_init_bool_array(context, builder, signature, args):
    down__xcubk, yvd__urnjx = args
    dvgzi__chqd = cgutils.create_struct_proxy(signature.return_type)(context,
        builder)
    dvgzi__chqd.data = down__xcubk
    dvgzi__chqd.null_bitmap = yvd__urnjx
    context.nrt.incref(builder, signature.args[0], down__xcubk)
    context.nrt.incref(builder, signature.args[1], yvd__urnjx)
    return dvgzi__chqd._getvalue()


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
    ddc__kmj = args[0]
    if equiv_set.has_shape(ddc__kmj):
        return ArrayAnalysis.AnalyzeResult(shape=ddc__kmj, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_libs_bool_arr_ext_get_bool_arr_data = (
    get_bool_arr_data_equiv)


def init_bool_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    ddc__kmj = args[0]
    if equiv_set.has_shape(ddc__kmj):
        return ArrayAnalysis.AnalyzeResult(shape=ddc__kmj, pre=[])
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
    mdand__zgbl = np.empty(n, dtype=np.bool_)
    rfzo__itd = np.empty(n + 7 >> 3, dtype=np.uint8)
    return init_bool_array(mdand__zgbl, rfzo__itd)


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
            ivpmj__ipen, zyi__tigg = array_getitem_bool_index(A, ind)
            return init_bool_array(ivpmj__ipen, zyi__tigg)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            ivpmj__ipen, zyi__tigg = array_getitem_int_index(A, ind)
            return init_bool_array(ivpmj__ipen, zyi__tigg)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            ivpmj__ipen, zyi__tigg = array_getitem_slice_index(A, ind)
            return init_bool_array(ivpmj__ipen, zyi__tigg)
        return impl_slice
    raise BodoError(
        f'getitem for BooleanArray with indexing type {ind} not supported.')


@overload(operator.setitem, no_unliteral=True)
def bool_arr_setitem(A, idx, val):
    if A != boolean_array:
        return
    if val == types.none or isinstance(val, types.optional):
        return
    eemo__djejp = (
        f"setitem for BooleanArray with indexing type {idx} received an incorrect 'value' type {val}."
        )
    if isinstance(idx, types.Integer):
        if types.unliteral(val) == types.bool_:

            def impl_scalar(A, idx, val):
                A._data[idx] = val
                bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap, idx, 1)
            return impl_scalar
        else:
            raise BodoError(eemo__djejp)
    if not (is_iterable_type(val) and val.dtype == types.bool_ or types.
        unliteral(val) == types.bool_):
        raise BodoError(eemo__djejp)
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
        for zntq__whoj in numba.parfors.parfor.internal_prange(len(A)):
            val = 0
            if not bodo.libs.array_kernels.isna(A, zntq__whoj):
                val = A[zntq__whoj]
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
            epi__gozw = np.empty(n, nb_dtype)
            for zntq__whoj in numba.parfors.parfor.internal_prange(n):
                epi__gozw[zntq__whoj] = data[zntq__whoj]
                if bodo.libs.array_kernels.isna(A, zntq__whoj):
                    epi__gozw[zntq__whoj] = np.nan
            return epi__gozw
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
    dkzyv__mij = op.__name__
    dkzyv__mij = ufunc_aliases.get(dkzyv__mij, dkzyv__mij)
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
    for jnb__xezox in numba.np.ufunc_db.get_ufuncs():
        txz__udelo = create_op_overload(jnb__xezox, jnb__xezox.nin)
        overload(jnb__xezox, no_unliteral=True)(txz__udelo)


_install_np_ufuncs()
skips = [operator.lt, operator.le, operator.eq, operator.ne, operator.gt,
    operator.ge, operator.add, operator.sub, operator.mul, operator.truediv,
    operator.floordiv, operator.pow, operator.mod, operator.or_, operator.and_]


def _install_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesArrayOperator._op_map.keys():
        if op in skips:
            continue
        txz__udelo = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(txz__udelo)


_install_binary_ops()


def _install_inplace_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesInplaceArrayOperator._op_map.keys(
        ):
        txz__udelo = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(txz__udelo)


_install_inplace_binary_ops()


def _install_unary_ops():
    for op in (operator.neg, operator.invert, operator.pos):
        txz__udelo = create_op_overload(op, 1)
        overload(op, no_unliteral=True)(txz__udelo)


_install_unary_ops()


@overload_method(BooleanArrayType, 'unique', no_unliteral=True)
def overload_unique(A):

    def impl_bool_arr(A):
        data = []
        zxjb__dgcog = []
        hpz__ipmxm = False
        hyi__geod = False
        ihmbh__dpmy = False
        for zntq__whoj in range(len(A)):
            if bodo.libs.array_kernels.isna(A, zntq__whoj):
                if not hpz__ipmxm:
                    data.append(False)
                    zxjb__dgcog.append(False)
                    hpz__ipmxm = True
                continue
            val = A[zntq__whoj]
            if val and not hyi__geod:
                data.append(True)
                zxjb__dgcog.append(True)
                hyi__geod = True
            if not val and not ihmbh__dpmy:
                data.append(False)
                zxjb__dgcog.append(True)
                ihmbh__dpmy = True
            if hpz__ipmxm and hyi__geod and ihmbh__dpmy:
                break
        ivpmj__ipen = np.array(data)
        n = len(ivpmj__ipen)
        buh__miq = 1
        zyi__tigg = np.empty(buh__miq, np.uint8)
        for qtwhf__zero in range(n):
            bodo.libs.int_arr_ext.set_bit_to_arr(zyi__tigg, qtwhf__zero,
                zxjb__dgcog[qtwhf__zero])
        return init_bool_array(ivpmj__ipen, zyi__tigg)
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
    sae__aun = context.compile_internal(builder, func, toty(fromty), [val])
    return impl_ret_borrowed(context, builder, toty, sae__aun)


@overload(operator.setitem, no_unliteral=True)
def overload_np_array_setitem_bool_arr(A, idx, val):
    if isinstance(A, types.Array) and idx == boolean_array:

        def impl(A, idx, val):
            A[idx._data] = val
        return impl


def create_nullable_logical_op_overload(op):
    vqu__awe = op == operator.or_

    def bool_array_impl(val1, val2):
        if not is_valid_boolean_array_logical_op(val1, val2):
            return
        qlme__rqqh = bodo.utils.utils.is_array_typ(val1, False)
        hqs__ukhr = bodo.utils.utils.is_array_typ(val2, False)
        xjc__jfa = 'val1' if qlme__rqqh else 'val2'
        qjpew__zlp = 'def impl(val1, val2):\n'
        qjpew__zlp += f'  n = len({xjc__jfa})\n'
        qjpew__zlp += (
            '  out_arr = bodo.utils.utils.alloc_type(n, bodo.boolean_array, (-1,))\n'
            )
        qjpew__zlp += '  for i in numba.parfors.parfor.internal_prange(n):\n'
        if qlme__rqqh:
            null1 = 'bodo.libs.array_kernels.isna(val1, i)\n'
            ydvk__imnb = 'val1[i]'
        else:
            null1 = 'False\n'
            ydvk__imnb = 'val1'
        if hqs__ukhr:
            null2 = 'bodo.libs.array_kernels.isna(val2, i)\n'
            ausd__swx = 'val2[i]'
        else:
            null2 = 'False\n'
            ausd__swx = 'val2'
        if vqu__awe:
            qjpew__zlp += f"""    result, isna_val = compute_or_body({null1}, {null2}, {ydvk__imnb}, {ausd__swx})
"""
        else:
            qjpew__zlp += f"""    result, isna_val = compute_and_body({null1}, {null2}, {ydvk__imnb}, {ausd__swx})
"""
        qjpew__zlp += '    out_arr[i] = result\n'
        qjpew__zlp += '    if isna_val:\n'
        qjpew__zlp += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
        qjpew__zlp += '      continue\n'
        qjpew__zlp += '  return out_arr\n'
        vctn__nknj = {}
        exec(qjpew__zlp, {'bodo': bodo, 'numba': numba, 'compute_and_body':
            compute_and_body, 'compute_or_body': compute_or_body}, vctn__nknj)
        impl = vctn__nknj['impl']
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
        vnx__oiefw = boolean_array
        return vnx__oiefw(*args)


def is_valid_boolean_array_logical_op(typ1, typ2):
    wpfek__fcis = (typ1 == bodo.boolean_array or typ2 == bodo.boolean_array
        ) and (bodo.utils.utils.is_array_typ(typ1, False) and typ1.dtype ==
        types.bool_ or typ1 == types.bool_) and (bodo.utils.utils.
        is_array_typ(typ2, False) and typ2.dtype == types.bool_ or typ2 ==
        types.bool_)
    return wpfek__fcis


def _install_nullable_logical_lowering():
    for op in (operator.and_, operator.or_):
        sfona__ghn = create_boolean_array_logical_lower_impl(op)
        infer_global(op)(BooleanArrayLogicalOperatorTemplate)
        for typ1, typ2 in [(boolean_array, boolean_array), (boolean_array,
            types.bool_), (boolean_array, types.Array(types.bool_, 1, 'C'))]:
            lower_builtin(op, typ1, typ2)(sfona__ghn)
            if typ1 != typ2:
                lower_builtin(op, typ2, typ1)(sfona__ghn)


_install_nullable_logical_lowering()
