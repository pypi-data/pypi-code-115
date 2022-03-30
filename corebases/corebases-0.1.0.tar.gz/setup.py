# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['corebases', 'corebases.backends']

package_data = \
{'': ['*']}

install_requires = \
['SQLAlchemy>=1.4.0,<2.0.0', 'asyncpg>=0.25,<0.26']

setup_kwargs = {
    'name': 'corebases',
    'version': '0.1.0',
    'description': 'SLQAlchemy.core for asyncpg',
    'long_description': None,
    'author': 'Evgeny Zuev',
    'author_email': 'zueves@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/MartinThoma/infer_pyproject',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
