from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeVar

from pytypeclass.monad import Monad

A = TypeVar("A", covariant=True)
B = TypeVar("B", contravariant=True)
Monad1 = TypeVar("Monad1", bound="Monad")


@dataclass
class Result(Monad[A]):
    """
    >>> def results():
    ...     x = yield Result(1)
    ...     y = yield Result(2)
    ...     yield Result(x + y)
    ...
    >>> Result.do(results)
    Result(3)
    >>> def results():
    ...     x = yield Result(1)
    ...     y = yield Result(RuntimeError("Oh no!"))
    ...     yield Result(x + y)
    ...
    >>> Result.do(results)
    Result(RuntimeError('Oh no!'))
    """

    get: A | Exception

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.get)})"

    def bind(  # type: ignore[override]
        self,
        f: Callable[[A], Result[B]],
    ) -> Result[B]:
        if isinstance(self.get, Exception):
            return Result(self.get)
        y = f(self.get)
        if not isinstance(y, Result):
            raise TypeError("Result.bind: f must return a Result")
        return y

    @classmethod
    def return_(cls, a: B) -> Result[B]:
        return Result(a)


class R(Result):
    pass
