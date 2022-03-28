# -*- coding: utf-8 -*-

import asyncio
import copy
import datetime
import json
from typing import Dict, List, Union

import ccxt
import pandas as pd
import pytz
import websockets

from tradingtools.exchange.abc import ABCExchange
from tradingtools.util import websocket_error_handler
from .deribit_response_mapper import DeribitResponseMapper

__all__ = ['DeribitExchange']

RESOLUTIONS = {
    '1d': '1D',
    '12h': '720',
    '6h': '360',
    '3h': '180',
    '2h': '120',
    '1h': '60',
    '30m': '30',
    '15m': '15',
    '10m': '10',
    '5m': '5',
    '3m': '3',
    '1m': '1',
}


class DeribitExchange(ABCExchange):
    name = 'deribit'

    def __init__(
        self,
        api_key: str = None,
        api_secret: str = None,
        test: bool = None,
        app_id: Union[int, float] = 1,
        headers: dict = None,
    ):
        super().__init__(api_key=api_key, api_secret=api_secret, test=test, headers=headers)
        self.__payload_base = {
            'jsonrpc': '2.0',
            'id': app_id,
            'method': '',
            'params': {},
        }

    @property
    def base_rest_url(self) -> str:
        if self.test:
            return 'wss://test.deribit.com/ws/api/v2'
        return 'wss://www.deribit.com/ws/api/v2'

    @property
    def base_wss_url(self) -> str:
        if self.test:
            return 'wss://test.deribit.com/ws/api/v2'
        return 'wss://www.deribit.com/ws/api/v2'

    @property
    def payload_base(
        self,
    ) -> Dict[
        str, Union[str, int, float, Dict[str, Union[str, int, float, bool]]]
    ]:
        return self.__payload_base

    def cancel_order(
        self, order_id: str, *args, **kwargs
    ) -> Dict[str, Union[str, int, float, bool]]:
        result = asyncio.run(self.__cancel_order(order_id))

        return result

    @websocket_error_handler
    async def __cancel_order(
        self, order_id: str
    ) -> Dict[str, Union[str, int, float, bool]]:
        async with websockets.connect(self.base_wss_url) as ws:
            await self.__authenticate_ws_connection(ws)

            payload = self.parse_cancel_payload(order_id)
            await ws.send(payload)

            response = await ws.recv()
            order = self.parse_cancel_response(response)

        return order

    def parse_cancel_payload(self, order_id: str) -> str:
        payload = copy.deepcopy(self.payload_base)
        payload['method'] = 'private/cancel'
        payload['params'] = {'order_id': order_id}

        return json.dumps(payload)

    @staticmethod
    def parse_cancel_response(
        response: str,
    ) -> Dict[str, Union[str, int, float, bool]]:
        response = json.loads(response)

        order = DeribitResponseMapper.map_order_response(response['result'])

        return order

    def cancel_orders(self) -> int:
        result = asyncio.run(self.__cancel_orders())

        return result

    @websocket_error_handler
    async def __cancel_orders(self) -> int:
        async with websockets.connect(self.base_wss_url) as ws:
            await self.__authenticate_ws_connection(ws)

            payload = self.parse_cancel_all_payload()
            await ws.send(payload)

            response = await ws.recv()
            total_cancelled = self.parse_cancel_all_response(response)

        return total_cancelled

    def parse_cancel_all_payload(self) -> str:
        payload = copy.deepcopy(self.payload_base)
        payload['method'] = 'private/cancel_all'
        payload['params'] = {}

        return json.dumps(payload)

    @staticmethod
    def parse_cancel_all_response(response: str) -> int:
        response = json.loads(response)

        return response['result']

    def close_position(
        self,
        instrument_name: str,
        order_type: str,
        price: Union[int, float] = None,
    ) -> Dict[str, Union[str, int, float, bool]]:
        result = asyncio.run(
            self.__close_position(instrument_name, order_type, price=price)
        )

        return result

    @websocket_error_handler
    async def __close_position(
        self,
        instrument_name: str,
        order_type: str,
        price: Union[int, float] = None,
    ) -> Dict[str, Union[str, int, float, bool]]:
        async with websockets.connect(self.base_wss_url) as ws:
            await self.__authenticate_ws_connection(ws)

            payload = self.parse_close_position_payload(
                instrument_name, order_type, price=price
            )
            await ws.send(payload)

            response = await ws.recv()
            order = self.parse_close_position_response(response)

        return order

    def parse_close_position_payload(
        self,
        instrument_name: str,
        order_type: str,
        price: Union[int, float] = None,
    ) -> str:
        payload = copy.deepcopy(self.payload_base)
        payload['method'] = 'private/close_position'
        payload['params'] = {
            'instrument_name': instrument_name,
            'type': order_type,
        }
        if price and order_type == 'limit':
            payload['params']['price'] = price

        return json.dumps(payload)

    @staticmethod
    def parse_close_position_response(
        response: str,
    ) -> Dict[str, Union[str, int, float, bool]]:
        response = json.loads(response)

        order = DeribitResponseMapper.map_order_response(
            response['result']['order']
        )

        return order

    def close_positions(
        self, currency: str, kind: str = None
    ) -> List[Dict[str, Union[str, int, float, bool]]]:
        results = asyncio.run(self.__close_positions(currency, kind=kind))

        return results

    @websocket_error_handler
    async def __close_positions(
        self, currency: str, kind: str = None
    ) -> List[Dict[str, Union[str, int, float, bool]]]:
        async with websockets.connect(self.base_wss_url) as ws:
            await self.__authenticate_ws_connection(ws)

            get_positions_payload = self.parse_get_positions_payload(
                currency, kind=kind
            )
            await ws.send(get_positions_payload)

            get_positions_response = await ws.recv()
            positions = self.parse_get_positions_response(
                get_positions_response
            )

            close_position_payloads = []
            for p in positions:
                payload = self.parse_close_position_payload(
                    p['symbol'], 'market'
                )
                close_position_payloads.append(payload)

            close_orders = []
            for payload in close_position_payloads:
                await ws.send(payload)

                close_order_response = await ws.recv()
                order = self.parse_close_position_response(
                    close_order_response
                )
                close_orders.append(order)

        return close_orders

    def get_ohlcv(
        self,
        instrument_name: str,
        start: str = None,
        end: str = None,
        time_frame: str = '1d',
    ) -> pd.DataFrame:
        if start is None:
            start_timestamp = int(
                (
                    datetime.datetime.now(tz=pytz.UTC)
                    - datetime.timedelta(365)
                ).timestamp()
                * 1000
            )
        else:
            start_timestamp = ccxt.Exchange.parse8601(start)

        if end is None:
            end_timestamp = int(
                datetime.datetime.now(tz=pytz.UTC).timestamp() * 1000
            )
        else:
            end_timestamp = ccxt.Exchange.parse8601(end)

        resolution = RESOLUTIONS[time_frame]

        result = asyncio.run(
            self.__get_ohlcv(
                instrument_name, start_timestamp, end_timestamp, resolution
            )
        )

        return result

    @websocket_error_handler
    async def __get_ohlcv(
        self,
        instrument_name: str,
        start_timestamp: int,
        end_timestamp: int,
        resolution: str,
    ):
        async with websockets.connect(self.base_wss_url) as ws:
            payload = self.parse_get_tradingview_chart_data_payload(
                instrument_name, start_timestamp, end_timestamp, resolution
            )
            await ws.send(payload)

            response = await ws.recv()
            ohlcv_data = self.parse_get_tradingview_chart_data_response(
                response
            )

        return ohlcv_data

    def parse_get_tradingview_chart_data_payload(
        self,
        instrument_name: str,
        start_timestamp: int,
        end_timestamp: int,
        resolution: str,
    ) -> str:
        payload = copy.deepcopy(self.payload_base)
        payload['method'] = 'public/get_tradingview_chart_data'
        payload['params'] = {
            'instrument_name': instrument_name,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp,
            'resolution': resolution,
        }

        return json.dumps(payload)

    @staticmethod
    def parse_get_tradingview_chart_data_response(
        response: str,
    ) -> pd.DataFrame:
        response = json.loads(response)
        timestamps = response['result']['ticks']
        open_prices = response['result']['open']
        high_prices = response['result']['high']
        low_prices = response['result']['low']
        close_prices = response['result']['close']
        volume = response['result']['volume']
        data = [
            timestamps,
            open_prices,
            high_prices,
            low_prices,
            close_prices,
            volume,
        ]

        data_df = pd.DataFrame(data)
        data_df = data_df.transpose()
        data_df.columns = [
            'timestamp',
            'open',
            'high',
            'low',
            'close',
            'volume',
        ]
        data_df['timestamp'] = pd.to_datetime(data_df['timestamp'], unit='ms')
        data_df.set_index('timestamp', inplace=True)
        return data_df

    def get_open_order(
        self, order_id: str
    ) -> Dict[str, Union[str, int, float, bool]]:
        results = asyncio.run(self.__get_open_order(order_id))
        return results

    @websocket_error_handler
    async def __get_open_order(
        self, order_id: str
    ) -> Dict[str, Union[str, int, float, bool]]:
        async with websockets.connect(self.base_wss_url) as ws:
            await self.__authenticate_ws_connection(ws)

            payload = self.parse_get_order_state_payload(order_id)
            await ws.send(payload)

            response = await ws.recv()
            order = self.parse_get_order_state_response(response)

        return order

    def parse_get_order_state_payload(self, order_id: str) -> str:
        payload = copy.deepcopy(self.payload_base)
        payload['method'] = 'private/get_order_state'
        payload['params'] = {'order_id': order_id}

        return json.dumps(payload)

    @staticmethod
    def parse_get_order_state_response(
        response: str,
    ) -> Dict[str, Union[str, int, float, bool]]:
        response = json.loads(response)

        order = DeribitResponseMapper.map_order_response(response['result'])

        return order

    def get_open_orders(
        self, currency: str, kind: str = None, order_type: str = 'all'
    ) -> List[Dict[str, Union[str, int, float, bool]]]:
        results = asyncio.run(
            self.__get_open_orders(currency, kind=kind, order_type=order_type)
        )

        return results

    @websocket_error_handler
    async def __get_open_orders(
        self, currency: str, kind: str = None, order_type: str = 'all'
    ) -> List[Dict[str, Union[str, int, float, bool]]]:
        async with websockets.connect(self.base_wss_url) as ws:
            await self.__authenticate_ws_connection(ws)

            payload = self.parse_get_open_orders_by_currency_payload(
                currency, kind=kind, order_type=order_type
            )
            await ws.send(payload)

            response = await ws.recv()
            order = self.parse_get_open_orders_by_currency_response(response)

        return order

    def parse_get_open_orders_by_currency_payload(
        self, currency: str, kind: str = None, order_type: str = 'all'
    ) -> str:
        payload = copy.deepcopy(self.payload_base)
        payload['method'] = 'private/get_open_orders_by_currency'
        payload['params'] = {'currency': currency, 'type': order_type}
        if kind is not None:
            payload['params']['kind'] = kind

        return json.dumps(payload)

    @staticmethod
    def parse_get_open_orders_by_currency_response(
        response: str,
    ) -> List[Dict[str, Union[str, int, float, bool]]]:
        response = json.loads(response)

        orders = []
        for o in response['result']:
            order = DeribitResponseMapper.map_order_response(o)
            orders.append(order)

        return orders

    def get_positions(
        self, currency: str, kind: str = None
    ) -> List[Dict[str, Union[str, int, float, bool]]]:
        result = asyncio.run(self.__get_positions(currency, kind=kind))

        return result

    @websocket_error_handler
    async def __get_positions(
        self, currency: str, kind: str = None
    ) -> List[Dict[str, Union[str, int, float, bool]]]:
        async with websockets.connect(self.base_wss_url) as ws:
            await self.__authenticate_ws_connection(ws)

            payload = self.parse_get_positions_payload(currency, kind=kind)
            await ws.send(payload)

            response = await ws.recv()
            positions = self.parse_get_positions_response(response)

        return positions

    def parse_get_positions_payload(
        self, currency: str, kind: str = None
    ) -> str:
        payload = copy.deepcopy(self.payload_base)
        payload['method'] = 'private/get_positions'
        payload['params'] = {
            'currency': currency,
        }
        if kind is not None:
            payload['params']['kind'] = kind

        return json.dumps(payload)

    @staticmethod
    def parse_get_positions_response(
        response: str,
    ) -> List[Dict[str, Union[str, int, float, bool]]]:
        response = json.loads(response)
        positions = []
        for p in response['result']:
            if p['size'] == 0:
                continue

            position = DeribitResponseMapper.map_position_response(p)
            positions.append(position)

        return positions

    def get_wallets(
        self,
    ) -> Dict[str, List[Dict[str, Union[str, int, float]]]]:
        result = asyncio.run(self.__get_wallets())

        return result

    @websocket_error_handler
    async def __get_wallets(
        self,
    ) -> Dict[str, List[Dict[str, Union[str, int, float]]]]:
        async with websockets.connect(self.base_wss_url) as ws:
            await self.__authenticate_ws_connection(ws)

            payload = self.parse_get_subaccounts_payload()
            await ws.send(payload)

            response = await ws.recv()
            account_wallets = self.parse_get_subaccounts_response(response)

        return account_wallets

    def parse_get_subaccounts_payload(self) -> str:
        payload = copy.deepcopy(self.payload_base)
        payload['method'] = 'private/get_subaccounts'
        payload['params'] = {'with_portfolio': True}

        return json.dumps(payload)

    @staticmethod
    def parse_get_subaccounts_response(
        response: str,
    ) -> Dict[str, List[Dict[str, Union[str, int, float]]]]:
        response = json.loads(response)

        accounts_wallets = {}
        for subaccount in response['result']:
            wallets = []
            for p in subaccount['portfolio'].values():
                wallet = DeribitResponseMapper.map_balance_response(p)
                wallets.append(wallet)

            if subaccount['type'] == 'main':
                name = 'main'
            else:
                name = subaccount['username']
            accounts_wallets[name] = wallets

        return accounts_wallets

    def modify_order(
        self,
        order_id: str,
        amount: Union[int, float],
        price: Union[int, float],
        **kwargs,
    ) -> Dict[str, Union[str, int, float, bool]]:
        result = asyncio.run(
            self.__modify_order(order_id, amount, price, **kwargs)
        )

        return result

    @websocket_error_handler
    async def __modify_order(
        self,
        order_id: str,
        amount: Union[int, float],
        price: Union[int, float],
        **kwargs,
    ) -> Dict[str, Union[str, int, float, bool]]:
        async with websockets.connect(self.base_wss_url) as ws:
            await self.__authenticate_ws_connection(ws)

            payload = self.parse_edit_payload(
                order_id, amount, price, **kwargs
            )
            await ws.send(payload)

            response = await ws.recv()
            order = self.parse_edit_response(response)

        return order

    def parse_edit_payload(
        self,
        order_id: str,
        amount: Union[int, float],
        price: Union[int, float],
        **kwargs,
    ) -> str:
        payload = copy.deepcopy(self.payload_base)
        payload['method'] = 'private/edit'
        payload['params'] = {
            'order_id': order_id,
            'amount': amount,
            'price': price,
        }
        payload['params'] = {**payload['params'], **kwargs}

        return json.dumps(payload)

    @staticmethod
    def parse_edit_response(
        response: str,
    ) -> Dict[str, Union[str, int, float, bool]]:
        response = json.loads(response)

        order = DeribitResponseMapper.map_order_response(
            response['result']['order']
        )

        return order

    def post_order(
        self,
        instrument_name: str,
        amount: Union[int, float],
        side: str,
        order_type: str,
        **kwargs,
    ) -> Dict[str, Union[str, int, float, bool]]:
        result = asyncio.run(
            self.__post_order(
                instrument_name, amount, side, order_type, **kwargs
            )
        )

        return result

    @websocket_error_handler
    async def __post_order(
        self,
        instrument_name: str,
        amount: Union[int, float],
        side: str,
        order_type: str,
        **kwargs,
    ) -> Dict[str, Union[str, int, float, bool]]:
        async with websockets.connect(self.base_wss_url) as ws:
            await self.__authenticate_ws_connection(ws)

            payload = self.parse_buy_sell_payload(
                instrument_name, amount, side, order_type, **kwargs
            )
            await ws.send(payload)

            response = await ws.recv()
            order = self.parse_buy_sell_response(response)

        return order

    def parse_buy_sell_payload(
        self,
        instrument_name: str,
        amount: Union[int, float],
        side: str,
        order_type: str,
        **kwargs,
    ) -> str:
        payload = copy.deepcopy(self.payload_base)
        payload['method'] = f'private/{side}'
        payload['params'] = {
            'instrument_name': instrument_name,
            'amount': amount,
            'type': order_type,
        }
        payload['params'] = {**payload['params'], **kwargs}

        return json.dumps(payload)

    @staticmethod
    def parse_buy_sell_response(
        response: str,
    ) -> Dict[str, Union[str, int, float, bool]]:
        response = json.loads(response)

        order = DeribitResponseMapper.map_order_response(
            response['result']['order']
        )

        return order

    async def __authenticate_ws_connection(
        self, ws: websockets.WebSocketClientProtocol
    ) -> Dict[str, Union[str, int]]:
        payload = self.parse_auth_payload()
        await ws.send(payload)

        response = await ws.recv()
        auth = self.parse_auth_response(response)

        return auth

    def parse_auth_payload(self) -> str:
        payload = copy.deepcopy(self.payload_base)
        payload['method'] = 'public/auth'
        payload['params'] = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret,
        }

        return json.dumps(payload)

    @staticmethod
    def parse_auth_response(response: str) -> Dict[str, Union[str, int]]:
        response = json.loads(response)

        auth = DeribitResponseMapper.map_auth_response(response['result'])

        return auth

    def get_ohlcv_parameters(
        self,
        start: str,
        end: str,
        limit: int,
        symbol: str,
        timeframe: str,
        tf_len: int,
        tf_format: str,
        partial: bool,
    ) -> dict:
        super().get_ohlcv_parameters(
            start, end, limit, symbol, timeframe, tf_len, tf_format, partial
        )
