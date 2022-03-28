from requests import Session

from tradingtools.exchange.ftx import FTXExchange, rest_authentication as ftx_rest

__all__ = ['ftx_convert_usd_to_btc', 'ftx_usd_to_btc_spot', 'ftx_usd_to_btc_otc']


def ftx_convert_usd_to_btc(api_key, api_secret, subaccount=None, spot=True):
    headers = None
    if subaccount:
        headers = {'FTX-SUBACCOUNT': subaccount}
    exchange = FTXExchange(api_key=api_key, api_secret=api_secret, headers=headers)

    wallets = exchange.get_wallets()
    wallets = next(iter(wallets.values()))

    for wallet in wallets:
        if wallet['asset'] != 'USD':
            continue

        print(wallet)
        if wallet['available']:
            if spot:
                ftx_usd_to_btc_spot(exchange, wallet)
            else:
                ftx_usd_to_btc_otc(exchange, wallet, api_key, api_secret, subaccount=subaccount)


def ftx_usd_to_btc_spot(exchange, wallet):
    ticker = exchange.ccxt_obj.fetch_ticker('BTC/USD')

    if wallet['available'] > 0:
        size = abs(wallet['available'] / ticker['ask'])
        side = 'buy'
    elif wallet['available'] < 0:
        size = abs(wallet['available'] / ticker['bid'])
        side = 'sell'
    else:
        print('Available USD balance is 0. No conversion done.')
        print(wallet)
        return

    print(f'order size: {side}')

    if size < ticker['info']['minProvideSize']:
        print('Available USD balance is too low to market order BTC')
        print(size)
    else:
        print('Converting USD gains/loss to BTC via spot market')
        response = exchange.post_order('BTC/USD', 'market', side, size)
        print(response)


def ftx_usd_to_btc_otc(exchange, wallet, api_key, api_secret, subaccount=None):
    raise NotImplementedError
    #
    # session = Session()
    # payload = {
    #     'fromCoin': 'USD',
    #     'toCoin': 'BTC',
    #     'size': wallet['available']
    # }
    #
    # # request OTC quote
    # request = ftx_rest('POST', f'{exchange.base_rest_url}/otc/quotes',api_key, api_secret, subaccount=subaccount, data=payload)
    # response = session.send(request)
    # response.raise_for_status()
    # response = response.json()
    # if response['success']:
    #     otc_quote = response['result']
    #     print(otc_quote)
    # else:
    #     raise Exception # throw specific exception for failed OTC quote
    #
    # # check OTC quote status
    # request = ftx_rest('GET', f'{exchange.base_rest_url}/otc/quotes/{otc_quote["quoteId"]}', api_key, api_secret, subaccount=subaccount)
    # response = session.send(request)
    # response.raise_for_status()
    # response = response.json()
    # if response['success']:
    #     otc_status = response['result']
    #     print(otc_status)
    # else:
    #     raise Exception # throw specific exception for failed OTC quote status
    #
    # # Accept OTC quote
    # payload = None
    # # payload = {'quoteId': otc_quote['quoteId']}
    # request = ftx_rest('POST', f'{exchange.base_rest_url}/otc/quotes/{otc_quote["quoteId"]}/accept', api_key, api_secret, subaccount=subaccount, data=payload)
    # response = session.send(request)
    # response.raise_for_status()
    # response = response.json()
    # if response['success']:
    #     # check OTC quote status
    #     request = ftx_rest('GET', f'{exchange.base_rest_url}/otc/quotes/{otc_quote["quoteId"]}', api_key, api_secret, subaccount=subaccount)
    #     response = session.send(request)
    #     response.raise_for_status()
    #     response = response.json()
    #     if response['success']:
    #         otc_status = response['result']
    #         print(otc_status)
    #     else:
    #         raise Exception  # throw specific exception for failed OTC quote status
    # else:
    #     raise Exception # throw specific exception for failed accept OTC quote
