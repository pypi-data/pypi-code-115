import glob
import logging
import os
import shutil
import stat
from zipfile import ZipFile

logger = logging.getLogger("utils")


def get_apk_from_universal_apks(
    apks_path,
    output_dir: str = "",
):
    filename = "universal.apk"

    with ZipFile(apks_path, "r") as zip_file:
        if not output_dir:
            output_dir = os.path.dirname(os.path.realpath(apks_path))
        try:
            logger.info(f"Extracting {apks_path}")
            zip_file.extract(filename, path=output_dir)
            return os.path.join(output_dir, filename)

        except KeyError:
            logger.error("Extraction failed. Maybe not an universal apks !")

        return None


def add_execution_permission_to_binaries(
    directory="",
):
    directory = (
        directory
        if directory
        else os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "binary-files/*",
        )
    )
    for file in glob.glob(directory):
        st = os.stat(file)
        os.chmod(file, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return


def clean_output_dir(path: str):
    logger.info("Cleaning output directory")
    shutil.rmtree(path)
    logger.info("Cleaning output directory successful")
