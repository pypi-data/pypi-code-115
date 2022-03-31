# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['dfops',
 'dfops._internal',
 'dfops._internal.cli',
 'dfops._internal.cli.commands',
 'dfops._internal.cli.io',
 'dfops._internal.cli.io.inputs',
 'dfops._internal.config',
 'dfops._internal.types',
 'dfops._internal.utils']

package_data = \
{'': ['*']}

install_requires = \
['PyYAML>=6.0,<7.0', 'identify>=2.4.12,<3.0.0']

entry_points = \
{'console_scripts': ['dfops = dfops._internal.cli:main']}

setup_kwargs = {
    'name': 'dfops',
    'version': '0.1.0',
    'description': '',
    'long_description': None,
    'author': 'Aviv Brook',
    'author_email': 'avivbrook@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
