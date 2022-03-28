#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/12/21 4:42 下午
# @Author  : Hubert Shelley
# @Project  : starlette_utils
# @FileName: auth_middleware.py
# @Software: PyCharm
"""
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware

from starlette_utils.backends.auth_backends import AuthBackend

AuthMiddleware = Middleware(AuthenticationMiddleware, backend=AuthBackend())
