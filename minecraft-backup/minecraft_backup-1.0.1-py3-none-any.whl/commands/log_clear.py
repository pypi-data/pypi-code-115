from fabric.colors import green
from minecraft_backup.convenience import logger
from minecraft_backup.config import LOG_FILE_PATH


def clear(args):
    with open(LOG_FILE_PATH, "w") as f:
        f.write("")
    print(green("Deleted the log file."))
    logger.debug("Delte the log file")
