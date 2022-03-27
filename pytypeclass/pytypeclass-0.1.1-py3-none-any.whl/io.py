from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generator, TypeVar

from pytypeclass.monad import Monad

A = TypeVar("A")
B = TypeVar("B", covariant=True)
C = TypeVar("C")


@dataclass
class IO(Monad[A]):
    """
    >>> def returns_1_with_side_effects():
    ...     print("foo")
    ...     return 1
    ...
    >>> def returns_2_with_side_effects():
    ...     print("bar")
    ...     return 2

    >>> def io():
    ...     x = yield IO(returns_1_with_side_effects)
    ...     y = yield IO(returns_2_with_side_effects)
    ...     yield IO(lambda: print(x + y))
    ...
    >>> IO.do(io)
    foo
    bar
    3
    IO(return_)
    """

    get: Callable[[], A]

    def __call__(self) -> A:
        return self.get()

    def __eq__(self, other) -> bool:
        if isinstance(other, IO):
            return self.get() == other.get()
        return False

    def __repr__(self) -> str:
        return f"IO({self.get.__name__})"

    def bind(self, f: Callable[[A], IO[B]]) -> IO[B]:  # type: ignore[override]
        return f(self())

    @classmethod
    def do(  # type: ignore[override]
        cls,
        generator: Callable[[], Generator[IO[A], A, None]],
    ):
        it = generator()

        def f(y: A):
            try:
                z = it.send(y)
            except StopIteration:
                return IO.return_(y)

            return cls.bind(z, f)

        return f(next(it)())

    @classmethod
    def return_(cls, a: C) -> IO[C]:
        def return_() -> C:
            return a

        return IO(return_)


class I(IO[A]):
    pass
