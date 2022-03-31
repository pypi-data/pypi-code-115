# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['heps_ds_utils']

package_data = \
{'': ['*']}

install_requires = \
['PyHive>=0.6.5,<0.7.0',
 'pandas>=1.4.1,<2.0.0',
 'paramiko>=2.10.3,<3.0.0',
 'sasl>=0.3.1,<0.4.0',
 'scp>=0.14.4,<0.15.0',
 'thrift-sasl>=0.4.3,<0.5.0',
 'thrift>=0.15.0,<0.16.0']

setup_kwargs = {
    'name': 'heps-ds-utils',
    'version': '0.1.0',
    'description': 'A Module to enable Hepsiburada Data Science Team to utilize different tools.',
    'long_description': None,
    'author': 'FarukBuldur',
    'author_email': 'faruk.buldur@hepsiburada.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
