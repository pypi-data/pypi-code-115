#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=7.0', ]

test_requirements = ['pytest>=3', ]

setup(
    author="Chinmay Shrinivas Joshi",
    author_email='chinmaysjoshi@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Shunya is all about creating something from nothing, a blank slate per se with some helpers on adrenaline",
    entry_points={
        'console_scripts': [
            'shunya=shunya.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='shunya',
    name='shunya',
    packages=find_packages(include=['shunya', 'shunya.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/chinmaysjoshi/shunya',
    version='0.0.1',
    zip_safe=False,
)
