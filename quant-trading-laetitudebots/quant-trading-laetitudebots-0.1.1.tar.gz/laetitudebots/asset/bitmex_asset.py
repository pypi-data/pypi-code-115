import numpy as np

from laetitudebots.asset import Asset

BITMEX_CONTRACT_MULTIPLIER = {
    'ADA': 0.01,
    'BCH': 0.000001,
    'BNB': 0.0001,
    'DOT': 0.0001,
    'EOS': 0.0001,
    'ETH': 0.000001,
    'LINK': 0.0001,
    'LTC': 0.000002,
    'XBT': 1,
    'XRP': 0.0002,
    'XTZ': 0.0001,
    'YFI': 0.0000001
}


class BitmexAsset(Asset):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'USD' in self.symbol and not self.symbol.startswith('BTC'):
            for key, value in BITMEX_CONTRACT_MULTIPLIER.items():
                if self.symbol.startswith(key):
                    self.mult = value
                    break
            else:
                raise ValueError(
                    f'Symbol not in BitMEX Contract Multiplier: {self.symbol}')
        else:
            self.mult = 1

    def pnl_calculator(self, size, price, avg_price, collateral_price=None):
        if self.symbol.startswith('BTC'):
            # sentinel guards 1/0 which usually happens when position is
            # 0 at the start. This allows 0*(high number) equal to 0 instead
            # of 0*(infinity) which is undefined
            sentinel = np.nan_to_num(1/avg_price - 1/price)
            pnl = size * sentinel
        else:
            pnl = size * self.mult * (price - avg_price)

        return pnl

    def fee_calculator(self, size, price, order_type, collateral_price=None):
        if order_type in ['limit', 'stop_limit']:
            fee_pct = self.maker_fee
        else:
            fee_pct = self.taker_fee

        if self.symbol.startswith('BTC'):
            fee = (size / price) * fee_pct
        else:
            fee = size * self.mult * price * fee_pct

        return -fee

    def get_contract_rate(self, price, collateral_price=None):
        if self.symbol.startswith('BTC'):
            rate = price
        else:
            rate = 1 / (price * self.mult)

        return rate
