# ----------------------------------------------------------------------------------------------------------------------
# - Package Imports -
# ----------------------------------------------------------------------------------------------------------------------
# General Packages

# Custom Library

# Custom Packages
from .Rgb import rgb

# ----------------------------------------------------------------------------------------------------------------------
# - Code -
# ----------------------------------------------------------------------------------------------------------------------
class hexadecimal(rgb):
    # ------------------------------------------------------------------------------------------------------------------
    # INIT method
    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, hex_value:str):
        if isinstance(hex_value, str) and hex_value[0] == "#":
            hex_v = hex_value.removeprefix('#')
            indexes = (0, 2, 4)
            self.r,self.g, self.b = tuple(
                int(hex_v[i:i+2], 16)
                for i in indexes
            )
        else:
            raise ValueError("no correct str was given on creation")