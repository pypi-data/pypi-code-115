from colored import fg

from .teallevel import TealLevel


class Colors:
    error: str = fg("red")
    warning: str = fg("dark_orange")


class TealConfig:
    level: TealLevel = TealLevel.info
    indent_char = " "
    indent_by: int = 4
    colors_enabled: bool = True
    unicode_enabled: bool = True
    colors_default: Colors = Colors()

    @staticmethod
    def reset():
        TealConfig.level = TealLevel.info
        TealConfig.indent_char = " "
        TealConfig.indent_by = 4
        TealConfig.colors_enabled = True
        TealConfig.unicode_enabled = True
        TealConfig.colors_default = Colors()
