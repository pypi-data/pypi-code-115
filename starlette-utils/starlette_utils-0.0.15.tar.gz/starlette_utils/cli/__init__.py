#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/12/21 1:50 下午
# @Author  : Hubert Shelley
# @Project  : starlette_utils
# @FileName: __init__.py.py
# @Software: PyCharm
"""
from .cli import cli_main, cli
from .app import start_app
from .db import migrate
from .project import start_project

cli.add_command(migrate)
cli.add_command(start_app)
cli.add_command(start_project)

if __name__ == "__main__":
    cli_main()
