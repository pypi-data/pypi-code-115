# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['genderclfml']

package_data = \
{'': ['*'], 'genderclfml': ['models/*']}

install_requires = \
['joblib>=1.1.0,<2.0.0', 'scikit-learn>=1.0.2,<2.0.0']

setup_kwargs = {
    'name': 'genderclfml',
    'version': '0.1.0',
    'description': 'Gender Classification for Names using Machine Learning',
    'long_description': None,
    'author': 'Author',
    'author_email': None,
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
