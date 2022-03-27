
from infographics.view.DorlingView import DorlingView

CIRLCE_RADIUS_MAX_LABEL_VALUE = 0.2


class FlagDorlingView(DorlingView):
    def __init__(
        self,
        ids,
        get_norm_multipolygon,
        get_label,
        get_cartogram_value,
        get_flag_data,
    ):
        def get_color(id):
            return 'gray'

        DorlingView.__init__(
            self,
            ids,
            get_norm_multipolygon,
            get_color,
            get_label,
            get_cartogram_value,
            FlagDorlingView.render_dorling_object,

        )
        self.get_flag_data = get_flag_data

    @staticmethod
    def render_dorling_object(dorling_view, palette, id, cxcy, rxry):
        flag_data = dorling_view.get_flag_data(id)
        n_sinhalese = flag_data['sinhalese']
        n_tamil = flag_data['tamil']
        n_moor = flag_data['muslim']
        n_buddhist = flag_data['buddhist']

        total = n_sinhalese + n_tamil + n_moor
        p_sinhalese = n_sinhalese / total
        p_tamil = n_tamil / total
        p_moor = n_moor / total

        p_buddhist = n_buddhist / n_sinhalese

        cx, cy = cxcy
        rx, ry = rxry
        ry /= 2

        x0 = cx - rx
        y0 = cy + ry
        inner_list = []
        for [color, p] in [
            ['green', p_moor],
            ['orange', p_tamil],
            ['yellow', p_sinhalese * p_buddhist],
            ['maroon', p_sinhalese * (1 - p_buddhist)],
        ]:
            rx0 = rx * p
            inner_list.append(
                palette.draw_rect(
                    (x0, y0),
                    (rx0 * 2, ry * 2),
                    {
                        'fill': color,
                        'stroke': 'black',
                        'stroke-width': 0.1,
                        'fill-opacity': 1,
                    },
                )
            )
            x0 += rx0 * 2

        return palette.draw_g(inner_list)
