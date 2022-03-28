# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['sfdata_stream_tutorial']

package_data = \
{'': ['*']}

install_requires = \
['Faker>=13.3.3,<14.0.0',
 'click>=8.0.4,<9.0.0',
 'sfdata-stream-parser>=0.2.0,<0.3.0',
 'tablib[xlsx]>=3.2.0,<4.0.0']

setup_kwargs = {
    'name': 'sfdata-stream-tutorial',
    'version': '0.1.0',
    'description': '',
    'long_description': None,
    'author': 'Kaj Siebert',
    'author_email': 'kaj@k-si.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
