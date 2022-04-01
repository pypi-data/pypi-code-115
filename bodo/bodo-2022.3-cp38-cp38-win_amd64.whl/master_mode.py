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
        xzcss__xpvf = state
        hpwm__pljp = inspect.getsourcelines(xzcss__xpvf)[0][0]
        assert hpwm__pljp.startswith('@bodo.jit') or hpwm__pljp.startswith(
            '@jit')
        pht__tdjp = eval(hpwm__pljp[1:])
        self.dispatcher = pht__tdjp(xzcss__xpvf)


def worker_loop():
    assert bodo.get_rank() != MASTER_RANK
    dhm__qir = MPI.COMM_WORLD
    while True:
        wzmd__difi = dhm__qir.bcast(None, root=MASTER_RANK)
        if wzmd__difi[0] == 'exec':
            xzcss__xpvf = pickle.loads(wzmd__difi[1])
            for kgbl__eedm, ubvpt__ovq in list(xzcss__xpvf.__globals__.items()
                ):
                if isinstance(ubvpt__ovq, MasterModeDispatcher):
                    xzcss__xpvf.__globals__[kgbl__eedm] = ubvpt__ovq.dispatcher
            if xzcss__xpvf.__module__ not in sys.modules:
                sys.modules[xzcss__xpvf.__module__] = pytypes.ModuleType(
                    xzcss__xpvf.__module__)
            hpwm__pljp = inspect.getsourcelines(xzcss__xpvf)[0][0]
            assert hpwm__pljp.startswith('@bodo.jit') or hpwm__pljp.startswith(
                '@jit')
            pht__tdjp = eval(hpwm__pljp[1:])
            func = pht__tdjp(xzcss__xpvf)
            lwe__ktyvx = wzmd__difi[2]
            nossf__utitj = wzmd__difi[3]
            azs__cegez = []
            for avn__syzb in lwe__ktyvx:
                if avn__syzb == 'scatter':
                    azs__cegez.append(bodo.scatterv(None))
                elif avn__syzb == 'bcast':
                    azs__cegez.append(dhm__qir.bcast(None, root=MASTER_RANK))
            uhk__tun = {}
            for argname, avn__syzb in nossf__utitj.items():
                if avn__syzb == 'scatter':
                    uhk__tun[argname] = bodo.scatterv(None)
                elif avn__syzb == 'bcast':
                    uhk__tun[argname] = dhm__qir.bcast(None, root=MASTER_RANK)
            eepau__qfmmj = func(*azs__cegez, **uhk__tun)
            if eepau__qfmmj is not None and func.overloads[func.signatures[0]
                ].metadata['is_return_distributed']:
                bodo.gatherv(eepau__qfmmj)
            del (wzmd__difi, xzcss__xpvf, func, pht__tdjp, lwe__ktyvx,
                nossf__utitj, azs__cegez, uhk__tun, eepau__qfmmj)
            gc.collect()
        elif wzmd__difi[0] == 'exit':
            exit()
    assert False


def master_wrapper(func, *args, **kwargs):
    dhm__qir = MPI.COMM_WORLD
    if {'all_args_distributed', 'all_args_distributed_block',
        'all_args_distributed_varlength'} & set(func.targetoptions.keys()):
        lwe__ktyvx = ['scatter' for tgl__brv in range(len(args))]
        nossf__utitj = {argname: 'scatter' for argname in kwargs.keys()}
    else:
        xkgm__evs = func.py_func.__code__.co_varnames
        wjml__vsw = func.targetoptions

        def get_distribution(argname):
            if argname in wjml__vsw.get('distributed', []
                ) or argname in wjml__vsw.get('distributed_block', []):
                return 'scatter'
            else:
                return 'bcast'
        lwe__ktyvx = [get_distribution(argname) for argname in xkgm__evs[:
            len(args)]]
        nossf__utitj = {argname: get_distribution(argname) for argname in
            kwargs.keys()}
    ckws__cwz = pickle.dumps(func.py_func)
    dhm__qir.bcast(['exec', ckws__cwz, lwe__ktyvx, nossf__utitj])
    azs__cegez = []
    for jqg__bftsl, avn__syzb in zip(args, lwe__ktyvx):
        if avn__syzb == 'scatter':
            azs__cegez.append(bodo.scatterv(jqg__bftsl))
        elif avn__syzb == 'bcast':
            dhm__qir.bcast(jqg__bftsl)
            azs__cegez.append(jqg__bftsl)
    uhk__tun = {}
    for argname, jqg__bftsl in kwargs.items():
        avn__syzb = nossf__utitj[argname]
        if avn__syzb == 'scatter':
            uhk__tun[argname] = bodo.scatterv(jqg__bftsl)
        elif avn__syzb == 'bcast':
            dhm__qir.bcast(jqg__bftsl)
            uhk__tun[argname] = jqg__bftsl
    qtdko__fakfu = []
    for kgbl__eedm, ubvpt__ovq in list(func.py_func.__globals__.items()):
        if isinstance(ubvpt__ovq, MasterModeDispatcher):
            qtdko__fakfu.append((func.py_func.__globals__, kgbl__eedm, func
                .py_func.__globals__[kgbl__eedm]))
            func.py_func.__globals__[kgbl__eedm] = ubvpt__ovq.dispatcher
    eepau__qfmmj = func(*azs__cegez, **uhk__tun)
    for qydru__hck, kgbl__eedm, ubvpt__ovq in qtdko__fakfu:
        qydru__hck[kgbl__eedm] = ubvpt__ovq
    if eepau__qfmmj is not None and func.overloads[func.signatures[0]
        ].metadata['is_return_distributed']:
        eepau__qfmmj = bodo.gatherv(eepau__qfmmj)
    return eepau__qfmmj


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
