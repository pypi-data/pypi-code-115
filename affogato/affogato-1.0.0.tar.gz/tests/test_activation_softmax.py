import numpy as np
from affogato.activation import Softmax, ReLU
from affogato.optimizer import SGD
from affogato.model import Model
from affogato.layer import Dense
from affogato.loss import MultiCrossEntropy


def test_softmax_output_is_normalized():
    """ Run softmax on some inputs and check that the output is normalized. """
    softmax = Softmax()
    for i in range(10):
        size = np.random.randint(1, 21)
        input_data = np.random.randint(-100, 100, size=(1, size))
        output = softmax(input_data)
        assert np.isclose(output.sum(), 1.0)
    

def test_softmax_cross_entropy_loss():
    """ Test the softmax with mutli-cross-entropy loss on some simple data """
    data = [
        (np.array([[0, 0]]), np.array([[1, 0, 0, 0]])),
        (np.array([[1, 0]]), np.array([[0, 1, 0, 0]])),
        (np.array([[0, 1]]), np.array([[0, 0, 1, 0]])),
        (np.array([[1, 1]]), np.array([[0, 0, 0, 1]])),
    ]
    model = Model(2)
    model.add(Dense(15, activation=ReLU()))
    model.add(Dense(4, activation=Softmax()))
    model.compile()
    opt = SGD(model.parameters, 0.2)
    loss_history = model.fit(data, opt, batch_size=3, num_epochs=30, loss=MultiCrossEntropy(), verbose=True)

    assert loss_history[0] > loss_history[-1], "Loss should decrease"
    assert loss_history[-1] < 0.1, "Model did not converge"
    for inp, label in data:
        assert np.allclose(
            model.predict(inp),
            label,
            rtol=0.2,
            atol=0.2,
        ), "Prediction is incorrect"

