# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['lfnt']

package_data = \
{'': ['*']}

install_requires = \
['Flask>=2.0.3,<3.0.0',
 'GitPython>=3.1.27,<4.0.0',
 'ansible>=5.5.0,<6.0.0',
 'awscli>=1.22.82,<2.0.0',
 'click-configfile>=0.2.3,<0.3.0',
 'click>=8.0.4,<9.0.0',
 'pulumi>=3.27.0,<4.0.0']

entry_points = \
{'console_scripts': ['lfnt = lfnt.cli:lfnt']}

setup_kwargs = {
    'name': 'lfnt',
    'version': '0.1.0',
    'description': 'A python app for eating elephants.',
    'long_description': None,
    'author': 'Dan Swartz',
    'author_email': '2fifty6@gmail.com',
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
