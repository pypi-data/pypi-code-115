"""
Errors module.
"""


class UnsupportedDriverException(Exception):
    """
        Raised when an unsupported driver executable is used.
        """

    def __init__(self, driver_path: str):
        super().__init__(f"The driver located at '{driver_path}' is not supported.")
