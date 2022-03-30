# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['clone_repo']

package_data = \
{'': ['*']}

install_requires = \
['click<8.1.0', 'rich>=12.0,<13.0', 'structlog>=21.5,<22.0', 'typer>=0.4,<0.5']

entry_points = \
{'console_scripts': ['clone-repo = clone_repo.main:app']}

setup_kwargs = {
    'name': 'clone-repo',
    'version': '0.1.0',
    'description': 'CLI tool to clone repos easily',
    'long_description': None,
    'author': 'Michael Twomey',
    'author_email': 'mick@twomeylee.name',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
