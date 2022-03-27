from functools import cache, cached_property

from infographics.base import humanize

DEFAULT_LEGEND_SIZE = 7


class ColorBase:
    def __init__(
        self,
        ids,
        get_color_value,
        get_color_from_color_value,
    ):
        self.ids = ids
        self.get_color_value = get_color_value
        self.get_color_from_color_value = get_color_from_color_value

    @cached_property
    def color_values(self):
        return list(map(
            lambda id: self.get_color_value(id),
            self.ids,
        ))

    @cached_property
    def sorted_color_values(self):
        return sorted(self.color_values)

    @cached_property
    def unique_color_values(self):
        return list(set(self.color_values))

    @cache
    def get_color_values(self, legend_size=DEFAULT_LEGEND_SIZE):
        sorted_color_values = self.sorted_color_values
        n = len(sorted_color_values)
        legend_color_values = []
        for i in range(0, legend_size):
            j = (int)(i * (n - 1) / (legend_size - 1))
            legend_color_values.append(sorted_color_values[j])
        return legend_color_values

    def get_color(self, id):
        color_value = self.get_color_value(id)
        return self.get_color_from_color_value(color_value)

    def get_int_label_from_color_value(self, color_value):
        return humanize.number(color_value)

    def get_percent_label_from_color_value(self, color_value):
        return humanize.percent(color_value)
