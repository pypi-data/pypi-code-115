import matplotlib.pyplot as plt
from matplotlib.projections.polar import PolarAxes
import logging

from signum.plotting.scaled_formatter import ScaledFormatter
from signum.tools.scale_manager import ScaleManager


_NOT_GIVEN_ = object()

logger = logging.getLogger(__name__)


class ScaledAxes:
    def __init__(self, ax: plt.Axes, x_unit='', y_unit='', x_label=None, y_label=None):
        if not isinstance(ax, plt.Axes):
            raise TypeError(f"Expected matplotlib.pyplot.Axes instance, got {type(ax)=}")

        self._ax = ax
        if not isinstance(ax, PolarAxes):
            ax.xaxis.set_major_formatter(ScaledFormatter(x_unit))
        ax.yaxis.set_major_formatter(ScaledFormatter(y_unit))

        if x_label:
            self.set_xlabel(x_label)
        if y_label:
            self.xet_ylabel(y_label)

    def __getattr__(self, item):
        return getattr(self._ax, item)

    @property
    def ax(self):
        return self._ax

    @property
    def x_ax_formatter(self):
        return self.ax.xaxis.get_major_formatter()

    @property
    def y_ax_formatter(self):
        return self.ax.yaxis.get_major_formatter()

    def get_x_unit(self):
        return self.x_ax_formatter.base_unit

    def set_x_unit(self, x_unit):
        self.x_ax_formatter.base_unit = x_unit

    def get_y_unit(self):
        return self.y_ax_formatter.base_unit

    def set_y_unit(self, y_unit):
        self.y_ax_formatter.base_unit = y_unit

    def get_units(self):
        return self.get_x_unit(), self.get_y_unit()

    def set_units(self, x_unit, y_unit):
        self.set_x_unit(x_unit)
        self.set_y_unit(y_unit)

    def plot(self, *args, add_legend=True, **kwargs):
        if len(args) == 3:
            x_data, y_data, fmt = args
        elif len(args) == 2:
            if isinstance(args[1], str):
                y_data, fmt = args
                x_data = None
            else:
                x_data, y_data = args
                fmt = None
        elif len(args) == 1:
            y_data, = args
            x_data = None
            fmt = None
        else:
            raise TypeError(f"Expected 1 to 3 positional arguments, got {len(args)}")

        x_unit = getattr(x_data, 'unit', None) if x_data is not None else getattr(y_data, 'x_unit', None)
        y_unit = getattr(y_data, 'unit', None)
        x_data = x_data if x_data is not None else getattr(y_data, 'x_axis', None)

        x_data, y_data = self._fix_units(x_data, y_data, x_unit, y_unit)

        plot_args = tuple(it for it in (x_data, y_data, fmt) if it is not None)
        lines = self.ax.plot(*plot_args, **kwargs)

        if add_legend and 'label' in kwargs:
            self.add_legend()

        return lines

    def add_legend(self, fancybox=True, framealpha=0.5, **kwargs):
        self.ax.legend(fancybox=fancybox, framealpha=framealpha, **kwargs)

    def _fix_units(self, data_x, data_y, data_x_unit, data_y_unit):
        data = {'x': data_x, 'y': data_y}
        data_units = {'x': data_x_unit, 'y': data_y_unit}

        for xy in 'xy':
            if isinstance(getattr(self.ax, f'{xy}axis').get_major_formatter(), ScaledFormatter):
                ax_unit = getattr(self, f'get_{xy}_unit')()
                data_unit = data_units[xy]
                if not data_unit:
                    logger.debug(f"{xy} data unit not specified")
                    continue

                if ax_unit:
                    if ax_unit != data_unit:
                        _, ax_unit_core = ScaleManager.split_unit(ax_unit)
                        _, data_unit_core = ScaleManager.split_unit(data_unit)
                        if ax_unit_core != data_unit_core:
                            raise ValueError(f"{xy} units of the axes and data do not agree: {ax_unit=}, {data_unit=}")

                        if data[xy] is not None:
                            logger.debug(f"Rescaling {xy} data from {data_unit} to {ax_unit}")
                            order_change = ScaleManager.order_from_unit(ax_unit) - ScaleManager.order_from_unit(data_unit)
                            data[xy], _ = ScaleManager.rescale(data[xy], data_unit, order_change)

                else:
                    logger.debug(f"Setting {xy} unit of the axes to data {xy} unit: {data_unit}")
                    getattr(self, f'set_{xy}_unit')(data_unit)

        return data['x'], data['y']
