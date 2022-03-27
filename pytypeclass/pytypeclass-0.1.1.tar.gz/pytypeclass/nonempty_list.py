from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Iterator, TypeVar

from pytypeclass.monad import Monad

A = TypeVar("A", covariant=True)
B = TypeVar("B", contravariant=True)


@dataclass
class NonemptyList(Monad[A]):
    head: A
    tail: NonemptyList[A] | None = None

    def __add__(self, other: NonemptyList[B]) -> NonemptyList[A | B]:
        if self.tail is None:
            return replace(self, tail=other)
        if other.tail is None:
            return replace(self, tail=self.tail + NonemptyList(other.head))
        return replace(self, tail=(self.tail + NonemptyList(other.head) + other.tail))

    def __iter__(self) -> Iterator[A]:
        yield self.head
        if self.tail:
            yield from self.tail

    def __repr__(self):
        return repr(list(self))

    def bind(self, f: Callable[[A], NonemptyList[B]]) -> NonemptyList[B]:  # type: ignore[override]
        def g() -> Iterator[B]:
            for x in self:
                yield from f(x)

        return NonemptyList.make(*g())

    @staticmethod
    def make(x: B, *xs: B) -> NonemptyList[B]:
        if not xs:
            return NonemptyList(x)

        return NonemptyList(x, NonemptyList.make(*xs))

    @classmethod
    def return_(cls, a: B) -> NonemptyList[B]:
        return NonemptyList(a)
