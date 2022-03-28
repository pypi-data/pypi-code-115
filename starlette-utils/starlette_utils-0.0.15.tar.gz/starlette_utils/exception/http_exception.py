#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/7/20 9:46 下午
# @Author  : Hubert Shelley
# @Project  : microservice--registry-module
# @FileName: http_exception.py
# @Software: PyCharm
"""
import traceback

from starlette_utils.exception.exceptions import ValidationError
import re

from starlette_utils.response.response_results import error_result


async def http_exception(request, exc):
    print(traceback.format_exc())
    if isinstance(exc, ValidationError):
        return error_result(message=exc.detail, status_code=exc.status_code, code=exc.default_code, data=exc.data)
    return error_result(message=exc.detail or '请求失败，系统繁忙中！', status_code=exc.status_code, code=exc.default_code)


async def orm_exception(request, exc):
    print(traceback.format_exc())
    try:
        _exc_str = exc.args[0].args[1]
        _slot_str_list = re.findall(r"'.*?'", _exc_str)
        # exc_str = Translator(from_lang="english", to_lang="chinese").translate(re.sub(r"'.*?'", '{}', _exc_str)).format(
        #     *_slot_str_list)
        exc_str = ','.join(_slot_str_list)
    except Exception as e:
        exc_str = exc.__str__()
    return error_result(message=exc_str, status_code=502)
