# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['rpaframework_aws']

package_data = \
{'': ['*']}

setup_kwargs = {
    'name': 'rpaframework-aws',
    'version': '0.1.0',
    'description': 'AWS library for RPA Framework',
    'long_description': '# rpaframework-aws\n\nThis library enables Amazon AWS services for `RPA Framework`\\_\nlibraries, such as Textract and S3.\n\n.. \\_RPA Framework: https://rpaframework.org\n',
    'author': 'RPA Framework',
    'author_email': 'rpafw©robocorp.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'python_requires': '>=3.6.2,<4.0.0',
}


setup(**setup_kwargs)
