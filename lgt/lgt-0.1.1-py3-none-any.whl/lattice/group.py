"""
group.py

Contains implementations of various (special) unitary groups.

Date: 2022/03/25

Original version from:

  https://github.com/nftqcd/nthmc/blob/master/lib/group.py

written by Xiao-Yong Jin
"""
from __future__ import absolute_import, division, print_function, annotations

import tensorflow as tf
import math
from typing import Callable

Tensor = tf.Tensor
PI = tf.convert_to_tensor(math.pi)


class Group:
    """Gauge group represented as matrices in the last two dims in tensors."""
    def mul(
            self,
            a: Tensor,
            b: Tensor,
            adjoint_a: bool = False,
            adjoint_b: bool = False
    ) -> Tensor:
        return tf.linalg.matmul(a, b, adjoint_a=adjoint_a, adjoint_b=adjoint_b)


class U1Phase(Group):
    def mul(
            self,
            a: Tensor,
            b: Tensor,
            adjoint_a: bool = False,
            adjoint_b: bool = False
    ) -> Tensor:
        if adjoint_a and adjoint_b:
            return tf.subtract(tf.math.negative(a), b)
        elif adjoint_a:
            return tf.add(tf.math.negative(a), b)
        elif adjoint_b:
            return tf.subtract(a, b)
        else:
            return tf.add(a, b)

    def adjoint(self, x: Tensor) -> Tensor:
        return tf.math.negative(x)

    def trace(self, x: Tensor) -> Tensor:
        return tf.math.cos(x)

    def diff_trace(self, x: Tensor) -> Tensor:
        return tf.math.negative(tf.math.sin(x))

    def diff2trace(self, x: Tensor) -> Tensor:
        return tf.math.negative(tf.math.cos(x))

    def compat_proj(self, x: Tensor) -> Tensor:
        return tf.math.floormod(x + PI, 2 * PI) - PI

    def random(self, shape: list[int]):
        return self.compat_proj(tf.random.uniform(shape, *(-4, 4)))

    def random_momentum(self, shape: list[int]) -> Tensor:
        return tf.random.normal(shape)

    def kinetic_energy(self, p: Tensor) -> Tensor:
        return tf.reduce_sum(
            tf.square(tf.reshape(p, [p.shape[0], -1])),
            axis=1
        )


class SU3(Group):
    dtype = tf.complex128
    size = [3, 3]

    def mul(
            self,
            a: Tensor,
            b: Tensor,
            adjoint_a: bool = False,
            adjoint_b: bool = False,
    ) -> Tensor:
        return tf.linalg.matmul(a, b, adjoint_a=adjoint_a, adjoint_b=adjoint_b)

    def adjoint(self, x: Tensor) -> Tensor:
        return tf.linalg.adjoint(x)

    def trace(self, x: Tensor) -> Tensor:
        return tf.linalg.trace(x)

    def diff_trace(self, x: Tensor):  # type: ignore
        print('TODO')

    def diff2Trace(self, x: Tensor):  # -> Tensor:
        print('TODO')


def eyeOf(m):
    batch_shape = [1] * (len(m.shape) - 2)
    return tf.eye(*m.shape[-2:], batch_shape=batch_shape, dtype=m.dtype)


def exp(m: Tensor, order: int = 12):
    eye = eyeOf(m)
    x = eye + m / tf.constant(order)
    for i in tf.range(order-1, 0, -1):
        x = eye + tf.linalg.matmul(m, x) / tf.constant(tf.cast(i, m.dtype))

    return x


def su3fromvec(v: Tensor) -> Tensor:
    """
    X = X^a T^a
    tr{X T^b} = X^a tr{T^a T^b} = X^a (-1/2) 𝛅^ab = -1/2 X^b
    X^a = -2 X_{ij} T^a_{ji}
    """
    s3 = 0.57735026918962576451  # sqrt(1/3)
    c = -0.5
    zero = tf.zeros(v[..., 0].shape, dtype=v[..., 0].dtype)
    x01 = c * tf.dtypes.complex(v[..., 1], v[..., 0])
    x02 = c * tf.dtypes.complex(v[..., 4], v[..., 3])
    x12 = c * tf.dtypes.complex(v[..., 6], v[..., 5])
    x2i = s3 * v[..., 7]
    x0i = c * (x2i + v[..., 2])
    x1i = c * (x2i - v[..., 2])

    def neg_conj(x: Tensor) -> Tensor:
        return tf.math.negative(tf.math.conj(x))

    # ----------------------------------------------------
    # NOTE: Returns matrix of the form:
    #
    #  M = [[ cmplx(x0i),        -x01*,       -x02*],
    #       [        x01,   cmplx(x1i),       -x12*],
    #       [        x02,          x12,  cmplx(x2i)]]
    # ----------------------------------------------------
    v1 = tf.stack([
        tf.dtypes.complex(zero, x0i), neg_conj(x01), neg_conj(x02)
    ], axis=-1)
    v2 = tf.stack([
        x01, tf.dtypes.complex(zero, x1i), neg_conj(x12)
    ], axis=-1)
    v3 = tf.stack([
        x02, x12, tf.dtypes.complex(zero, x2i)
    ], axis=-1)

    return tf.stack([v1, v2, v3])


def SU3GradientTF(
        f: Callable[[Tensor], Tensor],
        x: Tensor,
) -> tuple[Tensor, Tensor]:
    """Compute gradient using TensorFlow GradientTape.

    y = f(x) must be a real scalar value.

    Returns:
      - (f(x), D), where D = T^a D^a = T^a ∂_a f(x)

    NOTE: Use real vector derivatives, e.g.
      D^a = ∂_a f(x)
          = ∂_t f(exp(T^a) x) |_{t=0}
    """
    zeros = tf.zeros(8)
    with tf.GradientTape(watch_accessed_variables=False) as tape:
        tape.watch(zeros)
        y = f(tf.linalg.matmul(exp(su3fromvec(zeros)), x))
    d = tape.gradient(y, zeros)

    return  y, d
