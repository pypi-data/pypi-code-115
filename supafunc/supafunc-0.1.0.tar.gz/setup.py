# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['supafunc']

package_data = \
{'': ['*']}

setup_kwargs = {
    'name': 'supafunc',
    'version': '0.1.0',
    'description': '',
    'long_description': None,
    'author': 'Joel Lee',
    'author_email': 'joel@joellee.org',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
