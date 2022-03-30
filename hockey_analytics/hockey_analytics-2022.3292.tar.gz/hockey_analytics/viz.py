"""Viz-focused utilities"""

# imports
from hockey_rink import NHLRink, IIHFRink, NWHLRink
import matplotlib.pyplot as plt

def plot_bdc_rink(league="NWHL"):
    """
    Lower level utility to wrap hockey_rink package in the context of the data within this package.
    After loading this utility, plt.show() will plot the rink.

    Args:
        league (str, optional): The rink to . Defaults to "NWHL".

    Returns:
        tuple: A tuple of the rink, ax for `matplotlib.pyplot`
    """
    # wrapper for plotting via the fantastic hockey_rink
    if league=="NWHL":
        rink = NWHLRink(x_shift=100, y_shift=42.5, nzone={"length": 50})
    ax = rink.draw()
    return rink, ax
    
