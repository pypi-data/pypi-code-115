import numpy as np
from affogato.layer import Flatten


def test_flatten_3D():
    f = Flatten()

    data = np.array([[[[1., 2., 3.], [1., 2., 3.]]]])    
    assert np.array_equal(
        f.forward(data),
        np.array([[1., 2., 3., 1., 2., 3.]])
    )

    data = np.array([[[[1., 2., 3.], [1., 2., 3.]], [[4., 5., 6.], [4., 5., 6.]]]])
    assert np.array_equal(
        f.forward(data),
        np.array([[1., 2., 3., 1., 2., 3., 4., 5., 6., 4., 5., 6.]])
    )


def test_flatten_2D():
    f = Flatten()

    data = np.array([[[1., 2., 3., 1., 2., 3.], [4., 5., 6., 4., 5., 6.]]])
    assert np.array_equal(
        f.forward(data),
        np.array([[1., 2., 3., 1., 2., 3., 4., 5., 6., 4., 5., 6.]])
    )


def test_flatten_on_batch():
    f = Flatten()

    data = np.array(
        [
            [[1., 2., 3.], [1., 2., 3.]],
            [[4., 5., 6.], [4., 5., 6.]],
            [[7., 8., 9.], [7., 8., 9.]],
        ]
    )

    assert np.array_equal(
        f.forward(data),
        np.array([[1., 2., 3., 1., 2., 3.], [4., 5., 6., 4., 5., 6.], [7., 8., 9., 7., 8., 9.]])
    )

