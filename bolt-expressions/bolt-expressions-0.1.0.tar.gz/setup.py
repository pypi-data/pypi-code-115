# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['bolt_expressions']

package_data = \
{'': ['*']}

install_requires = \
['beet>=0.55.0', 'mecha>=0.43.1']

entry_points = \
{'pytest11': ['bolt_expressions = beet.pytest_plugin']}

setup_kwargs = {
    'name': 'bolt-expressions',
    'version': '0.1.0',
    'description': 'Provides pandas-like expressions capabilities to the bolt extension of mecha',
    'long_description': '# bolt-expressions\n\n[![GitHub Actions](https://github.com/rx-modules/bolt-expressions/workflows/CI/badge.svg)](https://github.com/rx-modules/bolt-expressions/actions)\n[![PyPI](https://img.shields.io/pypi/v/FIXME.svg)](https://pypi.org/project/bolt-expressions/)\n[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/FIXME.svg)](https://pypi.org/project/bolt-expressions/)\n[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)\n[![Discord](https://img.shields.io/discord/900530660677156924?color=7289DA&label=discord&logo=discord&logoColor=fff)](https://discord.gg/98MdSGMm8j)\n\n> a `pandas`-esque API for creating expressions within bolt\n\n## Introduction\n\nBolt is a scripting language which mixes both python and mcfunction. This package amplifies this language by adding an API for creating fluent expressions losely based off of the `pandas` syntax. These expressions are use for simplifying large bits of scoreboard and storage operation allowing you to swiftly create complex operations with the ease of normal programming.\n\n```py\nfrom bolt_expressions import Scoreboard\n\nObjective = ctx.inject(Scoreboard)\nmath = Objective("math")\n\nmath["@s"] = math["@r"] * 10 + math["@r"] + 100\n```\n->\n```mcfunction\nscoreboard players operations $i0 bolt.expressions.temp = @r math\nscoreboard players operations $i0 bolt.expressions.temp *= #10 bolt.expressions.int\nscoreboard players operations $i1 bolt.expressions.temp = @r math\nscoreboard players add $i1 bolt.expressions.temp 100\nscoreboard players operations $i0 bolt.expressions.temp += $i1 bolt.expressions.temp\nscoreboard players operations @s math = $i0 bolt.expressions.temp\n```\n\n## Installation\n\nThe package can be installed with `pip`. Note, you must have both `beet` and `mecha` installed to use this package.\n\n```bash\n$ pip install bolt-expressions\n```\n\n## Getting started\n\nThis package is designed to be used within any `bolt` script (either a `.mcfunction` or `bolt` file) inside a `mecha.contrib.bolt` enabled project. Note, `bolt-expressions` is not a plugin (yet), so there\'s no need to `require` `bolt-expressions`.\n\n```yaml\nrequire:\n    - mecha.contrib.bolt\n\npipeline:\n    - mecha\n```\n\nOnce you\'ve enabled bolt, you are able to import the python package directly inside your bolt script.\n\n```py\nfrom bolt_expressions import Scoreboard, Storage\n```\n\nAny usage of the `bolt_expressions` package will require you to inject the current beet context into the API objects. Then, you can create an objective and start creating expressions.\n\n```py\nObjective = ctx.inject(Scoreboard)\n\nmath = Objective("math")\nentity_id = Objective("entity_id")\n\nmath["@s"] += 10\n```\n\n## Features\n\nThe `Scoreboard` object provides a rich API for you to interact within your bolt landscape. Most numerical operations (such as `+`, `*`, `%`) will produce correct `scoreboard operation` commands for you to work with.\n\n```\nCONSTANT = 60 * 60 * 24\nmath["@s"] *= (entity_id["current_id"] / 200) + CONSTANT\n```\n\nYou can also utilize local variables to simplify readability with longer operations. This is due to the unique `__rebind__` operator provided only in the `bolt` context which allows us provide custom behavior with the `=` operation. We also have defined helper functions such as `min` and `max`, alongside `sqrt` and `**` (for `pow`).\n\n```py\ndmg_obj = Objective("damage")\ndamage = dmg_obj["damage"]\ntoughness = dmg_obj["toughness"]\narmor = dmg_obj["armor"]\n\natf = (10 * armor - (400 * damage / (80 + 10 * toughness)))  # local variable\nmaxxed = max((10 * armor) / 5, atf)                          # still local variable\ndamage = damage * (250 - (min(200, maxxed))) / 25            # calls __rebind__!\n```\n\n## Contributing\n\nContributions are welcome. Make sure to first open an issue discussing the problem or the new feature before creating a pull request. The project uses [`poetry`](https://python-poetry.org).\n\n```bash\n$ poetry install\n```\n\nYou can run the tests with `poetry run pytest`.\n\n```bash\n$ poetry run pytest\n```\n\nThe project must type-check with [`pyright`](https://github.com/microsoft/pyright). If you\'re using VSCode the [`pylance`](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) extension should report diagnostics automatically. You can also install the type-checker locally with `npm install` and run it from the command-line.\n\n```bash\n$ npm run watch\n$ npm run check\n```\n\nThe code follows the [`black`](https://github.com/psf/black) code style. Import statements are sorted with [`isort`](https://pycqa.github.io/isort/).\n\n```bash\n$ poetry run isort bolt_expressions examples tests\n$ poetry run black bolt_expressions examples tests\n$ poetry run black --check bolt_expressions examples tests\n```\n\n---\n\nLicense - [MIT](https://github.com/rx-modules/bolt-expressions/blob/main/LICENSE)\n',
    'author': 'rx97',
    'author_email': None,
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/rx-modules/bolt-expressions',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
