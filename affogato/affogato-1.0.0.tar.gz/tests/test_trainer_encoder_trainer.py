import numpy as np
from affogato.model import Model, EncoderTrainer
from affogato.layer import Dense, Convolution, Flatten, Reshape
from affogato.activation import Linear, ReLU, Sigmoid
from affogato.optimizer import SGD, Adam


def test_trivial_encoder():
    inputs = [
        np.random.rand(1, 1)
        for _ in range(128)
    ]

    enc = Model(1)
    enc.add(Dense(1))
    enc.compile()

    dec = Model(1)
    dec.add(Dense(1))
    dec.compile()

    trainer = EncoderTrainer(enc, dec, SGD(enc.parameters), SGD(dec.parameters))
    trainer.train(inputs, num_epochs=20, verbose=True)

    assert trainer.loss_history[0] > trainer.loss_history[-1], "Loss did not decrease"
    assert trainer.loss_history[-1] < 1e-1, "Models did not converge"
    x = np.random.rand(1, 1)
    assert np.allclose(
        x,
        trainer.decoder.predict(trainer.encoder.predict(x)),
        atol=1e-1,
    ), "Encoder and decoder do not match"


def test_():
    # Data of some lines on 5x5 grid
    data = [
        np.array([[[[0], [1], [0], [0], [0]],
                   [[0], [1], [0], [0], [0]],
                   [[1], [0], [0], [0], [0]],
                   [[1], [0], [0], [0], [0]],
                   [[1], [0], [0], [0], [0]]]]),

        np.array([[[[0], [1], [0], [0], [0]],
                   [[0], [1], [1], [1], [1]],
                   [[0], [0], [0], [0], [0]],
                   [[0], [0], [0], [0], [0]],
                   [[0], [0], [0], [0], [0]]]]),

        np.array([[[[0], [0], [0], [0], [0]],
                   [[0], [0], [0], [0], [0]],
                   [[1], [1], [1], [1], [1]],
                   [[1], [0], [0], [0], [0]],
                   [[1], [0], [0], [0], [0]]]]),

        np.array([[[[0], [0], [1], [0], [0]],
                   [[0], [0], [1], [0], [0]],
                   [[0], [1], [1], [1], [1]],
                   [[0], [0], [1], [0], [0]],
                   [[0], [0], [1], [0], [0]]]]),

        np.array([[[[0], [0], [1], [0], [0]],
                   [[0], [0], [1], [0], [0]],
                   [[0], [1], [1], [1], [1]],
                   [[0], [0], [1], [0], [0]],
                   [[0], [0], [1], [0], [0]]]]),

        np.array([[[[0], [0], [1], [0], [0]],
                   [[0], [0], [1], [0], [0]],
                   [[0], [0], [1], [1], [1]],
                   [[0], [0], [1], [0], [0]],
                   [[0], [0], [1], [0], [0]]]]),

        np.array([[[[0], [0], [1], [0], [0]],
                   [[0], [0], [1], [0], [0]],
                   [[0], [0], [1], [0], [0]],
                   [[0], [0], [0], [1], [1]],
                   [[0], [0], [0], [0], [0]]]]),

        np.array([[[[0], [1], [1], [1], [0]],
                   [[0], [0], [0], [0], [0]],
                   [[0], [0], [0], [0], [0]],
                   [[0], [0], [1], [0], [0]],
                   [[0], [0], [1], [0], [0]]]]),
    ]

    encoder = Model((1, 5, 5, 1))
    encoder.add(Convolution(3))
    encoder.add(Flatten())
    encoder.add(Dense(15, activation=ReLU()))
    encoder.compile()
    
    decoder = Model(15)
    decoder.add(Dense(10, activation=Sigmoid()))
    decoder.add(Dense(25, activation=Sigmoid()))
    decoder.add(Reshape((1, 5, 5, 1)))
    decoder.compile()

    trainer = EncoderTrainer(encoder, decoder, Adam(encoder.parameters, 0.05), Adam(decoder.parameters, 0.05))
    trainer.train(data, batch_size=4, num_epochs=80, verbose=True)

    assert trainer.loss_history[0] > trainer.loss_history[-1], "Loss did not decrease"
    print(decoder.predict(encoder.predict(data[0])))
    assert trainer.loss_history[-1] < 1e-1, "Models did not converge"

