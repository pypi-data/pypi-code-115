from cleo.helpers import option

from foresight.console.commands.command import Command


class PeekCommand(Command):

    name = "peek"

    description = "Preview the next upcoming meeting."

    options = [
        option("count", description="The number of meetings to preview", flag=False)
    ]

    def handle(self) -> None:
        calendar = self.calendar

        event_count = self.option("count") or 1
        upcoming_events = calendar.peek(event_count)

        if upcoming_events == []:
            self.error("No upcoming meetings.")
            return 1

        self.line(f"Showing {event_count} upcoming meetings.")
        self.line("")

        for event in upcoming_events:
            self.line(event.concise())
            self.line("")

        return 0
