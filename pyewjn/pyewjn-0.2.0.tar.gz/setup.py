# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['pyewjn', 'pyewjn.dielectric', 'pyewjn.noise', 'pyewjn.util']

package_data = \
{'': ['*']}

install_requires = \
['numpy>=1.21.1,<2.0.0', 'scipy>=1.8,<1.9']

setup_kwargs = {
    'name': 'pyewjn',
    'version': '0.2.0',
    'description': '',
    'long_description': None,
    'author': 'Deepak',
    'author_email': 'dmallubhotla+github@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<3.10',
}


setup(**setup_kwargs)
