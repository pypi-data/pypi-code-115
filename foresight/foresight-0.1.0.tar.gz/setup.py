# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['foresight']

package_data = \
{'': ['*']}

install_requires = \
['cleo>=0.8.1,<0.9.0']

setup_kwargs = {
    'name': 'foresight',
    'version': '0.1.0',
    'description': 'A simple tool to aid in tracking your time.',
    'long_description': None,
    'author': 'ethan.schmitz',
    'author_email': 'ethan.schmitz@mercuryds.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
