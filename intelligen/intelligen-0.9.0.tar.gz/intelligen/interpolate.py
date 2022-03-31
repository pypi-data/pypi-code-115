import numpy as np
import numpy.polynomial as pol
from typing import Callable, List, Union
Vector = List[float]
Function = Callable[[float], float]
Polynomial = pol.Polynomial


def lagrange(X: Vector, Y: Vector) -> Function:
    """Returns the lagrange interpolation
    Args:
        X (Vector): X-data
        Y (Vector): Y-data
    Returns:
        Callable[[Vector], Vector]: returns the function that evaluates the lagrange interpolation
    """
    X = np.asarray(X)  

    def lagran(x):
        # Checks the input's type
        if type(x) is np.ndarray:
            x = x.reshape(-1, 1)
        
        if isinstance(x, list):
            x = np.array(x).reshape(-1, 1)
        
        else:
            x = np.array([x]).reshape(-1, 1)

        out = 0
        for i in range(len(X)):
            #pi_x = (x - np.array([(X[X != xi]).reshape(-1)] * len(x))) because X[X != xi] autoreshape (-1)
            pi_x = x - np.array([(X[X != X[i]])] * len(x))

            out += Y[i] * (pi_x / (X[i] - X[X != X[i]])).prod(axis = 1)

        return out
    
    return lagran

def lagrange2(X: Vector, Y: Vector) -> Function:

    M = len(X)
    p = np.poly1d(0.0)
    for j in range(M):
        pt = np.poly1d(Y[j])
        for k in range(M):
            if k == j:
                continue
            fac = X[j]-X[k]
            pt *= np.poly1d([1.0, -X[k]])/fac
        p += pt
    return p
    
def mylagrange(X: Vector, Y: Vector) -> Polynomial:
    p = 0
    for i in range(len(X)):
        qn = pol.Polynomial.fromroots(X[X != X[i]])
        p += Y[i] * qn / qn(X[i])
    return p
    

def main() -> None:
    from time import perf_counter
    """ X = np.array([-1, 0, 4,  1, 7, 8])
    X = np.concatenate((X, X+10))
    Y = np.array([ 4, 2, 3, -2, 6, 6])
    Y = np.concatenate((Y, Y+1)) """

    X = np.arange(15)
    Y = np.random.randint(1,100, size=15)

    _x = np.linspace(min(X),max(X),1000)

    s = perf_counter()
    Lagran = mylagrange(X.reshape(-1),Y.reshape(-1))
    f = perf_counter()
    print(f'my lagrange: {f-s}')

    s = perf_counter()
    Lagran2 = lagrange2(X.reshape(-1),Y.reshape(-1))
    f = perf_counter()
    print(f'scipy lagrange: {f-s}')
    
    #Lagran = lagrange(X,Y)
    
    print(type(Lagran))
    print(type(Lagran2))


    s = perf_counter()
    y1 = Lagran(_x)
    f = perf_counter()
    print(f'my lagrange evaluates in: {f-s}')

    s = perf_counter()
    y2 = Lagran2(_x)
    f = perf_counter()
    print(f'scipy lagrange evaluates in: {f-s}')


    plt.scatter(X, Y, c='salmon')
    plt.title('my lagrange')
    plt.ylim(0,101)
    plt.plot(_x, Lagran(_x))
    plt.show()

    plt.scatter(X, Y, c='salmon')
    plt.title('scipy lagrange')
    plt.ylim(0,101)
    plt.plot(_x, Lagran2(_x))
    plt.show()

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    main()