from laetitudebots.util.talib_method import talib_method


def initialize(factors, config):
    idx = config['parameters']['idx']

    factors['close'] = factors.close
    factors['high'] = factors.high
    factors['slow'] = factors.low
    factors['dx'] = talib_method(method='DX', timeperiod = idx, args = [factors.high, factors.low, factors.close])
    factors['min_di'] = talib_method(method='MINUS_DI', timeperiod = idx, args =[factors.high, factors.low, factors.close])
    factors['plus_di'] = talib_method(method='PLUS_DI', timeperiod = idx, args =[factors.high, factors.low, factors.close])

def process_bitmex(window, assets, context):
    total_unrealised_pnl = sum([asset.position.unrealised_pnl for _, asset in assets.items()])
    total_balance = total_unrealised_pnl + context['balance']

    for symbol, asset in assets.items():
        position = asset.position
        last = window.latest(symbol)
        lastlast = window.previous(symbol, 2)
        settings = context['assets'][symbol]

        dx = last.dx
        pdi = last.plus_di
        mdi = last.min_di

        lg_ent = ((dx > 25) and
                 (dx > lastlast.dx) and
                 (pdi > mdi) and
                 (pdi > lastlast.plus_di))
        st_ent = ((dx > 25) and
                 (dx > lastlast.dx) and
                 (mdi > pdi) and
                 (mdi > lastlast.min_di))
        lg_ext = (pdi < mdi)
        st_ext = (pdi > mdi)

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
        print(f"last dx: {last.dx}, last pdi: {last.plus_di}, last mdi: {last.min_di} ")
        print(f"lastlast: {lastlast.dx}, lastlast pdi: {lastlast.plus_di}, lastlast mdi: {lastlast.min_di} ")
        print(f"Long Entry?: {lg_ent}")
        print(f"Short Entry?: {st_ent}")
        print(f"Long Exit?: {lg_ext}")
        print(f"Short Exit?: {st_ext}")

        if position.size == 0:
            if lg_ent:

                pos_size = total_balance * settings['allocation']
                size =  pos_size * asset.get_contract_rate(last.close)
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
            print("pdi < mdi")
            print("Last pdi: ", last.plus_di)
            print("Last mdi: ", last.min_di)

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
            print("pdi > mdi")
            print("Last pdi: ", last.plus_di)
            print("Last mdi: ", last.min_di)


def process_ftx(window, assets, context):
    total_unrealised_pnl = sum([asset.position.unrealised_pnl for _, asset in assets.items()])
    total_balance = total_unrealised_pnl + context['balance']

    for symbol, asset in assets.items():
        position = asset.position
        last = window.latest(symbol)
        lastlast = window.previous(symbol, 2)
        settings = context['assets'][symbol]

        dx = last.dx
        pdi = last.plus_di
        mdi = last.min_di

        lg_ent = ((dx > 25) and
                 (dx > lastlast.dx) and
                 (pdi > mdi) and
                 (pdi > lastlast.plus_di))
        st_ent = ((dx > 25) and
                 (dx > lastlast.dx) and
                 (mdi > pdi) and
                 (mdi > lastlast.min_di))
        lg_ext = pdi < mdi
        st_ext = pdi > mdi

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
        print(f"last dx: {last.dx}, last pdi: {last.plus_di}, last mdi: {last.min_di} ")
        print(f"lastlast: {lastlast.dx}, lastlast pdi: {lastlast.plus_di}, lastlast mdi: {lastlast.min_di} ")
        print(f"Long Entry?: {lg_ent}")
        print(f"Short Entry?: {st_ent}")
        print(f"Long Exit?: {lg_ext}")
        print(f"Short Exit?: {st_ext}")

        if position.size == 0:
            if lg_ent:
                pos_size = total_balance * settings['allocation']
                size =  pos_size * asset.get_contract_rate(last.close,  last.collateral )
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
            print("pdi < mdi")
            print("Last pdi: ", last.plus_di)
            print("Last mdi: ", last.min_di)

        if position.size == 0:
            if st_ent:
                pos_size = total_balance * settings['allocation']
                size = pos_size * asset.get_contract_rate(last.close,  last.collateral)
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
            print("pdi > mdi")
            print("Last pdi: ", last.plus_di)
            print("Last mdi: ", last.min_di)


def process_bitmex_LO(window, assets, context):
    total_unrealised_pnl = sum([asset.position.unrealised_pnl for _, asset in assets.items()])
    total_balance = total_unrealised_pnl + context['balance']

    for symbol, asset in assets.items():
        position = asset.position
        last = window.latest(symbol)
        lastlast = window.previous(symbol, 2)
        settings = context['assets'][symbol]

        dx = last.dx
        pdi = last.plus_di
        mdi = last.min_di

        lg_ent = ((dx > 25) and
                 (dx > lastlast.dx) and
                 (pdi > mdi) and
                 (pdi > lastlast.plus_di))
        lg_ext = (pdi < mdi)

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
        print(f"last dx: {last.dx}, last pdi: {last.plus_di}, last mdi: {last.min_di} ")
        print(f"lastlast: {lastlast.dx}, lastlast pdi: {lastlast.plus_di}, lastlast mdi: {lastlast.min_di} ")
        print(f"Long Entry?: {lg_ent}")
        print(f"Long Exit?: {lg_ext}")

        if position.size == 0:
            if lg_ent:

                pos_size = total_balance * settings['allocation']
                size =  pos_size * asset.get_contract_rate(last.close)
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
            print("pdi < mdi")
            print("Last pdi: ", last.plus_di)
            print("Last mdi: ", last.min_di)