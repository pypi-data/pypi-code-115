#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/12/21 2:01 下午
# @Author  : Hubert Shelley
# @Project  : starlette_utils
# @FileName: cli.py
# @Software: PyCharm
"""
import click


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli():
    pass


def cli_main():
    cli()
