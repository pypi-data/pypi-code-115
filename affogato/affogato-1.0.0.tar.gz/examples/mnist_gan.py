from affogato.activation import ReLU, Sigmoid
from affogato.layer import Deconvolution, Dense, Dropout, Flatten, Reshape
from affogato.loss import MeanSquaredError
from affogato.model import GANTrainer, Model, OutputAnimator, LossAnimator
import affogato.data as data
from affogato.optimizer import SGD
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
import multiprocessing
import os
import pickle as pk

MODEL_PATH_GEN = "gen_mnist5.pickle"
MODEL_PATH_DISC = "disc_mnist5.pickle"


def predict_sample(data):
    """
    shows an image and gives it to the model for prediction
    """
    plt.style.use("grayscale")
    plt.imshow(data.reshape(28,28,1), interpolation='nearest')
    plt.colorbar()
    plt.show()


def create_discriminator():
    model = Model((1, 28, 28, 1))
    # model.add(Convolution(4, 6))
    # model.add(Convolution(5, 16))
    model.add(Flatten())
    model.add(Dense(12, ReLU()))
    model.add(Dropout(0.8))
    model.add(Dense(12, ReLU()))
    model.add(Dropout(0.8))
    model.add(Dense(1, Sigmoid()))
    return model


def create_generator():
    model = Model(100)
    model.add(Dense(32, ReLU()))
    model.add(Dense(16, ReLU()))
    model.add(Reshape((1, 4, 4, 1))) # TODO: add a layer to reshape the vector into a 2d matrix
    model.add(Deconvolution(18, 3))
    model.add(Deconvolution(8, activation=Sigmoid()))

    return model


def create_complex_generator():
    model = Model(100)
    model.add(Dense(256, ReLU()))
    model.add(Dense(512, ReLU()))
    model.add(Dense(16, ReLU()))
    model.add(Reshape((1, 4, 4, 1))) # TODO: add a layer to reshape the vector into a 2d matrix
    # model.add(Deconvolution(9, 3))
    model.add(Deconvolution(18, 3))
    model.add(Deconvolution(8, activation=Sigmoid()))
    # model.add(Flatten())
    # model.add(Dense(28*28, Sigmoid()))
    # model.add(Reshape((1, 28, 28, 1))) # TODO: add a layer to reshape the vector into a 2d matrix
    
    return model

def create_complex_discriminator():
    model = Model((1, 28, 28, 1))
    model.add(Flatten())
    model.add(Dense(32, ReLU()))
    model.add(Dropout(0.3))
    model.add(Dense(32, ReLU()))
    model.add(Dropout(0.3))
    model.add(Dense(1, Sigmoid()))
    return model

def live_plot(q: multiprocessing.Queue):
    def animate(i):
        if q.qsize() < 10:
            # print("!")
            pass
            
        else:
            last_image = q.get()
            for _ in range(q.qsize()-2):
                try:
                    last_image = q.get_nowait()
                except:
                    pass
            plt.cla()
            plt.imshow(last_image, cmap='gray')
            # print(q.qsize())

    ani = animation.FuncAnimation(plt.gcf(), animate, interval=0.00001)
    plt.show()



def show_and_save_gif(images):
    fig, ax = plt.subplots()
    plt.style.use("grayscale")
    ims = []
    for i in range(len(images)):
        im = ax.imshow(images[i], animated=True)
        ttl = plt.text(0.5, 1.1, i, horizontalalignment='center', verticalalignment='bottom', transform=ax.transAxes)
        
        if i == 0:
            ax.imshow(images[i])  # show an initial one first
        ims.append([im, ttl])

    ani = animation.ArtistAnimation(fig, ims, interval=50, blit=True,
                                    repeat_delay=1000)
    
    
    plt.show()
    f = r"animation1.gif" 
    writergif = animation.PillowWriter(fps=30) 
    ani.save(f, writer=writergif)
  

def load_or_create_model(path, creation_func, keep=False):
    if not os.path.isfile(path) or not keep:
        model = creation_func()
        
    else:
        with open(path, "rb") as file:
            model = pk.load(file)
    return model


def save_model(model, path):
    # Save the model to a .pickle file
    with open(path, "wb") as file:
        pk.dump((model), file)


def graph_loss(trainer, batch_number):
    disc_loss_combined = [i+j for i,j in zip(trainer.disc_real_loss_history, trainer.disc_fake_loss_history)]
    disc_loss = []
    genartor_loss = []
    batch_number = round(batch_number)

    for i in range(0, len(disc_loss_combined), batch_number):
        
        disc_loss.append(sum(disc_loss_combined[i:i+batch_number])/batch_number)
        genartor_loss.append(sum(trainer.gen_loss_history[i:i+batch_number])/batch_number)
    plt.style.use("default")
    plt.plot(genartor_loss)
    plt.plot(disc_loss)
    plt.legend(labels=["gen", "disc_fake", "disc_real"])
    plt.show()


def main():
    scaled_data = [ inp for inp, label in data.numpy_file("mnist_testing.npz") ]

    gen = load_or_create_model(MODEL_PATH_GEN, create_generator)
    disc = load_or_create_model(MODEL_PATH_DISC, create_discriminator)

    trainer = GANTrainer(
        gen, disc,
        SGD(gen.parameters,0.05), SGD(disc.parameters, 0.008),
        MeanSquaredError(),
    )
    batch_size = 32


    with OutputAnimator(trainer):
        with LossAnimator(trainer):
            trainer.train(scaled_data, batch_size=batch_size, verbose=True, num_epochs=2000)

    # Save the models after raining
    save_model(gen, MODEL_PATH_GEN)
    save_model(disc, MODEL_PATH_DISC)

    # Graph the loss of the GAN
    # TODO: add it to the gan trainer!
    batch_number = len(scaled_data) / batch_size
    graph_loss(trainer, batch_number)

    for _ in range(4):
        fig, axs = plt.subplots(3, 3)
        for i in range(3):
            for j in range(3):
                noise = np.random.normal(size=(1,) + gen.input_shape[1:])
                
                plt.style.use("grayscale")
                axs[i, j].imshow(gen.predict(noise).reshape(28,28,1), interpolation='nearest')
                # plt.colorbar()
        plt.show()

    noise = np.random.normal(size=(1,) + gen.input_shape[1:])
    print("finished")


if __name__ == "__main__":
    main()
    
