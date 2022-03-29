# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['mpsprep']

package_data = \
{'': ['*']}

install_requires = \
['ipykernel>=6.9.2,<7.0.0',
 'matplotlib==3.5',
 'numpy==1.21',
 'pytest-cov>=3.0.0,<4.0.0',
 'scipy==1.7',
 'tqdm==4.60']

setup_kwargs = {
    'name': 'mpsprep',
    'version': '0.1.2',
    'description': 'State preparation for quantum computing using the Matrix Product States approach.',
    'long_description': None,
    'author': 'Prithvi Gundlapalli, Junyi Lee',
    'author_email': None,
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<3.10',
}


setup(**setup_kwargs)
