#!/usr/bin/env python3

import re
from datetime import datetime
from typing import List

from setuptools import find_packages, setup


def get_requirements() -> List[str]:
    req = []
    with open("requirements.txt") as requirements:
        pattern = re.compile(r"^.*#egg=([\w]+)$")
        for line in requirements.read().splitlines():
            if pattern.match(line):
                req.append(pattern.findall(line)[0])
            else:
                req.append(line)
    return req


setup(
    version="1.0.2" + f".{datetime.utcnow().strftime('%Y%m%d%H%M')}",
    packages=find_packages(),
    install_requires=get_requirements(),
)
