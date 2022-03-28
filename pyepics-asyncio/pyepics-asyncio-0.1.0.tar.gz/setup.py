# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['pyepics_asyncio']

package_data = \
{'': ['*']}

install_requires = \
['pyepics>=3.5.1,<4.0.0']

setup_kwargs = {
    'name': 'pyepics-asyncio',
    'version': '0.1.0',
    'description': 'PyEpics with async/await',
    'long_description': None,
    'author': 'Alexey Gerasev',
    'author_email': 'alexey.gerasev@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
