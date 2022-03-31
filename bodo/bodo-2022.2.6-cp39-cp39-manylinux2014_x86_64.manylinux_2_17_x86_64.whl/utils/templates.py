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
            dfpp__edgf = set()
            cmfte__gyza = list(self.context._get_attribute_templates(self.key))
            nzdob__mgaj = cmfte__gyza.index(self) + 1
            for dkk__fhbe in range(nzdob__mgaj, len(cmfte__gyza)):
                if isinstance(cmfte__gyza[dkk__fhbe], numba.core.typing.
                    templates._OverloadAttributeTemplate):
                    dfpp__edgf.add(cmfte__gyza[dkk__fhbe]._attr)
            self._attr_set = dfpp__edgf
        return attr_name in self._attr_set
