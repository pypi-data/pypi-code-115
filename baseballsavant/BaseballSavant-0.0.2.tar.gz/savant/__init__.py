"""

"""


import os
from pkg_resources import DistributionNotFound
from pkg_resources import get_distribution


try:
    _dist = get_distribution("BaseballSavant")
    dist_loc = os.path.normcase(_dist.location)
    here = os.path.normcase(__file__)
    if not here.startswith(os.path.join(dist_loc, "BaseballSavant")):
        raise DistributionNotFound
except DistributionNotFound:
    __version__ = "Please install this project with setup.py"
else:
    __version__ = _dist.version
