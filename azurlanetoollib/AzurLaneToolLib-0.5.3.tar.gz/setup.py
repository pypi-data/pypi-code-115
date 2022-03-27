#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
THIS FILE IS PART OF AZUR LANE TOOL LIB BY MATT BELFAST BROWN
setup.py - The core part of the Azur Lane Tool.

Author: Matt Belfast Brown
E-mail: thedayofthedo@gmail.com
Create Date: 2021-07-10
Version Date: 2022-03-27
Version: 0.5.3

THIS PROGRAM IS FREE FOR EVERYONE,IS LICENSED UNDER GPL-3.0
YOU SHOULD HAVE RECEIVED A COPY OF GPL-3.0 LICENSE.

Copyright (C) 2021-2022 Matt Belfast Brown

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from setuptools import setup, find_packages

with open("Descriptiption.md", 'r', encoding="utf-8") as dest_pimd:
    long_description = dest_pimd.read()

setup(
    name="AzurLaneToolLib",
    version="0.5.3",

    author="Matt Belfast Brown",
    author_email="thedayofthedo@gmail.com",
    license="GPL-3.0 LICENSE",

    description="Tools lib for Azur Lane which game powered by ManJiu Shanghai",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=["pip", "azur_lane", "tool"],

    url="https://github.com/thedayofthedoctor/altl",
    project_urls={
        "Documentation": "http://belfast.web3v.work/program/doc/altl/",
    },

    packages=find_packages(),
    py_modules=['AzurLaneToolLib.__init__', 'AzurLaneToolLib.mode.mode_BlP_Cal', 'AzurLaneToolLib.mode.mode_EXP_Cal',
                'AzurLaneToolLib.mode.mode_KSN_Com', 'AzurLaneToolLib.mode.mode_CME_Cal',
                'AzurLaneToolLib.mode.mode_FCS_Cal', 'AzurLaneToolLib.mode.mode_FLE_Shi',
                'AzurLAneToolLib.data.data_FLE_Shi'],
    include_package_data=True,
    zip_safe=True,

    classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        ],
    platforms="any",
    install_requires=['lzstring'],
    python_requires=">=3.7"
)
