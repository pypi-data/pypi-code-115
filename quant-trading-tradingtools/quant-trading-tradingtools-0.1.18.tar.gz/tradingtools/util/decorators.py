# -*- coding: utf-8 -*-

import functools

import websockets

__all__ = ['websocket_error_handler']


def websocket_error_handler(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception:
            raise

    return wrapper
