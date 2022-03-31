import copy, os, sys, time, configparser
from tools import simple, info
mass_py = []

def class_def_comp(path: ('str'), encoding = 'utf-8', black_list: 'list' = [], white_list: 'list' = []):
    r'''Создаёт скрипты *.py из файлов *.class, *.def и *.pre, которые находятся в папке по передаваймой ссылке
    *Внимание, удалит одноименный папке скрипт, если он есть в корне её расположения!
    *Если вы работаете в Windows, создавайте файлы *.class, *.def и *.pre в кодировке cp1251
    *Черные и белые списки принимают список из наименований файлов с расширениями'''

    global mass_py
    mass_py.append(path + '.py')
    if os.path.isfile(path + '.py'): os.remove(path + '.py')

    names = os.listdir(path)
    if white_list == []:
        for value in black_list:
            if value in names:
                names.remove(value)
    else:
        _names = copy.deepcopy(names)
        for value in _names:
            if value not in white_list:
                names.remove(value)

    out = ''
    for name in names:
        if '.pre' in name:
            file = open(path + f'/{name}', 'r', errors='ignore', encoding = encoding)
            out += file.read() + '\n\n\n'

    for name in names:
        if '.class' in name:
            file = open(path + f'/{name}', 'r', errors='ignore', encoding = encoding)
            name = name.split('.')[0]
            out += f'class {name}:\n'
            for line in file:
                out += f'\t{line}'
            out += '\n\n\n'

        if '.def' in name:
            file = open(path + f'/{name}', 'r', errors='ignore', encoding = encoding).read()
            name = name.split('.')[0]
            args_line = ''
            body_line = ''

            if file[0] == '(': i = 1
            else: i = 0
            while file[0] == '(' and i < len(file):
                if file[i] == ')':
                    i += 1
                    break
                elif file[i] == '\n':
                    i += 1
                else:
                    args_line += file[i]
                i += 1

            if file[0] == '(': file = file[i + 1:]
            if file[0] == '\n': file = file[1:]

            for line in file.split('\n'):
                body_line += f'\t{line}\n'
            out += f'def {name}({args_line}):\n{body_line}\n\n'

    for name in names:
        if '.pst' in name:
            file = open(path + f'/{name}', 'r', errors='ignore', encoding = encoding)
            out += file.read() + '\n\n'

    file = open(path + '.py', 'w', encoding = 'utf-8')
    file.write(out)
    file.close()

def temp_py_clear():
    r'''Удаляет все временные файлы, созданные при помощи class_def_comp во время работы программы'''
    pass

def fold_dict(path: 'str'):
    r'''Получить словарь, который содержит всю информацию о папке, файлы, вложенные папки и ссылки на них
    *Ссылка на папку, будет хранится в ключе "/"'''
    path = simple.path_os(path)
    out = dict()
    out['/'] = path
    for elem in os.listdir(path):
        if os.path.isdir(path + simple.path_os('/') + elem):
            out[elem] = fold_dict(path + simple.path_os('/') + elem)
        else:
            out[elem] = path + simple.path_os('/') + elem
    return out

def manifest(path: 'str'):
    r'''Принимает абсолютную ссылку на расположение ini файла и возвращает информацию из него в виде словаря
    *Создаёт временный файл temp.ini в корневой папке AC'''
    file = open(str(path), 'r')
    _file = open(r'temp.ini', 'w')
    _file.write(file.read())
    _file.close()
    read_conf = configparser.ConfigParser()
    read_conf.read(r'temp.ini')
    out = dict()

    for section in read_conf.keys():
        _out = dict()
        for key in read_conf[section].keys():
            _out[key] = read_conf[section][key]
        out[section] = _out

    os.remove(r'temp.ini')
    return out

def var():
    r'''Позволяет создавать общие переменные, на время работы программы'''
    pass

def convert():
    r'''Работает с папкой extens'''
    pass