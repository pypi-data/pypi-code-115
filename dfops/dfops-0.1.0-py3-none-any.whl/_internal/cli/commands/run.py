from __future__ import annotations

import functools
import shlex
import shutil
import sys as _sys
from argparse import ArgumentTypeError
from gettext import gettext as _
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

import dfops._internal.constants as const
from dfops._internal.cli.io import Command
from dfops._internal.cli.io.argparse import Verbosity
from dfops._internal.cli.io.inputs import Argument
from dfops._internal.config import Config
from dfops._internal.utils import GitClient, cmd_output

if TYPE_CHECKING:
    from argparse import Namespace

    from dfops._internal.cli.io import ArgumentParser
    from dfops._internal.config import CommandConfig

yaml_load = functools.partial(
    yaml.load, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader)
)


def validate_config_file(config_file: str) -> Config:
    if config_file == "-":
        config_data_raw = _sys.stdin.read()
    else:
        config_path = Path(config_file)

        try:
            config_data_raw = config_path.read_text(encoding="utf-8")
        except OSError as err:
            args = {"filename": config_file, "error": err}
            message = _("can't open %(filename)r: %(error)s")
            raise ArgumentTypeError(message % args) from err

    config_data = yaml_load(config_data_raw)
    config = Config(**config_data)
    return config


class RunCommand(Command):
    description = "Run commands"

    arguments = (
        Argument(
            "-c",
            "--config",
            default=const.CONFIG_FILE,
            validator=validate_config_file,
            description="Path to the config file",
            dest="config",
            metavar="PATH",
        ),
        Argument(
            "--dry-run",
            action="store_true",
            description="Don't actually run commands",
        ),
        Argument(
            "-n",
            default=0,
            validator=int,
            description="Start n commits behind the " "current",
            dest="n",
        ),
        Argument(
            "commands",
            nargs="*",
            default=(),
            description="The command IDs/aliases to run",
            metavar="ID_OR_ALIAS",
        ),
        Argument("-v", "--verbose", action="count", dest="verbosity", default=1),
    )

    def __init__(self, name: str, *, parser: ArgumentParser) -> None:
        super().__init__(name, parser=parser)
        self._git_client = GitClient()

    def run(self, args: Namespace) -> int:
        return_code = 0
        for command in args.config.filter(*args.commands):
            cmd_return_code = self.__run(command, args)
            return_code |= cmd_return_code

            if cmd_return_code and command.exit_on_error:
                break

        return return_code

    # pylint: disable-next=unused-argument,no-self-use
    def __run(self, command: CommandConfig, args: Namespace) -> int:
        if args.n:
            diff_files = self._git_client.diff(*command.targets, n=args.n)
        else:
            diff_files = self._git_client.status(*command.targets)

        filtered_diff_files = tuple(filter(command.file_has_types, diff_files))

        if not filtered_diff_files and not command.always_run:
            return 0

        term_cols, _ = shutil.get_terminal_size()

        if args.verbosity >= Verbosity.NORMAL:
            entry = shlex.join(command.entry)
            print("=" * term_cols)
            header = " " + entry + (" \\" if filtered_diff_files else "")
            header += " " * (term_cols - len(header))
            print(header)

            num_files = len(filtered_diff_files)
            for i, file in enumerate(filtered_diff_files):
                header = "   " + file + ("" if i == num_files - 1 else " \\")
                header += " " * (term_cols - len(header))
                print(header)
            print("=" * term_cols)

        return_code, stdout, stderr = cmd_output(*command.entry, *filtered_diff_files)

        if args.verbosity >= Verbosity.VERBOSE and stdout:
            print(stdout)
        elif return_code and stdout:
            print(stdout)

        if stderr:
            print(stderr)

        return return_code
