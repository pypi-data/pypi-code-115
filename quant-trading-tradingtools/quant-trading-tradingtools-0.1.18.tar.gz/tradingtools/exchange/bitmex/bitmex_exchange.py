# -*- coding: utf-8 -*-
from typing import Dict, List

import ccxt
import pandas as pd

from tradingtools.exchange.abc import ABCExchange
from tradingtools.util import to_nearest
from .bitmex_response_mapper import BitmexResponseMapper

__all__ = ['BitmexExchange']


class BitmexExchange(ABCExchange):
    name = 'bitmex'
    mapper = BitmexResponseMapper

    @property
    def base_rest_url(self) -> str:
        if self.test:
            return 'https://testnet.bitmex.com/api/v1'
        return 'https://bitmex.com/api/v1'

    @property
    def base_wss_url(self) -> str:
        if self.test:
            return 'wss://testnet.bitmex.com/ws'
        return 'wss://bitmex.com/ws'

    def cancel_order(self, order_id, params={}, *args, **kwargs) -> str:
        try:
            response = self.ccxt_obj.cancel_order(order_id, params=params)
        except Exception:
            raise

        return response

    def cancel_orders(self, symbol=None, params={}) -> dict:
        if symbol:
            symbol = self.ccxt_obj.markets_by_id[symbol]['symbol']
        try:
            response = self.ccxt_obj.cancel_all_orders(
                symbol=symbol,
                params=params,
            )
        except Exception:
            raise

        return response

    def close_position(self, symbol) -> dict:
        positions = self.get_positions(symbol)
        position = None
        for p in positions:
            if p['symbol'] == symbol:
                position = p
                break
        if position is None:
            raise ValueError('No position to close')

        side = 'buy' if position['side'] == 'sell' else 'sell'

        order = self.post_order(
            position['symbol'],
            'market',
            side,
            abs(position['size']),
            reduce_only=True,
        )

        return order

    def close_positions(self) -> List[dict]:
        positions = self.get_positions()

        orders = []
        for p in positions:
            side = 'buy' if p['side'] == 'sell' else 'sell'
            order = self.post_order(
                p['symbol'],
                'market',
                side,
                abs(p['size']),
                reduce_only=True,
            )
            orders.append(order)

        return orders

    def get_ohlcv_parameters(
        self,
        start,
        end,
        limit,
        symbol,
        timeframe,
        tf_len,
        tf_format,
        partial,
    ):
        start = pd.to_datetime(start) + pd.Timedelta(timeframe)
        start = start.strftime(tf_format)

        start_time = pd.to_datetime(start)
        end_time = pd.to_datetime(end)
        start_time_key = 'startTime'
        end_time_key = 'endTime'
        params = {
            'reverse': False,
            'count': min(limit or 1000, 1000),
            start_time_key: start_time.strftime(tf_format),
            end_time_key: end_time.strftime(tf_format),
        }

        def start_time_conv(ts):
            res = pd.to_datetime(ts, unit='ms').strftime('%Y-%m-%d %H:%M:%S')

            return res

        def end_time_conv(ts):
            return params[end_time_key]

        return {
            'symbol': self.ccxt_obj.markets_by_id[symbol]['symbol'],
            'start_time_key': start_time_key,
            'start_time_conv': start_time_conv,
            'end_time_key': end_time_key,
            'end_time_conv': end_time_conv,
            'params': params,
        }

    def get_open_order(self, order_id) -> dict:
        try:
            response = self.ccxt_obj.fetch_order(order_id)
        except ccxt.OrderNotFound:
            raise ValueError('Bitmex Order not found.')
        except Exception:
            raise

        order = self.mapper.map_order_response(response['info'])

        return order

    def get_open_orders(self, symbol=None) -> List[dict]:
        try:
            response = self.ccxt_obj.fetch_open_orders()
        except Exception:
            raise

        orders = []
        if symbol:
            orders = [
                self.mapper.map_order_response(r['info'])
                for r in response
                if r['info']['symbol'] == symbol
            ]
        else:
            orders = [
                self.mapper.map_order_response(r['info']) for r in response
            ]

        return orders

    def get_positions(self, collateral_symbol=None, round_pnl=8) -> List[dict]:
        if collateral_symbol and not isinstance(collateral_symbol, str):
            raise ValueError('collateral_symbol must be a string')

        if round_pnl < 0 or not isinstance(round_pnl, int):
            raise ValueError('round_pnl must be a positive integer')

        try:
            positions = self.ccxt_obj.private_get_position(
                {'filter': self.ccxt_obj.json({'isOpen': True})}
            )
        except Exception:
            raise

        if not positions:
            return []

        tickers = self.ccxt_obj.fetch_tickers()
        if collateral_symbol:
            collateral_symbol = self.ccxt_obj.markets_by_id[collateral_symbol][
                'symbol'
            ]
        positions = [
            self.mapper.map_get_positions_response(
                p,
                tickers,
                collateral_symbol=collateral_symbol,
                round_pnl=round_pnl,
            )
            for p in positions
        ]
        return positions

    def get_wallets(self) -> Dict[str, List[dict]]:
        try:
            balance = self.ccxt_obj.fetchBalance()['info'][0]
        except Exception:
            raise

        account_wallets = {'main': [self.mapper.map_balance_response(balance)]}
        return account_wallets

    def modify_order(
        self,
        order_id,
        price=None,
        size=None,
        trigger_price=None,
        trail_value=None,
    ) -> dict:
        symbol = self.get_open_order(order_id)['symbol']
        market_info = self.markets[
            self.ccxt_obj.markets_by_id[symbol]['symbol']
        ]
        size_increment = market_info['info']['lotSize']
        price_increment = market_info['info']['tickSize']

        if size:
            size = to_nearest(size, size_increment)
        if price:
            price = to_nearest(price, price_increment)
        if trigger_price:
            trigger_price = to_nearest(trigger_price, price_increment)
        if trail_value:
            trail_value = to_nearest(trail_value, price_increment)

        params = {}

        if trigger_price:
            params['stopPx'] = trigger_price
        if trail_value:
            params['pegOffsetValue'] = trail_value

        response = self.ccxt_obj.edit_order(
            order_id, None, None, None, amount=size, price=price, params=params
        )

        order = self.mapper.map_order_response(response['info'])

        return order

    def post_order(
        self,
        symbol,
        order_type,
        side,
        size,
        price=None,
        post_only=False,
        reduce_only=False,
        trigger_price=None,
        trigger_price_type=None,
        close_on_trigger=False,
        trail_value=None,
    ) -> dict:
        size_increment = self.size_inc(symbol)
        price_increment = self.price_inc(symbol)

        size = to_nearest(size, size_increment)

        if price:
            price = to_nearest(price, price_increment)
        if trigger_price:
            trigger_price = to_nearest(trigger_price, price_increment)
        if trail_value:
            trail_value = to_nearest(trail_value, price_increment)

        params = {}
        exec_inst_params = []

        if reduce_only is True:
            exec_inst_params.append('ReduceOnly')
        if post_only is True:
            exec_inst_params.append('ParticipateDoNotInitiate')
        if close_on_trigger is True:
            exec_inst_params.append('Close')
        if trigger_price_type and trigger_price_type != 'MarkPrice':
            exec_inst_params.append(trigger_price_type)
        if trail_value:
            params['pegOffsetValue'] = trail_value
            params['pegPriceType'] = 'TrailingStopPeg'
        if trigger_price:
            params['stopPx'] = trigger_price

        if len(exec_inst_params):
            params['execInst'] = ','.join(exec_inst_params)

        try:
            response = self.ccxt_obj.create_order(
                self.ccxt_obj.markets_by_id[symbol]['symbol'],
                order_type.title().replace('_', ''),
                side,
                size,
                price=price,
                params=params,
            )
        except Exception:
            raise

        order = self.mapper.map_order_response(response['info'])

        return order

    def size_inc(self, symbol):
        market_info = self.markets[
            self.ccxt_obj.markets_by_id[symbol]['symbol']
        ]
        return market_info['info']['lotSize']

    def price_inc(self, symbol):
        market_info = self.markets[
            self.ccxt_obj.markets_by_id[symbol]['symbol']
        ]
        return market_info['info']['tickSize']
