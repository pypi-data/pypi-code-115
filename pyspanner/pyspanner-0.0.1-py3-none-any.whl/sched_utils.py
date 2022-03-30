# -*- encoding: utf-8 -*-
# @Author   :   haogooder
# @Date     :   2021/10/10
# @Desc     :   the description of this file

from sched import scheduler
import time


class MySched:
    def __init__(self):
        self.sc = scheduler(time.time, time.sleep)

    def every(self, interval=60):
        def wrapper(func):
            def inner(*args, **kwargs):
                func(*args, **kwargs)
                self.sc.enter(delay=interval, priority=1, action=inner, argument=())
            return inner()
        return wrapper

    def start(self):
        self.sc.run()
