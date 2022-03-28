# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['aiolastfm', 'aiolastfm.types']

package_data = \
{'': ['*']}

modules = \
['py']
install_requires = \
['aiohttp>=3.8.0,<4.0.0']

extras_require = \
{'docs': ['sphinx>=4.5.0,<5.0.0',
          'sphinxcontrib-trio>=1.1.0,<2.0.0',
          'sphinx-copybutton>=0.5.0,<0.6.0',
          'sphinxext-opengraph>=0.6.0,<0.7.0',
          'furo>=2022.3.0,<2023.0.0'],
 'speed': ['orjson>=3.6.0,<4.0.0']}

setup_kwargs = {
    'name': 'aiolastfm',
    'version': '0.0.2',
    'description': 'An async wrapper for the last.fm API.',
    'long_description': '# aiolastfm\n',
    'author': 'Axel',
    'author_email': 'axelancerr@gmail.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'https://github.com/Axelware/aiolastfm',
    'packages': packages,
    'package_data': package_data,
    'py_modules': modules,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'python_requires': '>=3.10.0,<4.0.0',
}


setup(**setup_kwargs)
