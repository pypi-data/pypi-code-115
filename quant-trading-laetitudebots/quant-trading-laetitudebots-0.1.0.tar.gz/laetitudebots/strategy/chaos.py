import numpy as np

from laetitudebots.util import custom_method
from laetitudebots.util.indicators import high_pivot, low_pivot
from laetitudebots.util.talib_method import talib_method


def initialize(factors, config):
    left_look_p = config['parameters']['left_look_p']
    right_look_p = config['parameters']['right_look_p']
    stop = config['parameters']['stop']
    lips = config['parameters']['lips']
    teeth = config['parameters']['teeth']
    jaw = config['parameters']['jaw']
    factors['p_high'] = factors.high
    factors['p_low'] = factors.low
    factors['high_pivot'] = custom_method(high_pivot,
                                          [factors.high, left_look_p,
                                           right_look_p])
    factors['low_pivot'] = custom_method(low_pivot,
                                         [factors.low, left_look_p,
                                          right_look_p])
    factors['avg_close'] = (factors.high + factors.low) / 2
    factors['stop'] = talib_method(method='SMA', timeperiod=stop,
                                   args=[factors.avg_close]).shift(2)
    factors['lips'] = factors.avg_close.ewm(alpha=1 / lips,
                                            adjust=True).mean().shift(3)
    factors['teeth'] = factors.avg_close.ewm(alpha=1 / teeth,
                                             adjust=True).mean().shift(5)
    factors['jaw'] = factors.avg_close.ewm(alpha=1 / jaw,
                                           adjust=True).mean().shift(8)


def process_bitmex(window, assets, context):

    total_unrealised_pnl = sum([asset.position.unrealised_pnl
                                for _, asset in assets.items()])
    total_balance = total_unrealised_pnl + context['balance']

    for symbol, asset in assets.items():
        position = asset.position
        last_bar = window.latest(symbol)
        if not np.all([last_bar.stop, last_bar.high_pivot,
                       last_bar.low_pivot]):
            continue
        settings = context['assets'][symbol]
        lg_ent = last_bar.lips > last_bar.teeth > last_bar.jaw
        st_ent = last_bar.lips < last_bar.teeth < last_bar.jaw

        print("WINDOW")
        print(window)   
        print(f"Window Latest - Timestamp: {last_bar.timestamp}")
        print(f"Window Latest - Open: {last_bar.open}")
        print(f"Window Latest - High: {last_bar.high}")
        print(f"Window Latest - Low: {last_bar.low}") 
        print(f"Window Latest - Close: {last_bar.close}")
        print(f"Window Latest - Volume: {last_bar.volume}")
        print("######## \n")

        print(f"Pair: {symbol}")
        print(f"Last Bar Close: {last_bar.close}")  ###
        print(f"Last Bar Stop : {last_bar.stop}")   ###
        print(f"Last Bar Lips : {last_bar.lips}")   ###
        print(f"Last Bar Teeth: {last_bar.teeth}")  ###
        print(f"Last Bar Jaw  : {last_bar.jaw} \n") ###
        print(f"Long Signal? {lg_ent}")             ###
        print(f"Short Signal? {st_ent}")            ###

        if position.size <= 0:
            # check if there's a short position or none
            if position.size == 0:
                print("No position")
            elif position.size < 0:
                print(f"Short position: {position.size}")

            if lg_ent:
                print(f"Long Signal? {lg_ent}") ###
                hp = last_bar.high_pivot
                print(f"Last High Fractal: {hp}") ###
                pos_size = total_balance * settings['allocation']

                size = (abs(position.size)
                        + pos_size * asset.get_contract_rate(hp))
                if hp > last_bar.close:
                    print("HP > Last Bar Close")
                    order = {
                        'order_type': 'stop',
                        'size': size,
                        'side': 'buy',
                        'trigger_price': hp
                    }
                # else:
                #     order = {
                #         'order_type': 'limit',
                #         'size': size,
                #         'side': 'buy',
                #         'price': hp
                #     }

                    asset.create_order('chaos_long', order)
                    print(f"Long Stop Order Placed: {order}") ###
            else:
                asset.cancel_order('chaos_long')
                print(f"Chaos Long order cancelled because lg_ent is {lg_ent}.") ###

            if position.size < 0:
                print(f"Short position: {position.size}") ###
                asset.cancel_order('chaos_short_exit')
                print("Short exit order cancelled because there's a new stop formed.") ###
                if last_bar.close > last_bar.stop:
                    print("Last Bar Close > Last Bar Stop") ###
                    # will market order on open, so if 'chaos_long' exists,
                    # remove the size attributed to this short position
                    order = {
                        'order_type': 'market',
                        'size': abs(position.size),
                        'side': 'buy'
                    }

                    if lg_ent:
                        print("Short and lg_ent?") ###
                        chaos_long = asset.orders.get('chaos_long')
                        print(f"Chaos long order exists?: {chaos_long}") ###
                        chaos_long['size'] -= abs(position.size)
                        asset.create_order('chaos_long', chaos_long)
                        print(f"Chaos long updated: {chaos_long}") ###
                    asset.create_order('chaos_short_exit', order)
                    print(f"Short Exit Market Order placed: {order}")
                else:
                    if last_bar.stop < last_bar.high_pivot and lg_ent:
                        # if stop < high pivot, check if chaos_long exists
                        # and remove the the size attributed to this position
                        # because stop will be hit first in the first place
                        chaos_long = asset.orders.get('chaos_long')
                        chaos_long['size'] -= abs(position.size)
                        asset.create_order('chaos_long', chaos_long)
                        print(f"Last Bar Stop < Last Bar High Pivot and lg_ent is {lg_ent}")
                        print(f"Chaos Long Order: {chaos_long}")
                    elif not lg_ent:
                        # if lg_ent is not triggered, post a buy order at stop
                        size = abs(position.size)
                        if last_bar.stop > last_bar.close:
                            print("Last bar Stop > Last bar Close.")
                            order = {
                                'order_type': 'stop',
                                'size': size,
                                'side': 'buy',
                                'trigger_price': last_bar.stop
                            }
                        # else:
                        #     order = {
                        #         'order_type': 'limit',
                        #         'size': size,
                        #         'side': 'buy',
                        #         'price': last_bar.stop
                        #     }
                            asset.create_order('chaos_short_exit', order)
                            print(f"Stop loss order placed: {order}")

        if position.size >= 0:  # long or no position
            # check if there's a long position or none
            if position.size == 0:
                print("No position")
            elif position.size > 0:
                print(f"Long position: {position.size}")

            if st_ent:
                print(f"Short Signal? {st_ent}")
                lp = last_bar.low_pivot
                print(f"Last Low Fractal: {lp}")
                pos_size = total_balance * settings['allocation']

                size = (abs(position.size)
                        + pos_size * asset.get_contract_rate(lp))
                if lp > last_bar.close:
                    pass
                    # order = {
                    #     'order_type': 'limit',
                    #     'size': size,
                    #     'side': 'sell',
                    #     'price': lp
                    # }
                else:
                    print(f"Low Pivot < Last Bar Close? {lp < last_bar.close}")
                    order = {
                        'order_type': 'stop',
                        'size': size,
                        'side': 'sell',
                        'trigger_price': lp
                    }

                    asset.create_order('chaos_short', order)
                    print(f"Short Stop Order Placed: {order}")
            else:
                asset.cancel_order('chaos_short')
                print(f"Chaos Short order cancelled because st_ent is {st_ent}")

            if position.size > 0:
                print(f"Long position: {position.size}")
                asset.cancel_order('chaos_long_exit')
                print("Long order cancelled because there's a new stop formed.")
                if last_bar.close < last_bar.stop:
                    print("Last bar Close < Last Bar Stop")
                    # will market order on open, so if 'chaos_short' exists,
                    # remove the size attributed to this long position
                    order = {
                        'order_type': 'market',
                        'size': abs(position.size),
                        'side': 'sell'
                    }

                    if st_ent:
                        print("Long and st_ent?")
                        chaos_short = asset.orders.get('chaos_short')
                        print(f"Chaos short order exists?: {chaos_short}")
                        chaos_short['size'] -= abs(position.size)
                        asset.create_order('chaos_short', chaos_short)
                        print(f"Chaos short updated: {chaos_short}")
                    asset.create_order('chaos_long_exit', order)
                    print(f"Long Exit Market Order placed: {order}")
                else:
                    if last_bar.stop > last_bar.low_pivot and st_ent:
                        # if stop > low pivot, remove the the size attributed
                        # to this position because stop will be hit first
                        # in the first place
                        chaos_short = asset.orders.get('chaos_short')
                        chaos_short['size'] -= abs(position.size)
                        asset.create_order('chaos_short', chaos_short)
                        print(f"Last Bar Stop > Last Bar Low Pivot and st_ent is {st_ent}")
                        print(f"Chaos Short Order: {chaos_short}")
                    elif not st_ent:
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
                            print("Last bar Stop < Last bar Close.")
                            order = {
                                'order_type': 'stop',
                                'size': size,
                                'side': 'sell',
                                'trigger_price': last_bar.stop
                            }
                            asset.create_order('chaos_long_exit', order)
                            print(f"Stop loss order placed: {order}")


# this is needed because FTX works with a collateral system
# In the future, we should be able to know what exchange the strategy
# is being applied to in the context
def process_ftx(window, assets, context):
    total_unrealised_pnl = sum([asset.position.unrealised_pnl
                                for _, asset in assets.items()])
    total_balance = total_unrealised_pnl + context['balance']

    for symbol, asset in assets.items():
        position = asset.position
        last_bar = window.latest(symbol)
        if not np.all([last_bar.stop, last_bar.high_pivot,
                       last_bar.low_pivot]):
            continue
        settings = context['assets'][symbol]
        lg_ent = last_bar.lips > last_bar.teeth > last_bar.jaw
        st_ent = last_bar.lips < last_bar.teeth < last_bar.jaw

        print("WINDOW")
        print(window)   
        print(f"Window Latest - Timestamp: {last_bar.timestamp}")
        print(f"Window Latest - Open: {last_bar.open}")
        print(f"Window Latest - High: {last_bar.high}")
        print(f"Window Latest - Low: {last_bar.low}") 
        print(f"Window Latest - Close: {last_bar.close}")
        print(f"Window Latest - Volume: {last_bar.volume}")
        print("######## \n")

        print(f"Pair: {symbol}")
        print(f"Last Bar Close: {last_bar.close}")  ###
        print(f"Last Bar Stop : {last_bar.stop}")   ###
        print(f"Last Bar Lips : {last_bar.lips}")   ###
        print(f"Last Bar Teeth: {last_bar.teeth}")  ###
        print(f"Last Bar Jaw  : {last_bar.jaw} \n") ###
        print(f"Long Signal? {lg_ent}")             ###
        print(f"Short Signal? {st_ent}")            ###
        
        if position.size <= 0:
            # check if there's a short position or none
            if position.size == 0:
                print("No position")
            elif position.size < 0:
                print(f"Short position: {position.size}")

            if lg_ent:
                print(f"Long Signal? {lg_ent}") ###
                hp = last_bar.high_pivot
                print(f"Last High Fractal: {hp}") ###
                pos_size = total_balance * settings['allocation']

                size = (abs(position.size)
                        + pos_size
                        * asset.get_contract_rate(hp, last_bar.collateral))

                if hp > last_bar.close:
                    print("HP > Last Bar Close")
                    order = {
                        'order_type': 'stop',
                        'size': size,
                        'side': 'buy',
                        'trigger_price': hp
                    }
                # else:
                #     order = {
                #         'order_type': 'limit',
                #         'size': size,
                #         'side': 'buy',
                #         'price': hp
                #     }

                    asset.create_order('chaos_long', order)
                    print(f"Long Stop Order Placed: {order}") ###
            else:
                asset.cancel_order('chaos_long')
                print(f"Chaos Long order cancelled because lg_ent is {lg_ent}.")

            if position.size < 0:
                print(f"Short position: {position.size}") ###
                asset.cancel_order('chaos_short_exit')
                print("Short exit order cancelled because there's a new stop formed.") ###
                if last_bar.close > last_bar.stop:
                    print("Last Bar Close > Last Bar Stop") ###
                    # will market order on open, so if 'chaos_long' exists,
                    # remove the size attributed to this short position
                    order = {
                        'order_type': 'market',
                        'size': abs(position.size),
                        'side': 'buy'
                    }
                    if lg_ent:
                        print("Short and lg_ent?") ###
                        chaos_long = asset.orders.get('chaos_long')
                        print(f"Chaos long order exists?: {chaos_long}") ###
                        chaos_long['size'] -= abs(position.size)
                        asset.create_order('chaos_long', chaos_long)
                        print(f"Chaos long updated: {chaos_long}") ###
                    asset.create_order('chaos_short_exit', order)
                    print(f"Short Exit Market Order placed: {order}")
                else:
                    if last_bar.stop < last_bar.high_pivot and lg_ent:
                        # if stop < high pivot, check if chaos_long exists
                        # and remove the the size attributed to this position
                        # because stop will be hit first in the first place
                        chaos_long = asset.orders.get('chaos_long')
                        chaos_long['size'] -= abs(position.size)
                        asset.create_order('chaos_long', chaos_long)
                        print(f"Last Bar Stop < Last Bar High Pivot and lg_ent is {lg_ent}")
                        print(f"Chaos Long Order: {chaos_long}")
                    elif not lg_ent:
                        # if lg_ent is not triggered, post a buy order at stop
                        size = abs(position.size)
                        if last_bar.stop > last_bar.close:
                            print("Last bar Stop > Last bar Close.")
                            order = {
                                'order_type': 'stop',
                                'size': size,
                                'side': 'buy',
                                'trigger_price': last_bar.stop
                            }
                        # else:
                        #     order = {
                        #         'order_type': 'limit',
                        #         'size': size,
                        #         'side': 'buy',
                        #         'price': last_bar.stop
                        #     }
                            asset.create_order('chaos_short_exit', order)
                            print(f"Stop loss order placed: {order}")

        if position.size >= 0:  # long or no position
            # check if there's a long position or none
            if position.size == 0:
                print("No position")
            elif position.size > 0:
                print(f"Long position: {position.size}")

            if st_ent:
                print(f"Short Signal? {st_ent}")
                lp = last_bar.low_pivot
                print(f"Last Low Fractal: {lp}")
                pos_size = total_balance * settings['allocation']

                size = (abs(position.size)
                        + pos_size
                        * asset.get_contract_rate(lp, last_bar.collateral))
                if lp > last_bar.close:
                    pass
                    # order = {
                    #     'order_type': 'limit',
                    #     'size': size,
                    #     'side': 'sell',
                    #     'price': lp
                    # }
                else:
                    print(f"Low Pivot < Last Bar Close? {lp < last_bar.close}")
                    order = {
                        'order_type': 'stop',
                        'size': size,
                        'side': 'sell',
                        'trigger_price': lp
                    }

                    asset.create_order('chaos_short', order)
                    print(f"Short Stop Order Placed: {order}")
            else:
                asset.cancel_order('chaos_short')
                print(f"Chaos Short order cancelled because st_ent is {st_ent}")

            if position.size > 0:
                print(f"Long position: {position.size}")
                asset.cancel_order('chaos_long_exit')
                print("Long order cancelled because there's a new stop formed.")
                if last_bar.close < last_bar.stop:
                    print("Last bar Close < Last Bar Stop")
                    # will market order on open, so if 'chaos_short' exists,
                    # remove the size attributed to this long position
                    order = {
                        'order_type': 'market',
                        'size': abs(position.size),
                        'side': 'sell'
                    }

                    if st_ent:
                        print("Long and st_ent?")
                        chaos_short = asset.orders.get('chaos_short')
                        print(f"Chaos short order exists?: {chaos_short}")
                        chaos_short['size'] -= abs(position.size)
                        asset.create_order('chaos_short', chaos_short)
                        print(f"Chaos short updated: {chaos_short}")
                    asset.create_order('chaos_long_exit', order)
                    print(f"Long Exit Market Order placed: {order}")
                else:
                    if last_bar.stop > last_bar.low_pivot and st_ent:
                        # if stop > low pivot, remove the the size attributed
                        # to this position because stop will be hit first
                        # in the first place
                        chaos_short = asset.orders.get('chaos_short')
                        chaos_short['size'] -= abs(position.size)
                        asset.create_order('chaos_short', chaos_short)
                        print(f"Last Bar Stop > Last Bar Low Pivot and st_ent is {st_ent}")
                        print(f"Chaos Short Order: {chaos_short}")
                    elif not st_ent:
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
                            print("Last bar Stop < Last bar Close.")
                            order = {
                                'order_type': 'stop',
                                'size': size,
                                'side': 'sell',
                                'trigger_price': last_bar.stop
                            }
                            asset.create_order('chaos_long_exit', order)
                            print(f"Stop loss order placed: {order}")
