import matplotlib.pyplot as plt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from signum import SignalContainer

from signum.plotting.plotter import Plotter


class IQPlotter(Plotter):
    def __init__(self, figsize=(8, 6), sharey='all', unit='', x_unit='', x_label='', **kwargs):
        super().__init__(n_rows=2, n_cols=1, sharex='all', sharey=sharey, figsize=figsize, **kwargs)

        self.i_ax.set_ylabel("Real")
        self.q_ax.set_ylabel("Imag")
        self.q_ax.set_xlabel(x_label)

        self.i_ax.set_y_unit(unit)
        self.q_ax.set_y_unit(unit)
        self.q_ax.set_x_unit(x_unit)

    @property
    def i_ax(self) -> plt.Axes:
        return self.axes[0, 0]

    @property
    def q_ax(self) -> plt.Axes:
        return self.axes[1, 0]

    def _add_line(self, signal: 'SignalContainer', **kwargs):
        i_lines = self.i_ax.plot(signal.real.T, **kwargs)
        q_lines = self.q_ax.plot(signal.imag.T, **kwargs)

        return i_lines, q_lines

