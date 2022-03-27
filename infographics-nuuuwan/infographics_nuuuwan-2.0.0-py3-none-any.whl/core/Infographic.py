from cairosvg import svg2png

from infographics._utils import log
from infographics.core.SVGPalette import SVGPalette


class Infographic:
    DEFAULT_SIZE = 1200, 675, 20
    DEFAULT_BASE_FONT_SIZE = 16
    DEFAULT_FOOTER_TEXT = 'Visualization Created with' \
        + ' github.com/nuuuwan/infographics'

    def __init__(
        self,
        title='Title',
        subtitle='Subtitle',
        data_source_text='Data Source',
        footer_text=DEFAULT_FOOTER_TEXT,
        children=[],
        size=DEFAULT_SIZE,
        base_font_size=DEFAULT_BASE_FONT_SIZE,
    ):
        self.title = title
        self.subtitle = subtitle
        self.data_source_text = data_source_text
        self.footer_text = footer_text

        self.children = children
        self.palette = SVGPalette(size, base_font_size)

    def __xml__(self):
        return self.palette.draw_svg([
            self.palette.draw_rect(),
        ] + [child.__xml__(self.palette) for child in self.children] + [
            self.palette.draw_text(self.title, (0, 0.9), 2),
            self.palette.draw_text(self.subtitle, (0, 0.82), 1),
            self.palette.draw_text(self.data_source_text, (0, -0.87), 1),
            self.palette.draw_text(self.footer_text, (0, -0.93), 0.67),
        ])

    def save(self, svg_file):
        self.__xml__().store(svg_file)
        log.info(f'Saved {svg_file}')

        png_file = svg_file[:-3] + 'png'
        svg2png(url=svg_file, write_to=png_file, scale=4)
        log.info(f'Saved {png_file}')
