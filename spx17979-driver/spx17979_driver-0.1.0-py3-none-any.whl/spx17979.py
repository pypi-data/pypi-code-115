from pca9536 import PCA9536, PinMode
from smbus2 import SMBus


class SPX17979:
    """Driver for the SparkFun SPX-17979 Qwiic Sound Trigger"""

    def __init__(self, bus: SMBus, address: int = 0x41):
        """Initialise the SPX17979.

        Args:
            bus: An open SMBus object.
            address: The I2C address of the on-board PCA9536 device. Defaults to 0x41.
                Since it is fixed, one should never have to change this."""
        self._device = PCA9536(bus=bus, address=address)
        self._device.mode = PinMode.input  # type: ignore  # https://github.com/python/mypy/issues/3004
        self._mode, self._trigger = self._device[0], self._device[1]
        self._mode.write(False)

    def reset(self) -> None:
        """Reset the trigger.

        Sets the trigger value back to False."""
        # We normally keep the reset pin in input mode. For the reset, we briefly
        # set the reset pin to output mode. This allows a reset with the button.
        self._mode.mode = PinMode.output
        self._mode.mode = PinMode.input

    @property
    def trigger(self) -> bool:
        """Get the trigger status.

        Returns True when the device has been triggered."""
        return self._trigger.read()
