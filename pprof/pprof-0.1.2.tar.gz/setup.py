# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['pprof']

package_data = \
{'': ['*']}

install_requires = \
['line-profiler>=3.5.1,<4.0.0']

setup_kwargs = {
    'name': 'pprof',
    'version': '0.1.2',
    'description': 'Python profiling tool',
    'long_description': '<p align="center">\n  <a href="https://github.com/mirecl/pprof"><img src="https://github.com/mirecl/pprof/blob/master/examples/report.png?raw=true" alt="pprof"></a>\n</p>\n\n[![PyPI](https://img.shields.io/pypi/v/pprof)](https://pypi.org/project/pprof/)\n[![Downloads](https://pepy.tech/badge/pprof)](https://pepy.tech/project/pprof)\n[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)\n[![GitHub](https://img.shields.io/github/license/mirecl/pprof)](https://github.com/mirecl/pprof/blob/master/LICENSE)\n[![Tests](https://github.com/mirecl/pprof/actions/workflows/tests.yaml/badge.svg)](https://github.com/mirecl/pprof/actions/workflows/tests.yaml)\n[![codecov](https://codecov.io/gh/mirecl/pprof/branch/master/graph/badge.svg?token=UFDA1JG40A)](https://codecov.io/gh/mirecl/pprof)\n[![python version](https://img.shields.io/pypi/pyversions/pprof.svg)](https://pypi.org/project/pprof/)\n\n## Installing\n\n```sh\npip install pprof\n```\n\nor\n\n```sh\npoetry add pprof\n```\n\n## A Simple Example\n\n```python\nfrom typing import List\nfrom pprof import cpu\n\ncpu.auto_report()\n\n@cpu\ndef run(arr: List) -> float:\n    tmp = []\n    for row in arr:\n        if row % 3 == 0:\n            tmp.append(row)\n    result = (sum(tmp*100) + len(arr)) / len(tmp)\n    return result\n\nrun(list(range(100000)))\n```\n\n```sh\n(venv) python run.py\n```\n\n## Links\n\n+ **line_profiler** (<https://github.com/pyutils/line_profiler>)\n',
    'author': 'mirecl',
    'author_email': 'grazhdankov@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.6.2,<4.0',
}


setup(**setup_kwargs)
