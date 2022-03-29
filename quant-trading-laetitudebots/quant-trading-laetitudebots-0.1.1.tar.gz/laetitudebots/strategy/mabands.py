from laetitudebots.util.talib_method import talib_method


def initialize(factors, config):
    ma_len = config['parameters']['ma_len']

    factors['mao'] = talib_method(
        method='SMA', timeperiod=ma_len, args=[factors.open]
    )
    factors['mah'] = talib_method(
        method='SMA', timeperiod=ma_len, args=[factors.high]
    )
    factors['mal'] = talib_method(
        method='SMA', timeperiod=ma_len, args=[factors.low]
    )
    factors['mac'] = talib_method(
        method='SMA', timeperiod=ma_len, args=[factors.close]
    )

    factors['mah2'] = factors.mah + (factors.mah - factors.mal)
    factors['mal2'] = factors.mal - (factors.mah - factors.mal)
    factors['mah3'] = factors.mah2 + (factors.mah - factors.mal)
    factors['mal3'] = factors.mah2 - (factors.mah - factors.mal)

    print(f"MAO: {factors['mao'].iloc[-2:]}")
    print(f"MAH: {factors['mah'].iloc[-2:]}")
    print(f"MAL: {factors['mal'].iloc[-2:]}")
    print(f"MAC: {factors['mac'].iloc[-2:]}")
    print(f"MAH2: {factors['mah2'].iloc[-2:]}")
    print(f"MAL2: {factors['mal2'].iloc[-2:]}")
    print(f"MAH3: {factors['mah3'].iloc[-2:]}")
    print(f"MAL3: {factors['mal3'].iloc[-2:]}")


def process_bitmex(window, assets, context):

    total_unrealised_pnl = sum(
        [asset.position.unrealised_pnl for _, asset in assets.items()]
    )
    total_balance = total_unrealised_pnl + context['balance']

    for symbol, asset in assets.items():
        print(f'Symbol: {symbol}')

        position = asset.position
        last = window.latest(symbol)
        prev = window.previous(symbol, 2)
        settings = context['assets'][symbol]

        lg_cond1 = (prev.close < prev.mah2) and (last.close > last.mah2)
        lg_cond2 = last.low > last.mah3
        lg_ent = lg_cond1 or lg_cond2

        lg_close_cond1 = (prev.close > prev.mah3) and (last.close < prev.mah3)
        lg_close_cond2 = (prev.close > prev.mal) and (last.close < last.mal)
        lg_close = lg_close_cond1 or lg_close_cond2

        print(f"Window Latest - Timestamp: {last.timestamp}")
        print(f"Window Latest - Open: {last.open}")
        print(f"Window Latest - High: {last.high}")
        print(f"Window Latest - Low: {last.low}")
        print(f"Window Latest - Close: {last.close}")
        print(f"Window Latest - Volume: {last.volume}")

        print(f'Long Cond1: {lg_cond1}')
        print(f'Long Cond2: {lg_cond2}')
        print(f'Long Entry: {lg_ent}')

        print(f'Long Close Cond1: {lg_close_cond1}')
        print(f'Long Close Cond2: {lg_close_cond2}')
        print(f'Long Close: {lg_close}')

        if position.size == 0:
            if lg_ent:
                print('Buy Signal')
                pos_size = total_balance * settings['allocation']
                size = pos_size * asset.get_contract_rate(last.close)
                order = {'order_type': 'market', 'size': size, 'side': 'buy'}
                asset.create_order('l_entry', order)

        elif position.size > 0:
            pos_size = total_balance * settings['allocation']
            size = pos_size * asset.get_contract_rate(last.close)
            size2 = abs(position.size)
            if lg_close:
                print('Long Close Signal')
                order = {'order_type': 'market', 'size': size2, 'side': 'sell'}
                asset.create_order('l_close', order)

