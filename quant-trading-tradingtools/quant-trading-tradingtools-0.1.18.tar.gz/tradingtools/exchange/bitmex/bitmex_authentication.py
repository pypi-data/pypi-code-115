# -*- coding: utf-8 -*-

import hashlib
import hmac
import time
from urllib.parse import urlparse

from requests import Request


def _generate_signature(
    secret: str, verb: str, url: str, nonce: int, data: (str, bytes, bytearray)
) -> str:
    """Generate a request signature compatible with BitMEX."""
    # Parse the url so we can remove the base and extract just the path.
    parsed_url = urlparse(url)
    path = parsed_url.path
    if parsed_url.query:
        path = path + '?' + parsed_url.query

    if isinstance(data, (bytes, bytearray)):
        data = data.decode('utf8')

    message = verb + path + str(nonce) + data

    signature = hmac.new(
        bytes(secret, 'utf8'), bytes(message, 'utf8'), digestmod=hashlib.sha256
    ).hexdigest()
    return signature


def rest_authentication(
    api_method: str,
    api_endpoint: str,
    api_key: str,
    api_secret: str,
    request_body: str = '',
) -> Request:
    request = Request(api_method, api_endpoint)

    expires = int(round(time.time()) + 5)
    request.headers['api-expires'] = str(expires)
    request.headers['api-key'] = api_key
    request.headers['api-signature'] = _generate_signature(
        api_secret, api_method, api_endpoint, expires, request_body
    )

    return request


def wss_authentication(api_key, api_secret, subaccount=None) -> dict:
    expires = int(round(time.time()) + 5)
    signature = _generate_signature(
        api_secret, 'GET', '/realtime', expires, ''
    )
    payload = {'op': 'authKeyExpires', 'args': [api_key, expires, signature]}

    return payload
