# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['toolstack', 'toolstack.core', 'toolstack.core.plugins']

package_data = \
{'': ['*']}

install_requires = \
['PyYAML>=5.4.1,<6.0.0',
 'beautifulsoup4>=4.10.0,<5.0.0',
 'click>=8.0.4,<9.0.0',
 'requests>=2.27.1,<3.0.0']

setup_kwargs = {
    'name': 'toolstack-core',
    'version': '0.1.1',
    'description': '',
    'long_description': None,
    'author': 'Pascal Prins',
    'author_email': 'pascal.prins@toolstack.ninja',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
