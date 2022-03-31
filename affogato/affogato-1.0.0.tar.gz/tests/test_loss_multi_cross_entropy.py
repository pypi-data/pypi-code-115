from affogato.loss import MultiCrossEntropy
import numpy as np


def test_multi_cross_entropy_simple():
    loss = MultiCrossEntropy()

    assert np.allclose(
        loss(
            np.array([[0.1, 0.9, 0.1]]),
            np.array([[0, 1, 0]])
        ),
        0.05,
        atol=0.05,
    )

    assert np.allclose(
        loss(
            np.array([[0.1, 0.9, 0.1]]),
            np.array([[1, 0, 0]])
        ),
        0.8,
        atol=0.05,
    )


def test_multi_cross_entropy_boundaries():
    loss = MultiCrossEntropy()

    inp = np.array([[0, 1, 0]])
    assert np.allclose(loss(inp, inp), 0)


def test_multi_cross_entropy_derivative():
    loss = MultiCrossEntropy()

    target = np.array([[0, 1, 0]])
    actual = np.array([[0.1, 0.9, 0.1]])

    loss(actual, target)
    deriv = loss.derivative()

    assert np.allclose(
        deriv,
        np.array([[0, -1, 0]]),
        atol=0.2,
    )

