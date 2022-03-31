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
        whohj__qwl = state
        ivc__iyipm = inspect.getsourcelines(whohj__qwl)[0][0]
        assert ivc__iyipm.startswith('@bodo.jit') or ivc__iyipm.startswith(
            '@jit')
        arq__smz = eval(ivc__iyipm[1:])
        self.dispatcher = arq__smz(whohj__qwl)


def worker_loop():
    assert bodo.get_rank() != MASTER_RANK
    hcvk__epo = MPI.COMM_WORLD
    while True:
        djero__hehjy = hcvk__epo.bcast(None, root=MASTER_RANK)
        if djero__hehjy[0] == 'exec':
            whohj__qwl = pickle.loads(djero__hehjy[1])
            for zwrm__qezrb, big__gvv in list(whohj__qwl.__globals__.items()):
                if isinstance(big__gvv, MasterModeDispatcher):
                    whohj__qwl.__globals__[zwrm__qezrb] = big__gvv.dispatcher
            if whohj__qwl.__module__ not in sys.modules:
                sys.modules[whohj__qwl.__module__] = pytypes.ModuleType(
                    whohj__qwl.__module__)
            ivc__iyipm = inspect.getsourcelines(whohj__qwl)[0][0]
            assert ivc__iyipm.startswith('@bodo.jit') or ivc__iyipm.startswith(
                '@jit')
            arq__smz = eval(ivc__iyipm[1:])
            func = arq__smz(whohj__qwl)
            uiig__zlpbw = djero__hehjy[2]
            vha__nctv = djero__hehjy[3]
            cab__zsjgm = []
            for ehdh__hid in uiig__zlpbw:
                if ehdh__hid == 'scatter':
                    cab__zsjgm.append(bodo.scatterv(None))
                elif ehdh__hid == 'bcast':
                    cab__zsjgm.append(hcvk__epo.bcast(None, root=MASTER_RANK))
            jwf__beirj = {}
            for argname, ehdh__hid in vha__nctv.items():
                if ehdh__hid == 'scatter':
                    jwf__beirj[argname] = bodo.scatterv(None)
                elif ehdh__hid == 'bcast':
                    jwf__beirj[argname] = hcvk__epo.bcast(None, root=
                        MASTER_RANK)
            utkg__tppc = func(*cab__zsjgm, **jwf__beirj)
            if utkg__tppc is not None and func.overloads[func.signatures[0]
                ].metadata['is_return_distributed']:
                bodo.gatherv(utkg__tppc)
            del (djero__hehjy, whohj__qwl, func, arq__smz, uiig__zlpbw,
                vha__nctv, cab__zsjgm, jwf__beirj, utkg__tppc)
            gc.collect()
        elif djero__hehjy[0] == 'exit':
            exit()
    assert False


def master_wrapper(func, *args, **kwargs):
    hcvk__epo = MPI.COMM_WORLD
    if {'all_args_distributed', 'all_args_distributed_block',
        'all_args_distributed_varlength'} & set(func.targetoptions.keys()):
        uiig__zlpbw = ['scatter' for siid__pvug in range(len(args))]
        vha__nctv = {argname: 'scatter' for argname in kwargs.keys()}
    else:
        fdp__qdew = func.py_func.__code__.co_varnames
        jslgu__wtve = func.targetoptions

        def get_distribution(argname):
            if argname in jslgu__wtve.get('distributed', []
                ) or argname in jslgu__wtve.get('distributed_block', []):
                return 'scatter'
            else:
                return 'bcast'
        uiig__zlpbw = [get_distribution(argname) for argname in fdp__qdew[:
            len(args)]]
        vha__nctv = {argname: get_distribution(argname) for argname in
            kwargs.keys()}
    dynpm__fub = pickle.dumps(func.py_func)
    hcvk__epo.bcast(['exec', dynpm__fub, uiig__zlpbw, vha__nctv])
    cab__zsjgm = []
    for xol__igav, ehdh__hid in zip(args, uiig__zlpbw):
        if ehdh__hid == 'scatter':
            cab__zsjgm.append(bodo.scatterv(xol__igav))
        elif ehdh__hid == 'bcast':
            hcvk__epo.bcast(xol__igav)
            cab__zsjgm.append(xol__igav)
    jwf__beirj = {}
    for argname, xol__igav in kwargs.items():
        ehdh__hid = vha__nctv[argname]
        if ehdh__hid == 'scatter':
            jwf__beirj[argname] = bodo.scatterv(xol__igav)
        elif ehdh__hid == 'bcast':
            hcvk__epo.bcast(xol__igav)
            jwf__beirj[argname] = xol__igav
    cbm__zgzr = []
    for zwrm__qezrb, big__gvv in list(func.py_func.__globals__.items()):
        if isinstance(big__gvv, MasterModeDispatcher):
            cbm__zgzr.append((func.py_func.__globals__, zwrm__qezrb, func.
                py_func.__globals__[zwrm__qezrb]))
            func.py_func.__globals__[zwrm__qezrb] = big__gvv.dispatcher
    utkg__tppc = func(*cab__zsjgm, **jwf__beirj)
    for qnzx__vkfx, zwrm__qezrb, big__gvv in cbm__zgzr:
        qnzx__vkfx[zwrm__qezrb] = big__gvv
    if utkg__tppc is not None and func.overloads[func.signatures[0]].metadata[
        'is_return_distributed']:
        utkg__tppc = bodo.gatherv(utkg__tppc)
    return utkg__tppc


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
