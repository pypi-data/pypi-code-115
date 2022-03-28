# -*- coding: utf-8 -*-
import argparse
from . import commands
from fabric.colors import red


def main():
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="""\
        This is a backup management library for Minecraft servers.
        It should be run and used on a regular basis using cron or similar.
        """
    )

    subparser: argparse._SubParsersAction = parser.add_subparsers(
        dest="command", help="Normal Command"
    )

    # Backup Commands
    parser_backup: argparse.ArgumentParser = subparser.add_parser(
        "backup", help="Command to backup your minecraft folder. see `backup -h`"
    )
    parser_backup.set_defaults(handler=commands.backup)

    parser_backup.add_argument(
        "minecraft_folder", help="Write the Minecraft folder path."
    )

    parser_backup.add_argument(
        "backup_folder", help="Write the folder path should you want to save backup."
    )

    parser_backup.add_argument(
        "--no-log", help="Mode to don't save the backup log.", action="store_true"
    )

    parser_backup_group = parser_backup.add_mutually_exclusive_group()
    parser_backup_group.add_argument(
        "-z", "--zip", help="Mode to save and compress to zip", action="store_true"
    )

    parser_backup_group.add_argument(
        "-t",
        "--tar",
        help="Mode to save and compress to tgz/tar.gz",
        action="store_true",
    )

    parser_backup_group.add_argument(
        "-tz",
        "--tar-zip",
        help="Mode to save and compress to zip and tgz/tar.gz",
        action="store_true",
    )

    # log Commands
    parser_log: argparse.ArgumentParser = subparser.add_parser(
        "clear", help="Clear the all logs of backup. see `clear -h`"
    )
    parser_log.set_defaults(handler=commands.clear)

    # Config Commands
    parser_config: argparse.ArgumentParser = subparser.add_parser(
        "config",
        help="You can change or check the config of backup management. see `config -h`",
    )
    parser_config.set_defaults(handler=commands.config)

    parser_config.add_argument(
        "-lg",
        "--logs-path",
        help="You can change the path of logs. (Default path is minecraft_backup.__path__/data/user_config.json) {}".format(
            red('Warning! When you use this command you will be lost your log data. I recommend saving the files if you need to do it before doing it. ')
        )
    )

    parser_config.add_argument(
        "-dt",
        "--delete-target",
        help="Setting of auto delete target. Example: `0y7d00h00m00s` (You can just setting to 7d)",
    )

    parser_config.add_argument(
        "-ad",
        "--auto-delete",
        help="You can turn off/on auto delete.",
        action="store_true",
    )

    parser_config.add_argument(
        "--no-log", help="Mode to don't save the config log.", action="store_true"
    )

    args = parser.parse_args()

    if hasattr(args, "handler"):
        args.handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
