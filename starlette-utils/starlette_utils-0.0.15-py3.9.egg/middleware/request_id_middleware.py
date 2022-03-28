#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/5/18 下午2:52
# @Author  : Hubert Shelley
# @Project  : net_gateway_python
# @FileName: request_id_middleware.py
# @Software: PyCharm
"""
import typing
import uuid

from asgiref.sync import async_to_sync
from starlette.datastructures import Headers


class RequestIdMiddleware:
    def __init__(self, app, on_startup: typing.Sequence[typing.Union[typing.Awaitable, typing.Callable]] = None):
        self.app = app
        if on_startup:
            for on_startup_func in on_startup:
                if isinstance(on_startup_func(), typing.Awaitable):
                    async_to_sync(on_startup_func)()
                elif isinstance(on_startup_func, typing.Callable):
                    on_startup_func()

    async def __call__(self, scope, receiver, send):
        path = scope['path']
        headers = Headers(scope=scope)
        if not headers.get('request_id'):
            scope['headers'].append((b'request_id', uuid.uuid4().hex.encode()))
        scope['headers'].append((b'request_path', path.encode()))
        return await self.app(scope, receiver, send)
