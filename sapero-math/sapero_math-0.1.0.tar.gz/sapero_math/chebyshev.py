from .primegen import *
from .lcm import *
import math

def chebyshev_1(x):
    primes = primelist(x)
    summed = 0
    for k in range(len(primes)):
        summed += math.log(primes[k], math.e)
    return summed

def vonmangoldt(n):
    m, k = pk(n)
    if (m, k) != (0, 0) and k >= 1:
        p = math.log(m, math.e)
    else:
        p = float(0)
    return p

def chebyshev_2lcm(x):
    return math.log(REP(x), math.e)


def chebyshev_2(x):
    summed = 0
    for i in range(x):
        summed += vonmangoldt(i+1)
    return summed

def e_psi(x):
    return math.exp(chebyshev_2(x))