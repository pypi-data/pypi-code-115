from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING

from dfops._internal.cli.io import ArgumentParser

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture


def test_no_args(capsys: CaptureFixture) -> None:
    parser = ArgumentParser()
    assert parser.run() == 0

    captured = capsys.readouterr()
    assert captured.err == ""

    with StringIO() as string_io:
        parser.print_help(string_io)
        assert captured.out == string_io.getvalue()
