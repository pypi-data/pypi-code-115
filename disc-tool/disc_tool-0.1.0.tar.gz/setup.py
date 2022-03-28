# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['disc_tool']

package_data = \
{'': ['*']}

install_requires = \
['click>=8.0.4,<9.0.0',
 'discord.py>=1.7.3,<2.0.0',
 'networkx>=2.7.1,<3.0.0',
 'tqdm>=4.63.1,<5.0.0']

entry_points = \
{'console_scripts': ['disc = disc_tool.cli:build']}

setup_kwargs = {
    'name': 'disc-tool',
    'version': '0.1.0',
    'description': 'A tool to build Discord implicit social graphs',
    'long_description': '<p align="center">\n    <img src="https://raw.githubusercontent.com/tomasff/disc/main/static/disc.png" height=256 />\n</p>\n\nDISC is a tool to build implicit social graphs for Discord\n',
    'author': 'Tomás F.',
    'author_email': 'contact@tomff.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/tomasff/disc',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
