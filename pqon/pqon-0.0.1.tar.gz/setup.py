# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['pqon']

package_data = \
{'': ['*']}

entry_points = \
{'console_scripts': ['pqon = pqon.cli:entry']}

setup_kwargs = {
    'name': 'pqon',
    'version': '0.0.1',
    'description': 'Manipulate JSON similarly to jq',
    'long_description': None,
    'author': 'Malthe Jørgensen',
    'author_email': 'malthe.jorgensen@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'entry_points': entry_points,
    'python_requires': '>=3.6,<4.0',
}


setup(**setup_kwargs)
