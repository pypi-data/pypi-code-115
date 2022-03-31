# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['icloud_todotxt']

package_data = \
{'': ['*']}

install_requires = \
['pyicloud>=1.0.0,<2.0.0', 'typer>=0.4.1,<0.5.0']

entry_points = \
{'console_scripts': ['icloud-todotxt = icloud_todotxt.main:app']}

setup_kwargs = {
    'name': 'icloud-todotxt',
    'version': '0.1.3',
    'description': 'Synchronize your local `todo.txt` with iCloud.',
    'long_description': '<p align="center"><h1 align="center">iCloud todo.txt</h1></p>\n\n<p align="center"><em>Synchronize your local `todo.txt` with iCloud.</em></p>\n\n<p align="center">\n<img src="https://raw.githubusercontent.com/DavidHeresy/icloud-todotxt/main/public/pylint.svg" alt="Linting: pylint">\n<a href="https://github.com/psf/black" target="_blank">\n    <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black">\n</a>\n<!-- TODO: Add PyPi badge. -->\n<!-- TODO: Add licencse badge. -->\n<!-- TODO: Add GitHub stars badge. -->\n</p>\n\n## Requirements\n\nOn your local machine, you have to set the following two environment variables.\n\n```bash\nTODO_FILE="path/to/your/todo.txt"\nAPPLE_ID="<Your Apple ID email address.>"\n```\n\nOn iCloud you need a folder called `ToDo` where the `todo.txt` will live.\n\n## Installation\n\nInstall the package with pip\n\n```bash\npip install --user path/to/dist/icloud_todotxt-0.1.0-py3-none-any.whl\n```\n\nor pipx\n\n```bash\npipx install path/to/dist/icloud_todotxt-0.1.0-py3-none-any.whl\n```\n\n## Usage\n\nBefore you can use the tool, you have to login once into iCloud.\n\n```bash\nicloud --username=$APPLE_ID\n```\n\nDownload the `todo.txt` from iCloud.\n\n```bash\nicloud-todotxt download\n```\n\nUpload the `todo.txt` to iCloud.\n\n```bash\nicloud-todotxt upload\n```\n\n## Internal Dependencies\n\n* [pyiCloud](https://github.com/picklepete/pyicloud)\n* [Typer](https://typer.tiangolo.com/)\n',
    'author': 'David Härer',
    'author_email': 'david@familie-haerer.de',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/DavidHeresy/icloud-todotxt',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
