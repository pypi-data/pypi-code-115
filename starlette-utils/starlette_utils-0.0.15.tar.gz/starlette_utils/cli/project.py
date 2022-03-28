#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/12/21 1:59 下午
# @Author  : Hubert Shelley
# @Project  : starlette_utils
# @FileName: project.py
# @Software: PyCharm
"""
import os

import click

from .cli import cli
from ..utils import secret


def edit_idea_project_name(old_name, new_name):
    for filename in ['modules.xml', 'workspace.xml']:
        with open(f'.idea/{filename}', '+r') as f:
            t = f.read()
            t = t.replace(old_name, new_name)

            # 读写偏移位置移到最开始处
            f.seek(0, 0)
            f.write(t)

            # 设置文件结尾 EOF
            f.truncate()
    with open('.idea/.name', 'w') as f:
        f.write(new_name)


def add_routes(_dir, project_name: str):
    root_path = f'{_dir}/{project_name}/routes'
    os.makedirs(root_path)
    with open(f'{root_path}/__init__.py', 'w') as f:
        f.write("""from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from starlette_utils.schemas.views import OpenApi, swagger_view
from .web_routes import web_routes
from .api_routes import api_routes
import settings

routes = [
]

routes.extend(web_routes)
if settings.DEBUG:
    routes.append(Mount(f'/{settings.APP_NAME}/v{settings.APP_VERSION}', routes=api_routes))
    routes.append(Route(path='/swagger/', endpoint=swagger_view))
    routes.extend([
        Mount('/static', app=StaticFiles(directory='static', packages=['starlette_utils.schemas']), name="static"),
        Route("/schema", endpoint=OpenApi.get_schemas(
            [Mount(f'/{settings.APP_NAME}/v{settings.APP_VERSION}', routes=api_routes)]),
              include_in_schema=False),
    ])
else:
    routes.extend(api_routes)
""")
    with open(f'{root_path}/api_routes.py', 'w') as f:
        f.write("""from starlette.routing import Mount


api_routes = [
]
        """)
    with open(f'{root_path}/web_routes.py', 'w') as f:
        f.write("""from starlette.routing import Route


web_routes = [
]
        """)


def add_running_command(_dir: str, project_name: str):
    root_path = f'{_dir}/{project_name}'
    with open(f'{root_path}/main.py', 'w') as f:
        f.write(f"""from starlette.applications import Starlette
from tortoise.contrib.starlette import register_tortoise

import settings
from starlette_utils.middleware.request_id_middleware import RequestIdMiddleware
from migrate import get_config
from starlette_utils.exception import exception_handlers
from .routes import routes


async def startup_task():
    print('startup_task')
    register_tortoise(
        app, config=get_config(), generate_schemas=False
    )
    print('orm started')
    pass


app = Starlette(
    debug=settings.DEBUG,
    routes=routes,
    middleware=[],
    exception_handlers=exception_handlers,
    on_startup=[
        startup_task
    ],
    on_shutdown=[
    ],
)

# 自动生成请求ID
# application = RequestIdMiddleware(app, on_startup=[loop_registry_start])
# 不生成请求ID
application = app
            """)

    with open('run.py', 'w') as f:
        f.write(f"""import uvicorn
from starlette_utils.utils.arg_handler import handle_args
from starlette_utils.utils.temp_utils import delete_temp_dirs

import settings
from main import application

if __name__ == '__main__':
    delete_temp_dirs()

    handle_args()

    uvicorn.run(
        '{project_name}.main:application',
        host="0.0.0.0",
        port=settings.LOCAL_PORT,
        log_level="info",
        # loop='uvloop',
        http='httptools',
        ws='none',
        debug=settings.DEBUG,
        reload=settings.DEBUG,
    )""")


def add_settings():
    with open(f'settings.py', 'w') as f:
        f.write("""from starlette.config import Config
from starlette.datastructures import Secret, CommaSeparatedStrings

config = Config(".env")

DEBUG = config('DEBUG', cast=bool, default=False)
APP_NAME = config('APP_NAME', cast=str, default='app')
APP_VERSION = config('APP_VERSION', cast=int, default=0)
SECRET_KEY = config('SECRET_KEY', cast=Secret)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=CommaSeparatedStrings)
LOCAL_HOST = config('LOCAL_HOST', cast=str, default='127.0.0.1')
LOCAL_PORT = config('LOCAL_PORT', cast=int, default=9001)
MANAGE_PORT = config('MANAGE_PORT', cast=int, default=8001)

LOG_MAX_SIZE = config('LOG_MAX_SIZE', cast=int, default=5) * 1024 * 1024
LOG_BACKUP_COUNT = config('LOG_BACKUP_COUNT', cast=int, default=5)

DB_HOST = config('DB_HOST', cast=str, default='127.0.0.1')
DB_NAME = config('DB_NAME', cast=str, default='project_template')
DB_USER = config('DB_USER', cast=str, default='root')
DB_PASSWORD = config('DB_PASSWORD', cast=str, default='DB_PASSWORD')
DB_PORT = config('DB_PORT', cast=int, default=3306)
REGISTER_HOST = config('REGISTER_HOST', cast=str, default='http://127.0.0.1:8005')

OSS_TYPE = config('OSS_TYPE', cast=str, default='')
OSS_KEY_ID = config('OSS_KEY_ID', cast=str, default='')
OSS_KEY_SECRET = config('OSS_KEY_SECRET', cast=str, default='')
OSS_ENDPOINT = config('OSS_ENDPOINT', cast=str, default='')
OSS_BUCKET_NAME = config('OSS_BUCKET_NAME', cast=str, default='')

# sqlite setting
database = {
    "db": 'SQLite',
    "path": "test_table.db",
}
# db setting
# db type: 'MySQL', ...
# database = {
#     'db': 'MySQL',
#     'host': DB_HOST,
#     'db_name': DB_NAME,
#     'username': DB_USER,
#     'password': DB_PASSWORD,
#     'port': DB_PORT,
# }

JWT_ISSUER = config('JWT_ISSUER', cast=str, default='')
JWT_PASS_TIME = config('JWT_PASS_TIME', cast=int, default=7200)
JWT_REFRESH_PASS_TIME = config('JWT_REFRESH_PASS_TIME', cast=int, default=604800)

AUTH_URL = config('AUTH_URL', cast=str, default='http://127.0.0.1:8005/')
        """)


def add_readme():
    pass


def add_migrate():
    with open(f'migrate.py', 'w') as f:
        f.write("""import asyncio

from aerich import Command
from smart7_orm.utils import discover_models, get_connection_url


def get_config():
    config = {
        "connections": {
            "default": get_connection_url().replace('///', '//'),
        },
        "apps": {
            "models": {
                "models": ["aerich.models", *discover_models()],
                "default_connection": "default",
            },
        },
    }
    return config


TORTOISE_ORM = get_config()


async def init_db():
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


if __name__ == '__main__':
    config = get_config()
    command = Command(tortoise_config=config, app='models')
    print(config)
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(init_db())
    # loop.close()
    """)


def add_app_dir(_dir):
    root_path = f'{_dir}/apps'
    os.makedirs(root_path)
    with open(f'{root_path}/__init__.py', 'w') as f:
        f.write("")
    statics_path = f'{_dir}/statics'
    os.makedirs(statics_path)


def add_env_template(project_name: str):
    with open(f'.env.template', 'w') as f:
        f.write(f"""# Don't commit this to source control.
# Eg. Include ".env" in your `.gitignore` file.
# 应用名称
APP_NAME={project_name}
# 应用版本
APP_VERSION=1
DEBUG=True
SECRET_KEY={secret.get_secrets_key(64)}
ALLOWED_HOSTS=127.0.0.1
LOCAL_HOST=127.0.0.1
LOCAL_PORT=8000
# 统一认证url
AUTH_URL=https://AUTH_URL.com/

[DB]
DB_NAME={project_name}
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306

[JWT]
JWT_ISSUER=template_iss
# 过期时间（秒）
JWT_PASS_TIME=7200
# 续签时间（秒）
JWT_REFRESH_PASS_TIME=604800
""")


def add_build_file(project_name: str):
    with open(f'build.spec', 'w') as f:
        f.write(f"""# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['run.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=['python-multipart'],
             hookspath=[],
             hooksconfig={{}},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='{project_name}',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir='.',
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
""")


@cli.command()
@click.argument('name', default='star7_project')
@click.argument('dir', default='.')
def start_project(name, dir):
    """
    创建项目

    :param name: 项目名称
    :param dir: 项目目录
    :return:
    """
    click.echo(f'project {name} creating')
    if dir != '.':
        project_path = os.path.join(f'{dir}', name)
    else:
        project_path = os.path.join(f'', name)
    if os.path.isdir(project_path):
        click.secho(f'{name} is already exists!', err=True, fg='red')
        return
    os.makedirs(project_path)
    if os.path.isdir('.idea') and dir == '.':
        for root, dirs, files in os.walk('.idea'):
            for file in files:
                if os.path.splitext(file)[1] == '.iml':  # 想要保存的文件格式
                    os.rename(os.path.join('.idea', file), os.path.join('.idea', f'{name}.iml'))
                    edit_idea_project_name(os.path.splitext(file)[0], name)
                    break
    # 添加路由
    add_routes(dir, name)
    # 添加运行程序
    add_running_command(dir, name)
    # 添加设置
    add_settings()
    # 添加说明文件
    add_readme()
    # 添加数据库迁移文件
    add_migrate()
    # 添加应用目录
    add_app_dir(dir)
    # 添加环境配置模板
    add_env_template(name)
    # 添加构建配置文件
    add_build_file(name)
    click.secho(f'{name} is created!', err=True, fg='green')
