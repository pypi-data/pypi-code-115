from typing import Dict


class Result:
    def __init__(self, response: Dict):
        self._status = response.get("status", "QUEUED")
        self._tracing = response.get("tracing", "")

    def get_status(self):
        return self._status

    def get_tracing(self):
        return self._tracing
