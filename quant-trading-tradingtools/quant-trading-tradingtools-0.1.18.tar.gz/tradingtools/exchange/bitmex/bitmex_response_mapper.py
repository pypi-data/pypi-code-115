# -*- coding: utf-8 -*-
import numpy as np


__all__ = ['BitmexResponseMapper']


class BitmexResponseMapper:
    @staticmethod
    def map_balance_response(balance: dict) -> dict:
        xbt_sats_mult = 0.00000001
        return {
            'asset': 'BTC',
            'available': balance['availableMargin'] * xbt_sats_mult,
            'total': balance['walletBalance'] * xbt_sats_mult,
        }

    @staticmethod
    def map_order_response(order: dict) -> dict:
        order_type = (
            'TrailingStop'
            if order.get('pegPriceType') == 'TrailingStopPeg'
            else order['ordType']
        )

        return {
            'created_at': order['transactTime'],
            'id': order['orderID'],
            'symbol': order['symbol'],
            'type': order_type,
            'order_type': order_type,
            'side': order['side'],
            'size': order['orderQty'],
            'price': order.get('price'),
            'trigger_price': order.get('stopPx'),
            'trail_value': order.get('pegOffsetValue'),
            'filled_size': order.get('cumQty'),
            'remaining_size': order.get('leavesQty'),
            'status': order['ordStatus'],
            'reduce_only': 'ReduceOnly' in order['execInst'],
            'ioc': None,
            'post_only': 'ParticipateDoNotInitiate' in order['execInst'],
            'retry_until_filled': None,
        }

    @staticmethod
    def map_get_positions_response(
        position: dict,
        tickers: dict,
        collateral_symbol: str = None,
        round_pnl: int = 8,
    ) -> dict:
        symbol = position['symbol']
        current_price = position['lastPrice']
        side = 'buy' if position['currentQty'] > 0 else 'sell'
        size = position['currentQty']
        avg_price = position['avgEntryPrice']
        btc_usd_rate = tickers['BTC/USD']['info']['lastPrice']

        unrealized_usd_pnl = (
            BitmexResponseMapper._calculate_btc_pnl(
                symbol, size, current_price, avg_price
            )
            * btc_usd_rate
        )

        unrealized_pnl = 0
        if collateral_symbol:
            collateral_price = tickers[collateral_symbol]['info']['lastPrice']
            unrealized_pnl = unrealized_usd_pnl / collateral_price
        else:
            unrealized_pnl = unrealized_usd_pnl

        return {
            'symbol': symbol,
            'side': side,
            'size': size,
            'avg_price': avg_price,
            'unrealized_pnl': round(unrealized_pnl, round_pnl),
        }

    @staticmethod
    def _calculate_btc_pnl(
        symbol: str,
        size: (int, float),
        price: (int, float),
        avg_price: (int, float),
    ) -> float:
        symbol = symbol.replace('XBT', 'BTC')
        if symbol.startswith('BTC'):
            sentinel = np.nan_to_num(1 / avg_price - 1 / price)
            pnl = size * sentinel
        else:
            mult = BitmexResponseMapper._get_mult(symbol)
            pnl = size * mult * (price - avg_price)

        return pnl

    @staticmethod
    def _get_mult(symbol: str) -> float:
        if 'USD' in symbol and not symbol.startswith('BTC'):
            if symbol.startswith('ETH'):
                return 0.000001
            elif symbol.startswith('LTC'):
                return 0.000002
            elif symbol.startswith('XRP'):
                return 0.0002
        else:
            return 1
