from foresight.console.commands.command import Command


class JoinCommand(Command):

    name = "join"

    description = "Attempts to join an upcoming meeting's <c1>zoom</c1> call."

    def handle(self) -> None:
        calendar = self.calendar

        upcoming_events = calendar.peek(1)
        if upcoming_events == []:
            self.error("No upcoming meetings.")
            return 1

        event = upcoming_events[0]
        self.line(event.concise())
        self.line("")
        self.line("Attempting to join...")

        error = event.join()
        if error:
            self.error(error)
            return 1

        return 0
