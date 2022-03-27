from functools import cache

from gig import ext_data
from utils import colorx, dt

from infographics._utils import log
from infographics.data.AbstractData import AbstractData


def valid_value(x):
    if not x:
        return 0
    return dt.parse_float(str(x))


class GIGData(AbstractData):
    def __init__(self, data_group, table_id):
        self.data_group = data_group
        self.table_id = table_id
        self.source_text = ''

    @property
    def table_name(self):
        return self.table_id.replace('_', ' ').title()

    def get_field_name(self, field_list):
        field_str = ', '.join(list(map(
            lambda s: '"' + s.replace('_', ' ').title() + '"',
            field_list,
        )))
        return f'{self.table_name} ({field_str})'

    @cache
    def get_data(self):
        log.debug('[expensive] calling ext_data._get_table_index')
        return ext_data._get_table_index(self.data_group, self.table_id)

    @cache
    def get_total_population(self, id):
        return self[id][self.get_total_field()]

    def get_get_population(self, field_list):
        def get_population(id):
            return sum([valid_value(self[id][field]) for field in field_list])
        return get_population

    def get_get_p_population(self, field_list):
        get_population = self.get_get_population(field_list)

        def get_p_population(id):
            n_total = self.get_total_population(id)
            n_fields = get_population(id)
            return n_fields / n_total
        return get_p_population

    @cache
    def get_first_row(self):
        return list(self.get_data().values())[0]

    @cache
    def get_fields(self):
        return sorted(list(filter(
            lambda k: k not in [
                'entity_id',
                'total',
                'electors',
                'polled',
                'valid',
                'rejected',
            ],
            self.get_first_row().keys(),
        )))

    @cache
    def get_total_field(self):
        return list(filter(
            lambda k: 'total' in k or 'valid' in k,
            self.get_first_row().keys(),
        ))[0]

    @cache
    def get_most_common(self, id):
        d = self.get_data().get(id)
        if not d:
            return 'none'
        max_field = None
        max_v = None
        for field in self.get_fields():
            v = d[field]
            if not v:
                v = 0
            if not max_v or v > max_v:
                max_field = field
                max_v = v
        return max_field

    @cache
    def get_color_from_color_value_index(self):
        fields = self.get_fields()
        n_fields = len(fields)
        return dict(list(map(
            lambda x: [x[1], colorx.random_hsl(
                hue=(int)(240 * x[0] / n_fields),
                lightness=0.5,
            )],
            enumerate(fields),
        )))

    def get_color_from_color_value(self, color_value):
        return self.get_color_from_color_value_index().get(color_value)

    def get_label_from_color_value(self, color_value):
        if isinstance(color_value, str):
            return color_value.replace('_', ' ').title()
        return color_value
