# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['subprocess_middleware', 'subprocess_middleware.tests']

package_data = \
{'': ['*']}

install_requires = \
['WebOb>=1.8.7,<2.0.0']

setup_kwargs = {
    'name': 'subprocess-middleware-c4',
    'version': '0.4.0.0b1',
    'description': 'Subprocess WSGI middleware and Pyramid tween.',
    'long_description': None,
    'author': '4dn-dcic',
    'author_email': None,
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<3.8',
}


setup(**setup_kwargs)
