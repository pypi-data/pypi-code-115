# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['cursecord']

package_data = \
{'': ['*']}

install_requires = \
['aiohttp>=3.8.1,<4.0.0',
 'fishhook>=0.1.4,<0.2.0',
 'typing-extensions>=4.1.1,<5.0.0']

setup_kwargs = {
    'name': 'cursecord',
    'version': '0.1.0',
    'description': 'Why',
    'long_description': 'CURSECORD\n=========\nWhy.\n\n.. image:: https://img.shields.io/codecov/c/github/an-dyy/Cursecord?style=for-the-badge\n   :target: https://app.codecov.io/gh/an-dyy/Cursecord\n   :alt: Code coverage\n\n.. image:: https://img.shields.io/pypi/dm/cursecord?style=for-the-badge\n   :target: https://pypi.org/project/cursecord/\n   :alt: PyPi page\n\n.. image:: https://img.shields.io/github/v/release/an-dyy/Cursecord?sort=semver&style=for-the-badge\n   :target: https://github.com/an-dyy/Cursecord/releases\n   :alt: Github release\n\n\nNotable contributors\n====================\n- `Andy <https://github.com/an-dyy>`_ Creator & Maintainer.\n',
    'author': 'andy',
    'author_email': 'andy.development@protonmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/an-dyy/Cursecord',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
