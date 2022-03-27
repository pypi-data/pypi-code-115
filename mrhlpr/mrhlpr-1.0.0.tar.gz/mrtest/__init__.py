# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Various small functions used in other files in mrtest. """

import os


def get_sudo():
    """ :returns: either "doas" or "sudo" """
    if os.path.exists("/usr/bin/doas"):
        return "doas"
    return "sudo"


def get_virtual_group(origin, mr_id):
    """ Generate a virtual group id to be passed to apk when installing
        packages from a merge request.
        :param origin: gitlab origin information, see gitlab.parse_git_origin()
        :param mr_id: merge request ID """
    return f".mrtest-{mr_id}-{origin['project']}"
