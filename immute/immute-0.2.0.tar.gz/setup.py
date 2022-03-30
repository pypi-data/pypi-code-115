# -*- coding: utf-8 -*-
from setuptools import setup

modules = \
['immute']
setup_kwargs = {
    'name': 'immute',
    'version': '0.2.0',
    'description': 'Create immutable python classes',
    'long_description': None,
    'author': 'fitzypop',
    'author_email': 'fitzypop@pm.me',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'py_modules': modules,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
