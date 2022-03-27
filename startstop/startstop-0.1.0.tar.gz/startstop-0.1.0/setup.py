# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['startstop', 'startstop.scripts']

package_data = \
{'': ['*']}

setup_kwargs = {
    'name': 'startstop',
    'version': '0.1.0',
    'description': 'Tiny process manager written in Python',
    'long_description': None,
    'author': 'Yuri Escalianti',
    'author_email': 'yuriescl@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/yuriescl/startstop',
    'packages': packages,
    'package_data': package_data,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
