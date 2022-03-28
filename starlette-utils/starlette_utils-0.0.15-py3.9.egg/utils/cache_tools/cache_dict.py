#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/12/31 3:33 下午
# @Author  : Hubert Shelley
# @Project  : starlette_utils
# @FileName: cache_dict.py
# @Software: PyCharm
"""
import time


class CacheDict(dict):
    def __init__(self, _live_time: int = 1200, auto_grew: float = 1.1, **kwargs):
        """
        自缓存字典

        :param _live_time: 缓存时间，单位：秒
        :param auto_grew: 缓存时间成长系数
        :param kwargs:
        """
        self.live_time = _live_time
        self.auto_grew = auto_grew
        self.live_cache = {}
        super().__init__(**kwargs)
        import threading
        _thread = threading.Thread(target=self.auto_minus)
        _thread.setDaemon(True)
        _thread.start()
        for key in kwargs.keys():
            self.live_cache[key] = self.live_time

    def auto_minus(self):
        while True:
            list(map(self.set_minus, list(self.live_cache.keys())))
            list(map(self.del_zero, list(self.live_cache.keys())))
            time.sleep(1)

    def __getitem__(self, y):
        self.set_longer(y)
        return super().__getitem__(y)

    def __setitem__(self, *args, **kwargs):
        if args:
            self.live_cache[args[0]] = self.live_time
        for key in kwargs.keys():
            self.live_cache[key] = self.live_time
        return super().__setitem__(*args, **kwargs)

    def set_longer(self, x):
        self.live_cache[x] = int(self.live_cache[x] * self.auto_grew)

    def set_minus(self, x):
        self.live_cache[x] = self.live_cache[x] - 1

    def del_zero(self, x):
        if self.live_cache[x] <= 0:
            self.live_cache.pop(x)
            self.pop(x)
