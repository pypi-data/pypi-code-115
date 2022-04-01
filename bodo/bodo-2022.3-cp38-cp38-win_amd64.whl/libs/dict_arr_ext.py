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
        sjux__spyj = [('data', fe_type.data), ('indices',
            dict_indices_arr_type), ('has_global_dictionary', types.bool_)]
        models.StructModel.__init__(self, dmm, fe_type, sjux__spyj)


make_attribute_wrapper(DictionaryArrayType, 'data', '_data')
make_attribute_wrapper(DictionaryArrayType, 'indices', '_indices')
make_attribute_wrapper(DictionaryArrayType, 'has_global_dictionary',
    '_has_global_dictionary')
lower_builtin('getiter', dict_str_arr_type)(numba.np.arrayobj.getiter_array)


@intrinsic
def init_dict_arr(typingctx, data_t, indices_t, glob_dict_t=None):
    assert indices_t == dict_indices_arr_type, 'invalid indices type for dict array'

    def codegen(context, builder, signature, args):
        ljh__jqxxz, uxws__rkr, zrcx__cop = args
        odc__ydtdd = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        odc__ydtdd.data = ljh__jqxxz
        odc__ydtdd.indices = uxws__rkr
        odc__ydtdd.has_global_dictionary = zrcx__cop
        context.nrt.incref(builder, signature.args[0], ljh__jqxxz)
        context.nrt.incref(builder, signature.args[1], uxws__rkr)
        return odc__ydtdd._getvalue()
    fkit__gxcto = DictionaryArrayType(data_t)
    ouswc__hyv = fkit__gxcto(data_t, indices_t, types.bool_)
    return ouswc__hyv, codegen


@typeof_impl.register(pa.DictionaryArray)
def typeof_dict_value(val, c):
    if val.type.value_type == pa.string():
        return dict_str_arr_type


def to_pa_dict_arr(A):
    if isinstance(A, pa.DictionaryArray):
        return A
    for uza__ujp in range(len(A)):
        if pd.isna(A[uza__ujp]):
            A[uza__ujp] = None
    return pa.array(A).dictionary_encode()


@unbox(DictionaryArrayType)
def unbox_dict_arr(typ, val, c):
    if bodo.hiframes.boxing._use_dict_str_type:
        xnw__nob = c.pyapi.unserialize(c.pyapi.serialize_object(to_pa_dict_arr)
            )
        val = c.pyapi.call_function_objargs(xnw__nob, [val])
        c.pyapi.decref(xnw__nob)
    odc__ydtdd = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    mnxx__dmgwz = c.pyapi.object_getattr_string(val, 'dictionary')
    nadl__hzt = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_, 
        False))
    qsm__hwgwa = c.pyapi.call_method(mnxx__dmgwz, 'to_numpy', (nadl__hzt,))
    odc__ydtdd.data = c.unbox(typ.data, qsm__hwgwa).value
    deckr__ypev = c.pyapi.object_getattr_string(val, 'indices')
    gzfms__lfkmc = c.context.insert_const_string(c.builder.module, 'pandas')
    wzup__hwubn = c.pyapi.import_module_noblock(gzfms__lfkmc)
    wwq__ntfih = c.pyapi.string_from_constant_string('Int32')
    gqd__che = c.pyapi.call_method(wzup__hwubn, 'array', (deckr__ypev,
        wwq__ntfih))
    odc__ydtdd.indices = c.unbox(dict_indices_arr_type, gqd__che).value
    odc__ydtdd.has_global_dictionary = c.context.get_constant(types.bool_, 
        False)
    c.pyapi.decref(mnxx__dmgwz)
    c.pyapi.decref(nadl__hzt)
    c.pyapi.decref(qsm__hwgwa)
    c.pyapi.decref(deckr__ypev)
    c.pyapi.decref(wzup__hwubn)
    c.pyapi.decref(wwq__ntfih)
    c.pyapi.decref(gqd__che)
    if bodo.hiframes.boxing._use_dict_str_type:
        c.pyapi.decref(val)
    yllru__qbbpo = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(odc__ydtdd._getvalue(), is_error=yllru__qbbpo)


@box(DictionaryArrayType)
def box_dict_arr(typ, val, c):
    odc__ydtdd = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    if typ == dict_str_arr_type:
        c.context.nrt.incref(c.builder, typ.data, odc__ydtdd.data)
        rcmni__shpvr = c.box(typ.data, odc__ydtdd.data)
        rmjb__jtdup = cgutils.create_struct_proxy(dict_indices_arr_type)(c.
            context, c.builder, odc__ydtdd.indices)
        lih__cgrfy = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), c.
            pyapi.pyobj, lir.IntType(32).as_pointer(), lir.IntType(8).
            as_pointer()])
        puqg__iqgki = cgutils.get_or_insert_function(c.builder.module,
            lih__cgrfy, name='box_dict_str_array')
        wkb__ives = cgutils.create_struct_proxy(types.Array(types.int32, 1,
            'C'))(c.context, c.builder, rmjb__jtdup.data)
        olzzi__ihx = c.builder.extract_value(wkb__ives.shape, 0)
        xjaot__xad = wkb__ives.data
        toj__juk = cgutils.create_struct_proxy(types.Array(types.int8, 1, 'C')
            )(c.context, c.builder, rmjb__jtdup.null_bitmap).data
        qsm__hwgwa = c.builder.call(puqg__iqgki, [olzzi__ihx, rcmni__shpvr,
            xjaot__xad, toj__juk])
        c.pyapi.decref(rcmni__shpvr)
    else:
        gzfms__lfkmc = c.context.insert_const_string(c.builder.module,
            'pyarrow')
        miklw__gpwzd = c.pyapi.import_module_noblock(gzfms__lfkmc)
        umu__icpaf = c.pyapi.object_getattr_string(miklw__gpwzd,
            'DictionaryArray')
        c.context.nrt.incref(c.builder, typ.data, odc__ydtdd.data)
        rcmni__shpvr = c.box(typ.data, odc__ydtdd.data)
        c.context.nrt.incref(c.builder, dict_indices_arr_type, odc__ydtdd.
            indices)
        deckr__ypev = c.box(dict_indices_arr_type, odc__ydtdd.indices)
        oarq__xpsuo = c.pyapi.call_method(umu__icpaf, 'from_arrays', (
            deckr__ypev, rcmni__shpvr))
        nadl__hzt = c.pyapi.bool_from_bool(c.context.get_constant(types.
            bool_, False))
        qsm__hwgwa = c.pyapi.call_method(oarq__xpsuo, 'to_numpy', (nadl__hzt,))
        c.pyapi.decref(miklw__gpwzd)
        c.pyapi.decref(rcmni__shpvr)
        c.pyapi.decref(deckr__ypev)
        c.pyapi.decref(umu__icpaf)
        c.pyapi.decref(oarq__xpsuo)
        c.pyapi.decref(nadl__hzt)
    c.context.nrt.decref(c.builder, typ, val)
    return qsm__hwgwa


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
    ujunx__jyuux = pyval.dictionary.to_numpy(False)
    dcaa__mplw = pd.array(pyval.indices, 'Int32')
    ujunx__jyuux = context.get_constant_generic(builder, typ.data, ujunx__jyuux
        )
    dcaa__mplw = context.get_constant_generic(builder,
        dict_indices_arr_type, dcaa__mplw)
    gtsp__fjxn = context.get_constant(types.bool_, False)
    pbt__kwr = lir.Constant.literal_struct([ujunx__jyuux, dcaa__mplw,
        gtsp__fjxn])
    return pbt__kwr


@overload(operator.getitem, no_unliteral=True)
def dict_arr_getitem(A, ind):
    if not isinstance(A, DictionaryArrayType):
        return
    if isinstance(ind, types.Integer):

        def dict_arr_getitem_impl(A, ind):
            if bodo.libs.array_kernels.isna(A._indices, ind):
                return ''
            jsjru__kjqo = A._indices[ind]
            return A._data[jsjru__kjqo]
        return dict_arr_getitem_impl
    return lambda A, ind: init_dict_arr(A._data, A._indices[ind], A.
        _has_global_dictionary)


@overload_method(DictionaryArrayType, '_decode', no_unliteral=True)
def overload_dict_arr_decode(A):

    def impl(A):
        ljh__jqxxz = A._data
        uxws__rkr = A._indices
        olzzi__ihx = len(uxws__rkr)
        nyet__ajzy = [get_str_arr_item_length(ljh__jqxxz, uza__ujp) for
            uza__ujp in range(len(ljh__jqxxz))]
        bjx__xdknf = 0
        for uza__ujp in range(olzzi__ihx):
            if not bodo.libs.array_kernels.isna(uxws__rkr, uza__ujp):
                bjx__xdknf += nyet__ajzy[uxws__rkr[uza__ujp]]
        vos__nfdq = pre_alloc_string_array(olzzi__ihx, bjx__xdknf)
        for uza__ujp in range(olzzi__ihx):
            if bodo.libs.array_kernels.isna(uxws__rkr, uza__ujp):
                bodo.libs.array_kernels.setna(vos__nfdq, uza__ujp)
                continue
            ind = uxws__rkr[uza__ujp]
            if bodo.libs.array_kernels.isna(ljh__jqxxz, ind):
                bodo.libs.array_kernels.setna(vos__nfdq, uza__ujp)
                continue
            vos__nfdq[uza__ujp] = ljh__jqxxz[ind]
        return vos__nfdq
    return impl


@overload(operator.setitem)
def dict_arr_setitem(A, idx, val):
    if not isinstance(A, DictionaryArrayType):
        return
    raise_bodo_error(
        "DictionaryArrayType is read-only and doesn't support setitem yet")


@numba.njit(no_cpython_wrapper=True)
def find_dict_ind(arr, val):
    jsjru__kjqo = -1
    ljh__jqxxz = arr._data
    for uza__ujp in range(len(ljh__jqxxz)):
        if bodo.libs.array_kernels.isna(ljh__jqxxz, uza__ujp):
            continue
        if ljh__jqxxz[uza__ujp] == val:
            jsjru__kjqo = uza__ujp
            break
    return jsjru__kjqo


@numba.njit(no_cpython_wrapper=True)
def dict_arr_eq(arr, val):
    olzzi__ihx = len(arr)
    jsjru__kjqo = find_dict_ind(arr, val)
    if jsjru__kjqo == -1:
        return init_bool_array(np.full(olzzi__ihx, False, np.bool_), arr.
            _indices._null_bitmap.copy())
    return arr._indices == jsjru__kjqo


@numba.njit(no_cpython_wrapper=True)
def dict_arr_ne(arr, val):
    olzzi__ihx = len(arr)
    jsjru__kjqo = find_dict_ind(arr, val)
    if jsjru__kjqo == -1:
        return init_bool_array(np.full(olzzi__ihx, True, np.bool_), arr.
            _indices._null_bitmap.copy())
    return arr._indices != jsjru__kjqo


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
        ytz__aevm = arr._data
        xfnv__wihm = bodo.libs.int_arr_ext.alloc_int_array(len(ytz__aevm),
            dtype)
        for rlzvh__mbm in range(len(ytz__aevm)):
            if bodo.libs.array_kernels.isna(ytz__aevm, rlzvh__mbm):
                bodo.libs.array_kernels.setna(xfnv__wihm, rlzvh__mbm)
                continue
            xfnv__wihm[rlzvh__mbm] = np.int64(ytz__aevm[rlzvh__mbm])
        olzzi__ihx = len(arr)
        uxws__rkr = arr._indices
        vos__nfdq = bodo.libs.int_arr_ext.alloc_int_array(olzzi__ihx, dtype)
        for uza__ujp in range(olzzi__ihx):
            if bodo.libs.array_kernels.isna(uxws__rkr, uza__ujp):
                bodo.libs.array_kernels.setna(vos__nfdq, uza__ujp)
                continue
            vos__nfdq[uza__ujp] = xfnv__wihm[uxws__rkr[uza__ujp]]
        return vos__nfdq
    return impl


def cat_dict_str(arrs, sep):
    pass


@overload(cat_dict_str)
def cat_dict_str_overload(arrs, sep):
    mnpu__qzm = len(arrs)
    mfjn__oqbh = 'def impl(arrs, sep):\n'
    mfjn__oqbh += '  ind_map = {}\n'
    mfjn__oqbh += '  out_strs = []\n'
    mfjn__oqbh += '  n = len(arrs[0])\n'
    for uza__ujp in range(mnpu__qzm):
        mfjn__oqbh += f'  indices{uza__ujp} = arrs[{uza__ujp}]._indices\n'
    for uza__ujp in range(mnpu__qzm):
        mfjn__oqbh += f'  data{uza__ujp} = arrs[{uza__ujp}]._data\n'
    mfjn__oqbh += (
        '  out_indices = bodo.libs.int_arr_ext.alloc_int_array(n, np.int32)\n')
    mfjn__oqbh += '  for i in range(n):\n'
    guky__yaey = ' or '.join([
        f'bodo.libs.array_kernels.isna(arrs[{uza__ujp}], i)' for uza__ujp in
        range(mnpu__qzm)])
    mfjn__oqbh += f'    if {guky__yaey}:\n'
    mfjn__oqbh += '      bodo.libs.array_kernels.setna(out_indices, i)\n'
    mfjn__oqbh += '      continue\n'
    for uza__ujp in range(mnpu__qzm):
        mfjn__oqbh += f'    ind{uza__ujp} = indices{uza__ujp}[i]\n'
    rpp__spvg = '(' + ', '.join(f'ind{uza__ujp}' for uza__ujp in range(
        mnpu__qzm)) + ')'
    mfjn__oqbh += f'    if {rpp__spvg} not in ind_map:\n'
    mfjn__oqbh += '      out_ind = len(out_strs)\n'
    mfjn__oqbh += f'      ind_map[{rpp__spvg}] = out_ind\n'
    mts__pvbo = "''" if is_overload_none(sep) else 'sep'
    obrp__dymv = ', '.join([f'data{uza__ujp}[ind{uza__ujp}]' for uza__ujp in
        range(mnpu__qzm)])
    mfjn__oqbh += f'      v = {mts__pvbo}.join([{obrp__dymv}])\n'
    mfjn__oqbh += '      out_strs.append(v)\n'
    mfjn__oqbh += '    else:\n'
    mfjn__oqbh += f'      out_ind = ind_map[{rpp__spvg}]\n'
    mfjn__oqbh += '    out_indices[i] = out_ind\n'
    mfjn__oqbh += (
        '  out_str_arr = bodo.libs.str_arr_ext.str_arr_from_sequence(out_strs)\n'
        )
    mfjn__oqbh += """  return bodo.libs.dict_arr_ext.init_dict_arr(out_str_arr, out_indices, False)
"""
    cygg__keh = {}
    exec(mfjn__oqbh, {'bodo': bodo, 'numba': numba, 'np': np}, cygg__keh)
    impl = cygg__keh['impl']
    return impl


@lower_cast(DictionaryArrayType, StringArrayType)
def cast_dict_str_arr_to_str_arr(context, builder, fromty, toty, val):
    if fromty != dict_str_arr_type:
        return
    kalj__qyas = bodo.utils.typing.decode_if_dict_array_overload(fromty)
    ouswc__hyv = toty(fromty)
    tfbw__fsn = context.compile_internal(builder, kalj__qyas, ouswc__hyv, (
        val,))
    return impl_ret_new_ref(context, builder, toty, tfbw__fsn)


@numba.jit(cache=True, no_cpython_wrapper=True)
def str_replace(arr, pat, repl, flags, regex):
    ujunx__jyuux = arr._data
    lptn__kng = len(ujunx__jyuux)
    oxyib__wagvx = pre_alloc_string_array(lptn__kng, -1)
    if regex:
        grsp__hyz = re.compile(pat, flags)
        for uza__ujp in range(lptn__kng):
            if bodo.libs.array_kernels.isna(ujunx__jyuux, uza__ujp):
                bodo.libs.array_kernels.setna(oxyib__wagvx, uza__ujp)
                continue
            oxyib__wagvx[uza__ujp] = grsp__hyz.sub(repl=repl, string=
                ujunx__jyuux[uza__ujp])
    else:
        for uza__ujp in range(lptn__kng):
            if bodo.libs.array_kernels.isna(ujunx__jyuux, uza__ujp):
                bodo.libs.array_kernels.setna(oxyib__wagvx, uza__ujp)
                continue
            oxyib__wagvx[uza__ujp] = ujunx__jyuux[uza__ujp].replace(pat, repl)
    return init_dict_arr(oxyib__wagvx, arr._indices.copy(), arr.
        _has_global_dictionary)
