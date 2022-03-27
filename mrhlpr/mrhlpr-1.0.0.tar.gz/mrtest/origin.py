# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Origin information about gitlab instances relevant to mrtest, in the format
    needed for mrhlpr.gitlab.parse_git_origin(). """

pmaports = {"api": "https://gitlab.com/api/v4",
            "api_project_id": "postmarketOS%2Fpmaports",
            "full": "git@gitlab.com:postmarketOS/pmaports.git",
            "project": "postmarketOS",
            "project_id": "postmarketOS/pmaports",
            "host": "gitlab.com"}

aports = {"api": "https://gitlab.alpinelinux.org/api/v4",
          "api_project_id": "alpine%2Faports",
          "full": "git@gitlab.alpinelinux.org:alpine/aports.git",
          "project": "alpine",
          "project_id": "alpine/aports",
          "host": "gitlab.alpinelinux.org"}
