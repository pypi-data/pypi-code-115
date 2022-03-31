# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

modules = \
['module_cli']
entry_points = \
{'console_scripts': ['module-cli = module_cli:cli']}

setup_kwargs = {
    'name': 'module-cli',
    'version': '0.1.0',
    'description': '',
    'long_description': None,
    'author': 'Andrew Ross',
    'author_email': 'andrew.ross.mail@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'py_modules': modules,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
