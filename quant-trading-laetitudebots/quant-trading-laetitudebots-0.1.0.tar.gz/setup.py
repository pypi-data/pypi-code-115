#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from typing import List

import setuptools


def requirements() -> List[str]:
    with open('requirements.txt') as fh:
        packages = fh.readlines()
        packages = [p.rstrip() for p in packages]
    return packages


setuptools.setup(
    name='quant-trading-laetitudebots',
    version='0.1.0',
    description='Laetitude Bots for Swapoo Labs',
    author='Swapoo Labs Trading - Quantitative Development',
    packages=setuptools.find_packages(),
    python_requires='>=3.7',
    install_requires=requirements(),
    # setup_requires=['pytest-runner'],
    # tests_require=['pytest-mock==3.1.1', 'pytest-asyncio==0.14.0'],
)
