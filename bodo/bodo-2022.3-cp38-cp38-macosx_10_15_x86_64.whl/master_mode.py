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
        ckvvd__ygd = state
        fcan__seqm = inspect.getsourcelines(ckvvd__ygd)[0][0]
        assert fcan__seqm.startswith('@bodo.jit') or fcan__seqm.startswith(
            '@jit')
        wvfh__ymk = eval(fcan__seqm[1:])
        self.dispatcher = wvfh__ymk(ckvvd__ygd)


def worker_loop():
    assert bodo.get_rank() != MASTER_RANK
    prt__yhu = MPI.COMM_WORLD
    while True:
        cbmof__ulpe = prt__yhu.bcast(None, root=MASTER_RANK)
        if cbmof__ulpe[0] == 'exec':
            ckvvd__ygd = pickle.loads(cbmof__ulpe[1])
            for zegfn__cjca, rjp__zpr in list(ckvvd__ygd.__globals__.items()):
                if isinstance(rjp__zpr, MasterModeDispatcher):
                    ckvvd__ygd.__globals__[zegfn__cjca] = rjp__zpr.dispatcher
            if ckvvd__ygd.__module__ not in sys.modules:
                sys.modules[ckvvd__ygd.__module__] = pytypes.ModuleType(
                    ckvvd__ygd.__module__)
            fcan__seqm = inspect.getsourcelines(ckvvd__ygd)[0][0]
            assert fcan__seqm.startswith('@bodo.jit') or fcan__seqm.startswith(
                '@jit')
            wvfh__ymk = eval(fcan__seqm[1:])
            func = wvfh__ymk(ckvvd__ygd)
            dwumw__frw = cbmof__ulpe[2]
            ozqos__xuyn = cbmof__ulpe[3]
            lgor__bitv = []
            for ilhvm__gqut in dwumw__frw:
                if ilhvm__gqut == 'scatter':
                    lgor__bitv.append(bodo.scatterv(None))
                elif ilhvm__gqut == 'bcast':
                    lgor__bitv.append(prt__yhu.bcast(None, root=MASTER_RANK))
            lkdm__fav = {}
            for argname, ilhvm__gqut in ozqos__xuyn.items():
                if ilhvm__gqut == 'scatter':
                    lkdm__fav[argname] = bodo.scatterv(None)
                elif ilhvm__gqut == 'bcast':
                    lkdm__fav[argname] = prt__yhu.bcast(None, root=MASTER_RANK)
            gkbg__anak = func(*lgor__bitv, **lkdm__fav)
            if gkbg__anak is not None and func.overloads[func.signatures[0]
                ].metadata['is_return_distributed']:
                bodo.gatherv(gkbg__anak)
            del (cbmof__ulpe, ckvvd__ygd, func, wvfh__ymk, dwumw__frw,
                ozqos__xuyn, lgor__bitv, lkdm__fav, gkbg__anak)
            gc.collect()
        elif cbmof__ulpe[0] == 'exit':
            exit()
    assert False


def master_wrapper(func, *args, **kwargs):
    prt__yhu = MPI.COMM_WORLD
    if {'all_args_distributed', 'all_args_distributed_block',
        'all_args_distributed_varlength'} & set(func.targetoptions.keys()):
        dwumw__frw = ['scatter' for vly__rfmyp in range(len(args))]
        ozqos__xuyn = {argname: 'scatter' for argname in kwargs.keys()}
    else:
        kqfn__hvntf = func.py_func.__code__.co_varnames
        fcktl__daedv = func.targetoptions

        def get_distribution(argname):
            if argname in fcktl__daedv.get('distributed', []
                ) or argname in fcktl__daedv.get('distributed_block', []):
                return 'scatter'
            else:
                return 'bcast'
        dwumw__frw = [get_distribution(argname) for argname in kqfn__hvntf[
            :len(args)]]
        ozqos__xuyn = {argname: get_distribution(argname) for argname in
            kwargs.keys()}
    wwhwq__fzxx = pickle.dumps(func.py_func)
    prt__yhu.bcast(['exec', wwhwq__fzxx, dwumw__frw, ozqos__xuyn])
    lgor__bitv = []
    for ijlf__mpfjz, ilhvm__gqut in zip(args, dwumw__frw):
        if ilhvm__gqut == 'scatter':
            lgor__bitv.append(bodo.scatterv(ijlf__mpfjz))
        elif ilhvm__gqut == 'bcast':
            prt__yhu.bcast(ijlf__mpfjz)
            lgor__bitv.append(ijlf__mpfjz)
    lkdm__fav = {}
    for argname, ijlf__mpfjz in kwargs.items():
        ilhvm__gqut = ozqos__xuyn[argname]
        if ilhvm__gqut == 'scatter':
            lkdm__fav[argname] = bodo.scatterv(ijlf__mpfjz)
        elif ilhvm__gqut == 'bcast':
            prt__yhu.bcast(ijlf__mpfjz)
            lkdm__fav[argname] = ijlf__mpfjz
    puv__ceu = []
    for zegfn__cjca, rjp__zpr in list(func.py_func.__globals__.items()):
        if isinstance(rjp__zpr, MasterModeDispatcher):
            puv__ceu.append((func.py_func.__globals__, zegfn__cjca, func.
                py_func.__globals__[zegfn__cjca]))
            func.py_func.__globals__[zegfn__cjca] = rjp__zpr.dispatcher
    gkbg__anak = func(*lgor__bitv, **lkdm__fav)
    for ryy__bajbo, zegfn__cjca, rjp__zpr in puv__ceu:
        ryy__bajbo[zegfn__cjca] = rjp__zpr
    if gkbg__anak is not None and func.overloads[func.signatures[0]].metadata[
        'is_return_distributed']:
        gkbg__anak = bodo.gatherv(gkbg__anak)
    return gkbg__anak


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
