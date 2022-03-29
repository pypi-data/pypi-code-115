# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['ckpt']

package_data = \
{'': ['*']}

install_requires = \
['GitPython>=3.1.27,<4.0.0', 'dill>=0.3.4,<0.4.0', 'typer>=0.4.0,<0.5.0']

entry_points = \
{'console_scripts': ['checkpoint = ckpt.main:app']}

setup_kwargs = {
    'name': 'ckpt',
    'version': '0.1.1',
    'description': 'Checkpointing functions for easier debugging',
    'long_description': None,
    'author': 'Holger Hoefling',
    'author_email': 'hhoeflin@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
