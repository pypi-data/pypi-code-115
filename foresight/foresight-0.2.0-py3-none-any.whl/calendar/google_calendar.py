import datetime
from typing import Any, List, Optional

from foresight.calendar.event import Event
from foresight.utils.auth import create_google_calendar_service


class GoogleCalendar:
    def __init__(self, service: Optional[Any] = None) -> None:
        self.service = service or create_google_calendar_service()

    def events(self, start_date: str, end_date: str) -> List[Event]:
        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=start_date,
                timeMax=end_date,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        return self._process(events)

    def peek(self, n: int = 1) -> List[Event]:
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time

        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=n,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        return self._process(events)

    def _process(self, events: list) -> List[Event]:
        return [Event(event) for event in events]
