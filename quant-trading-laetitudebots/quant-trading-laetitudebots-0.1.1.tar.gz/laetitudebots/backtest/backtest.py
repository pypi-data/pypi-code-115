from collections import defaultdict
from copy import deepcopy

import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd
import trading.datasets as tds
from tqdm.notebook import tqdm

from laetitudebots.asset import Asset, BitmexAsset
from laetitudebots.factors.factors import Factors
from laetitudebots.util.plotting import plot_equity


OFFSET_DATA_SKEW = 'data skew'
OFFSET_EXEC_DELAY = 'execution delay'


class Backtest:
    ohlcv = None
    assets = None
    positions = None
    factors = None
    config = None

    initialize = None
    process = None

    def __init__(self, config):
        self.pos_records = defaultdict(list)
        self.clock = []
        self.config = config

        # Keep the offset configs here to lessen
        # the redundancy in other parts of the class
        self.offset_type = config.get('offset_type')
        self.offset = tds.Timeframe(
            interval=config.get('offset_interval', 0),
            unit=config.get('offset_unit'))

        self.ohlcv = self.download_ohlcv(config)
        self.charting_ohlcv = self.download_charting_ohlcv(config)

    def update_config(self, config):
        if (config['time_interval'] != self.config['time_interval']
                or config['time_unit'] != self.config['time_unit']
                or config['start_date'] != self.config['start_date']
                or config['end_date'] != self.config['end_date']):
            self.config = config
            self.ohlcv = self.download_ohlcv(config)
        else:
            # caching - don't download again already downloaded data
            config_copy = deepcopy(self.config)
            # get all assets
            old_assets = set(self.config['context']['assets'].keys())
            new_assets = set(config['context']['assets'].keys())
            all_assets = new_assets.union(old_assets)

            new_config = deepcopy(config)
            # new config now contains all the assets in old and new configs
            config_copy.update(config)

            for symbol in all_assets:
                asset_old = self.config['context']['assets'].get(symbol, {})
                asset_new = config['context']['assets'].get(symbol, {})
                if (symbol in self.config['context']['assets']
                        and (asset_old.get('collateral')
                             == asset_new.get('collateral'))
                        and asset_new):
                    # symbol is already downloaded
                    new_config['context']['assets'].pop(symbol)
                elif not asset_new:
                    # symbol does not exist in new config so drop it
                    cols_to_drop = [(val, symbol) for val in
                                    ['open', 'high', 'low', 'close', 'volume']]
                    self.ohlcv.drop(columns=cols_to_drop, inplace=True)

            additional_ohlcv = self.download_ohlcv(new_config)

            self.config['context']['assets'] = config['context']['assets']
            self.config.update(config)

            self.ohlcv = pd.concat([self.ohlcv, additional_ohlcv], axis=1)

    def set_strategy(self, initialize=lambda *args: None,
                     process=lambda *args: None):
        self.initialize = initialize
        self.process = process

    def reset(self):
        self.pos_records = defaultdict(list)
        self.clock = []

    def download_ohlcv(self, config):
        assets = config['context']['assets']
        timeframe = f"{config['time_interval']}{config['time_unit']}"
        start = config['start_date']
        end = config['end_date']

        if self.offset_type == OFFSET_DATA_SKEW and self.offset.interval != 0:
            return self._download_ohlcv(
                assets, timeframe, start, end, offset=self.offset)

        return self._download_ohlcv(assets, timeframe, start, end)

    def download_charting_ohlcv(self, config):
        assets = config['context']['assets']
        timeframe = f"{config['time_interval']}{config['time_unit']}"
        start = config['start_date']
        end = config['end_date']

        if self.offset_type != OFFSET_EXEC_DELAY:
            return self.ohlcv

        return self._download_ohlcv(
            assets, timeframe, start, end, offset=self.offset)

    @staticmethod
    def _download_ohlcv(assets, timeframe, start, end, offset=None):
        dfs = {}

        downloaded_collateral = {}

        for symbol in assets:
            asset = assets[symbol]
            exchange = asset['exchange']
            print(f'Downloading {symbol}...')
            df = tds.OHLCV.from_exchange(
                exchange, symbol, timeframe, start, end, offset=offset)

            # check if you have to download collateral data
            if asset.get('collateral'):
                # All collateral data will be downloaded from Binance for
                # simplicity. In real life, collateral price will be
                # from exchange of execution
                coll = asset.get('collateral') + '/USDT'

                # caching
                if coll in downloaded_collateral:
                    coll_close = downloaded_collateral[coll]
                else:
                    print(f'Downloading collateral data {coll}...')
                    coll_close = tds.OHLCV.from_exchange(
                        'binance', coll, timeframe, start, end,
                        offset=offset).close
                    downloaded_collateral[coll] = coll_close

                dfs[('collateral', symbol)] = coll_close

            for col in df.columns:
                dfs[(col, symbol)] = df[col]

        return pd.DataFrame(dfs)

    def run(self, start=None, end=None, progressbar=False):
        self.reset()
        if start is None:
            start = self.config.get('start_date', self.ohlcv.index[0])
        if end is None:
            end = self.config.get('end_date', self.ohlcv.index[-1])

        window_length = self.config.get('window_length', 1)
        ohlcv = self.ohlcv[start:end]
        charting_ohlcv = self.charting_ohlcv[start:end]

        self.factors = Factors(ohlcv, window_length=window_length)
        self.charting_factors = Factors(
            charting_ohlcv, window_length=window_length)

        self.assets = self.initialize_assets(self.config)

        context = deepcopy(self.config['context'])

        self.initialize(self.factors, context)

        if progressbar:
            pbar = tqdm(total=len(ohlcv)-window_length)

        for window, charting_window in zip(self.factors, self.charting_factors):
            if self.offset_type == OFFSET_EXEC_DELAY:
                self.process_orders(charting_window, self.assets, context)
                self.record_positions(charting_window, self.assets, context)
            else:
                self.process_orders(window, self.assets, context)
                self.record_positions(window, self.assets, context)
            self.process(window, self.assets, context)

            if progressbar:
                pbar.update(1)

        if progressbar:
            pbar.update(pbar.total - pbar.n)
            pbar.close()

        self.positions = pd.DataFrame(self.pos_records)
        self.positions['timestamp'] = self.clock
        self.positions.set_index('timestamp', inplace=True)

    @staticmethod
    def initialize_assets(config):
        res = {}
        assets = config['context']['assets']
        # config['exchange'] is different
        # from a config['context']['assets'][coin]['exchange'] such that
        # the former is the exchange of execution while the the latter is
        # where to get data from
        # (e.g. CKS gets data from Binance but is executed in Bitmex)
        exchange = config['exchange']

        # almost every exchange has the same contract and pnl
        # calculation except Bitmex so it's better (for now) to create
        # a special class for Bitmex only and not for every exchange
        if exchange.lower() == 'bitmex':
            asset_class = BitmexAsset
        else:
            asset_class = Asset

        for symbol, variables in assets.items():
            kwargs = {
                'symbol': symbol,
                'taker_fee': variables['taker_fee'],
                'maker_fee': variables['maker_fee'],
                'collateral': variables.get('collateral'),
                'asset_type': variables.get('type', 'futures')
            }
            asset_obj = asset_class(**kwargs)
            res[symbol] = asset_obj

        return res

    def process_orders(self, window, assets, context):
        for symbol, asset in assets.items():
            latest = window.latest(symbol)
            orders = asset.orders
            orders_to_remove = []

            # remove cancelled orders
            # * needed for live
            asset.orders_to_cancel = []

            if asset.collateral:
                collateral = latest.collateral
            else:
                collateral = None

            for identifier, order in orders.items():
                if order['order_type'] == 'limit':
                    prev = window.previous(symbol, 2)
                    if prev.close > order['price'] and order['side'] == 'sell':
                        raise ValueError('Invalid limit order! Price too low.'
                                         f' Given: {order["price"]}, '
                                         f'Current price: {prev.close}, '
                                         f'Timestamp: {prev.timestamp}')

                    if prev.close < order['price'] and order['side'] == 'buy':
                        raise ValueError('Invalid limit order! Price too high.'
                                         f' Given: {order["price"]}, '
                                         f'Current price: {prev.close}, '
                                         f'Timestamp: {prev.timestamp}')

                    if latest.low < order['price'] < latest.high:
                        order['status'] = 'filled'
                        order['fill_price'] = order['price']

                        orders_to_remove.append(identifier)
                    else:
                        order['status'] = 'open'
                elif order['order_type'] == 'stop':
                    prev = window.previous(symbol, 2)
                    trigger_price = order['trigger_price']
                    if prev.close < trigger_price and order['side'] == 'sell':
                        raise ValueError('Invalid stop market order! '
                                         'Price too high.'
                                         f' Given: {trigger_price}, '
                                         f'Current price: {prev.close}, '
                                         f'Timestamp: {prev.timestamp}')

                    if prev.close > trigger_price and order['side'] == 'buy':
                        raise ValueError('Invalid stop market order!'
                                         ' Price too low.'
                                         f' Given: {trigger_price}, '
                                         f'Current price: {prev.close}, '
                                         f'Timestamp: {prev.timestamp}')

                    if latest.low < trigger_price < latest.high:
                        order['status'] = 'filled'
                        order['fill_price'] = self.slippage(trigger_price,
                                                            order['side'])
                        orders_to_remove.append(identifier)
                    else:
                        order['status'] = 'open'
                elif order['order_type'] == 'market':
                    order['fill_price'] = self.slippage(latest.open,
                                                        order['side'])
                    order['status'] = 'filled'
                    orders_to_remove.append(identifier)

                self.update_position(collateral, asset, order, context)

            if asset.position.size != 0:
                # NOTE: if asset type is spot, unrealised pnl translates
                # to asset value
                asset.position.unrealised_pnl = asset.pnl_calculator(
                    asset.position.size, latest.close,
                    asset.position.avg_price, collateral)
            else:
                asset.position.unrealised_pnl = 0

            for order in orders_to_remove:
                orders.pop(order)

    def update_position(self, collateral, asset, order, context):
        if context.get('is_shared_balance'):
            settings = context
        else:
            settings = context['assets'][asset.symbol]
        pos = asset.position

        if order['status'] == 'filled':
            # subtract fees from your balance
            settings['balance'] += asset.fee_calculator(
                order['size'], order['fill_price'], order['order_type'],
                collateral
            )

            if asset.type == 'spot':
                # subtract cost of the spot to the existing balance
                if order['side'] == 'buy':
                    val = -order['size'] * order['fill_price']
                    new_size = pos.size + order['size']
                    if new_size > pos.size:  # position was increased
                        pos.avg_price = self.calculate_avg_price(pos, order)
                    elif pos.size == 0:  # new position
                        pos.avg_price = order['fill_price']
                # since it's a sell, add the new value
                else:  # sell
                    val = order['size'] * order['fill_price']
                    new_size = pos.size - order['size']
                    if new_size == 0:
                        pos.avg_price = order['fill_price']
                settings['balance'] += val
                # NOTE avg price here is a matter of displaying purposes
                # in self.visualize
            else:
                if order['side'] == 'sell':
                    new_size = pos.size - order['size']
                    if pos.size < 0:  # position is increased
                        pos.avg_price = self.calculate_avg_price(pos, order)
                    elif pos.size == 0:  # no prior position
                        pos.avg_price = order['fill_price']
                    elif new_size > 0:  # position is reduced
                        # average entry price remains the same
                        settings['balance'] += asset.pnl_calculator(
                            order['size'], order['fill_price'], pos.avg_price,
                            collateral
                        )
                    elif new_size <= 0:  # reversed or exited all positions
                        settings['balance'] += asset.pnl_calculator(
                            pos.size, order['fill_price'], pos.avg_price,
                            collateral
                        )
                        # there is a new average price
                        pos.avg_price = order['fill_price']
                else:  # buy
                    new_size = pos.size + order['size']
                    if pos.size > 0:  # position is increased
                        pos.avg_price = self.calculate_avg_price(pos, order)
                        # reduce your balance by fees
                    elif pos.size == 0:
                        pos.avg_price = order['fill_price']
                    elif new_size < 0:  # position is reduced
                        # average entry price remains the same
                        settings['balance'] += asset.pnl_calculator(
                            order['size'], order['fill_price'], pos.avg_price,
                            collateral
                        )
                    elif new_size >= 0:  # reversed or exited all positions
                        settings['balance'] += asset.pnl_calculator(
                            pos.size, order['fill_price'], pos.avg_price,
                            collateral
                        )
                        # there is a new average price
                        pos.avg_price = order['fill_price']

            pos.size = new_size
            if pos.size > 0:
                pos.side = 'buy'
            elif pos.size < 0:
                pos.side = 'sell'
            else:
                pos.side = None

    @staticmethod
    def calculate_avg_price(pos, order):
        prev_size = abs(pos.size)
        total_size = prev_size + order['size']
        avg_price = (prev_size * pos.avg_price
                     + order['size'] * order['fill_price']) / total_size

        return avg_price

    def slippage(self, price, side):
        slip_pct = self.config['slippage']
        if side == 'sell':
            fill_price = price * (1 - slip_pct)
        else:  # buy
            fill_price = price * (1 + slip_pct)

        return fill_price

    def record_positions(self, window, assets, context):
        for symbol, asset in assets.items():
            latest = window.latest(symbol)
            pos = asset.position

            size = pos.size

            avg_price = pos.avg_price
            cur_price = latest.close

            self.pos_records[('size', symbol)].append(size)
            self.pos_records[('avg_price', symbol)].append(avg_price)
            self.pos_records[('cur_price', symbol)].append(cur_price)

            if not context.get('is_shared_balance'):
                balance = context['assets'][symbol]['balance']
                self.pos_records[('balance', symbol)].append(balance)

        if context.get('is_shared_balance'):
            balance = context['balance']
            self.pos_records[('balance', '')].append(balance)

        self.clock.append(window.clock[-1])

    def calculate_equity(self):
        pnl = {}

        for symbol, asset in self.assets.items():
            size = self.positions['size'][symbol]
            cur_price = self.positions['cur_price'][symbol]
            avg_price = self.positions['avg_price'][symbol]
            if asset.collateral:
                collateral = self.factors.ohlcv.collateral[symbol]
            else:
                collateral = None
            pnl[symbol] = asset.pnl_calculator(size, cur_price, avg_price,
                                               collateral).dropna()

        if self.config['context'].get('is_shared_balance'):
            equity = pd.DataFrame(pnl).sum(axis=1) + self.positions['balance']
        else:
            equity = pd.DataFrame(pnl) + self.positions['balance']

        return equity.fillna(method='bfill')

    def plot_performance(self):
        if self.config['context'].get('is_shared_balance'):
            equity = self.calculate_equity()
        else:
            equity = self.calculate_equity().sum(axis=1)

        ax = plot_equity(equity)

        return ax

    def visualize(self, symbol, factors=None, candles=True):
        _, ax = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]},
                             sharex=True, figsize=(5.5 * (16 / 9), 5.5))
        if factors is None:
            factors = []
            candles = True
        elif isinstance(factors, str):
            factors = [factors]

        if self.offset_type == OFFSET_EXEC_DELAY and not factors:
            factors_ohlcv = self.charting_factors.ohlcv
        else:
            factors_ohlcv = self.factors.ohlcv

        ohlcv = deepcopy(factors_ohlcv)
        positions = deepcopy(self.positions)

        # Copy factors into the OHLCv from the original OHLCV
        # for factor in factors:
        #     ohlcv[(factor, symbol)] = self.factors.ohlcv[(factor, symbol)]

        if candles:
            ohlcv.index = np.arange(len(ohlcv))
            positions.index = np.arange(len(positions)) + 1

        zorder = 1
        for factor in factors:
            if factor in ['open', 'high', 'low', 'close']:
                ax[0].step(ohlcv.index,
                           ohlcv[(factor, symbol)],
                           label=factor, where='mid', alpha=0.5)
            else:
                ax[0].plot(ohlcv[(factor, symbol)], label=factor)
            zorder += 1

        ts = positions.index
        max_price = ohlcv['high'][symbol].max()
        min_price = ohlcv['low'][symbol].min()
        size = positions['size'][symbol]

        ax[0].fill_between(ts, max_price, min_price,
                           where=size < 0, color='r', alpha=0.1)
        ax[0].fill_between(ts, max_price, min_price,
                           where=size > 0, color='g', alpha=0.1)

        zorder += 2

        ax[0].set_title('Factors')
        if factors:
            ax[0].legend()

        avg_price = positions['avg_price'][symbol]

        if (size > 0).any():
            ax[1].fill_between(size.index, size, 0, where=size > 0, alpha=0.3,
                               color='g', label='long')
            zorder += 1
        if (size < 0).any():
            ax[1].fill_between(size.index, size, 0, where=size < 0, alpha=0.3,
                               color='r', label='short')
            zorder += 1

        ax[1].set_title('Position')
        ax[1].legend()

        size_diff = size.diff()
        longs = size_diff[size_diff > 0].dropna().index
        shorts = size_diff[size_diff < 0].dropna().index

        # avg_price is used for interpolating trade prices but this
        # visualization will not show properly on multiple entries/exits
        ax[0].scatter(longs, avg_price[longs], marker='>', color='b',
                      zorder=zorder)
        ax[0].scatter(shorts, avg_price[shorts], marker='>', color='r',
                      zorder=zorder)

        quotes = pd.DataFrame({
            'open': factors_ohlcv[('open', symbol)],
            'high': factors_ohlcv[('high', symbol)],
            'low': factors_ohlcv[('low', symbol)],
            'close': factors_ohlcv[('close', symbol)],
        })

        if candles:
            mpf.plot(quotes, type='candle', ax=ax[0], style='yahoo')

        return ax
