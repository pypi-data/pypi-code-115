from pathlib import Path
from click import ClickException

class ToolstackError(ClickException):
    """The base exception for any error originating from this fancy tool"""

class NoConfigFound(ToolstackError):
    """Raised when configuration is not found"""

    def __init__(self, directory:Path) -> None:
        if not isinstance(directory, str):
            directory = str(directory)

        super().__init__(f"Unable to find configuration in directory {directory}")

        self.directory = directory

class BeforeError(ToolstackError):

    def __init__(self, cmd:str) -> None:
        super().__init__(f"while trying to execute before action '{cmd}'")
        self.cmd = cmd

class AfterError(ToolstackError):

    def __init__(self, cmd:str) -> None:
        super().__init__(f"while trying to execute after action '{cmd}'")
        self.cmd = cmd