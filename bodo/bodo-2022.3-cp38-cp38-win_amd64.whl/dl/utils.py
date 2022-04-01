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
    hmk__ptaed = MPI.COMM_WORLD
    tuefr__twwo = hmk__ptaed.Get_rank()
    plah__kcbvr = get_host_ranks()
    wpmrc__nxfxb = get_nodes_first_ranks()
    if tuefr__twwo in wpmrc__nxfxb:
        try:
            ttcr__uijs = get_num_gpus(framework)
        except Exception as lxwj__mni:
            ttcr__uijs = lxwj__mni
        mqyg__qbmy = create_subcomm_mpi4py(wpmrc__nxfxb)
        ndi__cvqyz = mqyg__qbmy.gather(ttcr__uijs)
        if tuefr__twwo == 0:
            gpu_ranks = []
            exey__waha = None
            for gxzbm__tbyz, skjar__jvma in enumerate(plah__kcbvr.values()):
                gdsfw__bsrqd = ndi__cvqyz[gxzbm__tbyz]
                if isinstance(gdsfw__bsrqd, Exception):
                    exey__waha = gdsfw__bsrqd
                    break
                if gdsfw__bsrqd == 0:
                    continue
                bhv__pdo = len(skjar__jvma) // gdsfw__bsrqd
                for azi__yksb, dfjd__aco in enumerate(skjar__jvma):
                    if azi__yksb % bhv__pdo == 0:
                        cvj__sfsgj = azi__yksb / bhv__pdo
                        if cvj__sfsgj < gdsfw__bsrqd:
                            gpu_ranks.append(dfjd__aco)
            if exey__waha:
                hmk__ptaed.bcast(exey__waha)
                raise exey__waha
            else:
                hmk__ptaed.bcast(gpu_ranks)
    if tuefr__twwo != 0:
        gpu_ranks = hmk__ptaed.bcast(None)
        if isinstance(gpu_ranks, Exception):
            lxwj__mni = gpu_ranks
            raise lxwj__mni
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
    czc__eufhm = MPI.COMM_WORLD.rank
    if len(gpu_ranks) > 0:
        mqyg__qbmy = MPI.COMM_WORLD.Split(color=0 if czc__eufhm in
            gpu_ranks else MPI.UNDEFINED, key=czc__eufhm)
        if mqyg__qbmy != MPI.COMM_NULL:
            hvd.init(comm=mqyg__qbmy)
            if framework == 'torch':
                torch.cuda.set_device(hvd.local_rank())
            elif framework == 'tensorflow':
                ximpe__snhy = tf.config.experimental.list_physical_devices(
                    'GPU')
                for jjikm__pssvy in ximpe__snhy:
                    tf.config.experimental.set_memory_growth(jjikm__pssvy, True
                        )
                tf.config.experimental.set_visible_devices(ximpe__snhy[hvd.
                    local_rank()], 'GPU')
    else:
        if czc__eufhm == 0:
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
        zpnm__ipyu = 17
        hmk__ptaed = MPI.COMM_WORLD
        fzz__mmlz = MPI.Get_processor_name()
        xqvwp__ijlry = get_host_ranks()[fzz__mmlz]
        assert_dl_initialized()
        if bodo.get_rank() == xqvwp__ijlry[0]:
            assert bodo.get_rank() in dl_status.gpu_ranks
            for tuefr__twwo in xqvwp__ijlry[1:]:
                hmk__ptaed.isend(1, dest=tuefr__twwo, tag=zpnm__ipyu)
        else:
            while True:
                fasa__rgmx = MPI.Status()
                tipt__aqcj = hmk__ptaed.Iprobe(MPI.ANY_SOURCE, MPI.ANY_TAG,
                    fasa__rgmx)
                if tipt__aqcj:
                    assert fasa__rgmx.source == xqvwp__ijlry[0]
                    assert fasa__rgmx.tag == zpnm__ipyu
                    hmk__ptaed.recv(source=0, tag=zpnm__ipyu)
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
