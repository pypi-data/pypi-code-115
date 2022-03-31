from __future__ import annotations

from gettext import gettext as _
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def import_string(*modpath: str) -> Any:
    dotted_path = ".".join(modpath)

    try:
        module_path, class_name = dotted_path.strip().rsplit(".", 1)
    except ValueError as err:
        raise ImportError(
            _("%r: doesn't look like a module path") % dotted_path
        ) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError(
            _("module %r doesn't define a %r attribute") % (module_path, class_name)
        ) from err
