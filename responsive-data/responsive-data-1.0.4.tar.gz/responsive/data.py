"""Module data.

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
from responsive.subject import Subject
from responsive.wrapper import DictWrapper, ListWrapper


def __make_responsive_for_list(root: object, parent: list) -> None:
    """Modify recursive object to be responsive.

    Args:
        root (object): the main object that should be responsive
        parent (object): the current parent in the hierachy
    """
    for index, value in enumerate(parent):
        current_type = type(value)
        if not current_type.__module__ == "builtins" or isinstance(value, dict):
            wrapped_value = DictWrapper(value, make_responsive, root=root)
            __make_responsive_for_dict(root, value)
            wrapped_value.add_observer(root)
            parent[index] = wrapped_value
        elif isinstance(value, list):
            wrapped_value = ListWrapper(value, make_responsive, root=root)
            __make_responsive_for_list(root, value)
            wrapped_value.add_observer(root)
            parent[index] = wrapped_value


def __make_responsive_for_dict(root: object, parent: object) -> None:
    """Modify recursive object to be responsive.

    Args:
        root (object): the main object that should be responsive
        parent (object): the current parent in the hierachy
    """
    the_dict = parent if isinstance(parent, dict) else parent.__dict__

    for key, value in the_dict.items():
        current_type = type(value)
        if not current_type.__module__ == "builtins" or isinstance(value, dict):
            wrapped_value = DictWrapper(value, make_responsive, root=root)
            __make_responsive_for_dict(root, value)
            wrapped_value.add_observer(root)
            the_dict[key] = wrapped_value
        elif isinstance(value, list):
            wrapped_value = ListWrapper(value, make_responsive, root=root)
            __make_responsive_for_list(root, value)
            wrapped_value.add_observer(root)
            the_dict[key] = wrapped_value


def __is_class(obj):
    """Checking an object to be a user defined class."""
    current_type = type(obj)
    return str(current_type).startswith("<class") and not current_type.__module__ == "builtins"


def make_responsive(obj: object, root: Subject = None) -> object:
    """Modify object to be responsive.

    Args:
        obj (object): the object to modify
        root (Subject): another root

    Returns:
        Modified object.
    """
    if isinstance(obj, list):
        wrapped_list = ListWrapper(obj, make_responsive, root=root)
        __make_responsive_for_list(root if root is not None else wrapped_list, obj)
        if root is not None:
            wrapped_list.add_observer(root)
        return wrapped_list

    if isinstance(obj, dict) or __is_class(obj):
        wrapped_dict_or_class = DictWrapper(obj, make_responsive, root=root)
        __make_responsive_for_dict(root if root is not None else wrapped_dict_or_class, obj)
        if root is not None:
            wrapped_dict_or_class.add_observer(root)
        return wrapped_dict_or_class

    return obj
