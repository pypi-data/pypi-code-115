import hashlib
import inspect
import warnings
import pandas as pd
_check_pandas_change = False


def _set_noconvert_columns(self):
    assert self.orig_names is not None
    hzb__fsod = {ofxp__qho: xgo__gln for xgo__gln, ofxp__qho in enumerate(
        self.orig_names)}
    ealha__ognwj = [hzb__fsod[ofxp__qho] for ofxp__qho in self.names]
    grgim__pxc = self._set_noconvert_dtype_columns(ealha__ognwj, self.names)
    for aab__uew in grgim__pxc:
        self._reader.set_noconvert(aab__uew)


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
