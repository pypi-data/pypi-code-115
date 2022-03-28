# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['bolster',
 'bolster.data_sources',
 'bolster.stats',
 'bolster.utils',
 'bolster.utils.aws']

package_data = \
{'': ['*']}

install_requires = \
['boto3>=1.18.29,<2.0.0',
 'bs4>=0.0.1,<0.0.2',
 'click-log>=0.3.2,<0.5.0',
 'click>=8.0.1,<9.0.0',
 'numpy>=1.21.2,<2.0.0',
 'openpyxl>=3.0.9,<4.0.0',
 'pandas>=1.3.2,<2.0.0',
 'psycopg2-binary>=2.9.1,<3.0.0',
 'requests-cache>=0.9.3,<0.10.0',
 'requests>=2.26.0,<3.0.0',
 'scipy>=1.7.1,<2.0.0',
 'tqdm>=4.62.1,<5.0.0']

entry_points = \
{'console_scripts': ['bolster = bolster.cli:main']}

setup_kwargs = {
    'name': 'bolster',
    'version': '0.1.2',
    'description': "Bolster's Brain, you've been warned",
    'long_description': '=======\nBolster\n=======\n\n\n.. image:: https://img.shields.io/pypi/v/bolster.svg\n    :target: https://pypi.python.org/pypi/bolster\n\n.. image:: https://travis-ci.com/andrewbolster/bolster.svg?branch=main\n    :target: https://travis-ci.com/andrewbolster/bolster\n\n.. image:: https://readthedocs.org/projects/bolster/badge/?version=latest\n    :target: https://bolster.readthedocs.io/en/latest/?version=latest\n    :alt: Documentation Status\n\n.. image:: https://pyup.io/repos/github/andrewbolster/bolster/shield.svg\n    :target: https://pyup.io/repos/github/andrewbolster/bolster/\n    :alt: Updates\n\n.. image:: https://requires.io/github/andrewbolster/bolster/requirements.svg?branch=main\n    :target: https://requires.io/github/andrewbolster/bolster/requirements/?branch=main\n    :alt: Requirements Status\n\nBolster\'s Brain, you\'ve been warned\n\n* Free software: GNU General Public License v3\n* Documentation: https://bolster.readthedocs.io.\n\n\nFeatures\n--------\n\n* Efficient tree/node traversal and iteration\n* Datetime helpers\n* Concurrecy Helpers\n* Web safe Encapsulation/Decapsulation helpers\n* `pandas`-esque `aggregate`/`transform_r` functions\n* "Best Practice" AWS service handling\n\nData Sources\n------------\n* UK Companies House Listings\n* NI House Price Index Data Wrangling\n\nCredits\n-------\n\nThis package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.\n\n.. _Cookiecutter: https://github.com/audreyr/cookiecutter\n.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage\n',
    'author': 'Andrew Bolster',
    'author_email': 'me@andrewbolster.info',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/andrewbolster/bolster',
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8.0,<3.10',
}


setup(**setup_kwargs)
