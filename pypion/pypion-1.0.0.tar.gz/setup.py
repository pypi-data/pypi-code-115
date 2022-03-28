#!/usr/bin/env python

from setuptools import setup, __version__
from pkg_resources import parse_version

minimum_version = parse_version('30.4.0')

if parse_version(__version__) < minimum_version:
    raise RuntimeError("Package setuptools must be at least version {}".format(minimum_version))

setup()
