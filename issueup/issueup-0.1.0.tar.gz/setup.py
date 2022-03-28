# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['issueup']

package_data = \
{'': ['*']}

install_requires = \
['PyYAML>=6.0,<7.0', 'click>=8.0.3,<9.0.0', 'requests>=2.26.0,<3.0.0']

entry_points = \
{'console_scripts': ['issueup = issueup:main']}

setup_kwargs = {
    'name': 'issueup',
    'version': '0.1.0',
    'description': '',
    'long_description': None,
    'author': 'Roni Choudhury',
    'author_email': 'roni.choudhury@kitware.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
