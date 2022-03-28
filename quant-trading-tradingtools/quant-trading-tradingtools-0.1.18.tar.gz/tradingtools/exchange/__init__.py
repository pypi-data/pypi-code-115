# -*- coding: utf-8 -*-

from .binance import BinanceSpotExchange
from .bitmex import BitmexExchange
from .deribit import DeribitExchange
from .ftx import FTXExchange

__all__ = ['exchange_factory']


class ExchangeFactory:
    def __init__(self):
        self._exchanges = {}

    def register_exchange(self, exchange_class):
        self._exchanges[exchange_class.name] = exchange_class

    def get_exchange(
        self,
        exchange_name: str,
        api_key: str = None,
        api_secret: str = None,
        test: bool = False,
        headers: dict = None,
    ):
        exchange_class = self._exchanges.get(exchange_name)
        if not exchange_class:
            raise ValueError(f'Exchange {exchange_name} not implemented')
        return exchange_class(
            api_key=api_key, api_secret=api_secret, test=test, headers=headers
        )


exchange_factory = ExchangeFactory()
exchange_factory.register_exchange(BinanceSpotExchange)
exchange_factory.register_exchange(BitmexExchange)
exchange_factory.register_exchange(DeribitExchange)
exchange_factory.register_exchange(FTXExchange)
