from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Any


class ResultsDbDatatypes(Enum):
    INTEGER = auto()
    REAL    = auto()
    TEXT    = auto()

@dataclass
class ResultsDbTableDefinition:
    name:    str
    columns: Dict[str, ResultsDbDatatypes]

@dataclass
class ResultsDbReport:
    name:    str
    columns: Dict[str, Any]
