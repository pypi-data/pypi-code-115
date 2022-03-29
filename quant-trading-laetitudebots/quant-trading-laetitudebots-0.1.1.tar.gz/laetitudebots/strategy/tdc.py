import talib

from laetitudebots.util import custom_method
from laetitudebots.util.talib_method import talib_method

def initialize(factors, config):
    band = config['parameters']['band']
    keltner = config['parameters']['keltner']
    per = config['parameters']['per']
    
    factors['high'] = factors.high.ffill()
    factors['low'] = factors.low.ffill()
    factors['close'] = factors.close.ffill()
    factors['psar'] = custom_method(talib.SAR, [factors.high, factors.low, 0.02, 0.2])
    factors['bb'] = talib_method(method='SMA', timeperiod=band, args = [factors.close])
    factors['keltner'] = talib_method(method='EMA', timeperiod =keltner, args = [factors.close])    
    factors['ma1'] = talib_method(method='EMA', timeperiod = per, args = [factors.close])
    factors['ma2'] = talib_method(method='EMA', timeperiod = per, args = [factors.ma1])

def process_bitmex(window, assets, context):
    total_unrealised_pnl = sum([asset.position.unrealised_pnl for _, asset in assets.items()])
    total_balance = total_unrealised_pnl + context['balance']
        
    for symbol, asset in assets.items():
        position = asset.position
        last = window.latest(symbol)
        settings = context['assets'][symbol]  
            
        keltner = last.keltner
        bb = last.bb
        ma2 = last.ma2
        close = last.close
        psar = last.psar
                    
        lg_ent = (keltner > bb) and (ma2 < close > psar)
        st_ent = (keltner < bb) and (ma2 > close < psar)

        print("WINDOW")
        print(window)   
        print(window.latest(symbol))
        print("########")
        print(f"Window Latest - Timestamp: {last.timestamp}")
        print(f"Window Latest - Open: {last.open}")
        print(f"Window Latest - High: {last.high}")
        print(f"Window Latest - Low: {last.low}") 
        print(f"Window Latest - Close: {last.close}")
        print(f"Window Latest - Volume: {last.volume}")
        print("######## \n")

        print(f"Pair: {symbol}")
        print(f"Last Bar Close: ", {last.close})
        print(f"Prev Keltner: {last.keltner}, Prev BB: {last.bb}, Prev MA2: {last.ma2}, Prev PSAR: {last.psar} ")
        print(f"Long Entry?: {lg_ent}")
        print(f"Short Entry?: {st_ent}")
            
        if position.size <= 0 and lg_ent:
            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(last.close)
            order = {
                    'order_type': 'market',
                    'size': size,
                    'side': 'buy'
                    }
            asset.create_order('tdc_long', order)
            print("Order placed.")
            print(order)
            print("Asset: ", asset)
            print("Symbol: ", symbol)
            print("Last Bar Close: ", last.close)
                
        elif position.size >= 0 and st_ent:
            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(last.close)
            order = {
                    'order_type': 'market',
                    'size': size,
                    'side': 'sell'
                    }
            asset.create_order('tdc_short', order)
            print("Order placed.")
            print(order)
            print("Asset: ", asset)
            print("Symbol: ", symbol)
            print("Last Bar Close: ", last.close)


def process_ftx(window, assets, context):
    total_unrealised_pnl = sum([asset.position.unrealised_pnl for _, asset in assets.items()])
    total_balance = total_unrealised_pnl + context['balance']
    
    for symbol, asset in assets.items():
        position = asset.position
        last = window.latest(symbol)
        settings = context['assets'][symbol]  
            
        keltner = last.keltner
        bb = last.bb
        ma2 = last.ma2
        close = last.close
        psar = last.psar
        
        lg_ent = (keltner > bb) and (ma2 < close > psar)
        st_ent = (keltner < bb) and (ma2 > close < psar)

        print("WINDOW")
        print(window)   
        print(window.latest(symbol))
        print("########")
        print(f"Window Latest - Timestamp: {last.timestamp}")
        print(f"Window Latest - Open: {last.open}")
        print(f"Window Latest - High: {last.high}")
        print(f"Window Latest - Low: {last.low}") 
        print(f"Window Latest - Close: {last.close}")
        print(f"Window Latest - Volume: {last.volume}")
        print("######## \n")

        print(f"Pair: {symbol}")
        print(f"Last Bar Close: ", {last.close})
        print(f"Prev Keltner: {last.keltner}, Prev BB: {last.bb}, Prev MA2: {last.ma2}, Prev PSAR: {last.psar} ")
        print(f"Long Entry?: {lg_ent}")
        print(f"Short Entry?: {st_ent}")
            
        if position.size <= 0 and lg_ent:
            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(last.close, last.collateral)
            order = {
                    'order_type': 'market',
                    'size': size,
                    'side': 'buy'
                    }
            asset.create_order('tdc_long', order)
            print("Order placed.")
            print(order)
            print("Asset: ", asset)
            print("Symbol: ", symbol)
            print("Last Bar Close: ", last.close)
                
        elif position.size >= 0 and st_ent:
            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(last.close, last.collateral)
            order = {
                    'order_type': 'market',
                    'size': size,
                    'side': 'sell'
                    }
            asset.create_order('tdc_short', order)
            print("Order placed.")
            print(order)
            print("Asset: ", asset)
            print("Symbol: ", symbol)
            print("Last Bar Close: ", last.close)                   