# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['pytest_wiremock',
 'pytest_wiremock.client',
 'pytest_wiremock.client.endpoints',
 'pytest_wiremock.client.resources',
 'pytest_wiremock.dsl']

package_data = \
{'': ['*']}

install_requires = \
['httpx>=0.22.0,<0.23.0', 'marshmallow>=3.15.0,<4.0.0', 'pytest>=7.1.1,<8.0.0']

entry_points = \
{'pytest11': ['pytest-wiremock = pytest_wiremock.plugin']}

setup_kwargs = {
    'name': 'pytest-wiremock',
    'version': '0.1.0',
    'description': 'A pytest plugin for programmatically using wiremock in integration tests',
    'long_description': "# pytest-wiremock\nA pytest plugin and DSL for easy integration testing with wiremock :rocket:\n\n[![PyPI version fury.io](https://badge.fury.io/py/pytest-wiremock.svg)](https://pypi.python.org/pypi/pytest-wiremock/)\n[![codecov](https://codecov.io/gh/symonk/pytest-wiremock/branch/main/graph/badge.svg?token=DT2823RGAG)](https://codecov.io/gh/symonk/pytest-wiremock)\n\n# Usage:\n\n```python\n# Todo: Update.\n```\n\n\n# Contributing\n---------------\n\n - Install `docker`.\n - Install `docker-compose`.\n - Install `poetry`.\n - Install `tox`.\n - Run `pre-commit install`.\n - Create and branch and make changes.\n - execute `tox -e py38`\n - Hooks will automatically run; NO PR's will be accepted with a decrease in coverage.\n",
    'author': 'symonk',
    'author_email': 'jackofspaces@gmail.com',
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
