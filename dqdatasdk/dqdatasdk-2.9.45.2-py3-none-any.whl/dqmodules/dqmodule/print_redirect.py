# -*- coding: utf-8 -*-

import sys
import threading

#保存stdout，防止丢失
_stdout = sys.stdout

'''
这个类的
'''
class __PrintArea__(object):
    _instance_lock = threading.Lock()
    
    # 保存原本的stdout的变量，用于恢复原本的stdout，如果是None则未重定向
    _stdout = None
    # 保存print的变量数组，格式为[]
    _buffer = None
    def __init__(self) -> None:
        self._buffer = []

    #以new方法实现单例模式
    def __new__(cls: type, *args, **kwargs):
        if not hasattr(__PrintArea__, "_instance"):
            with __PrintArea__._instance_lock:
                if not hasattr(__PrintArea__, "_instance"):
                    __PrintArea__._instance = object.__new__(cls)
        
        return __PrintArea__._instance

    # 实现write接口
    def write(self, *args, **kwargs):
        self._buffer.append(args)

    # 实现flush接口
    def flush(*args, **kwargs):
        pass

    def _get_and_clear_buffer(self):
        buffer = self._buffer
        self._buffer = []
        return buffer

    def exucte_proxy_print_init(self, func,  username, password, replacefunc):
        if func == None:
            return
        try:
            self._redirect_printarea()
            data = func(username, password)
        finally:
            self._direct_printarea()
        
        printinfo = self._get_and_clear_buffer()
        if replacefunc != None:
            [print(replacefunc(str[0]), end="") for str in printinfo]
        else:
            [print(str[0], end="") for str in printinfo]
        return data

    # 接管func的print并打印，注意不能嵌套调用
    def excute_proxy_print(self, func, replacefunc = None, *args):
        if func == None:
            return
        try:
            self._redirect_printarea()
            if len(args) != 0:
                data = func(args)
            else:
                data = func()
        finally:
            self._direct_printarea()
        
        printinfo = self._get_and_clear_buffer()
        if replacefunc != None:
            [print(replacefunc(str[0]), end="") for str in printinfo]
        else:
            [print(str[0], end="") for str in printinfo]
        return data
    
    # 将stdout重定向到buffer
    def _redirect_printarea(self):
        if self._stdout == None:
            self._stdout = sys.stdout
        else:
            raise Exception("不能嵌套调用print重定向")
        sys.stdout = self

    # 重新将stdout恢复
    def _direct_printarea(self):
        if self._stdout != None:
            sys.stdout = self._stdout
            self._stdout = None

'''
这里构建一个只对外部使用的变量，外部直接导入就使用这个变量
'''
printarea = __PrintArea__()


if __name__ == "__main__":
    teststr = "this is teststr;"
    print(teststr)

    func = lambda :print(teststr + "print area")
    strlist = printarea.excute_proxy_print(func)
    

    




