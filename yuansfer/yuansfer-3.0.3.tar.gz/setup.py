# -*- coding: utf-8 -*-

import sys
from setuptools import setup, find_packages

if sys.version_info[0] < 3:
    with open('README.md', 'r') as fh:
        long_description = fh.read()
else:
    with open('README.md', 'r', encoding='utf-8') as fh:
        long_description = fh.read()

setup(
    name='yuansfer',
    version='3.0.3',
    description='Use Yuansfer SDK to manage and run business including payment, refund, customer',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Shawn Zheng',
    author_email='shawn@yuansfer.com',
    url='https://docs.yuansfer.com/',
    packages=find_packages(),
    install_requires=[
        'requests>=2.9.1, <3.0',
        'python-dateutil>=2.5.3, <3.0',
        'deprecation>=2.0.6'
    ],
    tests_require=[
        'nose>=1.3.7'
    ],
    test_suite = 'nose.collector'
)