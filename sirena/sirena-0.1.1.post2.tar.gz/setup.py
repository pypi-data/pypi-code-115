# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['sirena', 'sirena.bin', 'sirena.erd', 'sirena.flowchart', 'sirena.luigi']

package_data = \
{'': ['*']}

install_requires = \
['pydantic>=1.9.0,<2.0.0', 'tox>=3.24.5,<4.0.0', 'typer>=0.4.1,<0.5.0']

extras_require = \
{':python_version < "3.8"': ['importlib-metadata==0.12'],
 'luigi': ['luigi>=3.0.3,<4.0.0']}

entry_points = \
{'console_scripts': ['sirena = sirena.bin.cli:app']}

setup_kwargs = {
    'name': 'sirena',
    'version': '0.1.1.post2',
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
    'extras_require': extras_require,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
