import numpy as np

from laetitudebots.util import custom_method
from laetitudebots.util.indicators import high_pivot
from laetitudebots.util.indicators import low_pivot
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

        pos_size = total_balance * settings['allocation']
        
        if position.size == 0:
            print(f"No position yet on {symbol}")
            if lg_ent:               
              
                hp = last_bar.high_pivot
                                
                size = pos_size * asset.get_contract_rate(hp)
                
                # if short order hasn't been hit
                # and ma's are aligned for long entry,
                # cancel short entry order if it exists
                if asset.orders.get('chaos_short_entry'):
                    asset.cancel_order('chaos_short_entry')
                    print("Long Signal. Short order cancelled.")
                
                # if high pivot is still higher than
                # the close of the last bar, place
                # stop market order           
                if hp > last_bar.close:
                    # if there's no previous long entry order,
                    # place long stop market order
                    if not asset.orders.get('chaos_long_entry'):
                        order = {
                            'order_type': 'stop',
                            'size': size,
                            'side': 'buy',
                            'trigger_price': hp
                        }
                        asset.create_order('chaos_long_entry', order)
                        print(f"Long order placed at {hp}")
                            
                    # if a long entry order has been
                    # previously placed and a new (lower) 
                    # hp forms, cancel the previous order
                    # and place new order
                    if (asset.orders.get('chaos_long_entry') and
                        (asset.orders.get('chaos_long_entry').get('trigger_price') > hp)
                       ):
                        asset.cancel_order('chaos_long_entry')
                        order = {
                            'order_type': 'stop',
                            'size': size,
                            'side': 'buy',
                            'trigger_price': hp
                        }
                        asset.create_order('chaos_long_entry', order)
                        print(f"Lower HP formed. Previous order cancelled. New one placed at {hp}.")
                
                # if in case price gaps up and previous order
                # was not hit, market order upon open
                if hp < last_bar.close:
                    # if previous long entry was not hit
                    # cancel order
                    if asset.orders.get('chaos_long_entry'):
                        asset.cancel_order('chaos_long_entry')
                        print(f"HP < close. Long order cancelled.")
                        
                    order = {
                        'order_type': 'market',
                        'size': size,
                        'side': 'buy'
                    }
                    asset.create_order('chaos_long_entry', order)
                    print(f"Market buy at {last_bar.close}")
               
            if st_ent:
                
                # if long order hasn't been hit
                # and ma's are aligned for short entry,
                # cancel long entry order if it exists
                if asset.orders.get('chaos_long_entry'):
                    asset.cancel_order('chaos_long_entry')
                    print("Short signal. Long order cancelled.")
                
                lp = last_bar.low_pivot
                
                size = pos_size * asset.get_contract_rate(lp)
                
                # if low pivot is still below
                # the close of the last bar,
                # place stop market order
                if lp < last_bar.close:
                    
                    # if there's no previous short order placed,
                    # place stop market order
                    if not asset.orders.get('chaos_short_entry'):
                        order = {
                            'order_type': 'stop',
                            'size': size,
                            'side': 'sell',
                            'trigger_price': lp
                        }
                        asset.create_order('chaos_short_entry', order)
                        print(f"Short order placed at {lp}")
                    
                    # if a short entry order has been
                    # previously placed and a new (higher) 
                    # lp forms, cancel the previous order
                    # and place new order
                    if (asset.orders.get('chaos_short_entry') and
                        (asset.orders.get('chaos_short_entry').get('trigger_price') < lp)
                       ):
                        asset.cancel_order('chaos_short_entry')
                        order = {
                            'order_type': 'stop',
                            'size': size,
                            'side': 'sell',
                            'trigger_price': lp
                        }
                        asset.create_order('chaos_short_entry', order)
                        print(f"Higher LP formed. Previous order cancelled. New one placed at {lp}.")                 
                    
                # if in case price gaps down and
                # previous order is not hit, 
                # market order upon open
                if lp > last_bar.close:
                    # if previous short entry was not hit
                    # cancel order
                    if asset.orders.get('chaos_short_entry'):
                        asset.cancel_order('chaos_short_entry')
                        print(f"LP > close. Short order cancelled.")
                    
                    order = {
                        'order_type': 'market',
                        'size': size,
                        'side': 'sell'
                    }
                    asset.create_order('chaos_short_entry', order)
                    print(f"Market sell at {last_bar.close}")

            # if MAs are not aligned for long signal
            # and there's a pending order, cancel long order
            if not lg_ent and asset.orders.get('chaos_long_entry'):
                asset.cancel_order('chaos_long_entry')
                print('MAs not aligned. Long order cancelled.')   

            # if MAs are not aligned for short signal
            # and there's a pending order, cancel short order
            if not st_ent and asset.orders.get('chaos_short_entry'):
                asset.cancel_order('chaos_short_entry')
                print("MAs not aligned. Short order cancelled.")
        
        if position.size > 0:
            if last_bar.close <= last_bar.stop:
                size = abs(position.size)
                order = {
                    'order_type': 'market',
                    'size': size,
                    'side': 'sell',
                }
                asset.create_order('chaos_long_exit', order)
                print(f"Long stop hit. Position exited.")

        if position.size < 0:
            if last_bar.close >= last_bar.stop:
                size = abs(position.size)
                order = {
                    'order_type': 'market',
                    'size': size,
                    'side': 'buy',
                }
                asset.create_order('chaos_short_exit', order)
                print(f"Short stop hit. Position exited.")
                