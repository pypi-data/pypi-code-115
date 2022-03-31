from typing import List
import numpy as np
import affogato.layer


class Optimizer:
    """
    An algorithm that provides the necessary recipe to update the model's
    parameters using their gradients with respect to the loss function (optimization objective)
    
    Implementors should implement `adjust_parameters`
    """

    parameters: List[affogato.layer.Parameters]
    
    def __init__(self, parameters):
        self.parameters = parameters

    def adjust_parameters(self) -> None:
        """
        Adjusts each parameter according to it's gradient
        (stored in the parameter after calling `.backward()`)
        """
        raise NotImplementedError()
        
    def clear_backward_data(self) -> None:
        """ Removes data stored in parameters after calling `.backward()`. """
        for parameter in self.parameters:
            parameter.gradients.fill(0.)


class SGD(Optimizer):
    """
    Implements the Stochastic Gradient Descent optimizer.
    The optimizer updates the weights of the model by subtructing the LR times their gradients. 

    The learning rate is a configurable hyperparameter used in the training of the network
    that has a small positive value, often in the range between [0, 1]. 
    The learning rate controls how quickly the model is adapted to the problem.
    
    A good (or good enough) learning rate must be discovered via trial and error, there is no formula to decide which LR to use before training.
    In general, a large learning rate allows the model to learn faster, at the cost of arriving on a sub-optimal set of weights. 
    A smaller learning rate may allow the model to learn a more optimal set of weights but it can take significantly longer to train.


    Parameters:
    ----------
    parameters:
        the trainable parameters of the model.

    learning_rate: float
        the learning rate that will be used when adjusting the model's weights.(see above for description)
    """
    learning_rate: float

    def __init__(self, parameters, learning_rate: float = .01):
        super().__init__(parameters)
        self.learning_rate = learning_rate

    def adjust_parameters(self) -> None:
        for parameter in self.parameters:
            parameter.values -= self.learning_rate * parameter.gradients


class Adam(Optimizer):
    """
    Adam is an industry standard optimizer for general problems that can learn
    complex data efficiently.

    The difference between Adam and SGD is Adam's momentum and learning rate decay.
    """

    learning_rate: float
    """
    The initial learning rate of the optimizer.
    """
    momentum_decay: float
    """
    A value between 0 and 1 that controls the decay of momentum of parameter change.
    Usually called beta 1 in most contexts.

    Momentum is a technique that helps to overcome the problem of vanishing
    gradients.
    When the value of this variable is close to 0, the errors in a single output
    cause immediate changes.
    When the value is closer to 1, errors in single outputs may not affect the
    model as much.
    """
    learning_rate_decay: float
    """
    A value between 0 and 1 that controls the decay of learning rate.
    Usually called beta 2 in most contexts.

    In most cases, a value of 0.999 is a good choice.
    """

    momentums: List[np.ndarray]
    decay_values: List[np.ndarray]
    time: int
    """ The number of times the optimizer has been called. """

    def __init__(self, parameters: List[affogato.layer.Parameters],
            learning_rate: float = 0.001,
            momentum_decay: float = 0.9, learning_rate_decay: float = 0.999,
            epsilon: float = 1e-7) -> None:
        self.parameters = parameters
        self.learning_rate = learning_rate
        self.momentum_decay = momentum_decay
        self.learning_rate_decay = learning_rate_decay
        self.epsilon = epsilon
        
        self.momentums = [ np.zeros(p.shape()) for p in parameters ]
        self.decay_values = [ np.zeros(p.shape()) for p in parameters ]
        self.time = 0

    def adjust_parameters(self) -> None:
        # Algroithm taken from https://arxiv.org/pdf/1412.6980.pdf

        self.time += 1

        for i, (parameter, momentum, decay_value) \
        in enumerate(zip(self.parameters, self.momentums, self.decay_values)):
            # Update the momentum
            momentum *= self.momentum_decay
            momentum += (1 - self.momentum_decay) * parameter.gradients
            momentum_hat = momentum / (1 - self.momentum_decay ** self.time)

            # Update the decay value
            decay_value *= self.learning_rate_decay
            decay_value += (1 - self.learning_rate_decay) * np.square(parameter.gradients)
            decay_value_hat = decay_value / (1 - self.learning_rate_decay ** self.time)

            # Update the parameter
            parameter.values -= self.learning_rate * momentum_hat / (np.sqrt(decay_value_hat) + self.epsilon)

            # Store the new values
            self.momentums[i] = momentum
            self.decay_values[i] = decay_value

