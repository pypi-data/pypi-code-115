from setuptools import setup, find_packages
import codecs
import os

VERSION = '0.0.4'
DESCRIPTION = 'milan'
LONG_DESCRIPTION = 'package for testing elastic bug'

# Setting up
setup(
    name="elastic-transports",
    version=VERSION,
    author="milan",
    author_email="milankatwal2056@gmail.com",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[],
    keywords=['arithmetic', 'math', 'mathematics', 'python tutorial', 'avi upadhyay'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)
