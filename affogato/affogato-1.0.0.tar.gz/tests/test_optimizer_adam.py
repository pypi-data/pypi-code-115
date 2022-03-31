import numpy as np
from affogato.model import Model
from affogato.optimizer import Adam
from affogato.layer import Dense
from affogato.activation import Sigmoid, ReLU, Linear
from affogato.loss import MeanSquaredError, CrossEntropy


def test_adam_trivial_problem():
    def pair(x): return (x, x)

    data = [
        pair(np.random.randn(1, 1))
        for _ in range(100)
    ]

    model = Model(1)
    model.add(Dense(1, activation=Linear()))
    model.compile()
    loss_history = model.fit(
        data,
        Adam(model.parameters, 0.1),
        num_epochs=20,
        batch_size=32,
        verbose=True,
    )

    print(f"{model.parameters = }")

    assert loss_history[0] > loss_history[-1], "Loss did not decrease"
    assert loss_history[-1] < 1e-2, "Loss did not converge"
    assert np.allclose(
        model.predict(np.array([[1]])),
        np.array([[1]]),
        atol=1e-1,
    ), "Model did not learn the identity function"


def test_adam_xor_problem():
    data = [
        (np.array([[0, 0]]), np.array([[0]])),
        (np.array([[0, 1]]), np.array([[1]])),
        (np.array([[1, 0]]), np.array([[1]])),
        (np.array([[1, 1]]), np.array([[0]])),
    ]

    model = Model(2)
    model.add(Dense(8, activation=ReLU()))
    model.add(Dense(1, activation=Sigmoid()))
    model.compile()

    opt = Adam(model.parameters, 0.1)
    loss_history = model.fit(
        data,
        opt,
        num_epochs=50,
        verbose=True,
        loss=CrossEntropy(),
    )

    assert loss_history[0] > loss_history[-1], "Loss did not decrease"
    assert loss_history[-1] < 1e-1, "Model did not converge"
    assert np.allclose(
        model.predict(np.array([[0, 0]])),
        np.array([[0]]),
        atol=1e-1,
    ), "Model did not learn the XOR function"
    assert np.allclose(
        model.predict(np.array([[1, 0]])),
        np.array([[1]]),
        atol=1e-1,
    ), "Model did not learn the XOR function"
    assert np.allclose(
        model.predict(np.array([[0, 1]])),
        np.array([[1]]),
        atol=1e-1,
    ), "Model did not learn the XOR function"
    assert np.allclose(
        model.predict(np.array([[1, 1]])),
        np.array([[0]]),
        atol=1e-1,
    ), "Model did not learn the XOR function"

