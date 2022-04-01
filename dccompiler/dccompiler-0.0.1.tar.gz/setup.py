# -------------------------------
# PipeBit
# 'setup.py'
# Author: Juan Carlos Juárez.
# Licensed under MPL 2.0.
# All rights reserved.
# -------------------------------

from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = 'Dynamo Charlotte Compiler'
LONG_DESCRIPTION = 'A Dynamo Charlotte Compiler for CLI.'

# Setting up
setup(
    name="dccompiler",
    version=VERSION,
    author="Juan Carlos Juárez",
    author_email="<jc.juarezgarcia@outlook.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[],
    keywords=['Dynamo Charlotte', 'Python', 'Compiler'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)