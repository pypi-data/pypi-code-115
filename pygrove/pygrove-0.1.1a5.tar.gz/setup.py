# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

modules = \
['pygrove']
install_requires = \
['pyforest>=1.1.0,<2.0.0']

setup_kwargs = {
    'name': 'pygrove',
    'version': '0.1.1a5',
    'description': 'Common data science imports based on pyforest, with a NLP focus',
    'long_description': None,
    'author': 'sileod',
    'author_email': 'damien.sileo@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'py_modules': modules,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
