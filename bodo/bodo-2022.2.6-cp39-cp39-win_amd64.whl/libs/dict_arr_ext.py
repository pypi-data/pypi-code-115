"""Dictionary encoded array data type, similar to DictionaryArray of Arrow.
The purpose is to improve memory consumption and performance over string_array_type for
string arrays that have a lot of repetitive values (typical in practice).
Can be extended to be used with types other than strings as well.
See:
https://bodo.atlassian.net/browse/BE-2295
https://bodo.atlassian.net/wiki/spaces/B/pages/993722369/Dictionary-encoded+String+Array+Support+in+Parquet+read+compute+...
https://arrow.apache.org/docs/cpp/api/array.html#dictionary-encoded
"""
import operator
import re
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
import pyarrow as pa
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import impl_ret_new_ref, lower_builtin, lower_constant
from numba.extending import NativeValue, box, intrinsic, lower_cast, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_model, typeof_impl, unbox
import bodo
from bodo.libs import hstr_ext
from bodo.libs.bool_arr_ext import init_bool_array
from bodo.libs.int_arr_ext import IntegerArrayType
from bodo.libs.str_arr_ext import StringArrayType, get_str_arr_item_length, overload_str_arr_astype, pre_alloc_string_array
from bodo.utils.typing import BodoArrayIterator, is_overload_none, raise_bodo_error
ll.add_symbol('box_dict_str_array', hstr_ext.box_dict_str_array)
dict_indices_arr_type = IntegerArrayType(types.int32)


class DictionaryArrayType(types.IterableType, types.ArrayCompatible):

    def __init__(self, arr_data_type):
        self.data = arr_data_type
        super(DictionaryArrayType, self).__init__(name=
            f'DictionaryArrayType({arr_data_type})')

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def iterator_type(self):
        return BodoArrayIterator(self)

    @property
    def dtype(self):
        return self.data.dtype

    def copy(self):
        return DictionaryArrayType(self.data)

    @property
    def indices_type(self):
        return dict_indices_arr_type

    @property
    def indices_dtype(self):
        return dict_indices_arr_type.dtype

    def unify(self, typingctx, other):
        if other == bodo.string_array_type:
            return bodo.string_array_type


dict_str_arr_type = DictionaryArrayType(bodo.string_array_type)


@register_model(DictionaryArrayType)
class DictionaryArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        zmhy__cxc = [('data', fe_type.data), ('indices',
            dict_indices_arr_type), ('has_global_dictionary', types.bool_)]
        models.StructModel.__init__(self, dmm, fe_type, zmhy__cxc)


make_attribute_wrapper(DictionaryArrayType, 'data', '_data')
make_attribute_wrapper(DictionaryArrayType, 'indices', '_indices')
make_attribute_wrapper(DictionaryArrayType, 'has_global_dictionary',
    '_has_global_dictionary')
lower_builtin('getiter', dict_str_arr_type)(numba.np.arrayobj.getiter_array)


@intrinsic
def init_dict_arr(typingctx, data_t, indices_t, glob_dict_t=None):
    assert indices_t == dict_indices_arr_type, 'invalid indices type for dict array'

    def codegen(context, builder, signature, args):
        bamka__pxee, fqio__mgrf, uowa__gbxu = args
        myzg__wpmv = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        myzg__wpmv.data = bamka__pxee
        myzg__wpmv.indices = fqio__mgrf
        myzg__wpmv.has_global_dictionary = uowa__gbxu
        context.nrt.incref(builder, signature.args[0], bamka__pxee)
        context.nrt.incref(builder, signature.args[1], fqio__mgrf)
        return myzg__wpmv._getvalue()
    aea__qpvb = DictionaryArrayType(data_t)
    woo__cclcv = aea__qpvb(data_t, indices_t, types.bool_)
    return woo__cclcv, codegen


@typeof_impl.register(pa.DictionaryArray)
def typeof_dict_value(val, c):
    if val.type.value_type == pa.string():
        return dict_str_arr_type


def to_pa_dict_arr(A):
    if isinstance(A, pa.DictionaryArray):
        return A
    for oqa__tzbz in range(len(A)):
        if pd.isna(A[oqa__tzbz]):
            A[oqa__tzbz] = None
    return pa.array(A).dictionary_encode()


@unbox(DictionaryArrayType)
def unbox_dict_arr(typ, val, c):
    if bodo.hiframes.boxing._use_dict_str_type:
        srxg__jyze = c.pyapi.unserialize(c.pyapi.serialize_object(
            to_pa_dict_arr))
        val = c.pyapi.call_function_objargs(srxg__jyze, [val])
        c.pyapi.decref(srxg__jyze)
    myzg__wpmv = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    fgc__yku = c.pyapi.object_getattr_string(val, 'dictionary')
    sqx__jco = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_, 
        False))
    eqg__lmf = c.pyapi.call_method(fgc__yku, 'to_numpy', (sqx__jco,))
    myzg__wpmv.data = c.unbox(typ.data, eqg__lmf).value
    rndz__voof = c.pyapi.object_getattr_string(val, 'indices')
    ljdas__liiap = c.context.insert_const_string(c.builder.module, 'pandas')
    raeh__ncuti = c.pyapi.import_module_noblock(ljdas__liiap)
    yfzc__dfw = c.pyapi.string_from_constant_string('Int32')
    clvc__ltdxa = c.pyapi.call_method(raeh__ncuti, 'array', (rndz__voof,
        yfzc__dfw))
    myzg__wpmv.indices = c.unbox(dict_indices_arr_type, clvc__ltdxa).value
    myzg__wpmv.has_global_dictionary = c.context.get_constant(types.bool_, 
        False)
    c.pyapi.decref(fgc__yku)
    c.pyapi.decref(sqx__jco)
    c.pyapi.decref(eqg__lmf)
    c.pyapi.decref(rndz__voof)
    c.pyapi.decref(raeh__ncuti)
    c.pyapi.decref(yfzc__dfw)
    c.pyapi.decref(clvc__ltdxa)
    if bodo.hiframes.boxing._use_dict_str_type:
        c.pyapi.decref(val)
    tvd__eklhk = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(myzg__wpmv._getvalue(), is_error=tvd__eklhk)


@box(DictionaryArrayType)
def box_dict_arr(typ, val, c):
    myzg__wpmv = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    if typ == dict_str_arr_type:
        c.context.nrt.incref(c.builder, typ.data, myzg__wpmv.data)
        eyut__mjd = c.box(typ.data, myzg__wpmv.data)
        dijal__nffbq = cgutils.create_struct_proxy(dict_indices_arr_type)(c
            .context, c.builder, myzg__wpmv.indices)
        alapf__neec = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), c.
            pyapi.pyobj, lir.IntType(32).as_pointer(), lir.IntType(8).
            as_pointer()])
        pin__arjal = cgutils.get_or_insert_function(c.builder.module,
            alapf__neec, name='box_dict_str_array')
        kqo__frr = cgutils.create_struct_proxy(types.Array(types.int32, 1, 'C')
            )(c.context, c.builder, dijal__nffbq.data)
        xbzsu__kmttz = c.builder.extract_value(kqo__frr.shape, 0)
        dkvbp__kejws = kqo__frr.data
        ama__jjdro = cgutils.create_struct_proxy(types.Array(types.int8, 1,
            'C'))(c.context, c.builder, dijal__nffbq.null_bitmap).data
        eqg__lmf = c.builder.call(pin__arjal, [xbzsu__kmttz, eyut__mjd,
            dkvbp__kejws, ama__jjdro])
        c.pyapi.decref(eyut__mjd)
    else:
        ljdas__liiap = c.context.insert_const_string(c.builder.module,
            'pyarrow')
        encnd__oait = c.pyapi.import_module_noblock(ljdas__liiap)
        rhgv__git = c.pyapi.object_getattr_string(encnd__oait,
            'DictionaryArray')
        c.context.nrt.incref(c.builder, typ.data, myzg__wpmv.data)
        eyut__mjd = c.box(typ.data, myzg__wpmv.data)
        c.context.nrt.incref(c.builder, dict_indices_arr_type, myzg__wpmv.
            indices)
        rndz__voof = c.box(dict_indices_arr_type, myzg__wpmv.indices)
        aotmf__mlazd = c.pyapi.call_method(rhgv__git, 'from_arrays', (
            rndz__voof, eyut__mjd))
        sqx__jco = c.pyapi.bool_from_bool(c.context.get_constant(types.
            bool_, False))
        eqg__lmf = c.pyapi.call_method(aotmf__mlazd, 'to_numpy', (sqx__jco,))
        c.pyapi.decref(encnd__oait)
        c.pyapi.decref(eyut__mjd)
        c.pyapi.decref(rndz__voof)
        c.pyapi.decref(rhgv__git)
        c.pyapi.decref(aotmf__mlazd)
        c.pyapi.decref(sqx__jco)
    c.context.nrt.decref(c.builder, typ, val)
    return eqg__lmf


@overload(len, no_unliteral=True)
def overload_dict_arr_len(A):
    if isinstance(A, DictionaryArrayType):
        return lambda A: len(A._indices)


@overload_attribute(DictionaryArrayType, 'shape')
def overload_dict_arr_shape(A):
    return lambda A: (len(A._indices),)


@overload_attribute(DictionaryArrayType, 'ndim')
def overload_dict_arr_ndim(A):
    return lambda A: 1


@overload_attribute(DictionaryArrayType, 'size')
def overload_dict_arr_size(A):
    return lambda A: len(A._indices)


@overload_method(DictionaryArrayType, 'tolist', no_unliteral=True)
def overload_dict_arr_tolist(A):
    return lambda A: list(A)


overload_method(DictionaryArrayType, 'astype', no_unliteral=True)(
    overload_str_arr_astype)


@overload_method(DictionaryArrayType, 'copy', no_unliteral=True)
def overload_dict_arr_copy(A):

    def copy_impl(A):
        return init_dict_arr(A._data.copy(), A._indices.copy(), A.
            _has_global_dictionary)
    return copy_impl


@overload_attribute(DictionaryArrayType, 'dtype')
def overload_dict_arr_dtype(A):
    return lambda A: A._data.dtype


@overload_attribute(DictionaryArrayType, 'nbytes')
def dict_arr_nbytes_overload(A):
    return lambda A: A._data.nbytes + A._indices.nbytes


@lower_constant(DictionaryArrayType)
def lower_constant_dict_arr(context, builder, typ, pyval):
    if bodo.hiframes.boxing._use_dict_str_type and isinstance(pyval, np.ndarray
        ):
        pyval = pa.array(pyval).dictionary_encode()
    kqylx__kvo = pyval.dictionary.to_numpy(False)
    kbsw__qoa = pd.array(pyval.indices, 'Int32')
    kqylx__kvo = context.get_constant_generic(builder, typ.data, kqylx__kvo)
    kbsw__qoa = context.get_constant_generic(builder, dict_indices_arr_type,
        kbsw__qoa)
    fjvr__rcpbp = context.get_constant(types.bool_, False)
    lwbm__jge = lir.Constant.literal_struct([kqylx__kvo, kbsw__qoa,
        fjvr__rcpbp])
    return lwbm__jge


@overload(operator.getitem, no_unliteral=True)
def dict_arr_getitem(A, ind):
    if not isinstance(A, DictionaryArrayType):
        return
    if isinstance(ind, types.Integer):

        def dict_arr_getitem_impl(A, ind):
            if bodo.libs.array_kernels.isna(A._indices, ind):
                return ''
            zjziz__ksh = A._indices[ind]
            return A._data[zjziz__ksh]
        return dict_arr_getitem_impl
    return lambda A, ind: init_dict_arr(A._data, A._indices[ind], A.
        _has_global_dictionary)


@overload_method(DictionaryArrayType, '_decode', no_unliteral=True)
def overload_dict_arr_decode(A):

    def impl(A):
        bamka__pxee = A._data
        fqio__mgrf = A._indices
        xbzsu__kmttz = len(fqio__mgrf)
        qemdk__ydqvo = [get_str_arr_item_length(bamka__pxee, oqa__tzbz) for
            oqa__tzbz in range(len(bamka__pxee))]
        rog__nva = 0
        for oqa__tzbz in range(xbzsu__kmttz):
            if not bodo.libs.array_kernels.isna(fqio__mgrf, oqa__tzbz):
                rog__nva += qemdk__ydqvo[fqio__mgrf[oqa__tzbz]]
        ctob__jbq = pre_alloc_string_array(xbzsu__kmttz, rog__nva)
        for oqa__tzbz in range(xbzsu__kmttz):
            if bodo.libs.array_kernels.isna(fqio__mgrf, oqa__tzbz):
                bodo.libs.array_kernels.setna(ctob__jbq, oqa__tzbz)
                continue
            ind = fqio__mgrf[oqa__tzbz]
            if bodo.libs.array_kernels.isna(bamka__pxee, ind):
                bodo.libs.array_kernels.setna(ctob__jbq, oqa__tzbz)
                continue
            ctob__jbq[oqa__tzbz] = bamka__pxee[ind]
        return ctob__jbq
    return impl


@overload(operator.setitem)
def dict_arr_setitem(A, idx, val):
    if not isinstance(A, DictionaryArrayType):
        return
    raise_bodo_error(
        "DictionaryArrayType is read-only and doesn't support setitem yet")


@numba.njit(no_cpython_wrapper=True)
def find_dict_ind(arr, val):
    zjziz__ksh = -1
    bamka__pxee = arr._data
    for oqa__tzbz in range(len(bamka__pxee)):
        if bodo.libs.array_kernels.isna(bamka__pxee, oqa__tzbz):
            continue
        if bamka__pxee[oqa__tzbz] == val:
            zjziz__ksh = oqa__tzbz
            break
    return zjziz__ksh


@numba.njit(no_cpython_wrapper=True)
def dict_arr_eq(arr, val):
    xbzsu__kmttz = len(arr)
    zjziz__ksh = find_dict_ind(arr, val)
    if zjziz__ksh == -1:
        return init_bool_array(np.full(xbzsu__kmttz, False, np.bool_), arr.
            _indices._null_bitmap.copy())
    return arr._indices == zjziz__ksh


@numba.njit(no_cpython_wrapper=True)
def dict_arr_ne(arr, val):
    xbzsu__kmttz = len(arr)
    zjziz__ksh = find_dict_ind(arr, val)
    if zjziz__ksh == -1:
        return init_bool_array(np.full(xbzsu__kmttz, True, np.bool_), arr.
            _indices._null_bitmap.copy())
    return arr._indices != zjziz__ksh


def get_binary_op_overload(op, lhs, rhs):
    if op == operator.eq:
        if lhs == dict_str_arr_type and types.unliteral(rhs
            ) == bodo.string_type:
            return lambda lhs, rhs: dict_arr_eq(lhs, rhs)
        if rhs == dict_str_arr_type and types.unliteral(lhs
            ) == bodo.string_type:
            return lambda lhs, rhs: dict_arr_eq(rhs, lhs)
    if op == operator.ne:
        if lhs == dict_str_arr_type and types.unliteral(rhs
            ) == bodo.string_type:
            return lambda lhs, rhs: dict_arr_ne(lhs, rhs)
        if rhs == dict_str_arr_type and types.unliteral(lhs
            ) == bodo.string_type:
            return lambda lhs, rhs: dict_arr_ne(rhs, lhs)


def convert_dict_arr_to_int(arr, dtype):
    return arr


@overload(convert_dict_arr_to_int)
def convert_dict_arr_to_int_overload(arr, dtype):

    def impl(arr, dtype):
        jostm__sntu = arr._data
        gzwgq__redn = bodo.libs.int_arr_ext.alloc_int_array(len(jostm__sntu
            ), dtype)
        for pfmpf__luj in range(len(jostm__sntu)):
            if bodo.libs.array_kernels.isna(jostm__sntu, pfmpf__luj):
                bodo.libs.array_kernels.setna(gzwgq__redn, pfmpf__luj)
                continue
            gzwgq__redn[pfmpf__luj] = np.int64(jostm__sntu[pfmpf__luj])
        xbzsu__kmttz = len(arr)
        fqio__mgrf = arr._indices
        ctob__jbq = bodo.libs.int_arr_ext.alloc_int_array(xbzsu__kmttz, dtype)
        for oqa__tzbz in range(xbzsu__kmttz):
            if bodo.libs.array_kernels.isna(fqio__mgrf, oqa__tzbz):
                bodo.libs.array_kernels.setna(ctob__jbq, oqa__tzbz)
                continue
            ctob__jbq[oqa__tzbz] = gzwgq__redn[fqio__mgrf[oqa__tzbz]]
        return ctob__jbq
    return impl


def cat_dict_str(arrs, sep):
    pass


@overload(cat_dict_str)
def cat_dict_str_overload(arrs, sep):
    njpmu__cutpp = len(arrs)
    oowc__xyoyz = 'def impl(arrs, sep):\n'
    oowc__xyoyz += '  ind_map = {}\n'
    oowc__xyoyz += '  out_strs = []\n'
    oowc__xyoyz += '  n = len(arrs[0])\n'
    for oqa__tzbz in range(njpmu__cutpp):
        oowc__xyoyz += f'  indices{oqa__tzbz} = arrs[{oqa__tzbz}]._indices\n'
    for oqa__tzbz in range(njpmu__cutpp):
        oowc__xyoyz += f'  data{oqa__tzbz} = arrs[{oqa__tzbz}]._data\n'
    oowc__xyoyz += (
        '  out_indices = bodo.libs.int_arr_ext.alloc_int_array(n, np.int32)\n')
    oowc__xyoyz += '  for i in range(n):\n'
    ode__rnw = ' or '.join([
        f'bodo.libs.array_kernels.isna(arrs[{oqa__tzbz}], i)' for oqa__tzbz in
        range(njpmu__cutpp)])
    oowc__xyoyz += f'    if {ode__rnw}:\n'
    oowc__xyoyz += '      bodo.libs.array_kernels.setna(out_indices, i)\n'
    oowc__xyoyz += '      continue\n'
    for oqa__tzbz in range(njpmu__cutpp):
        oowc__xyoyz += f'    ind{oqa__tzbz} = indices{oqa__tzbz}[i]\n'
    kxn__neuah = '(' + ', '.join(f'ind{oqa__tzbz}' for oqa__tzbz in range(
        njpmu__cutpp)) + ')'
    oowc__xyoyz += f'    if {kxn__neuah} not in ind_map:\n'
    oowc__xyoyz += '      out_ind = len(out_strs)\n'
    oowc__xyoyz += f'      ind_map[{kxn__neuah}] = out_ind\n'
    uksd__evxw = "''" if is_overload_none(sep) else 'sep'
    uigq__ssv = ', '.join([f'data{oqa__tzbz}[ind{oqa__tzbz}]' for oqa__tzbz in
        range(njpmu__cutpp)])
    oowc__xyoyz += f'      v = {uksd__evxw}.join([{uigq__ssv}])\n'
    oowc__xyoyz += '      out_strs.append(v)\n'
    oowc__xyoyz += '    else:\n'
    oowc__xyoyz += f'      out_ind = ind_map[{kxn__neuah}]\n'
    oowc__xyoyz += '    out_indices[i] = out_ind\n'
    oowc__xyoyz += (
        '  out_str_arr = bodo.libs.str_arr_ext.str_arr_from_sequence(out_strs)\n'
        )
    oowc__xyoyz += """  return bodo.libs.dict_arr_ext.init_dict_arr(out_str_arr, out_indices, False)
"""
    pedc__elpmk = {}
    exec(oowc__xyoyz, {'bodo': bodo, 'numba': numba, 'np': np}, pedc__elpmk)
    impl = pedc__elpmk['impl']
    return impl


@lower_cast(DictionaryArrayType, StringArrayType)
def cast_dict_str_arr_to_str_arr(context, builder, fromty, toty, val):
    if fromty != dict_str_arr_type:
        return
    zwo__byjg = bodo.utils.typing.decode_if_dict_array_overload(fromty)
    woo__cclcv = toty(fromty)
    sbjb__wemf = context.compile_internal(builder, zwo__byjg, woo__cclcv, (
        val,))
    return impl_ret_new_ref(context, builder, toty, sbjb__wemf)


@numba.jit(cache=True, no_cpython_wrapper=True)
def str_replace(arr, pat, repl, flags, regex):
    kqylx__kvo = arr._data
    zsqw__hcei = len(kqylx__kvo)
    wrn__fakq = pre_alloc_string_array(zsqw__hcei, -1)
    if regex:
        gja__pny = re.compile(pat, flags)
        for oqa__tzbz in range(zsqw__hcei):
            if bodo.libs.array_kernels.isna(kqylx__kvo, oqa__tzbz):
                bodo.libs.array_kernels.setna(wrn__fakq, oqa__tzbz)
                continue
            wrn__fakq[oqa__tzbz] = gja__pny.sub(repl=repl, string=
                kqylx__kvo[oqa__tzbz])
    else:
        for oqa__tzbz in range(zsqw__hcei):
            if bodo.libs.array_kernels.isna(kqylx__kvo, oqa__tzbz):
                bodo.libs.array_kernels.setna(wrn__fakq, oqa__tzbz)
                continue
            wrn__fakq[oqa__tzbz] = kqylx__kvo[oqa__tzbz].replace(pat, repl)
    return init_dict_arr(wrn__fakq, arr._indices.copy(), arr.
        _has_global_dictionary)
