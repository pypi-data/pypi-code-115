import os

from .models import *
from .pipeline import *
from .plots import *
from .plots_copy import *
from .target import *
from .target_copy import *
from .utils import *
from .utils_copy import *

__all__ = ['cli', 'pipeline', 'models', 'target', 'target_copy', 'plots', 'plots_copy', 'utils', 'utils_copy']

__version__ = '4.1.2'

_ROOT = os.path.abspath(os.getcwd())
INFDIR = os.path.join(_ROOT, 'info')
INPDIR = os.path.join(_ROOT, 'data')
OUTDIR = os.path.join(_ROOT, 'results')
