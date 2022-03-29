from laetitudebots.util.talib_method import talib_method


def initialize(factors, config):
    idx = config['parameters']['idx']

    factors['close'] = factors.close
    factors['high'] = factors.high
    factors['slow'] = factors.low

    factors['dx'] = talib_method(
        method='DX',
        timeperiod=idx,
        args=[factors.high, factors.low, factors.close],
    )
    factors['min_di'] = talib_method(
        method='MINUS_DI',
        timeperiod=idx,
        args=[factors.high, factors.low, factors.close],
    )
    factors['plus_di'] = talib_method(
        method='PLUS_DI',
        timeperiod=idx,
        args=[factors.high, factors.low, factors.close],
    )

    print(f"dx: {factors['dx'].iloc[-2:]}")
    print(f"min_di: {factors['min_di'].iloc[-2:]}")
    print(f"plus_di: {factors['plus_di'].iloc[-2:]}")


def process_bitmex(window, assets, context):

    total_unrealised_pnl = sum(
        [asset.position.unrealised_pnl for _, asset in assets.items()]
    )
    total_balance = total_unrealised_pnl + context['balance']

    for symbol, asset in assets.items():
        print(f'Symbol: {symbol}')

        position = asset.position
        last = window.latest(symbol)
        lastlast = window.previous(symbol, 2)
        settings = context['assets'][symbol]

        print(f'Last Bar DX {last.dx}')
        print(f'Previous Bar plus_di {lastlast.plus_di}')
        print(f'Previous Bar min_di {lastlast.min_di}')
        print(f'Last Bar plus_di {last.plus_di}')
        print(f'Last Bar min_di {last.min_di}')

        lg_ent_cond_1 = (
            lastlast.plus_di < lastlast.min_di and last.plus_di > last.min_di
        )
        lg_ent_cond_2 = last.plus_di > last.min_di and last.dx > 30
        lg_ent = lg_ent_cond_1 or lg_ent_cond_2

        st_ent = (
            lastlast.plus_di > lastlast.min_di and last.plus_di < last.min_di
        )

        if position.size == 0:
            if lg_ent:
                print('Long entry')
                pos_size = total_balance * settings['allocation']
                size = pos_size * asset.get_contract_rate(last.close)
                order = {'order_type': 'market', 'size': size, 'side': 'buy'}
                asset.create_order('l_entry', order)

        elif position.size > 0:
            pos_size = total_balance * settings['allocation']
            size = pos_size * asset.get_contract_rate(last.close)
            size2 = abs(position.size)
            if st_ent:
                print('Long close')
                order = {'order_type': 'market', 'size': size2, 'side': 'sell'}
                asset.create_order('l_close', order)
