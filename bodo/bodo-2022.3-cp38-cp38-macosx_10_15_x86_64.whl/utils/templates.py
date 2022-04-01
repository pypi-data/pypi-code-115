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
            pnr__khwem = set()
            jtq__ddk = list(self.context._get_attribute_templates(self.key))
            azvy__kfi = jtq__ddk.index(self) + 1
            for svjzc__amu in range(azvy__kfi, len(jtq__ddk)):
                if isinstance(jtq__ddk[svjzc__amu], numba.core.typing.
                    templates._OverloadAttributeTemplate):
                    pnr__khwem.add(jtq__ddk[svjzc__amu]._attr)
            self._attr_set = pnr__khwem
        return attr_name in self._attr_set
