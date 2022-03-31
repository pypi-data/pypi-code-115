# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['rushmore_tools', 'rushmore_tools._api', 'rushmore_tools.utils']

package_data = \
{'': ['*']}

install_requires = \
['requests>=2.27.1,<3.0.0']

setup_kwargs = {
    'name': 'rushmore-tools',
    'version': '0.1.1',
    'description': '',
    'long_description': "\nTHREE60 Energy `rushmore-tools`\n================================\n[![Build Status](https://github.com/THREE60-Energy/rushmore-tools/workflows/release/badge.svg)](https://github.com/THREE60-Energy/rushmore-tools/actions)\n[![codecov](https://codecov.io/gh/THREE60-Energy/rushmore-tools/branch/main/graph/badge.svg)](https://codecov.io/gh/THREE60-Energy/rushmore-tools)\n[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)\n\nThe `rushmore-tools` package is a collection of tools developed for handling Rushmore Performance Review data developed by THREE60 Energy Norway.\n\nOverview\n================================\nThe collection contains utilities:\n- RushmoreExtractor\n\n\n## Development environment\n\nWe use [poetry](https://python-poetry.org) to manage dependencies and to administrate virtual environments. To develop\n`rushmore-tools`, follow the following steps to set up your local environment:\n\n 1. [Install poetry](https://python-poetry.org/docs/#installation) if you haven't already.\n\n 2. Clone repository:\n    ```\n    $ git clone git@github.com:THREE60-Energy/rushmore-tools.git\n    ```\n 3. Move into the newly created local repository:\n    ```\n    $ cd rushmore-tools\n    ```\n 4. Create virtual environment and install dependencies:\n    ```\n    $ poetry install\n    ```\n\n### Code requirements\n\nAll code must pass [black](https://github.com/ambv/black) and [isort](https://github.com/timothycrosley/isort) style\nchecks to be merged. It is recommended to install pre-commit hooks to ensure this locally before commiting code:\n\n```\n$ poetry run pre-commit install\n```\n\nEach public method, class and module should have docstrings. Docstrings are written in the [Google\nstyle](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).\n",
    'author': 'Marcus Risanger',
    'author_email': '69350948+MarcusRisanger@users.noreply.github.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/THREE60-Energy/rushmore-tools',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.10,<4.0',
}


setup(**setup_kwargs)
