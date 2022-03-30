# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['modelator_py',
 'modelator_py.apalache',
 'modelator_py.tlc',
 'modelator_py.util',
 'modelator_py.util.tla',
 'modelator_py.util.tla.examples',
 'modelator_py.util.tlc']

package_data = \
{'': ['*']}

install_requires = \
['fire>=0.4.0,<0.5.0',
 'infix==1.2',
 'pathos>=0.2.8,<0.3.0',
 'ply==3.10',
 'recordclass>=0.16.2,<0.17.0']

entry_points = \
{'console_scripts': ['cli = modelator_py.cli:cli']}

setup_kwargs = {
    'name': 'modelator-py',
    'version': '0.1.0',
    'description': 'Lightweight utilities to assist model writing and model-based testing activities using the TLA+ ecosystem',
    'long_description': None,
    'author': 'Daniel Tisdall',
    'author_email': 'daniel@informal.systems',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.9.7,<4.0.0',
}


setup(**setup_kwargs)
