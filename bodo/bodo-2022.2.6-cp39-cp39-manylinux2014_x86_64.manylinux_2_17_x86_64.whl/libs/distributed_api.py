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
    gqfn__yag = get_type_enum(send_arr)
    _send(send_arr.ctypes, 1, gqfn__yag, rank, tag)


_recv = types.ExternalFunction('c_recv', types.void(types.voidptr, types.
    int32, types.int32, types.int32, types.int32))


@numba.njit
def recv(dtype, rank, tag):
    recv_arr = np.empty(1, dtype)
    gqfn__yag = get_type_enum(recv_arr)
    _recv(recv_arr.ctypes, 1, gqfn__yag, rank, tag)
    return recv_arr[0]


_isend = types.ExternalFunction('dist_isend', mpi_req_numba_type(types.
    voidptr, types.int32, types.int32, types.int32, types.int32, types.bool_))


@numba.generated_jit(nopython=True)
def isend(arr, size, pe, tag, cond=True):
    if isinstance(arr, types.Array):

        def impl(arr, size, pe, tag, cond=True):
            gqfn__yag = get_type_enum(arr)
            return _isend(arr.ctypes, size, gqfn__yag, pe, tag, cond)
        return impl
    if isinstance(arr, (IntegerArrayType, DecimalArrayType)) or arr in (
        boolean_array, datetime_date_array_type):
        gqfn__yag = np.int32(numba_to_c_type(arr.dtype))
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))

        def impl_nullable(arr, size, pe, tag, cond=True):
            lhpt__orl = size + 7 >> 3
            mpd__kylh = _isend(arr._data.ctypes, size, gqfn__yag, pe, tag, cond
                )
            yoyu__liio = _isend(arr._null_bitmap.ctypes, lhpt__orl,
                ypndc__vfeo, pe, tag, cond)
            return mpd__kylh, yoyu__liio
        return impl_nullable
    if is_str_arr_type(arr) or arr == binary_array_type:
        chagv__gld = np.int32(numba_to_c_type(offset_type))
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))

        def impl_str_arr(arr, size, pe, tag, cond=True):
            arr = decode_if_dict_array(arr)
            ausq__yve = np.int64(bodo.libs.str_arr_ext.num_total_chars(arr))
            send(ausq__yve, pe, tag - 1)
            lhpt__orl = size + 7 >> 3
            _send(bodo.libs.str_arr_ext.get_offset_ptr(arr), size + 1,
                chagv__gld, pe, tag)
            _send(bodo.libs.str_arr_ext.get_data_ptr(arr), ausq__yve,
                ypndc__vfeo, pe, tag)
            _send(bodo.libs.str_arr_ext.get_null_bitmap_ptr(arr), lhpt__orl,
                ypndc__vfeo, pe, tag)
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
            gqfn__yag = get_type_enum(arr)
            return _irecv(arr.ctypes, size, gqfn__yag, pe, tag, cond)
        return impl
    if isinstance(arr, (IntegerArrayType, DecimalArrayType)) or arr in (
        boolean_array, datetime_date_array_type):
        gqfn__yag = np.int32(numba_to_c_type(arr.dtype))
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))

        def impl_nullable(arr, size, pe, tag, cond=True):
            lhpt__orl = size + 7 >> 3
            mpd__kylh = _irecv(arr._data.ctypes, size, gqfn__yag, pe, tag, cond
                )
            yoyu__liio = _irecv(arr._null_bitmap.ctypes, lhpt__orl,
                ypndc__vfeo, pe, tag, cond)
            return mpd__kylh, yoyu__liio
        return impl_nullable
    if arr in [binary_array_type, string_array_type]:
        chagv__gld = np.int32(numba_to_c_type(offset_type))
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))
        if arr == binary_array_type:
            kchw__ofua = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
        else:
            kchw__ofua = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
        dxfra__rogyq = f"""def impl(arr, size, pe, tag, cond=True):
            # recv the number of string characters and resize buffer to proper size
            n_chars = bodo.libs.distributed_api.recv(np.int64, pe, tag - 1)
            new_arr = {kchw__ofua}(size, n_chars)
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
        seu__wwq = dict()
        exec(dxfra__rogyq, {'bodo': bodo, 'np': np, 'offset_typ_enum':
            chagv__gld, 'char_typ_enum': ypndc__vfeo}, seu__wwq)
        impl = seu__wwq['impl']
        return impl
    raise BodoError(f'irecv(): array type {arr} not supported yet')


_alltoall = types.ExternalFunction('c_alltoall', types.void(types.voidptr,
    types.voidptr, types.int32, types.int32))


@numba.njit
def alltoall(send_arr, recv_arr, count):
    assert count < INT_MAX
    gqfn__yag = get_type_enum(send_arr)
    _alltoall(send_arr.ctypes, recv_arr.ctypes, np.int32(count), gqfn__yag)


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
        bved__mivu = n_pes if rank == root or allgather else 0
        brxsb__vtceq = np.empty(bved__mivu, dtype)
        c_gather_scalar(send.ctypes, brxsb__vtceq.ctypes, np.int32(typ_val),
            allgather, np.int32(root))
        return brxsb__vtceq
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
        bkn__dns = cgutils.alloca_once(builder, args[0].type)
        builder.store(args[0], bkn__dns)
        return builder.bitcast(bkn__dns, lir.IntType(8).as_pointer())
    return types.voidptr(val_tp), codegen


@intrinsic
def load_val_ptr(typingctx, ptr_tp, val_tp=None):

    def codegen(context, builder, sig, args):
        bkn__dns = builder.bitcast(args[0], args[1].type.as_pointer())
        return builder.load(bkn__dns)
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
    zao__olhv = types.unliteral(value)
    if isinstance(zao__olhv, IndexValueType):
        zao__olhv = zao__olhv.val_typ
        vkzp__veiwk = [types.bool_, types.uint8, types.int8, types.uint16,
            types.int16, types.uint32, types.int32, types.float32, types.
            float64]
        if not sys.platform.startswith('win'):
            vkzp__veiwk.append(types.int64)
            vkzp__veiwk.append(bodo.datetime64ns)
            vkzp__veiwk.append(bodo.timedelta64ns)
            vkzp__veiwk.append(bodo.datetime_date_type)
        if zao__olhv not in vkzp__veiwk:
            raise BodoError('argmin/argmax not supported for type {}'.
                format(zao__olhv))
    typ_enum = np.int32(numba_to_c_type(zao__olhv))

    def impl(value, reduce_op):
        cldf__lam = value_to_ptr(value)
        uws__jgzgj = value_to_ptr(value)
        _dist_reduce(cldf__lam, uws__jgzgj, reduce_op, typ_enum)
        return load_val_ptr(uws__jgzgj, value)
    return impl


_dist_exscan = types.ExternalFunction('dist_exscan', types.void(types.
    voidptr, types.voidptr, types.int32, types.int32))


@numba.generated_jit(nopython=True)
def dist_exscan(value, reduce_op):
    zao__olhv = types.unliteral(value)
    typ_enum = np.int32(numba_to_c_type(zao__olhv))
    lgnx__xstrg = zao__olhv(0)

    def impl(value, reduce_op):
        cldf__lam = value_to_ptr(value)
        uws__jgzgj = value_to_ptr(lgnx__xstrg)
        _dist_exscan(cldf__lam, uws__jgzgj, reduce_op, typ_enum)
        return load_val_ptr(uws__jgzgj, value)
    return impl


@numba.njit
def get_bit(bits, i):
    return bits[i >> 3] >> (i & 7) & 1


@numba.njit
def copy_gathered_null_bytes(null_bitmap_ptr, tmp_null_bytes,
    recv_counts_nulls, recv_counts):
    otyyu__mcjrn = 0
    wgjcw__mihy = 0
    for i in range(len(recv_counts)):
        enufg__llsxd = recv_counts[i]
        lhpt__orl = recv_counts_nulls[i]
        dyr__yoxio = tmp_null_bytes[otyyu__mcjrn:otyyu__mcjrn + lhpt__orl]
        for ompgx__zrcl in range(enufg__llsxd):
            set_bit_to(null_bitmap_ptr, wgjcw__mihy, get_bit(dyr__yoxio,
                ompgx__zrcl))
            wgjcw__mihy += 1
        otyyu__mcjrn += lhpt__orl


@numba.generated_jit(nopython=True)
def gatherv(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
    from bodo.libs.csr_matrix_ext import CSRMatrixType
    bodo.hiframes.pd_dataframe_ext.check_runtime_cols_unsupported(data,
        'bodo.gatherv()')
    if isinstance(data, CategoricalArrayType):

        def impl_cat(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
            ghiq__ajasf = bodo.gatherv(data.codes, allgather, root=root)
            return bodo.hiframes.pd_categorical_ext.init_categorical_array(
                ghiq__ajasf, data.dtype)
        return impl_cat
    if isinstance(data, types.Array):
        typ_val = numba_to_c_type(data.dtype)

        def gatherv_impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            data = np.ascontiguousarray(data)
            rank = bodo.libs.distributed_api.get_rank()
            obp__pijwm = data.size
            recv_counts = gather_scalar(np.int32(obp__pijwm), allgather,
                root=root)
            owq__dvn = recv_counts.sum()
            ctwsu__avafj = empty_like_type(owq__dvn, data)
            ryvvd__bvzpy = np.empty(1, np.int32)
            if rank == root or allgather:
                ryvvd__bvzpy = bodo.ir.join.calc_disp(recv_counts)
            c_gatherv(data.ctypes, np.int32(obp__pijwm), ctwsu__avafj.
                ctypes, recv_counts.ctypes, ryvvd__bvzpy.ctypes, np.int32(
                typ_val), allgather, np.int32(root))
            return ctwsu__avafj.reshape((-1,) + data.shape[1:])
        return gatherv_impl
    if is_str_arr_type(data):

        def gatherv_str_arr_impl(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            data = decode_if_dict_array(data)
            ctwsu__avafj = bodo.gatherv(data._data, allgather, warn_if_rep,
                root)
            return bodo.libs.str_arr_ext.init_str_arr(ctwsu__avafj)
        return gatherv_str_arr_impl
    if data == binary_array_type:

        def gatherv_binary_arr_impl(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            ctwsu__avafj = bodo.gatherv(data._data, allgather, warn_if_rep,
                root)
            return bodo.libs.binary_arr_ext.init_binary_arr(ctwsu__avafj)
        return gatherv_binary_arr_impl
    if data == datetime_timedelta_array_type:
        typ_val = numba_to_c_type(types.int64)
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))

        def gatherv_impl_int_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            obp__pijwm = len(data)
            lhpt__orl = obp__pijwm + 7 >> 3
            recv_counts = gather_scalar(np.int32(obp__pijwm), allgather,
                root=root)
            owq__dvn = recv_counts.sum()
            ctwsu__avafj = empty_like_type(owq__dvn, data)
            ryvvd__bvzpy = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            obbj__qybp = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                ryvvd__bvzpy = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                obbj__qybp = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(data._days_data.ctypes, np.int32(obp__pijwm),
                ctwsu__avafj._days_data.ctypes, recv_counts.ctypes,
                ryvvd__bvzpy.ctypes, np.int32(typ_val), allgather, np.int32
                (root))
            c_gatherv(data._seconds_data.ctypes, np.int32(obp__pijwm),
                ctwsu__avafj._seconds_data.ctypes, recv_counts.ctypes,
                ryvvd__bvzpy.ctypes, np.int32(typ_val), allgather, np.int32
                (root))
            c_gatherv(data._microseconds_data.ctypes, np.int32(obp__pijwm),
                ctwsu__avafj._microseconds_data.ctypes, recv_counts.ctypes,
                ryvvd__bvzpy.ctypes, np.int32(typ_val), allgather, np.int32
                (root))
            c_gatherv(data._null_bitmap.ctypes, np.int32(lhpt__orl),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, obbj__qybp
                .ctypes, ypndc__vfeo, allgather, np.int32(root))
            copy_gathered_null_bytes(ctwsu__avafj._null_bitmap.ctypes,
                tmp_null_bytes, recv_counts_nulls, recv_counts)
            return ctwsu__avafj
        return gatherv_impl_int_arr
    if isinstance(data, (IntegerArrayType, DecimalArrayType)) or data in (
        boolean_array, datetime_date_array_type):
        typ_val = numba_to_c_type(data.dtype)
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))

        def gatherv_impl_int_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            obp__pijwm = len(data)
            lhpt__orl = obp__pijwm + 7 >> 3
            recv_counts = gather_scalar(np.int32(obp__pijwm), allgather,
                root=root)
            owq__dvn = recv_counts.sum()
            ctwsu__avafj = empty_like_type(owq__dvn, data)
            ryvvd__bvzpy = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            obbj__qybp = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                ryvvd__bvzpy = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                obbj__qybp = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(data._data.ctypes, np.int32(obp__pijwm), ctwsu__avafj
                ._data.ctypes, recv_counts.ctypes, ryvvd__bvzpy.ctypes, np.
                int32(typ_val), allgather, np.int32(root))
            c_gatherv(data._null_bitmap.ctypes, np.int32(lhpt__orl),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, obbj__qybp
                .ctypes, ypndc__vfeo, allgather, np.int32(root))
            copy_gathered_null_bytes(ctwsu__avafj._null_bitmap.ctypes,
                tmp_null_bytes, recv_counts_nulls, recv_counts)
            return ctwsu__avafj
        return gatherv_impl_int_arr
    if isinstance(data, DatetimeArrayType):
        xxzd__cyzie = data.tz

        def impl_pd_datetime_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            iqr__hll = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.pd_datetime_arr_ext.init_pandas_datetime_array(
                iqr__hll, xxzd__cyzie)
        return impl_pd_datetime_arr
    if isinstance(data, IntervalArrayType):

        def impl_interval_arr(data, allgather=False, warn_if_rep=True, root
            =MPI_ROOT):
            wak__wszmz = bodo.gatherv(data._left, allgather, warn_if_rep, root)
            qpprl__cum = bodo.gatherv(data._right, allgather, warn_if_rep, root
                )
            return bodo.libs.interval_arr_ext.init_interval_array(wak__wszmz,
                qpprl__cum)
        return impl_interval_arr
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            isc__vftsg = bodo.hiframes.pd_series_ext.get_series_name(data)
            out_arr = bodo.libs.distributed_api.gatherv(arr, allgather,
                warn_if_rep, root)
            eau__oeco = bodo.gatherv(index, allgather, warn_if_rep, root)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                eau__oeco, isc__vftsg)
        return impl
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):
        qmfew__bhpnv = np.iinfo(np.int64).max
        say__vgey = np.iinfo(np.int64).min

        def impl_range_index(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            start = data._start
            stop = data._stop
            if len(data) == 0:
                start = qmfew__bhpnv
                stop = say__vgey
            start = bodo.libs.distributed_api.dist_reduce(start, np.int32(
                Reduce_Type.Min.value))
            stop = bodo.libs.distributed_api.dist_reduce(stop, np.int32(
                Reduce_Type.Max.value))
            total_len = bodo.libs.distributed_api.dist_reduce(len(data), np
                .int32(Reduce_Type.Sum.value))
            if start == qmfew__bhpnv and stop == say__vgey:
                start = 0
                stop = 0
            dwuui__oin = max(0, -(-(stop - start) // data._step))
            if dwuui__oin < total_len:
                stop = start + data._step * total_len
            if bodo.get_rank() != root and not allgather:
                start = 0
                stop = 0
            return bodo.hiframes.pd_index_ext.init_range_index(start, stop,
                data._step, data._name)
        return impl_range_index
    if bodo.hiframes.pd_index_ext.is_pd_index_type(data):
        from bodo.hiframes.pd_index_ext import DatetimeIndexType, PeriodIndexType
        if isinstance(data, PeriodIndexType):
            kliw__wzow = data.freq

            def impl_pd_index(data, allgather=False, warn_if_rep=True, root
                =MPI_ROOT):
                arr = bodo.libs.distributed_api.gatherv(data._data,
                    allgather, root=root)
                return bodo.hiframes.pd_index_ext.init_period_index(arr,
                    data._name, kliw__wzow)
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
            ctwsu__avafj = bodo.gatherv(data._data, allgather, root=root)
            return bodo.hiframes.pd_multi_index_ext.init_multi_index(
                ctwsu__avafj, data._names, data._name)
        return impl_multi_index
    if isinstance(data, bodo.hiframes.table.TableType):
        hlsyl__yarv = {'bodo': bodo, 'get_table_block': bodo.hiframes.table
            .get_table_block, 'ensure_column_unboxed': bodo.hiframes.table.
            ensure_column_unboxed, 'set_table_block': bodo.hiframes.table.
            set_table_block, 'set_table_len': bodo.hiframes.table.
            set_table_len, 'alloc_list_like': bodo.hiframes.table.
            alloc_list_like, 'init_table': bodo.hiframes.table.init_table}
        dxfra__rogyq = f"""def impl_table(data, allgather=False, warn_if_rep=True, root={MPI_ROOT}):
"""
        dxfra__rogyq += '  T = data\n'
        dxfra__rogyq += '  T2 = init_table(T, True)\n'
        for iqh__yjk in data.type_to_blk.values():
            hlsyl__yarv[f'arr_inds_{iqh__yjk}'] = np.array(data.
                block_to_arr_ind[iqh__yjk], dtype=np.int64)
            dxfra__rogyq += (
                f'  arr_list_{iqh__yjk} = get_table_block(T, {iqh__yjk})\n')
            dxfra__rogyq += f"""  out_arr_list_{iqh__yjk} = alloc_list_like(arr_list_{iqh__yjk}, True)
"""
            dxfra__rogyq += f'  for i in range(len(arr_list_{iqh__yjk})):\n'
            dxfra__rogyq += (
                f'    arr_ind_{iqh__yjk} = arr_inds_{iqh__yjk}[i]\n')
            dxfra__rogyq += f"""    ensure_column_unboxed(T, arr_list_{iqh__yjk}, i, arr_ind_{iqh__yjk})
"""
            dxfra__rogyq += f"""    out_arr_{iqh__yjk} = bodo.gatherv(arr_list_{iqh__yjk}[i], allgather, warn_if_rep, root)
"""
            dxfra__rogyq += (
                f'    out_arr_list_{iqh__yjk}[i] = out_arr_{iqh__yjk}\n')
            dxfra__rogyq += (
                f'  T2 = set_table_block(T2, out_arr_list_{iqh__yjk}, {iqh__yjk})\n'
                )
        dxfra__rogyq += (
            f'  length = T._len if bodo.get_rank() == root or allgather else 0\n'
            )
        dxfra__rogyq += f'  T2 = set_table_len(T2, length)\n'
        dxfra__rogyq += f'  return T2\n'
        seu__wwq = {}
        exec(dxfra__rogyq, hlsyl__yarv, seu__wwq)
        dtgp__puk = seu__wwq['impl_table']
        return dtgp__puk
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        ninkc__wptm = len(data.columns)
        if ninkc__wptm == 0:

            def impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
                index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data
                    )
                pes__leh = bodo.gatherv(index, allgather, warn_if_rep, root)
                return bodo.hiframes.pd_dataframe_ext.init_dataframe((),
                    pes__leh, ())
            return impl
        gpk__kyo = ', '.join(f'g_data_{i}' for i in range(ninkc__wptm))
        kqh__nfa = bodo.utils.transform.gen_const_tup(data.columns)
        dxfra__rogyq = (
            'def impl_df(data, allgather=False, warn_if_rep=True, root={}):\n'
            .format(MPI_ROOT))
        if data.is_table_format:
            from bodo.transforms.distributed_analysis import Distribution
            cdjd__xtf = bodo.hiframes.pd_dataframe_ext.DataFrameType(data.
                data, data.index, data.columns, Distribution.REP, True)
            hlsyl__yarv = {'bodo': bodo, 'df_type': cdjd__xtf}
            gpk__kyo = 'T2'
            kqh__nfa = 'df_type'
            dxfra__rogyq += (
                '  T = bodo.hiframes.pd_dataframe_ext.get_dataframe_table(data)\n'
                )
            dxfra__rogyq += (
                '  T2 = bodo.gatherv(T, allgather, warn_if_rep, root)\n')
        else:
            hlsyl__yarv = {'bodo': bodo}
            for i in range(ninkc__wptm):
                dxfra__rogyq += (
                    """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                    .format(i, i))
                dxfra__rogyq += (
                    """  g_data_{} = bodo.gatherv(data_{}, allgather, warn_if_rep, root)
"""
                    .format(i, i))
        dxfra__rogyq += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        dxfra__rogyq += (
            '  g_index = bodo.gatherv(index, allgather, warn_if_rep, root)\n')
        dxfra__rogyq += (
            """  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})
"""
            .format(gpk__kyo, kqh__nfa))
        seu__wwq = {}
        exec(dxfra__rogyq, hlsyl__yarv, seu__wwq)
        tqbm__xmzcs = seu__wwq['impl_df']
        return tqbm__xmzcs
    if isinstance(data, ArrayItemArrayType):
        taku__eqmp = np.int32(numba_to_c_type(types.int32))
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))

        def gatherv_array_item_arr_impl(data, allgather=False, warn_if_rep=
            True, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            zjwic__psro = bodo.libs.array_item_arr_ext.get_offsets(data)
            abapr__ogtr = bodo.libs.array_item_arr_ext.get_data(data)
            abapr__ogtr = abapr__ogtr[:zjwic__psro[-1]]
            glaui__efb = bodo.libs.array_item_arr_ext.get_null_bitmap(data)
            obp__pijwm = len(data)
            ncl__adh = np.empty(obp__pijwm, np.uint32)
            lhpt__orl = obp__pijwm + 7 >> 3
            for i in range(obp__pijwm):
                ncl__adh[i] = zjwic__psro[i + 1] - zjwic__psro[i]
            recv_counts = gather_scalar(np.int32(obp__pijwm), allgather,
                root=root)
            owq__dvn = recv_counts.sum()
            ryvvd__bvzpy = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            obbj__qybp = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                ryvvd__bvzpy = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for fkf__dvsk in range(len(recv_counts)):
                    recv_counts_nulls[fkf__dvsk] = recv_counts[fkf__dvsk
                        ] + 7 >> 3
                obbj__qybp = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            ufwq__bjf = np.empty(owq__dvn + 1, np.uint32)
            ysq__aho = bodo.gatherv(abapr__ogtr, allgather, warn_if_rep, root)
            zruy__gotuc = np.empty(owq__dvn + 7 >> 3, np.uint8)
            c_gatherv(ncl__adh.ctypes, np.int32(obp__pijwm), ufwq__bjf.
                ctypes, recv_counts.ctypes, ryvvd__bvzpy.ctypes, taku__eqmp,
                allgather, np.int32(root))
            c_gatherv(glaui__efb.ctypes, np.int32(lhpt__orl),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, obbj__qybp
                .ctypes, ypndc__vfeo, allgather, np.int32(root))
            dummy_use(data)
            azl__ddcpy = np.empty(owq__dvn + 1, np.uint64)
            convert_len_arr_to_offset(ufwq__bjf.ctypes, azl__ddcpy.ctypes,
                owq__dvn)
            copy_gathered_null_bytes(zruy__gotuc.ctypes, tmp_null_bytes,
                recv_counts_nulls, recv_counts)
            out_arr = bodo.libs.array_item_arr_ext.init_array_item_array(
                owq__dvn, ysq__aho, azl__ddcpy, zruy__gotuc)
            return out_arr
        return gatherv_array_item_arr_impl
    if isinstance(data, StructArrayType):
        cgcq__gsmz = data.names
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))

        def impl_struct_arr(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            sdnmw__mxtyw = bodo.libs.struct_arr_ext.get_data(data)
            pbzg__sgghc = bodo.libs.struct_arr_ext.get_null_bitmap(data)
            eea__smv = bodo.gatherv(sdnmw__mxtyw, allgather=allgather, root
                =root)
            rank = bodo.libs.distributed_api.get_rank()
            obp__pijwm = len(data)
            lhpt__orl = obp__pijwm + 7 >> 3
            recv_counts = gather_scalar(np.int32(obp__pijwm), allgather,
                root=root)
            owq__dvn = recv_counts.sum()
            tnfh__znf = np.empty(owq__dvn + 7 >> 3, np.uint8)
            recv_counts_nulls = np.empty(1, np.int32)
            obbj__qybp = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                obbj__qybp = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(pbzg__sgghc.ctypes, np.int32(lhpt__orl),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, obbj__qybp
                .ctypes, ypndc__vfeo, allgather, np.int32(root))
            copy_gathered_null_bytes(tnfh__znf.ctypes, tmp_null_bytes,
                recv_counts_nulls, recv_counts)
            return bodo.libs.struct_arr_ext.init_struct_arr(eea__smv,
                tnfh__znf, cgcq__gsmz)
        return impl_struct_arr
    if data == binary_array_type:

        def impl_bin_arr(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            ctwsu__avafj = bodo.gatherv(data._data, allgather, warn_if_rep,
                root)
            return bodo.libs.binary_arr_ext.init_binary_arr(ctwsu__avafj)
        return impl_bin_arr
    if isinstance(data, TupleArrayType):

        def impl_tuple_arr(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            ctwsu__avafj = bodo.gatherv(data._data, allgather, warn_if_rep,
                root)
            return bodo.libs.tuple_arr_ext.init_tuple_arr(ctwsu__avafj)
        return impl_tuple_arr
    if isinstance(data, MapArrayType):

        def impl_map_arr(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            ctwsu__avafj = bodo.gatherv(data._data, allgather, warn_if_rep,
                root)
            return bodo.libs.map_arr_ext.init_map_arr(ctwsu__avafj)
        return impl_map_arr
    if isinstance(data, CSRMatrixType):

        def impl_csr_matrix(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            ctwsu__avafj = bodo.gatherv(data.data, allgather, warn_if_rep, root
                )
            etic__tevyq = bodo.gatherv(data.indices, allgather, warn_if_rep,
                root)
            yuony__deyry = bodo.gatherv(data.indptr, allgather, warn_if_rep,
                root)
            pvmvd__wovfe = gather_scalar(data.shape[0], allgather, root=root)
            yyw__cxswz = pvmvd__wovfe.sum()
            ninkc__wptm = bodo.libs.distributed_api.dist_reduce(data.shape[
                1], np.int32(Reduce_Type.Max.value))
            fdhu__hnba = np.empty(yyw__cxswz + 1, np.int64)
            etic__tevyq = etic__tevyq.astype(np.int64)
            fdhu__hnba[0] = 0
            mvg__fhmz = 1
            kmyfx__kcx = 0
            for kppnv__jdhf in pvmvd__wovfe:
                for wfm__svkkk in range(kppnv__jdhf):
                    fckr__zsbh = yuony__deyry[kmyfx__kcx + 1] - yuony__deyry[
                        kmyfx__kcx]
                    fdhu__hnba[mvg__fhmz] = fdhu__hnba[mvg__fhmz - 1
                        ] + fckr__zsbh
                    mvg__fhmz += 1
                    kmyfx__kcx += 1
                kmyfx__kcx += 1
            return bodo.libs.csr_matrix_ext.init_csr_matrix(ctwsu__avafj,
                etic__tevyq, fdhu__hnba, (yyw__cxswz, ninkc__wptm))
        return impl_csr_matrix
    if isinstance(data, types.BaseTuple):
        dxfra__rogyq = (
            'def impl_tuple(data, allgather=False, warn_if_rep=True, root={}):\n'
            .format(MPI_ROOT))
        dxfra__rogyq += '  return ({}{})\n'.format(', '.join(
            'bodo.gatherv(data[{}], allgather, warn_if_rep, root)'.format(i
            ) for i in range(len(data))), ',' if len(data) > 0 else '')
        seu__wwq = {}
        exec(dxfra__rogyq, {'bodo': bodo}, seu__wwq)
        anei__cot = seu__wwq['impl_tuple']
        return anei__cot
    if data is types.none:
        return (lambda data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT: None)
    raise BodoError('gatherv() not available for {}'.format(data))


@numba.generated_jit(nopython=True)
def rebalance(data, dests=None, random=False, random_seed=None, parallel=False
    ):
    bodo.hiframes.pd_dataframe_ext.check_runtime_cols_unsupported(data,
        'bodo.rebalance()')
    dxfra__rogyq = (
        'def impl(data, dests=None, random=False, random_seed=None, parallel=False):\n'
        )
    dxfra__rogyq += '    if random:\n'
    dxfra__rogyq += '        if random_seed is None:\n'
    dxfra__rogyq += '            random = 1\n'
    dxfra__rogyq += '        else:\n'
    dxfra__rogyq += '            random = 2\n'
    dxfra__rogyq += '    if random_seed is None:\n'
    dxfra__rogyq += '        random_seed = -1\n'
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        soobw__gbsx = data
        ninkc__wptm = len(soobw__gbsx.columns)
        for i in range(ninkc__wptm):
            dxfra__rogyq += f"""    data_{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {i})
"""
        dxfra__rogyq += """    ind_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data))
"""
        gpk__kyo = ', '.join(f'data_{i}' for i in range(ninkc__wptm))
        dxfra__rogyq += ('    info_list_total = [{}, array_to_info(ind_arr)]\n'
            .format(', '.join('array_to_info(data_{})'.format(dsfq__hbb) for
            dsfq__hbb in range(ninkc__wptm))))
        dxfra__rogyq += (
            '    table_total = arr_info_list_to_table(info_list_total)\n')
        dxfra__rogyq += '    if dests is None:\n'
        dxfra__rogyq += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        dxfra__rogyq += '    else:\n'
        dxfra__rogyq += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        for vwf__fvr in range(ninkc__wptm):
            dxfra__rogyq += (
                """    out_arr_{0} = info_to_array(info_from_table(out_table, {0}), data_{0})
"""
                .format(vwf__fvr))
        dxfra__rogyq += (
            """    out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)
"""
            .format(ninkc__wptm))
        dxfra__rogyq += '    delete_table(out_table)\n'
        dxfra__rogyq += '    if parallel:\n'
        dxfra__rogyq += '        delete_table(table_total)\n'
        gpk__kyo = ', '.join('out_arr_{}'.format(i) for i in range(ninkc__wptm)
            )
        kqh__nfa = bodo.utils.transform.gen_const_tup(soobw__gbsx.columns)
        index = 'bodo.utils.conversion.index_from_array(out_arr_index)'
        dxfra__rogyq += (
            '    return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), {}, {})\n'
            .format(gpk__kyo, index, kqh__nfa))
    elif isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):
        dxfra__rogyq += (
            '    data_0 = bodo.hiframes.pd_series_ext.get_series_data(data)\n')
        dxfra__rogyq += """    ind_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(data))
"""
        dxfra__rogyq += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(data)\n')
        dxfra__rogyq += """    table_total = arr_info_list_to_table([array_to_info(data_0), array_to_info(ind_arr)])
"""
        dxfra__rogyq += '    if dests is None:\n'
        dxfra__rogyq += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        dxfra__rogyq += '    else:\n'
        dxfra__rogyq += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        dxfra__rogyq += (
            '    out_arr_0 = info_to_array(info_from_table(out_table, 0), data_0)\n'
            )
        dxfra__rogyq += """    out_arr_index = info_to_array(info_from_table(out_table, 1), ind_arr)
"""
        dxfra__rogyq += '    delete_table(out_table)\n'
        dxfra__rogyq += '    if parallel:\n'
        dxfra__rogyq += '        delete_table(table_total)\n'
        index = 'bodo.utils.conversion.index_from_array(out_arr_index)'
        dxfra__rogyq += f"""    return bodo.hiframes.pd_series_ext.init_series(out_arr_0, {index}, name)
"""
    elif isinstance(data, types.Array):
        assert is_overload_false(random
            ), 'Call random_shuffle instead of rebalance'
        dxfra__rogyq += '    if not parallel:\n'
        dxfra__rogyq += '        return data\n'
        dxfra__rogyq += """    dim0_global_size = bodo.libs.distributed_api.dist_reduce(data.shape[0], np.int32(bodo.libs.distributed_api.Reduce_Type.Sum.value))
"""
        dxfra__rogyq += '    if dests is None:\n'
        dxfra__rogyq += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, bodo.get_size(), bodo.get_rank())
"""
        dxfra__rogyq += '    elif bodo.get_rank() not in dests:\n'
        dxfra__rogyq += '        dim0_local_size = 0\n'
        dxfra__rogyq += '    else:\n'
        dxfra__rogyq += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, len(dests), dests.index(bodo.get_rank()))
"""
        dxfra__rogyq += """    out = np.empty((dim0_local_size,) + tuple(data.shape[1:]), dtype=data.dtype)
"""
        dxfra__rogyq += """    bodo.libs.distributed_api.dist_oneD_reshape_shuffle(out, data, dim0_global_size, dests)
"""
        dxfra__rogyq += '    return out\n'
    elif bodo.utils.utils.is_array_typ(data, False):
        dxfra__rogyq += (
            '    table_total = arr_info_list_to_table([array_to_info(data)])\n'
            )
        dxfra__rogyq += '    if dests is None:\n'
        dxfra__rogyq += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        dxfra__rogyq += '    else:\n'
        dxfra__rogyq += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        dxfra__rogyq += (
            '    out_arr = info_to_array(info_from_table(out_table, 0), data)\n'
            )
        dxfra__rogyq += '    delete_table(out_table)\n'
        dxfra__rogyq += '    if parallel:\n'
        dxfra__rogyq += '        delete_table(table_total)\n'
        dxfra__rogyq += '    return out_arr\n'
    else:
        raise BodoError(f'Type {data} not supported for bodo.rebalance')
    seu__wwq = {}
    exec(dxfra__rogyq, {'np': np, 'bodo': bodo, 'array_to_info': bodo.libs.
        array.array_to_info, 'shuffle_renormalization': bodo.libs.array.
        shuffle_renormalization, 'shuffle_renormalization_group': bodo.libs
        .array.shuffle_renormalization_group, 'arr_info_list_to_table':
        bodo.libs.array.arr_info_list_to_table, 'info_from_table': bodo.
        libs.array.info_from_table, 'info_to_array': bodo.libs.array.
        info_to_array, 'delete_table': bodo.libs.array.delete_table}, seu__wwq)
    impl = seu__wwq['impl']
    return impl


@numba.generated_jit(nopython=True)
def random_shuffle(data, seed=None, dests=None, parallel=False):
    dxfra__rogyq = 'def impl(data, seed=None, dests=None, parallel=False):\n'
    if isinstance(data, types.Array):
        if not is_overload_none(dests):
            raise BodoError('not supported')
        dxfra__rogyq += '    if seed is None:\n'
        dxfra__rogyq += """        seed = bodo.libs.distributed_api.bcast_scalar(np.random.randint(0, 2**31))
"""
        dxfra__rogyq += '    np.random.seed(seed)\n'
        dxfra__rogyq += '    if not parallel:\n'
        dxfra__rogyq += '        data = data.copy()\n'
        dxfra__rogyq += '        np.random.shuffle(data)\n'
        dxfra__rogyq += '        return data\n'
        dxfra__rogyq += '    else:\n'
        dxfra__rogyq += """        dim0_global_size = bodo.libs.distributed_api.dist_reduce(data.shape[0], np.int32(bodo.libs.distributed_api.Reduce_Type.Sum.value))
"""
        dxfra__rogyq += '        permutation = np.arange(dim0_global_size)\n'
        dxfra__rogyq += '        np.random.shuffle(permutation)\n'
        dxfra__rogyq += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, bodo.get_size(), bodo.get_rank())
"""
        dxfra__rogyq += """        output = np.empty((dim0_local_size,) + tuple(data.shape[1:]), dtype=data.dtype)
"""
        dxfra__rogyq += (
            '        dtype_size = bodo.io.np_io.get_dtype_size(data.dtype)\n')
        dxfra__rogyq += """        bodo.libs.distributed_api.dist_permutation_array_index(output, dim0_global_size, dtype_size, data, permutation, len(permutation))
"""
        dxfra__rogyq += '        return output\n'
    else:
        dxfra__rogyq += """    return bodo.libs.distributed_api.rebalance(data, dests=dests, random=True, random_seed=seed, parallel=parallel)
"""
    seu__wwq = {}
    exec(dxfra__rogyq, {'np': np, 'bodo': bodo}, seu__wwq)
    impl = seu__wwq['impl']
    return impl


@numba.generated_jit(nopython=True)
def allgatherv(data, warn_if_rep=True, root=MPI_ROOT):
    return lambda data, warn_if_rep=True, root=MPI_ROOT: gatherv(data, True,
        warn_if_rep, root)


@numba.njit
def get_scatter_null_bytes_buff(null_bitmap_ptr, sendcounts, sendcounts_nulls):
    if bodo.get_rank() != MPI_ROOT:
        return np.empty(1, np.uint8)
    xwxo__yizuj = np.empty(sendcounts_nulls.sum(), np.uint8)
    otyyu__mcjrn = 0
    wgjcw__mihy = 0
    for cwhmq__hwrma in range(len(sendcounts)):
        enufg__llsxd = sendcounts[cwhmq__hwrma]
        lhpt__orl = sendcounts_nulls[cwhmq__hwrma]
        dyr__yoxio = xwxo__yizuj[otyyu__mcjrn:otyyu__mcjrn + lhpt__orl]
        for ompgx__zrcl in range(enufg__llsxd):
            set_bit_to_arr(dyr__yoxio, ompgx__zrcl, get_bit_bitmap(
                null_bitmap_ptr, wgjcw__mihy))
            wgjcw__mihy += 1
        otyyu__mcjrn += lhpt__orl
    return xwxo__yizuj


def _bcast_dtype(data, root=MPI_ROOT):
    try:
        from mpi4py import MPI
    except:
        raise BodoError('mpi4py is required for scatterv')
    vrfsc__otjzy = MPI.COMM_WORLD
    data = vrfsc__otjzy.bcast(data, root)
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
    cfaob__aeyvs = data.ndim
    dtype = data.dtype
    if dtype == types.NPDatetime('ns'):
        dtype = np.dtype('datetime64[ns]')
    elif dtype == types.NPTimedelta('ns'):
        dtype = np.dtype('timedelta64[ns]')
    hpok__yskjp = (0,) * cfaob__aeyvs

    def scatterv_arr_impl(data, send_counts=None, warn_if_dist=True):
        rank = bodo.libs.distributed_api.get_rank()
        n_pes = bodo.libs.distributed_api.get_size()
        ennqf__tgg = np.ascontiguousarray(data)
        sqgs__rfdt = data.ctypes
        lwh__hpugr = hpok__yskjp
        if rank == MPI_ROOT:
            lwh__hpugr = ennqf__tgg.shape
        lwh__hpugr = bcast_tuple(lwh__hpugr)
        qpe__zncgb = get_tuple_prod(lwh__hpugr[1:])
        send_counts = _get_scatterv_send_counts(send_counts, n_pes,
            lwh__hpugr[0])
        send_counts *= qpe__zncgb
        obp__pijwm = send_counts[rank]
        akdn__yeh = np.empty(obp__pijwm, dtype)
        ryvvd__bvzpy = bodo.ir.join.calc_disp(send_counts)
        c_scatterv(sqgs__rfdt, send_counts.ctypes, ryvvd__bvzpy.ctypes,
            akdn__yeh.ctypes, np.int32(obp__pijwm), np.int32(typ_val))
        return akdn__yeh.reshape((-1,) + lwh__hpugr[1:])
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
        wllo__apr = '{}Int{}'.format('' if dtype.dtype.signed else 'U',
            dtype.dtype.bitwidth)
        return pd.array([3], wllo__apr)
    if dtype == boolean_array:
        return pd.array([True], 'boolean')
    if isinstance(dtype, DecimalArrayType):
        return np.array([Decimal('32.1')])
    if dtype == datetime_date_array_type:
        return np.array([datetime.date(2011, 8, 9)])
    if dtype == datetime_timedelta_array_type:
        return np.array([datetime.timedelta(33)])
    if bodo.hiframes.pd_index_ext.is_pd_index_type(dtype):
        isc__vftsg = _get_name_value_for_type(dtype.name_typ)
        if isinstance(dtype, bodo.hiframes.pd_index_ext.RangeIndexType):
            return pd.RangeIndex(1, name=isc__vftsg)
        sza__sprkq = bodo.utils.typing.get_index_data_arr_types(dtype)[0]
        arr = get_value_for_type(sza__sprkq)
        return pd.Index(arr, name=isc__vftsg)
    if isinstance(dtype, bodo.hiframes.pd_multi_index_ext.MultiIndexType):
        import pyarrow as pa
        isc__vftsg = _get_name_value_for_type(dtype.name_typ)
        cgcq__gsmz = tuple(_get_name_value_for_type(t) for t in dtype.names_typ
            )
        mzwt__zjsp = tuple(get_value_for_type(t) for t in dtype.array_types)
        mzwt__zjsp = tuple(a.to_numpy(False) if isinstance(a, pa.Array) else
            a for a in mzwt__zjsp)
        val = pd.MultiIndex.from_arrays(mzwt__zjsp, names=cgcq__gsmz)
        val.name = isc__vftsg
        return val
    if isinstance(dtype, bodo.hiframes.pd_series_ext.SeriesType):
        isc__vftsg = _get_name_value_for_type(dtype.name_typ)
        arr = get_value_for_type(dtype.data)
        index = get_value_for_type(dtype.index)
        return pd.Series(arr, index, name=isc__vftsg)
    if isinstance(dtype, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        mzwt__zjsp = tuple(get_value_for_type(t) for t in dtype.data)
        index = get_value_for_type(dtype.index)
        return pd.DataFrame({isc__vftsg: arr for isc__vftsg, arr in zip(
            dtype.columns, mzwt__zjsp)}, index)
    if isinstance(dtype, CategoricalArrayType):
        return pd.Categorical.from_codes([0], dtype.dtype.categories)
    if isinstance(dtype, types.BaseTuple):
        return tuple(get_value_for_type(t) for t in dtype.types)
    if isinstance(dtype, ArrayItemArrayType):
        return pd.Series([get_value_for_type(dtype.dtype),
            get_value_for_type(dtype.dtype)]).values
    if isinstance(dtype, IntervalArrayType):
        sza__sprkq = get_value_for_type(dtype.arr_type)
        return pd.arrays.IntervalArray([pd.Interval(sza__sprkq[0],
            sza__sprkq[0])])
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
    return lambda data, send_counts=None, warn_if_dist=True: scatterv_impl(data
        , send_counts)


@numba.generated_jit(nopython=True)
def scatterv_impl(data, send_counts=None, warn_if_dist=True):
    if isinstance(data, types.Array):
        return lambda data, send_counts=None, warn_if_dist=True: _scatterv_np(
            data, send_counts)
    if is_str_arr_type(data) or data == binary_array_type:
        taku__eqmp = np.int32(numba_to_c_type(types.int32))
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))
        if data == binary_array_type:
            kchw__ofua = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
        else:
            kchw__ofua = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
        dxfra__rogyq = f"""def impl(
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
            recv_arr = {kchw__ofua}(n_loc, n_loc_char)

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
        seu__wwq = dict()
        exec(dxfra__rogyq, {'bodo': bodo, 'np': np, 'int32_typ_enum':
            taku__eqmp, 'char_typ_enum': ypndc__vfeo,
            'decode_if_dict_array': decode_if_dict_array}, seu__wwq)
        impl = seu__wwq['impl']
        return impl
    if isinstance(data, ArrayItemArrayType):
        taku__eqmp = np.int32(numba_to_c_type(types.int32))
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))

        def scatterv_array_item_impl(data, send_counts=None, warn_if_dist=True
            ):
            xlwsy__xbmaa = bodo.libs.array_item_arr_ext.get_offsets(data)
            kmcny__haox = bodo.libs.array_item_arr_ext.get_data(data)
            kmcny__haox = kmcny__haox[:xlwsy__xbmaa[-1]]
            hltuo__ekrib = bodo.libs.array_item_arr_ext.get_null_bitmap(data)
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            ajt__jkiw = bcast_scalar(len(data))
            ryip__ysvx = np.empty(len(data), np.uint32)
            for i in range(len(data)):
                ryip__ysvx[i] = xlwsy__xbmaa[i + 1] - xlwsy__xbmaa[i]
            send_counts = _get_scatterv_send_counts(send_counts, n_pes,
                ajt__jkiw)
            ryvvd__bvzpy = bodo.ir.join.calc_disp(send_counts)
            fkwd__ungc = np.empty(n_pes, np.int32)
            if rank == 0:
                audl__kto = 0
                for i in range(n_pes):
                    ewto__ogiag = 0
                    for wfm__svkkk in range(send_counts[i]):
                        ewto__ogiag += ryip__ysvx[audl__kto]
                        audl__kto += 1
                    fkwd__ungc[i] = ewto__ogiag
            bcast(fkwd__ungc)
            huzd__bgsk = np.empty(n_pes, np.int32)
            for i in range(n_pes):
                huzd__bgsk[i] = send_counts[i] + 7 >> 3
            obbj__qybp = bodo.ir.join.calc_disp(huzd__bgsk)
            obp__pijwm = send_counts[rank]
            jcp__cxzsh = np.empty(obp__pijwm + 1, np_offset_type)
            nbl__mzuj = bodo.libs.distributed_api.scatterv_impl(kmcny__haox,
                fkwd__ungc)
            skic__svgc = obp__pijwm + 7 >> 3
            zxas__coa = np.empty(skic__svgc, np.uint8)
            gbb__wrnp = np.empty(obp__pijwm, np.uint32)
            c_scatterv(ryip__ysvx.ctypes, send_counts.ctypes, ryvvd__bvzpy.
                ctypes, gbb__wrnp.ctypes, np.int32(obp__pijwm), taku__eqmp)
            convert_len_arr_to_offset(gbb__wrnp.ctypes, jcp__cxzsh.ctypes,
                obp__pijwm)
            ivp__yvk = get_scatter_null_bytes_buff(hltuo__ekrib.ctypes,
                send_counts, huzd__bgsk)
            c_scatterv(ivp__yvk.ctypes, huzd__bgsk.ctypes, obbj__qybp.
                ctypes, zxas__coa.ctypes, np.int32(skic__svgc), ypndc__vfeo)
            return bodo.libs.array_item_arr_ext.init_array_item_array(
                obp__pijwm, nbl__mzuj, jcp__cxzsh, zxas__coa)
        return scatterv_array_item_impl
    if isinstance(data, (IntegerArrayType, DecimalArrayType)) or data in (
        boolean_array, datetime_date_array_type):
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))
        if isinstance(data, IntegerArrayType):
            zyr__iwer = bodo.libs.int_arr_ext.init_integer_array
        if isinstance(data, DecimalArrayType):
            precision = data.precision
            scale = data.scale
            zyr__iwer = numba.njit(no_cpython_wrapper=True)(lambda d, b:
                bodo.libs.decimal_arr_ext.init_decimal_array(d, b,
                precision, scale))
        if data == boolean_array:
            zyr__iwer = bodo.libs.bool_arr_ext.init_bool_array
        if data == datetime_date_array_type:
            zyr__iwer = (bodo.hiframes.datetime_date_ext.
                init_datetime_date_array)

        def scatterv_impl_int_arr(data, send_counts=None, warn_if_dist=True):
            n_pes = bodo.libs.distributed_api.get_size()
            ennqf__tgg = data._data
            pbzg__sgghc = data._null_bitmap
            yvc__jbmjs = len(ennqf__tgg)
            asw__wvl = _scatterv_np(ennqf__tgg, send_counts)
            ajt__jkiw = bcast_scalar(yvc__jbmjs)
            tshxc__uiuv = len(asw__wvl) + 7 >> 3
            erti__nnbuz = np.empty(tshxc__uiuv, np.uint8)
            send_counts = _get_scatterv_send_counts(send_counts, n_pes,
                ajt__jkiw)
            huzd__bgsk = np.empty(n_pes, np.int32)
            for i in range(n_pes):
                huzd__bgsk[i] = send_counts[i] + 7 >> 3
            obbj__qybp = bodo.ir.join.calc_disp(huzd__bgsk)
            ivp__yvk = get_scatter_null_bytes_buff(pbzg__sgghc.ctypes,
                send_counts, huzd__bgsk)
            c_scatterv(ivp__yvk.ctypes, huzd__bgsk.ctypes, obbj__qybp.
                ctypes, erti__nnbuz.ctypes, np.int32(tshxc__uiuv), ypndc__vfeo)
            return zyr__iwer(asw__wvl, erti__nnbuz)
        return scatterv_impl_int_arr
    if isinstance(data, IntervalArrayType):

        def impl_interval_arr(data, send_counts=None, warn_if_dist=True):
            tvx__lftrz = bodo.libs.distributed_api.scatterv_impl(data._left,
                send_counts)
            owmyy__xjl = bodo.libs.distributed_api.scatterv_impl(data.
                _right, send_counts)
            return bodo.libs.interval_arr_ext.init_interval_array(tvx__lftrz,
                owmyy__xjl)
        return impl_interval_arr
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):

        def impl_range_index(data, send_counts=None, warn_if_dist=True):
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            start = data._start
            stop = data._stop
            siwtr__pmec = data._step
            isc__vftsg = data._name
            isc__vftsg = bcast_scalar(isc__vftsg)
            start = bcast_scalar(start)
            stop = bcast_scalar(stop)
            siwtr__pmec = bcast_scalar(siwtr__pmec)
            nwy__pcrlo = bodo.libs.array_kernels.calc_nitems(start, stop,
                siwtr__pmec)
            chunk_start = bodo.libs.distributed_api.get_start(nwy__pcrlo,
                n_pes, rank)
            chunk_count = bodo.libs.distributed_api.get_node_portion(nwy__pcrlo
                , n_pes, rank)
            lpn__seirs = start + siwtr__pmec * chunk_start
            ehafk__ihdd = start + siwtr__pmec * (chunk_start + chunk_count)
            ehafk__ihdd = min(ehafk__ihdd, stop)
            return bodo.hiframes.pd_index_ext.init_range_index(lpn__seirs,
                ehafk__ihdd, siwtr__pmec, isc__vftsg)
        return impl_range_index
    if isinstance(data, bodo.hiframes.pd_index_ext.PeriodIndexType):
        kliw__wzow = data.freq

        def impl_period_index(data, send_counts=None, warn_if_dist=True):
            ennqf__tgg = data._data
            isc__vftsg = data._name
            isc__vftsg = bcast_scalar(isc__vftsg)
            arr = bodo.libs.distributed_api.scatterv_impl(ennqf__tgg,
                send_counts)
            return bodo.hiframes.pd_index_ext.init_period_index(arr,
                isc__vftsg, kliw__wzow)
        return impl_period_index
    if bodo.hiframes.pd_index_ext.is_pd_index_type(data):

        def impl_pd_index(data, send_counts=None, warn_if_dist=True):
            ennqf__tgg = data._data
            isc__vftsg = data._name
            isc__vftsg = bcast_scalar(isc__vftsg)
            arr = bodo.libs.distributed_api.scatterv_impl(ennqf__tgg,
                send_counts)
            return bodo.utils.conversion.index_from_array(arr, isc__vftsg)
        return impl_pd_index
    if isinstance(data, bodo.hiframes.pd_multi_index_ext.MultiIndexType):

        def impl_multi_index(data, send_counts=None, warn_if_dist=True):
            ctwsu__avafj = bodo.libs.distributed_api.scatterv_impl(data.
                _data, send_counts)
            isc__vftsg = bcast_scalar(data._name)
            cgcq__gsmz = bcast_tuple(data._names)
            return bodo.hiframes.pd_multi_index_ext.init_multi_index(
                ctwsu__avafj, cgcq__gsmz, isc__vftsg)
        return impl_multi_index
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl_series(data, send_counts=None, warn_if_dist=True):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            isc__vftsg = bodo.hiframes.pd_series_ext.get_series_name(data)
            ypr__kthrj = bcast_scalar(isc__vftsg)
            out_arr = bodo.libs.distributed_api.scatterv_impl(arr, send_counts)
            eau__oeco = bodo.libs.distributed_api.scatterv_impl(index,
                send_counts)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                eau__oeco, ypr__kthrj)
        return impl_series
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        ninkc__wptm = len(data.columns)
        gpk__kyo = ', '.join('g_data_{}'.format(i) for i in range(ninkc__wptm))
        kqh__nfa = bodo.utils.transform.gen_const_tup(data.columns)
        dxfra__rogyq = (
            'def impl_df(data, send_counts=None, warn_if_dist=True):\n')
        for i in range(ninkc__wptm):
            dxfra__rogyq += (
                """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                .format(i, i))
            dxfra__rogyq += (
                """  g_data_{} = bodo.libs.distributed_api.scatterv_impl(data_{}, send_counts)
"""
                .format(i, i))
        dxfra__rogyq += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        dxfra__rogyq += (
            '  g_index = bodo.libs.distributed_api.scatterv_impl(index, send_counts)\n'
            )
        dxfra__rogyq += (
            """  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})
"""
            .format(gpk__kyo, kqh__nfa))
        seu__wwq = {}
        exec(dxfra__rogyq, {'bodo': bodo}, seu__wwq)
        tqbm__xmzcs = seu__wwq['impl_df']
        return tqbm__xmzcs
    if isinstance(data, CategoricalArrayType):

        def impl_cat(data, send_counts=None, warn_if_dist=True):
            ghiq__ajasf = bodo.libs.distributed_api.scatterv_impl(data.
                codes, send_counts)
            return bodo.hiframes.pd_categorical_ext.init_categorical_array(
                ghiq__ajasf, data.dtype)
        return impl_cat
    if isinstance(data, types.BaseTuple):
        dxfra__rogyq = (
            'def impl_tuple(data, send_counts=None, warn_if_dist=True):\n')
        dxfra__rogyq += '  return ({}{})\n'.format(', '.join(
            'bodo.libs.distributed_api.scatterv_impl(data[{}], send_counts)'
            .format(i) for i in range(len(data))), ',' if len(data) > 0 else ''
            )
        seu__wwq = {}
        exec(dxfra__rogyq, {'bodo': bodo}, seu__wwq)
        anei__cot = seu__wwq['impl_tuple']
        return anei__cot
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
        chagv__gld = np.int32(numba_to_c_type(offset_type))
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))

        def bcast_str_impl(data, root=MPI_ROOT):
            data = decode_if_dict_array(data)
            obp__pijwm = len(data)
            jjlwg__fcs = num_total_chars(data)
            assert obp__pijwm < INT_MAX
            assert jjlwg__fcs < INT_MAX
            drrd__lkm = get_offset_ptr(data)
            sqgs__rfdt = get_data_ptr(data)
            null_bitmap_ptr = get_null_bitmap_ptr(data)
            lhpt__orl = obp__pijwm + 7 >> 3
            c_bcast(drrd__lkm, np.int32(obp__pijwm + 1), chagv__gld, np.
                array([-1]).ctypes, 0, np.int32(root))
            c_bcast(sqgs__rfdt, np.int32(jjlwg__fcs), ypndc__vfeo, np.array
                ([-1]).ctypes, 0, np.int32(root))
            c_bcast(null_bitmap_ptr, np.int32(lhpt__orl), ypndc__vfeo, np.
                array([-1]).ctypes, 0, np.int32(root))
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
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))

        def impl_str(val, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            if rank != root:
                knnqm__uqzbm = 0
                cqe__zqdw = np.empty(0, np.uint8).ctypes
            else:
                cqe__zqdw, knnqm__uqzbm = (bodo.libs.str_ext.
                    unicode_to_utf8_and_len(val))
            knnqm__uqzbm = bodo.libs.distributed_api.bcast_scalar(knnqm__uqzbm,
                root)
            if rank != root:
                puw__bng = np.empty(knnqm__uqzbm + 1, np.uint8)
                puw__bng[knnqm__uqzbm] = 0
                cqe__zqdw = puw__bng.ctypes
            c_bcast(cqe__zqdw, np.int32(knnqm__uqzbm), ypndc__vfeo, np.
                array([-1]).ctypes, 0, np.int32(root))
            return bodo.libs.str_arr_ext.decode_utf8(cqe__zqdw, knnqm__uqzbm)
        return impl_str
    typ_val = numba_to_c_type(val)
    dxfra__rogyq = f"""def bcast_scalar_impl(val, root={MPI_ROOT}):
  send = np.empty(1, dtype)
  send[0] = val
  c_bcast(send.ctypes, np.int32(1), np.int32({typ_val}), np.array([-1]).ctypes, 0, np.int32(root))
  return send[0]
"""
    dtype = numba.np.numpy_support.as_dtype(val)
    seu__wwq = {}
    exec(dxfra__rogyq, {'bodo': bodo, 'np': np, 'c_bcast': c_bcast, 'dtype':
        dtype}, seu__wwq)
    qoh__gdxi = seu__wwq['bcast_scalar_impl']
    return qoh__gdxi


@numba.generated_jit(nopython=True)
def bcast_tuple(val, root=MPI_ROOT):
    assert isinstance(val, types.BaseTuple)
    ulf__cow = len(val)
    dxfra__rogyq = f'def bcast_tuple_impl(val, root={MPI_ROOT}):\n'
    dxfra__rogyq += '  return ({}{})'.format(','.join(
        'bcast_scalar(val[{}], root)'.format(i) for i in range(ulf__cow)), 
        ',' if ulf__cow else '')
    seu__wwq = {}
    exec(dxfra__rogyq, {'bcast_scalar': bcast_scalar}, seu__wwq)
    ifgk__mat = seu__wwq['bcast_tuple_impl']
    return ifgk__mat


def prealloc_str_for_bcast(arr, root=MPI_ROOT):
    return arr


@overload(prealloc_str_for_bcast, no_unliteral=True)
def prealloc_str_for_bcast_overload(arr, root=MPI_ROOT):
    if arr == string_array_type:

        def prealloc_impl(arr, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            obp__pijwm = bcast_scalar(len(arr), root)
            hzd__mqz = bcast_scalar(np.int64(num_total_chars(arr)), root)
            if rank != root:
                arr = pre_alloc_string_array(obp__pijwm, hzd__mqz)
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
        siwtr__pmec = slice_index.step
        dilzu__zlhg = 0 if siwtr__pmec == 1 or start > arr_start else abs(
            siwtr__pmec - arr_start % siwtr__pmec) % siwtr__pmec
        lpn__seirs = max(arr_start, slice_index.start
            ) - arr_start + dilzu__zlhg
        ehafk__ihdd = max(slice_index.stop - arr_start, 0)
        return slice(lpn__seirs, ehafk__ihdd, siwtr__pmec)
    return impl


def slice_getitem(arr, slice_index, arr_start, total_len):
    return arr[slice_index]


@overload(slice_getitem, no_unliteral=True, jit_options={'cache': True})
def slice_getitem_overload(arr, slice_index, arr_start, total_len):

    def getitem_impl(arr, slice_index, arr_start, total_len):
        fsuia__ouhp = get_local_slice(slice_index, arr_start, total_len)
        return bodo.utils.conversion.ensure_contig_if_np(arr[fsuia__ouhp])
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
        vzov__jrej = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND
        ypndc__vfeo = np.int32(numba_to_c_type(types.uint8))
        lgf__fevc = arr.dtype

        def str_getitem_impl(arr, ind, arr_start, total_len, is_1D):
            if ind >= total_len:
                raise IndexError('index out of bounds')
            arr = decode_if_dict_array(arr)
            ind = ind % total_len
            root = np.int32(0)
            bpfd__idke = np.int32(10)
            tag = np.int32(11)
            xcirw__drbj = np.zeros(1, np.int64)
            if arr_start <= ind < arr_start + len(arr):
                ind = ind - arr_start
                abapr__ogtr = arr._data
                kdve__blf = bodo.libs.array_item_arr_ext.get_offsets_ind(
                    abapr__ogtr, ind)
                kobs__xehs = bodo.libs.array_item_arr_ext.get_offsets_ind(
                    abapr__ogtr, ind + 1)
                length = kobs__xehs - kdve__blf
                bkn__dns = abapr__ogtr[ind]
                xcirw__drbj[0] = length
                isend(xcirw__drbj, np.int32(1), root, bpfd__idke, True)
                isend(bkn__dns, np.int32(length), root, tag, True)
            rank = bodo.libs.distributed_api.get_rank()
            val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(lgf__fevc,
                vzov__jrej, 0, 1)
            dwuui__oin = 0
            if rank == root:
                dwuui__oin = recv(np.int64, ANY_SOURCE, bpfd__idke)
                val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(
                    lgf__fevc, vzov__jrej, dwuui__oin, 1)
                sqgs__rfdt = bodo.libs.str_ext.get_unicode_or_numpy_data(val)
                _recv(sqgs__rfdt, np.int32(dwuui__oin), ypndc__vfeo,
                    ANY_SOURCE, tag)
            dummy_use(xcirw__drbj)
            dwuui__oin = bcast_scalar(dwuui__oin)
            dummy_use(arr)
            if rank != root:
                val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(
                    lgf__fevc, vzov__jrej, dwuui__oin, 1)
            sqgs__rfdt = bodo.libs.str_ext.get_unicode_or_numpy_data(val)
            c_bcast(sqgs__rfdt, np.int32(dwuui__oin), ypndc__vfeo, np.array
                ([-1]).ctypes, 0, np.int32(root))
            val = transform_str_getitem_output(val, dwuui__oin)
            return val
        return str_getitem_impl
    if isinstance(arr, bodo.CategoricalArrayType):
        yey__twdsa = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            arr.dtype)

        def cat_getitem_impl(arr, ind, arr_start, total_len, is_1D):
            if ind >= total_len:
                raise IndexError('index out of bounds')
            ind = ind % total_len
            root = np.int32(0)
            tag = np.int32(11)
            send_arr = np.zeros(1, yey__twdsa)
            if arr_start <= ind < arr_start + len(arr):
                ghiq__ajasf = (bodo.hiframes.pd_categorical_ext.
                    get_categorical_arr_codes(arr))
                data = ghiq__ajasf[ind - arr_start]
                send_arr = np.full(1, data, yey__twdsa)
                isend(send_arr, np.int32(1), root, tag, True)
            rank = bodo.libs.distributed_api.get_rank()
            val = yey__twdsa(-1)
            if rank == root:
                val = recv(yey__twdsa, ANY_SOURCE, tag)
            dummy_use(send_arr)
            val = bcast_scalar(val)
            fib__miuj = arr.dtype.categories[max(val, 0)]
            return fib__miuj
        return cat_getitem_impl
    qqd__dcum = arr.dtype

    def getitem_impl(arr, ind, arr_start, total_len, is_1D):
        if ind >= total_len:
            raise IndexError('index out of bounds')
        ind = ind % total_len
        root = np.int32(0)
        tag = np.int32(11)
        send_arr = np.zeros(1, qqd__dcum)
        if arr_start <= ind < arr_start + len(arr):
            data = arr[ind - arr_start]
            send_arr = np.full(1, data)
            isend(send_arr, np.int32(1), root, tag, True)
        rank = bodo.libs.distributed_api.get_rank()
        val = np.zeros(1, qqd__dcum)[0]
        if rank == root:
            val = recv(qqd__dcum, ANY_SOURCE, tag)
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
    zda__bqtdm = get_type_enum(out_data)
    assert typ_enum == zda__bqtdm
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
    dxfra__rogyq = (
        'def f(send_data, out_data, send_counts, recv_counts, send_disp, recv_disp):\n'
        )
    for i in range(count):
        dxfra__rogyq += (
            """  alltoallv(send_data[{}], out_data[{}], send_counts, recv_counts, send_disp, recv_disp)
"""
            .format(i, i))
    dxfra__rogyq += '  return\n'
    seu__wwq = {}
    exec(dxfra__rogyq, {'alltoallv': alltoallv}, seu__wwq)
    qpky__vfzqa = seu__wwq['f']
    return qpky__vfzqa


@numba.njit
def get_start_count(n):
    rank = bodo.libs.distributed_api.get_rank()
    n_pes = bodo.libs.distributed_api.get_size()
    start = bodo.libs.distributed_api.get_start(n, n_pes, rank)
    count = bodo.libs.distributed_api.get_node_portion(n, n_pes, rank)
    return start, count


@numba.njit
def get_start(total_size, pes, rank):
    brxsb__vtceq = total_size % pes
    sazq__sdtnc = (total_size - brxsb__vtceq) // pes
    return rank * sazq__sdtnc + min(rank, brxsb__vtceq)


@numba.njit
def get_end(total_size, pes, rank):
    brxsb__vtceq = total_size % pes
    sazq__sdtnc = (total_size - brxsb__vtceq) // pes
    return (rank + 1) * sazq__sdtnc + min(rank + 1, brxsb__vtceq)


@numba.njit
def get_node_portion(total_size, pes, rank):
    brxsb__vtceq = total_size % pes
    sazq__sdtnc = (total_size - brxsb__vtceq) // pes
    if rank < brxsb__vtceq:
        return sazq__sdtnc + 1
    else:
        return sazq__sdtnc


@numba.generated_jit(nopython=True)
def dist_cumsum(in_arr, out_arr):
    lgnx__xstrg = in_arr.dtype(0)
    jumga__oown = np.int32(Reduce_Type.Sum.value)

    def cumsum_impl(in_arr, out_arr):
        ewto__ogiag = lgnx__xstrg
        for wsmnz__zti in np.nditer(in_arr):
            ewto__ogiag += wsmnz__zti.item()
        spwgo__hhkp = dist_exscan(ewto__ogiag, jumga__oown)
        for i in range(in_arr.size):
            spwgo__hhkp += in_arr[i]
            out_arr[i] = spwgo__hhkp
        return 0
    return cumsum_impl


@numba.generated_jit(nopython=True)
def dist_cumprod(in_arr, out_arr):
    homxy__gvnk = in_arr.dtype(1)
    jumga__oown = np.int32(Reduce_Type.Prod.value)

    def cumprod_impl(in_arr, out_arr):
        ewto__ogiag = homxy__gvnk
        for wsmnz__zti in np.nditer(in_arr):
            ewto__ogiag *= wsmnz__zti.item()
        spwgo__hhkp = dist_exscan(ewto__ogiag, jumga__oown)
        if get_rank() == 0:
            spwgo__hhkp = homxy__gvnk
        for i in range(in_arr.size):
            spwgo__hhkp *= in_arr[i]
            out_arr[i] = spwgo__hhkp
        return 0
    return cumprod_impl


@numba.generated_jit(nopython=True)
def dist_cummin(in_arr, out_arr):
    if isinstance(in_arr.dtype, types.Float):
        homxy__gvnk = np.finfo(in_arr.dtype(1).dtype).max
    else:
        homxy__gvnk = np.iinfo(in_arr.dtype(1).dtype).max
    jumga__oown = np.int32(Reduce_Type.Min.value)

    def cummin_impl(in_arr, out_arr):
        ewto__ogiag = homxy__gvnk
        for wsmnz__zti in np.nditer(in_arr):
            ewto__ogiag = min(ewto__ogiag, wsmnz__zti.item())
        spwgo__hhkp = dist_exscan(ewto__ogiag, jumga__oown)
        if get_rank() == 0:
            spwgo__hhkp = homxy__gvnk
        for i in range(in_arr.size):
            spwgo__hhkp = min(spwgo__hhkp, in_arr[i])
            out_arr[i] = spwgo__hhkp
        return 0
    return cummin_impl


@numba.generated_jit(nopython=True)
def dist_cummax(in_arr, out_arr):
    if isinstance(in_arr.dtype, types.Float):
        homxy__gvnk = np.finfo(in_arr.dtype(1).dtype).min
    else:
        homxy__gvnk = np.iinfo(in_arr.dtype(1).dtype).min
    homxy__gvnk = in_arr.dtype(1)
    jumga__oown = np.int32(Reduce_Type.Max.value)

    def cummax_impl(in_arr, out_arr):
        ewto__ogiag = homxy__gvnk
        for wsmnz__zti in np.nditer(in_arr):
            ewto__ogiag = max(ewto__ogiag, wsmnz__zti.item())
        spwgo__hhkp = dist_exscan(ewto__ogiag, jumga__oown)
        if get_rank() == 0:
            spwgo__hhkp = homxy__gvnk
        for i in range(in_arr.size):
            spwgo__hhkp = max(spwgo__hhkp, in_arr[i])
            out_arr[i] = spwgo__hhkp
        return 0
    return cummax_impl


_allgather = types.ExternalFunction('allgather', types.void(types.voidptr,
    types.int32, types.voidptr, types.int32))


@numba.njit
def allgather(arr, val):
    gqfn__yag = get_type_enum(arr)
    _allgather(arr.ctypes, 1, value_to_ptr(val), gqfn__yag)


def dist_return(A):
    return A


def rep_return(A):
    return A


def dist_return_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    upnhp__xglkf = args[0]
    if equiv_set.has_shape(upnhp__xglkf):
        return ArrayAnalysis.AnalyzeResult(shape=upnhp__xglkf, pre=[])
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
        vlak__prijv = ','.join(f'_wait(req[{i}], cond)' for i in range(count))
        dxfra__rogyq = 'def f(req, cond=True):\n'
        dxfra__rogyq += f'  return {vlak__prijv}\n'
        seu__wwq = {}
        exec(dxfra__rogyq, {'_wait': _wait}, seu__wwq)
        impl = seu__wwq['f']
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
    lpn__seirs = max(start, chunk_start)
    ehafk__ihdd = min(stop, chunk_start + chunk_count)
    upa__vluu = lpn__seirs - chunk_start
    pcmvy__fhnor = ehafk__ihdd - chunk_start
    if upa__vluu < 0 or pcmvy__fhnor < 0:
        upa__vluu = 1
        pcmvy__fhnor = 0
    return upa__vluu, pcmvy__fhnor


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
        brxsb__vtceq = 1
        for a in t:
            brxsb__vtceq *= a
        return brxsb__vtceq
    return get_tuple_prod_impl


sig = types.void(types.voidptr, types.voidptr, types.intp, types.intp,
    types.intp, types.intp, types.int32, types.voidptr)
oneD_reshape_shuffle = types.ExternalFunction('oneD_reshape_shuffle', sig)


@numba.njit(no_cpython_wrapper=True, cache=True)
def dist_oneD_reshape_shuffle(lhs, in_arr, new_dim0_global_len, dest_ranks=None
    ):
    gqwt__pfq = np.ascontiguousarray(in_arr)
    lhv__gaz = get_tuple_prod(gqwt__pfq.shape[1:])
    lchqo__efi = get_tuple_prod(lhs.shape[1:])
    if dest_ranks is not None:
        xwahi__pcoy = np.array(dest_ranks, dtype=np.int32)
    else:
        xwahi__pcoy = np.empty(0, dtype=np.int32)
    dtype_size = bodo.io.np_io.get_dtype_size(in_arr.dtype)
    oneD_reshape_shuffle(lhs.ctypes, gqwt__pfq.ctypes, new_dim0_global_len,
        len(in_arr), dtype_size * lchqo__efi, dtype_size * lhv__gaz, len(
        xwahi__pcoy), xwahi__pcoy.ctypes)
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
    htatz__gteqo = np.ascontiguousarray(rhs)
    cawr__lyntk = get_tuple_prod(htatz__gteqo.shape[1:])
    jcko__tqw = dtype_size * cawr__lyntk
    permutation_array_index(lhs.ctypes, lhs_len, jcko__tqw, htatz__gteqo.
        ctypes, htatz__gteqo.shape[0], p.ctypes, p_len)
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
        dxfra__rogyq = (
            f"""def bcast_scalar_impl(data, comm_ranks, nranks, root={MPI_ROOT}):
  send = np.empty(1, dtype)
  send[0] = data
  c_bcast(send.ctypes, np.int32(1), np.int32({{}}), comm_ranks,ctypes, np.int32({{}}), np.int32(root))
  return send[0]
"""
            .format(typ_val, nranks))
        dtype = numba.np.numpy_support.as_dtype(data)
        seu__wwq = {}
        exec(dxfra__rogyq, {'bodo': bodo, 'np': np, 'c_bcast': c_bcast,
            'dtype': dtype}, seu__wwq)
        qoh__gdxi = seu__wwq['bcast_scalar_impl']
        return qoh__gdxi
    if isinstance(data, types.Array):
        return lambda data, comm_ranks, nranks, root=MPI_ROOT: _bcast_np(data,
            comm_ranks, nranks, root)
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        ninkc__wptm = len(data.columns)
        gpk__kyo = ', '.join('g_data_{}'.format(i) for i in range(ninkc__wptm))
        kqh__nfa = bodo.utils.transform.gen_const_tup(data.columns)
        dxfra__rogyq = (
            f'def impl_df(data, comm_ranks, nranks, root={MPI_ROOT}):\n')
        for i in range(ninkc__wptm):
            dxfra__rogyq += (
                """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                .format(i, i))
            dxfra__rogyq += (
                """  g_data_{} = bodo.libs.distributed_api.bcast_comm_impl(data_{}, comm_ranks, nranks, root)
"""
                .format(i, i))
        dxfra__rogyq += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        dxfra__rogyq += """  g_index = bodo.libs.distributed_api.bcast_comm_impl(index, comm_ranks, nranks, root)
"""
        dxfra__rogyq += (
            """  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})
"""
            .format(gpk__kyo, kqh__nfa))
        seu__wwq = {}
        exec(dxfra__rogyq, {'bodo': bodo}, seu__wwq)
        tqbm__xmzcs = seu__wwq['impl_df']
        return tqbm__xmzcs
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):

        def impl_range_index(data, comm_ranks, nranks, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            start = data._start
            stop = data._stop
            siwtr__pmec = data._step
            isc__vftsg = data._name
            isc__vftsg = bcast_scalar(isc__vftsg, root)
            start = bcast_scalar(start, root)
            stop = bcast_scalar(stop, root)
            siwtr__pmec = bcast_scalar(siwtr__pmec, root)
            nwy__pcrlo = bodo.libs.array_kernels.calc_nitems(start, stop,
                siwtr__pmec)
            chunk_start = bodo.libs.distributed_api.get_start(nwy__pcrlo,
                n_pes, rank)
            chunk_count = bodo.libs.distributed_api.get_node_portion(nwy__pcrlo
                , n_pes, rank)
            lpn__seirs = start + siwtr__pmec * chunk_start
            ehafk__ihdd = start + siwtr__pmec * (chunk_start + chunk_count)
            ehafk__ihdd = min(ehafk__ihdd, stop)
            return bodo.hiframes.pd_index_ext.init_range_index(lpn__seirs,
                ehafk__ihdd, siwtr__pmec, isc__vftsg)
        return impl_range_index
    if bodo.hiframes.pd_index_ext.is_pd_index_type(data):

        def impl_pd_index(data, comm_ranks, nranks, root=MPI_ROOT):
            ennqf__tgg = data._data
            isc__vftsg = data._name
            arr = bodo.libs.distributed_api.bcast_comm_impl(ennqf__tgg,
                comm_ranks, nranks, root)
            return bodo.utils.conversion.index_from_array(arr, isc__vftsg)
        return impl_pd_index
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl_series(data, comm_ranks, nranks, root=MPI_ROOT):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            isc__vftsg = bodo.hiframes.pd_series_ext.get_series_name(data)
            ypr__kthrj = bodo.libs.distributed_api.bcast_comm_impl(isc__vftsg,
                comm_ranks, nranks, root)
            out_arr = bodo.libs.distributed_api.bcast_comm_impl(arr,
                comm_ranks, nranks, root)
            eau__oeco = bodo.libs.distributed_api.bcast_comm_impl(index,
                comm_ranks, nranks, root)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                eau__oeco, ypr__kthrj)
        return impl_series
    if isinstance(data, types.BaseTuple):
        dxfra__rogyq = (
            f'def impl_tuple(data, comm_ranks, nranks, root={MPI_ROOT}):\n')
        dxfra__rogyq += '  return ({}{})\n'.format(', '.join(
            'bcast_comm_impl(data[{}], comm_ranks, nranks, root)'.format(i) for
            i in range(len(data))), ',' if len(data) > 0 else '')
        seu__wwq = {}
        exec(dxfra__rogyq, {'bcast_comm_impl': bcast_comm_impl}, seu__wwq)
        anei__cot = seu__wwq['impl_tuple']
        return anei__cot
    if data is types.none:
        return lambda data, comm_ranks, nranks, root=MPI_ROOT: None


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _bcast_np(data, comm_ranks, nranks, root=MPI_ROOT):
    typ_val = numba_to_c_type(data.dtype)
    cfaob__aeyvs = data.ndim
    dtype = data.dtype
    if dtype == types.NPDatetime('ns'):
        dtype = np.dtype('datetime64[ns]')
    elif dtype == types.NPTimedelta('ns'):
        dtype = np.dtype('timedelta64[ns]')
    hpok__yskjp = (0,) * cfaob__aeyvs

    def bcast_arr_impl(data, comm_ranks, nranks, root=MPI_ROOT):
        rank = bodo.libs.distributed_api.get_rank()
        ennqf__tgg = np.ascontiguousarray(data)
        sqgs__rfdt = data.ctypes
        lwh__hpugr = hpok__yskjp
        if rank == root:
            lwh__hpugr = ennqf__tgg.shape
        lwh__hpugr = bcast_tuple(lwh__hpugr, root)
        qpe__zncgb = get_tuple_prod(lwh__hpugr[1:])
        send_counts = lwh__hpugr[0] * qpe__zncgb
        akdn__yeh = np.empty(send_counts, dtype)
        if rank == MPI_ROOT:
            c_bcast(sqgs__rfdt, np.int32(send_counts), np.int32(typ_val),
                comm_ranks.ctypes, np.int32(nranks), np.int32(root))
            return data
        else:
            c_bcast(akdn__yeh.ctypes, np.int32(send_counts), np.int32(
                typ_val), comm_ranks.ctypes, np.int32(nranks), np.int32(root))
            return akdn__yeh.reshape((-1,) + lwh__hpugr[1:])
    return bcast_arr_impl


node_ranks = None


def get_host_ranks():
    global node_ranks
    if node_ranks is None:
        vrfsc__otjzy = MPI.COMM_WORLD
        exljf__yzbi = MPI.Get_processor_name()
        dkuuz__itrf = vrfsc__otjzy.allgather(exljf__yzbi)
        node_ranks = defaultdict(list)
        for i, gjv__eqh in enumerate(dkuuz__itrf):
            node_ranks[gjv__eqh].append(i)
    return node_ranks


def create_subcomm_mpi4py(comm_ranks):
    vrfsc__otjzy = MPI.COMM_WORLD
    azd__sgz = vrfsc__otjzy.Get_group()
    nlrfa__slc = azd__sgz.Incl(comm_ranks)
    rtijf__nqtv = vrfsc__otjzy.Create_group(nlrfa__slc)
    return rtijf__nqtv


def get_nodes_first_ranks():
    sregx__cekc = get_host_ranks()
    return np.array([segri__kltsb[0] for segri__kltsb in sregx__cekc.values
        ()], dtype='int32')


def get_num_nodes():
    return len(get_host_ranks())
