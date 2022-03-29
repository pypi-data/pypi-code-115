# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['pylsp_autoimport']

package_data = \
{'': ['*']}

install_requires = \
['autoimport>=1.2.2,<2.0.0', 'python-lsp-server>=1.4.1,<2.0.0']

entry_points = \
{'pylsp': ['pylsp_autoimport = pylsp_autoimport.plugin']}

setup_kwargs = {
    'name': 'pylsp-autoimport',
    'version': '0.1.0',
    'description': '',
    'long_description': None,
    'author': 'bageljr',
    'author_email': 'bageljr897@protonmail.com',
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
