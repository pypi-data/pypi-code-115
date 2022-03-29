# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['basemigrator']

package_data = \
{'': ['*']}

install_requires = \
['PyMySQL>=1.0.2,<2.0.0', 'PyYAML>=6.0,<7.0']

setup_kwargs = {
    'name': 'basemigrator',
    'version': '0.1.1',
    'description': '',
    'long_description': "# Base Migrator\n\n\n## Installation\n\n```\n$ pip install basemigrator\n```\n\n## Example\n\n```\n# changelog.yaml\n\n- file: Book/001-create-table-ddl.sql\n- file: Author/001-create-table-ddl.sql\n  context: dev, prod\n```\n\n```\n$ python\n>>> from migrator import migrate\n>>> from flask import Flask\n>>> from pathlib import Path\n>>> app = Flask(__name__)\n>>> changelog = f'Path(__file__).parent.absolute()}/migrations'\n>>> migrate(app, changelog)\n```\n\n## TODO\n\n- Improve documentation\n- CI/CD to code linting\n- Support different sql clients(postgres, sqlite3, etc)\n- Contributing section\n- tests/\n",
    'author': 'Eduardo Cristiano Thums',
    'author_email': 'eduardocristiano01@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/EduardoThums/basemigrator',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
