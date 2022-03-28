# -*- coding: utf-8 -*-


class BinanceResponseMapper:
    @staticmethod
    def map_balance_response(balance: dict) -> dict:
        return {
            'asset': balance['asset'],
            'available': float(balance['free']),
            'total': float(balance['free']) + float(balance['locked'])
        }

    @staticmethod
    def map_order_response(order: dict) -> dict:
        return {
            'created_at': order['timestamp'],
            'id': order['id'],
            'symbol': order['symbol'],
            'type': order['type'],
            'order_type': order['type'],
            'side': order['side'],
            'size': order['amount'],
            'price': order.get('price'),
            'trigger_price': float(order['info'].get('stopPrice', 'nan')),
            'filled_size': order.get('filled'),
            'remaining_size': order.get('remaining'),
            'status': order['status'],
        }

    @staticmethod
    def map_position_response(
        position: dict,
        tickers,
        collateral_symbol: str = None,
        round_pnl: int = 8,
    ) -> dict:
        # no need yet for a spot trading account
        pass
