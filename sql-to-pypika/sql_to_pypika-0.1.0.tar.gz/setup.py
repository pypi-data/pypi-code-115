# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['sql_to_pypika']

package_data = \
{'': ['*']}

install_requires = \
['PyPika>=0.48.9,<0.49.0', 'click>=8.0.4,<9.0.0', 'sly>=0.4,<0.5']

setup_kwargs = {
    'name': 'sql-to-pypika',
    'version': '0.1.0',
    'description': 'Convert raw SQL to Pypika Objects',
    'long_description': None,
    'author': 'Amit Pahwa',
    'author_email': 'amit@amitpahwa.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
