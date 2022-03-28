# -*- coding: utf-8 -*-
'''
author:阿狸
email:2528104776@qq.com
'''
import configparser
import glob
import os
import pickle
import threading
import time


def print_time(func):
    def method(*args):
        present_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        if args and args[0].name and args[0].name == 'Initialize':
            result = func(args[0], present_time)
            print(present_time)
            return result

        else:
            result = func(present_time)
            print(present_time)
            return result

    return method


class Initialize:
    name = 'Initialize'
    threadings = 0

    def __init__(self, cfg_path):

        config = configparser.ConfigParser()
        config.read(cfg_path, encoding='utf-8')
        self.root_path = config.get("DATA", "total_folder_path")
        self.pickle_file_path = os.path.dirname(cfg_path) + "\\info"
        self.log_path = os.path.dirname(cfg_path) + "\\log.txt"
        self.select_file_or_folder = config.get("DATA", "select_file_or_folder")
        self.coding = config.get("DATA", "coding")
        self.items = dict()

    @property
    def Scan(self):

        def __isdir__(x):
            file_name = os.path.splitext(x)[0]
            if os.path.isdir(x):
                return x
            elif os.path.isfile(x):
                self.items[x.split("\\")[-2] + "\\" + file_name] = x

        print("当前时间: %d当前线程程:%d,累计调用线程数为:%d" % (
            time.time() * 1000, threading.currentThread().ident, Initialize.threadings))

        f_path = glob.glob(self.root_path + "\\*")
        __paths = list(map(__isdir__, f_path))

        for i in __paths:
            if i != "" and i != None:
                self.iteration(i)
        return self.items

    def iteration(self, file_path):

        def func1():
            Initialize.threadings += 1
            print("当前时间:%d 当前线程程:%d,累计调用线程数为:%d" % (
                time.time() * 1000, threading.currentThread().ident, Initialize.threadings))
            for root, dirs, files in os.walk(file_path):
                for i in files:
                    if self.select_file_or_folder == '2' or self.select_file_or_folder == '3':
                        path = r'{0}\{1}'.format(root, i)
                        if self.items.__contains__(i):
                            self.items[path.split("\\")[-2] + "\\" + i] = path
                        else:
                            self.items[i] = path

        def func2():
            Initialize.threadings += 1
            print("当前时间:%d 当前线程程:%d,累计调用线程数为:%d" % (
                time.time() * 1000, threading.currentThread().ident, Initialize.threadings))
            for root, dirs, files in os.walk(file_path):
                for i in dirs:
                    if self.select_file_or_folder == '1' or self.select_file_or_folder == '3':
                        path = r'{0}\{1}'.format(root, i)
                        if self.items.__contains__(i):
                            self.items[path.split("\\")[-2] + "\\" + i] = path
                        else:
                            self.items[i] = path

        t1 = create_thread(func=func1,
                           name="files_")
        t2 = create_thread(func=func2,
                           name="dirs_")
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        return None

    @print_time
    def run(self, present_time):
        print("Initialize...")
        items = self.Scan
        data = dict()
        if os.path.exists(self.pickle_file_path):
            if os.path.getsize(self.pickle_file_path) > 0:
                with open(self.pickle_file_path, mode='rb') as file:
                    data = pickle.load(file)
                    data.update(items)
        if not data:
            data = self.items

        with open(self.pickle_file_path, mode='wb') as file, \
                open(self.log_path, mode='a', encoding=self.coding) as log:
            pickle.dump(data, file)
            log.write("{0}，初始化\n".format(present_time))
            print('Initialization succeeded!')

        return None


def create_thread(func, name=None):
    thread = threading.Thread(target=func, name=name)
    return thread


if __name__ == "__main__":
    pass
