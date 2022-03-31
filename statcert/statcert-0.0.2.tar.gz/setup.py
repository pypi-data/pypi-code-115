# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['statcert', 'statcert.cli', 'statcert.model', 'statcert.operation']

package_data = \
{'': ['*']}

install_requires = \
['aiohttp>=3.8.1,<4.0.0',
 'cryptography>=36.0.1,<37.0.0',
 'tqdm>=4.62.3,<5.0.0',
 'tranco>=0.6,<0.7']

entry_points = \
{'console_scripts': ['statcert = statcert.cli:main']}

setup_kwargs = {
    'name': 'statcert',
    'version': '0.0.2',
    'description': 'Fetch information about domains and their TLS certificates.',
    'long_description': None,
    'author': 'Kalil Cabral',
    'author_email': 'kbcv@cesar.school',
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
