from typing import TYPE_CHECKING, Union

import pendulum
from cleo.commands.command import Command as BaseCommand

from foresight.calendar.event import Event

if TYPE_CHECKING:
    from foresight.calendar.google_calendar import GoogleCalendar
    from foresight.console.application import Application
    from foresight.tracking.harvest import Harvest


class Command(BaseCommand):
    loggers: list[str] = []

    _harvest: Union["Harvest", None] = None
    _calendar: Union["GoogleCalendar", None] = None

    @property
    def calendar(self) -> "GoogleCalendar":
        if self._calendar is None:
            return self.get_application().calendar

        return self._calendar

    @property
    def harvest(self) -> "Harvest":
        if self._harvest is None:
            return self.get_application().harvest

        return self._harvest

    def set_calendar(self, calendar: "GoogleCalendar") -> None:
        self._calendar = calendar

    def set_harvest(self, harvest: "Harvest") -> None:
        self._harvest = harvest

    def get_application(self) -> "Application":
        return self.application
