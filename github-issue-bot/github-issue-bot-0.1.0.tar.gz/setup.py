# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['github_issue_bot']

package_data = \
{'': ['*']}

install_requires = \
['aiohttp>=3.8.1,<4.0.0',
 'click<8.1.0',
 'irc3>=1.1.7,<2.0.0',
 'structlog>=21.5.0,<22.0.0',
 'typer>=0.4.0,<0.5.0']

entry_points = \
{'console_scripts': ['github-issue-bot = github_issue_bot.__main__:cli']}

setup_kwargs = {
    'name': 'github-issue-bot',
    'version': '0.1.0',
    'description': 'Lookup issue titles from issue identifiers on IRC',
    'long_description': None,
    'author': 'Martin Weinelt',
    'author_email': None,
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
