#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2022/1/13 20:48
# @Author  : Hubert Shelley
# @Project  : starlette_utils
# @FileName: decorators.py
# @Software: PyCharm
"""
import threading
from functools import wraps


def thread_decorator(func):
    @wraps(func)
    def inner(*args, **kwargs):
        _thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        _thread.setDaemon(True)
        _thread.start()

    return inner
