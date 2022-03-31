# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['mailing_manager', 'mailing_manager.migrations']

package_data = \
{'': ['*'], 'mailing_manager': ['templates/admin/*', 'templates/tests/*']}

install_requires = \
['Django>=3.2.4,<4.0.0', 'django-mail-queue>=3.2.4,<4.0.0']

setup_kwargs = {
    'name': 'mailing-manager',
    'version': '0.1.1',
    'description': 'Basic mail template managing integrated with admin panel and django-mail-queue.',
    'long_description': None,
    'author': 'Codi Cooperatiu',
    'author_email': 'hola@codi.coop',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.6,<4.0',
}


setup(**setup_kwargs)
