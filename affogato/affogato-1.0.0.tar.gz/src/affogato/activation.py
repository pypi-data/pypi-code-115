import numpy as np

class Activation:
    """
    Represents an activation function.
    
    The activation object itself can be called like a function (`activation(input)`)
    
    Implementers should implement `__call__` and `backward`
    """

    def __call__(self, input: np.ndarray) -> np.ndarray:
        """
        Returns the value after the function is applied
        
        Also updates data for the next `backward` call
        """
        raise NotImplementedError()

    def backward(self, output_delta: np.ndarray) -> np.ndarray:
        """
        Returns the delta of the last call's input to this function
        """
        raise NotImplementedError()


class ReLU(Activation):
    """
    Zeros out negative signals and lets positive signals through
    """

    def __init__(self, leak: float = 0.):
        self.leak = leak

    def __call__(self, input: np.ndarray) -> np.ndarray:
        self.output = input.copy()
        self.output[self.output<0.] *= self.leak
        return self.output
    
    def backward(self, output_delta: np.ndarray) -> np.ndarray:
        # At least that what I think it should do because: 
        # In the first case, when x<0 so the derivative of f(x) with respect to x gives result f'(x)=0. 
        # In the second case, it's clear to compute f'(x)=1.
        # Return f'(x) * dy
        return np.where(self.output>0, output_delta, output_delta*self.leak)
    
    
class Sigmoid(Activation):
    """
    Represents a Sigmoid activation function. The function squashes the input to the range of [0, 1].
    
    The mathematical equation for the function is `S(x) = 1 / (1+e^-x)`
    """
    clip_radius: float = 500

    def __call__(self, input: np.ndarray) -> np.ndarray:
        self.input = input.copy()
        self.output = 1. / (1. + np.exp(-np.clip(input, -self.clip_radius, self.clip_radius)))
        return self.output
    
    def backward(self, output_delta: np.ndarray) -> np.ndarray:
        return (self.output * (1. - self.output)) * output_delta


class Tanh(Activation):
    """
    Represents a Tanh activation function. The function squashes the input to the range of [-1, 1].
    
    The mathematical equation for the function is `tanh(x) = (e^x - e^-x)/(e^x + e^-x)`
    """
    def __call__(self, input: np.ndarray) -> np.ndarray:
        self.output = np.tanh(input)
        return self.output

    def backward(self, output_delta: np.ndarray) -> np.ndarray:
        return (1 - (self.output * self.output)) * output_delta


class Linear(Activation):
    """
    Represents a Linear activation function. The function returns the exact input. 
    
    The mathematical equation for the function is `f(x) = x`
    """
    def __call__(self, x: np.ndarray) -> np.ndarray:
        self.input = x
        return self.input
    
    def backward(self, output_delta: np.ndarray) -> np.ndarray:
        return output_delta


class Softmax(Activation):
    """
    An activation function that returns a normalized exponential of the input.
    It only works on flat input (with shape (b, n), b is batch size, n is input
    size).

    It is often used as the last activation of model in a multi-class
    classification problem, with a loss of `MultiCrossEntropy`.
    The reason is that an error in a single class affects the propagated error
    in the entire input.
    The mathematical equation for the function is `f(x) = e^x / sum(e^x)`.
    
    It is noteable that the output is always normalized (Sums to 1). The output
    is usually treated as a probability distribution of categories.
    """

    output: np.ndarray

    def __call__(self, x: np.ndarray) -> np.ndarray:
        assert len(x.shape) == 2, "Softmax can only be applied to flat inputs"

        # e^x. add -max(x) at each input to increase numerical stability
        exp = np.exp(x - np.max(x, axis=1, keepdims=True))
        self.output = exp / np.sum(exp, axis=1, keepdims=True)
        return self.output
    
    def backward(self, output_delta: np.ndarray) -> np.ndarray:
        # According to https://e2eml.school/softmax.html
        # And https://eli.thegreenplace.net/2016/the-softmax-function-and-its-derivative/
        # And https://www.mldawn.com/the-derivative-of-softmaxz-function-w-r-t-z/
        #
        # The "derivative" of softmax is defined using
        #   d S(x)_i / d x_j = S(x)_i * (1(i = j) - S(x)_j)
        #                    = S(x)_i * 1(i = j) - S(x)_i * S(x)_j
        #   d S(x) / d x = diag(S(x)) -  S(x)^T * S(x)
        # where x_j is the j-th element of the input vector
        # and S(x)_i is the i-th element of the output vector
        # and 1(i = j) is equal to 1 if i = j, and 0 otherwise
        #
        # This is called a jacobian matrix. It can be used to compute the input
        # deltas.

        # If we ignore batches we can write
        # jacobian = (
        #     self.output * np.identity(self.output.shape[1])
        #     - np.dot(self.output.T, self.output)
        #     # or - self.output.T * self.output, in this case it doens't matter
        # )
        jacobian = (
            self.output[:, :, None] * np.identity(self.output.shape[1])[None, :, :]
            - self.output[:, :, None] * self.output[:, None, :]
        )

        # If we ignore batches we can write
        # return np.dot(jacobian, output_delta)
        return np.sum(jacobian * output_delta[:, :, None], axis=1)

