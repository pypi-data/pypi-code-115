"""
Additional Graphic classes.
"""

from pytamaro import Graphic
from skia import Canvas, Image, Path, Rect

# pylint: disable=super-init-not-called


class BitmapImage(Graphic):
    """
    A bitmap image loaded from a file.
    """
    def __init__(self, file_path: str, pixel_per_unit: int):
        self.image = Image.open(file_path)
        self.image = self.image.resize(self.image.width() // pixel_per_unit,
                                       self.image.height() // pixel_per_unit)
        self.path = Path().addRect(Rect.MakeSize(self.image.dimensions()))
        bounds = self.path.computeTightBounds()
        self.set_pin_position(bounds.width() / 2, bounds.height() / 2)

    def render(self, canvas: Canvas):
        canvas.drawImage(self.image, 0, 0)
