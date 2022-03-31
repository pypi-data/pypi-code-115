# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['pi_finder']

package_data = \
{'': ['*']}

install_requires = \
['python-nmap>=0.7.1,<0.8.0', 'yaspin>=2.1.0,<3.0.0']

entry_points = \
{'console_scripts': ['pi-finder = pi_finder.main:run']}

setup_kwargs = {
    'name': 'pi-finder',
    'version': '0.1.1',
    'description': '',
    'long_description': None,
    'author': 'Philipp Viereck',
    'author_email': 'no@email.nothingexist',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
