import numpy as np
from affogato.model import Model
from affogato.layer import Deconvolution
from affogato.optimizer import SGD


def test_deconvolution_backward_simple():
    """
    Test the backward pass of a simple deconvolution layer.

    Simplest case imaginable:
    1 input channel, 1 output channel, 1x1 kernal.
    Learn an identity problem.
    """

    input_shape = (1, 10, 10, 1)
    def pair(x):
        return (x, x)
    data = [
        pair(np.random.uniform(size=input_shape))
        for _ in range(10)
    ]
    test = np.random.uniform(size=input_shape)

    model = Model(input_shape)
    model.add(Deconvolution(1, 1))
    opt = SGD(model.parameters, 1)
    
    loss_history = model.fit(data, opt, verbose=True, batch_size=1)
    print(f"{model.layers[0].filters = }")

    print("Model predictions:")
    print(model.predict(test))
    print("Actual:")
    print(test)

    assert loss_history[0] > loss_history[-1]
    assert np.allclose(model.predict(test), test, atol = 1e-2)
