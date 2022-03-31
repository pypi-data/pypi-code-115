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
            lcbj__mbcjs = set()
            zdm__srazk = list(self.context._get_attribute_templates(self.key))
            lpyla__lcux = zdm__srazk.index(self) + 1
            for ebw__kevp in range(lpyla__lcux, len(zdm__srazk)):
                if isinstance(zdm__srazk[ebw__kevp], numba.core.typing.
                    templates._OverloadAttributeTemplate):
                    lcbj__mbcjs.add(zdm__srazk[ebw__kevp]._attr)
            self._attr_set = lcbj__mbcjs
        return attr_name in self._attr_set
