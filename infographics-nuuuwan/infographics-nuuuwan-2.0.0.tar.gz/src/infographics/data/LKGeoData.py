from functools import cache

from geo import geodata

from infographics._utils import log
from infographics.base import pandax, xy
from infographics.data.AbstractData import AbstractData

log.debug('[?expensive] from geo import geodata...')


class LKGeoData(AbstractData):
    def __init__(
        self,
        region_id,
        subregion_type,
    ):
        self.region_id = region_id
        self.subregion_type = subregion_type
        self.source_text = 'Data Source: statistics.gov.lk'

    @cache
    def get_data(self):
        log.debug('[expensive] geodata.get_region_geodata...')
        df = geodata.get_region_geodata(
            self.region_id,
            self.subregion_type,
        )
        geodata_index = pandax.get_geodata_index(df)
        return geodata_index

    @cache
    def get_norm_transformer(self, palette):
        data = self.get_data()
        multi2polygon = list(map(lambda d: d['multipolygon'], data.values()))
        return xy.get_norm_transformer(
            multi2polygon,
            aspect_ratio=palette.aspect_ratio,
        )

    @cache
    def get_norm_multipolygon(self, palette, id):
        return xy.get_norm_multipolygon(
            self.get_norm_transformer(palette),
            self[id]['multipolygon'],
        )

    def get_name(self, id):
        return self[id]['name']

    def get_population(self, id):
        return self[id]['population']

    def get_population_density(self, id):
        return self[id]['population'] / self[id]['area']
