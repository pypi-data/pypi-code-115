# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['pyntegrant']

package_data = \
{'': ['*']}

install_requires = \
['icontract>=2.6.0,<3.0.0',
 'networkx>=2.6,<3.0',
 'pyrsistent>=0.18.0,<0.19.0',
 'toolz>=0.11.2,<0.12.0']

setup_kwargs = {
    'name': 'pyntegrant',
    'version': '0.1.0',
    'description': '',
    'long_description': None,
    'author': 'Vic Putz',
    'author_email': 'vbputz@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
