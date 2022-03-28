# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['needly']

package_data = \
{'': ['*']}

install_requires = \
['Everything-Tkinter>=0.2,<0.3', 'Pillow>=9.0.1,<10.0.0']

setup_kwargs = {
    'name': 'needly',
    'version': '2.5.0',
    'description': 'Python Needle Editor for openQA',
    'long_description': None,
    'author': 'Lukáš Růžička',
    'author_email': 'lruzicka@redhat.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.10,<4.0',
}


setup(**setup_kwargs)
