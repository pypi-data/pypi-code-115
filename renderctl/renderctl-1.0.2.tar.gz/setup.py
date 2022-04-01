#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: 1058449090@qq.com


from setuptools import find_packages, setup
import os


URL = 'https://github.com/penny1027/renderctl.git'
NAME = 'renderctl'
VERSION = os.getenv('RENDERCTL_VER')
#VERSION = 'v1.0.1'
DESCRIPTION = 'RENDER CTL Tool'
if os.path.exists('README.md'):
    with open('README.md', encoding='utf-8') as f:
        LONG_DESCRIPTION = f.read()
else:
    LONG_DESCRIPTION = DESCRIPTION
AUTHOR = 'Penny'
AUTHOR_EMAIL = '1058449090@qq.com'
LICENSE = 'MIT'
PLATFORMS = [
    'any',
]
REQUIRES = [
    'PyYAML',
    'jinja2',
]
CONSOLE_SCRIPTS = 'renderctl=renderctl.main:main'

setup(
    name=NAME,
    version=VERSION,
    description=(
        DESCRIPTION
    ),
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    maintainer=AUTHOR,
    maintainer_email=AUTHOR_EMAIL,
    license=LICENSE,
    packages=find_packages(),
    platforms=PLATFORMS,
    url=URL,
    install_requires=REQUIRES,
    entry_points={
        'console_scripts': [CONSOLE_SCRIPTS],
    }
)
