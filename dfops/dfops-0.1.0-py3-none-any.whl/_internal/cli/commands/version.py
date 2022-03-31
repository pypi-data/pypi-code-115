from __future__ import annotations

from typing import TYPE_CHECKING

from dfops._internal.cli.io import Command

if TYPE_CHECKING:
    import argparse


class VersionCommand(Command):
    description = "Show the program's version"

    def run(self, args: argparse.Namespace) -> int:
        return self._parser.run("-V")
