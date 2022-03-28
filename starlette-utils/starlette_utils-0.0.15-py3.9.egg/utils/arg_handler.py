#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2022/1/13 21:10
# @Author  : Hubert Shelley
# @Project  : starlette_utils
# @FileName: arg_handler.py
# @Software: PyCharm
"""
import sys
import settings


def handle_args():
    args = sys.argv
    for arg in args:
        if arg.startswith('-p='):
            port_arg = arg.split('=')
            if port_arg.__len__() > 1:
                try:
                    settings.LOCAL_PORT = int(port_arg[1])
                except Exception as ex:
                    pass
