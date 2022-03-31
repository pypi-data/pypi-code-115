from setuptools import setup, find_packages
import codecs
import os

VERSION = '0.0.2'
DESCRIPTION = 'test hello'
LONG_DESCRIPTION = 'try to add to pypi a test print hello'

# Setting up
setup(
    name="testhelloAlberPrueba",
    version=VERSION,
    author="Alberto",
    author_email="prueba@prueba.com",
    description=DESCRIPTION,
    packages=find_packages(),
    install_requires=['scanpy', 'pandas', 'numpy'],
    keywords=['python', 'AI'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)
