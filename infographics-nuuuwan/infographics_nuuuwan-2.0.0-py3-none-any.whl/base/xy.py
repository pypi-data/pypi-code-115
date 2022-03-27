from utils import ds


def get_bounds(polygon):
    min_x, min_y = 180, 180
    max_x, max_y = -180, -180
    for x, y in polygon:
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)
    return ((min_x, min_y), (max_x, max_y))


def get_midxy(polygon):
    ((min_x, min_y), (max_x, max_y)) = get_bounds(polygon)
    return ((min_x + max_x) / 2, (min_y + max_y) / 2)


def get_spans(polygon):
    ((min_x, min_y), (max_x, max_y)) = get_bounds(polygon)
    return (max_x - min_x), (max_y - min_y)


def get_cxcyrxry(polygon):
    cx, cy = get_midxy(polygon)
    x_span, y_span = get_spans(polygon)
    rx, ry = x_span / 2, y_span / 2
    return (cx, cy), (rx, ry)


def get_cxcyrxry_for_multipolygon(multipolygon):
    return get_cxcyrxry(ds.flatten(multipolygon))


def get_norm_transformer(
    multi2polygon,
    aspect_ratio=16 / 9,
    padding_p=0.75,
):
    polygon = ds.flatten(ds.flatten(multi2polygon))
    ((min_x, min_y), ___) = get_bounds(polygon)
    x_span, y_span = get_spans(polygon)

    r = x_span / y_span * aspect_ratio
    padding_x = 0
    padding_y = 0
    if r > 1:
        padding_x = (1 - (1 / r)) / 2
    else:
        padding_y = (1 - r) / 2

    def t(xy):
        x, y = xy
        qy = (x - min_x) / x_span
        qx = (y - min_y) / y_span

        rx = padding_x + qx * (1 - padding_x * 2)
        ry = padding_y + qy * (1 - padding_y * 2)

        px = (rx * 2 - 1) * padding_p
        py = (ry * 2 - 1) * padding_p
        return (px, py)

    return t


def get_norm_multi2polygon(
    multi2polygon,
    aspect_ratio=16 / 9,
    padding_p=0.75,
):
    t = get_norm_transformer(multi2polygon, aspect_ratio, padding_p)
    return list(map(
        lambda multipolygon: list(map(
            lambda polygon: list(map(
                t,
                polygon,
            )), multipolygon
        )),
        multi2polygon,
    ))


def get_norm_multipolygon(
    t,
    multipolygon,
):
    return list(map(
        lambda polygon: list(map(
            t,
            polygon,
        )), multipolygon
    ))
