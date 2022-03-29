from laetitudebots.util.talib_method import talib_method


def initialize(factors, config):
    period = config['parameters']['period']
    fastln = config['parameters']['fastln']
    slowln = config['parameters']['slowln']
    stmacdln = config['parameters']['stmacdln']
    factors['highest'] = factors.high.rolling(period).max()
    factors['lowest'] = factors.low.rolling(period).min()
    factors['fastval'] = talib_method(
        method='EMA', timeperiod=fastln, args=[factors.close]
    )
    factors['slowval'] = talib_method(
        method='EMA', timeperiod=slowln, args=[factors.close]
    )
    factors['fast_stoch'] = (factors.fastval - factors.lowest) / (
        factors.highest - factors.lowest
    )
    factors['slow_stoch'] = (factors.slowval - factors.lowest) / (
        factors.highest - factors.lowest
    )
    factors['stmacd'] = (factors.fast_stoch - factors.slow_stoch) * 100
    factors['stmacdavg'] = talib_method(
        method='EMA', timeperiod=stmacdln, args=[factors.stmacd]
    )


def process_bitmex(window, assets, context):
    total_unrealised_pnl = sum(
        [asset.position.unrealised_pnl for asset in assets.values()]
    )
    total_balance = total_unrealised_pnl + context['balance']

    for symbol, asset in assets.items():
        position = asset.position
        prev_bar = window.previous(symbol, 2)
        last_bar = window.latest(symbol)
        settings = context['assets'][symbol]
        lg_sig = (prev_bar.stmacd < prev_bar.stmacdavg) & (
            last_bar.stmacd > last_bar.stmacdavg
        )
        st_sig = (prev_bar.stmacd > prev_bar.stmacdavg) & (
            last_bar.stmacd < last_bar.stmacdavg
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

        print(f"Pair: {symbol}")
        print(f"Last Bar OHLC: {last_bar.open}, {last_bar.high}, {last_bar.low}, {last_bar.close} \n")
        print(f"Buy Signal?: {lg_sig}")
        print(f"Sell Signal?: {st_sig} \n")

        print("Check figures:")        
        print(f"Prev Bar StMACD: {prev_bar.stmacd}, Prev Bar StMACDAvg: {prev_bar.stmacdavg}")
        print(f"Prev Bar StMACD < Prev Bar StMACDAvg?: {prev_bar.stmacd < prev_bar.stmacdavg}")
        print(f"Prev Bar StMACD > Prev Bar StMACDAvg?: {prev_bar.stmacd > prev_bar.stmacdavg} \n")
        print(f"Last Bar StMACD: {last_bar.stmacd}, Last Bar StMACDAvg: {last_bar.stmacdavg}")
        print(f"Last Bar StMACD > Last Bar StMACDAvg?: {last_bar.stmacd > last_bar.stmacdavg}")
        print(f"Last Bar StMACD < Last Bar StMACDAvg?: {last_bar.stmacd < last_bar.stmacdavg}")

        if position.size <= 0 and lg_sig:
            print("Buy Signal.")
            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(
                last_bar.close
            )
            order = {'order_type': 'market', 'size': size, 'side': 'buy'}
            asset.create_order('stmacd_long', order)
            print(f"Long Market Order: {order}")

        if position.size >= 0 and st_sig:
            print("Sell Signal.")
            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(
                last_bar.close
            )
            order = {'order_type': 'market', 'size': size, 'side': 'sell'}
            asset.create_order('stmacd_short', order)
            print(f"Short Market Order: {order}")


def process_binance(window, assets, context):
    total_unrealised_pnl = sum(
        [asset.position.unrealised_pnl for asset in assets.values()]
    )
    total_balance = total_unrealised_pnl + context['balance']

    for symbol, asset in assets.items():
        position = asset.position
        prev_bar = window.previous(symbol, 2)
        last_bar = window.latest(symbol)
        settings = context['assets'][symbol]
        lg_sig = (prev_bar.stmacd < prev_bar.stmacdavg) & (
            last_bar.stmacd > last_bar.stmacdavg
        )
        st_sig = (prev_bar.stmacd > prev_bar.stmacdavg) & (
            last_bar.stmacd < last_bar.stmacdavg
        )

        pos_size = total_balance * settings['allocation']
        size = abs(pos_size) * asset.get_contract_rate(last_bar.close)

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
        print(f"Last Bar OHLC: {last_bar.open}, {last_bar.high}, {last_bar.low}, {last_bar.close} \n")
        print(f"Buy Signal?: {lg_sig}")
        print(f"Sell Signal?: {st_sig} \n")
        print("Check figures:")        
        print(f"Prev Bar StMACD: {prev_bar.stmacd}, Prev Bar StMACDAvg: {prev_bar.stmacdavg}")
        print(f"Prev Bar StMACD < Prev Bar StMACDAvg?: {prev_bar.stmacd < prev_bar.stmacdavg}")
        print(f"Prev Bar StMACD > Prev Bar StMACDAvg?: {prev_bar.stmacd > prev_bar.stmacdavg} \n")
        print(f"Last Bar StMACD: {last_bar.stmacd}, Last Bar StMACDAvg: {last_bar.stmacdavg}")
        print(f"Last Bar StMACD > Last Bar StMACDAvg?: {last_bar.stmacd > last_bar.stmacdavg}")
        print(f"Last Bar StMACD < Last Bar StMACDAvg?: {last_bar.stmacd < last_bar.stmacdavg} \n")
        print(f"Current position size: {position.size}")

        if position.size < (size * 0.5):
            if lg_sig:
                print("Buy signal.")
                print(f"Position Size: {position.size}")
                print(f"Size * 0.5: {size * 0.5}")
                order = {'order_type': 'market', 'size': size, 'side': 'buy'}
                asset.create_order('stmacd_entry', order)
                print(f"Long market order: {order}")

        if position.size > (size * 0.5): 
            if st_sig:
                print("Sell signal.")
                print(f"Position Size: {position.size}")
                print(f"Size * 0.5: {size * 0.5}")
                size = abs(position.size)
                order = {'order_type': 'market', 'size': size, 'side': 'sell'}
                asset.create_order('stmacd_exit', order)
                print(f"Market exit: {order}")
