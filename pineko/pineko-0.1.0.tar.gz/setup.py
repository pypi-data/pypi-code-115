# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['pineko', 'pineko.cli']

package_data = \
{'': ['*']}

install_requires = \
['PyYAML>=6.0,<7.0',
 'a3b2bbc3ced97675ac3a71df45f55ba>=6.4.0,<7.0.0',
 'appdirs>=1.4.4,<2.0.0',
 'click>=8.0.4,<9.0.0',
 'eko>=0.8.5,<0.9.0',
 'numpy>=1.21.0,<2.0.0',
 'pandas>=1.4.1,<2.0.0',
 'pineappl>=0.5.2,<0.6.0',
 'rich>=11.2.0,<12.0.0',
 'tomli>=2.0.1,<3.0.0']

entry_points = \
{'console_scripts': ['pineko = pineko:command']}

setup_kwargs = {
    'name': 'pineko',
    'version': '0.1.0',
    'description': 'Combine PineAPPL grids and EKOs into FK tables',
    'long_description': None,
    'author': 'Alessandro Candido',
    'author_email': 'alessandro.candido@mi.infn.it',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<3.11',
}


setup(**setup_kwargs)
