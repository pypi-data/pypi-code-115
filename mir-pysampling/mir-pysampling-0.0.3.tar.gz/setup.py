from setuptools import setup, find_packages
from pathlib import Path

name = "pysampling"
_name = name

# see https://packaging.python.org/guides/single-sourcing-package-version/
version_dict = {}
with open(Path(__file__).parents[0] / _name / "_version.py") as fp:
    exec(fp.read(), version_dict)
version = version_dict["__version__"]
del version_dict

setup(
    name="mir-"+name,
    version=version,
    author="Lixin Sun",
    python_requires=">=3.6.9",
    packages=find_packages(include=[name, _name, _name + ".*"]),
    install_requires=[
        "numpy",
        "matplotlib",
        "ase",
        "pyfile-utils",
        "ndsimulator",
    ],
    entry_points={
        # make the scripts available as command line scripts
        "console_scripts": [
            "pysampling = pysampling.scripts.run:main",
        ]
    },
    zip_safe=True,
)
