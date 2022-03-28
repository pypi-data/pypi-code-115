# -*- coding: utf-8 -*-

import hmac
import time

from requests import Request


def rest_authentication(
    api_method: str,
    api_endpoint: str,
    api_key: str,
    api_secret: str,
    subaccount: str = None,
) -> Request:
    ts = int(time.time() * 1000)
    request = Request(api_method, api_endpoint)
    prepared = request.prepare()
    signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
    signature = hmac.new(
        api_secret.encode(), signature_payload, 'sha256'
    ).hexdigest()

    request.headers['FTX-KEY'] = api_key
    request.headers['FTX-SIGN'] = signature
    request.headers['FTX-TS'] = str(ts)

    if subaccount:
        request.headers['FTX-SUBACCOUNT'] = 'my_subaccount_nickname'

    return request


def wss_authentication(
    api_key: str, api_secret: str, subaccount: str = None
) -> dict:
    ts = int(time.time() * 1000)
    signature_payload = f'{ts}websocket_login'.encode()
    signature = hmac.new(
        api_secret.encode(), signature_payload, 'sha256'
    ).hexdigest()

    payload = {
        'args': {'key': api_key, 'sign': signature, 'time': ts},
        'op': 'login',
    }

    if subaccount:
        payload['args']['subaccount'] = subaccount

    return payload
