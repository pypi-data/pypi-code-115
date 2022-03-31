import numpy as np
from affogato.layer import Dense
from affogato.model import Model
from affogato.optimizer import SGD
from affogato.activation import Linear, Sigmoid


def test_dense_learning_linear_sum():
    """
    Verify that a dense layer can learn a linear sum of inputs.
    """
    # Create a model with a single dense layer.
    model = Model(4)
    model.add(Dense(1, activation=Linear()))
    opt = SGD(model.parameters, learning_rate=0.001)
    
    def inp():
        x = np.random.randint(-10, 10, size=(1, 4))
        return x, np.sum(x, keepdims=True)

    # Create a dataset of inputs and outputs.
    data = [ inp() for _ in range(50) ]

    # Train the model.
    loss_history = model.fit(data, opt, num_epochs=10, batch_size=4, verbose=True)

    # Verify that the model learned the linear sum of inputs.
    assert np.allclose(
        model.predict(np.array([[0, 0, 0, 0]])),
        np.array([[0]]),
        atol=1,
    )
    assert np.allclose(
        model.predict(np.array([[5, 1, 2, 3]])),
        np.array([[10]]),
        atol=3,
    )
    
    # Verify that the loss decreased.
    assert loss_history[-1] < loss_history[0]


def test_dense_learning_biased_problem():
    """
    Verify that a dense layer can learn a heavily biased problem.
    """

    # Create a model with a single layer.
    model = Model(3)
    model.add(Dense(2, activation=Sigmoid()))
    opt = SGD(model.parameters, learning_rate=0.2)
    
    # Create a dataset of inputs and outputs.
    data = [
        (np.array([[0, 0, 0]]), np.array([[0, 1]])),
        (np.array([[0, 0, 1]]), np.array([[0, 1]])),
        (np.array([[0, 1, 0]]), np.array([[0, 1]])),
        (np.array([[0, 1, 1]]), np.array([[0, 1]])),
        (np.array([[1, 0, 1]]), np.array([[0, 1]])),
    ]

    # Train the model.
    loss_history = model.fit(data, opt, batch_size=1, num_epochs=40, verbose=True)

    # Verify it
    assert np.allclose(
        model.predict(np.array([[1, 1, 1]])),
        np.array([[0, 1]]),
        atol=0.15,
    )
    assert loss_history[-1] < loss_history[0]


