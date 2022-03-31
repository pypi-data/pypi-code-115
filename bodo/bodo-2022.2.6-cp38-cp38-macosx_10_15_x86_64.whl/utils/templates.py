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
            ecfxv__kdaj = set()
            kmba__gcv = list(self.context._get_attribute_templates(self.key))
            ifloy__mtiuw = kmba__gcv.index(self) + 1
            for lty__wvtoi in range(ifloy__mtiuw, len(kmba__gcv)):
                if isinstance(kmba__gcv[lty__wvtoi], numba.core.typing.
                    templates._OverloadAttributeTemplate):
                    ecfxv__kdaj.add(kmba__gcv[lty__wvtoi]._attr)
            self._attr_set = ecfxv__kdaj
        return attr_name in self._attr_set
