# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['fawaris']

package_data = \
{'': ['*']}

install_requires = \
['PyJWT>=2.1,<3.0',
 'pydantic>=1.0,<2.0',
 'stellar-sdk>=7.0.1,<8.0.0',
 'typing-extensions>=4.1.1,<5.0.0']

setup_kwargs = {
    'name': 'fawaris',
    'version': '0.1.37',
    'description': 'Async framework-agnostic Stellar Anchor interface',
    'long_description': None,
    'author': 'Yuri Escalianti',
    'author_email': 'yuriescl@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/yuriescl/fawaris-python',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
