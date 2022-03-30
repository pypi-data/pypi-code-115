#!/usr/bin/env python

from setuptools import setup

setup(
    name='MagPy_TMS',
    version='1.4',
    description='A Python toolbox for controlling Magstim TMS stimulators via serial communication',
    long_description='A Python toolbox for controlling Magstim TMS stimulators via serial communication',
    author='Nicolas McNair',
    author_email='nicolas.mcnair@sydney.edu.au',
    url='http://github.com/nicolasmcnair/magpy',
    classifiers=['Development Status :: 5 - Production/Stable',
                 'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                 'Programming Language :: Python :: 3'],
    keywords='TMS Magstim',
    packages=['magpy'],
    package_data={'magpy':['*.yaml']},
    python_requires='>=3.3',
    install_requires=['pyserial']
)
