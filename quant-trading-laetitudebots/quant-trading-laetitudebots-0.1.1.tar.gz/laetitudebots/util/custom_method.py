import pandas as pd


def custom_method(func, args):
    if not isinstance(args, (list, tuple)):
        raise ValueError('Must a list of arguments.')
    if len(args) == 0:
        raise ValueError('Empty arguments.')

    if not hasattr(args[0], 'columns'):
        raise ValueError('First argument is without columns for id.')

    assets = args[0].columns
    res = {}
    for asset in assets:
        params = []
        for arg in args:
            if hasattr(arg, '__array__'):
                params.append(arg[asset].values)
            else:
                params.append(arg)
        res[asset] = func(*params)

    return pd.DataFrame(res)
