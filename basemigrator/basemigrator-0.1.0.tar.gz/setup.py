# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['basemigrator']

package_data = \
{'': ['*']}

install_requires = \
['PyMySQL>=1.0.2,<2.0.0', 'PyYAML>=6.0,<7.0']

setup_kwargs = {
    'name': 'basemigrator',
    'version': '0.1.0',
    'description': '',
    'long_description': None,
    'author': 'Eduardo Cristiano Thums',
    'author_email': 'eduardocristiano01@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
