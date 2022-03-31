import setuptools
from sys import platform

# py_cui setup
setuptools.setup(
    name="py_cui_fork",
    description="A widget and grid based framework for building command line user interfaces in python.",
    version="0.0.2",
    author="fork",
    license="BSD (3-clause)",
    packages=setuptools.find_packages(exclude=["docs", "tests", "examples", "venv"]),
    install_requires=['windows-curses ; platform_system=="Windows"'],
    url="https://github.com/PabloLec/py_cui",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="cui cli commandline user-interface ui",
    python_requires=">=3.6",
)
