"""Exceptions for pyiocare."""

from typing import Any


class IoCareError(Exception):
    """Error from Coway API."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception."""
        Exception.__init__(self, *args)
