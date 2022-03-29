from cho_util.math.common import *
import numpy as np


def from_matrix(x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty(shape=np.shape(x)[:-2] + (4,))

    m00, m01, m02 = [x[..., 0, i] for i in range(3)]
    m10, m11, m12 = [x[..., 1, i] for i in range(3)]
    m20, m21, m22 = [x[..., 2, i] for i in range(3)]

    np.subtract(m21, m12, out=out[..., 0])
    np.subtract(m02, m20, out=out[..., 1])
    np.subtract(m10, m01, out=out[..., 2])
    out[..., :3] = uvec(out[..., :3])
    out[..., 3] = np.arccos(np.clip((m00 + m11 + m22 - 1)*0.5, -1.0, 1.0))
    return out


def from_quaternion(x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty(shape=np.shape(x)[:-1] + (4,))
    qw = x[..., 3:]
    out[..., :3] = uvec(x[..., :3])
    out[..., 3:] = 2 * np.arccos(np.clip(qw, -1.0, 1.0))
    return out


def from_euler(x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty(shape=np.shape(x)[:-1] + (4,))

    x, y, z = [x[..., i] for i in range(3)]

    x0 = np.cos(x)
    x6 = np.sin(x)
    x3 = np.cos(y)
    x4 = np.sin(y)
    x5 = np.cos(z)
    x1 = np.sin(z)

    x2 = x0*x1
    x10 = x1*x6
    x7 = x5*x6
    x11 = x0*x5

    x8 = x1*x3 + x2 - x4*x7
    x9 = -x2*x4 + x3*x6 + x7
    x12 = x10 + x11*x4 + x4

    out[..., 0] = x9
    out[..., 1] = x12
    out[..., 2] = x8
    out[..., :3] = uvec(out[..., :3])

    out[..., 3] = np.arccos(
        np.clip(0.5 * (x0*x3 + x10*x4 + x11 + x3*x5 - 1), -1.0, 1.0))
    return out


def from_axis_angle(x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty(shape=np.shape(x)[:-1] + (4,))
    np.copyto(out, x)
    return out


def rotate(r, x, out=None):
    x = np.asarray(x)
    if out is None:
        out = np.empty_like(x)
    if r.shape[-1] == 3:
        # format : angle * axis
        angle = norm(r, keepdims=True)
        axis = r / angle
    elif r.shape[-1] == 4:
        # format : (axis, angle)
        axis = r[..., :3]
        angle = r[..., 3:]
    else:
        raise ValueError("Invalid Input Shape : {}".format(x.shape))
    u = axis
    c, s = np.cos(angle), np.sin(angle)
    d = (u*x).sum(axis=-1, keepdims=True)

    # out = (x*c) + s*np.cross(u, x) + (1.-c)*d*u
    np.multiply(x, c, out=out)
    out += s*np.cross(u, x)
    out += (1.-c)*d*u
    return out


def random(size=(), *args, **kwargs):
    size = tuple(np.reshape(size, [-1])) + (4,)
    out = np.random.normal(size=size, *args, **kwargs)
    out[..., :3] = uvec(out[..., :3])
    return out


def inverse(r, out=None):
    r = np.asarray(r)
    if out is None:
        out = np.empty_like(r)
    out[..., :3] = r[..., :3]
    out[..., 3] = -r[..., 3]
    return out


def identity(dtype=np.float64):
    return np.asarray([1, 0, 0, 0], dtype=dtype)
