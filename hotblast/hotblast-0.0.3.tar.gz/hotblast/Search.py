# -*- coding: utf-8 -*-

'''
author:阿狸
email:2528104776@qq.com
'''

import configparser
import difflib
import os
import pickle
import platform
import sys
import time

config = configparser.ConfigParser()
config.read("config.cfg", encoding='utf-8')

coding = config.get("DATA", "coding")
times = 0
container = list()


class Stack:
    def __init__(self):
        self.__list = list()

    def __str__(self):
        return "\n".join(self.__list.reverse())

    def push(self, item):
        self.__list.append(item)

    def pop(self):
        return self.__list.pop()

    def peek(self):
        return self.__list[-1]

    def is_empty(self):
        return not self.__list

    @property
    def size(self):
        return len(self.__list)


def print_time(func):
    def method(*args):
        present_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

        result = func(present_time, *args)
        print(present_time)
        return result

    return method


@print_time
def main(present_time, cfg_path):
    pickle_file_path = os.path.dirname(cfg_path) + "\\info"
    log_path = os.path.dirname(cfg_path) + "\\log.txt"
    words = dict()
    with open(pickle_file_path, mode='rb') as file:
        data = pickle.load(file)

    if sys.getsizeof(data) <= 0 or data == {}:
        print("文件数据为空值,读取失败...")
        sys.exit()

    name = input('请输入名称:')
    if name == "q" or name == "exit" or name == "quit" or name == "":
        sys.exit(0)

    def loop_data(file_name):
        global times
        if name in file_name:
            Degree_of_similarity = get_equal_rate(name, os.path.splitext(file_name)[0])
            words[file_name] = Degree_of_similarity

            times += 1

    generator = map(loop_data, data.keys())
    list(generator)
    stack = sort_values(words)
    for index in range(stack.size):
        current = stack.pop()
        container.append(current)
        print("序号:%d\t%s" % (index, current))

    if container:
        message = input('请选择:')
        num = int(message)
        file_path = data[container[num]]
        if os.path.exists(file_path):
            with open(log_path, mode='a', encoding=coding) as log:
                log.write('{1}，查找了"{0}"\n'.format(container[num], present_time))
            if os.path.isdir(file_path):
                os.startfile(file_path)
            elif os.path.isfile(file_path):
                if platform.system() == "Windows":
                    os.system("explorer /select,%s" % (file_path))
                else:
                    file_path = file_path.replace(container[num], '')
                    os.startfile(file_path)

                print('所在路径:"{0}"'.format(file_path))
        else:

            print("查找结果(不是一个有效的路径):{0}".format(file_path))
            with open('../log.txt', mode='a', encoding=coding) as log:
                log.write(
                    '{1}，查找"{0}"时文件路径失效！请运行初始化程序:"python Initialization.py"\n'.format(container[num], present_time))

    else:
        print("未找到结果!")
    input("输入回车退出...")
    return name


def get_equal_rate(str1, str2):
    return difflib.SequenceMatcher(None, str1, str2).quick_ratio()


def sort_values(items):
    stack = Stack()
    items = sorted(items.items(), key=lambda kv: (kv[1], kv[0]))

    for i in items:
        stack.push(i[0])

    return stack


if __name__ == "__main__":
    main(r"C:\Users\25281\Desktop\config.cfg")
