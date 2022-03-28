import logging
import re
from typing import Optional, Tuple, Union
from xeda.utils import XedaBaseModeAllowExtra, validator
from xeda.design import Design

_logger = logging.getLogger(__name__)


class LwcSpec(XedaBaseModeAllowExtra):
    algorithm: Union[str, Tuple[str, ...]]
    supports_hash: bool = False
    variant: Optional[str] = None
    two_pass: bool = False
    block_bits: Optional[int] = None

class LwcDesign(Design):
    lwc: LwcSpec

    @property
    def variant(self):
        design_name = self.name
        lwc_variant = self.lwc.variant
        if not lwc_variant:
            name_splitted = design_name.split("-")
            assert (
                len(name_splitted) > 1
            ), "either specify design.lwc.variant or design.name should be ending with -v\\d+"
            lwc_variant = name_splitted[-1]
            assert re.match(
                r"v\d+", lwc_variant
            ), "either specify design.lwc.variant or design.name should be ending with -v\\d+"

        return lwc_variant

    @property
    def supports_hash(self):
        return self.lwc.supports_hash or (
            isinstance(self.lwc.algorithm, tuple) and len(self.lwc.algorithm) == 2
        )

    @classmethod
    def wrap_design(cls, design_settings):
        lwc = design_settings.get("lwc", {})
        lwc_wrapper = lwc.get("wrapper")
        if lwc_wrapper:
            two_pass = lwc.get("two_pass")
            for section in "rtl", "tb":
                for k, v in lwc_wrapper.get(section, {}).items():
                    if k == "sources":
                        _logger.info(
                            f"Extending design.{section}.{k} with sources from design.lwc.wrapper.{section}.{k}"
                        )
                        design_settings[section][k] += [
                            x for x in v if x not in design_settings[section].get(k, {})
                        ]
                    else:
                        _logger.info(
                            f"Replacing design.{section}.{k} with design.lwc.wrapper.{section}.{k}={v}"
                        )
                        design_settings[section][k] = v
