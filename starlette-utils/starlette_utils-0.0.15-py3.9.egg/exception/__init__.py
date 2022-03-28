#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/7/20 9:42 下午
# @Author  : Hubert Shelley
# @Project  : microservice--registry-module
# @FileName: __init__.py.py
# @Software: PyCharm
"""
from starlette.exceptions import HTTPException
from tortoise.exceptions import BaseORMException

from .http_exception import http_exception, orm_exception
from .not_found import not_found
from .server_error import server_error

exception_handlers = {
    404: not_found,
    500: server_error,
    HTTPException: http_exception,
    BaseORMException: orm_exception,
}
