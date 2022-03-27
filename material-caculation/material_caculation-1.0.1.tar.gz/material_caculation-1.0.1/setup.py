#!/usr/bin/env python
from __future__ import print_function
from setuptools import setup, find_packages
import sys

setup(
    name="material_caculation",
    version="1.0.1",
    author="jeffery",
    author_email="lizuobang@163.com",
    description="hmaterial caculation script",
    long_description=open("README.rst").read(),
    platforms=["all"],  # 平台
    license="MIT",
    url="https://github.com/Jeffreyliming/pandas_test",
    packages=["material_caculation"],
    install_requires=[
        "pandas",
        "flask"
    ],
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Indexing",
        "Topic :: Utilities",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3.8",
    ],
)