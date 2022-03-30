# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['bonfo', 'bonfo.msp', 'bonfo.msp.structs', 'tests']

package_data = \
{'': ['*']}

install_requires = \
['click==8.0.1',
 'construct>=2.10.67,<3.0.0',
 'dataclass-wizard>=0.22.0,<0.23.0',
 'loca>=2.0.1,<3.0.0',
 'pyserial>=3.5,<4.0',
 'rich-click>=1.2.1,<2.0.0',
 'rich>=12.0.1,<13.0.0']

extras_require = \
{'dev': ['pytest-watcher>=0.2.3,<0.3.0',
         'tox>=3.20.1,<4.0.0',
         'virtualenv>=20.2.2,<21.0.0',
         'pip>=20.3.1,<21.0.0',
         'twine>=3.8.0,<4.0.0',
         'pre-commit>=2.12.0,<3.0.0',
         'toml>=0.10.2,<0.11.0',
         'bump2version>=1.0.1,<2.0.0',
         'autoflake8>=0.3.1,<0.4.0',
         'construct-typing>=0.5.2,<0.6.0'],
 'doc': ['mkdocs>=1.3.0,<2.0.0',
         'mkdocs-include-markdown-plugin>=3.3.0,<4.0.0',
         'mkdocs-material>=8.2.8,<9.0.0',
         'mkdocstrings>=0.18.1,<0.19.0',
         'mkdocs-autorefs>=0.4.1,<0.5.0'],
 'test': ['black>=21.5b2,<22.0',
          'isort>=5.8.0,<6.0.0',
          'flake8>=3.9.2,<4.0.0',
          'flake8-docstrings>=1.6.0,<2.0.0',
          'mypy>=0.940,<0.941',
          'pytest>=6.2.4,<7.0.0',
          'pytest-cov>=2.12.0,<3.0.0']}

entry_points = \
{'console_scripts': ['bonfo = bonfo.cli:main']}

setup_kwargs = {
    'name': 'bonfo',
    'version': '0.1.0',
    'description': 'Multiwii flight controller configuration management',
    'long_description': '# Bonfo - Betaflight configuration management\n\n[![pypi](https://img.shields.io/pypi/v/bonfo.svg)](https://pypi.org/project/bonfo/)\n[![python](https://img.shields.io/pypi/pyversions/bonfo.svg)](https://pypi.org/project/bonfo/)\n[![Build Status](https://github.com/destos/bonfo/actions/workflows/dev.yml/badge.svg)](https://github.com/destos/bonfo/actions/workflows/dev.yml)\n[![codecov](https://codecov.io/gh/destos/bonfo/branch/main/graphs/badge.svg)](https://codecov.io/github/destos/bonfo)\n\n\n* Documentation: <https://destos.github.io/bonfo>\n* GitHub: <https://github.com/destos/bonfo>\n* PyPI: <https://pypi.org/project/bonfo/>\n* Free software: MIT\n\n## Features\n\n* Connects to Betaflight flight controllers\n* More soon ( lol )\n\n## Credits\n\nThis package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [waynerv/cookiecutter-pypackage](https://github.com/waynerv/cookiecutter-pypackage) project template.\n',
    'author': 'Patrick Forringer',
    'author_email': 'patrick@forringer.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/destos/bonfo',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
