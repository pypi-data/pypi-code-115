
CIRCLE_R_LEGEND = 0.02


class LegendView:

    def __init__(
        self,
        legend_title,
        color_values,
        get_color_from_color_value,
        get_label_from_color_value,

    ):
        self.legend_title = legend_title
        self.color_values = color_values
        self.get_color_from_color_value = get_color_from_color_value
        self.get_label_from_color_value = get_label_from_color_value

    def render_row(self, palette, color_value, xy):
        color = self.get_color_from_color_value(color_value)

        x, y = xy
        return palette.draw_g([
            palette.draw_circle(
                (x + CIRCLE_R_LEGEND, y + CIRCLE_R_LEGEND / 2),
                CIRCLE_R_LEGEND,
                {'fill': color},
            ),
            palette.draw_text(
                self.get_label_from_color_value(color_value),
                (x + CIRCLE_R_LEGEND * 2.5, y),
                1,
                {'text-anchor': 'start'},
            ),
        ])

    def __xml__(self, palette):
        x0, y0 = 0.5, 0.5
        inner_list = [
            palette.draw_text(
                self.legend_title, (x0, y0), 1, {
                    'text-anchor': 'start'},)]
        for i, color_value in enumerate(self.color_values):
            y = y0 - ((i + 1.5) * 0.05)
            inner_list.append(self.render_row(palette, color_value, (x0, y)))
        return palette.draw_g(inner_list)
