from typing import Any

from .insigth_type import InsightType
from .payloads import Log, Event
from ..errors.payload import InvalidPayloadException


class Insight:
    def __init__(self, enterprise_id: str, insight_type: InsightType, payload: Any):
        self._enterprise_id = enterprise_id
        self._insight_type = insight_type
        self._payload = payload

        if self._insight_type == InsightType.LOG and not isinstance(payload, Log):
            raise InvalidPayloadException()

        if self._insight_type == InsightType.EVENT and not isinstance(payload, Event):
            raise InvalidPayloadException()

    def to_dict(self):
        return {
            "enterprise_id": self._enterprise_id,
            "insight_type": self._insight_type.value,
            "payload": self._payload.to_dict()
        }
