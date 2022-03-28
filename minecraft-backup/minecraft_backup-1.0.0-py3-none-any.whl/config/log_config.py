import minecraft_backup
from pathlib import Path

LOG_CONFIG_PATH: Path = Path(minecraft_backup.__path__[0]) / "data" / "log_config.json"
LOG_FILE_PATH: Path = Path(minecraft_backup.__path__[0] + "/data/logs/logfile.log")
