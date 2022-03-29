# -*- coding: utf-8 -*-
from datetime import datetime

import pandas as pd
from ccxt import binance, bitmex, ftx
from tqdm.notebook import tqdm

from laetitudebots.util.pandas_helpers import resample


def in_notebook():
    try:
        __IPYTHON__
        return True
    except NameError:
        return False


def download_data(exchange, symbol, timeframe, start=None, end=None,
                  limit=None):
    time_interval = int(timeframe[:-1])
    time_unit = timeframe[-1:]
    if time_unit == 'd':
        tf_len = 60 * 60 * 24 * 1000 * time_interval
        tf_format = '%Y-%m-%d 00:00:00'
    elif time_unit == 'h':
        tf_len = 60 * 60 * 1000 * time_interval
        tf_format = '%Y-%m-%d %H:00:00'
    elif time_unit == 'm':
        tf_len = 60 * 1000 * time_interval
        tf_format = '%Y-%m-%d %H:%M:00'
    else:
        raise ValueError(f'Unsupported timeframe {timeframe}.')

    if start is None and limit:
        if end is None:
            end = datetime.utcnow()
        else:
            end = pd.to_datetime(end)
        start = end - limit * pd.Timedelta(timeframe)

        start = start.strftime(tf_format)
        end = end.strftime(tf_format)
    elif end is None and limit:
        end = pd.to_datetime(start) + limit * pd.Timedelta(timeframe)
        end = end.strftime(tf_format)
    else:
        start = start or '2013'
        end = end or datetime.utcnow().strftime(tf_format)

    if exchange.lower() == 'bitmex':
        exchange_client = bitmex({'enableRateLimit': True})
        start_time = pd.to_datetime(start) + pd.Timedelta(timeframe)
        end_time = pd.to_datetime(end) + pd.Timedelta(timeframe)
        start_time_key = 'startTime'
        end_time_key = 'endTime'
        start_time_conv = (lambda ts: pd.to_datetime(ts, unit='ms')
                                        .strftime('%Y-%m-%d %H:%M:%S'))
        params = {
            'count': limit or 1000,
            start_time_key: start_time.strftime('%Y-%m-%d %H:%M:%S'),
            end_time_key: end_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        end_time_conv = lambda ts: params[end_time_key]
    elif exchange.lower() == 'binance':
        exchange_client = binance({'enableRateLimit': True})
        start_time = int(pd.to_datetime(start).timestamp() * 1000)
        end_time = int(pd.to_datetime(end).timestamp() * 1000)
        start_time_key = 'startTime'
        end_time_key = 'endTime'
        start_time_conv = lambda ts: ts
        params = {
            'limit': limit or 1000,
            start_time_key: start_time,
            end_time_key: end_time
        }
        end_time_conv = lambda ts: params[end_time_key]
    elif exchange.lower() == 'ftx':
        exchange_client = ftx({'enableRateLimit': True})
        start_time = int(pd.to_datetime(start).timestamp())
        start_time_key = 'start_time'
        end_time_key = 'end_time'
        start_time_conv = lambda ts: int(ts/1000)
        params = {
            'limit': limit or 1500,
            start_time_key: start_time,
            end_time_key: int(1500 * (tf_len/1000) + start_time)
        }
        end_time_conv = lambda ts: int(1500*(tf_len/1000) + ts/1000)
    else:
        raise ValueError(f'Exchange {exchange} not supported yet!')

    from_timestamp = int(pd.to_datetime(start).timestamp() * 1000)
    to_timestamp = int(pd.to_datetime(end).timestamp() * 1000)
    columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    data = []

    resample_data = False
    resample_timeframe = timeframe

    if in_notebook():
        progress_bar = tqdm(total=to_timestamp-from_timestamp)

    while from_timestamp < to_timestamp:
        try:
            candles = exchange_client.fetch_ohlcv(symbol, timeframe,
                                                  params=params)
        except KeyError:
            timeframe = f'1{time_unit}'
            resample_data = True
            continue

        last = candles[-1][0]
        if in_notebook():
            progress_bar.update(last-from_timestamp)
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

    if resample_data:
        data = resample(data, resample_timeframe)

    return data[~data.index.duplicated(keep='first')]
