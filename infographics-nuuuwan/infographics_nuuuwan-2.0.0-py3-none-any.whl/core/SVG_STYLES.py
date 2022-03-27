DEFAULT_FONT = 'Futura'


DEFAULT_FILL = {
    'fill': 'white',
}
DEFAULT_STROKE = {
    'stroke': 'lightgray',
    'stroke-width': 0.5,
}
DEFAULT_BORDERED_AREA = DEFAULT_FILL | DEFAULT_STROKE


class SVG_STYLES:
    SVG = {
        'xmlns': 'http://www.w3.org/2000/svg',
    }

    TEXT = {
        'fill': 'black',
        'stroke': 'none',
        'text-anchor': 'middle',
        'dominant-baseline': 'middle',
        'font-family': DEFAULT_FONT,
    }

    LINE = DEFAULT_STROKE
    RECT = DEFAULT_BORDERED_AREA
    CIRCLE = DEFAULT_BORDERED_AREA | {'stroke': 'gray'}
    PATH = DEFAULT_BORDERED_AREA
