# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['spsftp']

package_data = \
{'': ['*']}

install_requires = \
['paramiko>=2.10.3,<3.0.0', 'xmltodict>=0.12.0,<0.13.0']

setup_kwargs = {
    'name': 'spsftp',
    'version': '0.0.1',
    'description': "Small library for sending/receiving files using the Serviceplatformen sftp 'simple file transfer'",
    'long_description': None,
    'author': 'Magenta ApS',
    'author_email': 'info@magenta.dk',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
