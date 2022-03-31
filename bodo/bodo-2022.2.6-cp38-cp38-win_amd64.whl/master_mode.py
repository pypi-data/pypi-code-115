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
        tna__bieeb = state
        qgdhm__hgpth = inspect.getsourcelines(tna__bieeb)[0][0]
        assert qgdhm__hgpth.startswith('@bodo.jit') or qgdhm__hgpth.startswith(
            '@jit')
        gfagx__grw = eval(qgdhm__hgpth[1:])
        self.dispatcher = gfagx__grw(tna__bieeb)


def worker_loop():
    assert bodo.get_rank() != MASTER_RANK
    nvx__mhi = MPI.COMM_WORLD
    while True:
        szt__zzdzr = nvx__mhi.bcast(None, root=MASTER_RANK)
        if szt__zzdzr[0] == 'exec':
            tna__bieeb = pickle.loads(szt__zzdzr[1])
            for mgpw__erlnf, edad__erorf in list(tna__bieeb.__globals__.items()
                ):
                if isinstance(edad__erorf, MasterModeDispatcher):
                    tna__bieeb.__globals__[mgpw__erlnf
                        ] = edad__erorf.dispatcher
            if tna__bieeb.__module__ not in sys.modules:
                sys.modules[tna__bieeb.__module__] = pytypes.ModuleType(
                    tna__bieeb.__module__)
            qgdhm__hgpth = inspect.getsourcelines(tna__bieeb)[0][0]
            assert qgdhm__hgpth.startswith('@bodo.jit'
                ) or qgdhm__hgpth.startswith('@jit')
            gfagx__grw = eval(qgdhm__hgpth[1:])
            func = gfagx__grw(tna__bieeb)
            brbw__vwf = szt__zzdzr[2]
            zxonl__zghtv = szt__zzdzr[3]
            gis__jnuo = []
            for fgxvx__ffbj in brbw__vwf:
                if fgxvx__ffbj == 'scatter':
                    gis__jnuo.append(bodo.scatterv(None))
                elif fgxvx__ffbj == 'bcast':
                    gis__jnuo.append(nvx__mhi.bcast(None, root=MASTER_RANK))
            xic__fqdr = {}
            for argname, fgxvx__ffbj in zxonl__zghtv.items():
                if fgxvx__ffbj == 'scatter':
                    xic__fqdr[argname] = bodo.scatterv(None)
                elif fgxvx__ffbj == 'bcast':
                    xic__fqdr[argname] = nvx__mhi.bcast(None, root=MASTER_RANK)
            xpqd__gsf = func(*gis__jnuo, **xic__fqdr)
            if xpqd__gsf is not None and func.overloads[func.signatures[0]
                ].metadata['is_return_distributed']:
                bodo.gatherv(xpqd__gsf)
            del (szt__zzdzr, tna__bieeb, func, gfagx__grw, brbw__vwf,
                zxonl__zghtv, gis__jnuo, xic__fqdr, xpqd__gsf)
            gc.collect()
        elif szt__zzdzr[0] == 'exit':
            exit()
    assert False


def master_wrapper(func, *args, **kwargs):
    nvx__mhi = MPI.COMM_WORLD
    if {'all_args_distributed', 'all_args_distributed_block',
        'all_args_distributed_varlength'} & set(func.targetoptions.keys()):
        brbw__vwf = ['scatter' for grkt__vhz in range(len(args))]
        zxonl__zghtv = {argname: 'scatter' for argname in kwargs.keys()}
    else:
        zohcr__xsd = func.py_func.__code__.co_varnames
        fji__ixvt = func.targetoptions

        def get_distribution(argname):
            if argname in fji__ixvt.get('distributed', []
                ) or argname in fji__ixvt.get('distributed_block', []):
                return 'scatter'
            else:
                return 'bcast'
        brbw__vwf = [get_distribution(argname) for argname in zohcr__xsd[:
            len(args)]]
        zxonl__zghtv = {argname: get_distribution(argname) for argname in
            kwargs.keys()}
    rysa__sxxv = pickle.dumps(func.py_func)
    nvx__mhi.bcast(['exec', rysa__sxxv, brbw__vwf, zxonl__zghtv])
    gis__jnuo = []
    for rjvv__qmaag, fgxvx__ffbj in zip(args, brbw__vwf):
        if fgxvx__ffbj == 'scatter':
            gis__jnuo.append(bodo.scatterv(rjvv__qmaag))
        elif fgxvx__ffbj == 'bcast':
            nvx__mhi.bcast(rjvv__qmaag)
            gis__jnuo.append(rjvv__qmaag)
    xic__fqdr = {}
    for argname, rjvv__qmaag in kwargs.items():
        fgxvx__ffbj = zxonl__zghtv[argname]
        if fgxvx__ffbj == 'scatter':
            xic__fqdr[argname] = bodo.scatterv(rjvv__qmaag)
        elif fgxvx__ffbj == 'bcast':
            nvx__mhi.bcast(rjvv__qmaag)
            xic__fqdr[argname] = rjvv__qmaag
    elyoz__pgvjs = []
    for mgpw__erlnf, edad__erorf in list(func.py_func.__globals__.items()):
        if isinstance(edad__erorf, MasterModeDispatcher):
            elyoz__pgvjs.append((func.py_func.__globals__, mgpw__erlnf,
                func.py_func.__globals__[mgpw__erlnf]))
            func.py_func.__globals__[mgpw__erlnf] = edad__erorf.dispatcher
    xpqd__gsf = func(*gis__jnuo, **xic__fqdr)
    for cziu__aug, mgpw__erlnf, edad__erorf in elyoz__pgvjs:
        cziu__aug[mgpw__erlnf] = edad__erorf
    if xpqd__gsf is not None and func.overloads[func.signatures[0]].metadata[
        'is_return_distributed']:
        xpqd__gsf = bodo.gatherv(xpqd__gsf)
    return xpqd__gsf


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
