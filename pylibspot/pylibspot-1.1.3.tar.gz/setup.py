# -*- coding: utf-8 -*-
from setuptools import setup

modules = \
['pylibspot']
setup_kwargs = {
    'name': 'pylibspot',
    'version': '1.1.3',
    'description': 'PyPI version of the python3 bindings to libspot',
    'long_description': None,
    'author': 'Alban Siffer',
    'author_email': 'alban.siffer@irisa.fr',
    'maintainer': 'Alban Siffer',
    'maintainer_email': 'alban.siffer@irisa.fr',
    'url': 'https://asiffer.github.io/libspot/',
    'py_modules': modules,
    'python_requires': '>=3,<4',
}


setup(**setup_kwargs)
