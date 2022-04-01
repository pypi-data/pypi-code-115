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
        dzqq__wutb = [('data', data_type), ('null_bitmap', nulls_type)]
        models.StructModel.__init__(self, dmm, fe_type, dzqq__wutb)


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
    yqi__bwe = c.context.insert_const_string(c.builder.module, 'pandas')
    bkicv__yhvvg = c.pyapi.import_module_noblock(yqi__bwe)
    thlqv__psn = c.pyapi.call_method(bkicv__yhvvg, 'BooleanDtype', ())
    c.pyapi.decref(bkicv__yhvvg)
    return thlqv__psn


@unbox(BooleanDtype)
def unbox_boolean_dtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


typeof_impl.register(pd.BooleanDtype)(lambda a, b: boolean_dtype)
type_callable(pd.BooleanDtype)(lambda c: lambda : boolean_dtype)
lower_builtin(pd.BooleanDtype)(lambda c, b, s, a: c.get_dummy_value())


@numba.njit
def gen_full_bitmap(n):
    bwpcr__arpru = n + 7 >> 3
    return np.full(bwpcr__arpru, 255, np.uint8)


def call_func_in_unbox(func, args, arg_typs, c):
    szeyn__fwp = c.context.typing_context.resolve_value_type(func)
    uqan__oiit = szeyn__fwp.get_call_type(c.context.typing_context,
        arg_typs, {})
    oqb__ljlww = c.context.get_function(szeyn__fwp, uqan__oiit)
    fka__oau = c.context.call_conv.get_function_type(uqan__oiit.return_type,
        uqan__oiit.args)
    rkxer__deq = c.builder.module
    xxubv__biik = lir.Function(rkxer__deq, fka__oau, name=rkxer__deq.
        get_unique_name('.func_conv'))
    xxubv__biik.linkage = 'internal'
    gxii__rvf = lir.IRBuilder(xxubv__biik.append_basic_block())
    ppp__ddkn = c.context.call_conv.decode_arguments(gxii__rvf, uqan__oiit.
        args, xxubv__biik)
    perye__iak = oqb__ljlww(gxii__rvf, ppp__ddkn)
    c.context.call_conv.return_value(gxii__rvf, perye__iak)
    iqku__sbue, cgao__ttwa = c.context.call_conv.call_function(c.builder,
        xxubv__biik, uqan__oiit.return_type, uqan__oiit.args, args)
    return cgao__ttwa


@unbox(BooleanArrayType)
def unbox_bool_array(typ, obj, c):
    amswj__izat = c.pyapi.call_method(obj, '__len__', ())
    n = c.pyapi.long_as_longlong(amswj__izat)
    c.pyapi.decref(amswj__izat)
    fka__oau = lir.FunctionType(lir.IntType(32), [lir.IntType(8).as_pointer()])
    uyi__jpbem = cgutils.get_or_insert_function(c.builder.module, fka__oau,
        name='is_bool_array')
    fka__oau = lir.FunctionType(lir.IntType(32), [lir.IntType(8).as_pointer()])
    xxubv__biik = cgutils.get_or_insert_function(c.builder.module, fka__oau,
        name='is_pd_boolean_array')
    wiryf__wtgza = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    vdswd__ddoou = c.builder.call(xxubv__biik, [obj])
    mgjnj__vhqd = c.builder.icmp_unsigned('!=', vdswd__ddoou, vdswd__ddoou.
        type(0))
    with c.builder.if_else(mgjnj__vhqd) as (kqp__zxw, rgmqr__eovar):
        with kqp__zxw:
            kzxp__zjtld = c.pyapi.object_getattr_string(obj, '_data')
            wiryf__wtgza.data = c.pyapi.to_native_value(types.Array(types.
                bool_, 1, 'C'), kzxp__zjtld).value
            acsc__xzt = c.pyapi.object_getattr_string(obj, '_mask')
            owmyp__tjsfz = c.pyapi.to_native_value(types.Array(types.bool_,
                1, 'C'), acsc__xzt).value
            bwpcr__arpru = c.builder.udiv(c.builder.add(n, lir.Constant(lir
                .IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
            cfzta__bivu = c.context.make_array(types.Array(types.bool_, 1, 'C')
                )(c.context, c.builder, owmyp__tjsfz)
            msa__hcqk = bodo.utils.utils._empty_nd_impl(c.context, c.
                builder, types.Array(types.uint8, 1, 'C'), [bwpcr__arpru])
            fka__oau = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
            xxubv__biik = cgutils.get_or_insert_function(c.builder.module,
                fka__oau, name='mask_arr_to_bitmap')
            c.builder.call(xxubv__biik, [msa__hcqk.data, cfzta__bivu.data, n])
            wiryf__wtgza.null_bitmap = msa__hcqk._getvalue()
            c.context.nrt.decref(c.builder, types.Array(types.bool_, 1, 'C'
                ), owmyp__tjsfz)
            c.pyapi.decref(kzxp__zjtld)
            c.pyapi.decref(acsc__xzt)
        with rgmqr__eovar:
            khrh__kzkt = c.builder.call(uyi__jpbem, [obj])
            laocn__tft = c.builder.icmp_unsigned('!=', khrh__kzkt,
                khrh__kzkt.type(0))
            with c.builder.if_else(laocn__tft) as (ajy__lpn, zgbc__pknep):
                with ajy__lpn:
                    wiryf__wtgza.data = c.pyapi.to_native_value(types.Array
                        (types.bool_, 1, 'C'), obj).value
                    wiryf__wtgza.null_bitmap = call_func_in_unbox(
                        gen_full_bitmap, (n,), (types.int64,), c)
                with zgbc__pknep:
                    wiryf__wtgza.data = bodo.utils.utils._empty_nd_impl(c.
                        context, c.builder, types.Array(types.bool_, 1, 'C'
                        ), [n])._getvalue()
                    bwpcr__arpru = c.builder.udiv(c.builder.add(n, lir.
                        Constant(lir.IntType(64), 7)), lir.Constant(lir.
                        IntType(64), 8))
                    wiryf__wtgza.null_bitmap = bodo.utils.utils._empty_nd_impl(
                        c.context, c.builder, types.Array(types.uint8, 1,
                        'C'), [bwpcr__arpru])._getvalue()
                    tdpqi__ktsk = c.context.make_array(types.Array(types.
                        bool_, 1, 'C'))(c.context, c.builder, wiryf__wtgza.data
                        ).data
                    kksm__adau = c.context.make_array(types.Array(types.
                        uint8, 1, 'C'))(c.context, c.builder, wiryf__wtgza.
                        null_bitmap).data
                    fka__oau = lir.FunctionType(lir.VoidType(), [lir.
                        IntType(8).as_pointer(), lir.IntType(8).as_pointer(
                        ), lir.IntType(8).as_pointer(), lir.IntType(64)])
                    xxubv__biik = cgutils.get_or_insert_function(c.builder.
                        module, fka__oau, name='unbox_bool_array_obj')
                    c.builder.call(xxubv__biik, [obj, tdpqi__ktsk,
                        kksm__adau, n])
    return NativeValue(wiryf__wtgza._getvalue())


@box(BooleanArrayType)
def box_bool_arr(typ, val, c):
    wiryf__wtgza = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    data = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        wiryf__wtgza.data, c.env_manager)
    sypvm__bvup = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, wiryf__wtgza.null_bitmap).data
    amswj__izat = c.pyapi.call_method(data, '__len__', ())
    n = c.pyapi.long_as_longlong(amswj__izat)
    yqi__bwe = c.context.insert_const_string(c.builder.module, 'numpy')
    jzybj__gzoy = c.pyapi.import_module_noblock(yqi__bwe)
    fdg__wtcj = c.pyapi.object_getattr_string(jzybj__gzoy, 'bool_')
    owmyp__tjsfz = c.pyapi.call_method(jzybj__gzoy, 'empty', (amswj__izat,
        fdg__wtcj))
    zsvr__syvb = c.pyapi.object_getattr_string(owmyp__tjsfz, 'ctypes')
    vbmed__hvui = c.pyapi.object_getattr_string(zsvr__syvb, 'data')
    qucuh__zcdad = c.builder.inttoptr(c.pyapi.long_as_longlong(vbmed__hvui),
        lir.IntType(8).as_pointer())
    with cgutils.for_range(c.builder, n) as asbx__wtyx:
        bvth__rbki = asbx__wtyx.index
        stnnn__whfu = c.builder.lshr(bvth__rbki, lir.Constant(lir.IntType(
            64), 3))
        mmdug__fgxh = c.builder.load(cgutils.gep(c.builder, sypvm__bvup,
            stnnn__whfu))
        eos__cpw = c.builder.trunc(c.builder.and_(bvth__rbki, lir.Constant(
            lir.IntType(64), 7)), lir.IntType(8))
        val = c.builder.and_(c.builder.lshr(mmdug__fgxh, eos__cpw), lir.
            Constant(lir.IntType(8), 1))
        val = c.builder.xor(val, lir.Constant(lir.IntType(8), 1))
        ifx__subko = cgutils.gep(c.builder, qucuh__zcdad, bvth__rbki)
        c.builder.store(val, ifx__subko)
    c.context.nrt.decref(c.builder, types.Array(types.uint8, 1, 'C'),
        wiryf__wtgza.null_bitmap)
    yqi__bwe = c.context.insert_const_string(c.builder.module, 'pandas')
    bkicv__yhvvg = c.pyapi.import_module_noblock(yqi__bwe)
    dzrjx__wvrkt = c.pyapi.object_getattr_string(bkicv__yhvvg, 'arrays')
    thlqv__psn = c.pyapi.call_method(dzrjx__wvrkt, 'BooleanArray', (data,
        owmyp__tjsfz))
    c.pyapi.decref(bkicv__yhvvg)
    c.pyapi.decref(amswj__izat)
    c.pyapi.decref(jzybj__gzoy)
    c.pyapi.decref(fdg__wtcj)
    c.pyapi.decref(zsvr__syvb)
    c.pyapi.decref(vbmed__hvui)
    c.pyapi.decref(dzrjx__wvrkt)
    c.pyapi.decref(data)
    c.pyapi.decref(owmyp__tjsfz)
    return thlqv__psn


@lower_constant(BooleanArrayType)
def lower_constant_bool_arr(context, builder, typ, pyval):
    n = len(pyval)
    xxe__qmlk = np.empty(n, np.bool_)
    ddr__doeq = np.empty(n + 7 >> 3, np.uint8)
    for bvth__rbki, s in enumerate(pyval):
        sqq__mvjeb = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(ddr__doeq, bvth__rbki, int(not
            sqq__mvjeb))
        if not sqq__mvjeb:
            xxe__qmlk[bvth__rbki] = s
    fpiq__zqqji = context.get_constant_generic(builder, data_type, xxe__qmlk)
    tbm__rll = context.get_constant_generic(builder, nulls_type, ddr__doeq)
    return lir.Constant.literal_struct([fpiq__zqqji, tbm__rll])


def lower_init_bool_array(context, builder, signature, args):
    mmyqc__hdab, ail__jpli = args
    wiryf__wtgza = cgutils.create_struct_proxy(signature.return_type)(context,
        builder)
    wiryf__wtgza.data = mmyqc__hdab
    wiryf__wtgza.null_bitmap = ail__jpli
    context.nrt.incref(builder, signature.args[0], mmyqc__hdab)
    context.nrt.incref(builder, signature.args[1], ail__jpli)
    return wiryf__wtgza._getvalue()


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
    ryup__awvoi = args[0]
    if equiv_set.has_shape(ryup__awvoi):
        return ArrayAnalysis.AnalyzeResult(shape=ryup__awvoi, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_libs_bool_arr_ext_get_bool_arr_data = (
    get_bool_arr_data_equiv)


def init_bool_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    ryup__awvoi = args[0]
    if equiv_set.has_shape(ryup__awvoi):
        return ArrayAnalysis.AnalyzeResult(shape=ryup__awvoi, pre=[])
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
    xxe__qmlk = np.empty(n, dtype=np.bool_)
    bvmmd__ggfd = np.empty(n + 7 >> 3, dtype=np.uint8)
    return init_bool_array(xxe__qmlk, bvmmd__ggfd)


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
            bpxwr__wak, vnqt__qbuef = array_getitem_bool_index(A, ind)
            return init_bool_array(bpxwr__wak, vnqt__qbuef)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            bpxwr__wak, vnqt__qbuef = array_getitem_int_index(A, ind)
            return init_bool_array(bpxwr__wak, vnqt__qbuef)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            bpxwr__wak, vnqt__qbuef = array_getitem_slice_index(A, ind)
            return init_bool_array(bpxwr__wak, vnqt__qbuef)
        return impl_slice
    raise BodoError(
        f'getitem for BooleanArray with indexing type {ind} not supported.')


@overload(operator.setitem, no_unliteral=True)
def bool_arr_setitem(A, idx, val):
    if A != boolean_array:
        return
    if val == types.none or isinstance(val, types.optional):
        return
    kvwu__gmvw = (
        f"setitem for BooleanArray with indexing type {idx} received an incorrect 'value' type {val}."
        )
    if isinstance(idx, types.Integer):
        if types.unliteral(val) == types.bool_:

            def impl_scalar(A, idx, val):
                A._data[idx] = val
                bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap, idx, 1)
            return impl_scalar
        else:
            raise BodoError(kvwu__gmvw)
    if not (is_iterable_type(val) and val.dtype == types.bool_ or types.
        unliteral(val) == types.bool_):
        raise BodoError(kvwu__gmvw)
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
        for bvth__rbki in numba.parfors.parfor.internal_prange(len(A)):
            val = 0
            if not bodo.libs.array_kernels.isna(A, bvth__rbki):
                val = A[bvth__rbki]
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
            kfj__vshlm = np.empty(n, nb_dtype)
            for bvth__rbki in numba.parfors.parfor.internal_prange(n):
                kfj__vshlm[bvth__rbki] = data[bvth__rbki]
                if bodo.libs.array_kernels.isna(A, bvth__rbki):
                    kfj__vshlm[bvth__rbki] = np.nan
            return kfj__vshlm
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
    fnqd__mfl = op.__name__
    fnqd__mfl = ufunc_aliases.get(fnqd__mfl, fnqd__mfl)
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
    for gjliu__mtf in numba.np.ufunc_db.get_ufuncs():
        yha__kmide = create_op_overload(gjliu__mtf, gjliu__mtf.nin)
        overload(gjliu__mtf, no_unliteral=True)(yha__kmide)


_install_np_ufuncs()
skips = [operator.lt, operator.le, operator.eq, operator.ne, operator.gt,
    operator.ge, operator.add, operator.sub, operator.mul, operator.truediv,
    operator.floordiv, operator.pow, operator.mod, operator.or_, operator.and_]


def _install_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesArrayOperator._op_map.keys():
        if op in skips:
            continue
        yha__kmide = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(yha__kmide)


_install_binary_ops()


def _install_inplace_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesInplaceArrayOperator._op_map.keys(
        ):
        yha__kmide = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(yha__kmide)


_install_inplace_binary_ops()


def _install_unary_ops():
    for op in (operator.neg, operator.invert, operator.pos):
        yha__kmide = create_op_overload(op, 1)
        overload(op, no_unliteral=True)(yha__kmide)


_install_unary_ops()


@overload_method(BooleanArrayType, 'unique', no_unliteral=True)
def overload_unique(A):

    def impl_bool_arr(A):
        data = []
        eos__cpw = []
        bpc__obvv = False
        gjy__aixss = False
        spdar__jsl = False
        for bvth__rbki in range(len(A)):
            if bodo.libs.array_kernels.isna(A, bvth__rbki):
                if not bpc__obvv:
                    data.append(False)
                    eos__cpw.append(False)
                    bpc__obvv = True
                continue
            val = A[bvth__rbki]
            if val and not gjy__aixss:
                data.append(True)
                eos__cpw.append(True)
                gjy__aixss = True
            if not val and not spdar__jsl:
                data.append(False)
                eos__cpw.append(True)
                spdar__jsl = True
            if bpc__obvv and gjy__aixss and spdar__jsl:
                break
        bpxwr__wak = np.array(data)
        n = len(bpxwr__wak)
        bwpcr__arpru = 1
        vnqt__qbuef = np.empty(bwpcr__arpru, np.uint8)
        for vawl__ipu in range(n):
            bodo.libs.int_arr_ext.set_bit_to_arr(vnqt__qbuef, vawl__ipu,
                eos__cpw[vawl__ipu])
        return init_bool_array(bpxwr__wak, vnqt__qbuef)
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
    thlqv__psn = context.compile_internal(builder, func, toty(fromty), [val])
    return impl_ret_borrowed(context, builder, toty, thlqv__psn)


@overload(operator.setitem, no_unliteral=True)
def overload_np_array_setitem_bool_arr(A, idx, val):
    if isinstance(A, types.Array) and idx == boolean_array:

        def impl(A, idx, val):
            A[idx._data] = val
        return impl


def create_nullable_logical_op_overload(op):
    irng__bihw = op == operator.or_

    def bool_array_impl(val1, val2):
        if not is_valid_boolean_array_logical_op(val1, val2):
            return
        pdx__anitb = bodo.utils.utils.is_array_typ(val1, False)
        dgjs__emm = bodo.utils.utils.is_array_typ(val2, False)
        ejm__ysyw = 'val1' if pdx__anitb else 'val2'
        tvt__alao = 'def impl(val1, val2):\n'
        tvt__alao += f'  n = len({ejm__ysyw})\n'
        tvt__alao += (
            '  out_arr = bodo.utils.utils.alloc_type(n, bodo.boolean_array, (-1,))\n'
            )
        tvt__alao += '  for i in numba.parfors.parfor.internal_prange(n):\n'
        if pdx__anitb:
            null1 = 'bodo.libs.array_kernels.isna(val1, i)\n'
            huyvm__ajrmv = 'val1[i]'
        else:
            null1 = 'False\n'
            huyvm__ajrmv = 'val1'
        if dgjs__emm:
            null2 = 'bodo.libs.array_kernels.isna(val2, i)\n'
            rwgyb__mcl = 'val2[i]'
        else:
            null2 = 'False\n'
            rwgyb__mcl = 'val2'
        if irng__bihw:
            tvt__alao += f"""    result, isna_val = compute_or_body({null1}, {null2}, {huyvm__ajrmv}, {rwgyb__mcl})
"""
        else:
            tvt__alao += f"""    result, isna_val = compute_and_body({null1}, {null2}, {huyvm__ajrmv}, {rwgyb__mcl})
"""
        tvt__alao += '    out_arr[i] = result\n'
        tvt__alao += '    if isna_val:\n'
        tvt__alao += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
        tvt__alao += '      continue\n'
        tvt__alao += '  return out_arr\n'
        leyg__ekrzh = {}
        exec(tvt__alao, {'bodo': bodo, 'numba': numba, 'compute_and_body':
            compute_and_body, 'compute_or_body': compute_or_body}, leyg__ekrzh)
        impl = leyg__ekrzh['impl']
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
        gchd__hwx = boolean_array
        return gchd__hwx(*args)


def is_valid_boolean_array_logical_op(typ1, typ2):
    exprk__eiejd = (typ1 == bodo.boolean_array or typ2 == bodo.boolean_array
        ) and (bodo.utils.utils.is_array_typ(typ1, False) and typ1.dtype ==
        types.bool_ or typ1 == types.bool_) and (bodo.utils.utils.
        is_array_typ(typ2, False) and typ2.dtype == types.bool_ or typ2 ==
        types.bool_)
    return exprk__eiejd


def _install_nullable_logical_lowering():
    for op in (operator.and_, operator.or_):
        byysi__juair = create_boolean_array_logical_lower_impl(op)
        infer_global(op)(BooleanArrayLogicalOperatorTemplate)
        for typ1, typ2 in [(boolean_array, boolean_array), (boolean_array,
            types.bool_), (boolean_array, types.Array(types.bool_, 1, 'C'))]:
            lower_builtin(op, typ1, typ2)(byysi__juair)
            if typ1 != typ2:
                lower_builtin(op, typ2, typ1)(byysi__juair)


_install_nullable_logical_lowering()
