# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['formee', 'formee.auth', 'formee.formTools']

package_data = \
{'': ['*']}

install_requires = \
['PyInquirer>=1.0.3,<2.0.0',
 'PyYAML>=6.0,<7.0',
 'aiohttp>=3.8.1,<4.0.0',
 'gql>=3.1.0,<4.0.0',
 'pyfiglet>=0.8.post1,<0.9',
 'python-dotenv>=0.20.0,<0.21.0',
 'requests>=2.27.1,<3.0.0',
 'rich>=12.0.1,<13.0.0']

entry_points = \
{'console_scripts': ['formee = formee.__main__:main']}

setup_kwargs = {
    'name': 'formee',
    'version': '0.1.2',
    'description': 'Formee is a tool that provides an easy way to create, edit and manage all of your forms from the command line. It uses a powerful GraphQL API and strives to make the process of working with forms as easy and simple as possible.',
    'long_description': '# Formee- The terminal forms\nFormee is a tool that provides an easy way to create, edit and manage all of your forms from the command line. It uses a powerful GraphQL API and strives to make the process of working with forms as easy and simple as possible.',
    'author': 'Arpan Pandey',
    'author_email': 'arpan@hackersreboot.tech',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/Arpan-206/formee',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
