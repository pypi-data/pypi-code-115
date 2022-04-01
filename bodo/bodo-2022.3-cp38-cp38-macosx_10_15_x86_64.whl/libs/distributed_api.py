import atexit
import datetime
import operator
import sys
import time
import warnings
from collections import defaultdict
from decimal import Decimal
from enum import Enum
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from mpi4py import MPI
from numba.core import cgutils, ir_utils, types
from numba.core.typing import signature
from numba.core.typing.builtins import IndexValueType
from numba.core.typing.templates import AbstractTemplate, infer_global
from numba.extending import intrinsic, models, overload, register_jitable, register_model
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
from bodo.hiframes.datetime_date_ext import datetime_date_array_type
from bodo.hiframes.datetime_timedelta_ext import datetime_timedelta_array_type
from bodo.hiframes.pd_categorical_ext import CategoricalArrayType
from bodo.libs import hdist
from bodo.libs.array_item_arr_ext import ArrayItemArrayType, np_offset_type, offset_type
from bodo.libs.binary_arr_ext import binary_array_type
from bodo.libs.bool_arr_ext import boolean_array
from bodo.libs.decimal_arr_ext import DecimalArrayType
from bodo.libs.int_arr_ext import IntegerArrayType, set_bit_to_arr
from bodo.libs.interval_arr_ext import IntervalArrayType
from bodo.libs.map_arr_ext import MapArrayType
from bodo.libs.pd_datetime_arr_ext import DatetimeArrayType
from bodo.libs.str_arr_ext import convert_len_arr_to_offset, get_bit_bitmap, get_data_ptr, get_null_bitmap_ptr, get_offset_ptr, num_total_chars, pre_alloc_string_array, set_bit_to, string_array_type
from bodo.libs.struct_arr_ext import StructArrayType
from bodo.libs.tuple_arr_ext import TupleArrayType
from bodo.utils.typing import BodoError, BodoWarning, decode_if_dict_array, is_overload_false, is_overload_none, is_str_arr_type
from bodo.utils.utils import CTypeEnum, check_and_propagate_cpp_exception, empty_like_type, numba_to_c_type
ll.add_symbol('dist_get_time', hdist.dist_get_time)
ll.add_symbol('get_time', hdist.get_time)
ll.add_symbol('dist_reduce', hdist.dist_reduce)
ll.add_symbol('dist_arr_reduce', hdist.dist_arr_reduce)
ll.add_symbol('dist_exscan', hdist.dist_exscan)
ll.add_symbol('dist_irecv', hdist.dist_irecv)
ll.add_symbol('dist_isend', hdist.dist_isend)
ll.add_symbol('dist_wait', hdist.dist_wait)
ll.add_symbol('dist_get_item_pointer', hdist.dist_get_item_pointer)
ll.add_symbol('get_dummy_ptr', hdist.get_dummy_ptr)
ll.add_symbol('allgather', hdist.allgather)
ll.add_symbol('comm_req_alloc', hdist.comm_req_alloc)
ll.add_symbol('comm_req_dealloc', hdist.comm_req_dealloc)
ll.add_symbol('req_array_setitem', hdist.req_array_setitem)
ll.add_symbol('dist_waitall', hdist.dist_waitall)
ll.add_symbol('oneD_reshape_shuffle', hdist.oneD_reshape_shuffle)
ll.add_symbol('permutation_int', hdist.permutation_int)
ll.add_symbol('permutation_array_index', hdist.permutation_array_index)
ll.add_symbol('c_get_rank', hdist.dist_get_rank)
ll.add_symbol('c_get_size', hdist.dist_get_size)
ll.add_symbol('c_barrier', hdist.barrier)
ll.add_symbol('c_alltoall', hdist.c_alltoall)
ll.add_symbol('c_gather_scalar', hdist.c_gather_scalar)
ll.add_symbol('c_gatherv', hdist.c_gatherv)
ll.add_symbol('c_scatterv', hdist.c_scatterv)
ll.add_symbol('c_allgatherv', hdist.c_allgatherv)
ll.add_symbol('c_bcast', hdist.c_bcast)
ll.add_symbol('c_recv', hdist.dist_recv)
ll.add_symbol('c_send', hdist.dist_send)
mpi_req_numba_type = getattr(types, 'int' + str(8 * hdist.mpi_req_num_bytes))
MPI_ROOT = 0
ANY_SOURCE = np.int32(hdist.ANY_SOURCE)


class Reduce_Type(Enum):
    Sum = 0
    Prod = 1
    Min = 2
    Max = 3
    Argmin = 4
    Argmax = 5
    Or = 6
    Concat = 7
    No_Op = 8


_get_rank = types.ExternalFunction('c_get_rank', types.int32())
_get_size = types.ExternalFunction('c_get_size', types.int32())
_barrier = types.ExternalFunction('c_barrier', types.int32())


@numba.njit
def get_rank():
    return _get_rank()


@numba.njit
def get_size():
    return _get_size()


@numba.njit
def barrier():
    _barrier()


_get_time = types.ExternalFunction('get_time', types.float64())
dist_time = types.ExternalFunction('dist_get_time', types.float64())


@overload(time.time, no_unliteral=True)
def overload_time_time():
    return lambda : _get_time()


@numba.generated_jit(nopython=True)
def get_type_enum(arr):
    arr = arr.instance_type if isinstance(arr, types.TypeRef) else arr
    dtype = arr.dtype
    if isinstance(dtype, bodo.hiframes.pd_categorical_ext.PDCategoricalDtype):
        dtype = bodo.hiframes.pd_categorical_ext.get_categories_int_type(dtype)
    typ_val = numba_to_c_type(dtype)
    return lambda arr: np.int32(typ_val)


INT_MAX = np.iinfo(np.int32).max
_send = types.ExternalFunction('c_send', types.void(types.voidptr, types.
    int32, types.int32, types.int32, types.int32))


@numba.njit
def send(val, rank, tag):
    send_arr = np.full(1, val)
    ioj__mdx = get_type_enum(send_arr)
    _send(send_arr.ctypes, 1, ioj__mdx, rank, tag)


_recv = types.ExternalFunction('c_recv', types.void(types.voidptr, types.
    int32, types.int32, types.int32, types.int32))


@numba.njit
def recv(dtype, rank, tag):
    recv_arr = np.empty(1, dtype)
    ioj__mdx = get_type_enum(recv_arr)
    _recv(recv_arr.ctypes, 1, ioj__mdx, rank, tag)
    return recv_arr[0]


_isend = types.ExternalFunction('dist_isend', mpi_req_numba_type(types.
    voidptr, types.int32, types.int32, types.int32, types.int32, types.bool_))


@numba.generated_jit(nopython=True)
def isend(arr, size, pe, tag, cond=True):
    if isinstance(arr, types.Array):

        def impl(arr, size, pe, tag, cond=True):
            ioj__mdx = get_type_enum(arr)
            return _isend(arr.ctypes, size, ioj__mdx, pe, tag, cond)
        return impl
    if isinstance(arr, (IntegerArrayType, DecimalArrayType)) or arr in (
        boolean_array, datetime_date_array_type):
        ioj__mdx = np.int32(numba_to_c_type(arr.dtype))
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))

        def impl_nullable(arr, size, pe, tag, cond=True):
            nbhoj__zdfhm = size + 7 >> 3
            exa__uxnsj = _isend(arr._data.ctypes, size, ioj__mdx, pe, tag, cond
                )
            rbj__vlojb = _isend(arr._null_bitmap.ctypes, nbhoj__zdfhm,
                talnx__onhi, pe, tag, cond)
            return exa__uxnsj, rbj__vlojb
        return impl_nullable
    if is_str_arr_type(arr) or arr == binary_array_type:
        pyfo__ehmrd = np.int32(numba_to_c_type(offset_type))
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))

        def impl_str_arr(arr, size, pe, tag, cond=True):
            arr = decode_if_dict_array(arr)
            klo__xrb = np.int64(bodo.libs.str_arr_ext.num_total_chars(arr))
            send(klo__xrb, pe, tag - 1)
            nbhoj__zdfhm = size + 7 >> 3
            _send(bodo.libs.str_arr_ext.get_offset_ptr(arr), size + 1,
                pyfo__ehmrd, pe, tag)
            _send(bodo.libs.str_arr_ext.get_data_ptr(arr), klo__xrb,
                talnx__onhi, pe, tag)
            _send(bodo.libs.str_arr_ext.get_null_bitmap_ptr(arr),
                nbhoj__zdfhm, talnx__onhi, pe, tag)
            return None
        return impl_str_arr
    typ_enum = numba_to_c_type(types.uint8)

    def impl_voidptr(arr, size, pe, tag, cond=True):
        return _isend(arr, size, typ_enum, pe, tag, cond)
    return impl_voidptr


_irecv = types.ExternalFunction('dist_irecv', mpi_req_numba_type(types.
    voidptr, types.int32, types.int32, types.int32, types.int32, types.bool_))


@numba.generated_jit(nopython=True)
def irecv(arr, size, pe, tag, cond=True):
    if isinstance(arr, types.Array):

        def impl(arr, size, pe, tag, cond=True):
            ioj__mdx = get_type_enum(arr)
            return _irecv(arr.ctypes, size, ioj__mdx, pe, tag, cond)
        return impl
    if isinstance(arr, (IntegerArrayType, DecimalArrayType)) or arr in (
        boolean_array, datetime_date_array_type):
        ioj__mdx = np.int32(numba_to_c_type(arr.dtype))
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))

        def impl_nullable(arr, size, pe, tag, cond=True):
            nbhoj__zdfhm = size + 7 >> 3
            exa__uxnsj = _irecv(arr._data.ctypes, size, ioj__mdx, pe, tag, cond
                )
            rbj__vlojb = _irecv(arr._null_bitmap.ctypes, nbhoj__zdfhm,
                talnx__onhi, pe, tag, cond)
            return exa__uxnsj, rbj__vlojb
        return impl_nullable
    if arr in [binary_array_type, string_array_type]:
        pyfo__ehmrd = np.int32(numba_to_c_type(offset_type))
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))
        if arr == binary_array_type:
            jheng__wnhw = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
        else:
            jheng__wnhw = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
        gejat__tmsyz = f"""def impl(arr, size, pe, tag, cond=True):
            # recv the number of string characters and resize buffer to proper size
            n_chars = bodo.libs.distributed_api.recv(np.int64, pe, tag - 1)
            new_arr = {jheng__wnhw}(size, n_chars)
            bodo.libs.str_arr_ext.move_str_binary_arr_payload(arr, new_arr)

            n_bytes = (size + 7) >> 3
            bodo.libs.distributed_api._recv(
                bodo.libs.str_arr_ext.get_offset_ptr(arr),
                size + 1,
                offset_typ_enum,
                pe,
                tag,
            )
            bodo.libs.distributed_api._recv(
                bodo.libs.str_arr_ext.get_data_ptr(arr), n_chars, char_typ_enum, pe, tag
            )
            bodo.libs.distributed_api._recv(
                bodo.libs.str_arr_ext.get_null_bitmap_ptr(arr),
                n_bytes,
                char_typ_enum,
                pe,
                tag,
            )
            return None"""
        gotlz__avr = dict()
        exec(gejat__tmsyz, {'bodo': bodo, 'np': np, 'offset_typ_enum':
            pyfo__ehmrd, 'char_typ_enum': talnx__onhi}, gotlz__avr)
        impl = gotlz__avr['impl']
        return impl
    raise BodoError(f'irecv(): array type {arr} not supported yet')


_alltoall = types.ExternalFunction('c_alltoall', types.void(types.voidptr,
    types.voidptr, types.int32, types.int32))


@numba.njit
def alltoall(send_arr, recv_arr, count):
    assert count < INT_MAX
    ioj__mdx = get_type_enum(send_arr)
    _alltoall(send_arr.ctypes, recv_arr.ctypes, np.int32(count), ioj__mdx)


@numba.generated_jit(nopython=True)
def gather_scalar(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
    data = types.unliteral(data)
    typ_val = numba_to_c_type(data)
    dtype = data

    def gather_scalar_impl(data, allgather=False, warn_if_rep=True, root=
        MPI_ROOT):
        n_pes = bodo.libs.distributed_api.get_size()
        rank = bodo.libs.distributed_api.get_rank()
        send = np.full(1, data, dtype)
        rbdx__inrve = n_pes if rank == root or allgather else 0
        dtpoh__cckgt = np.empty(rbdx__inrve, dtype)
        c_gather_scalar(send.ctypes, dtpoh__cckgt.ctypes, np.int32(typ_val),
            allgather, np.int32(root))
        return dtpoh__cckgt
    return gather_scalar_impl


c_gather_scalar = types.ExternalFunction('c_gather_scalar', types.void(
    types.voidptr, types.voidptr, types.int32, types.bool_, types.int32))
c_gatherv = types.ExternalFunction('c_gatherv', types.void(types.voidptr,
    types.int32, types.voidptr, types.voidptr, types.voidptr, types.int32,
    types.bool_, types.int32))
c_scatterv = types.ExternalFunction('c_scatterv', types.void(types.voidptr,
    types.voidptr, types.voidptr, types.voidptr, types.int32, types.int32))


@intrinsic
def value_to_ptr(typingctx, val_tp=None):

    def codegen(context, builder, sig, args):
        mqj__xiwv = cgutils.alloca_once(builder, args[0].type)
        builder.store(args[0], mqj__xiwv)
        return builder.bitcast(mqj__xiwv, lir.IntType(8).as_pointer())
    return types.voidptr(val_tp), codegen


@intrinsic
def load_val_ptr(typingctx, ptr_tp, val_tp=None):

    def codegen(context, builder, sig, args):
        mqj__xiwv = builder.bitcast(args[0], args[1].type.as_pointer())
        return builder.load(mqj__xiwv)
    return val_tp(ptr_tp, val_tp), codegen


_dist_reduce = types.ExternalFunction('dist_reduce', types.void(types.
    voidptr, types.voidptr, types.int32, types.int32))
_dist_arr_reduce = types.ExternalFunction('dist_arr_reduce', types.void(
    types.voidptr, types.int64, types.int32, types.int32))


@numba.generated_jit(nopython=True)
def dist_reduce(value, reduce_op):
    if isinstance(value, types.Array):
        typ_enum = np.int32(numba_to_c_type(value.dtype))

        def impl_arr(value, reduce_op):
            A = np.ascontiguousarray(value)
            _dist_arr_reduce(A.ctypes, A.size, reduce_op, typ_enum)
            return A
        return impl_arr
    hwakh__rutr = types.unliteral(value)
    if isinstance(hwakh__rutr, IndexValueType):
        hwakh__rutr = hwakh__rutr.val_typ
        zyl__wqhan = [types.bool_, types.uint8, types.int8, types.uint16,
            types.int16, types.uint32, types.int32, types.float32, types.
            float64]
        if not sys.platform.startswith('win'):
            zyl__wqhan.append(types.int64)
            zyl__wqhan.append(bodo.datetime64ns)
            zyl__wqhan.append(bodo.timedelta64ns)
            zyl__wqhan.append(bodo.datetime_date_type)
        if hwakh__rutr not in zyl__wqhan:
            raise BodoError('argmin/argmax not supported for type {}'.
                format(hwakh__rutr))
    typ_enum = np.int32(numba_to_c_type(hwakh__rutr))

    def impl(value, reduce_op):
        cky__rzpaz = value_to_ptr(value)
        aww__cqqgj = value_to_ptr(value)
        _dist_reduce(cky__rzpaz, aww__cqqgj, reduce_op, typ_enum)
        return load_val_ptr(aww__cqqgj, value)
    return impl


_dist_exscan = types.ExternalFunction('dist_exscan', types.void(types.
    voidptr, types.voidptr, types.int32, types.int32))


@numba.generated_jit(nopython=True)
def dist_exscan(value, reduce_op):
    hwakh__rutr = types.unliteral(value)
    typ_enum = np.int32(numba_to_c_type(hwakh__rutr))
    opert__vvqh = hwakh__rutr(0)

    def impl(value, reduce_op):
        cky__rzpaz = value_to_ptr(value)
        aww__cqqgj = value_to_ptr(opert__vvqh)
        _dist_exscan(cky__rzpaz, aww__cqqgj, reduce_op, typ_enum)
        return load_val_ptr(aww__cqqgj, value)
    return impl


@numba.njit
def get_bit(bits, i):
    return bits[i >> 3] >> (i & 7) & 1


@numba.njit
def copy_gathered_null_bytes(null_bitmap_ptr, tmp_null_bytes,
    recv_counts_nulls, recv_counts):
    jtbyh__dkd = 0
    fedt__gepn = 0
    for i in range(len(recv_counts)):
        usu__ynw = recv_counts[i]
        nbhoj__zdfhm = recv_counts_nulls[i]
        cox__eudl = tmp_null_bytes[jtbyh__dkd:jtbyh__dkd + nbhoj__zdfhm]
        for lrbsc__gugfu in range(usu__ynw):
            set_bit_to(null_bitmap_ptr, fedt__gepn, get_bit(cox__eudl,
                lrbsc__gugfu))
            fedt__gepn += 1
        jtbyh__dkd += nbhoj__zdfhm


@numba.generated_jit(nopython=True)
def gatherv(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
    from bodo.libs.csr_matrix_ext import CSRMatrixType
    bodo.hiframes.pd_dataframe_ext.check_runtime_cols_unsupported(data,
        'bodo.gatherv()')
    if isinstance(data, CategoricalArrayType):

        def impl_cat(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
            yqcht__qvt = bodo.gatherv(data.codes, allgather, root=root)
            return bodo.hiframes.pd_categorical_ext.init_categorical_array(
                yqcht__qvt, data.dtype)
        return impl_cat
    if isinstance(data, types.Array):
        typ_val = numba_to_c_type(data.dtype)

        def gatherv_impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            data = np.ascontiguousarray(data)
            rank = bodo.libs.distributed_api.get_rank()
            ldxc__xqco = data.size
            recv_counts = gather_scalar(np.int32(ldxc__xqco), allgather,
                root=root)
            vqi__cfs = recv_counts.sum()
            rzja__uce = empty_like_type(vqi__cfs, data)
            baep__fsgnv = np.empty(1, np.int32)
            if rank == root or allgather:
                baep__fsgnv = bodo.ir.join.calc_disp(recv_counts)
            c_gatherv(data.ctypes, np.int32(ldxc__xqco), rzja__uce.ctypes,
                recv_counts.ctypes, baep__fsgnv.ctypes, np.int32(typ_val),
                allgather, np.int32(root))
            return rzja__uce.reshape((-1,) + data.shape[1:])
        return gatherv_impl
    if is_str_arr_type(data):

        def gatherv_str_arr_impl(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            data = decode_if_dict_array(data)
            rzja__uce = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.str_arr_ext.init_str_arr(rzja__uce)
        return gatherv_str_arr_impl
    if data == binary_array_type:

        def gatherv_binary_arr_impl(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            rzja__uce = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.binary_arr_ext.init_binary_arr(rzja__uce)
        return gatherv_binary_arr_impl
    if data == datetime_timedelta_array_type:
        typ_val = numba_to_c_type(types.int64)
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))

        def gatherv_impl_int_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            ldxc__xqco = len(data)
            nbhoj__zdfhm = ldxc__xqco + 7 >> 3
            recv_counts = gather_scalar(np.int32(ldxc__xqco), allgather,
                root=root)
            vqi__cfs = recv_counts.sum()
            rzja__uce = empty_like_type(vqi__cfs, data)
            baep__fsgnv = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            cga__mwfx = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                baep__fsgnv = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                cga__mwfx = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(data._days_data.ctypes, np.int32(ldxc__xqco),
                rzja__uce._days_data.ctypes, recv_counts.ctypes,
                baep__fsgnv.ctypes, np.int32(typ_val), allgather, np.int32(
                root))
            c_gatherv(data._seconds_data.ctypes, np.int32(ldxc__xqco),
                rzja__uce._seconds_data.ctypes, recv_counts.ctypes,
                baep__fsgnv.ctypes, np.int32(typ_val), allgather, np.int32(
                root))
            c_gatherv(data._microseconds_data.ctypes, np.int32(ldxc__xqco),
                rzja__uce._microseconds_data.ctypes, recv_counts.ctypes,
                baep__fsgnv.ctypes, np.int32(typ_val), allgather, np.int32(
                root))
            c_gatherv(data._null_bitmap.ctypes, np.int32(nbhoj__zdfhm),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, cga__mwfx.
                ctypes, talnx__onhi, allgather, np.int32(root))
            copy_gathered_null_bytes(rzja__uce._null_bitmap.ctypes,
                tmp_null_bytes, recv_counts_nulls, recv_counts)
            return rzja__uce
        return gatherv_impl_int_arr
    if isinstance(data, (IntegerArrayType, DecimalArrayType)) or data in (
        boolean_array, datetime_date_array_type):
        typ_val = numba_to_c_type(data.dtype)
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))

        def gatherv_impl_int_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            ldxc__xqco = len(data)
            nbhoj__zdfhm = ldxc__xqco + 7 >> 3
            recv_counts = gather_scalar(np.int32(ldxc__xqco), allgather,
                root=root)
            vqi__cfs = recv_counts.sum()
            rzja__uce = empty_like_type(vqi__cfs, data)
            baep__fsgnv = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            cga__mwfx = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                baep__fsgnv = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                cga__mwfx = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(data._data.ctypes, np.int32(ldxc__xqco), rzja__uce.
                _data.ctypes, recv_counts.ctypes, baep__fsgnv.ctypes, np.
                int32(typ_val), allgather, np.int32(root))
            c_gatherv(data._null_bitmap.ctypes, np.int32(nbhoj__zdfhm),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, cga__mwfx.
                ctypes, talnx__onhi, allgather, np.int32(root))
            copy_gathered_null_bytes(rzja__uce._null_bitmap.ctypes,
                tmp_null_bytes, recv_counts_nulls, recv_counts)
            return rzja__uce
        return gatherv_impl_int_arr
    if isinstance(data, DatetimeArrayType):
        jvz__crcza = data.tz

        def impl_pd_datetime_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            eux__uag = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.pd_datetime_arr_ext.init_pandas_datetime_array(
                eux__uag, jvz__crcza)
        return impl_pd_datetime_arr
    if isinstance(data, IntervalArrayType):

        def impl_interval_arr(data, allgather=False, warn_if_rep=True, root
            =MPI_ROOT):
            zux__lmm = bodo.gatherv(data._left, allgather, warn_if_rep, root)
            mhn__zdiul = bodo.gatherv(data._right, allgather, warn_if_rep, root
                )
            return bodo.libs.interval_arr_ext.init_interval_array(zux__lmm,
                mhn__zdiul)
        return impl_interval_arr
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            puol__buqni = bodo.hiframes.pd_series_ext.get_series_name(data)
            out_arr = bodo.libs.distributed_api.gatherv(arr, allgather,
                warn_if_rep, root)
            stv__kptjl = bodo.gatherv(index, allgather, warn_if_rep, root)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                stv__kptjl, puol__buqni)
        return impl
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):
        byfl__wys = np.iinfo(np.int64).max
        syqsl__mrz = np.iinfo(np.int64).min

        def impl_range_index(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            start = data._start
            stop = data._stop
            if len(data) == 0:
                start = byfl__wys
                stop = syqsl__mrz
            start = bodo.libs.distributed_api.dist_reduce(start, np.int32(
                Reduce_Type.Min.value))
            stop = bodo.libs.distributed_api.dist_reduce(stop, np.int32(
                Reduce_Type.Max.value))
            total_len = bodo.libs.distributed_api.dist_reduce(len(data), np
                .int32(Reduce_Type.Sum.value))
            if start == byfl__wys and stop == syqsl__mrz:
                start = 0
                stop = 0
            yedn__ofadp = max(0, -(-(stop - start) // data._step))
            if yedn__ofadp < total_len:
                stop = start + data._step * total_len
            if bodo.get_rank() != root and not allgather:
                start = 0
                stop = 0
            return bodo.hiframes.pd_index_ext.init_range_index(start, stop,
                data._step, data._name)
        return impl_range_index
    if bodo.hiframes.pd_index_ext.is_pd_index_type(data):
        from bodo.hiframes.pd_index_ext import PeriodIndexType
        if isinstance(data, PeriodIndexType):
            pkcr__nppze = data.freq

            def impl_pd_index(data, allgather=False, warn_if_rep=True, root
                =MPI_ROOT):
                arr = bodo.libs.distributed_api.gatherv(data._data,
                    allgather, root=root)
                return bodo.hiframes.pd_index_ext.init_period_index(arr,
                    data._name, pkcr__nppze)
        else:

            def impl_pd_index(data, allgather=False, warn_if_rep=True, root
                =MPI_ROOT):
                arr = bodo.libs.distributed_api.gatherv(data._data,
                    allgather, root=root)
                return bodo.utils.conversion.index_from_array(arr, data._name)
        return impl_pd_index
    if isinstance(data, bodo.hiframes.pd_multi_index_ext.MultiIndexType):

        def impl_multi_index(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            rzja__uce = bodo.gatherv(data._data, allgather, root=root)
            return bodo.hiframes.pd_multi_index_ext.init_multi_index(rzja__uce,
                data._names, data._name)
        return impl_multi_index
    if isinstance(data, bodo.hiframes.table.TableType):
        aaj__igz = {'bodo': bodo, 'get_table_block': bodo.hiframes.table.
            get_table_block, 'ensure_column_unboxed': bodo.hiframes.table.
            ensure_column_unboxed, 'set_table_block': bodo.hiframes.table.
            set_table_block, 'set_table_len': bodo.hiframes.table.
            set_table_len, 'alloc_list_like': bodo.hiframes.table.
            alloc_list_like, 'init_table': bodo.hiframes.table.init_table}
        gejat__tmsyz = f"""def impl_table(data, allgather=False, warn_if_rep=True, root={MPI_ROOT}):
"""
        gejat__tmsyz += '  T = data\n'
        gejat__tmsyz += '  T2 = init_table(T, True)\n'
        for feyyn__mnvo in data.type_to_blk.values():
            aaj__igz[f'arr_inds_{feyyn__mnvo}'] = np.array(data.
                block_to_arr_ind[feyyn__mnvo], dtype=np.int64)
            gejat__tmsyz += (
                f'  arr_list_{feyyn__mnvo} = get_table_block(T, {feyyn__mnvo})\n'
                )
            gejat__tmsyz += f"""  out_arr_list_{feyyn__mnvo} = alloc_list_like(arr_list_{feyyn__mnvo}, True)
"""
            gejat__tmsyz += f'  for i in range(len(arr_list_{feyyn__mnvo})):\n'
            gejat__tmsyz += (
                f'    arr_ind_{feyyn__mnvo} = arr_inds_{feyyn__mnvo}[i]\n')
            gejat__tmsyz += f"""    ensure_column_unboxed(T, arr_list_{feyyn__mnvo}, i, arr_ind_{feyyn__mnvo})
"""
            gejat__tmsyz += f"""    out_arr_{feyyn__mnvo} = bodo.gatherv(arr_list_{feyyn__mnvo}[i], allgather, warn_if_rep, root)
"""
            gejat__tmsyz += (
                f'    out_arr_list_{feyyn__mnvo}[i] = out_arr_{feyyn__mnvo}\n')
            gejat__tmsyz += f"""  T2 = set_table_block(T2, out_arr_list_{feyyn__mnvo}, {feyyn__mnvo})
"""
        gejat__tmsyz += (
            f'  length = T._len if bodo.get_rank() == root or allgather else 0\n'
            )
        gejat__tmsyz += f'  T2 = set_table_len(T2, length)\n'
        gejat__tmsyz += f'  return T2\n'
        gotlz__avr = {}
        exec(gejat__tmsyz, aaj__igz, gotlz__avr)
        uff__nwar = gotlz__avr['impl_table']
        return uff__nwar
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        oze__vvo = len(data.columns)
        if oze__vvo == 0:

            def impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
                index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data
                    )
                fkfa__wpy = bodo.gatherv(index, allgather, warn_if_rep, root)
                return bodo.hiframes.pd_dataframe_ext.init_dataframe((),
                    fkfa__wpy, ())
            return impl
        qtq__vzuo = ', '.join(f'g_data_{i}' for i in range(oze__vvo))
        dcjzg__axseo = bodo.utils.transform.gen_const_tup(data.columns)
        gejat__tmsyz = (
            'def impl_df(data, allgather=False, warn_if_rep=True, root={}):\n'
            .format(MPI_ROOT))
        if data.is_table_format:
            from bodo.transforms.distributed_analysis import Distribution
            uwqbr__kxa = bodo.hiframes.pd_dataframe_ext.DataFrameType(data.
                data, data.index, data.columns, Distribution.REP, True)
            aaj__igz = {'bodo': bodo, 'df_type': uwqbr__kxa}
            qtq__vzuo = 'T2'
            dcjzg__axseo = 'df_type'
            gejat__tmsyz += (
                '  T = bodo.hiframes.pd_dataframe_ext.get_dataframe_table(data)\n'
                )
            gejat__tmsyz += (
                '  T2 = bodo.gatherv(T, allgather, warn_if_rep, root)\n')
        else:
            aaj__igz = {'bodo': bodo}
            for i in range(oze__vvo):
                gejat__tmsyz += (
                    """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                    .format(i, i))
                gejat__tmsyz += (
                    """  g_data_{} = bodo.gatherv(data_{}, allgather, warn_if_rep, root)
"""
                    .format(i, i))
        gejat__tmsyz += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        gejat__tmsyz += (
            '  g_index = bodo.gatherv(index, allgather, warn_if_rep, root)\n')
        gejat__tmsyz += (
            """  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})
"""
            .format(qtq__vzuo, dcjzg__axseo))
        gotlz__avr = {}
        exec(gejat__tmsyz, aaj__igz, gotlz__avr)
        dytyd__rpmu = gotlz__avr['impl_df']
        return dytyd__rpmu
    if isinstance(data, ArrayItemArrayType):
        ylh__mhw = np.int32(numba_to_c_type(types.int32))
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))

        def gatherv_array_item_arr_impl(data, allgather=False, warn_if_rep=
            True, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            ipgnd__ezlu = bodo.libs.array_item_arr_ext.get_offsets(data)
            elceq__fecl = bodo.libs.array_item_arr_ext.get_data(data)
            elceq__fecl = elceq__fecl[:ipgnd__ezlu[-1]]
            ulrho__voyn = bodo.libs.array_item_arr_ext.get_null_bitmap(data)
            ldxc__xqco = len(data)
            amjih__zxgtu = np.empty(ldxc__xqco, np.uint32)
            nbhoj__zdfhm = ldxc__xqco + 7 >> 3
            for i in range(ldxc__xqco):
                amjih__zxgtu[i] = ipgnd__ezlu[i + 1] - ipgnd__ezlu[i]
            recv_counts = gather_scalar(np.int32(ldxc__xqco), allgather,
                root=root)
            vqi__cfs = recv_counts.sum()
            baep__fsgnv = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            cga__mwfx = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                baep__fsgnv = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for bfv__hdf in range(len(recv_counts)):
                    recv_counts_nulls[bfv__hdf] = recv_counts[bfv__hdf
                        ] + 7 >> 3
                cga__mwfx = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            jjx__ddhe = np.empty(vqi__cfs + 1, np.uint32)
            pmvy__zhe = bodo.gatherv(elceq__fecl, allgather, warn_if_rep, root)
            klq__oze = np.empty(vqi__cfs + 7 >> 3, np.uint8)
            c_gatherv(amjih__zxgtu.ctypes, np.int32(ldxc__xqco), jjx__ddhe.
                ctypes, recv_counts.ctypes, baep__fsgnv.ctypes, ylh__mhw,
                allgather, np.int32(root))
            c_gatherv(ulrho__voyn.ctypes, np.int32(nbhoj__zdfhm),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, cga__mwfx.
                ctypes, talnx__onhi, allgather, np.int32(root))
            dummy_use(data)
            gqbc__yulub = np.empty(vqi__cfs + 1, np.uint64)
            convert_len_arr_to_offset(jjx__ddhe.ctypes, gqbc__yulub.ctypes,
                vqi__cfs)
            copy_gathered_null_bytes(klq__oze.ctypes, tmp_null_bytes,
                recv_counts_nulls, recv_counts)
            out_arr = bodo.libs.array_item_arr_ext.init_array_item_array(
                vqi__cfs, pmvy__zhe, gqbc__yulub, klq__oze)
            return out_arr
        return gatherv_array_item_arr_impl
    if isinstance(data, StructArrayType):
        bjh__qmie = data.names
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))

        def impl_struct_arr(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            fzo__xaq = bodo.libs.struct_arr_ext.get_data(data)
            zxbm__gmg = bodo.libs.struct_arr_ext.get_null_bitmap(data)
            glj__ftp = bodo.gatherv(fzo__xaq, allgather=allgather, root=root)
            rank = bodo.libs.distributed_api.get_rank()
            ldxc__xqco = len(data)
            nbhoj__zdfhm = ldxc__xqco + 7 >> 3
            recv_counts = gather_scalar(np.int32(ldxc__xqco), allgather,
                root=root)
            vqi__cfs = recv_counts.sum()
            fgkh__byd = np.empty(vqi__cfs + 7 >> 3, np.uint8)
            recv_counts_nulls = np.empty(1, np.int32)
            cga__mwfx = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                cga__mwfx = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(zxbm__gmg.ctypes, np.int32(nbhoj__zdfhm),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, cga__mwfx.
                ctypes, talnx__onhi, allgather, np.int32(root))
            copy_gathered_null_bytes(fgkh__byd.ctypes, tmp_null_bytes,
                recv_counts_nulls, recv_counts)
            return bodo.libs.struct_arr_ext.init_struct_arr(glj__ftp,
                fgkh__byd, bjh__qmie)
        return impl_struct_arr
    if data == binary_array_type:

        def impl_bin_arr(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            rzja__uce = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.binary_arr_ext.init_binary_arr(rzja__uce)
        return impl_bin_arr
    if isinstance(data, TupleArrayType):

        def impl_tuple_arr(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            rzja__uce = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.tuple_arr_ext.init_tuple_arr(rzja__uce)
        return impl_tuple_arr
    if isinstance(data, MapArrayType):

        def impl_map_arr(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            rzja__uce = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.map_arr_ext.init_map_arr(rzja__uce)
        return impl_map_arr
    if isinstance(data, CSRMatrixType):

        def impl_csr_matrix(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            rzja__uce = bodo.gatherv(data.data, allgather, warn_if_rep, root)
            rtn__oem = bodo.gatherv(data.indices, allgather, warn_if_rep, root)
            yrlo__anqxk = bodo.gatherv(data.indptr, allgather, warn_if_rep,
                root)
            bdhc__zlug = gather_scalar(data.shape[0], allgather, root=root)
            eea__ree = bdhc__zlug.sum()
            oze__vvo = bodo.libs.distributed_api.dist_reduce(data.shape[1],
                np.int32(Reduce_Type.Max.value))
            gcy__efc = np.empty(eea__ree + 1, np.int64)
            rtn__oem = rtn__oem.astype(np.int64)
            gcy__efc[0] = 0
            foo__fctok = 1
            zagr__jjmaq = 0
            for hls__jsvsi in bdhc__zlug:
                for wjgt__xdad in range(hls__jsvsi):
                    tyi__suzox = yrlo__anqxk[zagr__jjmaq + 1] - yrlo__anqxk[
                        zagr__jjmaq]
                    gcy__efc[foo__fctok] = gcy__efc[foo__fctok - 1
                        ] + tyi__suzox
                    foo__fctok += 1
                    zagr__jjmaq += 1
                zagr__jjmaq += 1
            return bodo.libs.csr_matrix_ext.init_csr_matrix(rzja__uce,
                rtn__oem, gcy__efc, (eea__ree, oze__vvo))
        return impl_csr_matrix
    if isinstance(data, types.BaseTuple):
        gejat__tmsyz = (
            'def impl_tuple(data, allgather=False, warn_if_rep=True, root={}):\n'
            .format(MPI_ROOT))
        gejat__tmsyz += '  return ({}{})\n'.format(', '.join(
            'bodo.gatherv(data[{}], allgather, warn_if_rep, root)'.format(i
            ) for i in range(len(data))), ',' if len(data) > 0 else '')
        gotlz__avr = {}
        exec(gejat__tmsyz, {'bodo': bodo}, gotlz__avr)
        exeph__ikyk = gotlz__avr['impl_tuple']
        return exeph__ikyk
    if data is types.none:
        return (lambda data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT: None)
    raise BodoError('gatherv() not available for {}'.format(data))


@numba.generated_jit(nopython=True)
def rebalance(data, dests=None, random=False, random_seed=None, parallel=False
    ):
    bodo.hiframes.pd_dataframe_ext.check_runtime_cols_unsupported(data,
        'bodo.rebalance()')
    gejat__tmsyz = (
        'def impl(data, dests=None, random=False, random_seed=None, parallel=False):\n'
        )
    gejat__tmsyz += '    if random:\n'
    gejat__tmsyz += '        if random_seed is None:\n'
    gejat__tmsyz += '            random = 1\n'
    gejat__tmsyz += '        else:\n'
    gejat__tmsyz += '            random = 2\n'
    gejat__tmsyz += '    if random_seed is None:\n'
    gejat__tmsyz += '        random_seed = -1\n'
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        zuox__zwqza = data
        oze__vvo = len(zuox__zwqza.columns)
        for i in range(oze__vvo):
            gejat__tmsyz += f"""    data_{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {i})
"""
        gejat__tmsyz += """    ind_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data))
"""
        qtq__vzuo = ', '.join(f'data_{i}' for i in range(oze__vvo))
        gejat__tmsyz += ('    info_list_total = [{}, array_to_info(ind_arr)]\n'
            .format(', '.join('array_to_info(data_{})'.format(kausv__hpyf) for
            kausv__hpyf in range(oze__vvo))))
        gejat__tmsyz += (
            '    table_total = arr_info_list_to_table(info_list_total)\n')
        gejat__tmsyz += '    if dests is None:\n'
        gejat__tmsyz += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        gejat__tmsyz += '    else:\n'
        gejat__tmsyz += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        for qdj__sllvm in range(oze__vvo):
            gejat__tmsyz += (
                """    out_arr_{0} = info_to_array(info_from_table(out_table, {0}), data_{0})
"""
                .format(qdj__sllvm))
        gejat__tmsyz += (
            """    out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)
"""
            .format(oze__vvo))
        gejat__tmsyz += '    delete_table(out_table)\n'
        gejat__tmsyz += '    if parallel:\n'
        gejat__tmsyz += '        delete_table(table_total)\n'
        qtq__vzuo = ', '.join('out_arr_{}'.format(i) for i in range(oze__vvo))
        dcjzg__axseo = bodo.utils.transform.gen_const_tup(zuox__zwqza.columns)
        index = 'bodo.utils.conversion.index_from_array(out_arr_index)'
        gejat__tmsyz += (
            '    return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), {}, {})\n'
            .format(qtq__vzuo, index, dcjzg__axseo))
    elif isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):
        gejat__tmsyz += (
            '    data_0 = bodo.hiframes.pd_series_ext.get_series_data(data)\n')
        gejat__tmsyz += """    ind_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(data))
"""
        gejat__tmsyz += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(data)\n')
        gejat__tmsyz += """    table_total = arr_info_list_to_table([array_to_info(data_0), array_to_info(ind_arr)])
"""
        gejat__tmsyz += '    if dests is None:\n'
        gejat__tmsyz += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        gejat__tmsyz += '    else:\n'
        gejat__tmsyz += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        gejat__tmsyz += (
            '    out_arr_0 = info_to_array(info_from_table(out_table, 0), data_0)\n'
            )
        gejat__tmsyz += """    out_arr_index = info_to_array(info_from_table(out_table, 1), ind_arr)
"""
        gejat__tmsyz += '    delete_table(out_table)\n'
        gejat__tmsyz += '    if parallel:\n'
        gejat__tmsyz += '        delete_table(table_total)\n'
        index = 'bodo.utils.conversion.index_from_array(out_arr_index)'
        gejat__tmsyz += f"""    return bodo.hiframes.pd_series_ext.init_series(out_arr_0, {index}, name)
"""
    elif isinstance(data, types.Array):
        assert is_overload_false(random
            ), 'Call random_shuffle instead of rebalance'
        gejat__tmsyz += '    if not parallel:\n'
        gejat__tmsyz += '        return data\n'
        gejat__tmsyz += """    dim0_global_size = bodo.libs.distributed_api.dist_reduce(data.shape[0], np.int32(bodo.libs.distributed_api.Reduce_Type.Sum.value))
"""
        gejat__tmsyz += '    if dests is None:\n'
        gejat__tmsyz += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, bodo.get_size(), bodo.get_rank())
"""
        gejat__tmsyz += '    elif bodo.get_rank() not in dests:\n'
        gejat__tmsyz += '        dim0_local_size = 0\n'
        gejat__tmsyz += '    else:\n'
        gejat__tmsyz += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, len(dests), dests.index(bodo.get_rank()))
"""
        gejat__tmsyz += """    out = np.empty((dim0_local_size,) + tuple(data.shape[1:]), dtype=data.dtype)
"""
        gejat__tmsyz += """    bodo.libs.distributed_api.dist_oneD_reshape_shuffle(out, data, dim0_global_size, dests)
"""
        gejat__tmsyz += '    return out\n'
    elif bodo.utils.utils.is_array_typ(data, False):
        gejat__tmsyz += (
            '    table_total = arr_info_list_to_table([array_to_info(data)])\n'
            )
        gejat__tmsyz += '    if dests is None:\n'
        gejat__tmsyz += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        gejat__tmsyz += '    else:\n'
        gejat__tmsyz += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        gejat__tmsyz += (
            '    out_arr = info_to_array(info_from_table(out_table, 0), data)\n'
            )
        gejat__tmsyz += '    delete_table(out_table)\n'
        gejat__tmsyz += '    if parallel:\n'
        gejat__tmsyz += '        delete_table(table_total)\n'
        gejat__tmsyz += '    return out_arr\n'
    else:
        raise BodoError(f'Type {data} not supported for bodo.rebalance')
    gotlz__avr = {}
    exec(gejat__tmsyz, {'np': np, 'bodo': bodo, 'array_to_info': bodo.libs.
        array.array_to_info, 'shuffle_renormalization': bodo.libs.array.
        shuffle_renormalization, 'shuffle_renormalization_group': bodo.libs
        .array.shuffle_renormalization_group, 'arr_info_list_to_table':
        bodo.libs.array.arr_info_list_to_table, 'info_from_table': bodo.
        libs.array.info_from_table, 'info_to_array': bodo.libs.array.
        info_to_array, 'delete_table': bodo.libs.array.delete_table},
        gotlz__avr)
    impl = gotlz__avr['impl']
    return impl


@numba.generated_jit(nopython=True)
def random_shuffle(data, seed=None, dests=None, parallel=False):
    gejat__tmsyz = 'def impl(data, seed=None, dests=None, parallel=False):\n'
    if isinstance(data, types.Array):
        if not is_overload_none(dests):
            raise BodoError('not supported')
        gejat__tmsyz += '    if seed is None:\n'
        gejat__tmsyz += """        seed = bodo.libs.distributed_api.bcast_scalar(np.random.randint(0, 2**31))
"""
        gejat__tmsyz += '    np.random.seed(seed)\n'
        gejat__tmsyz += '    if not parallel:\n'
        gejat__tmsyz += '        data = data.copy()\n'
        gejat__tmsyz += '        np.random.shuffle(data)\n'
        gejat__tmsyz += '        return data\n'
        gejat__tmsyz += '    else:\n'
        gejat__tmsyz += """        dim0_global_size = bodo.libs.distributed_api.dist_reduce(data.shape[0], np.int32(bodo.libs.distributed_api.Reduce_Type.Sum.value))
"""
        gejat__tmsyz += '        permutation = np.arange(dim0_global_size)\n'
        gejat__tmsyz += '        np.random.shuffle(permutation)\n'
        gejat__tmsyz += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, bodo.get_size(), bodo.get_rank())
"""
        gejat__tmsyz += """        output = np.empty((dim0_local_size,) + tuple(data.shape[1:]), dtype=data.dtype)
"""
        gejat__tmsyz += (
            '        dtype_size = bodo.io.np_io.get_dtype_size(data.dtype)\n')
        gejat__tmsyz += """        bodo.libs.distributed_api.dist_permutation_array_index(output, dim0_global_size, dtype_size, data, permutation, len(permutation))
"""
        gejat__tmsyz += '        return output\n'
    else:
        gejat__tmsyz += """    return bodo.libs.distributed_api.rebalance(data, dests=dests, random=True, random_seed=seed, parallel=parallel)
"""
    gotlz__avr = {}
    exec(gejat__tmsyz, {'np': np, 'bodo': bodo}, gotlz__avr)
    impl = gotlz__avr['impl']
    return impl


@numba.generated_jit(nopython=True)
def allgatherv(data, warn_if_rep=True, root=MPI_ROOT):
    return lambda data, warn_if_rep=True, root=MPI_ROOT: gatherv(data, True,
        warn_if_rep, root)


@numba.njit
def get_scatter_null_bytes_buff(null_bitmap_ptr, sendcounts, sendcounts_nulls):
    if bodo.get_rank() != MPI_ROOT:
        return np.empty(1, np.uint8)
    zlah__twwb = np.empty(sendcounts_nulls.sum(), np.uint8)
    jtbyh__dkd = 0
    fedt__gepn = 0
    for iufh__abgz in range(len(sendcounts)):
        usu__ynw = sendcounts[iufh__abgz]
        nbhoj__zdfhm = sendcounts_nulls[iufh__abgz]
        cox__eudl = zlah__twwb[jtbyh__dkd:jtbyh__dkd + nbhoj__zdfhm]
        for lrbsc__gugfu in range(usu__ynw):
            set_bit_to_arr(cox__eudl, lrbsc__gugfu, get_bit_bitmap(
                null_bitmap_ptr, fedt__gepn))
            fedt__gepn += 1
        jtbyh__dkd += nbhoj__zdfhm
    return zlah__twwb


def _bcast_dtype(data, root=MPI_ROOT):
    try:
        from mpi4py import MPI
    except:
        raise BodoError('mpi4py is required for scatterv')
    skhl__pgc = MPI.COMM_WORLD
    data = skhl__pgc.bcast(data, root)
    return data


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _get_scatterv_send_counts(send_counts, n_pes, n):
    if not is_overload_none(send_counts):
        return lambda send_counts, n_pes, n: send_counts

    def impl(send_counts, n_pes, n):
        send_counts = np.empty(n_pes, np.int32)
        for i in range(n_pes):
            send_counts[i] = get_node_portion(n, n_pes, i)
        return send_counts
    return impl


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _scatterv_np(data, send_counts=None, warn_if_dist=True):
    typ_val = numba_to_c_type(data.dtype)
    wyulp__gmjv = data.ndim
    dtype = data.dtype
    if dtype == types.NPDatetime('ns'):
        dtype = np.dtype('datetime64[ns]')
    elif dtype == types.NPTimedelta('ns'):
        dtype = np.dtype('timedelta64[ns]')
    xpkh__nqo = (0,) * wyulp__gmjv

    def scatterv_arr_impl(data, send_counts=None, warn_if_dist=True):
        rank = bodo.libs.distributed_api.get_rank()
        n_pes = bodo.libs.distributed_api.get_size()
        etbc__bpqvj = np.ascontiguousarray(data)
        onop__ylp = data.ctypes
        kpqw__ohwwm = xpkh__nqo
        if rank == MPI_ROOT:
            kpqw__ohwwm = etbc__bpqvj.shape
        kpqw__ohwwm = bcast_tuple(kpqw__ohwwm)
        lwbzz__hid = get_tuple_prod(kpqw__ohwwm[1:])
        send_counts = _get_scatterv_send_counts(send_counts, n_pes,
            kpqw__ohwwm[0])
        send_counts *= lwbzz__hid
        ldxc__xqco = send_counts[rank]
        ebfp__vdwlm = np.empty(ldxc__xqco, dtype)
        baep__fsgnv = bodo.ir.join.calc_disp(send_counts)
        c_scatterv(onop__ylp, send_counts.ctypes, baep__fsgnv.ctypes,
            ebfp__vdwlm.ctypes, np.int32(ldxc__xqco), np.int32(typ_val))
        return ebfp__vdwlm.reshape((-1,) + kpqw__ohwwm[1:])
    return scatterv_arr_impl


def _get_name_value_for_type(name_typ):
    assert isinstance(name_typ, (types.UnicodeType, types.StringLiteral)
        ) or name_typ == types.none
    return None if name_typ == types.none else '_' + str(ir_utils.next_label())


def get_value_for_type(dtype):
    if isinstance(dtype, types.Array):
        return np.zeros((1,) * dtype.ndim, numba.np.numpy_support.as_dtype(
            dtype.dtype))
    if dtype == string_array_type:
        return pd.array(['A'], 'string')
    if dtype == bodo.dict_str_arr_type:
        import pyarrow as pa
        return pa.array(['a'], type=pa.dictionary(pa.int32(), pa.string()))
    if dtype == binary_array_type:
        return np.array([b'A'], dtype=object)
    if isinstance(dtype, IntegerArrayType):
        iip__wtgv = '{}Int{}'.format('' if dtype.dtype.signed else 'U',
            dtype.dtype.bitwidth)
        return pd.array([3], iip__wtgv)
    if dtype == boolean_array:
        return pd.array([True], 'boolean')
    if isinstance(dtype, DecimalArrayType):
        return np.array([Decimal('32.1')])
    if dtype == datetime_date_array_type:
        return np.array([datetime.date(2011, 8, 9)])
    if dtype == datetime_timedelta_array_type:
        return np.array([datetime.timedelta(33)])
    if bodo.hiframes.pd_index_ext.is_pd_index_type(dtype):
        puol__buqni = _get_name_value_for_type(dtype.name_typ)
        if isinstance(dtype, bodo.hiframes.pd_index_ext.RangeIndexType):
            return pd.RangeIndex(1, name=puol__buqni)
        iqtj__nbidg = bodo.utils.typing.get_index_data_arr_types(dtype)[0]
        arr = get_value_for_type(iqtj__nbidg)
        return pd.Index(arr, name=puol__buqni)
    if isinstance(dtype, bodo.hiframes.pd_multi_index_ext.MultiIndexType):
        import pyarrow as pa
        puol__buqni = _get_name_value_for_type(dtype.name_typ)
        bjh__qmie = tuple(_get_name_value_for_type(t) for t in dtype.names_typ)
        sbyf__yioyf = tuple(get_value_for_type(t) for t in dtype.array_types)
        sbyf__yioyf = tuple(a.to_numpy(False) if isinstance(a, pa.Array) else
            a for a in sbyf__yioyf)
        val = pd.MultiIndex.from_arrays(sbyf__yioyf, names=bjh__qmie)
        val.name = puol__buqni
        return val
    if isinstance(dtype, bodo.hiframes.pd_series_ext.SeriesType):
        puol__buqni = _get_name_value_for_type(dtype.name_typ)
        arr = get_value_for_type(dtype.data)
        index = get_value_for_type(dtype.index)
        return pd.Series(arr, index, name=puol__buqni)
    if isinstance(dtype, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        sbyf__yioyf = tuple(get_value_for_type(t) for t in dtype.data)
        index = get_value_for_type(dtype.index)
        return pd.DataFrame({puol__buqni: arr for puol__buqni, arr in zip(
            dtype.columns, sbyf__yioyf)}, index)
    if isinstance(dtype, CategoricalArrayType):
        return pd.Categorical.from_codes([0], dtype.dtype.categories)
    if isinstance(dtype, types.BaseTuple):
        return tuple(get_value_for_type(t) for t in dtype.types)
    if isinstance(dtype, ArrayItemArrayType):
        return pd.Series([get_value_for_type(dtype.dtype),
            get_value_for_type(dtype.dtype)]).values
    if isinstance(dtype, IntervalArrayType):
        iqtj__nbidg = get_value_for_type(dtype.arr_type)
        return pd.arrays.IntervalArray([pd.Interval(iqtj__nbidg[0],
            iqtj__nbidg[0])])
    raise BodoError(f'get_value_for_type(dtype): Missing data type {dtype}')


def scatterv(data, send_counts=None, warn_if_dist=True):
    rank = bodo.libs.distributed_api.get_rank()
    if rank != MPI_ROOT and data is not None:
        warnings.warn(BodoWarning(
            "bodo.scatterv(): A non-None value for 'data' was found on a rank other than the root. This data won't be sent to any other ranks and will be overwritten with data from rank 0."
            ))
    dtype = bodo.typeof(data)
    dtype = _bcast_dtype(dtype)
    if rank != MPI_ROOT:
        data = get_value_for_type(dtype)
    return scatterv_impl(data, send_counts)


@overload(scatterv)
def scatterv_overload(data, send_counts=None, warn_if_dist=True):
    bodo.hiframes.pd_dataframe_ext.check_runtime_cols_unsupported(data,
        'bodo.scatterv()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
        'bodo.scatterv()')
    return lambda data, send_counts=None, warn_if_dist=True: scatterv_impl(data
        , send_counts)


@numba.generated_jit(nopython=True)
def scatterv_impl(data, send_counts=None, warn_if_dist=True):
    if isinstance(data, types.Array):
        return lambda data, send_counts=None, warn_if_dist=True: _scatterv_np(
            data, send_counts)
    if is_str_arr_type(data) or data == binary_array_type:
        ylh__mhw = np.int32(numba_to_c_type(types.int32))
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))
        if data == binary_array_type:
            jheng__wnhw = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
        else:
            jheng__wnhw = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
        gejat__tmsyz = f"""def impl(
            data, send_counts=None, warn_if_dist=True
        ):  # pragma: no cover
            data = decode_if_dict_array(data)
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            n_all = bodo.libs.distributed_api.bcast_scalar(len(data))

            # convert offsets to lengths of strings
            send_arr_lens = np.empty(
                len(data), np.uint32
            )  # XXX offset type is offset_type, lengths for comm are uint32
            for i in range(len(data)):
                send_arr_lens[i] = bodo.libs.str_arr_ext.get_str_arr_item_length(
                    data, i
                )

            # ------- calculate buffer counts -------

            send_counts = bodo.libs.distributed_api._get_scatterv_send_counts(send_counts, n_pes, n_all)

            # displacements
            displs = bodo.ir.join.calc_disp(send_counts)

            # compute send counts for characters
            send_counts_char = np.empty(n_pes, np.int32)
            if rank == 0:
                curr_str = 0
                for i in range(n_pes):
                    c = 0
                    for _ in range(send_counts[i]):
                        c += send_arr_lens[curr_str]
                        curr_str += 1
                    send_counts_char[i] = c

            bodo.libs.distributed_api.bcast(send_counts_char)

            # displacements for characters
            displs_char = bodo.ir.join.calc_disp(send_counts_char)

            # compute send counts for nulls
            send_counts_nulls = np.empty(n_pes, np.int32)
            for i in range(n_pes):
                send_counts_nulls[i] = (send_counts[i] + 7) >> 3

            # displacements for nulls
            displs_nulls = bodo.ir.join.calc_disp(send_counts_nulls)

            # alloc output array
            n_loc = send_counts[rank]  # total number of elements on this PE
            n_loc_char = send_counts_char[rank]
            recv_arr = {jheng__wnhw}(n_loc, n_loc_char)

            # ----- string lengths -----------

            recv_lens = np.empty(n_loc, np.uint32)
            bodo.libs.distributed_api.c_scatterv(
                send_arr_lens.ctypes,
                send_counts.ctypes,
                displs.ctypes,
                recv_lens.ctypes,
                np.int32(n_loc),
                int32_typ_enum,
            )

            # TODO: don't hardcode offset type. Also, if offset is 32 bit we can
            # use the same buffer
            bodo.libs.str_arr_ext.convert_len_arr_to_offset(recv_lens.ctypes, bodo.libs.str_arr_ext.get_offset_ptr(recv_arr), n_loc)

            # ----- string characters -----------

            bodo.libs.distributed_api.c_scatterv(
                bodo.libs.str_arr_ext.get_data_ptr(data),
                send_counts_char.ctypes,
                displs_char.ctypes,
                bodo.libs.str_arr_ext.get_data_ptr(recv_arr),
                np.int32(n_loc_char),
                char_typ_enum,
            )

            # ----------- null bitmap -------------

            n_recv_bytes = (n_loc + 7) >> 3

            send_null_bitmap = bodo.libs.distributed_api.get_scatter_null_bytes_buff(
                bodo.libs.str_arr_ext.get_null_bitmap_ptr(data), send_counts, send_counts_nulls
            )

            bodo.libs.distributed_api.c_scatterv(
                send_null_bitmap.ctypes,
                send_counts_nulls.ctypes,
                displs_nulls.ctypes,
                bodo.libs.str_arr_ext.get_null_bitmap_ptr(recv_arr),
                np.int32(n_recv_bytes),
                char_typ_enum,
            )

            return recv_arr"""
        gotlz__avr = dict()
        exec(gejat__tmsyz, {'bodo': bodo, 'np': np, 'int32_typ_enum':
            ylh__mhw, 'char_typ_enum': talnx__onhi, 'decode_if_dict_array':
            decode_if_dict_array}, gotlz__avr)
        impl = gotlz__avr['impl']
        return impl
    if isinstance(data, ArrayItemArrayType):
        ylh__mhw = np.int32(numba_to_c_type(types.int32))
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))

        def scatterv_array_item_impl(data, send_counts=None, warn_if_dist=True
            ):
            jsy__bsey = bodo.libs.array_item_arr_ext.get_offsets(data)
            tzwl__kooh = bodo.libs.array_item_arr_ext.get_data(data)
            tzwl__kooh = tzwl__kooh[:jsy__bsey[-1]]
            bkj__hxslc = bodo.libs.array_item_arr_ext.get_null_bitmap(data)
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            pwf__ubp = bcast_scalar(len(data))
            ucy__bkj = np.empty(len(data), np.uint32)
            for i in range(len(data)):
                ucy__bkj[i] = jsy__bsey[i + 1] - jsy__bsey[i]
            send_counts = _get_scatterv_send_counts(send_counts, n_pes,
                pwf__ubp)
            baep__fsgnv = bodo.ir.join.calc_disp(send_counts)
            xnu__jdd = np.empty(n_pes, np.int32)
            if rank == 0:
                rglvy__rep = 0
                for i in range(n_pes):
                    bxwzv__ilhtk = 0
                    for wjgt__xdad in range(send_counts[i]):
                        bxwzv__ilhtk += ucy__bkj[rglvy__rep]
                        rglvy__rep += 1
                    xnu__jdd[i] = bxwzv__ilhtk
            bcast(xnu__jdd)
            fnhb__rchm = np.empty(n_pes, np.int32)
            for i in range(n_pes):
                fnhb__rchm[i] = send_counts[i] + 7 >> 3
            cga__mwfx = bodo.ir.join.calc_disp(fnhb__rchm)
            ldxc__xqco = send_counts[rank]
            esh__mnk = np.empty(ldxc__xqco + 1, np_offset_type)
            zpx__fjlx = bodo.libs.distributed_api.scatterv_impl(tzwl__kooh,
                xnu__jdd)
            tjd__pjyf = ldxc__xqco + 7 >> 3
            cho__oqqtx = np.empty(tjd__pjyf, np.uint8)
            qkkt__nnjfq = np.empty(ldxc__xqco, np.uint32)
            c_scatterv(ucy__bkj.ctypes, send_counts.ctypes, baep__fsgnv.
                ctypes, qkkt__nnjfq.ctypes, np.int32(ldxc__xqco), ylh__mhw)
            convert_len_arr_to_offset(qkkt__nnjfq.ctypes, esh__mnk.ctypes,
                ldxc__xqco)
            cfu__dhsj = get_scatter_null_bytes_buff(bkj__hxslc.ctypes,
                send_counts, fnhb__rchm)
            c_scatterv(cfu__dhsj.ctypes, fnhb__rchm.ctypes, cga__mwfx.
                ctypes, cho__oqqtx.ctypes, np.int32(tjd__pjyf), talnx__onhi)
            return bodo.libs.array_item_arr_ext.init_array_item_array(
                ldxc__xqco, zpx__fjlx, esh__mnk, cho__oqqtx)
        return scatterv_array_item_impl
    if isinstance(data, (IntegerArrayType, DecimalArrayType)) or data in (
        boolean_array, datetime_date_array_type):
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))
        if isinstance(data, IntegerArrayType):
            llr__conik = bodo.libs.int_arr_ext.init_integer_array
        if isinstance(data, DecimalArrayType):
            precision = data.precision
            scale = data.scale
            llr__conik = numba.njit(no_cpython_wrapper=True)(lambda d, b:
                bodo.libs.decimal_arr_ext.init_decimal_array(d, b,
                precision, scale))
        if data == boolean_array:
            llr__conik = bodo.libs.bool_arr_ext.init_bool_array
        if data == datetime_date_array_type:
            llr__conik = (bodo.hiframes.datetime_date_ext.
                init_datetime_date_array)

        def scatterv_impl_int_arr(data, send_counts=None, warn_if_dist=True):
            n_pes = bodo.libs.distributed_api.get_size()
            etbc__bpqvj = data._data
            zxbm__gmg = data._null_bitmap
            uxps__lzii = len(etbc__bpqvj)
            pihfl__grcqz = _scatterv_np(etbc__bpqvj, send_counts)
            pwf__ubp = bcast_scalar(uxps__lzii)
            wszl__sxu = len(pihfl__grcqz) + 7 >> 3
            appxl__vzup = np.empty(wszl__sxu, np.uint8)
            send_counts = _get_scatterv_send_counts(send_counts, n_pes,
                pwf__ubp)
            fnhb__rchm = np.empty(n_pes, np.int32)
            for i in range(n_pes):
                fnhb__rchm[i] = send_counts[i] + 7 >> 3
            cga__mwfx = bodo.ir.join.calc_disp(fnhb__rchm)
            cfu__dhsj = get_scatter_null_bytes_buff(zxbm__gmg.ctypes,
                send_counts, fnhb__rchm)
            c_scatterv(cfu__dhsj.ctypes, fnhb__rchm.ctypes, cga__mwfx.
                ctypes, appxl__vzup.ctypes, np.int32(wszl__sxu), talnx__onhi)
            return llr__conik(pihfl__grcqz, appxl__vzup)
        return scatterv_impl_int_arr
    if isinstance(data, IntervalArrayType):

        def impl_interval_arr(data, send_counts=None, warn_if_dist=True):
            vwqi__saw = bodo.libs.distributed_api.scatterv_impl(data._left,
                send_counts)
            dta__wtfi = bodo.libs.distributed_api.scatterv_impl(data._right,
                send_counts)
            return bodo.libs.interval_arr_ext.init_interval_array(vwqi__saw,
                dta__wtfi)
        return impl_interval_arr
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):

        def impl_range_index(data, send_counts=None, warn_if_dist=True):
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            start = data._start
            stop = data._stop
            wuio__mbz = data._step
            puol__buqni = data._name
            puol__buqni = bcast_scalar(puol__buqni)
            start = bcast_scalar(start)
            stop = bcast_scalar(stop)
            wuio__mbz = bcast_scalar(wuio__mbz)
            kwb__yfx = bodo.libs.array_kernels.calc_nitems(start, stop,
                wuio__mbz)
            chunk_start = bodo.libs.distributed_api.get_start(kwb__yfx,
                n_pes, rank)
            chunk_count = bodo.libs.distributed_api.get_node_portion(kwb__yfx,
                n_pes, rank)
            kpu__ynw = start + wuio__mbz * chunk_start
            dut__hxaa = start + wuio__mbz * (chunk_start + chunk_count)
            dut__hxaa = min(dut__hxaa, stop)
            return bodo.hiframes.pd_index_ext.init_range_index(kpu__ynw,
                dut__hxaa, wuio__mbz, puol__buqni)
        return impl_range_index
    if isinstance(data, bodo.hiframes.pd_index_ext.PeriodIndexType):
        pkcr__nppze = data.freq

        def impl_period_index(data, send_counts=None, warn_if_dist=True):
            etbc__bpqvj = data._data
            puol__buqni = data._name
            puol__buqni = bcast_scalar(puol__buqni)
            arr = bodo.libs.distributed_api.scatterv_impl(etbc__bpqvj,
                send_counts)
            return bodo.hiframes.pd_index_ext.init_period_index(arr,
                puol__buqni, pkcr__nppze)
        return impl_period_index
    if bodo.hiframes.pd_index_ext.is_pd_index_type(data):

        def impl_pd_index(data, send_counts=None, warn_if_dist=True):
            etbc__bpqvj = data._data
            puol__buqni = data._name
            puol__buqni = bcast_scalar(puol__buqni)
            arr = bodo.libs.distributed_api.scatterv_impl(etbc__bpqvj,
                send_counts)
            return bodo.utils.conversion.index_from_array(arr, puol__buqni)
        return impl_pd_index
    if isinstance(data, bodo.hiframes.pd_multi_index_ext.MultiIndexType):

        def impl_multi_index(data, send_counts=None, warn_if_dist=True):
            rzja__uce = bodo.libs.distributed_api.scatterv_impl(data._data,
                send_counts)
            puol__buqni = bcast_scalar(data._name)
            bjh__qmie = bcast_tuple(data._names)
            return bodo.hiframes.pd_multi_index_ext.init_multi_index(rzja__uce,
                bjh__qmie, puol__buqni)
        return impl_multi_index
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl_series(data, send_counts=None, warn_if_dist=True):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            puol__buqni = bodo.hiframes.pd_series_ext.get_series_name(data)
            gnadf__wzya = bcast_scalar(puol__buqni)
            out_arr = bodo.libs.distributed_api.scatterv_impl(arr, send_counts)
            stv__kptjl = bodo.libs.distributed_api.scatterv_impl(index,
                send_counts)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                stv__kptjl, gnadf__wzya)
        return impl_series
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        oze__vvo = len(data.columns)
        qtq__vzuo = ', '.join('g_data_{}'.format(i) for i in range(oze__vvo))
        dcjzg__axseo = bodo.utils.transform.gen_const_tup(data.columns)
        gejat__tmsyz = (
            'def impl_df(data, send_counts=None, warn_if_dist=True):\n')
        for i in range(oze__vvo):
            gejat__tmsyz += (
                """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                .format(i, i))
            gejat__tmsyz += (
                """  g_data_{} = bodo.libs.distributed_api.scatterv_impl(data_{}, send_counts)
"""
                .format(i, i))
        gejat__tmsyz += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        gejat__tmsyz += (
            '  g_index = bodo.libs.distributed_api.scatterv_impl(index, send_counts)\n'
            )
        gejat__tmsyz += (
            """  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})
"""
            .format(qtq__vzuo, dcjzg__axseo))
        gotlz__avr = {}
        exec(gejat__tmsyz, {'bodo': bodo}, gotlz__avr)
        dytyd__rpmu = gotlz__avr['impl_df']
        return dytyd__rpmu
    if isinstance(data, CategoricalArrayType):

        def impl_cat(data, send_counts=None, warn_if_dist=True):
            yqcht__qvt = bodo.libs.distributed_api.scatterv_impl(data.codes,
                send_counts)
            return bodo.hiframes.pd_categorical_ext.init_categorical_array(
                yqcht__qvt, data.dtype)
        return impl_cat
    if isinstance(data, types.BaseTuple):
        gejat__tmsyz = (
            'def impl_tuple(data, send_counts=None, warn_if_dist=True):\n')
        gejat__tmsyz += '  return ({}{})\n'.format(', '.join(
            'bodo.libs.distributed_api.scatterv_impl(data[{}], send_counts)'
            .format(i) for i in range(len(data))), ',' if len(data) > 0 else ''
            )
        gotlz__avr = {}
        exec(gejat__tmsyz, {'bodo': bodo}, gotlz__avr)
        exeph__ikyk = gotlz__avr['impl_tuple']
        return exeph__ikyk
    if data is types.none:
        return lambda data, send_counts=None, warn_if_dist=True: None
    raise BodoError('scatterv() not available for {}'.format(data))


@intrinsic
def cptr_to_voidptr(typingctx, cptr_tp=None):

    def codegen(context, builder, sig, args):
        return builder.bitcast(args[0], lir.IntType(8).as_pointer())
    return types.voidptr(cptr_tp), codegen


def bcast(data, root=MPI_ROOT):
    return


@overload(bcast, no_unliteral=True)
def bcast_overload(data, root=MPI_ROOT):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
        'bodo.bcast()')
    if isinstance(data, types.Array):

        def bcast_impl(data, root=MPI_ROOT):
            typ_enum = get_type_enum(data)
            count = data.size
            assert count < INT_MAX
            c_bcast(data.ctypes, np.int32(count), typ_enum, np.array([-1]).
                ctypes, 0, np.int32(root))
            return
        return bcast_impl
    if isinstance(data, DecimalArrayType):

        def bcast_decimal_arr(data, root=MPI_ROOT):
            count = data._data.size
            assert count < INT_MAX
            c_bcast(data._data.ctypes, np.int32(count), CTypeEnum.Int128.
                value, np.array([-1]).ctypes, 0, np.int32(root))
            bcast(data._null_bitmap, root)
            return
        return bcast_decimal_arr
    if isinstance(data, IntegerArrayType) or data in (boolean_array,
        datetime_date_array_type):

        def bcast_impl_int_arr(data, root=MPI_ROOT):
            bcast(data._data, root)
            bcast(data._null_bitmap, root)
            return
        return bcast_impl_int_arr
    if is_str_arr_type(data) or data == binary_array_type:
        pyfo__ehmrd = np.int32(numba_to_c_type(offset_type))
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))

        def bcast_str_impl(data, root=MPI_ROOT):
            data = decode_if_dict_array(data)
            ldxc__xqco = len(data)
            uym__xfop = num_total_chars(data)
            assert ldxc__xqco < INT_MAX
            assert uym__xfop < INT_MAX
            ibijf__hev = get_offset_ptr(data)
            onop__ylp = get_data_ptr(data)
            null_bitmap_ptr = get_null_bitmap_ptr(data)
            nbhoj__zdfhm = ldxc__xqco + 7 >> 3
            c_bcast(ibijf__hev, np.int32(ldxc__xqco + 1), pyfo__ehmrd, np.
                array([-1]).ctypes, 0, np.int32(root))
            c_bcast(onop__ylp, np.int32(uym__xfop), talnx__onhi, np.array([
                -1]).ctypes, 0, np.int32(root))
            c_bcast(null_bitmap_ptr, np.int32(nbhoj__zdfhm), talnx__onhi,
                np.array([-1]).ctypes, 0, np.int32(root))
        return bcast_str_impl


c_bcast = types.ExternalFunction('c_bcast', types.void(types.voidptr, types
    .int32, types.int32, types.voidptr, types.int32, types.int32))


@numba.generated_jit(nopython=True)
def bcast_scalar(val, root=MPI_ROOT):
    val = types.unliteral(val)
    if not (isinstance(val, (types.Integer, types.Float)) or val in [bodo.
        datetime64ns, bodo.timedelta64ns, bodo.string_type, types.none,
        types.bool_]):
        raise BodoError(
            f'bcast_scalar requires an argument of type Integer, Float, datetime64ns, timedelta64ns, string, None, or Bool. Found type {val}'
            )
    if val == types.none:
        return lambda val, root=MPI_ROOT: None
    if val == bodo.string_type:
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))

        def impl_str(val, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            if rank != root:
                cnwjj__dikzj = 0
                stbvo__bdpes = np.empty(0, np.uint8).ctypes
            else:
                stbvo__bdpes, cnwjj__dikzj = (bodo.libs.str_ext.
                    unicode_to_utf8_and_len(val))
            cnwjj__dikzj = bodo.libs.distributed_api.bcast_scalar(cnwjj__dikzj,
                root)
            if rank != root:
                evyxv__lhj = np.empty(cnwjj__dikzj + 1, np.uint8)
                evyxv__lhj[cnwjj__dikzj] = 0
                stbvo__bdpes = evyxv__lhj.ctypes
            c_bcast(stbvo__bdpes, np.int32(cnwjj__dikzj), talnx__onhi, np.
                array([-1]).ctypes, 0, np.int32(root))
            return bodo.libs.str_arr_ext.decode_utf8(stbvo__bdpes, cnwjj__dikzj
                )
        return impl_str
    typ_val = numba_to_c_type(val)
    gejat__tmsyz = f"""def bcast_scalar_impl(val, root={MPI_ROOT}):
  send = np.empty(1, dtype)
  send[0] = val
  c_bcast(send.ctypes, np.int32(1), np.int32({typ_val}), np.array([-1]).ctypes, 0, np.int32(root))
  return send[0]
"""
    dtype = numba.np.numpy_support.as_dtype(val)
    gotlz__avr = {}
    exec(gejat__tmsyz, {'bodo': bodo, 'np': np, 'c_bcast': c_bcast, 'dtype':
        dtype}, gotlz__avr)
    jaq__dezr = gotlz__avr['bcast_scalar_impl']
    return jaq__dezr


@numba.generated_jit(nopython=True)
def bcast_tuple(val, root=MPI_ROOT):
    assert isinstance(val, types.BaseTuple)
    beaj__ezixp = len(val)
    gejat__tmsyz = f'def bcast_tuple_impl(val, root={MPI_ROOT}):\n'
    gejat__tmsyz += '  return ({}{})'.format(','.join(
        'bcast_scalar(val[{}], root)'.format(i) for i in range(beaj__ezixp)
        ), ',' if beaj__ezixp else '')
    gotlz__avr = {}
    exec(gejat__tmsyz, {'bcast_scalar': bcast_scalar}, gotlz__avr)
    wpy__lsmk = gotlz__avr['bcast_tuple_impl']
    return wpy__lsmk


def prealloc_str_for_bcast(arr, root=MPI_ROOT):
    return arr


@overload(prealloc_str_for_bcast, no_unliteral=True)
def prealloc_str_for_bcast_overload(arr, root=MPI_ROOT):
    if arr == string_array_type:

        def prealloc_impl(arr, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            ldxc__xqco = bcast_scalar(len(arr), root)
            delm__eopct = bcast_scalar(np.int64(num_total_chars(arr)), root)
            if rank != root:
                arr = pre_alloc_string_array(ldxc__xqco, delm__eopct)
            return arr
        return prealloc_impl
    return lambda arr, root=MPI_ROOT: arr


def get_local_slice(idx, arr_start, total_len):
    return idx


@overload(get_local_slice, no_unliteral=True, jit_options={'cache': True,
    'no_cpython_wrapper': True})
def get_local_slice_overload(idx, arr_start, total_len):

    def impl(idx, arr_start, total_len):
        slice_index = numba.cpython.unicode._normalize_slice(idx, total_len)
        start = slice_index.start
        wuio__mbz = slice_index.step
        hted__ddxcf = 0 if wuio__mbz == 1 or start > arr_start else abs(
            wuio__mbz - arr_start % wuio__mbz) % wuio__mbz
        kpu__ynw = max(arr_start, slice_index.start) - arr_start + hted__ddxcf
        dut__hxaa = max(slice_index.stop - arr_start, 0)
        return slice(kpu__ynw, dut__hxaa, wuio__mbz)
    return impl


def slice_getitem(arr, slice_index, arr_start, total_len):
    return arr[slice_index]


@overload(slice_getitem, no_unliteral=True, jit_options={'cache': True})
def slice_getitem_overload(arr, slice_index, arr_start, total_len):

    def getitem_impl(arr, slice_index, arr_start, total_len):
        cvrwu__cspyn = get_local_slice(slice_index, arr_start, total_len)
        return bodo.utils.conversion.ensure_contig_if_np(arr[cvrwu__cspyn])
    return getitem_impl


dummy_use = numba.njit(lambda a: None)


def int_getitem(arr, ind, arr_start, total_len, is_1D):
    return arr[ind]


def transform_str_getitem_output(data, length):
    pass


@overload(transform_str_getitem_output)
def overload_transform_str_getitem_output(data, length):
    if data == bodo.string_type:
        return lambda data, length: bodo.libs.str_arr_ext.decode_utf8(data.
            _data, length)
    if data == types.Array(types.uint8, 1, 'C'):
        return lambda data, length: bodo.libs.binary_arr_ext.init_bytes_type(
            data, length)
    raise BodoError(
        f'Internal Error: Expected String or Uint8 Array, found {data}')


@overload(int_getitem, no_unliteral=True)
def int_getitem_overload(arr, ind, arr_start, total_len, is_1D):
    if is_str_arr_type(arr) or arr == bodo.binary_array_type:
        eqk__ykcdi = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND
        talnx__onhi = np.int32(numba_to_c_type(types.uint8))
        qibrm__sgcxz = arr.dtype

        def str_getitem_impl(arr, ind, arr_start, total_len, is_1D):
            if ind >= total_len:
                raise IndexError('index out of bounds')
            arr = decode_if_dict_array(arr)
            ind = ind % total_len
            root = np.int32(0)
            faa__oraiz = np.int32(10)
            tag = np.int32(11)
            brzd__mwt = np.zeros(1, np.int64)
            if arr_start <= ind < arr_start + len(arr):
                ind = ind - arr_start
                elceq__fecl = arr._data
                pin__cxx = bodo.libs.array_item_arr_ext.get_offsets_ind(
                    elceq__fecl, ind)
                gve__lapln = bodo.libs.array_item_arr_ext.get_offsets_ind(
                    elceq__fecl, ind + 1)
                length = gve__lapln - pin__cxx
                mqj__xiwv = elceq__fecl[ind]
                brzd__mwt[0] = length
                isend(brzd__mwt, np.int32(1), root, faa__oraiz, True)
                isend(mqj__xiwv, np.int32(length), root, tag, True)
            rank = bodo.libs.distributed_api.get_rank()
            val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(
                qibrm__sgcxz, eqk__ykcdi, 0, 1)
            yedn__ofadp = 0
            if rank == root:
                yedn__ofadp = recv(np.int64, ANY_SOURCE, faa__oraiz)
                val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(
                    qibrm__sgcxz, eqk__ykcdi, yedn__ofadp, 1)
                onop__ylp = bodo.libs.str_ext.get_unicode_or_numpy_data(val)
                _recv(onop__ylp, np.int32(yedn__ofadp), talnx__onhi,
                    ANY_SOURCE, tag)
            dummy_use(brzd__mwt)
            yedn__ofadp = bcast_scalar(yedn__ofadp)
            dummy_use(arr)
            if rank != root:
                val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(
                    qibrm__sgcxz, eqk__ykcdi, yedn__ofadp, 1)
            onop__ylp = bodo.libs.str_ext.get_unicode_or_numpy_data(val)
            c_bcast(onop__ylp, np.int32(yedn__ofadp), talnx__onhi, np.array
                ([-1]).ctypes, 0, np.int32(root))
            val = transform_str_getitem_output(val, yedn__ofadp)
            return val
        return str_getitem_impl
    if isinstance(arr, bodo.CategoricalArrayType):
        txh__jyf = bodo.hiframes.pd_categorical_ext.get_categories_int_type(arr
            .dtype)

        def cat_getitem_impl(arr, ind, arr_start, total_len, is_1D):
            if ind >= total_len:
                raise IndexError('index out of bounds')
            ind = ind % total_len
            root = np.int32(0)
            tag = np.int32(11)
            send_arr = np.zeros(1, txh__jyf)
            if arr_start <= ind < arr_start + len(arr):
                yqcht__qvt = (bodo.hiframes.pd_categorical_ext.
                    get_categorical_arr_codes(arr))
                data = yqcht__qvt[ind - arr_start]
                send_arr = np.full(1, data, txh__jyf)
                isend(send_arr, np.int32(1), root, tag, True)
            rank = bodo.libs.distributed_api.get_rank()
            val = txh__jyf(-1)
            if rank == root:
                val = recv(txh__jyf, ANY_SOURCE, tag)
            dummy_use(send_arr)
            val = bcast_scalar(val)
            buixc__ussnx = arr.dtype.categories[max(val, 0)]
            return buixc__ussnx
        return cat_getitem_impl
    iowd__sazgp = arr.dtype

    def getitem_impl(arr, ind, arr_start, total_len, is_1D):
        if ind >= total_len:
            raise IndexError('index out of bounds')
        ind = ind % total_len
        root = np.int32(0)
        tag = np.int32(11)
        send_arr = np.zeros(1, iowd__sazgp)
        if arr_start <= ind < arr_start + len(arr):
            data = arr[ind - arr_start]
            send_arr = np.full(1, data)
            isend(send_arr, np.int32(1), root, tag, True)
        rank = bodo.libs.distributed_api.get_rank()
        val = np.zeros(1, iowd__sazgp)[0]
        if rank == root:
            val = recv(iowd__sazgp, ANY_SOURCE, tag)
        dummy_use(send_arr)
        val = bcast_scalar(val)
        return val
    return getitem_impl


c_alltoallv = types.ExternalFunction('c_alltoallv', types.void(types.
    voidptr, types.voidptr, types.voidptr, types.voidptr, types.voidptr,
    types.voidptr, types.int32))


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def alltoallv(send_data, out_data, send_counts, recv_counts, send_disp,
    recv_disp):
    typ_enum = get_type_enum(send_data)
    dog__laaex = get_type_enum(out_data)
    assert typ_enum == dog__laaex
    if isinstance(send_data, (IntegerArrayType, DecimalArrayType)
        ) or send_data in (boolean_array, datetime_date_array_type):
        return (lambda send_data, out_data, send_counts, recv_counts,
            send_disp, recv_disp: c_alltoallv(send_data._data.ctypes,
            out_data._data.ctypes, send_counts.ctypes, recv_counts.ctypes,
            send_disp.ctypes, recv_disp.ctypes, typ_enum))
    if isinstance(send_data, bodo.CategoricalArrayType):
        return (lambda send_data, out_data, send_counts, recv_counts,
            send_disp, recv_disp: c_alltoallv(send_data.codes.ctypes,
            out_data.codes.ctypes, send_counts.ctypes, recv_counts.ctypes,
            send_disp.ctypes, recv_disp.ctypes, typ_enum))
    return (lambda send_data, out_data, send_counts, recv_counts, send_disp,
        recv_disp: c_alltoallv(send_data.ctypes, out_data.ctypes,
        send_counts.ctypes, recv_counts.ctypes, send_disp.ctypes, recv_disp
        .ctypes, typ_enum))


def alltoallv_tup(send_data, out_data, send_counts, recv_counts, send_disp,
    recv_disp):
    return


@overload(alltoallv_tup, no_unliteral=True)
def alltoallv_tup_overload(send_data, out_data, send_counts, recv_counts,
    send_disp, recv_disp):
    count = send_data.count
    assert out_data.count == count
    gejat__tmsyz = (
        'def f(send_data, out_data, send_counts, recv_counts, send_disp, recv_disp):\n'
        )
    for i in range(count):
        gejat__tmsyz += (
            """  alltoallv(send_data[{}], out_data[{}], send_counts, recv_counts, send_disp, recv_disp)
"""
            .format(i, i))
    gejat__tmsyz += '  return\n'
    gotlz__avr = {}
    exec(gejat__tmsyz, {'alltoallv': alltoallv}, gotlz__avr)
    omr__yxjjh = gotlz__avr['f']
    return omr__yxjjh


@numba.njit
def get_start_count(n):
    rank = bodo.libs.distributed_api.get_rank()
    n_pes = bodo.libs.distributed_api.get_size()
    start = bodo.libs.distributed_api.get_start(n, n_pes, rank)
    count = bodo.libs.distributed_api.get_node_portion(n, n_pes, rank)
    return start, count


@numba.njit
def get_start(total_size, pes, rank):
    dtpoh__cckgt = total_size % pes
    ejmmw__ayl = (total_size - dtpoh__cckgt) // pes
    return rank * ejmmw__ayl + min(rank, dtpoh__cckgt)


@numba.njit
def get_end(total_size, pes, rank):
    dtpoh__cckgt = total_size % pes
    ejmmw__ayl = (total_size - dtpoh__cckgt) // pes
    return (rank + 1) * ejmmw__ayl + min(rank + 1, dtpoh__cckgt)


@numba.njit
def get_node_portion(total_size, pes, rank):
    dtpoh__cckgt = total_size % pes
    ejmmw__ayl = (total_size - dtpoh__cckgt) // pes
    if rank < dtpoh__cckgt:
        return ejmmw__ayl + 1
    else:
        return ejmmw__ayl


@numba.generated_jit(nopython=True)
def dist_cumsum(in_arr, out_arr):
    opert__vvqh = in_arr.dtype(0)
    lauza__mjua = np.int32(Reduce_Type.Sum.value)

    def cumsum_impl(in_arr, out_arr):
        bxwzv__ilhtk = opert__vvqh
        for avpew__tija in np.nditer(in_arr):
            bxwzv__ilhtk += avpew__tija.item()
        knrbr__rgi = dist_exscan(bxwzv__ilhtk, lauza__mjua)
        for i in range(in_arr.size):
            knrbr__rgi += in_arr[i]
            out_arr[i] = knrbr__rgi
        return 0
    return cumsum_impl


@numba.generated_jit(nopython=True)
def dist_cumprod(in_arr, out_arr):
    yhenh__lka = in_arr.dtype(1)
    lauza__mjua = np.int32(Reduce_Type.Prod.value)

    def cumprod_impl(in_arr, out_arr):
        bxwzv__ilhtk = yhenh__lka
        for avpew__tija in np.nditer(in_arr):
            bxwzv__ilhtk *= avpew__tija.item()
        knrbr__rgi = dist_exscan(bxwzv__ilhtk, lauza__mjua)
        if get_rank() == 0:
            knrbr__rgi = yhenh__lka
        for i in range(in_arr.size):
            knrbr__rgi *= in_arr[i]
            out_arr[i] = knrbr__rgi
        return 0
    return cumprod_impl


@numba.generated_jit(nopython=True)
def dist_cummin(in_arr, out_arr):
    if isinstance(in_arr.dtype, types.Float):
        yhenh__lka = np.finfo(in_arr.dtype(1).dtype).max
    else:
        yhenh__lka = np.iinfo(in_arr.dtype(1).dtype).max
    lauza__mjua = np.int32(Reduce_Type.Min.value)

    def cummin_impl(in_arr, out_arr):
        bxwzv__ilhtk = yhenh__lka
        for avpew__tija in np.nditer(in_arr):
            bxwzv__ilhtk = min(bxwzv__ilhtk, avpew__tija.item())
        knrbr__rgi = dist_exscan(bxwzv__ilhtk, lauza__mjua)
        if get_rank() == 0:
            knrbr__rgi = yhenh__lka
        for i in range(in_arr.size):
            knrbr__rgi = min(knrbr__rgi, in_arr[i])
            out_arr[i] = knrbr__rgi
        return 0
    return cummin_impl


@numba.generated_jit(nopython=True)
def dist_cummax(in_arr, out_arr):
    if isinstance(in_arr.dtype, types.Float):
        yhenh__lka = np.finfo(in_arr.dtype(1).dtype).min
    else:
        yhenh__lka = np.iinfo(in_arr.dtype(1).dtype).min
    yhenh__lka = in_arr.dtype(1)
    lauza__mjua = np.int32(Reduce_Type.Max.value)

    def cummax_impl(in_arr, out_arr):
        bxwzv__ilhtk = yhenh__lka
        for avpew__tija in np.nditer(in_arr):
            bxwzv__ilhtk = max(bxwzv__ilhtk, avpew__tija.item())
        knrbr__rgi = dist_exscan(bxwzv__ilhtk, lauza__mjua)
        if get_rank() == 0:
            knrbr__rgi = yhenh__lka
        for i in range(in_arr.size):
            knrbr__rgi = max(knrbr__rgi, in_arr[i])
            out_arr[i] = knrbr__rgi
        return 0
    return cummax_impl


_allgather = types.ExternalFunction('allgather', types.void(types.voidptr,
    types.int32, types.voidptr, types.int32))


@numba.njit
def allgather(arr, val):
    ioj__mdx = get_type_enum(arr)
    _allgather(arr.ctypes, 1, value_to_ptr(val), ioj__mdx)


def dist_return(A):
    return A


def rep_return(A):
    return A


def dist_return_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    wwn__jydb = args[0]
    if equiv_set.has_shape(wwn__jydb):
        return ArrayAnalysis.AnalyzeResult(shape=wwn__jydb, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_libs_distributed_api_dist_return = (
    dist_return_equiv)
ArrayAnalysis._analyze_op_call_bodo_libs_distributed_api_rep_return = (
    dist_return_equiv)


def threaded_return(A):
    return A


@numba.njit
def set_arr_local(arr, ind, val):
    arr[ind] = val


@numba.njit
def local_alloc_size(n, in_arr):
    return n


@infer_global(threaded_return)
@infer_global(dist_return)
@infer_global(rep_return)
class ThreadedRetTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 1
        return signature(args[0], *args)


@numba.njit
def parallel_print(*args):
    print(*args)


@numba.njit
def single_print(*args):
    if bodo.libs.distributed_api.get_rank() == 0:
        print(*args)


@numba.njit(no_cpython_wrapper=True)
def print_if_not_empty(arg):
    if len(arg) != 0 or bodo.get_rank() == 0:
        print(arg)


_wait = types.ExternalFunction('dist_wait', types.void(mpi_req_numba_type,
    types.bool_))


@numba.generated_jit(nopython=True)
def wait(req, cond=True):
    if isinstance(req, types.BaseTuple):
        count = len(req.types)
        wiy__qjqos = ','.join(f'_wait(req[{i}], cond)' for i in range(count))
        gejat__tmsyz = 'def f(req, cond=True):\n'
        gejat__tmsyz += f'  return {wiy__qjqos}\n'
        gotlz__avr = {}
        exec(gejat__tmsyz, {'_wait': _wait}, gotlz__avr)
        impl = gotlz__avr['f']
        return impl
    if is_overload_none(req):
        return lambda req, cond=True: None
    return lambda req, cond=True: _wait(req, cond)


class ReqArrayType(types.Type):

    def __init__(self):
        super(ReqArrayType, self).__init__(name='ReqArrayType()')


req_array_type = ReqArrayType()
register_model(ReqArrayType)(models.OpaqueModel)
waitall = types.ExternalFunction('dist_waitall', types.void(types.int32,
    req_array_type))
comm_req_alloc = types.ExternalFunction('comm_req_alloc', req_array_type(
    types.int32))
comm_req_dealloc = types.ExternalFunction('comm_req_dealloc', types.void(
    req_array_type))
req_array_setitem = types.ExternalFunction('req_array_setitem', types.void(
    req_array_type, types.int64, mpi_req_numba_type))


@overload(operator.setitem, no_unliteral=True)
def overload_req_arr_setitem(A, idx, val):
    if A == req_array_type:
        assert val == mpi_req_numba_type
        return lambda A, idx, val: req_array_setitem(A, idx, val)


@numba.njit
def _get_local_range(start, stop, chunk_start, chunk_count):
    assert start >= 0 and stop > 0
    kpu__ynw = max(start, chunk_start)
    dut__hxaa = min(stop, chunk_start + chunk_count)
    zagqr__rnc = kpu__ynw - chunk_start
    dqf__zvbk = dut__hxaa - chunk_start
    if zagqr__rnc < 0 or dqf__zvbk < 0:
        zagqr__rnc = 1
        dqf__zvbk = 0
    return zagqr__rnc, dqf__zvbk


@register_jitable
def _set_if_in_range(A, val, index, chunk_start):
    if index >= chunk_start and index < chunk_start + len(A):
        A[index - chunk_start] = val


@register_jitable
def _root_rank_select(old_val, new_val):
    if get_rank() == 0:
        return old_val
    return new_val


def get_tuple_prod(t):
    return np.prod(t)


@overload(get_tuple_prod, no_unliteral=True)
def get_tuple_prod_overload(t):
    if t == numba.core.types.containers.Tuple(()):
        return lambda t: 1

    def get_tuple_prod_impl(t):
        dtpoh__cckgt = 1
        for a in t:
            dtpoh__cckgt *= a
        return dtpoh__cckgt
    return get_tuple_prod_impl


sig = types.void(types.voidptr, types.voidptr, types.intp, types.intp,
    types.intp, types.intp, types.int32, types.voidptr)
oneD_reshape_shuffle = types.ExternalFunction('oneD_reshape_shuffle', sig)


@numba.njit(no_cpython_wrapper=True, cache=True)
def dist_oneD_reshape_shuffle(lhs, in_arr, new_dim0_global_len, dest_ranks=None
    ):
    cmf__auax = np.ascontiguousarray(in_arr)
    pshw__haf = get_tuple_prod(cmf__auax.shape[1:])
    ssf__ogs = get_tuple_prod(lhs.shape[1:])
    if dest_ranks is not None:
        jzxgc__bhmbg = np.array(dest_ranks, dtype=np.int32)
    else:
        jzxgc__bhmbg = np.empty(0, dtype=np.int32)
    dtype_size = bodo.io.np_io.get_dtype_size(in_arr.dtype)
    oneD_reshape_shuffle(lhs.ctypes, cmf__auax.ctypes, new_dim0_global_len,
        len(in_arr), dtype_size * ssf__ogs, dtype_size * pshw__haf, len(
        jzxgc__bhmbg), jzxgc__bhmbg.ctypes)
    check_and_propagate_cpp_exception()


permutation_int = types.ExternalFunction('permutation_int', types.void(
    types.voidptr, types.intp))


@numba.njit
def dist_permutation_int(lhs, n):
    permutation_int(lhs.ctypes, n)


permutation_array_index = types.ExternalFunction('permutation_array_index',
    types.void(types.voidptr, types.intp, types.intp, types.voidptr, types.
    int64, types.voidptr, types.intp))


@numba.njit
def dist_permutation_array_index(lhs, lhs_len, dtype_size, rhs, p, p_len):
    vwpiy__gmj = np.ascontiguousarray(rhs)
    njpij__yeg = get_tuple_prod(vwpiy__gmj.shape[1:])
    ctat__oad = dtype_size * njpij__yeg
    permutation_array_index(lhs.ctypes, lhs_len, ctat__oad, vwpiy__gmj.
        ctypes, vwpiy__gmj.shape[0], p.ctypes, p_len)
    check_and_propagate_cpp_exception()


from bodo.io import fsspec_reader, hdfs_reader, s3_reader
ll.add_symbol('finalize', hdist.finalize)
finalize = types.ExternalFunction('finalize', types.int32())
ll.add_symbol('finalize_s3', s3_reader.finalize_s3)
finalize_s3 = types.ExternalFunction('finalize_s3', types.int32())
ll.add_symbol('finalize_fsspec', fsspec_reader.finalize_fsspec)
finalize_fsspec = types.ExternalFunction('finalize_fsspec', types.int32())
ll.add_symbol('disconnect_hdfs', hdfs_reader.disconnect_hdfs)
disconnect_hdfs = types.ExternalFunction('disconnect_hdfs', types.int32())


def _check_for_cpp_errors():
    pass


@overload(_check_for_cpp_errors)
def overload_check_for_cpp_errors():
    return lambda : check_and_propagate_cpp_exception()


@numba.njit
def call_finalize():
    finalize()
    finalize_s3()
    finalize_fsspec()
    _check_for_cpp_errors()
    disconnect_hdfs()


def flush_stdout():
    if not sys.stdout.closed:
        sys.stdout.flush()


atexit.register(call_finalize)
atexit.register(flush_stdout)


def bcast_comm(data, comm_ranks, nranks, root=MPI_ROOT):
    rank = bodo.libs.distributed_api.get_rank()
    dtype = bodo.typeof(data)
    dtype = _bcast_dtype(dtype, root)
    if rank != MPI_ROOT:
        data = get_value_for_type(dtype)
    return bcast_comm_impl(data, comm_ranks, nranks, root)


@overload(bcast_comm)
def bcast_comm_overload(data, comm_ranks, nranks, root=MPI_ROOT):
    return lambda data, comm_ranks, nranks, root=MPI_ROOT: bcast_comm_impl(data
        , comm_ranks, nranks, root)


@numba.generated_jit(nopython=True)
def bcast_comm_impl(data, comm_ranks, nranks, root=MPI_ROOT):
    bodo.hiframes.pd_dataframe_ext.check_runtime_cols_unsupported(data,
        'bodo.bcast_comm()')
    if isinstance(data, (types.Integer, types.Float)):
        typ_val = numba_to_c_type(data)
        gejat__tmsyz = (
            f"""def bcast_scalar_impl(data, comm_ranks, nranks, root={MPI_ROOT}):
  send = np.empty(1, dtype)
  send[0] = data
  c_bcast(send.ctypes, np.int32(1), np.int32({{}}), comm_ranks,ctypes, np.int32({{}}), np.int32(root))
  return send[0]
"""
            .format(typ_val, nranks))
        dtype = numba.np.numpy_support.as_dtype(data)
        gotlz__avr = {}
        exec(gejat__tmsyz, {'bodo': bodo, 'np': np, 'c_bcast': c_bcast,
            'dtype': dtype}, gotlz__avr)
        jaq__dezr = gotlz__avr['bcast_scalar_impl']
        return jaq__dezr
    if isinstance(data, types.Array):
        return lambda data, comm_ranks, nranks, root=MPI_ROOT: _bcast_np(data,
            comm_ranks, nranks, root)
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        oze__vvo = len(data.columns)
        qtq__vzuo = ', '.join('g_data_{}'.format(i) for i in range(oze__vvo))
        dcjzg__axseo = bodo.utils.transform.gen_const_tup(data.columns)
        gejat__tmsyz = (
            f'def impl_df(data, comm_ranks, nranks, root={MPI_ROOT}):\n')
        for i in range(oze__vvo):
            gejat__tmsyz += (
                """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                .format(i, i))
            gejat__tmsyz += (
                """  g_data_{} = bodo.libs.distributed_api.bcast_comm_impl(data_{}, comm_ranks, nranks, root)
"""
                .format(i, i))
        gejat__tmsyz += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        gejat__tmsyz += """  g_index = bodo.libs.distributed_api.bcast_comm_impl(index, comm_ranks, nranks, root)
"""
        gejat__tmsyz += (
            """  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})
"""
            .format(qtq__vzuo, dcjzg__axseo))
        gotlz__avr = {}
        exec(gejat__tmsyz, {'bodo': bodo}, gotlz__avr)
        dytyd__rpmu = gotlz__avr['impl_df']
        return dytyd__rpmu
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):

        def impl_range_index(data, comm_ranks, nranks, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            start = data._start
            stop = data._stop
            wuio__mbz = data._step
            puol__buqni = data._name
            puol__buqni = bcast_scalar(puol__buqni, root)
            start = bcast_scalar(start, root)
            stop = bcast_scalar(stop, root)
            wuio__mbz = bcast_scalar(wuio__mbz, root)
            kwb__yfx = bodo.libs.array_kernels.calc_nitems(start, stop,
                wuio__mbz)
            chunk_start = bodo.libs.distributed_api.get_start(kwb__yfx,
                n_pes, rank)
            chunk_count = bodo.libs.distributed_api.get_node_portion(kwb__yfx,
                n_pes, rank)
            kpu__ynw = start + wuio__mbz * chunk_start
            dut__hxaa = start + wuio__mbz * (chunk_start + chunk_count)
            dut__hxaa = min(dut__hxaa, stop)
            return bodo.hiframes.pd_index_ext.init_range_index(kpu__ynw,
                dut__hxaa, wuio__mbz, puol__buqni)
        return impl_range_index
    if bodo.hiframes.pd_index_ext.is_pd_index_type(data):

        def impl_pd_index(data, comm_ranks, nranks, root=MPI_ROOT):
            etbc__bpqvj = data._data
            puol__buqni = data._name
            arr = bodo.libs.distributed_api.bcast_comm_impl(etbc__bpqvj,
                comm_ranks, nranks, root)
            return bodo.utils.conversion.index_from_array(arr, puol__buqni)
        return impl_pd_index
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl_series(data, comm_ranks, nranks, root=MPI_ROOT):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            puol__buqni = bodo.hiframes.pd_series_ext.get_series_name(data)
            gnadf__wzya = bodo.libs.distributed_api.bcast_comm_impl(puol__buqni
                , comm_ranks, nranks, root)
            out_arr = bodo.libs.distributed_api.bcast_comm_impl(arr,
                comm_ranks, nranks, root)
            stv__kptjl = bodo.libs.distributed_api.bcast_comm_impl(index,
                comm_ranks, nranks, root)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                stv__kptjl, gnadf__wzya)
        return impl_series
    if isinstance(data, types.BaseTuple):
        gejat__tmsyz = (
            f'def impl_tuple(data, comm_ranks, nranks, root={MPI_ROOT}):\n')
        gejat__tmsyz += '  return ({}{})\n'.format(', '.join(
            'bcast_comm_impl(data[{}], comm_ranks, nranks, root)'.format(i) for
            i in range(len(data))), ',' if len(data) > 0 else '')
        gotlz__avr = {}
        exec(gejat__tmsyz, {'bcast_comm_impl': bcast_comm_impl}, gotlz__avr)
        exeph__ikyk = gotlz__avr['impl_tuple']
        return exeph__ikyk
    if data is types.none:
        return lambda data, comm_ranks, nranks, root=MPI_ROOT: None


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _bcast_np(data, comm_ranks, nranks, root=MPI_ROOT):
    typ_val = numba_to_c_type(data.dtype)
    wyulp__gmjv = data.ndim
    dtype = data.dtype
    if dtype == types.NPDatetime('ns'):
        dtype = np.dtype('datetime64[ns]')
    elif dtype == types.NPTimedelta('ns'):
        dtype = np.dtype('timedelta64[ns]')
    xpkh__nqo = (0,) * wyulp__gmjv

    def bcast_arr_impl(data, comm_ranks, nranks, root=MPI_ROOT):
        rank = bodo.libs.distributed_api.get_rank()
        etbc__bpqvj = np.ascontiguousarray(data)
        onop__ylp = data.ctypes
        kpqw__ohwwm = xpkh__nqo
        if rank == root:
            kpqw__ohwwm = etbc__bpqvj.shape
        kpqw__ohwwm = bcast_tuple(kpqw__ohwwm, root)
        lwbzz__hid = get_tuple_prod(kpqw__ohwwm[1:])
        send_counts = kpqw__ohwwm[0] * lwbzz__hid
        ebfp__vdwlm = np.empty(send_counts, dtype)
        if rank == MPI_ROOT:
            c_bcast(onop__ylp, np.int32(send_counts), np.int32(typ_val),
                comm_ranks.ctypes, np.int32(nranks), np.int32(root))
            return data
        else:
            c_bcast(ebfp__vdwlm.ctypes, np.int32(send_counts), np.int32(
                typ_val), comm_ranks.ctypes, np.int32(nranks), np.int32(root))
            return ebfp__vdwlm.reshape((-1,) + kpqw__ohwwm[1:])
    return bcast_arr_impl


node_ranks = None


def get_host_ranks():
    global node_ranks
    if node_ranks is None:
        skhl__pgc = MPI.COMM_WORLD
        agcy__mxq = MPI.Get_processor_name()
        dgae__bvdou = skhl__pgc.allgather(agcy__mxq)
        node_ranks = defaultdict(list)
        for i, frda__euya in enumerate(dgae__bvdou):
            node_ranks[frda__euya].append(i)
    return node_ranks


def create_subcomm_mpi4py(comm_ranks):
    skhl__pgc = MPI.COMM_WORLD
    pjli__cupyx = skhl__pgc.Get_group()
    vaq__ivps = pjli__cupyx.Incl(comm_ranks)
    yklco__dpzw = skhl__pgc.Create_group(vaq__ivps)
    return yklco__dpzw


def get_nodes_first_ranks():
    wde__sqflq = get_host_ranks()
    return np.array([zad__edlle[0] for zad__edlle in wde__sqflq.values()],
        dtype='int32')


def get_num_nodes():
    return len(get_host_ranks())
