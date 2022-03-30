# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['nlp_analyser']

package_data = \
{'': ['*']}

install_requires = \
['LanguageIdentifier>=1.1.1,<2.0.0',
 'bertopic>=0.9.4,<0.10.0',
 'click==8.0.4',
 'pandas-profiling>=3.1.0,<4.0.0',
 'rich>=11.1.0,<12.0.0',
 'spacy>=3.2.1,<4.0.0',
 'streamlit>=1.8.0,<2.0.0']

entry_points = \
{'console_scripts': ['nlp_analyser = nlp_analyser.cli:cli']}

setup_kwargs = {
    'name': 'botpress-analyser',
    'version': '0.1.0',
    'description': 'A package to make clusters from a corpus',
    'long_description': '',
    'author': 'Pierre Snell',
    'author_email': 'pierre.snell@botpress.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
