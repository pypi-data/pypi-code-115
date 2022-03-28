# -*- coding: utf-8 -*-

from typing import Union

from iconsdk.builder.transaction_builder import Transaction, TransactionBuilder, MessageTransactionBuilder
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet

from iconconsole.base import DEFAULT_STEP_LIMIT
from iconconsole.network import Network
from iconconsole.transaction import TransactionResult


class Account:
    def __init__(self, keystore: str = None, password: str = None, net: Network = None) -> 'Account':
        if keystore is None:
            wallet = KeyWallet.create()
        else:
            wallet = KeyWallet.load(keystore, password)
        self._wallet = wallet
        self._net = net

    def save_keystore(self, path: str, password: str = "iconconsole"):
        self._wallet.store(path, password)

    def get_network(self) -> Network:
        return self._net

    def network(self, net: Network) -> 'Account':
        self._net = net
        return self

    def wallet(self) -> KeyWallet:
        return self._wallet

    def address(self) -> str:
        return self._wallet.get_address()

    def balance(self) -> int:
        return self._net.sdk.get_balance(self.address())

    def transfer(self, to: Union['Account', str], value: int, step_limit: int = DEFAULT_STEP_LIMIT) -> TransactionResult:
        request = {
            "to": get_address(to),
            "value": value,
            "nid": self._net.nid,
            "step_limit": step_limit,
        }
        return self._send(TransactionBuilder.from_dict(request).build())

    def message(self, to: Union['Account', str], message: str, value: int = 0, step_limit: int = DEFAULT_STEP_LIMIT) -> TransactionResult:
        request = {
            "to": get_address(to),
            "value": value,
            "nid": self._net.nid,
            "step_limit": step_limit,
            "data": message
        }
        return self._send(MessageTransactionBuilder.from_dict(request).build())

    def _send(self, tx: Transaction) -> TransactionResult:
        signed_tx = SignedTransaction(tx, self._wallet)
        print(signed_tx.signed_transaction_dict)
        tx_hash = self._net.sdk.send_transaction_and_wait(signed_tx)
        return TransactionResult(self._net, tx_hash)


def get_address(addr: Union[Account, str]) -> str:
    if isinstance(addr, Account):
        return addr.address()
    return addr
