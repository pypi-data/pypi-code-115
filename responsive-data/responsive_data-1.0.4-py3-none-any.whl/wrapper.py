"""Module wrapper.

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
from typing import Any

from responsive.constants import Context, Operation
from responsive.observer import Observer
from responsive.subject import Subject


class DictWrapper(Subject, Observer):
    """Wrapper for a dictionary object."""

    def __init__(self, obj: object, make_responsive: callable, root: Subject = None):
        """Initialize wrapper.

        Args:
            obj (objec): object to wrap.
            make_responsive (callable): function to make responsive
            root (Subject): root object receiving notifications
        """
        super().__init__()
        self.make_responsive = make_responsive
        self.root = root
        self.obj = obj

    def __repr__(self) -> str:
        """Get string representation of wrapped data.

        Returns:
            string representation of wrapped data.
        """
        return f"{self.obj}"

    def __setattr__(self, name: str, value: Any) -> None:
        """Creating attribute 'obj' or changing one of its attributes.

        Args:
            name  (str): name of the attribute.
            value (Any): value of the attribute.
        """
        if "obj" in self.__dict__:
            if isinstance(self.obj, dict):
                old_value = self.obj[name]
                self.obj[name] = self.make_responsive(
                    value, root=self.root if self.root is not None else self
                )
                self.notify(
                    id=id(self),
                    context=Context.DICTIONARY,
                    name=name,
                    old=old_value,
                    new=value,
                    operation=Operation.VALUE_CHANGED,
                )
            else:
                old_value = self.obj.__dict__[name]
                self.obj.__dict__[name] = self.make_responsive(
                    value, root=self.root if self.root is not None else self
                )
                self.notify(
                    id=id(self),
                    context=Context.CLASS,
                    name=name,
                    old=old_value,
                    new=value,
                    operation=Operation.VALUE_CHANGED,
                )
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name: str) -> Any:
        """Get value of attribute.

        Args:
            name (str): name of the attribute

        Returns:
            value of the attribute.
        """
        if isinstance(self.obj, dict):
            return self.obj[name]

        return self.obj.__dict__[name]

    def __len__(self):
        """Get length of dictionary."""
        return len(self.obj)

    def update(self, subject: object, *args: Any, **kwargs: Any):
        """Called when related subject has changed.

        Args:
            subject (object): the one who does the notification.
            *args (Any): optional positional arguments
            **kwargs (Any): optional key/value arguments
        """
        self.notify(*args, **kwargs)

    def __eq__(self, other: object) -> bool:
        """Comparing two lists.

        Args:
            other (object): another object to compare with

        Returns:
            true when equal, otherwise false.
        """
        if isinstance(other, dict):
            return self.obj.__eq__(other)

        if isinstance(other, DictWrapper):
            return self.obj.__eq__(other.obj)

        return False

    def __hash__(self):
        """Calculating hash of underlying object."""
        return hash(tuple(sorted(self.obj.items())))


class ListWrapper(Subject, Observer):
    """Wrapper for a dictionary object."""

    def __init__(self, obj: object, make_responsive: callable, root: Subject = None):
        """Initialize wrapper.

        Args:
            obj (objec): object to wrap.
            make_responsive (callable): function to make responsive
            root (Subject): root object receiving notifications
        """
        super().__init__()
        self.make_responsive = make_responsive
        self.root = root
        self.obj = obj

    def __repr__(self) -> str:
        """Get string representation of wrapped data.

        Returns:
            string representation of wrapped data.
        """
        return f"{self.obj}"

    def append(self, value):
        """Appending a value to the list."""
        self.obj.append(value)
        self.notify(id=id(self), context=Context.LIST, new=value, operation=Operation.VALUE_ADDED)

    def remove(self, value):
        """Removing a value to the list."""
        self.obj.remove(value)
        self.notify(id=id(self), context=Context.LIST, old=value, operation=Operation.VALUE_REMOVED)

    def __setitem__(self, index, value):
        """Change value at given index."""
        old_value = self.obj[index]
        self.obj[index] = self.make_responsive(
            value, root=self.root if self.root is not None else self
        )
        self.notify(
            id=id(self),
            context=Context.LIST,
            index=index,
            old=old_value,
            new=value,
            operation=Operation.VALUE_CHANGED,
        )

    def __getitem__(self, index):
        """Get value at given index."""
        return self.obj[index]

    def __len__(self):
        """Get length of list."""
        return len(self.obj)

    def update(self, subject: object, *args: Any, **kwargs: Any):
        """Called when related subject has changed.

        Args:
            subject (object): the one who does the notification.
            *args (Any): optional positional arguments
            **kwargs (Any): optional key/value arguments
        """
        self.notify(*args, **kwargs)

    def __eq__(self, other: object) -> bool:
        """Comparing two lists.

        Args:
            other (object): another object to compare with

        Returns:
            true when equal, otherwise false.
        """
        if isinstance(other, list):
            return self.obj.__eq__(other)

        if isinstance(other, ListWrapper):
            return self.obj.__eq__(other.obj)

        return False

    def __hash__(self):
        """Calculating hash of underlying object."""
        return hash(self.obj)
