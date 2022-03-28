# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['auspost']

package_data = \
{'': ['*']}

install_requires = \
['MechanicalSoup>=1.1.0,<2.0.0', 'lxml>=4.8.0,<5.0.0']

setup_kwargs = {
    'name': 'auspost',
    'version': '0.0.10',
    'description': 'A quick module for searching and pulling suburb data from the Australia Post website.',
    'long_description': None,
    'author': 'James Hodgkinson',
    'author_email': 'james@terminaloutcomes.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
