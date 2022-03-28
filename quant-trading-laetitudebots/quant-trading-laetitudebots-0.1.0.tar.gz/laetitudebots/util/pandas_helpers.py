# -*- encoding: utf-8 -*-

import pandas as pd


def resample(ohlcv_df, freq):
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
