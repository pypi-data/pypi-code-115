# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['house_prices']

package_data = \
{'': ['*']}

install_requires = \
['catboost>=1.0.4,<2.0.0',
 'category-encoders>=2.4.0,<3.0.0',
 'eli5>=0.11.0,<0.12.0',
 'ipdb>=0.13.9,<0.14.0',
 'ipython>=8.1.1,<9.0.0',
 'jupyter>=1.0.0,<2.0.0',
 'lightgbm>=3.3.2,<4.0.0',
 'matplotlib>=3.5.1,<4.0.0',
 'optuna>=2.10.0,<3.0.0',
 'pandas-profiling>=3.1.0,<4.0.0',
 'plotly>=5.6.0,<6.0.0',
 'scikit-learn>=1.0.2,<2.0.0',
 'seaborn>=0.11.2,<0.12.0',
 'sklearn-transformer-extensions>=0.2.2,<0.3.0',
 'xgboost>=1.5.2,<2.0.0']

setup_kwargs = {
    'name': 'house-prices',
    'version': '0.1.0',
    'description': '',
    'long_description': None,
    'author': 'Your Name',
    'author_email': 'you@example.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
