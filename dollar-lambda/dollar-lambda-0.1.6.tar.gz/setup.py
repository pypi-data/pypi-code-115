# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['dollar_lambda']

package_data = \
{'': ['*']}

install_requires = \
['pytypeclass>=0.1.1,<0.2.0']

setup_kwargs = {
    'name': 'dollar-lambda',
    'version': '0.1.6',
    'description': '',
    'long_description': None,
    'author': 'Ethan Brooks',
    'author_email': 'ethanabrooks@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
