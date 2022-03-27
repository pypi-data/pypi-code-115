# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Interactive package selection dialog """

import os
import zipfile

import mrtest.apk_installed


def get_apks_in_zip(zip_path):
    """
    :param zip_path: downloaded artifacts zip containing the apks
    :returns: list of paths inside the zip file like:
              ["packages/edge/aarch64/postmarketos-ui-phosh-18-r0.apk"m ...]
    """
    ret = []
    with zipfile.ZipFile(zip_path) as zip:
        for path in zip.namelist():
            if path.endswith(".apk"):
                ret += [path]
    return ret


def show_selection_short(apks, ret):
    """
    Print a short summary of how many packages have been selected.
    :param apks: list of all apks inside the zip file
    :param ret: list of selected apks inside the zip file
    """
    print(f"{len(ret)} of {len(apks)} selected.")


def show_selection(apks, ret):
    """
    Print the list of available packages, with a checkbox for each package.
    :param apks: list of all apks inside the zip file
    :param ret: list of selected apks inside the zip file
    """
    i = 1
    for apk in apks:
        sel = "X" if apk in ret else " "

        installed = mrtest.apk_installed.get_installed(apk)
        installed_str = ""
        if installed:
            installed_str = f" [installed: {installed}]"
        print(f"  {i}) [{sel}] {os.path.basename(apk)}{installed_str}")
        i += 1

    print("")


def toggle_installed(apks, ret):
    """
    Toggle all already instaleld packages.
    :param apks: list of all apks inside the zip file
    :param ret: list of selected apks inside the zip file
    :returns: updated version of ret
    """
    already_selected = True
    apks_installed = []

    for apk in apks:
        installed = mrtest.apk_installed_get_installed(apk)
        if installed:
            apks_installed += [apk]
        if apk not in ret:
            already_selected = False

    # Unselect all packages that are already installed
    if already_selected:
        ret = [x for x in ret if x not in apks_installed]
        return ret

    # Select all packages that are already installed
    for apk in apks_installed:
        if apk not in ret:
            ret += [apk]
    return ret


def show_commands():
    print("Commands:")
    print("  1-99: toggle this package")
    print("  a:    toggle all packages")
    print("  u:    toggle upgrade (or downgrade) of installed packages")
    print("  l:    list selection")
    print("  y:    confirm selection")
    print("  q:    quit")


def ask(zip_path):
    """ Ask the user which packages shall be installed or upgraded.
        :param zip_path: downloaded artifacts zip containing the apks
        :returns: paths inside the zip file of the packages that the user wants
                  to install, e.g. ["packages/edge/aarch64/postmarketos-ui-phosh-18-r0.apk"] """
    ret = []
    apks = get_apks_in_zip(zip_path)

    # Fill up cache and log message of getting these here
    mrtest.apk_installed.get_installed_all()

    print("Which packages to install?")
    print("")
    show_selection(apks, ret)
    show_selection_short(apks, ret)
    print()
    show_commands()
    print()

    while True:
        action = input("What now?> ")
        if action == "a":
            if len(ret) == len(apks):
                ret = []
            else:
                ret = apks.copy()
        elif action == "l":
            show_selection(apks, ret)
        elif action == "y":
            print("Selection confirmed")
            return ret
        elif action == "q":
            print("Quitting")
            exit(1)
        elif action == "u":
            ret = toggle_installed(apks, ret)
        elif int(action) >= 1 and int(action) <= len(apks):
            apk = apks[int(action) - 1]
            if apk in ret:
                ret = [x for x in ret if x != apk]
            else:
                ret += [apk]
        show_selection_short(apks, ret)
