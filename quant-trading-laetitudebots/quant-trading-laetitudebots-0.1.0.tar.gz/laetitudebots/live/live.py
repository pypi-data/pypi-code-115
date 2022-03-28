from collections import defaultdict
from copy import deepcopy

import pandas as pd
from tradingtools.exchange import exchange_factory

from laetitudebots.asset import Asset, BitmexAsset
from laetitudebots.factors import Factors
from laetitudebots.model import Config, Position

# for cleaning order kwargs before post_order
ORDER_KWARGS = ['side', 'size', 'price', 'trigger_price', 'order_type']


class Live:
    initialize = None
    process = None
    ohlcv = None
    factors = None
    wallets = {}

    def __init__(self, key):
        self.config_obj = Config.get(key)
        self.config = self.config_obj.data
        self.context = self.config['context']
        self.exchange = exchange_factory.get_exchange(
            exchange_name=self.config['exchange'],
            api_key=self.config['api_key'],
            api_secret=self.config['api_secret'],
            test=self.config.get('is_test', True),
            headers=self.config.get('headers', None),
        )

    def set_strategy(self, initialize=lambda *args: None,
                     process=lambda *args: None):
        self.initialize = initialize
        self.process = process

    def run(self):
        window_length = self.config.get('window_length', 2)
        print('Downloading data from exchange')
        self.ohlcv = self.download_ohlcv()

        self.factors = Factors(self.ohlcv, window_length=window_length)

        print('Downloading BTC balance from exchange')
        self.calc_balance()

        print('Initializing assets from DynamoDB')
        assets = self.initialize_assets()

        print('Initializing strategy...')
        self.initialize(self.factors, self.context)

        print('Running strategy...')
        self.process(self.factors.latest_window, assets, self.context)

        print('Processing orders...')
        self.process_orders(assets, self.context)

        print('Updating context...')
        self.config_obj.save()
        print('Strategy run done.')

    def download_ohlcv(self):
        config_assets = self.context['assets']
        timeframe = f"{self.config['time_interval']}{self.config['time_unit']}"
        lookback = self.config['lookback']

        dfs = {}

        downloaded_collateral = {}
        clients = {
            self.config['exchange']: self.exchange
        }
        for symbol in config_assets:
            asset = config_assets[symbol]
            exchange = asset['exchange']
            if exchange not in clients:
                clients[exchange] = exchange_factory.get_exchange(exchange)
            print(f'Downloading {symbol} {timeframe} data with {lookback} lookback from {exchange}')

            exchange_client = clients[exchange]
            df = exchange_client.get_ohlcv(symbol, timeframe, limit=lookback)
            print(df.head())
            print(df.tail())
            print(f'Number of rows: {df.shape[0]}')

            # check if you have to download collateral data
            if asset.get('collateral'):
                # All collateral data will be downloaded from Binance for
                # simplicity.
                exch = 'binance'
                if exch not in clients:
                    clients[exch] = exchange_factory.get_exchange(exch)
                binance_client = clients[exch]
                coll = asset.get('collateral') + '/USDT'

                # caching
                if coll in downloaded_collateral:
                    dfs[('collateral', symbol)] = downloaded_collateral[coll]
                else:
                    print(f'...Downloading collateral data {coll}')
                    coll_close = binance_client.get_ohlcv(coll, timeframe,
                                                          limit=lookback)
                    downloaded_collateral[coll] = coll_close.close

                    dfs[('collateral', symbol)] = coll_close.close

            for col in df.columns:
                dfs[(col, symbol)] = df[col]

        return pd.DataFrame(dfs)

    def calc_balance(self):
        acct_balances = self.exchange.get_wallets()
        # check if it's using subaccounts or not
        # ? shared balance should be the default behaviour
        is_shared_balance = self.context.get('is_shared_balance')

        if is_shared_balance:
            for acc_wallets in acct_balances.values():
                for wallet in acc_wallets:
                    bal = wallet['total']
                    asset = wallet['asset']
                    if asset == 'BTC':
                        # NOTE: context['balance'] now refers to
                        # BTC balance ONLY
                        self.context['balance'] = bal
                    else:
                        # this implies single account only
                        # otherwise values will be overriden by the latest
                        # account wallet
                        self.wallets[asset] = bal

            print(f'Balance - BTC{self.context["balance"]}')
        else:
            # ? permanently remove support for subaccounts?
            config_assets = self.context['assets']
            for symbol in config_assets:
                asset = config_assets[symbol]
                # subaccount name should be present in context
                subaccount = asset['subaccount']
                acc_wallets = acct_balances[subaccount]
                for wallet in acc_wallets:
                    if wallet['asset'] == 'BTC':
                        asset['balance'] = wallet['total']
                        break
            print(f'Balance - {config_assets} BTC')

    def initialize_assets(self):
        config_assets = self.context['assets']
        print(f'Config assets - {config_assets}')
        exchange = self.config['exchange']
        print(f'Downloading open positions from {exchange}')
        positions = self.get_positions()
        print(f'Downloading open orders from {exchange}')
        orders = self.get_orders()

        if exchange.lower() == 'bitmex':
            asset_class = BitmexAsset
        else:
            asset_class = Asset

        assets = {}
        for symbol, variables in config_assets.items():
            kwargs = {
                'symbol': symbol,
                'collateral': variables.get('collateral'),
                'asset_type': variables.get('type', 'futures')
            }

            asset = asset_class(**kwargs)
            # check if symbol has current positions
            if symbol in positions:
                pos = positions[symbol]
                asset.position = self.initialize_position(asset, pos)
            else:
                asset.position = Position(symbol)
                if asset.type == 'spot':
                    # lot size is required so we
                    # know when to consider "no" position
                    # for example, XRP has a lot size of 1, so an XRP
                    # balance of .99 should be considered as no position
                    wallet_key = variables['spot_symbol']
                    size = self.wallets[wallet_key]
                    min_lot_size = self.exchange.size_inc(symbol)
                    if size > min_lot_size:
                        side = 'buy'  # spot is always buy!
                        close = self.ohlcv.close[asset.symbol].iloc[-1]
                        asset.position.size = size
                        asset.position.side = side
                        asset.position.avg_price = float('nan')  # unavailable
                        asset.position.unrealised_pnl = asset.pnl_calculator(
                            size, close, None, None,
                        )

            asset.orders = orders.get(symbol, {})

            assets[symbol] = asset
        print(f'Assets initialized - {assets}')
        return assets

    def get_positions(self):
        """
        :return: dict
        positions = {
            'BTC/USD': {...},
            'ETH/USD': {...}
        }
        """
        res = {}
        positions = self.exchange.get_positions()
        config_assets = self.context['assets']

        for pos in positions:
            # get symbol
            symbol = pos['symbol']
            for sym, asset in config_assets.items():
                # e.g. when you download from binance and execute in bitmex
                # 'ETH/BTC': {
                #     ...
                #     'symbol_map': 'ETHU20',
                # }
                if asset.get('symbol_map') == symbol:
                    symbol = sym
                    break

            res[symbol] = pos
        print(f'Positions -\n{res}')
        return res

    def initialize_position(self, asset, pos):
        last = self.factors.latest_window.latest(asset.symbol)
        position = Position(asset.symbol)
        position.size = pos['size']
        position.side = pos['side']
        position.avg_price = pos['avg_price']
        if asset.collateral:
            collateral = last.collateral
        else:
            collateral = None
        position.unrealised_pnl = asset.pnl_calculator(
            pos['size'], last.close, pos['avg_price'], collateral
        )

        return position

    def get_orders(self):
        """
        :return: dict
        orders = {
            'BTC/USD': {
                'high_pivot': {
                    'order_type': 'stop',
                    ...
                },
                'low_pivot': {...}
            },
            'ETH/USD': {
                'low_pivot': {...}
        }
        """
        res = defaultdict(dict)
        config_assets = self.context['assets']
        print(f'Assets in config - {config_assets}')
        orders = self.exchange.get_open_orders()
        print(f'orders response -   {orders}')

        exchange_open_orders = []
        for order in orders:
            # get symbol
            symbol = order['symbol']
            for sym, asset in config_assets.items():
                # e.g. when you download from binance and execute in bitmex
                # 'ETH/BTC': {
                #     ...
                #     'symbol_map': 'ETHU20',
                # }
                if asset.get('symbol_map') == symbol:
                    symbol = sym
                    break
            # get order id
            order_id = str(order['id'])
            # check what is the client id for that order id
            client_id_mapper = config_assets[symbol]['orders']
            client_id = client_id_mapper.get(order_id)

            if client_id is not None:
                res[symbol][client_id] = order
            else:
                # log warning here
                print(f'Untracked order - {order}')

            exchange_open_orders.append(order_id)
        print(f'Open orders - {exchange_open_orders}')
        # remove orders that are already filled / cancelled
        # e.g., a limit order that was filled will not be
        # automatically remove from config asset in dynamo
        # so you have to manually remove it here
        for asset in config_assets.values():
            order_copies = deepcopy(asset['orders'])
            for order_id in order_copies.keys():
                if order_id not in exchange_open_orders:
                    print(f'Order filled/cancelled. Removing order from DynamoDB - {asset["orders"]}')
                    asset['orders'].pop(order_id)

        print('......Orders downloaded')

        return res

    def process_orders(self, assets, context):
        # TODO retry

        for symbol, asset in assets.items():
            context_asset = context['assets'][symbol]
            order_symbol = context_asset.get('symbol_map', symbol)
            client_id_mapper = {}
            # process orders to cancel first
            for order in asset.orders_to_cancel:
                print('...Cancelling order')
                print(f"...{order_symbol}, {order}")
                order['symbol'] = order_symbol
                resp = self.exchange.cancel_order(order['id'],
                                                  details=order)
                print(f"....{resp}")

            for client_id, order in asset.orders.items():
                # add error handling here
                print('...Posting order')
                print(f"...{order_symbol}, {order}")
                order_details = {}
                for kwarg in ORDER_KWARGS:
                    order_details[kwarg] = order.get(kwarg)

                exchange_order = None
                order_id = order.get('id')
                if order_id:
                    try:
                        exchange_order = self.exchange.get_open_order(order_id)
                    except ValueError as e:
                        print('Order is not in exchange. Creating new order.')
                        print(f'Exchange API response message - {e}')
                    except Exception as e:
                        print(f'Unknown exception raised when fetching order - {e}')
                        raise

                if exchange_order is not None:
                    print('Order is still active')
                    print(f'Order in exchange - {exchange_order}')
                    resp = exchange_order
                else:
                    resp = self.exchange.post_order(symbol=order_symbol,
                                                **order_details)
                # get order id here
                if order['order_type'] != 'market':
                    print('...Order saved to context')
                    client_id_mapper[str(resp['id'])] = client_id
                    print(f"...{resp['id']}, {client_id}")

            # update context asset for asset
            context_asset['orders'] = client_id_mapper
            print('...Orders')
            print(f"...{context_asset['orders']}")
