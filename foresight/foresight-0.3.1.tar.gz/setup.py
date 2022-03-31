# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['foresight',
 'foresight.calendar',
 'foresight.console',
 'foresight.console.commands',
 'foresight.tracking',
 'foresight.utils']

package_data = \
{'': ['*']}

install_requires = \
['cleo==1.0.0a4',
 'google-api-python-client>=2.42.0,<3.0.0',
 'google-auth-httplib2>=0.1.0,<0.2.0',
 'google-auth-oauthlib>=0.5.1,<0.6.0',
 'pendulum>=2.1.2,<3.0.0',
 'tomlkit>=0.10.1,<0.11.0']

entry_points = \
{'console_scripts': ['foresight = foresight.console.application:main']}

setup_kwargs = {
    'name': 'foresight',
    'version': '0.3.1',
    'description': 'Time management tool.',
    'long_description': '',
    'author': 'etschz',
    'author_email': 'ethanschmitz214@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/etschz/foresight',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
