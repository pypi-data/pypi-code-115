# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['kicksaw_github_secrets_management']

package_data = \
{'': ['*']}

install_requires = \
['PyGithub>=1.55,<2.0', 'PyNaCl>=1.5.0,<2.0.0', 'click>=8.1.1,<9.0.0']

entry_points = \
{'console_scripts': ['github-secrets-mgmt = '
                     'kicksaw_github_secrets_management.cli:main']}

setup_kwargs = {
    'name': 'kicksaw-github-secrets-management',
    'version': '0.0.1',
    'description': 'Provides a cli command for pushing secrets to a GitHub repo.',
    'long_description': '# Install\n\n```\ngithub-secrets-mgmt\n```\n',
    'author': 'Alex Drozd',
    'author_email': 'alex@kicksaw.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/Kicksaw-Consulting/kicksaw-github-secrets-management',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
