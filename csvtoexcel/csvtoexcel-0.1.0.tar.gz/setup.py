# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['csvtoexcel']

package_data = \
{'': ['*']}

install_requires = \
['openpyxl>=3.0.5,<4.0.0']

entry_points = \
{'console_scripts': ['csvtoexcel = csvtoexcel.csvtoexcel:main',
                     'exceltocsv = csvtoexcel.exceltocsv:main']}

setup_kwargs = {
    'name': 'csvtoexcel',
    'version': '0.1.0',
    'description': 'Command-line tool to convert CSV-files (.csv) to Excel-files (.xlsx)',
    'long_description': None,
    'author': 'Malthe Jørgensen',
    'author_email': 'malthe.jorgensen@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/malthejorgensen/csvtoexcel',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
