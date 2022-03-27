"""Simple calculator package"""

__version__ = "0.1.7"


class Calculator:
    """
    Class containing basic mathematical operations:

    * Addition                      calculator.add(number)
    * Subtraction                   calculator.subtract(number)
    * Division                      calculator.divide(number)
    * Multiplication                calculator.multiply(number)
    * nth root of a number          calculator.n_root(n)
    * Reset                         calculator.reset()
    * Show memory value             calculator.memory()

    For example:

    >>> calculator = Calculator()
    >>> calculator.add(1000)
    1000
    >>> calculator.divide(10)
    100.0
    >>> calculator.n_root(2)
    10.0
    >>> calculator.reset()
    >>> calculator.memory()
    0
    """

    def __init__(self, value: float = 0) -> None:
        """Constructor which is used to initialize memory value"""
        self.value = value

    def memory(self) -> float:
        """Memory value"""
        return self.value

    def add(self, number: float) -> float:
        """Adds number to memory value"""
        self.value += number
        return self.value

    def subtract(self, number: float) -> float:
        """Subtracts number from memory value"""
        self.value -= number
        return self.value

    def multiply(self, number: float) -> float:
        """Multiplies memory value by number"""
        self.value *= number
        return self.value

    def divide(self, number: float) -> float:
        """Divides memory value by number"""
        self.value /= number
        return self.value

    def n_root(self, n: float) -> float:
        """Finds the root of memory value by the inputted number"""
        if self.value <= 0:
            raise ValueError("(n) root of a negative number is not valid")
        elif n <= 0:
            raise ValueError("negative (n) root is not valid")
        else:
            self.value = self.value**(1/n)
        return self.value

    def reset(self) -> None:
        """Resets memory value to its initial value - 0"""
        self.value = 0


if __name__ == '__main__':

    import doctest

    print(doctest.testmod())
