# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['noaa_ftp', 'noaa_ftp.noaa']

package_data = \
{'': ['*']}

install_requires = \
['progressbar2==4.0.0']

setup_kwargs = {
    'name': 'noaa-ftp',
    'version': '0.1.7',
    'description': 'A python package to work with NOAA FTP',
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
