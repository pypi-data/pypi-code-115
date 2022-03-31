class Calculate:
    def __init__(self, first_digit, second_digit):
        self.first_digit = first_digit
        self.second_digit = second_digit

    def addition(self):
        result = self.first_digit + self.second_digit
        return result

    def subtraction(self):
        result = self.first_digit - self.second_digit
        return result

    def multiplication(self):
        result = self.first_digit * self.second_digit
        return result

    def division(self):
        try:
            result = self.first_digit / self.second_digit
            return result
        except ZeroDivisionError:
            return 'Cant divide by zero'


class ExceptionOperation(Exception):
    def __init__(self, message='Choose a number from 1 to 4 '):
        super().__init__(message)


try:
    a = float(input('Enter  first digit'))
    b = float(input('Enter second digit'))
    operation = int(input('Enter the code of the operation you want to perform: \n'
                          '1. Addition\n'
                          '2. Subtraction\n'
                          '3. Multiplication\n'
                          '4. Division'))

except ValueError:
    print('Please, enter DIGITS')

else:
    express = Calculate(a, b)
    if operation == 1:
        print(express.addition())
    elif operation == 2:
        print(express.subtraction())
    elif operation == 3:
        print(express.multiplication())
    elif operation == 4:
        print(express.division())
    else:
        raise ExceptionOperation
