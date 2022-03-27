# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['telegram_log']

package_data = \
{'': ['*']}

install_requires = \
['python-telegram-bot>=13.11,<14.0']

setup_kwargs = {
    'name': 'telegram-log',
    'version': '1.0.13',
    'description': '',
    'long_description': None,
    'author': 'Your Name',
    'author_email': 'you@example.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.6,<4.0',
}


setup(**setup_kwargs)
