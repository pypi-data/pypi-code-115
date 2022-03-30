""" Nothing to see here """
import sys

__version__ = "0.1.0"

__uri__ = 'https://github.com/garbled1/ecowitt'
__title__ = "Ecowitt"
__description__ = 'Interface Library for Ecowitt Protocol'
__doc__ = __description__ + " <" + __uri__ + ">"
__author__ = 'Ecowitt'
__email__ = 'admin@ecowitt.net'
__license__ = "Apache 2.0"

__copyright__ = "Copyright (c) 2022,2022 Ecowitt"

from .ecowitt import (
    EcoWittSensor,
    EcoWittListener,
    WINDCHILL_OLD,
    WINDCHILL_NEW,
    WINDCHILL_HYBRID,
)

if __name__ == '__main__': print(__version__)
