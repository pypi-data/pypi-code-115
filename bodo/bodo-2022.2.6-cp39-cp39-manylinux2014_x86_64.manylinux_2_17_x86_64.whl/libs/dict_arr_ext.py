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
        laib__kox = [('data', fe_type.data), ('indices',
            dict_indices_arr_type), ('has_global_dictionary', types.bool_)]
        models.StructModel.__init__(self, dmm, fe_type, laib__kox)


make_attribute_wrapper(DictionaryArrayType, 'data', '_data')
make_attribute_wrapper(DictionaryArrayType, 'indices', '_indices')
make_attribute_wrapper(DictionaryArrayType, 'has_global_dictionary',
    '_has_global_dictionary')
lower_builtin('getiter', dict_str_arr_type)(numba.np.arrayobj.getiter_array)


@intrinsic
def init_dict_arr(typingctx, data_t, indices_t, glob_dict_t=None):
    assert indices_t == dict_indices_arr_type, 'invalid indices type for dict array'

    def codegen(context, builder, signature, args):
        mlv__bomm, qlp__jno, lpngt__ddozz = args
        hhgrj__kxe = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        hhgrj__kxe.data = mlv__bomm
        hhgrj__kxe.indices = qlp__jno
        hhgrj__kxe.has_global_dictionary = lpngt__ddozz
        context.nrt.incref(builder, signature.args[0], mlv__bomm)
        context.nrt.incref(builder, signature.args[1], qlp__jno)
        return hhgrj__kxe._getvalue()
    yxgob__nrz = DictionaryArrayType(data_t)
    tbojo__okbcr = yxgob__nrz(data_t, indices_t, types.bool_)
    return tbojo__okbcr, codegen


@typeof_impl.register(pa.DictionaryArray)
def typeof_dict_value(val, c):
    if val.type.value_type == pa.string():
        return dict_str_arr_type


def to_pa_dict_arr(A):
    if isinstance(A, pa.DictionaryArray):
        return A
    for zgu__vdr in range(len(A)):
        if pd.isna(A[zgu__vdr]):
            A[zgu__vdr] = None
    return pa.array(A).dictionary_encode()


@unbox(DictionaryArrayType)
def unbox_dict_arr(typ, val, c):
    if bodo.hiframes.boxing._use_dict_str_type:
        phcw__rjta = c.pyapi.unserialize(c.pyapi.serialize_object(
            to_pa_dict_arr))
        val = c.pyapi.call_function_objargs(phcw__rjta, [val])
        c.pyapi.decref(phcw__rjta)
    hhgrj__kxe = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    ogk__ylcgy = c.pyapi.object_getattr_string(val, 'dictionary')
    kvb__rkj = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_, 
        False))
    oqlh__kagna = c.pyapi.call_method(ogk__ylcgy, 'to_numpy', (kvb__rkj,))
    hhgrj__kxe.data = c.unbox(typ.data, oqlh__kagna).value
    yxqs__dsia = c.pyapi.object_getattr_string(val, 'indices')
    tpl__cde = c.context.insert_const_string(c.builder.module, 'pandas')
    vrpdd__vpe = c.pyapi.import_module_noblock(tpl__cde)
    lfz__qqab = c.pyapi.string_from_constant_string('Int32')
    rzj__sjspm = c.pyapi.call_method(vrpdd__vpe, 'array', (yxqs__dsia,
        lfz__qqab))
    hhgrj__kxe.indices = c.unbox(dict_indices_arr_type, rzj__sjspm).value
    hhgrj__kxe.has_global_dictionary = c.context.get_constant(types.bool_, 
        False)
    c.pyapi.decref(ogk__ylcgy)
    c.pyapi.decref(kvb__rkj)
    c.pyapi.decref(oqlh__kagna)
    c.pyapi.decref(yxqs__dsia)
    c.pyapi.decref(vrpdd__vpe)
    c.pyapi.decref(lfz__qqab)
    c.pyapi.decref(rzj__sjspm)
    if bodo.hiframes.boxing._use_dict_str_type:
        c.pyapi.decref(val)
    abdgp__amtlo = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(hhgrj__kxe._getvalue(), is_error=abdgp__amtlo)


@box(DictionaryArrayType)
def box_dict_arr(typ, val, c):
    hhgrj__kxe = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    if typ == dict_str_arr_type:
        c.context.nrt.incref(c.builder, typ.data, hhgrj__kxe.data)
        the__kuw = c.box(typ.data, hhgrj__kxe.data)
        atax__wiml = cgutils.create_struct_proxy(dict_indices_arr_type)(c.
            context, c.builder, hhgrj__kxe.indices)
        ksl__zvb = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), c.
            pyapi.pyobj, lir.IntType(32).as_pointer(), lir.IntType(8).
            as_pointer()])
        abcmz__ijrc = cgutils.get_or_insert_function(c.builder.module,
            ksl__zvb, name='box_dict_str_array')
        strjh__shh = cgutils.create_struct_proxy(types.Array(types.int32, 1,
            'C'))(c.context, c.builder, atax__wiml.data)
        xzo__hvv = c.builder.extract_value(strjh__shh.shape, 0)
        gps__rai = strjh__shh.data
        iiiv__kfirg = cgutils.create_struct_proxy(types.Array(types.int8, 1,
            'C'))(c.context, c.builder, atax__wiml.null_bitmap).data
        oqlh__kagna = c.builder.call(abcmz__ijrc, [xzo__hvv, the__kuw,
            gps__rai, iiiv__kfirg])
        c.pyapi.decref(the__kuw)
    else:
        tpl__cde = c.context.insert_const_string(c.builder.module, 'pyarrow')
        pmbku__gpi = c.pyapi.import_module_noblock(tpl__cde)
        fst__vab = c.pyapi.object_getattr_string(pmbku__gpi, 'DictionaryArray')
        c.context.nrt.incref(c.builder, typ.data, hhgrj__kxe.data)
        the__kuw = c.box(typ.data, hhgrj__kxe.data)
        c.context.nrt.incref(c.builder, dict_indices_arr_type, hhgrj__kxe.
            indices)
        yxqs__dsia = c.box(dict_indices_arr_type, hhgrj__kxe.indices)
        ehoto__jyis = c.pyapi.call_method(fst__vab, 'from_arrays', (
            yxqs__dsia, the__kuw))
        kvb__rkj = c.pyapi.bool_from_bool(c.context.get_constant(types.
            bool_, False))
        oqlh__kagna = c.pyapi.call_method(ehoto__jyis, 'to_numpy', (kvb__rkj,))
        c.pyapi.decref(pmbku__gpi)
        c.pyapi.decref(the__kuw)
        c.pyapi.decref(yxqs__dsia)
        c.pyapi.decref(fst__vab)
        c.pyapi.decref(ehoto__jyis)
        c.pyapi.decref(kvb__rkj)
    c.context.nrt.decref(c.builder, typ, val)
    return oqlh__kagna


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
    gav__oss = pyval.dictionary.to_numpy(False)
    ctifz__qmyps = pd.array(pyval.indices, 'Int32')
    gav__oss = context.get_constant_generic(builder, typ.data, gav__oss)
    ctifz__qmyps = context.get_constant_generic(builder,
        dict_indices_arr_type, ctifz__qmyps)
    qaiod__rkca = context.get_constant(types.bool_, False)
    hraak__vlpx = lir.Constant.literal_struct([gav__oss, ctifz__qmyps,
        qaiod__rkca])
    return hraak__vlpx


@overload(operator.getitem, no_unliteral=True)
def dict_arr_getitem(A, ind):
    if not isinstance(A, DictionaryArrayType):
        return
    if isinstance(ind, types.Integer):

        def dict_arr_getitem_impl(A, ind):
            if bodo.libs.array_kernels.isna(A._indices, ind):
                return ''
            pls__cqnp = A._indices[ind]
            return A._data[pls__cqnp]
        return dict_arr_getitem_impl
    return lambda A, ind: init_dict_arr(A._data, A._indices[ind], A.
        _has_global_dictionary)


@overload_method(DictionaryArrayType, '_decode', no_unliteral=True)
def overload_dict_arr_decode(A):

    def impl(A):
        mlv__bomm = A._data
        qlp__jno = A._indices
        xzo__hvv = len(qlp__jno)
        qzlx__ivd = [get_str_arr_item_length(mlv__bomm, zgu__vdr) for
            zgu__vdr in range(len(mlv__bomm))]
        naygq__rxqt = 0
        for zgu__vdr in range(xzo__hvv):
            if not bodo.libs.array_kernels.isna(qlp__jno, zgu__vdr):
                naygq__rxqt += qzlx__ivd[qlp__jno[zgu__vdr]]
        wym__dvi = pre_alloc_string_array(xzo__hvv, naygq__rxqt)
        for zgu__vdr in range(xzo__hvv):
            if bodo.libs.array_kernels.isna(qlp__jno, zgu__vdr):
                bodo.libs.array_kernels.setna(wym__dvi, zgu__vdr)
                continue
            ind = qlp__jno[zgu__vdr]
            if bodo.libs.array_kernels.isna(mlv__bomm, ind):
                bodo.libs.array_kernels.setna(wym__dvi, zgu__vdr)
                continue
            wym__dvi[zgu__vdr] = mlv__bomm[ind]
        return wym__dvi
    return impl


@overload(operator.setitem)
def dict_arr_setitem(A, idx, val):
    if not isinstance(A, DictionaryArrayType):
        return
    raise_bodo_error(
        "DictionaryArrayType is read-only and doesn't support setitem yet")


@numba.njit(no_cpython_wrapper=True)
def find_dict_ind(arr, val):
    pls__cqnp = -1
    mlv__bomm = arr._data
    for zgu__vdr in range(len(mlv__bomm)):
        if bodo.libs.array_kernels.isna(mlv__bomm, zgu__vdr):
            continue
        if mlv__bomm[zgu__vdr] == val:
            pls__cqnp = zgu__vdr
            break
    return pls__cqnp


@numba.njit(no_cpython_wrapper=True)
def dict_arr_eq(arr, val):
    xzo__hvv = len(arr)
    pls__cqnp = find_dict_ind(arr, val)
    if pls__cqnp == -1:
        return init_bool_array(np.full(xzo__hvv, False, np.bool_), arr.
            _indices._null_bitmap.copy())
    return arr._indices == pls__cqnp


@numba.njit(no_cpython_wrapper=True)
def dict_arr_ne(arr, val):
    xzo__hvv = len(arr)
    pls__cqnp = find_dict_ind(arr, val)
    if pls__cqnp == -1:
        return init_bool_array(np.full(xzo__hvv, True, np.bool_), arr.
            _indices._null_bitmap.copy())
    return arr._indices != pls__cqnp


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
        yuiy__mlft = arr._data
        zscgh__wqtq = bodo.libs.int_arr_ext.alloc_int_array(len(yuiy__mlft),
            dtype)
        for dyv__ezjw in range(len(yuiy__mlft)):
            if bodo.libs.array_kernels.isna(yuiy__mlft, dyv__ezjw):
                bodo.libs.array_kernels.setna(zscgh__wqtq, dyv__ezjw)
                continue
            zscgh__wqtq[dyv__ezjw] = np.int64(yuiy__mlft[dyv__ezjw])
        xzo__hvv = len(arr)
        qlp__jno = arr._indices
        wym__dvi = bodo.libs.int_arr_ext.alloc_int_array(xzo__hvv, dtype)
        for zgu__vdr in range(xzo__hvv):
            if bodo.libs.array_kernels.isna(qlp__jno, zgu__vdr):
                bodo.libs.array_kernels.setna(wym__dvi, zgu__vdr)
                continue
            wym__dvi[zgu__vdr] = zscgh__wqtq[qlp__jno[zgu__vdr]]
        return wym__dvi
    return impl


def cat_dict_str(arrs, sep):
    pass


@overload(cat_dict_str)
def cat_dict_str_overload(arrs, sep):
    chaow__uvos = len(arrs)
    epvkk__rya = 'def impl(arrs, sep):\n'
    epvkk__rya += '  ind_map = {}\n'
    epvkk__rya += '  out_strs = []\n'
    epvkk__rya += '  n = len(arrs[0])\n'
    for zgu__vdr in range(chaow__uvos):
        epvkk__rya += f'  indices{zgu__vdr} = arrs[{zgu__vdr}]._indices\n'
    for zgu__vdr in range(chaow__uvos):
        epvkk__rya += f'  data{zgu__vdr} = arrs[{zgu__vdr}]._data\n'
    epvkk__rya += (
        '  out_indices = bodo.libs.int_arr_ext.alloc_int_array(n, np.int32)\n')
    epvkk__rya += '  for i in range(n):\n'
    ywgx__cge = ' or '.join([
        f'bodo.libs.array_kernels.isna(arrs[{zgu__vdr}], i)' for zgu__vdr in
        range(chaow__uvos)])
    epvkk__rya += f'    if {ywgx__cge}:\n'
    epvkk__rya += '      bodo.libs.array_kernels.setna(out_indices, i)\n'
    epvkk__rya += '      continue\n'
    for zgu__vdr in range(chaow__uvos):
        epvkk__rya += f'    ind{zgu__vdr} = indices{zgu__vdr}[i]\n'
    hsie__raf = '(' + ', '.join(f'ind{zgu__vdr}' for zgu__vdr in range(
        chaow__uvos)) + ')'
    epvkk__rya += f'    if {hsie__raf} not in ind_map:\n'
    epvkk__rya += '      out_ind = len(out_strs)\n'
    epvkk__rya += f'      ind_map[{hsie__raf}] = out_ind\n'
    mtgfu__aal = "''" if is_overload_none(sep) else 'sep'
    bfjqf__opz = ', '.join([f'data{zgu__vdr}[ind{zgu__vdr}]' for zgu__vdr in
        range(chaow__uvos)])
    epvkk__rya += f'      v = {mtgfu__aal}.join([{bfjqf__opz}])\n'
    epvkk__rya += '      out_strs.append(v)\n'
    epvkk__rya += '    else:\n'
    epvkk__rya += f'      out_ind = ind_map[{hsie__raf}]\n'
    epvkk__rya += '    out_indices[i] = out_ind\n'
    epvkk__rya += (
        '  out_str_arr = bodo.libs.str_arr_ext.str_arr_from_sequence(out_strs)\n'
        )
    epvkk__rya += """  return bodo.libs.dict_arr_ext.init_dict_arr(out_str_arr, out_indices, False)
"""
    ngalm__xxxa = {}
    exec(epvkk__rya, {'bodo': bodo, 'numba': numba, 'np': np}, ngalm__xxxa)
    impl = ngalm__xxxa['impl']
    return impl


@lower_cast(DictionaryArrayType, StringArrayType)
def cast_dict_str_arr_to_str_arr(context, builder, fromty, toty, val):
    if fromty != dict_str_arr_type:
        return
    gtt__kumez = bodo.utils.typing.decode_if_dict_array_overload(fromty)
    tbojo__okbcr = toty(fromty)
    oehn__stk = context.compile_internal(builder, gtt__kumez, tbojo__okbcr,
        (val,))
    return impl_ret_new_ref(context, builder, toty, oehn__stk)


@numba.jit(cache=True, no_cpython_wrapper=True)
def str_replace(arr, pat, repl, flags, regex):
    gav__oss = arr._data
    oum__isdpz = len(gav__oss)
    aqqq__qocii = pre_alloc_string_array(oum__isdpz, -1)
    if regex:
        zdv__qfdyd = re.compile(pat, flags)
        for zgu__vdr in range(oum__isdpz):
            if bodo.libs.array_kernels.isna(gav__oss, zgu__vdr):
                bodo.libs.array_kernels.setna(aqqq__qocii, zgu__vdr)
                continue
            aqqq__qocii[zgu__vdr] = zdv__qfdyd.sub(repl=repl, string=
                gav__oss[zgu__vdr])
    else:
        for zgu__vdr in range(oum__isdpz):
            if bodo.libs.array_kernels.isna(gav__oss, zgu__vdr):
                bodo.libs.array_kernels.setna(aqqq__qocii, zgu__vdr)
                continue
            aqqq__qocii[zgu__vdr] = gav__oss[zgu__vdr].replace(pat, repl)
    return init_dict_arr(aqqq__qocii, arr._indices.copy(), arr.
        _has_global_dictionary)
