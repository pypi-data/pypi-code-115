# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['hotedit']

package_data = \
{'': ['*']}

extras_require = \
{'test': ['pytest>=5.2,<6.0', 'pytest-flakes>=4.0.5,<5.0.0']}

setup_kwargs = {
    'name': 'hotedit',
    'version': '0.9.0',
    'description': 'Automatically find and launch an editor with a stream of text to edit; then save',
    'long_description': None,
    'author': 'Cory Dodt',
    'author_email': 'corydodt@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'extras_require': extras_require,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
