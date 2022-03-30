# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['pytamaro_extra', 'pytamaro_extra.de', 'pytamaro_extra.it']

package_data = \
{'': ['*']}

install_requires = \
['pytamaro>=0.1.1,<0.2.0', 'skia-python>=87.4,<88.0']

setup_kwargs = {
    'name': 'pytamaro-extra',
    'version': '0.1.0',
    'description': 'Extra functionalities for PyTamaro',
    'long_description': None,
    'author': 'Luca Chiodini',
    'author_email': 'luca@chiodini.org',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
