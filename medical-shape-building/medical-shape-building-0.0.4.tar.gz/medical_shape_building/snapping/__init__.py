from enum import Enum
from typing import Any

from medical_shape_building.snapping.snapper import PointSnapper, SnappingTransform
from medical_shape_building.snapping.strategy import (
    DistanceSnappingStrategy,
    IdentitySnappingStrategy,
    LocalNormalSnappingStrategy,
    NormalSnappingStrategy,
    SnappingStrategy,
)


# Reimplementation of LightningEnum to get full class not only string version
class SnappingStrategies(Enum):
    IDENTITY = IdentitySnappingStrategy
    DISTANCE = DistanceSnappingStrategy
    NORMALS = NormalSnappingStrategy
    LOCALNORMAL = LocalNormalSnappingStrategy

    @classmethod
    def from_str(cls, value: str) -> "SnappingStrategies":
        statuses = [status for status in dir(cls) if not status.startswith("_")]
        for st in statuses:
            if str(st).lower() == str(value).lower():
                return getattr(cls, st)
        raise ValueError(f"{value} is not a valid SnappingStrategies")

    def __eq__(self, other: Any) -> bool:
        other = other.value if isinstance(other, Enum) else str(other)
        return str(self.value).lower() == str(other).lower()

    def __hash__(self) -> int:
        # re-enable hashtable so it can be used as a dict key or in a set
        # example: set(LightningEnum)
        return hash(str(self.value).lower())


__all__ = [
    "PointSnapper",
    "SnappingTransform",
    "SnappingStrategy",
    "IdentitySnappingStrategy",
    "DistanceSnappingStrategy",
    "NormalSnappingStrategy",
    "LocalNormalSnappingStrategy",
]
