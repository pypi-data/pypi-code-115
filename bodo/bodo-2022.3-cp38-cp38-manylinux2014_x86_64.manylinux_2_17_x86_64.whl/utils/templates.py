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
            esie__ljmbi = set()
            eoml__vazo = list(self.context._get_attribute_templates(self.key))
            unio__cgb = eoml__vazo.index(self) + 1
            for kpyze__cmi in range(unio__cgb, len(eoml__vazo)):
                if isinstance(eoml__vazo[kpyze__cmi], numba.core.typing.
                    templates._OverloadAttributeTemplate):
                    esie__ljmbi.add(eoml__vazo[kpyze__cmi]._attr)
            self._attr_set = esie__ljmbi
        return attr_name in self._attr_set
