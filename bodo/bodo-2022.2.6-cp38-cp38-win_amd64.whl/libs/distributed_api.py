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
    qaydt__wrzo = get_type_enum(send_arr)
    _send(send_arr.ctypes, 1, qaydt__wrzo, rank, tag)


_recv = types.ExternalFunction('c_recv', types.void(types.voidptr, types.
    int32, types.int32, types.int32, types.int32))


@numba.njit
def recv(dtype, rank, tag):
    recv_arr = np.empty(1, dtype)
    qaydt__wrzo = get_type_enum(recv_arr)
    _recv(recv_arr.ctypes, 1, qaydt__wrzo, rank, tag)
    return recv_arr[0]


_isend = types.ExternalFunction('dist_isend', mpi_req_numba_type(types.
    voidptr, types.int32, types.int32, types.int32, types.int32, types.bool_))


@numba.generated_jit(nopython=True)
def isend(arr, size, pe, tag, cond=True):
    if isinstance(arr, types.Array):

        def impl(arr, size, pe, tag, cond=True):
            qaydt__wrzo = get_type_enum(arr)
            return _isend(arr.ctypes, size, qaydt__wrzo, pe, tag, cond)
        return impl
    if isinstance(arr, (IntegerArrayType, DecimalArrayType)) or arr in (
        boolean_array, datetime_date_array_type):
        qaydt__wrzo = np.int32(numba_to_c_type(arr.dtype))
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))

        def impl_nullable(arr, size, pe, tag, cond=True):
            pdx__syci = size + 7 >> 3
            qct__wpbb = _isend(arr._data.ctypes, size, qaydt__wrzo, pe, tag,
                cond)
            enh__ldo = _isend(arr._null_bitmap.ctypes, pdx__syci,
                wusn__ymbfw, pe, tag, cond)
            return qct__wpbb, enh__ldo
        return impl_nullable
    if is_str_arr_type(arr) or arr == binary_array_type:
        zbzo__yahh = np.int32(numba_to_c_type(offset_type))
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))

        def impl_str_arr(arr, size, pe, tag, cond=True):
            arr = decode_if_dict_array(arr)
            hhkys__udicz = np.int64(bodo.libs.str_arr_ext.num_total_chars(arr))
            send(hhkys__udicz, pe, tag - 1)
            pdx__syci = size + 7 >> 3
            _send(bodo.libs.str_arr_ext.get_offset_ptr(arr), size + 1,
                zbzo__yahh, pe, tag)
            _send(bodo.libs.str_arr_ext.get_data_ptr(arr), hhkys__udicz,
                wusn__ymbfw, pe, tag)
            _send(bodo.libs.str_arr_ext.get_null_bitmap_ptr(arr), pdx__syci,
                wusn__ymbfw, pe, tag)
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
            qaydt__wrzo = get_type_enum(arr)
            return _irecv(arr.ctypes, size, qaydt__wrzo, pe, tag, cond)
        return impl
    if isinstance(arr, (IntegerArrayType, DecimalArrayType)) or arr in (
        boolean_array, datetime_date_array_type):
        qaydt__wrzo = np.int32(numba_to_c_type(arr.dtype))
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))

        def impl_nullable(arr, size, pe, tag, cond=True):
            pdx__syci = size + 7 >> 3
            qct__wpbb = _irecv(arr._data.ctypes, size, qaydt__wrzo, pe, tag,
                cond)
            enh__ldo = _irecv(arr._null_bitmap.ctypes, pdx__syci,
                wusn__ymbfw, pe, tag, cond)
            return qct__wpbb, enh__ldo
        return impl_nullable
    if arr in [binary_array_type, string_array_type]:
        zbzo__yahh = np.int32(numba_to_c_type(offset_type))
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))
        if arr == binary_array_type:
            bqc__hxlek = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
        else:
            bqc__hxlek = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
        ngew__ooz = f"""def impl(arr, size, pe, tag, cond=True):
            # recv the number of string characters and resize buffer to proper size
            n_chars = bodo.libs.distributed_api.recv(np.int64, pe, tag - 1)
            new_arr = {bqc__hxlek}(size, n_chars)
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
        cjbt__mun = dict()
        exec(ngew__ooz, {'bodo': bodo, 'np': np, 'offset_typ_enum':
            zbzo__yahh, 'char_typ_enum': wusn__ymbfw}, cjbt__mun)
        impl = cjbt__mun['impl']
        return impl
    raise BodoError(f'irecv(): array type {arr} not supported yet')


_alltoall = types.ExternalFunction('c_alltoall', types.void(types.voidptr,
    types.voidptr, types.int32, types.int32))


@numba.njit
def alltoall(send_arr, recv_arr, count):
    assert count < INT_MAX
    qaydt__wrzo = get_type_enum(send_arr)
    _alltoall(send_arr.ctypes, recv_arr.ctypes, np.int32(count), qaydt__wrzo)


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
        yqe__dhb = n_pes if rank == root or allgather else 0
        ihqz__aude = np.empty(yqe__dhb, dtype)
        c_gather_scalar(send.ctypes, ihqz__aude.ctypes, np.int32(typ_val),
            allgather, np.int32(root))
        return ihqz__aude
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
        qwdtt__imld = cgutils.alloca_once(builder, args[0].type)
        builder.store(args[0], qwdtt__imld)
        return builder.bitcast(qwdtt__imld, lir.IntType(8).as_pointer())
    return types.voidptr(val_tp), codegen


@intrinsic
def load_val_ptr(typingctx, ptr_tp, val_tp=None):

    def codegen(context, builder, sig, args):
        qwdtt__imld = builder.bitcast(args[0], args[1].type.as_pointer())
        return builder.load(qwdtt__imld)
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
    uye__vgq = types.unliteral(value)
    if isinstance(uye__vgq, IndexValueType):
        uye__vgq = uye__vgq.val_typ
        dkipm__qbod = [types.bool_, types.uint8, types.int8, types.uint16,
            types.int16, types.uint32, types.int32, types.float32, types.
            float64]
        if not sys.platform.startswith('win'):
            dkipm__qbod.append(types.int64)
            dkipm__qbod.append(bodo.datetime64ns)
            dkipm__qbod.append(bodo.timedelta64ns)
            dkipm__qbod.append(bodo.datetime_date_type)
        if uye__vgq not in dkipm__qbod:
            raise BodoError('argmin/argmax not supported for type {}'.
                format(uye__vgq))
    typ_enum = np.int32(numba_to_c_type(uye__vgq))

    def impl(value, reduce_op):
        zgm__nbmt = value_to_ptr(value)
        xkkw__bfouz = value_to_ptr(value)
        _dist_reduce(zgm__nbmt, xkkw__bfouz, reduce_op, typ_enum)
        return load_val_ptr(xkkw__bfouz, value)
    return impl


_dist_exscan = types.ExternalFunction('dist_exscan', types.void(types.
    voidptr, types.voidptr, types.int32, types.int32))


@numba.generated_jit(nopython=True)
def dist_exscan(value, reduce_op):
    uye__vgq = types.unliteral(value)
    typ_enum = np.int32(numba_to_c_type(uye__vgq))
    atih__stdxg = uye__vgq(0)

    def impl(value, reduce_op):
        zgm__nbmt = value_to_ptr(value)
        xkkw__bfouz = value_to_ptr(atih__stdxg)
        _dist_exscan(zgm__nbmt, xkkw__bfouz, reduce_op, typ_enum)
        return load_val_ptr(xkkw__bfouz, value)
    return impl


@numba.njit
def get_bit(bits, i):
    return bits[i >> 3] >> (i & 7) & 1


@numba.njit
def copy_gathered_null_bytes(null_bitmap_ptr, tmp_null_bytes,
    recv_counts_nulls, recv_counts):
    rvyfh__dxz = 0
    nlk__luepb = 0
    for i in range(len(recv_counts)):
        ymjtq__lkpp = recv_counts[i]
        pdx__syci = recv_counts_nulls[i]
        cogog__tjkv = tmp_null_bytes[rvyfh__dxz:rvyfh__dxz + pdx__syci]
        for uron__fefy in range(ymjtq__lkpp):
            set_bit_to(null_bitmap_ptr, nlk__luepb, get_bit(cogog__tjkv,
                uron__fefy))
            nlk__luepb += 1
        rvyfh__dxz += pdx__syci


@numba.generated_jit(nopython=True)
def gatherv(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
    from bodo.libs.csr_matrix_ext import CSRMatrixType
    bodo.hiframes.pd_dataframe_ext.check_runtime_cols_unsupported(data,
        'bodo.gatherv()')
    if isinstance(data, CategoricalArrayType):

        def impl_cat(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
            xmdui__eqdn = bodo.gatherv(data.codes, allgather, root=root)
            return bodo.hiframes.pd_categorical_ext.init_categorical_array(
                xmdui__eqdn, data.dtype)
        return impl_cat
    if isinstance(data, types.Array):
        typ_val = numba_to_c_type(data.dtype)

        def gatherv_impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            data = np.ascontiguousarray(data)
            rank = bodo.libs.distributed_api.get_rank()
            zjlj__rmdwp = data.size
            recv_counts = gather_scalar(np.int32(zjlj__rmdwp), allgather,
                root=root)
            von__ner = recv_counts.sum()
            dgbgr__lyguc = empty_like_type(von__ner, data)
            ygpzb__cmost = np.empty(1, np.int32)
            if rank == root or allgather:
                ygpzb__cmost = bodo.ir.join.calc_disp(recv_counts)
            c_gatherv(data.ctypes, np.int32(zjlj__rmdwp), dgbgr__lyguc.
                ctypes, recv_counts.ctypes, ygpzb__cmost.ctypes, np.int32(
                typ_val), allgather, np.int32(root))
            return dgbgr__lyguc.reshape((-1,) + data.shape[1:])
        return gatherv_impl
    if is_str_arr_type(data):

        def gatherv_str_arr_impl(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            data = decode_if_dict_array(data)
            dgbgr__lyguc = bodo.gatherv(data._data, allgather, warn_if_rep,
                root)
            return bodo.libs.str_arr_ext.init_str_arr(dgbgr__lyguc)
        return gatherv_str_arr_impl
    if data == binary_array_type:

        def gatherv_binary_arr_impl(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            dgbgr__lyguc = bodo.gatherv(data._data, allgather, warn_if_rep,
                root)
            return bodo.libs.binary_arr_ext.init_binary_arr(dgbgr__lyguc)
        return gatherv_binary_arr_impl
    if data == datetime_timedelta_array_type:
        typ_val = numba_to_c_type(types.int64)
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))

        def gatherv_impl_int_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            zjlj__rmdwp = len(data)
            pdx__syci = zjlj__rmdwp + 7 >> 3
            recv_counts = gather_scalar(np.int32(zjlj__rmdwp), allgather,
                root=root)
            von__ner = recv_counts.sum()
            dgbgr__lyguc = empty_like_type(von__ner, data)
            ygpzb__cmost = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            vosqh__sin = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                ygpzb__cmost = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                vosqh__sin = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(data._days_data.ctypes, np.int32(zjlj__rmdwp),
                dgbgr__lyguc._days_data.ctypes, recv_counts.ctypes,
                ygpzb__cmost.ctypes, np.int32(typ_val), allgather, np.int32
                (root))
            c_gatherv(data._seconds_data.ctypes, np.int32(zjlj__rmdwp),
                dgbgr__lyguc._seconds_data.ctypes, recv_counts.ctypes,
                ygpzb__cmost.ctypes, np.int32(typ_val), allgather, np.int32
                (root))
            c_gatherv(data._microseconds_data.ctypes, np.int32(zjlj__rmdwp),
                dgbgr__lyguc._microseconds_data.ctypes, recv_counts.ctypes,
                ygpzb__cmost.ctypes, np.int32(typ_val), allgather, np.int32
                (root))
            c_gatherv(data._null_bitmap.ctypes, np.int32(pdx__syci),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, vosqh__sin
                .ctypes, wusn__ymbfw, allgather, np.int32(root))
            copy_gathered_null_bytes(dgbgr__lyguc._null_bitmap.ctypes,
                tmp_null_bytes, recv_counts_nulls, recv_counts)
            return dgbgr__lyguc
        return gatherv_impl_int_arr
    if isinstance(data, (IntegerArrayType, DecimalArrayType)) or data in (
        boolean_array, datetime_date_array_type):
        typ_val = numba_to_c_type(data.dtype)
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))

        def gatherv_impl_int_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            zjlj__rmdwp = len(data)
            pdx__syci = zjlj__rmdwp + 7 >> 3
            recv_counts = gather_scalar(np.int32(zjlj__rmdwp), allgather,
                root=root)
            von__ner = recv_counts.sum()
            dgbgr__lyguc = empty_like_type(von__ner, data)
            ygpzb__cmost = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            vosqh__sin = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                ygpzb__cmost = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                vosqh__sin = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(data._data.ctypes, np.int32(zjlj__rmdwp),
                dgbgr__lyguc._data.ctypes, recv_counts.ctypes, ygpzb__cmost
                .ctypes, np.int32(typ_val), allgather, np.int32(root))
            c_gatherv(data._null_bitmap.ctypes, np.int32(pdx__syci),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, vosqh__sin
                .ctypes, wusn__ymbfw, allgather, np.int32(root))
            copy_gathered_null_bytes(dgbgr__lyguc._null_bitmap.ctypes,
                tmp_null_bytes, recv_counts_nulls, recv_counts)
            return dgbgr__lyguc
        return gatherv_impl_int_arr
    if isinstance(data, DatetimeArrayType):
        ocdjd__kvuy = data.tz

        def impl_pd_datetime_arr(data, allgather=False, warn_if_rep=True,
            root=MPI_ROOT):
            oflds__ptnfa = bodo.gatherv(data._data, allgather, warn_if_rep,
                root)
            return bodo.libs.pd_datetime_arr_ext.init_pandas_datetime_array(
                oflds__ptnfa, ocdjd__kvuy)
        return impl_pd_datetime_arr
    if isinstance(data, IntervalArrayType):

        def impl_interval_arr(data, allgather=False, warn_if_rep=True, root
            =MPI_ROOT):
            iuz__ovqn = bodo.gatherv(data._left, allgather, warn_if_rep, root)
            icsfe__hrsbe = bodo.gatherv(data._right, allgather, warn_if_rep,
                root)
            return bodo.libs.interval_arr_ext.init_interval_array(iuz__ovqn,
                icsfe__hrsbe)
        return impl_interval_arr
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            ejbbb__eisbl = bodo.hiframes.pd_series_ext.get_series_name(data)
            out_arr = bodo.libs.distributed_api.gatherv(arr, allgather,
                warn_if_rep, root)
            ing__gzf = bodo.gatherv(index, allgather, warn_if_rep, root)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                ing__gzf, ejbbb__eisbl)
        return impl
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):
        yvq__siko = np.iinfo(np.int64).max
        qqeqw__afx = np.iinfo(np.int64).min

        def impl_range_index(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            start = data._start
            stop = data._stop
            if len(data) == 0:
                start = yvq__siko
                stop = qqeqw__afx
            start = bodo.libs.distributed_api.dist_reduce(start, np.int32(
                Reduce_Type.Min.value))
            stop = bodo.libs.distributed_api.dist_reduce(stop, np.int32(
                Reduce_Type.Max.value))
            total_len = bodo.libs.distributed_api.dist_reduce(len(data), np
                .int32(Reduce_Type.Sum.value))
            if start == yvq__siko and stop == qqeqw__afx:
                start = 0
                stop = 0
            joyj__rhfu = max(0, -(-(stop - start) // data._step))
            if joyj__rhfu < total_len:
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
            fsb__risa = data.freq

            def impl_pd_index(data, allgather=False, warn_if_rep=True, root
                =MPI_ROOT):
                arr = bodo.libs.distributed_api.gatherv(data._data,
                    allgather, root=root)
                return bodo.hiframes.pd_index_ext.init_period_index(arr,
                    data._name, fsb__risa)
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
            dgbgr__lyguc = bodo.gatherv(data._data, allgather, root=root)
            return bodo.hiframes.pd_multi_index_ext.init_multi_index(
                dgbgr__lyguc, data._names, data._name)
        return impl_multi_index
    if isinstance(data, bodo.hiframes.table.TableType):
        bfyo__viohh = {'bodo': bodo, 'get_table_block': bodo.hiframes.table
            .get_table_block, 'ensure_column_unboxed': bodo.hiframes.table.
            ensure_column_unboxed, 'set_table_block': bodo.hiframes.table.
            set_table_block, 'set_table_len': bodo.hiframes.table.
            set_table_len, 'alloc_list_like': bodo.hiframes.table.
            alloc_list_like, 'init_table': bodo.hiframes.table.init_table}
        ngew__ooz = (
            f'def impl_table(data, allgather=False, warn_if_rep=True, root={MPI_ROOT}):\n'
            )
        ngew__ooz += '  T = data\n'
        ngew__ooz += '  T2 = init_table(T, True)\n'
        for cjk__shbfc in data.type_to_blk.values():
            bfyo__viohh[f'arr_inds_{cjk__shbfc}'] = np.array(data.
                block_to_arr_ind[cjk__shbfc], dtype=np.int64)
            ngew__ooz += (
                f'  arr_list_{cjk__shbfc} = get_table_block(T, {cjk__shbfc})\n'
                )
            ngew__ooz += f"""  out_arr_list_{cjk__shbfc} = alloc_list_like(arr_list_{cjk__shbfc}, True)
"""
            ngew__ooz += f'  for i in range(len(arr_list_{cjk__shbfc})):\n'
            ngew__ooz += (
                f'    arr_ind_{cjk__shbfc} = arr_inds_{cjk__shbfc}[i]\n')
            ngew__ooz += f"""    ensure_column_unboxed(T, arr_list_{cjk__shbfc}, i, arr_ind_{cjk__shbfc})
"""
            ngew__ooz += f"""    out_arr_{cjk__shbfc} = bodo.gatherv(arr_list_{cjk__shbfc}[i], allgather, warn_if_rep, root)
"""
            ngew__ooz += (
                f'    out_arr_list_{cjk__shbfc}[i] = out_arr_{cjk__shbfc}\n')
            ngew__ooz += (
                f'  T2 = set_table_block(T2, out_arr_list_{cjk__shbfc}, {cjk__shbfc})\n'
                )
        ngew__ooz += (
            f'  length = T._len if bodo.get_rank() == root or allgather else 0\n'
            )
        ngew__ooz += f'  T2 = set_table_len(T2, length)\n'
        ngew__ooz += f'  return T2\n'
        cjbt__mun = {}
        exec(ngew__ooz, bfyo__viohh, cjbt__mun)
        xhkhp__givxc = cjbt__mun['impl_table']
        return xhkhp__givxc
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        izz__qvi = len(data.columns)
        if izz__qvi == 0:

            def impl(data, allgather=False, warn_if_rep=True, root=MPI_ROOT):
                index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data
                    )
                gkrn__bynd = bodo.gatherv(index, allgather, warn_if_rep, root)
                return bodo.hiframes.pd_dataframe_ext.init_dataframe((),
                    gkrn__bynd, ())
            return impl
        muua__mkk = ', '.join(f'g_data_{i}' for i in range(izz__qvi))
        rqdh__hsh = bodo.utils.transform.gen_const_tup(data.columns)
        ngew__ooz = (
            'def impl_df(data, allgather=False, warn_if_rep=True, root={}):\n'
            .format(MPI_ROOT))
        if data.is_table_format:
            from bodo.transforms.distributed_analysis import Distribution
            wwh__ntvpc = bodo.hiframes.pd_dataframe_ext.DataFrameType(data.
                data, data.index, data.columns, Distribution.REP, True)
            bfyo__viohh = {'bodo': bodo, 'df_type': wwh__ntvpc}
            muua__mkk = 'T2'
            rqdh__hsh = 'df_type'
            ngew__ooz += (
                '  T = bodo.hiframes.pd_dataframe_ext.get_dataframe_table(data)\n'
                )
            ngew__ooz += (
                '  T2 = bodo.gatherv(T, allgather, warn_if_rep, root)\n')
        else:
            bfyo__viohh = {'bodo': bodo}
            for i in range(izz__qvi):
                ngew__ooz += (
                    """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                    .format(i, i))
                ngew__ooz += (
                    '  g_data_{} = bodo.gatherv(data_{}, allgather, warn_if_rep, root)\n'
                    .format(i, i))
        ngew__ooz += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        ngew__ooz += (
            '  g_index = bodo.gatherv(index, allgather, warn_if_rep, root)\n')
        ngew__ooz += (
            '  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})\n'
            .format(muua__mkk, rqdh__hsh))
        cjbt__mun = {}
        exec(ngew__ooz, bfyo__viohh, cjbt__mun)
        fhbex__cehhn = cjbt__mun['impl_df']
        return fhbex__cehhn
    if isinstance(data, ArrayItemArrayType):
        kbo__quw = np.int32(numba_to_c_type(types.int32))
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))

        def gatherv_array_item_arr_impl(data, allgather=False, warn_if_rep=
            True, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            qza__wuo = bodo.libs.array_item_arr_ext.get_offsets(data)
            slfdu__poe = bodo.libs.array_item_arr_ext.get_data(data)
            slfdu__poe = slfdu__poe[:qza__wuo[-1]]
            cmebe__mbih = bodo.libs.array_item_arr_ext.get_null_bitmap(data)
            zjlj__rmdwp = len(data)
            wdwv__bvszf = np.empty(zjlj__rmdwp, np.uint32)
            pdx__syci = zjlj__rmdwp + 7 >> 3
            for i in range(zjlj__rmdwp):
                wdwv__bvszf[i] = qza__wuo[i + 1] - qza__wuo[i]
            recv_counts = gather_scalar(np.int32(zjlj__rmdwp), allgather,
                root=root)
            von__ner = recv_counts.sum()
            ygpzb__cmost = np.empty(1, np.int32)
            recv_counts_nulls = np.empty(1, np.int32)
            vosqh__sin = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                ygpzb__cmost = bodo.ir.join.calc_disp(recv_counts)
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for hts__egck in range(len(recv_counts)):
                    recv_counts_nulls[hts__egck] = recv_counts[hts__egck
                        ] + 7 >> 3
                vosqh__sin = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            niy__rap = np.empty(von__ner + 1, np.uint32)
            mxl__igte = bodo.gatherv(slfdu__poe, allgather, warn_if_rep, root)
            ujza__pxjsk = np.empty(von__ner + 7 >> 3, np.uint8)
            c_gatherv(wdwv__bvszf.ctypes, np.int32(zjlj__rmdwp), niy__rap.
                ctypes, recv_counts.ctypes, ygpzb__cmost.ctypes, kbo__quw,
                allgather, np.int32(root))
            c_gatherv(cmebe__mbih.ctypes, np.int32(pdx__syci),
                tmp_null_bytes.ctypes, recv_counts_nulls.ctypes, vosqh__sin
                .ctypes, wusn__ymbfw, allgather, np.int32(root))
            dummy_use(data)
            ksi__eujn = np.empty(von__ner + 1, np.uint64)
            convert_len_arr_to_offset(niy__rap.ctypes, ksi__eujn.ctypes,
                von__ner)
            copy_gathered_null_bytes(ujza__pxjsk.ctypes, tmp_null_bytes,
                recv_counts_nulls, recv_counts)
            out_arr = bodo.libs.array_item_arr_ext.init_array_item_array(
                von__ner, mxl__igte, ksi__eujn, ujza__pxjsk)
            return out_arr
        return gatherv_array_item_arr_impl
    if isinstance(data, StructArrayType):
        yps__qylux = data.names
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))

        def impl_struct_arr(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            eulj__heun = bodo.libs.struct_arr_ext.get_data(data)
            tkf__inbj = bodo.libs.struct_arr_ext.get_null_bitmap(data)
            zdjvs__lfrw = bodo.gatherv(eulj__heun, allgather=allgather,
                root=root)
            rank = bodo.libs.distributed_api.get_rank()
            zjlj__rmdwp = len(data)
            pdx__syci = zjlj__rmdwp + 7 >> 3
            recv_counts = gather_scalar(np.int32(zjlj__rmdwp), allgather,
                root=root)
            von__ner = recv_counts.sum()
            odq__oqpgd = np.empty(von__ner + 7 >> 3, np.uint8)
            recv_counts_nulls = np.empty(1, np.int32)
            vosqh__sin = np.empty(1, np.int32)
            tmp_null_bytes = np.empty(1, np.uint8)
            if rank == root or allgather:
                recv_counts_nulls = np.empty(len(recv_counts), np.int32)
                for i in range(len(recv_counts)):
                    recv_counts_nulls[i] = recv_counts[i] + 7 >> 3
                vosqh__sin = bodo.ir.join.calc_disp(recv_counts_nulls)
                tmp_null_bytes = np.empty(recv_counts_nulls.sum(), np.uint8)
            c_gatherv(tkf__inbj.ctypes, np.int32(pdx__syci), tmp_null_bytes
                .ctypes, recv_counts_nulls.ctypes, vosqh__sin.ctypes,
                wusn__ymbfw, allgather, np.int32(root))
            copy_gathered_null_bytes(odq__oqpgd.ctypes, tmp_null_bytes,
                recv_counts_nulls, recv_counts)
            return bodo.libs.struct_arr_ext.init_struct_arr(zdjvs__lfrw,
                odq__oqpgd, yps__qylux)
        return impl_struct_arr
    if data == binary_array_type:

        def impl_bin_arr(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            dgbgr__lyguc = bodo.gatherv(data._data, allgather, warn_if_rep,
                root)
            return bodo.libs.binary_arr_ext.init_binary_arr(dgbgr__lyguc)
        return impl_bin_arr
    if isinstance(data, TupleArrayType):

        def impl_tuple_arr(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            dgbgr__lyguc = bodo.gatherv(data._data, allgather, warn_if_rep,
                root)
            return bodo.libs.tuple_arr_ext.init_tuple_arr(dgbgr__lyguc)
        return impl_tuple_arr
    if isinstance(data, MapArrayType):

        def impl_map_arr(data, allgather=False, warn_if_rep=True, root=MPI_ROOT
            ):
            dgbgr__lyguc = bodo.gatherv(data._data, allgather, warn_if_rep,
                root)
            return bodo.libs.map_arr_ext.init_map_arr(dgbgr__lyguc)
        return impl_map_arr
    if isinstance(data, CSRMatrixType):

        def impl_csr_matrix(data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT):
            dgbgr__lyguc = bodo.gatherv(data.data, allgather, warn_if_rep, root
                )
            gwd__ccol = bodo.gatherv(data.indices, allgather, warn_if_rep, root
                )
            rvssh__tzgqe = bodo.gatherv(data.indptr, allgather, warn_if_rep,
                root)
            zzacz__lqyx = gather_scalar(data.shape[0], allgather, root=root)
            uzk__qtfh = zzacz__lqyx.sum()
            izz__qvi = bodo.libs.distributed_api.dist_reduce(data.shape[1],
                np.int32(Reduce_Type.Max.value))
            tfxqu__vrug = np.empty(uzk__qtfh + 1, np.int64)
            gwd__ccol = gwd__ccol.astype(np.int64)
            tfxqu__vrug[0] = 0
            wfjr__jpnm = 1
            kylad__rczuw = 0
            for mbbo__nicy in zzacz__lqyx:
                for vpsz__ouqd in range(mbbo__nicy):
                    jsas__ues = rvssh__tzgqe[kylad__rczuw + 1] - rvssh__tzgqe[
                        kylad__rczuw]
                    tfxqu__vrug[wfjr__jpnm] = tfxqu__vrug[wfjr__jpnm - 1
                        ] + jsas__ues
                    wfjr__jpnm += 1
                    kylad__rczuw += 1
                kylad__rczuw += 1
            return bodo.libs.csr_matrix_ext.init_csr_matrix(dgbgr__lyguc,
                gwd__ccol, tfxqu__vrug, (uzk__qtfh, izz__qvi))
        return impl_csr_matrix
    if isinstance(data, types.BaseTuple):
        ngew__ooz = (
            'def impl_tuple(data, allgather=False, warn_if_rep=True, root={}):\n'
            .format(MPI_ROOT))
        ngew__ooz += '  return ({}{})\n'.format(', '.join(
            'bodo.gatherv(data[{}], allgather, warn_if_rep, root)'.format(i
            ) for i in range(len(data))), ',' if len(data) > 0 else '')
        cjbt__mun = {}
        exec(ngew__ooz, {'bodo': bodo}, cjbt__mun)
        mxx__yay = cjbt__mun['impl_tuple']
        return mxx__yay
    if data is types.none:
        return (lambda data, allgather=False, warn_if_rep=True, root=
            MPI_ROOT: None)
    raise BodoError('gatherv() not available for {}'.format(data))


@numba.generated_jit(nopython=True)
def rebalance(data, dests=None, random=False, random_seed=None, parallel=False
    ):
    bodo.hiframes.pd_dataframe_ext.check_runtime_cols_unsupported(data,
        'bodo.rebalance()')
    ngew__ooz = (
        'def impl(data, dests=None, random=False, random_seed=None, parallel=False):\n'
        )
    ngew__ooz += '    if random:\n'
    ngew__ooz += '        if random_seed is None:\n'
    ngew__ooz += '            random = 1\n'
    ngew__ooz += '        else:\n'
    ngew__ooz += '            random = 2\n'
    ngew__ooz += '    if random_seed is None:\n'
    ngew__ooz += '        random_seed = -1\n'
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        ppjce__ctacy = data
        izz__qvi = len(ppjce__ctacy.columns)
        for i in range(izz__qvi):
            ngew__ooz += f"""    data_{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {i})
"""
        ngew__ooz += """    ind_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data))
"""
        muua__mkk = ', '.join(f'data_{i}' for i in range(izz__qvi))
        ngew__ooz += ('    info_list_total = [{}, array_to_info(ind_arr)]\n'
            .format(', '.join('array_to_info(data_{})'.format(ohrj__dhfmr) for
            ohrj__dhfmr in range(izz__qvi))))
        ngew__ooz += (
            '    table_total = arr_info_list_to_table(info_list_total)\n')
        ngew__ooz += '    if dests is None:\n'
        ngew__ooz += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        ngew__ooz += '    else:\n'
        ngew__ooz += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        for rzb__aicrq in range(izz__qvi):
            ngew__ooz += (
                """    out_arr_{0} = info_to_array(info_from_table(out_table, {0}), data_{0})
"""
                .format(rzb__aicrq))
        ngew__ooz += (
            '    out_arr_index = info_to_array(info_from_table(out_table, {}), ind_arr)\n'
            .format(izz__qvi))
        ngew__ooz += '    delete_table(out_table)\n'
        ngew__ooz += '    if parallel:\n'
        ngew__ooz += '        delete_table(table_total)\n'
        muua__mkk = ', '.join('out_arr_{}'.format(i) for i in range(izz__qvi))
        rqdh__hsh = bodo.utils.transform.gen_const_tup(ppjce__ctacy.columns)
        index = 'bodo.utils.conversion.index_from_array(out_arr_index)'
        ngew__ooz += (
            '    return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), {}, {})\n'
            .format(muua__mkk, index, rqdh__hsh))
    elif isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):
        ngew__ooz += (
            '    data_0 = bodo.hiframes.pd_series_ext.get_series_data(data)\n')
        ngew__ooz += """    ind_arr = bodo.utils.conversion.index_to_array(bodo.hiframes.pd_series_ext.get_series_index(data))
"""
        ngew__ooz += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(data)\n')
        ngew__ooz += """    table_total = arr_info_list_to_table([array_to_info(data_0), array_to_info(ind_arr)])
"""
        ngew__ooz += '    if dests is None:\n'
        ngew__ooz += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        ngew__ooz += '    else:\n'
        ngew__ooz += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        ngew__ooz += (
            '    out_arr_0 = info_to_array(info_from_table(out_table, 0), data_0)\n'
            )
        ngew__ooz += (
            '    out_arr_index = info_to_array(info_from_table(out_table, 1), ind_arr)\n'
            )
        ngew__ooz += '    delete_table(out_table)\n'
        ngew__ooz += '    if parallel:\n'
        ngew__ooz += '        delete_table(table_total)\n'
        index = 'bodo.utils.conversion.index_from_array(out_arr_index)'
        ngew__ooz += f"""    return bodo.hiframes.pd_series_ext.init_series(out_arr_0, {index}, name)
"""
    elif isinstance(data, types.Array):
        assert is_overload_false(random
            ), 'Call random_shuffle instead of rebalance'
        ngew__ooz += '    if not parallel:\n'
        ngew__ooz += '        return data\n'
        ngew__ooz += """    dim0_global_size = bodo.libs.distributed_api.dist_reduce(data.shape[0], np.int32(bodo.libs.distributed_api.Reduce_Type.Sum.value))
"""
        ngew__ooz += '    if dests is None:\n'
        ngew__ooz += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, bodo.get_size(), bodo.get_rank())
"""
        ngew__ooz += '    elif bodo.get_rank() not in dests:\n'
        ngew__ooz += '        dim0_local_size = 0\n'
        ngew__ooz += '    else:\n'
        ngew__ooz += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, len(dests), dests.index(bodo.get_rank()))
"""
        ngew__ooz += """    out = np.empty((dim0_local_size,) + tuple(data.shape[1:]), dtype=data.dtype)
"""
        ngew__ooz += """    bodo.libs.distributed_api.dist_oneD_reshape_shuffle(out, data, dim0_global_size, dests)
"""
        ngew__ooz += '    return out\n'
    elif bodo.utils.utils.is_array_typ(data, False):
        ngew__ooz += (
            '    table_total = arr_info_list_to_table([array_to_info(data)])\n'
            )
        ngew__ooz += '    if dests is None:\n'
        ngew__ooz += """        out_table = shuffle_renormalization(table_total, random, random_seed, parallel)
"""
        ngew__ooz += '    else:\n'
        ngew__ooz += """        out_table = shuffle_renormalization_group(table_total, random, random_seed, parallel, len(dests), np.array(dests, dtype=np.int32).ctypes)
"""
        ngew__ooz += (
            '    out_arr = info_to_array(info_from_table(out_table, 0), data)\n'
            )
        ngew__ooz += '    delete_table(out_table)\n'
        ngew__ooz += '    if parallel:\n'
        ngew__ooz += '        delete_table(table_total)\n'
        ngew__ooz += '    return out_arr\n'
    else:
        raise BodoError(f'Type {data} not supported for bodo.rebalance')
    cjbt__mun = {}
    exec(ngew__ooz, {'np': np, 'bodo': bodo, 'array_to_info': bodo.libs.
        array.array_to_info, 'shuffle_renormalization': bodo.libs.array.
        shuffle_renormalization, 'shuffle_renormalization_group': bodo.libs
        .array.shuffle_renormalization_group, 'arr_info_list_to_table':
        bodo.libs.array.arr_info_list_to_table, 'info_from_table': bodo.
        libs.array.info_from_table, 'info_to_array': bodo.libs.array.
        info_to_array, 'delete_table': bodo.libs.array.delete_table}, cjbt__mun
        )
    impl = cjbt__mun['impl']
    return impl


@numba.generated_jit(nopython=True)
def random_shuffle(data, seed=None, dests=None, parallel=False):
    ngew__ooz = 'def impl(data, seed=None, dests=None, parallel=False):\n'
    if isinstance(data, types.Array):
        if not is_overload_none(dests):
            raise BodoError('not supported')
        ngew__ooz += '    if seed is None:\n'
        ngew__ooz += """        seed = bodo.libs.distributed_api.bcast_scalar(np.random.randint(0, 2**31))
"""
        ngew__ooz += '    np.random.seed(seed)\n'
        ngew__ooz += '    if not parallel:\n'
        ngew__ooz += '        data = data.copy()\n'
        ngew__ooz += '        np.random.shuffle(data)\n'
        ngew__ooz += '        return data\n'
        ngew__ooz += '    else:\n'
        ngew__ooz += """        dim0_global_size = bodo.libs.distributed_api.dist_reduce(data.shape[0], np.int32(bodo.libs.distributed_api.Reduce_Type.Sum.value))
"""
        ngew__ooz += '        permutation = np.arange(dim0_global_size)\n'
        ngew__ooz += '        np.random.shuffle(permutation)\n'
        ngew__ooz += """        dim0_local_size = bodo.libs.distributed_api.get_node_portion(dim0_global_size, bodo.get_size(), bodo.get_rank())
"""
        ngew__ooz += """        output = np.empty((dim0_local_size,) + tuple(data.shape[1:]), dtype=data.dtype)
"""
        ngew__ooz += (
            '        dtype_size = bodo.io.np_io.get_dtype_size(data.dtype)\n')
        ngew__ooz += """        bodo.libs.distributed_api.dist_permutation_array_index(output, dim0_global_size, dtype_size, data, permutation, len(permutation))
"""
        ngew__ooz += '        return output\n'
    else:
        ngew__ooz += """    return bodo.libs.distributed_api.rebalance(data, dests=dests, random=True, random_seed=seed, parallel=parallel)
"""
    cjbt__mun = {}
    exec(ngew__ooz, {'np': np, 'bodo': bodo}, cjbt__mun)
    impl = cjbt__mun['impl']
    return impl


@numba.generated_jit(nopython=True)
def allgatherv(data, warn_if_rep=True, root=MPI_ROOT):
    return lambda data, warn_if_rep=True, root=MPI_ROOT: gatherv(data, True,
        warn_if_rep, root)


@numba.njit
def get_scatter_null_bytes_buff(null_bitmap_ptr, sendcounts, sendcounts_nulls):
    if bodo.get_rank() != MPI_ROOT:
        return np.empty(1, np.uint8)
    doq__nng = np.empty(sendcounts_nulls.sum(), np.uint8)
    rvyfh__dxz = 0
    nlk__luepb = 0
    for nfi__kib in range(len(sendcounts)):
        ymjtq__lkpp = sendcounts[nfi__kib]
        pdx__syci = sendcounts_nulls[nfi__kib]
        cogog__tjkv = doq__nng[rvyfh__dxz:rvyfh__dxz + pdx__syci]
        for uron__fefy in range(ymjtq__lkpp):
            set_bit_to_arr(cogog__tjkv, uron__fefy, get_bit_bitmap(
                null_bitmap_ptr, nlk__luepb))
            nlk__luepb += 1
        rvyfh__dxz += pdx__syci
    return doq__nng


def _bcast_dtype(data, root=MPI_ROOT):
    try:
        from mpi4py import MPI
    except:
        raise BodoError('mpi4py is required for scatterv')
    pwzx__djvq = MPI.COMM_WORLD
    data = pwzx__djvq.bcast(data, root)
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
    vzm__iwouw = data.ndim
    dtype = data.dtype
    if dtype == types.NPDatetime('ns'):
        dtype = np.dtype('datetime64[ns]')
    elif dtype == types.NPTimedelta('ns'):
        dtype = np.dtype('timedelta64[ns]')
    qszm__bgn = (0,) * vzm__iwouw

    def scatterv_arr_impl(data, send_counts=None, warn_if_dist=True):
        rank = bodo.libs.distributed_api.get_rank()
        n_pes = bodo.libs.distributed_api.get_size()
        cgxs__caw = np.ascontiguousarray(data)
        jje__qutqy = data.ctypes
        xoer__ulx = qszm__bgn
        if rank == MPI_ROOT:
            xoer__ulx = cgxs__caw.shape
        xoer__ulx = bcast_tuple(xoer__ulx)
        rogmn__bgfun = get_tuple_prod(xoer__ulx[1:])
        send_counts = _get_scatterv_send_counts(send_counts, n_pes,
            xoer__ulx[0])
        send_counts *= rogmn__bgfun
        zjlj__rmdwp = send_counts[rank]
        rznn__wanzf = np.empty(zjlj__rmdwp, dtype)
        ygpzb__cmost = bodo.ir.join.calc_disp(send_counts)
        c_scatterv(jje__qutqy, send_counts.ctypes, ygpzb__cmost.ctypes,
            rznn__wanzf.ctypes, np.int32(zjlj__rmdwp), np.int32(typ_val))
        return rznn__wanzf.reshape((-1,) + xoer__ulx[1:])
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
        oytyk__gowyl = '{}Int{}'.format('' if dtype.dtype.signed else 'U',
            dtype.dtype.bitwidth)
        return pd.array([3], oytyk__gowyl)
    if dtype == boolean_array:
        return pd.array([True], 'boolean')
    if isinstance(dtype, DecimalArrayType):
        return np.array([Decimal('32.1')])
    if dtype == datetime_date_array_type:
        return np.array([datetime.date(2011, 8, 9)])
    if dtype == datetime_timedelta_array_type:
        return np.array([datetime.timedelta(33)])
    if bodo.hiframes.pd_index_ext.is_pd_index_type(dtype):
        ejbbb__eisbl = _get_name_value_for_type(dtype.name_typ)
        if isinstance(dtype, bodo.hiframes.pd_index_ext.RangeIndexType):
            return pd.RangeIndex(1, name=ejbbb__eisbl)
        npgf__zihr = bodo.utils.typing.get_index_data_arr_types(dtype)[0]
        arr = get_value_for_type(npgf__zihr)
        return pd.Index(arr, name=ejbbb__eisbl)
    if isinstance(dtype, bodo.hiframes.pd_multi_index_ext.MultiIndexType):
        import pyarrow as pa
        ejbbb__eisbl = _get_name_value_for_type(dtype.name_typ)
        yps__qylux = tuple(_get_name_value_for_type(t) for t in dtype.names_typ
            )
        vulp__ccna = tuple(get_value_for_type(t) for t in dtype.array_types)
        vulp__ccna = tuple(a.to_numpy(False) if isinstance(a, pa.Array) else
            a for a in vulp__ccna)
        val = pd.MultiIndex.from_arrays(vulp__ccna, names=yps__qylux)
        val.name = ejbbb__eisbl
        return val
    if isinstance(dtype, bodo.hiframes.pd_series_ext.SeriesType):
        ejbbb__eisbl = _get_name_value_for_type(dtype.name_typ)
        arr = get_value_for_type(dtype.data)
        index = get_value_for_type(dtype.index)
        return pd.Series(arr, index, name=ejbbb__eisbl)
    if isinstance(dtype, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        vulp__ccna = tuple(get_value_for_type(t) for t in dtype.data)
        index = get_value_for_type(dtype.index)
        return pd.DataFrame({ejbbb__eisbl: arr for ejbbb__eisbl, arr in zip
            (dtype.columns, vulp__ccna)}, index)
    if isinstance(dtype, CategoricalArrayType):
        return pd.Categorical.from_codes([0], dtype.dtype.categories)
    if isinstance(dtype, types.BaseTuple):
        return tuple(get_value_for_type(t) for t in dtype.types)
    if isinstance(dtype, ArrayItemArrayType):
        return pd.Series([get_value_for_type(dtype.dtype),
            get_value_for_type(dtype.dtype)]).values
    if isinstance(dtype, IntervalArrayType):
        npgf__zihr = get_value_for_type(dtype.arr_type)
        return pd.arrays.IntervalArray([pd.Interval(npgf__zihr[0],
            npgf__zihr[0])])
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
        kbo__quw = np.int32(numba_to_c_type(types.int32))
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))
        if data == binary_array_type:
            bqc__hxlek = 'bodo.libs.binary_arr_ext.pre_alloc_binary_array'
        else:
            bqc__hxlek = 'bodo.libs.str_arr_ext.pre_alloc_string_array'
        ngew__ooz = f"""def impl(
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
            recv_arr = {bqc__hxlek}(n_loc, n_loc_char)

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
        cjbt__mun = dict()
        exec(ngew__ooz, {'bodo': bodo, 'np': np, 'int32_typ_enum': kbo__quw,
            'char_typ_enum': wusn__ymbfw, 'decode_if_dict_array':
            decode_if_dict_array}, cjbt__mun)
        impl = cjbt__mun['impl']
        return impl
    if isinstance(data, ArrayItemArrayType):
        kbo__quw = np.int32(numba_to_c_type(types.int32))
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))

        def scatterv_array_item_impl(data, send_counts=None, warn_if_dist=True
            ):
            kmm__ebeuh = bodo.libs.array_item_arr_ext.get_offsets(data)
            xjakd__xdqs = bodo.libs.array_item_arr_ext.get_data(data)
            xjakd__xdqs = xjakd__xdqs[:kmm__ebeuh[-1]]
            zqwgn__zhmw = bodo.libs.array_item_arr_ext.get_null_bitmap(data)
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            caha__ofagw = bcast_scalar(len(data))
            wkwj__vbtr = np.empty(len(data), np.uint32)
            for i in range(len(data)):
                wkwj__vbtr[i] = kmm__ebeuh[i + 1] - kmm__ebeuh[i]
            send_counts = _get_scatterv_send_counts(send_counts, n_pes,
                caha__ofagw)
            ygpzb__cmost = bodo.ir.join.calc_disp(send_counts)
            egdvy__bcl = np.empty(n_pes, np.int32)
            if rank == 0:
                hdz__qydd = 0
                for i in range(n_pes):
                    uar__zkp = 0
                    for vpsz__ouqd in range(send_counts[i]):
                        uar__zkp += wkwj__vbtr[hdz__qydd]
                        hdz__qydd += 1
                    egdvy__bcl[i] = uar__zkp
            bcast(egdvy__bcl)
            fri__vbtnd = np.empty(n_pes, np.int32)
            for i in range(n_pes):
                fri__vbtnd[i] = send_counts[i] + 7 >> 3
            vosqh__sin = bodo.ir.join.calc_disp(fri__vbtnd)
            zjlj__rmdwp = send_counts[rank]
            got__kwlud = np.empty(zjlj__rmdwp + 1, np_offset_type)
            gal__shtu = bodo.libs.distributed_api.scatterv_impl(xjakd__xdqs,
                egdvy__bcl)
            nbg__hlgur = zjlj__rmdwp + 7 >> 3
            ektg__rucx = np.empty(nbg__hlgur, np.uint8)
            nclxk__ljt = np.empty(zjlj__rmdwp, np.uint32)
            c_scatterv(wkwj__vbtr.ctypes, send_counts.ctypes, ygpzb__cmost.
                ctypes, nclxk__ljt.ctypes, np.int32(zjlj__rmdwp), kbo__quw)
            convert_len_arr_to_offset(nclxk__ljt.ctypes, got__kwlud.ctypes,
                zjlj__rmdwp)
            koopl__sfdhe = get_scatter_null_bytes_buff(zqwgn__zhmw.ctypes,
                send_counts, fri__vbtnd)
            c_scatterv(koopl__sfdhe.ctypes, fri__vbtnd.ctypes, vosqh__sin.
                ctypes, ektg__rucx.ctypes, np.int32(nbg__hlgur), wusn__ymbfw)
            return bodo.libs.array_item_arr_ext.init_array_item_array(
                zjlj__rmdwp, gal__shtu, got__kwlud, ektg__rucx)
        return scatterv_array_item_impl
    if isinstance(data, (IntegerArrayType, DecimalArrayType)) or data in (
        boolean_array, datetime_date_array_type):
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))
        if isinstance(data, IntegerArrayType):
            lgfwa__zkqsr = bodo.libs.int_arr_ext.init_integer_array
        if isinstance(data, DecimalArrayType):
            precision = data.precision
            scale = data.scale
            lgfwa__zkqsr = numba.njit(no_cpython_wrapper=True)(lambda d, b:
                bodo.libs.decimal_arr_ext.init_decimal_array(d, b,
                precision, scale))
        if data == boolean_array:
            lgfwa__zkqsr = bodo.libs.bool_arr_ext.init_bool_array
        if data == datetime_date_array_type:
            lgfwa__zkqsr = (bodo.hiframes.datetime_date_ext.
                init_datetime_date_array)

        def scatterv_impl_int_arr(data, send_counts=None, warn_if_dist=True):
            n_pes = bodo.libs.distributed_api.get_size()
            cgxs__caw = data._data
            tkf__inbj = data._null_bitmap
            evciu__ljd = len(cgxs__caw)
            nic__nbl = _scatterv_np(cgxs__caw, send_counts)
            caha__ofagw = bcast_scalar(evciu__ljd)
            pqe__ull = len(nic__nbl) + 7 >> 3
            aqr__dvp = np.empty(pqe__ull, np.uint8)
            send_counts = _get_scatterv_send_counts(send_counts, n_pes,
                caha__ofagw)
            fri__vbtnd = np.empty(n_pes, np.int32)
            for i in range(n_pes):
                fri__vbtnd[i] = send_counts[i] + 7 >> 3
            vosqh__sin = bodo.ir.join.calc_disp(fri__vbtnd)
            koopl__sfdhe = get_scatter_null_bytes_buff(tkf__inbj.ctypes,
                send_counts, fri__vbtnd)
            c_scatterv(koopl__sfdhe.ctypes, fri__vbtnd.ctypes, vosqh__sin.
                ctypes, aqr__dvp.ctypes, np.int32(pqe__ull), wusn__ymbfw)
            return lgfwa__zkqsr(nic__nbl, aqr__dvp)
        return scatterv_impl_int_arr
    if isinstance(data, IntervalArrayType):

        def impl_interval_arr(data, send_counts=None, warn_if_dist=True):
            zka__lxvhb = bodo.libs.distributed_api.scatterv_impl(data._left,
                send_counts)
            qaoes__ljpd = bodo.libs.distributed_api.scatterv_impl(data.
                _right, send_counts)
            return bodo.libs.interval_arr_ext.init_interval_array(zka__lxvhb,
                qaoes__ljpd)
        return impl_interval_arr
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):

        def impl_range_index(data, send_counts=None, warn_if_dist=True):
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            start = data._start
            stop = data._stop
            nuj__mhaw = data._step
            ejbbb__eisbl = data._name
            ejbbb__eisbl = bcast_scalar(ejbbb__eisbl)
            start = bcast_scalar(start)
            stop = bcast_scalar(stop)
            nuj__mhaw = bcast_scalar(nuj__mhaw)
            elb__xwndh = bodo.libs.array_kernels.calc_nitems(start, stop,
                nuj__mhaw)
            chunk_start = bodo.libs.distributed_api.get_start(elb__xwndh,
                n_pes, rank)
            chunk_count = bodo.libs.distributed_api.get_node_portion(elb__xwndh
                , n_pes, rank)
            raqcg__zqzmp = start + nuj__mhaw * chunk_start
            tdk__kioo = start + nuj__mhaw * (chunk_start + chunk_count)
            tdk__kioo = min(tdk__kioo, stop)
            return bodo.hiframes.pd_index_ext.init_range_index(raqcg__zqzmp,
                tdk__kioo, nuj__mhaw, ejbbb__eisbl)
        return impl_range_index
    if isinstance(data, bodo.hiframes.pd_index_ext.PeriodIndexType):
        fsb__risa = data.freq

        def impl_period_index(data, send_counts=None, warn_if_dist=True):
            cgxs__caw = data._data
            ejbbb__eisbl = data._name
            ejbbb__eisbl = bcast_scalar(ejbbb__eisbl)
            arr = bodo.libs.distributed_api.scatterv_impl(cgxs__caw,
                send_counts)
            return bodo.hiframes.pd_index_ext.init_period_index(arr,
                ejbbb__eisbl, fsb__risa)
        return impl_period_index
    if bodo.hiframes.pd_index_ext.is_pd_index_type(data):

        def impl_pd_index(data, send_counts=None, warn_if_dist=True):
            cgxs__caw = data._data
            ejbbb__eisbl = data._name
            ejbbb__eisbl = bcast_scalar(ejbbb__eisbl)
            arr = bodo.libs.distributed_api.scatterv_impl(cgxs__caw,
                send_counts)
            return bodo.utils.conversion.index_from_array(arr, ejbbb__eisbl)
        return impl_pd_index
    if isinstance(data, bodo.hiframes.pd_multi_index_ext.MultiIndexType):

        def impl_multi_index(data, send_counts=None, warn_if_dist=True):
            dgbgr__lyguc = bodo.libs.distributed_api.scatterv_impl(data.
                _data, send_counts)
            ejbbb__eisbl = bcast_scalar(data._name)
            yps__qylux = bcast_tuple(data._names)
            return bodo.hiframes.pd_multi_index_ext.init_multi_index(
                dgbgr__lyguc, yps__qylux, ejbbb__eisbl)
        return impl_multi_index
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl_series(data, send_counts=None, warn_if_dist=True):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            ejbbb__eisbl = bodo.hiframes.pd_series_ext.get_series_name(data)
            runsh__tnbx = bcast_scalar(ejbbb__eisbl)
            out_arr = bodo.libs.distributed_api.scatterv_impl(arr, send_counts)
            ing__gzf = bodo.libs.distributed_api.scatterv_impl(index,
                send_counts)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                ing__gzf, runsh__tnbx)
        return impl_series
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        izz__qvi = len(data.columns)
        muua__mkk = ', '.join('g_data_{}'.format(i) for i in range(izz__qvi))
        rqdh__hsh = bodo.utils.transform.gen_const_tup(data.columns)
        ngew__ooz = 'def impl_df(data, send_counts=None, warn_if_dist=True):\n'
        for i in range(izz__qvi):
            ngew__ooz += (
                """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                .format(i, i))
            ngew__ooz += (
                """  g_data_{} = bodo.libs.distributed_api.scatterv_impl(data_{}, send_counts)
"""
                .format(i, i))
        ngew__ooz += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        ngew__ooz += (
            '  g_index = bodo.libs.distributed_api.scatterv_impl(index, send_counts)\n'
            )
        ngew__ooz += (
            '  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})\n'
            .format(muua__mkk, rqdh__hsh))
        cjbt__mun = {}
        exec(ngew__ooz, {'bodo': bodo}, cjbt__mun)
        fhbex__cehhn = cjbt__mun['impl_df']
        return fhbex__cehhn
    if isinstance(data, CategoricalArrayType):

        def impl_cat(data, send_counts=None, warn_if_dist=True):
            xmdui__eqdn = bodo.libs.distributed_api.scatterv_impl(data.
                codes, send_counts)
            return bodo.hiframes.pd_categorical_ext.init_categorical_array(
                xmdui__eqdn, data.dtype)
        return impl_cat
    if isinstance(data, types.BaseTuple):
        ngew__ooz = (
            'def impl_tuple(data, send_counts=None, warn_if_dist=True):\n')
        ngew__ooz += '  return ({}{})\n'.format(', '.join(
            'bodo.libs.distributed_api.scatterv_impl(data[{}], send_counts)'
            .format(i) for i in range(len(data))), ',' if len(data) > 0 else ''
            )
        cjbt__mun = {}
        exec(ngew__ooz, {'bodo': bodo}, cjbt__mun)
        mxx__yay = cjbt__mun['impl_tuple']
        return mxx__yay
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
        zbzo__yahh = np.int32(numba_to_c_type(offset_type))
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))

        def bcast_str_impl(data, root=MPI_ROOT):
            data = decode_if_dict_array(data)
            zjlj__rmdwp = len(data)
            yutrl__lmln = num_total_chars(data)
            assert zjlj__rmdwp < INT_MAX
            assert yutrl__lmln < INT_MAX
            bqj__gxwae = get_offset_ptr(data)
            jje__qutqy = get_data_ptr(data)
            null_bitmap_ptr = get_null_bitmap_ptr(data)
            pdx__syci = zjlj__rmdwp + 7 >> 3
            c_bcast(bqj__gxwae, np.int32(zjlj__rmdwp + 1), zbzo__yahh, np.
                array([-1]).ctypes, 0, np.int32(root))
            c_bcast(jje__qutqy, np.int32(yutrl__lmln), wusn__ymbfw, np.
                array([-1]).ctypes, 0, np.int32(root))
            c_bcast(null_bitmap_ptr, np.int32(pdx__syci), wusn__ymbfw, np.
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
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))

        def impl_str(val, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            if rank != root:
                nni__rctt = 0
                wtotb__pzjbc = np.empty(0, np.uint8).ctypes
            else:
                wtotb__pzjbc, nni__rctt = (bodo.libs.str_ext.
                    unicode_to_utf8_and_len(val))
            nni__rctt = bodo.libs.distributed_api.bcast_scalar(nni__rctt, root)
            if rank != root:
                tlnx__neeg = np.empty(nni__rctt + 1, np.uint8)
                tlnx__neeg[nni__rctt] = 0
                wtotb__pzjbc = tlnx__neeg.ctypes
            c_bcast(wtotb__pzjbc, np.int32(nni__rctt), wusn__ymbfw, np.
                array([-1]).ctypes, 0, np.int32(root))
            return bodo.libs.str_arr_ext.decode_utf8(wtotb__pzjbc, nni__rctt)
        return impl_str
    typ_val = numba_to_c_type(val)
    ngew__ooz = f"""def bcast_scalar_impl(val, root={MPI_ROOT}):
  send = np.empty(1, dtype)
  send[0] = val
  c_bcast(send.ctypes, np.int32(1), np.int32({typ_val}), np.array([-1]).ctypes, 0, np.int32(root))
  return send[0]
"""
    dtype = numba.np.numpy_support.as_dtype(val)
    cjbt__mun = {}
    exec(ngew__ooz, {'bodo': bodo, 'np': np, 'c_bcast': c_bcast, 'dtype':
        dtype}, cjbt__mun)
    rnesd__vjjj = cjbt__mun['bcast_scalar_impl']
    return rnesd__vjjj


@numba.generated_jit(nopython=True)
def bcast_tuple(val, root=MPI_ROOT):
    assert isinstance(val, types.BaseTuple)
    xmw__wejx = len(val)
    ngew__ooz = f'def bcast_tuple_impl(val, root={MPI_ROOT}):\n'
    ngew__ooz += '  return ({}{})'.format(','.join(
        'bcast_scalar(val[{}], root)'.format(i) for i in range(xmw__wejx)),
        ',' if xmw__wejx else '')
    cjbt__mun = {}
    exec(ngew__ooz, {'bcast_scalar': bcast_scalar}, cjbt__mun)
    hgvsp__xnp = cjbt__mun['bcast_tuple_impl']
    return hgvsp__xnp


def prealloc_str_for_bcast(arr, root=MPI_ROOT):
    return arr


@overload(prealloc_str_for_bcast, no_unliteral=True)
def prealloc_str_for_bcast_overload(arr, root=MPI_ROOT):
    if arr == string_array_type:

        def prealloc_impl(arr, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            zjlj__rmdwp = bcast_scalar(len(arr), root)
            kyzt__ybhoh = bcast_scalar(np.int64(num_total_chars(arr)), root)
            if rank != root:
                arr = pre_alloc_string_array(zjlj__rmdwp, kyzt__ybhoh)
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
        nuj__mhaw = slice_index.step
        zlnph__ocmzb = 0 if nuj__mhaw == 1 or start > arr_start else abs(
            nuj__mhaw - arr_start % nuj__mhaw) % nuj__mhaw
        raqcg__zqzmp = max(arr_start, slice_index.start
            ) - arr_start + zlnph__ocmzb
        tdk__kioo = max(slice_index.stop - arr_start, 0)
        return slice(raqcg__zqzmp, tdk__kioo, nuj__mhaw)
    return impl


def slice_getitem(arr, slice_index, arr_start, total_len):
    return arr[slice_index]


@overload(slice_getitem, no_unliteral=True, jit_options={'cache': True})
def slice_getitem_overload(arr, slice_index, arr_start, total_len):

    def getitem_impl(arr, slice_index, arr_start, total_len):
        hfvo__eiipt = get_local_slice(slice_index, arr_start, total_len)
        return bodo.utils.conversion.ensure_contig_if_np(arr[hfvo__eiipt])
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
        dkqb__bhosn = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND
        wusn__ymbfw = np.int32(numba_to_c_type(types.uint8))
        psjz__dpbch = arr.dtype

        def str_getitem_impl(arr, ind, arr_start, total_len, is_1D):
            if ind >= total_len:
                raise IndexError('index out of bounds')
            arr = decode_if_dict_array(arr)
            ind = ind % total_len
            root = np.int32(0)
            wxdws__sgg = np.int32(10)
            tag = np.int32(11)
            dwiw__ori = np.zeros(1, np.int64)
            if arr_start <= ind < arr_start + len(arr):
                ind = ind - arr_start
                slfdu__poe = arr._data
                dnu__afy = bodo.libs.array_item_arr_ext.get_offsets_ind(
                    slfdu__poe, ind)
                qbckl__cdwg = bodo.libs.array_item_arr_ext.get_offsets_ind(
                    slfdu__poe, ind + 1)
                length = qbckl__cdwg - dnu__afy
                qwdtt__imld = slfdu__poe[ind]
                dwiw__ori[0] = length
                isend(dwiw__ori, np.int32(1), root, wxdws__sgg, True)
                isend(qwdtt__imld, np.int32(length), root, tag, True)
            rank = bodo.libs.distributed_api.get_rank()
            val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(
                psjz__dpbch, dkqb__bhosn, 0, 1)
            joyj__rhfu = 0
            if rank == root:
                joyj__rhfu = recv(np.int64, ANY_SOURCE, wxdws__sgg)
                val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(
                    psjz__dpbch, dkqb__bhosn, joyj__rhfu, 1)
                jje__qutqy = bodo.libs.str_ext.get_unicode_or_numpy_data(val)
                _recv(jje__qutqy, np.int32(joyj__rhfu), wusn__ymbfw,
                    ANY_SOURCE, tag)
            dummy_use(dwiw__ori)
            joyj__rhfu = bcast_scalar(joyj__rhfu)
            dummy_use(arr)
            if rank != root:
                val = bodo.libs.str_ext.alloc_empty_bytes_or_string_data(
                    psjz__dpbch, dkqb__bhosn, joyj__rhfu, 1)
            jje__qutqy = bodo.libs.str_ext.get_unicode_or_numpy_data(val)
            c_bcast(jje__qutqy, np.int32(joyj__rhfu), wusn__ymbfw, np.array
                ([-1]).ctypes, 0, np.int32(root))
            val = transform_str_getitem_output(val, joyj__rhfu)
            return val
        return str_getitem_impl
    if isinstance(arr, bodo.CategoricalArrayType):
        vdgfl__sns = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            arr.dtype)

        def cat_getitem_impl(arr, ind, arr_start, total_len, is_1D):
            if ind >= total_len:
                raise IndexError('index out of bounds')
            ind = ind % total_len
            root = np.int32(0)
            tag = np.int32(11)
            send_arr = np.zeros(1, vdgfl__sns)
            if arr_start <= ind < arr_start + len(arr):
                xmdui__eqdn = (bodo.hiframes.pd_categorical_ext.
                    get_categorical_arr_codes(arr))
                data = xmdui__eqdn[ind - arr_start]
                send_arr = np.full(1, data, vdgfl__sns)
                isend(send_arr, np.int32(1), root, tag, True)
            rank = bodo.libs.distributed_api.get_rank()
            val = vdgfl__sns(-1)
            if rank == root:
                val = recv(vdgfl__sns, ANY_SOURCE, tag)
            dummy_use(send_arr)
            val = bcast_scalar(val)
            dnd__wadej = arr.dtype.categories[max(val, 0)]
            return dnd__wadej
        return cat_getitem_impl
    bzvi__azs = arr.dtype

    def getitem_impl(arr, ind, arr_start, total_len, is_1D):
        if ind >= total_len:
            raise IndexError('index out of bounds')
        ind = ind % total_len
        root = np.int32(0)
        tag = np.int32(11)
        send_arr = np.zeros(1, bzvi__azs)
        if arr_start <= ind < arr_start + len(arr):
            data = arr[ind - arr_start]
            send_arr = np.full(1, data)
            isend(send_arr, np.int32(1), root, tag, True)
        rank = bodo.libs.distributed_api.get_rank()
        val = np.zeros(1, bzvi__azs)[0]
        if rank == root:
            val = recv(bzvi__azs, ANY_SOURCE, tag)
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
    nwv__dmyym = get_type_enum(out_data)
    assert typ_enum == nwv__dmyym
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
    ngew__ooz = (
        'def f(send_data, out_data, send_counts, recv_counts, send_disp, recv_disp):\n'
        )
    for i in range(count):
        ngew__ooz += (
            """  alltoallv(send_data[{}], out_data[{}], send_counts, recv_counts, send_disp, recv_disp)
"""
            .format(i, i))
    ngew__ooz += '  return\n'
    cjbt__mun = {}
    exec(ngew__ooz, {'alltoallv': alltoallv}, cjbt__mun)
    omxv__kgrn = cjbt__mun['f']
    return omxv__kgrn


@numba.njit
def get_start_count(n):
    rank = bodo.libs.distributed_api.get_rank()
    n_pes = bodo.libs.distributed_api.get_size()
    start = bodo.libs.distributed_api.get_start(n, n_pes, rank)
    count = bodo.libs.distributed_api.get_node_portion(n, n_pes, rank)
    return start, count


@numba.njit
def get_start(total_size, pes, rank):
    ihqz__aude = total_size % pes
    jsh__qtg = (total_size - ihqz__aude) // pes
    return rank * jsh__qtg + min(rank, ihqz__aude)


@numba.njit
def get_end(total_size, pes, rank):
    ihqz__aude = total_size % pes
    jsh__qtg = (total_size - ihqz__aude) // pes
    return (rank + 1) * jsh__qtg + min(rank + 1, ihqz__aude)


@numba.njit
def get_node_portion(total_size, pes, rank):
    ihqz__aude = total_size % pes
    jsh__qtg = (total_size - ihqz__aude) // pes
    if rank < ihqz__aude:
        return jsh__qtg + 1
    else:
        return jsh__qtg


@numba.generated_jit(nopython=True)
def dist_cumsum(in_arr, out_arr):
    atih__stdxg = in_arr.dtype(0)
    wlylh__ltrwg = np.int32(Reduce_Type.Sum.value)

    def cumsum_impl(in_arr, out_arr):
        uar__zkp = atih__stdxg
        for vfme__bhbu in np.nditer(in_arr):
            uar__zkp += vfme__bhbu.item()
        vefhg__hqask = dist_exscan(uar__zkp, wlylh__ltrwg)
        for i in range(in_arr.size):
            vefhg__hqask += in_arr[i]
            out_arr[i] = vefhg__hqask
        return 0
    return cumsum_impl


@numba.generated_jit(nopython=True)
def dist_cumprod(in_arr, out_arr):
    qfiw__viz = in_arr.dtype(1)
    wlylh__ltrwg = np.int32(Reduce_Type.Prod.value)

    def cumprod_impl(in_arr, out_arr):
        uar__zkp = qfiw__viz
        for vfme__bhbu in np.nditer(in_arr):
            uar__zkp *= vfme__bhbu.item()
        vefhg__hqask = dist_exscan(uar__zkp, wlylh__ltrwg)
        if get_rank() == 0:
            vefhg__hqask = qfiw__viz
        for i in range(in_arr.size):
            vefhg__hqask *= in_arr[i]
            out_arr[i] = vefhg__hqask
        return 0
    return cumprod_impl


@numba.generated_jit(nopython=True)
def dist_cummin(in_arr, out_arr):
    if isinstance(in_arr.dtype, types.Float):
        qfiw__viz = np.finfo(in_arr.dtype(1).dtype).max
    else:
        qfiw__viz = np.iinfo(in_arr.dtype(1).dtype).max
    wlylh__ltrwg = np.int32(Reduce_Type.Min.value)

    def cummin_impl(in_arr, out_arr):
        uar__zkp = qfiw__viz
        for vfme__bhbu in np.nditer(in_arr):
            uar__zkp = min(uar__zkp, vfme__bhbu.item())
        vefhg__hqask = dist_exscan(uar__zkp, wlylh__ltrwg)
        if get_rank() == 0:
            vefhg__hqask = qfiw__viz
        for i in range(in_arr.size):
            vefhg__hqask = min(vefhg__hqask, in_arr[i])
            out_arr[i] = vefhg__hqask
        return 0
    return cummin_impl


@numba.generated_jit(nopython=True)
def dist_cummax(in_arr, out_arr):
    if isinstance(in_arr.dtype, types.Float):
        qfiw__viz = np.finfo(in_arr.dtype(1).dtype).min
    else:
        qfiw__viz = np.iinfo(in_arr.dtype(1).dtype).min
    qfiw__viz = in_arr.dtype(1)
    wlylh__ltrwg = np.int32(Reduce_Type.Max.value)

    def cummax_impl(in_arr, out_arr):
        uar__zkp = qfiw__viz
        for vfme__bhbu in np.nditer(in_arr):
            uar__zkp = max(uar__zkp, vfme__bhbu.item())
        vefhg__hqask = dist_exscan(uar__zkp, wlylh__ltrwg)
        if get_rank() == 0:
            vefhg__hqask = qfiw__viz
        for i in range(in_arr.size):
            vefhg__hqask = max(vefhg__hqask, in_arr[i])
            out_arr[i] = vefhg__hqask
        return 0
    return cummax_impl


_allgather = types.ExternalFunction('allgather', types.void(types.voidptr,
    types.int32, types.voidptr, types.int32))


@numba.njit
def allgather(arr, val):
    qaydt__wrzo = get_type_enum(arr)
    _allgather(arr.ctypes, 1, value_to_ptr(val), qaydt__wrzo)


def dist_return(A):
    return A


def rep_return(A):
    return A


def dist_return_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    bpiwt__bgbua = args[0]
    if equiv_set.has_shape(bpiwt__bgbua):
        return ArrayAnalysis.AnalyzeResult(shape=bpiwt__bgbua, pre=[])
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
        gippy__gfg = ','.join(f'_wait(req[{i}], cond)' for i in range(count))
        ngew__ooz = 'def f(req, cond=True):\n'
        ngew__ooz += f'  return {gippy__gfg}\n'
        cjbt__mun = {}
        exec(ngew__ooz, {'_wait': _wait}, cjbt__mun)
        impl = cjbt__mun['f']
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
    raqcg__zqzmp = max(start, chunk_start)
    tdk__kioo = min(stop, chunk_start + chunk_count)
    idjz__piu = raqcg__zqzmp - chunk_start
    zmrl__scutk = tdk__kioo - chunk_start
    if idjz__piu < 0 or zmrl__scutk < 0:
        idjz__piu = 1
        zmrl__scutk = 0
    return idjz__piu, zmrl__scutk


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
        ihqz__aude = 1
        for a in t:
            ihqz__aude *= a
        return ihqz__aude
    return get_tuple_prod_impl


sig = types.void(types.voidptr, types.voidptr, types.intp, types.intp,
    types.intp, types.intp, types.int32, types.voidptr)
oneD_reshape_shuffle = types.ExternalFunction('oneD_reshape_shuffle', sig)


@numba.njit(no_cpython_wrapper=True, cache=True)
def dist_oneD_reshape_shuffle(lhs, in_arr, new_dim0_global_len, dest_ranks=None
    ):
    met__bfu = np.ascontiguousarray(in_arr)
    jlptf__aqmu = get_tuple_prod(met__bfu.shape[1:])
    byi__ugkm = get_tuple_prod(lhs.shape[1:])
    if dest_ranks is not None:
        nzs__pntqw = np.array(dest_ranks, dtype=np.int32)
    else:
        nzs__pntqw = np.empty(0, dtype=np.int32)
    dtype_size = bodo.io.np_io.get_dtype_size(in_arr.dtype)
    oneD_reshape_shuffle(lhs.ctypes, met__bfu.ctypes, new_dim0_global_len,
        len(in_arr), dtype_size * byi__ugkm, dtype_size * jlptf__aqmu, len(
        nzs__pntqw), nzs__pntqw.ctypes)
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
    wow__dljci = np.ascontiguousarray(rhs)
    jmd__gqa = get_tuple_prod(wow__dljci.shape[1:])
    ogoh__afz = dtype_size * jmd__gqa
    permutation_array_index(lhs.ctypes, lhs_len, ogoh__afz, wow__dljci.
        ctypes, wow__dljci.shape[0], p.ctypes, p_len)
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
        ngew__ooz = (
            f"""def bcast_scalar_impl(data, comm_ranks, nranks, root={MPI_ROOT}):
  send = np.empty(1, dtype)
  send[0] = data
  c_bcast(send.ctypes, np.int32(1), np.int32({{}}), comm_ranks,ctypes, np.int32({{}}), np.int32(root))
  return send[0]
"""
            .format(typ_val, nranks))
        dtype = numba.np.numpy_support.as_dtype(data)
        cjbt__mun = {}
        exec(ngew__ooz, {'bodo': bodo, 'np': np, 'c_bcast': c_bcast,
            'dtype': dtype}, cjbt__mun)
        rnesd__vjjj = cjbt__mun['bcast_scalar_impl']
        return rnesd__vjjj
    if isinstance(data, types.Array):
        return lambda data, comm_ranks, nranks, root=MPI_ROOT: _bcast_np(data,
            comm_ranks, nranks, root)
    if isinstance(data, bodo.hiframes.pd_dataframe_ext.DataFrameType):
        izz__qvi = len(data.columns)
        muua__mkk = ', '.join('g_data_{}'.format(i) for i in range(izz__qvi))
        rqdh__hsh = bodo.utils.transform.gen_const_tup(data.columns)
        ngew__ooz = (
            f'def impl_df(data, comm_ranks, nranks, root={MPI_ROOT}):\n')
        for i in range(izz__qvi):
            ngew__ooz += (
                """  data_{} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(data, {})
"""
                .format(i, i))
            ngew__ooz += (
                """  g_data_{} = bodo.libs.distributed_api.bcast_comm_impl(data_{}, comm_ranks, nranks, root)
"""
                .format(i, i))
        ngew__ooz += (
            '  index = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(data)\n'
            )
        ngew__ooz += """  g_index = bodo.libs.distributed_api.bcast_comm_impl(index, comm_ranks, nranks, root)
"""
        ngew__ooz += (
            '  return bodo.hiframes.pd_dataframe_ext.init_dataframe(({},), g_index, {})\n'
            .format(muua__mkk, rqdh__hsh))
        cjbt__mun = {}
        exec(ngew__ooz, {'bodo': bodo}, cjbt__mun)
        fhbex__cehhn = cjbt__mun['impl_df']
        return fhbex__cehhn
    if isinstance(data, bodo.hiframes.pd_index_ext.RangeIndexType):

        def impl_range_index(data, comm_ranks, nranks, root=MPI_ROOT):
            rank = bodo.libs.distributed_api.get_rank()
            n_pes = bodo.libs.distributed_api.get_size()
            start = data._start
            stop = data._stop
            nuj__mhaw = data._step
            ejbbb__eisbl = data._name
            ejbbb__eisbl = bcast_scalar(ejbbb__eisbl, root)
            start = bcast_scalar(start, root)
            stop = bcast_scalar(stop, root)
            nuj__mhaw = bcast_scalar(nuj__mhaw, root)
            elb__xwndh = bodo.libs.array_kernels.calc_nitems(start, stop,
                nuj__mhaw)
            chunk_start = bodo.libs.distributed_api.get_start(elb__xwndh,
                n_pes, rank)
            chunk_count = bodo.libs.distributed_api.get_node_portion(elb__xwndh
                , n_pes, rank)
            raqcg__zqzmp = start + nuj__mhaw * chunk_start
            tdk__kioo = start + nuj__mhaw * (chunk_start + chunk_count)
            tdk__kioo = min(tdk__kioo, stop)
            return bodo.hiframes.pd_index_ext.init_range_index(raqcg__zqzmp,
                tdk__kioo, nuj__mhaw, ejbbb__eisbl)
        return impl_range_index
    if bodo.hiframes.pd_index_ext.is_pd_index_type(data):

        def impl_pd_index(data, comm_ranks, nranks, root=MPI_ROOT):
            cgxs__caw = data._data
            ejbbb__eisbl = data._name
            arr = bodo.libs.distributed_api.bcast_comm_impl(cgxs__caw,
                comm_ranks, nranks, root)
            return bodo.utils.conversion.index_from_array(arr, ejbbb__eisbl)
        return impl_pd_index
    if isinstance(data, bodo.hiframes.pd_series_ext.SeriesType):

        def impl_series(data, comm_ranks, nranks, root=MPI_ROOT):
            arr = bodo.hiframes.pd_series_ext.get_series_data(data)
            index = bodo.hiframes.pd_series_ext.get_series_index(data)
            ejbbb__eisbl = bodo.hiframes.pd_series_ext.get_series_name(data)
            runsh__tnbx = bodo.libs.distributed_api.bcast_comm_impl(
                ejbbb__eisbl, comm_ranks, nranks, root)
            out_arr = bodo.libs.distributed_api.bcast_comm_impl(arr,
                comm_ranks, nranks, root)
            ing__gzf = bodo.libs.distributed_api.bcast_comm_impl(index,
                comm_ranks, nranks, root)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                ing__gzf, runsh__tnbx)
        return impl_series
    if isinstance(data, types.BaseTuple):
        ngew__ooz = (
            f'def impl_tuple(data, comm_ranks, nranks, root={MPI_ROOT}):\n')
        ngew__ooz += '  return ({}{})\n'.format(', '.join(
            'bcast_comm_impl(data[{}], comm_ranks, nranks, root)'.format(i) for
            i in range(len(data))), ',' if len(data) > 0 else '')
        cjbt__mun = {}
        exec(ngew__ooz, {'bcast_comm_impl': bcast_comm_impl}, cjbt__mun)
        mxx__yay = cjbt__mun['impl_tuple']
        return mxx__yay
    if data is types.none:
        return lambda data, comm_ranks, nranks, root=MPI_ROOT: None


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _bcast_np(data, comm_ranks, nranks, root=MPI_ROOT):
    typ_val = numba_to_c_type(data.dtype)
    vzm__iwouw = data.ndim
    dtype = data.dtype
    if dtype == types.NPDatetime('ns'):
        dtype = np.dtype('datetime64[ns]')
    elif dtype == types.NPTimedelta('ns'):
        dtype = np.dtype('timedelta64[ns]')
    qszm__bgn = (0,) * vzm__iwouw

    def bcast_arr_impl(data, comm_ranks, nranks, root=MPI_ROOT):
        rank = bodo.libs.distributed_api.get_rank()
        cgxs__caw = np.ascontiguousarray(data)
        jje__qutqy = data.ctypes
        xoer__ulx = qszm__bgn
        if rank == root:
            xoer__ulx = cgxs__caw.shape
        xoer__ulx = bcast_tuple(xoer__ulx, root)
        rogmn__bgfun = get_tuple_prod(xoer__ulx[1:])
        send_counts = xoer__ulx[0] * rogmn__bgfun
        rznn__wanzf = np.empty(send_counts, dtype)
        if rank == MPI_ROOT:
            c_bcast(jje__qutqy, np.int32(send_counts), np.int32(typ_val),
                comm_ranks.ctypes, np.int32(nranks), np.int32(root))
            return data
        else:
            c_bcast(rznn__wanzf.ctypes, np.int32(send_counts), np.int32(
                typ_val), comm_ranks.ctypes, np.int32(nranks), np.int32(root))
            return rznn__wanzf.reshape((-1,) + xoer__ulx[1:])
    return bcast_arr_impl


node_ranks = None


def get_host_ranks():
    global node_ranks
    if node_ranks is None:
        pwzx__djvq = MPI.COMM_WORLD
        fcic__tpcjc = MPI.Get_processor_name()
        apdlw__beju = pwzx__djvq.allgather(fcic__tpcjc)
        node_ranks = defaultdict(list)
        for i, hah__olcfs in enumerate(apdlw__beju):
            node_ranks[hah__olcfs].append(i)
    return node_ranks


def create_subcomm_mpi4py(comm_ranks):
    pwzx__djvq = MPI.COMM_WORLD
    rbl__jpfo = pwzx__djvq.Get_group()
    zsjej__prd = rbl__jpfo.Incl(comm_ranks)
    htayn__hnmu = pwzx__djvq.Create_group(zsjej__prd)
    return htayn__hnmu


def get_nodes_first_ranks():
    esy__hdb = get_host_ranks()
    return np.array([yge__zsrai[0] for yge__zsrai in esy__hdb.values()],
        dtype='int32')


def get_num_nodes():
    return len(get_host_ranks())
