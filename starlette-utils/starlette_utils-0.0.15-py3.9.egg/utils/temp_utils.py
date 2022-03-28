#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2022/1/13 20:36
# @Author  : Hubert Shelley
# @Project  : starlette_utils
# @FileName: temp_utils.py
# @Software: PyCharm
"""
import os

from .decorators import thread_decorator


@thread_decorator
def delete_temp_dirs():
    """
    清理运行目录中以下划线开始的目录

    :return:
    """
    _temp_path = os.path.abspath(__file__)
    for dir in os.listdir():
        if os.path.isdir(dir) and dir.startswith('_'):
            if dir in _temp_path:
                continue
            os.popen(f'rm -rf {dir}')
            print(f'clear temp dir: {dir}')
