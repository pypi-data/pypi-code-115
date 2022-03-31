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
        rce__sqt = [('data', data_type), ('null_bitmap', nulls_type)]
        models.StructModel.__init__(self, dmm, fe_type, rce__sqt)


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
    synbq__vlk = c.context.insert_const_string(c.builder.module, 'pandas')
    yrizn__acm = c.pyapi.import_module_noblock(synbq__vlk)
    pbire__kld = c.pyapi.call_method(yrizn__acm, 'BooleanDtype', ())
    c.pyapi.decref(yrizn__acm)
    return pbire__kld


@unbox(BooleanDtype)
def unbox_boolean_dtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


typeof_impl.register(pd.BooleanDtype)(lambda a, b: boolean_dtype)
type_callable(pd.BooleanDtype)(lambda c: lambda : boolean_dtype)
lower_builtin(pd.BooleanDtype)(lambda c, b, s, a: c.get_dummy_value())


@numba.njit
def gen_full_bitmap(n):
    psu__lqx = n + 7 >> 3
    return np.full(psu__lqx, 255, np.uint8)


def call_func_in_unbox(func, args, arg_typs, c):
    vse__bjhqo = c.context.typing_context.resolve_value_type(func)
    zfu__feq = vse__bjhqo.get_call_type(c.context.typing_context, arg_typs, {})
    hwi__ktinv = c.context.get_function(vse__bjhqo, zfu__feq)
    ygo__rrqiu = c.context.call_conv.get_function_type(zfu__feq.return_type,
        zfu__feq.args)
    yns__fgwmz = c.builder.module
    szhaj__vfagi = lir.Function(yns__fgwmz, ygo__rrqiu, name=yns__fgwmz.
        get_unique_name('.func_conv'))
    szhaj__vfagi.linkage = 'internal'
    cxlbw__ltquf = lir.IRBuilder(szhaj__vfagi.append_basic_block())
    mpp__nss = c.context.call_conv.decode_arguments(cxlbw__ltquf, zfu__feq.
        args, szhaj__vfagi)
    dgv__acfsm = hwi__ktinv(cxlbw__ltquf, mpp__nss)
    c.context.call_conv.return_value(cxlbw__ltquf, dgv__acfsm)
    qfaoa__ctqlq, dwfl__rjxza = c.context.call_conv.call_function(c.builder,
        szhaj__vfagi, zfu__feq.return_type, zfu__feq.args, args)
    return dwfl__rjxza


@unbox(BooleanArrayType)
def unbox_bool_array(typ, obj, c):
    pcxk__akogw = c.pyapi.call_method(obj, '__len__', ())
    n = c.pyapi.long_as_longlong(pcxk__akogw)
    c.pyapi.decref(pcxk__akogw)
    ygo__rrqiu = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
        as_pointer()])
    wqgrh__wgvn = cgutils.get_or_insert_function(c.builder.module,
        ygo__rrqiu, name='is_bool_array')
    ygo__rrqiu = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
        as_pointer()])
    szhaj__vfagi = cgutils.get_or_insert_function(c.builder.module,
        ygo__rrqiu, name='is_pd_boolean_array')
    uinj__zjsmb = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    xsr__czsgz = c.builder.call(szhaj__vfagi, [obj])
    qsy__cfewx = c.builder.icmp_unsigned('!=', xsr__czsgz, xsr__czsgz.type(0))
    with c.builder.if_else(qsy__cfewx) as (simd__wrvf, dpdj__fmfv):
        with simd__wrvf:
            otaiq__uoxsz = c.pyapi.object_getattr_string(obj, '_data')
            uinj__zjsmb.data = c.pyapi.to_native_value(types.Array(types.
                bool_, 1, 'C'), otaiq__uoxsz).value
            qacn__hdps = c.pyapi.object_getattr_string(obj, '_mask')
            znx__weucj = c.pyapi.to_native_value(types.Array(types.bool_, 1,
                'C'), qacn__hdps).value
            psu__lqx = c.builder.udiv(c.builder.add(n, lir.Constant(lir.
                IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
            kqz__muygm = c.context.make_array(types.Array(types.bool_, 1, 'C')
                )(c.context, c.builder, znx__weucj)
            uge__yhiuj = bodo.utils.utils._empty_nd_impl(c.context, c.
                builder, types.Array(types.uint8, 1, 'C'), [psu__lqx])
            ygo__rrqiu = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
            szhaj__vfagi = cgutils.get_or_insert_function(c.builder.module,
                ygo__rrqiu, name='mask_arr_to_bitmap')
            c.builder.call(szhaj__vfagi, [uge__yhiuj.data, kqz__muygm.data, n])
            uinj__zjsmb.null_bitmap = uge__yhiuj._getvalue()
            c.context.nrt.decref(c.builder, types.Array(types.bool_, 1, 'C'
                ), znx__weucj)
            c.pyapi.decref(otaiq__uoxsz)
            c.pyapi.decref(qacn__hdps)
        with dpdj__fmfv:
            lzh__xqsp = c.builder.call(wqgrh__wgvn, [obj])
            hfps__rht = c.builder.icmp_unsigned('!=', lzh__xqsp, lzh__xqsp.
                type(0))
            with c.builder.if_else(hfps__rht) as (tpa__khljt, dyd__bdq):
                with tpa__khljt:
                    uinj__zjsmb.data = c.pyapi.to_native_value(types.Array(
                        types.bool_, 1, 'C'), obj).value
                    uinj__zjsmb.null_bitmap = call_func_in_unbox(
                        gen_full_bitmap, (n,), (types.int64,), c)
                with dyd__bdq:
                    uinj__zjsmb.data = bodo.utils.utils._empty_nd_impl(c.
                        context, c.builder, types.Array(types.bool_, 1, 'C'
                        ), [n])._getvalue()
                    psu__lqx = c.builder.udiv(c.builder.add(n, lir.Constant
                        (lir.IntType(64), 7)), lir.Constant(lir.IntType(64), 8)
                        )
                    uinj__zjsmb.null_bitmap = bodo.utils.utils._empty_nd_impl(c
                        .context, c.builder, types.Array(types.uint8, 1,
                        'C'), [psu__lqx])._getvalue()
                    dpwfu__ozygs = c.context.make_array(types.Array(types.
                        bool_, 1, 'C'))(c.context, c.builder, uinj__zjsmb.data
                        ).data
                    erorf__eis = c.context.make_array(types.Array(types.
                        uint8, 1, 'C'))(c.context, c.builder, uinj__zjsmb.
                        null_bitmap).data
                    ygo__rrqiu = lir.FunctionType(lir.VoidType(), [lir.
                        IntType(8).as_pointer(), lir.IntType(8).as_pointer(
                        ), lir.IntType(8).as_pointer(), lir.IntType(64)])
                    szhaj__vfagi = cgutils.get_or_insert_function(c.builder
                        .module, ygo__rrqiu, name='unbox_bool_array_obj')
                    c.builder.call(szhaj__vfagi, [obj, dpwfu__ozygs,
                        erorf__eis, n])
    return NativeValue(uinj__zjsmb._getvalue())


@box(BooleanArrayType)
def box_bool_arr(typ, val, c):
    uinj__zjsmb = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    data = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        uinj__zjsmb.data, c.env_manager)
    ggui__jij = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, uinj__zjsmb.null_bitmap).data
    pcxk__akogw = c.pyapi.call_method(data, '__len__', ())
    n = c.pyapi.long_as_longlong(pcxk__akogw)
    synbq__vlk = c.context.insert_const_string(c.builder.module, 'numpy')
    pdw__jxg = c.pyapi.import_module_noblock(synbq__vlk)
    rhe__qee = c.pyapi.object_getattr_string(pdw__jxg, 'bool_')
    znx__weucj = c.pyapi.call_method(pdw__jxg, 'empty', (pcxk__akogw, rhe__qee)
        )
    dwd__xur = c.pyapi.object_getattr_string(znx__weucj, 'ctypes')
    aurg__ihugq = c.pyapi.object_getattr_string(dwd__xur, 'data')
    ganza__wlbzg = c.builder.inttoptr(c.pyapi.long_as_longlong(aurg__ihugq),
        lir.IntType(8).as_pointer())
    with cgutils.for_range(c.builder, n) as apwp__gnkka:
        jizxd__tgz = apwp__gnkka.index
        wvo__ahenc = c.builder.lshr(jizxd__tgz, lir.Constant(lir.IntType(64
            ), 3))
        rdr__mfqxn = c.builder.load(cgutils.gep(c.builder, ggui__jij,
            wvo__ahenc))
        rfjpy__bdm = c.builder.trunc(c.builder.and_(jizxd__tgz, lir.
            Constant(lir.IntType(64), 7)), lir.IntType(8))
        val = c.builder.and_(c.builder.lshr(rdr__mfqxn, rfjpy__bdm), lir.
            Constant(lir.IntType(8), 1))
        val = c.builder.xor(val, lir.Constant(lir.IntType(8), 1))
        rir__qpype = cgutils.gep(c.builder, ganza__wlbzg, jizxd__tgz)
        c.builder.store(val, rir__qpype)
    c.context.nrt.decref(c.builder, types.Array(types.uint8, 1, 'C'),
        uinj__zjsmb.null_bitmap)
    synbq__vlk = c.context.insert_const_string(c.builder.module, 'pandas')
    yrizn__acm = c.pyapi.import_module_noblock(synbq__vlk)
    fbk__sis = c.pyapi.object_getattr_string(yrizn__acm, 'arrays')
    pbire__kld = c.pyapi.call_method(fbk__sis, 'BooleanArray', (data,
        znx__weucj))
    c.pyapi.decref(yrizn__acm)
    c.pyapi.decref(pcxk__akogw)
    c.pyapi.decref(pdw__jxg)
    c.pyapi.decref(rhe__qee)
    c.pyapi.decref(dwd__xur)
    c.pyapi.decref(aurg__ihugq)
    c.pyapi.decref(fbk__sis)
    c.pyapi.decref(data)
    c.pyapi.decref(znx__weucj)
    return pbire__kld


@lower_constant(BooleanArrayType)
def lower_constant_bool_arr(context, builder, typ, pyval):
    n = len(pyval)
    krq__tduwc = np.empty(n, np.bool_)
    gdltr__rlq = np.empty(n + 7 >> 3, np.uint8)
    for jizxd__tgz, s in enumerate(pyval):
        jtozp__afmt = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(gdltr__rlq, jizxd__tgz, int(
            not jtozp__afmt))
        if not jtozp__afmt:
            krq__tduwc[jizxd__tgz] = s
    rrce__ssv = context.get_constant_generic(builder, data_type, krq__tduwc)
    sdux__ykrw = context.get_constant_generic(builder, nulls_type, gdltr__rlq)
    return lir.Constant.literal_struct([rrce__ssv, sdux__ykrw])


def lower_init_bool_array(context, builder, signature, args):
    soywv__igt, uvgn__gkz = args
    uinj__zjsmb = cgutils.create_struct_proxy(signature.return_type)(context,
        builder)
    uinj__zjsmb.data = soywv__igt
    uinj__zjsmb.null_bitmap = uvgn__gkz
    context.nrt.incref(builder, signature.args[0], soywv__igt)
    context.nrt.incref(builder, signature.args[1], uvgn__gkz)
    return uinj__zjsmb._getvalue()


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
    gim__hsm = args[0]
    if equiv_set.has_shape(gim__hsm):
        return ArrayAnalysis.AnalyzeResult(shape=gim__hsm, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_libs_bool_arr_ext_get_bool_arr_data = (
    get_bool_arr_data_equiv)


def init_bool_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    gim__hsm = args[0]
    if equiv_set.has_shape(gim__hsm):
        return ArrayAnalysis.AnalyzeResult(shape=gim__hsm, pre=[])
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
    krq__tduwc = np.empty(n, dtype=np.bool_)
    ebl__trb = np.empty(n + 7 >> 3, dtype=np.uint8)
    return init_bool_array(krq__tduwc, ebl__trb)


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
            zdp__hhheh, prx__pcqkx = array_getitem_bool_index(A, ind)
            return init_bool_array(zdp__hhheh, prx__pcqkx)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            zdp__hhheh, prx__pcqkx = array_getitem_int_index(A, ind)
            return init_bool_array(zdp__hhheh, prx__pcqkx)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            zdp__hhheh, prx__pcqkx = array_getitem_slice_index(A, ind)
            return init_bool_array(zdp__hhheh, prx__pcqkx)
        return impl_slice
    raise BodoError(
        f'getitem for BooleanArray with indexing type {ind} not supported.')


@overload(operator.setitem, no_unliteral=True)
def bool_arr_setitem(A, idx, val):
    if A != boolean_array:
        return
    if val == types.none or isinstance(val, types.optional):
        return
    gcjle__eyow = (
        f"setitem for BooleanArray with indexing type {idx} received an incorrect 'value' type {val}."
        )
    if isinstance(idx, types.Integer):
        if types.unliteral(val) == types.bool_:

            def impl_scalar(A, idx, val):
                A._data[idx] = val
                bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap, idx, 1)
            return impl_scalar
        else:
            raise BodoError(gcjle__eyow)
    if not (is_iterable_type(val) and val.dtype == types.bool_ or types.
        unliteral(val) == types.bool_):
        raise BodoError(gcjle__eyow)
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
        for jizxd__tgz in numba.parfors.parfor.internal_prange(len(A)):
            val = 0
            if not bodo.libs.array_kernels.isna(A, jizxd__tgz):
                val = A[jizxd__tgz]
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
            wqi__jgi = np.empty(n, nb_dtype)
            for jizxd__tgz in numba.parfors.parfor.internal_prange(n):
                wqi__jgi[jizxd__tgz] = data[jizxd__tgz]
                if bodo.libs.array_kernels.isna(A, jizxd__tgz):
                    wqi__jgi[jizxd__tgz] = np.nan
            return wqi__jgi
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
    zoiq__olif = op.__name__
    zoiq__olif = ufunc_aliases.get(zoiq__olif, zoiq__olif)
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
    for omidd__evrsf in numba.np.ufunc_db.get_ufuncs():
        cncz__otnx = create_op_overload(omidd__evrsf, omidd__evrsf.nin)
        overload(omidd__evrsf, no_unliteral=True)(cncz__otnx)


_install_np_ufuncs()
skips = [operator.lt, operator.le, operator.eq, operator.ne, operator.gt,
    operator.ge, operator.add, operator.sub, operator.mul, operator.truediv,
    operator.floordiv, operator.pow, operator.mod, operator.or_, operator.and_]


def _install_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesArrayOperator._op_map.keys():
        if op in skips:
            continue
        cncz__otnx = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(cncz__otnx)


_install_binary_ops()


def _install_inplace_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesInplaceArrayOperator._op_map.keys(
        ):
        cncz__otnx = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(cncz__otnx)


_install_inplace_binary_ops()


def _install_unary_ops():
    for op in (operator.neg, operator.invert, operator.pos):
        cncz__otnx = create_op_overload(op, 1)
        overload(op, no_unliteral=True)(cncz__otnx)


_install_unary_ops()


@overload_method(BooleanArrayType, 'unique', no_unliteral=True)
def overload_unique(A):

    def impl_bool_arr(A):
        data = []
        rfjpy__bdm = []
        kenf__voa = False
        ina__qty = False
        qfwou__aaiv = False
        for jizxd__tgz in range(len(A)):
            if bodo.libs.array_kernels.isna(A, jizxd__tgz):
                if not kenf__voa:
                    data.append(False)
                    rfjpy__bdm.append(False)
                    kenf__voa = True
                continue
            val = A[jizxd__tgz]
            if val and not ina__qty:
                data.append(True)
                rfjpy__bdm.append(True)
                ina__qty = True
            if not val and not qfwou__aaiv:
                data.append(False)
                rfjpy__bdm.append(True)
                qfwou__aaiv = True
            if kenf__voa and ina__qty and qfwou__aaiv:
                break
        zdp__hhheh = np.array(data)
        n = len(zdp__hhheh)
        psu__lqx = 1
        prx__pcqkx = np.empty(psu__lqx, np.uint8)
        for bgz__erduo in range(n):
            bodo.libs.int_arr_ext.set_bit_to_arr(prx__pcqkx, bgz__erduo,
                rfjpy__bdm[bgz__erduo])
        return init_bool_array(zdp__hhheh, prx__pcqkx)
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
    pbire__kld = context.compile_internal(builder, func, toty(fromty), [val])
    return impl_ret_borrowed(context, builder, toty, pbire__kld)


@overload(operator.setitem, no_unliteral=True)
def overload_np_array_setitem_bool_arr(A, idx, val):
    if isinstance(A, types.Array) and idx == boolean_array:

        def impl(A, idx, val):
            A[idx._data] = val
        return impl


def create_nullable_logical_op_overload(op):
    juax__mwqac = op == operator.or_

    def bool_array_impl(val1, val2):
        if not is_valid_boolean_array_logical_op(val1, val2):
            return
        saz__xdz = bodo.utils.utils.is_array_typ(val1, False)
        alr__nddco = bodo.utils.utils.is_array_typ(val2, False)
        gwvn__tki = 'val1' if saz__xdz else 'val2'
        vmkz__byupn = 'def impl(val1, val2):\n'
        vmkz__byupn += f'  n = len({gwvn__tki})\n'
        vmkz__byupn += (
            '  out_arr = bodo.utils.utils.alloc_type(n, bodo.boolean_array, (-1,))\n'
            )
        vmkz__byupn += '  for i in numba.parfors.parfor.internal_prange(n):\n'
        if saz__xdz:
            null1 = 'bodo.libs.array_kernels.isna(val1, i)\n'
            stqu__fwtsa = 'val1[i]'
        else:
            null1 = 'False\n'
            stqu__fwtsa = 'val1'
        if alr__nddco:
            null2 = 'bodo.libs.array_kernels.isna(val2, i)\n'
            yuv__apkb = 'val2[i]'
        else:
            null2 = 'False\n'
            yuv__apkb = 'val2'
        if juax__mwqac:
            vmkz__byupn += f"""    result, isna_val = compute_or_body({null1}, {null2}, {stqu__fwtsa}, {yuv__apkb})
"""
        else:
            vmkz__byupn += f"""    result, isna_val = compute_and_body({null1}, {null2}, {stqu__fwtsa}, {yuv__apkb})
"""
        vmkz__byupn += '    out_arr[i] = result\n'
        vmkz__byupn += '    if isna_val:\n'
        vmkz__byupn += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
        vmkz__byupn += '      continue\n'
        vmkz__byupn += '  return out_arr\n'
        pymf__ondvc = {}
        exec(vmkz__byupn, {'bodo': bodo, 'numba': numba, 'compute_and_body':
            compute_and_body, 'compute_or_body': compute_or_body}, pymf__ondvc)
        impl = pymf__ondvc['impl']
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
        jcu__dwth = boolean_array
        return jcu__dwth(*args)


def is_valid_boolean_array_logical_op(typ1, typ2):
    eot__fwx = (typ1 == bodo.boolean_array or typ2 == bodo.boolean_array) and (
        bodo.utils.utils.is_array_typ(typ1, False) and typ1.dtype == types.
        bool_ or typ1 == types.bool_) and (bodo.utils.utils.is_array_typ(
        typ2, False) and typ2.dtype == types.bool_ or typ2 == types.bool_)
    return eot__fwx


def _install_nullable_logical_lowering():
    for op in (operator.and_, operator.or_):
        tlmfk__cxu = create_boolean_array_logical_lower_impl(op)
        infer_global(op)(BooleanArrayLogicalOperatorTemplate)
        for typ1, typ2 in [(boolean_array, boolean_array), (boolean_array,
            types.bool_), (boolean_array, types.Array(types.bool_, 1, 'C'))]:
            lower_builtin(op, typ1, typ2)(tlmfk__cxu)
            if typ1 != typ2:
                lower_builtin(op, typ2, typ1)(tlmfk__cxu)


_install_nullable_logical_lowering()
