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
        tabvn__sfz = [('data', fe_type.data), ('indices',
            dict_indices_arr_type), ('has_global_dictionary', types.bool_)]
        models.StructModel.__init__(self, dmm, fe_type, tabvn__sfz)


make_attribute_wrapper(DictionaryArrayType, 'data', '_data')
make_attribute_wrapper(DictionaryArrayType, 'indices', '_indices')
make_attribute_wrapper(DictionaryArrayType, 'has_global_dictionary',
    '_has_global_dictionary')
lower_builtin('getiter', dict_str_arr_type)(numba.np.arrayobj.getiter_array)


@intrinsic
def init_dict_arr(typingctx, data_t, indices_t, glob_dict_t=None):
    assert indices_t == dict_indices_arr_type, 'invalid indices type for dict array'

    def codegen(context, builder, signature, args):
        pyo__cfuro, mrnph__yaoc, bkm__exily = args
        imhd__nti = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        imhd__nti.data = pyo__cfuro
        imhd__nti.indices = mrnph__yaoc
        imhd__nti.has_global_dictionary = bkm__exily
        context.nrt.incref(builder, signature.args[0], pyo__cfuro)
        context.nrt.incref(builder, signature.args[1], mrnph__yaoc)
        return imhd__nti._getvalue()
    kvnc__xye = DictionaryArrayType(data_t)
    ikhf__mbxwx = kvnc__xye(data_t, indices_t, types.bool_)
    return ikhf__mbxwx, codegen


@typeof_impl.register(pa.DictionaryArray)
def typeof_dict_value(val, c):
    if val.type.value_type == pa.string():
        return dict_str_arr_type


def to_pa_dict_arr(A):
    if isinstance(A, pa.DictionaryArray):
        return A
    for tnbcz__ayz in range(len(A)):
        if pd.isna(A[tnbcz__ayz]):
            A[tnbcz__ayz] = None
    return pa.array(A).dictionary_encode()


@unbox(DictionaryArrayType)
def unbox_dict_arr(typ, val, c):
    if bodo.hiframes.boxing._use_dict_str_type:
        qzvu__wqp = c.pyapi.unserialize(c.pyapi.serialize_object(
            to_pa_dict_arr))
        val = c.pyapi.call_function_objargs(qzvu__wqp, [val])
        c.pyapi.decref(qzvu__wqp)
    imhd__nti = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    bkypf__rmt = c.pyapi.object_getattr_string(val, 'dictionary')
    uwjq__flgik = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_,
        False))
    ecupm__ogejg = c.pyapi.call_method(bkypf__rmt, 'to_numpy', (uwjq__flgik,))
    imhd__nti.data = c.unbox(typ.data, ecupm__ogejg).value
    wog__aoxjp = c.pyapi.object_getattr_string(val, 'indices')
    ebja__bri = c.context.insert_const_string(c.builder.module, 'pandas')
    ppm__roev = c.pyapi.import_module_noblock(ebja__bri)
    jkkxe__sluvn = c.pyapi.string_from_constant_string('Int32')
    yqes__tmbu = c.pyapi.call_method(ppm__roev, 'array', (wog__aoxjp,
        jkkxe__sluvn))
    imhd__nti.indices = c.unbox(dict_indices_arr_type, yqes__tmbu).value
    imhd__nti.has_global_dictionary = c.context.get_constant(types.bool_, False
        )
    c.pyapi.decref(bkypf__rmt)
    c.pyapi.decref(uwjq__flgik)
    c.pyapi.decref(ecupm__ogejg)
    c.pyapi.decref(wog__aoxjp)
    c.pyapi.decref(ppm__roev)
    c.pyapi.decref(jkkxe__sluvn)
    c.pyapi.decref(yqes__tmbu)
    if bodo.hiframes.boxing._use_dict_str_type:
        c.pyapi.decref(val)
    dmkzf__qfyb = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(imhd__nti._getvalue(), is_error=dmkzf__qfyb)


@box(DictionaryArrayType)
def box_dict_arr(typ, val, c):
    imhd__nti = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    if typ == dict_str_arr_type:
        c.context.nrt.incref(c.builder, typ.data, imhd__nti.data)
        ujh__deslw = c.box(typ.data, imhd__nti.data)
        owdzu__hore = cgutils.create_struct_proxy(dict_indices_arr_type)(c.
            context, c.builder, imhd__nti.indices)
        cyb__ulr = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), c.
            pyapi.pyobj, lir.IntType(32).as_pointer(), lir.IntType(8).
            as_pointer()])
        ybgqd__uukb = cgutils.get_or_insert_function(c.builder.module,
            cyb__ulr, name='box_dict_str_array')
        ofhus__myme = cgutils.create_struct_proxy(types.Array(types.int32, 
            1, 'C'))(c.context, c.builder, owdzu__hore.data)
        zerav__sinoq = c.builder.extract_value(ofhus__myme.shape, 0)
        bltk__wyi = ofhus__myme.data
        wgfki__iyjm = cgutils.create_struct_proxy(types.Array(types.int8, 1,
            'C'))(c.context, c.builder, owdzu__hore.null_bitmap).data
        ecupm__ogejg = c.builder.call(ybgqd__uukb, [zerav__sinoq,
            ujh__deslw, bltk__wyi, wgfki__iyjm])
        c.pyapi.decref(ujh__deslw)
    else:
        ebja__bri = c.context.insert_const_string(c.builder.module, 'pyarrow')
        ccrkp__lnfh = c.pyapi.import_module_noblock(ebja__bri)
        yxorh__xyvhj = c.pyapi.object_getattr_string(ccrkp__lnfh,
            'DictionaryArray')
        c.context.nrt.incref(c.builder, typ.data, imhd__nti.data)
        ujh__deslw = c.box(typ.data, imhd__nti.data)
        c.context.nrt.incref(c.builder, dict_indices_arr_type, imhd__nti.
            indices)
        wog__aoxjp = c.box(dict_indices_arr_type, imhd__nti.indices)
        txe__awn = c.pyapi.call_method(yxorh__xyvhj, 'from_arrays', (
            wog__aoxjp, ujh__deslw))
        uwjq__flgik = c.pyapi.bool_from_bool(c.context.get_constant(types.
            bool_, False))
        ecupm__ogejg = c.pyapi.call_method(txe__awn, 'to_numpy', (uwjq__flgik,)
            )
        c.pyapi.decref(ccrkp__lnfh)
        c.pyapi.decref(ujh__deslw)
        c.pyapi.decref(wog__aoxjp)
        c.pyapi.decref(yxorh__xyvhj)
        c.pyapi.decref(txe__awn)
        c.pyapi.decref(uwjq__flgik)
    c.context.nrt.decref(c.builder, typ, val)
    return ecupm__ogejg


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
    epves__ivagw = pyval.dictionary.to_numpy(False)
    tzywi__dqu = pd.array(pyval.indices, 'Int32')
    epves__ivagw = context.get_constant_generic(builder, typ.data, epves__ivagw
        )
    tzywi__dqu = context.get_constant_generic(builder,
        dict_indices_arr_type, tzywi__dqu)
    nlu__hjpfv = context.get_constant(types.bool_, False)
    fsvz__jld = lir.Constant.literal_struct([epves__ivagw, tzywi__dqu,
        nlu__hjpfv])
    return fsvz__jld


@overload(operator.getitem, no_unliteral=True)
def dict_arr_getitem(A, ind):
    if not isinstance(A, DictionaryArrayType):
        return
    if isinstance(ind, types.Integer):

        def dict_arr_getitem_impl(A, ind):
            if bodo.libs.array_kernels.isna(A._indices, ind):
                return ''
            zyqh__xlkeo = A._indices[ind]
            return A._data[zyqh__xlkeo]
        return dict_arr_getitem_impl
    return lambda A, ind: init_dict_arr(A._data, A._indices[ind], A.
        _has_global_dictionary)


@overload_method(DictionaryArrayType, '_decode', no_unliteral=True)
def overload_dict_arr_decode(A):

    def impl(A):
        pyo__cfuro = A._data
        mrnph__yaoc = A._indices
        zerav__sinoq = len(mrnph__yaoc)
        dsbvs__eib = [get_str_arr_item_length(pyo__cfuro, tnbcz__ayz) for
            tnbcz__ayz in range(len(pyo__cfuro))]
        gfxk__bvcxi = 0
        for tnbcz__ayz in range(zerav__sinoq):
            if not bodo.libs.array_kernels.isna(mrnph__yaoc, tnbcz__ayz):
                gfxk__bvcxi += dsbvs__eib[mrnph__yaoc[tnbcz__ayz]]
        tkwj__wzttb = pre_alloc_string_array(zerav__sinoq, gfxk__bvcxi)
        for tnbcz__ayz in range(zerav__sinoq):
            if bodo.libs.array_kernels.isna(mrnph__yaoc, tnbcz__ayz):
                bodo.libs.array_kernels.setna(tkwj__wzttb, tnbcz__ayz)
                continue
            ind = mrnph__yaoc[tnbcz__ayz]
            if bodo.libs.array_kernels.isna(pyo__cfuro, ind):
                bodo.libs.array_kernels.setna(tkwj__wzttb, tnbcz__ayz)
                continue
            tkwj__wzttb[tnbcz__ayz] = pyo__cfuro[ind]
        return tkwj__wzttb
    return impl


@overload(operator.setitem)
def dict_arr_setitem(A, idx, val):
    if not isinstance(A, DictionaryArrayType):
        return
    raise_bodo_error(
        "DictionaryArrayType is read-only and doesn't support setitem yet")


@numba.njit(no_cpython_wrapper=True)
def find_dict_ind(arr, val):
    zyqh__xlkeo = -1
    pyo__cfuro = arr._data
    for tnbcz__ayz in range(len(pyo__cfuro)):
        if bodo.libs.array_kernels.isna(pyo__cfuro, tnbcz__ayz):
            continue
        if pyo__cfuro[tnbcz__ayz] == val:
            zyqh__xlkeo = tnbcz__ayz
            break
    return zyqh__xlkeo


@numba.njit(no_cpython_wrapper=True)
def dict_arr_eq(arr, val):
    zerav__sinoq = len(arr)
    zyqh__xlkeo = find_dict_ind(arr, val)
    if zyqh__xlkeo == -1:
        return init_bool_array(np.full(zerav__sinoq, False, np.bool_), arr.
            _indices._null_bitmap.copy())
    return arr._indices == zyqh__xlkeo


@numba.njit(no_cpython_wrapper=True)
def dict_arr_ne(arr, val):
    zerav__sinoq = len(arr)
    zyqh__xlkeo = find_dict_ind(arr, val)
    if zyqh__xlkeo == -1:
        return init_bool_array(np.full(zerav__sinoq, True, np.bool_), arr.
            _indices._null_bitmap.copy())
    return arr._indices != zyqh__xlkeo


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
        odqb__kjqa = arr._data
        fbjeo__ilky = bodo.libs.int_arr_ext.alloc_int_array(len(odqb__kjqa),
            dtype)
        for hpfmw__onn in range(len(odqb__kjqa)):
            if bodo.libs.array_kernels.isna(odqb__kjqa, hpfmw__onn):
                bodo.libs.array_kernels.setna(fbjeo__ilky, hpfmw__onn)
                continue
            fbjeo__ilky[hpfmw__onn] = np.int64(odqb__kjqa[hpfmw__onn])
        zerav__sinoq = len(arr)
        mrnph__yaoc = arr._indices
        tkwj__wzttb = bodo.libs.int_arr_ext.alloc_int_array(zerav__sinoq, dtype
            )
        for tnbcz__ayz in range(zerav__sinoq):
            if bodo.libs.array_kernels.isna(mrnph__yaoc, tnbcz__ayz):
                bodo.libs.array_kernels.setna(tkwj__wzttb, tnbcz__ayz)
                continue
            tkwj__wzttb[tnbcz__ayz] = fbjeo__ilky[mrnph__yaoc[tnbcz__ayz]]
        return tkwj__wzttb
    return impl


def cat_dict_str(arrs, sep):
    pass


@overload(cat_dict_str)
def cat_dict_str_overload(arrs, sep):
    dlqw__fmiia = len(arrs)
    eyr__yhnkm = 'def impl(arrs, sep):\n'
    eyr__yhnkm += '  ind_map = {}\n'
    eyr__yhnkm += '  out_strs = []\n'
    eyr__yhnkm += '  n = len(arrs[0])\n'
    for tnbcz__ayz in range(dlqw__fmiia):
        eyr__yhnkm += f'  indices{tnbcz__ayz} = arrs[{tnbcz__ayz}]._indices\n'
    for tnbcz__ayz in range(dlqw__fmiia):
        eyr__yhnkm += f'  data{tnbcz__ayz} = arrs[{tnbcz__ayz}]._data\n'
    eyr__yhnkm += (
        '  out_indices = bodo.libs.int_arr_ext.alloc_int_array(n, np.int32)\n')
    eyr__yhnkm += '  for i in range(n):\n'
    sad__elloq = ' or '.join([
        f'bodo.libs.array_kernels.isna(arrs[{tnbcz__ayz}], i)' for
        tnbcz__ayz in range(dlqw__fmiia)])
    eyr__yhnkm += f'    if {sad__elloq}:\n'
    eyr__yhnkm += '      bodo.libs.array_kernels.setna(out_indices, i)\n'
    eyr__yhnkm += '      continue\n'
    for tnbcz__ayz in range(dlqw__fmiia):
        eyr__yhnkm += f'    ind{tnbcz__ayz} = indices{tnbcz__ayz}[i]\n'
    prva__gsof = '(' + ', '.join(f'ind{tnbcz__ayz}' for tnbcz__ayz in range
        (dlqw__fmiia)) + ')'
    eyr__yhnkm += f'    if {prva__gsof} not in ind_map:\n'
    eyr__yhnkm += '      out_ind = len(out_strs)\n'
    eyr__yhnkm += f'      ind_map[{prva__gsof}] = out_ind\n'
    pxprt__vlfso = "''" if is_overload_none(sep) else 'sep'
    nfeka__nlp = ', '.join([f'data{tnbcz__ayz}[ind{tnbcz__ayz}]' for
        tnbcz__ayz in range(dlqw__fmiia)])
    eyr__yhnkm += f'      v = {pxprt__vlfso}.join([{nfeka__nlp}])\n'
    eyr__yhnkm += '      out_strs.append(v)\n'
    eyr__yhnkm += '    else:\n'
    eyr__yhnkm += f'      out_ind = ind_map[{prva__gsof}]\n'
    eyr__yhnkm += '    out_indices[i] = out_ind\n'
    eyr__yhnkm += (
        '  out_str_arr = bodo.libs.str_arr_ext.str_arr_from_sequence(out_strs)\n'
        )
    eyr__yhnkm += """  return bodo.libs.dict_arr_ext.init_dict_arr(out_str_arr, out_indices, False)
"""
    tbfw__ijtsu = {}
    exec(eyr__yhnkm, {'bodo': bodo, 'numba': numba, 'np': np}, tbfw__ijtsu)
    impl = tbfw__ijtsu['impl']
    return impl


@lower_cast(DictionaryArrayType, StringArrayType)
def cast_dict_str_arr_to_str_arr(context, builder, fromty, toty, val):
    if fromty != dict_str_arr_type:
        return
    idaa__tba = bodo.utils.typing.decode_if_dict_array_overload(fromty)
    ikhf__mbxwx = toty(fromty)
    fobxb__xwtep = context.compile_internal(builder, idaa__tba, ikhf__mbxwx,
        (val,))
    return impl_ret_new_ref(context, builder, toty, fobxb__xwtep)


@numba.jit(cache=True, no_cpython_wrapper=True)
def str_replace(arr, pat, repl, flags, regex):
    epves__ivagw = arr._data
    vopq__vhwvv = len(epves__ivagw)
    ubt__csjgc = pre_alloc_string_array(vopq__vhwvv, -1)
    if regex:
        jdije__ejy = re.compile(pat, flags)
        for tnbcz__ayz in range(vopq__vhwvv):
            if bodo.libs.array_kernels.isna(epves__ivagw, tnbcz__ayz):
                bodo.libs.array_kernels.setna(ubt__csjgc, tnbcz__ayz)
                continue
            ubt__csjgc[tnbcz__ayz] = jdije__ejy.sub(repl=repl, string=
                epves__ivagw[tnbcz__ayz])
    else:
        for tnbcz__ayz in range(vopq__vhwvv):
            if bodo.libs.array_kernels.isna(epves__ivagw, tnbcz__ayz):
                bodo.libs.array_kernels.setna(ubt__csjgc, tnbcz__ayz)
                continue
            ubt__csjgc[tnbcz__ayz] = epves__ivagw[tnbcz__ayz].replace(pat, repl
                )
    return init_dict_arr(ubt__csjgc, arr._indices.copy(), arr.
        _has_global_dictionary)
