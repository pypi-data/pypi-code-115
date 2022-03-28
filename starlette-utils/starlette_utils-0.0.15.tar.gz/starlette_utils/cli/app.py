#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/12/21 1:59 下午
# @Author  : Hubert Shelley
# @Project  : starlette_utils
# @FileName: app.py
# @Software: PyCharm
"""
import os

import click

from .cli import cli


def add_app(name):
    root_path = f'apps/{name}'
    os.makedirs(root_path)
    with open(f'{root_path}/__init__.py', 'w') as f:
        f.write("")
    with open(f'{root_path}/{name}_routes.py', 'w') as f:
        f.write("""from starlette.routing import Mount


routes = [
]
        """)
    with open(f'{root_path}/views.py', 'w') as f:
        f.write("""from starlette_utils.response import api_endpoints""")
    with open(f'{root_path}/models.py', 'w') as f:
        f.write('''from starlette_utils.models import Model
from tortoise import fields


class TemplateModel(Model):
    """
    模型模板
    """
    
    name = fields.CharField(max_length=255, description='姓名')
    age = fields.SmallIntField(description='年龄')''')
    with open(f'{root_path}/serializers.py', 'w') as f:
        f.write('''from marshmallow import fields

from starlette_utils.schemas.schema import BaseSchema
from . import models


class TemplateSerializer(BaseSchema):
    """
    测试序列化器
    """
    name = fields.String(title='姓名')
    size = fields.Integer(title='年龄')

    class Meta:
        model = models.TemplateModel''')
    with open(f'{root_path}/filters.py', 'w') as f:
        f.write('''from marshmallow import fields

from starlette_utils.schemas.schema import BaseSchema


class TemplateFilter(BaseSchema):
    name = fields.String()''')


@cli.command()
@click.argument('name')
def start_app(name: str):
    """
    创建应用

    :param name: 应用名称
    :return:
    """
    click.echo(f'app {name} creating')
    # 添加应用
    add_app(name)
    click.secho(f'{name} is created!', err=True, fg='green')
