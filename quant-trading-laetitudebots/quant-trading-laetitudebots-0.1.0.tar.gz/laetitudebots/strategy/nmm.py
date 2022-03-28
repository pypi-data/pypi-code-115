import numpy as np

from laetitudebots.util.talib_method import talib_method


def nmm(values):
    nmm = 0.0
    sum = 0.0
    length = 0.0
    length = len(values)
    last_val = values[-1]

    for i in range(1, (length - 1)):
        sum = sum + (last_val - values[i]) / np.sqrt(i * 1.0)

    nmmv = sum / (length)

    return float(nmmv)


def initialize(factors, config):
    lb = config['parameters']['lb']
    factors['log'] = np.log(factors.close)
    factors['nmm'] = factors.log.rolling(lb).apply(nmm)


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
        lg_sig = (prev_bar.nmm < 0) & (last_bar.nmm > 0)
        st_sig = (prev_bar.nmm > 0) & (last_bar.nmm < 0)

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
        print(f"Buy Signal? {lg_sig}")
        print(f"Sell Signal? {st_sig} \n")
        print("Check figures:")
        print(f"Prev Bar NMM: {prev_bar.nmm}")
        print(f"Last Bar NMM: {last_bar.nmm} \n")

        if position.size <= 0 and lg_sig:
            print("Long Signal. NMM crosses above 0")
            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(
                last_bar.close
            )
            order = {'order_type': 'market', 'size': size, 'side': 'buy'}
            asset.create_order('nmm_long', order)
            print(f"Long market order: {order}")

        if position.size >= 0 and st_sig:
            print("Short signal. NMM crosses below 0")
            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(
                last_bar.close
            )
            order = {'order_type': 'market', 'size': size, 'side': 'sell'}
            asset.create_order('nmm_short', order)
            print(f"Short market order: {order}")

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
        lg_sig = (prev_bar.nmm < 0) & (last_bar.nmm > 0)
        st_sig = (prev_bar.nmm > 0) & (last_bar.nmm < 0)

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
        print(f"Position size: {position.size}")
        print(f"Last Bar OHLC: {last_bar.open}, {last_bar.high}, {last_bar.low}, {last_bar.close} \n")
        print(f"Buy Signal? {lg_sig}")
        print(f"Sell Signal? {st_sig} \n")
        print("Check figures:")
        print(f"Prev Bar NMM: {prev_bar.nmm}")
        print(f"Last Bar NMM: {last_bar.nmm} \n")

        pos_size = total_balance * settings['allocation']
        size = abs(pos_size) * asset.get_contract_rate(last_bar.close)

        if position.size < (size * 0.5):
            if lg_sig:
                print("Buy signal.")
                print(f"Position size: {position.size}")
                print(f"Size * 0.5: {size * 0.5}")
                order = {'order_type': 'market', 'size': size, 'side': 'buy'}
                asset.create_order('nmm_entry', order)
                print(f"Long market order: {order}")

        if position.size > (size * 0.5):
            if st_sig:
                print("Sell signal.")
                print(f"Position size: {position.size}")
                print(f"Size * 0.5: {size * 0.5}")
                size = abs(position.size)
                order = {'order_type': 'market', 'size': size, 'side': 'sell'}
                asset.create_order('nmm_exit', order)
                print(f"Market exit: {order}")