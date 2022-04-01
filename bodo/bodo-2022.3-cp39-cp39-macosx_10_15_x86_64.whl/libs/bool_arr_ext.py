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
        ngs__quaj = [('data', data_type), ('null_bitmap', nulls_type)]
        models.StructModel.__init__(self, dmm, fe_type, ngs__quaj)


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
    ypbe__iyw = c.context.insert_const_string(c.builder.module, 'pandas')
    nixpg__oukwm = c.pyapi.import_module_noblock(ypbe__iyw)
    jgwmf__jrz = c.pyapi.call_method(nixpg__oukwm, 'BooleanDtype', ())
    c.pyapi.decref(nixpg__oukwm)
    return jgwmf__jrz


@unbox(BooleanDtype)
def unbox_boolean_dtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


typeof_impl.register(pd.BooleanDtype)(lambda a, b: boolean_dtype)
type_callable(pd.BooleanDtype)(lambda c: lambda : boolean_dtype)
lower_builtin(pd.BooleanDtype)(lambda c, b, s, a: c.get_dummy_value())


@numba.njit
def gen_full_bitmap(n):
    pdo__eowgi = n + 7 >> 3
    return np.full(pdo__eowgi, 255, np.uint8)


def call_func_in_unbox(func, args, arg_typs, c):
    ybju__rzath = c.context.typing_context.resolve_value_type(func)
    afhhz__xqu = ybju__rzath.get_call_type(c.context.typing_context,
        arg_typs, {})
    ipkui__hjeok = c.context.get_function(ybju__rzath, afhhz__xqu)
    cwtka__lwa = c.context.call_conv.get_function_type(afhhz__xqu.
        return_type, afhhz__xqu.args)
    wekxe__tpam = c.builder.module
    ley__qudxu = lir.Function(wekxe__tpam, cwtka__lwa, name=wekxe__tpam.
        get_unique_name('.func_conv'))
    ley__qudxu.linkage = 'internal'
    qrjtd__oegah = lir.IRBuilder(ley__qudxu.append_basic_block())
    eqo__nram = c.context.call_conv.decode_arguments(qrjtd__oegah,
        afhhz__xqu.args, ley__qudxu)
    ffhj__obum = ipkui__hjeok(qrjtd__oegah, eqo__nram)
    c.context.call_conv.return_value(qrjtd__oegah, ffhj__obum)
    fqvog__mlyyd, ntg__zvdxh = c.context.call_conv.call_function(c.builder,
        ley__qudxu, afhhz__xqu.return_type, afhhz__xqu.args, args)
    return ntg__zvdxh


@unbox(BooleanArrayType)
def unbox_bool_array(typ, obj, c):
    lrj__jjn = c.pyapi.call_method(obj, '__len__', ())
    n = c.pyapi.long_as_longlong(lrj__jjn)
    c.pyapi.decref(lrj__jjn)
    cwtka__lwa = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
        as_pointer()])
    ustt__isv = cgutils.get_or_insert_function(c.builder.module, cwtka__lwa,
        name='is_bool_array')
    cwtka__lwa = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
        as_pointer()])
    ley__qudxu = cgutils.get_or_insert_function(c.builder.module,
        cwtka__lwa, name='is_pd_boolean_array')
    aetcy__mjqcc = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    fds__ydirs = c.builder.call(ley__qudxu, [obj])
    arw__sye = c.builder.icmp_unsigned('!=', fds__ydirs, fds__ydirs.type(0))
    with c.builder.if_else(arw__sye) as (iyftb__tpw, hfrd__ntqv):
        with iyftb__tpw:
            pia__gnwb = c.pyapi.object_getattr_string(obj, '_data')
            aetcy__mjqcc.data = c.pyapi.to_native_value(types.Array(types.
                bool_, 1, 'C'), pia__gnwb).value
            jsb__ctdp = c.pyapi.object_getattr_string(obj, '_mask')
            vsx__wvua = c.pyapi.to_native_value(types.Array(types.bool_, 1,
                'C'), jsb__ctdp).value
            pdo__eowgi = c.builder.udiv(c.builder.add(n, lir.Constant(lir.
                IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
            ylqyx__yqpq = c.context.make_array(types.Array(types.bool_, 1, 'C')
                )(c.context, c.builder, vsx__wvua)
            jmo__iov = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
                types.Array(types.uint8, 1, 'C'), [pdo__eowgi])
            cwtka__lwa = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
            ley__qudxu = cgutils.get_or_insert_function(c.builder.module,
                cwtka__lwa, name='mask_arr_to_bitmap')
            c.builder.call(ley__qudxu, [jmo__iov.data, ylqyx__yqpq.data, n])
            aetcy__mjqcc.null_bitmap = jmo__iov._getvalue()
            c.context.nrt.decref(c.builder, types.Array(types.bool_, 1, 'C'
                ), vsx__wvua)
            c.pyapi.decref(pia__gnwb)
            c.pyapi.decref(jsb__ctdp)
        with hfrd__ntqv:
            ahn__kij = c.builder.call(ustt__isv, [obj])
            aiu__krii = c.builder.icmp_unsigned('!=', ahn__kij, ahn__kij.
                type(0))
            with c.builder.if_else(aiu__krii) as (mqzor__myya, nfih__vuzag):
                with mqzor__myya:
                    aetcy__mjqcc.data = c.pyapi.to_native_value(types.Array
                        (types.bool_, 1, 'C'), obj).value
                    aetcy__mjqcc.null_bitmap = call_func_in_unbox(
                        gen_full_bitmap, (n,), (types.int64,), c)
                with nfih__vuzag:
                    aetcy__mjqcc.data = bodo.utils.utils._empty_nd_impl(c.
                        context, c.builder, types.Array(types.bool_, 1, 'C'
                        ), [n])._getvalue()
                    pdo__eowgi = c.builder.udiv(c.builder.add(n, lir.
                        Constant(lir.IntType(64), 7)), lir.Constant(lir.
                        IntType(64), 8))
                    aetcy__mjqcc.null_bitmap = bodo.utils.utils._empty_nd_impl(
                        c.context, c.builder, types.Array(types.uint8, 1,
                        'C'), [pdo__eowgi])._getvalue()
                    njle__pumnm = c.context.make_array(types.Array(types.
                        bool_, 1, 'C'))(c.context, c.builder, aetcy__mjqcc.data
                        ).data
                    fpeog__hgrb = c.context.make_array(types.Array(types.
                        uint8, 1, 'C'))(c.context, c.builder, aetcy__mjqcc.
                        null_bitmap).data
                    cwtka__lwa = lir.FunctionType(lir.VoidType(), [lir.
                        IntType(8).as_pointer(), lir.IntType(8).as_pointer(
                        ), lir.IntType(8).as_pointer(), lir.IntType(64)])
                    ley__qudxu = cgutils.get_or_insert_function(c.builder.
                        module, cwtka__lwa, name='unbox_bool_array_obj')
                    c.builder.call(ley__qudxu, [obj, njle__pumnm,
                        fpeog__hgrb, n])
    return NativeValue(aetcy__mjqcc._getvalue())


@box(BooleanArrayType)
def box_bool_arr(typ, val, c):
    aetcy__mjqcc = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    data = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        aetcy__mjqcc.data, c.env_manager)
    bih__btbi = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, aetcy__mjqcc.null_bitmap).data
    lrj__jjn = c.pyapi.call_method(data, '__len__', ())
    n = c.pyapi.long_as_longlong(lrj__jjn)
    ypbe__iyw = c.context.insert_const_string(c.builder.module, 'numpy')
    qjaqf__ngzog = c.pyapi.import_module_noblock(ypbe__iyw)
    ttzn__oykxz = c.pyapi.object_getattr_string(qjaqf__ngzog, 'bool_')
    vsx__wvua = c.pyapi.call_method(qjaqf__ngzog, 'empty', (lrj__jjn,
        ttzn__oykxz))
    qzq__mmck = c.pyapi.object_getattr_string(vsx__wvua, 'ctypes')
    rqfp__jmv = c.pyapi.object_getattr_string(qzq__mmck, 'data')
    hob__iwtv = c.builder.inttoptr(c.pyapi.long_as_longlong(rqfp__jmv), lir
        .IntType(8).as_pointer())
    with cgutils.for_range(c.builder, n) as cmy__lcovo:
        llwnl__isl = cmy__lcovo.index
        oth__dkoaz = c.builder.lshr(llwnl__isl, lir.Constant(lir.IntType(64
            ), 3))
        kocud__kxf = c.builder.load(cgutils.gep(c.builder, bih__btbi,
            oth__dkoaz))
        vzjtn__bvbso = c.builder.trunc(c.builder.and_(llwnl__isl, lir.
            Constant(lir.IntType(64), 7)), lir.IntType(8))
        val = c.builder.and_(c.builder.lshr(kocud__kxf, vzjtn__bvbso), lir.
            Constant(lir.IntType(8), 1))
        val = c.builder.xor(val, lir.Constant(lir.IntType(8), 1))
        uju__jkqd = cgutils.gep(c.builder, hob__iwtv, llwnl__isl)
        c.builder.store(val, uju__jkqd)
    c.context.nrt.decref(c.builder, types.Array(types.uint8, 1, 'C'),
        aetcy__mjqcc.null_bitmap)
    ypbe__iyw = c.context.insert_const_string(c.builder.module, 'pandas')
    nixpg__oukwm = c.pyapi.import_module_noblock(ypbe__iyw)
    gxfz__luco = c.pyapi.object_getattr_string(nixpg__oukwm, 'arrays')
    jgwmf__jrz = c.pyapi.call_method(gxfz__luco, 'BooleanArray', (data,
        vsx__wvua))
    c.pyapi.decref(nixpg__oukwm)
    c.pyapi.decref(lrj__jjn)
    c.pyapi.decref(qjaqf__ngzog)
    c.pyapi.decref(ttzn__oykxz)
    c.pyapi.decref(qzq__mmck)
    c.pyapi.decref(rqfp__jmv)
    c.pyapi.decref(gxfz__luco)
    c.pyapi.decref(data)
    c.pyapi.decref(vsx__wvua)
    return jgwmf__jrz


@lower_constant(BooleanArrayType)
def lower_constant_bool_arr(context, builder, typ, pyval):
    n = len(pyval)
    cssg__xiewb = np.empty(n, np.bool_)
    jsxhh__sjzu = np.empty(n + 7 >> 3, np.uint8)
    for llwnl__isl, s in enumerate(pyval):
        aiseq__bqkp = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(jsxhh__sjzu, llwnl__isl, int(
            not aiseq__bqkp))
        if not aiseq__bqkp:
            cssg__xiewb[llwnl__isl] = s
    luj__ouqji = context.get_constant_generic(builder, data_type, cssg__xiewb)
    dyzo__xnqw = context.get_constant_generic(builder, nulls_type, jsxhh__sjzu)
    return lir.Constant.literal_struct([luj__ouqji, dyzo__xnqw])


def lower_init_bool_array(context, builder, signature, args):
    vmde__muqy, vvg__mhb = args
    aetcy__mjqcc = cgutils.create_struct_proxy(signature.return_type)(context,
        builder)
    aetcy__mjqcc.data = vmde__muqy
    aetcy__mjqcc.null_bitmap = vvg__mhb
    context.nrt.incref(builder, signature.args[0], vmde__muqy)
    context.nrt.incref(builder, signature.args[1], vvg__mhb)
    return aetcy__mjqcc._getvalue()


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
    uhnh__bypdm = args[0]
    if equiv_set.has_shape(uhnh__bypdm):
        return ArrayAnalysis.AnalyzeResult(shape=uhnh__bypdm, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_libs_bool_arr_ext_get_bool_arr_data = (
    get_bool_arr_data_equiv)


def init_bool_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    uhnh__bypdm = args[0]
    if equiv_set.has_shape(uhnh__bypdm):
        return ArrayAnalysis.AnalyzeResult(shape=uhnh__bypdm, pre=[])
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
    cssg__xiewb = np.empty(n, dtype=np.bool_)
    gfuix__iqcjr = np.empty(n + 7 >> 3, dtype=np.uint8)
    return init_bool_array(cssg__xiewb, gfuix__iqcjr)


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
            jro__ezn, ixbu__gdme = array_getitem_bool_index(A, ind)
            return init_bool_array(jro__ezn, ixbu__gdme)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            jro__ezn, ixbu__gdme = array_getitem_int_index(A, ind)
            return init_bool_array(jro__ezn, ixbu__gdme)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            jro__ezn, ixbu__gdme = array_getitem_slice_index(A, ind)
            return init_bool_array(jro__ezn, ixbu__gdme)
        return impl_slice
    raise BodoError(
        f'getitem for BooleanArray with indexing type {ind} not supported.')


@overload(operator.setitem, no_unliteral=True)
def bool_arr_setitem(A, idx, val):
    if A != boolean_array:
        return
    if val == types.none or isinstance(val, types.optional):
        return
    istsp__mry = (
        f"setitem for BooleanArray with indexing type {idx} received an incorrect 'value' type {val}."
        )
    if isinstance(idx, types.Integer):
        if types.unliteral(val) == types.bool_:

            def impl_scalar(A, idx, val):
                A._data[idx] = val
                bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap, idx, 1)
            return impl_scalar
        else:
            raise BodoError(istsp__mry)
    if not (is_iterable_type(val) and val.dtype == types.bool_ or types.
        unliteral(val) == types.bool_):
        raise BodoError(istsp__mry)
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
        for llwnl__isl in numba.parfors.parfor.internal_prange(len(A)):
            val = 0
            if not bodo.libs.array_kernels.isna(A, llwnl__isl):
                val = A[llwnl__isl]
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
            xses__qlbp = np.empty(n, nb_dtype)
            for llwnl__isl in numba.parfors.parfor.internal_prange(n):
                xses__qlbp[llwnl__isl] = data[llwnl__isl]
                if bodo.libs.array_kernels.isna(A, llwnl__isl):
                    xses__qlbp[llwnl__isl] = np.nan
            return xses__qlbp
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
    pyk__sfq = op.__name__
    pyk__sfq = ufunc_aliases.get(pyk__sfq, pyk__sfq)
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
    for wqir__twuiw in numba.np.ufunc_db.get_ufuncs():
        ljt__zzogx = create_op_overload(wqir__twuiw, wqir__twuiw.nin)
        overload(wqir__twuiw, no_unliteral=True)(ljt__zzogx)


_install_np_ufuncs()
skips = [operator.lt, operator.le, operator.eq, operator.ne, operator.gt,
    operator.ge, operator.add, operator.sub, operator.mul, operator.truediv,
    operator.floordiv, operator.pow, operator.mod, operator.or_, operator.and_]


def _install_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesArrayOperator._op_map.keys():
        if op in skips:
            continue
        ljt__zzogx = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(ljt__zzogx)


_install_binary_ops()


def _install_inplace_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesInplaceArrayOperator._op_map.keys(
        ):
        ljt__zzogx = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(ljt__zzogx)


_install_inplace_binary_ops()


def _install_unary_ops():
    for op in (operator.neg, operator.invert, operator.pos):
        ljt__zzogx = create_op_overload(op, 1)
        overload(op, no_unliteral=True)(ljt__zzogx)


_install_unary_ops()


@overload_method(BooleanArrayType, 'unique', no_unliteral=True)
def overload_unique(A):

    def impl_bool_arr(A):
        data = []
        vzjtn__bvbso = []
        tfx__twyvr = False
        fdq__wazkm = False
        plfaz__isajf = False
        for llwnl__isl in range(len(A)):
            if bodo.libs.array_kernels.isna(A, llwnl__isl):
                if not tfx__twyvr:
                    data.append(False)
                    vzjtn__bvbso.append(False)
                    tfx__twyvr = True
                continue
            val = A[llwnl__isl]
            if val and not fdq__wazkm:
                data.append(True)
                vzjtn__bvbso.append(True)
                fdq__wazkm = True
            if not val and not plfaz__isajf:
                data.append(False)
                vzjtn__bvbso.append(True)
                plfaz__isajf = True
            if tfx__twyvr and fdq__wazkm and plfaz__isajf:
                break
        jro__ezn = np.array(data)
        n = len(jro__ezn)
        pdo__eowgi = 1
        ixbu__gdme = np.empty(pdo__eowgi, np.uint8)
        for ywuoq__sstcy in range(n):
            bodo.libs.int_arr_ext.set_bit_to_arr(ixbu__gdme, ywuoq__sstcy,
                vzjtn__bvbso[ywuoq__sstcy])
        return init_bool_array(jro__ezn, ixbu__gdme)
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
    jgwmf__jrz = context.compile_internal(builder, func, toty(fromty), [val])
    return impl_ret_borrowed(context, builder, toty, jgwmf__jrz)


@overload(operator.setitem, no_unliteral=True)
def overload_np_array_setitem_bool_arr(A, idx, val):
    if isinstance(A, types.Array) and idx == boolean_array:

        def impl(A, idx, val):
            A[idx._data] = val
        return impl


def create_nullable_logical_op_overload(op):
    afoyt__dzhew = op == operator.or_

    def bool_array_impl(val1, val2):
        if not is_valid_boolean_array_logical_op(val1, val2):
            return
        zfwki__qifgt = bodo.utils.utils.is_array_typ(val1, False)
        haeov__hagbd = bodo.utils.utils.is_array_typ(val2, False)
        lfbz__thuu = 'val1' if zfwki__qifgt else 'val2'
        hxlmk__ehmml = 'def impl(val1, val2):\n'
        hxlmk__ehmml += f'  n = len({lfbz__thuu})\n'
        hxlmk__ehmml += (
            '  out_arr = bodo.utils.utils.alloc_type(n, bodo.boolean_array, (-1,))\n'
            )
        hxlmk__ehmml += '  for i in numba.parfors.parfor.internal_prange(n):\n'
        if zfwki__qifgt:
            null1 = 'bodo.libs.array_kernels.isna(val1, i)\n'
            noi__cno = 'val1[i]'
        else:
            null1 = 'False\n'
            noi__cno = 'val1'
        if haeov__hagbd:
            null2 = 'bodo.libs.array_kernels.isna(val2, i)\n'
            inoak__nbi = 'val2[i]'
        else:
            null2 = 'False\n'
            inoak__nbi = 'val2'
        if afoyt__dzhew:
            hxlmk__ehmml += f"""    result, isna_val = compute_or_body({null1}, {null2}, {noi__cno}, {inoak__nbi})
"""
        else:
            hxlmk__ehmml += f"""    result, isna_val = compute_and_body({null1}, {null2}, {noi__cno}, {inoak__nbi})
"""
        hxlmk__ehmml += '    out_arr[i] = result\n'
        hxlmk__ehmml += '    if isna_val:\n'
        hxlmk__ehmml += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
        hxlmk__ehmml += '      continue\n'
        hxlmk__ehmml += '  return out_arr\n'
        qnfz__gkis = {}
        exec(hxlmk__ehmml, {'bodo': bodo, 'numba': numba,
            'compute_and_body': compute_and_body, 'compute_or_body':
            compute_or_body}, qnfz__gkis)
        impl = qnfz__gkis['impl']
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
        spdxp__zhgk = boolean_array
        return spdxp__zhgk(*args)


def is_valid_boolean_array_logical_op(typ1, typ2):
    vyi__pccm = (typ1 == bodo.boolean_array or typ2 == bodo.boolean_array
        ) and (bodo.utils.utils.is_array_typ(typ1, False) and typ1.dtype ==
        types.bool_ or typ1 == types.bool_) and (bodo.utils.utils.
        is_array_typ(typ2, False) and typ2.dtype == types.bool_ or typ2 ==
        types.bool_)
    return vyi__pccm


def _install_nullable_logical_lowering():
    for op in (operator.and_, operator.or_):
        qrj__fixj = create_boolean_array_logical_lower_impl(op)
        infer_global(op)(BooleanArrayLogicalOperatorTemplate)
        for typ1, typ2 in [(boolean_array, boolean_array), (boolean_array,
            types.bool_), (boolean_array, types.Array(types.bool_, 1, 'C'))]:
            lower_builtin(op, typ1, typ2)(qrj__fixj)
            if typ1 != typ2:
                lower_builtin(op, typ2, typ1)(qrj__fixj)


_install_nullable_logical_lowering()
