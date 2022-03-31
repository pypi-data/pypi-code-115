# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['sirena', 'sirena.erd', 'sirena.flowchart', 'sirena.luigi']

package_data = \
{'': ['*']}

install_requires = \
['pydantic>=1.9.0,<2.0.0']

setup_kwargs = {
    'name': 'sirena',
    'version': '0.1.0',
    'description': '',
    'long_description': None,
    'author': 'Sam Phinizy',
    'author_email': 'nipper@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
