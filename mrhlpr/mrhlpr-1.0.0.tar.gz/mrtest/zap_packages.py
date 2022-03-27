# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Remove packages previously added with 'mrtest add' """

import logging
import subprocess

import mrtest.apk_installed


def get_installed_mrtest_virtual_packages():
    ret = []
    pkgs = mrtest.apk_installed.get_installed_all()
    for pkgname, version in pkgs.items():
        if pkgname.startswith(".mrtest-"):
            ret += [pkgname]
    return ret


def remove_virtual():
    virtual = get_installed_mrtest_virtual_packages()
    if not virtual:
        print("No virtual '.mrtest' packages found, nothing to do.")
        return

    print("Virtual packages from previous 'mrtest add':")
    for pkgname in virtual:
        print(f"* {pkgname}")

    answer = input("Remove virtual packages and packages added with mrtest? [y/N] ")
    if answer != "y":
        print("Aborted.")
        exit(1)

    cmd = [mrtest.get_sudo(), "apk", "del"] + virtual

    print("Removing packages...")
    logging.debug(f"+ {cmd}")
    subprocess.run(cmd)

    print("All done!")


def zap_packages():
    remove_virtual()

    print()
    print("Note that 'mrtest zap' will only remove packages *added* during")
    print("'mrtest add'. If you want to revert package *upgrades*, run")
    print("'apk upgrade -a'. This will upgrade/downgrade all your packages")
    print("to the versions in the repositories.")
