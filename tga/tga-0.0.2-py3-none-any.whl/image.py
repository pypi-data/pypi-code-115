import struct
from enum import IntEnum
from typing import List, Union

from tga.color import Color


class ImageType(IntEnum):
    NO_DATA = 0
    UNCOMPRESSED_COLOR_MAPPED = 1
    UNCOMPRESSED_RGB = 2
    UNCOMPRESSED_BW = 3
    RLE_COLOR_MAPPED = 9
    RLE_RGB = 10
    COMPRESSED_BW = 11
    COMPRESSED_COLOR_MAPPED = 32
    COMPRESSED_COLOR_MAPPED_QUADTREE = 33


class ImageDepth(IntEnum):
    TARGA_16 = 16
    TARGA_24 = 24
    TARGA_32 = 32


class Image:
    """
    References / Specifications
    ===========================
    - http://paulbourke.net/dataformats/tga/
    - https://docs.fileformat.com/image/tga/
    """

    id_length: int = 0
    has_color_map: bool = False
    image_type: ImageType = ImageType.UNCOMPRESSED_RGB

    # color map specification
    color_map_origin: int = 0
    color_map_length: int = 0
    color_map_depth: Union[ImageDepth, None] = None

    # image specification
    x_origin: int = 0
    y_origin: int = 0
    width: int = 0
    height: int = 0
    depth: ImageDepth = ImageDepth.TARGA_24
    descriptor: int = 0  # unused bit packed metadata: should be set to zero

    data: List[List[Color]] = [[]]  # multidimensional ([row][column]) image data

    def __init__(
        self, width: int, height: int, color: Color = Color.from_int(255, 255, 255)
    ):
        self.width = width
        self.height = height
        self.depth = ImageDepth.TARGA_24 if color.alpha is None else ImageDepth.TARGA_32
        self.data = [
            [color for column in range(self.width)] for row in range(self.height)
        ]

    def set_pixel(self, row: int, column: int, color: Color) -> None:
        try:
            self.data[row][column] = color
        except IndexError:
            raise Exception(
                f"row={row} column={column} outside of canvas "
                f"(width={self.width} height={self.height}) "
                f"hint: set_pixel uses a zero-based coordinate system"
            )

    def header_to_bytes(self) -> bytes:
        color_map_type = 1 if self.has_color_map else 0
        color_map_depth = self.color_map_depth or 0

        return b"".join(
            (
                struct.pack("<B", self.id_length),
                struct.pack("<B", color_map_type),
                struct.pack("<B", self.image_type),
                struct.pack("<H", self.color_map_origin),
                struct.pack("<H", self.color_map_length),
                struct.pack("<B", color_map_depth),
                struct.pack("<H", self.x_origin),
                struct.pack("<H", self.y_origin),
                struct.pack("<H", self.width),
                struct.pack("<H", self.height),
                struct.pack("<B", self.depth),
                struct.pack("<B", self.descriptor),
            )
        )

    def identification_to_bytes(self) -> bytes:
        """
        Return the image identification in byte representation.

        This field is not currently supported.
        """
        return b""

    def color_map_to_bytes(self) -> bytes:
        """
        Return the image color map lookup table in byte representation.

        This field is not currently supported.
        """
        return b""

    def data_to_bytes(self) -> bytes:
        """
        Return the image data in byte representation. This field
        specifies the (width) by (height) in pixels.
        """
        length = self.width * self.height * (self.depth // 8)
        data = []

        if self.depth == ImageDepth.TARGA_32:
            for row in self.data:
                for color in row:
                    data += [color.blue, color.green, color.red, color.alpha]

        elif self.depth == ImageDepth.TARGA_24:
            for row in self.data:
                for color in row:
                    data += [color.blue, color.green, color.red]

        return struct.pack(f"<{length}B", *data)

    def to_bytes(self) -> bytes:
        return b"".join(
            (
                self.header_to_bytes(),
                self.identification_to_bytes(),
                self.color_map_to_bytes(),
                self.data_to_bytes(),
            )
        )
