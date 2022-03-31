# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['zhfirstpypi']

package_data = \
{'': ['*']}

install_requires = \
['typer>=0.4.1,<0.5.0']

entry_points = \
{'console_scripts': ['zhfirstpypi = zhfirstpypi.main:app']}

setup_kwargs = {
    'name': 'zhfirstpypi',
    'version': '0.1.0',
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
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
