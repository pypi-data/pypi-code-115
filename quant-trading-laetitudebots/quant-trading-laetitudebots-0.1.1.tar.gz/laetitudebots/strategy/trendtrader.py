from laetitudebots.util.talib_method import talib_method


def initialize(factors, config):
    length = config['parameters']['length']
    mult = config['parameters']['mult']
    factors['atr'] = talib_method(
        method='ATR',
        timeperiod=1,
        args=[factors.high, factors.low, factors.close],
    )
    factors['avg_tr'] = talib_method(
        method='WMA', timeperiod=length, args=[factors.atr]
    )
    factors['highest'] = factors.high.rolling(length).max()
    factors['lowest'] = factors.low.rolling(length).min()
    factors['hi_lim'] = factors.highest.shift(1) - (
        factors.avg_tr.shift(1) * mult
    )
    factors['lo_lim'] = factors.lowest.shift(1) + (
        factors.avg_tr.shift(1) * mult
    )


def process_bitmex(window, assets, context):
    total_unrealised_pnl = sum(
        [asset.position.unrealised_pnl for _, asset in assets.items()]
    )
    total_balance = total_unrealised_pnl + context['balance']

    for symbol, asset in assets.items():
        position = asset.position
        prev_bar = window.previous(symbol, 2)
        last_bar = window.latest(symbol)

        settings = context['assets'][symbol]
        lg_sig = (
                (last_bar.hi_lim < last_bar.close > last_bar.lo_lim) & 
                (((prev_bar.close < prev_bar.hi_lim) & (last_bar.close > last_bar.hi_lim)) | 
                ((prev_bar.close < prev_bar.lo_lim) & (last_bar.close > last_bar.lo_lim)))
                )
        st_sig = (
                (last_bar.hi_lim > last_bar.close < last_bar.lo_lim) & 
                (((prev_bar.close > prev_bar.hi_lim) & (last_bar.close < last_bar.hi_lim)) | 
                ((prev_bar.close > prev_bar.lo_lim) & (last_bar.close < last_bar.lo_lim)))
                )

        print("WINDOW")
        print(window)   
        print(f"Window Latest - Timestamp: {last_bar.timestamp}")
        print(f"Window Latest - Open: {last_bar.open}")
        print(f"Window Latest - High: {last_bar.high}")
        print(f"Window Latest - Low: {last_bar.low}") 
        print(f"Window Latest - Close: {last_bar.close}")
        print(f"Window Latest - Volume: {last_bar.volume}")
        print("######## \n")

        if position.size <= 0 and lg_sig:
            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(
                last_bar.close
            )
            order = {'order_type': 'market', 'size': size, 'side': 'buy'}
            asset.create_order('rider_long', order)

        if position.size >= 0 and st_sig:
            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(
                last_bar.close
            )
            order = {'order_type': 'market', 'size': size, 'side': 'sell'}
            asset.create_order('rider_short', order)


def process_ftx(window, assets, context):
    total_unrealised_pnl = sum(
        [asset.position.unrealised_pnl for _, asset in assets.items()]
    )
    total_balance = total_unrealised_pnl + context['balance']

    for symbol, asset in assets.items():
        position = asset.position
        prev_bar = window.previous(symbol, 2)
        last_bar = window.latest(symbol)
        settings = context['assets'][symbol]
        lg_sig = (
                (last_bar.hi_lim < last_bar.close > last_bar.lo_lim) & 
                (((prev_bar.close < prev_bar.hi_lim) & (last_bar.close > last_bar.hi_lim)) | 
                ((prev_bar.close < prev_bar.lo_lim) & (last_bar.close > last_bar.lo_lim)))
                )
        st_sig = (
                (last_bar.hi_lim > last_bar.close < last_bar.lo_lim) & 
                (((prev_bar.close > prev_bar.hi_lim) & (last_bar.close < last_bar.hi_lim)) | 
                ((prev_bar.close > prev_bar.lo_lim) & (last_bar.close < last_bar.lo_lim)))
                )

        print("WINDOW")
        print(window)   
        print(f"Window Latest - Timestamp: {last_bar.timestamp}")
        print(f"Window Latest - Open: {last_bar.open}")
        print(f"Window Latest - High: {last_bar.high}")
        print(f"Window Latest - Low: {last_bar.low}") 
        print(f"Window Latest - Close: {last_bar.close}")
        print(f"Window Latest - Volume: {last_bar.volume}")
        print("######## \n")

        print("Asset: ", asset)
        print("Symbol: ", symbol)
        print("Last Bar Lo_Limit: ", last_bar.lo_lim)
        print("Last Bar Hi_Limit: ", last_bar.hi_lim)
        print("Last Bar Close: ", last_bar.close, "\n")

        print("Hi_Lim < Close > Lo_Limit? ", last_bar.hi_lim < last_bar.close > last_bar.lo_lim)
        print("Hi_Lim > Close < Lo_Lim? ", last_bar.hi_lim > last_bar.close < last_bar.lo_lim, "\n")

        if position.size <= 0 and lg_sig:
            asset.cancel_order('rider_short')
            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(
                last_bar.close, last_bar.collateral
            )
            order = {'order_type': 'market', 'size': size, 'side': 'buy'}
            asset.create_order('rider_long', order)
            
            print('Order placed.')
            print(order)
            print("Asset: ", asset)
            print("Symbol: ", symbol)
            print("Last Bar Close: ", last_bar.close)
            print("Last Bar Lo_Limit: ", last_bar.lo_lim)
            print("Last Bar Hi_Limit: ", last_bar.hi_lim)
            print("Hi_Lim < Close > Lo_Limit? ", last_bar.hi_lim < last_bar.close > last_bar.lo_lim)

        
        if position.size >= 0 and st_sig:
            asset.cancel_order('rider_long')
            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(
                last_bar.close, last_bar.collateral
            )
            order = {'order_type': 'market', 'size': size, 'side': 'sell'}
            asset.create_order('rider_short', order)

            print('Order placed.')
            print(order)
            print("Asset: ", asset)
            print("Symbol: ", symbol)
            print("Last Bar Close: ", last_bar.close)
            print("Last Bar Lo_Limit: ", last_bar.lo_lim)
            print("Last Bar Hi_Limit: ", last_bar.hi_lim)
            print("Hi_Lim > Close < Lo_Lim? ", last_bar.hi_lim > last_bar.close < last_bar.lo_lim)

