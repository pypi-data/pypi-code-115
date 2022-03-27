from typing import Union


class Color:
    red: int = 0
    green: int = 0
    blue: int = 0
    alpha: Union[int, None] = None

    @classmethod
    def from_int(cls, red: int, green: int, blue: int, alpha: int = None):
        return cls(red, green, blue, alpha)

    def __init__(self, red: int, green: int, blue: int, alpha: int = None):
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha

    def __eq__(self, other):
        return (
            self.red == other.red
            and self.green == other.green
            and self.blue == other.blue
            and self.alpha == other.alpha
        )
