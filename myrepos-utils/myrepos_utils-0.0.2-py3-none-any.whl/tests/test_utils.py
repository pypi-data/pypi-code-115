#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) Meta Platforms, Inc. and affiliates.
#
# Fedora-License-Identifier: GPLv2+
# SPDX-2.0-License-Identifier: GPL-2.0+
# SPDX-3.0-License-Identifier: GPL-2.0-or-later
#
# This program is free software.
# For more information on the license, see COPYING.md.
# For more information on free software, see
# <https://www.gnu.org/philosophy/free-sw.en.html>.

import configparser
import os
from myrepos_utils import utils
from unittest import mock


REPOS = {
    "src/github/owner1/projA": {"checkout": "github clone owner1/projA"},
    "src/gitlab/owner2/projB": {"checkout": "gitlab clone owner2/projB"},
    "src/github/owner0/projC": {"checkout": "github clone owner0/projC"},
}


def get_mock_config():
    config = configparser.ConfigParser()
    config.read_dict(REPOS)
    mock_config = mock.MagicMock()
    mock_config.keys.return_value = config.keys()
    mock_config.sections.return_value = config.sections()
    mock_config.__getitem__.side_effect = config.__getitem__
    return mock_config


def test_get_repos():
    mock_config = get_mock_config()
    result = utils.get_repos(mock_config)
    # keys would include DEFAULT, it should not be called
    mock_config.keys.assert_not_called()
    mock_config.sections.assert_called_once()
    assert result == list(REPOS.keys())


def test_find_repo():
    mock_config = get_mock_config()
    result = utils.find_repo("gitlab", mock_config)
    mock_config.sections.assert_called_once()
    assert result == [os.path.expanduser("~/src/gitlab/owner2/projB")]

def test_sort():
    mock_config = get_mock_config()
    result = utils.sort(mock_config)
    assert len(result) == len(REPOS) + 1 # DEFAULT
    assert set(result.sections()) == set(REPOS.keys())
    assert result.sections() == sorted(result.sections())
