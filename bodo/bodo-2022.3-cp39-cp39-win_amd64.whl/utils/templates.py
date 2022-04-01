"""
Helper functions and classes to simplify Template Generation
for Bodo classes.
"""
import numba
from numba.core.typing.templates import AttributeTemplate


class OverloadedKeyAttributeTemplate(AttributeTemplate):
    _attr_set = None

    def _is_existing_attr(self, attr_name):
        if self._attr_set is None:
            mxv__wyrjb = set()
            ucwcb__rfxq = list(self.context._get_attribute_templates(self.key))
            gje__vcwp = ucwcb__rfxq.index(self) + 1
            for kvf__ladqc in range(gje__vcwp, len(ucwcb__rfxq)):
                if isinstance(ucwcb__rfxq[kvf__ladqc], numba.core.typing.
                    templates._OverloadAttributeTemplate):
                    mxv__wyrjb.add(ucwcb__rfxq[kvf__ladqc]._attr)
            self._attr_set = mxv__wyrjb
        return attr_name in self._attr_set
