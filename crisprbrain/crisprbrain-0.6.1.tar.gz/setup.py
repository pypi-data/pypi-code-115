# Copyright 2022 The CRISPRbrain.org Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import setuptools
import os

__PACKAGE_PATH = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(__PACKAGE_PATH, "README.md"), "r") as fp:
    long_description = fp.read()

with open(os.path.join(__PACKAGE_PATH, "requirements.txt"), "r") as fp:
    requirements = fp.read().split("\n")

setuptools.setup(
    name='crisprbrain',
    version="0.6.1",
    packages=setuptools.find_packages(),
    url='https://crisprbrain.org',
    license='Apache-2.0',
    author='CRISPRbrain',
    author_email='faraz@datatecnica.com',
    maintainer='Faraz Faghri',
    maintainer_email='faraz.faghri@gmail.com',
    description=('Data Commons for functional genomics screens '
                 'in differentiated human cell types'),
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    install_requires=requirements,
)
