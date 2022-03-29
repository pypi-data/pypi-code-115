# -*- coding: utf-8 -*-
from logging import exception
import sys
import functools
import traceback
import rqdatac
import dqdatasdk.dqmodule.dqcertificate as dqc
from dqdatasdk.dqmodule.print_redirect import printarea

_dqdatasdk = "dqdatasdk"

def replace(str):
    str = str.replace('rqdatac ', 'dqdatasdk ')
    str = str.replace('rqdatac.', 'dqdatasdk.rqdatac.')
    str = str.replace('0755-22676337', '0755-86952080')
    return str

'''
这个装饰器用来装饰所有调用函数，将异常信息中的rqdata转换为dqdata
'''
def catchexception(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, ** kwargs)
        except Exception as e:
            tracebackinfo = traceback.format_exc()
            exceptinfo = str(e)
            print("\033[1;31m" + tracebackinfo + "\033[0m")
            print("\033[1;31m" + replace(exceptinfo) + "\033[0m")
            # print(tracebackinfo, end="")
            # print(replace(exceptinfo), end="")
            # value = sys.exc_info()[2]
            # value.tb_frame.f_locals.update
            # ty = type(value)
            # raise e.with_traceback(sys.exc_info()[2])
            # excute_info = sys.exc_info()
            # six.reraise(*excute_info)
    
    return wrapper



@catchexception
def info():
    return printarea.excute_proxy_print(rqdatac.info, replace)
    
def init(username=None, password=None, addr=("rqdatad-pro.ricequant.com", 16011), *_, **kwargs):
    """initialize dqdatasdk.

    dqdatasdk connection is thread safe but not fork safe. Every thread have their own connection by
    default. you can set param 'use_pool' to True to use a connection pool instead.

    NOTE: if you are using dqdatasdk with python < 3.7 in a multi-process program, remember to call
    reset in child process.

    Environment Variable:
    RQDATAC_CONF / RQDATAC2_CONF: When init called with no argument, the value in RQDATAC2_CONF is used as uri, then RQDATAC_CONF.
    RQDATAC_PROXY: proxy info, e.g. http://username:password@host:port

    :param username: string
    :param password: string
    :param addr: ('127.0.0.1', 80) or '127.0.0.1:80'

    :keyword uri: keyword only. a uri like rqdata://username:password@host:port or tcp://username:password@host:port
    :keyword connect_timeout: socket connect connect timeout, default is 5 sec.
    :keyword timeout: socket time out, default is 60 sec.
    :keyword lazy: True by default, means "do not connect to server immediately".
    :keyword use_pool: use connection pool. default is False
    :keyword max_pool_size: max pool size, default is 8
    :keyword proxy_info: a tuple like (proxy_type, host, port, user, password) if use proxy, default is None
    :keyword auto_load_plugins: boolean, enable or disable auto load plugin, default to True.
    """
    import warnings
    warnings.filterwarnings("ignore")
    license = dqc.get_dqdata_license(username=username, password=password)
    return printarea.exucte_proxy_print_init(rqdatac.init, 'license', license, replace)
    

@catchexception
def test():
    init('13392405029', '123456')
    info()

    # rqdatac.init(username="11111", password="1231111456")
    data = rqdatac.all_instruments(type='CS', market='cn', date='2021-12-27')

    

if __name__ == "__main__":
    test()



    
