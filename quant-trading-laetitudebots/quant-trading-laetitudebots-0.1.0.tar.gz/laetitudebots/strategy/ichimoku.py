from laetitudebots.util.talib_method import talib_method


def initialize(factors, config):
    tenkansenp = config['parameters']['tenkansenp']
    kijunsenp = config['parameters']['kijunsenp']
    senkouspanbp = 52 
    senkouspanlag = 26        
    
    #tenkansen 
    factors['tkph'] = factors.high.rolling(tenkansenp).max()
    factors['tkpl'] = factors.low.rolling(tenkansenp).min()
    factors['tenkan_sen'] = (factors.tkph + factors.tkpl) / 2
    
    #kijunsen
    factors['kjph'] = factors.high.rolling(kijunsenp).max()
    factors['kjpl'] = factors.low.rolling(kijunsenp).min()
    factors['kijun_sen'] = (factors.kjph + factors.kjpl) / 2
    
    #senkouspan
    factors['senkou_span_a'] = ((factors.tenkan_sen + factors.kijun_sen) / 2).shift(senkouspanlag) #leadingspan_a
    factors['sksbph'] = factors.high.rolling(senkouspanbp).max()
    factors['sksbpl'] = factors.low.rolling(senkouspanbp).min()
    factors['senkou_span_b'] = ((factors.sksbph + factors.sksbpl) / 2).shift(senkouspanlag) #leadingspan_b


def process_bitmex(window, assets, context):
    total_unrealised_pnl = sum([asset.position.unrealised_pnl for _, asset in assets.items()])
    total_balance = total_unrealised_pnl + context['balance']
    
    for symbol, asset in assets.items():
        position = asset.position
        last = window.latest(symbol)
        lastlast = window.previous(symbol, 2)
        settings = context['assets'][symbol]   
        
        lg_ent = ((last.close > last.kijun_sen) and (last.senkou_span_a < last.close > last.senkou_span_b))    
        lg_ext = (last.tenkan_sen < last.kijun_sen)   
        st_ent = ((last.close < last.kijun_sen) and (last.senkou_span_a > last.close < last.senkou_span_b))
        st_ext = (last.tenkan_sen > last.kijun_sen)  

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
        print(f"last tenkansen: {last.tenkan_sen}, last kijunsen: {last.kijun_sen}, last senkouspana: {last.senkou_span_a}, last senkouspanb: {last.senkou_span_b} ")
        print(f"Long Entry?: {lg_ent}")
        print(f"Short Entry?: {st_ent}")
        print(f"Long Exit?: {lg_ext}")
        print(f"Short Exit?: {st_ext}")
        
        if position.size == 0: 
            if lg_ent:
                pos_size = total_balance * settings['allocation']
                size = pos_size * asset.get_contract_rate(last.close)
                order = {
                    'order_type' : 'market',
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
                'order_type' : 'market',
                'size' : size,
                'side' : 'sell'
            }
            asset.create_order('l_exit', order)
            print("tenkansen < kijunsen")
            print("Last tenkansen: ", last.tenkan_sen) 
            print("Last kijunsen: ", last.kijun_sen) 
            
        if position.size == 0: 
            if st_ent:
                pos_size = total_balance * settings['allocation']
                size = pos_size * asset.get_contract_rate(last.close)
                order = {
                    'order_type' : 'market',
                    'size' : size,
                    'side' : 'sell'
                }
                asset.create_order('s_entry', order)
                print("Order placed.")
                print(order)
                print("Asset: ", asset)
                print("Symbol: ", symbol)
                print("Last Bar Close: ", last.close)
                
                
        if position.size < 0 and st_ext:
            size = abs(position.size) 
            order = {
                'order_type' : 'market',          
                'size' : size,
                'side' : 'buy'                    
                }
            asset.create_order('s_exit', order)
            print("tenkansen > kijunsen")
            print("Last tenkansen: ", last.tenkan_sen) 
            print("Last kijunsen: ", last.kijun_sen)


def process_binance(window, assets, context):
    total_unrealised_pnl = sum([asset.position.unrealised_pnl for _, asset in assets.items()])
    total_balance = total_unrealised_pnl + context['balance']
    
    for symbol, asset in assets.items():
        position = asset.position
        last = window.latest(symbol)
        lastlast = window.previous(symbol, 2)
        settings = context['assets'][symbol]  
          
        lg_ent = (last.close > last.tenkan_sen > last.kijun_sen > last.senkou_span_a > last.senkou_span_b)
        lg_ext = (lastlast.tenkan_sen > lastlast.kijun_sen and last.tenkan_sen < last.kijun_sen)

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
        print(f"last tenkansen: {last.tenkan_sen}, last kijunsen: {last.kijun_sen}, last senkouspana: {last.senkou_span_a}, last senkouspanb: {last.senkou_span_b} ")
        print(f"last last tenkansen: {lastlast.tenkan_sen}, lastlast kijunsen: {lastlast.kijun_sen}")
        print(f"Long Entry?: {lg_ent}")
        print(f"Short Entry?: {st_ent}")
        print(f"Long Exit?: {lg_ext}")
        print(f"Short Exit?: {st_ext}")  
        
        if position.size == 0: 
            if lg_ent:
                pos_size = total_balance * settings['allocation']
                size = pos_size * asset.get_contract_rate(last.close)
                order = {
                    'order_type' : 'market',
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
                'order_type' : 'market',
                'size' : size,
                'side' : 'sell'
            }
            asset.create_order('l_exit', order)
            print("lastlast.tenkan_sen > lastlast.kijun_sen & last.tenkan_sen < last.kijun_sen")
            print("Lastlast tenkansen: ", lastlast.tenkan_sen) 
            print("Lastlast kijunsen: ", lastlast.kijun_sen) 
            print("Last tenkansen: ", last.tenkan_sen) 
            print("Last kijunsen: ", last.kijun_sen) 


def process_bitmex_LO(window, assets, context):
    total_unrealised_pnl = sum([asset.position.unrealised_pnl for _, asset in assets.items()])
    total_balance = total_unrealised_pnl + context['balance']
    
    for symbol, asset in assets.items():
        position = asset.position
        last = window.latest(symbol)
        lastlast = window.previous(symbol, 2)
        settings = context['assets'][symbol]   
        
        lg_ent = ((last.close > last.kijun_sen) and (last.senkou_span_a < last.close > last.senkou_span_b))    
        lg_ext = (last.tenkan_sen < last.kijun_sen)   

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
        print(f"last tenkansen: {last.tenkan_sen}, last kijunsen: {last.kijun_sen}, last senkouspana: {last.senkou_span_a}, last senkouspanb: {last.senkou_span_b} ")
        print(f"Long Entry?: {lg_ent}")
        print(f"Long Exit?: {lg_ext}")
        
        if position.size == 0: 
            if lg_ent:
                pos_size = total_balance * settings['allocation']
                size = pos_size * asset.get_contract_rate(last.close)
                order = {
                    'order_type' : 'market',
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
                'order_type' : 'market',
                'size' : size,
                'side' : 'sell'
            }
            asset.create_order('l_exit', order)
            print("tenkansen < kijunsen")
            print("Last tenkansen: ", last.tenkan_sen) 
            print("Last kijunsen: ", last.kijun_sen) 