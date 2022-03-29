import numpy as np
from matplotlib.ticker import ScalarFormatter

from signum.tools.scale_manager import ScaleManager


class ScaledFormatter(ScalarFormatter):

    def __init__(self, base_unit, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_unit = base_unit

    def get_offset_order(self):
        return int(np.log10(self.offset))

    def get_offset(self):
        if len(self.locs) == 0:
            return ''

        if not self.base_unit:
            return super().get_offset()

        if self.offset:
            offset_str = ScaleManager.display(self.offset, unit=self.base_unit,
                                              order_change=0 if self.no_rescale else None)
            if self.offset > 0:
                offset_str = '+' + offset_str
        else:
            offset_str = ''

        if self.orderOfMagnitude:
            oom_val, oom_unit = ScaleManager.rescale(10 ** self.orderOfMagnitude, self.base_unit)
            oom_str = oom_unit if oom_val == 1 else ScaleManager.display(oom_val, oom_unit)
        else:
            oom_str = self.base_unit

        s = ' '.join((oom_str, offset_str))

        return self.fix_minus(s)

    @property
    def no_rescale(self):
        return self.base_unit.lower() in ['db', 'deg', 'rad', 'none', '']

    def _set_order_of_magnitude(self):
        if len(self.locs) == 0 or self.no_rescale:
            self.orderOfMagnitude = 0
        else:
            # Restrict to visible ticks (this line comes from the ScalarFormatter code)
            vmin, vmax = sorted(self.axis.get_view_interval())

            order = int(np.log10(max([abs(vmin - self.offset), abs(vmax - self.offset)])))
            self.orderOfMagnitude = 3 * divmod(order, 3)[0]

    def __call__(self, x, pos=None):
        if len(self.locs) == 0:
            return ''

        xp = (x - self.offset) / (10. ** self.orderOfMagnitude)
        if abs(xp) < 1e-8:
            xp = 0
        s = self.format % xp
        return self.fix_minus(s)
