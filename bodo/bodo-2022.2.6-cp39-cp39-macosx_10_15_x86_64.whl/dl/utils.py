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
    yko__nrulq = MPI.COMM_WORLD
    awrw__hjy = yko__nrulq.Get_rank()
    pezu__azvd = get_host_ranks()
    vzk__dpv = get_nodes_first_ranks()
    if awrw__hjy in vzk__dpv:
        try:
            ldde__orlts = get_num_gpus(framework)
        except Exception as syov__bkc:
            ldde__orlts = syov__bkc
        snnzb__hvyu = create_subcomm_mpi4py(vzk__dpv)
        ipj__nnya = snnzb__hvyu.gather(ldde__orlts)
        if awrw__hjy == 0:
            gpu_ranks = []
            nrzy__prt = None
            for pbbh__isrk, hvot__nxt in enumerate(pezu__azvd.values()):
                qgu__pavj = ipj__nnya[pbbh__isrk]
                if isinstance(qgu__pavj, Exception):
                    nrzy__prt = qgu__pavj
                    break
                if qgu__pavj == 0:
                    continue
                fybr__xbir = len(hvot__nxt) // qgu__pavj
                for nzbf__dvts, cagmm__behv in enumerate(hvot__nxt):
                    if nzbf__dvts % fybr__xbir == 0:
                        wyc__gnmbb = nzbf__dvts / fybr__xbir
                        if wyc__gnmbb < qgu__pavj:
                            gpu_ranks.append(cagmm__behv)
            if nrzy__prt:
                yko__nrulq.bcast(nrzy__prt)
                raise nrzy__prt
            else:
                yko__nrulq.bcast(gpu_ranks)
    if awrw__hjy != 0:
        gpu_ranks = yko__nrulq.bcast(None)
        if isinstance(gpu_ranks, Exception):
            syov__bkc = gpu_ranks
            raise syov__bkc
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
    nfw__ewbk = MPI.COMM_WORLD.rank
    if len(gpu_ranks) > 0:
        snnzb__hvyu = MPI.COMM_WORLD.Split(color=0 if nfw__ewbk in
            gpu_ranks else MPI.UNDEFINED, key=nfw__ewbk)
        if snnzb__hvyu != MPI.COMM_NULL:
            hvd.init(comm=snnzb__hvyu)
            if framework == 'torch':
                torch.cuda.set_device(hvd.local_rank())
            elif framework == 'tensorflow':
                ejb__kllpc = tf.config.experimental.list_physical_devices('GPU'
                    )
                for prqe__hmow in ejb__kllpc:
                    tf.config.experimental.set_memory_growth(prqe__hmow, True)
                tf.config.experimental.set_visible_devices(ejb__kllpc[hvd.
                    local_rank()], 'GPU')
    else:
        if nfw__ewbk == 0:
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
        jhs__itrk = 17
        yko__nrulq = MPI.COMM_WORLD
        gkwtd__sydhu = MPI.Get_processor_name()
        kao__pang = get_host_ranks()[gkwtd__sydhu]
        assert_dl_initialized()
        if bodo.get_rank() == kao__pang[0]:
            assert bodo.get_rank() in dl_status.gpu_ranks
            for awrw__hjy in kao__pang[1:]:
                yko__nrulq.isend(1, dest=awrw__hjy, tag=jhs__itrk)
        else:
            while True:
                atnct__npdj = MPI.Status()
                eecja__vrbr = yko__nrulq.Iprobe(MPI.ANY_SOURCE, MPI.ANY_TAG,
                    atnct__npdj)
                if eecja__vrbr:
                    assert atnct__npdj.source == kao__pang[0]
                    assert atnct__npdj.tag == jhs__itrk
                    yko__nrulq.recv(source=0, tag=jhs__itrk)
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
