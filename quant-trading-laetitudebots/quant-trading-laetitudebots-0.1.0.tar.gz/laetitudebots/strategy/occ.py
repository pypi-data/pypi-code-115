from laetitudebots.util.talib_method import talib_method


def initialize(factors, config):
    per = config['parameters']['per']
       
    factors['cse'] = talib_method(method='DEMA', timeperiod = per, args = [factors.close])
    factors['ose'] = talib_method(method='DEMA', timeperiod = per, args = [factors.open])
    factors['rsi'] = talib_method(method='RSI', timeperiod = 14, args = [factors.close]) 


def process_bitmex(window, assets, context):
    total_unrealised_pnl = sum([asset.position.unrealised_pnl for _, asset in assets.items()])
    total_balance = total_unrealised_pnl + context['balance']
    
    for symbol, asset in assets.items():
        position = asset.position
        last = window.latest(symbol)
        settings = context['assets'][symbol]  
            
        cse = last.cse
        ose = last.ose
        rsi = last.rsi
            
        lg_ent = (cse > ose) and (rsi >= 60)
        st_ent = (cse < ose) and (rsi <= 40)

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
        print(f"Prev CSE: {last.cse}, Prev OSE: {last.ose}, Prev RSI: {last.rsi} ")
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
            asset.create_order('occ_long', order)
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
            asset.create_order('occ_short', order)
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
            
        cse = last.cse
        ose = last.ose
        rsi = last.rsi
            
        lg_ent = (cse > ose) and (rsi >=60)
        st_ent = (cse < ose) and (rsi <= 40)

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
        print(f"Prev CSE: {last.cse}, Prev OSE: {last.ose}, Prev RSI: {last.rsi} ")
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
            asset.create_order('occ_long', order)
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
            asset.create_order('occ_short', order)
            print("Order placed.")
            print(order)
            print("Asset: ", asset)
            print("Symbol: ", symbol)
            print("Last Bar Close: ", last.close)