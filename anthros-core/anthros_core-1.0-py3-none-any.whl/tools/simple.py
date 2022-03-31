from tools import info
import sys, os
_type = type

def type(object: '_class'):
    r'''Возвращает название имени объекта'''
    out = _type(object).__name__.split('.')
    return out[len(out) - 1]

def slash_os():
    r'''Возвращает / или \ в зависимости от установленной системы'''
    if sys.platform in ['win32']: return '\\'
    else: return '/'

def path_os(path: 'str', in_list: 'bool' = False):
    r'''Унифицирует ссылку для windows и linux'''
    _path = ['']
    i = 0
    for sb in path:
        if sb not in ['\\', '/']:
            _path[i] += sb
        else:
            _path.append('')
            i += 1
    if in_list: return _path
    else: return slash_os().join(_path)

def path_name(path: 'str'):
    r'''Возвращает имя файла или папки'''
    name = path_os(path, in_list = True)
    return name[len(name) - 1]

def file_exist(path: 'str'):
    r'''Проверяет наличие файла по абсолютному пути
    *Если папка существует, вернёт "folder", если файл, "file", если пусто, None'''
    if os.path.isdir(path): return 'folder'
    elif os.path.isfile(path): return 'file'
    else: return None


def smart_path(path: 'str', rel: ('str', 'tuple', 'list') = None):
    r'''Проверяет действительно ли расположение и возвращает абсолютную ссылку
    *rel (relative) постоянная переменная, принимающая смещение для расположения, в виде строки или списка расположений
    *По умолчанию (rel = None) смотрит относительное расположение AC, проекта и корня жесткого диска
    *Если по расположению не чего нет, то вернёт None'''
    path = path_os(path)
    if rel == None: rel = [info.ac_path(), info.project_path(), '']
    if type(rel) in ['tuple', 'list']:
        for rel_path in rel:
            if rel_path == '' and file_exist(path):
                return path
            elif file_exist(str(rel_path) + slash_os() + path):
                return str(rel_path) + slash_os() + path
    else:
        if file_exist(str(rel) + slash_os() + path):
            return str(rel) + slash_os() + path

def pos_switch(path: ('str', 'dict') = None, sys_path: 'str' = None, os_chdir: 'str' = None):
    r'''Изменяет все системных расположения для корректной работы импортов и тд.
    *Вы так же можете изменить только одно из значений
    *path изменяет все значения или значения которые не указаны в ручную
    *Возвращает словарь с предыдущими значениями (kwargs)
    *Используйте pos_switch(**kwargs) что бы вернуть значения'''
    if type(path) == 'dict': sys_path, os_chdir, path = path['sys_path'], path['os_chdir'], None
    out = dict(sys_path = sys.path[0], os_chdir = os.getcwd())

    if sys_path: sys.path[0] = sys_path
    elif path: sys.path[0] = path
    if os_chdir: os.chdir(os_chdir)
    elif path: os.chdir(path)
    if sys.platform == 'win32' and os_chdir or path:
        if os_chdir: os.system(os_chdir.split(slash_os())[:1][0])
        else: os.system(path.split(slash_os())[:1][0])

    return out