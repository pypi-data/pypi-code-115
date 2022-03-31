from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace

    from dfops._internal.cli.io import ArgumentParser
    from dfops._internal.types import Iterable

    from .inputs import Argument


class Command(ABC):
    __slots__ = "_name", "_parser"

    description: str | None = None
    arguments: Iterable[Argument] = ()

    def __init__(self, name: str, *, parser: ArgumentParser) -> None:
        self._name = name
        self._parser = parser

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def run(self, args: Namespace) -> int:
        ...
