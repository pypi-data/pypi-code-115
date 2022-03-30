# @auto-fold regex /^\s*if/ /^\s*else/ /^\s*def/
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version 0.0.1
# date 30 march 2022

__all__ = ['owoifier']

import numpy as np
import os, sys

def fold(x, y, yerr=None, per=None):
    if per == None:
        per = 2. * np.pi
    x_f = x % per
    order = np.argsort(x_f)
    if yerr is None:
        return x_f[order], y[order]
    else:
        return x_f[order], y[order], yerr[order]
    pass

def minmax(x):
    return np.amin(x), np.amax(x)

def flatten(t):
    return [item for sublist in t for item in sublist]
