# -*- coding: utf-8 -*-
from setuptools import setup

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

packages = \
['cvdastwrapper']

package_data = \
{'': ['*'],
 'cvdastwrapper': ['templates/*',
                   'templates/assets/images/*',
                   'templates/assets/images/charts/*',
                   'templates/assets/styles/*']}

install_requires = [
    'cvdast',
]

entry_points = \
{'console_scripts': ['cvdast-wrapper = cvdastwrapper.entry:main']}

setup_kwargs = {
    'name': 'cvdastwrapper',
    'version': '1.48.25',
    'description': 'This is a wrapper around CVDAST',
    'long_description': long_description,
    'long_description_content_type': 'text/markdown',
    'author': 'Bala Kumaran',
    'author_email': 'balak@cloudvector.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.5,<4.0',
}


setup(**setup_kwargs)
