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
        lvtse__hekf = [('data', data_type), ('null_bitmap', nulls_type)]
        models.StructModel.__init__(self, dmm, fe_type, lvtse__hekf)


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
    mezsy__wpw = c.context.insert_const_string(c.builder.module, 'pandas')
    pwsc__bhptr = c.pyapi.import_module_noblock(mezsy__wpw)
    qbx__uokrj = c.pyapi.call_method(pwsc__bhptr, 'BooleanDtype', ())
    c.pyapi.decref(pwsc__bhptr)
    return qbx__uokrj


@unbox(BooleanDtype)
def unbox_boolean_dtype(typ, val, c):
    return NativeValue(c.context.get_dummy_value())


typeof_impl.register(pd.BooleanDtype)(lambda a, b: boolean_dtype)
type_callable(pd.BooleanDtype)(lambda c: lambda : boolean_dtype)
lower_builtin(pd.BooleanDtype)(lambda c, b, s, a: c.get_dummy_value())


@numba.njit
def gen_full_bitmap(n):
    wer__jgskq = n + 7 >> 3
    return np.full(wer__jgskq, 255, np.uint8)


def call_func_in_unbox(func, args, arg_typs, c):
    vuc__muyo = c.context.typing_context.resolve_value_type(func)
    sfyd__vjbnw = vuc__muyo.get_call_type(c.context.typing_context,
        arg_typs, {})
    vhp__vtw = c.context.get_function(vuc__muyo, sfyd__vjbnw)
    zgn__nhq = c.context.call_conv.get_function_type(sfyd__vjbnw.
        return_type, sfyd__vjbnw.args)
    zsuh__npd = c.builder.module
    rjilb__xiqva = lir.Function(zsuh__npd, zgn__nhq, name=zsuh__npd.
        get_unique_name('.func_conv'))
    rjilb__xiqva.linkage = 'internal'
    qnclp__qzkl = lir.IRBuilder(rjilb__xiqva.append_basic_block())
    dnepu__jbs = c.context.call_conv.decode_arguments(qnclp__qzkl,
        sfyd__vjbnw.args, rjilb__xiqva)
    bhoo__cfn = vhp__vtw(qnclp__qzkl, dnepu__jbs)
    c.context.call_conv.return_value(qnclp__qzkl, bhoo__cfn)
    fdns__hbl, tzye__prc = c.context.call_conv.call_function(c.builder,
        rjilb__xiqva, sfyd__vjbnw.return_type, sfyd__vjbnw.args, args)
    return tzye__prc


@unbox(BooleanArrayType)
def unbox_bool_array(typ, obj, c):
    uxcgz__ozyop = c.pyapi.call_method(obj, '__len__', ())
    n = c.pyapi.long_as_longlong(uxcgz__ozyop)
    c.pyapi.decref(uxcgz__ozyop)
    zgn__nhq = lir.FunctionType(lir.IntType(32), [lir.IntType(8).as_pointer()])
    moka__guee = cgutils.get_or_insert_function(c.builder.module, zgn__nhq,
        name='is_bool_array')
    zgn__nhq = lir.FunctionType(lir.IntType(32), [lir.IntType(8).as_pointer()])
    rjilb__xiqva = cgutils.get_or_insert_function(c.builder.module,
        zgn__nhq, name='is_pd_boolean_array')
    ftr__qqsgh = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    blmt__ygqvb = c.builder.call(rjilb__xiqva, [obj])
    ykaqq__lzcd = c.builder.icmp_unsigned('!=', blmt__ygqvb, blmt__ygqvb.
        type(0))
    with c.builder.if_else(ykaqq__lzcd) as (dodd__dcww, emy__zixqt):
        with dodd__dcww:
            nncr__ycrhf = c.pyapi.object_getattr_string(obj, '_data')
            ftr__qqsgh.data = c.pyapi.to_native_value(types.Array(types.
                bool_, 1, 'C'), nncr__ycrhf).value
            bskt__eux = c.pyapi.object_getattr_string(obj, '_mask')
            gstod__ftf = c.pyapi.to_native_value(types.Array(types.bool_, 1,
                'C'), bskt__eux).value
            wer__jgskq = c.builder.udiv(c.builder.add(n, lir.Constant(lir.
                IntType(64), 7)), lir.Constant(lir.IntType(64), 8))
            glju__vdftq = c.context.make_array(types.Array(types.bool_, 1, 'C')
                )(c.context, c.builder, gstod__ftf)
            rnm__svw = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
                types.Array(types.uint8, 1, 'C'), [wer__jgskq])
            zgn__nhq = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
                as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
            rjilb__xiqva = cgutils.get_or_insert_function(c.builder.module,
                zgn__nhq, name='mask_arr_to_bitmap')
            c.builder.call(rjilb__xiqva, [rnm__svw.data, glju__vdftq.data, n])
            ftr__qqsgh.null_bitmap = rnm__svw._getvalue()
            c.context.nrt.decref(c.builder, types.Array(types.bool_, 1, 'C'
                ), gstod__ftf)
            c.pyapi.decref(nncr__ycrhf)
            c.pyapi.decref(bskt__eux)
        with emy__zixqt:
            cwso__uia = c.builder.call(moka__guee, [obj])
            lfbx__rbvsc = c.builder.icmp_unsigned('!=', cwso__uia,
                cwso__uia.type(0))
            with c.builder.if_else(lfbx__rbvsc) as (eoqty__uun, uzty__wifz):
                with eoqty__uun:
                    ftr__qqsgh.data = c.pyapi.to_native_value(types.Array(
                        types.bool_, 1, 'C'), obj).value
                    ftr__qqsgh.null_bitmap = call_func_in_unbox(gen_full_bitmap
                        , (n,), (types.int64,), c)
                with uzty__wifz:
                    ftr__qqsgh.data = bodo.utils.utils._empty_nd_impl(c.
                        context, c.builder, types.Array(types.bool_, 1, 'C'
                        ), [n])._getvalue()
                    wer__jgskq = c.builder.udiv(c.builder.add(n, lir.
                        Constant(lir.IntType(64), 7)), lir.Constant(lir.
                        IntType(64), 8))
                    ftr__qqsgh.null_bitmap = bodo.utils.utils._empty_nd_impl(c
                        .context, c.builder, types.Array(types.uint8, 1,
                        'C'), [wer__jgskq])._getvalue()
                    xuqq__dxfne = c.context.make_array(types.Array(types.
                        bool_, 1, 'C'))(c.context, c.builder, ftr__qqsgh.data
                        ).data
                    tom__vhwi = c.context.make_array(types.Array(types.
                        uint8, 1, 'C'))(c.context, c.builder, ftr__qqsgh.
                        null_bitmap).data
                    zgn__nhq = lir.FunctionType(lir.VoidType(), [lir.
                        IntType(8).as_pointer(), lir.IntType(8).as_pointer(
                        ), lir.IntType(8).as_pointer(), lir.IntType(64)])
                    rjilb__xiqva = cgutils.get_or_insert_function(c.builder
                        .module, zgn__nhq, name='unbox_bool_array_obj')
                    c.builder.call(rjilb__xiqva, [obj, xuqq__dxfne,
                        tom__vhwi, n])
    return NativeValue(ftr__qqsgh._getvalue())


@box(BooleanArrayType)
def box_bool_arr(typ, val, c):
    ftr__qqsgh = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    data = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        ftr__qqsgh.data, c.env_manager)
    wxt__joms = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, ftr__qqsgh.null_bitmap).data
    uxcgz__ozyop = c.pyapi.call_method(data, '__len__', ())
    n = c.pyapi.long_as_longlong(uxcgz__ozyop)
    mezsy__wpw = c.context.insert_const_string(c.builder.module, 'numpy')
    wacn__jbptj = c.pyapi.import_module_noblock(mezsy__wpw)
    dcbn__nsj = c.pyapi.object_getattr_string(wacn__jbptj, 'bool_')
    gstod__ftf = c.pyapi.call_method(wacn__jbptj, 'empty', (uxcgz__ozyop,
        dcbn__nsj))
    wtxm__yygp = c.pyapi.object_getattr_string(gstod__ftf, 'ctypes')
    jbncc__ppwh = c.pyapi.object_getattr_string(wtxm__yygp, 'data')
    jvr__uzni = c.builder.inttoptr(c.pyapi.long_as_longlong(jbncc__ppwh),
        lir.IntType(8).as_pointer())
    with cgutils.for_range(c.builder, n) as aoc__jkknk:
        wsabf__wvz = aoc__jkknk.index
        cwpli__rrkv = c.builder.lshr(wsabf__wvz, lir.Constant(lir.IntType(
            64), 3))
        ipm__fhxne = c.builder.load(cgutils.gep(c.builder, wxt__joms,
            cwpli__rrkv))
        pkp__sdlgk = c.builder.trunc(c.builder.and_(wsabf__wvz, lir.
            Constant(lir.IntType(64), 7)), lir.IntType(8))
        val = c.builder.and_(c.builder.lshr(ipm__fhxne, pkp__sdlgk), lir.
            Constant(lir.IntType(8), 1))
        val = c.builder.xor(val, lir.Constant(lir.IntType(8), 1))
        vfuxg__xpgl = cgutils.gep(c.builder, jvr__uzni, wsabf__wvz)
        c.builder.store(val, vfuxg__xpgl)
    c.context.nrt.decref(c.builder, types.Array(types.uint8, 1, 'C'),
        ftr__qqsgh.null_bitmap)
    mezsy__wpw = c.context.insert_const_string(c.builder.module, 'pandas')
    pwsc__bhptr = c.pyapi.import_module_noblock(mezsy__wpw)
    ibis__vgb = c.pyapi.object_getattr_string(pwsc__bhptr, 'arrays')
    qbx__uokrj = c.pyapi.call_method(ibis__vgb, 'BooleanArray', (data,
        gstod__ftf))
    c.pyapi.decref(pwsc__bhptr)
    c.pyapi.decref(uxcgz__ozyop)
    c.pyapi.decref(wacn__jbptj)
    c.pyapi.decref(dcbn__nsj)
    c.pyapi.decref(wtxm__yygp)
    c.pyapi.decref(jbncc__ppwh)
    c.pyapi.decref(ibis__vgb)
    c.pyapi.decref(data)
    c.pyapi.decref(gstod__ftf)
    return qbx__uokrj


@lower_constant(BooleanArrayType)
def lower_constant_bool_arr(context, builder, typ, pyval):
    n = len(pyval)
    uaee__mpby = np.empty(n, np.bool_)
    vewe__oifs = np.empty(n + 7 >> 3, np.uint8)
    for wsabf__wvz, s in enumerate(pyval):
        nvcxp__qyo = pd.isna(s)
        bodo.libs.int_arr_ext.set_bit_to_arr(vewe__oifs, wsabf__wvz, int(
            not nvcxp__qyo))
        if not nvcxp__qyo:
            uaee__mpby[wsabf__wvz] = s
    aubna__jdn = context.get_constant_generic(builder, data_type, uaee__mpby)
    cyr__llgx = context.get_constant_generic(builder, nulls_type, vewe__oifs)
    return lir.Constant.literal_struct([aubna__jdn, cyr__llgx])


def lower_init_bool_array(context, builder, signature, args):
    xpas__cfix, stre__sscu = args
    ftr__qqsgh = cgutils.create_struct_proxy(signature.return_type)(context,
        builder)
    ftr__qqsgh.data = xpas__cfix
    ftr__qqsgh.null_bitmap = stre__sscu
    context.nrt.incref(builder, signature.args[0], xpas__cfix)
    context.nrt.incref(builder, signature.args[1], stre__sscu)
    return ftr__qqsgh._getvalue()


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
    puoh__jwod = args[0]
    if equiv_set.has_shape(puoh__jwod):
        return ArrayAnalysis.AnalyzeResult(shape=puoh__jwod, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_libs_bool_arr_ext_get_bool_arr_data = (
    get_bool_arr_data_equiv)


def init_bool_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    puoh__jwod = args[0]
    if equiv_set.has_shape(puoh__jwod):
        return ArrayAnalysis.AnalyzeResult(shape=puoh__jwod, pre=[])
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
    uaee__mpby = np.empty(n, dtype=np.bool_)
    hrsq__qcy = np.empty(n + 7 >> 3, dtype=np.uint8)
    return init_bool_array(uaee__mpby, hrsq__qcy)


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
            nca__shfny, zysao__dabdo = array_getitem_bool_index(A, ind)
            return init_bool_array(nca__shfny, zysao__dabdo)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            nca__shfny, zysao__dabdo = array_getitem_int_index(A, ind)
            return init_bool_array(nca__shfny, zysao__dabdo)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            nca__shfny, zysao__dabdo = array_getitem_slice_index(A, ind)
            return init_bool_array(nca__shfny, zysao__dabdo)
        return impl_slice
    raise BodoError(
        f'getitem for BooleanArray with indexing type {ind} not supported.')


@overload(operator.setitem, no_unliteral=True)
def bool_arr_setitem(A, idx, val):
    if A != boolean_array:
        return
    if val == types.none or isinstance(val, types.optional):
        return
    cddji__mceqc = (
        f"setitem for BooleanArray with indexing type {idx} received an incorrect 'value' type {val}."
        )
    if isinstance(idx, types.Integer):
        if types.unliteral(val) == types.bool_:

            def impl_scalar(A, idx, val):
                A._data[idx] = val
                bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap, idx, 1)
            return impl_scalar
        else:
            raise BodoError(cddji__mceqc)
    if not (is_iterable_type(val) and val.dtype == types.bool_ or types.
        unliteral(val) == types.bool_):
        raise BodoError(cddji__mceqc)
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
        for wsabf__wvz in numba.parfors.parfor.internal_prange(len(A)):
            val = 0
            if not bodo.libs.array_kernels.isna(A, wsabf__wvz):
                val = A[wsabf__wvz]
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
            xig__wtvu = np.empty(n, nb_dtype)
            for wsabf__wvz in numba.parfors.parfor.internal_prange(n):
                xig__wtvu[wsabf__wvz] = data[wsabf__wvz]
                if bodo.libs.array_kernels.isna(A, wsabf__wvz):
                    xig__wtvu[wsabf__wvz] = np.nan
            return xig__wtvu
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
    vpnvt__ygv = op.__name__
    vpnvt__ygv = ufunc_aliases.get(vpnvt__ygv, vpnvt__ygv)
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
    for cnlp__etuir in numba.np.ufunc_db.get_ufuncs():
        hkc__djz = create_op_overload(cnlp__etuir, cnlp__etuir.nin)
        overload(cnlp__etuir, no_unliteral=True)(hkc__djz)


_install_np_ufuncs()
skips = [operator.lt, operator.le, operator.eq, operator.ne, operator.gt,
    operator.ge, operator.add, operator.sub, operator.mul, operator.truediv,
    operator.floordiv, operator.pow, operator.mod, operator.or_, operator.and_]


def _install_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesArrayOperator._op_map.keys():
        if op in skips:
            continue
        hkc__djz = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(hkc__djz)


_install_binary_ops()


def _install_inplace_binary_ops():
    for op in numba.core.typing.npydecl.NumpyRulesInplaceArrayOperator._op_map.keys(
        ):
        hkc__djz = create_op_overload(op, 2)
        overload(op, no_unliteral=True)(hkc__djz)


_install_inplace_binary_ops()


def _install_unary_ops():
    for op in (operator.neg, operator.invert, operator.pos):
        hkc__djz = create_op_overload(op, 1)
        overload(op, no_unliteral=True)(hkc__djz)


_install_unary_ops()


@overload_method(BooleanArrayType, 'unique', no_unliteral=True)
def overload_unique(A):

    def impl_bool_arr(A):
        data = []
        pkp__sdlgk = []
        ycd__buz = False
        twmd__xaze = False
        aem__ghocy = False
        for wsabf__wvz in range(len(A)):
            if bodo.libs.array_kernels.isna(A, wsabf__wvz):
                if not ycd__buz:
                    data.append(False)
                    pkp__sdlgk.append(False)
                    ycd__buz = True
                continue
            val = A[wsabf__wvz]
            if val and not twmd__xaze:
                data.append(True)
                pkp__sdlgk.append(True)
                twmd__xaze = True
            if not val and not aem__ghocy:
                data.append(False)
                pkp__sdlgk.append(True)
                aem__ghocy = True
            if ycd__buz and twmd__xaze and aem__ghocy:
                break
        nca__shfny = np.array(data)
        n = len(nca__shfny)
        wer__jgskq = 1
        zysao__dabdo = np.empty(wer__jgskq, np.uint8)
        for zyhli__vgrb in range(n):
            bodo.libs.int_arr_ext.set_bit_to_arr(zysao__dabdo, zyhli__vgrb,
                pkp__sdlgk[zyhli__vgrb])
        return init_bool_array(nca__shfny, zysao__dabdo)
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
    qbx__uokrj = context.compile_internal(builder, func, toty(fromty), [val])
    return impl_ret_borrowed(context, builder, toty, qbx__uokrj)


@overload(operator.setitem, no_unliteral=True)
def overload_np_array_setitem_bool_arr(A, idx, val):
    if isinstance(A, types.Array) and idx == boolean_array:

        def impl(A, idx, val):
            A[idx._data] = val
        return impl


def create_nullable_logical_op_overload(op):
    uupl__zej = op == operator.or_

    def bool_array_impl(val1, val2):
        if not is_valid_boolean_array_logical_op(val1, val2):
            return
        bqm__itzhs = bodo.utils.utils.is_array_typ(val1, False)
        fud__rnnlq = bodo.utils.utils.is_array_typ(val2, False)
        otnrz__spoy = 'val1' if bqm__itzhs else 'val2'
        uvjl__tmbd = 'def impl(val1, val2):\n'
        uvjl__tmbd += f'  n = len({otnrz__spoy})\n'
        uvjl__tmbd += (
            '  out_arr = bodo.utils.utils.alloc_type(n, bodo.boolean_array, (-1,))\n'
            )
        uvjl__tmbd += '  for i in numba.parfors.parfor.internal_prange(n):\n'
        if bqm__itzhs:
            null1 = 'bodo.libs.array_kernels.isna(val1, i)\n'
            sfm__hpkp = 'val1[i]'
        else:
            null1 = 'False\n'
            sfm__hpkp = 'val1'
        if fud__rnnlq:
            null2 = 'bodo.libs.array_kernels.isna(val2, i)\n'
            giyyj__mzr = 'val2[i]'
        else:
            null2 = 'False\n'
            giyyj__mzr = 'val2'
        if uupl__zej:
            uvjl__tmbd += f"""    result, isna_val = compute_or_body({null1}, {null2}, {sfm__hpkp}, {giyyj__mzr})
"""
        else:
            uvjl__tmbd += f"""    result, isna_val = compute_and_body({null1}, {null2}, {sfm__hpkp}, {giyyj__mzr})
"""
        uvjl__tmbd += '    out_arr[i] = result\n'
        uvjl__tmbd += '    if isna_val:\n'
        uvjl__tmbd += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
        uvjl__tmbd += '      continue\n'
        uvjl__tmbd += '  return out_arr\n'
        xvgwi__asvly = {}
        exec(uvjl__tmbd, {'bodo': bodo, 'numba': numba, 'compute_and_body':
            compute_and_body, 'compute_or_body': compute_or_body}, xvgwi__asvly
            )
        impl = xvgwi__asvly['impl']
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
        kpaap__ihy = boolean_array
        return kpaap__ihy(*args)


def is_valid_boolean_array_logical_op(typ1, typ2):
    nba__noikq = (typ1 == bodo.boolean_array or typ2 == bodo.boolean_array
        ) and (bodo.utils.utils.is_array_typ(typ1, False) and typ1.dtype ==
        types.bool_ or typ1 == types.bool_) and (bodo.utils.utils.
        is_array_typ(typ2, False) and typ2.dtype == types.bool_ or typ2 ==
        types.bool_)
    return nba__noikq


def _install_nullable_logical_lowering():
    for op in (operator.and_, operator.or_):
        njk__phno = create_boolean_array_logical_lower_impl(op)
        infer_global(op)(BooleanArrayLogicalOperatorTemplate)
        for typ1, typ2 in [(boolean_array, boolean_array), (boolean_array,
            types.bool_), (boolean_array, types.Array(types.bool_, 1, 'C'))]:
            lower_builtin(op, typ1, typ2)(njk__phno)
            if typ1 != typ2:
                lower_builtin(op, typ2, typ1)(njk__phno)


_install_nullable_logical_lowering()
