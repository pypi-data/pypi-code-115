# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['src']

package_data = \
{'': ['*']}

install_requires = \
['python-dotenv>=0.19.0,<0.20.0',
 'regex>=2022.3.15,<2023.0.0',
 'requests>=2.27.1,<3.0.0']

entry_points = \
{'console_scripts': ['obsidian-todos = src.main:main']}

setup_kwargs = {
    'name': 'obsidian-telegram-reminders',
    'version': '0.1.0',
    'description': '',
    'long_description': None,
    'author': "'Anton Shuvalov'",
    'author_email': 'anton@shuvalov.info',
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
