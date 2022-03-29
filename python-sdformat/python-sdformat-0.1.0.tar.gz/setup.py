# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['pysdf']

package_data = \
{'': ['*']}

install_requires = \
['lxml>=4.8.0,<5.0.0', 'numpy>=1.22.3,<2.0.0']

setup_kwargs = {
    'name': 'python-sdformat',
    'version': '0.1.0',
    'description': 'Python Parser for SDFormat files.',
    'long_description': None,
    'author': 'FirefoxMetzger',
    'author_email': 'sebastian@wallkoetter.net',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
