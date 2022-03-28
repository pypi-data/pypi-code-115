# -*- coding: utf-8 -*-
from setuptools import setup

modules = \
['main']
entry_points = \
{'console_scripts': ['pypaye = payecalculator/main:entrypoint']}

setup_kwargs = {
    'name': 'pypaye',
    'version': '0.1.0',
    'description': 'This is a simple python cscript that calculates PAYE and NI tax payments in the U.K.',
    'long_description': None,
    'author': 'Vsevolod Mineev',
    'author_email': 'vsevolod.mineev@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/vsevolod-mineev/pyPAYE',
    'py_modules': modules,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<3.11',
}


setup(**setup_kwargs)
