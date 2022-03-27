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
    'version': '0.0.4',
    'description': 'Automatically sign out of Slack workspaces on macOS.',
    'long_description': '# Overview\n\nAutomatically sign out of Slack workspaces (on macOS) to minimize distractions during or after working hours.\n\n[![Build Status](https://img.shields.io/github/workflow/status/jacebrowning/slackoff/main)](https://github.com/jacebrowning/slackoff/actions)\n[![Coverage Status](https://img.shields.io/codecov/c/gh/jacebrowning/slackoff)](https://codecov.io/gh/jacebrowning/slackoff)\n[![Scrutinizer Code Quality](https://img.shields.io/scrutinizer/g/jacebrowning/slackoff.svg)](https://scrutinizer-ci.com/g/jacebrowning/slackoff)\n[![PyPI License](https://img.shields.io/pypi/l/slackoff.svg)](https://pypi.org/project/slackoff)\n[![PyPI Version](https://img.shields.io/pypi/v/slackoff.svg)](https://pypi.org/project/slackoff)\n[![PyPI Downloads](https://img.shields.io/pypi/dm/slackoff.svg?color=orange)](https://pypistats.org/packages/slackoff)\n\n## Setup\n\n### Requirements\n\n* macOS (for AppleScript)\n* Slack for Mac\n* Python 3.10+\n\n### Installation\n\nInstall this tool globally with [pipx](https://pipxproject.github.io/pipx/) (or pip):\n\n```sh\n$ pipx install slackoff\n```\nor add it to your [Poetry](https://python-poetry.org/docs/) project:\n\n```sh\n$ poetry add slackoff\n```\n\n## Usage\n\nAfter installation, automatically sign out of a Slack workspace:\n\n```sh\n$ slackoff My Workspace Name\n```\n\nor sign back in:\n\n```sh\n$ slackoff My Workspace Name\n```\n',
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
