from interfaces import console
from tools import assemblу, info, represent, stdinout, simple
import os, sys, threading, copy, time

return_value = (None, 0, None, 0) #Описать этот нюанс в руководстве
auto_var = []

class sub():
    r'''Вспомогательный класс для работы core и tools. Он не расчитан для личного использования, но вы все ещё можете им воспользоватся'''
    def command_pars(line: 'str', auto_var: ('list', 'tuple')):
        r'''Принимает сырую строку от пользователя и делит её на список, после чего вставляет переменные
        *auto_var это список, содержащий в себе переменные, вставляются по правилу, самое последние значние в списке auto_var первое'''
        command = line.split(' ')
        global return_value

        i_cmd = 0
        while i_cmd < len(command):
            i = 0
            lenght = 0
            while i < len(command[i_cmd]):
                if command[i_cmd][i] == '_': lenght += 1
                else:
                    lenght = 0
                    break
                i += 1

            if lenght > 0:
                if auto_var and lenght <= len(auto_var): command[i_cmd] = auto_var[len(auto_var) - lenght]
                else:
                    try: raise Exception('no saved variables')
                    except:
                        return stdinout.exception(sys.exc_info())
                        return None
            i_cmd += 1

        return command

    def indent_offset(command):
        r'''Считает смещение для команды и возвращает число'''
        out = 0
        while out < len(command):
            if command[out] == '': out += 1
            else: break
        return out

    def attr_offset(obj, command):
        r'''Автоматический определяет момент перехода от атрибутов к аргументов в команде. возращает массив с атрибутами
        *Можно явно указать переход, поставив дополнительный пробел
        *Принимает любой атрибут для объектов с методом __getattr__'''
        global return_value
        index = None
        if '' in command:
            index = command.index('')
            if '' in command[:index]:
                try: raise Exception('odd space')
                except:
                    return stdinout.exception(sys.exc_info())
            command = command[:index]

        i = 0
        out = []
        while i < len(command):
            if simple.type(obj) == 'exception': return obj
            try: obj = getattr(obj, command[i])
            except:
                if index:
                    return stdinout.exception(sys.exc_info()) #Нет пояснения ошибки
                break
            out.append(command[i])
            i += 1
        return out

    def filter(command):
        r'''Удаляет вообще все пустые строки("") из комманды'''
        out = []
        for elm in command:
            if elm not in ['']: out.append(elm)
        return out

    def types_obj(obj):
        r'''Создаёт словарь со списком названий типов переменных, требуемых для вызова переданного объекта
        *Если в анотации переменной больше одной переменной запишет список на её месте
        *Если объект принимает *args и/или **kwargs, укажет "*args", "**kwargs" в конце списка'''
        args = info.args(obj)
        out = {'args': [], 'kwargs': {}, '*args': None, '**kwargs': None}

        for arg in args['args']:
            if simple.type(arg['ann']) in ['str', 'list', 'tuple']:
                if arg['def'] == None: out['args'].append(arg['ann'])
                else: out['kwargs'][arg['name']] = arg['ann']
            else:
                if arg['def'] == None: out['args'].append('str')
                else: out['kwargs'][arg['name']] = 'str'

        if args['*args'] and args['*args']['ann'] in ['str', 'list', 'tuple']: out['*args'] = args['*args']['ann']
        elif args['*args'] and args['*args']['ann'] == None: out['*args'] = 'str'

        if args['**kwargs'] and args['**kwargs']['ann'] in ['str', 'list', 'tuple']: out['**kwargs'] = args['**kwargs']['ann']
        elif args['**kwargs'] and args['**kwargs']['ann'] == None: out['**kwargs'] = 'str'

        return out

    def types_vars(args, kwargs, types):
        r'''Подготавливает args и kwargs для конвертации в типы указанные в словаре types
        *Непостоянные аргументы, переданные не в словаре, будут вставлены подряд в незанятыми словарём переменные'''
        if len(types['args']) > len(args):
            try: raise Exception('not enough arguments passed')
            except: return stdinout.exception(sys.exc_info())
        if kwargs == None: kwargs = dict()

        _args = []
        temp_kwargs = []
        _types = copy.deepcopy(types['args'])
        if types['*args'] == None:
            temp_kwargs = args[len(types['args']):]
            args = args[:len(types['args'])]
        else:
            _types += [types['*args'] for i in range(len(types['args']), len(args))]
        for i in range(0, len(_types)):
            _args.append(dict(value = args[i], type = _types[i]))

        if types['kwargs'] == None: types['kwargs'] == dict()
        if types['**kwargs'] == None and len(kwargs) + len(temp_kwargs) > len(types['kwargs']):
            try: raise Exception('extra positional arguments')
            except: return stdinout.exception(sys.exc_info())
        _kwargs = []
        for kwarg in types['kwargs'].keys():
            if kwargs.get(kwarg) != None:
                _kwargs.append(dict(value = kwargs.pop(kwarg), type = types['kwargs']['kwarg']))
            elif len(temp_kwargs) > 0:
                _kwargs.append(dict(value = temp_kwargs.pop(0), type = types['kwargs']['kwarg']))
        if types['**kwargs']:
            for key in kwargs.keys():
                _kwargs.append(dict(name = key, value = kwargs.pop(key), type = types['**kwargs']))
            for i in range(0, len(temp_kwargs)):
                _kwargs.append(dict(name = str(i), value = temp_kwargs[i], type = types['**kwargs']))
        elif len(kwargs) > 0 or len(temp_kwargs) > 0:
            try: raise Exception('too many arguments')
            except: stdinout.exception(sys.exc_info())

        return dict(args = _args, kwargs = _kwargs)

    def convert_var(value, type):
        r'''Конвертирует переменную в указанный тип. Для конветрации использует extens'''
        _extens = extens()
        _excepts = []
        if simple.type(type) == 'str': type = [type]
        elif simple.type(type) in ['tuple', 'list']: pass
        else:
            try: raise Exception('invalid annotation type, must be: str, tuple or list')
            except: return stdinout.exception(sys.exc_info())

        for _type in type:
            if simple.type(value) == _type:
                return value
            else:
                try: return getattr(_extens, _type)(value)
                except: _excepts.append(stdinout.exception(sys.exc_info()))

        if _excepts == []:
            try: raise Exception('failed to convert')
            except: return stdinout.exception(sys.exc_info())
        else:
            return _excepts[0]  # Доработать эту ошибку, что бы могло передавать сразу все или выбирала наиболее подходящую

    def convert_vars(args, kwargs):
        r'''Принимает два списка с переменными и возвращает готовый сконвертированный *args и **kwargs'''
        _args = []
        _kwargs = {}
        temp = None

        for arg in args:
            temp = sub.convert_var(arg['value'], arg['type'])
            if simple.type(temp) == 'exception': return temp
            else: _args.append(temp)
        for kwarg in kwargs:
            temp = sub.convert_var(kwarg['value'], kwarg['type'])
            if simple.type(temp) == 'exception': return temp
            else: _kwargs[kwarg['name']] = temp

        return dict(args = _args, kwargs = _kwargs)

class tools():
    r'''Возвращает экземпляр tools, Не желательно создавать этот экземпляр самостоятельно, воспользуйтесь anthros.core.tools()'''
    def __init__(self): self.none = None

    def __call__(self):
        out = dir(self)
        i = 0
        while i < len(out):
            if len(out[i]) < 2: i += 1
            elif out[i][:2] != '__': i += 1
            else: out.pop(i)
        return out

    def ac_pos(self):
        r'''Возвращает корневое расположение Anthro-Core'''
        return info.ac_path()

    def pj_pos(self):
        r'''Возвращает текущее расположение проекта'''
        return info.project_path()

    def args(self, obj: ('_def', '_class')):
        r'''Возвращает аргументы требуемые для вызова объекта'''
        return info.args(obj)#['args']

    def file_exist(self, path: 'str'):
        r'''Проверят, существует ли объект по указаному абсолютному пути'''
        return simple.file_exist(path)

    def smart_path(self, path: 'str'):
        r'''Вернёт абсолютную ссылку со смещением от AC, проекта или корневой папки жесткого диска, если файла нет, вернёт None'''
        return simple.smart_path(path)

    def echo(self, *args):
        r'''Возвращает написанное. Нужен для прсмотр содержания в переменных или для создания переменной вручную'''
        if len(args) == 1: return args[0]
        else: return args

    def vars(self):
        r'''Возвращает зарезервированные переменные AC'''
        global auto_var
        return auto_var

    def test(self, abc, cba, aaa = 111, bbb = 222, ccc = 333, *args, **kwargs):
        print('test:', abc, cba, aaa, bbb, ccc, args, kwargs, sep = ', ')

class extens():
    def __init__(self):
        r'''Возвращает все объекты расширений из папки extens, в виде словаря
        *Внимание! Функция будет работать правильно только после запуска core.run()'''
        represent.class_def_comp(info.ac_path() + simple.path_os('/extens'), encoding='cp1251')
        save_pos = simple.pos_switch(info.ac_path())

        import extens
        folder = represent.fold_dict(info.ac_path() + simple.path_os('/extens'))
        separ = {'str': str, 'int': int}
        for elem in folder:
            if simple.type(elem) == 'str':
                name = simple.path_name(elem)
                if '.class' in name:
                    name = name.split('.')[0]
                    separ[name] = getattr(extens, name)

        simple.pos_switch(**save_pos)
        self.separ = separ

    def __getitem__(self, key):
        return self.separ[key]

    def __getattr__(self, attr):
        return self.separ[attr]

    def __dir__(self):
        return self.separ.keys()

    def keys(self):
        return self.separ.keys()

class interfaces():
    def __init__(self): self.none = None

    def console(self):
        return console

class core():
    def __init__(self):
        r'''Возвращает экземпляр core. Не желательно создавать этот экземпляр самостоятельно, воспользуйтесь anthros.core.run()'''
        class general():
            def __init__(self, ac_tools, ac_extens, pj_env):
                r'''Приоритет от первого аргумента к последнему'''
                self.pj_env = [pj_env]
                self.tools = ac_tools
                self.extens = ac_extens

            def __getattr__(self, attr):
                r'''Возвращает первый найденный артибут окружения, в порядке приоритета, если найден не будет, вернёт None'''
                for obj in self.pj_env:
                    try: return getattr(obj, attr)
                    except:
                        try: raise Exception('the environment does not have this attribute')
                        except: return stdinout.exception(sys.exc_info())

            def __dir__(self):
                r'''Возвращает список всех возможных вызовов, кроме системных'''
                out = []
                for obj in self.pj_env:
                    for elm in dir(obj):
                        if len(elm) == 1: out.append(elm)
                        elif len(elm) >= 2 and elm[:2] != '__': out.append(elm)
                return ['tools', 'extens'] + out

            def tools(self):
                r'''Возвращает объект для использования инструментов AC'''
                return self.tools

            def extens(self):
                r'''Возвращает объект для использования расширений AC'''
                return self.extens

        save_pos = simple.pos_switch(info.ac_path())
        self.env = general(tools(), extens(), extens().fold(info.project_path()))
        self.auto_var = []
        simple.pos_switch(**save_pos)

    def command(self, command: ('str', 'list'), kwargs: 'dict' = None):
        r'''Выполняет команду по правилам AC
        *Если будет аннотация, не содержащаяся в папке extens, тогда переменная будет переданна как строка'''
        global return_value
        return_value = (None, 0, None, 0)
        obj = self.env

        if command in ['', []]: #перенести в mods
            return dir(obj)

        command = sub.command_pars(command, self.auto_var)
        if simple.type(command) == 'exception': return command

        indent = sub.indent_offset(command)
        command = command[indent:]

        if simple.type(command[0]) == 'str': obj = self.env
        else:
            obj = command[0]
            command = command[1:]

        attrs = sub.attr_offset(obj, command)
        if simple.type(attrs) == 'exception': return attrs
        for attr in attrs: obj = getattr(obj, attr)
        args = sub.filter(command[len(attrs):])
        if simple.type(obj) == 'exception': return obj

        types = sub.types_obj(obj)
        if simple.type(types) == 'exception': return types
        vars = sub.types_vars(args, kwargs, types)
        if simple.type(vars) == 'exception':
            if str(vars.description()) == 'not enough arguments passed': return info.args(obj) #эксперементальный вывод аргументов
            return vars
        args = sub.convert_vars(vars['args'], vars['kwargs'])
        if simple.type(args) == 'exception': return args

        try: return_value = obj(*args['args'], **args['kwargs'])
        except:
            err = stdinout.exception(sys.exc_info())
            if str(err.description()) == '\'extens\' object is not callable': return dir(obj)
            return err

        if return_value != None: self.auto_var.append(return_value)
        global auto_var
        auto_var = self.auto_var
        return return_value

    def exit(self):
        represent.temp_py_clear()

def run(load_out = None):
    r'''Подгатавливает всё для AC и проекта. Возвращает объект AC, с которым вы можете взаимодействовать
    *Для получения информации о запуске, load_out = True'''
    save_pos = simple.pos_switch(info.ac_path())

    if load_out: print('compiling project...')
    #написать функцию для компилирования всех вложенных в папку файлов
    #manifest = represent.manifest(info.ac_path() + simple.slash_os() + 'manifest.ini') #провести работу над манифестом

    simple.pos_switch(**save_pos)
    return core()