
from utils.xmlx import _

from infographics.core.SVG_STYLES import SVG_STYLES

DEFAULT_WIDTH, DEFAULT_HEIGHT, PADDING = 1200, 675, 20
DEFAULT_BASE_FONT_SIZE = 16


class SVGPalettePolygon:
    def draw_multipolygon(self, multipolygon, attribs={}):
        return self.draw_g(
            list(map(
                lambda polygon: self.draw_polygon(polygon, attribs),
                multipolygon,
            )),
        )

    def draw_polygon(self, polygon, attribs={}):
        d_list = []
        for p in polygon:
            x, y = self.t(p)
            prefix = 'L' if (d_list) else 'M'
            d_list.append(f'{prefix}{x},{y}')
        d_list.append('z')
        d = ' '.join(d_list)

        return _('path', [], SVG_STYLES.PATH | {'d': d} | attribs)
