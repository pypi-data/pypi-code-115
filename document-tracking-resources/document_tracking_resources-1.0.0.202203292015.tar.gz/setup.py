#!/usr/bin/env python3

import os
import re
from typing import List

from setuptools import find_packages, setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


def get_requirements() -> List[str]:
    req = list()
    print(os.getcwd())
    print(os.listdir())
    with open("./requirements.txt") as requirements:
        pattern = re.compile(r"^.*#egg=([\w]+)$")
        for line in requirements.read().splitlines():
            if pattern.match(line):
                req.append(pattern.findall(line)[0])
            else:
                req.append(line)
    return req


exec(open("document_tracking_resources/__init__.py").read())

# noinspection PyUnresolvedReferences
setup(
    version=__version__,
    packages=find_packages(),
    install_requires=get_requirements(),
)
