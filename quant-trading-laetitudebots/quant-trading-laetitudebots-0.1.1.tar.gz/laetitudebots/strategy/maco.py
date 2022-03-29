from laetitudebots.util.talib_method import talib_method


def initialize(factors, config):
    per = config['parameters']['per']
    factors['per'] = talib_method(method='SMA', timeperiod = per, args = [factors.close])


def process_binance(window, assets, context):
    total_unrealised_pnl = sum([asset.position.unrealised_pnl for _, asset in assets.items()])
    total_balance = total_unrealised_pnl + context['balance']
    
    for symbol, asset in assets.items():
        position = asset.position
        last = window.latest(symbol)
        settings = context['assets'][symbol]  
            
        per = last.per
        close = last.close
          
        lg_ent = (close > per)  
        lg_ext = (close < per)

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
        print(f"Prev Per: {last.per}")
        print(f"Long Entry?: {lg_ent}")
        print(f"Long Exit?: {lg_ext}")
                
        if position.size == 0: 
            if lg_ent:
                pos_size = total_balance * settings['allocation']
                size = pos_size * asset.get_contract_rate(last.close)
                order = {
                    'type' : 'market',
                    'size' : size,
                    'side' : 'buy'
                }
                asset.create_order('l_entry', order)
                print("Order placed.")
                print(order)
                print("Asset: ", asset)
                print("Symbol: ", symbol)
                print("Last Bar Close: ", last.close)
           
        if position.size > 0 and lg_ext:
            size = abs(position.size)
            order = {
                'type' : 'market',
                'size' : size,
                'side' : 'sell'
            }
            asset.create_order('l_exit', order)
            print("close < per")
            print("Last Bar Close: ", last.close)
            print("Prev Per: ", last.per)