"""
Functions to create additional primitive graphics (e.g., bitmap image)
"""

from __future__ import annotations

from pytamaro.de import Grafik
from pytamaro_extra.primitives import bitmap as original_bitmap


def bitmap(file_path: str, pixel_per_unit: int = 1) -> Grafik:
    """
    Loads a bitmap image from a file (e.g., a PNG file).

    :param file_path: path to the file, including the file name and the extension
    :param pixel_per_unit: how many pixels correspond to one unit in our domain
           (defaults to 1, which means that 1 pixel in the image will correspond
           exactly to 1 unit in the resulting graphic)
    :returns: the loaded image as a graphic
    """
    return original_bitmap(file_path, pixel_per_unit)
