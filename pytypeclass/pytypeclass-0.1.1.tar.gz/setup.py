# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['pytypeclass']

package_data = \
{'': ['*']}

setup_kwargs = {
    'name': 'pytypeclass',
    'version': '0.1.1',
    'description': '',
    'long_description': None,
    'author': 'Ethan Brooks',
    'author_email': 'ethanabrooks@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
