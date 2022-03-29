# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['cloudlab_client']

package_data = \
{'': ['*']}

install_requires = \
['selenium>=4.1.3,<5.0.0']

setup_kwargs = {
    'name': 'cloudlab-client',
    'version': '0.1.2',
    'description': 'Client for the cloudlab academic cloud environment.',
    'long_description': None,
    'author': 'Yannis Zarkadas',
    'author_email': 'yanniszark@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
