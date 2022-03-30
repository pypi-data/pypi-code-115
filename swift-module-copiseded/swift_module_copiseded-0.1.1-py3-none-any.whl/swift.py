import cmath
def addOne(number):
    return number + 1
def addDouble(number):
    return number * 2
def add(distance,number):
    return number + distance
def stepUpTimes(times,number):
    return number + times * number
def numberTimes(times,number):
    return number * times
def aNumberOfFactorial(number):
    result = 1
    for item in range(1,number+1):
        result = result * item
    return result
def squareRoot_negativeNumber(number):
    num = number
    num_sqrt = cmath.sqrt(num)
    return '{0} 的平方根为 {1:0.3f}+{2:0.3f}j'.format(num ,num_sqrt.real,num_sqrt.imag)
def squareRoot_positiveNumber(number):
    num = number
    num_sqrt = num ** 0.5
    return ' %0.3f 的平方根为 %0.3f'%(num ,num_sqrt)
def squareOfANumber(number):
    return number * number
