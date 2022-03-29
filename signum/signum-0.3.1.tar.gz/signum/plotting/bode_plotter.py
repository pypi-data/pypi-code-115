import matplotlib.pyplot as plt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from signum import SignalContainer

from signum.plotting.plotter import Plotter


class BodePlotter(Plotter):
    def __init__(self, figsize=(8, 6), db_scale: bool = False, rad: bool = False, unwrapped: bool = False,
                 unit='', x_unit='', x_label='', **kwargs):
        super().__init__(n_rows=2, n_cols=1, sharex='all', figsize=figsize, **kwargs)

        self.amplitude_ax.set_ylabel(f"Amplitude")
        self.amplitude_ax.set_y_unit('dB' if db_scale else unit)
        self.phase_ax.set_ylabel(f"Phase")
        self.phase_ax.set_y_unit('rad' if rad else 'deg')
        self.phase_ax.set_x_unit(x_unit)
        self.phase_ax.set_xlabel(x_label)

        self._db_scale = db_scale
        self._rad = rad
        self._unwrapped = unwrapped

    @property
    def amplitude_ax(self) -> plt.Axes:
        return self.axes[0, 0]

    @property
    def phase_ax(self) -> plt.Axes:
        return self.axes[1, 0]

    def _add_line(self, signal: 'SignalContainer', **kwargs):
        mag = signal.magnitude_db if self._db_scale else signal.magnitude
        amplitude_lines = self.amplitude_ax.plot(mag.T, **kwargs)

        phase = signal.get_phase(rad=self._rad, unwrapped=self._unwrapped)
        phase_lines = self.phase_ax.plot(phase.T, **kwargs)

        return amplitude_lines, phase_lines

