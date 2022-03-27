from abc import ABC


class SVGPaletteSize(ABC):
    @property
    def width(self):
        return self.size[0]

    @property
    def height(self):
        return self.size[1]

    @property
    def padding(self):
        return self.size[2]

    @property
    def actual_width(self):
        return self.width - self.padding * 2

    @property
    def actual_height(self):
        return self.height - self.padding * 2

    @property
    def aspect_ratio(self):
        return self.width / self.height

    def t(self, p):
        px, py = p
        qx, qy = (px + 1) / 2, (py + 1) / 2
        x = self.padding + qx * self.actual_width
        y = self.padding + (1 - qy) * self.actual_height
        return (x, y)
