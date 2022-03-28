#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/12/21 1:59 下午
# @Author  : Hubert Shelley
# @Project  : starlette_utils
# @FileName: db.py
# @Software: PyCharm
"""
import asyncio

import click
from aerich import Command
from smart7_orm.utils import discover_models, get_connection_url

from .cli import cli


def get_config():
    config = {
        "connections": {
            "default": get_connection_url(),
        },
        "apps": {
            "models": {
                "models": ['apps.files.models', discover_models],
                "default_connection": "default",
            },
        },
    }
    return config


TORTOISE_ORM = get_config()


async def init_db(command: Command):
    try:
        await command.init()
    except Exception as e:
        pass
    try:
        await command.init_db(True)
    except Exception as e:
        pass
    try:
        await command.migrate()
    except Exception as e:
        pass
    try:
        await command.upgrade()
    except Exception as e:
        pass


@cli.command()
def migrate():
    click.echo('migrate starting')
    config = get_config()
    command = Command(tortoise_config=config, app='models')
    print(config)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db(command))
    loop.close()
