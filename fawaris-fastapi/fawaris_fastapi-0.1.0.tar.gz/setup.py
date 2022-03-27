# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['fawaris_fastapi', 'fawaris_fastapi.scripts']

package_data = \
{'': ['*']}

install_requires = \
['aiosqlite>=0.17.0,<0.18.0',
 'databases>=0.5.5,<0.6.0',
 'fastapi>=0.75.0,<0.76.0',
 'fawaris>=0.1.36,<0.2.0',
 'overrides>=6.1.0,<7.0.0',
 'python-multipart>=0.0.5,<0.0.6',
 'typer>=0.4.0,<0.5.0',
 'uvicorn>=0.17.6,<0.18.0']

setup_kwargs = {
    'name': 'fawaris-fastapi',
    'version': '0.1.0',
    'description': 'Stellar Anchor implementation using FastAPI',
    'long_description': None,
    'author': 'Yuri Escalianti',
    'author_email': 'yuriescl@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
