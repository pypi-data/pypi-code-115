# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


setup(
    name='ghunt',
    version="0.1",
    packages=find_packages(),
    author="mxrch",
    install_requires=["httpx"],
    description="Dummy package to register the ghunt package name on pypi.",
    include_package_data=True,
    url='https://github.com/Malfrats/xeuledoc',
    entry_points = {'console_scripts': ['xeuledoc = xeuledoc.core:main']},
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
