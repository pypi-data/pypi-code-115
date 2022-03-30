import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
#version_ns = {}  # type: ignore
#with open(os.path.join(here, "nbtermix", "_version.py")) as f:
#    exec(f.read(), {}, version_ns)

setup(
    name="mcplay",
    version="1.0.4",
    url="https://github.com/mtatton/mcplay",
    author="Michael Tatton",
    description="Music Console Player",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=["mcplay"],
    python_requires=">=3.7",
    install_requires=[
    ],
    entry_points={
        "console_scripts": ["mcplay = mcplay.play:main"],
    },
    classifiers=(
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Topic :: Terminals",
    ),
)
