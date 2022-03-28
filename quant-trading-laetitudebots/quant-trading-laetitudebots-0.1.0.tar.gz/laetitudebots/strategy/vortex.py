from laetitudebots.util.talib_method import talib_method


def initialize(factors, config):
    v_period = config['parameters']['v_period']
    t_period = config['parameters']['t_period']
    factors['vmp'] = (
        abs(factors.high - factors.low.shift(1)).rolling(v_period).sum()
    )
    factors['vmm'] = (
        abs(factors.low - factors.high.shift(1)).rolling(v_period).sum()
    )
    factors['str'] = (
        talib_method(
            method='ATR',
            timeperiod=t_period,
            args=[factors.high, factors.low, factors.close],
        )
        .rolling(v_period)
        .sum()
    )
    factors['vip'] = factors.vmp / factors.str
    factors['vim'] = factors.vmm / factors.str


def process_bitmex(window, assets, context):
    
    total_unrealised_pnl = sum([asset.position.unrealised_pnl for asset in assets.values()])
    total_balance = total_unrealised_pnl + context['balance']
    
    for symbol, asset in assets.items():
        position = asset.position
        
        prev_bar = window.previous(symbol, 2)
        last_bar = window.latest(symbol)
        
        settings = context['assets'][symbol]
        buy_sig = (prev_bar.vip < prev_bar.vim) & (last_bar.vip > last_bar.vim)
        sell_sig = (prev_bar.vip > prev_bar.vim) & (last_bar.vip < last_bar.vim)

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
        print(f"Prev VIP: {prev_bar.vip}, Prev VIM: {prev_bar.vim}")
        print(f"Last VIP: {last_bar.vip}, Last VIM: {last_bar.vim}")
        print(f"Buy Signal?: {buy_sig}")
        print(f"Sell Signal?: {sell_sig}")

        if position.size == 0:
            print("No position. Buy order if buy signal, Sell order if sell signal.")
            pos_size = total_balance * settings['allocation']
            if buy_sig:
                print(f"Buy signal?: {buy_sig}")
                if asset.orders:
                    asset.cancel_order('vortex_short')
                    print("Short order cancelled.")
                else:
                    print("Orders empty. No short order cancelled.")
                lg_ent = last_bar.high
                print(f"Last Bar High: {lg_ent}")
                print(f"Last Bar Close: {last_bar.close}")
                size = pos_size * asset.get_contract_rate(lg_ent)
                if lg_ent > last_bar.close:
                    print(f"Last Bar High > Last Bar Close? {lg_ent > last_bar.close}")
                    order = {
                        'order_type': 'stop',
                        'side': 'buy',
                        'trigger_price': lg_ent,
                        'size' : size
                    }
                    asset.create_order('vortex_long', order)
                    print(f"Long stop market order created: {order}")
                elif lg_ent == last_bar.close:
                    print(f"Last Bar High == Last Bar Close? {lg_ent == last_bar.close}")
                    order = {
                        'order_type': 'market',
                        'side': 'buy',
                        'size': size
                    }
                    asset.create_order('vortex_long', order)
                    print(f"Long market entry: {order}")
                else:
                    print("High < Close? Check fetched data.")
                    print(f"Last Bar High: {last_bar.high}")
                    print(f"Last Bar Close: {last_bar.close}")
                    raise ValueError("High can never be lower than the Close!")
            if sell_sig:
                print(f"Sell signal?: {sell_sig}")
                if asset.orders:
                    asset.cancel_order('vortex_long')
                    print("Long order has been cancelled.")
                else:
                    print("No long order cancelled.")
                st_ent = last_bar.low
                print(f"Last Bar Low: {st_ent}")
                print(f"Last Bar Close: {last_bar.close}")
                size = pos_size * asset.get_contract_rate(st_ent)
                if st_ent < last_bar.close:
                    print(f"Last Bar Low < Last Bar Close? {st_ent < last_bar.close}")
                    order = {
                        'order_type': 'stop',
                        'side': 'sell',
                        'trigger_price': st_ent,
                        'size' : size
                    }
                    asset.create_order('vortex_short', order)
                    print(f"Short stop market order created: {order}")
                elif st_ent == last_bar.close:
                    print(f"Last Bar Low == Last Bar Close? {st_ent == last_bar.close}")
                    order = {
                        'order_type': 'market',
                        'side': 'sell',
                        'size' : size
                    }
                    asset.create_order('vortex_short', order)
                    print(f"Short market entry: {order}")
                else: 
                    print("Low > Close? Check fetched data.")
                    print(f"Last Bar Low: {last_bar.low}")
                    print(f"Last Bar Close: {last_bar.close}")
                    raise ValueError("Low can never be higher than the Close!")
        if position.size > 0:
            print("Currently on long position.")
            if buy_sig:
                print(f"Buy signal?: {buy_sig}")
                if asset.orders:
                    asset.cancel_order('vortex_short')
                    print("Short order cancelled.")
                else:
                    print("Check why there's no short order in previous sell signal.")
            if sell_sig:
                print(f"Sell signal?: {sell_sig}")
                st_ent = last_bar.low
                print(f"Last Bar Low: {st_ent}")
                print(f"Last Bar Close: {last_bar.close}")
                pos_size = total_balance * settings['allocation']
                size = abs(position.size) + pos_size * asset.get_contract_rate(st_ent)
                if st_ent < last_bar.close:
                    print(f"Last Bar Low < Last Bar Close?: {st_ent < last_bar.close}")
                    order = {
                        'order_type': 'stop',
                        'side': 'sell',
                        'trigger_price': st_ent,
                        'size': size
                    }
                    asset.create_order('vortex_short', order)
                    print(f"Short stop market order created: {order}")
                elif st_ent == last_bar.close:
                    print(f"Last Bar Low == Last Bar Close?: {st_ent == last_bar.close}")
                    order = {
                        'order_type': 'market',
                        'side': 'sell',
                        'size': size
                    }
                    asset.create_order('vortex_short', order)
                    print(f"Short market entry: {order}")
                else:
                    print('Low > Close? Check fetched data.')
                    print(f'Last Bar High: {last_bar.low}')
                    print(f'Last Bar Close: {last_bar.close}')
                    raise ValueError("Low can never be higher than the Close!")
        if position.size < 0:
            print("Currently on short position.")
            if sell_sig:
                print(f"Sell signal?: {sell_sig}")
                if asset.orders:
                    asset.cancel_order('vortex_long')
                    print("Long order cancelled.")
                else:
                    print("Check why there's no long order in previous buy signal.")
            if buy_sig:
                print(f"Buy signal?: {buy_sig}")
                lg_ent = last_bar.high
                print(f"Last Bar High: {lg_ent}")
                print(f"Las Bar Close: {last_bar.close}")
                pos_size = total_balance * settings['allocation']
                size = abs(position.size) + pos_size * asset.get_contract_rate(lg_ent)
                if lg_ent > last_bar.close:
                    order = {
                        'order_type': 'stop',
                        'side': 'buy',
                        'trigger_price': lg_ent,
                        'size': size
                    }
                    asset.create_order('vortex_long', order)
                    print(f"Long stop market order created: {order}")
                elif lg_ent == last_bar.close:
                    print(f"Last Bar High == Last Bar Close?: {lg_ent == last_bar.close}")
                    order = {
                        'order_type': 'market',
                        'side': 'buy',
                        'size': size
                    }
                    asset.create_order('vortex_long', order)
                    print(f"Long market entry: {order}")
                else:
                    print("High < Close? Check fetched data.")
                    print(f"Last Bar High: {last_bar.high}")
                    print(f"Last Bar Close: {last_bar.close}")
                    raise ValueError("High can never be lower than the Close!")
