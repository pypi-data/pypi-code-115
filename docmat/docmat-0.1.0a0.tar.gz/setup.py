# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['docmat', 'docmat.docstring_formats.google', 'docmat.docstring_formats.shared']

package_data = \
{'': ['*']}

entry_points = \
{'console_scripts': ['docmat = docmat.__main__:main']}

setup_kwargs = {
    'name': 'docmat',
    'version': '0.1.0a0',
    'description': 'Python docstring formatter',
    'long_description': None,
    'author': 'claudio.arcidiacono',
    'author_email': 'claudio.arcidiacono@ing.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
