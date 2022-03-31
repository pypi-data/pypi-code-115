from __future__ import annotations

import functools
import shlex
from collections import OrderedDict
from types import GeneratorType
from typing import TYPE_CHECKING

from identify.identify import ALL_TAGS, FILE, tags_from_path

if TYPE_CHECKING:
    from typing import Any, Literal, TypeVar, Union

    from dfops._internal.types import (
        Dict,
        FrozenSet,
        Iterator,
        List,
        OrderedDict as OrderedDictType,
        Set,
        Tuple,
    )

    _T_co = TypeVar("_T_co", covariant=True)

    SequenceLike = Union[List[_T_co], Tuple[_T_co, ...], Iterator[_T_co]]
    SetLike = Union[Set[_T_co], FrozenSet[_T_co]]

    SequenceOrSet = Union[SequenceLike[_T_co], SetLike[_T_co]]

    _TypeInput = Union[
        str, List[str], Tuple[str, ...], Iterator[str], Set[str], FrozenSet[str]
    ]


class Types:
    __slots__ = "_and", "_or", "_exclude"

    def __init__(
        self,
        types: _TypeInput | Dict[Literal["and", "or", "exclude"], _TypeInput] = FILE,
    ) -> None:
        types_and: Set[str] = set()
        types_or: Set[str] = set()
        exclude_types: Set[str] = set()

        if isinstance(types, (str, list, tuple, GeneratorType, set, frozenset)):
            self.__update_key(types_and, types)
        else:
            if not isinstance(types, dict):
                raise TypeError

            if set(types.keys()) > {"and", "or", "exclude"}:
                raise ValueError

            if "and" in types:
                self.__update_key(types_and, types["and"])
            if "or" in types:
                self.__update_key(types_or, types["or"])
            if "exclude" in types:
                self.__update_key(exclude_types, types["exclude"])

        self._and = frozenset(types_and)
        self._or = frozenset(types_or)
        self._exclude = frozenset(exclude_types)

    @property
    def and_(self) -> FrozenSet[str]:
        return self._and

    @property
    def or_(self) -> FrozenSet[str]:
        return self._or

    @property
    def exclude(self) -> FrozenSet[str]:
        return self._exclude

    @staticmethod
    def __update_key(key: Set[str], types: _TypeInput = FILE) -> None:
        types_list: List[str] = []

        if isinstance(types, (list, tuple, GeneratorType, set, frozenset)):
            for typ in types:
                if not isinstance(typ, str):
                    raise TypeError

                types_list.append(typ)
        elif isinstance(types, str):
            types_list.append(types)
        else:
            raise TypeError

        for tag in types_list:
            if tag not in ALL_TAGS:
                raise ValueError

            key.add(tag)


@functools.lru_cache(maxsize=None)
def _types_for_file(filename: str) -> Set[str]:
    return tags_from_path(filename)


class CommandConfig:  # pylint: disable=too-many-instance-attributes
    __slots__ = (
        "_id",
        "_entry",
        "_aliases",
        "_name",
        "_targets",
        "_types",
        "_always_run",
        "_exit_on_error",
    )

    def __init__(
        self,
        *,
        id: str,  # pylint: disable=redefined-builtin
        entry: str | SequenceLike[str],
        name: str | None = None,
        alias: str | None = None,
        aliases: SequenceOrSet[str] | None = None,
        targets: SequenceOrSet[str] | None = None,
        types: _TypeInput | Dict[Literal["and", "or", "exclude"], _TypeInput] = FILE,
        always_run: bool = False,
        exit_on_error: bool = False,
    ) -> None:
        # pylint: disable=too-many-branches
        if not isinstance(id, str):
            raise TypeError

        entry_tokens: List[str] = []

        if isinstance(entry, (list, tuple, GeneratorType)):
            for token in entry:
                if not isinstance(token, str):
                    raise TypeError

                entry_tokens.append(token)
        elif isinstance(entry, str):
            entry_tokens.extend(shlex.split(entry))
        else:
            raise TypeError

        if name is not None and not isinstance(name, str):
            raise TypeError

        if alias is not None and aliases is not None:
            raise ValueError

        aliases_set = set()

        if alias is not None:
            if not isinstance(alias, str):
                raise TypeError

            aliases_set.add(alias)

        if aliases is not None:
            if not isinstance(aliases, (list, tuple, set, frozenset, GeneratorType)):
                raise TypeError

            for token in aliases:
                if not isinstance(token, str):
                    raise TypeError

                aliases_set.add(token)

        targets_set: Set[str] = set()

        if targets is not None:
            if not isinstance(targets, (list, tuple, set, frozenset, GeneratorType)):
                raise TypeError

            for token in targets:
                if not isinstance(token, str):
                    raise TypeError

                targets_set.add(token)

        if not isinstance(always_run, bool):
            raise TypeError

        if not isinstance(exit_on_error, bool):
            raise TypeError

        self._id = id
        self._name = name
        self._entry = tuple(entry_tokens)
        self._aliases = frozenset(aliases_set)
        self._targets = frozenset(targets_set)
        self._types = Types(types)
        self._always_run = always_run
        self._exit_on_error = exit_on_error

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name or self.id

    @property
    def entry(self) -> Tuple[str, ...]:
        return self._entry

    @property
    def aliases(self) -> FrozenSet[str]:
        return self._aliases

    @property
    def targets(self) -> FrozenSet[str]:
        return self._targets

    @property
    def types(self) -> Types:
        return self._types

    @property
    def always_run(self) -> bool:
        return self._always_run

    @property
    def exit_on_error(self) -> bool:
        return self._exit_on_error

    def file_has_types(self, filename: str) -> bool:
        tags = _types_for_file(filename)
        return bool(
            tags >= self.types.and_
            and (not self.types.or_ or tags & self.types.or_)
            and not tags & self.types.exclude
        )


class Config:  # pylint: disable=too-few-public-methods
    __slots__ = "_commands", "_aliases"

    def __init__(
        self,
        *,
        # defaults: Dict[Literal["types"], Any] | None = None,
        config: SequenceLike[Dict[str, Any]],
    ) -> None:
        if not isinstance(config, (tuple, list, set, frozenset, GeneratorType)):
            raise TypeError

        self._commands: OrderedDictType[str, CommandConfig] = OrderedDict()
        self._aliases: Dict[str, str] = {}

        for cmd_config_raw in config:
            command_config = CommandConfig(**cmd_config_raw)
            if command_config.id in self._commands:
                raise ValueError

            self._commands[command_config.id] = command_config

            for alias in command_config.aliases:
                if alias in self._aliases:
                    raise ValueError

                self._aliases[alias] = command_config.id

    def filter(self, *commands: str) -> Iterator[CommandConfig]:
        if commands:
            for name in commands:
                try:
                    yield self._commands[name]
                except KeyError:
                    yield self._commands[self._aliases[name]]
        else:
            yield from self._commands.values()
