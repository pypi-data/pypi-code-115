from affogato.optimizer import SGD
import numpy as np
import pickle as pk
from affogato.model import Model, test_model_by_classes, graph_loss_history
from affogato.layer import Convolution, Dense, Dropout, Flatten
from affogato.activation import ReLU, Sigmoid, Softmax
from affogato.data import labeled_image_directory, numpy_file, image_file_to_array
import os.path
from matplotlib import pyplot as plt
MODEL_PATH = "model_mnist2.pickle"
DATA_SET = "mnist_training.npz"


def predict_image_sample(data, model):
    """
    shows an image and gives it to the model for prediction
    """
    plt.style.use('default')
    fig, axes = plt.subplots(1, 2)

    axes[0].imshow(data.reshape(28,28,1), interpolation='nearest')
    axes[0].title.set_text("predicted " + str(np.argmax(model.predict(data))))
    vals = [x for x in model.predict(data)[0]]
    
    axes[1].title.set_text("model predictions:")
    axes[1].bar([str(x) for x in range(len(vals))] ,vals)
    plt.show()


def main():
    # load the dataset
    dataset_path = DATA_SET
    scaled_data = numpy_file(dataset_path)
    
    # Scale the data to the range of [0, 1]
    # scaled_data = []
    # for sample in data:
    #     scaled_data.append((np.array(sample[0]/255), sample[1]))

    if not os.path.isfile(MODEL_PATH):
        # create a model with input shape as the images in the dataset
        model = Model((1, 28, 28, 1))
        model.add(Flatten())
        model.add(Dense(16, Sigmoid()))
        model.add(Dense(16, Sigmoid()))
        model.add(Dense(10, Softmax()))
        model.compile()

        loss_history = model.fit(scaled_data, num_epochs=20, verbose=True, optimizer=SGD(model.parameters, 0.05))
        
        # Save the model to a .pickle file
        with open(MODEL_PATH, "wb") as file:
            pk.dump((model, loss_history), file)

    else:
        with open(MODEL_PATH, "rb") as file:
            model, loss_history = pk.load(file)
    
    # graph the loss history
    graph_loss_history(loss_history)

    # test the model by classes
    test_model_by_classes(model, scaled_data)
    
    # the user can input images for prediction
    while True:
        path = input()
        predict_image_sample(image_file_to_array(path,True), model)

if __name__ == "__main__":
    main()
