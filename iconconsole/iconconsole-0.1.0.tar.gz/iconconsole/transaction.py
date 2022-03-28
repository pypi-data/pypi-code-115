# -*- coding: utf-8 -*-
from iconconsole.network import Network


class TransactionResult:
    def __init__(self, net: Network, tx_hash: str):
        self._net = net
        self._hash = tx_hash

    def net(self) -> Network:
        return self._net

    def hash(self) -> str:
        return self._hash

    def transaction(self) -> dict:
        return self._net.sdk.get_transaction(self._hash, True)

    def result(self) -> dict:
        return self._net.sdk.get_transaction_result(self._hash, True)

    def trace(self) -> dict:
        return self._net.sdk.get_trace(self._hash)
