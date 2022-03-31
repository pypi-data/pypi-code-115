from typing import List, Union, Optional
from dataclasses import dataclass
import numpy as np

from affogato.activation import Activation, Linear, Sigmoid, Tanh


@dataclass
class Parameters:
    """
    A dataclass that represents the trainable parameters for each layer.
    It contains the values of the parameters, as well as the gradients for backpropagation purposes.
    """
    values: np.ndarray
    gradients: np.ndarray
    
    def __init__(self, shape: tuple[int, ...], randomize: bool = False) -> None:
        self.values = np.random.uniform(-1., 1., shape) if randomize else np.zeros(shape)
        self.gradients = np.zeros(shape)
    
    def shape(self) -> tuple:
        return self.values.shape


class Layer:
    """
    A base class that represents a generic layer of any type.
    
    Implementers should implement `forward_raw`, `backward_raw`, and `get_parameters` 

    Parameters
    ----------
    activation : Activation. Default: Linear
        The activation function to use. Defaults to Linear.
    """

    activation: Activation

    def __init__(self, activation: Optional[Activation] = None) -> None:
        self.activation = activation or Linear()
    
    def forward(self, input: np.ndarray) -> np.ndarray:
        """
        Takes some input column vector and returns the output
        """
        return self.activation(self.forward_raw(input))

    def forward_raw(self, input: np.ndarray) -> np.ndarray:
        """ Same as forward, but without the activation. To be implemented by subclasses """
        raise NotImplementedError()

    def backward(self, output_delta: np.ndarray) -> np.ndarray:
        """
        Takes the error in the output as a column vector and returns
        the error in input.
        
        Should only be called after forward was called.
        
        Also updates the gradients of the parameters optimizers. 
        """
        return self.backward_raw(self.activation.backward(output_delta))

    def backward_raw(self, output_delta: np.ndarray) -> np.ndarray:
        """ Same as backward, but without the activation. To be implemented by subclasses """
        raise NotImplementedError()
    
    def compile(self, input_size: tuple[int, ...]) -> tuple[int, ...]:
        """
        Takes the input size of the layer and builds the weights accordingly.
        
        returns the layers output size.
        """
        raise NotImplementedError()
    
    def get_parameters(self) -> List[Parameters]:
        """
        Returns the adjustable paremeters the layer contains
        """
        raise NotImplementedError()


class Dense(Layer):
    """
    The basic class for all deep learning model. The layer represents a fully conected layer.

    Should be initialized with the followings:
    `input_size` as the input for the layer.
    `output_size` as the output of the layer.
    `activation` for the activaion function the layer will use.


    Example:
    -------
    >>> # Create a `Model` and add a Dense layer as the first layer.
    >>> # Note: you need to give the input shape to the model at creation. 
    >>> # After that, there is no need to enter the input shape for each layer.
    >>> model = affogato.model.Model((1, 2))
    >>> model.add(Dense(2, ReLU())) 
    >>> # Now the model will take as input arrays of shape (1, 2)
    >>> # and output arrays of shape (1, 2).
    >>> # The activation function will be Relu, but it can be anything that derives from `affogato.activaion.Activation()`
    >>> model.compile()
    >>> # Note: after we created the model, we need to compile it in order to use it.

    Parameters:
    ---------
    output_size: int 
        the size of the output vector from that layer.

    activation: Activation. Default: Linear
        the activation function of the layer. 
    """
    weights: Parameters
    bias: Parameters
    input_size: int
    output_size: int
    
    def __init__(self, output_size: int, activation: Optional[Activation] = None, no_bias: bool = False) -> None:
        super().__init__(activation)
        self.output_size = output_size
        self.no_bias = no_bias
        if not self.no_bias:
            self.bias = Parameters((1,output_size))

    def compile(self, input_size: tuple[int, ...]) -> tuple[int, ...]:
        self.input_size = input_size[1]
        self.weights = Parameters((input_size[1],self.output_size), randomize=True)
        return (input_size[0], self.output_size)

    def forward_raw(self, input: np.ndarray) -> np.ndarray:
        assert input.shape[1:] == (self.input_size,)
        
        self.input = input
        output = np.dot(input, self.weights.values)
        if not self.no_bias:
            output += self.bias.values
        return output
    
    def backward_raw(self, output_delta: np.ndarray) -> np.ndarray:
        #assert(output_delta.shape == (self.output_size, 1))
        
        #   Cache gradients for the optimizer
        self.weights.gradients += np.dot(self.input.T, output_delta)
        if not self.no_bias:
            self.bias.gradients += np.sum(output_delta, axis=0, keepdims=True)
        #   Return input delta
        return np.dot(output_delta, self.weights.values.T)
    
    def get_parameters(self) -> List[Parameters]:
        return [self.weights] + ([self.bias] if not self.no_bias else [])


class Dropout(Layer):
    """
    The Dropout layer randomly sets input units to 0 with a frequency of `rate` 
    at each step during training time, which helps prevent overfitting.

    Parameters:
    -----------
    rate: float
        the rate of dropout, between 0 and 1.
        Smaller values mean more dropout.
        A value of 1 means no dropout.

    activation: Activation. Default: Linear
        the activation function of the layer.
    """
    rate: float
    input_size: tuple[int, ...]

    def __init__(self, rate: float, activation: Optional[Activation] = None) -> None:
        super().__init__(activation)
        self.rate = rate
        
    def compile(self, input_size: tuple[int, ...]) -> tuple[int, ...]:
        self.input_size = input_size
        return input_size

    def forward_raw(self, x: np.ndarray) -> np.ndarray:
        self.drops = np.random.binomial(1, self.rate, size=self.input_size)
        return x * self.drops
    
    def backward_raw(self, output_delta: np.ndarray) -> np.ndarray:
        return output_delta * self.drops

    def get_parameters(self) -> List[Parameters]:
        return []


class Flatten(Layer):
    """ Flattens an input to a single column vector. """

    previous_shape: tuple[int, ...] = ()

    def compile(self, input_size: tuple[int, ...]) -> tuple[int, ...]:
        output_shape = 1
        for element in input_size:
            output_shape *= element  

        return (1, output_shape)

    def forward_raw(self, x: np.ndarray) -> np.ndarray:
        self.previous_shape = x.shape
        # (No need to explicitly copy because .reshape() is a pure function)
        return x.reshape((x.shape[0], -1))

    def backward_raw(self, output_delta: np.ndarray) -> np.ndarray:
        # Reshape the output_delta for the previous layer
        return output_delta.reshape(self.previous_shape)

    def get_parameters(self) -> List[Parameters]:
        return []


class Reshape(Layer):
    """ Flattens an input to a single column vector. """

    previous_shape: tuple[int, ...] = ()
    def __init__(self, convert_to_shape, activation: Optional[Activation] = None) -> None:
        super().__init__(activation)
        self.convert_to_shape = convert_to_shape

    def compile(self, input_size: tuple[int, ...]) -> tuple[int, ...]:
        return self.convert_to_shape

    def forward_raw(self, x: np.ndarray) -> np.ndarray:
        self.previous_shape = x.shape
        # (No need to explicitly copy because .reshape() is a pure function)
        return x.reshape((x.shape[0], ) + self.convert_to_shape[1:])

    def backward_raw(self, output_delta: np.ndarray) -> np.ndarray:
        # Reshape the output_delta for the previous layer
        return output_delta.reshape(self.previous_shape)

    def get_parameters(self) -> List[Parameters]:
        return []



class Convolution(Layer):
    """
    Like a space invariant dense layer (using a convolutional filter).
    
    Takes an input of shape (batch_size, input_width, input_height, input_channels)
    and returns an output of shape (batch_size, input_width - f + 1, input_height - f + 1, output_channels)
    where f is the filter size.
    """

    input_width: int
    input_height: int
    filter_size: int
    input_channels: int
    output_channels: int

    filters: Parameters
    """
    Matrix of shape (output_channels, f, f, input_channels)
    
    Explanation:
    Each filter is of shape (f, f, input_channels) - a square with depth of the
    input image. The first axis is the number of filters.
    """

    input: np.ndarray
    """ The last input fed to the layer """

    def __init__(self, filter_size: int, output_channels: int = 1,
                 activation: Optional[Activation] = None) -> None:
        super().__init__(activation)
        self.filter_size = filter_size
        self.output_channels = output_channels

    def compile(self, input_size: tuple[int, ...]) -> tuple[int, ...]:
        if len(input_size) != 4:
            raise ValueError(
                "Input size must be of shape "
                "(1, input_width, input_height, input_channels)"
            )

        self.input_width = input_size[1]
        self.input_height = input_size[2]
        self.input_channels = input_size[3]
        self.filters = Parameters(
            (self.output_channels, self.filter_size, self.filter_size, self.input_channels),
            randomize=True,
        )
        
        return (1, self.input_width - self.filter_size + 1, self.input_height - self.filter_size + 1, self.output_channels)


    def forward_raw(self, x: np.ndarray) -> np.ndarray:
        assert (x.shape[1:] == (self.input_width, self.input_height, self.input_channels))

        self.input = x
        batch_size = x.shape[0]
        output_width = self.input_width - self.filter_size + 1
        output_height = self.input_height - self.filter_size + 1
        
        output = np.zeros((batch_size, output_width, output_height, self.output_channels))

        # Iterate over output pixels for each image in the batch
        for w in range(output_width):
            for h in range(output_height):
                f = self.filter_size
                # Current input slices in the batch
                # Shape: (batch_size, f, f, input_channels)
                img_slices = self.input[:, w:w+f, h:h+f, :]
                # Pixels (w, h) of the output in the batch
                output_pixels = output[:, w, h, :]

                # Sum over the filter and input channels, for each output channel
                # and each image in the batch
                output_pixels += np.sum(
                        img_slices[:, None, :, :, :] * 
                        self.filters.values[None, :, :, :, :],
                        axis=(2, 3, 4),
                    )

        return output

    def backward_raw(self, output_delta: np.ndarray) -> np.ndarray:
        output_width = self.input_width - self.filter_size + 1
        output_height = self.input_height - self.filter_size + 1

        # This is the function's return value
        input_delta = np.zeros(self.input.shape)

        # Iterate over output pixels for each image in the batch
        for h in range(output_height):
            for w in range(output_width):
                # Slices of the input affecting the current output pixel
                # Shape is (batch, f, f, input_channels)
                f = self.filter_size
                img_slices = self.input[:, w:w+f, h:h+f]
                img_slices_delta = input_delta[:, w:w+f, h:h+f]

                # The output delta of the (w, h) pixels in the current batch
                # Shape is (batch, output_channels)
                output_pixels_delta = output_delta[:, w, h]

                # sum filter deltas over the batch
                self.filters.gradients += (
                    img_slices[:, None, :, :, :] *
                    output_pixels_delta[:, :, None, None, None]
                ).sum(axis=0)

                # sum input deltas over the output channels
                img_slices_delta += (
                    output_pixels_delta[:, :, None, None, None] *
                    self.filters.values[None, :, :, :, :]
                ).sum(axis=1)

        return input_delta

    def get_parameters(self) -> List[Parameters]:
        return [self.filters]


class Deconvolution(Layer):
    """
    Takes an input of shape (batch_size, input_width, input_height, input_channels)
    and returns an output of shape (batch_size, input_width + f - 1, input_height + f - 1, output_channels)
    where f is the filter size.

    Useful in GAN models, among other things.
    """

    input_width: int
    input_height: int
    filter_size: int
    input_channels: int
    output_channels: int

    filters: Parameters
    """
    Matrix of shape (input_channels, f, f, output_channels)
    
    Explanation:
    Each filter is of shape (f, f, input_channels) - a square with depth of the
    input image. The first axis is the number of filters.
    """

    input: np.ndarray
    """ The last input fed to the layer """

    def __init__(self, filter_size: int, output_channels: int = 1,
                 activation: Optional[Activation] = None) -> None:
        super().__init__(activation)
        self.filter_size = filter_size
        self.output_channels = output_channels

    def compile(self, input_size: tuple[int, ...]) -> tuple[int, ...]:
        if len(input_size) != 4:
            raise ValueError(
                "Input size must be of shape "
                "(1, input_width, input_height, input_channels)"
            )

        self.input_width = input_size[1]
        self.input_height = input_size[2]
        self.input_channels = input_size[3]
        self.filters = Parameters(
            (self.input_channels, self.filter_size, self.filter_size, self.output_channels),
            randomize=True,
        )
        
        return (1, self.input_width + self.filter_size - 1, self.input_height + self.filter_size - 1, self.output_channels)

    def forward_raw(self, x: np.ndarray) -> np.ndarray:
        assert x.shape[1:] == (self.input_width, self.input_height, self.input_channels), "Wrong input shape"

        self.input = x
        batch_size = x.shape[0]
        output_width = self.input_width + self.filter_size - 1
        output_height = self.input_height + self.filter_size - 1
        
        output = np.zeros((batch_size, output_width, output_height, self.output_channels))

        # Iterate over input pixels for each image in the batch
        for w in range(self.input_width):
            for h in range(self.input_height):
                f = self.filter_size
                # Current output slices in the batch
                # Shape: (batch_size, f, f, output_channels)
                output_slices = output[:, w:w+f, h:h+f, :]
                # Pixels (w, h) of the input in the batch
                # Shape (batch_size, input_channels)
                input_pixels = self.input[:, w, h, :]

                # Sum over the filter and input pixels, for each output channel
                # and each pixel in the batch
                output_slices += np.sum(
                        input_pixels[:, :, None, None, None] * 
                        self.filters.values[None, :, :, :, :],
                        axis=1,
                    )

        return output

    def backward_raw(self, output_delta: np.ndarray) -> np.ndarray:
        output_width = self.input_width + self.filter_size - 1
        output_height = self.input_height + self.filter_size - 1
        # This is the function's return value
        input_delta = np.zeros(self.input.shape)

        # Iterate over input pixels for each image in the batch
        for h in range(self.input_height):
            for w in range(self.input_width):
                # Slices of the output affecting the current input pixel
                # Shape is (batch, f, f, output_channels)
                f = self.filter_size
                output_slices_delta = output_delta[:, w:w+f, h:h+f]

                # The input delta of the (w, h) pixels in the current batch
                # Shape is (batch, input_channels)
                input_pixels = self.input[:, w, h, :]
                input_pixels_delta = input_delta[:, w, h]

                # sum filter deltas over the batch
                self.filters.gradients += (
                    input_pixels[:, :, None, None, None] *
                    output_slices_delta[:, None, :, :, :]
                ).sum(axis=0)

                # sum input deltas over the output channels
                input_pixels_delta += (
                    output_slices_delta[:, None, :, :, :] *
                    self.filters.values[None, :, :, :, :]
                ).sum(axis=(2, 3, 4))

        return input_delta

    def get_parameters(self) -> List[Parameters]:
        return [self.filters]

