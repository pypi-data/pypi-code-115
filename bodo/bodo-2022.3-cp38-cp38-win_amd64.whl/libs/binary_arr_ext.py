"""Array implementation for binary (bytes) objects, which are usually immutable.
It is equivalent to string array, except that it stores a 'bytes' object for each
element instead of 'str'.
"""
import operator
import llvmlite.binding as ll
import numba
import numpy as np
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import impl_ret_borrowed
from numba.extending import intrinsic, lower_builtin, lower_cast, make_attribute_wrapper, overload, overload_attribute, overload_method
import bodo
from bodo.libs import hstr_ext
from bodo.libs.array_item_arr_ext import ArrayItemArrayType
from bodo.utils.typing import BodoError, is_list_like_index_type
_bytes_fromhex = types.ExternalFunction('bytes_fromhex', types.int64(types.
    voidptr, types.voidptr, types.uint64))
ll.add_symbol('bytes_to_hex', hstr_ext.bytes_to_hex)
ll.add_symbol('bytes_fromhex', hstr_ext.bytes_fromhex)
bytes_type = types.Bytes(types.uint8, 1, 'C', readonly=True)


class BinaryArrayType(types.IterableType, types.ArrayCompatible):

    def __init__(self):
        super(BinaryArrayType, self).__init__(name='BinaryArrayType()')

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def dtype(self):
        return bytes_type

    def copy(self):
        return BinaryArrayType()

    @property
    def iterator_type(self):
        return bodo.utils.typing.BodoArrayIterator(self)


binary_array_type = BinaryArrayType()


@overload(len, no_unliteral=True)
def bin_arr_len_overload(bin_arr):
    if bin_arr == binary_array_type:
        return lambda bin_arr: len(bin_arr._data)


@overload_attribute(BinaryArrayType, 'size')
def bin_arr_size_overload(bin_arr):
    return lambda bin_arr: len(bin_arr._data)


@overload_attribute(BinaryArrayType, 'shape')
def bin_arr_shape_overload(bin_arr):
    return lambda bin_arr: (len(bin_arr._data),)


@overload_attribute(BinaryArrayType, 'nbytes')
def bin_arr_nbytes_overload(bin_arr):
    return lambda bin_arr: bin_arr._data.nbytes


@overload_attribute(BinaryArrayType, 'ndim')
def overload_bin_arr_ndim(A):
    return lambda A: 1


@overload_attribute(BinaryArrayType, 'dtype')
def overload_bool_arr_dtype(A):
    return lambda A: np.dtype('O')


@numba.njit
def pre_alloc_binary_array(n_bytestrs, n_chars):
    if n_chars is None:
        n_chars = -1
    bin_arr = init_binary_arr(bodo.libs.array_item_arr_ext.
        pre_alloc_array_item_array(np.int64(n_bytestrs), (np.int64(n_chars)
        ,), bodo.libs.str_arr_ext.char_arr_type))
    if n_chars == 0:
        bodo.libs.str_arr_ext.set_all_offsets_to_0(bin_arr)
    return bin_arr


@intrinsic
def init_binary_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, ArrayItemArrayType
        ) and data_typ.dtype == types.Array(types.uint8, 1, 'C')

    def codegen(context, builder, sig, args):
        hsuta__ayns, = args
        ajhie__rzjpr = context.make_helper(builder, binary_array_type)
        ajhie__rzjpr.data = hsuta__ayns
        context.nrt.incref(builder, data_typ, hsuta__ayns)
        return ajhie__rzjpr._getvalue()
    return binary_array_type(data_typ), codegen


@intrinsic
def init_bytes_type(typingctx, data_typ, length_type):
    assert data_typ == types.Array(types.uint8, 1, 'C')
    assert length_type == types.int64

    def codegen(context, builder, sig, args):
        luu__faa = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        gtrs__fbtcc = args[1]
        wkv__zphh = cgutils.create_struct_proxy(bytes_type)(context, builder)
        wkv__zphh.meminfo = context.nrt.meminfo_alloc(builder, gtrs__fbtcc)
        wkv__zphh.nitems = gtrs__fbtcc
        wkv__zphh.itemsize = lir.Constant(wkv__zphh.itemsize.type, 1)
        wkv__zphh.data = context.nrt.meminfo_data(builder, wkv__zphh.meminfo)
        wkv__zphh.parent = cgutils.get_null_value(wkv__zphh.parent.type)
        wkv__zphh.shape = cgutils.pack_array(builder, [gtrs__fbtcc],
            context.get_value_type(types.intp))
        wkv__zphh.strides = luu__faa.strides
        cgutils.memcpy(builder, wkv__zphh.data, luu__faa.data, gtrs__fbtcc)
        return wkv__zphh._getvalue()
    return bytes_type(data_typ, length_type), codegen


@intrinsic
def cast_bytes_uint8array(typingctx, data_typ):
    assert data_typ == bytes_type

    def codegen(context, builder, sig, args):
        return impl_ret_borrowed(context, builder, sig.return_type, args[0])
    return types.Array(types.uint8, 1, 'C')(data_typ), codegen


@overload_method(BinaryArrayType, 'copy', no_unliteral=True)
def binary_arr_copy_overload(arr):

    def copy_impl(arr):
        return init_binary_arr(arr._data.copy())
    return copy_impl


@overload_method(types.Bytes, 'hex')
def binary_arr_hex(arr):
    jub__ohru = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

    def impl(arr):
        gtrs__fbtcc = len(arr) * 2
        output = numba.cpython.unicode._empty_string(jub__ohru, gtrs__fbtcc, 1)
        bytes_to_hex(output, arr)
        return output
    return impl


@lower_cast(types.CPointer(types.uint8), types.voidptr)
def cast_uint8_array_to_voidptr(context, builder, fromty, toty, val):
    return val


make_attribute_wrapper(types.Bytes, 'data', '_data')


@overload_method(types.Bytes, '__hash__')
def bytes_hash(arr):

    def impl(arr):
        return numba.cpython.hashing._Py_HashBytes(arr._data, len(arr))
    return impl


@intrinsic
def bytes_to_hex(typingctx, output, arr):

    def codegen(context, builder, sig, args):
        kdy__ppy = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        yuuze__zxmw = cgutils.create_struct_proxy(sig.args[1])(context,
            builder, value=args[1])
        vwx__fyjr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(64)])
        pwepv__jnv = cgutils.get_or_insert_function(builder.module,
            vwx__fyjr, name='bytes_to_hex')
        builder.call(pwepv__jnv, (kdy__ppy.data, yuuze__zxmw.data,
            yuuze__zxmw.nitems))
    return types.void(output, arr), codegen


@overload(operator.getitem, no_unliteral=True)
def binary_arr_getitem(arr, ind):
    if arr != binary_array_type:
        return
    if isinstance(ind, types.Integer):

        def impl(arr, ind):
            xdjzs__subbx = arr._data[ind]
            return init_bytes_type(xdjzs__subbx, len(xdjzs__subbx))
        return impl
    if is_list_like_index_type(ind) and (ind.dtype == types.bool_ or
        isinstance(ind.dtype, types.Integer)) or isinstance(ind, types.
        SliceType):
        return lambda arr, ind: init_binary_arr(arr._data[ind])
    raise BodoError(
        f'getitem for Binary Array with indexing type {ind} not supported.')


def bytes_fromhex(hex_str):
    pass


@overload(bytes_fromhex)
def overload_bytes_fromhex(hex_str):
    hex_str = types.unliteral(hex_str)
    if hex_str == bodo.string_type:
        jub__ohru = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

        def impl(hex_str):
            if not hex_str._is_ascii or hex_str._kind != jub__ohru:
                raise TypeError(
                    'bytes.fromhex is only supported on ascii strings')
            hsuta__ayns = np.empty(len(hex_str) // 2, np.uint8)
            gtrs__fbtcc = _bytes_fromhex(hsuta__ayns.ctypes, hex_str._data,
                len(hex_str))
            ggh__mav = init_bytes_type(hsuta__ayns, gtrs__fbtcc)
            return ggh__mav
        return impl
    raise BodoError(f'bytes.fromhex not supported with argument type {hex_str}'
        )


@overload(operator.setitem)
def binary_arr_setitem(arr, ind, val):
    if arr != binary_array_type:
        return
    if val == types.none or isinstance(val, types.optional):
        return
    if val != bytes_type:
        raise BodoError(
            f'setitem for Binary Array only supported with bytes value and integer indexing'
            )
    if isinstance(ind, types.Integer):

        def impl(arr, ind, val):
            arr._data[ind] = bodo.libs.binary_arr_ext.cast_bytes_uint8array(val
                )
        return impl
    raise BodoError(
        f'setitem for Binary Array with indexing type {ind} not supported.')


def create_binary_cmp_op_overload(op):

    def overload_binary_cmp(lhs, rhs):
        epu__tpsqm = lhs == binary_array_type
        bkff__anph = rhs == binary_array_type
        zxd__meao = 'lhs' if epu__tpsqm else 'rhs'
        skgkq__frhku = 'def impl(lhs, rhs):\n'
        skgkq__frhku += '  numba.parfors.parfor.init_prange()\n'
        skgkq__frhku += f'  n = len({zxd__meao})\n'
        skgkq__frhku += (
            '  out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(n)\n')
        skgkq__frhku += '  for i in numba.parfors.parfor.internal_prange(n):\n'
        sirgw__ohh = []
        if epu__tpsqm:
            sirgw__ohh.append('bodo.libs.array_kernels.isna(lhs, i)')
        if bkff__anph:
            sirgw__ohh.append('bodo.libs.array_kernels.isna(rhs, i)')
        skgkq__frhku += f"    if {' or '.join(sirgw__ohh)}:\n"
        skgkq__frhku += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
        skgkq__frhku += '      continue\n'
        wlub__huzvd = 'lhs[i]' if epu__tpsqm else 'lhs'
        fvfv__deb = 'rhs[i]' if bkff__anph else 'rhs'
        skgkq__frhku += f'    out_arr[i] = op({wlub__huzvd}, {fvfv__deb})\n'
        skgkq__frhku += '  return out_arr\n'
        gxb__mojor = {}
        exec(skgkq__frhku, {'bodo': bodo, 'numba': numba, 'op': op}, gxb__mojor
            )
        return gxb__mojor['impl']
    return overload_binary_cmp


lower_builtin('getiter', binary_array_type)(numba.np.arrayobj.getiter_array)


def pre_alloc_binary_arr_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


from numba.parfors.array_analysis import ArrayAnalysis
(ArrayAnalysis._analyze_op_call_bodo_libs_binary_arr_ext_pre_alloc_binary_array
    ) = pre_alloc_binary_arr_equiv
