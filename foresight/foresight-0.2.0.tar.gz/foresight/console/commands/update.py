from foresight.console.commands.command import Command


class UpdateCommand(Command):

    name = "update"

    description = "Records hours in <c1>Harvest</c1>."

    def handle(self) -> None:
        pass
