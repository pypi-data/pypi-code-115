import os

import numpy as np

if os.getenv('ENVIRONMENT'):
    from laetitudebots.util.decorators import jit
else:
    from numba import jit


@jit(nopython=True)
def high_pivot(high, lb=2, rb=2):
    size = high.shape[0]

    high_pivots = np.full(size, np.nan)

    for i in range(lb + rb, size):
        window = high[i - (rb + lb):i+1]
        mid = high[i - rb]

        if mid == np.max(window):
            high_pivots[i] = mid
        else:
            high_pivots[i] = high_pivots[i-1]

    return high_pivots
