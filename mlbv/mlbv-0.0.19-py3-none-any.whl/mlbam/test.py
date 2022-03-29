from dataclasses import dataclass, field
from datetime import datetime
from datetime import timedelta
from typing import Dict, Any


@dataclass
class GameRecord:
    game_pk: str
    seriesGameNumber: str = None
    # teams: Any = None
    # feed: Any = None
    teams: Dict[str, str] = None


def test():
    gr = GameRecord("asf")
    gr.seriesGameNumber = "0"
    gr.teams = dict()
    gr.teams["a"] = "b"
