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
        hrun__jrfjo = [('data', fe_type.data), ('indices',
            dict_indices_arr_type), ('has_global_dictionary', types.bool_)]
        models.StructModel.__init__(self, dmm, fe_type, hrun__jrfjo)


make_attribute_wrapper(DictionaryArrayType, 'data', '_data')
make_attribute_wrapper(DictionaryArrayType, 'indices', '_indices')
make_attribute_wrapper(DictionaryArrayType, 'has_global_dictionary',
    '_has_global_dictionary')
lower_builtin('getiter', dict_str_arr_type)(numba.np.arrayobj.getiter_array)


@intrinsic
def init_dict_arr(typingctx, data_t, indices_t, glob_dict_t=None):
    assert indices_t == dict_indices_arr_type, 'invalid indices type for dict array'

    def codegen(context, builder, signature, args):
        kjg__owstc, itsam__punyq, eteev__fxvqt = args
        ocau__nnfgx = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        ocau__nnfgx.data = kjg__owstc
        ocau__nnfgx.indices = itsam__punyq
        ocau__nnfgx.has_global_dictionary = eteev__fxvqt
        context.nrt.incref(builder, signature.args[0], kjg__owstc)
        context.nrt.incref(builder, signature.args[1], itsam__punyq)
        return ocau__nnfgx._getvalue()
    azs__vauv = DictionaryArrayType(data_t)
    yxctx__avk = azs__vauv(data_t, indices_t, types.bool_)
    return yxctx__avk, codegen


@typeof_impl.register(pa.DictionaryArray)
def typeof_dict_value(val, c):
    if val.type.value_type == pa.string():
        return dict_str_arr_type


def to_pa_dict_arr(A):
    if isinstance(A, pa.DictionaryArray):
        return A
    for jjjb__swo in range(len(A)):
        if pd.isna(A[jjjb__swo]):
            A[jjjb__swo] = None
    return pa.array(A).dictionary_encode()


@unbox(DictionaryArrayType)
def unbox_dict_arr(typ, val, c):
    if bodo.hiframes.boxing._use_dict_str_type:
        gckc__yfb = c.pyapi.unserialize(c.pyapi.serialize_object(
            to_pa_dict_arr))
        val = c.pyapi.call_function_objargs(gckc__yfb, [val])
        c.pyapi.decref(gckc__yfb)
    ocau__nnfgx = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    zdzh__mpq = c.pyapi.object_getattr_string(val, 'dictionary')
    dcddg__lbe = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_,
        False))
    cju__gka = c.pyapi.call_method(zdzh__mpq, 'to_numpy', (dcddg__lbe,))
    ocau__nnfgx.data = c.unbox(typ.data, cju__gka).value
    sna__swj = c.pyapi.object_getattr_string(val, 'indices')
    zaaqj__kzf = c.context.insert_const_string(c.builder.module, 'pandas')
    qyw__tyvty = c.pyapi.import_module_noblock(zaaqj__kzf)
    ifxx__vct = c.pyapi.string_from_constant_string('Int32')
    kwdu__haqn = c.pyapi.call_method(qyw__tyvty, 'array', (sna__swj, ifxx__vct)
        )
    ocau__nnfgx.indices = c.unbox(dict_indices_arr_type, kwdu__haqn).value
    ocau__nnfgx.has_global_dictionary = c.context.get_constant(types.bool_,
        False)
    c.pyapi.decref(zdzh__mpq)
    c.pyapi.decref(dcddg__lbe)
    c.pyapi.decref(cju__gka)
    c.pyapi.decref(sna__swj)
    c.pyapi.decref(qyw__tyvty)
    c.pyapi.decref(ifxx__vct)
    c.pyapi.decref(kwdu__haqn)
    if bodo.hiframes.boxing._use_dict_str_type:
        c.pyapi.decref(val)
    tfe__jtvf = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(ocau__nnfgx._getvalue(), is_error=tfe__jtvf)


@box(DictionaryArrayType)
def box_dict_arr(typ, val, c):
    ocau__nnfgx = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    if typ == dict_str_arr_type:
        c.context.nrt.incref(c.builder, typ.data, ocau__nnfgx.data)
        bjr__iyv = c.box(typ.data, ocau__nnfgx.data)
        rudht__gtzoo = cgutils.create_struct_proxy(dict_indices_arr_type)(c
            .context, c.builder, ocau__nnfgx.indices)
        vusxv__bajcg = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), c.
            pyapi.pyobj, lir.IntType(32).as_pointer(), lir.IntType(8).
            as_pointer()])
        zobab__phkcy = cgutils.get_or_insert_function(c.builder.module,
            vusxv__bajcg, name='box_dict_str_array')
        clf__ovfe = cgutils.create_struct_proxy(types.Array(types.int32, 1,
            'C'))(c.context, c.builder, rudht__gtzoo.data)
        dlpg__qaaup = c.builder.extract_value(clf__ovfe.shape, 0)
        enxg__mwv = clf__ovfe.data
        pwn__vngja = cgutils.create_struct_proxy(types.Array(types.int8, 1,
            'C'))(c.context, c.builder, rudht__gtzoo.null_bitmap).data
        cju__gka = c.builder.call(zobab__phkcy, [dlpg__qaaup, bjr__iyv,
            enxg__mwv, pwn__vngja])
        c.pyapi.decref(bjr__iyv)
    else:
        zaaqj__kzf = c.context.insert_const_string(c.builder.module, 'pyarrow')
        klzig__mgwwt = c.pyapi.import_module_noblock(zaaqj__kzf)
        xssm__ksd = c.pyapi.object_getattr_string(klzig__mgwwt,
            'DictionaryArray')
        c.context.nrt.incref(c.builder, typ.data, ocau__nnfgx.data)
        bjr__iyv = c.box(typ.data, ocau__nnfgx.data)
        c.context.nrt.incref(c.builder, dict_indices_arr_type, ocau__nnfgx.
            indices)
        sna__swj = c.box(dict_indices_arr_type, ocau__nnfgx.indices)
        tyjkf__eebfp = c.pyapi.call_method(xssm__ksd, 'from_arrays', (
            sna__swj, bjr__iyv))
        dcddg__lbe = c.pyapi.bool_from_bool(c.context.get_constant(types.
            bool_, False))
        cju__gka = c.pyapi.call_method(tyjkf__eebfp, 'to_numpy', (dcddg__lbe,))
        c.pyapi.decref(klzig__mgwwt)
        c.pyapi.decref(bjr__iyv)
        c.pyapi.decref(sna__swj)
        c.pyapi.decref(xssm__ksd)
        c.pyapi.decref(tyjkf__eebfp)
        c.pyapi.decref(dcddg__lbe)
    c.context.nrt.decref(c.builder, typ, val)
    return cju__gka


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
    uquen__kgrd = pyval.dictionary.to_numpy(False)
    qcmn__txxob = pd.array(pyval.indices, 'Int32')
    uquen__kgrd = context.get_constant_generic(builder, typ.data, uquen__kgrd)
    qcmn__txxob = context.get_constant_generic(builder,
        dict_indices_arr_type, qcmn__txxob)
    uvbo__zqo = context.get_constant(types.bool_, False)
    wmi__hcjw = lir.Constant.literal_struct([uquen__kgrd, qcmn__txxob,
        uvbo__zqo])
    return wmi__hcjw


@overload(operator.getitem, no_unliteral=True)
def dict_arr_getitem(A, ind):
    if not isinstance(A, DictionaryArrayType):
        return
    if isinstance(ind, types.Integer):

        def dict_arr_getitem_impl(A, ind):
            if bodo.libs.array_kernels.isna(A._indices, ind):
                return ''
            ikp__voo = A._indices[ind]
            return A._data[ikp__voo]
        return dict_arr_getitem_impl
    return lambda A, ind: init_dict_arr(A._data, A._indices[ind], A.
        _has_global_dictionary)


@overload_method(DictionaryArrayType, '_decode', no_unliteral=True)
def overload_dict_arr_decode(A):

    def impl(A):
        kjg__owstc = A._data
        itsam__punyq = A._indices
        dlpg__qaaup = len(itsam__punyq)
        nyjyd__stc = [get_str_arr_item_length(kjg__owstc, jjjb__swo) for
            jjjb__swo in range(len(kjg__owstc))]
        omxul__wxq = 0
        for jjjb__swo in range(dlpg__qaaup):
            if not bodo.libs.array_kernels.isna(itsam__punyq, jjjb__swo):
                omxul__wxq += nyjyd__stc[itsam__punyq[jjjb__swo]]
        shsjr__kov = pre_alloc_string_array(dlpg__qaaup, omxul__wxq)
        for jjjb__swo in range(dlpg__qaaup):
            if bodo.libs.array_kernels.isna(itsam__punyq, jjjb__swo):
                bodo.libs.array_kernels.setna(shsjr__kov, jjjb__swo)
                continue
            ind = itsam__punyq[jjjb__swo]
            if bodo.libs.array_kernels.isna(kjg__owstc, ind):
                bodo.libs.array_kernels.setna(shsjr__kov, jjjb__swo)
                continue
            shsjr__kov[jjjb__swo] = kjg__owstc[ind]
        return shsjr__kov
    return impl


@overload(operator.setitem)
def dict_arr_setitem(A, idx, val):
    if not isinstance(A, DictionaryArrayType):
        return
    raise_bodo_error(
        "DictionaryArrayType is read-only and doesn't support setitem yet")


@numba.njit(no_cpython_wrapper=True)
def find_dict_ind(arr, val):
    ikp__voo = -1
    kjg__owstc = arr._data
    for jjjb__swo in range(len(kjg__owstc)):
        if bodo.libs.array_kernels.isna(kjg__owstc, jjjb__swo):
            continue
        if kjg__owstc[jjjb__swo] == val:
            ikp__voo = jjjb__swo
            break
    return ikp__voo


@numba.njit(no_cpython_wrapper=True)
def dict_arr_eq(arr, val):
    dlpg__qaaup = len(arr)
    ikp__voo = find_dict_ind(arr, val)
    if ikp__voo == -1:
        return init_bool_array(np.full(dlpg__qaaup, False, np.bool_), arr.
            _indices._null_bitmap.copy())
    return arr._indices == ikp__voo


@numba.njit(no_cpython_wrapper=True)
def dict_arr_ne(arr, val):
    dlpg__qaaup = len(arr)
    ikp__voo = find_dict_ind(arr, val)
    if ikp__voo == -1:
        return init_bool_array(np.full(dlpg__qaaup, True, np.bool_), arr.
            _indices._null_bitmap.copy())
    return arr._indices != ikp__voo


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
        obnqv__vedoh = arr._data
        fbv__zbwum = bodo.libs.int_arr_ext.alloc_int_array(len(obnqv__vedoh
            ), dtype)
        for utrku__ped in range(len(obnqv__vedoh)):
            if bodo.libs.array_kernels.isna(obnqv__vedoh, utrku__ped):
                bodo.libs.array_kernels.setna(fbv__zbwum, utrku__ped)
                continue
            fbv__zbwum[utrku__ped] = np.int64(obnqv__vedoh[utrku__ped])
        dlpg__qaaup = len(arr)
        itsam__punyq = arr._indices
        shsjr__kov = bodo.libs.int_arr_ext.alloc_int_array(dlpg__qaaup, dtype)
        for jjjb__swo in range(dlpg__qaaup):
            if bodo.libs.array_kernels.isna(itsam__punyq, jjjb__swo):
                bodo.libs.array_kernels.setna(shsjr__kov, jjjb__swo)
                continue
            shsjr__kov[jjjb__swo] = fbv__zbwum[itsam__punyq[jjjb__swo]]
        return shsjr__kov
    return impl


def cat_dict_str(arrs, sep):
    pass


@overload(cat_dict_str)
def cat_dict_str_overload(arrs, sep):
    pqv__rwb = len(arrs)
    hyye__fjso = 'def impl(arrs, sep):\n'
    hyye__fjso += '  ind_map = {}\n'
    hyye__fjso += '  out_strs = []\n'
    hyye__fjso += '  n = len(arrs[0])\n'
    for jjjb__swo in range(pqv__rwb):
        hyye__fjso += f'  indices{jjjb__swo} = arrs[{jjjb__swo}]._indices\n'
    for jjjb__swo in range(pqv__rwb):
        hyye__fjso += f'  data{jjjb__swo} = arrs[{jjjb__swo}]._data\n'
    hyye__fjso += (
        '  out_indices = bodo.libs.int_arr_ext.alloc_int_array(n, np.int32)\n')
    hyye__fjso += '  for i in range(n):\n'
    frf__ncsa = ' or '.join([
        f'bodo.libs.array_kernels.isna(arrs[{jjjb__swo}], i)' for jjjb__swo in
        range(pqv__rwb)])
    hyye__fjso += f'    if {frf__ncsa}:\n'
    hyye__fjso += '      bodo.libs.array_kernels.setna(out_indices, i)\n'
    hyye__fjso += '      continue\n'
    for jjjb__swo in range(pqv__rwb):
        hyye__fjso += f'    ind{jjjb__swo} = indices{jjjb__swo}[i]\n'
    jab__zxby = '(' + ', '.join(f'ind{jjjb__swo}' for jjjb__swo in range(
        pqv__rwb)) + ')'
    hyye__fjso += f'    if {jab__zxby} not in ind_map:\n'
    hyye__fjso += '      out_ind = len(out_strs)\n'
    hyye__fjso += f'      ind_map[{jab__zxby}] = out_ind\n'
    hce__uac = "''" if is_overload_none(sep) else 'sep'
    wtof__edb = ', '.join([f'data{jjjb__swo}[ind{jjjb__swo}]' for jjjb__swo in
        range(pqv__rwb)])
    hyye__fjso += f'      v = {hce__uac}.join([{wtof__edb}])\n'
    hyye__fjso += '      out_strs.append(v)\n'
    hyye__fjso += '    else:\n'
    hyye__fjso += f'      out_ind = ind_map[{jab__zxby}]\n'
    hyye__fjso += '    out_indices[i] = out_ind\n'
    hyye__fjso += (
        '  out_str_arr = bodo.libs.str_arr_ext.str_arr_from_sequence(out_strs)\n'
        )
    hyye__fjso += """  return bodo.libs.dict_arr_ext.init_dict_arr(out_str_arr, out_indices, False)
"""
    tmje__jeu = {}
    exec(hyye__fjso, {'bodo': bodo, 'numba': numba, 'np': np}, tmje__jeu)
    impl = tmje__jeu['impl']
    return impl


@lower_cast(DictionaryArrayType, StringArrayType)
def cast_dict_str_arr_to_str_arr(context, builder, fromty, toty, val):
    if fromty != dict_str_arr_type:
        return
    laqwh__ryx = bodo.utils.typing.decode_if_dict_array_overload(fromty)
    yxctx__avk = toty(fromty)
    jkmsu__tjenl = context.compile_internal(builder, laqwh__ryx, yxctx__avk,
        (val,))
    return impl_ret_new_ref(context, builder, toty, jkmsu__tjenl)


@numba.jit(cache=True, no_cpython_wrapper=True)
def str_replace(arr, pat, repl, flags, regex):
    uquen__kgrd = arr._data
    rzcx__ekrwh = len(uquen__kgrd)
    szoj__mup = pre_alloc_string_array(rzcx__ekrwh, -1)
    if regex:
        ieat__mlv = re.compile(pat, flags)
        for jjjb__swo in range(rzcx__ekrwh):
            if bodo.libs.array_kernels.isna(uquen__kgrd, jjjb__swo):
                bodo.libs.array_kernels.setna(szoj__mup, jjjb__swo)
                continue
            szoj__mup[jjjb__swo] = ieat__mlv.sub(repl=repl, string=
                uquen__kgrd[jjjb__swo])
    else:
        for jjjb__swo in range(rzcx__ekrwh):
            if bodo.libs.array_kernels.isna(uquen__kgrd, jjjb__swo):
                bodo.libs.array_kernels.setna(szoj__mup, jjjb__swo)
                continue
            szoj__mup[jjjb__swo] = uquen__kgrd[jjjb__swo].replace(pat, repl)
    return init_dict_arr(szoj__mup, arr._indices.copy(), arr.
        _has_global_dictionary)
