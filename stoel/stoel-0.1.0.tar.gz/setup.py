# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['stoel']

package_data = \
{'': ['*']}

install_requires = \
['SQLAlchemy>=1.4.32,<2.0.0',
 'fastapi>=0.75.0,<0.76.0',
 'psycopg2>=2.9.3,<3.0.0',
 'pydantic>=1.9.0,<2.0.0',
 'speedtest-cli>=2.1.3,<3.0.0',
 'uvicorn[standard]>=0.17.6,<0.18.0']

setup_kwargs = {
    'name': 'stoel',
    'version': '0.1.0',
    'description': 'Bandwidth measurement tool.',
    'long_description': None,
    'author': 'Jan Willems',
    'author_email': 'jw@elevenbits.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.10,<4.0',
}


setup(**setup_kwargs)
