# -*- coding: utf-8 -*-

from typing import Dict, List

import ccxt
import pandas as pd

from tradingtools.exchange.abc import ABCExchange
from tradingtools.util import rounder, to_nearest

from .binance_response_mapper import BinanceResponseMapper

__all__ = ['BinanceSpotExchange']

ORDER_TYPES = {'market': 'market', 'limit': 'limit'}


class BinanceSpotExchange(ABCExchange):
    # binance defaults to binance-spot, in the future that margin and
    # futures are added, separate classes should should be created and
    # name it as 'binance-margin' or 'binance-futures'
    name = 'binance'

    @property
    def base_rest_url(self) -> str:
        # no test rest url
        return 'https://api.binance.com'

    @property
    def base_wss_url(self) -> str:
        return ''

    def cancel_order(self, order_id, details, *args, **kwargs) -> str:
        symbol = details['symbol']
        try:
            response = self.ccxt_obj.cancel_order(order_id, symbol=symbol)
        except ccxt.OrderNotFound:
            raise ValueError('Invalid order_id.')
        except Exception:
            raise

        return response

    def cancel_orders(
        self,
        symbol=None,
        conditional_orders_only=False,
        limit_orders_only=False,
    ) -> dict:
        try:
            response = self.ccxt_obj.cancel_all_orders(symbol=symbol)
        except Exception:
            raise

        return response

    def close_position(self, symbol) -> dict:
        pass

    def close_positions(self) -> List[dict]:
        pass

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
        start_time = int(pd.to_datetime(start).timestamp() * 1000)
        end_time = int(pd.to_datetime(end).timestamp() * 1000)
        start_time_key = 'startTime'
        end_time_key = 'endTime'
        params = {
            'limit': min(limit or 1500, 1500),
            start_time_key: start_time,
            end_time_key: end_time,
        }

        def start_time_conv(ts):
            return ts

        def end_time_conv(ts):
            return params[end_time_key]

        return {
            'symbol': symbol,
            'start_time_key': start_time_key,
            'start_time_conv': start_time_conv,
            'end_time_key': end_time_key,
            'end_time_conv': end_time_conv,
            'params': params,
        }

    def get_open_order(self, order_id) -> dict:
        pass

    def get_open_orders(self, symbol=None) -> List[dict]:
        self.ccxt_obj.options["warnOnFetchOpenOrdersWithoutSymbol"] = False

        try:
            response = self.ccxt_obj.fetch_open_orders(symbol=symbol)
        except Exception:
            raise
        orders = [
            BinanceResponseMapper.map_order_response(r) for r in response
        ]

        return orders

    def get_positions(self, collateral_symbol=None, round_pnl=8) -> List[dict]:
        # this class is only for spot
        # create a new one for margin and futures trading account
        return []

    def get_wallets(self) -> Dict[str, List[dict]]:
        balances = self.ccxt_obj.private_get_account()['balances']

        mapped_balance = map(
            BinanceResponseMapper.map_balance_response, balances
        )

        wallets = {'SPOT': [bal for bal in mapped_balance]}

        return wallets

    def modify_order(
        self,
        order_id,
        price=None,
        size=None,
        order_type=None,
        trigger_price=None,
        trail_value=None,
    ) -> dict:
        # no modify order for now since it's not used in live bot
        pass

    def post_order(
        self,
        symbol,
        order_type,
        side,
        size,
        price=None,
        trigger_price=None,
        trail_value=None,
        *args,
        **kwargs,
    ) -> dict:
        if order_type not in ['stop_loss_limit', 'limit', 'market']:
            raise ValueError(f'{order_type} not supported for this exchange!')

        params = None
        size_inc = self.size_inc(symbol)
        price_rounder = (
            lambda price, side: rounder(price, self.price_inc(symbol))
            if side == 'sell'
            else to_nearest(price, self.price_inc(symbol))
        )

        # this rounds down by default because this is spot and you
        # can't sell the minimum lot size
        if side == 'sell':
            size = rounder(size, size_inc)
        else:
            size = to_nearest(size, size_inc)

        if price:
            price = price_rounder(price, side)

        if trigger_price:
            trigger_price = price_rounder(trigger_price, side)
            params = {'stopPrice': trigger_price}

        try:
            response = self.ccxt_obj.create_order(
                symbol, order_type, side, size, price=price, params=params
            )
        except Exception:
            raise

        order = BinanceResponseMapper.map_order_response(response)

        return order

    def size_inc(self, symbol):
        market_info = self.markets[symbol]['info']
        for info in market_info['filters']:
            if info['filterType'] == 'LOT_SIZE':
                return float(info['stepSize'])

    def price_inc(self, symbol):
        market_info = self.markets[symbol]['info']
        for info in market_info['filters']:
            if info['filterType'] == 'PRICE_FILTER':
                return float(info['tickSize'])
