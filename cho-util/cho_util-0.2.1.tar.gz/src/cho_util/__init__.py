try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("cho_util")
    except PackageNotFoundError:
        # package is not installed
        pass
except ModuleNotFoundError:
    # Python3.6 fallback
    from pkg_resources import get_distribution, DistributionNotFound
    try:
        __version__ = get_distribution("cho_util").version
    except DistributionNotFound:
        # package is not installed
        pass

from . import cam
from . import math
from . import viz
from . import app
