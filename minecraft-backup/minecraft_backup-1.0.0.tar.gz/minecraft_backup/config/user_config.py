import minecraft_backup
from pathlib import Path

USER_CONFIG_FILE_PATH: Path = (
    Path(minecraft_backup.__path__[0]) / "data" / "user_config.json"
)
