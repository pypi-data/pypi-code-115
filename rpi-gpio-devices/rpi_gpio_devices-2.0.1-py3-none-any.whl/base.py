import logging
from datetime import datetime

import RPi.GPIO as gpio


class BaseDevice:
    """ Base class for other devices or classes

    :param gpiomode: Gpio pin numbering mode. "board" or "bcm"
    :param gpiowarnings: Gpio configuration warnings
    :param log: If True, log what happens
    :param log_file: File to save log messages
    """
    def __init__(self, gpiomode='board', gpiowarnings=False, log=False, log_file=''):
        self.log = log
        if log:
            logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S',
                                level=logging.INFO,
                                filename=log_file,
                                filemode='w')
            self._logger = logging.getLogger()
        # GPIO basic settings
        gpio.setmode({'board': gpio.BOARD, 'bcm': gpio.BCM}[gpiomode])
        gpio.setwarnings(gpiowarnings)

    def message(self, value):
        """ Print messages if log mode is on """
        if self.log:
            self._logger.info(value)

    def cleanup(self):
        """ Cleanup GPIOs """
        self.message('Cleanup GPIOs...')
        gpio.cleanup()


class SwitchableDevice(BaseDevice):
    """ Device that can be switched on or off

    :param power: Pin used for powering the device
    """
    def __init__(self, power, **kwargs):
        super().__init__(**kwargs)
        self.on = False # Device is on or off
        self.turned_on_at = False # When the device was turned on
        self.power = power
        if power:
            gpio.setup(power, gpio.OUT)

    def is_on(self):
        """ True if device is on """
        return self.on

    def is_off(self):
        """ True if device is off """
        return not self.on

    def _turn_on(self):
        self.message('Device turned on.')
        self.turned_on_at = datetime.now()
        self.on = True

    def turn_on(self):
        """ Turn on the device """
        if self.is_on():
            return
        gpio.output(self.power, 1)
        self._turn_on()

    def _turn_off(self):
        self.message('Device turned off.')
        self.turned_on_at = False
        self.on = False

    def turn_off(self):
        """ Turn off the device """
        if self.is_off():
            return
        gpio.output(self.power, 0)
        self._turn_off()

    def toggle(self):
        """ Toggle device """
        if self.is_off():
            self.turn_on()
        elif self.is_on():
            self.turn_off()

    def ontime(self):
        """ Calculate the ontime if the device is on """
        if self.is_off():
            return 0
        difference = datetime.now() - self.turned_on_at
        ontime = int(difference.total_seconds())
        self.message(f'Ontime {ontime} seconds.')
        return ontime


class PWMDevice(SwitchableDevice):
    """ Device that can be controlled with PWM signals

    :param pwm: Pin used for pwm control
    :param power: Pin used for giving power supply (optional)
    :param frequency: Frequency used for the pwm signal
    """
    def __init__(self, pwm, power=False, frequency=100, **kwargs):
        super().__init__(power, **kwargs)
        self.frequency = frequency
        self.duty_cycle = 0 # Duty cycle between 0.0 and 100.0
        self.pwm = False
        if pwm:
            gpio.setup(pwm, gpio.OUT)
            self.pwm = gpio.PWM(pwm, self.frequency)

    def turn_on(self):
        """ Turn on the power and pwm on the lowest setting """
        if self.is_on():
            return
        self.duty_cycle = 0
        if self.pwm:
            self.pwm.start(0)
        if self.power:
            gpio.output(self.power, 1)
        self._turn_on()

    def turn_off(self):
        """ Turn off the power and pwm """
        if self.is_off():
            return
        self.duty_cycle = 0
        if self.pwm:
            self.pwm.stop()
        if self.power:
            gpio.output(self.power, 0)
        self._turn_off()

    def set_duty_cycle(self, percent, z_off=True):
        """ Set duty cycle.

        :param percent: Duty cycle between 0% and 100%
        :param z_off: Turn off at zero
        """
        if not self.pwm:
            raise ValueError('No pin provided for outputting PWM signal!')
        if z_off and percent == 0:
            self.turn_off()
            return
        if self.is_off():
            self.turn_on()
        elif self.duty_cycle == percent:
            return
        self.message(f'Duty cycle set to {percent}%.')
        self.duty_cycle = percent
        self.pwm.ChangeDutyCycle(percent)
