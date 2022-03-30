from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

if TYPE_CHECKING:
    from signum import SignalContainer

from signum.plotting.scaled_axes import ScaledAxes


mpl.rcParams['axes.grid'] = True
mpl.rcParams['grid.color'] = 'lightgrey'


class Plotter:
    def __init__(self, n_rows=1, n_cols=1, title=None, **kwargs):
        fig, axes = plt.subplots(n_rows, n_cols, **kwargs)
        if n_rows == 1 and n_cols == 1:
            axes = np.array([axes])
        axes = axes.reshape(n_rows, n_cols)

        for row in range(n_rows):
            for col in range(n_cols):
                axes[row, col] = ScaledAxes(axes[row, col])

        self.fig = fig
        self.axes = axes
        self.lines = {}
        self.plot_data = {}

        if title:
            fig.suptitle(title)

    def add_legend(self, **kwargs):
        """Add legend to each of the main grid axes."""

        for ax in self.axes.flatten():
            ax.add_legend(**kwargs)

    def show_fig(self, **kwargs):
        self.fig.show(**kwargs)

    @staticmethod
    def show_all(**kwargs):
        plt.show(**kwargs)

    def add_line(self, signal: 'SignalContainer', add_legend=True, **kwargs):
        if signal.description and 'label' not in kwargs:
            kwargs['label'] = signal.description

        lines = self._add_line(signal, **kwargs)

        if add_legend and 'label' in kwargs:
            self.add_legend()

        k = kwargs.get('label', f'line {len(self.lines)}')
        self.lines[k] = lines
        self.plot_data[k] = signal

    def _add_line(self, signal, **kwargs):
        raise NotImplementedError


class SimplePlotter(Plotter):
    def __init__(self, x_label='', y_label='', **kwargs):
        super().__init__(n_rows=1, n_cols=1, **kwargs)

        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)

    @property
    def ax(self):
        return self.axes[0, 0]

    def _add_line(self, signal: 'SignalContainer', **kwargs):
        if np.iscomplexobj(signal):
            raise ValueError("Can't plot complex data on a SimplePlotter")

        lines = self.ax.plot(signal, **kwargs)

        return lines
