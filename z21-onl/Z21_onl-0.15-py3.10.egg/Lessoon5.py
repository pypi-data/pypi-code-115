import time
from functools import reduce
# Задание 1: создать декоратор


def timer(func):
    """Декоратор вычисляет время работы функции"""
    def wrapper(*args):
        start = time.perf_counter()
        result = func(*args)
        end = time.perf_counter()
        print('Время выполнения функции', end - start)
        return result

    return wrapper


number = int(input('Введите число'))

@timer
def fibon(a: int):
    """Функция возвращает ряд Фибоначчи до а-того элемента"""
    row_fibonacci: list = [0, 1]
    while len(row_fibonacci) < a:
        row_fibonacci.append(row_fibonacci[-2] + row_fibonacci[-1])
    return f'Ряд Фибоначчи: {row_fibonacci}'


print(fibon(number))

# Задание 2:

months = ['January', 'February', 'March', 'April',
          'May', 'June', 'July', 'August', 'September',
          'October', 'November', 'December']


@timer
def choice_y(b: list):
    """Функция проверяет, есть в элементах списка буква у"""
    choice = list(filter(lambda k: 'y' in k, b))
    return choice


print(choice_y(months))

digits = [[1, 4, 6, 5, 3], [4, 3, 6, 9], [9, 7, 4, 6, 2]]


@timer
def lst_join(a: list):
    """Функция соединяет списки внутри списка"""
    lst_numb = list(reduce(lambda k, y: k + y, a))
    return lst_numb


print(lst_join(digits))
