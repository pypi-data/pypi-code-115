"""
Functions to create additional primitive graphics (e.g., bitmap image)
"""

from pytamaro import Graphic
from pytamaro_extra.graphic import BitmapImage


def bitmap(file_path: str, pixel_per_unit: int = 1) -> Graphic:
    """
    Loads a bitmap image from a file (e.g., a PNG file).

    :param file_path: path to the file, including the file name and the extension
    :param pixel_per_unit: how many pixels correspond to one unit in our domain
           (defaults to 1, which means that 1 pixel in the image will correspond
           exactly to 1 unit in the resulting graphic)
    :returns: the loaded image as a graphic
    """
    return BitmapImage(file_path, pixel_per_unit)
