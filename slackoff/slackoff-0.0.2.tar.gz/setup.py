# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['slackoff', 'slackoff.tests']

package_data = \
{'': ['*']}

install_requires = \
['applescript>=2021.2.9,<2022.0.0', 'click', 'minilog']

entry_points = \
{'console_scripts': ['slackoff = slackoff.cli:main']}

setup_kwargs = {
    'name': 'slackoff',
    'version': '0.0.2',
    'description': 'Automatically sign out of Slack workspaces.',
    'long_description': '# Overview\n\nAutomatically sign out of Slack workspaces.\n\nThis project was generated with [cookiecutter](https://github.com/audreyr/cookiecutter) using [jacebrowning/template-python](https://github.com/jacebrowning/template-python).\n\n[![Unix Build Status](https://img.shields.io/travis/com/jacebrowning/slackoff.svg?label=unix)](https://travis-ci.com/jacebrowning/slackoff)\n[![Windows Build Status](https://img.shields.io/appveyor/ci/jacebrowning/slackoff.svg?label=windows)](https://ci.appveyor.com/project/jacebrowning/slackoff)\n[![Coverage Status](https://img.shields.io/codecov/c/gh/jacebrowning/slackoff)](https://codecov.io/gh/jacebrowning/slackoff)\n[![Scrutinizer Code Quality](https://img.shields.io/scrutinizer/g/jacebrowning/slackoff.svg)](https://scrutinizer-ci.com/g/jacebrowning/slackoff)\n[![PyPI License](https://img.shields.io/pypi/l/slackoff.svg)](https://pypi.org/project/slackoff)\n[![PyPI Version](https://img.shields.io/pypi/v/slackoff.svg)](https://pypi.org/project/slackoff)\n[![PyPI Downloads](https://img.shields.io/pypi/dm/slackoff.svg?color=orange)](https://pypistats.org/packages/slackoff)\n\n# Setup\n\n## Requirements\n\n* Python 3.10+\n\n## Installation\n\nInstall it directly into an activated virtual environment:\n\n```text\n$ pip install slackoff\n```\n\nor add it to your [Poetry](https://poetry.eustace.io/) project:\n\n```text\n$ poetry add slackoff\n```\n\n# Usage\n\nAfter installation, the package can imported:\n\n```text\n$ python\n>>> import slackoff\n>>> slackoff.__version__\n```\n',
    'author': 'Jace Browning',
    'author_email': 'jacebrowning@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://pypi.org/project/slackoff',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.10,<4.0',
}


setup(**setup_kwargs)
