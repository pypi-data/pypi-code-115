import numpy as np
from cho_util.math.common import *


def from_matrix(x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty(shape=np.shape(x)[:-2] + (3,))
    i, j, k = 0, 1, 2

    cy = np.sqrt(x[..., i, i]*x[..., i, i] + x[..., j, i]*x[..., j, i])

    msk = (cy > np.finfo(x.dtype).eps)
    x_a = x[msk]
    out[msk, 0] = np.arctan2(x_a[..., k, j], x_a[..., k, k])
    out[msk, 1] = np.arctan2(-x_a[..., k, i], cy[msk])
    out[msk, 2] = np.arctan2(x_a[..., j, i], x_a[..., i, i])

    nmsk = ~msk
    if nmsk.sum() > 0:
        raise ValueError("{}".format(nmsk.sum()))
    x_b = x[nmsk]
    out[nmsk, 0] = np.arctan2(-x_b[..., j, k],  x_b[..., j, j])
    out[nmsk, 1] = np.arctan2(-x_b[..., k, i],  cy[nmsk])
    out[nmsk, 2] = 0.0

    return out


def from_quaternion(x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty(shape=np.shape(x)[:-1] + (3,))

    qx, qy, qz, qw = [x[..., i] for i in range(4)]

    xx = 2.0 * qx*qx
    yy = 2.0 * qy*qy
    zz = 2.0 * qz*qz

    wx = 2.0 * qw*qx
    wy = 2.0 * qw*qy
    wz = 2.0 * qw*qz

    xy = 2.0 * qx*qy
    yz = 2.0 * qy*qz
    zx = 2.0 * qx*qz

    cy = np.sqrt(np.square(wz+xy) + np.square(yy+zz-1.0))
    out[..., 0] = np.arctan2(wx+yz, 1.0-xx-yy)
    out[..., 1] = np.arctan2(wy-zx, cy)
    out[..., 2] = np.arctan2(wz+xy, 1.0-yy-zz)

    return out


def from_euler(x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty(shape=np.shape(x)[:-1] + (3,))
    np.copyto(out, x)
    return out


def from_axis_angle(x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty(shape=np.shape(x)[:-1] + (3,))

    if x.shape[-1] == 3:
        # format : angle * axis
        angle = norm(x)
        axis = x / angle[..., None]
    elif x.shape[-1] == 4:
        # format : (axis, angle)
        axis = x[..., :3]
        angle = x[..., 3]
    else:
        raise ValueError("Invalid Input Shape : {}".format(x.shape))

    h = angle
    x, y, z = [axis[..., i] for i in range(3)]

    x0 = h
    x3 = np.cos(x0)
    x1 = np.sin(x0)
    x2 = y*z
    x10 = x*z
    x24 = x*y
    x4 = np.square(x)
    x7 = np.square(y)
    x16 = np.square(z)
    x11 = np.square(x7)
    x13 = np.square(x16)
    x5 = x3
    x6 = x4*x5
    x8 = x5*x7
    x9 = -x7 + x8 + 1
    x12 = x11
    x14 = x13
    x15 = 2.0*x7
    x17 = 2.0*x16
    x18 = x4*x7
    x19 = np.square(x5)
    x20 = x1
    x21 = x15*x16
    x22 = 2.0*x5
    x23 = x*x2*x20
    cy = np.sqrt(-x11*x22 + x12*x19 + x12 - x13*x22 + x14*x19 + x14 - x15*x6 - x15 + x16*np.square(x20) -
                 4.0*x16*x8 + x17*x5 - x17 + x18*x19 + x18 + x19*x21 + x21 - x22*x23 + 2.0*x23 + 2.0*x8 + 1.0)

    out[..., 0] = np.arctan2(x*x1 - x2*x3 + x2, -x4 + x6 + x9)
    out[..., 1] = np.arctan2(x1*y + x10*x3 - x10, cy)
    out[..., 2] = np.arctan2(x1*z - x24*x3 + x24, x16*x5 - x16 + x9)
    return out


def rotate(r, x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty_like(x)

    c = np.cos(r)
    s = np.sin(r)

    cx, cy, cz = [c[..., i] for i in range(3)]
    sx, sy, sz = [s[..., i] for i in range(3)]
    x, y, z = [x[..., i] for i in range(3)]

    x2 = -cx*sz
    x6 = cz*sx
    x7 = sz*sx
    x8 = cx*cz
    x10 = x*cy

    np.multiply(x10, cz, out=out[..., 0])
    out[..., 0] += y*(sy*x6+x2)
    out[..., 0] += z*(sy*x8+x7)

    np.multiply(sz, x10, out=out[..., 1])
    out[..., 1] += y*(sy*x7+x8)
    out[..., 1] -= z*(x2*sy+x6)

    np.multiply(-x, sy, out=out[..., 2])
    out[..., 2] += cx*cy*z
    out[..., 2] += sx*cy*y

    return out


def random(size=(), *args, **kwargs):
    size = tuple(np.reshape(size, [-1])) + (3,)
    return np.random.normal(size=size, *args, **kwargs)


def identity(dtype=np.float64):
    return np.zeros(3, dtype=dtype)
