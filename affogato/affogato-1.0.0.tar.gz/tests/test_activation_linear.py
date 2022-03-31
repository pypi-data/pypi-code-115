import numpy as np
from affogato.layer import Dense
from affogato.optimizer import SGD
from affogato.model import Model
from affogato.activation import Linear, Sigmoid



def test_functionality():
    l = Linear()
    inp = np.array([[2.], [5.]])
    outp = l(inp)

    assert np.array_equal(inp, outp)



def _two_outputs():
    data = [
        (np.array([[0., 1.]]), np.array([[1., 0.]])),
        (np.array([[1., 0]]), np.array([[0., 1.]])),
        (np.array([[1., 1.]]), np.array([[0., 0.]])),
        (np.array([[0., 0.]]), np.array([[1., 1.]])),
        
    ]
    model = Model(2)
    model.add(Dense(2, Linear())) 
    opt = SGD(model.parameters, learning_rate=0.05) 
    loss_history = model.fit(data, opt, verbose=True, num_epochs=2000)

    assert loss_history[-1] < 0.01 


def test_one_output():
    data = [
        (np.array([[0]]), np.array([[0.]])),
        (np.array([[1.]]), np.array([[2.]])),
        (np.array([[2.]]), np.array([[4.]])),
        (np.array([[3.]]), np.array([[6.]])),
        
    ]
    model = Model(1)
    model.add(Dense(1, Linear())) 
    opt = SGD(model.parameters, learning_rate=0.05) 
    loss_history = model.fit(data, opt, verbose=True, num_epochs=100)
    
    print("1", model.predict(np.array([[1.]])))
    print("2", model.predict(np.array([[2.]])))
    print("3", model.predict(np.array([[3.]])))

    for i, layer in enumerate(model.layers):
        print(f"{i = }")
        print(f"weights = \n{layer.weights.values}")
        print(f"bias = \n{layer.bias.values}")

    assert loss_history[-1] < 0.01 
    


def test_non_linear_problem():
    # A linear model can not solve this problem
    data = [
        (np.array([[2., 8.]]), np.array([[81]])),
        (np.array([[3., 7.]]), np.array([[92]])),
        (np.array([[5., 3.]]), np.array([[62]])),
        (np.array([[2., 1.]]), np.array([[10]])),
        (np.array([[5., 2.]]), np.array([[50]])),
        (np.array([[4., 4.]]), np.array([[42]])),
        (np.array([[3., 4.]]), np.array([[52]])),
        (np.array([[1., 8.]]), np.array([[70]])),
        (np.array([[4., 9.]]), np.array([[100]])),
        (np.array([[1., 6.]]), np.array([[60]])),
        (np.array([[1., 6.]]), np.array([[63]])),
        (np.array([[4., 7.]]), np.array([[98]])),
        (np.array([[4., 8.]]), np.array([[100]])),
        (np.array([[3., 7.]]), np.array([[93]])),
        (np.array([[2., 6.]]), np.array([[82]])),
        (np.array([[2., 6.]]), np.array([[80]])),
        (np.array([[1., 7.]]), np.array([[71]])),
        (np.array([[1., 8.]]), np.array([[72]])),
        (np.array([[5., 8.]]), np.array([[100]])),
        (np.array([[3., 7.]]), np.array([[88]])),
        (np.array([[2., 9.]]), np.array([[85]])),
    ]
    model = Model(2)
    model.add(Dense(8, Sigmoid())) 
    model.add(Dense(1, Linear())) 
    opt = SGD(model.parameters, learning_rate=0.05) 
    loss_history = model.fit(data, opt, verbose=True, num_epochs=100)
    
    print("5, 8", model.predict(np.array([[5., 8.]])))
    print("3, 5", model.predict(np.array([[3., 5.]])))
    print("4, 7", model.predict(np.array([[4., 7.]])))

    assert loss_history[-1] > 0.02

