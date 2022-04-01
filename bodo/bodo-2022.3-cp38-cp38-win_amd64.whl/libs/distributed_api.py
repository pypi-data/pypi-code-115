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
    zszsz__xjkk = get_type_enum(send_arr)
    _send(send_arr.ctypes, 1, zszsz__xjkk, rank, tag)


_recv = types.ExternalFunction('c_recv', types.void(types.voidptr, types.
    int32, types.int32, types.int32, types.int32))


@numba.njit
def recv(dtype, rank, tag):
    recv_arr = np.empty(1, dtype)
    zszsz__xjkk = get_type_enum(recv_arr)
    _recv(recv_arr.ctypes, 1, zszsz__xjkk, rank, tag)
    return recv_arr[0]


_isend = types.ExternalFunction('dist_isend', mpi_req_numba_type(types.
    voidptr, types.int32, types.int32, types.int32, types.int32, types.bool_))


@numba.generated_jit(nopython=True)
def isend(arr, size, pe, tag, cond=True):
    if isinstance(arr, types.Array):

        def impl(arr, size, pe, tag, cond=True):
            zszsz__xjkk = get_type_enum(arr)
            return _isend(arr.ctypes, size, zszsz__xjkk, pe, tag, cond)
        return impl
    if isinstance(arr, (IntegerArrayType, DecimalArrayType)) or arr in (
        boolean_array, datetime_date_array_type):
        zszsz__xjkk = np.int32(numba_to_c_type(arr.dtype))
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))

        def impl_nullable(arr, size, pe, tag, cond=True):
            eezpf__yolz = size + 7 >> 3
            inzmd__emyo = _isend(arr._data.ctypes, size, zszsz__xjkk, pe,
                tag, cond)
            fyc__msz = _isend(arr._null_bitmap.ctypes, eezpf__yolz,
                oxfne__dcg, pe, tag, cond)
            return inzmd__emyo, fyc__msz
        return impl_nullable
    if is_str_arr_type(arr) or arr == binary_array_type:
        qfqvd__ocr = np.int32(numba_to_c_type(offset_type))
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))

        def impl_str_arr(arr, size, pe, tag, cond=True):
            arr = decode_if_dict_array(arr)
            addia__jsxpv = np.int64(bodo.libs.str_arr_ext.num_total_chars(arr))
            send(addia__jsxpv, pe, tag - 1)
            eezpf__yolz = size + 7 >> 3
            _send(bodo.libs.str_arr_ext.get_offset_ptr(arr), size + 1,
                qfqvd__ocr, pe, tag)
            _send(bodo.libs.str_arr_ext.get_data_ptr(arr), addia__jsxpv,
                oxfne__dcg, pe, tag)
            _send(bodo.libs.str_arr_ext.get_null_bitmap_ptr(arr),
                eezpf__yolz, oxfne__dcg, pe, tag)
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
            zszsz__xjkk = get_type_enum(arr)
            return _irecv(arr.ctypes, size, zszsz__xjkk, pe, tag, cond)
        return impl
    if isinstance(arr, (IntegerArrayType, DecimalArrayType)) or arr in (
        boolean_array, datetime_date_array_type):
        zszsz__xjkk = np.int32(numba_to_c_type(arr.dtype))
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))

        def impl_nullable(arr, size, pe, tag, cond=True):
            eezpf__yolz = size + 7 >> 3
            inzmd__emyo = _irecv(arr._data.ctypes, size, zszsz__xjkk, pe,
                tag, cond)
            fyc__msz = _irecv(arr._null_bitmap.ctypes, eezpf__yolz,
                oxfne__dcg, pe, tag, cond)
            return inzmd__emyo, fyc__msz
        return impl_nullable
    if arr in [binary_array_type, string_array_type]:
        qfqvd__ocr = np.int32(numba_to_c_type(offset_type))
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))
        if arr == binary_array_type:
            ajt__ayjg = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
        else:
            ajt__ayjg = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
        tof__mtokq = f"""def impl(arr, size, pe, tag, cond=True):
            # recv the number of string characters and resize buffer to proper size
            n_chars = bodo.libs.distributed_api.recv(np.int64, pe, tag - 1)
            new_arr = {ajt__ayjg}(size, n_chars)
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
        iwyn__tvoov = dict()
        exec(tof__mtokq, {'bodo': bodo, 'np': np, 'offset_typ_enum':
            qfqvd__ocr, 'char_typ_enum': oxfne__dcg}, iwyn__tvoov)
        impl = iwyn__tvoov['impl']
        return impl
    raise BodoError(f'irecv(): array type {arr} not supported yet')


_alltoall = types.ExternalFunction('c_alltoall', types.void(types.voidptr,
    types.voidptr, types.int32, types.int32))


@numba.njit
def alltoall(send_arr, recv_arr, count):
    assert count < INT_MAX
    zszsz__xjkk = get_type_enum(send_arr)
    _alltoall(send_arr.ctypes, recv_arr.ctypes, np.int32(count), zszsz__xjkk)


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
        trl__ypeq = n_pes if rank == root or allgather else 0
        dud__gvd = np.empty(trl__ypeq, dtype)
        c_gather_scalar(send.ctypes, dud__gvd.ctypes, np.int32(typ_val),
            allgather, np.int32(root))
        return dud__gvd
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
        hidy__ndr = cgutils.alloca_once(builder, args[0].type)
        builder.store(args[0], hidy__ndr)
        return builder.bitcast(hidy__ndr, lir.IntType(8).as_pointer())
    return types.voidptr(val_tp), codegen


@intrinsic
def load_val_ptr(typingctx, ptr_tp, val_tp=None):

    def codegen(context, builder, sig, args):
        hidy__ndr = builder.bitcast(args[0], args[1].type.as_pointer())
        return builder.load(hidy__ndr)
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
    qem__uxw = types.unliteral(value)
    if isinstance(qem__uxw, IndexValueType):
        qem__uxw = qem__uxw.val_typ
        ipsfw__bgukd = [types.bool_, types.uint8, types.int8, types.uint16,
            types.int16, types.uint32, types.int32, types.float32, types.
            float64]
        if not sys.platform.startswith('win'):
            ipsfw__bgukd.append(types.int64)
            ipsfw__bgukd.append(bodo.datetime64ns)
            ipsfw__bgukd.append(bodo.timedelta64ns)
            ipsfw__bgukd.append(bodo.datetime_date_type)
        if qem__uxw not in ipsfw__bgukd:
            raise BodoError('argmin/argmax not supported for type {}'.
                format(qem__uxw))
    typ_enum = np.int32(numba_to_c_type(qem__uxw))

    def impl(value, reduce_op):
        hndxf__uwmow = value_to_ptr(value)
        hidim__byb = value_to_ptr(value)
        _dist_reduce(hndxf__uwmow, hidim__byb, reduce_op, typ_enum)
        return load_val_ptr(hidim__byb, value)
    return impl


_dist_exscan = types.ExternalFunction('dist_exscan', types.void(types.
    voidptr, types.voidptr, types.int32, types.int32))


@numba.generated_jit(nopython=True)
def dist_exscan(value, reduce_op):
    qem__uxw = types.unliteral(value)
    typ_enum = np.int32(numba_to_c_type(qem__uxw))
    lqqoq__ltnxr = qem__uxw(0)

    def impl(value, reduce_op):
        hndxf__uwmow = value_to_ptr(value)
        hidim__byb = value_to_ptr(lqqoq__ltnxr)
        _dist_exscan(hndxf__uwmow, hidim__byb, reduce_op, typ_enum)
        return load_val_ptr(hidim__byb, value)
    return impl


@numba.njit
def get_bit(bits, i):
    return bits[i >> 3] >> (i & 7) & 1


@numba.njit
def copy_gathered_null_bytes(null_bitmap_ptr, tmp_null_bytes,
    recv_counts_nulls, recv_counts):
    jeqlt__ohhm = 0
    suvw__asb = 0
    for i in range(len(recv_counts)):
        lubu__aiec = recv_counts[i]
        eezpf__yolz = recv_counts_nulls[i]
        pxpg__fya = tmp_null_bytes[jeqlt__ohhm:jeqlt__ohhm + eezpf__yolz]
        for avjd__txq in range(lubu__aiec):
            set_bit_to(null_bitmap_ptr, suvw__asb, get_bit(pxpg__fya,
                avjd__txq))
            suvw__asb += 1
        jeqlt__ohhm += eezpf__yolz


@numba.generated_jit(nopython=True)
def gatherv(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
    from bodo.libs.csr_matrix_ext import CSRMatrixType
    bodo.hiframes.pd_dataframe_ext.check_runtime_cols_unsupported(data,
        'bodo.gatherv()')
    if isinstance(data, CategoricalArrayType):

        def impl_cat(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
            szwuv__rpai = bodo.gatherv(data.codes, allgather, root=root)
            return bodo.hiframes.pd_categorical_ext.init_categorical_array(
                szwuv__rpai, data.dtype)
        return impl_cat
    if isinstance(data, types.Array):
        typ_val = numba_to_c_type(data.dtype)

        def gatherv_impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            data = np.ascontiguousarray(data)
            rank = bodo.libs.distributed_api.get_rank()
            hahwz__ytww = data.size
            recv_counts = gather_scalar(np.int32(hahwz__ytww), allgather,
                root=root)
            jdgpf__ctpkb = recv_counts.sum()
            sqxe__snrb = empty_like_type(jdgpf__ctpkb, data)
            rqi__numx = np.empty(1, np.int32)
            if rank == root or allgather:
                rqi__numx = bodo.ir.join.calc_disp(recv_counts)
            c_gatherv(data.ctypes, np.int32(hahwz__ytww), sqxe__snrb.ctypes,
                recv_counts.ctypes, rqi__numx.ctypes, np.int32(typ_val),
                allgather, np.int32(root))
            return sqxe__snrb.reshape((-1,) + data.shape[1:])
        return gatherv_impl
    if is_str_arr_type(data):

        def gatherv_str_arr_impl(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            data = decode_if_dict_array(data)
            sqxe__snrb = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.str_arr_ext.init_str_arr(sqxe__snrb)
        return gatherv_str_arr_impl
    if data == binary_array_type:

        def gatherv_binary_arr_impl(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            sqxe__snrb = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.binary_arr_ext.init_binary_arr(sqxe__snrb)
        return gatherv_binary_arr_impl
    if data == datetime_timedelta_array_type:
        typ_val = numba_to_c_type(types.int64)
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))

        def gatherv_impl_int_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            hahwz__ytww = len(data)
            eezpf__yolz = hahwz__ytww + 7 >> 3
            recv_counts = gather_scalar(np.int32(hahwz__ytww), allgather,
                root=root)
            jdgpf__ctpkb = recv_counts.sum()
            sqxe__snrb = empty_like_type(jdgpf__ctpkb, data)
            rqi__numx = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            svrxa__snm = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                rqi__numx = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                svrxa__snm = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(data._days_data.ctypes, np.int32(hahwz__ytww),
                sqxe__snrb._days_data.ctypes, recv_counts.ctypes, rqi__numx
                .ctypes, np.int32(typ_val), allgather, np.int32(root))
            c_gatherv(data._seconds_data.ctypes, np.int32(hahwz__ytww),
                sqxe__snrb._seconds_data.ctypes, recv_counts.ctypes,
                rqi__numx.ctypes, np.int32(typ_val), allgather, np.int32(root))
            c_gatherv(data._microseconds_data.ctypes, np.int32(hahwz__ytww),
                sqxe__snrb._microseconds_data.ctypes, recv_counts.ctypes,
                rqi__numx.ctypes, np.int32(typ_val), allgather, np.int32(root))
            c_gatherv(data._null_bitmap.ctypes, np.int32(eezpf__yolz),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, svrxa__snm
                .ctypes, oxfne__dcg, allgather, np.int32(root))
            copy_gathered_null_bytes(sqxe__snrb._null_bitmap.ctypes,
                tmp_null_bytes, recv_counts_nulls, recv_counts)
            return sqxe__snrb
        return gatherv_impl_int_arr
    if isinstance(data, (IntegerArrayType, DecimalArrayType)) or data in (
        boolean_array, datetime_date_array_type):
        typ_val = numba_to_c_type(data.dtype)
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))

        def gatherv_impl_int_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            hahwz__ytww = len(data)
            eezpf__yolz = hahwz__ytww + 7 >> 3
            recv_counts = gather_scalar(np.int32(hahwz__ytww), allgather,
                root=root)
            jdgpf__ctpkb = recv_counts.sum()
            sqxe__snrb = empty_like_type(jdgpf__ctpkb, data)
            rqi__numx = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            svrxa__snm = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                rqi__numx = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                svrxa__snm = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(data._data.ctypes, np.int32(hahwz__ytww), sqxe__snrb.
                _data.ctypes, recv_counts.ctypes, rqi__numx.ctypes, np.
                int32(typ_val), allgather, np.int32(root))
            c_gatherv(data._null_bitmap.ctypes, np.int32(eezpf__yolz),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, svrxa__snm
                .ctypes, oxfne__dcg, allgather, np.int32(root))
            copy_gathered_null_bytes(sqxe__snrb._null_bitmap.ctypes,
                tmp_null_bytes, recv_counts_nulls, recv_counts)
            return sqxe__snrb
        return gatherv_impl_int_arr
    if isinstance(data, DatetimeArrayType):
        hipk__yup = data.tz

        def impl_pd_datetime_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            uxbk__bmt = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.pd_datetime_arr_ext.init_pandas_datetime_array(
                uxbk__bmt, hipk__yup)
        return impl_pd_datetime_arr
    if isinstance(data, IntervalArrayType):

        def impl_interval_arr(data, allgather=False, warn_if_rep=True, root
            =MPI_ROOT):
            cgjo__qebqe = bodo.gatherv(data._left, allgather, warn_if_rep, root
                )
            uumq__lydqx = bodo.gatherv(data._right, allgather, warn_if_rep,
                root)
            return bodo.libs.interval_arr_ext.init_interval_array(cgjo__qebqe,
                uumq__lydqx)
        return impl_interval_arr
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            ozeq__qand = bodo.hiframes.pd_series_ext.get_series_name(data)
            out_arr = bodo.libs.distributed_api.gatherv(arr, allgather,
                warn_if_rep, root)
            szuu__fjr = bodo.gatherv(index, allgather, warn_if_rep, root)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                szuu__fjr, ozeq__qand)
        return impl
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):
        hwucm__zvoti = np.iinfo(np.int64).max
        aej__nus = np.iinfo(np.int64).min

        def impl_range_index(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            start = data._start
            stop = data._stop
            if len(data) == 0:
                start = hwucm__zvoti
                stop = aej__nus
            start = bodo.libs.distributed_api.dist_reduce(start, np.int32(
                Reduce_Type.Min.value))
            stop = bodo.libs.distributed_api.dist_reduce(stop, np.int32(
                Reduce_Type.Max.value))
            total_len = bodo.libs.distributed_api.dist_reduce(len(data), np
                .int32(Reduce_Type.Sum.value))
            if start == hwucm__zvoti and stop == aej__nus:
                start = 0
                stop = 0
            qwjpu__mdyy = max(0, -(-(stop - start) // data._step))
            if qwjpu__mdyy < total_len:
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
            velyw__hoez = data.freq

            def impl_pd_index(data, allgather=False, warn_if_rep=True, root
                =MPI_ROOT):
                arr = bodo.libs.distributed_api.gatherv(data._data,
                    allgather, root=root)
                return bodo.hiframes.pd_index_ext.init_period_index(arr,
                    data._name, velyw__hoez)
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
            sqxe__snrb = bodo.gatherv(data._data, allgather, root=root)
            return bodo.hiframes.pd_multi_index_ext.init_multi_index(sqxe__snrb
                , data._names, data._name)
        return impl_multi_index
    if isinstance(data, bodo.hiframes.table.TableType):
        ynvql__dmk = {'bodo': bodo, 'get_table_block': bodo.hiframes.table.
            get_table_block, 'ensure_column_unboxed': bodo.hiframes.table.
            ensure_column_unboxed, 'set_table_block': bodo.hiframes.table.
            set_table_block, 'set_table_len': bodo.hiframes.table.
            set_table_len, 'alloc_list_like': bodo.hiframes.table.
            alloc_list_like, 'init_table': bodo.hiframes.table.init_table}
        tof__mtokq = (
            f'def impl_table(data, allgather=False, warn_if_rep=True, root={MPI_ROOT}):\n'
            )
        tof__mtokq += '  T = data\n'
        tof__mtokq += '  T2 = init_table(T, True)\n'
        for isz__wssl in data.type_to_blk.values():
            ynvql__dmk[f'arr_inds_{isz__wssl}'] = np.array(data.
                block_to_arr_ind[isz__wssl], dtype=np.int64)
            tof__mtokq += (
                f'  arr_list_{isz__wssl} = get_table_block(T, {isz__wssl})\n')
            tof__mtokq += f"""  out_arr_list_{isz__wssl} = alloc_list_like(arr_list_{isz__wssl}, True)
"""
            tof__mtokq += f'  for i in range(len(arr_list_{isz__wssl})):\n'
            tof__mtokq += (
                f'    arr_ind_{isz__wssl} = arr_inds_{isz__wssl}[i]\n')
            tof__mtokq += f"""    ensure_column_unboxed(T, arr_list_{isz__wssl}, i, arr_ind_{isz__wssl})
"""
            tof__mtokq += f"""    out_arr_{isz__wssl} = bodo.gatherv(arr_list_{isz__wssl}[i], allgather, warn_if_rep, root)
"""
            tof__mtokq += (
                f'    out_arr_list_{isz__wssl}[i] = out_arr_{isz__wssl}\n')
            tof__mtokq += (
                f'  T2 = set_table_block(T2, out_arr_list_{isz__wssl}, {isz__wssl})\n'
                )
        tof__mtokq += (
            f'  length = T._len if bodo.get_rank() == root or allgather else 0\n'
            )
        tof__mtokq += f'  T2 = set_table_len(T2, length)\n'
        tof__mtokq += f'  return T2\n'
        iwyn__tvoov = {}
        exec(tof__mtokq, ynvql__dmk, iwyn__tvoov)
        yevw__cose = iwyn__tvoov['impl_table']
        return yevw__cose
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        vvoog__omj = len(data.columns)
        if vvoog__omj == 0:

            def impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
                index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data
                    )
                siwf__xrbql = bodo.gatherv(index, allgather, warn_if_rep, root)
                return bodo.hiframes.pd_dataframe_ext.init_dataframe((),
                    siwf__xrbql, ())
            return impl
        elka__dbf = ', '.join(f'g_data_{i}' for i in range(vvoog__omj))
        phbm__ghkvj = bodo.utils.transform.gen_const_tup(data.columns)
        tof__mtokq = (
            'def impl_df(data, allgather=False, warn_if_rep=True, root={}):\n'
            .format(MPI_ROOT))
        if data.is_table_format:
            from bodo.transforms.distributed_analysis import Distribution
            uhyy__hnukz = bodo.hiframes.pd_dataframe_ext.DataFrameType(data
                .data, data.index, data.columns, Distribution.REP, True)
            ynvql__dmk = {'bodo': bodo, 'df_type': uhyy__hnukz}
            elka__dbf = 'T2'
            phbm__ghkvj = 'df_type'
            tof__mtokq += (
                '  T = bodo.hiframes.pd_dataframe_ext.get_dataframe_table(data)\n'
                )
            tof__mtokq += (
                '  T2 = bodo.gatherv(T, allgather, warn_if_rep, root)\n')
        else:
            ynvql__dmk = {'bodo': bodo}
            for i in range(vvoog__omj):
                tof__mtokq += (
                    """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                    .format(i, i))
                tof__mtokq += (
                    '  g_data_{} = bodo.gatherv(data_{}, allgather, warn_if_rep, root)\n'
                    .format(i, i))
        tof__mtokq += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        tof__mtokq += (
            '  g_index = bodo.gatherv(index, allgather, warn_if_rep, root)\n')
        tof__mtokq += (
            """  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})
"""
            .format(elka__dbf, phbm__ghkvj))
        iwyn__tvoov = {}
        exec(tof__mtokq, ynvql__dmk, iwyn__tvoov)
        elzcj__tfpqf = iwyn__tvoov['impl_df']
        return elzcj__tfpqf
    if isinstance(data, ArrayItemArrayType):
        xygnd__rds = np.int32(numba_to_c_type(types.int32))
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))

        def gatherv_array_item_arr_impl(data, allgather=False, warn_if_rep=
            True, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            kzbkd__anq = bodo.libs.array_item_arr_ext.get_offsets(data)
            utxph__oim = bodo.libs.array_item_arr_ext.get_data(data)
            utxph__oim = utxph__oim[:kzbkd__anq[-1]]
            zuw__khm = bodo.libs.array_item_arr_ext.get_null_bitmap(data)
            hahwz__ytww = len(data)
            vxv__sezi = np.empty(hahwz__ytww, np.uint32)
            eezpf__yolz = hahwz__ytww + 7 >> 3
            for i in range(hahwz__ytww):
                vxv__sezi[i] = kzbkd__anq[i + 1] - kzbkd__anq[i]
            recv_counts = gather_scalar(np.int32(hahwz__ytww), allgather,
                root=root)
            jdgpf__ctpkb = recv_counts.sum()
            rqi__numx = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            svrxa__snm = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                rqi__numx = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for whqw__wrjx in range(len(recv_counts)):
                    recv_counts_nulls[whqw__wrjx] = recv_counts[whqw__wrjx
                        ] + 7 >> 3
                svrxa__snm = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            nwmm__ykq = np.empty(jdgpf__ctpkb + 1, np.uint32)
            ihh__vlrp = bodo.gatherv(utxph__oim, allgather, warn_if_rep, root)
            cclfw__thw = np.empty(jdgpf__ctpkb + 7 >> 3, np.uint8)
            c_gatherv(vxv__sezi.ctypes, np.int32(hahwz__ytww), nwmm__ykq.
                ctypes, recv_counts.ctypes, rqi__numx.ctypes, xygnd__rds,
                allgather, np.int32(root))
            c_gatherv(zuw__khm.ctypes, np.int32(eezpf__yolz),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, svrxa__snm
                .ctypes, oxfne__dcg, allgather, np.int32(root))
            dummy_use(data)
            zfu__cyq = np.empty(jdgpf__ctpkb + 1, np.uint64)
            convert_len_arr_to_offset(nwmm__ykq.ctypes, zfu__cyq.ctypes,
                jdgpf__ctpkb)
            copy_gathered_null_bytes(cclfw__thw.ctypes, tmp_null_bytes,
                recv_counts_nulls, recv_counts)
            out_arr = bodo.libs.array_item_arr_ext.init_array_item_array(
                jdgpf__ctpkb, ihh__vlrp, zfu__cyq, cclfw__thw)
            return out_arr
        return gatherv_array_item_arr_impl
    if isinstance(data, StructArrayType):
        vfjve__ytjp = data.names
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))

        def impl_struct_arr(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            cnlb__urxft = bodo.libs.struct_arr_ext.get_data(data)
            xsess__vqzm = bodo.libs.struct_arr_ext.get_null_bitmap(data)
            vawh__sfj = bodo.gatherv(cnlb__urxft, allgather=allgather, root
                =root)
            rank = bodo.libs.distributed_api.get_rank()
            hahwz__ytww = len(data)
            eezpf__yolz = hahwz__ytww + 7 >> 3
            recv_counts = gather_scalar(np.int32(hahwz__ytww), allgather,
                root=root)
            jdgpf__ctpkb = recv_counts.sum()
            tcp__etew = np.empty(jdgpf__ctpkb + 7 >> 3, np.uint8)
            recv_counts_nulls = np.empty(1, np.int32)
            svrxa__snm = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                svrxa__snm = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(xsess__vqzm.ctypes, np.int32(eezpf__yolz),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, svrxa__snm
                .ctypes, oxfne__dcg, allgather, np.int32(root))
            copy_gathered_null_bytes(tcp__etew.ctypes, tmp_null_bytes,
                recv_counts_nulls, recv_counts)
            return bodo.libs.struct_arr_ext.init_struct_arr(vawh__sfj,
                tcp__etew, vfjve__ytjp)
        return impl_struct_arr
    if data == binary_array_type:

        def impl_bin_arr(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            sqxe__snrb = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.binary_arr_ext.init_binary_arr(sqxe__snrb)
        return impl_bin_arr
    if isinstance(data, TupleArrayType):

        def impl_tuple_arr(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            sqxe__snrb = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.tuple_arr_ext.init_tuple_arr(sqxe__snrb)
        return impl_tuple_arr
    if isinstance(data, MapArrayType):

        def impl_map_arr(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            sqxe__snrb = bodo.gatherv(data._data, allgather, warn_if_rep, root)
            return bodo.libs.map_arr_ext.init_map_arr(sqxe__snrb)
        return impl_map_arr
    if isinstance(data, CSRMatrixType):

        def impl_csr_matrix(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            sqxe__snrb = bodo.gatherv(data.data, allgather, warn_if_rep, root)
            njma__wpel = bodo.gatherv(data.indices, allgather, warn_if_rep,
                root)
            macb__bwst = bodo.gatherv(data.indptr, allgather, warn_if_rep, root
                )
            pmvxa__byxzn = gather_scalar(data.shape[0], allgather, root=root)
            xsv__zai = pmvxa__byxzn.sum()
            vvoog__omj = bodo.libs.distributed_api.dist_reduce(data.shape[1
                ], np.int32(Reduce_Type.Max.value))
            qasa__ixc = np.empty(xsv__zai + 1, np.int64)
            njma__wpel = njma__wpel.astype(np.int64)
            qasa__ixc[0] = 0
            ifwbf__rlebt = 1
            buu__sva = 0
            for rmc__gmx in pmvxa__byxzn:
                for rkc__xsm in range(rmc__gmx):
                    xoi__pcu = macb__bwst[buu__sva + 1] - macb__bwst[buu__sva]
                    qasa__ixc[ifwbf__rlebt] = qasa__ixc[ifwbf__rlebt - 1
                        ] + xoi__pcu
                    ifwbf__rlebt += 1
                    buu__sva += 1
                buu__sva += 1
            return bodo.libs.csr_matrix_ext.init_csr_matrix(sqxe__snrb,
                njma__wpel, qasa__ixc, (xsv__zai, vvoog__omj))
        return impl_csr_matrix
    if isinstance(data, types.BaseTuple):
        tof__mtokq = (
            'def impl_tuple(data, allgather=False, warn_if_rep=True, root={}):\n'
            .format(MPI_ROOT))
        tof__mtokq += '  return ({}{})\n'.format(', '.join(
            'bodo.gatherv(data[{}], allgather, warn_if_rep, root)'.format(i
            ) for i in range(len(data))), ',' if len(data) > 0 else '')
        iwyn__tvoov = {}
        exec(tof__mtokq, {'bodo': bodo}, iwyn__tvoov)
        izih__gor = iwyn__tvoov['impl_tuple']
        return izih__gor
    if data is types.none:
        return (lambda data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT: None)
    raise BodoError('gatherv() not available for {}'.format(data))


@numba.generated_jit(nopython=True)
def rebalance(data, dests=None, random=False, random_seed=None, parallel=False
    ):
    bodo.hiframes.pd_dataframe_ext.check_runtime_cols_unsupported(data,
        'bodo.rebalance()')
    tof__mtokq = (
        'def impl(data, dests=None, random=False, random_seed=None, parallel=False):\n'
        )
    tof__mtokq += '    if random:\n'
    tof__mtokq += '        if random_seed is None:\n'
    tof__mtokq += '            random = 1\n'
    tof__mtokq += '        else:\n'
    tof__mtokq += '            random = 2\n'
    tof__mtokq += '    if random_seed is None:\n'
    tof__mtokq += '        random_seed = -1\n'
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        krdi__flc = data
        vvoog__omj = len(krdi__flc.columns)
        for i in range(vvoog__omj):
            tof__mtokq += f"""    data_{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {i})
"""
        tof__mtokq += """    ind_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data))
"""
        elka__dbf = ', '.join(f'data_{i}' for i in range(vvoog__omj))
        tof__mtokq += ('    info_list_total = [{}, array_to_info(ind_arr)]\n'
            .format(', '.join('array_to_info(data_{})'.format(rupo__vjh) for
            rupo__vjh in range(vvoog__omj))))
        tof__mtokq += (
            '    table_total = arr_info_list_to_table(info_list_total)\n')
        tof__mtokq += '    if dests is None:\n'
        tof__mtokq += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        tof__mtokq += '    else:\n'
        tof__mtokq += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        for xdumv__ktclh in range(vvoog__omj):
            tof__mtokq += (
                """    out_arr_{0} = info_to_array(info_from_table(out_table, {0}), data_{0})
"""
                .format(xdumv__ktclh))
        tof__mtokq += (
            """    out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)
"""
            .format(vvoog__omj))
        tof__mtokq += '    delete_table(out_table)\n'
        tof__mtokq += '    if parallel:\n'
        tof__mtokq += '        delete_table(table_total)\n'
        elka__dbf = ', '.join('out_arr_{}'.format(i) for i in range(vvoog__omj)
            )
        phbm__ghkvj = bodo.utils.transform.gen_const_tup(krdi__flc.columns)
        index = 'bodo.utils.conversion.index_from_array(out_arr_index)'
        tof__mtokq += (
            '    return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), {}, {})\n'
            .format(elka__dbf, index, phbm__ghkvj))
    elif isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):
        tof__mtokq += (
            '    data_0 = bodo.hiframes.pd_series_ext.get_series_data(data)\n')
        tof__mtokq += """    ind_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(data))
"""
        tof__mtokq += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(data)\n')
        tof__mtokq += """    table_total = arr_info_list_to_table([array_to_info(data_0), array_to_info(ind_arr)])
"""
        tof__mtokq += '    if dests is None:\n'
        tof__mtokq += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        tof__mtokq += '    else:\n'
        tof__mtokq += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        tof__mtokq += (
            '    out_arr_0 = info_to_array(info_from_table(out_table, 0), data_0)\n'
            )
        tof__mtokq += (
            '    out_arr_index = info_to_array(info_from_table(out_table, 1), ind_arr)\n'
            )
        tof__mtokq += '    delete_table(out_table)\n'
        tof__mtokq += '    if parallel:\n'
        tof__mtokq += '        delete_table(table_total)\n'
        index = 'bodo.utils.conversion.index_from_array(out_arr_index)'
        tof__mtokq += f"""    return bodo.hiframes.pd_series_ext.init_series(out_arr_0, {index}, name)
"""
    elif isinstance(data, types.Array):
        assert is_overload_false(random
            ), 'Call random_shuffle instead of rebalance'
        tof__mtokq += '    if not parallel:\n'
        tof__mtokq += '        return data\n'
        tof__mtokq += """    dim0_global_size = bodo.libs.distributed_api.dist_reduce(data.shape[0], np.int32(bodo.libs.distributed_api.Reduce_Type.Sum.value))
"""
        tof__mtokq += '    if dests is None:\n'
        tof__mtokq += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, bodo.get_size(), bodo.get_rank())
"""
        tof__mtokq += '    elif bodo.get_rank() not in dests:\n'
        tof__mtokq += '        dim0_local_size = 0\n'
        tof__mtokq += '    else:\n'
        tof__mtokq += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, len(dests), dests.index(bodo.get_rank()))
"""
        tof__mtokq += """    out = np.empty((dim0_local_size,) + tuple(data.shape[1:]), dtype=data.dtype)
"""
        tof__mtokq += """    bodo.libs.distributed_api.dist_oneD_reshape_shuffle(out, data, dim0_global_size, dests)
"""
        tof__mtokq += '    return out\n'
    elif bodo.utils.utils.is_array_typ(data, False):
        tof__mtokq += (
            '    table_total = arr_info_list_to_table([array_to_info(data)])\n'
            )
        tof__mtokq += '    if dests is None:\n'
        tof__mtokq += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        tof__mtokq += '    else:\n'
        tof__mtokq += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        tof__mtokq += (
            '    out_arr = info_to_array(info_from_table(out_table, 0), data)\n'
            )
        tof__mtokq += '    delete_table(out_table)\n'
        tof__mtokq += '    if parallel:\n'
        tof__mtokq += '        delete_table(table_total)\n'
        tof__mtokq += '    return out_arr\n'
    else:
        raise BodoError(f'Type {data} not supported for bodo.rebalance')
    iwyn__tvoov = {}
    exec(tof__mtokq, {'np': np, 'bodo': bodo, 'array_to_info': bodo.libs.
        array.array_to_info, 'shuffle_renormalization': bodo.libs.array.
        shuffle_renormalization, 'shuffle_renormalization_group': bodo.libs
        .array.shuffle_renormalization_group, 'arr_info_list_to_table':
        bodo.libs.array.arr_info_list_to_table, 'info_from_table': bodo.
        libs.array.info_from_table, 'info_to_array': bodo.libs.array.
        info_to_array, 'delete_table': bodo.libs.array.delete_table},
        iwyn__tvoov)
    impl = iwyn__tvoov['impl']
    return impl


@numba.generated_jit(nopython=True)
def random_shuffle(data, seed=None, dests=None, parallel=False):
    tof__mtokq = 'def impl(data, seed=None, dests=None, parallel=False):\n'
    if isinstance(data, types.Array):
        if not is_overload_none(dests):
            raise BodoError('not supported')
        tof__mtokq += '    if seed is None:\n'
        tof__mtokq += """        seed = bodo.libs.distributed_api.bcast_scalar(np.random.randint(0, 2**31))
"""
        tof__mtokq += '    np.random.seed(seed)\n'
        tof__mtokq += '    if not parallel:\n'
        tof__mtokq += '        data = data.copy()\n'
        tof__mtokq += '        np.random.shuffle(data)\n'
        tof__mtokq += '        return data\n'
        tof__mtokq += '    else:\n'
        tof__mtokq += """        dim0_global_size = bodo.libs.distributed_api.dist_reduce(data.shape[0], np.int32(bodo.libs.distributed_api.Reduce_Type.Sum.value))
"""
        tof__mtokq += '        permutation = np.arange(dim0_global_size)\n'
        tof__mtokq += '        np.random.shuffle(permutation)\n'
        tof__mtokq += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, bodo.get_size(), bodo.get_rank())
"""
        tof__mtokq += """        output = np.empty((dim0_local_size,) + tuple(data.shape[1:]), dtype=data.dtype)
"""
        tof__mtokq += (
            '        dtype_size = bodo.io.np_io.get_dtype_size(data.dtype)\n')
        tof__mtokq += """        bodo.libs.distributed_api.dist_permutation_array_index(output, dim0_global_size, dtype_size, data, permutation, len(permutation))
"""
        tof__mtokq += '        return output\n'
    else:
        tof__mtokq += """    return bodo.libs.distributed_api.rebalance(data, dests=dests, random=True, random_seed=seed, parallel=parallel)
"""
    iwyn__tvoov = {}
    exec(tof__mtokq, {'np': np, 'bodo': bodo}, iwyn__tvoov)
    impl = iwyn__tvoov['impl']
    return impl


@numba.generated_jit(nopython=True)
def allgatherv(data, warn_if_rep=True, root=MPI_ROOT):
    return lambda data, warn_if_rep=True, root=MPI_ROOT: gatherv(data, True,
        warn_if_rep, root)


@numba.njit
def get_scatter_null_bytes_buff(null_bitmap_ptr, sendcounts, sendcounts_nulls):
    if bodo.get_rank() != MPI_ROOT:
        return np.empty(1, np.uint8)
    wek__xhggw = np.empty(sendcounts_nulls.sum(), np.uint8)
    jeqlt__ohhm = 0
    suvw__asb = 0
    for pih__joz in range(len(sendcounts)):
        lubu__aiec = sendcounts[pih__joz]
        eezpf__yolz = sendcounts_nulls[pih__joz]
        pxpg__fya = wek__xhggw[jeqlt__ohhm:jeqlt__ohhm + eezpf__yolz]
        for avjd__txq in range(lubu__aiec):
            set_bit_to_arr(pxpg__fya, avjd__txq, get_bit_bitmap(
                null_bitmap_ptr, suvw__asb))
            suvw__asb += 1
        jeqlt__ohhm += eezpf__yolz
    return wek__xhggw


def _bcast_dtype(data, root=MPI_ROOT):
    try:
        from mpi4py import MPI
    except:
        raise BodoError('mpi4py is required for scatterv')
    xzgsu__jbgxc = MPI.COMM_WORLD
    data = xzgsu__jbgxc.bcast(data, root)
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
    omlu__dngax = data.ndim
    dtype = data.dtype
    if dtype == types.NPDatetime('ns'):
        dtype = np.dtype('datetime64[ns]')
    elif dtype == types.NPTimedelta('ns'):
        dtype = np.dtype('timedelta64[ns]')
    phty__ymi = (0,) * omlu__dngax

    def scatterv_arr_impl(data, send_counts=None, warn_if_dist=True):
        rank = bodo.libs.distributed_api.get_rank()
        n_pes = bodo.libs.distributed_api.get_size()
        aij__xjigz = np.ascontiguousarray(data)
        bmxmk__vwhq = data.ctypes
        sphx__uqnrm = phty__ymi
        if rank == MPI_ROOT:
            sphx__uqnrm = aij__xjigz.shape
        sphx__uqnrm = bcast_tuple(sphx__uqnrm)
        qen__sklm = get_tuple_prod(sphx__uqnrm[1:])
        send_counts = _get_scatterv_send_counts(send_counts, n_pes,
            sphx__uqnrm[0])
        send_counts *= qen__sklm
        hahwz__ytww = send_counts[rank]
        omp__gkqe = np.empty(hahwz__ytww, dtype)
        rqi__numx = bodo.ir.join.calc_disp(send_counts)
        c_scatterv(bmxmk__vwhq, send_counts.ctypes, rqi__numx.ctypes,
            omp__gkqe.ctypes, np.int32(hahwz__ytww), np.int32(typ_val))
        return omp__gkqe.reshape((-1,) + sphx__uqnrm[1:])
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
        ybxsg__ltcw = '{}Int{}'.format('' if dtype.dtype.signed else 'U',
            dtype.dtype.bitwidth)
        return pd.array([3], ybxsg__ltcw)
    if dtype == boolean_array:
        return pd.array([True], 'boolean')
    if isinstance(dtype, DecimalArrayType):
        return np.array([Decimal('32.1')])
    if dtype == datetime_date_array_type:
        return np.array([datetime.date(2011, 8, 9)])
    if dtype == datetime_timedelta_array_type:
        return np.array([datetime.timedelta(33)])
    if bodo.hiframes.pd_index_ext.is_pd_index_type(dtype):
        ozeq__qand = _get_name_value_for_type(dtype.name_typ)
        if isinstance(dtype, bodo.hiframes.pd_index_ext.RangeIndexType):
            return pd.RangeIndex(1, name=ozeq__qand)
        yyi__crfli = bodo.utils.typing.get_index_data_arr_types(dtype)[0]
        arr = get_value_for_type(yyi__crfli)
        return pd.Index(arr, name=ozeq__qand)
    if isinstance(dtype, bodo.hiframes.pd_multi_index_ext.MultiIndexType):
        import pyarrow as pa
        ozeq__qand = _get_name_value_for_type(dtype.name_typ)
        vfjve__ytjp = tuple(_get_name_value_for_type(t) for t in dtype.
            names_typ)
        yhrcd__fsvv = tuple(get_value_for_type(t) for t in dtype.array_types)
        yhrcd__fsvv = tuple(a.to_numpy(False) if isinstance(a, pa.Array) else
            a for a in yhrcd__fsvv)
        val = pd.MultiIndex.from_arrays(yhrcd__fsvv, names=vfjve__ytjp)
        val.name = ozeq__qand
        return val
    if isinstance(dtype, bodo.hiframes.pd_series_ext.SeriesType):
        ozeq__qand = _get_name_value_for_type(dtype.name_typ)
        arr = get_value_for_type(dtype.data)
        index = get_value_for_type(dtype.index)
        return pd.Series(arr, index, name=ozeq__qand)
    if isinstance(dtype, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        yhrcd__fsvv = tuple(get_value_for_type(t) for t in dtype.data)
        index = get_value_for_type(dtype.index)
        return pd.DataFrame({ozeq__qand: arr for ozeq__qand, arr in zip(
            dtype.columns, yhrcd__fsvv)}, index)
    if isinstance(dtype, CategoricalArrayType):
        return pd.Categorical.from_codes([0], dtype.dtype.categories)
    if isinstance(dtype, types.BaseTuple):
        return tuple(get_value_for_type(t) for t in dtype.types)
    if isinstance(dtype, ArrayItemArrayType):
        return pd.Series([get_value_for_type(dtype.dtype),
            get_value_for_type(dtype.dtype)]).values
    if isinstance(dtype, IntervalArrayType):
        yyi__crfli = get_value_for_type(dtype.arr_type)
        return pd.arrays.IntervalArray([pd.Interval(yyi__crfli[0],
            yyi__crfli[0])])
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
        xygnd__rds = np.int32(numba_to_c_type(types.int32))
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))
        if data == binary_array_type:
            ajt__ayjg = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
        else:
            ajt__ayjg = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
        tof__mtokq = f"""def impl(
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
            recv_arr = {ajt__ayjg}(n_loc, n_loc_char)

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
        iwyn__tvoov = dict()
        exec(tof__mtokq, {'bodo': bodo, 'np': np, 'int32_typ_enum':
            xygnd__rds, 'char_typ_enum': oxfne__dcg, 'decode_if_dict_array':
            decode_if_dict_array}, iwyn__tvoov)
        impl = iwyn__tvoov['impl']
        return impl
    if isinstance(data, ArrayItemArrayType):
        xygnd__rds = np.int32(numba_to_c_type(types.int32))
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))

        def scatterv_array_item_impl(data, send_counts=None, warn_if_dist=True
            ):
            dycsr__oxzcp = bodo.libs.array_item_arr_ext.get_offsets(data)
            fala__snj = bodo.libs.array_item_arr_ext.get_data(data)
            fala__snj = fala__snj[:dycsr__oxzcp[-1]]
            pnqph__qgmsd = bodo.libs.array_item_arr_ext.get_null_bitmap(data)
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            sbve__yow = bcast_scalar(len(data))
            rdzx__rjsj = np.empty(len(data), np.uint32)
            for i in range(len(data)):
                rdzx__rjsj[i] = dycsr__oxzcp[i + 1] - dycsr__oxzcp[i]
            send_counts = _get_scatterv_send_counts(send_counts, n_pes,
                sbve__yow)
            rqi__numx = bodo.ir.join.calc_disp(send_counts)
            fqpil__pth = np.empty(n_pes, np.int32)
            if rank == 0:
                elvs__ruas = 0
                for i in range(n_pes):
                    pbu__hvjdi = 0
                    for rkc__xsm in range(send_counts[i]):
                        pbu__hvjdi += rdzx__rjsj[elvs__ruas]
                        elvs__ruas += 1
                    fqpil__pth[i] = pbu__hvjdi
            bcast(fqpil__pth)
            aaon__xykor = np.empty(n_pes, np.int32)
            for i in range(n_pes):
                aaon__xykor[i] = send_counts[i] + 7 >> 3
            svrxa__snm = bodo.ir.join.calc_disp(aaon__xykor)
            hahwz__ytww = send_counts[rank]
            hbw__twyjp = np.empty(hahwz__ytww + 1, np_offset_type)
            ith__gde = bodo.libs.distributed_api.scatterv_impl(fala__snj,
                fqpil__pth)
            awqb__wufh = hahwz__ytww + 7 >> 3
            mtcvu__qsa = np.empty(awqb__wufh, np.uint8)
            zrbir__wdft = np.empty(hahwz__ytww, np.uint32)
            c_scatterv(rdzx__rjsj.ctypes, send_counts.ctypes, rqi__numx.
                ctypes, zrbir__wdft.ctypes, np.int32(hahwz__ytww), xygnd__rds)
            convert_len_arr_to_offset(zrbir__wdft.ctypes, hbw__twyjp.ctypes,
                hahwz__ytww)
            dcv__kashw = get_scatter_null_bytes_buff(pnqph__qgmsd.ctypes,
                send_counts, aaon__xykor)
            c_scatterv(dcv__kashw.ctypes, aaon__xykor.ctypes, svrxa__snm.
                ctypes, mtcvu__qsa.ctypes, np.int32(awqb__wufh), oxfne__dcg)
            return bodo.libs.array_item_arr_ext.init_array_item_array(
                hahwz__ytww, ith__gde, hbw__twyjp, mtcvu__qsa)
        return scatterv_array_item_impl
    if isinstance(data, (IntegerArrayType, DecimalArrayType)) or data in (
        boolean_array, datetime_date_array_type):
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))
        if isinstance(data, IntegerArrayType):
            dvk__cgyu = bodo.libs.int_arr_ext.init_integer_array
        if isinstance(data, DecimalArrayType):
            precision = data.precision
            scale = data.scale
            dvk__cgyu = numba.njit(no_cpython_wrapper=True)(lambda d, b:
                bodo.libs.decimal_arr_ext.init_decimal_array(d, b,
                precision, scale))
        if data == boolean_array:
            dvk__cgyu = bodo.libs.bool_arr_ext.init_bool_array
        if data == datetime_date_array_type:
            dvk__cgyu = (bodo.hiframes.datetime_date_ext.
                init_datetime_date_array)

        def scatterv_impl_int_arr(data, send_counts=None, warn_if_dist=True):
            n_pes = bodo.libs.distributed_api.get_size()
            aij__xjigz = data._data
            xsess__vqzm = data._null_bitmap
            zafbs__incq = len(aij__xjigz)
            iqvw__knq = _scatterv_np(aij__xjigz, send_counts)
            sbve__yow = bcast_scalar(zafbs__incq)
            rgxw__xsv = len(iqvw__knq) + 7 >> 3
            hcdww__aqkx = np.empty(rgxw__xsv, np.uint8)
            send_counts = _get_scatterv_send_counts(send_counts, n_pes,
                sbve__yow)
            aaon__xykor = np.empty(n_pes, np.int32)
            for i in range(n_pes):
                aaon__xykor[i] = send_counts[i] + 7 >> 3
            svrxa__snm = bodo.ir.join.calc_disp(aaon__xykor)
            dcv__kashw = get_scatter_null_bytes_buff(xsess__vqzm.ctypes,
                send_counts, aaon__xykor)
            c_scatterv(dcv__kashw.ctypes, aaon__xykor.ctypes, svrxa__snm.
                ctypes, hcdww__aqkx.ctypes, np.int32(rgxw__xsv), oxfne__dcg)
            return dvk__cgyu(iqvw__knq, hcdww__aqkx)
        return scatterv_impl_int_arr
    if isinstance(data, IntervalArrayType):

        def impl_interval_arr(data, send_counts=None, warn_if_dist=True):
            bmal__mnn = bodo.libs.distributed_api.scatterv_impl(data._left,
                send_counts)
            fdcup__hjoj = bodo.libs.distributed_api.scatterv_impl(data.
                _right, send_counts)
            return bodo.libs.interval_arr_ext.init_interval_array(bmal__mnn,
                fdcup__hjoj)
        return impl_interval_arr
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):

        def impl_range_index(data, send_counts=None, warn_if_dist=True):
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            start = data._start
            stop = data._stop
            lbv__jyus = data._step
            ozeq__qand = data._name
            ozeq__qand = bcast_scalar(ozeq__qand)
            start = bcast_scalar(start)
            stop = bcast_scalar(stop)
            lbv__jyus = bcast_scalar(lbv__jyus)
            wox__vgmwr = bodo.libs.array_kernels.calc_nitems(start, stop,
                lbv__jyus)
            chunk_start = bodo.libs.distributed_api.get_start(wox__vgmwr,
                n_pes, rank)
            chunk_count = bodo.libs.distributed_api.get_node_portion(wox__vgmwr
                , n_pes, rank)
            fzpm__ffhq = start + lbv__jyus * chunk_start
            wsfyl__tgwc = start + lbv__jyus * (chunk_start + chunk_count)
            wsfyl__tgwc = min(wsfyl__tgwc, stop)
            return bodo.hiframes.pd_index_ext.init_range_index(fzpm__ffhq,
                wsfyl__tgwc, lbv__jyus, ozeq__qand)
        return impl_range_index
    if isinstance(data, bodo.hiframes.pd_index_ext.PeriodIndexType):
        velyw__hoez = data.freq

        def impl_period_index(data, send_counts=None, warn_if_dist=True):
            aij__xjigz = data._data
            ozeq__qand = data._name
            ozeq__qand = bcast_scalar(ozeq__qand)
            arr = bodo.libs.distributed_api.scatterv_impl(aij__xjigz,
                send_counts)
            return bodo.hiframes.pd_index_ext.init_period_index(arr,
                ozeq__qand, velyw__hoez)
        return impl_period_index
    if bodo.hiframes.pd_index_ext.is_pd_index_type(data):

        def impl_pd_index(data, send_counts=None, warn_if_dist=True):
            aij__xjigz = data._data
            ozeq__qand = data._name
            ozeq__qand = bcast_scalar(ozeq__qand)
            arr = bodo.libs.distributed_api.scatterv_impl(aij__xjigz,
                send_counts)
            return bodo.utils.conversion.index_from_array(arr, ozeq__qand)
        return impl_pd_index
    if isinstance(data, bodo.hiframes.pd_multi_index_ext.MultiIndexType):

        def impl_multi_index(data, send_counts=None, warn_if_dist=True):
            sqxe__snrb = bodo.libs.distributed_api.scatterv_impl(data._data,
                send_counts)
            ozeq__qand = bcast_scalar(data._name)
            vfjve__ytjp = bcast_tuple(data._names)
            return bodo.hiframes.pd_multi_index_ext.init_multi_index(sqxe__snrb
                , vfjve__ytjp, ozeq__qand)
        return impl_multi_index
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl_series(data, send_counts=None, warn_if_dist=True):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            ozeq__qand = bodo.hiframes.pd_series_ext.get_series_name(data)
            fok__chn = bcast_scalar(ozeq__qand)
            out_arr = bodo.libs.distributed_api.scatterv_impl(arr, send_counts)
            szuu__fjr = bodo.libs.distributed_api.scatterv_impl(index,
                send_counts)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                szuu__fjr, fok__chn)
        return impl_series
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        vvoog__omj = len(data.columns)
        elka__dbf = ', '.join('g_data_{}'.format(i) for i in range(vvoog__omj))
        phbm__ghkvj = bodo.utils.transform.gen_const_tup(data.columns)
        tof__mtokq = (
            'def impl_df(data, send_counts=None, warn_if_dist=True):\n')
        for i in range(vvoog__omj):
            tof__mtokq += (
                """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                .format(i, i))
            tof__mtokq += (
                """  g_data_{} = bodo.libs.distributed_api.scatterv_impl(data_{}, send_counts)
"""
                .format(i, i))
        tof__mtokq += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        tof__mtokq += (
            '  g_index = bodo.libs.distributed_api.scatterv_impl(index, send_counts)\n'
            )
        tof__mtokq += (
            """  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})
"""
            .format(elka__dbf, phbm__ghkvj))
        iwyn__tvoov = {}
        exec(tof__mtokq, {'bodo': bodo}, iwyn__tvoov)
        elzcj__tfpqf = iwyn__tvoov['impl_df']
        return elzcj__tfpqf
    if isinstance(data, CategoricalArrayType):

        def impl_cat(data, send_counts=None, warn_if_dist=True):
            szwuv__rpai = bodo.libs.distributed_api.scatterv_impl(data.
                codes, send_counts)
            return bodo.hiframes.pd_categorical_ext.init_categorical_array(
                szwuv__rpai, data.dtype)
        return impl_cat
    if isinstance(data, types.BaseTuple):
        tof__mtokq = (
            'def impl_tuple(data, send_counts=None, warn_if_dist=True):\n')
        tof__mtokq += '  return ({}{})\n'.format(', '.join(
            'bodo.libs.distributed_api.scatterv_impl(data[{}], send_counts)'
            .format(i) for i in range(len(data))), ',' if len(data) > 0 else ''
            )
        iwyn__tvoov = {}
        exec(tof__mtokq, {'bodo': bodo}, iwyn__tvoov)
        izih__gor = iwyn__tvoov['impl_tuple']
        return izih__gor
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
        qfqvd__ocr = np.int32(numba_to_c_type(offset_type))
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))

        def bcast_str_impl(data, root=MPI_ROOT):
            data = decode_if_dict_array(data)
            hahwz__ytww = len(data)
            eyqvx__mwsss = num_total_chars(data)
            assert hahwz__ytww < INT_MAX
            assert eyqvx__mwsss < INT_MAX
            jsxcb__end = get_offset_ptr(data)
            bmxmk__vwhq = get_data_ptr(data)
            null_bitmap_ptr = get_null_bitmap_ptr(data)
            eezpf__yolz = hahwz__ytww + 7 >> 3
            c_bcast(jsxcb__end, np.int32(hahwz__ytww + 1), qfqvd__ocr, np.
                array([-1]).ctypes, 0, np.int32(root))
            c_bcast(bmxmk__vwhq, np.int32(eyqvx__mwsss), oxfne__dcg, np.
                array([-1]).ctypes, 0, np.int32(root))
            c_bcast(null_bitmap_ptr, np.int32(eezpf__yolz), oxfne__dcg, np.
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
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))

        def impl_str(val, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            if rank != root:
                bbmje__xdoyh = 0
                beb__jnl = np.empty(0, np.uint8).ctypes
            else:
                beb__jnl, bbmje__xdoyh = (bodo.libs.str_ext.
                    unicode_to_utf8_and_len(val))
            bbmje__xdoyh = bodo.libs.distributed_api.bcast_scalar(bbmje__xdoyh,
                root)
            if rank != root:
                inmmn__aurk = np.empty(bbmje__xdoyh + 1, np.uint8)
                inmmn__aurk[bbmje__xdoyh] = 0
                beb__jnl = inmmn__aurk.ctypes
            c_bcast(beb__jnl, np.int32(bbmje__xdoyh), oxfne__dcg, np.array(
                [-1]).ctypes, 0, np.int32(root))
            return bodo.libs.str_arr_ext.decode_utf8(beb__jnl, bbmje__xdoyh)
        return impl_str
    typ_val = numba_to_c_type(val)
    tof__mtokq = f"""def bcast_scalar_impl(val, root={MPI_ROOT}):
  send = np.empty(1, dtype)
  send[0] = val
  c_bcast(send.ctypes, np.int32(1), np.int32({typ_val}), np.array([-1]).ctypes, 0, np.int32(root))
  return send[0]
"""
    dtype = numba.np.numpy_support.as_dtype(val)
    iwyn__tvoov = {}
    exec(tof__mtokq, {'bodo': bodo, 'np': np, 'c_bcast': c_bcast, 'dtype':
        dtype}, iwyn__tvoov)
    btppd__ibuc = iwyn__tvoov['bcast_scalar_impl']
    return btppd__ibuc


@numba.generated_jit(nopython=True)
def bcast_tuple(val, root=MPI_ROOT):
    assert isinstance(val, types.BaseTuple)
    nwp__mvwns = len(val)
    tof__mtokq = f'def bcast_tuple_impl(val, root={MPI_ROOT}):\n'
    tof__mtokq += '  return ({}{})'.format(','.join(
        'bcast_scalar(val[{}], root)'.format(i) for i in range(nwp__mvwns)),
        ',' if nwp__mvwns else '')
    iwyn__tvoov = {}
    exec(tof__mtokq, {'bcast_scalar': bcast_scalar}, iwyn__tvoov)
    qttfm__xwzxs = iwyn__tvoov['bcast_tuple_impl']
    return qttfm__xwzxs


def prealloc_str_for_bcast(arr, root=MPI_ROOT):
    return arr


@overload(prealloc_str_for_bcast, no_unliteral=True)
def prealloc_str_for_bcast_overload(arr, root=MPI_ROOT):
    if arr == string_array_type:

        def prealloc_impl(arr, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            hahwz__ytww = bcast_scalar(len(arr), root)
            wcho__qjace = bcast_scalar(np.int64(num_total_chars(arr)), root)
            if rank != root:
                arr = pre_alloc_string_array(hahwz__ytww, wcho__qjace)
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
        lbv__jyus = slice_index.step
        bfsb__gkf = 0 if lbv__jyus == 1 or start > arr_start else abs(
            lbv__jyus - arr_start % lbv__jyus) % lbv__jyus
        fzpm__ffhq = max(arr_start, slice_index.start) - arr_start + bfsb__gkf
        wsfyl__tgwc = max(slice_index.stop - arr_start, 0)
        return slice(fzpm__ffhq, wsfyl__tgwc, lbv__jyus)
    return impl


def slice_getitem(arr, slice_index, arr_start, total_len):
    return arr[slice_index]


@overload(slice_getitem, no_unliteral=True, jit_options={'cache': True})
def slice_getitem_overload(arr, slice_index, arr_start, total_len):

    def getitem_impl(arr, slice_index, arr_start, total_len):
        lko__ykskh = get_local_slice(slice_index, arr_start, total_len)
        return bodo.utils.conversion.ensure_contig_if_np(arr[lko__ykskh])
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
        mfis__pre = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND
        oxfne__dcg = np.int32(numba_to_c_type(types.uint8))
        jpfqg__dyjr = arr.dtype

        def str_getitem_impl(arr, ind, arr_start, total_len, is_1D):
            if ind >= total_len:
                raise IndexError('index out of bounds')
            arr = decode_if_dict_array(arr)
            ind = ind % total_len
            root = np.int32(0)
            subeq__mnmk = np.int32(10)
            tag = np.int32(11)
            amfl__vtldm = np.zeros(1, np.int64)
            if arr_start <= ind < arr_start + len(arr):
                ind = ind - arr_start
                utxph__oim = arr._data
                yycr__wtim = bodo.libs.array_item_arr_ext.get_offsets_ind(
                    utxph__oim, ind)
                ebiz__ahbqx = bodo.libs.array_item_arr_ext.get_offsets_ind(
                    utxph__oim, ind + 1)
                length = ebiz__ahbqx - yycr__wtim
                hidy__ndr = utxph__oim[ind]
                amfl__vtldm[0] = length
                isend(amfl__vtldm, np.int32(1), root, subeq__mnmk, True)
                isend(hidy__ndr, np.int32(length), root, tag, True)
            rank = bodo.libs.distributed_api.get_rank()
            val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(
                jpfqg__dyjr, mfis__pre, 0, 1)
            qwjpu__mdyy = 0
            if rank == root:
                qwjpu__mdyy = recv(np.int64, ANY_SOURCE, subeq__mnmk)
                val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(
                    jpfqg__dyjr, mfis__pre, qwjpu__mdyy, 1)
                bmxmk__vwhq = bodo.libs.str_ext.get_unicode_or_numpy_data(val)
                _recv(bmxmk__vwhq, np.int32(qwjpu__mdyy), oxfne__dcg,
                    ANY_SOURCE, tag)
            dummy_use(amfl__vtldm)
            qwjpu__mdyy = bcast_scalar(qwjpu__mdyy)
            dummy_use(arr)
            if rank != root:
                val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(
                    jpfqg__dyjr, mfis__pre, qwjpu__mdyy, 1)
            bmxmk__vwhq = bodo.libs.str_ext.get_unicode_or_numpy_data(val)
            c_bcast(bmxmk__vwhq, np.int32(qwjpu__mdyy), oxfne__dcg, np.
                array([-1]).ctypes, 0, np.int32(root))
            val = transform_str_getitem_output(val, qwjpu__mdyy)
            return val
        return str_getitem_impl
    if isinstance(arr, bodo.CategoricalArrayType):
        mmkg__tnuil = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            arr.dtype)

        def cat_getitem_impl(arr, ind, arr_start, total_len, is_1D):
            if ind >= total_len:
                raise IndexError('index out of bounds')
            ind = ind % total_len
            root = np.int32(0)
            tag = np.int32(11)
            send_arr = np.zeros(1, mmkg__tnuil)
            if arr_start <= ind < arr_start + len(arr):
                szwuv__rpai = (bodo.hiframes.pd_categorical_ext.
                    get_categorical_arr_codes(arr))
                data = szwuv__rpai[ind - arr_start]
                send_arr = np.full(1, data, mmkg__tnuil)
                isend(send_arr, np.int32(1), root, tag, True)
            rank = bodo.libs.distributed_api.get_rank()
            val = mmkg__tnuil(-1)
            if rank == root:
                val = recv(mmkg__tnuil, ANY_SOURCE, tag)
            dummy_use(send_arr)
            val = bcast_scalar(val)
            sszz__fqugh = arr.dtype.categories[max(val, 0)]
            return sszz__fqugh
        return cat_getitem_impl
    ktr__xqf = arr.dtype

    def getitem_impl(arr, ind, arr_start, total_len, is_1D):
        if ind >= total_len:
            raise IndexError('index out of bounds')
        ind = ind % total_len
        root = np.int32(0)
        tag = np.int32(11)
        send_arr = np.zeros(1, ktr__xqf)
        if arr_start <= ind < arr_start + len(arr):
            data = arr[ind - arr_start]
            send_arr = np.full(1, data)
            isend(send_arr, np.int32(1), root, tag, True)
        rank = bodo.libs.distributed_api.get_rank()
        val = np.zeros(1, ktr__xqf)[0]
        if rank == root:
            val = recv(ktr__xqf, ANY_SOURCE, tag)
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
    nhkwr__fiuv = get_type_enum(out_data)
    assert typ_enum == nhkwr__fiuv
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
    tof__mtokq = (
        'def f(send_data, out_data, send_counts, recv_counts, send_disp, recv_disp):\n'
        )
    for i in range(count):
        tof__mtokq += (
            """  alltoallv(send_data[{}], out_data[{}], send_counts, recv_counts, send_disp, recv_disp)
"""
            .format(i, i))
    tof__mtokq += '  return\n'
    iwyn__tvoov = {}
    exec(tof__mtokq, {'alltoallv': alltoallv}, iwyn__tvoov)
    caqyl__llrpg = iwyn__tvoov['f']
    return caqyl__llrpg


@numba.njit
def get_start_count(n):
    rank = bodo.libs.distributed_api.get_rank()
    n_pes = bodo.libs.distributed_api.get_size()
    start = bodo.libs.distributed_api.get_start(n, n_pes, rank)
    count = bodo.libs.distributed_api.get_node_portion(n, n_pes, rank)
    return start, count


@numba.njit
def get_start(total_size, pes, rank):
    dud__gvd = total_size % pes
    suc__dbi = (total_size - dud__gvd) // pes
    return rank * suc__dbi + min(rank, dud__gvd)


@numba.njit
def get_end(total_size, pes, rank):
    dud__gvd = total_size % pes
    suc__dbi = (total_size - dud__gvd) // pes
    return (rank + 1) * suc__dbi + min(rank + 1, dud__gvd)


@numba.njit
def get_node_portion(total_size, pes, rank):
    dud__gvd = total_size % pes
    suc__dbi = (total_size - dud__gvd) // pes
    if rank < dud__gvd:
        return suc__dbi + 1
    else:
        return suc__dbi


@numba.generated_jit(nopython=True)
def dist_cumsum(in_arr, out_arr):
    lqqoq__ltnxr = in_arr.dtype(0)
    gfzrj__tkn = np.int32(Reduce_Type.Sum.value)

    def cumsum_impl(in_arr, out_arr):
        pbu__hvjdi = lqqoq__ltnxr
        for tfmlg__taxb in np.nditer(in_arr):
            pbu__hvjdi += tfmlg__taxb.item()
        uxy__fyo = dist_exscan(pbu__hvjdi, gfzrj__tkn)
        for i in range(in_arr.size):
            uxy__fyo += in_arr[i]
            out_arr[i] = uxy__fyo
        return 0
    return cumsum_impl


@numba.generated_jit(nopython=True)
def dist_cumprod(in_arr, out_arr):
    bzcbm__dik = in_arr.dtype(1)
    gfzrj__tkn = np.int32(Reduce_Type.Prod.value)

    def cumprod_impl(in_arr, out_arr):
        pbu__hvjdi = bzcbm__dik
        for tfmlg__taxb in np.nditer(in_arr):
            pbu__hvjdi *= tfmlg__taxb.item()
        uxy__fyo = dist_exscan(pbu__hvjdi, gfzrj__tkn)
        if get_rank() == 0:
            uxy__fyo = bzcbm__dik
        for i in range(in_arr.size):
            uxy__fyo *= in_arr[i]
            out_arr[i] = uxy__fyo
        return 0
    return cumprod_impl


@numba.generated_jit(nopython=True)
def dist_cummin(in_arr, out_arr):
    if isinstance(in_arr.dtype, types.Float):
        bzcbm__dik = np.finfo(in_arr.dtype(1).dtype).max
    else:
        bzcbm__dik = np.iinfo(in_arr.dtype(1).dtype).max
    gfzrj__tkn = np.int32(Reduce_Type.Min.value)

    def cummin_impl(in_arr, out_arr):
        pbu__hvjdi = bzcbm__dik
        for tfmlg__taxb in np.nditer(in_arr):
            pbu__hvjdi = min(pbu__hvjdi, tfmlg__taxb.item())
        uxy__fyo = dist_exscan(pbu__hvjdi, gfzrj__tkn)
        if get_rank() == 0:
            uxy__fyo = bzcbm__dik
        for i in range(in_arr.size):
            uxy__fyo = min(uxy__fyo, in_arr[i])
            out_arr[i] = uxy__fyo
        return 0
    return cummin_impl


@numba.generated_jit(nopython=True)
def dist_cummax(in_arr, out_arr):
    if isinstance(in_arr.dtype, types.Float):
        bzcbm__dik = np.finfo(in_arr.dtype(1).dtype).min
    else:
        bzcbm__dik = np.iinfo(in_arr.dtype(1).dtype).min
    bzcbm__dik = in_arr.dtype(1)
    gfzrj__tkn = np.int32(Reduce_Type.Max.value)

    def cummax_impl(in_arr, out_arr):
        pbu__hvjdi = bzcbm__dik
        for tfmlg__taxb in np.nditer(in_arr):
            pbu__hvjdi = max(pbu__hvjdi, tfmlg__taxb.item())
        uxy__fyo = dist_exscan(pbu__hvjdi, gfzrj__tkn)
        if get_rank() == 0:
            uxy__fyo = bzcbm__dik
        for i in range(in_arr.size):
            uxy__fyo = max(uxy__fyo, in_arr[i])
            out_arr[i] = uxy__fyo
        return 0
    return cummax_impl


_allgather = types.ExternalFunction('allgather', types.void(types.voidptr,
    types.int32, types.voidptr, types.int32))


@numba.njit
def allgather(arr, val):
    zszsz__xjkk = get_type_enum(arr)
    _allgather(arr.ctypes, 1, value_to_ptr(val), zszsz__xjkk)


def dist_return(A):
    return A


def rep_return(A):
    return A


def dist_return_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    wqhd__eijq = args[0]
    if equiv_set.has_shape(wqhd__eijq):
        return ArrayAnalysis.AnalyzeResult(shape=wqhd__eijq, pre=[])
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
        jhrhi__jcl = ','.join(f'_wait(req[{i}], cond)' for i in range(count))
        tof__mtokq = 'def f(req, cond=True):\n'
        tof__mtokq += f'  return {jhrhi__jcl}\n'
        iwyn__tvoov = {}
        exec(tof__mtokq, {'_wait': _wait}, iwyn__tvoov)
        impl = iwyn__tvoov['f']
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
    fzpm__ffhq = max(start, chunk_start)
    wsfyl__tgwc = min(stop, chunk_start + chunk_count)
    ygfbc__blbuh = fzpm__ffhq - chunk_start
    utfwq__dsr = wsfyl__tgwc - chunk_start
    if ygfbc__blbuh < 0 or utfwq__dsr < 0:
        ygfbc__blbuh = 1
        utfwq__dsr = 0
    return ygfbc__blbuh, utfwq__dsr


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
        dud__gvd = 1
        for a in t:
            dud__gvd *= a
        return dud__gvd
    return get_tuple_prod_impl


sig = types.void(types.voidptr, types.voidptr, types.intp, types.intp,
    types.intp, types.intp, types.int32, types.voidptr)
oneD_reshape_shuffle = types.ExternalFunction('oneD_reshape_shuffle', sig)


@numba.njit(no_cpython_wrapper=True, cache=True)
def dist_oneD_reshape_shuffle(lhs, in_arr, new_dim0_global_len, dest_ranks=None
    ):
    dtr__way = np.ascontiguousarray(in_arr)
    tocji__otida = get_tuple_prod(dtr__way.shape[1:])
    knr__tyy = get_tuple_prod(lhs.shape[1:])
    if dest_ranks is not None:
        ikzef__pcaqs = np.array(dest_ranks, dtype=np.int32)
    else:
        ikzef__pcaqs = np.empty(0, dtype=np.int32)
    dtype_size = bodo.io.np_io.get_dtype_size(in_arr.dtype)
    oneD_reshape_shuffle(lhs.ctypes, dtr__way.ctypes, new_dim0_global_len,
        len(in_arr), dtype_size * knr__tyy, dtype_size * tocji__otida, len(
        ikzef__pcaqs), ikzef__pcaqs.ctypes)
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
    cugul__gal = np.ascontiguousarray(rhs)
    qgi__unit = get_tuple_prod(cugul__gal.shape[1:])
    fwhud__riv = dtype_size * qgi__unit
    permutation_array_index(lhs.ctypes, lhs_len, fwhud__riv, cugul__gal.
        ctypes, cugul__gal.shape[0], p.ctypes, p_len)
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
        tof__mtokq = (
            f"""def bcast_scalar_impl(data, comm_ranks, nranks, root={MPI_ROOT}):
  send = np.empty(1, dtype)
  send[0] = data
  c_bcast(send.ctypes, np.int32(1), np.int32({{}}), comm_ranks,ctypes, np.int32({{}}), np.int32(root))
  return send[0]
"""
            .format(typ_val, nranks))
        dtype = numba.np.numpy_support.as_dtype(data)
        iwyn__tvoov = {}
        exec(tof__mtokq, {'bodo': bodo, 'np': np, 'c_bcast': c_bcast,
            'dtype': dtype}, iwyn__tvoov)
        btppd__ibuc = iwyn__tvoov['bcast_scalar_impl']
        return btppd__ibuc
    if isinstance(data, types.Array):
        return lambda data, comm_ranks, nranks, root=MPI_ROOT: _bcast_np(data,
            comm_ranks, nranks, root)
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        vvoog__omj = len(data.columns)
        elka__dbf = ', '.join('g_data_{}'.format(i) for i in range(vvoog__omj))
        phbm__ghkvj = bodo.utils.transform.gen_const_tup(data.columns)
        tof__mtokq = (
            f'def impl_df(data, comm_ranks, nranks, root={MPI_ROOT}):\n')
        for i in range(vvoog__omj):
            tof__mtokq += (
                """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                .format(i, i))
            tof__mtokq += (
                """  g_data_{} = bodo.libs.distributed_api.bcast_comm_impl(data_{}, comm_ranks, nranks, root)
"""
                .format(i, i))
        tof__mtokq += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        tof__mtokq += """  g_index = bodo.libs.distributed_api.bcast_comm_impl(index, comm_ranks, nranks, root)
"""
        tof__mtokq += (
            """  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})
"""
            .format(elka__dbf, phbm__ghkvj))
        iwyn__tvoov = {}
        exec(tof__mtokq, {'bodo': bodo}, iwyn__tvoov)
        elzcj__tfpqf = iwyn__tvoov['impl_df']
        return elzcj__tfpqf
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):

        def impl_range_index(data, comm_ranks, nranks, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            start = data._start
            stop = data._stop
            lbv__jyus = data._step
            ozeq__qand = data._name
            ozeq__qand = bcast_scalar(ozeq__qand, root)
            start = bcast_scalar(start, root)
            stop = bcast_scalar(stop, root)
            lbv__jyus = bcast_scalar(lbv__jyus, root)
            wox__vgmwr = bodo.libs.array_kernels.calc_nitems(start, stop,
                lbv__jyus)
            chunk_start = bodo.libs.distributed_api.get_start(wox__vgmwr,
                n_pes, rank)
            chunk_count = bodo.libs.distributed_api.get_node_portion(wox__vgmwr
                , n_pes, rank)
            fzpm__ffhq = start + lbv__jyus * chunk_start
            wsfyl__tgwc = start + lbv__jyus * (chunk_start + chunk_count)
            wsfyl__tgwc = min(wsfyl__tgwc, stop)
            return bodo.hiframes.pd_index_ext.init_range_index(fzpm__ffhq,
                wsfyl__tgwc, lbv__jyus, ozeq__qand)
        return impl_range_index
    if bodo.hiframes.pd_index_ext.is_pd_index_type(data):

        def impl_pd_index(data, comm_ranks, nranks, root=MPI_ROOT):
            aij__xjigz = data._data
            ozeq__qand = data._name
            arr = bodo.libs.distributed_api.bcast_comm_impl(aij__xjigz,
                comm_ranks, nranks, root)
            return bodo.utils.conversion.index_from_array(arr, ozeq__qand)
        return impl_pd_index
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl_series(data, comm_ranks, nranks, root=MPI_ROOT):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            ozeq__qand = bodo.hiframes.pd_series_ext.get_series_name(data)
            fok__chn = bodo.libs.distributed_api.bcast_comm_impl(ozeq__qand,
                comm_ranks, nranks, root)
            out_arr = bodo.libs.distributed_api.bcast_comm_impl(arr,
                comm_ranks, nranks, root)
            szuu__fjr = bodo.libs.distributed_api.bcast_comm_impl(index,
                comm_ranks, nranks, root)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                szuu__fjr, fok__chn)
        return impl_series
    if isinstance(data, types.BaseTuple):
        tof__mtokq = (
            f'def impl_tuple(data, comm_ranks, nranks, root={MPI_ROOT}):\n')
        tof__mtokq += '  return ({}{})\n'.format(', '.join(
            'bcast_comm_impl(data[{}], comm_ranks, nranks, root)'.format(i) for
            i in range(len(data))), ',' if len(data) > 0 else '')
        iwyn__tvoov = {}
        exec(tof__mtokq, {'bcast_comm_impl': bcast_comm_impl}, iwyn__tvoov)
        izih__gor = iwyn__tvoov['impl_tuple']
        return izih__gor
    if data is types.none:
        return lambda data, comm_ranks, nranks, root=MPI_ROOT: None


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _bcast_np(data, comm_ranks, nranks, root=MPI_ROOT):
    typ_val = numba_to_c_type(data.dtype)
    omlu__dngax = data.ndim
    dtype = data.dtype
    if dtype == types.NPDatetime('ns'):
        dtype = np.dtype('datetime64[ns]')
    elif dtype == types.NPTimedelta('ns'):
        dtype = np.dtype('timedelta64[ns]')
    phty__ymi = (0,) * omlu__dngax

    def bcast_arr_impl(data, comm_ranks, nranks, root=MPI_ROOT):
        rank = bodo.libs.distributed_api.get_rank()
        aij__xjigz = np.ascontiguousarray(data)
        bmxmk__vwhq = data.ctypes
        sphx__uqnrm = phty__ymi
        if rank == root:
            sphx__uqnrm = aij__xjigz.shape
        sphx__uqnrm = bcast_tuple(sphx__uqnrm, root)
        qen__sklm = get_tuple_prod(sphx__uqnrm[1:])
        send_counts = sphx__uqnrm[0] * qen__sklm
        omp__gkqe = np.empty(send_counts, dtype)
        if rank == MPI_ROOT:
            c_bcast(bmxmk__vwhq, np.int32(send_counts), np.int32(typ_val),
                comm_ranks.ctypes, np.int32(nranks), np.int32(root))
            return data
        else:
            c_bcast(omp__gkqe.ctypes, np.int32(send_counts), np.int32(
                typ_val), comm_ranks.ctypes, np.int32(nranks), np.int32(root))
            return omp__gkqe.reshape((-1,) + sphx__uqnrm[1:])
    return bcast_arr_impl


node_ranks = None


def get_host_ranks():
    global node_ranks
    if node_ranks is None:
        xzgsu__jbgxc = MPI.COMM_WORLD
        lap__ebc = MPI.Get_processor_name()
        shymv__ozyvw = xzgsu__jbgxc.allgather(lap__ebc)
        node_ranks = defaultdict(list)
        for i, nlhrx__xejui in enumerate(shymv__ozyvw):
            node_ranks[nlhrx__xejui].append(i)
    return node_ranks


def create_subcomm_mpi4py(comm_ranks):
    xzgsu__jbgxc = MPI.COMM_WORLD
    aawfp__xdrjl = xzgsu__jbgxc.Get_group()
    godkg__jbc = aawfp__xdrjl.Incl(comm_ranks)
    cvjj__wjau = xzgsu__jbgxc.Create_group(godkg__jbc)
    return cvjj__wjau


def get_nodes_first_ranks():
    hoq__xgsm = get_host_ranks()
    return np.array([qkdi__hkor[0] for qkdi__hkor in hoq__xgsm.values()],
        dtype='int32')


def get_num_nodes():
    return len(get_host_ranks())
