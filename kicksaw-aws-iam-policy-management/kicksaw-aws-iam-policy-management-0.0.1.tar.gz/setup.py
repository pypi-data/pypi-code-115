# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['kicksaw_aws_iam_policy_management']

package_data = \
{'': ['*']}

install_requires = \
['boto3>=1.17.3,<2.0.0', 'click>=8.1.1,<9.0.0']

entry_points = \
{'console_scripts': ['iam-mgmt = kicksaw_aws_iam_policy_management.cli:main']}

setup_kwargs = {
    'name': 'kicksaw-aws-iam-policy-management',
    'version': '0.0.1',
    'description': 'Provides a shell utility for managing an iam policy within your repo. Typically useful for tracking a deploy policy in your codebase and pushing updates to said policy right from your repo.',
    'long_description': '# Install\n\n```\niam-mgmt\n```',
    'author': 'Alex Drozd',
    'author_email': 'alex@kicksaw.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/Kicksaw-Consulting/kicksaw-aws-iam-policy-management',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
