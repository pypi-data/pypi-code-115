# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['skiio', 'skiio.utils']

package_data = \
{'': ['*']}

setup_kwargs = {
    'name': 'skiio',
    'version': '0.1.0',
    'description': 'A "practical" ski compiler with I/O',
    'long_description': None,
    'author': 'Julia',
    'author_email': 'julia.poo.poo.poo@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
