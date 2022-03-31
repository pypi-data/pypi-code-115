r'''Данный модуль отвечает за предоставление информации системы или python'''
from tools import simple, represent
import inspect, copy, sys

def attributes(obj, sys: 'bool' = False, call: 'bool' = True, arg: 'bool' = False):
    attrs = dir(obj)
    out = []

    i = 0
    while i < len(attrs):
        if '__' in attrs[i]:
            if sys: out.append(attrs[i])
            attrs.pop(i)
            i -= 1
        i += 1

    i = 0
    while i < len(attrs):
        if '__call__' in dir(getattr(obj, attrs[i])):
            if call: out.append(attrs[i])
            attrs.pop(i)
        i += 1

    if arg: out += attrs
    return out

def args(obj: ('_def', '_class')):
    r'''Принимает объект и возвращает аргументы для вызова этого объекта функции или класса
    *При неккоректном использовании может возвращать пустую информацию
    *Игнорирует переменные с наименованием safe
    *Если в классе есть метод __args__ то возьмёт информацию из его вывода'''
    if type(obj).__name__ not in ['method', 'function']: argspec = inspect.getfullargspec(obj.__init__)
    else: argspec = inspect.getfullargspec(obj)

    arguments = copy.copy(argspec[0])
    defaults = copy.copy(argspec[3])
    arguments.reverse()
    if type(defaults).__name__ != 'tuple': defaults = tuple()

    temp = dict()
    for i in range(len(arguments) - 1):
        if i < len(defaults): temp[arguments[i]] = defaults[i]
        else: temp[arguments[i]] = None

    arguments.reverse()
    defaults = temp
    arguments += argspec[4]
    if type(argspec[5]).__name__ == 'dict': defaults.update(argspec[5])
    annotation = copy.copy(argspec[6])

    temp = list()
    for name in arguments:
        arg = dict(name = name)
        if annotation.get(name) != None: arg['ann'] = annotation[name]
        else: arg['ann'] = None
        if defaults.get(name) != None: arg['def'] = defaults[name]
        else: arg['def'] = None
        temp.append(arg)

    i = 0
    while i < len(temp):
        if temp[i]['name'] in ['self']: temp.pop(i)
        else: i += 1
    out = dict(args = temp)

    if argspec[1] != None:
        temp = dict(name = argspec[1])
        if annotation.get(argspec[1]) != None: temp['ann'] = annotation[argspec[1]]
        else: temp['ann'] = None
        if defaults.get(argspec[1]) != None: temp['def'] = defaults[argspec[1]]
        else: temp['def'] = None
        out['*args'] = temp
    else: out['*args'] = None

    if argspec[2] != None:
        temp = dict(name = argspec[2])
        if annotation.get(argspec[2]) != None: temp['ann'] = annotation[argspec[2]]
        else: temp['ann'] = None
        if defaults.get(argspec[2]) != None: temp['def'] = defaults[argspec[2]]
        else: temp['def'] = None
        out['**kwargs'] = temp
    else: out['**kwargs'] = None

    return out

def ac_path():
    r'''Показывает расположение АС'''
    sb = simple.slash_os()
    _path = __file__
    _path = _path.split(sb)
    _path = _path[:len(_path) - 2]
    _path = sb.join(_path)
    return _path

def project_path(): #Берёт просто текущее системное расположение
    r'''Достаёт информацию о расположении проекта из ac/data/manifest.ini'''
    #return represent.manifest(ac_path() + simple.path_os('/manifest.ini'))['environment']['project']
    out = sys.path[0]
    if out == '' or out == ac_path(): out = ac_path() + simple.slash_os() + 'project'
    return out