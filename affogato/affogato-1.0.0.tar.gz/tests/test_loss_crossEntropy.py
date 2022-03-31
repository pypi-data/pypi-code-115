from affogato.loss import CrossEntropy
import numpy as np


def test_functionallity():
    loss = CrossEntropy()

    target = np.array([[1., 0.]])
    actual = np.array([[0.999999, 0.000001]])
    assert np.allclose(loss(actual, target), 0., atol=1e-4)


def test_boundaries():
    loss = CrossEntropy()

    inp = np.array([[1., 0.]])
    assert np.allclose(loss(inp, inp), 0., atol=1e-6)


def test_gradient():
    loss = CrossEntropy()

    target = np.array([[1., 0.]])
    actual = np.array([[0.999999, 0.000001]])
    loss(actual, target)
    assert np.allclose(loss.derivative(), np.array([[-1., 1.]]), atol=1e-6)


def test_and_problem_cross_entropy():
    from affogato.model import Model
    from affogato.layer import Dense
    from affogato.optimizer import SGD
    from affogato.activation import Sigmoid

    # Create a model
    model = Model(2)
    model.add(Dense(1, activation=Sigmoid()))
    model.compile()
    opt = SGD(model.parameters, learning_rate=1.5)

    data = [
        (np.array([[0., 0.]]), np.array([[0.]])),
        (np.array([[0., 1.]]), np.array([[0.]])),
        (np.array([[1., 0.]]), np.array([[0.]])),
        (np.array([[1., 1.]]), np.array([[1.]])),
    ]
    
    # Train it
    loss_history = model.fit(data, opt, loss=CrossEntropy(), num_epochs=40, batch_size=1)

    # Check the loss
    assert loss_history[-1] < loss_history[0]
    # Check the accuracy
    for (x, y) in data:
        assert np.allclose(model.predict(x), y, atol=0.1)

if __name__ == "__main__":
    test_functionallity()
