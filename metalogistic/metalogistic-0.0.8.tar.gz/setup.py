# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['metalogistic']

package_data = \
{'': ['*']}

install_requires = \
['matplotlib>=3.5.1,<4.0.0', 'numpy>=1.22.3,<2.0.0', 'scipy>=1.8.0,<2.0.0']

setup_kwargs = {
    'name': 'metalogistic',
    'version': '0.0.8',
    'description': 'A Python package for the metalogistic distribution. The metalogistic or metalog distribution is a highly flexible probability distribution that can be used to model data without traditional parameters.',
    'long_description': None,
    'author': 'tadamcz',
    'author_email': 'tmkadamcz@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<3.9',
}


setup(**setup_kwargs)
