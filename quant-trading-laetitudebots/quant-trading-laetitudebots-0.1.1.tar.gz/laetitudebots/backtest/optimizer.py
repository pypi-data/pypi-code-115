import multiprocessing as mp
import os
from itertools import product

import pandas as pd
import quantstats as qs
from tqdm.notebook import tqdm


class Optimizer:
    def __init__(self, bt, start=None, end=None):
        self.bt = bt
        self.start = start
        self.end = end

    def runner(self, params):
        self.bt.config['context']['parameters'].update(params)
        self.bt.run(start=self.start, end=self.end)

        if self.bt.config['context'].get('is_shared_balance'):
            eq = self.bt.calculate_equity()
        else:
            eq = self.bt.calculate_equity().sum(axis=1)

        eq = eq[eq.index.hour == 0]
        rets = eq.pct_change().fillna(0)

        if rets.std() != 0:
            params['mdd'] = qs.stats.max_drawdown(rets)
            params['sortino'] = qs.stats.sortino(rets, periods=365, annualize=True)
            params['sharpe'] = qs.stats.sharpe(rets, periods=365, annualize=True)
            params['total_pnl'] = qs.stats.comp(rets) + 1
            params['avg_ret'] = rets.mean()
            params['score'] = (0.4 * (params['sortino']) + 0.2 * (params['sharpe'] + params['total_pnl'] + params['avg_ret'] / params['mdd']))

        return params

    def optimize(self, params):
        params_range = []
        key_index = []
        for key in params:
            key_index.append(key)
            params_range.append(params[key])

        params_list = []
        for prod in product(*params_range):
            params = {key_index[i]: prod[i] for i in range(len(prod))}
            params_list.append(params)

        processes = os.cpu_count()
        total = len(params_list)

        with mp.Pool(processes=processes) as pool:
            opt_res = list(tqdm(pool.imap_unordered(self.runner, params_list),
                                total=total))

        return pd.DataFrame(opt_res)
