# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['phylum_ci', 'tests']

package_data = \
{'': ['*']}

entry_points = \
{'console_scripts': ['phylum-ci = phylum_ci.cli:main']}

setup_kwargs = {
    'name': 'phylum-ci',
    'version': '0.0.1',
    'description': 'Utilities for Phylum integrations',
    'long_description': '# phylum-ci\n\nPython package for handling CI and other integrations\n\n## Local Development\n\nHere\'s how to set up `phylum-ci` for local development.\n\n1. Clone the `phylum-ci` repo locally\n\n    ```sh\n    git clone git@github.com:phylum-dev/phylum-ci.git\n    ```\n\n2. Ensure [poetry](https://python-poetry.org/docs/) is installed\n3. Install dependencies with `poetry`, which will automatically create a virtual environment:\n\n    ```sh\n    cd phylum-ci\n    poetry install\n    ```\n\n4. Create a branch for local development:\n\n    ```sh\n    git checkout -b <name-of-your-branch>\n    ```\n\n    Now you can make your changes locally.\n\n5. When you\'re done making changes, check that your changes pass the tests:\n\n    ```sh\n    poetry run pytest\n    ```\n\n6. Commit your changes and push your branch to GitHub:\n\n    ```sh\n    git add .\n    git commit -m "Description of the changes goes here"\n    git push --set-upstream origin <name-of-your-branch>\n    ```\n\n7. Submit a pull request through the GitHub website\n',
    'author': 'Phylum, Inc.',
    'author_email': 'engineering@phylum.io',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://phylum.io/',
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
