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
        azpsu__abm = state
        qihdt__nxyks = inspect.getsourcelines(azpsu__abm)[0][0]
        assert qihdt__nxyks.startswith('@bodo.jit') or qihdt__nxyks.startswith(
            '@jit')
        gvj__xep = eval(qihdt__nxyks[1:])
        self.dispatcher = gvj__xep(azpsu__abm)


def worker_loop():
    assert bodo.get_rank() != MASTER_RANK
    gsgcg__jyvuv = MPI.COMM_WORLD
    while True:
        myfnk__htpve = gsgcg__jyvuv.bcast(None, root=MASTER_RANK)
        if myfnk__htpve[0] == 'exec':
            azpsu__abm = pickle.loads(myfnk__htpve[1])
            for gdfo__sae, ydd__wrtu in list(azpsu__abm.__globals__.items()):
                if isinstance(ydd__wrtu, MasterModeDispatcher):
                    azpsu__abm.__globals__[gdfo__sae] = ydd__wrtu.dispatcher
            if azpsu__abm.__module__ not in sys.modules:
                sys.modules[azpsu__abm.__module__] = pytypes.ModuleType(
                    azpsu__abm.__module__)
            qihdt__nxyks = inspect.getsourcelines(azpsu__abm)[0][0]
            assert qihdt__nxyks.startswith('@bodo.jit'
                ) or qihdt__nxyks.startswith('@jit')
            gvj__xep = eval(qihdt__nxyks[1:])
            func = gvj__xep(azpsu__abm)
            wpcai__xwmwi = myfnk__htpve[2]
            ixrg__ddsfy = myfnk__htpve[3]
            tnjk__fjpzl = []
            for yun__cqpf in wpcai__xwmwi:
                if yun__cqpf == 'scatter':
                    tnjk__fjpzl.append(bodo.scatterv(None))
                elif yun__cqpf == 'bcast':
                    tnjk__fjpzl.append(gsgcg__jyvuv.bcast(None, root=
                        MASTER_RANK))
            gexmn__dubeh = {}
            for argname, yun__cqpf in ixrg__ddsfy.items():
                if yun__cqpf == 'scatter':
                    gexmn__dubeh[argname] = bodo.scatterv(None)
                elif yun__cqpf == 'bcast':
                    gexmn__dubeh[argname] = gsgcg__jyvuv.bcast(None, root=
                        MASTER_RANK)
            tvqt__esm = func(*tnjk__fjpzl, **gexmn__dubeh)
            if tvqt__esm is not None and func.overloads[func.signatures[0]
                ].metadata['is_return_distributed']:
                bodo.gatherv(tvqt__esm)
            del (myfnk__htpve, azpsu__abm, func, gvj__xep, wpcai__xwmwi,
                ixrg__ddsfy, tnjk__fjpzl, gexmn__dubeh, tvqt__esm)
            gc.collect()
        elif myfnk__htpve[0] == 'exit':
            exit()
    assert False


def master_wrapper(func, *args, **kwargs):
    gsgcg__jyvuv = MPI.COMM_WORLD
    if {'all_args_distributed', 'all_args_distributed_block',
        'all_args_distributed_varlength'} & set(func.targetoptions.keys()):
        wpcai__xwmwi = ['scatter' for jaofw__gzuj in range(len(args))]
        ixrg__ddsfy = {argname: 'scatter' for argname in kwargs.keys()}
    else:
        dtirj__ctutk = func.py_func.__code__.co_varnames
        zmww__hgqa = func.targetoptions

        def get_distribution(argname):
            if argname in zmww__hgqa.get('distributed', []
                ) or argname in zmww__hgqa.get('distributed_block', []):
                return 'scatter'
            else:
                return 'bcast'
        wpcai__xwmwi = [get_distribution(argname) for argname in
            dtirj__ctutk[:len(args)]]
        ixrg__ddsfy = {argname: get_distribution(argname) for argname in
            kwargs.keys()}
    bfwe__yuoan = pickle.dumps(func.py_func)
    gsgcg__jyvuv.bcast(['exec', bfwe__yuoan, wpcai__xwmwi, ixrg__ddsfy])
    tnjk__fjpzl = []
    for vro__crrw, yun__cqpf in zip(args, wpcai__xwmwi):
        if yun__cqpf == 'scatter':
            tnjk__fjpzl.append(bodo.scatterv(vro__crrw))
        elif yun__cqpf == 'bcast':
            gsgcg__jyvuv.bcast(vro__crrw)
            tnjk__fjpzl.append(vro__crrw)
    gexmn__dubeh = {}
    for argname, vro__crrw in kwargs.items():
        yun__cqpf = ixrg__ddsfy[argname]
        if yun__cqpf == 'scatter':
            gexmn__dubeh[argname] = bodo.scatterv(vro__crrw)
        elif yun__cqpf == 'bcast':
            gsgcg__jyvuv.bcast(vro__crrw)
            gexmn__dubeh[argname] = vro__crrw
    gqs__nmt = []
    for gdfo__sae, ydd__wrtu in list(func.py_func.__globals__.items()):
        if isinstance(ydd__wrtu, MasterModeDispatcher):
            gqs__nmt.append((func.py_func.__globals__, gdfo__sae, func.
                py_func.__globals__[gdfo__sae]))
            func.py_func.__globals__[gdfo__sae] = ydd__wrtu.dispatcher
    tvqt__esm = func(*tnjk__fjpzl, **gexmn__dubeh)
    for foqj__ldjju, gdfo__sae, ydd__wrtu in gqs__nmt:
        foqj__ldjju[gdfo__sae] = ydd__wrtu
    if tvqt__esm is not None and func.overloads[func.signatures[0]].metadata[
        'is_return_distributed']:
        tvqt__esm = bodo.gatherv(tvqt__esm)
    return tvqt__esm


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
