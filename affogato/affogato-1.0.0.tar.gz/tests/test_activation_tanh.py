import numpy as np
from affogato.layer import Dense
from affogato.optimizer import SGD
from affogato.model import Model
from affogato.activation import ReLU, Tanh


def test_two_outputs():
    data = [
        (np.array([[0., 1.]]), np.array([[1., 0.]])),
        (np.array([[1., 0]]), np.array([[0., 1.]])),
        (np.array([[1., 1.]]), np.array([[0., 0.]])),
        (np.array([[0., 0.]]), np.array([[1., 1.]])),
        
    ]
    model = Model(2)
    model.add(Dense(3, ReLU())) 
    model.add(Dense(2, Tanh()))
    opt = SGD(model.parameters, learning_rate=0.05) 
    loss_history = model.fit(data, opt, verbose=True, num_epochs=200)

    assert loss_history[-1] < loss_history[0]


def test_one_output():
    data = [
        (np.array([[0., 1.]]), np.array([[1.]])),
        (np.array([[1., 0]]), np.array([[ 1.]])),
        (np.array([[1., 1.]]), np.array([[0.]])),
        (np.array([[0., 0.]]), np.array([[0]])),
        
    ]
    model = Model(2)
    model.add(Dense(3, ReLU())) 
    model.add(Dense(1, Tanh()))
    opt = SGD(model.parameters, learning_rate=0.05) 
    loss_history = model.fit(data, opt, verbose=True, num_epochs=200)
    
    assert loss_history[-1] < 0.3
    
