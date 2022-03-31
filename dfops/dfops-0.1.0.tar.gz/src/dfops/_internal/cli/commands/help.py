from __future__ import annotations

from typing import TYPE_CHECKING

from dfops._internal.cli.io import Command
from dfops._internal.cli.io.inputs import Argument

if TYPE_CHECKING:
    import argparse


class HelpCommand(Command):
    description = "Show help for a specific command"

    arguments = (
        Argument(
            "help_cmd", nargs="*", default=[], description="Command to show help for"
        ),
    )

    def run(self, args: argparse.Namespace) -> int:
        help_cmd = getattr(args, "help_cmd", [])

        return self._parser.run(*help_cmd, "-h")
