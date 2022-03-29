
import os
import tempfile
import pytest
from unittest.mock import patch
import EnvAlias


def test_name_exist():
    ea = EnvAlias
    assert ea.__title__ is not None


def test_version_exist():
    ea = EnvAlias
    assert ea.__version__ is not None
