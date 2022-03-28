# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['ecs_scaling_scheduler', 'ecs_scaling_scheduler.aws_lambda_functions']

package_data = \
{'': ['*']}

install_requires = \
['boto3>=1.21,<2.0', 'compose-x-common>=0.4.4,<0.5.0']

setup_kwargs = {
    'name': 'ecs-scaling-scheduler',
    'version': '0.1.0',
    'description': 'Functions triggered on events to manage ECS Services scaling activities',
    'long_description': '=====================\necs-scaling-scheduler\n=====================\n\n\n.. image:: https://img.shields.io/pypi/v/ecs_scaling_scheduler.svg\n        :target: https://pypi.python.org/pypi/ecs_scaling_scheduler\n\nFunctions triggered on events to manage ECS Services scaling activities\n\n\n* Free software: MPL-2.0\n* Documentation: https://ecs-scaling-scheduler.readthedocs.io.\n\n\nFeatures\n--------\n\n* TODO\n\nCredits\n-------\n\nThis package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.\n\n.. _Cookiecutter: https://github.com/audreyr/cookiecutter\n.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage\n',
    'author': 'johnpreston',
    'author_email': 'john@compose-x.io',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
