from traceback import extract_tb
import sys

_print = print
_input = input

class exception:
    def __init__(self, exc_info: 'tuple'):
        r'''Принимает результат функции sys.exc_info(). Создаёт описание ошибки, не вызывая остановку выполения'''
        self.type = exc_info[0]
        self.desc = sys.exc_info()[1]
        self.poss = extract_tb(sys.exc_info()[2])

        self.name = exc_info[0].__name__
        self.text = str(sys.exc_info()[1])
        self.posl = []
        i = 0
        for line in self.poss:
            line = str(line).split()
            self.posl.append(dict())
            _i = 0
            while _i < len(line):
                if '/' in line[_i] or '\\' in line[_i]:
                    if line[_i][len(line[_i]) - 1] == ',': line[_i] = line[_i][:len(line[_i]) - 1]
                    self.posl[i]['path'] = line[_i]
                if 'line' in line[_i]:
                    self.posl[i]['line'] = line[_i + 1]
                _i += 1
            i += 1

    def __str__(self):
        #return self.short_out()
        return self.standard_out()

    def __call__(self):
        # return self.short_out()
        return self.standard_out()

    def __getitem__(self, item):
        print('stdinout:', item)
        return '!!!'

    def standard_out(self):
        r'''Симулирует стандартного вида ошибку и возвращает её в виде строки'''
        posl = self.posl
        i = 0
        out = 'exception in:\n'
        while i < len(posl):
            if 'path' not in posl[i].keys(): out += f'system output: "{posl[i]["line"]}"\n'
            else: out += f'file "{posl[i]["path"]}", line {posl[i]["line"]}:\n'
            i += 1
        return out + f'{self.name}: {self.desc}'

    def custom_out(self):
        r'''Возвращает строку с упрощёным видом, которая содержит информацию об ошибке'''
        return 'custom output doesnt work now'

    def short_out(self):
        r'''Возвращает краткую информацию об ошибке в виде строки'''
        posl = self.posl[len(self.posl) - 1]
        return f'exception in "{posl["path"]}", line {posl["line"]}:\n    {self.name}: {self.desc}'

    def description(self):
        r'''Возвращает описание текущей ошибки'''
        return self.desc



