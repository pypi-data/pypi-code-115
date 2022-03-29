import numpy as np

from cho_util.math.rotation import _matrix
from cho_util.math.rotation import _quaternion
from cho_util.math.rotation import _euler
from cho_util.math.rotation import _axis_angle
from cho_util.math.rotation._euler import *


def to_matrix(x, *args, **kwargs):
    return _matrix.from_euler(x, *args, **kwargs)


def to_quaternion(x, *args, **kwargs):
    return _quaternion.from_euler(x, *args, **kwargs)


def to_euler(x, *args, **kwargs):
    return _euler.from_euler(x, *args, **kwargs)


def to_axis_angle(x, *args, **kwargs):
    return _axis_angle.from_euler(x, *args, **kwargs)


def inverse(r, out=None):
    r = np.asarray(r)
    if out is None:
        out = np.empty_like(r)
    return _euler.from_quaternion(_quaternion.inverse(_quaternion.from_euler(r)), out=out)

# def rotate(r, x, out=None):
#    # option : delegate to matrix
#    r = to_matrix(r)
#    out = _matrix.rotate(r, x, out)
#    return out
