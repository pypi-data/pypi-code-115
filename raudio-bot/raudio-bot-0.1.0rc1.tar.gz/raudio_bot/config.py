from dataclasses import dataclass
import json
import os
from typing import Optional

@dataclass
class RaudioConfig:
    """A Dataclass containing the configuration for the bot

        Note: Properties prefixed with '_' are considered private. These should
        not be printed out to the user as it might contain sensitive data
    """
    _config_file_path: Optional[str]
    authenticated: list[int]
    stream_url: str


def raudio_config_from_json(file_name) -> RaudioConfig:
    if os.path.exists(file_name):
        with open(file_name) as f:
            data = json.load(f)

        return RaudioConfig(**data, _config_file_path=os.path.abspath(file_name))
