# -*- coding: utf-8 -*-
import warnings

warnings.filterwarnings("ignore", message="[.\n]*Pandas[.\n]*")
warnings.simplefilter(action="ignore", category=FutureWarning)
from .client import init, reset, initialized  # noqa


__all__ = ["__version__", "init", "reset", "initialized"]


def __go():
    import importlib
    import pkgutil

    for loader, module_name, is_pkg in pkgutil.walk_packages(__path__, "dqdatasdk."):
        if module_name.startswith("dqdatasdk.services") and not is_pkg:
            importlib.import_module(module_name)


__go()

del __go

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
