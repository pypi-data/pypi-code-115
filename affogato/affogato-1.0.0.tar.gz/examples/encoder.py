from affogato.model import Model, EncoderTrainer, graph_loss_history, OutputAnimator
from affogato.data import numpy_file
from affogato.layer import Dense, Flatten, Reshape, Dropout
from affogato.activation import ReLU, Sigmoid, Softmax
from affogato.loss import CrossEntropy
from affogato.optimizer import Adam
from pathlib import Path
import pickle
import matplotlib.pyplot as plt
import random


if __name__ == '__main__':
    model_path = Path(__file__).parent / "encoder.pickle"
    data_path = Path(__file__).parent / "mnist_training.npz"
    create_new_model = "y" in input("Create new model? [y/N]: ").lower() if model_path.exists() else True
    skip_training = "y" in input("Skip training? [y/N]: ").lower() if not create_new_model else False

    # Load data
    data = numpy_file(str(data_path))

    # scale data and remove labels
    print("Scaling data...")
    data = [ inp / 255 for inp, _ in data ]

    # Load/Create model
    encoder, decoder = None, None
    if model_path.exists() and not create_new_model:
        print("Loading saved model...")
        with open(model_path, "rb") as f:
            encoder, decoder = pickle.load(f)
    else:
        print("Creating new model...")
        latent_dim = 4

        encoder = Model((1, 28, 28, 1))
        encoder.add(Flatten())
        encoder.add(Dense(200, activation=ReLU(leak=0.02)))
        encoder.add(Dropout(0.95))
        encoder.add(Dense(latent_dim, activation=Sigmoid()))
        encoder.compile()

        decoder = Model((1, latent_dim))
        decoder.add(Dense(200, activation=ReLU(leak=0.02)))
        decoder.add(Dense(784, activation=Sigmoid()))
        decoder.add(Reshape((1, 28, 28, 1)))
        decoder.compile()


    # Train model
    if not skip_training:
        print("Beginning training...")
        trainer = EncoderTrainer(
                encoder, decoder,
                Adam(encoder.parameters),
                Adam(decoder.parameters),
                loss_function=CrossEntropy(),
                )
        with OutputAnimator(trainer):
            trainer.train(data, verbose=True, num_epochs=40)
        graph_loss_history(trainer.loss_history)

        print("Saving model...")
        with open(model_path, "wb+") as f:
            pickle.dump((encoder, decoder), f)

    # pick an input and output and show
    images = 7
    fig, axes = plt.subplots(2, images)
    for i in range(images):
        inp = random.choice(data)
        out = decoder.predict(encoder.predict(inp))
        axes[0][i].imshow(inp[0, :, :, 0], cmap="gray")
        axes[1][i].imshow(out[0, :, :, 0], cmap="gray")
    plt.show()

