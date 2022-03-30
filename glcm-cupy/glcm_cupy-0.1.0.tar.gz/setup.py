# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['glcm_cupy']

package_data = \
{'': ['*']}

install_requires = \
['scikit-image>=0.18.3,<0.19.0']

setup_kwargs = {
    'name': 'glcm-cupy',
    'version': '0.1.0',
    'description': 'Binned GLCM 5 Features implemented in CuPy',
    'long_description': None,
    'author': 'Evening',
    'author_email': None,
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8',
}


setup(**setup_kwargs)
