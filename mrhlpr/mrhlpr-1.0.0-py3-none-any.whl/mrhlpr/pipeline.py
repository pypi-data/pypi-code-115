# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Parse output from gitlab's pipeline api. """

import platform


def get_arch_alpine_native():
    """ :returns: string for the architecture used in Alpine, e.g. 'armv7' """
    machine = platform.machine()

    mapping = {
        "i686": "x86",
        "x86_64": "x86_64",
        "aarch64": "aarch64",
        "armv6l": "armhf",
        "armv7l": "armv7"
    }
    if machine in mapping:
        return mapping[machine]
    raise ValueError(f"Cannot map platform.machine '{machine}' to the right Alpine Linux arch")


def get_build_job(api_pipeline_jobs):
    """ :param api_pipeline_jobs: dict from gitlab's pipelines/:id/jobs api
        :returns: job dict of the build job with the native arch or None """

    build_native = f"build-{get_arch_alpine_native()}"

    for job in api_pipeline_jobs:
        if job["name"] == build_native:
            return job

    return None
