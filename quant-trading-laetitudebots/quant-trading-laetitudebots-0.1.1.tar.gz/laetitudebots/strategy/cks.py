from laetitudebots.util.talib_method import talib_method


def initialize(factors, context):
    params = context['parameters']
    p = params['p']
    q = params['q']
    x = params['x']

    factors['atr'] = talib_method(method='ATR', timeperiod=p,
                                  args=[factors.high, factors.low,
                                        factors.close])

    factors['highest_high'] = factors.high.rolling(p).max()
    factors['lowest_high'] = factors.high.rolling(p).min()

    factors['first_high_stop'] = factors.highest_high - x * factors.atr
    factors['first_low_stop'] = factors.lowest_high + x * factors.atr

    factors['stop_short'] = factors.first_high_stop.rolling(q).max()
    factors['stop_long'] = factors.first_low_stop.rolling(q).min()


def process(window, assets, context):
    total_unrealised_pnl = sum([asset.position.unrealised_pnl
                                for asset in assets.values()])
    balance = total_unrealised_pnl + context['balance']
    for symbol, asset in assets.items():
        position = asset.position

        last = window.latest(symbol)
        settings = context['assets'][symbol]

        stop_long = last.stop_long
        stop_short = last.stop_short
        close = last.close

        long = stop_long < close > stop_short
        short = stop_long > close < stop_short

        if position.size <= 0 and long:
            pos_size = balance * settings['allocation']
            size = abs(position.size) + (pos_size
                                         * asset.get_contract_rate(last.close))
            order = {
                'order_type': 'market',
                'size': size,
                'side': 'buy'
            }
            asset.create_order('cks_long', order)
        if position.size >= 0 and short:
            pos_size = balance * settings['allocation']
            size = abs(position.size) + (pos_size
                                         * asset.get_contract_rate(last.close))
            order = {
                'order_type': 'market',
                'size': size,
                'side': 'sell'
            }
            asset.create_order('cks_short', order)
