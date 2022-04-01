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
        ggvv__zwn = [('data', fe_type.data), ('indices',
            dict_indices_arr_type), ('has_global_dictionary', types.bool_)]
        models.StructModel.__init__(self, dmm, fe_type, ggvv__zwn)


make_attribute_wrapper(DictionaryArrayType, 'data', '_data')
make_attribute_wrapper(DictionaryArrayType, 'indices', '_indices')
make_attribute_wrapper(DictionaryArrayType, 'has_global_dictionary',
    '_has_global_dictionary')
lower_builtin('getiter', dict_str_arr_type)(numba.np.arrayobj.getiter_array)


@intrinsic
def init_dict_arr(typingctx, data_t, indices_t, glob_dict_t=None):
    assert indices_t == dict_indices_arr_type, 'invalid indices type for dict array'

    def codegen(context, builder, signature, args):
        vwcxa__zpf, dfw__gcw, rcdei__flcs = args
        qah__kyybk = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        qah__kyybk.data = vwcxa__zpf
        qah__kyybk.indices = dfw__gcw
        qah__kyybk.has_global_dictionary = rcdei__flcs
        context.nrt.incref(builder, signature.args[0], vwcxa__zpf)
        context.nrt.incref(builder, signature.args[1], dfw__gcw)
        return qah__kyybk._getvalue()
    krnz__vbwrf = DictionaryArrayType(data_t)
    udl__hxgyj = krnz__vbwrf(data_t, indices_t, types.bool_)
    return udl__hxgyj, codegen


@typeof_impl.register(pa.DictionaryArray)
def typeof_dict_value(val, c):
    if val.type.value_type == pa.string():
        return dict_str_arr_type


def to_pa_dict_arr(A):
    if isinstance(A, pa.DictionaryArray):
        return A
    for kjh__ove in range(len(A)):
        if pd.isna(A[kjh__ove]):
            A[kjh__ove] = None
    return pa.array(A).dictionary_encode()


@unbox(DictionaryArrayType)
def unbox_dict_arr(typ, val, c):
    if bodo.hiframes.boxing._use_dict_str_type:
        vhp__jib = c.pyapi.unserialize(c.pyapi.serialize_object(to_pa_dict_arr)
            )
        val = c.pyapi.call_function_objargs(vhp__jib, [val])
        c.pyapi.decref(vhp__jib)
    qah__kyybk = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    jva__mod = c.pyapi.object_getattr_string(val, 'dictionary')
    svsw__dod = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_, 
        False))
    slwg__vgduj = c.pyapi.call_method(jva__mod, 'to_numpy', (svsw__dod,))
    qah__kyybk.data = c.unbox(typ.data, slwg__vgduj).value
    rupiy__uuqc = c.pyapi.object_getattr_string(val, 'indices')
    pot__itea = c.context.insert_const_string(c.builder.module, 'pandas')
    zyygd__ilbml = c.pyapi.import_module_noblock(pot__itea)
    jhfm__lkhpw = c.pyapi.string_from_constant_string('Int32')
    rikk__wby = c.pyapi.call_method(zyygd__ilbml, 'array', (rupiy__uuqc,
        jhfm__lkhpw))
    qah__kyybk.indices = c.unbox(dict_indices_arr_type, rikk__wby).value
    qah__kyybk.has_global_dictionary = c.context.get_constant(types.bool_, 
        False)
    c.pyapi.decref(jva__mod)
    c.pyapi.decref(svsw__dod)
    c.pyapi.decref(slwg__vgduj)
    c.pyapi.decref(rupiy__uuqc)
    c.pyapi.decref(zyygd__ilbml)
    c.pyapi.decref(jhfm__lkhpw)
    c.pyapi.decref(rikk__wby)
    if bodo.hiframes.boxing._use_dict_str_type:
        c.pyapi.decref(val)
    mjj__hriin = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(qah__kyybk._getvalue(), is_error=mjj__hriin)


@box(DictionaryArrayType)
def box_dict_arr(typ, val, c):
    qah__kyybk = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    if typ == dict_str_arr_type:
        c.context.nrt.incref(c.builder, typ.data, qah__kyybk.data)
        qmu__yaq = c.box(typ.data, qah__kyybk.data)
        bjeeq__jocbr = cgutils.create_struct_proxy(dict_indices_arr_type)(c
            .context, c.builder, qah__kyybk.indices)
        atszk__xtv = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), c.
            pyapi.pyobj, lir.IntType(32).as_pointer(), lir.IntType(8).
            as_pointer()])
        eqa__iqlxg = cgutils.get_or_insert_function(c.builder.module,
            atszk__xtv, name='box_dict_str_array')
        revq__ifid = cgutils.create_struct_proxy(types.Array(types.int32, 1,
            'C'))(c.context, c.builder, bjeeq__jocbr.data)
        tvj__lir = c.builder.extract_value(revq__ifid.shape, 0)
        ijjn__lgq = revq__ifid.data
        kvujy__qrc = cgutils.create_struct_proxy(types.Array(types.int8, 1,
            'C'))(c.context, c.builder, bjeeq__jocbr.null_bitmap).data
        slwg__vgduj = c.builder.call(eqa__iqlxg, [tvj__lir, qmu__yaq,
            ijjn__lgq, kvujy__qrc])
        c.pyapi.decref(qmu__yaq)
    else:
        pot__itea = c.context.insert_const_string(c.builder.module, 'pyarrow')
        pfyjm__vzoa = c.pyapi.import_module_noblock(pot__itea)
        wboon__bzuz = c.pyapi.object_getattr_string(pfyjm__vzoa,
            'DictionaryArray')
        c.context.nrt.incref(c.builder, typ.data, qah__kyybk.data)
        qmu__yaq = c.box(typ.data, qah__kyybk.data)
        c.context.nrt.incref(c.builder, dict_indices_arr_type, qah__kyybk.
            indices)
        rupiy__uuqc = c.box(dict_indices_arr_type, qah__kyybk.indices)
        qdp__ogws = c.pyapi.call_method(wboon__bzuz, 'from_arrays', (
            rupiy__uuqc, qmu__yaq))
        svsw__dod = c.pyapi.bool_from_bool(c.context.get_constant(types.
            bool_, False))
        slwg__vgduj = c.pyapi.call_method(qdp__ogws, 'to_numpy', (svsw__dod,))
        c.pyapi.decref(pfyjm__vzoa)
        c.pyapi.decref(qmu__yaq)
        c.pyapi.decref(rupiy__uuqc)
        c.pyapi.decref(wboon__bzuz)
        c.pyapi.decref(qdp__ogws)
        c.pyapi.decref(svsw__dod)
    c.context.nrt.decref(c.builder, typ, val)
    return slwg__vgduj


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
    wjb__faanz = pyval.dictionary.to_numpy(False)
    gbb__webpe = pd.array(pyval.indices, 'Int32')
    wjb__faanz = context.get_constant_generic(builder, typ.data, wjb__faanz)
    gbb__webpe = context.get_constant_generic(builder,
        dict_indices_arr_type, gbb__webpe)
    iulqf__vmlk = context.get_constant(types.bool_, False)
    hcvxk__wmgzu = lir.Constant.literal_struct([wjb__faanz, gbb__webpe,
        iulqf__vmlk])
    return hcvxk__wmgzu


@overload(operator.getitem, no_unliteral=True)
def dict_arr_getitem(A, ind):
    if not isinstance(A, DictionaryArrayType):
        return
    if isinstance(ind, types.Integer):

        def dict_arr_getitem_impl(A, ind):
            if bodo.libs.array_kernels.isna(A._indices, ind):
                return ''
            ppboh__lemj = A._indices[ind]
            return A._data[ppboh__lemj]
        return dict_arr_getitem_impl
    return lambda A, ind: init_dict_arr(A._data, A._indices[ind], A.
        _has_global_dictionary)


@overload_method(DictionaryArrayType, '_decode', no_unliteral=True)
def overload_dict_arr_decode(A):

    def impl(A):
        vwcxa__zpf = A._data
        dfw__gcw = A._indices
        tvj__lir = len(dfw__gcw)
        nhqm__oohac = [get_str_arr_item_length(vwcxa__zpf, kjh__ove) for
            kjh__ove in range(len(vwcxa__zpf))]
        feljm__fzt = 0
        for kjh__ove in range(tvj__lir):
            if not bodo.libs.array_kernels.isna(dfw__gcw, kjh__ove):
                feljm__fzt += nhqm__oohac[dfw__gcw[kjh__ove]]
        rquz__hcn = pre_alloc_string_array(tvj__lir, feljm__fzt)
        for kjh__ove in range(tvj__lir):
            if bodo.libs.array_kernels.isna(dfw__gcw, kjh__ove):
                bodo.libs.array_kernels.setna(rquz__hcn, kjh__ove)
                continue
            ind = dfw__gcw[kjh__ove]
            if bodo.libs.array_kernels.isna(vwcxa__zpf, ind):
                bodo.libs.array_kernels.setna(rquz__hcn, kjh__ove)
                continue
            rquz__hcn[kjh__ove] = vwcxa__zpf[ind]
        return rquz__hcn
    return impl


@overload(operator.setitem)
def dict_arr_setitem(A, idx, val):
    if not isinstance(A, DictionaryArrayType):
        return
    raise_bodo_error(
        "DictionaryArrayType is read-only and doesn't support setitem yet")


@numba.njit(no_cpython_wrapper=True)
def find_dict_ind(arr, val):
    ppboh__lemj = -1
    vwcxa__zpf = arr._data
    for kjh__ove in range(len(vwcxa__zpf)):
        if bodo.libs.array_kernels.isna(vwcxa__zpf, kjh__ove):
            continue
        if vwcxa__zpf[kjh__ove] == val:
            ppboh__lemj = kjh__ove
            break
    return ppboh__lemj


@numba.njit(no_cpython_wrapper=True)
def dict_arr_eq(arr, val):
    tvj__lir = len(arr)
    ppboh__lemj = find_dict_ind(arr, val)
    if ppboh__lemj == -1:
        return init_bool_array(np.full(tvj__lir, False, np.bool_), arr.
            _indices._null_bitmap.copy())
    return arr._indices == ppboh__lemj


@numba.njit(no_cpython_wrapper=True)
def dict_arr_ne(arr, val):
    tvj__lir = len(arr)
    ppboh__lemj = find_dict_ind(arr, val)
    if ppboh__lemj == -1:
        return init_bool_array(np.full(tvj__lir, True, np.bool_), arr.
            _indices._null_bitmap.copy())
    return arr._indices != ppboh__lemj


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
        atue__hnl = arr._data
        ooagr__tixk = bodo.libs.int_arr_ext.alloc_int_array(len(atue__hnl),
            dtype)
        for ytgf__mtdw in range(len(atue__hnl)):
            if bodo.libs.array_kernels.isna(atue__hnl, ytgf__mtdw):
                bodo.libs.array_kernels.setna(ooagr__tixk, ytgf__mtdw)
                continue
            ooagr__tixk[ytgf__mtdw] = np.int64(atue__hnl[ytgf__mtdw])
        tvj__lir = len(arr)
        dfw__gcw = arr._indices
        rquz__hcn = bodo.libs.int_arr_ext.alloc_int_array(tvj__lir, dtype)
        for kjh__ove in range(tvj__lir):
            if bodo.libs.array_kernels.isna(dfw__gcw, kjh__ove):
                bodo.libs.array_kernels.setna(rquz__hcn, kjh__ove)
                continue
            rquz__hcn[kjh__ove] = ooagr__tixk[dfw__gcw[kjh__ove]]
        return rquz__hcn
    return impl


def cat_dict_str(arrs, sep):
    pass


@overload(cat_dict_str)
def cat_dict_str_overload(arrs, sep):
    gize__tdqn = len(arrs)
    uigr__ilac = 'def impl(arrs, sep):\n'
    uigr__ilac += '  ind_map = {}\n'
    uigr__ilac += '  out_strs = []\n'
    uigr__ilac += '  n = len(arrs[0])\n'
    for kjh__ove in range(gize__tdqn):
        uigr__ilac += f'  indices{kjh__ove} = arrs[{kjh__ove}]._indices\n'
    for kjh__ove in range(gize__tdqn):
        uigr__ilac += f'  data{kjh__ove} = arrs[{kjh__ove}]._data\n'
    uigr__ilac += (
        '  out_indices = bodo.libs.int_arr_ext.alloc_int_array(n, np.int32)\n')
    uigr__ilac += '  for i in range(n):\n'
    aiwwl__yhc = ' or '.join([
        f'bodo.libs.array_kernels.isna(arrs[{kjh__ove}], i)' for kjh__ove in
        range(gize__tdqn)])
    uigr__ilac += f'    if {aiwwl__yhc}:\n'
    uigr__ilac += '      bodo.libs.array_kernels.setna(out_indices, i)\n'
    uigr__ilac += '      continue\n'
    for kjh__ove in range(gize__tdqn):
        uigr__ilac += f'    ind{kjh__ove} = indices{kjh__ove}[i]\n'
    xyzd__pkumx = '(' + ', '.join(f'ind{kjh__ove}' for kjh__ove in range(
        gize__tdqn)) + ')'
    uigr__ilac += f'    if {xyzd__pkumx} not in ind_map:\n'
    uigr__ilac += '      out_ind = len(out_strs)\n'
    uigr__ilac += f'      ind_map[{xyzd__pkumx}] = out_ind\n'
    oij__fmh = "''" if is_overload_none(sep) else 'sep'
    pznz__cevjl = ', '.join([f'data{kjh__ove}[ind{kjh__ove}]' for kjh__ove in
        range(gize__tdqn)])
    uigr__ilac += f'      v = {oij__fmh}.join([{pznz__cevjl}])\n'
    uigr__ilac += '      out_strs.append(v)\n'
    uigr__ilac += '    else:\n'
    uigr__ilac += f'      out_ind = ind_map[{xyzd__pkumx}]\n'
    uigr__ilac += '    out_indices[i] = out_ind\n'
    uigr__ilac += (
        '  out_str_arr = bodo.libs.str_arr_ext.str_arr_from_sequence(out_strs)\n'
        )
    uigr__ilac += """  return bodo.libs.dict_arr_ext.init_dict_arr(out_str_arr, out_indices, False)
"""
    zlb__bzj = {}
    exec(uigr__ilac, {'bodo': bodo, 'numba': numba, 'np': np}, zlb__bzj)
    impl = zlb__bzj['impl']
    return impl


@lower_cast(DictionaryArrayType, StringArrayType)
def cast_dict_str_arr_to_str_arr(context, builder, fromty, toty, val):
    if fromty != dict_str_arr_type:
        return
    bbzhz__atbb = bodo.utils.typing.decode_if_dict_array_overload(fromty)
    udl__hxgyj = toty(fromty)
    alm__lyg = context.compile_internal(builder, bbzhz__atbb, udl__hxgyj, (
        val,))
    return impl_ret_new_ref(context, builder, toty, alm__lyg)


@numba.jit(cache=True, no_cpython_wrapper=True)
def str_replace(arr, pat, repl, flags, regex):
    wjb__faanz = arr._data
    yyxzb__fdrd = len(wjb__faanz)
    jfoa__iezts = pre_alloc_string_array(yyxzb__fdrd, -1)
    if regex:
        xsc__godol = re.compile(pat, flags)
        for kjh__ove in range(yyxzb__fdrd):
            if bodo.libs.array_kernels.isna(wjb__faanz, kjh__ove):
                bodo.libs.array_kernels.setna(jfoa__iezts, kjh__ove)
                continue
            jfoa__iezts[kjh__ove] = xsc__godol.sub(repl=repl, string=
                wjb__faanz[kjh__ove])
    else:
        for kjh__ove in range(yyxzb__fdrd):
            if bodo.libs.array_kernels.isna(wjb__faanz, kjh__ove):
                bodo.libs.array_kernels.setna(jfoa__iezts, kjh__ove)
                continue
            jfoa__iezts[kjh__ove] = wjb__faanz[kjh__ove].replace(pat, repl)
    return init_dict_arr(jfoa__iezts, arr._indices.copy(), arr.
        _has_global_dictionary)
