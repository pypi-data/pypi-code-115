import re


# Задание 1
class Geoprogres:
    def __init__(self, first_term: int, denominator: int):
        self.first_term = first_term
        self.denominator = denominator
        Geoprogres.validate(self)

    def validate(self):
        if self.first_term != 0 and self.denominator != 0:
            return self.first_term, self.denominator
        raise InvalidProgressionValuesException

    def __call__(self):
        n = 0
        while True:
            res = self.first_term * self.denominator ** n
            n += 1
            yield res


class InvalidProgressionValuesException(Exception):
    def __init__(self, message='a and q must not be 0 '):
        super().__init__(message)


progression = Geoprogres(1, 2)
try:
    for i in progression():
        print(i)
except KeyboardInterrupt:
    print('Bye')


# Задание 2


def filtr(text: str):
    """Функция выбирает из текста email адреса"""
    res = re.findall(r'([\w.\-]{0,64}@[\w\-]+\.[A-Za-z]{2,})', text, flags=re.ASCII)
    print(f'В строке обнаружены следующие адреса:{res}')


input_text = str(input('Введите ваш текст для поиска '))
filtr(input_text)
