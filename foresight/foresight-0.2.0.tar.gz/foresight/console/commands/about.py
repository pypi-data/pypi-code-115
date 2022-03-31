from foresight.console.commands.command import Command


class AboutCommand(Command):

    name = "about"

    description = "Shows information about Foresight."

    def handle(self) -> None:
        self.line(f"<c1>Foresight - Time management tool.</c1>")
