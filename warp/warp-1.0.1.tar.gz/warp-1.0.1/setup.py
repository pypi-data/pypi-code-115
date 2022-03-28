#!/usr/bin/env python

from setuptools import setup

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='warp',
    description='WARP: Wrapper around Replicated Processes',
    author='Willem Pienaar',
    license="Apache-2.0",
    author_email='pypi@willem.co',
    url='https://github.com/woop/warp',
    install_requires=['pykka', 'pandas', 'nucleonic'],
    long_description=long_description,
)
