import matplotlib.pyplot as plt
import numpy as np


def plot_equity(equity, filename=None):
    _, ax = plt.subplots(2, 1, gridspec_kw={'height_ratios': [1, 3]},
                         sharex=True, figsize=(5.5*(16/9), 5.5))
    running_max = np.maximum.accumulate(equity)
    drawdown = -100 * ((running_max - equity) / running_max)

    ax[0].fill_between(equity.index, 0, drawdown, alpha=0.3, color='r')
    ax[0].set_title('Drawdown')

    ax[1].plot(equity)
    ax[1].set_title('Total Balance')

    if filename:
        plt.savefig(filename)

    return ax
