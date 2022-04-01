"""Support distributed deep learning with Horovod
"""
import time
import numba
import numpy as np
from mpi4py import MPI
import bodo
from bodo.libs.distributed_api import create_subcomm_mpi4py, get_host_ranks, get_nodes_first_ranks
dl_status = None


def assert_dl_initialized():
    assert dl_status is not None, 'Horovod has not been initialized. Call bodo.dl.start() first'


class DLStatus(object):

    def __init__(self, framework, gpu_ranks):
        self.framework = framework
        self.gpu_ranks = gpu_ranks


def get_num_gpus(framework):
    if framework == 'torch':
        import torch
        return torch.cuda.device_count()
    elif framework == 'tensorflow':
        import tensorflow as tf
        return len(tf.config.experimental.list_physical_devices('GPU'))
    else:
        raise RuntimeError('Framework {} not recognized'.format(framework))


def get_gpu_ranks(framework):
    uqp__dpzf = MPI.COMM_WORLD
    xjshz__xsm = uqp__dpzf.Get_rank()
    bbijz__kwz = get_host_ranks()
    qmt__zbass = get_nodes_first_ranks()
    if xjshz__xsm in qmt__zbass:
        try:
            zckze__aldn = get_num_gpus(framework)
        except Exception as qgj__ela:
            zckze__aldn = qgj__ela
        xtnhz__swwcm = create_subcomm_mpi4py(qmt__zbass)
        kpqe__jfi = xtnhz__swwcm.gather(zckze__aldn)
        if xjshz__xsm == 0:
            gpu_ranks = []
            zhstt__bflm = None
            for coygp__hbkv, cmh__icvm in enumerate(bbijz__kwz.values()):
                kfjgf__gcig = kpqe__jfi[coygp__hbkv]
                if isinstance(kfjgf__gcig, Exception):
                    zhstt__bflm = kfjgf__gcig
                    break
                if kfjgf__gcig == 0:
                    continue
                fjhpa__esnq = len(cmh__icvm) // kfjgf__gcig
                for lljhd__zzb, gkor__kaa in enumerate(cmh__icvm):
                    if lljhd__zzb % fjhpa__esnq == 0:
                        ttjk__gbz = lljhd__zzb / fjhpa__esnq
                        if ttjk__gbz < kfjgf__gcig:
                            gpu_ranks.append(gkor__kaa)
            if zhstt__bflm:
                uqp__dpzf.bcast(zhstt__bflm)
                raise zhstt__bflm
            else:
                uqp__dpzf.bcast(gpu_ranks)
    if xjshz__xsm != 0:
        gpu_ranks = uqp__dpzf.bcast(None)
        if isinstance(gpu_ranks, Exception):
            qgj__ela = gpu_ranks
            raise qgj__ela
    return gpu_ranks


def is_cuda_available():
    assert_dl_initialized()
    return len(dl_status.gpu_ranks) > 0


def initialize_horovod(framework):
    global dl_status
    if dl_status is not None:
        assert dl_status.framework == framework, 'Attempted to initialize Horovod with different DL frameworks'
        return np.array(dl_status.gpu_ranks, dtype=np.int32)
    gpu_ranks = get_gpu_ranks(framework)
    if framework == 'torch':
        import horovod.torch as hvd
        import torch
        torch.set_num_threads(1)
    elif framework == 'tensorflow':
        import horovod.tensorflow as hvd
        import tensorflow as tf
    else:
        raise RuntimeError('Framework {} not recognized'.format(framework))
    rdmg__sty = MPI.COMM_WORLD.rank
    if len(gpu_ranks) > 0:
        xtnhz__swwcm = MPI.COMM_WORLD.Split(color=0 if rdmg__sty in
            gpu_ranks else MPI.UNDEFINED, key=rdmg__sty)
        if xtnhz__swwcm != MPI.COMM_NULL:
            hvd.init(comm=xtnhz__swwcm)
            if framework == 'torch':
                torch.cuda.set_device(hvd.local_rank())
            elif framework == 'tensorflow':
                dwgtn__ibqbw = tf.config.experimental.list_physical_devices(
                    'GPU')
                for tlm__zew in dwgtn__ibqbw:
                    tf.config.experimental.set_memory_growth(tlm__zew, True)
                tf.config.experimental.set_visible_devices(dwgtn__ibqbw[hvd
                    .local_rank()], 'GPU')
    else:
        if rdmg__sty == 0:
            print('[BODO-DL]: No GPUs found in cluster. Using CPUs')
        hvd.init()
    dl_status = DLStatus(framework, np.array(gpu_ranks, dtype=np.int32))


@numba.njit
def start(framework):
    with numba.objmode:
        initialize_horovod(framework)


@numba.njit
def end():
    with numba.objmode:
        end_py()


def end_py():
    if is_cuda_available():
        goasz__dpuwv = 17
        uqp__dpzf = MPI.COMM_WORLD
        gbfmy__ouy = MPI.Get_processor_name()
        bfu__unzuu = get_host_ranks()[gbfmy__ouy]
        assert_dl_initialized()
        if bodo.get_rank() == bfu__unzuu[0]:
            assert bodo.get_rank() in dl_status.gpu_ranks
            for xjshz__xsm in bfu__unzuu[1:]:
                uqp__dpzf.isend(1, dest=xjshz__xsm, tag=goasz__dpuwv)
        else:
            while True:
                gnyia__tlt = MPI.Status()
                guo__fbe = uqp__dpzf.Iprobe(MPI.ANY_SOURCE, MPI.ANY_TAG,
                    gnyia__tlt)
                if guo__fbe:
                    assert gnyia__tlt.source == bfu__unzuu[0]
                    assert gnyia__tlt.tag == goasz__dpuwv
                    uqp__dpzf.recv(source=0, tag=goasz__dpuwv)
                    break
                time.sleep(1.0)
    else:
        bodo.barrier()


def _prepare_data_get_gpu_ranks():
    assert_dl_initialized()
    return dl_status.gpu_ranks


@numba.njit
def prepare_data(data):
    with numba.objmode(gpu_ranks='int32[:]'):
        gpu_ranks = _prepare_data_get_gpu_ranks()
    if len(gpu_ranks) > 0:
        data = bodo.rebalance(data, dests=list(gpu_ranks), parallel=True)
    else:
        data = bodo.rebalance(data, parallel=True)
    return data
