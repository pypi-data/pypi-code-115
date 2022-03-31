import numpy as np

class Loss:
    """
    Represents a loss/cost function. It is the optimization objective.
    
    The loss object itself can be called like a function
    (`loss(actual, target)`) as well the derivative (`loss.derivative()`)
    
    Implementers should implement `__call__` and `derivative`
    """

    def __call__(self, actual: np.ndarray, target: np.ndarray) -> float:
        """
        Get the loss/cost value between the target output and the actual
        output
        
        Also updates derivative data
        """
        raise NotImplementedError()
    
    def derivative(self) -> np.ndarray:
        """
        Returns the derivative of the last call to this function
        """
        raise NotImplementedError()


class MeanSquaredError(Loss):
    """
    Returns the average of squared errors between the target and the
    actual value.

    This is a simple and fast loss function that can be used for many problems
    but generally is not the best choice for most problems.

    For classification problems, `CrossEntropy` or `MultiCrossEntropy` might be
    better.
    """
    def __call__(self, actual: np.ndarray, target: np.ndarray) -> float:
        assert actual.shape == target.shape
        self.difference = np.subtract(target, actual)
        return np.average(self.difference * self.difference)

    def derivative(self) -> np.ndarray:
        return -2. * self.difference / self.difference[0].size


class CrossEntropy(Loss):
    """
    Classification loss function suitable for binary classification.
    Use MultiCrossEntropy for multiclass classification.
    """
    epsilon: float = 1e-8

    def __call__(self, actual: np.ndarray, target: np.ndarray) -> float:
        assert actual.shape == target.shape
        
        actual = np.clip(actual, self.epsilon, 1. - self.epsilon)
        self.actual = actual
        self.target = target

        return -np.sum(
            target*np.log(actual) + (1. - target)*np.log(1. - actual),
        ) / actual.shape[0] # average per batch size

    def derivative(self) -> np.ndarray:
        return (self.actual - self.target) / (self.actual * (1 - self.actual))


class MultiCrossEntropy(Loss):
    """
    Classification loss function suitable for multi-class classification.
    Should only be used on arrays which are probability distribution - i.e.
    after a softmax function.

    Use CrossEntropy for binary classification.
    In certain cases, this can be used after an activation function other than
    softmax, but that function should always give normalized arrays (unless
    you know what you are doing).
    """
    epsilon: float = 1e-8

    actual: np.ndarray
    target: np.ndarray
    categories: int

    def __call__(self, actual: np.ndarray, target: np.ndarray) -> float:
        assert actual.shape == target.shape
        
        actual = np.clip(actual, self.epsilon, 1. - self.epsilon)
        self.actual = actual
        self.target = target
        self.categories = np.prod(actual.shape)

        return -np.average(target*np.log(actual))

    def derivative(self) -> np.ndarray:
        return np.where(self.target == 1, -1. / self.actual, 0.)

