from __future__ import annotations

import re as _re
from typing import TYPE_CHECKING

from dfops._internal.utils import cmd_output

if TYPE_CHECKING:
    from dfops._internal.types import Iterator, List


class GitClient:
    __slots__ = ("_version",)

    _version_re = _re.compile(r"\Agit version (?P<version>\d+(\.\d+)*)(:? \(.+\))?\n\Z")
    _status_re = _re.compile(
        r"\A(?:\?\?|[ AM][AM]) (?P<quote>[\"']?)(?P<filename>.+)(?P=quote)\Z"
    )

    def __init__(self) -> None:
        self._version = self.__get_version()

    @property
    def version(self) -> str:
        return self._version

    def status(self, *paths: str) -> Iterator[str]:
        return_code, stdout, stderr = cmd_output(
            "git", "status", "--porcelain", "--ignore-submodules", "-zu", *paths
        )

        if return_code or stderr:
            raise ValueError

        if stdout:
            for line in self.__zsplit(stdout):
                if (match := self._status_re.fullmatch(line)) is not None:
                    yield match.group("filename")

    def diff(self, *paths: str, n: int) -> Iterator[str]:
        return_code, stdout, stderr = cmd_output(
            "git",
            "diff",
            "--name-only",
            "--ignore-submodules",
            "-z",
            f"HEAD{'' if n == 1 else '~'+str(n-1)}",
            f"HEAD~{n}",
            "--",
            *paths,
        )

        if return_code or stderr:
            raise ValueError

        if stdout:
            yield from self.__zsplit(stdout)

    def __get_version(self) -> str:
        return_code, stdout, stderr = cmd_output("git", "--version")

        if return_code or stderr:
            raise ValueError

        if not stdout or (match := self._version_re.fullmatch(stdout)) is None:
            raise ValueError

        return match.group("version")

    @staticmethod
    def __zsplit(output: str) -> Iterator[str]:
        yield from output.strip("\0").split("\0")
