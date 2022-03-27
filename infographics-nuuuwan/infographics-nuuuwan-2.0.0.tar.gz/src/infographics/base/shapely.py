from shapely.geometry import MultiPolygon, Polygon


def get_shapely_polygon_list_from_multipolygon(multipolygon):
    return list(multipolygon)


def get_shapely_point_list_from_polygon(polygon):
    return list(polygon.exterior.coords)


def get_xy_from_shapely_point(point):
    return (point[1], point[0])


def get_shapely_polygon_list_from_shape(shape):
    if isinstance(shape, MultiPolygon):
        return get_shapely_polygon_list_from_multipolygon(shape)
    if isinstance(shape, Polygon):
        return [shape]
    raise Exception('Unknown shape: ', type(shape))


def get_multipolygon_from_shapely_polygon_list(shapely_polygon_list):
    point_list_list = list(map(
        get_shapely_point_list_from_polygon,
        shapely_polygon_list,
    ))

    multipolygon = list(map(
        lambda point_list: list(map(
            get_xy_from_shapely_point,
            point_list,
        )),
        point_list_list,
    ))

    return multipolygon
