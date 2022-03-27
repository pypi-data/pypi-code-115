# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['flake8_spellcheck']

package_data = \
{'': ['*']}

install_requires = \
['flake8>3.0.0']

entry_points = \
{'flake8.extension': ['SC = flake8_spellcheck:SpellCheckPlugin']}

setup_kwargs = {
    'name': 'flake8-spellcheck',
    'version': '0.28.0',
    'description': 'Spellcheck variables, comments and docstrings',
    'long_description': "=================\nFlake8 Spellcheck\n=================\n\n|CircleCI| |Black| |PyPi|\n\nFlake8 Plugin that spellchecks variables, functions, classes and other bits of your python code.\n\nYou can whitelist words that are specific to your project simply by adding them to ``whitelist.txt``\nin the root of your project directory. Each word you add  should be separated by a newline.\n\nSpelling is assumed to be in en_US.\n\nThis plugin supports python 3.8+\n\nCodes\n-----\n\n* SC100 - Spelling error in comments\n* SC200 - Spelling error in name (e.g. variable, function, class)\n\nEnable Django support\n---------------------\n\nYou can enable support for a Django dictionary by adding the following to your\nflake8 configuration (e.g. your ``.flake8`` file):\n\n.. code-block:: ini\n\n    [flake8]\n    dictionaries=en_US,python,technical,django\n\nEnable pandas support\n---------------------\n\nYou can enable support for pandas DataFrames by adding the following to your\nflake8 configuration (e.g. your ``.flake8`` file):\n\n.. code-block:: ini\n\n    [flake8]\n    dictionaries=en_US,python,technical,pandas\n\n\nSpecify Targets\n---------------\n\nBoth ``comments`` and ``names`` (variable names, function names...) are spellchecked by default.\nYou can specify what targets to spellcheck in your flake8 configuration (e.g. in your ``.flake8`` file):\n\n.. code-block:: ini\n\n   [flake8]\n   spellcheck-targets=comments\n\nThe above configuration would only spellcheck comments\n\n.. code-block:: ini\n\n   [flake8]\n   spellcheck-targets=names\n\nThe above configuration would only spellcheck names\n\nContributing\n------------\n\nIf you have found word(s) which are listed as a spelling error but are actually correct terms used\nin python or in technical implementations (e.g. http), then you can very easily contribute by\nadding those word(s) to the appropriate dictionaries:\n\n* `python dictionary <flake8_spellcheck/python.txt>`_\n* `technical dictionary <flake8_spellcheck/technical.txt>`_\n* `django dictionary <flake8_spellcheck/django.txt>`_\n* `pandas dictionary <flake8_spellcheck/pandas.txt>`_\n\nBefore you submit a PR, it is recommended to run ``check-sorting.sh`` in the root of this repository,\nto verify that all the dictionary files are still sorted correctly. Sorting is enforced by CI, so\nyou'll need to make sure the files are sorted before your PR can be merged.\n\nDeveloping\n----------\n\n* Install `poetry <https://github.com/python-poetry>`__\n* Run ``poetry install``\n* Install ``pre-commit`` and run ``pre-commit install --install-hooks``\n\n\n.. |CircleCI| image:: https://circleci.com/gh/MichaelAquilina/flake8-spellcheck.svg?style=svg\n   :target: https://circleci.com/gh/MichaelAquilina/flake8-spellcheck\n\n.. |PyPi| image:: https://badge.fury.io/py/flake8-spellcheck.svg\n   :target: https://badge.fury.io/py/flake8-spellcheck\n\n.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg\n   :target: https://github.com/psf/black\n",
    'author': 'Michael Aquilina',
    'author_email': 'michaelaquilina@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/MichaelAquilina/flake8-spellcheck',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8',
}


setup(**setup_kwargs)
