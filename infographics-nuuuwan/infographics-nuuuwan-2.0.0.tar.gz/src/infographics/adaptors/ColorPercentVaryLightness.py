from utils import colorx


class ColorPercentVaryLightness:
    def __init__(self, hue=0, min_p_lightness=1, max_p_lightness=0.2):
        self.hue = hue
        self.min_p_lightness = min_p_lightness
        self.max_p_lightness = max_p_lightness

    @property
    def lightness_span(self):
        return self.max_p_lightness - self.min_p_lightness

    def get_color_from_color_value(self, p):
        return colorx.random_hsl(
            hue=self.hue,
            lightness=self.min_p_lightness + self.lightness_span * p,
        )
