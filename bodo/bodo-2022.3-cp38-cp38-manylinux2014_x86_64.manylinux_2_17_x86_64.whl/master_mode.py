import gc
import inspect
import sys
import types as pytypes
import bodo
master_mode_on = False
MASTER_RANK = 0


class MasterModeDispatcher(object):

    def __init__(self, dispatcher):
        self.dispatcher = dispatcher

    def __call__(self, *args, **kwargs):
        assert bodo.get_rank() == MASTER_RANK
        return master_wrapper(self.dispatcher, *args, **kwargs)

    def __getstate__(self):
        assert bodo.get_rank() == MASTER_RANK
        return self.dispatcher.py_func

    def __setstate__(self, state):
        assert bodo.get_rank() != MASTER_RANK
        fqca__bgolx = state
        kcx__ckcxl = inspect.getsourcelines(fqca__bgolx)[0][0]
        assert kcx__ckcxl.startswith('@bodo.jit') or kcx__ckcxl.startswith(
            '@jit')
        dgic__kfzwy = eval(kcx__ckcxl[1:])
        self.dispatcher = dgic__kfzwy(fqca__bgolx)


def worker_loop():
    assert bodo.get_rank() != MASTER_RANK
    pxagy__xlq = MPI.COMM_WORLD
    while True:
        vxn__mytth = pxagy__xlq.bcast(None, root=MASTER_RANK)
        if vxn__mytth[0] == 'exec':
            fqca__bgolx = pickle.loads(vxn__mytth[1])
            for mes__gra, evo__gqha in list(fqca__bgolx.__globals__.items()):
                if isinstance(evo__gqha, MasterModeDispatcher):
                    fqca__bgolx.__globals__[mes__gra] = evo__gqha.dispatcher
            if fqca__bgolx.__module__ not in sys.modules:
                sys.modules[fqca__bgolx.__module__] = pytypes.ModuleType(
                    fqca__bgolx.__module__)
            kcx__ckcxl = inspect.getsourcelines(fqca__bgolx)[0][0]
            assert kcx__ckcxl.startswith('@bodo.jit') or kcx__ckcxl.startswith(
                '@jit')
            dgic__kfzwy = eval(kcx__ckcxl[1:])
            func = dgic__kfzwy(fqca__bgolx)
            nbfqg__ugeve = vxn__mytth[2]
            iin__nyrm = vxn__mytth[3]
            ykhv__mpu = []
            for wenq__imopx in nbfqg__ugeve:
                if wenq__imopx == 'scatter':
                    ykhv__mpu.append(bodo.scatterv(None))
                elif wenq__imopx == 'bcast':
                    ykhv__mpu.append(pxagy__xlq.bcast(None, root=MASTER_RANK))
            kam__cztr = {}
            for argname, wenq__imopx in iin__nyrm.items():
                if wenq__imopx == 'scatter':
                    kam__cztr[argname] = bodo.scatterv(None)
                elif wenq__imopx == 'bcast':
                    kam__cztr[argname] = pxagy__xlq.bcast(None, root=
                        MASTER_RANK)
            vek__bsoe = func(*ykhv__mpu, **kam__cztr)
            if vek__bsoe is not None and func.overloads[func.signatures[0]
                ].metadata['is_return_distributed']:
                bodo.gatherv(vek__bsoe)
            del (vxn__mytth, fqca__bgolx, func, dgic__kfzwy, nbfqg__ugeve,
                iin__nyrm, ykhv__mpu, kam__cztr, vek__bsoe)
            gc.collect()
        elif vxn__mytth[0] == 'exit':
            exit()
    assert False


def master_wrapper(func, *args, **kwargs):
    pxagy__xlq = MPI.COMM_WORLD
    if {'all_args_distributed', 'all_args_distributed_block',
        'all_args_distributed_varlength'} & set(func.targetoptions.keys()):
        nbfqg__ugeve = ['scatter' for ond__tloqr in range(len(args))]
        iin__nyrm = {argname: 'scatter' for argname in kwargs.keys()}
    else:
        uxg__lcbas = func.py_func.__code__.co_varnames
        zez__ayz = func.targetoptions

        def get_distribution(argname):
            if argname in zez__ayz.get('distributed', []
                ) or argname in zez__ayz.get('distributed_block', []):
                return 'scatter'
            else:
                return 'bcast'
        nbfqg__ugeve = [get_distribution(argname) for argname in uxg__lcbas
            [:len(args)]]
        iin__nyrm = {argname: get_distribution(argname) for argname in
            kwargs.keys()}
    kmc__oikj = pickle.dumps(func.py_func)
    pxagy__xlq.bcast(['exec', kmc__oikj, nbfqg__ugeve, iin__nyrm])
    ykhv__mpu = []
    for dnyvn__umt, wenq__imopx in zip(args, nbfqg__ugeve):
        if wenq__imopx == 'scatter':
            ykhv__mpu.append(bodo.scatterv(dnyvn__umt))
        elif wenq__imopx == 'bcast':
            pxagy__xlq.bcast(dnyvn__umt)
            ykhv__mpu.append(dnyvn__umt)
    kam__cztr = {}
    for argname, dnyvn__umt in kwargs.items():
        wenq__imopx = iin__nyrm[argname]
        if wenq__imopx == 'scatter':
            kam__cztr[argname] = bodo.scatterv(dnyvn__umt)
        elif wenq__imopx == 'bcast':
            pxagy__xlq.bcast(dnyvn__umt)
            kam__cztr[argname] = dnyvn__umt
    vuucc__ilusw = []
    for mes__gra, evo__gqha in list(func.py_func.__globals__.items()):
        if isinstance(evo__gqha, MasterModeDispatcher):
            vuucc__ilusw.append((func.py_func.__globals__, mes__gra, func.
                py_func.__globals__[mes__gra]))
            func.py_func.__globals__[mes__gra] = evo__gqha.dispatcher
    vek__bsoe = func(*ykhv__mpu, **kam__cztr)
    for pih__rtku, mes__gra, evo__gqha in vuucc__ilusw:
        pih__rtku[mes__gra] = evo__gqha
    if vek__bsoe is not None and func.overloads[func.signatures[0]].metadata[
        'is_return_distributed']:
        vek__bsoe = bodo.gatherv(vek__bsoe)
    return vek__bsoe


def init_master_mode():
    if bodo.get_size() == 1:
        return
    global master_mode_on
    assert master_mode_on is False, 'init_master_mode can only be called once on each process'
    master_mode_on = True
    assert sys.version_info[:2] >= (3, 8
        ), 'Python 3.8+ required for master mode'
    from bodo import jit
    globals()['jit'] = jit
    import cloudpickle
    from mpi4py import MPI
    globals()['pickle'] = cloudpickle
    globals()['MPI'] = MPI

    def master_exit():
        MPI.COMM_WORLD.bcast(['exit'])
    if bodo.get_rank() == MASTER_RANK:
        import atexit
        atexit.register(master_exit)
    else:
        worker_loop()
