# -*- coding: utf-8 -*-

from typing import Dict, List

import ccxt
import pandas as pd

from tradingtools.exchange.abc import ABCExchange
from tradingtools.util import to_nearest
from .ftx_response_mapper import FTXResponseMapper

__all__ = ['FTXExchange']

ORDER_TYPES = {
    'market': 'market',
    'limit': 'limit',
    'stop': 'stop',
    'trailing_stop': 'trailingStop',
    'take_profit': 'takeProfit',
}


class FTXExchange(ABCExchange):
    name = 'ftx'
    mapper = FTXResponseMapper

    @property
    def base_rest_url(self) -> str:
        if self.test:
            return 'https://ftx.com/api'
        return 'https://ftx.com/api'

    @property
    def base_wss_url(self) -> str:
        if self.test:
            return 'wss://ftx.com/ws'
        return 'wss://ftx.com/ws'

    def cancel_order(self, order_id, details, *args, **kwargs) -> str:
        try:
            params = None
            order_type = details.get('type')
            if order_type:
                params = {'type': order_type}
            response = self.ccxt_obj.cancel_order(order_id, params=params)
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
        params = {
            'conditionalOrdersOnly': conditional_orders_only,
            'limitOrdersOnly': limit_orders_only,
        }
        try:
            response = self.ccxt_obj.cancel_all_orders(
                symbol=symbol, params=params
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
                p['symbol'], 'market', side, abs(p['size']), reduce_only=True,
            )
            orders.append(order)

        return orders

    def get_ohlcv_parameters(
        self, start, end, limit, symbol, timeframe, tf_len, tf_format, partial,
    ):
        start_time = int(pd.to_datetime(start).timestamp())
        end_time = int(pd.to_datetime(end).timestamp())
        start_time_key = 'start_time'
        end_time_key = 'end_time'
        params = {
            'limit': min(limit or 1500, 1500),
            start_time_key: start_time,
            end_time_key: min(
                int(1500 * (tf_len / 1000) + start_time), end_time,
            ),
        }

        def start_time_conv(ts):
            return int(ts / 1000)

        def end_time_conv(ts):
            res = 1500 * (tf_len / 1000) + ts / 1000
            return int(min(res, end_time))

        return {
            'symbol': symbol,
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
            raise ValueError(
                'FTX Order not found. get_open_order() only supports '
                'non-trigger orders '
            )
        except Exception:
            raise

        order = FTXResponseMapper.map_order_response(response['info'])

        return order

    def get_open_orders(self, symbol=None) -> List[dict]:
        try:
            response = self.ccxt_obj.fetch_open_orders()
        except Exception:
            raise
        orders = [
            FTXResponseMapper.map_order_response(r['info']) for r in response
        ]

        try:
            response = self.ccxt_obj.request(
                'conditional_orders', api='private', method='GET'
            )
        except Exception:
            raise
        if not response['success']:
            raise ValueError('FTX get positions did not get a valid response')
        trigger_orders = []
        if response['result']:
            trigger_orders = [
                FTXResponseMapper.map_order_response(r)
                for r in response['result']
            ]

        all_orders = orders + trigger_orders

        if symbol:
            all_orders = [o for o in all_orders if o['symbol'] == symbol]

        return all_orders

    def get_positions(self, collateral_symbol=None, round_pnl=8) -> List[dict]:
        if collateral_symbol and not isinstance(collateral_symbol, str):
            raise ValueError('collateral_price must be a number')

        if round_pnl < 0 or not isinstance(round_pnl, int):
            raise ValueError('round_pnl must be a number')

        try:
            response = self.ccxt_obj.private_get_positions()
        except Exception:
            raise

        if not response['success']:
            raise ValueError('FTX get positions did not get a valid response')

        positions = []
        for position in response['result']:
            if position['netSize'] == 0:
                continue
            positions.append(position)

        if not positions:
            return []

        tickers = self.ccxt_obj.fetch_tickers()

        positions = [
            FTXResponseMapper.map_position_response(
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
            subaccount = self.ccxt_obj.headers.get('FTX-SUBACCOUNT')
            if subaccount:
                response = {
                    'result': {
                        subaccount: self.ccxt_obj.request(
                            'wallet/balances', api='private'
                        )['result']
                    }
                }
            else:
                response = self.ccxt_obj.request(
                    'wallet/all_balances', api='private'
                )
        except Exception:
            raise

        account_wallets = {}
        for account, wallets in response['result'].items():
            wallets_parsed = []
            for wallet in wallets:
                w = FTXResponseMapper.map_balance_response(wallet)
                wallets_parsed.append(w)

            account_wallets[account] = wallets_parsed

        return account_wallets

    def modify_order(
        self,
        order_id,
        price=None,
        size=None,
        order_type=None,
        trigger_price=None,
        trail_value=None,
    ) -> dict:
        params = {}

        if size:
            params['size'] = size

        if order_type in ['market', 'limit']:
            start_endpoint = 'orders'

            if price:
                params['price'] = price
        elif order_type in ['stop', 'trailingStop', 'takeProfit']:
            start_endpoint = 'conditional_orders'

            if order_type in ['stop', 'takeProfit']:
                if price:
                    params['orderPrice'] = price

                if trigger_price and not isinstance(
                    trigger_price, (int, float)
                ):
                    raise ValueError('triggerPrice must be int/float type.')
                params['triggerPrice'] = trigger_price
            else:
                if trail_value and not isinstance(trail_value, (int, float)):
                    raise ValueError('trailValue must be int/float type.')
                params['trailValue'] = trail_value
        else:
            raise ValueError(
                'Invalid order type. FTX order types: market, limit, stop, '
                'trailingStop, takeProfit '
            )

        endpoint = f'{start_endpoint}/{order_id}/modify'
        response = self.ccxt_obj.request(
            endpoint, api='private', method='POST', params=params
        )

        order = FTXResponseMapper.map_order_response(response['result'])

        return order

    def post_order(
        self,
        symbol,
        order_type,
        side,
        size,
        price=None,
        reduce_only=False,
        trigger_price=None,
        post_only=False,
        ioc=False,
        retry_until_filled=False,
        trail_value=None,
    ) -> dict:

        size_increment = self.size_inc(symbol)
        size = to_nearest(size, size_increment)

        if price:
            price_increment = self.price_inc(symbol)
            price = to_nearest(price, price_increment)

        if trigger_price:
            price_increment = self.price_inc(symbol)
            trigger_price = to_nearest(trigger_price, price_increment)

        params = {
            'reduceOnly': reduce_only,
        }

        order_type = ORDER_TYPES[order_type]

        if post_only:
            params['postOnly'] = post_only

        if ioc:
            params['ioc'] = ioc

        if retry_until_filled:
            params['retryUntilFilled'] = retry_until_filled

        if trigger_price:
            params['triggerPrice'] = trigger_price

        if trail_value:
            params['trailValue'] = trail_value

        try:
            response = self.ccxt_obj.create_order(
                symbol, order_type, side, size, price=price, params=params
            )
        except Exception:
            raise

        order = FTXResponseMapper.map_order_response(response['info'])

        return order

    def size_inc(self, symbol):
        market_info = self.markets[symbol]

        return market_info['info']['sizeIncrement']

    def price_inc(self, symbol):
        market_info = self.markets[symbol]

        return market_info['info']['priceIncrement']
