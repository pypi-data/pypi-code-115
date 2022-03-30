# -*- encoding: utf-8 -*-
# @Author   :   haogooder
# @Date     :   2021/10/10
# @Desc     :   the description of this file
import fcntl
import logging as _log_
import time
import os


_logger = _log_.getLogger("singleton_util")
_logger.setLevel(_log_.INFO)
_logger.propagate = False
fh = _log_.Formatter('%(asctime)s[%(levelname)9s] %(name)-16s | %(lineno)4s: %(filename)-20s | %(message)s')
sh = _log_.StreamHandler()
sh.setFormatter(fh)
_logger.addHandler(sh)


class Singleton:
    pidfile = -1

    def __init__(self):
        pass

    @staticmethod
    def is_running(process_name):
        """
        判断程序是否已经运行，如果未运行，则会在 /var/run/svd_spider/ 目录下创建一个 process_name.pid 文件，记录进程号
        :param process_name:进程名，调用者需保证 process_name 全局唯一
        :return:
                True	已运行一个实例
                False	未运行实例，暂时不考虑创建 pid 文件失败的情况
        """
        if Singleton.pidfile != -1:
            return True
        pid_file_name = "/var/run/svd_spider/" + process_name + '.pid'
        try:
            Singleton.pidfile = open(pid_file_name, 'r')
            try:
                fcntl.flock(Singleton.pidfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except Exception as e:
                _logger.info(e)
                return True
            Singleton.pidfile.close()
        except Exception as e:
            _logger.info(e)
        try:
            Singleton.pidfile = open(pid_file_name, 'w')
        except Exception as e:
            _logger.info(e)
            return False
        fcntl.flock(Singleton.pidfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        Singleton.pidfile.write(str(os.getpid()))
        Singleton.pidfile.flush()
        return False


if __name__ == '__main__':
    if Singleton.is_running('test_process'):
        print('already running')
    else:
        while True:
            print('running...')
            time.sleep(1)
