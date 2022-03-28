# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['noaa_ftp']

package_data = \
{'': ['*']}

install_requires = \
['progressbar2==4.0.0', 'tqdm==4.63.1']

setup_kwargs = {
    'name': 'noaa-ftp',
    'version': '0.1.0',
    'description': 'A python package to work wit NOAA FTP',
    'long_description': None,
    'author': 'javad',
    'author_email': 'javad.rezvanpour@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
