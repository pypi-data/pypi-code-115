"""Module subject.

..
    The MIT License

    Copyright 2022 Thomas Lehmann.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
"""
# pylint: disable=too-few-public-methods
from typing import Any

from responsive.observer import Observer


class Subject:
    """Subject from the subject/observer pattern."""

    def __init__(self):
        """Initialize empty list of observers."""
        self.__observers: list[Observer] = []

    def notify(self, *args: Any, **kwargs: Any):
        """Updating all observers.

        Args:
            *args (Any): optional positional arguments
            **kwargs (Any): optional key/value arguments
        """
        for observer in self.__observers:
            interests = observer.get_interests()
            if len(interests) == 0:  # pylint: disable=compare-to-zero
                observer.update(self, *args, **kwargs)
            else:
                for key, value in kwargs.items():
                    if key in interests and interests[key](value):
                        observer.update(self, *args, **kwargs)
                        break

    def add_observer(self, observer: Observer) -> None:
        """Adding observer to list.

        Args:
            observer (obj): object that will be notified.
        """
        if observer not in self.__observers:
            self.__observers.append(observer)

    def remove_observer(self, observer: Observer) -> None:
        """Remove observer from list.

        Args:
            observer (obj): object that don't want to get updated anymore.
        """
        self.__observers.remove(observer)
