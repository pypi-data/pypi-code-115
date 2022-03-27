from infographics.base import ds, shapely


def get_geodata_index(df):
    geodata_index = {}
    for row in df.itertuples():
        d = dict(row._asdict())

        shapely_polygon_list = shapely.get_shapely_polygon_list_from_shape(
            d['geometry'])
        multipolygon = shapely.get_multipolygon_from_shapely_polygon_list(
            shapely_polygon_list,
        )

        del d['geometry']
        geodata_index[d['id']] = d | {
            'multipolygon': multipolygon,
        }

    return ds.sort_dict_by_key(geodata_index)
