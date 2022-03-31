from importlib import import_module
from typing import Callable, Union

from cleo.application import Application as BaseApplication
from cleo.formatters.style import Style
from cleo.io.inputs.input import Input
from cleo.io.io import IO
from cleo.io.outputs.output import Output

from foresight.__version__ import __version__
from foresight.calendar.google_calendar import GoogleCalendar
from foresight.console.command_loader import CommandLoader
from foresight.console.commands.command import Command
from foresight.factory import Factory
from foresight.tracking.harvest import Harvest


def load_command(name: str) -> Callable:
    def _load() -> type[Command]:
        words = name.split(" ")
        module = import_module("foresight.console.commands." + ".".join(words))
        command_class = getattr(module, "".join(c.title() for c in words) + "Command")
        return command_class()

    return _load


COMMANDS = ["about", "join", "peek", "update"]


class Application(BaseApplication):
    def __init__(self) -> None:
        super().__init__("foresight", __version__)

        self._calendar = None
        self._harvest = None
        self._io: IO | None = None

        command_loader = CommandLoader({name: load_command(name) for name in COMMANDS})
        self.set_command_loader(command_loader)

    @property
    def calendar(self) -> "GoogleCalendar":
        if self._calendar is not None:
            return self._calendar

        self._calendar = Factory(self._io).create_google_calendar()

        return self._calendar

    @property
    def harvest(self) -> Harvest:
        if self._harvest is not None:
            return self._harvest

        self._harvest = Factory(self._io).create_harvest()

        return self._harvest

    @property
    def command_loader(self) -> CommandLoader:
        return self._command_loader

    def create_io(
        self,
        input: Union[Input, None] = None,
        output: Union[Output, None] = None,
        error_output: Union[Output, None] = None,
    ) -> IO:
        io = super().create_io(input, output, error_output)

        # Set our own CLI styles
        formatter = io.output.formatter
        formatter.set_style("c1", Style("blue"))
        formatter.set_style("c2", Style("magenta", options=["bold"]))

        io.output.set_formatter(formatter)
        io.error_output.set_formatter(formatter)

        self._io = io

        return io


def main() -> int:
    return Application().run()


if __name__ == "__main__":
    main()
