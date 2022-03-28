import numpy as np

from laetitudebots.util import custom_method
from laetitudebots.util.indicators import high_pivot, low_pivot
from laetitudebots.util.talib_method import talib_method


def read_data(initialize, process_binance):
    return initialize_data + process_binance_order


def initialize(factors, config):
    left_look_p = config['parameters']['left_look_p']
    right_look_p = config['parameters']['right_look_p']
    stop = config['parameters']['stop']
    lips = config['parameters']['lips']
    teeth = config['parameters']['teeth']
    jaw = config['parameters']['jaw']
    factors['p_high'] = factors.high
    factors['p_low'] = factors.low
    factors['high_pivot'] = custom_method(
        high_pivot, [factors.high, left_look_p, right_look_p]
    )
    factors['low_pivot'] = custom_method(
        low_pivot, [factors.low, left_look_p, right_look_p]
    )
    factors['avg_close'] = (factors.high + factors.low) / 2
    factors['stop'] = talib_method(
        method='SMA', timeperiod=stop, args=[factors.avg_close]
    ).shift(2)
    factors['lips'] = (
        factors.avg_close.ewm(alpha=1 / lips, adjust=True).mean().shift(3)
    )
    factors['teeth'] = (
        factors.avg_close.ewm(alpha=1 / teeth, adjust=True).mean().shift(5)
    )
    factors['jaw'] = (
        factors.avg_close.ewm(alpha=1 / jaw, adjust=True).mean().shift(8)
    )

    print(f"Lips: {factors['lips'].iloc[-2:]}")
    print(f"Jaw: {factors['jaw'].iloc[-2:]}")
    print(f"Teeth: {factors['teeth'].iloc[-2:]}")


def process_binance(window, assets, context):

    total_unrealised_pnl = sum(
        [asset.position.unrealised_pnl for _, asset in assets.items()]
    )
    total_balance = total_unrealised_pnl + context['balance']

    for symbol, asset in assets.items():
        print(f'Symbol: {symbol}')

        position = asset.position
        last_bar = window.latest(symbol)
        if not np.all(
            [last_bar.stop, last_bar.high_pivot, last_bar.low_pivot]
        ):
            continue
        settings = context['assets'][symbol]
        lg_ent = last_bar.lips > last_bar.teeth > last_bar.jaw
        st_ent = last_bar.lips < last_bar.teeth < last_bar.jaw

        pos_size = total_balance * settings['allocation']
        hp = last_bar.high_pivot
        size = abs(position.size) + pos_size * asset.get_contract_rate(hp)
        print(f'Last Bar Lips {last_bar.lips}')
        print(f'Last Bar Teeth {last_bar.teeth}')
        print(f'Last Bar Jaw {last_bar.jaw}')

        if position.size < (size * 0.5):
            if lg_ent:

                # hp = last_bar.high_pivot
                # pos_size = total_balance * (1/len(assets))
                # pos_size = total_balance * settings['allocation']

                if hp > last_bar.close:

                    order = {
                        'order_type': 'stop_loss_limit',
                        'trigger_price': hp,
                        'size': size - position.size,
                        'side': 'buy',
                        'price': hp * 1.05,
                    }

                    asset.create_order('chaos_long', order)

            else:
                asset.cancel_order('chaos_long')

        if position.size > (size * 0.5):

            asset.cancel_order('chaos_long_exit')

            if last_bar.close < last_bar.stop:
                # will market order on open, so if 'chaos_short' exists,
                # remove the size attributed to this long position
                order = {
                    'order_type': 'market',
                    'size': abs(position.size),
                    'side': 'sell',
                }

                asset.create_order('chaos_long_exit', order)

            else:
                #                 if last_bar.stop > last_bar.low_pivot and st_ent:
                #                     # if stop > low pivot, remove the the size attributed
                #                     # to this position because stop will be hit first
                #                     # in the first place
                #                     chaos_short = asset.orders.get('chaos_short')
                #                     chaos_short['size'] -= abs(position.size)
                #                     asset.create_order('chaos_short', chaos_short)
                if not st_ent:
                    # if st_ent is not triggered, post a sell order at stop
                    size = abs(position.size)
                    if last_bar.stop > last_bar.close:
                        pass
                        # order = {
                        #     'order_type': 'limit',
                        #     'size': size,
                        #     'side': 'sell',
                        #     'price': last_bar.stop
                        # }
                    else:
                        order = {
                            'order_type': 'stop_loss_limit',
                            'trigger_price': last_bar.stop,
                            'size': size,
                            'side': 'sell',
                            'price': last_bar.stop * 0.95,
                        }
                        asset.create_order('chaos_long_exit', order)

