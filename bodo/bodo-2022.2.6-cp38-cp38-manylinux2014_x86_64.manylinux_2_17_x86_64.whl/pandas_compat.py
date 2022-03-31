import hashlib
import inspect
import warnings
import pandas as pd
_check_pandas_change = False


def _set_noconvert_columns(self):
    assert self.orig_names is not None
    nyrp__tigs = {qcr__efp: fruk__xfn for fruk__xfn, qcr__efp in enumerate(
        self.orig_names)}
    pug__lko = [nyrp__tigs[qcr__efp] for qcr__efp in self.names]
    egyn__lncg = self._set_noconvert_dtype_columns(pug__lko, self.names)
    for dxupg__jcea in egyn__lncg:
        self._reader.set_noconvert(dxupg__jcea)


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
