import re
import os
import stat
import glob
import shutil
import textwrap
from pathlib import Path
from enum import IntEnum
from .user_config import Config
from fabric.colors import green
from typing import TypeVar, Generic, Dict, Union
from datetime import datetime, timedelta, timezone

from . import logger

T = TypeVar("T")


now = datetime.now()


class CompressType(IntEnum):
    NONE = 0
    ZIP = 1
    TAR = 2
    TAR_AND_ZIP = 4


class File(Generic[T]):
    def __init__(
        self,
        minecraft_folder: Union[str, Path],
        backup_folder: Union[str, Path],
        compress_type: CompressType,
        is_no_log: bool,
    ):
        if type(minecraft_folder) == str:
            minecraft_folder = Path(minecraft_folder).resolve()
        else:
            minecraft_folder = minecraft_folder.resolve()

        if type(backup_folder) == str:
            backup_folder = Path(backup_folder).resolve()
        else:
            backup_folder = backup_folder.resolve()

        if minecraft_folder == backup_folder:
            raise TypeError(
                "The minecraft folder path and backup folder path shouldn't be the same."
            )

        self.minecraft_folder: Union[str, Path] = minecraft_folder
        self.backup_folder: Union[str, Path] = backup_folder
        self.is_no_log: bool = is_no_log
        self.compress_type: CompressType = compress_type

    def backup(self):
        if self.compress_type == CompressType.NONE:
            shutil.copytree(
                self.minecraft_folder,
                self.backup_folder
                / f"{self.minecraft_folder.name}_{now.strftime('%Y-%m-%d_%Hh-%Mm-%Ss')}",
            )
            if self.is_no_log:
                logger.info(
                    f"{self.minecraft_folder.name}: Backup none compress at {self.backup_folder}"
                )
            print(green("Success to create backup none compressed!"))
        elif self.compress_type == CompressType.ZIP:
            shutil.make_archive(
                self.backup_folder
                / f"{self.minecraft_folder.name}_{now.strftime('%Y-%m-%d_%Hh-%Mm-%Ss')}",
                "zip",
                root_dir=self.minecraft_folder,
            )
            if self.is_no_log:
                logger.info(
                    f"{self.minecraft_folder.name}: Backup zip compress at {self.backup_folder}"
                )
            print(green("Success to create backup and compressed to zip!"))
        elif self.compress_type == CompressType.TAR:
            shutil.make_archive(
                self.backup_folder
                / f"{self.minecraft_folder.name}_{now.strftime('%Y-%m-%d_%Hh-%Mm-%Ss')}",
                "gztar",
                root_dir=self.minecraft_folder,
            )
            if self.is_no_log:
                logger.info(
                    f"{self.minecraft_folder.name}: Backup tar.gz compress at {self.backup_folder}"
                )
            print(green("Success to create backup and compressed to tar.gz!"))
        elif self.compress_type == CompressType.TAR_AND_ZIP:
            shutil.make_archive(
                self.backup_folder
                / f"{self.minecraft_folder.name}_{now.strftime('%Y-%m-%d_%Hh-%Mm-%Ss')}",
                "gztar",
                root_dir=self.minecraft_folder,
            )

            shutil.make_archive(
                self.backup_folder
                / f"{self.minecraft_folder.name}_{now.strftime('%Y-%m-%d_%Hh-%Mm-%Ss')}",
                "zip",
                root_dir=self.minecraft_folder,
            )

            if self.is_no_log:
                logger.info(
                    f"{self.minecraft_folder.name}: Backup zip and tar.gz compress at {self.backup_folder}"
                )
            print(green("Success to create backup and compressed to zip/tar.gz"))

    def auto_delete(self):
        file_target = Config.get_delete_target()
        times_list = []
        match_list = [
            "[0-9]{,2}y",
            "[0-9]{,2}d",
            "[0-9]{,2}h",
            "[0-9]{,2}m",
            "[0-9]{,2}s",
        ]

        for match in match_list:
            matched_string = re.findall(match, file_target)

            if len(matched_string) != 0:
                file_target = file_target.replace(matched_string[0], "")
                times_list.append(int(matched_string[0][:-1]))
            else:
                times_list.append(0)

        year, day, hours, minutes, seconds = times_list

        target_date = timedelta(
            days=(year * 365) + day,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=0,
            milliseconds=0,
            weeks=0,
        )

        backup_files = self.get_backup_files()
        files_date = self.filename_to_date(backup_files)

        for file_date in files_date:
            file_path, target_file_date = file_date

            if (now - target_date) > target_file_date:
                if os.path.isdir(file_path):
                    self._rmtree(file_path)
                else:
                    os.remove(file_path)

                print(green("Delete old backup:"), file_path)

    def filename_to_date(self, *files: str):
        for file in files[0]:
            file_date = file.split(".")[0].replace(
                str(self.backup_folder / self.minecraft_folder.name) + "_", ""
            )

            file_date = datetime.strptime(file_date, "%Y-%m-%d_%Hh-%Mm-%Ss")

            yield (file, file_date)

    def get_backup_files(self) -> list:
        backup_folder_files = glob.glob(str(self.backup_folder / "*"))
        verified_backup_folder_files = [
            str(backup_folder_file)
            for backup_folder_file in backup_folder_files
            if self.minecraft_folder.name in backup_folder_file
        ]

        return verified_backup_folder_files

    def _rmtree(self, top):
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                filename = os.path.join(root, name)
                os.chmod(filename, stat.S_IWUSR)
                os.remove(filename)
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(top)

    @classmethod
    def is_can_backup(
        cls, minecraft_folder: Union[str, Path], backup_folder: Union[str, Path]
    ) -> Dict[bool, str]:
        if type(minecraft_folder) == str:
            minecraft_folder = Path(minecraft_folder).resolve()
        else:
            minecraft_folder = minecraft_folder.resolve()

        if type(backup_folder) == str:
            backup_folder = Path(backup_folder).resolve()
        else:
            backup_folder = backup_folder.resolve()

        # Check to avoid the same files.
        if minecraft_folder == backup_folder:
            return {
                "result": False,
                "message": "The minecraft folder path and backup folder path shouldn't be the same.",
            }

        # Check if the file or directory exists.
        if not os.path.exists(minecraft_folder) and not os.path.exists(backup_folder):
            return {
                "result": False,
                "message": "Can't find Minecraft folder and Backup folder.",
            }
        elif not os.path.exists(minecraft_folder):
            return {"result": False, "message": "Can't find Minecraft folder."}
        elif not os.path.exists(backup_folder):
            return {"result": False, "message": "Can't find BackupFolder."}

        # Check if the directory exists by referring to PATH.
        if not os.path.isdir(minecraft_folder) and not os.path.isdir(backup_folder):
            return {
                "result": False,
                "message": "Minecraft folder and Backup folder aren't directory. Please select a directory.",
            }
        elif not os.path.isdir(minecraft_folder):
            return {
                "result": False,
                "message": "Minecraft folder isn't directory. Please select a directory.",
            }
        elif not os.path.isdir(backup_folder):
            return {
                "result": False,
                "message": "Backup folder isn't directory. Plase selct a directory.",
            }

        return {"result": True}

    def __str__(self):
        return textwrap.dedent(
            f"""\
            MinecraftFolder: {self.minecraft_folder}
            BackupFolder: {self.backup_folder}\
            """
        )

    def __repr__(self):
        return self
