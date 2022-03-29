#!/usr/bin/env python2

import numpy as np
import cho_util.math.rotation as rotation

def print_Rt(R, t, round=2):
    print('\tR', np.round(np.rad2deg(rotation.euler.from_matrix(R)), round))

    n = np.linalg.norm(t)
    u = (t.ravel()/n  if n > np.finfo(np.float32).eps else t.ravel())
    print('\tt', np.round(u, round))

def print_ratio(a, b, name=''):
    q = (np.nan if (np.isscalar(b) and np.isclose(b, 0)) else (100.0*a)/b)
    print('[{}] {}/{}={}%'.format(name, a, b, q))
