import time

import RPi.GPIO as gpio

from .base import BaseDevice


class Button(BaseDevice):
    """ Button device

    :param pin: Which pin is connected to the button
    :param debounce_time: Debounce time when checking button state (ms)
    :param polarity: When you press the button, will the pin be connected to low or high?
    """
    def __init__(self, pin, debounce_time=200, polarity='low', **kwargs):
        super().__init__(**kwargs)
        self.debounce_time = debounce_time / 1000
        self.polarity = polarity
        self.pin = pin
        gpio.setup(pin, gpio.IN, pull_up_down={'low': gpio.PUD_UP, 'high': gpio.PUD_DOWN}[polarity])

    def is_pressed(self):
        """ True if the button is pressed """
        def low(pin):
            return bool(not gpio.input(pin))
        def high(pin):
            return bool(gpio.input(pin))
        test = {'low': low, 'high': high}[self.polarity]

        if test(self.pin):
            time.sleep(self.debounce_time)
            if test(self.pin):
                self.message('Button is pressed!')
                return True
        return False
