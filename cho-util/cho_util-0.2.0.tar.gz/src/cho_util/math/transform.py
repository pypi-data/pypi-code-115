import numpy as np
from .common import *
from . import rotation

def to_homogeneous(x):
    x = np.asarray(x)
    o = np.ones_like(x[..., :1])
    return np.concatenate([x, o], axis=-1)

def from_homogeneous(x):
    return x[..., :-1] / x[..., -1:]

def compose(r, t, rtype, out=None):
    if out is None:
        shape = tuple(np.shape(t)[:-1]) + (4, 4)
        out = np.zeros(shape, dtype=t.dtype)
    rtype.to_matrix(r, out=out[..., :3, :3])
    out[..., :3, 3:] = t.reshape(out[...,:3,3:].shape)
    return out

def translation_from_matrix(T):
    return T[..., :3, 3]

def rotation_from_matrix(T):
    return T[..., :3, :3]

def rotation_2d(x, R=None, c=None, s=None):
    if R is None:
        shape = tuple(np.shape(x)[:-1]) + (2, 2)
        R = np.zeros(shape, dtype=x.dtype)
    if c is None:
        c = np.cos(x)
    if s is None:
        s = np.sin(x)
    R[..., 0, 0] = c
    R[..., 0, 1] = -s
    R[..., 1, 0] = s
    R[..., 1, 1] = c
    return R

def Rz(x, T=None, c=None, s=None):
    if T is None:
        shape = tuple(np.shape(x)[:-1]) + (4, 4)
        T = np.zeros(shape, dtype=np.float32)
    if c is None:
        c = np.cos(x)
    if s is None:
        s = np.sin(x)

    T[..., 0, 0] = c
    T[..., 0, 1] = -s
    T[..., 1, 0] = s
    T[..., 1, 1] = c
    T[..., 2, 2] = 1

    return T

def invert(T, out=None):
    R = T[..., :3, :3]
    t = T[..., :3, 3:]

    if out is None:
        out = np.zeros_like(T)
    out[..., :3, :3] = R.swapaxes(-1, -2)
    out[..., :3, 3:] = -np.einsum('...ba,...bc->...ac', R, t)
    out[..., 3, 3] = 1
    return out


def Rti(R, t):
    Ri = R.swapaxes(-1, -2)
    if np.ndim(t) < np.ndim(Ri):
        # case (...,D)
        ti = -np.einsum('...ab,...b->...a', Ri, t)
    else:
        # case (...,D,1)
        ti = -np.einsum('...ab,...bc->...ac', Ri, t)
    return Ri, ti


def lerp(a, b, w):
    return (a * (1.0-w)) + (b*w)


def flerp(a, b, w, f, fi):
    return fi(lerp(f(a), f(b), w))


def rlerp(ra, rb, w):
    Ra = np.eye(4, dtype=np.float32)
    Rb = np.eye(4, dtype=np.float32)
    Ra[:3, :3] = ra
    Rb[:3, :3] = rb

    qa = tx.quaternion_from_matrix(Ra)
    qb = tx.quaternion_from_matrix(Rb)
    q = tx.quaternion_slerp(q0, q1, w)
    R = tx.quaternion_matrix(q)[:3, :3]
    return R

def rx3(R, x):
    rx = np.einsum('...ab,...b->...a', R[..., :3, :3], x)
    return rx

def tx3(T, x):
    rx = np.einsum('...ab,...b->...a', T[..., :3, :3], x)
    return rx + T[..., :3, 3:].swapaxes(-2, -1)


def rtx3(r, t, x):
    return x.dot(r.swapaxes(-2, -1)) + t


def tx4(T, x):
    return np.einsum('...ab,...b->...a', T, x)
