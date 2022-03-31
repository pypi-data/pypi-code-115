"""This module was created to help improve the quality of application logs.

It's only uses building libraries, therefore, it has no external dependency.
It is also lightweight and thread-safe, which makes it ideal for use in services and microservices.

However, the module has some limitations.
The most important thing to note in this scenario is that it only works with the CPython implementation.

Typical usage example:

---------------------------------------

# Caller's Stack Frame Depth 1

stack_frame_analyzer = StackFrameAnalyzer("my_service_name")

def foo(bar):
    try:
        ...
    except Exception as error:
        context = stack_frame_analyzer.get_frame_context()
        logging.error(context)

---------------------------------------

# Caller's Stack Frame Depth 2

stack_frame_analyzer = StackFrameAnalyzer("my_service_name")

class MyException(Exception):
    def __init__(self):
        self.context = stack_frame_analyzer.get_frame_context(stack_frame_depth=2)
        super().__init__()


def foo(bar):
    try:
        ...
    except MyException as error:
        logging.error(error.context)

---------------------------------------

# Caller's Stack Frame Depth 3


class ExceptionWithContext(Exception):
    def __init__(self, message: str):
        self.message = message
        self.context = stack_frame_analyzer.get_frame_context(stack_frame_depth=3)
        super().__init__(self.message)


class FooException(ExceptionWithContext):
    '''Foo Exception'''

    def __init__(self, message: str = "message"):
        self.message = message
        super().__init__(self.message)


def foo(bar):
    try:
        raise FooException
    except FooException as error:
        print(error.context)

---------------------------------------

"""

import inspect
import os
import sys
from types import FrameType
from typing import Tuple

from .exceptions import (
    FrameDepthOutOfRange,
    InvalidFrameDepth,
    StackFrameAnalyzerException,
)


class StackFrameAnalyzer:
    """Help to get the context of a frame on the caller's stack, using only the builtin modules.
    This is a thread-safe implementation.
    The main method to use is get_frame_context that return the context of selected frame of the caller's stack.


    The main builtin functions used are:
        sys._getframe: Used to get the frame of the caller's stack.
        inspect.getmodule: Used to get the module of the frame.
        inspect.getargvalues: Used to get the args in the frame.


    Limitations:
        Compatible only with CPython implementation.
        Not compatible with pyinstaller.
        It is not possible to reach the decorated function inside the decorator.
        For static class methods it's not possible to get the class name.


    Args:
        project_name (str): Name of your project. Defaults is directory of your '__main__' module.
        instance_representation_name (str): The representation name of the instance in methods. Defaults is 'self'.
        class_representation_name (str): The representation name of the class in classmethods. Defaults is 'cls'.
        context_structure = 'project_name:package_name:module_name:class_name:callable_name(callable_arguments)'


    """

    __slots__ = (
        "project_name",
        "instance_representation_name",
        "class_representation_name",
        "context_structure",
    )

    PROJECT_NAME: str = os.path.split(os.path.abspath(os.curdir))[-1]

    def __init__(
        self,
        project_name: str = None,
        instance_representation_name: str = "self",
        class_representation_name: str = "cls",
    ) -> "StackFrameAnalyzer":
        self.project_name = project_name or self.PROJECT_NAME
        self.instance_representation_name = instance_representation_name
        self.class_representation_name = class_representation_name
        self.context_structure = "{project_name}:{package}:{module}:{class_name}:{callable_name}({arguments})"

    def _get_package_and_module(self, frame: FrameType) -> Tuple[str, str]:
        module_obj = inspect.getmodule(frame)

        if not module_obj:
            return "", ""

        if module_obj.__name__ == "__main__":
            module = module_obj.__file__.split(".")[0]
            return "", module

        package, module = module_obj.__name__.rsplit(".", 1)
        del module_obj
        return package, module

    def _get_class_name(self, frame: FrameType) -> str:
        instance_representation = frame.f_locals.get(self.instance_representation_name)

        class_representation = frame.f_locals.get(self.class_representation_name)

        if instance_representation and not class_representation:
            class_name = instance_representation.__class__.__name__
        elif class_representation and not instance_representation:
            class_name = class_representation.__name__
        else:
            class_name = ""

        return class_name

    def _get_callable_name(self, frame: FrameType) -> str:
        callable_name = frame.f_code.co_name

        if callable_name == "<module>":
            return ""

        return callable_name

    def _stringfy_armguments(self, arguments: dict) -> str:
        buffer = []
        for key, value in arguments.items():
            buffer.append(f"{key}={value}")

        return ", ".join(buffer)

    def _get_callable_arguments(self, frame: FrameType) -> str:
        args_info = inspect.getargvalues(frame)
        arguments = {}
        for arg in args_info.args:
            if arg == self.instance_representation_name:
                arguments[self.instance_representation_name] = "<instance>"
            elif arg == self.class_representation_name:
                pass
            else:
                arguments[arg] = args_info.locals[arg]

        arguments_string = self._stringfy_armguments(arguments)

        del args_info
        return arguments_string

    def _build_context(
        self,
        package: str,
        module: str,
        class_name: str,
        callable_name: str,
        arguments: str,
    ) -> str:
        context = self.context_structure.format(
            project_name=self.project_name,
            package=package,
            module=module,
            class_name=class_name,
            callable_name=callable_name,
            arguments=arguments,
        )
        return context

    def get_frame_context(self, stack_frame_depth: int = 1) -> str:
        f"""Get the context of select frame.
        The structure of the context is:
          {self.context_structure}.

        Even though the frame only exists as a local variable,
        the reference cycles created when the frame object is referenceated
        is explicitly broken on the finally clause to avoid the delayed destruction of objects
        which can cause increased of memory consumption.

        Args:
            stack_frame_depth (int): Frame index below the top of the caller's stack. Defaults to 1.

        Raises:
            InvalidFrameDepth: Invalid stack_frame_depth input value.
            FrameDepthOutOfRange: Caller's stack is not deep enough.
            StackFrameAnalyzerException: Internal error.

        Returns:
            str: A string with the context of the selected frame.
        """

        if not isinstance(stack_frame_depth, int) or stack_frame_depth < 0:
            raise InvalidFrameDepth

        try:
            frame = sys._getframe(stack_frame_depth)
        except ValueError as error:
            raise FrameDepthOutOfRange from error

        try:
            package, module = self._get_package_and_module(frame)
            class_name = self._get_class_name(frame)
            callable_name = self._get_callable_name(frame)
            arguments = self._get_callable_arguments(frame)

            context = self._build_context(
                package, module, class_name, callable_name, arguments
            )

            return context

        except Exception as error:
            raise StackFrameAnalyzerException from error
            return ""

        finally:
            del frame
