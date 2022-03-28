# -*- coding: utf-8 -*-

from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider


class Network:
    PREDEFINED = {
        "mainnet": {"uri": "https://ctz.solidwallet.io", "nid": 3, },
        "sejong": {"uri": "https://sejong.net.solidwallet.io", "nid": 0x53,
                   "faucets": "cx6434bfdcb6b3ad4a4f5ced0075c73b9fea2a172c"},
        "lisbon": {"uri": "https://lisbon.net.solidwallet.io", "nid": 2,
                   "faucets": "cxcbece91fb181b754f906640a9746f361a3113641"},
        "berlin": {"uri": "https://berlin.net.solidwallet.io", "nid": 7,
                   "faucets": "cx760787ff9b4b337ac1f2bacd2bfe2ec42ef88c0d"},
    }

    def __init__(self, uri: str, nid: int = None):
        network = self.PREDEFINED.get(uri, None)
        if network is not None:
            self.uri = network["uri"]
            self.nid = network['nid']
        else:
            self.uri = uri
            self.nid = nid
        self.sdk = IconService(HTTPProvider(self.uri, 3, request_kwargs={"timeout": 20}))
