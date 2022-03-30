from setuptools import find_packages, setup

from distutils.core import setup

setup(name = "nlutils-mini",
    version = "0.0.2",
    description = "Toolkit for neural learning training",
    author = "Nikola Liu",
    author_email = "nikolaliu@icloud.com",
    py_modules=['nlutils_mini'],
    packages = find_packages(),
    install_requires=[
        'coloredlogs',
        'tqdm',
    ],
)