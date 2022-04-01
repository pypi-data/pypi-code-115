import hashlib
import inspect
import warnings
import pandas as pd
_check_pandas_change = False


def _set_noconvert_columns(self):
    assert self.orig_names is not None
    fwstb__poer = {teef__gdr: usp__unbux for usp__unbux, teef__gdr in
        enumerate(self.orig_names)}
    pvmy__shig = [fwstb__poer[teef__gdr] for teef__gdr in self.names]
    tlfe__fthuf = self._set_noconvert_dtype_columns(pvmy__shig, self.names)
    for adfy__fiqx in tlfe__fthuf:
        self._reader.set_noconvert(adfy__fiqx)


if _check_pandas_change:
    lines = inspect.getsource(pd.io.parsers.c_parser_wrapper.CParserWrapper
        ._set_noconvert_columns)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'afc2d738f194e3976cf05d61cb16dc4224b0139451f08a1cf49c578af6f975d3':
        warnings.warn(
            'pd.io.parsers.c_parser_wrapper.CParserWrapper._set_noconvert_columns has changed'
            )
pd.io.parsers.c_parser_wrapper.CParserWrapper._set_noconvert_columns = (
    _set_noconvert_columns)
