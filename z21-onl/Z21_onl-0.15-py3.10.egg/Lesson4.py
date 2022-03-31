import random
from typing import List
from datetime import datetime
# Задание 1, отобрать из списка стран и столиц, все
# постсоветские страны '

random_country = {'China': 'Beijing', 'Belarus': 'Minsk',
                  'France': 'Paris', 'USA': 'Washington', 'Russia': 'Moscow',
                  'Germany': 'Berlin', 'Spain': 'Madrid', 'Georgia': 'Tbilisi',
                  'Egypt': 'Cairo', 'Italy': 'Rome', 'Ireland': 'Dublin'}
country = [key for key, value in random_country.items()
           if key in ['Azerbaijan', 'Armenia', 'Belarus', 'Georgia',
                      'Kazakhstan', 'Kyrgyzstan', 'Latvia', 'Lithuania',
                      'Russia', 'Tajikistan', 'Turkmenistan',
                      'Uzbekistan', 'Ukraine', 'Estonia']]
print(country)


# Задание 2: функция, генерирующая матрицу
def create_matrix(a: int, n: int, m: int) -> List[list]:
    matrix = [[random.randrange(a) ** 2 for j in range(n)] for i in range(m)]
    return matrix


digit = int(input('Введите число, в пределах которого будет рандомно '
                  'выбираться элемент матрицы: '))
columns = int(input('Введите количество столбцов: '))
strings = int(input('Введите количество строк: '))
print(create_matrix(digit, columns, strings))

# Задание 3: генератор списка с текущим временем


def now_time():
    return datetime.now()


print(now_time())
a = [f'Текущее время {now_time()}' for i in range(2)]
print(a)
