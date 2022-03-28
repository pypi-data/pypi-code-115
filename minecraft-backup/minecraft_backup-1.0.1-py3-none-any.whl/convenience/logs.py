import os
import json
from logging import getLogger, config, Logger
from minecraft_backup.convenience.user_config import Config
from minecraft_backup.config import LOG_CONFIG_PATH, LOG_FILE_PATH

if Config.is_user_changed_logs_path_config():
    LOG_CONFIG_PATH = Config.get_logs_path()

if os.path.exists(LOG_CONFIG_PATH):
    with open(LOG_CONFIG_PATH, "r") as f:
        log_conf = json.load(f)
else:
    raise FileNotFoundError(LOG_CONFIG_PATH)

logger: Logger = getLogger(__name__)

if log_conf["handlers"]["fileHandler"]["filename"] == "to be replaced":
    log_conf["handlers"]["fileHandler"]["filename"] = LOG_FILE_PATH

config.dictConfig(log_conf)