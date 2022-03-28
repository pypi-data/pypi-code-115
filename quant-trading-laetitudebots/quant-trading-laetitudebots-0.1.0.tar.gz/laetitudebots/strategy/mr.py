import numpy as np

from laetitudebots.util.talib_method import talib_method

def rolling_sharpe(series):
    out = []
    weights = 10*(np.log2(range(2, len(series)+2)))
    for i in range(len(series)):
        out.extend([series[i]]*int(weights[i]))
    out = np.array(out)
    try:
        res = out.mean() / out.std()
    except ZeroDivisionError:
        res = 0
    
    return res

def initialize(factors, config):

    period = config['parameters']['period']
    
    factors['rets'] = factors.close.pct_change()
    factors['mr'] = factors.rets.rolling(period).apply(rolling_sharpe, raw=False)

def process_bitmex(window, assets, context):

    total_unrealised_pnl = sum([asset.position.unrealised_pnl for _, asset in assets.items()])
    total_balance = total_unrealised_pnl + context['balance'] 

    for symbol, asset in assets.items():

        position = asset.position

        prev_bar = window.previous(symbol, 2)
        last_bar = window.latest(symbol)

        settings = context['assets'][symbol] 

        lg_sig = (prev_bar.mr < 0) and (last_bar.mr > 0)
        st_sig = (prev_bar.mr > 0) and (last_bar.mr < 0) 

        print("WINDOW")
        print(window)   
        print(f"Window Latest - Timestamp: {last_bar.timestamp}")
        print(f"Window Latest - Open: {last_bar.open}")
        print(f"Window Latest - High: {last_bar.high}")
        print(f"Window Latest - Low: {last_bar.low}") 
        print(f"Window Latest - Close: {last_bar.close}")
        print(f"Window Latest - Volume: {last_bar.volume}")
        print("######## \n")
        print("INDICATOR VALUES")
        print(f"Previous MR: {prev_bar.mr}")
        print(f"Last Bar MR: {last_bar.mr}")
        print(f"Long Signal: {lg_sig}")
        print(f"Short Signal: {st_sig}")

        if position.size <= 0 and lg_sig:

            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(last_bar.close)

            order = {
                'order_type' : 'market',
                'size' : size,
                'side' : 'buy'
            }

            asset.create_order('mr_long', order)
        
        if position.size >= 0 and st_sig:
  
            pos_size = total_balance * settings['allocation']
            size = abs(position.size) + pos_size * asset.get_contract_rate(last_bar.close)

            order = {
                'order_type' : 'market',
                'size' : size,
                'side' : 'sell'
            }

            asset.create_order('mr_short', order)
            