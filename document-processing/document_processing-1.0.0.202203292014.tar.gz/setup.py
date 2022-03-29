#!/usr/bin/env python3

import os
import re
from datetime import datetime
from typing import List

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8") as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


def get_requirements() -> List[str]:
    req = list()
    with open("requirements.txt") as requirements:
        pattern = re.compile(r"^.*#egg=([\w]+)$")
        for line in requirements.read().splitlines():
            if pattern.match(line):
                req.append(pattern.findall(line)[0])
            else:
                req.append(line)
    return req


setup(
    version="1.0.0" + f".{datetime.utcnow().strftime('%Y%m%d%H%M')}",
    packages=find_packages(),
    install_requires=get_requirements(),
)
