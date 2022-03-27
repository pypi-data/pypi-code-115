# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['metrax']

package_data = \
{'': ['*']}

setup_kwargs = {
    'name': 'metrax',
    'version': '0.1.0',
    'description': '',
    'long_description': '## metrax\n\n',
    'author': 'Yusuf Sarıgöz',
    'author_email': 'yusufsarigoz@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/monatis/metrax',
    'packages': packages,
    'package_data': package_data,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
