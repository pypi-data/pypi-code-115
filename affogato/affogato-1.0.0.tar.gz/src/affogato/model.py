from tqdm import tqdm
from typing import Iterable, List, Tuple, Union, Optional, Callable
from multiprocessing import Process, Queue
import numpy as np
import random 
import pickle
from affogato.layer import Dropout, Layer, Parameters
from affogato.loss import Loss, MeanSquaredError
from affogato.optimizer import SGD, Adam, Optimizer
import matplotlib.pyplot as plt
import matplotlib.animation as anim


class Model:
    """
    Represents a model that's built out of connected layers. It handles the fitting of the indevitual layers,
    as well as predicting and feedfarwarding through the layers. It olso keeps track of the Parameters of each layer.

    In order to use a model you need to `compile()` it. Compiling the model creates the trainable parameters for each layer.
    The input of the model is entered in its creation. 

    The main way to fit the model is using the `fit()` method. It is responsible of keeping track of the gradients of each paremeter
    and adjust it using the chosen optimizer.

    Example:
    -------
    First we need to import all the relevent modules.
    >>> import numpy as np
    >>> from affogato.activation import ReLU, Sigmoid
    >>> from affogato.layer import Dense
    >>> from affogato.optimizer import SGD
    >>> from affogato.model import Model

    Let's create a model that is capable of learning the XOR logical gate.
    >>> # Create a `Model` and add a Dense layer as the first layer.
    >>> # Note: you need to give the input shape to the model at creation. 
    >>> # After that, there is no need to enter the input shape for each layer.
    >>> model = affogato.model.Model((1, 2))
    >>> model.add(Dense(2, ReLU())) 
    >>> # Now the model will take as input arrays of shape (1, 2)
    >>> # and output arrays of shape (1, 2).
    >>> # The activation function will be Relu, but it can be anything that derives from `affogato.activaion.Activation()`
    >>> model.add(Dense(1, Sigmoid())) 
    >>> # the last layer of the model will be the output layer of the model. 
    >>> #Note: the output size of the model must mach the label size.
    >>> model.compile()
    >>> # Note: after we created the model, we need to compile it in order to use it.

    Now let's make some data for our model to learn.
    >>> data = [
        (np.array([[0., 1.]]), np.array([[1.]])),
        (np.array([[1., 0]]), np.array([[1.]])),
        (np.array([[1., 1.]]), np.array([[0.]])),
        (np.array([[0., 0.]]), np.array([[0.]])),
        
    ]

    To train the model we use the `fit()` method.
    >>> # At first we need to create an optimizer for our model.
    >>> # the default optimizer has a learning rate that is not suited for our purpose.
    >>> # So we create an SGD optimizer, with a better learning rate of 0.05.
    >>> # A good (or good enough) learning rate must be discovered via trial and error, there is no formula to decide which LR to use before testing.
    >>> opt = SGD(model.parameters, learning_rate=0.05) 
    >>> # We give the data and the optimizer to the fitting process, as well as the number of epochs to go through.
    >>> # The function then fits the model to the data, and returns the loss history of the model.
    >>> loss_history = model.fit(data, opt, verbose=True, num_epochs=2000)

    Now the model is trained and can be used:
    >>> # We use the `predict()` method to pass data without backpropagation.
    >>> print(f"{model.predict(data[1][0]):} true:", data[1][1])

    Parameters:
    ----------
    input_shape: Union[tuple[int, ...], int]
        the input shape of the model.
    """
    layers: List[Layer]
    parameters: List[Parameters]
    input_shape: tuple[int, ...]
    
    def __init__(self, input_shape: Union[tuple[int, ...], int]):
        self._compiled = False
        self.input_shape = input_shape if isinstance(input_shape, tuple) else (1, input_shape)
        self.layers = []
        self.parameters = []

    def add(self, layer: Layer) -> None:
        """
        Connects a layer after the last added one - either the previous
        layer will be connected to it, or the input if there an no layers
        """
        if self._compiled:
            raise RuntimeError("Cannot add a new layer to a compiled model. Please, add the layer before compiling.")
        self.layers.append(layer)       

    def compile(self):
        """
        Compiles the model and connects the layers to the optimizer.

        Required before calling the `fit` method.
        """
        previous_layer_output_shape = self.input_shape
        for layer in self.layers:
            previous_layer_output_shape = layer.compile(previous_layer_output_shape)
            self.parameters.extend(layer.get_parameters())
        
        self._compiled = True
    
    def predict(self, input: np.ndarray) -> np.ndarray:
        """ Predict the output of the model for the given input. """
        if not self._compiled:
            self.compile()

        X = input
        for layer in self.layers:  X = layer.forward(X) if layer is not Dropout else X 
        return X

    def forward(self, inp: np.ndarray) -> np.ndarray:
        """ Forward pass of the model. Same as `.predict(inp)` """
        return self.predict(inp)
            
    def backward(self, output_delta: np.ndarray) -> np.ndarray:
        """
        Teaches the model based on output delta of the last input.
        This is usually the derivative of a loss function for the last output.

        Must be called after `forward`.

        Parameters
        ----------
        output_delta : np.ndarray
            The output delta of the last input given to the model.

        Returns
        -------
        np.ndarray
            The delta of the original input.
        """

        delta = output_delta
        for layer in reversed(self.layers):
            delta = layer.backward(delta)

        return delta

    def fit(self, data: Iterable[Tuple[np.ndarray, np.ndarray]],
            optimizer: Optimizer = None,
            loss: Loss = MeanSquaredError(),
            batch_size: int = 32, num_epochs: int = 10,
            verbose: bool = False) -> List[float]:
        """
        Train the model on the given data.

        Parameters
        ----------
        data: Iterable[Tuple[np.ndarray, np.ndarray]]
            A list of tuples of the form (input, target)

        optimizer: Optimizer. Default: SGD
            The optimizer is the algorithm used to update the weights
            of the model.

        loss: Loss. Default: MeanSquaredError
            The loss function used to calculate the error of the model.
            In some cases, a cross entropy loss function is preferred.

        batch_size: int. Default: 32
            The batch size is the number of samples that are used to update
            the weights

        num_epochs: int. Default: 10
            The number of epochs is the number of times the whole dataset is

        verbose: bool. Default: False
            If True, the progress of the training is shown in the terminal
            used to update the weights

        Returns
        -------
        List[np.ndarray]
            A list of the losses for each batch in order.
        """

        optimizer = SGD(self.parameters) if optimizer is None else optimizer
        
        trainer = SingleModelTrainer(self, optimizer, loss)
        trainer.train(data, batch_size, num_epochs, verbose)
        return trainer.loss_history


class Trainer():
    """
    An abstract base class responsible for training a model.

    The `SingleModelTrainer` class is sufficiant for most tasks.
    Derive from this class to implement your own training algorithm.

    In general, pickling a `Trainer` object is fine and common practice, but
    some behaviors (that use the `on_batch_end` or `on_epoch_end` hooks)
    will not work. For example, pickling a `TrainerAnimator` will break it.
    """

    on_batch_end: List[Callable[[], None]]
    on_epoch_end: List[Callable[[], None]]

    def __init__(self):
        self.on_batch_end = []
        self.on_epoch_end = []

    def train(self, data: Union[Iterable[np.ndarray], Iterable[Tuple[np.ndarray, np.ndarray]]],
              batch_size: int = 32, num_epochs: int = 10,
              verbose: bool = False,
              checkpoint_path: Optional[str] = None,
              checkpoint_epoch_interval: int = 1,
              ) -> None:
        """
        Run the training algorithm on the given data.

        Parameters
        ----------
        data: Iterable[np.ndarray] or Iterable[Tuple[np.ndarray, np.ndarray]]
            A list of tuples of the form (input, target) or just (input)
            Wether the target is given or not depends on the subclass.

        batch_size: int. Default: 32
            The batch size is the number of samples that are used to update
            the weights at once.
            Bigger batches are faster and more consistent, but too big will lead
            to bad training.

        num_epochs: int. Default: 10
            The number of epochs is the number of times the whole dataset is
            used to update the weights.

        checkpoint_path: str. Default: None
            If given, the model is saved to the given path every
            `checkpoint_epoch_interval` epochs.

        checkpoint_epoch_interval: int. Default: 1
            Defines how often checkpoints should be made. Only relevent if
            `checkpoint_path` is given.

        verbose: bool. Default: False
            If True, the progress of the training is shown in the terminal
            used to update the weights.
        """
        from sys import stdout

        # Clone the data to a list because we will be shuffling it
        shuffled_data = [ x if isinstance(x, tuple) else (x,) for x in data ]

        for epoch in range(num_epochs):
            random.shuffle(shuffled_data)

            # Create a progress bar
            batches = tqdm(
                    self.get_batches(shuffled_data, batch_size),
                    desc=f"epoch {epoch+1:0{len(str(num_epochs))}}/{num_epochs}",
                    disable=not verbose,
                    file=stdout
                )

            for batch in batches:
                inp, out = (batch + (None,))[:2] # Hack to give out None if tuple is 1
                message = self.train_batch(inp, out)
                
                # Verbosity
                batches.set_postfix_str(message)

                for on_batch_end in self.on_batch_end:
                    on_batch_end()

            # Checkpointing
            if checkpoint_path is not None and (epoch + 1) % checkpoint_epoch_interval == 0:
                self.save(checkpoint_path)

            for on_epoch_end in self.on_epoch_end:
                on_epoch_end()

    def train_batch(self, inp: np.ndarray, expected: Optional[np.ndarray] = None,
                    ) -> str:
        """
        Train the model on the given batch.

        Parameters
        ----------
        inp: np.ndarray
            The input batch.

        expected: np.ndarray, optional
            The expected output batch.
            Certain training algorithms require this and certain dont.

        verbose: bool. Default: False
            If True, certain information is printed to the terminal.

        Returns
        -------
        str
            A message that will be printed to the terminal by .train().
        """
        raise NotImplementedError("The `train_batch` method must be implemented in a subclass.")

    def get_batches(self, shuffled_data: List[Tuple[np.ndarray, ...]],
                    batch_size: int) -> List[Tuple[np.ndarray, ...]]:
        """
        Get batches of data from the given data.

        Parameters
        ----------
        shuffled_data: List[Tuple[np.ndarray, ...]]
            The data to get the batch from.

        batch_size: int
            The size of the batch.

        Returns
        -------
        List[Tuple[np.ndarray, ...]]
            The batches of data.
        """

        ret = []
        for i in range(0, len(shuffled_data), batch_size):
            # Use zip(* ...) to unzip the data
            arrays_iter = zip(*shuffled_data[i:i+batch_size])
            
            # Concatenate the arrays into a single array
            ret.append(tuple(np.concatenate(arrays) for arrays in arrays_iter))

        return ret

    def save(self, path: str) -> None:
        """
        Save the model to the given path.

        This saves the current state of the trainer in a pickle file.
        To load again, use the `pickle` module from the standard library to load
        the trainer again.

        Parameters
        ----------
        path: str
            The path to save the model to.
        """
        with open(path, "wb") as f:
            pickle.dump(self, f)

    def __getstate__(self):
        state = self.__dict__.copy()
        # Don't pickle hooks
        del state["on_batch_end"]
        del state["on_epoch_end"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Add hooks
        self.on_batch_end = []
        self.on_epoch_end = []


def graph_loss_history(loss_history: List[float], loss_function: Optional[Loss] = None):
    plt.style.use('ggplot')
    plt.plot(loss_history)
    plt.title("Loss History")
    plt.xlabel("epoch index")
    plt.ylabel(f"loss({type(loss_function)})" if loss_function is not None else f"loss")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


class SingleModelTrainer(Trainer):
    """
    Trains a single model with a single optimizer and loss function.

    This class trains a model on the given input and expected output.
    (So target must be given when calling `train`.)
    """

    model: Model
    optimizer: Optimizer
    loss_function: Loss

    loss_history: List[float]

    def __init__(self, model: Model, optimizer: Optimizer, loss_function: Loss):
        """
        Parameters
        ----------
        model: Model
            The model to train.

        optimizer: Optimizer
            The optimizer to use. Should have the parameters already passed in.

        loss_function: Loss
            The loss function to use.
        """
        super().__init__()

        self.model = model
        self.optimizer = optimizer
        self.loss_function = loss_function
        self.loss_history = []

    def train_batch(self, inp: np.ndarray, expected: Optional[np.ndarray] = None,
                    ) -> str:

        if expected is None:
            raise ValueError("Expected output must be given to `SingleModelTrainer`.")
        
        # Clear data between runs
        self.optimizer.clear_backward_data()

        output = self.model.forward(inp)
        loss = self.loss_function(output, expected)
        loss_deriv = self.loss_function.derivative()
        self.model.backward(loss_deriv)

        # Learn from the batch
        self.optimizer.adjust_parameters()

        self.loss_history.append(loss)
        return f"loss: {loss:.2e}"

    def graph_loss_history(self):
        graph_loss_history(self.loss_history, self.loss_function)


class GANTrainer(Trainer):
    gen: Model
    disc: Model
    gen_optimizer: Optimizer
    disc_optimizer: Optimizer
    loss_function: Loss

    gen_loss_history: List[float]
    disc_real_loss_history: List[float]
    disc_fake_loss_history: List[float]
    last_output: np.ndarray

    def __init__(self, gen: Model, disc: Model,
                 gen_optimizer: Optimizer, disc_optimizer: Optimizer,
                 loss_function: Loss):
        super().__init__()
        self.disc = disc
        self.gen = gen
        self.gen_optimizer = gen_optimizer
        self.disc_optimizer = disc_optimizer
        self.loss_function = loss_function

        self.gen_loss_history = []
        self.disc_real_loss_history = []
        self.disc_fake_loss_history = []

    def train_batch(self, inp: np.ndarray, expected: Optional[np.ndarray] = None,
                    ) -> str:

        if expected is not None:
            raise ValueError("Expected output must not be given to `GANTrainer`.")

        batch_size = inp.shape[0]

        # Clear data between runs
        self.gen_optimizer.clear_backward_data()
        self.disc_optimizer.clear_backward_data()

        # Generate fake data
        noise = np.random.normal(size=(batch_size,) + self.gen.input_shape[1:])
        fake_inp = self.gen.forward(noise)
        fake_expected = np.full((batch_size, 1), 0.95) # Not everything!
        # TODO: label smoothing

        # Train the discriminator on the real data
        disc_out_real = self.disc.forward(inp)
        disc_loss_real = self.loss_function(disc_out_real, np.zeros_like(disc_out_real))
        disc_loss_real_deriv = self.loss_function.derivative()
        self.disc.backward(disc_loss_real_deriv)

        # Train the discriminator on the fake data
        disc_out_fake = self.disc.forward(fake_inp)
        disc_loss_fake = self.loss_function(disc_out_fake, fake_expected)
        disc_loss_fake_deriv = self.loss_function.derivative()
        self.disc.backward(disc_loss_fake_deriv)

        # Adjust it's parameters
        self.disc_optimizer.adjust_parameters()
        
        # Train the generator based on the discriminator's output
        # Get the loss for the same output, with the label switched
        # Then calculate input delta for the discriminator and send to generator
        disc_out_expected = np.zeros((batch_size, 1))
        gen_disc_loss = self.loss_function(disc_out_fake, disc_out_expected)
        gen_disc_loss_deriv = self.loss_function.derivative()
        gen_output_delta = self.disc.backward(gen_disc_loss_deriv)
        self.gen.backward(gen_output_delta)

        # Adjust the generator's parameters
        self.gen_optimizer.adjust_parameters()

        # Save the loss
        self.gen_loss_history.append(gen_disc_loss)
        self.disc_real_loss_history.append(disc_loss_real)
        self.disc_fake_loss_history.append(disc_loss_fake)

        self.last_output = fake_inp

        return f"gen loss = {gen_disc_loss:.2e} disc loss = {disc_loss_fake + disc_loss_real:.2e}"


class EncoderTrainer(Trainer):
    """
    Trains an encoder/decoder pair.

    This class trains two models (an encoder and a decoder) on unlabeled input.
    At the end of training, the encoder can be used to encode the input in less
    data, and the decoder can be fed the encoded data to reconstruct the input.

    Parameters
    ----------
    encoder: Model
        The encoder model.

    decoder: Model
        The decoder model.

    encoder_optimizer: Optimizer. Default: Adam.
        The optimizer to use for the encoder.

    decoder_optimizer: Optimizer. Default: Adam.
        The optimizer to use for the decoder.

    loss_function: Loss. Default: MeanSquaredError.
        The loss function to use for the decoder.
    """
    
    encoder: Model
    decoder: Model
    encoder_optimizer: Optimizer
    decoder_optimizer: Optimizer
    loss_function: Loss

    loss_history: List[float]
    last_output: np.ndarray

    def __init__(self, encoder: Model, decoder: Model,
                 encoder_optimizer: Optional[Optimizer] = None,
                 decoder_optimizer: Optional[Optimizer] = None,
                 loss_function: Loss = MeanSquaredError()):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.encoder_optimizer = encoder_optimizer or Adam(encoder.parameters)
        self.decoder_optimizer = decoder_optimizer or Adam(decoder.parameters)
        self.loss_function = loss_function

        # TODO: Check that encoder's input shape is the same as decoder's output shape
        # and that the decoder's input shape is the same as the encoder's output shape

        self.loss_history = []

    def train_batch(self, inp: np.ndarray, expected: Optional[np.ndarray] = None,
                    ) -> str:

        if expected is not None:
            raise ValueError("Expected output must not be given to `EncoderTrainer`.")

        # Clear data between runs
        self.encoder_optimizer.clear_backward_data()
        self.decoder_optimizer.clear_backward_data()

        # Encode the input
        encoded = self.encoder.forward(inp)

        # Decode the encoded data
        decoded = self.decoder.forward(encoded)

        # Calculate the loss
        loss = self.loss_function(decoded, inp)
        loss_deriv = self.loss_function.derivative()

        # Backpropagate the loss
        encoding_loss = self.decoder.backward(loss_deriv)
        self.encoder.backward(encoding_loss)

        # Adjust the parameters
        self.decoder_optimizer.adjust_parameters()
        self.encoder_optimizer.adjust_parameters()

        self.loss_history.append(loss)
        self.last_output = decoded

        return f"loss: {loss:.2e}"

    def graph_loss_history(self):
        graph_loss_history(self.loss_history, self.loss_function)


def test_model_by_classes(model: Model, test_set: np.ndarray, class_names: list=None):
    class_accuracy = {}
    correct = 0
    for item in test_set:
        predicted_class = np.argmax(model.predict(item[0]))
        actual_class = np.argmax(item[1])

        if  predicted_class == actual_class:
            correct += 1
            if actual_class in class_accuracy.keys():
                class_accuracy[actual_class][0] += 1
                class_accuracy[actual_class][1] += 1

            else:
                class_accuracy[actual_class] = [1, 1]

        else:
            if actual_class in class_accuracy.keys():
                class_accuracy[actual_class][1] += 1
            else:
                class_accuracy[actual_class] = [0, 1]

    accuracy_rate = correct/len(test_set)
    plt.style.use('ggplot')
    # plt.bar([range(len(class_accuracy.items()))], )
    acc = [x[1][0]/x[1][1] for x in class_accuracy.items()]
    print(acc)
    plt.bar(range(len(acc)) if class_names is None else class_names, acc)
    plt.title("Accuracy By Class In The Testset")
    plt.suptitle(f"Over all accuracy: {accuracy_rate}")
    plt.show()


class OutputAnimator:
    """
    Animates the training of a model.

    This class does not work on all trainer. Currently it only supports 
    `EncoderTrainer` and `GANTrainer`. Uses matplotlib to display the training
    progress on a live window.

    Should not be pickled.
    """

    figure: plt.Figure
    animation_process: Process
    outputs_queue: Queue
    trainer: Trainer
    trainer_hook: Callable[[], None]

    def __init__(self, trainer: Trainer) -> None:
        self.animation_process = Process(target=self.begin_animation, args=(), daemon=True)
        self.figure = plt.figure()
        self.outputs_queue = Queue()
        self.trainer = trainer
        self.trainer_hook = self.log_trainer_output

        if not isinstance(trainer, (EncoderTrainer, GANTrainer)):
            raise ValueError("TrainerAnimator only works with EncoderTrainer and GANTrainer.")

    def __enter__(self):
        self.animation_process.start()
        self.trainer.on_batch_end.append(self.trainer_hook)
        return self

    def __exit__(self, type, value, traceback):
        self.trainer.on_batch_end.remove(self.trainer_hook)
        self.animation_process.kill()
        plt.close(self.figure)
        self.outputs_queue.close()
        return True

    def begin_animation(self) -> None:
        def update_animation(frame: int):
            # Get the last image requested for showing, if there is one
            image_to_show = None
            if self.outputs_queue.qsize() > 0:
                for _ in range(self.outputs_queue.qsize()):
                    image_to_show = self.outputs_queue.get()

            # Show the image
            if image_to_show is not None:
                self.figure.clear()
                self.figure.add_subplot(1, 1, 1)
                self.figure.axes[0].imshow(image_to_show[0, :, :, 0], cmap='gray')
        
        # Start the animation
        self.animation = anim.FuncAnimation(self.figure, update_animation)
        plt.show()
        # Close it
        plt.close(self.figure)

    def log_trainer_output(self) -> None:
        last_output = (
            self.trainer.last_output
            if isinstance(self.trainer, EncoderTrainer) else
            self.trainer.last_output
            if isinstance(self.trainer, GANTrainer) else
            None
        )

        if last_output is not None:
            self.outputs_queue.put(last_output)


class LossAnimator:
    """
    Animates the training of a model.

    This class does not work on all trainer. Currently it only supports 
    `EncoderTrainer` and `GANTrainer`. Uses matplotlib to display the loss
    graph progress on a live window.

    Should not be pickled.
    """

    figure: plt.Figure
    animation_process: Process
    trainer: Trainer
    trainer_hook: Callable[[], None]

    graph_queue: Queue

    def __init__(self, trainer: Trainer) -> None:
        self.animation_process = Process(target=self.begin_animation, args=(), daemon=True)
        self.figure = plt.figure()
        self.trainer = trainer
        self.trainer_hook = self.copy_loss_history
        self.graph_queue = Queue()

    def __enter__(self):
        self.animation_process.start()
        self.trainer.on_batch_end.append(self.trainer_hook)
        return self

    def __exit__(self, type, value, traceback):
        self.trainer.on_batch_end.remove(self.trainer_hook)
        self.animation_process.kill()
        plt.close(self.figure)
        return True

    def begin_animation(self) -> None:
        def update_animation(frame: int):
            graphs = None
            if self.graph_queue.qsize() > 0:
                for _ in range(self.graph_queue.qsize()):
                    graphs = self.graph_queue.get()

            if graphs is not None:
                self.figure.clear()
                self.figure.add_subplot(1, 1, 1)
                for label, graph in graphs.items():
                    self.figure.axes[0].plot(graph, label=label)
                self.figure.axes[0].legend(loc='upper center')
        
        # Start the animation
        self.animation = anim.FuncAnimation(self.figure, update_animation)
        plt.show()
        # Close it
        plt.close(self.figure)

    def copy_loss_history(self) -> None:
        loss_history = (
            { 'loss': self.trainer.loss_history }
            if isinstance(self.trainer, EncoderTrainer) else
            { 'loss': self.trainer.loss_history }
            if isinstance(self.trainer, SingleModelTrainer) else
            {
                'generator loss': self.trainer.gen_loss_history,
                'discriminator real loss': self.trainer.disc_real_loss_history,
                'discriminator fake loss': self.trainer.disc_fake_loss_history,
            }
            if isinstance(self.trainer, GANTrainer) else
            None
        )

        if loss_history is not None:
            self.graph_queue.put(loss_history)

