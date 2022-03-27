BAR_PADDING = 0.005
P_BAR_CHART_SIZE = 0.7


class BarGraphBasic:
    def __init__(self, data):
        self.data = data

    def __xml__(self, palette):
        nx = len(self.data)
        sx = (2 * P_BAR_CHART_SIZE) / nx
        max_total_y = None
        for d in self.data:
            total_y = sum(list(map(
                lambda dy: dy[0],
                d[1],
            )))
            if not max_total_y or max_total_y < total_y:
                max_total_y = total_y
        sy = (2 * P_BAR_CHART_SIZE) / max_total_y

        rendered_bars = []
        rendered_x_labels = []
        rendered_bar_labels = []
        for ix, d in enumerate(self.data):
            cx = sx * (ix + 0.5) - P_BAR_CHART_SIZE
            cy = -P_BAR_CHART_SIZE

            rendered_x_labels.append(palette.draw_text(
                str(d[0]),
                (cx, cy - 0.05),
                1,
                {'text-anchor': 'middle'},
            ))

            total_y = 0
            for iy, dy in enumerate(d[1]):

                val_y = dy[0]
                color = ['red', 'orange'][iy]
                for iyi in range(0, val_y):
                    (width, height) = (sx, sy * 1)
                    rendered_bars.append(palette.draw_rect(
                        (
                            cx - width / 2 + BAR_PADDING,
                            height + cy + BAR_PADDING,
                        ),
                        (width - BAR_PADDING * 2, height - BAR_PADDING * 2),
                        {'fill': color, 'opacity': 0.5},
                    ))
                    cy += sy * 1

                rendered_x_labels.append(palette.draw_text(
                    str(dy[0]),
                    (cx - 0.005, cy),
                    2,
                    {'text-anchor': 'end', 'font-weight': 800},
                ))
                rendered_x_labels.append(palette.draw_text(
                    str(dy[1]),
                    (cx + 0.005, cy + 0.01),
                    0.6,
                    {'text-anchor': 'start', 'font-weight': 800},
                ))

        return palette.draw_g(
            rendered_bars +
            rendered_x_labels +
            rendered_bar_labels)
