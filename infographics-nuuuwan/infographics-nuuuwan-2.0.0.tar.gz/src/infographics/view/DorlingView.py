import math
from functools import cache

from infographics._utils import log
from infographics.base import dorling_compress, xy
from infographics.view.PolygonView import PolygonView


class DorlingView(PolygonView):
    def __init__(
        self,
        ids,
        get_norm_multipolygon,
        get_color_cartogram,
        get_label,
        get_cartogram_value,
        render_dorling_object,
    ):
        def get_color(id):
            return 'white'

        PolygonView.__init__(
            self,
            ids,
            get_norm_multipolygon,
            get_color,
            get_label,
        )
        self.get_color_cartogram = get_color_cartogram
        self.get_cartogram_value = get_cartogram_value
        self.render_dorling_object = render_dorling_object

    @cache
    def get_id_to_cxcyrxry_index(self, palette):
        log.debug('[expensive] DorlingView.id_to_cxcyrxry')
        total_cartogram_value = 0
        for id in self.ids:
            cartogram_value = self.get_cartogram_value(id)
            total_cartogram_value += cartogram_value

        id_to_cxcyrxry = {}
        for id in self.ids:
            norm_multipolygon = self.get_norm_multipolygon(palette, id)
            cartogram_value = self.get_cartogram_value(id)
            (cx, cy), ____ = xy.get_cxcyrxry_for_multipolygon(norm_multipolygon)
            pr = 0.2 * math.sqrt(cartogram_value / total_cartogram_value)

            id_to_cxcyrxry[id] = [[cx, cy], [pr, pr]]

        xyrs = list(id_to_cxcyrxry.values())
        xyrs = dorling_compress._compress(xyrs, [-1, -1, 1, 1])
        id_to_cxcyrxry = dict(zip(id_to_cxcyrxry.keys(), xyrs))
        return id_to_cxcyrxry

    def get_cxcyrxry(self, palette, id):
        return self.get_id_to_cxcyrxry_index(palette).get(id)

    def render_dorling_objects(self, palette):
        rendered_dorling_objects = []
        for id in self.ids:
            [cx, cy], [rx, ry] = self.get_cxcyrxry(palette, id)
            rendered_dorling_objects.append(
                self.render_dorling_object(
                    self,
                    palette,
                    id,
                    (cx, cy),
                    (rx, ry),
                )
            )
        return rendered_dorling_objects

    def __xml__(self, palette):
        return palette.draw_g(
            self.render_polygons(palette) +
            self.render_dorling_objects(palette) +
            self.render_labels(palette),
        )

    @staticmethod
    def render_ellipse_object(dorling_view, palette, id, cxcy, rxry):
        return palette.draw_ellipse(
            cxcy,
            rxry,
            {'fill': dorling_view.get_color_cartogram(id)},
        )

    @staticmethod
    def render_rect_object(dorling_view, palette, id, cxcy, rxry):
        cx, cy = cxcy
        rx, ry = rxry
        left, top = cx - rx, cy + ry
        width, height = rx * 2, ry * 2
        return palette.draw_rect(
            [left, top],
            [width, height],
            {'fill': dorling_view.get_color_cartogram(id)},
        )

    @staticmethod
    def get_render_polygon_object(n):
        def render_polygon_object_with_n(
                dorling_view, palette, id, cxcy, rxry):
            return DorlingView.render_polygon_object(
                dorling_view, palette, id, cxcy, rxry, n)
        return render_polygon_object_with_n

    @staticmethod
    def render_polygon_object(dorling_view, palette, id, cxcy, rxry, n):
        cx, cy = cxcy
        rx, ry = rxry
        polygon = []
        theta0 = -math.pi / 2
        for i in range(0, n):
            theta = 2 * math.pi * i / n + theta0
            x, y = cx + rx * math.cos(theta), cy - ry * math.sin(theta)
            polygon.append([x, y])
        return palette.draw_polygon(
            polygon,
            {'fill': dorling_view.get_color_cartogram(id)},
        )
