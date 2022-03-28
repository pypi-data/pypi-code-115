# -*- coding: utf-8 -*-

__all__ = ['DeribitResponseMapper']


class DeribitResponseMapper:
    @staticmethod
    def map_auth_response(auth):
        return {
            'access_token': auth['access_token'],
            'expires_in': auth['expires_in'],
            'refresh_token': auth['refresh_token'],
            'scope': auth['scope'],
            'token': auth['token'],
        }

    @staticmethod
    def map_balance_response(balance):
        return {
            'asset': balance['currency'],
            'available': balance['available_funds'],
            'total': balance['balance'],
        }

    @staticmethod
    def map_order_response(order):
        return {
            'created_at': order['creation_timestamp'],
            'id': order['order_id'],
            'symbol': order['instrument_name'],
            'type': order['order_type'],
            'order_type': order.get('original_order_type'),
            'side': order['direction'],
            'size': order['amount'],
            'price': order['price'],
            'trigger_price': order.get('stop_price'),
            'filled_size': order['filled_amount'],
            'remaining_size': order['amount'] - order['filled_amount'],
            'status': order['order_state'],
            'reduce_only': order.get('reduce_only'),
            'post_only': order.get('post_only'),
            'retry_until_filled': order.get('retryUntilFilled'),
            # deribit specific fields
            'average_price': order['average_price'],
            'profit_loss': order['profit_loss'],
            'commission': order['commission'],
            'time_in_force': order['time_in_force'],
            'trigger': order.get('trigger'),
            'api': order['api'],
            'web': order.get('web'),
            'advanced': order.get('advanced'),
            'triggered': order.get('triggered'),
            'block_trade': order.get('block_trade'),
            'auto_replaced': order.get('auto_replaced'),
            'stop_order_id': order.get('stop_order_id'),
            'replaced': order['replaced'],
            'app_name': order.get('app_name'),
            'label': order.get('label'),
            'is_liquidation': order.get('is_liquidation'),
            'usd': order.get('usd'),
            'implv': order.get('implv'),
        }

    @staticmethod
    def map_position_response(position) -> dict:
        return {
            'symbol': position['instrument_name'],
            'side': position['direction'],
            'size': position['size'],
            'avg_price': position['average_price'],
            'unrealized_pnl': position['floating_profit_loss'],
            # anything below is specific to Deribit
            'realized_funding': position.get('realized_funding'),  # for perps
            'size_currency': position.get('size_currency'),  # for future
            'avg_price_usd': position.get('average_price_usd'),  # for option
            'delta': position['delta'],
            'unrealized_pnl_usd': position.get('floating_profit_loss_usd'),
            'gamma': position.get('gamma'),
            'kind': position['kind'],
            'leverage': position.get('leverage'),
            'initial_margin': position['initial_margin'],
            'maintenance_margin': position['maintenance_margin'],
            'realized_pnl': position['realized_profit_loss'],
            'total_pnl': position['total_profit_loss'],
            'theta': position.get('theta'),
            'vega': position.get('vega'),
        }
