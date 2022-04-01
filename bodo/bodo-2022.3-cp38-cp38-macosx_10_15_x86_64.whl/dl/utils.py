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
    sjwbr__wmtzh = MPI.COMM_WORLD
    tvq__fojnx = sjwbr__wmtzh.Get_rank()
    hiteg__mrtg = get_host_ranks()
    apgn__fee = get_nodes_first_ranks()
    if tvq__fojnx in apgn__fee:
        try:
            cgvu__kullz = get_num_gpus(framework)
        except Exception as wvse__rpqr:
            cgvu__kullz = wvse__rpqr
        kbh__rsoq = create_subcomm_mpi4py(apgn__fee)
        dntly__ueonv = kbh__rsoq.gather(cgvu__kullz)
        if tvq__fojnx == 0:
            gpu_ranks = []
            cqpo__ghf = None
            for npma__ywi, tfwm__phrax in enumerate(hiteg__mrtg.values()):
                iwidk__ldwbf = dntly__ueonv[npma__ywi]
                if isinstance(iwidk__ldwbf, Exception):
                    cqpo__ghf = iwidk__ldwbf
                    break
                if iwidk__ldwbf == 0:
                    continue
                tsw__ipeu = len(tfwm__phrax) // iwidk__ldwbf
                for yqvd__qrx, fltwk__gjmh in enumerate(tfwm__phrax):
                    if yqvd__qrx % tsw__ipeu == 0:
                        bunth__ywpq = yqvd__qrx / tsw__ipeu
                        if bunth__ywpq < iwidk__ldwbf:
                            gpu_ranks.append(fltwk__gjmh)
            if cqpo__ghf:
                sjwbr__wmtzh.bcast(cqpo__ghf)
                raise cqpo__ghf
            else:
                sjwbr__wmtzh.bcast(gpu_ranks)
    if tvq__fojnx != 0:
        gpu_ranks = sjwbr__wmtzh.bcast(None)
        if isinstance(gpu_ranks, Exception):
            wvse__rpqr = gpu_ranks
            raise wvse__rpqr
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
    xjn__cnjd = MPI.COMM_WORLD.rank
    if len(gpu_ranks) > 0:
        kbh__rsoq = MPI.COMM_WORLD.Split(color=0 if xjn__cnjd in gpu_ranks else
            MPI.UNDEFINED, key=xjn__cnjd)
        if kbh__rsoq != MPI.COMM_NULL:
            hvd.init(comm=kbh__rsoq)
            if framework == 'torch':
                torch.cuda.set_device(hvd.local_rank())
            elif framework == 'tensorflow':
                naqu__edejd = tf.config.experimental.list_physical_devices(
                    'GPU')
                for zkydu__wbvj in naqu__edejd:
                    tf.config.experimental.set_memory_growth(zkydu__wbvj, True)
                tf.config.experimental.set_visible_devices(naqu__edejd[hvd.
                    local_rank()], 'GPU')
    else:
        if xjn__cnjd == 0:
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
        mlsx__aqdq = 17
        sjwbr__wmtzh = MPI.COMM_WORLD
        pcfgt__gip = MPI.Get_processor_name()
        fgnh__ncu = get_host_ranks()[pcfgt__gip]
        assert_dl_initialized()
        if bodo.get_rank() == fgnh__ncu[0]:
            assert bodo.get_rank() in dl_status.gpu_ranks
            for tvq__fojnx in fgnh__ncu[1:]:
                sjwbr__wmtzh.isend(1, dest=tvq__fojnx, tag=mlsx__aqdq)
        else:
            while True:
                mguf__jxtx = MPI.Status()
                hrz__xcm = sjwbr__wmtzh.Iprobe(MPI.ANY_SOURCE, MPI.ANY_TAG,
                    mguf__jxtx)
                if hrz__xcm:
                    assert mguf__jxtx.source == fgnh__ncu[0]
                    assert mguf__jxtx.tag == mlsx__aqdq
                    sjwbr__wmtzh.recv(source=0, tag=mlsx__aqdq)
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
