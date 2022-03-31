import webbrowser
from re import A
from typing import Any, Dict, Optional

import pendulum
from pendulum import datetime

from foresight.tracking.project_task import ProjectTask
from foresight.utils.zoom import contains_zoom_link


class Event:
    def __init__(
        self,
        event: Optional[Dict[str, Any]] = None,
        client: Optional[str] = None,
        project: Optional[str] = None,
        task: Optional[str] = None,
        date: Optional[datetime] = None,
        duration: Optional[float] = None,
    ) -> None:
        if not (event or date or duration):
            raise ValueError(
                "Must provide either an event description, or a date and duration."
            )

        self.event = event

        labels = self.event.get("extendedProperties", {}).get("private", {})

        self._client = client or labels.get("client")
        self._project = project or labels.get("project")
        self._task = task or labels.get("task")

        self._date = date
        self._duration = duration

    @property
    def date(self) -> datetime:
        """The date the event took place."""
        if self._date is not None:
            return self._date

        start = self.event.get("start", {})
        if start is not None:
            self._date = pendulum.parse(start.get("dateTime"), tz=start.get("timeZone"))

        return self._date

    @property
    def duration(self) -> float:
        """The duration of the event in hours."""
        if self._duration is not None:
            return self._duration

        event = self.event

        start = event.get("start")
        end = event.get("end")

        if not (start and end):
            raise ValueError(
                "You must either provide event information with start and end times, or provide a duration value on init."
            )

        start = pendulum.parse(start["dateTime"], tz=start["timeZone"])
        end = pendulum.parse(end["dateTime"], tz=end["timeZone"])

        self._duration = (
            end - start
        ).in_minutes() / 60.0  # Capture durations < 1 hour.

        return self._duration

    def project_task(self) -> ProjectTask:
        """Create a project task from the event."""
        if not self._client and self._project and self._task:
            raise ValueError(
                "Creation of project task requires client, project, and task name to be defined."
            )

        return ProjectTask(
            client=self._client,
            project=self._project,
            task=self._task,
            date=self.date,
            duration=self.duration,
        )

    def join(self) -> Optional[str]:
        link = self.zoom_link()
        if link is None:
            return "Could not locate a zoom link inside the calendar event."

        webbrowser.open(link)

    def zoom_link(self) -> Optional[str]:
        location = self.event.get("location", "")
        link = contains_zoom_link(location)
        if link is not None and isinstance(link, str):
            return link

        entries = self.event.get("conferenceData", {}).get("entryPoints", [])
        for entry in entries:
            label = entry.get("uri", "")
            link = contains_zoom_link(label)
            if link is not None and isinstance(link, str):
                return link

        description = self.event.get("description", "")
        link = contains_zoom_link(description)
        if link is not None and isinstance(link, str):
            return link

        return None

    def concise(self) -> str:
        status_labels = {
            "accepted": "🟢",
            "needsAction": "🟡",
            "tentative": "🟡",
            "declined": "🔴",
        }
        attendees = self.event.get("attendees", [])
        if attendees == []:
            pretty_attendees = "None"
        else:
            pretty_attendees = []
            for attendee in attendees:
                email = attendee.get("email")
                status = attendee.get("responseStatus")

                status_label = status_labels.get(status, "🔴")

                name = f"<{email}> {status_label}"
                pretty_attendees.append(name)

                spacing = "\n              "
            pretty_attendees = spacing.join(pretty_attendees)

        summary = self.event.get("summary")
        creator_name = self.event.get("creator").get("displayName")
        creator_email = self.event.get("creator").get("email")
        if creator_name is not None:
            creator = f"{creator_name} <{creator_email}>"
        else:
            creator = f"<{creator_email}>"

        start = self.event.get("start")
        end = self.event.get("end")

        if not (start and end):
            raise ValueError(
                "You must either provide event information with start and end times, or provide a duration value on init."
            )

        start = pendulum.parse(
            start["dateTime"], tz=start["timeZone"]
        ).to_day_datetime_string()
        end = pendulum.parse(
            end["dateTime"], tz=end["timeZone"]
        ).to_day_datetime_string()

        pretty_event = f"""\
Meeting Name: {summary}
Creator:      {creator}
Starts At:    {start}
Ends At:      {end}
Attendees:    {pretty_attendees}
"""
        zoom_link = self.zoom_link()
        if zoom_link is not None:
            pretty_event += f"Zoom Link:    {zoom_link}"

        return pretty_event

    def _getattr__(self, key: str) -> Any:
        return self.event.get(key)
