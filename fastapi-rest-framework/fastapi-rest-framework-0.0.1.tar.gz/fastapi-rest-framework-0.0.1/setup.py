# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['fastapi_rest_framework']

package_data = \
{'': ['*']}

install_requires = \
['SQLAlchemy>=1.4.32,<2.0.0',
 'fastapi>=0.75.0,<0.76.0',
 'pydantic>=1.9.0,<2.0.0']

setup_kwargs = {
    'name': 'fastapi-rest-framework',
    'version': '0.0.1',
    'description': 'Restful API based on FastAPI, Pydantic and SQLAlchemy',
    'long_description': '# FastAPI REST framework\n\n[![Release](https://img.shields.io/github/release/Flaiers/fastapi-rest-framework.svg)](https://github.com/Flaiers/fastapi-rest-framework/releases/latest)\n[![Licence](https://img.shields.io/github/license/Flaiers/fastapi-rest-framework)](https://github.com/Flaiers/fastapi-rest-framework/blob/main/LICENSE)\n\n\n## Introduction\n\nRestful API based on FastAPI, Pydantic and SQLAlchemy\n\n## Installation\n\n```shell\npoetry add fastapi-rest-framework\n```\n\n```shell\npip install fastapi-rest-framework\n```\n',
    'author': 'Maxim Bigin',
    'author_email': 'i@flaiers.me',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/long2ice/fastapi-rest',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.10,<4.0',
}


setup(**setup_kwargs)
