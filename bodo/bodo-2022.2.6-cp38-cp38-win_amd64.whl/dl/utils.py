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
    akbhw__ritfu = MPI.COMM_WORLD
    wgwm__ovwv = akbhw__ritfu.Get_rank()
    lvyv__cyis = get_host_ranks()
    lvkl__kqapk = get_nodes_first_ranks()
    if wgwm__ovwv in lvkl__kqapk:
        try:
            gqz__ktu = get_num_gpus(framework)
        except Exception as okol__suz:
            gqz__ktu = okol__suz
        nyp__ggwhn = create_subcomm_mpi4py(lvkl__kqapk)
        yiyr__hyke = nyp__ggwhn.gather(gqz__ktu)
        if wgwm__ovwv == 0:
            gpu_ranks = []
            chy__zaqxs = None
            for wyyfq__sqatx, rpys__aknv in enumerate(lvyv__cyis.values()):
                kajw__waci = yiyr__hyke[wyyfq__sqatx]
                if isinstance(kajw__waci, Exception):
                    chy__zaqxs = kajw__waci
                    break
                if kajw__waci == 0:
                    continue
                zwfbi__vpz = len(rpys__aknv) // kajw__waci
                for zkgek__kxf, kjdu__ckag in enumerate(rpys__aknv):
                    if zkgek__kxf % zwfbi__vpz == 0:
                        hawb__ccijq = zkgek__kxf / zwfbi__vpz
                        if hawb__ccijq < kajw__waci:
                            gpu_ranks.append(kjdu__ckag)
            if chy__zaqxs:
                akbhw__ritfu.bcast(chy__zaqxs)
                raise chy__zaqxs
            else:
                akbhw__ritfu.bcast(gpu_ranks)
    if wgwm__ovwv != 0:
        gpu_ranks = akbhw__ritfu.bcast(None)
        if isinstance(gpu_ranks, Exception):
            okol__suz = gpu_ranks
            raise okol__suz
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
    hbczv__kkqy = MPI.COMM_WORLD.rank
    if len(gpu_ranks) > 0:
        nyp__ggwhn = MPI.COMM_WORLD.Split(color=0 if hbczv__kkqy in
            gpu_ranks else MPI.UNDEFINED, key=hbczv__kkqy)
        if nyp__ggwhn != MPI.COMM_NULL:
            hvd.init(comm=nyp__ggwhn)
            if framework == 'torch':
                torch.cuda.set_device(hvd.local_rank())
            elif framework == 'tensorflow':
                zqa__had = tf.config.experimental.list_physical_devices('GPU')
                for pmpue__meso in zqa__had:
                    tf.config.experimental.set_memory_growth(pmpue__meso, True)
                tf.config.experimental.set_visible_devices(zqa__had[hvd.
                    local_rank()], 'GPU')
    else:
        if hbczv__kkqy == 0:
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
        yjng__njop = 17
        akbhw__ritfu = MPI.COMM_WORLD
        cfpu__ndctt = MPI.Get_processor_name()
        kdryc__tzk = get_host_ranks()[cfpu__ndctt]
        assert_dl_initialized()
        if bodo.get_rank() == kdryc__tzk[0]:
            assert bodo.get_rank() in dl_status.gpu_ranks
            for wgwm__ovwv in kdryc__tzk[1:]:
                akbhw__ritfu.isend(1, dest=wgwm__ovwv, tag=yjng__njop)
        else:
            while True:
                lszq__gneu = MPI.Status()
                kykc__fam = akbhw__ritfu.Iprobe(MPI.ANY_SOURCE, MPI.ANY_TAG,
                    lszq__gneu)
                if kykc__fam:
                    assert lszq__gneu.source == kdryc__tzk[0]
                    assert lszq__gneu.tag == yjng__njop
                    akbhw__ritfu.recv(source=0, tag=yjng__njop)
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
