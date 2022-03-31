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
    nxk__zucr = get_type_enum(send_arr)
    _send(send_arr.ctypes, 1, nxk__zucr, rank, tag)


_recv = types.ExternalFunction('c_recv', types.void(types.voidptr, types.
    int32, types.int32, types.int32, types.int32))


@numba.njit
def recv(dtype, rank, tag):
    recv_arr = np.empty(1, dtype)
    nxk__zucr = get_type_enum(recv_arr)
    _recv(recv_arr.ctypes, 1, nxk__zucr, rank, tag)
    return recv_arr[0]


_isend = types.ExternalFunction('dist_isend', mpi_req_numba_type(types.
    voidptr, types.int32, types.int32, types.int32, types.int32, types.bool_))


@numba.generated_jit(nopython=True)
def isend(arr, size, pe, tag, cond=True):
    if isinstance(arr, types.Array):

        def impl(arr, size, pe, tag, cond=True):
            nxk__zucr = get_type_enum(arr)
            return _isend(arr.ctypes, size, nxk__zucr, pe, tag, cond)
        return impl
    if isinstance(arr, (IntegerArrayType, DecimalArrayType)) or arr in (
        boolean_array, datetime_date_array_type):
        nxk__zucr = np.int32(numba_to_c_type(arr.dtype))
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))

        def impl_nullable(arr, size, pe, tag, cond=True):
            ste__afx = size + 7 >> 3
            mfwe__nkak = _isend(arr._data.ctypes, size, nxk__zucr, pe, tag,
                cond)
            ajhj__ohzdh = _isend(arr._null_bitmap.ctypes, ste__afx,
                ihebz__egxb, pe, tag, cond)
            return mfwe__nkak, ajhj__ohzdh
        return impl_nullable
    if is_str_arr_type(arr) or arr == binary_array_type:
        nahpf__qju = np.int32(numba_to_c_type(offset_type))
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))

        def impl_str_arr(arr, size, pe, tag, cond=True):
            arr = decode_if_dict_array(arr)
            kem__oozx = np.int64(bodo.libs.str_arr_ext.num_total_chars(arr))
            send(kem__oozx, pe, tag - 1)
            ste__afx = size + 7 >> 3
            _send(bodo.libs.str_arr_ext.get_offset_ptr(arr), size + 1,
                nahpf__qju, pe, tag)
            _send(bodo.libs.str_arr_ext.get_data_ptr(arr), kem__oozx,
                ihebz__egxb, pe, tag)
            _send(bodo.libs.str_arr_ext.get_null_bitmap_ptr(arr), ste__afx,
                ihebz__egxb, pe, tag)
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
            nxk__zucr = get_type_enum(arr)
            return _irecv(arr.ctypes, size, nxk__zucr, pe, tag, cond)
        return impl
    if isinstance(arr, (IntegerArrayType, DecimalArrayType)) or arr in (
        boolean_array, datetime_date_array_type):
        nxk__zucr = np.int32(numba_to_c_type(arr.dtype))
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))

        def impl_nullable(arr, size, pe, tag, cond=True):
            ste__afx = size + 7 >> 3
            mfwe__nkak = _irecv(arr._data.ctypes, size, nxk__zucr, pe, tag,
                cond)
            ajhj__ohzdh = _irecv(arr._null_bitmap.ctypes, ste__afx,
                ihebz__egxb, pe, tag, cond)
            return mfwe__nkak, ajhj__ohzdh
        return impl_nullable
    if arr in [binary_array_type, string_array_type]:
        nahpf__qju = np.int32(numba_to_c_type(offset_type))
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))
        if arr == binary_array_type:
            ury__pzc = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
        else:
            ury__pzc = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
        wdsqu__emilb = f"""def impl(arr, size, pe, tag, cond=True):
            # recv the number of string characters and resize buffer to proper size
            n_chars = bodo.libs.distributed_api.recv(np.int64, pe, tag - 1)
            new_arr = {ury__pzc}(size, n_chars)
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
        zfsd__hekn = dict()
        exec(wdsqu__emilb, {'bodo': bodo, 'np': np, 'offset_typ_enum':
            nahpf__qju, 'char_typ_enum': ihebz__egxb}, zfsd__hekn)
        impl = zfsd__hekn['impl']
        return impl
    raise BodoError(f'irecv(): array type {arr} not supported yet')


_alltoall = types.ExternalFunction('c_alltoall', types.void(types.voidptr,
    types.voidptr, types.int32, types.int32))


@numba.njit
def alltoall(send_arr, recv_arr, count):
    assert count < INT_MAX
    nxk__zucr = get_type_enum(send_arr)
    _alltoall(send_arr.ctypes, recv_arr.ctypes, np.int32(count), nxk__zucr)


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
        jbg__esz = n_pes if rank == root or allgather else 0
        qowz__mut = np.empty(jbg__esz, dtype)
        c_gather_scalar(send.ctypes, qowz__mut.ctypes, np.int32(typ_val),
            allgather, np.int32(root))
        return qowz__mut
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
        uxr__idqj = cgutils.alloca_once(builder, args[0].type)
        builder.store(args[0], uxr__idqj)
        return builder.bitcast(uxr__idqj, lir.IntType(8).as_pointer())
    return types.voidptr(val_tp), codegen


@intrinsic
def load_val_ptr(typingctx, ptr_tp, val_tp=None):

    def codegen(context, builder, sig, args):
        uxr__idqj = builder.bitcast(args[0], args[1].type.as_pointer())
        return builder.load(uxr__idqj)
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
    foap__iyfpq = types.unliteral(value)
    if isinstance(foap__iyfpq, IndexValueType):
        foap__iyfpq = foap__iyfpq.val_typ
        qyas__lsk = [types.bool_, types.uint8, types.int8, types.uint16,
            types.int16, types.uint32, types.int32, types.float32, types.
            float64]
        if not sys.platform.startswith('win'):
            qyas__lsk.append(types.int64)
            qyas__lsk.append(bodo.datetime64ns)
            qyas__lsk.append(bodo.timedelta64ns)
            qyas__lsk.append(bodo.datetime_date_type)
        if foap__iyfpq not in qyas__lsk:
            raise BodoError('argmin/argmax not supported for type {}'.
                format(foap__iyfpq))
    typ_enum = np.int32(numba_to_c_type(foap__iyfpq))

    def impl(value, reduce_op):
        dkdef__jqlsc = value_to_ptr(value)
        stg__zygxl = value_to_ptr(value)
        _dist_reduce(dkdef__jqlsc, stg__zygxl, reduce_op, typ_enum)
        return load_val_ptr(stg__zygxl, value)
    return impl


_dist_exscan = types.ExternalFunction('dist_exscan', types.void(types.
    voidptr, types.voidptr, types.int32, types.int32))


@numba.generated_jit(nopython=True)
def dist_exscan(value, reduce_op):
    foap__iyfpq = types.unliteral(value)
    typ_enum = np.int32(numba_to_c_type(foap__iyfpq))
    ygod__limrq = foap__iyfpq(0)

    def impl(value, reduce_op):
        dkdef__jqlsc = value_to_ptr(value)
        stg__zygxl = value_to_ptr(ygod__limrq)
        _dist_exscan(dkdef__jqlsc, stg__zygxl, reduce_op, typ_enum)
        return load_val_ptr(stg__zygxl, value)
    return impl


@numba.njit
def get_bit(bits, i):
    return bits[i >> 3] >> (i & 7) & 1


@numba.njit
def copy_gathered_null_bytes(null_bitmap_ptr, tmp_null_bytes,
    recv_counts_nulls, recv_counts):
    ttaz__qkj = 0
    iypdn__ynrxu = 0
    for i in range(len(recv_counts)):
        qouap__muzo = recv_counts[i]
        ste__afx = recv_counts_nulls[i]
        ezkb__xyymv = tmp_null_bytes[ttaz__qkj:ttaz__qkj + ste__afx]
        for zbc__okua in range(qouap__muzo):
            set_bit_to(null_bitmap_ptr, iypdn__ynrxu, get_bit(ezkb__xyymv,
                zbc__okua))
            iypdn__ynrxu += 1
        ttaz__qkj += ste__afx


@numba.generated_jit(nopython=True)
def gatherv(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
    from bodo.libs.csr_matrix_ext import CSRMatrixType
    bodo.hiframes.pd_dataframe_ext.check_runtime_cols_unsupported(data,
        'bodo.gatherv()')
    if isinstance(data, CategoricalArrayType):

        def impl_cat(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
            nca__swe = bodo.gatherv(data.codes, allgather, root=root)
            return bodo.hiframes.pd_categorical_ext.init_categorical_array(
                nca__swe, data.dtype)
        return impl_cat
    if isinstance(data, types.Array):
        typ_val = numba_to_c_type(data.dtype)

        def gatherv_impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            data = np.ascontiguousarray(data)
            rank = bodo.libs.distributed_api.get_rank()
            wgt__tmux = data.size
            recv_counts = gather_scalar(np.int32(wgt__tmux), allgather,
                root=root)
            wnez__jmakz = recv_counts.sum()
            nse__cjsh = empty_like_type(wnez__jmakz, data)
            ezyzv__iqv = np.empty(1, np.int32)
            if rank == root or allgather:
                ezyzv__iqv = bodo.ir.join.calc_disp(recv_counts)
            c_gatherv(data.ctypes, np.int32(wgt__tmux), nse__cjsh.ctypes,
                recv_counts.ctypes, ezyzv__iqv.ctypes, np.int32(typ_val),
                allgather, np.int32(root))
            return nse__cjsh.reshape((-1,) + data.shape[1:])
        return gatherv_impl
    if is_str_arr_type(data):

        def gatherv_str_arr_impl(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            data = decode_if_dict_array(data)
            nse__cjsh = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.str_arr_ext.init_str_arr(nse__cjsh)
        return gatherv_str_arr_impl
    if data == binary_array_type:

        def gatherv_binary_arr_impl(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            nse__cjsh = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.binary_arr_ext.init_binary_arr(nse__cjsh)
        return gatherv_binary_arr_impl
    if data == datetime_timedelta_array_type:
        typ_val = numba_to_c_type(types.int64)
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))

        def gatherv_impl_int_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            wgt__tmux = len(data)
            ste__afx = wgt__tmux + 7 >> 3
            recv_counts = gather_scalar(np.int32(wgt__tmux), allgather,
                root=root)
            wnez__jmakz = recv_counts.sum()
            nse__cjsh = empty_like_type(wnez__jmakz, data)
            ezyzv__iqv = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            gftqg__xku = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                ezyzv__iqv = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                gftqg__xku = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(data._days_data.ctypes, np.int32(wgt__tmux),
                nse__cjsh._days_data.ctypes, recv_counts.ctypes, ezyzv__iqv
                .ctypes, np.int32(typ_val), allgather, np.int32(root))
            c_gatherv(data._seconds_data.ctypes, np.int32(wgt__tmux),
                nse__cjsh._seconds_data.ctypes, recv_counts.ctypes,
                ezyzv__iqv.ctypes, np.int32(typ_val), allgather, np.int32(root)
                )
            c_gatherv(data._microseconds_data.ctypes, np.int32(wgt__tmux),
                nse__cjsh._microseconds_data.ctypes, recv_counts.ctypes,
                ezyzv__iqv.ctypes, np.int32(typ_val), allgather, np.int32(root)
                )
            c_gatherv(data._null_bitmap.ctypes, np.int32(ste__afx),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, gftqg__xku
                .ctypes, ihebz__egxb, allgather, np.int32(root))
            copy_gathered_null_bytes(nse__cjsh._null_bitmap.ctypes,
                tmp_null_bytes, recv_counts_nulls, recv_counts)
            return nse__cjsh
        return gatherv_impl_int_arr
    if isinstance(data, (IntegerArrayType, DecimalArrayType)) or data in (
        boolean_array, datetime_date_array_type):
        typ_val = numba_to_c_type(data.dtype)
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))

        def gatherv_impl_int_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            wgt__tmux = len(data)
            ste__afx = wgt__tmux + 7 >> 3
            recv_counts = gather_scalar(np.int32(wgt__tmux), allgather,
                root=root)
            wnez__jmakz = recv_counts.sum()
            nse__cjsh = empty_like_type(wnez__jmakz, data)
            ezyzv__iqv = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            gftqg__xku = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                ezyzv__iqv = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                gftqg__xku = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(data._data.ctypes, np.int32(wgt__tmux), nse__cjsh.
                _data.ctypes, recv_counts.ctypes, ezyzv__iqv.ctypes, np.
                int32(typ_val), allgather, np.int32(root))
            c_gatherv(data._null_bitmap.ctypes, np.int32(ste__afx),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, gftqg__xku
                .ctypes, ihebz__egxb, allgather, np.int32(root))
            copy_gathered_null_bytes(nse__cjsh._null_bitmap.ctypes,
                tmp_null_bytes, recv_counts_nulls, recv_counts)
            return nse__cjsh
        return gatherv_impl_int_arr
    if isinstance(data, DatetimeArrayType):
        mdz__cuw = data.tz

        def impl_pd_datetime_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            vrr__dknnh = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.pd_datetime_arr_ext.init_pandas_datetime_array(
                vrr__dknnh, mdz__cuw)
        return impl_pd_datetime_arr
    if isinstance(data, IntervalArrayType):

        def impl_interval_arr(data, allgather=False, warn_if_rep=True, root
            =MPI_ROOT):
            zyeo__sdrbt = bodo.gatherv(data._left, allgather, warn_if_rep, root
                )
            tank__gsju = bodo.gatherv(data._right, allgather, warn_if_rep, root
                )
            return bodo.libs.interval_arr_ext.init_interval_array(zyeo__sdrbt,
                tank__gsju)
        return impl_interval_arr
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            cytf__jfm = bodo.hiframes.pd_series_ext.get_series_name(data)
            out_arr = bodo.libs.distributed_api.gatherv(arr, allgather,
                warn_if_rep, root)
            shiep__hdo = bodo.gatherv(index, allgather, warn_if_rep, root)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                shiep__hdo, cytf__jfm)
        return impl
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):
        urei__sfe = np.iinfo(np.int64).max
        emotc__aqlbb = np.iinfo(np.int64).min

        def impl_range_index(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            start = data._start
            stop = data._stop
            if len(data) == 0:
                start = urei__sfe
                stop = emotc__aqlbb
            start = bodo.libs.distributed_api.dist_reduce(start, np.int32(
                Reduce_Type.Min.value))
            stop = bodo.libs.distributed_api.dist_reduce(stop, np.int32(
                Reduce_Type.Max.value))
            total_len = bodo.libs.distributed_api.dist_reduce(len(data), np
                .int32(Reduce_Type.Sum.value))
            if start == urei__sfe and stop == emotc__aqlbb:
                start = 0
                stop = 0
            ixns__yvknz = max(0, -(-(stop - start) // data._step))
            if ixns__yvknz < total_len:
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
            awp__exvyy = data.freq

            def impl_pd_index(data, allgather=False, warn_if_rep=True, root
                =MPI_ROOT):
                arr = bodo.libs.distributed_api.gatherv(data._data,
                    allgather, root=root)
                return bodo.hiframes.pd_index_ext.init_period_index(arr,
                    data._name, awp__exvyy)
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
            nse__cjsh = bodo.gatherv(data._data, allgather, root=root)
            return bodo.hiframes.pd_multi_index_ext.init_multi_index(nse__cjsh,
                data._names, data._name)
        return impl_multi_index
    if isinstance(data, bodo.hiframes.table.TableType):
        rsmye__phwy = {'bodo': bodo, 'get_table_block': bodo.hiframes.table
            .get_table_block, 'ensure_column_unboxed': bodo.hiframes.table.
            ensure_column_unboxed, 'set_table_block': bodo.hiframes.table.
            set_table_block, 'set_table_len': bodo.hiframes.table.
            set_table_len, 'alloc_list_like': bodo.hiframes.table.
            alloc_list_like, 'init_table': bodo.hiframes.table.init_table}
        wdsqu__emilb = f"""def impl_table(data, allgather=False, warn_if_rep=True, root={MPI_ROOT}):
"""
        wdsqu__emilb += '  T = data\n'
        wdsqu__emilb += '  T2 = init_table(T, True)\n'
        for urbj__vzs in data.type_to_blk.values():
            rsmye__phwy[f'arr_inds_{urbj__vzs}'] = np.array(data.
                block_to_arr_ind[urbj__vzs], dtype=np.int64)
            wdsqu__emilb += (
                f'  arr_list_{urbj__vzs} = get_table_block(T, {urbj__vzs})\n')
            wdsqu__emilb += f"""  out_arr_list_{urbj__vzs} = alloc_list_like(arr_list_{urbj__vzs}, True)
"""
            wdsqu__emilb += f'  for i in range(len(arr_list_{urbj__vzs})):\n'
            wdsqu__emilb += (
                f'    arr_ind_{urbj__vzs} = arr_inds_{urbj__vzs}[i]\n')
            wdsqu__emilb += f"""    ensure_column_unboxed(T, arr_list_{urbj__vzs}, i, arr_ind_{urbj__vzs})
"""
            wdsqu__emilb += f"""    out_arr_{urbj__vzs} = bodo.gatherv(arr_list_{urbj__vzs}[i], allgather, warn_if_rep, root)
"""
            wdsqu__emilb += (
                f'    out_arr_list_{urbj__vzs}[i] = out_arr_{urbj__vzs}\n')
            wdsqu__emilb += (
                f'  T2 = set_table_block(T2, out_arr_list_{urbj__vzs}, {urbj__vzs})\n'
                )
        wdsqu__emilb += (
            f'  length = T._len if bodo.get_rank() == root or allgather else 0\n'
            )
        wdsqu__emilb += f'  T2 = set_table_len(T2, length)\n'
        wdsqu__emilb += f'  return T2\n'
        zfsd__hekn = {}
        exec(wdsqu__emilb, rsmye__phwy, zfsd__hekn)
        yno__zodao = zfsd__hekn['impl_table']
        return yno__zodao
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        ccwx__fkyf = len(data.columns)
        if ccwx__fkyf == 0:

            def impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
                index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data
                    )
                fzgg__dyfl = bodo.gatherv(index, allgather, warn_if_rep, root)
                return bodo.hiframes.pd_dataframe_ext.init_dataframe((),
                    fzgg__dyfl, ())
            return impl
        tjypp__mfz = ', '.join(f'g_data_{i}' for i in range(ccwx__fkyf))
        alrg__vqfvj = bodo.utils.transform.gen_const_tup(data.columns)
        wdsqu__emilb = (
            'def impl_df(data, allgather=False, warn_if_rep=True, root={}):\n'
            .format(MPI_ROOT))
        if data.is_table_format:
            from bodo.transforms.distributed_analysis import Distribution
            mhj__scqrj = bodo.hiframes.pd_dataframe_ext.DataFrameType(data.
                data, data.index, data.columns, Distribution.REP, True)
            rsmye__phwy = {'bodo': bodo, 'df_type': mhj__scqrj}
            tjypp__mfz = 'T2'
            alrg__vqfvj = 'df_type'
            wdsqu__emilb += (
                '  T = bodo.hiframes.pd_dataframe_ext.get_dataframe_table(data)\n'
                )
            wdsqu__emilb += (
                '  T2 = bodo.gatherv(T, allgather, warn_if_rep, root)\n')
        else:
            rsmye__phwy = {'bodo': bodo}
            for i in range(ccwx__fkyf):
                wdsqu__emilb += (
                    """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                    .format(i, i))
                wdsqu__emilb += (
                    """  g_data_{} = bodo.gatherv(data_{}, allgather, warn_if_rep, root)
"""
                    .format(i, i))
        wdsqu__emilb += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        wdsqu__emilb += (
            '  g_index = bodo.gatherv(index, allgather, warn_if_rep, root)\n')
        wdsqu__emilb += (
            """  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})
"""
            .format(tjypp__mfz, alrg__vqfvj))
        zfsd__hekn = {}
        exec(wdsqu__emilb, rsmye__phwy, zfsd__hekn)
        eqad__hkl = zfsd__hekn['impl_df']
        return eqad__hkl
    if isinstance(data, ArrayItemArrayType):
        xqvvx__arcx = np.int32(numba_to_c_type(types.int32))
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))

        def gatherv_array_item_arr_impl(data, allgather=False, warn_if_rep=
            True, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            qeo__azdft = bodo.libs.array_item_arr_ext.get_offsets(data)
            kopop__zzrrt = bodo.libs.array_item_arr_ext.get_data(data)
            kopop__zzrrt = kopop__zzrrt[:qeo__azdft[-1]]
            qtp__abk = bodo.libs.array_item_arr_ext.get_null_bitmap(data)
            wgt__tmux = len(data)
            tjv__mfoql = np.empty(wgt__tmux, np.uint32)
            ste__afx = wgt__tmux + 7 >> 3
            for i in range(wgt__tmux):
                tjv__mfoql[i] = qeo__azdft[i + 1] - qeo__azdft[i]
            recv_counts = gather_scalar(np.int32(wgt__tmux), allgather,
                root=root)
            wnez__jmakz = recv_counts.sum()
            ezyzv__iqv = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            gftqg__xku = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                ezyzv__iqv = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for wxl__chkj in range(len(recv_counts)):
                    recv_counts_nulls[wxl__chkj] = recv_counts[wxl__chkj
                        ] + 7 >> 3
                gftqg__xku = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            kuji__toxu = np.empty(wnez__jmakz + 1, np.uint32)
            rpt__mas = bodo.gatherv(kopop__zzrrt, allgather, warn_if_rep, root)
            fac__eozq = np.empty(wnez__jmakz + 7 >> 3, np.uint8)
            c_gatherv(tjv__mfoql.ctypes, np.int32(wgt__tmux), kuji__toxu.
                ctypes, recv_counts.ctypes, ezyzv__iqv.ctypes, xqvvx__arcx,
                allgather, np.int32(root))
            c_gatherv(qtp__abk.ctypes, np.int32(ste__afx), tmp_null_bytes.
                ctypes, recv_counts_nulls.ctypes, gftqg__xku.ctypes,
                ihebz__egxb, allgather, np.int32(root))
            dummy_use(data)
            zlqu__jxvcn = np.empty(wnez__jmakz + 1, np.uint64)
            convert_len_arr_to_offset(kuji__toxu.ctypes, zlqu__jxvcn.ctypes,
                wnez__jmakz)
            copy_gathered_null_bytes(fac__eozq.ctypes, tmp_null_bytes,
                recv_counts_nulls, recv_counts)
            out_arr = bodo.libs.array_item_arr_ext.init_array_item_array(
                wnez__jmakz, rpt__mas, zlqu__jxvcn, fac__eozq)
            return out_arr
        return gatherv_array_item_arr_impl
    if isinstance(data, StructArrayType):
        omkb__uhc = data.names
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))

        def impl_struct_arr(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            rceh__lxla = bodo.libs.struct_arr_ext.get_data(data)
            tge__zib = bodo.libs.struct_arr_ext.get_null_bitmap(data)
            nwfj__dcpd = bodo.gatherv(rceh__lxla, allgather=allgather, root
                =root)
            rank = bodo.libs.distributed_api.get_rank()
            wgt__tmux = len(data)
            ste__afx = wgt__tmux + 7 >> 3
            recv_counts = gather_scalar(np.int32(wgt__tmux), allgather,
                root=root)
            wnez__jmakz = recv_counts.sum()
            kswpn__jobm = np.empty(wnez__jmakz + 7 >> 3, np.uint8)
            recv_counts_nulls = np.empty(1, np.int32)
            gftqg__xku = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                gftqg__xku = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(tge__zib.ctypes, np.int32(ste__afx), tmp_null_bytes.
                ctypes, recv_counts_nulls.ctypes, gftqg__xku.ctypes,
                ihebz__egxb, allgather, np.int32(root))
            copy_gathered_null_bytes(kswpn__jobm.ctypes, tmp_null_bytes,
                recv_counts_nulls, recv_counts)
            return bodo.libs.struct_arr_ext.init_struct_arr(nwfj__dcpd,
                kswpn__jobm, omkb__uhc)
        return impl_struct_arr
    if data == binary_array_type:

        def impl_bin_arr(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            nse__cjsh = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.binary_arr_ext.init_binary_arr(nse__cjsh)
        return impl_bin_arr
    if isinstance(data, TupleArrayType):

        def impl_tuple_arr(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            nse__cjsh = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.tuple_arr_ext.init_tuple_arr(nse__cjsh)
        return impl_tuple_arr
    if isinstance(data, MapArrayType):

        def impl_map_arr(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            nse__cjsh = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.map_arr_ext.init_map_arr(nse__cjsh)
        return impl_map_arr
    if isinstance(data, CSRMatrixType):

        def impl_csr_matrix(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            nse__cjsh = bodo.gatherv(data.data, allgather, warn_if_rep, root)
            iyt__syyqc = bodo.gatherv(data.indices, allgather, warn_if_rep,
                root)
            uncmt__ixgp = bodo.gatherv(data.indptr, allgather, warn_if_rep,
                root)
            ibxo__mxt = gather_scalar(data.shape[0], allgather, root=root)
            sxo__hcmy = ibxo__mxt.sum()
            ccwx__fkyf = bodo.libs.distributed_api.dist_reduce(data.shape[1
                ], np.int32(Reduce_Type.Max.value))
            wtgr__sfsso = np.empty(sxo__hcmy + 1, np.int64)
            iyt__syyqc = iyt__syyqc.astype(np.int64)
            wtgr__sfsso[0] = 0
            kyxb__iqv = 1
            dkj__vxtf = 0
            for cuqp__mtl in ibxo__mxt:
                for frhv__txyro in range(cuqp__mtl):
                    fif__bqu = uncmt__ixgp[dkj__vxtf + 1] - uncmt__ixgp[
                        dkj__vxtf]
                    wtgr__sfsso[kyxb__iqv] = wtgr__sfsso[kyxb__iqv - 1
                        ] + fif__bqu
                    kyxb__iqv += 1
                    dkj__vxtf += 1
                dkj__vxtf += 1
            return bodo.libs.csr_matrix_ext.init_csr_matrix(nse__cjsh,
                iyt__syyqc, wtgr__sfsso, (sxo__hcmy, ccwx__fkyf))
        return impl_csr_matrix
    if isinstance(data, types.BaseTuple):
        wdsqu__emilb = (
            'def impl_tuple(data, allgather=False, warn_if_rep=True, root={}):\n'
            .format(MPI_ROOT))
        wdsqu__emilb += '  return ({}{})\n'.format(', '.join(
            'bodo.gatherv(data[{}], allgather, warn_if_rep, root)'.format(i
            ) for i in range(len(data))), ',' if len(data) > 0 else '')
        zfsd__hekn = {}
        exec(wdsqu__emilb, {'bodo': bodo}, zfsd__hekn)
        ehx__hpjd = zfsd__hekn['impl_tuple']
        return ehx__hpjd
    if data is types.none:
        return (lambda data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT: None)
    raise BodoError('gatherv() not available for {}'.format(data))


@numba.generated_jit(nopython=True)
def rebalance(data, dests=None, random=False, random_seed=None, parallel=False
    ):
    bodo.hiframes.pd_dataframe_ext.check_runtime_cols_unsupported(data,
        'bodo.rebalance()')
    wdsqu__emilb = (
        'def impl(data, dests=None, random=False, random_seed=None, parallel=False):\n'
        )
    wdsqu__emilb += '    if random:\n'
    wdsqu__emilb += '        if random_seed is None:\n'
    wdsqu__emilb += '            random = 1\n'
    wdsqu__emilb += '        else:\n'
    wdsqu__emilb += '            random = 2\n'
    wdsqu__emilb += '    if random_seed is None:\n'
    wdsqu__emilb += '        random_seed = -1\n'
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        tpuqr__wcun = data
        ccwx__fkyf = len(tpuqr__wcun.columns)
        for i in range(ccwx__fkyf):
            wdsqu__emilb += f"""    data_{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {i})
"""
        wdsqu__emilb += """    ind_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data))
"""
        tjypp__mfz = ', '.join(f'data_{i}' for i in range(ccwx__fkyf))
        wdsqu__emilb += ('    info_list_total = [{}, array_to_info(ind_arr)]\n'
            .format(', '.join('array_to_info(data_{})'.format(aqpa__wbw) for
            aqpa__wbw in range(ccwx__fkyf))))
        wdsqu__emilb += (
            '    table_total = arr_info_list_to_table(info_list_total)\n')
        wdsqu__emilb += '    if dests is None:\n'
        wdsqu__emilb += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        wdsqu__emilb += '    else:\n'
        wdsqu__emilb += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        for ivvhk__zev in range(ccwx__fkyf):
            wdsqu__emilb += (
                """    out_arr_{0} = info_to_array(info_from_table(out_table, {0}), data_{0})
"""
                .format(ivvhk__zev))
        wdsqu__emilb += (
            """    out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)
"""
            .format(ccwx__fkyf))
        wdsqu__emilb += '    delete_table(out_table)\n'
        wdsqu__emilb += '    if parallel:\n'
        wdsqu__emilb += '        delete_table(table_total)\n'
        tjypp__mfz = ', '.join('out_arr_{}'.format(i) for i in range(
            ccwx__fkyf))
        alrg__vqfvj = bodo.utils.transform.gen_const_tup(tpuqr__wcun.columns)
        index = 'bodo.utils.conversion.index_from_array(out_arr_index)'
        wdsqu__emilb += (
            '    return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), {}, {})\n'
            .format(tjypp__mfz, index, alrg__vqfvj))
    elif isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):
        wdsqu__emilb += (
            '    data_0 = bodo.hiframes.pd_series_ext.get_series_data(data)\n')
        wdsqu__emilb += """    ind_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(data))
"""
        wdsqu__emilb += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(data)\n')
        wdsqu__emilb += """    table_total = arr_info_list_to_table([array_to_info(data_0), array_to_info(ind_arr)])
"""
        wdsqu__emilb += '    if dests is None:\n'
        wdsqu__emilb += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        wdsqu__emilb += '    else:\n'
        wdsqu__emilb += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        wdsqu__emilb += (
            '    out_arr_0 = info_to_array(info_from_table(out_table, 0), data_0)\n'
            )
        wdsqu__emilb += """    out_arr_index = info_to_array(info_from_table(out_table, 1), ind_arr)
"""
        wdsqu__emilb += '    delete_table(out_table)\n'
        wdsqu__emilb += '    if parallel:\n'
        wdsqu__emilb += '        delete_table(table_total)\n'
        index = 'bodo.utils.conversion.index_from_array(out_arr_index)'
        wdsqu__emilb += f"""    return bodo.hiframes.pd_series_ext.init_series(out_arr_0, {index}, name)
"""
    elif isinstance(data, types.Array):
        assert is_overload_false(random
            ), 'Call random_shuffle instead of rebalance'
        wdsqu__emilb += '    if not parallel:\n'
        wdsqu__emilb += '        return data\n'
        wdsqu__emilb += """    dim0_global_size = bodo.libs.distributed_api.dist_reduce(data.shape[0], np.int32(bodo.libs.distributed_api.Reduce_Type.Sum.value))
"""
        wdsqu__emilb += '    if dests is None:\n'
        wdsqu__emilb += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, bodo.get_size(), bodo.get_rank())
"""
        wdsqu__emilb += '    elif bodo.get_rank() not in dests:\n'
        wdsqu__emilb += '        dim0_local_size = 0\n'
        wdsqu__emilb += '    else:\n'
        wdsqu__emilb += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, len(dests), dests.index(bodo.get_rank()))
"""
        wdsqu__emilb += """    out = np.empty((dim0_local_size,) + tuple(data.shape[1:]), dtype=data.dtype)
"""
        wdsqu__emilb += """    bodo.libs.distributed_api.dist_oneD_reshape_shuffle(out, data, dim0_global_size, dests)
"""
        wdsqu__emilb += '    return out\n'
    elif bodo.utils.utils.is_array_typ(data, False):
        wdsqu__emilb += (
            '    table_total = arr_info_list_to_table([array_to_info(data)])\n'
            )
        wdsqu__emilb += '    if dests is None:\n'
        wdsqu__emilb += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        wdsqu__emilb += '    else:\n'
        wdsqu__emilb += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        wdsqu__emilb += (
            '    out_arr = info_to_array(info_from_table(out_table, 0), data)\n'
            )
        wdsqu__emilb += '    delete_table(out_table)\n'
        wdsqu__emilb += '    if parallel:\n'
        wdsqu__emilb += '        delete_table(table_total)\n'
        wdsqu__emilb += '    return out_arr\n'
    else:
        raise BodoError(f'Type {data} not supported for bodo.rebalance')
    zfsd__hekn = {}
    exec(wdsqu__emilb, {'np': np, 'bodo': bodo, 'array_to_info': bodo.libs.
        array.array_to_info, 'shuffle_renormalization': bodo.libs.array.
        shuffle_renormalization, 'shuffle_renormalization_group': bodo.libs
        .array.shuffle_renormalization_group, 'arr_info_list_to_table':
        bodo.libs.array.arr_info_list_to_table, 'info_from_table': bodo.
        libs.array.info_from_table, 'info_to_array': bodo.libs.array.
        info_to_array, 'delete_table': bodo.libs.array.delete_table},
        zfsd__hekn)
    impl = zfsd__hekn['impl']
    return impl


@numba.generated_jit(nopython=True)
def random_shuffle(data, seed=None, dests=None, parallel=False):
    wdsqu__emilb = 'def impl(data, seed=None, dests=None, parallel=False):\n'
    if isinstance(data, types.Array):
        if not is_overload_none(dests):
            raise BodoError('not supported')
        wdsqu__emilb += '    if seed is None:\n'
        wdsqu__emilb += """        seed = bodo.libs.distributed_api.bcast_scalar(np.random.randint(0, 2**31))
"""
        wdsqu__emilb += '    np.random.seed(seed)\n'
        wdsqu__emilb += '    if not parallel:\n'
        wdsqu__emilb += '        data = data.copy()\n'
        wdsqu__emilb += '        np.random.shuffle(data)\n'
        wdsqu__emilb += '        return data\n'
        wdsqu__emilb += '    else:\n'
        wdsqu__emilb += """        dim0_global_size = bodo.libs.distributed_api.dist_reduce(data.shape[0], np.int32(bodo.libs.distributed_api.Reduce_Type.Sum.value))
"""
        wdsqu__emilb += '        permutation = np.arange(dim0_global_size)\n'
        wdsqu__emilb += '        np.random.shuffle(permutation)\n'
        wdsqu__emilb += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, bodo.get_size(), bodo.get_rank())
"""
        wdsqu__emilb += """        output = np.empty((dim0_local_size,) + tuple(data.shape[1:]), dtype=data.dtype)
"""
        wdsqu__emilb += (
            '        dtype_size = bodo.io.np_io.get_dtype_size(data.dtype)\n')
        wdsqu__emilb += """        bodo.libs.distributed_api.dist_permutation_array_index(output, dim0_global_size, dtype_size, data, permutation, len(permutation))
"""
        wdsqu__emilb += '        return output\n'
    else:
        wdsqu__emilb += """    return bodo.libs.distributed_api.rebalance(data, dests=dests, random=True, random_seed=seed, parallel=parallel)
"""
    zfsd__hekn = {}
    exec(wdsqu__emilb, {'np': np, 'bodo': bodo}, zfsd__hekn)
    impl = zfsd__hekn['impl']
    return impl


@numba.generated_jit(nopython=True)
def allgatherv(data, warn_if_rep=True, root=MPI_ROOT):
    return lambda data, warn_if_rep=True, root=MPI_ROOT: gatherv(data, True,
        warn_if_rep, root)


@numba.njit
def get_scatter_null_bytes_buff(null_bitmap_ptr, sendcounts, sendcounts_nulls):
    if bodo.get_rank() != MPI_ROOT:
        return np.empty(1, np.uint8)
    cmo__yazzu = np.empty(sendcounts_nulls.sum(), np.uint8)
    ttaz__qkj = 0
    iypdn__ynrxu = 0
    for fisd__ccrio in range(len(sendcounts)):
        qouap__muzo = sendcounts[fisd__ccrio]
        ste__afx = sendcounts_nulls[fisd__ccrio]
        ezkb__xyymv = cmo__yazzu[ttaz__qkj:ttaz__qkj + ste__afx]
        for zbc__okua in range(qouap__muzo):
            set_bit_to_arr(ezkb__xyymv, zbc__okua, get_bit_bitmap(
                null_bitmap_ptr, iypdn__ynrxu))
            iypdn__ynrxu += 1
        ttaz__qkj += ste__afx
    return cmo__yazzu


def _bcast_dtype(data, root=MPI_ROOT):
    try:
        from mpi4py import MPI
    except:
        raise BodoError('mpi4py is required for scatterv')
    muxaw__mhd = MPI.COMM_WORLD
    data = muxaw__mhd.bcast(data, root)
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
    jyur__nua = data.ndim
    dtype = data.dtype
    if dtype == types.NPDatetime('ns'):
        dtype = np.dtype('datetime64[ns]')
    elif dtype == types.NPTimedelta('ns'):
        dtype = np.dtype('timedelta64[ns]')
    yqioe__nif = (0,) * jyur__nua

    def scatterv_arr_impl(data, send_counts=None, warn_if_dist=True):
        rank = bodo.libs.distributed_api.get_rank()
        n_pes = bodo.libs.distributed_api.get_size()
        jor__ycymc = np.ascontiguousarray(data)
        ccuc__merhb = data.ctypes
        eyxzd__vnfc = yqioe__nif
        if rank == MPI_ROOT:
            eyxzd__vnfc = jor__ycymc.shape
        eyxzd__vnfc = bcast_tuple(eyxzd__vnfc)
        fwv__xgs = get_tuple_prod(eyxzd__vnfc[1:])
        send_counts = _get_scatterv_send_counts(send_counts, n_pes,
            eyxzd__vnfc[0])
        send_counts *= fwv__xgs
        wgt__tmux = send_counts[rank]
        ifjl__ulck = np.empty(wgt__tmux, dtype)
        ezyzv__iqv = bodo.ir.join.calc_disp(send_counts)
        c_scatterv(ccuc__merhb, send_counts.ctypes, ezyzv__iqv.ctypes,
            ifjl__ulck.ctypes, np.int32(wgt__tmux), np.int32(typ_val))
        return ifjl__ulck.reshape((-1,) + eyxzd__vnfc[1:])
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
        oahlx__ceqbv = '{}Int{}'.format('' if dtype.dtype.signed else 'U',
            dtype.dtype.bitwidth)
        return pd.array([3], oahlx__ceqbv)
    if dtype == boolean_array:
        return pd.array([True], 'boolean')
    if isinstance(dtype, DecimalArrayType):
        return np.array([Decimal('32.1')])
    if dtype == datetime_date_array_type:
        return np.array([datetime.date(2011, 8, 9)])
    if dtype == datetime_timedelta_array_type:
        return np.array([datetime.timedelta(33)])
    if bodo.hiframes.pd_index_ext.is_pd_index_type(dtype):
        cytf__jfm = _get_name_value_for_type(dtype.name_typ)
        if isinstance(dtype, bodo.hiframes.pd_index_ext.RangeIndexType):
            return pd.RangeIndex(1, name=cytf__jfm)
        rjpf__hlni = bodo.utils.typing.get_index_data_arr_types(dtype)[0]
        arr = get_value_for_type(rjpf__hlni)
        return pd.Index(arr, name=cytf__jfm)
    if isinstance(dtype, bodo.hiframes.pd_multi_index_ext.MultiIndexType):
        import pyarrow as pa
        cytf__jfm = _get_name_value_for_type(dtype.name_typ)
        omkb__uhc = tuple(_get_name_value_for_type(t) for t in dtype.names_typ)
        stnzl__vnmym = tuple(get_value_for_type(t) for t in dtype.array_types)
        stnzl__vnmym = tuple(a.to_numpy(False) if isinstance(a, pa.Array) else
            a for a in stnzl__vnmym)
        val = pd.MultiIndex.from_arrays(stnzl__vnmym, names=omkb__uhc)
        val.name = cytf__jfm
        return val
    if isinstance(dtype, bodo.hiframes.pd_series_ext.SeriesType):
        cytf__jfm = _get_name_value_for_type(dtype.name_typ)
        arr = get_value_for_type(dtype.data)
        index = get_value_for_type(dtype.index)
        return pd.Series(arr, index, name=cytf__jfm)
    if isinstance(dtype, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        stnzl__vnmym = tuple(get_value_for_type(t) for t in dtype.data)
        index = get_value_for_type(dtype.index)
        return pd.DataFrame({cytf__jfm: arr for cytf__jfm, arr in zip(dtype
            .columns, stnzl__vnmym)}, index)
    if isinstance(dtype, CategoricalArrayType):
        return pd.Categorical.from_codes([0], dtype.dtype.categories)
    if isinstance(dtype, types.BaseTuple):
        return tuple(get_value_for_type(t) for t in dtype.types)
    if isinstance(dtype, ArrayItemArrayType):
        return pd.Series([get_value_for_type(dtype.dtype),
            get_value_for_type(dtype.dtype)]).values
    if isinstance(dtype, IntervalArrayType):
        rjpf__hlni = get_value_for_type(dtype.arr_type)
        return pd.arrays.IntervalArray([pd.Interval(rjpf__hlni[0],
            rjpf__hlni[0])])
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
        xqvvx__arcx = np.int32(numba_to_c_type(types.int32))
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))
        if data == binary_array_type:
            ury__pzc = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
        else:
            ury__pzc = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
        wdsqu__emilb = f"""def impl(
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
            recv_arr = {ury__pzc}(n_loc, n_loc_char)

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
        zfsd__hekn = dict()
        exec(wdsqu__emilb, {'bodo': bodo, 'np': np, 'int32_typ_enum':
            xqvvx__arcx, 'char_typ_enum': ihebz__egxb,
            'decode_if_dict_array': decode_if_dict_array}, zfsd__hekn)
        impl = zfsd__hekn['impl']
        return impl
    if isinstance(data, ArrayItemArrayType):
        xqvvx__arcx = np.int32(numba_to_c_type(types.int32))
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))

        def scatterv_array_item_impl(data, send_counts=None, warn_if_dist=True
            ):
            ins__hmito = bodo.libs.array_item_arr_ext.get_offsets(data)
            kck__ety = bodo.libs.array_item_arr_ext.get_data(data)
            kck__ety = kck__ety[:ins__hmito[-1]]
            oujde__ympe = bodo.libs.array_item_arr_ext.get_null_bitmap(data)
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            hdv__nkvpv = bcast_scalar(len(data))
            dvbjt__wbelf = np.empty(len(data), np.uint32)
            for i in range(len(data)):
                dvbjt__wbelf[i] = ins__hmito[i + 1] - ins__hmito[i]
            send_counts = _get_scatterv_send_counts(send_counts, n_pes,
                hdv__nkvpv)
            ezyzv__iqv = bodo.ir.join.calc_disp(send_counts)
            rlpby__xfb = np.empty(n_pes, np.int32)
            if rank == 0:
                qooq__esyu = 0
                for i in range(n_pes):
                    ansxv__ripv = 0
                    for frhv__txyro in range(send_counts[i]):
                        ansxv__ripv += dvbjt__wbelf[qooq__esyu]
                        qooq__esyu += 1
                    rlpby__xfb[i] = ansxv__ripv
            bcast(rlpby__xfb)
            enuc__srkpi = np.empty(n_pes, np.int32)
            for i in range(n_pes):
                enuc__srkpi[i] = send_counts[i] + 7 >> 3
            gftqg__xku = bodo.ir.join.calc_disp(enuc__srkpi)
            wgt__tmux = send_counts[rank]
            oaoq__xyqus = np.empty(wgt__tmux + 1, np_offset_type)
            ont__mpdb = bodo.libs.distributed_api.scatterv_impl(kck__ety,
                rlpby__xfb)
            mzez__cgvdj = wgt__tmux + 7 >> 3
            zvrrv__oxju = np.empty(mzez__cgvdj, np.uint8)
            zaac__dpef = np.empty(wgt__tmux, np.uint32)
            c_scatterv(dvbjt__wbelf.ctypes, send_counts.ctypes, ezyzv__iqv.
                ctypes, zaac__dpef.ctypes, np.int32(wgt__tmux), xqvvx__arcx)
            convert_len_arr_to_offset(zaac__dpef.ctypes, oaoq__xyqus.ctypes,
                wgt__tmux)
            hcna__tjfv = get_scatter_null_bytes_buff(oujde__ympe.ctypes,
                send_counts, enuc__srkpi)
            c_scatterv(hcna__tjfv.ctypes, enuc__srkpi.ctypes, gftqg__xku.
                ctypes, zvrrv__oxju.ctypes, np.int32(mzez__cgvdj), ihebz__egxb)
            return bodo.libs.array_item_arr_ext.init_array_item_array(wgt__tmux
                , ont__mpdb, oaoq__xyqus, zvrrv__oxju)
        return scatterv_array_item_impl
    if isinstance(data, (IntegerArrayType, DecimalArrayType)) or data in (
        boolean_array, datetime_date_array_type):
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))
        if isinstance(data, IntegerArrayType):
            ysclb__plmlt = bodo.libs.int_arr_ext.init_integer_array
        if isinstance(data, DecimalArrayType):
            precision = data.precision
            scale = data.scale
            ysclb__plmlt = numba.njit(no_cpython_wrapper=True)(lambda d, b:
                bodo.libs.decimal_arr_ext.init_decimal_array(d, b,
                precision, scale))
        if data == boolean_array:
            ysclb__plmlt = bodo.libs.bool_arr_ext.init_bool_array
        if data == datetime_date_array_type:
            ysclb__plmlt = (bodo.hiframes.datetime_date_ext.
                init_datetime_date_array)

        def scatterv_impl_int_arr(data, send_counts=None, warn_if_dist=True):
            n_pes = bodo.libs.distributed_api.get_size()
            jor__ycymc = data._data
            tge__zib = data._null_bitmap
            ksrm__ffmd = len(jor__ycymc)
            mibo__ddvti = _scatterv_np(jor__ycymc, send_counts)
            hdv__nkvpv = bcast_scalar(ksrm__ffmd)
            oywbl__gbpyu = len(mibo__ddvti) + 7 >> 3
            dtv__fxd = np.empty(oywbl__gbpyu, np.uint8)
            send_counts = _get_scatterv_send_counts(send_counts, n_pes,
                hdv__nkvpv)
            enuc__srkpi = np.empty(n_pes, np.int32)
            for i in range(n_pes):
                enuc__srkpi[i] = send_counts[i] + 7 >> 3
            gftqg__xku = bodo.ir.join.calc_disp(enuc__srkpi)
            hcna__tjfv = get_scatter_null_bytes_buff(tge__zib.ctypes,
                send_counts, enuc__srkpi)
            c_scatterv(hcna__tjfv.ctypes, enuc__srkpi.ctypes, gftqg__xku.
                ctypes, dtv__fxd.ctypes, np.int32(oywbl__gbpyu), ihebz__egxb)
            return ysclb__plmlt(mibo__ddvti, dtv__fxd)
        return scatterv_impl_int_arr
    if isinstance(data, IntervalArrayType):

        def impl_interval_arr(data, send_counts=None, warn_if_dist=True):
            iua__tbin = bodo.libs.distributed_api.scatterv_impl(data._left,
                send_counts)
            zlx__yqcvv = bodo.libs.distributed_api.scatterv_impl(data.
                _right, send_counts)
            return bodo.libs.interval_arr_ext.init_interval_array(iua__tbin,
                zlx__yqcvv)
        return impl_interval_arr
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):

        def impl_range_index(data, send_counts=None, warn_if_dist=True):
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            start = data._start
            stop = data._stop
            dnpne__mbuux = data._step
            cytf__jfm = data._name
            cytf__jfm = bcast_scalar(cytf__jfm)
            start = bcast_scalar(start)
            stop = bcast_scalar(stop)
            dnpne__mbuux = bcast_scalar(dnpne__mbuux)
            yxqr__tzbup = bodo.libs.array_kernels.calc_nitems(start, stop,
                dnpne__mbuux)
            chunk_start = bodo.libs.distributed_api.get_start(yxqr__tzbup,
                n_pes, rank)
            chunk_count = bodo.libs.distributed_api.get_node_portion(
                yxqr__tzbup, n_pes, rank)
            rtp__axa = start + dnpne__mbuux * chunk_start
            mshfd__limsi = start + dnpne__mbuux * (chunk_start + chunk_count)
            mshfd__limsi = min(mshfd__limsi, stop)
            return bodo.hiframes.pd_index_ext.init_range_index(rtp__axa,
                mshfd__limsi, dnpne__mbuux, cytf__jfm)
        return impl_range_index
    if isinstance(data, bodo.hiframes.pd_index_ext.PeriodIndexType):
        awp__exvyy = data.freq

        def impl_period_index(data, send_counts=None, warn_if_dist=True):
            jor__ycymc = data._data
            cytf__jfm = data._name
            cytf__jfm = bcast_scalar(cytf__jfm)
            arr = bodo.libs.distributed_api.scatterv_impl(jor__ycymc,
                send_counts)
            return bodo.hiframes.pd_index_ext.init_period_index(arr,
                cytf__jfm, awp__exvyy)
        return impl_period_index
    if bodo.hiframes.pd_index_ext.is_pd_index_type(data):

        def impl_pd_index(data, send_counts=None, warn_if_dist=True):
            jor__ycymc = data._data
            cytf__jfm = data._name
            cytf__jfm = bcast_scalar(cytf__jfm)
            arr = bodo.libs.distributed_api.scatterv_impl(jor__ycymc,
                send_counts)
            return bodo.utils.conversion.index_from_array(arr, cytf__jfm)
        return impl_pd_index
    if isinstance(data, bodo.hiframes.pd_multi_index_ext.MultiIndexType):

        def impl_multi_index(data, send_counts=None, warn_if_dist=True):
            nse__cjsh = bodo.libs.distributed_api.scatterv_impl(data._data,
                send_counts)
            cytf__jfm = bcast_scalar(data._name)
            omkb__uhc = bcast_tuple(data._names)
            return bodo.hiframes.pd_multi_index_ext.init_multi_index(nse__cjsh,
                omkb__uhc, cytf__jfm)
        return impl_multi_index
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl_series(data, send_counts=None, warn_if_dist=True):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            cytf__jfm = bodo.hiframes.pd_series_ext.get_series_name(data)
            zthh__hlfcn = bcast_scalar(cytf__jfm)
            out_arr = bodo.libs.distributed_api.scatterv_impl(arr, send_counts)
            shiep__hdo = bodo.libs.distributed_api.scatterv_impl(index,
                send_counts)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                shiep__hdo, zthh__hlfcn)
        return impl_series
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        ccwx__fkyf = len(data.columns)
        tjypp__mfz = ', '.join('g_data_{}'.format(i) for i in range(ccwx__fkyf)
            )
        alrg__vqfvj = bodo.utils.transform.gen_const_tup(data.columns)
        wdsqu__emilb = (
            'def impl_df(data, send_counts=None, warn_if_dist=True):\n')
        for i in range(ccwx__fkyf):
            wdsqu__emilb += (
                """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                .format(i, i))
            wdsqu__emilb += (
                """  g_data_{} = bodo.libs.distributed_api.scatterv_impl(data_{}, send_counts)
"""
                .format(i, i))
        wdsqu__emilb += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        wdsqu__emilb += (
            '  g_index = bodo.libs.distributed_api.scatterv_impl(index, send_counts)\n'
            )
        wdsqu__emilb += (
            """  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})
"""
            .format(tjypp__mfz, alrg__vqfvj))
        zfsd__hekn = {}
        exec(wdsqu__emilb, {'bodo': bodo}, zfsd__hekn)
        eqad__hkl = zfsd__hekn['impl_df']
        return eqad__hkl
    if isinstance(data, CategoricalArrayType):

        def impl_cat(data, send_counts=None, warn_if_dist=True):
            nca__swe = bodo.libs.distributed_api.scatterv_impl(data.codes,
                send_counts)
            return bodo.hiframes.pd_categorical_ext.init_categorical_array(
                nca__swe, data.dtype)
        return impl_cat
    if isinstance(data, types.BaseTuple):
        wdsqu__emilb = (
            'def impl_tuple(data, send_counts=None, warn_if_dist=True):\n')
        wdsqu__emilb += '  return ({}{})\n'.format(', '.join(
            'bodo.libs.distributed_api.scatterv_impl(data[{}], send_counts)'
            .format(i) for i in range(len(data))), ',' if len(data) > 0 else ''
            )
        zfsd__hekn = {}
        exec(wdsqu__emilb, {'bodo': bodo}, zfsd__hekn)
        ehx__hpjd = zfsd__hekn['impl_tuple']
        return ehx__hpjd
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
        nahpf__qju = np.int32(numba_to_c_type(offset_type))
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))

        def bcast_str_impl(data, root=MPI_ROOT):
            data = decode_if_dict_array(data)
            wgt__tmux = len(data)
            inx__odcad = num_total_chars(data)
            assert wgt__tmux < INT_MAX
            assert inx__odcad < INT_MAX
            lusqw__pdaid = get_offset_ptr(data)
            ccuc__merhb = get_data_ptr(data)
            null_bitmap_ptr = get_null_bitmap_ptr(data)
            ste__afx = wgt__tmux + 7 >> 3
            c_bcast(lusqw__pdaid, np.int32(wgt__tmux + 1), nahpf__qju, np.
                array([-1]).ctypes, 0, np.int32(root))
            c_bcast(ccuc__merhb, np.int32(inx__odcad), ihebz__egxb, np.
                array([-1]).ctypes, 0, np.int32(root))
            c_bcast(null_bitmap_ptr, np.int32(ste__afx), ihebz__egxb, np.
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
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))

        def impl_str(val, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            if rank != root:
                hmwm__ruy = 0
                tbs__suvp = np.empty(0, np.uint8).ctypes
            else:
                tbs__suvp, hmwm__ruy = (bodo.libs.str_ext.
                    unicode_to_utf8_and_len(val))
            hmwm__ruy = bodo.libs.distributed_api.bcast_scalar(hmwm__ruy, root)
            if rank != root:
                airq__kmzsa = np.empty(hmwm__ruy + 1, np.uint8)
                airq__kmzsa[hmwm__ruy] = 0
                tbs__suvp = airq__kmzsa.ctypes
            c_bcast(tbs__suvp, np.int32(hmwm__ruy), ihebz__egxb, np.array([
                -1]).ctypes, 0, np.int32(root))
            return bodo.libs.str_arr_ext.decode_utf8(tbs__suvp, hmwm__ruy)
        return impl_str
    typ_val = numba_to_c_type(val)
    wdsqu__emilb = f"""def bcast_scalar_impl(val, root={MPI_ROOT}):
  send = np.empty(1, dtype)
  send[0] = val
  c_bcast(send.ctypes, np.int32(1), np.int32({typ_val}), np.array([-1]).ctypes, 0, np.int32(root))
  return send[0]
"""
    dtype = numba.np.numpy_support.as_dtype(val)
    zfsd__hekn = {}
    exec(wdsqu__emilb, {'bodo': bodo, 'np': np, 'c_bcast': c_bcast, 'dtype':
        dtype}, zfsd__hekn)
    cnh__dlcwm = zfsd__hekn['bcast_scalar_impl']
    return cnh__dlcwm


@numba.generated_jit(nopython=True)
def bcast_tuple(val, root=MPI_ROOT):
    assert isinstance(val, types.BaseTuple)
    ahy__sfzx = len(val)
    wdsqu__emilb = f'def bcast_tuple_impl(val, root={MPI_ROOT}):\n'
    wdsqu__emilb += '  return ({}{})'.format(','.join(
        'bcast_scalar(val[{}], root)'.format(i) for i in range(ahy__sfzx)),
        ',' if ahy__sfzx else '')
    zfsd__hekn = {}
    exec(wdsqu__emilb, {'bcast_scalar': bcast_scalar}, zfsd__hekn)
    cod__khcw = zfsd__hekn['bcast_tuple_impl']
    return cod__khcw


def prealloc_str_for_bcast(arr, root=MPI_ROOT):
    return arr


@overload(prealloc_str_for_bcast, no_unliteral=True)
def prealloc_str_for_bcast_overload(arr, root=MPI_ROOT):
    if arr == string_array_type:

        def prealloc_impl(arr, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            wgt__tmux = bcast_scalar(len(arr), root)
            dpujj__bfa = bcast_scalar(np.int64(num_total_chars(arr)), root)
            if rank != root:
                arr = pre_alloc_string_array(wgt__tmux, dpujj__bfa)
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
        dnpne__mbuux = slice_index.step
        danh__vdro = 0 if dnpne__mbuux == 1 or start > arr_start else abs(
            dnpne__mbuux - arr_start % dnpne__mbuux) % dnpne__mbuux
        rtp__axa = max(arr_start, slice_index.start) - arr_start + danh__vdro
        mshfd__limsi = max(slice_index.stop - arr_start, 0)
        return slice(rtp__axa, mshfd__limsi, dnpne__mbuux)
    return impl


def slice_getitem(arr, slice_index, arr_start, total_len):
    return arr[slice_index]


@overload(slice_getitem, no_unliteral=True, jit_options={'cache': True})
def slice_getitem_overload(arr, slice_index, arr_start, total_len):

    def getitem_impl(arr, slice_index, arr_start, total_len):
        eqkb__bvf = get_local_slice(slice_index, arr_start, total_len)
        return bodo.utils.conversion.ensure_contig_if_np(arr[eqkb__bvf])
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
        xlqm__qdf = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND
        ihebz__egxb = np.int32(numba_to_c_type(types.uint8))
        wrvw__niwb = arr.dtype

        def str_getitem_impl(arr, ind, arr_start, total_len, is_1D):
            if ind >= total_len:
                raise IndexError('index out of bounds')
            arr = decode_if_dict_array(arr)
            ind = ind % total_len
            root = np.int32(0)
            crv__qagu = np.int32(10)
            tag = np.int32(11)
            asill__vvf = np.zeros(1, np.int64)
            if arr_start <= ind < arr_start + len(arr):
                ind = ind - arr_start
                kopop__zzrrt = arr._data
                jbjkg__vvidj = bodo.libs.array_item_arr_ext.get_offsets_ind(
                    kopop__zzrrt, ind)
                cfm__ylc = bodo.libs.array_item_arr_ext.get_offsets_ind(
                    kopop__zzrrt, ind + 1)
                length = cfm__ylc - jbjkg__vvidj
                uxr__idqj = kopop__zzrrt[ind]
                asill__vvf[0] = length
                isend(asill__vvf, np.int32(1), root, crv__qagu, True)
                isend(uxr__idqj, np.int32(length), root, tag, True)
            rank = bodo.libs.distributed_api.get_rank()
            val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(wrvw__niwb
                , xlqm__qdf, 0, 1)
            ixns__yvknz = 0
            if rank == root:
                ixns__yvknz = recv(np.int64, ANY_SOURCE, crv__qagu)
                val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(
                    wrvw__niwb, xlqm__qdf, ixns__yvknz, 1)
                ccuc__merhb = bodo.libs.str_ext.get_unicode_or_numpy_data(val)
                _recv(ccuc__merhb, np.int32(ixns__yvknz), ihebz__egxb,
                    ANY_SOURCE, tag)
            dummy_use(asill__vvf)
            ixns__yvknz = bcast_scalar(ixns__yvknz)
            dummy_use(arr)
            if rank != root:
                val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(
                    wrvw__niwb, xlqm__qdf, ixns__yvknz, 1)
            ccuc__merhb = bodo.libs.str_ext.get_unicode_or_numpy_data(val)
            c_bcast(ccuc__merhb, np.int32(ixns__yvknz), ihebz__egxb, np.
                array([-1]).ctypes, 0, np.int32(root))
            val = transform_str_getitem_output(val, ixns__yvknz)
            return val
        return str_getitem_impl
    if isinstance(arr, bodo.CategoricalArrayType):
        lrzp__kmjq = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            arr.dtype)

        def cat_getitem_impl(arr, ind, arr_start, total_len, is_1D):
            if ind >= total_len:
                raise IndexError('index out of bounds')
            ind = ind % total_len
            root = np.int32(0)
            tag = np.int32(11)
            send_arr = np.zeros(1, lrzp__kmjq)
            if arr_start <= ind < arr_start + len(arr):
                nca__swe = (bodo.hiframes.pd_categorical_ext.
                    get_categorical_arr_codes(arr))
                data = nca__swe[ind - arr_start]
                send_arr = np.full(1, data, lrzp__kmjq)
                isend(send_arr, np.int32(1), root, tag, True)
            rank = bodo.libs.distributed_api.get_rank()
            val = lrzp__kmjq(-1)
            if rank == root:
                val = recv(lrzp__kmjq, ANY_SOURCE, tag)
            dummy_use(send_arr)
            val = bcast_scalar(val)
            prcar__ydur = arr.dtype.categories[max(val, 0)]
            return prcar__ydur
        return cat_getitem_impl
    mulro__jfdk = arr.dtype

    def getitem_impl(arr, ind, arr_start, total_len, is_1D):
        if ind >= total_len:
            raise IndexError('index out of bounds')
        ind = ind % total_len
        root = np.int32(0)
        tag = np.int32(11)
        send_arr = np.zeros(1, mulro__jfdk)
        if arr_start <= ind < arr_start + len(arr):
            data = arr[ind - arr_start]
            send_arr = np.full(1, data)
            isend(send_arr, np.int32(1), root, tag, True)
        rank = bodo.libs.distributed_api.get_rank()
        val = np.zeros(1, mulro__jfdk)[0]
        if rank == root:
            val = recv(mulro__jfdk, ANY_SOURCE, tag)
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
    vob__qpd = get_type_enum(out_data)
    assert typ_enum == vob__qpd
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
    wdsqu__emilb = (
        'def f(send_data, out_data, send_counts, recv_counts, send_disp, recv_disp):\n'
        )
    for i in range(count):
        wdsqu__emilb += (
            """  alltoallv(send_data[{}], out_data[{}], send_counts, recv_counts, send_disp, recv_disp)
"""
            .format(i, i))
    wdsqu__emilb += '  return\n'
    zfsd__hekn = {}
    exec(wdsqu__emilb, {'alltoallv': alltoallv}, zfsd__hekn)
    rvzg__cxccy = zfsd__hekn['f']
    return rvzg__cxccy


@numba.njit
def get_start_count(n):
    rank = bodo.libs.distributed_api.get_rank()
    n_pes = bodo.libs.distributed_api.get_size()
    start = bodo.libs.distributed_api.get_start(n, n_pes, rank)
    count = bodo.libs.distributed_api.get_node_portion(n, n_pes, rank)
    return start, count


@numba.njit
def get_start(total_size, pes, rank):
    qowz__mut = total_size % pes
    dfof__pwad = (total_size - qowz__mut) // pes
    return rank * dfof__pwad + min(rank, qowz__mut)


@numba.njit
def get_end(total_size, pes, rank):
    qowz__mut = total_size % pes
    dfof__pwad = (total_size - qowz__mut) // pes
    return (rank + 1) * dfof__pwad + min(rank + 1, qowz__mut)


@numba.njit
def get_node_portion(total_size, pes, rank):
    qowz__mut = total_size % pes
    dfof__pwad = (total_size - qowz__mut) // pes
    if rank < qowz__mut:
        return dfof__pwad + 1
    else:
        return dfof__pwad


@numba.generated_jit(nopython=True)
def dist_cumsum(in_arr, out_arr):
    ygod__limrq = in_arr.dtype(0)
    qzs__rckza = np.int32(Reduce_Type.Sum.value)

    def cumsum_impl(in_arr, out_arr):
        ansxv__ripv = ygod__limrq
        for thx__atmj in np.nditer(in_arr):
            ansxv__ripv += thx__atmj.item()
        mhuhy__zyi = dist_exscan(ansxv__ripv, qzs__rckza)
        for i in range(in_arr.size):
            mhuhy__zyi += in_arr[i]
            out_arr[i] = mhuhy__zyi
        return 0
    return cumsum_impl


@numba.generated_jit(nopython=True)
def dist_cumprod(in_arr, out_arr):
    mrbnh__rbppz = in_arr.dtype(1)
    qzs__rckza = np.int32(Reduce_Type.Prod.value)

    def cumprod_impl(in_arr, out_arr):
        ansxv__ripv = mrbnh__rbppz
        for thx__atmj in np.nditer(in_arr):
            ansxv__ripv *= thx__atmj.item()
        mhuhy__zyi = dist_exscan(ansxv__ripv, qzs__rckza)
        if get_rank() == 0:
            mhuhy__zyi = mrbnh__rbppz
        for i in range(in_arr.size):
            mhuhy__zyi *= in_arr[i]
            out_arr[i] = mhuhy__zyi
        return 0
    return cumprod_impl


@numba.generated_jit(nopython=True)
def dist_cummin(in_arr, out_arr):
    if isinstance(in_arr.dtype, types.Float):
        mrbnh__rbppz = np.finfo(in_arr.dtype(1).dtype).max
    else:
        mrbnh__rbppz = np.iinfo(in_arr.dtype(1).dtype).max
    qzs__rckza = np.int32(Reduce_Type.Min.value)

    def cummin_impl(in_arr, out_arr):
        ansxv__ripv = mrbnh__rbppz
        for thx__atmj in np.nditer(in_arr):
            ansxv__ripv = min(ansxv__ripv, thx__atmj.item())
        mhuhy__zyi = dist_exscan(ansxv__ripv, qzs__rckza)
        if get_rank() == 0:
            mhuhy__zyi = mrbnh__rbppz
        for i in range(in_arr.size):
            mhuhy__zyi = min(mhuhy__zyi, in_arr[i])
            out_arr[i] = mhuhy__zyi
        return 0
    return cummin_impl


@numba.generated_jit(nopython=True)
def dist_cummax(in_arr, out_arr):
    if isinstance(in_arr.dtype, types.Float):
        mrbnh__rbppz = np.finfo(in_arr.dtype(1).dtype).min
    else:
        mrbnh__rbppz = np.iinfo(in_arr.dtype(1).dtype).min
    mrbnh__rbppz = in_arr.dtype(1)
    qzs__rckza = np.int32(Reduce_Type.Max.value)

    def cummax_impl(in_arr, out_arr):
        ansxv__ripv = mrbnh__rbppz
        for thx__atmj in np.nditer(in_arr):
            ansxv__ripv = max(ansxv__ripv, thx__atmj.item())
        mhuhy__zyi = dist_exscan(ansxv__ripv, qzs__rckza)
        if get_rank() == 0:
            mhuhy__zyi = mrbnh__rbppz
        for i in range(in_arr.size):
            mhuhy__zyi = max(mhuhy__zyi, in_arr[i])
            out_arr[i] = mhuhy__zyi
        return 0
    return cummax_impl


_allgather = types.ExternalFunction('allgather', types.void(types.voidptr,
    types.int32, types.voidptr, types.int32))


@numba.njit
def allgather(arr, val):
    nxk__zucr = get_type_enum(arr)
    _allgather(arr.ctypes, 1, value_to_ptr(val), nxk__zucr)


def dist_return(A):
    return A


def rep_return(A):
    return A


def dist_return_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    ekqf__ias = args[0]
    if equiv_set.has_shape(ekqf__ias):
        return ArrayAnalysis.AnalyzeResult(shape=ekqf__ias, pre=[])
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
        wziw__anfrm = ','.join(f'_wait(req[{i}], cond)' for i in range(count))
        wdsqu__emilb = 'def f(req, cond=True):\n'
        wdsqu__emilb += f'  return {wziw__anfrm}\n'
        zfsd__hekn = {}
        exec(wdsqu__emilb, {'_wait': _wait}, zfsd__hekn)
        impl = zfsd__hekn['f']
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
    rtp__axa = max(start, chunk_start)
    mshfd__limsi = min(stop, chunk_start + chunk_count)
    yzhgi__zmjst = rtp__axa - chunk_start
    cdg__khw = mshfd__limsi - chunk_start
    if yzhgi__zmjst < 0 or cdg__khw < 0:
        yzhgi__zmjst = 1
        cdg__khw = 0
    return yzhgi__zmjst, cdg__khw


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
        qowz__mut = 1
        for a in t:
            qowz__mut *= a
        return qowz__mut
    return get_tuple_prod_impl


sig = types.void(types.voidptr, types.voidptr, types.intp, types.intp,
    types.intp, types.intp, types.int32, types.voidptr)
oneD_reshape_shuffle = types.ExternalFunction('oneD_reshape_shuffle', sig)


@numba.njit(no_cpython_wrapper=True, cache=True)
def dist_oneD_reshape_shuffle(lhs, in_arr, new_dim0_global_len, dest_ranks=None
    ):
    wgs__ujjw = np.ascontiguousarray(in_arr)
    mxwkw__klwfo = get_tuple_prod(wgs__ujjw.shape[1:])
    grkx__mbzy = get_tuple_prod(lhs.shape[1:])
    if dest_ranks is not None:
        azwmy__hzan = np.array(dest_ranks, dtype=np.int32)
    else:
        azwmy__hzan = np.empty(0, dtype=np.int32)
    dtype_size = bodo.io.np_io.get_dtype_size(in_arr.dtype)
    oneD_reshape_shuffle(lhs.ctypes, wgs__ujjw.ctypes, new_dim0_global_len,
        len(in_arr), dtype_size * grkx__mbzy, dtype_size * mxwkw__klwfo,
        len(azwmy__hzan), azwmy__hzan.ctypes)
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
    uhn__bsh = np.ascontiguousarray(rhs)
    ldjcf__luhtm = get_tuple_prod(uhn__bsh.shape[1:])
    qqj__lon = dtype_size * ldjcf__luhtm
    permutation_array_index(lhs.ctypes, lhs_len, qqj__lon, uhn__bsh.ctypes,
        uhn__bsh.shape[0], p.ctypes, p_len)
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
        wdsqu__emilb = (
            f"""def bcast_scalar_impl(data, comm_ranks, nranks, root={MPI_ROOT}):
  send = np.empty(1, dtype)
  send[0] = data
  c_bcast(send.ctypes, np.int32(1), np.int32({{}}), comm_ranks,ctypes, np.int32({{}}), np.int32(root))
  return send[0]
"""
            .format(typ_val, nranks))
        dtype = numba.np.numpy_support.as_dtype(data)
        zfsd__hekn = {}
        exec(wdsqu__emilb, {'bodo': bodo, 'np': np, 'c_bcast': c_bcast,
            'dtype': dtype}, zfsd__hekn)
        cnh__dlcwm = zfsd__hekn['bcast_scalar_impl']
        return cnh__dlcwm
    if isinstance(data, types.Array):
        return lambda data, comm_ranks, nranks, root=MPI_ROOT: _bcast_np(data,
            comm_ranks, nranks, root)
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        ccwx__fkyf = len(data.columns)
        tjypp__mfz = ', '.join('g_data_{}'.format(i) for i in range(ccwx__fkyf)
            )
        alrg__vqfvj = bodo.utils.transform.gen_const_tup(data.columns)
        wdsqu__emilb = (
            f'def impl_df(data, comm_ranks, nranks, root={MPI_ROOT}):\n')
        for i in range(ccwx__fkyf):
            wdsqu__emilb += (
                """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                .format(i, i))
            wdsqu__emilb += (
                """  g_data_{} = bodo.libs.distributed_api.bcast_comm_impl(data_{}, comm_ranks, nranks, root)
"""
                .format(i, i))
        wdsqu__emilb += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        wdsqu__emilb += """  g_index = bodo.libs.distributed_api.bcast_comm_impl(index, comm_ranks, nranks, root)
"""
        wdsqu__emilb += (
            """  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})
"""
            .format(tjypp__mfz, alrg__vqfvj))
        zfsd__hekn = {}
        exec(wdsqu__emilb, {'bodo': bodo}, zfsd__hekn)
        eqad__hkl = zfsd__hekn['impl_df']
        return eqad__hkl
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):

        def impl_range_index(data, comm_ranks, nranks, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            start = data._start
            stop = data._stop
            dnpne__mbuux = data._step
            cytf__jfm = data._name
            cytf__jfm = bcast_scalar(cytf__jfm, root)
            start = bcast_scalar(start, root)
            stop = bcast_scalar(stop, root)
            dnpne__mbuux = bcast_scalar(dnpne__mbuux, root)
            yxqr__tzbup = bodo.libs.array_kernels.calc_nitems(start, stop,
                dnpne__mbuux)
            chunk_start = bodo.libs.distributed_api.get_start(yxqr__tzbup,
                n_pes, rank)
            chunk_count = bodo.libs.distributed_api.get_node_portion(
                yxqr__tzbup, n_pes, rank)
            rtp__axa = start + dnpne__mbuux * chunk_start
            mshfd__limsi = start + dnpne__mbuux * (chunk_start + chunk_count)
            mshfd__limsi = min(mshfd__limsi, stop)
            return bodo.hiframes.pd_index_ext.init_range_index(rtp__axa,
                mshfd__limsi, dnpne__mbuux, cytf__jfm)
        return impl_range_index
    if bodo.hiframes.pd_index_ext.is_pd_index_type(data):

        def impl_pd_index(data, comm_ranks, nranks, root=MPI_ROOT):
            jor__ycymc = data._data
            cytf__jfm = data._name
            arr = bodo.libs.distributed_api.bcast_comm_impl(jor__ycymc,
                comm_ranks, nranks, root)
            return bodo.utils.conversion.index_from_array(arr, cytf__jfm)
        return impl_pd_index
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl_series(data, comm_ranks, nranks, root=MPI_ROOT):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            cytf__jfm = bodo.hiframes.pd_series_ext.get_series_name(data)
            zthh__hlfcn = bodo.libs.distributed_api.bcast_comm_impl(cytf__jfm,
                comm_ranks, nranks, root)
            out_arr = bodo.libs.distributed_api.bcast_comm_impl(arr,
                comm_ranks, nranks, root)
            shiep__hdo = bodo.libs.distributed_api.bcast_comm_impl(index,
                comm_ranks, nranks, root)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                shiep__hdo, zthh__hlfcn)
        return impl_series
    if isinstance(data, types.BaseTuple):
        wdsqu__emilb = (
            f'def impl_tuple(data, comm_ranks, nranks, root={MPI_ROOT}):\n')
        wdsqu__emilb += '  return ({}{})\n'.format(', '.join(
            'bcast_comm_impl(data[{}], comm_ranks, nranks, root)'.format(i) for
            i in range(len(data))), ',' if len(data) > 0 else '')
        zfsd__hekn = {}
        exec(wdsqu__emilb, {'bcast_comm_impl': bcast_comm_impl}, zfsd__hekn)
        ehx__hpjd = zfsd__hekn['impl_tuple']
        return ehx__hpjd
    if data is types.none:
        return lambda data, comm_ranks, nranks, root=MPI_ROOT: None


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _bcast_np(data, comm_ranks, nranks, root=MPI_ROOT):
    typ_val = numba_to_c_type(data.dtype)
    jyur__nua = data.ndim
    dtype = data.dtype
    if dtype == types.NPDatetime('ns'):
        dtype = np.dtype('datetime64[ns]')
    elif dtype == types.NPTimedelta('ns'):
        dtype = np.dtype('timedelta64[ns]')
    yqioe__nif = (0,) * jyur__nua

    def bcast_arr_impl(data, comm_ranks, nranks, root=MPI_ROOT):
        rank = bodo.libs.distributed_api.get_rank()
        jor__ycymc = np.ascontiguousarray(data)
        ccuc__merhb = data.ctypes
        eyxzd__vnfc = yqioe__nif
        if rank == root:
            eyxzd__vnfc = jor__ycymc.shape
        eyxzd__vnfc = bcast_tuple(eyxzd__vnfc, root)
        fwv__xgs = get_tuple_prod(eyxzd__vnfc[1:])
        send_counts = eyxzd__vnfc[0] * fwv__xgs
        ifjl__ulck = np.empty(send_counts, dtype)
        if rank == MPI_ROOT:
            c_bcast(ccuc__merhb, np.int32(send_counts), np.int32(typ_val),
                comm_ranks.ctypes, np.int32(nranks), np.int32(root))
            return data
        else:
            c_bcast(ifjl__ulck.ctypes, np.int32(send_counts), np.int32(
                typ_val), comm_ranks.ctypes, np.int32(nranks), np.int32(root))
            return ifjl__ulck.reshape((-1,) + eyxzd__vnfc[1:])
    return bcast_arr_impl


node_ranks = None


def get_host_ranks():
    global node_ranks
    if node_ranks is None:
        muxaw__mhd = MPI.COMM_WORLD
        qfams__ocrbg = MPI.Get_processor_name()
        xlnc__vyz = muxaw__mhd.allgather(qfams__ocrbg)
        node_ranks = defaultdict(list)
        for i, odvx__cokc in enumerate(xlnc__vyz):
            node_ranks[odvx__cokc].append(i)
    return node_ranks


def create_subcomm_mpi4py(comm_ranks):
    muxaw__mhd = MPI.COMM_WORLD
    lbm__rmpwx = muxaw__mhd.Get_group()
    nzd__pkfj = lbm__rmpwx.Incl(comm_ranks)
    mnqfo__opz = muxaw__mhd.Create_group(nzd__pkfj)
    return mnqfo__opz


def get_nodes_first_ranks():
    dphc__jhpk = get_host_ranks()
    return np.array([lialc__wrnxq[0] for lialc__wrnxq in dphc__jhpk.values(
        )], dtype='int32')


def get_num_nodes():
    return len(get_host_ranks())
