# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['heavyai']

package_data = \
{'': ['*']}

setup_kwargs = {
    'name': 'heavyai',
    'version': '0.1',
    'description': 'heavyai',
    'long_description': '# heavyai\n\nStay tuned!\n',
    'author': 'Heavy.AI',
    'author_email': None,
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'python_requires': '>=3.7',
}


setup(**setup_kwargs)
