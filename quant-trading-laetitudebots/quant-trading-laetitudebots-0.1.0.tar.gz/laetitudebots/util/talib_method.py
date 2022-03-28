import pandas as pd
import talib


def talib_method(method, timeperiod, args):
    if not isinstance(args, (list, tuple)):
        raise ValueError('Must a list of arguments.')
    if len(args) == 0:
        raise ValueError('Empty arguments.')

    if not hasattr(args[0], 'columns'):
        raise ValueError('First argument is without columns for id.')

    assets = args[0].columns
    func = getattr(talib, method)
    res = {}
    for asset in assets:
        params = [arg[asset] for arg in args]
        res[asset] = func(*params, timeperiod=timeperiod)

    return pd.DataFrame(res)
