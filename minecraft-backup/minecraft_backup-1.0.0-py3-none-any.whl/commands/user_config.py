from fabric.colors import green, red
from minecraft_backup.convenience import logger
from minecraft_backup.convenience.user_config import Config


def config(args):
    CHANGE_LOGS_PATH = args.logs_path
    CHANGE_AUTO_DELETE_TARGET = args.delete_target
    CHANGE_AUTO_DELETE_TURN = args.auto_delete
    IS_NO_LOG = args.no_log

    if CHANGE_LOGS_PATH is not None:
        Config.change_logs_path(CHANGE_LOGS_PATH)

        if not IS_NO_LOG:
            logger.info(f"Change user config: Logs file path to {CHANGE_LOGS_PATH}.")
        print(green(f"Success to change logs path to {CHANGE_LOGS_PATH}."))

    if CHANGE_AUTO_DELETE_TARGET is not None:
        Config.change_delete_target(CHANGE_AUTO_DELETE_TARGET)

        if not IS_NO_LOG:
            logger.info(
                f"Change user config: Auto delete target to {CHANGE_AUTO_DELETE_TARGET}"
            )
        print(
            green(
                f"Success to change auto delete target to {CHANGE_AUTO_DELETE_TARGET}."
            )
        )

    if CHANGE_AUTO_DELETE_TURN:
        Config.turn_auto_delete()

        On_or_Off = "On" if Config.get_auto_delete() else "Off"

        if not IS_NO_LOG:
            logger.info(f"Change user config: Turn { On_or_Off } the auto delete.")

        if On_or_Off == "On":
            print(
                f"{ green('Success to turn') } { On_or_Off } { green('the auto delete.') }"
            )
        else:
            print(
                f"{ green('Success to turn') } { red(On_or_Off) } { green('the auto delete.') }"
            )
