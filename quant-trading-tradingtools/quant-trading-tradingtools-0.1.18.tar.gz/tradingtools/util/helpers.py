# -*- coding: utf-8 -*-

from decimal import Decimal

import pandas as pd

__all__ = ['resample', 'to_nearest', 'rounder']


def resample(ohlcv_df: pd.DataFrame, freq: str) -> pd.DataFrame:
    if freq.endswith('m'):
        freq = freq.replace('m', 'T')
    open_ = ohlcv_df.open.resample(freq).first()
    close = ohlcv_df.close.resample(freq).last()
    high = ohlcv_df.high.resample(freq).max()
    low = ohlcv_df.low.resample(freq).min()
    volume = ohlcv_df.volume.resample(freq).sum()

    ohlcv_df = pd.DataFrame(
        {
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'datetime': close.index,
        }
    )

    ohlcv_df.set_index('datetime', inplace=True)

    return ohlcv_df


def to_nearest(value: (int, float), increment: (int, float)) -> float:
    increment_decimal = Decimal(str(increment))

    return float(Decimal(round(value / increment, 0)) * increment_decimal)


def rounder(value: (int, float), increment: (int, float), down=True) -> float:
    if down:
        return int(value/increment)*increment
    else:
        return (int(value/increment)+1)*increment
