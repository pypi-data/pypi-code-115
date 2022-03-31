from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import dfops._internal.constants as const
from dfops._internal.cli import main

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch

    from dfops._internal.types import Sequence


def test_no_argv(capsys: CaptureFixture, monkeypatch: MonkeyPatch) -> None:
    from dfops._internal.cli.main import _sys  # pylint: disable=import-outside-toplevel

    monkeypatch.setattr(_sys, "argv", [])

    assert main() == 0

    captured = capsys.readouterr()
    assert captured.err == ""


@pytest.mark.parametrize("args", (("-V",), ("--version",)))
def test_version(args: Sequence[str], capsys: CaptureFixture) -> None:
    assert main(const.NAME, *args) == 0

    captured = capsys.readouterr()
    assert captured.out == f"{const.NAME} {const.VERSION}\n"
    assert captured.err == ""
