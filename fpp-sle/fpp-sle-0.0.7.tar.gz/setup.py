# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['fpp_sle', 'fpp_sle.fpp', 'fpp_sle.sde']

package_data = \
{'': ['*']}

install_requires = \
['numba>=0.53.1,<0.54.0', 'numpy>=1.20.2,<2.0.0', 'superposed-pulses>=1.2,<2.0']

setup_kwargs = {
    'name': 'fpp-sle',
    'version': '0.0.7',
    'description': 'Implements FPP and SLE algorithms',
    'long_description': '<h1 align="center">FPP-SLE</h1>\n<div align="center">\n\n ___A filtered Poisson process and stochastic logistic equation comparison playground___\n\n[![PyPI version](https://img.shields.io/pypi/v/fpp-sle)](https://pypi.org/project/fpp-sle/)\n[![Python version](https://img.shields.io/pypi/pyversions/fpp-sle)](https://pypi.org/project/fpp-sle/)\n[![Licence](https://img.shields.io/badge/license-GPL3-yellow)](https://opensource.org/licenses/GPL-3.0)\n[![Tests](https://github.com/engeir/fpp-sle/workflows/Tests/badge.svg)](https://github.com/engeir/fpp-sle/actions?workflow=Tests)\n[![codecov](https://codecov.io/gh/engeir/fpp-sle/branch/main/graph/badge.svg?token=F98z2i3T4G)](https://codecov.io/gh/engeir/fpp-sle)\n[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)\n[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)\n\n</div>\n\n## Install\n\nThe package is publised on [PyPI] and installable via `pip`:\n\n```sh\npip install fpp-sle\n```\n\nTo contribute to the project, clone and install the full development version (uses\n[poetry] for dependencies):\n\n```sh\ngit clone https://github.com/engeir/fpp-sle\ncd fpp-sle\npoetry install\npre-commit install\n```\n\nBefore committing new changes to a branch you can run command\n\n```sh\nnox\n```\n\nto run the full test suite. You will need [Poetry], [nox] and [nox-poetry] installed for\nthis.\n\n## Usage\n\nSee the [examples.py] script for working examples. The main classes and functions this\npackage provide is\n\n- `VariableRateForcing` (inside `fpp` module)\n\n  This is a class that inherit from the forcing generator class provided by\n  [`superposed-pulses`](https://github.com/uit-cosmo/superposed-pulses). The class adds\n  a method for setting a custom function that generates arrival times given the time axis\n  and a given number of total pulses to generate.\n\n- `get_arrival_times` (inside the `fpp` module)\n\n  This is a module that holds functions that draws arrival times according to some\n  non-negative numpy array or callable, that is, the variable rate process.\n\n  - `pass_rate` (inside `get_arrival_times`)\n\n    Used to decorate the functions that draws arrival times from the rate function. This is\n    the function you may want to pass in to the `set_arrival_times_function` method of the\n    `VariableRateForcing` class. It decorates functions within `get_arrival_times` staring\n    with `from_`.\n\n  - `from_` (inside `get_arrival_times`)\n\n    These are generator functions that can take a callable or a numpy array as input, and\n    returns arrival times based on the rate function. Currently only one generator function\n    is implemented (`from_inhomogeneous_poisson_process`) which draws arrival times as if\n    the rate was the underlying rate of a Poisson process.\n\n- `sde`\n\n  This module holds different implementations of stochastic differential equations. See\n  the docstring of the individual functions for explanations.\n\n[pypi]: https://pypi.org/\n[poetry]: https://python-poetry.org\n[examples.py]: ./assets/examples.py\n[nox]: https://nox.thea.codes/en/stable/\n[nox-poetry]: https://nox-poetry.readthedocs.io/\n',
    'author': 'engeir',
    'author_email': 'eirroleng@gmail.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<3.10',
}


setup(**setup_kwargs)
