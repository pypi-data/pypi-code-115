# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Verification of gitlab CI runners. """

import hashlib
import json
import logging
import os


def get_no_state_str(runner):
    """ Create a human-readable json string of runner, with information about
        current state (active or not) removed.
        :returns: json string """
    no_state = runner.copy()

    # All these keys basically say if the runner is online or not. If the user
    # trusted the runner while it was online, and it is now offline, the
    # packages it built are still trustworthy.
    no_state.pop("active")
    no_state.pop("paused")
    no_state.pop("online")
    no_state.pop("status")

    return json.dumps(no_state, indent=4)


def get_runner_trusted_path(no_state_str, mkdir=False):
    """ :param runner_no_state_str: as returned by get_no_state_str()
        :returns: path to store that the given runner is trusted """
    config_dir = f"{os.getenv('HOME')}/.config/mrhlpr/known_runners"
    if mkdir:
        os.makedirs(config_dir, exist_ok=True)

    key = hashlib.sha256(no_state_str.encode("utf-8")).hexdigest()
    return f"{config_dir}/{key}"


def is_runner_known(no_state_str):
    """
    :param no_state_str: from get_no_state_str()
    """
    path = get_runner_trusted_path(no_state_str, True)
    logging.debug(f" -> {path}")

    if not os.path.exists(path):
        return False

    with open(path, "r") as handle:
        return no_state_str == handle.read()


def mark_as_known(no_state_str):
    """
    :param no_state_str: from get_no_state_str()
    """
    path = get_runner_trusted_path(no_state_str, True)
    with open(path, "w") as handle:
        handle.write(no_state_str)
    print("Permanently added this runner to the list of known runners.")
    return


def verify(runner):
    """ Verify that a runner ist trusted, or ask the user if they want to trust
        it. Exit if the user does not trust it.
        :param runner: as returned from the gitlab jobs api:
                {"id": 12270837,
                 "description": "4-blue.shared.runners-manager.gitlab.com/default",
                 "ip_address": "34.74.35.215",
                 "active": true,
                 "paused": false,
                 "is_shared": true,
                 "runner_type": "instance_type",
                 "name": "gitlab-runner",
                 "online": true,
                 "status": "online"}
    """
    no_state_str = get_no_state_str(runner)
    if is_runner_known(no_state_str):
        return

    print("Packages have been built by unknown CI runner:")
    print(json.dumps(runner, indent=4))

    action = input("Are you sure you trust this CI runner (yes/no)? ")
    if action == "yes":
        mark_as_known(no_state_str)
        return
    elif action == "no":
        print("Not installing packages from untrusted CI runner, aborting.")
        exit(1)

    print("Not answered with 'yes' or 'no', aborting.")
    exit(1)
