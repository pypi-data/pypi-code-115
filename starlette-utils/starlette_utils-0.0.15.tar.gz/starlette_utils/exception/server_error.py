#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/7/20 9:43 下午
# @Author  : Hubert Shelley
# @Project  : microservice--registry-module
# @FileName: server_error.py
# @Software: PyCharm
"""
from starlette.exceptions import HTTPException

from starlette_utils.response.response_results import error_result


async def server_error(request, exc):
    if isinstance(exc, HTTPException):
        return error_result(message=exc.detail, status_code=exc.status_code)
    return error_result(message=exc.__str__(), status_code=500)


def server_error_handler(request, exc):
    if isinstance(exc, HTTPException):
        return error_result(message=exc.detail, status_code=exc.status_code)
    return error_result(message=exc.__str__(), status_code=502)
