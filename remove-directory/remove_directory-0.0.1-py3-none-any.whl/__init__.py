#!/usr/bin/env python


from remove_directory import version
from datetime import date
from pathlib import Path


__author__ = "Борис Верховский"
__author_email__ = "sven.siegmund@gmail.com"
__maintainer__ = "Sven Siegmund"
__maintainer_email__ = __author_email__
__release_date__ = date(year=2022, month=3, day=30)
__version__ = version.version
__repository__ = "https://github.com/Nagidal/remove_directory"


def rmdir(directory: Path) -> None:
    """
    Recursively removes a directory.
    Borrowed from https://stackoverflow.com/a/49782093/9235421 
    """
    for item in directory.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    directory.rmdir()
