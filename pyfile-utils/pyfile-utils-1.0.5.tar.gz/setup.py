from setuptools import setup, find_packages
from pathlib import Path

package_names = ["pyfile", "utils"]
_name = "_".join(package_names)
name = "-".join(package_names)

# see https://packaging.python.org/guides/single-sourcing-package-version/
version_dict = {}
with open(Path(__file__).parents[0] / _name / "_version.py") as fp:
    exec(fp.read(), version_dict)
version = version_dict["__version__"]
del version_dict

setup(
    name=name,
    version=f"{version}",
    author="Lixin Sun",
    author_email="nw13mifaso@gmail.com",
    description="A collection of utils for file write/load and instantiation",
    url="https://github.com/mir-group/PyfileUtils",
    python_requires=">=3.6.9",
    packages=find_packages(include=[name, _name, _name + ".*"]),
    install_requires=[
        "numpy",
        "pyyaml",
        "contextvars",
    ],
    zip_safe=True,
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
