from __future__ import annotations

import abc
from functools import partial
from typing import Callable, Generator, Generic, Optional, Type, TypeVar

from pytypeclass.stateless_iterator import StatelessIterator

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
A_Monad = TypeVar("A_Monad", bound="Monad")
A_cont = TypeVar("A_cont", contravariant=True)
B_Monad = TypeVar("B_Monad", bound="Monad")


class Monad(Generic[A]):
    """
    Monad laws:
    ```haskell
    return a >>= f = f a
    p >>= return = p
    p >>= (\\a -> (f a >>= g)) = (p >>= (\\a -> f a)) >>= g
    ```
    """

    def __ge__(self: Monad[B], f: Callable[[B], Monad[C]]) -> Monad[C]:
        return self.bind(f)

    @abc.abstractmethod
    def bind(self: Monad[B], f: Callable[[B], Monad[C]]) -> Monad[C]:
        ...
        """
        ```haskell
        (>>=) :: m a -> (a -> m b) -> m b
        ```
        """
        raise NotImplementedError

    @classmethod
    def do(
        cls: Type[Monad[A]],
        generator: Callable[[], Generator[Monad[A], A, None]],
    ) -> Monad[A]:
        def f(a: Optional[A], it: StatelessIterator[Monad[A], A]) -> Monad[A]:
            try:
                it2: StatelessIterator[Monad[A], A]
                if a is None:
                    ma, it2 = it.__next__()
                else:
                    ma, it2 = it.send(a)
            except StopIteration:
                if a is None:
                    raise RuntimeError("Cannot use an empty iterator with do.")
                return cls.return_(a)
            return ma.bind(partial(f, it=it2))

        return f(None, StatelessIterator(generator))

    @classmethod
    @abc.abstractmethod
    def return_(cls: Type[Monad[A]], a: A) -> Monad[A]:  # type: ignore[misc]
        # see https://github.com/python/mypy/issues/6178#issuecomment-1057111790
        """
        ```haskell
        return :: a -> m a
        ```
        """
        raise NotImplementedError
