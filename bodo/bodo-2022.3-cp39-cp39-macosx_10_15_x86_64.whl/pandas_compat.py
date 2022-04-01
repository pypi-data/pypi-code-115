import hashlib
import inspect
import warnings
import pandas as pd
_check_pandas_change = False


def _set_noconvert_columns(self):
    assert self.orig_names is not None
    qujn__ustfn = {ufdt__dxtbc: yjrp__akeq for yjrp__akeq, ufdt__dxtbc in
        enumerate(self.orig_names)}
    scwbi__ablr = [qujn__ustfn[ufdt__dxtbc] for ufdt__dxtbc in self.names]
    exmb__qgl = self._set_noconvert_dtype_columns(scwbi__ablr, self.names)
    for ecb__ilj in exmb__qgl:
        self._reader.set_noconvert(ecb__ilj)


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
