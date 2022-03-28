# -*- coding: utf-8 -*-

import abc
import datetime
from typing import Dict, List

import ccxt
import pandas as pd
import pytz
from tqdm.notebook import tqdm

from tradingtools.util import resample


__all__ = ['ABCExchange']


def in_notebook():
    try:
        __IPYTHON__
        return True
    except NameError:
        return False


class ABCExchange(abc.ABC):
    def __init__(
        self, api_key=None, api_secret=None, test=False, headers=None
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.test = test
        # binance has a different set of API for Margin, Futures,
        # and Spot so proposed convention would be binance-spot,
        # binance-margin etc.
        exchange = self.name.split('-')[0]
        ccxt_class = getattr(ccxt, exchange)
        if ccxt_class:
            init_dict = {
                'enableRateLimit': True,
                'apiKey': api_key,
                'secret': api_secret,
            }
            if headers:
                init_dict['headers'] = headers
            self.ccxt_obj = ccxt_class(init_dict)
            if test and self.ccxt_obj.urls.get('test'):
                self.ccxt_obj.urls['api'] = self.ccxt_obj.urls['test']
            self.markets = self.ccxt_obj.load_markets()
        else:
            self.ccxt_obj = None
            self.markets = None

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def base_rest_url(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def base_wss_url(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def cancel_order(self, *args, **kwargs) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def cancel_orders(self, *args, **kwargs) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    def close_position(self, *args, **kwargs) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    def close_positions(self, *args, **kwargs) -> List[dict]:
        raise NotImplementedError

    @abc.abstractmethod
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
        raise NotImplementedError

    @abc.abstractmethod
    def get_open_order(self, *args, **kwargs) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    def get_open_orders(self, *args, **kwargs) -> List[dict]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_positions(self, *args, **kwargs) -> List[dict]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_wallets(self) -> Dict[str, List[dict]]:
        raise NotImplementedError

    @abc.abstractmethod
    def modify_order(self, *args, **kwargs) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    def post_order(self, *args, **kwargs) -> dict:
        raise NotImplementedError

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: str = None,
        end: str = None,
        limit: int = None,
        partial: bool = False,
    ) -> pd.DataFrame:
        tf_format, tf_len = self._get_timeframe_settings(timeframe)
        data_start, data_end = self._get_start_end(
            start, end, limit, partial, timeframe, tf_format
        )
        exchange_settings = self.get_ohlcv_parameters(
            data_start,
            data_end,
            limit,
            symbol,
            timeframe,
            tf_len,
            tf_format,
            partial,
        )

        return self._download_ohlcv(
            data_start,
            data_end,
            timeframe,
            tf_len,
            partial,
            **exchange_settings,
        )

    @staticmethod
    def _get_timeframe_settings(timeframe: str) -> tuple:
        time_interval = int(timeframe[:-1])
        time_unit = timeframe[-1:]
        if time_unit == 'd':
            tf_len = 60 * 60 * 24 * 1000 * time_interval
            tf_format = '%Y-%m-%d 00:00:00 %Z'
        elif time_unit == 'h':
            tf_len = 60 * 60 * 1000 * time_interval
            tf_format = '%Y-%m-%d %H:00:00 %Z'
        elif time_unit == 'm':
            tf_len = 60 * 1000 * time_interval
            tf_format = '%Y-%m-%d %H:%M:00 %Z'
        else:
            raise ValueError(f'Unsupported timeframe {timeframe}.')

        return tf_format, tf_len

    @staticmethod
    def _get_start_end(start, end, limit, partial, timeframe, tf_format) -> tuple:
        end = end or datetime.datetime.now(tz=pytz.UTC)
        if partial:
            end = end + pd.Timedelta(timeframe)

        start = start or datetime.datetime.now(tz=pytz.UTC) - datetime.timedelta(days=365)
        if limit:
            start = end - limit * pd.Timedelta(timeframe)

        start = start.strftime(tf_format)
        end = end.strftime(tf_format)

        return start, end

    def _download_ohlcv(
        self,
        start,
        end,
        timeframe,
        tf_len,
        partial,
        symbol,
        start_time_key,
        start_time_conv,
        end_time_key,
        end_time_conv,
        params,
        *args,
        **kwargs
    ):

        now = datetime.datetime.now(tz=pytz.UTC)
        from_timestamp = int(pd.to_datetime(start).timestamp() * 1000)
        to_timestamp = int(pd.to_datetime(end).timestamp() * 1000)
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        data = []

        resample_data = False

        time_interval = timeframe[0:-1]
        time_unit = timeframe[-1]

        if in_notebook():
            progress_bar = tqdm(total=to_timestamp - from_timestamp)

        while from_timestamp < to_timestamp:
            print(f'Downloading data from {from_timestamp} to {to_timestamp}')
            try:
                candles = self.ccxt_obj.fetch_ohlcv(
                    symbol, timeframe, params=params
                )
            except KeyError:
                timeframe = f'1{time_unit}'
                resample_data = True
                continue

            last = candles[-1][0]

            if in_notebook():
                progress_bar.update(last - from_timestamp)

            from_timestamp = last + tf_len
            params[start_time_key] = start_time_conv(from_timestamp)
            params[end_time_key] = end_time_conv(from_timestamp)
            data += candles

        if in_notebook():
            progress_bar.update(progress_bar.total - progress_bar.n)
            progress_bar.close()

        data = pd.DataFrame(data, columns=columns)
        data['timestamp'] = pd.to_datetime(data.timestamp, unit='ms')
        data.set_index('timestamp', inplace=True)

        data = data[~data.index.duplicated(keep='first')]

        print(f'{symbol} data fetched from {self.name}')
        print(data.tail(10))

        if resample_data:
            frequency = str(time_interval) + time_unit.upper()
            print(f'Resampling data with {frequency} frequency')
            data = data.resample(frequency).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            })

            data.open = data.open.astype('float64').values
            data.high = data.high.astype('float64').values
            data.low = data.low.astype('float64').values
            data.close = data.close.astype('float64').values
            data.volume = data.volume.astype('float64').values

        if not partial:
            timeframe = str(time_interval) + time_unit
            data = data[: now - pd.Timedelta(timeframe)]


        return data
