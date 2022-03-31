# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['supafunc']

package_data = \
{'': ['*']}

install_requires = \
['httpx>=0.21.3,<0.22.0']

setup_kwargs = {
    'name': 'supafunc',
    'version': '0.1.3',
    'description': 'Functions library for Supabase',
    'long_description': None,
    'author': 'Joel Lee',
    'author_email': 'joel@joellee.org',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
