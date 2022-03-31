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
    ayfi__ohdm = MPI.COMM_WORLD
    hgh__vllml = ayfi__ohdm.Get_rank()
    aowsf__qiyia = get_host_ranks()
    bum__pfqlr = get_nodes_first_ranks()
    if hgh__vllml in bum__pfqlr:
        try:
            fsxn__vmoi = get_num_gpus(framework)
        except Exception as wdk__vxuuy:
            fsxn__vmoi = wdk__vxuuy
        veq__tvdz = create_subcomm_mpi4py(bum__pfqlr)
        sewv__ydk = veq__tvdz.gather(fsxn__vmoi)
        if hgh__vllml == 0:
            gpu_ranks = []
            qjk__oel = None
            for tnozf__vohf, rstit__nacvm in enumerate(aowsf__qiyia.values()):
                cyxf__sgge = sewv__ydk[tnozf__vohf]
                if isinstance(cyxf__sgge, Exception):
                    qjk__oel = cyxf__sgge
                    break
                if cyxf__sgge == 0:
                    continue
                xug__pae = len(rstit__nacvm) // cyxf__sgge
                for famd__kiinu, azmv__xgdnd in enumerate(rstit__nacvm):
                    if famd__kiinu % xug__pae == 0:
                        mqlf__aklh = famd__kiinu / xug__pae
                        if mqlf__aklh < cyxf__sgge:
                            gpu_ranks.append(azmv__xgdnd)
            if qjk__oel:
                ayfi__ohdm.bcast(qjk__oel)
                raise qjk__oel
            else:
                ayfi__ohdm.bcast(gpu_ranks)
    if hgh__vllml != 0:
        gpu_ranks = ayfi__ohdm.bcast(None)
        if isinstance(gpu_ranks, Exception):
            wdk__vxuuy = gpu_ranks
            raise wdk__vxuuy
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
    dztl__bohw = MPI.COMM_WORLD.rank
    if len(gpu_ranks) > 0:
        veq__tvdz = MPI.COMM_WORLD.Split(color=0 if dztl__bohw in gpu_ranks
             else MPI.UNDEFINED, key=dztl__bohw)
        if veq__tvdz != MPI.COMM_NULL:
            hvd.init(comm=veq__tvdz)
            if framework == 'torch':
                torch.cuda.set_device(hvd.local_rank())
            elif framework == 'tensorflow':
                abgj__dsu = tf.config.experimental.list_physical_devices('GPU')
                for hpcma__udx in abgj__dsu:
                    tf.config.experimental.set_memory_growth(hpcma__udx, True)
                tf.config.experimental.set_visible_devices(abgj__dsu[hvd.
                    local_rank()], 'GPU')
    else:
        if dztl__bohw == 0:
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
        yki__kejs = 17
        ayfi__ohdm = MPI.COMM_WORLD
        zekmt__puxts = MPI.Get_processor_name()
        rfbms__uziwm = get_host_ranks()[zekmt__puxts]
        assert_dl_initialized()
        if bodo.get_rank() == rfbms__uziwm[0]:
            assert bodo.get_rank() in dl_status.gpu_ranks
            for hgh__vllml in rfbms__uziwm[1:]:
                ayfi__ohdm.isend(1, dest=hgh__vllml, tag=yki__kejs)
        else:
            while True:
                bils__ywef = MPI.Status()
                ryh__lmz = ayfi__ohdm.Iprobe(MPI.ANY_SOURCE, MPI.ANY_TAG,
                    bils__ywef)
                if ryh__lmz:
                    assert bils__ywef.source == rfbms__uziwm[0]
                    assert bils__ywef.tag == yki__kejs
                    ayfi__ohdm.recv(source=0, tag=yki__kejs)
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
