# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['web_grepy']

package_data = \
{'': ['*']}

install_requires = \
['click>=8.0.4,<9.0.0', 'easy-scraper-py>=1.0.0,<2.0.0']

entry_points = \
{'console_scripts': ['web-grepy = web_grepy.cli:main']}

setup_kwargs = {
    'name': 'web-grepy',
    'version': '1.1.0',
    'description': 'web-grep written in Python3',
    'long_description': "# web-grepy: CommandLine web-grep.py\n\n![](https://img.shields.io/static/v1?label=+&message=Python%203.9%2B&color=lightblue&logo=Python&style=flat-square)\n[![PyPI](https://img.shields.io/pypi/v/web-grepy.svg?style=flat-square)](https://pypi.python.org/pypi/web-grepy)\n\nRe-implementation [web-grep](https://github.com/cympfh/web-grep) with Python3,  \nScraping HTML or XML with simple Pattern Matching like `grep -o`.\n\n```bash\n# Requires Python3\n$ pip install web-grepy\n$ which web-grepy\n$ curl -sL https://example.com/xxx | web-grepy '<a href={}></a>'\n$ curl -sL https://example.com/xxx | web-grepy '<a href={link}>{text}</a>'  # ltsv by default\n$ curl -sL https://example.com/xxx | web-grepy '<a href={link}>{text}</a>' -f json\n```\n",
    'author': 'cympfh',
    'author_email': 'cympfh@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/cympfh/web-grepy/',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
