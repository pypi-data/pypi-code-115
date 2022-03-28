
from collections import defaultdict
from itertools import product

import pandas as pd


class Indexer:

    def __init__(self, timestamp, values, col_idx, symbol,
                 n, series=False):
        self.clock = timestamp
        self.values = values
        self.col_idx = col_idx
        self.symbol = symbol
        self.n = -n
        self.series = series

    def __getattr__(self, name):
        if name == 'timestamp':
            if self.series:
                return self.clock[self.n:]

            return self.clock[self.n]

        try:
            key = (name, self.symbol)
            idx = self.col_idx[key]
        except KeyError:
            key = (name, 'values')
            if key in self.col_idx:
                idx = self.col_idx[key]
            else:
                raise ValueError(f'No factor named {name}')

        if self.series:
            return self.values[self.n:, idx]

        return self.values[self.n, idx]


class Window:

    def __init__(self, column_dict):
        self.column_dict = column_dict
        self.factor_indices = defaultdict(list)

        for col, idx in self.column_dict.items():
            self.factor_indices[col[0]].append(idx)

        self.clock = None
        self.values = None

    def set_values(self, timestamp, values):
        self.clock = timestamp
        self.values = values

    def __getitem__(self, name):
        indices = self.factor_indices[name]

        return self.values[:, indices]

    def __getattr__(self, name):
        indices = self.factor_indices[name]

        return self.values[:, indices]

    def previous(self, symbol, n, series=False):
        return Indexer(self.clock, self.values,
                       self.column_dict, symbol, n,
                       series)

    def latest(self, symbol):
        return self.previous(symbol, 1)

    def __repr__(self):
        if self.clock is None:
            return 'Empty Window'
        return f"{self.clock[0]} to {self.clock[-1]}"


class Factors:
    def __init__(self, ohlcv, window_length=2):
        self.window_length = window_length

        self.ohlcv = ohlcv
        self.timestamp = ohlcv.index

    def __setattr__(self, name, value):
        special_attrs = ['ohlcv', 'timestamp']
        if hasattr(value, '__array__') and name not in special_attrs:
            if isinstance(value, pd.DataFrame):
                series = value.values
                columns = [col for col in product([name], value.columns)]
            elif value.shape == (self.ohlcv.shape[0],):
                series = value
                columns = [(name, 'values')]
            else:
                raise ValueError('Invalid numpy/dataframe!')

            for col_idx in range(len(columns)):
                col = columns[col_idx]
                if col[1] == 'values':
                    self.ohlcv.loc[:, col] = series
                else:
                    self.ohlcv.loc[:, col] = series[:, col_idx]
        else:
            super().__setattr__(name, value)

    def __setitem__(self, name, value):
        self.__setattr__(name, value)

    def __getitem__(self, item):
        return self.__getattribute__(item)

    def __reduce__(self):
        # this is needed to pickle correctly when optimizing using
        # the multiprocessing module
        return self.__class__, (self.ohlcv, self.window_length)

    def __getattribute__(self, attr):
        getter = super().__getattribute__
        ohlcv = getter('ohlcv')
        factors = ohlcv.columns.levels[0]
        if attr in factors:
            return ohlcv[attr]
        return getter(attr)

    def get_column_dict(self):
        cols = self.ohlcv.columns
        column_dict = {}
        for col_i in range(len(cols)):
            column_dict[cols[col_i]] = col_i

        return column_dict

    def __iter__(self):
        column_dict = self.get_column_dict()

        length = self.timestamp.shape[0]
        window = Window(column_dict)
        factor_values = self.ohlcv.values
        timestamp = self.timestamp.values

        if self.window_length == 0:
            starting_idx = 1
        else:
            starting_idx = self.window_length

        for idx in range(starting_idx, length+1):
            if self.window_length == 0:
                start = 0
            else:
                start = idx - self.window_length
            window_vals = factor_values[start:idx]
            clock = timestamp[start:idx]
            window.set_values(clock, window_vals)

            yield window

    @property
    def latest_window(self):
        column_dict = self.get_column_dict()
        window = Window(column_dict)
        factor_values = self.ohlcv.values
        timestamp = self.timestamp.values

        latest_vals = factor_values[-self.window_length:]
        clock = timestamp[-self.window_length:]

        window.set_values(clock, latest_vals)

        return window
