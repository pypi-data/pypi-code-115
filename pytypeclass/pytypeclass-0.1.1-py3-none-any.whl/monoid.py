from __future__ import annotations

import abc
from typing import Generic, Type, TypeVar

from pytypeclass import Monad

A = TypeVar("A")
B = TypeVar("B")
A_co = TypeVar("A_co", covariant=True)


class Monoid(Generic[A_co]):
    @abc.abstractmethod
    def __or__(self: Monoid[A], other: Monoid[B]) -> Monoid[A | B]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def zero(cls: Type[Monoid[A]]) -> Monoid[A]:
        raise NotImplementedError


class MonadPlus(Monad[A_co], Monoid[A_co]):
    pass
