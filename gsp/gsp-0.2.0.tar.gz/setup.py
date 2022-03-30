# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['gsp']

package_data = \
{'': ['*']}

install_requires = \
['click>=7.1.2,<8.0.0', 'gspread>=5.3.0,<6.0.0', 'typer>=0.4.0,<0.5.0']

setup_kwargs = {
    'name': 'gsp',
    'version': '0.2.0',
    'description': 'Google Sheet Poster',
    'long_description': None,
    'author': 'juke',
    'author_email': 'juke@free.fr',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
