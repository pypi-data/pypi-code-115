#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/7/20 9:43 下午
# @Author  : Hubert Shelley
# @Project  : microservice--registry-module
# @FileName: not_found.py
# @Software: PyCharm
"""
from starlette_utils.response.response_results import not_found_result


async def not_found(request, exc):
    return not_found_result()
