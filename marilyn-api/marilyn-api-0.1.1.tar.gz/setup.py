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
    'version': '0.1.1',
    'description': 'Async client for Marilyn API',
    'long_description': '![Supported Python Versions](https://img.shields.io/static/v1?label=python&message=>=3.7&color=green)\n[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/vintasoftware/marilyn-api/master/LICENSE)\n[![Downloads](https://pepy.tech/badge/marilyn-api)](https://pepy.tech/project/marilyn-api)\n<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>\n\n\n# Async client for Marilyn API\n\n\n## Installation\n    \n    pip install marilyn-api\n\n## Examples\n\n```python\nfrom marilyn_api import AsyncClient\n\napi_root = "https://app.mymarilyn.ru"\nheaders = {\n    "X-API-Account": 100500,\n    "X-API-Token": "{auth token}",\n}\naclient = AsyncClient(api_root, headers=headers)\n\nbody = {\n    "channel_id": [],\n    "start_date": "2022-02-01",\n    "end_date": "2022-02-18",\n    "date_grouping": "day",\n    "grouping": "placement",\n    "filtering": [\n        {\n            "entity": "no",\n            "entities": []\n        },\n        {\n            "entity": "project",\n            "entities": [\n                4551\n            ]\n        }\n    ],\n    "custom_metrics": [],\n    "profiles": [],\n    "goals": [],\n    "with_vat": False,\n    "per_page": 200,\n    "sorting": "date",\n    "columns": [\n        "date",\n        "placement_id",\n        "placement_name",\n        "campaign_xid",\n        "channel_id",\n        "impressions",\n        "clicks",\n        "cpm_fact",\n        "reach_total_sum",\n        "viral_reach_total_sum",\n        "ctr",\n        "cost_fact",\n        "cpc_fact",\n        "orders",\n        "model_orders",\n        "revenue",\n        "revenue_model_orders"\n    ]\n}\n\nasync for page in aclient.iter_statistics_detailed(body):\n    for item in page["items"]:\n        print("RECORD:", item)\n\n```\n\n## Script examples\n\n```bash\npython Examples/statistics_detailed.py --help\npython Examples/statistics_detailed.py -r https://app.mymarilyn.ru -a 100500 -t MytoKeN12345 -c Examples/detailed-stats-config.json\n```\n\n```bash\npython Examples/project_placements.py.py --help\npython Examples/project_placements.py.py -r https://app.mymarilyn.ru -a 100500 -p 12345 -t MytoKeN12345\n```\n\n## Dependencies\n- aiohttp\n\n## Author\nPavel Maksimov\n\nYou can contact me at\n[Telegram](https://teleg.run/pavel_maksimow)\n\nУдачи тебе, друг! Поставь звездочку ;)',
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
