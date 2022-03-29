

import arrow
from kivy_garden.ebs.core.labels import SelfScalingLabel
from .base import ClockBase


class SimpleDigitalClock(ClockBase, SelfScalingLabel):
    def __init__(self, fmt="HH:mm:ss", **kwargs):
        self._format = fmt
        ClockBase.__init__(self)
        SelfScalingLabel.__init__(self, **kwargs)
        self.bind(texture_size=self.setter('size'))
        self.start()

    def update(self):
        self.text = arrow.now().format(self._format)
