# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['no_ppap_milter']

package_data = \
{'': ['*']}

install_requires = \
['pymilter>=1.0.5,<2.0.0']

entry_points = \
{'console_scripts': ['no-ppap-milter = no_ppap_milter.cli_no_ppap_milter:main']}

setup_kwargs = {
    'name': 'no-ppap-milter',
    'version': '0.1.0',
    'description': '',
    'long_description': None,
    'author': 'HIRANO Yoshitaka',
    'author_email': 'yo@hirano.cc',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
