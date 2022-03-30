'''Load plugins from qwilfish.plugins'''

# Standard lib imports
import importlib
import pkgutil

# Local imports
import qwilfish.plugins

def _namespace_iterator(package):
    return pkgutil.iter_modules(package.__path__, package.__name__ + ".")

def _import_module(name):
    return importlib.import_module(name)

def load_plugins():
    for _,name,_ in _namespace_iterator(qwilfish.plugins):
        plugin = _import_module(name)
        plugin.initialize() # Loaded module must provide this function!
