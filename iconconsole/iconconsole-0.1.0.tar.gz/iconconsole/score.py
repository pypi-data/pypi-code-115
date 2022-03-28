# -*- coding: utf-8 -*-
from typing import Optional, Tuple, Union

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import CallTransactionBuilder, DeployTransactionBuilder
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet

from iconconsole.base import BUILTIN_SCORE_ADDRESS_MAPPER, DEFAULT_STEP_LIMIT
from iconconsole.account import Account
from iconconsole.network import Network
from iconconsole.transaction import TransactionResult


class API:
    def __init__(self, name: str, _type: str, inputs: list, outputs: list, readonly: bool, payable: bool):
        self._name = name
        self._type = _type
        self._inputs = inputs
        self._outputs = outputs
        self._readonly = readonly
        self._payable = payable

    def __str__(self):
        mode = "readonly" if self._readonly else "writable"
        i = [f"{x['name']}: {x['type']}" for x in self._inputs]
        anno = ", ".join(i)
        return f"{mode} {self._name}({anno}){self.ret()}:"

    @property
    def name(self) -> str:
        return self._name

    @property
    def readonly(self) -> bool:
        return self._readonly

    def ret(self) -> str:
        if len(self._outputs) != 0:
            return f" -> {self._outputs[0]['type']}"
        else:
            return ""

    def _args_to_param(self, args, kwargs) -> dict:
        params = {}
        if len(args) > len(self._inputs):
            raise Exception("Invalid argument")
        for i, value in enumerate(args):
            x = self._inputs[i]
            params[x['name']] = value
        params.update(kwargs)
        return params

    def call(self, net: Network, to: str, args, kwargs,
             sender: KeyWallet = None, value: int = None, step_limit: int = None):
        if not self.is_function():
            raise Exception("This is not function type API")

        params = self._args_to_param(args, kwargs)
        if self._readonly:
            call = CallBuilder() \
                .to(to) \
                .method(self._name) \
                .params(params) \
                .build()
            return net.sdk.call(call, full_response=True)
        else:
            call = CallTransactionBuilder() \
                .to(to) \
                .nid(net.nid) \
                .method(self._name) \
                .value(value) \
                .step_limit(step_limit) \
                .params(params) \
                .build()
            signed_tx = SignedTransaction(call, sender)
            tx_hash = net.sdk.send_transaction(signed_tx)
            return TransactionResult(net, tx_hash)

    @classmethod
    def from_dict(cls, src: dict) -> 'API':
        return cls(
            name=src["name"],
            _type=src["type"],
            inputs=src.get("inputs", []),
            outputs=src.get("outputs", []),
            readonly=src.get("readonly", "0x0") == "0x1",
            payable=src.get("payable", "0x0") == "0x1",
        )

    def is_function(self) -> bool:
        return self._type == "function"


class Score(object):
    PREDEFINED = BUILTIN_SCORE_ADDRESS_MAPPER

    def __init__(self, net: Network, address: str, account: Account = None):
        self._address = self.PREDEFINED.get(address, address)
        self._net = net
        self._apis = {}
        self._set_methods()
        self._account: Account = account
        self._step_limit = DEFAULT_STEP_LIMIT
        self._value = 0

    def address(self) -> str:
        return self._address

    def get_account(self):
        return self._account

    def account(self, owner: Account) -> 'Score':
        self._account = owner
        return self

    def step_limit(self, step_limit: int) -> 'Score':
        self._step_limit = step_limit
        return self

    def apis(self) -> list:
        return [str(x) for x in self._apis.values()]

    @classmethod
    def deploy(
            cls,
            net: Network,
            account: Account,
            score_path: str,
            params: dict = {},
            step_limit: int = 10000 * DEFAULT_STEP_LIMIT,
    ) -> Tuple[Optional['Score'], TransactionResult]:
        score_address, tx_result = cls._deploy(net, account, score_path, cls.PREDEFINED.get("chain"), params, step_limit)
        return Score(net, score_address, account), tx_result

    def update(
            self,
            score_path: str,
            params: dict = {},
            step_limit: int = 10000 * DEFAULT_STEP_LIMIT,
    ) -> TransactionResult:
        _, tx_result = self._deploy(self._net, self._account, score_path, self.address(), params, step_limit)
        return tx_result

    @staticmethod
    def _deploy(
            net: Network,
            account: Account,
            score_path: str,
            to: Union['Score', str],
            params: dict = {},
            step_limit: int = 10000 * DEFAULT_STEP_LIMIT,
    ) -> Tuple[str, TransactionResult]:
        content_type = "application/java"
        deploy = DeployTransactionBuilder() \
            .from_(account.address()) \
            .to(to) \
            .step_limit(step_limit) \
            .nid(net.nid) \
            .nonce(100) \
            .content_type(content_type) \
            .content(generate_deploy_data(content_type, score_path)) \
            .params(params) \
            .build()

        print(deploy.to_dict())
        signed_tx = SignedTransaction(deploy, account.wallet())
        print(signed_tx.signed_transaction_dict)
        tx_result = net.sdk.send_transaction_and_wait(signed_tx)
        print(tx_result)
        return tx_result.get("scoreAddress", None), TransactionResult(net, tx_result['txHash'])

    def _call(self, func: str, args, kwargs):
        api: API = self._apis[func]
        return api.call(self._net, self._address, args, kwargs, self._account.wallet(), self._value, self._step_limit)

    def _set_methods(self):
        resp = self._net.sdk.get_score_api(self.address())
        methods = {}
        for r in resp:
            api = API.from_dict(r)
            if api.is_function():
                methods[api.name] = api
        self._apis = methods

        for m in methods.values():
            self._bind_method(m)

    def _bind_method(self, api: API):
        def f(*args, **kwargs):
            return self._call(f.__name__, args, kwargs)

        f.__name__ = api.name
        # f.__annotations__ = api.annotations()
        setattr(self, api.name, f)


def generate_deploy_data(content_type: str, path: str) -> bytes:
    if content_type == "application/zip":
        return gen_deploy_data_content(path)
    else:
        f = open(path, "rb")
        return f.read()
