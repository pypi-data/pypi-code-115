# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['pip_middleware_fluig',
 'pip_middleware_fluig.domain',
 'pip_middleware_fluig.interface',
 'pip_middleware_fluig.repositories',
 'pip_middleware_fluig.services',
 'pip_middleware_fluig.tests',
 'pip_middleware_fluig.utils']

package_data = \
{'': ['*']}

install_requires = \
['black>=22.1.0,<23.0.0',
 'httpx>=0.22.0,<0.23.0',
 'ipython>=8.2.0,<9.0.0',
 'pydantic>=1.9.0,<2.0.0',
 'pytest>=7.1.1,<8.0.0',
 'safety>=1.10.3,<2.0.0',
 'twine>=3.8.0,<4.0.0',
 'zeep>=4.1.0,<5.0.0']

setup_kwargs = {
    'name': 'pip-middleware-fluig',
    'version': '0.1.8',
    'description': 'middleware service fluig plataform',
    'long_description': None,
    'author': 'Rodrigo Becker',
    'author_email': 'rodrigo.beckermore@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
