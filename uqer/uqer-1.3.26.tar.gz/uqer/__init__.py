# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals


import sys
from . import uqer
from .uqer import Client
from .mfclient import neutralize, standardize, winsorize, simple_long_only, long_only
from . import DataAPI

from .version import __version__
from .utils import format_print

from .DataAPI import retry_interval, max_retries


try:
    DataAPI.api_base.replace_api_files()
    for e in list(sys.modules.keys()):
        if e.startswith('DataAPI') or e.startswith('uqer.DataAPI'):
            del sys.modules[e]
    from . import DataAPI
except:
    import traceback
    format_print(traceback.format_exc(), with_date=True)
    format_print('upgrade fail.', with_date=True)