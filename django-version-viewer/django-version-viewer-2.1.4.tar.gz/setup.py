# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['django_version_viewer',
 'django_version_viewer.templatetags',
 'django_version_viewer.tests']

package_data = \
{'': ['*'], 'django_version_viewer': ['templates/*']}

setup_kwargs = {
    'name': 'django-version-viewer',
    'version': '2.1.4',
    'description': 'Django app for viewing python packages and their versions',
    'long_description': None,
    'author': 'Imagescape',
    'author_email': 'info@imagescape.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/ImaginaryLandscape/django-version-viewer',
    'packages': packages,
    'package_data': package_data,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
