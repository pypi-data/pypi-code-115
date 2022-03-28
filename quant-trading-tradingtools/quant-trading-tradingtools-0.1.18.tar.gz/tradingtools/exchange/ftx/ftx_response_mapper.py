# -*- coding: utf-8 -*-


class FTXResponseMapper:
    @staticmethod
    def map_balance_response(balance: dict) -> dict:
        return {
            'asset': balance['coin'],
            'available': balance['free'],
            'total': balance['total'],
        }

    @staticmethod
    def map_order_response(order: dict) -> dict:
        return {
            'created_at': order['createdAt'],
            'id': order['id'],
            'symbol': order['future'],
            'type': order['type'],
            'order_type': order['type'],
            'side': order['side'],
            'size': order['size'],
            'price': order.get('price', order.get('orderPrice')),
            'trigger_price': order.get('triggerPrice'),
            'filled_size': order.get('filledSize'),
            'remaining_size': order.get('remainingSize'),
            'status': order['status'],
            'reduce_only': order['reduceOnly'],
            'ioc': order.get('ioc'),
            'post_only': order.get('postOnly'),
            'retry_until_filled': order.get('retryUntilFilled'),
        }

    @staticmethod
    def map_position_response(
        position: dict,
        tickers,
        collateral_symbol: str = None,
        round_pnl: int = 8,
    ) -> dict:
        if position['side'] == 'buy':
            position_current_price = tickers[position['future']]['info']['bid']
        else:
            position_current_price = tickers[position['future']]['info']['ask']

        unrealized_usd_pnl = (
            position_current_price * position['netSize'] - position['cost']
        )

        if collateral_symbol:
            collateral_price = tickers[collateral_symbol]['info']['ask']
            unrealized_pnl = unrealized_usd_pnl / collateral_price
        else:
            unrealized_pnl = unrealized_usd_pnl

        return {
            'symbol': position['future'],
            'side': position['side'],
            'size': position['netSize'],
            'avg_price': position['entryPrice'],
            'unrealized_pnl': round(unrealized_pnl, round_pnl),
        }
