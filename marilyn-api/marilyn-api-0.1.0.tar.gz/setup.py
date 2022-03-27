# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['marilyn_api']

package_data = \
{'': ['*']}

install_requires = \
['aiohttp>=3.8.1,<4.0.0']

setup_kwargs = {
    'name': 'marilyn-api',
    'version': '0.1.0',
    'description': 'Async client for Marilyn API',
    'long_description': '```bash\npython Examples/statistics_detailed.py --help\npython Examples/statistics_detailed.py -r https://app.mymarilyn.ru -a 100500 -t MytoKeN12345 -c Examples/detailed-stats-config.json\n```\n\n```bash\npython Examples/project_placements.py.py --help\npython Examples/project_placements.py.py -r https://app.mymarilyn.ru -a 100500 -p 12345 -t MytoKeN12345\n```\n\n',
    'author': 'pmaksimov',
    'author_email': 'vur21@ya.ru',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/pavelmaksimov/marilyn-api',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
