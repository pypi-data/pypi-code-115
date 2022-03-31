import numpy as np
from affogato.layer import Dropout


def test_dropout_layer():
    """
    Verify that a dropout layer drops inputs and also drops output errors
    """

    dropout = Dropout(0.5)
    dropout.compile((1, 10))
    inp = np.array([[1, 5, -1, 4, -2, 2, 1, -3, -1, -2]])

    # Verify that the dropout layer drops inputs.
    assert any(0 in dropout.forward(inp) for _ in range(100))

    # Verify that the dropout layer drops output errors.
    output = dropout.forward(inp)
    outp_err = np.array([[2, -1, 8, -3, 5, -1, -1, -1, -1, -1]])
    inp_err = dropout.backward(outp_err)
    assert all(o == e for o, e in zip(output[0], inp_err[0]) if o == 0 or e == 0)

