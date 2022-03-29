import numpy as np
from cho_util.math.common import *


def from_matrix(x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty(shape=np.shape(x)[:-2] + (3, 3))
    np.copyto(out, x)
    return out


def from_quaternion(x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty(shape=np.shape(x)[:-1] + (3, 3))

    qx, qy, qz, qw = [x[..., i] for i in range(4)]

    tx = 2.0 * qx
    ty = 2.0 * qy
    tz = 2.0 * qz
    twx = tx * qw
    twy = ty * qw
    twz = tz * qw
    txx = tx * qx
    txy = ty * qx
    txz = tz * qx
    tyy = ty * qy
    tyz = tz * qy
    tzz = tz * qz

    out[..., 0, 0] = 1.0 - (tyy + tzz)
    out[..., 0, 1] = txy - twz
    out[..., 0, 2] = txz + twy

    out[..., 1, 0] = txy + twz
    out[..., 1, 1] = 1.0 - (txx + tzz)
    out[..., 1, 2] = tyz - twx

    out[..., 2, 0] = txz - twy
    out[..., 2, 1] = tyz + twx
    out[..., 2, 2] = 1.0 - (txx + tyy)

    return out


def from_euler(x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty(shape=np.shape(x)[:-1] + (3, 3))

    c, s = np.cos(x), np.sin(x)
    cx, cy, cz = [c[..., i] for i in range(3)]
    sx, sy, sz = [s[..., i] for i in range(3)]

    out[..., 0, 0] = cy * cz
    out[..., 0, 1] = (sx * sy * cz) - (cx * sz)
    out[..., 0, 2] = (cx * sy * cz) + (sx * sz)
    out[..., 1, 0] = cy * sz
    out[..., 1, 1] = (sx * sy * sz) + (cx * cz)
    out[..., 1, 2] = (cx * sy * sz) - (sx * cz)
    out[..., 2, 0] = -sy
    out[..., 2, 1] = sx * cy
    out[..., 2, 2] = cx * cy

    return out


def from_axis_angle(x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty(shape=np.shape(x)[:-1] + (3, 3))

    if x.shape[-1] == 3:
        # format : angle * axis
        angle = norm(x, keepdims=True)
        axis = x / angle[..., None]
    elif x.shape[-1] == 4:
        # format : (axis, angle)
        axis = x[..., :3]
        angle = x[..., 3:]
    else:
        raise ValueError("Invalid Input Shape : {}".format(x.shape))

    sin_axis = np.sin(angle) * axis
    cos_angle = np.cos(angle)
    cos1_axis = (1.0 - cos_angle) * axis
    axis_y, axis_z = [axis[..., i] for i in (1, 2)]
    cos1_axis_x, cos1_axis_y = [cos1_axis[..., i] for i in (0, 1)]
    sin_axis_x, sin_axis_y, sin_axis_z = [sin_axis[..., i] for i in range(3)]
    tmp = cos1_axis_x * axis_y
    m01 = tmp - sin_axis_z
    m10 = tmp + sin_axis_z
    tmp = cos1_axis_x * axis_z
    m02 = tmp + sin_axis_y
    m20 = tmp - sin_axis_y
    tmp = cos1_axis_y * axis_z
    m12 = tmp - sin_axis_x
    m21 = tmp + sin_axis_x
    diag = cos1_axis * axis + cos_angle
    diag_x, diag_y, diag_z = [diag[..., i] for i in range(3)]

    out[..., 0, 0] = diag_x
    out[..., 0, 1] = m01
    out[..., 0, 2] = m02

    out[..., 1, 0] = m10
    out[..., 1, 1] = diag_y
    out[..., 1, 2] = m12

    out[..., 2, 0] = m20
    out[..., 2, 1] = m21
    out[..., 2, 2] = diag_z

    return out


def rotate(r, x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty_like(x)
    np.einsum('...ij,...j->...i', r, x, out=out)
    return out


def random(size=(), *args, **kwargs):
    # TODO(yycho0108): more efficient randomization
    size = tuple(np.reshape(size, [-1])) + (3, 3)
    out = np.random.normal(size=size, *args, **kwargs)
    out = [np.linalg.qr(o)[0] for o in out.reshape(-1, 3, 3)]
    out = np.reshape(out, size)
    return out


def inverse(r, out=None):
    if out is None:
        out = np.empty_like(r)
    np.copyto(out, r.swapaxes(-2, -1))
    return out

def identity(dtype=np.float64):
    return np.eye(3, dtype=dtype)
