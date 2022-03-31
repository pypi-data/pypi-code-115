from __future__ import annotations

from gettext import gettext as _
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Action, ArgumentParser
    from typing import Any, TypeVar

    from dfops._internal.types import Callable

    _T = TypeVar("_T")


class Argument:
    __slots__ = "_args", "_kwargs", "_action"

    def __init__(
        self,
        *args: str,
        description: str | None = None,
        validator: Callable[[str], _T] | None = None,
        **kwargs: Any,
    ) -> None:
        self._args = args

        if description is not None:
            kwargs["help"] = _(description)

        if validator is not None:
            kwargs["type"] = validator

        self._kwargs = kwargs
        self._action: Action | None = None

    @property
    def action(self) -> Action | None:
        return self._action

    def add_to_parser(self, parser: ArgumentParser) -> None:
        action = parser.add_argument(*self._args, **self._kwargs)
        self._action = action
