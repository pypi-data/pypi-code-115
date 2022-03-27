# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Code interacting with apk (Alpine's package manager) """

import logging
import os
import subprocess

cache_installed_all = None


def get_installed_all():
    global cache_installed_all

    if cache_installed_all:
        return cache_installed_all

    print("Getting installed packages...")

    ret = {}
    cmd = ["apk", "info", "-vv"]
    logging.debug(f"+ {cmd}")
    output = subprocess.run(cmd, capture_output=True).stdout
    output = output.decode("utf-8")
    for line in output.split("\n"):
        if not line:
            continue
        if " - " not in line:
            print(f"ERROR: unexpected output from 'apk info -vv': {line}")
            exit(1)
        pkgname_version = line.split(" - ")[0]
        if pkgname_version.split("-")[-1:][0].startswith("r"):
            # package, ending in a version like 1.2.3-r5
            version = "-".join(pkgname_version.split("-")[-2:])
            pkgname = "-".join(pkgname_version.split("-")[:-2])
        else:
            # virtual package
            version = None
            pkgname = "-".join(pkgname_version.split("-")[:-1])
        ret[pkgname] = version

    cache_installed_all = ret
    return ret


def get_installed(pkg):
    """
    :param pkg: path to an apk file, ending in .../$pkgname-$version.apk
    """
    installed_all = get_installed_all()

    # Get pkgname from filename, e.g. "hello-world-1-r6.apk"
    pkgname = "-".join(os.path.basename(pkg).split("-")[:-2])

    if pkgname in installed_all:
        return installed_all[pkgname]
