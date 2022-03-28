# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['codereport']

package_data = \
{'': ['*'], 'codereport': ['templates/*']}

install_requires = \
['Jinja2>=3.1.1,<4.0.0',
 'Pygments>=2.11.2,<3.0.0',
 'fs>=2.4.15,<3.0.0',
 'python-slugify>=6.1.1,<7.0.0']

entry_points = \
{'console_scripts': ['codereport = codereport.cli:main']}

setup_kwargs = {
    'name': 'codereport',
    'version': '0.3.0',
    'description': 'Make annotated code reports',
    'long_description': None,
    'author': 'Paul Gessinger',
    'author_email': 'hello@paulgessinger.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
