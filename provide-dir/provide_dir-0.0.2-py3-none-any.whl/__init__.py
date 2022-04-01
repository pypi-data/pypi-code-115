#!/usr/bin/env python


from remove_directory import version
from datetime import date
from pathlib import Path


__author__ = "Sven Siegmund"
__author_email__ = "sven.siegmund@gmail.com"
__maintainer__ = __author__
__maintainer_email__ = __author_email__
__release_date__ = date(year=2022, month=3, day=31)
__version__ = version.version
__repository__ = "https://github.com/Nagidal/provide_dir"


def provide_dir(directory: Path) -> bool:
    """
    Checks if `directory` already exists.
    If not, it will try to create one.
    Returns True if at least one directory had to be created
    Raises FileExistsError if the path or a subpath of it
        already exists as a file.
    """
    created_something = False
    if directory.exists() and directory.is_dir():
        pass
    else:
        while True:
            try:
                directory.mkdir()
                created_something = True
                break
            except FileNotFoundError:
                _ = provide_dir(directory.parent)
                continue
            except FileExistsError:
                raise
    return created_something
