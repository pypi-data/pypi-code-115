from __future__ import annotations

import argparse
import functools
import re as _re
from enum import IntFlag, auto
from gettext import gettext as _
from pathlib import Path
from typing import TYPE_CHECKING

import dfops._internal.constants as const
from dfops._internal.utils import import_string

from . import Command
from .inputs import Argument

if TYPE_CHECKING:
    from typing import ClassVar

    from dfops._internal.types import Iterable


class Verbosity(IntFlag):
    QUIET = auto()
    NORMAL = auto()
    VERBOSE = auto()
    VERY_VERBOSE = auto()


def verbosity_validator(verbosity: int) -> Verbosity:
    verbosity_tup = tuple(Verbosity)
    verbosity = max(verbosity, 0)

    try:
        return verbosity_tup[verbosity]
    except IndexError:
        return verbosity_tup[-1]


class ArgumentParser(argparse.ArgumentParser):
    __slots__ = ("_script_name",)

    SUBCOMMAND_DEST: ClassVar[str] = "subcommand"

    commands: Iterable[str] = "run", "help", "version"
    default_command: str | None = "help"

    arguments: Iterable[Argument] = (
        Argument("-h", "--help", action="help", description="Show help for a command"),
        Argument(
            "-V",
            "--version",
            action="version",
            version=f"%(prog)s {const.VERSION}",
            description="Show the program's version",
        ),
        Argument("-v", "--verbose", action="count", dest="verbosity", default=1),
    )

    def __init__(self, script_name: str | None = None) -> None:
        super().__init__(prog=const.NAME, add_help=False, allow_abbrev=False)

        if script_name is None:
            self._script_name = const.NAME
        else:
            self._script_name = Path(script_name).name

        self.commands = frozenset(self.commands)
        self.add_arguments()

    def add_arguments(self) -> None:
        for argument in self.arguments:
            argument.add_to_parser(self)

        subparsers = self.add_subparsers(
            parser_class=argparse.ArgumentParser,
            dest=self.SUBCOMMAND_DEST,
            required=self.default_command is None,
        )

        for command_name in self.commands:
            command_obj = self.get_subcommand(command_name)
            cmd_parser = subparsers.add_parser(
                command_obj.name, help=command_obj.description
            )

            for argument in command_obj.arguments:
                argument.add_to_parser(cmd_parser)

    @functools.lru_cache(maxsize=None)
    def get_subcommand(self, name: str) -> Command:
        command_class = import_string(
            self._subcommands_module,
            self._subcommand_module_name(name),
            self._subcommand_class_name(name),
        )

        if not issubclass(command_class, Command):
            raise TypeError(
                _("%r: must be a subclass of %r") % (command_class, Command)
            )

        return command_class(name, parser=self)

    def run(self, *args: str) -> int:
        try:
            namespace = self.parse_args(args)

            namespace.verbosity = verbosity_validator(namespace.verbosity)

            command_name = getattr(
                namespace, self.SUBCOMMAND_DEST, self.default_command
            )
            if command_name is None:
                command_name = self.default_command

            command = self.get_subcommand(command_name)

            return command.run(namespace)
        except SystemExit as err:
            return err.code

    @property
    def _subcommands_module(self) -> str:
        return self.__module__.rsplit(".", 2)[0] + ".commands"

    @staticmethod
    def _subcommand_module_name(command_name: str) -> str:
        return _re.sub(r"-", "_", command_name).lower()

    @staticmethod
    def _subcommand_class_name(command_name: str) -> str:
        return (
            "".join(part.title() for part in _re.split(r"-", command_name) if part)
            + "Command"
        )
