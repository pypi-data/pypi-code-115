from laetitudebots.model import Position


class Asset:

    def __init__(self, symbol, taker_fee=0, maker_fee=0, asset_type='futures',
                 collateral=None):
        self.symbol = symbol
        self.taker_fee = taker_fee
        self.maker_fee = maker_fee

        self.collateral = collateral

        self.orders = {}
        self.position = Position(symbol)

        self.orders_to_cancel = []

        self.type = asset_type

    def create_order(self, identifier, details):
        # cancel order if it exists
        self.cancel_order(identifier)
        self.orders[identifier] = details

    def cancel_order(self, identifier):
        if identifier in self.orders.keys():
            self.orders_to_cancel.append(self.orders.pop(identifier))

    def pnl_calculator(self, size, price, avg_price, collateral_price=None):
        if self.collateral and collateral_price is None:
            raise ValueError('collateral_price is required for assets with '
                             '"collateral" set to True')

        if self.type == 'futures':
            if collateral_price is not None:
                try:
                    collateral_price.index = collateral_price.index.tz_localize(None)
                except AttributeError:
                    pass
                pnl = size * (price - avg_price) / collateral_price
            else:  # anything else will follow generic pnl calculation
                pnl = size * (price - avg_price)
        elif self.type == 'spot':
            # not really pnl but value of the asset
            pnl = size * price
        else:
            raise ValueError(f'Unknown asset type {self.type}')

        return pnl

    def fee_calculator(self, size, price, order_type, collateral_price=None):
        if self.collateral and collateral_price is None:
            raise ValueError('collateral_price is required for assets with '
                             '"collateral" set to True')
        if order_type in ['limit', 'stop_limit']:
            fee_pct = self.maker_fee
        else:
            fee_pct = self.taker_fee

        if collateral_price is not None:
            fee = (size * price / collateral_price) * fee_pct
        else:  # anything else
            fee = (size * price) * fee_pct

        return -fee

    def get_contract_rate(self, price, collateral_price=1):
        rate = collateral_price / price

        return rate
