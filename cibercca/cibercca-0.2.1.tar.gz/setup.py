# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['cibercca']

package_data = \
{'': ['*'], 'cibercca': ['inventory/*']}

install_requires = \
['PyYAML==6.0',
 'hvac==0.11.2',
 'napalm==3.3.1',
 'netmiko==3.4.0',
 'nornir==3.2.0',
 'openpyxl==3.0.9',
 'pandas==1.3.4',
 'tabulate==0.8.9',
 'tqdm==4.62.3',
 'ttp==0.8.1',
 'typer==0.4.0']

entry_points = \
{'console_scripts': ['ciberc-ca = cibercca.main:main']}

setup_kwargs = {
    'name': 'cibercca',
    'version': '0.2.1',
    'description': 'CiberC Code Automation - reports excel and json formats',
    'long_description': '# ciberc-ca\n\nCiberC Code Automation\n\n# Commands:\n\n```\nCommands:\n  alive       Alive for all device filter with groups\n  interfaces  Device interface information\n  inventory   Create files for inventory system\n  login       Login on (CiberC Code Automations) [not required]\n  ping        report por vrf and ping results for inventory devices\n  ping-merge  Command to merge the source vrf listing files and...\n```\n\n### Login command:\n\n```\nDescription: login on ciberc-ca for use\n\nOptions:\n  --name TEXT      The name user for ciberc-ca  [required]\n  --password TEXT  [required]\n\nExample:\n    $ ciberc-ca login --name=name-example\n        $ password:\n        $ Repeat for confirmation:\n```\n\n### Alive command:\n\n```\nDescription: ping report of all inventory devices\n\nOptions:\n  --path TEXT\n  --group TEXT\n  --workers INTEGER\n  --output TEXT\n\nExample:\n    $ ciberc-ca alive --path=inventory/ --group=guatemala --workers=4 --output=json > alive-report.json\n```\n\n### Inventory files command:\n\n```\nDescription: create the necessary files to create the cyberc-ca system inventory\n\nOptions:\n  --create / --no-create  create files from inventory examples  [default: no-create]\n\nExample:\n    $ ciberc-ca inventory --create\n```\n\n### Interfaces command:\n\n```\nDescription: report interfaces of cisco ios devices currently, generates report in json as a summary in excel\n    - BVI\n    - Vlans\n    - trunk interfaces\n    - bridge-domain\n    - mac-address-table dynamic\n\nOptions:\n  --path PATH        The path to inventory  [required]\n  --group TEXT       The groups to filter inventory [required]\n  --workers INTEGER  The parallel execution  [default: 2]\n  --output TEXT      The type to print report  [default: json]\n  --mechanism TEXT   The excel mechanism to print report\n  --name TEXT        The name of excel report\n\nExample:\n    $ ciberc-ca interfaces --path=core/inventory/ --output=json > interfaces.json\n    $ ciberc-ca interfaces --path=core/inventory/ --output=excel --mechanism=row --name=interfaces > interfaces.json\n```\n\n\n### Ping command:\n\n```\nDescription: report por vrf and ping results for inventory devices\n\nOptions:\n  --path PATH        The path to inventory  [required]\n  --group TEXT       The groups to filter inventory  [required]\n  --workers INTEGER  The parallel execution  [default: 2]\n  --output TEXT      The type to print report  [default: json]\n  --name TEXT        The name of the excel file\n  --process TEXT     what type of process for the vrf report [src, dst] [required]\n  --help             Show this message and exit.\n\nExample:\n    $ ciberc-ca ping --path=core/inventory/ --group=src,guatemala,escuintla --output=json --name=ReportPingSource --process=src\n    $ ciberc-ca ping --path=core/inventory/ --group=dst,guatemala,escuintla --output=json --name=ReportPingDestinations --process=dst\n```\n\n### Ping-Merge command:\n\n```\nDescription: Command to merge the source vrf listing files and destination with validated report\n\nOptions:\n  --file-src TEXT  Vrf origin listing file  [required]\n  --file-dst TEXT  Target vrf listing file  [required]\n  --output TEXT    The type to print report  [required]\n  --name TEXT      The name of the excel file\n  --help           Show this message and exit.\n\nExample:\n    $ ciberc-ca ping-merge --file-src=file_vrfs_source.json --file-dst=file_vrf_destinations.json --output=excel --name=ReporteMigrations\n\n```',
    'author': 'Rafael Garcia Sagastume',
    'author_email': 'rafael.garcia@ciberc.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
