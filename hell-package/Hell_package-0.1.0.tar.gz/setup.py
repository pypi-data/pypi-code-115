# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['my_package']

package_data = \
{'': ['*']}

install_requires = \
['Unidecode>=1.3.4,<2.0.0', 'requests>=2.13.0,<3.0.0']

setup_kwargs = {
    'name': 'hell-package',
    'version': '0.1.0',
    'description': '" "',
    'long_description': None,
    'author': 'Oussama BATATA',
    'author_email': None,
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
