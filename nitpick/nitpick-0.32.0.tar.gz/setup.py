# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['nitpick',
 'nitpick.plugins',
 'nitpick.resources',
 'nitpick.resources.any',
 'nitpick.resources.javascript',
 'nitpick.resources.kotlin',
 'nitpick.resources.presets',
 'nitpick.resources.proto',
 'nitpick.resources.python',
 'nitpick.resources.shell',
 'nitpick.style',
 'nitpick.style.fetchers']

package_data = \
{'': ['*']}

install_requires = \
['ConfigUpdater',
 'StrEnum',
 'attrs>=20.1.0',
 'autorepr',
 'click',
 'dictdiffer',
 'dpath',
 'flake8>=3.0.0',
 'flatten-dict',
 'furl',
 'identify',
 'jmespath',
 'loguru',
 'marshmallow-polyfield>=5.10,<6.0',
 'marshmallow>=3.0.0b10',
 'more-itertools',
 'pluggy',
 'python-slugify',
 'requests',
 'requests-cache',
 'ruamel.yaml',
 'sortedcontainers',
 'toml',
 'tomlkit>=0.8.0']

extras_require = \
{':extra == "test"': ['pytest-socket'],
 ':python_version >= "3.7" and python_version < "3.9"': ['importlib-resources'],
 'doc': ['sphinx', 'sphinx_rtd_theme', 'sphobjinv', 'sphinx-gitref'],
 'lint': ['pylint'],
 'test': ['pytest',
          'pytest-cov',
          'testfixtures',
          'responses',
          'freezegun',
          'pytest-testmon',
          'pytest-watch',
          'pytest-datadir']}

entry_points = \
{'console_scripts': ['nitpick = nitpick.cli:nitpick_cli'],
 'flake8.extension': ['NIP = nitpick.flake8:NitpickFlake8Extension'],
 'nitpick': ['ini = nitpick.plugins.ini',
             'json = nitpick.plugins.json',
             'text = nitpick.plugins.text',
             'toml = nitpick.plugins.toml',
             'yaml = nitpick.plugins.yaml']}

setup_kwargs = {
    'name': 'nitpick',
    'version': '0.32.0',
    'description': 'Enforce the same settings across multiple language-independent projects',
    'long_description': 'Nitpick\n=======\n\n|PyPI|\n|Supported Python versions|\n|GitHub Actions Python Workflow|\n|Documentation Status|\n|Coveralls|\n|Maintainability|\n|Test Coverage|\n|pre-commit|\n|pre-commit.ci status|\n|Project License|\n|Code style: black|\n|Renovate|\n|semantic-release|\n|FOSSA Status|\n\nCommand-line tool and `flake8 <https://github.com/PyCQA/flake8>`_\nplugin to enforce the same settings across multiple language-independent\nprojects.\n\nUseful if you maintain multiple projects and are tired of\ncopying/pasting the same INI/TOML/YAML/JSON keys and values over and\nover, in all of them.\n\nThe CLI now has a ``nitpick fix`` command that modifies configuration\nfiles directly (pretty much like\n`black <https://github.com/psf/black>`_ and\n`isort <https://github.com/PyCQA/isort>`_ do with Python files).\nSee the `CLI docs for more\ninfo <https://nitpick.rtfd.io/en/latest/cli.html>`_.\n\nMany more features are planned for the future, check `the\nroadmap <https://github.com/andreoliwa/nitpick/projects/1>`_.\n\nThe style file\n--------------\n\nA "Nitpick code style" is a `TOML <https://github.com/toml-lang/toml>`_\nfile with the settings that should be present in config files from other\ntools.\n\nExample of a style:\n\n.. code-block:: toml\n\n    ["pyproject.toml".tool.black]\n    line-length = 120\n\n    ["pyproject.toml".tool.poetry.dev-dependencies]\n    pylint = "*"\n\n    ["setup.cfg".flake8]\n    ignore = "D107,D202,D203,D401"\n    max-line-length = 120\n    inline-quotes = "double"\n\n    ["setup.cfg".isort]\n    line_length = 120\n    multi_line_output = 3\n    include_trailing_comma = true\n    force_grid_wrap = 0\n    combine_as_imports = true\n\nThis style will assert that:\n\n-  ... `black <https://github.com/psf/black>`_,\n   `isort <https://github.com/PyCQA/isort>`_ and\n   `flake8 <https://github.com/PyCQA/flake8>`_ have a line length of\n   120;\n-  ... `flake8 <https://github.com/PyCQA/flake8>`_ and\n   `isort <https://github.com/PyCQA/isort>`_ are configured as above in\n   ``setup.cfg``;\n-  ... `Pylint <https://www.pylint.org>`__ is present as a\n   `Poetry <https://github.com/python-poetry/poetry>`_ dev dependency\n   in ``pyproject.toml``.\n\nSupported file types\n--------------------\n\nThese are the file types currently handled by Nitpick.\n\n-  Some files are only being checked and have to be modified manually;\n-  Some files can already be fixed automatically (with the\n   ``nitpick fix`` command);\n-  Others are still under construction; the ticket numbers are shown in\n   the table (upvote the ticket with 👍🏻 if you would like to prioritise\n   development).\n\nImplemented\n~~~~~~~~~~~\n\n.. auto-generated-start-implemented\n.. list-table::\n   :header-rows: 1\n\n   * - File type\n     - ``nitpick check``\n     - ``nitpick fix``\n   * - `Any INI file <https://nitpick.rtfd.io/en/latest/plugins.html#ini-files>`_\n     - ✅\n     - ✅\n   * - `Any JSON file <https://nitpick.rtfd.io/en/latest/plugins.html#json-files>`_\n     - ✅\n     - ✅\n   * - `Any plain text file <https://nitpick.rtfd.io/en/latest/plugins.html#text-files>`_\n     - ✅\n     - ❌\n   * - `Any TOML file <https://nitpick.rtfd.io/en/latest/plugins.html#toml-files>`_\n     - ✅\n     - ✅\n   * - `Any YAML file <https://nitpick.rtfd.io/en/latest/plugins.html#yaml-files>`_\n     - ✅\n     - ✅\n   * - `.editorconfig <https://nitpick.rtfd.io/en/latest/library.html#any>`_\n     - ✅\n     - ✅\n   * - `.pylintrc <https://nitpick.rtfd.io/en/latest/plugins.html#ini-files>`_\n     - ✅\n     - ✅\n   * - `setup.cfg <https://nitpick.rtfd.io/en/latest/plugins.html#ini-files>`_\n     - ✅\n     - ✅\n.. auto-generated-end-implemented\n\nPlanned\n~~~~~~~\n\n.. auto-generated-start-planned\n.. list-table::\n   :header-rows: 1\n\n   * - File type\n     - ``nitpick check``\n     - ``nitpick fix``\n   * - Any Markdown file\n     - `#280 <https://github.com/andreoliwa/nitpick/issues/280>`_ 🚧\n     - ❓\n   * - Any Terraform file\n     - `#318 <https://github.com/andreoliwa/nitpick/issues/318>`_ 🚧\n     - ❓\n   * - Dockerfile\n     - `#272 <https://github.com/andreoliwa/nitpick/issues/272>`_ 🚧\n     - `#272 <https://github.com/andreoliwa/nitpick/issues/272>`_ 🚧\n   * - .dockerignore\n     - `#8 <https://github.com/andreoliwa/nitpick/issues/8>`_ 🚧\n     - `#8 <https://github.com/andreoliwa/nitpick/issues/8>`_ 🚧\n   * - .gitignore\n     - `#8 <https://github.com/andreoliwa/nitpick/issues/8>`_ 🚧\n     - `#8 <https://github.com/andreoliwa/nitpick/issues/8>`_ 🚧\n   * - Jenkinsfile\n     - `#278 <https://github.com/andreoliwa/nitpick/issues/278>`_ 🚧\n     - ❓\n   * - Makefile\n     - `#277 <https://github.com/andreoliwa/nitpick/issues/277>`_ 🚧\n     - ❓\n.. auto-generated-end-planned\n\nStyle Library (Presets)\n-----------------------\n\nNitpick has a builtin library of style presets, shipped as `Python resources <https://docs.python.org/3/library/importlib.html#module-importlib.resources>`_.\n\nThis library contains building blocks for your your custom style.\nJust choose styles from the table below and create your own style, like LEGO.\n\nRead how to:\n\n- `...add multiple styles to the configuration file <https://nitpick.readthedocs.io/en/latest/configuration.html#multiple-styles>`_;\n- `...include styles inside a style <https://nitpick.readthedocs.io/en/latest/nitpick_section.html#nitpick-styles>`_.\n\n.. auto-generated-start-style-library\n\nany\n~~~\n\n.. list-table::\n   :header-rows: 1\n\n   * - Style URL\n     - Description\n   * - `py://nitpick/resources/any/codeclimate <src/nitpick/resources/any/codeclimate.toml>`_\n     - `CodeClimate <https://codeclimate.com/>`_\n   * - `py://nitpick/resources/any/commitizen <src/nitpick/resources/any/commitizen.toml>`_\n     - `Commitizen (Python) <https://github.com/commitizen-tools/commitizen>`_\n   * - `py://nitpick/resources/any/commitlint <src/nitpick/resources/any/commitlint.toml>`_\n     - `commitlint <https://github.com/conventional-changelog/commitlint>`_\n   * - `py://nitpick/resources/any/editorconfig <src/nitpick/resources/any/editorconfig.toml>`_\n     - `EditorConfig <http://editorconfig.org/>`_\n   * - `py://nitpick/resources/any/git-legal <src/nitpick/resources/any/git-legal.toml>`_\n     - `Git.legal - CodeClimate Community Edition <https://github.com/kmewhort/git.legal-codeclimate>`_\n   * - `py://nitpick/resources/any/markdownlint <src/nitpick/resources/any/markdownlint.toml>`_\n     - `Markdown lint <https://github.com/markdownlint/markdownlint>`_\n   * - `py://nitpick/resources/any/pre-commit-hooks <src/nitpick/resources/any/pre-commit-hooks.toml>`_\n     - `pre-commit hooks for any project <https://github.com/pre-commit/pre-commit-hooks>`_\n   * - `py://nitpick/resources/any/prettier <src/nitpick/resources/any/prettier.toml>`_\n     - `Prettier <https://github.com/prettier/prettier>`_\n\njavascript\n~~~~~~~~~~\n\n.. list-table::\n   :header-rows: 1\n\n   * - Style URL\n     - Description\n   * - `py://nitpick/resources/javascript/package-json <src/nitpick/resources/javascript/package-json.toml>`_\n     - `package.json <https://github.com/yarnpkg/website/blob/master/lang/en/docs/package-json.md>`_\n\nkotlin\n~~~~~~\n\n.. list-table::\n   :header-rows: 1\n\n   * - Style URL\n     - Description\n   * - `py://nitpick/resources/kotlin/ktlint <src/nitpick/resources/kotlin/ktlint.toml>`_\n     - `ktlint <https://github.com/pinterest/ktlint>`_\n\npresets\n~~~~~~~\n\n.. list-table::\n   :header-rows: 1\n\n   * - Style URL\n     - Description\n   * - `py://nitpick/resources/presets/nitpick <src/nitpick/resources/presets/nitpick.toml>`_\n     - `Default style file for Nitpick <https://nitpick.rtfd.io/>`_\n\nproto\n~~~~~\n\n.. list-table::\n   :header-rows: 1\n\n   * - Style URL\n     - Description\n   * - `py://nitpick/resources/proto/protolint <src/nitpick/resources/proto/protolint.toml>`_\n     - `protolint (Protobuf linter) <https://github.com/yoheimuta/protolint>`_\n\npython\n~~~~~~\n\n.. list-table::\n   :header-rows: 1\n\n   * - Style URL\n     - Description\n   * - `py://nitpick/resources/python/310 <src/nitpick/resources/python/310.toml>`_\n     - Python 3.10\n   * - `py://nitpick/resources/python/37 <src/nitpick/resources/python/37.toml>`_\n     - Python 3.7\n   * - `py://nitpick/resources/python/38 <src/nitpick/resources/python/38.toml>`_\n     - Python 3.8\n   * - `py://nitpick/resources/python/39 <src/nitpick/resources/python/39.toml>`_\n     - Python 3.9\n   * - `py://nitpick/resources/python/absent <src/nitpick/resources/python/absent.toml>`_\n     - Files that should not exist\n   * - `py://nitpick/resources/python/autoflake <src/nitpick/resources/python/autoflake.toml>`_\n     - `autoflake <https://github.com/myint/autoflake>`_\n   * - `py://nitpick/resources/python/bandit <src/nitpick/resources/python/bandit.toml>`_\n     - `Bandit <https://github.com/PyCQA/bandit>`_\n   * - `py://nitpick/resources/python/black <src/nitpick/resources/python/black.toml>`_\n     - `Black <https://github.com/psf/black>`_\n   * - `py://nitpick/resources/python/flake8 <src/nitpick/resources/python/flake8.toml>`_\n     - `Flake8 <https://github.com/PyCQA/flake8>`_\n   * - `py://nitpick/resources/python/github-workflow <src/nitpick/resources/python/github-workflow.toml>`_\n     - `GitHub Workflow for Python <https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions>`_\n   * - `py://nitpick/resources/python/ipython <src/nitpick/resources/python/ipython.toml>`_\n     - `IPython <https://github.com/ipython/ipython>`_\n   * - `py://nitpick/resources/python/isort <src/nitpick/resources/python/isort.toml>`_\n     - `isort <https://github.com/PyCQA/isort>`_\n   * - `py://nitpick/resources/python/mypy <src/nitpick/resources/python/mypy.toml>`_\n     - `Mypy <https://github.com/python/mypy>`_\n   * - `py://nitpick/resources/python/poetry-editable <src/nitpick/resources/python/poetry-editable.toml>`_\n     - `Poetry (editable projects; PEP 600 support) <https://github.com/python-poetry/poetry>`_\n   * - `py://nitpick/resources/python/poetry <src/nitpick/resources/python/poetry.toml>`_\n     - `Poetry <https://github.com/python-poetry/poetry>`_\n   * - `py://nitpick/resources/python/pre-commit-hooks <src/nitpick/resources/python/pre-commit-hooks.toml>`_\n     - `pre-commit hooks for Python projects <https://pre-commit.com/hooks>`_\n   * - `py://nitpick/resources/python/pylint <src/nitpick/resources/python/pylint.toml>`_\n     - `Pylint <https://github.com/PyCQA/pylint>`_\n   * - `py://nitpick/resources/python/radon <src/nitpick/resources/python/radon.toml>`_\n     - `Radon <https://github.com/rubik/radon>`_\n   * - `py://nitpick/resources/python/readthedocs <src/nitpick/resources/python/readthedocs.toml>`_\n     - `Read the Docs <https://github.com/readthedocs/readthedocs.org>`_\n   * - `py://nitpick/resources/python/sonar-python <src/nitpick/resources/python/sonar-python.toml>`_\n     - `SonarQube Python plugin <https://github.com/SonarSource/sonar-python>`_\n   * - `py://nitpick/resources/python/stable <src/nitpick/resources/python/stable.toml>`_\n     - Current stable Python version\n   * - `py://nitpick/resources/python/tox <src/nitpick/resources/python/tox.toml>`_\n     - `tox <https://github.com/tox-dev/tox>`_\n\nshell\n~~~~~\n\n.. list-table::\n   :header-rows: 1\n\n   * - Style URL\n     - Description\n   * - `py://nitpick/resources/shell/bashate <src/nitpick/resources/shell/bashate.toml>`_\n     - `bashate (code style for Bash) <https://github.com/openstack/bashate>`_\n   * - `py://nitpick/resources/shell/shellcheck <src/nitpick/resources/shell/shellcheck.toml>`_\n     - `ShellCheck (static analysis for shell scripts) <https://github.com/koalaman/shellcheck>`_\n   * - `py://nitpick/resources/shell/shfmt <src/nitpick/resources/shell/shfmt.toml>`_\n     - `shfmt (shell script formatter) <https://github.com/mvdan/sh>`_\n.. auto-generated-end-style-library\n\nQuickstart\n----------\n\nInstall\n~~~~~~~\n\nInstall in an isolated global environment with\n`pipx <https://github.com/pipxproject/pipx>`_::\n\n    # Latest PyPI release\n    pipx install nitpick\n\n    # Development branch from GitHub\n    pipx install git+https://github.com/andreoliwa/nitpick\n\nOn macOS/Linux, install with\n`Homebrew <https://github.com/Homebrew/brew>`_::\n\n    # Latest PyPI release\n    brew install andreoliwa/formulae/nitpick\n\n    # Development branch from GitHub\n    brew install andreoliwa/formulae/nitpick --HEAD\n\nOn Arch Linux, install with yay::\n\n    yay -Syu nitpick\n\nAdd to your project with\n`Poetry <https://github.com/python-poetry/poetry>`_::\n\n    poetry add --dev nitpick\n\nOr install it with pip::\n\n    pip install -U nitpick\n\nRun\n~~~\n\nTo fix and modify your files directly::\n\n    nitpick fix\n\nTo check for errors only::\n\n    nitpick check\n\nNitpick is also a ``flake8`` plugin, so you can run this on a project\nwith at least one Python (``.py``) file::\n\n    flake8 .\n\nNitpick will download and use the opinionated `default style file <nitpick-style.toml>`_.\n\nYou can use it as a template to configure your own style.\n\nRun as a pre-commit hook\n~~~~~~~~~~~~~~~~~~~~~~~~\n\nIf you use `pre-commit <https://pre-commit.com/>`_ on your project, add\nthis to the ``.pre-commit-config.yaml`` in your repository::\n\n    repos:\n      - repo: https://github.com/andreoliwa/nitpick\n        rev: v0.32.0\n        hooks:\n          - id: nitpick\n\nThere are 3 available hook IDs:\n\n- ``nitpick`` and ``nitpick-fix`` both run the ``nitpick fix`` command;\n- ``nitpick-check`` runs ``nitpick check``.\n\nIf you want to run Nitpick as a flake8 plugin instead::\n\n    repos:\n      - repo: https://github.com/PyCQA/flake8\n        rev: 4.0.1\n        hooks:\n          - id: flake8\n            additional_dependencies: [nitpick]\n\nMore information\n----------------\n\nNitpick is being used by projects such as:\n\n-  `wemake-services/wemake-python-styleguide <https://github.com/wemake-services/wemake-python-styleguide>`_\n-  `dry-python/returns <https://github.com/dry-python/returns>`_\n-  `sobolevn/django-split-settings <https://github.com/sobolevn/django-split-settings>`_\n-  `catalyst-team/catalyst <https://github.com/catalyst-team/catalyst>`_\n-  `alan-turing-institute/AutSPACEs <https://github.com/alan-turing-institute/AutSPACEs>`_\n-  `pytest-dev/pytest-mimesis <https://github.com/pytest-dev/pytest-mimesis>`_\n\nFor more details on styles and which configuration files are currently\nsupported, `see the full documentation <https://nitpick.rtfd.io/>`_.\n\n.. |PyPI| image:: https://img.shields.io/pypi/v/nitpick.svg\n   :target: https://pypi.org/project/nitpick\n.. |GitHub Actions Python Workflow| image:: https://github.com/andreoliwa/nitpick/workflows/Python/badge.svg\n.. |Documentation Status| image:: https://readthedocs.org/projects/nitpick/badge/?version=latest\n   :target: https://nitpick.rtfd.io/en/latest/?badge=latest\n.. |Coveralls| image:: https://coveralls.io/repos/github/andreoliwa/nitpick/badge.svg\n   :target: https://coveralls.io/github/andreoliwa/nitpick\n.. |Maintainability| image:: https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/maintainability\n   :target: https://codeclimate.com/github/andreoliwa/nitpick\n.. |Test Coverage| image:: https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/test_coverage\n   :target: https://codeclimate.com/github/andreoliwa/nitpick\n.. |Supported Python versions| image:: https://img.shields.io/pypi/pyversions/nitpick.svg\n   :target: https://pypi.org/project/nitpick/\n.. |Project License| image:: https://img.shields.io/pypi/l/nitpick.svg\n   :target: https://pypi.org/project/nitpick/\n.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg\n   :target: https://github.com/psf/black\n.. |Renovate| image:: https://img.shields.io/badge/renovate-enabled-brightgreen.svg\n   :target: https://renovatebot.com/\n.. |semantic-release| image:: https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg\n   :target: https://github.com/semantic-release/semantic-release\n.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white\n   :target: https://github.com/pre-commit/pre-commit\n   :alt: pre-commit\n.. |pre-commit.ci status| image:: https://results.pre-commit.ci/badge/github/andreoliwa/nitpick/develop.svg\n   :target: https://results.pre-commit.ci/latest/github/andreoliwa/nitpick/develop\n.. |FOSSA Status| image:: https://app.fossa.com/api/projects/git%2Bgithub.com%2Fandreoliwa%2Fnitpick.svg?type=shield\n   :target: https://app.fossa.com/projects/git%2Bgithub.com%2Fandreoliwa%2Fnitpick?ref=badge_shield\n\nContributing\n------------\n\nYour help is very much appreciated.\n\nThere are many possibilities for new features in this project, and not enough time or hands to work on them.\n\nIf you want to contribute with the project, set up your development environment following the steps on the `contribution guidelines <https://nitpick.rtfd.io/en/latest/contributing.html>`_ and send your pull request.\n',
    'author': 'W. Augusto Andreoli',
    'author_email': 'andreoliwa@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/andreoliwa/nitpick',
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
