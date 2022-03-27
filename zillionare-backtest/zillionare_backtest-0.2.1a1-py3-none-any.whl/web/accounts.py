from backtest.common.errors import AccountConflictError
from backtest.trade.broker import Broker


class Accounts:
    _brokers = {}

    def get_broker(self, token):
        return self._brokers.get(token)

    def is_valid(self, token: str):
        return token in self._brokers

    def create_account(self, token: str, name: str, capital: float, commission: float):
        """创建新账户

        如果指定的token已存在，但name不相同，则认为是冲突，创建失败。
        """
        if token not in self._brokers:
            broker = Broker(name, capital, commission)
            self._brokers[token] = broker
        else:
            broker = self._brokers[token]

            if broker.name != name:
                msg = f"{token[-4:]}已被{broker.name}账户使用，不能创建{name}账户"
                raise AccountConflictError(msg)

        return {
            "account_name": name,
            "token": token,
            "account_start_date": broker.account_start_date,
            "cash": broker.cash,
        }

    def list_accounts(self):
        return [
            {
                "account_name": broker.account_name,
                "token": token,
                "account_start_date": broker.account_start_date,
                "cash": broker.cash,
            }
            for token, broker in self._brokers.items()
        ]
