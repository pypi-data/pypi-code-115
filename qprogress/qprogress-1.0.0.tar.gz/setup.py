# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['qprogress']

package_data = \
{'': ['*']}

setup_kwargs = {
    'name': 'qprogress',
    'version': '1.0.0',
    'description': 'Quera Progress Bar - A decoupled progress bar to show the progress of your loops!',
    'long_description': None,
    'author': 'Mohammad Jafari',
    'author_email': 'm.jafari9877@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
