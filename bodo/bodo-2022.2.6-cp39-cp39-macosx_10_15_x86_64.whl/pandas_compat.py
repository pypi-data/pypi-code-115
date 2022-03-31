import hashlib
import inspect
import warnings
import pandas as pd
_check_pandas_change = False


def _set_noconvert_columns(self):
    assert self.orig_names is not None
    xol__mqtl = {ytkb__nnr: ynzsz__sqf for ynzsz__sqf, ytkb__nnr in
        enumerate(self.orig_names)}
    cwofy__dawe = [xol__mqtl[ytkb__nnr] for ytkb__nnr in self.names]
    scq__ewsk = self._set_noconvert_dtype_columns(cwofy__dawe, self.names)
    for zbonc__eyuvw in scq__ewsk:
        self._reader.set_noconvert(zbonc__eyuvw)


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
