import os

import numpy as np

if os.getenv('ENVIRONMENT'):
    from laetitudebots.util.decorators import jit
else:
    from numba import jit

@jit(nopython=True)
def low_pivot(low, lb=2, rb=2):
    size = low.shape[0]

    low_pivots = np.full(size, np.nan)

    for i in range(lb + rb, size):
        window = low[i - (rb + lb):i+1]
        mid = low[i - rb]

        if mid == np.min(window):
            low_pivots[i] = mid
        else:
            low_pivots[i] = low_pivots[i-1]

    return low_pivots
