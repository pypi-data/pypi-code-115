# -*- coding: utf-8 -*-

'''
这是dqdata包
'''

from .dqdatasdk import *
from .dqmodule.overwriteif import *
from .dqmodule.dqcertificate import *
from .dqmodule.print_redirect import *


__all__ = ["__version__", "init", "reset", "initialized"]

def __go():
    import importlib
    import pkgutil

    for loader, module_name, is_pkg in pkgutil.walk_packages(["."], "dqdatasdk."):
        if module_name.startswith("dqdatasdk.dqmodule") and not is_pkg:
            importlib.import_module(module_name)


__go()

del __go


from ._version import get_version
__version__ = get_version()
del get_version