from affogato.activation import Sigmoid
import numpy as np
from affogato.model import Model
from affogato.layer import Convolution, Dense, Flatten


def test_convolution_forward_simple():
    """
    Test the forward pass of a simple convolution layer.
    1 input channel and 1 output channel.
    """

    # Edge detection filter
    filter = np.array([[[[1], [0], [-1]] ,
                        [[2], [0], [-2]] ,
                        [[1], [0], [-1]]]])

    # Input/output data of 10x10 image
    input_image = np.array([[[[0], [0], [0], [0], [0], [0], [0], [0], [0], [0]],
                             [[0], [0], [0], [0], [0], [0], [0], [0], [0], [0]],
                             [[0], [0], [1], [0], [0], [0], [0], [0], [0], [0]],
                             [[0], [0], [1], [0], [0], [0], [0], [0], [0], [0]],
                             [[0], [0], [1], [1], [0], [0], [0], [0], [0], [0]],
                             [[0], [0], [0], [1], [0], [0], [0], [0], [0], [0]],
                             [[0], [0], [0], [1], [1], [0], [0], [0], [0], [0]],
                             [[0], [0], [0], [1], [1], [0], [0], [0], [0], [0]],
                             [[0], [0], [0], [0], [1], [1], [1], [1], [0], [0]],
                             [[0], [0], [0], [0], [1], [0], [0], [0], [0], [0]]]])
    output_image = np.array([[[[-1], [0], [1], [0], [0], [0], [0], [0]],
                              [[-3], [0], [3], [0], [0], [0], [0], [0]],
                              [[-4], [-1], [4], [1], [0], [0], [0], [0]],
                              [[-3], [-3], [3], [3], [0], [0], [0], [0]],
                              [[-1], [-4], [0], [4], [1], [0], [0], [0]],
                              [[0], [-4], [-3], [4], [3], [0], [0], [0]],
                              [[0], [-3], [-4], [2], [3], [0], [1], [1]],
                              [[0], [-1], [-4], [-1], [2], [0], [2], [2]]]])

    # Create a convolution layer and set edge detection filter
    conv = Convolution(3)
    conv.compile((1, 10, 10, 1))
    np.copyto(conv.filters.values[0], filter)

    output = conv.forward(input_image)
    print(f"{output.reshape((1, 8, 8)) = }")
    assert output.shape == (1, 8, 8, 1)
    assert np.array_equal(output, output_image)

def test_convolution_backward_simple():
    """
    Test the backward pass of a simple convolution layer.
    1 input channel and 1 output channel.
    """

    # Input/output data of 5x5 image
    input_image = np.array([[[[0], [0], [0], [0], [0]],
                             [[0], [0], [0], [0], [0]],
                             [[0], [0], [0], [0], [0]],
                             [[0], [0], [1], [0], [0]],
                             [[0], [0], [0], [0], [0]]]])
    output_image = np.array([[[[0], [0], [0]],
                              [[0], [0], [0]],
                              [[0], [1], [0]]]])
    data = [(input_image, output_image)]

    # Create a convolution layer and teach it a little
    model = Model((1, 5, 5, 1))
    model.add(Convolution(3))
    model.compile()
    loss_history = model.fit(data, num_epochs=10, verbose=True)
    # Check that the loss decreased
    assert loss_history[-1] < loss_history[0]

def test_convolution_backward_simple_2():
    """
    Test the backward pass of a simple convolution layer.
    1 input channel and 1 output channel.
    """

    # Input/output data of 10x10 image
    input_image = np.array([[[[0], [0], [0], [0], [0], [0], [0], [0], [0], [0]],
                             [[0], [0], [0], [0], [0], [0], [0], [0], [0], [0]],
                             [[0], [0], [1], [0], [0], [0], [0], [0], [0], [0]],
                             [[0], [0], [1], [0], [0], [0], [0], [0], [0], [0]],
                             [[0], [0], [1], [1], [0], [0], [0], [0], [0], [0]],
                             [[0], [0], [0], [1], [0], [0], [0], [0], [0], [0]],
                             [[0], [0], [0], [1], [1], [0], [0], [0], [0], [0]],
                             [[0], [0], [0], [1], [1], [0], [0], [0], [0], [0]],
                             [[0], [0], [0], [0], [1], [1], [1], [1], [0], [0]],
                             [[0], [0], [0], [0], [1], [0], [0], [0], [0], [0]]]])
    output_image = np.array([[[[-1], [0], [1], [0], [0], [0], [0], [0]],
                              [[-3], [0], [3], [0], [0], [0], [0], [0]],
                              [[-4], [-1], [4], [1], [0], [0], [0], [0]],
                              [[-3], [-3], [3], [3], [0], [0], [0], [0]],
                              [[-1], [-4], [0], [4], [1], [0], [0], [0]],
                              [[0], [-4], [-3], [4], [3], [0], [0], [0]],
                              [[0], [-3], [-4], [2], [3], [0], [1], [1]],
                              [[0], [-1], [-4], [-1], [2], [0], [2], [2]]]])
    data = [(input_image, output_image)]

    # Create a convolution layer and teach it a little
    model = Model((1, 10, 10, 1))
    model.add(Convolution(3))
    model.compile()
    loss_history = model.fit(data, num_epochs=10, verbose=True)
    # Check that the loss decreased
    assert loss_history[-1] < loss_history[0]

