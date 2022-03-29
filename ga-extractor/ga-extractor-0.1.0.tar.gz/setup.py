# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['ga_extractor']

package_data = \
{'': ['*']}

install_requires = \
['PyYAML>=6.0,<7.0',
 'colorama>=0.4.4,<0.5.0',
 'coverage[toml]>=6.3.2,<7.0.0',
 'google-api-python-client>=2.41.0,<3.0.0',
 'google-auth-oauthlib>=0.5.1,<0.6.0',
 'shellingham>=1.4.0,<2.0.0',
 'typer>=0.4.0,<0.5.0',
 'validators>=0.18.2,<0.19.0']

entry_points = \
{'console_scripts': ['ga-extractor = ga_extractor.extractor:extractor']}

setup_kwargs = {
    'name': 'ga-extractor',
    'version': '0.1.0',
    'description': 'Tool for extracting Google Analytics data suitable for migrating to other platforms',
    'long_description': None,
    'author': 'Martin-Heinz1',
    'author_email': 'martin.heinz1@ibm.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/MartinHeinz/ga-extractor',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
