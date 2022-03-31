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
        all__plh, = args
        mfwh__kuy = context.make_helper(builder, binary_array_type)
        mfwh__kuy.data = all__plh
        context.nrt.incref(builder, data_typ, all__plh)
        return mfwh__kuy._getvalue()
    return binary_array_type(data_typ), codegen


@intrinsic
def init_bytes_type(typingctx, data_typ, length_type):
    assert data_typ == types.Array(types.uint8, 1, 'C')
    assert length_type == types.int64

    def codegen(context, builder, sig, args):
        laqw__jide = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        gyy__msbvj = args[1]
        qch__ulmvr = cgutils.create_struct_proxy(bytes_type)(context, builder)
        qch__ulmvr.meminfo = context.nrt.meminfo_alloc(builder, gyy__msbvj)
        qch__ulmvr.nitems = gyy__msbvj
        qch__ulmvr.itemsize = lir.Constant(qch__ulmvr.itemsize.type, 1)
        qch__ulmvr.data = context.nrt.meminfo_data(builder, qch__ulmvr.meminfo)
        qch__ulmvr.parent = cgutils.get_null_value(qch__ulmvr.parent.type)
        qch__ulmvr.shape = cgutils.pack_array(builder, [gyy__msbvj],
            context.get_value_type(types.intp))
        qch__ulmvr.strides = laqw__jide.strides
        cgutils.memcpy(builder, qch__ulmvr.data, laqw__jide.data, gyy__msbvj)
        return qch__ulmvr._getvalue()
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
    kfj__bze = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

    def impl(arr):
        gyy__msbvj = len(arr) * 2
        output = numba.cpython.unicode._empty_string(kfj__bze, gyy__msbvj, 1)
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
        imjb__ujly = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=args[0])
        ale__vhr = cgutils.create_struct_proxy(sig.args[1])(context,
            builder, value=args[1])
        ftizj__ktpyy = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(64)])
        nygym__hxfhb = cgutils.get_or_insert_function(builder.module,
            ftizj__ktpyy, name='bytes_to_hex')
        builder.call(nygym__hxfhb, (imjb__ujly.data, ale__vhr.data,
            ale__vhr.nitems))
    return types.void(output, arr), codegen


@overload(operator.getitem, no_unliteral=True)
def binary_arr_getitem(arr, ind):
    if arr != binary_array_type:
        return
    if isinstance(ind, types.Integer):

        def impl(arr, ind):
            wbbwv__yook = arr._data[ind]
            return init_bytes_type(wbbwv__yook, len(wbbwv__yook))
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
        kfj__bze = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

        def impl(hex_str):
            if not hex_str._is_ascii or hex_str._kind != kfj__bze:
                raise TypeError(
                    'bytes.fromhex is only supported on ascii strings')
            all__plh = np.empty(len(hex_str) // 2, np.uint8)
            gyy__msbvj = _bytes_fromhex(all__plh.ctypes, hex_str._data, len
                (hex_str))
            zyvd__bbrw = init_bytes_type(all__plh, gyy__msbvj)
            return zyvd__bbrw
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
        kzbrq__qoxs = lhs == binary_array_type
        zwxu__pvv = rhs == binary_array_type
        yuihk__gbn = 'lhs' if kzbrq__qoxs else 'rhs'
        uzzn__ftaw = 'def impl(lhs, rhs):\n'
        uzzn__ftaw += '  numba.parfors.parfor.init_prange()\n'
        uzzn__ftaw += f'  n = len({yuihk__gbn})\n'
        uzzn__ftaw += (
            '  out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(n)\n')
        uzzn__ftaw += '  for i in numba.parfors.parfor.internal_prange(n):\n'
        gnapr__eggam = []
        if kzbrq__qoxs:
            gnapr__eggam.append('bodo.libs.array_kernels.isna(lhs, i)')
        if zwxu__pvv:
            gnapr__eggam.append('bodo.libs.array_kernels.isna(rhs, i)')
        uzzn__ftaw += f"    if {' or '.join(gnapr__eggam)}:\n"
        uzzn__ftaw += '      bodo.libs.array_kernels.setna(out_arr, i)\n'
        uzzn__ftaw += '      continue\n'
        ptcf__feb = 'lhs[i]' if kzbrq__qoxs else 'lhs'
        dkir__edeb = 'rhs[i]' if zwxu__pvv else 'rhs'
        uzzn__ftaw += f'    out_arr[i] = op({ptcf__feb}, {dkir__edeb})\n'
        uzzn__ftaw += '  return out_arr\n'
        emy__yyuf = {}
        exec(uzzn__ftaw, {'bodo': bodo, 'numba': numba, 'op': op}, emy__yyuf)
        return emy__yyuf['impl']
    return overload_binary_cmp


lower_builtin('getiter', binary_array_type)(numba.np.arrayobj.getiter_array)


def pre_alloc_binary_arr_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


from numba.parfors.array_analysis import ArrayAnalysis
(ArrayAnalysis._analyze_op_call_bodo_libs_binary_arr_ext_pre_alloc_binary_array
    ) = pre_alloc_binary_arr_equiv
