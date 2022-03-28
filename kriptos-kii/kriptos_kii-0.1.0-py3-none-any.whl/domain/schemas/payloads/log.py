from .ipayload import IPayload
from ...errors.payload import MalformedPayloadException


class Log(IPayload):
    _valid_log_levels: list = [
        "info",
        "warning",
        "error"
    ]

    def __init__(self, level: str, message: str):
        self._level: str = level.strip()
        self._message: str = message.strip()

        if self._level not in self._valid_log_levels:
            raise MalformedPayloadException()

        if self._message.strip() == "":
            raise MalformedPayloadException()

    def to_dict(self):
        return {
            "level": self._level,
            "message": self._message
        }
