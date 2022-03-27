#!/usr/bin/env python3
# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import re
import ast

from setuptools import setup, find_packages

from codecs import open
from os import path


here = path.abspath(path.dirname(__file__))
_version_re = re.compile(r'version\s+=\s+(.*)')

with open(path.join(here, 'mrhlpr/__init__.py'), 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='mrhlpr',
    version=version,
    description='postmarketOS tools for interacting with gitlab MRs',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='postmarketOS Developers',
    author_email='info@postmarketos.org',
    url='https://www.postmarketos.org',
    license='GPLv3',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='postmarketos gitlab',
    packages=find_packages(),
    extras_require={
        'completion': ['argcomplete'],
    },
    entry_points={
        'console_scripts': [
            'mrhlpr=mrhlpr.frontend:main',
            'mrtest=mrtest.frontend:main',
        ],
    },
    include_package_data=True,
)
