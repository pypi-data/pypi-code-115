import os
import re

import setuptools


def read(filename):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
    with open(path, 'r') as f:
        return f.read()


def find_version(text):
    match = re.search(r"^__version__\s*=\s*['\"](.*)['\"]\s*$", text,
                      re.MULTILINE)
    return match.group(1)


AUTHOR = "Conservation Technology Lab at the San Diego Zoo Wildlife Alliance"
DESC = ("Experiments, packages, and other tools for performing automatic "
        "detection of animal sounds in audio recordings.")

setuptools.setup(
    name="area42",
    version=find_version(read('area42/__init__.py')),
    author=AUTHOR,
    description=DESC,
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url="https://github.com/icr-ctl/area42",
    license="MIT",
    packages=['area42'],
    include_package_data=True,
    install_requires=[
        'matplotlib',
        'numpy',
        'pandas',
        'sounddevice',
        'tensorflow',
        'tensorflow_hub',
        'tensorflow_io'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering'
    ]
)
